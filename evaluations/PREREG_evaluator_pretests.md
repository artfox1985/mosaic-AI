<!-- STATUS: OFFEN | Frage: Welche Bewerter-Vorschlaege aus der Architektur-Recherche vom 2026-09-25 (E1 Einpass-Konsum, E2 Margen-Schwellen, E3 Rundenschicht, E4 Angebots-Bedarfs-Sicht) ueberleben einen billigen Vortest, bevor Self-Play-Zeit faellt? | Beleg: Stufe 1 gefahren 2026-09-26 (par.8): E1 gleich gut (Brier-Differenz -0,00012, CI um 0), Arm kommt wegen der Kosten; E2 BESTEHT (+0,00213); E3 TOT (global besser in allen Runden); E4-Vortest BESTEHT (18/18, par.8c). Stufe 2 (E1-Arm, E4) nach Kette und b02 (par.5). -->

# Vorregistrierung: Vortests fuer den Bewerter (E1-E4)

**Angelegt 2026-09-25.** Quelle der Vorschlaege:
`evaluations/RESEARCH_evaluator_architecture_external_2026-09-25.md` Abschnitt 7 (E1-E5).
E5 (Gewichtsmittelung) ist hier NICHT aufgenommen: kleiner erwarteter Gewinn, kein Vortest auf
vorhandenen Laeufen moeglich (dort Abschnitt 7, E5).

## par.1 Anlass und Nutzer-Entscheid

Nutzer 2026-09-25, nach Vorlage der Recherche: *"V9 Ergebnisse sind hoffnungslos ueberholt. Da
lohnt sich e1 sicher. Ja Takte deinen Vorschlag so ein"*.

Daraus folgt:
* **E1 bekommt einen Arm, unabhaengig vom Vortest.** Der einzige Test (2026-07-20, `v9b_domeonly`,
  150 Sims, n = 100 gegen die Heuristik, 3:97; `engine/src/net_mcts.rs:1951-1957`) lief mit einem
  Netz, das in beiden Armen fast alles verlor; der Nachtest wurde spaeter bewusst zurueckgestellt
  (`archive/history.md:1366-1368`). Der Vortest in par.3 liefert die Erwartung und die
  Lesegrundlage fuer den Arm, er entscheidet ihn nicht.
* **E2, E3, E4 bekommen einen Arm NUR, wenn ihr Vortest besteht** (par.4, par.5c). Eine tote
  Idee soll Minuten kosten, nicht rund 4.500 Partien (Kostenrechnung im Recherche-Bericht,
  Abschnitt 7).

**Kein neuer Kopf** (Nutzer 2026-09-14): E1 ist reiner Konsum, E2 sind Verlustterme am bestehenden
WDL-Logit, E3 ein Umbau der letzten Value-Schicht, E4 ein Encoder-Abschnitt.

## par.2 Gemeinsames Substrat (Stufe 1)

**Werkzeug:** `tools/probes/evaluator_pretests.py` (geschrieben 2026-09-25, noch nicht gelaufen;
Aufruf `python -u tools/probes/evaluator_pretests.py`). Konstanten dort tragen die Werte dieses
Absatzes und von par.4; eine Aenderung geht zuerst hierher.

* **Modell:** Champion `models/alphazero_v32-b01_brierbest.pth` (identisch mit
  `models/frozen_champions/v32-b01/model.pth`; die Werkzeug-Pruefung vergleicht die sha256 und
  bricht bei Abweichung ab).
* **Zustaende:** Val-Menge des Champion-Trainings, `data/window_v32_val.txt` (147 Dateien, am
  2026-09-25 vollstaendig im Baum, gezaehlt: 51 `v31-b01-policy`, 41 `v31-b01-value-excursion`,
  55 `v31-b01-value-tempc`). Der Champion hat diese Dateien nie trainiert.
  **Auswahl:** 60 Dateien, je Klasse 20, gezogen mit `random.Random(20260926)` aus der sortierten
  Liste je Klasse. **Grundmenge:** alle Records mit `state.phase == "drafting"`
  (`engine/py/corpus_dataset.py:1330`) und `completed is not False` dieser Dateien. **Einheit:** Zustand. **Block:** Datei (60 Bloecke);
  jede Streuangabe ist ein Block-Bootstrap ueber Dateien (2.000 Ziehungen, Seed 20260927).
