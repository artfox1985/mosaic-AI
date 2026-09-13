# v29-Programm: Gesamtreihenfolge fuer autonome Agenten-Abarbeitung

**Angelegt 2026-09-13** auf Nutzer-Auftrag (02:15: "schau dir dann die offenen preregs nochmal
durch und passe sie so an, dass ein opus agent selbststaendig die programmpunkte abarbeiten
kann"). Diese Datei ist **keine Vorregistrierung** (kein `PREREG_`-Praefix, sie zaehlt nicht im
Index) und trifft **keine Entscheide**. Sie ist die Fahrplan-Ansicht ueber die zwoelf Dateien,
die am 2026-09-13 offen sind; die verbindlichen Angaben stehen je Punkt im Abschnitt
**AGENTEN-AUFTRAG** der jeweiligen Prereg, die Regeln in `CLAUDE.md`, der Stand in
`evaluations/STATUS.md` Abschnitt 1.

**Stand beim Anlegen:** Champion `v28-b02_brierbest` (Elo 1353 [1306, 1402], Segment 2, Anker
`hv4_anchor`); `tools/night_sims_curve_v28b02.sh` laeuft seit 01:13, danach startet
`tools/night_v28b02s100_vs_v22s25.sh` von selbst; der P.10-Fix steht unkompiliert in
`engine/src/state.rs`; die Schwarm-Erzeugung v29 mit 100 Sims ist freigegeben, der Sockel
zurueckgestellt.

## Reihenfolge

