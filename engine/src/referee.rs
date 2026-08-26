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
/// PER-ENTSCHEIDUNG-Protokoll (KERNBEWEIS-FIX par.8d, Koordinator-Zuschnitt
/// 2026-08-23, loest die fruehere ATOMARE Kuppel-Sonderbehandlung ab): diese
/// Funktion trifft GENAU EINE Drafting-Entscheidung -- was `drafting_actions`
/// fuer den uebergebenen Zustand als Kandidaten liefert (Stein-Zug, Kuppel-
/// Slot- ODER -Rotationswahl, Stapel-Peek, Stapel-Slot, Bonuschip, Pass),
/// keine Sonderbehandlung nach Aktionstyp. Steckt der Zustand mitten in einem
/// angefangenen Kuppel-/Stapel-Zug (`pending_dome_choice`/
/// `pending_stack_draw`), grenzt `drafting_actions` die Kandidaten von selbst
/// auf die Folgeschritte ein -- das setzt voraus, dass `state_json` diesen
/// Zwischenzustand exakt traegt (`serialize::state_to_json_exact`s fuenftes
/// Feld `pending_dome_choice_exact`, par.8d; `pending_stack_draw` war schon
/// vorher Teil der Basis-Serialisierung). Der Aufrufer (`RefereeGame` ueber
/// den Treiber in `tools/frozen_referee_match.py`) fragt deshalb fuer JEDEN
/// einzelnen Schritt eines mehrstufigen Zugs erneut an, jeweils mit einem
/// frischen `RefereeGame::pending_search_seed()` -- ein einziger, genereller
/// Mechanismus statt getrennter Pfade je Aktionstyp. `rot_seed` (par.8c) und
/// die atomare `rotation`-Anreicherung der Antwort (par.8a) entfallen damit
/// ERSATZLOS, nicht nur ungenutzt: der ZWEITE Parameter existierte nur, weil
/// die Rotationsstufe frueher IM SELBEN Aufruf mitentschieden wurde.
///
/// KERNBEWEIS-FIX FORK A (PREREG_agent_encapsulation.md par.8b,
/// Nutzer-Entscheid 2026-08-23): `state_json` traegt additiv die EXAKTEN
/// Reihenfolgen der verdeckten Sammlungen (Beutel/Turm/Kuppelstapel/
/// Bonuschip-Pool, `serialize::state_to_json_exact`, erzeugt von
/// `RefereeGame::state_json`). `json_to_state_exact` liest sie als
/// PFLICHTFELDER (harter Fehler bei Fehlen, kein stiller Rueckfall auf
/// Zaehler-Rekonstruktion). Der Such-RNG (`rng` unten) startet FRISCH aus
/// `seed` -- `seed` ist hier bereits `derive_search_seed(game_seed, steps)`
/// (siehe `RefereeGame::pending_search_seed`), also byte-identische
/// Ableitung zum In-Process-Pfad (`RefereeGame::
/// drafting_decide_and_apply_inprocess`, welcher `agent.decide()`
/// ebenfalls je EINZELNER Entscheidung mit genau diesem Seed-Muster aufruft,
/// `self_play.rs::unified_game_loop`).
/// Wie [`choose_drafting_action_json`], aber fuer eine NETZLOSE
/// Heuristik-Seite.
///
/// Notwendig fuer eingefrorene Heuristik-Artefakte: die haben kein ONNX, ihr
/// Verhalten steckt vollstaendig im Wheel. Der bestehende Worker-Pfad
/// verlangte ein Modell und war damit fuer sie verschlossen.
///
/// Ruft `self_play::heuristic_arena_choose_action` -- dieselbe Funktion, die
/// auch `HeuristicArenaAgent::decide` benutzt, keine zweite Auswahl-Logik
/// (gleiche Regel wie beim Netz-Gegenstueck oben).
///
/// Die Variante kommt aus der `SearchConfig` und damit aus der Spec des
/// Artefakts, NICHT aus einem Parameter des Aufrufers. Das ist der ganze
/// Punkt: am 2026-08-26 hat ein vom Aufrufer vergessenes
/// `--heuristik-variante` einen falschen Befund erzeugt. Ein Artefakt, das
/// sich selbst beschreibt, kann so nicht mehr falsch gespielt werden.
/// Waehlt einen Tiling-Schritt fuer einen extern gespeicherten Zustand --
/// mit der Variante aus der Spec.
///
/// Das ist die Haelfte, die der Referee bis 2026-08-26 selbst entschied, und
/// zwar ueber `resolve_tiling_step`, das auf `V1` verdrahtet ist. Fuer ein
/// Netz war das die richtige Abgrenzung; fuer eine Heuristik nicht -- der
/// v2-Durchbruch sitzt im Platzierungs-Routing.
///
/// `net`: optionales Tiling-Netz. Die v2-Vorzugskarte greift nur, wenn sie
/// einen Zug liefert; sonst faellt es auf den Bestandspfad durch, und DORT
/// entscheidet das Netz Gleichstaende (self_play.rs). Ein v2-Artefakt bringt
/// sein Netz deshalb selbst mit (`tiling_net.onnx`).
/// Waehlt eine Startsetzung fuer einen extern gespeicherten Zustand -- mit
/// der Variante aus der Spec.
///
/// `game_seed` ist Pflicht und kein Zufall: fuer v2-Varianten waehlt
/// `choose_start_placement_variante` unter mehreren Kandidaten SEED-BASIERT
/// aus. Ohne den Seed des Referees waere die Setzung eine andere als die, die
/// derselbe Agent in-process getroffen haette.
pub(crate) fn choose_start_placement_json(
    search_config: &SearchConfig,
    state_json: &str,
    pi: usize,
    game_seed: u64,
) -> PyResult<Value> {
    let parsed: Value = serde_json::from_str(state_json)
        .map_err(|e| PyValueError::new_err(format!("state_json: JSON-Parse-Fehler: {e}")))?;
    let state = crate::serialize::json_to_state_exact(&parsed).map_err(PyValueError::new_err)?;
    match crate::self_play::choose_start_placement_variante(
        &state, pi, search_config.heuristik_variante, game_seed,
    ) {
        Some((tid, r, c, rot)) => Ok(json!({"tile_id": tid, "row": r, "col": c, "rot": rot})),
        None => Err(PyValueError::new_err(
            "choose_start_placement_json: keine legale Startsetzung fuer diesen Zustand",
        )),
    }
}

