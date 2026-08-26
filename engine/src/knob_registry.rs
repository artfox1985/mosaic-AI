//! Deklarative Registratur ALLER `MOSAIC_*`-Laufzeit-Knoepfe (Architektur-
//! Fahrplan Punkt 3, Nutzer-Auftrag 2026-08-15).
//!
//! EINE Tabelle ([`KNOBS`]): Name, Default, Status (aktiv/diagnose/tot),
//! Kurzzweck (mit Pruefstelle `datei:zeile`, Stand 2026-08-15), Beleg-/
//! Prereg-Verweis. Export nach Python via `knob_registry_json()` (`lib.rs`,
//! Muster `engine_config_json`); Markdown-Doku via
//! `tools/generate_knob_docs.py` (parst diese Datei direkt, siehe dort).
//!
//! MINIMAL-INVASIV: die bestehenden `OnceLock`-Getter der Module bleiben
//! unangetastet -- diese Datei LIEST keine Env-Vars, sie DOKUMENTIERT sie.
//! Die Kopplung an den Code sichert der Waechter-Test unten
//! (`all_mosaic_env_vars_in_code_are_registered`): jeder im Quelltext
//! (engine/src + *.py) vorkommende `MOSAIC_*`-Name ohne Registratur-Eintrag
//! ist ein Testfehler -- kein stiller Knopf-Wildwuchs mehr. Die Gegenrichtung
//! (`registered_non_dead_knobs_exist_in_code`) verhindert veraltete
//! Eintraege: ein nicht-toter Eintrag, dessen Name nirgends mehr im Code
//! steht, ist ebenfalls ein Testfehler.
//!
//! FORMAT-VERTRAG mit `tools/generate_knob_docs.py`: jeder Eintrag steht als
//! EINE Zeile `KnobEntry { name: "...", default: "...", status:
//! KnobStatus::..., purpose: "...", prereg: "..." },` in [`KNOBS`] -- der
//! Generator parst genau dieses Muster. Mehrzeilige Eintraege brechen ihn.

/// Status eines Knopfs -- drei Werte aus dem Auftrag plus `Geplant`:
/// - `Aktiv`: verdrahteter Laufzeit-Hebel (Default kann an ODER aus sein).
/// - `Diagnose`: Mess-/Untersuchungs-Knopf, Default AUS, NIE im Gating.
/// - `Tot`: wirkungslos (Warn-Stub) oder entfernt -- nur noch dokumentiert.
/// - `Geplant`: in einem Prereg beschrieben, im Arbeitsbaum (noch) NICHT
///   verdrahtet -- Grep findet den Namen nur in evaluations/, nicht im Code.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum KnobStatus {
    Aktiv,
    Diagnose,
    Tot,
    Geplant,
}

impl KnobStatus {
    pub fn as_str(self) -> &'static str {
        match self {
            KnobStatus::Aktiv => "aktiv",
            KnobStatus::Diagnose => "diagnose",
            KnobStatus::Tot => "tot",
            KnobStatus::Geplant => "geplant",
        }
    }
}

/// Ein Registratur-Eintrag. `default` ist ein BESCHREIBENDER String (der
/// echte Default lebt im jeweiligen Getter -- Pruefstelle in `purpose`),
/// `prereg` der Beleg-Verweis oder `"-"`, wenn es keinen gibt.
#[derive(Debug, Clone, Copy)]
pub struct KnobEntry {
    pub name: &'static str,
    pub default: &'static str,
    pub status: KnobStatus,
    pub purpose: &'static str,
    pub prereg: &'static str,
}

