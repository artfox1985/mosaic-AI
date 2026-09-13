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

## 1. UEBERGABE an die naechste Sitzung (2026-09-13, 02:50; Anlass: Kontextfenster der alten Sitzung voll, Sims-Kette Teil B laeuft)

**Champion laut `models/champion.txt`: `v28-b02_brierbest` (Promotion 2026-09-12), Elo 1394
[1350, 1445]** aus 1.860 Partien im LEITERSEGMENT 2 (40 Kanten, Anker `hv4_anchor` fix 1000,
Block-Bootstrap; Treppe Anker -> hv4@600 -> v22@25 -> v22@100 -> v22@400 traegt,
`PREREG_code_cleanup_closeout.md` par.7a Nachtrag "TREPPE GEFESTIGT"). Generator v29 = v28-b02.
**Fahrplan fuer alles Weitere: `evaluations/v29_program_agent_plan.md`** (41 Punkte, Betriebsregeln,
"Was ein Agent NICHT darf"); je Prereg der Abschnitt AGENTEN-AUFTRAG. Ahead-Stand vor dem
Uebergabe-Commit: 10 Commits, kein Push (Nutzer pusht selbst).

### LAEUFT (Maschine BELEGT)

- **`tools/night_sims_curve_v28b02.sh` DURCH** (01:13 bis 04:08, exklusiv). Teil A und Teil B sind
  gemessen und in `PREREG_search_depth_column_optimum.md` par.8e registriert; Verdikt **VIERTER
  FALL, die Formen widersprechen sich**: Teil A (Staerke) saettigt bei 400 (@100 45:105, @200
  53:97, @600 74:76 gegen @400), Teil B (Korpus, argmax, je 200 Partien) faellt MONOTON (volle
  Spalten je Seite 1,0975 / 0,9575 / 0,8950 / 0,8200 bei 100 / 200 / 400 / 600 Sims; @100 gegen
  @400 z = +3,74), und es faellt allein die Vollendung, nicht die Teilspalten. Die
  "eklatant"-Regel des Nutzers ist mit 1 von 3 Bedingungen NICHT erfuellt: **Betriebspunkt 100
  bleibt**. Sieben Artefakte, sieben Laufzeit-Zeilen in `docs/measured_runtimes.md`.
  Die Self-Play-Dateien `data/selfplay_depth<S>-v28b02_*.pkl` sind MESSMATERIAL: vor dem
  v29-Fensterbau in `MOSAIC_DATA_EXCLUDE` (Loeschung nur auf pfadgenaue Freigabe).
- **Kante v28-b02@100 gegen v22-b05@25 DURCH** (10:11-10:21, `tools/run_v28b02s100_vs_v22s25.sh`,
  601,3 s, 3,007 s je Partie, 10 Threads): **172:28** (86 Prozent), n = 200 Partien aus 100
  Paaren ohne Frueh-Stopp, McNemar p = 5e-19, gepaarte Differenz +1,44 [+1,24; +1,64], Punkte
  58,9 gegen 41,2, Strafleiste 9,1 gegen 9,0. Im Register eingetragen.
- **`tools/night_v28b02s100_vs_v22s25.sh` ist DEFEKT und haengt weiter** (Prozess der alten
  Sitzung). Sein Prozessfilter (Z.13) enthaelt `self_play.py|paired_gating.py` unmaskiert und
  trifft die CommandLine des eigenen pwsh-Aufrufs; der Zaehler wird nie 0, die Kante waere nie
  gestartet. Gemessen 04:18: maskiertes Muster 0 Kettenprozesse, Originalmuster 4. Ein
  Doppelstart ist ausgeschlossen (derselbe Grund), sein Poll kostet alle 120 s einen Kern von 12.
  **Zu tun:** Prozess beenden (der Versuch der Sitzung wurde vom Berechtigungssystem abgelehnt)
  und den Filter im Skript maskieren oder das Skript loeschen -- pfadgenaue Freigabe noetig.

### ERSTE AUFGABE DER NEUEN SITZUNG (in dieser Reihenfolge; Details je Punkt im Fahrplan)

