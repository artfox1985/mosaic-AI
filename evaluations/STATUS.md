# Mosaic-AI – Status & Fahrplan

**Dieses Dokument traegt NUR Aktuelles und Offenes.** Neufassung vom 2026-09-19
(Generationswechsel v30 -> v31, Skill Schritt 6); der vollstaendige Stand davor liegt in
`../archive/history.md`, Kapitel **"Vollstaendiger STATUS-Stand vom 2026-09-19 (vor der
Neufassung zum Generationswechsel v30 -> v31)"**, der **"Generationsbericht v30 (2026-09-18
bis 2026-09-19)"** als Kapitel davor, die Generationsberichte v24 bis v29 weiter oben.

**Pflegeregel:** wer einen Befund erzeugt, traegt ihn im selben Zug hier nach und prueft, ob
ein anderer Abschnitt dadurch falsch wird. Wer einen Strang abschliesst, schiebt die
Herleitung ins Archiv und laesst hier eine Zeile mit Verweis stehen. Wer ein Ergebnis
registriert, greppt nach seinen KONSUMENTEN (CLAUDE.md, Rueckwaerts-Pruefung).

**Dauerhaftes Prozesswissen steht NICHT hier**, sondern in `../docs/`: `generation_loop.md`,
`promotion_checklist.md`, `generation_naming.md`, `working_rules.md`, `pitfalls.md`,
`measured_runtimes.md`, `architecture_reference.md`, `engine_manual.md`.

---

## 1. WAS GERADE LAEUFT

**Die v31-Erzeugung**, gestartet 2026-09-19 um 21:55 als `bash tools/night_v31_generate.sh`,
drei Klassen nacheinander, Generator `v30-b02`, Seeds 20260934/35/36, `--return-order-random-p
0.81` als CLI-Flag. Stand 22:10 gezaehlt: **168 von 1.201 Dateien**, Klasse 1 (Sockel).
Erwartete Dauer rund 14 h nach der v30-Messung.

**Wichtig zum Knopf:** die Dosis geht als CLI-Flag hinein, NICHT als Umgebungsvariable.
`self_play.py` Z.236-240 setzt `MOSAIC_RETURN_ORDER_RANDOM_P` aus seinem eigenen CLI-Default
(0.0) neu und ueberschreibt einen exportierten Wert stillschweigend; der erste v31-Anlauf ist
daran 45 Dateien weit ohne eine einzige Streuung gelaufen und wurde verworfen. Gegenprobe am
neuen Korpus: **15,0 Prozent der Partien mit gestreuter Rueckgabe** (Ziel 15, Obergrenze 17,75).

### NACH DEM ENDE DER ERZEUGUNG, in dieser Reihenfolge

1. Wiedervorlage am ersten Record (traegt er `return_order_randomized`?), Manifest-Diff gegen
   die Referenz, Stack-Draw-Kontrolle.
2. **Tor 0** je Klasse (sechs Standard-Kennzahlen) und **Tor 2a**: `sp_voll` der neuen
   Policy-Klasse gegen **0,90087** von `v29-b11` (`PREREG_v31_window.md` par.2).
3. Fensterliste v31 bauen (par.1: 2.947 Dateien, Seed 20260949, Val-Pool `^selfplay_v30-`),
   Traeger-Manifest 580, **`MOSAIC_DATA_EXCLUDE` beim Cache-Bau setzen**.
4. Kette fuer v31 als Datei schreiben und vorlegen; der Start braucht eine Anweisung.

### FREIGABEN UND VERBOTE (woertlich, unveraendert gueltig)

* Nutzer 2026-09-19: *"Dann mach das und fahr die self plays fuer v31"* -- die Erzeugung laeuft;
  der Start der Trainingskette ist NICHT freigegeben (vorlegen).
* Nutzer 2026-09-19: Loeschfreigabe fuer den v27-b01-Korpus, die zwoelf Ketten-Skripte und beide
  Monolithen -- ausgefuehrt und verbraucht. Jede weitere Loeschung braucht restic-Beleg UND neue
  pfadgenaue Freigabe.
* Kein Push ohne Anweisung. Kein Commit waehrend eines Wanduhr-Messlaufs; neben Self-Play und
  Training ist der Sekunden-Hook hingenommen.
