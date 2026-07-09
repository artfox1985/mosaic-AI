trainiert mit

- --games 11000 --mode mcts --sims 400

value weight 8



**Netzdaten**

```
Datensatz geladen: 1501066 Züge. (Features pro Zug: 684)
Val-Split: 990 Trainings-Dateien / 110 Val-Dateien (1,501,066 / 167,036 Züge)
Value-Ziel-Streuung: σ=0.183 (Varianz=0.0334)

Hyperparameter: Learning Rate 0.0004, Value Weight 8, Batch Size 256
Epoche  1/100 | Total Loss:   3.13 (R²=+0.64, Policy:  3.04) | Val-R²=+0.28
Epoche  2/100 | Total Loss:   3.04 (R²=+0.82, Policy:  3.00) | Val-R²=+0.27
...
🧊 Value-Head eingefroren: Val-R² seit Epoche 1 nicht mehr verbessert (Bestwert 0.28, jetzt 0.23) — Gewichte auf Epoche 1 zurückgesetzt, Policy trainiert unbeeinflusst weiter.
...
Epoche 46/100 | Total Loss:   2.29 (R²=-0.07, Policy:  2.29) | Val-R²=-0.46  🟡 PLATEAU (Policy+Value)

⏹️  Early Stopping: Policy+Value plateaut seit Epoche 41 (5 Epochen ohne Fortschritt).

=======================================================
  TRAINING SUMMARY
=======================================================
  Epochen:       100
  Züge:          1,501,066  (+167,036 Val, nie trainiert)
───────────────────────────────────────────────────────
  Policy Loss:   2.2946 / 6.18 max  (37.1%)  🟡 Gut
  Value Loss:    0.0358  (R²=-0.07 ggü. Mittelwert-Baseline)  🔴 Nichts gelernt
  Value Val-R²:  -0.46  (Gap ggü. Train: +0.39)  ⚠️  großer Train/Val-Abstand — Overfitting wahrscheinlich
───────────────────────────────────────────────────────
  🧊 Value-Head eingefroren seit Epoche 9/100 (Gewichte von Epoche 1, bestes Val-R²=0.28)
  ⏹️  Early Stopping (Policy+Value-Plateau) nach Epoche 46/100
=======================================================

NETZAUSLASTUNG: Dead 3%, Eff.Rank 41% — 🟢 gesund

✅ Exportiert: models/alphazero_v1w8.onnx (input=684, hidden=512, value_hidden=64)
```

Gleiches Muster wie v1w15: Value-Head friert früh ein (Epoche 1), kollabiert
trotzdem weiter (Val-R² 0.28→-0.46), weil der Trunk danach rein auf Policy
weitertrainiert und driftet.

**Stage 1 vs. Stage 2**

```
STUFE 1 vs. STUFE 2 (max. 50 Spiele, 200 Sims, Early-Stop)
🏆 ERGEBNIS: v1w8(Stufe1) 9:1 v1w8(Stufe2) (90% A-Siege) in 116.5s  [vorzeitig nach 10/50 Spielen]
   Ø Score: v1w8(Stufe1) 34.5 | v1w8(Stufe2) 12.7
   0:0-Spiele: 1/10 (10.0%)
   Elo: v1w8(Stufe1) 1091 | v1w8(Stufe2) 909
```

**Arena vs. Heuristik**

```
v1w8 (Brett 0, 200 Sims, Stufe 1/DFS-Blatt) vs Heuristik(s200) (Brett 1, 200 Sims) — 100 Spiele
⏹️  Vorzeitig entschieden: Heuristik(s200) hat nach 10 Spielen bereits 9 Siege (95%-Signifikanz für >50% Gewinnchance).
🏆 ERGEBNIS: v1w8 1:9 Heuristik(s200) (10% Netz-Siege) in 150.7s  [vorzeitig nach 10/100 Spielen]
   Ø Score: v1w8 26.5 | Heuristik(s200) 47.0
   0:0-Spiele: 0/10 (0.0%)
   Ø Floor-Strafe: v1w8 16.4 | Heuristik(s200) 8.7
   Elo: v1w8 913 | Heuristik(s200) 1087
```
