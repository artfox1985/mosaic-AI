//! Die SHAPING-Schicht: additive Terme auf den Blattwert.
//!
//! Herausgeloest aus `net_mcts.rs` am 2026-08-27 (Architektur-Schritt A).
//! Die Datei war 10.923 Zeilen und trug siebzehn durch Banner getrennte
//! Anliegen, fast jedes mit eigener Prereg. Das hier ist eins davon --
//! Langreihen-Initiierung, Wertungsplatten-Shaping, EGO-Shaping,
//! Ownership-Verbrauch, Freischaltung -- plus die Knopf-Zugriffe, die dazu
//! gehoeren.
//!
//! WARUM GERADE DIESE SCHICHT ZUERST: sie ist die, die mit jeder neuen
//! Vorregistrierung waechst. Der benannte Nutzniesser ist gemessen, nicht
//! erhofft: v2 aus dem Quellstand zu nehmen kostete am 2026-08-27 rund 2.900
//! Zeilen ueber fuenf Module, weil die Variante durchgefaedelt statt
//! gekapselt war. Ein Term, der hier liegt, ist eine Datei -- und seine
//! Verwerfung eine geloeschte Datei.
//!
//! REINE VERSCHIEBUNG: kein Term ist veraendert, keine Reihenfolge, kein
//! Default. Was vorher privat war, ist jetzt `pub(crate)` -- mehr nicht.

use crate::state::GameState;

// Aus dem Suchmodul: die Bausteine, auf denen die Shaping-Terme rechnen.
// Rust erlaubt die Gegenrichtung ausdruecklich (Module eines Crates duerfen
// sich gegenseitig benutzen) -- anders als bei der Python-Seite in Schritt C,
// wo ein Rueckimport einen echten Zyklus erzeugt haette.
use crate::net_mcts::{read_f64_env, floor_penalties, FLOOR_SHAPING_SCALE};
use crate::scoring::scoring_progress;

// ── Langreihen-Initiierung (PREREG_long_row_payoff.md par.3/B1) ─────────────

/// Skala fuer das Langreihen-Initiierungs-Additiv. **NICHT von
/// `FLOOR_SHAPING_SCALE`/`VALUE_SCALE` uebernommen** -- siehe
/// `PREREG_floor_shaping_scale.md`: dort ist nachgerechnet, dass ein Nenner
/// 50 fuer einen Zaehler mit kleiner Spanne die `tanh` dekorativ macht (der
/// Term bleibt vollstaendig im linearen Zipfel).
///
/// Hier laeuft der Zaehler nur ueber `[-2, +2]` (Differenz der Zahl
/// begonnener langer Reihen). Nenner 10 legt das maximale `tanh`-Argument auf
/// `0,2` und damit den maximalen Blattwert-Shift bei `w = 0,3` auf `0,059` --
/// dieselbe Groessenordnung wie der Floor-Term, der EINZIGE Blattwert-Term
/// mit nachgewiesener Staerkewirkung (11,25 pp, McNemar p=0,0001). Mit
/// Nenner 50 waere der Shift `0,012` gewesen, also fuenfmal schwaecher.
/// Nutzer-Entscheid 2026-08-24.
pub(crate) const LONG_ROW_INIT_SHAPING_SCALE: f64 = 10.0;

/// Musterreihen-Indizes der langen Reihen. Zentral in `board.rs`, damit das
/// Such-Additiv hier und die Arena-Zaehler (`execution.rs`, `round_end.rs`)
/// nicht auseinanderlaufen koennen: sonst koennte der Mitschrieb eine andere
/// Reihenmenge zaehlen als der Knopf bewegt.
use crate::board::LONG_ROW_INDICES;

/// Zahl der BEGONNENEN langen Musterreihen (mindestens eine Fliese), `0..=2`.
/// **Stufenfunktion am Uebergang 0 -> 1, kein Fuellstands-Anteil** -- das ist
/// der ganze Punkt des Terms (par.2a: die Luecke sitzt im Beginnen, nicht im
/// Fortsetzen).
pub(crate) fn long_rows_started(player: &crate::board::PlayerBoard) -> f64 {
    LONG_ROW_INDICES
        .iter()
        .filter(|&&i| !player.pattern_lines[i].tiles.is_empty())
        .count() as f64
}

/// Ego-perspektivische Differenz begonnener langer Reihen, skaliert --
/// dieselbe Bauform wie `floor_shaping_delta_ego` bei `opp_bias = 1.0`
/// (Nullsummen-Additiv, kein systematischer Versatz auf der Blattwertskala).
pub(crate) fn long_row_init_delta(state: &GameState, ego: usize) -> f64 {
    let own = long_rows_started(&state.players[ego]);
    let opp = long_rows_started(&state.players[1 - ego]);
    (own - opp) / LONG_ROW_INIT_SHAPING_SCALE
}

