# Loesch-Inventar zum Projektabschluss (Vorlage, Stand 2026-10-09)

**Dies ist eine Liste zur ENTSCHEIDUNG, keine Entscheidung.** Nichts hier ist freigegeben,
nichts wird auf Grund dieser Datei geloescht. Jede Zeile ist ein Vorschlag mit Begruendung;
geloescht wird erst nach pfadgenauer Freigabe des Nutzers am Tag der Loeschung (Abschnitt 4).

## 1. Zweck und Regeln

Mit v35 endet die Kampagne (letzte Generation, Champion nach der laufenden Promotion: `v35-b16`,
`evaluations/PREREG_v35_window.md` par.22). Ohne naechste Erzeugung folgt kein Training mehr; der
groesste Teil von `data/` und die Zwischenstaende in `models/` haben damit keinen Verbraucher mehr.

Es gelten unveraendert (Quelle `../CLAUDE.md` und `.claude/skills/mosaic-generation-turnover/SKILL.md`
Abschnitte 2 bis 5):

- **Loeschung nur auf pfadgenaue Nutzer-Freigabe.** Eine Frage ist keine Anweisung.
- **Gesicherte Dateien:** vorher daily-Snapshot, dann `restic find --snapshot <id> "<Muster>"` je
  Gruppe, Trefferzahl gegen die Dateizahl im Baum; beides ins Protokoll. Ohne diesen Beleg wird
  nichts geloescht (Praezedenz: Loeschprotokoll 2026-10-05, Snapshot `46be756f`, `evaluations/STATUS.md`).
- **Modelle:** zusaetzlich `restic snapshots --tag "run:<name>"` je Arm (train.py sichert jeden Lauf
  als Snapshot, `train.py` Z.3249-3267). Ohne Marke kein Loeschvorschlag (Skill Abschnitt 5).
- **Nicht im Backup** (`docs/backup_restore.md`, `tools/backup_excludes.txt`): alle `*.h5`,
  `engine/target`, `dist`, `build`, `__pycache__`, `logs`, `scratchpad` und die `venv/` in den
  eingefrorenen Artefakten. Fuer diese Gruppen gibt es KEINEN restic-Beleg (`restic find` liefert
  dort per Konstruktion 0 Treffer). **Sie sind nach dem Loeschen unwiederbringlich** und nur durch
  Neubau zu ersetzen; das steht bei jeder solchen Gruppe dabei.
- **Zwei-Champion-Regel** (Skill Abschnitt 5, Nutzer-Entscheid 2026-09-12): `models/frozen_champions/`
  behaelt nur den amtierenden Champion und seinen Vorgaenger.

Zaehlung: Dateizahlen und MB (10^6 Byte) am 2026-10-09 ueber Dateigroessen gezaehlt (os.walk,
keine h5-Datei geoeffnet). Wo eine Zahl nur vom Auftraggeber stammt, steht "(Zaehlung Auftraggeber)";
was gar nicht gezaehlt wurde, ist als **ungeprueft** markiert.

## 2. Was BLEIBT

