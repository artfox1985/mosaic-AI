trainiert mit

- --games 2000 --mode network --version v1b --sims 400 --stage 1
- --games 2000 --mode network --version v1c --sims 400 --stage 1
- --games 2000 --mode network --version v4 --sims 400 --stage 1
- --games 2000 --mode network --version v4b --sims 400 --stage 1
- --games 2000 --mode network --version v4c --sims 400 --stage 1
- -- load v4

512 neuronen pro hidden layer

**Architektur-Änderung:** Policy-Head jetzt 2-lagig (`Linear(512→256)→ReLU→Linear(256→482)`
statt nacktem `Linear(512→482)`) — Warm-Start von v4 startet den Policy-Head deshalb zufällig
(Shape-Mismatch), Body/Value-Head/Moon-Order-Head bleiben warm.

**Parameterstudie: Learning Rate 0.0006 vs. 0.0004** (identischer Datensatz, `VALUE_WEIGHT=15`,
100 Epochen, in beiden Fällen kein Plateau erreicht — Policy sinkt bis zum Schluss weiter)

| Version              | LR     | Policy Loss    | Value Loss | R²     | Total Loss (Policy + 15·Value) |
| -------------------- | ------ | -------------- | ---------- | ------ | ------------------------------ |
| (LR 0.0006, s.u.)    | 0.0006 | 2.0947 (33.9%) | 0.0090     | 0.7367 | **2.2297**                     |
| (LR 0.0004, gewählt) | 0.0004 | 2.0783 (33.6%) | 0.0094     | 0.7235 | **2.2193**                     |

→ **LR 0.0004 gewinnt** (niedrigerer Total Loss, niedrigerer Policy Loss, R² praktisch
gleichauf) und wird zum offiziellen `v7`. Der LR-0.0006-Lauf (komplettes Log unten, ursprünglich
als "v7" trainiert) ist als `alphazero_v7_lr0006.pth/.onnx` archiviert. Bestätigt den Verdacht
aus der vorherigen Diskussion: `0.0006` scheint für den Policy-Head leicht zu aggressiv
(überschießt knapp am besseren Minimum vorbei), `0.0004` konvergiert sauberer.

**Netzdaten (LR 0.0006 — archiviert als `alphazero_v7_lr0006`, NICHT der finale v7)**

