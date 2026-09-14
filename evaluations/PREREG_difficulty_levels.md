<!-- STATUS: OFFEN | Frage: Welche Schwierigkeitsstufen bietet die GUI beim Spiel gegen das Netz an, und woran ist jede Stufe gemessen? | Beleg: **GANZE LEITER auf v30 VERTAGT** (par.13, Nutzer 2026-09-14: sonst wird auf ein Modell geeicht, das zum Schluss nicht spielt). Zuschnitt ENTSCHIEDEN und gueltig (par.4.1/4.1a): vier Stufen, Anfaenger hv3 @150, die drei oberen aus dem dann amtierenden Champion. Gebaut und bestandserhaltend liegen geblieben: Schritte 1, 2 und 1b des Umbaus Weg A plus models/levels/beginner.spec.json. Bestand par.2: Presets sind aus der GUI unerreichbar, alle 33 Mensch-Partien liefen @400. -->

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
  Heuristik-Stufe spielt ein EINGEFRORENES Artefakt, nicht den lebenden Pfad.**
  Genannt war zunaechst `hv2_generator`; seit dem Entscheid 2026-09-13 ist es
  `hv3_generator` (par.4.1a: hv2 fehlt der Phantom-Fix A2 und ist nicht
  nachbaubar).
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
gemessen (`sims_a,sims_b`: 43 Zeilen 400/400, 11 Zeilen 400/150). **UEBERHOLT
seit 2026-09-13:** der Satz "fuer keinen Champion gibt es eine Elo-Kante bei
anderer Sim-Zahl" galt bis zur Sims-Kurve; seither traegt das Register die
Knoten `v28-b02@100` (1298), `@200` (1289) und `@600` (1389) gegen `@400`
(1394), je n=150 ohne Frueh-Stopp, plus die zweite Aufhaengung von @100 gegen
`v22-b05_live@25` (172:28, n=200). Eine Sims-Leiter ist damit fuer den
AMTIERENDEN Champion gemessen. Was zu Sims gemessen ist, steht in
`PREREG_search_depth_column_optimum.md`: dasselbe Netz (v22-b05) @25 gegen
@400 verliert 11:29 (SPRT H0, p = 0,0117), @100 gegen @400 33:47 (n.s.); am
Champion v28-b02 verliert @100 gegen @400 45:105 und @200 53:97, waehrend
@600 Gleichstand haelt. Die flache Suche baut im SELBSTSPIEL MEHR Spalten
(par.8e: 1,0975 bei 100 gegen 0,8950 bei 400 je Seite), in der ARENA gegen
eine tiefere Suche dagegen weniger. Eine Sims-Leiter aendert also weiter den
STIL des Gegners, nicht nur seine Staerke -- das bleibt der tragende Punkt.

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
| 1 | Anfaenger | Artefakt **`hv3_generator`** mit seiner Spec (hv2 GESTRICHEN, s. par.4.1a) | **hv3 @150** (Nutzer 2026-09-13, par.12c) | `Heuristik_hv3_generator@150` 972 [935, 1011], Segment 2 |
| 2 | Erfahren | aktueller Champion mit seiner Spec | @100, Wurzelrauschen AN, Besuchs-Sampling `action-temp 2` ueber die ganze Partie, Weg C (genau eine Abweichung je Partie, Stelle aus DEVIATE_ROUND_MASS/DECAY wie im Self-Play, 6 Kandidaten) | zu messen (Stufe 2) |
| 3 | Experte | aktueller Champion mit seiner Spec | @100, Wurzelrauschen AN, argmax ab Halbzug 1 (Traeger-Stil ohne Weg C) | zu messen (Stufe 2) |
| 4 | Meister | aktueller Champion mit seiner Spec | @400, argmax, ohne Wurzelrauschen (wie Arena und Elo-Register) | 1405 [1361, 1453] heute; am Projektende der letzte Champion |

### par.4.1a hv2 IST KEINE OPTION MEHR (Nutzer-Entscheid 2026-09-13)

Woertlich: **"Hv2 ist keine Option mehr. Da fehlt der fix. Deshalb hv3."** Gemeint ist der
Phantom-Fix A2: das Artefakt `hv2_generator` wurde am 2026-08-26 eingefroren, also VOR dem Fix,
und sein Quellzweig ist seither entfernt -- es ist nicht nachbaubar und liegt in einer anderen
Aera als der heutige Motor. `hv3_generator` ist genau dafuer gebaut worden: dasselbe hv2-Rezept
auf dem heutigen Motor MIT A2, eingefroren 2026-09-12.

Der Wechsel kostet nichts an Staerke und raeumt zwei Probleme ab:

- **Die Aera stimmt wieder.** Eine Kante gegen hv2 waere cross-aera; der Anker traegt A2, hv2
  nicht. hv3 gegen hv4 lief 73:77, gegen hv2 78:72 (je Deckel): der Fix bewegt die Staerke nicht
  messbar, die Knoten liegen bei 972 (hv3) und 983 (hv2), beide mit ueberlappenden Intervallen.
- **Die Identitaetsfrage entfaellt.** Stufe 0b musste klaeren, ob `hv2_generator` derselbe
  Spieler ist wie der Alt-Knoten `Heuristik_v2huelle`. Das war nicht beweisbar, weil hv2 mit
  `git_dirty: true` eingefroren wurde (par.12 Punkt b). hv3 hat einen sauberen Einfrierstand.

**Folge:** Stufe 0b aus par.5 entfaellt. Der Elo-Knoten der Anfaengerstufe ist
`Heuristik_hv3_generator@150` = 972 [935, 1011] (Segment 2, 400 Partien), nicht der Alt-Wert
1100 aus Segment 1.

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
  `net_mcts.rs:379`): `root_noise` (bool), `action_temp` (ganze Zahl 0..2, MODUS -- berichtigt 2026-09-13, par.12c: 0 heisst rohe Besuchszahlen, nicht argmax),
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
- Anfaenger: die Server-Heuristik spielt **hv3** mit der Spec des Artefakts und
  wird per Drift-Pruefung (Skill `mosaic-anchor-invariance`, 22 s je Lauf) als
  zuggleich mit `hv3_generator` belegt; sonst laeuft der Zug ueber den
  Artefakt-Worker (`tools/frozen_champion_worker.py`). Der Spieler ist
  entschieden (par.8.7, auf hv3 gestellt 2026-09-13 in par.4.1a).
  **Stufe 0 hat dazu den Blocker gefunden** (par.12 Punkt c): der
  GUI-Heuristik-Pfad ist auf `HeuristicVariant::Hv1` hart verdrahtet und nimmt
  die Variante nicht entgegen. Der Durchstich ist Punkt 1 der Umbau-Liste.

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
`models/frozen_heuristics/hv4_anchor` (`Heuristik_hv4_anchor@150` = 1000 fix); Kanten
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

**Nachtrag 2026-09-12, 16:20 (Segment 2, Stufe 1 gemessen):** die Anfaenger-Stufe hv2_generator@150
(c_puct 0,3) gegen den Anker hv4_anchor@150: **77:73 aus 150 Partien** (drei Bloecke a 50 ohne
Frueh-Stopp, p 0,81; `PREREG_code_cleanup_closeout.md` par.7a). Elo-Knoten `Heuristik_hv2_generator@150`
972 [921, 1022], also gleich stark wie der Anker. Die Zahl 1100 aus par.2.5 galt fuer
`Heuristik_v2huelle` im Segment 1 und ist fuer die Leiter der Stufen NICHT mehr zu verwenden. Damit
liegt die Anfaenger-Stufe rund 360 Elo unter dem Champion (Endstand 17:10: v28-b02 1344 [1298, 1399], hv2 987 [941, 1033]); die Stufen
2 und 3 (Champion mit Self-Play-Stilmitteln) muessen diesen Abstand fuellen (Stufe 2 der Prereg).

**Nachtrag 2026-09-12, 21:50 (hv3 verfuegbar):** fuer die Anfaenger-Stufe steht jetzt auch
`models/frozen_heuristics/hv3_generator` (Huellen-Lehrer MIT Phantom-Fix, Motor der heutigen
Aera) bereit; gegen hv4-Anker 73:77 und gegen hv2 78:72, Elo 992 [948, 1035], also gleich stark
wie hv2 (978). Empfehlung: Anfaenger = hv3, weil es auf dem Motor der Champions spielt (kein
Cross-Aera-Wheel im Spielbetrieb); Nutzer-Entscheid bei Stufe 2.