/// Eskalationsstufe E2 (`evaluations/PREREG_aggression_style_measurement.md`,
/// `MOSAIC_FLOOR_SHAPING_OPP_BIAS`): verallgemeinert `floor_shaping_delta`
/// von der festen Spieler0-minus-Spieler1-Differenz auf eine EGO-
/// perspektivische, asymmetrisch gewichtete Fassung:
/// `delta_ego = (own - opp_bias * opp) / FLOOR_SHAPING_SCALE`, wobei `own`
/// die Floor-Strafsumme von `ego` und `opp` die des jeweils ANDEREN Spielers
/// ist. Vorzeichenkonvention wie beim Bestand: `own`/`mine` = weniger
/// negativ = besser fuer `ego` (die eigene Strafe soll klein sein), `opp`
/// wird mit `opp_bias` skaliert, BEVOR es abgezogen wird -- `opp_bias>1`
/// gewichtet eine hohe GEGNER-Strafe staerker als die eigene, `opp_bias=1`
/// ist exakt die alte, symmetrische Definition (own - opp, ungewichtet).
///
/// Bei `opp_bias == 1.0` liefert dies fuer `ego=0` bit-identisch denselben
/// Wert wie `floor_shaping_delta` (Multiplikation mit exakt `1.0` rundet
/// nie, siehe IEEE754) -- die Aufrufstellen verzweigen trotzdem explizit
/// auf den alten Ausdruck, um jeden Zweifel an Bit-Identitaet auszuschliessen
/// (kein Vertrauen auf `tanh`s exakte Ungeradheit ueber Systemgrenzen).
pub(crate) fn floor_shaping_delta_ego(state: &GameState, ego: usize, opp_bias: f64) -> f64 {
    let (mine, theirs) = floor_penalties(state);
    let (own, opp) = if ego == 0 { (mine, theirs) } else { (theirs, mine) };
    (own - opp_bias * opp) / FLOOR_SHAPING_SCALE
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
pub(crate) const PLATE_SHAPING_SCALE: f64 = 50.0;

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
/// ([`crate::scoring::scoring_progress`], dieselbe stetige Fortschritts-
/// Heuristik, die die DFS-Blattbewertung in `mcts.rs::player_total` schon
/// lange nutzt), KEIN Netz-Forward-Pass, analog `floor_shaping_delta`.
/// `scoring_progress` selbst fällt bei voller Plattenfüllung exakt auf den
/// echten `calculate_end_scoring`-Punktwert zurück (siehe dortiger
/// Kommentar) -- keine Doppelzählung mit dem tatsächlichen Endwertungs-Score.
pub(crate) fn plate_shaping_delta(state: &GameState) -> f64 {
    let mine = scoring_progress(&state.players[0], &state.scoring_tile_ids);
    let theirs = scoring_progress(&state.players[1], &state.scoring_tile_ids);
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
pub(crate) fn apply_plate_shaping(value: [f64; 2], state: &GameState, parent_state: Option<&GameState>) -> [f64; 2] {
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
pub(crate) fn plate_shaping_marginal(state: &GameState, parent_state: Option<&GameState>) -> f64 {
    match parent_state {
        Some(ps) => plate_shaping_delta(state) - plate_shaping_delta(ps),
        None => 0.0,
    }
}

// ── Wertungsplatten-EGO-Shaping (Nutzer-Auftrag 2026-08-10) ─────────────────
// Eigenstaendiges, VOM Task-#93-Plattenshaping oben UNABHAENGIGES Additiv --
// nicht zu verwechseln, drei Unterschiede:
//   1. Formel: `scoring_progress_alpha` (parametrisierter Exponent, eigene
//      Funktion in `scoring.rs`) statt `scoring_progress` (fest `alpha=2`,
//      der Heuristik-Anker -- bleibt unangetastet, siehe dortige Doku).
//   2. Perspektive: JE SPIELER ABSOLUT, NICHT ego-only (Nutzer-Korrektur
//      2026-08-11 -- "ego-only" war eine falsche Lesart der urspruenglichen
//      Formulierung: BEIDE Spieler bekommen unabhaengig einen Shift aus
//      ihrem EIGENEN Brett, `value[i] += w*tanh(f(players[i])/scale)` fuer
//      i in {0,1} getrennt -- sonst wuerde die Suche annehmen, der GEGNER
//      ignoriere die Wertungsplatten, exakt die Self-Play-Blindheit nur
//      innerhalb der Suche. "NUR das eigene Brett" heisst NUR: kein
//      Cross-Term zwischen den Spielern (Index i haengt nicht von
//      `players[1-i]` ab) -- NICHT, dass der Gegner-Fortschritt ignoriert
//      wird. KEINE mine-minus-theirs-Differenz wie `plate_shaping_delta`
//      (stehende, unabhaengig begruendete Anforderung: eine Differenzform
//      macht 55:50 schlechter als 30:15, siehe Test `apply_wertung_shaping_
//      with_rejects_difference_form_same_margin_different_level`).
//   3. Absolut statt marginal: kein Eltern-Delta wie `plate_shaping_marginal`
//      (dessen Baseline-Trick loest ein Gumbel-Geschwistervergleichsproblem,
//      das hier nicht Gegenstand des Auftrags war).
//   4. Runtime-Knopf-Muster: zwei einfache `MOSAIC_*`-Env-Vars (Gewicht +
//      Exponent), analog `floor_shaping_weight`/`floor_shaping_opp_bias`
//      (OnceLock<f64>, EINMAL gelesen), statt eines Compile-Konstante-Togges
//      wie `PLATE_SHAPING_ENABLED`.
// Beide Additive sind unabhaengig voneinander AN/AUS-schaltbar und komponieren
// rein additiv, falls beide je aktiviert wuerden (hier: Anwendungsreihenfolge
// NACH dem Plattenshaping oben, siehe Aufrufstellen in `make_node`/
// `net_leaf_eval`).

/// Skala fuer das Wertungsplatten-EGO-Shaping, gleiche Groessenordnung wie
/// `FLOOR_SHAPING_SCALE`/`PLATE_SHAPING_SCALE` (beide 50.0) -- macht die
/// Korrektur direkt vergleichbar mit dem own-minus-opp-Score-Margin, das
/// `value`/`points_forecast` schon als Trainingsziel verwenden (`VALUE_SCALE`
/// in `neural_net.py`, ebenfalls 50.0). Eigene Konstante statt Wiederverwendung
/// von `PLATE_SHAPING_SCALE` -- unabhaengig nachkalibrierbar, ohne das andere
/// (unabhaengige) Additiv zu beeinflussen.
pub(crate) const WERTUNG_SHAPING_SCALE: f64 = 50.0;

/// Default-Gewicht des Wertungsplatten-EGO-Shaping-Additivs -- `0.0` = AUS,
/// exakt Bestandsverhalten (kein Netz-Blattwert je durch dieses Additiv
/// veraendert, solange `MOSAIC_WERTUNG_SHAPING_W` ungesetzt bleibt).
pub const WERTUNG_SHAPING_WEIGHT: f64 = 0.0;

/// Default-Exponent `alpha` fuer `scoring_progress_alpha` -- `2.0` reproduziert
/// exakt den Exponenten, den der Heuristik-Anker (`scoring_progress`,
/// `.powi(2)`) fest verwendet; nur bei `alpha != 2.0` weicht die Formung von
/// der Heuristik ab.
pub const WERTUNG_SHAPING_ALPHA: f64 = 2.0;

/// Laufzeit-Wert von `MOSAIC_WERTUNG_SHAPING_W` -- gleiches OnceLock-Muster
/// wie `floor_shaping_weight` (einmalig gelesen, kein GUI-Live-Regler
/// vorgesehen, anders als `points_utility_w`s `AtomicU64`-Zelle -- dafuer gibt
/// es hier keinen Anwendungsfall). Ohne gesetzte Env-Var byte-identisches
/// Bestandsverhalten (Default `WERTUNG_SHAPING_WEIGHT` = 0.0).
pub fn scoring_shaping_weight() -> f64 {
    static CELL: std::sync::OnceLock<f64> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| read_f64_env("MOSAIC_WERTUNG_SHAPING_W", WERTUNG_SHAPING_WEIGHT))
}

thread_local! {
    /// Plattengewicht der AKTUELLEN Partie in DIESEM Thread. `None` = der
    /// prozessweite Env-Wert gilt (Bestandsverhalten).
    static GAME_WEIGHT: std::cell::Cell<Option<f64>> = const { std::cell::Cell::new(None) };
}

/// Setzt das Wertungsplatten-Gewicht fuer die aktuelle Partie in DIESEM Thread.
///
/// WARUM THREAD-LOKAL und nicht prozessweit (Nutzer-Auftrag 2026-08-11: *"nimm als
/// hinweis fuers self play mit, dass wir je spiel auch das gewicht des
/// wertungsplattenshapings anpassen sollten. dann bekommt der ownership head
/// ordentlich was zu sehen"*): Self-Play spielt mehrere Partien GLEICHZEITIG in
/// Threads. Ein prozessweiter Wert -- wie ihn `MOSAIC_WERTUNG_SHAPING_W` ueber
/// `OnceLock` liefert -- waere fuer alle laufenden Partien derselbe, und die
/// Streuung entstuende gar nicht. Muster uebernommen von `STATS_OVERRIDE` in
/// `tiling_solver.rs`.
///
/// `None` stellt das Bestandsverhalten wieder her. Aufrufer MUSS am Partieende
/// zuruecksetzen, sonst leckt der Wert in die naechste Partie desselben Threads.
pub fn set_game_shaping_weight(w: Option<f64>) {
    GAME_WEIGHT.with(|c| c.set(w));
}

/// PREREG_ownership_corpus.md §3 Punkt 6: Fuehrt `f` mit AUSGESETZTER
/// Partie-STREUUNG aus (`GAME_WEIGHT` auf DIESEM Thread kurzzeitig
/// `None`) -- fuer Label-Rollouts (`round_transition_deep.rs`s
/// `bootstrap_value_after_rounds`/`continue_through_round{2,3,4}`), NICHT
/// fuer die eigentliche Suche/Zugwahl.
///
/// WARUM: `bootstrap_value`/`round_transition_value` sollen den
/// tatsaechlich erwartbaren Spielausgang moeglichst rauscharm schaetzen.
/// `GAME_WEIGHT` ist aber ein je Partie ZUFAELLIG aus dem Partie-Seed
/// abgeleiteter Wert (`game_weight_from_seed`, `MOSAIC_WERTUNG_STREUUNG_MAX`)
/// -- ohne diese Aussetzung wuerde derselbe Zustand im Trainingsziel rein
/// durch den Wuerfelwurf DIESER Partie anders bewertet, ohne jeden Bezug zum
/// echten Ausgang (die Suche/Zugwahl DARF diese Streuung weiterhin sehen --
/// das ist ihr eigentlicher Zweck, siehe `set_game_shaping_weight`-Doku:
/// mehr Vielfalt fuers Self-Play/den Ownership-Kopf; nur die LABEL-Rechnung
/// nicht).
///
/// Der PROZESSWEITE Basiswert (`MOSAIC_WERTUNG_SHAPING_W`, konstant ueber
/// alle Partien, seit laenger bestehend) bleibt bewusst WIRKSAM: faellt
/// `GAME_WEIGHT` auf `None` zurueck, liest `scoring_shaping_weights()`
/// wieder den Env-Wert (siehe dortiger Code) -- das ist die bestehende,
/// in `net_leaf_eval`s eigener Doku ausdruecklich gewollte Kopplung
/// ("gilt unveraendert fuer JEDEN net_leaf_eval-Aufrufer ... eingeschlossen"),
/// nicht Gegenstand dieser Frage und hier nicht angetastet.
///
/// RAII statt eines manuellen "danach zuruecksetzen": Rust fuehrt `Drop`
/// beim Stack-Unwinding auch bei einem Panic MITTEN in `f` aus -- ein
/// Fehlschlag tief in der rekursiven Simulation wuerde die Streuung sonst
/// fuer den Rest der Partie auf demselben (wiederverwendeten) Thread
/// verschlucken.
pub(crate) fn with_game_scatter_suspended<T>(f: impl FnOnce() -> T) -> T {
    let prev = GAME_WEIGHT.with(|c| c.get());
    struct Restore(Option<f64>);
    impl Drop for Restore {
        fn drop(&mut self) {
            GAME_WEIGHT.with(|c| c.set(self.0));
        }
    }
    let _restore = Restore(prev);
    GAME_WEIGHT.with(|c| c.set(None));
    f()
}

/// Streubreite fuer das partieweise Gewicht, `MOSAIC_WERTUNG_STREUUNG_MAX`.
/// Default **0,0 = aus**, dann gilt ausschliesslich der prozessweite Env-Wert.
/// Bei `> 0` leitet [`game_weight_from_seed`] je Partie einen Wert in
/// `[0, max]` ab.
pub fn scoring_scatter_max() -> f64 {
    static CELL: std::sync::OnceLock<f64> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| read_f64_env("MOSAIC_WERTUNG_STREUUNG_MAX", 0.0))
}

/// Deterministische Ableitung des Partiegewichts aus dem Partie-Seed.
///
/// Reproduzierbar (kein Zufall zur Laufzeit -- dieselbe Partie ergibt dasselbe
/// Gewicht), gleichverteilt in `[0, max]`. Die Mischung ist der
/// SplitMix64-Finalizer; er wird gebraucht, weil aufeinanderfolgende Partie-Seeds
/// im Self-Play sich oft nur in den unteren Bits unterscheiden und eine rohe
/// Modulo-Bildung dann eine Treppe statt einer Streuung ergaebe.
pub fn game_weight_from_seed(seed: u64, max: f64) -> f64 {
    let mut z = seed.wrapping_add(0x9E37_79B9_7F4A_7C15);
    z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
    z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
    z ^= z >> 31;
    max * ((z % 1_000_000) as f64 / 999_999.0)
}

/// PREREG_search_rng_split.md: Such-RNG von der Partie trennen. Leitet einen
/// EIGENEN, deterministischen Seed fuer EINE Such-/Entscheidungs-Episode aus
/// `(game_seed, move_index)` ab -- Praezedenz `game_weight_from_seed` oben
/// (gleicher SplitMix64-Finalizer), hier zweistufig, weil ZWEI Eingaben statt
/// einer gemischt werden muessen: erst `game_seed` durch den Finalizer, dann
/// `move_index` addiert und NOCHMAL durch den Finalizer -- eine simple
/// Summe/XOR beider Werte waere bei benachbarten `move_index`-Werten
/// (0,1,2,...) nur eine Treppe in den unteren Bits, keine echte Streuung.
///
/// Aufrufer (self_play.rs/py.rs, siehe dortige Kommentare) bauen daraus
/// `StdRng::seed_from_u64(derive_search_seed(...))` und geben DIESE Instanz
/// an die Suche/Entscheidungs-Sampling weiter -- NICHT mehr den echten
/// Partie-RNG. Der Partie-RNG selbst wird dadurch nur noch durch ECHTE
/// Spielzustands-Ereignisse (`Game::start`, `Bag::refill_from_tower` über
/// `apply_tiling`s `EndTiling`) verbraucht, deren Haeufigkeit NICHT von der
/// Suchtiefe (sims) abhaengt -- das ist der Kern des Schnitts (Prereg §2/§5).
pub fn derive_search_seed(game_seed: u64, move_index: u64) -> u64 {
    let mut z = game_seed.wrapping_add(0x9E37_79B9_7F4A_7C15);
    z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
    z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
    z ^= z >> 31;
    z = z.wrapping_add(move_index.wrapping_add(0x9E37_79B9_7F4A_7C15));
    z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
    z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
    z ^= z >> 31;
    z
}

/// `MOSAIC_WERTUNG_SHAPING_W` als **acht Werte, einer JE KRITERIUM** -- gleiches
/// Format und gleiche Haerte wie `scoring_shaping_alphas` (1 Wert gilt fuer alle;
/// falsche Laenge wird VERWORFEN, nicht teilgelesen).
///
/// WARUM ein Gewicht je Kriterium und nicht nur ein alpha je Kriterium
/// (Nutzer-Aufbau 2026-08-11): der Versuch will *"20 Spiele in denen die
/// vertikalen Wertungsplatten aktiv sind, NUR mit alpha variation der vertikalen
/// platten"*. Dafuer muessen die anderen Kriterien AUS sein, sonst laeuft jede
/// Messung gegen einen Hintergrund aus sieben weiteren Shaping-Termen und der
/// Effekt ist nicht mehr zurechenbar.
///
/// **Und alpha kann das nicht leisten**: ein Kriterium abzuschalten geht ueber den
/// Exponenten nicht -- ein hohes alpha drueckt den Teilfortschritt nur
/// asymptotisch gegen 0, `(1.0)^alpha` bleibt 1. Nur ein Gewicht 0 schaltet
/// wirklich ab. "Nur die Vertikale" heisst damit `0,1,0,0,0,0,0,0`.
pub fn scoring_shaping_weights() -> [f64; 8] {
    // Partieweiser Wert schlaegt den prozessweiten -- siehe
    // `set_game_shaping_weight`.
    if let Some(w) = GAME_WEIGHT.with(|c| c.get()) {
        return [w; 8];
    }

    static CELL: std::sync::OnceLock<[f64; 8]> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| {
        let mut out = [WERTUNG_SHAPING_WEIGHT; 8];
        let Ok(raw) = std::env::var("MOSAIC_WERTUNG_SHAPING_W") else { return out };
        let parts: Vec<&str> = raw.split(',').map(|p| p.trim()).filter(|p| !p.is_empty()).collect();
        let vals: Option<Vec<f64>> = parts.iter().map(|p| p.parse::<f64>().ok()).collect();
        match vals.as_deref() {
            Some([one]) => out = [*one; 8],
            Some(v) if v.len() == 8 => out.copy_from_slice(v),
            _ => eprintln!(
                "MOSAIC_WERTUNG_SHAPING_W={raw:?} ignoriert -- erwartet 1 oder 8 Zahlen, Default {WERTUNG_SHAPING_WEIGHT} gilt"
            ),
        }
        out
    })
}