* Messungen exklusiv; GPU-Training plus EIN CPU-Auftrag erlaubt; Builds zaehlen als Last. Ketten
  als DATEI starten, gehaertete Warteschleife, keine Pipes hinter langen Laeufen.
* Keine neuen Preregs, keine neuen Netzkoepfe. Nie den Projektordner verlassen. Laufzeiten ins
  Artefakt; sechs Standard-Kennzahlen in jedem Messbericht.
* Nie committen: `player_profiles.json`, `player_profiles.json.bak`.

### OFFENE NUTZER-ENTSCHEIDE (Fundstellen in Abschnitt 6)

Ein oder zwei Arme fuer v31 (Abschnitt 6 Punkt 1); Budget-Knopf fuer die Hilfsknoten als
WIRKUNGS-Frage (Punkt 2); Gruppe B des Aufraeumens (Punkt 3); R5/R4b-Sonden der
Promotionsliste ziehen oder die Zeile kuerzen (Punkt 4); Push-Stand (Punkt 5).

## 2. CHAMPION UND LEITER

**Champion laut `models/champion.txt`: `v30-b02_brierbest`** (Promotion 2026-09-19).
**Elo 1436 [1397; 1482]** aus 940 Partien im Leitersegment 2, Anker `hv4_anchor` fix 1000,
Bradley-Terry mit Block-Bootstrap. Er ist zugleich **Generator der v31-Erzeugung**.

Drei Kanten tragen ihn: Gating gegen `v29-b09` 443:297 = 59,9 Prozent (Block-z +5,36),
Anker `hv4_anchor` @150 mit n = 50 auf 45:5 = 90,0 Prozent, Champion-2 gegen `v28-b02`
96:54 = 64,0 Prozent.

| Modell | Elo | KI95 | Spiele | Frueh-Stopp-Kanten |
| --- | --- | --- | --- | --- |
| v29-b11@400 | 1440 | [1384; 1500] | 350 | 1 von 1 |
| **v30-b02@400 (Champion)** | **1436** | **[1397; 1482]** | **940** | 1 von 4 |
| v29-b03@400 | 1380 | [1340; 1426] | 640 | 3 von 4 |
| v30-b01@400 | 1369 | [1327; 1416] | 800 | 0 von 2 |
| v29-b09@400 | 1365 | [1332; 1407] | 2.990 | 2 von 9 |
| v29-b07@400 | 1356 | [1317; 1396] | 1.100 | 0 von 4 |
| v28-b02@400 | 1347 | [1316; 1385] | 4.100 | 6 von 18 |
| v27-b01@400 | 1306 | [1272; 1344] | 1.580 | 2 von 7 |

`v29-b11` fuehrt nominell mit vier Punkten, steht aber auf EINER frueh gestoppten Kante ueber
350 Partien und ist ein gepolsterter Champion ohne Trainingsschritt; die Intervalle ueberlappen
weit. Die beiden Tor-1-Kanten von `v30-b01` sind am 2026-09-19 nachgetragen worden, der
Kaltstart-Arm hatte bis dahin keinen Leiterknoten.

**Eingefrorene Artefakte:** `models/frozen_champions/` traegt nur noch `v29-b09` und `v30-b02`
(Zwei-Champion-Regel). `v27-b01` und `v28-b02` sind am 2026-09-19 geloescht, Beleg
restic-Snapshot `7157437d`; ihre Kanten stehen unveraendert im Register, die Artefakte kommen
fuer eine spaetere Neuverankerung aus restic zurueck.

## 3. LAUFZEITEN (gemessen, Planungsgroessen; Details in `../docs/measured_runtimes.md`)