pub(crate) fn choose_tiling_step_json(
    search_config: &SearchConfig,
    state_json: &str,
    net: Option<&Net>,
) -> PyResult<Value> {
    let parsed: Value = serde_json::from_str(state_json)
        .map_err(|e| PyValueError::new_err(format!("state_json: JSON-Parse-Fehler: {e}")))?;
    let state = crate::serialize::json_to_state_exact(&parsed).map_err(PyValueError::new_err)?;
    if state.phase != Phase::Tiling {
        return Err(PyValueError::new_err(
            "choose_tiling_step_json: state ist keine Tiling-Phase.",
        ));
    }
    let pi = state.current_player;
    let step = crate::self_play::resolve_tiling_step_variante(
        &state, pi, net, search_config.heuristik_variante,
    );
    Ok(crate::serialize::tiling_step_to_dict(&step))
}

pub(crate) fn choose_heuristic_drafting_action_json(
    search_config: &SearchConfig,
    state_json: &str,
    sims: u32,
    c: f64,
    seed: u64,
) -> PyResult<Value> {
    let parsed: Value = serde_json::from_str(state_json)
        .map_err(|e| PyValueError::new_err(format!("state_json: JSON-Parse-Fehler: {e}")))?;
    let state = crate::serialize::json_to_state_exact(&parsed).map_err(PyValueError::new_err)?;
    if state.phase != Phase::Drafting || state.players.iter().any(|p| p.start_tile_pending) {
        return Err(PyValueError::new_err(
            "choose_heuristic_drafting_action_json: state ist keine Drafting-Entscheidung.",
        ));
    }
    let actions = drafting_actions(&state);
    let mut rng = StdRng::seed_from_u64(seed);
    let chosen = crate::self_play::heuristic_arena_choose_action(
        &state, &actions, &mut rng, sims, c, search_config.heuristik_variante,
    );
    Ok(action_to_dict(&chosen))
}

