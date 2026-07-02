# Offensiv-Spiel: Repräsentation/Architektur statt Heuristik-Terme

## Status (aktualisiert nach Rust-Migration)

- ✅ **Stufe 1 (Linien-/Endwertungs-Features) ist umgesetzt — in Rust.**
- ⏳ Offen: Gen-0 mit den neuen Features neu trainieren + in der Arena messen
  (Punkte/Stein, Ø Siegerscore, Floor-Rate). Daten wurden bereits geleert.
- ⏳ Stufe 2 (räumlicher CNN-Zweig) nur, falls Stufe 1 nicht reicht.

Wichtige Korrektur zur ursprünglichen Deutung: Das „Mondsteine auf die Strafleiste
werfen" war **Netz-Degeneration nach dem Training**, nicht der Datengenerator — die
Heuristik-MCTS (Python *und* Rust) wirft freiwillig nicht. Das **flache MLP konnte
die Linien-Strategie nicht repräsentieren** und ist in den „sicheren" Strafleisten-
Hafen degeneriert. Genau diese Repräsentationslücke schließen die neuen Features.

## Context

Punkte entstehen aus **zusammenhängenden orthogonalen Linien** auf dem 6×6-Dome
([round_end.rs `score_placed_tile`/`count_line`](engine/src/round_end.rs:341)) plus
**Endwertung** (8 Kriterien, [scoring.rs](engine/src/scoring.rs)). Das ursprüngliche
Problem: Der Agent baute keine Linien (Punkte/Stein ~0,82, Ø Siegerscore ~9,8), weil
das eine mehrstufige Farb-Geometrie-Planung erfordert, die ein **flaches MLP**
([neural_net.py `MosaicNet`](engine/py/neural_net.py)) aus der **flachen** Dome-
Kodierung ohne Linien-Features nicht ausdrücken kann. Das Value-Target ist bereits
outcome-basiert — das Problem war Repräsentation, nicht die Belohnung.

## Was die Rust-Migration bereits geändert hat (Ausgangslage besser als 2024)

1. **`estimated_score` ist jetzt EXAKT statt Heuristik.** Früher Python
   `_estimate_round_score` (grobe per-Reihe-Schätzung); jetzt
   `estimated_score = solve_round_final_score − score`
   ([tiling_solver.rs](engine/src/tiling_solver.rs)), d.h. der **optimal erreichbare
   Tiling-Score** als Skalar — das Netz bekommt den Linien-Wert direkt.
2. **MCTS-Blätter werden mit dem exakten DFS-Solver bewertet** → die generierten
   Policy-Targets bevorzugen Linien-Bauen (Floor-Bias gemessen HARMLOS: 0 Strafleisten-
   Würfe, wenn eine Reihen-Alternative existiert; 0:0-Rate ~9 %).

## Stufe 1 — UMGESETZT (Linien- + Endwertungs-Features)

Berechnet in **Rust** ([scoring.rs](engine/src/scoring.rs)), ins State-Dict gespiegelt
([serialize.rs `serialize_player`](engine/src/serialize.rs)), gelesen in
[state_to_tensor](engine/py/neural_net.py). `INPUT_SIZE` 553 → **673**
([config.py](config.py)); +120 Features (60 je Spieler). Netz wird **von Null**
trainiert (Input-Schicht geändert).

**Linien-Geometrie** (`scoring::player_line_features` → `line_geo`):
- `h_hist`/`v_hist` — Linienlängen-Histogramm der zusammenhängenden Läufe (Länge 2–6).
- `cluster_sq` — Σ Lauflänge² (belohnt lange Linien indirekt über echte Outcomes).
- `row_potential`/`col_potential` — je Reihe/Spalte der **maximale Linien-Zuwachs eines
  füllbaren Felds** (= `score_placed_tile`-Wert) → direktes „welcher Zug baut eine
  Linie"-Signal für die Policy.

**Endwertung** (`scoring::player_scoring_features` → `scoring_tile_points` + `score_geo`):
- aktuelle Punkte aller 8 Wertungsplatten + Geometrie-Fortschritt (Reihen-/Spalten-/
  Diagonalen-Füllung, Farben/Reihe, Rand, Ecken, Wild, Spezial).

**placed-color-Fix:** Das `dome_grid`-Feld trägt jetzt die **platzierte Farbe**
(0=leer, 1-5=Farbe, 6=special) statt nur belegt/leer.

## Stufe 2 (nur falls Stufe 1 hilft, aber nicht reicht): räumlicher CNN-Zweig

Den Dome als `6×6×C`-Planes (belegt, required_color one-hot, type/locked) aufbereiten
und einen kleinen Conv-Zweig in `MosaicNet.body` einführen, dessen Output mit den
flachen Features konkateniert wird. Größerer Eingriff (Architektur + Reshape), echte
räumliche Induktion. Erst nach Messung von Stufe 1 entscheiden.

## Kritische Dateien

- `engine/src/scoring.rs` — `player_line_features`, `player_scoring_features`.
- `engine/src/serialize.rs` — `serialize_player` (Dict-Keys `line_geo`, `score_geo`,
  `scoring_tile_points`).
- `engine/py/neural_net.py` — `state_to_tensor` (Features), ggf. `MosaicNet` (Stufe 2).
- `config.py` — `INPUT_SIZE` (673).
- Referenz: `engine/src/round_end.rs` (`score_placed_tile`/`count_line`),
  `engine/src/tiling_solver.rs` (`solve_round_final_score`).

## Verifikation

1. **Feature-Sanity:** `len(state_to_tensor(state)) == INPUT_SIZE`; Linien-Features
   gegen ein Board mit bekannter Linie prüfen (Rust-Unit-Tests `line_features_*`,
   `scoring_features_*` decken das ab). ✅
2. **Frische Daten + Training:** `python self_play.py --mode mcts --games 3000
   --version s100 --sims 100 --threads 0` → `python train.py --name s100` von Null.
3. **Arena/Score-Messung (Hauptmetrik):** `python arena.py` (Netz vs. Heuristik-MCTS
   — Netz-Arena kommt mit Phase B / Network-Modus). Vergleich gegen Baseline:
   **Punkte/Stein** (>1,0 = Linien entstehen), **Ø Siegerscore** (Ziel ≫9,8),
   **0:0/Floor-Rate**. Datenseitige Sanity: `python -m utils.diagnosis`.

## Hinweis

Der Network-Modus (AlphaZero-Inferenz in Rust, Phase B) muss `state_to_tensor`
inkl. dieser Features im Rust-Port (`engine/src/features.rs`) identisch spiegeln.
