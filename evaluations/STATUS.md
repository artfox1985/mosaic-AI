# Mosaic-AI — Aktueller Status

Löst `STAGE2_TODO_ARCHIVED.md` als lebendes Status-/Fahrplan-Dokument ab
(2026-07-17) — dieses File trägt NUR den aktuellen Stand, keine
Sweep-/Kapazitätstest-Historie mehr. Für die alte Architektur (tanh-Delayed-
Reward-Value-Ziel, "Stufe 1 bleibt Produktionspfad", VALUE_WEIGHT-Sweep,
v1-v7cold) siehe das archivierte File (`../archive/STAGE2_TODO_ARCHIVED.md`,
mit dem restlichen alten Auswertungsmaterial zusammengelegt).

## Architektur, Stand jetzt

- **Stufe 2 (Netz-Value-Blatt) ist der Produktions-Pfad**, nicht mehr Stufe 1.
  `net_mcts::ACTIVE_LEAF = LeafEval::Net`. Stufe 1 (`mcts.rs`, DFS-Solver-
  Blatt) bleibt im Code liegen, dormant, nicht mehr aktiv gepflegt — der
  Bewerter dort liest `state.factories` nirgends und cacht Blattwerte nicht
  pro Knoten, ist also strukturell auch nicht fürs Rundenübergangs-Sampling
  geeignet (siehe unten).
- **Value-Head zurückgeholt**: `MosaicNet` hat wieder einen `value_head`
  (±1 Sieg/Niederlage, Tanh) PLUS separaten `points_head`
  (Hilfsziel/Aux-Head, alte score-Regression). `VALUE_WEIGHT=0.2`
  (2026-07-17 gesenkt, siehe unten), `POINTS_WEIGHT=0.5` (`config.py`).
  `VALUE_SCHEMA_VERSION=12` (`neural_net.py`).
  **Wichtig, ggü. früherem Stand hier korrigiert**: `values` (nicht
  `points_forecast`) treibt die Live-Suche — `net_mcts.rs::make_node` liest
  bei `ACTIVE_LEAF=Net` ausschließlich `value_to_win_prob(value)` für den
  PUCT-Blattwert, `points` wird dort verworfen. `points_forecast` ist reines
  Trunk-Zusatzsignal ohne Sucheinfluss.
- **`INPUT_SIZE=708`** (707 + `dome_wild_remaining_frac`, Wild-Anteil der
  verdeckten Kuppelstapel-Restplatten — explizites Aggregat ergänzend zur
  `dome_pool_mask`).
- **Runde 5: exakte Alpha-Beta-Suche** (`engine/src/round5.rs`). Ab Runde 5
  keine Kuppelplatzierung mehr, alle Rundenzufälligkeit vor Rundenbeginn
  aufgelöst → Full-Information-Endspiel, ersetzt PUCT/Netz-Approximation
  durch Minimax + Alpha-Beta-Pruning mit exakter Wertungsplatten-Endwertung.
  Zeitbudget-basiert (150ms/Entscheidung). **Fertig, getestet, aktiv.**
- **Kuppelstapel-Mechanik regelwerkstreu**: sequentielles Ziehen
  (`Action::DrawStackPeek`/`DrawStack`, Rückseite zeigt nur Typ vor dem
  Aufhören), `DrawFromStackMove::return_order` (Spieler wählt Reihenfolge
  der zurückgelegten Platten). Punkte-gedeckelte Ziehungen (max. so viele
  wie Punkte vorhanden, Deadlock-Ausnahme bei 0 Punkten). Rückseite der
  obersten Stapelplatte + aller bisher gezogenen Rückseiten eines Zugs
  jederzeit sichtbar (für beide Spieler). **Fertig, getestet, aktiv.**

## Runden-Übergangs-Sampling (Chance-Node-Evaluator)

`engine/src/round_transition.rs` — adressiert das dokumentierte
Val-R²-Plateau (0.2-0.3, siehe Archiv): der Suchbaum endet am
Rundenübergang als Pseudo-Terminal, bewertet per Einzelwert; die
Fabrik-Neubefüllung (+ Bonusplättchen-Zuteilung, beide nur einmal beim
Spielstart gemischt) ist nirgends als echter Zufallsknoten repräsentiert.
Sampelt N mögliche Neubefüllungen, wertet jede über einen netzbasierten
Bewerter aus, mittelt.

