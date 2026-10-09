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

**KETTE `tools/night_v35_b02_chain.sh` FERTIG 2026-10-06 01:32:32 (25,2 h). MASCHINE FREI. ERGEBNIS: v35-b02 TRAEGT TOR 1.**
Drei Seeds gegen v34-b01 @400: 218:182 (z +1,51), 219:181 (z +2,12), 159:91 (SPRT-Stopp nach 125 Paaren, z +3,99);
**gepoolt 596:454 = 56,8 %, Block-z +4,07 ueber 105 Bloecke** (`PREREG_v35_window.md` par.12c-12e). Tor 2b GRUEN in allen
Seeds (volle Spalten je Brett 1,085/1,097/1,108 gegen 0,978/0,985/1,040), Punkte +1,7 bis +5,0 je Partie, Plattenpunkte
hoeher, Strafsteine in zwei Seeds rund 0,7 mehr. Tor 2a: policy-s400 0,807 +- 0,032 gegen Bezug 0,826 (gleich bedingt).
**Offline (par.12f): der Wertkopf lernt auf dem @400-Fenster MESSBAR** (dBrier Warmstart minus Epoche 2 +0,00107
[+0,00041; +0,00169] auf 120 Val-Dateien; b01 @100: +0,0006 mit CI ueber 0), Policy-CE gepoolt +0,158; Netz GESUND
(`weight_health_v35-b02.json`). Zuordnung vorab: Suchtiefe 400 PLUS Modus 2 in allen Klassen, nicht getrennt.
**OFFEN, Nutzer-Entscheid: Promotion v35-b02 (`/mosaic-champion-promotion`, Ein-Promotion-Regel je Generation; Elo-Kanten
erst damit ins Register).** Erzeugung 18,9 h (11.000 Partien, je Partie 6,92 / 6,91 / 6,64 / 5,20 s), Training 1.676,8 s,
Tor 1 5,2 h; alle Laufzeiten in `docs/measured_runtimes.md`.