/// Laufzeit-Wert von `MOSAIC_WERTUNG_ALPHA` -- **acht Werte, einer JE KRITERIUM**
/// (Nutzer-Vorgabe 2026-08-11: *"wir wollen ja alpha pro wertungsplatte seperat
/// festlegen"*). Format: kommagetrennt in Kriterien-Reihenfolge 0..7, z.B.
/// `2,6,9,2,2,2.6,2,2`. **Ein einzelner Wert gilt fuer alle** (Rueckwaerts-
/// kompatibilitaet und bequem fuer globale A/Bs). Ungesetzt = alle
/// `WERTUNG_SHAPING_ALPHA` (2.0), also byte-identisches Bestandsverhalten.
///
/// Fehlerhafte oder unvollstaendige Listen fallen HART auf den Default zurueck --
/// kein stilles Teil-Parsen, sonst waere ein Tippfehler ein unbemerkt anderer
/// Versuch (vgl. `train.py --load`-Footgun).
pub fn scoring_shaping_alphas() -> [f64; 8] {
    static CELL: std::sync::OnceLock<[f64; 8]> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| {
        let mut out = [WERTUNG_SHAPING_ALPHA; 8];
        // Die alten Spezialfeld-Knoepfe sind seit der Zusammenfuehrung 2026-08-11
        // WIRKUNGSLOS (ein Gewicht, alphas[6] als Exponent). Ein still
        // wirkungsloser Regler ist gefaehrlicher als ein fehlender: jemand
        // setzt ihn, liest ein H0 und schliesst auf den Term. Deshalb laut.
        for alt_var in ["MOSAIC_UNLOCK_SHAPING_W", "MOSAIC_UNLOCK_BETA"] {
            if std::env::var(alt_var).is_ok() {
                eprintln!(
                    "{alt_var} ist WIRKUNGSLOS (seit 2026-08-11 zusammengefuehrt) --                      nutze MOSAIC_WERTUNG_SHAPING_W fuer das Gewicht und die 7. Stelle                      von MOSAIC_WERTUNG_ALPHA fuer den Spezialfeld-Exponenten."
                );
            }
        }
        let Ok(raw) = std::env::var("MOSAIC_WERTUNG_ALPHA") else { return out };
        let parts: Vec<&str> = raw.split(',').map(|p| p.trim()).filter(|p| !p.is_empty()).collect();
        let vals: Option<Vec<f64>> = parts.iter().map(|p| p.parse::<f64>().ok()).collect();
        match vals.as_deref() {
            Some([one]) => out = [*one; 8],
            Some(v) if v.len() == 8 => out.copy_from_slice(v),
            _ => eprintln!(
                "MOSAIC_WERTUNG_ALPHA={raw:?} ignoriert -- erwartet 1 oder 8 Zahlen, Default {WERTUNG_SHAPING_ALPHA} gilt"
            ),
        }
        out
    })
}

