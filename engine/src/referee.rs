//! Wave-3-Referee (`PREREG_agent_encapsulation.md` par.8): haelt die Live-
//! Partie fuer den Prozess-isolierten Champion-Vergleich (gefrorenes
//! Artefakt in einem eigenen Worker-Prozess gegen die aktuelle Engine).
//!
//! ABSICHTLICH keine zweite Spielschleife: jede Methode ruft dieselben
//! Rust-Funktionen wie `self_play::run_net_vs_net_arena`s Arena-Pfad
//! (Startplatzierung + Drafting + Tiling, `steps`-Zaehler,
//! `derive_search_seed`-Ableitung), nur einzeln von aussen angestossen --
//! eine Seite kann so extern (per Prozessgrenze) entscheiden, ohne dass der
//! GameState selbst je verlassen muss. Nur die Drafting-Entscheidung der
//! externen Seite quert die Prozessgrenze (`net_arena_choice_state_json` in
//! `lib.rs`, Worker-seitig); Startplatzierung und Tiling loest DIESER
//! Referee-Prozess immer selbst auf (mit dem Modell der jeweiligen Seite,
//! aber dem Code der AKTUELLEN Engine) -- "Regel-Autoritaet bleibt bei der
//! aktuellen Engine" (par.8), das gilt fuer Tiling-Solver-Fixes genauso wie
//! fuer Drafting-Regeln.

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use rand::rngs::StdRng;
use rand::SeedableRng;
use serde_json::{json, Value};

use crate::game::{apply_start_placement, drafting_actions, Game, TilingMove};
use crate::moves::Action;
use crate::net::Net;
use crate::net_mcts::{derive_search_seed, SearchConfig};
use crate::round_end::apply_bonus_chips_with;
use crate::scoring::sample_valid_scoring_ids;
use crate::self_play::{apply_chosen_action, choose_start_placement, net_arena_choose_action, resolve_tiling_step};
use crate::serialize::{action_to_dict, state_to_json_exact};
use crate::tile::TileColor;