- **Trainingsziel-Pfad** (`self_play.rs::play_net_self_play_game`): aktiv,
  hängt `round_transition_value` an Step-Records an. Ab
  `VALUE_SCHEMA_VERSION=12` ersetzt es (wo vorhanden) sowohl `values`
  (Hauptziel, treibt die Suche) als auch `points_forecast`. Bugfix
  2026-07-17: leckte vorher fälschlich auch in Runde-5-Records (dort kein
  echter Zufallsübergang) — behoben (`round_before < NUM_ROUNDS`-Guard).
  **Gegen echte Modelle verifiziert** (v8/v8b).
- **Live-Suche** (`net_mcts.rs::make_node`): gleiche Sampling-Logik am
  Runden-End-Blatt, hinter `ROUND_TRANSITION_SAMPLING` (Standard weiterhin
  `false`). 2026-07-17 einmalig testweise mit v8 auf `true` gesetzt und ein
  komplettes Netz-vs-Netz-Spiel über alle 5 Runden laufen lassen — kein
  Crash, Timing unauffällig (Median 143ms/Zug, Max 383ms). Bestätigt: der
  Codepfad funktioniert. Noch nicht als Standard aktiviert (siehe Punkt 5
  unten — Val-R²-Vergleich steht noch aus).

## v8 / v8b — Sanity-Check-Befunde (2026-07-17)

Erste INPUT_SIZE=708-kompatible Modelle. `values` (Such-treibender Head)
zeigte in v8 massives Overfitting: Val-R²=-0.43, Train/Val-Loss-Verhältnis
48.6x. `points_forecast` (kein Sucheinfluss) generalisierte am selben Trunk
deutlich besser: Val-R²=0.27.

- **VALUE_WEIGHT 1.0→0.2** (v8b): Verhältnis auf 13.7x gesenkt, Val-R² nur
  leicht verbessert (-0.36) — bleibt negativ, also schlechter als der reine
  Mittelwert. Reduziert Overfitting, löst das Problem aber nicht.
- **Early-Stopping-Lücke gefunden**: Plateau-Erkennung beobachtete bisher nur
  die TRAIN-Policy-Loss. Der v8b-Loss-Plot zeigt, dass die VAL-Policy-Loss
  ihr Minimum schon bei Epoche ~15-18 hatte und danach bis Epoche 56 (Ende
  des Laufs) durchgehend stieg (2.2→2.67), während Train-Policy-Loss
  weiter fiel — Early Stopping griff nie, weil es die falsche Kurve
  beobachtete. Behoben: `train.py` erkennt Plateau jetzt auf `val_ploss_history`
  (Fallback auf Train-Loss nur ohne Val-Split).
- **`round_transition_value` jetzt auch für `values` selbst** (nicht nur
  `points_forecast`), `VALUE_SCHEMA_VERSION=12` — gleiche Rauschreduktion,
  die beim Punktestand-Aux-Head schon half (0.27→0.34), jetzt auf dem Head
  angewendet, der tatsächlich die Suche treibt.

## Nächste Schritte (in Reihenfolge)

1. **v8c trainieren**: mit VALUE_SCHEMA_VERSION=12 (Cache-Rebuild nötig,
   Version geändert), Val-basiertem Early Stopping, `VALUE_WEIGHT=0.2`.
   Vergleich gegen v8b: `values`-Val-R² (Ziel: aus dem Negativbereich raus),
   Epoche, bei der Early Stopping jetzt greift (sollte deutlich vor 56
   liegen).
2. Falls `values`-Val-R² sich klar bewegt: `ROUND_TRANSITION_SAMPLING=true`
   als Standard erwägen, `net_game_timeout_secs` neu kalibrieren
   (Rundenend-Knoten werden durch Sampling teurer), A/B via
   `run_net_vs_net_arena` vor Umstellung.
3. Falls keine Bewegung: irreduzibles Rauschen wahrscheinlicher als
   Trainingsziel-Konstruktion — Ergebnis hier festhalten, nicht erneut
   aufrollen.

## Referenz

- Historische Details, alte Architektur, Sweep-/Kapazitätstests:
  [`archive/STAGE2_TODO_ARCHIVED.md`](../archive/STAGE2_TODO_ARCHIVED.md)
- Stufe-2-Ursachenforschung (0:0-Rate, Disagreement-Studie):
  [`archive/stage2_investigation.md`](../archive/stage2_investigation.md)