* **Merkmale:** ueber den Rust-Bauer (`MOSAIC_FEATURES_FROM_RUST=1`,
  `neural_net.state_to_tensor_rust`/`state_to_planes_rust`), also derselbe Code wie im Spielpfad.
* **Ausgang:** `winner` und `scores_unclamped` des Records (Feldnamen am Lader geprueft,
  `engine/py/corpus_dataset.py:1375-1377`).
* **Kosten:** UNGEMESSEN. Das Werkzeug schreibt den `laufzeit`-Block und einen
  Fortschrittszaehler mit `flush=True`.

## par.3 Stufe 1a: E1 offline

**Was die Suche heute tut** (am Code geprueft 2026-09-25): je Blatt zwei Vorwaertspaesse; der
zweite auf einer Kopie mit geflipptem `current_player` (`net_mcts.rs:3401-3405`), eine Eingabe,
die im Training nie vorkommt (`net_mcts.rs:1935-1941`). Der Wert des Nicht-Ziehers am Blatt kommt
aus diesem Pass (`net_mcts.rs:3575-3593`). E1 ersetzt ihn durch `1 - p_zieher`.

**Messgroessen je Zustand:** `p_z` = P(Sieg) des Ziehers aus dem normalen Pass, `p_f` = P(Sieg)
des Nicht-Ziehers aus dem geflippten Pass (Zustand mit `current_player` auf den Gegner gesetzt),
beide wie `value_to_win_prob` (`net_mcts.rs:2825-2828`: `(v + 1) / 2`, im Python-Netz
`softmax(wdl)[1]`).

1. **Versatz** `d = p_z + p_f - 1`, VORZEICHENBEHAFTET, Mittel je Runde 1-4 mit Block-CI. (Der
   Bestand loggt nur `|d|` und verwirft es, `self_play.py:797-803`; die Paarsumme 1,13-1,14 ist
   ein Bootstrap-Befund der v21-Aera, `PREREG_heuristic_v2_long_rows.md:1235-1240`.)
2. **Brier gegen den Ausgang des Nicht-Ziehers:** `B_flip = Brier(p_f)` gegen
   `B_e1 = Brier(1 - p_z)`, gepaarte Differenz `B_e1 - B_flip` je Runde und gesamt, Block-CI.

**Leseregel (liest den Arm, entscheidet ihn nicht):**
* CI von `B_e1 - B_flip` ganz unter 0: der geflippte Pass ist schlechter als die Einpass-Naeherung;
  E1 erwartet Staerke UND spart Rechenzeit.
* CI enthaelt 0: gleich gut in dieser Aufloesung; der Arm entscheidet ueber Staerke, der
  Kostengewinn ist das Hauptmotiv.
* CI ganz ueber 0: der zweite Pass traegt Information (Ensemble-Effekt); der Arm laeuft trotzdem,
  die Erwartung ist dann ein Stark-gegen-billig-Tausch.

**Vorbehalt Sicht, vorab benannt:** die Records sind aus Sicht des Ziehers serialisiert, und der
Rust-Bauer liest das JSON-Dict direkt (`engine/src/lib.rs:1763-1766`, `features::state_to_features`),
baut also keinen Zustand neu auf. Von den Feldern, die `features.rs` liest (gegrept 2026-09-25),
ist `dome_pool_view` sichtabhaengig serialisiert (`engine/src/serialize.rs:97-137`: `own`,
`designs`, `designs_ordered` nur fuer den Block des Ziehers); `chippable_tiling_rows` traegt den
Spieler als Feld `pi` (ob fuer beide Spieler befuellt, nicht nachgelesen; betrifft die
Tiling-Phase, das Substrat hier ist Drafting), `pending_stack_draw` ist Zustand, keine Sicht. Der Flip ueber JSON zeigt
dem Gegner die Rueckgabe-Bloecke deshalb nicht so, wie die Suche sie ihm zeigt (die Suche flippt
den vollen Zustand). **Primaerauswertung darum nur auf Zustaenden ohne bekannte Rueckgabe-Bloecke**
(`dome_pool_view.blocks` leer); die anderen werden getrennt berichtet. Ob die Kuppel-Zweistufigkeit
(`extended_action_nodes`) Geschwister mit gemischtem Folgezieher erzeugt, misst dieser Vortest
NICHT; das bleibt Herleitung (Recherche-Bericht 2.4).

## par.4 Stufe 1b: Kontrolle, E2 und E3 (lineare Leser auf dem Trunk)