```
PS D:\Archiv\Documents\Projekte\mosaic-AI> python train.py --name v7 --epochs 100 --load v4
Lade Daten aus 1000 Dateien...
Datensatz geladen: 1512166 Züge. (Features pro Zug: 684) — 601.9s
💾 Speichere HDF5-Cache...
✅ Cache gespeichert: D:\Archiv\Documents\Projekte\mosaic-AI\data\.cache_bc5b3ef59d09.h5
   Value-Ziel-Streuung: σ=0.185 (Varianz=0.0341, zum Vergleich mit v_pred σ unten; Varianz ist die Baseline-MSE bei reiner Mittelwert-Vorhersage)

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
Epoche  1/100 | Total Loss:   3.23 (R²=+0.31, Policy:  2.87) | v_pred μ=+0.10 σ=0.104
Epoche  2/100 | Total Loss:   3.00 (R²=+0.36, Policy:  2.68) | v_pred μ=+0.10 σ=0.112
Epoche  3/100 | Total Loss:   2.90 (R²=+0.40, Policy:  2.59) | v_pred μ=+0.10 σ=0.117
Epoche  4/100 | Total Loss:   2.82 (R²=+0.43, Policy:  2.53) | v_pred μ=+0.10 σ=0.122
Epoche  5/100 | Total Loss:   2.75 (R²=+0.45, Policy:  2.47) | v_pred μ=+0.10 σ=0.125
Epoche  6/100 | Total Loss:   2.70 (R²=+0.47, Policy:  2.43) | v_pred μ=+0.10 σ=0.128
Epoche  7/100 | Total Loss:   2.66 (R²=+0.49, Policy:  2.39) | v_pred μ=+0.10 σ=0.130
Epoche  8/100 | Total Loss:   2.63 (R²=+0.50, Policy:  2.37) | v_pred μ=+0.10 σ=0.132
Epoche  9/100 | Total Loss:   2.60 (R²=+0.51, Policy:  2.35) | v_pred μ=+0.10 σ=0.133
Epoche 10/100 | Total Loss:   2.57 (R²=+0.52, Policy:  2.33) | v_pred μ=+0.10 σ=0.135
Epoche 11/100 | Total Loss:   2.56 (R²=+0.53, Policy:  2.32) | v_pred μ=+0.10 σ=0.136
Epoche 12/100 | Total Loss:   2.54 (R²=+0.54, Policy:  2.30) | v_pred μ=+0.10 σ=0.137
Epoche 13/100 | Total Loss:   2.52 (R²=+0.55, Policy:  2.29) | v_pred μ=+0.10 σ=0.138
Epoche 14/100 | Total Loss:   2.51 (R²=+0.55, Policy:  2.28) | v_pred μ=+0.10 σ=0.139
Epoche 15/100 | Total Loss:   2.49 (R²=+0.56, Policy:  2.27) | v_pred μ=+0.10 σ=0.139
Epoche 16/100 | Total Loss:   2.48 (R²=+0.57, Policy:  2.26) | v_pred μ=+0.10 σ=0.140
Epoche 17/100 | Total Loss:   2.47 (R²=+0.57, Policy:  2.26) | v_pred μ=+0.10 σ=0.141
Epoche 18/100 | Total Loss:   2.46 (R²=+0.58, Policy:  2.25) | v_pred μ=+0.10 σ=0.142
Epoche 19/100 | Total Loss:   2.45 (R²=+0.58, Policy:  2.24) | v_pred μ=+0.10 σ=0.142
Epoche 20/100 | Total Loss:   2.45 (R²=+0.59, Policy:  2.24) | v_pred μ=+0.10 σ=0.143
Epoche 21/100 | Total Loss:   2.44 (R²=+0.59, Policy:  2.23) | v_pred μ=+0.10 σ=0.143
Epoche 22/100 | Total Loss:   2.43 (R²=+0.60, Policy:  2.23) | v_pred μ=+0.10 σ=0.144
Epoche 23/100 | Total Loss:   2.42 (R²=+0.60, Policy:  2.22) | v_pred μ=+0.10 σ=0.144
Epoche 24/100 | Total Loss:   2.42 (R²=+0.61, Policy:  2.22) | v_pred μ=+0.10 σ=0.145
Epoche 25/100 | Total Loss:   2.41 (R²=+0.61, Policy:  2.21) | v_pred μ=+0.10 σ=0.146
Epoche 26/100 | Total Loss:   2.40 (R²=+0.61, Policy:  2.21) | v_pred μ=+0.10 σ=0.146
Epoche 27/100 | Total Loss:   2.40 (R²=+0.62, Policy:  2.20) | v_pred μ=+0.10 σ=0.146
Epoche 28/100 | Total Loss:   2.39 (R²=+0.62, Policy:  2.20) | v_pred μ=+0.10 σ=0.147
Epoche 29/100 | Total Loss:   2.39 (R²=+0.62, Policy:  2.19) | v_pred μ=+0.10 σ=0.147
Epoche 30/100 | Total Loss:   2.38 (R²=+0.63, Policy:  2.19) | v_pred μ=+0.10 σ=0.148  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 31/100 | Total Loss:   2.38 (R²=+0.63, Policy:  2.19) | v_pred μ=+0.10 σ=0.148  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 32/100 | Total Loss:   2.37 (R²=+0.63, Policy:  2.19) | v_pred μ=+0.10 σ=0.148  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 33/100 | Total Loss:   2.37 (R²=+0.64, Policy:  2.18) | v_pred μ=+0.10 σ=0.149  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 34/100 | Total Loss:   2.36 (R²=+0.64, Policy:  2.18) | v_pred μ=+0.10 σ=0.149  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 35/100 | Total Loss:   2.36 (R²=+0.64, Policy:  2.18) | v_pred μ=+0.10 σ=0.149  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 36/100 | Total Loss:   2.36 (R²=+0.65, Policy:  2.17) | v_pred μ=+0.10 σ=0.150  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 37/100 | Total Loss:   2.35 (R²=+0.65, Policy:  2.17) | v_pred μ=+0.10 σ=0.150  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 38/100 | Total Loss:   2.35 (R²=+0.65, Policy:  2.17) | v_pred μ=+0.10 σ=0.150  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 39/100 | Total Loss:   2.34 (R²=+0.65, Policy:  2.17) | v_pred μ=+0.10 σ=0.151  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 40/100 | Total Loss:   2.34 (R²=+0.66, Policy:  2.17) | v_pred μ=+0.10 σ=0.151  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 41/100 | Total Loss:   2.34 (R²=+0.66, Policy:  2.16) | v_pred μ=+0.10 σ=0.151  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 42/100 | Total Loss:   2.34 (R²=+0.66, Policy:  2.16) | v_pred μ=+0.10 σ=0.151  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 43/100 | Total Loss:   2.33 (R²=+0.66, Policy:  2.16) | v_pred μ=+0.10 σ=0.152  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 44/100 | Total Loss:   2.33 (R²=+0.66, Policy:  2.16) | v_pred μ=+0.10 σ=0.152  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 45/100 | Total Loss:   2.33 (R²=+0.67, Policy:  2.16) | v_pred μ=+0.10 σ=0.152  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 46/100 | Total Loss:   2.32 (R²=+0.67, Policy:  2.15) | v_pred μ=+0.10 σ=0.152  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 47/100 | Total Loss:   2.32 (R²=+0.67, Policy:  2.15) | v_pred μ=+0.10 σ=0.152  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 48/100 | Total Loss:   2.32 (R²=+0.67, Policy:  2.15) | v_pred μ=+0.10 σ=0.153  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 49/100 | Total Loss:   2.31 (R²=+0.67, Policy:  2.15) | v_pred μ=+0.10 σ=0.153  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 50/100 | Total Loss:   2.31 (R²=+0.68, Policy:  2.15) | v_pred μ=+0.10 σ=0.153  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 51/100 | Total Loss:   2.31 (R²=+0.68, Policy:  2.14) | v_pred μ=+0.10 σ=0.153  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 52/100 | Total Loss:   2.31 (R²=+0.68, Policy:  2.14) | v_pred μ=+0.10 σ=0.154  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 53/100 | Total Loss:   2.31 (R²=+0.68, Policy:  2.14) | v_pred μ=+0.10 σ=0.154  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 54/100 | Total Loss:   2.30 (R²=+0.68, Policy:  2.14) | v_pred μ=+0.10 σ=0.154  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 55/100 | Total Loss:   2.30 (R²=+0.68, Policy:  2.14) | v_pred μ=+0.10 σ=0.154  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 56/100 | Total Loss:   2.30 (R²=+0.69, Policy:  2.14) | v_pred μ=+0.10 σ=0.154  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 57/100 | Total Loss:   2.29 (R²=+0.69, Policy:  2.13) | v_pred μ=+0.10 σ=0.154  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 58/100 | Total Loss:   2.29 (R²=+0.69, Policy:  2.14) | v_pred μ=+0.10 σ=0.155  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 59/100 | Total Loss:   2.29 (R²=+0.69, Policy:  2.13) | v_pred μ=+0.10 σ=0.155  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 60/100 | Total Loss:   2.29 (R²=+0.69, Policy:  2.13) | v_pred μ=+0.10 σ=0.155  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 61/100 | Total Loss:   2.29 (R²=+0.69, Policy:  2.13) | v_pred μ=+0.10 σ=0.155  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 62/100 | Total Loss:   2.28 (R²=+0.70, Policy:  2.13) | v_pred μ=+0.10 σ=0.155  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 63/100 | Total Loss:   2.28 (R²=+0.70, Policy:  2.13) | v_pred μ=+0.10 σ=0.156  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 64/100 | Total Loss:   2.28 (R²=+0.70, Policy:  2.13) | v_pred μ=+0.10 σ=0.156  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 65/100 | Total Loss:   2.28 (R²=+0.70, Policy:  2.12) | v_pred μ=+0.10 σ=0.156  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 66/100 | Total Loss:   2.28 (R²=+0.70, Policy:  2.13) | v_pred μ=+0.10 σ=0.156  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 67/100 | Total Loss:   2.28 (R²=+0.70, Policy:  2.12) | v_pred μ=+0.10 σ=0.156  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 68/100 | Total Loss:   2.27 (R²=+0.70, Policy:  2.12) | v_pred μ=+0.10 σ=0.156  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 69/100 | Total Loss:   2.27 (R²=+0.71, Policy:  2.12) | v_pred μ=+0.10 σ=0.156  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 70/100 | Total Loss:   2.27 (R²=+0.71, Policy:  2.12) | v_pred μ=+0.10 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 71/100 | Total Loss:   2.27 (R²=+0.71, Policy:  2.12) | v_pred μ=+0.10 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 72/100 | Total Loss:   2.27 (R²=+0.71, Policy:  2.12) | v_pred μ=+0.10 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 73/100 | Total Loss:   2.26 (R²=+0.71, Policy:  2.12) | v_pred μ=+0.10 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 74/100 | Total Loss:   2.26 (R²=+0.71, Policy:  2.12) | v_pred μ=+0.10 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 75/100 | Total Loss:   2.26 (R²=+0.71, Policy:  2.11) | v_pred μ=+0.10 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 76/100 | Total Loss:   2.26 (R²=+0.71, Policy:  2.11) | v_pred μ=+0.10 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 77/100 | Total Loss:   2.26 (R²=+0.71, Policy:  2.11) | v_pred μ=+0.10 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 78/100 | Total Loss:   2.26 (R²=+0.72, Policy:  2.11) | v_pred μ=+0.10 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 79/100 | Total Loss:   2.26 (R²=+0.72, Policy:  2.11) | v_pred μ=+0.10 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 80/100 | Total Loss:   2.25 (R²=+0.72, Policy:  2.11) | v_pred μ=+0.10 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 81/100 | Total Loss:   2.25 (R²=+0.72, Policy:  2.11) | v_pred μ=+0.10 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 82/100 | Total Loss:   2.25 (R²=+0.72, Policy:  2.11) | v_pred μ=+0.10 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 83/100 | Total Loss:   2.25 (R²=+0.72, Policy:  2.11) | v_pred μ=+0.10 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 84/100 | Total Loss:   2.25 (R²=+0.72, Policy:  2.11) | v_pred μ=+0.10 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 85/100 | Total Loss:   2.25 (R²=+0.72, Policy:  2.11) | v_pred μ=+0.10 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 86/100 | Total Loss:   2.25 (R²=+0.72, Policy:  2.10) | v_pred μ=+0.10 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 87/100 | Total Loss:   2.24 (R²=+0.72, Policy:  2.10) | v_pred μ=+0.10 σ=0.159  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 88/100 | Total Loss:   2.24 (R²=+0.73, Policy:  2.10) | v_pred μ=+0.10 σ=0.159  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 89/100 | Total Loss:   2.24 (R²=+0.73, Policy:  2.10) | v_pred μ=+0.10 σ=0.159  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 90/100 | Total Loss:   2.24 (R²=+0.73, Policy:  2.10) | v_pred μ=+0.10 σ=0.159  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 91/100 | Total Loss:   2.24 (R²=+0.73, Policy:  2.10) | v_pred μ=+0.10 σ=0.159  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 92/100 | Total Loss:   2.24 (R²=+0.73, Policy:  2.10) | v_pred μ=+0.10 σ=0.159  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 93/100 | Total Loss:   2.24 (R²=+0.73, Policy:  2.10) | v_pred μ=+0.10 σ=0.159  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 94/100 | Total Loss:   2.24 (R²=+0.73, Policy:  2.10) | v_pred μ=+0.10 σ=0.159  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 95/100 | Total Loss:   2.24 (R²=+0.73, Policy:  2.10) | v_pred μ=+0.10 σ=0.159  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 96/100 | Total Loss:   2.23 (R²=+0.73, Policy:  2.10) | v_pred μ=+0.10 σ=0.160  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 97/100 | Total Loss:   2.23 (R²=+0.73, Policy:  2.10) | v_pred μ=+0.10 σ=0.160  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 98/100 | Total Loss:   2.23 (R²=+0.73, Policy:  2.10) | v_pred μ=+0.10 σ=0.160  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 99/100 | Total Loss:   2.23 (R²=+0.74, Policy:  2.09) | v_pred μ=+0.10 σ=0.160  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 100/100 | Total Loss:   2.23 (R²=+0.74, Policy:  2.09) | v_pred μ=+0.10 σ=0.160  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)

=======================================================
  TRAINING SUMMARY
=======================================================
  Epochen:       100
  Züge:          1,512,166
  Batches/Epoche:5906
───────────────────────────────────────────────────────
  Policy Loss:   2.0947 / 6.18 max  (33.9%)  🟡 Gut
  Value Loss:    0.0090  (R²=0.74 ggü. Mittelwert-Baseline)  🟢 Sehr gut
───────────────────────────────────────────────────────
  🟢 Kein Plateau — Policy sinkt noch. Mehr Epochen möglich.
=======================================================

=======================================================
  NETZAUSLASTUNG (Hidden Size: 512)
───────────────────────────────────────────────────────
  Schicht          Dead   Aktiv-Rate        Eff.Rank
  ───────────────────────────────────────────────────
  layer1     0/512 (0%)          41%   221/512 (43%)
  layer2     0/512 (0%)          33%   212/512 (41%)
  layer3    63/512 (12%)          14%   202/512 (39%)
  ───────────────────────────────────────────────────
  🟢 Gesunde Auslastung (Dead 4%, Rank 41%).
=======================================================

✅ Training beendet! Neues Model gespeichert unter:
📂 D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v7.pth
📈 Loss-Verlauf gespeichert unter:
📂 D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v7_loss.png
✅ Exportiert: D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v7.onnx  (input=684, hidden=512, value_hidden=128, opset=13)
📎 Referenz für Rust-Parität: D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v7.onnx.ref.txt
```

