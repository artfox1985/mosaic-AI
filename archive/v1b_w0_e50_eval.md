trainiert mit

- --games 11000 --mode mcts --sims 400

value weight 0



**Netzdaten**

```
PS D:\Archiv\Documents\Projekte\mosaic-AI> python train.py --name v1w0_e50 --epochs 50 --no-early-stop
📦 Lade HDF5-Cache (990 Dateien)...
Datensatz geladen: 1501066 Züge. (Features pro Zug: 684) — 22.4s
📦 Lade HDF5-Cache (110 Dateien)...
Datensatz geladen: 167036 Züge. (Features pro Zug: 684) — 2.7s
   Val-Split: 990 Trainings-Dateien / 110 Val-Dateien (1,501,066 / 167,036 Züge)
   Value-Ziel-Streuung: σ=0.183 (Varianz=0.0334, zum Vergleich mit v_pred σ unten; Varianz ist die Baseline-MSE bei reiner Mittelwert-Vorhersage)

🚀 Starte PyTorch Training auf: CUDA
🧠 Netz-Architektur: 684→512→512→512
⚙️  Hyperparameter (config.py):
   Learning Rate : 0.0004
   Value Weight  : 0
   Batch Size    : 256
   Value-Target  : tanh(eigen/50) - 0.1*tanh(gegner/50) (Endergebnis statt Win/Loss)
   Epochen       : 50
🆕 Neues Modell: Trainiere für 50 Epochen.
Epoche  1/50 | Total Loss:   3.03 (R²=-0.95, Policy:  3.03) | Val-R²=-0.96 | v_pred μ=+0.02 σ=0.079
Epoche  2/50 | Total Loss:   2.98 (R²=-0.73, Policy:  2.98) | Val-R²=-0.76 | v_pred μ=+0.06 σ=0.096
Epoche  3/50 | Total Loss:   2.95 (R²=-0.70, Policy:  2.95) | Val-R²=-0.68 | v_pred μ=+0.06 σ=0.099
Epoche  4/50 | Total Loss:   2.93 (R²=-0.65, Policy:  2.93) | Val-R²=-0.78 | v_pred μ=+0.07 σ=0.103
Epoche  5/50 | Total Loss:   2.91 (R²=-0.70, Policy:  2.91) | Val-R²=-0.70 | v_pred μ=+0.08 σ=0.113
Epoche  6/50 | Total Loss:   2.89 (R²=-0.68, Policy:  2.89) | Val-R²=-0.70 | v_pred μ=+0.08 σ=0.109
Epoche  7/50 | Total Loss:   2.86 (R²=-0.70, Policy:  2.86) | Val-R²=-0.73 | v_pred μ=+0.08 σ=0.112
Epoche  8/50 | Total Loss:   2.83 (R²=-0.71, Policy:  2.83) | Val-R²=-0.81 | v_pred μ=+0.08 σ=0.112
Epoche  9/50 | Total Loss:   2.78 (R²=-0.71, Policy:  2.78) | Val-R²=-0.78 | v_pred μ=+0.08 σ=0.119
Epoche 10/50 | Total Loss:   2.75 (R²=-0.68, Policy:  2.75) | Val-R²=-0.75 | v_pred μ=+0.09 σ=0.119
Epoche 11/50 | Total Loss:   2.71 (R²=-0.73, Policy:  2.71) | Val-R²=-0.73 | v_pred μ=+0.08 σ=0.121
Epoche 12/50 | Total Loss:   2.67 (R²=-0.73, Policy:  2.67) | Val-R²=-0.79 | v_pred μ=+0.08 σ=0.121
Epoche 13/50 | Total Loss:   2.63 (R²=-0.78, Policy:  2.63) | Val-R²=-0.75 | v_pred μ=+0.08 σ=0.125
Epoche 14/50 | Total Loss:   2.60 (R²=-0.77, Policy:  2.60) | Val-R²=-0.79 | v_pred μ=+0.08 σ=0.127
Epoche 15/50 | Total Loss:   2.57 (R²=-0.80, Policy:  2.57) | Val-R²=-0.86 | v_pred μ=+0.09 σ=0.133
Epoche 16/50 | Total Loss:   2.55 (R²=-0.81, Policy:  2.55) | Val-R²=-0.78 | v_pred μ=+0.09 σ=0.134
Epoche 17/50 | Total Loss:   2.52 (R²=-0.79, Policy:  2.52) | Val-R²=-0.79 | v_pred μ=+0.09 σ=0.134
Epoche 18/50 | Total Loss:   2.51 (R²=-0.81, Policy:  2.51) | Val-R²=-0.86 | v_pred μ=+0.09 σ=0.135
Epoche 19/50 | Total Loss:   2.49 (R²=-0.83, Policy:  2.49) | Val-R²=-0.88 | v_pred μ=+0.08 σ=0.132
Epoche 20/50 | Total Loss:   2.47 (R²=-0.89, Policy:  2.47) | Val-R²=-1.01 | v_pred μ=+0.09 σ=0.142
Epoche 21/50 | Total Loss:   2.46 (R²=-0.87, Policy:  2.46) | Val-R²=-0.85 | v_pred μ=+0.10 σ=0.145
Epoche 22/50 | Total Loss:   2.44 (R²=-0.88, Policy:  2.44) | Val-R²=-0.97 | v_pred μ=+0.09 σ=0.141
Epoche 23/50 | Total Loss:   2.43 (R²=-0.91, Policy:  2.43) | Val-R²=-0.93 | v_pred μ=+0.08 σ=0.139
Epoche 24/50 | Total Loss:   2.42 (R²=-0.90, Policy:  2.42) | Val-R²=-0.91 | v_pred μ=+0.08 σ=0.142
Epoche 25/50 | Total Loss:   2.41 (R²=-0.94, Policy:  2.41) | Val-R²=-0.99 | v_pred μ=+0.09 σ=0.152
Epoche 26/50 | Total Loss:   2.40 (R²=-0.95, Policy:  2.40) | Val-R²=-1.07 | v_pred μ=+0.08 σ=0.147
Epoche 27/50 | Total Loss:   2.39 (R²=-0.98, Policy:  2.39) | Val-R²=-1.01 | v_pred μ=+0.08 σ=0.150
Epoche 28/50 | Total Loss:   2.38 (R²=-0.97, Policy:  2.38) | Val-R²=-0.96 | v_pred μ=+0.08 σ=0.149
Epoche 29/50 | Total Loss:   2.38 (R²=-0.96, Policy:  2.38) | Val-R²=-0.95 | v_pred μ=+0.08 σ=0.144
Epoche 30/50 | Total Loss:   2.37 (R²=-1.03, Policy:  2.37) | Val-R²=-1.05 | v_pred μ=+0.07 σ=0.147
Epoche 31/50 | Total Loss:   2.36 (R²=-1.05, Policy:  2.36) | Val-R²=-1.09 | v_pred μ=+0.07 σ=0.150
Epoche 32/50 | Total Loss:   2.36 (R²=-0.99, Policy:  2.36) | Val-R²=-0.95 | v_pred μ=+0.08 σ=0.147
Epoche 33/50 | Total Loss:   2.35 (R²=-0.96, Policy:  2.35) | Val-R²=-1.08 | v_pred μ=+0.08 σ=0.149
Epoche 34/50 | Total Loss:   2.35 (R²=-1.02, Policy:  2.35) | Val-R²=-1.03 | v_pred μ=+0.07 σ=0.147
Epoche 35/50 | Total Loss:   2.34 (R²=-1.03, Policy:  2.34) | Val-R²=-1.06 | v_pred μ=+0.08 σ=0.155
Epoche 36/50 | Total Loss:   2.33 (R²=-1.03, Policy:  2.33) | Val-R²=-1.08 | v_pred μ=+0.08 σ=0.151
Epoche 37/50 | Total Loss:   2.33 (R²=-1.12, Policy:  2.33) | Val-R²=-1.09 | v_pred μ=+0.07 σ=0.154
Epoche 38/50 | Total Loss:   2.33 (R²=-1.10, Policy:  2.33) | Val-R²=-1.10 | v_pred μ=+0.07 σ=0.154
Epoche 39/50 | Total Loss:   2.32 (R²=-1.12, Policy:  2.32) | Val-R²=-1.02 | v_pred μ=+0.07 σ=0.159
Epoche 40/50 | Total Loss:   2.32 (R²=-1.09, Policy:  2.32) | Val-R²=-1.10 | v_pred μ=+0.08 σ=0.160
Epoche 41/50 | Total Loss:   2.31 (R²=-1.14, Policy:  2.31) | Val-R²=-1.25 | v_pred μ=+0.07 σ=0.161  🟡 PLATEAU (Policy+Value)
Epoche 42/50 | Total Loss:   2.31 (R²=-1.16, Policy:  2.31) | Val-R²=-1.22 | v_pred μ=+0.08 σ=0.163  🟡 PLATEAU (Policy+Value)
Epoche 43/50 | Total Loss:   2.31 (R²=-1.19, Policy:  2.31) | Val-R²=-1.30 | v_pred μ=+0.07 σ=0.164  🟡 PLATEAU (Policy+Value)
Epoche 44/50 | Total Loss:   2.30 (R²=-1.22, Policy:  2.30) | Val-R²=-1.18 | v_pred μ=+0.07 σ=0.164  🟡 PLATEAU (Policy+Value)
Epoche 45/50 | Total Loss:   2.30 (R²=-1.22, Policy:  2.30) | Val-R²=-1.20 | v_pred μ=+0.08 σ=0.168  🟡 PLATEAU (Policy+Value)
Epoche 46/50 | Total Loss:   2.30 (R²=-1.15, Policy:  2.30) | Val-R²=-1.18 | v_pred μ=+0.08 σ=0.162  🟡 PLATEAU (Policy+Value)
Epoche 47/50 | Total Loss:   2.29 (R²=-1.18, Policy:  2.29) | Val-R²=-1.27 | v_pred μ=+0.08 σ=0.166  🟡 PLATEAU (Policy+Value)
Epoche 48/50 | Total Loss:   2.29 (R²=-1.24, Policy:  2.29) | Val-R²=-1.20 | v_pred μ=+0.08 σ=0.169  🟡 PLATEAU (Policy+Value)
Epoche 49/50 | Total Loss:   2.29 (R²=-1.16, Policy:  2.29) | Val-R²=-1.31 | v_pred μ=+0.08 σ=0.163  🟡 PLATEAU (Policy+Value)
Epoche 50/50 | Total Loss:   2.28 (R²=-1.17, Policy:  2.28) | Val-R²=-1.21 | v_pred μ=+0.08 σ=0.164  🟡 PLATEAU (Policy+Value)

=======================================================
  PHASE 2: VALUE-KALIBRIERUNG (Trunk/Policy eingefroren)
───────────────────────────────────────────────────────
  Kalibrierung  1/50 | Val-R²=+0.219  (bislang bester: Epoche 1)
  Kalibrierung  2/50 | Val-R²=+0.219  (bislang bester: Epoche 1)
  Kalibrierung  3/50 | Val-R²=+0.216  (bislang bester: Epoche 1)
  Kalibrierung  4/50 | Val-R²=+0.216  (bislang bester: Epoche 1)
  Kalibrierung  5/50 | Val-R²=+0.208  (bislang bester: Epoche 1)
  Kalibrierung  6/50 | Val-R²=+0.211  (bislang bester: Epoche 1)
  Kalibrierung  7/50 | Val-R²=+0.210  (bislang bester: Epoche 1)
  Kalibrierung  8/50 | Val-R²=+0.209  (bislang bester: Epoche 1)
  Kalibrierung  9/50 | Val-R²=+0.204  (bislang bester: Epoche 1)
  ⏹️  Kalibrierung gestoppt: Val-R² seit Epoche 1 nicht mehr verbessert (Bestwert 0.219).
  ✅ Value-Head auf besten Kalibrierungs-Stand zurückgesetzt (Epoche 1, Val-R²=0.219).
=======================================================

=======================================================
  TRAINING SUMMARY
=======================================================
  Epochen:       50
  Züge:          1,501,066  (+167,036 Val, nie trainiert)
  Batches/Epoche:5863
───────────────────────────────────────────────────────
  Policy Loss:   2.2836 / 6.18 max  (37.0%)  🟡 Gut
  Value Loss:    0.0257  (R²=0.23 ggü. Mittelwert-Baseline)  🟠 Schwaches Signal
  Value Val-R²:  0.22  (Gap ggü. Train: +0.01)  🟢 Train/Val nah beieinander
───────────────────────────────────────────────────────
  ℹ️  Phase 1 Val-R² war in Epoche 3 am besten (-0.68), danach Überfitten (normal — Value trainiert bewusst bis zum Ende mit).
  🎯 Phase 2 (Value-Kalibrierung): bester Stand nach Epoche 1, Val-R²=0.22 — Wert oben spiegelt diesen kalibrierten Value-Head wider.
  🟡 Plateau ab Epoche 41.
     → Für nächste Generation: mehr Sims im Self-Play.
=======================================================

=======================================================
  NETZAUSLASTUNG (Hidden Size: 512)
───────────────────────────────────────────────────────
  Schicht          Dead   Aktiv-Rate        Eff.Rank
  ───────────────────────────────────────────────────
  layer1     0/512 (0%)          40%   218/512 (43%)
  layer2     0/512 (0%)          40%   194/512 (38%)
  layer3    72/512 (14%)          11%   180/512 (35%)
  ───────────────────────────────────────────────────
  🟢 Gesunde Auslastung (Dead 5%, Rank 39%).
=======================================================

✅ Training beendet! Neues Model gespeichert unter:
📂 D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v1w0_e50.pth
📈 Loss-Verlauf gespeichert unter:
📂 D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v1w0_e50_loss.png
✅ Exportiert: D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v1w0_e50.onnx  (input=684, hidden=512, value_hidden=64, opset=13)
📎 Referenz für Rust-Parität: D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v1w0_e50.onnx.ref.txt

=======================================================
  STUFE 1 vs. STUFE 2 (max. 50 Spiele, 200 Sims, Early-Stop)
───────────────────────────────────────────────────────
🏟️ Mosaic-AI ARENA — Netz vs Netz (Rust) 🏟️
  v1w0_e50(Stufe1) (Brett 0, 200 Sims, c_puct=1.5, Stufe 1/DFS-Blatt) vs v1w0_e50(Stufe2) (Brett 1, 200 Sims, c_puct=1.5, Stufe 2/Netz-Value-Blatt) — 50 Spiele
--------------------------------------------------
  #  1/50:  16:0   -> v1w0_e50(Stufe1)       | Züge 154 | Strength 0.730 | Stand v1w0_e50(Stufe1) 1:0 v1w0_e50(Stufe2) | Elo 1012/988
  #  2/50:  52:8   -> v1w0_e50(Stufe1)       | Züge 163 | Strength 1.000 | Stand v1w0_e50(Stufe1) 2:0 v1w0_e50(Stufe2) | Elo 1027/973
  #  3/50:  20:5   -> v1w0_e50(Stufe1)       | Züge 155 | Strength 0.775 | Stand v1w0_e50(Stufe1) 3:0 v1w0_e50(Stufe2) | Elo 1037/963
  #  4/50:  31:0   -> v1w0_e50(Stufe1)       | Züge 148 | Strength 0.899 | Stand v1w0_e50(Stufe1) 4:0 v1w0_e50(Stufe2) | Elo 1048/952
  #  5/50:  48:28  -> v1w0_e50(Stufe1)       | Züge 171 | Strength 1.000 | Stand v1w0_e50(Stufe1) 5:0 v1w0_e50(Stufe2) | Elo 1060/940
  #  6/50:  25:16  -> v1w0_e50(Stufe1)       | Züge 153 | Strength 0.651 | Stand v1w0_e50(Stufe1) 6:0 v1w0_e50(Stufe2) | Elo 1067/933
  #  7/50:   4:4   -> v1w0_e50(Stufe2)       | Züge 154 | Strength 0.145 | Stand v1w0_e50(Stufe1) 6:1 v1w0_e50(Stufe2) | Elo 1064/936
  #  8/50:  19:19  -> v1w0_e50(Stufe2)       | Züge 158 | Strength 0.314 | Stand v1w0_e50(Stufe1) 6:2 v1w0_e50(Stufe2) | Elo 1057/943
  #  9/50:  30:0   -> v1w0_e50(Stufe1)       | Züge 158 | Strength 0.888 | Stand v1w0_e50(Stufe1) 7:2 v1w0_e50(Stufe2) | Elo 1067/933
  # 10/50:  45:17  -> v1w0_e50(Stufe1)       | Züge 156 | Strength 1.000 | Stand v1w0_e50(Stufe1) 8:2 v1w0_e50(Stufe2) | Elo 1077/923
  # 11/50:  24:21  -> v1w0_e50(Stufe1)       | Züge 163 | Strength 0.460 | Stand v1w0_e50(Stufe1) 9:2 v1w0_e50(Stufe2) | Elo 1081/919
  ⏹️  Vorzeitig entschieden: v1w0_e50(Stufe1) hat nach 11 Spielen bereits 9 Siege (95%-Signifikanz für >50% Gewinnchance).
--------------------------------------------------
🏆 ERGEBNIS: v1w0_e50(Stufe1) 9:2 v1w0_e50(Stufe2) (82% A-Siege) in 390.3s (0.0 Spiele/s)  [vorzeitig nach 11/50 Spielen]
   Ø Score: v1w0_e50(Stufe1) 28.5 | v1w0_e50(Stufe2) 10.7
   0:0-Spiele: 0/11 (0.0%)
   Elo: v1w0_e50(Stufe1) 1081 | v1w0_e50(Stufe2) 919
=======================================================
```

