# Loeschkandidaten Ketten-Skripte, Generationswechsel v28 -> v29 (2026-09-13)

Snapshot-Beleg: a36bc301 (daily, 2026-09-13 12:03), `tools/*.sh` 60 Treffer im Snapshot,
61 im Baum -- die Differenz ist `night_v29_generate.sh`, nach dem Snapshot committet.
Stichprobe `night_v28_tail5.sh`: 1 Treffer. **Die eigentliche Sicherung ist git**: alle Dateien
sind versioniert, `git rm` laesst sie in der Historie stehen (Skill Schritt 3).

Kriterium (Skill): Lauf beendet, Ergebnis in Prereg und Chronik, an eine Generation gebunden.

## Gruppe A -- v28-Generation (Erzeugung, Kette, Arme, Tore, Promotion, Tails)

- `tools/night_v28_ablations.sh`
- `tools/night_v28_after_reanchor.sh`
- `tools/night_v28_b02.sh`
- `tools/night_v28_chain_resume.sh`
- `tools/night_v28_freeze.sh`
- `tools/night_v28_generate.sh`
- `tools/night_v28_knob_build.sh`
- `tools/night_v28_measure.sh`
- `tools/night_v28_promotion.sh`
- `tools/night_v28_resume_freeze.sh`
- `tools/night_v28_tail.sh`
- `tools/night_v28_tail2.sh`
- `tools/night_v28_tail3.sh`
- `tools/night_v28_tail4.sh`
- `tools/night_v28_tail5.sh`
- `tools/night_v28_tail6.sh`
- `tools/night_v28_tail7.sh`
- `tools/night_v28_tail8.sh`
- `tools/night_v28_tail9.sh`
- `tools/night_v28_tail10.sh`
- `tools/night_v28_third_seed.sh`
- `tools/night_v28_tor1.sh`

## Gruppe B -- Leiter-Neuverankerung Segment 2 (2026-09-12/13)

- `tools/night_ladder_gap_fill.sh`
- `tools/night_ladder_heuristic_sims600.sh`
- `tools/night_ladder_missing_edges.sh`
- `tools/night_ladder_rungs.sh`
- `tools/night_ladder_rungs2.sh`
- `tools/night_ladder_v21_edges.sh`
- `tools/night_ladder_v22_edges.sh`
- `tools/night_ladder_v22_sims25.sh`
- `tools/night_ladder_v22_sims100.sh`
- `tools/night_ladder_v28b01_edges.sh`
- `tools/night_reanchor.sh`
- `tools/night_hv3_freeze_edges.sh`

## Gruppe C -- Sims-Kurve und Leiter-Kante der Nacht auf den 2026-09-13

- `tools/night_sims_curve_v28b02.sh`
- `tools/night_v28b02s100_vs_v22s25.sh`
- `tools/run_v28b02s100_vs_v22s25.sh`

## Gruppe D -- Wheel-1-Tore (heute gelaufen)

- `tools/wheel1_gates.sh`

## Gruppe E -- Einzel-A/Bs und Instrumente vom 2026-09-12

- `tools/night_start_by_search_ab.sh`
- `tools/night_start_dome_hv2.sh`
- `tools/night_start_search_hull_off.sh`
- `tools/night_startslot_build.sh`
- `tools/night_surprise_edge.sh`
- `tools/night_tile_probe_replay.sh`
- `tools/night_envelope_bridge.sh`
- `tools/night_k3d_joker_instrument.sh`

## Gruppe F -- Reste aus v25/v26

- `tools/cache_watch_v25.sh`
- `tools/promote_v25_b01.sh`
- `tools/cache_build_socket.sh`
- `tools/probe_g2_swarm_choice.sh`
- `tools/replay_dome_stack_pre.sh`

## Gruppe G -- Lehrer-Arenen vom 2026-08-24

- `tools/run_longrow_teacher_arena.sh`
- `tools/run_lr_init_arena.sh`
- `tools/run_v2_teacher_arena.sh`

## Bleiben

- `argmax_profile.sh`, `smoke_action_temp_modes.sh` -- generische Instrumente
- `restic_env.sh`, `restic_legacy_inventory.sh` -- Sicherungswerkzeuge
- `gate_hull_form_spec.sh` -- Tor-Skript, nicht generationsgebunden
- `night_v28_chain.sh` -- **Muster fuer die noch zu schreibende v29-Kette** (Skill Schritt 7
  verweist ausdruecklich darauf); faellt, sobald die v29-Kette steht
- `night_v29_generate.sh` -- LAEUFT gerade
