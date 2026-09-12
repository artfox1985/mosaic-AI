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

## 1. STAND (2026-09-13, 01:10; Sitzung uebernommen 00:11, Treppe gefestigt, Sims-Neumessung vorregistriert)

**Champion laut `models/champion.txt`: `v28-b02_brierbest` (Promotion 2026-09-12), Elo 1353
[1306, 1402]** aus 1.410 Partien im LEITERSEGMENT 2 (Stand 01:00, 36 Kanten, alle am Anker
`hv4_anchor` fix 1000, Block-Bootstrap; `python tools/elo_tracker.py report`): v28-b01 1326,
v27-b01 1310, v26-b01 1255, v22-b05@400 1213, v24-b07 1207, v21 1204, v22-b05@100 1173,
v28-b02@100 1146 (Intervall degeneriert, 30 Partien), v22-b05@25 1103, hv4_anchor@600 1046,
hv2 983, hv3 978. **Die Treppe Anker -> hv4@600 -> v22@25 -> v22@100 -> v22@400 traegt** (jeder
Knoten mindestens zwei Kanten am Deckel ohne Frueh-Stopp; `PREREG_code_cleanup_closeout.md` par.7a
Nachtrag "TREPPE GEFESTIGT", Endtabelle dort). Generator v29 = v28-b02 (Nutzer 2026-09-11). Alle
v28-Messungen registriert; der Generationswechsel v28 -> v29 (`/mosaic-generation-turnover`) ist
NICHT begonnen.

### MASCHINE FREI (seit 00:59)

`tools/night_ladder_gap_fill.sh` ist durch (00:03-00:59, acht Artefakte, vier Kanten im Register).
Kein Lauf aktiv. **Bereit, Start auf Anweisung:** `tools/night_sims_curve_v28b02.sh` (Sims-Kurve am
Generator v28-b02, `PREREG_search_depth_column_optimum.md` par.8e: Teil A gepaart @100/@200/@600
gegen @400 je 75 Paare ohne Frueh-Stopp mit Spaltensonde und Plattenpunkten, Teil B argmax
@100/@200/@400/@600 je 200 Partien; rund 2,5-3 h, ANNAHME). Vorher laeuft der Crosscheck am
Spiellog (unten), weil eine deterministische Sonde nicht neben einer Messung laufen darf.

### NAECHSTE SCHRITTE (Reihenfolge)

1. **Crosscheck Fliesenbuchhaltung** (Nutzer 2026-09-13, 01:05): am Server-Log
   `static/log/game_20260911_092554_seed946607.log` pruefen, ob sich je Zug die Fliesen je Farbe
   auf Brett, im Beutel und im Turm aus dem oeffentlichen Spielverlauf mitrechnen lassen (Ledger
   gegen Engine-Replay, `tools/analyze_game_log.py --dump-states`). Ergebnis in
   `PREREG_stack_top_feature.md` (P.9) nachtragen.
2. **Sims-Kette starten** (par.8e), danach Auswertung nach der Lesart dort und der VORSCHLAG fuer
   die Sims von Sockel und Schwarm getrennt, mit Kosten je Variante fuer v29 UND v30 (Nutzer:
   "zum schluss sind es nur noch zwei generationen"; Entscheidungsregel "eklatant" in par.8e).
3. **Generationswechsel v28 -> v29** nach `/mosaic-generation-turnover`, NUR auf Anweisung; darin
   der Bau des Sicht-Arms v29-b03 (P.3 Ziehserie, P.7 Phasenaufloesung, P.9 als Vorschlag;
   `PREREG_stack_top_feature.md` par.13, `PREREG_v29_window.md` par.6c) VOR dem Start der
   Erzeugung (Wheel-Wechsel); Loeschliste des Nutzers erst nach dem Start des v29-Self-Plays.
