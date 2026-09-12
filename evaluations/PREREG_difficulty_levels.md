<!-- STATUS: OFFEN | Frage: Welche Schwierigkeitsstufen bietet die GUI beim Spiel gegen das Netz an, und woran ist jede Stufe gemessen? | Beleg: nichts gefahren. Bestand (par.2): Presets im Server sind aus der GUI nicht erreichbar, alle 33 Mensch-Partien liefen @400 (Mensch 24:7:2). Zuschnitt ENTSCHIEDEN 2026-09-11 (par.4.1): vier Stufen, Anfaenger = Anker hv2 @150, Erfahren/Experte/Meister aus dem aktuellen Champion, Meister = Champion wie in der Arena, die zwei darunter mit den Self-Play-Stilmitteln (Sims 100, Wurzelrauschen, Besuchs-Sampling, Weg C); jede Stufe bekommt eine Kante (par.5). EINGETAKTET fuer v29 (Nutzer 2026-09-11, par.8.6): kein Bau und keine Kante vor der v29-Generation. -->

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
sie schlagen koennen, fuer einen Anfaenger eine Wand. Ein Endprodukt braucht
eine Leiter darunter, deren Stufen gemessen sind.

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
  Heuristik-Stufe spielt das EINGEFRORENE Anker-Artefakt `hv2_generator`,
  nicht den lebenden Pfad.**
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
| v25-b01 | ~~`models/frozen_champions/v25-b01/`~~ Artefakt vom Nutzer geloescht 2026-09-11 (Kanten im Register, `run:v25-b01` im restic-Repo) | – | – | – | 1336 [1298, 1380] |
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
Champion; der Nutzer hat den Zuschnitt auf vier Stufen mit dem Champion als
oberster festgelegt (par.4.1), eine Stufe darueber gibt es nicht.

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

- **H1 (die Stufen unter dem Meister sind der Champion im Self-Play-Stil).**
  Nutzer-Entscheid 2026-09-11 (par.8.1): Erfahren, Experte und Meister kommen
  alle aus dem AKTUELLEN Champion; Meister spielt ihn wie die Arena (@400,
  argmax, ohne Wurzelrauschen), die zwei Stufen darunter mit den Stilmitteln
  der Erzeugung. Was diese Stilmittel mit dem Spiel machen, ist am Korpus
  gemessen (par.3.1); was sie an STAERKE kosten, ist es nicht. Erwartung: jede
  Stilstufe verliert gegen die naechsthoehere mit mindestens 60 Prozent.
- **H2 (die Stilmittel ergeben eine Leiter, keine Wuerfelreihe).** Die
  Erzeugung spielt mit denselben Mitteln 12.000 Partien je Generation, und der
  Korpus daraus traegt das Training; das ist ein GEGNER mit anderem Stil, kein
  zufaelliger. Erwartung: die Stilstufen bauen weniger Spalten und weniger
  Punkte als der Meister (Richtung par.3.1), spielen aber ohne erkennbare
  Aussetzer (par.5 Stufe 4).
- **H3 (Sims allein reichen nicht).** @100 gegen @400 am selben Netz war
  33:47 (n.s., `PREREG_search_depth_column_optimum.md` par.2j2); eine Stufe
  aus Sims allein waere vom Meister womoeglich nicht unterscheidbar. Darum
  traegt Experte Sims UND Wurzelrauschen, Erfahren zusaetzlich Sampling und
  Weg C; die Kante entscheidet, ob eine Stufe eine Stufe ist (par.5 Stufe 2).
- **H4 (Anfaenger = hv2 @150 ist die unterste Stufe).** Nutzer-Entscheid
  (par.8.1). hv2 (1100) verliert gegen v21 152:255 (Register, Kante vom
  2026-08-25), und v21 verlieren die Menschen hier nie (12:0:1): fuer die
  Stammspieler ist Anfaenger eine Aufwaermstufe; ob sie fuer Neue reicht, sagt
  Stufe 4.