**b03 (Trajektorien-Bootstrap k = 1) TRAEGT TOR 1 (10:46): Seeds 159:91 (SPRT-Stopp, z +5,28) und 222:178 (z +2,64), gepoolt 381:269 = 58,6 %, Block-z +5,12 ueber 65 Bloecke; Spalten 1,08/1,10 gegen 1,02/1,01, Punkte +3,5/+1,9; Val-Brier 0,18965 gegen b02 0,18942 (par.13a/13b). Deskriptiv ueber b02 (54,6 % auf denselben Seeds), Unterschied in Seed-Streuung; direkte Kante b03 gegen b02 nicht vorregistriert (Nutzer-Entscheid). **b05 (k = 2) TRAEGT TOR 1 (15:28): 224:176 (z +2,53) und 227:173 (z +2,93), gepoolt 451:349 = 56,4 %, Block-z +3,88; Spalten 1,05 gegen 1,01, Punkte +3,2/+2,3; Val-Brier 0,18970 (par.13c/13d). **b06 (k = 3) TRAEGT TOR 1 (20:10): 231:169 (z +3,05) und 224:176 (z +2,35), gepoolt 455:345 = 56,9 %, Block-z +3,83; Spalten 1,06 gegen 0,99, Strafsteine gleichauf, kleinster Spezialfeld-Abzug der Reihe (par.13e/13f). Bootstrap-Reihe komplett: alle drei Tiefen tragen, deskriptiv 2-4 Punkte ueber b02 ohne Monotonie in k, innerhalb der Seed-Streuung (par.13f Tabelle). **b04 (Margen-Bootstrap b = 20): Training 1.691 s, Val-Brier-Minimum 0,19034 in Epoche 4, schlechtester der Reihe (b02 0,18942), gegatet `_brierbest` (par.14a). Tor 1: 216:184 (z +1,65) und 236:164 (z +3,08), gepoolt 452:348 = 56,5 %, z +3,41; Seed 3 222:178 (z +2,05); GEPOOLT 674:526 = 56,2 %, Block-z +3,98 ueber 120 Bloecke: TRAEGT gegen v34-b01, aber nicht ueber b02 hinaus (56,8 %), bei schlechterem Brier: kein Hebel (par.14c). **b07 (lambda 1,0): Training 1.358 s auf dem b02-Monolithen, Val-Brier-Minimum 0,18946 in Epoche 2 (= b02), gegatet `_best` (par.15a). Tor 1: 216:184 (z +1,75) und 202:198 (z +0,18), gepoolt 418:382 = 52,25 %, z +1,26: **TRAEGT NICHT** (erster Arm ohne Kante; par.15b). Lesung: ohne den 30-%-Suchwert-Anteil faellt die Kante von z +2,50 (b02, gleiche Seeds) auf +1,26, offline unsichtbar; lambda 0,7 bleibt. b08 (EMA) trainiert seit 07:08.** **Dazu registriert (Nutzer 23:xx: *"Registrier mir die Punkte 1 bis 5 der trajektorien"*): Arme b11-b15 =
Varianten des Trajektorien-Bootstraps (par.19: TD(lambda) ueber den echten Pfad, plus Gegnerstellungen, Mittel mit Rollout,
Mischgewichte neu, Verlaesslichkeits-Gewichtung) mit dem Schnellblick-Protokoll par.19.0 (Gegner b02, Offline-Vorfilter,
2 Seeds a 50 Paare, "spannend" bei >= 55 % oder Block-z >= +1,5, dann volle Breite). Bau erst NACH dem Ende der Ketten
(Datenschicht wird von Workern und train.py frisch importiert); HERLEITUNG rund 1,9 h je Arm ohne Vollausbau.** **Neu registriert (Nutzer 23:xx: *"Registrier das, da koennen wir uns evtl. Eine Mini suche + netz daraus bauen"*):
`PREREG_tiling_surprise_probe.md` (OFFEN): Diagnose-Sonde "Tiling-Ueberraschung" = Netzwert nach dem Tiling des Loesers minus
Netzwert davor, je Runde, auf dem b02-Val-Satz, Referenz root_q und exakte Rundenpunkte; danach ggf. Mini-Suche ueber die
Top-k Tilings mit Netzbewertung am echten Rundenende (par.4; Abgrenzung zu Variante B par.17.9 und zu
`envelope_tiling_value_w` vorab noetig). Kein Arm, Bau nach den Ketten.** **RECHNER-NEUSTART 2026-10-07 gegen 17:33 (Nutzer-Meldung 23:2x):** die b10/b09-Kette (Tab c6) starb mitten in der
b09-Erzeugung bei 389 von 400 Dateien (letzte Datei 17:32:41, g3890); b10 war fertig gemessen. Stand 23:3x: Maschine frei,
alles bis dahin COMMITTET (`1474b729` Runde-5-Schalter, `cda98426` Reihe b03-b10 und Registrierungen; 11 vor origin/main,
nicht gepusht; der pre-commit-Hook faehrt die ganze Testsuite, 513 Tests gruen). **ERZEUGUNGS-REST b09 FERTIG 23:50 (Tab c7):** `self_play.py --recipe models/v35_b09.recipe.json --class policy-s400-vol --games 110 --seed 20263889` (= Basis 20263500 + 389 fertige Chunks; Rezeptwerte sind Defaults, Flags Overrides, `recipe_config.py:518`; Chunk-Seed = Basis + Index, `self_play.py:1315`), Manifest `..._233354.json` 1.016,6 s = 9,24 s je Partie (11 Threads, 110 Partien, 21.874 Zuege); genau 400 Dateien `selfplay_v34-b01-policy-s400-vol_*.pkl` liegen. Der Hauptlauf (389 Dateien, Manifest `..._112529.json` ohne `laufzeit`, vom Neustart gekillt) lief nach Dateistempeln 11:26:33 bis 17:32:41 = 21.968 s fuer 3.890 Partien = 5,65 s je Partie (HERLEITUNG aus Stempeln, kein Waechter daneben). **AGENT GELIEFERT 23:5x (geprueft: Stichproben `paired_gating.py:396/501/543/833/1084`, Kette `:86-117/323-346`, 0 U+2014):** Arena-Zwischenstand je Block in `tools/paired_gating.py` (`<out>.partial.json` atomar nach jedem Block, `--resume` mit Konfigurationspruefung per sha256, LLR-Nachrechnung, Laufzeit-Segmente wie train.py), `RESUME=1`-Modus der Kette, Absatz in `docs/working_rules.md`, Tests `tools/tests/test_paired_gating_resume.py`. **Testsuite 23:53: 531 Tests gruen (1 skip, 15,8 s)**, vorher 513. **LAEUFT seit 23:54 (Tab c8): `$env:RESUME='1'; bash tools/night_v35_b09_b10_chain.sh`**: b10 uebersprungen (ONNX + 2 Artefakte liegen), Rezeptpruefung ok, Fensterliste 1.600 (Val-Pool trifft 1.200, val_frac 0,075), seit 23:54:51 Bloecke fuer die 400 neuen Dateien (1c); dann Traeger-Manifest 800, Split (Val byte-gleich b02), Merge, Training, Offline gegen b02, Tor 1 zwei Seeds. Waehrend der Kette kein Build, kein Commit (Aenderungen des Agenten und diese STATUS-Zeilen warten uncommittet).** **b16 TRAEGT MIT DER STAERKSTEN KANTE DER REIHE (07:03, par.20b): Seed 2 154:86 = 64,2 % (SPRT-Stopp nach 120 Paaren, z +4,62), gepoolt 289:161 = 64,2 %, Block-z +6,63 (45 Bloecke), Margin +5,7 in beiden Seeds, Spalten 1,11/1,10 gegen 0,94/0,99; Val-Brier 0,18857 (bestes der Reihe), offline ueber b10 (CE +0,0070 mit CI). Lesart par.20 mechanisch (b) gesaettigt (3,3 Punkte ueber b10, Grenze 4), an der Grenze zu (a). ALLE KETTEN FERTIG, Maschine FREI seit 07:03. NUTZER-ENTSCHEIDE: Promotion (Kandidat b16), direkte Kante b16 gegen b10 (4 h), b18 = Tree-Reuse-Spec auf b16 (Tor 1, 4-5 h), par.5.6 Tree Reuse. Danach Generationswechsel (`/mosaic-generation-turnover`) oder Abschluss.** **b16 TOR 1 SEED 1 (06:03, par.20a): 135:75 = 64,3 %, SPRT-Stopp nach 105 Paaren (fruehester der Reihe), Block-z +4,68; Punkte +5,7 (groesste Margin der Reihe), Spalten 1,11 gegen 0,94, Platten 8,32 gegen 6,34. Training 2.087 s, Val-Brier 0,18857 (bestes der Reihe); offline ueber b02 (Brier +0,00085, CE +0,037) und ueber b10 (CE +0,0070 mit CI, Brier +0,00019 Tendenz). Seed 20261601 laeuft seit 06:03.** **b15 VOLLE BREITE: KEIN HEBEL (04:04, par.19.5d): gegen b02 154:176 (SPRT H0 nach 165 Paaren) und 197:203, gepoolt 351:379 = 48,1 %, Block-z -1,12 (73 Bloecke), Punkte -1,0/-1,2; Schnellblick-Lesart bestaetigt, 3,5 h. Trajektorien-Varianten damit endgueltig durch. b16 laeuft seit 04:04 (c13: Manifest 1.600 Traeger, Split byte-gleich, Merge unter `58500785fe54`, dann Training, Offline gegen b02/b10, Tor 1).** **b08b ABGESCHLOSSEN, KEIN HEBEL (00:34, par.16c): EMA-Auswahl Epoche 5 wie vorhergesagt, Val-Brier 0,18928, Vorab-Test bestanden (Brier +0,00014 [-0,00010; +0,00038], Policy-CE +0,0138), Schnellblick gegen b02 44:56 und 48:52, gepoolt 92:108 = 46,0 %, Block-z -0,98. Gewichtsmittelung in beiden Bauformen kein Hebel. b15 volle Breite laeuft seit 00:34 (c12), danach b16 (c13).** **TREE REUSE TRAEGT, KNAPP (23:12, par.3c, Kopf ENTSCHIEDEN): Seed 3 210:190 = 52,5 % (z +1,01, 24,1 s je Partie, Aufschlag ungeklaert), gepoolt drei Seeds 637:563 = 53,1 %, Block-z +2,22 (120 Bloecke), Punkte +1,1 bis +2,1 je Seed bei gleichem Netz; Spalteneffekt aus Seed 1 wiederholt sich nicht. Kette 6,8 h. OFFEN (Nutzer): b18 = Spec auf b10 oder b16; par.5.6. Kette b08b (c11) uebernimmt die Maschine.** **TREE-REUSE SEED 2 (20:31, par.3b): b17 204:196 = 51,0 %, Block-z +0,42, Spalteneffekt weg (1,045 gegen 1,025); gepoolt 427:373 = 53,4 %, Block-z +2,00, genau ein Seed ueber +1,96 -> Stufenregel, dritter Seed 20261602 laeuft seit 20:31 (Ende gegen 22:35), Verdikt danach ueber drei Seeds.** **TREE-REUSE SEED 1 (18:53, par.3a): b17 223:177 = 55,8 %, Block-z +2,42 (Deckel), McNemar p 0,030, 18,7 s je Partie; volle Spalten 1,16 gegen 1,05 (groesster Spalteneffekt der Reihe bei gleichem Netz), Vertikale +1,6 [+0,6; +2,6]. Seed 2 laeuft seit 18:53. Ketten b08b (c11), b15 volle Breite (c12), b16 (c13) warten in dieser Reihenfolge.** **REGISTRIERT 16:5x: b08b gebaut (Agent; `--weight-average-select brierbest`, 24 Tests, Kette `tools/night_v35_b08b_chain.sh`, par.16b), b15 volle Breite gegen b02 als Nutzer-Entscheid gegen die Lesart (par.19.5c, Kette `tools/night_v35_b15_full_chain.sh`), b16 = b09-Fenster mit allen 1.600 Dateien als Policy-Traeger (par.20, Kette `tools/night_v35_b16_chain.sh`, Agent baut). REIHENFOLGE (Nutzer): Tree-Reuse-Arena (laeuft) -> b08b -> b15 volle Breite -> b16; zusammen HERLEITUNG rund 13 h Maschinenzeit.** **TILING-SONDE GEMESSEN 15:58 (par.3b, 95 s, 4.551 Paare, 3 Netze): Ueberraschung des Wertkopfs am Rundenende Mittel +0,009 (v34-b01) -> +0,001 (b02/b10) Gewinnwahrscheinlichkeit, Betrag 0,06 (Streuung; Eingabe traegt die Rundenpunkte exakt, Luecke 0,02); gepaart b10 minus b01 Mittel -0,008, Betrag -0,003, beide CI unter 0: das Netz lernt den Loeser. Kein systematischer Spielraum fuer die Mini-Suche par.4, Empfehlung nicht bauen (Nutzer-Entscheid). Kopf ENTSCHIEDEN. TREE-REUSE-ARENA laeuft seit 16:24 in Tab c10 (`tools/tree_reuse_arena_chain.sh`, b17 gegen v34-b01, Seeds 20261600/01); kein Commit waehrend des Laufs.** **TECHNIK 15:35-15:55 (Nutzer-Reihenfolge: Technik, dann b08b, b15 volle Breite, b16): Tree-Reuse-Entwurf kompiliert (ein Borrow-Fix, `1b256d1a`), cargo test 861 gruen inkl. Paritaets-Fixture und Knopfregister, Wheel `cd8995bf` installiert, Anker-Drift GRUEN (1.763 Schritte); Namen v35-b17 (v34-b01 + `models/v35-b17.spec.json`, tree_reuse 1 / round5 1) und b18 reserviert (b10); Smoke 5 Paare: Reuse greift in rund 2/3 der Suchen, +18-29 % Besuche, 20,5 s je Partie (Aufschlag ungeprueft). Replayer-Fix committet (`f71f2800`, 16 Tests). Tiling-Sonde gebaut (Agent, par.3a der Sonden-Prereg, kein Engine-Build noetig, 18 Tests), Netz-Rauchlauf und Messung folgen. LAEUFT/NAECHSTES: Tree-Reuse-Arena `tools/tree_reuse_arena_chain.sh` (2 x 200 Paare, rund 4-5 h), dann b08b.** **KETTE b11-b15 FERTIG 15:01 (10,1 h). b15 (Konfidenz s = 0,01224): Schnellblick 58:42 und 50:50, gepoolt 108:92 = 54,0 %, Block-z +0,95 = nach Regel KEIN HEBEL, einzige Variante an der Schwelle (par.19.5b; Policy-CE +0,0128 ist HERLEITUNG Checkpoint-Epoche 2 gegen 5). GESAMTVERDIKT par.19.6: keine der fuenf Varianten spannend, Bootstrap-Quelle als Hebel ABGESCHLOSSEN; Querbefund: alle Varianten verlieren bei vertikalen Reihen. Reihe v35 damit DURCH. Maschine FREI. OFFEN (Nutzer): Promotion (b10 / b09 / keine), direkte Kanten b10 gegen b09/b02, b16 = b10 + b09-Partien, b08b, volle Breite b15 (gegen Regel). Technisch offen: `knob_registry.rs` nicht kompiliert (vor Push `cargo test --release --no-run`), Tree-Reuse-Kompilat, Tiling-Sonde, sauberer Replayer-Fix (analyze_game_log.py).** **b14b ABGESCHLOSSEN, KEIN HEBEL (13:17, par.19.4b): Schnellblick gegen b02 49:51 und 45:55, gepoolt 94:106 = 47,0 %, Block-z -0,78; Val-Brier 0,18969, Vorfilter -0,00027 [-0,00074; +0,00023]. Beide Richtungen der Mischgewichte (b14a/b14b) unter b02, die heutige Mischung bleibt. b15 (Konfidenz s = 0,01224) baut seit 13:17 Bloecke, Kettenende HERLEITUNG gegen 15:05.** **b14a ABGESCHLOSSEN, KEIN HEBEL (11:52, par.19.4a): Schnellblick gegen b02 49:51 und 49:51, gepoolt 98:102 = 49,0 %, Block-z -0,35; Val-Brier 0,18972 (schlechteste Variante), Vorfilter Brier -0,00029 [-0,00081; +0,00022], Policy-CE -0,0005 [-0,0009; -0,0001]. b14b (value-target-lambda 0,5 auf dem b03-Monolithen) trainiert seit 11:52.** **b13 ABGESCHLOSSEN, KEIN HEBEL (10:09, par.19.3a): Schnellblick gegen b02 52:48 und 53:47, gepoolt 105:95 = 52,5 %, Block-z +0,86; Val-Brier 0,18943 (= b02), Vorfilter -0,00001 [-0,00021; +0,00019]; Spalten gleichauf, Platten leicht darunter. Beste der drei Varianten, innerhalb der Aufloesung auf b02. b14a (TD_LAMBDA 0,7) laeuft seit 10:09 (Bloecke).** **NUTZER 2026-10-08 09:xx: keine weiteren Claude-Partien bis zum finalen Modell (g13/g14 dann gegen Tessa); Erlaubnisregel `python -X utf8 tools/claude_play.py:*` liegt in `.claude/settings.local.json`, damit `peek` kuenftig durchgeht.** **b12 ABGESCHLOSSEN, KEIN HEBEL (08:23, par.19.2a): Schnellblick gegen b02 50:50 und 47:53, gepoolt 97:103 = 48,5 %, Block-z -0,43; Val-Brier 0,18959 (Epoche 5), Vorfilter -0,00016 [-0,00064; +0,00032]; Vertikale je Seed rund -1,5. Gegnerstellungen heben b11 um 10 Punkte zurueck auf b02-Niveau, nicht darueber. Arm 1,72 h. b13 (Trajektorie/Rollout halb-halb) laeuft seit 08:23 (Bloecke).** **b11 ABGESCHLOSSEN MIT GEGENBEFUND (06:40, par.19.1a): Schnellblick gegen b02 38:62 und 40:60, gepoolt 78:122 = 39,0 %, Block-z -3,93 (20 Bloecke); Vorfilter Brier -0,00023 [-0,00070; +0,00027]; weniger volle Spalten (0,94/0,98 gegen 1,09/1,15), mehr Strafsteine, Vertikale -1,9 je Seed. Arm 1,71 h. b12 laeuft seit 06:40 (Bloecke).** **b11-b15 GEBAUT UND ABGENOMMEN 05:0x (par.19.5a): sechs Knoepfe, Marker in beiden Schluesseln, Standardweg bitgleich, `paired_gating.py --fixed-length`, b15-Eichung s = 0,01224 (Verbraucher-Median, n = 1.873.732), Suite 575 gruen, Konventionen gruen; `knob_registry.rs` ergaenzt, NICHT kompiliert (vor Push `cargo test --release --no-run`). Kette `tools/night_v35_b11_b15_chain.sh` LAEUFT seit 04:57:33 in Tab c9 (`& "D:\Program Files\Git\bin\bash.exe" tools/night_v35_b11_b15_chain.sh`; alles bis `e1a3cb18` committet, 16 vor origin/main); je Arm Bloecke+Merge, Training, Vorfilter, Schnellblick 2 x 50 Paare gegen b02; HERLEITUNG rund 1,9 h je Arm, sechs Trainings, Ende gegen 16:30.** **STAND 04:4x: alles bis `b35dd611` COMMITTET (15 vor origin/main, nicht gepusht). LAEUFT: Opus-Agent baut b11-b15 (par.19: trajectory_lambda, TRAJ_OPPONENT, TRAJ_MIX, MOSAIC_TD_LAMBDA, TRAJ_CONF_SCALE mit Eichung; Marker in beiden Schluesseln; Tests; Kette `tools/night_v35_b11_b15_chain.sh` mit Schnellblick gegen b02, Seeds 20261700/01 a 50 Paare), nur Dateiarbeit und Unit-Tests, keine Laeufe. Danach: Bericht pruefen (Regel 0), Suite, Standardweg-Bitgleichheit, Kette im Terminal-Tab starten (rund 1,9 h je Arm, HERLEITUNG par.19.0).** **KETTE FERTIG 04:15:47. b09 TRAEGT TOR 1 (par.17c, Lesart (a) 'Volumen traegt'): Seed 2 226:174 = 56,5 % (z +2,21, Deckel), gepoolt 390:270 = 59,1 %, Block-z +4,15 ueber 66 Bloecke, beide Seeds einzeln ueber +1,96; Punkte +2,6/+4,0, Platten +1,0/+1,3; offline Brier UND Policy-CE ueber b02. Einordnung: zwischen b02 (54,6 %) und b10 (60,9 %), b10 der billigere Hebel (0 h Erzeugung gegen rund 7 h). Arm 4,35 h ohne Erzeugung. Maschine FREI seit 04:16. Keine Promotion (Nutzer). NAECHSTER SCHRITT: b11-b15 bauen (Agent, Datenschicht, Marker in beiden Cache-Schluesseln, Tests), b15-Kalibrierung, Schnellblick par.19.0; Tiling-Sonde; Tree-Reuse-Kompilat. Offen: MOSAIC_DATA_EXCLUDE kuenftiger Pool-Ketten um ^selfplay_v34-b01-policy-s400-vol_ ergaenzen (par.17c Nachlauf).** **b09 TOR 1 SEED 1 (02:15): 164:96 = 63,1 %, SPRT-Stopp nach 130 Paaren (LLR +7,22), Block-z +4,18; Spalten 1,069 gegen 0,992, Punkte +3,99, Margin +7,97, Platten +1,30 (par.17b); 20,4 s je Partie GEBREMST (claude_play daneben bis 02:00). Seed 20261601 laeuft seit 02:15:05, Ende HERLEITUNG gegen 04:10 (ohne Nebenlast, 200 Paare).** **b09 TRAINING UND OFFLINE (00:46): Training 2.355,4 s (2,83 M Samples, +39 %), Val-Brier-Minimum 0,18880 in Epoche 3 (b02 0,18942), Policy-Val 0,4737 (b02 0,4785); gepaart gegen b02: Brier +0,00063 [+0,00008; +0,00115], Policy-CE +0,0249 [+0,0224; +0,0274], beide zugunsten b09 (par.17a; b10 lag bei +0,00066 / +0,0301). Tor 1 Seed 20261600 seit 00:46:41 (mit claude_play daneben, markieren), Seed 20261601 folgt; Ende HERLEITUNG gegen 04:45.** **CLAUDE-PLAY g11/g12 GESPIELT (02:0x, eigene Sitzung):** gegen v35-b10 @400 Claude 48:54 (Spieler 0) und 30:38 (Spieler 1); in g11 kippte die Endwertung die Partie (54:45 davor); b10 laesst wie g09/g10 Spezialfelder leer (3 und 5) und faellt in Runde 2 auf 0, zieht aber nur 8 Platten je Partie (g09/g10: 25 und 28); `peek` wurde vom Auto-Modus abgelehnt, Claude zog nie vom Stapel; Replayer-Befund (`moon_order` gegen `choose_moon_top`) mit Umgehung in `tools/claude_play.py` (uncommittet), Kennzahlen und Details `PREREG_claude_play_interface.md` par.14a. **CLAUDE-PLAY g11/g12 GESPIELT (Spiel-Sitzung, 00:27-01:59, par.14a, Kopf ENTSCHIEDEN): b10 gewinnt 54:48 und 38:30; Null-Klammer in Runde 2 (aber nur 8 Stapelzuege je Partie statt 25-28 bei v31-b01), 3 bzw. 5 leere Spezialfelder beim Netz, Marker 9 von 10 Runden beim Netz; Werkzeug-Befunde: Replayer-Divergenz bei Netz-Mondzuegen (moon_order kanonisch statt gewaehlt; Umgehung `normalize_moon_hints` in claude_play.py, sauberer Fix in analyze_game_log.py OFFEN), `peek` vom Auto-Modus abgelehnt (0 Stapelzuege Claude, `stop`-Logik im Echtbetrieb ungeuebt).** **CLAUDE-PLAY WIEDER OFFEN (00:3x):** Sicht-Audit par.11 am Code nachgelesen (P.9/P.11 netzseitig gebaut), letzte Stelle am Fenster gefixt (`tools/claude_play.py`: gezogene Stapelplatten bis `stop` nur Rueckseite, keine Nummer; 7 Tests, Datei 35 gruen), registriert `PREREG_claude_play_interface.md` par.14. **g11/g12 gegen v35-b10 spielt eine EIGENE Sitzung (Chip), Nutzer-Entscheid: darf neben der b09-Kette laufen; b09-Gating-Laufzeiten darum als 'mit claude_play daneben' markieren.**

