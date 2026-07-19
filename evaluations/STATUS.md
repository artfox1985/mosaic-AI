# Mosaic-AI — Aktueller Status

Löst `STAGE2_TODO_ARCHIVED.md` als lebendes Status-/Fahrplan-Dokument ab
(2026-07-17) — dieses File trägt NUR den aktuellen Stand, keine
Sweep-/Kapazitätstest-Historie mehr. Für die alte Architektur (tanh-Delayed-
Reward-Value-Ziel, "Stufe 1 bleibt Produktionspfad", VALUE_WEIGHT-Sweep,
v1-v7cold) siehe das archivierte File (`../archive/STAGE2_TODO_ARCHIVED.md`,
mit dem restlichen alten Auswertungsmaterial zusammengelegt).

## Aktuelles Ziel (2026-07-19)

**Den Value-Head geradeziehen** — das ist gerade die Priorität vor allem
anderen. Grund: ein Net-vs-Heuristik-A/B (siehe unten) zeigt, dass der
aktuell trainierte Value-Head die Live-Suche AKTIV verschlechtert, nicht nur
neutral bleibt. Zwei Dinge ausdrücklich NICHT auf dem Tisch:

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

## Nächste Schritte (in Reihenfolge)

1. **Value-Head-Reparatur ist Priorität #1** (s.o. "Aktuelles Ziel") — bevor
   weitere Daten-Skalierung (round_transition_value oder Kuppel-Faktorisierung)
   als Lösung angenommen wird, klären: liegt das Problem an Datenmenge oder
   an der Zielkonstruktion selbst (binäres ±1 bei knappen Ergebnissen)? Ein
   möglicher nächster Test: Kalibrierung/Korrelation von `values`-Vorhersage
   gegen `points_forecast`-Vorhersage auf denselben Val-Zuständen, um zu
   sehen, ob das Problem tatsächlich am Ziel selbst liegt oder am Trunk/Head.
2. **5000-Spiele-Kuppel-Faktorisierungs-Auswertung** abschließen (self-play
   läuft/geplant), Ergebnis hier nachtragen: hat A einen messbaren
   Policy-Qualitäts-Effekt (nicht nur "kein Crash")?
3. Erst NACH 1: erwägen, ob mehr round_transition_value-Daten (2000-3000
   Spiele) oder eine andere Zielkonstruktion sinnvoller ist.
4. `ROUND_TRANSITION_SAMPLING` in der Live-Suche bleibt hinten angestellt,
   bis Punkt 1 einen klaren Fortschritt zeigt.
5. **Baustein B (zweistufiger Slot→Rotation-Suchknoten) explizit NACH
   Punkt 1** (Nutzer-Entscheidung 2026-07-19) — nicht parallel angehen.

## Referenz

- Historische Details, alte Architektur, Sweep-/Kapazitätstests:
  [`archive/STAGE2_TODO_ARCHIVED.md`](../archive/STAGE2_TODO_ARCHIVED.md)
- Stufe-2-Ursachenforschung (0:0-Rate, Disagreement-Studie):
  [`archive/stage2_investigation.md`](../archive/stage2_investigation.md)
