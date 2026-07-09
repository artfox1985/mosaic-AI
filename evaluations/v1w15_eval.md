trainiert mit

- --games 11000 --mode mcts --sims 400

value weight 15



**Netzdaten**

```
Lade Daten aus 990 Dateien...
Datensatz geladen: 1501066 Züge. (Features pro Zug: 684) — 573.4s
Lade Daten aus 110 Dateien...
Datensatz geladen: 167036 Züge. (Features pro Zug: 684) — 67.9s
   Val-Split: 990 Trainings-Dateien / 110 Val-Dateien (1,501,066 / 167,036 Züge)
   Value-Ziel-Streuung: σ=0.183 (Varianz=0.0334)

🚀 Starte PyTorch Training auf: CUDA
🧠 Netz-Architektur: 684→512→512→512
⚙️  Hyperparameter (config.py):
   Learning Rate : 0.0004
   Value Weight  : 15
   Batch Size    : 256
   Epochen       : 100
🆕 Neues Modell: Trainiere für 100 Epochen.
Epoche  1/100 | Total Loss:   3.21 (R²=+0.68, Policy:  3.05) | Val-R²=+0.26 | v_pred μ=+0.19 σ=0.151
Epoche  2/100 | Total Loss:   3.09 (R²=+0.86, Policy:  3.01) | Val-R²=+0.27 | v_pred μ=+0.19 σ=0.169
...
🧊 Value-Head eingefroren: Val-R² seit Epoche 2 nicht mehr verbessert (Bestwert 0.27, jetzt 0.23) — Gewichte auf Epoche 2 zurückgesetzt, Policy trainiert unbeeinflusst weiter.
Epoche 11/100 | Total Loss:   2.68 (R²=+0.62, Policy:  2.68) | Val-R²=+0.05 | v_pred μ=+0.23 σ=0.213
...
Epoche 47/100 | Total Loss:   2.29 (R²=-0.29, Policy:  2.29) | Val-R²=-0.87 | v_pred μ=+0.29 σ=0.236  🟡 PLATEAU (Policy+Value)

⏹️  Early Stopping: Policy+Value plateaut seit Epoche 42 (5 Epochen ohne Fortschritt).

=======================================================
  TRAINING SUMMARY
=======================================================
  Epochen:       100
  Züge:          1,501,066  (+167,036 Val, nie trainiert)
  Batches/Epoche:5863
───────────────────────────────────────────────────────
  Policy Loss:   2.2917 / 6.18 max  (37.1%)  🟡 Gut
  Value Loss:    0.0431  (R²=-0.29 ggü. Mittelwert-Baseline)  🔴 Nichts gelernt
  Value Val-R²:  -0.87  (Gap ggü. Train: +0.58)  ⚠️  großer Train/Val-Abstand — Overfitting wahrscheinlich
───────────────────────────────────────────────────────
  🧊 Value-Head eingefroren seit Epoche 10/100 (Gewichte von Epoche 2, bestes Val-R²=0.27) — Policy trainierte darüber hinaus unbeeinflusst weiter.
  ⏹️  Early Stopping (Policy+Value-Plateau) nach Epoche 47/100
=======================================================

NETZAUSLASTUNG: Dead 2%, Eff.Rank 42% — 🟢 gesund

✅ Exportiert: models/alphazero_v1w15.onnx (input=684, hidden=512, value_hidden=64)
```

Auffällig: der eingefrorene Value-Head kollabiert TROTZ Freeze (Val-R² 0.27→-0.87),
weil der gemeinsame Trunk nach dem Freeze noch ~37 Epochen rein auf Policy
weitertrainiert und dabei so driftet, dass die fixen Value-Head-Gewichte auf
den neuen Trunk-Features immer schlechter passen. Betrifft nur Stufe 2 (siehe
unten) — Stufe 1 nutzt den Value-Head beim Spielen nicht.

**Stage 1 vs. Stage 2**

```
STUFE 1 vs. STUFE 2 (max. 50 Spiele, 200 Sims, Early-Stop)
🏆 ERGEBNIS: v1w15(Stufe1) 10:0 v1w15(Stufe2) (100% A-Siege) in 116.9s  [vorzeitig nach 10/50 Spielen]
   Ø Score: v1w15(Stufe1) 35.0 | v1w15(Stufe2) 5.5
   0:0-Spiele: 0/10 (0.0%)
   Elo: v1w15(Stufe1) 1097 | v1w15(Stufe2) 903
```

Vorzeitig entschieden (9/10 Siege für Stufe 1 nach 10 Spielen) — Stufe 2
komplett chancenlos, konsistent mit dem kollabierten Value-Head oben.

**Arena vs. Heuristik**

```
v1w15 (Brett 0, 200 Sims, Stufe 1/DFS-Blatt) vs Heuristik(s200) (Brett 1, 200 Sims) — 100 Spiele
⏹️  Vorzeitig entschieden: Heuristik(s200) hat nach 21 Spielen bereits 15 Siege (95%-Signifikanz für >50% Gewinnchance).
🏆 ERGEBNIS: v1w15 6:15 Heuristik(s200) (29% Netz-Siege) in 445.6s  [vorzeitig nach 21/100 Spielen]
   Ø Score: v1w15 31.0 | Heuristik(s200) 49.8
   0:0-Spiele: 0/21 (0.0%)
   Ø Floor-Strafe: v1w15 14.8 | Heuristik(s200) 8.2
   Elo: v1w15 917 | Heuristik(s200) 1083
```