**Extraktion:** die Eingabe des Value-Kopfs (`model.value_head` Forward-Pre-Hook, Muster
`tools/r4b_zone_probe.py:148-153`) fuer alle Zustaende aus par.2; dazu der Ausgang des Kopfs.
**Kreuzvalidierung:** 5 Faltungen ueber DATEIEN (je 12, Seed 20260926), Anpassung auf 4, Brier
auf der fuenften. Leser: logistische Regression mit L2 (Staerke per innerer Faltung gewaehlt),
Merkmale standardisiert.

**Kontrollprobe (Pflicht, vor E2/E3):** derselbe Leser auf der Value-Kopf-Eingabe eines ZUFALLS-
initialisierten Netzes derselben Architektur (`torch.manual_seed(20260926)`). Hewitt/Liang-Lehre
(Recherche-Bericht 2.1): eine hohe Probe-Guete zaehlt erst gegen die Kontrolle.
* **Trunk traegt:** Brier(Leser, Champion) liegt mit Block-CI unter Brier(Leser, Zufall).
  Sonst sind E2 und E3 in dieser Form TOT (der Vortest kann sie dann nicht tragen).

**Berichtsgroesse ohne Torfunktion:** Brier(Kopf) gegen Brier(Leser, Champion) je Runde. Das ist
die Mittelspiel-Fassung der R4b-Frage (`PREREG_value_readout.md` par.2, dort zurueckgezogen, weil
kein Entscheid dahinter stand); hier steht einer dahinter, darum wird sie mitberichtet.

**Schwelle, an der ein Leser-Gewinn zaehlt:** **0,0012 Brier** und Block-CI ganz auf der
Gewinnseite. Die 0,0012 ist der Gewinn EINER Korpus-Verdopplung (`PREREG_task36_value_saturation.md`
Z.94-97: 202 -> 405 -> 810 Dateien, 0,19934 -> 0,19813 -> 0,19695, drei Seeds). Grundmenge dort:
Val-Brier des Value-Kopfs gegen den Ausgang, v20-Aera, anderes Messset; hier Brier eines Lesers
gegen den Ausgang auf Drafting-Zustaenden. Die Einheit stimmt, das Substrat nicht; die Zahl ist
ein Kostenanker ("so viel wie doppelt so viele Partien"), kein Aequivalenzbeweis.

**E2, Margen-Schwellen:** Leser (a) logistisch auf `1[Sieg]`. Leser (b) Proportional-Odds mit
gemeinsamem Logit `z` und Schwellen `t in {-10, -5, 0, +5, +10}` Punkte auf die Marge
`scores_unclamped[p] - scores_unclamped[1-p]`, Skala je Runde; bewertet wird (b) ueber
`sigma(z)` an der Schwelle 0 gegen `1[Sieg]`. **Besteht**, wenn Brier(a) - Brier(b) >= 0,0012
mit Block-CI > 0, gesamt ueber Runde 1-4. (Gleichstaende: `winner` entscheidet, die Marge 0 geht
an die Seite, die `winner` nennt; `docs/engine_manual.md` regelt den Gleichstand ueber eine
Zusatzregel, Stelle im Recherche-Bericht 2.4 zitiert, hier nicht nachgelesen.)

**E3, Rundenschicht:** Leser global (ein Satz Gewichte) gegen fuenf Leser je Runde (Runde 5 nur
berichtet: dort rechnet die Suche exakt, `round5.rs`). **Besteht**, wenn der Rundenleser in
MINDESTENS ZWEI der Runden 1-4 um >= 0,0012 mit Block-CI > 0 besser ist.

## par.5 Stufe 2: nach der v33-Kette und dem b02-A/B

**par.5a Bau (eine Wheel-Runde fuer beides):**
* E1 als LAUFZEIT-Knopf (Spec-Feld plus Env-Name, Registrierung in `knob_registry.rs`, dann
  `tools/generate_knob_docs.py`); Default aus = heutiges Verhalten, byte-identisch. Die
  Kompilierzeit-Konstante `MIRROR_OTHER_VAL` (`net_mcts.rs:1958`) wird dabei durch den Knopf
  ersetzt, nicht daneben gestellt.
