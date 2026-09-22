<!-- STATUS: ENTSCHIEDEN | Frage: Die Rueckgabe-Reihenfolge nicht gewaehlter Kuppelplatten ist ein legaler Zug -- wird die Wahl gebaut, und traegt sie? | Beleg: GEBAUT ja (Knoten 411-413 in Aktionsraum, Encoder, Suche, Korpus). TRAEGT nein: A/B 74:76 und 74:76, Vorzeichentest p=1,0 (par.9); erklaert durch den VORAB registrierten Deckel aus par.8a -- der Value-Kopf sieht nur die TYP-Folge, 93 bzw. 85 Prozent der Paare spielen dasselbe. Der Knopf bleibt (Massstab Vollstaendigkeit, nicht Elo), Default 0. Dosis-Nachrechnung an der v31-Erzeugung eingeloest (par.13): 28,0 Prozent der Sockel-Partien haben eine Gelegenheit gegen 17,75 an v30, Knoten durchgehend mit Lernziel. Nutzer-Entscheid 2026-09-21: geschlossen. -->

# Vorregistrierung: Rueckgabe-Reihenfolge der Kuppelplatten als Zug des Netzes

**Angelegt 2026-09-12, 02:00** auf Nutzer-Hinweis. Anlass war die Frage "kann das netz wenn es
mehrere kuppelplatten vom stapel zieht die reihenfolge waehlen und macht es das auch?"; Antwort
am Code: nein (par.2). Nutzer dazu: *"geht weniger darum ob ich es will. das ist ein gueltiger
[Zug] und dadurch laesst sich beeinflussen wann welche kuppelplatte kommt."* Das stellt die
Frage in dieselbe Klasse wie die Kuppelstapel-Informationsmengen
(`PREREG_dome_stack_information_sets.md`): ein Freiheitsgrad, den der Spieler rechtmaessig hat
und den das Modell nicht nutzt. Massstab ist Vollstaendigkeit, nicht Elo (CLAUDE.md
"Symmetrische Defekte sieht keine Arena"; Praezedenz "Korrektheit vor gemessenem Nutzen").

## par.1 Die Regel und was sie hergibt

Beim verdeckten Ziehen vom Kuppelstapel (Aktion A) zieht der Spieler eine oder mehrere Platten,
behaelt eine und legt die uebrigen UNTER den Stapel zurueck; die Reihenfolge waehlt er. Die
Engine prueft `return_order` als Permutation der nicht gewaehlten gezogenen Platten
(`game.rs:244-256`), der Mensch waehlt sie in der GUI (`static/js/app.js:2820-2900`), und der
Rueckleger kennt seinen Block seither in Reihenfolge (Variante A, `state.rs::determinize_dome_pool`;
Nutzer-Entscheid 2026-09-10: die Reihenfolge ist nur dem Rueckleger bekannt). Damit kann ein
Spieler steuern, welche seiner zurueckgelegten Platten als naechste oben liegt, sobald der
unbekannte Praefix aufgebraucht ist; der Gegner sieht nur die Menge.

## par.2 Bestand (Code geprueft 2026-09-12)

- **Netz-Spielpfad:** `self_play.rs:675-684` legt kanonisch in Ziehreihenfolge zurueck, mit dem
  Kommentar, die Reihenfolge sei "fuer die KI keine gelernte Policy-Dimension (wie
  moon_order/num_drawn)". Der Suchbaum (`game.rs:413-423`, `generate_draw_stack_moves`) faechert
  `return_order` ebenfalls nicht auf: ein Kandidat je (Platte, Slot), Rest in Ziehreihenfolge.
- **GUI-Pfad:** `py.rs:289` nimmt denselben Default, wenn der Aufrufer keine Reihenfolge
  mitgibt; die GUI gibt fuer den Menschen eine mit, fuer das Netz nicht.
- **Aktionsraum:** `choose_draw_stack_slot` (355-390) und `choose_dome_rotation` (391-394)
  kodieren Platte, Slot und Rotation; eine Reihenfolge-Aktion gibt es nicht
  (`features.rs:1444-1470`).
- **Records:** die `#a`-Zeile traegt `return_order` (`game.rs:285-290`), Replayer und Logs sind
  darauf eingerichtet; ein Netz, das waehlt, braucht kein neues Record-Feld.
- **Derselbe Bauplan bei den Mondsteinen, KORRIGIERT 2026-09-12:** `moon_order` ist im
  Aktionsraum und im Heuristik-Pfad kanonisch (`self_play.rs:234`, `validation.rs:175-193`), in
  der NETZSUCHE aber seit 2026-07-01 ein Suchentscheid (`net_mcts.rs:1724-1920`: alle Permutationen
  als Kinder, Prior aus dem Moon-Order-Kopf). Eigene Prereg `PREREG_moon_stack_order.md`.

## par.3 Hypothesen (VOR jeder Messung)

- **H1 (Vollstaendigkeit).** Ein Netz, das die Rueckgabe waehlt, spielt regelkonform
  vollstaendiger; das ist unabhaengig vom Messergebnis der Grund, es zu bauen (Nutzer).
- **H2 (Wirkung, klein und spaet).** Die Wahl wirkt nur, wenn (a) mehr als eine Platte gezogen
  wurde (Ziehserien; Median der Ziehungen je Partie 3, `dome_stack_known_block_draws_*.json`),
  (b) der eigene Block spaeter erreicht wird (Praefix aufgebraucht; Anteil "eigener Block" bei
  Ziehungen 22-28 Prozent, dieselben Artefakte) und (c) die Platten im Wert verschieden sind.
  Erwartung: Arena-Effekt unter der Aufloesung von 150 Partien, sichtbar nur in der
  Diagnostik (par.5).
- **H3 (Form).** Eine Erweiterung des Aktionsraums um Permutationen (bis 3! = 6 fuer drei
  Restplatten) lohnt bei ein bis zwei Restgenerationen nicht (neuer Kontrakt, Policy ohne
  Trainingsziel). Eine SUCHSEITIGE Wahl ohne neues Trainingsziel reicht: die Rueckgabe wird wie
  der Tiling-Stichentscheid vom Netz BEWERTET, nicht vorhergesagt.

## par.4 Bauform (registriert VOR dem Bau)

**Knopf `MOSAIC_RETURN_ORDER_MODE`** (Spec-Feld `return_order_mode`, optional, Default 0):

| Wert | Verhalten                                                                                                                                                                                                                                                                                                                             |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0    | Bestand: Ziehreihenfolge (bitidentisch, Default)                                                                                                                                                                                                                                                                                      |
| 1    | **netzbewertet**: fuer jede Permutation der nicht gewaehlten Platten (hoechstens 6) den Folgezustand bilden und aus Sicht des Rueckleger mit dem Value-Kopf bewerten (ein Vorwaertspass je Kandidat, Muster `deviation_best_action`/`net_tiling_tiebreak_value` in `self_play.rs`); die beste gewinnt, Gleichstand -> Ziehreihenfolge |
| 2    | Heuristik "beste Platte nach oben": Rangfolge nach der Handregel aus `choose_start_placement`/Plattenwert (Farbtreffer fuer offene Musterreihen, Spezialfelder), Rest in Ziehreihenfolge; ohne Netz, auch fuer die Heuristik-Spieler nutzbar (NICHT fuer den Anker: hv1 bleibt bei 0)                                                 |

Wirkort: `self_play.rs` Netzpfad (Ziehserie, Rueckgabe) und `py.rs` GUI-Default; der Suchbaum
(`game.rs:413`) bleibt bei einem Kandidaten je (Platte, Slot), die Wahl faellt am Ende der
Ziehserie, nicht in jeder Simulation (Kosten). Seit Variante A kennt die Suche des Ruecklegers
den Block in der gewaehlten Reihenfolge, die Wahl kommt also spaeter in seinen eigenen
Ziehungen an. Bau: Registratur, `docs/knobs.md`, Test (Modus 1 waehlt bei zwei Platten mit
klar verschiedenem Wert die bessere nach oben; Modus 0 bitidentisch), Netz-Paritaets-Fixture
unveraendert bei 0, Anker-Drift gruen (hv1 liest den Knopf nicht).

## par.5 Messung (VORAB)

1. **A/B ueber den Referee, gleiches Netz** (`v28-b02`, Champion-Spec), Modus 1 gegen Modus 0,
   150 Partien, zwei Seed-Basen (Blockgroesse 5). Verdikt "traegt" bei Vorzeichentest p < 0,05,
   sonst "kein messbarer Effekt", und der Knopf bleibt trotzdem (H1, Nutzer-Praezedenz).
2. **Diagnostik aus den Logs** (Grundmenge Rueckgaben mit >= 2 Restplatten, Einheit Rueckgaben):
   Anteil der Rueckgaben, deren Reihenfolge von der Ziehreihenfolge abweicht; Anteil, bei dem
   der Rueckleger die oben gelegte Platte spaeter selbst zieht; Ziehungen in den eigenen Block
   bei positivem Stand (wie `dome_stack_known_block_draw_probe.py`). Erwartung nach H2: die
   Abweichungsrate ist hoch, die Wiederkehr-Rate niedrig.
3. Sechs Standard-Kennzahlen (CLAUDE.md) aus denselben Logs.

## par.6 Kosten und Eintaktung

Bau rund 3 h (Permutationen, Bewertung, Knopf, Tests), Wheel, Fixture, Drift; Messung rund
45 min (2 x 150 Partien) plus Diagnostik. Eintaktung: NACH der Neuverankerung und der
Promotion von v28-b02 (beide laufen auf dem heutigen Wheel; ein Engine-Knopf dazwischen
haette die Promotionskanten auf eine andere Engine gestellt), als Teil des
v29-Begleitprogramms (`PREREG_v29_window.md` par.7 Punkt 4, gleiche Gruppe wie Stopp-Regel und
Peek-Bewertung). Wird Modus 1 Default (Nutzer-Entscheid), gilt er fuer die v29-Erzeugung.

## par.7 Was NICHT gebaut wird

- Keine Aktionsraum-Erweiterung, kein neues Trainingsziel (H3).
- `moon_order` (Mondsteine): in der Netzsuche schon gebaut (siehe par.2, korrigiert); Messung
  und Zielfrage in `PREREG_moon_stack_order.md`.
- Kein Eingriff in die Heuristik-Anker (hv1/hv2 bleiben bei Modus 0).

## par.8 Ergebnisse (leer bis zum Bau)

Nichts gebaut (Stand 2026-09-12, 02:00).

## par.8a BAUSTAND 2026-09-12 (gebaut, im Wheel seit 03:47)

Knopf `return_order_mode` (Spec optional, Env `MOSAIC_RETURN_ORDER_MODE`, 0/1/2) nach par.4 gebaut:
`self_play.rs` (`order_permutations`, `return_order_candidates`, `choose_return_order`,
`resolve_and_apply_stack_draw_with`, Diagnostik-Zeile `[return_order] mode=.. drawn=[..]
chosen=[..]`), `py.rs` GUI-Default und `ai_drafting_net_step`, `referee.rs` In-Process-Seite,
Registratur, `engine_config`, Spec-Abbildungen, sechs Tests. Zwei Bau-Entscheide ueber par.4
hinaus: (1) permutiert werden hoechstens die ersten drei Restplatten (`RETURN_ORDER_MAX_PERMUTED`),
der Schwanz bleibt in Ziehreihenfolge (`MAX_STACK_PEEKS` erlaubt laengere Serien; wie oft, ist
nicht gemessen); (2) Handregel Modus 2 mit gesetzten Gewichten Spezial 2, Joker 1, Farbtreffer

1. **Oben liegt `return_order[0]`** (geprueft: `game.rs:187` zieht per `remove(0)`, `game.rs:290-295`
   legt per `push` in Reihenfolge zurueck, der Block liegt unten und `[0]` kommt zuerst wieder).

**Zwei Befunde, die par.5 vorab einordnen (am Code geprueft, nicht gemessen):**

1. Der Value-Kopf sieht die Reihenfolge nur als TYP-Folge: `features.rs:212` kodiert fuer die
   obersten vier Positionen des eigenen Blocks +1 Spezial / -1 Joker / 0. Permutationen
   gleichtypiger Platten sind fuer das Netz identisch, Modus 1 waehlt dann per Gleichstand die
   Ziehreihenfolge. Die Abweichungsrate ist damit strukturell gedeckelt; ein Kopf, der
   Plattentypen im Block unterscheidet, waere die naechste Stufe (nicht registriert).
2. Modus 1 braucht die Sicht des Ruecklegers im FOLGEZUSTAND, in dem der Gegner am Zug ist;
   `net_leaf_eval` liefert beide Bretter nur ueber den gespiegelten zweiten Vorwaertspass
   (`MIRROR_OTHER_VAL = false`, `net_mcts.rs:1117`). Kosten je Kandidat: ein `eval_pair`-Batch,
   nicht ein Pass.
   Kompilierung, Fixture, Drift und die Messung par.5 folgen nach der Promotion von v28-b02.

**Kompiliert und im Wheel (Nachtrag 03:50):** Bau-Tor 2026-09-12, 03:44-03:48 (`tools/night_v28_knob_build.sh`, Artefakte `anchor_drift_live_wheel_20260912_knobs.json` / `anchor_conservation_artifact_wheel_20260912_knobs.json`): `cargo test --release --lib` 601 gruen (84 s; darunter Kontrakt-Hash-Literal 39648b95bbba1acf und die Netz-Paritaets-Fixture des Champions UNVERAENDERT), Beispiele/Benches kompilieren, Wheel gebaut und installiert (Kontrakt 39648b95bbba1acf, INPUT_SIZE 755), Anker-Drift gegen hv4_anchor GRUEN und Konservierung GRUEN, Konventions-Check gruen. Zwei Nachbesserungen beim Bau: `#![recursion_limit = "256"]` in lib.rs (das `json!`-Literal von `engine_config_json` riss das Makro-Limit) und die Lesestelle der Startslot-Knoepfe als zwei Literal-Aufrufe (Registratur-Scanner). Alle neuen Knoepfe stehen damit auf Default im Wheel, das die Promotion v28-b02 einfriert.

## AGENTEN-AUFTRAG (Stand 2026-09-13, fuer eine autonome Abarbeitung durch einen Opus-Agenten)

### 1. Ziel und Verdikt-Regel

