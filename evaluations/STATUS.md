# Mosaic-AI – Status & Fahrplan

**Dieses Dokument traegt NUR Aktuelles und Offenes.** Neufassung vom 2026-09-10, 23:55
(Generationswechsel v27 -> v28, Schritt 6); der vollstaendige Stand davor liegt in
`../archive/history.md`, Kapitel **"Vollstaendiger STATUS-Stand vom 2026-09-10 (vor der
Neufassung)"**, die Generationsberichte v24 bis v27 ebenfalls dort.

**Pflegeregel:** wer einen Befund erzeugt, traegt ihn im selben Zug hier nach und prueft, ob
ein anderer Abschnitt dadurch falsch wird. Wer einen Strang abschliesst, schiebt die
Herleitung ins Archiv und laesst hier eine Zeile mit Verweis stehen.

**Dauerhaftes Prozesswissen steht NICHT hier**, sondern in `../docs/`: `generation_loop.md`
(Schleife, Tore, Tor-2-Praezedenz, Seed-Regel), `promotion_checklist.md`,
`generation_naming.md`, `working_rules.md`, `pitfalls.md`, `measured_runtimes.md`,
`architecture_reference.md`, `engine_manual.md` (mit Regelbuch-Zitaten).

---

## 1. UEBERGABE an die naechste Sitzung (2026-09-10, 23:55)

**Champion laut `models/champion.txt`: `v27-b01_brierbest`, Elo 1405** [1361, 1453] aus 790
Partien; Leiter `v26-b01` 1364, `v25-b01` 1336, `v24-b07` 1283, Anker fix 1000. Promotion
vollstaendig (Artefakt `models/frozen_champions/v27-b01/`, restic `run:v27-b01`),
Generationsbericht v27 in `../archive/history.md`, Belege `PREREG_v27_window.md` par.7-10.

**Das Einfrieren ist beendet** (v25-b01 / v26-b01 / v27-b01: gleiches Rezept, rotierendes
Material; dreimal Tor 1, dreimal steigende Spalten). **Der Generationswechsel v27 -> v28 ist
bis Schritt 6 durch**; Schritt 7 (Start) wartet auf dich.

**MASCHINE BELEGT: ABLATIONS-KETTE `tools/night_v28_ablations.sh` (b03 ohne Ausflug-Klasse, b04
ohne G-2, je Training plus Tor 1 gegen b02 mit zwei Seeds), gestartet 2026-09-11 abends, Ende
etwa 8 h spaeter.** Davor: **v28-b02 NULLBEFUND** gegen b01 (207:193, 209:191, beide Deckel; Elo
1461 gegen 1447 ueberlappend; Blockziehungen bei positivem Stand eher mehr, nicht weniger;
`PREREG_v28_window.md` par.10, `dome_stack` par.15h). **Nutzer-Entscheid 20:30: b02 ist als
korrektere Fassung (volleres Merkmalsbild) der beste Stand und Generator-Kandidat fuer v29;**
Promotion dann fuer v28-b02, sofern keine Ablation ihn schlaegt. **K3-D plus Jokerfeld-Knopf GEBAUT** (`dead_cell_w`,
`out_wild_w`, Default 0 bitidentisch; 576 Tests gruen, Wheel installiert, Anker-Drift gruen,
`geometric_envelope` par.12c), Messungen C2 und A1/A2 folgen nach den Ablationen. Vorher 14:37-14:47: Baum auf INPUT_SIZE 755 (Stash
eingespielt), Wheel gebaut und installiert, Anker-Drift GRUEN, Paritaetstor Rust/Python
BESTANDEN (`PREREG_rust_data_layer.md` par.7). Der Baum ist damit auf Variante B; das
Tor-1-Instrument kuerzt 744er-Modelle auf Modellbreite (`net.rs:421`).