/// Laufzeit-Wert von `MOSAIC_WERTUNG_ROUND_GAIN` -- hebt ALLE Exponenten ueber die
/// Runden an: `alpha_c(r) = alpha_c * (1 + gain * (r-1)/4)`. Default **0,0** = keine
/// Rundenabhaengigkeit. Ersetzt die frueheren, einkompilierten kalibrierten
/// Zielwerte je Kriterium -- die waren nicht begruendbar, weil
/// `Mittel(x^alpha) > Rate` fuer JEDES alpha gilt (siehe `scoring.rs`-Doku).
/// Gewicht fuer den Strafleisten-Gegenterm im Wertungsplatten-Shaping.
/// Default **0,0** = aus, Bestandsverhalten.
///
/// WARUM (Nutzer: *"aber ja probier es aus"*, 2026-08-11): die HEURISTIK benutzt
/// `scoring_progress` nie allein, sondern als Mittelterm von
/// `player_total` (`mcts.rs:80-84`) -- daneben stehen der Tiling-Solver-Score UND
/// `projected_unplaceable_penalty`. Meine Injektion hatte nur den Mittelteil.
///
/// Zwei Gruende, es zu messen statt zu argumentieren:
///  1. GEMESSEN: die Injektion treibt die Strafleiste monoton hoch (+2,42 Pkt bei
///     w=1,0, t=+2,42) -- genau die Buesse, die dieser Term einpreist.
///  2. `projected_unplaceable_penalty` liest `player.pattern_lines`
///     (`round_end.rs:116-120`) und ist damit das EINZIGE verfuegbare Stueck des
///     Shapings, das die Musterreihen sieht. `scoring_progress` liest nur das
///     Kuppelraster und ist deshalb innerhalb einer Runde fuer JEDEN
///     Drafting-Zug gleich -- es kann die Wahl gar nicht lenken, dieser Term
///     kann es.
///
/// Gegenargument, das die Messung entscheiden soll: der Value-Kopf ist auf
/// AUSGAENGE trainiert, Strafpunkte gehen in den Ausgang ein -- er preist sie
/// also schon ein, und der Term koennte doppelt zaehlen.
pub fn scoring_floor_weight() -> f64 {
    static CELL: std::sync::OnceLock<f64> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| read_f64_env("MOSAIC_WERTUNG_FLOOR_W", 0.0))
}

/// Gewicht fuer den **Tiling-Potenzial**-Term. Default **0,0** = aus.
///
/// HERKUNFT (Nutzer-Entscheid 2026-08-11, nach *"nichts davon"* zu meinen zwei
/// selbst erfundenen Musterreihen-Termen): NICHT nachbauen, sondern den nehmen,
/// den die Heuristik benutzt. `mcts.rs::player_total` besteht aus DREI
/// Summanden, und der erste ist der, der die Musterreihen sieht:
///
/// ```text
/// solve_round_final_score(state, pi)                  <- dieser hier
///   + scoring_progress(..)                            <- MOSAIC_WERTUNG_SHAPING_W
///   + projected_unplaceable_penalty(..)               <- MOSAIC_WERTUNG_FLOOR_W
/// ```
///
/// Warum meine beiden Eigenbauten (`MOSAIC_ENDAWARE_W`/`tiling_vorausschau`,
/// `MOSAIC_MUSTERREIHEN_W`/`crate::scoring::musterreihen_fortschritt`) INZWISCHEN
/// entfernt sind (2026-08-13, PREREG_scoring_plate_injection.md Abschnitt N7):
/// gemessen taten sie nichts. `MOSAIC_ENDAWARE_W` bei w=0,1 gab -0,07 Punkte
/// (t=-0,07), bei w=0,3 -2,16 (t=-1,21) ohne jeden Plattengewinn;
/// `MOSAIC_MUSTERREIHEN_W` bei w=0,1 -0,84 (t=-0,69). Dieser Traeger hier blieb
/// unangetastet -- er ist der aus der Heuristik uebernommene, nicht selbst
/// erfundene Term.
pub fn tiling_weight() -> f64 {
    static CELL: std::sync::OnceLock<f64> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| read_f64_env("MOSAIC_TILING_W", 0.0))
}

/// Aus den HEUTIGEN Musterreihen erreichbare Platzierungspunkte.
///
/// `solve_round_final_score` liefert *aktueller Punktestand + max. Tiling-Punkte
/// + feste Boden-/Marker-Strafen* (`tiling_solver.rs:398`: `p.score + penalty +
/// solve_max_tiling_points`). Der Punktestand wird ABGEZOGEN -- Nutzer-Entscheid
/// "nur der Tiling-Anteil". Zwei Gruende, und beide zaehlen:
///  1. Er ist fuer alle Geschwisterzuege GLEICH und traegt zur Zugwahl nichts bei.
///  2. Er liegt bei ~50 Punkten und wuerde `tanh(pts/50)` saettigen, womit auch
///     der variable Rest keine Wirkung mehr haette.
///
/// Die Differenz ist keine Erfindung: `tiling_solver.rs:1069` prueft genau sie
/// (`solve_round_final_score(&s,0) - s.players[0].score == 3`). Uebrig bleiben
/// Tiling-Punkte + feste Strafen, beides drafting-abhaengig, und beides in
/// Punkten -- dieselbe Einheit wie die Nachbarterme.
///
/// Ueberschneidung mit `projected_unplaceable_penalty` ist gewollt und spiegelt
/// die Heuristik: `penalty` sind die Strafen der SCHON gebrochenen Fliesen, der
/// andere Term preist die Fliesen in Reihen, die sich nicht mehr platzieren
/// lassen -- der Solver sieht dort nur "0 Punkte", nicht die Busse.
pub(crate) fn tiling_potenzial(state: &GameState, pi: usize) -> f64 {
    (crate::tiling_solver::solve_round_final_score(state, pi) - state.players[pi].score) as f64
}

pub fn scoring_round_gain() -> f64 {
    static CELL: std::sync::OnceLock<f64> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| read_f64_env("MOSAIC_WERTUNG_ROUND_GAIN", 0.0))
}

/// Baustein 3 (`MOSAIC_WERTUNG_SCALE_PROFILE`, `PREREG_shaping_scale_per_
/// round.md` par.4): `profil_r` je Runde 1..5, gemessen aus dem
/// Punktestand-ANTEIL (nicht dem Punktestand selbst) ueber 22 Arena-Logs
/// (par.1) -- `SCALE_r = WERTUNG_SHAPING_SCALE * profil_r`.
const WERTUNG_SCALE_PROFILE: [f64; 5] = [0.083, 0.172, 0.327, 0.515, 0.825];

/// Laufzeit-Wert von `MOSAIC_WERTUNG_SCALE_PROFILE` -- Default **aus**
/// (ungesetzt, leer oder `"0"`) = flacher Nenner `WERTUNG_SHAPING_SCALE`
/// (50.0) fuer ALLE Runden, byte-identisches Bestandsverhalten. Gesetzt auf
/// `"1"` oder `"an"` = das rundenabhaengige Profil (par.4) gilt fuer den
/// Wertungsplatten-/Spezialfeld-Term in [`apply_scoring_shaping_full`] --
/// NICHT fuer den Strafleisten- oder den Tiling-Term, siehe dortige
/// Begruendung (par.6a).
pub fn scoring_scale_profile_active() -> bool {
    static CELL: std::sync::OnceLock<bool> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| match std::env::var("MOSAIC_WERTUNG_SCALE_PROFILE") {
        Ok(raw) => {
            let t = raw.trim();
            t == "1" || t.eq_ignore_ascii_case("an")
        }
        Err(_) => false,
    })
}

