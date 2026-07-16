//! MCTS für die Drafting-Phase — Port der Kern-Features aus agents/mcts.py
//! (HeuristicMCTSAgent): Progressive Widening, UCB c = 0.3, sublineares
//! Wachstum, `player_who_acted`-Backprop und Win-Prob-Bewertung.
//!
//! Wert eines Zustands = `total(0) − total(1)`, per Sigmoid (`diff_to_probs`)
//! in (0, 1) abgebildet. `total(pi)` ist der EXAKTE erwartete Rundenscore aus
//! dem Tiling-Solver ([`crate::tiling_solver::solve_round_final_score`]) — keine
//! per-Reihe-Heuristik mehr (erfasst auch reihenübergreifende Linien).
//!
//! Phasen-Umfang: Der Suchbaum läuft NUR über Drafting; am Übergang
//! Drafting→Tiling ist der Knoten Pseudo-Terminal und wird per DFS-Solver
//! bewertet (kein Tiling im Baum, kein Rundenwechsel/RNG-Neubefüllen).

use rand::seq::SliceRandom;
use rand::{Rng, RngExt};
use serde_json::{json, Value};

use crate::game::{drafting_actions, Game};
use crate::moves::Action;
use crate::scoring::wertung_progress;
use crate::tile::TileColor;
use crate::serialize::action_to_dict;
use crate::state::{GameState, Phase};
use crate::tiling_solver::solve_round_final_score;

/// Initialwelle an Aktionen pro Knoten (Progressive Widening).
pub const MAX_ACTIONS: usize = 10;
/// Faktor des sublinearen Wachstums: `allowed = MAX_ACTIONS + WIDEN_FACTOR·√N`.
pub const WIDEN_FACTOR: f64 = 2.5;
/// Standard-Explorationskonstante (wie agents/mcts.py).
pub const DEFAULT_C: f64 = 0.3;

/// Such-Zug des Drafting-MCTS. Tiling wird NICHT mehr im Baum gesucht — die
/// Tiling-Phase löst der exakte DFS (`crate::tiling_solver`) als Pseudo-Terminal.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SearchMove {
    Draft(Action),
}

struct Node {
    parent: Option<usize>,
    children: Vec<usize>,
    untried: Vec<SearchMove>,
    /// Für Progressive Widening zurückgehaltene, nach Güte sortierte Aktionen.
    remaining: Vec<SearchMove>,
    action: Option<SearchMove>,
    /// Spieler, der den Zug zu diesem Knoten gemacht hat (Backprop-Perspektive).
    player_who_acted: usize,
    visits: u32,
    value: f64,
    state: GameState,
    terminal: bool,
    /// Anzahl legaler Züge in diesem Zustand (Debug-/Analyse-Anzeige).
    n_actions: usize,
    /// Tiefe im Suchbaum (Wurzel = 0). Steuert die Ranking-Qualität beim
    /// Erzeugen (`make_node`) — Tiefe 0/1 teuer, ab Tiefe 2 billig.
    depth: u32,
}

impl crate::search_common::SearchNode for Node {
    fn parent(&self) -> Option<usize> { self.parent }
    fn children(&self) -> &[usize] { &self.children }
    fn terminal(&self) -> bool { self.terminal }
}

// ── Bewertung ────────────────────────────────────────────────────────────────

/// Erwarteter finaler Rundenscore eines Spielers — EXAKT per Tiling-Solver
/// (optimale Platzierung der vollen Reihen inkl. Linien über mehrere Reihen)
/// PLUS ein stetiger Wertungsplatten-Fortschritts-Term ([`wertung_progress`]),
/// damit die Suche Baustellen an aktiven Wertungsplatten (volle Reihen/Spalten/
/// Diagonalen, Ecken, Mehrfarbige Felder) schon vor Fertigstellung goutiert,
/// statt sie erst beim letzten fehlenden Feld zu bemerken, MINUS die Strafe,
/// die bereits unplatzierbare Musterreihen ([`projected_unplaceable_penalty`])
/// beim tatsächlichen Rundenende verursachen werden -- der DFS-Solver sieht
/// selbst nur "0 Punkte von dieser Reihe", nicht die Buße, die sie auf der
/// Strafleiste noch anrichtet. NICHT identisch mit dem `estimated_score` der
/// UI (`serialize.rs`) — der bleibt bewusst rein am real erreichbaren
/// Rundenscore, ohne diese beiden Suche-only-Korrekturterme.
pub(crate) fn player_total(state: &GameState, pi: usize) -> f64 {
    solve_round_final_score(state, pi) as f64
        + wertung_progress(&state.players[pi], &state.scoring_tile_ids)
        + crate::round_end::projected_unplaceable_penalty(&state.players[pi]) as f64
}

/// Skala für die Score→Wert-Normalisierung — identisch zum Netz-Value-Target
/// (`config.py` `VALUE_SCALE=50`), damit Heuristik- und Netzbewertung auf
/// derselben Punkte-Kalibrierung beruhen: gutes Signal bei ~50 Punkten,
/// deutlich sichtbare Sättigung erst deutlich über ~90 Punkten.
pub const VALUE_SCALE: f64 = 50.0;

/// Absoluter Rundenscore eines Spielers → normalisierter Wert in (0, 1).
/// BEWUSST unabhängig vom Score des Gegners (keine Differenzbildung mehr):
/// eine Differenz-Sigmoid sättigt bei großem Punkteabstand für BEIDE Spieler
/// gegen 0/1 — die Suche verliert dann jede Fähigkeit, zwischen "schlecht"
/// und "noch schlechter" (bzw. "gut" und "noch besser") zu unterscheiden,
/// obwohl das Ziel (maximale eigene Punkte, wo möglich auch Abstand
/// minimieren) in jeder Stellung weiterhin gilt. "Wissen" über den Gegner
/// kommt strukturell aus dem Suchbaum (eigene Zweige je Spieler), nicht aus
/// dieser Formel.
fn normalize_score(score: f64) -> f64 {
    ((score / VALUE_SCALE).tanh() + 1.0) / 2.0
}

/// Blattbewertung als Per-Spieler-Wert (absolut, nicht perspektivisch) —
/// [`player_total`] (exakter Rundenscore + Wertungsplatten-Fortschritt),
/// unabhängig davon ob `state` mitten im Drafting oder am Drafting→Tiling-
/// Übergang (Pseudo-Terminal) steht, `solve_round_final_score` behandelt
/// beide Fälle identisch. Öffentlich für den Netz-MCTS-Stufe-1-Modus
/// (DFS-Blattbewertung + Netz-Priors).
pub fn evaluate(state: &GameState, _n_actions: usize) -> [f64; 2] {
    [normalize_score(player_total(state, 0)), normalize_score(player_total(state, 1))]
}

