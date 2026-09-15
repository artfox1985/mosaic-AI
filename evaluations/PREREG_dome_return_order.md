<!-- STATUS: OFFEN | Frage: Die Rueckgabe-Reihenfolge nicht gewaehlter Kuppelplatten ist ein legaler Zug -- wird die Wahl gebaut, und traegt sie? | Beleg: Knopf gebaut (par.8a), A/B ohne Effekt (par.9), Streu-Knopf fuer die Erzeugung gebaut und abgenommen (par.11-11c, Dosis 0,015). **par.12: R1 gemessen -- der Value-Kopf reagiert auf die Typfolge (Median-Spannweite 0,019, 81 Prozent ueber 0,01, n = 300; 12.4); Arena gezaehlt: 0,6 Gelegenheiten je Partie und Seite, Modus 1 weicht in 42 Prozent ab, erwartete Wirkung rund 0,005 je Partie -- der par.9-Nullbefund ist Arithmetik, ein A/B loest den Knopf nicht auf (12.5).** ENTSCHIEDEN 2026-09-15 (12.6): R2 wird gebaut (VOR der v30-Erzeugung, INPUT_SIZE 798, Fahrplan 29c) und Modus 1 ist in der v30-Erzeugung AN (Korrektheit, Kostentor beim Start). OFFEN: Bau und Korpus. -->

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