### par.3.1 Was ueber die Stilmittel gemessen ist (Stand 2026-09-11)

Die Erzeugung (`tools/night_v28_generate.sh:42-58`, gelesen) faehrt drei
Klassen, alle @100 Sims: Traeger mit `--tau-argmax-from-move 1` (argmax ab dem
ersten Halbzug, Wurzelrauschen AN als Default) und `--deviate-prob 1.0` (Weg C:
GENAU EIN Drafting-Zug je Partie weicht ab, `docs/knobs.md` Zeile 170);
Schwarm a mit `--action-temp 2` (Besuchs-Sampling, Temperatur 2) und Weg C;
Schwarm b mit Ausflug, argmax, ohne Wurzelrauschen.

| Stilmittel | gemessene Wirkung | Instrument, n, Einheit | Staerke (Elo) |
| --- | --- | --- | --- |
| Sims 100 statt 400 | 33:47 gegen @400 (n.s.); @25 verliert 11:29 (p = 0,0117) | gepaarte Arena, 80 bzw. 40 Partien, v22-b05 (`PREREG_search_depth_column_optimum.md` par.2j2) | @100: nicht signifikant; @25: signifikant schwaecher |
| Sims 100 + Wurzelrauschen + Weg C (Traeger-Stil) | 0,737 volle Spalten je Seite fuer v25-b01 als Generator; derselbe Spieler @400 argmax in der Arena 0,803 | Tor 2a ex post am Korpus, n = 8.000 Seiten; Tor 2b Arena n = 400 (`docs/generation_loop.md`, `PREREG_v26_window.md` par.8b) | NICHT gemessen |
| Besuchs-Sampling (T = 1) | halbiert den Spaltenbau des Sockels (0,195 gegen 0,4225 bei argmax ab Halbzug 12) | Messung 3-V, `PREREG_search_path_remeasurements.md` Kopf | NICHT gemessen (3-W gestrichen; v25-Arm S3 nie gefahren, `PREREG_v25_window.md` Z. 672) |
| Weg C (eine Abweichung je Partie) | Abzweigstelle aus gemessener Rundenverteilung (`self_play.rs:1569` DEVIATE_ROUND_MASS), Kandidat = bester von 6 zufaelligen nach EINER Netzbewertung (`self_play.rs:1748`) | Bauform, `PREREG_start_position_seeding.md` par.9c/9h/9k | NICHT gemessen |
| Ausflug (Weg B) | zweite Partie ab einer Abzweigstelle | ein Partie-Konstrukt der Erzeugung, KEIN Zug-Stilmittel; fuer einen GUI-Gegner nicht anwendbar (par.4.1) | entfaellt |

Die Spaltenzahlen stammen aus verschiedenen Netzen und Aeren und belegen nur
die RICHTUNG je Instrument; eine Elo-Zahl fuer ein Stilmittel gibt es nicht.
Genau die liefert par.5 Stufe 2.

## par.4 Bauform (registriert VOR dem Bau)

### par.4.1 Stufen-Tabelle (Nutzer-Entscheid 2026-09-11, par.8.1)

| Stufe | Anzeige | Spieler | Suche | Elo-Knoten |
| --- | --- | --- | --- | --- |
| 1 | Anfaenger | Anker-Artefakt `hv2_generator` mit seiner Spec | hv2 @150 | `Heuristik_v2huelle@150` 1100 [1053, 1145] (Identitaet hv2_generator = v2huelle: Stufe 0b) |
| 2 | Erfahren | aktueller Champion mit seiner Spec | @100, Wurzelrauschen AN, Besuchs-Sampling `action-temp 2` ueber die ganze Partie, Weg C (genau eine Abweichung je Partie, Stelle aus DEVIATE_ROUND_MASS/DECAY wie im Self-Play, 6 Kandidaten) | zu messen (Stufe 2) |
| 3 | Experte | aktueller Champion mit seiner Spec | @100, Wurzelrauschen AN, argmax ab Halbzug 1 (Traeger-Stil ohne Weg C) | zu messen (Stufe 2) |
| 4 | Meister | aktueller Champion mit seiner Spec | @400, argmax, ohne Wurzelrauschen (wie Arena und Elo-Register) | 1405 [1361, 1453] heute; am Projektende der letzte Champion |