| Was | Pfad | Begruendung |
| --- | --- | --- |
| Champion live | `models/alphazero_v35-b16_brierbest.{onnx,pth}`, `.onnx.ref.txt`, `models/v35-b16_brierbest.spec.json`, `models/champion.txt` | promoviertes Paket (par.22: Netz `_brierbest` plus Spec); `champion.txt` steht bis zum `set_champion` noch auf `v34-b01_brierbest` |
| Champion-Artefakt | `models/frozen_champions/v35-b16/` | amtierend; derzeit 6 Dateien, Golden Probe und venv kommen erst mit der Promotionskette |
| Vorgaenger | `models/alphazero_v34-b01_brierbest.*`, `models/v34-b01_brierbest.spec.json`, `models/frozen_champions/v34-b01/` | Vorgaenger (Zwei-Champion-Regel); Generator aller v35-Korpora (`data/manifest_v34-b01-*`, Feld `model`) |
| Elo-Anker | `models/frozen_heuristics/hv4_anchor/` | aktiver Fixpunkt Segment 2 (`ANCHOR_NAME`, `tools/elo_tracker.py`), 21 Kanten |
| Anfaenger-Stufe | `models/frozen_heuristics/hv3_generator/`, `models/hv3.spec.json`, `models/levels/beginner.spec.json` | Stufe 1 der GUI (`PREREG_difficulty_levels.md` par.4.1/4.1a: "Anfaenger = hv3 @150") |
| Test-Netz | `models/engine_test.onnx` (9,2 MB, getrackt) | von `engine/src/net.rs` und `engine/examples/` benutzt |
| R4-Substrat | `data/frozen_substrates/` (1 Datei, 3,3 MB) | eingefrorenes Substrat der R4-Diagnostik (Promotionskette Schritt 5) |
| Auswertungssaetze | `evaluations/frozen_eval_set*.pkl` (darunter frozen_v3) | Referenz IMMER (Skill Abschnitt 4); Anzeige-Kalibrierung in `server.py` |
| Mensch-Logs | `static/log/` (56 Dateien, 1,6 MB) | Referenz IMMER (Skill Abschnitt 4); Quelle der Mensch-Partien |
| Elo-Register | `evaluations/elo_history.csv`, `arena_trends.csv` | traegt die Zahlen, wenn Artefakte weg sind (Skill Abschnitt 5) |
| Preregs, STATUS, Index | `evaluations/PREREG_*.md`, `STATUS.md`, `PREREG_INDEX.md` | Ergebnisse der Kampagne |
| Mess-Artefakte | `evaluations/artifacts/` (1.658 Dateien, 2.400 MB) | Belege der Elo-Kanten und Preregs; gesichert. Groesste Klassen `paired_*` 735 MB, `gating_*` 635 MB, `ab_*` 384 MB; Ausduennen waere eigener Nutzer-Entscheid |
| Trainings-Manifeste | `models/manifest_train_*.json` (74 Dateien, 0,8 MB) | Rezept und `cache_file` je Arm; getrackt |
| Specs und Rezepte | `models/*.spec.json`, `models/*.recipe.json` | klein; jede Spec, die eine Elo-Zeile nennt, bleibt |
| Traeger-Manifeste | `data/policy_carrier_manifest_*.json` (19 Dateien, 0,7 MB) | Referenz IMMER (Skill Abschnitt 4) |
| Seed-Positionen | `data/seed_positions/` (2 Dateien, 46,0 MB) | Startstellungs-Korpus von `self_play.py`; klein, gesichert; Loeschen nur auf eigenen Wunsch |

## 3. Loeschkandidaten je Gruppe

Spalte "Sicherung": **restic** = im daily-Snapshot, Beleg per `restic find` Pflicht; **NICHT gesichert** =
unwiederbringlich, nur Neubau. Empfehlung: **L** = Loeschkandidat, **N** = Nutzer-Entscheid, **B** = eher behalten.

### 3.1 Trainingscaches in `data/` (alle `*.h5`, NICHT gesichert)

| Muster | Anzahl | MB | Rolle / Verweis | Sicherung | Empfehlung |
| --- | --- | --- | --- | --- | --- |
| `data/.filecache_*.h5` (Bloecke, alle) | 13.900 | 7.272,7 | Datei-Bloecke je Korpusdatei und Marker (rund fuenf je Datei, HERLEITUNG 13.900 / 2.700); kein Training folgt | NICHT gesichert, unwiederbringlich | **L** |
| `data/.cache_*.h5` grosse Monolithe toter Arme (14 Schluessel, s. Tabelle unten) | 14 | 8.475,6 | Fenster-Caches der Arme b01-b15, b19 | NICHT gesichert, unwiederbringlich | **L** |
| `data/.cache_58500785fe54.h5` (b16) | 1 | 791,5 | Trainings-Cache des Champions (`manifest_train_v35-b16_*.json`) | NICHT gesichert, unwiederbringlich | **L** (nur fuer ein Nachtraining von b16 noetig) |
| `data/.cache_*.h5` kleine Val-Monolithe (15 Schluessel) | 15 | 872,6 | Val-Caches (je rund 58 MB); kein Manifest nennt ihren Schluessel, Besitz klaert `tools/cache_doctor.py`; `81bef1158189` gehoert zu b01 (`STATUS.md`) | NICHT gesichert, unwiederbringlich | **L** |
| **Summe `*.h5`** | **13.930** | **17.412,4** | | | |