| Aufbau | Dauer | Anmerkung |
| --- | --- | --- |
| Erzeugung 3 x 4.000 Partien @100, threads 11, 888/414 | **13,86 h** (v30) | 9,92 h (v28) / 12,8 h (v29); Sockel 18.984 s, temperiert 16.184 s, Ausflug 14.744 s |
| Erzeugungskosten je Partie @100, Policy-Klasse | 3,183 (v28) / 3,943 (v29) / **4,746** (v30) | +20,4 Prozent gegen v29, +49,1 Prozent gegen v28 |
| Blockbau fuers Fenster, Bloecke vom Waechter vorgebaut | 4 s plus **611 s** Merge | v30-Kette |
| Blockbau 2.800 Dateien plus Merge, 6 Worker, 884 | 2.144 s = 35,7 min | +9,2 Prozent gegen 794 |
| Training Warmstart 12 Epochen, 4,89 Mio Samples, 888/414 | **5.573 s = 1,55 h** (gebremst) | v30-b02, lief neben der b01-Arena; exklusiv frueher 57 min |
| Training KALTSTART 12 Epochen, 888/414 | **3.652 s = 1,01 h** | v30-b01; die alte ANNAHME 2,3-2,6 h stammte aus einer anderen Encoder-Aera |
| Tor 1 je Seed, 200 Paare @400, 10 Threads, mit Logs | **5.719 s** exklusiv / 6.940-7.468 s gebremst | 14,3 s je Partie exklusiv, 17,4-18,7 s gebremst |
| Anker-Kante n = 50 | **430 s** | seit 2026-09-19 die Groesse der Promotionsliste; n = 150 war 1.250-1.280 s |
| Champion-2-Kante n = 150 | **2.489 s = 41,5 min** | |
| Champion-Kanten je Kandidat gesamt | rund 3,5 h | 2 x Gating plus Anker plus Champion-2 |
| Promotion nach Checkliste (inkl. Golden-Probe 22 min) | 38 min | v29-Messung |
| Netz-Gesundheit komplett (Normen, tote Einheiten, offline, Platt) | rund 30 min | v30 |
| Voller Build: Lib-Tests, `--no-run`, Fixtures, Wheel | rund 5 min | `--no-run` allein 56 s |
| Anker-Drift / Anker-Konservierung | 22,4 s / 16,6 s | je 1.763 Schritte |
| Tagesschnappschuss restic plus check | 6-7 s | |

## 4. SPEC UND REZEPT

**Champion-Spec** `models/frozen_champions/v30-b02/spec.json`. **Erzeugungs-Spec**
`models/v30_generation.spec.json` (= `start_by_search_on.spec.json` plus `return_order_mode: 1`);
sie traegt auch die v31-Erzeugung.

**Engine-Stand:** INPUT_SIZE **888**, NUM_ACTIONS **414**, Vertragshash `6ef829e564c58bd5`
(unveraendert durch Gruppe A des Aufraeumens). Suchknoten: Mond 406-410, Rueckgabe 411-413,
Slot und Rotation als eigene Knoten mit Policy-Ziel. **Die Rueckgabe-Streuung sitzt seit
2026-09-19 im KNOTEN-Weg** (`self_play.rs`, eigener Seed-Unterscheider), die Maske dazu in
`engine/py/corpus_dataset.py` als eigene Bedingung auf `return_order_randomized` -- nicht ueber
`policy_target_valid`, weil beide Ketten `MOSAIC_IGNORE_POLICY_TARGET_VALID=1` fahren.

**Das v30-Rezept, belegt:** b03-Rezept mit `--moon-loss-weight 0`, `--ownership-weight 0` mit
`--ownership-head-2d`, ohne `--endgame-head`, `--opp-points-head` bleibt, 12 Epochen, lr 5e-05
cosine mit `--lr-t-max 12`, lambda 0,7, `--select-by-brier`, `--fast-loader`.

**Was v30 daran entschieden hat:** der KALTSTART ist widerlegt. Gleiches Fenster, gleicher
Monolith, gleicher Seed, gleiches Rezept, einziger Unterschied der Start -- 404:396 kalt gegen
443:297 warm, **9,36 Prozentpunkte**. Fuer v31 heisst das: **Warmstart von
`v30-b02_brierbest`**, kein Kaltstart mehr ohne eigenen Anlass.

**v31-Fenster** (`PREREG_v31_window.md` par.1): 2.947 Dateien aus `v30-b02` neu (1.201),
`v29-b11` als G-1 und `v28-b02` als G-2; `v27-b01` ist herausrotiert und geloescht. Seed
20260949, Val-Pool `^selfplay_v30-`, 580 Traeger. Die acht neuen Knoten sind erstmals in den
beiden juengsten Generationen belegt, also rund 81,6 Prozent des Fensters (HERLEITUNG aus par.1,
nicht am Korpus nachgezaehlt).