pub(crate) fn choose_drafting_action_json(
    net: &Net,
    search_config: &SearchConfig,
    state_json: &str,
    sims: u32,
    c_puct: f64,
    seed: u64,
) -> PyResult<Value> {
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
    Ok(action_to_dict(&chosen))
}

/// Wave-3-Worker-Engine: laedt Modell+Spec EINMAL (Konstruktor), `choose()`
/// je Zug OHNE Neuladen -- Performance-Fix, gemessen 2026-08-23 (siehe
/// `RefereeGame::nets`-Kommentar: ohne Cache schaffte ein 3-Partien-
/// Testlauf mit 20 Minuten Wall-Clock nicht mal die erste Partie).
/// `tools/frozen_champion_worker.py` haelt GENAU eine Instanz ueber die
/// gesamte Prozess-Laufzeit.
#[pyclass]
pub struct FrozenWorkerEngine {
    /// `None` fuer ein HEURISTIK-Artefakt: es hat kein ONNX, sein Verhalten
    /// steckt im Wheel. Fuer `v2huelle` ist es dennoch gesetzt -- der
    /// Tiling-Durchfall-Pfad braucht es (self_play.rs:1234).
    net: Option<Net>,
    /// Ob die DRAFTING-Entscheidung heuristisch faellt.
    ///
    /// Getrennt vom Vorhandensein eines Netzes, und das ist der Kern: ein
    /// `v2huelle`-Artefakt HAT ein Netz -- aber nur fuer den
    /// Tiling-Durchfall-Pfad (self_play.rs:1234). Sein Drafting ist
    /// heuristisch. Wer beides an derselben Frage aufhaengt ("ist ein Netz
    /// da?"), laesst den Generator als Netz draften und misst einen anderen
    /// Spieler.
    ///
    /// Genau das ist am 2026-08-26 passiert und nur aufgefallen, weil sich
    /// die Partieergebnisse gegenueber dem Lauf davor aenderten.
    heuristik_drafting: bool,
    search_config: SearchConfig,
}

#[pymethods]
impl FrozenWorkerEngine {
    #[new]
    #[pyo3(signature = (model_path=None, spec=None, heuristik_drafting=false))]
    fn new(model_path: Option<String>, spec: Option<String>, heuristik_drafting: bool)
        -> PyResult<Self> {
        let net = match model_path {
            Some(p) => Some(load_net(&p)?),
            None => None,
        };
        let search_config = crate::resolve_search_config(spec)?;
        Ok(FrozenWorkerEngine { net, heuristik_drafting, search_config })
    }

    /// `state_json` rein -- `{"action": ..., "value": null}`-JSON-String
    /// raus (identisches Schema zu `lib.rs::net_arena_choice_state_json`).
    /// Trifft GENAU EINE Drafting-Entscheidung (par.8d: PER-ENTSCHEIDUNG-
    /// Protokoll, kein `rot_seed` mehr -- siehe `choose_drafting_action_json`-
    /// Doku).
    fn choose(&self, state_json: String, sims: u32, c_puct: f64, seed: u64) -> PyResult<String> {
        // Nach dem MODUS verzweigen, nicht danach, ob ein Netz da ist -- siehe
        // Feld-Doku zu `heuristik_drafting`.
        let action = match (&self.net, self.heuristik_drafting) {
            (Some(net), false) => choose_drafting_action_json(
                net, &self.search_config, &state_json, sims, c_puct, seed)?,
            _ => choose_heuristic_drafting_action_json(
                &self.search_config, &state_json, sims, c_puct, seed)?,
        };
        let value: Option<f32> = None;
        Ok(json!({ "action": action, "value": value }).to_string())
    }