**Nachziehen bei jedem Champion-Wechsel:** die Stufen 2 bis 4 zeigen auf
`models/champion.txt`; die Kanten aus Stufe 2 gelten fuer den Champion, an dem
sie gemessen wurden. Ob sie fuer den naechsten Champion neu zu messen sind:
Prozessregel par.5 Stufe 2, letzter Absatz.

**Ausflug (Weg B) ist keine Stufe:** er erzeugt eine ZWEITE Partie ab einer
Abzweigstelle (`self_play.rs:1957` `excursion_gate`); ein Gegner in der GUI
spielt eine Partie. Sein einziges Zug-Element, die erzwungene Abweichung am
ersten Halbzug des Ausflugs (`EXCURSION_DEVIATION_MOVE = 1`, `self_play.rs:1873`),
ist Weg C an fester Stelle und damit in Stufe 2 enthalten.

**Notch-Regel, VORAB (fuer den Fall, dass eine Kante H0 liefert):** ist
Experte vom Meister nicht unterscheidbar (par.5 Stufe 2), wird Experte auf
@60 gesetzt (naechste Kerbe: @40); ist Erfahren vom Experten nicht
unterscheidbar, wird Erfahren auf @60 gesetzt (naechste Kerbe: @40, dann
`action-temp 3`). Jede Kerbe ist eine neue Kante; es gibt keine dritte
Kerbe. Bleibt eine Stufe auch danach ununterscheidbar, wird sie gestrichen
(drei Stufen statt vier), nicht "irgendwie" schwaecher gemacht.

### par.4.2 Eine Stufe ist eine Spec-Datei, die GUI und Arena gleich lesen

- Die Stilmittel werden Felder der Spec (`SearchConfig::from_spec_file`,
  `net_mcts.rs:379`): `root_noise` (bool), `action_temp` (f64, 0 = argmax),
  `tau_argmax_from_move`, `deviate_prob`, `deviate_candidates`, dazu `sims`.
  Heute sind Wurzelrauschen und argmax PARAMETER des Suchaufrufs
  (`net_search_with_tree(..., add_root_noise, ...)`, GUI: `py.rs:856` mit
  `false`), Weg C und Temperatur leben in der Self-Play-Schleife
  (`self_play.rs:2649-2700`) und in Env-Knoepfen. Der Umbau zieht sie in die
  Spec, damit `tools/paired_gating.py --spec-a/--spec-b` (Zeilen 248-299) und
  die GUI DENSELBEN Spieler lesen. Bestandsverhalten bleibt byte-gleich, wenn
  die Felder fehlen (Netz-Paritaets-Fixture, Anker-Drift: beide Pflicht nach
  dem Umbau).
- Je Stufe eine Datei `models/levels/<stufe>.spec.json` (englischer
  Dateiname: `beginner`, `advanced`, `expert`, `master`), die die Spec des
  Champions ERWEITERT (Champion-Knoepfe unveraendert, Stilfelder dazu). Der
  Server laedt die Stufen-Spec beim Stufenwechsel (Mechanismus wie
  `_apply_champion_spec_env`, `server.py:245-272`, mit Rueckstellung der
  Felder, die die neue Spec nicht traegt; Voraussetzung: Env wird zur Suchzeit
  gelesen, Stufe 0d prueft es fuer den Drafting-Pfad).
- Zufall in der GUI: der Such-RNG ist heute je Zug aus Seed und Zugfolge
  abgeleitet (`py.rs:854`, `derive_search_seed`); Rauschen, Sampling und die
  Weg-C-Ziehung haengen an DEMSELBEN Strom, damit "gespielt = gemessen"
  (Stufe 3) pruefbar bleibt und eine Partie aus dem Log reproduzierbar ist.