**v28-b01: TOR 1 BESTANDEN, TOR 2b HAELT (2026-09-11, `PREREG_v28_window.md` par.10):**
166:124 (Seed 20261036, SPRT nach 145 Paaren, p 0,015) und 221:179 (Seed 20261037, Deckel,
p 0,053, KI der Paardifferenz [+0,01; +0,41]); Elo **1447 [1395; 1499]**; volle Spalten je
Seite 1,030 gegen 0,884; Punkte +3,0 je Partie, vertikale Reihen +1,43, Spezialfelder +0,88.
Training `v28-b01` DURCH 11:55: brierbest Epoche 3 (val_brier 0,1802), 5.157 s,
`run:v28-b01` gesichert. Generator-Kandidat fuer v29: v28-b01, sofern kein v28-Arm ihn
schlaegt. Davor die Kette: Der erste Lauf starb um 10:13 im Monolith-Merge: 24 Bloecke
(`selfplay_v27-b01-policy_*_g410` bis `g640`, gebaut 00:14-00:28) trugen 755 Spalten unter
744er-Schluesseln, weil die Waechter-Worker `config.py` frisch importierten, waehrend die
Datei fuer den Variante-B-Bau auf 755 stand (der Elternprozess hatte 744 im Schluessel). Die
Kette startete das Training trotzdem auf dem halben Monolithen (Exit 1, KeyError `values`).
Behoben: 24 Bloecke an Ort und Stelle neu gebaut (Gesamtscan 3.203 x 744), Formen-Waechter
im Merge (`tools/build_cache_parallel.py`), Kette bricht bei Merge-Fehler ab. Kein Modell
entstanden, kein Artefakt betroffen. **Erzeugung FERTIG**
23:49:56 bis 09:45:31, 3 x 4.000 Partien, 1.201 Dateien, 35.726 s = 9,92 h
(`PREREG_v28_window.md` par.10). **Tor 2a HAELT: 0,816 gegen 0,777** volle Spalten je Seite
(n = 8.000 Seiten). Fenster 2.947 Dateien, Schluessel `2db448af20fe`, alle Bloecke unter
INPUT_SIZE 744. Monolith 9 min, Training 1,43 h, beides gemessen. Danach Tor 1 `v28-b01` gegen
`v27-b01` mit `--log-games` (zwei Seeds), dann `git stash pop` und Variante B fuer `v28-b02`.

**Claude-Partien: g02-g05 gegen `v27-b01` FERTIG (Claude 3:1), g06/g07 gegen
`v28-b02_brierbest` @400 FERTIG (2026-09-11): 1:1, g06 70:64 gewonnen, g07 45:58 verloren.**
Alle Seeds und Spec-Pfade aus den Partie-Manifesten; registriert in
`PREREG_claude_play_interface.md` par.7 mit Endwertung je Kriterium, den sechs
Standard-Kennzahlen, Beobachtungen und eigenen Fehlern. Zwei Linien tragen jetzt ueber sechs
Partien:

1. **Das Netz spielt plattenblind und gewinnt trotzdem ueber Platzierungen.** In g06 holte es
   0 von 10 moeglichen Endwertungspunkten (zwei Wildfelder leer, keine farbenreiche Reihe,
   keine Diagonale) und kam dennoch auf 64; in g07 verlor es die Endwertung 2:8 (drei leere
   Spezialfelder, -9) und gewann die Partie um 13. Nebenbefund aus g06: **zwei volle Spalten,
   obwohl keine Spaltenplatte auslag** -- der Spaltenbau laeuft unabhaengig von der Auslage.
2. **Die Null-Klammer ist fuer das Netz ein Werkzeug, kein Unfall.** In g07 fiel es in Runde 1
   bewusst von 5 auf 0 (13 Ziehungen in EINEM Zug, fuenf bezahlt) und durchsuchte danach bei
   Stand 0 den Stapel mit 8, 7 und 4 Ziehungen je Zug; zurueck bei 12 Punkten zog es genau
   einmal. In g06 fiel keine Seite je auf 0 -- und es gab keinen einzigen Mehrfachzug.
   Damit ist **Arm A1 der `PREREG_corpus_behaviour_audit.md` an lebenden Partien bestaetigt**
   (dort par.7 mit der Tabelle), bevor der Korpuslauf gefahren ist. **Der Lauf selbst kommt
   erst mit v29 (Nutzer 2026-09-11);** die Quellenfrage ist geklaert (Prereg par.3: keine
   Partielogs noetig, `state.log` je Record ueberlappend zusammensetzen).

**Eigene Schwaeche bleibt die Strafleiste:** ueber g06/g07 -40 gegen -19 des Netzes; in g07
allein -25 gegen -11 bei 13 Punkten Endabstand. Ursache in beiden Partien dieselbe wie in
g02/g04/g05: sind am Rundenende alle Musterreihen farblich festgelegt, fegt Aktion C die
Restfarben als Block herein. Dazu in g07 ein Rotationsfehler beim Plattenlegen (Schwarz-Zelle
in z5 statt z4, R4 zwangsgeraeumt, rund -5).

