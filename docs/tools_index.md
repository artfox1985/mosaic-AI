# Werkzeug-Index (GENERIERT)

**Diese Datei wird erzeugt, nicht von Hand gepflegt:**
`python -X utf8 tools/generate_tools_index.py`. Wer sie editiert, verliert die
Aenderung beim naechsten Lauf; `--check` meldet Drift.

Sie beantwortet die Frage, die eine gepflegte Liste nicht beantworten kann:
**wird das Ding noch gebraucht?** Das Kriterium ist nachpruefbar -- wer nennt die
Datei, und ruft er sie auf oder erwaehnt er sie nur? -- und ausdruecklich eine
Verwendungs-Evidenz, KEIN Loeschvorschlag.

| Stufe | Bedeutung |
| --- | --- |
| **WIRED** | Code, Test, Haken, Skill oder CLAUDE.md RUFT es auf (Nennung ausserhalb eines Kommentars). Haengt im Betrieb. |
| **DOCUMENTED** | nur `docs/` oder ein Code-KOMMENTAR nennt es: Werkzeug mit Anleitung oder Quellenangabe, nichts ruft es automatisch. Normalfall fuer Sonden. |
| **CHRONICLE** | nur `evaluations/` nennt es, also ein Messbericht oder eine Prereg. Typisch fuer Einmal-Skripte, deren Lauf vorbei ist. |
| **UNNAMED** | niemand nennt es ausser ihm selbst. Kandidat fuer eine Ruecksprache -- aber nicht automatisch tot: ein Werkzeug, das man von Hand aufruft, steht nirgends. |

**Stand: 228 Dateien** = 110 WIRED + 56 DOCUMENTED + 50 CHRONICLE + 12 UNNAMED.

## WIRED (110)

