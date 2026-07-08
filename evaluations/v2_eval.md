trainiert mit 

- --games 4000 --mode mcts --sims 400

- --games 6000 --mode network --version v1 --sims 400 --stage 1

**Netzdaten**

```
PS D:\Archiv\Documents\Projekte\mosaic-AI> python train.py --name v2 --epochs 100
Lade Daten aus 900 Dateien...
Datensatz geladen: 1353541 Züge. (Features pro Zug: 684) — 505.9s
💾 Speichere HDF5-Cache...
✅ Cache gespeichert: D:\Archiv\Documents\Projekte\mosaic-AI\data\.cache_1fc43aec29f7.h5
Lade Daten aus 100 Dateien...
Datensatz geladen: 150548 Züge. (Features pro Zug: 684) — 61.9s
💾 Speichere HDF5-Cache...
✅ Cache gespeichert: D:\Archiv\Documents\Projekte\mosaic-AI\data\.cache_9807fc331262.h5
   Val-Split: 900 Trainings-Dateien / 100 Val-Dateien (1,353,541 / 150,548 Züge)
   Value-Ziel-Streuung: σ=0.168 (Varianz=0.0281, zum Vergleich mit v_pred σ unten; Varianz ist die Baseline-MSE bei reiner Mittelwert-Vorhersage)

🚀 Starte PyTorch Training auf: CUDA
🧠 Netz-Architektur: 684→512→512→512
⚙️  Hyperparameter (config.py):
   Learning Rate : 0.0004
   Value Weight  : 15
   Batch Size    : 256
   Value-Target  : tanh(eigen/50) - 0.1*tanh(gegner/50) (Endergebnis statt Win/Loss)
   Epochen       : 100
🆕 Neues Modell: Trainiere für 100 Epochen.
Epoche  1/100 | Total Loss:   3.17 (R²=+0.69, Policy:  3.04) | Val-R²=+0.22 | v_pred μ=+0.15 σ=0.139
Epoche  2/100 | Total Loss:   3.07 (R²=+0.86, Policy:  3.01) | Val-R²=+0.23 | v_pred μ=+0.15 σ=0.156
Epoche  3/100 | Total Loss:   3.04 (R²=+0.89, Policy:  2.99) | Val-R²=+0.20 | v_pred μ=+0.15 σ=0.158
Epoche  4/100 | Total Loss:   3.02 (R²=+0.89, Policy:  2.98) | Val-R²=+0.20 | v_pred μ=+0.15 σ=0.159
Epoche  5/100 | Total Loss:   3.00 (R²=+0.89, Policy:  2.95) | Val-R²=+0.19 | v_pred μ=+0.15 σ=0.158
Epoche  6/100 | Total Loss:   2.97 (R²=+0.88, Policy:  2.91) | Val-R²=+0.18 | v_pred μ=+0.15 σ=0.158
Epoche  7/100 | Total Loss:   2.92 (R²=+0.87, Policy:  2.86) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.157
Epoche  8/100 | Total Loss:   2.86 (R²=+0.87, Policy:  2.81) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.156
Epoche  9/100 | Total Loss:   2.81 (R²=+0.86, Policy:  2.75) | Val-R²=+0.18 | v_pred μ=+0.15 σ=0.156
Epoche 10/100 | Total Loss:   2.76 (R²=+0.86, Policy:  2.70) | Val-R²=+0.17 | v_pred μ=+0.15 σ=0.156
Epoche 11/100 | Total Loss:   2.72 (R²=+0.86, Policy:  2.66) | Val-R²=+0.17 | v_pred μ=+0.15 σ=0.156
Epoche 12/100 | Total Loss:   2.69 (R²=+0.86, Policy:  2.62) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.155
Epoche 13/100 | Total Loss:   2.65 (R²=+0.85, Policy:  2.59) | Val-R²=+0.19 | v_pred μ=+0.15 σ=0.155
Epoche 14/100 | Total Loss:   2.63 (R²=+0.85, Policy:  2.56) | Val-R²=+0.18 | v_pred μ=+0.15 σ=0.155
Epoche 15/100 | Total Loss:   2.61 (R²=+0.85, Policy:  2.55) | Val-R²=+0.18 | v_pred μ=+0.15 σ=0.155
Epoche 16/100 | Total Loss:   2.58 (R²=+0.85, Policy:  2.52) | Val-R²=+0.18 | v_pred μ=+0.15 σ=0.155
Epoche 17/100 | Total Loss:   2.57 (R²=+0.85, Policy:  2.51) | Val-R²=+0.17 | v_pred μ=+0.15 σ=0.155
Epoche 18/100 | Total Loss:   2.55 (R²=+0.85, Policy:  2.49) | Val-R²=+0.18 | v_pred μ=+0.15 σ=0.155
Epoche 19/100 | Total Loss:   2.54 (R²=+0.85, Policy:  2.47) | Val-R²=+0.17 | v_pred μ=+0.15 σ=0.155
Epoche 20/100 | Total Loss:   2.52 (R²=+0.85, Policy:  2.46) | Val-R²=+0.18 | v_pred μ=+0.15 σ=0.155
Epoche 21/100 | Total Loss:   2.51 (R²=+0.86, Policy:  2.45) | Val-R²=+0.18 | v_pred μ=+0.15 σ=0.156
Epoche 22/100 | Total Loss:   2.50 (R²=+0.86, Policy:  2.44) | Val-R²=+0.17 | v_pred μ=+0.15 σ=0.156
Epoche 23/100 | Total Loss:   2.49 (R²=+0.86, Policy:  2.43) | Val-R²=+0.17 | v_pred μ=+0.15 σ=0.156
Epoche 24/100 | Total Loss:   2.49 (R²=+0.86, Policy:  2.43) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.156
Epoche 25/100 | Total Loss:   2.48 (R²=+0.86, Policy:  2.42) | Val-R²=+0.18 | v_pred μ=+0.15 σ=0.156
Epoche 26/100 | Total Loss:   2.47 (R²=+0.86, Policy:  2.41) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.156
Epoche 27/100 | Total Loss:   2.46 (R²=+0.86, Policy:  2.40) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.156
Epoche 28/100 | Total Loss:   2.46 (R²=+0.86, Policy:  2.40) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.156
Epoche 29/100 | Total Loss:   2.45 (R²=+0.86, Policy:  2.39) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.156
Epoche 30/100 | Total Loss:   2.44 (R²=+0.86, Policy:  2.38) | Val-R²=+0.15 | v_pred μ=+0.15 σ=0.156
Epoche 31/100 | Total Loss:   2.43 (R²=+0.86, Policy:  2.38) | Val-R²=+0.15 | v_pred μ=+0.15 σ=0.156
Epoche 32/100 | Total Loss:   2.43 (R²=+0.86, Policy:  2.37) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.156
Epoche 33/100 | Total Loss:   2.43 (R²=+0.86, Policy:  2.37) | Val-R²=+0.17 | v_pred μ=+0.15 σ=0.156
Epoche 34/100 | Total Loss:   2.42 (R²=+0.87, Policy:  2.36) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.156
Epoche 35/100 | Total Loss:   2.41 (R²=+0.87, Policy:  2.36) | Val-R²=+0.17 | v_pred μ=+0.15 σ=0.156
Epoche 36/100 | Total Loss:   2.41 (R²=+0.87, Policy:  2.35) | Val-R²=+0.17 | v_pred μ=+0.15 σ=0.157
Epoche 37/100 | Total Loss:   2.41 (R²=+0.87, Policy:  2.35) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 38/100 | Total Loss:   2.40 (R²=+0.87, Policy:  2.35) | Val-R²=+0.17 | v_pred μ=+0.15 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 39/100 | Total Loss:   2.40 (R²=+0.87, Policy:  2.34) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 40/100 | Total Loss:   2.40 (R²=+0.87, Policy:  2.34) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 41/100 | Total Loss:   2.39 (R²=+0.87, Policy:  2.34) | Val-R²=+0.15 | v_pred μ=+0.15 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 42/100 | Total Loss:   2.39 (R²=+0.87, Policy:  2.33) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 43/100 | Total Loss:   2.38 (R²=+0.87, Policy:  2.33) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 44/100 | Total Loss:   2.38 (R²=+0.87, Policy:  2.33) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 45/100 | Total Loss:   2.38 (R²=+0.87, Policy:  2.33) | Val-R²=+0.17 | v_pred μ=+0.15 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 46/100 | Total Loss:   2.37 (R²=+0.87, Policy:  2.32) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 47/100 | Total Loss:   2.37 (R²=+0.87, Policy:  2.32) | Val-R²=+0.17 | v_pred μ=+0.15 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 48/100 | Total Loss:   2.37 (R²=+0.88, Policy:  2.32) | Val-R²=+0.17 | v_pred μ=+0.15 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 49/100 | Total Loss:   2.37 (R²=+0.88, Policy:  2.31) | Val-R²=+0.17 | v_pred μ=+0.15 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 50/100 | Total Loss:   2.36 (R²=+0.88, Policy:  2.31) | Val-R²=+0.17 | v_pred μ=+0.15 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 51/100 | Total Loss:   2.36 (R²=+0.88, Policy:  2.31) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.157  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 52/100 | Total Loss:   2.36 (R²=+0.88, Policy:  2.30) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 53/100 | Total Loss:   2.35 (R²=+0.88, Policy:  2.30) | Val-R²=+0.18 | v_pred μ=+0.15 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 54/100 | Total Loss:   2.35 (R²=+0.88, Policy:  2.30) | Val-R²=+0.17 | v_pred μ=+0.15 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 55/100 | Total Loss:   2.35 (R²=+0.88, Policy:  2.30) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.158  🟡 POLICY-PLATEAU
Epoche 56/100 | Total Loss:   2.35 (R²=+0.88, Policy:  2.30) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.158  🟡 POLICY-PLATEAU
Epoche 57/100 | Total Loss:   2.35 (R²=+0.88, Policy:  2.30) | Val-R²=+0.17 | v_pred μ=+0.15 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 58/100 | Total Loss:   2.34 (R²=+0.88, Policy:  2.29) | Val-R²=+0.18 | v_pred μ=+0.15 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 59/100 | Total Loss:   2.34 (R²=+0.88, Policy:  2.29) | Val-R²=+0.17 | v_pred μ=+0.15 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 60/100 | Total Loss:   2.34 (R²=+0.88, Policy:  2.29) | Val-R²=+0.17 | v_pred μ=+0.15 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 61/100 | Total Loss:   2.34 (R²=+0.88, Policy:  2.29) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 62/100 | Total Loss:   2.33 (R²=+0.88, Policy:  2.28) | Val-R²=+0.17 | v_pred μ=+0.15 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 63/100 | Total Loss:   2.33 (R²=+0.88, Policy:  2.28) | Val-R²=+0.17 | v_pred μ=+0.15 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 64/100 | Total Loss:   2.33 (R²=+0.88, Policy:  2.28) | Val-R²=+0.17 | v_pred μ=+0.15 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 65/100 | Total Loss:   2.33 (R²=+0.88, Policy:  2.28) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 66/100 | Total Loss:   2.33 (R²=+0.88, Policy:  2.28) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 67/100 | Total Loss:   2.33 (R²=+0.88, Policy:  2.28) | Val-R²=+0.17 | v_pred μ=+0.15 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 68/100 | Total Loss:   2.32 (R²=+0.88, Policy:  2.27) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 69/100 | Total Loss:   2.32 (R²=+0.88, Policy:  2.27) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 70/100 | Total Loss:   2.32 (R²=+0.89, Policy:  2.27) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 71/100 | Total Loss:   2.32 (R²=+0.89, Policy:  2.27) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 72/100 | Total Loss:   2.32 (R²=+0.89, Policy:  2.27) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 73/100 | Total Loss:   2.32 (R²=+0.89, Policy:  2.27) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 74/100 | Total Loss:   2.31 (R²=+0.89, Policy:  2.27) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 75/100 | Total Loss:   2.31 (R²=+0.89, Policy:  2.27) | Val-R²=+0.15 | v_pred μ=+0.15 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 76/100 | Total Loss:   2.31 (R²=+0.89, Policy:  2.26) | Val-R²=+0.17 | v_pred μ=+0.15 σ=0.158  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 77/100 | Total Loss:   2.31 (R²=+0.89, Policy:  2.26) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.159  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 78/100 | Total Loss:   2.31 (R²=+0.89, Policy:  2.26) | Val-R²=+0.17 | v_pred μ=+0.15 σ=0.159  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 79/100 | Total Loss:   2.31 (R²=+0.89, Policy:  2.26) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.159  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 80/100 | Total Loss:   2.31 (R²=+0.89, Policy:  2.26) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.159  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 81/100 | Total Loss:   2.30 (R²=+0.89, Policy:  2.26) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.159  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 82/100 | Total Loss:   2.30 (R²=+0.89, Policy:  2.25) | Val-R²=+0.17 | v_pred μ=+0.15 σ=0.159  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 83/100 | Total Loss:   2.30 (R²=+0.89, Policy:  2.25) | Val-R²=+0.17 | v_pred μ=+0.15 σ=0.159  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 84/100 | Total Loss:   2.30 (R²=+0.89, Policy:  2.25) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.159  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 85/100 | Total Loss:   2.30 (R²=+0.89, Policy:  2.25) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.159  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 86/100 | Total Loss:   2.30 (R²=+0.89, Policy:  2.25) | Val-R²=+0.17 | v_pred μ=+0.15 σ=0.159  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 87/100 | Total Loss:   2.29 (R²=+0.89, Policy:  2.25) | Val-R²=+0.17 | v_pred μ=+0.15 σ=0.159  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 88/100 | Total Loss:   2.29 (R²=+0.89, Policy:  2.25) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.159  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 89/100 | Total Loss:   2.29 (R²=+0.89, Policy:  2.25) | Val-R²=+0.17 | v_pred μ=+0.15 σ=0.159  🟡 POLICY-PLATEAU
Epoche 90/100 | Total Loss:   2.29 (R²=+0.89, Policy:  2.25) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.159  🟡 POLICY-PLATEAU
Epoche 91/100 | Total Loss:   2.29 (R²=+0.89, Policy:  2.24) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.159  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 92/100 | Total Loss:   2.29 (R²=+0.89, Policy:  2.24) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.159  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 93/100 | Total Loss:   2.29 (R²=+0.89, Policy:  2.24) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.159  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 94/100 | Total Loss:   2.29 (R²=+0.89, Policy:  2.24) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.159  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 95/100 | Total Loss:   2.29 (R²=+0.89, Policy:  2.24) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.159  🟡 POLICY-PLATEAU
Epoche 96/100 | Total Loss:   2.29 (R²=+0.89, Policy:  2.24) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.159  🟡 POLICY-PLATEAU
Epoche 97/100 | Total Loss:   2.28 (R²=+0.89, Policy:  2.24) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.159  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 98/100 | Total Loss:   2.28 (R²=+0.89, Policy:  2.24) | Val-R²=+0.17 | v_pred μ=+0.15 σ=0.159  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 99/100 | Total Loss:   2.28 (R²=+0.89, Policy:  2.24) | Val-R²=+0.17 | v_pred μ=+0.15 σ=0.159  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 100/100 | Total Loss:   2.28 (R²=+0.90, Policy:  2.24) | Val-R²=+0.16 | v_pred μ=+0.15 σ=0.159  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)

=======================================================
  TRAINING SUMMARY
=======================================================
  Epochen:       100
  Züge:          1,353,541  (+150,548 Val, nie trainiert)
  Batches/Epoche:5287
───────────────────────────────────────────────────────
  Policy Loss:   2.2374 / 6.18 max  (36.2%)  🟡 Gut
  Value Loss:    0.0029  (R²=0.90 ggü. Mittelwert-Baseline)  🟢 Sehr gut
  Value Val-R²:  0.16  (Gap ggü. Train: +0.73)  ⚠️  großer Train/Val-Abstand — Overfitting wahrscheinlich
───────────────────────────────────────────────────────
  🟢 Kein Plateau — Policy sinkt noch. Mehr Epochen möglich.
=======================================================

=======================================================
  NETZAUSLASTUNG (Hidden Size: 512)
───────────────────────────────────────────────────────
  Schicht          Dead   Aktiv-Rate        Eff.Rank
  ───────────────────────────────────────────────────
  layer1     0/512 (0%)          41%   221/512 (43%)
  layer2     0/512 (0%)          36%   217/512 (42%)
  layer3    27/512 (5%)          14%   209/512 (41%)
  ───────────────────────────────────────────────────
  🟢 Gesunde Auslastung (Dead 2%, Rank 42%).
=======================================================

✅ Training beendet! Neues Model gespeichert unter:
📂 D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v2.pth
📈 Loss-Verlauf gespeichert unter:
📂 D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v2_loss.png
✅ Exportiert: D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v2.onnx  (input=684, hidden=512, value_hidden=128, opset=13)
📎 Referenz für Rust-Parität: D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v2.onnx.ref.txt
```