**Werkzeug `tools/claude_play.py`:** der ausstehende **Rauchtest mit lebendem Gegner ist
GRUEN** (g06, par.9 P.11). Neu dazugekommen (par.9 P.12/13): `save_manifest` wiederholt gegen
OneDrive-Sperren (ein `PermissionError` hatte in g06 einen schon berechneten Netzzug
verschluckt, weil `drive_ai` das Manifest VOR `append_log` schreibt), neues Unterkommando
**`step`** laesst nur die KI ziehen (Notausgang genau dafuer), und zwei offene Bedien-Luecken
sind benannt: die Zwangsraeumungs-Warnung kommt erst NACH dem Plattenlegen, und
`chips <reihe>` hat keine Chipwahl.

**Restprogramm der Reihe: g08-g10.** Claude spielt weiter als ZWEITSPIELER
(`--claude-side 1 --first-player 0`), damit die Reihe fuenf Partien je Seite hat. Die zehn
Partien laufen gegen drei verschiedene Champions (g01 v24-b06, g02-g05 v27-b01, g06-g10 v28)
-- eine Siegquote ueber alle zehn ist keine Groesse, ausgewiesen wird je Block
(`PREREG_claude_play_interface.md` par.8.8).

### v28: ZUSCHNITT UND KETTE (gestartet 2026-09-10, 23:49)

`PREREG_v28_window.md`: Zuschnitt (580 Traeger + rund 2.367 Schwarm, Seed 20260937, Val-Pool
`^selfplay_v27-`), Generator `v27-b01`, G-2-Schwarm aus der Ausflug-Haelfte von v25-b01
(Nutzer 2026-09-10), Record-Feld `dome_pool_view` im Wheel (Anker-Drift gruen, Rauchtest
321/321 Records), Skripte `tools/night_v28_generate.sh` (Seeds 20260917/18/19, rund 10,3 h)
und `tools/night_v28_chain.sh` (Training `v28-b01`, Rezept unveraendert). Zweiter Arm
`v28-b02` = Variante B: GEBAUT (par.9 der Prereg, elf Werte, INPUT_SIZE 755, Rust-Export,
Kontrakt-Hash neu c65768636c0560a7), aber **die Python-Seite liegt in `git stash` (stash@{0})**,
damit die laufende Kette b01 mit 744 trainiert. Nach Kette und Tor 1 b01: `git stash pop`,
Wheel, Anker-Drift, `tools/probes/feature_parity_rust_python.py`, Bloecke neu, Training b02.
**Wer den Baum vorher anfasst: NICHT `git stash pop` vor dem b01-Training.**

Start: `bash tools/night_v28_generate.sh` plus Cache-Waechter unter
`MOSAIC_IGNORE_POLICY_TARGET_VALID=1` (Aufruf im Skriptkopf), danach `bash tools/night_v28_chain.sh`.
Vorher pruefen: Maschine frei (Claude-Partien beendet), `models/champion.txt` = v27-b01_brierbest,
Platz (`data/` 6,96 GiB, Sicherungswurzel).

### FREIGABEN UND VERBOTE (woertlich vom Nutzer)

- **Kein Push ohne Anweisung.** Ahead-Stand im Chat melden.
- **Loeschung nur auf pfadgenaue Freigabe.**
- **Messungen laufen exklusiv**; GPU und CPU duerfen parallel, zwei CPU-Messungen nicht.
- **v28-Erzeugung gestartet 2026-09-10, 23:49 und fertig 2026-09-11, 09:45**; v29 nur auf Anweisung.
- **Trainings-Seed variabel je Generation, gleich innerhalb einer Generation** (2026-09-10).
- **Ziehen vom Stapel bei Punktestand 0 bleibt gratis und legal** (Regelbuch S.4/S.9,
  2026-09-10).

### BEFUNDE, die eine Entscheidung oder Nachschau brauchen

- **Artefakt `models/frozen_champions/v25-b01/` vom Nutzer geloescht (2026-09-11)**: der
  Elo-Kader haelt nur noch v26-b01 und v27-b01 als Artefakte; die Champion-2-Kante einer
  v28-Promotion geht gegen das v26-b01-Artefakt. Loeschung im Baum committet.
- **`player_profiles.json` ist im Arbeitsbaum veraendert** (plus `player_profiles.json.bak`),
  aus der Nutzer- bzw. Parallelsitzung; nicht committet.
- ~~Erzeugung v27/v28 langsamer als v26~~ GEKLAERT 2026-09-11 (Nutzer): Teile der
  v26-Erzeugung liefen ausgelagert, die v26-Zahl ist keine Referenz dieser Maschine. Fuer v29
  mit 10 h planen.
- **Alte Mess-Manifeste in `data/`** (`manifest_otw22*`, `manifest_p3s0*`, `manifest_peek22*`,
  `manifest_tor22*`, `manifest_v21depth*`, `manifest_frozenv3-b01*`, 30 Dateien, klein): ihre
  Korpora sind seit 2026-09-09 geloescht; Loeschkandidaten beim naechsten Wechsel.