Dauer-Spalte: **gemessen** heisst, die Zahl stammt aus `docs/measured_runtimes.md` oder einem
Artefakt; **ANNAHME** heisst, sie ist hergeleitet und nicht gemessen (CLAUDE.md "Laufzeiten
messen, nicht schaetzen").

| Nr. | Prereg | Punkt | Voraussetzung | Dauer | Stopp-Punkt |
| --- | --- | --- | --- | --- | --- |
| 1 | `search_depth_column_optimum` par.8e | Auswertung Sims-Kurve (Teil A 3 Punkte, Teil B 4 Punkte), Verdikt nach der "eklatant"-Regel | Kette durch, sieben Artefakte vollstaendig | Minuten (ANNAHME) | **ja** -- Sockel-Sims |
| 2 | `search_depth_column_optimum` par.8e / `code_cleanup_closeout` par.7a | Register-Zeile der wartenden Kante v28-b02@100 gegen v22-b05@25 (zweite Aufhaengung des Knotens) | Kante durch (Artefakt `..._seed58_full.json`) | Minuten (ANNAHME) | nein |
| 3 | `stack_top_feature` par.15 | **Wheel 1**: P.10-Suchfix kompilieren plus Record-Feld `tiled_max_row` in `state_to_json`; Tore Lib-Tests, no-run, Wheel, Fixture, Anker-Drift, Konventionen | Maschine frei, Nr. 1 und 2 durch | Tore rund 6 min (gemessen); Bau Minuten, Code liegt | **ja** -- bei ROT in der Drift; Fixture-Neuerzeugung melden |
| 4 | `stack_top_feature` par.13 | Sichtpunkt P.3 klaeren: kennt der Entscheid `DrawStackPeek` gegen `ChooseDrawStackSlot` die Vorderseiten? Entscheidet INPUT_SIZE 794 gegen 812 | nur Codelesen | Minuten (ANNAHME) | **ja** -- Nutzer waehlt die Zahl |
| 5 | `stack_top_feature` par.13/15, `v29_window` par.6c | **Wheel 2**: Encoder-Abschnitt 16 (P.3/P.7/P.9/P.11-P.15), Rust beide Pfade plus Python-Zwilling, `config.INPUT_SIZE`, Sichtgleichheits- und Regressionstest, Fixture, Drift | Nr. 3 und 4, Fenster ohne Erzeugung/Waechter/Kette | Bau und Tore rund 2 h (ANNAHME) | **ja** -- bei ROT in der Drift |
| 6 | `v29_window` par.4, Skill `/mosaic-generation-turnover` | Generationswechsel: Maschine frei, Einfrieren, daily-Snapshot mit restic-Beleg, Namen reservieren, STATUS-Neufassung | Nr. 3 und 5 | Snapshot 7-9 s (gemessen), Rest rund 1 h (ANNAHME) | **ja** -- Loeschungen nur pfadgenau und erst nach dem Self-Play-Start |
| 7 | `v29_window` par.5/par.8 Punkt 8 | **Schwarm-Erzeugung v29**: `value-tempc` und `value-excursion`, je 4.000 Partien @100, threads 11, Seeds 20260921/20260922, `MOSAIC_START_SLOT_RANDOM_P=0.15` | Nr. 6, Freigabe liegt vor (Nutzer 02:10) | 11.632 s + 11.361 s = **6,4 h** (gemessen an v28) | nein |
| 8 | `v29_window` par.4 Punkt 5 | Tor 0 / Tor 2a ex post je Klasse (`corpus_sanity_check.py`) | Nr. 7 | 271 s je Klasse (gemessen) | nein |
| 9 | `v29_window` par.2 | G-2-Haelfte festlegen (`G2_SWARM_PATTERN`), Vorschlag Ausflug-Haelfte | vor dem Fensterbau | Minuten | **ja** -- Nutzer-Entscheid |
| 10 | `v29_window` par.5 Nr. 1, `search_depth` par.8e | **Sockel-Erzeugung** 4.000 Partien policy-aktiv, Sims nach Nr. 1 | Nr. 1 beantwortet, Freigabe, Maschine geklaert | @100 4,0 h (gemessen); hoehere Sims ANNAHME | **ja** -- Sims, Maschine, Freigabe |
| 11 | `v29_window` par.4/par.6 | Kette: Manifeste, G-2-Kennzahlen, Fenster (Seed 20260941), Bloecke, Monolith mit Formen-Waechter | Nr. 7-10 | Kette rund 31 min, Merge 531-551 s (gemessen) | nein |
| 12 | `v29_window` par.6 | Training **v29-b01** (Pflichtarm, Rezept unveraendert) | Nr. 11 | 5.157 s = **1,43 h** (gemessen) | nein |
| 13 | `v29_window` par.6 | Tor 1 b01 gegen den Champion, zwei Seeds, Blockgroesse 5, Logs | Nr. 12, Maschine frei | 86-91 min je Seed (gemessen) | nein |
| 14 | `v29_window` par.6 | Tor 2b (`arena_column_probe`) und Plattenpunkte je Modell | Nr. 13 | 83-108 s bzw. unter 10 s (gemessen) | nein |
| 15 | `special_tile_yield` Nachtrag 2026-09-11, `v29_window` par.6 | Bau Ablations-Schalter `MOSAIC_SPECIAL_PLANES_OFF` plus Tore (Paritaet mit Schalter AN, Fixture bei AUS, Drift) | Maschine frei | Bau Stunden (ANNAHME), Tore rund 6 min (gemessen) | **ja** -- bei ROT |
| 16 | `v29_window` par.6 | Bloecke unter Planes-Schluessel, Monolith, Training **v29-b02** | Nr. 15, Fenster von b01 | 26 min + 9 min + 1,43 h (gemessen) | nein |
| 17 | `v29_window` par.6, `special_tile_yield` | Tor 1 b02 gegen b01, zwei Seeds; Diagnostik Plattenpunkte und Spezialfeld-Ertrag | Nr. 16 | 86-91 min je Seed (gemessen) | nein |
| 18 | `stack_top_feature`, `v29_window` par.6c | Bloecke unter dem 794er-Schluessel, Training **v29-b03** (Sicht-Arm, Warmstart mit null-initialisierten Spalten) | Nr. 5, Fenster von b01 | 26 min + 1,43 h (gemessen) | nein |
| 19 | `v29_window` par.6c | Tor 1 b03 gegen b01, zwei Seeds; Lesart Sichtgleichheit mit Verwerfungs-Ausgang | Nr. 18 | 86-91 min je Seed (gemessen) | nein |
| 20 | `v29_window` par.6d | **Netz-Gesundheit** (5 Punkte), darunter Bau `tools/probes/dead_unit_probe.py` (existiert nicht) | Nr. 12/16/18 | Bau rund 1 h, Laeufe Minuten je Modell (ANNAHME) | nein |
| 21 | `docs/promotion_checklist.md`, Skill `/mosaic-champion-promotion` | Promotion des Siegers: `set_champion`, drei Elo-Kanten, Pflicht-Diagnostiken, Fixture, Einfrieren, Golden Probe | Nr. 13/17/19 | Anker-Kante 1.441-1.491 s, Champion-2 2.516 s, Golden Probe 1.450 s (gemessen) | **ja** -- Champion-Wechsel |
| 22 | `difficulty_levels` par.5 Stufe 0, par.4.2/4.3 | Schwierigkeitsleiter: Inventur und Bau (Spec-Felder, Server-Stufentabelle, Frontend), Wheel mit Fixture und Drift | waehrend der v29-Erzeugung, aber nicht neben Waechter oder Kette | Rust 3-4 h, Server/Frontend 2-3 h (ANNAHME) | **ja** -- Namensschema der Elo-Knoten, Anfaenger hv2 gegen hv3 |
| 23 | `corpus_behaviour_audit` par.3/par.6, `claude_play_interface` par.9 | Werkzeug `tools/probes/corpus_behaviour_audit.py` bauen (existiert nicht) und an den Claude-Logs selbsttesten | v29-Korpus liegt | Bau 2-3 h (ANNAHME) | **ja** -- Umfang Arm C |
| 24 | `corpus_behaviour_audit` par.6 Punkt 3 | Korpuslauf ueber den v29-Korpus (Ziehsucht A1, Zwangsraeumungen A2, Null-Sturz B, Plattenkonditionierung C) | Nr. 23, Selbsttest gruen | unter 0,5 s je Partie, rund 1,5 h fuer 12.000 (ANNAHME) | nein |
| 25 | `claude_play_interface` par.10 | Zugklassen-Differential Claude gegen Champion an jedem Entscheid, mit Netz-gegen-Netz-Rauschboden | Nr. 24 (gleiches Replay), Maschine frei | unter 30 min (ANNAHME) | nein |
| 26 | `claude_play_interface` par.8 Punkt 8 | Partien g08-g10 gegen den amtierenden Champion, Claude als Zweitspieler, Subagent | CPU-freies Fenster (neben GPU erlaubt) | 30-60 min je Partie (ANNAHME) | **ja** -- mehr als zehn Partien? |
| 27 | `moon_stack_order` par.4 | Bau Knopf `MOSAIC_MOON_ORDER_VARIANTS` (Default 1 = Bestand) plus Tore | CPU-freies Fenster, kein Waechter/keine Kette | Bau rund 1 h (ANNAHME), Tore rund 6 min (gemessen) | **ja** -- bei ROT |
| 28 | `moon_stack_order` par.4 | A/B Fan-out an gegen aus am Champion, 200 Paare, Logs, plus Abweichungsrate je Seite | Nr. 27 | 86-91 min (gemessen) | **ja** -- Rezept-Aufnahme |
| 29 | `dome_return_order` par.5 | A/B Rueckgabe-Modus 1 gegen 0 ueber den Referee, 2 x 150 Partien, plus Diagnostik | Knopf ist gebaut (par.8a), Maschine frei | 2.515-2.621 s je Lauf (gemessen) | **ja** -- Modus 1 als Default? Modus 2 als Arm? |
| 30 | `round_estimate_leaf_term` par.5 Punkt 3 | Kostentor K4: Wanduhr je Partie mit gegen ohne Knopf, Schwelle 25 Prozent | Knopf ist gebaut (par.7), Maschine frei | rund 24 min je Lauf, zwei Laeufe (gemessen) | **ja** -- gerissenes Tor beendet den Arm |
| 31 | `round_estimate_leaf_term` par.5 Punkt 4 | argmax-Instrument, C_est 0,5 und 1,0, je mit und ohne K3 | Nr. 30 | rund 24 min je Lauf (gemessen) | nein |
| 32 | `round_estimate_leaf_term` par.5 Punkt 5, par.6a | A/B ueber den Referee, zwei Seed-Basen a 150 Partien, plus Spaltensonde | Nr. 31 | rund 43 min je Lauf (gemessen) | **ja** -- Rezept-Aufnahme |
| 33 | `round_transition_search_sampling` par.9/par.4.2/par.10 | Bau Variante B als Knopf `MOSAIC_ROUND_TRANSITION_LEAF` (Tiling im Blatt, EINE Neubefuellung, stellungsgebundener Seed, Beutel mit Turm daneben) | CPU-freies Fenster, Champion v29-b01 | rund ein Tag Bau (ANNAHME), Tore rund 6 min (gemessen) | **ja** -- bei ROT |
| 34 | `round_transition_search_sampling` par.10 | Sichttor: 300 Blatt-Zustaende Runde 3/4 mit `bag_count` < 21, ein Verstoss ist ROT | Nr. 33 | Minuten (ANNAHME) | **ja** -- ROT beendet den Bau |
| 35 | `round_transition_search_sampling` par.5 Schritt 1 | Kostentor 25 Prozent plus Anteil pseudo-terminaler Blaetter je Suche | Nr. 34 | rund 24 min je Lauf, zwei Laeufe (gemessen) | **ja** -- gerissenes Tor beendet den Arm |
| 36 | `round_transition_search_sampling` par.5 Schritt 2, par.9 | A/B gepaart am Champion v29-b01, 200 Paare, Blockgroesse 5, Logs | Nr. 35 | 86-91 min (gemessen) | **ja** -- Rezept-Aufnahme |
| 37 | `difficulty_levels` par.5 Stufen 1-3 | Antwortzeit je Stufe, drei Kanten (je 100 Paare), "gespielt = gemessen" | Nr. 21 und 22 | Latenz unter 5 min, Kanten unter 1 h (ANNAHME) | **ja** -- Notch-Regel, Streichen einer Stufe |
| 38 | `difficulty_levels` par.5 Stufe 4 | Mensch-Validierung, je Stufe mindestens 3 Partien | Nr. 37 gruen | Kalenderzeit des Nutzers | **ja** -- spielt der Nutzer |
| 39 | `v29_window` par.8 Punkt 3 | v30: nur Rezept-Knoepfe aus den v29-Verdikten, Zyklus wie v29 | Verdikte aus Nr. 28/29/32/36 | wie v29 (gemessen) | **ja** -- Rezept-Entscheide |
| 40 | `code_cleanup_closeout` par.4/par.5/par.5a | Code-Abschluss Stufen 2 und 3, Name "Tessa" im Schluss-Artefakt und in der GUI | nach der v30-Promotion | Stufe 2 offen, Stufe 3 rund 3 h (ANNAHME) | **ja** -- Umfang Stufe 2 |
| 41 | `difficulty_levels` par.5 Stufe 5, `v29_window` par.8 Punkt 3 | Leiter-Endfassung mit dem v30-Champion, STATUS-Neufassung als Abschlussbericht, letzter restic-Snapshot mit Beleg | Nr. 40 | Kanten wie Nr. 37 (ANNAHME) | **ja** |

**Nicht in der Tabelle, weil ohne Zuschnitt:** `special_tile_yield` par.4c (Slot-Ausloesungs-Kopf,
ungebaut, Nutzer-Priorisierung) und par.4a Drafting-Hebel; `stack_top_feature` par.11 (zweite
Achse "was WEISS die Suche"); `dome_return_order` Modus 2 als eigener Arm;
`moon_stack_order` par.5 (Zielwechsel des Kopfs, nur bei H1 positiv, v30);
`round_transition_search_sampling` par.4.3 (robuster Aggregator) und Variante A;
`claude_play_interface` par.9 Punkte 9 und 13b (Validator-Fix, Chipwahl in der Engine).
Fuer jeden gilt in seiner Prereg der Schritt "Zuschnitt registrieren und Nutzer fragen".

## Betriebsregeln in Kurzform (verbindlich ist `CLAUDE.md`)

- **Exklusiv messen.** Waehrend Arena, Self-Play oder netzgestuetzter Sonde erzeugt nichts
  anderes CPU-Last; **ein Build zaehlt als Last**. GPU und CPU duerfen parallel (ein Training
  plus EIN CPU-Auftrag), zwei CPU-Messungen nie. Vor jedem Start die Prozessliste pruefen, nicht
  die Task-Meldungen. Ablauf: `/mosaic-measurement-run`.
- **Keine Pipe, keine Umleitung** hinter Build, Test, Training oder Messlauf. Start als
  Hintergrundaufgabe, `python -X utf8 -u`, Fortschrittszeilen mit `flush=True`. Der Exit-Code
  verschwindet sonst, und PowerShell bricht die Pipeline frueh ab.
- **Laufzeit ins Artefakt**, nicht nur nach STATUS: Pflichtfelder
  `"laufzeit": {"wanduhr_s": .., "cpu_s": .., "threads": .., "s_je_partie": ..}`. Die
  Planungsgroesse wandert nach `docs/measured_runtimes.md`.
- **Blockgroesse 5 in JEDER Arena**, nie dem Werkzeug-Default trauen; Score-Analysen immer auf
  Block-Ebene.
- **Die sechs Standard-Kennzahlen** in jedem Messbericht: Reihen-, Spalten-,
  Strafleistenauslastung, Punkte je Wertungsplatte, eigene Punkte, Margin -- je Seite und als
  Differenz. Stilles Weglassen ist ein Regelbruch.
- **Regel 0:** jede Sachaussage traegt eine Pruefstelle (`datei:zeile`) oder ist als Annahme
  markiert; jede tragende Zahl nennt **n, Grundmenge und Einheit**, abgeglichen mit dem
  Verbraucher. Agenten-Befunde sind Behauptungen.
- **Kopf im selben Zug:** wer ein Ergebnis registriert, zieht die Zeile 1 der Prereg nach
  (Ueberholtes ERSETZEN, unter rund 600 Zeichen) und laesst sofort
  `python tools/generate_prereg_index.py` laufen.
- **Rueckwaerts-Pruefung:** nach dem NAMEN der Messung und ihren tragenden Zahlen ueber
  `evaluations/`, `docs/` und den Code greppen und jede Fundstelle lesen.
- **Nach jeder Engine-Aenderung Anker-Invarianz** (`/mosaic-anchor-invariance`): Drift und
  Konservierung. ROT heisst Nutzer-Entscheid, nie Reparatur.
- **Reihenfolge bei Bauten:** Bau -> Tore (Lib-Tests, `--no-run` fuer examples/benches, Wheel per
  `python -m maturin`, Paritaets-Fixture, Anker-Drift, `tools/check_conventions.py`) -> Messung.
  Die Python-DLL gehoert vor `cargo test` in den PATH.
- **Kein Push ohne Anweisung**, Ahead-Stand melden. **Keine Loeschung ohne pfadgenaue Freigabe.**
- **Bezeichner englisch** (Rust wie Python), Inhaltssprache deutsch, Dateinamen englisch; in
  Dateien keine Umlaute und kein Geviertstrich.
- **Dateien laufender Laeufe nicht anfassen** (Spec-JSONs, Listen, `config.py`,
  `engine/py/neural_net.py`, `corpus_dataset.py`, `file_cache_key.py`); Waechter und Worker
  importieren frisch.
- **Messmaterial ist kein Trainingsmaterial:** Streudateien vor dem Fensterbau in
  `MOSAIC_DATA_EXCLUDE` pinnen.

## Was ein Agent hier NICHT darf

1. **Keine Erzeugung starten**, die nicht ausdruecklich freigegeben ist. Freigegeben ist am
   2026-09-13 genau eines: der **Schwarm** (tempc plus excursion) mit **100 Sims**. Der Sockel
   ist zurueckgestellt.
2. **Keinen Champion wechseln**, keinen Anker neu setzen, kein `set_champion` aus eigenem
   Antrieb. Bei ROT in der Anker-Drift: anhalten und den Nutzer entscheiden lassen (Anker
   bewusst neu setzen oder Aenderung zuruecknehmen).
3. **Keinen Knopf ins Rezept aufnehmen** -- auch nicht bei positivem A/B. Rueckgabe-Reihenfolge,
   Mondstapel-Fan-out, Rundenschaetzer, Tiling im Blatt: alle vier sind Vorlagen an den Nutzer.
4. **Nichts loeschen** ohne pfadgenaue Freigabe: keine Modelle, keine Artefakte, keine
   Korpusdateien, keine Ketten-Skripte, keine Messdateien. Ausschlussliste ja, `rm` nein. Die
   freigegebene Loeschliste aus STATUS Abschnitt 1 loescht der NUTZER, und erst nach dem Start
   des v29-Self-Plays.
5. **Nicht pushen**, nicht `player_profiles.json` oder `player_profiles.json.bak` committen.
6. **Keinen Zuschnitt erfinden.** Wo eine Prereg keinen Arm, keine Dosis, keine Schwelle und
   keinen Namen registriert hat, wird der Punkt vorgelegt, nicht geraten -- namentlich:
   G-2-Haelfte, Sockel-Sims, INPUT_SIZE 794 gegen 812, Arm-C-Umfang, Namensschema der
   Stufen-Knoten, Anfaenger-Heuristik hv2 gegen hv3, Umfang Code-Abschluss Stufe 2,
   `special_tile_yield` par.4a/par.4c, `stack_top_feature` par.11, `dome_return_order` Modus 2,
   Validator-Fix und Chipwahl aus `claude_play_interface` par.9.
7. **Keine Messung neben einer Messung**, und kein Build waehrend eines Laufs -- auch nicht
   "nur schnell".
8. **Keine Zahl ohne n, Grundmenge und Einheit** weitergeben, keine ungepruefte Agenten-Zahl in
   eine Rechnung nehmen, keine Zwischengroesse als Verdikt ausgeben, wo die Prereg Punkte und
   Margin als Primaermass festgelegt hat.
9. **Kein stilles Neuerzeugen** der Netz-Paritaets-Fixture. Sie darf sich nur aendern, wenn die
   Aenderung das Spiel bewusst bewegt; dann mit Begruendung, Gegenprobe und Registrierung.
10. **Keine Prereg-Koepfe oder Bestandsabsaetze umschreiben**, ausser als Nachzug zu einem
    registrierten Ergebnis im selben Zug.