| Datei | Zweck | Genannt von | Letzter Commit |
| --- | --- | --- | --- |
| `tools/analyze_game_log.py` | tools/analyze_game_log.py -- wiederverwendbares Werkzeug zur Analyse von | Aufruf 13, Kommentar 10, Regeln 2, docs 4, evaluations 48 | 2026-09-10 |
| `tools/anchor_arena.py` | Arena gegen den EINGEFRORENEN Anker (B2 der Kapselungs-Kette). | Aufruf 1, Kommentar 1, Regeln 1, docs 4, evaluations 4 | 2026-08-31 |
| `tools/arena.py` | Mosaic-AI — Arena (Rust-Engine) | Aufruf 18, Kommentar 9, Regeln 2, docs 7, evaluations 28 | 2026-08-05 |
| `tools/argmax_profile.sh` | argmax-Instrument (Tor 2a, docs/generation_loop.md): 200 Partien @400, Seed 20260931, deterministisch, | Regeln 1, evaluations 4 | 2026-09-04 |
| `tools/backup_common.ps1` | (kein Kopfkommentar) | Aufruf 3, Kommentar 1, docs 1 | 2026-08-31 |
| `tools/build_cache_incremental.py` | Cache JE DATEI, auch WAEHREND der Erzeugung (PREREG_cache_build_time.md par.6, | Aufruf 7, Kommentar 1, docs 6, evaluations 9 | 2026-08-31 |
| `tools/build_cache_parallel.py` | Parallel gebauter Trainings-Cache (PREREG_cache_build_time.md Hebel 1). | Aufruf 3, Kommentar 2, docs 2 | 2026-08-31 |
| `tools/build_frozen_eval_set.py` | tools/build_frozen_eval_set.py — Task #87: eingefrorenes, generationsuebergreifendes | Aufruf 2, docs 2, evaluations 2 | 2026-09-01 |
| `tools/build_frozen_golden_probe.py` | Golden-Probe-Generator fuer eingefrorene Champion-Artefakte | Aufruf 1, docs 2, evaluations 2 | 2026-08-29 |
| `tools/build_frozen_oracle_labels.py` | tools/build_frozen_oracle_labels.py -- Task #89 Teil B, Schritt 1: Oracle-Labels | Aufruf 5, Kommentar 1, docs 3, evaluations 3 | 2026-09-01 |
| `tools/cache_inventory.py` | Inventar der Datei-Cache-Bloecke: welcher Block gehoert zu welcher Datei? | Regeln 1, docs 3, evaluations 2 | 2026-08-30 |
| `tools/check_conventions.py` | tools/check_conventions.py -- Konventions-Linter (Baustein A5). | Aufruf 6, Kommentar 2, Regeln 2, docs 4, evaluations 2 | 2026-09-06 |
| `tools/conjunction_head_selfcheck.py` | tools/conjunction_head_selfcheck.py -- Selbsttest der Konjunktions-Erweiterung | Aufruf 1, Kommentar 1, docs 1, evaluations 1 | 2026-08-13 |
| `tools/corpus_sanity_check.py` | Sanity-Check eines Self-Play-Korpus auf den sechs Standard-Kennzahlen | Aufruf 8, docs 3, evaluations 19 | 2026-09-05 |
| `tools/diagnosis.py` | tools/diagnosis.py — Sanity Check der Trainingsdaten | Aufruf 11, Kommentar 4, docs 3, evaluations 12 | 2026-09-07 |
| `tools/e3b_firing_rate.py` | E3b Stufe 1 (PREREG_denial_tiebreak.md): Feuerrate des Denial-Tie-Breaks | Aufruf 1, Kommentar 1, docs 1, evaluations 2 | 2026-08-25 |
| `tools/elo_tracker.py` | Mosaic-AI -- Elo-Tracking-Infrastruktur (Task #62) | Aufruf 4, Kommentar 1, Regeln 3, docs 6, evaluations 5 | 2026-08-31 |
| `tools/freeze_heuristic.py` | Friert eine Heuristik als vollstaendiges Agenten-Artefakt ein. | Aufruf 1, docs 3, evaluations 3 | 2026-09-07 |
| `tools/freeze_trunk_selfcheck.py` | tools/freeze_trunk_selfcheck.py -- Selbsttest des Trunk-Einfrier-Modus | Aufruf 1, docs 1, evaluations 1 | 2026-08-16 |
| `tools/frozen_champion_worker.py` | Wave-3-Worker (PREREG_agent_encapsulation.md par.8): persistenter Prozess | Aufruf 5, Kommentar 1, Regeln 1, docs 1 | 2026-08-28 |
| `tools/frozen_name_dialect.py` | Uebersetzt Heuristik-Variantennamen an der Grenze zu einem eingefrorenen | Aufruf 1, Kommentar 5, docs 2 | 2026-08-28 |
| `tools/frozen_referee_match.py` | Wave-3-Referee (PREREG_agent_encapsulation.md par.8): Partie-Serie Seite A | Aufruf 4, Kommentar 1, Regeln 1, docs 3, evaluations 6 | 2026-08-31 |
| `tools/generate_carrier_manifest.py` | Erzeuger fuer Policy-Traeger-Manifeste (Rekonstruktion, 2026-08-29). | Aufruf 1, Regeln 1, docs 3, evaluations 5 | 2026-09-04 |
| `tools/generate_knob_docs.py` | Erzeugt docs/knobs.md aus der MOSAIC_*-Knopf-Registratur. | Aufruf 2, Kommentar 1, Regeln 1, docs 3 | 2026-08-27 |
| `tools/generate_prereg_index.py` | tools/generate_prereg_index.py -- erzeugt den Tabellenteil von | Aufruf 2, Regeln 4, docs 4, evaluations 4 | 2026-08-15 |
| `tools/gpu_batch_throughput.py` | Teil 1 der GPU-Inferenz-Batcher-Machbarkeitsprobe | Aufruf 1, Kommentar 1, docs 1, evaluations 2 | 2026-08-25 |
| `tools/gumbel_scale_calibration.py` | tools/gumbel_scale_calibration.py -- Task #18, Schritt 1: ist GUMBEL_C_SCALE | Aufruf 1, Kommentar 1, docs 3, evaluations 5 | 2026-08-25 |
| `tools/hooks/pre-commit` | tools/hooks/pre-commit -- ruft den Konventions-Linter (Baustein A5) auf. | Aufruf 3, Regeln 2, docs 2, evaluations 2 | 2026-09-06 |
| `tools/hooks/pre-push` | tools/hooks/pre-push -- Golden-Waechter (A1-A4, `cargo test --release`), aber | Aufruf 4, Kommentar 7, Regeln 1, docs 2, evaluations 2 | 2026-09-07 |
| `tools/hooks/python_dll_path.sh` | tools/hooks/python_dll_path.sh -- EINE Herleitung des Verzeichnisses mit der | Aufruf 2, Kommentar 1, evaluations 1 | 2026-09-06 |
| `tools/mosaic_backup.ps1` | (kein Kopfkommentar) | Aufruf 2, Regeln 2, docs 4, evaluations 1 | 2026-08-31 |
| `tools/mosaic_backup_credential.ps1` | (kein Kopfkommentar) | Aufruf 1, docs 1 | 2026-08-31 |
| `tools/night_v28_chain.sh` | v27-Kette: Traeger-Kennzahl, Traeger-Manifest, Fenster, Bloecke, Monolith, Training v28-b01. | Aufruf 1, Regeln 1, evaluations 1 | 2026-09-10 |
| `tools/offline_diagnosis.py` | tools/offline_diagnosis.py — Offline-Diagnose eines trainierten Checkpoints: | Aufruf 8, Kommentar 3, docs 3, evaluations 8 | 2026-08-28 |
| `tools/offline_vs_arena.py` | tools/offline_vs_arena.py -- Sagen unsere Offline-Metriken die Arena voraus? | Aufruf 1, Kommentar 2, docs 2, evaluations 2 | 2026-08-25 |
| `tools/oracle_metrics.py` | tools/oracle_metrics.py -- Task #89 Teil B, Schritte 2-3: Offline-Metriken der | Aufruf 7, Kommentar 1, docs 3, evaluations 9 | 2026-09-02 |
| `tools/paired_arena_arm_worker.py` | Ein-Arm-Worker für den gepaarten Speed-Bündel-A/B (Phase 2a/2b, | Aufruf 7, Kommentar 1, docs 1, evaluations 8 | 2026-09-03 |
| `tools/paired_arena_env_ab.py` | tools/paired_arena_env_ab.py -- generischer gepaarter Zwei-Arm-A/B fuer | Aufruf 13, docs 5, evaluations 26 | 2026-09-03 |
| `tools/paired_arena_ismcts.py` | Gepaarter A/B fuer Task #65 (ISMCTS-Mehrfach-Determinisierung): ALT | Aufruf 4, Kommentar 2, docs 2 | 2026-08-25 |
| `tools/paired_arena_plate_ab.py` | Gepaarter A/B fuer Task #93 (Wertungsplatten-Shaping-Toggle, 2026-07-25): | Aufruf 1, Kommentar 2, docs 3, evaluations 4 | 2026-09-02 |
| `tools/paired_arena_plate_arm_worker.py` | Ein-Arm-Worker fuer den Task-#93-Wertungsplatten-Shaping-A/B | Aufruf 1, docs 2 | 2026-07-28 |
| `tools/paired_arena_round5.py` | Gepaarter A/B fuer die round5-Knoten-primaer-Umstellung (Determinismus-Fix, | Aufruf 1, Kommentar 1, docs 2 | 2026-08-25 |
| `tools/paired_arena_shrink_ab.py` | Gepaarter A/B fuer Task #78 (v12c Value-Shrinkage-Toggle, 2026-07-23): | Aufruf 1, Kommentar 1, docs 3, evaluations 1 | 2026-09-02 |
| `tools/paired_arena_shrink_arm_worker.py` | Ein-Arm-Worker fuer den Task-#78-Value-Shrinkage-A/B (VALUE_SHRINK_ENABLED | Aufruf 2, docs 2 | 2026-07-23 |
| `tools/paired_arena_speedbundle.py` | Gepaarter A/B: ALT (Commit b0c6a9c, Stand VOR dem Stufe-2-Speed-Bündel) | Aufruf 3, docs 2, evaluations 1 | 2026-08-11 |
| `tools/paired_gating.py` | Gepaartes Netz-vs-Netz-Gating als STANDARD-Werkzeug fuer Kandidaten- | Aufruf 14, Kommentar 3, docs 6, evaluations 22 | 2026-09-10 |
| `tools/pattern_row_availability.py` | Wie oft KANN Musterreihe r (Kapazitaet r) ueberhaupt geschlossen werden? | Aufruf 1, docs 3, evaluations 1 | 2026-08-25 |
| `tools/plate_head_labels.py` | Label-Extraktor fuer den Plattenkopf (`evaluations/PREREG_plate_head.md`). | Aufruf 2, docs 2, evaluations 2 | 2026-08-13 |
| `tools/plate_points_from_arena.py` | Wertungsplatten-Punkte und Strafleiste aus gepaarten Arena-Ergebnissen ziehen. | Aufruf 2, Kommentar 1, Regeln 2, docs 3, evaluations 16 | 2026-09-10 |
| `tools/plate_rank_invariance.py` | Mosaic-AI -- Task #5, Teil 1a: Score-Luecke vs. Platten-Signal (Gumbel-Rang- | Aufruf 1, docs 2, evaluations 2 | 2026-08-25 |
| `tools/platt_fit.py` | tools/platt_fit.py -- Platt-Kalibrierungs-Fit des Value-Kopfs gegen den | Aufruf 1, Kommentar 1, docs 4, evaluations 2 | 2026-08-07 |
| `tools/probes/anchor_referee_parity_probe.py` | DAS TOR vor der Anker-Umstellung: spielt der Referee-Pfad dieselben Partien | Aufruf 1, evaluations 2 | 2026-08-28 |
| `tools/probes/arena_column_probe.py` | Volle Spalten in der ARENA -- aus den Partie-Logs rekonstruiert. | Aufruf 3, docs 2, evaluations 11 | 2026-09-10 |
| `tools/probes/bootstrap_native_default_probe.py` | Fixier-Test: nativ ist der DEFAULT, entstaucht nur die Blockliste. | Aufruf 1, docs 1, evaluations 1 | 2026-08-31 |
| `tools/probes/cache_parity_probe.py` | Bit-Identitaet zweier Trainings-Caches (PREREG_cache_build_time.md par.4). | Aufruf 4, evaluations 1 | 2026-08-28 |
| `tools/probes/column_build_prior_mass.py` | Gate C / par.16.1 Sonde: Policy-Priormasse auf Spaltenbau-Aktionen. | Aufruf 1, evaluations 2 | 2026-08-29 |
| `tools/probes/column_build_structural_probe.py` | Strukturelle Spaltenbau-Messung an VORHANDENEN Arena-Partien (Auftrag | Aufruf 3, Kommentar 1, Regeln 2, docs 1, evaluations 1 | 2026-08-25 |
| `tools/probes/column_completion_gap_probe.py` | Vollendungs-Luecken-Sonde (Auftrag 2026-08-23, Erweiterung von | Aufruf 1, Regeln 2, docs 1 | 2026-08-25 |
| `tools/probes/conjunction_marginal_normal_play.py` | Was sagt der Konjunktions-Kopf im NORMALEN Spiel voraus -- und was passiert? | Aufruf 1, Kommentar 1, docs 1, evaluations 1 | 2026-08-18 |
| `tools/probes/corpus_state_diversity_probe.py` | Wieviel Stellungsvielfalt kostet der v2-Vorzug? | Aufruf 3, Kommentar 1, docs 1, evaluations 6 | 2026-09-07 |
| `tools/probes/file_cache_key_probe.py` | Schluessel-Tor fuer den Datei-Cache (PREREG_cache_build_time.md par.6). | Aufruf 1, evaluations 1 | 2026-08-31 |
| `tools/probes/floor_action_aversion_gate.py` | Tor fuer PREREG_floor_action_aversion.md par.6: Prior gegen Suche. | Aufruf 1, docs 3, evaluations 1 | 2026-08-25 |
| `tools/probes/human_row_profile_probe.py` | Das Musterreihen-Profil eines Spielers, DER ES KANN. | Aufruf 1, docs 1, evaluations 2 | 2026-08-25 |
| `tools/probes/implicit_minimax_selfplay_corpus_eval.py` | Der Self-Play-Arm des Implicit-Minimax-Knopfs ist eine KORPUS-Frage. | Aufruf 1, evaluations 1 | 2026-08-30 |
| `tools/probes/long_row_prior_gate.py` | PREREG_long_row_payoff.md par.2, Zweig A: Prior-Sichtbarkeit. | Aufruf 2, docs 2, evaluations 1 | 2026-08-25 |
| `tools/probes/ownership_gate_a.py` | Gate A head-quality evaluation for the ownership_weight sweep | Aufruf 1, evaluations 4 | 2026-08-25 |
| `tools/probes/ownership_map_completion_sites_probe.py` | PREREG_heuristic_v2_long_rows.md par.3b.8 Stufe A -- Karten-Diagnose an | Aufruf 1, evaluations 1 | 2026-08-29 |
| `tools/probes/paired_corpus_divergence_probe.py` | Bedingte Vielfalt: wie viel Streuung im Korpus kommt vom VERHALTEN, nicht vom Spiel? | Aufruf 1, evaluations 4 | 2026-09-07 |
| `tools/probes/penalty_track_probe.py` | Strafleisten-Auslastung je Seite (Standard-Kennzahl 3, CLAUDE.md). | Aufruf 1, Kommentar 1, docs 2, evaluations 2 | 2026-08-25 |
| `tools/probes/reachability_buffer_spread.py` | Arm-P-Sperre aus PREREG_reachability_target.md par.12: spreizt der Puffer? | Aufruf 1, docs 1, evaluations 1 | 2026-08-25 |
| `tools/probes/row_initiation_probe.py` | PREREG_long_row_payoff.md par.2a: Reihen-INITIIERUNG gegen -FORTSETZUNG. | Aufruf 2, evaluations 2 | 2026-08-25 |
| `tools/probes/row_opportunity_probe.py` | PREREG_long_row_payoff.md par.2a, Stufe 2: Initiierung NORMIERT auf Gelegenheit. | Aufruf 1, evaluations 2 | 2026-08-25 |
| `tools/probes/row_preference_probe.py` | Musterreihen-Praeferenz-Sonde (Auftrag 2026-08-23): prueft die Nutzer- | Aufruf 2, Regeln 2, docs 1, evaluations 2 | 2026-08-25 |
| `tools/probes/server_log_points_probe.py` | Punktbilanz der Server-Partien Mensch gegen KI, je Runde und Kategorie | Aufruf 1, docs 1, evaluations 2 | 2026-09-05 |
| `tools/probes/shaping_scale_e_distribution.py` | Verteilung von `E` je Kriterium und je RUNDE -- Vorbedingung zweier Preregs. | Aufruf 1, evaluations 3 | 2026-08-25 |
| `tools/probes/sibling_order_stability.py` | Ordnet der Ownership-Kopf die GESCHWISTERZUEGE stabil -- oder ist es Rauschen? | Aufruf 1, evaluations 5 | 2026-08-25 |
| `tools/probes/sibling_order_vs_predicate.py` | Ordnet der Ownership-Kopf die Geschwisterzuege wie das PRAEDIKAT selbst? | Aufruf 2, evaluations 1 | 2026-08-25 |
| `tools/probes/tiling_geometry_probe.py` | Tiling: Punkte gegen Nachbarschafts-Geometrie (PREREG_geometric_envelope.md par.8.12). | Aufruf 2, Kommentar 1, evaluations 3 | 2026-09-07 |
| `tools/probes/triangle_hull_coverage_probe.py` | PREREG_heuristic_v2_long_rows.md par.3b.8 Stufe D -- Huellen-Deckung. | Aufruf 2, Kommentar 1, docs 1, evaluations 3 | 2026-09-03 |
| `tools/probes/v2_envelope_arena.py` | STILLGELEGT am 2026-08-27 (B4a). NICHT MEHR LAUFFAEHIG auf dem heutigen Build. | Aufruf 2, docs 2, evaluations 2 | 2026-08-27 |
| `tools/probes/v2_teacher_arena.py` | STILLGELEGT am 2026-08-27 (B4a). NICHT MEHR LAUFFAEHIG auf dem heutigen Build. | Aufruf 1, docs 2, evaluations 1 | 2026-08-27 |
| `tools/promote_v25_b01.sh` | Promotion v25-b01 (docs/promotion_checklist.md, Skill mosaic-champion-promotion). | Aufruf 1, evaluations 1 | 2026-09-08 |
| `tools/r5_value_calibration.py` | Mosaic-AI -- Runde-5-Value-/Punkte-Kopf-Kalibrierung gegen exakte Ground Truth | Aufruf 3, Kommentar 2, docs 3, evaluations 7 | 2026-08-30 |
| `tools/relabel_drafts_with_teacher.py` | par.3b.9 -- Lehrer-Relabeling der Draft-Entscheidungen (DAgger-Muster). | Aufruf 1, docs 2, evaluations 3 | 2026-08-29 |
| `tools/restic_env.sh` | Sammelstelle fuer die restic-Umgebung. Von tools/restic_*.sh gesourcet. | Aufruf 1, docs 1, evaluations 2 | 2026-09-07 |
| `tools/restic_snapshot_inventory.py` | Aggregiert `restic ls <snapshot> --json` (auf stdin) nach Verzeichnis und Endung. | Aufruf 1, evaluations 1 | 2026-09-07 |
| `tools/run_longrow_teacher_arena.sh` | Kann der HEURISTIK-LEHRER lange Musterreihen, oder kann es niemand? | Aufruf 1, Kommentar 2, evaluations 3 | 2026-08-24 |
| `tools/run_lr_init_arena.sh` | PREREG_long_row_payoff.md par.3/B1, Messkette Schritt 2: | Aufruf 2, Kommentar 1, evaluations 2 | 2026-08-24 |
| `tools/run_v2_teacher_arena.sh` | PREREG_heuristic_v2_long_rows.md par.5.3, Messkette Schritt 3: | Aufruf 1, Kommentar 1, evaluations 3 | 2026-08-24 |
| `tools/scoring_tile_impact.py` | Mosaic-AI -- Wertungsplatten-Diagnose, Teil 1: Punkteanteil aus Wertungsplatten | Aufruf 2, Kommentar 1, docs 2, evaluations 1 | 2026-08-25 |
| `tools/scoring_tile_sensitivity.py` | Mosaic-AI -- Wertungsplatten-Diagnose, Teil 3: Policy-/Value-Sensitivitaet | Aufruf 2, Kommentar 1, docs 2, evaluations 2 | 2026-08-25 |
| `tools/seed_position_curation.py` | Seeding-Baustein 1 (PREREG_start_position_seeding.md par.2): Stellungssatz | Aufruf 2, docs 2, evaluations 2 | 2026-09-04 |
| `tools/seed_selection_plates.py` | tools/seed_selection_plates.py -- Seed-Auswahl fuer den Plattenkopf-Versuch | Aufruf 1, Kommentar 1, docs 2, evaluations 3 | 2026-08-25 |
| `tools/set_champion.py` | tools/set_champion.py -- setzt den amtierenden Champion fuer das Server- | Aufruf 4, Kommentar 1, Regeln 1, docs 5 | 2026-07-27 |
| `tools/smoke_action_temp_compare.py` | Vergleicht die drei Korpora der Rauchprobe aus tools/smoke_action_temp_modes.sh. | Aufruf 1, evaluations 1 | 2026-09-07 |
| `tools/smoke_action_temp_modes.sh` | Rauchprobe des Knopfs MOSAIC_ACTION_TEMP (PREREG_v25_window.md par.14/14d): BELEGT, dass | Aufruf 1, evaluations 1 | 2026-09-07 |
| `tools/snapshot_models.ps1` | (kein Kopfkommentar) | Aufruf 1, docs 4 | 2026-08-31 |
| `tools/spec_add_field.py` | Ein Pflichtfeld in lebende Spec-Dateien nachziehen (models/*.spec.json). | Aufruf 3, docs 1, evaluations 3 | 2026-09-07 |
| `tools/stamp_cache_key.py` | Praegt einem VORHANDENEN Trainings-Cache seinen Fenster-Schluessel auf | Aufruf 3, docs 2 | 2026-08-28 |
| `tools/tests/test_spec_add_field.py` | tools/spec_add_field.py: Feld landet vor 'heuristik_variante', wird nie ueberschrieben, --check schreibt nicht. | Aufruf 1, evaluations 1 | 2026-09-06 |
| `tools/tests/test_tiling_geometry_probe.py` | Reine Python-Logik der Reihen-Alter-Sonde (tools/probes/tiling_geometry_probe.py, | Aufruf 1, evaluations 1 | 2026-09-06 |
| `tools/tests/test_train_manifest_flags.py` | Jedes argparse-Flag von train.py mit Verhaltenswirkung landet im Manifest (`_cli_args`). | Aufruf 1, Kommentar 1, evaluations 1 | 2026-09-06 |
| `tools/tests/train_resume_pause_test.sh` | Funktionstest fuer Zwischenstand je Epoche, --resume und Pause auf Zuruf (train.py). | Aufruf 2, Kommentar 1, docs 1, evaluations 1 | 2026-09-06 |
| `tools/tiling_candidate_spread.py` | tools/tiling_candidate_spread.py -- lohnen sich Task #20 und #21 ueberhaupt? | Aufruf 1, Kommentar 2, docs 1, evaluations 2 | 2026-09-03 |
| `tools/train_2d_vs_flat_fs.py` | tools/train_2d_vs_flat_fs.py -- Task #11 Phase 2 (M3), siehe | Aufruf 1, Kommentar 2, docs 1, evaluations 3 | 2026-08-25 |
| `tools/train_corpus_dose.py` | tools/train_corpus_dose.py -- Korpus-Dosis-Wirkungs-Vorstudie (Task #14- | Aufruf 2, Kommentar 1, docs 2, evaluations 4 | 2026-08-25 |
| `tools/train_seed_sweep.py` | tools/train_seed_sweep.py -- Trainings-A/B mit MEHREREN Seeds je Arm | Aufruf 2, docs 2, evaluations 2 | 2026-08-25 |
| `tools/verify_backup.ps1` | (kein Kopfkommentar) | Aufruf 1, Regeln 1, docs 3 | 2026-09-09 |
| `tools/verify_frozen_heuristic.py` | Prueft ein eingefrorenes Heuristik-Artefakt gegen seine Golden Probe. | Aufruf 3, Kommentar 3, Regeln 1, docs 2, evaluations 2 | 2026-08-28 |
| `tools/window_train_split.py` | tools/window_train_split.py -- den Train/Val-Split von train.py VORAB | Aufruf 1, docs 2, evaluations 4 | 2026-09-02 |

## DOCUMENTED (56)

| Datei | Zweck | Genannt von | Letzter Commit |
| --- | --- | --- | --- |
| `tools/arena_compact.py` | Gepaarte Arena-Ergebnisse auf das Verwertbare eindampfen. | docs 3, evaluations 1 | 2026-08-25 |
| `tools/arena_trends.py` | Mosaic-AI — Arena-Trend-Log (Task #92, 2026-07-24, Nutzer-Anstoss). | docs 2, evaluations 1 | 2026-07-24 |
| `tools/atom_skill_check.py` | Bedingte Skill-Pruefung je Atom fuer die 34 Zusatzziele des Ownership-Kopfs. | docs 2, evaluations 2 | 2026-08-25 |
| `tools/build_cache_serial.py` | Seriell gebauter Referenz-Cache (PREREG_cache_build_time.md par.4). | docs 2 | 2026-08-27 |
| `tools/build_release.py` | Mosaic-AI — Release-Build-Skript (Task #96) | docs 4, evaluations 1 | 2026-08-15 |
| `tools/cache_build_socket.sh` | Cache-Bloecke fuer die 400 fertigen v25-SOCKEL-Dateien, waehrend die Ausflug-Haelfte | docs 1, evaluations 1 | 2026-09-09 |
| `tools/chance_node_pretest.py` | tools/chance_node_pretest.py -- Billiger Vortest zur Stochastic-MuZero- | docs 2 | 2026-08-25 |
| `tools/claude_play.py` | Spiel-Interface Claude gegen Netz (PREREG_claude_play_interface.md, Nutzer-Auftrag 2026-09-06). | docs 1, evaluations 7 | 2026-09-10 |
| `tools/color_denial_probe.py` | PREREG_opponent_disruption_v2.md, Stufe 1 -- die ECHTE, vorregistrierte | Kommentar 1, docs 1, evaluations 1 | 2026-08-16 |
| `tools/column_build_trace.py` | Entscheidungs-Spur des Spaltenbauers evaluate (`[SB]`-Logzeilen). | Kommentar 1, docs 2, evaluations 1 | 2026-08-25 |
| `tools/disruption_window_rate.py` | PREREG_opponent_disruption_v2.md, Stufe 0 + Stufe-1-Offline-Ersatz. | docs 1, evaluations 1 | 2026-08-25 |
| `tools/dome_split_diagnosis.py` | tools/dome_split_diagnosis.py -- TASK B "Zerlegungs-Diagnose" (Nutzer-Auftrag | Kommentar 1, docs 2, evaluations 3 | 2026-08-25 |
| `tools/export_frozen_drafting_states.py` | Exportiert die "sauberen" Phase::Drafting-Zustaende eines eingefrorenen | docs 1, evaluations 1 | 2026-08-12 |
| `tools/extract_kat2_examples.py` | tools/extract_kat2_examples.py — Extrahiert konkrete Beispiel-Zustände fuer | docs 1 | 2026-07-23 |
| `tools/game_log_report.py` | tools/game_log_report.py -- die MARKDOWN-DARSTELLUNG einer Partie-Analyse. | Kommentar 1, docs 2, evaluations 2 | 2026-09-10 |
| `tools/generate_tools_index.py` | Erzeugt `docs/tools_index.md`: was liegt in tools/, wozu, und wird es benutzt? | docs 1 | 2026-09-09 |
| `tools/git_tree.py` | (kein Kopfkommentar) | docs 1 | 2026-07-23 |
| `tools/gpu_inference_path_ipc_roundtrip.py` | Schritt 1 (Weg A) aus `evaluations/PREREG_gpu_inference_path.md` Abschnitt 6. | docs 2 | 2026-08-25 |
| `tools/hybrid_paired_arena.py` | Task #88 (Hybrid-Suche 2x2, kausaler Kopf-Test) -- gepaarter Arena-Runner | docs 3, evaluations 1 | 2026-09-02 |
| `tools/interleave_batch_probe.py` | Teil-1-Probe zu `evaluations/PREREG_gpu_offloading.md`: ist ein | docs 1, evaluations 1 | 2026-08-25 |
| `tools/model_info.py` | tools/model_info.py — Zeigt Metadaten eines gespeicherten Modells an. | docs 1, evaluations 1 | 2026-07-23 |
| `tools/pattern_row_throughput.py` | Wieviele Fliesen landen je RASTERREIHE und RUNDE tatsaechlich auf der Kuppel? | docs 3 | 2026-08-13 |
| `tools/plate_head_smoketest.py` | Rauchtest fuer den Plattenkopf (`evaluations/PREREG_plate_head.md`). | docs 2, evaluations 1 | 2026-08-13 |
| `tools/play_rule_cost.py` | Task #13: Was kostet die Play-Regel (visit-proportionales Sampling auf einem | docs 2 | 2026-08-25 |
| `tools/points_head_stage2.py` | Mosaic-AI -- PREREG_points_head_plates.md, Stufe 2 (ALLEINIGER Entscheidungspunkt, | docs 2, evaluations 1 | 2026-08-25 |
| `tools/pool_arena_ab.py` | tools/pool_arena_ab.py -- mehrere Bloecke eines gepaarten Arm-A/Bs zu EINER | Kommentar 1, docs 2 | 2026-08-28 |
| `tools/probes/action_count_profile_probe.py` | Verteilung der Aktionszahl je Runde und Zug-Index innerhalb der Runde. | Kommentar 1, evaluations 2 | 2026-09-07 |
| `tools/probes/asym_early_rate_check.py` | Fruehwarnung nach Block S1 des Asym-Korpus (PREREG_asymmetric_curriculum par.11). | docs 1, evaluations 1 | 2026-08-20 |
| `tools/probes/asym_value_sibling_check.py` | Teilfrage B des Asym-Curriculums (PREREG_asymmetric_curriculum.md par.6): | docs 1, evaluations 3 | 2026-08-29 |
| `tools/probes/bootstrap_coherence_probe.py` | Abnahme fuer Arm K: Bootstrap-Kohaerenz (Summen-Normierung) im WDL-Ziel. | docs 1, evaluations 3 | 2026-08-31 |
| `tools/probes/carrier_mask_at_merge_probe.py` | Abnahme des Traeger-Umbaus (2026-08-31): Maske beim FENSTERBAU statt im Block. | Kommentar 1, evaluations 1 | 2026-08-31 |
| `tools/probes/column_completion_legality_probe.py` | Legalitaets-Stufe der Vollendungs-Sonde (Auftrag 2026-08-23, | Kommentar 1, docs 3, evaluations 2 | 2026-08-30 |
| `tools/probes/conjunction_calibration_fit.py` | Kalibrierung des Konjunktions-Kopfes auf dem ausgesperrten Bewertungssatz. | docs 1 | 2026-08-25 |
| `tools/probes/conjunction_reliability_by_source.py` | Kennlinie des Konjunktions-Kopfes, getrennt nach Quelle. | docs 1 | 2026-08-25 |
| `tools/probes/corpus_column_outcome_symmetry_probe.py` | PREREG_heuristic_v2_long_rows.md par.3b.4, Stufe 0 -- Symmetrie-Pruefung. | docs 2, evaluations 3 | 2026-08-28 |
| `tools/probes/dome_stack_known_block_draw_probe.py` | Wiederholungsziehung in einen BEREITS BEKANNTEN Stapelteil -- gezaehlt | docs 1, evaluations 2 | 2026-09-10 |
| `tools/probes/frozen_agent_referee_probe.py` | Spielt ein gefrorenes Agenten-Artefakt VOLLSTAENDIG ueber den Referee-Pfad. | docs 1, evaluations 2 | 2026-08-28 |
| `tools/probes/frozen_worker_protocol_probe.py` | Prueft das erweiterte Worker-Protokoll gegen einen ECHTEN Worker-Prozess. | docs 1, evaluations 1 | 2026-08-28 |
| `tools/probes/human_oracle_gap_k1.py` | Auswertung PREREG_human_game_oracle_gap.md par.4/par.5: k1-relevant vs neutral. | docs 1, evaluations 1 | 2026-08-29 |
| `tools/probes/long_row_init_knob_effect.py` | PREREG_long_row_payoff.md par.3/B1, Messkette Schritt 1: | docs 2, evaluations 1 | 2026-08-25 |
| `tools/probes/ownership_column_intent.py` | Sagt der Feld-Kopf die ABSICHT vorher oder die GEOMETRIE? | docs 1, evaluations 1 | 2026-08-19 |
| `tools/probes/shaping_scale_pfad_a_e.py` | Verteilung der Pfad-A-Eingangsgroessen des Wertungs-Shapings je Runde. | docs 1, evaluations 1 | 2026-08-25 |
| `tools/r4_value_calibration.py` | Mosaic-AI -- Runde-4-Ende-Value-Kalibrierung gegen exakte Ground Truth | docs 1, evaluations 2 | 2026-08-25 |
| `tools/r4b_zone_probe.py` | tools/r4b_zone_probe.py -- Endspiel-Zonen-URSACHENANALYSE (v20-Aera-Task, | docs 2 | 2026-08-25 |
| `tools/relabel_drafts_with_net.py` | PREREG_reanalyze_label_depth.md par.A4 -- Reanalyze im engeren Sinn: die | docs 1, evaluations 1 | 2026-09-03 |
| `tools/repack_corpus.py` | Bestehende Korpus-Dateien in-place komprimieren (corpus_io-Format). | docs 1 | 2026-08-26 |
| `tools/rtv_redundancy_report.py` | Task #80: Offline-Redundanzanalyse rtv (round_transition_value) vs. | docs 2 | 2026-08-25 |
| `tools/runtime_block.py` | tools/runtime_block.py -- der `laufzeit`-Pflichtblock fuer Mess-Artefakte. | docs 1 | 2026-08-28 |
| `tools/scoring_tile_distribution.py` | Mosaic-AI -- Wertungsplatten-Randomisierungs-Audit (Wertungsplatten-Diagnose, | Kommentar 1, docs 3 | 2026-08-25 |
| `tools/selfplay_diversity_report.py` | Mosaic-AI -- Self-Play-Diversitaets-Monitoring (Task #67) | docs 2, evaluations 3 | 2026-07-23 |
| `tools/t36_curve_eval.py` | tools/t36_curve_eval.py -- Task #36: externe Brier-Auswertung aller | docs 3, evaluations 2 | 2026-08-25 |
| `tools/tiling_value_reference_main.py` | tools/tiling_value_reference_main.py -- Task #20, Hauptlauf der Referenz- | docs 2 | 2026-08-25 |
| `tools/tiling_value_reference_pilot.py` | tools/tiling_value_reference_pilot.py -- Task #20, Pilot. | Kommentar 1, docs 1 | 2026-08-25 |
| `tools/train_lambda_sweep.py` | tools/train_lambda_sweep.py -- λ-Misch-Value-Target-Sweep (soft-Z, | Kommentar 1, docs 2, evaluations 2 | 2026-08-25 |
| `tools/train_pcr_dose.py` | tools/train_pcr_dose.py -- PCR-A/B-Auswertung (Task #14), siehe | docs 2, evaluations 3 | 2026-08-25 |
| `tools/value_rank_metric.py` | tools/value_rank_metric.py -- Task #29: Value-Rangmetrik gegen das Orakel | docs 1, evaluations 1 | 2026-08-25 |

## CHRONICLE (50)

| Datei | Zweck | Genannt von | Letzter Commit |
| --- | --- | --- | --- |
| `tools/gate_hull_form_spec.sh` | Gating des Spec-Kandidaten (Huellenform 2, wahlweise plus K5) gegen die Champion-Spec, | evaluations 3 | 2026-09-07 |
| `tools/k3_arm_summary.py` | Kennzahlen eines Knopf-Arms der Kette night_k3_knobs_b06.sh fuer die Registrierung | evaluations 2 | 2026-09-06 |
| `tools/night_v28_generate.sh` | v28-ERZEUGUNG: die drei Klassen, nacheinander, Generator v27-b01. | evaluations 1 | 2026-09-10 |
| `tools/probe_g2_swarm_choice.sh` | Welche der beiden v24-b07-Schwarmhaelften traegt den G-2-Posten in v27? | evaluations 1 | 2026-09-09 |
| `tools/probes/arena_block_sd_probe.py` | Arena-Streuung fuer PREREG_geometric_envelope.md par.12b Punkt 3 (C1-Aufloesung). | evaluations 2 | 2026-09-06 |
| `tools/probes/arena_points_probe.py` | Punktbilanz je Seite aus den Partie-Logs eines Arena-Artefakts (`--log-games`), | evaluations 4 | 2026-09-05 |
| `tools/probes/blocker_split_abcd.py` | Aufspaltung des "Farbe nicht im Angebot"-Blockers (74-77%, PREREG_provokation | evaluations 1 | 2026-08-25 |
| `tools/probes/bootstrap_horizon_cost_gate.py` | PREREG_bootstrap_horizon.md Stufe 1: das KOSTEN-GATE. | evaluations 1 | 2026-08-25 |
| `tools/probes/bootstrap_horizon_paired_probe.py` | PREREG_bootstrap_horizon.md par.9: Horizont 2 gegen 3, GEPAART auf | evaluations 3 | 2026-08-25 |
| `tools/probes/bootstrap_plate_damping_probe.py` | PREREG_heuristic_v2_long_rows.md par.3b.3, Stufe 0 -- VORAB-SONDE. | evaluations 1 | 2026-08-27 |
| `tools/probes/completion_locus_row_delta.py` | PREREG_completion_bottleneck_locus.md par.5: die sekundaere Locus-Frage. | evaluations 1 | 2026-08-25 |
| `tools/probes/conjunction_base_rates.py` | Positivraten der Konjunktions-Atome je Korpus-Quelle. | evaluations 1 | 2026-08-25 |
| `tools/probes/cpu_stress.py` | (kein Kopfkommentar) | evaluations 1 | 2026-08-15 |
| `tools/probes/dome_stack_pre_post_compare.py` | PRE/POST-Vergleich der Kuppelstapel-Prereg (PREREG_dome_stack_information_sets.md par.12/par.15a). | evaluations 1 | 2026-09-10 |
| `tools/probes/effect_probe_arm.py` | Wirkungs-Probe (PREREG_ownership_corpus.md, Anti-Stillstand-Beweis fuer die | evaluations 1 | 2026-08-25 |
| `tools/probes/effect_probe_eval.py` | Auswertung der Wirkungs-Probe (Arm A/B/C/E/F) -- fuer JEDE der 30 Partien | evaluations 1 | 2026-08-15 |
| `tools/probes/emergency_cap_fire_rates.py` | PREREG_deterministic_labels.md §2 Stufe 1: Feuerraten-Messung der | evaluations 1 | 2026-08-15 |
| `tools/probes/env_ab_swap_eval.py` | Gepoolte Auswertung zweier `paired_arena_env_ab`-Laeufe mit Brett-Tausch | evaluations 2 | 2026-09-03 |
| `tools/probes/envelope_head_discrimination_probe.py` | PREREG_geometric_envelope.md Stufe 0 -- weiss der Kopf die Huelle schon? | evaluations 2 | 2026-09-03 |
| `tools/probes/generator_repro_probe.py` | Reproduziert der heutige Build den v22-Korpus-Erzeuger? (Nutzer-Auftrag 2026-08-26) | evaluations 1 | 2026-09-10 |
| `tools/probes/hull_coverage_server_logs.py` | par.3b.8 Stufe D, Ergaenzung (Nutzer-Auftrag 2026-08-29): Huellen-Deckung | evaluations 1 | 2026-08-29 |
| `tools/probes/implicit_minimax_sign_probe.py` | Vorzeichen-Sonde fuer `MOSAIC_IMPLICIT_MINIMAX_A` | evaluations 1 | 2026-08-25 |
| `tools/probes/long_row_init_arena_eval.py` | PREREG_long_row_payoff.md par.3/B1, Messkette Schritt 2: Auswertung. | evaluations 1 | 2026-09-02 |
| `tools/probes/measured_hull_probe.py` | PREREG_geometric_envelope.md par.8.15 Teil A -- gemessene Huelle. | evaluations 2 | 2026-09-06 |
| `tools/probes/net_capacity_probe.py` | Netzauslastung eines Checkpoints (Dead-Neuronen, Aktiv-Rate, effektiver Rang je ReLU-Schicht). | evaluations 1 | 2026-09-06 |
| `tools/probes/opponent_disruption_analysis.py` | PREREG_opponent_disruption.md §4 -- Auswertung der gepaarten Messung. | evaluations 2 | 2026-08-25 |
| `tools/probes/ownership_route_calibration.py` | Stufe 0 Punkte 2+3 fuer PREREG_ownership_selector.md (par.5): Kalibrierung | evaluations 2 | 2026-08-25 |
| `tools/probes/ownership_shift_magnitude.py` | Wie GROSS ist der Beitrag des Ownership-Reglers an der Wurzelentscheidung? | evaluations 2 | 2026-08-25 |
| `tools/probes/phase3_block_level_probe.py` | PREREG_r5_value_calibration.md par.12 -- Phase-3-Stufe-0 auf BLOCK-Ebene. | evaluations 1 | 2026-09-02 |
| `tools/probes/phase_sweep.py` | PREREG_heuristic_v2_long_rows.md par.13: Latin-Hypercube ueber STAERKE und | evaluations 1 | 2026-08-25 |
| `tools/probes/plate_action_signal_k1.py` | Prototyp: gibt es an der TILING-Entscheidung ein exaktes k1-Aktionssignal? | evaluations 1 | 2026-08-25 |
| `tools/probes/points_dist_bin_scale_gate.py` | Tor fuer PREREG_points_dist_bin_scale.md par.6. | evaluations 1 | 2026-08-25 |
| `tools/probes/r5_calibration_per_criterion.py` | Mosaic-AI -- Runde-5-Value-Kalibrierung, KRITERIENWEISE aufgeschluesselt | evaluations 2 | 2026-08-30 |
| `tools/probes/reachability_label_base_rate.py` | Sperre par.5 von PREREG_reachability_target.md: traegt das Vollendbarkeits-Label? | evaluations 1 | 2026-08-25 |
| `tools/probes/reachability_stage0_probe.py` | PREREG_v23_reachability_recheck.md Stufe 0 (par.2/par.4) -- Karten-Diagnose. | evaluations 2 | 2026-09-01 |
| `tools/probes/round_estimate_scale_probe.py` | Skala B_est fuer den Rundenschaetzer-Term (PREREG_round_estimate_leaf_term.md par.4). | evaluations 1 | 2026-09-05 |
| `tools/probes/row_initiation_opportunity_probe.py` | PREREG_long_row_payoff.md par.2a: Initiierung langer Reihen, auf | evaluations 1 | 2026-08-25 |
| `tools/probes/row_supply_ceiling_probe.py` | Analytische Versorgungs-Schranke je Musterreihe -- Sanity-Check. | evaluations 2 | 2026-08-25 |
| `tools/probes/saturating_score_utility_gate.py` | PREREG_saturating_score_utility.md par.3a: Tor "fast konstant" gegen | evaluations 1 | 2026-08-25 |
| `tools/probes/score_clamp_stage0_probe.py` | Stufe 0 zu evaluations/PREREG_score_clamp_incentive.md par.5 (+ par.9). | evaluations 3 | 2026-09-10 |
| `tools/probes/score_correlation_probe.py` | PREREG_score_correlation.md, komplett (par.2-par.7). | evaluations 1 | 2026-08-25 |
| `tools/probes/search_depth_column_label_probe.py` | PREREG_search_depth_column_optimum.md Stufe 4 Teil B -- ist das Verworfene | evaluations 2 | 2026-09-02 |
| `tools/probes/search_depth_rejection_probe.py` | PREREG_search_depth_column_optimum.md Stufe 4 Teil A -- Verwerfungsanteil. | evaluations 1 | 2026-09-01 |
| `tools/probes/special_tile_yield_measurement.py` | PREREG_special_tile_yield.md par.5(1) -- Neumessung auf hv2. | evaluations 1 | 2026-08-29 |
| `tools/probes/stack_draw_research_arena_eval.py` | Auswertung des Kontrollfluss-Knopfs MOSAIC_STACK_DRAW_RESEARCH. | evaluations 1 | 2026-08-30 |
| `tools/probes/tiling_hull_choice_probe.py` | Tiling-Wahlfreiheit und Huellen-Konflikt (PREREG_geometric_envelope.md par.8.10, | evaluations 2 | 2026-09-05 |
| `tools/probes/value_head_reliability_probe.py` | rho(r) des Value-Kopfs je Runde auf frozen_v3 plus Rauschboden (PREREG_geometric_envelope.md par.8.5, par.12a B1/B2, par.12b Punkte 1 und 2). | evaluations 2 | 2026-09-06 |
| `tools/replay_dome_stack_pre.sh` | Der PRE-Lauf der Referenz-Partie (PREREG_dome_stack_information_sets.md par.12): | evaluations 1 | 2026-09-09 |
| `tools/restic_legacy_inventory.sh` | Bestandsaufnahme des legacy-mirror-Stands im restic-Repo (Nutzer-Auftrag 2026-09-07: | evaluations 2 | 2026-09-07 |
| `tools/tests/test_analyze_game_log_pass.py` | Pass als eigene Log-Zeile (Nutzer 2026-09-07; PREREG_action_id_logging.md S2, Luecke 1 | evaluations 1 | 2026-09-10 |

## UNNAMED (12)

| Datei | Zweck | Genannt von | Letzter Commit |
| --- | --- | --- | --- |
| `tools/cache_watch_v25.sh` | Cache-Waechter fuer die v25-Erzeugung: baut den Block JE DATEI, waehrend das Self-Play | niemand | 2026-09-08 |
| `tools/probes/bootstrap_horizon_stage0_probe.py` | Stufe 0 (`PREREG_bootstrap_horizon.md`, Abschnitt "Stufe 0", Nutzer- | niemand | 2026-08-25 |
| `tools/probes/dagger_round2_eval.py` | PREREG_heuristic_v2_long_rows.md par.3b.11 -- Messung DAgger-Runde 2. | niemand | 2026-08-29 |
| `tools/probes/generator_drift_probe.py` | Wie gross ist die Erzeuger-Drift? (PREREG_generator_drift.md) | niemand | 2026-08-27 |
| `tools/probes/golden_diff.py` | Vergleicht zwei golden_game_loop_capture-JSON-Ausgaben (VOR/NACH) je Pfad | niemand | 2026-08-15 |
| `tools/probes/onpolicy_teacher_draft_fidelity_probe.py` | par.3b.8 (Nachtrag Draft-Check) -- On-Policy-Lehrer-Treue, LIVE-Variante. | niemand | 2026-08-29 |
| `tools/probes/ownership_corpus_coverage.py` | Deckungs-Bericht des Ownership-Korpus (PREREG_ownership_corpus.md §2): | niemand | 2026-08-28 |
| `tools/probes/ownership_tiling_consumer_eval.py` | PREREG_heuristic_v2_long_rows.md par.3b.6 -- Auswertung der | niemand | 2026-08-29 |
| `tools/probes/policy_teacher_fidelity_probe.py` | PREREG_heuristic_v2_long_rows.md par.3b.5 -- Lehrer-Treue der Policy nach SPIELTIEFE. | niemand | 2026-08-28 |
| `tools/probes/r5_four_head_comparison.py` | Vierer-Vergleich R5-Loeser-Kalibrierung (Auftrag 2026-08-23, | niemand | 2026-08-25 |
| `tools/tests/test_ladder_identity_fallback.py` | Namensaufloesung KI-Modell -> Elo-Leiter (Nutzer-Meldung 2026-09-09: das | niemand | 2026-09-09 |
| `tools/tests/test_unrated_reason.py` | Grund der Ungewertetheit im Historien-Eintrag (Nutzer-Meldung 2026-09-09: | niemand | 2026-09-09 |

