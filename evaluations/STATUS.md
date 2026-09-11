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

**MASCHINE BELEGT seit 2026-09-10, 23:49:56: v28-ERZEUGUNG LAEUFT** (Nutzer: "starte beides
hier, die app bleibt offen"; `tools/night_v28_generate.sh` als Hintergrundaufgabe dieser
Sitzung, Klasse 1 zuerst, Manifest `data/manifest_v27-b01-policy_20260910_234958.json`;
Cache-Waechter unter `MOSAIC_IGNORE_POLICY_TARGET_VALID=1` daneben; `night_v28_chain.sh` seit
23:49:57 scharf, wartet auf den `laufzeit`-Block der Ausflug-Klasse und faehrt dann Kennzahl mit
Tor-2a-Vorlage, Fenster, Bloecke, Monolith und Training `v28-b01`). Erwartet rund 10,3 h
Erzeugung plus 2 h Kette, also bis etwa 12:00 am 2026-09-11; die Claude-Partien laufen daneben,
die Laufzeit ist damit als Planungsgroesse gebremst zu lesen. Danach Tor 1 `v28-b01` gegen
`v27-b01` mit `--log-games`, Bau von Variante B fuer `v28-b02`.

**Claude-Partien g02-g05: FERTIG (2026-09-11). Die Parallelsitzung gibt ihren Teil der
Maschine frei -- von ihr laeuft nichts mehr.** Ergebnis: **Claude 3:1** gegen
`v27-b01_brierbest` @400 (g02 55:43, g03 66:48, g04 36:28, g05 50:55, alle Seeds und
Spec-Pfade aus den Partie-Manifesten). Registriert in `PREREG_claude_play_interface.md` par.7
mit Endwertung je Kriterium, den sechs Standard-Kennzahlen, Beobachtungen und eigenen Fehlern.
Zwei Muster tragen ueber alle vier Partien: die Ziehzahl am Kuppelstapel folgt dem
PUNKTESTAND (bei Stand 0 durchsucht das Netz den Stapel -- 21 Ziehungen allein in g04 Runde 1 --,
waehrend es in g05 nie auf 0 fiel und darum nur siebenmal zog), und das Netz fuellt lange
Musterreihen mit Farben, die seine eigene Kuppelzeile nicht aufnehmen kann (fuenf Vorfaelle,
in g04 zehn Steine auf einmal, volle Strafleiste). Beides ist seit 2026-09-11 als Sonde
vorregistriert: **`PREREG_corpus_behaviour_audit.md`**, drei Arme, alle aus vorhandenen
Partielogs, kein Engine-Eingriff und keine neue Erzeugung (A Anomalie-Report mit
Ziehungen je Platzierung bedingt auf den Punktestand und Zwangsraeumungen, B Siegquote
nach "faellt in Runde 1 auf 0", C konditioniert der Prior ueberhaupt auf die ausliegenden
Wertungsplatten). Die Prereg traegt damit Kanal 4 aus `PREREG_dome_stack_information_sets.md`
par.11. **Quellenfrage GEKLAERT 2026-09-11** (Prereg par.3): `--log-games` ist ein Arena-Flag,
`self_play.py` schreibt gar keine Partielogs -- aber jeder Record traegt `state.log` als
mitlaufendes Fenster, und ueberlappend ueber die Records einer Partie zusammengesetzt ergibt
das den vollstaendigen Log (ueber die UEBERLAPPUNG, nicht ueber eine Menge: 301 gegen 299
Zeilen). Alle drei Arme sind damit aus dem vorhandenen Korpus messbar, ohne neue Erzeugung.
Vorschau aus vier Partien: Stapelziehungen 4/24/5/36, Zwangsraeumungen 0/1/2/2.
**Der Lauf kommt erst mit v29 (Nutzer 2026-09-11);** bis dahin bleibt die Prereg
vorregistriert und ungemessen. Das Spiel-Werkzeug
`tools/claude_play.py` ist im selben Zug nachgebessert (par.9 P.8-10: falsche `KI:`-Zeile
durch die echten Engine-Logzeilen ersetzt, `m1`-`m4` abgewiesen, Pflichtzaehler und
Reihen-Ziele in `show`, Zugliste zusammengefasst); ein Rauchtest mit lebendem Gegner steht
aus, weil die Maschine belegt ist. Die verlorene Partie g05 ging an eigenen Strafleisten-Fehlern verloren (-32 gegen
-8), nicht an der Endwertung (21:9 fuer Claude).