/// Wie [`evaluate`], zusätzlich mit einer Klartext-Erklärung (nur fürs Log).
/// Verwendet die Spielernamen statt P0/P1.
fn evaluate_explain(state: &GameState, _n_actions: usize) -> ([f64; 2], String) {
    let n0 = state.players[0].name.as_str();
    let n1 = state.players[1].name.as_str();
    let t0 = player_total(state, 0);
    let t1 = player_total(state, 1);
    let v = [normalize_score(t0), normalize_score(t1)];
    if state.phase != Phase::Drafting {
        let why = format!(
            "DFS-Terminal (phase={}) {n0}={t0:.1} {n1}={t1:.1} (inkl. Wertungsplatten-Fortschritt)",
            state.phase.as_str(),
        );
        return (v, why);
    }
    let why = format!("Heuristik total[{n0}]={t0:.1} total[{n1}]={t1:.1} (absolut, scale={VALUE_SCALE})");
    (v, why)
}

/// Simulationszahl je Zug (Port von agents/mcts.py `_compute_dynamic_sims`,
/// Modus „play"): mehr Optionen → mehr Sims. `clamp(base + √n·25, base, base·5)`.
pub fn dynamic_sims(base: u32, num_actions: usize) -> u32 {
    let hi = base.saturating_mul(5);
    let target = base + ((num_actions as f64).sqrt() * 25.0) as u32;
    target.clamp(base, hi)
}

// ── Zuggenerierung & -ausführung (nur Drafting) ──────────────────────────────

/// Legale Such-Züge: nur Drafting (Tiling löst der DFS-Solver). Außerhalb der
/// Drafting-Phase leer → der Knoten ist (Pseudo-)Terminal.
fn valid_search_moves(state: &GameState) -> Vec<SearchMove> {
    match state.phase {
        Phase::Drafting => drafting_actions(state).into_iter().map(SearchMove::Draft).collect(),
        _ => Vec::new(),
    }
}

/// Wendet einen Drafting-Zug auf einen Klon an. None bei (unerwartet)
/// ungültigem Zug.
fn apply_search_move(state: &GameState, mv: &SearchMove) -> Option<GameState> {
    match mv {
        SearchMove::Draft(a) => {
            crate::profiling::note_gamestate_clone();
            let mut g = Game { state: state.clone() };
            g.apply_drafting(a).ok()?;
            let mut s = g.state;
            s.log.clear();
            Some(s)
        }
    }
}

// ── Aktions-Ranking für Widening ─────────────────────────────────────────────

/// Teures 1-Ply-Heuristik-Ranking (nur an der Wurzel): jede Aktion ausführen und
/// nach `total(acting) − total(other)` absteigend sortieren.
fn rank_actions_root(state: &GameState, moves: Vec<SearchMove>) -> Vec<SearchMove> {
    let acting = state.current_player;
    let other = 1 - acting;
    let mut scored: Vec<(f64, SearchMove)> = moves
        .into_iter()
        .map(|m| {
            let score = match apply_search_move(state, &m) {
                Some(child) => player_total(&child, acting) - player_total(&child, other),
                None => f64::NEG_INFINITY,
            };
            (score, m)
        })
        .collect();
    scored.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap_or(std::cmp::Ordering::Equal));
    scored.into_iter().map(|(_, m)| m).collect()
}

fn move_priority(m: &SearchMove) -> i32 {
    match m {
        SearchMove::Draft(a) => match a {
            Action::BonusChip(_) => 6,
            Action::Stone(_) => 4,
            Action::Dome(_) => 3,
            Action::DrawStack(_) | Action::DrawStackPeek => 2,
            Action::Pass => 1,
        },
    }
}

/// Billiges Ranking für tiefe Knoten: nach Typ-Priorität (innerhalb gleich:
/// zufällig).
fn rank_actions_cheap<R: Rng + ?Sized>(mut moves: Vec<SearchMove>, rng: &mut R) -> Vec<SearchMove> {
    moves.shuffle(rng);
    moves.sort_by(|a, b| move_priority(b).cmp(&move_priority(a)));
    moves
}

// ── Knoten ───────────────────────────────────────────────────────────────────

#[allow(clippy::too_many_arguments)]
fn make_node<R: Rng + ?Sized>(
    state: GameState,
    parent: Option<usize>,
    action: Option<SearchMove>,
    player_who_acted: usize,
    terminal: bool,
    depth: u32,
    rng: &mut R,
) -> Node {
    let (untried, remaining, n_actions) = if terminal {
        (Vec::new(), Vec::new(), 0)
    } else {
        let moves = valid_search_moves(&state);
        let n = moves.len();
        // Teures 1-Ply-Ranking für Wurzel UND den ersten Gegnerzug (Tiefe 0/1) —
        // die Suche erzwingt (s. build_tree) für jeden Wurzelkandidaten
        // mindestens diesen einen Gegenzug, bevor die Wurzel weiterbreitert;
        // der sollte dann auch plausibel sein, nicht zufällig. Ab Tiefe 2
        // (Enkel) wieder das billige Typ-Ranking wie bisher.
        let mut ordered = if depth <= 1 {
            rank_actions_root(&state, moves)
        } else {
            rank_actions_cheap(moves, rng)
        };
        let remaining = if ordered.len() > MAX_ACTIONS {
            ordered.split_off(MAX_ACTIONS)
        } else {
            Vec::new()
        };
        (ordered, remaining, n)
    };
    Node {
        parent,
        children: Vec::new(),
        untried,
        remaining,
        action,
        player_who_acted,
        visits: 0,
        value: 0.0,
        state,
        terminal,
        n_actions,
        depth,
    }
}

/// UCB1 (c = 0.3): bestes Kind aus Sicht des Knoten-Spielers. Da alle Kinder
/// vom selben Spieler (current_player des Knotens) erzeugt werden und ihr Wert
/// aus `player_who_acted`-Sicht gespeichert ist, wird NICHT negiert.
fn best_uct_child(nodes: &[Node], nid: usize, c: f64) -> usize {
    let ln_parent = (nodes[nid].visits.max(1) as f64).ln();
    let mut best = nodes[nid].children[0];
    let mut best_score = f64::NEG_INFINITY;
    for &cid in &nodes[nid].children {
        let n = nodes[cid].visits as f64;
        let exploit = nodes[cid].value / n;
        let explore = c * (ln_parent / n).sqrt();
        let score = exploit + explore;
        if score > best_score {
            best_score = score;
            best = cid;
        }
    }
    best
}

