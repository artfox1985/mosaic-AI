# Loeschvorschlag zum Generationswechsel v24 -> v25 (2026-09-07)

Schritt 3 und 5 des Ablaufs `/mosaic-generation-turnover`. **Nichts wird ohne pfadgenaue
Freigabe geloescht.** Schritt 4 (Korpora, Bloecke, Monolithe) folgt getrennt, weil er den
restic-Beleg je Gruppe braucht.

## A) Einmal-Skripte von heute, Laeufe beendet und registriert (4)

| Datei | Lauf | Ergebnis registriert in |
| --- | --- | --- |
| `tools/promote_v24_b07.sh` | Promotion, 17:33-18:42 | drei Elo-Kanten, `geometric_envelope` par.8.15f |
| `tools/night_k5_row6_special.sh` | K5-Arm, 09:50-11:21 | `special_tile_yield` par.9c |
| `tools/wegb_temp2_build_window.sh` | Build Weg B und Temperatur, 11:24-11:30 | Chronik |
| `tools/wegbc_build_window.sh` | Build Umbau, 19:26-19:32 | Chronik |

## B) Einmal-Skripte des Archiv-Aufraeumens (2)

| Datei | Lauf | Ergebnis |
| --- | --- | --- |
| `tools/restic_legacy_dryrun.sh` | Trockenlauf, 16:37 | `cleanup_proposal_restic_legacy.md` |
| `tools/restic_legacy_cleanup.sh` | scharf, 17:07 | 14,473 -> 8,968 GiB, check ohne Fehler |

## Was BLEIBT und warum

| Datei | Warum |
| --- | --- |
| `tools/argmax_profile.sh` | Tor-2a-Instrument, generisch |
| `tools/gate_hull_form_spec.sh` | seit heute generisch: nimmt Arm- UND Kontroll-Spec, belegt die Einfaktorialitaet selbst |
| `tools/smoke_action_temp_modes.sh` + `smoke_action_temp_compare.py` | wiederverwendbare Rauchprobe, belegt WIRKUNG statt Statuszeile |
| `tools/restic_legacy_inventory.sh` + `restic_snapshot_inventory.py` + `restic_env.sh` | Inventur ist wiederverwendbar, `restic_env.sh` ist die Sammelstelle |
| `tools/probes/action_count_profile_probe.py` | neue Sonde, generisch |
| `tools/run_longrow_teacher_arena.sh`, `run_lr_init_arena.sh`, `run_v2_teacher_arena.sh` | benannte Arena-Rezepte |
| `tools/night_v24_chain.sh` | **Muster fuer die v25-Kette** (`mosaic-generation-turnover` SKILL.md:143). Faellt, sobald die v25-Kette steht -- dann zeigt der Skill auf diese |

## C) Modelle -- Vorlage, kein Vorschlag (Schritt 5)

Der Ablauf verlangt: nie selbst entscheiden, und ohne `restic snapshots --tag run:<name>`
kein Loeschvorschlag. Beides steht aus. **Ich lege hier bewusst KEINE Modell-Liste vor**,
bis der Tagesschnappschuss steht und die Marken geprueft sind -- eine Liste ohne Beleg
waere genau der Fehler, gegen den Schritt 5 geschrieben ist.

Fest steht nur, was NICHT loeschbar ist: `v24-b07` (Champion), `v24-b06` (Elo-Knoten mit
vier Kanten), `v23-b01_k3p10` (Champion-2-Knoten), die eingefrorenen Artefakte unter
`models/frozen_champions/` und `models/frozen_heuristics/`, und `models/engine_test.onnx`
(Test-Fixture).

**Offen aus einer frueheren Sitzung:** `models/attic_20260906_k3p10_copies/` und
`venv_measure_hullform/` liegen weiter und warten seit gestern auf pfadgenaue Freigabe.