**Restprogramm der Reihe: g06-g10 gegen v28, sobald es steht (Nutzer 2026-09-11).** Claude
spielt dort als ZWEITSPIELER (`--claude-side 1 --first-player 0`), damit die Reihe fuenf
Partien je Seite hat. Die zehn Partien laufen damit gegen drei verschiedene Champions
(g01 v24-b06, g02-g05 v27-b01, g06-g10 v28) -- eine Siegquote ueber alle zehn ist keine
Groesse, ausgewiesen wird je Block (`PREREG_claude_play_interface.md` par.8.8). **Vor g06
faellt der Rauchtest des geaenderten Werkzeugs an** (par.9 P.10).

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
- **v28-Erzeugung nur auf Anweisung** (ausgesetzt seit 2026-09-10, 13:25).
- **Trainings-Seed variabel je Generation, gleich innerhalb einer Generation** (2026-09-10).
- **Ziehen vom Stapel bei Punktestand 0 bleibt gratis und legal** (Regelbuch S.4/S.9,
  2026-09-10).

### BEFUNDE, die eine Entscheidung oder Nachschau brauchen

- **`player_profiles.json` ist im Arbeitsbaum veraendert** (plus `player_profiles.json.bak`),
  aus der Nutzer- bzw. Parallelsitzung; nicht committet.
- **Erzeugung v27 war 23 % langsamer als v26** bei gleicher Konfiguration (10,25 h gegen
  8,35 h); Ursache nicht gemessen (Waechter-Last, OneDrive). Fuer v28 mit 10,3 h planen.
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
| Erzeugung 3 x 4.000 Partien @100, threads 11 (v27) | 36.912 s = 10,25 h |
| Kette Schritte 1-6 (Kennzahlen, Manifeste, Fenster, Monolith) | rund 31 min |
| Training 12 Epochen, Fenster 2.947 Dateien | 5.117 s = 1,4 h (v26 mit Nebenlast 2,1 h) |
| Gepaartes Gating 200 Paare @400, 10 Threads, mit `--log-games` | rund 5.190 s = 86 min |
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
| Kuppelstapel-Informationsmengen | `dome_stack_information_sets` par.15-15g | Variante A GEBAUT und gemessen: A/B 165:135 ohne Ruecklauf, Fix bleibt; Diagnostik auf 300 Partien: Ziehungen in den eigenen Block STEIGEN (+0,69 je Partie), meist gratis bei Stand 0; par.8-Erwartung nicht eingetreten, Diagnostik neu gefasst (Ziehungen bei positivem Stand). Naechster Hebel Variante B = v28-b02 |
| Null-Klammer | `score_clamp_incentive` | ENTSCHIEDEN: Regel bleibt (Stufe 0: 39 % der Partien auf 0, geschluckte Strafe Median 0, 3,1 Gratis-Ziehungen je Partie und Seite) |
| Startpositions-Seeding / Ausflug | `start_position_seeding` | ENTSCHIEDEN: Dubletten-Fix gebaut (par.9l); Folgearme brauchen eigene Registrierung |
| Sicht-Reststufen | `stack_top_feature` par.10/11/12 | offen; Merkmale erst nach v28-b02, weil sie Records brauchen |
| Claude-Partien | `claude_play_interface` par.9 | laufen (Parallelsitzung) |
| Werkzeuge | | `paired_gating --log-games` (Tor 2b aus Tor 1), `plate_points` je Modell, `dome_stack_known_block_draw_probe`, exakter Orakel-Pfad, Spec-Rueckfall in server.py |

## 5. PREREG-BESTAND (9 OFFEN, Ziel rund 7)

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
Index: `PREREG_INDEX.md` (generiert).

## 6. OFFENE NUTZER-ENTSCHEIDE

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