/// Die Registratur. Gruppiert nach Themenblock, innerhalb grob nach Datei.
/// Pruefstellen (`datei:zeile`) sind der Stand 2026-08-15 und driften mit
/// Refactorings -- der Dateiname ist der stabile Teil.
#[rustfmt::skip]
pub const KNOBS: &[KnobEntry] = &[
    // ── Suche / Blattwert (net_mcts.rs) ─────────────────────────────────────
    KnobEntry { name: "MOSAIC_POINTS_UTILITY_W", default: "0.0", status: KnobStatus::Aktiv, purpose: "Utility-Blend-Gewicht w des Punkte-Kopfs; danach per GUI-Regler set_aggression_params setzbar (net_mcts.rs:158)", prereg: "PREREG_task28_aggression.md" },
    KnobEntry { name: "MOSAIC_AGGR_LAMBDA", default: "0.0", status: KnobStatus::Aktiv, purpose: "Denial-Gewicht lambda (Gegner-Punkte-Abzug im Utility-Blend); GUI-Regler wie oben (net_mcts.rs:164)", prereg: "PREREG_task28_aggression.md" },
    KnobEntry { name: "MOSAIC_VALUE_CAL_A", default: "0.0", status: KnobStatus::Aktiv, purpose: "Logit-Shift A der monotonen Value-Kalibrierung (net_mcts.rs:321)", prereg: "STATUS.md Task #30" },
    KnobEntry { name: "MOSAIC_VALUE_CAL_B", default: "1.0", status: KnobStatus::Aktiv, purpose: "Logit-Streckung B der Value-Kalibrierung (net_mcts.rs:327)", prereg: "STATUS.md Task #30" },
    KnobEntry { name: "MOSAIC_ROOT_CHILD_Q", default: "an (=0 schaltet ab)", status: KnobStatus::Aktiv, purpose: "Wurzelkind-Q-Logging ins Self-Play-JSON (net_mcts.rs:219)", prereg: "STATUS.md Task #35" },
    KnobEntry { name: "MOSAIC_FLOOR_SHAPING_W", default: "0.3", status: KnobStatus::Aktiv, purpose: "Gewicht der Floor-Straf-Korrektur am Netz-Blattwert (net_mcts.rs:405)", prereg: "PREREG_search_path_remeasurements.md M1" },
    KnobEntry { name: "MOSAIC_FLOOR_SHAPING_OPP_BIAS", default: "1.0", status: KnobStatus::Aktiv, purpose: "Gegner-Gewichtung des Floor-Shapings, >1 belohnt Zuschieben (net_mcts.rs:422)", prereg: "PREREG_aggression_style_measurement.md E2" },
    KnobEntry { name: "MOSAIC_NUM_DETERMINIZATIONS", default: "1", status: KnobStatus::Aktiv, purpose: "ISMCTS-Weltenzahl k, auf >=1 geklemmt (net_mcts.rs:734)", prereg: "PREREG_ismcts_determinizations.md" },
    KnobEntry { name: "MOSAIC_WERTUNG_SHAPING_W", default: "0.0 (1 oder 8 Werte)", status: KnobStatus::Aktiv, purpose: "Wertungsplatten-EGO-Shaping-Gewicht je Kriterium (net_mcts.rs:1225)", prereg: "PREREG_scoring_plate_injection.md" },
    KnobEntry { name: "MOSAIC_WERTUNG_ALPHA", default: "2.0 (1 oder 8 Werte)", status: KnobStatus::Aktiv, purpose: "Formungs-Exponent alpha je Kriterium (net_mcts.rs:1264)", prereg: "PREREG_scoring_plate_injection.md" },
    KnobEntry { name: "MOSAIC_WERTUNG_ROUND_GAIN", default: "0.0", status: KnobStatus::Aktiv, purpose: "rundenabhaengige Anhebung aller Alphas (net_mcts.rs:1360)", prereg: "PREREG_scoring_plate_injection.md" },
    KnobEntry { name: "MOSAIC_WERTUNG_FLOOR_W", default: "0.0", status: KnobStatus::Aktiv, purpose: "Strafleisten-Gegenterm im Wertungsplatten-Shaping (net_mcts.rs:1306)", prereg: "PREREG_scoring_plate_injection.md" },
    KnobEntry { name: "MOSAIC_TILING_W", default: "0.0", status: KnobStatus::Aktiv, purpose: "Tiling-Potenzial-Term (Heuristik-Summand solve_round_final_score) im Shaping (net_mcts.rs:1332)", prereg: "PREREG_scoring_plate_injection.md" },
    KnobEntry { name: "MOSAIC_WERTUNG_SCALE_PROFILE", default: "aus (=0/leer; 1 oder an = Rundenprofil)", status: KnobStatus::Diagnose, purpose: "Baustein 3: rundenabhaengiger Nenner SCALE_r=50*profil_r fuer den Wertungsplatten-/Spezialfeld-Term (Pfad A); Strafleisten-/Tiling-Term bleiben auf dem flachen Nenner (net_mcts.rs, scoring_scale_profile_active)", prereg: "PREREG_shaping_scale_per_round.md par.4/par.6a" },
    KnobEntry { name: "MOSAIC_WERTUNG_STREUUNG_MAX", default: "0.0 (aus)", status: KnobStatus::Aktiv, purpose: "partieweise Streuung des Shaping-Gewichts aus dem Partie-Seed, Wert in [0,max] (net_mcts.rs:1154)", prereg: "PREREG_ownership_corpus.md" },
    KnobEntry { name: "MOSAIC_OWNERSHIP_W", default: "0.0 (aus)", status: KnobStatus::Aktiv, purpose: "Zwei-Pole-Regler w_own: Blatt-Shift aus den erwarteten Plattenpunkten E_k des Ownership-Kopfs (net_mcts.rs, ownership_weight)", prereg: "PREREG_ownership_consumer.md par.2" },
    KnobEntry { name: "MOSAIC_OWNERSHIP_GEW", default: "1.0 (1 oder 8 Werte)", status: KnobStatus::Aktiv, purpose: "Gewicht je Kriterium innerhalb des Ownership-Pols; Stelle 7 wirkungslos (net_mcts.rs, ownership_weights)", prereg: "PREREG_ownership_consumer.md par.2" },
    KnobEntry { name: "MOSAIC_OWNERSHIP_SCALE", default: "50.0 (1 oder 8 Werte)", status: KnobStatus::Diagnose, purpose: "Baustein 2: Nenner je Kriterium im Ownership-Pol tanh(E_k/scale_k), ersetzt die feste 50; gemessene Werte fuer Arm S: k0~17, k1~1, k2~0,3 (net_mcts.rs, ownership_scale)", prereg: "PREREG_reachability_target.md par.6" },
    KnobEntry { name: "MOSAIC_REACH_TARGET_K1", default: "0 (aus)", status: KnobStatus::Aktiv, purpose: "Zielwechsel des Ownership-Kopfes fuer k1: Spalten-Atome (Index 6..11) tragen ab Runde 3 VOLLENDBARKEIT statt Realisierung; eigener HDF5-Cache-Schluessel (neural_net.py, _reach_target_k1_active)", prereg: "PREREG_reachability_target.md" },
    KnobEntry { name: "MOSAIC_GUMBEL_TOP_M", default: "0 (= Formel sims/16)", status: KnobStatus::Aktiv, purpose: "fester Wurzelbreiten-Override m fuer Gumbel-Top-m (net_mcts.rs:2514)", prereg: "PREREG_search_path_remeasurements.md M2" },
    KnobEntry { name: "MOSAIC_TAU_ARGMAX_FROM_MOVE", default: "0 (= aus)", status: KnobStatus::Aktiv, purpose: "Self-Play: ab Halbzug N argmax statt Besuchs-Sampling (net_mcts.rs:2540)", prereg: "PREREG_search_path_remeasurements.md M3" },
    KnobEntry { name: "MOSAIC_DENIAL_TIEBREAK_EPS", default: "0.0 (aus)", status: KnobStatus::Aktiv, purpose: "eps-Fenster des Denial-Tie-Breaks E3 (net_mcts.rs:2556)", prereg: "PREREG_denial_tiebreak.md" },
    KnobEntry { name: "MOSAIC_DENIAL_UNCERT_Z", default: "0.0 (aus)", status: KnobStatus::Aktiv, purpose: "z-Schwelle des E3b-Unsicherheits-Fensters (net_mcts.rs:2570)", prereg: "PREREG_denial_tiebreak.md" },
    KnobEntry { name: "MOSAIC_DENIAL_MIN_VISIT_FRAC", default: "0.5", status: KnobStatus::Aktiv, purpose: "Mindest-Besuchsanteil f des E3b-Besuchs-Gates (net_mcts.rs:2579)", prereg: "PREREG_denial_tiebreak.md" },
    KnobEntry { name: "MOSAIC_COLOR_DENIAL_PROBE_Z", default: "0.0 (aus)", status: KnobStatus::Diagnose, purpose: "z-Schwelle des Stoerfenster-ZAEHLMODUS -- zaehlt nur, aendert die gespielte Aktion nicht (net_mcts.rs, color_denial_probe_with)", prereg: "PREREG_opponent_disruption_v2.md par.5.2" },
    KnobEntry { name: "MOSAIC_COLOR_DENIAL_PROBE_MIN_VISIT_FRAC", default: "0.5", status: KnobStatus::Diagnose, purpose: "Mindest-Besuchsanteil des Stoerfenster-Zaehlmodus (net_mcts.rs, color_denial_probe_min_visit_frac)", prereg: "PREREG_opponent_disruption_v2.md par.5.2" },
    KnobEntry { name: "MOSAIC_IMPLICIT_MINIMAX_A", default: "0.0 (aus)", status: KnobStatus::Aktiv, purpose: "Mischgewicht alpha der Implicit-Minimax-Backups (Baier/Winands): Selektions-Q der Tiefe-≥1-Gumbel-Auswahl wird (1-alpha)*Q_MC + alpha*v_IM, v_IM per Minimax ueber besuchte Kinder rueckpropagiert. Welle-1-Pilot der Agenten-Kapselung (PREREG_agent_encapsulation.md): liest ueber SearchConfig::from_env() (net_mcts.rs) statt eines prozessglobalen OnceLock -- der Knopf bleibt die Default-Quelle, pro-Seite ueberschreibbar per Spec-Datei (models/<name>.spec.json) an net_arena_match/net_vs_net_arena_match/net_self_play_games", prereg: "PREREG_implicit_minimax_backup.md par.1; PREREG_agent_encapsulation.md par.4" },
    KnobEntry { name: "MOSAIC_LONG_ROW_INIT_W", default: "0.0 (aus)", status: KnobStatus::Aktiv, purpose: "Gewicht des Langreihen-INITIIERUNGS-Additivs am Netz-Blattwert: (begonnene lange Reihen ego - begonnene lange Reihen gegner) / LONG_ROW_INIT_SHAPING_SCALE, tanh-gesaettigt, additiv wie das Floor-Shaping. Stufenfunktion am Uebergang 0->1 in Musterreihe 5/6, KEIN Fuellstands-Anteil -- PREREG_long_row_payoff.md par.2a hat gemessen, dass die Luecke zum Heuristik-Lehrer im BEGINNEN sitzt (Policy-Masse 11,5 % gegen 25,2 %, Faktor ~3, flach ueber R1-4), nicht im Fortsetzen. Nenner 10 statt 50, damit der maximale Blattwert-Shift (0,059 bei w=0,3) dem Floor-Term entspricht statt fuenfmal schwaecher zu sein (PREREG_floor_shaping_scale.md). Liest ueber SearchConfig, pro Seite per Spec-Datei ueberschreibbar", prereg: "PREREG_long_row_payoff.md par.3/B1; PREREG_floor_shaping_scale.md par.2" },
    // ── Runde 5 (round5.rs) ─────────────────────────────────────────────────
    KnobEntry { name: "MOSAIC_PHASE_STAGE", default: "both", status: KnobStatus::Diagnose, purpose: "Auf welchen Entscheidungsstellen der Phasenfaktor wirkt: draft/tiling/both (plate_builder.rs::phase_wirkt_auf) -- trennt Rang-Entscheidung im Drafting von der Summen-Entscheidung im Tiling", prereg: "PREREG_heuristic_v2_long_rows.md par.14" },
    KnobEntry { name: "MOSAIC_PHASE_AMP", default: "unset (= feste Tabelle SPALTEN_PHASE)", status: KnobStatus::Diagnose, purpose: "Gipfelhoehe des Phasenfaktors auf die Spalten-Stufen der v2-Zielkarte (plate_builder.rs::spalten_phase); 1.0 = wirkungslos, dient im Sweep als Nullpunkt", prereg: "PREREG_heuristic_v2_long_rows.md par.13" },
    KnobEntry { name: "MOSAIC_PHASE_PEAK", default: "2.5 (nur wirksam wenn MOSAIC_PHASE_AMP gesetzt)", status: KnobStatus::Diagnose, purpose: "Gipfel-Runde des Phasenfaktors (plate_builder.rs::spalten_phase)", prereg: "PREREG_heuristic_v2_long_rows.md par.13" },
    KnobEntry { name: "MOSAIC_R5_CHANCE_NODES", default: "an (=0 Altverhalten)", status: KnobStatus::Aktiv, purpose: "Zufallsknoten fuer verdeckte Bonuschips im R5-Loeser, scharf seit 2026-08-10 (round5.rs:159)", prereg: "PREREG_chance_nodes.md" },
    KnobEntry { name: "MOSAIC_R5_NET_SOLVER", default: "an (=0 Gegenprobe Netz)", status: KnobStatus::Aktiv, purpose: "Netzpfad nutzt in Runde 5 den exakten Loeser statt des Netz-Blattwerts (round5.rs:183)", prereg: "PREREG_chance_nodes.md Teil E" },
    KnobEntry { name: "MOSAIC_R5_NODE_BUDGET", default: "200", status: KnobStatus::Aktiv, purpose: "Knotenbudget je R5-Entscheidung (round5.rs:199, NODE_BUDGET round5.rs:88)", prereg: "PREREG_chance_nodes.md" },
    // ── Inferenz-Backends (net_ort.rs, net_batcher.rs) ──────────────────────
    KnobEntry { name: "MOSAIC_ORT_CUDA_ENABLED", default: "aus", status: KnobStatus::Aktiv, purpose: "Weg B: ORT-CUDA-Backend fuer eval_batch; wirkt nur mit Feature ort_cuda_probe (net_ort.rs:132)", prereg: "PREREG_gpu_inference_path.md par.11" },
    KnobEntry { name: "MOSAIC_INTERLEAVE_ENABLED", default: "aus", status: KnobStatus::Aktiv, purpose: "Weg V: Sammel-Faden-Verschraenkung mehrerer Suchfaeden zu einem Batch (net_batcher.rs:217)", prereg: "PREREG_async_search.md" },
    KnobEntry { name: "MOSAIC_INTERLEAVE_BATCH_MAX", default: "16 (= EVAL_BATCH_MAX_N)", status: KnobStatus::Aktiv, purpose: "Obergrenze der Sammel-Fuellung je eval_batch-Aufruf (net_batcher.rs:232)", prereg: "PREREG_async_search.md" },
    KnobEntry { name: "MOSAIC_INTERLEAVE_FILL_TIMEOUT_US", default: "200", status: KnobStatus::Aktiv, purpose: "Deadlock-Waechter-Fenster in Mikrosekunden je Fuell-Slot (net_batcher.rs:250)", prereg: "PREREG_async_search.md" },
    // ── Tiling (tiling_solver.rs, self_play.rs) ─────────────────────────────
    KnobEntry { name: "MOSAIC_TILING_CACHE", default: "an (=0 schaltet ab)", status: KnobStatus::Aktiv, purpose: "Tiling-Solver-Memoisierung, bitgleich, -20% Self-Play-Wandzeit (tiling_solver.rs:383)", prereg: "-" },
    KnobEntry { name: "MOSAIC_TILING_CACHE_STATS", default: "aus (nur =1)", status: KnobStatus::Diagnose, purpose: "zaehlt Schluessel-Wiederkehr im Tiling-Solver, kein Cache (tiling_solver.rs:371)", prereg: "-" },
    KnobEntry { name: "MOSAIC_TILING_SELECT", default: "0 (Bestandskriterium)", status: KnobStatus::Aktiv, purpose: "Auswahlkriterium unter Top-K-Tilings: 0=punkte*P(Sieg), 1=reines P(Sieg) (tiling_solver.rs:822)", prereg: "PREREG_t37_tiling_criterion.md" },
    KnobEntry { name: "MOSAIC_TILING_PLATTEN_W", default: "0.0 (aus)", status: KnobStatus::Aktiv, purpose: "plattenbewusste Tiling-Zugwahl R1-4: w * Endwertung nach Abschluss additiv (tiling_solver.rs:964)", prereg: "PREREG_placement_side.md" },
    KnobEntry { name: "MOSAIC_TILING_PLATTEN_GEW", default: "1.0 (1 oder 8 Werte)", status: KnobStatus::Aktiv, purpose: "Gewicht je Kriterium fuer den Plattenwert der Tiling-Wahl (tiling_solver.rs:1023)", prereg: "PREREG_placement_side.md" },
    KnobEntry { name: "MOSAIC_TILING_PUNKTE_W", default: "0.0 (aus)", status: KnobStatus::Aktiv, purpose: "Punkte-Kopf-Blend im Netz-Tiling-Stichentscheid; gemessen wirkungslos (self_play.rs:985; archive/history.md:10715)", prereg: "-" },
    KnobEntry { name: "MOSAIC_OWNERSHIP_TILING_W", default: "0.0 (aus)", status: KnobStatus::Aktiv, purpose: "Ownership-Pol der Tiling-Zugwahl R1-4: marginale Feldwerte aus der Wurzelkarte, additiv zum Plattenterm (tiling_solver.rs, ownership_tiling_weight)", prereg: "PREREG_ownership_consumer.md par.3" },
    KnobEntry { name: "MOSAIC_OWNERSHIP_CONJ", default: "0 (aus, Produktform)", status: KnobStatus::Aktiv, purpose: "FORMumschaltung, keine Dosis: die konjunktiven Kriterien (k0/k1/k2/k3/k5/k7) kommen aus den gelernten Konjunktions-Atomen statt aus dem Produkt der Feldwahrscheinlichkeiten; additive k4/k6 bleiben auf den Feldlabels. Braucht den 140er-Kopf, sonst Rueckfall MIT Warnung (net_mcts.rs, ownership_conj)", prereg: "PREREG_conjunction_terms.md par.4" },
    // ── Self-Play / Infrastruktur ───────────────────────────────────────────
    KnobEntry { name: "MOSAIC_STACK_DRAW_RESEARCH", default: "aus", status: KnobStatus::Diagnose, purpose: "Stapelzug nicht sammelaufloesen: nur der Peek wird angewandt, danach neue Suche (self_play.rs:609)", prereg: "PREREG_chance_nodes.md" },
    KnobEntry { name: "MOSAIC_ASYM_VORZUG", default: "aus", status: KnobStatus::Diagnose, purpose: "Baustein 1 (Arm S): je Self-Play-Partie bekommt GENAU EINE Seite den Bauer-Vorzug (vorzug:true), Seitenwahl deterministisch aus dem Partie-Seed 50/50; dome_preference faehrt in derselben Kette mit (self_play.rs, asym_preference_active/asym_preference_side)", prereg: "PREREG_asymmetric_curriculum.md par.3" },
    KnobEntry { name: "MOSAIC_PROFILE_SELFPLAY", default: "aus (nur =1)", status: KnobStatus::Diagnose, purpose: "Self-Play-Zeitprofil je Kategorie (profiling.rs:493)", prereg: "PREREG_gpu_offloading.md" },
    KnobEntry { name: "MOSAIC_DATA_DIR", default: "<repo>/data", status: KnobStatus::Aktiv, purpose: "Korpus-Ordner-Override fuer train/self_play/server (config.py:28; Kommentar-Erwaehnung net_mcts.rs:177)", prereg: "PREREG_corpus_dose.md" },
    KnobEntry { name: "MOSAIC_PROFILES_PATH", default: "player_profiles.json im Projektroot", status: KnobStatus::Aktiv, purpose: "Profil-Datei-Override, Pflicht fuer Test-/Zweitinstanzen seit Vorfall 2026-08-02 (player_profiles.py:51)", prereg: "-" },
    KnobEntry { name: "MOSAIC_MEM_LOG_EVERY", default: "2000 Batches (0 = aus)", status: KnobStatus::Diagnose, purpose: "Abstand der [mem]-Zeilen im Training. Vorher fest 100, also 215 Zeilen je Epoche; der Epochen-Verlauf im Manifest deckt den Bedarf ab. Nicht ganz abschaltbar per Default, weil RAM Engpass 2 ist (train.py)", prereg: "-" },
    // ── Diagnose-Spieler / Provokation ──────────────────────────────────────
    KnobEntry { name: "MOSAIC_SPALTENBAU", default: "aus", status: KnobStatus::Diagnose, purpose: "Spaltenbauer-Vorzugsschicht (Kriterium 1), nie im Gating (column_build.rs:78)", prereg: "PREREG_provocation.md par.11ff" },
    KnobEntry { name: "MOSAIC_SPALTENBAU_SICHERHEITSNETZ", default: "aus (Opt-in =1)", status: KnobStatus::Diagnose, purpose: "Baustein 1 Vollendbarkeits-Filter, seit par.15 default AUS (column_build.rs:134)", prereg: "PREREG_provocation.md par.15" },
    KnobEntry { name: "MOSAIC_SPALTENBAU_JACKPOT", default: "aus (Opt-in =1)", status: KnobStatus::Diagnose, purpose: "Baustein 3a dominante Jackpot-Gewichtung, seit par.15 default AUS (column_build.rs:151)", prereg: "PREREG_provocation.md par.15" },
    KnobEntry { name: "MOSAIC_SPALTENBAU_SPECIAL", default: "aus (Opt-in =1)", status: KnobStatus::Diagnose, purpose: "par.16 Special-Zellen-Erweiterung des Spaltenbauers (column_build.rs:204)", prereg: "PREREG_provocation.md par.16" },
    KnobEntry { name: "MOSAIC_STACK_DRAW_RESERVATION", default: "aus (Opt-in =1)", status: KnobStatus::Diagnose, purpose: "reparierte Blindzieh-Stopp-Regel: erwartete VERBESSERUNG in einer Einheit statt Niveau gegen Typmittelwert (self_play.rs::resolve_and_apply_stack_draw)", prereg: "PREREG_stack_draw_reservation_rule.md par.5b" },
    KnobEntry { name: "MOSAIC_UPDATE_FEATURE_FIXTURE", default: "aus (Opt-in =1)", status: KnobStatus::Diagnose, purpose: "schreibt die Feature-Golden-Fixture neu statt zu pruefen; NUR fuer gewollte Feature-Aenderungen (features.rs::maybe_update_fixture)", prereg: "-" },
    KnobEntry { name: "MOSAIC_SPALTENBAU_TRACE", default: "aus", status: KnobStatus::Diagnose, purpose: "[SB]-Entscheidungs-Spur im Logstrom, additiv (column_build.rs:1081)", prereg: "-" },
    KnobEntry { name: "MOSAIC_PLATTENBAU", default: "aus (0..7 oder auto)", status: KnobStatus::Diagnose, purpose: "generischer Plattenbauer fuer alle 8 Wertungskriterien (plate_builder.rs:83)", prereg: "STATUS.md Architektur-Fahrplan P.5" },
    KnobEntry { name: "MOSAIC_PROVOKATION_SPALTE", default: "aus (0..5 oder auto)", status: KnobStatus::Diagnose, purpose: "Beschneidung der Drafting-Aktionsmenge auf eine Ziel-Spalte, nie im Gating (provocation.rs:49)", prereg: "PREREG_provocation.md par.4" },
    KnobEntry { name: "MOSAIC_VORZUG_SPALTE", default: "aus (0..5)", status: KnobStatus::Diagnose, purpose: "Vorzugsmodus: konstruktiver Spaltenzug wird bevorzugt gespielt, kein Verbot (provocation.rs:440)", prereg: "PREREG_provocation.md" },
    KnobEntry { name: "MOSAIC_OPPONENT_DISRUPTION", default: "aus", status: KnobStatus::Diagnose, purpose: "Gegner-Stoerungs-Schicht, nie im Gating (provocation.rs:703)", prereg: "PREREG_opponent_disruption.md par.3" },
    KnobEntry { name: "MOSAIC_VOLLE_VERSORGUNG", default: "aus (=1 oder true)", status: KnobStatus::Diagnose, purpose: "Versorgungs-Deckenprobe: Fabriken deterministisch aus vollem Farbkreis (state.rs:208)", prereg: "PREREG_placement_side.md par.10" },
    KnobEntry { name: "MOSAIC_PLATTENKOPF_GAMES", default: "1000 bzw. 400 je Messtest", status: KnobStatus::Diagnose, purpose: "Partienzahl der Plattenkopf-Referenzlaeufe (#[ignore]-Messtests, scoring.rs:1330/1347/1374)", prereg: "-" },
    KnobEntry { name: "MOSAIC_PLATTENKOPF_SIMS", default: "150", status: KnobStatus::Diagnose, purpose: "Heuristik-Sims der Plattenkopf-Referenzlaeufe (scoring.rs:1348)", prereg: "-" },
    KnobEntry { name: "MOSAIC_FROZEN_STATES_JSON", default: "unset (Pfad; Tests sonst uebersprungen)", status: KnobStatus::Diagnose, purpose: "Pfad zum frozen-Drafting-States-Export fuer Entscheidungsgleichheits-Tests (net_mcts.rs, ort_cuda_/interleaved_-Tests)", prereg: "PREREG_gpu_inference_path.md" },
    // ── Training / Anzeige (Python) ─────────────────────────────────────────
    KnobEntry { name: "MOSAIC_DATA_EXCLUDE", default: "unset (Regex)", status: KnobStatus::Aktiv, purpose: "Fenster-Pinning: Dateien vor Cache-Key-Bildung und Training ausschliessen (neural_net.py:1214)", prereg: "-" },
    KnobEntry { name: "MOSAIC_CARRIER_MANIFEST", default: "policy_carrier_manifest_v20.json", status: KnobStatus::Aktiv, purpose: "Dateiname des Policy-Traeger-Manifests im Korpus-Ordner (neural_net.py:1244)", prereg: "PREREG_v21_window.md" },
    KnobEntry { name: "MOSAIC_IGNORE_POLICY_TARGET_VALID", default: "aus (nur =1)", status: KnobStatus::Aktiv, purpose: "Traeger-A/B Arm B: setzt GENAU die Policy-Maskierung aus `policy_target_valid=false` aus, sodass der Policy-Kopf auch die Vorzugszuege des v2-Lehrers sieht (Wirkstelle neural_net.py:1883). Einmal beim Import gelesen (neural_net.py:8), damit derselbe Prozess die Semantik nicht auf halber Strecke wechselt, und im Cache-Schluessel (`+ignore_ptv_v1`, neural_net.py:1335) -- sonst zoege der zweite Lauf still den Cache des ersten. Die anderen Nullsetzungen (Tiling/Start, Traeger-Manifest, PCR) bleiben unberuehrt", prereg: "PREREG_v22_window.md par.4" },
    KnobEntry { name: "MOSAIC_CACHE_NOPACK", default: "aus (nur =1)", status: KnobStatus::Aktiv, purpose: "erzwingt unkomprimiertes Cache-Format statt Bitpacking, eigener Cache-Key (neural_net.py:1290)", prereg: "PREREG_v21_window.md" },
    KnobEntry { name: "MOSAIC_CACHE_F32", default: "aus (nur =1)", status: KnobStatus::Aktiv, purpose: "float32 statt float16 fuer states/policies im Cache, Notausstieg (neural_net.py:1872)", prereg: "-" },
    KnobEntry { name: "MOSAIC_PLANES_LAZY", default: "aus (nur =1)", status: KnobStatus::Aktiv, purpose: "lazy HDF5-Pro-Index-Zugriff statt Planes-in-RAM, nur fuer knappes RAM (neural_net.py:2014)", prereg: "-" },
    KnobEntry { name: "MOSAIC_PLANES_H5_DIR", default: "unset", status: KnobStatus::Diagnose, purpose: "Planes-HDF5 aus anderem Ordner oeffnen, OneDrive-Ausschlusstest (neural_net.py:1105)", prereg: "-" },
    KnobEntry { name: "MOSAIC_VAL_POOL", default: "unset (Regex auf den Dateinamen)", status: KnobStatus::Aktiv, purpose: "schraenkt die KANDIDATEN des Val-Splits ein: was nicht matcht, geht garantiert in den Trainings-Teil (train.py:536). Fuer Warmstarts von einem Modell, das eine Teilmenge desselben Korpus schon trainiert hat -- ein frei gezogener Val-Split enthielte dessen Dateien, und `--select-by-brier` waehlte den Checkpoint auf einem mitgesehenen Mass. Zu kleiner Pool = harter Abbruch statt stillschweigend kleinerem Val-Split; der Regex steht im Trainings-Manifest (train.py:505)", prereg: "PREREG_v22_window.md par.6" },
    KnobEntry { name: "MOSAIC_DISPLAY_CAL", default: "an (=0 schaltet ab)", status: KnobStatus::Aktiv, purpose: "Platt-Kalibrierung der ANGEZEIGTEN Gewinnwahrscheinlichkeit, nicht der Suche (server.py:1409)", prereg: "evaluations/artifacts/platt_fit_v21.json" },
    KnobEntry { name: "MOSAIC_DISPLAY_CAL_A", default: "-0.0033", status: KnobStatus::Aktiv, purpose: "Platt-A der Anzeige-Kalibrierung, modellspezifisch (server.py:1407)", prereg: "evaluations/artifacts/platt_fit_v21.json" },
    KnobEntry { name: "MOSAIC_DISPLAY_CAL_B", default: "0.9060", status: KnobStatus::Aktiv, purpose: "Platt-B der Anzeige-Kalibrierung, modellspezifisch (server.py:1408)", prereg: "evaluations/artifacts/platt_fit_v21.json" },
    // ── Geplante Knoepfe (Prereg-beschrieben, im Arbeitsbaum nicht verdrahtet) ──
    KnobEntry { name: "MOSAIC_GAME_TIMEOUT_SCALE", default: "1.0 (geplant)", status: KnobStatus::Geplant, purpose: "Multiplikator auf den Pro-Partie-Timeout im Self-Play; im Prereg beschrieben, Grep 2026-08-15 findet KEIN Vorkommen in engine/src oder *.py -- nicht verdrahtet", prereg: "PREREG_gpu_inference_path.md (Deckel-Knopf)" },
    // ── Tote Knoepfe (dokumentiert statt geraten) ───────────────────────────
    KnobEntry { name: "MOSAIC_UNLOCK_SHAPING_W", default: "-", status: KnobStatus::Tot, purpose: "wirkungslos seit Zusammenfuehrung 2026-08-11, nur noch Warn-Stub (net_mcts.rs:1257)", prereg: "PREREG_scoring_plate_injection.md" },
    KnobEntry { name: "MOSAIC_UNLOCK_BETA", default: "-", status: KnobStatus::Tot, purpose: "wirkungslos seit Zusammenfuehrung 2026-08-11, nur noch Warn-Stub (net_mcts.rs:1257)", prereg: "PREREG_scoring_plate_injection.md" },
    KnobEntry { name: "MOSAIC_ENDAWARE_W", default: "-", status: KnobStatus::Tot, purpose: "entfernt 2026-08-13 (gemessen wirkungslos), nur noch Kommentar-Erwaehnung (net_mcts.rs:1322)", prereg: "PREREG_scoring_plate_injection.md N7" },
    KnobEntry { name: "MOSAIC_MUSTERREIHEN_W", default: "-", status: KnobStatus::Tot, purpose: "entfernt 2026-08-13 (gemessen wirkungslos), nur noch Kommentar-Erwaehnung (net_mcts.rs:1323)", prereg: "PREREG_scoring_plate_injection.md N7" },
    KnobEntry { name: "MOSAIC_TORCH_IPC_ENABLED", default: "-", status: KnobStatus::Tot, purpose: "Weg A (Torch-IPC) samt net_ipc.rs/torch_ipc_server.py entfernt 2026-08-15, gemessen verworfen", prereg: "PREREG_gpu_inference_path.md par.9" },
    KnobEntry { name: "MOSAIC_TORCH_IPC_PORT", default: "-", status: KnobStatus::Tot, purpose: "Weg A entfernt 2026-08-15, siehe MOSAIC_TORCH_IPC_ENABLED", prereg: "PREREG_gpu_inference_path.md par.9" },
    KnobEntry { name: "MOSAIC_TORCH_IPC_SHM_DIR", default: "-", status: KnobStatus::Tot, purpose: "Weg A entfernt 2026-08-15, siehe MOSAIC_TORCH_IPC_ENABLED", prereg: "PREREG_gpu_inference_path.md par.9" },
];

