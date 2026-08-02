//! AlphaZero-PUCT-Suche über die Drafting-Phase (Network-Modus, Phase B).
//!
//! Ähnliche Grundstruktur wie die Heuristik-MCTS (`crate::mcts`), aber
//! bewusst OHNE deren Force-Reply-Garantie/Nachlauf-Schließung (Tiefe 0/1
//! erzwang früher eine simulierte Gegner-Antwort vor weiterem Breitern,
//! plus ein Nachlauf-Pass für Fälle, die PUCT nie erneut besucht hätte) --
//! entfernt als unnötige Komplexität für den Netz-Pfad (Nutzer-Entscheidung).
//! `crate::mcts` behält beides (Stufe 1 bleibt unverändert). Sonst:
//!   - Selektion per **PUCT** mit Netz-Priors statt UCB1,
//!   - Blattbewertung = `ACTIVE_LEAF` (siehe unten) -- aktuell Stufe 2
//!     (Netz-Value, mit dem neuen ±1-Sieg/Niederlage-Ziel statt der alten
//!     verrauschten Punktestand-Regression), Stufe 1 (DFS-Solver) bleibt als
//!     abschaltbarer Pfad im Code, wird aber nicht mehr aktiv genutzt (siehe
//!     evaluations/stage2_investigation.md fuer die Historie: die
//!     Disagreement-Studie widerlegte Stufe 2 mit dem ALTEN Value-Ziel,
//!     Stufe 1 ist mit dem exakten DFS-Solver aber strukturell auf
//!     Ein-Runden-Sicht begrenzt -- "spielt man gegen Stufe 1, spielt man
//!     letztlich gegen die Heuristik". Stufe 2 mit einem sauber trainierten
//!     Value-Head ist der einzige Weg zu echter Mehrrunden-Strategie).
//!   - **Dirichlet-Wurzel-Noise** (Self-Play-Exploration).
//! Lazy Expansion nach Prior (höchster zuerst) + Progressive Widening.

use std::collections::HashMap;

use rand::seq::SliceRandom;
use rand::{Rng, RngExt};
use serde_json::{json, Value};

use crate::features::action_to_id;
use crate::game::{drafting_actions, Game};
use crate::mcts::{label_search_move, SearchMove};
use crate::moves::{Action, TakeSource};
use crate::net::{softmax, Net};
use crate::scoring::wertung_progress;
use crate::self_play::action_to_env_dict;
use crate::state::{GameState, Phase};
use crate::tile::TileColor;

/// Aktionsraum-Größe (= `config.NUM_ACTIONS`). Baustein B: 328 (Stone+Tiling)
/// + 27 (choose_dome_slot) + 36 (choose_draw_stack_slot) + 4 (choose_dome_rotation)
/// + 6 (use_chips) + 4 (bonus_chip) + 1 (dome_stack_peek) = 406.
pub(crate) const NUM_ACTIONS: usize = 406;
/// Standard-PUCT-Konstante (= agents/mcts.py `_c_puct`).
pub const DEFAULT_C_PUCT: f64 = 1.5;
/// Dirichlet-Wurzel-Noise (AlphaZero-Standard).
pub const DIRICHLET_EPS: f64 = 0.25;
pub const DIRICHLET_ALPHA: f64 = 0.3;
/// Kumulative Policy-Masse, ab der das Widening stoppt: nur die (nach Prior
/// absteigend sortierten) Kandidaten bis zu dieser Schwelle werden je
/// überhaupt zu Kindknoten — der "Long Tail" niedrig priorisierter Züge wird
/// nie besucht (spart Simulationsschritte, ersetzt die alte, rein
/// besuchszahl-gesteuerte Progressive-Widening-Formel `MAX_ACTIONS +
/// WIDEN_FACTOR·√N`).
pub const POLICY_MASS_CUTOFF: f64 = 0.95;

/// Blattbewertung der Netz-Suche. Priors kommen IMMER vom Netz; nur das Blatt
/// unterscheidet sich:
///   - `Dfs`: exakter DFS-Solver (Stufe 1 — saubere, scharfe Visit-Targets,
///     aber strukturell auf Ein-Runden-Sicht begrenzt).
///   - `Net`: Netz-Value (Stufe 2 — Mehrrunden-Value-Ziel, jetzt ±1
///     Sieg/Niederlage statt der alten Punktestand-Regression).
#[derive(Clone, Copy, PartialEq, Eq)]
pub enum LeafEval {
    Dfs,
    Net,
}

/// Aktiv genutzte Blattbewertung fuer Self-Play/Arena/Stufe 3 (siehe
/// Modul-Kommentar oben). Stufe 1 (`Dfs`) bleibt als Pfad im Code, wird aber
/// bewusst nicht mehr default-mäßig verwendet -- eine Zeile hier zurück auf
/// `Dfs` reaktiviert sie bei Bedarf wieder, ohne Funktionssignaturen
/// anzufassen.
pub const ACTIVE_LEAF: LeafEval = LeafEval::Net;

/// Rundenübergang per Chance-Node-Sampling bewerten (`round_transition.rs`)
/// statt eines einzelnen Netz-Blattwerts, nur wirksam bei `ACTIVE_LEAF=Net`.
/// Standardmäßig AUS -- siehe `round_transition.rs`-Modul-Kommentar (Phase 2
/// im Fahrplan, erst nach einer belegten Val-R²-Verbesserung über den
/// Trainingsziel-Pfad aktivieren, siehe `evaluations/STATUS.md`). Eine
/// Zeile hier auf `true` aktiviert die Live-Suche-Integration jederzeit
/// wieder, ohne Funktionssignaturen anzufassen (gleiches Muster wie
/// `ACTIVE_LEAF`).
pub const ROUND_TRANSITION_SAMPLING: bool = false;

/// KataGo-Stil geblendete Utility (siehe `project_v8d_value_head_root_cause`-
/// Memory / `evaluations/STATUS.md`): `value_head`s R² ist stark rundenabhängig
/// (~0.03 in Runde 1, ~0.62 in Runde 5) — die Suche vertraut ihm aber an jedem
/// Blatt gleichermaßen. `points_head`/`points_forecast` (kontinuierliches
/// Punktestand-Ziel, siehe `neural_net.py::VALUE_SCALE`/`VALUE_OPP_EPSILON`)
/// generalisiert historisch durchgehend besser (R²≈0.33-0.44) als `value`.
/// KataGo blendet genau so einen Score-basierten Utility-Term MIT der
/// Sieg-Wahrscheinlichkeit in die tatsächliche, such-treibende Utility (nicht
/// nur als Trainings-Nebenverlust) — siehe
/// github.com/lightvector/KataGo/blob/master/docs/KataGoMethods.md. Gewicht
/// hier bewusst ohne Vorab-Tuning auf 0.5 (gleichgewichtete Mischung) gesetzt;
/// erster Test, mit echten Arena-Ergebnissen gegenkalibrieren (0.0 = alter
/// reiner Value-Leaf-Zustand, 1.0 = reiner Points-Leaf).
///
/// GETESTET (2026-07-19, v9b_domeonly, 150 Sims, SPRT): weder 0.5 (1:14,
/// Score 19.5 vs 49.7, Floor 27.0 vs 10.5) noch 1.0 (0:12, Score 14.2 vs
/// 55.0, Floor 25.4 vs 10.1) schließen die Lücke zum 0.0-Baseline (0:12,
/// Score 13.7-18.2 vs 44.4-46.8, Floor ~20-25) — Floor-Strafe bleibt bei
/// ALLEN drei Werten im selben erhöhten Bereich, unabhängig von der
/// Blattwert-Formel. Auf 0.0 zurückgesetzt (= vorheriger, besser abgesicherter
/// Zustand); Code bleibt verfügbar für spätere Rekalibrierung, siehe
/// `project_v8d_value_head_root_cause`-Memory für die volle Diskussion.
pub const POINTS_UTILITY_WEIGHT: f64 = 0.0;

/// Skala für die Floor-Straf-Korrektur (siehe `floor_shaping_delta`), gleiche
/// Größenordnung wie `VALUE_SCALE` in `neural_net.py` (dort 50.0) — macht die
/// Korrektur direkt vergleichbar mit dem own-minus-opp-Score-Margin, den
/// `value`/`points_forecast` schon als Trainingsziel verwenden.
const FLOOR_SHAPING_SCALE: f64 = 50.0;

/// Gewicht der Floor-Straf-Korrektur relativ zum Netz-Blattwert. Bewusst
/// klein gewählt (Nudge, kein Ersatz für den Value-Head) — erster Test, mit
/// echten Arena-Ergebnissen kalibrieren.
///
/// GETESTET (2026-07-19/20, v9b_domeonly, 150 Sims, n=100, KEIN Early-Stop):
/// 11:89 (11% Siege), Score 24.5 vs. 44.2, Floor 16.9 vs. 11.2 — spürbar
/// engerer Floor-Abstand als Baseline (~20-27 vs. ~8-10) und die bisher
/// beste Netz-Performance der gesamten Session. Bleibt vorerst aktiv.
pub const FLOOR_SHAPING_WEIGHT: f64 = 0.3;

/// Task #78 (v12c): rundenabhängige Value-Shrinkage Richtung 0.5. Motivation:
/// der Value-Head ist in frühen Runden nachweislich kaum besser als der
/// Mittelwert (Runde-1-Noise-Floor-Deckel ≈0.007, siehe
/// `evaluations/STATUS.md` "Noise-Floor-Test"), wird an JEDEM PUCT-
/// Blattknoten aber gleich stark vertraut wie in Runde 5 (Deckel ≈0.44, klar
/// informativ). Shrinkage dämpft die Blattwert-AUSSCHLÄGE (nicht den
/// Mittelwert) proportional zur erwarteten Zuverlässigkeit je Runde, analog
/// zu einem James-Stein-artigen Schrumpfen des Schätzers Richtung des
/// uninformativen Priors 0.5.
///
/// GEPAARTER A/B-NACHWEIS GEFAHREN (2026-07-23, `tools/paired_arena_shrink_ab.py`,
/// v12b_lr_best@400 vs. v12_best@400, 100 seed-gepaarte Spiele je Arm, gleiche
/// Seeds in beiden Armen): Arm OFF 61:39, Arm ON 50:50 -- ON ist NICHT nur
/// unsignifikant, sondern tendenziell sogar schwächer (Diskordanz b=15 vs.
/// c=26, exakter McNemar p=0.117). Evidenzregel (siehe MEMORY.md/STATUS.md-
/// Präzedenzfälle: reine Performance-Hebel ohne Korrektheits-Charakter
/// brauchen einen signifikanten Beleg, bevor sie standardmäßig aktiv
/// geschaltet werden, siehe z.B. das ISMCTS-Mehrfach-Determinisierungs-
/// Verwerfungsmuster) verlangt p<0.05 UND Vorteil für ON -- keins von beiden
/// erfüllt. Bleibt daher AUS. Details: `evaluations/STATUS.md` Abschnitt
/// "v12c: Value-Shrinkage-Rekalibrierung + A/B (2026-07-23)".
pub const VALUE_SHRINK_ENABLED: bool = false;

/// Rekalibrierung (Task #78, 2026-07-23) `w_r` je Runde (Index 0 = Runde 1
/// ... Index 4 = Runde 5), angewendet als `v_shrunk = 0.5 + w_r·(v - 0.5)`.
/// Ersetzt die Phase-A-Platzhalterwerte (die auf dem separaten Noise-Floor-
/// Rückspiel-Test + geclampter v10/v9b-Modell-R²-Näherung beruhten, siehe
/// Git-Historie dieser Konstante).
///
/// Quelle der Zahlen: `tools/offline_diagnose.py`-Lauf auf dem AMTIERENDEN
/// Champion `v12b_lr_best` (2026-07-23, `evaluations/STATUS.md` Abschnitt
/// "v12b: LR-Schedule + From-Scratch-Kontrolle"), echter Val-Split
/// (n=32.392 Val-Züge). Für v12b_lr existiert KEIN separater Noise-Floor-
/// Rückspiel-Test (die Drei-Runden-Probe wurde nur einmal, gegen ein
/// anderes Modell/Korpus, gefahren) -- deshalb wird hier direkt das
/// Modell-R² pro Runde als Verlässlichkeits-Näherung verwendet (derselbe
/// Näherungsschritt, den Phase A bereits für Runde 4/5 mangels Deckel-
/// Messwert brauchte, jetzt konsistent auf alle 5 Runden angewendet).
///
/// Herleitung, unverändert zur Phase-A-Formel: `w_r ∝ sqrt(max(0, R²_r))`,
/// normiert auf `w_5 = 1.0` (keine Dämpfung in der letzten Runde). Die
/// frischen R²-Werte sind bereits von sich aus streng monoton steigend
/// (R1 0.0368 < R2 0.1106 < R3 0.1717 < R4 0.2298 < R5 0.5145) -- anders als
/// in Phase A ist HIER kein `max(Deckel_r, Deckel_{r-1})`-Clamping nötig.
/// Werte (vor Normierung, `sqrt`):
///   R1 √0.0368=0.19183, R2 √0.1106=0.33257, R3 √0.1717=0.41437,
///   R4 √0.2298=0.47937, R5 √0.5145=0.71729.
/// Normiert durch R5: `[0.2674, 0.4636, 0.5777, 0.6683, 1.0000]`.
pub const VALUE_SHRINK_PER_ROUND: [f64; 5] = [0.2674, 0.4636, 0.5777, 0.6683, 1.0000];

/// Rundenzahl (1-basiert, wie `state.round_number`) → Schrumpfgewicht `w_r`
/// aus `VALUE_SHRINK_PER_ROUND`. Defensiv geklammert (Runde 0 oder >5 sollte
/// in der Praxis nie vorkommen, klemmt statt zu paniken).
fn value_shrink_weight(round_number: u32) -> f64 {
    let last = VALUE_SHRINK_PER_ROUND.len() - 1;
    let idx = (round_number.saturating_sub(1) as usize).min(last);
    VALUE_SHRINK_PER_ROUND[idx]
}

/// Wendet die rundenabhängige Value-Shrinkage (Task #78) auf BEIDE
/// Blattwert-Perspektiven `[Spieler0, Spieler1]` an. Muss NACH
/// `blended_leaf_win_prob`, aber VOR dem Floor-Shaping-Additiv aufgerufen
/// werden (siehe `make_node`/`net_leaf_eval`) -- das exakte Floor-Signal
/// (`floor_shaping_delta`) ist eine reine State-Funktion und soll NICHT
/// geschrumpft werden, nur der Netz-Rohwert. Bei `VALUE_SHRINK_ENABLED=false`
/// (Standard) exakte Identität -- byte-identisch zum Vor-Task-#78-Verhalten.
fn apply_value_shrink(value: [f64; 2], round_number: u32) -> [f64; 2] {
    if !VALUE_SHRINK_ENABLED {
        return value;
    }
    let w = value_shrink_weight(round_number);
    [0.5 + w * (value[0] - 0.5), 0.5 + w * (value[1] - 0.5)]
}

/// Perspektiven-/OOD-Interventionstest (externer Hinweis, 2026-07-19): der
/// zweite Forward-Pass für `other_val` (künstlich geflipptes
/// `state.current_player`) bewertet einen Zustand, den das Netz im Training
/// NIE sieht — Trainingsdaten (`self_play.rs`) zeichnen Zustände IMMER nur
/// aus der Perspektive des TATSÄCHLICHEN Zugspielers auf, nie eine fremde
/// Ego-Sicht mitten in einem fremden Zug (inkl. pending-Phasen wie
/// Kuppelplatzierung). Dieser zweite Forward-Pass ist also potenziell
/// Out-of-Distribution und könnte inkohärente, nicht nullsummen-konsistente
/// Q-Backups in beide PUCT-Bäume einspeisen — eine Hypothese, die sowohl
/// "gesundes R², aber schadet der Suche" ALS AUCH "Value/Points/Blend
/// versagen alle identisch" erklären würde (gleiche Plumbing in allen drei
/// Fällen). `true` erzwingt stattdessen die günstige, garantiert
/// nullsummen-konsistente Näherung `other_val = 1 - mover_val` (EIN
/// Forward-Pass statt zwei, kein OOD-Risiko, halbiert nebenbei die
/// Inferenzkosten) — direkter, kostenloser Interventionstest.
///
/// GETESTET (2026-07-20, v9b_domeonly, 150 Sims, n=100, KEIN Early-Stop,
/// ISOLIERT ohne Floor-Shaping): 3:97 (3% Siege), Score 15.7 vs. 43.4,
/// Floor 21.3 vs. 11.1 — KEINE Verbesserung, eher schlechter als der
/// 0.0-Baseline-Bereich und deutlich schwächer als Floor-Shaping (11%).
/// Die Perspektiven-/OOD-Hypothese ist damit als ALLEINIGE Erklärung
/// widerlegt (der zweite Forward-Pass ist zumindest nicht der dominante
/// Schadensfaktor) -- auf `false` zurückgesetzt (Original-Verhalten).
pub const MIRROR_OTHER_VAL: bool = false;

/// Kuppelstapel-Determinisierung im Suchbaum (Fund 6, externer Hinweis,
/// 2026-07-20) -- mischt `dome_tile_pool` bei jedem simulierten
/// `DrawStackPeek` neu (siehe Kommentar an der Aufrufstelle in
/// `build_net_tree`), statt die ECHTE, im realen Spiel verdeckte oberste
/// Platte zu lesen.
///
/// GETESTET (2026-07-20, v9b_domeonly + Struktur-Fixes + Floor-Shaping
/// W=0.3, 150 Sims, n=100, KEIN Early-Stop): 9:91 (9% Siege), Score 21.9
/// vs. 43.9, Floor 18.8 vs. 12.1 -- SCHLECHTER als ohne diesen Fix (17%
/// Siege). Theoretisch gut begründet (entfernt Orakel-Wissen), aber die
/// Neumischung erhöht offenbar eher die Varianz der Suche (jeder simulierte
/// Ast sieht eine andere Ziehung) als dass sie echte Verzerrung beseitigt --
/// bei nur 150 Sims/Zug zu teuer. Auf `false` zurückgesetzt (Original-
/// Verhalten); Code bleibt verfügbar.
pub const SHUFFLE_STACK_PEEK_IN_SEARCH: bool = false;

/// Buendelt die ERSTMALIGE Expansion ALLER Top-m-Kandidaten an der Gumbel-
/// Wurzel (Perf-Auftrag, 2026-08-02: die 1,46x-2D-Inferenzkosten druecken)
/// in EINEM `Net::eval_batch`-Aufruf statt `m_prime` einzelner
/// `make_node`-Netz-Evals -- siehe `batched_expand_root_candidates`.
/// Standardmaessig AUS (gleiches Muster wie `USE_GUMBEL_SEARCH`/
/// `MIRROR_OTHER_VAL` etc. -- neue, noch nicht arena-validierte
/// Sucheigenschaft), Arena-A/B folgt VOR einer Aktivierung.
///
/// Numerisch THEORETISCH nicht ganz kostenlos beim Umschalten: die
/// per-Kandidat-Blattwerte selbst sind batch-invariant (Toleranz 1e-5,
/// siehe `net::eval_batch_matches_n_single_evals` -- derselbe
/// Praezedenzfall wie `eval_pair`), und die WURZEL-Aggregate
/// (`nodes[0].value`/`.visits`) KOENNTEN in den letzten Bits abweichen,
/// weil Gleitkomma-Summation nicht assoziativ ist und die Kandidaten-
/// Expansionsreihenfolge sich relativ zu den anschliessenden Tiefen-
/// Besuchen verschiebt (batched: ALLE `m_prime` Kandidaten zuerst, dann
/// deren weitere Besuche; unbatcht: je Kandidat Erstbesuch + weitere
/// Besuche EINGESCHACHTELT, bevor der naechste Kandidat drankommt) --
/// GEMESSEN (2026-08-02, Paritaetstest
/// `batched_root_expansion_matches_sequential_within_tolerance`, gegen
/// `v19_2d_best` UND ein flaches Modell, sims=400/m_prime=16) war das
/// Ergebnis aber tatsaechlich BIT-IDENTISCH (nicht nur innerhalb Toleranz)
/// -- kein beobachtbarer Effekt in der Praxis, die Toleranz im Test bleibt
/// trotzdem als Sicherheitsmarge stehen (kein Anspruch auf Bit-Identitaet
/// ueber alle Hardware-/tract-Versionen hinweg).
/// RNG-Verbrauch bleibt in der Standardkonfiguration UNVERAENDERT (siehe
/// `batched_expand_root_candidates`-Doku): `SHUFFLE_STACK_PEEK_IN_SEARCH`
/// und `ROUND_TRANSITION_SAMPLING` (beide Default `false`) sind die
/// einzigen `rng`-Verbrauchsstellen zwischen Expansion und Tiefenbesuch --
/// bei `SHUFFLE_STACK_PEEK_IN_SEARCH=true` faellt die Aufrufstelle
/// zusaetzlich auf den unbatchten Pfad zurueck (siehe dort), um die
/// RNG-Reihenfolge nicht zu verschieben.
pub const BATCH_ROOT_EXPANSION: bool = false;

/// Wurzel-Determinisierung (Nutzer-Vorschlag, 2026-07-20 -- Ersatz für
/// `SHUFFLE_STACK_PEEK_IN_SEARCH`s In-Tree-Neumischung): statt bei JEDEM
/// simulierten Peek/Chip-Reveal neu zu mischen (nachweislich MEHR
/// Such-Varianz als Bias-Korrektur, siehe dortiger Kommentar -- und für den
/// Kuppelstapel-Fall ohnehin irrelevant, siehe Bindungs-Check: der
/// Value-Head sieht `pending_stack_draw` architektonisch nie), wird hier
/// EINMAL pro Zugsuche (`build_net_tree`s Wurzel-Erzeugung) eine plausible,
/// fixierte "Stichwelt" gezogen -- `dome_tile_pool` UND die noch
/// unaufgedeckten Bonuschips (`bonus_chip_pool` + noch nicht enthüllte
/// Fabrik-Chips) werden einmalig neu gemischt, danach läuft die GESAMTE
/// Suche deterministisch auf dieser einen Welt. Kein zusätzliches
/// In-Tree-Rauschen (jeder Knoten bleibt intern konsistent) -- nur der
/// klassische, weit mildere Determinisierungs-Fehler (die Suche vertraut
/// EINER plausiblen Stichprobe statt der echten, aber unbekannten Welt).
/// Anders als beim Kuppelstapel (bewiesen irrelevant) sieht der Value-Head
/// aufgedeckte Bonuschip-Werte tatsächlich als Feature (`features.rs`,
/// `bonus_chip_revealed`) -- hier könnte Orakel-Wissen also durchaus
/// greifen.
///
/// GETESTET (2026-07-20, v9b_domeonly + Struktur-Fixes + Floor-Shaping
/// W=0.3, 150 Sims, n=100, KEIN Early-Stop): 12:88 (12% Siege), Score 19.2
/// vs. 40.5, Floor 19.2 vs. 13.7 -- KEINE Verbesserung ggü. der Baseline
/// ohne Determinisierung (17%), tendenziell sogar leicht schlechter (wenn
/// auch deutlich milder als der In-Tree-Fix, der von 17%→9% stürzte). Da
/// der Kuppelstapel-Anteil bewiesen irrelevant ist, kann die Ursache nur im
/// Bonuschip-Anteil liegen oder schlicht Stichproben-Rauschen sein (n=100,
/// ~5 Prozentpunkte liegen im selben Band wie andere Wiederholungen dieser
/// Session) -- kein separater Bonuschip-Bindungs-Check bisher gefahren.
///
/// NUTZER-ENTSCHEIDUNG (2026-07-20): TROTZDEM aktiv gelassen. Anders als
/// der In-Tree-Fix (klarer, großer Rückschritt 17%→9%, dort zu Recht
/// verworfen) ist der Effekt hier klein und im Rauschband dieser Session --
/// es geht nicht nur um gemessenen Vorteil, sondern auch um KORREKTHEIT:
/// die Suche soll kein Wissen nutzen, das ein echter Spieler nicht hat.
/// Dies ist der Minimalfix für das Orakel-Wissen-Problem (Fund 6), bewusst
/// als Standardverhalten beibehalten, unabhängig vom (unklaren) Arena-Delta.
pub const DETERMINIZE_ROOT_HIDDEN_INFO: bool = true;

/// Mischt `dome_tile_pool` und alle noch unaufgedeckten Bonuschip-Werte
/// (Fabrik-Chips mit `!bonus_chip_revealed` + `bonus_chip_pool`) einmalig
/// neu -- siehe `DETERMINIZE_ROOT_HIDDEN_INFO`-Kommentar. Bereits
/// AUFGEDECKTE Fabrik-Chips sind öffentliches Wissen und bleiben
/// unangetastet. Gleiches Muster wie `round_transition_deep::
/// simulate_one_round`s Kuppelstapel-Determinisierung, hier auf beide
/// verdeckten Informationsquellen erweitert und auf Wurzel-Ebene (einmal
/// pro Suche) statt pro Runde angewendet.
fn determinize_hidden_information<R: Rng + ?Sized>(state: &mut GameState, rng: &mut R) {
    state.dome_tile_pool.shuffle(rng);

    let orig_pool_len = state.bonus_chip_pool.len();
    let mut hidden_chips: Vec<crate::dome::BonusChip> = state.bonus_chip_pool.drain(..).collect();
    let unrevealed_idxs: Vec<usize> = state
        .factories
        .iter()
        .enumerate()
        .filter(|(_, f)| f.bonus_chip.is_some() && !f.bonus_chip_revealed)
        .map(|(i, _)| i)
        .collect();
    for &idx in &unrevealed_idxs {
        if let Some(chip) = state.factories[idx].bonus_chip.take() {
            hidden_chips.push(chip);
        }
    }
    hidden_chips.shuffle(rng);
    let remaining = hidden_chips.split_off(orig_pool_len.min(hidden_chips.len()));
    state.bonus_chip_pool = hidden_chips;
    for (idx, chip) in unrevealed_idxs.into_iter().zip(remaining.into_iter()) {
        state.factories[idx].bonus_chip = Some(chip);
    }
}

/// Klassisches ISMCTS (Task #65, 2026-07-22): `DETERMINIZE_ROOT_HIDDEN_INFO`
/// zieht bisher EINE Stichweltentscheidung pro Zugsuche -- die Suche
/// optimiert dann gegen genau diese eine mögliche Welt. Mit `> 1` werden
/// stattdessen `NUM_DETERMINIZATIONS` unabhängige Welten gezogen (je ein
/// eigener `build_net_tree`-Aufruf, das Sims-Budget gleichmäßig gesplittet,
/// Rest an die erste Welt, siehe `split_sims_across_worlds`), je Welt ein
/// eigener Baum gebaut, und die completed-Q-Politik an der Wurzel über die
/// Welten GEMITTELT (siehe `average_completed_q_policy`) -- Standard-ISMCTS-
/// Aggregation, statt sich auf eine einzelne Stichprobe zu verlassen.
///
/// `1` = EXAKT das bisherige Verhalten -- an allen drei Suche-Einstiegen
/// (`net_search_drafting_action`/`net_root_child_stats_and_policy`/
/// `net_search_with_tree`) bleibt der `<= 1`-Codepfad unverändert ein
/// einzelner `build_net_tree`-Aufruf + die alte Auswahl-/Extraktionslogik --
/// bewusst NICHT durch die neue Aggregations-Maschinerie geroutet, damit
/// `NUM_DETERMINIZATIONS=1` byte-identisch zum Alt-Verhalten bleibt (siehe
/// Testmodul).
///
/// **Befund zur Wurzel-Kandidatenliste (Aufgabenstellung fragte explizit
/// danach)**: `drafting_actions(state)` (game.rs) hängt an der Wurzel nur
/// von `state.factories` (Existenz/Farbe der Auslage-Fliesen, `bonus_chip.
/// is_some()` -- NICHT von dessen Identität/`bonus_chip_revealed`),
/// `state.dome_display`, `state.pending_dome_choice`/`pending_stack_draw`
/// (Struktur, nicht Inhalt) ab. `determinize_hidden_information` verändert
/// AUSSCHLIESSLICH die REIHENFOLGE von `dome_tile_pool` und die IDENTITÄT
/// (nicht Existenz) unaufgedeckter Bonus-Chips -- keines dieser Felder
/// beeinflusst, welche `Action`-Varianten legal sind. Die Wurzel-
/// Kandidatenliste (und mit ihr `build_untried_actions`s POLICY_MASS_CUTOFF-
/// Präfix, da die Netz-Priors auf denselben, für unaufgedeckte Information
/// maskierten Features beruhen) ist damit weltUNabhängig -- die Aggregation
/// per direktem Aktions-Schlüsselvergleich (`Action: PartialEq`) ist
/// folglich korrekt und braucht keinen Kandidatenlisten-Abgleich über
/// Indizes. Trotzdem defensiv robust implementiert (fehlende Aktion in
/// einer Welt wird einfach übersprungen, kein Panik), falls diese Invariante
/// künftig durch eine Regeländerung verletzt würde.
///
/// **Perspektiven-Divergenz-Logging/Diagnose-Pfade geprüft (kein n-faches
/// Zählen)**: `record_perspective_divergence` akkumuliert pro `make_node`-
/// Aufruf, also pro TATSÄCHLICH bewertetem Baumknoten -- bei N Welten gibt
/// es zwar N separate Bäume, aber JEDER Knoten in JEDEM Baum ist eine echte,
/// eigenständige Netz-Auswertung (kein Knoten wird mehrfach für dieselbe
/// Sim gezählt). Das Gesamt-Sims-Budget bleibt unverändert (nur gesplittet,
/// siehe `split_sims_across_worlds`) -- die Diagnose sammelt also über
/// denselben Gesamt-Simulationsaufwand wie zuvor, nur jetzt über mehrere
/// kleinere Bäume statt einem großen. Kein Fix nötig.
///
/// **GETESTET (2026-07-22, gepaarter A/B, `evaluations/paired_arena_ismcts.py`,
/// v10_best@NET_SIMS=400 vs. Heuristik@HEUR_SIMS=200, Blöcke à 25, kumulativer
/// exakter McNemar): n=3 verliert SIGNIFIKANT gegen n=1 -- Stopp nach 75
/// Paaren bei p=0.00088 (diskordant b=6 [n=3 gewinnt, n=1 nicht] vs. c=25
/// [umgekehrt]). Sieg-Anteil gegen Heuristik: n=3 19/75=25.3% (95%-KI
/// 16.9-36.2%), n=1 38/75=50.7% (95%-KI 39.6-61.7%) -- deutlich, nicht im
/// Rauschband. Wahrscheinlichste Erklärung: das 400er-Sims-Budget auf 3
/// Welten gesplittet (~133/Welt) unterbudgetiert `GUMBEL_TOP_M=16` +
/// Sequential Halving pro Welt stark genug, dass der Suchtiefen-/
/// Differenzierungsverlust den ISMCTS-Aggregationsgewinn (Robustheit gegen
/// EINE ungünstige Determinisierung) bei diesem Sims-Niveau klar überwiegt.
/// Reiner Performance-Hebel (kein Korrektheits-Fix, siehe
/// `DETERMINIZE_ROOT_HIDDEN_INFO`-Präzedenz für den Unterschied) -- hier
/// zählt der Nachweis, nicht die theoretische Eleganz (Floor-Shaping-
/// Präzedenz). Auf `1` zurückgesetzt (= Standard-Einzeldeterminisierung,
/// unverändert seit vor Task #65); der komplette Mehrwelten-/Aggregations-
/// Code bleibt als Toggle verfügbar (z.B. für einen künftigen Test bei
/// höherem Sims-Budget, wo der Unterbudgetierungs-Nachteil kleiner sein
/// könnte).
pub const NUM_DETERMINIZATIONS: usize = 1;

/// Teilt `sims` gleichmäßig auf `n` Welten auf (Rest an die ERSTE Welt).
/// `n` wird an den Aufrufstellen immer `NUM_DETERMINIZATIONS` sein.
fn split_sims_across_worlds(sims: u32, n: usize) -> Vec<u32> {
    let n = (n.max(1)) as u32;
    let base = sims / n;
    let rem = sims % n;
    (0..n).map(|i| if i == 0 { base + rem } else { base }).collect()
}