Neubau-Kosten, falls doch noch einmal trainiert wird: Bloecke 400 Dateien 269 s gemessen
(`PREREG_v35_window.md` par.21a), Kostenherleitung "400 x 0,79 s rund 5 min" (par.17); Merge eines
1.600-Dateien-Monolithen rund 5 min (par.20a) bzw. 359 s (par.21a). Voraussetzung ist, dass die
Korpora (3.3) noch da oder aus restic zurueckgeholt sind.

Zuordnung der grossen Monolithe (Feld `cache_file` in `models/manifest_train_v35-*.json`; der
v34-b01-Schluessel `abe92a3143a7` liegt nicht mehr im Baum):

| Schluessel | MB | Arme |
| --- | --- | --- |
| `ac852965e449` | 576,7 | b01 |
| `8e8096768cf0` | 573,6 | b02, b07, b08, b08b |
| `67fa71dc5b08` | 573,6 | b03, b14b |
| `cfb33cd893f5` | 573,3 | b04 |
| `3a2ded7d7af0` | 573,5 | b05 |
| `f769c305cdaa` | 573,4 | b06 |
| `1e0bdfe0d133` | 790,8 | b09 |
| `c577aaeafe38` | 574,3 | b10 |
| `f320ba94c902` | 576,9 | b11 |
| `a5a2868d3305` | 577,0 | b12 |
| `d8a17d0dcced` | 573,6 | b13 |
| `76554649eeb4` | 573,6 | b14a |
| `0f6bb3a71038` | 573,6 | b15 |
| `58500785fe54` | 791,5 | b16 (Champion) |
| `72ebe9e201c0` | 791,5 | b19 |

### 3.2 Smoke- und Restdateien in `data/` (gesichert)

| Muster | Anzahl | MB | Rolle / Verweis | Sicherung | Empfehlung |
| --- | --- | --- | --- | --- | --- |
| `data/probe_v35b02_smoke/`, `data/probe_v35b02_smoke_run1_0004/`, `data/probe_v35b09_smoke/` | 21 | 10,7 | Smoke-Laeufe vor den Erzeugungen b02/b09, erledigt | restic | **L** |
| `data/.heartbeat_v28-b02-policy_*.json` | 1 | 0,0 | liegengebliebener Herzschlag einer v28-Erzeugung | restic | **L** |

### 3.3 Self-Play-Korpora (alle vom Generator v34-b01, gesichert)

Sie sind das Trainingsmaterial des Champions und gesichert; ohne sie ist b16 nicht nachtrainierbar
(ausser per restic-Rueckholung). Darum **N** fuer die ganze Gruppe.