* Fuer E4: ein pyo3-Export, der aus einem Record-JSON je legalem Steinzug die Folge auf der
  Musterreihe liefert (Steine in der Reihe, Ueberlauf auf die Strafleiste, Reihe voll ja/nein).
  Grund: der Bestand hat keinen Weg, einen Zug auf einen JSON-Zustand anzuwenden (`py.rs` hat
  `apply_stone` nur am laufenden Spiel; gegrept 2026-09-25), und die Regel "wie viele Steine
  nimmt ein Zug" wird nicht in Python nachgebaut (CLAUDE.md, Regel 0 Ausloeser 3).
* Pflicht danach: Netz-Paritaet (Knopf aus), `/mosaic-anchor-invariance`, `cargo test --release
  --no-run` (examples/benches).

**par.5b E1-Arm:**
* **Kostentor:** Self-Play mit dem Champion, je Arm 100 Partien, gleiche Seeds, gleiche Threads,
  exklusiv; Messgroesse `s_je_partie` aus dem `laufzeit`-Block. Berichtet wird die Ersparnis in
  Prozent und umgerechnet in Partien je 4.000er-Klasse.
* **Staerke:** Champion mit Knopf gegen Champion ohne Knopf, Spec `models/v33_gating.spec.json`
  beidseits bis auf den Knopf, 2 Seeds x 200 Paare, Blockgroesse 5, Block-z
  (`tools/gating_block_z.py`). Champion ist, wer nach der v33-Kette Champion ist.
* **Entscheid fuer die v34-Erzeugung:** z >= +1,96 auf beiden Seeds oder gepoolt: Knopf an.
  z <= -1,96: Knopf aus. Dazwischen: Nutzer-Entscheid mit der Kostenzahl aus dem Kostentor
  (die Erzeugung waere dann gleich stark und billiger oder gleich stark und gleich teuer).
* **Folge fuer die Labels:** mit Knopf aendern sich `root_q` und die Bootstrap-Werte der naechsten
  Erzeugung; das ist gewollt und gehoert in die v34-Fenster-Prereg.
* **Bau-Stand 2026-09-26 (Agent, ungebaut):** Spec-Feld `single_pass_other_val` je Seite plus
  Env-Fallback `MOSAIC_SINGLE_PASS_OTHER_VAL`. Die LABEL-Pfade (`net_leaf_eval` in `self_play.rs`,
  `round_transition_deep.rs`) lesen nur den Env-Default: fuer eine v34-Erzeugung mit E1 muss die
  Env-Variable gesetzt sein, das Spec-Feld allein aendert die Bootstrap-Werte nicht. Fuer das
  Arena-A/B (par.5b) reicht das Spec-Feld.

**par.5c E4-Vortest:** mit dem Export aus par.5a je Zustand und eigener Musterreihe die Groessen
"groesste Steinzahl, die ein Zug ohne Ueberlauf in die Reihe legt", "ein Zug fuellt die Reihe
genau", "kleinster Ueberlauf eines Zugs, der die Reihe fuellt" berechnen (Zuschnitt vorlaeufig,
Recherche-Bericht E4). Linearer Leser auf der Value-Kopf-Eingabe des Champions, 5-fach ueber
Dateien wie par.4; Guete je Groesse als R2 (stetig) bzw. Brier (binaer), dazu dieselbe Kontrolle
mit Zufalls-Trunk. **Besteht (= Bau lohnt)**, wenn der Champion-Trunk die Groessen NICHT schon
traegt: R2 < 0,9 bzw. Brier deutlich ueber dem Zufalls-Trunk-Abstand; die genaue Schwelle wird
VOR dem Lauf in diesem Absatz nachgetragen, sobald die Grundraten der Groessen bekannt sind (die
Grundrate bestimmt, was bei Brier "deutlich" heisst).

**SCHWELLE, nachgetragen 2026-09-27 VOR dem Lauf:** fuer stetige UND binaere Groessen dasselbe Mass,
der erklaerte Varianzanteil `EV = 1 - MSE / Var` auf den ausgehaltenen Faltungen (bei binaeren
Groessen ist MSE der Brier und Var = p(1-p), EV also Brier-Skill gegen die Grundrate). Je Groesse
und Musterreihe:
* **Trunk traegt es schon:** EV(Champion) >= 0,9 -- dann lohnt der Encoder-Abschnitt fuer diese
  Groesse nicht.
* **Luecke belegt:** obere Block-CI-Grenze von EV(Champion) < 0,9 UND EV(Champion) > EV(Zufalls-Trunk)
  mit CI > 0 (sonst ist die Groesse linear ueberhaupt nicht lesbar, und der Vortest sagt nichts).