/// Knoten-Kurzlabel fürs Log (Aktionsbeschreibung bzw. „Wurzel"). Mit
/// Eltern-Zustand (VOR dem Zug) für Steinanzahl/Füllstand/Strafleisten-Hinweis.
fn log_label(nodes: &[Node], nid: usize) -> String {
    match &nodes[nid].action {
        None => "Wurzel".to_string(),
        Some(sm) => {
            let parent_state = nodes[nid].parent.map(|p| &nodes[p].state);
            label_search_move(sm, parent_state).1
        }
    }
}

/// Expandiert ein zufälliges unversuchtes Kind von `nid` (widened bei Bedarf
/// zuerst eine Aktion aus `remaining` frei) und backpropagiert dessen
/// Blattwert bis zur Wurzel — exakt der Expansion/Bewertung/Backprop-Schritt
/// einer normalen Simulation, nur außerhalb der Sim-Zählschleife aufrufbar.
/// Für die Nachlauf-Schließung offener Enden (siehe unten): kein Effekt,
/// falls `nid` bereits terminal ist oder keine Aktionen mehr übrig hat.
fn expand_and_backprop<R: Rng + ?Sized>(
    nodes: &mut Vec<Node>,
    nid: usize,
    names: &[&str; 2],
    rng: &mut R,
    log: &mut Option<&mut Vec<String>>,
) {
    if nodes[nid].untried.is_empty() && !nodes[nid].remaining.is_empty() {
        let allowed = MAX_ACTIONS + (WIDEN_FACTOR * (nodes[nid].visits as f64).sqrt()) as usize;
        if nodes[nid].children.len() < allowed {
            let mv = nodes[nid].remaining.remove(0);
            nodes[nid].untried.push(mv);
        }
    }
    if nodes[nid].untried.is_empty() {
        return;
    }
    let idx = rng.random_range(0..nodes[nid].untried.len());
    let mv = nodes[nid].untried.swap_remove(idx);
    let mover = nodes[nid].state.current_player;
    let Some(child_state) = apply_search_move(&nodes[nid].state, &mv) else { return };
    let terminal = child_state.phase != Phase::Drafting;
    let child_depth = nodes[nid].depth + 1;
    let child = make_node(child_state, Some(nid), Some(mv.clone()), mover, terminal, child_depth, rng);
    let cid = nodes.len();
    nodes.push(child);
    nodes[nid].children.push(cid);
    if let Some(l) = log.as_deref_mut() {
        l.push(format!(
            "  EXPAND #{nid} +[{}] → #{cid} (Zug: {}{})",
            label_search_move(&mv, Some(&nodes[nid].state)).1,
            names[mover],
            if terminal { ", terminal/DFS" } else { "" }
        ));
    }

    let value = if log.is_some() {
        let (v, why) = evaluate_explain(&nodes[cid].state, nodes[cid].n_actions);
        if let Some(l) = log.as_deref_mut() {
            l.push(format!(
                "  EVAL   #{cid} {why} → win[{}]={:.3} win[{}]={:.3}",
                names[0], v[0], names[1], v[1]
            ));
        }
        v
    } else {
        evaluate(&nodes[cid].state, nodes[cid].n_actions)
    };

    let mut bp = String::from("  BACKPROP");
    let mut cur = Some(cid);
    while let Some(i) = cur {
        nodes[i].visits += 1;
        let delta = value[nodes[i].player_who_acted];
        nodes[i].value += delta;
        if log.is_some() {
            bp.push_str(&format!(" #{i}+={delta:.3}({})", names[nodes[i].player_who_acted]));
        }
        cur = nodes[i].parent;
    }
    if let Some(l) = log.as_deref_mut() {
        l.push(bp);
    }
}