```
=======================================================
  STAGE-2-REIFEGRAD-SONDE (100 Spiele je Stufe, 400 Sims)
───────────────────────────────────────────────────────
  Stufe 1 (DFS-Blatt):   0:0  11.0% (11/100) | Ø Sieger-Score  15.9
  Stufe 2 (Netz-Value):  0:0  33.0% (33/100) | Ø Sieger-Score   6.5
  Verhältnis 0:0(Stufe2/Stufe1, geglättet): 2.83x
  🟡 GELB — noch nicht reif, Trend über Generationen beobachten
=======================================================
```

**Arena vs. aktuellen Champion v4** (100 Spiele, 200 Sims, Stufe 1/DFS-Blatt)

```
🏆 ERGEBNIS: v7 43:57 v4 (43% A-Siege) in 2334.7s (0.0 Spiele/s)
   Ø Score: v7 21.2 | v4 21.2
   0:0-Spiele: 3/100 (3.0%)
   Elo: v7 1003 | v4 997
```

**Gate NICHT bestanden.** 43:57 (z≈-1.4) — v7 verliert klar gegen v4, bei exakt identischem
Ø-Score (21.2 vs. 21.2). Kein Fortschritt gegenüber dem Vorgänger. **v4 bleibt Champion.**

**Arena vs. Heuristik** (100 Spiele, 200 Sims, Stufe 1/DFS-Blatt)