/// Baut `n` unabhängige Suchbäume ("Wald", ein Baum je Welt) -- `n` nimmt
/// alle Produktions-Aufrufstellen als `NUM_DETERMINIZATIONS` entgegen
/// (NUR für den `> 1`-Pfad gedacht, siehe Konstantenkommentar), als
/// Parameter statt hartkodierter Konstante gehalten, damit das Testmodul
/// direkt verschiedene `n` prüfen kann, ohne die Konstante selbst umbauen
/// zu müssen. `build_net_tree` zieht bei `DETERMINIZE_ROOT_HIDDEN_INFO=true`
/// selbst bei JEDEM Aufruf eine frische Determinisierung (RNG-Strom wird
/// zwischen den Welten einfach weitergereicht) -- kein separates Reseeding
/// nötig, um unterschiedliche Welten zu bekommen.
fn build_determinized_forest<R: Rng + ?Sized>(
    net_policy: &Net,
    net_value: Option<&Net>,
    state: &GameState,
    sims: u32,
    c_puct: f64,
    add_root_noise: bool,
    n: usize,
    rng: &mut R,
) -> Vec<Vec<Node>> {
    split_sims_across_worlds(sims, n)
        .into_iter()
        .map(|world_sims| {
            build_net_tree(net_policy, net_value, state, world_sims, c_puct, add_root_noise, rng, None, None)
        })
        .collect()
}

/// Rohe `(Action, Besuche, Q)`-Statistik der Wurzelkinder EINES Baums --
/// extrahiert aus `net_root_child_stats`/`net_root_child_stats_and_policy`s
/// altem `NUM_DETERMINIZATIONS<=1`-Pfad, zusätzlich von
/// `aggregate_root_child_stats` (Mehrwelten-Summierung) je Welt genutzt.
fn root_child_stats_from_nodes(nodes: &[Node]) -> Vec<(Action, u32, f64)> {
    nodes[0]
        .children
        .iter()
        .filter_map(|&cid| {
            let node = &nodes[cid];
            let q = if node.visits > 0 { node.value / node.visits as f64 } else { 0.0 };
            node.action.clone().map(|a| (a, node.visits, q))
        })
        .collect()
}

/// Aggregiert `(Action, Besuche, Q)` über den Determinisierungs-Wald:
/// Besuche werden SUMMIERT (treibt `self_play::net_drafting_policy`s
/// besuchsbasierte Stichprobe unverändert weiter, jetzt über die
/// Welten-SUMME statt einer einzelnen Welt), `Q = Σ(Value)/Σ(Besuche)` über
/// alle Welten, in denen die Aktion tatsächlich zu einem Wurzelkind wurde
/// (kleineres Pro-Welt-Sims-Budget kann dazu führen, dass eine Aktion nicht
/// in JEDER Welt besucht wird -- trägt dann einfach 0 bei). Aktions-
/// Gleichheit als Schlüssel ist korrekt, siehe `NUM_DETERMINIZATIONS`-
/// Kommentar (weltunabhängige Wurzel-Kandidaten).
fn aggregate_root_child_stats(forest: &[Vec<Node>]) -> Vec<(Action, u32, f64)> {
    let mut acc: Vec<(Action, u32, f64)> = Vec::new(); // (action, visits_sum, value_sum)
    for nodes in forest {
        for &cid in &nodes[0].children {
            let node = &nodes[cid];
            let Some(a) = node.action.clone() else { continue };
            match acc.iter_mut().find(|(act, _, _)| *act == a) {
                Some(entry) => {
                    entry.1 += node.visits;
                    entry.2 += node.value;
                }
                None => acc.push((a, node.visits, node.value)),
            }
        }
    }
    acc.into_iter()
        .map(|(a, v, val_sum)| (a, v, if v > 0 { val_sum / v as f64 } else { 0.0 }))
        .collect()
}

/// Mittelt `root_completed_q_policy` (completed-Q-Softmax an der Wurzel, je
/// Welt über `improved_policy(nodes, 0)`) über den Determinisierungs-Wald,
/// Aktions-Schlüssel = die Aktion selbst (siehe `NUM_DETERMINIZATIONS`-
/// Kommentar: Wurzel-Kandidaten sind weltunabhängig, jede Aktion sollte
/// daher in JEDER Welt genau einmal auftauchen). Defensiv trotzdem robust
/// gegen eine in einzelnen Welten fehlende Aktion (Mittelwert nur über die
/// Welten, in denen sie auftaucht, plus Renormalisierung am Ende, falls die
/// Summe dadurch von 1.0 abweicht).
fn average_completed_q_policy(forest: &[Vec<Node>]) -> Vec<(Action, f64)> {
    let per_world: Vec<Vec<(Action, f64)>> =
        forest.iter().map(|nodes| root_completed_q_policy(nodes)).collect();
    let Some(reference) = per_world.first() else { return Vec::new() };
    let mut out: Vec<(Action, f64)> = Vec::with_capacity(reference.len());
    for (act, _) in reference {
        let mut sum = 0.0f64;
        let mut count = 0usize;
        for world in &per_world {
            if let Some(&(_, p)) = world.iter().find(|(a, _)| a == act) {
                sum += p;
                count += 1;
            }
        }
        out.push((act.clone(), if count > 0 { sum / count as f64 } else { 0.0 }));
    }
    let total: f64 = out.iter().map(|(_, p)| p).sum();
    if total > 0.0 {
        for entry in out.iter_mut() {
            entry.1 /= total;
        }
    }
    out
}

/// Exakte, JETZT SCHON feststehende Floor-Straf-Differenz (Spieler0 minus
/// Spieler1) dieser Runde, roh (unskaliert). KEINE Vorhersage — reine
/// State-Funktion (`PlayerBoard::broken_penalty`, board.rs), verfügbar ohne
/// jeden Netz-Forward-Pass. Motivation: `execute_place`/`add_to_penalty`
/// (execution.rs) legen Überlauf-Fliesen zu 100% deterministisch beim
/// Anwenden eines Zugs fest — die resultierende Strafe ist beim Expandieren
/// eines PUCT-Knotens (`apply_drafting` ist da schon gelaufen) bereits exakt
/// bekannt, lange bevor irgendeine Runde endet und offiziell verrechnet wird.
/// Der Value-Head bekommt die rohe Fliesenanzahl zwar als Input-Feature
/// (`features.rs`, `floor_n/4`), muss die NICHTLINEARE, eskalierende
/// Strafskala (`BROKEN_PENALTIES` = -1,-2,-3,-4) aber selbst lernen UND
/// korrekt gegen den unsicheren Rest der Partie abwägen — genau dort ist der
/// Value-Head laut Rundenabhängigkeits-Befund (siehe
/// `project_v8d_value_head_root_cause`-Memory) am schwächsten. Diese
/// Korrektur reicht die exakt bekannte Teilinformation direkt durch, statt
/// darauf zu vertrauen, dass das Netz sie selbst wiederentdeckt.
///
/// Zwei Quellen, BEIDE exakt/deterministisch, BEIDE nötig (Nutzer-Hinweis --
/// Boden entsteht nicht nur beim Drafting-Überlauf): `broken_penalty()`
/// zählt bereits MATERIALISIERTE Strafleisten-Fliesen (Drafting-Überlauf,
/// `execution.rs::add_to_penalty`); `round_end::projected_unplaceable_penalty`
/// preist zusätzlich die beim NÄCHSTEN Drafting→Tiling-Übergang fällige
/// Strafe für schon jetzt erkennbar unplatzierbare Reihen ein
/// (`round_end.rs::process_unplaceable_rows`) — komponiert korrekt mit dem
/// MAX_BROKEN-Deckel der ersten Quelle (siehe dortiger Kommentar: selbst der
/// exakte DFS-Solver preist das NICHT ein). Ohne diese zweite Quelle sieht
/// die Korrektur an einem Rundenende-Knoten oft noch 0 Boden, obwohl er beim
/// tatsächlichen Übergang unausweichlich feststeht.
fn floor_shaping_delta(state: &GameState) -> f64 {
    let mine = (state.players[0].broken_penalty()
        + crate::round_end::projected_unplaceable_penalty(&state.players[0])) as f64;
    let theirs = (state.players[1].broken_penalty()
        + crate::round_end::projected_unplaceable_penalty(&state.players[1])) as f64;
    (mine - theirs) / FLOOR_SHAPING_SCALE
}

// ── Wertungsplatten-Shaping (Task #93) ──────────────────────────────────────
// Rekonstruiert 2026-07-27 aus Commit 3b7f36b/344970f (Worktree
// `worktree-plate-shaping`, nach der A/B-Messung aufgeraeumt/geloescht) --
// Nutzer-Anstoss: erneut fuer einen Folgetest (Task #5, Rang-Invarianz-
// Hypothese der Gumbel-Suche) brauchbar machen. Inhaltlich UNVERAENDERT
// gegenueber dem Original, siehe evaluations/STATUS.md Abschnitt
// "Wertungsplatten-Shaping A/B (Task #93, 2026-07-25)" fuer das damalige
// A/B-Ergebnis (p=0.7111, GEGEN Merge -- ENABLED bleibt daher `false`).

/// Skala für das Wertungsplatten-Fortschritts-Additiv, gleiche Größenordnung
/// wie `FLOOR_SHAPING_SCALE`/`VALUE_SCALE` (50.0) -- macht die Korrektur
/// direkt vergleichbar mit dem own-minus-opp-Score-Margin, das `value`/
/// `points_forecast` schon als Trainingsziel verwenden (gleiche Begründung
/// wie bei `FLOOR_SHAPING_SCALE`).
const PLATE_SHAPING_SCALE: f64 = 50.0;

/// Gewicht des Wertungsplatten-Fortschritts-Additivs relativ zum
/// Netz-Blattwert (Task #93, analog `FLOOR_SHAPING_WEIGHT`). Startwert 0.3
/// aus Analogie zum validierten Floor-Shaping übernommen -- war der
/// A/B-Testgegenstand (siehe `PLATE_SHAPING_ENABLED`-Kommentar für das
/// Ergebnis), NICHT weiter rekalibriert (der Toggle blieb aus, eine
/// Fein-Kalibrierung des Gewichts wäre reine Spekulation ohne neuen Beleg).
pub const PLATE_SHAPING_WEIGHT: f64 = 0.3;

/// Toggle für das Wertungsplatten-Shaping (Task #93, Compile-Konstante --
/// Arm OFF/ON per Wheel-Rebuild wie beim Value-Shrinkage-A/B, siehe
/// `VALUE_SHRINK_ENABLED`). `false` (Standard) = byte-identisches
/// Bestandsverhalten, der Additiv-Block in `make_node` wird dann gar nicht
/// erst ausgeführt (siehe `apply_plate_shaping`). Paritätstest:
/// `plate_shaping_disabled_is_exact_identity`.
///
/// GEPAARTER A/B GEFAHREN (2026-07-25, `tools/paired_arena_plate_ab.py`,
/// `v15_best`@400 vs. `v14b_best`@400, 100 seed-gepaarte Spiele je Arm,
/// identischer Basis-Seed 9315 in beiden Armen): Arm OFF 58:42 (Score 35.3
/// vs. 31.0, Floor 14.2 vs. 17.4), Arm ON 61:39 (Score 35.9 vs. 29.2, Floor
/// 13.7 vs. 17.8) -- ON liegt zwar numerisch vorn, aber die Diskordanz
/// (b=16 ON-only-Siege, c=13 OFF-only-Siege) ist klein und nicht signifikant
/// (exakter McNemar p=0.7111). Evidenzregel (siehe MEMORY.md/STATUS.md-
/// Präzedenzfälle, z.B. `VALUE_SHRINK_ENABLED`) verlangt p<0.05 UND Vorteil
/// für ON -- nur Ersteres fehlt hier klar. Bleibt daher AUS. Details:
/// `evaluations/STATUS.md` Abschnitt "Wertungsplatten-Shaping A/B (Task #93,
/// 2026-07-25)".
pub const PLATE_SHAPING_ENABLED: bool = false;

/// Exakte, JETZT SCHON feststehende Wertungsplatten-Fortschritts-Differenz
/// (Spieler0 minus Spieler1) -- reine State-Funktion
/// ([`crate::scoring::wertung_progress`], dieselbe stetige Fortschritts-
/// Heuristik, die die DFS-Blattbewertung in `mcts.rs::player_total` schon
/// lange nutzt), KEIN Netz-Forward-Pass, analog `floor_shaping_delta`.
/// `wertung_progress` selbst fällt bei voller Plattenfüllung exakt auf den
/// echten `calculate_end_scoring`-Punktwert zurück (siehe dortiger
/// Kommentar) -- keine Doppelzählung mit dem tatsächlichen Endwertungs-Score.
fn plate_shaping_delta(state: &GameState) -> f64 {
    let mine = wertung_progress(&state.players[0], &state.scoring_tile_ids);
    let theirs = wertung_progress(&state.players[1], &state.scoring_tile_ids);
    (mine - theirs) / PLATE_SHAPING_SCALE
}

/// Wendet das Wertungsplatten-Shaping-Additiv (Task #93, Experiment
/// "Marginal-Delta" 2026-07-27, Task #8) auf BEIDE Blattwert-Perspektiven
/// `[Spieler0, Spieler1]` an -- muss NACH dem Floor-Shaping-Additiv
/// aufgerufen werden (koexistiert additiv, siehe Aufrufstelle in
/// `make_node`). Bei `PLATE_SHAPING_ENABLED=false` (Standard) exakte
/// Identität -- der Block wird komplett übersprungen, nicht nur numerisch
/// neutralisiert, damit garantiert byte-identisches Bestandsverhalten
/// erhalten bleibt.
///
/// URSPRUENGLICHE Version (Task #93) wandte `tanh` auf den ABSOLUTEN
/// `plate_shaping_delta(state)` an -- A/B-Nullergebnis (p=0.7111). Task #5
/// (Gumbel-Rang-Invarianz-Diagnose) liefert die Erklaerung: alle
/// Geschwister-Kandidaten eines Knotens teilen denselben grossen
/// Baseline-Fortschritt (nur EIN Zug unterscheidet sie), `tanh` an dieser
/// Stelle hat dort eine kleine Ableitung (`tanh'(baseline)` sinkt mit
/// wachsendem |baseline|) -- die tatsaechlich entscheidungsrelevante
/// MARGINALE Differenz zwischen Geschwistern wird dadurch mit `tanh'
/// (baseline)` gedaempft, nicht durch `tanh'(0)=1` wie beabsichtigt.
/// Fix: `tanh` auf die Differenz zum ELTERNKNOTEN anwenden (isoliert den
/// Beitrag GENAU dieses Zugs, eliminiert die gemeinsame Baseline VOR der
/// Nichtlinearitaet statt danach). Bei fehlendem Elternknoten (Wurzel --
/// hat keine Geschwister-Vergleichsbasis) bleibt der Shift 0.
fn apply_plate_shaping(value: [f64; 2], state: &GameState, parent_state: Option<&GameState>) -> [f64; 2] {
    if !PLATE_SHAPING_ENABLED {
        return value;
    }
    let shift = PLATE_SHAPING_WEIGHT * plate_shaping_marginal(state, parent_state).tanh();
    [(value[0] + shift).clamp(0.0, 1.0), (value[1] - shift).clamp(0.0, 1.0)]
}

/// Marginaler Wertungsplatten-Fortschrittsbeitrag GENAU des Zugs, der von
/// `parent_state` zu `state` führte -- isoliert von der gemeinsamen
/// Baseline (siehe `apply_plate_shaping`-Kommentar). `None` (Wurzel, kein
/// Elternknoten) -> 0.0 (kein Shift, keine Geschwister-Vergleichsbasis).
/// Eigene, ungated Funktion (nicht hinter `PLATE_SHAPING_ENABLED`), damit
/// die reine Formel unabhängig vom Toggle testbar ist.
fn plate_shaping_marginal(state: &GameState, parent_state: Option<&GameState>) -> f64 {
    match parent_state {
        Some(ps) => plate_shaping_delta(state) - plate_shaping_delta(ps),
        None => 0.0,
    }
}

// ── Perspektiven-/OOD-Audit (externer Hinweis, 2026-07-20) ──────────────────
//
// Der Perspektiven-Mirror-Fix (`MIRROR_OTHER_VAL`) wurde arena-getestet und
// hat die Suchstärke NICHT verbessert (siehe dortiger Kommentar) -- die
// Hypothese "zweiter Forward-Pass ist der dominante Schadensfaktor" ist damit
// als ALLEINIGE Erklärung widerlegt. Der zugrunde liegende Verdacht (mover_val
// + other_val nicht nullsummen-konsistent, da `other_val` einen im Training
// nie gesehenen Zustand auswertet) bleibt aber eine berechtigte, noch nicht
// endgültig ausgeschlossene Teilursache -- daher NICHT die Suche selbst
// ändern (das Ergebnis war negativ), sondern permanent als Audit/Sanity-Check
// mitloggen: `|v_mover + v_other - 1|` pro Runde, unconditional (kein
// Feature-Flag, immer aktiv, im Gegensatz zu `profiling.rs`s
// `clone_profiling`-gated Tooling) -- Nutzer-Auftrag, im Self-Play als
// zusätzliche Ausgabewerte sichtbar bleiben. Gleiches Muster wie
// `self_play.rs`s `STAGE3_DECISIONS`-Zähler (Mutex statt Atomics, da hier
// auch Summen/Mittelwerte gebraucht werden, nicht nur Zählungen).
static PERSPECTIVE_DIVERGENCE_STATS: std::sync::OnceLock<std::sync::Mutex<[(u64, f64); 6]>> =
    std::sync::OnceLock::new();

fn perspective_divergence_stats() -> &'static std::sync::Mutex<[(u64, f64); 6]> {
    PERSPECTIVE_DIVERGENCE_STATS.get_or_init(|| std::sync::Mutex::new([(0u64, 0.0f64); 6]))
}

/// `mover_val`/`other_val` sind VOR der Floor-Shaping-Korrektur genau die
/// beiden unabhängigen Netz-Forward-Pass-Ergebnisse -- exakt die Größen, die
/// laut Hinweis nicht nullsummen-konsistent sein könnten. `round` wird auf
/// 1..=5 gekappt (Index 0 bleibt ungenutzt).
fn record_perspective_divergence(round: u32, mover_val: f64, other_val: f64) {
    let idx = (round as usize).clamp(1, 5);
    let div = (mover_val + other_val - 1.0).abs();
    let mut g = perspective_divergence_stats().lock().unwrap();
    g[idx].0 += 1;
    g[idx].1 += div;
}

pub(crate) fn perspective_divergence_reset() {
    let mut g = perspective_divergence_stats().lock().unwrap();
    *g = [(0u64, 0.0f64); 6];
}

/// JSON `{"round_1": {"n": .., "mean_abs_divergence": ..}, ...}` -- ans
/// Self-Play-Ergebnis angehängt, analog `self_play.rs`s
/// `stage3_diagnostics`-Objekt.
pub(crate) fn perspective_divergence_snapshot() -> Value {
    let g = perspective_divergence_stats().lock().unwrap();
    let mut out = serde_json::Map::new();
    for round in 1..=5usize {
        let (n, sum) = g[round];
        let mean = if n > 0 { sum / n as f64 } else { 0.0 };
        out.insert(format!("round_{round}"), json!({ "n": n, "mean_abs_divergence": mean }));
    }
    Value::Object(out)
}

// ── Suche-getriebene Moon-Order-Wahl ─────────────────────────────────────────
//
// Die Aktions-ID (`action_to_id`) kodiert `moon_order` NICHT — Farbe/Reihe/
// Fabrik bestimmen die ID, alle Reihenfolge-Varianten eines SmallFactorySun-
// Zugs fallen also auf dieselbe ID. Statt NUM_ACTIONS aufzublähen (würde alle
// bestehenden Checkpoints invalidieren), bleibt der 482-dim Policy-Head auf
// Farbe+Reihe beschränkt; die Permutations-Priors kommen SEPARAT aus dem
// moon_order_head (Plackett-Luce über die rohen 5 Farb-Scores) und werden erst
// beim Expandieren eines SmallFactorySun-Knotens mit dem Basis-Prior
// multipliziert: P(Zug) = P(Basis) × P(Order | Plackett-Luce).

/// TileColor → Index in COLOR_MAP-Reihenfolge (blau=0…türkis=4), sonst None.
fn color_idx5(c: TileColor) -> Option<usize> {
    TileColor::NORMAL.iter().position(|&x| x == c)
}

/// Alle EINDEUTIGEN Permutationen einer Farb-Multimenge (Tiles derselben Farbe
/// sind ununterscheidbar — Duplikate durch wiederholte Farben werden dedupliziert).
fn unique_moon_orders(remaining: &[TileColor]) -> Vec<Vec<TileColor>> {
    fn permute(items: &mut Vec<TileColor>, k: usize, out: &mut Vec<Vec<TileColor>>) {
        if k == items.len() {
            out.push(items.clone());
            return;
        }
        for i in k..items.len() {
            items.swap(k, i);
            permute(items, k + 1, out);
            items.swap(k, i);
        }
    }
    if remaining.is_empty() {
        return vec![Vec::new()];
    }
    let mut items = remaining.to_vec();
    let mut out = Vec::new();
    permute(&mut items, 0, &mut out);
    out.sort_by(|a, b| {
        let av: Vec<&str> = a.iter().map(|c| c.value()).collect();
        let bv: Vec<&str> = b.iter().map(|c| c.value()).collect();
        av.cmp(&bv)
    });
    out.dedup();
    out
}

/// Plackett-Luce-Wahrscheinlichkeit einer konkreten Farbfolge unter den 5 rohen
/// Moon-Head-Scores (unnormalisiert, Reihenfolge wie `TileColor::NORMAL`):
/// sequenzieller Softmax über die jeweils noch verbleibenden Farben.
fn plackett_luce_prob(scores: &[f32; 5], seq: &[TileColor]) -> f64 {
    let mut counts = [0i32; 5];
    for &c in seq {
        if let Some(i) = color_idx5(c) {
            counts[i] += 1;
        }
    }
    let mut p = 1.0f64;
    for &c in seq {
        let Some(cid) = color_idx5(c) else { continue };
        let avail: Vec<usize> = (0..5).filter(|&i| counts[i] > 0).collect();
        if avail.len() > 1 {
            let max_s = avail.iter().map(|&i| scores[i]).fold(f32::NEG_INFINITY, f32::max);
            let exps: Vec<f64> = avail.iter().map(|&i| ((scores[i] - max_s) as f64).exp()).collect();
            let sum: f64 = exps.iter().sum::<f64>().max(1e-12);
            let pos = avail.iter().position(|&i| i == cid).unwrap();
            p *= exps[pos] / sum;
        } // avail.len() <= 1: einziger Rest-Kandidat -> P=1, kein Beitrag
        counts[cid] -= 1;
    }
    p
}

struct Node {
    parent: Option<usize>,
    children: Vec<usize>,
    /// Noch nicht expandierte (Aktion, Prior), absteigend nach Prior sortiert.
    untried: Vec<(Action, f32)>,
    action: Option<Action>,
    player_who_acted: usize,
    visits: u32,
    value: f64,
    /// Prior, den der Elternknoten dieser Aktion zugewiesen hat (für PUCT).
    prior: f32,
    state: GameState,
    terminal: bool,
    /// DFS-Solver-Blattwert am Knotenzustand (je Spieler) — Backprop-Blattwert.
    leaf_value: [f64; 2],
    /// Gesamtzahl legaler Züge VOR Moon-Order-Expansion (= Basis-Aktionen) —
    /// für die "Gültige Aktionen"-Anzeige (Server-Debug-UI), unabhängig davon,
    /// wie viele davon durchs Widening tatsächlich zu Kindern wurden.
    n_actions: usize,
}

impl crate::search_common::SearchNode for Node {
    fn parent(&self) -> Option<usize> { self.parent }
    fn children(&self) -> &[usize] { &self.children }
    fn terminal(&self) -> bool { self.terminal }
}

/// Baut die priorisierte Kandidatenliste (Kind-Aktionen + Priors) für einen
/// Nicht-Terminal-Knoten aus den rohen Netz-Logits + Moon-Head-Scores. Reine
/// Funktion (kein `Net`-Aufruf) — direkt mit synthetischen Logits testbar.
/// Gibt `(sortierte Kandidaten, Basis-Aktionszahl VOR Moon-Order-Expansion)`
/// zurück; letzteres bleibt für den DFS-Solver-Blattwert unverändert.
fn build_untried_actions(
    state: &GameState,
    logits: &[f32],
    moon_scores: &[f32; 5],
    skip_cutoff: bool,
) -> (Vec<(Action, f32)>, usize) {
    let base_actions = drafting_actions(state);
    let n = base_actions.len();
    // Direkter Action→ID-Match statt JSON-Umweg (Performance, externer
    // Hinweis Abschnitt D, 2026-07-20) -- heißester Aufruf in
    // `build_untried_actions` (pro legaler Aktion pro Knoten), siehe
    // `self_play::action_to_id_direct`-Kommentar für die Parität-Absicherung.
    let ids: Vec<usize> = base_actions.iter().map(|a| crate::self_play::action_to_id_direct(state, a)).collect();

    // WICHTIG: Maskierte Softmax NUR über die EINDEUTIGEN legalen Aktions-IDs —
    // exakt wie das Training (masked log_softmax). Mehrere Moon-Order-Varianten
    // derselben Basis-Aktion teilen sich eine ID; würden sie hier dupliziert
    // eingehen, bekäme diese ID fälschlich mehrfaches Gewicht. Seit Baustein B
    // (zweistufiger Kuppel-Suchknoten) ist das die EINZIGE verbleibende
    // ID-Kollabierung -- Kuppel-Slot/Rotation haben jetzt eigene, nicht
    // kollabierte IDs (siehe features.rs::action_to_id), brauchen also keine
    // separate Prior-Faktorisierung mehr.
    let mut unique_ids: Vec<usize> = ids.clone();
    unique_ids.sort_unstable();
    unique_ids.dedup();
    let legal_logits: Vec<f32> = unique_ids
        .iter()
        .map(|&id| logits.get(id).copied().unwrap_or(f32::NEG_INFINITY))
        .collect();
    let base_probs = softmax(&legal_logits);
    let p_base: HashMap<usize, f32> = unique_ids.into_iter().zip(base_probs).collect();

    // Kandidaten: SmallFactorySun mit ≥2 Restfliesen → alle eindeutigen Moon-
    // Order-Permutationen, Prior = P(Basis) × P(Order | Plackett-Luce). Alle
    // anderen Aktionen unverändert 1:1.
    let mut acts: Vec<(Action, f32)> = Vec::with_capacity(base_actions.len());
    for (act, id) in base_actions.into_iter().zip(ids.into_iter()) {
        let base_p = *p_base.get(&id).unwrap_or(&0.0);
        if let Action::Stone(m) = &act {
            if m.take.source == TakeSource::SmallFactorySun && m.take.moon_order.len() >= 2 {
                let variants = unique_moon_orders(&m.take.moon_order);
                let pl: Vec<f64> =
                    variants.iter().map(|seq| plackett_luce_prob(moon_scores, seq)).collect();
                let pl_sum: f64 = pl.iter().sum::<f64>().max(1e-12);
                for (seq, p) in variants.into_iter().zip(pl.into_iter()) {
                    let mut mm = m.clone();
                    mm.take.moon_order = seq;
                    acts.push((Action::Stone(mm), base_p * (p / pl_sum) as f32));
                }
                continue;
            }
        }
        acts.push((act, base_p));
    }
    acts.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));

    // Policy-Masse-Cutoff: nur den minimalen Präfix behalten, dessen kumulierte
    // Priors POLICY_MASS_CUTOFF erreichen — der Rest (Long Tail) wird verworfen,
    // BEVOR er je ein Kandidat für Widening werden kann. Mindestens 1 Aktion
    // bleibt immer erhalten (auch wenn ihr eigener Prior schon >= Cutoff ist).
    //
    // `skip_cutoff` (externer Bugfix-Hinweis, Fund 4, 2026-07-20): an der
    // WURZEL ausgesetzt (siehe `make_node`s `parent.is_none()`-Aufruf) --
    // Dirichlet-Root-Noise (`build_net_tree`) wird sonst erst NACH diesem
    // Cutoff auf den bereits verkleinerten Präfix gemischt, wodurch Aktionen
    // jenseits der 95%-Masse im Self-Play NIE exploriert werden können (kein
    // AlphaZero-Standardverhalten: Root-Noise soll JEDER legalen Aktion eine
    // Explorations-Chance geben). Nur an der Wurzel relevant -- der
    // Progressive-Widening-Cap (`MAX_ACTIONS + WIDEN_FACTOR·√N`, siehe
    // `build_net_tree`) verhindert weiterhin, dass der Long Tail tatsächlich
    // durchgehend expandiert wird, auch ohne den harten Cutoff hier.
    if skip_cutoff {
        return (acts, n);
    }
    let mut cum = 0.0f64;
    let mut keep = acts.len();
    for (i, (_, p)) in acts.iter().enumerate() {
        cum += *p as f64;
        if cum >= POLICY_MASS_CUTOFF {
            keep = i + 1;
            break;
        }
    }
    acts.truncate(keep.max(1));
    (acts, n)
}

/// Netz-Value (Tanh, ±1) → Win-Prob [0,1] fuer die perspektivische Blattwert-
/// Skala von `leaf_value` (muss zu `crate::mcts::evaluate`s [0,1]-Skala passen,
/// damit PUCTs Q-Mittelung konsistent bleibt).
fn value_to_win_prob(value: &[f32]) -> f64 {
    let v = value.first().copied().unwrap_or(0.0) as f64;
    (v + 1.0) / 2.0
}

/// KataGo-Stil geblendete Blattbewertung: mischt `value_head`s Sieg-Wahr-
/// scheinlichkeit mit `points_head`s Punktestand-Prognose (`POINTS_UTILITY_
/// WEIGHT`, siehe dortiger Kommentar für die Begründung). `points` nutzt
/// dieselbe Tanh→[0,1]-Skalierung wie `value` (andere Zielformel, gleiche
/// Skala) — bei fehlendem `points`-Kopf (z.B. ältere ONNX-Checkpoints ohne
/// den Kopf) fällt dies auf reines `value` zurück, kein Panik/Skip nötig.
fn blended_leaf_win_prob(value: &[f32], points: &[f32]) -> f64 {
    let wr = value_to_win_prob(value);
    if points.is_empty() {
        return wr;
    }
    let pts = value_to_win_prob(points);
    (1.0 - POINTS_UTILITY_WEIGHT) * wr + POINTS_UTILITY_WEIGHT * pts
}

