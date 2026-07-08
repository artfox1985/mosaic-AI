trainiert mit 

- --games 4000 --mode mcts --sims 400

- --games 6000 --mode network --version v1 --sims 400 --stage 1

- --load v1

**Netzdaten**

```
PS D:\Archiv\Documents\Projekte\mosaic-AI> python train.py --name v2c --epochs 100 --load v1
📦 Lade HDF5-Cache (900 Dateien)...
Datensatz geladen: 1353541 Züge. (Features pro Zug: 684) — 21.5s
📦 Lade HDF5-Cache (100 Dateien)...
Datensatz geladen: 150548 Züge. (Features pro Zug: 684) — 2.5s
   Val-Split: 900 Trainings-Dateien / 100 Val-Dateien (1,353,541 / 150,548 Züge)
   Value-Ziel-Streuung: σ=0.168 (Varianz=0.0281, zum Vergleich mit v_pred σ unten; Varianz ist die Baseline-MSE bei reiner Mittelwert-Vorhersage)

🚀 Starte PyTorch Training auf: CUDA
🧠 Netz-Architektur: 684→512→512→512
⚙️  Hyperparameter (config.py):
   Learning Rate : 0.0004
   Value Weight  : 5
   Batch Size    : 256
   Value-Target  : tanh(eigen/50) - 0.1*tanh(gegner/50) (Endergebnis statt Win/Loss)
📥 Lade altes Model als Startpunkt: alphazero_v1.pth
   Epochen       : 100
🔄 Warm-Start erkannt: Trainiere für 100 Epochen.
Epoche  1/100 | Total Loss:   3.00 (R²=+0.56, Policy:  2.93) | Val-R²=+0.57 | v_pred μ=+0.15 σ=0.126
Epoche  2/100 | Total Loss:   2.82 (R²=+0.61, Policy:  2.77) | Val-R²=+0.54 | v_pred μ=+0.15 σ=0.132
Epoche  3/100 | Total Loss:   2.73 (R²=+0.64, Policy:  2.68) | Val-R²=+0.52 | v_pred μ=+0.15 σ=0.135
Epoche  4/100 | Total Loss:   2.65 (R²=+0.65, Policy:  2.61) | Val-R²=+0.51 | v_pred μ=+0.15 σ=0.137
Epoche  5/100 | Total Loss:   2.59 (R²=+0.66, Policy:  2.54) | Val-R²=+0.49 | v_pred μ=+0.15 σ=0.137
Epoche  6/100 | Total Loss:   2.54 (R²=+0.67, Policy:  2.49) | Val-R²=+0.48 | v_pred μ=+0.15 σ=0.138
Epoche  7/100 | Total Loss:   2.50 (R²=+0.68, Policy:  2.45) | Val-R²=+0.47 | v_pred μ=+0.15 σ=0.139
Epoche  8/100 | Total Loss:   2.47 (R²=+0.68, Policy:  2.42) | Val-R²=+0.46 | v_pred μ=+0.15 σ=0.139
Epoche  9/100 | Total Loss:   2.45 (R²=+0.69, Policy:  2.40) | Val-R²=+0.46 | v_pred μ=+0.15 σ=0.140
Epoche 10/100 | Total Loss:   2.43 (R²=+0.69, Policy:  2.38) | Val-R²=+0.45 | v_pred μ=+0.15 σ=0.140
Epoche 11/100 | Total Loss:   2.41 (R²=+0.69, Policy:  2.37) | Val-R²=+0.44 | v_pred μ=+0.15 σ=0.140
Epoche 12/100 | Total Loss:   2.40 (R²=+0.70, Policy:  2.36) | Val-R²=+0.43 | v_pred μ=+0.15 σ=0.141
Epoche 13/100 | Total Loss:   2.39 (R²=+0.70, Policy:  2.34) | Val-R²=+0.44 | v_pred μ=+0.15 σ=0.141
Epoche 14/100 | Total Loss:   2.38 (R²=+0.70, Policy:  2.34) | Val-R²=+0.43 | v_pred μ=+0.15 σ=0.141
Epoche 15/100 | Total Loss:   2.37 (R²=+0.70, Policy:  2.33) | Val-R²=+0.43 | v_pred μ=+0.15 σ=0.141
Epoche 16/100 | Total Loss:   2.36 (R²=+0.71, Policy:  2.32) | Val-R²=+0.43 | v_pred μ=+0.15 σ=0.142
Epoche 17/100 | Total Loss:   2.35 (R²=+0.71, Policy:  2.31) | Val-R²=+0.42 | v_pred μ=+0.15 σ=0.142
Epoche 18/100 | Total Loss:   2.35 (R²=+0.71, Policy:  2.31) | Val-R²=+0.41 | v_pred μ=+0.15 σ=0.142
Epoche 19/100 | Total Loss:   2.35 (R²=+0.71, Policy:  2.30) | Val-R²=+0.41 | v_pred μ=+0.15 σ=0.142
Epoche 20/100 | Total Loss:   2.34 (R²=+0.71, Policy:  2.30) | Val-R²=+0.41 | v_pred μ=+0.15 σ=0.142
Epoche 21/100 | Total Loss:   2.34 (R²=+0.71, Policy:  2.30) | Val-R²=+0.41 | v_pred μ=+0.15 σ=0.143
Epoche 22/100 | Total Loss:   2.33 (R²=+0.72, Policy:  2.29) | Val-R²=+0.39 | v_pred μ=+0.15 σ=0.143
Epoche 23/100 | Total Loss:   2.33 (R²=+0.72, Policy:  2.29) | Val-R²=+0.40 | v_pred μ=+0.15 σ=0.143
Epoche 24/100 | Total Loss:   2.33 (R²=+0.72, Policy:  2.29) | Val-R²=+0.40 | v_pred μ=+0.15 σ=0.143  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 25/100 | Total Loss:   2.32 (R²=+0.72, Policy:  2.29) | Val-R²=+0.40 | v_pred μ=+0.15 σ=0.143  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 26/100 | Total Loss:   2.32 (R²=+0.72, Policy:  2.28) | Val-R²=+0.41 | v_pred μ=+0.15 σ=0.143  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 27/100 | Total Loss:   2.32 (R²=+0.72, Policy:  2.28) | Val-R²=+0.40 | v_pred μ=+0.15 σ=0.144  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 28/100 | Total Loss:   2.32 (R²=+0.72, Policy:  2.28) | Val-R²=+0.40 | v_pred μ=+0.15 σ=0.144  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 29/100 | Total Loss:   2.31 (R²=+0.72, Policy:  2.27) | Val-R²=+0.40 | v_pred μ=+0.15 σ=0.144  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 30/100 | Total Loss:   2.31 (R²=+0.73, Policy:  2.27) | Val-R²=+0.41 | v_pred μ=+0.15 σ=0.144  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 31/100 | Total Loss:   2.31 (R²=+0.73, Policy:  2.27) | Val-R²=+0.40 | v_pred μ=+0.15 σ=0.144  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 32/100 | Total Loss:   2.31 (R²=+0.73, Policy:  2.27) | Val-R²=+0.39 | v_pred μ=+0.15 σ=0.144  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 33/100 | Total Loss:   2.30 (R²=+0.73, Policy:  2.27) | Val-R²=+0.39 | v_pred μ=+0.15 σ=0.144  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 34/100 | Total Loss:   2.30 (R²=+0.73, Policy:  2.26) | Val-R²=+0.39 | v_pred μ=+0.15 σ=0.144  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 35/100 | Total Loss:   2.30 (R²=+0.73, Policy:  2.26) | Val-R²=+0.39 | v_pred μ=+0.15 σ=0.144  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 36/100 | Total Loss:   2.30 (R²=+0.73, Policy:  2.26) | Val-R²=+0.39 | v_pred μ=+0.15 σ=0.145  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 37/100 | Total Loss:   2.30 (R²=+0.73, Policy:  2.26) | Val-R²=+0.39 | v_pred μ=+0.15 σ=0.145  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 38/100 | Total Loss:   2.29 (R²=+0.74, Policy:  2.26) | Val-R²=+0.38 | v_pred μ=+0.15 σ=0.145  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 39/100 | Total Loss:   2.29 (R²=+0.74, Policy:  2.25) | Val-R²=+0.38 | v_pred μ=+0.15 σ=0.145  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 40/100 | Total Loss:   2.29 (R²=+0.74, Policy:  2.25) | Val-R²=+0.39 | v_pred μ=+0.15 σ=0.145  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 41/100 | Total Loss:   2.29 (R²=+0.74, Policy:  2.25) | Val-R²=+0.38 | v_pred μ=+0.15 σ=0.145  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 42/100 | Total Loss:   2.29 (R²=+0.74, Policy:  2.25) | Val-R²=+0.39 | v_pred μ=+0.15 σ=0.145  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 43/100 | Total Loss:   2.29 (R²=+0.74, Policy:  2.25) | Val-R²=+0.39 | v_pred μ=+0.15 σ=0.145  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 44/100 | Total Loss:   2.28 (R²=+0.74, Policy:  2.25) | Val-R²=+0.39 | v_pred μ=+0.15 σ=0.145  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 45/100 | Total Loss:   2.28 (R²=+0.74, Policy:  2.25) | Val-R²=+0.38 | v_pred μ=+0.15 σ=0.146  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 46/100 | Total Loss:   2.28 (R²=+0.74, Policy:  2.25) | Val-R²=+0.37 | v_pred μ=+0.15 σ=0.146  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 47/100 | Total Loss:   2.28 (R²=+0.74, Policy:  2.24) | Val-R²=+0.37 | v_pred μ=+0.15 σ=0.146  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 48/100 | Total Loss:   2.28 (R²=+0.74, Policy:  2.24) | Val-R²=+0.38 | v_pred μ=+0.15 σ=0.146  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 49/100 | Total Loss:   2.28 (R²=+0.75, Policy:  2.24) | Val-R²=+0.37 | v_pred μ=+0.15 σ=0.146  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 50/100 | Total Loss:   2.28 (R²=+0.75, Policy:  2.24) | Val-R²=+0.38 | v_pred μ=+0.15 σ=0.146  🟡 POLICY-PLATEAU
Epoche 51/100 | Total Loss:   2.27 (R²=+0.75, Policy:  2.24) | Val-R²=+0.37 | v_pred μ=+0.15 σ=0.146  🟡 POLICY-PLATEAU
Epoche 52/100 | Total Loss:   2.27 (R²=+0.75, Policy:  2.24) | Val-R²=+0.38 | v_pred μ=+0.15 σ=0.146  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 53/100 | Total Loss:   2.27 (R²=+0.75, Policy:  2.24) | Val-R²=+0.37 | v_pred μ=+0.15 σ=0.146  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 54/100 | Total Loss:   2.27 (R²=+0.75, Policy:  2.24) | Val-R²=+0.38 | v_pred μ=+0.15 σ=0.146  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 55/100 | Total Loss:   2.27 (R²=+0.75, Policy:  2.24) | Val-R²=+0.38 | v_pred μ=+0.15 σ=0.146  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 56/100 | Total Loss:   2.27 (R²=+0.75, Policy:  2.24) | Val-R²=+0.37 | v_pred μ=+0.15 σ=0.146  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 57/100 | Total Loss:   2.27 (R²=+0.75, Policy:  2.23) | Val-R²=+0.37 | v_pred μ=+0.15 σ=0.146  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 58/100 | Total Loss:   2.27 (R²=+0.75, Policy:  2.23) | Val-R²=+0.38 | v_pred μ=+0.15 σ=0.147  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 59/100 | Total Loss:   2.27 (R²=+0.75, Policy:  2.23) | Val-R²=+0.37 | v_pred μ=+0.15 σ=0.147  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 60/100 | Total Loss:   2.27 (R²=+0.75, Policy:  2.23) | Val-R²=+0.38 | v_pred μ=+0.15 σ=0.147  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 61/100 | Total Loss:   2.26 (R²=+0.76, Policy:  2.23) | Val-R²=+0.37 | v_pred μ=+0.15 σ=0.147  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 62/100 | Total Loss:   2.27 (R²=+0.76, Policy:  2.23) | Val-R²=+0.37 | v_pred μ=+0.15 σ=0.147  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 63/100 | Total Loss:   2.26 (R²=+0.76, Policy:  2.23) | Val-R²=+0.37 | v_pred μ=+0.15 σ=0.147  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 64/100 | Total Loss:   2.26 (R²=+0.76, Policy:  2.23) | Val-R²=+0.38 | v_pred μ=+0.15 σ=0.147  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 65/100 | Total Loss:   2.26 (R²=+0.76, Policy:  2.23) | Val-R²=+0.37 | v_pred μ=+0.15 σ=0.147  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 66/100 | Total Loss:   2.26 (R²=+0.76, Policy:  2.23) | Val-R²=+0.38 | v_pred μ=+0.15 σ=0.147  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 67/100 | Total Loss:   2.26 (R²=+0.76, Policy:  2.23) | Val-R²=+0.36 | v_pred μ=+0.15 σ=0.147  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 68/100 | Total Loss:   2.26 (R²=+0.76, Policy:  2.22) | Val-R²=+0.36 | v_pred μ=+0.15 σ=0.147  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 69/100 | Total Loss:   2.26 (R²=+0.76, Policy:  2.23) | Val-R²=+0.38 | v_pred μ=+0.15 σ=0.147  🟡 POLICY-PLATEAU
Epoche 70/100 | Total Loss:   2.26 (R²=+0.76, Policy:  2.23) | Val-R²=+0.38 | v_pred μ=+0.15 σ=0.147  🟡 POLICY-PLATEAU
Epoche 71/100 | Total Loss:   2.26 (R²=+0.76, Policy:  2.22) | Val-R²=+0.37 | v_pred μ=+0.15 σ=0.147  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 72/100 | Total Loss:   2.26 (R²=+0.76, Policy:  2.23) | Val-R²=+0.38 | v_pred μ=+0.15 σ=0.147  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 73/100 | Total Loss:   2.25 (R²=+0.76, Policy:  2.22) | Val-R²=+0.38 | v_pred μ=+0.15 σ=0.148  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 74/100 | Total Loss:   2.26 (R²=+0.76, Policy:  2.22) | Val-R²=+0.37 | v_pred μ=+0.15 σ=0.148  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 75/100 | Total Loss:   2.25 (R²=+0.76, Policy:  2.22) | Val-R²=+0.37 | v_pred μ=+0.15 σ=0.148  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 76/100 | Total Loss:   2.25 (R²=+0.77, Policy:  2.22) | Val-R²=+0.37 | v_pred μ=+0.15 σ=0.148  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 77/100 | Total Loss:   2.25 (R²=+0.77, Policy:  2.22) | Val-R²=+0.37 | v_pred μ=+0.15 σ=0.148  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 78/100 | Total Loss:   2.25 (R²=+0.77, Policy:  2.22) | Val-R²=+0.37 | v_pred μ=+0.15 σ=0.148  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 79/100 | Total Loss:   2.25 (R²=+0.77, Policy:  2.22) | Val-R²=+0.37 | v_pred μ=+0.15 σ=0.148  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 80/100 | Total Loss:   2.25 (R²=+0.77, Policy:  2.22) | Val-R²=+0.37 | v_pred μ=+0.15 σ=0.148  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 81/100 | Total Loss:   2.25 (R²=+0.77, Policy:  2.22) | Val-R²=+0.37 | v_pred μ=+0.15 σ=0.148  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 82/100 | Total Loss:   2.25 (R²=+0.77, Policy:  2.22) | Val-R²=+0.37 | v_pred μ=+0.15 σ=0.148  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 83/100 | Total Loss:   2.25 (R²=+0.77, Policy:  2.22) | Val-R²=+0.36 | v_pred μ=+0.15 σ=0.148  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 84/100 | Total Loss:   2.25 (R²=+0.77, Policy:  2.22) | Val-R²=+0.36 | v_pred μ=+0.15 σ=0.148  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 85/100 | Total Loss:   2.25 (R²=+0.77, Policy:  2.22) | Val-R²=+0.37 | v_pred μ=+0.15 σ=0.148  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 86/100 | Total Loss:   2.25 (R²=+0.77, Policy:  2.21) | Val-R²=+0.36 | v_pred μ=+0.15 σ=0.148  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 87/100 | Total Loss:   2.25 (R²=+0.77, Policy:  2.21) | Val-R²=+0.36 | v_pred μ=+0.15 σ=0.148  🟡 POLICY-PLATEAU
Epoche 88/100 | Total Loss:   2.25 (R²=+0.77, Policy:  2.21) | Val-R²=+0.36 | v_pred μ=+0.15 σ=0.148  🟡 POLICY-PLATEAU
Epoche 89/100 | Total Loss:   2.25 (R²=+0.77, Policy:  2.21) | Val-R²=+0.36 | v_pred μ=+0.15 σ=0.149  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 90/100 | Total Loss:   2.24 (R²=+0.77, Policy:  2.21) | Val-R²=+0.36 | v_pred μ=+0.15 σ=0.149  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 91/100 | Total Loss:   2.24 (R²=+0.77, Policy:  2.21) | Val-R²=+0.37 | v_pred μ=+0.15 σ=0.149  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 92/100 | Total Loss:   2.24 (R²=+0.77, Policy:  2.21) | Val-R²=+0.37 | v_pred μ=+0.15 σ=0.149  🟡 POLICY-PLATEAU
Epoche 93/100 | Total Loss:   2.24 (R²=+0.77, Policy:  2.21) | Val-R²=+0.36 | v_pred μ=+0.15 σ=0.149  🟡 POLICY-PLATEAU
Epoche 94/100 | Total Loss:   2.24 (R²=+0.78, Policy:  2.21) | Val-R²=+0.36 | v_pred μ=+0.15 σ=0.149  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 95/100 | Total Loss:   2.24 (R²=+0.78, Policy:  2.21) | Val-R²=+0.36 | v_pred μ=+0.15 σ=0.149  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 96/100 | Total Loss:   2.24 (R²=+0.78, Policy:  2.21) | Val-R²=+0.34 | v_pred μ=+0.15 σ=0.149  🟡 PLATEAU (Policy+Value)
Epoche 97/100 | Total Loss:   2.24 (R²=+0.78, Policy:  2.21) | Val-R²=+0.36 | v_pred μ=+0.15 σ=0.149  🟡 PLATEAU (Policy+Value)
Epoche 98/100 | Total Loss:   2.24 (R²=+0.78, Policy:  2.21) | Val-R²=+0.36 | v_pred μ=+0.15 σ=0.149  🟡 PLATEAU (Policy+Value)
Epoche 99/100 | Total Loss:   2.24 (R²=+0.78, Policy:  2.21) | Val-R²=+0.36 | v_pred μ=+0.15 σ=0.149  🟡 PLATEAU (Policy+Value)
Epoche 100/100 | Total Loss:   2.24 (R²=+0.78, Policy:  2.21) | Val-R²=+0.37 | v_pred μ=+0.15 σ=0.149  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)

=======================================================
  TRAINING SUMMARY
=======================================================
  Epochen:       100
  Züge:          1,353,541  (+150,548 Val, nie trainiert)
  Batches/Epoche:5287
───────────────────────────────────────────────────────
  Policy Loss:   2.2072 / 6.18 max  (35.7%)  🟡 Gut
  Value Loss:    0.0062  (R²=0.78 ggü. Mittelwert-Baseline)  🟢 Sehr gut
  Value Val-R²:  0.37  (Gap ggü. Train: +0.41)  ⚠️  großer Train/Val-Abstand — Overfitting wahrscheinlich
───────────────────────────────────────────────────────
  🟡 Plateau ab Epoche 96.
     → Für nächste Generation: mehr Sims im Self-Play.
=======================================================
```

**Stage 1 vs. Stage 2**

```

```

**Arena vs. v1**

```

```

**Arena vs. Heuristik**

```

```