**ARM-KETTE FERTIG 2026-10-07 07:38 (24,9 h). b08 (EMA): Einzelstand-Pfad bitgleich b02, EMA je Epoche offline besser (Minimum
0,18930 in Epoche 5), aber gespeicherter ENDSTAND 0,18967 schlechter als `_brierbest`: Vorab-Test -0,00025 [-0,00045; -0,00007],
kein Tor 1 (par.16a; Folgevorschlag b08b = EMA am eigenen Minimum, Nutzer-Entscheid). ZUSAMMENFASSUNG der Netzarme in
`PREREG_v35_window.md` par.13-16: fuenf tragen gegen v34-b01 (Fenster-Effekt), b07 nicht, b08 ohne Gewinn. LAEUFT seit 07:38:
`tools/night_v35_b09_b10_chain.sh` (Tab c6): b10 (Manifest 1.200 Traeger, Merge Schluessel `c577aaeafe38`): **Training 1.714 s, Val-Brier-Minimum 0,18877 (bestes der
Reihe), offline gegen b02 auf der b02-Maske Brier +0,00066 [+0,00030; +0,00104] und Policy-CE +0,030 [+0,028; +0,033], beide CI ueber 0
(par.18a): Policy-Kopf WAR stichprobenbegrenzt.** Tor 1 Seed 1: 185:115 = 61,7 % nach 150 Paaren (SPRT-Stopp), Block-z +4,30, Punkte +4,3 je Partie, Spalten 1,03 gegen 0,98; Seed 2 235:155 = 60,3 % (SPRT-Stopp nach 195 Paaren), Block-z +4,44; **GEPOOLT 420:270 = 60,9 %, Block-z +6,22: b10 TRAEGT, staerkste
Kante der Reihe; Lesart (a): Policy-Volumen traegt (par.18b).** b09 (frische Sockel-Partien) laeuft seit 11:25 ohne Gegenwort des Nutzers
(Erzeugung rund 1 Datei/min, 400 Dateien bis gegen 18:10, danach Bloecke, Training, Tor 1); jederzeit per Tab c6 abbrechbar, dann b09 (Erzeugung 4.000 @400, rund 7,7 h). Waehrend der Laeufe kein Commit; Registrierungen
seit `2a8d5d35` warten uncommittet.** **Zuvor: `tools/night_v35_arms_chain.sh` (Tab c4; b03 -> b05 -> b06 -> b04 -> b07 -> b08, je Bloecke/Merge,
Training, Manifest-Diff, Tor 1 gegen v34-b01 mit Stufenregel; HERLEITUNG rund 14,5 h ohne zweite Seeds, Ende gegen 21:00) und
daneben wartend `tools/night_v35_b09_b10_chain.sh` (Reihenfolge auf Nutzer-Entscheid 06:5x getauscht: b10 VOR b09; Tab neu
gestartet; startet selbst, sobald die Arm-Kette aus der Prozessliste ist; b10 rund 2,2 h, b09 rund 9,4 h). Keine Promotion
von b02 (Nutzer 06:5x: *"Promotion machen wir noch keine"*). Tree Reuse: Runde-5-Schalter `tree_reuse_round5` mit Default 1 (Nutzer 06:5x:
*"Mach den runde 5 schalter mit default an"*; `PREREG_tree_reuse.md` par.5.4 entschieden); EINGETRAGEN 07:1x im unkompilierten Entwurf (`net_mcts.rs:8255`
Ausschluss nur bei Schalter 0; Env-Default `MOSAIC_TREE_REUSE_ROUND5`, Knopfregister, `spec_env.py`, Manifest, Beispiel; docs/knobs.md 153
Knoepfe), Konventions- und Knopf-Doku-Check gruen, nichts kompiliert. Waehrend der Laeufe: keine Builds, keine Sonden, kein Commit. COMMITTET 06:3x: fuenf
Commits `fda75a63` (Bootstrap-Knoepfe), `f2aca6c5` (EMA), `a6825807` (Tree-Reuse-Entwurf, zwei Such-Preregs), `428b6e7e`
(Ketten), `2a8d5d35` (b02-Ergebnis, Arme, README); 9 vor origin/main, NICHT gepusht.**