/// Netz-Blattwert für `state`: unabhängige Pro-Spieler-Werte. Das Netz liefert
/// einen EGO-perspektivischen Wert (die Input-Features hängen von
/// `state.current_player` ab, siehe features.rs/state_to_tensor) — für den
/// jeweils ANDEREN Spieler braucht es deshalb einen zweiten Forward-Pass mit
/// geflipptem `current_player`, nicht einfach `1-wert`. Extrahiert aus
/// `make_node` (dort weiterhin für den `terminal==false`-Pfad genutzt,
/// unverändert), zusätzlich von `round_transition`-Aufrufstellen (Sampling
/// über Runden-Neubefüllungen, siehe `round_transition.rs`) wiederverwendet,
/// da beide denselben Netz-Blattwert brauchen.
pub(crate) fn net_leaf_eval(net: &Net, state: &GameState) -> [f64; 2] {
    let feats = crate::profiling::timed(crate::profiling::note_features_ns, || {
        crate::features::features_for_net(net, state)
    });
    // Paket 1 (Inferenz-Batching, 2026-07-22): bei `MIRROR_OTHER_VAL=false`
    // braucht dieser Aufruf ohnehin ZWEI Forward-Pässe (Mover-/geflippte
    // Perspektive) -- `Net::eval_pair` fasst sie zu einem Batch=2-Aufruf
    // zusammen statt zwei sequenzieller Batch=1-Aufrufe zu bezahlen (Parität
    // siehe `net.rs::eval_pair_matches_two_single_evals`). Bei `true` entfällt
    // der zweite Pass ohnehin (reines `eval`, unverändert).
    let (mover_val, other_val) = if MIRROR_OTHER_VAL {
        // Task #81: Batch=1 (ein einzelner Forward-Pass) -- fuer die Amdahl-
        // Aufteilung des geplanten GPU-Batchers (Task #82).
        let (_logits, value, _moon, points) =
            crate::profiling::timed_net_eval(1, || {
                net.eval(&feats).unwrap_or_else(|_| {
                    (vec![0.0; NUM_ACTIONS], Vec::new(), Vec::new(), Vec::new())
                })
            });
        let mv = blended_leaf_win_prob(&value, &points);
        (mv, 1.0 - mv)
    } else {
        crate::profiling::note_gamestate_clone();
        let mut flipped = state.clone();
        flipped.current_player = 1 - state.current_player;
        let other_feats = crate::features::features_for_net(net, &flipped);
        // Task #81: Batch=2 (`eval_pair` buendelt Mover+Gegner-Pass).
        let ((_logits, value, _moon, points), (_o_logits, o_value, _o_moon, o_points)) =
            crate::profiling::timed_net_eval(2, || {
                net.eval_pair(&feats, &other_feats).unwrap_or_else(|_| {
                    (
                        (vec![0.0; NUM_ACTIONS], Vec::new(), Vec::new(), Vec::new()),
                        (Vec::new(), Vec::new(), Vec::new(), Vec::new()),
                    )
                })
            });
        (blended_leaf_win_prob(&value, &points), blended_leaf_win_prob(&o_value, &o_points))
    };
    if !MIRROR_OTHER_VAL {
        record_perspective_divergence(state.round_number, mover_val, other_val);
    }
    let raw = if state.current_player == 0 { [mover_val, other_val] } else { [other_val, mover_val] };
    // Task #78 (v12c Shrinkage) -- NACH blended_leaf_win_prob; `net_leaf_eval`
    // kennt keine Floor-Shaping-Korrektur (die lebt nur in `make_node`), also
    // gibt es hier keine "vor/nach"-Reihenfolge zu wahren.
    apply_value_shrink(raw, state.round_number)
}

/// Netz-Policy-Priors für `state`: EIN Forward-Pass, wiederverwendet
/// `build_untried_actions`s bestehende Prior-Sortierung/POLICY_MASS_CUTOFF-
/// Kappung/Moon-Order-Expansion unverändert (dieselbe Logik, die `make_node`
/// für die PUCT-Baumexpansion nutzt). Für `round_transition_deep.rs`s
/// Zwischenrunden-Zugwahl (`choose_drafting_action_pruned`) gedacht — dort
/// wird `priors` als generische Closure erwartet (kein `&Net` direkt), damit
/// Tests eine synthetische Closure ohne ONNX-Fixture übergeben können; dies
/// ist der dünne Produktions-Wrapper dafür. Liefert eine leere Liste bei
/// `terminal`-Zuständen (kein Policy-Kopf-Bedarf außerhalb Drafting).
pub(crate) fn drafting_action_priors(net: &Net, state: &GameState) -> Vec<(Action, f32)> {
    if state.phase != Phase::Drafting {
        return Vec::new();
    }
    let feats = crate::profiling::timed(crate::profiling::note_features_ns, || {
        crate::features::features_for_net(net, state)
    });
    // Task #81: Batch=1.
    let (logits, _value, moon, _points) =
        crate::profiling::timed_net_eval(1, || {
            net.eval(&feats).unwrap_or_else(|_| {
                (vec![0.0; NUM_ACTIONS], Vec::new(), Vec::new(), Vec::new())
            })
        });
    let mut moon_scores = [0f32; 5];
    for (i, s) in moon.iter().take(5).enumerate() {
        moon_scores[i] = *s;
    }
    build_untried_actions(state, &logits, &moon_scores, false).0
}

/// Erzeugt einen Knoten: Netz-Forward → Child-Priors (untried) + Blattwert
/// (per `ACTIVE_LEAF`: DFS-Solver oder Netz-Value).
///
/// Task #88 (Hybrid-Suche, kausaler Kopf-Test): `net_value` erlaubt ein
/// ZWEITES Netz für Blattwerte (Value+Points), waehrend `net_policy` weiter
/// die Priors (Policy-Logits) UND die Moon-Order (`moon`, policy-artig)
/// liefert -- siehe Modul-weite Erklaerung bei `net_search_drafting_action_
/// hybrid`. `net_value = None` (alle bisherigen Aufrufstellen) heisst
/// "gleiches Netz fuer beides" -- intern per `std::ptr::eq`-Kurzschluss
/// GENAU der alte Einzel-Netz-Codepfad (ein `eval`/`eval_pair`-Aufruf liefert
/// Policy UND Value zusammen), damit dieser Fall BYTE-IDENTISCH zum
/// Vor-Task-#88-Verhalten bleibt (Paritätstest siehe Testmodul unten:
/// `hybrid_search_with_equal_nets_matches_plain_search`). Nur wenn
/// `net_value` auf ein ANDERES Netz zeigt, greift der separate Hybrid-Pfad
/// (ein Batch=1-Policy-Pass + ein eigener Value-Pass/-Paar).
fn make_node<R: Rng + ?Sized>(
    net_policy: &Net,
    net_value: Option<&Net>,
    state: GameState,
    parent: Option<usize>,
    parent_state: Option<&GameState>,
    action: Option<Action>,
    prior: f32,
    player_who_acted: usize,
    rng: &mut R,
) -> Node {
    let terminal = state.phase != Phase::Drafting;
    // `points` fließt bei ACTIVE_LEAF=Net jetzt in `blended_leaf_win_prob` mit
    // ein (KataGo-Stil Score-Utility, siehe `POINTS_UTILITY_WEIGHT`-Kommentar).
    //
    // Paket 1 (Inferenz-Batching, 2026-07-22): bei ACTIVE_LEAF=Net UND
    // MIRROR_OTHER_VAL=false braucht dieser Knoten ohnehin einen zweiten
    // Forward-Pass für `other_val` (geflippte Perspektive, siehe weiter unten)
    // -- `Net::eval_pair` fasst Mover- und Gegner-Pass zu EINEM Batch=2-
    // ONNX-Aufruf zusammen statt zwei sequenzieller Batch=1-Aufrufe (Parität
    // siehe `net.rs::eval_pair_matches_two_single_evals`). Policy-Logits/
    // Moon-Scores werden nur aus dem Mover-Pass gebraucht -- die geflippte
    // Perspektive dient ausschließlich `other_val`, siehe `other_pass` unten.
    //
    // Task #11 Phase 2 (M3.5): Feature-Erzeugung läuft PRO NETZ
    // (`crate::features::features_for_net`), nicht mehr global VOR der
    // Verzweigung -- im Hybrid-Pfad (`same_net=false`) können `net_policy`
    // und `net_value` unterschiedliche Layouts haben (z.B. ein 2D- und ein
    // flaches Modell im selben Vergleich), ein einzelner geteilter
    // Feature-Puffer wäre für mindestens eines der beiden Netze falsch.
    let need_other_pass = ACTIVE_LEAF == LeafEval::Net && !MIRROR_OTHER_VAL;
    let same_net = net_value.is_none_or(|v| std::ptr::eq(v, net_policy));
    let (logits, value, moon, points, other_pass) = if same_net {
        // Unveraendert gegenueber vor Task #88 (Paritaets-Codepfad).
        let net = net_policy;
        let feats = crate::profiling::timed(crate::profiling::note_features_ns, || {
            crate::features::features_for_net(net, &state)
        });
        if need_other_pass {
            crate::profiling::note_gamestate_clone();
            let mut flipped = state.clone();
            flipped.current_player = 1 - state.current_player;
            let other_feats = crate::features::features_for_net(net, &flipped);
            // Task #81: Batch=2 (`eval_pair`).
            let ((logits, value, moon, points), (_o_logits, o_value, _o_moon, o_points)) =
                crate::profiling::timed_net_eval(2, || {
                    net.eval_pair(&feats, &other_feats).unwrap_or_else(|_| {
                        (
                            (vec![0.0; NUM_ACTIONS], Vec::new(), Vec::new(), Vec::new()),
                            (Vec::new(), Vec::new(), Vec::new(), Vec::new()),
                        )
                    })
                });
            (logits, value, moon, points, Some((o_value, o_points)))
        } else {
            // Task #81: Batch=1.
            let (logits, value, moon, points) =
                crate::profiling::timed_net_eval(1, || {
                    net.eval(&feats).unwrap_or_else(|_| {
                        (vec![0.0; NUM_ACTIONS], Vec::new(), Vec::new(), Vec::new())
                    })
                });
            (logits, value, moon, points, None)
        }
    } else {
        // Task #88 Hybrid-Pfad: Policy/Moon von `net_policy` (EIN Batch=1-
        // Pass, kein Gegner-Pass noetig -- Priors sind rein EGO-
        // perspektivisch), Value/Points von `net_value` (Mover+Gegner-Pass
        // wie im Nicht-Hybrid-Fall, siehe `net_leaf_eval`-Kommentar).
        // Task #11 Phase 2 (M3.5): jeweils EIGENER, netz-spezifischer
        // Feature-Puffer -- `net_policy` und `net_value` koennen
        // unterschiedliche Layouts haben.
        let net_value = net_value.expect("same_net=false impliziert Some(..)");
        let feats_policy = crate::profiling::timed(crate::profiling::note_features_ns, || {
            crate::features::features_for_net(net_policy, &state)
        });
        let (logits, _p_value, moon, _p_points) = crate::profiling::timed_net_eval(1, || {
            net_policy
                .eval(&feats_policy)
                .unwrap_or_else(|_| (vec![0.0; NUM_ACTIONS], Vec::new(), Vec::new(), Vec::new()))
        });
        if need_other_pass {
            crate::profiling::note_gamestate_clone();
            let mut flipped = state.clone();
            flipped.current_player = 1 - state.current_player;
            let feats_value = crate::features::features_for_net(net_value, &state);
            let other_feats_value = crate::features::features_for_net(net_value, &flipped);
            let ((_v_logits, value, _v_moon, points), (_o_logits, o_value, _o_moon, o_points)) =
                crate::profiling::timed_net_eval(2, || {
                    net_value.eval_pair(&feats_value, &other_feats_value).unwrap_or_else(|_| {
                        (
                            (Vec::new(), Vec::new(), Vec::new(), Vec::new()),
                            (Vec::new(), Vec::new(), Vec::new(), Vec::new()),
                        )
                    })
                });
            (logits, value, moon, points, Some((o_value, o_points)))
        } else {
            let feats_value = crate::features::features_for_net(net_value, &state);
            let (_v_logits, value, _v_moon, points) = crate::profiling::timed_net_eval(1, || {
                net_value.eval(&feats_value).unwrap_or_else(|_| (Vec::new(), Vec::new(), Vec::new(), Vec::new()))
            });
            (logits, value, moon, points, None)
        }
    };

    node_from_net_outputs(
        net_policy, net_value, state, parent, parent_state, action, prior, player_who_acted, terminal,
        logits, value, moon, points, other_pass, rng,
    )
}

/// Baut einen [`Node`] aus BEREITS BERECHNETEN Netz-Rohausgaben
/// (`logits`/`value`/`moon`/`points`/`other_pass`) -- reine Extraktion aus
/// `make_node` (Perf-Auftrag, 2026-08-02: Gumbel-Wurzel-Kandidaten-
/// Buendelung), KEINE Verhaltensaenderung: `make_node` ruft dies direkt im
/// Anschluss an seinen eigenen (unveraendert EINZELNEN) Netz-Eval-Block auf.
/// Der Sinn der Trennung: fuer eine GEBUENDELTE Wurzel-Kandidaten-Expansion
/// (`batched_expand_root_candidates` unten) werden die Netz-Rohausgaben
/// FUER ALLE KANDIDATEN GEMEINSAM per `Net::eval_batch` berechnet (EIN
/// ONNX-Aufruf statt `m_prime` einzelner) -- die eigentliche Knoten-
/// Konstruktion (Blattwert-Blending, Value-Shrink, Floor-/Plate-Shaping,
/// `build_untried_actions`, ...) bleibt dabei UNVERAENDERT dieselbe Funktion
/// wie im unbatchten Pfad, angewandt auf JEDEN Kandidaten einzeln -- kein
/// Doppelpflege-Risiko zwischen zwei Kopien derselben Logik.
#[allow(clippy::too_many_arguments)]
fn node_from_net_outputs<R: Rng + ?Sized>(
    net_policy: &Net,
    net_value: Option<&Net>,
    state: GameState,
    parent: Option<usize>,
    parent_state: Option<&GameState>,
    action: Option<Action>,
    prior: f32,
    player_who_acted: usize,
    terminal: bool,
    logits: Vec<f32>,
    value: Vec<f32>,
    moon: Vec<f32>,
    points: Vec<f32>,
    other_pass: Option<(Vec<f32>, Vec<f32>)>,
    rng: &mut R,
) -> Node {
    let mut moon_scores = [0f32; 5];
    for (i, s) in moon.iter().take(5).enumerate() {
        moon_scores[i] = *s;
    }
    // Cutoff ausgesetzt (siehe `build_untried_actions`-Kommentar zu
    // `skip_cutoff`, Fund 4) an der Wurzel (`parent.is_none()`, unabhängig
    // davon, ob Root-Noise gerade aktiv ist) -- UND (Paket 2, mctx-Treue
    // Tiefe-≥1-Auswahl, 2026-07-22) an JEDEM Knoten, wenn `USE_GUMBEL_SEARCH`
    // aktiv ist: die neue `gumbel_select_child`-Auswahlregel entscheidet
    // selbst über children ∪ untried, ohne einen vorab gekappten Long Tail zu
    // brauchen -- der PUCT-Legacy-Pfad (`USE_GUMBEL_SEARCH=false`) bleibt
    // unverändert nur an der Wurzel ausgesetzt (sein eigener Widening-Cap in
    // `build_net_tree` bremst dort weiterhin, wie bisher).
    let skip_cutoff = parent.is_none() || USE_GUMBEL_SEARCH;
    let (untried, n_actions) = if terminal {
        (Vec::new(), 0)
    } else {
        build_untried_actions(&state, &logits, &moon_scores, skip_cutoff)
    };

    // Blattwert: unabhängige Pro-Spieler-Werte. Das Netz liefert einen
    // EGO-perspektivischen Wert (die Input-Features hängen von
    // `state.current_player` ab, siehe features.rs/state_to_tensor) — für
    // den jeweils ANDEREN Spieler braucht es deshalb einen zweiten
    // Forward-Pass mit geflipptem `current_player`, nicht einfach `1-wert`.
    let leaf_value = match ACTIVE_LEAF {
        LeafEval::Net => {
            let mover_val = blended_leaf_win_prob(&value, &points);
            let other_val = if MIRROR_OTHER_VAL {
                1.0 - mover_val
            } else {
                // `other_pass` wurde oben bereits per `eval_pair` MIT dem
                // Mover-Pass zusammen berechnet (Paket 1) -- hier nur noch
                // auslesen, kein zweiter Forward-Pass mehr nötig.
                let (o_value, o_points) =
                    other_pass.expect("need_other_pass deckt genau diesen Zweig ab");
                blended_leaf_win_prob(&o_value, &o_points)
            };
            // Perspektiven-/OOD-Audit (siehe Modul-Kommentar oben) -- nur
            // aussagekräftig, wenn `other_val` ein ECHTER zweiter Forward-Pass
            // ist (bei `MIRROR_OTHER_VAL=true` wäre die Divergenz trivial 0,
            // per Konstruktion, keine echte Information).
            if !MIRROR_OTHER_VAL {
                record_perspective_divergence(state.round_number, mover_val, other_val);
            }
            let mut today_value =
                if state.current_player == 0 { [mover_val, other_val] } else { [other_val, mover_val] };

            // Task #78 (v12c Shrinkage) -- NACH blended_leaf_win_prob (oben),
            // aber VOR dem Floor-Shaping-Additiv (unten): das exakte
            // Floor-Signal ist eine reine State-Funktion und soll NICHT durch
            // die Netz-Unsicherheits-Schrumpfung gedämpft werden, nur der
            // rohe Netz-Blattwert selbst. Bei `VALUE_SHRINK_ENABLED=false`
            // (Standard) exakte Identität.
            today_value = apply_value_shrink(today_value, state.round_number);

            // Exakte Floor-Straf-Korrektur (siehe `floor_shaping_delta`-Kommentar) --
            // reine State-Funktion, kein Netz-Forward-Pass, direkt additiv auf
            // beide Perspektiven (Nullsummen-Charakter wie beim own-opp-Value-Ziel).
            let floor_shift = FLOOR_SHAPING_WEIGHT * floor_shaping_delta(&state).tanh();
            today_value[0] = (today_value[0] + floor_shift).clamp(0.0, 1.0);
            today_value[1] = (today_value[1] - floor_shift).clamp(0.0, 1.0);

            // Task #93: Wertungsplatten-Fortschritts-Additiv, NACH dem
            // Floor-Shaping-Additiv (koexistiert additiv, siehe
            // `apply_plate_shaping`-Kommentar). Bei `PLATE_SHAPING_ENABLED=false`
            // (Standard) exakte Identität -- der Block wird gar nicht ausgeführt.
            today_value = apply_plate_shaping(today_value, &state, parent_state);

            // Rundenübergang (Phase wechselt von Drafting weg) per Chance-Node-
            // Sampling statt Einzelwert bewerten -- siehe round_transition.rs
            // fuer die Begruendung (verrauschtes Trainingsziel/Blattwert, da die
            // Fabrik-Neubefuellung sonst nirgends als echter Zufallsknoten
            // repraesentiert ist). Standardmaessig AUS (siehe Konstante unten) --
            // erst nach einer Val-R²-Verbesserung im Trainingsziel-Pfad
            // (self_play.rs::play_net_self_play_game) aktivieren.
            if terminal && ROUND_TRANSITION_SAMPLING {
                match crate::round_transition::resolve_to_pre_chance(&state) {
                    Some(pre) => crate::round_transition::sample_round_transition_value(
                        &pre,
                        crate::round_transition::N_SAMPLES_SEARCH,
                        // Dead Code bei `ROUND_TRANSITION_SAMPLING=false` (Standard) --
                        // faellt fuer eine spaetere Aktivierung konsistent auf den
                        // Value-Net (falls Hybrid) statt Policy-Net zurueck.
                        |s, _rng| net_leaf_eval(net_value.unwrap_or(net_policy), s),
                        rng,
                        std::time::Instant::now() + crate::round_transition::TIME_BUDGET,
                    ),
                    None => today_value, // defensiv, sollte durch das `terminal`-Gating nie vorkommen
                }
            } else {
                today_value
            }
        }
        LeafEval::Dfs => crate::profiling::timed(crate::profiling::note_dfs_eval_ns, || {
            crate::mcts::evaluate(&state, n_actions)
        }),
    };

    Node {
        parent,
        children: Vec::new(),
        untried,
        action,
        player_who_acted,
        visits: 0,
        value: 0.0,
        prior,
        state,
        terminal,
        leaf_value,
        n_actions,
    }
}

// ── Gumbel AlphaZero (Danihelka/Guez/Schrittwieser/Silver, ICLR 2022) ───────
//
// Motivation (siehe evaluations/STATUS.md, "Struktureller Durchbruch"-
// Abschnitt): selbst nach den Widening-/Tiebreak-Fixes verteilt PUCT sein
// Sim-Budget bei ~150-195 Kandidaten in Runde 1 extrem duenn. Gumbel-Top-m +
// Sequential Halving konzentriert das Budget gezielt auf wenige Kandidaten
// statt "1 Besuch auf 150". Alle Formeln unten exakt aus der DeepMind-mctx-
// Referenzimplementierung (github.com/google-deepmind/mctx: seq_halving.py,
// qtransforms.py, action_selection.py, policies.py) uebernommen, NICHT nur
// aus der Paper-Prosa rekonstruiert -- siehe Plan-Dokument fuer die volle
// Herleitung/Quellenlage.

/// Gewicht der Q-Komponente relativ zum Log-Prior in Gumbel-Scores (§3 des
/// Plans): `σ(q) = (c_visit + max_N) · c_scale · q`. Paper-Werte (NICHT
/// mctx-Bibliotheks-Default 0.1 fuer c_scale) -- unsere Q sind schon
/// [0,1]-Win-Wahrscheinlichkeiten, keine zusaetzliche Min-Max-Rescale wie
/// bei mctx' unbeschraenkten Atari-Rewards noetig.
const GUMBEL_C_VISIT: f64 = 50.0;
/// GEMESSEN UND BESTAETIGT (2026-07-29, Task #18) -- bleibt 1.0.
///
/// `tools/gumbel_scale_calibration.py` hat ueber 216 frozen-set-Stellungen
/// (v18_best @ 400 Sims, letzte Sequential-Halving-Phase) erhoben, wie schwer
/// `sigma(q)` gegenueber `ln(prior)` wiegt -- beide ueber DIESELBE
/// Kandidatenmenge:
///   delta_q          Median 0,0073   delta_ln(prior)  Median 1,11
///   max_N            Median 96       Verhaeltnis      Median 1,23
///   je Runde: 1,01 / 1,08 / 1,56 / 1,44
/// q und Prior wiegen also praktisch gleich schwer; fuer exakte Gleichheit
/// waere c_scale = 0,81 noetig. Die Begruendung oben traegt damit.
///
/// GEGENPROBE (gepaarter Arena-A/B, v18_best@400 vs v17_best@400, 400 Spiele
/// je Arm, identischer Basis-Seed 31415926), c_scale 1,0 gegen 0,3:
///   Arm 1,0: Champion 210:190 | Score 39,13 vs 37,77 (Summe 76,90) | Floor 13,85/14,97
///   Arm 0,3: Champion 248:152 | Score 35,59 vs 31,32 (Summe 66,91) | Floor 15,61/17,32
///   McNemar p = 0,0057
///
/// Die Siegquote spricht fuer 0,3 -- **uebernommen wurde es trotzdem NICHT**.
/// Bei 0,3 spielen BEIDE Seiten massiv schlechter: zehn Punkte weniger in der
/// Summe (-13 %) und deutlich mehr Bodenstrafen auf beiden Brettern. Ein
/// kleineres c_scale verschiebt Gewicht von der SUCHE zum Policy-Prior; die
/// Suche traegt dann weniger bei. Dass v18 dabei oefter gewinnt, misst nur, dass
/// v17 unter der verschlechterten Suche staerker einbricht (v18 hat den besseren
/// Prior) -- also RELATIVE Robustheit, nicht Staerke.
///
/// LEHRE: bei einer engine-weiten Aenderung, die BEIDE Seiten trifft, ist die
/// Siegquote im Champion-gegen-Vorgaenger-Duell KEIN gueltiges Staerkemass. Der
/// absolute Ø-Score ist hier das entscheidende Signal gewesen.
const GUMBEL_C_SCALE: f64 = 1.0;

/// Anzahl der per Gumbel-Top-m an der Wurzel gezogenen Kandidaten (vor
/// Sequential Halving). Paper-/mctx-Standardwert, aus Go/Schach-Experimenten
/// mit aehnlichem/groesserem Verzweigungsfaktor -- fuer dieses Spiel noch
/// nicht eigens kalibriert (siehe Plan-Dokument, "Offene Risiken").
///
/// Dient seit Task #14 (PCR-Vorbereitung, 2026-08-02) als OBERE Grenze
/// (Ceiling) fuer `gumbel_top_m_for_budget` unten, nicht mehr als der fuer
/// JEDEN Suchaufruf feste Wert -- bleibt als eigene Konstante bestehen, weil
/// `lib.rs::engine_config_json` sie weiterhin als Referenz-/Ceiling-Wert ins
/// Lauf-Manifest schreibt (das tatsaechliche, budgetabhaengige M eines
/// einzelnen Suchaufrufs steht dort NICHT drin, nur die Obergrenze).
pub const GUMBEL_TOP_M: usize = 16;

/// Sim-budget-abhaengige Ober-Grenze fuer die Gumbel-Top-m-Kandidatenzahl
/// (Task #14, PCR-Vorbereitung, 2026-08-02): vorher war `GUMBEL_TOP_M` eine
/// reine Compile-Time-Konstante, gleich fuer JEDEN Suchaufruf, unabhaengig
/// vom tatsaechlichen Sim-Budget dieses Zugs. Mit Playout-Cap-Randomization
/// (KataGo-Vorbild, siehe `self_play.rs`) laufen im selben Prozess klassische
/// Voll-Suchen (400/600 Sims) UND sehr guenstige Cheap-Suchen (z.B. 150 Sims
/// oder weniger). Bei fixem M=16 wuerde eine Cheap-Suche mit z.B. 64 Sims
/// versuchen, 16 Kandidaten ueber `ceil(log2(16))=4` Sequential-Halving-Phasen
/// zu verteilen: 16*4=64 Sim-"Slots" (siehe `remaining_slots` unten) sind dann
/// schon aufgebraucht, nur um JEDEN Kandidaten EINMAL pro Phase zu besuchen --
/// keine Reserve mehr fuer die eigentliche Differenzierung (Sequential
/// Halving braucht MEHRERE Besuche pro Kandidat pro Phase, damit die
/// Q-Schaetzung, nach der die naechste Haelfte eliminiert wird, ueberhaupt
/// aussagekraeftig ist).
///
/// Formel: `m(budget) = clamp(round(budget / 16), 4, GUMBEL_TOP_M)`.
/// - Referenzteiler 16: bei den bisherigen Standard-Budgets ergibt
///   `round(400/16)=25` bzw. `round(600/16)=38`, beide werden vom oberen
///   Clamp auf `GUMBEL_TOP_M=16` gekappt -- IDENTISCHES Verhalten zur alten
///   fixen Konstante bei allen bisher produktiv genutzten Sim-Zahlen (400,
///   600). Regressionstest: `gumbel_top_m_for_budget_unchanged_at_400_and_600_sims`.
/// - Obere Grenze `GUMBEL_TOP_M`: der bisherige Paper-/mctx-Standardwert wird
///   durch die Skalierung nie ueberschritten -- keine unkalibrierte
///   Vergroesserung der Wurzelbreite ueber den bisher genutzten Bereich
///   hinaus.
/// - Untere Grenze 4: unter 4 Kandidaten verliert Sequential Halving an Sinn
///   (mit `ceil(log2(m))`-Phasen braucht selbst `m=2` schon eine
///   Halbierungs-Phase; bei `m=1` degeneriert die Suche zur reinen
///   Tiefensuche eines einzigen Zugs, siehe `candidates.len() <= 1`-Zweig
///   unten) -- 4 haelt auch bei sehr kleinen Cheap-Budgets eine minimale
///   Kandidaten-Diversitaet an der Wurzel.
/// - Dazwischen (z.B. Cheap-Suche mit 150 Sims -> `round(150/16)=9`):
///   proportional zum Budget, damit jeder Halbierungs-"Slot"
///   (`remaining_slots = remaining_phases * current.len()`, s.u.) im Schnitt
///   in einer aehnlichen Groessenordnung Sims pro Kandidat bleibt wie beim
///   bisherigen 400/600-Sims-Betrieb bei M=16.
pub fn gumbel_top_m_for_budget(sims: u32) -> usize {
    let raw = (sims as f64 / 16.0).round() as i64;
    raw.clamp(4, GUMBEL_TOP_M as i64) as usize
}

/// Schaltet die Suche komplett auf Gumbel-AlphaZero um (Wurzel: Gumbel-Top-m
/// + Sequential Halving statt Dirichlet-Noise + PUCT; Tiefe≥1: neue
/// deterministische Auswahlregel statt `best_puct`; Policy-Ziel: completed-Q-
/// Softmax statt Besuchsanteil). Standardmaessig AUS, bis Phase 3 (Arena-
/// Validierung ohne Neu-Training) ein Ergebnis liefert -- gleiches Muster
/// wie `ACTIVE_LEAF`/`MIRROR_OTHER_VAL`.
pub const USE_GUMBEL_SEARCH: bool = true;

/// Schaltet die dynamic_sims-Entkopplung im Gumbel-Netzpfad frei (externer
/// Befund, 2026-07-20, siehe `net_effective_sims`). Standardmäßig AN
/// (Nutzer-Entscheidung, 2026-07-21) -- Arena-Ablation davor (n=100, Netz
/// fest auf 330 Sims vs. Heuristik unverändert bei 150) ergab 20:80 (20%),
/// innerhalb des Rauschbands der 22-26%-Bestmarke, kein klarer Effekt in
/// diesem einzelnen Test, aber auch keine Verschlechterung -- die
/// theoretische Begründung (Gumbel-Wurzelbreite ist fix, dynamic_sims'
/// Kopplung an die Aktionszahl hat dort keine Grundlage mehr) bleibt
/// unabhängig vom uneindeutigen Arena-Ergebnis gültig.
/// **WICHTIG für alle Aufrufstellen mit `base_sims`** (Server-Mensch-vs-KI,
/// `self_play.py --mode network`, Arena-Konstanten): `dynamic_sims` skalierte
/// einen Wert wie 150 bisher automatisch auf ~185-499 hoch (siehe
/// `evaluations/actions_per_round.md`) -- mit dieser Umstellung ist der
/// übergebene Wert jetzt die TATSÄCHLICHE Sims-Zahl, keine Basis mehr.
/// Bestehende `base_sims`-Werte ggf. entsprechend nach oben anpassen, um
/// dieselbe effektive Suchtiefe zu behalten (z.B. `arena.py`s bisheriges
/// `NET_SIMS=150` ⇒ vergleichbar wäre eher ~300-330 flach).
pub const DECOUPLE_NET_SIMS_FROM_ACTIONS: bool = true;

/// Sims-Skalierung für NETZGEFÜHRTE Suche (Gumbel oder PUCT-Legacy) --
/// externer Befund (2026-07-20): `mcts::dynamic_sims`s Kopplung an die
/// Aktionszahl war für die alte PUCT-Zwangs-Expansion begründet (mehr
/// Kandidaten -> mehr Sims nötig, sonst Breitensuche ohne Differenzierung).
/// Mit Gumbel-Top-m + Sequential Halving ist die Wurzelbreite FIX
/// (`GUMBEL_TOP_M`) -- 195 legale Aktionen kosten nicht mehr Suchaufwand
/// als 44, dieselben Sims werden unabhängig von der Aktionszahl sinnvoll
/// auf `GUMBEL_TOP_M` Kandidaten verteilt. Die Kopplung ist im Gumbel-Pfad
/// daher THEORETISCH eine Fehlallokation (Zusatzbudget an breiten Wurzeln,
/// wo es am wenigsten bringt; Einsparung an engen Stellungen, wo es am
/// meisten hilft) -- EMPIRISCH aber noch nicht bestätigt (siehe
/// `DECOUPLE_NET_SIMS_FROM_ACTIONS`-Kommentar), daher Toggle statt Standard.
/// Bei `USE_GUMBEL_SEARCH=true UND DECOUPLE_NET_SIMS_FROM_ACTIONS=true`:
/// `base_sims` unverändert zurückgeben. Sonst (inkl. PUCT-Legacy-Pfad, wo
/// `dynamic_sims` weiterhin seine ursprüngliche Begründung hat): normales
/// `dynamic_sims`-Verhalten. Betrifft NUR netzgeführte Suche -- die
/// Heuristik-MCTS (`mcts.rs`) behält `dynamic_sims` an ihren eigenen
/// Aufrufstellen unverändert (braucht die Skalierung weiterhin, da sie
/// klassisches PUCT+Widening ohne Gumbel nutzt).
pub fn net_effective_sims(base_sims: u32, num_actions: usize) -> u32 {
    if USE_GUMBEL_SEARCH && DECOUPLE_NET_SIMS_FROM_ACTIONS {
        base_sims
    } else {
        crate::mcts::dynamic_sims(base_sims, num_actions)
    }
}

/// Gumbel(0,1)-Ziehung: `-ln(-ln(U))`, `U ~ Uniform(0,1)` (offenes Intervall,
/// `U=0` waere `ln(0)=-inf`).
fn sample_gumbel<R: Rng + ?Sized>(rng: &mut R) -> f64 {
    let u: f64 = rng.random_range(f64::MIN_POSITIVE..1.0);
    -(-u.ln()).ln()
}

/// `σ(q) = (c_visit + max_N) · c_scale · q` -- siehe Modul-Kommentar.
fn gumbel_sigma(q: f64, max_n: u32) -> f64 {
    (GUMBEL_C_VISIT + max_n as f64) * GUMBEL_C_SCALE * q
}