Bemerkenswert: obwohl der Trunk in Phase 1 NULL Value-Gradient bekam (Value
R² bleibt durchgehend negativ, das Netz lernt Value hier gar nicht), erreicht
ein frisch initialisierter Value-Head in Phase 2 gegen genau diesen Trunk
trotzdem Val-R²=0.22 — fast identisch mit v1b_w15_e50s 0.24 (siehe dort). Der
rein policy-trainierte Trunk liefert also fast gleich gute Repräsentationen
für die Value-Vorhersage wie einer, der die ganze Zeit mit vollem
VALUE_WEIGHT=15 mittrainiert wurde.

**Confounder-Arena (v1b_w15_e50 vs. v1b_w0_e50, A-vs-B, 100 Spiele, kein
Early-Stop, 200 Sims, Stufe 1)**

```
🏆 ERGEBNIS: v1b_w15_e50 50:50 v1b_w0_e50 (50% A-Siege) in 1877.4s
   Ø Score: v1b_w15_e50 32.7 | v1b_w0_e50 31.0
   0:0-Spiele: 0/100 (0.0%)
   Elo: v1b_w15_e50 1020 | v1b_w0_e50 980
```

Exaktes 50:50 bei n=100 — kein messbarer Unterschied zwischen VALUE_WEIGHT=15
und VALUE_WEIGHT=0 bei gleicher Trainingsdauer (50 Epochen, kein Early-Stop).
Stützt die Hypothese, dass der frühere scheinbare Vorteil von hohem
Value-Weight (v1 vs. v1b, altes Reset-Cycle) an der längeren Trainingsdauer
lag (Value plateaut später als Policy, das Stop-Kriterium ließ den
Value-Weight-15-Lauf daher länger trainieren), nicht am Value-Gradienten
selbst.

**Arena vs. Heuristik**

Nicht getestet — dieses Modell wurde nur im direkten Confounder-Vergleich
gegen v1b_w15_e50 eingesetzt, nicht gegen die Heuristik.