| Muster | Anzahl | MB | Rolle / Verweis | Sicherung | Empfehlung |
| --- | --- | --- | --- | --- | --- |
| `data/selfplay_v34-b01-policy-s400-vol_*.pkl` | 400 | 397,5 | im b16-Fenster (`window_v35_b09.txt`, = b16) | restic | **N** |
| `data/selfplay_v34-b01-value-deviate-s400_*.pkl` | 400 | 397,5 | im b16-Fenster | restic | **N** |
| `data/selfplay_v34-b01-value-excursion-s400_*.pkl` | 400 | 321,8 | im b16-Fenster | restic | **N** |
| `data/selfplay_v34-b01-policy-dice-v2-r1-s400_*.pkl` | 200 | 198,1 | im b16-Fenster | restic | **N** |
| `data/selfplay_v34-b01-policy-s400_*.pkl` | 100 | 99,3 | im b16-Fenster | restic | **N** |
| `data/selfplay_v34-b01-policy_*.pkl` | 100 | 99,1 | im b16-Fenster und im b01-Fenster | restic | **N** |
| Zwischensumme b16-Material | 1.600 | 1.513,3 | | | |
| `data/selfplay_v34-b01-value-deviate_*.pkl` | 400 | 373,3 | nur b01-Fenster (`window_v35.txt`, 100 Sims) | restic | **N**, eher L |
| `data/selfplay_v34-b01-value-excursion_*.pkl` | 400 | 302,9 | nur b01-Fenster | restic | **N**, eher L |
| `data/selfplay_v34-b01-policy-dice-v2-r1_*.pkl` | 200 | 187,6 | nur b01-Fenster | restic | **N**, eher L |
| `data/selfplay_v34-b01-policy-s100_*.pkl` | 100 | 93,8 | nur b01-Fenster | restic | **N**, eher L |
| Zwischensumme nur b01 | 1.100 | 957,6 | | | |
| **Summe Korpora** | **2.700** | **2.470,9** | | | |
| `data/manifest_v34-b01-*.json` | 11 | klein | Erzeugungs-Manifeste der Korpora oben | restic | mit ihren Korpora |

Musterfalle: `selfplay_v34-b01-policy*` trifft fuenf Klassen auf einmal. Im `restic find` und in
der Loeschliste darum immer den Datumsteil direkt hinter den Klassennamen setzen
(`selfplay_v34-b01-policy_2026*`, `selfplay_v34-b01-policy-s400_2026*`); dann trifft jedes Muster
genau seine Klasse.

### 3.4 Modelle in `models/` (gesichert, ausser venv)

Elo-Knoten laut `evaluations/elo_history.csv` (88 Zeilen, Spalten `player_a`/`player_b`, Stand
2026-10-09): **kein einziger v35-Arm ist Knoten**; b16 bekommt seine Kanten erst durch die laufende
Promotionskette. Knoten mit Netz im Baum: `v29-b11` (1 Kante), `v31-b01` (7), `v32-b01` (15),
`v33-b01` (7), `v34-b01` (5); dazu `Heuristik_hv2_generator` (6), `Heuristik_hv3_generator` (4),
`Heuristik_hv4_anchor` (21). Die Register-Zeilen bleiben in jedem Fall; geloescht wuerden nur Dateien.