/// Eigener Netz-/DFS-Blattwert von `nid`, aus der Sicht des an DIESEM Knoten
/// ziehenden Spielers (`state.current_player`) -- NICHT `nodes[nid].value`
/// (das akkumuliert aus der Sicht des Spielers, der in `nid` HINEIN gezogen
/// ist, i.d.R. der GEGNER von `state.current_player`). Für `v_mix` brauchen
/// wir explizit die Perspektive des Spielers, dessen Kinder gerade bewertet
/// werden -- exakt dieselbe Perspektive, in der `nodes[cid].value/visits`
/// für Kinder von `nid` bereits akkumuliert (deren `player_who_acted` ist
/// der Zieher AN `nid`, siehe `make_node`-Aufruf beim Expandieren).
fn node_own_value(nodes: &[Node], nid: usize) -> f64 {
    nodes[nid].leaf_value[nodes[nid].state.current_player]
}

/// `v_mix` (§4 des Plans) -- PRIOR-gewichtet über besuchte Kinder von `nid`
/// (NICHT visit-gewichtet, ein leicht zu verwechselnder Punkt):
/// `v_mix = (v(nid) + N_total · Σ_besucht[π(a)·Q(a)] / Σ_besucht[π(a)]) / (1 + N_total)`.
/// Fällt bei `N_total=0` (noch kein Kind besucht) exakt auf `v(nid)` zurück.
fn v_mix(nodes: &[Node], nid: usize) -> f64 {
    let v_node = node_own_value(nodes, nid);
    let n_total: f64 = nodes[nid].children.iter().map(|&c| nodes[c].visits as f64).sum();
    if n_total <= 0.0 {
        return v_node;
    }
    let mut prior_sum = 0.0f64;
    let mut weighted_q_sum = 0.0f64;
    for &c in &nodes[nid].children {
        if nodes[c].visits == 0 {
            continue;
        }
        let p = (nodes[c].prior as f64).max(1e-9);
        let q = nodes[c].value / nodes[c].visits as f64;
        prior_sum += p;
        weighted_q_sum += p * q;
    }
    if prior_sum <= 0.0 {
        return v_node;
    }
    (v_node + n_total * (weighted_q_sum / prior_sum)) / (1.0 + n_total)
}

/// `(Prior, completed Q)` je Kandidat von `nid`, Reihenfolge: erst
/// `children` (besucht → eigenes Q), dann `untried` (unbesucht → `v_mix`,
/// derselbe Wert für alle unbesuchten Kandidaten desselben Knotens).
fn completed_q_per_candidate(nodes: &[Node], nid: usize) -> Vec<(f64, f64)> {
    let vmix = v_mix(nodes, nid);
    let mut out: Vec<(f64, f64)> =
        Vec::with_capacity(nodes[nid].children.len() + nodes[nid].untried.len());
    for &c in &nodes[nid].children {
        let prior = nodes[c].prior as f64;
        let q = if nodes[c].visits > 0 { nodes[c].value / nodes[c].visits as f64 } else { vmix };
        out.push((prior, q));
    }
    for (_, prior) in &nodes[nid].untried {
        out.push((*prior as f64, vmix));
    }
    out
}

/// Softmax über `f64`-Scores (eigene Kopie statt `net::softmax`, das auf
/// `f32` arbeitet -- Gumbel-Score-Summen (Log-Prior + σ(Q)) profitieren von
/// der zusätzlichen Präzision).
fn softmax_f64(scores: &[f64]) -> Vec<f64> {
    let m = scores.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
    let exps: Vec<f64> = scores.iter().map(|&x| (x - m).exp()).collect();
    let sum: f64 = exps.iter().sum();
    if sum > 0.0 {
        exps.iter().map(|&e| e / sum).collect()
    } else {
        vec![1.0 / scores.len().max(1) as f64; scores.len()]
    }
}

/// `π'_node(a) = softmax(ln(prior(a)) + σ(completedQ(a)))` über
/// `children ∪ untried` von `nid`, gleiche Reihenfolge wie
/// `completed_q_per_candidate`. `max_N` (für σ) = größte Besuchszahl unter
/// `nid`s Kindern JETZT (wächst über die Suche).
fn improved_policy(nodes: &[Node], nid: usize) -> Vec<f64> {
    let max_n = nodes[nid].children.iter().map(|&c| nodes[c].visits).max().unwrap_or(0);
    let cq = completed_q_per_candidate(nodes, nid);
    let scores: Vec<f64> =
        cq.iter().map(|&(p, q)| p.max(1e-9).ln() + gumbel_sigma(q, max_n)).collect();
    softmax_f64(&scores)
}

/// PUCT: bestes Kind = argmax Q + c·P·√N_parent/(1+N_child). Priors über die
/// Kinder normalisiert (wie agents/mcts.py `_best_child`).
fn best_puct(nodes: &[Node], nid: usize, c_puct: f64) -> usize {
    let sqrt_pv = (nodes[nid].visits.max(1) as f64).sqrt();
    let psum: f64 = nodes[nid]
        .children
        .iter()
        .map(|&c| nodes[c].prior as f64)
        .sum::<f64>()
        .max(1e-8);
    let mut best = nodes[nid].children[0];
    let mut best_score = f64::NEG_INFINITY;
    for &cid in &nodes[nid].children {
        let n = nodes[cid].visits as f64;
        let q = if n > 0.0 { nodes[cid].value / n } else { 0.0 };
        let p = nodes[cid].prior as f64 / psum;
        let score = q + c_puct * p * sqrt_pv / (1.0 + n);
        if score > best_score {
            best_score = score;
            best = cid;
        }
    }
    best
}

/// Meistbesuchtes Wurzelkind (Tiebreak: Mittelwert Q, dann Prior) — Pendant
/// zu `mcts::best_root_child`. Externer Bugfix-Hinweis (2026-07-20): ein
/// reines `max_by_key(|c| nodes[c].visits)` ist hier ein echter Bug --
/// Rusts `max_by_key`/`max_by` liefern bei Gleichstand das LETZTE Maximum,
/// Kinder werden aber in ABSTEIGENDER Prior-Reihenfolge expandiert (siehe
/// `build_net_tree`s `untried.remove(0)`), das letzte (gleichstehende) Kind
/// ist also das mit dem NIEDRIGSTEN Prior im behaltenen Set. Besuchsgleich-
/// stand ist in frühen, hochverzweigten Runden wegen der (jetzt engeren,
/// aber nicht eliminierten) Voll-Expansions-Neigung der Normalfall --
/// ohne Tiebreak würde dort systematisch der am schlechtesten bewertete
/// Kandidat gespielt.
fn best_root_child(nodes: &[Node], children: &[usize]) -> Option<usize> {
    children.iter().copied().max_by(|&a, &b| {
        let qa = if nodes[a].visits > 0 { nodes[a].value / nodes[a].visits as f64 } else { 0.0 };
        let qb = if nodes[b].visits > 0 { nodes[b].value / nodes[b].visits as f64 } else { 0.0 };
        nodes[a]
            .visits
            .cmp(&nodes[b].visits)
            .then(qa.partial_cmp(&qb).unwrap_or(std::cmp::Ordering::Equal))
            .then(nodes[a].prior.partial_cmp(&nodes[b].prior).unwrap_or(std::cmp::Ordering::Equal))
    })
}

/// Tiefe-≥1-Auswahl über `children ∪ untried` von `nid` (Gumbel-Pendant zu
/// `best_puct`, §6 des Plans, JETZT mctx-treu ohne PUCT-geerbte Forced-
/// Expansion/Widening-Cap-Sonderbehandlung -- Paket 2 des Speed-Bündels,
/// 2026-07-22): `argmax[π'_node(a) − N(a)/(1+ΣN)]` über ALLE Kandidaten,
/// unbesuchte (untried) zählen mit `N(a)=0`, exakt wie mctx' `action_selection.py`
/// (vorher: nur über `nodes[nid].children`, WELCHE Kandidaten überhaupt als
/// Kind entstehen durften, entschied ein separater Progressive-Widening-Cap
/// -- beides jetzt entfernt, siehe `descend_and_backprop`).
///
/// Rückgabe: Index INNERHALB des Kombi-Vektors (`completed_q_per_candidate`-
/// Reihenfolge: erst `children`, dann `untried`). `< children.len()` heißt
/// bestehendes Kind (`nodes[nid].children[idx]`), sonst unbesuchter Kandidat
/// bei Offset `idx - children.len()` in `nodes[nid].untried` -- der Aufrufer
/// entscheidet anhand dieses Index, ob deszendiert oder on-demand expandiert
/// wird.
fn gumbel_select_child(nodes: &[Node], nid: usize) -> usize {
    let policy = improved_policy(nodes, nid);
    let n_children = nodes[nid].children.len();
    let sum_n: f64 = nodes[nid].children.iter().map(|&c| nodes[c].visits as f64).sum();
    let mut best = 0usize;
    let mut best_adv = f64::NEG_INFINITY;
    for (i, &p) in policy.iter().enumerate() {
        let n_a = if i < n_children { nodes[nodes[nid].children[i]].visits as f64 } else { 0.0 };
        let adv = p - n_a / (1.0 + sum_n);
        if adv > best_adv {
            best_adv = adv;
            best = i;
        }
    }
    best
}

/// Finale Wurzel-Zugwahl im Gumbel-Modus (§7 des Plans, `gumbel_scale=0` für
/// Arena/Produktion -- keine Ziehung): unter den Wurzelkindern mit
/// `N(a) == max_a N(a)` (den Sequential-Halving-Überlebenden), `argmax[
/// ln(prior(a)) + σ(completedQ(a))]`. Für besuchte Überlebende ist
/// `completedQ` immer das eigene Q (nie `v_mix`, siehe `completed_q`-
/// Kommentar), daher direkt `value/visits` statt der vollen
/// `completed_q_per_candidate`-Maschinerie.
fn gumbel_final_root_action(nodes: &[Node]) -> Option<usize> {
    let children = &nodes[0].children;
    if children.is_empty() {
        return None;
    }
    let max_n = children.iter().map(|&c| nodes[c].visits).max().unwrap_or(0);
    children
        .iter()
        .copied()
        .filter(|&c| nodes[c].visits == max_n)
        .max_by(|&a, &b| {
            let score = |cid: usize| -> f64 {
                let prior = (nodes[cid].prior as f64).max(1e-9);
                let q = if nodes[cid].visits > 0 { nodes[cid].value / nodes[cid].visits as f64 } else { 0.0 };
                prior.ln() + gumbel_sigma(q, max_n)
            };
            score(a).partial_cmp(&score(b)).unwrap_or(std::cmp::Ordering::Equal)
        })
}

/// Dispatcht die finale Wurzel-Zugwahl auf `gumbel_final_root_action`
/// (Gumbel-Modus) oder `best_root_child` (PUCT), je nach `USE_GUMBEL_SEARCH`.
fn select_final_root_child(nodes: &[Node]) -> Option<usize> {
    if USE_GUMBEL_SEARCH {
        gumbel_final_root_action(nodes)
    } else {
        best_root_child(nodes, &nodes[0].children)
    }
}

// ── Task #95: Debug-Trace (Value-Head-Einschätzung + granularer Gumbel-Trace) ──
//
// Beide unten definierten Strukturen fassen AUSSCHLIESSLICH bereits an anderer
// Stelle berechnete Zwischenwerte zusammen -- kein zusätzlicher Netz-Aufruf im
// Suchpfad selbst (`RootValueDebug` nutzt zwar EINEN eigenen `Net::eval`-aufruf,
// aber NUR wenn explizit angefordert, siehe `compute_root_value_debug`, und
// komplett losgelöst von `nodes`/RNG der eigentlichen Suche). Alle
// Trace-Sammelstellen in `build_gumbel_tree` sind reine Lesezugriffe auf
// bereits vorhandene lokale Werte (kein Effekt auf Auswahl/Backprop/RNG-Strom)
// -- siehe Paritätstest `gumbel_trace_collection_does_not_change_search`.

/// Root-Value-Debug-Breakdown (Anforderung 1, Task #95): rohe Value-/
/// Points-Kopf-Ausgaben + alle Blend-/Shaping-Zwischenschritte für die
/// ROOT-Position, aus Sicht des tatsächlich ziehenden Spielers (Ego). Nur
/// über `compute_root_value_debug` befüllt, ausschließlich vom Debug-Pfad
/// (`ai_debug_net_json`) angefordert.
#[derive(Clone, Debug)]
pub struct RootValueDebug {
    /// Roher `value_head`-Tanh-Output (Ego-Perspektive, VOR jeder Blend-/
    /// Shrink-/Floor-Korrektur).
    pub raw_value: f32,
    /// Roher `points_head`-Output, falls das Netz einen hat (ältere
    /// Checkpoints ohne Punktekopf → `None`).
    pub points_forecast: Option<f32>,
    /// `value_to_win_prob(raw_value)` -- reine Sieg-Wahrscheinlichkeit ohne
    /// Points-Blend.
    pub win_prob: f64,
    /// `blended_leaf_win_prob` (KataGo-Blend) NACH der Value-Shrinkage (Task
    /// #78, aktuell `VALUE_SHRINK_ENABLED=false` ⇒ Identität) -- exakt die
    /// Größe, die tatsächlich als Blattwert in die Suche einfließt, NUR noch
    /// ohne das Floor-Shaping-Additiv (separat ausgewiesen).
    pub blended_utility: f64,
    /// Floor-Shaping-Additiv (`FLOOR_SHAPING_WEIGHT · tanh(floor_shaping_delta)`),
    /// bereits auf Ego-Perspektive gedreht (positiv = Vorteil für den
    /// ziehenden Spieler). 0.0, wenn `FLOOR_SHAPING_WEIGHT=0` (Feature aus).
    pub floor_shift: f64,
    /// `(blended_utility + floor_shift)`, geklammert auf [0,1] -- identisch
    /// zum tatsächlichen `leaf_value[ego]` der Wurzel.
    pub final_value: f64,
}

impl RootValueDebug {
    fn to_json(&self) -> Value {
        json!({
            "raw_value": self.raw_value,
            "points_forecast": self.points_forecast,
            "win_prob": self.win_prob,
            "blended_utility": self.blended_utility,
            "floor_shift": self.floor_shift,
            "final_value": self.final_value,
        })
    }
}

/// Rechnet den Netz-Value-/Points-Blattwert für `state` (Ego-Perspektive,
/// EIN Batch=1-Forward-Pass) separat vom Suchpfad aus -- NUR für die
/// Debug-Anzeige (Anforderung 1). Liest/schreibt weder `nodes` noch den
/// RNG-Strom der Suche; `state` muss die bereits (falls
/// `DETERMINIZE_ROOT_HIDDEN_INFO`) determinisierte Wurzelposition sein
/// (`nodes[0].state`) -- KEINE zweite Determinisierung hier.
fn compute_root_value_debug(net_policy: &Net, net_value: Option<&Net>, state: &GameState) -> RootValueDebug {
    let net = net_value.unwrap_or(net_policy);
    let feats = crate::features::features_for_net(net, state);
    let (_logits, value, _moon, points) = net
        .eval(&feats)
        .unwrap_or_else(|_| (vec![0.0; NUM_ACTIONS], Vec::new(), Vec::new(), Vec::new()));
    let raw_value = value.first().copied().unwrap_or(0.0);
    let win_prob = value_to_win_prob(&value);
    let blended_raw = blended_leaf_win_prob(&value, &points);
    let blended_utility = if VALUE_SHRINK_ENABLED {
        0.5 + value_shrink_weight(state.round_number) * (blended_raw - 0.5)
    } else {
        blended_raw
    };
    let points_forecast = points.first().copied();
    let floor_raw = FLOOR_SHAPING_WEIGHT * floor_shaping_delta(state).tanh();
    // `floor_shaping_delta` ist absolut Spieler0-minus-Spieler1 -- auf
    // Ego-Perspektive (der an der Wurzel ziehende Spieler) drehen.
    let floor_shift = if state.current_player == 0 { floor_raw } else { -floor_raw };
    let final_value = (blended_utility + floor_shift).clamp(0.0, 1.0);
    RootValueDebug { raw_value, points_forecast, win_prob, blended_utility, floor_shift, final_value }
}

/// Ein Wurzel-Kandidat in der Gumbel-Top-m-Auswahlphase (Anforderung 2b).
#[derive(Clone, Debug)]
pub struct GumbelTraceCandidate {
    pub description: String,
    pub prior: f64,
    pub ln_prior: f64,
    pub gumbel_g: f64,
    pub score: f64,
    pub selected_top_m: bool,
}

impl GumbelTraceCandidate {
    fn to_json(&self) -> Value {
        json!({
            "description": self.description,
            "prior": self.prior,
            "ln_prior": self.ln_prior,
            "gumbel_g": self.gumbel_g,
            "score": self.score,
            "selected_top_m": self.selected_top_m,
        })
    }
}

/// Ein Kandidat innerhalb EINER Sequential-Halving-Phase (Anforderung 2c).
#[derive(Clone, Debug)]
pub struct GumbelPhaseCandidate {
    pub description: String,
    pub visits: u32,
    pub q: f64,
    pub sigma_q: f64,
    pub score: f64,
    pub eliminated: bool,
}

impl GumbelPhaseCandidate {
    fn to_json(&self) -> Value {
        json!({
            "description": self.description,
            "visits": self.visits,
            "q": self.q,
            "sigma_q": self.sigma_q,
            "score": self.score,
            "eliminated": self.eliminated,
        })
    }
}

/// Eine Sequential-Halving-Phase (Anforderung 2c).
#[derive(Clone, Debug)]
pub struct GumbelPhase {
    pub phase: u32,
    pub sims_per_survivor: u32,
    pub candidates: Vec<GumbelPhaseCandidate>,
}

impl GumbelPhase {
    fn to_json(&self) -> Value {
        json!({
            "phase": self.phase,
            "sims_per_survivor": self.sims_per_survivor,
            "candidates": self.candidates.iter().map(|c| c.to_json()).collect::<Vec<_>>(),
        })
    }
}

/// Ein Finalist der letzten Max-Visit-Menge (Anforderung 2d).
#[derive(Clone, Debug)]
pub struct GumbelFinalist {
    pub description: String,
    pub visits: u32,
    pub ln_prior: f64,
    pub sigma_q: f64,
    pub score: f64,
}

impl GumbelFinalist {
    fn to_json(&self) -> Value {
        json!({
            "description": self.description,
            "visits": self.visits,
            "ln_prior": self.ln_prior,
            "sigma_q": self.sigma_q,
            "score": self.score,
        })
    }
}

/// Granularer Gumbel-Such-Trace (Task #95, Anforderung 2) -- ersetzt den
/// bisherigen Platzhalter-Log-Eintrag „GUMBEL-SUCHE (kein granularer
/// Sim-Trace)" durch eine strukturierte Aufzeichnung von Top-m-Auswahl,
/// jeder Sequential-Halving-Phase und der finalen Wurzel-Zugwahl. Nur
/// befüllt, wenn `collect_trace=true` an `build_gumbel_tree`/`build_net_tree`
/// durchgereicht wird (siehe dortige Parameter) -- Self-Play/Arena rufen
/// IMMER mit `None`, byte-identisch zum Vor-Task-#95-Verhalten (Paritätstest
/// siehe Testmodul).
#[derive(Clone, Debug, Default)]
pub struct GumbelTrace {
    pub determinize_active: bool,
    pub root_value: Option<RootValueDebug>,
    pub top_m: Vec<GumbelTraceCandidate>,
    pub phases: Vec<GumbelPhase>,
    pub finalists: Vec<GumbelFinalist>,
}

impl GumbelTrace {
    pub fn to_json(&self) -> Value {
        json!({
            "determinize_active": self.determinize_active,
            "top_m_selection": self.top_m.iter().map(|c| c.to_json()).collect::<Vec<_>>(),
            "phases": self.phases.iter().map(|p| p.to_json()).collect::<Vec<_>>(),
            "final_selection": self.finalists.iter().map(|f| f.to_json()).collect::<Vec<_>>(),
        })
    }
}

/// Gumbel-AlphaZero-Baumaufbau (siehe Modul-Kommentar "Gumbel AlphaZero" für
/// die volle Herleitung) -- Ersatz für `build_net_tree`, wenn
/// `USE_GUMBEL_SEARCH=true`. Wurzel: Gumbel-Top-m + Sequential Halving statt
/// Dirichlet-Noise + PUCT über den vollen Kandidatensatz. Tiefe≥1 (Paket 2
/// des Speed-Bündels, 2026-07-22): `gumbel_select_child` über
/// `children ∪ untried` OHNE Progressive-Widening-Cap -- die mctx-Auswahlregel
/// selbst entscheidet, ob deszendiert oder ein neuer Kandidat expandiert wird
/// (vorher PUCT-Erbe: fester Widening-Cap erzwang Expansion, bevor überhaupt
/// zwischen Kindern gewählt wurde, siehe `descend_and_backprop`).
/// `add_root_noise = false` (Arena/Produktion) schaltet die Gumbel-Samples ab
/// (alle g(a) = 0.0): Top-m und Halving ranken dann rein nach
/// `ln(prior) + σ(Q̂)` -- deterministisch, äquivalent zu mctx
/// `gumbel_scale=0`. Self-Play ruft mit `true` und behält die echte
/// Gumbel-Exploration (G1, Vollaudit 2026-07-21).
///
/// `trace` (Task #95, Anforderung 2/3): NUR wenn `Some`, wird zusätzlich ein
/// granularer Trace (Top-m-Auswahl, jede Halving-Phase, finale Zugwahl)
/// gesammelt -- ausschließlich additive Lesezugriffe auf ohnehin berechnete
/// Werte, KEINE Änderung an Auswahl/Backprop/RNG-Verbrauch (siehe
/// Paritätstest).
/// Buendelt die ERSTMALIGE Expansion ALLER `candidates.len()` Top-m-
/// Kandidaten an der Gumbel-Wurzel in EINEM `Net::eval_batch`-Aufruf (Perf-
/// Auftrag, 2026-08-02, siehe `BATCH_ROOT_EXPANSION`-Doku) statt
/// `candidates.len()` einzelner `make_node`-Netz-Evals. NUR fuer den
/// `same_net`-Fall gedacht (Aufrufer prueft das) -- diese Funktion selbst
/// geht implizit davon aus, dass EIN Netz (`net_policy`) sowohl Policy- als
/// auch Value-Quelle ist (identisch zu `make_node`s `same_net=true`-Zweig).
///
/// Baut je erfolgreich expandiertem Kandidaten einen [`Node`] (ueber
/// `node_from_net_outputs`, DIESELBE Konstruktionslogik wie der unbatchte
/// Pfad -- kein Doppelpflege-Risiko), haengt ihn an `nodes[0].children` und
/// setzt `candidate_node[ci] = Some(cid)` -- ABSICHTLICH OHNE den
/// Erstbesuch-Backprop (`nodes[cid].visits` bleibt `0`, Frisch-Knoten-
/// Default): der Aufrufer (`build_gumbel_tree`s `visit_candidate!`-Makro)
/// erkennt `visits==0` und holt den Backprop beim naechsten reguraeren
/// Besuch nach -- dadurch bleibt die `budget_used`/`extra`-Buchhaltung der
/// Sequential-Halving-Phasenschleife UNVERAENDERT (jeder Kandidat zaehlt
/// weiterhin genau EINEN Sim fuer seinen Erstbesuch, exakt wie im unbatchten
/// Pfad -- nur WANN der Netz-Eval passiert, nicht WIE VIELE Sims er kostet,
/// aendert sich).
///
/// Fehlgeschlagene `apply_drafting`-Versuche werden wie im unbatchten Pfad
/// stillschweigend uebersprungen (`candidate_node[ci]` bleibt `None`).
///
/// RNG/Determinismus: siehe `BATCH_ROOT_EXPANSION`-Doku -- in der
/// Standardkonfiguration (`SHUFFLE_STACK_PEEK_IN_SEARCH=false`,
/// `ROUND_TRANSITION_SAMPLING=false`) verbraucht `node_from_net_outputs`
/// gar kein `rng`, die Aufrufreihenfolge ist daher irrelevant; der
/// `SHUFFLE_STACK_PEEK_IN_SEARCH=true`-Fall wird an der Aufrufstelle
/// zusaetzlich ausgeschlossen (fällt auf den unbatchten Pfad zurück).
fn batched_expand_root_candidates<R: Rng + ?Sized>(
    net_policy: &Net,
    net_value: Option<&Net>,
    root_state: &GameState,
    candidates: &[(Action, f32, f64)],
    nodes: &mut Vec<Node>,
    candidate_node: &mut [Option<usize>],
    rng: &mut R,
) {
    let mover = root_state.current_player;
    let need_other_pass = ACTIVE_LEAF == LeafEval::Net && !MIRROR_OTHER_VAL;

    struct Pending {
        ci: usize,
        action: Action,
        prior: f32,
        child_state: GameState,
        terminal: bool,
    }
    let mut pending: Vec<Pending> = Vec::with_capacity(candidates.len());
    for (ci, (act, prior, _g)) in candidates.iter().enumerate() {
        crate::profiling::note_gamestate_clone();
        let mut g = Game { state: root_state.clone() };
        // Kein `SHUFFLE_STACK_PEEK_IN_SEARCH`-Zweig hier -- die Aufrufstelle
        // schaltet den Batch-Pfad bei aktivem Toggle komplett ab (siehe
        // Funktionskommentar), diese Funktion wird dann nie erreicht.
        if g.apply_drafting(act).is_ok() {
            let mut child_state = g.state;
            child_state.log.clear();
            let terminal = child_state.phase != Phase::Drafting;
            pending.push(Pending { ci, action: act.clone(), prior: *prior, child_state, terminal });
        }
    }
    if pending.is_empty() {
        return;
    }

    let feats: Vec<Vec<f32>> = pending
        .iter()
        .map(|p| {
            crate::profiling::timed(crate::profiling::note_features_ns, || {
                crate::features::features_for_net(net_policy, &p.child_state)
            })
        })
        .collect();
    let feats_refs: Vec<&[f32]> = feats.iter().map(|v| v.as_slice()).collect();
    let n = pending.len();
    let outputs = crate::profiling::timed_net_eval(n, || net_policy.eval_batch(&feats_refs)).unwrap_or_else(|_| {
        (0..n).map(|_| (vec![0.0; NUM_ACTIONS], Vec::new(), Vec::new(), Vec::new())).collect()
    });

    let other_outputs: Vec<Option<(Vec<f32>, Vec<f32>)>> = if need_other_pass {
        let other_feats: Vec<Vec<f32>> = pending
            .iter()
            .map(|p| {
                let mut flipped = p.child_state.clone();
                flipped.current_player = 1 - p.child_state.current_player;
                crate::features::features_for_net(net_policy, &flipped)
            })
            .collect();
        let other_feats_refs: Vec<&[f32]> = other_feats.iter().map(|v| v.as_slice()).collect();
        let other_out = crate::profiling::timed_net_eval(n, || net_policy.eval_batch(&other_feats_refs))
            .unwrap_or_else(|_| (0..n).map(|_| (Vec::new(), Vec::new(), Vec::new(), Vec::new())).collect());
        other_out.into_iter().map(|(_, o_value, _, o_points)| Some((o_value, o_points))).collect()
    } else {
        (0..n).map(|_| None).collect()
    };

    for (idx, p) in pending.into_iter().enumerate() {
        let (logits, value, moon, points) = outputs[idx].clone();
        let other_pass = other_outputs[idx].clone();
        let child = node_from_net_outputs(
            net_policy, net_value, p.child_state, Some(0), Some(root_state), Some(p.action), p.prior, mover,
            p.terminal, logits, value, moon, points, other_pass, rng,
        );
        let cid = nodes.len();
        nodes.push(child);
        nodes[0].children.push(cid);
        candidate_node[p.ci] = Some(cid);
        // BEWUSST kein Backprop hier -- siehe Funktionskommentar
        // (`visits==0` bleibt der Marker fuer "expandiert, aber Erstbesuch
        // noch nicht gezaehlt", nachgeholt vom `visit_candidate!`-Makro).
    }
}

fn build_gumbel_tree<R: Rng + ?Sized>(
    net_policy: &Net,
    net_value: Option<&Net>,
    state: &GameState,
    sims: u32,
    add_root_noise: bool,
    rng: &mut R,
    trace: Option<&mut GumbelTrace>,
) -> Vec<Node> {
    build_gumbel_tree_inner(net_policy, net_value, state, sims, add_root_noise, rng, trace, BATCH_ROOT_EXPANSION)
}

