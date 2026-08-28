# MOSAIC_*-Laufzeit-Knoepfe

GENERIERT -- nicht von Hand editieren. Quelle: `engine/src/knob_registry.rs`
(direkt geparst, kein Wheel noetig), Generator: `tools/generate_knob_docs.py`.

Der Waechter-Test `knob_registry::tests::all_mosaic_env_vars_in_code_are_registered`
stellt sicher, dass jeder im Code vorkommende `MOSAIC_*`-Knopf hier steht.

Stand: 87 Knoepfe (50 aktiv, 29 diagnose, 7 tot, 1 geplant).

**Status** sagt, ob der Knopf VERDRAHTET ist -- ausdruecklich nicht, ob sein
Default an ist (`knob_registry.rs`: "Default kann an ODER aus sein").
**Verdikt** ist der Zeile-1-Status der zitierten Prereg. Erst beide zusammen
trennen "aus, weil noch niemand ihn eingeschaltet hat" von "aus, weil die
Messung ihn erledigt hat" -- in der Registratur allein sehen die gleich aus.

**51 verdrahtete Knoepfe haengen an einer BEANTWORTETEN Prereg** (entschieden oder ueberholt).

Der Statuskopf sagt ENTSCHIEDEN, aber NICHT die Richtung -- deshalb die
Trennung nach Default. Kein Loeschauftrag: ein negatives Ergebnis kann
"falscher Hebel, richtiges Ziel" heissen (`PREREG_long_row_payoff` ist
genau so ein Fall). Es ist die Liste, an der die Frage stellbar wird.

**Beantwortet UND Default aus (36)** -- hier lohnt die Nachfrage,
ob der Knopf noch etwas offen haelt:

- `MOSAIC_POINTS_UTILITY_W` (ENTSCHIEDEN, PREREG_task28_aggression.md)
- `MOSAIC_AGGR_LAMBDA` (ENTSCHIEDEN, PREREG_task28_aggression.md)
- `MOSAIC_WERTUNG_SHAPING_W` (ENTSCHIEDEN, PREREG_scoring_plate_injection.md)
- `MOSAIC_WERTUNG_ROUND_GAIN` (ENTSCHIEDEN, PREREG_scoring_plate_injection.md)
- `MOSAIC_WERTUNG_FLOOR_W` (ENTSCHIEDEN, PREREG_scoring_plate_injection.md)
- `MOSAIC_TILING_W` (ENTSCHIEDEN, PREREG_scoring_plate_injection.md)
- `MOSAIC_WERTUNG_SCALE_PROFILE` (ENTSCHIEDEN, PREREG_shaping_scale_per_round.md par.4/par.6a)
- `MOSAIC_WERTUNG_STREUUNG_MAX` (ENTSCHIEDEN, PREREG_ownership_corpus.md)
- `MOSAIC_OWNERSHIP_W` (UEBERHOLT, PREREG_ownership_consumer.md par.2)
- `MOSAIC_REACH_TARGET_K1` (ENTSCHIEDEN, PREREG_reachability_target.md)
- `MOSAIC_GUMBEL_TOP_M` (ENTSCHIEDEN, PREREG_search_path_remeasurements.md M2)
- `MOSAIC_TAU_ARGMAX_FROM_MOVE` (ENTSCHIEDEN, PREREG_search_path_remeasurements.md M3)
- `MOSAIC_DENIAL_TIEBREAK_EPS` (ENTSCHIEDEN, PREREG_denial_tiebreak.md)
- `MOSAIC_DENIAL_UNCERT_Z` (ENTSCHIEDEN, PREREG_denial_tiebreak.md)
- `MOSAIC_COLOR_DENIAL_PROBE_Z` (UEBERHOLT, PREREG_opponent_disruption_v2.md par.5.2)
- `MOSAIC_PHASE_AMP` (ENTSCHIEDEN, PREREG_heuristic_v2_long_rows.md par.13)
- `MOSAIC_ORT_CUDA_ENABLED` (ENTSCHIEDEN, PREREG_gpu_inference_path.md par.11)
- `MOSAIC_INTERLEAVE_ENABLED` (ENTSCHIEDEN, PREREG_async_search.md)
- `MOSAIC_TILING_SELECT` (ENTSCHIEDEN, PREREG_t37_tiling_criterion.md)
- `MOSAIC_TILING_PLATTEN_W` (ENTSCHIEDEN, PREREG_placement_side.md)
- `MOSAIC_OWNERSHIP_TILING_W` (UEBERHOLT, PREREG_ownership_consumer.md par.3)
- `MOSAIC_OWNERSHIP_CONJ` (ENTSCHIEDEN, PREREG_conjunction_terms.md par.4)
- `MOSAIC_ASYM_VORZUG` (ENTSCHIEDEN, PREREG_asymmetric_curriculum.md par.3)
- `MOSAIC_PROFILE_SELFPLAY` (ENTSCHIEDEN, PREREG_gpu_offloading.md)
- `MOSAIC_SPALTENBAU` (ENTSCHIEDEN, PREREG_provocation.md par.11ff)
- `MOSAIC_SPALTENBAU_SICHERHEITSNETZ` (ENTSCHIEDEN, PREREG_provocation.md par.15)
- `MOSAIC_SPALTENBAU_JACKPOT` (ENTSCHIEDEN, PREREG_provocation.md par.15)
- `MOSAIC_SPALTENBAU_SPECIAL` (ENTSCHIEDEN, PREREG_provocation.md par.16)
- `MOSAIC_PROVOKATION_SPALTE` (ENTSCHIEDEN, PREREG_provocation.md par.4)
- `MOSAIC_VORZUG_SPALTE` (ENTSCHIEDEN, PREREG_provocation.md)
- `MOSAIC_OPPONENT_DISRUPTION` (ENTSCHIEDEN, PREREG_opponent_disruption.md par.3)
- `MOSAIC_VOLLE_VERSORGUNG` (ENTSCHIEDEN, PREREG_placement_side.md par.10)
- `MOSAIC_FROZEN_STATES_JSON` (ENTSCHIEDEN, PREREG_gpu_inference_path.md)
- `MOSAIC_IGNORE_POLICY_TARGET_VALID` (ENTSCHIEDEN, PREREG_v22_window.md par.4)
- `MOSAIC_CACHE_NOPACK` (ENTSCHIEDEN, PREREG_v21_window.md)
- `MOSAIC_VAL_POOL` (ENTSCHIEDEN, PREREG_v22_window.md par.6)