- **Zwei untracked Replay-Reports** in `evaluations/game_analysis/` (Rauchtest 2026-09-10).
- **Server-Log-Kopf traegt seit `29b8e1a` Spec-Pfad und Knoepfe**; wirkt nach dem naechsten
  Neustart. Mensch-Partien vom 2026-09-08 bis 2026-09-10 18:20 liefen ohne Champion-Spec
  (Vorbehalte in `score_clamp` par.10 und `dome_stack` par.15d).

## 2. LAUFZEITEN (gemessen, Planungsgroessen; Artefakte und Details in `docs/measured_runtimes.md`)

| Aufbau | Dauer |
| --- | --- |
| Erzeugung 3 x 4.000 Partien @100, threads 11 (v27 / v28) | 36.912 s = 10,25 h / 35.726 s = 9,92 h |
| Kette Schritte 1-6 (Kennzahlen, Manifeste, Fenster, Monolith) | rund 31 min |
| Training 12 Epochen, Fenster 2.947 Dateien | 5.117 s = 1,4 h (v26 mit Nebenlast 2,1 h) |
| Gepaartes Gating 200 Paare @400, 10 Threads, mit `--log-games` | 5.182-5.446 s = 86-91 min (13,6 s je Partie) |
| Anker-Kante n=150, 6 Worker | rund 22 min |
| Champion-2-Kante gegen Artefakt, n=150 | rund 43 min |
| A/B ueber den Referee, gleiches Netz, n=150 | rund 43 min |
| sigma/Prior-Kalibrierung, Platt-Fits | 13 min, je 10 s |
| Golden Probe fuers Artefakt, Referee-Selbsttest | 23 min, 67 s |
| Spaltensonde / Block-Ziehungs-Sonde auf 400 Logs | 83 s / rund 95 s |
| Wheel-Bau plus Install, Anker-Drift | 30 s, 25 s |

## 3. SPEC UND REZEPT

Spec `models/v24-b07_brierbest.spec.json` (identisch mit der Spec im Artefakt v27-b01):
`envelope_projection_mode 1`, `envelope_search_c 1,0`, `envelope_flush_w 0,0`,
`envelope_hull_form 2`, `special_row6_w 1,0`, Profil 1/0,92/0,67/0,33/0. Nach dem Ende des
Einfrierens ist kein Spec- oder Rezept-Entscheid registriert; `v28-b01` faehrt beides
unveraendert, `v28-b02` aendert nur das Merkmal. Engine seit v27: Variante A des
Kuppelstapels, Dubletten-Fix im Ausflug, Record-Feld `dome_pool_view`, Rueckgabe-Reihenfolge
nur fuer den Ausfuehrenden sichtbar; Anker-Drift nach jedem Schritt gruen.

## 4. DAS PROGRAMM NACH v27 -- Stand

| Strang | Prereg | Stand 2026-09-10 |
| --- | --- | --- |
| Kuppelstapel-Informationsmengen | `dome_stack_information_sets` par.15-15h (Variante B: Nullbefund) | Variante A GEBAUT und gemessen: A/B 165:135 ohne Ruecklauf, Fix bleibt; Diagnostik auf 300 Partien: Ziehungen in den eigenen Block STEIGEN (+0,69 je Partie), meist gratis bei Stand 0; par.8-Erwartung nicht eingetreten, Diagnostik neu gefasst (Ziehungen bei positivem Stand). Naechster Hebel Variante B = v28-b02 |
| Null-Klammer | `score_clamp_incentive` | ENTSCHIEDEN: Regel bleibt (Stufe 0: 39 % der Partien auf 0, geschluckte Strafe Median 0, 3,1 Gratis-Ziehungen je Partie und Seite) |
| Startpositions-Seeding / Ausflug | `start_position_seeding` | ENTSCHIEDEN: Dubletten-Fix gebaut (par.9l); Folgearme brauchen eigene Registrierung |
| Sicht-Reststufen | `stack_top_feature` par.10/11/12 | offen; Merkmale erst nach v28-b02, weil sie Records brauchen |
| Claude-Partien | `claude_play_interface` par.7/par.9 | g02-g07 gespielt (3:1 gegen v27-b01, 1:1 gegen v28-b02); Werkzeug-Rauchtest gruen; g08-g10 offen |
| Einhuellende, Schliesskriterium | `geometric_envelope` par.12c | EINGETAKTET 2026-09-11 als v28-Schritt 8: K3-D plus Jokerfeld-Knopf bauen, C2 an den v28-Armen, A1/A2 am Champion |
| Werkzeuge | | `paired_gating --log-games` (Tor 2b aus Tor 1), `plate_points` je Modell, `dome_stack_known_block_draw_probe`, exakter Orakel-Pfad, Spec-Rueckfall in server.py |