| Muster | Anzahl | MB | Rolle / Verweis | Sicherung | Empfehlung |
| --- | --- | --- | --- | --- | --- |
| `models/alphazero_v35-b*_resume.pth` (b02-b08, b10) | 8 | 433,2 | Fortsetzungsstaende abgeschlossener Trainings | restic + `run:` | **L** |
| `models/alphazero_v35-{b01,b03,b04,b05,b06,b07,b08,b08b,b09,b11,b12,b13,b14a,b14b,b15,b19}*` ohne `_resume` | (in 168) | (in 1.155,4) | Arme ohne Kante, Ergebnis nur in der Prereg (`PREREG_v35_window.md` par.11-21, Kopf: b07 traegt nicht, b08/b08b/b11-b15/b19 ohne Hebel, die uebrigen tragen, aber unter b16) | restic + `run:` | **L** |
| `models/alphazero_v35-b10*` ohne `_resume` | (in 168) | (in 1.155,4) | staerkste Kante vor b16 (par.18b); Prereg-Kopf: "Offen: Kante b16 gegen b10" | restic + `run:` | **N** (nur falls die Kante noch gefahren werden soll) |
| `models/alphazero_v35-b02*` ohne `_resume` | (in 168) | (in 1.155,4) | Bezug der Reihe (b08b, b11-b15 gegen b02) | restic + `run:` | **N**, eher L |
| Summe v35-Arme ohne b16, ohne `_resume` | 168 | 1.155,4 | | | |
| `models/alphazero_v35-b16.{onnx,pth}`, `_best.*`, `_loss.png`, die zugehoerigen `.ref.txt` | 7 | 46,2 | Nebenstaende des Champions (Endstand, Val-Loss-Bester); promoviert ist `_brierbest` | restic + `run:` | **N** |
| `models/alphazero_v34-b01.{onnx,pth}`, `_best.*`, `_loss.png`, `.ref.txt` | 7 | 46,2 | Nebenstaende des Vorgaengers; Generator und Kanten liefen auf `_brierbest` | restic + `run:` | **N** |
| `models/alphazero_v33-b01*` | 4 | 23,1 | Elo-Knoten (7 Kanten), Generator der v34-Korpora (diese sind geloescht) | restic + `run:` | **L** (Register traegt die Zahl) |
| `models/alphazero_v32-b01*` | 6 | 23,2 | Elo-Knoten (15), Champion-2 der laufenden Kette ueber das Artefakt | restic + `run:` | **L** nach Kettenende |
| `models/alphazero_v31-b01*` | 6 | 23,2 | Elo-Knoten (7), Champion vor v32 | restic + `run:` | **L** |
| `models/alphazero_v29-b11*` | 3 | 23,1 | Elo-Knoten (1 Kante gegen v29-b09) | restic + `run:` | **L** |
| `models/frozen_champions/v32-b01/` | 891 | 62,9 | faellt nach der Promotion aus der Zwei-Champion-Regel (Nutzer-Entscheid laut par.22); Gegner von Schritt 4 der LAUFENDEN Kette | restic fuer 7 Dateien (30,2 MB); `venv/` 884 Dateien 32,7 MB NICHT gesichert (aus dem Wheel neu baubar) | **L** erst nach Kettenende und Registrierung |
| `models/frozen_heuristics/hv2_generator/` | 2.246 | 102,6 | Elo-Knoten (6 Kanten); keine Rolle mehr: als Anfaenger-Stufe gestrichen (`PREREG_difficulty_levels.md` par.4.1a, "hv2 ist keine Option mehr"), Quellzweig entfernt, also NICHT nachbaubar | restic fuer Wheel/Spec/Probe/`label_net.onnx`; `venv/` 2.240 Dateien 86,6 MB NICHT gesichert | **N** (einzige Kopie danach in restic) |

### 3.5 Ketten-Skripte in `tools/` (getrackt, Git-Historie behaelt sie)

Kriterien Skill Abschnitt 3: Lauf beendet, Ergebnis in Prereg und Chronik, an eine Generation gebunden.
Loeschen per `git rm`; die Docs, die sie nennen, im selben Zug nachziehen.

| Muster | Anzahl | MB | Rolle / Verweis | Sicherung | Empfehlung |
| --- | --- | --- | --- | --- | --- |
| `tools/night_v34_chain.sh`, `night_v34_generate.sh`, `v34_arms_ab_chain.sh`, `v34_cost_gate.sh`, `v34_e2_arm.sh`, `v34_e4_arm.sh`, `v34_promotion_chain.sh`, `v34_promotion_gate.sh` | 8 | rund 0,4 MB fuer alle 33 Skripte zusammen | v34-Zyklus, `PREREG_v34_window.md` | Git | **L** |
| `tools/night_v35_{chain,swarm,arms_chain,b02_chain,b08b_chain,b09_b10_chain,b11_b15_chain,b15_full_chain,b16_chain,b19_chain,exploiter_chain,exploiter2_chain}.sh`, `night_v35_prep_chain1..4.sh` | 16 | (s. o.) | v35-Erzeugung und Arme, `PREREG_v35_window.md` par.7-21 | Git | **L** |
| `tools/v35_b02_generate.sh`, `v35_sockel_generate.sh`, `v35_sockel_w_generate.sh` | 3 | (s. o.) | Erzeugungen v35, par.10/12 | Git | **L** |
| `tools/quicklook_b18_chain.sh`, `tree_reuse_arena_chain.sh` | 2 | (s. o.) | Tree-Reuse-Prereg par.3e | Git | **L** |
| `tools/asym_s4b_chain.sh`, `asym_s5_s4b2_chain.sh`, `asym_w_src4_chain.sh` | 3 | (s. o.) | `PREREG_asymmetric_selfplay.md` | Git | **L** |
| `tools/asym_probes.sh` | 1 | (s. o.) | wird von `tools/probes/asym_probe_report.py` als Quelle genannt | Git | **N** |
| `tools/r5_stage2_ab.sh` (weitere Kandidaten `r5_selfplay_series.sh`, `gate_hull_form_spec.sh`, `run_net_health_generations.sh`, `smoke_action_temp_modes.sh`: **ungeprueft**) | 1 | klein | an Champion v32-b01 gebunden (`PREREG_r5_net_vs_solver.md` par.5a/5b) | Git | **N** |
| `tools/v35_promotion_chain.sh` | 1 | klein | LAEUFT | Git | **B** bis zur Registrierung der Promotion |