- `/api/game/new` und `/api/ai/config` nehmen `difficulty` als Stufennamen;
  `model`/`sims` bleiben als Expertenpfad (Stufe "Frei") erhalten. Der Log-Kopf
  traegt `difficulty` und den Pfad der Stufen-Spec; ohne beides ist eine
  Mensch-Partie keiner Stufe zuzuordnen (par.2.4 liess sich nur auswerten,
  weil alle 33 bei 400 liefen).
- Anfaenger: die Server-Heuristik spielt hv2 mit der Spec des Artefakts und
  wird per Drift-Pruefung (Skill `mosaic-anchor-invariance`, 22 s je Lauf) als
  zuggleich mit `hv2_generator` belegt; sonst laeuft der Zug ueber den
  Artefakt-Worker (`tools/frozen_champion_worker.py`). Bau-Frage nach Stufe 0;
  der Spieler ist entschieden (par.8.7).

### par.4.3 Frontend

- Das Zahlenfeld `ng-sims` weicht einer Auswahl mit den vier Stufennamen und
  je Stufe einem Hinweis "Antwortzeit ca. X s je Zug" (X aus par.5 Stufe 1,
  nicht geschaetzt). Stufe "Frei" blendet die heutigen Felder Modell/Sims ein.
- Die Stufe ist im Spielfenster sichtbar (heute nur `ai_model`/`ai_sims`,
  `server.py:704-705`).
- Keine Aenderung an Lehrer-Modus (`teacher_level`), Tipp und Coach: Hilfe fuer
  den Menschen ist eine eigene Achse.

### par.4.4 Was durch den Zuschnitt WEGFAELLT

- **Die Eingabelaengen-Frage 744/755** (erste Fassung par.4.5): alle
  Netz-Stufen sind derselbe Champion, Anfaenger ist netzlos. Ein Champion-Wechsel
  auf ein 755er-Modell zieht alle drei Netz-Stufen mit. Kein Praefix-Kuerzen,
  kein Worker-Pfad je Stufe.
- **Einfrieren aelterer Champions als Stufen** (v24-b07, v25-b01): entfaellt;
  die Artefakte bleiben, was sie sind (Elo-Kader), keine GUI-Rolle.
- **Einsteiger-Stufe hv1 @40** und die zugehoerige Kante: entfaellt
  (Nutzer-Zuschnitt: vier Stufen, unterste hv2 @150).
- **Stufe ueber dem Meister (@1200)**: entfaellt; Meister IST der Champion, wie
  er gemessen ist.

## par.5 Messgroessen und Stufen (VOR dem Bau festgelegt)

**Stufe 0: Inventur, keine Rechenlast.** (a) Artefakt `hv2_generator`
vollstaendig (Spec, Manifest, Golden-Probe, Wheel)? (b) Identitaet
hv2_generator = Knoten `Heuristik_v2huelle` (Manifest gegen den Kommentar der
Kante vom 2026-08-25 in `elo_history.csv`). (c) Welche Heuristik-Variante
spielt `ai_step_json` heute, und mit welchen Knoepfen? (d) Liest der
Drafting-Pfad der GUI die Knoepfe zur Suchzeit? (e) Wo genau sitzen
Wurzelrauschen, `action_temp`, `tau_argmax_from_move`, Weg C im Code, und
welche davon erreicht ein Einzelzug-Aufruf heute NICHT (Umbau-Liste fuer
par.4.2). Ergebnis: Tabelle in par.10, keine Zahl ohne Pruefstelle.