## 5. PREREG-BESTAND (5 OFFEN laut Index 2026-09-19; Ziel rund 7)

| Prereg | Was noch aussteht |
| --- | --- |
| `v31_window` | der laufende Zyklus selbst |
| `dome_return_order` | die Streuung ist gebaut und wirksam; offen ist ihre WIRKUNG, messbar erst am v31-Training |
| `code_cleanup_closeout` | Gruppe B (Wrapper, drei Spec-Felder) und Gruppe C |
| `difficulty_levels` | ganze Leiter auf den Schluss-Champion vertagt |
| `claude_play_interface` | Partien g08-g10, Abschluss mit dem Schlussmodell |

Beim Generationswechsel am 2026-09-19 nachgezogen: die Koepfe von `v30_window` (auf
ENTSCHEIDEN), `code_cleanup_closeout` (Gruppe A) und `dome_return_order` (Dosis 0,81), danach
`python tools/generate_prereg_index.py`.

## 6. OFFENE NUTZER-ENTSCHEIDE

1. **Ein oder zwei Arme fuer v31** (`PREREG_v31_window.md` par.5 Punkt 2). v30 fuhr kalt und
   warm; der Warmstart gewann mit 9,36 Punkten Abstand, die Kaltstart-Frage ist damit
   beantwortet. Ein zweiter Arm braucht also einen ANDEREN Faktor, sonst reicht einer.

2. **Budget-Knopf fuer die Hilfsknoten** (Slot, Rotation, Rueckgabe, Mond). Die Kosten sind
   hingenommen (Nutzer 2026-09-18: "wenn es was bringt stoert mich der mehraufwand nicht"); offen
   ist allein die WIRKUNG, und v31 ist der erste Zyklus, in dem sie beantwortbar ist: in v30
   waren die Knoten mit 40,8 Prozent Fensterabdeckung vorregistriert unterbelegt, jetzt sind es
   rund 81,6 Prozent. Trennung aus dem Lernstoff: der **Mondknoten** traegt in 11,64 Prozent der
   Sockel-Records ein Policy-Ziel, der **Rueckgabeknoten in 0,18 Prozent**.

3. **Gruppe B des Aufraeumens**, drei Punkte, je eigener Entscheid: der Wrapper
   `resolve_and_apply_stack_draw` (ein Test ruft ihn auf) und die drei Spec-Felder aus
   `KNOWN_FIELDS` (drei rote Tests, Alt-Specs duerfen sie tragen), beide
   `PREREG_code_cleanup_closeout.md` par.8d; dazu die **Kanonisierung der Bonuschip-Farben**
   (par.8e): fuenf zweifarbige Kombinationen liegen je zweimal im Pool, bei zweien ist die
   Reihenfolge zwischen den Zwillingen vertauscht (`dome.rs:250-273`, Quelle
   `docs/bonus_chips_colors.csv`). Wertung und Netz-Eingabe sind davon unberuehrt (Bitmaske bzw.
   Farb-Flags); Arbeit kostet es in `round5.rs:281` (ein Zufallsast zu viel) und
   `tiling_solver.rs:331` (Cache-Fehlgriffe). **Die Anzeige-Haelfte ist am 2026-09-19 gebaut**
   (`static/js/app.js`, Helfer `chipColors`); die Engine-Haelfte aendert Records und gehoert an
   einen Generationswechsel.

4. **R5- und R4b-Sonden der Promotionsliste** werden seit v24-b06 nicht gefahren, ihre Werkzeuge
   sind auf die v18-Aera voreingestellt. Entweder auf den aktuellen Kontrakt ziehen und wieder
   Pflicht, oder die Zeile auf "Platt und Alt-Set-Brier" kuerzen (`docs/promotion_checklist.md`
   Punkt 5).

5. **Push.** Stand 2026-09-19 nach dem Generationswechsel: gemessen mit
   `git rev-list --count origin/main..main`. Kein Push ohne Anweisung; der Nutzer pusht selbst.

### Aeltere, weiterhin offene Punkte (unveraendert uebernommen)