/// Baut den Drafting-Suchbaum (Wurzel = Index 0). None, wenn `state` nicht in
/// der Drafting-Phase ist (Tiling löst der DFS-Solver separat). Mit
/// `log = Some(..)` wird die Schleife je Simulation (Selection/Expansion/
/// Bewertung/Backprop) protokolliert; `None` = kein Overhead.
fn build_tree<R: Rng + ?Sized>(
    state: &GameState,
    simulations: u32,
    c: f64,
    rng: &mut R,
    mut log: Option<&mut Vec<String>>,
) -> Option<Vec<Node>> {
    if state.phase != Phase::Drafting {
        return None;
    }

    let names = [state.players[0].name.as_str(), state.players[1].name.as_str()];
    let mut root_state = state.clone();
    root_state.log.clear();
    let root_player = root_state.current_player;
    let mut nodes: Vec<Node> =
        vec![make_node(root_state, None, None, root_player, false, 0, rng)];

    macro_rules! logln {
        ($($arg:tt)*) => { if let Some(l) = log.as_deref_mut() { l.push(format!($($arg)*)); } };
    }

    for sim in 0..simulations {
        logln!("=== Sim {}/{} ===", sim + 1, simulations);

        // 1. Selection (mit Progressive Widening).
        let mut nid = 0;
        loop {
            // Erzwungener Gegnerzug (Tiefe 0/1, siehe search_common::force_reply_target):
            // ein Knoten breitert erst weiter, wenn sein zuletzt erzeugtes Kind
            // selbst mindestens einen eigenen Kindknoten hat (= Antwort simuliert).
            if let Some(target) = crate::search_common::force_reply_target(&nodes, nid) {
                logln!("  FORCE-REPLY #{nid} → #{target}: Antwort erzwungen vor weiterem Breitern");
                nid = target;
                continue;
            }
            if nodes[nid].terminal {
                logln!("  SELECT #{nid} [{}] terminal", log_label(&nodes, nid));
                break;
            }
            // Widening: eine reservierte Aktion freischalten, sobald untried leer
            // ist und das sublineare Budget noch Platz lässt.
            if nodes[nid].untried.is_empty() && !nodes[nid].remaining.is_empty() {
                let allowed =
                    MAX_ACTIONS + (WIDEN_FACTOR * (nodes[nid].visits as f64).sqrt()) as usize;
                if nodes[nid].children.len() < allowed {
                    let mv = nodes[nid].remaining.remove(0);
                    logln!("  WIDEN  #{nid} schaltet Aktion frei (allowed={allowed}, Kinder={})",
                        nodes[nid].children.len());
                    nodes[nid].untried.push(mv);
                }
            }
            if !nodes[nid].untried.is_empty() {
                break; // hier expandieren
            }
            if nodes[nid].children.is_empty() {
                break; // (sollte bei nicht-terminal nicht auftreten)
            }
            let cid = best_uct_child(&nodes, nid, c);
            if log.is_some() {
                let n = nodes[cid].visits.max(1) as f64;
                let exploit = nodes[cid].value / n;
                let explore = c * ((nodes[nid].visits.max(1) as f64).ln() / n).sqrt();
                logln!(
                    "  SELECT #{nid} → #{cid} [{}] (Zug: {}) N={} Q={:.3} U={:.3} → {:.3}",
                    log_label(&nodes, cid), names[nodes[cid].player_who_acted],
                    nodes[cid].visits, exploit, explore, exploit + explore
                );
            }
            nid = cid;
        }

        // 2. Expansion (eine zufällige unversuchte Aktion).
        if !nodes[nid].terminal && !nodes[nid].untried.is_empty() {
            let idx = rng.random_range(0..nodes[nid].untried.len());
            let mv = nodes[nid].untried.swap_remove(idx);
            let mover = nodes[nid].state.current_player;
            if let Some(child_state) = apply_search_move(&nodes[nid].state, &mv) {
                // Terminal sobald die Drafting-Phase verlassen ist (→ DFS-Eval).
                let terminal = child_state.phase != Phase::Drafting;
                let child_depth = nodes[nid].depth + 1;
                let child = make_node(child_state, Some(nid), Some(mv.clone()), mover, terminal, child_depth, rng);
                let cid = nodes.len();
                nodes.push(child);
                nodes[nid].children.push(cid);
                logln!(
                    "  EXPAND #{nid} +[{}] → #{cid} (Zug: {}{})",
                    label_search_move(&mv, Some(&nodes[nid].state)).1,
                    names[mover],
                    if terminal { ", terminal/DFS" } else { "" }
                );
                nid = cid;
            }
        }

        // 3. Blattbewertung (Per-Spieler-Win-Prob).
        let value = if log.is_some() {
            let (v, why) = evaluate_explain(&nodes[nid].state, nodes[nid].n_actions);
            logln!("  EVAL   #{nid} {why} → win[{}]={:.3} win[{}]={:.3}", names[0], v[0], names[1], v[1]);
            v
        } else {
            evaluate(&nodes[nid].state, nodes[nid].n_actions)
        };

        // 4. Backprop (player_who_acted, ohne Vorzeichenwechsel).
        let mut bp = String::from("  BACKPROP");
        let mut cur = Some(nid);
        while let Some(i) = cur {
            nodes[i].visits += 1;
            let delta = value[nodes[i].player_who_acted];
            nodes[i].value += delta;
            if log.is_some() {
                bp.push_str(&format!(" #{i}+={delta:.3}({})", names[nodes[i].player_who_acted]));
            }
            cur = nodes[i].parent;
        }
        logln!("{bp}");
    }

    // Nachlauf: Force-Reply oben (Tiefe 0/1) greift nur, wenn UCB den Knoten
    // je wieder besucht — Wurzelkinder mit sehr niedrigem Score werden nie
    // erneut selektiert und ihr einziges erzwungenes Kind (Tiefe 2) bleibt
    // dauerhaft ohne eigene Antwort (siehe search_common::nachlauf_targets).
    for target in crate::search_common::nachlauf_targets(&nodes) {
        logln!("  NACHLAUF → #{target}: offenes Ende nachträglich geschlossen");
        expand_and_backprop(&mut nodes, target, &names, rng, &mut log);
    }

    Some(nodes)
}

/// Vollständiger Texttrace einer geloggten MCTS-Suche (für die Debug-Logdatei).
pub fn search_log_text<R: Rng + ?Sized>(
    state: &GameState,
    simulations: u32,
    c: f64,
    rng: &mut R,
) -> String {
    let mut lines: Vec<String> = Vec::new();
    let nodes = build_tree(state, simulations, c, rng, Some(&mut lines));

    let mut out = String::new();
    let n_actions = drafting_actions(state).len();
    out.push_str("MCTS-Debug-Log\n");
    out.push_str(&format!(
        "Simulationen={simulations}  #Aktionen={n_actions}  Wurzelspieler={}  c={c}\n",
        state.players[state.current_player].name
    ));
    out.push_str(&format!("Spieler: P0={}  P1={}\n", state.players[0].name, state.players[1].name));
    match &nodes {
        Some(nodes) => {
            if let Some(best) = best_root_child(nodes) {
                let label = nodes[best]
                    .action
                    .as_ref()
                    .map(|sm| label_search_move(sm, Some(state)).1)
                    .unwrap_or_default();
                out.push_str(&format!(
                    "Gewaehlter Zug: {label}  (Wurzel-N={}, Knoten={})\n",
                    nodes[0].visits,
                    nodes.len()
                ));
            }
        }
        None => out.push_str("(Zustand nicht in der Drafting-Phase — kein MCTS)\n"),
    }
    out.push_str("==================================================\n");
    for l in lines {
        out.push_str(&l);
        out.push('\n');
    }
    out
}

/// Meistbesuchtes Wurzelkind (Tiebreak: Mittelwert Q).
fn best_root_child(nodes: &[Node]) -> Option<usize> {
    nodes[0].children.iter().copied().max_by(|&a, &b| {
        let qa = nodes[a].value / nodes[a].visits.max(1) as f64;
        let qb = nodes[b].value / nodes[b].visits.max(1) as f64;
        nodes[a]
            .visits
            .cmp(&nodes[b].visits)
            .then(qa.partial_cmp(&qb).unwrap_or(std::cmp::Ordering::Equal))
    })
}

/// Tiefe des Teilbaums unter `nid` (0 = Blatt) — Pendant zu `net_mcts::subtree_depth`,
/// beide delegieren an `search_common::subtree_depth`.
fn subtree_depth(nodes: &[Node], nid: usize) -> u32 {
    crate::search_common::subtree_depth(nodes, nid)
}