**Stage 1 vs. Stage 2**

```
=======================================================
  STAGE-2-REIFEGRAD-SONDE (100 Spiele je Stufe, 400 Sims)
───────────────────────────────────────────────────────
  Stufe 1 (DFS-Blatt):   0:0  18.0% (18/100) | Ø Sieger-Score  11.4
  Stufe 2 (Netz-Value):  0:0  39.0% (39/100) | Ø Sieger-Score   6.5
  Verhältnis 0:0(Stufe2/Stufe1, geglättet): 2.11x
  🟡 GELB — noch nicht reif, Trend über Generationen beobachten
=======================================================
```

**Arena vs. v1**

```
🏟️ Mosaic-AI ARENA — Netz vs Netz (Rust) 🏟️
  v2 (Brett 0, 200 Sims, c_puct=1.5) vs v1 (Brett 1, 200 Sims, c_puct=1.5) — Stufe 1/DFS-Blatt — 100 Spiele
--------------------------------------------------
  #  1/100:  54:22  -> v2                     | Züge 163 | Strength 1.000 | Stand v2 1:0 v1 | Elo 1016/984
  #  2/100:  40:17  -> v2                     | Züge 163 | Strength 1.000 | Stand v2 2:0 v1 | Elo 1031/969
  #  3/100:  50:17  -> v2                     | Züge 159 | Strength 1.000 | Stand v2 3:0 v1 | Elo 1044/956
  #  4/100:  26:6   -> v2                     | Züge 160 | Strength 0.843 | Stand v2 4:0 v1 | Elo 1054/946
  #  5/100:  34:39  -> v1                     | Züge 158 | Strength 0.689 | Stand v2 4:1 v1 | Elo 1040/960
  #  6/100:  14:23  -> v1                     | Züge 155 | Strength 0.629 | Stand v2 4:2 v1 | Elo 1028/972
  #  7/100:  33:13  -> v2                     | Züge 158 | Strength 0.921 | Stand v2 5:2 v1 | Elo 1040/960
  #  8/100:  44:43  -> v2                     | Züge 167 | Strength 0.580 | Stand v2 6:2 v1 | Elo 1047/953
  #  9/100:  38:14  -> v2                     | Züge 163 | Strength 0.978 | Stand v2 7:2 v1 | Elo 1059/941
  # 10/100:  51:31  -> v2                     | Züge 157 | Strength 1.000 | Stand v2 8:2 v1 | Elo 1070/930
  # 11/100:  36:56  -> v1                     | Züge 160 | Strength 1.000 | Stand v2 8:3 v1 | Elo 1048/952
  # 12/100:  19:11  -> v2                     | Züge 155 | Strength 0.554 | Stand v2 9:3 v1 | Elo 1054/946
  # 13/100:  32:36  -> v1                     | Züge 159 | Strength 0.625 | Stand v2 9:4 v1 | Elo 1041/959
  # 14/100:  14:23  -> v1                     | Züge 164 | Strength 0.629 | Stand v2 9:5 v1 | Elo 1029/971
  # 15/100:  35:23  -> v2                     | Züge 161 | Strength 0.854 | Stand v2 10:5 v1 | Elo 1040/960
  # 16/100:  55:24  -> v2                     | Züge 164 | Strength 1.000 | Stand v2 11:5 v1 | Elo 1052/948
  # 17/100:  41:22  -> v2                     | Züge 152 | Strength 1.000 | Stand v2 12:5 v1 | Elo 1063/937
  # 18/100:  55:25  -> v2                     | Züge 164 | Strength 1.000 | Stand v2 13:5 v1 | Elo 1073/927
  # 19/100:  35:1   -> v2                     | Züge 161 | Strength 0.944 | Stand v2 14:5 v1 | Elo 1082/918
  # 20/100:  36:25  -> v2                     | Züge 166 | Strength 0.835 | Stand v2 15:5 v1 | Elo 1089/911
  # 21/100:  15:4   -> v2                     | Züge 159 | Strength 0.599 | Stand v2 16:5 v1 | Elo 1094/906
  # 22/100:  19:44  -> v1                     | Züge 161 | Strength 1.000 | Stand v2 16:6 v1 | Elo 1070/930
  # 23/100:  46:25  -> v2                     | Züge 155 | Strength 1.000 | Stand v2 17:6 v1 | Elo 1080/920
  # 24/100:  43:40  -> v2                     | Züge 160 | Strength 0.640 | Stand v2 18:6 v1 | Elo 1086/914
  # 25/100:  31:29  -> v2                     | Züge 159 | Strength 0.509 | Stand v2 19:6 v1 | Elo 1090/910
  # 26/100:  15:48  -> v1                     | Züge 157 | Strength 1.000 | Stand v2 19:7 v1 | Elo 1066/934
  # 27/100:  37:31  -> v2                     | Züge 162 | Strength 0.696 | Stand v2 20:7 v1 | Elo 1073/927
  # 28/100:  37:21  -> v2                     | Züge 156 | Strength 0.966 | Stand v2 21:7 v1 | Elo 1082/918
  # 29/100:  23:19  -> v2                     | Züge 156 | Strength 0.479 | Stand v2 22:7 v1 | Elo 1086/914
  # 30/100:  32:3   -> v2                     | Züge 158 | Strength 0.910 | Stand v2 23:7 v1 | Elo 1094/906
  # 31/100:  49:15  -> v2                     | Züge 163 | Strength 1.000 | Stand v2 24:7 v1 | Elo 1102/898
  # 32/100:  47:28  -> v2                     | Züge 155 | Strength 1.000 | Stand v2 25:7 v1 | Elo 1110/890
  # 33/100:  40:24  -> v2                     | Züge 159 | Strength 1.000 | Stand v2 26:7 v1 | Elo 1117/883
  # 34/100:  27:8   -> v2                     | Züge 162 | Strength 0.854 | Stand v2 27:7 v1 | Elo 1123/877
  # 35/100:  30:54  -> v1                     | Züge 157 | Strength 1.000 | Stand v2 27:8 v1 | Elo 1097/903
  # 36/100:  14:21  -> v1                     | Züge 169 | Strength 0.546 | Stand v2 27:9 v1 | Elo 1084/916
  # 37/100:  49:33  -> v2                     | Züge 158 | Strength 1.000 | Stand v2 28:9 v1 | Elo 1093/907
  # 38/100:  33:43  -> v1                     | Züge 157 | Strength 0.850 | Stand v2 28:10 v1 | Elo 1073/927
  # 39/100:  43:54  -> v1                     | Züge 162 | Strength 0.880 | Stand v2 28:11 v1 | Elo 1053/947
  # 40/100:  57:40  -> v2                     | Züge 156 | Strength 1.000 | Stand v2 29:11 v1 | Elo 1064/936
  # 41/100:  13:10  -> v2                     | Züge 157 | Strength 0.336 | Stand v2 30:11 v1 | Elo 1067/933
  # 42/100:  13:38  -> v1                     | Züge 164 | Strength 0.978 | Stand v2 30:12 v1 | Elo 1046/954
  # 43/100:  37:12  -> v2                     | Züge 163 | Strength 0.966 | Stand v2 31:12 v1 | Elo 1057/943
  # 44/100:  25:44  -> v1                     | Züge 154 | Strength 1.000 | Stand v2 31:13 v1 | Elo 1036/964
  # 45/100:   2:11  -> v1                     | Züge 160 | Strength 0.494 | Stand v2 31:14 v1 | Elo 1026/974
  # 46/100:  44:34  -> v2                     | Züge 159 | Strength 0.850 | Stand v2 32:14 v1 | Elo 1038/962
  # 47/100:  48:42  -> v2                     | Züge 157 | Strength 0.730 | Stand v2 33:14 v1 | Elo 1047/953
  # 48/100:  18:40  -> v1                     | Züge 157 | Strength 1.000 | Stand v2 33:15 v1 | Elo 1027/973
  # 49/100:  33:13  -> v2                     | Züge 160 | Strength 0.921 | Stand v2 34:15 v1 | Elo 1039/961
  # 50/100:  40:56  -> v1                     | Züge 158 | Strength 1.000 | Stand v2 34:16 v1 | Elo 1019/981
  # 51/100:  52:20  -> v2                     | Züge 164 | Strength 1.000 | Stand v2 35:16 v1 | Elo 1033/967
  # 52/100:  45:21  -> v2                     | Züge 168 | Strength 1.000 | Stand v2 36:16 v1 | Elo 1046/954
  # 53/100:  32:34  -> v1                     | Züge 164 | Strength 0.542 | Stand v2 36:17 v1 | Elo 1035/965
  # 54/100:  28:15  -> v2                     | Züge 151 | Strength 0.805 | Stand v2 37:17 v1 | Elo 1045/955
  # 55/100:  31:0   -> v2                     | Züge 162 | Strength 0.899 | Stand v2 38:17 v1 | Elo 1056/944
  # 56/100:  20:27  -> v1                     | Züge 156 | Strength 0.614 | Stand v2 38:18 v1 | Elo 1043/957
  # 57/100:  22:39  -> v1                     | Züge 154 | Strength 0.989 | Stand v2 38:19 v1 | Elo 1023/977
  # 58/100:  34:18  -> v2                     | Züge 157 | Strength 0.933 | Stand v2 39:19 v1 | Elo 1036/964
  # 59/100:  26:35  -> v1                     | Züge 148 | Strength 0.764 | Stand v2 39:20 v1 | Elo 1021/979
  # 60/100:  21:7   -> v2                     | Züge 150 | Strength 0.756 | Stand v2 40:20 v1 | Elo 1032/968
  # 61/100:  18:33  -> v1                     | Züge 164 | Strength 0.921 | Stand v2 40:21 v1 | Elo 1015/985
  # 62/100:  26:11  -> v2                     | Züge 156 | Strength 0.843 | Stand v2 41:21 v1 | Elo 1027/973
  # 63/100:  64:29  -> v2                     | Züge 171 | Strength 1.000 | Stand v2 42:21 v1 | Elo 1041/959
  # 64/100:   5:19  -> v1                     | Züge 167 | Strength 0.734 | Stand v2 42:22 v1 | Elo 1027/973
  # 65/100:  32:32  -> v1                     | Züge 162 | Strength 0.460 | Stand v2 42:23 v1 | Elo 1019/981
  # 66/100:  18:29  -> v1                     | Züge 159 | Strength 0.756 | Stand v2 42:24 v1 | Elo 1006/994
  # 67/100:  38:16  -> v2                     | Züge 163 | Strength 0.978 | Stand v2 43:24 v1 | Elo 1021/979
  # 68/100:  46:20  -> v2                     | Züge 152 | Strength 1.000 | Stand v2 44:24 v1 | Elo 1035/965
  # 69/100:  20:25  -> v1                     | Züge 158 | Strength 0.531 | Stand v2 44:25 v1 | Elo 1025/975
  # 70/100:  27:17  -> v2                     | Züge 156 | Strength 0.704 | Stand v2 45:25 v1 | Elo 1035/965
  # 71/100:  24:23  -> v2                     | Züge 152 | Strength 0.400 | Stand v2 46:25 v1 | Elo 1040/960
  # 72/100:  31:28  -> v2                     | Züge 154 | Strength 0.539 | Stand v2 47:25 v1 | Elo 1047/953
  # 73/100:  45:19  -> v2                     | Züge 159 | Strength 1.000 | Stand v2 48:25 v1 | Elo 1059/941
  # 74/100:  32:0   -> v2                     | Züge 160 | Strength 0.910 | Stand v2 49:25 v1 | Elo 1069/931
  # 75/100:  43:22  -> v2                     | Züge 160 | Strength 1.000 | Stand v2 50:25 v1 | Elo 1079/921
  # 76/100:  17:0   -> v2                     | Züge 162 | Strength 0.741 | Stand v2 51:25 v1 | Elo 1086/914
  # 77/100:  46:46  -> v1                     | Züge 156 | Strength 0.550 | Stand v2 51:26 v1 | Elo 1073/927
  # 78/100:  21:33  -> v1                     | Züge 167 | Strength 0.831 | Stand v2 51:27 v1 | Elo 1054/946
  # 79/100:  34:39  -> v1                     | Züge 153 | Strength 0.689 | Stand v2 51:28 v1 | Elo 1040/960
  # 80/100:  25:13  -> v2                     | Züge 163 | Strength 0.741 | Stand v2 52:28 v1 | Elo 1049/951
  # 81/100:  55:11  -> v2                     | Züge 162 | Strength 1.000 | Stand v2 53:28 v1 | Elo 1061/939
  # 82/100:  42:22  -> v2                     | Züge 152 | Strength 1.000 | Stand v2 54:28 v1 | Elo 1072/928
  # 83/100:  62:60  -> v2                     | Züge 167 | Strength 0.610 | Stand v2 55:28 v1 | Elo 1078/922
  # 84/100:  27:16  -> v2                     | Züge 160 | Strength 0.734 | Stand v2 56:28 v1 | Elo 1085/915
  # 85/100:  19:39  -> v1                     | Züge 161 | Strength 0.989 | Stand v2 56:29 v1 | Elo 1062/938
  # 86/100:  13:8   -> v2                     | Züge 157 | Strength 0.396 | Stand v2 57:29 v1 | Elo 1066/934
  # 87/100:  27:9   -> v2                     | Züge 162 | Strength 0.854 | Stand v2 58:29 v1 | Elo 1075/925
  # 88/100:   5:23  -> v1                     | Züge 160 | Strength 0.809 | Stand v2 58:30 v1 | Elo 1057/943
  # 89/100:  26:24  -> v2                     | Züge 156 | Strength 0.453 | Stand v2 59:30 v1 | Elo 1062/938
  # 90/100:  27:41  -> v1                     | Züge 166 | Strength 0.970 | Stand v2 59:31 v1 | Elo 1041/959
  # 91/100:  32:0   -> v2                     | Züge 161 | Strength 0.910 | Stand v2 60:31 v1 | Elo 1052/948
  # 92/100:  41:21  -> v2                     | Züge 165 | Strength 1.000 | Stand v2 61:31 v1 | Elo 1063/937
  # 93/100:  10:18  -> v1                     | Züge 164 | Strength 0.542 | Stand v2 61:32 v1 | Elo 1051/949
  # 94/100:  30:7   -> v2                     | Züge 160 | Strength 0.888 | Stand v2 62:32 v1 | Elo 1061/939
  # 95/100:  45:30  -> v2                     | Züge 150 | Strength 1.000 | Stand v2 63:32 v1 | Elo 1072/928
  # 96/100:   3:42  -> v1                     | Züge 155 | Strength 1.000 | Stand v2 63:33 v1 | Elo 1050/950
  # 97/100:  23:51  -> v1                     | Züge 163 | Strength 1.000 | Stand v2 63:34 v1 | Elo 1030/970
  # 98/100:  36:42  -> v1                     | Züge 168 | Strength 0.730 | Stand v2 63:35 v1 | Elo 1016/984
  # 99/100:  29:29  -> v1                     | Züge 156 | Strength 0.426 | Stand v2 63:36 v1 | Elo 1009/991
  #100/100:  29:62  -> v1                     | Züge 161 | Strength 1.000 | Stand v2 63:37 v1 | Elo 992/1008
--------------------------------------------------
🏆 ERGEBNIS: v2 63:37 v1 (63% A-Siege) in 2197.3s (0.0 Spiele/s)
   Ø Score: v2 32.1 | v1 25.8
   0:0-Spiele: 0/100 (0.0%)
   Elo: v2 992 | v1 1008
```

**Arena vs. Heuristik**

```

```