**Beantwortet, Default AN (15)** -- in Benutzung, hier ist "entschieden" das Ergebnis, nicht das Ende:

- `MOSAIC_FLOOR_SHAPING_W` = 0.3 (ENTSCHIEDEN, PREREG_search_path_remeasurements.md M1)
- `MOSAIC_FLOOR_SHAPING_OPP_BIAS` = 1.0 (ENTSCHIEDEN, PREREG_aggression_style_measurement.md E2)
- `MOSAIC_NUM_DETERMINIZATIONS` = 1 (ENTSCHIEDEN, PREREG_ismcts_determinizations.md)
- `MOSAIC_WERTUNG_ALPHA` = 2.0 (1 oder 8 Werte) (ENTSCHIEDEN, PREREG_scoring_plate_injection.md)
- `MOSAIC_OWNERSHIP_GEW` = 1.0 (1 oder 8 Werte) (UEBERHOLT, PREREG_ownership_consumer.md par.2)
- `MOSAIC_OWNERSHIP_SCALE` = 50.0 (1 oder 8 Werte) (ENTSCHIEDEN, PREREG_reachability_target.md par.6)
- `MOSAIC_DENIAL_MIN_VISIT_FRAC` = 0.5 (ENTSCHIEDEN, PREREG_denial_tiebreak.md)
- `MOSAIC_COLOR_DENIAL_PROBE_MIN_VISIT_FRAC` = 0.5 (UEBERHOLT, PREREG_opponent_disruption_v2.md par.5.2)
- `MOSAIC_PHASE_STAGE` = both (ENTSCHIEDEN, PREREG_heuristic_v2_long_rows.md par.14)
- `MOSAIC_PHASE_PEAK` = 2.5 (nur wirksam wenn MOSAIC_PHASE_AMP gesetzt) (ENTSCHIEDEN, PREREG_heuristic_v2_long_rows.md par.13)
- `MOSAIC_INTERLEAVE_BATCH_MAX` = 128 (= EVAL_BATCH_MAX_N) (ENTSCHIEDEN, PREREG_async_search.md)
- `MOSAIC_INTERLEAVE_FILL_TIMEOUT_US` = 200 (ENTSCHIEDEN, PREREG_async_search.md)
- `MOSAIC_TILING_PLATTEN_GEW` = 1.0 (1 oder 8 Werte) (ENTSCHIEDEN, PREREG_placement_side.md)
- `MOSAIC_DATA_DIR` = <repo>/data (ENTSCHIEDEN, PREREG_corpus_dose.md)
- `MOSAIC_CARRIER_MANIFEST` = policy_carrier_manifest_v20.json (ENTSCHIEDEN, PREREG_v21_window.md)