/// Typ, Beschreibung, Kategorie (für `.cat-*` in debug.html) und Move-Dict.
/// Wie viele Steine ein Take-Zug aus `state` entnimmt: alle der Farbe in der
/// Sonnen-Sektion bzw. (Mond) je Stapel mit passender Oberseite. Der globale
/// Mond-Zug (factory_id=None) summiert alle kleinen Fabriken + große Fabrik.
fn tiles_taken(state: &GameState, t: &crate::moves::TakeAction) -> usize {
    use crate::moves::TakeSource::*;
    let by_id = |fid: usize| state.factories.iter().find(|f| f.factory_id == fid);
    let moon_top = |f: &crate::factory::Factory, c: TileColor| {
        f.moon_stacks.iter().filter(|s| s.last() == Some(&c)).count()
    };
    match t.source {
        SmallFactorySun => t
            .factory_id
            .and_then(by_id)
            .map_or(0, |f| f.sun_tiles.iter().filter(|&&c| c == t.color).count()),
        LargeFactorySun => state.large_factory.sun_tiles.iter().filter(|&&c| c == t.color).count(),
        LargeFactoryMoon => state.large_factory.moon_pool.iter().filter(|&&c| c == t.color).count(),
        SmallFactoryMoon => match t.factory_id {
            Some(fid) => by_id(fid).map_or(0, |f| moon_top(f, t.color)),
            None => {
                let small: usize = state.factories.iter().map(|f| moon_top(f, t.color)).sum();
                let large = state.large_factory.moon_pool.iter().filter(|&&c| c == t.color).count();
                small + large
            }
        },
    }
}

/// `state=Some` blendet die Steinanzahl in die Stein-Beschreibung ein.
pub(crate) fn label_search_move(sm: &SearchMove, state: Option<&GameState>) -> (&'static str, String, &'static str, Value) {
    match sm {
        SearchMove::Draft(a) => match a {
            Action::Stone(m) => {
                let cat = if m.place.row_index < 0 { "penalty" } else { "row" };
                let dest = if m.place.row_index < 0 {
                    "Strafleiste".to_string()
                } else {
                    format!("Reihe {}", m.place.row_index + 1)
                };
                let src = match m.take.factory_id {
                    Some(id) => format!("F{id}"),
                    None => "GF".to_string(),
                };
                // Mit Zustand: Steinanzahl voranstellen und Füllstand der Zielreihe
                // NACH dem Zug anhängen ([gefüllt/Kapazität], wie im Game-Log) --
                // plus Überlauf-Hinweis, falls mehr Steine genommen werden, als in
                // die Reihe passen (Rest landet automatisch auf der Strafleiste,
                // siehe `execution::execute_place`/`add_to_penalty`).
                let (amount, fill) = match state {
                    Some(s) => {
                        let n = tiles_taken(s, &m.take);
                        let fill = if m.place.row_index >= 0 {
                            let row = &s.players[s.current_player].pattern_lines[m.place.row_index as usize];
                            let remaining = row.capacity().saturating_sub(row.tiles.len());
                            let placed = n.min(remaining);
                            let overflow = n.saturating_sub(remaining);
                            let filled = row.tiles.len() + placed;
                            let overflow_note =
                                if overflow > 0 { format!(" (+{overflow} Strafleiste)") } else { String::new() };
                            format!(" [{}/{}]{overflow_note}", filled, row.capacity())
                        } else {
                            String::new()
                        };
                        (format!("{n}× "), fill)
                    }
                    None => (String::new(), String::new()),
                };
                let desc = format!("{amount}Stein {} von {src} → {dest}{fill}", m.take.color.value());
                ("stone", desc, cat, action_to_dict(a))
            }
            Action::Dome(m) => (
                "dome",
                format!("Kuppel #{} → ({},{}) {}°", m.dome_tile_id, m.slot_row, m.slot_col, m.rotation),
                "dome",
                action_to_dict(a),
            ),
            Action::DrawStackPeek => (
                "dome_stack_peek",
                "Stapel: verdeckt ziehen".to_string(),
                "dome",
                action_to_dict(a),
            ),
            Action::DrawStack(m) => (
                "dome_stack",
                format!("Stapel → ({},{}) {}°", m.slot_row, m.slot_col, m.rotation),
                "dome",
                action_to_dict(a),
            ),
            Action::BonusChip(m) => (
                "bonus_chip",
                format!("Bonuschip F{}", m.factory_id),
                "chip",
                action_to_dict(a),
            ),
            Action::Pass => ("pass", "Pass".to_string(), "pass", action_to_dict(a)),
        },
    }
}

/// Serialisiert einen Knoten rekursiv (bis `depth_left`, je Knoten `top_k`
/// meistbesuchte Kinder) für das Debug-Baum-Panel.
fn serialize_node(nodes: &[Node], nid: usize, depth_left: u32, top_k: usize) -> Value {
    let node = &nodes[nid];
    let q = if node.visits > 0 { node.value / node.visits as f64 } else { 0.0 };
    let (typ, desc, cat, mv) = match &node.action {
        None => ("root", "Wurzel".to_string(), "pass", Value::Null),
        Some(sm) => {
            let parent_state = node.parent.map(|p| &nodes[p].state);
            label_search_move(sm, parent_state)
        }
    };
    let children = if depth_left > 0 && !node.children.is_empty() {
        let mut ch = node.children.clone();
        ch.sort_by(|a, b| nodes[*b].visits.cmp(&nodes[*a].visits));
        ch.truncate(top_k);
        ch.iter().map(|&c| serialize_node(nodes, c, depth_left - 1, top_k)).collect::<Vec<_>>()
    } else {
        Vec::new()
    };
    json!({
        "type": typ,
        "description": desc,
        "category": cat,
        "move": mv,
        "visits": node.visits,
        "q": q,
        "win_pct": q * 100.0,
        "depth": subtree_depth(nodes, nid),
        "player_who_acted": node.player_who_acted,
        "n_children": node.children.len(),
        "children": children,
    })
}

/// Anzeige-JSON einer Suchaktion (`{type, description, category, move}`).
pub fn search_move_json(sm: &SearchMove, state: Option<&GameState>) -> Value {
    let (typ, desc, cat, mv) = label_search_move(sm, state);
    json!({ "type": typ, "description": desc, "category": cat, "move": mv })
}

