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

**NICHTS** (Stand 2026-09-20, Prozessliste geprueft).

**Die Promotion von `v31-b01` ist VOLLSTAENDIG** nach `docs/promotion_checklist.md`, alle sieben
Punkte: Champion gesetzt, vier Elo-Kanten registriert, Diagnostiken gefahren, Artefakt eingefroren
und per Referee-Selbsttest abgenommen, STATUS und Chronik nachgezogen. Herleitung und alle Zahlen:
Kapitel "Promotion v31-b01" in `../archive/history.md`.

### ZWEI OFFENE PUNKTE AUS DER PROMOTION

1. **Brier-Regel gestreift** (par.3 Punkt 7d): 0,22919 gegen 0,22804 des Vorgaengers, +0,5 Prozent
   relativ. Zweite Generation in Folge, aber deutlich weniger als die +2,7 Prozent bei `v30-b02`.
   Ein Intervall dazu liegt NICHT vor.
2. **R5 und R4b nicht gefahren** -- seit v24-b06 nicht mehr, Werkzeuge auf die v18-Aera
   voreingestellt. Fuer den Schluss-Champion waere R5 die einzige Pruefung des Value-Kopfs gegen
   eine EXAKTE Grundwahrheit. Nutzer-Entscheid: ziehen oder die Checklisten-Zeile kuerzen.

### WAS ALS NAECHSTES ANSTEHT

* **Drei Claude-Partien g08-g10** (`PREREG_claude_play_interface.md` P1) -- die letzten der Reihe,
  erstmals gegen den Schluss-Champion. Server VOR dem Start neu starten, sonst spielt er `v30-b02`;
  danach die Konsolenzeile "Champion-Spec ..." lesen.
* **Die Restliste des Aufraeumens** (`PREREG_code_cleanup_closeout.md` par.8h): nur noch
  Punkt 4 (15 Kopien des Binomialtests) sowie 9 und 10, die Rust sind und den vollen Torlauf
  brauchen. Erledigt am 2026-09-21: Punkte 5, 6, 8 (par.8j), Punkt 1 (par.8k, 62 rohe
  Korpus-Leser, davon 43 live defekt) und Punkt 2 (par.8l, 13 unvollstaendige
  Laufzeit-Bloecke; die uebrigen 57 bleiben nach der Entscheidung von 2026-08-27 stehen).
  Dazu `tools/build_frozen_golden_probe.py`: laeuft 22 Minuten OHNE jede Fortschrittszeile (kein
  `flush` im ganzen Werkzeug), Verstoss gegen die Regel aus CLAUDE.md.
  Aus par.8g ist nur noch **Punkt 10** offen (`round_transition_resample`) -- ein Entscheid ueber
  den CODE, nicht ueber seine sieben Tests.
* **Letzter restic-Snapshot mit Beleg** und der Abschlussbericht.

**Erledigt am 2026-09-21:** die zehn Punkte aus par.8g als EIN Rust-Buendel (par.8i) -- neun
Beispiele unter `engine/examples/` und die drei toten E2E-Skripte unter `engine/` entfernt, der
Cache-Messtest auf `#[ignore]`, die Groessen-Basislinie nachgezogen; **drei Punkte nach Pruefung
abgelehnt** (der Stolperdraht am Fenster-Schluessel hat gehalten, die Tiling-Geometrie-Sonde lebt,
und der Nutzen der zwei Konventions-Teile IST die bessere Fehlermeldung). Alle Tore gruen,
Anker-Drift 1.763 Schritte identisch. **Neu ungedeckt:** die HTTP-Routen von `server.py` haben
keine automatische E2E-Abdeckung mehr; die drei Skripte waren rot, weil ihre eigene Zugwahl die
seit v30 neuen Knotentypen nicht kennt.

**Erledigt am 2026-09-20 nach der Promotion:** die Umbenennung auf Tessa in allen drei
Schritten (Manifestfeld, Frontend ueber die Konstante `AI_DISPLAY_NAME`, README), das
portable Bundle neu gebaut und am laufenden Bild geprueft, und die Loeschung von
`frozen_champions/v29-b09`.

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

Budget-Knopf fuer die Hilfsknoten als WIRKUNGS-Frage (Abschnitt 6 Punkt 2); Gruppe B des
Aufraeumens (Punkt 3); R5/R4b-Sonden ziehen oder die Checklisten-Zeile kuerzen (Punkt 5);
die drei GUI-Stellen im System-Sinn ("KI-Debugger", "KI-Einstellungen") und die Fehlertexte in
`server.py` -- mit umbenennen oder als System-Begriff stehen lassen.

## 2. CHAMPION UND LEITER

**Champion laut `models/champion.txt`: `v31-b01_brierbest`** (Promotion 2026-09-20), nach aussen
**Tessa**. **Elo 1458 [1414; 1510]** aus 1.000 Partien im Leitersegment 2, Anker `hv4_anchor`
fix 1000, Bradley-Terry mit Block-Bootstrap. **Keine seiner vier Kanten ist frueh gestoppt.**