/// PREREG_agent_encapsulation.md par.8 (Welle 3): DIE Auswahl-Logik hinter
/// dem "Stellung rein, Zug raus"-Protokoll -- gemeinsam genutzt von
/// `lib.rs::net_arena_choice_state_json` (Einzelaufruf, kein Cache, fuer
/// `golden_probe.json`) UND [`FrozenWorkerEngine`] (gecachtes Modell, fuer
/// den persistenten Worker-Prozess). Reiner Auszug -- KEINE zweite Kopie der
/// Auswahl-/Dome-Nachzieh-Logik.
///
/// NUR fuer Drafting-Entscheidungen (harter Fehler sonst) -- Start-
/// platzierung und Tiling loest der Referee-Prozess selbst auf.
///
/// Kuppelplatzierung (Sonderfall, GEMESSEN im Kernbeweis-Vorlauf
/// 2026-08-23): `pending_dome_choice` (Stufe-2-Rotationswahl) ist in
/// `state_json` NICHT sichtbar (dokumentierte, vorbestehende Naeherung,
/// `serialize.rs`-Kommentar "Kategorie 3"). Wird `ChooseDomeSlot` gewaehlt,
/// wird die Rotationswahl HIER, noch im selben Aufruf, auf einer lokalen
/// Kopie nachgezogen (derselbe fortlaufende `rng`-Strom) -- die Rueckgabe
/// ist dann der nach aussen ATOMARE Zug (Tile+Slot+Rotation in einem Dict),
/// exakt wie `PyGame::apply_dome`/server.py es dem Menschen gegenueber
/// schon tun. `RefereeGame::drafting_apply_external` erkennt das additive
/// `rotation`-Feld und wendet beide Stufen an.
pub(crate) fn choose_drafting_action_json(
    net: &Net,
    search_config: &SearchConfig,
    state_json: &str,
    sims: u32,
    c_puct: f64,
    seed: u64,
    rot_seed: u64,
) -> PyResult<Value> {
    // KERNBEWEIS-FIX FORK A (PREREG_agent_encapsulation.md par.8b,
    // Nutzer-Entscheid 2026-08-23): `state_json` traegt jetzt additiv die
    // EXAKTEN Reihenfolgen der verdeckten Sammlungen (Beutel/Turm/
    // Kuppelstapel/Bonuschip-Pool, `serialize::state_to_json_exact`,
    // erzeugt von `RefereeGame::state_json`). `json_to_state_exact` liest
    // sie als PFLICHTFELDER (harter Fehler bei Fehlen, kein stiller
    // Rueckfall auf Zaehler-Rekonstruktion). Der fruehere, domain-getrennte
    // Rekonstruktions-RNG (par.8a-Fix, `RECON_DISTINGUISHER`) entfaellt
    // dadurch ERSATZLOS: er loeste ausschliesslich das Vorbelastungs-Problem
    // einer RNG-basierten Neumischung, die es jetzt fuer diese vier Felder
    // gar nicht mehr gibt (weniger bewegliche Teile). Der Such-RNG (`rng`
    // unten) startet weiterhin FRISCH aus `seed` -- `seed` ist hier bereits
    // `derive_search_seed(game_seed, steps)` (siehe `RefereeGame::
    // pending_search_seed`), also byte-identische Ableitung zum In-Process-Pfad.
    //
    // KERNBEWEIS-FIX par.8c (2026-08-23): die zweistufige Kuppel-Entscheidung
    // (ChooseDomeSlot -> ChooseDomeRotation) lief bisher auf EINEM `rng`-
    // Strom -- der In-Process-Pfad (`RefereeGame::
    // drafting_decide_and_apply_inprocess`, je Entscheidungsstufe EIN
    // eigener Aufruf) zieht dagegen je Stufe einen FRISCHEN
    // `StdRng::seed_from_u64(derive_search_seed(game_seed, steps))`, mit
    // `steps` bereits um 1 weitergezaehlt fuer die Rotationsstufe (belegt in
    // `self_play.rs::unified_game_loop`, `steps += 1` NACH jeder einzelnen
    // Drafting-Entscheidung, VOR der Seed-Ableitung der naechsten). `rot_seed`
    // ist deshalb ein ZWEITER, eigener Parameter -- kein Default-Fallback auf
    // den alten Ein-Strom-Modus, alle Aufrufer liefern ihn hart mit (siehe
    // `RefereeGame::pending_rotation_search_seed`).
    let parsed: Value = serde_json::from_str(state_json)
        .map_err(|e| PyValueError::new_err(format!("state_json: JSON-Parse-Fehler: {e}")))?;
    let state = crate::serialize::json_to_state_exact(&parsed).map_err(PyValueError::new_err)?;
    if state.phase != Phase::Drafting || state.players.iter().any(|p| p.start_tile_pending) {
        return Err(PyValueError::new_err(
            "choose_drafting_action_json: state ist keine Drafting-Entscheidung (Startplatzierung/Tiling \
             loest der Referee-Prozess auf, nicht der Worker).",
        ));
    }
    let actions = drafting_actions(&state);
    let mut rng = StdRng::seed_from_u64(seed);
    let chosen = net_arena_choose_action(net, &state, &actions, &mut rng, sims, c_puct, true, search_config);
    let mut action = action_to_dict(&chosen);
    if let Action::ChooseDomeSlot(_) = &chosen {
        let follow_up_state = {
            let mut g = Game { state: state.clone() };
            g.apply_drafting(&chosen).map_err(PyValueError::new_err)?;
            g.state
        };
        let rot_actions = drafting_actions(&follow_up_state);
        let mut rot_rng = StdRng::seed_from_u64(rot_seed);
        let rot_chosen = net_arena_choose_action(
            net, &follow_up_state, &rot_actions, &mut rot_rng, sims, c_puct, true, search_config,
        );
        if let Action::ChooseDomeRotation(rot) = rot_chosen {
            if let Some(obj) = action.as_object_mut() {
                obj.insert("rotation".to_string(), json!(rot));
            }
        }
    }
    Ok(action)
}