6. **Brier-Regel gerissen** (`PREREG_v30_window.md` par.3 Punkt 7d): der Brier von `v30-b02`
   steigt auf 0,26196 gegen 0,25507 des Bezugs `v29-b11`, und aus genau diesem Fit kommt die
   Anzeige-Kalibrierung. Der Arm mit dem schlechteren Brier gewinnt die Arena; `frozen_eval_set`
   stammt aus einer aelteren Verteilung.

7. **Manifest meldet Spec-Felder falsch** (geprueft 2026-09-13): `engine_config` zeigt fuer
   `envelope_search_c`, `envelope_projection_mode`, `envelope_hull_form`, `special_row6_w` und
   `return_order_mode` den Env-Default statt des wirksamen Spec-Werts. Kein Belegverlust, jedes
   Manifest nennt den Spec-Pfad. Vorschlag: Spec-Inhalt plus sha256 additiv ins Manifest.

8. **Sichtluecke bei den gezogenen Stapelplatten** (`stack_top_feature` par.16/16a): die
   Vorderseiten sind erst NACH dem Aufhoeren bekannt. (a) Die Aktionsliste verraet sie ueber die
   Rotationsfilterung (`game.rs` Z.402) -- betrifft die Suche, Reparatur beruehrt `NUM_ACTIONS`.
   (b) `serialize.rs` Z.375-379 serialisiert sie sofort, die Anzeige druckt sie -- betrifft den
   menschlichen Spieler, eingetreten in Partie g07.

9. **Paritaets-Tor und Alt-Records** (`rust_data_layer` par.9/9a): Kanal 76 weicht auf Records
   von vor dem A2-Fix ab, weil das Tor eine GESPEICHERTE gegen eine frisch gerechnete Groesse
   haelt. Offen: gespeicherte Felder aufgeben oder das Tor auf frische Zustaende beschraenken.

10. **Drei Sonden zeigen auf das geloeschte Artefakt `hv1_anchor`**
    (`anchor_referee_parity_probe.py`, `frozen_agent_referee_probe.py`,
    `frozen_worker_protocol_probe.py`). Umstellung auf `hv4_anchor` braucht neue
    Erwartungswerte, also einen Lauf. Lohnt das, oder entfallen die drei als historisch?

11. **`-Deep`-Lauf der Backup-Verifikation**: `verify_backup.ps1` empfiehlt ihn vor der ersten
    Loeschung; zuletzt am 2026-09-13 auf Nutzer-Entscheid nicht gefahren.

12. **Rahmen:** v30 ist released, das Schlussmodell heisst **Tessa**, und v31 laeuft, "damit die
    ganzen aenderungen wirklich sauber durchschlagen". Ab v30 keine neuen Preregs; Arme nur aus
    den jetzt offenen Preregs, Aufnahme ins Rezept per Nutzer-Entscheid.

13. **Kleinkram:** die Dry-Artefakte `evaluations/artifacts/_dry_*.json` vom Sonden-Bau koennen
    weg (Verzeichnis ist git-ignoriert).

## 7. VERBOTE UND STEHENDE REGELN

- **Kein Push ohne Anweisung.** Ahead-Stand im Chat melden.
- **Loeschung nur auf pfadgenaue Freigabe**, mit restic-Beleg je Gruppe. Frage ist keine
  Anweisung. `.h5`-Dateien sind per `tools/backup_excludes.txt` nicht im Backup, weil
  regenerierbar -- fuer sie gibt es keinen Snapshot-Beleg.
- **Messungen laufen exklusiv.** GPU und CPU duerfen parallel, zwei CPU-Messungen nie; ein Build
  zaehlt als Last. **Kein Commit waehrend eines Wanduhr-Laufs.**
- **Nie committen:** `player_profiles.json`, `player_profiles.json.bak`,
  `models/manifest_train_v28-b0*.json`, `evaluations/game_analysis/*`. Nach `git add -A` die zwei
  Profil-Dateien gezielt mit `git restore --staged` herausnehmen.
- **Dateien laufender Laeufe nicht anfassen** -- auch nicht `self_play.py`,
  `selfplay_manifest.py`, `config.py`, `engine/py/neural_net.py`, `corpus_dataset.py`: die
  Chunk-Prozesse importieren frisch.