/// `SCALE_r` fuer Runde `round_number` (1-basiert, geklemmt auf 1..5, gleiche
/// Klemmung wie die bestehende `t`-Berechnung in [`apply_scoring_shaping_full`]).
/// Reine Funktion (kein Env-Zugriff) -- `profile_active` als Parameter, damit
/// Tests das OnceLock nicht umgehen muessen (gleiches Trennungsmuster wie
/// `apply_scoring_shaping_full` selbst).
pub(crate) fn scoring_scale_for_round(round_number: u32, profile_active: bool) -> f64 {
    if !profile_active {
        return WERTUNG_SHAPING_SCALE;
    }
    let idx = (round_number.clamp(1, 5) - 1) as usize;
    WERTUNG_SHAPING_SCALE * WERTUNG_SCALE_PROFILE[idx]
}

/// Reine Formel hinter [`apply_scoring_shaping`], OHNE Env-Var-Zugriff --
/// Gewichte/Exponenten als Parameter statt aus dem OnceLock-Cache gelesen,
/// gleiches Trennungsmuster wie `blended_leaf_win_prob`/`_with` (siehe
/// dortige Doku: ein Test, der den Env-Var-Cache nach dem ersten Zugriff
/// umstellen will, kaeme nie an sein Ziel). Frueher ueber zwei Test-Huellen
/// `apply_wertung_shaping_with`/`_with_alphas` aufgerufen (ausserhalb von
/// Tests nie gebraucht, deshalb entfernt -- Tests rufen diese Funktion jetzt
/// direkt mit `&[w; 8]`/`&[alpha; 8]` und den Gegenterm-Defaults `0.0`).
///
/// Fruehausstieg bei ALLEN Gewichten `== 0.0`: gibt `value` UNVERAENDERT
/// zurueck -- kein `scoring_progress_alpha`-Aufruf, kein `tanh`, keine
/// Rundung, also GARANTIERT numerisch identisch zum Vor-Additiv-Bestand
/// (exakt das Muster, das `blended_leaf_win_prob_with`s bestehender
/// `w == 0.0`-Kurzschluss schon fuer sein eigenes Gewicht vorgibt).
///
/// Skalierung: `scoring_progress_alpha` liefert PUNKTE, `value` sind
/// Gewinnwahrscheinlichkeiten -- Normierung ueber `tanh(punkte /
/// WERTUNG_SHAPING_SCALE)` (siehe dortige Doku), gleiche Konvention wie
/// `floor_shaping_delta`/`plate_shaping_delta`. JEDER Spieler bekommt seinen
/// EIGENEN, unabhaengigen Shift aus seinem EIGENEN Brett (`state.players[i]`)
/// -- keine mine-minus-theirs-Kopplung wie beim Plattenshaping oben, siehe
/// Modul-Kommentar. Ergebnis wird wie die bestehende Floor-/Platten-Additiv-
/// Logik auf `[0,1]` geklemmt.
///
/// Volle Form: Gewicht UND Exponent je Kriterium, plus den absoluten
/// Gegenterm (Strafleiste `floor_w`). Ein Gewicht 0 schaltet das jeweilige
/// Kriterium/Additiv vollstaendig ab -- das ist die Voraussetzung fuer den
/// Nutzer-Versuchsaufbau (je Satz nur EIN Kriterium injiziert).
///
/// Baustein 3 (`scale_profile_active`, `MOSAIC_WERTUNG_SCALE_PROFILE`,
/// `PREREG_shaping_scale_per_round.md` par.4/par.5/par.6a): wirkt NUR auf den
/// Nenner der Wertungsplatten-/Spezialfeld-Terme (die `bei`-Closure unten).
/// Der Strafleisten-Term (`floor_w`) und der Tiling-Term (`tiling_w`) bleiben
/// AUSDRUECKLICH auf dem flachen Nenner `WERTUNG_SHAPING_SCALE`, unabhaengig
/// vom Profil-Knopf -- par.6a Praezisierung (REGEL 0, geprueft, weicht vom
/// Prereg-Wortlaut ab): der DEFAULT von `floor_w` selbst
/// (`scoring_floor_weight()`/`MOSAIC_WERTUNG_FLOOR_W`) ist **0.0**, nicht
/// 0,3 -- der im Prereg zitierte Beleg "`floor_shaping_weight = 0,3`,
/// engine_config" (`lib.rs:631`) meint `FLOOR_SHAPING_WEIGHT`/
/// `floor_shaping_weight()` (`MOSAIC_FLOOR_SHAPING_W`), das GANZ ANDERE Floor-
/// Additiv in `blended_leaf_win_prob`/`floor_shaping_delta` -- eine separate
/// Funktion, die diese Closure gar nicht durchlaeuft. Der `floor_w`-Zweig
/// hier ist also per Default TOT (der fruehe `floor_w == 0.0`-Zweig unten
/// greift ohnehin nicht, weil der ganze Ausdruck schon durch den
/// Gesamt-Fruehausstieg abgefangen wird). Der flache Nenner bleibt trotzdem
/// EXPLIZIT gepinnt -- als Schutz fuer den Fall, dass jemand `MOSAIC_WERTUNG_
/// FLOOR_W` UND das Profil gleichzeitig setzt (nicht-default Kombination),
/// und weil `tiling_w` (`MOSAIC_TILING_W`, ebenfalls Default 0.0) aus
/// Symmetriegruenden analog behandelt wird.
pub(crate) fn apply_scoring_shaping_full(
    value: [f64; 2], state: &GameState, ws: &[f64; 8], alphas: &[f64; 8], round_gain: f64,
    floor_w: f64, tiling_w: f64, scale_profile_active: bool,
) -> [f64; 2] {
    if ws.iter().all(|w| *w == 0.0) && floor_w == 0.0 && tiling_w == 0.0 {
        return value;
    }
    let mut out = value;
    for i in 0..2 {
        // ALLE ACHT Kriterien in EINEM Term, EIN Gewicht (Nutzer-Korrektur
        // 2026-08-11: *"ich dachte das haengt zusammen"*).
        //
        // WARUM es zusammenhaengt: Kriterium 6 (Spezialfelder) IST eine der acht
        // Wertungsplatten. Es steckt aus Doppelzaehlungs-Gruenden nicht in
        // `scoring_progress_per_criterion` (dort liefert es 0), sondern in
        // `unlock_progress_beta` -- weil sein ⭐-Anteil UNGEGATET zahlt
        // (Grundwertung, Rasterreihe 1..6) und nur der -3-Anteil an der aktiven
        // Platte haengt. Vorher hingen die beiden an ZWEI Gewichten, und eine
        // Vorregistrierung von mir hat eines davon auf 0 gesetzt -- damit war
        // "alle Wertungsplatten injizieren" auf sieben verkuerzt.
        //
        // `alphas[6]` ist jetzt auch der Exponent des Freischalt-Terms: dieselbe
        // Bedeutung (wie steil zaehlt Teilfortschritt), nur mit Kapazitaet 3
        // statt 6. Damit deckt die achtstellige alpha-Liste tatsaechlich alle
        // acht Platten -- die Form, die der Versuchsplan "je Platte 20 Partien,
        // nur deren alpha" braucht.
        // Je Kriterium EINZELN gewichtet: `ws[k] == 0` laesst Kriterium k
        // vollstaendig weg. Deshalb je Kriterium ein eigener Aufruf mit
        // einelementiger tile_ids-Liste statt einem Sammelaufruf.
        // `w` muss AUSSEN am tanh bleiben, sonst ist es nicht mehr die
        // Obergrenze der Verschiebung: `tanh(w*P/50)` saettigt gegen 1
        // unabhaengig von w, `w*tanh(P/50)` gegen w. Bei Gewichten je Kriterium
        // gibt es kein einzelnes w -- also das GROESSTE aussen und innen darauf
        // normieren. Gleichmaessiger Fall: reproduziert `w*tanh(SUM pts/50)`
        // exakt. Isolierung (eins auf 1, Rest 0): `1*tanh(pts_k/50)`.
        // SUMME JE TERM, jeder mit EIGENEM Gewicht in EIGENER Schranke:
        //
        //     shift = SUM_term  w_term * tanh(P_term / SCALE)
        //
        // FEHLER, DER DAMIT BEHOBEN IST (2026-08-12, vom Nutzer an
        // bit-identischen Zellen erkannt): vorher gab es EIN gemeinsames
        // `pts` und davor ein `skala = max(alle Gewichte)`, innen normiert auf
        // `ws[k] / max(ws)`. Bei genau EINEM Null-verschiedenen
        // Kriteriumsgewicht `w` kuerzte sich `w` dadurch ZWEIMAL heraus --
        // innen als `w/w = 1`, aussen weil `max(w, floor_w, tiling_w)` bei
        // floor_w=tiling_w=1 immer 1 ergab. `w` war in der isolierten
        // Injektion wirkungslos, und nur `alpha` wirkte.
        //
        // Beide Bausteine waren einzeln begruendet: die Normierung, damit der
        // gleichmaessige Fall `w*tanh(SUM P/50)` exakt reproduziert; das `max`,
        // damit ein allein gesetzter Zusatzknopf nicht wirkungslos ist.
        // Zusammen hoben sie sich auf.
        //
        // Warum das Gewicht AUSSEN am jeweiligen tanh bleibt: `tanh(w*P/50)`
        // saettigt gegen 1 unabhaengig von w, `w*tanh(P/50)` gegen w -- nur die
        // zweite Form macht das Gewicht zur echten Obergrenze der Verschiebung.
        // Je Term ein eigenes tanh statt eines gemeinsamen, damit kein Term die
        // Schranke eines anderen mitbenutzt.
        //
        // NICHT rueckwaertskompatibel zum gleichmaessigen Fall: dort liefert die
        // neue Form `SUM_k w*tanh(P_k/50)` statt `w*tanh(SUM_k P_k/50)`. Gleiche
        // Richtung und Monotonie, andere Zahlen. Die Dosis-Kurve vom 11.08.
        // (w=0,03/0,1/0,3/1,0 gleichmaessig) ist damit unter der ALTEN Formel
        // gemessen und nicht mit neuen Zahlen vergleichbar.
        let t = ((state.round_number.clamp(1, 5) - 1) as f64) / 4.0;
        // Baustein 3: Nenner der Wertungsplatten-/Spezialfeld-Terme, gesteuert
        // von `MOSAIC_WERTUNG_SCALE_PROFILE` -- bei inaktivem Knopf identisch
        // zu `WERTUNG_SHAPING_SCALE` (byte-identisches Bestandsverhalten).
        let scale_r = scoring_scale_for_round(state.round_number, scale_profile_active);
        let bei = |x: f64| (x / scale_r).tanh();
        // Strafleisten-/Tiling-Term bleiben IMMER auf dem flachen Nenner --
        // siehe Funktionskommentar oben (par.6a-Praezisierung).
        let bei_flat = |x: f64| (x / WERTUNG_SHAPING_SCALE).tanh();
        let mut shift = 0.0;

        // Wertungsplatten, je Kriterium einzeln gewichtet und einzeln begrenzt.
        // `ws[k] == 0` laesst Kriterium k vollstaendig weg -- die Voraussetzung
        // fuer den Nutzer-Versuchsaufbau (je Satz nur EIN Kriterium injiziert).
        for &id in state.scoring_tile_ids.iter() {
            let k = (id as usize).min(7);
            if ws[k] == 0.0 {
                continue;
            }
            shift += ws[k] * bei(crate::scoring::scoring_progress_per_criterion(
                &state.players[i], &[id], alphas, state.round_number, round_gain,
            ));
        }
        // Spezialfelder: der Bonus-Anteil zahlt UNGEGATET, also unabhaengig von
        // `scoring_tile_ids` -- er haengt an `ws[6]`, nicht am Liegen der Platte.
        if ws[6] != 0.0 {
            let beta6 = alphas[6] * (1.0 + round_gain * t);
            shift += ws[6] * bei(crate::scoring::unlock_progress_beta(
                &state.players[i], &state.scoring_tile_ids, beta6,
            ));
        }
        // Strafleisten-Gegenterm: NEGATIV (Summe der BROKEN_PENALTIES).
        // Flacher Nenner (`bei_flat`), NICHT `scale_r` -- siehe
        // Funktionskommentar (par.6a).
        if floor_w != 0.0 {
            shift += floor_w * bei_flat(
                crate::round_end::projected_unplaceable_penalty(&state.players[i]) as f64);
        }
        // Tiling-Potenzial: der Musterreihen-Traeger aus der Heuristik.
        // Flacher Nenner, analog zum Strafleisten-Term (siehe oben).
        if tiling_w != 0.0 {
            shift += tiling_w * bei_flat(tiling_potenzial(state, i));
        }
        out[i] = (value[i] + shift).clamp(0.0, 1.0);
    }
    out
}