1. ~~**WATCHER** auf beide Laeufe~~ **ERLEDIGT 2026-09-13:** die Sims-Kette ist um 04:08 durch
   (vier `depth_curve_*_v28b02.json`). Die wartende Kante ist **NICHT** von selbst angelaufen
   (defektes Wartescript, siehe oben); sie laeuft seit 10:11 direkt. Dazwischen hing die Sitzung
   von 04:53 bis 10:11 (Nutzer: "da gab es einen haenger"), der Befund von 04:18 blieb also
   liegen. (Der Prozess-Grep darf sich nicht selbst treffen: Muster wie `[n]ight_...` -- genau
   daran ist das Wartescript gescheitert.)
2. ~~**Register**~~ **ERLEDIGT 2026-09-13, 10:30:** vier Kanten eingetragen (40 Match-Zeilen).
   Neue Knoten: `v28-b02@100` 1298 [1251, 1350], `@200` 1289 [1209, 1367], `@600` 1389
   [1306, 1474]. **Der Champion-Wert ist dadurch von 1353 auf 1394 [1350, 1445] gestiegen**
   (1.860 Partien), weil die drei neuen Knoten unter `@400` haengen; nachgezogen in README
   Z.26, `docs/project_overview.md` (zwei Stellen), `models/frozen_champions/v28-b02/manifest.json`
   Block `elo` samt `ladder_after_refit`, und in der Champion-Zeile oben. Ebenso nachgezogen:
   `PREREG_difficulty_levels.md` (der Satz "fuer keinen Champion gibt es eine Elo-Kante bei
   anderer Sim-Zahl" ist seit diesen Kanten ueberholt).
3. ~~**par.8e abschliessen**~~ **ERLEDIGT 2026-09-13, 04:15:** Verdikt vierter Fall, Betriebspunkt
   100 bleibt, Sockel-Vorschlag 100 Sims (oben unter den offenen Entscheiden). Nachgezogen sind
   Kopf und Index, `docs/measured_runtimes.md` (sieben Zeilen), `PREREG_v29_window.md` P2 und
   `docs/generation_loop.md`. **Korrektur zur Uebergabe:** der dort aufgetragene Hinweis, ein
   Sockel bei 400 reisse die Tor-0/Tor-2a-Bezugswerte NACH OBEN, ist durch die Messung widerlegt
   (er stand auf Teil A allein); eingetragen ist die gemessene Richtung, also nach unten. **Offen
   aus diesem Punkt:** Plattenpunkte je Kriterium fuer die drei Teil-A-Laeufe nachfahren (das
   Kettenskript rief `plate_points_from_arena.py` ohne `--out` auf, `night_sims_curve_v28b02.sh`
   Z.33; je unter 5 s auf vorhandenen Logs) und die Rueckwaerts-Stelle
   `PREREG_difficulty_levels.md` Z.137 ("Fuer keinen Champion gibt es eine Elo-Kante bei anderer
   Sim-Zahl") im selben Zug wie die Register-Zeilen nachziehen.
4. **Wheel 1 (Maschine frei!):** P.10-Fix ist in `engine/src/state.rs` (`restore_top_plate_type`,
   Test `determinization_keeps_the_public_type_of_the_top_plate`); dazu Record-Feld `tiled_max_row`
   additiv in `serialize.rs::state_to_json` (P.14, `PREREG_stack_top_feature.md` par.15). Tore:
   `cargo test --release --lib` (Python-DLL im PATH, CLAUDE.md), `--no-run`, Wheel per
   `python -m maturin` + pip, Netz-Paritaets-Fixture des Champions (aendert sich vermutlich durch
   P.10: bewusst neu mit Begruendung), Anker-Drift und Konservierung (`/mosaic-anchor-invariance`;
   der Heuristik-Pfad ruft `determinize_dome_pool` nicht, Erwartung GRUEN; ROT = Nutzer-Entscheid),
   `tools/check_conventions.py`. Commit.
5. **`/mosaic-generation-turnover`** (Skill laden) und danach die **SCHWARM-Erzeugung v29 mit 100
   Sims** starten (Freigabe unten; `PREREG_v29_window.md` par.5 value-tempc und value-excursion, je
   4.000 Partien, Seeds 20260921/20260922, `--start-slot-random-p 0.15`, Spec mit `start_by_search 1`
   nach par.6b; Manifest-Diff gegen `data/manifest_v27-b01-policy_20260910_234958.json`, par.4).
   Der Sockel wird NICHT erzeugt (Nutzer: schnellere Maschine). Nach dem Start: Nutzer informieren,
   Loeschliste (unten) loescht der Nutzer selbst; Snapshot-ID und Loeschung dann eintragen.
6. **Portable Build** (nur bei freier CPU, z. B. neben der GPU-losen Erzeugung NICHT: die Erzeugung
   ist CPU): `python tools/build_release.py` nach dem Plan in
   `evaluations/review/portable_build_audit_2026-09-13.md` Abschnitt C; Spec ist auf v28-b02
   umgestellt (Commit 3c81d0b). Zip-Name und Weitergabe = Nutzer.
7. Danach nach Fahrplan (Wheel 2 Sicht-Arm, Fenster, b01/b02/b03, Tore, Netz-Gesundheit, ...).

### FREIGABEN UND VERBOTE (woertlich vom Nutzer)

- **NEU 2026-09-13, 02:10 (Nutzer): "du kannst nach abschluss selbstaendig den skill starten fuer die
  schwarm erzeugung mit 100 sims. sockel lassen wir noch aussen vor und vermutlich mach ich diesen
  auf der schnelleren maschine."** Freigabe: nach dem Ende der Sims-Kette und der wartenden Kante
  (Maschine frei) `/mosaic-generation-turnover` selbststaendig durchlaufen und die
  SCHWARM-Erzeugung v29 (Value-Klasse: tempc plus excursion, je 4.000 Partien, 100 Sims, Rezept
  `PREREG_v29_window.md` par.5/par.6b) starten. Der SOCKEL (4.000 Partien policy-aktiv) wird NICHT
  hier erzeugt; Sims und Maschine dafuer entscheidet der Nutzer nach der Auswertung par.8e.
  Vor dem Start: P.10-Fix und Record-Feld `tiled_max_row` im Wheel (Schritt 6), Anker-Drift,
  Paritaets-Fixture, Manifest-Diff gegen die Referenz (par.4). Loeschliste erst nach dem Start.

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

- **NEU 2026-09-13, 11:20, STOPP-PUNKT: Anker-Drift nach Wheel 1 ist ROT -- aber als
  SERIALISIERUNGS-ARTEFAKT bewiesen, nicht als Drift.** Der Anker spielt Zug fuer Zug dieselben
  Partien. Belege, alle drei geprueft:
  (a) **Konservierung GRUEN**: das Artefakt-Wheel in der eigenen venv reproduziert die
  Referenzprobe Feld fuer Feld (1/1 Dateien, 1.763 Schritte,
  `anchor_conservation_20260913_wheel1.json`) -- die Referenz ist intakt, das Artefakt unversehrt.
  (b) **Drift ROT** (`anchor_drift_live_wheel_20260913_wheel1.json`), erste Abweichung Schritt 0,
  Feld `state`.
  (c) **Gegenprobe** (`anchor_drift_counterproof_20260913_wheel1.json`): Golden-Probe-Rezept mit
  dem Live-Wheel nachgespielt, Record fuer Record verglichen. Roh weichen 1.763 von 1.763 ab;
  nach Abzug des `game_id`-Zeitstempels UND des neuen Feldes `tiled_max_row` sind es **0 von
  1.763**. `completed`-Felder und `scores` sind identisch.
  **Ursache:** das Pruefwerkzeug vergleicht Feld fuer Feld und kennt additive Felder nicht; seine
  Referenzprobe stammt vom 2026-09-12, also von vor dem Record-Feld P.14.
  **Entscheid des Nutzers (CLAUDE.md: ROT ist nie eine Agenten-Reparatur):**
  A) Golden Probe des Ankers unter dem neuen Format neu aufnehmen, mit der Gegenprobe als
  Bruecke -- Pruefung bleibt scharf, aber ein eingefrorenes Artefakt wird angefasst.
  B) Werkzeug alle Feldunterschiede tolerieren lassen -- riskant, versteckt kuenftig echte
  Aenderungen.
  C) Record-Feld zuruecknehmen -- dann fehlt P.14 im v29-Korpus und der Sicht-Arm kann das
  Merkmal nicht lernen.
  D) (Vorschlag des Koordinators) Werkzeug NUR aufwaerts-tolerant machen: Felder, die im neuen
  Record NEU sind und in der Referenz fehlen, werden ignoriert und im Artefakt protokolliert;
  ein VERSCHWUNDENES oder geaendertes Feld bleibt ROT. Das bildet die additive Konvention ab
  (`project_2d_encoder_must_be_additive`), ohne echte Drifts zu verstecken.
  **Bis zum Entscheid steht Wheel 1 auf halbem Weg:** Wheel ist gebaut UND installiert
  (Vertragshash 39648b95bbba1acf unveraendert, input_size 755, neue Manifest-Felder
  `stack_draw_research`/`stack_draw_reservation` vorhanden), Lib-Tests 637/638 und
  `--no-run --all-targets` (16 Targets) gruen; offen sind Konventions-Lauf und die bewusste
  Neuerzeugung der Netz-Paritaets-Fixture.