**Stufe 1: Antwortzeit je Stufe, gemessen.** Nach dem Umbau je Stufe 2
Partien Stufe gegen sich selbst ueber den GUI-Pfad (Seeds 20260950 und
20260951, ein Prozess, 11 Threads wie im Spielbetrieb), aufgezeichnet je Zug:
Wanduhr in s. Kennzahl: Median und 90. Perzentil der Sekunden je Zug,
Grundmenge Drafting-Zuege beider Seiten, Einheit s je Zug. Artefakt
`evaluations/artifacts/difficulty_latency_<datum>.json` mit `laufzeit`-Block.
Exklusiv. Kosten: 8 Partien, unter 5 min (ANNAHME aus 6,98 s je
Self-Play-Partie @400, `docs/measured_runtimes.md`; dort ueber parallele
Partien gemittelt, hier eine Partie am Stueck, darum wird gemessen).

**Stufe 2: Die drei Kanten der Leiter.** Gepaarte Arena mit
`tools/paired_gating.py --log-games --block-size 5`, je Kante 100 Paare
(200 Partien), Spec je Seite aus `models/levels/`:

| Kante | Seed | Entscheidungsregel (VORAB) |
| --- | --- | --- |
| Meister gegen Experte | 20260952 | Meister gewinnt mindestens 120 von 200 (Vorzeichentest auf Paardifferenzen p < 0,05), sonst Notch-Regel par.4.1 |
| Experte gegen Erfahren | 20260953 | Experte gewinnt mindestens 120 von 200, sonst Notch-Regel |
| Erfahren gegen Anfaenger (hv2 @150, Artefakt-Referee `tools/frozen_referee_match.py`, festes n = 200) | 20260954 | Erfahren gewinnt mindestens 120 von 200; verliert Erfahren, ist die Leiter unten gebrochen und der Zuschnitt geht an den Nutzer zurueck |

Jede Kante geht als Knoten ins Elo-Register (`<champion>@100rn`,
`<champion>@100rn-t2-wegc`, Namensschema in Stufe 0 festzulegen), damit die
Stufen eine Leiterposition mit Konfidenzintervall tragen. Aus den Logs je
Seite die sechs Standard-Kennzahlen (CLAUDE.md), zusaetzlich je Stufe: volle
Spalten je Seite (`tools/probes/arena_column_probe.py`) und Punkte je
Wertungsplatte (`tools/plate_points_from_arena.py`), weil H2 genau diese
Richtung behauptet. Kosten: 600 Partien, davon 400 mit Sims 100 bis 400,
unter 1 h (ANNAHME; Tor 1 mit 400 Partien @400 ist gemessen, Wert in
`docs/measured_runtimes.md`).

Prozessregel fuer Champion-Wechsel (VORAB): die Kanten Meister/Experte und
Experte/Erfahren werden NICHT je Generation neu gemessen (Praezedenz
`PREREG_search_depth_column_optimum.md` par.8c: Neumessung nur bei
Aera-Wechseln). Am Projektende, mit dem letzten Champion, werden alle drei
Kanten EINMAL final gefahren (Stufe 5).

**Stufe 3: Gespielt = gemessen.** Je Stufe eine Partie ueber den GUI-Pfad und
dieselbe Partie ueber den Arena-Pfad (gleicher Seed, gleiche Stufen-Spec):
Zugfolge byte-gleich (Muster: Netz-Paritaets-Fixture, Promotions-Checkliste
5d). Rot heisst: die Stufe spielt in der GUI einen anderen Spieler als den,
dessen Kante sie traegt. Kein Bau der Auswahl, bevor jede Stufe gruen ist.

**Stufe 4: Mensch-Validierung (klein, qualitativ, markiert).** Der Nutzer
spielt je Stufe mindestens 3 Partien (Log-Kopf mit `difficulty`). Kennzahlen
je Stufe: Siege, Punkte, Margin, plus die sechs Standard-Kennzahlen aus
`tools/analyze_game_log.py` (Endstand aus den 🏆-Zeilen, par.2.4).
Erfolgskriterium, VORAB: keine Umkehr der Reihenfolge ueber zwei benachbarte
Stufen bei mindestens 3 Partien je Stufe gilt als "Reihenfolge nicht
widerlegt"; eine Umkehr ist bei n = 3 kein Befund, sondern eine Wiedervorlage
fuer 6 weitere Partien auf den zwei Stufen. Zusaetzlich je Stufe die Frage
an den Spieler: ein Zug, der wie ein Aussetzer aussah (H2)? Die Ziehsucht am
Stapel bei Stand 0 (`PREREG_claude_play_interface.md` par.7) ist ein bekanntes
Muster ALLER Netz-Stufen und zaehlt nicht.