/// Eigentliche Implementierung von [`build_gumbel_tree`], mit
/// `batch_root_expansion` als LAUFZEIT-Parameter statt der globalen
/// `BATCH_ROOT_EXPANSION`-Konstante (Perf-Auftrag, 2026-08-02) -- einziger
/// Zweck: der Paritaetstest
/// `batched_root_expansion_matches_sequential_within_tolerance` kann so
/// BEIDE Pfade (batched/unbatcht) mit IDENTISCHEM Seed direkt gegeneinander
/// vergleichen, ohne die Konstante zur Testlaufzeit umschalten zu muessen
/// (waere bei einem `const` ohnehin nicht moeglich). `build_gumbel_tree`
/// selbst bleibt die STABILE, unveraenderte Aufrufstellen-Signatur -- reicht
/// nur `BATCH_ROOT_EXPANSION`s aktuellen (Default `false`) Wert durch.
fn build_gumbel_tree_inner<R: Rng + ?Sized>(
    net_policy: &Net,
    net_value: Option<&Net>,
    state: &GameState,
    sims: u32,
    add_root_noise: bool,
    rng: &mut R,
    mut trace: Option<&mut GumbelTrace>,
    batch_root_expansion: bool,
) -> Vec<Node> {
    let mut root_state = state.clone();
    root_state.log.clear();
    if DETERMINIZE_ROOT_HIDDEN_INFO {
        determinize_hidden_information(&mut root_state, rng);
    }
    let root_player = root_state.current_player;
    let mut nodes =
        vec![make_node(net_policy, net_value, root_state, None, None, None, 0.0, root_player, rng)];

    if let Some(t) = trace.as_deref_mut() {
        t.determinize_active = DETERMINIZE_ROOT_HIDDEN_INFO;
        t.root_value = Some(compute_root_value_debug(net_policy, net_value, &nodes[0].state));
    }

    // Eine einzelne Tiefe-≥1-Deszension + Backprop, beginnend bei einem
    // bereits existierenden Knoten (typischerweise ein Wurzelkind). Paket 2
    // (2026-07-22): KEIN Progressive-Widening-Cap/Forced-Expansion mehr (PUCT-
    // Erbe, entfernt) -- `gumbel_select_child` wählt bei jedem Schritt über
    // `children ∪ untried`; fällt die Wahl auf einen unbesuchten Kandidaten,
    // wird GENAU DIESER on demand expandiert (statt immer `untried[0]`), sonst
    // wird zum gewählten bestehenden Kind weiter deszendiert. Der PUCT-Legacy-
    // Pfad (`build_net_tree`s eigene Sim-Schleife, `USE_GUMBEL_SEARCH=false`)
    // behält seinen eigenen Widening-Cap unverändert -- diese Funktion wird
    // von dort nie aufgerufen. Kein granularer Sim-Trace (siehe
    // `build_net_tree`-Dispatch-Kommentar).
    fn descend_and_backprop<R: Rng + ?Sized>(
        net_policy: &Net,
        net_value: Option<&Net>,
        nodes: &mut Vec<Node>,
        start_nid: usize,
        rng: &mut R,
    ) {
        let mut nid = start_nid;
        let mut expansion_failed = false;
        loop {
            if nodes[nid].terminal {
                break;
            }
            if nodes[nid].children.is_empty() && nodes[nid].untried.is_empty() {
                break; // defensiv: sollte an einem Nicht-Terminal-Knoten nie vorkommen
            }
            let n_children = nodes[nid].children.len();
            let idx = gumbel_select_child(nodes, nid);
            if idx < n_children {
                nid = nodes[nid].children[idx];
                continue;
            }
            // Auswahl faellt auf einen unbesuchten Kandidaten -- GENAU DIESEN
            // on demand expandieren (kein Zwang mehr auf `untried[0]`).
            let untried_idx = idx - n_children;
            let (act, prior) = nodes[nid].untried.remove(untried_idx);
            let mover = nodes[nid].state.current_player;
            crate::profiling::note_gamestate_clone();
            let mut g = Game { state: nodes[nid].state.clone() };
            if SHUFFLE_STACK_PEEK_IN_SEARCH && act == Action::DrawStackPeek {
                g.state.dome_tile_pool.shuffle(rng);
            }
            if g.apply_drafting(&act).is_ok() {
                let mut child_state = g.state;
                child_state.log.clear();
                let child = make_node(
                    net_policy, net_value, child_state, Some(nid), Some(&nodes[nid].state), Some(act), prior, mover, rng,
                );
                let cid = nodes.len();
                nodes.push(child);
                nodes[nid].children.push(cid);
                nid = cid;
            } else {
                expansion_failed = true;
            }
            break;
        }
        if expansion_failed {
            return;
        }
        let value = nodes[nid].leaf_value;
        let mut cur = Some(nid);
        while let Some(i) = cur {
            nodes[i].visits += 1;
            nodes[i].value += value[nodes[i].player_who_acted];
            cur = nodes[i].parent;
        }
    }

    let n_root = nodes[0].untried.len();
    if n_root == 0 {
        return nodes; // Wurzel terminal/keine legalen Züge -- nichts zu tun.
    }

    // Gumbel-Top-m an der Wurzel (§1 des Plans): je Kandidat einen Gumbel-
    // Wert ziehen, Score = g(a) + ln(prior(a)), Top m' behalten. `g(a)`
    // wird für die spätere Halbierungs-Rangfolge (§2) aufbewahrt (NICHT neu
    // gezogen).
    let m_prime = gumbel_top_m_for_budget(sims).min(n_root);
    let mut scored: Vec<(f64, f64, usize)> = nodes[0]
        .untried
        .iter()
        .enumerate()
        .map(|(i, &(_, p))| {
            // g(a) = 0 im deterministischen Modus (siehe Funktionskommentar).
            let g = if add_root_noise { sample_gumbel(rng) } else { 0.0 };
            (g + (p as f64).max(1e-9).ln(), g, i)
        })
        .collect();
    scored.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap_or(std::cmp::Ordering::Equal));

    // Anforderung 2b: ALLE legalen Wurzelkandidaten (nicht nur die Top-m) mit
    // prior/ln(prior)/Gumbel-g/Score + Top-16-Kennzeichnung -- muss VOR dem
    // Entfernen der gezogenen Einträge aus `nodes[0].untried` passieren
    // (`scored` referenziert deren Indizes).
    if let Some(t) = trace.as_deref_mut() {
        for (rank, &(score, g, idx)) in scored.iter().enumerate() {
            let (act, prior) = &nodes[0].untried[idx];
            let description = label_search_move(&SearchMove::Draft(act.clone()), Some(&nodes[0].state)).1;
            t.top_m.push(GumbelTraceCandidate {
                description,
                prior: *prior as f64,
                ln_prior: (*prior as f64).max(1e-9).ln(),
                gumbel_g: g,
                score,
                selected_top_m: rank < m_prime,
            });
        }
    }

    let mut chosen: Vec<(usize, f64)> = scored.iter().take(m_prime).map(|&(_, g, i)| (i, g)).collect();
    // Absteigend nach urspruenglichem Untried-Index entfernen, damit sich
    // die Indizes der VERBLEIBENDEN (nicht gezogenen) Einträge beim
    // Herausnehmen nicht verschieben.
    chosen.sort_by(|a, b| b.0.cmp(&a.0));
    let candidates: Vec<(Action, f32, f64)> = chosen
        .into_iter()
        .map(|(i, g)| {
            let (act, prior) = nodes[0].untried.remove(i);
            (act, prior, g)
        })
        .collect();
    // `nodes[0].untried` enthält jetzt nur noch die NICHT gezogenen
    // Kandidaten -- bleibt für `improved_policy`/das spätere Policy-Ziel
    // (§5, Phase 4) korrekt als "N(a)=0"-Menge erhalten.

    let mut candidate_node: Vec<Option<usize>> = vec![None; candidates.len()];
    let mut current: Vec<usize> = (0..candidates.len()).collect();

    // Perf-Auftrag (2026-08-02): gebuendelte Erstexpansion ALLER Kandidaten
    // in EINEM Netz-Batch-Aufruf statt `candidates.len()` einzelner Evals,
    // siehe `BATCH_ROOT_EXPANSION`-Doku. NUR wenn (a) der Toggle aktiv ist,
    // (b) mehr als 1 Kandidat da ist (bei genau 1 gibt's nichts zu
    // buendeln, der `candidates.len()<=1`-Zweig unten bleibt unberuehrt),
    // (c) Policy- und Value-Netz IDENTISCH sind (Hybrid-Pfad, Task #88,
    // faellt weiterhin auf den unbatchten Pfad zurueck -- ausserhalb des
    // Scopes dieses Auftrags) und (d) `SHUFFLE_STACK_PEEK_IN_SEARCH` AUS
    // ist (sonst wuerde die geaenderte Kandidaten-Reihenfolge den
    // RNG-Verbrauch verschieben, siehe `BATCH_ROOT_EXPANSION`-Doku).
    let same_net_for_batching = net_value.is_none_or(|v| std::ptr::eq(v, net_policy));
    if batch_root_expansion && candidates.len() > 1 && same_net_for_batching && !SHUFFLE_STACK_PEEK_IN_SEARCH {
        let root_state = nodes[0].state.clone();
        batched_expand_root_candidates(
            net_policy, net_value, &root_state, &candidates, &mut nodes, &mut candidate_node, rng,
        );
    }

    // Expandiert (falls nötig) und simuliert EINEN weiteren Besuch für
    // Kandidat `ci` (Index in `candidates`/`candidate_node`).
    macro_rules! visit_candidate {
        ($ci:expr) => {{
            let ci = $ci;
            match candidate_node[ci] {
                Some(cid) if nodes[cid].visits > 0 => {
                    descend_and_backprop(net_policy, net_value, &mut nodes, cid, rng)
                }
                Some(cid) => {
                    // Perf-Auftrag (2026-08-02): per `batched_expand_root_candidates`
                    // bereits per Batch-Netz-Eval expandiert (Node existiert,
                    // `leaf_value` bereits berechnet), aber NOCH NICHT als
                    // Besuch gezaehlt (`visits==0`, Frisch-Knoten-Default) --
                    // hier NUR den Erstbesuch-Backprop nachholen, KEIN
                    // zweiter Netz-Eval (identische Backprop-Logik wie im
                    // `None`-Zweig unten, ohne die dortige vorangehende
                    // Netz-/Expansionsarbeit, die schon erledigt ist).
                    let value = nodes[cid].leaf_value;
                    let mut cur = Some(cid);
                    while let Some(i) = cur {
                        nodes[i].visits += 1;
                        nodes[i].value += value[nodes[i].player_who_acted];
                        cur = nodes[i].parent;
                    }
                }
                None => {
                    let (act, prior, _g) = candidates[ci].clone();
                    let mover = nodes[0].state.current_player;
                    crate::profiling::note_gamestate_clone();
                    let mut g = Game { state: nodes[0].state.clone() };
                    if SHUFFLE_STACK_PEEK_IN_SEARCH && act == Action::DrawStackPeek {
                        g.state.dome_tile_pool.shuffle(rng);
                    }
                    if g.apply_drafting(&act).is_ok() {
                        let mut child_state = g.state;
                        child_state.log.clear();
                        let child = make_node(
                            net_policy, net_value, child_state, Some(0), Some(&nodes[0].state), Some(act), prior, mover, rng,
                        );
                        let cid = nodes.len();
                        nodes.push(child);
                        nodes[0].children.push(cid);
                        candidate_node[ci] = Some(cid);
                        let value = nodes[cid].leaf_value;
                        let mut cur = Some(cid);
                        while let Some(i) = cur {
                            nodes[i].visits += 1;
                            nodes[i].value += value[nodes[i].player_who_acted];
                            cur = nodes[i].parent;
                        }
                    }
                    // Fehlgeschlagenes apply_drafting: `candidate_node[ci]`
                    // bleibt `None` -- der Kandidat faellt bei der naechsten
                    // Rangfolge automatisch raus (Q=0-Fallback unten trifft
                    // nie einen ECHTEN Kandidaten, da jeder in `current`
                    // vor der ersten Rangfolge mind. 1 Sim bekommen hat --
                    // ausser bei wiederholtem Fehlschlag, dann bleibt er
                    // einfach auf Q=0 stehen, kein Panik/Sonderfall noetig).
                }
            }
        }};
    }

    if candidates.len() <= 1 {
        for _ in 0..sims {
            visit_candidate!(0);
        }
    } else {
        let m_actual = candidates.len();
        let num_phases = (m_actual as f64).log2().ceil().max(1.0) as u32;
        // G2 (Vollaudit 2026-07-21): das Restbudget wird wie in mctx durch
        // die VERBLEIBENDE Phasenzahl geteilt (Laufvariable, pro Halbierung
        // dekrementiert) -- die frühere Division durch die feste Anfangs-
        // Phasenzahl unterbudgetierte die frühen Phasen und kippte den Rest
        // per Tail-Loop nur auf die Finalisten.
        let mut remaining_phases = num_phases;
        let mut budget_used: u32 = 0;
        let mut phase_num: u32 = 0;
        while current.len() > 1 && budget_used < sims {
            phase_num += 1;
            let remaining_slots = (remaining_phases as usize) * current.len();
            // Invariante "jeder in current bekommt mind. 1 Sim je Phase"
            // (extra >= 1) gilt nur für sims >= m -- bei kleinerem Budget
            // bricht `budget_used >= sims` die Phase vorzeitig ab und
            // unbesuchte Kandidaten bleiben auf dem Q=0-Fallback.
            let extra = (((sims - budget_used) as usize / remaining_slots.max(1)).max(1)) as u32;
            for &ci in &current.clone() {
                for _ in 0..extra {
                    if budget_used >= sims {
                        break;
                    }
                    visit_candidate!(ci);
                    budget_used += 1;
                }
            }
            // Rangfolge: g(a) + ln(prior(a)) + σ(Q̂(a)) -- Q̂ ist der
            // empirische Mittelwert des zugehörigen Wurzelkindes (inzwischen
            // mind. 1x besucht, siehe `extra = max(1, ...)` oben).
            let max_n = current
                .iter()
                .filter_map(|&ci| candidate_node[ci].map(|cid| nodes[cid].visits))
                .max()
                .unwrap_or(0);
            current.sort_by(|&a, &b| {
                let score = |ci: usize| -> f64 {
                    let (_, prior, g) = candidates[ci];
                    let q = match candidate_node[ci] {
                        Some(cid) if nodes[cid].visits > 0 => nodes[cid].value / nodes[cid].visits as f64,
                        _ => 0.0,
                    };
                    g + (prior as f64).max(1e-9).ln() + gumbel_sigma(q, max_n)
                };
                score(b).partial_cmp(&score(a)).unwrap_or(std::cmp::Ordering::Equal)
            });
            let keep = (current.len() / 2).max(2);

            // Anforderung 2c: Trace-Eintrag für DIESE Phase -- `current` ist
            // hier bereits absteigend nach Score sortiert (siehe `sort_by`
            // oben), `rank >= keep` markiert exakt die Kandidaten, die
            // gleich per `truncate` eliminiert werden. Reine Lesezugriffe auf
            // bereits vorhandene Werte, kein Effekt auf `current` selbst.
            if let Some(t) = trace.as_deref_mut() {
                let mut phase_candidates = Vec::with_capacity(current.len());
                for (rank, &ci) in current.iter().enumerate() {
                    let (act, prior, g) = &candidates[ci];
                    let (visits, q) = match candidate_node[ci] {
                        Some(cid) if nodes[cid].visits > 0 => {
                            (nodes[cid].visits, nodes[cid].value / nodes[cid].visits as f64)
                        }
                        Some(cid) => (nodes[cid].visits, 0.0),
                        None => (0, 0.0),
                    };
                    let sigma_q = gumbel_sigma(q, max_n);
                    let score = g + (*prior as f64).max(1e-9).ln() + sigma_q;
                    let description =
                        label_search_move(&SearchMove::Draft(act.clone()), Some(&nodes[0].state)).1;
                    phase_candidates.push(GumbelPhaseCandidate {
                        description,
                        visits,
                        q,
                        sigma_q,
                        score,
                        eliminated: rank >= keep,
                    });
                }
                t.phases.push(GumbelPhase { phase: phase_num, sims_per_survivor: extra, candidates: phase_candidates });
            }

            current.truncate(keep);
            remaining_phases = remaining_phases.saturating_sub(1).max(1);
        }
        // Restbudget (Rundungsreste) auf die verbliebenen Kandidaten verteilen.
        while budget_used < sims {
            for &ci in &current.clone() {
                if budget_used >= sims {
                    break;
                }
                visit_candidate!(ci);
                budget_used += 1;
            }
        }
    }

    // Anforderung 2d: finale Zugwahl -- die Max-Visit-Menge (Sequential-
    // Halving-Überlebende) mit `ln(prior)+σ(Q)` je Finalist, exakt dieselbe
    // Menge/Formel wie `gumbel_final_root_action` (dort erneut, aber
    // unabhängig berechnet -- reiner Lesezugriff auf die fertigen `nodes`,
    // kein Effekt auf das Ergebnis).
    if let Some(t) = trace.as_deref_mut() {
        let children = &nodes[0].children;
        if !children.is_empty() {
            let max_n = children.iter().map(|&c| nodes[c].visits).max().unwrap_or(0);
            for &cid in children {
                if nodes[cid].visits != max_n {
                    continue;
                }
                let description = log_label(&nodes, cid);
                let ln_prior = (nodes[cid].prior as f64).max(1e-9).ln();
                let q = if nodes[cid].visits > 0 { nodes[cid].value / nodes[cid].visits as f64 } else { 0.0 };
                let sigma_q = gumbel_sigma(q, max_n);
                t.finalists.push(GumbelFinalist {
                    description,
                    visits: nodes[cid].visits,
                    ln_prior,
                    sigma_q,
                    score: ln_prior + sigma_q,
                });
            }
        }
    }

    nodes
}

/// Kurzlabel eines Knotens fürs Log (Aktionsbeschreibung bzw. „Wurzel"). Mit
/// Eltern-Zustand (VOR dem Zug) für Steinanzahl/Füllstand/Strafleisten-Hinweis.
fn log_label(nodes: &[Node], nid: usize) -> String {
    match &nodes[nid].action {
        None => "Wurzel".to_string(),
        Some(a) => {
            let parent_state = nodes[nid].parent.map(|p| &nodes[p].state);
            label_search_move(&SearchMove::Draft(a.clone()), parent_state).1
        }
    }
}

/// Baut den PUCT-Suchbaum. `add_root_noise` aktiviert Dirichlet-Wurzel-Noise.
/// Mit `log = Some(..)` wird jede Simulation (Selection/Expansion/Eval/Backprop)
/// als Text protokolliert (für den Server-Debug-Log, analog `mcts::build_tree`).
/// Dispatcht komplett auf `build_gumbel_tree`, wenn `USE_GUMBEL_SEARCH` --
/// `log` wird in diesem Fall ignoriert (der textuelle Platzhalter-Eintrag
/// bleibt für Rückwärtskompatibilität, siehe `net_search_log_header`-
/// Konsumenten). `trace` (Task #95, Anforderung 2/3): NUR wenn `Some`, wird
/// zusätzlich der granulare Gumbel-Trace gesammelt (`build_gumbel_tree`) --
/// bei `USE_GUMBEL_SEARCH=false` (PUCT-Legacy-Pfad) bleibt `trace` ungenutzt,
/// PUCT hat keinen strukturierten Trace (nur den bestehenden Text-`log`).
/// ALLE Produktions-Aufrufstellen (Self-Play/Arena) übergeben `None` --
/// byte-identisch zum Vor-Task-#95-Verhalten.
fn build_net_tree<R: Rng + ?Sized>(
    net_policy: &Net,
    net_value: Option<&Net>,
    state: &GameState,
    sims: u32,
    c_puct: f64,
    add_root_noise: bool,
    rng: &mut R,
    mut log: Option<&mut Vec<String>>,
    trace: Option<&mut GumbelTrace>,
) -> Vec<Node> {
    if USE_GUMBEL_SEARCH {
        if let Some(l) = log.as_deref_mut() {
            l.push("  GUMBEL-SUCHE (kein granularer Text-Sim-Trace -- strukturierter Trace siehe `gumbel_trace`-Feld, falls angefordert)".to_string());
        }
        return build_gumbel_tree(net_policy, net_value, state, sims, add_root_noise, rng, trace);
    }
    let names = [state.players[0].name.as_str(), state.players[1].name.as_str()];
    let mut root_state = state.clone();
    root_state.log.clear();
    if DETERMINIZE_ROOT_HIDDEN_INFO {
        determinize_hidden_information(&mut root_state, rng);
    }
    let root_player = root_state.current_player;
    let mut nodes =
        vec![make_node(net_policy, net_value, root_state, None, None, None, 0.0, root_player, rng)];

    macro_rules! logln {
        ($($arg:tt)*) => { if let Some(l) = log.as_deref_mut() { l.push(format!($($arg)*)); } };
    }

    // Dirichlet-Noise auf die Wurzel-Priors mischen (Self-Play-Exploration).
    if add_root_noise && !nodes[0].untried.is_empty() {
        let noise = dirichlet(nodes[0].untried.len(), DIRICHLET_ALPHA, rng);
        for (i, entry) in nodes[0].untried.iter_mut().enumerate() {
            entry.1 = ((1.0 - DIRICHLET_EPS) * (entry.1 as f64) + DIRICHLET_EPS * noise[i]) as f32;
        }
        nodes[0]
            .untried
            .sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
        logln!("  ROOT-NOISE gemischt (Dirichlet alpha={DIRICHLET_ALPHA}, eps={DIRICHLET_EPS})");
    }

    for sim in 0..sims {
        logln!("=== Sim {}/{} ===", sim + 1, sims);

        // Selection + (eine) Expansion.
        let mut nid = 0;
        // Fund 5 (externer Hinweis, 2026-07-20): ein fehlgeschlagenes
        // `apply_drafting` verwarf den Kandidaten still und liess `nid` auf
        // dem PARENT stehen -- die anschliessende Eval/Backprop-Sektion
        // backprop'te dann fälschlich noch einmal den Parent-eigenen,
        // bereits bekannten Blattwert (verzerrte Besuchszahlen ohne echten
        // Informationsgewinn). Fix: diese Sim sauber überspringen (kein
        // Eval/Backprop), statt den Parent nochmal zu zählen.
        let mut expansion_failed = false;
        loop {
            if nodes[nid].terminal {
                logln!("  SELECT #{nid} [{}] terminal", log_label(&nodes, nid));
                break;
            }
            // Progressive Widening ÜBER dem POLICY_MASS_CUTOFF-Präfix (externer
            // Bugfix-Hinweis, 2026-07-20): `untried` ist bereits beim Erzeugen des
            // Knotens auf den Cutoff-Präfix gekappt (siehe `build_untried_actions`,
            // schließt den Long Tail dauerhaft aus -- das bleibt), ABER ohne
            // zusätzliche Bremse hier würde ein Knoten mit dutzenden Kandidaten
            // (Runde 1, ~49% Top-1-Masse) seinen KOMPLETTEN Präfix erst voll
            // ausrollen (ein Kind pro Sim), bevor PUCT überhaupt einmal zwischen
            // ihnen differenzieren kann -- bei 150 Sims faktisch Breitensuche mit
            // Tiefe ~1-2 statt echter Suche. Derselbe `MAX_ACTIONS + WIDEN_FACTOR·
            // √N`-Wachstumscap wie `crate::mcts` (Heuristik-Suche) angewendet,
            // NUR auf den bereits gekappten Präfix -- der Long Tail bleibt
            // dauerhaft ausgeschlossen, aber selbst die guten Kandidaten kommen
            // erst nach und nach ins Spiel, sodass PUCT früh differenzieren kann.
            let widen_allowed = crate::mcts::MAX_ACTIONS
                + (crate::mcts::WIDEN_FACTOR * (nodes[nid].visits as f64).sqrt()) as usize;
            if !nodes[nid].untried.is_empty() && nodes[nid].children.len() < widen_allowed {
                let (act, prior) = nodes[nid].untried.remove(0); // höchster Prior zuerst
                let mover = nodes[nid].state.current_player;
                crate::profiling::note_gamestate_clone();
                let mut g = Game { state: nodes[nid].state.clone() };
                // Verdeckte-Information-Fix (externer Hinweis, Fund 6,
                // 2026-07-20): `execute_draw_stack_peek` (aufgerufen via
                // `apply_drafting` bei `DrawStackPeek`) liest sonst
                // `dome_tile_pool.remove(0)` -- die ECHTE, im realen Spiel
                // eigentlich verdeckte oberste Platte. Dieselbe
                // Determinisierung wie `round_transition_deep::
                // simulate_one_round` (mischt den Restpool einmalig beim
                // Runden-Eintritt): hier einmalig VOR jedem simulierten Peek,
                // da genau in diesem Moment eine neue verdeckte Information
                // aufgedeckt würde. `dome_tile_pool` enthält an dieser Stelle
                // ohnehin nur noch die ungezogenen (= wirklich verdeckten)
                // Platten -- volles Mischen ist daher exakt richtig, keine
                // Sonderbehandlung für bereits aufgedeckte Platten nötig.
                if SHUFFLE_STACK_PEEK_IN_SEARCH && act == Action::DrawStackPeek {
                    g.state.dome_tile_pool.shuffle(rng);
                }
                if g.apply_drafting(&act).is_ok() {
                    let mut child_state = g.state;
                    child_state.log.clear();
                    let terminal = child_state.phase != Phase::Drafting;
                    let child = make_node(
                        net_policy,
                        net_value,
                        child_state,
                        Some(nid),
                        Some(&nodes[nid].state),
                        Some(act.clone()),
                        prior,
                        mover,
                        rng,
                    );
                    let cid = nodes.len();
                    nodes.push(child);
                    nodes[nid].children.push(cid);
                    logln!(
                        "  EXPAND #{nid} +[{}] → #{cid} (Zug: {}, prior={:.1}%{})",
                        label_search_move(&SearchMove::Draft(act), Some(&nodes[nid].state)).1,
                        names[mover],
                        prior * 100.0,
                        if terminal { ", terminal" } else { "" }
                    );
                    nid = cid;
                } else {
                    expansion_failed = true;
                }
                break;
            }
            if nodes[nid].children.is_empty() {
                break;
            }
            let cid = best_puct(&nodes, nid, c_puct);
            if log.is_some() {
                let sqrt_pv = (nodes[nid].visits.max(1) as f64).sqrt();
                let psum: f64 = nodes[nid]
                    .children
                    .iter()
                    .map(|&c| nodes[c].prior as f64)
                    .sum::<f64>()
                    .max(1e-8);
                let n = nodes[cid].visits as f64;
                let q = if n > 0.0 { nodes[cid].value / n } else { 0.0 };
                let p = nodes[cid].prior as f64 / psum;
                let u = c_puct * p * sqrt_pv / (1.0 + n);
                logln!(
                    "  SELECT #{nid} → #{cid} [{}] (Zug: {}) N={} P={:.3} Q={:.3} U={:.3} → {:.3}",
                    log_label(&nodes, cid), names[nodes[cid].player_who_acted],
                    nodes[cid].visits, p, q, u, q + u
                );
            }
            nid = cid;
        }

        if expansion_failed {
            logln!("  SKIP   Sim {} (apply_drafting fehlgeschlagen, kein Backprop)", sim + 1);
            continue;
        }

        // Eval: Blattwert wurde schon bei Knoten-Erzeugung berechnet (make_node).
        let value = nodes[nid].leaf_value;
        logln!(
            "  EVAL   #{nid} ({}) win[{}]={:.3} win[{}]={:.3}",
            if ACTIVE_LEAF == LeafEval::Net { "Netz-Value" } else { "DFS-Solver" },
            names[0], value[0], names[1], value[1]
        );

        // Backprop (Netz-Blattwert, player_who_acted-Sicht).
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

    nodes
}

/// Beste Drafting-Aktion per Netz-PUCT (meistbesuchtes Wurzelkind). None außerhalb
/// der Drafting-Phase. `add_root_noise` nur im Self-Play aktivieren.
pub fn net_search_drafting_action<R: Rng + ?Sized>(
    net: &Net,
    state: &GameState,
    sims: u32,
    c_puct: f64,
    add_root_noise: bool,
    rng: &mut R,
) -> Option<Action> {
    if state.phase != Phase::Drafting {
        return None;
    }
    // Runde 5: informationsfreies Endspiel, siehe round5.rs -- exakte
    // Alpha-Beta-Wahl statt Netz-PUCT (kein Netz noetig, kein
    // Naeherungsfehler in der Wertungsplatten-Endwertung).
    if crate::round5::applies(state) {
        return crate::round5::choose_action(state);
    }
    if NUM_DETERMINIZATIONS <= 1 {
        let nodes = build_net_tree(net, None, state, sims, c_puct, add_root_noise, rng, None, None);
        let best = select_final_root_child(&nodes)?;
        return nodes[best].action.clone();
    }
    // ISMCTS-Mehrfach-Determinisierung (Task #65): finale Zugwahl = argmax
    // der über die Welten GEMITTELTEN completed-Q-Politik (siehe
    // `average_completed_q_policy`-Kommentar), nicht mehr
    // `select_final_root_child` auf einem Einzelbaum -- letzteres hätte
    // keinen sinnvollen "einen" Baum mehr, über den es entscheiden könnte.
    let forest =
        build_determinized_forest(net, None, state, sims, c_puct, add_root_noise, NUM_DETERMINIZATIONS, rng);
    average_completed_q_policy(&forest)
        .into_iter()
        .max_by(|a, b| a.1.partial_cmp(&b.1).unwrap_or(std::cmp::Ordering::Equal))
        .map(|(a, _)| a)
}

/// Task #88 (Hybrid-Suche, kausaler Kopf-Test): wie [`net_search_drafting_action`],
/// aber Priors/Moon-Order kommen von `net_policy`, Blattwert (Value+Points)
/// von `net_value` -- zwei UNTERSCHIEDLICHE Netze, um zu isolieren, ob die
/// Arena-Stärke eines Kandidaten aus dem Policy- oder dem Value-Kopf kommt
/// (siehe `make_node`-Kommentar für die Verdrahtung). `net_policy`/`net_value`
/// DÜRFEN dieselbe Referenz sein -- dann ist das Ergebnis BYTE-IDENTISCH zu
/// `net_search_drafting_action(net_policy, ...)` (Paritätstest siehe
/// Testmodul: `hybrid_search_with_equal_nets_matches_plain_search`). Nur für
/// die diagnostische Arena gedacht (`self_play::run_net_vs_net_arena_hybrid`),
/// KEIN Self-Play-/Trainingspfad.
pub fn net_search_drafting_action_hybrid<R: Rng + ?Sized>(
    net_policy: &Net,
    net_value: &Net,
    state: &GameState,
    sims: u32,
    c_puct: f64,
    add_root_noise: bool,
    rng: &mut R,
) -> Option<Action> {
    if state.phase != Phase::Drafting {
        return None;
    }
    if crate::round5::applies(state) {
        return crate::round5::choose_action(state);
    }
    if NUM_DETERMINIZATIONS <= 1 {
        let nodes = build_net_tree(net_policy, Some(net_value), state, sims, c_puct, add_root_noise, rng, None, None);
        let best = select_final_root_child(&nodes)?;
        return nodes[best].action.clone();
    }
    let forest = build_determinized_forest(
        net_policy,
        Some(net_value),
        state,
        sims,
        c_puct,
        add_root_noise,
        NUM_DETERMINIZATIONS,
        rng,
    );
    average_completed_q_policy(&forest)
        .into_iter()
        .max_by(|a, b| a.1.partial_cmp(&b.1).unwrap_or(std::cmp::Ordering::Equal))
        .map(|(a, _)| a)
}

/// Wurzelkind-Statistik `(Action, Besuche, Q)` — für Self-Play-Policy-Targets.
pub fn net_root_child_stats<R: Rng + ?Sized>(
    net: &Net,
    state: &GameState,
    sims: u32,
    c_puct: f64,
    add_root_noise: bool,
    rng: &mut R,
) -> Vec<(Action, u32, f64)> {
    if state.phase != Phase::Drafting {
        return Vec::new();
    }
    // Runde 5: siehe net_search_drafting_action. Einzelner Eintrag mit
    // Gewicht 1.0 (statt leer) macht `net_drafting_policy`s Zufalls-
    // Fallback (bei leerer Stats-Liste) nicht faelschlich fuer die
    // Aktionswahl zustaendig.
    if crate::round5::applies(state) {
        return crate::round5::choose_action(state)
            .into_iter()
            .map(|a| (a, 1, 1.0))
            .collect();
    }
    // Bewusst NICHT auf NUM_DETERMINIZATIONS umgestellt -- diese Funktion
    // dient nur der günstigen Stufe-3-Rollout-Kandidaten-Vorauswahl
    // (`self_play::alphabeta_choose_action`s Shortlisting), nicht einer der
    // drei in Task #65 benannten Haupt-Sucheinstiege (Arena/Self-Play-Ziel/
    // Debug-UI) -- bleibt unverändert Einzelwelt.
    let nodes = build_net_tree(net, None, state, sims, c_puct, add_root_noise, rng, None, None);
    root_child_stats_from_nodes(&nodes)
}

/// Wie [`net_root_child_stats`], liefert ZUSÄTZLICH Gumbels completed-Q-
/// Policy-Ziel (`improved_policy` an der Wurzel, §4 des Gumbel-Plans) für
/// die Self-Play-Aufzeichnung — EIN Baum-Aufbau statt zwei getrennte
/// (`build_net_tree` ist die teure Suche, hier nicht doppelt bezahlt).
/// Rückgabe: (rohe Stats für Zugwahl/Shortlisting, unverändert), (Aktion,
/// completed-Q-Wahrscheinlichkeit) je Kandidat für den Trainings-Policy-
/// Vektor — deckt `children ∪ untried` ab, d.h. ALLE Wurzelaktionen, nicht
/// nur die tatsächlich durchsuchten (unbesuchte bekommen `v_mix` statt
/// Null-Besuch, siehe `completed_q_per_candidate`). Die tatsächlich
/// GESPIELTE Aktion bleibt weiterhin besuchsbasiert (Sequential-Halving-
/// Ergebnis) — nur das aufgezeichnete Trainingsziel ändert sich, siehe
/// `self_play::net_drafting_policy`.
///
/// DRITTES Rückgabeelement (v19-Vorbereitung, Root-Q-Logging für das
/// geplante Misch-Value-Target-Experiment λ·z+(1−λ)·q_root, Recherche Fund 1):
/// der Wurzel-Q-Wert der Suche selbst, aus Sicht des ziehenden Spielers
/// (`state.current_player`), auf DERSELBEN [0,1]-Gewinnwahrscheinlichkeits-
/// Skala wie `mcts_q`/`win_pct` überall sonst (`value_to_win_prob`,
/// `crate::mcts::normalize_score`) -- also NICHT die [-1,1]-tanh-Skala des
/// späteren `z`-Labels; Python remapt beim Cache-Bau ohnehin `*2-1` (siehe
/// `round_transition_value`-Konvention, `neural_net.py::MosaicDataset`),
/// `root_q` folgt exakt demselben Muster. `None` nur, wenn keine Bewertung
/// zustande kam (kein Kandidat/leere Suche).
pub fn net_root_child_stats_and_policy<R: Rng + ?Sized>(
    net: &Net,
    state: &GameState,
    sims: u32,
    c_puct: f64,
    add_root_noise: bool,
    rng: &mut R,
) -> (Vec<(Action, u32, f64)>, Vec<(Action, f64)>, Option<f64>) {
    if state.phase != Phase::Drafting {
        return (Vec::new(), Vec::new(), None);
    }
    if crate::round5::applies(state) {
        let stats: Vec<(Action, u32, f64)> =
            crate::round5::choose_action(state).into_iter().map(|a| (a, 1, 1.0)).collect();
        let n = stats.len().max(1);
        let policy: Vec<(Action, f64)> = stats.iter().map(|(a, _, _)| (a.clone(), 1.0 / n as f64)).collect();
        // Runde 5 hat KEINEN MCTS-Baum (Alpha-Beta statt Netz-Suche, siehe
        // oben) -- der exakte Minimax-Wurzelwert kommt separat aus
        // `round5::choose_action_with_analysis`, die BEREITS (round5.rs,
        // nicht hier neu erfunden) exakt dieselbe tanh-Margin-Normierung auf
        // die [0,1]-Gewinnwahrscheinlichkeits-Skala anwendet wie das MCTS-
        // `root_q` unten (`((val/VALUE_SCALE).tanh()+1.0)/2.0`, siehe dortiger
        // Kommentar zu `mcts_q`). BEWUSST NICHT `choose_action`s eigene Suche
        // wiederverwendet: `choose_action` bricht bei Budget-/Zeit-
        // Überschreitung früh ab und lässt spätere Kandidaten UNBEWERTET,
        // während `choose_action_with_analysis` stattdessen auf einen
        // billigen `leaf_value`-Ersatzwert zurückfällt -- ein gemeinsamer Aufruf
        // könnte dadurch eine ANDERE Aktion als Sieger markieren. Die
        // tatsächlich GESPIELTE Aktion bleibt ausschließlich `choose_action`s
        // Ergebnis (oben, unverändert); die Zusatzanalyse dient NUR der
        // Root-Q-Metadatenerzeugung. Kosten: ein zusätzlicher, aber sehr
        // billiger Alpha-Beta-Lauf (NODE_BUDGET=200, keine Netz-Evals) --
        // anders als beim MCTS-Pfad unten NICHT wortwörtlich kostenlos, aber
        // neben der dominanten Netz-Suchkoste vernachlässigbar.
        let root_q = crate::round5::choose_action_with_analysis(state)
            .1
            .get("moves")
            .and_then(|m| m.as_array())
            .and_then(|moves| {
                moves.iter().find(|mv| mv.get("chosen").and_then(Value::as_bool) == Some(true))
            })
            .and_then(|mv| mv.get("mcts_q"))
            .and_then(Value::as_f64);
        return (stats, policy, root_q);
    }
    if NUM_DETERMINIZATIONS <= 1 {
        let nodes = build_net_tree(net, None, state, sims, c_puct, add_root_noise, rng, None, None);
        let root_visits = nodes[0].visits.max(1) as f64;
        let root_q = Some(nodes[0].value / root_visits);
        return (root_child_stats_from_nodes(&nodes), root_completed_q_policy(&nodes), root_q);
    }
    // ISMCTS-Mehrfach-Determinisierung: Stats über die Welten-SUMME der
    // Besuche (treibt Self-Plays besuchsbasierte Sampling-Auswahl
    // unverändert weiter, jetzt über den Wald statt einer Welt), Policy-
    // Ziel = über die Welten gemittelte completed-Q-Politik. `root_q`
    // folgt demselben Summen-Muster wie `aggregate_root_child_stats`
    // (Σvalue/Σvisits über die Welten, NICHT das arithmetische Mittel der
    // Pro-Welt-Quotienten).
    let forest =
        build_determinized_forest(net, None, state, sims, c_puct, add_root_noise, NUM_DETERMINIZATIONS, rng);
    let (visits_sum, value_sum) = forest.iter().fold((0.0f64, 0.0f64), |(vs, vals), nodes| {
        (vs + nodes[0].visits as f64, vals + nodes[0].value)
    });
    let root_q = if visits_sum > 0.0 { Some(value_sum / visits_sum) } else { None };
    (aggregate_root_child_stats(&forest), average_completed_q_policy(&forest), root_q)
}

/// Zippt `improved_policy(nodes, 0)` (reine Zahlen, Reihenfolge
/// `children ∪ untried`, siehe `completed_q_per_candidate`) mit den
/// zugehörigen Aktionen der Wurzel — extrahiert aus
/// [`net_root_child_stats_and_policy`] für einen Unit-Test ohne echtes
/// Netz/Suche (siehe Testmodul, hand-gebauter `Node`-Vektor).
fn root_completed_q_policy(nodes: &[Node]) -> Vec<(Action, f64)> {
    let improved = improved_policy(nodes, 0);
    let mut policy: Vec<(Action, f64)> = Vec::with_capacity(improved.len());
    for (i, &cid) in nodes[0].children.iter().enumerate() {
        if let Some(a) = nodes[cid].action.clone() {
            policy.push((a, improved[i]));
        }
    }
    let n_children = nodes[0].children.len();
    for (i, (act, _prior)) in nodes[0].untried.iter().enumerate() {
        policy.push((act.clone(), improved[n_children + i]));
    }
    policy
}

/// Wie [`net_search_drafting_action`], liefert zusätzlich ein debug.html-kompatibles
/// Analyse-Dict je Wurzelkind: rohen Netz-Prior (`net_prob`/`net_prob_norm`, VOR jeder
/// Suche — das eigentliche Policy-Head-Signal) zusammen mit den PUCT-Such-Stats
/// (`mcts_visits`/`mcts_share`/`mcts_q`). Für den Server (Mensch-vs-Netz) und Debug-UI;
/// `add_root_noise` hier i.d.R. `false` (Dirichlet-Noise ist nur ein Self-Play-Kniff).
/// Mit `log = Some(..)` wird zusätzlich ein Sim-für-Sim-Trace protokolliert
/// (für den Server-Debug-Log-Button, analog zur Heuristik). `collect_trace`
/// (Task #95, Anforderung 1-3): NUR wenn `true`, werden zusätzlich der
/// ROOT-Value-Breakdown (`value_debug`-Feld) und der granulare Gumbel-Trace
/// (`gumbel_trace`-Feld) im Analyse-Dict befüllt -- kostet EINEN zusätzlichen
/// Netz-Forward-Pass (`compute_root_value_debug`) plus ein paar zusätzliche
/// `Vec`-Pushes während des Baumaufbaus, sonst KEINE Änderung an Auswahl/
/// Backprop/RNG-Verbrauch (Paritätstest siehe Testmodul). Alle
/// Produktions-Aufrufstellen (`ai_step_net_json`/`ai_drafting_net_step`)
/// übergeben `false` -- nur `ai_debug_net_json` (reiner Analyse-Endpunkt,
/// kein Zug wird angewendet) übergibt `true`.
pub fn net_search_with_tree<R: Rng + ?Sized>(
    net: &Net,
    state: &GameState,
    sims: u32,
    c_puct: f64,
    add_root_noise: bool,
    rng: &mut R,
    mut log: Option<&mut Vec<String>>,
    collect_trace: bool,
) -> (Option<Action>, Value) {
    if state.phase != Phase::Drafting {
        return (None, Value::Null);
    }
    if crate::round5::applies(state) {
        return crate::round5::choose_action_with_analysis(state);
    }
    if NUM_DETERMINIZATIONS <= 1 {
        let mut trace = if collect_trace { Some(GumbelTrace::default()) } else { None };
        let nodes = build_net_tree(net, None, state, sims, c_puct, add_root_noise, rng, log, trace.as_mut());
        return net_search_with_tree_from_nodes(state, sims, &nodes, trace.as_ref());
    }
    // ISMCTS-Mehrfach-Determinisierung: kein granularer Sim-für-Sim-Trace je
    // Welt (würde N verschachtelte "=== Sim x/y ==="-Folgen ergeben, kaum
    // lesbar) -- ein einzelner Hinweis genügt, gleiches Muster wie
    // `build_net_tree`s Gumbel-Dispatch-Log. Strukturierter Gumbel-Trace
    // (`collect_trace`) ist im Mehrwelten-Pfad NICHT unterstützt (aktuell
    // ohnehin nie aktiv, `NUM_DETERMINIZATIONS=1`, siehe dortige Konstante).
    if let Some(l) = log.as_deref_mut() {
        l.push(format!(
            "  ISMCTS: {NUM_DETERMINIZATIONS} Determinisierungen (kein granularer Sim-Trace je Welt)"
        ));
    }
    let forest =
        build_determinized_forest(net, None, state, sims, c_puct, add_root_noise, NUM_DETERMINIZATIONS, rng);
    net_search_with_tree_from_forest(state, sims, &forest)
}

/// `net_search_with_tree`s Debug-Analyse-Dict aus einem EINZELNEN Baum
/// (`NUM_DETERMINIZATIONS <= 1`-Pfad, unverändert gegenüber vor Task #65).
/// `trace` (Task #95): nur `Some`, wenn `collect_trace=true` angefordert --
/// befüllt zusätzlich `value_debug`/`gumbel_trace`/`value`/`win_pct`.
fn net_search_with_tree_from_nodes(
    state: &GameState,
    sims: u32,
    nodes: &[Node],
    trace: Option<&GumbelTrace>,
) -> (Option<Action>, Value) {
    let best = select_final_root_child(nodes);
    let total_visits: u32 = nodes[0].children.iter().map(|&c| nodes[c].visits).sum();
    let prior_sum: f64 = nodes[0]
        .children
        .iter()
        .map(|&c| nodes[c].prior as f64)
        .sum::<f64>()
        .max(1e-8);

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
                Some(a) => label_search_move(&SearchMove::Draft(a.clone()), Some(state)),
                None => ("?", "?".to_string(), "pass", Value::Null),
            };
            // Task #89: `action_to_env_dict`-Schema (self_play.rs) -- NICHT
            // dasselbe wie `label_search_move`s `serialize::action_to_dict`
            // (unterschiedliche Feldnamen, z.B. `display_index` vs. `tile_id`)!
            // Nur `action_to_env_dict` passt zu `neural_net.py::action_to_id`
            // und damit zur festen NUM_ACTIONS-Indizierung eines Kandidaten-
            // Netzes (Oracle-Metriken, tools/oracle_metrics.py). Rein additiv,
            // bisherige Konsumenten (Debug-UI) ignorieren das neue Feld.
            let env_action = node.action.as_ref().map(|a| action_to_env_dict(state, a));
            let is_chosen = best == Some(cid);
            if is_chosen {
                chosen_id = Some(i);
            }
            // Task #97 (Lehrer-Modus-Feedback): `ChooseDomeSlot`/`ChooseDrawStackSlot`
            // tragen selbst KEINE Rotation (Platzhalter 0, siehe moves.rs) -- die
            // Rotationswahl ist ein separater `ChooseDomeRotation`-Zug, der als
            // KIND dieses Wurzelkandidaten im Suchbaum steht (game.rs::drafting_actions
            // liefert nach `ChooseDomeSlot`/`ChooseDrawStackSlot` via `pending_dome_choice`
            // ausschließlich `ChooseDomeRotation`-Kandidaten). Rein lesender Zugriff auf
            // bereits vorhandene Baumdaten (`node.children`) -- KEIN Effekt auf Suche/
            // Selektion/Backprop/RNG (nur diese Debug-JSON-Zusammenstellung betroffen).
            let best_rotation = node
                .children
                .iter()
                .filter_map(|&gc| match &nodes[gc].action {
                    Some(Action::ChooseDomeRotation(rot)) => Some((&nodes[gc], *rot)),
                    _ => None,
                })
                .max_by_key(|(gnode, _)| gnode.visits)
                .map(|(gnode, rot)| {
                    let gq = if gnode.visits > 0 { gnode.value / gnode.visits as f64 } else { 0.0 };
                    json!({ "rotation": rot, "visits": gnode.visits, "q": gq, "win_pct": gq * 100.0 })
                });
            json!({
                "action_id": i,
                "type": typ,
                "description": desc,
                "category": cat,
                "action": env_action,
                "net_prob": node.prior,
                "net_prob_norm": node.prior as f64 / prior_sum,
                "mcts_visits": node.visits,
                "mcts_share": if total_visits > 0 { node.visits as f64 / total_visits as f64 } else { 0.0 },
                "mcts_q": q,
                "mcts_win_pct": q * 100.0,
                // Task #95 (Anforderung 1): Netz-Blattwert DIESES Kindzustands,
                // aus Sicht des Spielers, der den Zug gemacht hat (dieselbe
                // Perspektive wie `mcts_q`/`node.value` -- siehe `node_own_value`-
                // Kommentar) -- bereits bei Expansion berechnet (`make_node`),
                // hier nur ausgelesen. Zeigt die Netz-ERSTEINSCHÄTZUNG dieses
                // Zugs, VOR jeder weiteren Suchvertiefung -- Divergenz zu
                // `mcts_q` zeigt, wo die Suche vom Netz abweicht.
                "net_leaf_value": node.leaf_value[node.player_who_acted],
                "max_depth": subtree_depth(nodes, cid),
                "chosen": is_chosen,
                // Task #97: besuchsstärkste Rotationswahl (Kind-Knoten) für
                // choose_dome_slot/choose_draw_stack_slot -- `null`, falls die Suche
                // diesen Kandidaten nie bis zur Rotationsstufe vertieft hat (kleines
                // Sim-Budget) oder der Kandidat kein Kuppelzug ist.
                "best_rotation": best_rotation,
            })
        })
        .collect();

    let root_visits = nodes[0].visits.max(1) as f64;
    let root_q = nodes[0].value / root_visits;

    // Task #95 (Anforderung 1): Root-Value-Anzeige -- `value`/`win_pct` sind
    // bestehende, vom Frontend (`debug.html`) bereits konsumierte Top-Level-
    // Felder (bisher IMMER `Null` im Netz-Pfad, siehe Git-Historie); mit
    // `value_debug` befüllt (nur wenn `collect_trace=true`) zeigen sie jetzt
    // den tatsächlichen Netz-Rohwert/die Ego-Win-Wahrscheinlichkeit der
    // Wurzel. `gumbel_trace` (Anforderung 2) bleibt `Null`, wenn kein Trace
    // angefordert wurde ODER die Suche nicht im Gumbel-Modus lief (PUCT-
    // Legacy-Pfad sammelt keinen Trace, siehe `build_net_tree`-Kommentar).
    let (value_field, win_pct_field, value_debug_field) = match trace.and_then(|t| t.root_value.as_ref()) {
        Some(vd) => (json!(vd.raw_value), json!(vd.win_prob * 100.0), vd.to_json()),
        None => (Value::Null, Value::Null, Value::Null),
    };
    let gumbel_trace_field = match trace {
        Some(t) if !t.top_m.is_empty() || !t.finalists.is_empty() => t.to_json(),
        _ => Value::Null,
    };

    let analysis = json!({
        "current_player": nodes[0].player_who_acted,
        "ai_player": state.current_player,
        "value": value_field,
        "win_pct": win_pct_field,
        "value_debug": value_debug_field,
        "gumbel_trace": gumbel_trace_field,
        "has_net": true,
        "simulations": sims,
        // Gesamtzahl legaler Züge (unabhängig vom Widening) vs. tatsächlich
        // durchsuchte Wurzelkinder — Server-Debug-UI zeigt "considered/total".
        "num_actions": nodes[0].n_actions,
        "num_actions_considered": nodes[0].children.len(),
        "max_depth": subtree_depth(nodes, 0),
        "ai_action": chosen_id,
        "moves": moves,
        "tree": json!({
            "visits": nodes[0].visits,
            "win_pct": root_q * 100.0,
            "depth": subtree_depth(nodes, 0),
            "n_children": nodes[0].children.len(),
        }),
    });

    let chosen = best.and_then(|cid| nodes[cid].action.clone());
    (chosen, analysis)
}

