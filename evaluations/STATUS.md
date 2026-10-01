# Mosaic-AI – Status & Fahrplan

**Dieses Dokument traegt NUR Aktuelles und Offenes.** Neufassung vom 2026-10-01 (Generationswechsel
v33 -> v34, `/mosaic-generation-turnover` Schritt 6); der vollstaendige Stand davor liegt in
`../archive/history.md`, Kapitel **"Vollstaendiger STATUS-Stand vom 2026-10-01 (vor der Neufassung
zum Generationswechsel v33 -> v34)"**, danach der **"Generation v33"**-Bericht.

**Pflegeregel:** wer einen Befund erzeugt, traegt ihn im selben Zug hier nach und prueft, ob ein
anderer Abschnitt dadurch falsch wird. Wer einen Strang abschliesst, schiebt die Herleitung ins
Archiv und laesst hier eine Zeile mit Verweis stehen. Wer ein Ergebnis registriert, greppt nach
seinen KONSUMENTEN (CLAUDE.md, Rueckwaerts-Pruefung).

**Dauerhaftes Prozesswissen steht NICHT hier**, sondern in `../docs/`: `generation_loop.md`,
`promotion_checklist.md`, `generation_naming.md`, `working_rules.md`, `pitfalls.md`,
`measured_runtimes.md`, `architecture_reference.md`, `engine_manual.md`.

---

## 1. WAS GERADE LAEUFT

**FERTIG: die v34-Erzeugung** (Nutzer-Freigabe 2026-10-01), `bash tools/night_v34_generate.sh` 10:06:42-17:25:01, Exit 0: je Klasse 400 Dateien / 4.000 Partien, Waechter je Klasse gruen, 0 `[Watchdog]`-Zeilen; Wanduhr 9.472,7 / 9.474,3 / 7.335,7 s (policy / value-wegc / value-excursion), zusammen 7,30 h gegen 8,8 h hergeleitet. Nebenlast waehrend policy: drei Datei-Edits per kurzem `python` (je rund 1 s), gemeldet. Naechster Schritt: Abnahmen par.4.

**Start der Erzeugung (NUR auf ausdrueckliche Nutzer-Freigabe):**

```
bash tools/night_v34_generate.sh
```

als Datei, `run_in_background`, ohne Pipe. Drei Klassen nacheinander aus `models/v34.recipe.json`
(policy, value-wegc, value-excursion, je 4.000 Partien), Waechter je Klasse. Planungszahl rund
8,8 h (HERLEITUNG, `PREREG_v34_window.md` par.8a). Waehrend des Laufs: nichts anderes, kein Build,
kein Commit.

**Erledigt im Wechsel am 2026-10-01** (alles exklusiv, alles committet):
* Anker-Invarianz gegen `hv4_anchor` auf Wheel 1.1.0 (`1a9e4bac...`): Drift und Konservierung gruen.
* R5-Kalibriersonde (`PREREG_r5_net_vs_solver.md` par.6b): beim heutigen Loeser frisst das erste
  Kind das Budget in 86 von 117 Entscheidungen; iterativ @2000 129 ms Median je Entscheidung.
* Smoke des v34-Rezepts (`PREREG_v34_window.md` par.7a): erst ROT (Waechter-Erwartung rezeptweit),
  dann Erwartung je Klasse gebaut, gruen in allen drei Klassen.
* Kostentor der Erzeugung (par.8a): Runde 5 per Netz +11,5 % je Partie (2,727 gegen 2,446 s).
* v33-Kontrolle der Offline-Pruefung (`PREREG_targeted_branching.md` par.7b): DiD(v33) -0,00071
  [-0,00160; +0,00020].
* Generator `v33-b01` eingefroren (`models/frozen_champions/v33-b01`, Rolle generator, Golden Probe,
  Referee-Selbsttest gruen); restic daily `a3755374` mit Pruefung; Aufraeumen A-H mit Freigabe
  (`data/` 9,5 -> 2,0 GB, Liste im Generationsbericht v33).