**NACH DER b02-KETTE (01:3x bis 06:3x):** Python-Suite (unittest discover, 513 Tests) nach Korrektur der EMA-Defaults in
train.py (Literale statt Konstanten im argparse-Block und in der train()-Signatur, Waechter-assert gegen die Konstanten;
Grund: `tools/tests/source_parser.py` baut den Parser per exec nach) und Nachzug des Tests "vier atomare Checkpoints"
(`_avg`); `generate_knob_docs.py --check` gruen (152 Knoepfe); Konventions-Check gruen nach Umbenennung `vorzug` ->
`preference` im Tree-Reuse-Entwurf (`self_play.rs` neue Funktion). DANN Commit (erster seit `4d100857`) und Start von
`tools/night_v35_arms_chain.sh` (b03, b05, b06, b04, b07, b08) sowie `tools/night_v35_b09_b10_chain.sh` (wartet auf die
Arm-Kette) in Terminal-Tabs. Die Arme messen gegen v34-b01 (Baseline b02 bleibt vergleichbar); bei Promotion von b02
ist der Gegner der Arme ein Nutzer-Entscheid.

**Zuvor (Ablauf der Kette):** Smoke je Klasse -> Cache-Waechter (3 Worker) daneben -> Erzeugung policy-s400 1.000,
policy-dice-v2-r1-s400 2.000, value-deviate-s400 4.000, value-excursion-s400 4.000 (alle @400, Modus 2) -> Abnahmen par.8
GRUEN -> Fenster v35-b02 (1.200 Dateien, 400 Traeger, Val 120) -> Training v35-b02 (Seed 20260965, Brier-beste Epoche 5)
-> Tor 1. **Vorige Kette `tools/night_v35_chain.sh` 2026-10-04 19:41-23:4x: Schritte 1-5 und Tor 1 Seed 1 fertig, Seed 2 abgebrochen.** Stand 20:40:
Fenster STEHT (20:00, Maske GRUEN) und Training v35-b01 DURCH (20:37, 2.198 s, Manifest-Diff 0 unerwartet,
gegatet `v35-b01_best`, Epoche 2; `PREREG_v35_window.md` par.11a); **Tor 1: Seed 20261600 FERTIG 23:15 (208:192 = 52,0 %, Block-z +0,92, Spalten 1,078 gegen 1,128;
par.11c, gebremst durch Nutzer-Spiel neben der Arena), Seed 20261601 auf Nutzer-Entscheid ABGEBROCHEN 23:4x bei 8:12** (par.11c Nachtrag; Tor 1 b01 = ein Seed,
nicht entschieden, Seed 2 bei Bedarf nachholbar). Maschine frei. **par.11b ERLEDIGT 23:27:** Wertkopf lernt aus dem Fenster nichts Messbares (dBrier Warmstart
minus Epoche 2 +0,0006 [-0,0003; +0,0014], je Klasse kein CI ueber 0, Punktschaetzer auf dem Schwarm am groessten,
W negativ); nur der Policy-Kopf bewegt sich (+0,068 [+0,055; +0,080], am meisten auf der @400-Klasse). Hypothese
"Modus-2-Material traegt fehlende Wert-Information" NICHT gestuetzt. **Netz-Gesundheit GESUND** (23:35: keine NaN/Inf, BN-tot 0/1.120; Wertkopf Epoche 12 um 22,9 %
bewegt bei unveraendertem Brier). **par.11d (23:39): die 100-Sim-Suche ist dem rohen Netz beim Wert in Runde 1 UNTERLEGEN (diff -0,0068 [-0,0125;
-0,0009]) und bis Runde 3 nicht ueberlegen; @400 liegt sie ab Runde 2 klar vorn (+0,014 bis +0,025).** Der Kreislauf
steht, weil die Erzeugungs-Suche @100 dem Netz nichts mehr voraus hat. **OFFEN: Nutzer-Entscheid** ueber Arm v35-b02
(Fenster komplett @400 mit Modus 2 neu erzeugen, rund 14 h HERLEITUNG), Seed 2 fuer b01, oder Abschluss mit v34-b01.
Schritte der Kette:
Traeger-Manifest v35 (400 Sockel-Dateien) -> Fenster `data/window_v35.txt` (1.200 Dateien, fuenf v34-b01-Klassen)
-> Bloecke und Monolith MIT Wertmaske `MOSAIC_MASK_DICE_PHASE_VALUE=1` -> Training `v35-b01` warm von
`v34-b01_brierbest`, Seed 20260965 -> Manifest-Diff (STOPPT bei Abweichung) -> Tor 1 = Champion-Kante gegen
`v34-b01` (Seeds 20261600/01, Stufenregel 20261602, Spec `v34-b01_brierbest.spec.json` beidseits, `--log-games`).
Registrierung: `PREREG_v35_window.md` par.11 (Commit `a193b409`). Kosten HERLEITUNG rund 4,5 h. **Waehrend des
Laufs: keine Builds, keine Sonden, kein Commit.** Danach faellig (par.11): Abnahme Fenster, Netz-Gesundheit,
Tor-1-Verdikt mit Block-z, Tor 2b, sechs Kennzahlen, Elo-Register, Laufzeiten; Promotion nur nach Nutzer-Entscheid.