    /// Tiling-Schritt -- mit dem EINMAL geladenen Netz.
    ///
    /// PERFORMANCE, und die Zahl ist gemessen: die freie Funktion
    /// `lib.rs::tiling_choice_state_json` laedt das ~9 MB ONNX bei JEDEM
    /// Aufruf neu und braucht dadurch **2.023 ms** je Entscheidung. Ueber die
    /// rund 24 Tiling-Schritte einer Partie sind das 48 Sekunden -- der
    /// Loewenanteil der 50 s, die eine Referee-Partie zunaechst kostete.
    ///
    /// Derselbe Fehler stand schon einmal im Code und ist dort dokumentiert
    /// ("ein 3-Partien-Testlauf schaffte in 20 Minuten nicht mal die erste
    /// Partie"). Ich habe ihn beim Bau von Baustein 2 wieder eingebaut; der
    /// Weg dagegen ist derselbe wie damals: der WORKER haelt das Netz.
    fn tiling(&self, state_json: String) -> PyResult<String> {
        let step = choose_tiling_step_json(&self.search_config, &state_json, self.net.as_ref())?;
        Ok(step.to_string())
    }

    /// Startsetzung -- braucht kein Netz, aber die Spec (und bei v2 den Seed).
    fn start_placement(&self, state_json: String, pi: usize, game_seed: u64) -> PyResult<String> {
        let p = choose_start_placement_json(&self.search_config, &state_json, pi, game_seed)?;
        Ok(p.to_string())
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
    /// Welcher Spieler bei einer angehaltenen EXTERNEN Startsetzung am Zug
    /// ist. Gemerkt statt neu hergeleitet, weil die Auswahl in
    /// `advance_to_decision` nicht `current_player()` folgt (der Nicht-Starter
    /// kann zuerst dran sein). Zweimal dieselbe Herleitung waeren zwei
    /// Gelegenheiten, sie unterschiedlich zu schreiben.
    pending_start_player: Option<usize>,
    /// Seiten, die eine Drafting-Aktion ueber `apply_chosen_action` anwenden
    /// (Sammelaufloesung des Stapelzugs) statt ueber `apply_drafting`.
    ///
    /// SPIEGELT `PlayerLoopConfig::apply_via_chosen_action` (self_play.rs:1971).
    /// Dort traegt die NETZ-Seite `true` und die HEURISTIK-Seite `false`: beim
    /// Netz loest `resolve_and_apply_stack_draw` den Zug zu Ende (Platte, Slot,
    /// Rotation nach fester Heuristik), bei der Heuristik wird nur der Peek
    /// angewandt und die Folgeschritte werden GESUCHT.
    ///
    /// Der Referee kannte diese Unterscheidung bis 2026-08-26 nicht und wandte
    /// immer sammelaufloesend an -- er gab der Heuristik-Seite also das
    /// Netz-Verhalten. Gemessen: 0 von 6 Partien identisch zu
    /// `net_arena_match`, erste Abweichung jeweils in der Kuppel-Slot-/
    /// Rotationswahl direkt nach einem Stapelzug.
    ///
    /// Default: BEIDE Seiten sammelaufloesend -- das ist das Bestandsverhalten
    /// des Referees und damit der Stand, auf dem der Kernbeweis (par.8f) gruen
    /// ist.
    sammelaufloesend: [bool; 2],
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
        RefereeGame { game, rng, game_seed: seed, steps: 0, nets: std::collections::HashMap::new(),
                      pending_start_player: None,
                      sammelaufloesend: [true, true] }
    }

    /// Fork A (par.8b) + par.8d: exakte Variante -- traegt zusaetzlich zu den
    /// bestehenden `state_to_json`-Feldern die vier geordneten verdeckten
    /// Sammlungen (Beutel/Turm/Kuppelstapel/Bonuschip-Pool) UND
    /// `pending_dome_choice_exact` (angefangener Kuppel-/Stapel-Zug, par.8d),
    /// die der Worker jetzt PFLICHT konsumiert (`choose_drafting_action_json`).
    /// Setzt den Anwendungsmodus je Seite (siehe Feld `sammelaufloesend`).
    ///
    /// `true` = wie die NETZ-Seite der Arena (`apply_chosen_action`,
    /// Sammelaufloesung des Stapelzugs), `false` = wie die HEURISTIK-Seite
    /// (`apply_drafting`, nur der Peek -- die Folgeschritte werden als eigene
    /// Entscheidungen gesucht).
    ///
    /// Muss gesetzt werden, wer eine Partie mit dem Arena-Pfad vergleichen
    /// will: der Default (beide sammelaufloesend) entspricht dort nur der
    /// Netz-Seite.
    fn set_apply_modes(&mut self, sammelaufloesend: (bool, bool)) {
        self.sammelaufloesend = [sammelaufloesend.0, sammelaufloesend.1];
    }

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