Verweise, die beim Loeschen nachzuziehen sind (grep 2026-10-09): `docs/measured_runtimes.md`,
`docs/pitfalls.md`, `docs/working_rules.md`, `evaluations/STATUS.md`; im Code nur Kommentare und
Hilfetexte in `tools/brier_best_checkpoint.py`, `tools/checkpoint_val_eval.py` (Pruefstelle
`night_v35_chain.sh:41-54`), `tools/probes/exploiter_cycle_report.py`, `tools/recipe_config.py`.

### 3.6 Build-Ausgabe (NICHT gesichert)

| Muster | Anzahl | MB | Rolle / Verweis | Sicherung | Empfehlung |
| --- | --- | --- | --- | --- | --- |
| `engine/target/` | ungeprueft | 10.793 (Zaehlung Auftraggeber) | cargo-Ausgabe; jeder spaetere `cargo build`/`cargo test` und der pre-push-Hook bauen dann komplett neu (Dauer ungeprueft) | NICHT gesichert, nur Neubau | **L** |
| `dist/Mosaic-AI/` | 127 | 95,0 | entpacktes PyInstaller-Bundle (`tools/build_release.py`) | NICHT gesichert, nur Neubau | **L** |
| `dist/Mosaic-AI_v1.1-alpha31.zip` | 1 | 45,0 | gepacktes Release-Bundle | NICHT gesichert, unwiederbringlich als Datei | **N** (liegt es woanders, z. B. als Release?) |
| `dist/mosaic_release.spec`, `run_mosaic.py`, `README_GAME.txt` | 3 | klein | getrackte Build-Quellen (`.gitignore` Ausnahmen) | Git | **B** |
| `build/` | 16 | 25,8 | PyInstaller-Zwischenstand | NICHT gesichert, nur Neubau | **L** |

### 3.7 Kleinkram (gesichert, eher behalten)

| Muster | Anzahl | MB | Rolle / Verweis | Sicherung | Empfehlung |
| --- | --- | --- | --- | --- | --- |
| `data/window_*` (v23-v35, Listen, Splits, `.valfrac`) | 130 | 8,1 | Fensterlisten; `window_v35_b09.txt` und `window_v35_b16_{train,val}.txt` sind das b16-Fenster | restic | **B** |
| `data/manifest_*.json` ausser v34-b01 (v28-v33, `frozenv3-b01`) | 31 | rund 0,2 | Erzeugungs-Manifeste geloeschter Korpora; Herkunftsnachweis | restic | **B** |
| `data/*_swarm_pick_*`, `carriers_*`, `hv2_swarm_*`, `policy_carrier_list_v35_b02.txt` | 20 | 0,1 | Schwarm-Picks und Traegerlisten | restic | **B** |
| `data/plate_labels_v1.json` | 1 | 3,6 | Ausgabe von `tools/plate_head_labels.py` | restic | **B** |
| `logs/` | 32 | 2,8 | Konsolen-Mitschnitte | NICHT gesichert | **B** |
| `player_profiles.json.bak` | 1 | 0,03 | ungetrackte Sicherungskopie, Herkunft ungeprueft | restic | **N** |

### 3.8 Summen

