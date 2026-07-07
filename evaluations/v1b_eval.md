trainiert mit 6000x mcts sims 400 daten

**Netzdaten**

```
PS D:\Archiv\Documents\Projekte\mosaic-AI> python train.py --name v1b --epochs 100
📦 Lade HDF5-Cache (600 Dateien)...
Datensatz geladen: 909891 Züge. (Features pro Zug: 684) — 11.3s
   Value-Ziel-Streuung: σ=0.182 (Varianz=0.0332, zum Vergleich mit v_pred σ unten; Varianz ist die Baseline-MSE bei reiner Mittelwert-Vorhersage)

🚀 Starte PyTorch Training auf: CUDA
🧠 Netz-Architektur: 684→512→512→512
⚙️  Hyperparameter (config.py):
   Learning Rate : 0.0004
   Value Weight  : 2.5
   Batch Size    : 256
   Value-Target  : tanh(eigen/50) - 0.1*tanh(gegner/50) (Endergebnis statt Win/Loss)
   Epochen       : 100
🆕 Neues Modell: Trainiere für 100 Epochen.
Epoche  1/100 | Total Loss:   3.08 (R²=+0.58, Policy:  3.05) | v_pred μ=+0.18 σ=0.140
Epoche  2/100 | Total Loss:   3.02 (R²=+0.74, Policy:  3.00) | v_pred μ=+0.18 σ=0.158
Epoche  3/100 | Total Loss:   2.99 (R²=+0.77, Policy:  2.97) | v_pred μ=+0.18 σ=0.161
Epoche  4/100 | Total Loss:   2.96 (R²=+0.77, Policy:  2.94) | v_pred μ=+0.18 σ=0.161
Epoche  5/100 | Total Loss:   2.93 (R²=+0.76, Policy:  2.91) | v_pred μ=+0.18 σ=0.159
Epoche  6/100 | Total Loss:   2.89 (R²=+0.74, Policy:  2.87) | v_pred μ=+0.18 σ=0.158
Epoche  7/100 | Total Loss:   2.84 (R²=+0.73, Policy:  2.82) | v_pred μ=+0.18 σ=0.156
Epoche  8/100 | Total Loss:   2.78 (R²=+0.71, Policy:  2.75) | v_pred μ=+0.18 σ=0.154
Epoche  9/100 | Total Loss:   2.71 (R²=+0.70, Policy:  2.69) | v_pred μ=+0.18 σ=0.153
Epoche 10/100 | Total Loss:   2.66 (R²=+0.70, Policy:  2.63) | v_pred μ=+0.18 σ=0.153
Epoche 11/100 | Total Loss:   2.61 (R²=+0.69, Policy:  2.58) | v_pred μ=+0.18 σ=0.152
Epoche 12/100 | Total Loss:   2.57 (R²=+0.69, Policy:  2.54) | v_pred μ=+0.18 σ=0.152
Epoche 13/100 | Total Loss:   2.54 (R²=+0.69, Policy:  2.51) | v_pred μ=+0.18 σ=0.152
Epoche 14/100 | Total Loss:   2.51 (R²=+0.69, Policy:  2.48) | v_pred μ=+0.18 σ=0.151
Epoche 15/100 | Total Loss:   2.49 (R²=+0.68, Policy:  2.46) | v_pred μ=+0.18 σ=0.151
Epoche 16/100 | Total Loss:   2.47 (R²=+0.69, Policy:  2.44) | v_pred μ=+0.18 σ=0.151
Epoche 17/100 | Total Loss:   2.45 (R²=+0.69, Policy:  2.42) | v_pred μ=+0.18 σ=0.151
Epoche 18/100 | Total Loss:   2.43 (R²=+0.69, Policy:  2.41) | v_pred μ=+0.18 σ=0.151
Epoche 19/100 | Total Loss:   2.42 (R²=+0.69, Policy:  2.39) | v_pred μ=+0.18 σ=0.152
Epoche 20/100 | Total Loss:   2.41 (R²=+0.69, Policy:  2.38) | v_pred μ=+0.18 σ=0.152
Epoche 21/100 | Total Loss:   2.40 (R²=+0.69, Policy:  2.37) | v_pred μ=+0.18 σ=0.152
Epoche 22/100 | Total Loss:   2.39 (R²=+0.69, Policy:  2.36) | v_pred μ=+0.18 σ=0.152
Epoche 23/100 | Total Loss:   2.38 (R²=+0.69, Policy:  2.36) | v_pred μ=+0.18 σ=0.152
Epoche 24/100 | Total Loss:   2.37 (R²=+0.69, Policy:  2.35) | v_pred μ=+0.18 σ=0.152
Epoche 25/100 | Total Loss:   2.36 (R²=+0.70, Policy:  2.34) | v_pred μ=+0.18 σ=0.152
Epoche 26/100 | Total Loss:   2.36 (R²=+0.70, Policy:  2.33) | v_pred μ=+0.18 σ=0.153
Epoche 27/100 | Total Loss:   2.35 (R²=+0.70, Policy:  2.33) | v_pred μ=+0.18 σ=0.153
Epoche 28/100 | Total Loss:   2.34 (R²=+0.70, Policy:  2.32) | v_pred μ=+0.18 σ=0.153
Epoche 29/100 | Total Loss:   2.33 (R²=+0.70, Policy:  2.31) | v_pred μ=+0.18 σ=0.153
Epoche 30/100 | Total Loss:   2.33 (R²=+0.70, Policy:  2.31) | v_pred μ=+0.18 σ=0.153
Epoche 31/100 | Total Loss:   2.32 (R²=+0.70, Policy:  2.30) | v_pred μ=+0.18 σ=0.153
Epoche 32/100 | Total Loss:   2.32 (R²=+0.70, Policy:  2.30) | v_pred μ=+0.18 σ=0.153
Epoche 33/100 | Total Loss:   2.31 (R²=+0.71, Policy:  2.29) | v_pred μ=+0.18 σ=0.154
Epoche 34/100 | Total Loss:   2.31 (R²=+0.71, Policy:  2.28) | v_pred μ=+0.18 σ=0.154
Epoche 35/100 | Total Loss:   2.30 (R²=+0.71, Policy:  2.28) | v_pred μ=+0.18 σ=0.154
Epoche 36/100 | Total Loss:   2.30 (R²=+0.71, Policy:  2.28) | v_pred μ=+0.18 σ=0.154
Epoche 37/100 | Total Loss:   2.30 (R²=+0.71, Policy:  2.27) | v_pred μ=+0.18 σ=0.154
Epoche 38/100 | Total Loss:   2.29 (R²=+0.71, Policy:  2.27) | v_pred μ=+0.18 σ=0.154
Epoche 39/100 | Total Loss:   2.29 (R²=+0.71, Policy:  2.26) | v_pred μ=+0.18 σ=0.154
Epoche 40/100 | Total Loss:   2.28 (R²=+0.71, Policy:  2.26) | v_pred μ=+0.18 σ=0.154  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 41/100 | Total Loss:   2.28 (R²=+0.71, Policy:  2.26) | v_pred μ=+0.18 σ=0.155  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 42/100 | Total Loss:   2.27 (R²=+0.72, Policy:  2.25) | v_pred μ=+0.18 σ=0.155  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 43/100 | Total Loss:   2.27 (R²=+0.72, Policy:  2.25) | v_pred μ=+0.18 σ=0.155  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 44/100 | Total Loss:   2.27 (R²=+0.72, Policy:  2.25) | v_pred μ=+0.18 σ=0.155  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 45/100 | Total Loss:   2.27 (R²=+0.72, Policy:  2.24) | v_pred μ=+0.18 σ=0.155  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 46/100 | Total Loss:   2.26 (R²=+0.72, Policy:  2.24) | v_pred μ=+0.18 σ=0.155  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 47/100 | Total Loss:   2.26 (R²=+0.72, Policy:  2.23) | v_pred μ=+0.18 σ=0.155  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 48/100 | Total Loss:   2.26 (R²=+0.72, Policy:  2.23) | v_pred μ=+0.18 σ=0.156  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 49/100 | Total Loss:   2.25 (R²=+0.72, Policy:  2.23) | v_pred μ=+0.18 σ=0.156  🟡 POLICY-PLATEAU
Epoche 50/100 | Total Loss:   2.25 (R²=+0.72, Policy:  2.23) | v_pred μ=+0.18 σ=0.156  🟡 POLICY-PLATEAU
Epoche 51/100 | Total Loss:   2.25 (R²=+0.73, Policy:  2.22) | v_pred μ=+0.18 σ=0.156  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 52/100 | Total Loss:   2.25 (R²=+0.73, Policy:  2.22) | v_pred μ=+0.18 σ=0.156  🟡 POLICY-PLATEAU
Epoche 53/100 | Total Loss:   2.24 (R²=+0.73, Policy:  2.22) | v_pred μ=+0.18 σ=0.156  🟡 POLICY-PLATEAU
Epoche 54/100 | Total Loss:   2.24 (R²=+0.73, Policy:  2.22) | v_pred μ=+0.18 σ=0.156  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 55/100 | Total Loss:   2.24 (R²=+0.73, Policy:  2.21) | v_pred μ=+0.18 σ=0.156  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 56/100 | Total Loss:   2.23 (R²=+0.73, Policy:  2.21) | v_pred μ=+0.18 σ=0.156  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 57/100 | Total Loss:   2.23 (R²=+0.73, Policy:  2.21) | v_pred μ=+0.18 σ=0.156  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 58/100 | Total Loss:   2.23 (R²=+0.73, Policy:  2.20) | v_pred μ=+0.18 σ=0.156  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 59/100 | Total Loss:   2.23 (R²=+0.73, Policy:  2.20) | v_pred μ=+0.18 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 60/100 | Total Loss:   2.22 (R²=+0.73, Policy:  2.20) | v_pred μ=+0.18 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 61/100 | Total Loss:   2.22 (R²=+0.74, Policy:  2.20) | v_pred μ=+0.18 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 62/100 | Total Loss:   2.22 (R²=+0.74, Policy:  2.20) | v_pred μ=+0.18 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 63/100 | Total Loss:   2.22 (R²=+0.74, Policy:  2.19) | v_pred μ=+0.18 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 64/100 | Total Loss:   2.21 (R²=+0.74, Policy:  2.19) | v_pred μ=+0.18 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 65/100 | Total Loss:   2.21 (R²=+0.74, Policy:  2.19) | v_pred μ=+0.18 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 66/100 | Total Loss:   2.21 (R²=+0.74, Policy:  2.19) | v_pred μ=+0.18 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 67/100 | Total Loss:   2.21 (R²=+0.74, Policy:  2.18) | v_pred μ=+0.18 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 68/100 | Total Loss:   2.21 (R²=+0.74, Policy:  2.18) | v_pred μ=+0.18 σ=0.157  🟡 POLICY-PLATEAU
Epoche 69/100 | Total Loss:   2.20 (R²=+0.74, Policy:  2.18) | v_pred μ=+0.18 σ=0.157  🟡 POLICY-PLATEAU
Epoche 70/100 | Total Loss:   2.20 (R²=+0.74, Policy:  2.18) | v_pred μ=+0.18 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 71/100 | Total Loss:   2.20 (R²=+0.74, Policy:  2.18) | v_pred μ=+0.18 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 72/100 | Total Loss:   2.20 (R²=+0.74, Policy:  2.18) | v_pred μ=+0.18 σ=0.158  🟡 POLICY-PLATEAU
Epoche 73/100 | Total Loss:   2.19 (R²=+0.74, Policy:  2.17) | v_pred μ=+0.18 σ=0.158  🟡 POLICY-PLATEAU
Epoche 74/100 | Total Loss:   2.19 (R²=+0.74, Policy:  2.17) | v_pred μ=+0.18 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 75/100 | Total Loss:   2.19 (R²=+0.74, Policy:  2.17) | v_pred μ=+0.18 σ=0.158  🟡 POLICY-PLATEAU
Epoche 76/100 | Total Loss:   2.19 (R²=+0.75, Policy:  2.17) | v_pred μ=+0.18 σ=0.158  🟡 POLICY-PLATEAU
Epoche 77/100 | Total Loss:   2.19 (R²=+0.75, Policy:  2.17) | v_pred μ=+0.18 σ=0.158  🟡 POLICY-PLATEAU
Epoche 78/100 | Total Loss:   2.19 (R²=+0.75, Policy:  2.17) | v_pred μ=+0.18 σ=0.158  🟡 POLICY-PLATEAU
Epoche 79/100 | Total Loss:   2.19 (R²=+0.75, Policy:  2.17) | v_pred μ=+0.18 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 80/100 | Total Loss:   2.19 (R²=+0.75, Policy:  2.16) | v_pred μ=+0.18 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 81/100 | Total Loss:   2.18 (R²=+0.75, Policy:  2.16) | v_pred μ=+0.18 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 82/100 | Total Loss:   2.18 (R²=+0.75, Policy:  2.16) | v_pred μ=+0.18 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 83/100 | Total Loss:   2.18 (R²=+0.75, Policy:  2.16) | v_pred μ=+0.18 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 84/100 | Total Loss:   2.18 (R²=+0.75, Policy:  2.16) | v_pred μ=+0.18 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 85/100 | Total Loss:   2.18 (R²=+0.75, Policy:  2.16) | v_pred μ=+0.18 σ=0.159  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 86/100 | Total Loss:   2.17 (R²=+0.75, Policy:  2.15) | v_pred μ=+0.18 σ=0.159  🟡 POLICY-PLATEAU
Epoche 87/100 | Total Loss:   2.18 (R²=+0.75, Policy:  2.15) | v_pred μ=+0.18 σ=0.159  🟡 POLICY-PLATEAU
Epoche 88/100 | Total Loss:   2.17 (R²=+0.75, Policy:  2.15) | v_pred μ=+0.18 σ=0.159  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 89/100 | Total Loss:   2.17 (R²=+0.75, Policy:  2.15) | v_pred μ=+0.18 σ=0.159  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 90/100 | Total Loss:   2.17 (R²=+0.75, Policy:  2.15) | v_pred μ=+0.18 σ=0.159  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 91/100 | Total Loss:   2.16 (R²=+0.75, Policy:  2.14) | v_pred μ=+0.18 σ=0.159  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 92/100 | Total Loss:   2.17 (R²=+0.75, Policy:  2.15) | v_pred μ=+0.18 σ=0.159  🟡 POLICY-PLATEAU
Epoche 93/100 | Total Loss:   2.16 (R²=+0.76, Policy:  2.14) | v_pred μ=+0.18 σ=0.159  🟡 PLATEAU (Policy+Value)
Epoche 94/100 | Total Loss:   2.16 (R²=+0.76, Policy:  2.14) | v_pred μ=+0.18 σ=0.159  🟡 PLATEAU (Policy+Value)
Epoche 95/100 | Total Loss:   2.16 (R²=+0.76, Policy:  2.14) | v_pred μ=+0.18 σ=0.159  🟡 PLATEAU (Policy+Value)
Epoche 96/100 | Total Loss:   2.16 (R²=+0.76, Policy:  2.14) | v_pred μ=+0.18 σ=0.159  🟡 PLATEAU (Policy+Value)
Epoche 97/100 | Total Loss:   2.16 (R²=+0.76, Policy:  2.14) | v_pred μ=+0.18 σ=0.159  🟡 PLATEAU (Policy+Value)
Epoche 98/100 | Total Loss:   2.16 (R²=+0.76, Policy:  2.14) | v_pred μ=+0.18 σ=0.159  🟡 PLATEAU (Policy+Value)

⏹️  Early Stopping: Policy+Value plateaut seit Epoche 93 (5 Epochen ohne Fortschritt).

=======================================================
  TRAINING SUMMARY
=======================================================
  Epochen:       100
  Züge:          909,891
  Batches/Epoche:3554
───────────────────────────────────────────────────────
  Policy Loss:   2.1385 / 6.18 max  (34.6%)  🟡 Gut
  Value Loss:    0.0080  (R²=0.76 ggü. Mittelwert-Baseline)  🟢 Sehr gut
───────────────────────────────────────────────────────
  ⏹️  Early Stopping nach Epoche 98/100
  🟡 Plateau ab Epoche 93.
     → Für nächste Generation: mehr Sims im Self-Play.
=======================================================

=======================================================
  NETZAUSLASTUNG (Hidden Size: 512)
───────────────────────────────────────────────────────
  Schicht          Dead   Aktiv-Rate        Eff.Rank
  ───────────────────────────────────────────────────
  layer1     0/512 (0%)          40%   221/512 (43%)
  layer2     0/512 (0%)          39%   210/512 (41%)
  layer3    44/512 (9%)          16%   198/512 (39%)
  ───────────────────────────────────────────────────
  🟢 Gesunde Auslastung (Dead 3%, Rank 41%).
=======================================================

✅ Training beendet! Neues Model gespeichert unter:
📂 D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v1b.pth
📈 Loss-Verlauf gespeichert unter:
📂 D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v1b_loss.png
✅ Exportiert: D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v1b.onnx  (input=684, hidden=512, value_hidden=128, opset=13)
📎 Referenz für Rust-Parität: D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v1b.onnx.ref.txt
```



**Stage 1 vs. Stage 2**

```
=======================================================
  STAGE-2-REIFEGRAD-SONDE (100 Spiele je Stufe, 400 Sims)
───────────────────────────────────────────────────────
  Stufe 1 (DFS-Blatt):   0:0  16.0% (16/100) | Ø Sieger-Score  10.7
  Stufe 2 (Netz-Value):  0:0  33.0% (33/100) | Ø Sieger-Score   7.8
  Verhältnis 0:0(Stufe2/Stufe1, geglättet): 2.00x
  🟡 GELB — noch nicht reif, Trend über Generationen beobachten
=======================================================
```



**Arena vs. Heuristik**

```

```