/// `net_search_with_tree`s Debug-Analyse-Dict aus dem Determinisierungs-Wald
/// (`NUM_DETERMINIZATIONS > 1`). Baut dieselben Felder wie
/// `net_search_with_tree_from_nodes`, aber aus den über die Welten
/// AGGREGIERTEN Größen (`aggregate_root_child_stats`/
/// `average_completed_q_policy`, siehe dortige Kommentare) statt einem
/// Einzelbaum -- "gewählter Zug" folgt derselben Regel wie
/// `net_search_drafting_action` (argmax gemittelte completed-Q-Politik).
/// Strukturelle Felder ohne sinnvolles Mehrwelten-Äquivalent (rohe
/// Netz-Priors VOR jeder Suche, `n_actions`) kommen repräsentativ aus der
/// ERSTEN Welt -- laut Befund im `NUM_DETERMINIZATIONS`-Kommentar sind
/// Wurzel-Kandidaten UND deren Priors (maskierte Features) weltunabhängig,
/// eine einzelne Welt ist hier also keine Näherung, sondern exakt.
fn net_search_with_tree_from_forest(state: &GameState, sims: u32, forest: &[Vec<Node>]) -> (Option<Action>, Value) {
    let stats = aggregate_root_child_stats(forest); // (Action, Σ Besuche, Q)
    let policy = average_completed_q_policy(forest); // (Action, gemittelte completed-Q-Wahrscheinlichkeit)
    let chosen: Option<Action> = policy
        .iter()
        .max_by(|a, b| a.1.partial_cmp(&b.1).unwrap_or(std::cmp::Ordering::Equal))
        .map(|(a, _)| a.clone());

    let total_visits: u32 = stats.iter().map(|(_, v, _)| *v).sum();
    let nodes0: &[Node] = &forest[0];
    let prior_sum: f64 = nodes0[0].children.iter().map(|&c| nodes0[c].prior as f64).sum::<f64>()
        + nodes0[0].untried.iter().map(|(_, p)| *p as f64).sum::<f64>();
    let prior_sum = prior_sum.max(1e-8);
    let prior_of = |a: &Action| -> f32 {
        nodes0[0]
            .children
            .iter()
            .find(|&&c| nodes0[c].action.as_ref() == Some(a))
            .map(|&c| nodes0[c].prior)
            .or_else(|| nodes0[0].untried.iter().find(|(act, _)| act == a).map(|(_, p)| *p))
            .unwrap_or(0.0)
    };
    // Task #95: `net_leaf_value` repräsentativ aus der ERSTEN Welt (siehe
    // Modul-Kommentar oben zu `prior_of`) -- `None`, wenn die Aktion in Welt 0
    // nie zu einem Kind wurde (kleineres Pro-Welt-Sims-Budget, siehe
    // `aggregate_root_child_stats`-Kommentar).
    let leaf_value_of = |a: &Action| -> Option<f64> {
        nodes0[0]
            .children
            .iter()
            .find(|&&c| nodes0[c].action.as_ref() == Some(a))
            .map(|&c| nodes0[c].leaf_value[nodes0[c].player_who_acted])
    };
    // Task #97: wie `leaf_value_of` -- repräsentativ aus Welt 0, besuchsstärkste
    // `ChooseDomeRotation`-KIND unter dem Wurzelkandidaten `a` (siehe ausführlicher
    // Kommentar in `net_search_with_tree_from_nodes`). `None`, wenn `a` in Welt 0
    // nie zu einem Kind wurde ODER dieses Kind nie bis zur Rotationsstufe vertieft
    // wurde. Aktuell praktisch unerreicht (NUM_DETERMINIZATIONS == 1 -> dieser
    // Forest-Pfad wird vom Debug-Endpunkt nicht durchlaufen), nur zur Schema-Parität
    // mit `net_search_with_tree_from_nodes` ergänzt (siehe Modul-Kommentar oben).
    let best_rotation_of = |a: &Action| -> Value {
        nodes0[0]
            .children
            .iter()
            .find(|&&c| nodes0[c].action.as_ref() == Some(a))
            .and_then(|&c| {
                nodes0[c]
                    .children
                    .iter()
                    .filter_map(|&gc| match &nodes0[gc].action {
                        Some(Action::ChooseDomeRotation(rot)) => Some((&nodes0[gc], *rot)),
                        _ => None,
                    })
                    .max_by_key(|(gnode, _)| gnode.visits)
                    .map(|(gnode, rot)| {
                        let gq = if gnode.visits > 0 { gnode.value / gnode.visits as f64 } else { 0.0 };
                        json!({ "rotation": rot, "visits": gnode.visits, "q": gq, "win_pct": gq * 100.0 })
                    })
            })
            .unwrap_or(Value::Null)
    };

    let mut ordered = stats.clone();
    ordered.sort_by(|a, b| b.1.cmp(&a.1));

    let mut chosen_id: Option<usize> = None;
    let moves: Vec<Value> = ordered
        .iter()
        .enumerate()
        .map(|(i, (act, visits, q))| {
            let (typ, desc, cat, _mv) = label_search_move(&SearchMove::Draft(act.clone()), Some(state));
            let is_chosen = chosen.as_ref() == Some(act);
            if is_chosen {
                chosen_id = Some(i);
            }
            let prior = prior_of(act);
            json!({
                "action_id": i,
                "type": typ,
                "description": desc,
                "category": cat,
                "net_prob": prior,
                "net_prob_norm": prior as f64 / prior_sum,
                "mcts_visits": *visits,
                "mcts_share": if total_visits > 0 { *visits as f64 / total_visits as f64 } else { 0.0 },
                "mcts_q": *q,
                "mcts_win_pct": *q * 100.0,
                "net_leaf_value": leaf_value_of(act),
                "max_depth": Value::Null,
                "chosen": is_chosen,
                "best_rotation": best_rotation_of(act),
            })
        })
        .collect();

    let (visits_sum, value_sum): (u32, f64) = stats
        .iter()
        .fold((0u32, 0.0f64), |(vs, vl), (_, v, q)| (vs + v, vl + q * (*v as f64)));
    let root_q = if visits_sum > 0 { value_sum / visits_sum as f64 } else { 0.0 };
    let max_depth = forest.iter().map(|nodes| subtree_depth(nodes, 0)).max().unwrap_or(0);

    let analysis = json!({
        "current_player": nodes0[0].player_who_acted,
        "ai_player": state.current_player,
        "value": Value::Null,
        "win_pct": Value::Null,
        // Task #95: ROOT-Value-Breakdown/Gumbel-Trace nur im Einzelbaum-Pfad
        // unterstützt (siehe `net_search_with_tree`-Kommentar) -- hier immer
        // `Null`, damit das Analyse-Dict-Schema in beiden Pfaden gleich bleibt.
        "value_debug": Value::Null,
        "gumbel_trace": Value::Null,
        "has_net": true,
        "simulations": sims,
        "determinizations": NUM_DETERMINIZATIONS,
        "num_actions": nodes0[0].n_actions,
        "num_actions_considered": stats.len(),
        "max_depth": max_depth,
        "ai_action": chosen_id,
        "moves": moves,
        "tree": json!({
            "visits": visits_sum,
            "win_pct": root_q * 100.0,
            "depth": max_depth,
            "n_children": stats.len(),
        }),
    });

    (chosen, analysis)
}

/// Tiefe des Teilbaums unter `nid` (0 = Blatt) — Pendant zu `mcts::subtree_depth`,
/// beide delegieren an `search_common::subtree_depth`.
fn subtree_depth(nodes: &[Node], nid: usize) -> u32 {
    crate::search_common::subtree_depth(nodes, nid)
}

/// Kopfzeilen für ein Netz-PUCT-Log aus State + Analyse (für den geloggten
/// KI-Zug) — Pendant zu `mcts::search_log_header`. Der eigentliche Sim-für-
/// Sim-Trace kommt separat aus `build_net_tree`s `log`-Parameter.
pub fn net_search_log_header(state: &GameState, analysis: &Value) -> String {
    let sims = analysis["simulations"].as_u64().unwrap_or(0);
    let na = analysis["num_actions"].as_u64().unwrap_or(0);
    let considered = analysis["num_actions_considered"].as_u64().unwrap_or(0);
    let chosen = analysis["moves"]
        .as_array()
        .and_then(|ms| ms.iter().find(|m| m["chosen"] == json!(true)))
        .and_then(|m| m["description"].as_str())
        .unwrap_or("?");
    format!(
        "Netz-PUCT-Debug-Log (KI-Zug)\nSimulationen={sims}  Aktionen={considered}/{na} durchsucht (Policy-Masse-Cutoff)  Wurzelspieler={}\nSpieler: P0={}  P1={}\nGewaehlter Zug: {chosen}\n{}\n",
        state.players[state.current_player].name,
        state.players[0].name,
        state.players[1].name,
        "=".repeat(60),
    )
}

// ── Dirichlet/Gamma-Sampling (ohne rand_distr) ──────────────────────────────────

fn std_normal<R: Rng + ?Sized>(rng: &mut R) -> f64 {
    let u1: f64 = rng.random_range(1e-12..1.0);
    let u2: f64 = rng.random_range(0.0..1.0);
    (-2.0 * u1.ln()).sqrt() * (2.0 * std::f64::consts::PI * u2).cos()
}

/// Gamma(alpha, 1) per Marsaglia-Tsang (mit Boost für alpha < 1).
fn gamma<R: Rng + ?Sized>(alpha: f64, rng: &mut R) -> f64 {
    if alpha < 1.0 {
        let u: f64 = rng.random_range(1e-12..1.0);
        return gamma(alpha + 1.0, rng) * u.powf(1.0 / alpha);
    }
    let d = alpha - 1.0 / 3.0;
    let c = 1.0 / (9.0 * d).sqrt();
    loop {
        let x = std_normal(rng);
        let v = (1.0 + c * x).powi(3);
        if v <= 0.0 {
            continue;
        }
        let u: f64 = rng.random_range(0.0..1.0);
        if u < 1.0 - 0.0331 * x.powi(4) || u.ln() < 0.5 * x * x + d * (1.0 - v + v.ln()) {
            return d * v;
        }
    }
}