| Kategorie | MB | Gesichert? |
| --- | --- | --- |
| `*.h5` gesamt (3.1) | 17.412,4 | nein |
| Korpora gesamt (3.3) | 2.470,9 | ja |
| Modelle, Empfehlung L (`_resume` 433,2; v35-Arme ohne b02/b10/b16 1.016,8; alte Knoten 92,6; Artefakt v32-b01 62,9) | 1.605,5 | ja, venv nein |
| Modelle, Empfehlung N (b02 69,3; b10 69,3; Nebenstaende b16/v34 92,4; hv2_generator 102,6) | 333,6 | ja, venv nein |
| Build-Ausgabe (3.6, ohne getrackte Quellen) | 10.958,8 (davon 10.793 Zaehlung Auftraggeber) | nein |
| Ketten-Skripte (3.5) | rund 0,4 | Git |

## 4. Handgriffe am Tag der Loeschung (Reihenfolge bindend)

**0. Voraussetzungen.** Promotionskette fertig und registriert (`champion.txt` = `v35-b16_brierbest`,
`frozen_champions/v35-b16/` vollstaendig mit Golden Probe und venv, Register-Zeilen, STATUS).
Maschine frei: keine Arena, kein Training, kein Build (Prozessliste wie Skill Abschnitt 0). Der
Backup-Lauf ist selbst I/O-Last ueber den ganzen Projektordner.

**1. Daily-Snapshot mit Beleg.**

```
powershell -NoProfile -File tools/mosaic_backup.ps1
powershell -NoProfile -File tools/verify_backup.ps1 -Source project
restic snapshots --tag daily
```

Die Snapshot-ID ins Protokoll (`archive/history.md`).

**2. restic-Beleg je gesicherter Gruppe.** Trefferzahl gegen die Dateizahl im Baum halten.
`restic find` druckt Pfade mit Vorwaertsschraegstrichen (`docs/backup_restore.md`, Fallen).

```
restic find --snapshot <id> "selfplay_v34-b01-value-deviate_2026*"
restic find --snapshot <id> "alphazero_v35-b03*"
restic find --snapshot <id> "alphazero_v35-b*_resume.pth"
restic snapshots --tag "run:v35-b03"
```

Je Gruppe aus Abschnitt 3 ein Muster; fuer `frozen_champions/v32-b01` und `hv2_generator` mit
Verzeichnismuster und dem Vermerk, dass `venv/` darin per Konstruktion fehlt. Fuer `*.h5`,
`engine/target`, `dist`, `build` KEIN restic-Beleg, stattdessen der Vermerk "unwiederbringlich,
Neubau" im Protokoll.

**3. Listen fuer Bloecke und Monolithe.**

```
python -X utf8 -u tools/cache_doctor.py --json evaluations/artifacts/cache_doctor_closeout.json
python -X utf8 tools/cache_inventory.py --orphans --print-delete-list
```

`cache_doctor.py` ordnet jeden Monolithen (auch die Val-Monolithen) einem Arm zu;
`cache_inventory.py` zeigt nur VERWAISTE Bloecke (Quelldatei weg). Sollen ALLE Bloecke weg
(Empfehlung 3.1), ist die Liste schlicht `data/.filecache_*.h5`; werden Korpora geloescht, laeuft
`--orphans` danach noch einmal. Beide Werkzeuge loeschen nichts.

**4. Pfadgenaue Freigabe.** Dem Nutzer je Gruppe Muster, Anzahl, MB, Trefferzahl im Snapshot
vorlegen; geloescht wird nur, was er ausdruecklich nennt.

**5. Loeschen.** Ketten-Skripte per `git rm` (Docs im selben Commit nachziehen), alles andere per
Dateiliste. Kein Commit und kein Loeschen waehrend eines Messlaufs.

**6. Nachkontrolle.**

```
python -X utf8 tools/cache_inventory.py --orphans
python -X utf8 -u tools/cache_doctor.py
python tools/check_conventions.py
```

Waisenliste muss leer sein; Dateizahlen je Gruppe erneut zaehlen; Loeschprotokoll mit
Snapshot-ID, Gruppen, Treffer- und Dateizahlen nach `archive/history.md`, Kurzvermerk in STATUS.