**Zwei Befunde beim Kettenbau (geprueft am Code):** (1) ohne Traeger-Manifest macht `corpus_dataset._is_policy_carrier`
(`corpus_dataset.py:126-158`, `carrier_set is None`) JEDE Datei zum Policy-Traeger, also auch den Schwarm; darum
traegt v35 ein Manifest mit genau den 400 Sockel-Dateien (die Uebergabe sagte "ohne Manifest", gemeint war "ohne
Alt-Generationen"). (2) `MOSAIC_DATA_EXCLUDE` ist ein Regex per `re.search` (`corpus_dataset.py:521`,
`train.py:1391`, `build_cache_incremental.py:164`); der v34-Wert als Kommaliste war ein Literal ohne Treffer, in
v34 folgenlos (die Dateiliste definiert das Fenster). v35 setzt eine Alternation mit `|`. Pitfalls-Eintrag faellig.

**Exploiter-v2 GESTRICHEN (Nutzer 2026-10-04 abends: *"streich den exploiter, sockel-manifest passt so"*;
`PREREG_asymmetric_selfplay.md` par.7c1). Traeger-Manifest mit 400 Sockel-Dateien bestaetigt.** Vorlage war:** v1 kostete 5,9 h
und kam auf 46,25 % (185:215, n = 400, gepaarte Arena @100) gegen Schwelle 55 %, Weg 1 trug nicht
(`PREREG_asymmetric_selfplay.md` par.7a/7b1); v2 HERLEITUNG rund 11 h, Vortor nach 5,5 h; v35 ist die letzte
Generation, eine korrigierte Form wuerde nie geerntet. Nutzer fragt selbst, ob der Nutzen den Aufwand rechtfertigt.

**LOESCHPROTOKOLL 2026-10-05 00:00 (Nutzer: *"freigegeben, mit Modellen"*; restic-Snapshot `46be756f` 23:57, check
ohne Fehler, 7.330 Dateien; Trefferzahlen je Gruppe im Snapshot = Dateizahl):** A `selfplay_v31-b01-*` 496,
`v32-b01-*` 496, `v33-b01-*` 1.200 (1,91 GB); B `data/probe_asym`, `probe_asym_rep`, `exploiter`, `exploiter_smoke`,
`probe_v35sockel_smoke` (1.070 Dateien, 0,90 GB; `exploiter2` gab es nicht); C sechs Monolithen der v34-Aera (2,23 GB);
D 5.058 verwaiste Bloecke (2,72 GB); Modelle `alphazero_x35-e01/02/03*`, `v34-b02*`, `v34-b03*` (44 Netzdateien, 0,30 GB;
die fuenf Trainings-Manifeste bleiben im Git). Rest in `data/`: 1.200 `selfplay_v34-b01-*`, 1.200 Bloecke, Monolithen
`.cache_ac852965e449.h5` und `.cache_81bef1158189.h5`, `frozen_substrates/`, `seed_positions/`. Offener Entscheid (c) ist
damit erledigt.

**Stand des Baums:** `a193b409`, 1 Commit vor `origin/main` (der Stand `be5bb104` wurde zwischen Uebergabe und
Uebernahme gepusht, Reflog "update by push"; nicht von dieser Sitzung). `player_profiles.json` veraendert, nie committen.

---

**UEBERGABE 2026-10-04 18:40 (ueberholt durch den Block oben; Aufgabenliste gilt weiter).**
Geprueft 18:35 damals: Geprueft 18:35: keine self_play-,
train-, paired_gating-, cargo- oder Kettenprozesse; Baum committet (`de886409`, 12 Commits vor `origin/main`, nicht
gepusht); Arbeitsbaum sauber bis auf `player_profiles.json` (nie committen). Installiertes Wheel = Stand `cb99977f`
(W-v2 plus Gegner-Sims; Anker-Drift und -Konservierung gruen 11:18, `anchor_v2_*_20261004_chain3.json`). Im
Projektordner arbeiten, KEIN Worktree (git-crypt, CLAUDE.md).