- **NEU 2026-09-13, 10:35: `MOSAIC_STACK_DRAW_RESEARCH` fuer die v29-Erzeugung -- Vorgabe und
  Praxis widersprechen sich.** `PREREG_chance_nodes.md` Z.1126 schreibt vor, der Knopf "gehoert
  in die Umgebung BEIDER Laeufe (Sockel und Schwarm)", und ihr Verdikt fuehrt ihn als Teil des
  Erzeugungsrezepts seit v23. Geprueft ist aber: `tools/night_v28_generate.sh` setzt ihn NICHT
  (exportiert nur `PYTHONIOENCODING`), der Befehl in `PREREG_v29_window.md` par.5 nennt ihn
  nicht, und das Lauf-Manifest der v28-Erzeugung fuehrt ihn in `engine_config` gar nicht -- er
  ist dort weder als gesetzt noch als ungesetzt belegbar. **VERSCHAERFT 10:55 nach Grep ueber
  Arbeitsbaum UND Git-Historie (Nutzer-Auftrag): der Knopf stand NIE in einem Erzeugungsskript,
  in keiner Generation** -- `night_v25_socket/excursion`, `night_v26_swarm/chain`,
  `night_v27_generate/chain`, `night_v28_generate/chain` haben je 0 Treffer (letzter Stand je
  Datei aus `git show`). Der Entscheid-Commit `3c5c44b` ("der Knopf gehoert in die Erzeugung",
  2026-08-30) fasste nur Doku und eine Sonde an. Gesetzt wird er ausschliesslich von
  MESS-Instrumenten (`argmax_profile.sh`, `night_v28_measure.sh`, `night_k3d_joker_instrument.sh`,
  `night_start_search_hull_off.sh`, `night_sims_curve_v28b02.sh`): **gemessen MIT, erzeugt OHNE**.
  In den Fenster-Preregs verliert er sich nach v25 (v24 und v25 haben die `export`-Zeile, v26 bis
  v29 nennen ihn nicht). Nicht ausschliessbar ist ein Setzen von Hand in der Shell; belegbar ist
  es nicht. Vollstaendig registriert in `PREREG_chance_nodes.md`, Nachtrag 2026-09-13.
  Inhaltlich ist `=1` die korrekte
  Fassung (ohne ihn bewertet die Suche eine Fortsetzung, die nicht ausgefuehrt wird,
  `engine/src/self_play.rs` Z.972-995). **Entscheid des Nutzers, weil Rezeptfrage:** setzen
  wir ihn fuer Sockel und Schwarm? Setzen wir ihn, weicht v29 vom belegbaren v28-Stand ab;
  setzen wir ihn nicht, weicht die Praxis weiter von der eigenen Vorgabe ab. Unabhaengig davon
  ist das Manifest GEBAUT: `engine_config_json()` gibt ab Wheel 1 `stack_draw_research` und
  `stack_draw_reservation` aus (`engine/src/lib.rs`; Getter in `self_play.rs` auf `pub(crate)`).
  Details in
  `PREREG_search_depth_column_optimum.md` par.8e, Abschnitt Einschraenkungen.