**E4 BESTEHT, wenn fuer mindestens die Haelfte der (Groesse, Reihe)-Paare mit Grundrate zwischen 5
und 95 Prozent (binaer) bzw. Var > 0 (stetig) die Luecke belegt ist.** Grundmenge: Drafting-Records
MIT mindestens einem Steinzug in `valid_actions` (der JSON-Rueckweg rekonstruiert offene Wahlen
nicht), Substrat wie par.2.

## par.6 Stufe 3

Was besteht (E2, E3, E4), wird ein Arm im v34-Rezept: einfaktoriell gegen den Referenzarm auf
demselben Fenster und Monolithen, Tor 1 wie gewohnt. Zuschnitt in der v34-Fenster-Prereg, nicht
hier.

## par.7 Zeitplan

1. v33-Erzeugung fertig, Pflichtpruefungen `PREREG_v33_window.md` par.9.
2. **Stufe 1 (par.3, par.4)**, Maschine exklusiv, keine Builds noetig.
3. Nutzer-Go, v33-Kette; danach `tools/night_v33_b02.sh`.
4. **Stufe 2 (par.5)**: Bau, Anker, E1-Kostentor, E1-Arm, E4-Vortest.
5. v34-Generationswechsel mit den Ergebnissen.

## par.8 Ergebnisse

### par.8c E4-Vortest, gefahren 2026-09-27 (345,2 s, exklusiv)

`tools/probes/e4_supply_demand_pretest.py`, Artefakt `evaluations/artifacts/e4_supply_demand_pretest_v32-b01.json`.
Substrat wie par.2 (60 Val-Dateien von v32, Champion `v32-b01`), Grundmenge **47.433** Drafting-Records
mit mindestens einem Steinzug (38.757 ohne Steinzug ausgelassen: offene Wahlen, par.5c). Groessen aus
dem Engine-Export `stone_move_outcomes_from_json` (jeder legale Steinzug auf einem Klon ausgefuehrt).

| Groesse (Reihe 0 bis 5) | EV Champion-Trunk | EV Zufalls-Trunk |
| --- | --- | --- |
| groesste Steinzahl ohne Ueberlauf | 0,674 / 0,743 / 0,725 / 0,664 / 0,631 / 0,592 | 0,36-0,56 |
| ein Zug fuellt die Reihe genau | 0,674 / 0,607 / 0,172 / 0,091 / 0,109 / 0,093 | 0,02-0,56 |
| kleinster Ueberlauf beim Fuellen | 0,377 / 0,442 / 0,411 / 0,062 / 0,120 / 0,044 | -0,16-0,04 |

(Reihe 0: die ersten beiden Groessen fallen bei Kapazitaet 1 zusammen, daher identisch.)
**Alle 18 zulaessigen Paare: Luecke belegt** (obere CI-Grenze < 0,9 und ueber dem Zufalls-Trunk).
**VERDIKT nach par.5c: BESTEHT** -- der Trunk des Champions traegt die Angebots-Bedarfs-Relation nur
teilweise, am schwaechsten fuer die langen Reihen (3-5) und fuer "genau fuellen". Folge nach par.6:
E4 wird ein Arm im v34-Rezept (Encoder-Abschnitt, Bau 1-2 Tage laut Recherche-Bericht E4; aendert
`INPUT_SIZE`, also additiv nach `project_2d_encoder_must_be_additive`). Zuschnitt in der v34-Prereg.
Einschraenkung: ein LINEARER Leser; ein nichtlinearer Kopf koennte mehr herausholen (vgl. par.8a:
dort schlug der Kopf den linearen Leser um 0,008-0,016 Brier).

### par.8a Stufe 1, gefahren 2026-09-26 (exklusiv, 495,2 s)

Artefakt `evaluations/artifacts/evaluator_pretests_stage1_v32-b01_brierbest.json`. Substrat wie
par.2: 60 Dateien, **86.190 Drafting-Zustaende**, davon 24.533 mit bekannten Rueckgabe-Bloecken,
0 Records mit abweichendem Zieher. Alle Streuangaben Block-Bootstrap ueber die 60 Dateien. Einmal
lief waehrend der Extraktion `generate_prereg_index.py` daneben (Sekunden); die Rechnung ist
deterministisch, betroffen waere nur die Laufzeit.