/// JSON-Export der Registratur -- von `lib.rs::knob_registry_json`
/// (PyO3-Bindung, Muster `engine_config_json`) und
/// `tools/generate_knob_docs.py --wheel` konsumiert.
pub fn registry_json() -> String {
    let entries: Vec<serde_json::Value> = KNOBS
        .iter()
        .map(|k| {
            serde_json::json!({
                "name": k.name,
                "default": k.default,
                "status": k.status.as_str(),
                "purpose": k.purpose,
                "prereg": k.prereg,
            })
        })
        .collect();
    serde_json::json!({ "knobs": entries, "count": KNOBS.len() }).to_string()
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::BTreeSet;
    use std::path::{Path, PathBuf};

    /// Zieht alle `MOSAIC_[A-Z0-9_]*`-Tokens aus `text`. Tokens mit
    /// abschliessendem `_` sind Prosa-Praefixe (Zeilenumbruch in Kommentaren,
    /// z.B. "MOSAIC_INTERLEAVE_") und werden uebersprungen; Tokens mit
    /// `_TEST_` sind synthetische Test-Env-Vars (OnceLock-Kontaminations-
    /// Schutzmuster, z.B. MOSAIC_TEST_ENV_VALID_28B) und ebenfalls kein
    /// Laufzeit-Knopf.
    fn extract_mosaic_tokens(text: &str, out: &mut BTreeSet<String>) {
        for (pos, _) in text.match_indices("MOSAIC_") {
            // Kein Treffer mitten in einem laengeren Bezeichner.
            if pos > 0 {
                let prev = text.as_bytes()[pos - 1];
                if prev.is_ascii_alphanumeric() || prev == b'_' {
                    continue;
                }
            }
            let rest = &text[pos..];
            let end = rest
                .find(|c: char| !(c.is_ascii_uppercase() || c.is_ascii_digit() || c == '_'))
                .unwrap_or(rest.len());
            let token = &rest[..end];
            if token == "MOSAIC_" || token.ends_with('_') || token.contains("_TEST_") {
                continue;
            }
            out.insert(token.to_string());
        }
    }

    fn repo_root() -> PathBuf {
        Path::new(env!("CARGO_MANIFEST_DIR")).join("..")
    }

    /// Sammelt die Scan-Menge: engine/src/*.rs (ohne diese Registratur-Datei
    /// selbst, sonst waere die Gegenrichtungs-Pruefung zirkulaer), *.py im
    /// Repo-Root, tools/ rekursiv, engine/py/.
    fn scan_files() -> Vec<PathBuf> {
        let root = repo_root();
        let mut files = Vec::new();
        collect(&root.join("engine/src"), "rs", true, &mut files);
        collect(&root, "py", false, &mut files);
        collect(&root.join("tools"), "py", true, &mut files);
        collect(&root.join("engine/py"), "py", true, &mut files);
        files.retain(|p| p.file_name().map(|n| n != "knob_registry.rs").unwrap_or(true));
        assert!(!files.is_empty(), "Scan-Menge leer -- Repo-Layout unerwartet?");
        files
    }

    fn collect(dir: &Path, ext: &str, recursive: bool, out: &mut Vec<PathBuf>) {
        let Ok(entries) = std::fs::read_dir(dir) else { return };
        for entry in entries.flatten() {
            let p = entry.path();
            if p.is_dir() {
                if recursive && p.file_name().map(|n| n != "__pycache__").unwrap_or(false) {
                    collect(&p, ext, true, out);
                }
            } else if p.extension().map(|e| e == ext).unwrap_or(false) {
                out.push(p);
            }
        }
    }

    fn scanned_tokens() -> BTreeSet<String> {
        let mut tokens = BTreeSet::new();
        for f in scan_files() {
            let Ok(text) = std::fs::read_to_string(&f) else { continue };
            extract_mosaic_tokens(&text, &mut tokens);
        }
        tokens
    }

    /// DER WAECHTER (Auftragspunkt 3): jeder im Quelltext vorkommende
    /// `MOSAIC_*`-Name MUSS einen Registratur-Eintrag haben. Ein neuer Knopf
    /// ohne Eintrag laesst diesen Test fehlschlagen -- kein stiller
    /// Knopf-Wildwuchs mehr.
    #[test]
    fn all_mosaic_env_vars_in_code_are_registered() {
        let registered: BTreeSet<&str> = KNOBS.iter().map(|k| k.name).collect();
        let missing: Vec<String> = scanned_tokens()
            .into_iter()
            .filter(|t| !registered.contains(t.as_str()))
            .collect();
        assert!(
            missing.is_empty(),
            "MOSAIC_*-Knoepfe im Code OHNE Registratur-Eintrag (engine/src/knob_registry.rs \
             ergaenzen -- Name, Default, Status, Kurzzweck, Prereg-Verweis): {missing:?}"
        );
    }

    /// Gegenrichtung: ein Registratur-Eintrag mit Status `Aktiv`/`Diagnose`,
    /// dessen Name nirgends mehr im gescannten Quelltext steht, ist veraltet
    /// -- entweder der Knopf wurde entfernt (dann Status auf `Tot` setzen)
    /// oder der Eintrag ist ein Tippfehler. `Tot`/`Geplant` sind per
    /// Definition ohne (Pflicht-)Vorkommen im Code.
    #[test]
    fn registered_non_dead_knobs_exist_in_code() {
        let tokens = scanned_tokens();
        let stale: Vec<&str> = KNOBS
            .iter()
            .filter(|k| {
                !matches!(k.status, KnobStatus::Tot | KnobStatus::Geplant) && !tokens.contains(k.name)
            })
            .map(|k| k.name)
            .collect();
        assert!(
            stale.is_empty(),
            "Registratur-Eintraege ohne Vorkommen im Code (Status auf Tot setzen oder \
             Eintrag korrigieren): {stale:?}"
        );
    }

    #[test]
    fn knob_names_are_unique_and_well_formed() {
        let mut seen = BTreeSet::new();
        for k in KNOBS {
            assert!(k.name.starts_with("MOSAIC_"), "{}: Name ohne MOSAIC_-Praefix", k.name);
            assert!(!k.name.ends_with('_'), "{}: Name endet mit Unterstrich", k.name);
            assert!(seen.insert(k.name), "{}: doppelter Registratur-Eintrag", k.name);
            assert!(!k.purpose.is_empty(), "{}: leerer Kurzzweck", k.name);
            assert!(!k.prereg.is_empty(), "{}: leerer Prereg-Verweis (nutze \"-\")", k.name);
        }
    }

    #[test]
    fn registry_json_parses_and_matches_table() {
        let parsed: serde_json::Value = serde_json::from_str(&registry_json()).expect("gueltiges JSON");
        assert_eq!(parsed["count"].as_u64().unwrap() as usize, KNOBS.len());
        let arr = parsed["knobs"].as_array().expect("knobs-Array");
        assert_eq!(arr.len(), KNOBS.len());
        assert_eq!(arr[0]["name"], KNOBS[0].name);
        // Status-Strings sind genau die vier vereinbarten Werte.
        for e in arr {
            let s = e["status"].as_str().unwrap();
            assert!(matches!(s, "aktiv" | "diagnose" | "tot" | "geplant"), "unerwarteter Status {s:?}");
        }
    }

    /// Fixpunkte gegen die Auftrags-Vorgaben: die genannten Diagnose-Knoepfe
    /// sind als `Diagnose` registriert, die bekannten Toten als `Tot`.
    #[test]
    fn mandated_statuses_are_recorded() {
        let by_name = |n: &str| KNOBS.iter().find(|k| k.name == n).unwrap_or_else(|| panic!("{n} fehlt"));
        for n in [
            "MOSAIC_SPALTENBAU",
            "MOSAIC_PLATTENBAU",
            "MOSAIC_VOLLE_VERSORGUNG",
            "MOSAIC_PROVOKATION_SPALTE",
        ] {
            assert_eq!(by_name(n).status, KnobStatus::Diagnose, "{n} muss Diagnose sein");
        }
        for n in ["MOSAIC_UNLOCK_SHAPING_W", "MOSAIC_UNLOCK_BETA", "MOSAIC_TORCH_IPC_ENABLED"] {
            assert_eq!(by_name(n).status, KnobStatus::Tot, "{n} muss Tot sein");
        }
    }
}