- **SIMS DES SOCKELS: ENTSCHIEDEN 2026-09-13, 11:50 -- 400 Sims** (Nutzer: "Die 100 sims fuer den sockel sind nicht entschieden. Ich nehm 400 und push die policy ein wenig."). Der Koordinator-Vorschlag lautete 100; der Nutzer folgt dem Gegenargument aus den Einschraenkungen (Zielqualitaet statt Zustandsverteilung). **Schwarm bleibt 100.** Kosten Sockel 8,29 h statt 4,40 h, auf der schnelleren Maschine. Erwartete Folge: Tor 0 und Tor 2a des Sockels fallen unter den Bezugswert 0,816 des v28-Generators, das ist der Suchtiefen-Effekt und allein kein Torriss. Offen bleibt nur noch der Startzeitpunkt. Herleitung: Ergebnis in
  `PREREG_search_depth_column_optimum.md` par.8e (vierter Fall: Staerke saettigt bei 400, Korpus
  faellt monoton zugunsten von 100; "eklatant"-Regel 1 von 3, Betriebspunkt 100 bleibt).
  **Vorschlag: Sockel mit 100 Sims, wie der Schwarm** (`PREREG_v29_window.md` P2, dort auch der
  Tor-0/Tor-2a-Hinweis). Kosten fuer 4.000 Partien aus gemessenen Sekunden je Partie: @100
  **4,40 h**, @200 5,82 h, @400 8,29 h, @600 11,74 h; der teurere Punkt liefert den
  spaltenaermeren Korpus (@400 kostet 3,89 h mehr und bringt 0,2025 volle Spalten je Seite
  weniger). Offen bleiben damit nur noch **Maschine und Startzeitpunkt** des Sockels (Nutzer:
  "vermutlich auf der schnelleren Maschine"). Der Schwarm ist unabhaengig davon auf 100
  entschieden und freigegeben.