/// Wurzelkind-Statistik nach einer Suche: `(Drafting-Action, Besuche, Q)` je
/// Kind. Basis für die Self-Play-Policy-Targets (`crate::self_play`). Leer
/// außerhalb der Drafting-Phase.
pub fn root_child_stats<R: Rng + ?Sized>(
    state: &GameState,
    simulations: u32,
    c: f64,
    rng: &mut R,
) -> Vec<(Action, u32, f64)> {
    // Runde 5: informationsfreies Endspiel, siehe round5.rs -- exakte
    // Alpha-Beta-Wahl statt PUCT-Baum. Einzelner Eintrag mit Gewicht 1.0
    // (statt leer) macht `drafting_policy`s Zufalls-Fallback (bei leerer
    // Stats-Liste) nicht faelschlich fuer die Aktionswahl zustaendig.
    if crate::round5::applies(state) {
        return crate::round5::choose_action(state)
            .into_iter()
            .map(|a| (a, 1, 1.0))
            .collect();
    }
    let nodes = match build_tree(state, simulations, c, rng, None) {
        Some(n) => n,
        None => return Vec::new(),
    };
    nodes[0]
        .children
        .iter()
        .filter_map(|&cid| {
            let node = &nodes[cid];
            let q = if node.visits > 0 { node.value / node.visits as f64 } else { 0.0 };
            match &node.action {
                Some(SearchMove::Draft(a)) => Some((a.clone(), node.visits, q)),
                None => None,
            }
        })
        .collect()
}

/// Beste Drafting-Aktion für `state` (als SearchMove). None außerhalb Drafting.
pub fn search_action<R: Rng + ?Sized>(
    state: &GameState,
    simulations: u32,
    c: f64,
    rng: &mut R,
) -> Option<SearchMove> {
    if crate::round5::applies(state) {
        return crate::round5::choose_action(state).map(SearchMove::Draft);
    }
    let nodes = build_tree(state, simulations, c, rng, None)?;
    let best = best_root_child(&nodes)?;
    nodes[best].action.clone()
}

/// Wie [`search_action`], liefert zusätzlich ein debug.html-kompatibles
/// Analyse-Dict (Per-Zug-Statistik `moves[]` + serialisierter `tree`).
pub fn search_with_tree<R: Rng + ?Sized>(
    state: &GameState,
    simulations: u32,
    c: f64,
    rng: &mut R,
    max_depth: u32,
    top_k: usize,
    log: Option<&mut Vec<String>>,
) -> (Option<SearchMove>, Value) {
    if crate::round5::applies(state) {
        let (a, analysis) = crate::round5::choose_action_with_analysis(state);
        return (a.map(SearchMove::Draft), analysis);
    }
    let nodes = match build_tree(state, simulations, c, rng, log) {
        Some(n) => n,
        None => return (None, Value::Null),
    };
    let best = best_root_child(&nodes);
    let total_visits: u32 = nodes[0].children.iter().map(|&c| nodes[c].visits).sum();

    let mut child_ids = nodes[0].children.clone();
    child_ids.sort_by(|a, b| nodes[*b].visits.cmp(&nodes[*a].visits));

    let mut chosen_id: Option<usize> = None;
    let moves: Vec<Value> = child_ids
        .iter()
        .enumerate()
        .map(|(i, &cid)| {
            let node = &nodes[cid];
            let q = if node.visits > 0 { node.value / node.visits as f64 } else { 0.0 };
            let (typ, desc, cat, _mv) = match &node.action {
                Some(sm) => label_search_move(sm, Some(state)),
                None => ("?", "?".to_string(), "pass", Value::Null),
            };
            let is_chosen = best == Some(cid);
            if is_chosen {
                chosen_id = Some(i);
            }
            json!({
                "action_id": i,
                "type": typ,
                "description": desc,
                "category": cat,
                "net_prob": Value::Null,
                "net_prob_norm": Value::Null,
                "mcts_visits": node.visits,
                "mcts_share": if total_visits > 0 { node.visits as f64 / total_visits as f64 } else { 0.0 },
                "mcts_q": q,
                "mcts_win_pct": q * 100.0,
                "max_depth": subtree_depth(&nodes, cid),
                "shaping": Value::Null,
                "chosen": is_chosen,
            })
        })
        .collect();

    let analysis = json!({
        "current_player": nodes[0].player_who_acted,
        "ai_player": nodes[0].player_who_acted,
        "value": Value::Null,
        "win_pct": Value::Null,
        "has_net": false,
        "simulations": simulations,
        "num_actions": nodes[0].n_actions,
        "num_actions_considered": nodes[0].children.len(),
        "max_depth": subtree_depth(&nodes, 0),
        "ai_action": chosen_id,
        "moves": moves,
        "tree": serialize_node(&nodes, 0, max_depth, top_k),
    });

    let chosen = best.and_then(|cid| nodes[cid].action.clone());
    (chosen, analysis)
}

/// Kopfzeilen für ein MCTS-Log aus state + Analyse (für den geloggten KI-Zug).
pub fn search_log_header(state: &GameState, analysis: &Value) -> String {
    let sims = analysis["simulations"].as_u64().unwrap_or(0);
    let na = analysis["num_actions"].as_u64().unwrap_or(0);
    let chosen = analysis["moves"]
        .as_array()
        .and_then(|ms| ms.iter().find(|m| m["chosen"] == json!(true)))
        .and_then(|m| m["description"].as_str())
        .unwrap_or("?");
    format!(
        "MCTS-Debug-Log (KI-Zug)\nSimulationen={sims}  #Aktionen={na}  Wurzelspieler={}\nSpieler: P0={}  P1={}\nGewaehlter Zug: {chosen}\n==================================================\n",
        state.players[state.current_player].name,
        state.players[0].name,
        state.players[1].name
    )
}