**E1 (par.3), Primaerstratum ohne Bloecke, n = 48.799 Zustaende in Runde 1-4:**

| Runde | Versatz d = p_z + p_f - 1 | B_e1 - B_flip |
| --- | --- | --- |
| 1 | **+0,0450** [+0,0412; +0,0489] | -0,00030 [-0,00148; +0,00091] |
| 2 | +0,0119 [+0,0050; +0,0185] | -0,00034 [-0,00140; +0,00066] |
| 3 | +0,0329 [+0,0224; +0,0428] | +0,00049 [-0,00068; +0,00170] |
| 4 | -0,0083 [-0,0193; +0,0030] | -0,00012 [-0,00144; +0,00122] |
| 1-4 | **+0,0231** [+0,0182; +0,0279] | **-0,00012** [-0,00066; +0,00042] |
| 5 (berichtet) | +0,0215 | -0,00200 [-0,00300; -0,00106] |

**Lesart nach par.3: gleich gut in dieser Aufloesung.** Die Einpass-Naeherung ist gegen den
Ausgang so genau wie der geflippte Pass; der zweite Pass traegt keine messbare Zusatzinformation.
Dafuer ist er systematisch OPTIMISTISCH: die beiden Siegwahrscheinlichkeiten eines Zustands
summieren sich im Mittel zu 1,023, in Runde 1 zu 1,045 (Richtung wie der v21-Bootstrap-Befund,
`PREREG_heuristic_v2_long_rows.md:1235-1240`, dort 1,13-1,14 auf anderer Grundmenge). Der
Versatz schwankt je Runde, hebt sich also zwischen Geschwistern verschiedener Folgezieher nicht
sicher weg (Herleitung, nicht gemessen). Im Stratum mit Bloecken (Flip dort NICHT suchtreu)
gleiche Richtung, B_e1 - B_flip = -0,00082 [-0,00184; +0,00016]. **Folge:** der E1-Arm (par.5b)
kommt wie entschieden; sein Hauptmotiv ist der Kostengewinn, eine Staerke-Erwartung traegt der
Vortest nicht.

**Kontrollprobe (par.4):** Brier(Leser, Zufalls-Trunk) - Brier(Leser, Champion) = **+0,0426**
[+0,0346; +0,0505], n = 73.332 (Runde 1-4, alle Leser mit gueltiger Vorhersage). **Der Trunk
traegt**, die Leser-Vortests sind zulaessig.

**Berichtsgroesse Kopf gegen Leser** (Brier gegen den Sieg): der KOPF ist in jeder Runde BESSER
als der lineare Leser auf seiner eigenen Eingabe, um 0,0077-0,0159 (alle CIs unter 0). Im
Mittelspiel ist also KEIN Auslese-Verlust gegen den Ausgang nachweisbar; der R4b-Befund (Trunk
liest die EXAKTE Marge besser als die Koepfe) ist endspiel- und zielspezifisch. Das korrigiert
die Einordnung "die Koepfe verlieren, was der Trunk weiss" fuer das Mittelspiel.

**E2 (par.4):** Brier(a) - Brier(b) = **+0,00213** [+0,00048; +0,00370], n = 73.332.
**BESTEHT** nach der registrierten Regel (Mittel >= 0,0012 und CI > 0). Einschraenkung, vorab
nicht bedacht und darum hier ausdruecklich: beide Leser sind linear und liegen rund 0,01 Brier
hinter dem Kopf. Belegt ist, dass die Margen-Schwellen einem LINEAREN Siegwert-Leser helfen; ob
sie dem nichtlinearen, gemeinsam trainierten Kopf helfen, beantwortet erst der Arm (par.6). Die
untere CI-Grenze liegt bei 0,4 Verdopplungs-Aequivalenten, der Punktwert bei 1,8.

**E3 (par.4):** der Rundenleser ist in JEDER Runde schlechter als der globale (Runde 1-4:
-0,0069 bis -0,0206, alle CIs unter 0; Runde 5 -0,0024, CI um 0). **TOT** nach der Regel
(0 von 4 Runden bestanden). Plausibler Grund (Herleitung): ein Fuenftel der Daten je Leser kostet
mehr, als die Phasen-Anpassung bringt. Ein Rundenumbau der letzten Schicht im Netz teilt den
Trunk und waere nicht ganz dasselbe; der Vortest traegt ihn trotzdem nicht.