Zu beantworten ist, ob die netzbewertete Wahl der Rueckgabe-Reihenfolge (Modus 1) etwas traegt.
Die Verdikt-Regel steht in **par.5 Punkt 1**: A/B ueber den Referee, gleiches Netz, Modus 1 gegen
Modus 0, 150 Partien, ZWEI Seed-Basen, Blockgroesse 5; "traegt" bei Vorzeichentest p < 0,05,
sonst "kein messbarer Effekt". **Und der Knopf bleibt in beiden Faellen** -- der Massstab ist
Vollstaendigkeit, nicht Elo (par.0/par.1, Nutzer 2026-09-12: "das ist ein gueltiger [Zug] und
dadurch laesst sich beeinflussen wann welche kuppelplatte kommt"; CLAUDE.md "Symmetrische
Defekte sieht keine Arena", Praezedenz "Korrektheit vor gemessenem Nutzen"). Die Erwartung ist
vorab klein (H2 in par.3: die Wahl wirkt nur bei Ziehserien mit mehr als einer Platte, bei
spaeter erreichtem eigenem Block und bei wertverschiedenen Platten), und par.8a nennt den
strukturellen Deckel: der Value-Kopf sieht die Reihenfolge nur als TYP-Folge
(`features.rs:212` kodiert fuer die obersten vier Positionen des eigenen Blocks +1 Spezial /
-1 Joker / 0), Permutationen gleichtypiger Platten sind fuer das Netz identisch, und Modus 1
faellt dann per Gleichstand auf die Ziehreihenfolge zurueck.

### 2. Voraussetzungen

- **Der Knopf ist GEBAUT und im Wheel seit 2026-09-12, 03:47** (par.8a Nachtrag):
  `return_order_mode` (Spec optional, Env `MOSAIC_RETURN_ORDER_MODE`, Werte 0/1/2), Bau-Tor
  `tools/night_v28_knob_build.sh` gruen -- 601 Lib-Tests, Kontrakt-Hash-Literal
  `39648b95bbba1acf` und Netz-Paritaets-Fixture des Champions UNVERAENDERT, Anker-Drift und
  Konservierung gruen, Konventions-Check gruen. **Es ist also nichts mehr zu bauen; offen ist
  allein die Messung.**
- **Maschine frei laut Prozessliste** (Prozesszaehler `0`); exklusiv, keine zweite CPU-Messung.
- **Spieler:** `v28-b02` mit Champion-Spec (par.5 Punkt 1), Modell
  `models/alphazero_v28-b02_brierbest.onnx`, Artefakt `models/frozen_champions/v28-b02/`.
  Wird bis zur Messung ein neuer Champion promoviert, gilt der amtierende Champion; das ist dann
  hier zu registrieren (par.6: Eintaktung NACH Neuverankerung und Promotion, damit kein
  Engine-Knopf zwischen den Promotionskanten liegt).
- **Eintaktung:** v29-Begleitprogramm (`PREREG_v29_window.md` par.7 Punkt 4, vierter
  Spiegelstrich, gleiche Gruppe wie Stopp-Regel und Peek-Bewertung).
- **Kein Eingriff in die Heuristik-Anker** (par.7): hv1/hv2 bleiben bei Modus 0.

### 3. Schritte

**P1 -- A/B Modus 1 gegen Modus 0 (par.5 Punkt 1)**

1. Zwei Spec-Dateien anlegen, die sich NUR im Feld `return_order_mode` unterscheiden (0 gegen 1),
   beide sonst identisch mit der Champion-Spec `models/frozen_champions/v28-b02/spec.json`.
   Ablage unter `models/` mit sprechendem englischem Namen (z.B.
   `models/return_order_mode1.spec.json`); der Dateiname geht ins Artefakt.

2. A/B ueber den Referee, gleiches Netz beidseits, 150 Partien je Seed-Basis, exklusiv, als
   Hintergrundaufgabe ohne Pipe:
   
   ```
   python -X utf8 -u tools/frozen_referee_match.py \
     --artifact-dir models/frozen_champions/v28-b02 \
     --model-a models/alphazero_v28-b02_brierbest.onnx \
     --spec-a models/return_order_mode1.spec.json \
     --sims-a 400 --c-puct-a 1.5 --sims-worker 400 --c-puct-worker 1.5 \
     --n-games 150 --seed-base <SEEDBASIS> --workers 6 \
     --out evaluations/artifacts/return_order_ab_mode1_vs_mode0_<SEEDBASIS>.json
   ```
   
   Zweite Seed-Basis analog. **Dauer (gemessen):** "A/B-Kante ueber den Referee, gleiches Netz,
   Live gegen Artefakt, n=150, 6 Prozesse" 2.515 s / 2.621 s, rund 17 s je Partie
   (`docs/measured_runtimes.md`, Abschnitt Generation v27) -- par.6 dieser Datei schaetzt 45 min
   fuer 2 x 150, die gemessene Nachbarzahl liegt hoeher (rund 43 min JE Lauf). Fuer die Planung
   gilt die gemessene Zahl.
   **Bei Abbruch:** Lauf mit derselben Seed-Basis wiederholen; ein Teil-Lauf wird nicht mit einem
   vollen gepoolt (Verzerrungs-Regel seit v26).
   **Handshake:** laeuft das Artefakt auf einem anderen Kontrakt-Hash, ist `--force-cross-era`
   noetig (Aera-Regel `docs/promotion_checklist.md`); der Golden-Selbsttest bleibt an
   (`--skip-golden` ist nur Debug).

**P2 -- Diagnostik aus den Logs (par.5 Punkt 2)**

3. Grundmenge Rueckgaben mit mindestens 2 Restplatten, Einheit Rueckgaben. Drei Groessen:
   (a) Anteil der Rueckgaben, deren Reihenfolge von der Ziehreihenfolge abweicht;
   (b) Anteil, bei dem der Rueckleger die oben gelegte Platte spaeter selbst zieht;
   (c) Ziehungen in den eigenen Block bei positivem Stand, mit
   `python -X utf8 -u tools/probes/dome_stack_known_block_draw_probe.py` (gemessen 105-129 s auf
   400 Partien, 1 Thread). Quelle fuer (a) und (b): die Diagnostik-Zeile des Knopfs
   `[return_order] mode=.. drawn=[..] chosen=[..]` (par.8a) und die `#a`-Zeile mit `return_order`
   (`game.rs:285-290`). **Erwartung nach H2:** Abweichungsrate hoch, Wiederkehr-Rate niedrig;
   nach par.8a Befund 1 ist die Abweichungsrate strukturell gedeckelt.
4. Sechs Standard-Kennzahlen (CLAUDE.md) aus denselben Logs (par.5 Punkt 3), je Seite und als
   Differenz: `tools/probes/arena_column_probe.py` und `tools/plate_points_from_arena.py`.

**P3 -- Modus 2 (Handregel) -- nicht beauftragt**

5. Modus 2 ist gebaut (Handregel "beste Platte nach oben", Gewichte Spezial 2, Joker 1,
   Farbtreffer 1), aber par.5 registriert nur den A/B von Modus 1 gegen 0. **Schritt "Zuschnitt
   registrieren und Nutzer fragen":** ob Modus 2 einen eigenen Arm bekommt (er waere auch fuer
   die Heuristik-Spieler nutzbar, NICHT fuer den Anker), ist nicht entschieden -- vorlegen, nicht
   raten.

### 4. Auswertung und Registrierung

- **Zahlen mit n, Grundmenge, Einheit**: A/B "n = 150 Partien je Seed-Basis, Grundmenge
  Referee-Partien gleiches Netz mit gegen ohne Knopf, Einheit Siege"; Diagnostik "n = Rueckgaben
  mit >= 2 Restplatten, Grundmenge Rueckgaben, Einheit Anteil"; Ziehungen "n = Partien,
  Grundmenge Partien je Seite, Einheit Ziehungen in den eigenen Block je Partie". Auswertung auf
  Block-Ebene (Blockgroesse 5).
- **Die sechs Standard-Kennzahlen** je Seite und als Differenz (CLAUDE.md).
- **Registrierung in par.8** dieser Datei (Ergebnisse), **Zeile-1-Kopf im selben Zug** nachziehen
  (auf ENTSCHIEDEN, sobald der A/B ein Verdikt traegt -- unabhaengig vom Vorzeichen, weil der
  Knopf ohnehin bleibt), danach sofort `python tools/generate_prereg_index.py`.
- **STATUS.md Abschnitt 1 und Abschnitt 5** sowie `archive/history.md` fortschreiben.
- **Rueckwaerts-Pruefung**:
  `grep -rn "return_order\|dome_return_order\|RETURN_ORDER_MODE" evaluations/ docs/ tools/ engine/`
  -- betroffen sind mindestens `PREREG_dome_stack_information_sets.md` (Variante A, die
  Reihenfolge ist nur dem Rueckleger bekannt), `PREREG_moon_stack_order.md` par.2 (dort steht die
  Korrektur der ungenauen Notiz aus par.2 hier), `docs/knobs.md`,
  `docs/architecture_reference.md`.
- **Laufzeit-Zeile** in `docs/measured_runtimes.md` (A/B Referee, n=150, 6 Prozesse, s je Partie).
- **Elo-Register: NICHTS.** Ein A/B desselben Netzes mit gegen ohne Knopf ist keine Kante am
  Champion; erst wenn Modus 1 Default WIRD (Nutzer-Entscheid), aendert sich die gemessene
  Identitaet des Champions -- und dann gilt Feedback `measured_identity_gets_own_bxx`, also ein
  neuer Knotenname, keine stille Umwidmung.

### 5. Stopp-Punkte fuer den Nutzer