/// Beste Drafting-Aktion (dünner Wrapper; None außerhalb Drafting bzw. wenn die
/// beste Wurzelaktion kein Drafting-Zug ist).
pub fn search_drafting_action<R: Rng + ?Sized>(
    state: &GameState,
    simulations: u32,
    c: f64,
    rng: &mut R,
) -> Option<Action> {
    match search_action(state, simulations, c, rng)? {
        SearchMove::Draft(a) => Some(a),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::state::setup_new_game;
    use rand::rngs::StdRng;
    use rand::SeedableRng;

    fn drafting_state(seed: u64) -> GameState {
        let mut rng = StdRng::seed_from_u64(seed);
        let mut s = setup_new_game(["P1".into(), "P2".into()], 0, &mut rng);
        for p in s.players.iter_mut() {
            p.start_tile_pending = false;
        }
        s
    }

    #[test]
    fn label_search_move_notes_penalty_overflow() {
        // Reihe 0 hat Kapazität 1 -- eine Fabrik mit >=2 gleichfarbigen
        // Sonnensteinen erzwingt einen Überlauf auf die Strafleiste, den das
        // Label jetzt direkt mitausweisen soll (Debug-Log-Anreicherung).
        use crate::moves::{Move, PlaceAction, TakeAction, TakeSource};
        let s = drafting_state(7);
        let (fidx, color, count) = s
            .factories
            .iter()
            .enumerate()
            .find_map(|(i, f)| {
                f.sun_colors().into_iter().find_map(|c| {
                    let n = f.sun_tiles.iter().filter(|&&t| t == c).count();
                    (n >= 2).then_some((i, c, n))
                })
            })
            .expect("Testfixtur braucht eine Fabrik mit >=2 gleichfarbigen Sonnensteinen");
        let f = &s.factories[fidx];
        let remaining: Vec<TileColor> = f.sun_tiles.iter().copied().filter(|&t| t != color).collect();
        let sm = SearchMove::Draft(Action::Stone(Move {
            take: TakeAction {
                source: TakeSource::SmallFactorySun,
                color,
                factory_id: Some(f.factory_id),
                moon_order: remaining,
            },
            place: PlaceAction { row_index: 0 },
        }));
        let (_, desc, _, _) = label_search_move(&sm, Some(&s));
        let overflow = count - 1;
        assert!(
            desc.contains(&format!("(+{overflow} Strafleiste)")),
            "Überlauf-Hinweis fehlt im Label: {desc}"
        );
    }

    #[test]
    fn returns_a_legal_drafting_action() {
        let s = drafting_state(7);
        let mut rng = StdRng::seed_from_u64(1);
        let action = search_drafting_action(&s, 200, DEFAULT_C, &mut rng).expect("Aktion");
        assert!(drafting_actions(&s).contains(&action), "MCTS-Aktion muss legal sein");
    }

    #[test]
    fn none_outside_drafting() {
        let mut s = drafting_state(7);
        s.phase = Phase::Tiling;
        let mut rng = StdRng::seed_from_u64(3);
        assert!(search_drafting_action(&s, 10, DEFAULT_C, &mut rng).is_none());
    }

    #[test]
    fn progressive_widening_grows_children_beyond_initial_wave() {
        // Frühes Drafting hat weit mehr als MAX_ACTIONS legale Züge.
        let s = drafting_state(7);
        assert!(valid_search_moves(&s).len() > MAX_ACTIONS);
        let mut rng = StdRng::seed_from_u64(2);
        let nodes = build_tree(&s, 300, DEFAULT_C, &mut rng, None).unwrap();
        // allowed = 10 + 2.5*sqrt(300) ≈ 53 → Wurzel muss > MAX_ACTIONS Kinder haben.
        assert!(
            nodes[0].children.len() > MAX_ACTIONS,
            "Widening sollte mehr als {MAX_ACTIONS} Kinder erzeugen, hat {}",
            nodes[0].children.len()
        );
    }

    #[test]
    fn root_children_all_get_at_least_one_forced_reply() {
        // Jeder (nicht-terminale) Wurzelkandidat muss mindestens einen eigenen
        // Kindknoten haben (simulierter Gegenzug), bevor die Wurzel einen NEUEN
        // Kandidaten anlegt -- sonst wäre der Vergleich zwischen Wurzelkindern
        // nicht "sauber" (nur der rohe Zustand direkt nach dem eigenen Zug,
        // ohne jede Gegner-Reaktion). Der Nachlauf am Ende von `build_tree`
        // schließt auch den zuletzt erzeugten Kandidaten nach, selbst wenn der
        // genau am Ende des Sim-Budgets entstand und nie erneut selektiert
        // wurde -- daher gilt die Garantie jetzt für ALLE Wurzelkinder.
        let s = drafting_state(7);
        let mut rng = StdRng::seed_from_u64(21);
        let nodes = build_tree(&s, 300, DEFAULT_C, &mut rng, None).unwrap();
        assert!(nodes[0].children.len() > 1, "Test braucht mehrere Wurzelkinder");
        for &cid in &nodes[0].children {
            if !nodes[cid].terminal {
                assert!(
                    !nodes[cid].children.is_empty(),
                    "Wurzelkind #{cid} hat keinen eigenen Kindknoten (Gegenzug nicht simuliert)"
                );
            }
        }
    }

    #[test]
    fn depth1_children_also_get_at_least_one_forced_reply() {
        // Die Force-Reply-Garantie gilt symmetrisch auch für Tiefe-1-Knoten
        // (Kind = 1. Gegnerzug): deren Kinder (Enkel, Tiefe 2) sollten
        // ebenfalls je einen eigenen Kindknoten (Urenkel) haben, bevor das
        // Tiefe-1-Kind weiterbreitert — sonst wären Enkel-Kandidaten anders
        // behandelt als Wurzelkandidaten (unsymmetrisch). Der Nachlauf schließt
        // auch hier den zuletzt erzeugten Enkel nach (selbst wenn das
        // Tiefe-1-Kind selbst nie wieder von UCB selektiert wurde, z.B. bei
        // niedrigem Score) — daher gilt die Garantie für ALLE Enkel, nicht nur
        // "alle außer dem letzten".
        let s = drafting_state(7);
        let mut rng = StdRng::seed_from_u64(33);
        let nodes = build_tree(&s, 600, DEFAULT_C, &mut rng, None).unwrap();
        let mut checked_any = false;
        for &root_child in &nodes[0].children {
            let grandkids = &nodes[root_child].children;
            if nodes[root_child].terminal || grandkids.is_empty() {
                continue;
            }
            checked_any = true;
            for &gc in grandkids {
                if !nodes[gc].terminal {
                    assert!(
                        !nodes[gc].children.is_empty(),
                        "Enkel #{gc} (unter Kind #{root_child}) hat keinen eigenen Kindknoten"
                    );
                }
            }
        }
        assert!(checked_any, "Test braucht mind. ein Wurzelkind mit Enkeln");
    }

    #[test]
    fn nachlauf_closed_nodes_have_even_visit_counts() {
        // Für jeden nicht-terminalen Knoten X gilt strukturell f(X) = 1
        // (eigene Erstellung/Eval) + f(letztes Kind) + ... -- ein Knoten, der
        // GENAU einmal per Nachlauf geschlossen wurde (ein einzelnes,
        // unerforschtes Antwort-Kind angehängt bekam), landet also bei
        // f(Antwort-Kind) = 1 (eigene Erstellung) + 1 (Nachlauf-Antwort) = 2.
        // Einfacher Sichtcheck im Debug-Log: jeder per NACHLAUF geschlossene
        // Knoten muss eine GERADE Visit-Zahl zeigen.
        let s = drafting_state(7);
        let mut rng = StdRng::seed_from_u64(21);
        let mut lines = Vec::new();
        let nodes = build_tree(&s, 300, DEFAULT_C, &mut rng, Some(&mut lines)).unwrap();
        let mut checked_any = false;
        for line in &lines {
            if !line.contains("NACHLAUF") {
                continue;
            }
            let after_arrow = line.split("→ #").nth(1).expect("NACHLAUF-Zeile ohne '→ #'");
            let closed_id: usize = after_arrow
                .chars()
                .take_while(|c| c.is_ascii_digit())
                .collect::<String>()
                .parse()
                .expect("NACHLAUF-Zeile ohne Knoten-ID nach '→ #'");
            checked_any = true;
            assert_eq!(
                nodes[closed_id].visits % 2,
                0,
                "per NACHLAUF geschlossener Knoten #{closed_id} hat ungerade Visits ({})",
                nodes[closed_id].visits
            );
        }
        assert!(checked_any, "Test braucht mind. einen NACHLAUF-Fund (ggf. Seed anpassen)");
    }

    #[test]
    fn normalize_score_stays_distinguishable_over_typical_score_range() {
        // Anders als die alte Differenz-Sigmoid (scale=2.0 bei >50 Aktionen,
        // sättigte schon bei Diffs von ~20-30 Punkten für BEIDE Spieler
        // gleichzeitig) bleibt die absolute Score-Normalisierung über den
        // gesamten typischen Punktebereich (0–90+) klar unterscheidbar und
        // monoton — auch bei bereits großem Abstand zum Gegner (den diese
        // Funktion gar nicht mehr kennt) bleibt "mehr eigene Punkte" ein
        // Signal.
        let v0 = normalize_score(0.0);
        let v45 = normalize_score(45.0);
        let v90 = normalize_score(90.0);
        assert!(v0 < v45 && v45 < v90, "muss streng monoton steigend sein");
        assert!(v45 > v0 + 0.1, "45 Punkte sollten sich deutlich von 0 abheben");
        assert!(v90 > v45 + 0.02, "90 Punkte sollten noch messbar über 45 liegen (nicht schon gesättigt)");
    }

    #[test]
    fn does_not_dump_to_floor_early() {
        let s = drafting_state(11);
        let mut rng = StdRng::seed_from_u64(4);
        let action = search_drafting_action(&s, 400, DEFAULT_C, &mut rng).expect("Aktion");
        if let Action::Stone(m) = &action {
            assert_ne!(m.place.row_index, -1, "MCTS sollte nicht auf die Strafleiste werfen");
        }
    }

    #[test]
    fn search_does_not_advance_round() {
        // Die Suche darf den Rundenwechsel nie betreten (Rundennummer bleibt).
        let s = drafting_state(7);
        let round_before = s.round_number;
        let mut rng = StdRng::seed_from_u64(9);
        let _ = search_drafting_action(&s, 300, DEFAULT_C, &mut rng);
        assert_eq!(s.round_number, round_before);
    }

    #[test]
    fn search_action_none_for_tiling_root() {
        // Tiling wird NICHT mehr im MCTS gesucht (löst der DFS-Solver).
        let mut s = drafting_state(7);
        s.phase = Phase::Tiling;
        let mut rng = StdRng::seed_from_u64(5);
        assert!(search_action(&s, 150, DEFAULT_C, &mut rng).is_none());
    }

    #[test]
    fn search_with_tree_produces_valid_tree() {
        let s = drafting_state(7);
        let mut rng = StdRng::seed_from_u64(6);
        let (chosen, analysis) = search_with_tree(&s, 300, DEFAULT_C, &mut rng, 3, 8, None);
        assert!(chosen.is_some());
        let tree = &analysis["tree"];
        assert!(tree["children"].as_array().unwrap().len() > 0);
        // Wurzelkinder ≤ top_k im Baum.
        assert!(tree["children"].as_array().unwrap().len() <= 8);
        // moves[] vorhanden, Summe der Visits ≈ Simulationen (jede Sim besucht
        // Wurzel) PLUS der Nachlauf-Sims, die offene Wurzel-/Tiefe-1-Enden
        // nachträglich schließen (siehe FORCE-REPLY-Nachlauf in build_tree) —
        // daher keine scharfe Obergrenze bei genau 300 mehr, nur eine
        // großzügige, um echte Regressionen (z.B. unbeschränkte Kaskaden)
        // trotzdem zu erkennen.
        let moves = analysis["moves"].as_array().unwrap();
        assert!(!moves.is_empty());
        let sum: u64 = moves.iter().map(|m| m["mcts_visits"].as_u64().unwrap()).sum();
        assert!(sum >= 300 && sum <= 450, "Visit-Summe {sum} ~ 300 (+ Nachlauf)");
    }

    #[test]
    fn dynamic_sims_scales_with_actions() {
        // Mehr Aktionen → mehr Sims; Grenzen [base, base*5] eingehalten.
        assert_eq!(dynamic_sims(300, 0), 300);
        assert!(dynamic_sims(300, 64) > 300); // 300 + 8*25 = 500
        assert_eq!(dynamic_sims(300, 64), 500);
        assert!(dynamic_sims(100, 100_000) <= 500); // clamp auf base*5
    }

    #[test]
    fn search_log_text_contains_all_phases() {
        let s = drafting_state(7);
        let mut rng = StdRng::seed_from_u64(8);
        // Mit dem erzwungenen Gegnerzug "kostet" jeder Wurzelkandidat jetzt
        // effektiv 2 statt 1 Sim (eigener Zug + erzwungene Antwort), bevor die
        // Wurzel weiterbreitert oder selektiert -- 300 statt 50 Sims, damit
        // die Wurzel ihr Widening-Budget innerhalb des Tests sicher ausschöpft.
        let log = search_log_text(&s, 300, DEFAULT_C, &mut rng);
        assert!(log.contains("=== Sim 1/300 ==="));
        assert!(log.contains("EXPAND"));
        assert!(log.contains("EVAL"));
        assert!(log.contains("BACKPROP"));
        assert!(log.contains("FORCE-REPLY"), "erzwungener Gegnerzug sollte im Log auftauchen");
        // Bei genug Sims wird auch selektiert (Abstieg).
        assert!(log.contains("SELECT"));
    }
}