/// Wave-3-Worker-Engine: laedt Modell+Spec EINMAL (Konstruktor), `choose()`
/// je Zug OHNE Neuladen -- Performance-Fix, gemessen 2026-08-23 (siehe
/// `RefereeGame::nets`-Kommentar: ohne Cache schaffte ein 3-Partien-
/// Testlauf mit 20 Minuten Wall-Clock nicht mal die erste Partie).
/// `tools/frozen_champion_worker.py` haelt GENAU eine Instanz ueber die
/// gesamte Prozess-Laufzeit.
#[pyclass]
pub struct FrozenWorkerEngine {
    net: Net,
    search_config: SearchConfig,
}

#[pymethods]
impl FrozenWorkerEngine {
    #[new]
    #[pyo3(signature = (model_path, spec=None))]
    fn new(model_path: String, spec: Option<String>) -> PyResult<Self> {
        let net = load_net(&model_path)?;
        let search_config = crate::resolve_search_config(spec)?;
        Ok(FrozenWorkerEngine { net, search_config })
    }

    /// `state_json` rein -- `{"action": ..., "value": null}`-JSON-String
    /// raus (identisches Schema zu `lib.rs::net_arena_choice_state_json`).
    /// `rot_seed` (par.8c-Fix): eigener Seed fuer die Kuppel-Rotationsstufe,
    /// harter Parameter -- siehe `choose_drafting_action_json`-Doku.
    fn choose(&self, state_json: String, sims: u32, c_puct: f64, seed: u64, rot_seed: u64) -> PyResult<String> {
        let action =
            choose_drafting_action_json(&self.net, &self.search_config, &state_json, sims, c_puct, seed, rot_seed)?;
        let value: Option<f32> = None;
        Ok(json!({ "action": action, "value": value }).to_string())
    }
}
use crate::state::Phase;
use crate::tiling_solver::TilingStep;

fn load_net(path: &str) -> PyResult<Net> {
    Net::load_auto(path).map_err(|e| PyValueError::new_err(format!("Netz konnte nicht geladen werden: {e}")))
}

/// GEMESSENER Befund (Kernbeweis-Vorlauf, 2026-08-23): `net_mcts.rs`s Suche
/// (`unique_moon_orders`, Zeile ~2015) durchsucht bei Sonnenzuegen aus
/// kleinen Fabriken MEHRERE `moon_order`-Permutationen der restlichen
/// Steine als eigene Suchkinder (Moon-Order-Kopf) -- die gewaehlte Aktion
/// traegt deshalb haeufig NICHT die eine kanonische Reihenfolge, die
/// `game::drafting_actions`/`generate_valid_moves` als EINZIGEN Kandidaten
/// auflistet (dort bleibt `moon_order` unveraendert die Fabrik-Ausgangs-
/// reihenfolge). Beide sind nach `validation.rs::validate_place`
/// (Multiset-Vergleich) gleich LEGAL. Der exakte Dict-Vergleich in
/// `drafting_apply_external` war deshalb zu eng -- diese Funktion vergleicht
/// `stone`-Aktionen OHNE `moon_order` und liefert danach getrennt die
/// Multiset-Pruefung.
fn stone_dict_without_moon_order(d: &Value) -> Value {
    let mut d = d.clone();
    if let Some(obj) = d.as_object_mut() {
        obj.remove("moon_order");
    }
    d
}

/// Multiset-Gleichheit zweier Farb-String-Listen (Reihenfolge egal).
fn moon_order_multiset_eq(a: &[String], b: &[String]) -> bool {
    if a.len() != b.len() {
        return false;
    }
    let mut a_sorted = a.to_vec();
    let mut b_sorted = b.to_vec();
    a_sorted.sort();
    b_sorted.sort();
    a_sorted == b_sorted
}