| Knopf | Default | Status | Verdikt | Zweck | Beleg |
|---|---|---|---|---|---|
| `MOSAIC_POINTS_UTILITY_W` | 0.0 | aktiv | ENTSCHIEDEN | Utility-Blend-Gewicht w des Punkte-Kopfs; danach per GUI-Regler set_aggression_params setzbar (net_mcts.rs:158) | PREREG_task28_aggression.md |
| `MOSAIC_AGGR_LAMBDA` | 0.0 | aktiv | ENTSCHIEDEN | Denial-Gewicht lambda (Gegner-Punkte-Abzug im Utility-Blend); GUI-Regler wie oben (net_mcts.rs:164) | PREREG_task28_aggression.md |
| `MOSAIC_VALUE_CAL_A` | 0.0 | aktiv | - | Logit-Shift A der monotonen Value-Kalibrierung (net_mcts.rs:321) | STATUS.md Task #30 |
| `MOSAIC_VALUE_CAL_B` | 1.0 | aktiv | - | Logit-Streckung B der Value-Kalibrierung (net_mcts.rs:327) | STATUS.md Task #30 |
| `MOSAIC_ROOT_CHILD_Q` | an (=0 schaltet ab) | aktiv | - | Wurzelkind-Q-Logging ins Self-Play-JSON (net_mcts.rs:219) | STATUS.md Task #35 |
| `MOSAIC_FLOOR_SHAPING_W` | 0.3 | aktiv | ENTSCHIEDEN | Gewicht der Floor-Straf-Korrektur am Netz-Blattwert (net_mcts.rs:405) | PREREG_search_path_remeasurements.md M1 |
| `MOSAIC_FLOOR_SHAPING_OPP_BIAS` | 1.0 | aktiv | ENTSCHIEDEN | Gegner-Gewichtung des Floor-Shapings, >1 belohnt Zuschieben (net_mcts.rs:422) | PREREG_aggression_style_measurement.md E2 |
| `MOSAIC_NUM_DETERMINIZATIONS` | 1 | aktiv | ENTSCHIEDEN | ISMCTS-Weltenzahl k, auf >=1 geklemmt (net_mcts.rs:734) | PREREG_ismcts_determinizations.md |
| `MOSAIC_WERTUNG_SHAPING_W` | 0.0 (1 oder 8 Werte) | aktiv | ENTSCHIEDEN | Wertungsplatten-EGO-Shaping-Gewicht je Kriterium (net_mcts.rs:1225) | PREREG_scoring_plate_injection.md |
| `MOSAIC_WERTUNG_ALPHA` | 2.0 (1 oder 8 Werte) | aktiv | ENTSCHIEDEN | Formungs-Exponent alpha je Kriterium (net_mcts.rs:1264) | PREREG_scoring_plate_injection.md |
| `MOSAIC_WERTUNG_ROUND_GAIN` | 0.0 | aktiv | ENTSCHIEDEN | rundenabhaengige Anhebung aller Alphas (net_mcts.rs:1360) | PREREG_scoring_plate_injection.md |
| `MOSAIC_WERTUNG_FLOOR_W` | 0.0 | aktiv | ENTSCHIEDEN | Strafleisten-Gegenterm im Wertungsplatten-Shaping (net_mcts.rs:1306) | PREREG_scoring_plate_injection.md |
| `MOSAIC_TILING_W` | 0.0 | aktiv | ENTSCHIEDEN | Tiling-Potenzial-Term (Heuristik-Summand solve_round_final_score) im Shaping (shaping.rs, tiling_weight) | PREREG_scoring_plate_injection.md |
| `MOSAIC_WERTUNG_SCALE_PROFILE` | aus (=0/leer; 1 oder an = Rundenprofil) | diagnose | ENTSCHIEDEN | Baustein 3: rundenabhaengiger Nenner SCALE_r=50*profil_r fuer den Wertungsplatten-/Spezialfeld-Term (Pfad A); Strafleisten-/Tiling-Term bleiben auf dem flachen Nenner (shaping.rs, scoring_scale_profile_active) | PREREG_shaping_scale_per_round.md par.4/par.6a |
| `MOSAIC_WERTUNG_STREUUNG_MAX` | 0.0 (aus) | aktiv | ENTSCHIEDEN | partieweise Streuung des Shaping-Gewichts aus dem Partie-Seed, Wert in [0,max] (shaping.rs, scoring_scatter_max) | PREREG_ownership_corpus.md |
| `MOSAIC_OWNERSHIP_W` | 0.0 (aus) | aktiv | UEBERHOLT | Zwei-Pole-Regler w_own: Blatt-Shift aus den erwarteten Plattenpunkten E_k des Ownership-Kopfs (shaping.rs, ownership_weight) | PREREG_ownership_consumer.md par.2 |
| `MOSAIC_OWNERSHIP_GEW` | 1.0 (1 oder 8 Werte) | aktiv | UEBERHOLT | Gewicht je Kriterium innerhalb des Ownership-Pols; Stelle 7 wirkungslos (shaping.rs, ownership_weights) | PREREG_ownership_consumer.md par.2 |
| `MOSAIC_OWNERSHIP_SCALE` | 50.0 (1 oder 8 Werte) | diagnose | ENTSCHIEDEN | Baustein 2: Nenner je Kriterium im Ownership-Pol tanh(E_k/scale_k), ersetzt die feste 50; gemessene Werte fuer Arm S: k0~17, k1~1, k2~0,3 (shaping.rs, ownership_scale) | PREREG_reachability_target.md par.6 |
| `MOSAIC_REACH_TARGET_K1` | 0 (aus) | aktiv | ENTSCHIEDEN | Zielwechsel des Ownership-Kopfes fuer k1: Spalten-Atome (Index 6..11) tragen ab Runde 3 VOLLENDBARKEIT statt Realisierung; eigener HDF5-Cache-Schluessel (reach_target.py, reach_target_k1_active) | PREREG_reachability_target.md |
| `MOSAIC_GUMBEL_TOP_M` | 0 (= Formel sims/16) | aktiv | ENTSCHIEDEN | fester Wurzelbreiten-Override m fuer Gumbel-Top-m (net_mcts.rs:2514) | PREREG_search_path_remeasurements.md M2 |
| `MOSAIC_TAU_ARGMAX_FROM_MOVE` | 0 (= aus) | aktiv | ENTSCHIEDEN | Self-Play: ab Halbzug N argmax statt Besuchs-Sampling (net_mcts.rs:2540) | PREREG_search_path_remeasurements.md M3 |
| `MOSAIC_DENIAL_TIEBREAK_EPS` | 0.0 (aus) | aktiv | ENTSCHIEDEN | eps-Fenster des Denial-Tie-Breaks E3 (net_mcts.rs:2556) | PREREG_denial_tiebreak.md |
| `MOSAIC_DENIAL_UNCERT_Z` | 0.0 (aus) | aktiv | ENTSCHIEDEN | z-Schwelle des E3b-Unsicherheits-Fensters (net_mcts.rs:2570) | PREREG_denial_tiebreak.md |
| `MOSAIC_DENIAL_MIN_VISIT_FRAC` | 0.5 | aktiv | ENTSCHIEDEN | Mindest-Besuchsanteil f des E3b-Besuchs-Gates (net_mcts.rs:2579) | PREREG_denial_tiebreak.md |
| `MOSAIC_COLOR_DENIAL_PROBE_Z` | 0.0 (aus) | diagnose | UEBERHOLT | z-Schwelle des Stoerfenster-ZAEHLMODUS -- zaehlt nur, aendert die gespielte Aktion nicht (net_mcts.rs, color_denial_probe_with) | PREREG_opponent_disruption_v2.md par.5.2 |
| `MOSAIC_COLOR_DENIAL_PROBE_MIN_VISIT_FRAC` | 0.5 | diagnose | UEBERHOLT | Mindest-Besuchsanteil des Stoerfenster-Zaehlmodus (net_mcts.rs, color_denial_probe_min_visit_frac) | PREREG_opponent_disruption_v2.md par.5.2 |
| `MOSAIC_IMPLICIT_MINIMAX_A` | 0.0 (aus) | aktiv | ENTSCHIEDEN/OFFEN | Mischgewicht alpha der Implicit-Minimax-Backups (Baier/Winands): Selektions-Q der Tiefe-≥1-Gumbel-Auswahl wird (1-alpha)*Q_MC + alpha*v_IM, v_IM per Minimax ueber besuchte Kinder rueckpropagiert. Welle-1-Pilot der Agenten-Kapselung (PREREG_agent_encapsulation.md): liest ueber SearchConfig::from_env() (net_mcts.rs) statt eines prozessglobalen OnceLock -- der Knopf bleibt die Default-Quelle, pro-Seite ueberschreibbar per Spec-Datei (models/<name>.spec.json) an net_arena_match/net_vs_net_arena_match/net_self_play_games | PREREG_implicit_minimax_backup.md par.1; PREREG_agent_encapsulation.md par.4 |
| `MOSAIC_LONG_ROW_INIT_W` | 0.0 (aus) | aktiv | ENTSCHIEDEN/OFFEN | Gewicht des Langreihen-INITIIERUNGS-Additivs am Netz-Blattwert: (begonnene lange Reihen ego - begonnene lange Reihen gegner) / LONG_ROW_INIT_SHAPING_SCALE, tanh-gesaettigt, additiv wie das Floor-Shaping. Stufenfunktion am Uebergang 0->1 in Musterreihe 5/6, KEIN Fuellstands-Anteil -- PREREG_long_row_payoff.md par.2a hat gemessen, dass die Luecke zum Heuristik-Lehrer im BEGINNEN sitzt (Policy-Masse 11,5 % gegen 25,2 %, Faktor ~3, flach ueber R1-4), nicht im Fortsetzen. Nenner 10 statt 50, damit der maximale Blattwert-Shift (0,059 bei w=0,3) dem Floor-Term entspricht statt fuenfmal schwaecher zu sein (PREREG_floor_shaping_scale.md). Liest ueber SearchConfig, pro Seite per Spec-Datei ueberschreibbar | PREREG_long_row_payoff.md par.3/B1; PREREG_floor_shaping_scale.md par.2 |
| `MOSAIC_PHASE_STAGE` | both | diagnose | ENTSCHIEDEN | Auf welchen Entscheidungsstellen der Phasenfaktor wirkt: draft/tiling/both (plate_builder.rs::phase_wirkt_auf) -- trennt Rang-Entscheidung im Drafting von der Summen-Entscheidung im Tiling | PREREG_heuristic_v2_long_rows.md par.14 |
| `MOSAIC_PHASE_AMP` | unset (= feste Tabelle SPALTEN_PHASE) | diagnose | ENTSCHIEDEN | Gipfelhoehe des Phasenfaktors auf die Spalten-Stufen der v2-Zielkarte (plate_builder.rs::spalten_phase); 1.0 = wirkungslos, dient im Sweep als Nullpunkt | PREREG_heuristic_v2_long_rows.md par.13 |
| `MOSAIC_PHASE_PEAK` | 2.5 (nur wirksam wenn MOSAIC_PHASE_AMP gesetzt) | diagnose | ENTSCHIEDEN | Gipfel-Runde des Phasenfaktors (plate_builder.rs::spalten_phase) | PREREG_heuristic_v2_long_rows.md par.13 |
| `MOSAIC_R5_CHANCE_NODES` | an (=0 Altverhalten) | aktiv | OFFEN | Zufallsknoten fuer verdeckte Bonuschips im R5-Loeser, scharf seit 2026-08-10 (round5.rs:159) | PREREG_chance_nodes.md |
| `MOSAIC_R5_NET_SOLVER` | an (=0 Gegenprobe Netz) | aktiv | OFFEN | Netzpfad nutzt in Runde 5 den exakten Loeser statt des Netz-Blattwerts (round5.rs:183) | PREREG_chance_nodes.md Teil E |
| `MOSAIC_R5_NODE_BUDGET` | 200 | aktiv | OFFEN | Knotenbudget je R5-Entscheidung (round5.rs:199, NODE_BUDGET round5.rs:88) | PREREG_chance_nodes.md |
| `MOSAIC_ORT_CUDA_ENABLED` | aus | aktiv | ENTSCHIEDEN | Weg B: ORT-CUDA-Backend fuer eval_batch; wirkt nur mit Feature ort_cuda_probe (net_ort.rs:132) | PREREG_gpu_inference_path.md par.11 |
| `MOSAIC_INTERLEAVE_ENABLED` | aus | aktiv | ENTSCHIEDEN | Weg V: Sammel-Faden-Verschraenkung mehrerer Suchfaeden zu einem Batch (net_batcher.rs:217) | PREREG_async_search.md |
| `MOSAIC_INTERLEAVE_BATCH_MAX` | 128 (= EVAL_BATCH_MAX_N) | aktiv | ENTSCHIEDEN | Obergrenze der Sammel-Fuellung je eval_batch-Aufruf (net_batcher.rs, configured_batch_max) | PREREG_async_search.md |
| `MOSAIC_INTERLEAVE_FILL_TIMEOUT_US` | 200 | aktiv | ENTSCHIEDEN | Deadlock-Waechter-Fenster in Mikrosekunden je Fuell-Slot (net_batcher.rs:250) | PREREG_async_search.md |
| `MOSAIC_TILING_CACHE` | an (=0 schaltet ab) | aktiv | - | Tiling-Solver-Memoisierung, bitgleich, -20% Self-Play-Wandzeit (tiling_solver.rs:383) | - |
| `MOSAIC_TILING_CACHE_STATS` | aus (nur =1) | diagnose | - | zaehlt Schluessel-Wiederkehr im Tiling-Solver, kein Cache (tiling_solver.rs:371) | - |
| `MOSAIC_TILING_SELECT` | 0 (Bestandskriterium) | aktiv | ENTSCHIEDEN | Auswahlkriterium unter Top-K-Tilings: 0=punkte*P(Sieg), 1=reines P(Sieg) (tiling_solver.rs:822) | PREREG_t37_tiling_criterion.md |
| `MOSAIC_TILING_PLATTEN_W` | 0.0 (aus) | aktiv | ENTSCHIEDEN | plattenbewusste Tiling-Zugwahl R1-4: w * Endwertung nach Abschluss additiv (tiling_solver.rs:964) | PREREG_placement_side.md |
| `MOSAIC_TILING_PLATTEN_GEW` | 1.0 (1 oder 8 Werte) | aktiv | ENTSCHIEDEN | Gewicht je Kriterium fuer den Plattenwert der Tiling-Wahl (tiling_solver.rs:1023) | PREREG_placement_side.md |
| `MOSAIC_TILING_PUNKTE_W` | 0.0 (aus) | aktiv | - | Punkte-Kopf-Blend im Netz-Tiling-Stichentscheid; gemessen wirkungslos (self_play.rs:985; archive/history.md:10715) | - |
| `MOSAIC_OWNERSHIP_TILING_W` | 0.0 (aus) | aktiv | UEBERHOLT | Ownership-Pol der Tiling-Zugwahl R1-4: marginale Feldwerte aus der Wurzelkarte, additiv zum Plattenterm (tiling_solver.rs, ownership_tiling_weight) | PREREG_ownership_consumer.md par.3 |
| `MOSAIC_OWNERSHIP_CONJ` | 0 (aus, Produktform) | aktiv | ENTSCHIEDEN | FORMumschaltung, keine Dosis: die konjunktiven Kriterien (k0/k1/k2/k3/k5/k7) kommen aus den gelernten Konjunktions-Atomen statt aus dem Produkt der Feldwahrscheinlichkeiten; additive k4/k6 bleiben auf den Feldlabels. Braucht den 140er-Kopf, sonst Rueckfall MIT Warnung (shaping.rs, ownership_conj) | PREREG_conjunction_terms.md par.4 |
| `MOSAIC_STACK_DRAW_RESEARCH` | aus | diagnose | OFFEN | Stapelzug nicht sammelaufloesen: nur der Peek wird angewandt, danach neue Suche (self_play.rs:609) | PREREG_chance_nodes.md |
| `MOSAIC_ASYM_VORZUG` | aus | diagnose | ENTSCHIEDEN | Baustein 1 (Arm S): je Self-Play-Partie bekommt GENAU EINE Seite den Bauer-Vorzug (vorzug:true), Seitenwahl deterministisch aus dem Partie-Seed 50/50; dome_preference faehrt in derselben Kette mit (self_play.rs, asym_preference_active/asym_preference_side) | PREREG_asymmetric_curriculum.md par.3 |
| `MOSAIC_PROFILE_SELFPLAY` | aus (nur =1) | diagnose | ENTSCHIEDEN | Self-Play-Zeitprofil je Kategorie (profiling.rs:493) | PREREG_gpu_offloading.md |
| `MOSAIC_DATA_DIR` | <repo>/data | aktiv | ENTSCHIEDEN | Korpus-Ordner-Override fuer train/self_play/server (config.py:28; Kommentar-Erwaehnung net_mcts.rs:177) | PREREG_corpus_dose.md |
| `MOSAIC_PROFILES_PATH` | player_profiles.json im Projektroot | aktiv | - | Profil-Datei-Override, Pflicht fuer Test-/Zweitinstanzen seit Vorfall 2026-08-02 (player_profiles.py:51) | - |
| `MOSAIC_MEM_LOG_EVERY` | 2000 Batches (0 = aus) | diagnose | - | Abstand der [mem]-Zeilen im Training. Vorher fest 100, also 215 Zeilen je Epoche; der Epochen-Verlauf im Manifest deckt den Bedarf ab. Nicht ganz abschaltbar per Default, weil RAM Engpass 2 ist (train.py) | - |
| `MOSAIC_SPALTENBAU` | aus | diagnose | ENTSCHIEDEN | Spaltenbauer-Vorzugsschicht (Kriterium 1), nie im Gating (column_build.rs:78) | PREREG_provocation.md par.11ff |
| `MOSAIC_SPALTENBAU_SICHERHEITSNETZ` | aus (Opt-in =1) | diagnose | ENTSCHIEDEN | Baustein 1 Vollendbarkeits-Filter, seit par.15 default AUS (column_build.rs:134) | PREREG_provocation.md par.15 |
| `MOSAIC_SPALTENBAU_JACKPOT` | aus (Opt-in =1) | diagnose | ENTSCHIEDEN | Baustein 3a dominante Jackpot-Gewichtung, seit par.15 default AUS (column_build.rs:151) | PREREG_provocation.md par.15 |
| `MOSAIC_SPALTENBAU_SPECIAL` | aus (Opt-in =1) | diagnose | ENTSCHIEDEN | par.16 Special-Zellen-Erweiterung des Spaltenbauers (column_build.rs:204) | PREREG_provocation.md par.16 |
| `MOSAIC_STACK_DRAW_RESERVATION` | aus (Opt-in =1) | diagnose | OFFEN | reparierte Blindzieh-Stopp-Regel: erwartete VERBESSERUNG in einer Einheit statt Niveau gegen Typmittelwert (self_play.rs::resolve_and_apply_stack_draw) | PREREG_stack_draw_reservation_rule.md par.5b |
| `MOSAIC_UPDATE_FEATURE_FIXTURE` | aus (Opt-in =1) | diagnose | - | schreibt die Feature-Golden-Fixture neu statt zu pruefen; NUR fuer gewollte Feature-Aenderungen (features.rs::maybe_update_fixture) | - |
| `MOSAIC_UPDATE_NET_PARITY_FIXTURE` | aus (Opt-in =1) | diagnose | - | schreibt die Netz-Paritaets-Fixture (engine/tests/fixtures/net_parity_champion.txt) neu statt zu pruefen; Pflicht-Schritt bei jedem Champion-Wechsel, siehe docs/promotion_checklist.md 5d (self_play.rs::maybe_update_net_parity_fixture) | - |
| `MOSAIC_SPALTENBAU_TRACE` | aus | diagnose | - | [SB]-Entscheidungs-Spur im Logstrom, additiv (column_build.rs:1081) | - |
| `MOSAIC_PLATTENBAU` | aus (0..7 oder auto) | diagnose | - | generischer Plattenbauer fuer alle 8 Wertungskriterien (plate_builder.rs:83) | STATUS.md Architektur-Fahrplan P.5 |
| `MOSAIC_PROVOKATION_SPALTE` | aus (0..5 oder auto) | diagnose | ENTSCHIEDEN | Beschneidung der Drafting-Aktionsmenge auf eine Ziel-Spalte, nie im Gating (provocation.rs:49) | PREREG_provocation.md par.4 |
| `MOSAIC_VORZUG_SPALTE` | aus (0..5) | diagnose | ENTSCHIEDEN | Vorzugsmodus: konstruktiver Spaltenzug wird bevorzugt gespielt, kein Verbot (provocation.rs:440) | PREREG_provocation.md |
| `MOSAIC_OPPONENT_DISRUPTION` | aus | diagnose | ENTSCHIEDEN | Gegner-Stoerungs-Schicht, nie im Gating (provocation.rs:703) | PREREG_opponent_disruption.md par.3 |
| `MOSAIC_VOLLE_VERSORGUNG` | aus (=1 oder true) | diagnose | ENTSCHIEDEN | Versorgungs-Deckenprobe: Fabriken deterministisch aus vollem Farbkreis (state.rs:208) | PREREG_placement_side.md par.10 |
| `MOSAIC_PLATTENKOPF_GAMES` | 1000 bzw. 400 je Messtest | diagnose | - | Partienzahl der Plattenkopf-Referenzlaeufe (#[ignore]-Messtests, scoring.rs:1330/1347/1374) | - |
| `MOSAIC_PLATTENKOPF_SIMS` | 150 | diagnose | - | Heuristik-Sims der Plattenkopf-Referenzlaeufe (scoring.rs:1348) | - |
| `MOSAIC_FROZEN_STATES_JSON` | unset (Pfad; Tests sonst uebersprungen) | diagnose | ENTSCHIEDEN | Pfad zum frozen-Drafting-States-Export fuer Entscheidungsgleichheits-Tests (net_mcts.rs, ort_cuda_/interleaved_-Tests) | PREREG_gpu_inference_path.md |
| `MOSAIC_DATA_EXCLUDE` | unset (Regex) | aktiv | - | Fenster-Pinning: Dateien vor Cache-Key-Bildung und Training ausschliessen (corpus_dataset.py, MosaicDataset.__init__) | - |
| `MOSAIC_CARRIER_MANIFEST` | policy_carrier_manifest_v20.json | aktiv | ENTSCHIEDEN | Dateiname des Policy-Traeger-Manifests im Korpus-Ordner (corpus_dataset.py, MosaicDataset.__init__) | PREREG_v21_window.md |
| `MOSAIC_IGNORE_POLICY_TARGET_VALID` | aus (nur =1) | aktiv | ENTSCHIEDEN | Traeger-A/B Arm B: setzt GENAU die Policy-Maskierung aus `policy_target_valid=false` aus, sodass der Policy-Kopf auch die Vorzugszuege des v2-Lehrers sieht (Wirkstelle corpus_dataset.py, MosaicDataset.__init__). Einmal beim Import gelesen (neural_net.py, `_IGNORE_PTV`), damit derselbe Prozess die Semantik nicht auf halber Strecke wechselt, und im Cache-Schluessel (`+ignore_ptv_v1` in corpus_dataset.py, `|ignore_ptv_v1` in file_cache_key.py) -- sonst zoege der zweite Lauf still den Cache des ersten. Die anderen Nullsetzungen (Tiling/Start, Traeger-Manifest, PCR) bleiben unberuehrt | PREREG_v22_window.md par.4 |
| `MOSAIC_CACHE_NOPACK` | aus (nur =1) | aktiv | ENTSCHIEDEN | erzwingt unkomprimiertes Cache-Format statt Bitpacking, eigener Cache-Key (corpus_dataset.py; Cache-Key in file_cache_key.py, per_file_cache_key) | PREREG_v21_window.md |
| `MOSAIC_CACHE_F32` | aus (nur =1) | aktiv | - | float32 statt float16 fuer states/policies im Cache, Notausstieg (corpus_dataset.py, _cache_f32_active) | - |
| `MOSAIC_PLANES_LAZY` | aus (nur =1) | aktiv | - | lazy HDF5-Pro-Index-Zugriff statt Planes-in-RAM, nur fuer knappes RAM (corpus_dataset.py, _maybe_load_planes_eager) | - |
| `MOSAIC_PLANES_H5_DIR` | unset | diagnose | - | Planes-HDF5 aus anderem Ordner oeffnen, OneDrive-Ausschlusstest (corpus_dataset.py) | - |
| `MOSAIC_VAL_POOL` | unset (Regex auf den Dateinamen) | aktiv | ENTSCHIEDEN | schraenkt die KANDIDATEN des Val-Splits ein: was nicht matcht, geht garantiert in den Trainings-Teil (train.py:536). Fuer Warmstarts von einem Modell, das eine Teilmenge desselben Korpus schon trainiert hat -- ein frei gezogener Val-Split enthielte dessen Dateien, und `--select-by-brier` waehlte den Checkpoint auf einem mitgesehenen Mass. Zu kleiner Pool = harter Abbruch statt stillschweigend kleinerem Val-Split; der Regex steht im Trainings-Manifest (train.py:505) | PREREG_v22_window.md par.6 |
| `MOSAIC_DISPLAY_CAL` | an (=0 schaltet ab) | aktiv | - | Platt-Kalibrierung der ANGEZEIGTEN Gewinnwahrscheinlichkeit, nicht der Suche (server.py:1409) | evaluations/artifacts/platt_fit_v21.json |
| `MOSAIC_DISPLAY_CAL_A` | -0.0033 | aktiv | - | Platt-A der Anzeige-Kalibrierung, modellspezifisch (server.py:1407) | evaluations/artifacts/platt_fit_v21.json |
| `MOSAIC_DISPLAY_CAL_B` | 0.9060 | aktiv | - | Platt-B der Anzeige-Kalibrierung, modellspezifisch (server.py:1408) | evaluations/artifacts/platt_fit_v21.json |
| `MOSAIC_GAME_TIMEOUT_SCALE` | 1.0 (geplant) | geplant | ENTSCHIEDEN | Multiplikator auf den Pro-Partie-Timeout im Self-Play; im Prereg beschrieben, Grep 2026-08-15 findet KEIN Vorkommen in engine/src oder *.py -- nicht verdrahtet | PREREG_gpu_inference_path.md (Deckel-Knopf) |
| `MOSAIC_UNLOCK_SHAPING_W` | - | tot | ENTSCHIEDEN | wirkungslos seit Zusammenfuehrung 2026-08-11, nur noch Warn-Stub (net_mcts.rs:1257) | PREREG_scoring_plate_injection.md |
| `MOSAIC_UNLOCK_BETA` | - | tot | ENTSCHIEDEN | wirkungslos seit Zusammenfuehrung 2026-08-11, nur noch Warn-Stub (net_mcts.rs:1257) | PREREG_scoring_plate_injection.md |
| `MOSAIC_ENDAWARE_W` | - | tot | ENTSCHIEDEN | entfernt 2026-08-13 (gemessen wirkungslos), nur noch Kommentar-Erwaehnung (net_mcts.rs:1322) | PREREG_scoring_plate_injection.md N7 |
| `MOSAIC_MUSTERREIHEN_W` | - | tot | ENTSCHIEDEN | entfernt 2026-08-13 (gemessen wirkungslos), nur noch Kommentar-Erwaehnung (net_mcts.rs:1323) | PREREG_scoring_plate_injection.md N7 |
| `MOSAIC_TORCH_IPC_ENABLED` | - | tot | ENTSCHIEDEN | Weg A (Torch-IPC) samt net_ipc.rs/torch_ipc_server.py entfernt 2026-08-15, gemessen verworfen | PREREG_gpu_inference_path.md par.9 |
| `MOSAIC_TORCH_IPC_PORT` | - | tot | ENTSCHIEDEN | Weg A entfernt 2026-08-15, siehe MOSAIC_TORCH_IPC_ENABLED | PREREG_gpu_inference_path.md par.9 |
| `MOSAIC_TORCH_IPC_SHM_DIR` | - | tot | ENTSCHIEDEN | Weg A entfernt 2026-08-15, siehe MOSAIC_TORCH_IPC_ENABLED | PREREG_gpu_inference_path.md par.9 |