**v35 ist die LETZTE Generation** (Nutzer 12:00: *"v34 hat das projektziel bereits erreicht. ich kann das netz in den
bisherigen spielen nicht mehr schlagen"*). Abschnitt RICHTUNG. Danach Promotion (falls die Kante faellt), Tessa,
Projektabschluss nach `/mosaic-generation-turnover`. Keine v36.

**ERZEUGUNG v35 KOMPLETT UND ABGENOMMEN** (`PREREG_v35_window.md` par.9, par.10a, par.10b), Generator `v34-b01`,
alles in `data/`:

| Klasse | Partien | Dateien | Sims | Stichentscheid | Stand |
| --- | --- | --- | --- | --- | --- |
| `value-deviate` (Schwarm) | 4.000 | 400 | 100 | Bestand (Modus 0) | abgenommen par.9 |
| `value-excursion` (Schwarm) | 4.000 | 400 | 100 | Bestand | abgenommen par.9 |
| `policy` | 1.000 | 100 | 400 | Modus 2 | abgenommen par.10b |
| `policy-s100` | 1.000 | 100 | 100 | Modus 2 | abgenommen par.10b |
| `policy-dice-v2-r1` (W-v2 Runde 1, Platzsuche 600) | 2.000 | 200 | 100 | Modus 2 | abgenommen par.10b |

Rezepte `models/v35.recipe.json` (Schwarm) und `models/v35_sockel.recipe.json` (Sockel). Nutzer-Entscheide dazu:
Schwarm bleibt wie erzeugt (11:35); Mischsockel statt rein @400, weil @400 nachweisbar 0,07 volle Spalten je Seite
verliert (par.8c1 der Asym-Prereg); W mit Basis 100 und Platzsuche 600 (13:30); Exploiter bleibt AUSSEN VOR (15:20).

**ERSTE AUFGABE DER NEUEN SITZUNG (Reihenfolge; alles CPU bzw. GPU, Maschine seit 18:00 frei):**
1. **Fenster bauen** nach `PREREG_v35_window.md` (par.1: Schwarm 8.000 + Sockel 4.000, G-1/G-2 fallen weg,
   `PREREG_asymmetric_selfplay.md` par.4a) auf dem Muster `tools/night_v34_chain.sh` Z. 38-135 (Env, Fensterliste,
   `window_train_split.py`, `build_cache_incremental.py`): neue Kette `tools/night_v35_chain.sh` als Datei, ohne
   Traeger-Manifest (keine Alt-Generationen), Val-Pool `^selfplay_v34-b01-`, `MOSAIC_DATA_EXCLUDE` um alle Sonden-
   und Probe-Praefixe (`selfplay_probe-`, `selfplay_x35`, `selfplay_x35e2`) erweitern, Datenordner `data/` (NICHT
   `data/probe_asym`, `data/exploiter*`, `data/probe_v35sockel_smoke`). **Vor dem Lauf registrieren** (par.11 der
   v35-Prereg): Fensterliste, Val-Frac, Trainings-Seed (Vierer-Schritt nach `docs/generation_loop.md`; v34 hatte
   20260961, also 20260965, pruefen), und die **Wertmaske der Wuerfelphase** `MOSAIC_MASK_DICE_PHASE_VALUE=1`
   (par.5d Records: Wertziele beider Seiten in Runde 1 der W-Partien maskiert; Knopf in corpus_dataset.py und
   train.py, beide Cache-Schluessel, gebaut 2026-10-03). Abnahme: Fensterliste 1.200 Dateien, keine Sonden-Datei
   darin (grep), Cache-Schluessel traegt die Maske.
2. **Training `v35-b01`** warm vom Generator (`--load v34-b01_brierbest`), Flags wie `models/manifest_train_v34-b01_20261001_183258.json`
   `cli_args` (12 Epochen, lr 5e-5 cosine `--lr-t-max 12`, WDL, nortv, lambda 0,7, `--select-by-brier`,
   `--fast-loader`), Kosten rund 1 h (GPU). Abnahme: Manifest-Diff gegen v34-b01 (nur erwartete Felder), Netz-
   Paritaets-Fixture, Diagnostiken wie `docs/promotion_checklist.md`.
3. **Tor 1** gegen `v34-b01` (Generator = Champion): `tools/paired_gating.py`, Seeds nach v34-Muster (par.2 der
   v34-Prereg: zwei Seeds a 200 Paare, Blockgroesse 5, `--log-games`, Spec `models/v34-b01_brierbest.spec.json` auf
   beiden Seiten), Stufenregel; Tor 2a/2b (Spalten) wie dort. Rund 1,6 h je Seed. Vorher die Tore in par.11
   registrieren.
4. **Bei bestandener Kante:** `/mosaic-champion-promotion`, dann Tessa und `/mosaic-generation-turnover`.
5. ~~Exploiter-v2~~ GESTRICHEN (Nutzer 2026-10-04 abends; `tools/night_v35_exploiter2_chain.sh` ist Loeschkandidat, `PREREG_asymmetric_selfplay.md`
   par.7c, rund 5,5 h bis zum Vortor, 11 h gesamt). Startbefehl im Terminal-Tab (2-h-Grenze der
   Hintergrundaufgaben; Git-bash aus `Git/bin/bash.exe`).

**Nutzer-Freigaben und Verbote (woertlich bzw. stehend):** *"committe sobald es moeglich ist"* (2026-10-01; committen
ja, pushen nein). **Kein Push ohne Anweisung.** Nie committen: `player_profiles.json`, `player_profiles.json.bak`.
Loeschungen nur mit restic-Beleg UND pfadgenauer Freigabe. Messungen exklusiv, ein Build ist Last, kein Commit
waehrend eines Wanduhr-Laufs. *"lass den exploiter noch aussen vor"* (15:20). Subagenten Opus medium, Befunde
nachpruefen; Koordinator baut nichts selbst (Nutzer 2026-10-04 00:00). Lange Ketten im Terminal-Tab starten.

**Offene Nutzer-Entscheide:** (a) ~~Exploiter-v2~~ GESTRICHEN 2026-10-04 abends (par.7c1);
(b) nach Tor 1: Promotion und Projektabschluss; (c) Reste in `data/probe_asym` (Sonden), `data/exploiter`,
`data/exploiter_smoke`, `data/exploiter2` (leer), `data/probe_v35sockel_smoke`, Modelle `alphazero_x35-e01/02/03*`:
Loeschung nur auf Freigabe mit restic-Beleg; (d) Server-Neustart fuer v34-b01 in der GUI (seit 2026-10-03 offen).

**Befunde des Tages, registriert (Kurzform; Details in den Preregs):** Q-Stichentscheid der Erzeugungs-Zugwahl
gewinnt 75 % gegen den Bestand (`PREREG_asymmetric_selfplay.md` par.5e2/5e3, `docs/pitfalls.md`); @400 mit Modus 2
verdoppelt die KL bei gleichen Punkten, verliert aber 0,07 volle Spalten (par.8b1/8c1; Sims-Kurve par.8e der
Sims-Prereg ist mit Modus 0 gemessen, par.8f dort); W-v2 Runde 1 traegt (par.5d3a/b: G-KL +0,054, kein Versatz,
W 44,5 %); Stoerer, Exploiter v1 (46 %), v32 als Gegner tragen nicht (par.5c3, 7a, 7b1).

**Betriebsbefunde:** Hintergrundaufgaben enden nach max. 2 h, danach scheitern NEUE Subprozesse der verwaisten Kette
mit 0xC0000142 (Memory); zwei Netze je Partie kosten 6,1 statt 2,9 s; Zyklus-Basis-Seeds brauchen Abstand >= Chunkzahl.

**FERTIG 2026-10-03 10:01: v35-Schwarm** (`tools/night_v35_swarm.sh`,
`PREREG_v35_window.md`): `value-deviate` 05:19-08:06 und `value-excursion` 08:06-10:01, je 4.000
Partien in 400 Dateien (`data/selfplay_v34-b01-value-*`), beide Exit 0, keine Watchdog-, Deadline- oder
Haenger-Zeile. Smoke vorher gruen (Waechter 6 Knoepfe, Manifest traegt `r5_net_sims` 400), Tages-Snapshot
`b39f5a06`. Abnahmen alle GRUEN (par.9).

**FERTIG 2026-10-03 05:11: Promotion v34-b01** (`PREREG_v34_window.md` par.10e): Replikation 285:115
(z +10,00), Anker 45:5, Champion-2 gegen v31-b01 108:42; Elo 1595 [1546; 1646]; Diagnostiken gepaart
gegen v32 (R5-Daempfung 0,177 -> 0,272, Brier-Regel haelt, sigma/Prior 1,54); Artefakt mit Golden
Probe und Selbsttest gruen. 5d Paritaets-Fixture nach der Erzeugung von Hand nachgezogen
(`34cf8da5c17b04d3`, frischer Prozess gruen; der Kettenlauf war an der PATH-Form in Git-Bash
gescheitert). **Offen fuer den Nutzer:** Server-Neustart (Champion, Spec, Anzeige-Kalibrierung). **Nebenlast-Vermerk:** die drei Register-Eintraege
(`elo_tracker.py add`, je rund 2-3 min Fit) liefen rund 05:12-05:21 parallel zu Smoke und den ersten
Minuten der Erzeugung (gemeldet; Erzeugung ist kein Messlauf mit Stoppregel, Wirkung hoechstens
einzelne Chunk-Zeitlimits; geprueft: keine Watchdog-, Deadline- oder Haenger-Zeile in der Ausgabe).

**UEBERGABE-STAND 2026-10-02 21:50 (Nutzer startet die Maschine neu; NICHTS laeuft).** Letzter Lauf:
R5-A/B 400 gegen 200 am Erzeugungspunkt, vollstaendig (800 von 800 Partien), registriert
(`PREREG_r5_net_vs_solver.md` par.6h, 435:365, z +3,90): **v35 faehrt Runde 5 per Netz mit 400 R5-Sims**;
die Prereg ist geschlossen. Server-Paket aus Code-Review 2 getestet und committet.

**v34 ist entschieden:** kein Arm traegt (E2 395:405 z -0,36, E4 413:387 z +0,96; `PREREG_v34_window.md`
par.10b/par.10c). **NUTZER-ENTSCHEID 2026-10-02: `v34-b01` wird promoviert** (par.10d), als Paket der
Kante par.2a: `v34-b01_brierbest` mit `models/v33_gating_r5net.spec.json`, Kante gegen v32-b01
239:121, Block-z +7,37.

**Nach der v35-Erzeugung, in dieser Reihenfolge (alles CPU, darum erst dann):**
1. ~~Abnahmen der Erzeugung~~ ERLEDIGT 2026-10-03, alle GRUEN (`PREREG_v35_window.md` par.9).
2. ~~Offline-Pruefung par.7a~~ ERLEDIGT 2026-10-03 (`PREREG_targeted_branching.md` par.7d): E = +0,00124
   [-0,00014; +0,00270], kein zuordenbarer Lerneffekt, Prereg geschlossen.
3. ~~Sechs Kennzahlen E2/E4~~ ERLEDIGT 2026-10-03 (`PREREG_v34_window.md` par.10f);
   `PREREG_evaluator_pretests.md` geschlossen (par.8e).
4. ~~Code-Review 2, Paket Messkette~~ ERLEDIGT 2026-10-03.

**Erledigt 2026-10-02** (Belege in den Preregs): Promotions-Kante v34-b01 (par.2a); Wheel-Runde A
(Schrittlimit statt Wanduhr, `completed` in der Arena, `r5_net_sims`); E2/E4 gebaut, trainiert, gesund,
A/B (par.10-10c); R5-Reihe am Erzeugungspunkt: Netz @400 in Runde 5 (`PREREG_r5_net_vs_solver.md`
par.6e-6g); R4-Substrat eingefroren; `v33_window` und `tie_mirror` geschlossen.

**Erledigt im Wechsel am 2026-10-01** (alles exklusiv, alles committet):
* Anker-Invarianz gegen `hv4_anchor` auf Wheel 1.1.0 (`1a9e4bac...`): Drift und Konservierung gruen.
* R5-Kalibriersonde (`PREREG_r5_net_vs_solver.md` par.6b): beim heutigen Loeser frisst das erste
  Kind das Budget in 86 von 117 Entscheidungen; iterativ @2000 129 ms Median je Entscheidung.
* Smoke des v34-Rezepts (`PREREG_v34_window.md` par.7a): erst ROT (Waechter-Erwartung rezeptweit),
  dann Erwartung je Klasse gebaut, gruen in allen drei Klassen.
* Kostentor der Erzeugung (par.8a): Runde 5 per Netz +11,5 % je Partie (2,727 gegen 2,446 s).
* v33-Kontrolle der Offline-Pruefung (`PREREG_targeted_branching.md` par.7b): DiD(v33) -0,00071
  [-0,00160; +0,00020].
* Generator `v33-b01` eingefroren (`models/frozen_champions/v33-b01`, am 2026-10-03 geloescht, restic `4c985a1f`; Golden Probe,
  Referee-Selbsttest gruen); restic daily `a3755374` mit Pruefung; Aufraeumen A-H mit Freigabe
  (`data/` 9,5 -> 2,0 GB, Liste im Generationsbericht v33).


**Review-Rest EINGETAKTET** (Nutzer 2026-10-01: *"takte #11, #12, #15 und den Rest von #23 aus dem
code review ein"*; Befunde `review/code_review_2026-09-26_verification.md`). Am Code geprueft
2026-10-01: `corpus_io.dump_records` ist schon atomar (`corpus_io.py:87-112`); offen sind
(a) `train.py` Endstaende nicht atomar (der Ueberschreib-Waechter `--overwrite-model` steht schon seit
`b00a9e09`, `train.py:1133-1150`; die Notiz vom Vormittag war falsch) -- GEBAUT 2026-10-01: `save_checkpoint_atomic`, (b) Cache-Schluessel ohne Inhaltsmerkmal (`engine/py/file_cache_key.py:84-222`),
(c) Panic im Netz-Self-Play als "[Watchdog] ... Deadline" gemeldet (`self_play.rs:7099-7103`, `:7217`).
* **Python, vor dem v34-TRAINING:** (a) ERLEDIGT 2026-10-01 (`save_checkpoint_atomic`, Test in
  `tools/tests/test_train_recipe.py`). (b) **ENTSCHIEDEN 2026-10-02 (Nutzer: *"ja, so einplanen"*):** die
  DATEIGROESSE kommt in den Block-Schluessel (`engine/py/file_cache_key.py::per_file_cache_key`, als
  versionierter Marker wie `|finalmargin_v1`), billigste Form, kein Inhalts-Hash. Eingebaut wird es
  beim NAECHSTEN Generationswechsel, wenn die Bloecke ohnehin neu gebaut werden (`/mosaic-generation-turnover`),
  nicht vorher. Begruendung: Self-Play-Dateien tragen einen Zeitstempel im Namen, ein Ersetzen unter
  gleichem Namen kommt praktisch nicht vor; der Schaden waere ein still veralteter Block.
* **Engine, in der Wheel-Runde nach der Erzeugung mit E4:** #11 `opp_points` in
  `try_batched_pair_ex` (`net_mcts.rs:3357-3359`), #12 ORT-Registry-Schluessel (`net_ort.rs:201`,
  nur Feature `ort_cuda_probe`), #15 Batcher-Registry (`net_batcher.rs:272-301`), (c) Panic ehrlich
  melden. #11/#12/#15 latent (Knoepfe/Feature aus), keine Wirkung auf die v34-Erzeugung.
* **Partie-Zeitlimit ersetzen** (Nutzer 2026-10-01: *"takte das fuer die Wheel-Runde ein. vielleicht
  gibt es auch einen besseren weg. der waechter ist eigentlich ein artefakt aus fruehen zeiten"*).
  Befund, am Code gelesen: die Arena-Partie (Tor 1, alle A/B) hat ein Wanduhr-Limit
  `net_game_timeout_secs(max Sims)` = 0,45 s je Sim, bei 400 Sims **180 s**, ohne Zuschlag
  (`self_play.rs:5833`, `:89-90`); wird es erreicht, bricht die Schleife ab (`:4354`), die Endwertung
  entfaellt (`:4945-4947`), und die Partie geht OHNE Markierung mit dem Zwischenstand in die Wertung
  (Summary traegt kein `completed`, `paired_gating.py` prueft nichts). Im Self-Play gibt es
  `completed: false` und den harten Waechter (+60 s, `:6982-6984`). In allen 15 registrierten
  Arena-Artefakten seit v33 (5.890 Partien) hat jede Partie 5 Runden abgerechnet (`floor_per_round`,
  `round_end.rs:451`): bisher kein Abschnitt. Vorschlag: (1) deterministisches Schrittlimit statt
  Wanduhr (der Zaehler `guard` steht schon in der Schleife; normale Partie rund 200 Schritte),
  (2) Wanduhr nur noch als grosszuegiger Haenger-Alarm, der den Lauf laut abbricht statt zu werten,
  (3) `completed` ins Arena-Ergebnis, `paired_gating.py` zaehlt unvollstaendige Partien und bricht ab.
  HERLEITUNG, ungeprueft: die Wanduhr ist ein Weg, ueber den CPU-Last Partien lastabhaengig
  verstuemmelt (CLAUDE.md, Signatur "Endstand 3:1"). Anker-Invarianz danach Pflicht (der Anker-Lauf
  geht durch dieselbe Schleife).

**Code-Review 2 EINGETAKTET** (Nutzer 2026-10-02: *"ja, so eintakten"*; Dokument "Code-Review
mosaic-AI: Grenzfaelle" auf `2d49b24`, 22 Befunde, ✔ = vom Review-Autor am Code gelesen, ◐ =
Agenten-Befund). #1 am Code nachgelesen (`train.py:2879-2881`: `_brierbest` nur, wenn die
Brier-beste Epoche weder die letzte noch `best_epoch` ist). Reihenfolge:
* **Sofort, ohne Bau:** bei den A/Bs von E2/E4 das gegatete Netz aus den Logzeilen ("Value-optimales
  Modell", "Bestes Modell (Epoche ...)") bestimmen, nie aus dem Dateinamen raten (#1).
* **Paket Messkette (#1 bis #7) ERLEDIGT 2026-10-03** (Commit `f6b19328`): `tools/brier_best_checkpoint.py`
  bestimmt das Brier-beste Netz aus dem Trainings-Manifest (#1; trifft v34-b01/b02/b03 und v33-b01);
  #2 ist durch die Bauform der neuen Ketten (Exit-Pruefungen) erledigt, `night_v34_chain.sh` ist
  v34-gebunden und Loeschkandidat; Block-z ohne Division durch null (#3), `validate_gating_params` (#4),
  `train.py` bricht bei `n_batches == 0` ab (#5), Resume-Fingerabdruck um 15 Verlust-/Kopf-Knoepfe (#6,
  nur bei Abweichung vom Default), #7: Rezept lehnt NaN/Infinity ab, pre-push mit `core.quotePath=false`
  und vollem Test bei Aenderungen an `engine/Cargo.*`/`examples`/`benches`/`tests`, GUI-Badge ohne
  Scheinwert fuer ungeschlagene Knoten. Tests `tools/tests/test_review2_measurement_chain.py` (8).
* **Paket Server (#8 bis #15) ERLEDIGT 2026-10-02** (Nutzer: *"ja, mach das Server-Paket"*; Tests
  `tools/tests/test_server_edge_cases.py` 11 gruen, nach der Arm-Kette gelaufen): `server.py` baut neue
  Partie und Replay erst lokal und stellt die Globalen in einem Zug um (#8, #13), `_json_body`
  (#12), `_human_turn_guard` in allen Drafting-Routen und Startplatten-Pruefung (#9),
  `_tiling_player` mit Server-Merker `_tiling_ended` (#10, Engine-Teil bleibt Wheel-Runde),
  Chip-Rumpf im try (#11), `OverflowError` bei `Infinity` (#12), Namen bereinigt und verschieden
  (#14), KI-Sperre auch um new_game/replay, eindeutiger Logname, Schreibsperre in
  `player_profiles.py` (#15). #16 (`json_to_state`) ist Engine und kommt in die naechste Wheel-Runde.
* **Wheel-Runde:** #20 (Stufe-3-Arena in `tools/arena.py:531` noch mit 3600-s-Wanduhr, ohne
  `completed`), #21 (Env-Parser), #22 (Engine-Raender). Fuer die laufende R5-Reihe geprueft: alle
  vier Leiter-Specs setzen `r5_net_solver: 0` zusammen mit `r5_net_sims`, #22 trifft sie nicht.
* **Nur nach Nutzer-Entscheid** (Anker oder Regeln): #17 (Loeser-Prognose ohne Untergrenze 0), #18,
  #19; danach `/mosaic-anchor-invariance`. Die zwei Regelfragen des Reviews sind entschieden
  (Kappung erst nach der Plattensumme, `docs/engine_manual.md` Abschnitt 6; Startspielerstein in
  Runde 5: kein Befund).

**R5-Reihe** (`PREREG_r5_net_vs_solver.md` par.5b, Nutzer 2026-10-01, 400 gegen 400): Stufe 2
(Spielpunkt) ENTSCHIEDEN, das Netz schlaegt auch den iterativen Loeser @400 (320:480, Block-z -7,32
fuer den Loeser, par.6d). Fuer das SELF-PLAY gelaufen 2026-10-02 08:39-11:07 (par.6e/par.6f, Generator
`v34-b01`): das Netz spielt Runde 5 auch am Erzeugungspunkt (2E 302:498 fuer den Loeser, z -9,74), und
zwar mit **400 statt 100 R5-Sims** (2E-b 464:336, z +7,56); die Sim-Leiter senkt mit mehr R5-Suche die
Self-Play-Punkte beider Seiten (gegenseitig haerter, nicht schwaecher), Knick 200-400, ab 400 flach.
Gilt ab v35. 400 schlaegt auch 200 (435:365, z +3,90, par.6h); Kosten @400 +19,2 % je Partie (par.6g);
Folge fuer Tor 2a v35 gegen v34 (wieder ungleich bedingt): `PREREG_v34_window.md` par.9a Nachtrag.

**NACH dem v34-Training: asymmetrisches Self-Play** (Nutzer 2026-10-01: *"prinzipiell wuensch ich
mir mehr asymetrisches self play um bewusst stellungen zu provozieren die nicht entstehen wenn du
gegen dich selber spielst"*). Entwurf `PREREG_asymmetric_selfplay.md`: Wuerfel-Klasse W festgelegt
(ALLE Platten der Wuerfel-Seite gewuerfelt, Quelle/ID bzw. Stapeltiefe d in 1..max mit Obergrenze 7 in Runde 2 und 3 in Runde 3/Rotation, Platz
per Suche @600, erzwungene Zuege ohne Record, alle Wertziele bleiben, Start normal); Stoerer-Klasse
S skizziert (lambda_aggr je Seite, Records beider Seiten, Stoerer-Policy nur bei fast gleichwertigem
eigenem Wert). Ziel-Zusammensetzung (Nutzer 2026-10-01, W-S am 2026-10-03 gestrichen): Sockel 3 x 2.000 (G-G, G-W, G-S),
Schwarm 4.000 Weg C plus 4.000 Ausflug, G-1/G-2 fallen weg; grob 12 h (HERLEITUNG); endgueltig nach
den Sonden S1-S4 (par.4). Bau in der Wheel-Runde nach der v34-Erzeugung.

### RICHTUNG (Nutzer-Entscheid 2026-09-27)

**NUTZER 2026-10-04 abends (waehrend Tor 1 bei 90:80 stand): *"ich will v35 noch staerker hinbekommen als v34"*.**
v35 bleibt die letzte Generation, aber mit dem Anspruch, die Kante gegen v34-b01 zu nehmen; weitere Arme (b02 ...)
sind damit Teil von v35. Hebel-Reihenfolge nach Beleglage (Koordinator, Vorlage): erst Tor 1 und par.11b lesen
(lernt der Wertkopf aus Modus-2-Material?), dann ggf. Schwarm mit Modus 2 neu erzeugen (Nutzer-Entscheid, rund
4,7 h HERLEITUNG aus par.9-Laufzeiten), Fenster nur aus Modus-2-Material; Rezept-Knoepfe (lr, Epochen, Kaltstart,
Kapazitaet) sind nach Memory und Kurven KEIN Hebel.

**NUTZER 2026-10-04 12:00: v35 wird WIRKLICH die letzte Generation.** *"v34 hat das projektziel meiner meinung nach
bereits erreicht. ich kann das netz in den bisherigen spielen nicht mehr schlagen."* Folge: v35 ist die
Abschluss-Generation (Sockel @400 Modus 2, Schwarm wie erzeugt, W/Exploiter nur falls sie ihre Leseregeln bestehen);
danach Promotion (falls die Kante faellt), Schlussmodell Tessa, Projektabschluss nach `/mosaic-generation-turnover`.
Keine v36.

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

**Champion laut `models/champion.txt`: `v34-b01_brierbest`** (Promotion 2026-10-03), Spec
`models/v34-b01_brierbest.spec.json` (Startkuppel-Suche, Runde 5 per Netz), nach aussen **Tessa**
(Anzeigename in `static/js/app.js`). **Elo 1595 [1546; 1646]** aus 960 Partien im Leitersegment 2,
Anker `hv4_anchor` fix 1000. Herleitung: `PREREG_v34_window.md` par.10e. Der Server zieht Champion,
Spec und Anzeige-Kalibrierung erst nach einem Neustart.

| Modell | Elo | KI95 | Partien |
| --- | --- | --- | --- |
| **v34-b01@400 (Champion, Tessa)** | **1595** | **[1546; 1646]** | **960** |
| v32-b01@400 (Vorgaenger) | 1460 | [1416; 1507] | 4.960 |
| v31-b01@400 | 1433 | [1392; 1476] | 1.950 |
| Heuristik_hv4_anchor@150 (Anker) | 1000 | fix | |

Stand 2026-10-03 05:2x (`python tools/elo_tracker.py report`, 87 Zeilen). Zwei der fuenf Kanten von
v34-b01 sind frueh gestoppt (die Promotions-Seeds); die Replikation bis zum Deckel traegt (Block-z +10,00).

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

## 5. PREREG-BESTAND (Stand 2026-10-03: 3 OFFEN; Ziel rund 7)

`v33_window`, `tie_mirror` und `r5_net_vs_solver` am 2026-10-02 geschlossen (Nutzer; Spiegelknopf bleibt fuer v35 an,
als Diversitaets-Mittel, `PREREG_tie_mirror.md` par.4b); `v34_window`, `targeted_branching` und `evaluator_pretests` am 2026-10-03.

| Prereg | Was noch aussteht |
| --- | --- |
| `v35_window` | Schwarm erzeugt und abgenommen (par.9); Sockel-Rezept als Entwurf (`models/v35_sockel_draft.recipe.json`), Entscheid Stichentscheid Modus 2 / Sims / W; Fenster, Arme, Tore |
| `asymmetric_selfplay` | Sonden alle gefahren (par.5a-5e3, 7a, 8a); offen nur die Zusammensetzung des v35-Sockels (Nutzer) |
| `difficulty_levels` | ganze Leiter auf den letzten Champion vertagt |

## 6. OFFENE NUTZER-ENTSCHEIDE

1. ~~Promotion v34-b01~~ ENTSCHIEDEN 2026-10-02 (ja, `PREREG_v34_window.md` par.10d); Ablauf nach dem
   Neustart, Abschnitt 1.
2. ~~Loeschfreigaben~~ ERLEDIGT 2026-10-03 (Nutzer: *"erteilt"*): `frozen_champions/v31-b01` und `v33-b01`,
   `data/selfplay_v30-b02-policy_*` (400), `data/probe_r5sims` (44), `probe_r5cost` (33), `probe_v35smoke` (6);
   je Gruppe Trefferzahl = Dateizahl in restic `4c985a1f` (2026-10-03 11:15), keine Links.
3. **Code-Review 2, nur nach Entscheid:** #17 (Loeser-Prognose ohne Untergrenze 0), #18, #19
   (Anker- bzw. Regelpfad, danach Anker-Invarianz).
4. ~~Asymmetrisches Self-Play, offene Fragen~~ ENTSCHIEDEN 2026-10-03 (`PREREG_asymmetric_selfplay.md`
   par.3a, F6 abweichend: Platzsuche deterministisch). Naechster Schritt: Bau (Bauplan
   `asymmetric_selfplay_build_plan.md`), dann Sonden S1-S4.
6. **Asym, nach S5/S4b neu:** Zusammensetzung des Sockels (policy / Eroeffnungs-W / Stoerer B) und
   Sockel-Rezept der v35-Erzeugung; Zugwahl-Stichentscheid der Erzeugung untersuchen? (par.5e).
5. **Aeltere, weiterhin offene Punkte** (Wortlaut im Archivkapitel vom 2026-10-01, Abschnitt 6):
   Budget-Knopf fuer die Hilfsknoten (Wirkung ungemessen); Gruppe B des Aufraeumens (Wrapper
   `resolve_and_apply_stack_draw`, drei Spec-Felder in `KNOWN_FIELDS`); R5/R4b-Sonden der
   Promotionsliste Pflicht oder je Promotion; Brier-Regel gegen `frozen_eval_set` aus aelterer
   Verteilung; Sichtluecke bei gezogenen Stapelplatten (`stack_top_feature` par.16/16a);
   Paritaets-Tor und Alt-Records (`rust_data_layer` par.9/9a); drei Sonden zeigen auf das
   geloeschte `hv1_anchor`; `-Deep`-Lauf der Backup-Verifikation (zuletzt 2026-10-01 wieder nicht
   gefahren); Dry-Artefakte `evaluations/artifacts/_dry_*.json`.

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
  die VOLLENDUNG. **Gemessen mit Bestands-Stichentscheid (Modus 0); mit Modus 2 ist @400 gegen @100 in der
  Vollendung gleich (par.8b1, 2026-10-04), die Kurve ist neu zu bewerten.**
- **Kein zurueckgehaltener Satz der laufenden Aera** (jede Datei liegt in mindestens einem Fenster).
- **Pfadform der Dateiliste im Cache-Schluessel:** Normalisierung auf Basenames entwertet jeden
  Monolithen; Nutzer-Entscheid an einem Generationswechsel (passt zu Review #23b).
- **Python-Werkzeuge nach einem Kontraktwechsel:** `tools/offline_diagnosis.py`,
  `tools/oracle_metrics.py` und `tools/probes/*_gate.py` uebergeben `num_actions` explizit.
- **Der heutige R5-Loeser entscheidet meist per Vorsortierung** (86 von 117, par.6b); das Label am
  Uebergang Runde 4 -> 5 (`exact_round5_outcome`) laeuft weiter ueber ihn, auch in der v34-Erzeugung.
- `player_profiles.json` im Arbeitsbaum veraendert (Server-Seite), nicht committet.
