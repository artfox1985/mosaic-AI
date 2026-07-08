trainiert mit 

- --games 4000 --mode mcts --sims 400

- --games 6000 --mode network --version v1 --sims 400 --stage 1

- --load v1

**Netzdaten**

```
PS D:\Archiv\Documents\Projekte\mosaic-AI> python train.py --name v2b --epochs 100 --load v1
📦 Lade HDF5-Cache (900 Dateien)...
Datensatz geladen: 1353541 Züge. (Features pro Zug: 684) — 19.4s
📦 Lade HDF5-Cache (100 Dateien)...
Datensatz geladen: 150548 Züge. (Features pro Zug: 684) — 2.1s
   Val-Split: 900 Trainings-Dateien / 100 Val-Dateien (1,353,541 / 150,548 Züge)
   Value-Ziel-Streuung: σ=0.168 (Varianz=0.0281, zum Vergleich mit v_pred σ unten; Varianz ist die Baseline-MSE bei reiner Mittelwert-Vorhersage)

🚀 Starte PyTorch Training auf: CUDA
🧠 Netz-Architektur: 684→512→512→512
⚙️  Hyperparameter (config.py):
   Learning Rate : 0.0004
   Value Weight  : 15
   Batch Size    : 256
   Value-Target  : tanh(eigen/50) - 0.1*tanh(gegner/50) (Endergebnis statt Win/Loss)
📥 Lade altes Model als Startpunkt: alphazero_v1.pth
   Epochen       : 100
🔄 Warm-Start erkannt: Trainiere für 100 Epochen.
Epoche  1/100 | Total Loss:   3.11 (R²=+0.58, Policy:  2.93) | Val-R²=+0.57 | v_pred μ=+0.15 σ=0.129
Epoche  2/100 | Total Loss:   2.91 (R²=+0.66, Policy:  2.77) | Val-R²=+0.55 | v_pred μ=+0.15 σ=0.137
Epoche  3/100 | Total Loss:   2.81 (R²=+0.70, Policy:  2.68) | Val-R²=+0.53 | v_pred μ=+0.15 σ=0.142
Epoche  4/100 | Total Loss:   2.72 (R²=+0.73, Policy:  2.61) | Val-R²=+0.51 | v_pred μ=+0.15 σ=0.144
Epoche  5/100 | Total Loss:   2.65 (R²=+0.74, Policy:  2.55) | Val-R²=+0.50 | v_pred μ=+0.15 σ=0.145
Epoche  6/100 | Total Loss:   2.60 (R²=+0.75, Policy:  2.49) | Val-R²=+0.49 | v_pred μ=+0.15 σ=0.146
Epoche  7/100 | Total Loss:   2.56 (R²=+0.76, Policy:  2.46) | Val-R²=+0.48 | v_pred μ=+0.15 σ=0.147
Epoche  8/100 | Total Loss:   2.52 (R²=+0.77, Policy:  2.43) | Val-R²=+0.48 | v_pred μ=+0.15 σ=0.148
Epoche  9/100 | Total Loss:   2.50 (R²=+0.77, Policy:  2.40) | Val-R²=+0.47 | v_pred μ=+0.15 σ=0.148
Epoche 10/100 | Total Loss:   2.48 (R²=+0.78, Policy:  2.39) | Val-R²=+0.47 | v_pred μ=+0.15 σ=0.148
Epoche 11/100 | Total Loss:   2.46 (R²=+0.78, Policy:  2.37) | Val-R²=+0.46 | v_pred μ=+0.15 σ=0.149
Epoche 12/100 | Total Loss:   2.45 (R²=+0.78, Policy:  2.36) | Val-R²=+0.46 | v_pred μ=+0.15 σ=0.149
Epoche 13/100 | Total Loss:   2.44 (R²=+0.79, Policy:  2.35) | Val-R²=+0.45 | v_pred μ=+0.15 σ=0.149
Epoche 14/100 | Total Loss:   2.43 (R²=+0.79, Policy:  2.34) | Val-R²=+0.45 | v_pred μ=+0.15 σ=0.150
Epoche 15/100 | Total Loss:   2.42 (R²=+0.79, Policy:  2.33) | Val-R²=+0.44 | v_pred μ=+0.15 σ=0.150
Epoche 16/100 | Total Loss:   2.41 (R²=+0.79, Policy:  2.33) | Val-R²=+0.44 | v_pred μ=+0.15 σ=0.150
Epoche 17/100 | Total Loss:   2.41 (R²=+0.80, Policy:  2.32) | Val-R²=+0.44 | v_pred μ=+0.15 σ=0.150
Epoche 18/100 | Total Loss:   2.40 (R²=+0.80, Policy:  2.32) | Val-R²=+0.44 | v_pred μ=+0.15 σ=0.151
Epoche 19/100 | Total Loss:   2.39 (R²=+0.80, Policy:  2.31) | Val-R²=+0.43 | v_pred μ=+0.15 σ=0.151
Epoche 20/100 | Total Loss:   2.39 (R²=+0.80, Policy:  2.30) | Val-R²=+0.43 | v_pred μ=+0.15 σ=0.151
Epoche 21/100 | Total Loss:   2.38 (R²=+0.80, Policy:  2.30) | Val-R²=+0.43 | v_pred μ=+0.15 σ=0.151
Epoche 22/100 | Total Loss:   2.38 (R²=+0.81, Policy:  2.30) | Val-R²=+0.43 | v_pred μ=+0.15 σ=0.151
Epoche 23/100 | Total Loss:   2.37 (R²=+0.81, Policy:  2.29) | Val-R²=+0.43 | v_pred μ=+0.15 σ=0.152
Epoche 24/100 | Total Loss:   2.37 (R²=+0.81, Policy:  2.29) | Val-R²=+0.44 | v_pred μ=+0.15 σ=0.152
Epoche 25/100 | Total Loss:   2.37 (R²=+0.81, Policy:  2.29) | Val-R²=+0.43 | v_pred μ=+0.15 σ=0.152  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 26/100 | Total Loss:   2.36 (R²=+0.81, Policy:  2.28) | Val-R²=+0.42 | v_pred μ=+0.15 σ=0.152  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 27/100 | Total Loss:   2.36 (R²=+0.81, Policy:  2.28) | Val-R²=+0.42 | v_pred μ=+0.15 σ=0.152  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 28/100 | Total Loss:   2.36 (R²=+0.82, Policy:  2.28) | Val-R²=+0.42 | v_pred μ=+0.15 σ=0.152  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 29/100 | Total Loss:   2.35 (R²=+0.82, Policy:  2.28) | Val-R²=+0.42 | v_pred μ=+0.15 σ=0.152  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 30/100 | Total Loss:   2.35 (R²=+0.82, Policy:  2.27) | Val-R²=+0.41 | v_pred μ=+0.15 σ=0.152  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 31/100 | Total Loss:   2.35 (R²=+0.82, Policy:  2.27) | Val-R²=+0.42 | v_pred μ=+0.15 σ=0.153  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 32/100 | Total Loss:   2.35 (R²=+0.82, Policy:  2.27) | Val-R²=+0.42 | v_pred μ=+0.15 σ=0.153  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 33/100 | Total Loss:   2.34 (R²=+0.82, Policy:  2.27) | Val-R²=+0.42 | v_pred μ=+0.15 σ=0.153  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 34/100 | Total Loss:   2.34 (R²=+0.82, Policy:  2.27) | Val-R²=+0.42 | v_pred μ=+0.15 σ=0.153  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 35/100 | Total Loss:   2.34 (R²=+0.82, Policy:  2.27) | Val-R²=+0.41 | v_pred μ=+0.15 σ=0.153  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 36/100 | Total Loss:   2.34 (R²=+0.83, Policy:  2.26) | Val-R²=+0.41 | v_pred μ=+0.15 σ=0.153  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 37/100 | Total Loss:   2.33 (R²=+0.83, Policy:  2.26) | Val-R²=+0.41 | v_pred μ=+0.15 σ=0.153  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 38/100 | Total Loss:   2.33 (R²=+0.83, Policy:  2.26) | Val-R²=+0.41 | v_pred μ=+0.15 σ=0.153  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 39/100 | Total Loss:   2.33 (R²=+0.83, Policy:  2.26) | Val-R²=+0.40 | v_pred μ=+0.15 σ=0.153  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 40/100 | Total Loss:   2.33 (R²=+0.83, Policy:  2.26) | Val-R²=+0.41 | v_pred μ=+0.15 σ=0.154  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 41/100 | Total Loss:   2.33 (R²=+0.83, Policy:  2.26) | Val-R²=+0.41 | v_pred μ=+0.15 σ=0.154  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 42/100 | Total Loss:   2.32 (R²=+0.83, Policy:  2.25) | Val-R²=+0.41 | v_pred μ=+0.15 σ=0.154  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 43/100 | Total Loss:   2.32 (R²=+0.83, Policy:  2.25) | Val-R²=+0.41 | v_pred μ=+0.15 σ=0.154  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 44/100 | Total Loss:   2.32 (R²=+0.83, Policy:  2.25) | Val-R²=+0.41 | v_pred μ=+0.15 σ=0.154  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 45/100 | Total Loss:   2.32 (R²=+0.83, Policy:  2.25) | Val-R²=+0.39 | v_pred μ=+0.15 σ=0.154  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 46/100 | Total Loss:   2.32 (R²=+0.84, Policy:  2.25) | Val-R²=+0.41 | v_pred μ=+0.15 σ=0.154  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 47/100 | Total Loss:   2.31 (R²=+0.84, Policy:  2.25) | Val-R²=+0.40 | v_pred μ=+0.15 σ=0.154  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 48/100 | Total Loss:   2.32 (R²=+0.84, Policy:  2.25) | Val-R²=+0.41 | v_pred μ=+0.15 σ=0.154  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 49/100 | Total Loss:   2.31 (R²=+0.84, Policy:  2.25) | Val-R²=+0.41 | v_pred μ=+0.15 σ=0.154  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 50/100 | Total Loss:   2.31 (R²=+0.84, Policy:  2.24) | Val-R²=+0.41 | v_pred μ=+0.15 σ=0.154  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 51/100 | Total Loss:   2.31 (R²=+0.84, Policy:  2.24) | Val-R²=+0.40 | v_pred μ=+0.15 σ=0.154  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 52/100 | Total Loss:   2.31 (R²=+0.84, Policy:  2.24) | Val-R²=+0.40 | v_pred μ=+0.15 σ=0.155  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 53/100 | Total Loss:   2.31 (R²=+0.84, Policy:  2.24) | Val-R²=+0.40 | v_pred μ=+0.15 σ=0.155  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 54/100 | Total Loss:   2.31 (R²=+0.84, Policy:  2.24) | Val-R²=+0.39 | v_pred μ=+0.15 σ=0.155  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 55/100 | Total Loss:   2.31 (R²=+0.84, Policy:  2.24) | Val-R²=+0.40 | v_pred μ=+0.15 σ=0.155  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 56/100 | Total Loss:   2.30 (R²=+0.84, Policy:  2.24) | Val-R²=+0.39 | v_pred μ=+0.15 σ=0.155  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 57/100 | Total Loss:   2.30 (R²=+0.84, Policy:  2.24) | Val-R²=+0.39 | v_pred μ=+0.15 σ=0.155  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 58/100 | Total Loss:   2.30 (R²=+0.85, Policy:  2.24) | Val-R²=+0.39 | v_pred μ=+0.15 σ=0.155  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 59/100 | Total Loss:   2.30 (R²=+0.85, Policy:  2.24) | Val-R²=+0.40 | v_pred μ=+0.15 σ=0.155  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 60/100 | Total Loss:   2.30 (R²=+0.85, Policy:  2.23) | Val-R²=+0.39 | v_pred μ=+0.15 σ=0.155  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 61/100 | Total Loss:   2.30 (R²=+0.85, Policy:  2.23) | Val-R²=+0.39 | v_pred μ=+0.15 σ=0.155  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 62/100 | Total Loss:   2.30 (R²=+0.85, Policy:  2.23) | Val-R²=+0.39 | v_pred μ=+0.15 σ=0.155  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 63/100 | Total Loss:   2.30 (R²=+0.85, Policy:  2.23) | Val-R²=+0.39 | v_pred μ=+0.15 σ=0.155  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 64/100 | Total Loss:   2.29 (R²=+0.85, Policy:  2.23) | Val-R²=+0.40 | v_pred μ=+0.15 σ=0.155  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 65/100 | Total Loss:   2.29 (R²=+0.85, Policy:  2.23) | Val-R²=+0.39 | v_pred μ=+0.15 σ=0.155  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 66/100 | Total Loss:   2.29 (R²=+0.85, Policy:  2.23) | Val-R²=+0.39 | v_pred μ=+0.15 σ=0.155  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 67/100 | Total Loss:   2.29 (R²=+0.85, Policy:  2.23) | Val-R²=+0.39 | v_pred μ=+0.15 σ=0.155  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 68/100 | Total Loss:   2.29 (R²=+0.85, Policy:  2.23) | Val-R²=+0.39 | v_pred μ=+0.15 σ=0.156  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 69/100 | Total Loss:   2.29 (R²=+0.85, Policy:  2.23) | Val-R²=+0.39 | v_pred μ=+0.15 σ=0.156  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 70/100 | Total Loss:   2.29 (R²=+0.85, Policy:  2.23) | Val-R²=+0.39 | v_pred μ=+0.15 σ=0.156  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 71/100 | Total Loss:   2.29 (R²=+0.85, Policy:  2.23) | Val-R²=+0.39 | v_pred μ=+0.15 σ=0.156  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 72/100 | Total Loss:   2.29 (R²=+0.85, Policy:  2.23) | Val-R²=+0.39 | v_pred μ=+0.15 σ=0.156  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 73/100 | Total Loss:   2.28 (R²=+0.85, Policy:  2.22) | Val-R²=+0.39 | v_pred μ=+0.15 σ=0.156  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 74/100 | Total Loss:   2.28 (R²=+0.86, Policy:  2.22) | Val-R²=+0.39 | v_pred μ=+0.15 σ=0.156  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 75/100 | Total Loss:   2.29 (R²=+0.86, Policy:  2.23) | Val-R²=+0.39 | v_pred μ=+0.15 σ=0.156  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 76/100 | Total Loss:   2.28 (R²=+0.86, Policy:  2.22) | Val-R²=+0.39 | v_pred μ=+0.15 σ=0.156  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 77/100 | Total Loss:   2.28 (R²=+0.86, Policy:  2.22) | Val-R²=+0.39 | v_pred μ=+0.15 σ=0.156  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 78/100 | Total Loss:   2.28 (R²=+0.86, Policy:  2.22) | Val-R²=+0.38 | v_pred μ=+0.15 σ=0.156  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 79/100 | Total Loss:   2.28 (R²=+0.86, Policy:  2.22) | Val-R²=+0.38 | v_pred μ=+0.15 σ=0.156  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 80/100 | Total Loss:   2.28 (R²=+0.86, Policy:  2.22) | Val-R²=+0.38 | v_pred μ=+0.15 σ=0.156  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 81/100 | Total Loss:   2.28 (R²=+0.86, Policy:  2.22) | Val-R²=+0.38 | v_pred μ=+0.15 σ=0.156  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 82/100 | Total Loss:   2.28 (R²=+0.86, Policy:  2.22) | Val-R²=+0.38 | v_pred μ=+0.15 σ=0.156  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 83/100 | Total Loss:   2.28 (R²=+0.86, Policy:  2.22) | Val-R²=+0.38 | v_pred μ=+0.15 σ=0.156  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 84/100 | Total Loss:   2.28 (R²=+0.86, Policy:  2.22) | Val-R²=+0.38 | v_pred μ=+0.15 σ=0.156  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 85/100 | Total Loss:   2.28 (R²=+0.86, Policy:  2.22) | Val-R²=+0.38 | v_pred μ=+0.15 σ=0.156  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 86/100 | Total Loss:   2.28 (R²=+0.86, Policy:  2.22) | Val-R²=+0.38 | v_pred μ=+0.15 σ=0.156  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 87/100 | Total Loss:   2.28 (R²=+0.86, Policy:  2.22) | Val-R²=+0.38 | v_pred μ=+0.15 σ=0.156  🟡 POLICY-PLATEAU
Epoche 88/100 | Total Loss:   2.28 (R²=+0.86, Policy:  2.22) | Val-R²=+0.38 | v_pred μ=+0.15 σ=0.156  🟡 POLICY-PLATEAU
Epoche 89/100 | Total Loss:   2.27 (R²=+0.86, Policy:  2.22) | Val-R²=+0.38 | v_pred μ=+0.15 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 90/100 | Total Loss:   2.27 (R²=+0.86, Policy:  2.22) | Val-R²=+0.38 | v_pred μ=+0.15 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 91/100 | Total Loss:   2.27 (R²=+0.86, Policy:  2.21) | Val-R²=+0.37 | v_pred μ=+0.15 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 92/100 | Total Loss:   2.27 (R²=+0.86, Policy:  2.21) | Val-R²=+0.38 | v_pred μ=+0.15 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 93/100 | Total Loss:   2.27 (R²=+0.86, Policy:  2.22) | Val-R²=+0.37 | v_pred μ=+0.15 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 94/100 | Total Loss:   2.27 (R²=+0.86, Policy:  2.21) | Val-R²=+0.37 | v_pred μ=+0.15 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 95/100 | Total Loss:   2.27 (R²=+0.87, Policy:  2.21) | Val-R²=+0.38 | v_pred μ=+0.15 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 96/100 | Total Loss:   2.27 (R²=+0.87, Policy:  2.21) | Val-R²=+0.37 | v_pred μ=+0.15 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 97/100 | Total Loss:   2.27 (R²=+0.87, Policy:  2.21) | Val-R²=+0.38 | v_pred μ=+0.15 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 98/100 | Total Loss:   2.27 (R²=+0.87, Policy:  2.21) | Val-R²=+0.37 | v_pred μ=+0.15 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 99/100 | Total Loss:   2.27 (R²=+0.87, Policy:  2.21) | Val-R²=+0.38 | v_pred μ=+0.15 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 100/100 | Total Loss:   2.27 (R²=+0.87, Policy:  2.21) | Val-R²=+0.37 | v_pred μ=+0.15 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)

=======================================================
  TRAINING SUMMARY
=======================================================
  Epochen:       100
  Züge:          1,353,541  (+150,548 Val, nie trainiert)
  Batches/Epoche:5287
───────────────────────────────────────────────────────
  Policy Loss:   2.2108 / 6.18 max  (35.8%)  🟡 Gut
  Value Loss:    0.0037  (R²=0.87 ggü. Mittelwert-Baseline)  🟢 Sehr gut
  Value Val-R²:  0.37  (Gap ggü. Train: +0.50)  ⚠️  großer Train/Val-Abstand — Overfitting wahrscheinlich
───────────────────────────────────────────────────────
  🟢 Kein Plateau — Policy sinkt noch. Mehr Epochen möglich.
=======================================================

=======================================================
  NETZAUSLASTUNG (Hidden Size: 512)
───────────────────────────────────────────────────────
  Schicht          Dead   Aktiv-Rate        Eff.Rank
  ───────────────────────────────────────────────────
  layer1     0/512 (0%)          42%   221/512 (43%)
  layer2     0/512 (0%)          36%   217/512 (42%)
  layer3    13/512 (3%)          16%   211/512 (41%)
  ───────────────────────────────────────────────────
  🟢 Gesunde Auslastung (Dead 1%, Rank 42%).
=======================================================

✅ Training beendet! Neues Model gespeichert unter:
📂 D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v2b.pth
📈 Loss-Verlauf gespeichert unter:
📂 D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v2b_loss.png
✅ Exportiert: D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v2b.onnx  (input=684, hidden=512, value_hidden=128, opset=13)
📎 Referenz für Rust-Parität: D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v2b.onnx.ref.txt
```

**Stage 1 vs. Stage 2**

```
=======================================================
  STAGE-2-REIFEGRAD-SONDE (100 Spiele je Stufe, 400 Sims)
───────────────────────────────────────────────────────
  Stufe 1 (DFS-Blatt):   0:0  21.0% (21/100) | Ø Sieger-Score  10.7
  Stufe 2 (Netz-Value):  0:0  31.0% (31/100) | Ø Sieger-Score   5.8
  Verhältnis 0:0(Stufe2/Stufe1, geglättet): 1.45x
  🟢 GRÜN — Value-Head trägt, voller Stufe-2-Zyklus lohnt sich
=======================================================
```

**Arena vs. v1**

```
🏆 ERGEBNIS: v2b 58:42 v1 (58% A-Siege) in 1949.4s (0.1 Spiele/s)
   Ø Score: v2b 30.8 | v1 27.0
   0:0-Spiele: 0/100 (0.0%)
   Elo: v2b 1050 | v1 950
```

**Arena vs. Heuristik**

```

```