- **Ob Modus 1 Default wird** (par.6: "Wird Modus 1 Default (Nutzer-Entscheid), gilt er fuer die
  v29-Erzeugung") -- Aufnahme ins Rezept entscheidet der Nutzer, auch bei positivem A/B.
- **Ob Modus 2 einen eigenen Arm bekommt** (Schritt 5). **Nutzer fragen.**
- **Ein Kopf, der Plattentypen im Block unterscheidet** (par.8a Befund 1, "die naechste Stufe,
  nicht registriert"): kein Bau ohne eigene Registrierung.
- **Anker-Drift ROT: anhalten** (der Anker liest den Knopf nicht, ROT waere also ein Hinweis auf
  etwas anderes).
- **Kein Push, keine Loeschung** ohne pfadgenaue Freigabe.

### 6. Abhaengigkeiten und Reihenfolge

**Vorher:** Promotion und Neuverankerung sind durch (par.6 -- der Knopf durfte nicht zwischen den
Promotionskanten liegen, das ist eingehalten); der Bau ist erledigt. Innerhalb des
Begleitprogramms (`PREREG_v29_window.md` par.7 Punkt 4) liegt dieser Punkt in derselben Gruppe
wie die Stapel-Stopp-Regel und die Peek-Bewertung; alle drei sind billiger als der Tiling-Umbau
(`PREREG_round_transition_search_sampling.md` par.9) und laufen davor. **Danach:** wird Modus 1
Default, gilt er fuer die v29-Erzeugung -- dann muss die Entscheidung VOR dem Start des Sockels
fallen, sonst faehrt der Korpus zwei Verhalten.

## par.9 A/B GEMESSEN (2026-09-14): kein messbarer Effekt, der Knopf bleibt

`tools/night_v29_return_order_ab.sh`, Fahrplan Nr. 29. Beide Seiten dasselbe Modell
(`alphazero_v28-b02_brierbest.onnx`) auf demselben Wheel, unterschieden durch GENAU ein
Spec-Feld (geprueft: 14 Felder je Datei, ein Unterschied).

| Seed     | mode1 : mode0 | McNemar p | gepaarte Diff           | Splits        | Punkte mode1 / mode0 | Wanduhr |
| -------- | ------------- | --------- | ----------------------- | ------------- | -------------------- | ------- |
| 20261071 | 74 : 76       | 1,0000    | -0,027 [-0,144, +0,091] | **70 von 75** | 54,14 / 54,23        | 2.080 s |
| 20261072 | 74 : 76       | 1,0000    | -0,027 [-0,201, +0,148] | **64 von 75** | 52,88 / 53,07        | 2.664 s |

**VERDIKT nach par.5 Punkt 1: kein messbarer Effekt.** Der Vorzeichentest verfehlt p < 0,05
deutlich (beide Seeds p = 1,0), das Intervall der gepaarten Differenz schliesst die Null in
beiden Faellen ein, und die Punkte sind gleich. **Der Knopf bleibt trotzdem** -- par.0/par.1,
Nutzer-Praezedenz: der Massstab ist Vollstaendigkeit, nicht Elo. Ein legaler Zug, den die Suche
nicht waehlen kann, ist eine Luecke im Modell, auch wenn sie nichts kostet.

**Die identische Endsumme in beiden Seeds ist Zufall, kein Alarm** (Pruefung wegen
`feedback_wheel_neu_bauen_nach_engine_aenderung`, "Zahlengleichheit ist ALARM"): die Struktur
dahinter unterscheidet sich klar -- 5 gegen 11 informative Paare, verschiedene Punkte,
verschiedene Laufzeiten. Bei 70 bzw. 64 Splits tragen nur wenige Paare ueberhaupt zur Bilanz bei.

**Der Split-Anteil ist der eigentliche Befund: 93 und 85 Prozent.** In der grossen Mehrheit der
Paare spielen beide Modi dasselbe Ergebnis. Das bestaetigt den vorab registrierten strukturellen
Deckel aus par.8a Befund 1: der Value-Kopf sieht die Reihenfolge nur als TYP-Folge
(`features.rs:212`, oberste vier Positionen des eigenen Blocks als +1 Spezial / -1 Joker / 0);
Permutationen gleichtypiger Platten sind fuer das Netz identisch, und Modus 1 faellt dann per
Gleichstand auf die Ziehreihenfolge zurueck. Die Wahl kann also nur dort wirken, wo die
Restplatten VERSCHIEDENE Typen haben -- und das ist selten.

### Abweichungen von par.5, bewusst und vorab im Skriptkopf festgehalten

1. **Nicht ueber den Referee, sondern ueber `paired_gating`.** par.5 und der AGENTEN-AUFTRAG
   schreiben `frozen_referee_match.py` vor (Live gegen eingefrorenes v28-b02-Artefakt). Als das
   registriert wurde, lagen Live-Wheel und Artefakt auf DERSELBEN Aera; seit dem v29-Wheelwechsel
   nicht mehr (live 39994362fba145a6 / 794, Artefakt 39648b95bbba1acf / 755). Der Referee
   verweigert dann den Handshake, und mit `--force-cross-era` waere Knopf PLUS Aerawechsel
   gemessen -- gerade nicht das, wonach par.5 fragt. `paired_gating` faehrt beide Seiten auf dem
   liven Wheel mit demselben Modell und unterscheidet sie nur ueber die Spec; das ist naeher an
   par.5s Absicht als der Wortlaut.
2. **SPRT praktisch abgeschaltet** (`--sprt-alpha 0.001 --sprt-beta 0.001`, Wald-Schranken
   +-6,907 statt +-2,944), damit beide Laeufe die vollen 75 Paare = 150 Partien fahren, wie par.5
   es verlangt. Beide endeten folgerichtig mit `UNDECIDED_CAP_REACHED`.

### Was NICHT gemessen ist: die Kosten

par.5 sieht kein Kostentor vor, und ein gepaarter Lauf taugt nicht dafuer -- beide Seiten spielen
je zur Haelfte mit Modus 1, die Blockzeiten sind gemischt. **Relevant wird das, wenn Modus 1
Default werden soll** (Fahrplan Nr. 29, Entscheidspalte "Modus 1 als Default?"): nach par.8a
Befund 2 braucht Modus 1 die Sicht des Ruecklegers im Folgezustand, und die liefert
`net_leaf_eval` nur ueber den gespiegelten zweiten Vorwaertspass -- **ein `eval_pair`-Batch je
Kandidat statt eines Passes**. Bei einer Erzeugung ueber rund zwoelf Stunden schlaegt das durch.
Vorschlag des Koordinators, offener Nutzer-Entscheid: ein kurzes Kostentor nach dem Muster von
Nr. 30 und Nr. 35 (Wanduhr je Partie mit gegen ohne Knopf, Schwelle 25 Prozent, rund 24 min je
Lauf), bevor der Modus ins Rezept geht.

### Offen aus par.5 Punkt 2

Die Diagnostik aus den Logzeilen (`[return_order] mode=.. drawn=[..] chosen=[..]`): Anteil der
Rueckgaben mit abweichender Reihenfolge, Wiederkehr-Rate, Ziehungen in den eigenen Block. Der
Split-Anteil oben ist ein starker Indikator, ersetzt sie aber nicht.

## par.10 KEINE WEITERE STUFE (Nutzer-Entscheid 2026-09-14)

Nach dem Nullbefund aus par.9 kam die Frage auf, ob die BAUFORM schuld ist. Sie ist es
nachweislich zur Haelfte: `choose_return_order` (`self_play.rs:771-798`) benutzt **weder Suche
noch Policy** -- die Kandidaten werden auf Spielkopien angewandt und mit EINEM `net_leaf_eval` je
Kandidat bewertet, danach argmax. Fuer dasselbe Problem gibt es im Baum eine zweite, bessere
Bauform: der Mondstapel-Fan-out gibt seine Varianten als Aktionen IN den Suchbaum
(`net_mcts.rs:2241-2255`) und laesst die Suche entscheiden.

**Erwogen und VERWORFEN wurde ein "Modus 3"** nach diesem Muster: Fan-out im Suchbaum, Prior
nicht aus einem neuen Kopf (die sind gesperrt, `special_tile_yield` par.12), sondern aus den
bereits vorhandenen Modus-2-Handregel-Scores ueber dieselbe Plackett-Luce-Funktion.

**Nutzer-Entscheid, woertlich:** *"nein das brauchst nicht rechnen. weil das netz es nicht sauber
kann."* -- und das schliesst auch die offene Diagnostik aus par.5 Punkt 2 ein, die vorher
gerechnet werden sollte.

**PRAEZISIERT auf Nutzer-Nachfrage am selben Tag** (*"ich hab eher gemeint dass du es nicht
messen kannst, weil es das netz bis dato nicht sauber gemacht hat. henne ei problem"*). Der
Koordinator hatte den Entscheid zuerst als "der Engpass sitzt in der Eingabe, strukturell nicht
aufloesbar" registriert. **Das ist zu stark und war falsch.** Der Punkt ist ein
Henne-Ei-Problem, kein Beweis der Unmoeglichkeit:

* **Modus 1 war bei der v29-Erzeugung AUS** (Default 0; die Erzeugungs-Spec
  `models/start_by_search_on.spec.json` fuehrt das Feld nicht). Im Korpus kommt also keine
  bewusst gewaehlte Rueckgabereihenfolge vor.
* Das Netz hat damit **nie gelernt, dass die Reihenfolge etwas bedeutet** -- auch nicht im Rahmen
  dessen, was die Typ-Folge in `features.rs:212` (+1 Spezial / -1 Joker / 0) hergaebe.
* **Ein A/B an genau diesem Netz kann den Nutzen deshalb nicht zeigen**, egal in welcher
  Entscheidungsform. Der Nullbefund aus par.9 misst ein Netz, dem die Voraussetzung fehlt.

Das ist dieselbe Struktur wie bei P.12 (`designs` fehlt im v29-Korpus, 18 Spalten mit Norm exakt
0) und bei der Startsetzungs-Phase (`PREREG_start_dome_choice.md` par.11): **ein Merkmal, das die
Erzeugung nicht traegt, kann das Training nicht aufgreifen**
(`feedback_record_field_must_precede_generation`).

**Was das kostet, und warum trotzdem nicht weiter investiert wird:** die Frage sauber zu
beantworten hiesse, mit Modus 1 einen Korpus zu erzeugen (rund 12 h), darauf zu trainieren und
erst dann das A/B zu fahren -- ein ganzer Generationsarm fuer einen Knopf, dessen Wirkung nach
par.8a strukturell gedeckelt ist. Der Nutzer hat das nicht angeordnet; der Koordinator schlaegt
es auch nicht vor.

**Was bleibt:** der Knopf `return_order_mode` mit Modus 0 (Default, Bestand), Modus 1 und Modus 2,
gebaut und abgenommen. Er bleibt aus Gruenden der Vollstaendigkeit -- die Rueckgabereihenfolge ist
ein legaler Zug, und die Suche kann ihn jetzt waehlen.

**Der Status bleibt OFFEN.** Die Prereg ist NICHT erschoepft: par.4 ist gebaut, par.5 Punkt 1 an
einem Netz ohne Voraussetzung gemessen, Punkt 2 gestrichen, Modus 3 verworfen -- aber die
Kernfrage ("traegt die Wahl?") ist mangels passendem Korpus unbeantwortet, nicht verneint. Wer
sie je beantworten will, erzeugt VORHER mit Modus 1.

## par.11 DER WEG AUS DEM HENNE-EI: Streuung in der Erzeugung (Nutzer-Vorschlag 2026-09-14)

Nutzer woertlich: *"ich wuerd bewusst im self play spiele generieren mit stapelzug > 5 und dort
dann zufaellig zuruecklegen lassen. dann hat der value head bzw. die policy was zum lernen"*.

Das loest par.10 an der Wurzel: nicht den ENTSCHEIDER verbessern (Modus 1/2/3), sondern dem Netz
ueberhaupt erst Beispiele geben, aus denen die Wirkung lernbar ist. **Praezedenz im eigenen Baum:**
genau so wurde die Startkuppel behandelt (`MOSAIC_START_SLOT_RANDOM_P=0.15`,
`PREREG_v29_window.md` par.6b, Nutzer 2026-09-12 "damit das netz auch mal sieht welchen einfluss
die startkuppel hat").

### Bauform, wie sie sich aus dem Bestand ergibt (VOR dem Bau registriert)

* **Erzeugungsknopf** nach dem Muster von `MOSAIC_START_SLOT_RANDOM_P` (`self_play.rs:1290-1310`):
  Wahrscheinlichkeit je Rueckgabe mit mindestens zwei Restplatten, aus dem Partie-RNG, Default 0
  = bitidentischer Bestand.
* **Kein Permutations-Deckel noetig.** `RETURN_ORDER_MAX_PERMUTED = 3` existiert nur, weil das
  AUFZAEHLEN der Kandidaten `n!` kostet (Kommentarbeleg `self_play.rs:625`: "Ziehserie kann
  laenger werden (MAX_STACK_PEEKS = 20), und n! waere ..."). Eine einzelne ZUFALLS-Permutation
  braucht keine Aufzaehlung -- der ganze Rest kann gemischt werden. Genau das trifft den vom
  Nutzer genannten Fall langer Ziehserien.
* **Der Record-Vertrag ist hier SAUBERER als bei der Startkuppel.** Dort musste
  `policy_target_valid = false` gesetzt werden, weil die gewaehlte AKTION zufaellig war. Die
  Rueckgabereihenfolge hat dagegen keine Policy-Dimension (par.2); der Zug
  `ChooseDrawStackSlot` bleibt derselbe. **Policy-Ziel und Value-Labels bleiben also gueltig.**
  Noetig ist nur eine Markierung (`return_order_randomized: true`) analog zu
  `start_slot_randomized`, damit Sonden die Faelle wiederfinden.

### Was das Netz daraus lernen kann -- und wo die Grenze bleibt

Der Value-Kopf sieht die Blockreihenfolge heute nur als TYP-Folge ueber die obersten vier
Positionen (`features.rs:212`, +1 Spezial / -1 Joker / 0). Innerhalb dieser Aufloesung ist die
Wirkung lernbar (etwa "Spezial oben ist besser"), darueber hinaus nicht.

**Und genau hier trifft der Vorschlag auf den zweiten offenen Strang: P.12.** Der Sichtpunkt
"Designs im eigenen Block" (18 Bits, `stack_top_feature`) loest genau diese Reihenfolge FEIN auf
statt nur als Typ -- er steht seit v29 im Encoder, ist aber tot, weil das Feld `designs` im
v29-Korpus fehlt (`PREREG_v29_window.md` par.6d: Spaltennorm exakt 0). Seit Commit 31a1321
schreibt der Serializer es, **ab der naechsten Erzeugung ist P.12 belebt**.

**Beides zusammen ist der eigentliche Hebel:** die Streuung liefert die VARIANZ, P.12 die
AUFLOESUNG. Einzeln bleibt jeweils die andere Haelfte der Engpass -- Streuung ohne P.12 stoesst
an die Typ-Folge, P.12 ohne Streuung sieht nur die eine Reihenfolge, die der Bestand ohnehin
legt. Beide Voraussetzungen fallen mit derselben Erzeugung zusammen.

**Status:** Vorschlag registriert, NICHT gebaut, nicht eingetaktet. Naechster natuerlicher Ort
waere die v30-Erzeugung (dort ist P.12 ohnehin belebt); die Dosis ist ein Nutzer-Entscheid wie
bei der Startkuppel (dort 0,15).

## par.11a BAUSTAND 2026-09-14: `MOSAIC_RETURN_ORDER_RANDOM_P` (noch nicht kompiliert)

Knopf nach par.11 gebaut, Default 0 = bitidentischer Bestand.

**Der Zufallsweg ist NICHT der Partie-RNG**, sondern der je Entscheid abgeleitete Strom:
`derive_search_seed(game_seed ^ RETURN_ORDER_SEED_DISTINGUISHER, move_number)`, daraus je
Rueckgabe ein frischer `StdRng`. Das ist die Konvention aus `PREREG_search_rng_split`
(Praezedenz im selben Block: `EXCURSION_SEED_DISTINGUISHER`, Weg B). **Der entscheidende Vorteil
gegenueber dem Partie-RNG:** dessen Strom verschiebt sich auch bei `p > 0` NICHT -- Aufbau,
Nachfuellen und Labels laufen Zug fuer Zug wie im Bestandsarm, die Streuung ist also isoliert und
der Lauf bleibt seed-reproduzierbar. Ein reiner Zustands-Hash ohne `game_seed` wurde verworfen,
weil `GameState` keinen Seed traegt (`state.rs:65-111`) und die Streuung dann eine
deterministische Funktion der gezogenen Plattennummern waere -- Behandlung und Zustand
korreliert, was die Varianz gerade entwertet.

**Gebaut** (`self_play.rs`): Distinguisher, Traeger `ReturnOrderRandom`,
`sanitize_return_order_random_p` (Wert ausserhalb [0,1] -> 0 plus Warnung), `return_order_random_p`,
`sample_random_return_order` (Muenze plus `shuffle` ueber den GANZEN Rest, ohne den
Permutations-Deckel -- der gilt nur fuers Aufzaehlen), Einhaengung in
`resolve_and_apply_stack_draw_with` NACH dem Entscheider, Record-Markierung
`return_order_randomized`, Diagnostikzeile `[return_order] random before=.. after=..`.
Dazu `lib.rs` (`engine_config`), `knob_registry.rs`, je ein `None` in `py.rs` und `referee.rs`.
**Acht Tests** in `mod return_order_random_tests`.

**Markiert wird die gefallene MUENZE, nicht die abweichende Permutation** -- eine Ziehung darf
die Ziehreihenfolge treffen, genau wie beim Startslot. **`policy_target_valid` bleibt
unberuehrt** (par.11: die Reihenfolge hat keine Policy-Dimension, der Zug bleibt derselbe).

**Keine oeffentliche Signatur beruehrt**, alle fuenf Aufrufstellen liegen in `engine/src`;
`SearchConfig` wurde bewusst nicht angefasst, weil das Struct-Literal in
`engine/examples/kernbeweis_910002_probe.rs` sonst E0063 wirft. Kontrakt-Hash und
Netz-Paritaets-Fixture nach Code-Lage nicht betroffen (`lib.rs:684-701`; das Record-Feld entsteht
nur bei `p > 0`, der Fixture-Lauf faehrt ungesetzt).

**BAU-TOR 2026-09-14 GRUEN, die Herleitung ist damit belegt:** `cargo test --release --lib`
**654 gruen** (646 Bestand plus die acht neuen, 0 rot, **Netz-Paritaets-Fixture UNVERAENDERT**),
`cargo test --release --no-run` deckt examples und benches ab (keine E0063), Wheel gebaut und
installiert, **Kontrakt-Hash UNVERAENDERT 39994362fba145a6** (gegengeprueft am laufenden Wheel,
das den Knopf jetzt mit `return_order_random_p: 0.0` fuehrt), `docs/knobs.md` neu generiert
(123 Knoepfe), Konventions-Check gruen, **Anker-Drift GRUEN und Konservierung GRUEN** gegen
`hv4_anchor` (`anchor_drift_live_wheel_20260914_returnstreu.json`,
`anchor_conservation_artifact_wheel_20260914_returnstreu.json`).

**Der Knopf ist damit einsatzbereit**, steht auf Default 0 und wartet auf die naechste Erzeugung.
Dosis offen (Nutzer-Entscheid, Startkuppel faehrt 0,15).

### PFLICHT VOR DER NAECHSTEN ERZEUGUNG: der Lauf-Treiber kennt den Knopf nicht

`tools/selfplay_manifest.py:55` liest `engine_config_json()` im ELTERNPROZESS, waehrend
`self_play.py:236` die Erzeugungs-Variablen erst im WORKER vor `import mosaic_rust` setzt. Per
Shell-Export erbt beides dieselbe Variable und das Manifest stimmt. **Wird spaeter ein Flag
`--return-order-random-p` nach dem Muster von `--start-slot-random-p` gebaut, muss es
ZUSAETZLICH ins `cli_args`-Dict** -- sonst zeigt `engine_config` 0.0, waehrend die Worker
streuen. Das ist die Fehlerklasse "fehlendes Flag = stiller Default"
(`feedback_run_manifest_gegen_referenz`). Flagname, Dosis und Zeitpunkt sind offen; die Dosis ist
nach par.11 ein Nutzer-Entscheid (Startkuppel: 0,15).

## par.11b DOSIS UND SEMANTIK (Nutzer-Entscheid 2026-09-14) -- Umbau noetig

Gebaut war zunaechst: Muenze JE RUECKGABE mit mindestens ZWEI Restplatten
(`self_play.rs:941-946`). Beides wird geaendert.

**1. Schwelle ab DREI Restplatten** (Nutzer: *"bei 2 macht die reihenfolge wenig sinn. ab 3 kann
ich die reihenfolge beeinflussen"*).

**2. Semantik: "in 15 Prozent der PARTIEN mindestens einmal"**, nicht je Rueckgabe. Das ist
dieselbe Lesart wie bei der Startkuppel-Streuung (`MOSAIC_START_SLOT_RANDOM_P`, dort je Partie
und je Spieler).

**Warum die Unterscheidung hier stark ins Gewicht faellt**, und das ist ein Nutzer-Befund:
*"sobald die spezialfliesen wertungsplatte aktiv ist, zieht das netz in der arena von selber
schon viele kuppelkarten um zu schauen wo welche kuppelplatten sind."* Eine Partie hat also nicht
ein oder zwei Gelegenheiten, sondern viele -- eine Muenze je Rueckgabe haette entsprechend
haeufiger gestreut als beabsichtigt.

**Gemessen dazu, aus den Logs von Nr. 29** (`return_order_ab_mode1_vs_mode0_s20261071.json`,
150 Partien, Seite mit Modus 1): **29 Abweichungen von der Ziehreihenfolge, also 0,19 je
Partie**; die Diagnostikzeile entsteht nur bei tatsaechlicher Abweichung. Laenge der gezogenen
Serie an diesen Stellen: 4 (3x), 6 (2x), 7 (4x), 8 (10x), 12 (10x) -- **alle mindestens vier,
zwei Drittel bei acht oder zwoelf**. Das stuetzt sowohl die Schwelle 3 als auch den
Nutzer-Hinweis auf lange Ziehserien.

**Nebenbefund, der par.9/par.10 nachtraeglich erklaert:** bei 0,19 Abweichungen je Partie konnte
Modus 1 in Nr. 29 gar nichts bewegen -- unabhaengig davon, wie gut er entscheidet. Der
Nullbefund dort ist damit nicht nur "Henne-Ei", sondern zusaetzlich eine Frage der Haeufigkeit.

### Bauform des Umbaus (VOR dem Bau registriert)

* `order.len() < 2` wird zu `< 3`.
* Die Muenze faellt EINMAL JE PARTIE. Faellt sie, wird GENAU EINE Gelegenheit gestreut.
* **Welche Gelegenheit: per GLEICHGEWICHTETEM Reservoir**, nicht die erste -- sonst laegen die
  gestreuten Stellen systematisch in fruehen Runden. Praezedenz im selben Modul: der Ausflug
  zieht seine Abzweigstelle per Reservoir (`MOSAIC_EXCURSION_PROB`, `reservoir_step`).
* **KEINE Gewichtung nach Serienlaenge** (Nutzer-Entscheid 2026-09-14). Der Koordinator hatte
  eingewandt, kurze Serien koennten die langen verdraengen, weil sie haeufiger sind, und eine
  Laengengewichtung vorgeschlagen. Nutzer dazu: *"das liegt am netz es zu lernen was sinnvoller
  ist. wir zeigen es ihm nur."* Die gestreuten Stellen sollen also der NATUERLICHEN Verteilung
  der Gelegenheiten folgen; eine kuenstlich ausbalancierte Streuung wuerde dem Netz eine
  Haeufigkeitsstruktur zeigen, die im Spiel nicht vorkommt. Das ist dieselbe Linie wie
  `feedback_dont_calibrate_to_plate_blind_play`: der Eichgrund ist die tatsaechliche Verteilung,
  nicht eine zurechtgelegte.
* **RUNDE 5 IST AUSGESCHLOSSEN** (Nutzer 2026-09-14: *"in runde 5 macht es keinen sinn, da gibt
  es keine mehr"*). Die Rueckgabe-Reihenfolge steuert, WANN eine Platte wiederkommt; nach Runde 5
  (`NUM_ROUNDS = 5`, `state.rs:15`) folgt die Endwertung, die Reihenfolge kann sich also nicht
  mehr auswirken. Eine Streuung dort waere reiner Schaden ohne Lerngewinn.
* **KEINE Bevorzugung frueher Runden: Runden 1 bis 4 gleichgewichtet** (Nutzer-Entscheid
  2026-09-14: *"nein, nicht zuviel einschraenken. soll das netz selber lernen und abschaetzen"*).
  Der Nutzer hatte zuvor angemerkt, frueh schmerze eine schlechte gestreute Reihenfolge weniger,
  weil die Punkte nicht unter 0 fallen (Score-Clamp, `PREREG_score_clamp_incentive.md`) -- diese
  Schadensbegrenzung wird bewusst NICHT eingebaut. **Der Unterschied zur Runde-5-Regel ist
  wesentlich:** Runde 5 faellt aus MECHANIK weg (die Reihenfolge kann sich dort nicht mehr
  auswirken), eine Bevorzugung frueher Runden waere dagegen eine Gewichtung der Verteilung -- und
  die bleibt aus demselben Grund aus wie die Laengengewichtung: das Netz soll die Kosten selbst
  abschaetzen lernen, wir zeigen ihm nur die Faelle.
* Zufall weiterhin aus dem abgeleiteten Strom (`derive_search_seed` plus
  `RETURN_ORDER_SEED_DISTINGUISHER`), nicht aus dem Partie-RNG.
* Default 0 bleibt bitidentisch; der Knopfname bleibt, nur seine Bedeutung wird praeziser
  dokumentiert (Registratur, `docs/knobs.md`, argparse-Hilfe in `self_play.py`).

**Dosis: 0,15** (Nutzer-Entscheid, dieselbe Zahl wie die Startkuppel-Streuung).

**Der Knopf ist damit NOCH NICHT einsatzbereit** -- die Abnahme vom 2026-09-14 (par.11a) gilt fuer
die alte Semantik. Nach dem Umbau ist das Bau-Tor zu wiederholen.

## par.11c DOSIS ENTSCHIEDEN, Muenze bleibt je Rueckgabe (Nutzer 2026-09-14)

**par.11b Punkt 2 und 3 (Muenze je Partie plus Reservoir) werden NICHT gebaut.** Der Bau hat
gezeigt, dass die Form im Rueckgabe-Pfad strukturell nicht erreichbar ist: der Ausflug kann sein
Reservoir fahren, weil sein Kandidat ein ZUSTANDS-KLON ist und erst nach der Partie verbraucht
wird (`self_play.rs:3601`, `:3933`, `:6233`) -- ein spaeterer Kandidat verdraengt den frueheren
kostenlos. Die Rueckgabe-Permutation wird dagegen SOFORT angewandt (`self_play.rs:1119`), die
Partie laeuft aus dem gestreuten Zustand weiter. Ein Reservoir mit sofortiger Anwendung
degeneriert exakt zu "erste Gelegenheit" -- genau die Fruehlage, die par.11b ausschliessen
wollte.

**Stattdessen ueber die DOSIS** (Nutzer: *"Dosis reicht. da brauchen wir nicht strenger sein als
notwendig"*). Eine unabhaengige Muenze je Gelegenheit trifft jede Stelle GLEICH WAHRSCHEINLICH --
die Position ist also exakt richtig, nur die Rate war falsch parametriert. Umgerechnet auf der
gemessenen Haeufigkeit:

* **11,07 Gelegenheiten mit mindestens drei Restplatten je Partie** (142.945 Faelle auf 12.907
  Partien, `PREREG_moon_stack_order.md` par.9b).
* Fuer "in 15 Prozent der Partien mindestens einmal": `p = 1 - 0,85^(1/11,07)` = **0,0146**.
* **Dosis also rund 0,015, nicht 0,15.** Erwartungswert 0,16 Streuungen je Partie; gelegentlich
  zwei statt genau einer.

**WARNUNG, die bestehen bleibt:** mit p = 0,15 laege die Partie-Rate bei rund 80 Prozent. Der
Wert aus par.11b darf so NICHT in eine Erzeugung.

**NACHTRAG 2026-09-18, 23:50 -- die Herleitung oben steht auf einer FREMDEN GRUNDMENGE.** Die
11,07 stammen aus `PREREG_moon_stack_order.md` par.9b und zaehlen dort **Mondstapel-Dreierstapel**
(Sonnensteine aus Fabriken), nicht zurueckgelegte Kuppelplatten. Am v30-Korpus gemessen sind es
**0,2225 Gelegenheiten mit mindestens drei Restplatten je Partie** (n = 1.778 Stapelzuege aus 400
Partien, Grundmenge Stapelzuege der Sockel-Klasse) -- ein Faktor 50. Die eigene Messung in par.11b
(0,19 Abweichungen je Partie) haette den Fehler sofort gezeigt. **Mit p = 0,0146 wuerde in 0,33
Prozent der Partien gestreut, nicht in 15 Prozent** (13 Streuungen je 4.000 Partien); fuer das
registrierte Ziel waere p = 0,52 noetig. Der Entscheid "15 Prozent der Partien" bleibt gueltig, die
ZAHL dahinter nicht. Details und Vorlage: 12.12.

**Gebaut sind die anderen beiden Punkte:** Schwelle ab drei Restplatten
(`RETURN_ORDER_MIN_REST = 3`) und das Rundenfenster 1 bis 4 gleichgewichtet
(`return_order_round_allowed`, Fruehausstieg vor dem RNG-Aufbau). Elf Tests im Modul.

### Der Zweck, noch einmal praezisiert

Nutzer: *"ich will ja nur dass das netz sieht das kuppelplatten auch einfach so aus dem stapel
gezogen werden koennen."* Es geht also um ABDECKUNG des Zustandsraums, nicht darum, eine bessere
Reihenfolge zu lehren -- dieselbe Absicht wie bei der Startkuppel-Streuung (par.6b der
Fenster-Prereg: "damit das netz auch mal sieht welchen einfluss die startkuppel hat"). Eine
niedrige Dosis genuegt dafuer; sie muss die Verteilung nicht verschieben, nur den Fall zeigen.

## par.12 ARCHITEKTUR KONKRETISIERT (Code-Audit 2026-09-15, Nutzer-Auftrag "konkretisiere moegliche architektur optimierungen")

Kein Bau, kein Entscheid. Drei Grenzen sind am Code belegt, vier Optionen darauf zugeschnitten,
eine Reihenfolge vorgeschlagen. Der Streu-Knopf (par.11-11c) bleibt der erste Schritt; er ist
gebaut und wirkt mit der naechsten Erzeugung.

### 12.0 Drei strukturelle Grenzen (am Code geprueft)

1. **Der Suchbaum faechert die Rueckgabe nicht auf.** `game.rs:403-430`
   (`generate_draw_stack_moves`): ein Kandidat je (Platte, Slot), `return_order` = Ziehreihenfolge
   aus `pending_stack_draw`; Kommentar `:414-418` "wie moon_order ... NICHT kombinatorisch
   aufgefaechert". Im Baum gibt es die Wahl also nicht, egal welcher Modus laeuft.
2. **Der Entscheider steht AUSSERHALB der Suche und bewertet mit einem Blatt.**
   `self_play.rs:750-816` (`choose_return_order`): Modus 1 legt bis zu 6 Permutationen der
   ersten drei Restplatten (`RETURN_ORDER_MAX_PERMUTED = 3`, `:629`) auf Spielkopien, spielt
   beide Stufen (`ChooseDrawStackSlot`, `ChooseDomeRotation`, `:786-787`) und nimmt
   `net_leaf_eval(net, &probe.state)[returner]` (`:793`) -- EIN Vorwaertspass je Kandidat, kein
   Baum. Aufgerufen am Ende der Ziehserie (`resolve_and_apply_stack_draw_with`, `:1168-1169`),
   in der GUI (`py.rs:1062-1071`) und im Referee (`referee.rs:846-851`).
3. **Der Encoder sieht die eigene Reihenfolge nur als Typfolge.** Abschnitt 15
   (`features.rs:130-160`): Indizes 4..7 = Typ der obersten VIER Positionen des obersten eigenen
   Blocks, +1 Spezial / -1 Joker / 0. Die Designs des eigenen Blocks liefert `serialize.rs:111-117`
   **SORTIERT** ("weil der Spieler die Reihenfolge im zurueckgelegten Block nicht mehr
   auseinanderhaelt", `:141-143`) -- P.12 (18 Bits, ab v30 belebt) traegt also die MENGE der
   eigenen Designs, nicht ihre Reihenfolge. Zwei Permutationen gleichtypiger Platten sind fuer das
   Netz identisch; Modus 1 waehlt dann per Gleichstand die Ziehreihenfolge (par.8a Punkt 1).

Die Regel dazu (`docs/engine_manual.md:84-90`): der Rueckleger kennt seine Reihenfolge, der Gegner
sieht nur die Vorderseiten der gezogenen Platten. Eine feinere EIGENE Sicht ist also regelkonform;
Grenze 3 ist eine Bauentscheidung vom 2026-09-13, keine Regel.

### 12.1 Vier Optionen

**R1 Sensitivitaets-Sonde (Instrument, kein Bau am Spiel).** Beantwortet das Henne-Ei aus par.10
mit einer Zahl: an Rueckgaben mit mindestens drei Restplatten (Grundmenge wie
`RETURN_ORDER_MIN_REST`) die Spannweite des Value-Kopfs ueber die bis zu 6 Permutationen aus
Sicht des Ruecklegers -- exakt die Groesse, die Modus 1 intern berechnet (`:771-799`). Quelle:
Zustaende aus `--log-games`-Artefakten oder dem v29-Korpus, Netz v29-b03 (heute) und spaeter das
v30-Netz. Einheit: max minus min der Siegwahrscheinlichkeit je Rueckgabe; Kennzahlen Median und
Anteil ueber 0,01. **Lesart vorab:** liegt die Spannweite bei v29-b03 nahe 0 (Erwartung nach
Grenze 3 und Henne-Ei), ist jedes A/B an diesem Netz sinnlos, egal in welcher Bauform; steigt sie
am v30-Netz (Streu-Korpus), hat das Netz die Wirkung gelernt und die Entscheidungsform wird zur
Frage. Getrennt ausweisen: Permutationen mit GLEICHER Typfolge (Grenze 3 verbietet dort jede
Spannweite) gegen verschiedene Typfolge. Kosten: Bau rund 1 h (ANNAHME), Lauf Minuten.

### 

### 12.2 Reihenfolge (Vorschlag, Entscheide beim Nutzer)

1. **R1 jetzt am v29-b03** (Minuten): beziffert das Henne-Ei. Erwartung: Spannweite nahe 0.
2. **v30-Erzeugung mit `MOSAIC_RETURN_ORDER_RANDOM_P=0.015`** (par.11c) und belebtem P.12; R2
   nur, wenn R1 die Typfolge als Deckel zeigt -- dann VOR der Erzeugung ins Record-Feld.
   ~~ENTSCHIEDEN 2026-09-15 (Nutzer: "bleibt aus"): Modus 1 bleibt in der v30-Erzeugung AUS~~
   **UEBERHOLT am selben Tag nach 12.5 -- ENTSCHIEDEN 2026-09-15 (Nutzer: "mit r2 und modus 1
   ein"): R2 wird gebaut UND Modus 1 ist in der v30-Erzeugung AN.** Einzelheiten und
   Bauvorgaben in 12.6.
3. **R1 am v30-Netz** wiederholen. Steigt die Spannweite: **A/B Modus 1 gegen 0** (par.5) am
   v30-Champion, 200 Paare ohne Frueh-Stopp, danach R4 als Knopf. Bleibt sie bei 0: die
   Rueckgabe-Reihenfolge ist fuer dieses Netz kein Hebel, Prereg auf ENTSCHIEDEN
   ("nicht lernbar in dieser Sicht") -- ausser R2 wird nachgezogen.
4. **R3** nur mit Weg A des Mondstapels und nur nach Rahmen-Entscheid.

**Was hier absichtlich fehlt:** ein Heuristik-Ziel fuer die Reihenfolge (Modus 2 als Trainingsziel
waere derselbe Fehler wie ein Handregel-Label beim Mondkopf, `moon_stack_order` par.12 B3) und
jede Aenderung an der Sicht des GEGNERS (die Regel gibt ihm die Reihenfolge nicht).

### 12.4 R1 GEMESSEN (2026-09-15): die Erwartung "Spannweite nahe 0" ist WIDERLEGT

`tools/probes/return_order_sensitivity_r1.py`, Artefakt
`evaluations/artifacts/return_order_sensitivity_r1.json`. Netz `v29-b03_brierbest`, Quelle
`selfplay_v28-b02-policy_*` (6 Dateien), **3,6 s fuer 300 Faelle**. Kein Bau am Spiel, kein
Wheel, keine Anker-Drift: die Sonde permutiert das Zustands-JSON und ruft
`state_features_from_json` / `state_planes_from_json` / eine EINMAL gebaute ONNX-Sitzung.

| Groesse                                        | Wert                                         |
| ---------------------------------------------- | -------------------------------------------- |
| Selbsttest (derselbe Zustand zweimal bewertet) | **0,0**                                      |
| eigene Bloecke mit mindestens 3 Platten        | n = 407                                      |
| davon mit AENDERBARER Typfolge                 | **300 = 73,7 Prozent**                       |
| Spannweite max-min des Value-Kopfs (n = 300)   | Median **0,0188**, Mittel 0,0231, Max 0,0933 |
| Anteil ueber 0,01                              | **81,3 Prozent**                             |

**Die vorab registrierte Lesart greift damit in ihrem ZWEITEN Zweig, nicht im ersten.** par.12.1
sagt: *"liegt die Spannweite bei v29-b03 nahe 0, ist jedes A/B an diesem Netz sinnlos"*. Sie
liegt nicht nahe 0 -- median 1,9 Prozentpunkte Siegwahrscheinlichkeit, in vier von fuenf Faellen
ueber einem Prozentpunkt, und die Gelegenheit besteht in drei von vier Rueckgaben. **Ein A/B an
diesem Netz ist also nicht von vornherein sinnlos, und der Streu-Korpus ist nicht die einzige
Tuer.**

**Zwei Einschraenkungen gehoeren zum Befund:**

1. **Sensitivitaet ist nicht Kompetenz.** Gemessen ist, dass der Value-Kopf auf eine geaenderte
   Typfolge REAGIERT -- nicht, dass die Reaktion mit echter Staerke korreliert. Ein Netz kann
   auf einen Eingabewert ausschlagen, ohne ihn richtig zu deuten. Genau diese Luecke hat der
   A/B aus par.9 gemessen (kein Effekt), und R1 hebt sie nicht auf.
2. **Die Sonde permutiert die TYPFOLGE, nicht die Plattenidentitaet.** Der Encoder sieht vom
   eigenen Block nur sie (`features.rs:231-236`); was zwei GLEICHTYPIGE Platten unterscheidet,
   misst R1 per Bauart nicht -- dort ist die Spannweite 0 und Modus 1 entscheidet per
   Gleichstand nach Ziehreihenfolge (par.8a Punkt 1). Die Gruppe "gleiche Typfolge" bleibt
   deshalb leer (n = 0); das ist kein Messausfall, sondern die Bauform. Der Selbsttest wurde
   entsprechend umgestellt: er prueft jetzt den Determinismus derselben Eingabe, nachdem die
   erste Fassung eine Bedingung verglich, die per Konstruktion nie eintreten kann.

**Was das fuer die Reihenfolge in par.12.1 heisst:** der Zwischenschritt "Streu-Korpus v30, dann
R1 am v30-Netz" ist nicht mehr die Voraussetzung fuer ein A/B, sondern eine eigene Frage (lernt
das Netz die Groesse BESSER zu deuten?). Ob ein A/B jetzt lohnt, haengt an der Haeufigkeit auf
der ANDEREN Seite: par.10 hat nur **0,19 Abweichungen je Partie** gemessen -- Modus 1 waehlt
also selten anders, obwohl er in 73,7 Prozent der Faelle etwas zu waehlen haette. Diese Luecke
ist der naechste Messpunkt, nicht die Sensitivitaet.

**R2 Encoder: geordnete eigene Designs (additiv, Merkmal P.16).** Zusaetzlich zu den sortierten
Designs die Design-Nummer der obersten k = 4 Positionen des eigenen Blocks (dieselben vier
Positionen wie die Typfolge), als 4 Werte `tile_id / 17` oder als 4 x 18 Bits; nur eigener Block
(regelkonform, der Rueckleger kennt sie), fremde Bloecke bleiben `Null`. Record-Feld
`dome_pool_view.blocks[].designs_ordered` additiv neben `designs`; **muss VOR der v30-Erzeugung im
Serializer stehen** (`feedback_record_field_must_precede_generation`, dieselbe Falle wie P.12).
INPUT_SIZE 794 -> 798 (Variante 4 Werte), Fenster- UND Val-Cache-Schluessel
(`feedback_feature_knob_belongs_in_both_cache_keys`), Paritaets-Fixture bewusst neu, Drift gruen
(die Heuristik liest den Vektor nicht). Nur sinnvoll, wenn R1 zeigt, dass die Spannweite bei
gleicher Typfolge exakt 0 ist UND bei verschiedener nicht -- dann ist Grenze 3 der Deckel.

**R3 Entscheidungsknoten im Baum (Spiegel von `moon_stack_order` par.12 Weg A).** Zwischen
`ChooseDrawStackSlot` und `ChooseDomeRotation` eine anhaengige Wahl "welche Restplatte kommt
zuerst wieder" (`return_order[0]`, `self_play.rs:606-621`): `PendingDomeChoice::FromDrawStack`
traegt `return_order` bereits (`moves.rs:99`), die Stufe liesse sich dort einhaengen. IDs nach
Zieh-Position (bis zu 3, Deckel wie `RETURN_ORDER_MAX_PERMUTED`), `NUM_ACTIONS` +3. Preis wie beim
Mondstapel: jeder Checkpoint verwaist (`feedback_num_actions_change_breaks_old_checkpoints`), der
Korpus muss die Knoten vor dem Training tragen, fruehestens v31 nutzbar -- **ausserhalb des
v30-Rahmens** (`project_v30_release_close`). Wenn, dann GEBUENDELT mit dem Mondknoten (5 + 3 IDs,
406 -> 414, EIN Kontraktwechsel), nach Nutzer-Entscheid ueber den Rahmen.

**R4 Nachsuche statt Blattwert (Modus 3, kein Training).** `choose_return_order` bewertet jeden
Kandidaten mit einem kleinen `build_net_tree` ueber den Folgezustand statt mit `net_leaf_eval`,
exakt das Muster von `moon_order_post_search` (`net_mcts.rs:5773-5832`: eigener Seed-Strom,
Budget obendrauf, Minimum aus Gegnersicht). Kosten je Entscheid wie dort (256 Sims je Variante);
bei 0,19 Abweichungen je Partie (par.11b) und 11,07 Gelegenheiten (par.11c) ist die Partie-Wanduhr
kaum betroffen (ANNAHME, Kostentor Pflicht). **Aber:** R4 verbessert den Entscheider, nicht das
Netz -- gegen das Henne-Ei aus par.10 hilft es nichts. Erst nach R1 am v30-Netz, und nur wenn die
Spannweite dort messbar ist.



### 12.5 GELEGENHEITEN IN DER ARENA GEZAEHLT (2026-09-15): der Nullbefund aus par.9 ist Arithmetik, kein Henne-Ei

Anschluss an 12.4 ("diese Luecke ist der naechste Messpunkt"). Gezaehlt aus den Logs der
beiden A/B-Artefakte `return_order_ab_mode1_vs_mode0_s20261071/_s20261072.json` (300 Partien,
je Partie eine Modus-1- und eine Modus-0-Seite; Rueckgabe-Zeile `Kuppelplatte(n) zurueck` dem
Spieler der letzten `Kachel vom Stapel gezogen`-Zeile zugeordnet; Abweichungen = Zeilen
`[return_order]`, die nur Modus 1 und nur bei Abweichung schreibt, `self_play.rs:1197-1210`):

| Groesse (n = 300 Partien)                       | Modus-1-Seite             | Modus-0-Seite |
| ----------------------------------------------- | ------------------------- | ------------- |
| Rueckgaben mit mindestens 2 Restplatten         | 187 = **0,62 je Partie**  | 196 = 0,65    |
| Rueckgaben mit mindestens 3 Restplatten         | 178 = 0,59                | 188 = 0,63    |
| Abweichungen von der Ziehreihenfolge            | **79 = 0,26 je Partie**   | --            |
| **Abweichungsrate bei Gelegenheit (>= 2 Rest)** | **79 / 187 = 42 Prozent** | --            |

**Drei Folgerungen:**

1. **Die 11,07 Gelegenheiten je Partie aus par.11c gelten fuer den ERZEUGUNGS-Korpus**
   (`MOSAIC_STACK_DRAW_RESEARCH=1`, 100 Sims), nicht fuer die Arena: dort zieht das Netz bei
   400 Sims ohne Forschungs-Knopf rund **0,6-mal je Partie und Seite** mit Rest >= 2. Die
   Dosis-Rechnung in par.11c (p = 0,015 fuer "15 Prozent der Partien") bleibt richtig, weil sie
   fuer die Erzeugung gemacht ist -- aber wer sie auf Arena-Partien anwendet, liegt um den
   Faktor 18 daneben.
2. **Modus 1 waehlt keineswegs selten anders:** in 42 Prozent seiner Gelegenheiten weicht er ab.
   Die 0,19 bzw. 0,26 Abweichungen je Partie sind Seltenheit der GELEGENHEIT, nicht Traegheit
   des Entscheiders. Damit ist auch die zweite Haelfte der par.11b-Deutung ("konnte gar nichts
   bewegen") praezisiert: er bewegt, aber selten.
3. **Der Nullbefund aus par.9 folgt aus Groessenordnung (Herleitung):** 0,26 Abweichungen je
   Partie mal Median-Spannweite 0,0188 (12.4) ergibt rund **0,005 Siegwahrscheinlichkeit je
   Partie** als Obergrenze der erwarteten Wirkung -- selbst wenn jede Abweichung die volle
   Spannweite einloest. Ein Vorzeichentest auf 300 Partien loest das nicht auf; dafuer braeuchte
   es zehntausende Partien. Kein Henne-Ei noetig, um par.9 zu erklaeren; das Henne-Ei aus
   par.10 bleibt trotzdem als Frage, ob das Netz die Groesse RICHTIG deutet (12.4 Punkt 1).

**Folge fuer 12.2:** Schritt 3 ("A/B Modus 1 gegen 0 am v30-Champion") kann bei dieser
Haeufigkeit auch am v30-Netz nichts aufloesen -- ausser der Streu-Korpus aendert die
Zieh-Haeufigkeit selbst (was er nicht soll, Dosis 0,015). **Das A/B ist damit als
Entscheidungsinstrument fuer diesen Knopf ungeeignet**; was bleibt, sind Diagnostiken (R1 am
v30-Netz, Wiederkehr-Rate aus par.5 Punkt 2) und der Vollstaendigkeits-Grund H1. Ob der Knopf
als Default in die Erzeugung geht, ist damit ein Korrektheits-Entscheid, kein Messentscheid --
Nutzer.

**R2 in diesem Licht:** die Typfolge traegt ein Signal (12.4), aber ein kleines an einer
seltenen Stelle. R2 (geordnete eigene Designs) verfeinert die Sicht dort, wo sie heute 0 ist
(26,3 Prozent der Bloecke mit >= 3 Platten sind typgleich, 12.4), an derselben seltenen Stelle.
Empfehlung: bauen, weil billig (+4 Werte, additiv) und weil es nach v30 keine Erzeugung mehr
gibt, die das Feld tragen koennte -- aber ohne Erwartung eines Arena-Effekts.

### 12.6 ENTSCHIEDEN (Nutzer 2026-09-15, "mit r2 und modus 1 ein"): R2 bauen, Modus 1 in der v30-Erzeugung an

Beide Entscheide fielen nach 12.5, das den par.9-Nullbefund als Arithmetik erklaert hat. Der
Modus-1-Entscheid ersetzt das "bleibt aus" vom selben Vormittag; Grund ist Korrektheit, nicht
Messung: die Rueckgabe-Reihenfolge ist ein legaler Zug (par.1), und der Generator soll ihn
waehlen, statt ihn der Ziehreihenfolge zu ueberlassen.

**R2 -- geordnete eigene Designs (Merkmal P.16), Bauvorgaben (VOR dem Bau registriert):**

1. **Record-Feld** `dome_pool_view.blocks[].designs_ordered`: die `tile_id`s des EIGENEN Blocks in
   Stapelreihenfolge (Index 0 = kommt zuerst wieder, wie `types`), fremde Bloecke `Null`;
   additiv neben dem sortierten `designs` (`serialize.rs:111-117`). **Muss im installierten Wheel
   stehen, BEVOR die v30-Erzeugung startet** (`feedback_record_field_must_precede_generation`;
   P.12 hat genau das gekostet).
2. **Encoder, beide Pfade (Rust `features.rs`, Python-Zwilling):** vier Werte, Design-Nummer der
   Positionen 0..3 des obersten eigenen Blocks als `tile_id / 17`, `0` wenn die Position fehlt
   oder das Feld nicht da ist (Alt-Records lesen sich als "Merkmal aus"). INPUT_SIZE 794 -> 798.
   Dieselben vier Positionen wie die Typfolge (Abschnitt 15, Indizes 4..7), damit beide Sichten
   dieselbe Tiefe haben.
3. **Schluessel und Tore:** `config.INPUT_SIZE` im selben Zug wie die Wheel-Installation
   (Unfall 2026-09-11); Merkmal in Fenster- UND Val-Cache-Schluessel
   (`feedback_feature_knob_belongs_in_both_cache_keys`); Netz-Paritaets-Fixture bewusst neu mit
   Begruendung; Anker-Drift und Konservierung gruen (die Heuristik liest den Vektor nicht);
   Sichtgleichheitstest: fremde Bloecke bleiben `Null` (Netz-sieht-MEHR ausgeschlossen);
   `tools/check_conventions.py`. Wheel-Bau nur bei freier Maschine.
4. **Wirkung:** erst im v30-Training (das Feld muss im Korpus liegen). Verdikt-Groesse: par.6d
   Punkt 1 der Fenster-Prereg (leben die vier Spalten?) und R1 am v30-Netz, getrennt nach
   gleicher und verschiedener Typfolge -- bei gleicher Typfolge muss die Spannweite jetzt
   ungleich 0 werden koennen. Kein Arena-Anspruch (12.5).
5. **Rahmen:** zweite Ausnahme vom Grundsatz "v30 nur Rezept-Knoepfe" neben P.12
   (`project_v30_release_close`), vom Nutzer entschieden. Fahrplan 29c.

**Modus 1 in der v30-Erzeugung AN:**

- Spec-Feld `return_order_mode: 1` in der v30-Erzeugungs-Spec (Nachfolger von
  `models/start_by_search_on.spec.json`); die Erzeugungs-Spec ist ohnehin eine neue gemessene
  Identitaet (`feedback_measured_identity_gets_own_bxx`).
- **Koexistenz mit dem Streu-Knopf ist gebaut:** die Streuung greift NACH dem Entscheider und
  ueberschreibt jeden Modus (`self_play.rs:1176-1191`); die gestreuten Faelle (p = 0,015)
  bleiben also Zufall, alle anderen tragen die bewertete Wahl. Beide Marker im Record
  (`return_order_randomized`, Diagnosezeile `[return_order]`), Sonden koennen trennen.
- **Kosten sind ungemessen** (par.9 "Was NICHT gemessen ist"): je Kandidat ein
  `eval_pair`-Batch (par.8a Punkt 2), bis zu 6 Kandidaten, rund 0,6 Gelegenheiten je Partie und
  Seite in der Arena (12.5) -- in der Erzeugung mit Forschungs-Knopf deutlich mehr (par.11c:
  11,07 Gelegenheiten mit Rest >= 3 je Partie). **Kostentor beim Start der Erzeugung:** `s_je_partie`
  der ersten Chunks gegen die v29-Erzeugung (10,8 h hochgerechnet, 12,8 h gemessen mit
  Nebenlast); mehr als 10 Prozent Aufschlag ist dem Nutzer vorzulegen, kein Abbruch von selbst.
- Wirkung auf den Korpus: das Netz lernt aus Records, in denen die Reihenfolge eine BEWERTETE
  Wahl war; ob es daraus mehr lernt als aus reiner Streuung, misst R1 am v30-Netz. Ein
  Nullbefund dort ist kein Grund, den Modus zurueckzunehmen (Korrektheitsentscheid).

### 12.7 ENTSCHIEDEN (Nutzer 2026-09-17): R3 wird gebaut, gebuendelt mit Weg A des Mondstapels

Mit dem Entscheid in `PREREG_moon_stack_order.md` par.12.6 (Weg A, Korrektheitsargument des Nutzers: im realen
Spiel waehlt der Spieler die Reihenfolge, um den Gegner zu stoeren und die Stapel zu planen) faellt die Bedingung
aus 12.2 Punkt 4 ("R3 nur mit Weg A und nur nach Rahmen-Entscheid"): **R3 wird gebaut**, gebuendelt zu EINEM
Kontraktwechsel `NUM_ACTIONS` 406 -> 414 (5 Mond-IDs + 3 Rueckgabe-IDs), additiver Policy-Kopf, Bauvorgaben
1-5 aus moon_stack_order 12.6 gelten wortgleich. R2 (P.16 `designs_ordered`) und Modus 1 aus 12.6 bleiben
bestehen: R2 ist die Sicht (das Netz sieht die Reihenfolge), R3 der Zug (das Netz waehlt sie im Baum); Modus 1
bleibt der Rueckfall fuer 406er-Netze und fuer den Heuristik-Pfad. Alles VOR der v30-Erzeugung im Wheel;
Wiedervorlage am ersten Record wie bei P.12/P.16. Fahrplan 36i.


### 12.8 Baustand R3 und R2 (2026-09-18, Agent)

Code vollstaendig, **Kompilat und Wheel stehen aus** (exklusive Arena-Messungen liefen; der
Auftrag war "Code ohne Kompilat"). Nichts gemessen, nichts committet. Gebuendelt mit Weg A des
Mondstapels zu EINEM Kontraktwechsel; die gemeinsamen Teile (Tor, Policy-Breite,
Vertragshash, additive Polsterung, Anker-Belege) stehen in
`PREREG_moon_stack_order.md` 12.10 und werden hier nicht wiederholt.

#### R3 -- Rueckgabe-Reihenfolge als Entscheidungsknoten

**Bauform.** `moves.rs`: `PendingReturnOrder { chosen_id, slot_row, slot_col,
rest_in_draw_order }` plus `Action::ChooseReturnFirst(usize)`. In
`game.rs::apply_drafting`, Zweig `Action::ChooseDrawStackSlot`: greift das Tor und gibt es
mindestens zwei Restplatten, wird statt `pending_dome_choice` das neue
`pending_return_order` gesetzt -- der Knoten sitzt damit GENAU zwischen
`ChooseDrawStackSlot` und `ChooseDomeRotation`, wie in 12.1 vorgegeben. Der Teilzug waehlt
`return_order[0]` per ZIEH-POSITION; der Rest bleibt in Ziehreihenfolge. Danach wird
`pending_dome_choice::FromDrawStack` mit der fertigen Reihenfolge gesetzt, ohne
`switch_player()`; die Rotation laeuft unveraendert weiter.

**Kandidaten und IDs.** `game::return_first_candidates` liefert
`0..min(rest, RETURN_ORDER_MAX_PERMUTED)` -- derselbe Deckel 3, den Modus 1 permutiert
(`self_play.rs`, jetzt `pub(crate)`), und damit dieselbe Menge, die der Rueckfall beschreibt.
Aktions-IDs 411..413 (`features::action_to_id`, Typ `choose_return_first`, Feld `draw_index`,
gedeckelt statt ueberlaufend), Spiegel in `self_play::action_to_id_direct` und
`neural_net.py`.

**Das eingereichte `return_order` wird bei aktivem Knoten VERWORFEN**, und der Bezugsrahmen
der IDs ist nicht es, sondern die Ziehreihenfolge: `game::rest_in_draw_order` bildet sie aus
`pending_stack_draw` und entfernt `chosen_id` genau einmal (Multimengen-Disziplin wie
`validate_draw_from_stack`).

**Die ehrliche Grenze dieses Baus, und sie ist der wichtigste Satz hier.** Der Stapelzug wird
im Betrieb NICHT von der Schleife entschieden, sondern von
`self_play::resolve_and_apply_stack_draw_with`: die Suche waehlt an der Wurzel nur das
`DrawStackPeek`, der Aufloeser macht danach alles allein (wie oft ziehen, welche Platte,
Slot, Rotation, Reihenfolge). Folge:

* Der Aufloeser SCHLIESST den Knoten selbst, mit genau der Wahl des Entscheiders
  (`choose_return_order`, also `return_order_mode`): Position von `return_order[0]` in der
  Ziehreihenfolge, bei Modus 0 also 0, bei Modus 1 immer ausdrueckbar (er permutiert genau den
  gedeckelten Kopf). Endzustand identisch zu heute, aber ueber die Knoten-Transition.
* **Damit traegt der Record fuer diesen Halbzug KEIN `policy_target` am Rueckgabeknoten** --
  anders als beim Mondknoten, den die Schleife als eigenen Entscheid sieht. R3 wirkt zunaechst
  nur IM SUCHBAUM (dort taucht der Knoten in jeder simulierten Fortsetzung nach einem Peek
  auf und wird vom Netz bewertet).
* Nutzer-/Koordinator-Entscheid, offen: soll die SCHLEIFE den Stapelzug uebernehmen (dann
  entscheidet die Suche auch Slot und Rotation, was heute `best_eval_for_tile` tut -- eine
  Agenten-Aenderung, die niemand vorregistriert hat), oder bleibt R3 ein reiner Baum-Knoten?
  Solange Letzteres gilt, ist die Wiedervorlage "erster v30-Record enthaelt
  `choose_return_first`" NICHT erfuellbar; `choose_moon_top` steht darin.
* Randfall Modus 2 (Handregel, Diagnoseknopf): koennte eine Platte jenseits des Deckels nach
  vorne ziehen. Dann nimmt der Aufloeser Position 0. Kein Zustandsschaden, aber Modus 2 ist
  mit Knoten nicht mehr deckungsgleich mit sich selbst ohne Knoten. Im Code vermerkt.

**Anker.** Der Heuristik-Pfad loest den Stapelzug gar nicht hier auf
(`apply_via_chosen_action: false`) und setzt das Tor nie -- Belege in
`moon_stack_order` 12.10.

**Tests (geschrieben, nicht gelaufen), `game.rs`:**
`return_order_node_offers_capped_draw_positions_and_orders_the_head` (Kandidaten gedeckelt
auf 3 bei 3 Restplatten, kein Spielerwechsel, `return_order[0]` ist die gewaehlte Platte,
Rest in Ziehreihenfolge, Rotation VOR dem Knoten wird abgelehnt, ungueltige Position laesst
den Knoten stehen), `return_order_node_is_off_without_the_gate` (ohne Tor direkt zur
Rotation, eingereichtes `return_order` uebernommen),
`action_id_round_trip_covers_the_eight_new_ids` (411..413).

#### R2 / P.16 -- geordnete eigene Designs (Bauvorgaben 1-5 aus 12.6)

1. **Record-Feld** `dome_pool_view.blocks[].designs_ordered` (`serialize.rs::dome_pool_view`,
   direkt neben `designs`): die `tile_id`s des EIGENEN Blocks in Stapelreihenfolge
   (Index 0 = kommt zuerst wieder, dieselbe Richtung wie `types`), fremde Bloecke `Null`.
   Additiv, `designs` bleibt unveraendert sortiert.
2. **Encoder, beide Pfade** (`features.rs`, neuer Abschnitt 18): vier Werte ANS ENDE,
   Design-Nummer der Positionen 0..3 des obersten eigenen Blocks als `tile_id / 17`, `0` wenn
   die Position fehlt oder das Feld nicht da ist. `INPUT_SIZE` 884 -> 888. Dieselben vier
   Positionen wie die Typfolge aus Abschnitt 15 (`DOME_POOL_TOP_TYPES`). JSON-Pfad aus dem
   Record-Feld, Direktpfad aus dem `GameState` mit derselben Sichtregel; der Python-Zwilling
   (`engine/py/neural_net.py`) hat denselben Block plus die Scharfschaltung
   `if INPUT_SIZE < LEN_WITH_ORDERED_DESIGNS: return` (Muster von Abschnitt 16/17, Unfall
   2026-09-11).
   **Eine Mehrdeutigkeit, so registriert wie vorgegeben:** Design 0 und "Position fehlt" sind
   beide `0,0` (die Prereg schreibt `tile_id / 17` und `0` fuer fehlend). Aufloesbar ist es
   ueber den Nachbarwert aus Abschnitt 15, dessen Typwert an derselben Position genau dann `0`
   ist, wenn die Position fehlt. Im Code vermerkt.
3. **Schluessel und Tore.** `config.INPUT_SIZE` 884 -> 888 setzt der Koordinator im
   Kompilat-Schritt (diese Sitzung hat `config.py` nicht angefasst, Auftrag); Merkmal in
   Fenster- UND Val-Cache-Schluessel (`feedback_feature_knob_belongs_in_both_cache_keys`) --
   das faellt automatisch, weil beide Schluessel `INPUT_SIZE` fuehren, ist aber vor dem ersten
   Cache-Bau zu PRUEFEN und nicht anzunehmen. Netz-Paritaets-Fixture bewusst neu (neues
   Record-Feld, dieselbe Lage wie Abschnitt 16); Anker-Drift und -Konservierung gruen erwartet
   (die Heuristik liest den Vektor nicht).
   **Sichtgleichheitstest gebaut:** `features.rs::ordered_designs_only_read_the_own_block_in_both_paths`
   prueft ueber >= 300 Zustaende gegen eine DRITTE Rechnung (direkt aus `dome_tile_pool`),
   dass beide Encoder-Pfade Wert fuer Wert dasselbe liefern, dass `designs_ordered` genau am
   eigenen Block steht und fremde `null` bleiben (Netz-sieht-MEHR ausgeschlossen), und dass es
   dieselbe Multimenge wie `designs` ist. Dazu
   `ordered_designs_are_appended_after_884` (Additivitaet: Abschnitt 17 unverschoben, vier
   Werte in [0,1], Laenge genau `ORDERED_DESIGN_VALUES`).
   `tools/check_conventions.py`: gruen.
4. **Wirkung** erst im v31-Training (das Feld muss im Korpus liegen); Verdikt-Groessen
   unveraendert (par.6d Punkt 1 der Fenster-Prereg, R1 am v30-Netz getrennt nach gleicher und
   verschiedener Typfolge). Kein Arena-Anspruch (12.5).
5. **Rahmen** unveraendert (zweite Ausnahme vom Grundsatz "v30 nur Rezept-Knoepfe",
   Nutzer-Entscheid).

**Eintrag in `docs/architecture_reference.md`** gemacht, Abschnitt "Wo der Code Information
ABSICHTLICH vernichtet": die SORTIERUNG in `designs` war eine Sicht-ANNAHME ("der Spieler
haelt die Reihenfolge nicht auseinander"), und sie war falsch -- er hat sie selbst gewaehlt,
und `determinize_dome_pool` laesst sie ihm auch in der Suche. `designs_ordered` hebt sie
additiv auf, nur fuer den eigenen Block. Dazu die Zeile zu den beiden neuen Knoten.

**Kompilat-Erwartung.** ROT (und vom Koordinator zu setzen): `config.py`
(`NUM_ACTIONS` 414, `INPUT_SIZE` 888), Feature-Golden-Fixture, Netz-Paritaets-Fixture.
GRUEN bleiben muss: Vertragshash (`lib.rs`, Literal `6ef829e564c58bd5`, nachgerechnet),
Anker-Drift/-Konservierung, alle `direct_matches_json_path_*`, alle Rundtrip-Tests in
`serialize.rs` (die drei neuen exakten Felder `pending_moon_order_exact`,
`pending_return_order_exact`, `extended_action_nodes_exact` werden TOLERANT gelesen, damit
bestehende Referee-/Seeding-Nutzlasten weiter laden).

### 12.9 Baustand: die Schleife uebernimmt den Stapelzug (2026-09-18, Agent)

**Nutzer-Entscheid 2026-09-18 ("dann a", STATUS Abschnitt 6 Punkt 22):** Slot, Rueckgabe und
Rotation werden bei aktivem 414er-Tor eigene Entscheide der SUCHE mit Besuchsverteilung als
Lernziel -- der offene Punkt aus 12.8 ("R3 traegt im Record kein Policy-Ziel") ist damit
beantwortet. Code fertig, **Kompilat und Wheel stehen aus** (exklusive Arena-Kette lief), nichts
gemessen, nichts committet. Gebuendelt mit Weg A, R3 und R2 zu EINEM Kontraktwechsel.

**Der Fund, der den Bau klein gemacht hat.** Der Mechanismus existiert seit v23 als Knopf:
`MOSAIC_STACK_DRAW_RESEARCH=1` schaltet die Sammelaufloesung ab, es wird nur der Peek angewandt,
und die Schleife entscheidet danach neu (`self_play.rs:1328` Getter, Wirkort das Match in
`apply_chosen_action_with`). Der Knopf steht in der v29- UND der v30-Erzeugung
(`tools/night_v29_generate.sh:37`, `tools/night_v30_generate.sh:32`). Drei Folgerungen, alle am
Code geprueft:

1. `ChooseDrawStackSlot` und `ChooseDomeRotation` sind dort SCHON heute eigene Halbzuege mit
   eigener Suche und eigenem Record -- die Schleife schreibt je Durchlauf genau einen Record mit
   `policy` und `valid_actions` (`self_play.rs:4267`ff). Der Stapelzug wechselt den Spieler erst
   in `ChooseDomeRotation` (`game.rs:1061`, `switch_player` am Ende des Arms); `DrawStackPeek`,
   `ChooseDrawStackSlot` (`game.rs:1033`) und `ChooseReturnFirst` (`game.rs:987`) beenden den Zug
   nicht.
2. Der Rueckgabeknoten braucht deshalb KEINEN neuen Transportweg: `drafting_actions` bietet ihn
   an (`game.rs:767`), `apply_drafting` hat den Rangfolge-Riegel, und die Schleife sieht ihn als
   eigenen Entscheid.
3. Was fehlte, war nur die KOPPLUNG an das Tor statt an eine Umgebungsvariable -- ohne sie bliebe
   eine 414er-Seite in der Arena und im Gating (Knopf aus) beim Aufloeser, waehrend sie in der
   Erzeugung zerlegt spielt.

**Die Aenderung, eine Zeile plus Tor.** Neue Torfunktion `game::stack_move_decided_by_loop`
(`game.rs:709`, liest `extended_action_nodes[current_player]`), gelesen im Match von
`apply_chosen_action_with` (`self_play.rs:1378-1392`): der Aufloeser laeuft nur noch, wenn
`!stack_draw_research() && !stack_move_decided_by_loop(...)`. Sonst wird der Peek einzeln
angewandt und die Schleife entscheidet weiter.

**Zustandsfluss der drei Teilzuege bei aktivem Tor** (je Schritt eine Suche, ein Record, kein
Spielerwechsel):

1. Der Wurzelentscheid der Schleife waehlt `DrawStackPeek` -> `execute_draw_stack_peek` legt eine
   Platte in `pending_stack_draw`; weitere Peeks sind eigene Entscheide (der Bestand entschied
   sie im Aufloeser per Erwartungswert-Regel).
2. `ChooseDrawStackSlot(m)`: `rest_in_draw_order` bildet die Restplatten; ab zwei oeffnet
   `pending_return_order` (`game.rs:1033-1045`), das eingereichte `m.return_order` wird
   verworfen. Bei einer oder keiner Restplatte direkt `pending_dome_choice` -- Bestandspfad.
3. `ChooseReturnFirst(pos)`: Position in der ZIEHREIHENFOLGE, Kandidaten `0..min(rest, 3)`
   (`return_first_candidates`), IDs 411..413. Setzt `pending_dome_choice::FromDrawStack` mit
   `return_order[0]` = gewaehlte Platte, Rest in Ziehreihenfolge.
4. `ChooseDomeRotation(rot)`: vier Kandidaten (`draw_stack_slot_rotation_candidates` filtert
   heute nichts weg), `execute_draw_from_stack`, dann `switch_player`.

**Bit-Identitaets-Belege (Pruefstellen).**

* Tor aus -> die Match-Bedingung ist wortgleich der Bestand, derselbe Aufloeser-Aufruf mit
  denselben Argumenten (`self_play.rs:1386-1392`). Gesetzt wird das Tor an GENAU EINER Stelle,
  `unified_game_loop` (`self_play.rs:3813-3815`), je Seite aus `tiling_net` plus Policy-Breite.
* Heuristik-Seiten erreichen den Aufloeser in der Schleife ohnehin nicht
  (`apply_via_chosen_action: false`, Belege in `moon_stack_order` 12.10) und setzen das Tor nie.
* `referee.rs:868`, `referee.rs:970` und `py.rs:1067` (GUI) rufen `apply_chosen_action_with`
  weiter mit einem Zustand, dessen Tor nie gesetzt wird -- fuer sie bleibt der Aufloeser der
  Wirkort, byte-identisch. `json_to_state` setzt das Feld auf `false` (`serialize.rs:1272`),
  Replay und Seeding ebenfalls.
* Der Abweichungs-Sonde (`deviation_best_action`, `self_play.rs:3010`) wird das Tor jetzt
  mitgeklont: sie bewertet fuer eine 414er-Seite denselben Folgezustand, der auch entsteht
  (vorher haette sie unter `MOSAIC_STACK_DRAW_RESEARCH=1` den ganzen Zug aufgeloest, waehrend der
  Spielpfad nur den Peek anwendet). Das ist eine KORREKTUR dieses Bestands-Missverhaeltnisses und
  wirkt nur bei aktivem Tor.

**Was mit dem Aufloeser wegfaellt, und das ist der wichtigste Nebenbefund.** `return_order_mode`
(Modus 1/2) und die Erzeugungs-Streuung `MOSAIC_RETURN_ORDER_RANDOM_P` sitzen AUSSCHLIESSLICH im
Aufloeser (`choose_return_order` hat genau einen Aufrufer, `self_play.rs:1187`;
`apply_return_order_random` genau einen, `self_play.rs:1196`). Fuer eine Seite mit Tor wirken sie
nicht mehr -- an ihre Stelle tritt der Knoten. **Unter `MOSAIC_STACK_DRAW_RESEARCH=1` gilt das
schon heute fuer JEDE Seite**, also auch fuer die v29-Erzeugung und fuer die v30-Kette, deren
Spec `return_order_mode: 1` fuehrt (`models/v30_generation.spec.json`): dieser Spec-Wert war dort
ohne Wirkung und stand nur im Manifest-Export. Der Streu-Knopf steht in KEINEM Skript und in
keiner Spec (geprueft mit einem Grep ueber `tools/*.sh` und `models/*.json`), verliert also keinen
lebenden Verbraucher. Wer die Abdeckungs-Absicht aus par.11 im v30-Korpus haben will, bekommt sie
jetzt ueber den Knoten (Temperatur der Besuchsverteilung, `action_temp_for`), nicht ueber den
Knopf. Die Knopf-Registratur ist an allen drei Stellen nachgezogen, `docs/knobs.md` neu erzeugt
(Quelle: Parse von `knob_registry.rs`, kein Wheel).

**Budget je Knoten: das volle `base_sims`, kein neuer Knopf.** Begruendung nach Praezedenz, nicht
nach Geschmack: (a) im Netzpfad ist das Budget je Entscheid ohnehin von der Aktionszahl
ENTKOPPELT -- `net_effective_sims` gibt `base_sims` unveraendert zurueck
(`net_mcts.rs:4122/4146`, `DECOUPLE_NET_SIMS_FROM_ACTIONS = true`), zwei Aktionen kosten dasselbe
wie 195; (b) der Mondknoten aus Weg A laeuft aus demselben Grund mit dem vollen Budget
(`moon_stack_order` 12.10); (c) `ChooseDrawStackSlot` und `ChooseDomeRotation` tun es in der
Erzeugung seit v29. Die 256 Sims von `moon_order_post_search` (`net_mcts.rs`, Stufe 3) sind KEINE
Praezedenz fuer den Knoten: das ist eine Nachsuche nach der Zugwahl, und Weg A schaltet sie ab.
Ein kleineres Budget bekaeme man nur mit einem neuen Knopf -- ausdruecklich nicht gewollt.

**Erwartete Zusatzkosten.** Je Stapelzug zaehlt die Schleife eine Suche fuer jeden weiteren Peek,
eine fuer den Slot, eine fuer den Rueckgabeknoten (nur bei >= 2 Restplatten) und eine fuer die
Rotation (vier Kandidaten).

* **Gegen die v30-Kette (Knopf schon an): genau eine zusaetzliche Suche je Rueckgabe mit >= 2
  Restplatten.** Alles andere lief dort bereits.
* **Gegen einen Lauf mit Knopf AUS** (Arena, Gating, Kostentor) kommen Peeks, Slot und Rotation
  hinzu. Gemessen ist nur die Haeufigkeit der Rueckgabe-Gelegenheit: **0,62 bzw. 0,65 Rueckgaben
  mit mindestens zwei Restplatten je Partie und Seite** (n = 300 Partien, Grundmenge
  Arena-Partien @400 Sims ohne Forschungsknopf, Einheit Rueckgaben je Partie und Seite --
  Tabelle in 12.5). Mit zwei bis vier Zusatzsuchen je Stapelzug sind das **rund 800 bis 1.600
  zusaetzliche Sims je Partie und Seite gegen rund 32.000 bei @400, also grob +2,5 bis +5
  Prozent** -- HERLEITUNG aus den beiden genannten Zahlen, nicht gemessen. Das Kostentor aus
  Punkt 23 (Schwelle 25 Prozent) misst es.
* **Fuer die ERZEUGUNG ist die Haeufigkeit ungemessen**, und die naheliegende Zahl ist falsch:
  die "11,07 Gelegenheiten mit mindestens drei Restplatten je Partie" aus par.11c stammen aus
  `PREREG_moon_stack_order.md` par.9b (142.945 Dreierstapel auf 12.907 Partien, Zeile 549 dort) --
  Grundmenge sind MONDSTAPEL-Ereignisse, Einheit Dreierstapel je Partie, nicht Kuppelplatten.
  par.11c bezeichnet sie als "Restplatten"; das ist eine Grundmengen-Verwechslung. 12.5 Punkt 1
  hat die Luecke halb gesehen (Faktor 18 zur Arena), aber die Bezeichnung nicht korrigiert.
  Betroffen ist allein die Dosis-Rechnung des Streu-Knopfs (p = 0,0146), und die hat keinen
  lebenden Verbraucher (siehe oben). **Wiedervorlage:** die Zahl aus dem ersten v30-Self-Play
  zaehlen -- `choose_return_first`-Records je Partie; die Record-Pruefung aus Punkt 21 oeffnet die
  Datei ohnehin.

**Tests (geschrieben, NICHT gelaufen), alle in `self_play.rs`:** gemeinsame Fixture
`stack_draw_ready_game` (`self_play.rs:8017`).

* (a) `stack_move_stays_with_the_resolver_without_the_gate` (`:8037`) -- ohne Tor beendet EIN
  `apply_chosen_action` den ganzen Stapelzug, Rueckgabe ist die Stufe-1-Aktion, Platte liegt,
  `pending_return_order` bleibt leer, Spielerwechsel gefallen. Dieselben Zusicherungen wie
  `resolve_and_apply_stack_draw_produces_valid_placement` (`:7987`), das den Bestand
  festschreibt.
* (b) `stack_move_is_decided_by_the_loop_with_the_gate` (`:8063`) -- drei Peeks je einzeln
  angewandt, dann Slot, dann der Knoten (nur seine Kandidaten legal, genau zwei), dann Rotation;
  `current_player` bleibt bis zur Rotation 0, `return_order[0]` ist die gewaehlte Platte. Dass
  jeder dieser Teilzuege einen eigenen Record mit Policy-Ziel bekommt, folgt aus dem
  `recording`-Zweig (`self_play.rs:4267`ff) -- ein Record-Test dazu braucht ein 414er-ONNX, die
  Fixture `engine_test.onnx` traegt 406 (offener Punkt unten).
* (c) Aktions-IDs 411..413 rundreisefaehig: `game.rs::action_id_round_trip_covers_the_eight_new_ids`
  aus 12.8 deckt sie ab, dazu `action_to_id_direct_matches_json_path_across_random_games`. Nichts
  Neues gebaut.
* (d) `loop_ownership_ignores_return_order_mode_and_the_randomizer` (`:8131`) -- mit Tor holt
  weder `return_order_mode = 1` noch ein gesetzter Streu-Traeger den Aufloeser zurueck, und die
  Muenze der Streuung bleibt ungefallen. Das ist die Zusicherung "Arena-Loop verhaelt sich wie
  Self-Play-Loop": beide uebergeben genau diese Argumente (`self_play.rs:4190`ff).

Alle beruehrten `.rs`-Dateien sind mit `rustfmt --check` auf Kopien parse-geprueft (KEIN Kompilat,
also keine Typpruefung). `python -X utf8 tools/check_conventions.py`: gruen.

**Kompilat-Erwartung.** Unveraendert die aus 12.8 und `moon_stack_order` 12.10 -- diese Aenderung
fuegt nichts hinzu, was rot werden muesste: keine oeffentliche Signatur geaendert (nur eine neue
`pub fn` in `game.rs`), also auch keine Nachziehpflicht in `engine/examples/` oder
`engine/benches/` (geprueft mit einem Grep nach `apply_chosen_action` dort: keine Fundstelle).
Replayer und GUI bleiben unberuehrt; NEUE Logzeilen entstehen nicht, im Gegenteil fallen bei
aktivem Tor die `[return_order]`-Zeilen weg (sie kamen aus dem Aufloeser). GRUEN bleiben muss
zusaetzlich `resolve_and_apply_stack_draw_produces_valid_placement` -- der Bestand des Aufloesers.

**Offene Punkte.**

1. **Zeile-1-Kopf dieser Prereg ist nach diesem Absatz ueberholt** (er fuehrt den Entscheid noch
   als offene Frage). Der Auftrag dieser Sitzung war ausdruecklich "Zeile 1 nicht aendern";
   nachziehen und `python tools/generate_prereg_index.py` laufen lassen ist damit Sache des
   Koordinators.
2. **Record-Test mit Tor fehlt**, weil die Test-ONNX 406 Ausgaenge hat. Sobald das gepolsterte
   b10 (Punkt 23) liegt, ist er billig nachzuziehen -- und die Self-Play-Stichprobe der
   Abnahmekette prueft dasselbe am echten Korpus.
3. **Der R3-Rueckfall im Aufloeser ist ueber `apply_chosen_action_with` nicht mehr erreichbar**
   (Tor an -> Schleife, Tor aus -> Knoten oeffnet nie). Er bleibt fuer direkte Aufrufer stehen,
   mit Kommentar an der Stelle (`self_play.rs:1240`ff); Loeschen ist ein eigener Entscheid.
4. **Sackgassen-Fall `Pass`:** findet die Schleife mitten im Stapelzug keine legale Slot-Wahl und
   keinen weiteren Peek, bietet `drafting_actions` `Pass` an, was den Spieler mit gefuelltem
   `pending_stack_draw` wechseln liesse. Das ist KEIN neuer Fall -- er existiert unveraendert
   unter `MOSAIC_STACK_DRAW_RESEARCH=1`, also in der v29-Erzeugung; ungemessen, ob er je eintritt.
5. **Der Encoder sieht die Zwischenstufe nicht:** `features.rs` liest `pending_stack_draw`, aber
   weder `pending_dome_choice` noch `pending_return_order`. Eingabevektor am Slot-, Rueckgabe- und
   Rotationsknoten sind damit gleich; unterschieden werden die Stufen nur ueber die legale
   Aktionsmenge. Gilt seit Baustein B fuer Slot/Rotation genauso, ist also Bestand und kein
   Regress -- fuer das Policy-Ziel unschaedlich (es lebt auf `valid_actions`), fuer den
   Value-Kopf heisst es mehrere gleiche Eingaben je Stapelzug mit demselben Ausgang.

### 12.10 Kompilat (2026-09-18, 09:21-09:31)

Siehe `PREREG_moon_stack_order.md` 12.11: 702 Tests gruen nach bewusster Neuerzeugung beider Fixtures (die
Netz-Paritaets-Fixture bewegt sich durch das neue Record-Feld `designs_ordered`, Hash `d049d1329abf2343`), Wheel
09:30:43, config 888/414. Abnahme laeuft (`tools/night_v30_wheel_acceptance.sh`); die Record-Stichprobe darin
zaehlt die Rueckgabe-Knoten (IDs 411-413) und ihre `policy`-Eintraege -- das ist die Wiedervorlage aus 12.9.

### 12.11 Wiedervorlage P.16 und Rueckgabeknoten im v30-Korpus (2026-09-18): GRUEN

**Wiedervorlage am ersten Record der v30-Erzeugung GRUEN (2026-09-18, 14:54; `data/selfplay_v29-b11-policy_20260918_1450_g10.pkl`,
1.952 Records aus 10 Partien, gzip-gelesen, IDs ueber `neural_net.action_to_id`):** P.12 `designs` 577 Records,
P.16 `designs_ordered` 577 Records (nur wo ein eigener Block liegt), Mondknoten 406-410 in `valid_actions` 478 / in
`policy` 424, Rueckgabeknoten 411-413 11 / 11, Rotation 640 / 640, Slot 8.132. Der v30-Korpus traegt die neuen
Merkmale und Knoten mit Lernziel; nichts faellt nach v31.

### 12.12 BAUPLAN: die Streuung in den Knoten-Weg holen, fuer das v31-Self-Play (2026-09-18, 23:30)

**Nutzer-Auftrag 2026-09-18, 23:20:** *"dann schau dass wir es ins self play fuer v31 bekommen."* Vorlauf:
par.9 der `PREREG_v30_window.md` (die Streuung ist in der v30-Erzeugung unwirksam, weil sie im verdraengten
Aufloeser sitzt; Ersatz nur in der temperierten Klasse). **Nichts gebaut, nichts kompiliert** -- auf der
Maschine laufen Erzeugung und v30-Kette, ein `cargo`-Build zaehlt als Last (CLAUDE.md).

**Warum der naheliegende Weg NICHT funktioniert, und das ist der tragende Befund dieses Abschnitts.** Im
Aufloeser blieb `policy_target_valid` unberuehrt, weil dort nur ein Nebenaspekt der Aktion gestreut wurde. Im
Knoten-Weg IST die Rueckgabe die Aktion; ein gestreuter Entscheid braucht also eine Maske, sonst lernt der
Policy-Kopf Zufall. Die naheliegende Loesung waere `policy_target_valid = false` wie bei der gestreuten
Startkuppel -- **sie greift hier aber nicht**: `engine/py/corpus_dataset.py` Z.1635 maskiert nur
`if step.get("policy_target_valid") is False and not _IGNORE_PTV`, und die Erzeugungs- wie die Trainingskette
fahren `MOSAIC_IGNORE_POLICY_TARGET_VALID=1` (par.6 der v30-Fenster-Prereg). Das Flag waere also
wegignoriert, und zwar genau in den Laeufen, fuer die es gedacht ist.

**Das Muster, das stattdessen zu kopieren ist**, steht zwei Bildschirme darueber: die gestreute Startkuppel
haengt NICHT am Ignore-Knopf, sondern an einer eigenen Bedingung (`corpus_dataset.py` Z.1593-1595,
`start_by_search and policy_target_valid is not False`). Ein gestreuter Rueckgabe-Entscheid braucht dieselbe
Bauform: eine eigene Regel, die unabhaengig von `_IGNORE_PTV` greift.

**Bauplan in vier Schritten, in dieser Reihenfolge:**

1. **Rust, Streuung im Knoten-Weg.** Angriffspunkt ist die Schleife nach dem Entscheid (`self_play.rs`
   Z.3979 `decide`, Ersetzung wie Weg B/C an Z.4095) oder die Auswahl-Rangfolge in `net_drafting_policy`
   (Z.5754-5815). Die Abgrenzung ist billig, weil die Aktionsliste am Rueckgabeknoten sortenrein ist
   (`game.rs` Z.767-769). Zufallsstrom nach dem Bestandsmuster mit EIGENEM Distinguisher
   (`derive_search_seed(game_seed ^ <neu>, move_number)`, Vorbild Z.892/4177); Reichweite nur im
   aufzeichnenden Zweig, Vorbild `MOSAIC_START_SLOT_RANDOM_P` (Z.1890-1905).
2. **Rust, Markierung.** Das Record-Feld `return_order_randomized` EXISTIERT bereits (`self_play.rs` Z.1071
   Feldbau, Z.4297 Schreibstelle), wird aber heute nur vom Aufloeser gesetzt (Z.1052). Der Knoten-Weg muss
   die Zelle selbst setzen. **Kein neues Feld noetig.**
3. **Python, Maske.** `corpus_dataset.py`: `pol_w = 0.0`, wenn der Record `return_order_randomized` traegt --
   als EIGENE Bedingung neben Z.1635, NICHT unter `_IGNORE_PTV`. **Geprueft 2026-09-18: das Feld wird heute
   von keinem Python-Verbraucher gelesen** (Grep ueber `corpus_dataset.py`, `train.py`, `file_cache_key.py`
   ohne Treffer), es ist also ein rein additiver Eingriff.
4. **Cache-Schluessel.** Schritt 3 aendert den Datensatz bei gleichem Korpus -- die Regel MUSS in den
   Schluessel, sonst zieht der naechste Lauf still den alten Monolithen
   (`feedback_feature_knob_belongs_in_both_cache_keys`, Praezedenz b03: mit Kanaelen trainiert, ohne
   validiert). Betrifft Fenster- UND Val-Schluessel.

**Zeitliche Zwaenge, die den Bau binden:**

* **Der Knopf muss VOR der v31-Erzeugung im Wheel sein** (`feedback_record_field_must_precede_generation`);
  sonst faellt das Merkmal wieder eine Generation zurueck -- genau der Fehler, den P.12 schon einmal gekostet hat.
* **`corpus_dataset.py` darf nicht angefasst werden, solange Cache-Waechter oder Kette laufen**
  (`feedback_watcher_workers_reimport_config`, Vorfall 2026-09-11: 24 Bloecke unter falschem Schluessel).
  Schritt 3 wartet also bis nach der v30-Kette.
* **Engine-Aenderung heisst Anker-Invarianz** (`/mosaic-anchor-invariance`, 22,4 s + 16,6 s) und
  `cargo test --release --no-run` wegen `examples/` und `benches/`.

**KORREKTUR 2026-09-18, 23:50 (Nutzer: "diese fragen sind sicher nicht offen. das haben wir schon alles
durchgekaut").** Der Koordinator hatte Dosis, Reichweite und den Zweck als offen ausgegeben, ohne par.11b und
par.11c gelesen zu haben. Sie sind entschieden, und zwar hier:

* **Schwelle ab DREI Restplatten** (par.11b Punkt 1, gebaut als `RETURN_ORDER_MIN_REST = 3`).
* **Runden 1 bis 4 gleichgewichtet, Runde 5 aus** (par.11b, gebaut als `return_order_round_allowed`).
* **Keine Laengengewichtung, keine Bevorzugung frueher Runden** (par.11b, Nutzer: *"das liegt am netz es zu
  lernen was sinnvoller ist. wir zeigen es ihm nur."*).
* **Muenze je Gelegenheit, nicht je Partie** (par.11c: das Reservoir ist im Rueckgabe-Pfad strukturell nicht
  erreichbar, weil die Permutation sofort wirkt).
* **Zweck: ABDECKUNG des Zustandsraums**, nicht eine bessere Reihenfolge lehren (par.11c, Nutzer: *"ich will
  ja nur dass das netz sieht das kuppelplatten auch einfach so aus dem stapel gezogen werden koennen."*).
  Damit ist auch die zweite angebliche Frage beantwortet: die Streuung haengt nicht an einer gemessenen
  Wirkung.

**ABER: die DOSIS steht auf einer fremden Grundmenge -- Rechenfehler, gefunden beim Nachlesen.** par.11c
leitet `p = 1 - 0,85^(1/11,07) = 0,0146` aus "11,07 Gelegenheiten mit mindestens drei Restplatten je Partie
(142.945 Faelle auf 12.907 Partien, `PREREG_moon_stack_order.md` par.9b)" her. **Die 142.945 sind
MONDSTAPEL-Dreierstapel** (Sonnensteine aus Fabriken, `moon_stack_order` par.9b: *"Korrekt gezaehlt sind es
142.945 Dreierstapel, also 22,4 Prozent aller Ereignisse"*, Grundmenge Mondstapel-Ereignisse), **nicht
zurueckgelegte Kuppelplatten**. Die Zahl beschreibt einen anderen Gegenstand als ihr Verbraucher.

**Gemessen am v30-Korpus** (2026-09-18, n = 1.778 Stapelzuege aus 400 Partien der Sockel-Klasse, Grundmenge
Stapelzuege, Einheit Zuege je Partie): Zuege mit mindestens vier gezogenen Platten, also mindestens DREI
Restplatten und damit genau der Knopf-Schwelle, gibt es **89 = 0,2225 je Partie**. Die Herleitung nahm das
**50-fache** an. Unabhaengige Stuetze im selben Dokument, zwei Absaetze ueber der Rechnung: par.11b misst
**0,19 Abweichungen je Partie** (150 Partien, Modus 1) mit Serienlaengen 4 bis 12 -- dieselbe
Groessenordnung wie 0,22, nicht wie 11.

### 12.12a DOSIS NEU GERECHNET (Nutzer 2026-09-18, 23:55: "es bleibt bei den 15%")

Der Zielwert bleibt: **in 15 Prozent der Partien mindestens einmal streuen** (par.11b Punkt 2). Die Zahl
dahinter wird neu gerechnet, und zwar diesmal ueber die VERTEILUNG der Gelegenheiten je Partie, nicht ueber
ihren Mittelwert -- der Unterschied ist hier gross, weil die Verteilung stark schief ist.

**Gemessen** (n = 400 Partien der Sockel-Klasse `v29-b11-policy`, 40 Dateien, Grundmenge Partien, Einheit
Gelegenheiten mit mindestens drei Restplatten je Partie):

| Gelegenheiten in der Partie | Partien | Anteil |
| --- | --- | --- |
| 0 | 329 | 82,2 % |
| 1 | 55 | 13,8 % |
| 2 | 14 | 3,5 % |
| 3 | 2 | 0,5 % |

**Nur 17,75 Prozent der Partien haben ueberhaupt eine Gelegenheit.** Das ist die OBERGRENZE der erreichbaren
Partie-Rate: selbst bei `p = 1,0` (immer streuen) kaeme man nicht ueber 17,75 Prozent. Die
Mittelwert-Rechnung aus 12.12 (`p = 0,52`) liefert in Wahrheit nur 10,29 Prozent -- sie unterstellt, jede
Partie haette 0,2225 Gelegenheiten, waehrend in Wirklichkeit vier Fuenftel der Partien gar keine haben.

| Dosis p | Partie-Rate (exakt ueber die Verteilung) |
| --- | --- |
| 0,0146 (registriert) | 0,32 % |
| 0,52 (Mittelwert-Rechnung) | 10,29 % |
| **0,81** | **15,0 %** |
| 1,0 (Maximum) | 17,75 % |

**DOSIS: `MOSAIC_RETURN_ORDER_RANDOM_P = 0.81`.**

**Was das bedeutet, damit es niemanden ueberrascht:** "15 Prozent der Partien" heisst bei dieser
Gelegenheitsrate **"in 81 Prozent der Gelegenheiten streuen"**. Die Streuung ist an dieser Stelle also nicht
mehr eine Beimischung, sondern der Normalfall -- schlicht deshalb, weil die Gelegenheit selbst so selten ist.
Fuer den registrierten Zweck (ABDECKUNG des Zustandsraums, par.11c) ist das stimmig; wer "15 Prozent" als
"selten" gelesen hat, sollte die zweite Zahl kennen.

**Vorbehalt, ausdruecklich:** die Gelegenheitsrate ist VERHALTENSABHAENGIG, nicht strukturell. Gemessen wurde
sie an einem Sockel, der an den Knoten argmax spielt und selten tief zieht (80,4 Prozent der Stapelzuege
ziehen nur eine Platte, `PREREG_v30_window.md` par.9). Lernt das Netz, oefter tief zu ziehen -- genau die
Wirkung, die der Nutzer sich erhofft --, steigt die Zahl der Gelegenheiten und mit ihr die Partie-Rate bei
gleicher Dosis. Die 0,81 sind daher an der v30-Erzeugung geeicht und gehoeren nach der v31-Erzeugung
nachgerechnet. Zweiter Vorbehalt: gemessen nur an der Sockel-Klasse; die temperierte Klasse zieht moeglicher-
weise anders tief, UNGEPRUEFT.

**Folge, gerechnet:** mit `p = 0,0146` wuerde in **0,33 Prozent der Partien** gestreut statt in 15 Prozent,
das sind **13 Streuungen je 4.000-Partien-Klasse**. Fuer das registrierte Ziel "in 15 Prozent der Partien
mindestens einmal" waere **p = 0,52** noetig (463 Streuungen je Klasse). **NUTZER-VORLAGE:** die Dosis ist
entschieden, ihre Zahl aber auf der falschen Grundmenge gerechnet -- 0,0146 beibehalten hiesse, einen Knopf
zu bauen, der praktisch nie feuert.

**Was fuer den Bau spricht, unabhaengig von der Dosis** (Nutzer-Hinweis 2026-09-18, 23:10 -- der tiefe
Stapelzug wird durch die Rueckgabewahl attraktiver, und in fruehen Runden ist das keine falsche Taktik):
gemessen an 1.778 Stapelzuegen aus 400 Partien der Sockel-Klasse ziehen **80,4 Prozent nur EINE Platte**;
tiefe Zuege (>= 3 Platten) machen **8,0 Prozent** aus und sitzen fast vollstaendig in **Runde 2 (18,4 Prozent,
mittlere Tiefe 1,99)**, waehrend Runde 4 **keinen einzigen** tiefen Zug zeigt (mittlere Tiefe exakt 1,00) --
passend zum Rundenfenster `return_order_round_allowed`. Gemessen wurde das an einem Sockel, der an diesen
Knoten argmax spielt; es zeigt also den IST-Zustand des Netzes, nicht das Optimum.

## par.13 WIRKUNGSFRAGE GESCHLOSSEN (Nutzer-Entscheid 2026-09-21)

**Nutzer: *"kannst schliessen"*.** Damit steht das Verdikt zur Leitfrage dieser Prereg.

### GEBAUT: ja, vollstaendig

Die Rueckgabe-Reihenfolge ist ein eigener Entscheidungsknoten (IDs 411-413, `choose_return_first`,
`neural_net.py:1067-1069`) und steht im Aktionsraum, im Encoder, in der Suche und im Korpus.

### TRAEGT: kein messbarer Effekt, und der Grund war vorab registriert

Das vorab festgelegte A/B (par.5 Punkt 1) ergab ueber zwei Seed-Basen **74:76 und 74:76**,
Vorzeichentest **p = 1,0** in beiden Faellen, gepaarte Differenz -0,027 mit der Null im Intervall,
Punkte praktisch gleich (54,14/54,23 und 52,88/53,07). Nach der Regel aus par.5 heisst das "kein
messbarer Effekt".

**Der erklaerende Befund steht daneben:** in **93 bzw. 85 Prozent** der Paare spielen beide Modi
dasselbe. Der Deckel dafuer war in par.8a Befund 1 VORAB registriert -- der Value-Kopf sieht die
Reihenfolge nur als TYP-Folge (`features.rs:212`, oberste vier Positionen als +1 Spezial /
-1 Joker / 0). Permutationen gleichtypiger Platten sind fuer das Netz identisch, und Modus 1
faellt dann per Gleichstand auf die Ziehreihenfolge zurueck.

**Der Knopf bleibt** (par.0/par.1, Nutzer-Praezedenz): der Massstab ist Vollstaendigkeit, nicht
Elo. Ein legaler Zug, den die Suche nicht waehlen kann, ist eine Luecke im Modell, auch wenn sie
nichts kostet. Default unveraendert `MOSAIC_RETURN_ORDER_MODE = 0` (Ziehreihenfolge); die
Champion-Spec `v31-b01` traegt das Feld nicht, der Champion spielt also auf dem Default.

### Die Dosis-Nachrechnung an der v31-Erzeugung: GEMACHT (2026-09-21)

12.12a hielt fest, dass `p = 0,81` an der **v30**-Erzeugung geeicht wurde und die Gelegenheitsrate
VERHALTENSABHAENGIG ist -- lernt das Netz, oefter tief zu ziehen, steigen die Gelegenheiten. Die
Wiedervorlage ist jetzt eingeloest.

**n = 300 Partien je Klasse** (30 ordnungsfrei gezogene Dateien je Klasse, Seed 7),
**GRUNDMENGE** die Partien dieser Dateien, **EINHEIT** Partien mit mindestens einem Record, dessen
`valid_actions` eine der IDs 411-413 traegt:

| Klasse | Partien mit Gelegenheit | Records mit Knoten (valid / policy) |
| --- | --- | --- |
| Sockel (`policy`) | 84 von 300 = **28,0 %** | 105 / 105 |
| temperiert (`value-tempc`) | 67 von 300 = **22,3 %** | 74 / 74 |
| Ausflug (`value-excursion`) | 62 von 295 = **21,0 %** | 78 / 78 |

**Die Vorhersage aus 12.12a haelt.** An der v30-Erzeugung hatten **17,75 Prozent** der Partien
ueberhaupt eine Gelegenheit; im Sockel der v31-Erzeugung sind es **28,0 Prozent** -- Faktor 1,58 in
genau der Richtung, die der Vorbehalt genannt hat. Der zweite Vorbehalt ("temperierte Klasse
UNGEPRUEFT") ist damit ebenfalls erledigt: sie liegt mit 22,3 Prozent unter dem Sockel, nicht
darueber.

**Und der Knoten traegt durchgehend ein Lernziel:** in allen drei Klassen ist jeder Record, der
die IDs in `valid_actions` hat, auch in `policy` vertreten (105/105, 74/74, 78/78). Der v31-Korpus
erfuellt damit die Bedingung aus `feedback_knob_ab_needs_corpus_that_used_it` -- ein A/B ueber
diesen Knopf waere auf ihm erstmals nicht mehr Henne-Ei.

**Vorbehalt zur Vergleichbarkeit, ausdruecklich:** die 17,75 Prozent stammen aus der Zaehlweise von
12.12a, meine 28,0 Prozent aus der oben benannten. Beide meinen "Partie hat mindestens eine
Gelegenheit", aber sie sind nicht Zeile fuer Zeile gegeneinander geprueft; die Richtung ist
belastbar, der Faktor 1,58 auf die zweite Stelle nicht.

### NACHTRAG 2026-09-22: die Nachrechnung hat jetzt einen Verbraucher

Als par.13 geschrieben wurde, galt v31 als letzte Generation; die Nachrechnung war damit ein
Abschlussbefund ohne Abnehmer. **Nutzer-Entscheid 2026-09-22: v32 wird gefahren.** Damit hat sie
einen, und zwar sofort:

**Die Dosis `MOSAIC_RETURN_ORDER_RANDOM_P = 0,81` ist an der v30-Erzeugung geeicht** -- dort hatten
17,75 Prozent der Partien ueberhaupt eine Gelegenheit. Gemessen an der v31-Erzeugung sind es
**28,0 Prozent** (Sockel). Bei unveraenderter Dosis streut die v32-Erzeugung also in deutlich mehr
Partien als die 15 Prozent, fuer die `p = 0,81` einmal ausgerechnet wurde.

**Vor dem Start der v32-Erzeugung ist die Dosis neu zu setzen oder ausdruecklich zu bestaetigen.**
Der Ort dafuer ist par.6 der v32-Fenster-Prereg, nicht diese Datei. Nach der Rechnung aus 12.12a
(gesucht ist das `p`, das die Zielrate bei der GEMESSENEN Gelegenheitsrate trifft) laegen bei
28,0 Prozent Gelegenheit rund **`p = 0,54`** an. **Das ist eine Herleitung aus der Messung oben,
keine Entscheidung** -- sie liegt beim Nutzer.

Das Verdikt zur Leitfrage bleibt unberuehrt: es haengt am A/B und am Typ-Folge-Deckel, nicht an der
Zahl der Generationen.

### BERICHTIGUNG 2026-09-23: mein Vergleich von gestern war apples-to-oranges

**Am v32-Korpus mit DERSELBEN Zaehlweise nachgemessen, beide Generationen, je 20 Dateien und
200 Partien:**

| Erzeugung | Partien mit Gelegenheit | Partien mit Streuung |
| --- | --- | --- |
| v31 (Generator `v30-b02`) | 45 von 200 = **22,5 %** | 24 = **12,0 %** |
| v32 (Generator `v31-b01`) | 47 von 200 = **23,5 %** | 28 = **14,0 %** |

**+1,0 Prozentpunkte bei n = 200 -- das ist Rauschen** (eine Standardabweichung liegt bei rund
3 Punkten). Die Gelegenheitsrate hat sich zwischen den Generationen NICHT bewegt.

**Wo mein Fehler lag:** die 17,75 Prozent aus 12.12a zaehlen Partien mit mindestens einer
Gelegenheit **mit MINDESTENS DREI Restplatten**. Meine 28,0 Prozent zaehlten Partien mit
mindestens einem Record, dessen `valid_actions` die IDs 411-413 traegt -- und der Knoten steht
dort, sobald ueberhaupt eine Wahl besteht, also **ab ZWEI Platten**. Die zweite Menge enthaelt die
erste; sie musste groesser sein. **Verglichen habe ich damit nicht zwei Generationen, sondern zwei
Kriterien.**

Ich hatte den Vorbehalt selbst hingeschrieben ("nicht Zeile fuer Zeile gegeneinander geprueft")
und die Zahl trotzdem eine Empfehlung tragen lassen. Genau davor warnt CLAUDE.md Zusatz 2: n,
GRUNDMENGE und EINHEIT gegen die des VERBRAUCHERS pruefen.

**Was damit faellt:**

* Der "Faktor 1,58 nach oben" -- nicht belegt.
* Die hergeleitete Dosis **`p = 0,54`** -- nicht belegt. Sie stand auf dem Sprung von 17,75 auf
  28,0, den es nicht gibt.
* Der Satz, die Nachrechnung sei "der erste Handgriff vor der v32-Erzeugung" -- sie war es nicht.

**Was steht:** die Streurate liegt bei **14,0 Prozent** gegen das Ziel von 15 Prozent, bei n = 200
also innerhalb einer halben Standardabweichung. **Die Dosis 0,81 ist richtig eingestellt**, und der
Nutzer-Entscheid "Einstellungen wie v31" brauchte keine Revision -- er war die richtige Wahl, aus
einem Grund, den ich erst hinterher sauber messen konnte.

### Warum hier nicht weiter gemessen wird

Ein A/B, das den Deckel umgeht, muesste zuerst den ENCODER aendern -- die Reihenfolge als mehr als
eine Typ-Folge zeigen. Das ist eine andere Frage als die dieser Prereg, und par.10 hat "keine
weitere Stufe" bereits als Nutzer-Entscheid registriert. Das A/B mit mehr Partien zu wiederholen
wuerde am 93-Prozent-Split nichts aendern: Paare, die nichts unterscheiden, werden durch mehr
Partien nicht informativ.