Vier Kanten tragen ihn: Gating gegen `v30-b02` 461:339 = 57,62 Prozent ueber zwei Seeds
(Block-z +4,24 auf differenzierten Werten), Anker `hv4_anchor` @150 mit n = 50 auf 45:5,
Champion-2 gegen `v29-b09` 79:71. **Die Champion-2-Kante liegt unter der transitiven Erwartung**
(52,7 statt rund 65 Prozent); unpaariertes Instrument, n = 150, nicht signifikant, Handshake
GRUEN. Herleitung im Kapitel "Promotion v31-b01" in `../archive/history.md`.

| Modell | Elo | KI95 | Spiele | Frueh-Stopp-Kanten |
| --- | --- | --- | --- | --- |
| **v31-b01@400 (Champion, Tessa)** | **1458** | **[1414; 1510]** | **1.000** | **0 von 4** |
| v29-b11@400 | 1439 | [1388; 1493] | 350 | 1 von 1 |
| v30-b02@400 | 1420 | [1382; 1463] | 1.740 | 1 von 6 |
| v29-b03@400 | 1378 | [1339; 1424] | 640 | 3 von 4 |
| v30-b01@400 | 1368 | [1322; 1418] | 800 | 0 von 2 |
| v29-b09@400 | 1364 | [1328; 1404] | 3.140 | 2 von 10 |
| v28-b02@400 | 1345 | [1314; 1382] | 4.100 | 6 von 18 |

**Engine-Stand:** Wheel **1.0.0** (mit dem Schluss-Champion von 0.1.0 gehoben), Vertragshash
unveraendert `6ef829e564c58bd5`, 888/414. Die Version geht weder in den Hash noch in einen
Cache-Schluessel noch in den Handshake ein -- belegt am lebenden Objekt (Golden Probe 10/10 ueber
den Versionswechsel, Anker-Drift gruen).

**Eingefrorene Artefakte:** `models/frozen_champions/` traegt genau `v30-b02` und `v31-b01`
(Zwei-Champion-Regel). **`v29-b09` ist am 2026-09-20 geloescht**, Beleg restic-Snapshot
`cc0d2a15` (7 sicherungswuerdige Dateien; das `venv/` ist per `backup_excludes.txt` ausgenommen
und aus dem mitgesicherten Wheel neu baubar). Seine zehn Kanten stehen unveraendert im Register,
der Knoten bleibt bei 1364 [1328; 1404] aus 3.140 Partien. **Folge, bewusst in Kauf genommen:**
die auffaellige Champion-2-Kante (52,7 Prozent) laesst sich ohne Rueckholung aus restic nicht mehr
mit DEMSELBEN Wheel nachfahren.

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

4. **Die Golden Probe des Elo-Ankers meldet ab jetzt dauerhaft ROT** (`PREREG_code_cleanup_closeout.md`
   par.8e). Sie traegt Records der alten Bonuschip-Schreibweise; die Kanonisierung vom 2026-09-20 aendert
   den serialisierten Zustand, NICHT das Spiel -- belegt Feld fuer Feld ueber 1.763 Schritte, alle
   Zugfelder gleich. Drei Wege: (a) der Pruefer normalisiert die Farblisten beidseits
   (Koordinator-Empfehlung, Vorbehalt: eng begrenzen, sonst schluckt der Waechter kuenftig echte
   Unterschiede), (b) Golden Probe neu erzeugen (verliert die Faehigkeit, aeltere Drift zu melden),
   (c) nichts tun und das ROT dokumentieren (abgeraten). **Bis dahin: die Drift-Pruefung vom
   2026-09-20 ist inhaltlich bestanden.**

5. **R5- und R4b-Sonden der Promotionsliste** werden seit v24-b06 nicht gefahren, ihre Werkzeuge
   sind auf die v18-Aera voreingestellt. Entweder auf den aktuellen Kontrakt ziehen und wieder
   Pflicht, oder die Zeile auf "Platt und Alt-Set-Brier" kuerzen (`docs/promotion_checklist.md`
   Punkt 5).

6. **Push.** Stand 2026-09-21: **0 Commits vor `origin/main`** (der Nutzer hat gepusht),
   Arbeitsbaum sauber. Kein Push ohne Anweisung; der Nutzer pusht selbst.

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
  Chunk-Prozesse importieren frisch. **Auch eine reine Kommentaraenderung zaehlt** (Verstoss
  2026-09-20 am `corpus_dataset.py` waehrend des Cache-Waechters, folgenlos geblieben): das
  Risiko ist das Schreibfenster, nicht der Inhalt -- ein Worker, der genau dann importiert,
  sieht eine halbe Datei.
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