```
🏆 ERGEBNIS: v7 59:41 Heuristik(s200) (59% Netz-Siege) in 1149.9s (0.1 Spiele/s)
   Ø Score: v7 27.2 | Heuristik(s200) 25.5
   0:0-Spiele: 2/100 (2.0%)  (Sauberkeits-Indikator)
   Ø Floor-Strafe: v7 21.9 | Heuristik(s200) 22.4
   Elo: v7 1009 | Heuristik(s200) 991
```

59% (z≈1.8) — bestes Ergebnis der gesamten Reihe gegen die Heuristik (v4: 48%, v5: 47%,
v6b: 58%, v7: 59%), Ø-Score erneut zugunsten des Netzes (27.2 vs. 25.5). Bestätigt den Trend
seit der `VALUE_WEIGHT`-Erhöhung: deutlich besseres Value-R² und stärkere Performance gegen die
Heuristik, aber (noch) kein Durchbruch gegen den Champion selbst.

**Arena vs. alten Champion v1**

Nicht gespielt — nur vorgesehen, falls v7 Champion wird. Da v4 Champion bleibt, entfällt dieser Lauf.

---

**Fazit:** v4 bleibt Champion. v7 zeigt trotz deutlich besserem Value-R² (0.72) und dem bisher stärksten Heuristik-Ergebnis (59%) keinen signifikanten Fortschritt gegen den Champion selbst
(43:57, z≈-1.4 — sogar ein numerischer Rückschritt, kein knappes Patt wie bei v2/v3/v5).
Fenster war bereits bei vollen 10.000 Spielen (v1b+v1c+v4+v4b+v4c). Nächster Schritt laut Eskalationsplan: `v4d`-Self-Play (2000 Spiele, 400 Sims, gleiche Sim-Zahl wie bisher) generieren, `v1b`-Runde ins Archiv (Fenster danach: v1c allein = 2000 alt + v4/v4b/v4c/v4d = 8000 aktueller Champion — die Ausdünnungs- und Eskalationsstufe fallen hier zusammen, da ohnehin eine weitere ~~~~Champion-Runde ansteht).