#[pyclass]
pub struct RefereeGame {
    game: Game,
    /// "Echte" Spielzustands-RNG (Startplatzierung/Beutel-Refill bei
    /// `EndTiling`) -- exakt dieselbe Rolle wie `unified_game_loop`s `rng`.
    /// Such-Entscheide ziehen NICHT hieraus (siehe `pending_search_seed`).
    rng: StdRng,
    game_seed: u64,
    /// Alle-Schritte-Zaehler (Startplatzierung + Drafting + Tiling), exakt
    /// die `steps`-Konvention aus `unified_game_loop` (Arena-Pfad,
    /// `seed_from_steps=true`) -- Grundlage jeder `derive_search_seed`-
    /// Ableitung.
    steps: u32,
    /// Modell-Cache je Pfad (Performance-Fix, gemessen 2026-08-23: OHNE
    /// Cache laedt `Net::load_auto` das ~9 MB ONNX-Modell bei JEDER
    /// Drafting-/Tiling-Entscheidung neu -- ein 3-Partien-Testlauf mit 20
    /// Minuten Wall-Clock schaffte nicht mal die erste Partie. Arena-Pfade
    /// (`self_play.rs::run_net_vs_net_arena`) laden `Net` ebenfalls nur
    /// EINMAL pro Match, dieselbe Erwartung gilt hier.
    nets: std::collections::HashMap<String, Net>,
}

/// Freie Funktion statt Methode (NICHT `&mut self`): so kann der Aufrufer
/// diesen Cache-Zugriff auf `self.nets` beschraenken und `self.game`/
/// `self.steps` in DERSELBEN Anweisung noch lesen -- ein Methodenaufruf mit
/// `&mut self` wuerde den Borrow-Checker den ganzen `self` sperren lassen.
fn load_cached<'a>(nets: &'a mut std::collections::HashMap<String, Net>, path: &str) -> PyResult<&'a Net> {
    if !nets.contains_key(path) {
        let net = load_net(path)?;
        nets.insert(path.to_string(), net);
    }
    Ok(nets.get(path).expect("gerade eingefuegt"))
}

#[pymethods]
impl RefereeGame {
    /// Baut den Startzustand GENAU wie `run_net_vs_net_arena`s `play`-Closure
    /// (`sample_valid_scoring_ids(3, &mut rng)` dann `Game::start`, derselbe
    /// `rng`-Strom) -- gleicher `seed` -> gleicher Startzustand.
    #[new]
    #[pyo3(signature = (names, first_player, seed, scoring_ids=None))]
    fn new(names: (String, String), first_player: usize, seed: u64, scoring_ids: Option<Vec<usize>>) -> Self {
        let mut rng = StdRng::seed_from_u64(seed);
        let ids = scoring_ids.unwrap_or_else(|| sample_valid_scoring_ids(3, &mut rng));
        let game = Game::start([names.0, names.1], first_player, ids, &mut rng);
        RefereeGame { game, rng, game_seed: seed, steps: 0, nets: std::collections::HashMap::new() }
    }