## 5. PREREG-BESTAND (14 OFFEN, Ziel rund 7)

`v28_window` (Vorlage), `dome_stack_information_sets` (Variante B), `stack_top_feature`,
`claude_play_interface` (laeuft), `round_estimate_leaf_term` (Skalenwahl a/b, Nutzer),
`round_transition_search_sampling` (haengt an dome_stack; Kandidat fuer UEBERHOLT),
`start_dome_choice` (Stufe 0 nie gefahren; Sonde am v28-Korpus), `policy_surprise_weighting`
(Kante v24-b05 gegen v24-b04 aus dem restic-Repo nachholbar), `rust_data_layer`
(Registrierung ohne Auftrag; Kandidat fuer UEBERHOLT), `difficulty_levels` (angelegt
2026-09-11; Zuschnitt vom Nutzer entschieden: Anfaenger = Anker hv2 @150, Erfahren/Experte
= Champion mit Self-Play-Stilmitteln, Meister = Champion wie in der Arena; drei Kanten je
100 Paare als Messung, Bau = Stilmittel in die Spec fuer GUI UND Arena; Mensch-Bilanz 24:7:2
aus den Endwertungszeilen, NICHT aus `# SPIELENDE`; EINGETAKTET fuer v29 (Nutzer 2026-09-11):
Bau waehrend der v29-Erzeugung, Kanten nach Tor 1 v29; offen nur das Knoten-Namensschema).
`v29_window` (angelegt 2026-09-11 als Zyklusdurchlauf: Pflichtarm b01, Generator = Sieger der
v28-Promotion, Begleitprogramm Leiter und Ziehsucht-Sonde; Nutzer-Entscheide par.8).
`code_cleanup_closeout` (angelegt 2026-09-11 nach dem Code-Review, `evaluations/review/`; Stufe 1
Korrektheit/Beobachtbarkeit vom Nutzer freigegeben, Bau neben der Kette, Tore danach; Stufen 2/3
nach der letzten Generation; drei Nutzer-Entscheide par.6).
Index: `PREREG_INDEX.md` (generiert).

## 6. OFFENE NUTZER-ENTSCHEIDE

0. ~~Name des Schlussmodells~~ ENTSCHIEDEN 2026-09-11: **Tessa** (Umsetzung mit Stufe 3 des
   Code-Abschlusses, `PREREG_code_cleanup_closeout.md` par.5a).

1. ~~Start der v28-Erzeugung~~ gestartet 2026-09-10, 23:49.
2. ~~Bau von Variante B~~ ENTSCHIEDEN 2026-09-11, 00:10: elf Werte plus Rust-Merkmalsexport
   (`PREREG_v28_window.md` par.8); Bau laeuft (Agent), danach Wheel und Paritaetstor.
3. **v28-Programm verbindlich** (par.8 dort): b01, b02, Ablationen b03/b04, Startkuppel-Sonde,
   Ueberraschungs-Kante, round_estimate als Such-Knopf nach b02. Offen darin: Skala des
   Rundenschaetzers (Vorschlag (a) je Runde; (b) 9,25 auf Zuruf).
4. **Loeschfreigaben**: alte Mess-Manifeste in `data/`, die zwei Replay-Reports.
5. **Spec- und Rezeptfragen nach dem Einfrieren**: keine gestellt; b01 faehrt beides fest.

## 7. MERKLISTE CODEPFLEGE und STRUKTURBEFUNDE

Die Merkliste vom Audit 2026-08-27 (Bool-Knopf-Dialekte, stille Env-Verschlucker,
ONNX-Paritaetspruefung, `champion.txt`-Eigenaufloesungen, 998-Zeilen-`MosaicDataset`) steht
unveraendert im Archiv-Kapitel "Vollstaendiger STATUS-Stand vom 2026-09-10", Abschnitt 7. Von
den Strukturbefunden dort ist der erste ("Der Champion vollendet keine Spalten") seit v26
UEBERHOLT (1,27 volle Spalten je Partie gegen den Anker); die uebrigen (Dreieck als
Machbarkeitshuelle, Rasterzeile nur ueber Spezialfliese, Drafting vor Routing, Mensch-Referenz,
Blindzieh-Regel) gelten weiter, Wortlaut im Archiv.