    /// Loest Startplatzierung und Tiling automatisch auf (Wortlaut-Kopie der
    /// Arena-Logik aus `unified_game_loop`, non-recording Zweig -- KEINE neue
    /// Spiellogik), bis eine Drafting-Entscheidung ansteht oder die Partie
    /// das Ende erreicht.
    ///
    /// `model_path_p{0,1}`: Tiling-Netz je Spieler (Board-Zuordnung wie
    /// `play_net_vs_net_game`: Spieler 0 -> `model_path_p0`, Spieler 1 ->
    /// `model_path_p1`); `None` = reiner DFS-Solver (Bestandsverhalten).
    ///
    /// `external_players`: Seiten, die ihre EIGENEN Entscheidungen treffen --
    /// Startsetzung wie Platzierung (Nutzer-Richtung 2026-08-26). Fuer sie
    /// haelt die Schleife mit `"start_placement"` bzw. `"tiling"` an, statt
    /// selbst zu entscheiden; der Aufrufer holt den Zug beim Artefakt und
    /// reicht ihn ueber `start_placement_apply_external` /
    /// `tiling_apply_external` zurueck. `None`/leer = Bestandsverhalten, der
    /// Referee loest alles selbst auf.
    ///
    /// EIN Begriff fuer beide Phasen, nicht zwei Listen: "diese Seite
    /// entscheidet selbst" ist EINE Eigenschaft des Agenten. Zwei Schalter
    /// waeren zwei Gelegenheiten, nur einen davon zu setzen -- und ein
    /// Artefakt, das sein Tiling selbst waehlt, aber die Startsetzung vom
    /// Referee bekommt, waere wieder ein halber Agent.
    ///
    /// WARUM DAS KEIN BRUCH DER REGEL-AUTORITAET IST (par.8): getrennt werden
    /// zwei Dinge, die bisher in `resolve_tiling_step` zusammenfielen -- WAS
    /// legal ist (bleibt beim Referee, `tiling_apply_external` prueft hart
    /// gegen `legal_steps`) und WELCHER legale Zug gewaehlt wird (gehoert dem
    /// Agenten). Beim Drafting steht diese Trennung seit Welle 3; fuer das
    /// Tiling fehlte sie, und damit spielte ein gefrorenes
    /// Heuristik-Artefakt nur seine halbe Identitaet: `resolve_tiling_step`
    /// ist auf `V1` verdrahtet (self_play.rs), also haette `v2huelle` wie
    /// `v1` gekachelt.
    ///
    /// Rueckgabe: `"drafting"` (Entscheidung noetig, `current_player()` sagt
    /// wer), `"tiling"` (Platzierung einer externen Seite noetig),
    /// `"game_over"` (Runde 5 fertig -- `finalize_scoring()` als
    /// naechstes aufrufen), oder `"stuck"` (Deadlock -- laut Bestandscode nie
    /// erwartet, siehe `unified_game_loop`s `None => break`-Zweige; wird hier
    /// NICHT verschluckt, sondern woertlich gemeldet).
    #[pyo3(signature = (model_path_p0=None, model_path_p1=None, external_players=None))]
    fn advance_to_decision(
        &mut self, model_path_p0: Option<String>, model_path_p1: Option<String>,
        external_players: Option<Vec<usize>>,
    ) -> PyResult<String> {
        let externe = external_players.unwrap_or_default();
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
                        if externe.contains(&pi) {
                            self.pending_start_player = Some(pi);
                            return Ok("start_placement".to_string());
                        }
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
                    if externe.contains(&pi) {
                        return Ok("tiling".to_string());
                    }
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

    /// Welcher Spieler bei `"start_placement"` am Zug ist.
    ///
    /// Eigene Abfrage, weil `current_player()` in dieser Phase NICHT die
    /// Antwort ist: die Startsetzung laeuft ueber `start_tile_pending` und
    /// kann den Nicht-Starter zuerst betreffen (siehe die Auswahllogik in
    /// `advance_to_decision`). Wer hier `current_player()` benutzt, setzt fuer
    /// die falsche Seite.
    fn pending_start_placement_player(&self) -> PyResult<usize> {
        self.pending_start_player.ok_or_else(|| {
            PyValueError::new_err(
                "pending_start_placement_player: keine Startsetzung anstehend \
                 (advance_to_decision hat zuletzt nicht 'start_placement' gemeldet)",
            )
        })
    }

    /// Wendet eine EXTERN entschiedene Startsetzung an -- nach Pruefung gegen
    /// die Kandidatenmenge der aktuellen Engine.
    ///
    /// Gleiche Linie wie [`Self::tiling_apply_external`]: die ENTSCHEIDUNG
    /// gehoert dem Agenten, die LEGALITAET der Engine. Anders als beim Tiling
    /// gibt es hier kein implizites "aufhoeren" -- jede eingereichte Setzung
    /// muss in der Kandidatenliste stehen.
    fn start_placement_apply_external(&mut self, placement_json: String) -> PyResult<String> {
        let pi = self.pending_start_placement_player()?;
        let parsed: Value = serde_json::from_str(&placement_json)
            .map_err(|e| PyValueError::new_err(format!("placement_json: JSON-Parse-Fehler: {e}")))?;
        let feld = |name: &str| -> PyResult<u64> {
            parsed.get(name).and_then(|x| x.as_u64()).ok_or_else(|| {
                PyValueError::new_err(format!("placement_json: Feld '{name}' fehlt oder ist keine Zahl"))
            })
        };
        let (tid, r, c, rot) = (
            feld("tile_id")? as usize, feld("row")? as usize,
            feld("col")? as usize, feld("rot")? as u32,
        );
        let legal = crate::self_play::start_placement_kandidaten(&self.game.state, pi);
        if !legal.iter().any(|(_, t, rr, cc, ro)| (*t, *rr, *cc, *ro) == (tid, r, c, rot)) {
            return Err(PyValueError::new_err(format!(
                "start_placement_apply_external: Setzung {placement_json} ist fuer Spieler {pi} \
                 NICHT legal ({} Kandidaten). Kein stiller Ersatz.",
                legal.len()
            )));
        }
        let _ = apply_start_placement(&mut self.game.state, pi, tid, r, c, rot);
        self.pending_start_player = None;
        self.steps += 1;
        Ok(json!({"tile_id": tid, "row": r, "col": c, "rot": rot}).to_string())
    }

    /// Wendet einen EXTERN entschiedenen Tiling-Schritt an -- nach harter
    /// Pruefung gegen die aktuell legalen Schritte.
    ///
    /// Gegenstueck zu [`Self::drafting_apply_external`]. Die Pruefung ist der
    /// Grund, warum die Regel-Autoritaet beim Referee bleiben kann, obwohl die
    /// ENTSCHEIDUNG von aussen kommt: ein Artefakt aus einer aelteren Aera
    /// kann keinen Zug durchsetzen, den die heutigen Regeln nicht kennen. Eine
    /// nicht-legale Antwort ist ein Abbruch mit Diagnose, keine stille
    /// Korrektur -- dieselbe Linie wie beim Drafting.
    ///
    /// `exact=true` bei der Legalitaetspruefung, weil GENAU DAS die Menge ist,
    /// aus der der echte Zug gewaehlt wird (`tiling_solver`: exakte
    /// Chip-Allokation nur im tatsaechlich gespielten Zug, nicht im
    /// MCTS-Blatt). Mit `false` waere eine legale Chip-Aufteilung faelschlich
    /// als illegal zurueckgewiesen worden.
    fn tiling_apply_external(&mut self, step_json: String) -> PyResult<String> {
        if self.game.state.phase != Phase::Tiling {
            return Err(PyValueError::new_err(
                "tiling_apply_external: keine Tiling-Phase anstehend",
            ));
        }
        let pi = self.game.state.current_player;
        let parsed: Value = serde_json::from_str(&step_json)
            .map_err(|e| PyValueError::new_err(format!("step_json: JSON-Parse-Fehler: {e}")))?;
        let step = crate::serialize::dict_to_tiling_step(&parsed).map_err(PyValueError::new_err)?;
        // `End` steht NICHT in `legal_steps` und ist trotzdem immer erlaubt:
        // der Solver fuehrt "hier aufhoeren" als Baseline 0 statt als
        // aufgezaehlten Schritt (`solve_rec`, Kommentar "Baseline 0 = hier
        // aufhoeren"). Die Liste enthaelt nur `Place` und `Chips`. Ohne diese
        // Unterscheidung waere JEDER Tiling-Abschluss als illegal
        // zurueckgewiesen worden -- der erste End-to-End-Lauf ist genau
        // darueber gestolpert.
        let legal = crate::tiling_solver::legal_steps(&self.game.state, pi, true);
        // Chips ORDNUNGSFREI vergleichen. `TilingStep` leitet `PartialEq` ab,
        // also vergleicht `contains` den `Vec<usize>` der Chip-Indizes
        // ORDNUNGSEMPFINDLICH -- die Engine tut das nicht:
        // `apply_bonus_chips_with` (round_end.rs) sortiert die Indizes als
        // ERSTES (`idx.sort_unstable(); idx.dedup();`), die Reihenfolge ist
        // semantisch bedeutungslos.
        //
        // Sie kommt trotzdem vor: bei mehr als `CHIP_ALLOC_CAP` Chips faellt
        // `chip_allocations` auf `greedy_chip_indices` zurueck, und das
        // liefert Greedy-Reihenfolge statt aufsteigender. Gefunden am
        // 2026-08-26 in einem 24-Partien-Lauf, der einen legalen Zug
        // `{"chips":[2,3,0,1,4]}` abwies.
        //
        // Das ist KEINE Aufweichung der Regel-Autoritaet: verglichen wird
        // genau das, was die Engine anwendet -- die MENGE. `Place` und `End`
        // bleiben strikt.
        let passt = |a: &TilingStep| -> bool {
            match (a, &step) {
                (TilingStep::Chips { row: r1, chips: c1 },
                 TilingStep::Chips { row: r2, chips: c2 }) => {
                    let (mut x, mut y) = (c1.clone(), c2.clone());
                    x.sort_unstable();
                    y.sort_unstable();
                    r1 == r2 && x == y
                }
                _ => a == &step,
            }
        };
        if step != TilingStep::End && !legal.iter().any(passt) {
            return Err(PyValueError::new_err(format!(
                "tiling_apply_external: Schritt {step_json} ist fuer Spieler {pi} NICHT legal \
                 ({} legale Schritte). Kein stiller Ersatz -- das Artefakt und die aktuelle \
                 Engine sind sich ueber die Regeln nicht einig, und das gehoert diagnostiziert.",
                legal.len()
            )));
        }
        match &step {
            TilingStep::Place(ta) => {
                let _ = self.game.apply_single_tiling(pi, ta);
            }
            TilingStep::Chips { row, chips } => {
                apply_bonus_chips_with(&mut self.game.state.players[pi], *row, chips);
            }
            TilingStep::End => {
                let _ = self.game.apply_tiling(&TilingMove::EndTiling { player: pi }, &mut self.rng);
            }
        }
        self.steps += 1;
        Ok(crate::serialize::tiling_step_to_dict(&step).to_string())
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
        let pi_akt = self.game.state.current_player;
        if self.sammelaufloesend[pi_akt] {
            apply_chosen_action(&mut self.game, chosen).map_err(PyValueError::new_err)?;
        } else {
            self.game.apply_drafting(&chosen).map_err(PyValueError::new_err)?;
        }
        self.steps += 1;
        Ok(dict.to_string())
    }

    /// Seite EXTERN (Worker): wendet die vom Worker gewaehlte Aktion an --
    /// HART validiert gegen die aktuell legalen Aktionen (exakter Vergleich
    /// ueber `serialize::action_to_dict`, dieselbe Funktion, die der Worker
    /// zur Auswahl bekommt, siehe `lib.rs::net_arena_choice_state_json`) --
    /// eine illegale/unbekannte Aktion ist ein Fehler, keine stille
    /// Ersatzwahl (par.8: "Regel-Autoritaet"). Wendet GENAU EINE Aktion an
    /// (par.8d: PER-ENTSCHEIDUNG-Protokoll) -- der Treiber
    /// (`tools/frozen_referee_match.py`) ruft diese Methode fuer JEDEN
    /// einzelnen Schritt eines mehrstufigen Kuppel-/Stapel-Zugs erneut auf,
    /// mit einem frisch von `state_json()`/`pending_search_seed()` geholten
    /// Zwischenzustand dazwischen. Die fruehere ATOMARE Sonderbehandlung fuer
    /// Kuppelplatzierungen (Stufe-2-Rotation im selben Aufruf, `rotation`-
    /// Feld im Antwort-Dict) ist entfallen: `pending_dome_choice` traegt
    /// `state_json` jetzt exakt (`serialize::state_to_json_exact`s fuenftes
    /// Feld, par.8d), also grenzt `drafting_actions` die naechste Anfrage von
    /// selbst auf die Rotationswahl ein -- keine Sonderbehandlung noetig.
    fn drafting_apply_external(&mut self, action_json: String) -> PyResult<()> {
        if self.game.state.phase != Phase::Drafting || self.game.state.players.iter().any(|p| p.start_tile_pending) {
            return Err(PyValueError::new_err("drafting_apply_external: keine Drafting-Entscheidung anstehend"));
        }
        let parsed: Value = serde_json::from_str(&action_json)
            .map_err(|e| PyValueError::new_err(format!("action_json: JSON-Parse-Fehler: {e}")))?;

        // par.8d (PER-ENTSCHEIDUNG-Protokoll): GENAU EINE Aktion pruefen und
        // anwenden -- keine Sonderbehandlung mehr fuer Kuppel-Zuege (die
        // fruehere atomare `rotation`-Anreicherung/Zwei-Stufen-Anwendung ist
        // entfallen, siehe `choose_drafting_action_json`-Doku). Eine
        // Rotationswahl (`ChooseDomeRotation`) ist hier einfach EINE weitere
        // Aktion unter `drafting_actions(&self.game.state)`, exakt wie jede
        // andere -- `drafting_actions` grenzt die Kandidaten von selbst auf
        // die Folgeschritte ein, solange `pending_dome_choice`/
        // `pending_stack_draw` korrekt gesetzt sind.
        let actions = drafting_actions(&self.game.state);
        let is_stone = parsed.get("type").and_then(|t| t.as_str()) == Some("stone");
        let found = if is_stone {
            // Sonderfall Moon-Order (siehe `stone_dict_without_moon_order`-
            // Doku): erst OHNE `moon_order` matchen, dann die eingereichte
            // Reihenfolge als Multiset gegen den Kandidaten pruefen -- eine
            // andere, aber gueltige Permutation ist LEGAL, wird aber nicht
            // stillschweigend durch die kanonische Reihenfolge ersetzt,
            // sondern EXAKT wie eingereicht angewandt (nach Pruefung).
            let target_stripped = stone_dict_without_moon_order(&parsed);
            let submitted_order: Vec<String> = parsed
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
            actions.into_iter().find(|a| action_to_dict(a) == parsed)
        };
        let chosen = match found {
            Some(a) => a,
            None => {
                return Err(PyValueError::new_err(format!(
                    "Worker-Aktion ist in dieser Stellung nicht legal (Regel-Autoritaet verweigert): {parsed}"
                )))
            }
        };
        let pi = self.game.state.current_player;
        if self.sammelaufloesend[pi] {
            apply_chosen_action(&mut self.game, chosen).map_err(PyValueError::new_err)?;
        } else {
            // Nur die eine Aktion. Bei `DrawStackPeek` bleibt der Zug damit
            // OFFEN, und `advance_to_decision` meldet gleich wieder
            // "drafting" -- die Folgeschritte werden zu eigenen Anfragen.
            // Genau dafuer ist das PER-ENTSCHEIDUNG-Protokoll aus par.8d
            // gebaut; bis 2026-08-26 wurde nur nie danach gefragt.
            self.game.apply_drafting(&chosen).map_err(PyValueError::new_err)?;
        }
        self.steps += 1;
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