**Stufe 5: Einfrieren des Stufensatzes am Projektende.** Nach der letzten
Generation: Meister = letzter Champion, die drei Kanten final, Tabelle par.4.1
mit Elo-Knoten je Stufe, `README.md` und `docs/` nachgezogen, Kopf dieser
Prereg auf ENTSCHIEDEN. Danach aendert sich die Leiter nicht mehr.

## par.6 Was NICHT gebaut wird (und warum)

- **Zufallszuege auf der Aktionsmenge (epsilon-Fehler) und Punkte-Handicap:**
  ein Gegner, der absichtlich Unsinn spielt, lehrt falsche Muster. Das Rauschen
  der Stilstufen sitzt IN der Suche (Wurzel-Prior, Besuchsverteilung,
  netzbewertete Weg-C-Kandidaten), genau wie in der Erzeugung, aus der der
  Champion gelernt hat; ein Weg-C-Kandidat ist der beste von sechs nach
  Netzbewertung, kein Wuerfelzug.
- **Aggressions-Regler als Stufe** (`/api/aggression`, `server.py` ab Zeile
  1533, Task #28): kein Arm mit p < 0,05 (`PREREG_task28_aggression.md`, Kopf).
- **Aeltere Champions als Stufen:** vom Nutzer verworfen (par.8.1); sie
  wuerden mit jedem Generationswechsel und jeder Eingabelaengen-Aenderung
  Pflege kosten.
- **Sims allein als Stufe** (die toten Presets 60/150/400): @100 gegen @400
  war n.s. (par.3.1); ohne Stilmittel ist es womoeglich keine Stufe.
- **Lehrer-Modus als Schwierigkeit:** eigene Achse (par.4.3).

## par.7 Kosten

Rechenlast: Stufe 1 unter 5 min, Stufe 2 unter 1 h, Stufe 3 acht Partien;
alles ANNAHMEN bis zum Artefakt. Bau: Spec-Felder fuer die Stilmittel und ihr
Durchgriff in Einzelzug-Aufruf und Arena (Rust, mit Paritaets-Fixture und
Anker-Drift danach) rund 3-4 h; Server (Stufentabelle, Stufen-Spec, Log-Kopf)
und Frontend (Auswahl, Hinweis, Expertenpfad) rund 2-3 h; alles ohne
Rechenlast ausser Wheel-Build. Mensch-Validierung: 12 Partien des Nutzers
(4 Stufen mal 3), die einzige Groesse, die Kalenderzeit kostet.

## par.8 Nutzer-Entscheide

1. ~~Stufenzahl, Namen, Spieler~~ ENTSCHIEDEN 2026-09-11 (Nutzer: "anfaenger
   hv2@150, erfahren, experte, meister (= aktueller champ). die stufe von
   erfahren bis meister sollen vom aktuellen champ kommen. sprich hier dann
   wurzelrauschen, wegc, exkurs whatever einfuehren"): vier Stufen nach
   par.4.1. Die konkrete Zuordnung der Stilmittel auf Erfahren und Experte
   (par.4.1) ist Vorschlag des Koordinators, die Kanten pruefen sie.
2. ~~Zwischenstufe 1100-1283~~ entfaellt mit 1.
3. ~~Artefakt v24-b07 neu anlegen~~ entfaellt mit 1.
4. ~~Eingabelaenge 744/755~~ entfaellt mit 1 (par.4.4).
5. ~~Antwortzeit-Schwelle fuer eine Stufe ueber dem Meister~~ entfaellt mit 1.
6. ~~Zeitpunkt~~ ENTSCHIEDEN 2026-09-11 (Nutzer: "nein. kannst fuer v29
   eintakten"): NICHT parallel zum v28-Programm. Eintaktung: Stufe 0 (Inventur)
   und der Bau (par.4.2/4.3, Wheel mit Paritaets-Fixture und Anker-Drift)
   waehrend der v29-Erzeugung, weil sie keine Messmaschine brauchen ausser dem
   Wheel-Build; Stufen 1 bis 3 (Antwortzeit, drei Kanten, gespielt = gemessen)
   im CPU-freien Fenster NACH Tor 1 der v29-Generation, mit dem dann
   amtierenden Champion als Meister; Stufe 4 (Mensch) danach; Stufe 5 mit dem
   letzten Champion. Ist v29 die letzte Generation, fallen Stufe 2 und 5
   zusammen.
7. ~~Heuristik-Stufe: lebender Pfad oder Anker-Artefakt?~~ ENTSCHIEDEN
   2026-09-11 (Nutzer: "aendere das auf die eingefrorenen anker"): das
   Anker-Artefakt `hv2_generator`.
8. Offen: Namensschema der Elo-Knoten fuer die Stilstufen (Vorschlag in
   par.5 Stufe 2) und ob die Kanten je Champion-Wechsel oder nur am Ende
   gefahren werden (Vorschlag: nur am Ende, par.5 Stufe 2 letzter Absatz).

## par.9 Konsumenten (Rueckwaerts-Pruefung beim Registrieren)

Wer hier ein Ergebnis eintraegt, zieht nach: `README.md:300-303` (Presets),
`server.py` Kopfkommentar Zeile 19-20 (`/api/ai/config` "Schwierigkeit
setzen"), `docs/knobs.md` falls ein Knopf dazukommt, `evaluations/STATUS.md`
Abschnitt 5, und `PREREG_claude_play_interface.md` par.5 (Antwortzeit @400 als
ANNAHME; Stufe 1 hier liefert die Messung).

## par.10 Ergebnisse (leer bis zur ersten Messung)

Nichts gefahren, nichts gebaut (Stand 2026-09-11).

## Nachtrag 2026-09-12 (Neuverankerung der Leiter, Segment 2)

Alle Elo-Zahlen in par.2.3, par.2.5 und par.4 stammen aus dem ALT-REGISTER (Segment 1,
Anker `Heuristik_hv1_anchor`), das am 2026-09-12 nach `archive/elo_history_pre_phantomfix.csv`
verschoben wurde (`PREREG_code_cleanup_closeout.md` par.7a: Phantom-Fix A2 bewegte den
Anker, Nutzer-Entscheid "setz den anker neu"). Seither gilt Segment 2 mit dem Anker
`models/frozen_heuristics/hv1_anchor_v2` (`Heuristik_hv1_anchor_v2@150` = 1000 fix); Kanten
ueber die Grenze werden nie gemischt. Folgen fuer diese Prereg:

- Die Zeile `hv1_anchor` in par.2.3 bezeichnet den Segment-1-Anker; der Spieler der Stufen
  bleibt unveraendert `hv2_generator`. **Sein Elo-Knoten 1100 [1053, 1145] ist im Segment 2
  UNGEMESSEN**; die Stufe-0b-Messung (Identitaet und Kante) laeuft im neuen Segment.
- Stufe 4 (Meister) zeigt auf `models/champion.txt`; die Zahl 1405 ist Segment 1. Seit der
  Promotion 2026-09-12 ist der Champion v28-b02 mit Segment-2-Elo 1299 [1244, 1359] aus 1.330
  Partien (Anker 126:24, drei Nachbar-Seeds gegen v27-b01, Champion-2 101:49; par.7a der
  Cleanup-Prereg). Stufe 1 (hv2@150) bleibt im Segment 2 ungemessen, bis Stufe 0b laeuft.
- Zahlen ab hier nur aus `evaluations/elo_history.csv` (Segment 2) lesen; par.2.5 ist
  historisch und wird nicht umgeschrieben.

