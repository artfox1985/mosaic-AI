<!-- STATUS: OFFEN | Frage: Welche Schwierigkeitsstufen bietet die GUI beim Spiel gegen das Netz an, und woran ist jede Stufe gemessen? | Beleg: nichts gefahren. Bestand (par.2): Presets im Server sind aus der GUI nicht erreichbar, alle 33 Mensch-Partien liefen @400 (Mensch 24:7:2); Vorschlag (par.4): Stufen als Leiter EINGEFRORENER Spieler mit Elo-Knoten (hv1 1000 bis Champion 1405), Heuristik-Stufen = Anker-Artefakte (Nutzer-Entscheid par.8.7), Sims nur als Feinregler; Stufe 0 (Inventur, Eingabelaenge 744/755) VOR jedem Bau. -->

# Vorregistrierung: Schwierigkeitsstufen beim Spiel gegen das Netz

**Angelegt 2026-09-11** auf Nutzer-Auftrag ("schreib mir eine prereg fuer die
unterschiedlichen schwierigkeitsstufen beim spiel gegen das netz. wir kommen
langsam zu einem projektende. vielleicht noch 1-2 generationen nach v28 und dann
ist es gut"). VOR jedem Bau und jeder Messung dieses Strangs. Sprache im Code
englisch (Konvention 2026-08-24), Dateiname englisch; die Stufennamen in der GUI
sind deutsch (Anzeige, kein Bezeichner).

## par.1 Anlass und Zweck

Das Projekt endet nach ein bis zwei Generationen nach v28. Was bleibt, ist die
GUI mit dem Netz als Gegner. Heute hat sie GENAU EINE Staerke (par.2): den
amtierenden Champion bei 400 Simulationen. In 33 Mensch-Partien (par.2.4) hat
der Mensch 24 gewonnen, 7 verloren und 2 punktgleich beendet; gegen die zwei
juengsten Champions steht es 5:5. Fuer die Stammspieler ist das eine Stufe, die
sie schlagen koennen, fuer einen Anfaenger eine Wand, und nach oben gibt es
nichts. Ein Endprodukt braucht eine Leiter in beide Richtungen.

Die Frage ist NICHT "wie macht man das Netz schwaecher" (das geht trivial:
weniger Sims, Zufallszuege). Die Frage ist: **welche Stufen sind GEMESSEN
verschieden stark, in welcher Reihenfolge, und spielt jede Stufe noch wie ein
Gegner und nicht wie ein Wuerfel.** Dafuer gibt es im Baum bereits eine Leiter,
die niemand fuer die GUI benutzt: das Elo-Register (par.2.5).

## par.2 Was heute ist (Code geprueft 2026-09-11)

### par.2.1 Presets im Server, aus der GUI unerreichbar

`server.py:275-283` traegt `DIFFICULTY_PRESETS`: `easy` = Heuristik @60,
`medium` = Champion @60, `hard` = Champion @150, `expert` = Champion @400,
`_default` = Champion @400. `_resolve_difficulty` (`server.py:286-293`) greift
auf ein Preset nur, wenn NICHT beide Werte `model` und `sims` mitkommen.

Das Frontend schickt beide immer mit: `static/js/app.js:239-240` liest
`ng-model` und das Zahlenfeld `ng-sims` (Default 400, `static/index.html:279`),
`app.js:273-274` legt beides in den Rumpf von `/api/game/new`. Ein Feld
`difficulty` kommt in `static/` nicht vor (Grep ueber `static/js/*.js` und
`static/index.html`: null Treffer). **Die Presets sind toter Code fuer die GUI;
die Schwierigkeit ist heute ein nacktes Zahlenfeld "Sims".** `README.md:300-303`
beschreibt die Presets trotzdem als Feature (Konsument, par.9).

### par.2.2 Welcher Spieler tatsaechlich spielt

- Netz: `_ai_model` aus `models/champion.txt` (heute `v27-b01_brierbest`),
  ONNX ueber `_champion_onnx_path` (`server.py:144-164`: erst
  `models/alphazero_<name>.onnx`, dann `models/frozen_champions/<name>/model.onnx`).
- Spec (Knoepfe): `_apply_champion_spec_env` (`server.py:245-272`) setzt die
  Spec des Champions EINMAL beim Serverstart in die Umgebung. Wer per
  `POST /api/ai/config` (`server.py:1487-1505`) ein anderes Modell laedt,
  spielt es mit den Knoepfen des CHAMPIONS. Ein Champion ist Modell PLUS Spec
  (`docs/promotion_checklist.md`); ein anderes Modell unter fremder Spec ist
  eine ungemessene Entitaet (`feedback_measured_identity_gets_own_bxx`).
  Beispiel: `models/v24-b06_brierbest.spec.json` hat `envelope_hull_form 1`
  und `special_row6_w 0.0`, die v27-Spec `hull_form 2` und `row6_w 1.0`
  (beide Dateien gelesen).
- Heuristik ("easy"): `_resolve_model_path` (`server.py:296-309`) gibt fuer
  `heuristic` None, der Zug laeuft ueber `ai_step_json` (`engine/src/py.rs:524`),
  also die LEBENDE In-Process-Heuristik. Das ist die Entwicklungsumgebung, nicht
  der eingefrorene Anker `hv1_anchor` (Skill `mosaic-anchor-invariance`); ihr
  Elo steht in keinem Register. Welche Variante (hv1/hv2) sie heute spielt, ist
  NICHT geprueft (Stufe 0). **Nutzer-Entscheid 2026-09-11 (par.8.7): die
  Heuristik-Stufen spielen die EINGEFRORENEN Anker (`hv1_anchor`,
  `hv2_generator`), nicht den lebenden Pfad.**
- Suche in der GUI: `net_search_with_tree(..., add_root_noise=false, ...)`
  (`py.rs:571` fuer den Debug-Pfad; fuer den Zugpfad `ai_drafting_net_step`
  ANNAHME gleicher Aufruf, Stufe 0 prueft es). Kein Wurzelrauschen, keine
  Temperatur: die GUI spielt den Suchzug, wie die Arena ihn spielt. Die
  wirksame Sim-Zahl ist `net_effective_sims` (`net_mcts.rs:2699-2705`), unter
  Gumbel mit entkoppelten Sims gleich `base_sims`.
- Env-Knoepfe werden zur Suchzeit gelesen (`py.rs:969`, `SearchConfig::from_env`
  im Tiling-Schritt; fuer den Drafting-Pfad ANNAHME, Stufe 0). Wenn das stimmt,
  kann ein Stufenwechsel die Spec der Stufe OHNE Serverneustart setzen.

### par.2.3 Welche Spieler im Baum liegen

| Spieler | Ort | Modell | Spec | Wheel | Elo-Knoten (par.2.5) |
| --- | --- | --- | --- | --- | --- |
| hv1_anchor | `models/frozen_heuristics/hv1_anchor/` | netzlos | ja | ja (Artefakt) | `Heuristik_hv1_anchor@150` = 1000 (fix) |
| hv2_generator | `models/frozen_heuristics/hv2_generator/` | netzlos (`label_net.onnx` fuer Labels) | ja | ja | `Heuristik_v2huelle@150` 1100 [1053, 1145]; **Identitaet hv2_generator = v2huelle NICHT geprueft** (Manifest: `heuristik_variante hv2`, Rolle "Erzeuger v22-Korpus") |
| v24-b06 | `models/alphazero_v24-b06_brierbest.onnx` + `models/v24-b06_brierbest.spec.json` | lebend | lebend | Live-Wheel | `v24-b06_k3p10@400` 1269 [1240, 1303] oder `v24-b06@400` 1238; **welcher Knoten zur Spec-Datei gehoert: NICHT geprueft** |
| v24-b07 | `models/alphazero_v24-b07_brierbest.onnx` + `models/v24-b07_brierbest.spec.json` | lebend | lebend | Live-Wheel | `v24-b07@400` 1283 [1248, 1318] |
| v25-b01 | `models/frozen_champions/v25-b01/` | ja | ja | ja | 1336 [1298, 1380] |
| v26-b01 | `models/frozen_champions/v26-b01/` | ja | ja | ja | 1364 [1324, 1406] |
| v27-b01 | `models/frozen_champions/v27-b01/` (Champion) | ja | ja | ja | 1405 [1361, 1453] |

Nicht mehr im Baum: v19, v20, v21, v23 (ONNX geloescht; `models/v23-b01_k3p10.spec.json`
liegt noch). Die Elo-Knoten dieser Modelle bleiben im Register, ihre Spieler sind
nur aus dem restic-Repo wiederherstellbar (`run:<name>`-Snapshots, nicht geprueft
fuer diese vier).

### par.2.4 Mensch gegen Netz: 33 Partien, alle bei 400 Sims

`static/log/game_*.log`, Kopfzeile 2 je Datei (alle 33 gelesen): `ai_player 1`
in allen 33, `first_player 0` in 28 und `1` in 5; `ai_sims 400` in allen 33.
Vier Menschen-Namen im Kopf: "Spieler 1" (23 Partien), "Spielerin" (8),
"Erwin" (1), "Spieler" (1); wer dahintersteht, steht nicht im Log.

**Endstand = die Zeilen `🏆 <Name>: Endwertung ... Gesamt: X Pkt`** (Regex
`FINAL_SCORE`, `tools/analyze_game_log.py:152`), je Partie eine je Seite. NICHT
die Zeile `# SPIELENDE: [..]`: die schreibt `server.py:1432-1436` aus
`_rust.scores()` beim Aufruf von `/api/end_game_log`, und in allen 33 Logs
weicht sie von den 🏆-Summen ab (Beispiel 2026-09-04 19:49: SPIELENDE [33, 48],
🏆 37:36). Warum sie die Endwertung nicht traegt, ist NICHT geprueft (ANNAHME:
der Aufruf kommt vor dem Einrechnen der Endwertung in `scores`). Die erste
Fassung dieser Prereg (Commit ea32dd3) hatte aus SPIELENDE gezaehlt und 13:18
gemeldet; der Nutzer hat es angezweifelt, die 🏆-Zeilen widerlegen es.

| Gegner | n | Mensch gewinnt | verliert | Punktgleich |
| --- | --- | --- | --- | --- |
| v21_2d_brierbest @400 | 13 | 12 | 0 | 1 (80:80) |
| v23-b01_k3p10 @400 | 9 | 6 | 2 | 1 (51:51) |
| v25-b01_brierbest @400 | 1 | 1 (69:0, KI-Endwertung 0, Abbruch nicht ausgeschlossen) | 0 | 0 |
| v26-b01_brierbest @400 | 7 | 3 | 4 | 0 |
| v27-b01_brierbest @400 | 3 | 2 | 1 | 0 |
| **gesamt** | **33** | **24** | **7** | **2** |

Nur "Spieler 1"/"Spieler" gegen v26/v27 (9 Partien): 5 Siege, 4 Niederlagen.
Punktgleichstaende loest die Startspielerstein-Regel im Spiel auf; hier steht
die rohe Endwertung. Einheit: Partien; Grundmenge: alle Logs in `static/log/`.
Lesart, MARKIERT als Deutung: v21 (Elo 1190) schlagen die Menschen durchweg,
v23 (1242) meist, v26/v27 (1364/1405) etwa zur Haelfte. Der Stammspieler liegt
damit ungefaehr auf Champion-Niveau; n = 10 gegen v26/v27 traegt keine feinere
Zahl. Fuer den Zuschnitt heisst das: die Leiter braucht Stufen UNTER dem
Champion fuer Neue und mindestens eine Stufe DARUEBER fuer die Stammspieler,
und die obere Stufe ist nicht optional (H3).

### par.2.5 Die vorhandene Leiter: das Elo-Register

`python tools/elo_tracker.py report` (2026-09-11 gelesen, 54 Match-Zeilen in
`evaluations/elo_history.csv`): Anker `Heuristik_hv1_anchor@150` = 1000 fix,
darueber v2huelle 1100, v19 1123, v20 1170, v21 1190, v23-b01_brierbest 1210,
v23-b01_k3p10 1242, v24-b06 1238, v24-b07 1283, v25-b01 1336, v26-b01 1364,
v27-b01 1405 (Konfidenzintervalle in par.2.3). ALLE Netz-Knoten sind @400
gemessen (`sims_a,sims_b`: 43 Zeilen 400/400, 11 Zeilen 400/150). **Fuer keinen
Champion gibt es eine Elo-Kante bei anderer Sim-Zahl.** Was zu Sims gemessen
ist, steht in `PREREG_search_depth_column_optimum.md`: dasselbe Netz (v22-b05)
@25 gegen @400 verliert 11:29 (SPRT H0, p = 0,0117), @100 gegen @400 33:47
(n.s.), und die flache Suche baut MEHR Spalten (Plateau 25-100 Sims). Eine
Sims-Leiter ist also nicht nur ungemessen, sie aendert auch den STIL des
Gegners, nicht nur seine Staerke.

Umrechnung Elo-Differenz in Erwartungswert (logistische Formel des
Elo-Systems, keine Messung): 100 Punkte = 0,64, 200 = 0,76, 300 = 0,85,
400 = 0,91 Erwartungsscore fuer den Staerkeren.

## par.3 Hypothesen (VOR jeder Messung)

- **H1 (Leiter aus Spielern, nicht aus Sims).** Eine Stufenfolge aus
  eingefrorenen Spielern mit Elo-Knoten (hv1 1000, hv2 1100, v24 ~1270, v25
  1336, v27 1405) ist monoton und in Schritten von 60 bis 130 Elo bereits
  GEMESSEN (par.2.5). Sie kostet keine neue Kante; jede Stufe spielt ihren
  Stil bei voller Suche. Erwartung: die Stufenreihenfolge, wie der Mensch sie
  erlebt (par.5 Stufe 4), stimmt mit der Elo-Reihenfolge ueberein.
- **H2 (Sims sind ein Feinregler, keine Stufe).** Innerhalb einer Stufe darf
  die Sim-Zahl die Antwortzeit steuern, aber die Stufe wird nicht durch Sims
  definiert. Grund: par.2.5 (Stilwechsel bei flacher Suche) und die fehlende
  Kante. Wird eine Stufe doch ueber Sims gebildet (par.4.2, Einsteigerstufe),
  bekommt sie ihre eigene Kante (par.5 Stufe 2).
- **H3 (die obere Stufe ist noetig, ihre Grenze ist die Antwortzeit).** Die
  Stammspieler stehen 5:5 gegen v26/v27 (par.2.4); eine Stufe UEBER dem Champion
  @400 (Champion @1200) gehoert in die Leiter. Ob @1200 spielbar ist,
  entscheidet die gemessene Sekundenzahl je Zug (par.5 Stufe 1); ob es staerker
  ist, braucht eine Kante (par.5 Stufe 2b), sonst bleibt die Stufe als
  "ungemessen staerker" markiert.
- **H4 (ein Einsteiger braucht etwas unter 1000).** Der Anker hv1 @150
  verliert 34:116 gegen v21 (Register), und v21 verlieren die Menschen hier
  nie (12:0:1). Ob hv1 @150 fuer einen Anfaenger schon zu stark ist, sagt keine
  Zahl im Baum; par.5 Stufe 2 misst hv1 @40 gegen hv1 @150 als Kandidat fuer
  eine Stufe unter dem Anker.
- **H5 (Kein Wuerfel).** Zufallszuege, Temperatur-Sampling und
  Punkte-Handicaps werden NICHT gebaut (par.6). Eine Stufe, die absichtlich
  Fehler macht, lehrt den Menschen falsche Muster; das Ziel ist ein schwaecherer
  GEGNER, kein zufaelligerer.

## par.4 Bauform (registriert VOR dem Bau)

### par.4.1 Stufen-Tabelle (Vorschlag, Nutzer-Entscheid par.8.1)

| Stufe | Anzeige (deutsch) | Spieler (Modell + Spec + Sims) | Quelle | Elo-Knoten |
| --- | --- | --- | --- | --- |
| 1 | Einsteiger | hv1 @40 (NUR wenn Stufe 2 der Messung ihn als schwaecher belegt, sonst entfaellt Stufe 1) | `frozen_heuristics/hv1_anchor` | zu messen (par.5 Stufe 2) |
| 2 | Anfaenger | hv1 @150 | `frozen_heuristics/hv1_anchor` | 1000 (Anker) |
| 3 | Fortgeschritten | hv2 @150 | `frozen_heuristics/hv2_generator` | 1100 (Identitaet zu pruefen) |
| 4 | Erfahren | v24-b07 @400 mit `v24-b07_brierbest.spec.json` | lebende Datei, einzufrieren (par.4.4) | 1283 |
| 5 | Stark | v25-b01 @400 mit seiner Spec | `frozen_champions/v25-b01` | 1336 |
| 6 | Champion | amtierender Champion @400 mit seiner Spec (heute v27-b01; am Projektende der letzte) | `frozen_champions/<champion>` | 1405 heute |
| 7 | Meister | Champion @1200 (Sims-Zahl nach Stufe 1 der Messung: die hoechste unter der Antwortzeit-Schwelle par.4.5) | wie 6 | ungemessen; Kante par.5 Stufe 2b |

Abstaende: 100, 180, 50, 70 Elo zwischen den Stufen 2 bis 6; die Luecke
zwischen 3 und 4 ist die groesste (hv2 1100 gegen v24-b07 1283). Ob eine
Zwischenstufe (v24-b06 1238 oder ein aus dem restic-Repo geholtes v21/v23)
noetig ist: Nutzer-Entscheid par.8.2. Sechs Stufen sind der Vorschlag; mehr
als sieben Stufen unterscheidet kein Mensch (ANNAHME, keine Messung).

**Die Heuristik-Stufen spielen die eingefrorenen Anker** (`hv1_anchor`,
`hv2_generator`), NICHT die lebende In-Process-Heuristik (par.2.2);
Nutzer-Entscheid 2026-09-11 (par.8.7). Wie: entweder die Server-Heuristik wird
als hv1/hv2 mit der Spec des Artefakts konfiguriert und per Drift-Pruefung
(Skill `mosaic-anchor-invariance`, 22 s) als zuggleich mit dem Artefakt belegt,
oder der Zug laeuft ueber den Artefakt-Worker (`tools/frozen_champion_worker.py`)
aus dem Wheel des Artefakts. Der Weg ist eine Bau-Frage nach Stufe 0 (par.5);
der Spieler ist entschieden.

### par.4.2 Server

- `DIFFICULTY_PRESETS` wird zur Stufentabelle: je Stufe `model` (Pfad ins
  Artefakt), `spec` (Pfad), `sims`, `label`. Die Spec der Stufe wird beim
  Stufenwechsel in die Umgebung gesetzt (derselbe Mechanismus wie
  `_apply_champion_spec_env`, aber je Stufe und mit Rueckstellung der Felder, die
  die neue Spec nicht traegt); Voraussetzung: Env wird zur Suchzeit gelesen
  (par.2.2, Stufe 0 prueft es fuer den Drafting-Pfad).
- `/api/game/new` und `/api/ai/config` nehmen `difficulty` als Stufennamen; die
  Felder `model`/`sims` bleiben als Expertenpfad (Stufe "Frei") erhalten.
- Der Log-Kopf traegt `difficulty` (Stufenname) zusaetzlich zu `ai_model`,
  `ai_sims`, `champion_spec`, `knobs` (seit 2026-09-10). Ohne diesen Eintrag
  ist eine Mensch-Partie spaeter keiner Stufe zuzuordnen (par.2.4 konnte nur
  deshalb ausgewertet werden, weil alle bei 400 liefen).
- Presets zeigen auf EINGEFRORENE Artefakte, nie auf `models/alphazero_*.onnx`:
  `models/` wird bei jedem Generationswechsel aufgeraeumt (Skill
  `mosaic-generation-turnover`, Schritt 5), ein Preset auf eine lebende Datei
  bricht still (Praezedenz: Champion nur noch im Artefakt, `server.py:151-154`).

### par.4.3 Frontend

- Das Zahlenfeld `ng-sims` weicht einer Auswahl mit den Stufennamen und je
  Stufe einem Hinweis "Antwortzeit ca. X s je Zug" (X aus par.5 Stufe 1, nicht
  geschaetzt). Stufe "Frei" blendet die heutigen Felder Modell/Sims ein.
- Die Stufe ist im Spielfenster sichtbar (heute: nur `ai_model`/`ai_sims` in der
  Antwort von `/api/game/new`, `server.py:704-705`).
- Keine Aenderung an Lehrer-Modus (`teacher_level`), Tipp und Coach: das ist
  Hilfe fuer den Menschen, keine Staerke des Gegners; die Achsen bleiben getrennt.

### par.4.4 Einfrieren der Stufen-Spieler

Jede Stufe, deren Spieler heute als lebende Datei liegt (v24-b07), bekommt ein
Artefakt `models/frozen_champions/v24-b07/` mit `model.onnx`, `spec.json`,
`manifest.json` und Golden-Probe (Muster: v25-b01; das Wheel ist fuer die GUI
das Live-Wheel, das Artefakt-Wheel dient der Konservierungspruefung). Das
Artefakt v24-b07 hat der Nutzer am 2026-09-10 geloescht (Turnover v27); ob es
fuer eine Stufe neu entsteht, ist Nutzer-Entscheid par.8.3.

### par.4.5 Eingabelaenge 744 gegen 755 (Pflichtpruefung VOR dem Bau)

Variante B (`PREREG_v28_window.md` par.9) hebt `INPUT_SIZE` auf 755; die elf
neuen Werte haengen am Ende (Index 744 bis 754, `engine/src/features.rs`
Abschnitt 15). Alle Stufen-Spieler unter v28-b02 sind 744er-Modelle.
`Net::load_auto` liest die Eingabeform aus der ONNX-Datei
(`engine/src/net.rs:100-125`, `InputLayout`), aber ob der Merkmalsvektor des
755er-Wheels fuer ein 744er-Modell auf dessen Laenge GEKUERZT wird oder der
Vorwaertspass abbricht, ist NICHT geprueft. Stufe 0 prueft genau das an
`v25-b01/model.onnx` unter dem Variante-B-Wheel. Faellt es rot aus, gibt es
zwei Wege, Nutzer-Entscheid par.8.4: (a) Praefix-Kuerzung im Wheel (die ersten
744 Werte sind byte-identisch zum alten Vektor, Praefix-Eigenschaft aus dem
Bau), (b) die Leiter unter dem Champion bleibt auf dem 744er-Wheel und die GUI
laedt je Stufe das Wheel des Artefakts (Worker-Pfad). Ohne diesen Entscheid
macht Variante B ALLE aelteren Stufen in der GUI unspielbar.

Antwortzeit-Schwelle fuer Stufe 7 (Vorschlag, Nutzer-Entscheid par.8.5):
hoechstens 5 s je Zug im Median auf dem Entwicklungsrechner, gemessen in
Stufe 1.

## par.5 Messgroessen und Stufen (VOR dem Bau festgelegt)

**Stufe 0: Inventur, keine Rechenlast.** (a) Je Stufen-Spieler: Artefakt
vollstaendig (Modell, Spec, Manifest, Golden-Probe)? (b) Identitaet
hv2_generator = Knoten `Heuristik_v2huelle` (Manifest gegen `elo_history.csv`
Kommentar der Kante vom 2026-08-25). (c) Zu welchem Elo-Knoten gehoert
`v24-b06_brierbest.spec.json` (k3p10 oder nicht)? (d) Liest der Drafting-Pfad
der GUI die Knoepfe zur Suchzeit (`ai_drafting_net_step`)? (e) Welche
Heuristik-Variante spielt `ai_step_json` heute? (f) Eingabelaenge: 744er-Modell
unter 755er-Wheel (par.4.5), EIN Vorwaertspass, kein Messlauf. Ergebnis:
Tabelle in par.10, keine Zahl ohne Pruefstelle.

**Stufe 1: Antwortzeit je Stufe, gemessen.** Je Stufe 2 Partien Netz gegen
Netz ueber den GUI-Pfad (`ai_step_net_json` bzw. `ai_step_json`, Seeds
20260950 und 20260951, ein Prozess, 11 Threads wie im Spielbetrieb),
aufgezeichnet je Zug: Wanduhr in s. Kennzahl: Median und 90. Perzentil der
Sekunden je Zug, Grundmenge Drafting-Zuege beider Seiten, Einheit s je Zug.
Artefakt `evaluations/artifacts/difficulty_latency_<datum>.json` mit
`laufzeit`-Block. Exklusiv (CPU frei, neben GPU-Training erlaubt). Kosten:
rund 14 Partien, unter 10 min (ANNAHME aus 6,98 s je Self-Play-Partie @400,
`docs/measured_runtimes.md`; die Zahl dort ist ueber viele parallele Partien
gemittelt, hier ist es eine Partie am Stueck, darum wird gemessen).

**Stufe 2: Kante fuer die Einsteigerstufe.** Gepaarte Arena hv1 @40 gegen
hv1 @150 (Anker-Artefakt beide Seiten, `tools/paired_gating.py` oder
`frozen_referee_match.py`, 100 Paare = 200 Partien, `--block-size 5`,
Seed 20260952, `--log-games`). Entscheidungsregel, VORAB: Stufe 1 der Tabelle
entsteht nur, wenn hv1 @40 hoechstens 80 von 200 Partien gewinnt
(Vorzeichentest auf Paardifferenzen p < 0,05); sonst entfaellt sie, und
"Einsteiger" ist hv1 @150. Eintrag ins Elo-Register als Knoten
`Heuristik_hv1_anchor@40`. Sechs Standard-Kennzahlen (CLAUDE.md) aus den Logs.
Kosten: rund 200 Partien Heuristik gegen Heuristik, unter 5 min (ANNAHME).

**Stufe 2b: Kante fuer die Meister-Stufe.** Gepaarte Arena Champion @S gegen
Champion @400 (S = hoechste Sim-Zahl unter der Antwortzeit-Schwelle aus
Stufe 1, Kandidat 1200), 100 Paare, `--block-size 5`, Seed 20260953,
`--log-games`. Entscheidungsregel, VORAB: die Stufe traegt den Namen "Meister"
nur, wenn Champion @S mindestens 120 von 200 gewinnt (Vorzeichentest p < 0,05);
sonst wird sie als "Champion, langsamer" gestrichen. Eintrag ins Elo-Register
als Knoten `<champion>@S`. Kosten: 200 Partien @1200 gegen @400, rund
4-mal die Kosten einer @400-Kante (ANNAHME).

**Stufe 3: Gespielt = gemessen.** Je Stufe eine Partie ueber den GUI-Pfad und
dieselbe Partie ueber den Arena-Pfad (gleicher Seed, gleiche Spec, gleiche
Sims): Zugfolge byte-gleich (Muster: Netz-Paritaets-Fixture, Promotions-
Checkliste 5d). Rot heisst: die Stufe spielt in der GUI einen anderen Spieler
als den, dessen Elo sie traegt. Kein Bau der Auswahl, bevor jede Stufe gruen
ist.

**Stufe 4: Mensch-Validierung (klein, qualitativ, markiert).** Der Nutzer
spielt je Stufe mindestens 3 Partien (Log-Kopf mit `difficulty`). Kennzahlen je
Stufe: Siege, Punkte, Margin, plus die sechs Standard-Kennzahlen aus
`tools/analyze_game_log.py`. Erfolgskriterium, VORAB: KEINE Umkehr der
Reihenfolge ueber zwei benachbarte Stufen bei mindestens 3 Partien je Stufe
gilt als "Reihenfolge nicht widerlegt"; eine Umkehr ist bei n = 3 kein Befund,
sondern eine Wiedervorlage fuer 6 weitere Partien auf den zwei Stufen. Diese
Stufe kann keine Elo-Zahl bestaetigen (n zu klein), sie prueft Erleben:
Antwortzeit ertraeglich, kein Zug, der wie ein Fehler des Werkzeugs aussieht
(Ziehsucht am Stapel bei Stand 0, `PREREG_claude_play_interface.md` par.7, ist
ein bekanntes Muster ALLER Stufen mit Netz und keine Stufen-Eigenschaft).

**Stufe 5: Einfrieren des Stufensatzes am Projektende.** Nach der letzten
Generation: Stufe 6 = letzter Champion, Tabelle par.4.1 final, alle Artefakte
im Baum, `README.md` und `docs/` nachgezogen, Elo-Knoten je Stufe im Kopf
dieser Prereg. Danach aendert sich die Leiter nicht mehr.

## par.6 Was NICHT gebaut wird (und warum)

- **Zufallszuege (epsilon-Fehler) und Temperatur-Sampling:** machen den Gegner
  zufaelliger, nicht schwaecher im Sinn eines Spielers; ein Anfaenger lernt an
  Wuerfelzuegen nichts (H5). Die GUI spielt heute ohne Wurzelrauschen
  (par.2.2), das bleibt.
- **Punkte-Handicap:** aendert die Wertung, nicht den Gegner; nicht mit dem
  Elo-Register vergleichbar.
- **Aggressions-Regler als Stufe** (`/api/aggression`, `server.py` ab Zeile 1533,
  Task #28): kein Arm mit p < 0,05 (`PREREG_task28_aggression.md`, Kopf); ein
  Regler ohne belegte Wirkung ist keine Stufe.
- **Sims-Leiter am Champion (60/150/400 wie die toten Presets):** keine Kante
  im Register, Stilwechsel bei flacher Suche belegt (par.2.5). Sims bleiben
  Feinregler in der Stufe "Frei".
- **Lehrer-Modus als Schwierigkeit:** Hilfe fuer den Menschen, eigene Achse
  (par.4.3).

## par.7 Kosten

Rechenlast: Stufe 1 unter 10 min, Stufe 2 unter 5 min, Stufe 2b rund 1-2 h, Stufe 3 je Stufe zwei
Partien (unter 5 min gesamt), alles ANNAHMEN bis zum Artefakt. Bau: Server
(Stufentabelle, Spec je Stufe, Log-Kopf) und Frontend (Auswahl, Hinweis,
Expertenpfad) rund 3-4 h ohne Rechenlast; Einfrieren v24-b07 rund 30 min
(Muster vorhanden). Mensch-Validierung: 21 Partien des Nutzers (7 Stufen mal
3), die einzige Groesse, die Kalenderzeit kostet.

## par.8 Offene Nutzer-Entscheide

1. Stufenzahl und Namen (par.4.1: sechs Stufen plus optional "Meister";
   Vorschlag der Namen: Einsteiger, Anfaenger, Fortgeschritten, Erfahren, Stark,
   Champion, Meister).
2. Zwischenstufe in der Luecke 1100 bis 1283 (v24-b06 aus dem Baum, oder
   v21/v23 aus dem restic-Repo)?
3. Artefakt v24-b07 neu anlegen (am 2026-09-10 geloescht) oder Stufe
   "Erfahren" auf v24-b06 legen?
4. Eingabelaenge 744/755 (par.4.5): Praefix-Kuerzung im Wheel oder Worker-Pfad
   je Stufe, falls Stufe 0 rot ist.
5. Antwortzeit-Schwelle fuer "Meister" (Vorschlag 5 s je Zug, Median).
6. Zeitpunkt: Bau vor oder nach der letzten Generation? Vorschlag: Stufen 0
   bis 3 und der Bau JETZT parallel zum v28-Programm (Konkurrenz um die CPU
   nur in Stufe 1-3; Stufe 2b ist die einzige laengere Messung), Stufe 5 nach
   dem letzten Champion.
7. ~~Heuristik-Stufen: lebender Pfad oder Anker-Artefakt?~~ ENTSCHIEDEN
   2026-09-11 (Nutzer: "aendere das auf die eingefrorenen anker"): die
   Anker-Artefakte `hv1_anchor` und `hv2_generator`.

## par.9 Konsumenten (Rueckwaerts-Pruefung beim Registrieren)

Wer hier ein Ergebnis eintraegt, zieht nach: `README.md:300-303` (Presets),
`server.py` Kopfkommentar Zeile 19-20 (`/api/ai/config` "Schwierigkeit
setzen"), `docs/knobs.md` falls ein Knopf dazukommt, `evaluations/STATUS.md`
Abschnitt 5, und `PREREG_claude_play_interface.md` par.5 (Antwortzeit @400 als
ANNAHME; Stufe 1 hier liefert die Messung).

## par.10 Ergebnisse (leer bis zur ersten Messung)

Nichts gefahren, nichts gebaut (Stand 2026-09-11).
