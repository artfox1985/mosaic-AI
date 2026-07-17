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
  (Hilfsziel/Aux-Head, alte score-Regression). `VALUE_WEIGHT=1.0`,
  `POINTS_WEIGHT=0.5` (`config.py`). `VALUE_SCHEMA_VERSION=11`
  (`neural_net.py`).
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

## Offen: Runden-Übergangs-Sampling (Chance-Node-Evaluator)

`engine/src/round_transition.rs` (neu) — adressiert das dokumentierte
Val-R²-Plateau (0.2-0.3, siehe Archiv): der Suchbaum endet am
Rundenübergang als Pseudo-Terminal, bewertet per Einzelwert; die
Fabrik-Neubefüllung (+ Bonusplättchen-Zuteilung, beide nur einmal beim
Spielstart gemischt) ist nirgends als echter Zufallsknoten repräsentiert.
Sampelt N mögliche Neubefüllungen, wertet jede über einen netzbasierten
Bewerter aus, mittelt.

- **Trainingsziel-Pfad** (`self_play.rs::play_net_self_play_game`):
  unconditional aktiv, hängt `round_transition_value` an Step-Records an.
  `neural_net.py` nutzt das für den `points_forecast`-Aux-Head. **Gebaut,
  103 Rust-Tests grün, aber NICHT end-to-end gegen ein echtes Modell
  verifiziert** — alle vorhandenen `.onnx`-Modelle sind älter als der
  INPUT_SIZE/Value-Head-Umbau und laden nicht mehr (Shape-Mismatch,
  bestätigt).
- **Live-Suche** (`net_mcts.rs::make_node`): gleiche Sampling-Logik am
  Runden-End-Blatt, hinter `ROUND_TRANSITION_SAMPLING` (aktuell `false`) —
  erst nach belegter Val-R²-Verbesserung im Trainingsziel-Pfad aktivieren.

## Nächste Schritte (in Reihenfolge)

1. **Datenlage entscheiden**: seit der letzten vollen Self-Play-Generierung
   wurde die Kuppelstapel-Mechanik umgebaut, Runde 5 auf Alpha-Beta
   umgestellt, `NUM_ACTIONS`/`INPUT_SIZE` geändert. Bewusst entscheiden, ob
   mit gemischtem altem/neuem Regelwerk trainiert wird, oder sauber neu
   generiert wird.
2. **Ersten INPUT_SIZE=708-kompatiblen Net bootstrappen**, Cold-Start aus
   Heuristik-Self-Play (Nutzer hat noch Heuristik-Spiele vom 07.07. verfügbar
   — Kandidat für diesen Cold-Start, sofern Punkt 1 sie als gültig
   einstuft). Braucht noch KEIN Runden-Übergangs-Sampling.
3. **Netzgeführtes Self-Play mit diesem Modell laufen lassen** — der
   Trainingsziel-Hook ist bereits aktiv, `round_transition_value` fällt
   automatisch mit ab.
4. **Neu trainieren, `points_forecast`-Val-R² gegen das 0.2-0.3-Plateau
   vergleichen** — das eigentliche Go/No-Go-Kriterium.
5. **Verzweigen**:
   - Bewegt sich vom Plateau weg → `ROUND_TRANSITION_SAMPLING=true`,
     `net_game_timeout_secs` neu kalibrieren, Wall-Clock-Regressionstest
     gegen echte Zustände, dann A/B via `run_net_vs_net_arena` vor
     Standard-Aktivierung.
   - Keine Bewegung → Ergebnis hier festhalten, damit es nicht erneut
     aufgerollt werden muss.

## Referenz

- Historische Details, alte Architektur, Sweep-/Kapazitätstests:
  [`archive/STAGE2_TODO_ARCHIVED.md`](../archive/STAGE2_TODO_ARCHIVED.md)
- Stufe-2-Ursachenforschung (0:0-Rate, Disagreement-Studie):
  [`archive/stage2_investigation.md`](../archive/stage2_investigation.md)