/// Laufzeit-Wrapper von [`apply_wertung_shaping_with`], liest `w`/`alpha` aus
/// den Prozess-weiten OnceLock-Caches (`scoring_shaping_weight()`/
/// `wertung_shaping_alpha()`) -- gleiches Trennungsmuster wie
/// `blended_leaf_win_prob`/`_with`. Aufrufstellen: `net_leaf_eval` (deckt
/// damit auch alle DESSEN Aufrufer ab -- `round_transition_deep.rs`,
/// `self_play.rs`, den Chance-Node-Zweig in `make_node` selbst) und
/// `make_node`s eigener `LeafEval::Net`-Zweig (der Haupt-Suchpfad, der NICHT
/// ueber `net_leaf_eval` laeuft, siehe dortige Duplizierung der Blend-Logik).
pub(crate) fn apply_scoring_shaping(value: [f64; 2], state: &GameState) -> [f64; 2] {
    apply_scoring_shaping_full(
        value, state, &scoring_shaping_weights(), &scoring_shaping_alphas(), scoring_round_gain(),
        scoring_floor_weight(), tiling_weight(), scoring_scale_profile_active(),
    )
}

// ── Ownership-Verbraucher Teil 1: Drafting/Blattbewertung ───────────────────
// `evaluations/PREREG_ownership_consumer.md` §2/§5/§6, freigegeben durch Tor A
// (`PREREG_ownership_corpus.md` §10). Der ZWEITE Pol neben dem Heuristik-Pol
// (`apply_scoring_shaping` oben): dort misst `scoring_progress_per_criterion`
// den IST-Fortschritt, hier prognostiziert das Netz die VOLLENDUNG. Gleiche
// Shift-Form, gleicher Rechen-Ort, eigener Regler.
//
// NUR die Drafting-Seite. Der Tiling-Verbraucher (§3, marginale Feldwerte im
// Solver) ist AUSDRUECKLICH nicht Teil dieses Schritts.

/// `MOSAIC_OWNERSHIP_W` -- der Zwei-Pole-Regler `w_own`. Default **0,0** =
/// Verbraucher TOT (Fruehausstieg in [`apply_ownership_shaping_full`], kein
/// Sigmoid, kein tanh, keine Rundung -> byte-identisches Bestandsverhalten,
/// Task-#28-Muster, siehe `blended_leaf_win_prob_with`s `w == 0.0`-Kurzschluss).
///
/// Prozessweit einmalig gelesen (`OnceLock`), wie alle Nachbarregler --
/// ein Test, der den Wert nach dem ersten Zugriff umstellen will, kaeme nie an
/// sein Ziel; die Formel ist deshalb ueber
/// [`apply_ownership_shaping_full`] ohne Env-Var direkt pruefbar.
pub fn ownership_weight() -> f64 {
    static CELL: std::sync::OnceLock<f64> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| read_f64_env("MOSAIC_OWNERSHIP_W", 0.0))
}