**Nachtrag 2026-09-13, 02:50 (Identitaet des GUI-Gegners "Heuristik"; Nutzer: "das kannst dir selbst
beantworten mit den schwierigkeitsgraden"):** der Portable-Build-Audit
(`evaluations/review/portable_build_audit_2026-09-13.md`, Luecke 3) fand, dass Partien gegen die
Server-Heuristik im Segment-2-Register ungewertet sind (`server.py` Z.768 uebergibt "Heuristik",
kein solcher Knoten, `ANCHOR_ALIASES` leer). Geprueft: das Preset "easy" spielt heute die LEBENDE
hv1-Heuristik mit 60 Sims (`server.py` Z.296) und der Netz-Konstante c_puct 1,5 (Z.109); kein
Register-Knoten hat diese Einstellung (Anker: hv4_anchor @150, c_puct 0,3). Ein Alias
"Heuristik" -> hv4_anchor waere deshalb eine ungeprueft gleichgesetzte Identitaet, und er unterbleibt.

**Antwort ueber die Stufen (Koordinator-Entscheid nach der Empfehlung im Nachtrag 21:50, Nutzer kann
ihn kippen):** die Anfaenger-Stufe IST der Gegner "Heuristik" der GUI. Sie spielt das eingefrorene
Artefakt `hv3_generator` (Huellen-Lehrer auf dem Motor der Champions, Spec `models/hv3.spec.json`
bzw. die Artefakt-Spec) mit 150 Sims und c_puct 0,3, und der Server uebergibt als Identitaet den
Knotennamen `Heuristik_hv3_generator` mit sims 150: Knoten vorhanden (978 [938, 1016] am
2026-09-13), keine Aliase noetig. Das Preset "easy" (hv1 @60) faellt weg (par.4.4). Bis der
Stufen-Bau (AGENTEN-AUFTRAG unten, Plan Nr. 22) durch ist, bleibt der heutige Heuristik-Gegner
ungewertet, und das ist richtig so. Die Anker-Drift ist davon unberuehrt: der Heuristik-Suchpfad
ruft `determinize_dome_pool` nicht (Aufrufer nur `net_mcts.rs`, `round_transition_deep.rs`,
`self_play.rs`-Diagnosen; Grep 2026-09-13), der P.10-Fix bewegt den Anker also nicht (Erwartung,
Drift-Pruefung folgt beim Wheel-Bau).

## AGENTEN-AUFTRAG (Stand 2026-09-13, fuer eine autonome Abarbeitung durch einen Opus-Agenten)

### 1. Ziel und Verdikt-Regel

Zu beantworten ist, welche Schwierigkeitsstufen die GUI anbietet und woran jede Stufe gemessen
ist. Der Zuschnitt ist ENTSCHIEDEN (**par.4.1**, Nutzer 2026-09-11): vier Stufen -- Anfaenger =
eingefrorenes Heuristik-Artefakt @150, Erfahren/Experte/Meister aus dem AKTUELLEN Champion,
Meister wie in der Arena (@400, argmax, ohne Wurzelrauschen), die zwei darunter mit den
Self-Play-Stilmitteln. Die Verdikt-Regel je Kante steht in **par.5 Stufe 2**: der staerkere Arm
muss mindestens 120 von 200 Partien gewinnen (Vorzeichentest auf Paardifferenzen, p < 0,05);
sonst greift die **Notch-Regel par.4.1** -- Experte auf @60 (naechste Kerbe @40), Erfahren auf
@60 (naechste Kerbe @40, dann `action-temp 3`); jede Kerbe ist eine neue Kante, es gibt keine
dritte Kerbe, und bleibt eine Stufe ununterscheidbar, wird sie GESTRICHEN (drei Stufen statt
vier), nicht "irgendwie" schwaecher gemacht. Verliert Erfahren gegen Anfaenger, ist die Leiter
unten gebrochen und der Zuschnitt geht an den Nutzer zurueck. **Stufe 3 ist ein hartes Tor:**
keine Auswahl im Frontend, bevor jede Stufe "gespielt = gemessen" gruen ist.

### 2. Voraussetzungen

- **EINGETAKTET fuer v29** (par.8 Punkt 6, Nutzer 2026-09-11): Stufe 0 (Inventur) und der Bau
  WAEHREND der v29-Erzeugung, weil sie keine Messmaschine brauchen ausser dem Wheel-Build;
  Stufen 1 bis 3 im CPU-freien Fenster NACH Tor 1 der v29-Generation, mit dem dann amtierenden
  Champion als Meister; Stufe 4 (Mensch) danach; Stufe 5 mit dem letzten Champion.
- **Der Wheel-Bau fuer die Leiter ist eine Engine-Aenderung** (`PREREG_v29_window.md` par.7
  Punkt 1): Anker-Drift und Paritaets-Fixture vor jedem weiteren Messlauf, und NICHT waehrend
  Waechter oder Kette (`PREREG_v29_window.md` par.4 Punkt 6).
- **Maschine frei** fuer Stufen 1-3 (Prozessliste `0`); exklusiv.
- **Dateien und Artefakte:** `models/frozen_heuristics/hv2_generator` und
  `models/frozen_heuristics/hv3_generator` (beide vorhanden), `models/champion.txt`,
  Champion-Artefakt `models/frozen_champions/<champion>/spec.json`; neu anzulegen je Stufe
  `models/levels/<stufe>.spec.json` (englische Dateinamen: `beginner`, `advanced`, `expert`,
  `master`).
- **Elo-Stand, der gilt:** NUR Segment 2 (`evaluations/elo_history.csv`, Anker
  `Heuristik_hv4_anchor@150` = 1000 fix). Die Zahlen in par.2.3/par.2.5/par.4 stammen aus dem
  ALT-Register (Segment 1) und sind fuer die Leiter NICHT zu verwenden (Nachtrag 2026-09-12).
  Gemessen im Segment 2 (Stand 2026-09-13, 10:30, nach den vier Kanten der Sims-Kurve, 40
  Match-Zeilen): hv2_generator@150 = 983, hv3_generator@150 = **972**, Champion v28-b02@400 =
  **1394**, also rund **420 Elo Abstand** zum Anfaenger-Kandidaten hv3, den die Stufen 2 und 3
  fuellen muessen. (Vorher stand hier 370 auf dem Stand von 01:00 mit Champion 1353 und hv3 978;
  der Champion ist durch die drei neuen Sim-Knoten unter seinem 400er-Knoten gestiegen, nicht
  durch eine neue Staerkemessung.) Zwischenstufen des Champions selbst stehen jetzt ebenfalls im
  Register und liegen genau in der Luecke: v28-b02@100 = 1298, @200 = 1289.

### 3. Schritte

**P1 -- Stufe 0: Inventur (keine Rechenlast, par.5)**

1. Fuenf Punkte abarbeiten und als Tabelle in par.10 registrieren, jede Zeile mit Pruefstelle
   (`datei:zeile`): (a) Artefakt des Anfaenger-Spielers vollstaendig (Spec, Manifest,
   Golden-Probe, Wheel)? (b) Identitaet `hv2_generator` = Elo-Knoten `Heuristik_v2huelle`
   (Manifest gegen den Kommentar der Kante vom 2026-08-25 im Alt-Register) -- Stufe 0b;
   (c) welche Heuristik-Variante spielt `ai_step_json` (`engine/src/py.rs:524`) heute, mit
   welchen Knoepfen? (d) liest der DRAFTING-Pfad der GUI die Knoepfe zur Suchzeit (fuer den
   Tiling-Schritt ist `SearchConfig::from_env` in `py.rs:969` belegt, fuer Drafting ANNAHME)?
   (e) wo genau sitzen Wurzelrauschen, `action_temp`, `tau_argmax_from_move` und Weg C im Code
   (`net_search_with_tree(..., add_root_noise, ...)`, GUI `py.rs:856` mit `false`;
   `self_play.rs:2649-2700`), und welche davon erreicht ein Einzelzug-Aufruf heute NICHT --
   das ist die Umbau-Liste fuer par.4.2. **Keine Zahl ohne Pruefstelle.**

**P2 -- Bau (par.4.2 / par.4.3, rund 3-4 h Rust plus 2-3 h Server/Frontend, ANNAHME)**

2. **Stilmittel werden Spec-Felder** (`SearchConfig::from_spec_file`, `engine/src/net_mcts.rs:379`):
   `root_noise` (bool), `action_temp` (ganze Zahl 0..2, MODUS -- berichtigt 2026-09-13, par.12c: 0 heisst rohe Besuchszahlen, nicht argmax), `tau_argmax_from_move`, `deviate_prob`,
   `deviate_candidates`, dazu `sims`. Alle OPTIONAL, damit die eingefrorenen Specs weiter laden
   (Muster `dead_cell_w`, `round_est_c`); fehlen sie, ist das Verhalten byte-gleich zum Bestand.
   Ziel: `tools/paired_gating.py --spec-a/--spec-b` und die GUI lesen DENSELBEN Spieler.
3. **Tore des Rust-Baus, Reihenfolge Bau -> Tore -> Messung:**

   ```
   $env:PATH = "$(python -c 'import sys,os;print(os.path.dirname(sys.executable))');" + $env:PATH
   cd engine; cargo test --release --lib            # gemessen 80-85 s
   cargo test --release --no-run                    # examples/benches, gemessen 33 s
   python -m maturin build --release                # gemessen 26-34 s
   python -m pip install --force-reinstall --no-deps engine/target/wheels/mosaic_rust-0.1.0-cp314-cp314-win_amd64.whl
   python -X utf8 -u tools/verify_frozen_heuristic.py --artifact-dir models/frozen_heuristics/hv4_anchor --out evaluations/artifacts/anchor_drift_live_wheel_<datum>_levels.json
   python -X utf8 -u tools/verify_frozen_heuristic.py --artifact-dir models/frozen_heuristics/hv4_anchor --venv --out evaluations/artifacts/anchor_conservation_artifact_wheel_<datum>_levels.json
   python -X utf8 tools/generate_knob_docs.py
   python -X utf8 tools/check_conventions.py
   ```

   **Netz-Paritaets-Fixture des Champions muss UNVERAENDERT bleiben** (Felder fehlen = Bestand).
   Anker-Drift muss gruen bleiben (die Heuristik liest die Stilfelder nicht).
4. **Stufen-Specs** anlegen: je Datei erweitert die Champion-Spec um die Stilfelder aus par.4.1
   (Erfahren: @100, `root_noise` an, `action_temp 2` ueber die ganze Partie, Weg C mit 6
   Kandidaten; Experte: @100, `root_noise` an, argmax ab Halbzug 1, kein Weg C; Meister: @400,
   argmax, kein Wurzelrauschen; Anfaenger: Artefakt-Spec des Heuristik-Artefakts, @150,
   c_puct 0,3).
5. **Server und Frontend** (par.4.2/4.3): `/api/game/new` und `/api/ai/config` nehmen
   `difficulty` als Stufennamen, `model`/`sims` bleiben als Expertenpfad "Frei"; der Server laedt
   die Stufen-Spec beim Stufenwechsel (Mechanismus wie `_apply_champion_spec_env`,
   `server.py:245-272`, MIT Rueckstellung der Felder, die die neue Spec nicht traegt);
   **der Log-Kopf traegt `difficulty` und den Pfad der Stufen-Spec** (ohne beides ist eine
   Mensch-Partie keiner Stufe zuzuordnen); das Zahlenfeld `ng-sims` weicht einer Auswahl mit den
   vier Namen und je Stufe dem Hinweis "Antwortzeit ca. X s je Zug" (X aus Stufe 1, nicht
   geschaetzt); die Stufe ist im Spielfenster sichtbar. Lehrer-Modus, Tipp und Coach bleiben
   unberuehrt.

**P3 -- Stufe 1: Antwortzeit je Stufe, gemessen (par.5)**

6. Je Stufe 2 Partien Stufe gegen sich selbst ueber den GUI-Pfad, Seeds 20260950 und 20260951,
   ein Prozess, 11 Threads wie im Spielbetrieb; je Zug die Wanduhr aufzeichnen. Kennzahl: Median
   und 90. Perzentil der Sekunden je Zug, Grundmenge Drafting-Zuege beider Seiten, Einheit s je
   Zug. Artefakt `evaluations/artifacts/difficulty_latency_<datum>.json` mit `laufzeit`-Block.
   Exklusiv. Kosten: 8 Partien, unter 5 min (ANNAHME aus 6,98 s je Self-Play-Partie @400,
   `docs/measured_runtimes.md`; dort ueber parallele Partien gemittelt, hier eine Partie am
   Stueck -- darum wird gemessen).

**P4 -- Stufe 2: die drei Kanten (par.5)**

7. Je Kante 100 Paare = 200 Partien, Blockgroesse 5, Logs, Spec je Seite aus `models/levels/`:

   ```
   python -X utf8 -u tools/paired_gating.py \
     --model-a models/alphazero_<champion>.onnx --spec-a models/levels/master.spec.json \
     --model-b models/alphazero_<champion>.onnx --spec-b models/levels/expert.spec.json \
     --name-a master --name-b expert --sims-a 400 --sims-b 100 --c-puct 1.5 \
     --block-size 5 --max-pairs 100 --sprt-alpha 1e-12 --sprt-beta 1e-12 \
     --seed 20260952 --threads 10 --log-games --no-promote-winner \
     --out evaluations/artifacts/difficulty_edge_master_vs_expert.json
   ```

   Zweite Kante Experte gegen Erfahren, Seed 20260953, analog (Sims beidseits 100, Unterschied
   nur in den Stilfeldern). Dritte Kante Erfahren gegen Anfaenger ueber den Artefakt-Referee
   `python -X utf8 -u tools/frozen_referee_match.py ...`, festes n = 200, Seed 20260954,
   `--force-cross-era` falls der Handshake ROT ist (das Heuristik-Artefakt traegt ein aelteres
   Wheel; Aera-Regel `docs/promotion_checklist.md`).
   **Kosten:** 600 Partien, davon 400 mit Sims 100 bis 400, unter 1 h (ANNAHME; gemessene
   Nachbarn: 200 Paare @400 mit Logs 5.182-5.446 s, 75 Paare @100 gegen @400 1.062 s,
   `docs/measured_runtimes.md`).
   **Bei Abbruch:** je Kante einzeln wiederholen, Seed beibehalten; Frueh-Stopp bleibt AUS
   (`--sprt-alpha 1e-12 --sprt-beta 1e-12`), weil hier eine Leiterposition gemessen wird und
   kein Champion-Tor.
8. Je Kante danach `tools/probes/arena_column_probe.py --artifact <ART>` und
   `tools/plate_points_from_arena.py <ART> --block 5` (H2 behauptet genau diese Richtung:
   die Stilstufen bauen weniger Spalten und weniger Punkte als der Meister).

**P5 -- Stufe 3: gespielt = gemessen (hartes Tor, par.5)**

9. Je Stufe eine Partie ueber den GUI-Pfad und dieselbe Partie ueber den Arena-Pfad (gleicher
   Seed, gleiche Stufen-Spec): Zugfolge byte-gleich (Muster Netz-Paritaets-Fixture,
   Promotions-Checkliste 5d). ROT heisst: die Stufe spielt in der GUI einen anderen Spieler als
   den, dessen Kante sie traegt. Kein Bau der Auswahl, bevor jede Stufe gruen ist.

**P6 -- Stufe 4 und 5**

10. **Stufe 4** ist Nutzerzeit: je Stufe mindestens 3 Partien mit `difficulty` im Log-Kopf;
    Kennzahlen je Stufe Siege, Punkte, Margin plus die sechs Standard-Kennzahlen aus
    `tools/analyze_game_log.py`. **Endstand aus den Endwertungszeilen, NICHT aus
    `# SPIELENDE`** (par.2.4: die Zeile weicht in allen 33 Logs ab). Erfolgskriterium vorab:
    keine Umkehr der Reihenfolge ueber zwei benachbarte Stufen; eine Umkehr bei n = 3 ist kein
    Befund, sondern eine Wiedervorlage fuer 6 weitere Partien auf den zwei Stufen. Die
    Ziehsucht am Stapel bei Stand 0 zaehlt nicht als Aussetzer (bekanntes Muster ALLER
    Netz-Stufen).
11. **Stufe 5** (Einfrieren am Projektende): Meister = letzter Champion, drei Kanten final,
    Tabelle par.4.1 mit Elo-Knoten je Stufe, `README.md` und `docs/` nachgezogen, Kopf dieser
    Prereg auf ENTSCHIEDEN.

### 4. Auswertung und Registrierung

- **Zahlen mit n, Grundmenge, Einheit**: Kanten "n = 200 Partien (100 Paare), Grundmenge
  gepaarte Partien der beiden Stufen, Einheit Siege"; Latenz "n = Drafting-Zuege beider Seiten
  aus 2 Partien je Stufe, Grundmenge Drafting-Zuege, Einheit s je Zug"; Mensch-Validierung
  "n = Partien je Stufe, Grundmenge Mensch-Partien, Einheit Siege/Punkte/Margin".
- **Die sechs Standard-Kennzahlen** je Stufe aus den Kanten-Logs, zusaetzlich volle Spalten
  (`arena_column_probe.py`) und Punkte je Wertungsplatte (`plate_points_from_arena.py`), weil H2
  genau diese Richtung behauptet.
- **Registrierung in par.10**; **Zeile-1-Kopf im selben Zug** nachziehen, danach sofort
  `python tools/generate_prereg_index.py`.
- **STATUS.md Abschnitt 1 und Abschnitt 5**, `archive/history.md` fortschreiben.
- **Rueckwaerts-Pruefung -- par.9 nennt die Konsumenten bereits**: `README.md:300-303` (Presets),
  `server.py` Kopfkommentar Z.19-20, `docs/knobs.md` (falls ein Knopf dazukommt),
  `evaluations/STATUS.md` Abschnitt 5, `PREREG_claude_play_interface.md` par.5 (Antwortzeit @400
  steht dort als ANNAHME; Stufe 1 liefert die Messung). Dazu
  `grep -rn "difficulty_levels\|DIFFICULTY_PRESETS\|models/levels" evaluations/ docs/ tools/ static/ server.py`.
- **Laufzeit-Zeilen** in `docs/measured_runtimes.md` (Latenz je Stufe, drei Kanten, Bau-Tore).
- **Elo-Register**: jede der drei Kanten geht als Knoten hinein
  (`python tools/elo_tracker.py add --player-a <stufe-a> --sims-a .. --player-b <stufe-b> --sims-b .. --wins-a .. --wins-b .. --n 200 --units-from-paired-artifact <ART>`),
  damit die Stufen eine Leiterposition mit Konfidenzintervall tragen. **Das Namensschema der
  Knoten ist offen** (par.8 Punkt 8) -- siehe Stopp-Punkte.

### 5. Stopp-Punkte fuer den Nutzer

- **Namensschema der Elo-Knoten fuer die Stilstufen** (par.8 Punkt 8; Vorschlag in par.5 Stufe 2:
  `<champion>@100rn`, `<champion>@100rn-t2-wegc`). **Nutzer fragen**, bevor die erste
  Register-Zeile geschrieben wird -- ein Knotenname ist eine gemessene Identitaet
  (Feedback `measured_identity_gets_own_bxx`).
- **Anfaenger-Stufe: hv2 oder hv3?** par.4.1 nennt `hv2_generator` (Nutzer-Entscheid
  2026-09-11), der Nachtrag 2026-09-12, 21:50 empfiehlt `hv3_generator`, weil es auf dem Motor
  der heutigen Champions spielt (kein Cross-Aera-Wheel im Spielbetrieb); beide sind im Segment 2
  gleich stark (983 gegen 978). **Nutzer fragen.**
- **Ob die Kanten je Champion-Wechsel oder nur am Ende gefahren werden** (par.8 Punkt 8,
  Vorschlag: nur am Ende, Praezedenz `PREREG_search_depth_column_optimum.md` par.8c).
- **Streichen einer Stufe** nach zwei Kerben (Notch-Regel) und **Rueckgabe des Zuschnitts**,
  falls Erfahren gegen Anfaenger verliert.
- **Anker-Drift ROT oder Paritaets-Fixture veraendert: anhalten**, Nutzer-Entscheid.
- **Kein Push, keine Loeschung** ohne Freigabe; die toten `DIFFICULTY_PRESETS` werden erst im
  Code-Abschluss Stufe 2 entfernt (`PREREG_code_cleanup_closeout.md` par.4).

### 6. Abhaengigkeiten und Reihenfolge

**Vorher:** Start der v29-Erzeugung (Stufe 0 und der Bau laufen daneben, aber NICHT waehrend
Waechter oder Kette) und Tor 1 der v29-Generation (die Kanten brauchen den dann amtierenden
Champion als Meister). **Danach:** Stufe 4 (Nutzerzeit), dann Stufe 5 mit dem letzten Champion
-- ist v29 doch die letzte Generation, fallen Stufe 2 und Stufe 5 zusammen (par.8 Punkt 6); nach
dem heutigen Stand folgt v30 (`PREREG_v29_window.md` par.8 Punkt 3), also laeuft Stufe 5 dort.
Dieser Punkt ist Nr. 1 des Begleitprogramms in `PREREG_v29_window.md` par.7.

## par.11 GEPRUEFT 2026-09-13: spielt das Netz in der GUI dasselbe Spiel wie in der Arena?

Nutzerfrage waehrend der v29-Erzeugung. Die Antwort ist fuer diese Prereg zentral, weil die
Stufen ueber die Sim-Zahl gebaut werden sollen. Alles am Code geprueft, kein Lauf.

**Gleich sind Suchweg und Konfiguration:**

| Punkt | Arena | GUI / Server |
| --- | --- | --- |
| Einstieg | `net_arena_choose_action` -> `net_search_drafting_action` | `py.rs::ai_drafting_net_step` -> `net_mcts::net_search_with_tree` |
| Finale Zugwahl | `select_final_root_child` | `select_final_root_child` (`net_mcts.rs` Z.5515) |
| Wurzelrauschen | `false` (hart) | `false` (hart, `py.rs` Z.915) |
| Runde-5-Loeser | Kurzschluss vorhanden | Kurzschluss vorhanden (`net_search_with_tree` Z.5472) |
| Spec | per `--spec`-Datei je Seite | **per UMGEBUNG** -- `server.py` schreibt die Champion-Spec beim Start dorthin (`_apply_champion_spec_env`, Z.289; Abbildung Z.205-232 deckt Huelle, Projektionsmodus, Huellenform, `special_row6_w`, `start_by_search` ab) |

Der Spec-Rueckfall im Server ist kein Schmuck: `net_search_with_tree` liest ausdruecklich
`SearchConfig::from_env()` (Kommentar `net_mcts.rs` Z.5475-5481, "Mensch-vs-Netz-Einstieg ...
AUSSERHALB des Wave-1-Scopes"). Ohne ihn spielte die GUI mit den Env-Defaults, also OHNE
Huelle -- genau der Vorfall, den `server.py` Z.242-245 beschreibt.

**Die SUCHTIEFE: die GUI spielt heute IMMER bei 400 -- also genau der Arena-Tiefe.**

**KORREKTUR 2026-09-13, in zwei Schritten und beide Male vom Nutzer angestossen.** Die erste
Fassung dieses Absatzes las `int(preset.get('sims') or 100)` (`server.py` Z.698, Z.830) und
`or 300` (Z.1529) als gesetzte Werte und schloss daraus, das Netz in der GUI sei schwaecher als
das im Register. Beides ist falsch:

1. Es sind FALLBACKS fuer ein Preset ohne `sims`, und kein Preset ist ohne. Sie greifen nie
   (Nutzer: "Ich denk die 100 sind legacy" -- zutreffend).
2. **Wichtiger: die Presets sind aus der GUI gar nicht erreichbar.** Das steht seit dem Anlegen
   im Kopf dieser Prereg und in par.2: "Presets im Server sind aus der GUI nicht erreichbar,
   alle 33 Mensch-Partien liefen @400". Gespielt wird also `_default` mit 400 Sims, argmax,
   ohne Wurzelrauschen -- **dieselbe Einstellung, bei der die Arena misst und der Elo-Knoten
   `v28-b02@400` gebildet ist.** Wer heute in der GUI gegen den Champion spielt, spielt gegen
   den vermessenen Spieler, nicht gegen eine abgeschwaechte Fassung.

**Der Bestand im Code ist NICHT der registrierte Zuschnitt.** `DIFFICULTY_PRESETS`
(`server.py` Z.292-301) traegt `easy` Heuristik@60, `medium` Champion@60, `hard` Champion@150,
`expert` und `_default` Champion@400. Der Zuschnitt dieser Prereg (par.4.1, ENTSCHIEDEN
2026-09-11, Nachtrag 2026-09-13) sieht dagegen vor: Anfaenger = `hv3_generator` @150, darueber
Erfahren und Experte aus dem Champion MIT Self-Play-Stilmitteln (Sims 100, Wurzelrauschen,
Besuchs-Sampling, Weg C), Meister = Champion wie in der Arena. Die beiden Zuschnitte
unterscheiden sich in jeder Stufe ausser der obersten; die alten Presets sind Bestand aus der
Zeit vor dieser Prereg und werden mit dem Bau (par.4.2/4.3) ersetzt. **Diese Prereg beschreibt
also nicht den heutigen Zustand, sondern loest ihn ab.**

**Was das fuer die Messung heisst.** Nur die oberste Stufe hat heute einen gemessenen
Elo-Knoten (`v28-b02@400` 1394). Fuer die geplanten Zwischenstufen bei 100 Sims traegt das
Register `@100` mit 1298 und `@200` mit 1289 -- aber ohne die Stilmittel, die der Zuschnitt
zusaetzlich vorsieht (Wurzelrauschen, Sampling, Weg C). Deren Wirkung ist ungemessen, und genau
dafuer sind die drei Kanten aus par.5 da. Der Abstand 100 zu 400 ist mit rund 96 Elopunkten
beziffert (45:105 gepaart, n = 150, McNemar p = 6e-7, `PREREG_search_depth_column_optimum.md`
par.8e) -- die Spanne allein aus Sims ist also da, die Frage ist, was die Stilmittel ergaenzen.

**Ein LATENTER Unterschied, heute ohne Wirkung, aber eine Sollbruchstelle:** die Arena ruft vor
der Suche `builder_drafting_preference` auf und wuerde deren Ergebnis der Suche VORZIEHEN
(`self_play.rs` Z.3123-3127); der Serverpfad kennt den Vorzug gar nicht (0 Treffer in `py.rs`
und in `net_search_with_tree`). Folgenlos ist das nur, weil die Kette bei unbesetzten Knoepfen
durchgaengig `None` liefert (`self_play.rs` Z.2253-2261: `MOSAIC_SPALTENBAU`/`MOSAIC_PLATTENBAU`
unset). **Wer einen der beiden Knoepfe je ins Rezept nimmt, laesst Arena und GUI auseinander
laufen** -- und nach dem Muster des Stapelzug-Knopfs (`PREREG_chance_nodes.md`, Nachtrag
2026-09-13) merkt das niemand, weil kein Artefakt es mitschreibt.

Bemerkenswert: genau diese Fehlerklasse ist schon einmal aufgetreten. Der Kommentar an der
vereinheitlichten Spielschleife (`self_play.rs` Z.2240-2251) nennt als Anlass, dass der
Bauer-Vorzug "in zwei Kopien verdrahtet (einmal einseitig, einmal beidseitig) und im
Produktionspfad zunaechst gar nicht" war. Der Serverpfad ist die Stelle, die bei jener
Zusammenlegung aussen vor blieb.

**Nicht geprueft:** ob der Tiling-Pfad (`ai_tiling_step`) in beiden gleich ist, und ob die
Startsetzung ueber `ai_start_tile_json` dieselbe Suche fuehrt wie `StartSearchParams::for_net`
in der Arena.

## par.12 STUFE 0: INVENTUR (2026-09-13, Nutzer-Freigabe "Fang an mit nummer 22"; keine Rechenlast)

**Nutzer-Entscheid im selben Zug, der den Zuschnitt von par.5 aendert: "Durchmessen wuerd ich es
erst mit v30, da das unser Release Modell wird."** Der BAU (par.4.2/4.3) laeuft also jetzt, die
KANTEN (par.5 Stufen 1-3) erst gegen den v30-Champion. Das ist konsistent: die Stufen 2 bis 4
haengen am amtierenden Champion, und den loest v30 ab -- Kanten gegen v29 waeren mit der
Promotion wertlos. Die Stufe-4-Mensch-Validierung verschiebt sich entsprechend.

### Die fuenf Punkte, jeder mit Pruefstelle

| # | Frage | Befund | Pruefstelle |
| --- | --- | --- | --- |
| a | Artefakt des Anfaenger-Spielers vollstaendig? | **JA** fuer `hv3_generator`: `spec.json`, `manifest.json`, `golden_probe/`, Wheel `mosaic_rust-0.1.0-cp314-cp314-win_amd64.whl`, dazu `venv/`. Manifest traegt `rolle`, `spec`, `wheel`, `contract_hash`, `engine_config`, `golden_probe`, `protokoll`, `freeze_date`. | `models/frozen_heuristics/hv3_generator/` |
| b | Identitaet `hv2_generator` = Elo-Knoten `Heuristik_v2huelle`? | **PLAUSIBEL, nicht bewiesen.** Das Manifest nennt als Rolle "Erzeuger des v22-Korpus (24.000 Partien, 2026-08-25/26)", Spec `heuristik_variante: hv2`, Einfrierdatum 2026-08-26. Die Alt-Register-Kante vom 2026-08-25 (`v21_2d_brierbest@400` gegen `Heuristik_v2huelle@150`, 255:152) stammt aus derselben Kampagne. **Aber:** `git_dirty: true` beim Einfrieren -- der Baum trug unversionierte Aenderungen, ein Bit-Beweis ist damit nicht zu fuehren. | `models/frozen_heuristics/hv2_generator/manifest.json`, `archive/elo_history_pre_phantomfix.csv:7` |
| c | Welche Heuristik-Variante spielt die GUI heute? | **hv1, HART VERDRAHTET.** Der GUI-Heuristik-Pfad `ai_drafting_step` ruft `search_with_tree`, und die ruft `build_tree(..., HeuristicVariant::Hv1)`. Die Funktion nimmt die Variante NICHT als Parameter; `py.rs` enthaelt keinen Treffer auf `resolve_heuristic_variant` oder `set_heuristic_variant`. Auch `server.py` kann sie nicht setzen: die Spec-Abbildung dort fuehrt `heuristik_variante` nicht (0 Treffer). | `engine/src/py.rs:763` und `:810`, `engine/src/mcts.rs:938`, `server.py` Z.205-232 |
| d | Liest der DRAFTING-Pfad der GUI die Knoepfe zur Suchzeit? | **NETZ-Pfad JA** (`net_search_with_tree` liest `SearchConfig::from_env()`, und `server.py` schreibt die Champion-Spec beim Start in die Umgebung). **HEURISTIK-Pfad NEIN**: `search_with_tree` nimmt gar keine `SearchConfig` entgegen (nur `state`, `sims`, `c`, `rng`, Tiefe, TopK, Log). Die Spec-Knoepfe wirken also nur, wenn ein Netz spielt. | `engine/src/net_mcts.rs:5481`, `server.py:289`, `engine/src/mcts.rs:925-938` |
| e | Wo sitzen Wurzelrauschen, `action_temp`, `tau_argmax_from_move` und Weg C -- und was erreicht ein Einzelzug-Aufruf NICHT? | **Wurzelrauschen:** erreichbar, aber hart auf `false` (`py.rs:915`). **Die drei anderen erreichen den GUI-Einzelzug GAR NICHT:** sie sitzen in der Self-Play-Zugwahl (`self_play.rs:5249` ff.: `deterministic`-Zweig, `tau_argmax_override`, Sampling ueber `weights`), waehrend der GUI-Pfad ueber `select_final_root_child` immer argmax spielt. Weg C (`deviate_prob`) ist eine Partie-Eigenschaft der Self-Play-Schleife und hat im Einzelzug-Einstieg keinen Ort. | `engine/src/py.rs:915`, `engine/src/self_play.rs:5249-5270`, `engine/src/net_mcts.rs:5515` |

### Was daraus die Umbau-Liste fuer par.4.2 wird

1. **Der Heuristik-Pfad braucht einen Variantenparameter.** Heute ist hv1 einbetoniert; der
   Zuschnitt will `hv3_generator @150` als Anfaenger. Ohne diesen Umbau ist die unterste Stufe
   nicht baubar. Die Fehlerklasse ist bekannt und dokumentiert: derselbe Einstieg nahm die
   Variante schon einmal nicht entgegen, und "ein `--heuristik-variante hv3` ohne `--model`
   haette still ein hv1-Korpus erzeugt" (`engine/src/lib.rs:84-89`).
2. **Drei der vier Stilmittel muessen in den Einzelzug-Einstieg gereicht werden**
   (Besuchs-Sampling, argmax-ab-Halbzug, Weg C). Wurzelrauschen ist schon da, steht aber fest
   auf aus.
3. **Die Spec-Abbildung in `server.py` braucht `heuristik_variante`**, sonst kann die
   Stufentabelle die Anfaengerstufe nicht ueber die Spec setzen.

### Offen, Nutzer-Entscheid (unveraendert aus par.4.1)

- **Namensschema der Elo-Knoten** je Stufe.
- **Anfaenger hv2 gegen hv3**: der Kopf dieser Prereg nennt seit dem Nachtrag 2026-09-13
  `hv3_generator`, die Tabelle in par.2.5 noch `hv2_generator`. Punkt (b) oben spricht fuer
  hv3, weil dessen Artefakt sauber eingefroren ist, waehrend hv2 mit `git_dirty: true`
  eingefroren wurde.

### par.12a ZUSCHNITT-PRAEZISIERUNG (Nutzer 2026-09-13): die unteren Stufen ueber hv3 mit verschiedenen Sims

Woertlich: **"Hv3 mit unterschiedlichen sims wird fuer die unteren Stufen relevant."** Damit
traegt die Sim-Zahl der HEURISTIK die unteren Stufen, statt dass sie alle aus dem Champion mit
Stilmitteln kommen (par.2.5 Tabelle Zeilen 2 und 3). Der Bau aus par.12 aendert sich dadurch in
der Prioritaet: Punkt 1 der Umbau-Liste (Variantenparameter fuer den Heuristik-Pfad) wird zur
Voraussetzung nicht nur der untersten, sondern mehrerer Stufen; die Stilmittel (Punkt 2) werden
fuer sie nicht gebraucht.

**Was zur Sim-Wirkung bei Heuristiken GEMESSEN ist** (Segment 2, `evaluations/elo_history.csv`,
Stand 2026-09-13) -- die Zahlen sind fuer die Stufenabstaende die Planungsgrundlage:

| Knoten | Elo | 95%-CI | Partien |
| --- | --- | --- | --- |
| `Heuristik_hv4_anchor@600` | 1030 | [992, 1068] | 600 |
| `Heuristik_hv4_anchor@150` | 1000 | fix (Anker) | 1.100 |
| `Heuristik_hv2_generator@150` | 983 | [949, 1019] | 500 |
| `Heuristik_hv3_generator@150` | 972 | [935, 1011] | 400 |

**Die tragende Einzelkante:** `hv4_anchor@600` gegen `hv4_anchor@150`, **82:68** (n = 150
Partien, Grundmenge Referee-Partien desselben Artefakts gegen sich selbst bei verschiedener
Sim-Zahl, drei Bloecke a 50 bis zum Deckel ohne Frueh-Stopp, Binomial p = 0,29). Das sind
55 Prozent und rund **30 Elopunkte fuer den Faktor vier** in den Simulationen.

**Zum Vergleich derselbe Sprung beim NETZ:** `v28-b02@100` gegen `@400` verliert 45:105, also
30 Prozent, und das Register trennt die beiden Knoten um rund 96 Punkte
(`PREREG_search_depth_column_optimum.md` par.8e). **Die Sim-Zahl ist bei der Heuristik ein
erheblich schwaecherer Regler als beim Netz** -- gemessen ist das bisher nur an hv4, nicht an
hv3.

**KORREKTUR 2026-09-13 (Nutzer: "Es gibt keine oberen hv3 Stufen. Wir machen das ueber das
Netz."):** die erste Fassung dieses Absatzes las "untere Stufen" als mehrere hv3-Stufen und
rechnete mit Abstaenden zwischen ihnen. Das ist falsch. **Die Heuristik traegt AUSSCHLIESSLICH
die unterste Stufe** (Anfaenger, hv3 @150, par.12c); alles darueber kommt aus dem Netz, wie es
die Stufentabelle in par.4.1 von Anfang an registriert hat. Die hv3-Sim-Zahl ist damit kein
Regler ZWISCHEN Stufen, sondern nur die Einstellung der einen Heuristik-Stufe.

Die Zahlen oben bleiben trotzdem nuetzlich: sie sagen, dass ein Verstellen der hv3-Sims die
Anfaengerstufe kaum bewegen wuerde (rund 30 Elopunkte fuer den Faktor vier), eine Feinjustierung
dort also wenig bringt. Wer die unterste Stufe leichter machen will, muesste deutlich unter 150
gehen -- und dort ist bei der Heuristik nichts gemessen.

**Die Abstaende zwischen den Stufen 2 bis 4 macht folglich das NETZ**, ueber Sims und die drei
Stilmittel (par.4.1). Deren Wirkung ist ungemessen; die Sim-Wirkung beim Netz dagegen ist es
(rund 96 Elopunkte zwischen 100 und 400) und ist die belastbare Groesse fuer den Zuschnitt.

### par.12b BAU BEGONNEN (2026-09-13, Nutzer: "baue alles was moeglich ist dafuer")

Die Maschine traegt die v29-Erzeugung, also wird geschrieben und NICHT kompiliert. Stand:

**GEBAUT (unkompiliert, Tore stehen aus):** `mcts::search_with_tree_variant`
(`engine/src/mcts.rs:957`) -- dieselbe Suche wie `search_with_tree`, aber mit waehlbarer
`HeuristicVariant`. Der Bestands-Einstieg bleibt und delegiert mit `Hv1`, ist also
bit-identisch; es gibt noch KEINEN Aufrufer mit einer anderen Variante. Damit ist der Blocker
aus par.12 Punkt c auf der Suchseite ausgeraeumt.

**NICHT GEBAUT, weil ein Entscheid fehlt: WIE kommt die Variante in den GUI-Pfad?**
`SearchConfig::from_env` setzt sie hart auf `Hv1` und begruendet das ausdruecklich
(`net_mcts.rs` Z.736-739): *"KEIN Env-Knopf: die Variante kommt aus der Spec oder gar nicht. Ein
prozessweiter Schalter waere fuer eine Partie hv1 GEGEN hv3 unbrauchbar -- er gaelte fuer beide
Seiten oder fuer keine."* Das ist eine bewusste Design-Entscheidung, und der geplante Weg aus
par.4.2 (Server schreibt die Stufen-Spec in die Umgebung, Muster `_apply_champion_spec_env`)
laeuft genau dagegen.

Zwei Wege, Nutzer-Entscheid:

- **(A) Spec-Datei bis in den Zugpfad.** `PyGame` bekommt ein Feld fuer die aktive
  `SearchConfig` plus eine Lademethode; `ai_drafting_step` und `ai_drafting_net_step` nutzen sie
  statt `from_env`. Folgt dem registrierten Design ("eine Stufe ist eine Spec-Datei, die GUI und
  Arena gleich lesen", par.4.2) und traegt auch die Stilmittel der oberen Stufen. Groesserer
  Umbau in `py.rs`, beruehrt jeden GUI-Suchpfad.
- **(B) Env-Knopf nur fuer den Server-Prozess.** Billiger, aber gegen den Kommentar. Der dortige
  Einwand ("gaelte fuer beide Seiten") trifft den Server allerdings NICHT: in der GUI spielt
  genau EINE KI-Seite gegen einen Menschen. Wer das nimmt, sollte den Kommentar im selben Zug
  praezisieren, statt ihn stehen zu lassen.

**Danach erst baubar:** `heuristik_variante` in der Spec-Abbildung von `server.py` (Z.205-232,
heute nicht enthalten), die Stufen-Specs unter `models/levels/`, und die drei fehlenden
Stilmittel fuer die oberen Stufen (par.12 Punkt e). Die Sim-Zahlen der hv3-Stufen sind
ebenfalls offen (par.12a).

### par.12c ENTSCHEIDE 2026-09-13 (Nutzer): hv3 @150 als Default der Heuristik-Stufe, Weg A fuer den Umbau

Woertlich: **"Hv1 als default macht keinen Sinn. Der ist archiviert. Nimm hv3 als default mit
150 Sims. Plane den groesseren Umbau ein."**

**Umgesetzt wird das als Default der STUFE, nicht als neuer Engine-weiter Default.** Der
Unterschied ist nicht kosmetisch, deshalb hier ausgeschrieben (geprueft 2026-09-13):

**Erst die Begriffe, weil ich sie in einer ersten Fassung vermengt habe (Nutzer-Korrektur
2026-09-13: "Nein tragen sie nicht. Das ist hv4"):** ARTEFAKTNAME und VARIANTENFELD sind zwei
Ebenen. Spielbar sind in diesem Build genau zwei Varianten, `hv1` und `hv3`
(`engine/src/lib.rs:140`); **`hv4` ist kein Variantenname, sondern die vierte Generation des
ANKER-ARTEFAKTS.** Es heisst so, weil es der Anker seit dem Phantom-Fix A2 ist
(Manifest-Rolle: "Elo-Anker, Segment 2 der Leiter (seit dem Phantom-Fix A2, 2026-09-12)"), und
nicht, weil es eine vierte Heuristik spielte.

| Traeger | Was es IST | `heuristik_variante` im Spec-Feld |
| --- | --- | --- |
| `frozen_heuristics/hv4_anchor` | Anker-Artefakt, 4. Generation, Motor MIT A2 | `hv1` |
| `frozen_heuristics/hv3_generator` | Artefakt der hv3-Heuristik | `hv3` |
| `frozen_champions/v28-b02` | Champion-Netz | `hv1` (fuer die Heuristik-Anteile der Suche) |

Der Unterschied zwischen `hv1_anchor` (geloescht 2026-09-13) und `hv4_anchor` war nie die
Variante, sondern der MOTOR: derselbe `hv1`, einmal ohne und einmal mit A2. Genau deshalb war
das alte Anker-Artefakt obsolet.

Beide tragen ihr Variantenfeld in der EIGENEN Spec und sind von einem geaenderten Env-Default
nicht betroffen -- eine Spec gewinnt immer. Betroffen waeren nur Pfade OHNE Spec.
Den Env-Default in `SearchConfig::from_env` (`net_mcts.rs` Z.739) anzufassen, waere trotzdem eine
ENGINE-Aenderung mit Anker-Drift-Pflicht und Wirkung auf jeden spec-losen Aufrufer, also auch auf
Sonden und Tests. Das ist hier nicht gemeint und wird nicht getan.

**Gemeint und registriert:** die Heuristik-Stufe der GUI spielt **hv3 mit 150 Sims**, und das ist
zugleich der Rueckfall, wenn keine Stufen-Spec geladen ist. Damit steht die Anfaengerstufe
vollstaendig: Artefakt `hv3_generator`, Variante hv3, 150 Sims, Elo-Knoten
`Heuristik_hv3_generator@150` = 972 [935, 1011].
**Falls doch der Engine-weite Default gemeint war**, ist das ein eigener Entscheid mit
Anker-Drift und Paritaets-Fixture als Toren -- nicht nebenbei.

**Weg A ist gewaehlt** ("Plane den groesseren Umbau ein"): die Spec-Datei reist bis in den
Zugpfad, statt ueber einen prozessweiten Env-Knopf zu gehen. Das folgt par.4.2 ("eine Stufe ist
eine Spec-Datei, die GUI und Arena gleich lesen") und respektiert den Einwand in
`net_mcts.rs` Z.736-739.

### Bauplan Weg A (Reihenfolge bindend, Tore am Ende)

1. **`PyGame` bekommt die aktive Suchkonfiguration als Feld** plus eine pyo3-Lademethode
   (`load_search_spec(path)`), die `SearchConfig::from_spec_file` nutzt. Ohne Aufruf bleibt
   `from_env()` der Inhalt -- Bestandsverhalten bit-identisch.
2. **Die GUI-Zugpfade lesen das Feld statt `from_env`:** `ai_drafting_net_step`
   (`py.rs` Z.913-915) und `ai_drafting_step` (Z.810). Letzterer ruft dann
   `mcts::search_with_tree_variant` (bereits gebaut, par.12b) mit der Variante aus der Config.
3. **`server.py`:** `heuristik_variante` in die Spec-Abbildung (Z.205-232) UND der Aufruf der
   neuen Lademethode beim Stufenwechsel; die Stufen-Spec erweitert die Champion-Spec, Felder die
   sie nicht traegt werden zurueckgesetzt (Muster `_apply_champion_spec_env`).
4. **Stufen-Specs** unter `models/levels/`: `beginner.spec.json` **GESCHRIEBEN 2026-09-13 Nacht**
   -- die vierzehn Felder der eingefrorenen Artefakt-Spec
   (`models/frozen_heuristics/hv3_generator/spec.json`, byte-gleich zu `models/hv3.spec.json`,
   geprueft) plus `sims: 150`. Sie laedt ERST mit dem Wheel von Schritt 1b: vorher kennt
   `KNOWN_FIELDS` das Feld `sims` nicht und weist die Datei hart ab. Der Elo-Knoten dieser Stufe
   steht bereits (`Heuristik_hv3_generator@150` 972 [935, 1011], Segment 2, par.4.1).
   Alte Fassung dieses Punktes: `beginner.spec.json` (hv3, 150 Sims) ist nach diesem
   Entscheid schreibbar; `advanced`/`expert`/`master` brauchen noch die Sim-Zahlen und die drei
   Stilmittel-Felder (par.12 Punkt e, par.12a).
5. **Tore, alle Pflicht:** Lib-Tests, `--no-run --all-targets`, Wheel, **Netz-Paritaets-Fixture**
   (darf sich NICHT aendern -- der Umbau ist per Konstruktion bestandsgleich, eine Abweichung
   waere ein Fehler), **Anker-Drift UND Konservierung**, `check_conventions.py`.
6. **Danach erst** die Kanten -- und die laufen nach Nutzer-Entscheid 2026-09-13 gegen den
   v30-Champion, nicht gegen v29.

**Aufwand (ANNAHME):** Schritte 1-3 rund 3-4 h Rust plus Server, Schritt 5 rund 6 min gemessen.
Alles davon braucht eine freie Maschine; waehrend der v29-Erzeugung wird nur geschrieben.

#### Zwei Korrekturen am Bauplan (am Code nachgelesen, 2026-09-13 Nacht)

**(a) Schritt 3, erster Halbsatz entfaellt: `heuristik_variante` kann NICHT in die
Spec-Abbildung von `server.py`.** Jene Abbildung (`_SPEC_TO_ENV`, Z.204-232) setzt je Spec-Feld
eine UMGEBUNGSVARIABLE -- und fuer die Variante gibt es bewusst keine. `net_mcts.rs` Z.735-739
sagt es woertlich: *"KEIN Env-Knopf: die Variante kommt aus der Spec oder gar nicht. Ein
prozessweiter Schalter waere fuer eine Partie hv1 GEGEN hv3 unbrauchbar -- er gaelte fuer beide
Seiten oder fuer keine."* Die Begruendung ist staerker als der Bauplan-Satz, und sie ist genau
der Grund fuer Weg A. Es bleibt der ZWEITE Halbsatz: der Server ruft beim Stufenwechsel
`PyGame::load_search_spec`, und die Variante reist im `SearchConfig`-Feld `heuristic_variant`
(`net_mcts.rs` Z.689) bis in den Zugpfad. Schritte 1 und 2 dafuer liegen gebaut im Baum
(`py.rs` Z.94/153/164).

**(b) Schritt 4 haengt HAERTER an Schritt 1, als dort steht: `beginner.spec.json` ist heute NICHT
schreibbar.** `SearchConfig::from_spec_file` prueft die Feldnamen gegen eine feste Liste und
lehnt jedes unbekannte Feld HART ab (`net_mcts.rs` Z.779-784). In dieser Liste stehen weder
`sims` noch die vier Stilfelder aus par.4.2 (`root_noise`, `action_temp`,
`tau_argmax_from_move`, `deviate_prob`/`deviate_candidates`). Eine Stufen-Spec mit
"hv3 @150" wuerde also beim Laden scheitern -- die 150 sind kein Spec-Feld. **Die Felder muessen
zuerst in `SearchConfig` und in `KNOWN_FIELDS`**, erst danach lassen sich die vier Dateien unter
`models/levels/` ueberhaupt anlegen. Die harte Ablehnung ist dabei kein Hindernis, sondern die
Zusage, die sie geben soll (derselbe Absatz: ein stiller Default wuerde "die 'beweisbar
identisch'-Zusage aushebeln").

**Folge fuer die Reihenfolge:** 1 (gebaut) -> 2 (gebaut) -> **1b: Stilfelder plus `sims` in
`SearchConfig`, `from_spec_file` und `KNOWN_FIELDS`** -> 3 (Server: `load_search_spec` beim
Stufenwechsel) -> 4 (Stufen-Specs) -> 5 (Tore). Schritt 1b ist neu und gehoert zu den 3-4 h
Rust; er braucht eine freie Maschine, weil ohne Bau kein Tor faellt. Vorhanden und
wiederverwendbar: `models/hv3.spec.json` traegt bereits `heuristik_variante: "hv3"` und alle
Champion-Felder -- sie ist die Vorlage fuer `beginner.spec.json`, sobald `sims` ein Feld ist.

#### Schritt 1b im Einzelnen (vorbereitet 2026-09-13 Nacht, Quellen nachgelesen)

Alle sechs Felder sind **OPTIONAL mit Default = Bestandsverhalten** -- dasselbe Muster und
dieselbe Begruendung wie bei `dead_cell_w`/`out_wild_w`/`round_est_c`
(`net_mcts.rs` Z.895-908): die eingefrorenen Artefakt-Specs und die lebenden
`models/*.spec.json` tragen sie nicht, und mit dem Default beschreibt eine Spec ohne sie
bitgenau das Verhalten, das sie schon immer beschrieben hat. Erst wenn ein Feld
Rezeptbestandteil wird, wandert es per `tools/spec_add_field.py` in die lebenden Specs und kann
auf Pflicht hochgestuft werden.

| Spec-Feld | Typ | Default | Heutige Quelle | Bemerkung |
| --- | --- | --- | --- | --- |
| `sims` | ganze Zahl > 0, optional | keiner (Aufrufer entscheidet) | Parameter des Suchaufrufs | als `Option<u32>` fuehren, nicht als 0-Sentinel: 0 Sims ist kein sinnvoller Wert und ein Sentinel verdeckt den Unterschied "nicht gesetzt" gegen "gesetzt" |
| `root_noise` | bool, optional | keiner (Aufrufer entscheidet) | Parameter `add_root_noise`, GUI ruft `false` (`py.rs` Z.856) | ebenfalls `Option<bool>` |
| `action_temp` | ganze Zahl 0..2 | 0 (aus, rohe Besuchszahlen) | `MOSAIC_ACTION_TEMP` | **MODUS, kein Faktor** (siehe Befund unten) |
| `tau_argmax_from_move` | ganze Zahl >= 0 | 0 (aus) | `MOSAIC_TAU_ARGMAX_FROM_MOVE` (`net_mcts.rs` Z.3101) | ab Halbzug N argmax statt Besuchs-Sampling |
| `deviate_prob` | Zahl 0..1 | 0.0 (aus) | `MOSAIC_DEVIATE_PROB` | bei 0.0 wird keine einzige Zusatz-Zufallszahl gezogen |
| `deviate_candidates` | ganze Zahl >= 1 | **6**, nicht 0 | `MOSAIC_DEVIATE_CANDIDATES` | wirkt nur bei `deviate_prob > 0` |

**BEFUND, der par.4.2 berichtigt: `action_temp` ist ein MODUS-Schalter, keine Temperatur.**
par.4.2 fuehrt es als "`action_temp` (f64, 0 = argmax)". Die Knopf-Registratur
(`knob_registry.rs` Z.140) sagt etwas anderes: *"MODUS, kein Faktor: 1 = Staffel wie im
Heuristik-Pfad (n>50 -> 0,7; n>15 -> 0,4; sonst 0,15), 2 = glatte Form ... Bei 0 exakt die rohen
Besuchszahlen, bitidentisch"*. Das Feld ist also eine ganze Zahl 0..2, und "0" heisst nicht
"argmax", sondern "rohe Besuchszahlen" -- argmax ist `tau_argmax_from_move`. Wer die Stufen
zuschneidet, muss das auseinanderhalten: die beiden Regler sitzen an verschiedenen Stellen.

**GEBAUT UND ABGENOMMEN 2026-09-14, 01:35.** Alle sechs Felder liegen in
`engine/src/net_mcts.rs` (Struct, `from_env`, `KNOWN_FIELDS`, Parser, Konstruktion, dazu der
Test-Helfer `search_config_off`), `self_play::deviate_prob`/`deviate_candidates` sind dafuer auf
`pub(crate)` gehoben, und `py.rs::search_config_json` gibt sie aus.

**Das vorregistrierte Tor ist BESTANDEN.** Gefahren neben dem laufenden b01-Training (GPU),
also als der eine erlaubte CPU-Auftrag (CLAUDE.md): 641 Tests gruen, 0 rot, keine
Compiler-Warnung, 100,3 s. Entscheidend ist `net_parity_hash_matches_champion_fixture` --
**sie ist gruen geblieben**, und genau das war die Vorhersage: ungenutzte Felder aendern das
Verhalten nicht. Dasselbe gilt fuer den Vertragshash und die Feature-Golden-Fixture.
Installiert wurde NICHTS: der Lauf beruehrt weder das Wheel noch `config.INPUT_SIZE`, die
laufende Kette bleibt also unberuehrt. Mitgebaut: `tools/check_conventions.py` Regel 8 erkennt
jetzt die dritte Bauform optionaler Felder (der gemeinsame Helfer `spec_u32`) -- ohne sie meldete
sie alle zwanzig lebenden Specs als unvollstaendig.

**Drei Stellen je Feld** (Muster an `start_by_search` ablesbar, es ist das juengste der
optionalen Felder): die Felddeklaration samt Doc-Kommentar im Struct `SearchConfig`
(`net_mcts.rs` ab Z.543), der Default in `from_env` (ab Z.700) und das Einlesen in
`from_spec_file` samt Eintrag in `KNOWN_FIELDS` (Z.760-785, Parser ab Z.800). `sims` und
`root_noise` haben keinen Env-Knopf -- sie bleiben in `from_env` schlicht `None`, so wie
`heuristic_variant` dort hart auf `Hv1` steht.

**Die VERDRAHTUNG ist ein eigener Schritt (1c) und der groessere.** Felder allein aendern nichts:
`root_noise` und `sims` sind heute Parameter des Suchaufrufs, Temperatur und Weg C leben in der
Self-Play-Schleife (`self_play.rs` Z.2649-2700). Erst wenn die Aufrufer die Werte AUS DER CONFIG
nehmen, liest die GUI denselben Spieler wie `paired_gating.py`. Schritt 1b ist bewusst davon
getrennt, weil er fuer sich bestandserhaltend ist und ein eigenes Tor bekommt: **die
Netz-Paritaets-Fixture darf sich nach 1b NICHT aendern** (ungenutzte Felder), waehrend sie nach
1c bewusst neu gesetzt werden koennte.


## par.13 GANZE LEITER auf v30 vertagt (Nutzer-Entscheid 2026-09-14)

**Woertlich:** *"ich wuerd die schwierigkeitsleiter nicht jetzt machen sondern erst mit dem
finalen champ. sonst kalibrieren wir es auf ein modell ein das zum schluss nicht spielt."*

**Das geht weiter als der Stand davor.** par.4.1 hatte nur die KANTEN auf den v30-Champion
vertagt (Entscheid 2026-09-13); Bau und Zuschnitt der Stufen standen weiter im v29-Programm
(Fahrplan Nr. 22). Der Einwand trifft aber den Zuschnitt selbst: die drei oberen Stufen sind als
"Champion mit weniger Sims und mehr Stilmitteln" definiert (par.4.1). Welche Sim-Zahl welche
Spielstaerke ergibt, haengt am Netz -- an einem anderen Netz liegen die Stufen anders.

**Fehlerklasse:** eine Skala auf einem Traeger eichen, der zur Messzeit nicht mehr existiert.
Das ist dieselbe Klasse wie
[[feedback-dont-calibrate-to-plate-blind-play]] und wie die Wiedervorlage-Regel aus CLAUDE.md
("eine Konstante nie auf einer Reihe verankern, von der man WEISS, dass ein Punkt fehlt"). Hier
ist der fehlende Punkt der Champion selbst.

**Was das heisst:**

- **Vertagt auf v30:** Schritt 1c (Verdrahtung), Schritt 3 (Server), Schritt 4 (die drei oberen
  Stufen-Specs), Schritt 5 (Tore), das Frontend aus par.4.3 und die Kanten aus par.5. Im Fahrplan
  sind das die Punkte 22 und 37.
- **Bleibt liegen und ist NICHT verloren:** Schritt 1 und 2 (das `SearchConfig`-Feld und die
  beiden GUI-Zugpfade) sowie Schritt 1b (die sechs optionalen Stilfelder) sind gebaut, getestet
  und bestandserhaltend -- die Netz-Paritaets-Fixture ist danach unveraendert geblieben. Sie
  kosten nichts, solange niemand eine Stufen-Spec laedt. Auch `models/levels/beginner.spec.json`
  bleibt: die Anfaenger-Stufe ist hv3 @150 und haengt NICHT am Champion, ihr Elo-Knoten steht
  bereits (972 [935, 1011]).
- **Gewinn fuer v29:** rund 6 bis 8 Stunden aus dem Begleitprogramm (Fahrplan-Schaetzung vom
  2026-09-14), plus die Stufen-Kanten aus Punkt 37.

**Der Zuschnitt selbst bleibt gueltig** (par.4.1/4.1a: vier Stufen, Anfaenger hv3 @150, die drei
oberen aus dem amtierenden Champion). Nur wird "der amtierende Champion" jetzt als der v30-Champion
gelesen, nicht als v28-b02 oder ein v29-Arm.
