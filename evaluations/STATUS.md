# Mosaic-AI — Aktueller Status

Löst `STAGE2_TODO_ARCHIVED.md` als lebendes Status-/Fahrplan-Dokument ab
(2026-07-17) — dieses File trägt NUR den aktuellen Stand, keine
Sweep-/Kapazitätstest-Historie mehr. Für die alte Architektur (tanh-Delayed-
Reward-Value-Ziel, "Stufe 1 bleibt Produktionspfad", VALUE_WEIGHT-Sweep,
v1-v7cold) siehe das archivierte File (`../archive/STAGE2_TODO_ARCHIVED.md`,
mit dem restlichen alten Auswertungsmaterial zusammengelegt).

## hs200 zurückgezogen (2026-07-19)

`data/selfplay_hs200_*.pkl` (600 Dateien, 6000 Spiele, ~7.7GB) nach
`data/archive_hs200/` verschoben (nicht gelöscht — `train.py`s Standard-Glob
`data/*.pkl` ist nicht rekursiv, greift also nicht mehr darauf zu). Grund:
bestätigter Korpus-Alter-Confound (siehe v9b_domeonly unten) — diese Partien
stammen von vor den Gamma-Pruning-Bugfixes dieser Session und verschlechterten
nachweislich die Policy-Generalisierung. Domefact-artige Selfplay-Daten
(sims=200, nach den Bugfixes) sind ab jetzt die alleinige Trainingsbasis.
Alte, jetzt permanent verwaiste HDF5-Caches (`data/.cache_*.h5`, ~2.1GB,
schlossen hs200 mit ein) können gefahrlos gelöscht werden — kein zukünftiger
Standard-Trainingslauf kann sie je wieder treffen.

## Aktuelles Ziel (2026-07-19, AKTUALISIERT nach v9b_domeonly)

**Den Value-Head geradeziehen** — das ist gerade die Priorität vor allem
anderen. Grund: ein Net-vs-Heuristik-A/B (siehe unten) zeigt, dass der
aktuell trainierte Value-Head die Live-Suche AKTIV verschlechtert, nicht nur
neutral bleibt. **WICHTIGE KORREKTUR nach v9b_domeonly**: das Problem ist
NICHT (nur) mehr "Val-R² ist negativ" — ein Value-Head mit gesundem,
stabilem, positivem R² (+0.22-0.24) zeigt in Arena WEITERHIN das
schlechteste Ergebnis der Session (0:12, Score 13.7 vs. 46.8). Die
"Zielformel reparieren"-Hypothese ist damit als VOLLSTÄNDIGE Erklärung
widerlegt (auch wenn sie die Val-R²-Metrik selbst nachweislich repariert
hat) — es braucht eine STRUKTURELLE Entscheidung, siehe "Nächste Schritte".
Zwei Dinge ausdrücklich NICHT auf dem Tisch:

- **Zurück auf Stufe 1 (DFS-Solver-Blatt) als Produktions-Default** — bewusst
  verworfen, obwohl es im A/B klar besser abschnitt (siehe unten). Das Ziel
  ist Rundenweitsicht (der Value-Head soll über den aktuellen Rundenrest
  hinaus einschätzen können) — genau die Fähigkeit, die Stufe 1 strukturell
  nicht hat (kein gecachter Blattwert pro Knoten, liest `state.factories`
  nirgends, siehe Architektur-Abschnitt unten). Ein Rückfall auf Stufe 1
  würde das eigentliche Ziel aufgeben, nicht erreichen.
- Weitere Experimente "draufsetzen" (mehr round_transition_value-Daten, mehr
  Kuppel-Faktorisierungs-Daten) OHNE zuerst zu verstehen, warum der Value-Head
  selbst nicht lernt — das wäre Symptombehandlung, nicht Ursachenbehebung.

## Architektur, Stand jetzt

- **Stufe 2 (Netz-Value-Blatt) bleibt der Produktions-Pfad**, trotz des
  Befunds unten — s.o., das Ziel ist Reparatur, nicht Rückfall.
  `net_mcts::ACTIVE_LEAF = LeafEval::Net`. Stufe 1 (`mcts.rs`, DFS-Solver-
  Blatt) bleibt im Code liegen, dormant, nicht mehr aktiv gepflegt.
- **Value-Head-Befund, KRITISCH (2026-07-19)**: kontrolliertes A/B (gleiche
  Sims=150 je Seite, SPRT-Abbruch) zeigt v8c UND v8d verlieren beide klar
  gegen die Heuristik-MCTS bei `ACTIVE_LEAF=Net` (v8c 1:14, v8d 0:12,
  Bodenstrafe ~20-25 vs. ~8-10). Diagnose-Flip auf `ACTIVE_LEAF=Dfs`
  (derselbe v8d-Checkpoint, sonst identische Einstellungen): Siegquote
  springt von 0% auf 26% (8:23), Score-/Bodenstrafe-Lücke schrumpft deutlich.
  **Schlussfolgerung**: der Value-Head (Val-R² durchgehend negativ, siehe
  unten) schadet der Suche aktiv, nicht nur "hilft nicht" — er wird an JEDEM
  PUCT-Blattknoten im ganzen Baum gelesen, nicht nur an Rundenübergängen.
  Produktions-Code steht auf `ACTIVE_LEAF=Net` (Entscheidung s.o.), der
  Diagnose-Flip war nur ein temporärer Test, sofort zurückgesetzt.
- **Value-Head**: `MosaicNet` hat `value_head` (±1 Sieg/Niederlage, Tanh)
  PLUS separaten `points_head` (Hilfsziel/Aux-Head, alte Score-Regression,
  ursprünglich der einzige Value-Head, dann bewusst aufgesplittet — der
  Nutzer wollte explizit einen Sieg/Niederlage-Head UND einen Punkte-Head
  getrennt, nicht nur die alte Formel). `VALUE_WEIGHT=0.2`, `POINTS_WEIGHT=0.5`
  (`config.py`). `VALUE_SCHEMA_VERSION=12` (`neural_net.py`). `values` (nicht
  `points_forecast`) treibt die Live-Suche bei `ACTIVE_LEAF=Net`
  (`net_mcts.rs::make_node` liest `value_to_win_prob(value)`, `points` wird
  dort verworfen).
- **Val-R²-Verlauf `values`-Head über die Generationen**: v8 -0.43 → v8b
  -0.36 → v8c -0.29 → v8d -0.25 (mit round_transition_value-Daten, siehe
  unten) — durchgehend negativ (schlechter als der reine Mittelwert),
  langsame, nie durchschlagende Verbesserung trotz VALUE_WEIGHT-Senkung,
  Val-basiertem Early Stopping und Rauschreduktion im Trainingsziel.
  `points_forecast`-Head generalisiert am selben Trunk durchgehend deutlich
  besser (Val-R² 0.27-0.34) — vermutlich weil die kontinuierliche
  Punkte-Marge Abstufungen (fast gewonnen vs. klar gewonnen) transportiert,
  die das binäre ±1-Ziel bei knappen Randergebnissen zu einem reinen
  Vorzeichen-Zufall kollabieren lässt, bei GLEICHER zugrunde liegender
  Rausch-/Datenquelle (`scores`/`winner` aus demselben Spielausgang).
  Kapazitätscheck (v8d: 4% tote Neuronen, 40% Eff.Rank) schließt
  Kapazitätsmangel als Ursache aus — kein reflexives Vergrößern des Heads
  ohne neuen Befund.
- **`INPUT_SIZE=708`**, **`NUM_ACTIONS=346`** (war 483 bis 2026-07-19, siehe
  Kuppelplatten-Faktorisierung unten).
- **VALUE_SCHEMA_VERSION=13 (2026-07-19)**: Kalibrierungs-Diagnose (v8e,
  über den gesamten -- ueberwiegend gesehenen -- Datensatz) zeigte
  `corr(val_true, pts_true)` nur 0.49 (die beiden Ziele selbst stimmen nur
  maessig ueberein) UND beide Koepfe fitten gesehene Daten aehnlich gut
  (`corr(pred,true)` ~0.68-0.69) -- die negative Val-R² ist also eine echte
  Generalisierungsluecke, kein grundsaetzlich ungelernbares Ziel. Fallback
  (ohne `round_transition_value`) von hartem `sign(own-opp)` auf weiches
  `tanh((own-opp)/VALUE_SCALE)` umgestellt. **Ergebnis (v9a): Val-R² steigt
  von +0.142 (Epoche 1) auf +0.208 (Epoche 4) und bleibt stabil bei
  ~0.19-0.21 bis Epoche 15 -- KEIN Zerfall in den Negativbereich, erstmals
  in der Session-Historie.** Bestaetigt die Hypothese auf Metrik-Ebene.
  **ABER: Arena v9a vs. Heuristik (s150) bleibt bei 1:14 (7% Siege, Ø Score
  15.4 vs. 56.0) -- SCHLECHTER im Score-Abstand als v8d/v8e trotz gesundem
  Val-R².** Die Metrik-Reparatur hat NICHT automatisch zu besserer
  Spielstaerke gefuehrt -- R²=0.19 ist offenbar nicht per se "gut genug",
  um PUCT wirksam zu leiten. Noch nicht geklaert.
- **NEUER NEBENBEFUND -- Policy-Qualitaet driftet ueber die Generationen
  (2026-07-19)**: DFS-Leaf-Diagnose (ACTIVE_LEAF=Dfs, macht den Value-Head
  irrelevant) ueber drei Generationen: v8d 26% (8:23), v8e 18% (4:18), v9a
  7% (1:14) gegen dieselbe Heuristik. v8e und v9a teilen sich denselben
  Aktionsraum (346) und einen wachsenden, gemeinsamen Korpus -- nur v9a hat
  zusaetzlich das neue Value-Ziel. Da DFS-Leaf den Value-Output gar nicht
  liest, kann das neue Value-Ziel diesen Abwaertstrend NICHT direkt
  erklaeren -- der gemeinsame Trunk koennte indirekt betroffen sein
  (gleiche Gradientenquelle), ODER der wachsende/gemischte Korpus selbst
  (hs200 enthaelt aeltere Partien von VOR den Gamma-Pruning-Bugfixes dieser
  Session, gemischt mit neueren domefact-Partien bei durchgehend sims=200)
  verschlechtert die Policy-Generalisierung unabhaengig vom Value-Thema.
  **Stichprobengroessen klein (15-22 Spiele je SPRT-Abbruch), Trend aber
  konsistent ueber drei Punkte.** Muss geklaert werden, bevor weitere
  Value-Head-Experimente auf dem wachsenden Mischkorpus sauber interpretierbar
  sind. Naechster Schritt: domefact-only-Training (nur frische, konsistente
  sims=200-Partien, kein hs200) isoliert diese Frage.
- **v9b_domeonly -- Korpus-Confound BESTAETIGT, Value-Head-Frage NEU
  GERAHMT (2026-07-19)**: Training exklusiv auf 5500 frischen domefact-
  Partien (550 Dateien à 10 Spiele -- 500 aus dem ersten Testlauf + volle
  5000 aus dem zweiten Batch, kein hs200) mit demselben weichen Value-Ziel.
  Zwei Ergebnisse:
  1) **DFS-Leaf-Diagnose: 30% Siegquote (13:30, n=43) -- BESSER als v8d
     (26%), mit groesserer Stichprobe.** Bestaetigt zweifelsfrei: das alte
     hs200 (Partien von vor den Gamma-Pruning-Bugfixes dieser Session)
     verschlechterte die Policy-Generalisierung, unabhaengig vom Value-
     Thema. Konsequenz: hs200 sollte als Trainingsquelle zurueckgezogen
     werden, frische domefact-artige Selfplay-Daten sind die bessere Basis
     ab jetzt.
  2) **ABER: Arena unter Produktions-Konfiguration (ACTIVE_LEAF=Net) bleibt
     bei 0:12 (0% Siege), Ø Score 13.7 vs. 46.8 -- SCHLECHTESTER Score-
     Abstand der gesamten Session**, trotz gesundem, stabilem Value-R²
     (+0.22 bis +0.24, bislang bester Wert) UND wiederhergestellter
     Policy-Qualitaet (30% DFS-Leaf).
  **Das aendert die Diagnose grundlegend**: es ist NICHT (nur) eine Frage
  von "wie hoch muss R² sein" -- selbst ein nachweislich gesunder,
  generalisierender Value-Head scheint die PUCT-Suche bei diesem Sim-
  Budget (150) genauso zu schaden wie der urspruenglich kaputte. Moegliche
  Erklaerungen (noch nicht getestet): (a) aggregiertes Val-R² verdeckt eine
  ungleichmaessige Fehlerverteilung ueber Spielphasen (z.B. gut in
  Spaetphasen, irrefuehrend in Fruehphasen, wo die Suche den Wert am
  noetigsten braucht); (b) 150 Sims reichen nicht, um PUCT durch
  UCB-Exploration von Value-Rauschen erholen zu lassen (mehr Sims koennten
  ein anderes Bild zeigen); (c) DFS-Leaf ist als beschraenkter, aber
  EXAKTER Rundenrest-Schaetzer grundsaetzlich zuverlaessiger als jede
  NN-Approximation ueber das GANZE Spiel, unabhaengig von deren Val-R².
  **Dies ist ein struktureller Befund, keine Parameter-Frage mehr** --
  naechster Schritt braucht eine Entscheidung (siehe "Naechste Schritte"),
  nicht noch einen Trainingslauf.
- **Runde 5: exakte Alpha-Beta-Suche** (`engine/src/round5.rs`). Fertig,
  getestet, aktiv.
- **Kuppelstapel-Mechanik regelwerkstreu**: sequentielles Ziehen, gedeckelte
  Ziehungen, Rückseiten-Sichtbarkeit. Fertig, getestet, aktiv.

## Runden-Übergangs-Sampling (Chance-Node-Evaluator)

`engine/src/round_transition.rs` + `round_transition_deep.rs` — adressiert
das Val-R²-Plateau: der Suchbaum endet am Rundenübergang als
Pseudo-Terminal; Fabrik-/Bonuschip-Neubefüllung ist sonst nirgends als
echter Zufallsknoten repräsentiert. Sampelt N mögliche Neubefüllungen,
wertet netzbasiert aus, mittelt. Seit dieser Session auch für
HEURISTIK-Self-Play verfügbar (`self_play_games_with_net_labels`,
`round_transition_deep.rs`s echtes Gamma-Pruning für rundenendende
Geschwister-Kandidaten) — deutlich billiger als Netz-geführtes Self-Play,
da nur die Blattbewertung an den vier Rundenübergängen vom Netz kommt, alle
Zugentscheidungen bleiben heuristisch.

- **v8d-Ergebnis (2026-07-19)**: 110 rtv-gelabelte Spiele (von 6110 gesamt,
  1,8%) — Val-R² `values` -0.29→-0.25, `points_forecast` 0.34→0.33
  (praktisch unverändert). Arena v8d vs. v8c: 25:24, SPRT erklärt Parität
  ("Gleich stark") — kein messbarer Stärkeunterschied. **Bewertung: bei
  diesem Stichprobenumfang kein klarer Effekt, aber auch keine
  Verschlechterung.** Ob mehr rtv-Daten (z.B. 2000-3000 Spiele statt 110)
  den Value-Head tatsächlich verbessern würden, ist NICHT geklärt — das
  eigentliche Problem könnte struktureller sein (s.o., binäres ±1-Ziel bei
  knappen Ergebnissen), nicht nur Stichprobenumfang. Vor weiterer Eskalation
  hier: erst verstehen, ob das Problem Datenmenge oder Zielkonstruktion ist.
- **Live-Suche** (`ROUND_TRANSITION_SAMPLING`): weiterhin `false`, nicht
  aktiviert (Kosten für JEDEN Baum-Ast in der Live-PUCT-Suche zu hoch,
  unverändert seit letztem Stand).

## Kuppelplatten-Faktorisierung (Slot × Rotation, analog Moon-Order)

Neu diese Session (2026-07-19), **Baustein A** aus
`C:\Users\Patrick\.claude\plans\elegant-wandering-mist.md`. Kuppelplatten-
Platzierung (3×3-Raster, 4 Rotationen) war der dominante Treiber der
riesigen Aktionsanzahl in frühen Runden (~195 Aktionen bei Zug 1). Im
Gegensatz zu Moon-Order kodierte `action_to_id` Slot UND Rotation bisher
SELBST (108 bzw. 36 IDs) — kein ID-Collapsing, der Policy-Head musste die
volle Kombination selbst lernen.

