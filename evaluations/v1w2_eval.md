trainiert mit

- --games 11000 --mode mcts --sims 400

value weight 2



**Netzdaten**

```
Datensatz geladen: 1501066 Züge. (Features pro Zug: 684)
Val-Split: 990 Trainings-Dateien / 110 Val-Dateien (1,501,066 / 167,036 Züge)
Value-Ziel-Streuung: σ=0.183 (Varianz=0.0334)

Hyperparameter: Learning Rate 0.0004, Value Weight 2, Batch Size 256
Epoche  1/100 | Total Loss:   3.06 (R²=+0.53, Policy:  3.03) | Val-R²=+0.35
Epoche  2/100 | Total Loss:   3.00 (R²=+0.65, Policy:  2.98) | Val-R²=+0.30
...
🧊 Value-Head eingefroren: Val-R² seit Epoche 1 nicht mehr verbessert (Bestwert 0.35, jetzt 0.29) — Gewichte auf Epoche 1 zurückgesetzt, Policy trainiert unbeeinflusst weiter.
...
Epoche 47/100 | Total Loss:   2.29 (R²=+0.25, Policy:  2.29) | Val-R²=+0.07  🟡 PLATEAU (Policy+Value)

⏹️  Early Stopping: Policy+Value plateaut seit Epoche 42 (5 Epochen ohne Fortschritt).

=======================================================
  TRAINING SUMMARY
=======================================================
  Epochen:       100
  Züge:          1,501,066  (+167,036 Val, nie trainiert)
───────────────────────────────────────────────────────
  Policy Loss:   2.2938 / 6.18 max  (37.1%)  🟡 Gut
  Value Loss:    0.0251  (R²=0.25 ggü. Mittelwert-Baseline)  🟠 Schwaches Signal
  Value Val-R²:  0.07  (Gap ggü. Train: +0.17)  🟡 spürbarer Train/Val-Abstand — im Auge behalten
───────────────────────────────────────────────────────
  🧊 Value-Head eingefroren seit Epoche 9/100 (Gewichte von Epoche 1, bestes Val-R²=0.35)
  ⏹️  Early Stopping (Policy+Value-Plateau) nach Epoche 47/100
=======================================================

NETZAUSLASTUNG: Dead 6%, Eff.Rank 39% — 🟢 gesund

✅ Exportiert: models/alphazero_v1w2.onnx (input=684, hidden=512, value_hidden=64)
```

Schwächster Value-Kollaps aller vier Varianten (Val-R² bleibt bei +0.07 statt
ins Negative zu rutschen wie bei v1w15/v1w8/v1w4) — passt zum Trend: je
niedriger VALUE_WEIGHT, desto weniger "wertvolle" Trunk-Repräsentation baut
sich vor dem Freeze überhaupt auf, also desto weniger geht beim
anschließenden reinen Policy-Training verloren.

**Stage 1 vs. Stage 2**

```
STUFE 1 vs. STUFE 2 (max. 50 Spiele, 200 Sims, Early-Stop)
🏆 ERGEBNIS: v1w2(Stufe1) 9:1 v1w2(Stufe2) (90% A-Siege) in 122.1s  [vorzeitig nach 10/50 Spielen]
   Ø Score: v1w2(Stufe1) 31.7 | v1w2(Stufe2) 7.9
   0:0-Spiele: 0/10 (0.0%)
   Elo: v1w2(Stufe1) 1077 | v1w2(Stufe2) 923
```

**Arena vs. Heuristik**

```

```
