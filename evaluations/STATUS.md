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

## Weitere zurückgestellte Punkte

- `ROUND_TRANSITION_SAMPLING` in der Live-Suche bleibt hinten angestellt,
  bis der Value-Head-Fix einen klaren Fortschritt zeigt.
- **Baustein B (zweistufiger Slot→Rotation-Suchknoten) weiterhin NACH
  der Value-Head-Reparatur** (Nutzer-Entscheidung 2026-07-19).
- round_transition_value-Daten-Skalierung (2000-3000 Spiele) bleibt
  hinten angestellt.

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