/// `MOSAIC_OWNERSHIP_GEW` -- Gewicht JE KRITERIUM `gew_k` innerhalb des
/// Ownership-Pols. Acht Werte in Kriterien-Reihenfolge 0..7, ein einzelner
/// gilt fuer alle; falsche Laenge wird VERWORFEN (mit Meldung), nicht
/// teilgelesen. Format und Haerte exakt wie `MOSAIC_WERTUNG_SHAPING_W`/
/// `MOSAIC_TILING_PLATTEN_GEW`.
///
/// Default **alle 1,0**, NICHT 0,0: `w_own` ist der Hauptschalter (§2), die
/// Kriteriengewichte sind der Isolier-Knopf darueber ("nur die Vertikale" =
/// `0,1,0,0,0,0,0,0`). Waere der Default 0, waere `w_own` allein wirkungslos
/// -- genau die still-wirkungslose Kombination, die bei
/// `MOSAIC_WERTUNG_SHAPING_W` schon einmal eine Messung entwertet hat.
///
/// Stelle 7 ist per Konstruktion wirkungslos: `expected_plate_points` liefert
/// fuer Kriterium 7 immer 0 (Farbinformation steckt nicht im Ownership-Ziel,
/// `neural_net.py:958`).
pub fn ownership_weights() -> [f64; 8] {
    static CELL: std::sync::OnceLock<[f64; 8]> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| {
        let mut out = [1.0f64; 8];
        let Ok(raw) = std::env::var("MOSAIC_OWNERSHIP_GEW") else { return out };
        let parts: Vec<&str> = raw.split(',').map(|p| p.trim()).filter(|p| !p.is_empty()).collect();
        let vals: Option<Vec<f64>> = parts.iter().map(|p| p.parse::<f64>().ok()).collect();
        match vals.as_deref() {
            Some([one]) => out = [*one; 8],
            Some(v) if v.len() == 8 => out.copy_from_slice(v),
            _ => eprintln!(
                "MOSAIC_OWNERSHIP_GEW={raw:?} ignoriert -- erwartet 1 oder 8 Zahlen, Default 1,0 je Kriterium gilt"
            ),
        }
        out
    })
}

/// Baustein 2 (`MOSAIC_OWNERSHIP_SCALE`, `PREREG_reachability_target.md`
/// par.6 / `PREREG_shaping_scale_per_round.md` par.3a): Nenner JE KRITERIUM
/// fuer den Ownership-Pol, ersetzt die feste `WERTUNG_SHAPING_SCALE` (50.0)
/// im `tanh(E_k / scale_k)`-Term. Format und Haerte exakt wie
/// `scoring_shaping_alphas`/`ownership_weights`: 1 oder 8 kommagetrennte
/// Zahlen, falsche Laenge wird VERWORFEN (mit Meldung), nicht teilgelesen.
///
/// Default alle `WERTUNG_SHAPING_SCALE` (50.0) = byte-identisches
/// Bestandsverhalten. Anlass (par.6, gemessen): `tanh(0,082/50)` = 0,0016
/// gegen eine q-Eigenspreizung der Suche von 0,078 -- Faktor ~50 zu leise.
/// Gemessene Nenner fuer Arm S: k0 ~17, k1 ~1, k2 ~0,3 statt einheitlich 50.
pub fn ownership_scale() -> [f64; 8] {
    static CELL: std::sync::OnceLock<[f64; 8]> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| {
        let mut out = [WERTUNG_SHAPING_SCALE; 8];
        let Ok(raw) = std::env::var("MOSAIC_OWNERSHIP_SCALE") else { return out };
        let parts: Vec<&str> = raw.split(',').map(|p| p.trim()).filter(|p| !p.is_empty()).collect();
        let vals: Option<Vec<f64>> = parts.iter().map(|p| p.parse::<f64>().ok()).collect();
        match vals.as_deref() {
            Some([one]) => out = [*one; 8],
            Some(v) if v.len() == 8 => out.copy_from_slice(v),
            _ => eprintln!(
                "MOSAIC_OWNERSHIP_SCALE={raw:?} ignoriert -- erwartet 1 oder 8 Zahlen, Default {WERTUNG_SHAPING_SCALE} je Kriterium gilt"
            ),
        }
        out
    })
}

/// Einmalige Warnung, wenn `w_own > 0` gesetzt ist, das geladene Netz aber
/// keinen brauchbaren Ownership-Kopf liefert -- Stufe 2 des
/// `blended_leaf_win_prob`-Musters (net_mcts.rs, `warn_missing_opp_head_once`):
/// laut scheitern statt still nichts tun. Der Verbraucher verhaelt sich danach
/// wie `w_own = 0`.
fn warn_ownership_head_unusable_once(len: usize) {
    static WARNED: std::sync::OnceLock<()> = std::sync::OnceLock::new();
    WARNED.get_or_init(|| {
        eprintln!(
            "⚠️  MOSAIC_OWNERSHIP_W ist gesetzt, aber der Ownership-Kopf des geladenen Netzes ist \
             unbrauchbar (Laenge {len}, gebraucht werden mindestens {min} Werte = 2 x 36 Felder). \
             Der Ownership-Pol verhaelt sich wie w_own=0. Diese Meldung erscheint nur einmal je Prozess.",
            min = 2 * crate::scoring::OWNERSHIP_FIELDS
        );
    });
}

/// Sigmoid -- der Ownership-Kopf endet auf `nn.Linear` OHNE Aktivierung
/// (`neural_net.py:2390-2394`) und wird mit
/// `binary_cross_entropy_with_logits` trainiert (`train.py:1171-1172`), die
/// Kopf-Ausgaben sind also LOGITS. Die Umrechnung gehoert hierher, nicht in
/// `net.rs` (das reicht Koepfe roh durch).
///
/// `pub(crate)` seit Teil 2 (Tiling): `self_play.rs::ownership_tiling_marginals`
/// dekodiert dieselben Logits fuer die Wurzelkarte des Tiling-Zuges. Eine
/// zweite lokale Kopie waere hier die schlechtere Wahl -- beide Pole muessen
/// dieselbe Umrechnung benutzen, sonst haben sie verschiedene Karten.
pub(crate) fn sigmoid(x: f64) -> f64 {
    1.0 / (1.0 + (-x).exp())
}

