trainiert mit

- --games 11000 --mode mcts --sims 400

value weight 4



**Netzdaten**

```
Datensatz geladen: 1501066 Züge. (Features pro Zug: 684)
Val-Split: 990 Trainings-Dateien / 110 Val-Dateien (1,501,066 / 167,036 Züge)
Value-Ziel-Streuung: σ=0.183 (Varianz=0.0334)

Hyperparameter: Learning Rate 0.0004, Value Weight 4, Batch Size 256
Epoche  1/100 | Total Loss:   3.09 (R²=+0.58, Policy:  3.03) | Val-R²=+0.30
Epoche  2/100 | Total Loss:   3.02 (R²=+0.74, Policy:  2.98) | Val-R²=+0.27
...
🧊 Value-Head eingefroren: Val-R² seit Epoche 1 nicht mehr verbessert (Bestwert 0.30, jetzt 0.26) — Gewichte auf Epoche 1 zurückgesetzt, Policy trainiert unbeeinflusst weiter.
...
Epoche 46/100 | Total Loss:   2.30 (R²=+0.19, Policy:  2.30) | Val-R²=-0.06  🟡 PLATEAU (Policy+Value)

⏹️  Early Stopping: Policy+Value plateaut seit Epoche 41 (5 Epochen ohne Fortschritt).

=======================================================
  TRAINING SUMMARY
=======================================================
  Epochen:       100
  Züge:          1,501,066  (+167,036 Val, nie trainiert)
───────────────────────────────────────────────────────
  Policy Loss:   2.3036 / 6.18 max  (37.3%)  🟡 Gut
  Value Loss:    0.0269  (R²=0.19 ggü. Mittelwert-Baseline)  🟠 Schwaches Signal
  Value Val-R²:  -0.06  (Gap ggü. Train: +0.26)  🟡 spürbarer Train/Val-Abstand — im Auge behalten
───────────────────────────────────────────────────────
  🧊 Value-Head eingefroren seit Epoche 9/100 (Gewichte von Epoche 1, bestes Val-R²=0.30)
  ⏹️  Early Stopping (Policy+Value-Plateau) nach Epoche 46/100
=======================================================

NETZAUSLASTUNG: Dead 4%, Eff.Rank 40% — 🟢 gesund

✅ Exportiert: models/alphazero_v1w4.onnx (input=684, hidden=512, value_hidden=64)
```

Der Value-Head-Kollaps nach dem Freeze ist hier deutlich milder als bei
v1w15/v1w8 (Val-R² landet bei -0.06 statt -0.46/-0.87) — plausibel, da der
Trunk bei niedrigerem VALUE_WEIGHT von Anfang an weniger stark auf Value
optimiert war, also beim anschließenden reinen Policy-Training auch weniger
"wertvolle" Repräsentation zu verlieren hat.

**Stage 1 vs. Stage 2**

```
STUFE 1 vs. STUFE 2 (max. 50 Spiele, 200 Sims, Early-Stop)
🏆 ERGEBNIS: v1w4(Stufe1) 9:2 v1w4(Stufe2) (82% A-Siege) in 222.9s  [vorzeitig nach 11/50 Spielen]
   Ø Score: v1w4(Stufe1) 33.5 | v1w4(Stufe2) 12.2
   0:0-Spiele: 0/11 (0.0%)
   Elo: v1w4(Stufe1) 1079 | v1w4(Stufe2) 921
```

**Arena vs. Heuristik**

```
v1w4 (Brett 0, 200 Sims, Stufe 1/DFS-Blatt) vs Heuristik(s200) (Brett 1, 200 Sims) — 100 Spiele
⏹️  Vorzeitig entschieden: Heuristik(s200) hat nach 29 Spielen bereits 20 Siege (95%-Signifikanz für >50% Gewinnchance).
🏆 ERGEBNIS: v1w4 9:20 Heuristik(s200) (31% Netz-Siege) in 502.7s  [vorzeitig nach 29/100 Spielen]
   Ø Score: v1w4 30.6 | Heuristik(s200) 44.2
   0:0-Spiele: 0/29 (0.0%)
   Ø Floor-Strafe: v1w4 17.2 | Heuristik(s200) 11.9
   Elo: v1w4 909 | Heuristik(s200) 1091
```