fn dirichlet<R: Rng + ?Sized>(n: usize, alpha: f64, rng: &mut R) -> Vec<f64> {
    let g: Vec<f64> = (0..n).map(|_| gamma(alpha, rng)).collect();
    let s: f64 = g.iter().sum::<f64>().max(1e-12);
    g.iter().map(|&x| x / s).collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::state::setup_new_game;
    use rand::rngs::StdRng;
    use rand::seq::IndexedRandom;
    use rand::SeedableRng;

    fn names() -> [String; 2] {
        ["P1".into(), "P2".into()]
    }

    #[test]
    fn unique_moon_orders_dedups_repeated_colors() {
        // 3 verschiedene Farben -> alle 6 Permutationen eindeutig.
        let all_diff = [TileColor::Blau, TileColor::Gelb, TileColor::Rot];
        assert_eq!(unique_moon_orders(&all_diff).len(), 6);

        // 2x dieselbe Farbe + 1 andere -> nur 3 unterscheidbare Reihenfolgen
        // (die beiden Rot-Fliesen sind ununterscheidbar).
        let two_same = [TileColor::Rot, TileColor::Rot, TileColor::Blau];
        let orders = unique_moon_orders(&two_same);
        assert_eq!(orders.len(), 3);
        for o in &orders {
            let mut sorted = o.clone();
            sorted.sort_by_key(|c| c.value());
            let mut expected = two_same.to_vec();
            expected.sort_by_key(|c| c.value());
            assert_eq!(sorted, expected);
        }

        // Alle 3 gleich -> nur 1 mögliche Reihenfolge.
        let all_same = [TileColor::Schwarz, TileColor::Schwarz, TileColor::Schwarz];
        assert_eq!(unique_moon_orders(&all_same).len(), 1);

        // 1 Restfliese -> genau 1 Reihenfolge.
        assert_eq!(unique_moon_orders(&[TileColor::Tuerkis]).len(), 1);

        // 0 Restfliesen -> 1 leere Reihenfolge (kein Stapel nötig).
        assert_eq!(unique_moon_orders(&[]), vec![Vec::<TileColor>::new()]);
    }

    #[test]
    fn gumbel_top_m_for_budget_unchanged_at_400_and_600_sims() {
        // Task #14: bei den bisherigen Standard-Suchbudgets (Arena/Self-Play,
        // s. `DECOUPLE_NET_SIMS_FROM_ACTIONS`-Kommentar) MUSS die neue
        // budgetabhaengige Formel exakt dieselbe Wurzelbreite liefern wie die
        // alte fixe Konstante -- sonst waere die Aenderung nicht additiv.
        assert_eq!(gumbel_top_m_for_budget(400), GUMBEL_TOP_M);
        assert_eq!(gumbel_top_m_for_budget(600), GUMBEL_TOP_M);
        // Auch knapp unterhalb/oberhalb bleibt es beim Ceiling (16*16=256 ist
        // die kleinste Sim-Zahl, bei der round(sims/16) ueberhaupt >= 16
        // wird -- alles ab da wird gekappt).
        assert_eq!(gumbel_top_m_for_budget(256), GUMBEL_TOP_M);
        assert_eq!(gumbel_top_m_for_budget(1000), GUMBEL_TOP_M);

        // Untere Clamp-Grenze: sehr kleine (z.B. PCR-Cheap-)Budgets duerfen
        // nie unter 4 Kandidaten fallen.
        assert_eq!(gumbel_top_m_for_budget(1), 4);
        assert_eq!(gumbel_top_m_for_budget(32), 4);

        // Dazwischen: proportional zum Budget (Sequential-Halving-Argument
        // im Funktionskommentar), gerundet.
        assert_eq!(gumbel_top_m_for_budget(150), 9); // round(150/16) = 9.375 -> 9
        assert_eq!(gumbel_top_m_for_budget(64), 4); // round(64/16) = 4 (untere Grenze exakt getroffen)
        assert_eq!(gumbel_top_m_for_budget(128), 8); // round(128/16) = 8
    }

    #[test]
    fn plackett_luce_probs_sum_to_one_over_all_unique_orders() {
        let remaining = [TileColor::Blau, TileColor::Gelb, TileColor::Rot];
        let orders = unique_moon_orders(&remaining);
        // Beliebige, nicht-uniforme Scores.
        let scores = [2.0f32, -1.0, 0.5, 3.0, -2.0];
        let total: f64 = orders.iter().map(|o| plackett_luce_prob(&scores, o)).sum();
        assert!((total - 1.0).abs() < 1e-9, "Summe war {total}, erwartet 1.0");

        // Auch mit Farbwiederholung (3 Order statt 6) muss die Summe 1 bleiben.
        let remaining2 = [TileColor::Rot, TileColor::Rot, TileColor::Blau];
        let orders2 = unique_moon_orders(&remaining2);
        let total2: f64 = orders2.iter().map(|o| plackett_luce_prob(&scores, o)).sum();
        assert!((total2 - 1.0).abs() < 1e-9, "Summe war {total2}, erwartet 1.0");
    }

    #[test]
    fn plackett_luce_prefers_higher_scored_color_first() {
        // Score für Rot (Index 2) klar am höchsten -> P(Rot zuerst) muss die
        // größte Einzelwahrscheinlichkeit unter den Permutationen sein, die
        // mit Rot beginnen, gegenüber denen, die mit Blau beginnen.
        let scores = [0.0f32, 0.0, 5.0, 0.0, 0.0]; // Rot dominiert klar
        let p_rot_first = plackett_luce_prob(&scores, &[TileColor::Rot, TileColor::Blau]);
        let p_blau_first = plackett_luce_prob(&scores, &[TileColor::Blau, TileColor::Rot]);
        assert!(p_rot_first > p_blau_first, "{p_rot_first} sollte > {p_blau_first} sein");
        assert!(p_rot_first > 0.9, "bei Score-Differenz 5.0 sollte P(Rot zuerst) dominieren");
    }

    #[test]
    fn build_untried_actions_truncates_long_tail_for_peaked_policy() {
        // Genau EINE legale Aktions-ID stark bevorzugen -> praktisch die gesamte
        // Masse liegt auf ihr (+ ggf. ihren Moon-Order-Varianten), der Rest ist
        // Long Tail und sollte komplett verworfen werden.
        let mut rng = StdRng::seed_from_u64(11);
        let state = setup_new_game(names(), 0, &mut rng);
        let base_actions = drafting_actions(&state);
        assert!(base_actions.len() > 5, "Testvoraussetzung: früher Zustand mit vielen legalen Zügen");
        let spike_id = action_to_id(&action_to_env_dict(&state, &base_actions[0]));

        let mut logits = vec![-10.0f32; NUM_ACTIONS];
        logits[spike_id] = 10.0;
        let moon_scores = [0.0f32; 5];

        let (acts, n_base) = build_untried_actions(&state, &logits, &moon_scores, false);
        assert!(!acts.is_empty());
        assert!(
            acts.len() < n_base,
            "Kappung sollte bei stark geneigter Verteilung deutlich weniger Kandidaten \
             behalten als Basis-Aktionen: {} Kandidaten vs. {} Basis-Aktionen",
            acts.len(),
            n_base
        );
        let total: f64 = acts.iter().map(|(_, p)| *p as f64).sum();
        assert!(total >= POLICY_MASS_CUTOFF && total <= 1.0 + 1e-4);
    }

    #[test]
    fn build_untried_actions_priors_reach_cutoff_and_expand_moon_orders() {
        let mut rng = StdRng::seed_from_u64(42);
        let state = setup_new_game(names(), 0, &mut rng);
        let logits = vec![0.1f32; NUM_ACTIONS];
        let moon_scores = [1.0f32, 0.5, -0.5, 2.0, 0.0];

        let (acts, n_base) = build_untried_actions(&state, &logits, &moon_scores, false);
        assert!(!acts.is_empty());

        // Kandidaten sind auf den POLICY_MASS_CUTOFF-Präfix gekappt (Long Tail
        // verworfen) — die Summe muss also mindestens den Cutoff erreichen
        // (der Schritt, der ihn überschreitet, wird noch mitgenommen), aber
        // nie mehr als 1.0 (Moon-Order-Aufteilung erzeugt/verliert keine Masse).
        let total: f64 = acts.iter().map(|(_, p)| *p as f64).sum();
        assert!(
            total >= POLICY_MASS_CUTOFF && total <= 1.0 + 1e-4,
            "Summe der (gekappten) Priors war {total}, erwartet in [{POLICY_MASS_CUTOFF}, 1.0]"
        );

        // Mindestens eine SmallFactorySun-Basis-Aktion mit ≥2 Restfliesen sollte
        // beim Spielstart existieren (4 Fabriken × 4 Fliesen) -> Expansion
        // muss stattgefunden haben (mehr Kandidaten als Basis-Aktionen).
        let has_multi_order = state.factories.iter().any(|f| {
            f.sun_colors().iter().any(|&c| {
                f.sun_tiles.iter().filter(|&&t| t != c).count() >= 2
            })
        });
        if has_multi_order {
            assert!(
                acts.len() > n_base,
                "Erwartete Moon-Order-Expansion (mehr Kandidaten als Basis-Aktionen): {} vs {}",
                acts.len(),
                n_base
            );
        }

        // Für jede expandierte SmallFactorySun-Gruppe: die Prior-Summe der
        // Varianten muss der Basis-ID-Wahrscheinlichkeit entsprechen (Prüfung
        // über Gruppierung nach (color,row,factory), da die ID selbst nicht
        // direkt zugänglich ist -> stattdessen Gesamtsumme je Gruppe > 0).
        use std::collections::HashMap as Map;
        let mut groups: Map<(String, i32, Option<usize>), f64> = Map::new();
        for (act, p) in &acts {
            if let Action::Stone(m) = act {
                if m.take.source == TakeSource::SmallFactorySun {
                    let key = (m.take.color.value().to_string(), m.place.row_index, m.take.factory_id);
                    *groups.entry(key).or_insert(0.0) += *p as f64;
                }
            }
        }
        assert!(!groups.is_empty(), "keine SmallFactorySun-Gruppen gefunden");
        for (_, sum) in &groups {
            assert!(*sum > 0.0);
        }
    }

    /// Baut einen frischen Zustand OHNE offene Startplatten-Pflicht (sonst
    /// blockiert `validate_dome_move`/`has_unplaced_start_tile` jede
    /// `Action::ChooseDomeSlot`-Kandidatengenerierung -- siehe game.rs).
    fn state_with_dome_moves_available(seed: u64) -> GameState {
        let mut rng = StdRng::seed_from_u64(seed);
        let mut state = setup_new_game(names(), 0, &mut rng);
        for p in state.players.iter_mut() {
            p.start_tile_pending = false;
        }
        state
    }

    #[test]
    fn build_untried_actions_dome_slot_candidates_get_independent_direct_priors() {
        // Baustein B: ChooseDomeSlot-Kandidaten (Kachel+Slot) haben seit der
        // Zerlegung in game.rs JEWEILS eine eigene, nicht kollabierte Policy-ID
        // (siehe features.rs::action_to_id) -- keine Faktorisierung mehr noetig.
        // Ein geboosteter Logit fuer GENAU EINE ID darf also NUR deren eigenen
        // Prior anheben, keine Geschwister-Kandidaten.
        let state = state_with_dome_moves_available(7);
        let base_actions = drafting_actions(&state);
        let dome_candidates: Vec<&Action> =
            base_actions.iter().filter(|a| matches!(a, Action::ChooseDomeSlot(_))).collect();
        assert!(dome_candidates.len() > 1, "Testvoraussetzung: mehrere ChooseDomeSlot-Kandidaten");

        let target_id = crate::self_play::action_to_id_direct(&state, dome_candidates[0]);
        let mut logits = vec![0.1f32; NUM_ACTIONS];
        logits[target_id] = 5.0;
        let moon_scores = [0f32; 5];

        let (acts, _n) = build_untried_actions(&state, &logits, &moon_scores, false);

        let target_p = acts
            .iter()
            .find(|(a, _)| matches!(a, Action::ChooseDomeSlot(_)) && crate::self_play::action_to_id_direct(&state, a) == target_id)
            .map(|(_, p)| *p)
            .expect("geboostete ID sollte im Kandidatenergebnis auftauchen");
        for (a, p) in &acts {
            if matches!(a, Action::ChooseDomeSlot(_)) && crate::self_play::action_to_id_direct(&state, a) != target_id {
                assert!(
                    target_p > *p,
                    "geboosteter Kandidat sollte strikt hoeheren Prior haben als \
                     ungeboostete Geschwister: {target_p} vs {p}"
                );
            }
        }
    }

    #[test]
    fn build_untried_actions_draw_stack_candidates_carry_positive_mass() {
        // DrawStack-Kandidaten existieren nur waehrend eines laufenden
        // Stapel-Zugs (`pending_stack_draw` nichtleer) -- direkt konstruieren
        // statt durch echtes Ziehen zu spielen (kein bestehender Test-
        // Helfer dafuer, siehe game.rs::generate_draw_stack_moves-Doc).
        let mut state = state_with_dome_moves_available(3);
        let pending: Vec<_> = state.dome_tile_pool.iter().take(2).cloned().collect();
        assert!(pending.len() >= 2, "Testvoraussetzung: genug Platten im verdeckten Stapel");
        state.pending_stack_draw = pending;

        let base_actions = drafting_actions(&state);
        let draw_stack_count =
            base_actions.iter().filter(|a| matches!(a, Action::ChooseDrawStackSlot(_))).count();
        assert!(draw_stack_count > 1, "Testvoraussetzung: mehrere ChooseDrawStackSlot-Kandidaten");

        let logits = vec![0.1f32; NUM_ACTIONS];
        let moon_scores = [0f32; 5];
        let (acts, _n) = build_untried_actions(&state, &logits, &moon_scores, false);

        let draw_stack_sum: f64 = acts
            .iter()
            .filter(|(a, _)| matches!(a, Action::ChooseDrawStackSlot(_)))
            .map(|(_, p)| *p as f64)
            .sum();
        assert!(draw_stack_sum > 0.0, "ChooseDrawStackSlot-Kandidaten sollten positive Prior-Masse tragen");
    }

    // ── Gumbel AlphaZero: Kern-Mathematik (Phase 1) ─────────────────────────

    fn gumbel_test_state(current_player: usize) -> GameState {
        let mut rng = StdRng::seed_from_u64(0);
        let mut s = setup_new_game(names(), 0, &mut rng);
        s.current_player = current_player;
        s
    }

    /// Minimaler Testknoten -- nur die für Gumbel-Mathematik relevanten
    /// Felder (`prior`/`visits`/`value`/`leaf_value`/`state.current_player`)
    /// sind aussagekräftig, der Rest ist Fuellwerk.
    fn gumbel_test_node(prior: f32, visits: u32, value: f64, current_player: usize) -> Node {
        Node {
            parent: None,
            children: Vec::new(),
            untried: Vec::new(),
            action: None,
            player_who_acted: 0,
            visits,
            value,
            prior,
            state: gumbel_test_state(current_player),
            terminal: false,
            leaf_value: [0.0, 0.0],
            n_actions: 0,
        }
    }

    #[test]
    fn sample_gumbel_is_reproducible_with_fixed_seed() {
        let mut rng_a = StdRng::seed_from_u64(42);
        let mut rng_b = StdRng::seed_from_u64(42);
        let a: Vec<f64> = (0..20).map(|_| sample_gumbel(&mut rng_a)).collect();
        let b: Vec<f64> = (0..20).map(|_| sample_gumbel(&mut rng_b)).collect();
        assert_eq!(a, b, "gleicher Seed muss dieselbe Gumbel-Folge liefern");
        // Sanity: nicht alle Werte identisch (echte Ziehung, keine Konstante).
        assert!(a.iter().any(|&x| (x - a[0]).abs() > 1e-6));
    }

    #[test]
    fn gumbel_sigma_matches_formula_directly() {
        let q = 0.7;
        let max_n = 30u32;
        let expected = (GUMBEL_C_VISIT + max_n as f64) * GUMBEL_C_SCALE * q;
        assert!((gumbel_sigma(q, max_n) - expected).abs() < 1e-12);
    }

    #[test]
    fn v_mix_falls_back_to_node_own_value_when_no_child_visited() {
        // Wurzel mit eigenem Blattwert 0.42 (Mover-Perspektive, current_player=0),
        // ein Kind, aber NIE besucht (visits=0) -- v_mix muss exakt auf den
        // eigenen Blattwert zurueckfallen (kein NaN, keine Division durch 0).
        let mut root = gumbel_test_node(0.0, 0, 0.0, 0);
        root.leaf_value = [0.42, 0.58];
        let child = gumbel_test_node(0.5, 0, 0.0, 1);
        let nodes = vec![root, child];
        let mut nodes = nodes;
        nodes[0].children.push(1);
        assert!((v_mix(&nodes, 0) - 0.42).abs() < 1e-12);
    }

    #[test]
    fn v_mix_matches_hand_computed_example_with_two_visited_children() {
        // Wurzel: eigener Blattwert 0.5 (current_player=0). Zwei Kinder:
        // Kind A prior=0.6 visits=4 value_sum=2.4 (Q=0.6), Kind B prior=0.2
        // visits=2 value_sum=1.6 (Q=0.8). N_total = 4+2 = 6.
        // weighted_Q = (0.6*0.6 + 0.2*0.8) / (0.6+0.2) = (0.36+0.16)/0.8 = 0.65
        // v_mix = (0.5 + 6*0.65) / (1+6) = (0.5 + 3.9) / 7 = 0.62857142857...
        let mut root = gumbel_test_node(0.0, 0, 0.0, 0);
        root.leaf_value = [0.5, 0.5];
        let child_a = gumbel_test_node(0.6, 4, 2.4, 1);
        let child_b = gumbel_test_node(0.2, 2, 1.6, 1);
        let mut nodes = vec![root, child_a, child_b];
        nodes[0].children.push(1);
        nodes[0].children.push(2);
        let expected = (0.5 + 6.0 * 0.65) / 7.0;
        assert!((v_mix(&nodes, 0) - expected).abs() < 1e-9, "v_mix={} expected={}", v_mix(&nodes, 0), expected);
    }

    #[test]
    fn completed_q_uses_own_q_for_visited_and_v_mix_for_unvisited() {
        let mut root = gumbel_test_node(0.0, 0, 0.0, 0);
        root.leaf_value = [0.5, 0.5];
        let child_a = gumbel_test_node(0.6, 4, 2.4, 1); // Q=0.6, besucht
        let mut nodes = vec![root, child_a];
        nodes[0].children.push(1);
        nodes[0].untried.push((Action::Pass, 0.1));
        nodes[0].untried.push((Action::Pass, 0.05));
        let cq = completed_q_per_candidate(&nodes, 0);
        assert_eq!(cq.len(), 3, "1 Kind + 2 untried");
        assert!((cq[0].1 - 0.6).abs() < 1e-9, "besuchtes Kind behaelt eigenes Q");
        let vmix = v_mix(&nodes, 0);
        assert!((cq[1].1 - vmix).abs() < 1e-12, "unbesucht #1 bekommt v_mix");
        assert!((cq[2].1 - vmix).abs() < 1e-12, "unbesucht #2 bekommt v_mix");
        assert!((cq[1].1 - cq[2].1).abs() < 1e-12, "alle unbesuchten Kandidaten teilen denselben v_mix");
    }

    #[test]
    fn improved_policy_sums_to_one_and_matches_hand_example() {
        // Wurzel mit einem besuchten Kind (prior=0.5, Q=0.6, visits=3) und
        // zwei unbesuchten Kandidaten (prior=0.3, prior=0.2). max_N=3.
        let mut root = gumbel_test_node(0.0, 0, 0.0, 0);
        root.leaf_value = [0.4, 0.6];
        let child = gumbel_test_node(0.5, 3, 1.8, 1); // Q = 1.8/3 = 0.6
        let mut nodes = vec![root, child];
        nodes[0].children.push(1);
        nodes[0].untried.push((Action::Pass, 0.3));
        nodes[0].untried.push((Action::Pass, 0.2));

        let policy = improved_policy(&nodes, 0);
        assert_eq!(policy.len(), 3);
        let total: f64 = policy.iter().sum();
        assert!((total - 1.0).abs() < 1e-9, "Policy muss zu 1.0 summieren, ist {total}");

        // Von Hand nachrechnen: max_N=3, vmix = (0.4 + 3*0.6)/(1+3) = 2.2/4 = 0.55
        let vmix_expected = (0.4 + 3.0 * 0.6) / 4.0;
        let score_child = 0.5f64.ln() + gumbel_sigma(0.6, 3);
        let score_u1 = 0.3f64.ln() + gumbel_sigma(vmix_expected, 3);
        let score_u2 = 0.2f64.ln() + gumbel_sigma(vmix_expected, 3);
        let expected = softmax_f64(&[score_child, score_u1, score_u2]);
        for (a, b) in policy.iter().zip(expected.iter()) {
            assert!((a - b).abs() < 1e-6, "policy={policy:?} expected={expected:?}");
        }
    }

    #[test]
    fn gumbel_select_child_can_pick_a_strongly_preferred_unvisited_candidate_over_existing_children() {
        // Paket 2 (mctx-treue Tiefe-≥1-Auswahl, 2026-07-22): anders als die
        // alte Auswahl (nur ueber `nodes[nid].children`, ein separater
        // Widening-Cap entschied, WANN neue Kandidaten ueberhaupt entstehen
        // duerfen) muss die Auswahl jetzt auch einen bislang UNBESUCHTEN
        // Kandidaten (hoher Prior, N=0) waehlen koennen, selbst wenn ein Kind
        // schon 200 Besuche hat -- `N(a)/(1+ΣN)` bestraft den vielbesuchten
        // Kandidaten irgendwann so stark, dass ein hochpriorisierter, nie
        // besuchter Kandidat gewinnt.
        let mut root = gumbel_test_node(0.0, 0, 0.0, 0);
        root.leaf_value = [0.5, 0.5];
        let child = gumbel_test_node(0.3, 200, 100.0, 1); // Q = 100/200 = 0.5, stark besucht
        let mut nodes = vec![root, child];
        nodes[0].children.push(1);
        nodes[0].untried.push((Action::Pass, 0.65)); // deutlich hoeherer Prior, N=0

        let idx = gumbel_select_child(&nodes, 0);
        assert_eq!(
            idx, 1,
            "Kombi-Index 1 (= der einzige untried-Kandidat, nach 1 Kind) haette gewaehlt werden muessen, war {idx}"
        );
    }

    #[test]
    fn root_completed_q_policy_pairs_each_action_with_its_own_probability() {
        // Wurzel mit einem besuchten Kind (Action::Pass) und zwei unbesuchten
        // Kandidaten (Action::DrawStackPeek, Action::ChooseDomeRotation(1)) --
        // prueft, dass `root_completed_q_policy` dieselben Zahlen wie
        // `improved_policy` liefert UND korrekt der jeweils richtigen Aktion
        // zuordnet (children zuerst, dann untried, wie `completed_q_per_candidate`).
        let mut root = gumbel_test_node(0.0, 0, 0.0, 0);
        root.leaf_value = [0.4, 0.6];
        let mut child = gumbel_test_node(0.5, 3, 1.8, 1); // Q = 0.6
        child.action = Some(Action::Pass);
        let mut nodes = vec![root, child];
        nodes[0].children.push(1);
        nodes[0].untried.push((Action::DrawStackPeek, 0.3));
        nodes[0].untried.push((Action::ChooseDomeRotation(1), 0.2));

        let numeric = improved_policy(&nodes, 0);
        let paired = root_completed_q_policy(&nodes);
        assert_eq!(paired.len(), 3);

        let total: f64 = paired.iter().map(|(_, p)| p).sum();
        assert!((total - 1.0).abs() < 1e-9, "Policy muss zu 1.0 summieren, ist {total}");

        assert_eq!(paired[0].0, Action::Pass);
        assert!((paired[0].1 - numeric[0]).abs() < 1e-12);
        assert_eq!(paired[1].0, Action::DrawStackPeek);
        assert!((paired[1].1 - numeric[1]).abs() < 1e-12);
        assert_eq!(paired[2].0, Action::ChooseDomeRotation(1));
        assert!((paired[2].1 - numeric[2]).abs() < 1e-12);
    }

    // ── ISMCTS-Mehrfach-Determinisierung (Task #65) ─────────────────────────

    #[test]
    fn average_completed_q_policy_averages_matching_actions_across_worlds() {
        // Zwei synthetische "Welten" mit identischem Kandidatensatz (Pass
        // besucht, DrawStackPeek/ChooseDomeRotation(1) unbesucht), aber
        // unterschiedlichen Besuchs-/Wertstatistiken -- prueft, dass
        // `average_completed_q_policy` exakt das arithmetische Mittel der
        // Pro-Welt-`root_completed_q_policy`-Ausgaben liefert (Aktions-
        // Schluessel, siehe `NUM_DETERMINIZATIONS`-Kommentar).
        fn make_world(child_visits: u32, child_value: f64, root_leaf: [f64; 2]) -> Vec<Node> {
            let mut root = gumbel_test_node(0.0, 0, 0.0, 0);
            root.leaf_value = root_leaf;
            let mut child = gumbel_test_node(0.5, child_visits, child_value, 1);
            child.action = Some(Action::Pass);
            let mut nodes = vec![root, child];
            nodes[0].children.push(1);
            nodes[0].untried.push((Action::DrawStackPeek, 0.3));
            nodes[0].untried.push((Action::ChooseDomeRotation(1), 0.2));
            nodes
        }

        let world1 = make_world(3, 1.8, [0.4, 0.6]); // Q_pass = 0.6
        let world2 = make_world(5, 2.0, [0.5, 0.5]); // Q_pass = 0.4
        let p1 = root_completed_q_policy(&world1);
        let p2 = root_completed_q_policy(&world2);
        let forest = vec![world1, world2];

        let averaged = average_completed_q_policy(&forest);
        assert_eq!(averaged.len(), 3);
        let total: f64 = averaged.iter().map(|(_, p)| p).sum();
        assert!((total - 1.0).abs() < 1e-9, "gemittelte Politik muss zu 1.0 summieren, ist {total}");

        for i in 0..3 {
            assert_eq!(averaged[i].0, p1[i].0, "Aktions-Reihenfolge sollte der ersten Welt folgen");
            assert_eq!(averaged[i].0, p2[i].0, "beide Welten sollten denselben Kandidatensatz haben");
            let expected = (p1[i].1 + p2[i].1) / 2.0;
            assert!(
                (averaged[i].1 - expected).abs() < 1e-9,
                "Aktion {:?}: gemittelt={} erwartet={}",
                averaged[i].0,
                averaged[i].1,
                expected
            );
        }
    }

    #[test]
    fn aggregate_root_child_stats_sums_visits_and_weighted_averages_q_across_worlds() {
        // Zwei Welten, beide besuchen Action::Pass als Wurzelkind mit
        // unterschiedlichen Besuchs-/Wertsummen -- Erwartung: Besuche werden
        // SUMMIERT (treibt Self-Plays besuchsbasierte Stichprobe ueber die
        // Welten-SUMME), Q = Sigma(Value)/Sigma(Besuche) -- NICHT das
        // einfache arithmetische Mittel der Pro-Welt-Q-Werte.
        fn make_world(child_visits: u32, child_value: f64) -> Vec<Node> {
            let mut root = gumbel_test_node(0.0, 0, 0.0, 0);
            root.leaf_value = [0.5, 0.5];
            let mut child = gumbel_test_node(0.5, child_visits, child_value, 1);
            child.action = Some(Action::Pass);
            let mut nodes = vec![root, child];
            nodes[0].children.push(1);
            nodes
        }
        let world1 = make_world(3, 1.8); // Q=0.6
        let world2 = make_world(5, 2.0); // Q=0.4
        let forest = vec![world1, world2];

        let stats = aggregate_root_child_stats(&forest);
        assert_eq!(stats.len(), 1);
        let (act, visits, q) = &stats[0];
        assert_eq!(*act, Action::Pass);
        assert_eq!(*visits, 8, "Besuche muessen SUMMIERT werden (3+5)");
        let expected_q = (1.8 + 2.0) / 8.0;
        assert!(
            (q - expected_q).abs() < 1e-9,
            "Q={q} erwartet={expected_q} (gewichteter Mittelwert, nicht einfacher Mittelwert der Pro-Welt-Qs)"
        );
    }

    #[test]
    fn split_sims_across_worlds_puts_remainder_on_first_world() {
        assert_eq!(split_sims_across_worlds(150, 3), vec![50, 50, 50]);
        assert_eq!(split_sims_across_worlds(151, 3), vec![51, 50, 50]);
        assert_eq!(split_sims_across_worlds(8, 1), vec![8]);
        assert_eq!(split_sims_across_worlds(7, 5), vec![3, 1, 1, 1, 1]);
    }

    /// Laedt das aktuelle Produktions-Modell fuer die beiden folgenden
    /// Perspektiven-/Vorzeichen-Tests (`evaluations/value head tests.txt`,
    /// Punkt 2, "klassische Vorzeichen-Unit-Tests"). Ueberspringt sich
    /// selbst (statt zu failen), falls die Datei lokal fehlt -- `models/`
    /// ist per `.gitignore` nicht Teil des Checkouts, ein frischer Klon
    /// haette also sonst einen harten Testfehler ohne jeden eigenen Fehler.
    fn load_test_net() -> Option<Net> {
        let path = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../models/alphazero_v10_best.onnx");
        match Net::load_auto(path.to_str().unwrap()) {
            Ok(n) => Some(n),
            Err(e) => {
                eprintln!("  ⚠️  {path:?} nicht ladbar ({e}) -- Test übersprungen (kein lokaler Checkpoint).");
                None
            }
        }
    }

    /// Spielt ein paar zufaellige Drafting-Zuege aus `Game::start` heraus
    /// (kein Tiling -- reicht fuer die Value-Head-Perspektiventests unten,
    /// die nur reale, unterschiedliche Drafting-Stellungen brauchen).
    /// Gibt `None`, falls die Drafting-Phase vor Ablauf der Schritte endet.
    fn random_drafting_state<R: Rng + ?Sized>(seed_tag: u64, steps: u32, rng: &mut R) -> Option<GameState> {
        let ids = crate::scoring::sample_valid_scoring_ids(3, rng);
        let mut game = Game::start(
            [format!("A{seed_tag}"), format!("B{seed_tag}")],
            (seed_tag % 2) as usize,
            ids,
            rng,
        );
        // Startkuppel-Platzierung überspringen -- seit dem R5-Gate
        // (Vollaudit 2026-07-21) lehnt apply_drafting sonst alles ab.
        for p in game.state.players.iter_mut() {
            p.start_tile_pending = false;
        }
        for _ in 0..steps {
            if game.state.phase != Phase::Drafting {
                return None;
            }
            let actions = drafting_actions(&game.state);
            if actions.is_empty() {
                return None;
            }
            let a = actions.choose(rng).unwrap().clone();
            let _ = game.apply_drafting(&a);
        }
        (game.state.phase == Phase::Drafting).then_some(game.state)
    }

    /// Laedt ein lokal vorhandenes Modell fuer den `BATCH_ROOT_EXPANSION`-
    /// Paritaetstest unten -- `load_test_net()` (oben) haengt an
    /// `alphazero_v10_best.onnx`, das im aktuellen Modell-Bestand nicht
    /// mehr vorhanden ist (gleicher Befund wie bei den Task-#14-PCR-Tests
    /// in `self_play.rs`/den `eval_batch`-Tests in `net.rs`). Bewusst der
    /// AMTIERENDE 2D-Champion `v19_2d_best` (nicht ein flaches Modell) --
    /// das ist der eigentliche Zielpunkt dieses Perf-Auftrags (die
    /// 1,46x-2D-Inferenzkosten druecken), der Paritaetstest soll also genau
    /// DIESE Architektur (`PlanesPlusFlat`-Layout, ZWEI ONNX-Graph-Inputs)
    /// abdecken, nicht nur den einfacheren flachen Pfad.
    fn load_batching_test_net() -> Option<Net> {
        let path = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../models/alphazero_v19_2d_best.onnx");
        Net::load_auto(path.to_str().unwrap()).ok()
    }

    /// Perf-Auftrag (2026-08-02) -- Kernabsicherung fuer `BATCH_ROOT_EXPANSION`:
    /// `build_gumbel_tree_inner` mit `batch_root_expansion=true` muss bei
    /// IDENTISCHEM Seed (a) dieselbe Gesamt-Besuchszahl an der Wurzel
    /// liefern (Sim-Buchhaltung unveraendert, siehe
    /// `batched_expand_root_candidates`-Doku), (b) pro Wurzelkind dieselbe
    /// Besuchszahl (Kontrollfluss/RNG bis zur Kandidatenauswahl ist in
    /// beiden Pfaden identischer Code, siehe Kommentar an der Aufrufstelle)
    /// und (c) dieselben Q-Werte wie der unbatchte Pfad liefern.
    ///
    /// GEMESSENES ERGEBNIS (2026-08-02, gegen `v19_2d_best` UND zusaetzlich
    /// gegen ein flaches Modell `v18_best` von Hand geprueft, sims=400,
    /// m_prime=16): root_q UND alle 16 Wurzelkind-Q-Werte sind
    /// BIT-IDENTISCH (`f64::to_bits()`-Vergleich, nicht nur "innerhalb
    /// Toleranz") zwischen batched und unbatcht -- kein messbarer
    /// Gleitkomma-Summationsreihenfolge-Effekt in der Praxis, obwohl
    /// theoretisch moeglich (siehe `BATCH_ROOT_EXPANSION`-Doku). Die
    /// Toleranz unten (1e-4) bleibt trotzdem als Sicherheitsmarge stehen
    /// (kein Anspruch auf Bit-Identitaet ueber alle Hardware-/tract-
    /// Versionen hinweg, gleiches Vorsichtsprinzip wie
    /// `net::eval_pair_matches_two_single_evals`s 1e-5) -- der eigentliche
    /// Befund (bit-identisch HEUTE) gehoert in den Auftragsbericht, nicht in
    /// eine ueberscharfe Assertion, die auf einer anderen Maschine flackern
    /// koennte.
    #[test]
    fn batched_root_expansion_matches_sequential_within_tolerance() {
        let Some(net) = load_batching_test_net() else { return };
        let mut state_rng = StdRng::seed_from_u64(2026_08_02);
        let Some(state) = random_drafting_state(1, 0, &mut state_rng) else {
            panic!("random_drafting_state(steps=0) sollte immer den frischen Runde-1-Zustand liefern");
        };

        let sims = 400u32; // Produktions-Standard -- ergibt m_prime=GUMBEL_TOP_M=16, deckt den vollen eval_batch-Bereich ab.
        let mut rng_unbatched = StdRng::seed_from_u64(555_555);
        let nodes_unbatched =
            build_gumbel_tree_inner(&net, None, &state, sims, false, &mut rng_unbatched, None, false);
        let mut rng_batched = StdRng::seed_from_u64(555_555);
        let nodes_batched =
            build_gumbel_tree_inner(&net, None, &state, sims, false, &mut rng_batched, None, true);

        assert_eq!(
            nodes_unbatched[0].visits, nodes_batched[0].visits,
            "Gesamtbesuchszahl an der Wurzel muss identisch sein (gleiche Sim-Buchhaltung)"
        );
        let root_q_u = nodes_unbatched[0].value / (nodes_unbatched[0].visits.max(1) as f64);
        let root_q_b = nodes_batched[0].value / (nodes_batched[0].visits.max(1) as f64);
        assert!(
            (root_q_u - root_q_b).abs() < 1e-4,
            "root_q weicht zu stark ab: unbatcht={root_q_u} batched={root_q_b}"
        );

        let stats_u = root_child_stats_from_nodes(&nodes_unbatched);
        let stats_b = root_child_stats_from_nodes(&nodes_batched);
        assert_eq!(stats_u.len(), stats_b.len(), "gleiche Anzahl besuchter Wurzelkinder erwartet");
        // Nach der Aktion selbst abgeglichen (nicht nach Position): die
        // Kandidaten-EXPANSIONSREIHENFOLGE ist identisch (siehe oben), aber
        // `nodes[0].children`s finale Reihenfolge unterscheidet sich
        // zwischen "alle Kandidaten zuerst" (batched) und "je Kandidat
        // interleaved mit seinen Tiefenbesuchen" (unbatcht).
        let map_b: std::collections::HashMap<String, (u32, f64)> =
            stats_b.iter().map(|(a, v, q)| (format!("{a:?}"), (*v, *q))).collect();
        let mut total_visits_u = 0u32;
        let mut total_visits_b_matched = 0u32;
        for (a, v_u, q_u) in &stats_u {
            total_visits_u += v_u;
            let key = format!("{a:?}");
            let (v_b, q_b) = *map_b.get(&key).unwrap_or(&(0, 0.0));
            assert_eq!(*v_u, v_b, "Besuchszahl fuer Aktion {key} weicht ab");
            total_visits_b_matched += v_b;
            if *v_u > 0 {
                assert!(
                    (q_u - q_b).abs() < 1e-4,
                    "Q fuer Aktion {key} weicht zu stark ab: unbatcht={q_u} batched={q_b}"
                );
            }
        }
        assert_eq!(total_visits_u, total_visits_b_matched, "Summe der Kind-Besuche muss uebereinstimmen");
    }

    /// Interleavte Latenz-Nachmessung `BATCH_ROOT_EXPANSION` an/aus (Perf-
    /// Auftrag 2026-08-02, Deliverable 4), direkt ueber
    /// `build_gumbel_tree_inner` (umgeht die Compile-Zeit-Konstante, siehe
    /// deren Doku) statt zweier getrennter Prozesslaeufe mit manuellem
    /// Konstanten-Umschalten -- INTERLEAVED innerhalb DESSELBEN Prozesses
    /// haelt Lastschwankungen (auf dieser Maschine liefen beim ersten Lauf
    /// parallel die PCR-A/B-Kampagnen) beiderseits gleich, macht das
    /// VERHAELTNIS robust (gleiches Messdesign-Prinzip wie
    /// `examples/latency_2d_vs_flat.rs`). Gemessenes Ergebnis (2026-08-02,
    /// `v19_2d_best`, sims=400, n=60, unter erheblicher Fremdlast durch die
    /// PCR-Kampagnen -- absolute Zeiten dadurch stark aufgeblaeht, ~750ms
    /// statt der ~2-4ms einer unbelasteten Maschine, aber das VERHAELTNIS
    /// bleibt aussagekraeftig): `ratio(on/off) ≈ 1.01` -- KEIN messbarer
    /// Geschwindigkeitsgewinn (siehe Auftragsbericht fuer die Einordnung:
    /// die gebuendelten `m_prime<=16` Erstexpansionen sind nur ein kleiner
    /// Bruchteil der insgesamt `sims` Netz-Aufrufe pro Zug).
    /// `#[ignore]`: kein Teil des normalen `cargo test`-Laufs (reine
    /// Zeitmessung, kein Korrektheits-Test -- der ist
    /// `batched_root_expansion_matches_sequential_within_tolerance` oben),
    /// manuell via `cargo test --release batch_root_expansion_latency_bench
    /// -- --ignored --nocapture` startbar, z.B. fuer eine Nachmessung ohne
    /// Fremdlast.
    #[test]
    #[ignore]
    fn batch_root_expansion_latency_bench() {
        let Some(net) = load_batching_test_net() else { return };
        let mut state_rng = StdRng::seed_from_u64(2026_08_02);
        let Some(state) = random_drafting_state(1, 0, &mut state_rng) else {
            panic!("random_drafting_state(steps=0) sollte immer den frischen Runde-1-Zustand liefern");
        };
        let sims = 400u32;
        const WARMUP: usize = 5;
        const RUNS: usize = 60;

        for i in 0..WARMUP {
            let mut rng = StdRng::seed_from_u64(i as u64);
            let _ = build_gumbel_tree_inner(&net, None, &state, sims, false, &mut rng, None, false);
            let _ = build_gumbel_tree_inner(&net, None, &state, sims, false, &mut rng, None, true);
        }

        let mut times_off = Vec::with_capacity(RUNS);
        let mut times_on = Vec::with_capacity(RUNS);
        for i in 0..RUNS {
            let mut rng_off = StdRng::seed_from_u64(1000 + i as u64);
            let t = std::time::Instant::now();
            let _ = build_gumbel_tree_inner(&net, None, &state, sims, false, &mut rng_off, None, false);
            times_off.push(t.elapsed().as_secs_f64() * 1000.0);

            let mut rng_on = StdRng::seed_from_u64(1000 + i as u64);
            let t = std::time::Instant::now();
            let _ = build_gumbel_tree_inner(&net, None, &state, sims, false, &mut rng_on, None, true);
            times_on.push(t.elapsed().as_secs_f64() * 1000.0);
        }
        let median = |v: &mut Vec<f64>| -> f64 {
            v.sort_by(|a, b| a.partial_cmp(b).unwrap());
            v[v.len() / 2]
        };
        let m_off = median(&mut times_off.clone());
        let m_on = median(&mut times_on.clone());
        eprintln!(
            "BATCH_ROOT_EXPANSION off med={m_off:.3}ms  on med={m_on:.3}ms  ratio(on/off)={:.3}  n={RUNS} sims={sims}",
            m_on / m_off
        );
    }

    #[test]
    fn build_determinized_forest_with_n_equals_1_matches_single_tree_stats_and_policy() {
        // (a) NUM_DETERMINIZATIONS<=1 ist byte-identisch zum Alt-Verhalten --
        // die drei Produktions-Einstiege routen bei <=1 zwar NICHT durch die
        // Forest-/Aggregations-Maschinerie (siehe deren Code, bewusst
        // unveraendert), aber selbst WENN man `build_determinized_forest`
        // mit n=1 aufruft, muss das aggregierte Ergebnis exakt dem direkten
        // `build_net_tree`-Aufruf mit identischem RNG-Seed entsprechen --
        // Sicherheitsnetz, falls ein zukuenftiges Refactoring den
        // <=1-Sonderfall an den Aufrufstellen versehentlich entfernt.
        let Some(net) = load_test_net() else { return };
        let mut rng_state = StdRng::seed_from_u64(777);
        let state = random_drafting_state(1, 10, &mut rng_state).expect("Testzustand sollte auswertbar sein");

        let mut rng_a = StdRng::seed_from_u64(999);
        let nodes = build_net_tree(&net, None, &state, 8, DEFAULT_C_PUCT, false, &mut rng_a, None, None);
        let direct_stats = root_child_stats_from_nodes(&nodes);
        let direct_policy = root_completed_q_policy(&nodes);

        let mut rng_b = StdRng::seed_from_u64(999);
        let forest = build_determinized_forest(&net, None, &state, 8, DEFAULT_C_PUCT, false, 1, &mut rng_b);
        assert_eq!(forest.len(), 1, "n=1 sollte genau einen Baum liefern");
        let forest_stats = aggregate_root_child_stats(&forest);
        let forest_policy = average_completed_q_policy(&forest);

        assert_eq!(direct_stats.len(), forest_stats.len());
        for ((a1, v1, q1), (a2, v2, q2)) in direct_stats.iter().zip(forest_stats.iter()) {
            assert_eq!(a1, a2, "Aktionsreihenfolge muss uebereinstimmen");
            assert_eq!(v1, v2, "Besuche muessen bei n=1 identisch sein");
            assert!((q1 - q2).abs() < 1e-12, "Q muss bei n=1 identisch sein: {q1} vs {q2}");
        }
        assert_eq!(direct_policy.len(), forest_policy.len());
        for ((a1, p1), (a2, p2)) in direct_policy.iter().zip(forest_policy.iter()) {
            assert_eq!(a1, a2, "Aktionsreihenfolge muss uebereinstimmen");
            assert!((p1 - p2).abs() < 1e-9, "completed-Q-Politik muss bei n=1 identisch sein: {p1} vs {p2}");
        }
    }

    #[test]
    fn build_determinized_forest_draws_three_different_determinizations_at_n_equals_3() {
        // (b) Kernanforderung Task #65: bei n=3 muessen drei GENUIN
        // unterschiedliche Determinisierungen gezogen werden (nicht dieselbe
        // Welt dreimal) -- `dome_tile_pool`-Reihenfolge NACH der Wurzel-
        // Determinisierung ist der direkteste Zeuge dafuer (siehe
        // `determinize_hidden_information`, `DETERMINIZE_ROOT_HIDDEN_INFO`
        // ist Standard `true`). Gleicher RNG-Strom (ein einziges `rng`,
        // wie `build_determinized_forest` es an `build_net_tree` weiterreicht)
        // muss trotzdem drei verschiedene Ziehungen liefern.
        let Some(net) = load_test_net() else { return };
        let mut rng = StdRng::seed_from_u64(2468);
        let state = random_drafting_state(2, 10, &mut rng).expect("Testzustand sollte auswertbar sein");
        assert!(
            state.dome_tile_pool.len() >= 3,
            "Testvoraussetzung: genug Platten im verdeckten Stapel fuer eine aussagekraeftige Mischung"
        );

        let forest = build_determinized_forest(&net, None, &state, 6, DEFAULT_C_PUCT, false, 3, &mut rng);
        assert_eq!(forest.len(), 3);
        let pools: Vec<Vec<usize>> = forest
            .iter()
            .map(|nodes| nodes[0].state.dome_tile_pool.iter().map(|t| t.tile_id).collect())
            .collect();
        assert_ne!(pools[0], pools[1], "Welt 1 und 2 sollten unterschiedliche dome_tile_pool-Reihenfolgen ziehen");
        assert_ne!(pools[1], pools[2], "Welt 2 und 3 sollten unterschiedliche dome_tile_pool-Reihenfolgen ziehen");
        assert_ne!(pools[0], pools[2], "Welt 1 und 3 sollten unterschiedliche dome_tile_pool-Reihenfolgen ziehen");
    }

    #[test]
    fn hybrid_search_with_equal_nets_matches_plain_search() {
        // Task #88 (Hybrid-Suche, kausaler Kopf-Test) -- WICHTIGSTER Korrekt-
        // heitstest fuer den neuen Hybrid-Codepfad: `net_policy` UND `net_value`
        // als DIESELBE Referenz muss den `same_net`-Kurzschluss in `make_node`
        // greifen lassen (siehe dortiger Kommentar) -- das Ergebnis muss dann
        // BYTE-IDENTISCH zur normalen (Nicht-Hybrid) Suche sein, sonst haette
        // jede kuenftige 2x2-Messung keinen sauberen A=B-Referenzpunkt. Prueft
        // volle Wurzel-Statistik (Besuche, Q), completed-Q-Politik UND die
        // finale Zugwahl, ueber mehrere zufaellige Stellungen und Sims-Budgets.
        let Some(net) = load_test_net() else { return };
        let mut setup_rng = StdRng::seed_from_u64(4242);
        let mut checked = 0;
        for gi in 0..6u64 {
            let Some(state) = random_drafting_state(gi, 12, &mut setup_rng) else { continue };
            for &sims in &[8u32, 24] {
                let mut rng_plain = StdRng::seed_from_u64(1000 + gi);
                let nodes_plain =
                    build_net_tree(&net, None, &state, sims, DEFAULT_C_PUCT, false, &mut rng_plain, None, None);
                let stats_plain = root_child_stats_from_nodes(&nodes_plain);
                let policy_plain = root_completed_q_policy(&nodes_plain);
                let action_plain =
                    select_final_root_child(&nodes_plain).and_then(|i| nodes_plain[i].action.clone());

                let mut rng_hybrid = StdRng::seed_from_u64(1000 + gi);
                let nodes_hybrid = build_net_tree(
                    &net,
                    Some(&net),
                    &state,
                    sims,
                    DEFAULT_C_PUCT,
                    false,
                    &mut rng_hybrid,
                    None,
                    None,
                );
                let stats_hybrid = root_child_stats_from_nodes(&nodes_hybrid);
                let policy_hybrid = root_completed_q_policy(&nodes_hybrid);
                let action_hybrid =
                    select_final_root_child(&nodes_hybrid).and_then(|i| nodes_hybrid[i].action.clone());

                assert_eq!(
                    nodes_plain.len(),
                    nodes_hybrid.len(),
                    "Spiel {gi} sims={sims}: Baumgroesse weicht ab"
                );
                assert_eq!(stats_plain.len(), stats_hybrid.len());
                for ((a1, v1, q1), (a2, v2, q2)) in stats_plain.iter().zip(stats_hybrid.iter()) {
                    assert_eq!(a1, a2, "Spiel {gi} sims={sims}: Aktionsreihenfolge weicht ab");
                    assert_eq!(v1, v2, "Spiel {gi} sims={sims}: Besuche weichen ab (A={a1:?})");
                    assert_eq!(
                        q1, q2,
                        "Spiel {gi} sims={sims}: Q nicht byte-identisch (A={a1:?}): {q1} vs {q2}"
                    );
                }
                assert_eq!(policy_plain.len(), policy_hybrid.len());
                for ((a1, p1), (a2, p2)) in policy_plain.iter().zip(policy_hybrid.iter()) {
                    assert_eq!(a1, a2, "Spiel {gi} sims={sims}: Policy-Aktionsreihenfolge weicht ab");
                    assert_eq!(
                        p1, p2,
                        "Spiel {gi} sims={sims}: completed-Q-Politik nicht byte-identisch (A={a1:?}): {p1} vs {p2}"
                    );
                }
                assert_eq!(action_plain, action_hybrid, "Spiel {gi} sims={sims}: finale Zugwahl weicht ab");
                checked += 1;
            }
        }
        assert!(checked >= 6, "zu wenige auswertbare Stichproben ({checked}) -- Testaufbau pruefen");
    }

    #[test]
    fn gumbel_trace_collection_does_not_change_search() {
        // Task #95 (Anforderung 3) -- WICHTIGSTER Korrektheitstest fuer den
        // neuen Debug-Trace: `collect_trace=true` (also `trace=Some(..)` an
        // `build_gumbel_tree`) darf die eigentliche Suche NICHT veraendern --
        // gleicher RNG-Seed muss exakt denselben Baum (Groesse, Besuche, Q je
        // Knoten) UND dieselbe finale Zugwahl liefern wie `trace=None`.
        // Gleiches Muster wie `hybrid_search_with_equal_nets_matches_plain_search`
        // (A=B-Referenzpunkt fuer einen additiven Codepfad).
        let Some(net) = load_test_net() else { return };
        let mut setup_rng = StdRng::seed_from_u64(9595);
        let mut checked = 0;
        for gi in 0..6u64 {
            let Some(state) = random_drafting_state(gi, 12, &mut setup_rng) else { continue };
            for &sims in &[8u32, 24] {
                let mut rng_plain = StdRng::seed_from_u64(2000 + gi);
                let nodes_plain =
                    build_net_tree(&net, None, &state, sims, DEFAULT_C_PUCT, false, &mut rng_plain, None, None);

                let mut rng_traced = StdRng::seed_from_u64(2000 + gi);
                let mut trace = GumbelTrace::default();
                let nodes_traced = build_net_tree(
                    &net,
                    None,
                    &state,
                    sims,
                    DEFAULT_C_PUCT,
                    false,
                    &mut rng_traced,
                    None,
                    Some(&mut trace),
                );

                assert_eq!(
                    nodes_plain.len(),
                    nodes_traced.len(),
                    "Spiel {gi} sims={sims}: Baumgroesse weicht ab, obwohl nur Trace-Sammlung aktiviert wurde"
                );
                for (np, nt) in nodes_plain.iter().zip(nodes_traced.iter()) {
                    assert_eq!(np.visits, nt.visits, "Spiel {gi} sims={sims}: Besuchszahl weicht ab");
                    assert_eq!(np.value, nt.value, "Spiel {gi} sims={sims}: akkumulierter Wert weicht ab");
                    assert_eq!(np.action, nt.action, "Spiel {gi} sims={sims}: Knoten-Aktion weicht ab");
                    assert_eq!(np.prior, nt.prior, "Spiel {gi} sims={sims}: Prior weicht ab");
                }
                let action_plain =
                    select_final_root_child(&nodes_plain).and_then(|i| nodes_plain[i].action.clone());
                let action_traced =
                    select_final_root_child(&nodes_traced).and_then(|i| nodes_traced[i].action.clone());
                assert_eq!(action_plain, action_traced, "Spiel {gi} sims={sims}: finale Zugwahl weicht ab");

                // Trace selbst muss sinnvoll befuellt sein (sonst waere der
                // Paritaetstest trivial, weil gar kein Trace-Code lief).
                assert!(!trace.top_m.is_empty(), "Spiel {gi} sims={sims}: Top-m-Trace ist leer");
                assert!(!trace.finalists.is_empty(), "Spiel {gi} sims={sims}: Finalisten-Trace ist leer");
                assert!(trace.root_value.is_some(), "Spiel {gi} sims={sims}: Root-Value-Debug fehlt");

                checked += 1;
            }
        }
        assert!(checked >= 6, "zu wenige auswertbare Stichproben ({checked}) -- Testaufbau pruefen");
    }

    #[test]
    fn net_leaf_eval_is_invariant_to_which_player_is_flagged_current() {
        // Kernbehauptung des Kollegen-Verdachts (Perspektivfehler): flippt man
        // NUR `current_player` an einem ansonsten identischen Zustand, MUSS
        // `net_leaf_eval` (das intern ohnehin beide Perspektiven per zwei
        // Forward-Pässen auswertet und fest auf [Spieler0, Spieler1] einsortiert)
        // exakt dasselbe Ergebnis liefern -- unabhaengig davon, wer gerade
        // "current_player" ist. Ein Perspektiv-/Plumbing-Bug wuerde diese
        // Invariante brechen.
        let Some(net) = load_test_net() else { return };
        let mut rng = StdRng::seed_from_u64(2026);
        let mut checked = 0;
        for gi in 0..10u64 {
            let Some(state) = random_drafting_state(gi, 15, &mut rng) else { continue };
            let mut flipped = state.clone();
            flipped.current_player = 1 - flipped.current_player;
            let a = net_leaf_eval(&net, &state);
            let b = net_leaf_eval(&net, &flipped);
            assert!(
                (a[0] - b[0]).abs() < 1e-9 && (a[1] - b[1]).abs() < 1e-9,
                "Spiel {gi}: net_leaf_eval haengt faelschlich von state.current_player ab -- a={a:?} b={b:?}"
            );
            checked += 1;
        }
        assert!(checked >= 5, "zu wenige auswertbare Stichproben ({checked}) -- Testaufbau pruefen");
    }

    #[test]
    fn net_leaf_eval_sign_mostly_agrees_with_exact_dfs_ground_truth() {
        // "Terminalnahe Zustaende mit bekanntem Sieger" (Kollegen-Vorschlag)
        // verallgemeinert: `mcts::evaluate` ist an JEDEM Drafting-Zustand ein
        // exaktes Ground-Truth-Urteil (Rundenscore + Wertungsplatten-
        // Fortschritt, dieselbe Grundlage wie das Runde-5-Alpha-Beta). Prueft
        // NICHT Genauigkeit (die ist bekanntermassen schwach, siehe Runde-1-R²
        // in STATUS.md) -- nur, ob das Netz MEHRHEITLICH auf der richtigen
        // Seite der 50%-Linie liegt. Ein echter Perspektivfehler wuerde die
        // Uebereinstimmungsrate weit unter 50% druecken (systematische
        // Umkehrung), reines Value-Rauschen bleibt darueber.
        let Some(net) = load_test_net() else { return };
        let mut rng = StdRng::seed_from_u64(4242);
        let (mut agree, mut total) = (0usize, 0usize);
        for gi in 0..40u64 {
            let Some(state) = random_drafting_state(gi, 25, &mut rng) else { continue };
            let net_vals = net_leaf_eval(&net, &state);
            let dfs_vals = crate::mcts::evaluate(&state, 0);
            // Nur werten, wenn beide Seiten ueberhaupt eine Praeferenz zeigen --
            // bei einem Gleichstand ist "Vorzeichen" nicht definiert.
            if (net_vals[0] - net_vals[1]).abs() < 1e-6 || (dfs_vals[0] - dfs_vals[1]).abs() < 1e-6 {
                continue;
            }
            total += 1;
            if (net_vals[0] > net_vals[1]) == (dfs_vals[0] > dfs_vals[1]) {
                agree += 1;
            }
        }
        assert!(total >= 10, "zu wenige auswertbare Stichproben ({total}) -- Testaufbau pruefen");
        let rate = agree as f64 / total as f64;
        eprintln!("  ℹ️  Vorzeichen-Uebereinstimmung Netz vs. DFS: {:.1}% ({agree}/{total})", rate * 100.0);
        assert!(
            rate > 0.5,
            "Vorzeichen-Uebereinstimmung Netz vs. exaktem DFS nur {:.0}% ({agree}/{total}) -- \
             das ist nicht besser als Zufall und deutet auf einen Perspektivfehler hin, nicht nur \
             auf gewöhnliches Value-Rauschen",
            rate * 100.0
        );
    }

    // ── Task #78 (v12c Value-Shrinkage, Platzhalter-Kalibrierung) ───────────

    #[test]
    fn value_shrink_per_round_table_is_monotone_and_normalized() {
        assert_eq!(VALUE_SHRINK_PER_ROUND.len(), 5);
        for w in VALUE_SHRINK_PER_ROUND.iter() {
            assert!(*w > 0.0 && *w <= 1.0, "Gewicht ausserhalb (0,1]: {w}");
        }
        for pair in VALUE_SHRINK_PER_ROUND.windows(2) {
            assert!(
                pair[1] >= pair[0] - 1e-12,
                "Tabelle muss monoton nicht-fallend sein: {:?}",
                VALUE_SHRINK_PER_ROUND
            );
        }
        assert!(
            (VALUE_SHRINK_PER_ROUND[4] - 1.0).abs() < 1e-9,
            "Runde 5 muss auf 1.0 normiert sein (keine Daempfung in der letzten Runde)"
        );
        assert!(
            VALUE_SHRINK_PER_ROUND[0] < VALUE_SHRINK_PER_ROUND[4],
            "Runde 1 muss strikt kleiner sein als Runde 5"
        );
    }

    #[test]
    fn value_shrink_weight_maps_round_number_and_clamps_out_of_range() {
        assert_eq!(value_shrink_weight(1), VALUE_SHRINK_PER_ROUND[0]);
        assert_eq!(value_shrink_weight(2), VALUE_SHRINK_PER_ROUND[1]);
        assert_eq!(value_shrink_weight(5), VALUE_SHRINK_PER_ROUND[4]);
        // Verteidigung: Runde 0 oder >5 sollte in der Praxis nie vorkommen,
        // klemmt aber statt zu paniken.
        assert_eq!(value_shrink_weight(0), VALUE_SHRINK_PER_ROUND[0]);
        assert_eq!(value_shrink_weight(99), VALUE_SHRINK_PER_ROUND[4]);
    }

    #[test]
    fn apply_value_shrink_matches_current_toggle_state() {
        // Task #78, robust gegen den A/B-Toggle-Flip (2026-07-23): dieser Test
        // muss bei `VALUE_SHRINK_ENABLED=false` UND `=true` gruen bleiben --
        // waehrend des Phase-B-Nachweislaufs wird die Konstante temporaer auf
        // `true` gesetzt (`cargo test --release` muss dabei gruen bleiben,
        // siehe `evaluations/STATUS.md` "v12c"-Abschnitt), danach je nach
        // Ergebnis wieder zurueckgesetzt. Bei AUS: reine Identitaet (byte-
        // identisch zum Vor-Task-#78-Verhalten). Bei AN: Runde 5 bleibt
        // Identitaet (w_5=1.0 per Normierung), fruehere Runden werden
        // sichtbar Richtung 0.5 gezogen.
        let v = [0.9, 0.05];
        if VALUE_SHRINK_ENABLED {
            assert_ne!(apply_value_shrink(v, 1), v, "bei AN muss Runde 1 sichtbar geschrumpft werden");
            let r5 = apply_value_shrink(v, 5);
            assert!(
                (r5[0] - v[0]).abs() < 1e-9 && (r5[1] - v[1]).abs() < 1e-9,
                "Runde 5 bleibt (bis auf Gleitkomma-Rauschen) Identitaet (w_5=1.0): {r5:?} vs {v:?}"
            );
        } else {
            assert_eq!(apply_value_shrink(v, 1), v);
            assert_eq!(apply_value_shrink(v, 5), v);
            assert_eq!(apply_value_shrink([0.0, 1.0], 3), [0.0, 1.0]);
        }
    }

    #[test]
    fn round1_weight_pulls_harder_toward_half_than_round5_weight() {
        // Direkter Formel-Test (unabhaengig vom ENABLED-Toggle): mit Runde-1-
        // Gewicht muss der geschrumpfte Wert naeher an 0.5 liegen als mit
        // Runde-5-Gewicht, fuer denselben Rohwert.
        let w1 = value_shrink_weight(1);
        let w5 = value_shrink_weight(5);
        for v in [0.9, 0.1, 0.99, 0.55] {
            let shrunk1 = 0.5 + w1 * (v - 0.5);
            let shrunk5 = 0.5 + w5 * (v - 0.5);
            assert!(
                (shrunk1 - 0.5).abs() < (shrunk5 - 0.5).abs(),
                "v={v}: Runde 1 (w={w1}, ->{shrunk1}) sollte staerker Richtung 0.5 \
                 gezogen werden als Runde 5 (w={w5}, ->{shrunk5})"
            );
        }
    }

    #[test]
    fn floor_shaping_additive_is_unaffected_by_shrink_when_applied_after_it() {
        // Konstruierter Vergleich (Task #78): reproduziert exakt die
        // Reihenfolge aus `make_node` -- `apply_value_shrink` (echte
        // Produktionsfunktion) laeuft VOR dem Floor-Additiv. Das reine
        // Floor-Signal (hier durch einen repraesentativen `floor_shift`-Wert
        // ersetzt, wie ihn `floor_shaping_delta(&state).tanh() *
        // FLOOR_SHAPING_WEIGHT` liefern wuerde) darf durch den Shrink-Schritt
        // NICHT gedaempft werden, weil es danach unveraendert additiv
        // aufaddiert wird -- Kontrast zur (falschen) umgekehrten Reihenfolge.
        let base = [0.5f64, 0.5f64]; // neutraler Netz-Rohwert vor Floor-Korrektur
        let floor_shift = 0.12;
        let round1_w = value_shrink_weight(1); // staerkster Schrumpf-Fall, Worst-Case

        // Richtige Reihenfolge (wie in make_node): erst schrumpfen (hier
        // manuell mit dem Runde-1-Gewicht erzwungen, unabhaengig vom
        // ENABLED-Toggle, um die Formel selbst zu pruefen), dann Floor addieren.
        let shrunk_base = [0.5 + round1_w * (base[0] - 0.5), 0.5 + round1_w * (base[1] - 0.5)];
        let correct_order = [
            (shrunk_base[0] + floor_shift).clamp(0.0, 1.0),
            (shrunk_base[1] - floor_shift).clamp(0.0, 1.0),
        ];
        assert!(
            (correct_order[0] - shrunk_base[0] - floor_shift).abs() < 1e-9,
            "Floor-Beitrag muss exakt +floor_shift bleiben, unabhaengig vom Schrumpfgewicht"
        );
        assert!(
            (correct_order[1] - shrunk_base[1] + floor_shift).abs() < 1e-9,
            "Floor-Beitrag muss exakt -floor_shift bleiben, unabhaengig vom Schrumpfgewicht"
        );

        // Kontrast: die (falsche) umgekehrte Reihenfolge -- erst Floor
        // addieren, DANACH schrumpfen -- wuerde das exakte Floor-Signal
        // sichtbar daempfen. Zeigt, warum die gewaehlte Reihenfolge wichtig ist.
        let wrong_order_p0 = 0.5 + round1_w * ((base[0] + floor_shift).clamp(0.0, 1.0) - 0.5);
        let wrong_order_contribution = wrong_order_p0 - (0.5 + round1_w * (base[0] - 0.5));
        assert!(
            wrong_order_contribution.abs() < floor_shift - 1e-9,
            "Erwartete Daempfung bei falscher Reihenfolge (Floor vor Shrink) nicht beobachtet -- \
             Testannahme pruefen"
        );
    }

    // ── Wertungsplatten-Shaping (Task #93) ──────────────────────────────────

    #[test]
    fn plate_shaping_delta_matches_wertung_progress_difference() {
        // Direkter Formel-Test: `plate_shaping_delta` muss exakt der (skalierten)
        // Differenz der stetigen Wertungsplatten-Fortschritts-Heuristik
        // entsprechen, die `mcts.rs::player_total` schon lange fuer die
        // DFS-Blattbewertung nutzt -- keine eigene Neuimplementierung, reine
        // Wiederverwendung.
        let mut rng = StdRng::seed_from_u64(93);
        let mut checked = 0;
        for gi in 0..8u64 {
            let Some(state) = random_drafting_state(gi, 14, &mut rng) else { continue };
            let expected = (wertung_progress(&state.players[0], &state.scoring_tile_ids)
                - wertung_progress(&state.players[1], &state.scoring_tile_ids))
                / PLATE_SHAPING_SCALE;
            assert!(
                (plate_shaping_delta(&state) - expected).abs() < 1e-12,
                "Spiel {gi}: plate_shaping_delta weicht von der erwarteten Formel ab"
            );
            checked += 1;
        }
        assert!(checked >= 4, "zu wenige auswertbare Stichproben ({checked}) -- Testaufbau pruefen");
    }

    #[test]
    fn plate_shaping_disabled_is_exact_identity() {
        // Kern-Paritätstest (Task #93): bei `PLATE_SHAPING_ENABLED=false`
        // (Standard) muss `apply_plate_shaping` die Eingabe UNVERÄNDERT
        // zurückgeben -- der Additiv-Block wird komplett übersprungen (siehe
        // Funktionskommentar), nicht nur numerisch neutralisiert. Geprüft über
        // mehrere reale Stellungen (unterschiedliche Plattenfortschritte) UND
        // synthetische Extremwerte, damit auch ein grosses `plate_shaping_delta`
        // bei ENABLED=false garantiert folgenlos bleibt.
        let mut rng = StdRng::seed_from_u64(931);
        let mut checked = 0;
        for gi in 0..8u64 {
            let Some(state) = random_drafting_state(gi, 16, &mut rng) else { continue };
            for v in [[0.5f64, 0.5f64], [0.9, 0.2], [0.0, 1.0], [1.0, 0.0]] {
                let out = apply_plate_shaping(v, &state, None);
                if PLATE_SHAPING_ENABLED {
                    // Falls der Toggle (Mess-Wheel-Arm) aktiv ist, muss das
                    // Ergebnis weiterhin ein gueltiges [0,1]-Paar bleiben.
                    assert!(out[0].is_finite() && (0.0..=1.0).contains(&out[0]));
                    assert!(out[1].is_finite() && (0.0..=1.0).contains(&out[1]));
                } else {
                    assert_eq!(
                        out, v,
                        "Spiel {gi}: PLATE_SHAPING_ENABLED=false muss byte-identisch zur \
                         Eingabe bleiben (v={v:?})"
                    );
                }
            }
            checked += 1;
        }
        assert!(checked >= 4, "zu wenige auswertbare Stichproben ({checked}) -- Testaufbau pruefen");
    }

    #[test]
    fn plate_shaping_marginal_isolates_parent_baseline() {
        // Marginal-Delta-Fix (Task #8, 2026-07-27): `plate_shaping_marginal`
        // muss GENAU `plate_shaping_delta(state) - plate_shaping_delta(parent)`
        // sein -- unabhaengig davon, wie GROSS die gemeinsame Baseline ist
        // (das war der Kern des Fixes: die alte Version wandte tanh auf den
        // ABSOLUTEN Wert an, wo eine grosse gemeinsame Baseline die kleine
        // Geschwister-Differenz via tanh'(baseline)->0 daempfte). Kein
        // Elternknoten (Wurzel) -> exakt 0.0.
        let mut rng = StdRng::seed_from_u64(834);
        let mut checked = 0;
        for gi in 0..8u64 {
            let Some(parent) = random_drafting_state(gi, 10, &mut rng) else { continue };
            let Some(child) = random_drafting_state(gi + 100, 11, &mut rng) else { continue };
            let expected = plate_shaping_delta(&child) - plate_shaping_delta(&parent);
            assert!(
                (plate_shaping_marginal(&child, Some(&parent)) - expected).abs() < 1e-12,
                "Spiel {gi}: marginal weicht von delta(child)-delta(parent) ab"
            );
            assert_eq!(
                plate_shaping_marginal(&child, None),
                0.0,
                "Spiel {gi}: ohne Elternknoten (Wurzel) muss marginal exakt 0 sein"
            );
            checked += 1;
        }
        assert!(checked >= 4, "zu wenige auswertbare Stichproben ({checked}) -- Testaufbau pruefen");
    }

    #[test]
    fn plate_shaping_disabled_search_matches_pre_task93_tree() {
        // End-zu-Ende-Parität auf Baum-Ebene: solange `PLATE_SHAPING_ENABLED`
        // (Standard) `false` ist, muss `build_net_tree` exakt dieselben
        // Wurzel-Statistiken/Politik/Zugwahl liefern wie vor Task #93 -- da
        // `apply_plate_shaping` bei ENABLED=false reine Identität ist (siehe
        // `plate_shaping_disabled_is_exact_identity`), reicht hier der
        // Determinismus-Nachweis: zwei Läufe mit identischem Seed müssen
        // uebereinstimmen. Bei aktivem Mess-Wheel-Arm (`ENABLED=true`, temporär
        // fürs A/B) ist dieser Test KEIN Paritätsnachweis mehr -- übersprungen
        // statt fehlzuschlagen, damit `cargo test --release` in BEIDEN
        // Toggle-Zuständen grün bleibt (Konvention wie `apply_value_shrink`s
        // Tests, die ebenfalls beide Zustände vertragen statt nur einen).
        if PLATE_SHAPING_ENABLED {
            eprintln!(
                "  ⚠️  PLATE_SHAPING_ENABLED=true (Mess-Wheel-Arm) -- \
                 Paritätstest übersprungen, kein Paritätsnachweis in diesem Zustand."
            );
            return;
        }
        let Some(net) = load_test_net() else { return };
        let mut setup_rng = StdRng::seed_from_u64(9300);
        let mut checked = 0;
        for gi in 0..4u64 {
            let Some(state) = random_drafting_state(gi, 12, &mut setup_rng) else { continue };
            let mut rng_a = StdRng::seed_from_u64(2000 + gi);
            let nodes_a = build_net_tree(&net, None, &state, 16, DEFAULT_C_PUCT, false, &mut rng_a, None, None);
            let stats_a = root_child_stats_from_nodes(&nodes_a);
            let policy_a = root_completed_q_policy(&nodes_a);

            let mut rng_b = StdRng::seed_from_u64(2000 + gi);
            let nodes_b = build_net_tree(&net, None, &state, 16, DEFAULT_C_PUCT, false, &mut rng_b, None, None);
            let stats_b = root_child_stats_from_nodes(&nodes_b);
            let policy_b = root_completed_q_policy(&nodes_b);

            assert_eq!(stats_a, stats_b, "Spiel {gi}: Wurzel-Statistiken nicht deterministisch/identisch");
            assert_eq!(policy_a, policy_b, "Spiel {gi}: completed-Q-Politik nicht deterministisch/identisch");
            checked += 1;
        }
        assert!(checked >= 4, "zu wenige auswertbare Stichproben ({checked}) -- Testaufbau pruefen");
    }
}
