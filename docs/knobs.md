# MOSAIC_*-Laufzeit-Knoepfe

GENERIERT -- nicht von Hand editieren. Quelle: `engine/src/knob_registry.rs`
(direkt geparst, kein Wheel noetig), Generator: `tools/generate_knob_docs.py`.

Der Waechter-Test `knob_registry::tests::all_mosaic_env_vars_in_code_are_registered`
stellt sicher, dass jeder im Code vorkommende `MOSAIC_*`-Knopf hier steht.

Stand: 78 Knoepfe (47 aktiv, 23 diagnose, 7 tot, 1 geplant).

| Knopf | Default | Status | Zweck | Beleg |
|---|---|---|---|---|
| `MOSAIC_POINTS_UTILITY_W` | 0.0 | aktiv | Utility-Blend-Gewicht w des Punkte-Kopfs; danach per GUI-Regler set_aggression_params setzbar (net_mcts.rs:158) | PREREG_task28_aggression.md |
| `MOSAIC_AGGR_LAMBDA` | 0.0 | aktiv | Denial-Gewicht lambda (Gegner-Punkte-Abzug im Utility-Blend); GUI-Regler wie oben (net_mcts.rs:164) | PREREG_task28_aggression.md |
| `MOSAIC_VALUE_CAL_A` | 0.0 | aktiv | Logit-Shift A der monotonen Value-Kalibrierung (net_mcts.rs:321) | STATUS.md Task #30 |
| `MOSAIC_VALUE_CAL_B` | 1.0 | aktiv | Logit-Streckung B der Value-Kalibrierung (net_mcts.rs:327) | STATUS.md Task #30 |
| `MOSAIC_ROOT_CHILD_Q` | an (=0 schaltet ab) | aktiv | Wurzelkind-Q-Logging ins Self-Play-JSON (net_mcts.rs:219) | STATUS.md Task #35 |
| `MOSAIC_FLOOR_SHAPING_W` | 0.3 | aktiv | Gewicht der Floor-Straf-Korrektur am Netz-Blattwert (net_mcts.rs:405) | PREREG_search_path_remeasurements.md M1 |
| `MOSAIC_FLOOR_SHAPING_OPP_BIAS` | 1.0 | aktiv | Gegner-Gewichtung des Floor-Shapings, >1 belohnt Zuschieben (net_mcts.rs:422) | PREREG_aggression_style_measurement.md E2 |
| `MOSAIC_NUM_DETERMINIZATIONS` | 1 | aktiv | ISMCTS-Weltenzahl k, auf >=1 geklemmt (net_mcts.rs:734) | PREREG_ismcts_determinizations.md |
| `MOSAIC_WERTUNG_SHAPING_W` | 0.0 (1 oder 8 Werte) | aktiv | Wertungsplatten-EGO-Shaping-Gewicht je Kriterium (net_mcts.rs:1225) | PREREG_scoring_plate_injection.md |
| `MOSAIC_WERTUNG_ALPHA` | 2.0 (1 oder 8 Werte) | aktiv | Formungs-Exponent alpha je Kriterium (net_mcts.rs:1264) | PREREG_scoring_plate_injection.md |
| `MOSAIC_WERTUNG_ROUND_GAIN` | 0.0 | aktiv | rundenabhaengige Anhebung aller Alphas (net_mcts.rs:1360) | PREREG_scoring_plate_injection.md |
| `MOSAIC_WERTUNG_FLOOR_W` | 0.0 | aktiv | Strafleisten-Gegenterm im Wertungsplatten-Shaping (net_mcts.rs:1306) | PREREG_scoring_plate_injection.md |
| `MOSAIC_TILING_W` | 0.0 | aktiv | Tiling-Potenzial-Term (Heuristik-Summand solve_round_final_score) im Shaping (net_mcts.rs:1332) | PREREG_scoring_plate_injection.md |
| `MOSAIC_WERTUNG_SCALE_PROFILE` | aus (=0/leer; 1 oder an = Rundenprofil) | diagnose | Baustein 3: rundenabhaengiger Nenner SCALE_r=50*profil_r fuer den Wertungsplatten-/Spezialfeld-Term (Pfad A); Strafleisten-/Tiling-Term bleiben auf dem flachen Nenner (net_mcts.rs, wertung_scale_profile_active) | PREREG_shaping_scale_per_round.md par.4/par.6a |
| `MOSAIC_WERTUNG_STREUUNG_MAX` | 0.0 (aus) | aktiv | partieweise Streuung des Shaping-Gewichts aus dem Partie-Seed, Wert in [0,max] (net_mcts.rs:1154) | PREREG_ownership_corpus.md |
| `MOSAIC_OWNERSHIP_W` | 0.0 (aus) | aktiv | Zwei-Pole-Regler w_own: Blatt-Shift aus den erwarteten Plattenpunkten E_k des Ownership-Kopfs (net_mcts.rs, ownership_weight) | PREREG_ownership_consumer.md par.2 |
| `MOSAIC_OWNERSHIP_GEW` | 1.0 (1 oder 8 Werte) | aktiv | Gewicht je Kriterium innerhalb des Ownership-Pols; Stelle 7 wirkungslos (net_mcts.rs, ownership_weights) | PREREG_ownership_consumer.md par.2 |
| `MOSAIC_OWNERSHIP_SCALE` | 50.0 (1 oder 8 Werte) | diagnose | Baustein 2: Nenner je Kriterium im Ownership-Pol tanh(E_k/scale_k), ersetzt die feste 50; gemessene Werte fuer Arm S: k0~17, k1~1, k2~0,3 (net_mcts.rs, ownership_scale) | PREREG_reachability_target.md par.6 |
| `MOSAIC_REACH_TARGET_K1` | 0 (aus) | aktiv | Zielwechsel des Ownership-Kopfes fuer k1: Spalten-Atome (Index 6..11) tragen ab Runde 3 VOLLENDBARKEIT statt Realisierung; eigener HDF5-Cache-Schluessel (neural_net.py, _reach_target_k1_active) | PREREG_reachability_target.md |
| `MOSAIC_GUMBEL_TOP_M` | 0 (= Formel sims/16) | aktiv | fester Wurzelbreiten-Override m fuer Gumbel-Top-m (net_mcts.rs:2514) | PREREG_search_path_remeasurements.md M2 |
| `MOSAIC_TAU_ARGMAX_FROM_MOVE` | 0 (= aus) | aktiv | Self-Play: ab Halbzug N argmax statt Besuchs-Sampling (net_mcts.rs:2540) | PREREG_search_path_remeasurements.md M3 |
| `MOSAIC_DENIAL_TIEBREAK_EPS` | 0.0 (aus) | aktiv | eps-Fenster des Denial-Tie-Breaks E3 (net_mcts.rs:2556) | PREREG_denial_tiebreak.md |
| `MOSAIC_DENIAL_UNCERT_Z` | 0.0 (aus) | aktiv | z-Schwelle des E3b-Unsicherheits-Fensters (net_mcts.rs:2570) | PREREG_denial_tiebreak.md |
| `MOSAIC_DENIAL_MIN_VISIT_FRAC` | 0.5 | aktiv | Mindest-Besuchsanteil f des E3b-Besuchs-Gates (net_mcts.rs:2579) | PREREG_denial_tiebreak.md |
| `MOSAIC_COLOR_DENIAL_PROBE_Z` | 0.0 (aus) | diagnose | z-Schwelle des Stoerfenster-ZAEHLMODUS -- zaehlt nur, aendert die gespielte Aktion nicht (net_mcts.rs, color_denial_probe_with) | PREREG_opponent_disruption_v2.md par.5.2 |
| `MOSAIC_COLOR_DENIAL_PROBE_MIN_VISIT_FRAC` | 0.5 | diagnose | Mindest-Besuchsanteil des Stoerfenster-Zaehlmodus (net_mcts.rs, color_denial_probe_min_visit_frac) | PREREG_opponent_disruption_v2.md par.5.2 |
| `MOSAIC_IMPLICIT_MINIMAX_A` | 0.0 (aus) | aktiv | Mischgewicht alpha der Implicit-Minimax-Backups (Baier/Winands): Selektions-Q der Tiefe-≥1-Gumbel-Auswahl wird (1-alpha)*Q_MC + alpha*v_IM, v_IM per Minimax ueber besuchte Kinder rueckpropagiert. Welle-1-Pilot der Agenten-Kapselung (PREREG_agent_encapsulation.md): liest ueber SearchConfig::from_env() (net_mcts.rs) statt eines prozessglobalen OnceLock -- der Knopf bleibt die Default-Quelle, pro-Seite ueberschreibbar per Spec-Datei (models/<name>.spec.json) an net_arena_match/net_vs_net_arena_match/net_self_play_games | PREREG_implicit_minimax_backup.md par.1; PREREG_agent_encapsulation.md par.4 |
| `MOSAIC_R5_CHANCE_NODES` | an (=0 Altverhalten) | aktiv | Zufallsknoten fuer verdeckte Bonuschips im R5-Loeser, scharf seit 2026-08-10 (round5.rs:159) | PREREG_chance_nodes.md |
| `MOSAIC_R5_NET_SOLVER` | an (=0 Gegenprobe Netz) | aktiv | Netzpfad nutzt in Runde 5 den exakten Loeser statt des Netz-Blattwerts (round5.rs:183) | PREREG_chance_nodes.md Teil E |
| `MOSAIC_R5_NODE_BUDGET` | 200 | aktiv | Knotenbudget je R5-Entscheidung (round5.rs:199, NODE_BUDGET round5.rs:88) | PREREG_chance_nodes.md |
| `MOSAIC_ORT_CUDA_ENABLED` | aus | aktiv | Weg B: ORT-CUDA-Backend fuer eval_batch; wirkt nur mit Feature ort_cuda_probe (net_ort.rs:132) | PREREG_gpu_inference_path.md par.11 |
| `MOSAIC_INTERLEAVE_ENABLED` | aus | aktiv | Weg V: Sammel-Faden-Verschraenkung mehrerer Suchfaeden zu einem Batch (net_batcher.rs:217) | PREREG_async_search.md |
| `MOSAIC_INTERLEAVE_BATCH_MAX` | 16 (= EVAL_BATCH_MAX_N) | aktiv | Obergrenze der Sammel-Fuellung je eval_batch-Aufruf (net_batcher.rs:232) | PREREG_async_search.md |
| `MOSAIC_INTERLEAVE_FILL_TIMEOUT_US` | 200 | aktiv | Deadlock-Waechter-Fenster in Mikrosekunden je Fuell-Slot (net_batcher.rs:250) | PREREG_async_search.md |
| `MOSAIC_TILING_CACHE` | an (=0 schaltet ab) | aktiv | Tiling-Solver-Memoisierung, bitgleich, -20% Self-Play-Wandzeit (tiling_solver.rs:383) | - |
| `MOSAIC_TILING_CACHE_STATS` | aus (nur =1) | diagnose | zaehlt Schluessel-Wiederkehr im Tiling-Solver, kein Cache (tiling_solver.rs:371) | - |
| `MOSAIC_TILING_SELECT` | 0 (Bestandskriterium) | aktiv | Auswahlkriterium unter Top-K-Tilings: 0=punkte*P(Sieg), 1=reines P(Sieg) (tiling_solver.rs:822) | PREREG_t37_tiling_criterion.md |
| `MOSAIC_TILING_PLATTEN_W` | 0.0 (aus) | aktiv | plattenbewusste Tiling-Zugwahl R1-4: w * Endwertung nach Abschluss additiv (tiling_solver.rs:964) | PREREG_placement_side.md |
| `MOSAIC_TILING_PLATTEN_GEW` | 1.0 (1 oder 8 Werte) | aktiv | Gewicht je Kriterium fuer den Plattenwert der Tiling-Wahl (tiling_solver.rs:1023) | PREREG_placement_side.md |
| `MOSAIC_TILING_PUNKTE_W` | 0.0 (aus) | aktiv | Punkte-Kopf-Blend im Netz-Tiling-Stichentscheid; gemessen wirkungslos (self_play.rs:985; archive/history.md:10715) | - |
| `MOSAIC_OWNERSHIP_TILING_W` | 0.0 (aus) | aktiv | Ownership-Pol der Tiling-Zugwahl R1-4: marginale Feldwerte aus der Wurzelkarte, additiv zum Plattenterm (tiling_solver.rs, ownership_tiling_weight) | PREREG_ownership_consumer.md par.3 |
| `MOSAIC_OWNERSHIP_CONJ` | 0 (aus, Produktform) | aktiv | FORMumschaltung, keine Dosis: die konjunktiven Kriterien (k0/k1/k2/k3/k5/k7) kommen aus den gelernten Konjunktions-Atomen statt aus dem Produkt der Feldwahrscheinlichkeiten; additive k4/k6 bleiben auf den Feldlabels. Braucht den 140er-Kopf, sonst Rueckfall MIT Warnung (net_mcts.rs, ownership_conj) | PREREG_conjunction_terms.md par.4 |
| `MOSAIC_STACK_DRAW_RESEARCH` | aus | diagnose | Stapelzug nicht sammelaufloesen: nur der Peek wird angewandt, danach neue Suche (self_play.rs:609) | PREREG_chance_nodes.md |
| `MOSAIC_ASYM_VORZUG` | aus | diagnose | Baustein 1 (Arm S): je Self-Play-Partie bekommt GENAU EINE Seite den Bauer-Vorzug (vorzug:true), Seitenwahl deterministisch aus dem Partie-Seed 50/50; dome_vorzug faehrt in derselben Kette mit (self_play.rs, asym_vorzug_active/asym_vorzug_seite) | PREREG_asymmetric_curriculum.md par.3 |
| `MOSAIC_PROFILE_SELFPLAY` | aus (nur =1) | diagnose | Self-Play-Zeitprofil je Kategorie (profiling.rs:493) | PREREG_gpu_offloading.md |
| `MOSAIC_DATA_DIR` | <repo>/data | aktiv | Korpus-Ordner-Override fuer train/self_play/server (config.py:28; Kommentar-Erwaehnung net_mcts.rs:177) | PREREG_corpus_dose.md |
| `MOSAIC_PROFILES_PATH` | player_profiles.json im Projektroot | aktiv | Profil-Datei-Override, Pflicht fuer Test-/Zweitinstanzen seit Vorfall 2026-08-02 (player_profiles.py:51) | - |
| `MOSAIC_MEM_LOG_EVERY` | 2000 Batches (0 = aus) | diagnose | Abstand der [mem]-Zeilen im Training. Vorher fest 100, also 215 Zeilen je Epoche; der Epochen-Verlauf im Manifest deckt den Bedarf ab. Nicht ganz abschaltbar per Default, weil RAM Engpass 2 ist (train.py) | - |
| `MOSAIC_SPALTENBAU` | aus | diagnose | Spaltenbauer-Vorzugsschicht (Kriterium 1), nie im Gating (column_build.rs:78) | PREREG_provocation.md par.11ff |
| `MOSAIC_SPALTENBAU_SICHERHEITSNETZ` | aus (Opt-in =1) | diagnose | Baustein 1 Vollendbarkeits-Filter, seit par.15 default AUS (column_build.rs:134) | PREREG_provocation.md par.15 |
| `MOSAIC_SPALTENBAU_JACKPOT` | aus (Opt-in =1) | diagnose | Baustein 3a dominante Jackpot-Gewichtung, seit par.15 default AUS (column_build.rs:151) | PREREG_provocation.md par.15 |
| `MOSAIC_SPALTENBAU_SPECIAL` | aus (Opt-in =1) | diagnose | par.16 Special-Zellen-Erweiterung des Spaltenbauers (column_build.rs:204) | PREREG_provocation.md par.16 |
| `MOSAIC_SPALTENBAU_TRACE` | aus | diagnose | [SB]-Entscheidungs-Spur im Logstrom, additiv (column_build.rs:1081) | - |
| `MOSAIC_PLATTENBAU` | aus (0..7 oder auto) | diagnose | generischer Plattenbauer fuer alle 8 Wertungskriterien (plate_builder.rs:83) | STATUS.md Architektur-Fahrplan P.5 |
| `MOSAIC_PROVOKATION_SPALTE` | aus (0..5 oder auto) | diagnose | Beschneidung der Drafting-Aktionsmenge auf eine Ziel-Spalte, nie im Gating (provocation.rs:49) | PREREG_provocation.md par.4 |
| `MOSAIC_VORZUG_SPALTE` | aus (0..5) | diagnose | Vorzugsmodus: konstruktiver Spaltenzug wird bevorzugt gespielt, kein Verbot (provocation.rs:440) | PREREG_provocation.md |
| `MOSAIC_OPPONENT_DISRUPTION` | aus | diagnose | Gegner-Stoerungs-Schicht, nie im Gating (provocation.rs:703) | PREREG_opponent_disruption.md par.3 |
| `MOSAIC_VOLLE_VERSORGUNG` | aus (=1 oder true) | diagnose | Versorgungs-Deckenprobe: Fabriken deterministisch aus vollem Farbkreis (state.rs:208) | PREREG_placement_side.md par.10 |
| `MOSAIC_PLATTENKOPF_GAMES` | 1000 bzw. 400 je Messtest | diagnose | Partienzahl der Plattenkopf-Referenzlaeufe (#[ignore]-Messtests, scoring.rs:1330/1347/1374) | - |
| `MOSAIC_PLATTENKOPF_SIMS` | 150 | diagnose | Heuristik-Sims der Plattenkopf-Referenzlaeufe (scoring.rs:1348) | - |
| `MOSAIC_FROZEN_STATES_JSON` | unset (Pfad; Tests sonst uebersprungen) | diagnose | Pfad zum frozen-Drafting-States-Export fuer Entscheidungsgleichheits-Tests (net_mcts.rs, ort_cuda_/interleaved_-Tests) | PREREG_gpu_inference_path.md |
| `MOSAIC_DATA_EXCLUDE` | unset (Regex) | aktiv | Fenster-Pinning: Dateien vor Cache-Key-Bildung und Training ausschliessen (neural_net.py:1214) | - |
| `MOSAIC_CARRIER_MANIFEST` | policy_carrier_manifest_v20.json | aktiv | Dateiname des Policy-Traeger-Manifests im Korpus-Ordner (neural_net.py:1244) | PREREG_v21_window.md |
| `MOSAIC_CACHE_NOPACK` | aus (nur =1) | aktiv | erzwingt unkomprimiertes Cache-Format statt Bitpacking, eigener Cache-Key (neural_net.py:1290) | PREREG_v21_window.md |
| `MOSAIC_CACHE_F32` | aus (nur =1) | aktiv | float32 statt float16 fuer states/policies im Cache, Notausstieg (neural_net.py:1872) | - |
| `MOSAIC_PLANES_LAZY` | aus (nur =1) | aktiv | lazy HDF5-Pro-Index-Zugriff statt Planes-in-RAM, nur fuer knappes RAM (neural_net.py:2014) | - |
| `MOSAIC_PLANES_H5_DIR` | unset | diagnose | Planes-HDF5 aus anderem Ordner oeffnen, OneDrive-Ausschlusstest (neural_net.py:1105) | - |
| `MOSAIC_DISPLAY_CAL` | an (=0 schaltet ab) | aktiv | Platt-Kalibrierung der ANGEZEIGTEN Gewinnwahrscheinlichkeit, nicht der Suche (server.py:1409) | evaluations/platt_fit_v21.json |
| `MOSAIC_DISPLAY_CAL_A` | -0.0033 | aktiv | Platt-A der Anzeige-Kalibrierung, modellspezifisch (server.py:1407) | evaluations/platt_fit_v21.json |
| `MOSAIC_DISPLAY_CAL_B` | 0.9060 | aktiv | Platt-B der Anzeige-Kalibrierung, modellspezifisch (server.py:1408) | evaluations/platt_fit_v21.json |
| `MOSAIC_GAME_TIMEOUT_SCALE` | 1.0 (geplant) | geplant | Multiplikator auf den Pro-Partie-Timeout im Self-Play; im Prereg beschrieben, Grep 2026-08-15 findet KEIN Vorkommen in engine/src oder *.py -- nicht verdrahtet | PREREG_gpu_inference_path.md (Deckel-Knopf) |
| `MOSAIC_UNLOCK_SHAPING_W` | - | tot | wirkungslos seit Zusammenfuehrung 2026-08-11, nur noch Warn-Stub (net_mcts.rs:1257) | PREREG_scoring_plate_injection.md |
| `MOSAIC_UNLOCK_BETA` | - | tot | wirkungslos seit Zusammenfuehrung 2026-08-11, nur noch Warn-Stub (net_mcts.rs:1257) | PREREG_scoring_plate_injection.md |
| `MOSAIC_ENDAWARE_W` | - | tot | entfernt 2026-08-13 (gemessen wirkungslos), nur noch Kommentar-Erwaehnung (net_mcts.rs:1322) | PREREG_scoring_plate_injection.md N7 |
| `MOSAIC_MUSTERREIHEN_W` | - | tot | entfernt 2026-08-13 (gemessen wirkungslos), nur noch Kommentar-Erwaehnung (net_mcts.rs:1323) | PREREG_scoring_plate_injection.md N7 |
| `MOSAIC_TORCH_IPC_ENABLED` | - | tot | Weg A (Torch-IPC) samt net_ipc.rs/torch_ipc_server.py entfernt 2026-08-15, gemessen verworfen | PREREG_gpu_inference_path.md par.9 |
| `MOSAIC_TORCH_IPC_PORT` | - | tot | Weg A entfernt 2026-08-15, siehe MOSAIC_TORCH_IPC_ENABLED | PREREG_gpu_inference_path.md par.9 |
| `MOSAIC_TORCH_IPC_SHM_DIR` | - | tot | Weg A entfernt 2026-08-15, siehe MOSAIC_TORCH_IPC_ENABLED | PREREG_gpu_inference_path.md par.9 |