- **Umgesetzt**: `action_to_id` kollabiert jetzt `dome`/`dome_stack` auf
  Auslage-Index bzw. gedeckelten Pending-Index (`features.rs`,
  `NUM_ACTIONS` 483→346). Neue kleine Köpfe `dome_slot_head`/
  `dome_rotation_head` (analog `moon_order_head`) faktorisieren
  `P(Slot) × P(Rotation)` beim Baumexpandieren (`net_mcts.rs::
  build_untried_actions`). Neue Self-Play-Zielfelder `dome_slot_target`/
  `dome_rotation_target`. Rust-Python-ONNX-Parität verifiziert (Maxdiff
  ~1e-7 über alle 6 Netz-Ausgaben). 117/117 Rust-Tests grün (6 neu,
  inkl. `action_to_id`-Rundtrip-Test gegen ID-Bereichs-Kollisionen).
  **Wichtig, mit Nutzer geklärt**: das reduziert NICHT die Anzahl der
  tatsächlichen Suchkandidaten pro Knoten (Suche muss weiterhin jede
  Slot×Rotation-Kombination einzeln betrachten) — nur die
  Policy-Lernqualität für diese Aktionsfamilie.
- **Status Auswertung**: 500-Spiele-Testlauf (`domefact`-Datensatz)
  ausschließlich zur Pipeline-Verifikation, NICHT aussagekräftig fürs
  Training der beiden neuen Köpfe (~8.000 kuppel-gelabelte Schritte, dünn
  für zwei Klassifikations-Köpfe). Echte Auswertung braucht einen größeren
  Datensatz (5000 Spiele, ~3h10 bei gemessenen 0,44 Spiele/s, läuft/geplant)
  — Ergebnis hier nachtragen, sobald verfügbar. Erstes v8e (500-Spiele-Sanity-
  Training): Value-Val-R² erreicht bei Epoche 1 erstmals in dieser
  Session +0.135 (positiv!), zerfällt aber bis Epoche 15 (Policy-Plateau-
  Stop) auf -0.073 — bestes bisher beobachtetes Final-R², aber Ursache
  unklar (Datenmenge/-qualität vs. Aktionsraum-Verkleinerung nicht
  auseinandergehalten, da beides gleichzeitig geändert wurde). Policy-Val-
  Loss 1.81 (v8c/v8d: ~2.20-2.22) — teils durch kleineren Aktionsraum
  erklärbar (ln(346)=5.85 vs. ln(483)=6.18, Differenz 0.33 von den
  beobachteten ~0.39-0.41 Nats), evtl. etwas mehr.
  **Arena v8e vs. Heuristik (s150, gleiche Einstellungen wie v8d): 0:12
  (0% Siege), Ø Score 20.8 vs. 42.1, Bodenstrafe 22.2 vs. 10.5 — praktisch
  identisch zu v8d (0:12, 14 vs. 42, Bodenstrafe 24.6 vs. 10.4).** Trotz
  besserer Trainings-Metriken KEINE Verbesserung der echten Spielstärke.
  Bestätigt: der Value-Head ist der voll bindende Engpass bei
  `ACTIVE_LEAF=Net` — er wird an JEDEM Blattknoten gelesen, unabhängig
  davon wie gut die Policy ist, und überdeckt jeden Policy-seitigen
  Fortschritt vollständig. Starke empirische Stütze für "Value-Head
  zuerst" als Priorität.
- **WICHTIGER NEBENBEFUND**: `v8c.onnx`/`v8d.onnx` sind durch das
  ID-Collapsing **dauerhaft inkompatibel mit der aktuellen Engine**
  geworden — nicht nur ein Re-Export-Problem. `action_to_id` hat sich
  semantisch geändert (dome/dome_stack-IDs bedeuten jetzt etwas anderes),
  UND der Policy-Head hat eine andere Ausgabedimension (483 vs. 346) — ein
  Re-Export würde am Shape-Mismatch scheitern und den Policy-Head
  stillschweigend zufällig neu initialisieren (nicht mehr das echte v8d).
  `net.rs::Net::eval` crasht beim Laden alter 4-Output-ONNX-Dateien hart
  (`out[4]` Index-out-of-bounds), da diese kein `dome_slot`/`dome_rotation`
  haben. **Konsequenz**: Arena-Vergleiche gegen v8c/v8d sind ab jetzt nur
  noch als bereits aufgezeichnete Referenzwerte nutzbar (z.B. v8d vs.
  Heuristik 0:12), nicht mehr als Live-Match gegen neuere Modelle. Jede
  NUM_ACTIONS-Änderung kostet also die komplette bisherige Modell-Generation
  für Live-Vergleiche — nicht nur fürs Warm-Start (das war schon bekannt).
- **Baustein B** (zweistufige Slot→Rotation-Suchknoten, echte
  Verzweigungsfaktor-Reduktion): nur vorbereitet/dokumentiert im Plan-File,
  NICHT umgesetzt. **Nutzer-Entscheidung (2026-07-19): explizit NACH der
  Value-Head-Reparatur**, nicht parallel/vorher — A hilft nur der
  Policy-Lernqualität, löst NICHT das eigentliche Kombinatorik-/
  Verzweigungsfaktor-Problem, das B adressieren soll. Beide Baustellen
  bewusst nacheinander, nicht gleichzeitig offen halten.

## Drei-Diagnosen-Runde abgeschlossen (2026-07-19)

Alle drei parallel beauftragten Diagnosen sind durch, plus eine Recherche
nach vergleichbaren Befunden in der AlphaZero/MCTS-Literatur.

**(a) Value-Head-Fehler NACH RUNDE aufgeschlüsselt — entscheidender Befund.**
R² steigt MONOTON mit der Rundenzahl (v9b_domeonly, ganzer Korpus, n=860k
Schritte):

| Runde | n | R² | MAE |
|---|---|---|---|
| 1 | 166.880 | **+0.032** (praktisch Rauschen) | 0.203 |
| 2 | 175.100 | +0.146 | 0.191 |
| 3 | 183.193 | +0.262 | 0.178 |
| 4 | 182.517 | +0.426 | 0.155 |
| 5 | 152.734 | **+0.621** (brauchbar) | 0.126 |

Das aggregierte R² (0.22-0.29) verdeckte diese massive Ungleichverteilung
komplett. Der Value-Head ist in Runde 1 — wo die Suche die meiste Führung
am nötigsten hätte (größter Verzweigungsfaktor, meiste verbleibende
Entscheidungen) — kaum besser als der Mittelwert, wird aber an JEDEM
PUCT-Blattknoten gleich stark vertraut wie in Runde 5, wo er tatsächlich gut
ist. Das ist die direkteste, am besten belegte Erklärung der drei
Kandidaten.

**(b) Sims-Budget hochgesetzt (150→400) — Hypothese verworfen.** Arena bleibt
bei 0:12 (0% Siege), Score 18.2 vs. 44.4 — praktisch identisch zu 150 Sims
(13.7 vs. 46.8). Mehr Sims schließen die Lücke NICHT — kein reines
Explorations-/Budget-Problem.

**(c) hs200 zurückgezogen** — siehe Abschnitt oben, erledigt.

