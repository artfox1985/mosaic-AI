trainiert mit

- --games 2000 --mode network --version v1b --sims 400 --stage 1
- --games 2000 --mode network --version v1c --sims 400 --stage 1
- --games 2000 --mode network --version v4 --sims 400 --stage 1
- --games 2000 --mode network --version v4b --sims 400 --stage 1
- -- load v4

512 neuronen pro hidden layer

Value weight 15

**Netzdaten**

```
PS D:\Archiv\Documents\Projekte\mosaic-AI> python train.py --name v6d --epochs 100 --load v4
📦 Lade HDF5-Cache (800 Dateien)...
Datensatz geladen: 1210259 Züge. (Features pro Zug: 684) — 20.6s
   Value-Ziel-Streuung: σ=0.185 (Varianz=0.0342, zum Vergleich mit v_pred σ unten; Varianz ist die Baseline-MSE bei reiner Mittelwert-Vorhersage)

🚀 Starte PyTorch Training auf: CUDA
🧠 Netz-Architektur: 684→512→512→512
⚙️  Hyperparameter (config.py):
   Learning Rate : 0.0006
   Value Weight  : 15
   Batch Size    : 256
   Value-Target  : tanh((eigen-0.5*gegner)/50) (Endergebnis statt Win/Loss)
📥 Lade altes Model als Startpunkt: alphazero_v4.pth
   ⚠️  Shape-Mismatch, startet frisch: policy_head.0.weight, policy_head.0.bias
   Epochen       : 100
🔄 Warm-Start erkannt: Trainiere für 100 Epochen.
Epoche  1/100 | Total Loss:   3.17 (R²=+0.34, Policy:  2.83) | v_pred μ=+0.10 σ=0.108
Epoche  2/100 | Total Loss:   2.91 (R²=+0.38, Policy:  2.59) | v_pred μ=+0.10 σ=0.116
Epoche  3/100 | Total Loss:   2.80 (R²=+0.42, Policy:  2.50) | v_pred μ=+0.10 σ=0.121
Epoche  4/100 | Total Loss:   2.71 (R²=+0.45, Policy:  2.43) | v_pred μ=+0.10 σ=0.125
Epoche  5/100 | Total Loss:   2.65 (R²=+0.48, Policy:  2.38) | v_pred μ=+0.10 σ=0.129
Epoche  6/100 | Total Loss:   2.60 (R²=+0.49, Policy:  2.34) | v_pred μ=+0.10 σ=0.131
Epoche  7/100 | Total Loss:   2.56 (R²=+0.51, Policy:  2.31) | v_pred μ=+0.10 σ=0.134
Epoche  8/100 | Total Loss:   2.53 (R²=+0.53, Policy:  2.29) | v_pred μ=+0.10 σ=0.135
Epoche  9/100 | Total Loss:   2.51 (R²=+0.54, Policy:  2.27) | v_pred μ=+0.10 σ=0.137
Epoche 10/100 | Total Loss:   2.49 (R²=+0.55, Policy:  2.25) | v_pred μ=+0.10 σ=0.138
Epoche 11/100 | Total Loss:   2.47 (R²=+0.56, Policy:  2.24) | v_pred μ=+0.10 σ=0.140
Epoche 12/100 | Total Loss:   2.45 (R²=+0.57, Policy:  2.23) | v_pred μ=+0.10 σ=0.141
Epoche 13/100 | Total Loss:   2.44 (R²=+0.58, Policy:  2.22) | v_pred μ=+0.10 σ=0.142
Epoche 14/100 | Total Loss:   2.43 (R²=+0.59, Policy:  2.21) | v_pred μ=+0.10 σ=0.143
Epoche 15/100 | Total Loss:   2.42 (R²=+0.59, Policy:  2.21) | v_pred μ=+0.10 σ=0.144
Epoche 16/100 | Total Loss:   2.41 (R²=+0.60, Policy:  2.20) | v_pred μ=+0.10 σ=0.144
Epoche 17/100 | Total Loss:   2.40 (R²=+0.61, Policy:  2.20) | v_pred μ=+0.10 σ=0.145
Epoche 18/100 | Total Loss:   2.39 (R²=+0.61, Policy:  2.19) | v_pred μ=+0.10 σ=0.146
Epoche 19/100 | Total Loss:   2.38 (R²=+0.62, Policy:  2.18) | v_pred μ=+0.10 σ=0.147
Epoche 20/100 | Total Loss:   2.37 (R²=+0.62, Policy:  2.18) | v_pred μ=+0.10 σ=0.147
Epoche 21/100 | Total Loss:   2.37 (R²=+0.63, Policy:  2.18) | v_pred μ=+0.10 σ=0.148
Epoche 22/100 | Total Loss:   2.36 (R²=+0.63, Policy:  2.17) | v_pred μ=+0.10 σ=0.148
Epoche 23/100 | Total Loss:   2.35 (R²=+0.64, Policy:  2.17) | v_pred μ=+0.10 σ=0.149
Epoche 24/100 | Total Loss:   2.35 (R²=+0.64, Policy:  2.16) | v_pred μ=+0.10 σ=0.149
Epoche 25/100 | Total Loss:   2.34 (R²=+0.65, Policy:  2.16) | v_pred μ=+0.10 σ=0.150
Epoche 26/100 | Total Loss:   2.34 (R²=+0.65, Policy:  2.16) | v_pred μ=+0.10 σ=0.150  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 27/100 | Total Loss:   2.33 (R²=+0.65, Policy:  2.15) | v_pred μ=+0.10 σ=0.151  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 28/100 | Total Loss:   2.33 (R²=+0.66, Policy:  2.15) | v_pred μ=+0.10 σ=0.151  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 29/100 | Total Loss:   2.32 (R²=+0.66, Policy:  2.15) | v_pred μ=+0.10 σ=0.152  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 30/100 | Total Loss:   2.32 (R²=+0.66, Policy:  2.14) | v_pred μ=+0.10 σ=0.152  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 31/100 | Total Loss:   2.31 (R²=+0.67, Policy:  2.14) | v_pred μ=+0.10 σ=0.152  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 32/100 | Total Loss:   2.31 (R²=+0.67, Policy:  2.14) | v_pred μ=+0.10 σ=0.153  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 33/100 | Total Loss:   2.30 (R²=+0.67, Policy:  2.14) | v_pred μ=+0.10 σ=0.153  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 34/100 | Total Loss:   2.30 (R²=+0.68, Policy:  2.14) | v_pred μ=+0.10 σ=0.153  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 35/100 | Total Loss:   2.30 (R²=+0.68, Policy:  2.13) | v_pred μ=+0.10 σ=0.154  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 36/100 | Total Loss:   2.29 (R²=+0.68, Policy:  2.13) | v_pred μ=+0.10 σ=0.154  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 37/100 | Total Loss:   2.29 (R²=+0.68, Policy:  2.13) | v_pred μ=+0.10 σ=0.154  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 38/100 | Total Loss:   2.29 (R²=+0.69, Policy:  2.13) | v_pred μ=+0.10 σ=0.155  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 39/100 | Total Loss:   2.29 (R²=+0.69, Policy:  2.13) | v_pred μ=+0.10 σ=0.155  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 40/100 | Total Loss:   2.28 (R²=+0.69, Policy:  2.12) | v_pred μ=+0.10 σ=0.155  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 41/100 | Total Loss:   2.28 (R²=+0.69, Policy:  2.12) | v_pred μ=+0.10 σ=0.155  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 42/100 | Total Loss:   2.28 (R²=+0.70, Policy:  2.12) | v_pred μ=+0.10 σ=0.156  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 43/100 | Total Loss:   2.27 (R²=+0.70, Policy:  2.12) | v_pred μ=+0.10 σ=0.156  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 44/100 | Total Loss:   2.27 (R²=+0.70, Policy:  2.12) | v_pred μ=+0.10 σ=0.156  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 45/100 | Total Loss:   2.27 (R²=+0.70, Policy:  2.11) | v_pred μ=+0.10 σ=0.156  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 46/100 | Total Loss:   2.27 (R²=+0.71, Policy:  2.11) | v_pred μ=+0.10 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 47/100 | Total Loss:   2.26 (R²=+0.71, Policy:  2.11) | v_pred μ=+0.10 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 48/100 | Total Loss:   2.26 (R²=+0.71, Policy:  2.11) | v_pred μ=+0.10 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 49/100 | Total Loss:   2.26 (R²=+0.71, Policy:  2.11) | v_pred μ=+0.10 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 50/100 | Total Loss:   2.25 (R²=+0.71, Policy:  2.11) | v_pred μ=+0.10 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 51/100 | Total Loss:   2.25 (R²=+0.71, Policy:  2.11) | v_pred μ=+0.10 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 52/100 | Total Loss:   2.25 (R²=+0.72, Policy:  2.10) | v_pred μ=+0.10 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 53/100 | Total Loss:   2.25 (R²=+0.72, Policy:  2.10) | v_pred μ=+0.10 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 54/100 | Total Loss:   2.25 (R²=+0.72, Policy:  2.11) | v_pred μ=+0.10 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 55/100 | Total Loss:   2.25 (R²=+0.72, Policy:  2.10) | v_pred μ=+0.10 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 56/100 | Total Loss:   2.24 (R²=+0.72, Policy:  2.10) | v_pred μ=+0.10 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 57/100 | Total Loss:   2.24 (R²=+0.72, Policy:  2.10) | v_pred μ=+0.10 σ=0.159  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 58/100 | Total Loss:   2.24 (R²=+0.73, Policy:  2.10) | v_pred μ=+0.10 σ=0.159  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 59/100 | Total Loss:   2.24 (R²=+0.73, Policy:  2.10) | v_pred μ=+0.10 σ=0.159  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 60/100 | Total Loss:   2.23 (R²=+0.73, Policy:  2.09) | v_pred μ=+0.10 σ=0.159  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 61/100 | Total Loss:   2.23 (R²=+0.73, Policy:  2.09) | v_pred μ=+0.10 σ=0.159  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 62/100 | Total Loss:   2.23 (R²=+0.73, Policy:  2.10) | v_pred μ=+0.10 σ=0.159  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 63/100 | Total Loss:   2.23 (R²=+0.73, Policy:  2.09) | v_pred μ=+0.10 σ=0.159  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 64/100 | Total Loss:   2.23 (R²=+0.73, Policy:  2.09) | v_pred μ=+0.10 σ=0.160  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 65/100 | Total Loss:   2.23 (R²=+0.73, Policy:  2.09) | v_pred μ=+0.10 σ=0.160  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 66/100 | Total Loss:   2.23 (R²=+0.74, Policy:  2.09) | v_pred μ=+0.10 σ=0.160  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 67/100 | Total Loss:   2.22 (R²=+0.74, Policy:  2.09) | v_pred μ=+0.10 σ=0.160  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 68/100 | Total Loss:   2.22 (R²=+0.74, Policy:  2.09) | v_pred μ=+0.10 σ=0.160  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 69/100 | Total Loss:   2.22 (R²=+0.74, Policy:  2.09) | v_pred μ=+0.10 σ=0.160  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 70/100 | Total Loss:   2.22 (R²=+0.74, Policy:  2.09) | v_pred μ=+0.10 σ=0.161  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 71/100 | Total Loss:   2.22 (R²=+0.74, Policy:  2.09) | v_pred μ=+0.10 σ=0.161  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 72/100 | Total Loss:   2.22 (R²=+0.74, Policy:  2.09) | v_pred μ=+0.10 σ=0.161  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 73/100 | Total Loss:   2.21 (R²=+0.75, Policy:  2.08) | v_pred μ=+0.10 σ=0.161  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 74/100 | Total Loss:   2.21 (R²=+0.75, Policy:  2.08) | v_pred μ=+0.10 σ=0.161  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 75/100 | Total Loss:   2.21 (R²=+0.75, Policy:  2.08) | v_pred μ=+0.10 σ=0.161  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 76/100 | Total Loss:   2.21 (R²=+0.75, Policy:  2.08) | v_pred μ=+0.10 σ=0.161  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 77/100 | Total Loss:   2.21 (R²=+0.75, Policy:  2.08) | v_pred μ=+0.10 σ=0.161  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 78/100 | Total Loss:   2.21 (R²=+0.75, Policy:  2.08) | v_pred μ=+0.10 σ=0.162  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 79/100 | Total Loss:   2.21 (R²=+0.75, Policy:  2.08) | v_pred μ=+0.10 σ=0.162  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 80/100 | Total Loss:   2.21 (R²=+0.75, Policy:  2.08) | v_pred μ=+0.10 σ=0.162  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 81/100 | Total Loss:   2.20 (R²=+0.75, Policy:  2.08) | v_pred μ=+0.10 σ=0.162  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 82/100 | Total Loss:   2.20 (R²=+0.75, Policy:  2.08) | v_pred μ=+0.10 σ=0.162  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 83/100 | Total Loss:   2.20 (R²=+0.76, Policy:  2.08) | v_pred μ=+0.10 σ=0.162  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 84/100 | Total Loss:   2.20 (R²=+0.76, Policy:  2.08) | v_pred μ=+0.10 σ=0.162  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 85/100 | Total Loss:   2.20 (R²=+0.76, Policy:  2.07) | v_pred μ=+0.10 σ=0.162  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 86/100 | Total Loss:   2.20 (R²=+0.76, Policy:  2.07) | v_pred μ=+0.10 σ=0.162  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 87/100 | Total Loss:   2.20 (R²=+0.76, Policy:  2.07) | v_pred μ=+0.10 σ=0.162  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 88/100 | Total Loss:   2.20 (R²=+0.76, Policy:  2.07) | v_pred μ=+0.10 σ=0.163  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 89/100 | Total Loss:   2.20 (R²=+0.76, Policy:  2.07) | v_pred μ=+0.10 σ=0.163  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 90/100 | Total Loss:   2.19 (R²=+0.76, Policy:  2.07) | v_pred μ=+0.10 σ=0.163  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 91/100 | Total Loss:   2.19 (R²=+0.76, Policy:  2.07) | v_pred μ=+0.10 σ=0.163  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 92/100 | Total Loss:   2.19 (R²=+0.76, Policy:  2.07) | v_pred μ=+0.10 σ=0.163  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 93/100 | Total Loss:   2.19 (R²=+0.77, Policy:  2.07) | v_pred μ=+0.10 σ=0.163  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 94/100 | Total Loss:   2.19 (R²=+0.77, Policy:  2.07) | v_pred μ=+0.10 σ=0.163  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 95/100 | Total Loss:   2.19 (R²=+0.77, Policy:  2.07) | v_pred μ=+0.10 σ=0.163  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 96/100 | Total Loss:   2.19 (R²=+0.77, Policy:  2.07) | v_pred μ=+0.10 σ=0.163  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 97/100 | Total Loss:   2.19 (R²=+0.77, Policy:  2.07) | v_pred μ=+0.10 σ=0.163  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 98/100 | Total Loss:   2.19 (R²=+0.77, Policy:  2.07) | v_pred μ=+0.10 σ=0.163  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 99/100 | Total Loss:   2.19 (R²=+0.77, Policy:  2.07) | v_pred μ=+0.10 σ=0.163  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 100/100 | Total Loss:   2.18 (R²=+0.77, Policy:  2.07) | v_pred μ=+0.10 σ=0.164  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)

=======================================================
  TRAINING SUMMARY
=======================================================
  Epochen:       100
  Züge:          1,210,259
  Batches/Epoche:4727
───────────────────────────────────────────────────────
  Policy Loss:   2.0666 / 6.18 max  (33.5%)  🟡 Gut
  Value Loss:    0.0078  (R²=0.77 ggü. Mittelwert-Baseline)  🟢 Sehr gut
───────────────────────────────────────────────────────
  🟢 Kein Plateau — Policy sinkt noch. Mehr Epochen möglich.
=======================================================

=======================================================
  NETZAUSLASTUNG (Hidden Size: 512)
───────────────────────────────────────────────────────
  Schicht          Dead   Aktiv-Rate        Eff.Rank
  ───────────────────────────────────────────────────
  layer1     0/512 (0%)          42%   220/512 (43%)
  layer2     0/512 (0%)          33%   213/512 (42%)
  layer3    66/512 (13%)          14%   202/512 (40%)
  ───────────────────────────────────────────────────
  🟢 Gesunde Auslastung (Dead 4%, Rank 41%).
=======================================================

✅ Training beendet! Neues Model gespeichert unter:
📂 D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v6d.pth
📈 Loss-Verlauf gespeichert unter:
📂 D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v6d_loss.png
✅ Exportiert: D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v6d.onnx  (input=684, hidden=512, value_hidden=128, opset=13)
📎 Referenz für Rust-Parität: D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v6d.onnx.ref.txt
```

R² = 0.77 -> Gut

```
=======================================================
  STAGE-2-REIFEGRAD-SONDE (100 Spiele je Stufe, 400 Sims)
───────────────────────────────────────────────────────
  Stufe 1 (DFS-Blatt):   0:0   9.0% (9/100) | Ø Sieger-Score  15.5
  Stufe 2 (Netz-Value):  0:0  38.0% (38/100) | Ø Sieger-Score   5.7
  Verhältnis 0:0(Stufe2/Stufe1, geglättet): 3.90x
  🔴 ROT — klar noch nicht reif, in Stufe 1 bleiben
=======================================================
```