- **Sims-Knoten v28-b02@200 und @600 im Register (Nutzer 2026-09-13, 02:25: "lass sie noch an einer
  kante. das ziehen wir dann in v29 oder v30 nach"):** die drei gepaarten Punkte der Sims-Kette werden
  als Kanten gegen @400 eingetragen; @200 und @600 haengen damit an EINER Kante (weiche Intervalle),
  eine zweite Aufhaengung (z. B. hv4@600 ueber den Referee, 150 Partien) erst in v29/v30.
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
| Claude-Partien | `claude_play_interface` par.7/par.9/par.10 | g02-g07 gespielt (3:1 gegen v27-b01, 1:1 gegen v28-b02); Werkzeug-Rauchtest gruen, Brett-Hilfen gebaut (par.9 P.14). **SICHTGLEICHHEIT DES FENSTERS GILT IN KEINE RICHTUNG (par.10):** vier Stellen sehe ich mehr (Beutel/Turm getrennt = P.9, Chipanzahl = P.11, Vorderseiten gezogener Platten = Regelverstoss des Fensters, Historie), die Gegenrichtung (18er-Stapelmaske plus Wild-Anteil und die elf Werte Rueckgabe-Wissen) ist am 2026-09-13 ins Fenster gebaut, mit Waechter: `dome_pool_view` gilt fuer den Spieler am Zug und bleibt weg, wenn die KI dran ist. Partien bleiben als Beobachtung gueltig, als Staerkevergleich nicht. Nutzer-Entscheid: Fenster angleichen? g08-g10 offen |
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