**Nach der Erzeugung, in dieser Reihenfolge:**
1. **Abnahmen der Erzeugung** (`PREREG_v34_window.md` par.4): Manifest-Diff je Klasse gegen v33,
   Waechter-Protokoll, Tor 0 je Klasse, Tor 2a am Sockel, `tie_mirrored`-Anteil, KL-Abnahme am
   Ausflug (par.7 von `PREREG_targeted_branching.md`), `[Watchdog]`-Zeilen je Klasse aus der
   Aufgabenausgabe zaehlen (obere Schranke fuer verworfene Panics, Review #23).
2. **Bauten fuer die Trainings-Arme:** E2 (Python, rund ein halber Tag) und E4 (Encoder, Kompilieren
   erst nach der Erzeugung) (`PREREG_evaluator_pretests.md`, `PREREG_v34_window.md` par.3).
   **In derselben Wheel-Runde** der Engine-Teil des Review-Rests (unten), dann EINE Anker-Invarianz.
3. **Python-Teil des Review-Rests VOR dem v34-Training** (unten).
4. **Kette fuer Fenster und Training schreiben** (Traeger-Manifest v34 per
   `tools/generate_carrier_manifest.py`, Fenster b04-Form, Monolith, Grundarm `v34-b01` plus E2/E4,
   Tor 1 gegen `v33-b01`); Muster in der Git-Historie (`tools/night_v33_chain.sh`).
5. **Offline-Pruefung par.7a** nach dem Training (E = DiD(v34) - DiD(v33)).

**Review-Rest EINGETAKTET** (Nutzer 2026-10-01: *"takte #11, #12, #15 und den Rest von #23 aus dem
code review ein"*; Befunde `review/code_review_2026-09-26_verification.md`). Am Code geprueft
2026-10-01: `corpus_io.dump_records` ist schon atomar (`corpus_io.py:87-112`); offen sind
(a) `train.py` Endstaende nicht atomar und ohne Ueberschreib-Waechter (`train.py:2655`, `:2710`,
`:2734`), (b) Cache-Schluessel ohne Inhaltsmerkmal (`engine/py/file_cache_key.py:84-222`),
(c) Panic im Netz-Self-Play als "[Watchdog] ... Deadline" gemeldet (`self_play.rs:7099-7103`, `:7217`).
* **Python, vor dem v34-TRAINING:** (a) atomar (tmp plus `os.replace`, Muster `train.py:1066-1074`)
  plus Waechter gegen Ueberschreiben. (b) **Bauentscheid offen:** jedes Inhaltsmerkmal aendert alle
  Schluessel einmal (Bloecke neu bauen); Vorlage an den Nutzer mit Kostenzahl.
* **Engine, in der Wheel-Runde nach der Erzeugung mit E4:** #11 `opp_points` in
  `try_batched_pair_ex` (`net_mcts.rs:3357-3359`), #12 ORT-Registry-Schluessel (`net_ort.rs:201`,
  nur Feature `ort_cuda_probe`), #15 Batcher-Registry (`net_batcher.rs:272-301`), (c) Panic ehrlich
  melden. #11/#12/#15 latent (Knoepfe/Feature aus), keine Wirkung auf die v34-Erzeugung.

**R5 Stufe 2a A/B** (`PREREG_r5_net_vs_solver.md` par.5a Punkt 2): iterativer Loeser @2000 gegen
das Netz in Runde 5, Seeds 20261672/73 a 200 Paare. Geplant parallel zum v34-Training (GPU plus
EIN CPU-Auftrag), rund 2 x 1,8 h (HERLEITUNG). Fehlt noch: Spec fuer Seite A
(`r5_solver_iterative: 1`, `r5_solver_node_budget: 2000`, sonst `models/v33_gating.spec.json`).
Haengt NICHT an der Erzeugung; frueher moeglich, dann blockiert sie die Maschine (Nutzer-Frage
2026-10-01 beantwortet, Entscheid offen, Abschnitt 6).

**NACH dem v34-Training: asymmetrisches Self-Play** (Nutzer 2026-10-01: *"prinzipiell wuensch ich
mir mehr asymetrisches self play um bewusst stellungen zu provozieren die nicht entstehen wenn du
gegen dich selber spielst"*). Entwurf `PREREG_asymmetric_selfplay.md`: Wuerfel-Klasse W festgelegt
(ALLE Platten der Wuerfel-Seite gewuerfelt, Quelle/ID bzw. Stapeltiefe d in 1..max mit Obergrenze 7 in Runde 2 und 3 in Runde 3/Rotation, Platz
per Suche @600, erzwungene Zuege ohne Record, alle Wertziele bleiben, Start normal); Stoerer-Klasse
S skizziert (lambda_aggr je Seite, Records beider Seiten, Stoerer-Policy nur bei fast gleichwertigem
eigenem Wert). Ziel-Zusammensetzung (Nutzer 2026-10-01): Sockel 4 x 2.000 (G-G, G-W, W-S, G-S),
Schwarm 4.000 Weg C plus 4.000 Ausflug, G-1/G-2 fallen weg; grob 12 h (HERLEITUNG); endgueltig nach
den Sonden S1-S4 (par.4). Bau in der Wheel-Runde nach der v34-Erzeugung.

### RICHTUNG (Nutzer-Entscheid 2026-09-27)

*"Mir scheint wir kommen mit unserer aktuellen Suche und Netz Architektur an die Decke. Somit werden
wir v34 noch fahren und uns dann ueberlegen welche alternativen Ansaetze es gibt."* v34 ist die
letzte Generation dieser Architektur und nimmt das Paket mit (`PREREG_v34_window.md` par.3); danach
alternative Ansaetze statt einer v35 im selben Rahmen (der erste: asymmetrisches Self-Play, oben).

### FREIGABEN UND VERBOTE (woertlich)

* Nutzer 2026-10-01: *"committe sobald es moeglich ist"* (committen ja, pushen nein).
* Loeschfreigabe A-H vom 2026-10-01 ist ausgefuehrt und verbraucht. Jede weitere Loeschung braucht
  restic-Beleg UND neue pfadgenaue Freigabe.
* **Kein Push ohne Anweisung.** Nie committen: `player_profiles.json`, `player_profiles.json.bak`.
* **Kein Commit waehrend eines Wanduhr-Laufs.** Messungen exklusiv; ein Build zaehlt als Last.
* *"Mehrkosten sind kritisch abzuwaegen."* *"Stelle sicher dass du nichts faehrst was nicht schon
  bereits getestet wurde."*

## 2. CHAMPION UND LEITER

**Champion laut `models/champion.txt`: `v32-b01_brierbest`** (Promotion 2026-09-25), nach aussen
**Tessa** (der Anzeigename steht fest in `static/js/app.js`). **Elo 1480 [1431; 1529]** aus 1.000
Partien im Leitersegment 2, Anker `hv4_anchor` fix 1000. Herleitung: `PREREG_v32_window.md` par.11.

| Modell | Elo | KI95 | Partien |
| --- | --- | --- | --- |
| **v32-b01@400 (Champion, Tessa)** | **1480** | **[1431; 1529]** | **1.000** |
| v31-b01@400 | 1450 | [1406; 1496] | 1.800 |
| v30-b02@400 | 1411 | [1371; 1453] | 1.890 |
| Heuristik_hv4_anchor@150 (Anker) | 1000 | fix | 1.700 |

Stand 2026-09-25; seither im Register (`evaluations/elo_history.csv`) nur A/B- und Tor-Zeilen vom
2026-09-27 (`v33-b02`, `v32-b01-e1`, `v32-b01-r5net`), keine Promotion. Die Tabelle ist darum nicht
neu gerechnet; aktueller Bericht: `python tools/elo_tracker.py report`.

**Engine-Stand:** Paketversion **1.1.0**, Vertragshash `6ef829e564c58bd5`, 888/414. Live ist seit
2026-10-01 das Wheel `1a9e4bac...` (Wheel-Runde `8005dc51`: KL-Abzweig-Knopf, iterativer R5-Loeser);
Anker-Drift und -Konservierung darauf gruen. Der Champion `v32-b01` ist auf `e11ea6d5...`
eingefroren, der Generator `v33-b01` auf `1a9e4bac...` -- gleiche Versionsnummer, verschiedene
Builds; das Artefakt identifiziert sein Wheel ueber den sha256.

**Eingefrorene Artefakte:** `models/frozen_champions/` traegt `v31-b01`, `v32-b01` (Zwei-Champion-
Regel) und `v33-b01` (Rolle generator, zaehlt nicht als Champion). Dazu `models/frozen_heuristics/`
(`hv4_anchor`, `hv2_generator`, `hv3_generator`). `.onnx`, `.pth` und Wheels der Artefakte sind
NICHT im Repo; getrackt werden Spec, Manifest, Golden Probe und `wheel.sha256`.

## 3. LAUFZEITEN (gemessen, Planungsgroessen; Details in `../docs/measured_runtimes.md`)

| Aufbau | Dauer | Anmerkung |
| --- | --- | --- |
| Erzeugung 3 x 4.000 Partien @100, threads 11 | **12,99 h** (v33) | v30 13,86 h; v34 mit E1 und R5-Netz rund 8,8 h (HERLEITUNG) |
| Sockel je Partie @100, E1 an, R5 per Netz | **2,727 s** (Kostentor v34, n = 100) | Loeser in R5: 2,446 s; v33-Sockel ohne E1: 4,14 s |
| Training Warmstart 12 Epochen | **61 min** (v33-b01) / 63 min (v32-b01) | exklusiv |
| Tor 1 je Seed, 200 Paare @400, 10 Threads, mit Logs | **5.719 s** exklusiv | R5-A/B Stufe 1: 6.504,5 s je Seed |
| Anker-Kante n = 50 / Champion-2-Kante n = 150 | 418,6 s / 2.377,5 s (v32) | |
| Promotion nach Checkliste MIT R4/R4b/R5 (ohne Tor 1) | rund 2,3 h (v32) | |
| Voller Build: Lib-Tests, `--no-run`, Fixtures, Wheel | rund 5 min | |
| Anker-Drift / Anker-Konservierung | 23,0 s / unter 30 s | je 1.763 Schritte |
| Golden Probe eines Netz-Artefakts @400 | 1.311 s (v33-b01) / 1.109 s (v32-b01) | einkernig |
| Offline-Pruefung, zwei Koepfe, 60 Dateien | 164,1 s | |
| restic daily plus check / `verify_backup.ps1` | 9 s / 27 s | |

## 4. SPEC UND REZEPT

**Champion-Spec** `models/frozen_champions/v32-b01/spec.json` (traegt weder `start_by_search` noch
`return_order_mode`). Tor 1 und die A/B der v33-Generation liefen auf `models/v33_gating.spec.json`
(mit `start_by_search: 1`); das ist auch die Spec des Generator-Artefakts `v33-b01`.

**Erzeugung v34:** Rezept `models/v34.recipe.json` (Generator `v33-b01_brierbest.onnx`, Spec
`models/v33_generation.spec.json`, byte-gleich mit `v32_generation.spec.json`, sha256 `4a3f9db3...`;
Seeds 20260946/47/48; env `MOSAIC_STACK_DRAW_RESEARCH=1`, `MOSAIC_SINGLE_PASS_OTHER_VAL=1`,
`MOSAIC_R5_NET_SOLVER=0`; Waechter `expect_engine_config` rezeptweit plus je Klasse,
`excursion_kl_weight` 1 nur im Ausflug). Rezept-sha256 seit dem Waechter-Fix `5ca42e9b1592...`.

**v34-Fenster** (`PREREG_v34_window.md` par.1): b04-Form, also die ganze v34-Erzeugung plus aus G-1
(`v32-b01-*`) und G-2 (`v31-b01-*`) NUR die Policy-Traeger (Traeger-Manifest v34 nach der
Erzeugung). Trainings-Seed 20260961, Val-Pool `^selfplay_v33-b01-`. Training wie v33 (warm vom
Generator, 12 Epochen, lr 5e-5 cosine mit `--lr-t-max 12`, WDL, nortv, lambda 0,7,
`--select-by-brier`).

**Im Korpus liegen noch** (Stand 2026-10-01, 1.392 Dateien, 2,0 GB): Sockel `v30-b02-policy`
(R4/R4b-Substrat), `v31-b01-policy`, `v32-b01-policy` (Traeger-Kandidaten G-2/G-1) und die 192
Val-Dateien der Wert-Klassen aus `window_v32_val.txt` / `window_v33_val.txt` (registrierte
Offline-Messungen laufen darauf).

## 5. PREREG-BESTAND (8 OFFEN laut Index 2026-10-01; Ziel rund 7)

| Prereg | Was noch aussteht |
| --- | --- |
| `v34_window` | Erzeugung (wartet auf Freigabe), Abnahmen par.4, Fenster, Arme, Tore |
| `v33_window` | Kopf auf ENTSCHIEDEN ziehen, sobald nichts mehr nachgetragen wird (keine Promotion, Generator v33-b01) |
| `evaluator_pretests` | E2- und E4-Arm in v34 (Bau offen) |
| `r5_net_vs_solver` | Stufe 2a A/B (par.5a Punkt 2), danach ggf. Stufe 3 |
| `targeted_branching` | KL-Abnahme in der v34-Erzeugung, Offline-Pruefung par.7a nach dem Training |
| `tie_mirror` | Abnahme in der v34-Erzeugung (Anteil `tie_mirrored` je Klasse) |
| `asymmetric_selfplay` | ENTWURF 2026-10-01: Bau, Sonden S1-S4, Zusammensetzung |
| `difficulty_levels` | ganze Leiter auf den letzten Champion vertagt |

## 6. OFFENE NUTZER-ENTSCHEIDE

1. **Start der v34-Erzeugung** (`bash tools/night_v34_generate.sh`).
2. **Zeitpunkt der R5-Stufe-2a-A/B:** jetzt vor der Erzeugung (blockiert die Maschine rund 3,5-4 h,
   HERLEITUNG) oder wie geplant parallel zum bzw. nach dem v34-Training (Vorschlag: nach der
   Erzeugung; die Erzeugung haengt nicht daran).
3. **Champion-Spec mit Netz in Runde 5** jetzt oder erst nach Stufe 2a (Vorschlag: nach Stufe 2a,
   eine Promotion statt zwei; dann ist die R5-Kalibrierung wieder Pflicht).
4. **Cache-Schluessel mit Inhaltsmerkmal** (Review #23b): Vorlage mit Kostenzahl folgt.
5. **Asymmetrisches Self-Play, offene Punkte im Entwurf** (`PREREG_asymmetric_selfplay.md`):
   Muenze Auslage/Stapel 50:50, Wuerfel-Seite je Partie 50:50, Weg-C-Abweichung in W (Vorschlaege);
   lambda und eps des Stoerers nach Pilot S4; Zusammensetzung nach den Sonden.
6. **v33-Prereg-Kopf** auf ENTSCHIEDEN ziehen (keine Promotion; Verdikt-Absatz steht in par.6e/par.10).
7. **Aeltere, weiterhin offene Punkte** (Wortlaut im Archivkapitel vom 2026-10-01, Abschnitt 6):
   Budget-Knopf fuer die Hilfsknoten (Wirkung ungemessen); Gruppe B des Aufraeumens (Wrapper
   `resolve_and_apply_stack_draw`, drei Spec-Felder in `KNOWN_FIELDS`); R5/R4b-Sonden der
   Promotionsliste Pflicht oder je Promotion; Brier-Regel gegen `frozen_eval_set` aus aelterer
   Verteilung; Sichtluecke bei gezogenen Stapelplatten (`stack_top_feature` par.16/16a);
   Paritaets-Tor und Alt-Records (`rust_data_layer` par.9/9a); drei Sonden zeigen auf das
   geloeschte `hv1_anchor`; `-Deep`-Lauf der Backup-Verifikation (zuletzt 2026-10-01 wieder nicht
   gefahren); Dry-Artefakte `evaluations/artifacts/_dry_*.json`; R4/R4b-Substrat
   `selfplay_v30-b02-policy_*` (die 72 Zustaende einfrieren, dann darf die Klasse rotieren).

## 7. VERBOTE UND STEHENDE REGELN

- **Kein Push ohne Anweisung.** Ahead-Stand im Chat melden.
- **Loeschung nur auf pfadgenaue Freigabe**, mit restic-Beleg je Gruppe. Frage ist keine
  Anweisung. `.h5`-Dateien sind per `tools/backup_excludes.txt` nicht im Backup, weil
  regenerierbar -- fuer sie gibt es keinen Snapshot-Beleg.
- **Messungen laufen exklusiv.** GPU und CPU duerfen parallel, zwei CPU-Messungen nie; ein Build
  zaehlt als Last. **Kein Commit waehrend eines Wanduhr-Laufs.**
- **Nie committen:** `player_profiles.json`, `player_profiles.json.bak`,
  `models/manifest_train_v28-b0*.json`, `evaluations/game_analysis/*`.
- **Dateien laufender Laeufe nicht anfassen** -- auch nicht `self_play.py`, `selfplay_manifest.py`,
  `config.py`, `engine/py/neural_net.py`, `corpus_dataset.py`, `tools/recipe_config.py`,
  `models/v34.recipe.json`: die Chunk-Prozesse importieren bzw. lesen frisch. Auch eine reine
  Kommentaraenderung zaehlt.
- **Rezept-Laeufe:** Flags und Env aus der Rezeptdatei; ein Knopf, den nur eine Klasse setzt,
  gehoert in deren `expect_engine_config` (`docs/working_rules.md`).
- **Kettenskripte als DATEI starten** (`bash tools/x.sh`), nie Heredoc-schreiben-und-starten.
- **Lange Laeufe nie in eine Pipe und ohne eigene Umleitung**, mit Fortschritt.
- **Vor dem Self-Play der naechsten Generation: `/mosaic-generation-turnover`.**
- **Regel 0**, Prereg-Kopf im selben Zug wie das Ergebnis, Laufzeiten ins Artefakt, sechs
  Standard-Kennzahlen in jedem Messbericht, kein Geviertstrich in Dateien, Bezeichner englisch,
  Inhalte deutsch.
- **Eingefrorene Netze sind NICHT im Repo** (Nutzer-Entscheid 2026-09-23); kein `git add -f`.
- Keine neuen Netzkoepfe; nicht jeden Arm in die Elo-Leiter.

## 8. BEFUNDE, die eine Nachschau brauchen

- **Arena-Logs tragen keine `#a`-Zeilen** (PyGame-Pfad, `py.rs:781`); repariert ueber den
  Endzustand im Artefakt, Tor 2b verwendbar.
- **Nicht-Transitivitaet am Leiterboden:** v22@25 gegen hv4@150 76 %, gegen hv4@600 50 %,
  hv4@600 gegen hv4@150 55 %. Bradley-Terry mittelt das.
- **SPRT stoppt zwischen Nachbar-Generationen nicht**; bei groesserem Abstand sehr wohl.
- **GUI und Arena: dasselbe Spiel, dieselbe Tiefe** (`select_final_root_child`). Latente
  Sollbruchstelle: die Arena zieht `builder_drafting_preference` der Suche vor, der Serverpfad
  kennt den Vorzug nicht.
- **Gating-Artefakte tragen keine Engine-Konfiguration** (`paired_gating.py` ohne Rezept): ein
  Env-Knopf ist dort nachtraeglich nicht belegbar. Mit `--recipe` traegt das Artefakt Rezept und
  `mosaic_env`.
- **`MOSAIC_ENVELOPE_REACH_W` und `_SLOT_W`** haben keine Spec-Entsprechung (heute inert).
- **Sims und Spaltenbau:** die Kurve am Champion faellt ueber 100-600 Sims monoton, allein ueber
  die VOLLENDUNG.
- **Kein zurueckgehaltener Satz der laufenden Aera** (jede Datei liegt in mindestens einem Fenster).
- **Pfadform der Dateiliste im Cache-Schluessel:** Normalisierung auf Basenames entwertet jeden
  Monolithen; Nutzer-Entscheid an einem Generationswechsel (passt zu Review #23b).
- **Python-Werkzeuge nach einem Kontraktwechsel:** `tools/offline_diagnosis.py`,
  `tools/oracle_metrics.py` und `tools/probes/*_gate.py` uebergeben `num_actions` explizit.
- **Der heutige R5-Loeser entscheidet meist per Vorsortierung** (86 von 117, par.6b); das Label am
  Uebergang Runde 4 -> 5 (`exact_round5_outcome`) laeuft weiter ueber ihn, auch in der v34-Erzeugung.
- `player_profiles.json` im Arbeitsbaum veraendert (Server-Seite), nicht committet.