4. ~~Vier Preregs koennen schliessen~~ ERLEDIGT 2026-09-13, 01:15 (Nutzer: "schliess auch die 3
   preregs"): `v28_window`, `dome_stack_information_sets`, `start_dome_choice` auf ENTSCHIEDEN;
   `stack_top_feature` bleibt OFFEN (Sichtgleichheit nicht erreicht, par.13). Index: 11 OFFEN.

### FREIGABEN UND VERBOTE (woertlich vom Nutzer)

- **Kein Push ohne Anweisung.** Ahead-Stand im Chat melden (Nutzer pusht selbst).
- **Loeschung nur auf pfadgenaue Freigabe.** Freigegebene Loeschliste (Nutzer 2026-09-12, 23:58:
  "ich heb mir nur die letzten zwei champs auf. und hv1 ist obsolet. somit brauchen wir nur v28 und
  v27"), aber **"wir loeschen es erst wenn das self play fuer v29 gestartet ist. dann ist es im
  restic daily"** (00:05): `models/frozen_champions/v21_2d_brierbest/`, `v24-b07/`, `v26-b01/`,
  `models/frozen_heuristics/hv1_anchor/`, `models/restored_v24/`. Der Nutzer loescht selbst; die
  Sitzung traegt danach Snapshot-ID und Loeschung in Chronik und STATUS ein und zieht die
  Text-Verweise auf `hv1_anchor` nach (CLAUDE.md Abschnitt Anker-Invarianz, `docs/working_rules.md`
  Z.50, `docs/generation_naming.md` Z.68, `docs/architecture_reference.md` Z.39, Docstrings
  `tools/verify_frozen_heuristic.py` Z.31/33 und `tools/anchor_arena.py` Z.8, Skill
  mosaic-anchor-invariance). Regel dazu im Turnover-Skill Schritt 5 aktualisiert.
- **Messungen laufen exklusiv**; GPU und CPU duerfen parallel, zwei CPU-Messungen nicht; Builds
  zaehlen als Last.
- **v29-Erzeugung nur auf Anweisung.** Generator v28-b02.
- **Nie committen:** `player_profiles.json`, `player_profiles.json.bak`.
- **Regel 0**, Prereg-Kopf im selben Zug wie das Ergebnis, Laufzeiten ins Artefakt, kein U+2014
  in Dateien, Bezeichner englisch.

### OFFENE NUTZER-ENTSCHEIDE

- **Sims der v29-Erzeugung: Neumessung VORREGISTRIERT und gebaut** (Nutzer 2026-09-13: "dann also
  beide ... miss nur bei 100 sims, 200, 400 und 600"; `PREREG_search_depth_column_optimum.md`
  par.8e, Kette `tools/night_sims_curve_v28b02.sh`). Entscheidungsregel des Nutzers dort woertlich
  ("eklatant besser" -> hoehere Erzeugungszeit in Kauf); faellt die Kurve fuer hoehere Sims aus,
  wird auch der Sockel des v29-Fensters mit den hoeheren Sims erzeugt (Kosten vorher in
  `PREREG_v29_window.md`). Pflicht-Auswertung: Vorschlag Sims Sockel/Schwarm getrennt.
- **P.9 (Turm je Farbe) im Sicht-Arm v29-b03 mitbauen?** (`PREREG_v29_window.md` par.8 Punkt 5)
- **Zweite Aufhaengung der Sims-Kante am Champion:** v28-b02@100 hat nur 30 Partien (Intervall
  degeneriert); mehr Partien nur, wenn der Knoten gebraucht wird.
- Generationswechsel-Start (Schritt 5 oben), Loeschzeitpunkt (nach Self-Play-Start).

### BEFUNDE, die eine Nachschau brauchen

- **Nicht-Transitivitaet am Leiterboden:** v22@25 gegen hv4@150 76 %, gegen hv4@600 50 %, hv4@600
  gegen hv4@150 55 %. Bradley-Terry mittelt das; die Intervalle der Netze haengen weiter am
  gesaettigten Anker-Schritt (par.7a).
- **Replayer-Grenze Chip-Vollendung:** 5 von 30 Partien der Champion-Sims-Kante nicht nachspielbar
  ("Reihe N nicht mit Chips komplettierbar" nach 60 Versuchen); bekannte Grenze, keine neue.
- `player_profiles.json` im Arbeitsbaum veraendert (Nutzer-/Server-Seite), nicht committet.
- Untracked: `models/manifest_train_v28-b03_*.json`, `v28-b04_*.json` (Loeschkandidaten beim
  Wechsel), zwei Replay-Reports in `evaluations/game_analysis/`.

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
| Einhuellende, Schliesskriterium | `geometric_envelope` par.13 | ENTSCHIEDEN 2026-09-12: Kriterium auf Arena-Groessen umgestellt (Nutzer); C2 erfuellt, A1/A2 gegen huellenblindes Orakel negativ und gestrichen; K3-P/Huellenform 2/K5 bleiben Rezept |
| Werkzeuge | | `paired_gating --log-games` (Tor 2b aus Tor 1), `plate_points` je Modell, `dome_stack_known_block_draw_probe`, exakter Orakel-Pfad, Spec-Rueckfall in server.py |

## 5. PREREG-BESTAND (11 OFFEN laut Index 2026-09-13, Ziel rund 7)

`v28_window` (Vorlage), `dome_stack_information_sets` (Variante B), `stack_top_feature`,
`claude_play_interface` (laeuft), `round_estimate_leaf_term` (Skalenwahl a/b, Nutzer),
`round_transition_search_sampling` (haengt an dome_stack; Kandidat fuer UEBERHOLT),
`start_dome_choice` (Stufe 0 GEBAUT 2026-09-12, volle Messung laeuft in der Fortsetzungskette),
~~`policy_surprise_weighting`~~ ENTSCHIEDEN 2026-09-12 (Kante v24-b05 gegen v24-b04 97:103,
SPRT H0: NEIN), `rust_data_layer`
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
`dome_return_order` (angelegt 2026-09-12 auf Nutzer-Hinweis: Rueckgabe-Reihenfolge der Kuppelplatten
ist ein legaler Zug, das Netz nutzt ihn nicht; netzbewertete Rueckgabe als Such-Knopf, A/B nach der
Promotion, v29-Begleitprogramm).
Index: `PREREG_INDEX.md` (generiert).

## 6. OFFENE NUTZER-ENTSCHEIDE

000. **ENTSCHIEDEN 2026-09-12, 18:05: v30 wird released und ist der Projektabschluss** (Tessa =
   v30-Champion). v29 traegt das Begleitprogramm, v30 nur Rezept-Knoepfe; danach Leiter-Endfassung,
   Code-Abschluss Stufen 2/3, Abschlussbericht (`PREREG_v29_window.md` par.8 Punkt 3).

00d. ~~hv3 (hv2 + Phantom-Fix) als Leiter-Knoten~~ ERLEDIGT 21:50: gebaut, Tore gruen,
   eingefroren (`models/frozen_heuristics/hv3_generator`), Kanten 73:77 gegen hv4 und 78:72 gegen
   hv2 (beide Deckel): der Fix aendert die Staerke nicht messbar, hv3 992. Aktions-ID-Waechter
   ebenfalls im Wheel (Spiegeltest 8/8). Urspruenglicher Eintrag: Port GESCHRIEBEN 18:00 (Agent;
   `heuristic_v3.rs`, `plate_builder_v3.rs`, Variante durch Suche/Self-Play/Referee, hv1 per
   Delegation bitidentisch; A2 wirkt in hv3 an zwei Routing-Stellen ueber `remaining_colors`),
   UNKOMPILIERT. Dazu der Aktions-ID-Waechter (Nutzer: Punkt 1): `action_to_id` kennt jeden Typ,
   unbekannter Typ ist ein harter Fehler, `dome` bildet auf die Slot-IDs ab, Python-Spiegel plus
   Test. Beides faehrt seine Tore in `tools/night_hv3_freeze_edges.sh` (tail9, nach tail8):
   Kompilat, Fixture, Anker-Drift, Einfrieren `hv3_generator`, Kanten gegen hv4-Anker und hv2. Dazu v22-b05 (live, k3v_off) als Sprosse
   in der Luecke 1000-1157 (`tools/night_ladder_v22_edges.sh`, nach dem Such-Start-A/B).

00a. **Startkuppel-Streuung in der v29-Erzeugung** (Nutzer 12:45: das Netz soll abweichende
   Startsetzungen kennen; 12:50: "nicht in jedem spiel, aber oft genug"): Dosis
   `MOSAIC_START_SLOT_RANDOM_P` = 0,15 je Spieler als Koordinator-Wahl im Nutzer-Rahmen;
   `PREREG_start_dome_choice.md` par.9b, `PREREG_v29_window.md` par.6b. Bau laeuft (Agent),
   Tore in der Luecke zwischen den Ketten (`tools/night_startslot_build.sh`).
00c. **Mondstapel-Reihenfolge** (Nutzer 13:20: "mit v29 oder v30"): im Netzpfad seit 2026-07-01
   Suchentscheid (nie gemessen); `PREREG_moon_stack_order.md` angelegt: Stufe 1 A/B Fan-out an
   gegen aus als v29-Begleitprogramm (Knopf Default = Bestand), Stufe 2 Zielfrage bei v30.
00e. **Startkuppel Platte/Rotation: Handregel gegen Zufall** (Nutzer 2026-09-12 "mach 1 und 2",
   Punkt 2; `PREREG_start_dome_choice.md` par.9a Punkt 1, Baustand par.9f): Stufe 0 hat den SLOT
   geschlossen (Handregel legt immer (0,0), fuer Heuristiken der beste). Offen waren die bis zu
   zwoelf Kandidaten IM Slot (3 Platten x 4 Rotationen). **GESCHRIEBEN (Agent), UNKOMPILIERT,
   UNGEMESSEN:** Diagnoseknopf `MOSAIC_START_TILE_RANDOM_P0/P1` (0/1, ungesetzt = Bestand
   bitidentisch, kein RNG-Zug) waehlt Platte und Rotation gleichverteilt aus den Kandidaten des
   Slots, den die Handregel gewaehlt haette; Wirkstellen nur dort, wo ein RNG durchgereicht wird
   (Heuristik-Arena `arena_match` und aufzeichnendes Self-Play), Referee/Rundenuebergang/py.rs
   unberuehrt. In der Arena zieht er aus einem aus `game_seed` abgeleiteten Strom, nicht aus dem
   Partie-RNG -- sonst waere der gepaarte Vergleich an der Wurzel entpaart. Sonde
   `tools/probes/start_dome_tile_probe.py` (netzfrei, hv1 beide Seiten, zwei Arme ueber demselben
   Seed, 200 Partien je Arm, Paarungen 25 und 400, Kontrollen: Slot bleibt (0,0), Platten- und
   Rotationsverteilung im Zufallsarm nicht entartet). Vorab-Lesart: KI der gepaarten Differenz
   schliesst 0 ein = auch Platte/Rotation kein Hebel; gross = die Handregel ist die Messlatte des
   Such-Starts. **GEMESSEN 22:24** (par.9f, 800 Partien in 322 s): Handregel minus Zufall
   +1,84 [-0,71; +4,39] Punkte @25 und +1,60 [-1,16; +4,37] @400, Marge und Spalten ebenso mit 0
   im Intervall; einzig "Mehrfarbige Felder" traegt (+0,72 / +0,56). Kontrollen bestanden (Slot
   200/200 (0,0) in beiden Armen; Zufallsarm 68 Kandidaten, Rotationen 44/55/47/54; Handregel
   immer Rotation 0). Verdikt: KEIN HEBEL, par.9a Punkt 1 geschlossen; Streuung fuer v29 bleibt
   auf den Slot beschraenkt.
00f. **Elo-Tracker: Block-Bootstrap und Frueh-Stopp-Markierung** (Nutzer gegen 22:50 "mach das
   Werkzeug"): ERLEDIGT 22:56 (`PREREG_code_cleanup_closeout.md` par.7a Nachtrag). Register-
   Spalten `units`/`early_stop` additiv, drei gepaarte Zeilen rueckgefuellt, elf Zeilen als frueh
   gestoppt markiert, Tests 8/8. Zahlen praktisch unveraendert (Champion [1301, 1393]).
00g. **Sprosse v22-b05@100** (Nutzer gegen 22:50 und 22:53): Kette `tools/night_ladder_v22_sims100.sh`
   GEFAHREN 23:09-23:23: v22@100 gegen hv4 39:11, gegen hv3 43:7 (je Block 1, Frueh-Stopp),
   gegen v22@400 21:39 (SPRT H0 nach 30 Paaren). Die Sprosse liegt NICHT in der Luecke (1175):
   weniger Sims kosten gegen sich selbst 35 %, gegen die Heuristiken fast nichts; der Fit hebt den
   unteren Netz-Block um 10-30 Punkte. Details par.7a.
00h. **Sims-Kanten und Heuristik@600** (Nutzer 23:35-00:10): v28-b02@100 gegen @400 7:23 nach 15
   Paaren, Punkte -9,2, volle Spalten 0,87 gegen 1,30: das Spalten-Plateau der flachen Suche gilt
   fuer den Champion nicht mehr (`PREREG_search_depth_column_optimum.md` Nachtrag; Betriebspunkt
   100 der Erzeugung damit offen, Neumessung par.8d in v29). v22@25: gegen hv4 38:12, hv3 35:15,
   @100 43:57. hv4@600: gegen Anker 82:68 (Deckel), gegen v22@25 76:74 (Deckel): die Heuristik mit
   600 Sims liegt in der Luecke (1069). Treppe Anker -> hv4@600 -> v22@25 -> v22@100 -> v22@400
   steht; Festigung (zwei Kanten je Knoten am Deckel) laeuft als `tools/night_ladder_gap_fill.sh`.
   Nutzer-Entscheid Aufraeumen: Artefakte nur fuer v28-b02 und v27-b01, v21/v24/v26/hv1_anchor/
   restored_v24 werden geloescht, aber erst nach dem Start des v29-Self-Plays (restic-daily).
00b. **Startsetzung als Suchentscheid im Spiel** (Nutzer 13:00, `PREREG_start_dome_choice.md`
   par.9c): ENTSCHIEDEN 13:15 (Nutzer: "bau den such-start dann vor v29"): Bau rund ein Tag
   (net_mcts, Spielpfade, Self-Play, Referee-Worker), Knopf MOSAIC_START_BY_SEARCH Default 0,
   A/B am Champion hinter der Leiter; v29-Erzeugung danach mit Such-Start UND Streuung.
   **A/B GEMESSEN 18:03** (par.9e): Suche legt zu 93 % auf (2,0), Siege 91:99 (SPRT H0 nach 95
   Paaren), Punkte gleich, Eckplatten +1,85 / Aussenfelder +0,83 gegen vertikale Reihen -0,82:
   gleichwertig, andere Praeferenz als die Heuristik. Diagnose 21:40: die (2,0)-Praeferenz bleibt
   ohne Huelle (84,5 % gegen 87,5 %), sie kommt aus dem Netz (Value-Kopf/Prior extrapolieren),
   die v29-Streuung ist die Korrektur. Replayer-Befund war ein RNG-Leck der Start-Suche
   (gefixt, eigener Strom); **WIEDERHOLUNG echt gepaart 23:09** (Seed 20261049, par.9e): 81:89,
   SPRT H0 nach 85 Paaren, 93 % (2,0), volle Spalten 0,95 gegen 0,98, Replay 169/170.
   Entscheid bleibt: Such-Start ins v29-Rezept.
   **GESCHRIEBEN 13:20 (Agent), UNKOMPILIERT** (`PREREG_start_dome_choice.md` par.9d): Suche
   `net_mcts.rs::search_start_placement` (Gumbel-Wurzel ueber die Startkandidaten, ein
   Vorwaertspass fuer Priors plus sims Simulationen), umgeschaltet in allen Netz-Spielpfaden
   inkl. Referee-Worker; Heuristik-Seiten unveraendert. BEFUND: `action_to_id` kennt den Typ
   "dome" nicht, alle Startkandidaten fielen bisher auf ID 405 (dome_stack_peek); der Such-Record
   kodiert die Setzung deshalb als choose_dome_slot (IDs 328-354, Rotationen gebuendelt) und
   bekommt im Trainings-Cache Gewicht 1 (bisher 0 fuer alle Start-Records). Streu-Knopf
   MOSAIC_START_SLOT_RANDOM_P ebenfalls geschrieben (Self-Play-Erzeugung, p=0 bitidentisch).
   **GEBAUT 13:33, Tore gruen** (613 Tests, Fixture und Kontrakt unveraendert, Anker-Drift und
   Konservierung gruen, Wheel installiert). Push erst, wenn die Leiter durch ist (der pre-push-
   Hook baut und testet neben den Referee-Partien).

00. ~~ANKER-DRIFT ROT durch A2~~ ENTSCHIEDEN 2026-09-12: (a) Anker neu gesetzt (`hv4_anchor`, Segment 2).
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