/// Reine Formel hinter [`apply_ownership_shaping`], OHNE Env-Var-Zugriff --
/// gleiches Trennungsmuster wie `apply_scoring_shaping_full`/
/// `blended_leaf_win_prob_with` (die OnceLock-Getter sind pro Prozess nur
/// einmal lesbar, ein env-basierter Test kaeme nie an sein Ziel).
///
/// ```text
/// shift_i = w_own * SUM_k gew_k * tanh(E_k(i) / 50)
/// out_i   = clamp(value_i + shift_i, 0, 1)
/// ```
///
/// -- dieselbe Form, dieselbe Skala (`WERTUNG_SHAPING_SCALE`) und dasselbe
/// "Gewicht AUSSEN am tanh" wie der Heuristik-Pol (siehe dortige Begruendung:
/// `tanh(w*P/50)` saettigt gegen 1 unabhaengig von w, `w*tanh(P/50)` gegen w).
///
/// PERSPEKTIVE: `ownership` ist die Karte des MOVER-Passes, ego-perspektivisch
/// -- `[0:36]` gehoert `state.current_player`, `[36:72]` dem anderen Spieler
/// (`neural_net.py:1825-1840`, "erst der Spieler am Zug, dann der Gegner").
/// Jeder Spieler bekommt seinen eigenen, unabhaengigen Shift aus seiner
/// eigenen Haelfte -- keine mine-minus-theirs-Kopplung, exakt wie der
/// Heuristik-Pol.
///
/// DREI STUFEN, Muster von `blended_leaf_win_prob_with`:
///   1. `w_own == 0.0` (Default) -> `value` UNVERAENDERT zurueck. Kein
///      Sigmoid, kein tanh, keine Rundung -> byte-identisch.
///   2. `w_own > 0`, aber der Kopf ist unbrauchbar (fehlt ganz oder ist
///      schmaler als 72) -> einmalige Warnung, dann wie Stufe 1. Deckt den
///      72er- UND den 140er-Kopf ab: gebraucht werden nur die ersten 72
///      Werte, alles dahinter (Konjunktionen) wird hier nicht gelesen.
///   3. `w_own > 0` und Kopf brauchbar -> Shift wie oben.
///
/// WARUM DER 140er-KOPF NICHT DIREKT GELESEN WIRD (bewusste Wahl, siehe
/// Bericht): `expected_plate_points` rechnet das PRODUKT der Feld-Randwahr-
/// scheinlichkeiten, obwohl der Konjunktionsteil des 140er-Kopfs
/// (`neural_net.py::_conjunctions_from_dome`, Index `[72:106]` ich /
/// `[106:140]` Gegner) genau diese Konjunktionen direkt schaetzt und laut
/// dortigem Docstring GENAUER ist ("P(alle 6 Felder) ist nicht das Produkt
/// der Einzelwahrscheinlichkeiten"). Drei Gruende fuer die Produktform:
///   - §2 des Vertrags schreibt sie woertlich vor;
///   - sie ist kopfbreiten-agnostisch, der amtierende Champion
///     (`v21_2d_brierbest`, 72 breit) und die Sweep-Checkpoints (140 breit)
///     nehmen denselben Codepfad -- kein zweiter, nur halb getesteter Zweig;
///   - der Tiling-Verbraucher (§3) braucht ohnehin marginale Feldwerte
///     (`punkte_k * PROD ueber die UEBRIGEN Felder`), die aus einer
///     Konjunktions-Ausgabe gar nicht ableitbar waeren.
/// Die Konjunktions-Ausgaenge sind damit heute UNGENUTZT -- ein moeglicher
/// zweiter Regler-Arm, kein Teil dieses Auftrags.
pub(crate) fn apply_ownership_shaping_full(
    value: [f64; 2],
    state: &GameState,
    ownership: &[f32],
    w_own: f64,
    gew: &[f64; 8],
    use_conj: bool,
    scale: &[f64; 8],
) -> [f64; 2] {
    if w_own == 0.0 {
        return value;
    }
    let need = 2 * crate::scoring::OWNERSHIP_FIELDS;
    if ownership.len() < need {
        warn_ownership_head_unusable_once(ownership.len());
        return value;
    }
    let mut out = value;
    for i in 0..2 {
        // Ego-Haelfte des ZIEHENDEN Spielers ist `[0:36]`, die des anderen
        // `[36:72]` -- siehe Funktionskommentar "PERSPEKTIVE".
        let base = if i == state.current_player { 0 } else { crate::scoring::OWNERSHIP_FIELDS };
        let mut p_own = [0.0f64; crate::scoring::OWNERSHIP_FIELDS];
        for (f, slot) in p_own.iter_mut().enumerate() {
            *slot = sigmoid(ownership[base + f] as f64);
        }
        // FORMUMSCHALTUNG (PREREG_conjunction_terms.md par.4): die konjunktiven
        // Kriterien aus den GELERNTEN Atomen statt aus dem Produkt der
        // Feldwahrscheinlichkeiten. Braucht den 140er-Kopf; bei schmalerem Kopf
        // Rueckfall auf die Produktform MIT Warnung -- still zurueckfallen wuerde
        // heissen, dass ein Knopf beim einen Checkpoint wirkt und beim anderen
        // nicht, und das waere in der Arena von einem Dosiseffekt nicht zu
        // unterscheiden (par.4.3).
        let conj_width = 2 * (crate::scoring::OWNERSHIP_FIELDS
                               + crate::scoring::CONJUNCTION_ATOMS);
        let e = if use_conj && ownership.len() >= conj_width {
            let cbase = 2 * crate::scoring::OWNERSHIP_FIELDS
                + if i == state.current_player { 0 } else { crate::scoring::CONJUNCTION_ATOMS };
            let mut p_conj = [0.0f64; crate::scoring::CONJUNCTION_ATOMS];
            for (a, slot) in p_conj.iter_mut().enumerate() {
                *slot = sigmoid(ownership[cbase + a] as f64);
            }
            crate::scoring::expected_plate_points_conj(
                &state.players[i], &p_own, &p_conj, &state.scoring_tile_ids,
            )
        } else {
            if use_conj {
                warn_ownership_conj_unavailable_once(ownership.len());
            }
            crate::scoring::expected_plate_points(
                &state.players[i], &p_own, &state.scoring_tile_ids,
            )
        };
        let mut shift = 0.0;
        for k in 0..8 {
            if gew[k] == 0.0 {
                continue;
            }
            shift += gew[k] * (e[k] / scale[k]).tanh();
        }
        out[i] = (value[i] + w_own * shift).clamp(0.0, 1.0);
    }
    out
}

/// Laufzeit-Wrapper von [`apply_ownership_shaping_full`], liest `w_own`/`gew`/
/// `scale` aus den prozessweiten OnceLock-Caches. Aufrufstellen: `net_leaf_eval`
/// und `node_from_net_outputs`s `LeafEval::Net`-Zweig -- dieselben zwei Stellen
/// wie [`apply_scoring_shaping`], jeweils DIREKT dahinter.
pub(crate) fn apply_ownership_shaping(value: [f64; 2], state: &GameState, ownership: &[f32]) -> [f64; 2] {
    apply_ownership_shaping_full(value, state, ownership, ownership_weight(),
                                 &ownership_weights(), ownership_conj(), &ownership_scale())
}

/// `MOSAIC_OWNERSHIP_CONJ` -- Formumschaltung des Ownership-Verbrauchers.
/// Default **0** = Produktform, byte-identisches Bestandsverhalten. 1 = die
/// konjunktiven Kriterien kommen aus den gelernten Atomen
/// (`scoring::expected_plate_points_conj`).
///
/// Das ist KEINE Dosis, sondern ein Schalter: die Staerke regelt weiterhin
/// `MOSAIC_OWNERSHIP_W`. Getrennt gehalten, damit Form und Dosis in der Arena
/// einzeln messbar bleiben (PREREG_conjunction_terms.md par.6).
pub(crate) fn ownership_conj() -> bool {
    static CELL: std::sync::OnceLock<bool> = std::sync::OnceLock::new();
    *CELL.get_or_init(|| {
        std::env::var("MOSAIC_OWNERSHIP_CONJ")
            .ok()
            .and_then(|s| s.trim().parse::<f64>().ok())
            .map(|v| v != 0.0)
            .unwrap_or(false)
    })
}

/// Einmalige Warnung, wenn `MOSAIC_OWNERSHIP_CONJ` gesetzt ist, der Kopf aber
/// keinen Konjunktionsteil hat (72 statt 140 breit -- etwa der amtierende
/// Champion). Absichtlich laut: siehe Begruendung an der Aufrufstelle.
fn warn_ownership_conj_unavailable_once(len: usize) {
    static EINMAL: std::sync::Once = std::sync::Once::new();
    EINMAL.call_once(|| {
        eprintln!("[mosaic] WARNUNG: MOSAIC_OWNERSHIP_CONJ ist gesetzt, aber der Ownership-Kopf ist nur {len} breit (noetig: {}). Rueckfall auf die Produktform -- die Formumschaltung ist fuer diesen Checkpoint WIRKUNGSLOS.",
                  2 * (crate::scoring::OWNERSHIP_FIELDS + crate::scoring::CONJUNCTION_ATOMS));
    });
}

// ── Freischalt-Shaping (Nutzer-Auftrag 2026-08-10, Messlage watchlist_v20_
// zwischenlese.md Abschnitt 2) ──────────────────────────────────────────────
// Eigener Knopf, eigene Formel (`unlock_progress_beta`, scoring.rs) --
// UNGEGATET (zahlt unabhaengig von `scoring_tile_ids`, siehe dortiger
// Kommentar), ABSOLUT statt marginal (bewusst KEIN Eltern-Delta wie
// `plate_shaping_marginal` -- eine Differenzform waere potentialbasiert und
// liesse die Zugwahl strukturell unberuehrt, das ist hier explizit NICHT
// gewollt: der Term soll echte Praeferenz fuer Freischalt-Fortschritt in die
// Suche tragen, nicht nur eine neutrale Reparametrisierung sein). Je Spieler
// ABSOLUT wie das Wertungsplatten-Shaping oben (siehe dortiger Kommentar,
// Nutzer-Korrektur 2026-08-11) -- BEIDE Spieler unabhaengig ueber ihr
// EIGENES Brett, kein Cross-Term, keine mine-minus-theirs-Differenz. Gleiche
// Skala (`tanh(x/50.0)`).

/// Default-Gewicht des Freischalt-Shaping-Additivs -- `0.0` = AUS, exakt
/// Bestandsverhalten ohne gesetzte `MOSAIC_UNLOCK_SHAPING_W`.
pub const UNLOCK_SHAPING_WEIGHT: f64 = 0.0;

/// Default-Exponent `beta` fuer `unlock_progress_beta` -- `2.0` (Startwert,
/// analog `WERTUNG_SHAPING_ALPHA`, keine eigene Kalibrierung ueber diesen
/// Default hinaus).
pub const UNLOCK_SHAPING_BETA: f64 = 2.0;