    /// Fork A (par.8b): exakte Variante -- traegt zusaetzlich zu den
    /// bestehenden `state_to_json`-Feldern die vier geordneten verdeckten
    /// Sammlungen (Beutel/Turm/Kuppelstapel/Bonuschip-Pool), die der Worker
    /// jetzt PFLICHT konsumiert (`choose_drafting_action_json`).
    fn state_json(&self) -> String {
        state_to_json_exact(&self.game.state, true).to_string()
    }
    fn phase(&self) -> &'static str {
        self.game.state.phase.as_str()
    }
    fn current_player(&self) -> usize {
        self.game.state.current_player
    }
    fn round_number(&self) -> u32 {
        self.game.state.round_number
    }
    fn scores(&self) -> (i32, i32) {
        (self.game.state.players[0].score, self.game.state.players[1].score)
    }
    fn steps(&self) -> u32 {
        self.steps
    }
    fn game_seed(&self) -> u64 {
        self.game_seed
    }
    /// Voller, UNGEFENSTERTER Partie-Log (`game.state.log`, wie
    /// `run_net_vs_net_arena`s `log_games=true`-Feld `log`) -- fuer den
    /// Kernbeweis-Vergleich (par.8, par.5c): `state_json()`s `log`-Feld ist
    /// UI-gefenstert (`take(30)`, `serialize.rs`), dieser hier nicht.
    fn full_log(&self) -> Vec<String> {
        self.game.state.log.clone()
    }

    /// Such-Seed, den die NAECHSTE Drafting-Entscheidung braucht (egal ob
    /// in-process oder extern via Worker) -- exakt
    /// `derive_search_seed(game_seed, steps)`, derselbe Ableitungspfad wie
    /// `unified_game_loop` (Arena-Pfad).
    fn pending_search_seed(&self) -> u64 {
        derive_search_seed(self.game_seed, self.steps as u64)
    }

    /// Such-Seed fuer die Kuppel-ROTATIONSSTUFE, FALLS die anstehende
    /// Drafting-Entscheidung eine Kuppelplatzierung ist (ChooseDomeSlot ->
    /// ChooseDomeRotation, zwei eigene Entscheidungsstufen). Steps-Arithmetik
    /// IN-PROCESS-IDENTISCH belegt (`self_play.rs::unified_game_loop`,
    /// `steps += 1` NACH jeder einzelnen Drafting-Entscheidung, VOR der
    /// Seed-Ableitung der naechsten -- dasselbe Muster reproduziert
    /// `drafting_decide_and_apply_inprocess` bei zwei aufeinanderfolgenden
    /// Aufrufen: Stufe 1 nutzt `steps`, Stufe 2 danach `steps + 1`, weil
    /// dieser hier NOCH VOR dem ersten `apply` aufgerufen wird, `self.steps`
    /// also noch den Stand VOR der Slot-Entscheidung traegt -- KERNBEWEIS-FIX
    /// par.8c, PREREG_agent_encapsulation.md).
    fn pending_rotation_search_seed(&self) -> u64 {
        derive_search_seed(self.game_seed, (self.steps + 1) as u64)
    }

    /// Loest Startplatzierung und Tiling automatisch auf (Wortlaut-Kopie der
    /// Arena-Logik aus `unified_game_loop`, non-recording Zweig -- KEINE neue
    /// Spiellogik), bis eine Drafting-Entscheidung ansteht oder die Partie
    /// das Ende erreicht.
    ///
    /// `model_path_p{0,1}`: Tiling-Netz je Spieler (Board-Zuordnung wie
    /// `play_net_vs_net_game`: Spieler 0 -> `model_path_p0`, Spieler 1 ->
    /// `model_path_p1`); `None` = reiner DFS-Solver (Bestandsverhalten).
    ///
    /// Rueckgabe: `"drafting"` (Entscheidung noetig, `current_player()` sagt
    /// wer), `"game_over"` (Runde 5 fertig -- `finalize_scoring()` als
    /// naechstes aufrufen), oder `"stuck"` (Deadlock -- laut Bestandscode nie
    /// erwartet, siehe `unified_game_loop`s `None => break`-Zweige; wird hier
    /// NICHT verschluckt, sondern woertlich gemeldet).
    fn advance_to_decision(
        &mut self, model_path_p0: Option<String>, model_path_p1: Option<String>,
    ) -> PyResult<String> {
        loop {
            match self.game.state.phase {
                Phase::StartPlacement | Phase::Drafting => {
                    if self.game.state.players.iter().any(|p| p.start_tile_pending) {
                        let first = self.game.state.current_player;
                        let non_starter = 1 - first;
                        let pi = if self.game.state.players[non_starter].start_tile_pending {
                            non_starter
                        } else if self.game.state.players[first].start_tile_pending {
                            first
                        } else {
                            return Ok("stuck".to_string());
                        };
                        match choose_start_placement(&self.game.state, pi) {
                            Some((tid, r, c2, rot)) => {
                                let _ = apply_start_placement(&mut self.game.state, pi, tid, r, c2, rot);
                            }
                            None => return Ok("stuck".to_string()),
                        }
                        self.steps += 1;
                    } else if self.game.state.phase == Phase::Drafting {
                        return Ok("drafting".to_string());
                    } else {
                        return Ok("stuck".to_string());
                    }
                }
                Phase::Tiling => {
                    let pi = self.game.state.current_player;
                    let model_path = if pi == 0 { &model_path_p0 } else { &model_path_p1 };
                    let net = match model_path {
                        Some(p) => Some(load_cached(&mut self.nets, p)?),
                        None => None,
                    };
                    let step = resolve_tiling_step(&self.game.state, pi, net);
                    match step {
                        TilingStep::Place(ta) => {
                            let _ = self.game.apply_single_tiling(pi, &ta);
                        }
                        TilingStep::Chips { row, chips } => {
                            apply_bonus_chips_with(&mut self.game.state.players[pi], row, &chips);
                        }
                        TilingStep::End => {
                            let _ = self.game.apply_tiling(&TilingMove::EndTiling { player: pi }, &mut self.rng);
                        }
                    }
                    self.steps += 1;
                }
                _ => return Ok("game_over".to_string()),
            }
        }
    }

    /// Seite IN-PROCESS: Netzsuche + Anwenden fuer die aktuell anstehende
    /// Drafting-Entscheidung, mit beliebigem Modell/Spec -- ruft
    /// `net_arena_choose_action` GENAU wie `NetArenaAgent::decide`
    /// (par.8-Refactor in `self_play.rs`, keine zweite Auswahl-Logik-Kopie).
    /// Gibt die angewandte Aktion zurueck (`serialize::action_to_dict`-Schema).
    fn drafting_decide_and_apply_inprocess(
        &mut self, model_path: String, spec: Option<String>, sims: u32, c_puct: f64,
    ) -> PyResult<String> {
        if self.game.state.phase != Phase::Drafting || self.game.state.players.iter().any(|p| p.start_tile_pending) {
            return Err(PyValueError::new_err(
                "drafting_decide_and_apply_inprocess: keine Drafting-Entscheidung anstehend",
            ));
        }
        let search_config = crate::resolve_search_config(spec)?;
        let actions = drafting_actions(&self.game.state);
        let mut search_rng = StdRng::seed_from_u64(derive_search_seed(self.game_seed, self.steps as u64));
        let chosen = {
            let net = load_cached(&mut self.nets, &model_path)?;
            net_arena_choose_action(net, &self.game.state, &actions, &mut search_rng, sims, c_puct, true, &search_config)
        };
        let dict = action_to_dict(&chosen);
        apply_chosen_action(&mut self.game, chosen).map_err(PyValueError::new_err)?;
        self.steps += 1;
        Ok(dict.to_string())
    }

    /// Seite EXTERN (Worker): wendet die vom Worker gewaehlte Aktion an --
    /// HART validiert gegen die aktuell legalen Aktionen (exakter Vergleich
    /// ueber `serialize::action_to_dict`, dieselbe Funktion, die der Worker
    /// zur Auswahl bekommt, siehe `lib.rs::net_arena_choice_state_json`) --
    /// eine illegale/unbekannte Aktion ist ein Fehler, keine stille
    /// Ersatzwahl (par.8: "Regel-Autoritaet").
    ///
    /// SONDERFALL Kuppelplatzierung: `pending_dome_choice` (Stufe-2-
    /// Rotationswahl) ist in `state_json` NICHT sichtbar (dokumentierte
    /// Naeherung, `serialize.rs`), der Worker antwortet deshalb bei einer
    /// `dome_display`-Wahl mit dem NACH AUSSEN ATOMAREN Dict INKLUSIVE
    /// `rotation` (siehe `lib.rs::net_arena_choice_state_json`). Hier werden
    /// dann BEIDE Stufen angewandt -- Stufe 1 exakt matchend wie sonst,
    /// Stufe 2 (`ChooseDomeRotation`) gegen die dann anstehenden legalen
    /// Kandidaten geprueft, genau wie `PyGame::apply_dome`s zwei
    /// aufeinanderfolgende `apply_drafting`-Aufrufe.
    fn drafting_apply_external(&mut self, action_json: String) -> PyResult<()> {
        if self.game.state.phase != Phase::Drafting || self.game.state.players.iter().any(|p| p.start_tile_pending) {
            return Err(PyValueError::new_err("drafting_apply_external: keine Drafting-Entscheidung anstehend"));
        }
        let parsed: Value = serde_json::from_str(&action_json)
            .map_err(|e| PyValueError::new_err(format!("action_json: JSON-Parse-Fehler: {e}")))?;

        let is_dome_with_rotation =
            parsed.get("type").and_then(|t| t.as_str()) == Some("dome_display") && parsed.get("rotation").is_some();
        let match_target = if is_dome_with_rotation {
            let mut stripped = parsed.clone();
            if let Some(obj) = stripped.as_object_mut() {
                obj.remove("rotation");
            }
            stripped
        } else {
            parsed.clone()
        };

        let actions = drafting_actions(&self.game.state);
        let is_stone = match_target.get("type").and_then(|t| t.as_str()) == Some("stone");
        let found = if is_stone {
            // Sonderfall Moon-Order (siehe `stone_dict_without_moon_order`-
            // Doku): erst OHNE `moon_order` matchen, dann die eingereichte
            // Reihenfolge als Multiset gegen den Kandidaten pruefen -- eine
            // andere, aber gueltige Permutation ist LEGAL, wird aber nicht
            // stillschweigend durch die kanonische Reihenfolge ersetzt,
            // sondern EXAKT wie eingereicht angewandt (nach Pruefung).
            let target_stripped = stone_dict_without_moon_order(&match_target);
            let submitted_order: Vec<String> = match_target
                .get("moon_order")
                .and_then(|v| v.as_array())
                .map(|arr| arr.iter().filter_map(|x| x.as_str().map(str::to_string)).collect())
                .unwrap_or_default();
            actions.into_iter().find_map(|a| {
                let d = action_to_dict(&a);
                if stone_dict_without_moon_order(&d) != target_stripped {
                    return None;
                }
                let candidate_order: Vec<String> = d
                    .get("moon_order")
                    .and_then(|v| v.as_array())
                    .map(|arr| arr.iter().filter_map(|x| x.as_str().map(str::to_string)).collect())
                    .unwrap_or_default();
                if !moon_order_multiset_eq(&candidate_order, &submitted_order) {
                    return None;
                }
                if candidate_order == submitted_order {
                    return Some(a);
                }
                // Gueltige, aber ANDERE Permutation -- die Aktion mit der
                // EINGEREICHTEN Reihenfolge neu bauen (nur `moon_order`
                // ersetzt, alle anderen Felder identisch zum Kandidaten).
                if let Action::Stone(m) = a {
                    let parsed_colors: Option<Vec<TileColor>> =
                        submitted_order.iter().map(|s| TileColor::from_value(s)).collect();
                    parsed_colors.map(|order| {
                        let mut m2 = m;
                        m2.take.moon_order = order;
                        Action::Stone(m2)
                    })
                } else {
                    None
                }
            })
        } else {
            actions.into_iter().find(|a| action_to_dict(a) == match_target)
        };
        let stage1 = match found {
            Some(a) => a,
            None => {
                return Err(PyValueError::new_err(format!(
                    "Worker-Aktion ist in dieser Stellung nicht legal (Regel-Autoritaet verweigert): {match_target}"
                )))
            }
        };
        apply_chosen_action(&mut self.game, stage1).map_err(PyValueError::new_err)?;
        self.steps += 1;

        if is_dome_with_rotation {
            let wanted_rot = parsed.get("rotation").and_then(|r| r.as_u64());
            let rot_actions = drafting_actions(&self.game.state);
            let rot_found = rot_actions.into_iter().find(|a| match a {
                crate::moves::Action::ChooseDomeRotation(r) => Some(u64::from(*r)) == wanted_rot,
                _ => false,
            });
            match rot_found {
                Some(a) => {
                    apply_chosen_action(&mut self.game, a).map_err(PyValueError::new_err)?;
                    self.steps += 1;
                }
                None => {
                    return Err(PyValueError::new_err(format!(
                        "Worker-Rotation ist in dieser Stellung nicht legal (Regel-Autoritaet verweigert): rotation={wanted_rot:?}"
                    )))
                }
            }
        }
        Ok(())
    }

    /// Endwertung anwenden, falls die Partie in Phase::End steht (Nachlauf
    /// wie `unified_game_loop`). Gibt zurueck, ob angewandt wurde.
    fn finalize_scoring(&mut self) -> bool {
        if self.game.state.phase == Phase::End {
            let _ = self.game.apply_end_scoring();
            true
        } else {
            false
        }
    }
}
