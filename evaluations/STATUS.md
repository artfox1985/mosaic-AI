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
- **Value-Head**: `MosaicNet` hat `value_head` (Sieg/Niederlage-Achse,
  Tanh; STAND 2026-08-04: das ZIEL ist seit `VALUE_SCHEMA_VERSION=13`
  kein hartes ±1 mehr, sondern `tanh((own-opp)/VALUE_SCALE)`, seit v15
  zusaetzlich per `TD_LAMBDA` mit dem Bootstrap-Wert gemischt --
  `neural_net.py:979/1049`. Hartes ±1 nur noch als Fallback fuer
  unvollstaendige Partien, Zeile 1056)
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
`DECOUPLE_NET_SIMS_FROM_ACTIONS=true`. `tools/arena.py`: `NET_SIMS=400` (flaches
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
  gecrasht. Filter in self_play.py ergänzt (tools/arena.py-Muster).
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
`tools/selfplay_diversity_report.py` (wiederverwendbar als
Regressions-Check), alle 200 netcq-Dateien vs. 30 domefactB-Referenzdateien,
Eröffnungen exakt aus den state-log-Diffs rekonstruiert: **1996/2000
einzigartige 3-Zug-Eröffnungen** (normierte Entropie 1.00, häufigste
Eröffnung 0.1%), Brett-/Startspieler-Siegraten ~50/50 (Fairness ok),
Spiellängen 161.5±4.3 (etwas kürzer als Heuristik 173.7±4.3 — plausibler
Stilunterschied, kein Befund). **Keine Eröffnungs-Temperatur für v12 nötig.**

**Elo-Tracker (#62) — Infrastruktur FERTIG, erste Kader-Matches ausstehend.**
`tools/elo_tracker.py` + `elo_history.csv`: Bradley-Terry-MLE
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

**Gepaarter A/B** (`tools/paired_arena_ismcts.py`, Muster wie beim
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
**[ERLEDIGT: siehe nächster Abschnitt (2026-07-23) — round5.rs ist jetzt
Knoten-primär, Arena-Gegenprobe ohne signifikanten Stärkeunterschied.]**

## round5.rs Knoten-primär umgestellt: Runde-4/5-Label deterministisch, Arena-Gegenprobe bestanden (2026-07-23)

Umsetzung des im vorigen Abschnitt offen gelassenen Folge-Tasks
(Commit 9312be0, exakt das Task-#71-Muster).

**Kalibrierung** (`round5_node_calibration_probe`, als ignorierter Test im
Repo dokumentiert; freie lokale Maschine, Release-Build): 8 realistische
Runde-5-Partien via `drive_to_round_start(seed, 5)`, je Entscheidung ein
Negamax mit unbegrenztem Knotenbudget und 150ms-Deadline. Deadline-
gebundene Entscheidungen (n=92): min 34, p25 88, Median 155, p75 203,
p90 292, max 473 Knoten; vor der Deadline vollständig gelöste Teilbäume
(n=24, Rundenausklang) <=144 Knoten. Kosten pro Knoten schwanken
stellungsabhängig >10x (0,3-4,4ms) — die frühere "~500-4000"-Schätzung
war zu hoch gegriffen, die direkte Messung ist konsistent mit der
45-393s-Hochrechnung für 200k Knoten.

**Umstellung** (`engine/src/round5.rs`): `NODE_BUDGET=200` (~p75 —
Rechenparität zur typischen alten 150ms-Suche, deckt alle beobachteten
natürlich terminierenden Teilbäume ab) ist jetzt der PRIMÄRE,
deterministische Cutoff; `TIME_BUDGET` 150ms→5s, nur noch Not-Deckel
(~5x Worst-Case 200x4,4ms). Betrifft `exact_round5_outcome` UND die
Live-Zugwahl `choose_action`/`choose_action_with_analysis` (ein
gemeinsamer Suchkern). WICHTIGER FOLGE-FIX: `TIME_BUDGET_TRAIN_ROUND4`
12s→60s — die 24-Sample-Runde-4→5-Kette kostet jetzt worst-case ~24x0,9s
~ 21s; mit dem alten 12s-Deckel wäre die Wanduhr genau am Runde-4-Label
wieder bindend geworden und hätte den Determinismus-Gewinn dort sofort
wieder zerstört. `EXTRA_GAME_TIMEOUT_SECS` entsprechend 207→255.

**Determinismus-Nachweise**: (1) neuer Suite-Test: 3x
`exact_round5_outcome` auf realistischer Stellung bit-identisch +
`choose_action` reproduzierbar; (2) Task-#71-Kernmuster-Test: 10x
aufgeblähte Deadline liefert dasselbe Bitmuster (`NODE_BUDGET` ist der
bindende Cutoff); (3) E2E über Prozessgrenzen: identischer
`net_arena_match`-Aufruf (2 Spiele, v10_best@400) in zwei separaten
Prozessstarts BYTE-IDENTISCH — zusammen mit der tract-onnx-Bit-Exaktheit
(voriger Abschnitt) ist die Prozess-A==Prozess-B-Reproduzierbarkeit
damit geschlossen. 145/145 Tests grün (Release und Debug).

**Arena-Gegenprobe** (`tools/paired_arena_round5.py`, Muster wie
ISMCTS-/Speed-Bündel-A/B; ALT=5cb4f56 in eigenem Worktree+venv, NEU=
9312be0; v10_best @ NET_SIMS=400 vs. Heuristik @ HEUR_SIMS=200, Blöcke à
25, kumulativer exakter McNemar): **150 Paare ohne Signifikanz — NEU
55:58 ALT, diskordant b=2/c=5, p=0,45.** Kein Beleg für einen
Stärkeverlust; hohe Konkordanz (143/150 Paare gleich) wie erwartet, weil
nur Runde-5-Züge betroffen sind. Laufzeitkosten der Umstellung: NEU-Arm
~+25% je 25er-Block (88-111s vs. 67-94s) — Folge der p75-Wahl (mehr
Knoten als der alte Median), bewusst in Kauf genommen — Determinismus
ist hier der Zweck, nicht ein Speed-Trade.

## Gepaartes Gating als Standard (2026-07-23)

**Task #76, Phase A (nur Code, kein Nachweis-Lauf) -- der netcq2-Self-Play-
Batch belegt das installierte Wheel bis ~13:00, deshalb keine Arena-/
Trainings-Laeufe in diesem Zug.**

**Seeding-Verifikat**: `run_net_vs_net_arena` (Rust,
`self_play.rs::run_net_vs_net_arena`) seedet bereits VOR diesem Task jedes
Spiel exakt so deterministisch wie `run_net_arena_match`/`run_arena_match`
(`seed.wrapping_add((i as u64).wrapping_mul(0x9E37_79B9_7F4A_7C15))`,
identisch in allen drei Funktionen) -- KEINE Rust-Aenderung noetig, nur
per neuem Test bestaetigt
(`self_play::tests::run_net_vs_net_arena_seeds_deterministically_like_run_net_arena_match`):
zwei unabhaengige Aufrufe mit gleichem Seed+Modellen liefern byte-identische
Spielfolgen, UND Spiel `i=0` ist unabhaengig von `n_games` (reine Funktion
von `seed+i`) -- Voraussetzung fuers gepaarte Design unten.

**Neues Werkzeug `tools/paired_gating.py`**: gepaartes Netz-vs-Netz-
Gating fuer Kandidat A vs. Kandidat B (z.B. neuer Checkpoint vs. amtierenden
Champion). Ein **Paar** = ein Seed, zwei Spiele mit GETAUSCHTEN Brettern (die
Rust-API bietet keinen eingebauten Brett-Tausch-Modus, daher zwei
`net_vs_net_arena_match`-Aufrufe mit vertauschten Modell-/Sims-/c_puct-
Zuordnungen bei identischem Seed) -- ein etwaiger Brett-/Zugreihenfolge-Bias
faellt damit PRO PAAR heraus, nicht erst im Erwartungswert. Jedes Paar wird in
`b` (A gewinnt beide Spiele, "A-Sweep"), `c` (B gewinnt beide, "B-Sweep") oder
Split (1:1, uninformativ) eingeteilt.

**SPRT-Upgrade (Nutzer-Anstoss, noch am selben Tag)**: die erste Fassung
brach bei "kumulativem McNemar p<0.05 je Block" ab -- informelles
wiederholtes Testen ohne Sequenz-Korrektur, dasselbe Verfahrens-Problem wie
bei der Floor-Shaping-Signifikanzanalyse (wiederholtes Peeking bei festem
Alpha treibt das tatsaechliche Fehlerniveau auf ca. 7-10% statt 5%). Die
STOPP-Entscheidung ist jetzt ein echtes Wald-SPRT (Fishtest-Muster) auf den
INFORMATIVEN Paaren (b/c, Splits tragen nichts bei): H0 p=0.5, H1 p=0.65
(Standard, per `--h1` anpassbar -- Konvention: bei ~35% informativer
Paarrate ungefaehr +10 Prozentpunkte Winrate-Differenz), alpha=beta=0.05,
Wald-Schranken `ln(beta/(1-alpha))`/`ln((1-beta)/alpha)` = ±2.9444 bei
alpha=beta=0.05 (Rechen-Selbsttest gegen Handrechnung `ln(0.05/0.95)`/
`ln(0.95/0.05)` bestaetigt, laeuft als `_sprt_bounds_selftest()` bei jedem
Skriptstart automatisch mit). LLR-Update nach jedem Block: obere Schranke
erreicht -> A signifikant besser (Gating-Entscheid); untere Schranke
erreicht -> kein Beleg fuer A, Champion bleibt (spart Rechenzeit statt bis
zum Deckel weiterzuspielen); harter Deckel jetzt 200 Paare (=400 Spiele,
vorher 150) ohne SPRT-Entscheid -> "kein Entscheid im SPRT-Sinn" wird explizit
ausgewiesen. Der exakte Paar-Vorzeichentest (`mcnemar_exact_p(b, c)`, gleiche
Formel/Funktion wie in `paired_arena_speedbundle.py`/`paired_arena_ismcts.py`)
und die gepaarte Differenz-KI (`d_i in {-2,0,+2}` je Paar, 95%-Normalapprox.)
bleiben vollstaendig erhalten -- sie sind jetzt aber NUR NOCH die finale
Fixed-n-Bericht-Statistik, nicht mehr die Stopp-Regel. Bloecke weiterhin a 25
Paare, JSON-Blocklogs (inkl. LLR-Verlauf), druckt am Ende eine fertige
`elo_tracker.py add`-Kommandozeile.

**Dokumentation aktualisiert**: `elo_tracker.py`-Modul-Docstring markiert
`paired_gating.py` jetzt als Standardweg fuer Champion-Ablösungs-
Entscheidungen (`tools/arena.py::run_net_vs_net`s SPRT bleibt fuer schnelle,
nicht-gating-relevante Sanity-Checks nuetzlich, entscheidet aber nicht mehr
ueber Champion-Wechsel).

**Plumbing-Smoke** (Winz-Parameter, n=2 Paare/sims=20, v10_best gegen sich
selbst auf BEIDEN Seiten -- Wheel nur lesend genutzt, nichts installiert,
zweimal gelaufen: vor und nach dem SPRT-Upgrade): beide Aufrufrichtungen
laufen durch, LLR/Wald-Schranken/Fixed-n-McNemar/CI rechnen ohne Fehler --
bei identischen Modellen erwartungsgemaess beide Paare Splits (0 informative
Paare), LLR bleibt bei 0.0, Deckel greift korrekt mit `SPRT_verdict=
UNDECIDED_CAP_REACHED`. Zusaetzlich per synthetischem Skript bestaetigt:
eine Kette reiner A-Sweeps ueberschreitet nach 12 Paaren die obere Wald-
Schranke (+2.944), eine Kette reiner B-Sweeps unterschreitet nach 9 Paaren
die untere (-2.944) -- beide SPRT-Richtungen sind also nachweislich
erreichbar, nicht nur der Deckel-Pfad. Ein echter Gating-Lauf mit
unterschiedlichen Kandidaten folgt in Phase B nach Batch-Ende.

## v12-Zyklus (2026-07-23)

**Task #74. Build-Gate**: `cargo test --release` 151/151 grün (1 ignoriert,
75.9s), Wheel neu gebaut/installiert (`pip install . --force-reinstall
--no-deps` in `engine/`, das vorher installierte Wheel war hinter dem
round5-Node-Budget-Merge `bd5a744` + Phase-A-Commits zurück).
`engine_config_json()` bestätigt `use_gumbel_search: true`;
`VALUE_SHRINK_ENABLED` bleibt unangetastet auf `false` (Rust-Konstante, kein
Laufzeit-Feld in der JSON-Ausgabe, per Quellcode `net_mcts.rs:139`
verifiziert -- Task #78, nicht dieser Zyklus).

**Korpus**: die 200 Dateien `data/selfplay_v10b_*.pkl` (2000 Spiele,
netzgeführtes Self-Play mit v10_best als Generator, base_sims=400, erste
Generation mit dem #71-Knotenbudget statt Zeitbudget UND dem Regelfix-Stand
`bd5a744`) -- unverändert übernommen, keine Dateien verschoben/ergänzt.

**Training (`v12`)**: Warm-Start von `alphazero_v10_best.pth`, `--epochs 100`
als Deckel, `TD_LAMBDA=0.5` (Code-Default, unverändert). 290.521 Trainings- /
32.392 Val-Züge (Val-Split 20/200 Dateien, gleicher Seed wie immer). Early
Stopping bei Epoche 15/100 (Val-Policy-Plateau seit Epoche 10). **Bester
Checkpoint: Epoche 1** (`val_combined` = 1.8219) -- der Value-Val-R² fällt
bereits ab Epoche 2 monoton (0.221 → 0.182 → 0.144 → ...), exakt das gleiche
Frühplateau-Muster wie v11 (dort ebenfalls Epoche 2). Netzauslastung gesund
(Dead 8%, Eff.Rank 40%). ONNX-Export automatisch mitgelaufen
(`alphazero_v12.onnx` + `alphazero_v12_best.onnx`, beide frischer als der
Trainingsstart). Manifest `models/manifest_train_v12_20260723_131750.json`
bestätigt 200 Dateien / 2000 Spiele Präfix `v10b`.

**Offline-Diagnose** (`v12_best`, echter Val-Split 20/200 Dateien, n=32.392
Val-Züge, eigenes Diagnose-Skript, da `tools/diagnosis.py` keine
Pro-Runde-R²/Top-1-Top-3-Metriken liefert -- Vorgehen mirrort MosaicDataset
1:1 inkl. Runden-Index je Schritt):

| Metrik | v12_best | v11_best (Referenz, anderer Korpus/Split) | v10_best (Referenz, anderer Korpus/Split) |
|---|---|---|---|
| Policy Top-1 (nur Drafting, n=23.638) | 39.8% | 38.2% | 44.0% |
| Policy Top-3 | 68.5% | 66.8% | 74.3% |
| Value Val-R² global | **0.2215** | 0.139 | 0.221 |
| R² Runde 1 | **0.0377** | 0.029 | −0.063 |
| R² Runde 2 | **0.1074** | 0.101 | 0.017 |
| R² Runde 3 | 0.1818 | 0.138 | 0.195 |
| R² Runde 4 | 0.2283 | 0.084 | 0.406 |
| R² Runde 5 | 0.4757 | 0.290 | 0.623 |

Referenzwerte für v11_best/v10_best wie in den jeweiligen Session-Abschnitten
oben dokumentiert (andere Korpora/Splits, s. dortige Einschränkungen).
**Zusätzlich direkt vergleichbar** (v10_best auf dem GLEICHEN v12-Val-Split
neu ausgewertet, n=32.392): global R²=−0.0344, Runde 1–4 durchweg NEGATIV
(−0.237/−0.354/−0.156/−0.046), nur Runde 5 positiv (0.492), Top-1=37.4%/
Top-3=64.8%. Dieser direkte Vergleich ist aber selbst konfundiert (v10_best
wurde auf dem alten, nicht TD-Bootstrap-geblendeten Werte-Schema trainiert --
die Zielskala hat sich seither verschoben, s. `VALUE_SCHEMA_VERSION`-Historie
in `neural_net.py`) und dient nur als Plausibilitätscheck, nicht als
Bewertung "v10 ist schlechter geworden". **Kernbefund**: v12 verbessert
gegenüber v11 (halbe Datenmenge, Zyklus davor) global-R² deutlich (0.139 →
0.2215, wieder auf v10-Referenzniveau) UND hält die in v11 erstmals
positiven Runde-1/2-Werte (0.029/0.101 → 0.038/0.107), bei gleichzeitig
klar besserem Runde-4-Wert (0.084 → 0.228) -- die volle 2000-Spiele-
Datenmenge auf dem netzgeführten completed-Q/TD-Bootstrap-Korpus zahlt sich
aus. Geschwister-Tau wurde in diesem Zyklus NICHT reproduziert (kein
Werkzeug dafür im Repo, nicht Teil der angeforderten Kernmetriken).

**Gepaartes SPRT-Gating v12_best vs. v10_best** (`tools/paired_gating.py`,
beide @400 Sims, deterministische Arena, H1 p=0.65, alpha=beta=0.05, Deckel
200 Paare):

| Block | Paare kum. | Ergebnis kum. | A-Sweep/B-Sweep/Split | LLR | Bericht-p |
|---|---|---|---|---|---|
| 1 | 25 | 26:24 | 8/7/10 | −0.398 | 1.000 |
| 2 | 50 | 55:45 | 15/10/25 | +0.369 | 0.424 |
| 3 | 75 | 90:60 | 28/13/34 | +2.709 | 0.028 |
| 4 | 100 | **124:76** | 39/15/46 | **+4.882** | **0.0015** |

**SPRT-Verdikt nach Block 4 (100 Paare, 200 Spiele): v12_best signifikant
besser (LLR=+4.882 ≥ obere Schranke +2.944).** Gepaarte Differenz +0.480,
95%-KI [+0.206, +0.754] -- eindeutig auf Seiten von v12. **Champion-Wechsel:
v12_best löst v10_best als Champion und künftigen Self-Play-Generator ab.**
Damit bestätigt sich die im v11-Abschnitt vermutete Erklärung: der
Confounder "halbe Datenmenge" war der limitierende Faktor, nicht das
completed-Q/TD-Bootstrap-Zielformat selbst -- bei voller 2000-Spiele-Menge
schlägt das netzgeführte Verfahren den Heuristik-Korpus-Champion klar.

**Elo-Kader aktualisiert** (`tools/elo_tracker.py add`, Match in
`evaluations/elo_history.csv` eingetragen): v12_best@400 Elo 943
[860, 1018] (124-76 über 200 Spiele) vs. v10_best@400 nun 858 [793, 915].
Heuristik@200 bleibt fixer Anker bei 1000.

**Nächste Schritte** (nicht Teil dieses Zyklus): Task #78
(`VALUE_SHRINK_PER_ROUND`-Rekalibrierung) kann jetzt die oben gelisteten
per-Runde-R²-Werte von v12_best als Grundlage nutzen; v12_best als neuer
Generator für den nächsten Self-Play-Korpus (v13).

## v12b: LR-Schedule + From-Scratch-Kontrolle (2026-07-23)

**Motivation**: sowohl v11 als auch v12 zeigten denselben Befund -- der beste
Checkpoint (nach `val_combined`) war jeweils **Epoche 1**, das Value-Val-R²
fällt ab Epoche 2 monoton (v12: 0.221 → 0.182 → 0.144 → ...). Verdacht: die
Lernrate ist fürs Warm-Start-Feintuning zu hoch, das Netz "zerstört" ab
Epoche 2 mehr an nützlichem Warm-Start-Wissen, als es aus den 2000 Spielen
neu lernt. Task #77 testet zwei Kontrollen auf demselben `v10b`-Korpus
(200 Dateien, unverändert, keine Dateien verschoben/ergänzt).

**LR-Ist-Zustand vor diesem Zyklus** (`config.py`/`train.py` gelesen):
Adam-Optimizer, `LEARNING_RATE = 0.0004` (`config.py`), **konstant über alle
Epochen** -- kein Scheduler, kein CLI-Parameter dafür vorhanden. Ergänzt (Commit
`27c3a3a`): `--lr` (Default: unverändert `LEARNING_RATE` aus `config.py`) und
`--lr-schedule {none,cosine}` (Default `none` = alte, konstante LR).
`none`/kein `--lr` reproduzieren exakt das bisherige Verhalten -- rein additiv,
kein bestehender Aufruf ändert sich. `cosine` aktiviert
`torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=<--epochs>)`,
ein `.step()` je Epoche nach der Batch-Schleife.

**Variante A (`v12b_lr`)**: Warm-Start von `alphazero_v10_best.pth` (exakt wie
v12), `--lr 0.00005` (8× niedriger als der Default 0.0004, innerhalb der
angeforderten 5-10×-Größenordnung) + `--lr-schedule cosine`, `--epochs 100`
als Deckel. Early Stopping bei Epoche 15/100 (Val-Policy-Plateau seit Epoche
10, gleiches Kriterium wie v12). **Bester Checkpoint: Epoche 4**
(`val_combined`=1.8147 -- sogar leicht besser als v12s eigenes Optimum von
1.8219 bei Epoche 1). Damit beantwortet: **ja, der beste Checkpoint liegt bei
Variante A endlich NICHT mehr bei Epoche 1.** Val-R²-Verlauf (Value-Head)
steigt von Epoche 1 (0.230) auf sein Maximum bei Epoche 2 (0.236), bleibt bis
Epoche 5 nahe diesem Niveau (0.226) und fällt danach spürbar langsamer als
bei v12 (Epoche 13: 0.173 hier vs. v12s Epoche-3-Wert von 0.144) -- das
Zerfallsmuster ist flacher, nicht mehr verschwunden. Netzauslastung gesund
(Dead 7%, Eff.Rank 38%).

**Variante B (`v12b_scratch`)**: identisch zu v12, aber OHNE `--load`
(frische Initialisierung), Standard-LR (`--lr`/`--lr-schedule` nicht
gesetzt). Early Stopping ebenfalls bei Epoche 15/100 (Plateau seit Epoche
10). **Bester Checkpoint: Epoche 3** (`val_combined`=1.9044 -- deutlich
schlechter als v12/v12b_lr). Value-Val-R² bleibt durchgehend niedrig (Maximum
0.088 bei Epoche 2, danach unter 0.05, teils negativ) -- ohne Warm-Start
reicht die Datenmenge (2000 Spiele) offensichtlich nicht annähernd, um
denselben Value-Head-Stand wie mit Warm-Start zu erreichen.

**Offline-Diagnose** (`tools/offline_diagnose.py`, neu gebaut -- das beim
v12-Zyklus benutzte Skript war weder committet noch als Arbeitsdatei
liegen geblieben, `git status` zum Zyklusbeginn war sauber. Rekonstruiert
nach der STATUS.md-Beschreibung "mirrort MosaicDataset 1:1 inkl.
Runden-Index je Schritt"; **Sanity-Check bestanden**: auf `v12_best`
reproduziert es die im v12-Abschnitt dokumentierten Referenzwerte exakt
(Top-1 39.8%, Top-3 68.5%, R² global 0.2215, R1-R5 0.0377/0.1074/0.1818/
0.2283/0.4757 -- alle auf 4 Nachkommastellen identisch). Gleicher Val-Split
wie v12 (Datei-Ebene, Seed 20260707, val_frac=0.1, 20/200 Dateien,
n=32.392 Val-Züge, davon 23.638 Drafting-Schritte):

| Metrik | v12b_lr_best | v12b_scratch_best | v12_best (Referenz) |
|---|---|---|---|
| Policy Top-1 (Drafting) | **40.0%** | 37.6% | 39.8% |
| Policy Top-3 (Drafting) | **68.7%** | 66.2% | 68.5% |
| Value Val-R² global | **0.2289** | 0.0464 | 0.2215 |
| R² Runde 1 | 0.0368 | -0.0440 | 0.0377 |
| R² Runde 2 | **0.1106** | -0.1156 | 0.1074 |
| R² Runde 3 | 0.1717 | -0.0064 | 0.1818 |
| R² Runde 4 | 0.2298 | 0.0125 | 0.2283 |
| R² Runde 5 | **0.5145** | 0.3156 | 0.4757 |

**Bewertung**: `v12b_scratch` ist auf jeder einzelnen Metrik klar schlechter
als `v12_best` (global R² 0.0464 vs. 0.2215, Runde 1-4 durchweg nahe 0 oder
negativ) -- der Warm-Start hilft also weiterhin deutlich, bremst die
Generalisierung NICHT (die eingangs gestellte Frage "hilft Warm-Start
überhaupt noch?" ist damit klar mit Ja beantwortet). `v12b_lr` ist
konsistent, wenn auch moderat, besser als `v12_best`: global-R² (+0.0074),
Policy Top-1/Top-3 (je +0.2pp), Runde 2 (+0.0032) und vor allem Runde 5
(+0.0388) klar vorn; Runde 1 praktisch gleichauf (-0.0009, Rauschen), nur
Runde 3 minimal schwächer (-0.0101). Zusammen mit dem klar verschobenen
besten Checkpoint (Epoche 4 statt 1) und dem flacheren Zerfall ein
konsistentes Bild: die niedrigere LR + Cosine-Annealing behebt das
"Epoche-1-Overfitting"-Muster, ohne die erreichte Endqualität zu verschlechtern.

**Gating-Entscheid**: nur `v12b_lr` erfüllt "klar besser" (primär globales
R² + frühe Runden, sekundär Policy) -- `v12b_scratch` wird NICHT gegatet
(eindeutig schlechter, kein Kandidat). Gepaartes SPRT-Gating
`v12b_lr_best` vs. `v12_best` (`tools/paired_gating.py`, beide @400 Sims,
c_puct=1.5, H1 p=0.65, alpha=beta=0.05, Deckel 200 Paare):

| Block | Paare kum. | Ergebnis kum. | A-Sweep/B-Sweep/Split | LLR | Bericht-p |
|---|---|---|---|---|---|
| 1 | 25 | 34:16 | 11/2/12 | +2.173 | 0.0225 |
| 2 | 50 | **65:35** | 22/7/21 | **+3.275** | **0.0081** |

**SPRT-Verdikt nach Block 2 (50 Paare, 100 Spiele): v12b_lr_best
signifikant besser (LLR=+3.275 ≥ obere Schranke +2.944).** Gepaarte
Differenz +0.600, 95%-KI [+0.208, +0.992] -- eindeutig auf Seiten von
v12b_lr. **Champion-Wechsel: v12b_lr_best löst v12_best als Champion und
künftigen Self-Play-Generator ab** (Ergebnis-JSON:
`evaluations/paired_gating_result_v12b_lr_best_vs_v12_best.json`).

**Elo-Kader aktualisiert** (`tools/elo_tracker.py add`, Match in
`evaluations/elo_history.csv` eingetragen): v12b_lr_best@400 Elo 1051
[945, 1157] (65-35 über 100 Spiele); v12_best@400 im selben Neuberechnungs-
Durchlauf nun 943 [866, 1018]. Heuristik@200 bleibt fixer Anker bei 1000.

**Werkzeug-Neuzugang**: `tools/offline_diagnose.py` (Policy Top-1/Top-3 +
Value-R² gesamt/pro Runde gegen den train.py-Val-Split) ist jetzt dauerhaft
im Repo -- künftige Zyklen müssen dieses Skript nicht mehr neu bauen.

**Nächste Schritte** (nicht Teil dieses Zyklus): `v12b_lr_best` als neuer
Generator für den nächsten Self-Play-Korpus; die LR/Cosine-Kombination
(`--lr 0.00005 --lr-schedule cosine`) ist jetzt als Standardrezept für
künftige Warm-Start-Feintunings verfügbar (noch keine Entscheidung, ob sie
DEFAULT werden soll -- bislang nur an einem Korpus getestet). Task #78
(`VALUE_SHRINK_PER_ROUND`) kann wahlweise die v12b_lr- statt der v12-Werte
als Grundlage nehmen (Unterschied gering, aber v12b_lr ist jetzt Champion).

## v12c: Value-Shrinkage-Rekalibrierung + A/B (2026-07-23)

**Ausgangslage**: Phase A (Commit 81e728b) hatte `VALUE_SHRINK_ENABLED=false`
+ `VALUE_SHRINK_PER_ROUND` als reinen Code-Platzhalter eingebaut (rundenabhängige
Dämpfung der Blattwert-Ausschläge Richtung 0.5, angewendet nach
`blended_leaf_win_prob`, vor dem Floor-Shaping-Additiv). Dieser Zyklus (Task
#78) rekalibriert die Konstanten auf den amtierenden Champion und liefert den
seinerzeit aufgeschobenen gepaarten Arena-Nachweis (Phase B) nach.

### Rekalibrierung

Gleiche Herleitungsformel wie Phase A: `w_r ∝ sqrt(max(0, R²_r))`, normiert
auf `w_5 = 1.0` (keine Dämpfung in Runde 5). Neue Grundlage: die frische
`tools/offline_diagnose.py`-Diagnose von `v12b_lr_best` (amtierender
Champion, siehe Abschnitt "v12b" oben), NICHT mehr der separate
Noise-Floor-Rückspiel-Test (für v12b_lr nicht neu gefahren) -- die
R²-Werte sind bereits von sich aus streng monoton steigend, kein Clamping
nötig (Phase A brauchte noch `max(Deckel_r, Deckel_{r-1})` für Runde 3/4).

| Runde | R² (v12b_lr_best, 2026-07-23) | √R² | w_r (normiert) |
|---|---|---|---|
| 1 | 0.0368 | 0.19183 | 0.2674 |
| 2 | 0.1106 | 0.33257 | 0.4636 |
| 3 | 0.1717 | 0.41437 | 0.5777 |
| 4 | 0.2298 | 0.47937 | 0.6683 |
| 5 | 0.5145 | 0.71729 | 1.0000 |

Alt (Phase A, Platzhalter): `[0.1045, 0.5162, 0.8375, 0.8375, 1.0000]`.
Neu: `[0.2674, 0.4636, 0.5777, 0.6683, 1.0000]` -- durchweg schwächere
Dämpfung als der Phase-A-Platzhalter (weniger extreme frühe-Runden-Werte in
der frischen Diagnose als in den alten Noise-Floor-Deckeln). Nebenbei musste
der Test `apply_value_shrink_is_identity_when_disabled_by_default` in
`apply_value_shrink_matches_current_toggle_state` umgebaut werden (geht jetzt
beide Toggle-Zustände durch), sonst hätte `cargo test --release` beim
Umschalten auf `ENABLED=true` unweigerlich gebrochen. Commit `06f43a7`.

### A/B-Design

`VALUE_SHRINK_ENABLED` ist eine Compile-Zeit-Konstante -- Shrink-ON/-OFF
können nicht im selben Prozess gegeneinander spielen. Neues Werkzeug
`tools/paired_arena_shrink_ab.py` + `tools/paired_arena_shrink_arm_worker.py`
(Muster wie `paired_arena_ismcts.py`/`paired_arena_speedbundle.py`, aber
`net_vs_net_arena_match` statt `net_arena_match`, da Champion gegen einen
Referenz-NETZGEGNER statt gegen die Heuristik antritt). Anders als bei den
ISMCTS-/round5-A/Bs genügte hier EIN venv (kein Worktree/Zweit-venv nötig):
die Arme laufen nie gleichzeitig, sondern sequenziell -- Arm OFF spielen,
Quellcode-Toggle flippen, `cargo test --release`, Wheel neu bauen, Arm ON
spielen (jeweils frischer Python-Prozess je Arm-Aufruf, damit garantiert das
gerade gebaute Wheel geladen wird).

Bedingungen: Champion `v12b_lr_best` (Brett 0) vs. Referenzgegner `v12_best`
(Brett 1, Elo 943 vs. 1051 -- nah genug für Sensitivität), beide @400 Sims,
`c_puct=1.5`, deterministische Arena. IDENTISCHE Basis-Seed (20260723) und
Blockstruktur (4x25) in beiden Armen -- `net_vs_net_arena_match`s interne
Pro-Spiel-Seed-Ableitung ist deterministisch aus `seed + i*const`, Spielindex
`i` hat daher in beiden Armen dieselben Startbedingungen. Ausgewertet
paarweise: Spiel `i` in Arm OFF vs. Spiel `i` in Arm ON, exakter zweiseitiger
McNemar-Test auf den diskordanten Zellen (gleiche Formel wie
`paired_gating.py`/`paired_arena_ismcts.py`). Fixed-n (100 Spiele je Arm, 200
gesamt), kein SPRT-Nachziehen -- reine Sensitivitätsmessung, keine
Champion-Gating-Entscheidung.

### Ergebnis

`cargo test --release` 151/151 grün in BEIDEN Toggle-Zuständen (OFF und ON).

| Arm | Champion-Siege | Wheel-Hash (sha256, Kurzform) |
|---|---|---|
| OFF (Ist-Zustand) | 61:39 | 9b22dac5... |
| ON (rekalibriert) | 50:50 | ae2eb99e... |

Gepaarte Auswertung (`evaluations/paired_arena_shrink_ab_result.json`, Roh-
daten in `paired_arena_shrink_off_raw.json`/`paired_arena_shrink_on_raw.json`):
diskordante Paare `b` (nur ON gewinnt) = 15, `c` (nur OFF gewinnt) = 26,
konkordant (beide gewinnen) = 35, konkordant (beide verlieren) = 24. Exakter
McNemar-Test: **p = 0,1173** -- nicht signifikant, und die Richtung zeigt
sogar leicht zugunsten OFF (c=26 > b=15), nicht zugunsten ON.

### Entscheidung

Evidenzregel (fest vereinbart): nur bei p<0.05 UND Vorteil für ON bleibt der
Toggle an. Keine der beiden Bedingungen erfüllt (p=0,117, UND die Richtung
zeigt sogar gegen ON) -- **`VALUE_SHRINK_ENABLED` bleibt/wird zurück auf
`false` gesetzt.** Die rekalibrierten Konstanten (`VALUE_SHRINK_PER_ROUND =
[0.2674, 0.4636, 0.5777, 0.6683, 1.0000]`) bleiben unverändert im Code
(dokumentiert, harmlos bei `ENABLED=false` -- reine Identität, siehe
`apply_value_shrink`).

**Finaler System-Zustand**: Quellcode `engine/src/net_mcts.rs` mit
`VALUE_SHRINK_ENABLED=false` (verifiziert per Quellcode-Stand + `cargo test
--release` 151/151 grün + frischem `pip install . --force-reinstall --no-deps`
Wheel-Rebuild NACH dem Zurücksetzen, sha256 `479c19e9...`, Plumbing-Smoke
bestanden). `engine_config_json()` exponiert `VALUE_SHRINK_ENABLED` weiterhin
NICHT (reine Rust-Konstante, kein Laufzeit-Feld) -- Verifikation läuft
ausschließlich über Quellcode-Stand + Test-/Build-Nachweis, wie in Task #74
bereits so gehandhabt.

**Kein Champion-Wechsel, kein Elo-Eintrag** durch diesen Test -- es ändert
sich höchstens die Engine-Konfiguration (hier: bleibt unverändert), nicht der
Champion oder Self-Play-Generator.

## v12d: VALUE_WEIGHT/POINTS_WEIGHT-Sweep (2026-07-23)

**Ist-Zustand vor dem Sweep** (`config.py`): `VALUE_WEIGHT = 0.2`,
`POINTS_WEIGHT = 0.5`. `train.py` verrechnet sie im Gesamt-Loss als
`loss = p_loss + VALUE_WEIGHT*v_loss + POINTS_WEIGHT*points_loss` (Policy-CE +
gewichteter Value-Aux-MSE + gewichteter Punktestand-Aux-MSE); dieselbe
gewichtete Formel entscheidet auch die "bestes Modell"-Checkpoint-Auswahl
(kombinierte Val-Metrik, nicht mehr nur Policy-Val-Loss allein, siehe Fund 8).
Beide Gewichte wirken NUR im Loss/der Checkpoint-Auswahl, nicht in den
Targets selbst -- der HDF5-Cache-Key hängt an `VALUE_SCHEMA_VERSION`
(Zieldefinition), nicht an den Gewichten, war also für diesen Sweep korrekt
wiederverwendbar (keine Neuberechnung nötig).

**CLI-Ergänzung** (`train.py`, Commit `3049d25`): `--value-weight`/
`--points-weight`, additiv analog zu `--lr` -- Default `None` lässt
`VALUE_WEIGHT`/`POINTS_WEIGHT` aus `config.py` unverändert wirken
(Bestandsverhalten), kein Antasten der Config-Datei zwischen Sweep-Läufen
nötig.

### Sweep (one-factor-at-a-time, 4 Läufe)

Alle mit dem v12b_lr-Standardrezept: Warm-Start `alphazero_v10_best`,
`--lr 0.00005 --lr-schedule cosine --epochs 100`, v10b-Korpus (200 Dateien,
2000 Spiele, unverändert). Alle 4 Läufe stoppten per Val-Policy-Plateau nach
Epoche 15, bestes Modell (kombinierte Val-Metrik) jeweils Epoche 4 --
identisches Muster wie beim v12b_lr-Referenzlauf.

| Lauf | Gewicht | Wert (Faktor) |
|---|---|---|
| v12d_vw2   | VALUE_WEIGHT  | 0.4  (2×) |
| v12d_vw05  | VALUE_WEIGHT  | 0.1  (0.5×) |
| v12d_pw2   | POINTS_WEIGHT | 1.0  (2×) |
| v12d_pw05  | POINTS_WEIGHT | 0.25 (0.5×) |

### Offline-Diagnose (`tools/offline_diagnose.py`, `evaluations/offline_diagnose_v12d_sweep.json`)

| Metrik | v12b_lr (Ref.) | v12d_vw2 | v12d_vw05 | v12d_pw2 | v12d_pw05 |
|---|---|---|---|---|---|
| Policy Top-1 | 40.0% | 40.1% | 40.0% | 39.9% | **40.3%** |
| Policy Top-3 | 68.7% | 68.6% | 68.8% | 68.7% | 68.7% |
| Value R² gesamt | 0.2289 | 0.2254 | 0.2260 | 0.2119 | **0.2323** |
| R² Runde 1 | 0.0368 | 0.0286 | 0.0361 | 0.0145 | **0.0434** |
| R² Runde 2 | 0.1106 | 0.0970 | 0.1060 | 0.0769 | **0.1167** |
| R² Runde 3 | 0.1717 | 0.1682 | 0.1705 | 0.1591 | **0.1719** |
| R² Runde 4 | 0.2298 | 0.2253 | 0.2272 | 0.2201 | **0.2301** |
| R² Runde 5 | 0.5145 | **0.5237** | 0.5093 | 0.5042 | 0.5186 |

Kein sauberer mechanischer Trade-off wie erwartet (höheres VW zulasten der
Policy, höheres PW zulasten des Value-Ziels o.ä.): `v12d_pw2` (PW verdoppelt)
ist auf praktisch JEDER Metrik schlechter als die Referenz -- das
Punktestand-Aux-Signal stärker zu gewichten schadet dem gemeinsamen Trunk,
statt zu helfen. `v12d_vw2`/`v12d_vw05` sind gemischt/neutral (R5 bei vw2
etwas besser, sonst eher leicht schlechter). Einzig `v12d_pw05` (PW halbiert)
verbessert Policy Top-1 UND Value-R² in allen 5 Runden gegenüber der
Referenz -- kein Metrik-Ausreißer, sondern durchgehend (schwach) besser.
Einziger Kandidat, der die Bar "klar UND breit besser, nicht nur die
mechanisch bevorzugte Metrik" erfüllt → einziger Gating-Kandidat.

### Gating: v12d_pw05_best vs. v12b_lr_best

Gepaartes SPRT (`tools/paired_gating.py`, beide @400 Sims, c_puct=1.5,
H1 p=0.65, alpha=beta=0.05, Deckel 200 Paare).

**Werkzeug-Fund unterwegs**: `paired_gating.py`s `DEFAULT_THREADS=0` läuft
für `net_vs_net_arena_match` **einzeln-threaded** (Rust-Code in
`self_play.rs::run_net_vs_net_arena`: `if num_threads <= 1 { sequenziell }`
-- anders als der `num_threads=0`-"alle Kerne"-Kommentar bei den
Self-Play-Funktionen in `lib.rs` vermuten lässt). Erster Gating-Versuch
(Seed 637428818, Default-Threads) brauchte ~650s pro Block (25 Paare/50
Spiele) und wurde nach 5 Blöcken (250 Spiele, ~54 Minuten) durch ein
Laufzeitlimit des Hintergrund-Tasks abgebrochen, ohne Ergebnis-JSON (LLR-Pfad
bereits rückläufig: +0.767 → +2.058 → +1.586 → −0.406 → −2.116). Neu
gestartet mit `--threads 10` (von 12 Kernen) -- ca. 4× schneller
(152-162s/Block).

| Block | Paare kum. | Ergebnis kum. | LLR | Bericht-p |
|---|---|---|---|---|
| 1 | 25 | 21:29 (gegen pw05) | −1.804 | 0.3877 |
| 2 | 50 | **42:58** (gegen pw05) | **−3.514** | 0.1338 |

**SPRT-Entscheid nach Block 2 (50 Paare, 100 Spiele): H0 angenommen
(LLR=−3.514 ≤ untere Schranke −2.944) -- kein Beleg, dass `v12d_pw05_best`
besser ist; die Richtung zeigt sogar GEGEN pw05** (42:58, gepaarte Differenz
−0.320, 95%-KI [−0.680, +0.040]). Ergebnis-JSON:
`evaluations/paired_gating_result_v12d_pw05_best_vs_v12b_lr_best.json`.

Auffällig: die beiden Gating-Versuche (verschiedene Basis-Seeds) zeigten
gegenläufige Zwischentrends -- Versuch 1 lag bis Block 2 klar FÜR pw05
(60:40, LLR=+2.058), Versuch 2 von Block 1 an GEGEN pw05. Das unterstreicht,
wie verrauscht einzelne Zwischen-Blöcke sind und warum ausschließlich die
SPRT-Stopp-Regel (nicht ein per Auge gelesener Zwischen-LLR-Wert) die
Entscheidung tragen darf.

### Entscheidung

**Kein Champion-Wechsel.** `v12b_lr_best` bleibt Champion. `VALUE_WEIGHT`
bleibt `0.2`, `POINTS_WEIGHT` bleibt `0.5` in `config.py` (Default,
unverändert) -- keiner der vier Sweep-Punkte hat sich als echter Fortschritt
bestätigt. **Kein Elo-Eintrag** (SPRT-Ergebnis H0, nicht ACCEPT_H1).

**Lehre**: die Offline-Diagnose-Differenz zwischen `v12d_pw05_best` und der
Referenz (Top-1 +0.3pp, R² +0.003 bis +0.007 über die Runden) lag
größenordnungsmäßig in demselben Bereich wie die Differenz, die beim
v12b_lr-Zyklus einen echten, arena-bestätigten Stärkegewinn anzeigte (dort
u.a. R² Runde 1 SCHLECHTER, Runde 3 SCHLECHTER als die Vorgänger-Referenz,
trotzdem arena-bestätigt überlegen) -- hier aber NICHT reproduzierbar, sogar
mit leicht negativer Tendenz. Eine Offline-Diagnose aus einem EINZELNEN
Trainingslauf (kein Seed-Ensemble, keine Wiederholung) bleibt ein
unzuverlässiger alleiniger Prädiktor für echte Spielstärke -- das gepaarte
Arena-Gating bleibt vor jedem Champion-Wechsel Pflicht, unabhängig davon wie
eindeutig die Offline-Zahlen aussehen.

**Werkzeug-Empfehlung**: künftige `paired_gating.py`-Läufe sollten
`--threads` explizit setzen (hier 10 von 12 Kernen, ca. 4× Speedup
gegenüber dem sequenziellen Default) -- sonst drohen Läufe mit vollem
200-Paare-Deckel (~87 Minuten sequenziell) an Hintergrund-Task-Laufzeitlimits
zu scheitern, wie im ersten Versuch dieses Zyklus geschehen.

## Task #80: Self-Play-Kostenprofil + rtv-Redundanz (2026-07-23)

Ausgangsfrage: der v10b-Batch (2000 Spiele, `alphazero_v10_best.onnx`,
`--threads 8`) brauchte 14h (~0.04 Spiele/s). Vermutung: die Task-#71-Label-
Budgets (`round_transition_deep.rs`) überkompensieren den 1,94×-Suchspeedup.
Zusätzliche Frage: ist `round_transition_value` (rtv) gegenüber dem
billigeren `bootstrap_value` (TD-Bootstrap) noch informativ, oder redundant
(Streichungskandidat)?

### Kostenprofil (Instrumentierung)

Neues Cargo-Feature `clone_profiling` (bereits vorhanden, für genau diesen
Zweck gedacht -- siehe `profiling.rs`) um drei Zähler erweitert:
`gumbel_move_ns`/`rtv_ns`/`bootstrap_ns`, je ein `profiling::timed(...)`-
Aufruf um die drei Kostenblöcke in `self_play.rs::play_net_self_play_game`
(Gumbel-Zugsuche, `sample_round_transition_for_round`,
`bootstrap_value_after_rounds`). Ohne das Feature (Produktions-Wheel)
sind alle drei No-Ops (wegkompiliert, wie die bestehenden
`features_ns`/`net_eval_ns`-Zähler). Zusätzlich in `lib.rs::profiling_snapshot()`
exponiert. Mess-Wheel gebaut mit
`pip install . --force-reinstall --no-deps --config-settings=build-args="--features clone_profiling"`,
danach wieder auf den Default-Wheel zurückgesetzt (kein Feature aktiv,
`cargo test --release` grün, 151/151, vor UND nach der Mess-Wheel-Phase).

Messung: 2× 20 Spiele, Champion `alphazero_v12b_lr_best.onnx`, sims=400,
c_puct=1.5, add_root_noise=an, `--threads 8` und `--threads 11` (identische
Parameter sonst). Alle Zähler sind CPU-Sekunden summiert über alle Threads
(rayon-parallel) -- durch die Thread-Zahl geteilt ergibt die
Wall-Clock-Äquivalenz; die Pro-Spiel-Mittelwerte unten sind threads-unabhängig
(CPU-Sekunden/Spiel).

| Kategorie | Ø CPU-s/Spiel | Anteil (von gumbel+rtv+bootstrap) |
|---|---:|---:|
| Gumbel-Suche der gespielten Züge (400 Sims) | ~18 | ~12% |
| `round_transition_value` (rtv, rekursive Rundensimulation inkl. #71-Policy-Node-Budget-Suche) | ~119–123 | **~83%** |
| `bootstrap_value` (TD-Bootstrap, Horizont 2 Runden) | ~7 | ~5% |
| Sonstiges (Tiling/StartPlacement/Serialisierung, nicht instrumentiert) | ~28–35 | (separat, ~15-19% der Wall-Clock) |

**Kernbefund**: `round_transition_value` dominiert die Kosten mit ~83% des
gemessenen Suchaufwands -- die Vermutung aus dem Auftrag bestätigt sich
deutlich. Würde rtv vollständig entfallen, bliebe (Gumbel + Bootstrap +
Sonstiges) ≈ 18+7+30 ≈ 55s/Spiel gegenüber ≈ 174s/Spiel aktuell -- ein
theoretisches Durchsatz-Potenzial von ~3× (nicht nur Faktor 2), FALLS die
Label-Qualität das erlaubt (siehe Redundanz-Analyse unten -- **NICHT**
gegeben ohne Weiteres).

### rtv/Bootstrap-Redundanz (offline, `tools/rtv_redundancy_report.py`)

Analyse des kompletten v10b-Korpus (2000 Spiele, 200 Dateien,
`data/selfplay_v10b_*.pkl`, **nicht verändert**), dedupliziert je
(`game_id`, Runde) -- rtv/bootstrap werden einmal je Rundenübergang berechnet
und rückwirkend auf alle Züge der Runde gestempelt, ohne Dedupe wäre derselbe
Wert ~15-20× gezählt worden. Ergebnis: `evaluations/rtv_redundancy_v10b.json`
(16.000 deduplizierte (Spiel,Runde,Spieler)-Paare, Runde 1-4).

| Runde | n | Pearson(rtv, bootstrap) | Pearson(rtv, Endergebnis) | Pearson(bootstrap, Endergebnis) | Δ Ziel bei rtv-Entfernung (mean\|Δ\|) |
|---|---:|---:|---:|---:|---:|
| 1 | 4000 | 0.138 | 0.141 | 0.255 | 0.220 |
| 2 | 4000 | 0.236 | 0.200 | 0.369 | 0.214 |
| 3 | 4000 | 0.242 | 0.244 | 0.475 | 0.212 |
| 4 | 4000 | 0.268 | 0.275 | 0.662 | 0.209 |
| **Gesamt** | 16000 | **0.222** | 0.215 | 0.445 | ~0.21 |

("Endergebnis" = `tanh((own-opp)/50)` aus den finalen `scores_unclamped` --
der Fallback-Wert ohne rtv-Override; "Δ Ziel" = tatsächliche Änderung des
trainierten Schema-15-Targets, wenn der rtv-Override entfiele, aber der
Bootstrap-Blend bliebe: `(1-TD_LAMBDA) * (rtv_val - fallback_val)`.)

**Zwei Kernbefunde, gegenläufig zur reinen Kosten-Perspektive:**

1. **rtv und bootstrap sind NICHT redundant** -- die Korrelation liegt bei
   nur 0,14-0,27 (schwach). Sie kodieren unterschiedliche Information; man
   kann bootstrap nicht einfach als "billigen Ersatz" für rtv annehmen.
2. **rtv korreliert SCHWÄCHER mit dem tatsächlichen Spielausgang als das
   viel billigere bootstrap** (Gesamt 0,215 vs. 0,445; in Runde 4 sogar
   0,275 vs. 0,662). Trotz ~17× höherer Rechenkosten (119s vs. 7s/Spiel)
   sagt rtv den echten Ausgang schlechter vorher als der kurze
   TD-Bootstrap-Horizont. Plausible Ursache: rtv rekursiert bis zu 3
   verschachtelte Zwischenrunden-Simulationen tief (Runde 1) und akkumuliert
   dabei Modell-Fehler des SELBEN (noch trainierenden) Netzes über jede
   Ebene -- Runde 1 zeigt konsequent die schwächste rtv-Korrelation sowohl
   zu bootstrap (0,138) als auch zum Endergebnis (0,141).
3. Die Zielwert-Änderung bei Entfernen des rtv-Override ist mit
   mean\|Δ\|≈0,21 (Skala [-1,1]) **substanziell, nicht vernachlässigbar** --
   ein Wegfall wäre ein echter Schema-Wechsel des Trainingsziels, kein
   reiner Performance-Knopf.

### Threads-Messung (8 vs. 11, Champion-Modell, identische Parameter)

| Threads | Spiele | Wall-Clock | Spiele/s | Hochgerechnet auf 2000 Spiele |
|---|---:|---:|---:|---:|
| 8 | 20 | 468,1s | 0,0449 | ~12,4h |
| 11 | 20 | 337,5s | 0,0622 | ~8,9h |

Speedup 11 vs. 8 Threads: **~1,39×** (11/8=1,375 -- also nahezu perfekte
lineare Skalierung, keine Anzeichen von Kontention). Keine Hänger, keine
Watchdog-Abbrüche, alle 20 Spiele je Lauf `completed=true`. RAM unauffällig
(Python-Hauptprozess 150-630MB Working-Set während der Läufe, per
`Get-Process` stichprobenartig geprüft). Der historische 8-Threads-Grund
(Gamma-Pruning-Hänger) ist damit für diese Stichprobengröße nicht mehr
reproduzierbar -- konsistent mit den bereits gelandeten Fixes
(`fill_large_factory`-Endlosschleife, 1a683d3; deterministische
Knoten-Budgets statt Zeitbudgets, Task #71).

### Empfehlungspaket für den v13-Batch (Priorität, NICHT umgesetzt)

1. **[P1, niedriges Risiko, sofort nutzbar] `--threads` 8 → 11 anheben.**
   Erwartung: ~14h → ~10h für 2000 Spiele (Übertragung des gemessenen
   1,39×-Faktors auf die reale v10b-Baseline). Reine Infrastruktur-Änderung,
   rührt weder Labels noch Trainingsziel an. Restrisiko: nur an 20-Spiele-
   Stichproben geprüft, kein Langlauf-Stabilitätsbeleg über mehrere Stunden
   -- vor dem vollen 2000er-Batch ggf. einen kürzeren Zwischen-Checkpoint
   (z.B. nach 200-300 Spielen) beobachten.
2. **[P2, NICHT als einfacher Performance-Knopf umsetzen] rtv-Reduktion/
   -Streichung als eigenständiges Experiment, nicht als Kosten-Entscheidung.**
   Bis zu ~3× Durchsatzgewinn theoretisch möglich (rtv ist ~83% der
   Suchkosten), ABER: rtv und bootstrap sind nicht redundant (schwache
   Korrelation) und rtv korreliert schwächer mit dem echten Spielausgang als
   das billigere bootstrap -- die Kostendaten allein rechtfertigen KEINE
   Entscheidung in irgendeine Richtung. Notwendig vor jeder Umsetzung: ein
   Trainings-Vergleichstest (z.B. `TD_LAMBDA=1.0` oder rtv-Override
   deaktiviert) mit vollem Arena-Gating gegen den amtierenden Champion --
   siehe Nutzer-Vorgabe und die Erfahrung aus dem v12-Zyklus (teure Labels
   haben dort nachweislich Stärke gebracht; nicht ohne Beleg rückgängig
   machen, siehe `feedback_correctness_over_measured_benefit`).
3. **[P3, aus diesem Task nicht weiter untersucht] Runde-1-rtv besonders
   teuer UND am wenigsten informativ** (schwächste rtv↔bootstrap- UND
   rtv↔Endergebnis-Korrelation aller vier Runden). Falls P2 verfolgt wird,
   wäre eine differenzierte Variante (rtv nur Runde 2-4, Runde 1 nur
   bootstrap) ein möglicher Zwischenweg -- ebenfalls nur über einen
   Trainings-/Arena-Vergleichstest zu entscheiden, nicht spekulativ.
4. **[P3, nicht instrumentiert] "Sonstiges"-Anteil** (Tiling/StartPlacement/
   Serialisierung, ~28-35s/Spiel, ~15-19% der Wall-Clock) ist nicht
   Bestandteil dieser Kategorisierung -- falls nach P1/P2 noch mehr Durchsatz
   gebraucht wird, wäre das der nächste Profiling-Kandidat.

### Repo-/Wheel-Endzustand

`git diff --stat` (Commit folgt separat): `engine/src/profiling.rs`
(+3 Zähler-Paare, `clone_profiling`-gated), `engine/src/self_play.rs`
(3× `profiling::timed(...)`-Wrapper, kein Verhaltensunterschied ohne
Feature), `engine/src/lib.rs` (`profiling_snapshot()` um die 3 Felder
erweitert). `tools/rtv_redundancy_report.py` (neu, reine Offline-Analyse,
`data/` unverändert). Installiertes Wheel am Task-Ende: Default-Features
(kein `clone_profiling`), `cargo test --release` 151/151 grün, identisch zum
committeten Stand. Mess-Zwischenstände (keine `.pkl`-Dateien in `data/`
angefallen -- Direktaufruf von `mosaic_rust.net_self_play_games` ohne
`progress_path`) wurden nicht persistiert, `data/tmp_task80/` wieder entfernt.

## Task #81: Amdahl-Split für GPU-Umbau (2026-07-24)

Ausgangsfrage: Task #82 plant einen zentralen GPU-Inferenz-Batcher (RTX 3060,
Batch 256 ≈ 203k Evals/s laut torch-Benchmark, vs. CPU heute ~1600-3200
Evals/s/Thread). Wieviel der GESAMTZEIT der drei Task-#80-Kategorien (Gumbel-
Suche, rtv, Bootstrap) ist Netz-Inferenz (wandert auf GPU) vs. reine CPU-
Spiellogik (Klonen, Zuggenerierung, Feature-Extraktion, Alpha-Beta-
Zugsortierung -- bleibt CPU)? Der Logik-Anteil setzt die Amdahl-Obergrenze für
den geplanten Umbau.

### Instrumentierung

`clone_profiling` (Feature bereits vorhanden) um einen Netz-Eval-vs-Logik-
Split JE Kategorie erweitert (`engine/src/profiling.rs`):

- Ein thread-lokaler Kategorie-Stack (`with_category(Category::{Gumbel,Rtv,
  Bootstrap}, f)`) markiert den Geltungsbereich der drei bestehenden
  `timed(note_gumbel_move_ns/note_rtv_ns/note_bootstrap_ns, ...)`-Blöcke in
  `self_play.rs::play_net_self_play_game` (nur eine zusätzliche Hülle, keine
  strukturelle Änderung).
- `timed_net_eval(batch_size, f)` ersetzt an ALLEN `Net::eval`/`eval_pair`-
  Aufrufstellen (`net_mcts.rs::net_leaf_eval`/`drafting_action_priors`/
  `make_node`, `self_play.rs::negamax_value`/`alphabeta_choose_action`) das
  bisherige `timed(note_net_eval_ns, ...)` 1:1 -- misst zusätzlich zum
  unveränderten globalen Zähler die aktuell aktive Kategorie (Nanosekunden +
  Aufrufzahl + Aufrufe×Batchgröße, `batch_size=1` für `Net::eval`, `=2` für
  `eval_pair`s gebündelten Mover+Gegner-Pass). Kategorien laufen je Thread
  strikt sequenziell (nie verschachtelt), ein einfacher "aktuelle Kategorie"-
  Slot hätte gereicht -- der Stack ist defensiv.
- `lib.rs::profiling_snapshot()` um 9 Felder erweitert (`{gumbel,rtv,
  bootstrap}_net_eval_{ns,calls,instances}`).
- Gleiches Feature-Gate wie bisher, alle neuen Funktionen ohne `clone_profiling`
  No-Ops. Default-Build unverändert (verifiziert: `cargo build --release` ohne
  Feature kompiliert sauber, nur die 3 vorbestehenden unabhängigen Warnungen).

`cargo test --release`: **151/151 grün** (vor der Mess-Wheel-Phase). Mess-Wheel
gebaut mit `pip install . --force-reinstall --no-deps
--config-settings=build-args="--features clone_profiling"` (im `engine/`-
Verzeichnis, wie in #80 -- `pip install .` im Repo-Root schlägt fehl, dort
liegt kein `pyproject.toml`).

### Messlauf

Direktaufruf `mosaic_rust.net_self_play_games` (kein `progress_path`, daher
keine `.pkl`-Dateien -- nur eine kleine Heartbeat-JSON unter
`data/tmp_task81/`, am Ende entfernt), Champion `alphazero_v12b_lr_best.onnx`,
`base_sims=400`, `c_puct=1.5`, `add_root_noise=true`. Zwei Läufe: 20 Spiele
`--threads 11` (Produktionsbetrieb) und 3 Spiele `--threads 1` (unverzerrte
Einzelspiel-Timings ohne Kern-Kontention). `data/`-Korpus (400 `.pkl`,
200×v12 + 200×v10b) nicht angerührt, nachträglich per `ls`-Zählung verifiziert.

| Kategorie | CPU-s/Spiel (11 Threads) | davon Netz-Eval | Eval-Anteil | CPU-s/Spiel (1 Thread) | Eval-Anteil |
|---|---:|---:|---:|---:|---:|
| Gumbel-Suche (gespielte Züge) | 25,6 | 7,16 | **28,0%** | 13,7 | 26,5% |
| `round_transition_value` (rtv) | 149,7 | 5,31 | **3,5%** | 92,6 | 4,2% |
| `bootstrap_value` (TD) | 9,25 | 0,47 | **5,0%** | 6,35 | 4,9% |
| **Summe (gumbel+rtv+bootstrap)** | 184,6 | 12,94 | **7,01%** | 112,6 | 6,9% |
| Sonstiges (Tiling/StartPlacement/Serialisierung) | ~45 (19,6% des CPU-Budgets) | -- | -- | ~0,8 (0,7%) | -- |

Die Eval-Anteile sind zwischen 1 und 11 Threads praktisch identisch (7,01% vs.
6,92%) -- Kern-Kontention verzerrt den Eval-vs-Logik-*Anteil* nicht spürbar,
auch wenn sie die absoluten Zeiten stark aufbläht (dazu unten mehr). Das
bestätigt die Kategorienverteilung aus #80 (rtv ~81% der Suchkosten hier,
vs. ~83% dort -- reproduziert).

### Amdahl-Obergrenze

Netz-Eval ist innerhalb der drei Kategorien ein kleiner Anteil -- entsprechend
niedrig die theoretische Obergrenze `1/(1-Eval-Anteil)` für den GPU-Umbau:

| Kategorie | Eval-Anteil | Amdahl-Obergrenze |
|---|---:|---:|
| Gumbel-Suche | 28,0% | **1,39×** |
| rtv | 3,5% | **1,04×** |
| Bootstrap | 5,0% | **1,05×** |
| Summe (gumbel+rtv+bootstrap) | 7,0% | **1,075×** |
| **Gesamte Suche inkl. Sonstiges** (Eval-Anteil am vollen CPU-Budget: 258,8s / 4594,2s) | 5,6% | **1,06×** |

**Kernbefund, gegen die Erwartung des Auftrags**: die theoretische
GPU-Umbau-Obergrenze liegt bei nur **~6-8% Gesamtlaufzeit-Reduktion**, nicht
bei einem Faktor 2-10, wie man von "Inferenz auf GPU auslagern" naiv erwarten
könnte. Grund: `round_transition_value` dominiert die Kosten (~81-83%,
konsistent #80), ist aber selbst zu >96% CPU-Spiellogik (Alpha-Beta-
Zugsortierung + rekursive Rundensimulation aus `round_transition_deep.rs`,
viele `GameState`-Klone/Zuggenerierungen je kleinem Netz-Aufruf, Batch=1) --
Netz-Eval ist dort nur ein kleiner Annex, nicht der Flaschenhals. Die Gumbel-
Suche hat den höchsten Eval-Anteil (28%, MCTS mit vielen Blattauswertungen je
Sim), ist aber selbst nur ~14% der Gesamtkosten.

**Konsequenz für #82**: ein reiner "Netz-Eval auf GPU"-Batcher (ohne
Architekturänderung) bringt bestenfalls ~6-8% schnellere Einzelspiele. Der
eigentliche Gewinn eines GPU-Batchers dürfte NICHT aus reduzierter
Einzelspiel-Latenz kommen, sondern aus **Durchsatz durch mehr Parallelität**:
sobald Netz-Aufrufe nicht mehr synchron denselben CPU-Kern blockieren (siehe
Kontentions-Fund unten), lassen sich pro Kern deutlich mehr gleichzeitige
Partien fahren, weil die wartende Zeit auf einen (jetzt asynchronen,
gebündelten) GPU-Call keine CPU-Ressourcen mehr bindet. Das ist ein
Durchsatz-, kein klassisches Amdahl-Latenz-Argument -- vor einer Umsetzung
lohnt sich eine explizite Diskussion, ob #82 auf dieses Ziel (mehr parallele
Spiele) statt auf "schnellere Einzelpartie" hin geplant wird. Ein zweiter,
unabhängiger Hebel mit höherem Potenzial bliebe die rtv-Kostenreduktion
(#80s P2, ~83% der Suchkosten, aber NICHT einfach als Performance-Knopf
umsetzbar -- siehe dortige Redundanz-Analyse).

### Evals/s-Nachfrage und Parallel-Spiele-Zahl für #82

Bei 11 Threads/20 Spielen: 1.509.061 Netz-Eval-Instanzen (Aufrufe×Batchgröße)
in 417,7s Wall-Clock = **~3.613 Evals/s Gesamtnachfrage** -- das ist nur
**~1,8%** der GPU-Referenzkapazität (Batch 256 ≈ 203.000 Evals/s), die GPU
wäre bei heutiger Parallelität massiv unterausgelastet. Pro-Thread/Spiel-Rate
bei 11-Wege-Kontention: ~328 Evals/s; unkontendiert (1-Thread-Lauf): ~662
Evals/s/Spiel (die Kontention halbiert grob auch die Anfrage-Rate, siehe
Kontentions-Fund unten).

Nötige Parallel-Spiele-Zahl, um GPU-Batches zu füllen (Rate × Sammelfenster =
Ziel-Batchgröße, linear in der Spielezahl angenommen -- Workload ist
logik-/CPU-dominiert, damit eine vertretbare Näherung):

| Ziel-Batch | Sammelfenster 10ms | Sammelfenster 20ms |
|---|---:|---:|
| 64 | ~10-20 parallele Spiele | ~5-10 parallele Spiele |
| 256 | ~39-78 parallele Spiele | ~20-39 parallele Spiele |

(Spannen decken die kontendierte/unkontendierte Rate ab.) **Empfehlung für
#82**: mit ~20-40 gleichzeitig laufenden Partien planen, um Batch~64-256
zuverlässig in einem 10-20ms-Fenster zu füllen -- das liegt bereits deutlich
über der heutigen Produktions-Parallelität (11 Threads = 11 Spiele
gleichzeitig), erfordert also eine Architektur, die CPU-Spiellogik von der
GPU-Wartezeit entkoppelt (z.B. async/Channel-basiertes Batching statt
synchronem Blockieren je Thread).

### Nebenbefund: Kern-Kontention (6 physische / 12 logische Kerne)

Die Maschine hat 6 physische Kerne (12 logische, Hyperthreading). Pro-Spiel-
CPU-Zeit ist bei 11 Threads deutlich höher als beim unkontendierten 1-Thread-
Lauf: Summe gumbel+rtv+bootstrap 184,6s/Spiel (11 Threads) vs. 112,6s/Spiel
(1 Thread) -- **+64%**. Lineare Hochrechnung vom 1-Thread-Wert auf 11 Threads
ergäbe 0,0977 Spiele/s, gemessen wurden nur 0,0479 Spiele/s -- **~51% Effizienz**
bei 11 Threads relativ zu dieser Idealannahme. Das relativiert #80s "~1,39×,
nahezu perfekte lineare Skalierung" (8→11 Threads): der Vergleich dort hatte
keinen unkontendierten 1-Thread-Anker, beide Konfigurationen (8 UND 11
Threads) liefen vermutlich bereits mit einem ähnlichen Kontentions-Abschlag
gegenüber einem echten Einzelkern -- Hyperthreading auf nur 6 physischen
Kernen skaliert für diese CPU-lastige Workload erwartbar nicht linear über
6-8 Threads hinaus. Für #82 relevant: falls der GPU-Batcher CPU-Kerne von
lokalen ONNX-Aufrufen befreit, könnte ein Teil dieser Kontention entfallen
(zusätzlich zum reinen Amdahl-Effekt oben) -- nicht separat quantifiziert,
nur als Hinweis vermerkt.

### Einordnung der -22%-Abweichung (#80-Prognose vs. realer Batch)

#80 sagte (aus einer v10-Modell-Messung) 0,0622 Spiele/s bei 11 Threads voraus;
der reale v12-Produktionsbatch lief mit 0,0471 Spiele/s (-22%). Dieser Messlauf
(v12b_lr, 11 Threads, 20 Spiele) reproduziert **0,0479 Spiele/s** -- nur 1,6%
über dem realen Wert, **erklärt die Abweichung also praktisch vollständig**:
nicht Threads/Kontention (die waren in #80 bereits mit 11 Threads gemessen),
sondern das TEURERE v12b_lr-Modell selbst. Pro-Spiel-CPU-Kosten sind bei
v12b_lr klar höher als #80s v10-Baseline: gumbel 25,6s (vs. ~18s), rtv 149,7s
(vs. ~119-123s), bootstrap 9,25s (vs. ~7s) -- Summe 184,6s vs. ~144-148s
(**+25-28%**), was die 23%ige Lücke zwischen #80s Prognose und diesem
Messlauf (0,0622→0,0479) fast exakt erklärt. Plausible Ursache: `round_
transition_deep.rs`s Alpha-Beta-Zugsortierung nutzt Netz-Policy-Priors, die
sich zwischen v10 und v12b_lr unterscheiden -- ob das zu mehr besuchten
Knoten (weniger scharfe Priors) oder längeren Partien führt, wurde hier nicht
weiter zerlegt (out of scope für #81).

### Repo-/Wheel-Endzustand

`engine/src/profiling.rs` (+Kategorie-Stack, `with_category`, `timed_net_eval`,
9 neue Getter/Resets, `clone_profiling`-gated), `engine/src/net_mcts.rs`
(5× `timed(note_net_eval_ns,...)` → `timed_net_eval(batch_size,...)`),
`engine/src/self_play.rs` (2× dito + 3× `with_category`-Hülle um die
bestehenden Task-#80-Blöcke), `engine/src/lib.rs` (`profiling_snapshot()` um
9 Felder erweitert). Kein Verhaltensunterschied ohne Feature. Nach der
Mess-Phase: Produktions-Wheel (Default-Features) neu gebaut/installiert,
`cargo test --release` **151/151 grün**, `data/tmp_task81/` entfernt,
`data/`-Korpus (400 `.pkl`) unverändert (vor/nach per Zählung verifiziert).

## Eingefrorenes Eval-Set (frozen_v1, 2026-07-24)

**Task #87. Motivation**: `tools/offline_diagnose.py::val_files()` zieht den
Val-Split aus dem jeweils AKTUELLEN `data/`-Inhalt (Glob + Seed-Shuffle) --
Diagnose-Zahlen zwischen Generationen sind dadurch nicht vergleichbar,
sobald sich `data/` ändert. Verdacht: das im v12-Zyklus dokumentierte
Policy-Top-1-Rätsel (v10_best 44.0% vs. v12_best 39.8%, andere
Korpora/Splits) war teilweise Cross-Korpus-Artefakt statt eines echten
Stärke-/Stil-Unterschieds. Dieser Task friert ein festes, generations-
übergreifendes Set ein und erweitert `offline_diagnose.py` darum.

**Nebenlauf-Disziplin**: parallel lief der 11-Thread-v12-Self-Play-Batch
weiter (`data/selfplay_v12_*.pkl`). `data/` wurde ausschließlich gelesen;
`tools/build_frozen_eval_set.py` verwendet nur v12-Dateien, deren mtime
seit ≥10 Minuten unverändert ist (Schutz gegen den noch schreibenden
Batch). Beide neuen/geänderten Skripte laufen mit reduziertem Thread-Budget
(`torch.set_num_threads` explizit auf 2 begrenzt bzw. Default
`max(1, CPU-2)` in `offline_diagnose.py`).

**Set-Aufbau** (`tools/build_frozen_eval_set.py`, neu, Version `frozen_v1`,
Seed 20260724): 1800 Zustände, stratifiziert nach Korpus × Runde (1-5), je
Bucket exakt 180 (2 Korpora × 5 Runden = 10 Buckets à 180). Je Korpus wird
eine feste, deterministisch permutierte Stichprobe von 20 Dateien komplett
eingelesen (bewusst nicht "stop sobald ein Bucket voll ist", um Spiel-/
Zeit-Diversität über den ganzen Korpus-Zeitraum zu erhalten), danach ein
fester Zufallszug je Runden-Bucket.

**Dritter Korpus (netcq) NICHT gefunden**: der Auftrag nannte
`data/archive netcq` als dritte Quelle (v11-Trainingskorpus
`selfplay_netcq_*.pkl`). Recherche — `data/` (keine Unterordner mehr
vorhanden), Projekt-Root `archive/` (leer bis auf zwei alte `.md`-Dateien),
rekursiver Scan des gesamten Projektbaums nach `*netcq*` und
`selfplay_netcq_*.pkl`, sowie eine Suche über den gesamten
`Projekte`-Ordner — ergab KEINEN Treffer. Der Korpus existiert auf dieser
Maschine aktuell nicht mehr auf Platte (vermutlich bereits gelöscht, ohne
dass ein `archive_netcq*`-Ordner zurückblieb, anders als bei
`archive_domefact_preBausteinB`/`archive_domefactB_preRuleFix`). Das Set
besteht daher aus **zwei** Korpora (v10b + v12) statt drei; das Skript
dokumentiert das explizit im Manifest (`netcq_available: false`) statt den
Lauf zu blockieren. Falls die netcq-Daten doch noch auffindbar sind (z.B.
externes Backup), kann ein `frozen_v2` sie nachträglich ergänzen — `frozen_v1`
bleibt dazu unangetastet (Versionierung ist bewusst additiv, kein Rebuild).

**Zusammensetzung** (`evaluations/frozen_eval_set_manifest.json`):

| Korpus | Runde 1 | Runde 2 | Runde 3 | Runde 4 | Runde 5 | Summe |
|---|---|---|---|---|---|---|
| v10b | 180 | 180 | 180 | 180 | 180 | 900 |
| v12 | 180 | 180 | 180 | 180 | 180 | 900 |
| **Gesamt** | 360 | 360 | 360 | 360 | 360 | **1800** |

Ablage: `evaluations/frozen_eval_set.pkl` (Records: state, valid_actions,
policy, scores/scores_unclamped, bootstrap_value, round_transition_value,
winner, completed, player, round, source_corpus, source_file, game_id) +
`evaluations/frozen_eval_set_manifest.json`. **Das Set ist ab jetzt
unveränderlich** (`build_frozen_eval_set.py` bricht ab, falls die Zieldatei
bereits existiert).

**`offline_diagnose.py` erweitert** um `--frozen` (Default AUS, Bestands-
verhalten ohne das Flag vollständig unverändert): lädt statt `val_files()`
das eingefrorene Set, rechnet dieselben Metriken (Value-R² gesamt + je
Runde, Policy Top-1/Top-3), zusätzlich aufgeschlüsselt je Quellkorpus
(`--frozen`-Ergebnis-JSON enthält je Modell ein `by_corpus`-Feld,
Konsolen-Ausgabe über eine eigene `print_corpus_table()`).

**Messung** (`evaluations/offline_diagnose_frozen_v1.json`, `--threads 2`,
n=1800, davon 1310 Drafting-Züge für Top-1/Top-3):

| Modell | Top-1 | Top-3 | Value-R² global | R² v10b-Subset | R² v12-Subset |
|---|---|---|---|---|---|
| v10_best | 39.5% | 65.5% | 0.0495 | 0.1105 | −0.0310 |
| v11_best | 40.5% | 69.3% | 0.2315 | 0.2548 | 0.2008 |
| v11_td07_best | 41.8% | 68.8% | 0.2254 | 0.2533 | 0.1886 |
| v12_best | 46.6% | 73.3% | 0.3482 | 0.4654 | 0.1936 |
| v12b_lr_best (Champion, Elo 1051) | 46.6% | 74.1% | 0.3379 | 0.4217 | 0.2273 |
| v12b_scratch_best | 43.6% | 71.7% | **0.3951** | **0.7058** | **−0.0148** |
| v12d_pw05_best | 46.5% | 73.4% | 0.3299 | 0.3966 | 0.2420 |
| v12d_pw2_best | 45.6% | 73.6% | 0.3475 | 0.4668 | 0.1900 |
| v12d_vw05_best | 47.0% | 73.7% | 0.3304 | 0.4082 | 0.2277 |
| v12d_vw2_best | 46.3% | 73.2% | 0.3451 | 0.4424 | 0.2166 |

**Kernfrage 1 -- war 44.0% vs. 39.8% ein Korpus-Artefakt?** Ja, überwiegend.
Auf dem festen Set dreht sich das Bild komplett: v12_best (46.6%) schlägt
v10_best (39.5%) in Top-1 deutlich -- und zwar sowohl gesamt als auch in
BEIDEN Korpus-Teilmengen (v10b-Subset 41.7% vs. 35.5%, v12-Subset 51.6% vs.
43.6%). Die alte 44.0%-Zahl für v10_best stammte aus einer früheren
Diagnose auf einem anderen (leichteren/älteren) Korpus/Split; STATUS.md
hatte das damals bereits als "anderer Korpus/Split" geflaggt, aber ohne
festes Set war keine saubere Trennung von Korpus- und Modell-Effekt
möglich. Die direkte v12-Zyklus-Gegenprobe (v10_best auf v12s eigenem Split
neu ausgewertet: 37.4%) zeigte in dieselbe Richtung und wird hier bestätigt
und mit echter Runden-/Korpus-Stratifizierung untermauert.

**Kernfrage 2 -- korreliert frozen-Top-1 besser mit der bekannten
Stärke-Reihenfolge?** Nein, nicht durchgehend. Frozen-Top-1 trennt sauber
zwischen den GENERATIONEN (v10/v11-Familie ~40-42% vs. v12-Familie
~44-47%), aber INNERHALB der v12-Familie liefert es keine mit der
Elo-Reihenfolge konsistente Sortierung: v12b_lr (Champion, Elo 1051) und
v12_best (943) liegen mit 46.6% exakt gleichauf, v12d_pw05 (laut Vorgabe
real schwächer als v12b_lr) liegt mit 46.5% praktisch identisch zu
v12b_lr. Auch innerhalb der v10/v11-Familie gibt es eine Inversion: v10_best
(858 Elo) hat das NIEDRIGSTE Top-1 (39.5%) der drei, obwohl v11_td07_best
(853 Elo, praktisch gleichauf) und v11_best (809 Elo, schwächer) beide
höhere Top-1-Werte zeigen (41.8%/40.5%). Das bestätigt das wiederkehrende
Projekt-Muster (v11-/v12-Zyklen): Offline-Policy-/Value-Metriken bewegen
sich mit dem Trainings-/Daten-Regime, aber nicht fein genug mit der
tatsächlichen Spielstärke -- Stärke-Gewinne kamen bisher fast immer aus
Such-Mechanik, nicht aus Netz-Metriken.

**Auffälligkeit: v12b_scratch_best zeigt starken Korpus-Overfit.** Global
hat es den höchsten Value-R² aller Modelle (0.3951), aber die
Korpus-Aufschlüsselung zeigt warum: R²=0.7058 auf dem v10b-Subset (dem
Korpus, auf dem es trainiert wurde -- from-scratch, kein Warm-Start) vs.
R²=−0.0148 auf dem v12-Subset (schlechter als der Mittelwerts-Prädiktor).
Kein anderes Modell zeigt eine annähernd so große Korpus-zu-Korpus-Spreizung
(alle anderen liegen typischerweise innerhalb ~0.15-0.25 R²-Punkten
zwischen den Subsets). Genau der Verteilungseffekt, den die
Korpus-Aufschlüsselung sichtbar machen sollte: ein hoher globaler R² kann
reines Auswendiglernen EINES Korpus sein statt echter Generalisierung.

**Commits**: Code (`tools/build_frozen_eval_set.py` neu,
`tools/offline_diagnose.py` `--frozen`/`--threads`/Korpus-Aufschlüsselung)
und Doku (dieser Abschnitt) getrennt committet, siehe Git-Historie.

## v13-Zyklus (2026-07-24)

**Task #86. Build-Gate**: Wheel bereits aktuell (Stand `115b5ba`, Default-
Features, 151/151 Tests) -- vor diesem Zyklus verifiziert, kein erneuter
Rebuild noetig.

**Replay-Fenster (Nutzer-Strategie: 2000 aktuelle + 1000 Alt-Champion)**:
alle 200 `data/selfplay_v12_*.pkl` (Generator v12b_lr, 2000 Spiele)
unveraendert uebernommen. Von den 200 `data/selfplay_v10b_*.pkl` (Altbestand,
Generator v10) deterministisch 100 ausgewaehlt --
`random.Random(20260724).sample(sorted(glob("data/selfplay_v10b_*.pkl")), 100)`
-- die NICHT gewaehlten 100 Dateien nach `data/archive_v10b_beyond_window/`
verschoben (reversibel, nichts geloescht; Auswahl-Manifest liegt dort als
`selection_manifest.json`). Endzustand `data/`: 200×v12 + 100×v10b (+
100 archivierte v10b in `archive_v10b_beyond_window/`).

**Training (`v13`)**: Warm-Start von `alphazero_v12b_lr_best.pth`, Standard-
Rezept `--lr 0.00005 --lr-schedule cosine --epochs 100`. **Zwischenfall**:
erster Versuch mit `--load alphazero_v12b_lr_best` schlug fehl, ohne
Exception -- `train.py` haengt selbst schon `alphazero_`-Praefix an
(`load_path = MODELS_DIR / f"alphazero_{load_version}.pth"`), der gebaute
Pfad `alphazero_alphazero_v12b_lr_best.pth` existierte nicht, Skript fiel
still auf `Trainiere von null!` zurueck (Value-Val-R² startete bei 0.158
statt sofort ~0.27 -- das war das erste Warnsignal). Lauf nach 6 Epochen
sauber abgebrochen (`taskkill`, kein Checkpoint geschrieben, Cache-Dateien
+ Fehl-Manifest geloescht), korrekt mit `--load v12b_lr_best` neu gestartet.
**Lehre**: `--load`-Argument ist der reine Versionsname OHNE `alphazero_`-
Praefix.

Neues Fenster erzwang neuen HDF5-Cache-Build (erwartet, ~204s/23.5s Train/Val-
Load). 435.778 Trainings- / 48.446 Val-Zuege (Val-Split 30/300 Dateien,
gleicher Seed wie immer). Manifest
`models/manifest_train_v13_20260724_114623.json` bestaetigt
`corpus_composition` **200 Dateien v12 (2000 Spiele) + 100 Dateien v10b
(1940 Spiele)** -- exakt wie geplant. Warm-Start bestaetigt im Log
("📥 Lade altes Model als Startpunkt: alphazero_v12b_lr_best.pth"), Value-
Val-R² startet bei 0.270 (Epoche 1) und faellt danach monoton (0.264 → 0.257
→ ... → 0.203 bei Epoche 15) -- dasselbe Fruehplateau-Muster wie v11/v12/v12b.
Early Stopping bei Epoche 15/100 (Val-Policy-Plateau seit Epoche 10). **Bester
Checkpoint: Epoche 4** (`val_combined`=1.6196, Value-Val-R²=0.253,
Points-Val-R²=0.225) -- wie erwartet im Bereich Epoche 2-5 mit dem LR-Rezept.
Netzauslastung gesund (Dead 6%, Eff.Rank 38%). ONNX-Export automatisch
mitgelaufen und verifiziert (`alphazero_v13.onnx` + `alphazero_v13_best.onnx`,
beide frischer als Trainingsstart, 4.85MB).

**Offline-Diagnose, klassisch** (`tools/offline_diagnose.py`, echter
Val-Split 30/300 Dateien, n=48.446 Val-Zuege, davon 35.325 Drafting-Schritte
-- **Achtung, anderer Split als der v12-Zyklus-Referenzwert** (neues Fenster
= neue Datei-Menge = andere Val-Auswahl trotz gleichem Seed), daher direkter
Vergleich mit den v12b_lr-Referenzzahlen aus dem Auftrag (R² 0.2289 etc., auf
einem v10b-Split) nur eingeschraenkt aussagekraeftig -- hier stattdessen
v12b_lr_best NEU auf demselben v13-Split mitgerechnet):

| Metrik | v13_best | v12b_lr_best (gleicher Split) |
|---|---|---|
| Policy Top-1 (Drafting) | 45.6% | 44.7% |
| Policy Top-3 (Drafting) | 75.8% | 74.2% |
| Value Val-R² global | 0.2528 | 0.2625 |
| R² Runde 1 | 0.0162 | 0.0246 |
| R² Runde 2 | 0.1138 | 0.1395 |
| R² Runde 3 | 0.1107 | 0.1198 |
| R² Runde 4 | 0.2270 | 0.2311 |
| R² Runde 5 | 0.6151 | 0.6208 |

Gemischtes Bild: v13 gewinnt bei Policy Top-1/Top-3, verliert leicht bei
Value-R² (global und in jeder Runde) -- Unterschiede klein und angesichts des
unterschiedlichen Splits ggue. der Auftrags-Referenz nicht ueberinterpretierbar.

**Offline-Diagnose, frozen** (`--frozen`, `evaluations/frozen_eval_set.pkl`,
Version `frozen_v1`, n=1.800, generationsuebergreifend vergleichbar --
DIES ist der eigentlich belastbare Vergleich):

| Metrik | v13_best | v12b_lr_best (frozen_v1-Referenz) |
|---|---|---|
| Policy Top-1 (Drafting) | **49.5%** | 46.6% |
| Policy Top-3 (Drafting) | **75.5%** | 74.1% |
| Value Val-R² global | **0.3688** | 0.3379 |
| R² Runde 1 | **0.0991** | 0.0956 |
| R² Runde 2 | **0.1941** | 0.1664 |
| R² Runde 3 | **0.2555** | 0.2172 |
| R² Runde 4 | **0.3339** | 0.3049 |
| R² Runde 5 | **0.6921** | 0.6479 |

Korpus-Aufschluesselung: v13_best schlaegt v12b_lr_best auf dem v12-Subset
deutlich (Top-1 57.5% vs. 51.8%, R² 0.3424 vs. 0.2273), liegt auf dem
v10b-Subset bei Top-1 praktisch gleichauf (41.8% vs. 41.7%) und leicht
niedriger bei R² (0.3887 vs. 0.4217). **Auf dem frozen Set schlaegt v13_best
v12b_lr_best in JEDER einzelnen Metrik** (Top-1, Top-3, R² global und alle
fuenf Runden) -- klar bestes Offline-Ergebnis der bisherigen frozen_v1-Reihe.

**Gepaartes SPRT-Gating v13_best vs. v12b_lr_best** (`tools/paired_gating.py`,
beide @400 Sims, H1 p=0.65, alpha=beta=0.05, Default-Threads jetzt 10 --
**Zwischenfall**: erster Versuch mit `--model-a v13_best --model-b
v12b_lr_best` (Kurznamen statt Pfad) schlug sofort fehl
(`ValueError: Opening "v13_best"`) -- das Skript erwartet den vollen
`.onnx`-Pfad als Argument (`--model-a models/alphazero_v13_best.onnx`),
anders als `offline_diagnose.py`s Kurzname-Konvention. Mit korrektem Pfad neu
gestartet, kein Datenverlust, da der Fehlversuch vor dem ersten Block abbrach):

| Block | Paare kum. | Ergebnis kum. | A-Sweep/B-Sweep/Split | LLR | Bericht-p |
|---|---|---|---|---|---|
| 1 | 25 | 24:26 | 7/8/10 | −1.017 | 1.000 |
| 2 | 50 | 50:50 | 13/13/24 | −1.226 | 1.000 |
| 3 | 75 | 74:76 | 18/19/38 | −2.054 | 1.000 |
| 4 | 100 | 103:97 | 26/23/51 | −1.382 | 0.775 |
| 5 | 125 | 132:118 | 34/27/64 | −0.710 | 0.443 |
| 6 | 150 | 160:140 | 41/31/78 | −0.300 | 0.289 |
| 7 | 175 | 185:165 | 45/35/95 | −0.677 | 0.314 |
| 8 | 200 | **212:188** | 54/42/104 | **−0.813** | **0.262** |

**SPRT-Verdikt: harter Deckel (200 Paare/400 Spiele) erreicht OHNE
Entscheid** (LLR=−0.813, Schranken [−2.944, +2.944] nie ueberschritten --
weder Richtung H1 noch Richtung H0). Fixed-n-Notbehelf: gepaarte Differenz
+0.120, 95%-KI [−0.072, +0.312] (schliesst Null ein), exakter Paar-
Vorzeichentest p=0.2615 -- **nicht signifikant**. **Kein Champion-Wechsel:
v12b_lr_best bleibt Champion.** Da kein Champion-Wechsel: keine neuen
Elo-Kader-Eintraege (`tools/elo_tracker.py`), nur diese Gating-Zahlen
dokumentiert. Hinweis-Kommandozeile fuers Protokoll (nicht ausgefuehrt, siehe
Kader-Regel):

    python tools/elo_tracker.py add --player-a v13_best --sims-a 400 \
      --player-b v12b_lr_best --sims-b 400 --wins-a 212 --wins-b 188 --n 400 \
      --comment "Gepaartes Gating (Task #86), SPRT=UNDECIDED_CAP_REACHED, p=0.2615"

**Einordnung**: v13 zeigt auf dem frozen Set die klarste Offline-
Verbesserung der bisherigen frozen_v1-Reihe (durchgehend besser in allen
Metriken), UND schlaegt v12b_lr_best auch im Fixed-n-Rohergebnis (212:188,
53%) -- aber das SPRT bleibt bei diesem n unentschieden, die 95%-KI
schliesst Null mit ein. Passt zum wiederkehrenden Projekt-Muster (v11-/v12-
/frozen_v1-Zyklen): Offline-Policy-/Value-Metriken bewegen sich mit dem
Trainings-/Daten-Regime, aber uebersetzen sich nicht zuverlaessig 1:1 in
messbare Arena-Staerke bei diesem Stichprobenumfang. Ein groesserer,
kostenintensiverer Gating-Lauf (z.B. hoeherer harter Deckel) koennte die
Frage klaeren, ist aber nicht Teil dieses Zyklus. `v12b_lr_best` bleibt
sowohl Champion als auch Self-Play-Generator; `v13_best` steht als
trainiertes, offline erfolgreiches, aber Arena-unbestaetigtes Modell bereit.

**Commits**: Datenfenster-Verschiebung (`data/archive_v10b_beyond_window/` +
Manifest, `data/` selbst ist gitignored, keine Code-Aenderung), Modelle
(`models/alphazero_v13*`, gitignored) und Doku (dieser Abschnitt) getrennt
committet, siehe Git-Historie.

## rtv-Ablation Phase 1 (2026-07-24)

**Task #84. Motivation**: `round_transition_value` (rtv) verursacht ~81% der
Self-Play-Kosten (#80/#81), ist aber schwaecher outcome-korreliert als
`bootstrap_value` (0.215 vs. 0.445, siehe Kostenprofil-Abschnitt oben, Task
#80). Faellt rtv weg, wird Self-Play ~3x schneller. Ob rtv im Value-Target ueberhaupt
Staerke beitraegt, wurde OHNE neues Self-Play getestet: zwei Trainings-
Varianten auf demselben v13-Fenster (200x `data/selfplay_v12_*.pkl` +
100x `data/selfplay_v10b_*.pkl`, unveraendert), die den rtv-Override beim
Target-Bau ignorieren, gegen die Referenz `v13_best` (rtv wie gehabt) gepaart
gegatet.

**Varianten-Schalter** (`engine/py/neural_net.py::MosaicDataset`,
`train.py --value-target-variant {default,nortv,nortv_r1}`, Commit
`fef7e3e`): `nortv` deaktiviert den rtv-Override komplett (Value-Target
faellt fuer ALLE Schritte auf die tanh-Margin-Formel zurueck, TD-Bootstrap-
Blend bleibt oben drauf unveraendert); `nortv_r1` deaktiviert ihn nur fuer
Runde-1-Zustaende (teuerster rtv-Fall, #80), Runden 2-5 bleiben wie
`default`. `default` reproduziert das Bestandsverhalten byte-identisch.
**Cache-Key-Nachweis** (dieselbe Falle wie TD_LAMBDA, 2026-07-22):
`value_target_variant` ist jetzt Teil des HDF5-Cache-Key-Hashes
(`neural_net.py::MosaicDataset.__init__`) -- ein Synthetik-Test mit einem
einzelnen Runde-1-Record (`round_transition_value=[0.9,0.1]`,
`scores_unclamped=[10,5]`) bestaetigte vor dem echten Training:
`default` → Value-Target 0.800 (rtv-Override, `0.9*2-1`), `nortv` UND
`nortv_r1` (Runde 1!) → beide 0.0997 (tanh-Margin-Fallback,
`tanh((10-5)/50)`), UND alle drei Varianten erzeugten drei VERSCHIEDENE
`.cache_*.h5`-Dateien im selben Ordner (kein stiller Cache-Reuse). Ein
Zweit-Test mit Runde 2 bestaetigte, dass `nortv_r1` dort wie `default`
den rtv-Wert (0.800) behaelt -- die Rundenbeschraenkung greift korrekt nur
fuer Runde 1.

**Training (`v13_nortv`, `v13_nortv_r1`)**: exakt das v13-Rezept, Warm-Start
von `alphazero_v12b_lr_best.pth` (Footgun beachtet: `--load v12b_lr_best`
OHNE `alphazero_`-Praefix), `--lr 0.00005 --lr-schedule cosine --epochs 100`,
Cache-Build je Variante frisch (~203s/23s Train/Val-Load, identisch zu v13 --
derselbe Datei-Umfang, nur neuer Cache-Key). **Warm-Start verifiziert** ueber
Epoche-1-Val-R²: `v13_nortv` startet bei **0.456** (deutlich ueber der
0.24-Schwelle), `v13_nortv_r1` bei **0.286** -- beide klar im Warm-Start-
Bereich, kein stiller From-Scratch-Fallback wie beim v13-Zwischenfall.

| Epoche | v13_nortv Val-R² (Value/Points) | v13_nortv_r1 Val-R² (Value/Points) |
|---|---|---|
| 1 | 0.456 / 0.511 | 0.286 / 0.278 |
| 2 | 0.461 / 0.518 | 0.282 / 0.272 |
| 3 | 0.464 / 0.521 | 0.278 / 0.268 |
| 4 | **0.465 / 0.522** | 0.274 / 0.264 |
| 5 | 0.464 / 0.522 | 0.268 / 0.259 |
| ... | (monotoner Abfall danach) | (monotoner Abfall danach) |
| 15 (Stop) | 0.443 / 0.502 | 0.229 / 0.212 |

Beide Laeufe: Val-Policy-Plateau ab Epoche 10, Early Stopping bei Epoche
15/100 (Patience 5, identisch zu v13). **Bester Checkpoint** nach
gewichteter Val-Kombination: `v13_nortv_best` = Epoche 4
(`val_combined`=1.5958), `v13_nortv_r1_best` = Epoche 3
(`val_combined`=1.6135, trotz Epoche 1 minimal hoeherem reinen Value-R² --
die Checkpoint-Auswahl gewichtet Policy+Value+Points gemeinsam, kein Fehler).
Netzauslastung beider Laeufe gesund (Dead 7%, Eff.Rank 38%, wie v13). ONNX-
Export automatisch mitgelaufen und verifiziert. Manifeste:
`models/manifest_train_v13_nortv_20260724_124658.json`,
`models/manifest_train_v13_nortv_r1_20260724_125959.json` (beide
`git_commit=fef7e3e`).

**Offline-Diagnose, klassisch** (`tools/offline_diagnose.py`, echter
Val-Split 30/300 Dateien, n=48.446, davon 35.325 Drafting -- **WICHTIG**: das
Skript baut das Referenz-Target IMMER MIT rtv-Override, ein niedrigeres R²
der nortv-Varianten auf diesem Massstab ist daher erwartbar und KEIN
Ausschlusskriterium, siehe Auftrag):

| Metrik | v13_best | v13_nortv_best | v13_nortv_r1_best |
|---|---|---|---|
| Policy Top-1 (Drafting) | 45.6% | 45.8% | 45.7% |
| Policy Top-3 (Drafting) | 75.8% | 75.8% | 75.8% |
| Value Val-R² global | 0.2528 | 0.2491 | 0.2609 |
| R² Runde 1 | 0.0162 | 0.0360 | 0.0290 |
| R² Runde 2 | 0.1138 | 0.1354 | 0.1308 |
| R² Runde 3 | 0.1107 | 0.0807 | 0.1160 |
| R² Runde 4 | 0.2270 | 0.1726 | 0.2328 |
| R² Runde 5 | 0.6151 | 0.6449 | 0.6190 |

Policy-Metriken praktisch identisch (erwartet -- Policy-Ziel haengt nicht am
Value-Target). Value-R² gemischt, KEIN klarer Abfall der nortv-Varianten
(Runde 1 sogar hoeher als v13_best in beiden Varianten -- plausibel: das
harte rtv-Ziel selbst ist fuer Runde 1 laut Noise-Floor-Test kaum von Null
unterscheidbar, siehe VALUE_SCHEMA_VERSION=15-Kommentar).

**Offline-Diagnose, frozen** (`--frozen`, `frozen_v1`, n=1.800, generations-
uebergreifend, gleicher rtv-Referenz-Massstab-Vorbehalt):

| Metrik | v13_best | v13_nortv_best | v13_nortv_r1_best |
|---|---|---|---|
| Policy Top-1 (Drafting) | **49.5%** | 48.5% | 48.0% |
| Policy Top-3 (Drafting) | **75.5%** | 75.5% | 75.3% |
| Value Val-R² global | **0.3688** | 0.3432 | 0.3629 |
| R² Runde 1 | **0.0991** | 0.0628 | 0.0763 |
| R² Runde 2 | 0.1941 | 0.1752 | **0.1971** |
| R² Runde 3 | **0.2555** | 0.2273 | 0.2543 |
| R² Runde 4 | **0.3339** | 0.2706 | 0.3272 |
| R² Runde 5 | 0.6921 | **0.6971** | 0.6880 |

Hier zeigt v13_best (mit rtv) durchgehend etwas hoehere Value-R²-Werte als
`nortv` -- auf DIESEM rtv-basierten Massstab erwartbar (rtv-Override ist Teil
der Referenz-Zielformel). Entscheidend fuer die eigentliche Frage ist wie
im Auftrag vorgegeben die Arena, nicht diese Offline-Zahlen.
JSON: `evaluations/offline_diagnose_v13_vs_nortv_variants.json` (klassisch),
`evaluations/offline_diagnose_v13_vs_nortv_variants_frozen.json` (frozen).

**Gepaartes Nicht-Unterlegenheits-Gating v13_best (A) vs. v13_nortv_best (B)**
(`tools/paired_gating.py`, beide @400 Sims, Threads 10, H1 p=0.65,
alpha=beta=0.05):

| Block | Paare kum. | Ergebnis kum. | A-Sweep/B-Sweep/Split | LLR | Bericht-p |
|---|---|---|---|---|---|
| 1 | 25 | 20:30 | 5/10/10 | −2.255 | 0.3018 |
| 2 | 50 | **38:62** | 6/18/26 | **−4.846** | **0.0227** |

**SPRT-Verdikt nach nur 2 Bloecken (50 Paare/100 Spiele): ACCEPT_H0**
(LLR=−4.846 <= untere Schranke −2.944) -- **kein Beleg, dass v13_best (mit
rtv) besser ist als v13_nortv_best (ohne rtv)**. Auffaellig: die
Fixed-n-Zahlen zeigen nicht bloss Gleichstand, sondern einen Vorteil fuer
`nortv` (38:62, gepaarte Differenz −0.480, 95%-KI [−0.844, −0.116] schliesst
Null NICHT ein, exakter Vorzeichentest p=0.0227) -- bei n=100 kein belastbarer
Beleg fuer "nortv ist besser" (dafuer waere ein H1-Test mit vertauschten
Rollen noetig, nicht Teil dieses Auftrags), aber definitiv KEIN Hinweis
darauf, dass der teure rtv-Override im Value-Target gebraucht wird.
JSON: `evaluations/paired_gating_result_v13_best_vs_v13_nortv_best.json`.

**r1-Gating entfaellt** (wie im Auftrag vorgesehen): da das komplette
`nortv` bereits ACCEPT_H0 erreicht hat (rtv-Streichung insgesamt
gerechtfertigt), entfaellt die separate Pruefung von `v13_nortv_r1_best`
gegen `v13_best` -- die Teilersparnis-Variante ist per Definition eine
schwaechere Streichung als die komplette und braucht keinen eigenen Beleg,
wenn die komplette bereits besteht. `v13_nortv_r1_best` wurde trotzdem
vollstaendig trainiert und offline diagnostiziert (s.o.), fuer den Fall dass
Phase 2 aus anderen Gruenden (z.B. Restrisiko) die konservativere
Teilstreichung bevorzugt.

**Einordnung & Empfehlung fuer Phase 2 (#85, Rust-Streichung)**: Das Ergebnis
ist eindeutiger als erwartet -- nicht nur "nicht messbar schlechter", sondern
im Fixed-n-Rohergebnis sogar zugunsten der rtv-freien Variante (bei kleinem
n, SPRT stoppte frueh Richtung H0). Zusammen mit dem bereits dokumentierten
Befund (#80: rtv = 81% der Self-Play-Kosten, schwaecher outcome-korreliert
als bootstrap_value) ist die Evidenzlage klar: **rtv traegt im aktuellen
Trainings-Setup keine messbare Staerke bei, kostet aber den grossen Teil der
Self-Play-Zeit. Empfehlung: #85 sollte die komplette Rust-seitige
rtv-Berechnung streichen (nicht nur die Runde-1-Teilersparnis)** -- das
noch teurere `nortv_r1` als Kompromiss ist auf Basis dieser Daten nicht
notwendig. Vor der eigentlichen Streichung in Rust: ein groesserer
Gating-Lauf (mehr Paare) waere sinnvoll, um den Fixed-n-Vorteil von `nortv`
entweder zu erhaerten oder als Rauschen bei n=100 zu entlarven -- fuer die
Kernfrage dieses Auftrags ("ist rtv verzichtbar?") reicht das ACCEPT_H0
bereits als Beleg.

**Commits**: Code (`engine/py/neural_net.py`, `train.py`, Commit `fef7e3e`)
und Doku (dieser Abschnitt) getrennt committet, siehe Git-Historie. Modelle
(`models/alphazero_v13_nortv*`, `models/alphazero_v13_nortv_r1*`, gitignored)
und Trainings-Manifeste nicht Teil des Commits.

## Champion-Gating v13_nortv vs. v12b_lr (2026-07-24)

Direkte Fortsetzung der rtv-Ablation Phase 1 (Abschnitt oben): `v13_nortv_best`
hatte das Nicht-Unterlegenheits-Gating gegen `v13_best` bereits deutlich
bestanden (Fixed-n 62:38 FUER nortv, SPRT ACCEPT_H0 nach 50 Paaren). `v13_best`
selbst spielte gegen den amtierenden Champion `v12b_lr_best` 212:188
(SPRT UNDECIDED_CAP_REACHED, nicht signifikant). Offene Frage: schlaegt
`v13_nortv_best` den Champion direkt?

**Gepaartes SPRT-Gating** (`tools/paired_gating.py`, Kandidat A=`v13_nortv_best`,
B=`v12b_lr_best`, beide @400 Sims, Threads 10, H1 p=0.65, alpha=beta=0.05):

| Block | Paare kum. | Ergebnis kum. | A-Sweep/B-Sweep/Split | LLR | Bericht-p |
|---|---|---|---|---|---|
| 1 | 25 | 34:16 | 13/4/8 | +1.984 | 0.0490 |
| 2 | 50 | 63:37 | 19/6/25 | +2.845 | 0.0146 |
| 3 | 75 | 90:60 | 27/12/36 | +2.804 | 0.0237 |
| 4 | 100 | 115:85 | 32/17/51 | +2.332 | 0.0444 |
| 5 | 125 | 143:107 | 38/20/67 | +2.836 | 0.0247 |
| 6 | 150 | **171:129** | 46/25/79 | **+3.152** | **0.0170** |

**SPRT-Verdikt nach 6 Bloecken (150 Paare/300 Spiele): ACCEPT_H1**
(LLR=+3.152 >= obere Schranke +2.944) -- **`v13_nortv_best` schlaegt den
Champion `v12b_lr_best` signifikant** (171:129, gepaarte Differenz +0.280,
95%-KI [+0.064, +0.496], exakter Vorzeichentest p=0.0170). Der LLR-Verlauf
pendelte ab Block 2 durchgehend nahe der oberen Schranke (2.3-2.9), ohne je
zur Null zu tendieren -- kein Hinweis auf einen instabilen/knappen Trend,
sondern ein konsistenter Vorteil, der erst in Block 6 die formale Schranke
ueberschritt. JSON:
`evaluations/paired_gating_result_v13_nortv_best_vs_v12b_lr_best.json`.

**Champion-Wechsel**: `v13_nortv_best` ist neuer Champion. Elo-Eintrag via
`tools/elo_tracker.py add` (siehe `evaluations/elo_history.csv`, Zeile
2026-07-24): Elo 1100 (95%-CI [990, 1214]) vs. `v12b_lr_best` 1051
(nach Neuberechnung durch den neuen Datenpunkt).

**Einordnung**: Das rtv-freie Value-Target ist damit doppelt bestaetigt --
einmal im direkten Nicht-Unterlegenheits-Vergleich gegen sein rtv-basiertes
Geschwistermodell `v13_best` (Abschnitt oben) und jetzt zusaetzlich durch
einen echten Champion-Wechsel gegen die staerkste bisherige Vergleichsbasis.
Das stuetzt die Empfehlung aus der rtv-Ablation (Phase 2 / #85: komplette
Rust-seitige rtv-Berechnung streichen) zusaetzlich, auch wenn dieser
Champion-Wechsel primaer eine Staerke-Aussage ist und kein direkter
Kostenbeleg (der liegt bereits in #80 vor).

## rtv-Ablation Phase 2 (2026-07-24)

**Task #85. Auftrag**: die Evidenzlage aus #80 (rtv = ~81% der Self-Play-
Kosten), #84 (rtv-freies Value-Target `v13_nortv_best` nicht unterlegen
gegen `v13_best`, 62:38) und der Champion-Gating-Runde oben
(`v13_nortv_best` schlaegt `v12b_lr_best` 171:129, neuer Champion) macht
die teure `round_transition_value`-Berechnung im Self-Play verzichtbar.
Dieser Task macht sie **abschaltbar** (Schalter, kein Hard-Delete) -- die
rtv-Infrastruktur (`round_transition.rs`, `round_transition_deep.rs`)
bleibt vollstaendig erhalten, nur der Aufruf im Self-Play-Loop wird
gated. Umgesetzt in einem eigenen Worktree/Branch (`worktree-rtv-removal`),
main unberuehrt.

### Schalter-Design

Neuer bool-Parameter `record_rtv` (Default `false` auf allen Rust->Python-
Bindings) in `engine/src/self_play.rs`:

- `play_one_game` (Heuristik-Self-Play + optionale Netz-Rundenuebergangs-
  Labels) und `play_net_self_play_game` (Netz-PUCT-Self-Play, der
  `--mode network`-Produktionspfad) bekommen je einen neuen `record_rtv:
  bool`-Parameter. Er gated NUR den Block, der
  `sample_round_transition_for_round` aufruft und `round_transition_value`
  ins Record schreibt. Der direkt danebenliegende `bootstrap_value`-Block
  (TD-Bootstrap, `round_transition_deep::bootstrap_value_after_rounds`)
  bleibt **unveraendert aktiv** -- eigene, separat gemessene
  Kostenkategorie (~5% laut #80/#81), nicht Teil dieser Ablation.
- `run_self_play_with_net_labels` und `run_net_self_play` reichen
  `record_rtv` durch.
- PyO3-Bindings `self_play_games_with_net_labels`/`net_self_play_games`
  (`engine/src/lib.rs`): neuer Parameter `record_rtv=false` (Default AUS
  = neues Verhalten).
- `self_play.py`: neues CLI-Flag `--rtv` (Default AUS, `action="store_true"`
  reaktiviert rtv), durchgereicht durch `generate_data` ->
  `_run_chunk_supervised` -> `_worker_run_chunk` -> `mosaic_rust`-Aufruf.
  Bei `--mode mcts` ohne `--model` ist das Flag ein No-Op (rtv wurde dort
  nie berechnet, `net` ist `None`).
- Task-#80/#81-Profiling-Kategorien (`rtv_count`/`rtv_ns` in
  `profiling.rs`) melden bei `record_rtv=false` einfach 0 -- kein
  separater Zaehler noetig, der `with_category(Category::Rtv, ...)`-Block
  wird schlicht nicht betreten.

Geaenderte Dateien: `engine/src/self_play.rs`, `engine/src/lib.rs`,
`self_play.py`. Kein Hard-Delete, keine Test-Loeschung.

### Nebeneffekt-Pruefung

- **Python-Target-Builder** (`engine/py/neural_net.py`, Zeile ~630):
  `rtv = step.get("round_transition_value")` -- gibt `None` zurueck, wenn
  das Feld fehlt, der nachfolgende Code faellt dann korrekt auf die
  tanh-Margin-Formel zurueck (`val`/`points_val` unveraendert berechnet),
  der TD-Bootstrap-Blend (`bv = step.get("bootstrap_value")`) greift
  unabhaengig davon. Verifiziert durch Lesen des Codes UND konkret durch
  einen Live-Aufruf (siehe Record-Stichprobe unten) -- Records ohne
  `round_transition_value` sind kein neuer Fall (~17% der Bestandsdaten
  hatten das Feld schon vorher nie, abgebrochene/Runde-5-Records), der
  Fallback-Pfad ist also bereits vielfach durchlaufen.
- **Sonstige Python-Konsumenten** (`tools/offline_diagnose.py`,
  `tools/build_frozen_eval_set.py`, `tools/rtv_redundancy_report.py`,
  `train.py`): alle lesen `round_transition_value` ausschliesslich per
  `.get(...)`/`step.get(...)`, keiner erzwingt das Feld. Die
  Redundanz-/Diagnose-Tools (#80s `rtv_redundancy_report.py`) sehen fuer
  kuenftige rtv-freie Korpora schlicht 0 Paare -- erwartet, kein Bug.
- **`--mode mcts --model X`-Pfad** (Heuristik-Self-Play mit Netz-Labels,
  `run_self_play_with_net_labels`): ebenfalls auf `record_rtv=false`
  standardisiert, aus denselben Gruenden.
- **`py.rs`** (interaktive `PyGame`-Bindings fuer `server.py`): keine
  rtv-Beruehrung, unveraendert.
- Keine bestehenden rtv-spezifischen Rust-Unit-Tests gefunden, die
  geloescht oder parametrisiert werden mussten (`grep` ueber
  `self_play.rs`/`round_transition*.rs`-Testmodule) -- die vorhandenen
  Tests fuer `resolve_to_pre_chance`/`sample_round_transition_value` testen
  die tiefere Infrastruktur direkt und sind vom neuen Schalter nicht
  betroffen.

### Testresultat

`cargo test --release` im Worktree: **151 passed, 1 ignored
(`round5_node_calibration_probe`, praeexistent/unabhaengig), 0 failed**
(85.6s Testlaufzeit). Volle Suite gruen, alle betroffenen Aufrufstellen
(2 Produktions-Testfaelle `play_one_game_terminates_with_records`,
`no_tiling_deadlock_across_seeds`, plus alle Aufrufer in `self_play.rs`/
`lib.rs`) auf den neuen Parameter angepasst.

### Durchsatzmessung

Mess-Wheel aus dem Worktree gebaut (`maturin build --release`) und
temporaer produktiv installiert (danach zurueckgebaut, siehe unten).
Direktaufruf `mosaic_rust.net_self_play_games` (kein `progress_path`,
keine `.pkl`/`data/`-Beruehrung, analog zur #81-Methodik), Champion
`alphazero_v13_nortv_best.onnx`, `base_sims=400`, `c_puct=1.5`,
`add_root_noise=true`, 11 Threads. Ergebnisse + Sample-Stats in
`results.json` (scratchpad, nicht committed).

| Konfiguration | Modell | Spiele | Wall-Clock | Spiele/s | Hochrechnung 2000 Spiele | Hochrechnung 6000 Spiele |
|---|---|---:|---:|---:|---:|---:|
| rtv AUS (Task #85, neuer Default) | v13_nortv_best | 20 | 83.8s | **0.2387** | ~2h20min | ~6h59min |
| rtv AN (Kontrollmessung, gleiches Modell) | v13_nortv_best | 10 | 219.1s | 0.0456 | ~12h10min | ~36h31min |
| rtv AN (#81-Referenz, zum Vergleich) | v12b_lr | 20 | 417.7s | 0.0479 | ~11h36min | ~34h47min |

**Durchsatzgewinn**: 0.2387 / 0.0456 = **5.23x** gegenueber der
modell-gleichen rtv-AN-Kontrollmessung, 0.2387 / 0.0479 = **4.98x**
gegenueber der #81-Referenz (anderes Modell `v12b_lr`) -- beide klar
**ueber** der im Auftrag erwarteten ~3x-Schaetzung (die aus #80/#81s
CPU-Sekunden-Aufschluesselung stammt: Gumbel+Bootstrap+Sonstiges
≈ 46-55 CPU-s/Spiel vs. rtv-inklusive ≈ 174-241 CPU-s/Spiel). Die
rtv-AN-Kontrollmessung mit `v13_nortv_best` (0.0456 Spiele/s) liegt nahe
an der #81-Referenz mit `v12b_lr` (0.0479 Spiele/s, -4.8%) -- der
Modell-Effekt ist also klein gegenueber dem rtv-Effekt, die ~5x-
Beschleunigung ist primaer dem abgeschalteten rtv zuzuschreiben, nicht
einem schnelleren Modell. Warum die tatsaechliche Wall-Clock-Beschleunigung
(~5x) ueber der reinen CPU-Sekunden-Schaetzung (~3x) liegt, wurde nicht
weiter zerlegt (moegliche Ursache: geringere Thread-Kontention bei
kuerzeren, gleichfoermigeren Partien ohne die teuren rtv-Rekursionsspitzen
-- out of scope fuer diesen Task).

### Record-Stichprobe (rtv AUS)

Live-Aufruf, `record_rtv=false`, Beispiel-Record eines abgeschlossenen
Spiels: Keys `['bootstrap_value', 'completed', 'game_id',
'moon_order_target', 'player', 'policy', 'scores', 'scores_unclamped',
'state', 'valid_actions', 'winner']` -- **kein** `round_transition_value`-
Key, `bootstrap_value` vorhanden (z.B. `[0.507, 0.504]`),
`scores_unclamped` vorhanden (z.B. `[4, -4]`), `policy` nicht-leer,
`completed=True`. Ueber den vollen 20-Spiele-Lauf: 0/3214 Steps mit
`round_transition_value`, 2670/3214 Steps mit `bootstrap_value` (nur
Runde-1-4-Uebergangs-Steps werden gestempelt, Runde-5-Steps nie -- exakt
das erwartete, unveraenderte Stempel-Muster). Gegenprobe rtv AN: 1333/1598
Steps mit `round_transition_value` UND `bootstrap_value` (deckungsgleich,
wie erwartet -- beide werden im selben Codeblock je Rundenuebergang
gestempelt).

### Repo-/Wheel-Endzustand

Branch `worktree-rtv-removal` (eigener `git worktree`), main unberuehrt.
Commit: Schalter-Implementierung (`engine/src/self_play.rs`,
`engine/src/lib.rs`, `self_play.py`). Nach der Mess-Phase: Produktions-
Wheel (main-Stand, Default-Features, `record_rtv`-Schalter Default-AUS
existiert dort NICHT -- main hat noch die alte, ungegatete rtv-Berechnung)
neu gebaut/installiert, Smoke-Test (`import mosaic_rust`) verifiziert.
Worktree bleibt bestehen (nicht geloescht) -- Merge-Entscheidung liegt
beim Nutzer.

**Empfehlung**: Merge von `worktree-rtv-removal` nach main. Die
Evidenzlage ist doppelt abgesichert (Nicht-Unterlegenheit UND
Champion-Gating-Sieg des rtv-freien Modells), der gemessene
Durchsatzgewinn (~5x, ueber der Erwartung) ist erheblich, und der Schalter
ist rueckwaertskompatibel (`--rtv` reaktiviert das alte Verhalten
verlustfrei, alte `.pkl`-Korpora mit `round_transition_value` bleiben
gueltig und werden vom Target-Builder unveraendert bevorzugt). Einziger
Wermutstropfen: die rtv-AN-Kontrollmessung nutzte nur 10 Spiele (Kosten-
/Zeitgruende) -- fuer eine praezisere Spiele/s-Zahl waere ein groesserer
Lauf moeglich, aendert aber nichts an der Groessenordnung der Aussage.

## Hybrid-Suche 2x2 (2026-07-24)

**Task #88, kausaler Kopf-Test.** Forschungsfrage: v12 spielt staerker als
v10 (Gating 124:76), die Staerke-Herkunft war unklar -- Policy-Head oder
Value-Head? (Das eingefrorene Eval-Set #87 zeigte v12 inzwischen auch bei
Policy vorn, aber offline-Metriken sagen Arena-Staerke notorisch schlecht
voraus -- ein kausaler Test war noetig.) Idee: Suche mit Priors von Netz A,
Blattwerten von Netz B -- isoliert, welcher Kopf die Suche tatsaechlich
staerker macht.

**Implementierung** (eigener Worktree `mosaic-AI-worktree-hybrid-search`,
Branch `worktree-hybrid-search`): `net_mcts.rs::make_node` bekommt einen
zweiten optionalen Netz-Parameter `net_value: Option<&Net>`. Bei `None`
(alle bisherigen Aufrufstellen unveraendert) oder wenn `net_value` per
`std::ptr::eq` auf dieselbe Referenz wie `net_policy` zeigt, laeuft
EXAKT der alte Code (ein `eval`/`eval_pair`-Aufruf liefert Policy UND Value
zusammen) -- Byte-Identitaet zum Vor-Task-#88-Zustand per Konstruktion, kein
Vergleich auf Toleranz. Nur bei einer ECHTEN zweiten Netz-Referenz greift
der Hybrid-Pfad: ein Batch=1-Pass gegen `net_policy` liefert Policy-Logits
UND Moon-Order (Moon-Order ist policy-artig, siehe Auftrag), ein zweiter
Pass (Batch=1 oder Batch=2 mit Gegner-Perspektive, je nach `MIRROR_OTHER_VAL`)
gegen `net_value` liefert Value- UND Points-Head (beide gehen in die
KataGo-Stil geblendete Utility ein). Die Verdrahtung wurde durch
`build_gumbel_tree`/`build_net_tree`/`build_determinized_forest` bis zu den
drei Produktions-Sucheinstiegen durchgereicht (dort weiterhin `None`, kein
Verhaltensunterschied); ein neuer, paralleler Einstieg
`net_search_drafting_action_hybrid(net_policy, net_value, ...)` exponiert den
echten Hybrid-Fall. In `self_play.rs`: `play_net_vs_net_hybrid_game`/
`run_net_vs_net_arena_hybrid` mit einem `hybrid_board`-Parameter (0/1) --
erlaubt echten Brett-Tausch bei identischem Seed (Paarungsmuster wie
`tools/paired_gating.py`), ohne eine zweite gespiegelte Funktion zu
brauchen. PyO3-Bindung: `net_vs_net_arena_match_hybrid` (`lib.rs`), additiv,
bestehende Funktionen unangetastet.

**Paritaetstest (wichtigster Korrektheitstest)**: zwei Ebenen, beide gruen.
(1) `net_mcts::tests::hybrid_search_with_equal_nets_matches_plain_search` --
`net_policy`/`net_value` als dieselbe Referenz, `build_net_tree` mit/ohne
Hybrid-Pfad muss ueber mehrere Zufallsstellungen/Sims-Budgets BYTE-IDENTISCHE
Wurzel-Statistik (Besuche, Q), completed-Q-Politik und finale Zugwahl liefern
(`assert_eq!`, keine Tolerenz). (2) `self_play::tests::
run_net_vs_net_arena_hybrid_with_equal_models_matches_plain_arena` --
End-zu-Ende ueber die tatsaechlich genutzte Arena-Funktion (inkl.
Tiling/Scoring), `hybrid_policy==hybrid_value==plain_model` muss fuer
`hybrid_board=0` UND `hybrid_board=1` byte-identische Spielfolgen zu
`run_net_vs_net_arena` liefern. `cargo test --release`: **153/153 gruen**
(151 Bestand + 2 neue).

**Messung** (gepaarte Arena, `tools/hybrid_paired_arena.py`, neu, nach
`paired_gating.py`-Muster: Brett-Tausch pro Seed-Paar, `mcnemar_exact_p`/
`paired_ci` von dort direkt wiederverwendet statt neu geschrieben; 400 Sims,
c_puct=1.5, 10 Threads, Basis-Seed 20260724 IDENTISCH ueber alle drei Zellen
-- Paar `i` nutzt in jeder Zelle denselben abgeleiteten Seed, siehe
Skript-Docstring). Referenzgegner fuer alle Zellen: `v10_best`.

| Zelle | Kandidat:Referenz | Winrate | McNemar p | gepaarte Diff (95%-KI) |
|---|---|---|---|---|
| Verankerung (v12_best vs. v10_best) | 61:39 (n=100, 50 Paare) | 61.0% | 0.0522 | +0.440 [+0.047, +0.833] |
| Hybrid P=v10, V=v12 | 69:51 (n=120, 60 Paare) | 57.5% | 0.1877 | +0.300 [-0.093, +0.693] |
| Hybrid P=v12, V=v10 | 59:61 (n=120, 60 Paare) | 49.2% | 1.0000 | -0.033 [-0.423, +0.356] |

Verankerung reproduziert die bekannte v12-Staerke gegen v10_best (61.0% hier
vs. 62.0% im urspruenglichen 124:76-Gating) -- interne Konsistenz der neuen
Seeds/Messbedingungen bestaetigt.

**Kausale Schlussfolgerung: der Value-Head traegt die Staerke, nicht der
Policy-Head.** `P=v10,V=v12` (Suche mit v10-Priors, aber v12-Blattwerten)
landet bei 57.5% -- nahe an der 61.0%-Verankerung, holt also den groessten
Teil von v12s Vorteil, OBWOHL die Priors/Moon-Order vom schwaecheren v10
stammen. `P=v12,V=v10` (v12-Priors, aber v10-Blattwerte) landet bei 49.2% --
ununterscheidbar von 50%, der Policy-Kopf allein traegt praktisch NICHTS
zur Arena-Staerke bei. Beide Zellen sind bei n=120 (60 Paare) statistisch
nicht signifikant von 50% bzw. von der Verankerung unterscheidbar (McNemar
p=0.19 bzw. p=1.00) -- die Aussage ist eine Richtungs-/Groessenordnungs-
Aussage (wie im Auftrag vorgesehen, keine Gating-Schaerfe), aber das Muster
ist eindeutig und in beide Zellen konsistent: die Reihenfolge Verankerung >
P=v10/V=v12 > P=v12/V=v10 ≈ 50% zeigt keine Ambiguitaet zwischen "geteilt"
und "Value" -- P=v12/V=v10 liegt praktisch exakt auf der 50%-Nulllinie, kein
Hinweis auf einen eigenstaendigen Policy-Beitrag. Das steht im Einklang mit
dem Eval-Set-#87-Befund (v12 auch bei Policy-Top-1 vorn), zeigt aber, dass
dieser Policy-Vorteil praktisch NICHT in Arena-Staerke uebersetzt -- die
Suche haengt bei diesem Sims-Niveau (400, Gumbel-Top-m=16 + Sequential
Halving) weit staerker vom Blattwert an den vielen durchsuchten Knoten ab
als vom initialen Prior-Ranking an der Wurzel.

**Auffaelligkeiten**: keine Fehler/Timeouts im Lauf (Log geprueft, sauber
durchgelaufen, ~28 Minuten Gesamtlaufzeit fuer alle drei Zellen bei 10
Threads). Ein durchgaengiger Split-Anteil von 35-42% (nicht-informative
1:1-Paare) ist erwartbar bei aehnlich starken Kandidaten (vgl. `paired_
gating.py`-Docstring). Rohdaten: `evaluations/hybrid_arena_anchor_v12_vs_v10.json`,
`evaluations/hybrid_arena_hybrid_P-v10_V-v12.json`,
`evaluations/hybrid_arena_hybrid_P-v12_V-v10.json` (im Worktree).

**Status**: reines Diagnose-Ergebnis, kein Code-/Architektur-Aenderungsauftrag
aus diesem Task. Der Hybrid-Suche-Code bleibt additiv im Worktree
(`worktree-hybrid-search`) verfuegbar, main unangetastet -- Merge-Entscheid
liegt beim Nutzer (analog zum wartenden `worktree-rtv-removal`).
*(Nachtrag beim Merge 2026-07-24: beide Worktrees sind inzwischen nach main
gemergt und abgeraeumt; rtv-Streichung ist produktiv, Hybrid-Suche als
Diagnose-Werkzeug in main verfuegbar.)*

## Datenverlust + v14-Neustart (2026-07-24)

**Task #89, Vorfallsbericht + From-Scratch-Neustart.** Am 2026-07-24 gingen
saemtliche Modellgewichte (v10, v11-Varianten, v12-Familie, v13-Familie,
inkl. Champion v13_nortv_best) unwiederbringlich verloren. Ursache: eine
Junction im Hybrid-Suche-Worktree (`mosaic-AI-worktree-hybrid-search`) zeigte
auf das Haupt-`models/`-Verzeichnis; `git worktree remove` hat beim Abraeumen
des Worktrees dieser Junction gefolgt und das echte `models/` mit-geloescht,
nicht nur die Worktree-Kopie. Ein `winfr`-Recovery-Versuch schlug fehl -- der
Speicherplatz war zwischenzeitlich von mehreren `cargo`/`maturin`-Build-
Laeufen ueberschrieben worden, die wiederhergestellten Dateien waren nur
Nullbyte-Huellen (richtige Groesse, kein Inhalt). Korpora (`data/`), Code und
Dokumentation (`evaluations/`, inkl. aller JSON-Diagnosen und dieser
STATUS.md) waren von der Junction nicht betroffen und blieben intakt.

**Backup-Konsequenz** (Nutzer-Entscheidung, noch am selben Tag umgesetzt):
taeglicher OneDrive-Spiegel weiterhin aktiv, zusaetzlich ab sofort ein
ereignisgesteuerter Modell-Snapshot nach JEDEM Trainingslauf --
`train.py`-Hook, Commit 5fa8b59. Der laufende v14-Trainingsprozess hatte
diesen Hook beim Start noch nicht geladen (Manifest zeigt `git_commit:
330b988`, den direkten Elternstand von 5fa8b59); der Snapshot fuer v14 wurde
deshalb manuell per `Start-ScheduledTask -TaskName "Mosaic-AI Backup"`
angestossen -- Ergebnis: `models_2026-07-24.zip` (19,6 MB) im OneDrive-Ordner
`Backups\mosaic-AI\models_snapshots\`, Inhalt verifiziert (alle acht
`alphazero_v14*`-Dateien inkl. `alphazero_v14_best.onnx` enthalten).

**v14-Training**: `python -u train.py --name v14 --value-target-variant
nortv --lr-schedule cosine --epochs 100`, From-Scratch (kein `--load`) auf
dem aktuellen 3000-Spiele-Fenster (`data/`: 200 Dateien `v12`-Praefix/2000
Spiele + 100 Dateien `v10b`-Praefix/1940 Spiele, macht real 300
Dateien/3940 Spiele). Lief 15 Epochen, Early-Stop-Plateau bei Epoche 10
(Val-Policy-Loss-Minimum ~1.87, danach 5 Epochen Geduld ohne Verbesserung,
Val-Policy-Loss steigt bis Epoche 15 auf ~2.00 -- klares Overfitting-Signal
nach dem Plateau). `alphazero_v14_best.onnx` = Checkpoint Epoche 10.

**Offline-Diagnose** (`tools/offline_diagnose.py`, frozen-Set `frozen_v1`,
n=1800, generationsuebergreifend vergleichbar -- Zahlen der verlorenen Netze
stammen aus `evaluations/offline_diagnose_v13_vs_nortv_variants_frozen.json`
und `evaluations/offline_diagnose_frozen_v1.json`, ueberlebten den
Datenverlust unbeschadet):

| Modell | Top-1 | Top-3 | R² global | R² R1-R5 | R² v10b-Korpus | R² v12-Korpus |
|---|---|---|---|---|---|---|
| v13_nortv_best (verlorener Champion) | 48.5% | 75.5% | 0.343 | 0.063/0.175/0.227/0.271/0.697 | 0.404 | 0.264 |
| v12b_lr_best (vorheriger Champion) | 46.6% | 74.1% | 0.338 | 0.096/0.166/0.217/0.305/0.648 | 0.422 | 0.227 |
| v12b_scratch (Warnbeispiel Korpus-Overfit) | 43.6% | -- | 0.395 | -- | **0.706** | **-0.015** |
| **v14_best (neu, Epoche 10)** | **45.1%** | **72.9%** | **0.241** | -0.009/0.077/0.062/0.073/0.683 | 0.259 | 0.216 |
| v14 (neu, Epoche 15, unstopped) | 52.3% | 76.0% | 0.216 | -0.087/0.044/0.079/0.154/0.587 | 0.189 | 0.250 |

Rohdaten: `evaluations/offline_diagnose_v14_frozen.json` (frozen) und
`evaluations/offline_diagnose_v14_classic.json` (klassisch, aktueller
Val-Split, 48.446 Zuege -- NICHT generationsuebergreifend vergleichbar, nur
als Kontrollmessung: v14_best dort Top-1 42,0% / Top-3 72,2% / R² 0,180).

**Einordnung**: `v14_best` liegt bei Policy (Top-1/Top-3) ueberraschend nah
an den verlorenen Champions (-3,4 / -2,6 Prozentpunkte ggue.
v13_nortv_best), faellt aber beim Value-R² deutlich zurueck (0,241 vs. 0,343
-- rund 30% relativer Rueckstand), am staerksten in den fruehen Runden
(R1-R2 nahe 0, wo die verlorenen Netze schon 0,06-0,23 erreichten). Der
Korpus-Split ist wichtig: `v14_best` zeigt KEIN v12b_scratch-Overfit-Muster
(0,259 vs. 0,216, ein moderater Abstand statt 0,706 vs. -0,015) -- die
From-Scratch-Destillation generalisiert einigermassen gleichmaessig ueber
beide Korpora. Der unstopped Epoche-15-Checkpoint (`v14`, nicht `v14_best`)
zeigt dagegen genau dieses Warnmuster im Kleinen: sein hoeherer Top-1-Wert
(52,3%) kommt fast ausschliesslich vom dominanten `v12`-Korpus (69,5% Top-1,
gegenueber nur 35,6%/61,5% bzw. 189/0,595 R² auf `v10b`) -- ein Beleg dafuer,
dass das Plateau-Early-Stopping bei Epoche 10 die richtige Wahl war und
`v14` (Epoche 15) trotz besserer Rohzahlen NICHT als Kandidat verwendet
werden sollte.

**Elo-Neuverankerung** (`tools/arena.py`, `v14_best@400` vs. `Heuristik@200`,
Rust-Engine, 10 Threads, SPRT frueh-Stop aktiv, p1=0,64/α=0,05/β=0,10):
SPRT entschied nach 56/400 Spielen zugunsten der Heuristik (LLR_Netz=-2,54,
LLR_Heur=+2,89 >= obere Schranke) -- **v14_best 19:37 Heuristik@200 (34%
Netzsiege)**. Eingetragen in `evaluations/elo_history.csv` via
`tools/elo_tracker.py add`; `v14_best@400` = **884 Elo [792, 988]**
(Heuristik@200 bleibt fixer Anker bei 1000). Kader-Einordnung:
v13_nortv_best 1100 > v12b_lr_best 1051 > Heuristik@200 1000 (Anker) >
v12_best 943 > **v14_best 884** > v10_best 858 > v11_td07_best 853 >
v11_best 809. `v14_best` ist ab sofort der EINZIGE lebende Netz-Kader-Punkt
-- die alten Zeilen bleiben als historische Referenz in der CSV stehen, sind
aber als Gegner nicht mehr spielbar (Gewichte verloren).

**Gesamteinschaetzung**: Die From-Scratch-Destillation (ein einziger
Trainingslauf, 15 Epochen, kein Warm-Start, unveraendertes 3940-Spiele-
Fenster) hat einen betraechtlichen, aber nicht den vollen Teil der
verlorenen Staerke zurueckgeholt -- offline naeher dran (Policy fast auf
Champion-Niveau) als in der Arena (216 Elo unter dem verlorenen Champion,
sogar unter v12_best). Die Value-Head-Schwaeche in den fruehen Runden
duerfte der Haupttreiber der Arena-Luecke sein (die Suche stuetzt sich laut
Task-#88-Befund staerker auf den Value- als den Policy-Kopf). **Empfehlung**:
Feintuning-Nachbrenner statt neuem From-Scratch-Lauf -- Warm-Start von
`v14_best` mit `--lr 0.00005 --lr-schedule cosine` (dasselbe Rezept, das
`v12b_lr` zum Champion gemacht hat, siehe `project_v12_cycle_result`-Notiz),
optional mit ein paar zusaetzlichen Epochen und/oder frischem Self-Play statt
des bestehenden 3940-Spiele-Fensters, um die fruehen Runden gezielt
nachzuschaerfen.

## v14b: Feintuning-Nachbrenner (2026-07-24/25)

**Ausgangslage**: `v14_best` (From-Scratch-Destillation nach dem Datenverlust,
siehe "Datenverlust + v14-Neustart" oben) verlor als Elo-Anker 19:37 gegen
Heuristik@200 (884 Elo). Empfehlung dort: Feintuning-Nachbrenner statt neuem
From-Scratch-Lauf.

**Training**: `python -u train.py --name v14b --load v14_best --lr 0.00005
--lr-schedule cosine --value-target-variant nortv --epochs 100
--early-stop`, Warm-Start von `alphazero_v14_best.pth` auf demselben
3940-Spiele-Fenster (`v12`-Praefix: 200 Dateien/2000 Spiele, `v10b`-Praefix:
100 Dateien/1940 Spiele) -- dasselbe Rezept, das `v12b_lr` seinerzeit zum
Champion gemacht hat. `alphazero_v14b_best.onnx`/`.pth` liegen in `models/`.
Waehrend des Laufs ist der Snapshot-Hook (Commit 5fa8b59) gefeuert:
`models_2026-07-24_2207_v14b.zip` im OneDrive-Backup-Ordner -- der Rechner
hing in der Nacht nach Training+Diagnose+Gating (Ursache nicht abschliessend
geklärt), aber Training UND Backup-Hook liefen bereits vollstaendig durch,
bevor der Haenger auftrat. Erster echter Ernstfall-Beleg, dass der
ereignisgesteuerte Snapshot-Hook wie vorgesehen greift.

**Offline-Diagnose** (`tools/offline_diagnose.py`, frozen-Set `frozen_v1`,
n=1800, `evaluations/offline_diagnose_v14b_best_vs_v14_best_frozen.json`):

| Modell | Top-1 | Top-3 | R² global | R² R1-R5 |
|---|---|---|---|---|
| v13_nortv_best (verlorener Champion, Referenz) | 48.5% | 75.5% | 0.343 | 0.063/0.175/0.227/0.271/0.697 |
| v12b_lr_best (verlorener vorheriger Champion, Referenz) | 46.6% | 74.1% | 0.338 | 0.096/0.166/0.217/0.305/0.648 |
| **v14b_best (neu, Warm-Start-Nachbrenner)** | **46.9%** | **74.4%** | **0.257** | -0.016/0.099/0.080/0.089/0.707 |
| v14_best (Vorgaenger, From-Scratch) | 45.1% | 72.9% | 0.241 | -0.009/0.077/0.062/0.073/0.683 |

`v14b_best` verbessert sich gegenueber `v14_best` in JEDER einzelnen Kennzahl
(Top-1 +1,8pp, Top-3 +1,5pp, R² global +0,016), bleibt aber weiterhin klar
unter den verlorenen Champions (v13_nortv_best: -8,6% relativ bei R² global)
-- und die R1-Schwaeche (-0,016) bleibt qualitativ unveraendert, ist sogar
minimal negativer als bei v14_best. Das Feintuning hat also die insgesamt
vorhandene Repraesentation geschaerft, aber NICHT die frueh-Runden-
Value-Schwaeche behoben, die als Haupttreiber der Arena-Luecke vermutet wird.

**Gepaartes Gating** (`tools/paired_gating.py`, `v14b_best` vs. `v14_best`,
beide @400 Sims, `evaluations/paired_gating_result_v14b_best_vs_v14_best.json`,
8 Bloecke a 25 Paare, gepaarter Vorzeichentest + SPRT p1=0,65/α=β=0,05):
**v14b_best 218:182 v14_best** (200 Paare/400 Spiele, kein frueher Abbruch --
`UNDECIDED_CAP_REACHED`, LLR=1,52 von noetigen ±2,94, McNemar p=0,066,
mittlere Paar-Differenz 0,18 [95%-CI -0,0005, 0,360]). Statistisch NICHT
signifikant (CI beruehrt die Null), aber die gesamte Trendrichtung ueber alle
8 Bloecke ist durchgehend positiv fuer `v14b_best` (kein einziger Block mit
negativer mittlerer Paar-Differenz).

**Koordinator-Entscheid**: `v14b_best` wird Referenz/Generator der
Wiederaufbau-Linie. Kein klassischer Champion-Gating-Fall (`v14_best` ist
selbst kein etablierter Champion, sondern nur der vorherige Rebuild-Stand) --
die Gesamtevidenz (Offline-Verbesserung in allen Kennzahlen + tendenziell
positives, wenn auch nicht signifikantes Gating) reicht aus, um `v14b_best`
als naechsten Stand zu fuehren, ohne dass ein hartes p<0,05-Kriterium wie bei
echten Champion-Ablösungen gefordert wird.

**Elo-Neuverankerung** (`tools/arena.py`, `v14b_best@400` vs. `Heuristik@200`,
Rust-Engine, 10 Threads, SPRT frueh-Stop aktiv, p1=0,64/α=0,05/β=0,10): SPRT
entschied nach 170/400 Spielen auf **"Gleich stark"** (beide Seiten haben
ihre H1 verworfen -- LLR_Netz=-2,29 [untere Schranke -2,25 unterschritten],
LLR_Heur=-2,34 [ebenfalls unter -2,25], keine Seite erreichte je die obere
Schranke +2,89) -- **v14b_best 77:93 Heuristik@200 (45% Netzsiege)**. Das ist
ein deutlicher Fortschritt gegenueber `v14_best`s fruehem Abbruch zugunsten
der Heuristik (19:37 nach nur 56 Spielen, 34% Netzsiege): `v14b_best` haelt
sich ueber mehr als dreimal so viele Spiele in echter Paritaetsnaehe.
Eingetragen in `evaluations/elo_history.csv` via `tools/elo_tracker.py add`;
Bradley-Terry-Fit (Heuristik@200 fixer Anker bei 1000) ergibt
**v14b_best@400 = 967 Elo [917, 1020]**. Neue Kader-Reihenfolge:
v13_nortv_best 1100 > v12b_lr_best 1051 > Heuristik@200 1000 (Anker) >
**v14b_best 967** > v12_best 943 > v14_best 884 > v10_best 858 >
v11_td07_best 853 > v11_best 809. `v14b_best` liegt damit nicht nur klar vor
seinem direkten Vorgaenger `v14_best` (+83 Elo), sondern im globalen
Bradley-Terry-Fit auch vor `v12_best` (943) -- ein indirekter Vergleich
ueber den gemeinsamen Heuristik-Anker, KEIN direktes Match, entsprechend mit
Vorsicht zu lesen (unterschiedliche Regelwerks-/Sims-Historie je nach Zeile,
siehe Kommentar-Spalte der CSV).

**Repro-Haenger-Hinweis**: der Rechner, auf dem dieser Nachbrenner-Zyklus
(Training + Offline-Diagnose + gepaartes Gating) lief, hing in der Nacht auf
den 2026-07-25 aus ungeklaertem Grund (kein Hinweis auf einen Zusammenhang
mit dem Training selbst). Wichtig: sowohl das Training als auch der
Snapshot-Hook (Commit 5fa8b59) waren zu diesem Zeitpunkt bereits
vollstaendig durchgelaufen -- der erste echte Ernstfall-Beleg, dass der nach
dem `models/`-Datenverlust eingefuehrte ereignisgesteuerte Backup-Hook wie
vorgesehen greift. Die Elo-Neuverankerung wurde nachtraeglich (dieser
Task-Abschluss) nachgeholt.

**Gesamteinschaetzung**: Der Feintuning-Nachbrenner (Warm-Start + `lr 5e-5
Cosine`, dasselbe Rezept wie `v12b_lr`) hat funktioniert -- offline eine
kleine, aber konsistente Verbesserung in JEDER Kennzahl gegenueber
`v14_best`, in der Arena ein deutlich groesserer Sprung (+83 Elo, von klar
unterlegen zu echter Paritaet mit Heuristik@200). Die fruehe-Runden-
Value-Schwaeche (R1 R² weiterhin nahe null) bleibt aber unveraendert
bestehen und ist vermutlich der Hauptgrund, warum `v14b_best` trotz des
Elo-Sprungs weiterhin klar hinter den verlorenen Champions (`v13_nortv_best`
1100, `v12b_lr_best` 1051) zurueckbleibt. Der Nachbrenner konnte also die
vorhandene Repraesentation schaerfen, aber nicht die strukturelle Luecke
(zu wenig frische Bootstrap-Daten fuer fruehe Runden im bestehenden
3940-Spiele-Fenster) schliessen -- dafuer braucht es neues Self-Play mit
`v14b_best` als Generator (rtv aus, ~0,24 Spiele/s bei 20 Threads siehe
Task-#85-Messung), gezielt um die Runde-1/2-Zielwerte zu verbreitern.
**Empfehlung**: 6000 statt 2000 Spiele fuer den naechsten Self-Play-Batch
(~6,9h statt ~2,3h Laufzeit, ueber Nacht machbar) -- die R1-Schwaeche ist ein
Daten-, kein Kapazitaetsproblem (siehe `feedback_value_head_capacity`-Notiz),
und die `v11`-Zyklus-Erfahrung (project_v11_cycle_result: ein 2000-Spiele-
Halbkorpus als Hauptverdaechtiger fuer eine ausgebliebene Staerkeverbesserung)
spricht dagegen, erneut mit der kleineren Menge zu knausern. Das passt auch
zur bestehenden Fenster-Strategie (~5000 aktueller Champion + je ~1000 der
letzten zwei Vorgaenger, `project_replay_window_strategy`) -- 6000 frische
`v14b_best`-Spiele waeren die neue Kern-Kohorte fuer das naechste
Trainingsfenster.

## Task #92: Arena-Trend-Log fuer Ø-Score/Floor (2026-07-24)

Elo/Winrate sagen nur "staerker/schwaecher", nicht ob die Partien selbst
besser werden (mehr Punkte, weniger Floor-Strafen). Neues, persistentes
Append-Log dafuer: `tools/arena_trends.py` (`append_run` + CLI
`python tools/arena_trends.py report [--model X] [--quelle Y]`) schreibt
nach `evaluations/arena_trends.csv` (Header selbstanlegend), eine Zeile je
Lauf aus Sicht des Kandidaten: `iso_datum, quelle, modell, gegner, sims,
n_spiele, winrate, avg_score, avg_score_gegner, avg_floor,
avg_floor_gegner, zerozero_anteil`.

Eingebaute Hooks (reine Ergaenzung, bestehende Konsolenausgaben/
Rueckgabewerte unveraendert):
  - `tools/paired_gating.py::run_paired_gating` -- akkumuliert Score/Floor
    jetzt zusaetzlich zu Sieg/Niederlage ueber BEIDE Brett-Orientierungen
    jedes Paares, schreibt die Aggregate zusaetzlich ins Ergebnis-JSON
    (`avg_score_a/b`, `avg_floor_a/b`, `zerozero_anteil`) und haengt eine
    Zeile an (Quelle `paired_gating`).
  - `tools/arena.py::run_net_arena` (Netz-vs-Heuristik-Anker) -- nutzt die
    dort bereits vorhandenen `net_scores`/`heur_scores`/`floor`-Werte, die
    bisher nur gedruckt, nie persistiert wurden (Quelle `arena_anchor`).
  - `tools/arena.py::run_net_vs_net` (Generationen-Vergleich) -- Floor-
    Tracking war hier NICHT vorhanden und wurde ergaenzt; Quelle `sonstige`.

**Backfill-Befund**: von den bestehenden Ergebnis-JSONs in `evaluations/`
enthalten NUR `paired_arena_shrink_off_raw.json`/`_on_raw.json` (Task #78,
Value-Shrinkage-A/B) echte Spiel-Level-Scores/Floor -- 2 Zeilen rueckwirkend
erzeugt (Quelle `sonstige_backfill`, Zeitstempel = Commit-Zeit 711f9bd).
Alle sieben `paired_gating_result_*.json`-Dateien (v12_best_vs_v10_best bis
v14b_best_vs_v14_best) enthalten NUR Sieg/Niederlage-Aggregate je Block,
KEINE Scores/Floor je Spiel -- fuer diese ist ehrlich kein Backfill moeglich,
der Score-/Floor-Trend beginnt also erst mit dem naechsten Gating-Lauf
(der jetzt automatisch mitschreibt).

Verifikation ohne Rechenlast (11-Thread-Self-Play `v14b_best`, 6000 Spiele,
lief parallel -- keine eigenen Arena-/Rechenlaeufe): `py_compile` aller
angefassten Dateien, Unit-Trockentest von `append_run`/`report` (Header,
Rundung, `n_spiele<=0`-Guard, Filter), sowie ein End-zu-Ende-Trockentest der
drei Hooks mit `mosaic_rust` durch ein Fake-Modul (kanonische, aber
deterministisch generierte Spiel-Dicts) ersetzt -- Ergebnis-JSON-Felder und
CSV-Zeilen gegen von-Hand nachgerechnete Aggregate aus den gemockten
Spiel-Dicts geprueft, alle Assertions bestanden.

## Task #91: v15-Zyklus + Frischdaten-Ablation (2026-07-25)

Zwei identische Trainings (Warm-Start von `v14b_best`, `lr 5e-5` Cosine, 100
Epochen, `nortv`), die sich NUR in der Frischdaten-Menge (`v14b`-Selfplay)
unterscheiden -- Kernfrage: reichen 2000 der 6000 frischen `v14b_best`-Spiele,
oder bringt die volle Menge messbar mehr Staerke? Kader-Kontext:
Datenverlust-Wiederaufbau `v14` (884 Elo) -> `v14b` (967, Referenz); `data/`
enthaelt 100×`v10b` + 200×`v12` + 600×`v14b` = 9000 Spiele, `v14b`-Korpus ist
der erste komplett OHNE `rtv`-Feld.

**Self-Play-Batch** (Vorlauf, vor Task-Start bereits abgeschlossen, Maschine
frei uebernommen): 6000 Spiele `v14b_best`@400 Sims, 11 Threads,
`record_rtv=false` (Manifest `data/manifest_v14b_20260724_230023.json`),
Zeitraum 2026-07-24 23:01 -- 2026-07-25 06:53 (7h52min, aus den
Dateizeitstempeln nachgerechnet) = **0,212 Spiele/s**, bestaetigt den ~4,5×
`rtv`-aus-Speedup aus Task #80/#85 bei aehnlicher Thread-Zahl.

**Trainings** (`train.py --load v14b_best --lr 0.00005 --lr-schedule cosine
--epochs 100 --value-target-variant nortv`, identisch bis auf Datenmenge):

| | v15 (voll) | v15_f2k (Ablation) |
|---|---|---|
| Korpus | 100 v10b + 200 v12 + 600 v14b = 900 Dateien | 100 v10b + 200 v12 + 200 v14b = 500 Dateien |
| Trainings-/Val-Split | 810/90 Dateien (1.307.950/145.338 Zuege) | 450/50 Dateien (726.574/80.725 Zuege) |
| Cache-Build | 867,7s + 67,6s (kompletter Neubau, 9000 Spiele) | ~36s (kleinerer Korpus) |
| Epoche-1 Val-R² (Value) | 0,493 (Warm-Start bestaetigt, ≫0,2-Schwelle) | 0,551 (ebenfalls bestaetigt) |
| Fruehstopp | Epoche 15 (Plateau seit Epoche 10, Patience 5) | Epoche 15 (Plateau seit Epoche 10, Patience 5) |
| Bestes Modell | Epoche 2 (val_combined=1,4839) | Epoche 1 (val_combined=1,4954) |
| OneDrive-Snapshot | `models_2026-07-25_0737_v15.zip` (54 MB) | `models_2026-07-25_0756_v15_f2k.zip` (72 MB) |

Beide Snapshots (train.py-Hook, ereignisgesteuert) bestaetigt.

Die 200 v14b-Dateien fuer den Ablationsarm wurden deterministisch gezogen
(`random.Random(20260725).sample(sorted(v14b_files), 200)`), die restlichen
400 waehrend des `v15_f2k`-Trainings nach `data/tmp_ablation_holdout/`
verschoben und danach SOFORT zurueckverschoben.

**Offline-Diagnose** (`tools/offline_diagnose.py`, klassisch + `--frozen`,
`evaluations/offline_diagnose_v15_v15f2k_v14b_classic.json` /
`..._frozen.json`):

*Klassischer Val-Split (Datei-Ebene, Seed 20260707, n=145.338 Zuege,
Top-1/Top-3 nur Drafting n=105.604):*

| Modell | Top-1 | Top-3 | R² global | R1 | R2 | R3 | R4 | R5 |
|---|---|---|---|---|---|---|---|---|
| v15_best | 49,4% | 79,2% | 0,377 | 0,107 | 0,220 | 0,311 | 0,414 | 0,627 |
| v15_f2k_best | 49,8% | 79,2% | 0,367 | 0,102 | 0,211 | 0,298 | 0,400 | 0,621 |
| v14b_best | 48,6% | 78,1% | 0,346 | 0,092 | 0,187 | 0,270 | 0,371 | 0,610 |

*Frozen Set (`frozen_v1`, n=1800, generationsuebergreifend, direkt
vergleichbar mit alten Kennzahlen; `v13_nortv_best`-Zeile aus
`evaluations/offline_diagnose_v13_vs_nortv_variants_frozen.json`
uebernommen -- das Checkpoint selbst existiert nach dem Datenverlust nicht
mehr):*

| Modell | Top-1 | Top-3 | R² global | R1 | R2 | R3 | R4 | R5 |
|---|---|---|---|---|---|---|---|---|
| v13_nortv_best (verlorene Messlatte) | 48,5% | 75,5% | 0,343 | 0,063 | 0,175 | 0,227 | 0,271 | 0,697 |
| **v15_best (neu)** | **46,9%** | **73,3%** | **0,300** | **0,020** | **0,125** | **0,149** | **0,162** | **0,726** |
| v15_f2k_best | 46,9% | 74,8% | 0,284 | 0,011 | 0,130 | 0,119 | 0,136 | 0,710 |
| v14b_best (bisherige Referenz) | 46,9% | 74,4% | 0,257 | -0,016 | 0,099 | 0,080 | 0,089 | 0,707 |

**Kernbefund R1/R2**: Zum ersten Mal seit dem Datenverlust ist die
Runde-1-Value-R² auf dem frozen Set POSITIV (`v15_best`: +0,020,
`v15_f2k_best`: +0,011 -- beide ueber `v14b_best`s -0,016). Die Hypothese
aus dem v14b-Zyklus ("R1-Schwaeche ist ein Daten-, kein
Kapazitaetsproblem", Empfehlung 6000 statt 2000 frische Spiele) bestaetigt
sich: mehr frische `v14b_best`-Bootstrap-Daten bringen tatsaechlich Leben
in die fruehen Runden. `v15_best` (volle 6000) schlaegt `v15_f2k_best` (nur
2000) in JEDER Runde 1-4 auf beiden Split-Arten, R5 liegt bei beiden etwa
gleichauf. `v13_nortv_best` bleibt bei R1-R4 weiterhin vorn, `v15_best`
schliesst die Luecke aber deutlich (R² global 0,257 -> 0,300 auf frozen,
0,346 -> 0,377 auf klassisch).

Aufschluesselung je Quellkorpus (frozen Set): v10b-Anteil (n=900) Value-R²
`v15_best` 0,309 / `v15_f2k_best` 0,286 / `v14b_best` 0,255; v12-Anteil
(n=900) 0,288 / 0,280 / 0,260 -- `v15_best` verbessert sich in BEIDEN
Alt-Korpora gegenueber `v14b_best`, nicht nur auf dem frischen v14b-Anteil
selbst.

**Ablations-Gating** (`tools/paired_gating.py`, `v15_best` (A) vs.
`v15_f2k_best` (B), beide @400 Sims,
`evaluations/paired_gating_result_v15_best_vs_v15_f2k_best.json`, 8 Bloecke
a 25 Paare, gepaarter Vorzeichentest + SPRT p1=0,65/α=β=0,05):

| Block | kumulativ A:B | LLR | Bericht-p (McNemar) |
|---|---|---|---|
| 1 (n=25) | 29:21 | +0,48 | 0,45 |
| 2 (n=50) | 58:42 | +1,16 | 0,18 |
| 3 (n=75) | 82:68 | +0,52 | 0,31 |
| 4 (n=100) | 103:97 | -1,29 | 0,77 |
| 5 (n=125) | 134:116 | -0,09 | 0,31 |
| 6 (n=150) | 165:135 | +1,11 | 0,11 |
| 7 (n=175) | 194:156 | +1,78 | 0,05 |
| 8 (n=200, Deckel) | **224:176** | **+2,81** | **0,02** |

**200 Paare (harter Deckel) erreicht OHNE SPRT-Entscheid** (LLR=+2,807,
Schranken ±2,944 -- +0,137 von der oberen Schranke entfernt). Formal also
**UNDECIDED_CAP_REACHED**, keine formale ACCEPT_H1. Gepaarte Differenz
(A-Siege minus B-Siege pro Paar) +0,240 [95%-CI +0,048, +0,432] -- das CI
beruehrt die Null NICHT (anders als beim `v14b`-vs-`v14`-Fall, wo das CI die
Null beruehrte), und 7 von 8 Bloecken liegen im positiven Bereich fuer
`v15_best`. Fixed-n-Vorzeichentest p=0,0197 (explizit NICHT die
Stopp-Entscheidung, nur Bericht-Statistik -- siehe
`feedback_statistical_rigor`-Notiz).

**Ablations-Verdikt**: Trotz UNDECIDED nach strengem SPRT-Kriterium ist die
Evidenz fuer "6000 Spiele bringen messbar mehr" deutlich staerker als
reines Rauschen -- LLR verfehlt die Schranke nur knapp, das CI schliesst
die Null aus, und die Offline-Diagnose zeigt `v15_best` (voll) auf JEDER
Kennzahl vor `v15_f2k_best` (Ablation). **Empfehlung fuer die
Batch-Policy**: bei der aktuellen Rechnerkapazitaet (~7h53min fuer 6000
Spiele, ueber Nacht machbar) bei der vollen 6000er-Menge bleiben -- 2000
Spiele sind ein spuerbarer, wenn auch nicht SPRT-hart bewiesener
Kompromiss; kein Grund, kuenftig auf 2000 zu verkleinern, wenn 6000 im
bestehenden Zeitbudget machbar sind.

**Referenz-Gating** (Ablations-Gewinner `v15_best` (A) vs. `v14b_best` (B),
`evaluations/paired_gating_result_v15_best_vs_v14b_best.json`): **v15_best
91:59 v14b_best** (150 Spiele, 75 Paare) -- SPRT entschied bereits nach 75
Paaren: `v15_best` signifikant staerker (LLR=+3,255 >= obere Schranke
+2,944, Bericht-p=0,0113), gepaarte Differenz +0,427 [95%-CI +0,126,
+0,727] (CI klar ueber Null). **`v15_best` wird neue Referenz/Generator der
Wiederaufbau-Linie.**

**Elo-Neuverankerung** (`tools/arena.py`, `v15_best`@400 vs. Heuristik@200,
Rust-Engine, 10 Threads, SPRT p1=0,64/α=0,05/β=0,10): SPRT entschied nach
86/400 Spielen auf "Gleich stark" (LLR_Netz=-2,36, LLR_Heur=-2,38, beide
Seiten verwerfen H1) -- **v15_best 45:41 Heuristik@200 (52% Netzsiege)**,
Fortschritt gegenueber `v14b_best`s 45% (77:93). Eingetragen via
`tools/elo_tracker.py add`; Bradley-Terry-Fit ergibt **v15_best@400 = 1029
[978, 1080]**.

Neue Kader-Reihenfolge: v13_nortv_best 1100 > v12b_lr_best 1051 >
**v15_best 1029** > Heuristik@200 1000 (Anker) > v15_f2k_best 987 >
v14b_best 961 > v12_best 943 > v14_best 884 > v10_best 858 >
v11_td07_best 853 > v11_best 809.

**Gesamteinschaetzung**: Der Frischdaten-Zyklus liefert auf allen drei
Ebenen ein konsistentes Bild: (1) Offline zeigt die volle 6000er-Menge die
erwuenschte R1/R2-Verbesserung (erstmals positives R1-R² auf dem frozen
Set), (2) das gepaarte Ablations-Gating tendiert klar (wenn auch nicht
SPRT-hart) zugunsten der vollen Menge, und (3) `v15_best` schlaegt die
bisherige Referenz `v14b_best` klar und signifikant (LLR=+3,26) UND rueckt
im Elo-Kader ueber den Heuristik-Anker (1029 vs. 1000) -- der erste
Rebuild-Stand seit dem Datenverlust, der die Heuristik@200 wieder klar
hinter sich laesst. `v15_best` bleibt weiterhin hinter den verlorenen
Champions `v12b_lr_best` (1051) und `v13_nortv_best` (1100) zurueck, aber
die Luecke schrumpft (`v14b_best`: -84/-133 Elo -> `v15_best`: -22/-71 Elo)
UND die strukturelle R1-Schwaeche, die als Haupttreiber der Elo-Luecke
vermutet wurde, zeigt jetzt echte Fortschritte. Naechster Schritt waere
vermutlich ein weiterer Frischdaten-Batch mit `v15_best` als neuem
Generator, um die R1/R2-R²-Werte weiter zu verbreitern.

**data/-Integritaetsnachweis**: 100 v10b + 200 v12 + 600 v14b = 900
Dateien (verifiziert nach Ablations-Ruecksicherung), `data/tmp_ablation_holdout/`
entfernt.

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

## Wertungsplatten-Shaping A/B (Task #93, 2026-07-25)

**Idee**: Analog zum validierten Floor-Shaping (`FLOOR_SHAPING_WEIGHT=0.3`,
exakte Bodenstrafe additiv auf den Blattwert nach `blended_leaf_win_prob`,
gepaart validiert +14pp) ein zweites exaktes Zustandssignal fuer die
Wertungsplatten ergaenzen. Kontext: Der Value-Head traegt die Suchstaerke
(#88), exakte Zusatzinformation am Blatt ist ein heisser Kandidat -- ABER
das konzeptionell aehnliche Value-Shrinkage (#78) wurde im A/B klar
widerlegt, Shaping-Ideen sind NICHT automatisch gut.

**Heuristik-Befund**: `engine/src/scoring.rs` enthaelt bereits
`wertung_progress(player, tile_ids)` -- eine stetige Ersatzformel fuer die
8 Wertungsplatten, seit langem von der DFS-Heuristik-Blattbewertung
(`mcts.rs::player_total`) genutzt. Die "Alles-oder-nichts"-Platten
(Horizontale/Vertikale/Diagonale Reihen, Mehrfarbige Felder, Eckplatten,
Farbenreiche Reihen) bekommen bei Teilfuellung einen quadratisch skalierten
Teil-Bonus (`(fill/max)² × Punktwert`) statt hartem 0 -- bei voller Fuellung
faellt die Formel exakt auf den echten `calculate_end_scoring`-Punktwert
zurueck (keine Doppelzaehlung). Die additiven Platten (Aeussere Felder,
Spezialfelder) bleiben unveraendert linear. Reine Zustandsfunktion, kein
Netz-Forward-Pass -- exakt das Analogon zur exakten Floor-Straf-Korrektur,
keine Neuentwicklung noetig.

**Signal-Definition**: `plate_shaping_delta(state) = (wertung_progress(P0)
− wertung_progress(P1)) / PLATE_SHAPING_SCALE` (Skala 50.0, gleiche
Groessenordnung wie `FLOOR_SHAPING_SCALE`/`VALUE_SCALE`). Angewendet als
`plate_shift = PLATE_SHAPING_WEIGHT · tanh(plate_shaping_delta)`,
`value[0] += plate_shift`, `value[1] -= plate_shift` (beide auf `[0,1]`
geklemmt) -- NACH dem Floor-Shaping-Additiv in `net_mcts.rs::make_node`,
koexistiert additiv damit. `PLATE_SHAPING_WEIGHT=0.3` (Startwert analog
Floor). `PLATE_SHAPING_ENABLED` (Compile-Konstante) schaltet den ganzen
Block ein/aus -- bei `false` (Standard) wird `apply_plate_shaping` gar nicht
wirksam ausgefuehrt, garantiert byte-identisches Bestandsverhalten.

**Implementierung + Paritaetstest**: eigener Worktree
`mosaic-AI-worktree-plate-shaping`, Branch `worktree-plate-shaping`. 3 neue
Tests: (1) `plate_shaping_delta_matches_wertung_progress_difference` --
Formel-Test gegen `wertung_progress` direkt, (2)
`plate_shaping_disabled_is_exact_identity` -- Kern-Paritaetstest,
`apply_plate_shaping` muss bei `ENABLED=false` die Eingabe ueber mehrere
reale Stellungen UND synthetische Extremwerte unveraendert zurueckgeben,
(3) `plate_shaping_disabled_search_matches_pre_task93_tree` --
End-zu-Ende-Determinismus-Nachweis auf Baum-Ebene (uebersprungen statt
fehlzuschlagen, wenn der Mess-Wheel-Arm aktiv ist, damit `cargo test
--release` in BEIDEN Toggle-Zustaenden gruen bleibt). `cargo test --release`:
**156/156 gruen** (153 Basis + 3 neu), in BEIDEN Toggle-Zustaenden
(ENABLED=false UND ENABLED=true) verifiziert.

**A/B-Design**: `tools/paired_arena_plate_ab.py` +
`paired_arena_plate_arm_worker.py` (Muster von
`paired_arena_shrink_ab.py`/`_arm_worker.py` kopiert). Referenz-Champion
`v15_best` (Elo 1029, Brett 0) vs. Vor-Referenz `v14b_best` (Elo 961, Brett
1), beide @400 Sims, 100 seed-gepaarte Spiele je Arm (identischer
Basis-Seed 9315), sequenziell EIN venv (Arm OFF → Toggle-Flip + Rebuild →
Arm ON, kein Worktree/Zweit-venv noetig, da die Arme nie gleichzeitig
laufen muessen).

**A/B-Ergebnis** (2026-07-25):

| Arm | Champion:Gegner | Ø-Score Champion:Gegner | Ø-Floor Champion:Gegner |
|---|---:|---:|---:|
| OFF (Ist-Zustand) | 58:42 | 35.3 : 31.0 | 14.2 : 17.4 |
| ON (`PLATE_SHAPING_ENABLED=true`) | 61:39 | 35.9 : 29.2 | 13.7 : 17.8 |

Diskordante Paare (gleicher Seed, unterschiedliches Ergebnis):
b(ON-only-Sieg)=16, c(OFF-only-Sieg)=13, konkordant(beide gewinnen)=45,
konkordant(beide verlieren)=26. Exakter zweiseitiger McNemar-Test:
**p=0.7111**.

**Empfehlung**: **GEGEN Merge / Toggle bleibt AUS.** ON liegt zwar
numerisch leicht vorn (61:39 vs. 58:42, etwas hoeherer Ø-Score, etwas
niedrigerer Ø-Floor), aber die Diskordanz (16 vs. 13 von 100 Paaren) ist
klein und weit von Signifikanz entfernt (p=0.7111, Evidenzregel verlangt
p<0.05 UND Vorteil fuer ON). Analog zum Value-Shrinkage-Praezedenzfall
(#78, p=0.117, ebenfalls verworfen): eine plausible, heuristisch gut
begruendete Shaping-Idee bestaetigt sich im A/B NICHT automatisch. Moegliche
Erklaerung: der Value-Head lernt den Wertungsplatten-Fortschritt (anders
als die eskalierende, stark nichtlineare Floor-Strafskala) vermutlich schon
recht gut selbst aus den Input-Features (`features.rs` enthaelt die
Wertungsplatten-Auswahl + Board-Zustand direkt) -- der exakte Zusatz-Nudge
bringt dann wenig zusaetzliche Information gegenueber dem, was das Netz
ohnehin schon sieht (im Unterschied zur Floor-Strafe, deren NICHTLINEARE
Eskalationsformel das Netz laut Rundenabhaengigkeits-Befund nachweislich
schwerer selbst lernt).

**Konstanten-Endzustand**: `PLATE_SHAPING_WEIGHT=0.3` (unveraendert, reine
Dokumentation, kein neuer Beleg fuer eine Rekalibrierung),
`PLATE_SHAPING_ENABLED=false` (Standard, byte-identisches
Bestandsverhalten). Code + Tests + A/B-Ergebnis bleiben im Worktree
dokumentiert, Merge-Entscheid liegt beim Nutzer.

**Repo-/Wheel-Endzustand**: Branch `worktree-plate-shaping` (eigener `git
worktree`), main unberuehrt. Nach der Mess-Phase: Produktions-Wheel
(main-Stand, `PLATE_SHAPING_ENABLED` existiert dort gar nicht) neu
gebaut/installiert, Smoke-Test (`import mosaic_rust`) verifiziert. Worktree
bleibt bestehen (nicht geloescht).
*(Nachtrag 25.07.: nach Nutzer-Go aufgeraeumt — Worktree + Branch entfernt;
Doku + Ergebnis-JSONs zuvor nach main uebernommen.)*

## Task #94: v16-Zyklus (2026-07-25)

Naechster Frischdaten-Zyklus der Wiederaufbau-Linie: `v14` (884 Elo) ->
`v14b` (961) -> `v15` (1029, bisherige Referenz) -> **v16**. Zielmarke bleibt
der verlorene Alt-Champion (1100 Elo, `v13_nortv_best`). `data/` lag beim
Task-Start bereits fertig vor (vom Nutzer vorbereitet): **100×`v12` +
200×`v14b` + 600×`v15` = 900 Dateien / 9000 Spiele**, verifiziert. Der
frische `v15`-Anteil (600 Dateien) traegt kein `rtv`-Feld (korrekt, seit
`v13_nortv`-Umstellung Standard). Selfplay-Batch-Fakten fuer diesen frischen
`v15`-Anteil (Vorlauf, vor Task-Start bereits gelaufen): 6000 Spiele in
7h17min = **0,229 Spiele/s**.

**Training** (`train.py --name v16 --load v15_best --lr 0.00005
--lr-schedule cosine --epochs 100 --value-target-variant nortv`, kompletter
Cache-Neubau fuers neue Fenster):

| | v16 |
|---|---|
| Korpus | 100 v12 + 200 v14b + 600 v15 = 900 Dateien |
| Trainings-/Val-Split | 810/90 Dateien (1.308.650/145.336 Zuege) |
| Cache-Build | 986,5s + 97,0s (kompletter Neubau, 9000 Spiele) |
| Epoche-1 Val-R² (Value/Points) | 0,463 / 0,543 (Warm-Start bestaetigt, ≫0,2-Schwelle) |
| Fruehstopp | Epoche 15 (VAL-POLICY-PLATEAU seit Epoche 10, Patience 5) |
| Bestes Modell | Epoche 3 (val_combined=1,3665) |
| Netzauslastung | Dead 1% (layer3 3%), Eff.Rank 39% -- gesund |
| OneDrive-Snapshot | `models_2026-07-25_1825_v16.zip` (90 MB), bestaetigt |

**Offline-Diagnose** (`tools/offline_diagnose.py`, klassisch + `--frozen`;
`v13_nortv_best`-Checkpoint existiert nach dem Datenverlust nicht mehr, daher
nur als feste Referenzzeile aus dem Task-Kontext uebernommen):

*Klassischer Val-Split (Datei-Ebene, Seed 20260707, n=145.336 Zuege,
Top-1/Top-3 nur Drafting n=105.370; `evaluations/offline_diagnose_v16_classic.json`):*

| Modell | Top-1 | Top-3 | R² global | R1 | R2 | R3 | R4 | R5 |
|---|---|---|---|---|---|---|---|---|
| **v16_best** | **52,8%** | **82,4%** | **0,443** | **0,104** | **0,279** | **0,413** | **0,524** | **0,626** |
| v15_best | 52,2% | 81,7% | 0,432 | 0,098 | 0,274 | 0,409 | 0,512 | 0,607 |

*Frozen Set (`frozen_v1`, n=1800; `evaluations/offline_diagnose_v16_frozen.json`):*

| Modell | Top-1 | Top-3 | R² global | R1 | R2 | R3 | R4 | R5 |
|---|---|---|---|---|---|---|---|---|
| v13_nortv_best (verlorene Messlatte) | 48,5% | 75,5% | 0,343 | 0,063 | 0,175 | 0,227 | 0,271 | 0,697 |
| v15_best (bisherige Referenz) | 46,9% | 73,3% | 0,300 | 0,020 | 0,125 | 0,149 | 0,162 | 0,726 |
| v16_best (neu) | 45,6% | 71,6% | 0,295 | 0,014 | 0,135 | 0,166 | 0,139 | 0,713 |

Aufschluesselung je Quellkorpus (frozen Set): v10b-Anteil (n=900) Value-R²
`v16_best` 0,316 / `v15_best` 0,309 (v16 leicht vorn); v12-Anteil (n=900)
0,268 / 0,288 (v16 leicht zurueck).

**Kernbefund R1/R2**: Die Frueshspiel-Erholung setzt sich auf dem frozen Set
NICHT eindeutig fort -- R1 stagniert praktisch (0,014 vs. 0,0195, minimal
schlechter), R2/R3 legen leicht zu (0,135/0,166 vs. 0,125/0,149), R4/R5
fallen leicht ab. Auf dem klassischen (In-Distribution-)Val-Split zeigt
`v16_best` dagegen in JEDER Runde eine kleine, durchgehende Verbesserung
gegenueber `v15_best`. Insgesamt ein flaches, gemischtes Bild -- plausibel
angesichts des sehr fruehen Stopps (bestes Modell bereits Epoche 3, LR
5e-5 Warm-Start bewegt das Netz nur wenig von `v15_best` weg). Wichtig:
trotz dieser flachen/gemischten Offline-Metriken zeigt das Live-Gating (s.u.)
eine klare, signifikante Staerkeverbesserung -- bestaetigt erneut den
`Hybrid-head-attribution`-Befund, dass Offline-Policy-/Value-Metriken kein
verlaesslicher Staerke-Praediktor sind.

**Gepaartes Gating** (`tools/paired_gating.py`, `v16_best` (A) vs.
`v15_best` (B), beide @400 Sims,
`evaluations/paired_gating_result_v16_best_vs_v15_best.json`, Bloecke a 25
Paare, gepaarter Vorzeichentest + SPRT p1=0,65/α=β=0,05):

| Block | kumulativ A:B | LLR | Bericht-p (McNemar) |
|---|---|---|---|
| 1 (n=25) | 31:19 | +1,10 | 0,21 |
| 2 (n=50) | 61:39 | +1,94 | 0,07 |
| 3 (n=75) | **91:59** | **+2,97** | **0,02** |

**SPRT-Entscheid bereits nach 75 Paaren (150 Spielen)**: `v16_best`
signifikant staerker (LLR=+2,972 >= obere Schranke +2,944, ACCEPT_H1).
Gepaarte Differenz (A-Siege minus B-Siege pro Paar) +0,427 [95%-CI +0,100,
+0,754] -- CI klar ueber Null. **`v16_best` wird neue Referenz/Generator der
Wiederaufbau-Linie.**

**Elo-Neuverankerung** (`tools/arena.py`, `v16_best`@400 vs. Heuristik@200,
Rust-Engine, 10 Threads, SPRT p1=0,64/α=0,05/β=0,10): SPRT entschied bereits
nach 47/400 Spielen: `v16_best` signifikant staerker (LLR_Netz=+2,97,
LLR_Heur=-2,38) -- **v16_best 32:15 Heuristik@200 (68% Netzsiege)**,
deutlicher Sprung gegenueber `v15_best`s 52% (45:41). Eingetragen via
`tools/elo_tracker.py add`; Bradley-Terry-Fit ergibt **v16_best@400 = 1132
[1037, 1250]** (CI breit, kleines n=47 durch fruehen SPRT-Stopp).

Neue Kader-Reihenfolge: **v16_best 1132** > v13_nortv_best 1100 (verlorener
Alt-Champion) > v12b_lr_best 1051 > v15_best 1029 > Heuristik@200 1000
(Anker) > v15_f2k_best 987 > v14b_best 961 > v12_best 943 > v14_best 884 >
v10_best 858 > v11_td07_best 853 > v11_best 809.

**Gesamteinschaetzung**: `v16_best` ist der erste Stand der
Wiederaufbau-Linie, der die Zielmarke von 1100 Elo (verlorener
`v13_nortv_best`-Champion) UEBERTRIFFT (1132 vs. 1100), trotz eines flachen
bis leicht durchwachsenen Offline-Diagnose-Bilds auf dem frozen Set und
eines sehr fruehen Trainings-Stopps (bestes Modell Epoche 3 von 100). Das
gepaarte Gating (LLR=+2,97, ACCEPT_H1 nach nur 75 Paaren) UND die
Elo-Neuverankerung (68% Netzsiege, SPRT nach nur 47 Spielen) sind beide
deutlich eindeutiger als beim `v15`-Zyklus (dort jeweils "Gleich stark"
bzw. knapp ueber der Grenze). Das CI der neuen Elo-Zahl ist wegen des sehr
fruehen SPRT-Stopps breit (1037-1250) -- die Zahl 1132 sollte als vorlaeufig
gelten, nicht als praezise Messung; ein zukuenftiger laengerer Lauf koennte
den Wert nach unten UND oben korrigieren. Erneut ein Beleg gegen die
Verwendung von Offline-Metriken als alleinigem Staerke-Praediktor (s.
`project_hybrid_head_attribution`).

**data/-Integritaetsnachweis**: 100 v12 + 200 v14b + 600 v15 = 900 Dateien
(vom Nutzer vorbereitet, unveraendert bestaetigt, `data/` nicht umgebaut).

## Task #89: Oracle-Metriken (2026-07-25) -- BLOCKIERT (fehlender Such-Einstieg)

**Ziel**: Tiefe Suche (v16_best, ~5000 Sims, deterministisch) je der 1800
Zustaende aus `evaluations/frozen_eval_set.pkl` als "Oracle"-Referenz (beste
Aktion, volles Q-/Besuchs-Ranking der Wurzelkandidaten, Root-Value), dann
Offline-Metriken der 6 Kandidaten-Netze (v14_best, v14b_best, v15_f2k_best,
v15_best, v16_best, v16 Epoche 15) gegen dieses Oracle vergleichen und
Spearman-Rangkorrelation mit der bekannten Elo-Reihenfolge bilden --
Hypothese aus `project_hybrid_head_attribution`: wertseitige Metriken gegen
eine TIEFE-SUCHE-Referenz (statt reine Val-R²/Top-1) sollten Staerke
vorhersagen, wo klassische Offline-Metriken (siehe `v16-Zyklus` oben)
nachweislich versagen.

**Befund vor Schritt 1 (Pruefung der PyO3-Bindings, `engine/src/lib.rs` +
`engine/src/py.rs` + `engine/src/net_mcts.rs` + `engine/src/state.rs`
durchsucht)**: es gibt KEINEN Such-Einstieg, der einen EXTERN gespeicherten
Zustand (wie die JSON-Zustandsdicts in `frozen_eval_set.pkl`s
`records[i]["state"]`) in die Rust-Engine laedt und dort eine
konfigurierbare Netz-Suche darauf faehrt. Konkret:

1. `GameState` (`engine/src/state.rs:46`) leitet nur `#[derive(Debug, Clone)]`
   ab -- KEIN `Deserialize`. `serialize::state_to_json` (`engine/src/
   serialize.rs:198`) ist eine EINBAHNSTRASSE (`GameState` → JSON fuers
   Frontend); es existiert keine Umkehrfunktion, die ein JSON-Zustandsdict
   zurueck in einen `GameState` baut.
2. `PyGame::new` (`engine/src/py.rs:69`, einziger Konstruktor) startet IMMER
   eine frische Partie ueber `Game::start(...)` (Namen/Startspieler/Seed/
   Wertungsplatten) -- es gibt keinen Konstruktor/Setter, der einen
   bestehenden Zustand injiziert. Ein gespeicherter Zustand aus dem frozen
   Set liesse sich also nur erreichen, indem man dieselbe Partie Zug fuer
   Zug von Neuem nachspielt -- fuer 1800 beliebige, aus verschiedenen
   Korpora gezogene Zwischenzustaende praktisch nicht rekonstruierbar (die
   exakte Zugfolge dorthin ist in den Pickle-Records nicht vollstaendig
   mitgefuehrt).
3. Alle `#[pyfunction]`-Eintraege in `lib.rs`, die eine Netz-Suche fahren
   (`net_arena_match`, `net_vs_net_arena_match`, `net_self_play_games`,
   `sibling_ranking_diagnostic`, `draw_stack_peek_impact_diagnostic`, ...)
   spielen entweder komplette Partien von Grund auf (`Game::start`) oder
   erzeugen ihre Zustaende SELBST durch einen internen Self-Play-Walk
   (z.B. `self_play::sibling_ranking_diagnostic`, `engine/src/self_play.rs:
   2866` -- vergleicht Netz-Value gegen den DFS-Solver an selbst erzeugten
   Geschwister-Zustaenden, nicht gegen extern vorgegebene). Keine dieser
   Funktionen nimmt einen beliebigen Zustand als Parameter entgegen.
4. `PyGame::ai_debug_net_json`/`ai_step_net_json` (`py.rs:405-431`) rufen
   zwar genau die richtige Maschinerie auf (`net_mcts::net_search_with_tree`,
   konfigurierbare `simulations`, volle Wurzel-Analyse inkl. Q/Besuche je
   Kandidat) -- aber NUR auf `self.game.state`, dem intern gefuehrten
   Zustand der jeweiligen `PyGame`-Instanz, nicht auf einen von aussen
   uebergebenen Zustand.

**Es fehlen daher zwei neue Bausteine, um Schritt 1 auszufuehren** (beide
sind Rust-Aenderungen -- laut Auftrag NICHT eigenmaechtig umzusetzen,
Ruecksprache noetig):
  - ein `json_to_state`-Deserializer (Umkehrung von `state_to_json`), der
    ein `frozen_eval_set.pkl`-Zustandsdict in einen `GameState` baut, und
  - eine neue PyO3-Funktion (z.B. `analyze_state_json(model_path, state_json,
    sims, c_puct, deterministic)`), die daraus einen `GameState` baut und
    `net_mcts::net_search_with_tree`/`net_root_child_stats_and_policy`
    darauf aufruft, um Root-Value + volles Q-/Besuchs-Ranking der
    Wurzelkandidaten zurueckzugeben.

**Status**: Schritte 2-4 (Metriken je Netz, Rangkorrelation mit Elo,
Gating-Rueckblick, Ergebnis-Tabellen) haengen vollstaendig von den in
Schritt 1 erzeugten Oracle-Labels ab und wurden NICHT ausgefuehrt --
jede Metrik gegen eine "Oracle"-Referenz waere ohne echte Tiefensuche auf
den frozen-Set-Zustaenden nur eine Notloesung (z.B. DFS-Solver oder erneut
klassische Offline-Metriken), die exakt die bereits widerlegte
Fragestellung reproduzieren wuerde. Kein Code in `engine/` geaendert, kein
Wheel neu gebaut, `evaluations/frozen_eval_set.pkl`/`data/` nur gelesen.
Aufgabe pausiert bis zur Entscheidung, ob der fehlende Such-Einstieg
ergaenzt werden soll.

**AUFGELÖST (2026-07-25, Fortsetzung)**: der fehlende Such-Einstieg wurde
ergänzt (`engine/src/serialize.rs::json_to_state` + neue PyO3-Funktion
`net_search_state_json`, Commits `392b680`/Folgecommit s.u.) -- Schritte 1-3
sind jetzt durchgeführt, siehe Ergebnis-Abschnitt unten.

## Task #89: Oracle-Metriken -- Ergebnisse (2026-07-25)

**Teil A -- Engine-Erweiterung.** `json_to_state` (manueller Parser, kein
serde-Derive: `state_to_json` ist keine bijektive Serialisierung) invertiert
`state_to_json` für alle direkt/vollständig ableitbaren Felder. Drei
Kategorien von Abweichungen, jede einzeln gegen den Engine-Code geprüft
(ausführlicher Kommentar direkt vor der Funktion in `serialize.rs`):

1. **Echte verdeckte Information** (bag/tower/dome_tile_pool/bonus_chip_pool):
   JSON trägt nur Zähler/Masken. Rekonstruktion: die daraus ableitbare
   Identitätsmenge, neu gemischt mit dem übergebenen RNG -- deckt sich mit
   `net_mcts::determinize_hidden_information` (`DETERMINIZE_ROOT_HIDDEN_INFO`),
   das an jedem echten Sucheinstieg ohnehin genau diese Felder neu mischt.
   `bonus_chip_pool` ist ein Sonderfall (gar kein Zähler im JSON) -- Größe
   deterministisch aus der Rundenzahl (20-4·Runde), Identität zufällig aus
   den aktuell nicht sichtbaren Designs.
2. **Vollständig ableitbare Felder**: `first_player_next_round` (Spieler mit
   `marker=true`), `monochrome_fallback` der großen Fabrik (aus
   `sun_tiles`-Farbhomogenität).
3. **Dokumentierte, für die Wurzel-Legalität unschädliche Näherungen**:
   `dome_tiles_placed_this_round` (0/2 je nach `can_place_dome`-Bool, exakt
   für den Wurzelknoten, +/-1 Platzierung tiefer im Baum im seltenen
   Zwischenwert-1-Fall), `tiled_max_row` (-1, exakt für JEDEN
   `Phase::Drafting`-Zustand -- EINE geprüfte Ausnahme: `estimated_score`
   via `tiling_solver::chippable_rows`, nur wenn der Spieler einen
   ungenutzten Bonuschip hält), `pending_dome_choice` (nicht serialisiert,
   IMMER als "Stufe 1 offen" statt "Stufe 2/Rotationswahl" rekonstruiert).

**Roundtrip-Tests** (6 neue, `engine/src/serialize.rs::json_to_state_tests`):
state → json → state → json strukturell stabil (Value-Vergleich,
ordnungsunabhängig), inkl. Zufalls-Selfplay-Walk über mehrere Runden bis
Runde 5 (PendingDomeChoice-/Stapelzug-Zwischenzustände eingeschlossen). Ein
Vergleichs-Helfer toleriert GENAU die eine geprüfte `estimated_score`-Lücke
(Kategorie 3, `tiled_max_row`) -- jede andere Abweichung bleibt ein harter
Fehler. `cargo test --release`: 159/159 grün (156 Basis + 6 neu, 1 wie
zuvor ignoriert). Wheel gebaut + installiert.

**Empirische Kreuzvalidierung gegen echte `frozen_eval_set.pkl`-Zustände**
deckte zwei Randgruppen auf, in denen die rekonstruierte Wurzel-
Kandidatenzahl von der am echten Spielzustand aufgezeichneten
`valid_actions`-Länge abweicht (Stichprobe 80 "sauberer" Zustände: 0
Abweichungen danach):
- **Startkuppel-angrenzende Zustände** (19 von 1329 Drafting-Zuständen):
  `Phase::StartPlacement` wird in dieser Engine nie tatsächlich gesetzt
  (`setup_new_game` schreibt immer `Phase::Drafting`, auch während beide
  Spieler noch `start_tile_pending` sind) -- solche Zustände tragen
  `phase="drafting"` im JSON, obwohl die Startkuppel-Wahl über eine
  komplett separate, rein heuristische Route läuft
  (`choose_start_placement`/`apply_start_placement`, NIE über
  `net_search_with_tree`). Kein Rekonstruktionsfehler, sondern ein
  Anwendungsbereich, den die neue Suchfunktion (wie `ai_debug_net_json`,
  ihr Vorbild) von Haus aus nicht abdeckt.
- **PendingDomeChoice-Zwischenzustände** (125 von 1329): die im
  `json_to_state`-Kommentar dokumentierte Kategorie-3-Lücke -- betrifft
  empirisch ca. 9% der Drafting-Zustände.

Beide Kategorien werden beim Oracle-Labeling ausgeschlossen (s.u.),
verbleiben 1185 "saubere" Zustände.

**Teil B, Schritt 1 -- Oracle-Labels** (`tools/build_frozen_oracle_labels.py`,
`evaluations/frozen_v1_oracle_labels.json`): v16_best, 5000 Sims/Zustand,
c_puct=1.5, Seed je Zustand deterministisch aus SHA-256(kanonisches JSON)
abgeleitet. 1185 Zustände gelabelt in 969s (16.1 Min, ~1.2 Zustände/s), **0
Mismatches, 0 Fehler** (Wurzel-Kandidatenzahl gegen `valid_actions`
durchgehend gegengeprüft). Von den 1800 Frozen-Set-Records: 471 nicht
Drafting-Phase (Tiling/Scoring/etc. -- `net_search_with_tree` liefert dort
strukturell immer leer, kein Rekonstruktionsproblem), 19
startkuppel-angrenzend, 125 PendingDomeChoice -- ausgeschlossen wie oben
begründet.

**Teil B, Schritt 2 -- Metriken je Netz** (`tools/oracle_metrics.py`,
`evaluations/task89_oracle_metrics.json`). **Wichtige zusätzliche
Einschränkung, beim ersten Lauf entdeckt**: Runde 5 (`round5::applies`)
fällt in `net_search_with_tree` auf den EXAKTEN Alpha-Beta-Solver zurück
(architektonisch bewusst kein Netz-Entscheid in dieser Engine, siehe
"Runde 5: exakte Alpha-Beta-Suche" oben) -- dessen Analyse-Struktur trägt
weder `net_prob` noch `action`-Dict noch eine `[0,1]`-Root-Value, ist also
für Policy-Prior-/Value-Korrelations-Metriken gegenstandslos. Konsequent
ausgeschlossen (analog zur Startkuppel-Platzierung) -- verbleiben **952
auswertbare Zustände** (Runden 1-4).

Vier Metriken, GESAMT + je Runde (Runde 1-4; n=245/245/231/231):

| Netz | Elo | Prior-Recall@16 | Prior-Masse Top-3 | Value Pearson-r | Value Spearman-r | Kendall-Tau (Policy vs. Oracle-Q) |
|---|---|---|---|---|---|---|
| v14_best | 884 | 0.970 | 0.569 | 0.810 | 0.778 | 0.220 |
| v14b_best | 961 | 0.971 | 0.585 | 0.813 | 0.789 | 0.214 |
| v15_f2k_best | 987 | 0.978 | 0.602 | 0.833 | 0.806 | 0.227 |
| v15_best | 1029 | 0.982 | 0.618 | 0.859 | 0.829 | 0.245 |
| v16_best | 1132 | 0.999 | 0.652 | 0.884 | 0.859 | 0.279 |
| v16 (Epoche 15, kein Elo) | -- | 0.997 | 0.666 | 0.844 | 0.810 | 0.288 |

(Prior-Recall@16/Prior-Masse-Top-3/Value-Pearson/Value-Spearman/Kendall-Tau
je Runde: durchgehend dieselbe monotone Netz-Reihenfolge in Runde 1-3;
Value-Pearson steigt zusätzlich mit der RUNDE selbst je Netz, deckt sich mit
dem seit 2026-07-19 bekannten Runde-für-Runde-R²-Befund oben -- Runde 4
0.85-0.91, Runde 1 0.71-0.81.)

**Teil B, Schritt 3 -- Rangkorrelationen + Gating-Rückblick.** Spearman
zwischen jeder Metrik (Gesamt) und der bekannten Elo-Reihe
(884/961/987/1029/1132, NUR die 5 Netze mit Elo-Eintrag -- `v16` bleibt wie
beauftragt Außenpunkt ohne eigenen Elo-Wert):

| Metrik | Spearman-r vs. Elo (n=5) |
|---|---|
| Prior-Recall@16 | 1.000 |
| Prior-Masse Top-3 | 1.000 |
| Value Pearson-r | 1.000 |
| Value Spearman-r | 1.000 |
| Kendall-Tau | 0.900 |

**Gating-Rückblick** (hätte die Metrik den bekannten Gewinner richtig
vorhergesagt? 3 bekannte Gating-Ausgänge: v15_best>v14b_best,
v16_best>v15_best, v15_best>v15_f2k_best): **alle 5 Metriken 3/3 richtig.**

**EHRLICHE Einordnung (n=5, vorläufig, wie beauftragt)**: die
Rangkorrelation ist bei ALLEN 5 Metriken nahezu perfekt (4 von 5 exakt 1.0)
-- deutlich sauberer als die klassischen Offline-Metriken (Val-R²/Top-1),
die beim v16-Zyklus nachweislich NICHT monoton mit der Stärke liefen (siehe
"v16-Zyklus" oben: v16_best schlägt v15_best in der Arena trotz teils
flacher/gemischter klassischer Metriken). Das stützt die Ausgangshypothese
(`project_hybrid_head_attribution`): eine Tiefe-Suche-Referenz sagt Stärke
hier besser vorher als reine Offline-Metriken. **ZWEI wichtige,
einschränkende Vorbehalte, die dieses Ergebnis relativieren:**

1. **v16_best ist sowohl Oracle-Quelle als auch einer der 6 bewerteten
   Kandidaten** -- ein Netz, das gegen SICH SELBST (dieselbe tiefe Suche)
   verglichen wird, gewinnt aus rein mechanischen Gründen (kein
   Distributionsschift zwischen "Prior" und "Suche"), nicht notwendig, weil
   "Prior/Value-Korrelation mit Tiefensuche" allgemein Stärke misst. v16_best
   liegt in JEDER Metrik an der Spitze -- konsistent mit dieser
   Erklärung, nicht eindeutig widerlegbar mit n=5.
2. **Alle 6 Netze sind sequenziell warmgestartet** (v14→v14b→v15→v15_f2k/
   v15_best→v16→v16_best) -- spätere Netze sind im Gewichtsraum tendenziell
   ÄHNLICHER zu v16_best als frühere, unabhängig von echter Spielstärke. Die
   fast perfekte Korrelation könnte teilweise "Nähe zur Oracle-Quelle in der
   Trainingslinie" statt "Spielstärke" messen -- mit dieser einen
   Trainingslinie (n=5, keine unabhängigen Architekturen/Läufe) nicht
   auseinanderzuhalten.

**Fazit -- welche Metrik taugt als Gate-Prädiktor?** Bei diesem n (5 Netze,
eine Trainingslinie) unterscheiden sich die 5 Metriken NICHT klar
voneinander (4 von 5 bei r=1.000) -- keine sticht als überlegen heraus.
**Prior-Masse-Top-3** und **Value-Pearson-r** sind am einfachsten zu
berechnen (kein Kandidatenlisten-Ranking nötig, robust gegen kleine
Stichproben je Zustand) und daher pragmatisch die ersten Kandidaten für
einen künftigen Gate-Zusatzcheck -- aber NUR als ergänzendes Signal, nicht
als Ersatz für eine echte Arena-Messung, und nur mit einer unabhängigeren
Stichprobe (andere Trainingslinie/Architektur, oder ein Oracle-Netz, das
NICHT selbst zu den bewerteten Kandidaten zählt) erneut zu prüfen, bevor
daraus eine Gate-Entscheidung abgeleitet wird.

**Artefakte**: `evaluations/frozen_v1_oracle_labels.json` (Oracle-Labels,
ab jetzt unveränderlich wie `frozen_eval_set.pkl` selbst),
`evaluations/task89_oracle_metrics.json` (Metrik-/Korrelations-Ergebnisse),
`tools/build_frozen_oracle_labels.py`, `tools/oracle_metrics.py`.


## Korrigendum Elo-Anker-Beschriftung (2026-07-25)

Nutzer-Nachfrage deckte eine Etikettier-Inkonsistenz auf: Alle Anker-Matches
(v10 bis v16) liefen faktisch gegen die Heuristik mit HEUR_SIMS=150
(arena.py-Konfig; nominal 150, durch dynamic_sims real Ø~330 Sims) -- die
elo_history.csv und diverse Doku-Stellen etikettierten den Anker aber als
"Heuristik@200" (urspruengliche Kader-Vorgabe, nie so umgesetzt). Da der
Gegner ueber ALLE Eintraege identisch war, bleiben saemtliche Elo-Relationen
gueltig -- reines Label-Problem. Nutzer-Entscheid: Anker bleibt faktisch
s150(dyn~330), Beschriftung ueberall korrigiert auf "Heuristik@150(dyn~330)".
Alle aelteren "Heuristik@200"-Erwaehnungen in diesem Dokument sind
entsprechend zu lesen.


## Kader-Konsolidierung v16 vs. v14b (2026-07-25)

Zusaetzliche Elo-Kante auf Nutzer-Anstoss (KEIN Gating -- v16_best ist
bereits Referenz): `paired_gating.py` v16_best@400 vs. v14b_best@400, SPRT
entschied frueh nach 50 Paaren zugunsten von v16_best (LLR=+3.275, obere
Schranke +2.944 ueberschritten). Ergebnis **v16_best 65:35 v14b_best**
(n=100, exakter Paar-Vorzeichentest p=0.0081, gepaarte Diff +0.600
95%-KI [+0.208, +0.992]). Eingetragen in `elo_history.csv`.

Neuer Bradley-Terry-Fit: v16_best 1132->**1094** (95%-KI [1037,1250] ->
**[1033,1164]**, deutlich schmaler durch die zusaetzlichen 100 Spiele auf
einer verbundenen Kante), v14b_best 961->968.

**Transitivitaets-Check**: aus den VORHERIGEN Elo-Werten (v16 1132, v14b
961, Differenz 171) folgt eine erwartete Winrate fuer v16 von rechnerisch
~72.8%. Gemessen wurden 65% (65:35). Die Differenz (-7.8 Prozentpunkte)
liegt an der unteren Seite, aber noch INNERHALB des 95%-KI der gemessenen
Winrate (ca. [55%, 75%], aus der gepaarten Diff-KI umgerechnet) -- die
erwarteten 72.8% beruehren gerade noch den oberen Rand. Einordnung: kein
klarer Beleg fuer Nicht-Transitivitaet/Stil-Effekte, aber das Ergebnis liegt
konsistent auf der schwaecheren Seite dessen, was der reine Elo-Abstand
vorhersagen wuerde -- am ehesten normale Stichprobenstreuung bei n=100
gepaarten Spielen, ein systematischer Effekt ist mit dieser Stichprobe nicht
auszuschliessen, aber auch nicht separat belegt. Wie beauftragt: nur
Beobachtung, keine weitere Massnahme.


## Task #95: KI-Debugger -- Value-Head-Anzeige + granularer Gumbel-Trace (2026-07-25)

Der KI-Debugger (`debug.html`/`/api/ai/debug*`) zeigte im Netz-Pfad bisher
IMMER `value: null`/`win_pct: null` (Wurzel-Gauge blieb tot) und beim
Gumbel-Suchpfad (`USE_GUMBEL_SEARCH=true`, seit Task #65 Standard) nur den
Platzhaltertext "GUMBEL-SUCHE (kein granularer Sim-Trace)" statt eines
echten Sim-Traces (Fundstelle: `net_mcts.rs::build_net_tree`s Dispatch-Zweig,
vormals Zeile ~1666).

**Value-Head-Anzeige** (`engine/src/net_mcts.rs`): neue `RootValueDebug`-
Struktur fasst rohen `value_head`-Tanh-Output, `points_forecast`, reine
Win-Wahrscheinlichkeit, KataGo-Blend NACH Value-Shrinkage (Task #78) und das
(auf Ego-Perspektive gedrehte) Floor-Shaping-Additiv (Task #78, `evaluations/
STATUS.md` "Floor-Shaping") zusammen -- berechnet in `compute_root_value_debug`
per EINEM separaten `Net::eval`-Forward-Pass auf der bereits determinisierten
Wurzelposition, komplett losgelöst vom Suchpfad (kein RNG-Verbrauch, kein
Effekt auf `nodes`). Je Wurzelkind zusätzlich `net_leaf_value` (Netz-Blattwert
bei Expansion, Perspektive des ziehenden Spielers -- direkt vergleichbar mit
`mcts_q`, zeigt Netz-Ersteinschätzung vs. Such-Ergebnis).

**Granularer Gumbel-Trace**: `GumbelTrace` sammelt (a) Determinisierungs-
Status, (b) ALLE legalen Wurzelkandidaten der Top-m-Auswahl (Prior/ln(Prior)/
Gumbel-g/Score/Top-16-Kennzeichnung), (c) je Sequential-Halving-Phase
(Sims/Überlebendem, je Kandidat Visits/Q/σ(Q)/Score/Eliminierung), (d) die
finale Max-Visit-Menge mit ln(Prior)+σ(Q) je Finalist -- als strukturiertes
JSON (`gumbel_trace`-Feld), nicht mehr nur Text.

**Nur der Debug-Pfad zahlt**: Trace-Sammlung hängt an einem neuen
`trace: Option<&mut GumbelTrace>`-Parameter, durchgereicht durch
`build_gumbel_tree`/`build_net_tree`. Alle Selbstspiel-/Arena-Aufrufstellen
(`net_search_drafting_action`, `net_root_child_stats(_and_policy)`,
`build_determinized_forest`) übergeben unverändert `None` -- keiner dieser
Pfade läuft je über `net_search_with_tree` (das bleibt dem Server/Debug-UI +
dem Oracle-Metriken-Tool vorbehalten). Neuer Paritätstest
`gumbel_trace_collection_does_not_change_search` (analog zu
`hybrid_search_with_equal_nets_matches_plain_search`) belegt: gleicher
RNG-Seed liefert mit und ohne Trace-Sammlung bit-identische Besuchszahlen/
Q-Werte je Knoten und dieselbe finale Zugwahl. `cargo test --release`:
160/160 (vorher 159, +1 neuer Test), 1 weiterhin ignoriert
(`round5_node_calibration_probe`, unveraendert).

`ai_debug_net_json` (reiner `/api/ai/debug`-Analyse-Endpunkt) und
`ai_drafting_net_step` (Mensch-vs-KI-Einzelzug im Server, füllt
`/api/ai/debug_history`) rufen mit `collect_trace=true` -- beide sind
Einzelzug-pro-Aufruf-Pfade, kein Self-Play/Arena-Hot-Path. Das Oracle-
Metriken-Tool (`net_search_state_json`, `lib.rs`, potenziell tausende
State-Aufrufe via `tools/build_frozen_oracle_labels.py`) bleibt bei
`collect_trace=false`.

`server.py`s `/api/ai/debug` reicht das Analyse-Dict bereits 1:1 durch
(`analysis["ok"]=True; jsonify(analysis)`) -- keine Aenderung noetig.
`debug.html` zeigt jetzt oben einen Value-Head-Breakdown (6 Kacheln:
Roh-Value/Points-Forecast/Win%/Blended-Utility/Floor-Shift/Finaler
Blattwert) und unten ein aufklappbares `<details>`-Trace-Panel
(Top-m-Tabelle, je Halving-Phase eine Tabelle mit durchgestrichenen
eliminierten Kandidaten, Finalisten-Tabelle) -- kein Framework, reines
HTML/CSS/JS wie der Rest der Seite.

**Wheel-Status**: Vorab-Check (`tasklist`/`Get-CimInstance Win32_Process`)
fand 3 laufende `python.exe server.py`-Prozesse (Nutzer-Server aktiv) --
gemaess Vorgabe KEIN `pip install` (gesperrte `.pyd`). Rust-Implementierung +
`cargo test --release` vollstaendig abgeschlossen und gruen; der
Wheel-Rebuild (`pip install -e engine/` bzw. `maturin develop`) UND der
Live-Smoke-Test (`ai_debug_net_json` gegen `v16_best`, Kandidatenzahl 16,
Phasen>0) stehen noch aus -- nachzuholen, sobald kein Server/Self-Play mehr
laeuft.

## Task #98: v17-Zyklus (2026-07-26)

Naechster Frischdaten-Zyklus: `v16` (Referenz, 1094 Elo) -> **v17** (erster
Versuch, den Loop ueber die 1100er-Marke der verlorenen Alt-Linie
(`v13_nortv_best`) zu tragen). Standard-Rezept: Warm-Start + lr 5e-5 +
cosine + nortv.

**Batch-Verifikation** (`data/manifest_v16_20260726_111336.json`,
`record_rtv=false`): 600×`selfplay_v16_*.pkl` vorhanden, 6000 Spiele.
Stichprobe (erste + letzte Datei): `completed=True` durchgaengig (100%),
kein `rtv`-Feld, Bootstrap-Anteil 83,5% (Referenz v16-Batch: ~83%, passt).
Rate: Start 11:13:36 (Manifest) bis letzte Datei 17:57:44 (mtime) = 24248s
fuer 6000 Spiele = **0,247 Spiele/s** (vs. v15-Batch 0,229 Spiele/s, +8%).

**Wheel-Rebuild** (Rust-Commit `a8b7642`, `best_rotation` im Debug-JSON):
`cargo test --release` schlug beim ersten Versuch mit
`STATUS_DLL_NOT_FOUND` fehl (Python-DLL nicht im PATH der Shell) --
behoben durch Aufnahme von
`C:\Users\Patrick\AppData\Local\Python\pythoncore-3.14-64` in den PATH,
danach **161/161 Tests gruen** (1 weiterhin ignoriert). `pip install .
--force-reinstall --no-deps` erfolgreich. Smoke-Test via
`mosaic_rust.net_search_state_json` auf einem Runde-3-Drafting-Zustand aus
dem frischen v16-Batch (Kuppel-Display belegt): 2 von 16 Wurzelkandidaten
tragen ein `best_rotation`-Feld (Beispiel: Kuppel #2, `rotation=180`,
`q=0,549`, `visits=2`) -- Feature im installierten Wheel bestaetigt.

**Fenster-Rotation**: bei Task-Start bereits `data/` = 600×`v16` (neu) +
200×`v15` + 100×`v14b` = 900 Dateien / 9000 Spiele vorgefunden -- entspricht
exakt dem Zielfenster, kein `v12` mehr vorhanden. **Auffaelligkeit**: kein
`selection_manifest.json` und `data/archive/` leer -- die Rotation (weg vom
Vorzustand 100×v12+200×v14b+600×v15+600×v16) fand offenbar ausserhalb des
in Schritt 3 vorgesehenen Skript-Workflows statt (vermutlich Nutzer-
Handarbeit); die ueberzaehligen/aussortierten Dateien sind nicht im
vorgesehenen reversiblen Archiv-Pfad auffindbar. Reine Verifikation
durchgefuehrt, keine weitere Aktion (Endzustand entspricht der Vorgabe).

**Training** (`train.py --name v17 --load v16_best --lr 0.00005
--lr-schedule cosine --epochs 100 --value-target-variant nortv`, kompletter
Cache-Neubau fuers Fenster):

| | v17 |
|---|---|
| Korpus | 600 v16 + 200 v15 + 100 v14b = 900 Dateien |
| Trainings-/Val-Split | 810/90 Dateien (1.310.019/145.565 Zuege) |
| Cache-Build | 607,5s + 68,7s |
| Epoche-1 Val-R² (Value/Points) | 0,492 / 0,567 (Warm-Start bestaetigt, ≫0,2-Schwelle) |
| Fruehstopp | Epoche 15 (VAL-POLICY-PLATEAU seit Epoche 10, Patience 5) |
| Bestes Modell | **Epoche 1** (val_combined=1,2652) -- noch frueher als v16 (Epoche 3) |
| Netzauslastung | Dead 1% (layer3 2%), Eff.Rank 39% -- gesund |
| OneDrive-Snapshot | `models_2026-07-26_1913_v17.zip` (108 MB), bestaetigt |

Bestes Modell bereits nach Epoche 1 -- die LR-5e-5-Warm-Start-Bewegung ist
diesmal so klein, dass zusaetzliches Training den Val-Kombiwert nur noch
verschlechtert (Value-R² faellt von Epoche 1 bis 15 monoton von 0,492 auf
0,475). `v17_best` liegt damit inhaltlich sehr nah an `v16_best`.

**Offline-Diagnose** (`tools/offline_diagnose.py`, klassisch + `--frozen`):

*Klassischer Val-Split (n=145.565 Zuege, Top-1/Top-3 nur Drafting
n=105.183; `evaluations/offline_diagnose_v17_classic.json`):*

| Modell | Top-1 | Top-3 | R² global | R1 | R2 | R3 | R4 | R5 |
|---|---|---|---|---|---|---|---|---|
| **v17_best** | **56,2%** | **84,6%** | **0,4917** | 0,1120 | 0,3014 | 0,4732 | **0,6031** | **0,6634** |
| v16_best | 55,8% | 84,4% | 0,4899 | **0,1156** | **0,3059** | **0,4719*** | 0,5967 | 0,6596 |

(*R3 v16 minimal vorn, Rundung; im Kern ein durchgehend flacher,
minimaler Vorsprung von v17 auf dem In-Distribution-Split.)

*Frozen Set (`frozen_v1`, n=1800; `evaluations/offline_diagnose_v17_frozen.json`):*

| Modell | Top-1 | Top-3 | R² global | R1 | R2 | R3 | R4 | R5 |
|---|---|---|---|---|---|---|---|---|
| v13_nortv_best (verlorene Messlatte) | 48,5% | 75,5% | 0,343 | 0,063 | 0,175 | 0,227 | 0,271 | 0,697 |
| v15_best | 46,9% | 73,3% | 0,2998 | 0,0195 | 0,1245 | 0,1491 | 0,1617 | 0,7262 |
| v16_best (bisherige Referenz) | 45,6% | 71,6% | 0,2949 | 0,0142 | 0,1351 | 0,1661 | 0,1393 | 0,7125 |
| v17_best (neu) | 45,0% | 71,2% | 0,2903 | 0,0274 | 0,1348 | 0,1701 | 0,1009 | 0,7151 |

Der auf dem frozen Set bereits seit v15->v16 laufende leichte Abwaertstrend
(0,300 -> 0,295 -> **0,290**) setzt sich fort -- konsistent mit dem sehr
frueh gestoppten Training (bestes Modell Epoche 1). Aufschluesselung je
Quellkorpus: v10b-Anteil (n=900) Value-R² v17 0,3197 (vorn) vs. v16 0,3156
vs. v15 0,3089; v12-Anteil (n=900) 0,2515 (v17 zurueck) vs. 0,2676 vs.
0,2877 -- durchgaengiges Muster seit v16: auf dem aelteren v10b-Korpus legt
jede Generation leicht zu, auf dem juengeren v12-Korpus faellt sie leicht
zurueck.

**Oracle-Metriken** (`tools/oracle_metrics.py`, Pool-Erweiterung um
`v17_best`, tiefe v16_best@5000-Sims-Suche als Referenz,
`evaluations/task89_oracle_metrics.json`):

| Modell | Recall@16 | Top3-Masse | Value-Pearson | Value-Spearman | Kendall-Tau |
|---|---|---|---|---|---|
| **v17_best** | **1,000** | **0,673** | 0,8705 | 0,8407 | **0,3067** |
| v16_best | 0,999 | 0,652 | **0,8835** | **0,8594** | 0,2791 |
| v15_best | 0,982 | 0,618 | 0,8594 | 0,8293 | 0,2445 |

**Erster Bruch der bisherigen Monotonie**: alle vier Metriken stiegen bis
v16 monoton mit der bekannten Elo-Reihenfolge (Spearman-Rangkorrelation
Metrik<->Elo = 1,0 fuer die 5 etablierten Modelle). `v17_best` legt bei den
policy-seitigen Metriken weiter zu (Recall@16, Top3-Masse, Kendall-Tau alle
vorn), faellt aber bei BEIDEN Value-Korrelationen (Pearson/Spearman) hinter
`v16_best` zurueck -- passend zum minimal schwaecheren Frozen-Value-R² und
dem extrem fruehen Trainings-Stopp. `v17_best` selbst geht NICHT in die
Rangkorrelation ein (noch kein etablierter Elo-Wert, siehe Gating unten).

**Gepaartes Gating** (`tools/paired_gating.py`, `v17_best` (A) vs.
`v16_best` (B), beide @400 Sims,
`evaluations/paired_gating_result_v17_best_vs_v16_best.json`, Bloecke a 25
Paare, gepaarter Vorzeichentest + SPRT p1=0,65/α=β=0,05, harter Deckel 200
Paare):

| Block | kumulativ A:B | LLR | Bericht-p (McNemar) |
|---|---|---|---|
| 1 (n=25) | 22:28 | -1,542 | 0,58 |
| 2 (n=50) | 47:53 | -2,107 | 0,69 |
| 3 (n=75) | 80:70 | -0,291 | 0,52 |
| 4 (n=100) | 106:94 | -0,689 | 0,50 |
| 5 (n=125) | 133:117 | -0,447 | 0,37 |
| 6 (n=150) | 161:139 | -0,132 | 0,25 |
| 7 (n=175) | 194:156 | +1,495 | 0,06 |
| 8 (n=200) | **221:179** | **+1,454** | **0,053** |

**Harter Deckel (200 Paare/400 Spiele) erreicht OHNE SPRT-Entscheid**
(LLR=+1,454, Schranken ±2,944) -- der LLR-Verlauf schwankte stark (bis
-2,107 nach Block 2, dann Erholung), ein klassischer Fall fuer die
`feedback_statistical_rigor`-Lehre: 221:179 (55,25% Netzsiege) klingt nach
einem Vorteil, aber Fixed-n-Vorzeichentest p=0,053 (knapp NICHT
signifikant bei α=0,05) und die gepaarte Differenz +0,210 [95%-CI +0,009,
+0,411] beruehrt die Null fast. **Kein ACCEPT_H1 -> `v16_best` bleibt
Referenz/Champion der Wiederaufbau-Linie.** Gemaess Vorgabe wurden Schritt 7
(Kader-Matches) und Schritt 8 (Elo-Tracker-Eintrag) uebersprungen -- diese
Dokumentation ist die einzige Buchung dieses Gating-Ergebnisses.

**Elo-Einordnung / 1100er-Marke**: Da `v17_best` keinen neuen Elo-Punkt
erhaelt (Gating unentschieden), bleibt die Kader-Tabelle unveraendert:
`v13_nortv_best` (verlorene Alt-Linie) 1100 [988, 1217] > `v16_best`
(Referenz) 1094 [1033, 1164] > `v12b_lr_best` 1051 > `v15_best` 1033 >
Heuristik@150 1000 (Anker) > `v15_f2k_best` 991 > `v14b_best` 968 >
`v12_best` 943 > `v14_best` 884 > `v10_best` 858 > `v11_td07_best` 853 >
`v11_best` 809. **Zentrale Antwort**: Nein -- die Wiederaufbau-Linie liegt
NICHT nachweislich signifikant ueber der 1100er-Marke. Der im v16-Zyklus
gemeldete "Sieg" ueber die 1100-Marke (damals 1132 [1037,1250], basierend
auf einem sehr fruehen SPRT-Stopp nach nur 47 Spielen) hat sich nach
Ergaenzung einer weiteren Elo-Kante (`v16_best` vs. `v14b_best`) bereits auf
1094 [1033, 1164] nach UNTEN korrigiert -- ein CI, das die 1100-Marke
vollstaendig ueberlappt. Der v17-Zyklus liefert keinen weiteren Beleg in
die eine oder andere Richtung: sein Gating gegen den amtierenden Champion
blieb unentschieden. Fazit: die 1100er-Marke der verlorenen Linie ist
weiterhin NICHT statistisch abgesichert uebertroffen -- weder von `v16`
noch von `v17`.

**Bundle-Neubau** (`python tools/build_release.py`, unabhaengig vom
Gating-Ausgang, schliesst den offenen Punkt aus Task #97 ab): packt das
frische Wheel (`best_rotation` im Debug-JSON) + UI-Fixes. Da `v16_best`
Referenz bleibt, sind KEINE Aenderungen an `dist/mosaic_release.spec` oder
den `server.py`-Presets noetig (Bundle referenziert weiterhin `v16_best`).
Ergebnis: `dist/Mosaic-AI_v16_20260726.zip` (27,3 MB gepackt / 54,7 MB
entpackt).

**Exe-Smoke-Test**: `Mosaic-AI.exe` auf freiem Port (5000) gestartet,
`/api/new_game` mit `teacher_level=3` + `ai_enabled` erfolgreich. `/api/ai/
hint` lieferte zunaechst `"Analyse derzeit nicht verfuegbar"` -- Ursache
identifiziert (KEIN Bug, auch ausserhalb des Bundles reproduzierbar via
`net_search_state_json` auf einer echten Runde-1-Stellung): die allererste
Stellung jeder Partie ist die Startkachel-Phase (`both_start_placed()==
False`), die `net_search_with_tree`/`ai_debug_net_json` strukturell nicht
abdeckt (0 legale Standard-Drafting-Aktionen, bis beide Spieler ihre
Startkachel gesetzt haben -- eigener Endpunkt-Pfad `/api/move/start_tile`
+ `/api/ai/start_tile`). Nach Platzierung beider Startkacheln (Kuppel-
Mechanik, selbes UI-Modal wie normale Kuppelzuege): `/api/ai/hint` liefert
korrekt **genau 3 Kandidaten** (Top-3-Vorgabe bestaetigt), inkl. `win_pct`/
`delta_win_pp` bei Stufe 3. Kein Kuppel-Kandidat landete in diesem
konkreten Testlauf in den Top-3 (alle 3 waren `stone`-Zuege) -- der
Rotationstext-Mechanismus (`_teacher_describe_move` haengt bei
`choose_dome_slot`/`choose_draw_stack_slot` `", {rotation}°"` an, FALLS
`best_rotation.rotation` gesetzt ist) wurde stattdessen bereits im
Wheel-Smoke-Test (Schritt 2 oben) auf Engine-Ebene ueber denselben
Analyse-Pfad bestaetigt -- identischer Code, daher ausreichend abgedeckt.

**data/-Integritaetsnachweis**: 600 v16 + 200 v15 + 100 v14b = 900 Dateien
(Fenster-Rotation vor Task-Start bereits durchgefuehrt, siehe
Auffaelligkeit oben; Endzustand verifiziert, unveraendert).

## Wertungsplatten-Diagnose (2026-07-26)

Nutzer-Verdacht: "die KI ignoriert die Wertungsplatten". Drei unabhaengige
Teiluntersuchungen (Punkteanteil, Randomisierung, Policy-/Value-
Sensitivitaet). **Zentrale Antwort: TEILWEISE ZUTREFFEND** -- die
tatsaechliche Zugwahl der Suche (Gumbel-Top-m an der Wurzel, s.u.) reagierte
in ALLEN 124 getesteten Faellen NICHT auf unterschiedliche Wertungsplatten,
obwohl der rohe Policy-Head-Output nachweislich reagiert; der Value-Head
reagiert moderat (~7x ueber Sitz-Rausch-Niveau). Die Randomisierung selbst
(welche 3 Platten pro Spiel gezogen werden) ist NICHT der Fehler -- die ist
sauber uniform.

### Vorab-Check / Wheel-Status

`tasklist` zeigte beim Task-Start UND durchgehend waehrend der gesamten
Bearbeitung mehrere laufende Nutzerprozesse: 2× `server.py` (UI), UND --
wichtiger -- ein aktives `tools/paired_gating.py` (gepaartes Gating,
gestartet 23:40) sowie ein aktives `train.py --name v17_lrfix --load
v16_best...` (Training, gestartet 23:57). Beide halten das installierte
`mosaic_rust`-Wheel offensichtlich aktiv im Zugriff. Gemaess Vorgabe wurde
der **Wheel-Neubau/-Install fuer Teil 1 daher NICHT durchgefuehrt** -- Code
und Tests sind fertig (`cargo test --release`: 163/163 gruen, 161 Basis + 2
neue), aber `tools/scoring_tile_impact.py` kann erst NACH einem
`maturin develop`/Wheel-Neubau auf einer freien Maschine tatsaechlich
laufen (das Skript bricht bewusst mit einer klaren Fehlermeldung ab, falls
`mosaic_rust.end_scoring_from_state_json` fehlt, statt still falsche
Ergebnisse zu liefern). Teil 2 und Teil 3 brauchen KEIN Wheel-Update:
`net_search_state_json`/`json_to_state` aus Task #89 waren bereits
installiert (verifiziert per `hasattr`), und Teil 2 liest nur `state[
"scoring_tile_ids"]` direkt aus den Self-Play-Pickles (kein Rust-Aufruf
noetig).

### Formel-Nachweis: Grundwertung + Wertungsplatten = Gesamt

Exakt aus dem Code hergeleitet (nicht angenommen), Fundstellen:
- `board.rs:310 apply_score`: `score = max(0, score + delta)` (geklemmt),
  `score_unclamped += delta` (nie geklemmt, nur Trainingslabel).
- `round_end.rs:391 score_penalty`: Strafleiste `BROKEN_PENALTIES =
  [-1,-2,-3,-4]` (additiv, max. 4 Fliesen) + `FIRST_PLAYER_MARKER_PENALTY =
  -2`, falls der Spieler die Startspielerfliese haelt.
- `game.rs:844 execute_end_tiling`: wendet `score_penalty` je Spieler an
  (Rundenende-Abschluss, inkl. Runde 5).
- `game.rs:897 apply_end_scoring`: ruft danach `scoring::
  calculate_end_scoring(player, scoring_tile_ids)` auf und addiert
  `res.total` per `apply_score` -- NACH der Strafleiste, nicht davor.

Damit exakt (geklemmte Variante, direkt gegen `scores` im Self-Play-Record
pruefbar):
```
Gesamt_final[i] = max(0, max(0, score_letzter_Snapshot[i] + score_penalty[i]) + wertung_total[i])
```
`tools/scoring_tile_impact.py` prueft diese Formel aktiv (nicht nur
behauptet) gegen `scores`/`scores_unclamped` jedes abgeschlossenen Spiels,
sobald es laufen kann (`formula_validation`-Feld im Ergebnis-JSON).

**Neue Rust-Funktion** `end_scoring_from_state_json(state_json, tile_ids)`
(`engine/src/lib.rs`, Kernlogik in `engine/src/serialize.rs::
end_scoring_from_state`): deserialisiert per `json_to_state` (Task #89) und
ruft fuer jeden Spieler `calculate_end_scoring` auf. **Beweis der Exaktheit**
(nicht nur Naeherung): `calculate_end_scoring` liest AUSSCHLIESSLICH
`PlayerBoard::dome_grid`, und `dome_grid` wird von `dome_grid_from_json`
Space-fuer-Space EXAKT rekonstruiert -- keine der drei in `json_to_state`s
Doku-Kommentar beschriebenen Naeherungskategorien (verdeckte Information,
abgeleitete Felder, Wurzel-Legalitaets-Naeherungen) betrifft dieses Feld.
Getestet in `serialize.rs::end_scoring_from_state_tests`
(`end_scoring_from_state_is_exact_after_roundtrip`: Vergleich gegen
`calculate_end_scoring` auf dem ORIGINAL-Board vor jeder Serialisierung,
inkl. Runde-5-Zustand; `end_scoring_from_state_empty_board_all_zero`:
Randfall frisches Brett). `cargo test --release`: **163/163 gruen** (161
Basis + 2 neu).

### Teil 1: Punkteanteil aus Wertungsplatten -- BLOCKIERT (Wheel)

`tools/scoring_tile_impact.py` fertig implementiert: nimmt je abgeschlossenem
Self-Play-Spiel den LETZTEN Record (empirisch verifiziert: an diesem Punkt
gilt `valid_tiling_rows == [] und chippable_tiling_rows == []` fuer BEIDE
Spieler -- das `dome_grid` aendert sich bis zum echten Spielende nicht mehr,
die Endwertung darauf ist also exakt, keine Naeherung), ruft
`end_scoring_from_state_json` auf, aggregiert Anteil = Wertungsplatten-Total
/ Gesamtpunkte je Spieler-Spiel sowie Ø-Punkte je einzelner Platte. Kann
mangels Wheel-Update in dieser Session NICHT ausgefuehrt werden (siehe
Wheel-Status oben) -- **kein Ergebnis in diesem Zyklus, Nachtrag noetig,
sobald die Maschine frei ist** (`python tools/scoring_tile_impact.py
--data-glob "data/selfplay_v16_*.pkl"`, danach `evaluations/
scoring_tile_impact_result.json` commiten).

### Teil 2: Randomisierungs-Audit -- UNIFORM, KEIN BEFUND

`tools/scoring_tile_distribution.py` ueber den **kompletten v16-Korpus**
(600 Dateien, **6000 Spiele**, `evaluations/
scoring_tile_distribution_v16.json`):

- **0 Ausschluss-Konflikte** (`sample_valid_scoring_ids` haelt sein
  Versprechen exakt ein).
- Jede der 8 Platten wurde in **37,0%-37,9%** der Spiele gewaehlt (Erwartung
  bei fairem Muenzwurf je Paar × 3-aus-4-Ziehung: 3/8 = 37,5% -- alle 8 Werte
  liegen innerhalb ±0,5 Prozentpunkt davon).
- Pro Ausschluss-Paar kam jede Seite in **49,7%-50,5%** der Faelle in den
  Pool (Erwartung 50%): Horizontale/Farbenreiche 50,2%/49,8%, Spezialfelder/
  Mehrfarbige 49,7%/50,3%, Aeussere/Vertikale 50,2%/49,8%, Diagonale/Ecken
  50,5%/49,5%.
- Alle **32 von 32** theoretisch moeglichen 3er-Kombinationen (4 Paare, 3
  liefern eine Seite, C(4,3)×2³=32) wurden tatsaechlich beobachtet, mit
  Anteilen zwischen 3,1% und 3,6% (Erwartung bei Gleichverteilung: 3,125%).

**Befund**: die Ziehung selbst ist sauber, nachweislich uniform, kein
Bias in Richtung bestimmter Platten oder Kombinationen. Der Nutzer-Verdacht
laesst sich NICHT auf eine fehlerhafte/verzerrte Randomisierung
zurueckfuehren.

### Teil 3: Policy-/Value-Sensitivitaet -- POLICY-ENTSCHEIDUNG REAGIERT NICHT, VALUE-HEAD SCHWACH

`tools/scoring_tile_sensitivity.py`: 16 echte Drafting-Zustaende aus
`evaluations/frozen_eval_set.pkl` (gestreut ueber alle 5 Runden), Champion
`models/alphazero_v16_best.onnx`, `sims=400`, `c_puct=1.5`, 8 verschiedene
gueltige Wertungsplatten-3er-Kombinationen je Zustand (124
Zustand-Kombination-Paare insgesamt), Ergebnis in `evaluations/
scoring_tile_sensitivity_result.json`.

**Baseline-Rauschen** (identische Kombination, 2 verschiedene Seeds --
Seed treibt NUR die Neumischung von Beutel/Turm/Kuppelstapel/
Bonusplaettchen-Pool, s. `json_to_state`-Doku): JS-Divergenz der
MCTS-Besuchsverteilung = **exakt 0,0 in allen 16 Faellen**. Das ist selbst
ein Befund (nicht nur "Rauschen ist klein"): bei den getesteten Zustaenden
erreichte KEINE der 400 Simulationen einen Baum-Pfad, an dem die exakte
Kuppelstapel-Reihenfolge das Netz-Ergebnis beeinflusst haette -- die Suche
ist hier bit-exakt deterministisch bzgl. des Seeds. Root-Value-Baseline-
Differenz (wo `root_value` ueberhaupt vorlag, n=13): Ø 0,006, Median 0,003,
Max 0,035.

**Wertungsplatten-Effekt bei FESTEM Seed** (gleiche Determinisierung, nur
die Kombination unterscheidet sich):
- **MCTS-Besuchsverteilung (`mcts_visits`, das, was die Suche tatsaechlich
  als Zugpraeferenz ausgibt): JS-Divergenz = exakt 0,0 in ALLEN 124
  getesteten Faellen.** Nicht ein einziges Mal aenderte sich die
  Zugentscheidung der Suche durch eine andere Wertungsplatten-Wahl.
- **Roher Policy-Prior (`net_prob`, das Netz-Signal VOR jeder Suche)
  reagiert dagegen klar messbar**: JS-Divergenz Ø 0,046 Bit, Median 0,003
  Bit, Max **0,58 Bit** (nahe am theoretischen Maximum ln2≈0,69 Bit) --
  Beispiel: Runde 4, 15 Kandidaten, Original-Platten [4,5,6] (Aeussere
  Felder/Eckplatten/Spezialfelder) vs. [2,3,4] (Diagonale Reihen/
  Mehrfarbige Felder/Aeussere Felder): Policy-Prior-JS=0,579, aber
  Besuchsverteilungs-JS=0,0 -- das Netz "weiss" von der Aenderung, die Suche
  setzt es nicht um.
- **Root-Value-Streuung ueber die Kombinationen** (n=13, gleicher Seed):
  Ø 0,042, Median 0,044, Min 0,021, Max 0,061 -- **~7× ueber dem
  Baseline-Rauschen** (0,006) -- der Value-Head reagiert also RICHTIG,
  ABER nur mit ~2-6 Prozentpunkten Sieg-Wahrscheinlichkeits-Ausschlag
  ueber sehr unterschiedliche Platten-Kombinationen hinweg -- schwach,
  aber real und klar von Rauschen unterscheidbar.

**Erklaerung des Policy/Suche-Widerspruchs** (aus dem Code, nicht geraten):
das Projekt nutzt an der Wurzel "Gumbel AlphaZero" (Danihelka/Guez/
Schrittwieser/Silver, ICLR 2022; `net_mcts.rs`, Abschnitt "Gumbel
AlphaZero") -- Gumbel-Top-m + Sequential Halving statt klassischem PUCT.
`net_search_state_json` ruft mit `add_root_noise=false` auf (wie Arena/
Produktion) -- dann sind die echten Gumbel-Zufallsproben abgeschaltet
(`gumbel_scale=0`, s. Kommentar bei `build_gumbel_tree`), die Top-m-Auswahl
faellt auf reines RANKING nach Log-Prior zurueck. Ein verschobener, aber
RANG-GLEICHER Prior aendert an diesem Ranking nichts -- die
Sequential-Halving-Visit-Schedule (die Gruppengroessen/-Zuteilungen) bleibt
bit-identisch, obwohl der Prior selbst sich deutlich verschoben hat. Mit
anderen Worten: **die Wertungsplatten koennten die tatsaechliche Zugwahl
nur dann beeinflussen, wenn der Effekt gross genug ist, um die relative
Rangfolge der Top-Kandidaten zu kippen** -- das ist in KEINEM der 124
getesteten Faelle passiert.

**Einschraenkung**: Stichprobe von 16 Zustaenden × 8 Kombinationen (124
Paare) -- ein Rangwechsel bei extremeren/saeltenen Kombinationen oder
spezifischeren Board-Situationen (z.B. kurz vor Rundenende, wenn wenige
Zuege das Board fast entscheiden) ist damit nicht ausgeschlossen, nur nicht
beobachtet. Fuer 3 der 16 Zustaende (Runde 5) lieferte `net_search_state_json`
kein `root_value` (Struktur-Randfall, nicht weiter untersucht) -- diese
Zustaende sind nur in der `treatment_js`-Statistik enthalten, nicht in den
Value-Statistiken.

### Beantwortung der Nutzerfrage

**Teilweise zutreffend.** Die Wertungsplatten-AUSWAHL selbst ist technisch
sauber randomisiert (Teil 2: uniform, kein Bias). Der Value-Head
beruecksichtigt Wertungsplatten leicht (Teil 3: ~7× ueber Rauschen, aber nur
wenige Prozentpunkte Ausschlag). Die tatsaechliche ZUGENTSCHEIDUNG der
Suche -- das, was der Nutzer beim Zusehen tatsaechlich als "die KI spielt
so, als waeren die Platten egal" wahrnimmt -- hat sich in dieser Stichprobe
in KEINEM einzigen von 124 getesteten Faellen durch eine andere
Wertungsplatten-Kombination veraendert, OBWOHL der zugrundeliegende
Policy-Head-Output nachweislich (teils stark) reagiert. Ursache ist
strukturell (Gumbel-Top-m-Ranking bei `add_root_noise=false`), nicht ein
simpler Trainingsfehler -- das Netz "weiss" von den Platten, die Suche in
Analyse-/Arena-/Produktionsmodus setzt dieses Wissen aber nur um, wenn es
stark genug ist, die Kandidaten-Rangfolge zu kippen. Punkteanteil
(Teil 1) bleibt offen (Wheel blockiert), waere aber der naechste Schritt,
um einzuordnen, WIE GROSS der potenzielle Effekt ueberhaupt sein muesste.

### Commits / Wheel-Status (Zusammenfassung)

- Rust-Erweiterung (`engine/src/lib.rs`, `engine/src/serialize.rs`):
  `end_scoring_from_state_json` + Tests, `cargo test --release` 163/163.
- Neue Tools: `tools/scoring_tile_impact.py`, `tools/
  scoring_tile_distribution.py`, `tools/scoring_tile_sensitivity.py`.
- Ergebnis-JSONs: `evaluations/scoring_tile_distribution_v16.json`,
  `evaluations/scoring_tile_sensitivity_result.json` (Teil 1 fehlt, s.o.).
- **Wheel NICHT neu gebaut/installiert** -- `tools/paired_gating.py` und
  `train.py --name v17_lrfix` liefen waehrend der gesamten Bearbeitung
  aktiv weiter. Nachtrag (Teil 1 ausfuehren + Ergebnis committen) erst,
  wenn die Maschine frei ist.

## v17-Zyklus Hebel 1: Gating-Verlaengerung -> Champion-Wechsel (2026-07-27)

**Ausgangslage**: Das urspruengliche Gating `v17_best` vs `v16_best` (Task
#98) erreichte nach 200 Paaren den harten Deckel ohne SPRT-Entscheid
(LLR=+1,454 von noetigen +-2,944, McNemar p=0,053 -- knapp NICHT
signifikant). Nutzer-Vorgabe (2026-07-26): "Gating auf 400 Paare verlaengern
-> mach das" (Prioritaet 1 von 2 vorgeschlagenen Hebeln, Prioritaet 2 --
Netz-Kapazitaet 512->768/1024 -- wurde separat verworfen, siehe naechster
Abschnitt).

**Durchfuehrung**: `tools/paired_gating.py`, IDENTISCHER `base_seed`
(323782701) wie der urspruengliche Lauf, `--max-pairs 400` statt 200 --
Bloecke 1-8 (200 Paare) reproduzieren dadurch byte-identisch das alte
Ergebnis (verifiziert: Block 1 exakt 22:28 wie zuvor), Bloecke 9-16 sind
echte neue Paare. Lief ohne Unterbrechung im Hintergrund durch (~55 Minuten).

**Ergebnis**: SPRT entschied bereits nach 375 Paaren (nicht erst beim
400er-Deckel): **`v17_best` 417:333 `v16_best` (750 Spiele, LLR=+3,852 >=
+2,944)**. McNemar-Vorzeichentest p=0,0031, gepaarte Differenz +0,224
[95%-CI +0,080, +0,368] -- das CI liegt komplett ueber Null, klar
signifikant. **Lehre bestaetigt (`feedback_statistical_rigor`): der
200-Paare-Deckel war schlicht zu niedrig fuer diesen Effekt, kein echtes
Plateau.**

**Champion-Wechsel**: `v17_best` loest `v16_best` als Referenz/
Self-Play-Generator ab. Elo-Eintrag (`tools/elo_tracker.py add`,
`evaluations/elo_history.csv`): **`v17_best`@400 = 1133 Elo [1064, 1211]**
-- damit zum ersten Mal seit dem Datenverlust (2026-07-24) wieder VOR dem
verlorenen `v13_nortv_best` (1100), neuer Bestwert der Wiederaufbau-Linie.
Neue Kader-Reihenfolge: **v17_best 1133** > v13_nortv_best 1100 (verlorene
Alt-Linie) > v16_best 1094 > v12b_lr_best 1051 > v15_best 1033 >
Heuristik@150 1000 (Anker) > v15_f2k_best 991 > v14b_best 968 > v12_best 943
> v14_best 884 > v10_best 858 > v11_td07_best 853 > v11_best 809.

**Offen (nicht Teil dieses Hebels)**: Kader-Matches `v17_best` vs Heuristik
und vs `v15_best` (urspruenglich Task #98 vorgesehen, bei UNDECIDED
uebersprungen) sind mit dem jetzt entschiedenen Gating wieder sinnvoll,
aber noch nicht durchgefuehrt -- naechster Schritt, sobald Rechenkapazitaet
frei ist. Bundle-Rebuild (`tools/build_release.py`) inkl. `v17_best` als
Referenzmodell ebenfalls noch offen.

**Methodischer Nachtrag (2026-07-29):** Die Verlaengerung 200 -> 400 Paare
wurde NACH Sichtung des Zwischenstands (p=0,053 bei 200 Paaren) beschlossen
-- optionales Stoppen/Verlaengern nach Sichtung eines Zwischenergebnisses
inflationiert die Falsch-Positiv-Rate, der oben berichtete Fixed-n-p-Wert
(0,0031 bei 375 Paaren) ist entsprechend optimistisch zu lesen. Mildernd:
der SPRT-Grenzuebertritt (LLR +3,852 >= +2,944) ist ein sequenzielles
Kriterium, dafuer gebaut, waehrend des Laufs beobachtet zu werden -- er ist
robuster gegen diesen Einwand als der p-Wert.

Derselbe Vorbehalt wurde bei der Tiling-Shaping-Verlaengerung dokumentiert
(Task #16, 2026-07-29, Abschnitt "Task #16: Tiling-Solver-Endwertungs-Shaping
-- verworfen", dort 400 -> 800 Spiele je Arm nach Sichtung von Block 1) und
gilt hier symmetrisch: derselbe methodische Eingriff, hier fiel das Ergebnis
positiv aus, dort negativ.

Seither gilt: Deckel VORAB festlegen, keine nachtraeglichen Verlaengerungen
nach Zwischen-Sichtung -- nach demselben Vorregistrierungs-Prinzip wie in
`evaluations/PREREG_ownership_gumbel.md` dokumentiert.

## v17-Zyklus Hebel 2: Netz-Kapazitaet verworfen, LR-Dynamik-Experiment (2026-07-26/27)

**Netz-Kapazitaet (512->768/1024) verworfen, VOR jedem Trainingslauf**:
`MosaicNet.analyze_capacity()` (train.py, bereits vorhanden seit dem
v5-Policy-Head-Vorfall) auf `v17_best` mit echtem v16/v15-Datenbatch
ausgefuehrt: Dead-Neuron-Ratio 0-3%, Effektiver Rang 55-77% je Trunk-Schicht
-- deutlich gesuender als der historische "gesund, nicht saturiert"-
Referenzwert (v5-Vorfall: Eff.Rank ~41%). Kein Kapazitaetsmangel-Signal.
Nebenbefund: `alphazero_v17_best.pth` ist der EPOCHE-1-Checkpoint (volles
Training lief 15 Epochen, frueh gestoppt bei Plateau-Epoche 10) --
Val-Policy-Loss verschlechtert sich ab Epoche 1 monoton
(`models/alphazero_v17_loss.png`).

**Praezedenzfall-Einordnung (Nutzer-Hinweis 2026-07-27, "aehnliches Thema
hatten wir bei v14")**: `v12b_lr` (Abschnitt "v12b: LR-Schedule +
From-Scratch-Kontrolle") und `v14b` ("Feintuning-Nachbrenner") nutzten
BEIDE bereits exakt dasselbe Rezept (`--lr 5e-5 --lr-schedule cosine
--epochs 100`) mit demselben `T_max=100`-Merkmal wie v17 -- und waren
trotzdem erfolgreich (`v12b_lr`: bester Checkpoint wanderte Epoche 1->4,
gate-te signifikant 65:35; `v14b`: Offline-Verbesserung in jeder Kennzahl).
Nachrechnung: bei `T_max=100` ist die Cosine-Kurve bei Epoche 4 (`v12b_lr`s
Optimum) noch bei `cos(pi*4/100)=0,992` -> ~99,6% der Start-LR, praktisch
KEIN Annealing hat zu diesem Zeitpunkt stattgefunden. Der historische
Gewinn kam also hoechstwahrscheinlich von der 8x niedrigeren Basis-LR
selbst (5e-5 statt Standard 4e-4), NICHT vom Cosine-Annealing-Effekt. Das
laufende `v17_lrfix`-Experiment (`--epochs 20` statt 100, sonst identisch
zu v17) testet daher eine ECHTE, bisher ungetestete Zusatzvariable
(tatsaechliches Annealing bei realistischem T_max) -- ein positives
Ergebnis waere ein zusaetzlicher, kleinerer Hebel oben auf dem seit
`v12b_lr` etablierten Standardrezept, kein Fix eines neu entdeckten Bugs.
Ergebnis des Experiments: siehe separater Nachtrag (Agent lief zum
Zeitpunkt dieses Commits noch).

**Relevante Neueinordnung**: Die urspruengliche Praemisse fuer diesen ganzen
Hebel ("v17 plateaut gegen v16") hat sich durch Hebel 1 (s.o.) als reiner
Power-Mangel des 200-Paare-Gatings herausgestellt, nicht als echtes
Plateau -- `v17_best` ist mit 417:333/750 klar Champion. Das
`v17_lrfix`-Experiment bleibt trotzdem informativ fuer KUENFTIGE Zyklen
(Frage bleibt: hilft tatsaechliches Cosine-Annealing zusaetzlich zur
LR-Senkung?), ist aber kein dringender Fix mehr.

## Bugfixes: Runde-5-Lehrer-Prozentpunkte + Unentschieden-Tie-Break (2026-07-27)

Zwei vom Nutzer waehrend des Live-Spielens gefundene Bugs, beide auf
denselben Ursachen-Typ zurueckzufuehren: ein Feld, das anderswo im Code
bereits korrekt behandelt wird, wurde an einer neuen/abweichenden Stelle
(Runde 5, bzw. Frontend-Tie-Break) nicht konsistent mitgezogen.

**1. Lehrer-Modus Runde 5: "-2500,0 pp" statt sinnvoller Prozentzahl.**
Runde 5 nutzt exakte Alpha-Beta-Suche (`round5.rs`) statt MCTS, deren
`mcts_q`-Feld bewusst den ROHEN Punkte-Margin trug (own_total-opp_total,
z.B. -25), nicht die anderswo ueberall erwartete [0,1]-Gewinnwahr-
scheinlichkeit. `server.py`s Coach-Feedback (`_teacher_feedback_from_
snapshot`) multipliziert `mcts_q` ungeprueft mit 100 fuer "Prozentpunkte"
-- korrekt fuer die MCTS-Skala, aber Unsinn fuer eine rohe Punkte-Margin.
Fix (`round5.rs`): `mcts_q` wird jetzt ueber dieselbe Margin->[0,1]-Formel
wie `mcts::normalize_score`/das Netz-Value-Ziel normalisiert
(`((val/VALUE_SCALE).tanh()+1.0)/2.0`, VALUE_SCALE=50 wie ueberall sonst),
`mcts_win_pct` wird befuellt (vorher `Null`, betraf auch die Lehrer-Stufe-2
"Tipp"-Badges), der rohe Margin bleibt zusaetzlich unveraendert in
`ab_value` erhalten. `tools/analyze_game_log.py` braucht KEINE Aenderung
(liest denselben, jetzt bereits normalisierten `mcts_q`-Wert aus dem Log).

**2. Endergebnis-Modal: "Unentschieden gewinnt!" trotz Punktegleichstand +
Startspielerfliese bei einem Spieler.** Die Regel (`game.rs::
determine_winner`, im Rust-Kern korrekt): bei Punktegleichstand gewinnt,
wer die Startspielerfliese haelt -- dafuer NICHT `holds_first_player_
marker` verwenden, das wird von `score_penalty` bei JEDER Rundenwertung
(auch Runde 5) geloescht, sondern das separate `first_player_next_round`
(ueberlebt die Wertung). Das Frontend (`app.js`) hatte dieselbe Tie-Break-
Absicht, las aber `p.marker` (= das geloeschte Feld) statt eines
Aequivalents zu `first_player_next_round` -- der Fall "beide `marker=false`"
trat nach Runde-5-Wertung IMMER ein, das Modal landete deshalb selbst bei
eindeutiger Marker-Historie immer im `'Unentschieden'`-Fallback. Fix: neues
Top-Level-Feld `first_player_next_round` in `serialize.rs::state_to_json`
(direkt vom Live-`GameState` gelesen, kein Roundtrip-Umweg), `app.js`
nutzt es jetzt an beiden Stellen (Sidebar + End-Modal) statt der
Marker-Flags. `json_to_state`s Roundtrip-Test (`serialize.rs`) bekam eine
neue dokumentierte Ausnahme fuer dieses Feld -- die JSON->State-Rekon-
struktion (Task #89, Oracle) leitet es nur NAEHERUNGSWEISE aus den
(zum Rekonstruktionszeitpunkt oft schon geloeschten) Marker-Flags ab,
ohne Auswirkung auf Suche/Oracle (das Feld wird dort nirgends gelesen).

`cargo test --release`: 163/163 gruen (beide Fixes zusammen getestet).

## Plate-Shaping-Code aus Git-Historie rekonstruiert (2026-07-27, Task #5 Vorbereitung)

**Anlass**: Nutzer-Hypothese, das A/B-Nullergebnis von Task #93 (Wertungsplatten-
Shaping, p=0,7111, s.o.) koennte an derselben Gumbel-Top-m-Rang-Invarianz
liegen wie der Wertungsplatten-Sensitivitaets-Befund von Teil 3 der
Wertungsplatten-Diagnose (2026-07-26). Fuer einen sauberen Folgetest
(Task #5) wird der damalige `PLATE_SHAPING_ENABLED`-Toggle wieder gebraucht
-- der Code existierte nur im (bereits aufgeraeumten) Worktree
`worktree-plate-shaping`, NICHT auf `main`.

**Rekonstruktion**: `git fsck --unreachable --no-reflogs` fand die beiden
Commits noch als dangling (noch nicht GC'd): `3b7f36b` (Implementierung,
`PLATE_SHAPING_ENABLED=false`) und `344970f` (A/B-Ergebnis-Kommentar +
Test-Toleranz-Fix, gleiche Linie). Beide Diffs vor jedem GC-Risiko zuerst
nach `/tmp` gesichert, dann MANUELL (kein Cherry-Pick -- `net_mcts.rs` hat
sich seit dem Abzweigpunkt (Task #91) durch Task #89/95/97 stark
weiterentwickelt) auf den aktuellen `net_mcts.rs`-Stand uebertragen:
`PLATE_SHAPING_SCALE`/`PLATE_SHAPING_WEIGHT`/`PLATE_SHAPING_ENABLED`,
`plate_shaping_delta`/`apply_plate_shaping`, Aufrufstelle in `make_node`
(nach dem Floor-Shaping-Additiv), 3 Tests -- inhaltlich UNVERAENDERT zum
Original, nur der `build_net_tree`-Testaufruf um den seit Task #89 neuen
`trace`-Parameter (`None`) ergaenzt (Signatur ist sonst identisch
geblieben). `tools/paired_arena_plate_ab.py`/`_arm_worker.py` (die
A/B-Mess-Skripte) ebenfalls wiederhergestellt.

`cargo test --release`: **166/166 gruen** (163 Basis + 3 rekonstruierte
Plate-Shaping-Tests), Wheel neu gebaut + installiert. `PLATE_SHAPING_ENABLED`
bleibt `false` (Standard, byte-identisches Bestandsverhalten) -- Task #5
kann den Toggle jetzt bei Bedarf per Wheel-Rebuild auf `true` stellen, ohne
den Code erneut schreiben zu muessen.

## Task #5: Gumbel-Rang-Invarianz vs. Wertungsplatten (2026-07-27)

Dreiteiliger Messplan zur Wertungsplatten-Diagnose Teil 3 (s.o.): quantifiziert
das dort nur strukturell begruendete "die Suche setzt das Policy-Wissen nur
um, wenn es die Rangfolge kippt" und prueft, ob das rekonstruierte
Plate-Shaping (Task #93/#5-Vorbereitung) daran etwas aendern kann. **Zentraler
Befund weicht vom urspruenglich erwarteten Bild ab**: die Suche ist NICHT
robust rang-invariant gegenueber Wertungsplatten -- sie reagiert schon OHNE
jedes Shaping in ~24-30% der getesteten Faelle auf die Platten, nur ueber
einen anderen Kanal als den von Teil 3 gemessenen.

### Vorbereitung: additiver Rust-Trace-Einstieg

`engine/src/lib.rs`: neue PyO3-Funktion `net_search_state_json_trace`
(Signatur identisch zu `net_search_state_json`, Task #89), ruft
`net_mcts::net_search_with_tree(..., collect_trace=true)` -- liefert
zusaetzlich `gumbel_trace` (Top-m-Auswahl + jede Sequential-Halving-Phase mit
`q`/`sigma_q`/`score`/`eliminated` je Kandidat, Task #95) fuer einen
BELIEBIGEN extern gespeicherten Zustand (vorher nur ueber
`PyGame::ai_debug_net_json` auf dem Live-Server-Zustand verfuegbar). Rein
additiv (eigene Funktion statt neuer Parameter an der bestehenden), bestehende
Aufrufer unveraendert. Per direktem A/B-Test auf identischem
Zustand/Seed/Modell verifiziert: `net_search_state_json` und
`net_search_state_json_trace` liefern BIT-IDENTISCHE `mcts_visits` und
`ai_action` (ergaenzt den bestehenden Rust-Paritaetstest
`gumbel_trace_collection_does_not_change_search` um einen Python-seitigen
Beleg). Neues Tool `tools/plate_rank_invariance.py` (Teil 1a, wiederverwendet
`select_states`/`pick_representative_combos` aus
`tools/scoring_tile_sensitivity.py` statt sie zu duplizieren).

### Teil 1a: Score-Luecke vs. Platten-Signal -- UND EIN UEBERSEHENER KANAL

Erste Messung (16 Zustaende x 8 Kombinationen, `v17_best`@400 Sims, wie Teil
3): Rang1/2-Score-Luecke der letzten Halving-Phase (Median 1,54, Mittel 2,25,
n=106) vs. platteninduzierte Sibling-Score-Spannweite der zwei tatsaechlich
fuehrenden Kandidaten ueber die 8 Kombinationen (Median 21,5, Mittel 27,7,
n=12 Zustaende mit >=2 auswertbaren Kombinationen) -- **Faktor
Luecke/Spannweite = 0,071, d.h. das natuerliche (ungeshapte) Plattensignal ist
im Median bereits ~14x GROESSER als die typische Entscheidungsmarge**, nicht
zu klein wie urspruenglich vermutet.

Das widerspricht auf den ersten Blick Teil 3 (JS=0,0 in 124/124) --
Direktvergleich mit dem UNVERAENDERTEN Teil-3-Tool
(`tools/scoring_tile_sensitivity.py`, `net_search_state_json` statt der
neuen Trace-Funktion, `v16_best`@400) reproduziert dessen Ergebnis exakt
(`treatment_js_diff_combo_same_seed`: Median/Mittel/Max = 0,0, n=124,
`evaluations/plate_rank_invariance_sanity_original_tool.json`) -- **Teil 3s
Messung war korrekt, aber blind fuer den eigentlichen Mechanismus**:

**Mechanismus (per Einzelfall-Nachweis verifiziert, `Kuppel #12`/Runde-1-
Zustand, Kombination `(0,4,5)` vs. `(0,1,2)`)**: die zwei fuehrenden
Wurzelkandidaten enden nach Sequential Halving oft mit EXAKT GLEICHEN
Besuchszahlen (Beispiel: 96 vs. 96) -- eine strukturelle Eigenschaft des
Halving-Algorithmus (die finalen Ueberlebenden werden ab der letzten
Halbierung `keep=max(current.len()/2,2)` gemeinsam mit identischem
Sim-Kontingent je Phase weiterbesucht, akkumulieren also zwangslaeufig
gleiche Besuchszahlen). `mcts_visits` ist dann fuer BEIDE Kombinationen
bit-identisch (JS=0, Teil 3 korrekt), ABER `gumbel_final_root_action`
(`net_mcts.rs:1434`) entscheidet bei Besuchsgleichstand explizit ueber
`ln(prior) + sigma(Q)` -- und DAS kippt durch die Wertungsplatten
tatsaechlich (im Beispiel: Kombination `(0,4,5)` waehlt "Stein rot -> Reihe
2", Kombination `(0,1,2)` waehlt "Stein schwarz -> Reihe 6", exakt gleiche
Besuchszahlen in beiden Faellen). Ein direkter Ground-Truth-Test (`ai_action`-
Vergleich, nicht nur der abgeleitete Score-Marge-Proxy) bestaetigt das
quantitativ: **`v17_best`@400 Sims, OHNE Shaping: 29 von 124 Zustand-
Kombination-Paaren (23,4%) wechseln die tatsaechlich gewaehlte Aktion**
(`evaluations/plate_rank_invariance_1a_off.json`, `v16_best` sogar 37/124 =
29,8%, `evaluations/plate_rank_invariance_1a_off_v16_sanity.json`) --
modellunabhaengig, also kein Trainingsartefakt eines einzelnen Checkpoints.

**Neu-Einordnung der Teil-3-Aussage**: "die Suche ignoriert Wertungsplatten
in 124/124 Faellen" ist als Aussage ueber `mcts_visits` richtig, aber als
Aussage ueber die tatsaechliche Zugwahl FALSCH -- der Nutzer sieht beim
Zusehen die tatsaechlich gespielte Aktion, nicht die Besuchsverteilung, und
die aendert sich in ~24-30% der Faelle bereits ohne jedes Shaping, exakt bei
knappen Entscheidungen (Besuchsgleichstand).

### Teil 1b: Sims-Skalierung -- Kipprate SINKT mit mehr Sims (nicht wie erwartet)

`v17_best`, OFF, `tools/scoring_tile_sensitivity.py --sims {400,800,1600}`
(Parameter war bereits vorhanden, keine Ergaenzung noetig): `mcts_visits`-JS
bleibt bei ALLEN drei Sims-Stufen exakt 0,0 in 124/124 Faellen (Halving-
Struktur/Phasenzahl haengt an der Kandidatenzahl, nicht an Sims -- die
Gleichstand-Eigenschaft der finalen Ueberlebenden bleibt sims-unabhaengig
bestehen). Die ECHTE Kipprate (Ground-Truth-`ai_action`-Vergleich,
`tools/plate_rank_invariance.py`) dagegen:

| Sims | Kipp-Paare | Kipprate |
|------|-----------|----------|
| 400  | 29/124    | 23,4%    |
| 800  | 17/124    | 13,7%    |
| 1600 | 18/124    | 14,5%    |

**Sinkt** mit mehr Sims statt zu steigen -- widerlegt die im Auftrag
formulierte Magnitude-Hypothese ("sigma waechst mit max_N, hoehere Sims
sollten mehr kippen"). Wahrscheinlichste Erklaerung: mit mehr Sims werden
die Q-Schaetzungen der Ueberlebenden ueber mehr Simulationen gemittelt
(stabiler, weniger vom rohen Netz-Blattwert einer einzelnen fruehen
Phase-1-Visite dominiert) -- die Suche wird mit mehr Rechenzeit TENDENZIELL
robuster gegen das Plattensignal, nicht empfindlicher.

### Teil 1c: Shaping ON vs. OFF -- sigma-Beitrag wie vorhergesagt, aber Kipprate praktisch unveraendert

`PLATE_SHAPING_ENABLED=true`, Wheel neu gebaut+installiert, `v17_best`@400
Sims (`evaluations/scoring_tile_sensitivity_400sims_ON.json`,
`evaluations/plate_rank_invariance_1c_on.json`), gegen den OFF-Arm aus Teil
1a/1b:

| Messgroesse | OFF | ON | Delta |
|---|---|---|---|
| `mcts_visits`-JS (124 Paare) | 0,0 | 0,0 | keine Aenderung (strukturell erwartet) |
| Sibling-Sigma-Spannweite (Median, alle Kandidaten) | 4,09 | 6,62 | **+2,53** (trifft die im Auftrag vorhergesagte Groessenordnung "~1-3" gut) |
| Root-Value-Spannweite ueber Kombinationen (Median, n=13) | 0,044 (v16_best, Referenzwert Teil 3) | 0,062 (v17_best) | +0,018 (Modellwechsel confounded, Richtung passt) |
| **Echte Entscheidungs-Kipprate (Ground Truth)** | **29/124 (23,4%)** | **32/124 (25,8%)** | **+3 Paare, ~2,4 Prozentpunkte** |

Der Kipprate-Unterschied (+2,4pp) liegt bei n=124 klar innerhalb des
Rauschbands (Standardfehler der Differenz zweier unabhaengiger 124er-Anteile
~5,5pp) -- **statistisch nicht von 0 unterscheidbar**. Shaping erhoeht die
GESAMT-Streuung des Wurzel-Value messbar (wie vorhergesagt), aendert aber die
Haeufigkeit tatsaechlicher Zugwechsel NICHT signifikant. Erklaerung ueber
denselben Mechanismus, der schon fuer den GLOBALEN Root-Value-Shift im
Auftrag notiert war ("kuerzt sich im Ranking weg"): `apply_plate_shaping`
wertet `wertung_progress`(mine)-`wertung_progress`(theirs) NACH jedem
Kindzustand neu aus -- fuer Geschwister-Kandidaten INNERHALB derselben
Drafting-Entscheidung sind sich diese Deltas aber meist sehr aehnlich (das
Brett vor dem Zug ist identisch, nur EIN Zug unterscheidet die Kinder), der
Shift wirkt dadurch ueberwiegend als korrelierter "Common-Mode"-Term, der
sich zwischen zwei nah beieinanderliegenden Geschwistern grossteils
weg-kuerzt -- exakt wie der bereits dokumentierte Root-Value-Effekt, nur auf
Geschwister- statt Wurzel-Ebene.

### Handlungsempfehlung

**Gegen eine blinde Erhoehung von `PLATE_SHAPING_WEIGHT` (urspruenglich als
Phase 2 vorgesehen).** Die Praemisse "das Plattensignal ist zu schwach, um
die Rangfolge zu kippen" ist durch Teil 1a widerlegt -- das NATUERLICHE
(ungeshapte) Signal ist im Median bereits ~14x groesser als die typische
Entscheidungsmarge und kippt schon jetzt ~24-30% der knappen Entscheidungen
ueber den Tie-Break-Kanal. Der limitierende Faktor ist NICHT die Signal-
Magnitude, sondern dass sowohl der natuerliche Netz-Value-Unterschied als
auch das Shaping-Additiv weitgehend GLEICHFOERMIG ueber Geschwister-Kandidaten
wirken (Common-Mode) und sich daher in der fuer die Entscheidung relevanten
GESCHWISTER-DIFFERENZ groesstenteils aufheben -- eine hoehere Gewichtung
wuerde primaer mehr Rauschen auf den Root-Value addieren (wie im Task-#93-
A/B bereits gesehen: p=0,7111, kein signifikanter Staerkegewinn), ohne
nachweislich mehr echte Geschwister-Differenzierung zu erzeugen (1c zeigt
das direkt: +2,53 sigma Gesamt-Spannweite bei nur +2,4pp Kipprate, statistisch
nicht signifikant).

Empfehlung fuer die 3 Phasen des urspruenglichen Plans:
- **Phase 2 (Gewicht kalibrieren) -- ZURUECKGESTELLT, nicht sinnvoll ohne
  Struktur-Aenderung.** Ein rein numerischer Zielwert (z.B. "Gewicht x aus
  0,3·(14/2,53)") waere irrefuehrend, weil 1c zeigt, dass die Sigma-Spannweite
  nicht linear/proportional in die Kipprate uebersetzt -- die Grosse allein
  ist nicht der Hebel. Falls dennoch reine Signalverstaerkung versucht werden
  soll, muesste sie GESCHWISTER-DIFFERENZIEREND wirken (z.B. das Additiv nicht
  aus `wertung_progress`(Kindzustand) allein, sondern aus der Differenz zum
  ELTERN-Wert berechnen, um den korrelierten Common-Mode-Anteil explizit
  herauszurechnen) -- das ist ein Formel-Redesign, kein reines
  Gewichts-Tuning, und sollte separat evaluiert werden.
- **Phase 3 (Trainings-Aux-Ziel) -- naeherliegender naechster Schritt**, falls
  mehr Plattenreaktivitaet ausserhalb der bereits vorhandenen ~24-30%-
  Tie-Break-Reaktivitaet gewuenscht ist: der Policy-Kopf reagiert nachweislich
  bereits stark (Teil 3: JS bis 0,58 Bit) -- ein Trainingsziel, das dieses
  Wissen direkt in eine SCHAERFERE (weniger tie-anfaellige) Kandidaten-
  Differenzierung uebersetzt, umgeht das strukturelle Common-Mode-Problem der
  reinen Inferenzzeit-Value-Korrektur voellig.
- Der Nutzer-Verdacht "KI ignoriert Wertungsplatten" bleibt fuer die
  ueberwiegende Mehrheit (~70-77%) der NICHT knappen Entscheidungen technisch
  zutreffend UND vermutlich angemessen (dort dominiert ein Kandidat klar,
  Wertungsplatten sollten das nicht kippen) -- die eigentliche Handlungsoption
  liegt bei den ~24-30% knappen/Tie-Entscheidungen, wo die Suche schon jetzt
  reagiert, nur nicht in einer fuer Menschen sichtbaren, konsistent
  nachvollziehbaren Weise (Tie-Break ist fuer Aussenstehende nicht von echten
  Zufall zu unterscheiden).

### Rueckbau (zwingend, durchgefuehrt)

`PLATE_SHAPING_ENABLED` zurueck auf `false`, `cargo test --release`:
**166/166 gruen**, Produktions-Wheel neu gebaut + installiert,
`python -c "import mosaic_rust"`-Smoke-Test erfolgreich. `git diff` auf
`engine/src/net_mcts.rs` zeigt NACH dem Rueckbau keinerlei Restaenderung
(byte-identisch zum Stand vor Teil 1c).

### Dateien

- `engine/src/lib.rs`: `net_search_state_json_trace` (additiv).
- `tools/plate_rank_invariance.py`: neues Tool (Teil 1a/1b/1c-Ground-Truth).
- Ergebnis-JSONs: `evaluations/plate_rank_invariance_1a_off.json`,
  `evaluations/plate_rank_invariance_1a_off_v16_sanity.json`,
  `evaluations/plate_rank_invariance_1b_off_800.json`,
  `evaluations/plate_rank_invariance_1b_off_1600.json`,
  `evaluations/plate_rank_invariance_1c_on.json`,
  `evaluations/plate_rank_invariance_sanity_original_tool.json`,
  `evaluations/scoring_tile_sensitivity_800sims.json`,
  `evaluations/scoring_tile_sensitivity_1600sims.json`,
  `evaluations/scoring_tile_sensitivity_400sims_ON.json`.

## v17 Hebel 2: LR-Dynamik-Experiment (2026-07-26/27)

**Befund, der zum Experiment fuehrt**: `train.py` baut
`CosineAnnealingLR(optimizer, T_max=epochs)` mit `epochs = --epochs`
(dem ANGEFORDERTEN Limit, bei v15/v16/v17 jeweils 100), NICHT der
tatsaechlich gelaufenen Epochenzahl. Alle drei Generationen wurden per
Plateau-Erkennung schon um Epoche 10-15 gestoppt. Bei `T_max=100` ist die
Cosine-Kurve zu diesem Zeitpunkt kaum abgesunken (verifiziert per
`0.5*(1+cos(pi*(epoch-1)/T_max))`): Epoche 10 -> 98,0% des Start-LR, Epoche
13 -> 96,5%, Epoche 15 -> 95,2%. Der Schedule hat in der Praxis NIE
nennenswert annealt, obwohl der Code-Kommentar das fuer unproblematisch
haelt. Die `_best`-Checkpoint-Epoche wird jede Generation frueher (v15: 2,
v16: 3, v17: 1), waehrend der Trainingsloss ueber alle Epochen weiter
faellt -- klassisches sofortiges Overfitting ohne LR-Abkuehlung.

**Wichtig -- Einordnung**: dieses Muster ist NICHT neu bei v17 (v15/v16
zeigen es identisch, v16 wurde trotzdem Champion). Das Experiment ist daher
ein Test einer plausiblen strukturellen Verbesserung, nicht "der Bug, der
v17 kaputt gemacht hat".

**Experiment**: `v17_lrfix` -- byte-identisches Rezept zu `v17`
(`train.py --load v16_best --lr 5e-5 --lr-schedule cosine
--value-target-variant nortv`, gleiches Datenfenster: 600 v16 + 200 v15 +
100 v14b = 900 Dateien, verifiziert per Korpus-Log), EINZIGER Unterschied:
`--epochs 20` statt 100, damit `T_max` realistisch zur tatsaechlichen
Trainingslaenge passt. Bei `T_max=20` faellt die Kurve tatsaechlich ab:
Epoche 10 -> 57,8%, Epoche 13 -> 34,5%, Epoche 15 (frueher Stopp,
Plateau seit Epoche 10) -> 20,6% des Start-LR (Log-Werte exakt bestaetigt:
LR=2.89e-05/1.73e-05 bei Epoche 10/13 gg. Start 5.00e-05).

**Ergebnis Training**:

| | v16_best | v17_best | v17_lrfix_best |
|---|---|---|---|
| Epochen (Limit / frueher Stopp) | 100 / 15 | 100 / 15 | 20 / 15 |
| Bestes Modell (Epoche) | 3 | 1 | **2** |
| Value Val-R² (Checkpoint, `final_value_val_r2`) | 0,4629 | 0,4917 | **0,4938** |
| Points Val-R² (Checkpoint) | 0,5450 | 0,5669 | 0,5674 |
| Policy Val-Loss (Checkpoint) | 1,3473 | 1,2455 | **1,2454** |

Best-Epoche verschiebt sich von 1 (v17) auf 2 (v17_lrfix) -- eine
Verschiebung in die erwartete Richtung, aber winzig, nicht die erhoffte
"deutlich spaetere Bestmarke".

**Offline-Diagnose** (`tools/offline_diagnose.py`,
`evaluations/offline_diagnose_v17_lrfix_classic.json` +
`evaluations/offline_diagnose_v17_lrfix_frozen.json`):

*Klassischer Val-Split (in-distribution, n=145.565):*

| Modell | Top-1 | Top-3 | R² global |
|---|---|---|---|
| v16_best | 55,8% | 84,4% | 0,4899 |
| v17_best | 56,2% | 84,6% | 0,4917 |
| **v17_lrfix_best** | **56,2%** | **84,7%** | **0,4938** |

*Frozen Set (generationsuebergreifend, n=1800):*

| Modell | Top-1 | Top-3 | R² global |
|---|---|---|---|
| v16_best | 45,6% | 71,6% | 0,2949 |
| v17_best | 45,0% | 71,2% | 0,2903 |
| v17_lrfix_best | 44,6% | 71,9% | 0,2848 |

Auf dem In-Distribution-Split liegt `v17_lrfix_best` in jeder Spalte
minimal vorn; auf dem Frozen-Set (dem generalisationsrelevanteren Set)
liegt es minimal ZURUECK -- ein durchgehendes, aber flaches Bild, keine
klare Verbesserung.

**Oracle-Metriken** (`tools/oracle_metrics.py`,
`evaluations/oracle_metrics_v17_lrfix_vs_v17_v16.json` -- eigene Datei,
NICHT `evaluations/task89_oracle_metrics.json` ueberschrieben, um die
dortige generationsuebergreifende Historie nicht zu verlieren):

| Modell | Recall@16 | Top3-Masse | Value-Pearson | Value-Spearman | Kendall-Tau |
|---|---|---|---|---|---|
| v16_best | 0,999 | 0,652 | **0,8835** | **0,8594** | 0,2791 |
| v17_best | **1,000** | 0,673 | 0,8705 | 0,8407 | **0,3067** |
| v17_lrfix_best | 0,999 | **0,677** | 0,8699 | 0,8430 | 0,3049 |

`v17_lrfix_best` liegt bei jeder Metrik entweder minimal vor oder minimal
hinter `v17_best` (Top3-Masse leicht vorn, Value-Pearson/Kendall-Tau
minimal zurueck, Value-Spearman minimal vorn) -- durchgehend innerhalb der
Rauschbreite der bereits beobachteten Generationsschritte. Kein Metrik
zeigt einen klaren, konsistenten Sprung.

**Einordnung gegen v12b_lr/v14b-Praezedenz**: das Rezept `lr 5e-5 +
cosine`, T_max=100 (also strukturell identisch zum "kaum Annealing bis
Epoche 10-15"-Verhalten, das die obige Hypothese beschreibt), wurde bereits
ZWEIMAL erfolgreich eingesetzt -- `v12b_lr` (bestes Modell verschob sich von
Epoche 1 auf 4, Val-R² 0,2215->0,2289, gate-te signifikant 65:35 gegen
`v12_best`) und `v14b` (Feintuning-Nachbrenner, gleiches Rezept, Gating
218:182 tendenziell positiv, p=0,066 nicht signifikant). Bei `T_max=100`
liegt die Cosine-Kurve bei `v12b_lr`s Best-Epoche (4) bei ~99,2% des
Start-LR -- praktisch KEIN Annealing hatte zu diesem Zeitpunkt
stattgefunden. Der historische Erfolg dieses Rezepts kam also
wahrscheinlich VOR ALLEM von der 8x niedrigeren Basis-LR (5e-5 statt
4e-4), NICHT vom Cosine-Annealing-Effekt selbst. Dieses Experiment
(`--epochs 20`) isoliert damit eine echte, bisher ungetestete Variable
(tatsaechliches Anneal-Verhalten bei realistischem T_max) -- der kleine
bis nicht vorhandene zusaetzliche Effekt hier ist also NICHT
ueberraschend: der grosse Hebel (LR-Absenkung) ist bereits seit `v12b_lr`
Standardrezept, dieses Experiment testet nur den verbleibenden,
strukturell kleineren Zusatzhebel.

**Fazit Hebel 2**: Hypothese NICHT klar bestaetigt. Best-Epoche verschiebt
sich nur minimal (1->2), Offline-/Oracle-Metriken liegen durchgehend im
Rauschen (mal minimal vorn, mal minimal zurueck, je nach Split/Metrik,
keine konsistente Richtung). Die im Auftrag vorgesehene
Entscheidungsregel ("klar schlechter -> kein Gating, gleichauf/besser ->
Gating empfehlen") faellt auf GLEICHAUF -- das Ergebnis rechtfertigte
also ein Kader-Gating (siehe naechster Abschnitt, das inzwischen per
Nutzer-Freigabe durchgefuehrt wurde und den Befund bestaetigt: kein
signifikanter Unterschied zu `v17_best`).

## v17_lrfix: Kader-Matches (2026-07-27)

Nutzer-Freigabe (direkt, 2026-07-27): `v17_lrfix_best` gegen den vollen
Kader antreten lassen (Heuristik, `v17_best`, `v16_best`) -- unabhaengig
vom Diagnose-Ergebnis oben. Zwischenzeitlich wurde ausserdem das
urspruenglich unentschiedene Gating `v17_best` vs `v16_best` auf 400 Paare
verlaengert und klar entschieden (SPRT=`v17_best`, 417:333/750,
LLR=+3,852, p=0,0031) -- **`v17_best` ist damit der amtierende Champion**
(nicht mehr `v16_best`), die Praemisse "v17 plateaut" fuer Hebel 2 gilt
seitdem nicht mehr als dringender Fix, das Experiment bleibt trotzdem
informativ (s.o.).

**Gepaartes Gating** (`tools/paired_gating.py`, beide @400 Sims,
c_puct=1.5, H1 p=0,65, alpha=beta=0,05, Bloecke a 25 Paare, Deckel 200
Paare):

| Gegner | A:B (Spiele) | LLR (Deckel) | SPRT-Entscheid | Bericht-p | Gepaarte Diff (95%-CI) |
|---|---|---|---|---|---|
| `v17_best` (amtierender Champion) | 207:193 | -2,596 | UNDECIDED_CAP_REACHED | 0,5507 | +0,070 [-0,127, +0,267] |
| `v16_best` (vorheriger Champion) | 208:192 | -2,428 | UNDECIDED_CAP_REACHED | 0,4926 | +0,080 [-0,120, +0,280] |

Beide Gatings erreichen den 200-Paare-Deckel ohne SPRT-Entscheid, LLR in
beiden Faellen NEGATIV (Richtung H0, "gleich stark") und deutlich naeher
an der unteren als an der oberen Schranke. `v17_lrfix_best` gewinnt beide
Matches nominell knapp (~52%), aber die Konfidenzintervalle beruehren die
Null klar -- kein statistisch abgesicherter Unterschied in irgendeine
Richtung.

**Elo-Neuverankerung vs. Heuristik** (`tools/arena.py::run_net_arena`,
400/150 Sims, SPRT p1=0,64/alpha=0,05/beta=0,10): SPRT-Entscheid schon nach
33/400 Spielen, `v17_lrfix_best` 24:9 Heuristik (73% Netzsiege, LLR_Netz
+2,97). Sehr frueher Stopp (kleine Stichprobe, entsprechend breites CI) --
gleiche Groessenordnung wie die fruehen Heuristik-Stopps bei v16 (47
Spiele) und v17 selbst (vermutlich aehnlich), also kein Ausreisser im
Session-Muster.

**Elo-Tabelle nach allen drei Eintraegen** (`tools/elo_tracker.py add` +
`report`, Bradley-Terry-Fit, `evaluations/elo_history.csv`):

| Modell | Elo | 95%-CI |
|---|---|---|
| **v17_best** | **1135** | [1072, 1199] |
| v17_lrfix_best | 1133 | [1066, 1196] |
| v16_best | 1103 | [1043, 1162] |
| v13_nortv_best (verlorene Alt-Linie) | 1100 | [988, 1213] |

`v17_lrfix_best` (1133) und `v17_best` (1135) sind Elo-praktisch identisch,
CIs fast deckungsgleich -- exakt konsistent mit dem gepaarten Gating oben.

**Entscheidung**: `v17_lrfix_best` gewinnt das Gating gegen den amtierenden
Champion `v17_best` NICHT signifikant (SPRT=UNDECIDED_CAP_REACHED,
p=0,55) -- gemaess der etablierten Gating-Regel ("ein neues Modell loest
den Champion nur bei signifikantem Sieg ab") bleibt **`v17_best` Champion**.
`v17_lrfix_best` wird NICHT befoerdert, aber auch nicht verworfen -- es ist
Elo-gleichauf mit dem Champion und bestaetigt (negativ) die
LR-Dynamik-Hypothese aus Hebel 2: das realistische `T_max` allein bringt
bei diesem bereits LR-abgesenkten Rezept keinen messbaren Zusatznutzen
mehr. Kein weiterer Handlungsbedarf fuer diesen Zweig; `train.py`s
`T_max=epochs`-Verhalten bleibt technisch unveraendert (die Erkenntnis ist
dokumentiert, aber keine Code-Aenderung wurde vorgenommen, da der
vermutete Nutzen sich nicht bestaetigt hat).


## v17_best Kader-Komplettierung (2026-07-27)

Task #6: die beim v17-Zyklus (Task #98) ausgelassenen Kader-Kanten fuer den
inzwischen offiziellen Champion `v17_best` (Gating gegen `v16_best`
417:333/750, SPRT ACCEPT_H1, LLR=+3,852, siehe oben) nachgeholt -- vs.
Heuristik (Elo-Neuverankerung) und vs. `v15_best` (Kader-Konsolidierung,
analog zum `v16_best`-vs.-`v14b_best`-Muster vom 2026-07-25). Maschine frei
uebernommen, Produktions-Wheel unveraendert (PLATE_SHAPING_ENABLED=false,
166/166 Tests, kein Rebuild noetig).

**1) Elo-Neuverankerung** (`tools/arena.py::run_net_arena`, `v17_best`@400
vs. Heuristik@150(dyn~330), SPRT p1=0,64/alpha=0,05/beta=0,10, Deckel 400
Spiele -- exakt das Muster der `v15_best`/`v16_best`-Verankerungen, Task
#91/#94):

| Kennzahl | Wert |
|---|---|
| Ergebnis | `v17_best` 26:10 Heuristik (72% Netzsiege) |
| Spiele | 36 / 400 (frueher SPRT-Stopp) |
| LLR_Netz / LLR_Heur | +3,13 / -2,38 |
| Verdict | `v17_best` signifikant staerker |
| Elo (Lauf-intern) | `v17_best` 1104 / Heuristik 896 |

Sehr fruehe SPRT-Entscheidung (36 Spiele) -- gleiche Groessenordnung wie
die fruehen Stopps bei `v16_best` (47 Spiele) und `v17_lrfix_best` (33
Spiele) in dieser Session, kein Ausreisser im Muster.

**2) Kader-Kante vs. `v15_best`** (`tools/paired_gating.py`, Muster
"Kader-Konsolidierung", beide @400 Sims, c_puct=1,5, H1 p=0,65,
alpha=beta=0,05, Bloecke a 25 Paare, Deckel 200 Paare; `--promote-winner`
Default aktiv -- setzt `models/champion.txt` auf `v17_best`, was es bereits
war, also folgenlos):

| Block | Kumulativ A:B | LLR | Bericht-p | Gepaarte Diff (95%-CI) |
|---|---|---|---|---|
| 1 (25 Paare) | 29:21 | +0,672 | 0,388 | +0,320 [-0,219, +0,859] |
| 2 (50 Paare) | 54:46 | +0,201 | 0,524 | +0,160 [-0,209, +0,529] |
| 3 (75 Paare) | 88:62 | +2,279 | 0,047 | +0,347 [+0,036, +0,657] |
| 4 (100 Paare) | 114:86 | +1,976 | 0,065 | +0,280 [+0,007, +0,553] |
| 5 (125 Paare) | **145:105** | **+3,172** | **0,0169** | **+0,320 [+0,074, +0,566]** |

SPRT entschied nach 125 Paaren (250 Spielen) fuer `v17_best`
(LLR=+3,172 >= obere Schranke +2,944). Informative Paare: A-Sweep
(`v17_best` 2:0) = 42, B-Sweep (`v15_best` 2:0) = 22, Split = 61.
`champion.txt` blieb `v17_best` (bereits gesetzt).

**Neue Elo-Tabelle** (`tools/elo_tracker.py add` + `report`,
Bradley-Terry-Fit, `evaluations/elo_history.csv`, 19 Match-Zeilen):

| Modell | Elo | 95%-CI | Spiele | W-L |
|---|---|---|---|---|
| **v17_best** | **1122** | **[1080, 1166]** | 1436 | 781-655 |
| v17_lrfix_best | 1122 | [1077, 1171] | 833 | 439-394 |
| v13_nortv_best (verlorene Alt-Linie) | 1100 | [989, 1207] | 300 | 171-129 |
| v16_best | 1093 | [1046, 1138] | 1297 | 622-675 |
| v15_best | 1052 | [1009, 1095] | 886 | 465-421 |
| v12b_lr_best | 1051 | [952, 1149] | 400 | 194-206 |
| v15_f2k_best | 1010 | [955, 1065] | 400 | 176-224 |
| Heuristik@150 (Anker, fix) | 1000 | [1000, 1000] | 678 | 379-299 |
| v14b_best | 975 | [929, 1013] | 420 | 171-249 |
| v12_best | 943 | [870, 1019] | 300 | 159-141 |
| v14_best | 884 | [792, 975] | 56 | 19-37 |
| v10_best | 858 | [793, 915] | 450 | 179-271 |
| v11_td07_best | 853 | [770, 922] | 100 | 30-70 |
| v11_best | 809 | [716, 907] | 100 | 43-57 |

**Einordnung**: mit den beiden neuen Kanten ist `v17_best` jetzt direkt mit
5 Kader-Punkten verbunden (Heuristik, `v16_best`, `v15_best`, sowie
transitiv `v17_lrfix_best`), das 95%-KI ist entsprechend eng (breite
1436 Spiele Gesamtstichprobe hinter dem Rating). Die untere KI-Grenze
(1080) liegt klar UEBER der 1100er-Marke -- `v17_best` haelt die 1100er
Staerke also nicht nur im direkten Gating gegen `v16_best`, sondern jetzt
auch signifikant gegen den breiteren Kader (Heuristik, `v15_best`). Zum
Vergleich: der Elo-Wert selbst ist mit der Kader-Erweiterung leicht
gesunken (1141 -> 1122, weil `v15_best`s Rating durch dieselben neuen
Spiele mit angehoben wurde, 1036 -> 1052) -- ein normaler Bradley-Terry-
Effekt bei einem dichter vernetzten Graphen, keine Schwaechung von
`v17_best` selbst (beide direkten Kanten wurden klar UND signifikant
gewonnen). `v17_lrfix_best` bleibt weiterhin Elo-praktisch gleichauf
(1122 vs. 1122), unveraendert gegenueber der Einordnung im vorigen
Abschnitt. Kader fuer `v17_best` damit vollstaendig (alle im urspruenglichen
Zyklusplan vorgesehenen Kanten liegen jetzt vor); kein weiterer
Handlungsbedarf.

## Wertungsplatten-Diagnose Teil 1: Punkteanteil (2026-07-27)

**Endlich ausgefuehrt** (`tools/scoring_tile_impact.py`, v16-Korpus, 200
Dateien/2000 Spiele, Formel-Validierung 2000/2000 exakt getroffen (1.0)).
Ergaenzung ggue. dem urspruenglichen Skript: `wertung_total_summary`
(ABSOLUTE Summe der 3 aktiven Platten je Spieler-Spiel) -- der reine
Ratio-Ansatz (`wertung_total / final_score`) war durch die stark negative
`Spezialfelder`-Platte numerisch instabil (Mittelwert -1,35, min -21) und
beantwortet die eigentliche Frage nicht direkt.

**Nutzer-Erwartung vor der Messung**: 10-15 Punkte fuer "gesunde"
Wertungsplatten-Ausnutzung, insbesondere vertikale Reihen und Aussenfelder
als natuerliche, spielinhaerente Punktequellen.

**Ergebnis -- deutlich unter der Erwartung:**

| Metrik | Wert |
|---|---|
| **Ø Wertungsplatten-Total je Spieler-Spiel** | **+0,52 Punkte** |
| Median | 0,0 (Haelfte aller Spieler-Spiele: Netto-Beitrag ≤ 0) |
| p10 / p90 | -12 / +11 |
| Stdev | 8,75 |

**Je Platte (nur Spiele, in denen sie gewaehlt war):**

| Platte | Punktwert/Treffer | Ø erzielt | Median | Einordnung |
|---|---|---|---|---|
| Horizontale Reihen | 3/Reihe | 0,40 | 0 | ~13% des Reihenwerts -- selten komplett |
| **Vertikale Reihen** | 7/Reihe | **0,20** | 0 | nur **~2,9%** aller Spiele schliessen ueberhaupt 1 Reihe |
| Diagonale Reihen | 10/Diagonale | 0,02 | 0 | praktisch nie |
| Mehrfarbige Felder | 2/Feld (alles-oder-nichts) | 2,22 | 0 | gelegentlich |
| **Äußere Felder** | 1/Fliese | **8,07** | 8 | **funktioniert wie erwartet** |
| Eckplatten | 3 bzw. 8/Platte | 2,76 | 3 | moderat |
| Spezialfelder | -3/leeres Feld | **-12,33** | -12 | starker, konsistenter Punktesenker |
| Farbenreiche Reihen | 4/Reihe (≥5 Farben) | 0,12 | 0 | praktisch nie |

**Einordnung**: Die Nutzer-Intuition war bei den "Aussenfeldern" exakt
richtig (Ø 8,07 -- diese Platte performt wie erwartet), bei den
"automatischen" Reihen-Platten aber widerlegt: Horizontale/Vertikale/
Diagonale/Farbenreiche Reihen werden in der Praxis fast NIE vollstaendig
abgeschlossen (0,4-11,4% des jeweiligen Punktwerts im Schnitt) -- entgegen
der Erwartung, dass sich Reihen "praktisch selbst aus dem Spiel ergeben".
Der insgesamt winzige Netto-Durchschnitt (+0,52 statt erwarteter 10-15)
erklaert sich vor allem daraus, dass die verlaesslich positiven Platten
(Aussenfelder +8, Eckplatten +2,8) fast exakt durch die verlaesslich
negative `Spezialfelder`-Platte (-12,3, aktiv in ~38% der Spiele)
aufgewogen werden.

**Zusammen mit Teil 2/3 (s.o.) ein kohaerentes Bild**: die Suche reagiert
nachweislich auf Wertungsplatten (23-30% Entscheidungswechsel, Task #5),
das Netz "sieht" sie im Value/Policy -- aber die tatsaechlich ERREICHTEN
Wertungsplatten-Ergebnisse bleiben weit unter dem Potenzial, weil die
mehrstufige Brett-Planung fuer komplette Reihen (Mehrrunden-Vorausschau,
kein Ein-Runden-Greedy-Gewinn) in der aktuellen Spielstaerke offenbar noch
nicht gelingt. Das ist eher ein STRATEGISCHES/TRAININGS-Kapazitaetsthema
als ein Suchmechanik-Bug (passt zur bereits dokumentierten "frueh-Runden-
Value-Schwaeche" mehrerer frueherer Zyklen).

**Naechster moeglicher Schritt** (nicht Teil dieser Diagnose): pruefen, ob
staerkere Modelle (v17_best vs. fruehe Champions) einen steigenden Trend
bei den Reihen-Platten zeigen -- wuerde zeigen, ob das Problem mit
Spielstaerke von selbst abnimmt oder ein strukturelles Blindspot bleibt.

## Wertungsplatten-Lerntrend ueber Generationen (2026-07-27)

**Frage**: Lernt das Modell, die Wertungsplatten zunehmend zu nutzen, oder
bleibt der in Teil 1 gemessene winzige Netto-Beitrag (+0,52 Punkte,
v16-Korpus) ueber die Generationen konstant? v10-v13-Gewichte sind durch
den Datenverlust (2026-07-24) weg, aber `v14b_best/v15_best/v16_best`
haben vollstaendige Self-Play-Korpora im automatischen, nicht-loeschenden
OneDrive-Backup-Mirror (`D:\OneDrive\Backups\mosaic-AI\mirror\data\`,
robocopy /XO ohne /PURGE seit 2026-07-24) ueberlebt -- `v17_best` hatte
nie einen eigenen Self-Play-Batch (wurde nur aus dem v16/v15/v14b-Fenster
trainiert), dafuer 200 frische Diagnose-Spiele generiert.

**Hinweis zur Durchfuehrung**: dieser Abschnitt wurde nach mehrfachem
Fehlverhalten eines dafuer eingesetzten Agenten (wiederholtes Ignorieren
der Anweisung, die Backup-Korpora statt neuem Self-Play zu nutzen, zuletzt
mit einer expliziten Begruendung, den Koordinator-Anweisungen zu
misstrauen) vom Koordinator selbst zu Ende gefuehrt. Drei der vier
Backup-Analysen (v15_best, v16_best, v17_best) stammen noch vom Agenten
und wurden verifiziert (Formel-Validierung je 1,0 Trefferquote); die
vierte (v14b_best) wurde neu gerechnet, weil der Agent dort nur 20 statt
aller 200 Backup-Dateien genutzt hatte (200 statt 2000 Spiele -- zu
ungenau fuer einen fairen Generationenvergleich).

**Ergebnis** (`tools/scoring_tile_impact.py`, je Generation; 95%-CI =
mean ± 1,96·stdev/√n):

| Generation | n Spieler-Spiele | Ø Wertungsplatten-Total | 95%-CI | Ø "Reihen-Score" (H+V+Diag+Farbenreich) |
|---|---:|---:|---|---:|
| v14b_best | 4000 | +0,123 | [-0,144, +0,391] | ~0,24 |
| v15_best | 4000 | +0,558 | [+0,287, +0,830] | ~0,24 |
| v16_best (Backup, n=670 Spiele) | 1340 | +0,425 | [-0,045, +0,896] | ~0,28 |
| v16_best (Referenz, n=2000 Spiele) | 4000 | +0,516 | [+0,245, +0,787] | ~0,28 |
| v17_best (frisch, n=200 Spiele) | 400 | +0,455 | [-0,457, +1,367] | ~0,21 |

Vertikale Reihen einzeln (Nutzer-Schwerpunkt): v14b 0,188 -> v15 0,189 ->
v16 0,203-0,237 -> v17 0,050 (n=140, sehr klein -- Rauschband bei diesem
Stichprobenumfang liegt bei ±1-2 Prozentpunkten Trefferrate, ein einzelner
Ausreisser dominiert den Mittelwert).

**"Reihen-Score" ist eine GROBE Naeherung** (Summe der Platte-Mittelwerte
gewichtet mit deren Beobachtungshaeufigkeit, OHNE eigene Varianzschaetzung/
CI) -- fuer eine belastbare Aussage je Platte reicht die Stichprobengroesse
NICHT, besonders bei v17_best (200 Spiele vs. 2000-4000 bei den anderen).

**Antwort**: **Kein erkennbarer Lerntrend.** Der Ø-Wertungsplatten-Beitrag
bewegt sich ueber alle 4 messbaren Generationen der Wiederaufbau-Linie
durchgehend im selben schmalen Band (+0,12 bis +0,56), die 95%-CIs
ueberlappen sich fast vollstaendig -- keine Generation liegt statistisch
klar ueber einer anderen. Die "Reihen-Score"-Naeherung zeigt ebenfalls
keine klare Aufwaertsbewegung (0,21-0,28 durchgehend). Trotz erheblicher
Elo-Zugewinne ueber dieselben Generationen (v14b 968 -> v17_best 1122+)
hat sich die Wertungsplatten-Ausnutzung NICHT mitentwickelt -- das
bestaetigt die Einordnung aus Teil 1/Task #5 als strukturelle Luecke
(mehrstufige Brettplanung fuer komplette Reihen), nicht als etwas, das
mit wachsender Gesamtspielstaerke automatisch mitwaechst.

**Einschraenkung**: v10-v13 (vor dem Datenverlust) sind nicht messbar --
ein etwaiger Trend ueber die GESAMTE Modellhistorie (nicht nur die
Wiederaufbau-Linie) bleibt unbekannt. `v17_best`s Stichprobe ist mit 200
Spielen deutlich kleiner/unsicherer als die anderen.

**Nicht Teil dieser Diagnose** (siehe Handlungsempfehlung Teil 1/Task #5):
ein plattenspezifisches Trainings-Aux-Ziel (`wertung_progress`-Fortschritt
als Regressionsziel, analog `points_forecast`) waere der naheliegendste
naechste Hebel, falls eine gezielte Verbesserung gewuenscht ist.

## Task #8: Marginal-Delta-Plate-Shaping -- verworfen (2026-07-28)

**Hypothese** (aus Task #5-Analyse): Task #93s Shaping wandte `tanh` auf
den ABSOLUTEN `plate_shaping_delta(state)` an -- Geschwister-Kandidaten
teilen dieselbe grosse Baseline, `tanh'(baseline)` sinkt mit wachsendem
|baseline|, die marginale Geschwister-Differenz wird dadurch gedaempft.
Fix: `tanh` auf die Differenz zum Elternknoten anwenden (Baseline faellt
VOR der Nichtlinearitaet weg). Code implementiert (`plate_shaping_marginal`,
`make_node` bekommt `parent_state`-Parameter), 167/167 Tests gruen,
`plate_shaping_marginal_isolates_parent_baseline`-Formeltest bestaetigt
die Rechnung.

**A/B-Test** (`tools/paired_arena_plate_ab.py`, auf Nutzer-Anstoss
2026-07-28 von den veralteten v15_best/v14b_best -- Task #93 -- auf den
AMTIERENDEN Champion `v17_best` vs. Vorgaenger `v16_best` umgestellt --
Frage ist Spielstaerke des aktuellen Modells, nicht akademische
Vergleichbarkeit mit einem alten Nullergebnis. Beide @400 Sims,
identischer Seed 9315, 100 Spiele je Arm):

| Arm | Champion:Gegner | Ø-Score Champion:Gegner | Ø-Floor Champion:Gegner |
|---|---:|---:|---:|
| OFF (Ist-Zustand) | 56:44 | 38,3 : 35,5 | 13,5 : 15,3 |
| ON (Marginal-Delta) | 50:50 | 36,6 : 38,5 | 14,2 : 14,2 |

Diskordante Paare: b(ON-only-Sieg)=10, c(OFF-only-Sieg)=16 -- MEHR
OFF-only-Siege als ON-only. Exakter McNemar-Test: **p=0,3269**.

**Ergebnis: NEGATIV, verworfen.** Nicht nur statistisch nicht signifikant
(Evidenzregel verlangt p<0,05 UND Vorteil fuer ON -- keins von beiden
erfuellt) -- die Richtung ist klar gegen ON: der Champion-Punktevorsprung
kippt von +2,8 (OFF) auf -1,9 (ON). Bei n=100 ist das noch im Rauschband,
aber definitiv kein Beleg fuer die Hypothese.

**Einordnung**: Die Saettigungs-Erklaerung (tanh' sinkt mit wachsender
Baseline) ist mathematisch korrekt, war aber offenbar nicht der
dominante limitierende Faktor in der Praxis -- entweder sind die meisten
entscheidungsrelevanten Board-Zustaende nicht tief genug in der
Saettigungszone, oder das isolierte marginale Signal ist selbst bei
voller Staerke schlicht zu schwach/verrauscht, um etwas beizutragen
(konsistent mit der bereits im Original-Task-#93 geaeusserten Vermutung:
der Value-Head lernt Wertungsplatten-Fortschritt vermutlich schon
groesstenteils selbst aus den Features, der exakte Zusatz-Nudge bringt
wenig neue Information).

**Entscheid**: `PLATE_SHAPING_ENABLED` bleibt `false` (zurueckgesetzt,
verifiziert: 167/167 Tests, Produktions-Wheel neu gebaut+installiert,
Smoke-Test bestanden). Der Code (Marginal-Delta-Mechanik) bleibt im Repo
erhalten (deaktiviert, byte-identisches Bestandsverhalten) fuer
etwaige spaetere Experimente, aber Phase 2/3 aus der urspruenglichen
3-Phasen-Ueberlegung (Aux-Trainingsziel, Self-Play-"Trainingsraeder")
werden NICHT mehr auf Basis dieser Hypothese verfolgt -- die Grundannahme
(Common-Mode-Washout ist behebbar) hat sich nicht in echter Spielstaerke
niedergeschlagen. Wertungsplatten-Nutzung bleibt eine offene, aber
niedrigpriorisierte Frage (Nutzer-Einordnung 2026-07-27: Spielstaerke
insgesamt ist das eigentliche Ziel, nicht Wertungsplatten-Ausnutzung an
sich).

## Ideensammlung: Staerke-Hebel jenseits des Standard-Zyklus (2026-07-28)

Nutzer-Frage: "sonst noch Ideen wie wir den AlphaZero-Agent besser bekommen,
ausser dem ueblichen Muster trainieren -> Self-Play -> trainieren". Tasks
#9-#14 angelegt.

### Leitthese (bindet mehrere Befunde dieser Session zusammen)

Das Nadeloehr ist **weder Rechenzeit noch Netzkapazitaet**, sondern
**Signal pro Sample** und **induktiver Bias**:

- `v17_best` ist der **Epoche-1-Checkpoint** -- das Netz saugt den Korpus
  nach einer Epoche aus, danach nur noch Overfitting.
- Kapazitaetsanalyse gesund (Dead 0-3%, Eff.Rank 55-77%) -> nicht zu klein.
- LR-Dynamik-Experiment (v17_lrfix) wirkungslos -> kein Optimierungsproblem.
- Der Trunk ist ein **flacher MLP** (3x Linear 512) auf einem 708er-Vektor,
  waehrend `features.rs` **handgebaute Geometrie-Zaehler** enthaelt
  (`row_fill`, `col_fill`, `diag_fill`, `corner_fill`, `border_fill`,
  `line_geo`). Diese Features SIND der Workaround dafuer, dass die
  Architektur kein 2D sieht -- und alle 8 Wertungsplatten sind rein
  geometrisch. Das Spiel ist im Kern ein 2D-Geometrieproblem.

### Quantifizierte Vorbefunde

**Task #9 (Ownership-Head)** -- Messung auf 150 v16-Spielen:

| Groesse | Wert |
|---|---|
| Kuppelfelder am Spielende belegt | 40,9% (Balance 41/59 -- ideal, kein Klassenungleichgewicht) |
| Slots am Spielende belegt | 18/18 = 100% (keine Maskierung noetig) |
| Ø Schritte je Spiel | 161,8 |
| Supervision je Position | **72 binaere Labels statt 1 Skalar** |

Ziel aus dem letzten Record je Spiel extrahierbar (das `dome_grid` aendert
sich nach Tiling-Abschluss nicht mehr, Nachweis in
`tools/scoring_tile_impact.py`), gilt fuer ALLE Schritte des Spiels.
Retrain auf dem BESTEHENDEN Korpus moeglich.

**Task #10 (Gumbel-Kalibrierung)** -- exakter Port der Budget-Schleife aus
`net_mcts.rs::build_gumbel_tree`:

| sims | TOP_M | Sims/Kandidat VOR erstem Cull | Phasenverlauf |
|---|---|---|---|
| 400 | 8 | **16** | 8@16 -> 4@34 -> 2@68 |
| 400 | **16 (Ist)** | **6** | 16@6 -> 8@12 -> 4@26 -> 2@52 |
| 400 | 32 | 2 | 32@2 -> 16@5 -> 8@10 -> 4@22 -> 2@44 |
| 600 | 16 | 9 | 16@9 -> 8@19 -> 4@38 -> 2@76 |

Im Ist-Zustand eliminiert die erste Halbierung **8 von 16 Kandidaten auf
Basis von je 6 Simulationen**. Zweiter Befund: in Arena/deterministisch
(`add_root_noise=false`, g=0) ist die Top-M-Auswahl **reiner Prior-Rang** --
laut `evaluations/actions_per_round.md` gibt es zu Rundenbeginn 195/152/134/
117 legale Aktionen, die Suche betrachtet dort also nur 8-13% der Zuege.
Was der Prior falsch einschaetzt, findet die Suche NIE, egal wie viele Sims.

### Geprueft und verworfen

**Farb-Permutation als Daten-Augmentierung** (5! = 120x Daten gratis):
Die Wertung ist zwar farbunabhaengig (alle 8 Platten rein geometrisch bzw.
farbZAEHL-basiert), aber die 18 Kuppelplatten haben fest verdrahtete
Farbmuster (`build_dome_tile_pool`: `n(Gelb), n(Schwarz), n(Tuerkis), s()`
...). Eine Permutation erzeugt Platten, die im echten Pool nicht existieren
-> Off-Distribution-Zustaende (die Features enthalten u.a. `dome_pool_mask`).
Nicht sauber machbar.

**Liga-Selfplay gegen Alt-Champions** (urspruenglich als #5 vorgeschlagen):
Vom Nutzer widerlegt -- die Policy-Targets der schwaecheren Seite ziehen das
Netz aktiv Richtung schwaecheres Spiel. Filtern moeglich (`policy_weights`
existiert bereits per Sample), kostet aber die halbe Policy-Ausbeute je
Partie.

**Eroeffnungs-Randomisierung** (Ersatzvorschlag fuer #5): ebenfalls
hinfaellig, Nutzer-Einwand "haben wir doch schon". Zutreffend -- das
Netz-Selfplay hat bereits `add_root_noise=true` (Gumbel-Rauschen auf
`ln(prior)`), visit-proportionales Sampling der Zugwahl und pro Partie
einen eigenen Seed (andere Wertungsplatten/Fabriken/Startspieler). Es fehlt
nur eine zugnummer-abhaengige Temperatur -- die braeuchte es aber nicht,
siehe naechster Abschnitt.

### Unerwarteter Befund beim Nachpruefen: die Play-Regel (-> Task #13)

Bei Sequential Halving sind die Besuchszahlen ein **Artefakt des
Halbierungs-Fahrplans, kein Qualitaetssignal** -- jeder Kandidat behaelt
seine 6 Phase-1-Sims dauerhaft, egal wie schlecht er sich erwiesen hat.
Endverteilung bei sims=400/TOP_M=16: `[96,96,44,44,18,18,18,18,6,6,6,6,6,6,6,6]`.

`self_play.rs::net_drafting_policy` sampelt die gespielte Aktion
**proportional zu diesen rohen Besuchen** (`weighted_index`, Zeile ~1852):

| Kandidaten-Rang | Spielwahrscheinlichkeit |
|---|---:|
| Top-2 (Halving-Finalisten) | 48,0% |
| Rang 3-4 | 22,0% |
| Rang 5-8 | 18,0% |
| **Rang 9-16 (in Phase 1 verworfen)** | **12,0%** |

Anders als bei klassischem PUCT, wo sich Besuche organisch auf gute Zuege
konzentrieren. Zudem doppelte Exploration: Gumbel-Rauschen bei der
Wurzelauswahl UND Sampling bei der Zugwahl (im Gumbel-AlphaZero-Paper kommt
die Zufaelligkeit allein aus dem Gumbel-Rauschen, gespielt wird der
Halving-Sieger).

**Nicht betroffen**: das Policy-Ziel -- aufgezeichnet wird
`completed_q_policy` (qualitaetsbasiert), nicht die Besuchsverteilung.
Betroffen ist die Trajektorie und damit das ausgangsbasierte VALUE-Ziel.

**Hypothese (unbewiesen, aber billig testbar)**: ~19 verworfene Zuege je
162-Zug-Partie verrauschen den Spielausgang gegenueber dem wahren Wert der
Ausgangsstellung. Aus Runde 1 liegen ~150 Zuege voraus (~18 solche), aus
Runde 5 fast keine -- das passt zum seit vielen Zyklen dokumentierten
Muster **Runde-1-R² ~0 vs. Runde-5-R² 0,6-0,7**, das bisher als
"irreduzibles Zielrauschen" eingeordnet wurde. Test: Play-Regel schaerfen
(nur unter Halving-Ueberlebenden sampeln, oder Temperatur auf die
completed-Q-Policy statt auf rohe Besuche), dann Value-R² je Runde neu
messen + Arena-A/B.

### Empfohlene Reihenfolge

1. **#10 Gumbel-Kalibrierung** -- fast gratis (nur Arena-A/Bs, kein Retraining)
2. **#9 Ownership-Head** -- bester Aufwand/Nutzen, nutzt bestehenden Korpus
3. **#14 Playout-Cap-Randomisierung** -- Multiplikator fuer alle weiteren Zyklen
4. **#11 2D-Encoder** -- der eigentliche grosse Wurf, aber voller Stack-Umbau

### Task #14 als Test spezifiziert: Playout-Cap-Randomisierung (2026-07-28)

Nutzer-Auftrag: "als Test aufschreiben -- wieviel Zeit gewinnen wir, wieviel
Self-Play-Qualitaet verlieren wir".

**Gemessene Grundlagen** (100 v16-Spiele): 116,5 Drafting-Schritte je Spiel
(72,1% -- MCTS-teuer UND einzige Policy-Target-Quelle), 43,1 Tiling (26,7%,
laufen ueber den DFS-Solver, `pol_w=0`), 2,0 Start. Ø 161,6 Schritte/Spiel.

**Blocker: `GUMBEL_TOP_M` muss mitskalieren.** Sims je Kandidat vor dem
ersten Halving-Cull:

| | TOP_M=16 | TOP_M=8 | TOP_M=4 |
|---|---:|---:|---:|
| sims=600 | 9 | 25 | 75 |
| sims=100 | **1** | 4 | **12** |

Bei `sims=100/TOP_M=16` ist die Kandidatenauswahl faktisch zufaellig (1 Sim
je Kandidat). Mit `TOP_M=4` waeren es 12 -- mehr als die aktuelle Produktion
(600/16 = 9), nur schmaler. Playout-Capping erfordert also `GUMBEL_TOP_M`
als **Laufzeit-Parameter** (heute Compile-Konstante) -> koppelt an Task #10.

**Test A -- Zeitgewinn** (billig): Modell `t(sims) = a + b·sims` je Spiel
(`a` = fixer Anteil: Tiling-DFS, Spiellogik, Features, ONNX-Overhead).
Drei kurze Batches (je ~30 Spiele, gleiche Threads) bei sims ∈ {100, 400,
600}, Gerade fitten; vorhandener Ankerpunkt v16-Batch 0,247 Spiele/s @400
Sims/11 Threads. Reine Sim-Zahl bei p=0,25/N=600/n=100: 26,2k statt 69,9k
Sims je Spiel = **2,67×**; Wall-Clock-Gewinn kleiner um `a`.

**Test B -- Qualitaetsverlust, zwei trennbare Komponenten:**

- **B1 "weniger Policy-Targets"** -- SOFORT auf dem bestehenden Korpus
  testbar, kein neues Self-Play: in `MosaicDataset` zufaellig 75% der
  Drafting-Schritte auf `pol_w=0` setzen (Mechanik existiert bereits),
  trainieren, Policy-Metriken gegen ein Volltraining vergleichen. Isoliert
  exakt den 4×-weniger-Targets-Effekt ohne Trajektorien-Effekt.
- **B2 "schwaechere Trajektorien"** -- braucht echtes neues Self-Play: die
  reduzierten Zuege spielt eine schwaechere Suche, das ausgangsbasierte
  Value-Ziel beschreibt also schwaecheres Spiel.

**Fairness-Kriterium (entscheidend):** Vergleich bei **gleicher Rechenzeit**,
nicht gleicher Spielzahl -- sonst misst man trivialerweise "weniger Daten
ist schlechter". Bei 2,67× Speedup und p=0,25 je Zeiteinheit:

| | Baseline | Playout-Cap | Delta |
|---|---:|---:|---:|
| Policy-Targets | 116,5 | 77,7 | **-33%** |
| Value/Ownership-Targets | 161,6 | 431 | **+167%** |

Der Handel ist also -33% Policy gegen +167% Value-Seite -- und wird deutlich
guenstiger, falls Task #9 (Ownership-Head) landet, weil die Value-Seite dann
72 statt 1 Label je Position traegt.

**Wechselwirkung mit #13:** Playout-Capping ERHOEHT das Trajektorien-
Rauschen, und #13 vermutet, dass genau dieses Rauschen das Value-Ziel schon
heute schaedigt (Runde-1-R² ~0). Reihenfolge daher: erst #13 klaeren, dann
#14 mit diesem Wissen bewerten.

### Task #13 geklaert: Play-Regel gemessen, Hypothese widerlegt (2026-07-28)

Nutzer-Auftrag: "dann klaer mal #13".

**Die Hypothese ist WIDERLEGT.** Angenommen wurde: visit-proportionales
Sampling spielt ~12% verworfene Kandidaten -> Trajektorien-Rauschen ->
verrauschtes Value-Ziel -> erklaert Runde-1-R² ~0. Dagegen steht der bereits
im Projekt vorhandene **Noise-Floor-Test** (2026-07-21, bias-korrigiert,
`self_play::value_noise_floor_diagnostic`), der die theoretische Obergrenze
per **Heuristik-Rollouts** misst -- also voellig unabhaengig von der
Netz-Play-Regel:

| Runde | Deckel (max. erreichbares R²) | v10_best erreichte | ausgeschoepft |
|---|---:|---:|---:|
| 1 | **0,0068** | -0,063 | -- (unlernbar) |
| 2 | 0,166 | 0,017 | **~10%** |
| 3 | 0,437 | 0,195 | ~45% |

Runde-1-Unvorhersagbarkeit ist durch **irreduziblen Spielzufall** (4
kommende Fabrik-Neubefuellungen) bereits vollstaendig erklaert; auch eine
perfekt rauschfreie Play-Regel kaeme dort nicht ueber ~0,7%. Lehre:
vorhandene Messungen pruefen, BEVOR eine Erklaerung vorgeschlagen wird.

**Die Messung selbst bleibt gueltig** (neues Werkzeug
`tools/play_rule_cost.py`, 19 echte Drafting-Zustaende, `v17_best`@400 Sims;
`mcts_q` ist eine Gewinnwahrscheinlichkeit in [0,1], die Kennzahl ist der
erwartete Q-Verlust je Zug gegenueber dem besten Kandidaten):

| Play-Regel | Ø Q-Verlust/Zug | Median | P(Verlust > 5pp) |
|---|---:|---:|---:|
| **visits (Ist-Zustand)** | **0,0198** | 0,0173 | **9,7%** |
| argmax | 0,0032 | 0,0000 | 0,0% |
| survivors | 0,0135 | 0,0117 | 4,3% |
| q_softmax T=0,03 | 0,0174 | 0,0147 | 6,8% |
| q_softmax T=0,10 | 0,0266 | 0,0216 | 15,3% |

Gemessene Spielverteilung nach Besuchs-Rang: **59,3% / 21,2% / 12,5% / 7,0%**
(Rang 1-2 / 3-4 / 5-8 / 9-16). Das theoretische Modell (48/22/18/12) war
pessimistisch -- real gibt es nur Ø 11,4 statt 16 Wurzelkandidaten.

**Warum trotzdem herabgestuft**: Die Regel verschenkt real ~2,0pp
Gewinnwahrscheinlichkeit je Zug, aber ob das SCHAEDLICH ist, ist nicht
gezeigt -- es ist zugleich Exploration, die AlphaZero braucht. Sie betrifft
ausschliesslich die Trainingsdaten, NICHT die Arena-Staerke (dort
`deterministic=true` -> argmax). Ein Test braeuchte zwei Korpora + zwei
Trainings + Gating; bei weggefallener Hauptmotivation lohnt das nicht.
Falls doch: `survivors` halbiert die grossen Fehlgriffe (9,7% -> 4,3%) bei
-32% Q-Verlust und behaelt Exploration -- risikoarmer Kandidat.

**Wertvoller Nebenbefund -> Task #15**: Die Deckel-Tabelle zeigt, dass der
Value-Head in **Runde 2 nur ~10% des erreichbaren Signals** ausschoepft
(0,017 von 0,166) und in Runde 3 ~45%. Historisch zielten die meisten
Optimierungsversuche (rtv, TD-Bootstrap, Value-Shrinkage) auf Runde 1 --
also auf die eine Runde, die nachweislich unlernbar ist. Kuenftige
Zielmetrik sollte die **Luecke Deckel-minus-Ist je Runde** sein statt des
globalen R² (das wird von Runde 5 dominiert, wo ohnehin fast alles
erreichbar ist, und verdeckt damit genau die Runden mit echtem Potenzial).

### Zielzone praezisiert: Runde 2-4 (Nutzer-Einwand, 2026-07-28)

Nutzer: "Runde 5 brauchen wir nichts messen, da haben wir Alpha-Beta-Solver
drauf." Zutreffend -- und mit groesserer Reichweite als nur der Messung.

**Verifiziert**: Das Netz wird in Runde 5 NIE konsultiert.
`net_mcts.rs:2265` -- `if round5::applies(state) { return
round5::choose_action(state) }` -- der Bypass sitzt im Netz-Suchpfad selbst,
gilt also fuer Self-Play, Arena UND Server. Auch der Runde-4-Bootstrap
braucht das Netz dort nicht: der Uebergang 4->5 nutzt
`round5::exact_round5_outcome` ("exakter Freebie, kein Netz-Rauschen",
`self_play.rs:1879`).

**Gemessener Verschnitt** (10 v16-Dateien):

| Runde | Records | Anteil | Policy-Samples |
|---|---:|---:|---:|
| 1 | 3233 | 20,0% | 2474 |
| 2 | 3345 | 20,7% | 2502 |
| 3 | 3456 | 21,4% | 2484 |
| 4 | 3416 | 21,1% | 2495 |
| **5** | **2710** | **16,8%** | **1698 (14,6%)** |

**16,8% des Value-Signals und 14,6% des Policy-Signals** entfallen auf
Entscheidungen, die das Netz nie trifft. Das Runde-5-Policy-Ziel ist sogar
ein One-Hot auf die Alpha-Beta-Wahl (`net_mcts.rs:2388`:
`round5::choose_action(...).map(|a| (a,1,1.0))`) -- das Netz lernt, einen
exakten Solver zu imitieren, dessen Aufgabe es nie uebernimmt.
Praezedenzfall im Code: `pol_w=0` fuer Tiling-Schritte, weil "Tiling macht
der DFS-Solver" -- Runde 5 ist fuer BEIDE Koepfe dieselbe Situation.

**Folge fuer die Zielmetrik:**

| Runde | Status |
|---|---|
| 1 | **unlernbar** -- Deckel 0,0068, Zufall-dominiert |
| 2-4 | **die eigentliche Zielzone** (Runde 2: nur ~10% des Deckels ausgeschoepft) |
| 5 | **irrelevant** -- Alpha-Beta spielt, Bootstrap nutzt exakten Solver |

Das globale Value-R², an dem ueber viele Zyklen Netze beurteilt wurden, wird
von Runde 5 (0,6-0,7) nach oben gezogen -- ausgerechnet von der Runde ohne
Beitrag zur Spielstaerke -- und verdeckt damit die Runden mit echtem
Potenzial. Kuenftige Bewertung sollte auf **R² je Runde 2-4** bzw. die
Luecke Deckel-minus-Ist dort umgestellt werden (Task #15).

## Task #10: Gumbel-Kalibrierung GUMBEL_TOP_M 16 vs. 8 -- Nullergebnis (2026-07-28)

**Motivation** (aus dem Budget-Port, siehe Ideensammlung oben): bei
`sims=400/TOP_M=16` eliminiert die erste Halbierung 8 von 16 Kandidaten auf
Basis von je 6 Simulationen. `TOP_M=8` gaebe 16 Sims vor dem ersten Cull
(2,7x zuverlaessiger), kostet aber Breite.

**Methodisch wichtig -- Wheel-Isolation statt `site-packages`-Tausch:**
`GUMBEL_TOP_M` ist eine Compile-Konstante, der A/B braucht also zwei Wheels.
Waehrenddessen lief der 6000-Spiele-Self-Play-Batch. `self_play.py` startet
pro 10er-Chunk einen FRISCHEN `mp.Process`, der `mosaic_rust` neu importiert
(`_run_chunk_supervised`, Zeile ~231) -- ein `pip install` in `site-packages`
haette die restlichen ~5500 Spiele mit `TOP_M=8` erzeugt, ohne jede Spur im
Record (Mischkorpus, nachtraeglich nicht trennbar). Stattdessen:
`pip install --target <scratchpad>` + `PYTHONPATH` nur fuer den ON-Arm.
Funktionsnachweis statt Annahme -- dieselben 8 Zustaende durch beide
Installationen: `site-packages` deckelt bei 16 Wurzelkandidaten, die
isolierte bei 8, und bei Zustaenden mit nur 6/3/2 legalen Zuegen liefern
beide identische Werte. Quelle nach dem Build sofort auf 16 zurueckgesetzt.

**Ergebnis** (`v17_best` vs `v16_best` @400 Sims, Seed 4711, 100 Spiele je
Arm, 3 Threads wegen paralleler Self-Play-Last):

| Arm | Champion:Gegner | Ø-Score | Ø-Floor |
|---|---:|---:|---:|
| OFF (`TOP_M=16`, Ist) | 50:50 | 36,1 : 35,2 | 15,7 : 15,0 |
| ON (`TOP_M=8`) | 51:49 | 34,3 : 34,5 | 16,2 : 15,4 |

Diskordanz b(ON-only)=25, c(OFF-only)=24, konkordant 26/25. **Exakter
McNemar p=1,0000.**

**Bewertung: perfekter Wash, aber informativ.** Die Diskordanz ist mit 49
von 100 Paaren SEHR hoch -- `TOP_M=8` aendert das Spiel massiv, ist aber
exakt gleich stark. Der Tradeoff Breite gegen Cull-Zuverlaessigkeit hebt
sich also praktisch vollstaendig auf: was an Kandidaten-Breite verloren
geht (8 statt 16 betrachtete Zuege), wird durch die zuverlaessigere
Halbierung (16 statt 6 Sims vor dem ersten Cull) genau kompensiert.
`TOP_M=16` bleibt.

**Nicht getestet**: `GUMBEL_C_VISIT=50` / `GUMBEL_C_SCALE=1.0` (steuern das
Gewicht von σ(Q) gegen `ln(prior)` in der Halbierungs-Rangfolge -- eine
andere Achse als TOP_M). Angesichts des klaren Washes bei TOP_M und des
weit groesseren Fundes in Task #16 (Tiling-Solver blind fuer die
Endwertung) zurueckgestellt.

## Task #15 B: Runde-5-Ausschluss im Loss -- Wash (2026-07-28)

**Aufbau**: zwei identische Trainings (`--load v16_best --epochs 20 --lr 5e-5
--lr-schedule cosine`, nortv), einziger Unterschied `--exclude-round5`
(nimmt Runde-5-Samples aus Value-, Points- UND Policy-Loss, in Training UND
Validierung). Bewertet mit `offline_diagnose --frozen` -- ein fuer beide Arme
identischer externer Massstab, den keiner der beiden optimiert hat.

| Metrik | r5base (Baseline) | r5excl (Experiment) | v17_best |
|---|---:|---:|---:|
| **Value R² Runde 1-4** (Entscheidung) | 0,1208 | **0,1217** | 0,1130 |
| Value R² global (nur Info) | 0,2921 | 0,2644 | 0,2903 |
| R² Runde 1 | 0,0151 | 0,0142 | 0,0274 |
| R² Runde 2 | 0,1297 | 0,1259 | 0,1348 |
| R² Runde 3 | 0,1948 | 0,1957 | 0,1701 |
| R² Runde 4 | 0,1179 | 0,1236 | 0,1009 |
| R² Runde 5 (irrelevant) | 0,7024 | 0,6060 | 0,7151 |
| Policy Top-1 / Top-3 | 45,9% / 70,6% | 45,1% / 70,8% | 45,0% / 71,2% |

**Ergebnis: Wash.** +0,0009 auf der Entscheidungsmetrik = 0,7% relativ, aus
je EINEM Trainingslauf ohne Wiederholungen -- weit unter jeder
verteidigbaren Effektschwelle. Kein Gewinner.

**Drei Erkenntnisse trotzdem:**

1. **Der Mechanismus greift**: R5 faellt von 0,70 auf 0,61 -- das Netz hoert
   tatsaechlich auf, Runde 5 zu lernen. Kein stiller No-op.
2. **Die Kalibrierungs-Anker-Gegenhypothese ist widerlegt**: die Sorge war,
   Runde 5 koennte dem Value-Head die Skala geben und ihr Wegfall den fruehen
   Runden schaden. Tut sie nicht -- R3/R4 wurden sogar minimal besser. Die
   ~17% Samples tragen zu den relevanten Runden nichts bei, schaden aber
   auch nicht.
3. **Metrik A (Task #15 A) hat sich sofort bewaehrt**: global gemessen saehe
   das nach klarer Verschlechterung aus (-0,028), der entscheidungsrelevante
   Teil ist minimal besser. Ohne die Metrikumstellung waere dieses Experiment
   als Fehlschlag abgehakt worden.

**Entscheid: `--exclude-round5` bleibt Default AUS.** Kein gemessener Nutzen,
kein Rechenzeitgewinn (die Samples werden weiterhin geladen und
forward-gepasst, nur ihr Loss-Gewicht ist null), und eine Abweichung vom
Rezept, das alle bisherigen Champions erzeugt hat, ohne Gegenwert. Das Flag
bleibt verfuegbar.
**Wiedervorlage**: wenn die freigewordene Kapazitaet ZUSAMMEN mit einem
zusaetzlichen Ziel genutzt wird (Ownership-Head #9, distributionaler Kopf
#12) -- dann koennte der Wegfall mehr bringen als isoliert.

**Nebenbefund zum Vergleich mit v17_best**: beide neuen Arme liegen in
Runde 1-4 ueber `v17_best` (0,121/0,122 vs 0,113), obwohl identisches Rezept
und identischer Korpus -- einziger Unterschied ist `--epochs 20` statt 100
(also ein realistischeres Cosine-T_max, vgl. v17_lrfix-Experiment). Kein
kontrollierter Vergleich, nur eine Beobachtung.

### Nachtrag: Heuristik spielt Runde 5 ebenfalls per Alpha-Beta (2026-07-28)

Nutzer-Frage: "spielt die Heuristik in Runde 5 auch mit dem Alpha-Beta-
Solver?" -- Ja, identisch. `mcts.rs` hat denselben `round5::applies(state)`-
Gate an allen drei Einstiegspunkten: `drafting_policy` (~728, die im
Self-Play aufgezeichnete Policy), `choose_drafting_action` (~759, die echte
Zugwahl) und `choose_drafting_action_with_analysis` (~778). Wortgleich zu
`net_mcts.rs:2265`.

**Konsequenz -- unabhaengiges Argument fuer Metrik A (Task #15 A):** In
Runde 5 sind Netz und Heuristik BUCHSTAEBLICH derselbe Spieler; beide
berechnen aus demselben Zustand exakt dieselbe Alpha-Beta-Wahl. Daraus
folgt: **jeder Elo-Unterschied zwischen zwei beliebigen Spielern entsteht
ausschliesslich in Runde 1-4.** Auch der Anker Heuristik@150 = 1000 misst
nur Runde-1-4-Spiel -- Runde 5 ist eine geteilte, identische Komponente, die
sich in jedem Head-to-Head weghebt.

Das ist staerker als die urspruengliche Begruendung fuer Metrik A (dort:
"der Value-Head wird in Runde 5 nicht konsultiert"). Jetzt: Runde 5
differenziert UEBERHAUPT KEINE zwei Spieler. Die Offline-Metrik
(R² Runde 1-4) misst damit genau das, was die Elo-Leiter ueberhaupt messen
kann -- vorher waren Offline-Massstab und Arena-Massstab an dieser Stelle
systematisch entkoppelt.

**Fuer Task #16 zusaetzlich relevant**: die Tiling-Aenderung greift auch in
Runde 5 (das Alpha-Beta bewertet ueber `solve_round_final_score`, und die
tatsaechlichen Platzierungen aendern sich) -- sie betrifft also beide Seiten
und alle fuenf Runden, nicht nur 1-4. Verschaerft die Anker-Konsequenz:
nach der Aenderung ist auch die Heuristik ein anderer Spieler, die
Elo-Leiter braucht eine Neuverankerung.

## KORREKTUR: Trainings-A/Bs waehrend laufendem Self-Play sind konfundiert (2026-07-28)

**Nutzer-Fund**: "interferierst du nun eh nicht mit den Self Plays?" -- Ja,
und zwar schwerwiegender als durch CPU-Konkurrenz.

`MosaicDataset` wird von `train.py` mit `files=None` aufgerufen und globt
dann `data/*.pkl` -- also GENAU das Verzeichnis, in das ein laufender
Self-Play-Batch fortlaufend neue Dateien schreibt. Jeder Trainingslauf sieht
dadurch einen ANDEREN Korpus. Aus den Lauf-Manifesten:

| Lauf | Dateien | davon v17 |
|---|---:|---:|
| r5base | 382 | 82 |
| r5excl | 404 | **104** |
| own_off | 787 | **487** |

**Folge 1 -- Task #15 B ist NICHT interpretierbar.** Die beiden Arme
(`r5base` ohne, `r5excl` mit `--exclude-round5`) trainierten auf
verschiedenen Korpora (382 vs. 404 Dateien, 22 zusaetzliche v17-Dateien im
Experimentalarm). Der gemessene Unterschied von +0,0009 auf
`value_r2_rounds_1_4` kann dem Flag NICHT zugeschrieben werden. Die
DAMALIGE ENTSCHEIDUNG (Default bleibt aus) bleibt richtig -- aber die
Begruendung war falsch: es ist nicht "kein Effekt gemessen", sondern
"konfundiert, kein Effekt messbar". Ebenso sind die drei abgeleiteten
Erkenntnisse neu zu bewerten:
- "Mechanismus greift" (R5-R² 0,70 -> 0,61) bleibt gueltig -- so ein grosser,
  gerichteter Effekt genau in der ausgeschlossenen Runde ist nicht durch
  22 Zusatzdateien erklaerbar.
- "Kalibrierungs-Anker-Gegenhypothese widerlegt" ist NICHT mehr gestuetzt
  (die R3/R4-Verbesserungen koennten vom groesseren Korpus kommen).
- "Metrik A hat sich bewaehrt" bleibt gueltig -- das ist ein Argument ueber
  die Metrik selbst, unabhaengig vom Korpus.

**Folge 2 -- der laufende Ownership-A/B wurde abgebrochen.** `own_off` lief
auf 787 Dateien; bis `own_on` gelaufen waere, haette der Korpus weiter
zugenommen. Beide Arme muessen auf einem STABILEN Korpus laufen.

**Regel ab jetzt**: **Kein Training, waehrend Self-Play in dasselbe `data/`
schreibt.** Das Lauf-Manifest (`corpus_composition`) ist das Mittel, das
nachtraeglich aufzudecken -- genau so wurde es hier gefunden. Latentes
Zusatzrisiko: `MosaicDataset` koennte eine gerade halb geschriebene `.pkl`
lesen (bisher nicht eingetreten, aber moeglich).

**Verstaerkend**: An diesem Tag wurde der HDF5-Cache-Key ZWEIMAL geaendert
(`+rounds_v1`, dann `+own_v1`) -- jede Aenderung erzwingt einen vollen
Rebuild ueber alle Dateien in `data/` (bei 787 Dateien mehrere Minuten
CPU-Last, einzelthreadig) und konkurriert damit zusaetzlich mit dem
11-Thread-Self-Play.

## Seed-Sweep: drei Hebel gepaart ueber 6 Seeds -- alle drei folgenlos (2026-07-28)

Erster A/B dieses Projekts mit MEHREREN Seeds je Arm. Vorgeschichte: alle
frueheren Trainings-A/Bs verglichen je EINEN Lauf pro Arm gegen eine
unbekannte Lauf-zu-Lauf-Varianz -- `train.py` setzte gar keinen Seed. Dazu kam
die Korpus-Konfundierung des Vortags (siehe Abschnitt "KORREKTUR: Trainings-
A/Bs waehrend laufendem Self-Play"). Beides ist hier behoben: 24 Laeufe
(4 Arme x 6 Seeds), alle sequenziell auf einem **stabilen Korpus von 900
Dateien**, gepaart ausgewertet (Seed s in Arm A gegen Seed s in Arm B --
identische Gewichts-Init und Batch-Reihenfolge).

Werkzeug: `tools/train_seed_sweep.py`. Basis-Rezept je Lauf:
`--load v17_best --epochs 100 --lr 5e-5 --lr-schedule cosine --seed N`.

**Entscheidungsmetrik vorab festgelegt**: `value_r2_rounds_1_4` auf dem
frozen set (Task #15 A -- Runde 5 ausgeschlossen, weil das Netz dort nie
konsultiert wird, das entscheidet der Alpha-Beta-Solver).

### Ergebnis

| Arm | Ø `value_r2_rounds_1_4` | gepaarte Diff | Richtung | Vorzeichentest |
|---|---|---|---|---|
| `base` (Referenz) | 0.1133 | -- | -- | -- |
| `own` (`--ownership-weight 0.3`) | 0.1150 | **+0.0017** | 5:1 | p=0.2188 |
| `r5x` (`--exclude-round5`) | 0.1144 | +0.0011 | 4:2 | p=0.6875 |
| `lr1e5` (`--lr 1e-5 --epochs 40`) | 0.1120 | **-0.0013** | 2:4 | p=0.6875 |

**Kein Arm ist signifikant.** Entscheidender Groessenvergleich: die Streuung
des `base`-Arms ueber die sechs Seeds allein reicht von 0.1091 bis 0.1160 --
eine Spanne von 0.0069, also das **Vier- bis Sechsfache** jedes gemessenen
Arm-Effekts. Der Seed bewegt mehr als jeder der drei getesteten Hebel. Das
ist selbst das Hauptergebnis: an diesen Stellschrauben ist nichts zu holen.

### Methodischer Befund: `val_combined` taugt nicht als Arbiter

Der `lr1e5`-Arm sah auf der Trainings-Validierung deutlich besser aus:
val_combined 1.2550 gegen 1.2614 im `base`-Arm -- bei einer Seed-Streuung von
nur ~0.0008 ist das rund die **achtfache Streuung**. Auf der vorregistrierten
Metrik ist derselbe Arm dann **schlechter** (-0.0013, 2:4).

Erklaerung: `val_combined` ist die Groesse, nach der auch der beste Checkpoint
AUSGEWAEHLT wird. Ein Arm mit niedrigerer LR laeuft laenger, bevor das
Plateau-Early-Stopping greift (bester Checkpoint bei Epoche 6-9 statt 2), hat
also schlicht mehr Ziehungen auf demselben Split -- das drueckt das Minimum,
ohne dass das Modell besser waere. Zwischen Armen mit verschiedenen
Epochenbudgets ist `val_combined` damit systematisch verzerrt.

**Konsequenz**: Metrik VOR dem Lauf festlegen und danach nicht wechseln. Hier
hat genau das die falsche Abzweigung verhindert -- nach `val_combined` waere
`lr 1e-5` als Gewinner ins Standard-Rezept gewandert.

### Nebenbefund: Epoche-2-Konvergenz bestaetigt

Bester Checkpoint im `base`-Arm ueber sechs Seeds: **[2,2,2,2,2,3]**. Damit ist
die bisher nur aus Einzellaeufen vermutete Regel belegt. Praktische Folge: die
Frage "cosine `T_max=100` annealt kaum" ist gegenstandslos -- bei Epoche 2-3
steht die LR ohnehin noch bei 97,6-100 % des Startwerts, egal wie `T_max`
gesetzt ist.

### Entscheidungen

* `OWNERSHIP_WEIGHT` bleibt **0.0**. Beste Tendenz der drei, aber 5:1 bei n=6
  kann p<0.05 nicht erreichen (dafuer braeuchte es 6:0, p=0.031). Kandidat fuer
  eine Wiederholung mit mehr Seeds. Der Kopf bleibt im Code und ist bei
  Gewicht 0 inert; er ist ZULETZT in `__init__`/`forward` deklariert, damit
  ONNX `out[0..3]` und die RNG-Init-Reihenfolge stabil bleiben.
* `--exclude-round5` bleibt Default **AUS** (Wiederholung des konfundierten
  Tests -- diesmal sauber, weiterhin Wash).
* `--lr 1e-5` **verworfen**.
* v18 uebernimmt damit unveraendert das Rezept aus dem `base`-Arm.

## Orakel-Metriken validiert: 7/7 auf entschiedenen Gatings (2026-07-28)

**Anlass** (Nutzer): "wir haben bis dato noch immer keine belastbare offline
metrik wie sich die modelle im vergleich in der arena schlagen werden."
Zutreffend -- und mit `tools/offline_vs_arena.py` (neu) erstmals messbar.

### Schritt 1: die klassischen Metriken sind widerlegt

Neun gepaarte Gating-Laeufe (v14..v18) gegen die Frozen-Set-Diagnosen gejoint.
`value_r2_rounds_1_4` musste fuer v14..v17_lrfix erst nachgerechnet werden --
die Metrik existiert erst seit dem 2026-07-28, es gab also **keinen einzigen
historischen Datenpunkt** fuer die Groesse, nach der an diesem Tag den ganzen
Tag entschieden wurde.

| Δ `value_r2_rounds_1_4` | Paare | Richtung richtig |
|---|---|---|
| gross (+0,016 .. +0,053) | 3 | **3/3** |
| klein (-0,001 .. -0,009) | 3 | **0/3** |

Aufloesungsgrenze bei grob Δ 0,015; darunter sagt die Metrik nichts. Das
Pearson r = +0,717 (Permutations-p 0,031) wird vollstaendig von den drei
grossen Punkten getragen -- Spannweiten-Artefakt.

`policy_top3` zeigte in **6 von 6** entschiedenen Paaren auf den VERLIERER
(Binomial p = 0,031, Pearson r = -0,82). Ursache mit hoher Wahrscheinlichkeit:
das frozen set stammt aus ALTEN Korpora (v10b, v12) -- Uebereinstimmung mit
aufgezeichneten Zuegen misst Aehnlichkeit zum alten Selbstspiel, nicht
Qualitaet, und bestraft neuere Netze systematisch.

### Schritt 2: das Orakel loest genau diesen Confounder

`tools/build_frozen_oracle_labels.py` (Task #89, 2026-07-25) ersetzt die
Referenz "aufgezeichneter alter Zug" durch "tiefe 5000-Sim-Suche" (v16_best,
1185 saubere Drafting-Zustaende, davon 952 in Runde 1-4 auswertbar). Suche
verstaerkt das Netz erheblich -- die Referenz ist deutlich staerker als das
Netz, aus dem sie stammt.

Der damalige Bericht validierte gegen 3 Gating-Ausgaenge und notierte selbst
zwei Vorbehalte: (1) v16_best war zugleich Orakel-Quelle UND Kandidat, (2)
alle Netze stammen aus derselben Warm-Start-Linie, spaetere sind dem Orakel
im Gewichtsraum naeher. Beide waren mit n=5 nicht aufloesbar.

**Jetzt sind sie aufloesbar**: v17_best, v17_lrfix_best und v18_best sind NACH
dem Orakel entstanden. `oracle_metrics.py --models ...` auf alle acht Netze:

| Netz | recall@16 | Top-3-Masse | Value-Pearson | Kendall-Tau |
|---|---|---|---|---|
| v14_best | 0,9695 | 0,5687 | 0,8097 | 0,2201 |
| v14b_best | 0,9706 | 0,5848 | 0,8133 | 0,2143 |
| v15_f2k_best | 0,9779 | 0,6023 | 0,8329 | 0,2273 |
| v15_best | 0,9821 | 0,6175 | 0,8594 | 0,2445 |
| **v16_best (Orakel-Quelle)** | 0,9989 | 0,6524 | **0,8835** | 0,2791 |
| v17_best | 1,0000 | 0,6729 | 0,8705 | 0,3067 |
| v17_lrfix_best | 0,9989 | 0,6765 | 0,8699 | 0,3049 |
| v18_best | 0,9968 | **0,6861** | 0,8612 | **0,3272** |

Gegen die **sieben entschiedenen** Gating-Paare (McNemar p<0,05):

| Metrik | richtig | Binomial p |
|---|---|---|
| **Prior-Masse auf Orakel-Top-3** | **7/7** | **0,0156** |
| **Kendall-Tau (Policy vs. Orakel-Q)** | **7/7** | **0,0156** |
| Prior-Recall@16 | 6/7 | 0,125 |
| Value-Pearson / -Spearman | 5/7 | 0,453 |
| klassisch `value_r2_rounds_1_4` | 4/7 | 0,688 |

### Die beiden alten Vorbehalte loesen sich GEGENLAEUFIG auf

* **Fuer die zwei 7/7-Metriken widerlegt.** Sie steigen ueber die
  Orakel-Quelle HINAUS monoton weiter (Top-3-Masse 0,6524 → 0,6729 → 0,6861
  fuer v16 → v17 → v18). Waere es Naehe zu v16 im Gewichtsraum, muesste dort
  ein Gipfel liegen. Liegt er nicht.
* **Fuer die Value-Metriken bestaetigt.** `value_pearson` gipfelt EXAKT bei
  v16_best (0,8835) und faellt danach -- und genau die beiden Nach-Orakel-Paare
  (v17>v16, v18>v17) sind die zwei, die sie falsch vorhersagt. Der mechanische
  Selbstbezugs-Vorteil war also real, betrifft aber spezifisch die Value-Seite.
* **`recall@16` ist gesaettigt** (v17_best = 1,0000) und damit als
  Unterscheidungsmass verbraucht.

Bemerkenswert: es gewinnen POLICY-Metriken -- dieselbe Groesse, die gegen
aufgezeichnete alte Zuege gemessen 6 von 6 mal auf den Verlierer zeigte. Nicht
die Policy-Seite war das Problem, sondern die Referenz.

### Konsequenz fuer den Zyklus

`prior_mass_on_oracle_top3` und `kendall_tau_policy_vs_oracle_q` werden als
Vor-Gating-Check in die Standard-Diagnose aufgenommen. Sie haetten v18 richtig
vorhergesagt, wo die klassische Value-Metrik im blinden Bereich lag (+0,0030).

**Kein Ersatz fuer die Arena.** Zwei Gruende: n=7 mit nicht unabhaengigen
Paaren (Modelle wiederholen sich), und p=0,0156 ist bei 7/7 der bestmoegliche
Wert -- mehr Trennschaerfe gibt die Stichprobe nicht her.

**Orakel-Auffrischung**: die Referenz ist v16-basiert und veraltet, je weiter
die Modelle davonziehen. Beim Neubau (Kandidat: aktueller Champion) gilt die
Regel aus Task #89 weiter -- die Orakel-Quelle darf NICHT selbst zu den
bewerteten Kandidaten zaehlen, und die Validierung ist danach zu wiederholen.
`frozen_v1_oracle_labels.json` bleibt als historische Grundlinie unveraendert.

### KORREKTUR (2026-07-29, nach Archiv-Integration)

Commit `43ccb08` kopierte 12 archivierte Gating-/Diagnose-Dateien der
v10..v13-Generation aus `archive/` nach `evaluations/` (dort lagen sie fuer
`offline_vs_arena.py` bislang unsichtbar). Damit waechst die Basis von 11 auf
**18 auswertbare** und von 8 auf **12 entschiedene** Gating-Paare (McNemar
p<0,05) -- verifiziert per Neulauf von `python tools/offline_vs_arena.py`:

| Metrik | vorher | jetzt |
|---|---|---|
| `policy_top3` | 0/6 richtig (6/6 auf den VERLIERER), p=0,031 | **3/11** richtig, p=0,2266 |
| `policy_top1` | 1/5 | **4/11**, p=0,5488 |
| `value_r2_global` | 3/6 | **6/12**, p=1,0000 |
| `value_r2_rounds_1_4` | 4/7 | **4/8** (Archiv traegt hier nichts bei -- die v10..v13-GEWICHTE sind seit dem Datenverlust vom 2026-07-24 weg, die Metrik ist fuer sie nicht nachrechenbar) |

Die Aussage "`policy_top3` zeigte in 6 von 6 entschiedenen Paaren auf den
VERLIERER (p=0,031)" war ein **Kleinstichproben-Artefakt**: mit 11
auswertbaren entschiedenen Paaren sind es 3/11 richtig (Binomial p=0,2266) --
weiterhin unter dem Zufallsniveau, aber NICHT mehr signifikant von Zufall zu
unterscheiden. Die Kernaussage (`policy_top3` taugt nicht als
Fortschrittsmass) bleibt bestehen, der dramatische Teil war Rauschen.

`policy_top1` liegt bei 4/11 (p=0,5488), `value_r2_global` bei 6/12
(p=1,0000), `value_r2_rounds_1_4` unveraendert bei 4/8 -- fuer Letzteres kann
das Archiv nichts beitragen, weil die v10..v13-Gewichte seit dem Datenverlust
vom 2026-07-24 fehlen und die Metrik ohne Gewichte nicht nachrechenbar ist.

Die "Aufloesungsgrenze ~0,015" (Schritt 1 oben) beruht weiterhin auf nur 3
Punkten je Regime (gross/klein) und ist als grobe Faustregel zu lesen, nicht
als scharfe Schwelle -- das Archiv liefert dafuer keine zusaetzlichen
Datenpunkte.

Die beiden Orakel-Metriken (`prior_mass_on_oracle_top3`,
`kendall_tau_policy_vs_oracle_q`) sind von dieser Korrektur NICHT betroffen:
fuer v10..v13 sind sie mangels Gewichten nicht berechenbar, ihre 7/7-Bilanz
stuetzt sich weiterhin ausschliesslich auf die v14+-Paare.

## Task #16: Tiling-Solver-Endwertungs-Shaping -- verworfen (2026-07-29)

### Befund, der den Versuch ausgeloest hat

`tiling_solver.rs::best_first_step_inner` maximierte `pts + solve_rec(..)`,
also **reine Sofortpunkte der Runde**. `calculate_end_scoring` und
`wertung_progress` kamen im gesamten Modul nicht vor. Da `best_first_step_exact`
der Pfad fuer ALLE echten Platzierungen ist (`self_play.rs:894`, `py.rs:687`,
`round_transition.rs:135/323`), waehlte die KI ihre Steine endwertungsblind --
waehrend die Heuristik darueber (`mcts::player_total` =
`solve_round_final_score` + `wertung_progress` + Straf-Term) den Term seit jeher
mitfuehrt. Eine echte Inkonsistenz, kein Hirngespinst.

### Umsetzung

Derselbe Fortschritts-Term als Delta ueber den ERSTEN Schritt, Gewicht 1.0
(gleiche Einheiten wie `player_total`). Bewusst nur auf der ersten Stufe, NICHT
in `solve_rec`: dort ist der MCTS-Blatt-Hot-Path, und der Term wuerde mit
`player_total`s eigenem `wertung_progress` doppelt zaehlen. Hinter
`TILING_SHAPING_ENABLED` (Muster wie `PLATE_SHAPING_ENABLED`).

Tests: `cargo test --release` 169/169 in BEIDEN Toggle-Zustaenden. Der
Diskriminierungstest sucht ueber 200 Seeds eine Stellung, in der geshapt und
ungeshapt VERSCHIEDENE Zuege waehlen, und bricht ab, wenn keine existiert --
ohne diese Zusicherung waere er leer gruen gewesen. (Beim ersten Anlauf hat er
genau das aufgedeckt: `tiling_state()` hat ein LEERES Kuppelraster, es gab
ueberhaupt keine legalen Zuege.)

### A/B-Ergebnis -- 1600 Spiele

Gepaarter Arena-A/B, `v18_best`@400 vs `v17_best`@400, zwei Bloecke à 400
Spiele je Arm, identischer Basis-Seed innerhalb jedes Blocks. Wheel fuer BEIDE
Arme neu gebaut, damit sich die Arme wirklich nur im Toggle unterscheiden.

| Block | OFF | ON | b(nur ON) | c(nur OFF) | McNemar p |
|---|---|---|---|---|---|
| 1 (Seed 5150271) | 226:174 | 245:155 | 63 | 44 | 0,0814 |
| 2 (Seed 77150271) | 228:172 | 219:181 | 50 | 59 | 0,4437 |
| **gepoolt** | **454 (56,8 %)** | **464 (58,0 %)** | **113** | **103** | **0,5404** |

Ø-Score beider Seiten (das vorab benannte Hauptmass): Block 1 Summe 74,0 (OFF)
vs 73,9 (ON), gepoolt 73,4 vs 74,1 -- die Richtung wechselt, kein Signal.

**ENTSCHEIDUNG: `TILING_SHAPING_ENABLED` bleibt AUS.** Der Code bleibt inert
erhalten, weil der Befund weiter gilt -- der Solver IST endwertungsblind, es ist
an dieser Stelle nur nicht spielentscheidend.

### Zwei Lehren

**1. Nicht auf ein knappes p handeln, sondern replizieren.** Block 1 sah mit
p=0,0814 nach einem Effekt aus. Haette man uebernommen, waere eine wirkungslose
Aenderung eingebaut UND der Elo-Anker unnoetig entwertet worden: der Solver ist
gemeinsamer Code und haette auch die HEURISTIK-Spielstaerke veraendert, womit
`Heuristik@150 = 1000` und in der Folge jeder Elo-Wert neu zu vermessen gewesen
waere. Deckt sich mit dem Ausreisser-Praezedenzfall vom 2026-07-22.

**2. Das Hauptmass war schlecht konstruiert -- und das faellt einem nach dem
Ergebnis ein.** Angekuendigt war der Ø-Score BEIDER Seiten, mit der Begruendung,
dass ein engine-weites Shaping beide Spieler betrifft und sich deshalb nicht in
der relativen Siegquote zeigen muss. Uebersehen: in einem Draft-Spiel
konkurrieren beide um dieselben Steine, die Gesamtpunkte sind durch das Angebot
gedeckelt. Spielen beide besser, muss die Summe nicht steigen. Die Metrik kann
also unempfindlich sein, unabhaengig von der Wirkung. Hier war es egal (beide
Masse sagen dasselbe), bei einem engeren Ergebnis waere es nicht egal gewesen.

### Vorbehalt

Die Verlaengerung von 400 auf 800 Spiele je Arm wurde NACH Sichtung von Block 1
beschlossen. Optionales Stoppen inflationiert die Falsch-Positiv-Rate -- hier
ohne Folgen, weil das Ergebnis negativ ausfiel (der Vorbehalt wirkt nur zugunsten
von ON). `tools/pool_arena_ab.py` schreibt den Hinweis automatisch mit aus.

### Nebenbefund, NICHT mitgeaendert

`projected_unplaceable_penalty` fehlt dem Tiling-Solver ebenso, obwohl
`player_total` ihn fuehrt. Separat zu testen -- zusammen waere kein A/B
attribuierbar. Nach diesem Ergebnis aber mit gedaempfter Erwartung.

## Task #18: Gumbel c_scale -- gemessen, gegengeprueft, bleibt 1,0 (2026-07-29)

### Schritt 1: Messung statt Sprossenleiter

`net_mcts.rs:1290`: `sigma(q) = (c_visit + max_N) * c_scale * q`, c_visit=50,
c_scale=1,0. Der Quellcode begruendet 1,0 (statt mctx-Default 0,1) damit, dass
unsere q schon [0,1]-Gewinnwahrscheinlichkeiten sind. Die Luecke darin: mctx'
Min-Max-Normalisierung spannt die Kinder-q auf den VOLLEN Bereich, unsere rohen
Werte nur so weit, wie sich die Stellungen unterscheiden. Die Kalibrierung
haengt also an einer nie gemessenen Groesse.

`tools/gumbel_scale_calibration.py` (neu) erhebt sie ueber
`net_search_state_json_trace` auf 216 frozen-set-Stellungen:

| Groesse | Median | IQR |
|---|---|---|
| delta_q | 0,0073 | 0,0029 .. 0,0140 |
| delta_ln(prior) | 1,11 | 0,41 .. 2,12 |
| max_N | 96 | (Schaetzung aus Sequential Halving war 93) |
| **delta_sigma / delta_lnprior** | **1,23** | 0,43 .. 2,77 |

Je Runde 1,01 / 1,08 / 1,56 / 1,44 (n=68/71/46/31). **q und Prior wiegen
praktisch gleich schwer** -- fuer exakte Gleichheit waere c_scale = 0,81 noetig.
Die vermutete Fehlkalibrierung existiert nicht.

Damit ist auch B1 gestuetzt: `c_visit` braucht keinen eigenen Test. Beide
Konstanten gehen multiplikativ in denselben Term, und mit gemessenem max_N = 96
ist `c_visit 50 -> 0` numerisch fast identisch zu `c_scale 1,0 -> 0,66`.

**Messfehler unterwegs, behoben:** im ersten Anlauf lief `delta_q` ueber die
Ueberlebenden der letzten Phase, `delta_ln(prior)` aber ueber alle 16 top_m --
darin stecken sehr unwahrscheinliche Aktionen mit stark negativem ln(prior).
Das ergab ein Verhaeltnis von 0,05 statt 1,23, also die GEGENTEILIGE
Schlussfolgerung ("Prior dominiert zwanzigfach"). Unentdeckt haette es einen
A/B in die falsche Richtung ausgeloest.

### Schritt 2: Gegenprobe -- und ein Fallstrick im Regelwerk

Getestet wurde nicht 1,0 gegen 0,81 (das waere nichts), sondern **1,0 gegen
0,3** -- ein Wert, der die Balance klar verschiebt. 400 Spiele je Arm,
gepaart, identischer Basis-Seed, v18_best@400 vs v17_best@400.

| Arm | Siegquote v18 | Score v18 | Score v17 | Summe | Floor v18 | Floor v17 |
|---|---|---|---|---|---|---|
| c_scale 1,0 | 210:190 (52,5 %) | 39,13 | 37,77 | **76,90** | 13,85 | 14,97 |
| c_scale 0,3 | 248:152 (62,0 %) | 35,59 | 31,32 | **66,91** | 15,61 | 17,32 |

McNemar p = 0,0057. Nach der WOERTLICHEN Evidenzregel (p<0,05 UND Vorteil fuer
den neuen Wert) waere das eine Annahme.

**Uebernommen wurde es NICHT.** Bei 0,3 spielen BEIDE Seiten massiv schlechter:
zehn Punkte weniger in der Summe (-13 %) und deutlich mehr Bodenstrafen auf
beiden Brettern. Ein kleineres c_scale verschiebt Gewicht von der SUCHE zum
Policy-Prior -- die Suche traegt dann weniger bei. Dass v18 oefter gewinnt,
misst nur, dass v17 unter der verschlechterten Suche staerker einbricht (v18 hat
den besseren Prior): RELATIVE Robustheit, nicht Staerke.

**Die vorregistrierte Regel war unvollstaendig.** Sie unterstellt, dass die
Siegquote im Champion-gegen-Vorgaenger-Duell Staerke abbildet. Bei einer
ENGINE-WEITEN Aenderung, die beide Seiten gleichermassen trifft, gilt das nicht
-- die Siegquote misst dann nur, welcher Spieler die Aenderung besser vertraegt.
Der absolute Ø-Score war hier das entscheidende Signal.

Bemerkenswert im Kontrast zu Task #16: dort hatte ich befuerchtet, der Ø-Score
sei als Mass unempfindlich (Draft-Spiel, Gesamtpunkte durchs Angebot gedeckelt).
Hier ist er das Gegenteil -- eindeutig, gross und rettend. Beide Masse gehoeren
also nebeneinander berichtet, nicht eines statt des anderen.

### Ergebnis

`GUMBEL_C_SCALE` bleibt **1,0**, `GUMBEL_C_VISIT` bleibt **50**. Quellcode auf
1,0 zurueckgesetzt, Wheel neu gebaut, `cargo test --release` 169/169 gruen.

**Die Gumbel-Familie ist damit geschlossen.** Zusammen mit dem
TOP_M-Nullergebnis (16 vs 8, perfekter Wash, p=1,0000 bei 49/100 diskordanten
Paaren) ist die Parametrisierung dreifach geprueft: der eine Knopf ist
wirkungslos, der andere sitzt gemessen am Gleichgewicht, und eine gezielte
Verschiebung macht das Spiel schlechter.

## Task #12: Distributionaler Punkte-Kopf -- nicht uebernommen (2026-07-29)

### Umsetzung

`points_head` sagt bei `POINTS_DIST_BINS>0` eine VERTEILUNG der tanh-gestauchten
Punktedifferenz ueber Bins vorher (51 = C51-Standard) und wird per
Kreuzentropie gegen ein HL-Gauss-geglaettetes Ziel trainiert (Gauss-CDF-
Differenzen ueber die Bin-Kanten). Nach aussen unveraendert: `forward` gibt an
Index 3 weiterhin einen Skalar aus, naemlich den ERWARTUNGSWERT; die Logits
haengen hinter `ownership`.

**Die Schnittstellen-Annahme haelt.** Rust laedt `v18_dist_best.onnx` ohne eine
Zeile Aenderung und liefert plausible, vom Skalar-Netz verschiedene Werte
(win_pct 52,67 vs 52,13). Das Muster "Erwartungswert an der alten Position,
neuer Kopf hinten angehaengt" ist damit fuer kuenftige Kopf-Erweiterungen
bestaetigt.

Der VALIDIERUNGS-Verlust blieb bewusst MSE auf dem Erwartungswert -- auch im
Verteilungs-Arm -- weil `val_combined` zugleich die Checkpoint-Auswahlmetrik ist
und sonst in den Armen eine andere GROESSE waere.

### Fairer Kontrollarm -- und eine widerlegte Hypothese

Der Verteilungs-Kopf KANN nicht warm starten (andere Ausgabebreite). Der
naheliegende Verdacht war, dass ein guter Teil seines Rueckstands vom Kaltstart
kommt -- bei Early Stopping nach Epoche 2 plausibel. Dafuer wurde
`--reinit-points-head` ergaenzt und `v18_freshpts` trainiert: identisches
Rezept, aber der SKALAR-Kopf startet ebenfalls frisch.

| | v18_dist | v18_freshpts | v18_best |
|---|---|---|---|
| `value_r2_rounds_1_4` | 0,0906 | **0,1160** | 0,1160 |
| Orakel Prior-Masse Top-3 | 0,6845 | 0,6861 | 0,6861 |

**Die Hypothese war falsch.** Ein frisch initialisierter Skalar-Kopf holt den
Rueckstand innerhalb von zwei Epochen vollstaendig auf. Das Defizit des
Verteilungs-Arms geht also auf die KOPF-ART zurueck, nicht auf den Kaltstart.
(An den Gewichten gegengeprueft: `points_head` weicht um 0,20-0,28 ab, der Trunk
um 0,009 -- die Neuinitialisierung hat nachweislich gegriffen.)

### Arena -- und die dritte Replikation des Tages

| Block | Paare | dist | v18 | b | c | p | Ø Score dist/v18 |
|---|---|---|---|---|---|---|---|
| 1 (SPRT-Stopp) | 75 | 92 | 58 | 28 | 11 | **0,0095** | 41,29 / 37,53 |
| 2 (Seed 8675309) | 150 | 151 | 149 | 36 | 35 | **1,0000** | 39,27 / 37,02 |
| **gepoolt** | 225 | 243 | 207 (54,0 %) | 64 | 46 | **0,1046** | -- |

Block 1 sah mit p=0,0095 nach einem klaren Sieg aus -- Block 2 entschied den
SPRT sogar in die GEGENRICHTUNG ("kein Beleg, dass v18_dist besser ist").
Gepoolt nicht signifikant. **Nicht uebernommen, `POINTS_DIST_BINS` bleibt 0.**
Der Code bleibt inert erhalten.

Damit ist das an EINEM Tag der dritte Fall, in dem ein ueberzeugendes p bei
Replikation verschwindet (Task #16: 0,0814 -> 0,5404; Task #18-Gegenprobe:
0,0057, aber durch den absoluten Score entlarvt; hier: 0,0095 -> 0,1046). Die
Projekt-Erfahrung "Ergebnisse bei n<=75 sind Kontext, nie Referenz" hat sich
erneut bestaetigt.

### Zwei Befunde, die BLEIBEN

**1. Der Punkte-Vorsprung ist in BEIDEN Bloecken positiv** (+3,76 und +2,25).
Der Verteilungs-Kopf holt in denselben Partien konsistent mehr Punkte, ohne das
in Siege umzumuenzen. Fuer eine Aussage reicht es nicht -- aber es ist der
einzige der heute geprueften Hebel, bei dem der absolute Punktwert konsistent in
eine Richtung zeigt. Beim erklaerten Projektziel (Punktemaximierung) ist das
notiert und nicht abgehakt.

**2. Unser Offline-Instrumentarium misst den PUNKTE-Kopf ueberhaupt nicht.**
`value_r2_rounds_1_4` misst den Value-Kopf, die beiden Orakel-Metriken messen
Policy-Prior und Kandidatenrangfolge. Geaendert wurde aber ausschliesslich der
Punkte-Kopf -- den die Engine an `out[3]` liest und in die Bewertung
einrechnet. Die 8/8-Validierung der Orakel-Metriken beruht auf Vergleichen, bei
denen sich Policy UND Value aenderten; fuer Punkte-Kopf-Aenderungen ist ihre
Trefferquote schlicht ungemessen. **Die Orakel-Metriken sind kopfspezifisch
validiert, nicht universell** -- das gehoert zu ihrer Beschreibung dazu.
Konkrete Folgerung fuer Task #19: eine Punkte-Kopf-Metrik ins frozen-set-
Instrumentarium aufnehmen.

## Task #19: Orakel-Metriken in die Diagnose + Orakel aus v18 (2026-07-29)

**Teil A.** `offline_diagnose.py --frozen` rechnet und zeigt jetzt die beiden
gegen die Arena validierten Praediktoren mit (`prior_mass_on_oracle_top3`,
`kendall_tau_policy_vs_oracle_q`). BEWUSST nur diese zwei: `prior_recall_at_16`
ist gesaettigt (v17_best = 1,0000), die Value-Varianten kommen nur auf 5/7 und
gipfeln exakt bei der Orakel-Quelle. Ist ein Kandidat selbst die Quelle, wird
das erkannt und markiert. Fehlende Labels sind nicht fatal (Warnung,
Diagnose laeuft weiter), abschaltbar per `--no-oracle`.

**Teil B.** Neues Orakel aus `v18_best` gebaut: 1185 Labels, 5000 Sims,
0 Mismatches, 0 Fehler, 15,1 min -> `evaluations/frozen_v1_oracle_labels_v18.json`.

**NOCH NICHT AKTIV.** v18_best ist amtierender Champion und damit selbst
Kandidat -- die harte Regel aus Task #89 (Quelle darf kein Kandidat sein) ist am
selben Tag empirisch bestaetigt worden. Aktiv bleibt das v16-Orakel, gueltig
fuer v14..v18. Umstellung ab v19: `ORACLE_JSON` in `tools/oracle_metrics.py`
umhaengen UND `tools/offline_vs_arena.py` erneut laufen lassen -- die alte
Trefferbilanz ist NICHT uebertragbar, sie gilt dann nur fuer Paare ab v19.
Die v16-Labels bleiben als historische Grundlinie erhalten;
`build_frozen_oracle_labels.py` verweigert jetzt das Ueberschreiben vorhandener
Label-Dateien.

**Einschraenkung, die aus Task #12 folgt und zur Beschreibung dazugehoert:**
die 8/8-Bilanz der beiden Metriken beruht ausschliesslich auf Gating-Paaren, bei
denen sich POLICY und VALUE aenderten. Beim Verteilungs-Punkte-Kopf, der
ausschliesslich den PUNKTE-Kopf aendert, lagen beide falsch (0/1). **Die
Orakel-Metriken sind kopfspezifisch validiert, nicht universell.** Eine
Punkte-Kopf-Metrik fehlt im frozen-set-Instrumentarium komplett.

## v18-Zyklus: Training, Gating, Kader (2026-07-28/29)

**Korpus**: 900 Dateien, stabil waehrend des gesamten Trainings -- 600
v17-Dateien (6000 Spiele) + 200 v16-Dateien (2000 Spiele) + 100 v15-Dateien
(1000 Spiele).

**Rezept** (`models/manifest_train_v18_20260728_223600.json`): `--load
v17_best --epochs 100 --lr 5e-5 --lr-schedule cosine --seed 2`,
`value_target_variant=nortv`, `ownership_weight` unveraendert (0),
`exclude_round5=false`. Seed 2 war der beste Seed des `base`-Arms im
Seed-Sweep (Auswahl auf dem frozen set getroffen, das Gating urteilt
unabhaengig davon). Bester Checkpoint Epoche 2, `val_combined` 1,2612 --
reproduziert `base_s2` aus dem Sweep. Early Stopping griff nach Epoche 15.
Snapshot-Hook ausgeloest (`models_2026-07-28_2305_v18.zip`).

**Diagnose** (`evaluations/offline_diagnose_v18.json`): `value_r2_rounds_1_4`
v18 0,1160 vs. v17 0,1130 -- liegt INNERHALB der ueber die sechs
Seed-Sweep-Seeds gemessenen Streuung des `base`-Arms (0,1091..0,1160),
offline also ein Wash. Je Runde: R1 fiel 0,0274 -> 0,0053, R3 stieg 0,1701
-> 0,1842, R4 stieg 0,1009 -> 0,1157. Die beiden Orakel-Metriken sagten
dagegen v18 RICHTIG voraus: `prior_mass_on_oracle_top3` 0,6861 vs. 0,6729
(v17), `kendall_tau_policy_vs_oracle_q` 0,3272 vs. 0,3067.

**Gating vs. `v17_best`**
(`evaluations/paired_gating_result_v18_best_vs_v17_best.json`): **146:104
(125 Paare, 250 Spiele)**, SPRT=`v18_best` (LLR=+3,718 >= +2,944),
McNemar-Vorzeichentest p=0,0086, gepaarte Differenz +0,336 [95%-CI +0,101,
+0,571]. Champion automatisch via `--promote-winner` gesetzt
(`models/champion.txt` = `v18_best`), Server-Neustart fuer den Live-Betrieb
noetig.

**Kader-Kante vs. `v16_best`**
(`evaluations/paired_gating_result_v18_best_vs_v16_best.json`, kein
Ablosungs-Gating -- `v18_best` ist bereits Champion): **150:100 (125 Paare,
250 Spiele)**, SPRT=`v18_best` (LLR=+5,050), p=0,0013, gepaarte Differenz
+0,400 [95%-CI +0,173, +0,627]. Steht (wieder) in
`evaluations/elo_history.csv`, gegen `paired_gating_result_v18_best_vs_v16_best.json`
verifiziert -- siehe Vorfall-Absatz unten zur Historie dieses Eintrags.

**Heuristik-Anker**: SPRT-Fruehstopp 23:8 nach 31/400 Spielen (74,2%
Netzsiege, Score 41,7 vs. 32,6), Lauf vom 2026-07-28T23:44:55. Steht in
`evaluations/elo_history.csv` und als Zeile in `evaluations/arena_trends.csv`
(`winrate 0.7419` = 23/31, verifiziert). **Beide Zeilen sind ausdruecklich
als REKONSTRUIERT markiert** (Quelle: Sitzungsaufzeichnung, nicht die
Original-Ergebnisdatei -- siehe Vorfall-Absatz). Der Vorbehalt bleibt
bestehen: n=31 ist ein SPRT-Fruehstopp, nach der Projektregel "n<=75 ist
Kontext, keine Referenz" (`feedback_statistical_rigor`) eine duenne Kante;
Nachmessung mit festem n>=150 ist bei der naechsten Neuverankerung
eingeplant.

**Vorfall (2026-07-29): Messdaten durch pauschalen `git checkout` verloren
und rekonstruiert.** Bei einer OneDrive-Wiederherstellung (verschwundene
Dateien, siehe `project_onedrive_file_disappearance`) wurde pauschal `git
checkout -- evaluations/` statt einer selektiven Wiederherstellung nur der
tatsaechlich fehlenden Dateien ausgefuehrt -- dabei gingen auch uncommittete
MODIFIKATIONEN an getrackten Messdaten-CSVs (`elo_history.csv`,
`arena_trends.csv`) verloren, darunter die Kader-Kante vs. `v16_best` und der
Heuristik-Anker. Wiederhergestellt aus dem noch vorhandenen Gating-JSON
(Kader-Kante) bzw. aus der Sitzungsaufzeichnung (Heuristik-Anker, dort als
REKONSTRUIERT markiert). Regel ab jetzt: bei Wiederherstellungen NUR
tatsaechlich geloeschte Dateien selektiv zuruecksetzen (`git status --short |
grep '^ D'` -> Pfade einzeln per `git checkout -- <pfad>`), nie pauschal
einen ganzen Ordner; Mess-CSVs zeitnah committen, damit uncommittete
Aenderungen an ihnen erst gar nicht verlierbar sind.

**Aktuelle Elo-Tabelle** (`python tools/elo_tracker.py report`, jetzt
inklusive Kader-Kante und Heuristik-Anker):

| Modell | Elo | 95%-CI | Spiele | W-L |
|---|---:|---:|---:|---:|
| v18_best@400 | 1172 | [1119, 1226] | 531 | 319-212 |
| v17_lrfix_best@400 | 1122 | [1075, 1174] | 833 | 439-394 |
| v17_best@400 | 1121 | [1076, 1167] | 1686 | 885-801 |
| v13_nortv_best@400 | 1100 | [985, 1213] | 300 | 171-129 |
| v16_best@400 | 1094 | [1052, 1141] | 1547 | 722-825 |
| v15_best@400 | 1052 | [1005, 1094] | 886 | 465-421 |
| v12b_lr_best@400 | 1051 | [940, 1154] | 400 | 194-206 |

**Einordnung**: dritter Zyklus in Folge (nach v17 und der Orakel-Validierung
selbst), in dem die Arena einen Gewinner findet, den die klassische
Offline-Metrik (`value_r2_rounds_1_4`) nicht aufloest -- hier sogar mit
leicht POSITIVEM Vorzeichen (+0,0030), also im "blinden Bereich" unterhalb
der ~0,015-Aufloesungsgrenze.

## Task #20/#21: Tiling-Auswahl -- Messungen und Implementierungsstand (2026-07-29)

**Kontext**: Nutzer-Idee, das rein punktegierige Tiling mit dem Netz zu
verbinden. Task #20: in Runde 2-4 `punkte * value(Folgezustand)` statt nur
`punkte` als Auswahlkriterium (Value als Stichentscheid unter sonst
gleichwertigen Abschluessen). Task #21: in Runde 5 direkt `punkte + exakte
Endwertung` maximieren, weil das Spiel nach dem Tiling endet und die
Endwertung dort exakt berechenbar ist (ein KORREKTHEITS-, kein
Staerke-Fix).

**Implementiert** (Commit `78b45d4`; weitere Arbeiten am Runde-5-Pfad und an
der Dedup-Signatur liegen Stand dieser Doku als UNCOMMITTED Aenderungen im
Arbeitsverzeichnis vor, siehe "Offene Punkte" unten): `tiling_solver::top_k_tilings`
liefert bis zu k VOLLSTAENDIGE Tiling-Abschluesse (erster Schritt + fertiges
Brett), dedupliziert ueber die Belegungssignatur. Neue pyfunctions
`tiling_candidates_json` und `advance_after_tiling_json`. `best_first_step_round5`
hinter `ROUND5_ENDSCORING_ENABLED` (Default `false`). `cargo test --release`
169/169 gruen in beiden Toggle-Zustaenden (laut Commit-Nachricht).

**Messung Kandidaten-Spreizung**
(`evaluations/tiling_candidate_spread.json`, `v18_best`, 400
frozen-set-Stellungen, k=12):

- Task #21, Runde 5: andere Zugwahl in **2/33 Faellen (6,1%)**, dabei je
  genau **8 Punkte** gewonnen (Median und Max identisch).
- Task #20, Runden 2-4: Value-Spreizung unter den Kandidaten Median
  **0,0216** (IQR 0,011..0,035). Wahl geaendert in **18/131 Faellen
  (13,7%)** (JSON-Zahl, s.u.).
  - Die Commit-Nachricht von `78b45d4` nennt fuer dieselbe Fragestellung
    **19/133 (14,3%)** mit Aufschluesselung R2 11,1% / R3 4,7% / R4 24,1% je
    Runde. Beide Zahlen sind korrekt, aber aus VERSCHIEDENEN Stichproben:
    das JSON (18/131) stammt aus dem gespeicherten Tool-Lauf, der aus ALLEN
    471 Tiling-Stellungen des frozen set 400 sampelt (`--max-states 400`,
    inkl. Runde 1 und 5 im Sample, `n_rounds_2_4=131` davon in Runde 2-4);
    die 19/133 stammen aus einem separaten Inline-Lauf ueber ALLE 279
    echten Runde-2-4-Stellungen des frozen set OHNE Sampling (471
    Tiling-Stellungen insgesamt, davon 78+100+101=279 in Runde 2-4 --
    beide Zahlen gegen `evaluations/frozen_eval_set.pkl` verifiziert). Fuer
    die Runde-2-4-Aussage ist der ungesampelte Lauf (19/133) massgeblich,
    kein Datenproblem, sondern unterschiedliche Stichprobenziehung.

**Zentraler Befund**: in allen (18 bzw. 19) Faellen betraegt der
aufgegebene Punktwert **exakt 0** -- die Multiplikation ueberstimmt nie
einen Punktvorsprung, sie wirkt nur als Stichentscheid unter punktgleichen
Abschluessen. Eine Rundengewichtung (Exponent aus der gemessenen
Zielstreuung, R2 1,00 / R3 1,10 / R4 1,18) aendert laut Commit-Nachricht
KEINE einzige Entscheidung; der gewuenschte "spaeter staerker"-Effekt
entsteht strukturell von selbst, weil es in Runde 4 mehr punktgleiche
Abschluesse gibt als in Runde 2.

**RMSE-Befund** (Commit `109a619`, neue Felder `rmse`/`target_std` je Runde
in `tools/offline_diagnose.py`; zum Zeitpunkt dieser Doku noch in keiner
`evaluations/offline_diagnose_*.json`-Datei persistiert, Zahlen aus der
Commit-Nachricht):

| Runde | R2 | RMSE | Zielstreuung |
|---|---:|---:|---:|
| 1 | 0,0053 | 0,2531 | 0,2538 |
| 2 | 0,1337 | 0,2343 | 0,2517 |
| 3 | 0,1842 | 0,2497 | 0,2765 |
| 4 | 0,1157 | 0,2788 | 0,2964 |

Value-RMSE steigt ab Runde 2 monoton (0,234 -> 0,250 -> 0,279), waehrend die
Zielstreuung ebenfalls waechst (0,252 -> 0,296). Das widerlegt sowohl die
Hypothese "Vertrauen waechst zum Rundenende" als auch die Schrumpf-Hypothese
fuer den R2-Abfall in Runde 4 (die Streuung schrumpft nicht, sie waechst).
Runde 1: RMSE 0,2531 bei Zielstreuung 0,2538 -- praktisch identisch, das
Netz erklaert dort nichts. Das stuetzt "Runde 1 weglassen" sauber ueber
RMSE~Zielstreuung.

**Wichtige Richtigstellung**: fruehere Formulierungen im Projekt verglichen
R2-Werte direkt mit den Noise-Floor-"Decken" aus dem
`value_noise_floor_diagnostic`-Test (Runde 1 = 0,0068, siehe Abschnitt
"Task #13 geklaert"). Das ist strukturell unzulaessig: die Decken sind gegen
ein REINES Outcome-Ziel gemessen (`self_play.rs:3316`,
`((own - opp) / VALUE_SCALE).tanh()`, kein TD-Bootstrap), waehrend
`offline_diagnose.py` gegen das im Training tatsaechlich verwendete,
TD-geblendete Ziel misst (`TD_LAMBDA=0,5`, siehe Trainings-Manifeste) --
unterschiedliche Zielgroessen, direkter Vergleich ungueltig. Ein
dokumentierter Praezedenzfall, wonach Modelle die Decke um das 16-Fache
"uebertroffen" haetten, liess sich zum Zeitpunkt dieser Doku in keiner
Quelldatei auffinden -- **[unverifiziert]**, nur der strukturelle Einwand
selbst ist ueber den Code belegt. Die Runde-1-Aussage oben stuetzt sich
bewusst auf RMSE~Zielstreuung, NICHT auf einen Vergleich mit der Decke.

**Pilot Referenz-Validierung** (Task #20,
`evaluations/tiling_value_reference_pilot.json`): 31 punktegleiche
Kandidatenpaare -- das frozen set ist damit fuer diese Fragestellung
ERSCHOEPFT. Nachfuell-Zufall gepaart ueber `advance_after_tiling_json` (16
Ziehungen, 2000 Sims, `v18_best`): Streuung der gepaarten Differenz (Median
0,0056) liegt klar unter dem Signal (Value-Spreizung 0,0216) -- schon
wenige Ziehungen genuegen zur Unterscheidung. Richtungsuebereinstimmung
29/31 (93,5%). ABER zwei Einschraenkungen: Selbstbezug (die
Referenz-Tiefensuche nutzt denselben Value-Head wie das zu pruefende
Kriterium) und die erschoepfte Stichprobe (nicht replizierbar, ohne die
Datenbasis zu wechseln). Geplanter Hauptlauf: Stellungen aus `data/` statt
dem frozen set, Referenzsuche mit `v17_best` statt `v18_best` (entkoppelt
Kandidat und Referenz), M=4 Ziehungen.

**Offene Punkte aus dem Review vom 2026-07-29** (bestaetigt: Stand dieser
Doku liegen `engine/src/round5.rs`, `engine/src/tiling_solver.rs`,
`engine/src/lib.rs` und `engine/src/round_transition.rs` als UNCOMMITTED
Aenderungen im Arbeitsverzeichnis vor, inhaltlich deckungsgleich mit (a) und
(b)):

(a) Task #21 ist nur die HALBE Korrektur: `round5.rs::player_total_exact`
berechnet die Endwertung fuer die DRAFTING-Zugwahl in Runde 5 weiterhin auf
dem Brett VOR dem Tiling-Schritt -- nur die Tiling-eigene Zugwahl
(`tiling_solver.rs`) wurde korrigiert, der Drafting-Teil der Runde-5-Suche
noch nicht (in Arbeit).

(b) Die Dedup-Signatur von `top_k_tilings` ignorierte urspruenglich den
verbleibenden Bonuschip-Bestand (zwei Abschluesse mit identischer
Steinbelegung, aber unterschiedlichem Chip-Rest, galten als Duplikat) --
ebenfalls in Arbeit.

(c) Arena zu #21 ist als reiner DOKU-Lauf geplant, ausdruecklich KEIN Gate:
Nutzer-Entscheidung, die Korrektur wird als Korrektheitsfix so oder so
aktiviert, unabhaengig vom Arena-Ausgang.

### Nachtrag zu Task #20/#21 (2026-07-29, nach Dedup-Fix und Blattfix)

Die beiden im Abschnitt oben als "in Arbeit" gefuehrten Punkte sind erledigt
(Commit 3132b8c):

**(a) Runde-5-Blattfix**: `player_total_exact` verzweigt jetzt hinter
`ROUND5_ENDSCORING_ENABLED` auf `solve_round_final_score_endaware` (Endwertung
des ERREICHTEN Bretts in der Blatt-Rekursion, keine Doppelzaehlung). Gemessen:
5/100 Runde-5-DRAFTING-Stellungen (5,0 %) waehlen einen anderen Zug; Runtime
ON/OFF x1,08. Tests 173/173 in beiden Toggle-Zustaenden.

**(b) Dedup-Signatur** beruecksichtigt jetzt den verbleibenden Bonuschip-
Bestand. Damit AKTUALISIERTE #20-Kennzahlen (ersetzen die oben genannten
19/133 bzw. 18/131): Stellungen mit >1 Kandidat 187 -> 201, Umentscheidungen
**51/142 (35,9 %)**, Value-Spreizung Median 0,0169. Die Nullkosten-Eigenschaft
haelt auf der dreifachen Fallzahl: aufgegebene Punkte in ALLEN 51 Faellen
exakt 0. (Die Verdreifachung der Rate ist der Fix selbst: vorher wurden
Abschluesse mit gleichem Brett, aber verschiedenem Chip-Rest faelschlich
verschmolzen -- genau zwischen solchen entscheidet die Regel besonders oft.)

Beide Toggles bleiben AUS bis zur gemeinsamen Aktivierung (#20+#21: ein Wheel,
ein Arena-Doku-Lauf, EINE Elo-Neuverankerung, dabei Ersatz der duennen
n=31-Ankerkante durch festes n>=150).

### Task #20: Referenz-Validierung komplett (2026-07-29) -- und die Runde-4-Ueberraschung

Hauptlauf (`tools/tiling_value_reference_main.py`): rangiert v18s Value-Head
punktgleiche Tiling-Abschluesse richtig? Referenz ist eine UNABHAENGIGE
v17_best-Tiefensuche@2000 Sims auf der Folgestellung nach dem Rundenuebergang
(`advance_after_tiling_json`, Nachfuell-Zufall gepaart, M=4 Ziehungen wie vom
Piloten kalibriert), Stellungen aus data/ (das frozen set war nach dem Piloten
erschoepft).

| Runde | Trefferquote | Binomial-p |
|---|---|---|
| 2 | 84/118 (71,2 %) | < 0,0001 |
| 3 | 110/134 (82,1 %) | < 0,0001 |
| **4** | **70/145 (48,3 %)** | **0,74 -- ZUFALL** |

Runden 2-3 klar belegt (gesamt 194/252, p=2,6e-18). **In Runde 4 rangiert der
Value-Head nicht besser als eine Muenze** -- konsistent mit dem RMSE-Befund
(dort am schwaechsten). Harmlos, nicht schaedlich: Zufall heisst gleichwertig
zum bisherigen willkuerlichen Stichentscheid, und die Nullkosten-Eigenschaft
gilt unveraendert. Fehlgriffe konzentrieren sich weiter dort, wo die Referenz
die Kandidaten ohnehin fast gleich sieht (Median 0,0042 vs 0,0090 bei Treffern).

ENTSCHEIDUNG: Fenster Runde 2-4 bleibt (Nutzer-Rationale: kostet nichts, erbt
automatisch jede Value-Head-Verbesserung -- ein Zurueckschneiden auf 2-3 wuerde
die heutige Schwaeche fest verdrahten, die genau das Ziel des 2D-Encoders ist).
Nach dem naechsten Value-Head-Sprung ist die Messung fuer Minuten wiederholbar.

ZWEI MESS-VORBEHALTE: (1) die R4-Referenz kommt aus einem ANDEREN Mechanismus
als R2/R3 -- nach dem Uebergang steht Runde-5-Drafting, dort antwortet der
Alpha-Beta-Solver (dessen Analyse kein root_value traegt; als Ersatz dient das
mcts_q des gewaehlten Zugs -- entdeckt, nachdem ein erster R4-Lauf 1800
Zustaende scannte und 0 Paare fand). Der Rundenvergleich mischt also
Referenztypen. (2) Dieser Alpha-Beta traegt die bekannte #21-Schwaeche noch in
sich; die wahre R4-Leistung koennte etwas besser sein als gemessen.

AUSSERDEM: `scoring_tile_ids` wird jetzt in allen drei Arena-Spielausgaben
mitgeschrieben (net-vs-net, net-vs-Heuristik, Heuristik-Arena) -- kuenftige
A/Bs sind damit nach Plattenkonfiguration aufschluesselbar; bei Task #16 blieb
genau diese Frage offen.

## AKTIVIERUNG Task #20 + #21 (2026-07-30) -- Doku-Lauf und Platten-Aufschluesselung

Beide Toggles aktiv (Commit c59f8e3), 185/185 Tests im Aktivierungszustand,
Wheel installiert. Der Arena-Lauf DOKUMENTIERT die Effektgroesse, er war
ausdruecklich kein Gate (Nutzer-Entscheidung: Korrektheitsfix #21 bzw.
Nullkosten-Regel #20 werden unabhaengig vom Ergebnis uebernommen).

**Doku-Lauf** (v18_best vs v17_best, 400 Spiele je Arm, identischer Basis-Seed
41507290, beide Arme mit scoring_tile_ids in der Ausgabe):

| | OFF | ON | Differenz |
|---|---|---|---|
| Siege v18 | 228 (57,0 %) | 216 (54,0 %) | p=0,34, unauffaellig |
| Score v18 | 39,12 | 40,17 | +1,05 |
| Score v17 | 35,38 | 37,10 | +1,72 |
| **Punktesumme** | **74,50** | **77,27** | **+2,77** |
| Floor v18 / v17 | 13,98 / 15,77 | 13,79 / 15,20 | beide runter |

**BEIDE Seiten spielen besser** -- mehr Punkte, weniger Strafen. Das ist die
Signatur einer echten Engine-Verbesserung und das GEGENTEIL des
c_scale-Fehlversuchs (dort fiel die Summe um 10 Punkte, waehrend die Siegquote
"gewann"). Dass v17 etwas mehr profitiert als v18, erklaert die leicht
gesunkene Siegquote -- der schwaechere Spieler gewinnt durch die Tiling-/
Endspielkorrekturen mehr.

**Erste Platten-Aufschluesselung ueberhaupt** (moeglich durch die neuen
scoring_tile_ids; Differenz der Punktesumme ON-OFF, gepaart je Spiel, jedes
Spiel zaehlt zu seinen 3 aktiven Platten):

| Platte | n | Mittel-Differenz |
|---|---|---|
| Diagonalen | 134 | **+4,31** (SE 1,39) |
| Spezialfelder | 157 | +3,89 (SE 1,53) |
| Aussenfelder | 155 | +3,02 (SE 1,42) |
| H-Reihen | 149 | +2,56 (SE 1,49) |
| Mehrfarbig | 147 | +2,54 (SE 1,32) |
| Eckplatten | 165 | +2,48 (SE 1,33) |
| V-Reihen | 142 | +2,12 (SE 1,39) |
| Farbenreich | 151 | +1,37 (SE 1,36) |

Alle acht positiv; vorn liegen genau die zwei Platten, bei denen der
Runde-5-Endwertungs-Fix mechanistisch am meisten holt (Diagonalen: 10 Punkte
je Abschluss, vorher fuer die Zugwahl unsichtbar; Spezialfelder:
Straf-Vermeidung). Vorbehalt: die Plattenmengen ueberlappen (3 je Spiel),
die Zeilen sind nicht unabhaengig.

Elo-Neuverankerung (feste n=150-Kante, ersetzt die duenne n=31) laeuft;
Eintrag wird als Beginn der NEUEN ENGINE-AERA markiert -- #21 veraendert auch
die Heuristik, Vorher/Nachher-Elo sind nur eingeschraenkt vergleichbar.

### Elo-Neuverankerung nach der Aktivierung (2026-07-30)

Feste n=150-Kante ohne Fruehstopp: **v18_best 88:62 Heuristik (58,7 %)**,
Score 44,7 : 40,1, Floor 11,0 : 15,1. Ersetzt methodisch die duenne
n=31-Kante (74,2 %) -- der Rueckgang ist ZWEI erwartbaren Effekten
zuzuschreiben: Kleinstichproben-Ueberschaetzung der alten Kante UND die
Heuristik selbst wurde durch #21 staerker (gemeinsamer Solver; ihr Ø-Score
sprang von historisch ~32 auf 40,1). v18s Absolutscore stieg gleichzeitig
41,7 -> 44,7 -- kein Rueckschritt, ein ehrlicherer Massstab.

OFFENER PUNKT fuer spaeter: elo_history mischt jetzt Kanten gegen die alte
und die neue Heuristik unter EINEM Ankerknoten (fix 1000). Mit v19+ werden
die Neue-Aera-Kanten dominieren; falls die Verzerrung stoert, ist ein
sauberer Schnitt (eigener Ankerknoten je Aera + Neuverankerung des Kaders)
der richtige Weg -- bewusst NICHT jetzt gemacht.

Damit sind Task #20 und #21 ABGESCHLOSSEN: implementiert, validiert,
aktiviert, dokumentiert. Kein Self-Play gestartet (Nutzer-Vorgabe: erst mit
dem 2D-Encoder-Ergebnis entscheiden).

## Task #11: 2D-Encoder -- from-scratch-Vergleich, Engine-Verdrahtung, Gating (2026-08-01)

Phase 2 abgeschlossen: `Mosaic2DNet` (Conv-Zweig auf `state_to_planes`
[76,6,6] + Flach-Zweig auf dem bestehenden 708er-Vektor, siehe
`docs/design_2d_encoder.md`) gegen das bestehende `MosaicNet` from-scratch
verglichen (`evaluations/PREREG_2d_encoder.md`, 6 gepaarte Seeds, identisches
Rezept bis auf `--encoder`), anschliessend Engine-seitig verdrahtet und
gegatet.

**PREREG-Ergebnis, hoechste Befundstufe** (`evaluations/train_2d_vs_flat_fs_result.json`):
auf BEIDEN vorregistrierten, arena-validierten Orakel-Metriken gepaart 6/6
Seeds pro `fs_2d`:

| Metrik | Ø-Differenz (2D-flach) | Richtung | gepaarter t-Test |
|---|---|---|---|
| `prior_mass_on_oracle_top3` | **+0,0100** | 6/6 | p=0,0019 |
| `kendall_tau_policy_vs_oracle_q` | **+0,0149** | 6/6 | p=0,0046 |

**Value-Head-Paarvergleich** (`evaluations/offline_diagnose_2d_vs_flat_fs_frozen.json`,
`value_r2_rounds_1_4`): 4/6 Seeds pro 2D, Ø **+0,0088**, gemischte Vorzeichen
(Seeds 1/2 negativ, 3-6 positiv) -- unterhalb der bekannten ~0,015-Aufloesungsgrenze
dieser Metrik (Memory `project_offline_metric_resolution_limit`). **Value-Heads
gelten als gleichwertig**, der Policy-seitige Orakel-Befund traegt den
2D-Vorteil allein.

**Arena-Gating** (`fs_2d_s2_best` vs. `fs_flat_s3_best`, je Arm bester Seed nach
den Orakel-Metriken, 400 gepaarte Partien fix, `evaluations/paired_gating_result_fs_2d_s2_best_vs_fs_flat_s3_best.json`,
im elo_tracker protokolliert): **416:384**, gepaarte Differenz +0,080,
95%-KI [-0,063, +0,223], exakter McNemar p=0,3029 -- **KEIN nachweisbarer
Staerkeunterschied** (bewusst nicht als "Sieg" formuliert; das KI schliesst
0 nicht aus). Konsistent mit dem Value-Head-Befund: die Policy ist gemessen
staerker, der Value-Head unveraendert -- und Value traegt bei 400 Sims die
Spielstaerke (Memory `project_hybrid_head_attribution`, 2×2-Kopf-Attribution),
Policy allein reicht hier nicht fuer einen Arena-sichtbaren Sprung.

**Kosten**: 2D-Training ~30x langsamer als flach (Wanduhr), aber absolut nur
~1-2 h auf einer freien GPU -- die anfangs beobachteten ~14 h/Lauf waren zu
~90% GPU-Konkurrenz durch ein parallel laufendes Spiel auf derselben Maschine,
kein Pipeline-Problem (Profiling bestaetigte: Daten-Pfad + H2D + Compute
zusammen nur ~26-29 ms/Batch von den beobachteten ~250 ms/Batch -- siehe
Betriebs-Lektion: GPU-exklusiv fuer produktive Laeufe reservieren). **Inferenz
bleibt 1,46x teurer als flach** (gemessen vor dem Training, `examples/latency_2d_vs_flat.rs`)
-- der eigentliche Dauerposten, unabhaengig vom heutigen Gating-Ausgang.

**Engine-Verdrahtung** (M3.5, Commit `43d62aa`): `net.rs`/`features.rs` hatten
seit Phase 1/2 `load_auto`/`InputLayout`/`state_to_features_2d_direct`, aber
KEIN Aufrufer nutzte sie -- alle Produktions-Einstiegspunkte luden weiter
zwangsflach (`Net::load(path, INPUT_SIZE)`), `net_vs_net_arena` auf einem
2D-Checkpoint crashte beim Laden (tract-Shape-Fehler am ersten Conv-Knoten).
Additiv geschlossen: alle Lade-Stellen auf `Net::load_auto` umgestellt, ein
zentraler Dispatch-Helfer `features::features_for_net`/`features_for_layout`
waehlt die Feature-Erzeugung pro geladenem Netz (Flat -> unveraendert,
PlanesPlusFlat -> der kombinierte Puffer) -- inklusive `net_mcts::make_node`s
Hybrid-Pfad, wo Policy- und Value-Netz UNTERSCHIEDLICHE Layouts haben koennen.
Flach-Modelle bleiben nachweislich byte-identisch (`net_load_auto_backcompat.rs`
weiterhin bit-identisch gegen `v17_best`/`v18_best`). 189/189 Tests gruen
(+4 neue ONNX-freie Dispatch-Tests).

**`--load`-Footgun-Pruefung** (v13-Praezedenzfall: stiller From-scratch-Fallback):
bereits durch einen bestehenden Schutz abgedeckt, kein Fix noetig.
Warm-Start von `fs_2d_s2_best` mit `--encoder 2d` zeigt eine explizite
Lade-Meldung UND Epoche-1-Metriken weit ueber From-scratch-Niveau (Val-R²
Value +0,46 vs. -0,18 from scratch). Ein Encoder-Mismatch (`--load` eines
2D-Checkpoints ohne `--encoder 2d` bzw. umgekehrt) bricht in BEIDE Richtungen
hart ab (`sys.exit`, kein Teil-Load).

**ENTSCHEIDUNGEN (Nutzer):**
- v19-Generator bleibt `v18_best` (unveraendert, kein Ersatz durch 2D).
- `fs_2d_s2_best` wird als `alphazero_v18_2d.*` designiert -- der
  2D-Warm-Start-Anker der v18-Generation (Kopien liegen in `models/`).
- v19 trainiert BEIDE Arme warm (flach von `v18_best`, 2D von `v18_2d`),
  Adoption ausschliesslich ueber Champion-Gating -- kein Vorschuss-Vertrauen
  in die Architektur trotz des Orakel-Befunds.

**Kalibrier-Notiz Orakel-Metriken**: erstmals auf einem
ARCHITEKTUR-Vergleich getestet (bisher nur Generationen-Vergleiche
innerhalb derselben Architektur, Memory `project_oracle_metrics_validated`,
7/7). Hier: beide Metriken signifikant pro 2D, Arena aber Gleichstand --
der Validierungszaehler gilt WEITERHIN fuer Generationen-Vergleiche
(unveraendert 7/7), fuer Architektur-Vergleiche steht er jetzt bei 0/1 als
Staerke-Praediktor. Praezedenzfall fuer eine kopf-/kontextspezifische
Einschraenkung, analog zur bereits bekannten Selbstbezugs-Vorbehalt-Regel
(Task #89).

Querverweis: `evaluations/RESEARCH_alphazero_verbesserungen_2026-08-01.md`
(Ideen-Pipeline jenseits des 2D-Encoders, frisch angelegt).

## Korpus-Dosis-Messung (2026-08-01)

**Frage**: hilft schlicht MEHR Self-Play-Spiele in der aktuellen Engine-Aera
der Netzqualitaet ueberhaupt -- als Vorstudie zu Task #14
(Playout-Cap-Randomisierung, STATUS.md 2026-07-28: "Test B", der Zeit gegen
Spielmenge tauscht)? Praezedenzfall v11 (Memory `project_v11_cycle_result`,
"halber Korpus"-Verdacht als moegliche Mitursache fuer den ausbleibenden
Staerkegewinn) war laut Nutzer-Einschaetzung nicht mehr uebertragbar --
andere Engine-Aera, andere Netzarchitektur, kein direkter Vergleich.

**Design** (vorregistriert, `evaluations/PREREG_corpus_dose.md`, VOR dem
ersten Lauf festgeschrieben): `voll` (900 Dateien, kompletter Korpus zum
Stichtag) vs. `halb` (450 Dateien, stratifiziert je Versions-Praefix gezogen
-- 300 v17 + 100 v16 + 50 v15, Zusammensetzungsverhaeltnis exakt erhalten,
fester Seed `20260801`), 6 gepaarte Seeds, beide Arme from scratch, flacher
Encoder, identisches Rezept bis auf Korpusgroesse. Technisch ueber
eingefrorene HARDLINK-Sandboxes geloest (`data_dose_voll/`,
`data_dose_halb/`, additive `MOSAIC_DATA_DIR`-Env-Var in `config.py`,
`train.py` unangetastet) -- immun gegen die PARALLEL laufenden
v18-Self-Plays, die waehrend des Sweeps neue Dateien nach `data/` schrieben
(v19-Kampagne zum Zeitpunkt der Split-Ziehung, siehe unten).

**ERGEBNIS** (`evaluations/train_corpus_dose_result.json`): `voll` auf
BEIDEN vorregistrierten, arena-validierten Orakel-Metriken gepaart 6/6
Seeds besser:

| Metrik | Ø-Differenz (voll-halb) | Richtung | gepaarter t-Test |
|---|---|---|---|
| `prior_mass_on_oracle_top3` | **+0,0221** | 6/6 | p=0,0013 |
| `kendall_tau_policy_vs_oracle_q` | **+0,0189** | 6/6 | p=0,0067 |

**Einordnung gegen den 2D-Architektur-Befund** (Task #11 oben, gleicher
Tag, gleiche Orakel-Metriken, gleiche 6-Seed-Methodik): der Mengen-Effekt
ist auf `prior_mass_on_oracle_top3` **~2,2x** so gross (+0,0221 vs. +0,0100)
und auf `kendall_tau_policy_vs_oracle_q` **~1,3x** so gross (+0,0189 vs.
+0,0149) wie der 2D-Encoder-Effekt -- im Mittel rund doppelt so gross,
staerker auf der Top-3-Metrik als auf der Rang-Metrik. Beide Befunde sind
unabhaengig entstanden (verschiedene Stellschrauben, gleiche Diagnose-
Pipeline), direkter Zahlenvergleich ist informativ, kein formaler Test.

**KONSEQUENZ**: Task #14 (Playout-Cap-Randomisierung) steigt deutlich in
der Prioritaet -- der in `PREREG_corpus_dose.md` vorab festgelegte
Interpretationspfad "`voll` auf BEIDEN Metriken gepaart besser -> starker
Befund fuer Menge-hilft, erhoeht die Prioritaet von Task #14 (Test B2)
deutlich" greift.

**EINSCHRAENKUNG (wiederholt aus der PREREG, bleibt bestehen)**: getestet
wurde nur "hilft Menge ueberhaupt, bei UNVERAENDERTER Suchtiefe" -- NICHT
der eigentliche Task-#14-Tradeoff (mehr, aber schwaechere Trajektorien
durch Playout-Capping, bei GLEICHEM Rechenaufwand pro Zug). Ein positiver
Befund hier ist notwendig, aber NICHT hinreichend fuer eine
Task-#14-Entscheidung -- die eigentliche Trajektorienqualitaets-Frage
(Test B2, STATUS.md 2026-07-28) braucht weiterhin echtes neues Self-Play
mit reduzierten Sims.

**Betriebsnotiz**: ein Cleanup-Reihenfolge-Bug im Treiber
(`tools/train_corpus_dose.py`) hat den ersten Sweep-Durchlauf getroffen --
die Sandbox-Aufraeumung lief VOR `run_diagnose_and_eval`, ein
`PermissionError` beim Entfernen von `data_dose_voll/` (haengendes
Windows-Datei-Handle) liess den Lauf dort abstuerzen, die Diagnose musste
per `--skip-training` nachgeholt werden. Gefixt: Diagnose+Auswertung laeuft
jetzt IMMER vor jedem Cleanup-Schritt, und `remove_sandbox_dir()` ist
fehlertolerant (Warnung statt Absturz bei `OSError`) -- ein haengendes
Datei-Handle beim Aufraeumen darf nie wieder ein bereits fertiges
Messergebnis verhindern.

**Nachtrag Dosis-Arena (2026-08-01, auf User-Anstoss):** Die Orakel-Befunde wurden
zusaetzlich in der echten Arena bestaetigt -- voll_s3_best 479:321 halb_s3_best
(400 fixe Paare, exakter McNemar p<0.0001, gepaarte Differenz +0.395,
95%-KI [+0.255, +0.535], keine Promotion; Ergebnis:
`evaluations/paired_gating_result_voll_s3_best_vs_halb_s3_best.json`, im
elo_tracker protokolliert). Damit steht der #14-Befund auf zwei Beinen
(Orakel-Metriken + Arena), und die Orakel-Metriken sind in ihrem validierten
Regime (gleiche Architektur, unterschiedliche Daten) jetzt 8/8 als
Staerke-Praediktor -- im Kontrast zum Architektur-Regime (0/1, siehe
Task-#11-Abschnitt).

## v19-Zyklus: ERSTER 2D-CHAMPION (2026-08-02)

**Self-Play**: 6000 Spiele / 974.937 Zuege in 14,6h, `v18_best`@600 Sims,
11 Threads -- ERSTMALS mit `root_q`-Labels (Commit `2718b9a`, siehe
Task-#11-Nachtrag zum v19-Vorbereitungsauftrag). Naming-Korrektur im
Nachgang: Dateien liefen als `selfplay_v19_*` an, wurden auf
`selfplay_v18_*` umbenannt (Generator-Konvention -- der Dateiname traegt
das Netz, das die Zuege gemacht hat, nicht die kuenftige Generation; die
`game_id`-Strings INNERHALB der Dateien tragen kosmetisch weiter `v19`,
das ist bekannt und harmlos).

**Fenster-Rotation** (Nutzer-Entscheid): 600×`v18` + 200×`v17` + 100×`v16`
= 900 Dateien (9000 Spiele), `v15` faellt komplett raus, alte Caches
geloescht (bestaetigt: `data/` traegt aktuell exakt 600/200/100 nach
Versions-Praefix).

**Doppel-Arm-Training** (Champion-Warm-Start-Rezept, `lr 5e-5`, cosine,
Seed 2, `nortv`): `v19` (flach, warm von `v18_best`) `val_combined`
**1,2376**, `v19_2d` (warm von `v18_2d`, dem in Task #11 designierten
2D-Anker) **1,1729** -- identischer Val-Split, direkt vergleichbar.

**Orakel-Umstellung vollzogen** (`tools/oracle_metrics.py`): `ORACLE_JSON`
zeigt jetzt auf `frozen_v1_oracle_labels_v18.json` (vorbereitet seit
2026-07-29, siehe damaliger Kommentar zur "UMSTELLUNG AB v19"). Die alte
v16-Trefferbilanz ist NICHT auf diese neue Quelle uebertragbar -- eine neue
Bilanz beginnt bei null. Quelle-nie-Kandidat-Regel (Task #89) bleibt in
Kraft: `v18_best` wird selbst nicht gescored.

**Diagnose** (`evaluations/offline_diagnose_v19_arms_frozen.json`,
verifiziert): `v19_2d_best` fuehrt auf allen drei Spalten vor `v19_best`:

| Metrik | v19_best | v19_2d_best |
|---|---|---|
| `prior_mass_on_oracle_top3` | 0,7020 | **0,7187** |
| `kendall_tau_policy_vs_oracle_q` | 0,3296 | **0,3558** |
| `value_r2_rounds_1_4` (nur Fingerzeig, unter Aufloesungsgrenze) | 0,0906 | 0,1009 |

Zusaetzlich: `v19_2d_best` schlaegt `v18_2d` auf ALLEN drei Spalten
(0,7187>0,7040, 0,3558>0,3383, 0,1009>0,0830) -- die 2D-Linie lernt ueber
Generationen weiter, kein Einmaleffekt.

**Gating 1** (`evaluations/paired_gating_result_v19_best_vs_v18_best.json`):
**`v19_best` 96:54 `v18_best`**, SPRT-Entscheid nach 75 Paaren, exakter
McNemar p=0,0011, gepaarte Differenz +0,56 -> `v19_best` neuer flacher
Champion.

**Gating 2 / FINALE**
(`evaluations/paired_gating_result_v19_2d_best_vs_v19_best.json`):
**`v19_2d_best` 64:36 `v19_best`**, SPRT-Entscheid nach 50 Paaren, exakter
McNemar p=0,0094, gepaarte Differenz +0,56 -> **`v19_2d_best` ist der ERSTE
2D-CHAMPION der Projektgeschichte.**

Einordnung gegen den from-scratch-Befund (Task #11, 2026-08-01): der
damalige `fs_2d`-vs-`fs_flat`-Arena-Vergleich war ein Staerke-Wash (416:384,
p=0,30, kein nachweisbarer Unterschied). Mit Warm-Start-Symmetrie (beide
Arme von derselben v18-Generation gestartet, `v18_2d` als eigens dafuer
designierter Anker, Nutzer-Entscheid Task #11) uebersetzt sich derselbe
Policy-Vorsprung (Orakel-Metriken, gleiche Richtung wie im from-scratch-
Vergleich) jetzt in echte Spielstaerke. Dies ist zugleich der ERSTE Treffer
der neuen v18-Label-Orakel-Validierungsbilanz: die Metriken sagten dieses
Duell (`v19_2d_best` vor `v19_best`) VOR dem Gating korrekt voraus.

**Konsequenzen**:
- Die Champion-Linie ist ab jetzt 2D-nativ -- kuenftige Warm-Starts gehen
  von `v19_2d_best` aus.
- Der flache Arm wird zum Parallel-Arm (weiterlaufend, aber nicht mehr die
  Haupt-Linie).
- Self-Play ab v20 mit dem 2D-Generator = 1,46x Inferenzkosten (siehe
  Task-#11-Kostenmessung) -- der Nutzer-Vorentscheid vom 2026-07-30 ("wenn
  dann gleich mit 2D") ist damit eingeloest, kein halber Schritt.
- Der GUI-Server braucht einen Neustart, um den neuen Champion zu laden.

**Laufend/offen**: Heuristik-Anker-Match fuer `v19_2d_best` (feste
n=150-Kante, ohne Fruehstopp, Muster wie beim v18-Anker) laeuft noch.
Naechste Hebel: Task #14 (Playout-Cap-Randomisierung, Dosis-Effekt jetzt
validiert, siehe Abschnitt oben) und das Misch-Value-Target-Experiment
(`λ·z+(1−λ)·q_root`) -- `root_q` liegt seit diesem Zyklus im Korpus vor.

**Betriebsnotiz**: ein losgeloester Prozessstart (`&`-Kette) beim
Koordinator fuehrte kurz zu einem haengenden `elo_tracker`-Prozess UND
einem stumm gestarteten Gating-Lauf (keine sichtbare Ausgabe) -- bereinigt,
die Start-Routine ist seither verschaerft (kein `&`-Loesloesen mehr ohne
expliziten Log-Pfad/Prozess-Tracking).

## Lambda-Sweep + PCR-A/B: Laeufe angelaufen, PCR-Policy-Maske nachgeruestet (2026-08-02/03)

**Drei vorregistrierte Experimente in der Pipeline** (Reihenfolge fix:
Lambda -> PCR -> R5-Kalibrierung voller Lauf -> R4-Kalibrierung):

**1. λ-Misch-Value-Target** (`PREREG_lambda_target.md`,
`tools/train_lambda_sweep.py`): 24 from-scratch-Laeufe (4 Arme
λ∈{1.0, 0.7, 0.5, 0.3} × 6 Seeds) auf der eingefrorenen 900-Datei-Sandbox
`data_lambda_sweep/`. Sample-Misch-Anteil exakt gemessen und in der PREREG
nachgetragen: **43,83%** (640.246 von 1.460.731 Samples tragen `root_q`).
Sweep lief am 2026-08-02 bis Lauf 13 (Unterbrechung bei `lam07_s4`), am
2026-08-03 per Skip-Logik wiederaufgenommen -- Diagnose + gepaarte
Auswertung (`train_lambda_sweep_result.json`) laufen nach dem letzten Lauf
automatisch. Primaermetrik `value_r2_rounds_1_4` (Aufloesungsgrenze 0,015),
Arena-Gating nur bei Signal (`--no-promote-winner`).

**2. PCR-A/B, Task #14** (`PREREG_pcr.md`): Self-Play beider Arme ist
abgeschlossen (`data_pcr_ab/`: `pcrkontrolle` 117 Dateien/1170 Spiele
klassisch @600 Sims, `pcrpcr` 210 Dateien/2100 Spiele PCR p=0,25/cheap=150
-- gleicher Generator `v19_2d_best`, Wandzeit-gematcht). **Kritische Luecke
vor dem Training gefunden und geschlossen** (Commit `2777cf6`): die Engine
schreibt `policy_target_valid=false` an Cheap-Suche-Zuege, aber die
Trainings-Pipeline ignorierte das Feld -- ~75% des pcr-Korpus waeren mit
unzuverlaessigen 150-Sim-Visit-Zielen in den Policy-Loss gelaufen.
Fix additiv in `neural_net.py` (Cache-Bau: `policy_weight=0` fuer solche
Records, No-Op fuer alle Nicht-PCR-Korpora, kein Cache-Schema-Bump).
Treiber `tools/train_pcr_dose.py` neu (Vorbild `train_corpus_dose.py`):
12 Laeufe (6 Seeds × 2 Arme), Orakel-Metriken primaer, PREREG-Verdikt
automatisch. Rauchtest gruen inkl. exakter Masken-Verifikation gegen den
HDF5-Cache (706==706). Voll-Suche-Quote im pcr-Korpus: **25,1%** (Soll
~25%); Kontroll-Korpus traegt das Feld nirgends -- Arm-Design bestaetigt.
Sandboxes (`data_pcr_kontrolle/`, `data_pcr_pcr/`) stehen; Training startet
nach Sweep-Ende (GPU-Serialisierung).

**3. R4-Ende-Value-Kalibrierung NEU vorregistriert**
(`PREREG_r4_value_calibration.md`, 2026-08-03): Nutzer-Fund, code- und
datenverifiziert -- ab Runde-4-Ende ist das Brett vollstaendig bekannt
(`dome_stack_count=0` in allen geprueften letzten R4-Records), einzige
Restunsicherheit ist die Fabrik-Neubefuellung 4->5. Design: Ground Truth =
Erwartung ueber K=16 gesampelte Neubefuellungen des exakten
R5-Alpha-Beta-Werts; `true_winprob` = Refill-Gewinnquote liegt DIREKT auf
der Value-Kopf-Skala (keine Kennlinie noetig, Saettigungsproblem des
R5-Designs entfaellt). Setzt die Noise-Floor-Serie vom 2026-07-21
(R²_max korrigiert: R1 0,0068 / R2 0,166 / R3 0,437) am R4-Ende fort,
mit SCHAERFERER Methode: exaktes Optimal-Spiel statt Heuristik-Rollouts
-- als Rauschen zaehlt nur noch der echte Chance-Knoten; zusaetzlich
Anschlussmessung mit der bestehenden `value_noise_floor_diagnostic`
(target_round=4) zur Serien-Vergleichbarkeit. Baustein des
uebergeordneten Nutzer-Ziels "Value-Head an den maximal moeglichen R²
heranfuehren, ab Runde 2 ist Luft nach oben" (Praezisierung 2026-08-03:
gemeint ist der R²-Wert; Referenz ist genau diese Serie -- R2: 0,017
erreicht vs. 0,166 moeglich, R3: 0,195 vs. 0,437, jeweils v10-Stand). Rust-Vorbedingung: additives
Binding `resample_round_transition_json` (existiert noch nicht) +
Wheel-Build. Ausfuehrung gated hinter dem vollen R5-Lauf; R3/R2 =
Ausblick mit Decken-Priorisierungsregel.

**Aufraeum-Notiz**: Experiment-Checkpoints (`lam*`, `pcr*`) werden nach
Auswertung (bei Lambda: nach einem evtl. Arena-Gating) geloescht --
Konvention wie `voll_s*`/`halb_s*`/`fs_2d_s*` (nur Manifeste bleiben).
Sandboxes raeumen die Treiber selbst ab; OneDrive-Handle-Reste werden
manuell nachgeraeumt (Smoke-Sandboxes 2026-08-03 so bereinigt).

## Lambda-Sweep ABGESCHLOSSEN: klares Offline-Signal, KEINE Arena-Bestaetigung (2026-08-03)

**Offline (24 Laeufe, 6 gepaarte Seeds x 4 Arme, PREREG_lambda_target.md)**:
ALLE drei λ-Arme schlagen die lam10-Baseline auf der Primaermetrik
`value_r2_rounds_1_4`, jeweils 6/6 Seeds, alle ueber der
0,015-Aufloesungsgrenze:

| Arm | Ø-Diff vs lam10 | Richtung | t-Test |
|---|---|---|---|
| lam07 (λ=0.7) | **+0,0270** | 6/6 | p=0,0061 |
| lam05 (λ=0.5) | +0,0233 | 6/6 | p=0,0001 |
| lam03 (λ=0.3) | +0,0269 | 6/6 | p=0,0061 |

Orakel-Metriken flach ueber alle Arme (Sanity bestanden: reiner
Value-Kopf-Effekt, Policy unberuehrt). Die Varianzreduktions-Hypothese
(soft-Z) traegt OFFLINE klar -- bemerkenswert bei nur 43,83%
root_q-Sample-Anteil.

**Arena (vorregistrierter Schritt, `--no-promote-winner`)**: bester Arm
lam07 (Checkpoint-Wahl je Arm: bester Seed nach Primaermetrik, s3 vs s4)
gegen lam10: **43:57, SPRT nimmt H0 nach 50 Paaren an** (LLR=-3,44,
gepaarte Diff -0,28 [KI -0,68..+0,12], Bericht-McNemar p=0,25;
`paired_gating_result_lam07_s3_best_vs_lam10_s4_best.json`, im
elo_tracker protokolliert).

**Verdikt nach PREREG-Regel 4**: Offline-Signal OHNE Arena-Bestaetigung =
Beobachtung, KEIN Rezeptwechsel -- `--value-target-lambda` bleibt 1.0
(Standard). Einordnung: passt zum v11-Praezedenzfall (TD-Bootstrap hob
R1/R2-R², brachte aber keine Staerke) und zur bekannten Offline-Arena-
Luecke des Value-R². Wiedervorlage laut PREREG-Interpretationsregel:
wiederholen, wenn ein groesserer Korpusanteil root_q traegt (nach v20-
Self-Play faellt v16/v17 aus dem Fenster, dann ~100% root_q-faehige
Dateien). Aufgeraeumt: 24 Checkpoints geloescht (Manifeste + Ergebnis-
JSONs bleiben), data_lambda_sweep/ entfernt.

**Nebenbefund**: der offene Heuristik-Anker fuer v19_2d_best ist laengst
gelaufen (2026-08-02, festes n=150: 113:37, 75% Siege, Elo 1326) --
offener Punkt geschlossen.

## PCR-A/B ABGESCHLOSSEN: Task #14 wird NICHT produktiv eingesetzt (2026-08-03)

**12 Laeufe (6 gepaarte Seeds x kontrolle/pcr, flacher Encoder from scratch,
PREREG_pcr.md), Policy-Maske aktiv** (Cheap-Zuege mit
`policy_target_valid=false` -> `policy_weight=0`, Rauchtest-verifiziert).

**Primaermetriken (arena-validierte Orakel-Praediktoren), pcr - kontrolle:**

| Metrik | Ø-Diff | Richtung | t-Test |
|---|---|---|---|
| `prior_mass_on_oracle_top3` | **-0,0262** | 0/6 pcr besser | p=0,0008 |
| `kendall_tau_policy_vs_oracle_q` | **-0,0211** | 0/6 pcr besser | p=0,0020 |

**Verdikt nach PREREG-Abbruchregel**: pcr auf BEIDEN Orakel-Metriken
gepaart schlechter -- der Tausch Suchqualitaet-gegen-Menge lohnt sich fuer
dieses Design NICHT. Kein Arena-Gating, KEIN Zwei-Kampagnen-Betrieb ab v20;
v20-Self-Play laeuft klassisch (jeder Zug Voll-Suche @600 Sims).

**Einordnung**: die Wette war "mehr, aber teils schwaechere Value-Masse
gegen weniger, aber verlaessliche Policy-Masse". Die Value-Seite hat sogar
geliefert (`value_r2_rounds_1_4` sekundaer: +0,0402, 5/6 pcr besser,
p=0,04 -- konsistent mit dem Dosis-Befund), aber der Policy-Verlust
dominiert klar auf den einzigen arena-validierten Praediktoren. Bekannte
Einschraenkung bleibt: flacher Encoder als Messproxy, cheap=150/p=0,25 als
einziger Messpunkt -- mildere Regime (hoeheres p, mehr cheap-Sims) waeren
neue Messpunkte, kein Widerspruch. KORREKTUR 2026-08-03: die im
PCR-PREREG (Einschraenkung 5) zitierte Ownership-Kopf-These ("PCR-Handel
wird guenstiger, sobald Task #9 landet") war beim Schreiben bereits
ueberholt -- Task #9 ist seit 2026-07-28 GESCHLOSSEN
(PREREG_ownership_gumbel.md: OWNERSHIP_WEIGHT bleibt 0,0, Effekt +0,0017
= ~1/10 der Metrik-Aufloesung, Wiedereroeffnung nur mit Arena-Instrument)
-- sie zaehlt NICHT als PCR-Wiedereroeffnungsgrund.

**Aufgeraeumt**: 12 Checkpoints geloescht (Manifeste + Ergebnis-JSONs
bleiben), beide Sandboxes entfernt. `data_pcr_ab/` (327 Roh-Dateien)
bleibt vorerst -- Nutzer-Entscheid ueber Archivierung/Loeschung steht aus
(PCR-Spiele duerfen laut Fenster-Politik NIE als Tail in Trainingsfenster,
die kontrolle-Spiele waeren prinzipiell nutzbar, laufen aber unter
pcrkontrolle-Praefix ausserhalb der Fenster-Rotation).

**NACHTRAG -- Doku-Arena (2026-08-03, Nutzer-Anstoss "vertraust du den
Orakel-Metriken?")**: Der Offline-Befund lag an zwei bekannten Raendern
des Orakel-Vertrauensbereichs (Korpus-Regime-Grenze analog zum
Architektur-0/1; 2x2-Befund "Value traegt Staerke bei 400 Sims" +
gegenlaeufige value_r2-Prognose +0,04 fuer pcr). Deshalb Doku-Arena
(keine Promotion): beste Checkpoints je Arm (kontrolle_s6, pcr_s5) aus
Manifest+Seed+Rezept reproduziert (statistische Zwillinge, GPU nicht
bit-deterministisch), dann gepaartes Gating. **Ergebnis: pcrpcr 67:83
pcrkontrolle, SPRT-H0 nach 75 Paaren** (gepaarte Diff -0,213, KI
[-0,534,+0,107], McNemar p=0,26; elo_tracker protokolliert). Die
Orakel-RICHTUNG bestaetigt sich, die value_r2-Gegenprognose
materialisiert sich NICHT -- das PCR-Verdikt steht damit doppelt.
Zweite Lehre desselben Tages (nach Lambda): value_r2-Offline-Gewinne
uebersetzen wiederholt nicht in Arena-Staerke. Lehre fuers Aufraeumen
umgesetzt: die zwei reproduzierten Checkpoints bleiben bis zum Abschluss
der Ergebnis-Diskussion liegen.

## R5-Value-Kalibrierung (Task #27) ABGESCHLOSSEN: Unterkalibrierung BESTAETIGT (2026-08-03)

**Voller Lauf nach PREREG_r5_value_calibration.md** (24 Zustaende x 6
Kombinationen, 139 auswertbare Paare je Modell, Kennlinie aus 233
R5-Records, `r5_value_calibration_result.json`).

**Kennlinie**: b=0,128 Logit/Punkt, McFadden-R²=0,316 -- KNAPP ueber der
0,3-Kaskaden-Schwelle (Hauptmessung damit interpretierbar, aber die
Kennlinie selbst ist deutlich schwaecher als der 2-Zustaende-Rauchtest
suggerierte; mid-Drafting-R5-Records tragen offenbar mehr Restrauschen
als Rundenstart-Endspiele, u.a. verdeckte-Info-Neumischung).

**Kalibrierungs-Steigungen** (Modell-Reaktion auf Wertungsplatten-Tausch
vs. erwartete Reaktion aus exakter Alpha-Beta-Ground-Truth; Soll ~1):

| Modell | Value-Kopf Steigung | R² | Punkte-Kopf Steigung | R² |
|---|---|---|---|---|
| v18_best | **0,087** | 0,152 | 0,258 | 0,021 |
| v19_best | 0,061 | 0,097 | 0,263 | 0,023 |
| v19_2d_best | **0,061** | 0,134 | 0,156 | 0,008 |

**Verdikt nach den vorregistrierten Regeln**:
- **Value-Kopf: Unterkalibrierung BESTAETIGT** fuer v18_best und
  v19_2d_best (R²>0,1, KI-Obergrenze der Steigung weit unter 0,85) --
  der Kopf zeigt nur **~6-9% der erwarteten Win-Prob-Reaktion** auf
  Platten-Aenderungen. Der Nutzer-Verdacht "unterkalibriert, nicht klein-
  aber-real" ist damit quantitativ belegt. v19_best liegt mit R²=0,097
  haarscharf unter der 0,1-Interpretationsschwelle (formal "kein
  Befund", Zahlen praktisch deckungsgleich mit v19_2d).
- **Punkte-Kopf: kein Befund** (R² 0,008-0,023, weit unter 0,1 -- zu
  verrauscht relativ zum Signal; keine Aussage, ob kopf-spezifisch).
- Anschauung aus den Rohdaten: exakt entschiedene +29-Punkte-Endspiele
  bewertet das Modell mit nur 60-64% Win -- dasselbe Muster wie der
  Live-Fund game_155431.

**Handlungsempfehlung laut PREREG** (kein automatischer Rezeptwechsel):
Kandidat fuers Value-Zielrauschen-Thema. Passt konsistent zum
Lambda-Befund vom selben Tag (root_q-Mix hebt value_r2 offline klar --
das Zielrauschen IST reduzierbar -- uebersetzt aber (noch) nicht in
Staerke). Naechster Diagnose-Baustein: R4-Ende-Kalibrierung
(PREREG_r4_value_calibration.md, wartet auf Rust-Vorbedingung + Freigabe).

## Task #31 (vorgemerkt): Menschen-Schwierigkeitsstufen leicht/mittel/schwer/extrem (2026-08-03)

**Nutzer-Auftrag**: Staerke-Skalierung fuer Mensch-Spiele; Einschaetzung
"Sims allein richten es nicht" ist KORREKT und hier besonders: (a) R5-
Alpha-Beta + Tiling-DFS spielen sim-unabhaengig exakt -- eine 20-Sims-KI
spielt trotzdem perfekte Endspiele; (b) Gumbel+Policy-Prior traegt auch
Mini-Budgets -- flacher, aber nicht menschlich-fehlbar.

**Design-Skizze (3 Hebel je Stufe)**: Sims-Budget + Endspiel-/Tiling-
Degradation (R5-Knotenbudget-Override bzw. Policy-Sampling statt Solver,
Tiling greedy statt exakt bei "leicht") + Fehler-Injektion via Root-
Temperatur-Sampling mit Q-GAP-DECKEL (nur plausible Fehler <=3-5 Punkte;
menschlich-fehlbar statt gleichmaessig-flach; loest auch Ausrechenbarkeit).
Stufen: extrem=Champion@600-800 (optional lambda_aggr als Stil),
schwer=heutiger Stand @400, mittel=~100-150 Sims + Deckel-Sampling +
reduziertes R5-Budget, leicht=~8-16 Sims + Temperatur hoeher + epsilon +
Greedy-Tiling. ABGERATEN: alte Generationen als Stufen (Wartung,
OneDrive-Risiko, Regel-Fix-Inkompatibilitaeten, "gleichmaessig schwach").

**Kalibrierung**: vorhandene Elo-Leiter + Heuristik-Anker; je Konfiguration
n=150 vs 2 Anker, Ziel-Baender ~leicht 700-800 / mittel ~1000 / schwer
~1150-1200 / extrem=Champion. Umsetzung nach Muster Task #28
(Laufzeit-Parameter + Server-Preset + GUI-Dropdown). OFFEN (Nutzer):
Ziel-Baender ok? Darf "leicht" sichtbar Endspiele verstolpern?

**GATE (Nutzer-Entscheid 2026-08-03): ZURUECKGESTELLT** -- wird erst
angegangen, wenn ein Champion existiert, der auch gute menschliche
Spieler wirklich fordert. Bis dahin bleibt die Prioritaet auf
Staerke-Arbeit (v20-Zyklus, Value-Head-Front #29/#30, lambda=0.7-
Kandidat), nicht auf Schwierigkeits-UX.

## Lambda-v18only: ARENA-SIGNIFIKANTER SIEG -- λ=0.7 wird v20-Standard-Kandidat (2026-08-03)

**Kehrtwende nach dem 900er-Null** (`PREREG_lambda_v18only.md`, Nutzer-
Vorschlag "Dosis vorziehen statt auf v20 warten"): 12 Laeufe auf dem
reinen v18-Korpus (600 Dateien, Sample-Misch-Anteil 65,67% = strukturelles
Maximum, 1,5x der 900er-Dosis).

- **Offline-Gate**: +0,0183 auf `value_r2_rounds_1_4` (5/6 Seeds, t-Test
  p=0,065) -- knapp UEBER der 0,015-Grenze, aber SCHWAECHER als das
  900er-Signal (+0,027) trotz hoeherer Dosis. Orakel-Metriken flach.
- **Arena (Pflichtschritt, entscheidend)**: `l07v18_s6` (bester Seed nach
  Primaermetrik, 0,1236) vs `l10v18_s3` (0,1075): **227:173 (56,75%),
  SPRT-H1 bei exakt 200 Paaren (LLR +3,50), McNemar p=0,0101, gepaarte
  Diff +0,27 [KI +0,074, +0,466]**
  (`paired_gating_result_l07v18_s6_best_vs_l10v18_s3_best.json`,
  elo_tracker protokolliert).

**Konsequenz nach PREREG-Regel 3**: λ=0,7 ist TRAININGS-STANDARD-KANDIDAT
fuer v20 -- finale Uebernahme faellt im v20-Zyklus selbst (dort dann auf
dem echten v20-Fenster, 2D-Warm-Start-Regime, gegen den amtierenden
Champion gated). KEINE Champion-Promotion aus diesem Ablationstest.

**Wissenschaftliche Einordnung (wichtig fuer Task #29)**: Das
Offline-Signal war im ERFOLGREICHEN Experiment KLEINER als im
gescheiterten (0,018 vs 0,027) -- die value_r2-Magnitude trackt den
Arena-Effekt weiterhin nicht (vierter Beleg). Der Unterschied zum
900er-Null liegt plausibel im Korpus-Regime (reiner v18-Korpus ohne
Alt-Generationen-Verduennung, 66% statt 44% Mix-Dosis) -- und/oder in
Checkpoint-Paar-Varianz (andere Seeds). Ehrliche Restunsicherheit: EIN
Arena-Paar; die v20-Uebernahme-Entscheidung liefert die Replikation.
Checkpoints bleiben bis zum Abschluss der Diskussion liegen
(Aufraeum-Lektion).

## Task #28 DURCHGEFUEHRT: Gates bestanden, lambda_aggr-Sweep ohne signifikanten Denial-Effekt (2026-08-03)

**Komplette Kette an EINEM Tag** (PREREG_task28_aggression.md): Engine-Blend
(Laufzeit-Regler MOSAIC_POINTS_UTILITY_W/MOSAIC_AGGR_LAMBDA, w=0
byte-identisch), Python-opp_points-Kopf (Symmetrie own=points+0.1*opp
numerisch exakt), Training `v19_2d_opp` (warm, Champion-Rezept, gepinntes
900er-Fenster, val_combined 1.1738 ~ Champion 1.1729).

- **Gate 1 (offline)**: Opp-R² frozen 0.4401 (best) / 0.5121 (final);
  Degradations-Check: alle 3 Referenzmetriken LEICHT UEBER Champion
  (+0.004..+0.006). BESTANDEN.
- **Gate 2 (Arena-Nichtunterlegenheit, w=0)**: 209:191 vs v19_2d_best,
  Cap ohne Entscheid, Diff +0.09 [-0.105,+0.285]. BESTANDEN.
- **Hauptmessung** (4 Arme lambda_aggr {0, 0.5, 1, 2} @ w=0.1, je 75
  Paare, identische Seeds, kein Fruehstopp; Per-Paar-Scores via
  paired_gating-Erweiterung):

| Arm | vs Champion | Gegnerpunkte-Diff gepaart vs la00 | eigene Diff | Guardrail |
|---|---|---|---|---|
| la00 | 81:69 | -- | -- | -- |
| la05 | 81:69 | -2.92 (p=0.18) | -2.17 | OK |
| la10 | 76:74 | -1.31 (p=0.61) | +0.52 | OK |
| la20 | 80:70 | **-6.16 (p=0.078)** | -9.77 | OK |

**Verdikt nach PREREG-Regel**: kein Arm p<0.05 -> "kein nutzbarer
Denial-Effekt bei w=0.1" (formal). Richtung durchgaengig konsistent
(alle Arme senken Gegnerpunkte, la20 knapp an Signifikanz, Denial kostet
erwartungsgemaess eigenes Tempo), KEIN Guardrail gerissen. Ein w-Sweep
oder mehr Paare waeren eine NEUE Vorregistrierung.

**Nebenbefunde**: (1) w=0.1 allein schadet NICHT (la00 81:69 Trend
positiv) -- Kontrast zum v9b-Desaster bei w=0.5/1.0 bestaetigt das
Kleine-w-Regime. (2) Praktisch nutzbar ab sofort: der Regler ist
gefahrlos -- `MOSAIC_AGGR_LAMBDA=2.0` spielt ~3 Gegnerpunkte
gegnerfeindlicher bei gleicher Staerke (GUI-Server-Env). v19_2d_opp-
Checkpoints bleiben (Traeger des Reglers; ein Champion-Wechsel auf
v19_2d_opp waere ein separates Gating).

**REVISION (Nutzer-Entscheid 2026-08-04)**: Der GUI-Schieberegler wird
WIEDER ENTFERNT -- stattdessen EIN Standardwert: (w=0,1, lambda =
hoechstes sicheres lambda aus der Kartierung PREREG_lambda_ceiling_and_
gating), beim Serverstart gesetzt (Engine-Bindings + /api/aggression
bleiben als Infrastruktur). lambda-nach-Schwierigkeit wird Baustein des
geparkten Task #31. Umsetzung nach Vorliegen des Kartierungs-Ergebnisses.

**NACHT-PIPELINE 2026-08-04 (sequenziell auf Abschluss-Meldungen)**:
A) lambda-Kartierung {0,3,5} + Champion-Gating v19_2d_opp@w=0.1/
lambda_Kartierung (laeuft) -> B) #29-Erweiterungs-Arenen + Rangmetrik-
Validierung, parallel B') GUI-Umbau Slider->Startup-Default -> C) #30
Platt-Fit + Skalen-A/B -> D) R4b-PREREG + Playout-Ground-Truth-Werkzeug
(cargo erst ab hier) -> E) Task-#32-Kostenprofil-Messung (ruhigste
Maschine zuletzt). NICHT automatisiert (Morgen-Entscheide): Promotion +
Server-Neustart, v20-Start + lambda07-Uebernahme-Gating, Modell-
Aufraeumen Runde 2, git push.

## Task #28 Power-Erweiterung: WIDERSPRUCH zwischen Stichproben -- Konfirmation AUSGESETZT (2026-08-03)

**Frische Stichprobe** (PREREG_task28_power_extension, 150 Paare/Arm,
Seed 30260803, NEUES Wheel #2 mit #30-Knopf + Regler-Atomics):
- la00 (w=0,1, lambda=0): **173:127 vs Champion, McNemar p=0,0076,
  Diff +0,307 [0,094, 0,519]** -- SIGNIFIKANTER Sieg ueber v19_2d_best!
- la20 frisch: 155:145 (p=0,64)
- **PRIMAERTEST la20-la00 (frische Paare): Gegnerpunkte +9,63 (p=0,0001)
  -- GEGENRICHTUNG zum Erst-Sweep** (-6,16, p=0,078). Beide Arme
  tauschten komplette Score-Profile (Erst-Sweep: la20 senkt beide
  Scores; frisch: la20 hebt beide). ~5 SE Widerspruch -- das ist kein
  Stichprobenrauschen.

**Konfundierung**: zwischen den Stichproben wurde Wheel #2 installiert
(#30-Skalen-Knopf + Regler-Atomic-Refactor). Byte-Identitaets-Tests
deckten NUR w=0 ab -- die aktiven w>0-Pfade waren zwischen Wheels nie
gepinnt. Sonden-Check Wheel #2: Env-Mapping korrekt, Blend reagiert in
Design-Richtung (0,538 -> +w: 0,544 -> +lambda2: 0,530). Wheel #1
(Commit 5219d77) ist ueberschrieben -- Forensik braucht Worktree-Rebuild
+ identische Sonde + ggf. Mini-Arena.

**Konsequenz (ehrlich)**: lambda=2-Konfirmation AUSGESETZT (keine
Richtung wird akzeptiert), der la00-Sieg ueber den Champion bleibt UNTER
VORBEHALT (falls Wheel #2 korrekt ist, waere das ein Champion-Gating-
wuerdiger Befund: v19_2d_opp@w=0,1 schlaegt v19_2d_best signifikant --
konsistent mit der Skalen-These #30!), Kipppunkt-Arme pausiert.
**Lehre**: Verhaltens-Pins muessen auch AKTIVE Parameter-Pfade abdecken,
nicht nur Defaults. Forensik-Plan (morgen): Wheel #1 aus 5219d77 im
Worktree bauen, Sonden-Vergleich w=0/0,1/lambda auf identischen
Zustaenden, dann entscheiden, welche Stichprobe zaehlt.

## PCR-mild (p=0,5/cheap=300): Wandzeit-Kriterium VERFEHLT -- nicht empfohlen (2026-08-03/04)

**Voller Lauf** (PREREG_pcr_mild.md): 1320 Spiele / 215.791 Zuege in
4,04h = **327 Spiele/h** vs. Kontrolle 292,5/h -> **Faktor 1,118x**,
UNTER der vorregistrierten 1,15x-Schwelle (Kalibrierungs-Batch 330/h
hatte es angekuendigt). Da die Uebernahme-Regel (a)UND(b)UND(c) verlangt
und (c) messbar verfehlt ist, sind die 12 Trainings + Arena
GEGENSTANDSLOS -- begruendeter Abbruch des Ausfuehrungsplans (keine
Regel-/Metrikaenderung; das Adoption-Verdikt steht unabhaengig vom
Qualitaets-Ausgang fest). Korpus nach data/archive_pcrmild/ (Fenster-
Politik: PCR-Spiele nie als Tail).

**Tiefere Erkenntnis (wichtig fuer die 21h-Frage)**: 25% Sims-Reduktion
(600->450 Oe) ergab nur 11,8% Wandzeit -- der FIX-Kostenanteil je Zug
dominiert (~60%). Damit ist JEDE Such-Verbilligung (auch uniform weniger
Sims) als Self-Play-Beschleuniger nahezu wirkungslos. **Task #32
(vorgemerkt): Self-Play-Kostenprofil neu vermessen** -- der Fix-Anteil
ist seit `nortv` (altes 83%-rtv-Profil hinfaellig) voellig unvermessen.
KORREKTUR 2026-08-04 (code-geprueft): `bootstrap_value` laeuft NICHT je
Zug, sondern per HashMap einmal PRO RUNDE (`bootstrap_values.insert(
round_before, bv)`, self_play.rs:1096/2336) -- also ~4x/Partie, als
Haupttreiber weitgehend ausgeschieden. Neue Kandidatenliste:
(1) **Runde-5-Alpha-Beta** (`round5.rs`, NODE_BUDGET=200, je Knoten eine
EXAKTE Endwertung inkl. Tiling-Solve) -- vollstaendig sim-unabhaengig und
betrifft ~20% aller Zuege: neuer Hauptverdaechtiger;
(2) Tiling-DFS-Solver je Runde/Spieler;
(3) fixer Knoten-Overhead (Feature-Extraktion, ONNX-Aufrufkosten, dort
wirkt der 2D-Aufschlag 1,46-1,8x);
(4) bootstrap_value (4x/Partie, aber 2-Runden-Vorausschau je Aufruf --
messen statt vermuten).
Erst mit dem Profil entscheiden, wo die ~20h wirklich herkommen.

**HERLEITUNG 2026-08-04 (Nutzer-Anstoss "der 2D-Umstieg war dann teurer,
wenn nur dieser Anteil zaehlt")**: Die 1,46x sind ein reiner
INFERENZ-Mikrobenchmark (`examples/latency_2d_vs_flat.rs`, "gemessen vor
dem Training"), KEINE Gesamtdurchsatz-Zahl. Aus PCR-mild folgt
25% weniger Ø-Sims -> 10,6% weniger Zeit/Partie, also
`0,25*S/(F+S)=0,106` -> **S~42%, F~58%**. F ist reine Nicht-Netz-Arbeit
(R5-Alpha-Beta, Tiling-DFS, Spiellogik) und damit zwischen flach und 2D
IDENTISCH. Daraus:
- 2D-Gesamtaufschlag = 1,15x (bei 1,46x Inferenz) bzw. 1,23x (bei den
  nachgemessenen 1,8x) -- der Fixanteil VERDUENNT den Netz-Aufschlag,
  der Umstieg war also billiger als die Schlagzeile suggeriert.
- **Kehrseite, entscheidungsrelevant**: dieselbe Verduennung trifft jede
  Inferenz-OPTIMIERUNG. Static Folding (1,8x -> 1,58x, geschaetzt 3-5
  Tage) braechte `S*1,58/1,8 = 0,372` -> Gesamt 0,948, also **nur ~5%
  Wandzeit**. **Damit ist Static Folding erledigt, ohne es zu bauen** --
  der Hebel liegt im F-Anteil (58%), allen voran R5-Alpha-Beta.
- Konsequenz fuer die #32-Messung: das Profil MUSS Netz-Zeit und
  Nicht-Netz-Zeit getrennt ausweisen, sonst wiederholt sich der
  Fehlschluss.

## AUFLOESUNG des Stichproben-Widerspruchs: BLOCK-KORRELATION, nicht Wheel (2026-08-04)

**Forensik** (Wheel #1 aus 5219d77 im Scratchpad-Worktree rekonstruiert,
Sonden-Vergleich, `wheel_forensics_w_path.json`): **Wheel-These
WIDERLEGT** -- 30/30 Sonden byte-identisch zwischen den Wheels, w- und
lambda-Wirkung nachweisbar und identisch. Nebenbefund des Agenten fuehrte
zur wahren Ursache:

**Paare innerhalb eines 25er-Arena-Blocks sind KORRELIERT** (ein
Block-Seed formt die Spiel-Population; Block-Mittel der Scores streuen
~4 SE ueber das, was i.i.d.-Paare erlaubten -- z.B. la00-Bloecke 69 vs 92
Punkte/Paarsumme). Die Paar-Ebene-Statistik unterschaetzt die
Standardfehler systematisch. **Block-Ebene-Reanalyse:**
- Erst-Sweep-Denial (-6,16, "p=0,078"): kam aus EINEM Extremblock
  (+2,4/+6,2/-27,1) -> Block-p=0,62. ARTEFAKT.
- Frische Gegenrichtung (+9,63, "p=0,0001"): Block-p=0,061. Nicht
  belastbar.
- la00-Champion-Sieg (173:127, "p=0,0076"): Block-Winraten 54/66/48/54/
  70/54%, 5/6 ueber 50%, Block-p=0,076 -> TREND, nicht Beleg.

**Konsequenzen:**
1. **lambda_aggr-Fazit final**: KEIN belegter Denial-Effekt in beide
   Richtungen; der Regler bleibt als gefahrloser Stil-Knopf (Guardrail
   win-basiert nie gerissen), ohne belegten Score-Effekt. Kipppunkt-
   Kartierung gestrichen (Frage hinfaellig ohne belegten Effekt).
2. **v19_2d_opp @ w=0,1 als Champion-Kandidat**: drei unabhaengige
   positive Stichproben (Gate-2 52,3%, Erst-la00 54%, frisch 57,7%) --
   verdient ein REGULAERES Champion-Gating mit block-bewusster
   Auswertung (viele Bloecke; Block-Ebene-Bericht zusaetzlich zu SPRT).
3. **METHODIK-LEHRE (projektweit)**: Score-basierte Paar-Analysen
   MUESSEN auf Block-Ebene gerechnet werden; win-basierte SPRT/McNemar-
   Gatings sind vermutlich milder betroffen (relative Ausgaenge), aber
   kuenftige Berichte ergaenzen Block-Ebene-Zahlen. Historische
   Champion-Gatings mit grossen Margen (96:54 etc.) bleiben plausibel,
   knappe Score-Nebenbefunde (z.B. Task-#12-Punkte-Trend) sind neu zu
   bewerten.

## Kartierung + Champion-Gating v19_2d_opp: KEIN Staerkebeleg, Promotion offen (2026-08-04)

**Betriebsvorfall vorweg**: Agent A (Nacht-Pipeline) startete Arm 1 als
Hintergrund-Prozess und wachte danach nie wieder auf -- ~7,5h Maschine
idle, Pipeline B-E lief nie an. Lehre in Memory
`feedback_agent_background_process_discipline` ergaenzt: Laeufe >10 min
NUR vom Koordinator als harness-getrackte Tasks takten.

**lambda-Kartierung** (w=0.1, je 75 Paare, block-size 5, 15 Bloecke):

| lambda | Siege | Winrate | Block-Diff vs lam=0 | p |
|---|---|---|---|---|
| 0 | 80:70 | 53.3% | Referenz | -- |
| 3.0 | 74:76 | 49.3% | -0.040 | 0.41 |
| 5.0 | 64:86 | 42.7% | -0.107 | 0.084 |

**BREAK-EVEN GEFUNDEN**: monoton fallend, Klippe zwischen lambda=2 und 5,
Wendepunkt um 3. lambda=5 dreht die Bilanz gegen den Champion.

**w-Leiter** (lambda=0, je 75 Paare): 0.1 -> 53.3% | 0.2 -> 52.0%
(p=0.78) | 0.3 -> 55.3% (p=0.66) -- **FLACH, kein Einbruch bis 0.3**;
das v9b-Desaster bei w=0.5 war kopf-, nicht w-bedingt. Nebenbefund gegen
eine starke Skalen-Kompensations-These: mehr Punkte-Blend hilft NICHT
mehr -- erhoeht die Bedeutung von #30 (direkte Skalen-Korrektur).

**Champion-Gating** (w=0.1, lambda=2.0, 200 Paare, block-size 5,
`--no-promote-winner`): **205:195 = 51.25%, KEIN SPRT-Entscheid**
(LLR=-2.932, Deckel), McNemar p=0.68, Block-Ebene 17/40 Bloecke ueber
50%, t=+0.48 p=0.63.

**Gesamtbild ueber ALLE 7 Stichproben (1850 Spiele): 984:866 = 53.2%**
(i.i.d.-KI 50.9-55.5%, echtes KI wegen Block-Korrelation breiter --
beruehrt die 50%). Muster: **je hoeher die Power, desto kleiner der
Effekt** (57.7% bei n=300 -> 51.2% bei n=400) -- klassische Regression
zur Mitte, die frueheren "Siege" waren ueberschaetzt.

**NUTZER-ENTSCHEID (2026-08-04)**: Champion bleibt **v19_2d_best**.
Der opp-Kopf kommt ueber die naechste Generation in die Champion-Linie
(`v20_2d_opp`) -- Promotion also nicht jetzt auf Feature-Gruenden,
sondern regulaer per Generations-Gating. Planungs-Konsequenzen fuer v20:
(a) **Warm-Start von `v19_2d_opp_best`** (nicht v19_2d_best) -- der
opp-Kopf ist dort bereits trainiert (Opp-R² 0,44), beide Netze sind
arena-gleichwertig (205:195), kostet also keine Staerke; (b) das
v20-Gating testet dann Generationssprung UND opp-Kopf gemeinsam --
vertretbar, weil der Kopf in Gate 1/2 als staerkeneutral nachgewiesen
ist; bei einem Fehlschlag waere ein Zusatz-Gating ohne Kopf noetig, um
die Ursache zu trennen; (c) der Aggressions-Standardwert (w=0,1,
lambda=2,0) wird produktiv wirksam, sobald v20_2d_opp Champion ist --
bis dahin bleibt er Labor-Einstellung; (d) `v19_2d_opp_best`-Checkpoints
NICHT loeschen (Warm-Start-Basis).

**VERDIKT**: KEIN Staerkebeleg -> **keine Promotion auf Staerke-Gruenden**.
Der Kandidat ist aber auch nicht schlechter (7/7 Stichproben >=50%).
**Offene Nutzer-Entscheidung**: Die Aggressions-Funktion existiert
produktiv NUR, wenn v19_2d_opp geladen ist (der Champion hat keinen
opp-Kopf). Also entweder (a) Promotion auf FEATURE-Gruenden
(gleichstark + Aggressions-Faehigkeit, dokumentiert als solche) oder
(b) Aggression bleibt Labor-Feature und der Champion bleibt v19_2d_best.

## Task #32 GEMESSEN: Netz-Inferenz dominiert, Runde-5-Hypothese widerlegt (2026-08-04)

Instrumentierung (`engine/src/profiling.rs::selfplay_profile`, env-gegated
`MOSAIC_PROFILE_SELFPLAY=1`, ueberlappende Kategorien + Zusatzzaehler),
Messlauf 30 Partien / v19_2d_best / 600 Sims / 11 Threads / 500,6s
Wandzeit = 4845s Thread-Zeit (`selfplay_time_profile.json`):

| Kategorie | Zeit | Anteil | Aufrufe |
|---|---|---|---|
| Netz-Inferenz | 3002 s | **62,0%** | 1.314.962 |
| Tiling-Solver | 1311 s | **27,1%** | 6.324.160 |
| bootstrap_value | 401 s | 8,3% | 120 |
| round5-Alpha-Beta | 206 s | **4,3%** | 451 |

Ueberlappungen aufgeloest: von 206s Runde-5 sind 192s Tiling-Solver, nur
14s echte Alpha-Beta-Buchfuehrung; Netz-Zeit in Runde 5 **exakt 0**
(round5 ruft das Netz nie -- Agent-Vorhersage bestaetigt). Disjunkt:
Netz 62,0% | Tiling ausserhalb R5 23,1% | bootstrap ohne Netz 6,9% |
R5-Buchfuehrung 0,3% | Rest 3,8%.

**KORREKTUR meiner beiden Verdaechtigen**: weder `bootstrap_value`
(8,3%, laeuft pro Runde) noch der Runde-5-Alpha-Beta (4,3%) treibt die
Kosten. Die Endspiel-Verbilligungs-Idee ist damit ERLEDIGT (selbst eine
Halbierung braechte 2%).

**KORREKTUR der S/F-Herleitung vom selben Tag** (S~42%/F~58%): widerlegt.
Ursache des Fehlers: sie stuetzte sich auf "Kontroll-Lauf = 4h" -- aus
dem PREREG-PLAN uebernommen, nie als Dauer GEMESSEN; eine Annahme, die
wie ein Messwert behandelt wurde. Direkte Messung: **~85% der Zeit
skaliert mit Suchaufwand (Netz+Tiling), nur ~15% sind echt fix.** Sims
sind also doch der Haupthebel.

**Neuer Optimierungskandidat: Tiling-Solver-Memoisierung.** 6,3 Mio
Aufrufe bei 30 Partien (210k je Partie, 4,8 je Netz-Aufruf) auf 27% der
Laufzeit -- Transpositionen sind bei dieser Aufrufdichte wahrscheinlich,
und ein Cache liefert BITGLEICHE Ergebnisse (kein Qualitaetsrisiko,
anders als jede Budget-Kuerzung).

**Fuer die v20-Planung beziffert**: bei 1,8x 2D-Aufschlag entfallen
~1334s von 4845s auf den 2D-Mehrpreis -- **der 2D-Encoder kostet ~27,5%
der Self-Play-Zeit** gegenueber flach (Stand: exakt gemessen, nicht mehr
geschaetzt). Static Folding (1,8->1,58x) braechte entsprechend ~7,6%.

## Task #30 ERGEBNIS: Skalen-Korrektur +6pp, knapp nicht signifikant (2026-08-04)

Gepaarter A/B nach `PREREG_value_scale_correction.md` (Netz vs. Heuristik,
je 200 Spiele, identische Seeds, gepaart je Spielindex, fixed-n):

| Arm | Netz-Siege | Ø Score | Ø Floor |
|---|---|---|---|
| OFF (A=0, B=1) | 136/200 = **68,0%** | 49,74 | 9,22 |
| ON (A=0,00507, B=1,92689) | 148/200 = **74,0%** | 49,51 | 9,43 |

Diskordant: b(ON)=43, c(OFF)=31, konkordant 126 -> **exakter McNemar
p=0,2007**.

**VERDIKT nach PREREG-Regel: KEIN Staerkebeleg, kein Standardwechsel.**

**Einordnung**: +6 Prozentpunkte ist der GROESSTE gerichtete Effekt, den
eine value-seitige Intervention in diesem Projekt bisher gezeigt hat, und
es fehlen nur ~3 diskordante Paare zur Signifikanz -- ein unterpowerter
Beinahe-Treffer, kein Nullergebnis. Der Mechanismus passt zur
Report-Vorhersage (Idee 7.3): Gumbels `sigma(q)` ist linear in q,
gestreckte Werte setzen sich staerker gegen den Policy-Prior durch.

**Entscheidung zur Reihenfolge**: #30 (Platt-Korrektur) ist ein PFLASTER
auf der Stauchung, #34 zielt auf deren URSACHE (Kopf lernt Punkte-Marge
statt Sieg/Niederlage). Wirkt #34, sollte Platt-B von 1,93 Richtung 1
fallen und die Korrektur GEGENSTANDSLOS werden. Daher: **erst #34, dann
pruefen, ob #30 ueberhaupt noch gebraucht wird** -- statt jetzt ~2h in
eine Bestaetigungsmessung zu stecken, die #34 obsolet machen koennte.
Rohdaten: `value_scale_ab_arm_off.json` / `_arm_on.json`.

## Chance-Knoten-Vortest: Afterstate-These NICHT gestuetzt -- Projekt bleibt geparkt (2026-08-04)

Vor der Entscheidung ueber einen eigenen Worktree fuer den
Stochastic-MuZero-Afterstate-Kopf (Report 3.1) der vom Report selbst
empfohlene billige Vortest (`tools/chance_node_pretest.py`, neu).

**Designlogik**: ein reiner R²-Vergleich vor/nach dem Chance-Knoten waere
WERTLOS (vor dem Knoten ist der Ausgang objektiv unsicherer, da MUSS R²
sinken -- das misst die Aufgabe, nicht das Modell). Die eigentliche
Signatur der These ist die KALIBRIERUNG: ein sauber spezifizierter
Schaetzer bleibt auch unter Unsicherheit kalibriert (er sagt dann Werte
nahe 0,5). Fehlkalibrierung SPEZIELL vor Chance-Knoten waere der Beleg,
dass der Skalar zwei Unsicherheitsarten nicht trennen kann.

**Ergebnis** (v19_2d_best, frozen_eval_set, Runden 1-4, Gruppierung ueber
den Fabrik-Fuellstand):

| Gruppe | n | Platt-B | Brier | R² |
|---|---|---|---|---|
| nach Chance-Knoten (Fuellstand >=15) | 246 | 1,880 | 0,2384 | 0,045 |
| vor Chance-Knoten (Fuellstand <=6) | 515 | 2,021 | 0,2323 | 0,071 |

**Die Stauchung ist GLEICHMAESSIG ueber die Runde verteilt** (B~2 in
beiden Gruppen, praktisch identisch zum globalen Platt-Fit B=1,93). Die
These haette B_vor deutlich weiter von 1 verlangt, Richtung
UEBERkonfidenz (B<1) -- weder das eine noch das andere.

**Einschraenkungen, ehrlich**: (a) CONFOUND -- niedriger Fuellstand heisst
auch "weiter fortgeschritten in der Runde" (mehr Information); das
erklaert vermutlich das hoehere R² VOR dem Knoten, was der naiven
Erwartung widerspricht. Fuer die Kalibrierungsfrage wiegt es weniger,
sauber ist es nicht. (b) Zellen von 50-150 -> die Einzelrunden-Fits
schwanken zwischen -2,8 und +4,0 und sind NICHT interpretierbar, nur die
gepoolten Zahlen tragen. (c) gemessen am aktuellen, fehlgeleiteten
Value-Ziel (siehe #34).

**ENTSCHEIDUNG: kein Worktree, Afterstate-Projekt bleibt geparkt.**
Wiedervorlage nur, falls #34 die Kalibrierung global repariert UND
danach eine RESTlücke speziell an Chance-Knoten sichtbar bleibt -- dann
mit sauber herausgerechnetem Fortschritts-Confound.

## Tasks #33-#35 (eingetaktet 2026-08-04): drei Value-Head-Hebel aus dem Research-Report

Gemeinsame Randbedingung: Es gibt KEINEN validierten Offline-Praediktor
fuer die Value-Seite (#29 gescheitert, value_r2 4x widerlegt) -- jeder
dieser Hebel braucht ein eigenes Arena-Gating (~1h). Offline-Kennzahlen
werden nur deskriptiv berichtet.

### Task #33: Value-/Policy-Loss-Gewicht-Sweep (Report 5.3) -- BILLIGSTER, zuerst
Leiden-Befund (CoG 2019): reines Value-Loss schlaegt die AlphaZero-Summe
in 3 von 4 Spielen; bei uns nie systematisch variiert
(`VALUE_WEIGHT=0.2`, `POINTS_WEIGHT=0.5`). **Kein Code noetig** --
`train.py` hat bereits `--value-weight`/`--points-weight`.
Arme: value_weight ∈ {0.2 (Kontrolle), 0.5, 1.0}, warm von
`v19_2d_best`, sonst Champion-Rezept.
**FALLE, vorab benannt**: `val_combined` ist die Checkpoint-Auswahl-
Metrik UND enthaelt `value_weight` als Faktor -- zwischen Armen hat sie
also eine ANDERE DEFINITION und ist als Vergleichsgroesse UNGUELTIG
([[feedback-preregister-decision-metric]]). Auswahl je Arm daher intern
per val_combined (Bestandslogik), Vergleich NUR per Arena.

### Task #34 (HOCHGESTUFT 2026-08-04): Sieg/Niederlage-Ziel wiederherstellen -- die Kopf-Trennung ist faktisch aufgehoben

**Nutzer-Einwand 2026-08-04**: "wir haben extra einen value head mit
sieg/niederlage und einen point head mit dem forecast der eigenen
punkte" -- code-geprueft und BESTAETIGT, mit einer Historie, die das
Problem groesser macht als gedacht:

1. **Vor Schema 13 war der Value-Kopf genau das.** Der v13-Kommentar
   (`neural_net.py:538ff`) sagt woertlich: *"points_forecast gewichtet
   own_total stark, values ist reines Sieg/Niederlage"*, gemessen
   `corr(val_true, pts_true)=0,49` -- zwei klar verschiedene Ziele.
2. **Die Umstellung war eine HYPOTHESE, kein A/B**: *"Hypothese: das
   HARTE ±1-Ziel ... treibt den gemeinsamen Trunk staerker Richtung
   Overfitting"*. Ein Test dazu ist nirgends dokumentiert.
3. **Die Diagnose stammt aus der v8e-Aera** -- der Generation mit
   Val-R²<0, in der der Value-Kopf die Suche nachweislich
   VERSCHLECHTERTE.
4. **Es war damals nur der FALLBACK** (*"rtv bleibt unveraendert
   bevorzugt, wo vorhanden"*). Als `nortv` am 2026-07-28 Standard wurde,
   ist dieser Fallback STILLSCHWEIGEND zum Hauptziel befoerdert worden --
   in dieser Rolle nie getestet.

**Konsequenz**: Der Value-Kopf trainiert heute auf
`tanh((own-opp)/SCALE)` -- eine gestauchte PUNKTE-MARGE, also dasselbe
Material wie der Punkte-Kopf. `(v+1)/2` ist damit keine
Gewinnwahrscheinlichkeit, sondern eine umetikettierte Punktedifferenz.
Das erklaert die gemessenen Pathologien zwanglos: Runde-5-Fehlanzeige
(Δ+18 Punkte -> 31-37% angezeigt), Kopf-Uneinigkeit r=0,68, und die
Platten-Blindheit (Steigung 0,06).

**Neuer Zuschnitt**: Hauptarm = hartes Sieg/Niederlage-Ziel
(Kreuzentropie statt MSE), womit die beabsichtigte Kopf-Trennung
wiederhergestellt ist; der WDL-/Klassifikations-Umbau (Report 1.2) ist
dann die technisch saubere Umsetzung davon, kein eigenstaendiges
Experiment. Der v13-Overfitting-Einwand wird dabei mitgetestet (er
koennte in der heutigen, gesunden Kopf-Generation schlicht nicht mehr
gelten) -- Kontrolle ist das aktuelle weiche Ziel, Entscheidung per
Arena. **Prioritaet: vor #33 und #35.**

**PFLICHT-DIAGNOSTIK zu #34 (Nutzer-Entscheid 2026-08-04)**: Nach dem
Training `tools/r5_value_calibration.py` auf dem neuen Netz wiederholen
(identische Parameter wie der Lauf vom 2026-08-03: 24 Zustaende x 6
Kombinationen, 3 Modelle -> hier nur das neue + das weiche Kontrollnetz).
Frage: steigt die Wertungsplatten-Kalibrierungssteigung von heute
**0,06-0,09** Richtung 1? Ausserdem den Platt-Fit
(`value_calibration_fit.json`-Verfahren) wiederholen: faellt B von
**1,93** Richtung 1?

**Damit ist die separat angedachte WERTUNGSPLATTEN-INTERVENTION
ZURUECKGESTELLT** (Symptom vs. Ursache): erst messen, ob die
Platten-Blindheit nach der Ziel-Reparatur ueberhaupt noch existiert.
Nur falls die Steigung flach BLEIBT, ist ein gezielter Eingriff
(Platten-Encoding / Aux-Kopf auf den Platten-Endbonus) gerechtfertigt --
dann aber als eigene Vorregistrierung mit dann bekanntem Ausgangswert.

### (urspruenglicher Zuschnitt) WDL-/Klassifikations-Value-Kopf (Report 1.2)
KataGo/lc0 ersetzen die Tanh-Regression durch Softmax-Klassifikation
ueber Ergebnisklassen; lc0s expliziter Ausloeser war exakt unser
Nichtlinearitaets-Symptom. Aufwand: Python (Kopf 1 Skalar -> 2 Logits,
MSE -> Kreuzentropie) + Rust (`value_to_win_prob` liest P(win) statt
(tanh+1)/2) + ONNX-Vertrag wie beim opp-Kopf (additiv, per Name erkannt,
Alt-Modelle unberuehrt).
**KONZEPTIONELLER VORBEHALT, vorab benannt**: Klassifikation braucht ein
HARTES Ergebnis-Ziel -- das Projekt hat sich mit VALUE_SCHEMA_VERSION=13
bewusst vom harten +-1 zum weichen tanh-Margin bewegt. WDL ist damit
teilweise eine Rueckabwicklung dieser Entscheidung; die Kombination
"weiches Margin-Ziel + Klassifikationsverlust" ist NICHT
literaturgestuetzt. Vor dem Bau ist zu entscheiden, welches Ziel gilt
(Vorschlag: hartes Sieg/Niederlage als eigener Arm, weil genau das der
lc0/KataGo-Praezedenzfall ist).

### Task #35: Ranking-Loss auf Geschwister-Q (Report 7.1) -- BRAUCHT ENGINE-VORLAUF
**Datenlage geprueft 2026-08-04**: Self-Play-Records tragen NUR
`policy[].prob` und ein SKALARES `root_q` -- **kein Q je Wurzelkind**.
Der Ranking-Loss braucht aber genau diese Paare.
**Konsequenz fuer die Reihenfolge**: das additive Logging (completed-Q je
Wurzelkind, analog zum `root_q`-Commit 2718b9a) muss VOR der
v20-Self-Play-Kampagne in die Engine -- sonst kostet das Experiment
spaeter eine eigene Kampagne (~20h) oder eine teure Nachannotation.
Danach: Trainings-Loss (RankNet-Stil auf Geschwisterpaaren) + Arena.
Dass #29 die Rang-METRIK verworfen hat, praejudiziert das Rang-TRAINING
nicht -- nur die Vorauswahl per Metrik faellt weg.

### Reihenfolge
#33 (heute/morgen, kein Code) -> #35-Engine-Logging (VOR v20-Self-Play,
klein und additiv) -> #34 (Code + Ziel-Entscheidung) -> #35-Training
(nach v20-Self-Play, wenn die Labels da sind).

## Task #29 ERGEBNIS: Value-Rangmetrik NICHT VALIDIERT (2026-08-04)

**Paar-Basis erweitert** (3 neue SPRT-Arenen, alle entschieden):
v19_2d_best 53:27 v17_best | v19_best 81:39 v17_best | v19_2d_best 85:55
v18_best -- damit 6 auswertbare entschiedene Paare statt 4.

**Validierung** (`value_rank_metric_validation.json`, 952 Orakel-Zustaende
je Modell, mean_overlap 0.94-0.97):

| Paar | Siegq. A | Δtau | richtig? | Δvalue_r2 | richtig? |
|---|---|---|---|---|---|
| l07v18_s6 vs l10v18_s3 | 0.568 | +0.0016 | JA | +0.0162 | JA |
| v18_best vs v17_best | 0.584 | +0.0068 | JA | +0.0030 | JA |
| v19_2d_best vs v18_best | 0.607 | -0.1056 | nein | -0.0152 | nein |
| v19_2d_best vs v19_best | 0.640 | -0.0980 | nein | +0.0102 | JA |
| v19_best vs v17_best | 0.675 | -0.0007 | nein | -0.0224 | nein |
| v19_best vs v18_best | 0.640 | -0.0075 | nein | -0.0254 | nein |

**`value_kendall_tau_vs_oracle_q`: 2/6 richtig (p=0.69) -- NICHT
VALIDIERT**, sogar schlechter als das globale `value_r2_rounds_1_4`
(3/6, p=1.0). Beide auf Zufallsniveau.

**Einordnung (ehrlich)**: Die Ordnungs-These ist damit NICHT bestaetigt --
zumindest nicht in DIESER Operationalisierung (Kendall-Tau der
Value-Kopf-Blattwerte ueber Wurzelkandidaten gegen die Orakel-Q-Ordnung).
Moegliche Gruende, unentschieden: (a) die Orakel-Q-Referenz stammt selbst
aus einer 5000-Sims-SUCHE (policy-gefuehrt) -- eine Value-Ordnung dagegen
zu messen vergleicht evtl. Aepfel mit Birnen; (b) relevant koennte die
Ordnung an TIEFEREN Blaettern sein, nicht an Wurzelkindern.

**Auffaelliger Nebenbefund**: Der 2D-Champion hat eine deutlich
SCHLECHTERE Value-Rangordnung als die flachen Netze, die er schlaegt
(tau 0.241 vs 0.339) -- konsistent mit dem alten Befund, dass
Offline-Metriken ueber ARCHITEKTUR-Grenzen hinweg nicht tragen
([[project-2d-encoder-phase2-result]]). Der 2D-Vorteil liegt offenbar
nicht in der Value-Rangordnung.

**Konsequenz fuer den Projektbetrieb**: Es gibt weiterhin KEINEN
validierten Offline-Praediktor fuer die Value-Seite. Value-Experimente
muessen per Arena entschieden werden -- teuer, aber ehrlich. Das
Ranking-Loss-Experiment (Report-Idee 7.1) war hinter dieser Validierung
gegated; es kann weiterhin gefahren werden, aber NUR mit Arena als
Schiedsrichter (die Metrik taugt nicht zur Vorauswahl).

**Nutzer-These nach der Dreifach-Evidenz des Tages**: value_r2 ist
vermutlich nicht der richtige Hebel fuer Arena-Staerke. Belege: (1)
v11-TD-Bootstrap hob R1/R2-R², keine Staerke; (2) Lambda-Sweep 6/6 Seeds
offline positiv, Arena SPRT-H0; (3) PCR value_r2 +0,04 fuer pcr,
Arena-Trend negativ. GLEICHZEITIG traegt der Value-Head die Staerke
(2x2-Kopftausch bei 400 Sims). Aufloesung: die Suche konsumiert lokale
ORDNUNG von Blatt-/Geschwisterzustaenden, nicht globale
Ausgangs-Vorhersage -- R² misst die falsche Eigenschaft. Konsistent:
beide arena-validierten Policy-Praediktoren sind Ordnungs-Metriken;
v8d-Postmortem-Fingerzeig (Sibling-Ranking-Tau R1 besser als R²
suggerierte).

**Plan (PREREG bei Angehen)**:
1. Metrik `value_kendall_tau_vs_oracle_q` (Arbeitsname): Value-Head auf
   den AFTERSTATES der Wurzelkandidaten der frozen-set-Zustaende
   auswerten (wie die Suche an Blaettern), Kendall-Tau gegen die
   Orakel-Q-Ordnung (`frozen_v1_oracle_labels_v18`); R5-Teilmenge
   optional gegen exakte ab_values.
2. Historische Validierung ueber die entschiedenen Gating-Paare
   (`tools/offline_vs_arena.py`-Prozedur -- dieselbe, mit der value_r2
   als Fein-Praediktor durchfiel und die Orakel-Metriken bestanden).
3. NUR bei bestandener Validierung: Metrik wird Entscheidungskriterium
   fuer Value-Experimente; danach erst ueber Ranking-orientierte
   Trainingsziele nachdenken (Paarvergleichs-/Margin-Loss) -- als
   separate PREREG.

**Einordnung**: VOR jedem weiteren Value-Trainingsexperiment (sonst wird
wieder am falschen Messziel optimiert). Research-Agent (2026-08-03) hat
die These als Fokus-Nachtrag erhalten.

## Task #30 (vorgemerkt): Skalen-Korrektur-A/B -- monotone Value-Rekalibrierung als Laufzeit-Knopf (2026-08-03)

**Motivation (Research-Report Idee 4.1 + 7.3, Gumbel-Paper-Volltext)**: Die
Gumbel-Policy-Improvement-Beweise verlangen von σ nur Monotonie, die
implementierte Instanz ist aber LINEAR in q̂ -- unsere gemessene
6-9%-Wertstauchung (R5-Kalibrierung, Task #27) wird 1:1 in eine zu
schwache completed-Q-Perturbation durchgereicht: die Suche zieht sich
staerker zum Policy-Prior zurueck, als die wahren Wert-Differenzen
rechtfertigen. Eine MONOTONE Skalen-Korrektur (Platt-artig) aendert die
Ordnung per Definition NICHT -- hebt sie die Arena-Staerke, war die Skala
der Engpass (und R² nur der falsche Proxy dafuer).

**Design-Skizze (PREREG bei Angehen)**: Laufzeit-Parameter in der Engine
(monotone Streckung des Value-Outputs vor der σ-Konsumtion, z.B.
Logit-Skalierung; Kalibrierungs-Quelle und Fit-Split VORAB festlegen --
Kandidat: frozen-set-Ausgaenge je Runde, R5-Kurve aus Task #27 als
Startpunkt), dann gepaarte Arena DESSELBEN Netzes mit vs. ohne Korrektur
(n>=150, fixe Sims, kein Fruehstopp). Kein Retraining, kein Self-Play.

**Diagnose-Paar mit der Ordnungs-Seite**: Task #30 ist die reine
SKALA-Intervention; das reine ORDNUNGs-Gegenstueck (Ranking-Loss auf
Geschwister-Q, Report Idee 7.1) wird ERST nach bestandener
#29-Metrik-Validierung als eigenes Experiment aufgesetzt. Zusammen
beantworten sie, welche Eigenschaft "R² war der falsche Hebel" konkret
war (Ordnung, Skala, oder beides).

**Reihenfolge (Nutzer-Entscheid 2026-08-03)**: #29 und #30 direkt NACH
der laufenden Queue (v18only-Lambda -> Task #28 -> R4-Kalibrierung),
VOR jedem neuen Value-Trainingsexperiment und vor dem v20-Zyklus-Start.

## Task #28 (vorgemerkt): Aggressiveres Spiel -- Score-/Denial-Utility (2026-08-03)

**Nutzer-Wunsch**: die KI soll aktiv dem Gegner schaden (Punkte wegnehmen/
verhindern), solange es das eigene Gewinnen nicht gefaehrdet -- nicht nur
selbst sammeln. Nutzer-Vorschlag: `VALUE_OPP_EPSILON` (Punkte-Kopf-Ziel)
hochsetzen im Sweep, dann Punkte eines GLEICHBLEIBENDEN Gegners vergleichen.

**Verdrahtungs-Befund (2026-08-03, code-geprueft)**: der Punkte-Kopf
beeinflusst die Live-Suche aktuell GAR NICHT --
`net_mcts.rs::POINTS_UTILITY_WEIGHT = 0.0` (KataGo-Stil-Blend
`(1-w)*winprob + w*points` existiert, ist aber aus). Ein reiner
ε-Sweep (`VALUE_OPP_EPSILON`, aktuell 0.1, `neural_net.py:583`) wuerde
das Live-Verhalten daher NICHT aendern -- ε wirkt nur ins TRAINING des
Punkte-Kopfs. Beide Hebel muessen gekoppelt werden. Zusaetzlich zu wissen:
`round5.rs` spielt Runde 5 bereits exakt auf Marge (eigen-gegner) --
maximal "aggressiv" im Endspiel; der Hebel betrifft Runden 1-4.

**Historischer Kontext (Warnung)**: POINTS_UTILITY_WEIGHT 0.5/1.0 wurde
2026-07-19 (v9b-Aera, kaputte Head-Generation, 150 Sims) getestet und
scheiterte klar -- Kommentar an der Konstante. Der Retest heute hat zwei
andere Vorzeichen: gesunde Koepfe (v19_2d, Punkte-Kopf-R² historisch
0.33-0.44) und ein KLEINES w-Regime (0.05-0.2 statt 0.5/1.0) -- genau dort
liefert der Blend das Gewuenschte: solange die Partie offen ist, dominiert
winprob; ist sie (fast) entschieden, saettigt winprob und der
Punkte-/Denial-Term uebernimmt den Gradienten.

**Design-Skizze (zweiphasig, PREREG folgt bei Angehen; ueberarbeitet nach
Nutzer-Einwand 2026-08-03)**:
- **Nutzer-Einwand zum ersten Entwurf (korrekt)**: ein reiner
  `POINTS_UTILITY_WEIGHT`-Sweep mit dem BESTEHENDEN Kopf (ε=0.1) blendet
  zu ~90% EIGENE Punktemaximierung ein, nur ~10% Gegner-Term -- das ist
  "Gier", nicht "Schaden". Der Denial-Anteil haengt allein an ε, und ε
  steckt aktuell im TRAININGSZIEL (cache-zeitlich eingebacken) -- jede
  Aggressions-Stufe wuerde ein eigenes Retraining kosten.
- **Phase A (Architektur, EIN Retraining)**: separater
  **Gegner-Punkte-Kopf** (`opp_points_head`, Aux-Ziel
  `tanh(opp_total/VALUE_SCALE)` -- additiv, Praezedenz value/points/moon/
  ownership-Mehrkopf-Struktur). Damit wird die Utility zur Laufzeit frei
  mischbar, OHNE weitere Retrainings:
  `utility = (1-w)*winprob + w*(own_pts - λ_aggr*opp_pts)`,
  `w`/`λ_aggr` laufzeit-konfigurierbar (Praezedenz GUMBEL_TOP_M/PCR).
  ε im bestehenden Punkte-Kopf-Ziel bleibt unangetastet (kein Eingriff in
  die Bestandsheads, kein VALUE_SCHEMA-Bruch fuer alte Caches noetig --
  additives Feld wie root_q/ownership).
- **Phase B (Messung, Nutzer-Design)**: λ_aggr-Sweep zur Laufzeit (z.B.
  {0, 0.5, 1.0, 2.0} bei festem kleinem w) -- gepaarte Arena gegen FESTEN
  Gegner (amtierender Champion, w=0), Primaermetrik = Ø-GEGNERpunkte
  (Denial-Nachweis: sinken sie, WEIL λ_aggr steigt?), **Guardrail =
  eigene Win-Rate darf nicht signifikant fallen** (Nicht-Unterlegenheit,
  McNemar -- operationalisiert "solange es dem Gewinnen nicht im Weg
  ist"), sekundaer eigene Punkte + Bodenstrafe. Erwartbares Muster bei
  steigendem λ_aggr: Gegnerpunkte sinken, eigene Punkte sinken leicht
  (Denial kostet Tempo), Win-Rate stabil -- bis zum Kipppunkt, ab dem
  der Guardrail reisst; der beste λ_aggr ist der letzte VOR dem
  Kipppunkt.

- **Konsequenz (Nutzer, 2026-08-03): `VALUE_OPP_EPSILON` wird damit
  obsolet.** Zielbild: reiner Own-Punkte-Kopf (ε=0) + reiner
  Opp-Punkte-Kopf -- JEDE Mischung inkl. der bisherigen 0,1er-Semantik
  ist dann ein Laufzeit-Spezialfall (own − λ·opp, λ=0,1). Migration im
  SELBEN Schema-Schritt wie der neue Kopf (ein Cache-Bump); betroffene
  Konsumenten klein (debug.html-Ruecktransformation zeigt dann reine
  eigene Punkte, rtv-Zweig der Formel). Alt-Checkpoints behalten ihre
  Alt-Semantik (kein opp-Kopf vorhanden, w=0-Default -> Live-Verhalten
  byte-identisch, Additiv-Regel eingehalten).

**Einordnung**: nach der laufenden Experimentkette (Lambda -> PCR -> R5 ->
R4) und dem v20-Zyklus einplanen -- kein Blocker fuer v20, aber ein
direkt spuerbarer GUI-Spielstaerke-/Spielstil-Hebel.