- **Knoepfe, die self_play.py kennt, gehen als CLI-Flag hinein**, nicht ueber die Umgebung:
  `self_play.py` setzt die Variable aus seinem eigenen Default neu (Z.236-240).
- **Kettenskripte als DATEI starten** (`bash tools/x.sh`), NIE Heredoc-schreiben-und-starten in
  einem Befehl.
- **Lange Laeufe nie in eine Pipe und ohne eigene Umleitung**, mit Fortschritt (`python -u`,
  `flush=True`).
- **Vor dem Self-Play der naechsten Generation: `/mosaic-generation-turnover`** -- der Ablauf
  gehoert VOR den Start, nicht daneben (Vorfall 2026-09-19).
- **Regel 0**, Prereg-Kopf im selben Zug wie das Ergebnis, Laufzeiten ins Artefakt, sechs
  Standard-Kennzahlen in jedem Messbericht, kein Geviertstrich in Dateien, Bezeichner englisch,
  Inhalte deutsch.
- Keine neuen Netzkoepfe; nicht jeden Arm in die Elo-Leiter.

## 8. BEFUNDE, die eine Nachschau brauchen

- **Arena-Logs tragen keine `#a`-Zeilen**, weil die im PyGame-Pfad geschrieben werden
  (`py.rs:781`). Der Replayer riet dort die Rueckgabe-Reihenfolge kanonisch und divergierte in
  15-18 Prozent der Partien. Repariert ueber den Endzustand im Artefakt (`score_geo`,
  `dome_grid`); Tor 2b ist ab der naechsten Arena wieder verwendbar. Server- und Mensch-Logs
  waren nie betroffen.
- **Nicht-Transitivitaet am Leiterboden:** v22@25 gegen hv4@150 76 %, gegen hv4@600 50 %,
  hv4@600 gegen hv4@150 55 %. Bradley-Terry mittelt das.
- **SPRT stoppt zwischen Nachbar-Generationen nicht** (beide v30-b01-Laeufe `UNDECIDED_CAP_REACHED`),
  bei groesserem Abstand sehr wohl. Beim Gating bleibt der Stopp aktiv und zieht unter 150 Paaren
  eine Replikation nach; nur die Anker-Kante faehrt ohne ihn.
- **GUI und Arena: dasselbe Spiel, dieselbe Tiefe.** Beide enden in `select_final_root_child`,
  ohne Wurzelrauschen, mit Runde-5-Kurzschluss. Die GUI spielt immer bei 400 Sims. Latente
  Sollbruchstelle: die Arena zieht `builder_drafting_preference` der Suche vor, der Serverpfad
  kennt den Vorzug nicht.
- **Gating-Artefakte tragen keine Engine-Konfiguration** (`paired_gating.py`): ein Env-Knopf, der
  in einer Arena an war, ist dort nachtraeglich nicht belegbar.
- **`MOSAIC_ENVELOPE_REACH_W` und `_SLOT_W`** haben keine Spec-Entsprechung. Heute inert, weil
  das Rezept Projektionsmodus 1 faehrt.
- **Sims und Spaltenbau:** die Kurve am Champion faellt ueber 100-600 Sims monoton, allein ueber
  die VOLLENDUNG; die Teilspalten bleiben gleich.
- **Kein zurueckgehaltener Satz der laufenden Aera:** jede Datei in `data/` liegt in mindestens
  einem Fenster, deshalb ist der Trend ueber die Generationen nicht von der Verteilungsnaehe
  trennbar. Der Handgriff waere, vor dem v31-Training eine Scheibe des frischen Self-Plays zu
  reservieren und aus der Fensterliste zu nehmen.
- **Pfadform der Dateiliste im Cache-Schluessel:** Stempel und Verbraucher stimmen ueberein, die
  eigentliche Reparatur (Normalisierung auf Basenames) entwertet jeden Monolithen und ist
  Nutzer-Entscheid an einem Generationswechsel.
- **Python-Werkzeuge nach einem Kontraktwechsel:** `tools/offline_diagnosis.py`,
  `tools/oracle_metrics.py` und `tools/probes/*_gate.py` uebergeben `num_actions` noch explizit
  und laden Alt-Checkpoints darum nicht.
- `player_profiles.json` im Arbeitsbaum veraendert (Server-Seite), nicht committet.