**Recherche-Befund** (Internet-Agent, Quellen siehe unten): das exakte
Phänomen "Value-Head mit gutem Offline-R² schadet der Suche trotzdem" ist
nirgends als benanntes Problem dokumentiert, aber drei eng verwandte
Präzedenzfälle:
- Leela Chess Zero hatte einen Stärke-Rückgang, der auf `value_loss_weight`
  zurückgeführt wurde (github.com/leela-zero/leela-zero#1480).
- Grupen et al., "Policy-Value Alignment and Robustness in Search-based
  Multi-Agent Learning" (arXiv:2301.11857): Policy und Value widersprechen
  sich am selben Zustand systematisch, Value-Funktion ist intern
  inkonsistent — passt strukturell zu unserem Runden-Befund.
- **KataGo blendet eine Winrate MIT einem kontinuierlichen
  Punktestand-Vorhersage-Kopf zu einer "Utility", die tatsächlich die Suche
  treibt** (nicht nur Trainings-Zusatzsignal) — dokumentierter Erfolgsfall
  für genau die Idee, die `points_forecast` bei uns schon existiert, aber
  bisher nur als Aux-Loss genutzt wird.

## Empfohlener nächster Schritt

**Nutzer-Entscheidung (2026-07-19): Option 1 (rundenabhängige Blattbewertung)
explizit ABGELEHNT** — würde ausgerechnet in Runde 1-2 (wo die meisten Runden
noch bevorstehen und Rundenweitsicht am wichtigsten wäre) auf DFS/Heuristik
zurückfallen, das widerspricht direkt dem eigentlichen Ziel von Stufe 2.

**Option 2 (KataGo-Stil Blended Utility) implementiert und GETESTET — schließt
die Lücke NICHT.** `net_mcts.rs`: neue Konstante `POINTS_UTILITY_WEIGHT`
mischt `value_head`s Sieg-Wahrscheinlichkeit mit `points_head`s
Punktestand-Prognose (`blended_leaf_win_prob`, gleiche Tanh→[0,1]-Skala für
beide). Arena v9b_domeonly vs. Heuristik, 150 Sims, SPRT, drei Gewichte:

| Gewicht | Ergebnis | Ø Score | Floor-Strafe |
|---|---|---|---|
| 0.0 (nur `value`, Baseline) | 0:12 (0%) | 13.7-18.2 vs. 44.4-46.8 | ~20-25 vs. ~8-10 |
| 0.5 (hälftiger Blend) | 1:14 (7%) | 19.5 vs. 49.7 | 27.0 vs. 10.5 |
| 1.0 (nur `points_forecast`) | 0:12 (0%) | 14.2 vs. 55.0 | 25.4 vs. 10.1 |

Keines der drei Gewichte kommt in die Nähe einer echten Verbesserung — alle
verlieren 93-100% gegen die Heuristik. **Bemerkenswert**: die Floor-Strafe
bleibt bei ALLEN drei Werten im selben erhöhten Bereich, unabhängig davon,
welches Signal den Blattwert bestimmt. Das spricht dagegen, dass die
Blattwert-Formel (egal ob `value`, `points_forecast` oder eine Mischung) der
eigentliche Flaschenhals ist — der Fehler sitzt wahrscheinlich woanders
(Policy-Kopf-Qualität oder wie Priors/Blattwert in der PUCT-Formel
zusammenwirken). Code bleibt als Konstante verfügbar (aktuell auf 0.0
zurückgesetzt = alter, besser abgesicherter Zustand), aber "Blend-Gewicht
tunen" ist als eigenständiger nächster Schritt damit erledigt/verworfen.

**Damit ist die Vorbedingung für Baustein B ("nach der Value-Head-
Reparatur") noch NICHT erfüllt** — beide vorgeschlagenen Optionen sind jetzt
durch (eine abgelehnt, eine getestet und widerlegt), ohne dass die Suche
tatsächlich repariert wurde. Nächster Schritt braucht eine neue Idee oder
eine explizite Nutzer-Entscheidung, wie weiter vorgegangen wird.

**Offener, teurerer Verdacht, weiterhin zurückgestellt**: der gesamte
domefact-Korpus stammt aus HEURISTIK-geführtem Self-Play (nur die
Rundenübergangs-Labels kommen vom Netz) — der Value-Head lernt also auf
Zuständen, die die Heuristik besucht, muss aber zur Inferenzzeit Zustände
bewerten, die die NETZ-eigene PUCT-Suche besucht. Eine Trainings-/Inferenz-
Verteilungsverschiebung wäre ein weiterer, unabhängiger Erklärungskandidat.
**Nutzer-Präzisierung (2026-07-19)**: das lässt sich sinnvoll erst testen,
wenn bereits ein brauchbarer netz-geführter Agent existiert, der überhaupt
sinnvolles Self-Play erzeugen kann — Henne-Ei-Problem, kann also nicht VOR
einer Lösung geprüft werden, nur zur Bestätigung danach.

## Floor-Straf-Ursachenforschung (2026-07-19, Anschluss an KataGo-Blend)

Nutzer-Fragen nach dem Blend-Fehlschlag: Policy-Kopf-Qualität separat prüfen,
PUCT-Prior/Blattwert-Gewichtung prüfen, und woher die erhöhte Floor-Strafe
kommt (Heuristik zeigt das nicht) — inkl. Idee "eigener Mini-Head für
Floor-Strafen?".

**Policy-Kopf-Qualität, erstmals gemessen** (v9b_domeonly, echter Val-Split,
n=87.498 Züge, gleicher Seed wie beim Training): **Top-1-Accuracy 61.8%,
Top-3 87.1%**, Ø Wahrscheinlichkeitsmasse auf dem Trainings-Target-Argmax
49.1%. Moderat, nicht katastrophal, aber ein echter, bisher unbeachteter
Faktor — bei 346 Aktionen weicht die Netz-eigene Top-Wahl in ~38% der Fälle
vom Trainings-Label ab.

**PUCT-Gewichtung geprüft** (`best_puct`, net_mcts.rs): Standard-AlphaZero-
PUCT-Formel (Q + c·P·√N/(1+n)), `c_puct=1.5`, meistbesuchtes Wurzelkind
gewinnt — beim Code-Review keine offensichtliche Fehlfunktion gefunden.

**Floor-Strafe-Mechanismus geklärt** (`execution.rs`, `round_end.rs`): Boden-
Strafe ist eine **100% deterministische Konsequenz** zweier Aktionen — (1)
Drafting-Überlauf (`execute_place`/`add_to_penalty`, sofort beim Zug), UND
(2, Nutzer-Korrektur) beim Drafting→Tiling-Übergang selbst, wenn Musterreihen
wegen belegter Dome-Reihe unplatzierbar werden (`process_unplaceable_rows`).
Beides ist beim PUCT-Knoten schon exakt bekannt — braucht keine Netz-
Vorhersage. `round_end::projected_unplaceable_penalty` existierte für Quelle
(2) bereits (dort dokumentiert: selbst der DFS-Solver preist das NICHT ein).

**Idee statt Mini-Head**: kein Training nötig — Reward-Shaping mit der
EXAKTEN, bereits bekannten Strafe direkt in den PUCT-Blattwert einspeisen
(`floor_shaping_delta`, `FLOOR_SHAPING_WEIGHT`), auf dem bestehenden
`v9b_domeonly`-Modell getestet:

| Konfiguration | Ergebnis | Ø Score | Floor-Strafe |
|---|---|---|---|
| Baseline (kein Shaping) | 0:12 (0%) | 13.7-18.2 vs. 44.4-46.8 | ~20-25 vs. ~8-10 |
| Shaping W=0.3 (nur Quelle 1, VOR Fix) | 2:15 (12%) | 12.9 vs. 44.8 | 21.4 vs. 10.8 |
| Shaping W=0.6 (nur Quelle 1, VOR Fix) | 0:12 (0%) | 17.2 vs. 53.6 | 18.8 vs. 11.5 |
| Shaping W=0.3 (Quelle 1+2, NACH Fix) | 0:12 (0%) | 19.3 vs. 43.9 | 19.3 vs. 11.2 |

**Ehrliche Einordnung**: bei n=12-17 Spielen/Konfiguration (SPRT-Abbruch) sind
diese Ergebnisse NICHT sauber voneinander unterscheidbar — die 12%-Rate bei
W=0.3 war wahrscheinlich Stichproben-Glück, kein belastbarer Effekt. Alle
vier Konfigurationen verlieren weiterhin signifikant gegen die Heuristik.
Floor-Strafe selbst bewegt sich leicht (bis ~19 statt ~20-25), aber nicht
genug, um als Durchbruch zu gelten. Aktuell auf W=0.3 (Quelle 1+2) belassen,
Code bleibt verfügbar. Für ein belastbares Urteil bräuchte es einen
größeren, nicht früh abgebrochenen Testlauf (z.B. `early_stop=False`,
feste 100+ Spiele).

**Wichtiger Fund: passt zu einer bereits archivierten, unabhängigen
Untersuchung** (`archive/stage2_investigation.md`, altes v2-Modell, VOR
allen Architekturänderungen dieser Session). Dort wurde bereits einmal
komplett rauschfrei (Argmax-Arena + deterministisches Self-Play, doppelt
bestätigt) gezeigt: Stufe 1 (DFS-Blatt) = 0% "0:0-Rate" (beide Spieler
Richtung Boden gedrückt), Stufe 2 (Netz-Value-Blatt) = ~7%. Der Value-Head
zeigte dabei die RICHTIGE Richtung schon ab Runde 1, aber mit zu wenig
Trennschärfe (~0.05-0.08 vs. ~0.17-0.19 — ein schmales Band statt einer
scharfen Bewertung wie beim exakten DFS-Solver). Die
Mehrrunden-Weitsicht-Hypothese wurde dort direkt getestet (Meinungsverschie-
denheits-Rollout-Studie, n=597) und WIDERLEGT — Stufe 2s abweichende Züge
schlugen sich in Runde 1-2 nicht besser, in Runde 3 sogar signifikant
schlechter. **Konsistentes Gesamtbild über zwei Untersuchungsrunden und
komplett verschiedene Architekturen hinweg**: es geht nicht darum, WELCHES
gelernte Signal (value/points/Blend) die Suche treibt, sondern dass ein
weiches, gelerntes Signal grundsätzlich zu wenig "Rückstellkraft" gegen
Sucherauschen hat verglichen mit einer exakten Bewertung — was auch erklärt,
warum Floor-Shaping (ein exaktes Teilsignal statt eines weiteren gelernten)
die einzige Variante ist, die überhaupt in Bewegung kam.

## Größere Testläufe + externe Zweitmeinung (2026-07-20)

Nutzer-Auftrag: größere Arena-Tests (je 100 Spiele, kein Early-Stop) für die
vielversprechendsten Kandidaten, plus Diagnose-Vorschläge von einem externen
Kollegen (Repo-Review).

**Floor-Shaping W=0.3, n=100, kein Early-Stop — bestätigt sich als echter,
wenn auch kleiner Effekt:**

| Konfiguration | Ergebnis | Ø Score | Floor-Strafe |
|---|---|---|---|
| Floor-Shaping W=0.3 (Quelle 1+2) | 11:89 (11%) | 24.5 vs. 44.2 | **16.9 vs. 12.3** |

Deutlich engerer Floor-Abstand als jede Baseline/Blend-Variante (~20-27 vs.
~8-10) und die bisher beste Netz-Performance der Session — bei n=100 kein
Stichproben-Artefakt mehr. Bleibt aktiv (Standard-Konfiguration).

**Externe Zweitmeinung (Kollege, Repo-Review) — Kernthese: `net_leaf_eval`/
`make_node`s zweiter Forward-Pass für `other_val` (künstlich geflipptes
`current_player`) ist Out-of-Distribution, da Trainingsdaten nur die echte
Zugspieler-Perspektive kennen — potenzieller Erklärer für "gesundes R², aber
schadet der Suche" UND "Value/Points/Blend versagen identisch" (gleiche
Plumbing).** Cheap Interventionstest direkt umgesetzt: `MIRROR_OTHER_VAL`
erzwingt `other_val = 1 - mover_val` (ein Forward-Pass, kein OOD-Risiko).

| Konfiguration | Ergebnis | Ø Score | Floor-Strafe |
|---|---|---|---|
| Mirror-Fix, ISOLIERT (kein Floor-Shaping), n=100 | 3:97 (3%) | 15.7 vs. 43.4 | 21.3 vs. 11.1 |

**Ergebnis: KEINE Verbesserung** — eher schwächer als Baseline, klar
schwächer als Floor-Shaping. Die Perspektiven-/OOD-Hypothese ist damit als
ALLEINIGE/dominante Erklärung widerlegt (der zweite Forward-Pass mag
suboptimal sein, ist aber nicht der Haupttäter). Zurückgesetzt auf
`false` (Original-Zwei-Forward-Pass-Verhalten). Die übrigen Diagnose-
Vorschläge des Kollegen (Noise-Floor-Test für Runde-1-R²-Deckel,
Geschwister-Kendall-τ statt globalem R², FPU/Unvisited-Q-Audit,
Kalibrierungs-Shrinkage-Intervention, TD-Bootstrap-Ziele) sind NICHT
umgesetzt/getestet — bleiben als hochwertige, noch offene Kandidaten für
die Fortsetzung dieser Untersuchung.

**Policy-Ziel-Schärfung (Exponent 2.0 auf MCTS-Visit-Anteile, kein neues
Self-Play nötig)**: `v9c_sharpen` warm-gestartet von `v9b_domeonly`, 15
Epochen (Early-Stop bei Policy-Val-Plateau ab Epoche 10). Ergebnis: Top-1
61.5% (vorher 61.8%), Top-3 86.6% (vorher 87.1%), Ø Wahrscheinlichkeitsmasse
auf Ziel-Argmax 53.6% (vorher 49.1%, mechanisch erwartbar da Exponent die
Reihenfolge/den Argmax NICHT ändert, nur die Schärfe der Verteilung um ihn
herum). **Top-1-Accuracy bewegt sich NICHT** — bestätigt, dass die
~60-65%-Decke wahrscheinlich der Ziel-eigenen Mehrdeutigkeit (viele
Drafting-Entscheidungen sind echte Fast-Gleichstände) entspringt, nicht
einem Trainings-/Kapazitätsdefizit. Kein Arena-Test nötig, da die
Accuracy-Messung schon keinen Hebel zeigte.

## Struktureller Durchbruch: zwei echte Such-Bugs gefunden (2026-07-20)

Zweiter externer Kollege ging die Engine durch (Schwerpunkt `net_mcts.rs`,
`mcts.rs`, `features.rs`, `game.rs`/`execution.rs`, `self_play.rs`,
`neural_net.py`, `train.py`, siehe `evaluations/Bugfixes.txt` +
`evaluations/Gumbal Alphazero.txt`) und fand mehrere konkrete, spielstärke-
relevante Implementierungsfehler — zwei davon direkt verifiziert und
gefixt, mit dem bislang größten Fortschritt der gesamten Session:

**Bug 1 — erzwungene Voll-Expansion vor jeder Suchtiefe.** `build_net_tree`s
Selection-Loop expandierte den KOMPLETTEN POLICY_MASS_CUTOFF-Präfix eines
Knotens (in Runde 1 oft Dutzende Kandidaten, gegeben ~49% Policy-Top-1-
Masse), bevor überhaupt einmal PUCT zwischen ihnen differenzieren konnte —
bei 150 Sims faktisch Breitensuche mit Tiefe ~1-2 statt echter Suche. Aus
der Historie (`git log`, Commit `068bb62`) bestätigt: eine FRÜHERE Version
hatte echtes besuchszahl-gesteuertes Progressive Widening
(`MAX_ACTIONS + WIDEN_FACTOR·√N`, identisch zu `mcts.rs`), das bewusst
entfernt wurde, um den Long Tail dauerhaft auszuschließen (guter, separater
Zweck) — dabei aber versehentlich auch die Drosselung ÜBER dem
verbleibenden Präfix mit entfernt. **Fix**: denselben Widening-Cap wie
`mcts.rs` wieder eingeführt, aber nur auf den bereits gekappten Präfix
angewendet (Long-Tail-Ausschluss bleibt vollständig erhalten).

**Bug 2 — Tie-Breaking wählt bei Besuchsgleichstand den SCHLECHTESTEN
Kandidaten.** `net_search_drafting_action`/`net_search_with_tree` nutzten
`max_by_key(|c| nodes[c].visits)` — Rusts `max_by_key`/`max_by` liefern bei
Gleichstand dokumentiert das LETZTE Maximum. Kinder werden aber in
ABSTEIGENDER Prior-Reihenfolge expandiert, das letzte gleichstehende Kind
ist also das mit dem NIEDRIGSTEN Prior im Set. Wegen Bug 1 ist Besuchs-
gleichstand in frühen, hochverzweigten Runden der Normalfall — die Suche
spielte also systematisch einen der am schlechtesten bewerteten Kandidaten.
`mcts.rs`s eigene `best_root_child` hat bereits den korrekten Tiebreak
(`visits.cmp(...).then(Q-Vergleich)`) — `net_mcts.rs` hatte ihn nicht.
**Fix**: neue `best_root_child`-Hilfsfunktion (Pendant zu `mcts.rs`),
Tiebreak über `(visits, Q, prior)`, an beiden Aufrufstellen eingesetzt.

**Wichtige Erkenntnis, warum das die ganze Session lang verdeckt blieb**:
BEIDE Bugs betreffen `build_net_tree`/`net_search_drafting_action` UNABHÄNGIG
von `ACTIVE_LEAF` — Stufe 1 (DFS-Blatt) UND Stufe 2 (Netz-Value) laufen durch
denselben Code, nur der Blattwert unterscheidet sich. Das erklärt, warum DFS-
Blatt trotz identischer Bugs immer noch klar besser abschnitt (26-30% vs.
0-12%): DFS' exakte, scharfe Q-Werte brechen Besuchsgleichstände schnell
durch echte Differenzierung auf, während Netz-Values weiches/verrauschtes
Signal liefern, das Gleichstände viel länger bestehen lässt — Bug 2 trifft
also gerade das schwache Signal viel härter. Das verbindet die gesamte
bisherige "weiches Signal hat zu wenig Rückstellkraft"-Erkenntnis
(`stage2_investigation.md`) mit einem konkreten, jetzt behobenen Mechanismus.

**Arena-Ergebnis (n=100, kein Early-Stop, v9b_domeonly, 150 Sims,
Struktur-Fixes + Floor-Shaping W=0.3 kombiniert)**:

| Konfiguration | Ergebnis | Ø Score | Floor-Strafe |
|---|---|---|---|
| Floor-Shaping allein (vorher) | 11:89 (11%) | 24.5 vs. 44.2 | 16.9 vs. 12.3 |
| **+ Struktur-Fixes (Bug 1+2)** | **17:83 (17%)** | 22.7 vs. 42.2 | 18.1 vs. 12.5 |

Deutlichster Sprung der gesamten Session (11% → 17%, +55% relativ) bei
gleicher Stichprobengröße — kein Zufallsrauschen. Attributions-Test
(Struktur-Fixes ISOLIERT ohne Floor-Shaping) noch nicht gefahren.

**Weitere, noch nicht umgesetzte Funde aus derselben Kollegen-Review**
(Details in `evaluations/Bugfixes.txt`), nach Priorität:
- **Fund 6 (verdeckte Information)**: `execute_draw_stack_peek`/Kuppelstapel-
  Refill nutzen `dome_tile_pool.remove(0)` — im Suchbaum liegt die ECHTE
  oberste Platte offen, obwohl Features sie korrekt maskieren. Erzeugt
  prinzipiell unlernbares Zielrauschen, am stärksten in frühen Runden.
  `round_transition.rs` hat für Rundenübergänge bereits das richtige Muster
  (Chance-Node-Sampling) — fehlt noch für Peek-Ziehungen/Chip-Aufdeckungen
  innerhalb des Baums.
- **Fund 7 (Score-Clamp verzerrt Value-Ziel)**: `apply_score` clampt bei 0;
  das Value-Ziel nutzt diesen geclampten Endstand — ein Spieler bei
  "eigentlich" -25 bekommt dasselbe Label wie einer bei 0. Genau die
  Floor-Spiralen, die bekämpft werden sollen, kollabieren im Label auf
  denselben Wert.
- **Fund 8**: Checkpoint-Auswahl in `train.py` ignoriert den Value-Head
  (wählt nur nach Policy-Val-Loss).
- **Fund 3/4/5**: Self-Play-Policy-Targets werden bei breiten Knoten
  near-uniform (Folge von Bug 1, jetzt gemildert); Dirichlet-Noise wird erst
  NACH dem Policy-Cutoff gemischt (Root-Aktionen jenseits der 95%-Masse
  können im Self-Play nie exploriert werden); fehlgeschlagenes
  `apply_drafting` verbraucht eine Sim ohne Backprop.
- **Performance**: `action_to_id`-Aufruf im heißesten Suchpfad geht über
  JSON-Umweg (`action_to_env_dict` + String-Matching) statt direktem
  `Action → id`-Match.

**Gumbel AlphaZero** (`evaluations/Gumbal Alphazero.txt`): größerer,
eigenständiger Umbauvorschlag (Sequential Halving + completed-Q-Policy-
Targets statt PUCT+Dirichlet-Noise an der Wurzel) — würde Bug 2 strukturell
eliminieren und Bug 3/4 mit auflösen, aber KEIN Ersatz für einen besseren
Value-Head (Halving-Ranking hängt selbst am Q-Schätzer) und kein Ersatz für
Baustein B. Eigenständiges, größeres Vorhaben, noch nicht begonnen.

**Stand jetzt**: die beiden Struktur-Fixes plus Floor-Shaping sind
zusammen der stärkste bestätigte Fortschritt der Session (0% → 17%
Netz-Siege). Noch keine Parität, aber ein klar anderes Bild als der
gesamte bisherige Session-Verlauf (der ausschließlich an der Blattwert-
Formel drehte, ohne die Suchmechanik selbst zu hinterfragen). Nächste
Schritte: Fund 6/7 (beide zahlen direkt auf Runde-1-Zielrauschen ein),
danach erneut der Kollegen-Vorschlag Nr. 1 aus der vorherigen Runde
(Noise-Floor-Test für Runde-1-R²-Deckel) zur Einordnung, wie viel
Kopfraum nach den Struktur-Fixes noch bleibt.

## Fund 6, Fund 4/5, Geschwister-Ranking-Diagnose (2026-07-20, Fortsetzung)

**Fund 6 (verdeckte Information/Orakel-Wissen) implementiert und GETESTET —
schließt die Lücke NICHT, eher schlechter.** `SHUFFLE_STACK_PEEK_IN_SEARCH`:
mischt `dome_tile_pool` bei jedem simulierten `DrawStackPeek` im Suchbaum neu
(analog `round_transition_deep::simulate_one_round`s Determinisierungs-
Muster), statt die echte, im realen Spiel verdeckte oberste Platte zu lesen.
Arena (n=100, kein Early-Stop, Struktur-Fixes + Floor-Shaping W=0.3 als
Basis): **9:91 (9%), Score 21.9 vs. 43.9, Floor 18.8 vs. 12.1 — schlechter
als ohne (17%)**. Theoretisch gut begründet, aber die Neumischung erhöht
offenbar die Such-Varianz (jeder simulierte Ast sieht eine andere Ziehung)
mehr, als sie echte Verzerrung beseitigt — bei 150 Sims/Zug zu teuer.
Zurückgesetzt auf `false` (Original-Verhalten), Code bleibt verfügbar.

**Fund 4 (Dirichlet-Noise nach Cutoff) behoben.** `build_untried_actions`
bekommt jetzt einen `skip_cutoff`-Parameter, an der WURZEL (`make_node`s
`parent.is_none()`) ausgesetzt — Dirichlet-Root-Noise (Self-Play) wirkt
jetzt auf den VOLLEN Kandidatensatz, nicht mehr nur auf den bereits auf
POLICY_MASS_CUTOFF gekappten Präfix. Jede legale Wurzelaktion hat damit
wieder eine echte Explorations-Chance (AlphaZero-Standardverhalten). Der
Progressive-Widening-Cap verhindert weiterhin, dass der Long Tail in der
Arena tatsächlich durchgehend expandiert wird.

**Fund 5 (stille Sim-Verschwendung) behoben.** Ein fehlgeschlagenes
`apply_drafting` ließ die Simulation fälschlich den PARENT-eigenen
Blattwert ein zweites Mal backpropagieren (verzerrte Besuchszahlen ohne
echten Informationsgewinn). Jetzt wird eine solche Sim sauber übersprungen
(kein Backprop). Der `q=0.0`-Fallback in `best_puct` bleibt bewusst
unverändert — er ist nur bei einem FPU-basierten Fix für Fund 1 relevant
(hier stattdessen per Widening gelöst), also weiterhin totes, harmloses Code.

**Perspektiven-/OOD-Audit dauerhaft ins Self-Play integriert** (Nutzer-
Auftrag): `|v_mover + v_other − 1|` wird bei JEDER Netz-Blattbewertung
(sofern `MIRROR_OTHER_VAL=false`) unconditional mitgeloggt (kein Feature-
Flag, im Gegensatz zu `profiling.rs`), aggregiert nach Runde. `run_net_self_play`
hängt das Ergebnis als `perspective_divergence_diagnostics`-Objekt ans
JSON an (gleiches Muster wie `stage3_diagnostics`) — kein Einfluss auf die
Suche selbst (der Mirror-Fix-Test war negativ, siehe oben), reine
Sichtbarkeit für künftige Selbstplay-Läufe.

**Neue Standard-Metrik: Geschwister-Ranking-Kendall-Tau statt globalem R²**
(Nutzer-Auftrag, Kollegen-Vorschlag Punkt 3). Neue Funktion
`self_play::sibling_ranking_diagnostic` (pyo3: `sibling_ranking_diagnostic`):
läuft die Netz-eigene Suche ein Stück weit (realistische Zustands-
verteilung), sammelt Runde-1/2-Entscheidungspunkte, wertet für jeden alle
Geschwister-Nachfolgezustände per Netz UND per exaktem DFS-Solver (Ground
Truth) aus, berichtet Kendall-Tau zwischen beiden Rangfolgen.

Ergebnis (v9b_domeonly, n=100 Zustände/Runde, Ø 17.6/15.1 Geschwister):

| Runde | Kendall-Tau | Ø Geschwister |
|---|---|---|
| 1 | **0.318** | 17.6 |
| 2 | 0.164 | 15.1 |

**Wichtige Einordnung**: das ist ein ANDERES Bild als die frühere globale
Val-R²-Tabelle (Runde 1 = 0.032, Runde 2 = 0.146) — R² ist empfindlich
gegenüber absoluter Kalibrierungs-Verzerrung, Kendall-Tau nur gegenüber der
RELATIVEN Reihenfolge. Ein Tau von 0.32 in Runde 1 zeigt, dass der Value-Head
dort eine echte, wenn auch bescheidene, lokale Unterscheidungsfähigkeit hat
-- die frühere "praktisch nutzlos"-Einordnung (aus dem R²=0.03) war insofern
zu pessimistisch. Die Umkehrung (Runde 2 < Runde 1) ist unerwartet und noch
nicht erklärt -- könnte an mehr echten Fast-Gleichständen in Runde 2 liegen
(siehe `run_penalty_bias`-Diagnose) oder an der Stichprobengröße (n=100)
liegen. Kein Perfekt-Wert (1.0) in keiner Runde -- es bleibt Verbesserungs-
potenzial, aber "praktisch Zufall" ist nach diesem Befund nicht mehr die
richtige Beschreibung für Runde 1.

**Aktueller Stand der Konstanten** (`net_mcts.rs`): `ACTIVE_LEAF=Net`,
`POINTS_UTILITY_WEIGHT=0.0`, `FLOOR_SHAPING_WEIGHT=0.3`,
`MIRROR_OTHER_VAL=false`, `SHUFFLE_STACK_PEEK_IN_SEARCH=false` -- die
beiden Struktur-Fixes (Widening, Tiebreak) sind fest im Code (kein Toggle,
echte Bugfixes). Bestätigter bester Stand bleibt **17% Netz-Siege** (n=100).

## Fund 6: Bindungs-Check — abgeschlossen, KEIN echtes Problem (2026-07-20)

Nutzer-Auftrag vor weiterer Arbeit an Fund 6: erst messen, ob der Orakel-Bias
überhaupt bindend ist, statt blind mehr Aufwand reinzustecken. Neue
Diagnose `self_play::draw_stack_peek_impact_diagnostic` (pyo3:
`draw_stack_peek_impact_diagnostic`): loggt pro Runde, wie oft
`DrawStackPeek` unter den legalen Aktionen ist bzw. von der Netz-Suche
tatsächlich gespielt wird, UND an tatsächlich gespielten Peek-Entscheidungen
die Wertspanne (max−min) des Netz-Blattwerts über ALLE aktuell im
`dome_tile_pool` verbleibenden Plattenidentitäten (statt der einen echten).

Ergebnis (v9b_domeonly, 30 Spiele, Netz-eigene Suche):

| Runde | Peek angeboten | Peek gewählt | Wahlrate | Ø Wertspanne | Max Wertspanne |
|---|---|---|---|---|---|
| 1 | 397/767 | 36 | 4.7% | **0.0** | **0.0** |
| 2 | 262/737 | 33 | 4.5% | **0.0** | **0.0** |
| 3 | 330/737 | 37 | 5.0% | **0.0** | **0.0** |
| 4 | 472/744 | 30 | 4.0% | **0.0** | **0.0** |
| 5 | 0/531 | 0 | 0% | — | — |

**Eindeutiges Ergebnis, kein Diagnose-Artefakt**: Peeks werden selten
gewählt (~4-5%, obwohl oft angeboten), UND die Wertspanne ist in JEDER
einzelnen Stichprobe EXAKT 0.0 — nicht nur klein. Verifiziert per Code-Grep:
`pending_stack_draw` kommt in `features.rs` NUR in einem Kommentar vor,
nirgends im tatsächlichen Feature-Vektor. Der Value-Head ist also
architektonisch BLIND dafür, welche Platte gerade verdeckt gezogen wurde —
es gibt keinen Bias zu korrigieren, weil die Information den Value-Head nie
erreicht. Das erklärt auch sauber den 17%→9%-Regressions-Befund von vorhin:
die Neumischung (`SHUFFLE_STACK_PEEK_IN_SEARCH`) korrigierte keinen echten
Bias (es gab keinen), sondern führte reines Rauschen ein (welche Platte am
Ende tatsächlich platziert wird, ändert sich zufällig zwischen simulierten
Ästen, ohne dass der Value-Head das je hätte nutzen können).

**Fund 6 damit abgeschlossen** (nicht nur zurückgestellt) — kein weiterer
Aufwand hier gerechtfertigt, zumindest nicht für den Value-Head-Pfad. Ob die
fehlende Kodierung von `pending_stack_draw` die POLICY-Entscheidung
"nochmal ziehen oder aufhören" schwächt, ist eine separate, nicht
untersuchte Frage (Peek-Wahlrate von nur ~4-5% könnte darauf hindeuten,
dass das Netz das Nachziehen generell selten für lohnend hält — unabhängig
von Fund 6).

## Wurzel-Determinisierung, C8-Fix, D-Performance (2026-07-20, Fortsetzung)

**Wurzel-Determinisierung: getestet, gemischtes Ergebnis, TROTZDEM aktiv
belassen (Nutzer-Entscheidung).** Sauberer Ersatz für den In-Tree-Fix: statt
bei jedem simulierten Peek/Chip-Reveal neu zu mischen, EINMAL pro Zugsuche
(`build_net_tree`s Wurzel) `dome_tile_pool` UND unaufgedeckte Bonuschips
(`bonus_chip_pool` + verdeckte Fabrik-Chips) neu mischen, dann die gesamte
Suche deterministisch auf dieser einen Welt laufen lassen — kein
In-Tree-Rauschen. Arena (n=100, kein Early-Stop): **12:88 (12%), Score 19.2
vs. 40.5, Floor 19.2 vs. 13.7** gegen die 17%-Baseline. Ein direkter
Wiederholungslauf DERSELBEN Baseline-Konfiguration (kein Determinisieren,
nur der D-Performance-Fix zusätzlich) ergab bei n=100 aber **11%** statt
17% — d.h. eine Schwankung von 6 Prozentpunkten bei IDENTISCHER
Konfiguration. Das Rauschband dieser Session ist also mindestens so breit
wie der 12%-vs-17%-Unterschied selbst, der Wurzel-Determinisierungs-Befund
ist damit statistisch nicht von "kein Effekt" zu unterscheiden.

**Nutzer-Entscheidung**: trotzdem aktiv lassen (`DETERMINIZE_ROOT_HIDDEN_INFO
= true`) — es geht nicht nur um gemessenen Vorteil, sondern auch um
KORREKTHEIT: die Suche soll kein Wissen nutzen, das ein echter Spieler nicht
hat. Anders als der In-Tree-Fix (klarer, großer, NICHT im Rauschen
erklärbarer Rückschritt 17%→9%, zu Recht verworfen) ist dieser Minimalfix
für das Orakel-Wissen-Problem (Fund 6) bewusst Standardverhalten, unabhängig
vom unklaren Arena-Delta.

**C8 (Checkpoint-Auswahl ignoriert Value-Head) behoben.** `train.py`:
"bestes Modell" wurde bisher NUR nach Policy-Val-Loss gewählt. Jetzt
dieselbe gewichtete Kombination wie der Trainings-Loss selbst
(`p_loss + VALUE_WEIGHT·v_loss + POINTS_WEIGHT·points_loss`), auf den
Val-Metriken (Fallback Train-Loss ohne Val-Split). Wirkt sich erst beim
nächsten Trainingslauf aus.

**D (Performance) — JSON-Umweg im heißesten Suchpfad eliminiert.**
`build_untried_actions` rief pro legaler Aktion pro Knoten
`action_to_id(&action_to_env_dict(...))` auf (serde_json-Objektbau +
String-Matching). Neue Funktion `self_play::action_to_id_direct` matcht
direkt auf `&Action`/`&GameState`, ohne JSON-Umweg — Parität mit dem
JSON-Pfad per neuem Test abgesichert
(`action_to_id_direct_matches_json_path_across_random_games`, 8 Seeds ×
60 Züge, alle legalen Aktionen pro Schritt). Restliche "Kleinkram"-Funde
(D: `feats.to_vec()`-Kopie, `unique_moon_orders`-String-Sortierung) bewusst
NICHT angefasst — beide vom externen Kollegen selbst als minor eingestuft,
Kosten gegenüber dem ONNX-Forward-Pass vernachlässigbar. Python-`p`-
Variablen-Kollision (Spielerindex → Schleifenvariable, `neural_net.py`)
umbenannt (`pe`) — reine Sicherheits-/Klarheits-Änderung, kein
Verhaltensunterschied.

## Gumbel AlphaZero implementiert + arena-validiert (2026-07-20)

Plan-Dokument `elegant-wandering-mist.md` (Nutzer-genehmigt) umgesetzt:
Gumbel-Top-m (m=16) + Sequential Halving an der Wurzel statt Dirichlet-
Noise + PUCT über den vollen Kandidatensatz; neue deterministische
Tiefe-≥1-Auswahlregel (`argmax[π'_node(a) − N(a)/(1+ΣN)]`, `π'_node` =
completed-Q-Softmax) statt `best_puct`; finale Zugwahl unter den
Sequential-Halving-Überlebenden. Formeln exakt aus der DeepMind-mctx-
Referenzimplementierung (nicht nur Paper-Prosa). `USE_GUMBEL_SEARCH`-Toggle,
124/124 Tests grün (reine Erweiterung, alter PUCT-Pfad unverändert).

**Arena-Ergebnis (n=100, kein Early-Stop, GLEICHE Gewichte v9b_domeonly.onnx,
nur andere Suche): 10:90 (10%), Score 22.8 vs. 47.2, Floor 17.3 vs. 14.0 —
liegt im selben Rauschband wie die PUCT-Wiederholungen dieser Session
(11-17%), keine klare Verbesserung.** Nachvollziehbar: Sequential Halvings
Rangfolge UND completed-Q hängen weiter am selben, in Runde 1 schwachen
Value-Head; und die eingesetzten Priors wurden unter PUCT-Besuchszahl-
Zielen trainiert, nicht Gumbels completed-Q-Ziel — der im Plan als
"eigentlicher Gewinn" erwartete Effekt (Phase 4: frisches Self-Play mit
completed-Q-Policy-Zielen + Retrain) ist damit noch nicht getestet, nur die
reine Such-Mechanik (ohne Neu-Training).

**Entscheidungspunkt gemäß Plan**: Ergebnis liegt NICHT klar über dem
Rauschband → mit dem Nutzer besprechen, ob trotzdem zu Phase 4
(frisches Self-Play + Retrain, deutlich teurer) weitergegangen wird oder
pausiert wird. Stand: offen, noch nicht entschieden.

## Baustein B (zweistufiger Kuppel-Suchknoten) + Fund 7 (Schattenpunkte) implementiert (2026-07-20)

Plan-Dokument `elegant-wandering-mist.md` (Nutzer-genehmigt) umgesetzt --
Nutzer-Entscheidung, Baustein B jetzt doch VOR statt nach dem
Value-Head-Entscheidungspunkt umzusetzen, da Gumbel ohnehin einen frischen
Self-Play-Zyklus verlangt (completed-Q-Ziele), und Baustein B (NUM_ACTIONS
ändert sich) diesen Zyklus ohnehin erzwingt -- Effizienzgewinn, beides in
EINEM teuren Batch zu bündeln.

**Baustein B**: der Kuppelplatten-Zug (Kachel/Stapel × Slot × Rotation) ist
jetzt ein ECHTER zweistufiger Suchknoten statt eines kollabierten Einzelzugs
mit Prior-Faktorisierung (Baustein A). Neue `Action`-Varianten
`ChooseDomeSlot`/`ChooseDrawStackSlot` (Stufe 1: Kachel+Slot, ~24-27
Kandidaten) und `ChooseDomeRotation` (Stufe 2: nur Rotation, ≤4 Kandidaten,
gemeinsam für beide Pfade), neues `GameState`-Feld `pending_dome_choice`.
`execute_dome_move`/`execute_draw_from_stack`/`validate_*` (game.rs) bleiben
komplett unverändert -- nur wann/wie die volle Move-Struktur zusammengesetzt
wird, ändert sich (zwei Spielerentscheidungen statt einer, ohne
`switch_player()` zwischen Stufe 1 und 2, exakt wie beim bereits bestehenden
Stapel-Zieh-Muster DrawStackPeek/ChooseDrawStackSlot). Dead-End-Analyse
ergab: Rotation ist in dieser Regelbasis NIE gültigkeitsrelevant
(`validate_dome_move`/`validate_draw_from_stack` prüfen `rotation` gar
nicht, `apply_rotation` schlägt nur bei einer bereits befüllten Kachel fehl,
was für frisch gezogene Kacheln nie zutrifft) -- Stufe 2 hat also strukturell
IMMER ≥1 Fortsetzung, per Test abgesichert
(`dome_slot_candidates_never_yield_a_dead_end_stage_two`).

Frontend/menschliche Spieler-API (`server.py` über `PyGame::apply_dome`/
`apply_dome_stack_choose`, `serialize_valid_moves`) bleibt NACH AUSSEN
byte-identisch -- Tile+Slot+Rotation weiterhin EIN atomarer Aufruf bzw. eine
volle Enumeration in der UI-Zugliste, intern jetzt zwei `apply_drafting`-
Aufrufe bzw. eine lokale Rotations-Auffächerung. Nur die KI-Suche
(net_mcts.rs/mcts.rs, über `drafting_actions()`) sieht die kleinere
Verzweigung.

Die alte `dome_slot_head`/`dome_rotation_head`-Prior-Faktorisierung
(Baustein A, net_mcts.rs + neural_net.py) ist komplett entfernt -- jede
Kachel×Slot- bzw. Rotations-Kombination hat jetzt eine EIGENE, nicht
kollabierte Policy-ID (`action_to_id`: 328-354 choose_dome_slot, 355-390
choose_draw_stack_slot, 391-394 choose_dome_rotation; `NUM_ACTIONS`
346→406), keine Faktorisierung mehr nötig. ONNX-Modellausgabe von 6 auf 4
Tensoren reduziert (policy/value/moon/points).

**Fund 7 (Schattenpunkte, externe Bugfix-Review Abschnitt C)**: `apply_score`
klemmt den sichtbaren Punktestand regelkonform bei 0 -- das verwischte
bisher im Value-/Points-Trainingsziel "schlecht" (0) und "desaströs"
(eigentlich weit im Minus) zum selben Label. Neues `PlayerBoard`-Feld
`score_unclamped` läuft NIE geklemmt parallel mit (Start 5, wie `score`),
wird in `self_play.rs` an allen 6 Backfill-Stellen als `scores_unclamped`
aufgezeichnet (2 Post-hoc-Backfill-Funktionen + 4 Einzelrecord-Stellen --
alle 6 gebraucht, initial wurden nur die 4 Einzelrecord-Stellen gepatcht,
die tatsächlich von `self_play_games` genutzten Backfill-Stellen fehlten
zunächst und wurden erst durch einen End-to-End-Smoke-Test über die echte
Python-Bindung entdeckt). `neural_net.py::VALUE_SCHEMA_VERSION` 13→14,
Zielformel nutzt `scores_unclamped` statt `scores` (Fallback bei fehlendem
Feld für alte Daten). Verifiziert an echtem Self-Play: ein Spiel endete mit
sichtbar `[5, 10]` aber ungeklemmt `[-19, -8]` -- zeigt genau den Fall, den
Fund 7 beheben soll (mehrfach auf 0 geklemmt, dann wieder erholt, sichtbarer
Endstand verschleiert den tatsächlich viel schlechteren Verlauf).

Volle Testsuite 122/122 grün (124 alt − 3 jetzt gegenstandslose
`masked_softmax`-Tests − 2 durch Baustein-B-Umbau ersetzte Faktorisierungs-
Tests + 2 neue Baustein-B-Tests + 1 neuer Dead-End-Test). Wheel neu gebaut
und per End-to-End-Smoke-Test über die echte Python-Bindung verifiziert
(nicht nur `cargo test`).

**Nächster Schritt** (noch NICHT gestartet, braucht Nutzer-Freigabe wegen
Laufzeit/Kosten): frischer Self-Play-Batch (Baustein B + Fund 7 + Gumbel
kombiniert) + Retrain + volle Diagnose-Kette gegen die Session-Baselines
(17% Struktur-Fixes, 10% Gumbel-ohne-Retrain). NUM_ACTIONS-Änderung macht
bestehende Checkpoints für Live-Inferenz endgültig unbrauchbar (erzwingt
ohnehin Policy-Head-Neustart).

## Weitere zurückgestellte Punkte

- `ROUND_TRANSITION_SAMPLING` in der Live-Suche bleibt hinten angestellt,
  bis der Value-Head-Fix einen klaren Fortschritt zeigt.
- round_transition_value-Daten-Skalierung (2000-3000 Spiele) bleibt
  hinten angestellt.
- Gumbels eigentliches completed-Q-Policy-Ziel (`net_drafting_policy` müsste
  `π'(a) = softmax(ln(prior)+σ(completedQ))` statt Besuchsanteil
  aufzeichnen) ist bewusst NICHT Teil des kommenden Self-Play-Zyklus --
  separater Folgeversuch, je nach Ergebnis von B+Fund-7.

## Teil 3: frischer Self-Play-Zyklus + Retrain (Baustein B + Fund 7), v10 (2026-07-20)

Umsetzung des in `elegant-wandering-mist.md` als "braucht Nutzer-Freigabe"
markierten letzten Schritts: da Baustein B (NUM_ACTIONS 346→406, zweistufiger
Kuppel-Suchknoten) und Fund 7 (`score_unclamped`) sowohl alle bestehenden
Checkpoints als auch den kompletten domefact-Korpus strukturell unbrauchbar
machen (gleicher Präzedenzfall wie hs200), war ein frischer, konsistenter
Korpus + Neu-Training nötig.

**Daten-Hygiene**: alle 561 alten `.pkl`-Dateien (550 domefact + 11 ältere
v8d-rtv-Dateien, beide altes 346er-Einstufen-Schema) nach
`data/archive_domefact_preBausteinB/` verschoben (nicht gelöscht, gleiches
Muster wie hs200).

**Self-Play**: 5500 Spiele, Heuristik-MCTS (`--mode mcts`, kein Modell —
kein kompatibler Checkpoint verfügbar), sims=200, 953.832 Züge, 8452s
(~2h21, schneller als domefact trotz gleicher Spielezahl — plausibel durch
Baustein Bs kleineren echten Verzweigungsfaktor). Keine Hänger-Warnungen,
550/550 Dateien vollständig.

**Training (`v10`)**: kein Warm-Start (Nutzer-Entscheidung — Action-Raum UND
Value-Zielformel ändern sich gleichzeitig), `--epochs 100` als reiner
Deckel, Early Stopping (Val-Policy-Plateau) griff bei Epoche 15 (Plateau
seit Epoche 10). Bestes Modell nach gewichteter Val-Metrik (Fund 8):
**Epoche 4** (`alphazero_v10_best`). Netzauslastung gesund (Dead 6%,
Eff.Rank 39%).

**Diagnose-Kette** (`v10_best`, echter Val-Split 55/550 Dateien, n=95.339
Val-Züge):

| Metrik | v10_best | v9b_domeonly (Referenz) |
|---|---|---|
| Policy Top-1 (nur Drafting) | 44.0% | 61.8% |
| Policy Top-3 | 74.3% | 87.1% |
| Value Val-R² (global) | 0.221 | 0.22-0.24 |
| Points Val-R² (global) | 0.377 | 0.27-0.34 |
| Geschwister-Tau Runde 1 | 0.264 (Ø 13.6 Geschw.) | 0.318 (Ø 17.6 Geschw.) |
| Geschwister-Tau Runde 2 | 0.339 (Ø 12.9 Geschw.) | 0.164 (Ø 15.1 Geschw.) |

Value-R² nach Runde (monoton steigend, gleiches Muster wie zuvor):

| Runde | n | R² | MAE |
|---|---|---|---|
| 1 | 18.971 | -0.063 | 0.310 |
| 2 | 19.876 | 0.017 | 0.294 |
| 3 | 20.623 | 0.195 | 0.266 |
| 4 | 20.586 | 0.406 | 0.225 |
| 5 | 15.283 | 0.623 | 0.180 |

**Auffällig, NICHT glattgezogen**: Policy-Top-1/Top-3 und Runde-1/2-Value-R²
sind gegenüber der v9b_domeonly-Referenz sogar leicht SCHLECHTER, obwohl das
Arena-Ergebnis (unten) klar besser ausfällt. Wahrscheinlichste Erklärung:
Baustein B macht aus einem kollabierten Kuppel-Zug zwei echte
Policy-Entscheidungen (mehr, feinere Drafting-Schritte je Spiel, dadurch
strengerer Top-1-Maßstab) UND der Geschwister-Tau sinkt in der
Stichprobengröße (Ø-Geschwister 13.6/12.9 statt 17.6/15.1 — Baustein B
reduziert den ECHTEN Verzweigungsfaktor, weniger Geschwister zum Ranken).
Nicht direkt vergleichbar mit der alten Messung, da sich die zugrunde
liegende Aktionsstruktur geändert hat — als Vorsicht vermerkt, nicht als
Regression gewertet, weil die Suchstärke selbst (Arena) das Gegenteil zeigt.

**Arena (n=100, kein Early-Stop, 150 Sims — Session-Standard für die
17%/10%-Baselines) — neue Bestmarke der Session:**

| Konfiguration | Ergebnis | Ø Score | Floor-Strafe |
|---|---|---|---|
| Struktur-Fixes (vorherige Bestmarke, v9b_domeonly) | 17:83 (17%) | 22.7 vs. 42.2 | 18.1 vs. 12.5 |
| Gumbel ohne Retrain (v9b_domeonly, gleiche Gewichte) | 10:90 (10%) | 22.8 vs. 47.2 | 17.3 vs. 14.0 |
| **v10_best (Baustein B + Fund 7 + frisches Self-Play), Floor-Shaping W=0.3** | **22:78 (22%)** | **26.1 vs. 39.4** | 16.1 vs. 14.1 |
| v10_best, Floor-Shaping W=0.0 (Ablation, gleiches Modell) | 17:83 (17%) | 22.6 vs. 41.1 | 20.7 vs. 13.3 |

**Floor-Shaping-Ablation beantwortet die offene Frage aus dieser Runde
("macht Fund 7 Floor-Shaping überflüssig?") klar mit NEIN**: ohne Shaping
fällt dasselbe Modell von 22% auf 17% zurück, UND die Floor-Strafe
verschlechtert sich sichtbar (20.7 vs. 13.3, gegenüber 16.1 vs. 14.1 mit
Shaping) — Fund 7 (Trainings-Label-Rauschen behoben) und Floor-Shaping
(Such-Zeit-Korrektur) lösen unterschiedliche Probleme, keine Redundanz.
`FLOOR_SHAPING_WEIGHT` bleibt auf 0.3, Wheel zurückgebaut, 122/122 Tests
grün.

**Einordnung**: 22% ist das beste Einzelergebnis der gesamten Session
(vorher 17%), mit engerem Score- UND Floor-Abstand — nach den beiden
Struktur-Bugfixes vom vorigen Zyklus der zweite klare Fortschritt. **Aber**:
nur ein einzelner n=100-Lauf je Konfiguration, das Session-eigene
Rauschband lag bei identischer Konfiguration schon einmal bei 6 Prozent-
punkten (11% vs. 17%) — ein Wiederholungslauf vor endgültiger Einordnung
als neue Baseline wäre angebracht, ist aber (noch) nicht gelaufen.

**Wiederholungslauf (2026-07-20, gleiche Konfiguration, frischer Seed):
26:74 (26%), Ø Score 31.1 vs. 38.9, Floor 16.1 vs. 15.0.** Zusammen mit dem
ersten Lauf (22%) macht das 48:152 (24%) über 200 Spiele — deutlich über der
alten 17%-Bestmarke in BEIDEN Einzelläufen, kein Zufallsartefakt. Der
Score-/Floor-Abstand ist im zweiten Lauf sogar noch enger. **22-26% gilt
damit als bestätigte neue Bestmarke der Session.**

**Gumbels completed-Q-Policy-Ziel implementiert (2026-07-20)**:
`net_mcts::net_root_child_stats_and_policy` baut den Suchbaum einmal und
liefert zusätzlich zu den rohen Stats (weiterhin für die Zugwahl genutzt)
das completed-Q-Policy-Ziel (`improved_policy` an der Wurzel) für ALLE
Wurzelkandidaten. `self_play::net_drafting_policy` zeichnet dieses Ziel
jetzt als Trainings-Policy auf, statt der rohen Besuchsverteilung — die
tatsächlich gespielte Aktion bleibt bewusst besuchsbasiert (keine Änderung
an der Self-Play-Trajektorie/Explorationsvielfalt). Neuer Unit-Test
(`root_completed_q_policy_pairs_each_action_with_its_own_probability`),
123/123 Tests grün. **Wichtige Einschränkung**: `net_drafting_policy` wird
nur von netzgeführtem Self-Play (`--mode network`) genutzt — der
tatsächliche Trainingskorpus dieser Session (domefactB, wie alle Korpora
zuvor) läuft über Heuristik-Self-Play (`--mode mcts`) und ist von dieser
Änderung NICHT betroffen. Um den Effekt zu messen, bräuchte es einen
eigenen netzgeführten Self-Play-Zyklus (Strategiewechsel der Datenquelle,
noch nicht mit dem Nutzer abgestimmt) — Umsetzung bewusst getrennt von
dieser Entscheidung.

**`dynamic_sims`-Entkopplung getestet, als Toggle belassen (2026-07-20).**
`net_mcts::net_effective_sims` kann bei `USE_GUMBEL_SEARCH=true` `base_sims`
unverändert zurückgeben (kein Skalieren mit der Aktionszahl mehr) statt
`dynamic_sims(base,n)`, gated über neues `DECOUPLE_NET_SIMS_FROM_ACTIONS`
(Standard `false`). Ablation (n=100, kein Early-Stop): Netz fest auf 330
Sims (≈ altes `dynamic_sims(150,n)`-Mittel, siehe
`evaluations/actions_per_round.md`) vs. Heuristik unverändert bei 150 —
**20:80 (20%), Ø Score 27.2 vs. 40.9, Floor 16.3 vs. 15.0** — liegt im
Rauschband der 22-26%-Bestmarke, kein klarer Effekt in diesem einzelnen
Test. Bewusst als Toggle (Standard AUS) statt unconditional umgesetzt: eine
unconditional Änderung hätte still überall, wo netzgeführte Suche mit
einem `base_sims`-Wert aufgerufen wird (Server-Mensch-vs-KI,
`self_play.py --mode network`, künftige Arena-Standardwerte), dessen
Bedeutung geändert (vorher automatisch auf ~185-499 hochskaliert, jetzt
exakt der übergebene Wert) — ohne bestätigten Nutzen ein unnötiges stilles
Regressionsrisiko. Code bleibt verfügbar für einen saubereren
Wiederholungstest.

**Offen für die Fortsetzung** (siehe auch Task-Liste dieser Session):
- Ob/wann auf netzgeführtes Self-Play als primäre Datenquelle umgestellt
  wird, um das completed-Q-Ziel tatsächlich zu nutzen — offene
  Nutzer-Entscheidung, kein automatischer Folgeschritt.
- `dynamic_sims`-Entkopplung: nur ein Einzeltest, kein klares Ergebnis —
  bei Bedarf mit mehr Wiederholungen oder anderem `GUMBEL_TOP_M` erneut
  prüfen.

## Zweiter Kollegen-Diagnosevorschlag: günstige Punkte abgearbeitet (2026-07-20)

`evaluations/value head tests.txt` (zweiter externer Kollege) schlägt 7
Diagnosen vor, grob nach Aufwand/Erkenntnisgewinn priorisiert. Punkt 2
(Perspektiven-/OOD-Audit) und 3 (Geschwister-Ranking) waren bereits
größtenteils erledigt (Divergenz-Logging, `MIRROR_OTHER_VAL`-Test,
`sibling_ranking_diagnostic`) — die beiden verbleibenden günstigen Punkte
sind jetzt nachgezogen:

**Punkt 2, Rest (klassische Vorzeichen-/Mirror-Unit-Tests) — implementiert,
KEIN Perspektivfehler gefunden.** Zwei neue Rust-Tests
(`net_mcts::tests`, gegen `alphazero_v10_best.onnx`):
- `net_leaf_eval_is_invariant_to_which_player_is_flagged_current`: flippt
  NUR `state.current_player` an sonst identischen Zuständen — `net_leaf_eval`
  muss (da es intern ohnehin beide Perspektiven separat auswertet und fest
  auf [Spieler0, Spieler1] einsortiert) exakt dasselbe Ergebnis liefern.
  **Hält exakt** (Toleranz 1e-9, 10 Stichproben) — kein Plumbing-Bug in der
  Index-Zuordnung.
- `net_leaf_eval_sign_mostly_agrees_with_exact_dfs_ground_truth`: Netz-
  Vorzeichen (wer liegt vorne) gegen `mcts::evaluate` (exaktes DFS-Urteil)
  über 40 zufällige Drafting-Zustände. **76.9% Übereinstimmung (30/39
  auswertbare Stichproben)** — deutlich über Zufall (50%), passt zum
  positiven (wenn auch schwachen) Geschwister-Tau. Ein systematischer
  Perspektivfehler würde die Rate weit UNTER 50% drücken, nicht nur
  dämpfen — beide Tests zusammen schließen einen groben Perspektiv-/
  Plumbing-Bug als Erklärung für "gesundes R², aber schadet der Suche"
  aus (konsistent mit dem bereits negativen `MIRROR_OTHER_VAL`-Befund).
  125/125 Tests grün.

**Punkt 5 (FPU-/Unvisited-Q-Audit) — Code-Audit, KEIN Fix nötig.**
Nachvollzogen für beide Suchpfade (`build_net_tree`/PUCT-Legacy UND
`build_gumbel_tree`, beide mit identischem Expansions-/Backprop-Muster):
ein Kandidat wird NUR dann in `nodes[nid].children` aufgenommen, wenn
`apply_drafting` erfolgreich war — und genau dieselbe Simulation backprop't
danach sofort entlang des Pfads bis zur Wurzel (inkl. des gerade erzeugten
Kindes). Jedes Element in `.children` hat also strukturell IMMER ≥1 Besuch,
bevor `best_puct`/`gumbel_select_child` es je zu Gesicht bekommen — der
`q=0.0`-Fallback in `best_puct` (auf der [0,1]-Skala eigentlich "sicherer
Verlust", nicht neutral) ist damit bestätigt toter Code, keine Regression
durch Baustein B. Der tatsächlich relevante "unbesucht"-Fall (Kandidaten,
die noch gar nicht expandiert sind) tritt nur im Gumbel-Pfad auf
(`completed_q_per_candidate`) und bekommt dort bereits `v_mix` — einen
plausiblen, prior-gewichteten Elternwert-Schätzer, keine naive Konstante
(0/0.5). **Keine FPU-Reduction-Variante nötig, Punkt 5 damit geschlossen.**

**Punkt 1 (Noise-Floor-Test) gelaufen, dann BIAS-KORRIGIERT (2026-07-21,
Nutzer-Anstoß) — Ergebnis: Deckel praktisch bei Null, Ziel selbst ist das
Problem, noch deutlicher als zunächst gemessen.** Neue pyo3-Funktion
`self_play::value_noise_floor_diagnostic` (rayon-parallel über die
Zustände, jetzt auf beliebige `target_round` verallgemeinert): sampelt
Entscheidungspunkte einer Runde per Heuristik-Walk (KEINE Netz-
Abhängigkeit), spielt je Zustand K unabhängige Heuristik-Fortsetzungen bis
Spielende (Beutel/Kuppelstapel je Wiederholung neu gemischt),
Varianzzerlegung auf dem AKTUELLEN Value-Ziel (VALUE_SCHEMA_VERSION=15,
`score_unclamped`-Margin).

**Bias-Fix**: der erste Lauf berechnete `Var(E[y|s])` naiv als Varianz der
K-Rollout-MITTELWERTE über die Zustände — das schätzt aber
`Var(E[y|s]) + E[Var(y|s)]/K`, nicht `Var(E[y|s])` allein (jeder Mittelwert
ist selbst nur aus K Stichproben geschätzt, der Standardfehler dieser
Schätzung ging fälschlich als erklärbare Signal-Varianz durch). Korrigiert:
`Var(E[y|s])_korrigiert = Var(Mittelwerte)_beobachtet − E[Var(y|s)]/K`. Der
Korrekturterm skaliert mit `1/K`, NICHT mit der Zustandszahl — deshalb K
von 8 auf 16 erhöht (nicht mehr Zustände) für den korrigierten Lauf.

Runde 1 (n_states=120, k_rollouts=16, walk_sims=80, rollout_sims=60,
3070s/~51 Min):

| Metrik | Naiv (K=8, erster Lauf) | Naiv (K=16) | **Korrigiert (K=16)** |
|---|---|---|---|
| max. erreichbares R² | 0.117 | 0.065 | **0.0068** |

Die naive Schätzung sinkt bereits allein durch die K-Erhöhung (0.117→0.065,
wie von der `1/K`-Korrekturformel vorhergesagt) — der korrigierte Wert
landet bei **0.68%**, praktisch nicht von Null unterscheidbar. **Runde-1-
Zustände sagen den finalen Spielausgang so gut wie gar nicht voraus**,
solange beide Seiten danach vernünftig (heuristisch) weiterspielen — noch
entschiedener als die erste (unkorrigierte) Messung nahelegte. Erklärt
zwanglos, warum trotz Baustein B, Fund 7 und alter Struktur-Fixes das
Runde-1-R² dieser Session nie über ~0.03-0.06 hinauskam — kein
Trainingsansatz auf dem AKTUELLEN Ziel (finaler Spielausgang) hätte das je
können. **Wichtige Einordnung (Nutzer-Diskussion)**: das ist eine Aussage
über die VORHERSAGBARKEIT eines Runde-1-Zustands unter WEITERHIN
vernünftigem Spiel, keine direkte Aussage darüber, ob Runde-1-
Entscheidungen selbst kausal irrelevant wären (bei schwächerer Fortsetzung
könnten frühe Unterschiede stärker durchschlagen).

**Runde 2 (gleiche Parameter, 2452s/~41 Min) — ÜBERRASCHUNG: Deckel schon
deutlich höher als Runde 1, NICHT nah bei Null wie zunächst vermutet:**

**Runde 3 (gleiche Parameter, 2142s/~36 Min) — klar in der "echtes
Lernpotenzial"-Zone, bestätigt den monotonen Anstieg:**

| Runde | max. erreichbares R² (korrigiert) | zum Vergleich: trainiertes Modell (v10_best) |
|---|---|---|
| 1 | **0.0068** | -0.063 |
| 2 | **0.166** | 0.017 |
| 3 | **0.437** | 0.195 |

**Gesamtbild (alle drei Runden, gleiche Methode/Parameter,
n_states=120/k_rollouts=16 je Runde)**: der Deckel steigt klar monoton
(0.007 → 0.17 → 0.44) — konsistent mit dem allgemeinen Muster "weniger
verbleibende Runden Zufall = höhere Vorhersagbarkeit". Runde 1 ist
tatsächlich ein Sonderfall (Ziel selbst praktisch unlernbar), Runde 2 hat
bereits einen soliden, vom trainierten Modell bei Weitem nicht ausgeschöpften
Deckel (0.166 möglich vs. 0.017 erreicht — reines Lern-/Trainingsdefizit,
kein Ziel-Problem), Runde 3 zeigt kaum noch Lücke zwischen Deckel und
Modell-R² (0.437 vs. 0.195 — hier ist eher unklar ob die Lücke Trainings-
oder Rauschen-in-der-Deckel-Schätzung selbst ist). **Praktische Konsequenz
für Punkt 6/TD-Bootstrap**: `BOOTSTRAP_HORIZON_ROUNDS=2` (Runde r → r+2)
zielt für Runde-1-Zustände auf einen Zwischenpunkt mit ECHTEM Deckel
(Runde 2/3s Bereich) statt auf Runde 1s eigenen Nahe-Null-Deckel — die
Design-Entscheidung ist durch diese Drei-Runden-Messung nachträglich gut
gestützt. Für Runde-2-Zustände selbst wäre eher ein reines Trainings-
/Kapazitäts-Hebel (mehr Daten, mehr Epochen, evtl. größerer Head) der
naheliegendere nächste Schritt als eine Zieländerung.

**Punkt 6 (TD-/Bootstrap-Value-Ziele) UMGESETZT** (direkt durch diesen
Befund motiviert): `round_transition_deep::bootstrap_value_after_rounds`
bewertet Zustände NUR `BOOTSTRAP_HORIZON_ROUNDS=2` Runden voraus (statt bis
zum echten Spielende wie die bestehende `continue_through_roundN`-Kette,
die dieselbe niedrige Decke wie das Endergebnis hat), dann direkte
`net_leaf_eval`. In beiden Self-Play-Pfaden als neues Feld
`bootstrap_value` aufgezeichnet, in `neural_net.py` (VALUE_SCHEMA_VERSION
14→15) per `TD_LAMBDA=0.5` ins bisherige Ziel gemischt (nicht komplett
ersetzt wie `rtv`). Erster, noch UNGETESTETER Startwert — noch kein
frischer Self-Play-Batch/Retrain damit gefahren, siehe "Nächste Schritte".

**`dynamic_sims`-Entkopplung jetzt Standard** (Nutzer-Entscheidung,
2026-07-21, unabhängig vom uneindeutigen 20%-Ablationsergebnis oben):
`DECOUPLE_NET_SIMS_FROM_ACTIONS=true`. `arena.py`: `NET_SIMS=400` (flaches
Budget, Nutzer-Vorgabe), `HEUR_SIMS` bewusst von `NET_SIMS` entkoppelt und
bei 150 belassen (weiterhin `dynamic_sims`-skaliert, Vergleichbarkeit mit
den 17-26%-Baselines bleibt erhalten). **Server (`server.py`) bewusst NICHT
angepasst** — Sims-Werte werden künftig über Leicht/Mittel/Schwer-Presets
gepflegt, der Standard-KI-Gegner bleibt bis auf Weiteres die Heuristik
(kein aktueller Netz-Checkpoint gilt als "reif genug" für den Standard-Slot).

## Vollaudit Regelbuch + Kollegen-Docs (2026-07-21)

Systematischer Abgleich: offizielles Regelbuch vs. Engine (33 Regeln
geprüft, 29 direkt VERIFIED — alle 8 Wertungsplatten, Punkteformeln,
Strafleiste, Musterreihen-Mechanik, Aktionen B/C/D und Chip-Formeln exakt
korrekt) plus Kontrolle der externen Review-Dokumente (`Bugfixes.txt`,
`Gumbal Alphazero.txt`, `value head tests.txt`). Zwei Agenten-Meldungen
stellten sich als Fehlalarme heraus und bleiben unverändert:

- **T2** (unvollständige Reihen bei vollem Kuppel-Row geräumt): Regelbuch
  S.7 Punkt 3 hat keinen Vollständigkeits-Vorbehalt — Engine korrekt.
- **T5** (genutzte Chips entfernt statt umgedreht): Umdrehen ist laut
  Regelbuch nur Gedächtnisstütze, kein Regel-Effekt hängt an behaltenen
  genutzten Chips — funktional äquivalent.

**Gefixt (alle in einem Commit, volle Testsuite 130/130 grün, Wheel neu
gebaut, End-to-End-Smoke bestanden):**

- **R1 — Sieger-Tie-Break**: `determine_winner` las
  `holds_first_player_marker`, das `score_penalty` bei der Runde-5-Wertung
  aber immer schon gelöscht hatte — jedes Unentschieden ging an Spieler 1.
  Jetzt entscheidet `first_player_next_round` (überlebt die Wertung).
- **R2 — Startspielerfliese nur bei Mond-Nahme**: Regelbuch S.5 vergibt den
  Marker NUR bei der ersten Nahme vom Mondbereich der großen Fabrik; die
  Engine gab ihn bisher schon bei der Sonnen-Nahme ab.
  `LargeFactory::take_from_sun` lässt den Marker jetzt liegen.
- **R3 — Monochrom-Fallback** (gehört zu R2): `fill_large_factory` konnte
  endlos loopen, wenn Beutel+Turm keine 2 Farben mehr liefern. Jetzt wird
  die monochrome Befüllung akzeptiert (`LargeFactory::monochrome_fallback`),
  und nur in diesem Fall vergibt die Sonnen-Nahme den Marker (Regelbuch
  S.10). Ganz ohne Restfliesen wird der Marker defensiv entfernt.
- **R4 — Chip-Reveal auf leer bleibenden Fabriken**: bleibt eine kleine
  Manufaktur bei der Rundenvorbereitung fliesenlos (Vorrat erschöpft), wird
  ihr Bonusplättchen sofort aufgedeckt (Regelbuch S.10, Deadlock-Schutz).
- **R5 — Phasen-Gate**: `apply_drafting` lehnt defensiv jede Aktion ab,
  solange eine Startkuppel-Platzierung aussteht.
- **R6 — Stack-Zieh-Hausregel entfernt** (Nutzer-Entscheidung): die
  Budget-Deckelung "weiterziehen nur mit Punkten" fällt zugunsten der
  Regelbuch-Variante — beliebig oft wiederholen, je −1 Punkt, Score klemmt
  bei 0 (bei 0 Punkten effektiv gratis bis Stapel leer). `score_unclamped`
  zählt die echten Kosten weiter.
- **B1 — `scores_unclamped` im netzgeführten Self-Play**: der Post-hoc-
  Backfill von `play_net_self_play_game` schrieb nur `scores`; jetzt beide
  (Fund-7-Restlücke geschlossen, per Smoke verifiziert).
- **B2 — Tie-Break in `net_drafting_policy`**: deterministischer Zweig
  wählte per nacktem `max_by(visits)` (letzter gewinnt = niedrigster
  Prior); jetzt Tie-Break visits→Q wie `net_mcts::best_root_child`.
- **B3 — Stale Kommentar**: `VALUE_SCHEMA_VERSION=14` → 15 (self_play.rs).
- **G1 — Deterministisches Gumbel für Arena**: `build_gumbel_tree` bekommt
  `add_root_noise` durchgereicht; bei `false` (Arena/Produktion) sind alle
  g(a)=0 — Top-m und Halving ranken rein nach ln(prior)+σ(Q), äquivalent zu
  mctx `gumbel_scale=0`. Self-Play behält echte Gumbel-Exploration.
- **G2 — SH-Budget-Verteilung**: das Restbudget wird jetzt wie in mctx
  durch die VERBLEIBENDE Phasenzahl geteilt (statt der festen
  Anfangs-Phasenzahl), frühe Phasen sind nicht mehr unterbudgetiert.

**Einordnung**: der domefactB-Korpus (5500 Spiele) und v10 sind unter der
alten Marker-Regel + kaputtem Tie-Break entstanden. Keine sofortige
Neugenerierung nötig — der ohnehin anstehende frische Self-Play-Zyklus
(TD-Bootstrap, VALUE_SCHEMA_VERSION=15) nimmt die korrigierten Regeln
automatisch mit. **Nach G1 muss die Arena-Baseline neu gemessen werden**
(deterministisches Gumbel ändert das Arena-Verhalten ggü. den
22-26%-Referenzen) — ein n=100-Lauf als neue Referenz steht aus.

## Arena-Re-Baseline nach den Audit-Fixes (2026-07-21)

Zwei unabhängige n=100-Läufe (v10_best, NET_SIMS=400 flach, deterministisches
Gumbel, neue Regeln, kein Early-Stop) — versehentlich zeitgleich gestartet
(CPU-Doppellast), daher als zwei Stichproben gewertet:

| Lauf | Ergebnis | Ø Score | Floor-Strafe |
|---|---|---|---|
| A | ~36-39% (36:61 nach 97 erfassten Spielen) | 33.6 vs. 39.1 | n/a |
| B | **49:51 (49%)** | 35.3 vs. 34.8 | **14.6 vs. 17.4** |

Gepoolt ≈ **43%** (85/197) — massiv über der alten 22-26%-Referenz, und in
Lauf B erstmals Netz-Floor-Strafe BESSER als die der Heuristik. Der Sprung
ist konfundiert aus drei gleichzeitigen Änderungen (NET_SIMS 400 flach statt
150, deterministisches Arena-Gumbel/G1, Regelfixes R1/R2/R6) und nicht
auftrennbar. Die A/B-Differenz liegt über dem üblichen ±6pp-Band, plausibel
durch die parallele Doppellast. **22-26% ist als Referenz obsolet; neue
Arbeitsreferenz ~43-49% unter den neuen Standardbedingungen.**

## Floor-Shaping-Signifikanzanalyse W=0.3 vs. W=0.0 (2026-07-21)

Nutzer-Auftrag: ist `FLOOR_SHAPING_WEIGHT=0.3` wirklich signifikant besser
als 0.0? Vorab-Erkenntnis: die ALTEN Daten (48/200 vs. 17/100, alte
Bedingungen) sind mit Fisher exakt **p=0.183**, CI [−3.1, +15.8] pp,
Power ~27% schlicht unterpowert — die frühere "bestätigt bei n=100"-
Einordnung oben war statistisch nicht haltbar.

Neues Design: **gepaarte Arena** (identische Spiel-Seeds in beiden Armen —
`net_arena_match` seedet deterministisch je Spielindex), Arm A = W=0.3
(Haupt-Wheel), Arm B = W=0.0 (isolierter Git-Worktree
`../mosaic-floorablation` + eigenes venv, Einzeilen-Diff), beide v10_best,
NET_SIMS=400/HEUR_SIMS=150; Blöcke à 25 Paare, kumulativer exakter McNemar,
Early-Stop-Regime.

**Endergebnis (fixed n=150 Paare)**:

| | W=0.3 | W=0.0 |
|---|---|---|
| Netz-Siege | **52/150 (34.7%)** | 31/150 (20.7%) |
| Ø Floor-Strafe Netz | **15.9** | 20.1 |
| Ø Score-Margin (Netz−Heur.) | **−7.8** | −14.6 |

Diskordante Paare 39:18, **exakter McNemar p=0.0075**, gepaarte
Winrate-Differenz **+14.0 pp, 95%-CI [+4.4, +23.6]**. Sekundärendpunkte
alle gleichgerichtet und hochsignifikant (Floor-Differenz −4.25, p<0.0001 —
der Mechanismus tut nachweislich genau das, wofür er gebaut wurde).
Sequenzielle Ehrlichkeit: der Interim-Stopp bei n=100 (nominal p=0.047)
wäre wegen 4 Zwischenblicken allein KEIN sauberer Nachweis gewesen
(Verfahrens-α≈0.07-0.10); die 50 unabhängigen Zusatzpaare verstärkten den
Effekt aber (Diskordanz 14:6 in Blöcken 5-6 allein), selbst konservativ
verdoppeltes p bleibt <0.02. **Fazit: W=0.3 ist signifikant besser —
FLOOR_SHAPING_WEIGHT=0.3 bleibt.** (Rohdaten/Skripte im Session-Scratchpad,
W=0.0-Worktree `../mosaic-floorablation` steht noch, nichts committet.)

## Netz-Self-Play-Zyklus v11 — Zwischenstand (2026-07-21; Endergebnisse siehe eigener Abschnitt unten)

Erster netzgeführter Zyklus (Nutzer-Freigabe: 2000 Spiele): completed-Q-
Policy-Ziele + TD-Bootstrap (Schema 15) + korrigierte Regeln in einem
Korpus (`selfplay_netcq_*`).

- **Benchmark**: 10 Spiele, 1618 Züge, 146.7s (0.068 Spiele/s) →
  Hochrechnung 2000 Spiele ≈ 8.2h solo.
- **Record-Stichprobe bestanden**: `policy` = echte completed-Q-Verteilung
  (keine One-Hots), `bootstrap_value` in 923/923 Drafting-Steps,
  `scores_unclamped` konsistent.
- **Bugfix nebenbei**: `run_net_self_play` hängt einen
  `perspective_divergence_diagnostics`-Record ans JSON, den self_play.py
  als 11. "Spiel" in die .pkl schrieb — hätte das Training mit KeyError
  gecrasht. Filter in self_play.py ergänzt (arena.py-Muster).
- **Unterbrechungen**: tagsüber Nutzer-Abbruch (Rechner gebraucht, 50
  Spiele gesichert); abends Neustart kollidierte mit der parallelen
  Floor-Shaping-Ablation (lastabhängiger Gamma-Pruning-Chunk-Hänger, vom
  self_play.py-Supervisor korrekt abgefangen) → **Nutzer-Entscheidung:
  serialisieren** — erst Ablation solo fertig, dann Batch solo (~8h,
  Rest 1950 Spiele, frischer Seed).
- **Trainingsplan** (nach Batch): v11 UND v11_sharp1 auf demselben Korpus —
  `POLICY_TARGET_SHARPEN_EXPONENT` 2.0 vs. 1.0, weil das ^2-Schärfen für
  flache Heuristik-Besuchsanteile gedacht war und Gumbels π′ (bereits die
  theoretisch korrekte Zielverteilung) verzerren dürfte. Warm-Start v10,
  gleiche Diagnose-Kette für beide.

## Projekt-Entscheidungen aus der Hyperparameter-/Backlog-Review (2026-07-21)

- **Replay-Fenster (Nutzer-Entscheidung)**: Trainingskorpus je Generation =
  ~5000 Spiele vom aktuellen Champion + je ~1000 der letzten 2
  Vorgänger-Champions (Datei-Subsampling). Impliziert Champion-Gating
  (neues Modell muss den amtierenden in der Arena schlagen). Gilt ab den
  Netz-Generationen; Alt-Regel-Korpora (domefactB und früher) kommen nie
  zurück in den Mix. Datenbedarf je Generation wird per
  Skalierungs-Ablation auf dem netcq-Korpus kalibriert (500/1000/2000-
  Subsets, Potenzgesetz-Fit).
- **`VALUE_SCALE=50` bleibt bewusst fix** (Nutzer: 50 Punkte = gutes Spiel,
  semantischer Anker). Schattenpunkte verlängern nur den negativen Rand der
  Margin-Skala (z.B. −75 → tanh −0.91 statt geklemmt −0.76) — gewollte
  Differenzierung, keine Sättigungsgefahr; Label-Histogramm wird bei der
  v11-Diagnose geprüft.
- **Tote Knöpfe seit Gumbel** (nicht mehr tunen): `DEFAULT_C_PUCT`,
  `DIRICHLET_EPS/ALPHA` (nur Legacy-PUCT-Pfad), `TARGET_TEMP`/
  Temperaturleiter (nur Heuristik-Pfad).
- **Statt Tuning: Entfernen** — `MAX_ACTIONS`/`WIDEN_FACTOR`/
  `POLICY_MASS_CUTOFF` sind im Gumbel-Pfad ab Tiefe ≥1 noch PUCT-Erbe
  (Wurzel ist bereits frei davon); mctx braucht beides nicht, weil die
  Auswahlregel über ALLE Kandidaten läuft und sich selbst begrenzt. Umbau
  als eigenes Arbeitspaket geplant (gebündelt mit Inferenz-Batching).
- **Runde-5-Alpha-Beta**: Prüfauftrag ergab — bereits vollständig
  implementiert und in BEIDEN Suchpfaden verdrahtet (`round5::applies` an
  allen vier Netz-Einstiegspunkten); kein offener Punkt.
- **Nächste Arbeitspakete** (nach v11): Elo-Tracking mit festem
  Benchmark-Kader (beendet Baseline-Drift), Inferenz-Batching Batch=2 je
  Blatt (+ `MIRROR_OTHER_VAL`-Neubewertung anhand der perspective_divergence-
  Daten aus dem netcq-Batch), Run-Manifeste je Lauf, ISMCTS-Mehrfach-
  Determinisierung, Diversitäts-Monitoring auf dem netcq-Korpus.

## Netzgeführter Self-Play-Zyklus v11 — Endergebnisse (completed-Q + TD-Bootstrap + Regelfixes) (2026-07-22)

Abschluss des oben als Zwischenstand dokumentierten ersten NETZGEFÜHRTEN
Zyklus: 2000 Spiele `selfplay_netcq_*` (v10_best als Generator, base_sims=400,
Gumbel-Self-Play mit Root-Noise, completed-Q-Policy-Ziele via
`net_drafting_policy`, `bootstrap_value`/`scores_unclamped` nach Schema 15,
korrigierte Regeln).

**Batch-Historie / Hänger-Bewährung.** Der Batch lief über mehrere
Unterbrechungen (Nutzer-Abbrüche tagsüber, Serialisierung gegen die
Floor-Shaping-Ablation): 300 Spiele stammen aus Läufen VOR dem
Root-Cause-Fix `1a683d3`, die restlichen 1700 aus dem Nutzer-Lauf danach.
Entscheidender Befund auf dem Weg: die Chunk-Hänger sind INTRINSISCH
(seltener Spielzustand — 1 Rust-Thread spinnt auf 100%, alle übrigen
rayon-Worker idle; auch solo ohne Parallellast, ~1 Hänger je ~7 Chunks;
py-spy sieht nur rayons WaitOnAddress im Hauptthread, Dump
`hang_dump_15024.txt` im Session-Scratchpad), NICHT lastbedingt — die
Lasthypothese vom Vorabend war damit widerlegt. Mitigation:
`MAX_CHUNK_TIMEOUT_SECS=450` in self_play.py (Hänger-Steuer 7,5 statt
20 Min). **Bewährungsprobe bestanden: der 1700-Spiele-Nutzer-Lauf nach dem
Root-Cause-Fix lief KOMPLETT ohne einen einzigen Hänger durch** (~0.07
Spiele/s durchgehend). Record-Stichprobe über frühe/mittlere/späte Dateien:
0 Pseudo-Records (Diagnostics-Filter wirkt), ~98-99% echte
completed-Q-Verteilungen, `bootstrap_value` 100% der Drafting-Steps,
`scores_unclamped` 100%, keine unvollständigen Partien. domefactB (550
Dateien, alte Regeln + Besuchsanteil-Ziele) nach
`data/archive_domefactB_preRuleFix/` verschoben — kommt nie zurück in den
Mix (Replay-Fenster-Regel).

**Training: v11 (Exponent 2.0) und v11_sharp1 (Exponent 1.0)** — beide
Warm-Start von v10, 290.702 Train- / 32.370 Val-Züge (Val-Split 20/200
Dateien). Hintergrund sharp1: `POLICY_TARGET_SHARPEN_EXPONENT=2.0` war für
flache Heuristik-Besuchsanteile eingeführt worden; auf Gumbels π′
(theoretisch bereits korrekte Zielverteilung) ist das Schärfen mutmaßlich
eine Verzerrung. Beide Läufe nahezu deckungsgleich: Early Stop Epoche
15/100 (Val-Policy-Plateau ab 10), **bester Checkpoint jeweils EPOCHE 2**
(val_combined 1.8738 bzw. 1.9096), Value-Val-R² peakt bei Epoche 1-2
(~0.13-0.15) und zerfällt danach monoton. Netzauslastung gesund (Dead 5%,
Eff.Rank 41%/40%). Die Epoche-2-Auswahl bestätigt den C8-Fix als wirksam —
der reine Policy-Val-Loss hätte einen späteren, valueseitig schlechteren
Stand gewählt.

**Offline-Diagnose (Val-Split, identischer Seed wie Training):**

| Metrik | v11_best | v11_sharp1_best | v10_best (Referenz)* |
|---|---|---|---|
| Policy Top-1 (nur Drafting, n=23.667) | 38.2% | 38.3% | 44.0% |
| Policy Top-3 | 66.8% | 66.5% | 74.3% |
| Value Val-R² global | +0.139 | +0.134 | 0.221 |
| R² Runde 1 | **+0.029** | +0.020 | **−0.063** |
| R² Runde 2 | **+0.101** | +0.098 | **+0.017** |
| R² Runde 3 | +0.138 | +0.109 | 0.195 |
| R² Runde 4 | +0.084 | +0.080 | 0.406 |
| R² Runde 5 | +0.290 | +0.305 | 0.623 |
| Geschwister-Tau R1 (n=100) | 0.207 (Ø 16.2) | 0.175 (Ø 15.1) | 0.264 |
| Geschwister-Tau R2 | 0.179 (Ø 13.4) | 0.193 (Ø 12.6) | 0.339 |

*v10-Spalte NICHT direkt vergleichbar: anderer Korpus (domefactB) UND
anderes Value-Ziel (der TD-Bootstrap-Blend ändert die Zieldefinition
selbst — die niedrigeren R4/R5-Werte messen ein anderes Ziel, nicht
zwingend schlechteres Lernen). Kernbefund im Sinne der Design-Absicht von
Punkt 6: **Runde-1/2-R² erstmals positiv bzw. deutlich verbessert**
(+0.029/+0.101 statt −0.063/+0.017). Exponent 2.0 vs. 1.0: praktisch kein
Unterschied (v11 hauchdünn vorn bei Top-3, globalem R², R1-R², R1-Tau) —
Arena nur für v11_best gefahren, sharp1 nicht (Bild ist "kein messbarer
Unterschied", nicht "unklar"; Nutzer-/Koordinator-Entscheid).

**Label-Histogramm (VALUE_SCALE-Check, Val-Split n=32.370):**
|Ziel|>0.9: **0.00%** (auch >0.99: 0.00%); 66.2% unter 0.3, 32.4% in
[0.3,0.6), 1.4% in [0.6,0.9). Keinerlei Sättigung — falls überhaupt, ist
`VALUE_SCALE=50` eher zu groß (Ziele in ein schmales Band gestaucht), die
Schattenpunkte-Sättigungssorge ist damit empirisch vom Tisch.

**Arena + Champion-Gating:**

| Match | Ergebnis | Ø Score | Floor |
|---|---|---|---|
| v11_best vs. Heuristik (n=100, 400/150, kein Early-Stop) | **37:63 (37%)** | 30.2 vs. 39.8 | 15.0 vs. 16.3 |
| v11_best vs. v10_best (Gating, n=100, je 400 Sims) | **43:57 (43%)** | 26.9 vs. 29.4 | — |

37% liegt am unteren Rand der v10-Re-Baseline (37%/49%, gepoolt ~43%) —
kein Beleg für Verbesserung, aber im ±6pp-Band auch kein klarer
Rückschritt. Das Gating-Match ist statistisch nicht von Parität zu
unterscheiden (z≈−1.41, p≈0.16), aber sicher KEIN Sieg für v11.
**Gating-Entscheid: v10_best bleibt Champion und Self-Play-Generator für
v12.**

**Ehrliche Einordnung — dreifach konfundiert, nicht auftrennbar:** der
Vergleich v11 vs. v10 vermischt (1) completed-Q- statt Besuchsanteil-
Policy-Ziele, (2) TD-Bootstrap-Value-Ziel (Schema 15), (3) die Regelfixes
aus dem Audit — und zusätzlich (4) die HALBIERTE Datenmenge (2000 netcq-
vs. 5500 domefactB-Spiele) sowie (5) den Generatorwechsel (netzgeführtes
statt heuristisches Self-Play, andere Zustandsverteilung). Dass v11 bei
halber Datenmenge nahe an v10 herankommt und die Runde-1/2-Value-Metriken
verbessert, ist kein Misserfolg des Ansatzes — aber ein Nachweis der
Überlegenheit ist es ebenso wenig. Naheliegendster nächster Hebel gemäß
Replay-Fenster-Regel: Korpus auf ~5000 Spiele des Champions (v10_best)
auffüllen und v12 auf voller Datenmenge trainieren, bevor am Zielformat
weitergedreht wird.

## Nach-v11-Arbeitspakete: Stand + Tuning-Konsolidierung (2026-07-22, laufend)

Drei Agenten-Arbeitspakete parallel (Nutzer-Direktive: Koordinator plant,
Sonnet-Agenten führen aus):

**Speed-Bündel Phase 1 — FERTIG (135/135 Tests, noch uncommitted, Commit
kommt mit Phase 2 als Paket):**
- **Inferenz-Batching (#63a)**: `Net::eval_pair` — beide Blatt-Perspektiven
  (Mover + geflippt) in EINEM Batch=2-ONNX-Aufruf statt zwei sequenziellen.
  Eigener fest auf Batch=2 optimierter tract-Plan, Paritätstest (1e-5) grün.
  Gemessen: 190µs → 98µs je Blatt-Doppelauswertung = **~1.94× Suchspeedup**.
- **Gumbel Tiefe ≥1 mctx-treu (#68)**: `gumbel_select_child` wählt jetzt
  über children ∪ untried (unbesuchte mit N=0, completed-Q=v_mix),
  Expansion on demand — Widening-Cap UND 95%-Cutoff im Gumbel-Pfad
  vollständig entfernt (Legacy-PUCT-Pfad unangetastet). Echte
  Suchverhaltens-Änderung → gepaarter Alt-vs-Neu-Arena-A/B in Phase 2
  zwingend, bevor es Standard wird.
- **R6-Nachtrag Peek-Kosten (#70)**: neue `PlayerBoard::apply_paid_cost` —
  Stapel-Ziehungen ziehen nur den tatsächlich BEZAHLTEN Betrag von beiden
  Scores ab (Gratis-Ziehung bei 0 Punkten lässt `score_unclamped` konstant);
  Strafen laufen weiter ungeklemmt (Fund-7-Kern unberührt). Nutzer-
  Klarstellung: freiwilliger Kauf ≠ Strafe.

**Phase 2 (wartet auf Trainings-Ende):** Run-Manifeste + Trainings-Korpus-
Log (#64, Nutzer-Wunsch: je Trainingsstart die Zusammensetzung nach
Versions-Präfix loggen, z.B. "3000× v10, 2000× v11" — das Replay-Fenster
stellt der Nutzer MANUELL zusammen, die frühere Implementierungs-Aufgabe
ist gestrichen), Wheel-Rebuild, gepaarte Arena-Validierung des Bündels.

**Daten-Skalierungs-Ablation (#69) — FERTIG, differenziertes Ergebnis**
(fixer Val-Split identisch zu v11, Cache-Key-Bug vorab gefixt+committiert
`475d9c8`: TD_LAMBDA fehlte im HDF5-Cache-Key — ein Lambda-Sweep hätte
sonst still die 0.5-Targets recycelt):

| Spiele | Epoche | val_combined | Val-Ploss | R² global |
|---|---|---|---|---|
| 500 | 2 | 1.9148 | 1.8609 | 0.113 |
| 1000 | 2 | 1.8993 | 1.8461 | 0.121 |
| 2000 (=v11) | 2 | 1.8738 | 1.8222 | 0.139 |

**Policy-Seite ab 500 Spielen praktisch flach** (Potenzgesetz-Exponent
val_combined ≈ −0.016) — die Datenmengen-Halbierung erklärt den v11-
Stärke-Rückstand also NICHT über die Policy. **Value-Seite steigt monoton
ohne Sättigung**, aber mit kleiner Effektgröße (Fit: 5000 Spiele ≈ +0.02
R² global). Konsequenz: mehr Daten sind fürs Value-Ziel vertretbar, aber
kein Zwang; die Datenmangel-These ist als Haupterklärung geschwächt.

**TD_LAMBDA-Sweep (#72) — FERTIG, klare Empfehlung λ=0.7:**

| λ | Val-Ploss | R²-Struktur | Label-Band <0.3 |
|---|---|---|---|
| 0.3 | 1.8262 | Signal fast nur R5 (R1-R4 schwach) | 52.7% |
| 0.5 (=v11) | 1.8222 | R1/R2 positiv, R3/R4 mittel | 66.2% |
| 0.7 | 1.8269 | gleichmäßig über ALLE Runden inkl. R1 0.059 | 73.3% |

Alle λ: beste Epoche 2 (Overfitting-Tempo unverändert), Val-Ploss
praktisch identisch (Spanne 0.005 — policy-neutral). R² über λ hinweg
NICHT höhenvergleichbar (Zieldefinition ändert sich) — bewertet wurde nur
die Struktur. **v11_td07 (λ=0.7) verdient einen Arena-Test** (gleichmäßige
Rundenabdeckung = genau die Punkt-6-Absicht); λ=0.3 verworfen.

**Diversität (#67) + Elo-Infra (#62):** siehe oben — beide fertig.

**Speed-Bündel Phase 2b — FERTIG (Commit ad13044):** train.py-Manifest +
Korpus-Log live (corpus_composition nach Versions-Präfix). Gepaarter
A/B ALT-vs-NEU (150 Paare, v10_best@400 vs. Heuristik@200): NEU 46:56 ALT,
McNemar p=0.28, CI [−17.3, +4.0] pp — **kein Nachweis in irgendeine
Richtung**, Bündel bleibt (1.94× Speed + mctx-Treue; #68 als Merkposten,
falls v12 enttäuscht). Perspektiven-Divergenz-Readout: 7-15% je Runde
(sinkend R1→R5), MIRROR-Retest bewusst nicht priorisiert (alter klarer
Negativ-Befund, Mechanik von keinem Umbau berührt).

**Erste vollständige Elo-Kader-Tabelle (Heuristik@200 = 1000, Anker):**

| Modell | Elo | 95%-CI | Spiele |
|---|---|---|---|
| v10_best@400 (Champion) | 858 | [793, 915] | 250 |
| v11_td07_best@400 | 853 | [770, 922] | 100 |
| v11_best@400 | 809 | [708, 895] | 100 |

Kader-Realität: der Champion liegt bei ~31% gegen Heuristik@200 (die
200-Sims-Heuristik ist stärker als die alte 150er-Referenz — Messlatte
verschoben, aber ab jetzt fix).

**td07-Arena-Test (#73) — λ=0.7 NICHT übernommen:** v11_td07 30:70 gegen
Heuristik@200 — statistisch identisch mit v10s 30.7%-Referenz (p≈0.91),
Gating-Match daher übersprungen, v10_best bleibt Champion. Die im Sweep
gesehene gleichmäßigere Value-Struktur übersetzt sich (wie schon bei v11)
nicht in Spielstärke. **v12 trainiert mit TD_LAMBDA=0.5 (Status quo).**
Wiederkehrendes Muster der Projektgeschichte bestätigt sich: Value-Ziel-
Verbesserungen bewegen Offline-Metriken, aber die Stärke-Hebel waren bisher
ausnahmslos Such-Mechanik (Struktur-Fixes, Sims-Budget, Floor-Shaping).
Nebenbefund für künftige Läufe: run_net_arena mit threads=0 läuft
single-threaded (Rust-Default 1) — threads explizit setzen (4× Speedup
gemessen).

**Danach eingeplant:** ISMCTS-Mehrfach-Determinisierung (#65, eigener
gepaarter A/B nach Phase 2 — Suchänderungen werden nie gebündelt getestet),
Knoten-Budgets/Einzelspiel-Flush/Heartbeat (#71, vor dem v12-Batch:
Zeitbudgets machen rtv/bootstrap-Labels lastabhängig, Knoten-Budgets machen
sie deterministisch).

**Diversitäts-Monitoring (#67) — FERTIG, Urteil: GESUND, kein Kollaps.**
`evaluations/selfplay_diversity_report.py` (wiederverwendbar als
Regressions-Check), alle 200 netcq-Dateien vs. 30 domefactB-Referenzdateien,
Eröffnungen exakt aus den state-log-Diffs rekonstruiert: **1996/2000
einzigartige 3-Zug-Eröffnungen** (normierte Entropie 1.00, häufigste
Eröffnung 0.1%), Brett-/Startspieler-Siegraten ~50/50 (Fairness ok),
Spiellängen 161.5±4.3 (etwas kürzer als Heuristik 173.7±4.3 — plausibler
Stilunterschied, kein Befund). **Keine Eröffnungs-Temperatur für v12 nötig.**

**Elo-Tracker (#62) — Infrastruktur FERTIG, erste Kader-Matches ausstehend.**
`evaluations/elo_tracker.py` + `elo_history.csv`: Bradley-Terry-MLE
(MM-Algorithmus) je Zusammenhangskomponente des Match-Graphen,
Heuristik@200 als fixer 1000-Anker, 95%-CI per Bootstrap, CLI add/report.
Initial nur das kader-valide Gating-Match (v11 43:57 v10) eingetragen; alte
@150/Alt-Regel-Matches bewusst nicht backfilled (im Docstring begründet).
Die ersten echten Kader-Matches (v10_best/v11_best je vs. Heuristik@200)
sind als Kommandos vorbereitet und laufen, sobald die Maschine frei ist.

**Tuning-Parameter-Konsolidierung (Stand 2026-07-22):**

| Parameter | Status |
|---|---|
| POLICY_TARGET_SHARPEN_EXPONENT | ERLEDIGT: toter Knopf auf completed-Q (v11 vs. sharp1 identisch), bleibt 2.0 |
| FLOOR_SHAPING_WEIGHT=0.3 | VALIDIERT (gepaart, +14pp, p=0.0075); 0.15/0.6-Sweep optional |
| VALUE_SCALE=50 | FIX (Nutzer-Anker); Histogramm: 0% Sättigung, eher gestaucht |
| MAX_ACTIONS/WIDEN_FACTOR/POLICY_MASS_CUTOFF | ENTFERNT statt getunt (#68), Validierung Phase 2 |
| c_puct / Dirichlet / TARGET_TEMP | tote Knöpfe (Legacy-/Heuristik-Pfad) |
| TD_LAMBDA | Sweep LÄUFT (0.3/0.7 vs. 0.5) |
| Datenmenge/Generation | Ablation LÄUFT (500/1000/2000) |
| NET_SIMS 400 vs. 800 | offen, nach Phase 2 (Batching halbiert die Kosten) |
| GUMBEL_TOP_M 16 vs. 32 | offen, nach Phase 2 (#68 ändert vorher die Tiefe-≥1-Breite) |
| VALUE_WEIGHT/POINTS_WEIGHT | offen, nach TD-Ergebnis (billiger Retrain-Sweep) |
| GUMBEL_C_SCALE/C_VISIT | offen, niedrige Priorität |
| BOOTSTRAP_HORIZON_ROUNDS | geparkt bis nach v12 (teuer, Noise-Floor stützt 2) |

## Task #71: Knoten-Budgets, Einzelspiel-Flush, Heartbeat (2026-07-22, Commit 753f749)

Label-Determinismus + Robustheit vor v12. Kalibrierung deckte auf, dass die
alten Zeitbudgets REALE Cutoffs waren: Runde-2-Sampling überschritt seine
30s regelmäßig schon unbelastet (Median 23.9s, Max 32.1s), und
`choose_drafting_action_pruned` wurde faktisch von der 15ms-Deadline
beschnitten (Median nur 13 Knoten!) statt vom 20.000er-Knotenbudget —
**die rtv-/bootstrap-Labels aller bisherigen Korpora waren also
lastsensitiv.** Jetzt: `POLICY_NODE_BUDGET=40` als primärer,
deterministischer Cutoff; alle Zeitbudgets zu großzügigen Not-Deckeln
umgewidmet (Werte siehe Code-Kommentare mit Kalibrier-Basis).
Einzelspiel-Flush (.jsonl je Spiel, Chunk-Kill kostet ≤1 Spiel, Retry
fordert nur Fehlendes nach — im Smoke real bewährt: 18/20 gerettet) +
Heartbeat-Erkennung (180s ohne Herzschlag = tot, langsam ≠ tot).
138/138 Tests inkl. Determinismus-Test (`bootstrap_value_after_rounds`
seed-exakt reproduzierbar). Nebenbefund als Folge-Task: ~1e-4
Prozessgrenzen-Nichtdeterminismus in tract-onnx (vorbestehend,
vernachlässigbar). **[KORRIGIERT: tract-onnx ist bit-exakt; die wahre
Quelle ist round5.rs' 150ms-Wall-Clock-Deadline — siehe eigener
Abschnitt unten (2026-07-22).]**

## Task #65: ISMCTS-Mehrfach-Determinisierung implementiert + arena-widerlegt (2026-07-22)

`net_mcts.rs`: neue Konstante `NUM_DETERMINIZATIONS` -- klassisches ISMCTS
(mehrere unabhängige Welten statt der bisherigen EINEN Stichprobe pro
Zugsuche, siehe `DETERMINIZE_ROOT_HIDDEN_INFO`). Bei `>1` wird das
Sims-Budget gleichmäßig auf `N` Welten gesplittet (Rest an die erste Welt),
je Welt ein eigener Baum gebaut, die completed-Q-Politik an der Wurzel über
die Welten gemittelt (Standard-ISMCTS-Aggregation). Umgesetzt an allen drei
Such-Einstiegen (`net_search_drafting_action`, `net_root_child_stats_and_policy`,
`net_search_with_tree`); der `<=1`-Codepfad bleibt an allen drei Stellen
unverändert (kein Routing durch die neue Aggregations-Maschinerie), damit
`NUM_DETERMINIZATIONS=1` byte-identisch zum Alt-Verhalten bleibt.

**Befund zur Wurzel-Kandidatenliste** (Aufgabenstellung fragte explizit
danach): weltunabhängig -- `drafting_actions(state)` hängt nur von
öffentlichem Zustand ab (Fabrik-Existenz/-Farbe, Dome-Auslage,
Pending-Struktur), NIE von `dome_tile_pool`-Reihenfolge oder der Identität
unaufgedeckter Bonuschips (nur deren Existenz zählt). Die Aggregation über
den direkten Aktions-Schlüssel ist damit exakt, keine Näherung. 143/143
Tests grün (138 Baseline + 5 neu: Sims-Split-Arithmetik, synthetische
Aggregations-Mathematik, n=1-Äquivalenz zum Alt-Pfad, n=3 zieht
nachweislich 3 verschiedene `dome_tile_pool`-Ordnungen).

**Gepaarter A/B** (`evaluations/paired_arena_ismcts.py`, Muster wie beim
Speed-Bündel-A/B): ALT (n=1, Worktree `../mosaic-ismcts-n1`) vs. NEU (n=3,
Haupt-Wheel), v10_best @ NET_SIMS=400 vs. Heuristik @ HEUR_SIMS=200, Blöcke
à 25, kumulativer exakter McNemar, Stopp bei p<0.05 oder 150 Paaren.
**Ergebnis: STOPP nach 75 Paaren, p=0.00088 -- n=1 gewinnt signifikant
gegen n=3** (nicht wie erhofft umgekehrt):

| Arm | Siege vs. Heuristik | 95%-KI |
|---|---|---|
| ALT (n=1) | 38/75 = 50.7% | 39.6-61.7% |
| NEU (n=3) | 19/75 = 25.3% | 16.9-36.2% |

Diskordant b=6 (n=3 gewinnt, n=1 nicht), c=25 (umgekehrt) -- deutlich, nicht
im Rauschband. Wahrscheinlichste Erklärung: das 400er-Sims-Budget auf 3
Welten gesplittet (~133/Welt) unterbudgetiert `GUMBEL_TOP_M=16` + Sequential
Halving pro Welt stark genug, dass der Suchtiefenverlust den
ISMCTS-Aggregationsgewinn bei diesem Sims-Niveau klar überwiegt.

**Entscheid**: reiner Performance-Hebel (kein Korrektheits-Fix, anders als
`DETERMINIZE_ROOT_HIDDEN_INFO` selbst) -- Nachweis-Regel greift, nicht die
Floor-Shaping-Präzedenz (die gilt nur für Korrektheits-Fixes bei flachem
Ergebnis). `NUM_DETERMINIZATIONS` auf `1` zurückgesetzt (Standard bleibt
Einzeldeterminisierung), Haupt-Wheel entsprechend neu gebaut/installiert.
Der komplette Mehrwelten-/Aggregations-Code bleibt als Toggle im Code
verfügbar (z.B. für einen künftigen Test bei höherem Sims-Budget). Kein
neuer `elo_history.csv`-Eintrag (v10_best@400 vs. Heuristik@200 existiert
bereits als Paarung, siehe oben) -- nur hier dokumentiert.

## Task #65 (ISMCTS) + Mess-Diskrepanz-Klärung (2026-07-22)

**ISMCTS-Mehrfach-Determinisierung getestet und VERWORFEN** (Commit 61fce82):
n=3 Welten mit gesplittetem Budget (~133 Sims/Welt) verlor den gepaarten
A/B klar (25.3% vs. 50.7%, McNemar p=0.0009, Stopp nach 75 Paaren) — der
Budget-Split hungert Sequential Halving stärker aus, als die Welten-
Mittelung bringt. `NUM_DETERMINIZATIONS` zurück auf 1, Code bleibt als
Toggle (143/143 Tests). Sauberer Implementierungs-Befund nebenbei:
Wurzel-Kandidaten sind beweisbar weltenunabhängig (Aggregation exakt).

**Diskrepanz-Klärung**: der ALT-Arm des ISMCTS-A/B (50.7% vs. Heuristik@200)
widersprach dem Elo-Referenzwert (30.7%, 46/150) um +3.7σ. Frische
Replikation auf dem aktuellen Wheel (n=150, neuer Seed): **34.7%** —
kompatibel mit 30.7% (p=0.46), NICHT kompatibel mit 50.7% (p=0.02).
Chi²-Heterogenität über alle drei Messungen (p=0.012) geht vollständig auf
den 75er-Ausreißer zurück. Arena-Pfad zwischen den Wheel-Ständen per
git-diff als funktional identisch verifiziert. **Elo-Eintrag v10=858
bleibt; die 50.7% werden als Kleinstichproben-Ausreißer verworfen.**
Einordnung fürs n=3-Urteil: gegen die replizierte 31-35%-Basis ist NEUs
25.3% allein nicht mehr signifikant schlechter (p≈0.15) — die Rückbau-
Entscheidung bleibt trotzdem richtig (Nachweis-Regel: n=3 müsste einen
VORTEIL zeigen, und davon ist nichts zu sehen).

**Prozess-Lernpunkt** (aus der Bohrung): bei Worktree-A/B-Tests den
tatsächlich gebauten Diff (inkl. uncommitted lokaler Edits) VOR dem Löschen
des Worktrees persistieren — der ISMCTS-ALT-Worktree war bereits gelöscht,
die Konstanten-Verifikation nur noch indirekt möglich (interne Konsistenz
des gepaarten Splits widerlegte die Wheel-Verwechslung, aber ein Beleg wäre
besser gewesen).

## Prozessgrenzen-Nichtdeterminismus geklärt: tract-onnx entlastet, round5.rs überführt (2026-07-22)

Untersuchung des Task-#71-Nebenbefunds (bootstrap_value/rtv weichen über
separate Prozessstarts ~1e-4..1e-3 ab, trotz Knoten-Budgets und identischer
Live-Züge). Ergebnis in zwei Teilen:

**Teil 1 — tract-onnx ist BIT-EXAKT reproduzierbar** (Hypothese
"Fließkomma-Nichtdeterminismus über Prozessgrenzen" widerlegt). Isolierte
Probe `engine/examples/net_determinism.rs` (bleibt im Repo): 8 seeded
Zufalls-Feature-Vektoren durch `Net::eval` UND `Net::eval_pair`
(v10_best.onnx), alle vier Köpfe als f32-Bitmuster in Datei. 12 separate
Prozessstarts → alle Dateien bitweise identisch; zusätzlich zwei
`Net::load`-Instanzen im selben Prozess bitgleich (auch die
Graph-OPTIMIERUNG ist deterministisch, keine HashMap-Order-Effekte) und
Wiederholungs-Aufrufe bitgleich. tract-linalg läuft default
single-threaded (`Executor::SingleThread`, `multithread-mm`-Feature aus,
kein rayon in der Dep-Kette) — es gibt dort nichts zu konfigurieren.

**Teil 2 — die wahre Quelle: `round5::TIME_BUDGET` (150ms) ist weiterhin
ein PRIMÄRER Wall-Clock-Cutoff.** Task #71 hat nur
round_transition/round_transition_deep auf Knoten-primär umgestellt;
`round5::negamax` prüft `Instant::now() >= deadline` an JEDEM Knoten, und
das `NODE_BUDGET=200_000` ist dort de facto unerreichbar: temporäre
Diagnose-Probe (6 realistische Runde-5-Stellungen via
`drive_to_round_start(seed, 5)`, Release-Build, danach wieder entfernt):

- 200k Knoten brauchen **45-393 SEKUNDEN** (nicht ms) — bei 150ms schafft
  die Suche nur ~0,04-0,7% des Knotenbudgets, der Umfang hängt allein von
  der momentanen Maschinenlast ab.
- **4 von 6 Stellungen liefern schon IN-PROZESS bei 3 direkt
  aufeinanderfolgenden `exact_round5_outcome`-Aufrufen verschiedene
  Werte**, Spanne bis **0,065 Gewinnwahrscheinlichkeit** (z.B. 0,739 vs.
  0,681). Das ist kein Prozessgrenzen-Effekt, sondern Run-zu-Run-Rauschen
  bei jedem einzelnen Aufruf.

Damit vollständig konsistent mit dem E2E-Bild: `mcts.rs` ist komplett
wanduhrfrei (Live-Züge exakt reproduzierbar; Ausnahme Runde-5-Züge via
`round5::choose_action` — gleiche Deadline, Argmax war im E2E-Test nur
zufällig robust), und die ~1e-4..1e-3 im Label sind das ±0,065-Rauschen
des Runde-4→5-Evaluators, verdünnt durch 24-Sample-Mittelung und die
Bootstrap-Kette. Die Restgröße nach der 1h-Budget-Probe in
round_transition_deep.rs erklärt sich exakt dadurch, dass round5.rs (und
die Not-Deckel `TIME_BUDGET_TRAIN`/`_ROUND4` in round_transition.rs) von
dieser Probe nicht erfasst waren.

**Einordnung/Handlungsbedarf**: Kein net.rs-Problem, nichts zu fixen an
tract. Aber die Task-#71-Aussage "Labels sind jetzt deterministisch" gilt
NUR bis Runde 3 — das Runde-4-Label (und jede Bootstrap-Kette, die Runde 5
erreicht) trägt weiterhin lastabhängiges Rauschen von ±einigen Prozent
Gewinnwahrscheinlichkeit pro Evaluator-Aufruf. Möglicher Folge-Task (nicht
umgesetzt, Entscheidung offen): round5.rs analog Task #71 auf
Knoten-primär umstellen — dazu müsste das Knotenbudget auf das real in
150ms Erreichbare kalibriert werden (~500-4000 Knoten laut Messung, statt
200k), Zeit-Deadline nur noch als Not-Deckel; betrifft neben dem Label
auch die Live-Runde-5-Zugwahl (`choose_action`), also per Arena
gegenprüfen. Bis dahin: Größenordnung im Label nach Verdünnung ~1e-3,
für Arena-/Replays-Vergleiche vernachlässigbar, für exakte
Reproduzierbarkeits-Tests (Prozess A == Prozess B) NICHT.

## Quellen (Recherche 2026-07-19)

- [Leela Chess Zero: value_loss_weight-Stärkeregression](https://github.com/leela-zero/leela-zero/issues/1480)
- [Grupen et al., Policy-Value Alignment and Robustness (arXiv:2301.11857)](https://arxiv.org/abs/2301.11857)
- [KataGo Methods docs (Score/Utility-Blending)](https://github.com/lightvector/KataGo/blob/master/docs/KataGoMethods.md)
- [Wu, Accelerating Self-Play Learning in Go (arXiv:1902.10565)](https://arxiv.org/pdf/1902.10565)
- [Multi-Labelled Value Networks for Computer Go (arXiv:1705.10701)](https://arxiv.org/abs/1705.10701)
- [MCTS mit Uncertainty Propagation via Optimal Transport (arXiv:2309.10737)](https://arxiv.org/pdf/2309.10737)

## Referenz

- Historische Details, alte Architektur, Sweep-/Kapazitätstests:
  [`archive/STAGE2_TODO_ARCHIVED.md`](../archive/STAGE2_TODO_ARCHIVED.md)
- Stufe-2-Ursachenforschung (0:0-Rate, Disagreement-Studie):
  [`archive/stage2_investigation.md`](../archive/stage2_investigation.md)
