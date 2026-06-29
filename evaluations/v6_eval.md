trainiert mit v2+v3+2000 v4, kaltstart

512 neuronen pro hidden layer



**Netzzustand**

```
PS D:\Archiv\Documents\Projekte\mosaic-AI> python train.py --name v6 --epochs 100 --hidden 512
📦 Lade HDF5-Cache (475 Dateien)...
Datensatz geladen: 568763 Züge. (Features pro Zug: 673) — 6.2s

🚀 Starte PyTorch Training auf: CUDA
🧠 Netz-Architektur: 673→512→512→512
⚙️  Hyperparameter (config.py):
   Learning Rate : 0.0006
   Value Weight  : 0.5
   Batch Size    : 256
   Value-Target  : ±1 (reines Ergebnis)
   Epochen       : 100
🆕 Neues Modell: Trainiere für 100 Epochen.
Epoche  1/100 | Total Loss:   3.48 (Value:  0.54, Policy:  3.21) | v_pred μ=+0.01 σ=0.675
Epoche  2/100 | Total Loss:   3.25 (Value:  0.24, Policy:  3.13) | v_pred μ=+0.01 σ=0.872
Epoche  3/100 | Total Loss:   3.16 (Value:  0.17, Policy:  3.08) | v_pred μ=+0.01 σ=0.909
Epoche  4/100 | Total Loss:   3.10 (Value:  0.15, Policy:  3.02) | v_pred μ=+0.01 σ=0.922
Epoche  5/100 | Total Loss:   3.03 (Value:  0.14, Policy:  2.96) | v_pred μ=+0.01 σ=0.929
Epoche  6/100 | Total Loss:   2.95 (Value:  0.13, Policy:  2.88) | v_pred μ=+0.01 σ=0.933
Epoche  7/100 | Total Loss:   2.87 (Value:  0.12, Policy:  2.81) | v_pred μ=+0.01 σ=0.937
Epoche  8/100 | Total Loss:   2.80 (Value:  0.12, Policy:  2.74) | v_pred μ=+0.01 σ=0.939
Epoche  9/100 | Total Loss:   2.74 (Value:  0.11, Policy:  2.68) | v_pred μ=+0.01 σ=0.941
Epoche 10/100 | Total Loss:   2.69 (Value:  0.11, Policy:  2.63) | v_pred μ=+0.01 σ=0.943
Epoche 11/100 | Total Loss:   2.65 (Value:  0.11, Policy:  2.59) | v_pred μ=+0.01 σ=0.945
Epoche 12/100 | Total Loss:   2.61 (Value:  0.11, Policy:  2.56) | v_pred μ=+0.01 σ=0.946
Epoche 13/100 | Total Loss:   2.58 (Value:  0.10, Policy:  2.53) | v_pred μ=+0.01 σ=0.948
Epoche 14/100 | Total Loss:   2.55 (Value:  0.10, Policy:  2.50) | v_pred μ=+0.01 σ=0.949
Epoche 15/100 | Total Loss:   2.53 (Value:  0.10, Policy:  2.48) | v_pred μ=+0.01 σ=0.951
Epoche 16/100 | Total Loss:   2.50 (Value:  0.09, Policy:  2.46) | v_pred μ=+0.01 σ=0.952
Epoche 17/100 | Total Loss:   2.48 (Value:  0.09, Policy:  2.44) | v_pred μ=+0.01 σ=0.953
Epoche 18/100 | Total Loss:   2.47 (Value:  0.09, Policy:  2.42) | v_pred μ=+0.01 σ=0.954
Epoche 19/100 | Total Loss:   2.45 (Value:  0.09, Policy:  2.41) | v_pred μ=+0.01 σ=0.956
Epoche 20/100 | Total Loss:   2.43 (Value:  0.09, Policy:  2.39) | v_pred μ=+0.01 σ=0.957
Epoche 21/100 | Total Loss:   2.42 (Value:  0.08, Policy:  2.38) | v_pred μ=+0.01 σ=0.958
Epoche 22/100 | Total Loss:   2.41 (Value:  0.08, Policy:  2.37) | v_pred μ=+0.01 σ=0.959
Epoche 23/100 | Total Loss:   2.39 (Value:  0.08, Policy:  2.35) | v_pred μ=+0.01 σ=0.960
Epoche 24/100 | Total Loss:   2.38 (Value:  0.08, Policy:  2.34) | v_pred μ=+0.01 σ=0.961
Epoche 25/100 | Total Loss:   2.37 (Value:  0.08, Policy:  2.33) | v_pred μ=+0.01 σ=0.961
Epoche 26/100 | Total Loss:   2.36 (Value:  0.07, Policy:  2.33) | v_pred μ=+0.01 σ=0.963
Epoche 27/100 | Total Loss:   2.35 (Value:  0.07, Policy:  2.32) | v_pred μ=+0.01 σ=0.964
Epoche 28/100 | Total Loss:   2.34 (Value:  0.07, Policy:  2.31) | v_pred μ=+0.01 σ=0.964
Epoche 29/100 | Total Loss:   2.33 (Value:  0.07, Policy:  2.30) | v_pred μ=+0.01 σ=0.965
Epoche 30/100 | Total Loss:   2.33 (Value:  0.07, Policy:  2.29) | v_pred μ=+0.01 σ=0.966
Epoche 31/100 | Total Loss:   2.32 (Value:  0.07, Policy:  2.29) | v_pred μ=+0.01 σ=0.967
Epoche 32/100 | Total Loss:   2.31 (Value:  0.06, Policy:  2.28) | v_pred μ=+0.01 σ=0.968
Epoche 33/100 | Total Loss:   2.31 (Value:  0.06, Policy:  2.27) | v_pred μ=+0.01 σ=0.968
Epoche 34/100 | Total Loss:   2.30 (Value:  0.06, Policy:  2.27) | v_pred μ=+0.01 σ=0.969
Epoche 35/100 | Total Loss:   2.29 (Value:  0.06, Policy:  2.26) | v_pred μ=+0.01 σ=0.970
Epoche 36/100 | Total Loss:   2.29 (Value:  0.06, Policy:  2.26) | v_pred μ=+0.01 σ=0.971
Epoche 37/100 | Total Loss:   2.28 (Value:  0.06, Policy:  2.25) | v_pred μ=+0.01 σ=0.971
Epoche 38/100 | Total Loss:   2.28 (Value:  0.06, Policy:  2.25) | v_pred μ=+0.01 σ=0.972
Epoche 39/100 | Total Loss:   2.27 (Value:  0.05, Policy:  2.24) | v_pred μ=+0.01 σ=0.973
Epoche 40/100 | Total Loss:   2.26 (Value:  0.05, Policy:  2.24) | v_pred μ=+0.01 σ=0.974
Epoche 41/100 | Total Loss:   2.26 (Value:  0.05, Policy:  2.23) | v_pred μ=+0.01 σ=0.974
Epoche 42/100 | Total Loss:   2.26 (Value:  0.05, Policy:  2.23) | v_pred μ=+0.01 σ=0.975
Epoche 43/100 | Total Loss:   2.25 (Value:  0.05, Policy:  2.23) | v_pred μ=+0.01 σ=0.976  🔴 PLATEAU + VALUE SINKT (Overfitting-Risiko)
Epoche 44/100 | Total Loss:   2.25 (Value:  0.05, Policy:  2.22) | v_pred μ=+0.01 σ=0.976  🔴 PLATEAU + VALUE SINKT (Overfitting-Risiko)
Epoche 45/100 | Total Loss:   2.24 (Value:  0.05, Policy:  2.22) | v_pred μ=+0.01 σ=0.977  🔴 PLATEAU + VALUE SINKT (Overfitting-Risiko)
Epoche 46/100 | Total Loss:   2.24 (Value:  0.05, Policy:  2.22) | v_pred μ=+0.01 σ=0.978  🔴 PLATEAU + VALUE SINKT (Overfitting-Risiko)
Epoche 47/100 | Total Loss:   2.23 (Value:  0.04, Policy:  2.21) | v_pred μ=+0.01 σ=0.978  🔴 PLATEAU + VALUE SINKT (Overfitting-Risiko)
Epoche 48/100 | Total Loss:   2.23 (Value:  0.04, Policy:  2.21) | v_pred μ=+0.01 σ=0.979  🔴 PLATEAU + VALUE SINKT (Overfitting-Risiko)

⏹️  Early Stopping: Policy plateaut seit Epoche 43 (5 Epochen ohne Fortschritt).

=======================================================
  TRAINING SUMMARY
=======================================================
  Epochen:       100
  Züge:          568,763
  Batches/Epoche:2222
───────────────────────────────────────────────────────
  Policy Loss:   2.2096 / 6.18 max  (35.8%)  🟡 Gut
  Value Loss:    0.0431  🟢 Sehr gut
───────────────────────────────────────────────────────
  ⏹️  Early Stopping nach Epoche 48/100
  🟡 Plateau ab Epoche 43.
     → Für nächste Generation: mehr Sims im Self-Play.
=======================================================

=======================================================
  NETZAUSLASTUNG (Hidden Size: 512)
───────────────────────────────────────────────────────
  Schicht          Dead   Aktiv-Rate        Eff.Rank
  ───────────────────────────────────────────────────
  layer1     0/512 (0%)          38%   221/512 (43%)
  layer2     0/512 (0%)          32%   216/512 (42%)
  layer3    76/512 (15%)           9%   178/512 (35%)
  ───────────────────────────────────────────────────
  🟢 Gesunde Auslastung (Dead 5%, Rank 40%).
=======================================================

✅ Training beendet! Neues Model gespeichert unter:
📂 D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v6.pth
✅ Exportiert: D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v6.onnx  (input=673, hidden=512, value_hidden=128, opset=13)
📎 Referenz für Rust-Parität: D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v6.onnx.ref.txt
```



**Arena vs v5**

```
PS D:\Archiv\Documents\Projekte\mosaic-AI> python arena.py
🏟️ Mosaic-AI ARENA — Netz vs Netz (Rust) 🏟️
  v6 (Brett 0, 200 Sims) vs v5 (Brett 1, 200 Sims) — Stufe 1/DFS-Blatt — 100 Spiele
--------------------------------------------------
  #  1/100:  12:1   -> v6                     | Züge 158 | Strength 0.565 | Stand v6 1:0 v5 | Elo 1009/991
  #  2/100:   5:11  -> v5                     | Züge 155 | Strength 0.404 | Stand v6 1:1 v5 | Elo 1002/998
  #  3/100:   2:34  -> v5                     | Züge 157 | Strength 0.933 | Stand v6 1:2 v5 | Elo 987/1013
  #  4/100:  24:25  -> v5                     | Züge 156 | Strength 0.411 | Stand v6 1:3 v5 | Elo 981/1019
  #  5/100:  22:26  -> v5                     | Züge 156 | Strength 0.513 | Stand v6 1:4 v5 | Elo 974/1026
  #  6/100:  29:3   -> v6                     | Züge 149 | Strength 0.876 | Stand v6 2:4 v5 | Elo 990/1010
  #  7/100:  40:40  -> v5                     | Züge 160 | Strength 0.550 | Stand v6 2:5 v5 | Elo 982/1018
  #  8/100:  26:30  -> v5                     | Züge 153 | Strength 0.557 | Stand v6 2:6 v5 | Elo 974/1026
  #  9/100:   0:14  -> v5                     | Züge 158 | Strength 0.677 | Stand v6 2:7 v5 | Elo 965/1035
  # 10/100:  10:37  -> v5                     | Züge 159 | Strength 0.966 | Stand v6 2:8 v5 | Elo 953/1047
  # 11/100:   0:37  -> v5                     | Züge 150 | Strength 0.966 | Stand v6 2:9 v5 | Elo 942/1058
  # 12/100:  15:11  -> v6                     | Züge 152 | Strength 0.389 | Stand v6 3:9 v5 | Elo 950/1050
  # 13/100:  36:15  -> v6                     | Züge 149 | Strength 0.955 | Stand v6 4:9 v5 | Elo 970/1030
  # 14/100:  22:31  -> v5                     | Züge 159 | Strength 0.719 | Stand v6 4:10 v5 | Elo 960/1040
  # 15/100:  16:0   -> v6                     | Züge 156 | Strength 0.730 | Stand v6 5:10 v5 | Elo 974/1026
  # 16/100:  25:10  -> v6                     | Züge 151 | Strength 0.831 | Stand v6 6:10 v5 | Elo 989/1011
  # 17/100:   0:28  -> v5                     | Züge 163 | Strength 0.865 | Stand v6 6:11 v5 | Elo 976/1024
  # 18/100:  16:20  -> v5                     | Züge 159 | Strength 0.445 | Stand v6 6:12 v5 | Elo 970/1030
  # 19/100:  12:25  -> v5                     | Züge 151 | Strength 0.771 | Stand v6 6:13 v5 | Elo 960/1040
  # 20/100:   3:48  -> v5                     | Züge 164 | Strength 1.000 | Stand v6 6:14 v5 | Elo 948/1052
  # 21/100:  14:0   -> v6                     | Züge 152 | Strength 0.677 | Stand v6 7:14 v5 | Elo 962/1038
  # 22/100:  32:21  -> v6                     | Züge 157 | Strength 0.790 | Stand v6 8:14 v5 | Elo 977/1023
  # 23/100:  16:29  -> v5                     | Züge 153 | Strength 0.816 | Stand v6 8:15 v5 | Elo 966/1034
  # 24/100:  17:29  -> v5                     | Züge 151 | Strength 0.786 | Stand v6 8:16 v5 | Elo 956/1044
  # 25/100:  18:30  -> v5                     | Züge 159 | Strength 0.798 | Stand v6 8:17 v5 | Elo 946/1054
  # 26/100:  35:16  -> v6                     | Züge 166 | Strength 0.944 | Stand v6 9:17 v5 | Elo 966/1034
  # 27/100:  31:31  -> v5                     | Züge 152 | Strength 0.449 | Stand v6 9:18 v5 | Elo 960/1040
  # 28/100:   2:35  -> v5                     | Züge 155 | Strength 0.944 | Stand v6 9:19 v5 | Elo 948/1052
  # 29/100:   7:0   -> v6                     | Züge 156 | Strength 0.389 | Stand v6 10:19 v5 | Elo 956/1044
  # 30/100:  42:16  -> v6                     | Züge 153 | Strength 1.000 | Stand v6 11:19 v5 | Elo 976/1024
  # 31/100:  45:45  -> v5                     | Züge 153 | Strength 0.550 | Stand v6 11:20 v5 | Elo 968/1032
  # 32/100:  13:45  -> v5                     | Züge 151 | Strength 1.000 | Stand v6 11:21 v5 | Elo 955/1045
  # 33/100:  12:35  -> v5                     | Züge 160 | Strength 0.944 | Stand v6 11:22 v5 | Elo 944/1056
  # 34/100:  36:22  -> v6                     | Züge 158 | Strength 0.925 | Stand v6 12:22 v5 | Elo 963/1037
  # 35/100:  18:0   -> v6                     | Züge 156 | Strength 0.753 | Stand v6 13:22 v5 | Elo 978/1022
  # 36/100:   3:26  -> v5                     | Züge 158 | Strength 0.843 | Stand v6 13:23 v5 | Elo 966/1034
  # 37/100:  11:11  -> v5                     | Züge 148 | Strength 0.224 | Stand v6 13:24 v5 | Elo 963/1037
  # 38/100:  14:0   -> v6                     | Züge 150 | Strength 0.677 | Stand v6 14:24 v5 | Elo 976/1024
  # 39/100:   0:0   -> v5                     | Züge 154 | Strength 0.100 | Stand v6 14:25 v5 | Elo 975/1025
  # 40/100:   6:0   -> v6                     | Züge 149 | Strength 0.348 | Stand v6 15:25 v5 | Elo 981/1019
  # 41/100:  21:16  -> v6                     | Züge 150 | Strength 0.486 | Stand v6 16:25 v5 | Elo 990/1010
  # 42/100:  59:9   -> v6                     | Züge 156 | Strength 1.000 | Stand v6 17:25 v5 | Elo 1007/993
  # 43/100:   0:4   -> v5                     | Züge 153 | Strength 0.265 | Stand v6 17:26 v5 | Elo 1003/997
  # 44/100:   9:28  -> v5                     | Züge 148 | Strength 0.865 | Stand v6 17:27 v5 | Elo 989/1011
  # 45/100:   4:18  -> v5                     | Züge 165 | Strength 0.723 | Stand v6 17:28 v5 | Elo 978/1022
  # 46/100:  11:47  -> v5                     | Züge 152 | Strength 1.000 | Stand v6 17:29 v5 | Elo 964/1036
  # 47/100:  27:30  -> v5                     | Züge 165 | Strength 0.528 | Stand v6 17:30 v5 | Elo 957/1043
  # 48/100:  34:33  -> v6                     | Züge 148 | Strength 0.512 | Stand v6 18:30 v5 | Elo 967/1033
  # 49/100:  30:24  -> v6                     | Züge 157 | Strength 0.618 | Stand v6 19:30 v5 | Elo 979/1021
  # 50/100:  16:5   -> v6                     | Züge 146 | Strength 0.610 | Stand v6 20:30 v5 | Elo 990/1010
  # 51/100:   1:4   -> v5                     | Züge 157 | Strength 0.235 | Stand v6 20:31 v5 | Elo 986/1014
  # 52/100:  10:27  -> v5                     | Züge 146 | Strength 0.854 | Stand v6 20:32 v5 | Elo 973/1027
  # 53/100:  45:71  -> v5                     | Züge 165 | Strength 1.000 | Stand v6 20:33 v5 | Elo 959/1041
  # 54/100:  19:12  -> v6                     | Züge 155 | Strength 0.524 | Stand v6 21:33 v5 | Elo 969/1031
  # 55/100:  17:45  -> v5                     | Züge 158 | Strength 1.000 | Stand v6 21:34 v5 | Elo 956/1044
  # 56/100:   0:17  -> v5                     | Züge 159 | Strength 0.741 | Stand v6 21:35 v5 | Elo 947/1053
  # 57/100:  27:6   -> v6                     | Züge 142 | Strength 0.854 | Stand v6 22:35 v5 | Elo 965/1035
  # 58/100:  36:28  -> v6                     | Züge 158 | Strength 0.745 | Stand v6 23:35 v5 | Elo 979/1021
  # 59/100:   7:25  -> v5                     | Züge 156 | Strength 0.831 | Stand v6 23:36 v5 | Elo 967/1033
  # 60/100:  23:18  -> v6                     | Züge 152 | Strength 0.509 | Stand v6 24:36 v5 | Elo 977/1023
  # 61/100:  45:13  -> v6                     | Züge 156 | Strength 1.000 | Stand v6 25:36 v5 | Elo 995/1005
  # 62/100:  23:24  -> v5                     | Züge 152 | Strength 0.400 | Stand v6 25:37 v5 | Elo 989/1011
  # 63/100:  19:20  -> v5                     | Züge 150 | Strength 0.355 | Stand v6 25:38 v5 | Elo 984/1016
  # 64/100:   5:27  -> v5                     | Züge 163 | Strength 0.854 | Stand v6 25:39 v5 | Elo 972/1028
  # 65/100:  51:21  -> v6                     | Züge 158 | Strength 1.000 | Stand v6 26:39 v5 | Elo 991/1009
  # 66/100:  25:2   -> v6                     | Züge 159 | Strength 0.831 | Stand v6 27:39 v5 | Elo 1005/995
  # 67/100:  49:31  -> v6                     | Züge 163 | Strength 1.000 | Stand v6 28:39 v5 | Elo 1021/979
  # 68/100:  22:16  -> v6                     | Züge 154 | Strength 0.528 | Stand v6 29:39 v5 | Elo 1028/972
  # 69/100:  11:0   -> v6                     | Züge 155 | Strength 0.554 | Stand v6 30:39 v5 | Elo 1035/965
  # 70/100:  37:33  -> v6                     | Züge 159 | Strength 0.636 | Stand v6 31:39 v5 | Elo 1043/957
  # 71/100:  18:48  -> v5                     | Züge 158 | Strength 1.000 | Stand v6 31:40 v5 | Elo 1023/977
  # 72/100:  27:39  -> v5                     | Züge 147 | Strength 0.899 | Stand v6 31:41 v5 | Elo 1007/993
  # 73/100:  30:26  -> v6                     | Züge 162 | Strength 0.557 | Stand v6 32:41 v5 | Elo 1016/984
  # 74/100:   0:23  -> v5                     | Züge 153 | Strength 0.809 | Stand v6 32:42 v5 | Elo 1002/998
  # 75/100:   6:23  -> v5                     | Züge 159 | Strength 0.809 | Stand v6 32:43 v5 | Elo 989/1011
  # 76/100:  20:27  -> v5                     | Züge 154 | Strength 0.614 | Stand v6 32:44 v5 | Elo 980/1020
  # 77/100:  11:39  -> v5                     | Züge 156 | Strength 0.989 | Stand v6 32:45 v5 | Elo 966/1034
  # 78/100:  55:25  -> v6                     | Züge 148 | Strength 1.000 | Stand v6 33:45 v5 | Elo 985/1015
  # 79/100:  29:37  -> v5                     | Züge 163 | Strength 0.756 | Stand v6 33:46 v5 | Elo 974/1026
  # 80/100:  13:14  -> v5                     | Züge 147 | Strength 0.287 | Stand v6 33:47 v5 | Elo 970/1030
  # 81/100:  34:20  -> v6                     | Züge 160 | Strength 0.903 | Stand v6 34:47 v5 | Elo 987/1013
  # 82/100:   5:25  -> v5                     | Züge 153 | Strength 0.831 | Stand v6 34:48 v5 | Elo 975/1025
  # 83/100:  33:45  -> v5                     | Züge 163 | Strength 0.910 | Stand v6 34:49 v5 | Elo 963/1037
  # 84/100:  35:0   -> v6                     | Züge 160 | Strength 0.944 | Stand v6 35:49 v5 | Elo 981/1019
  # 85/100:  36:13  -> v6                     | Züge 162 | Strength 0.955 | Stand v6 36:49 v5 | Elo 998/1002
  # 86/100:  32:72  -> v5                     | Züge 162 | Strength 1.000 | Stand v6 36:50 v5 | Elo 982/1018
  # 87/100:  35:8   -> v6                     | Züge 149 | Strength 0.944 | Stand v6 37:50 v5 | Elo 999/1001
  # 88/100:  41:40  -> v6                     | Züge 159 | Strength 0.580 | Stand v6 38:50 v5 | Elo 1008/992
  # 89/100:   0:17  -> v5                     | Züge 151 | Strength 0.741 | Stand v6 38:51 v5 | Elo 996/1004
  # 90/100:  46:40  -> v6                     | Züge 164 | Strength 0.730 | Stand v6 39:51 v5 | Elo 1008/992
  # 91/100:   6:36  -> v5                     | Züge 146 | Strength 0.955 | Stand v6 39:52 v5 | Elo 992/1008
  # 92/100:  26:4   -> v6                     | Züge 155 | Strength 0.843 | Stand v6 40:52 v5 | Elo 1006/994
  # 93/100:  19:23  -> v5                     | Züge 158 | Strength 0.479 | Stand v6 40:53 v5 | Elo 998/1002
  # 94/100:   0:35  -> v5                     | Züge 142 | Strength 0.944 | Stand v6 40:54 v5 | Elo 983/1017
  # 95/100:  26:18  -> v6                     | Züge 151 | Strength 0.633 | Stand v6 41:54 v5 | Elo 994/1006
  # 96/100:  28:23  -> v6                     | Züge 157 | Strength 0.565 | Stand v6 42:54 v5 | Elo 1003/997
  # 97/100:   6:15  -> v5                     | Züge 156 | Strength 0.539 | Stand v6 42:55 v5 | Elo 994/1006
  # 98/100:  24:0   -> v6                     | Züge 159 | Strength 0.820 | Stand v6 43:55 v5 | Elo 1008/992
  # 99/100:  10:12  -> v5                     | Züge 156 | Strength 0.295 | Stand v6 43:56 v5 | Elo 1003/997
  #100/100:  10:16  -> v5                     | Züge 147 | Strength 0.460 | Stand v6 43:57 v5 | Elo 996/1004
--------------------------------------------------
🏆 ERGEBNIS: v6 43:57 v5 (43% A-Siege) in 1842.2s (0.1 Spiele/s)
   Ø Score: v6 20.3 | v5 22.5
   0:0-Spiele: 1/100 (1.0%)
   Elo: v6 996 | v5 1004
```



**Arena vs. heuristik**

```
PS D:\Archiv\Documents\Projekte\mosaic-AI> python arena.py
🏟️ Mosaic-AI ARENA — Netz vs Heuristik (Rust) 🏟️
  v6 (Brett 0, 200 Sims, Stufe 1/DFS-Blatt) vs Heuristik(s200) (Brett 1, 200 Sims) — 100 Spiele
--------------------------------------------------
  #  1/100:  12:13  -> Heuristik(s200)          | Züge 157 | Strength 0.276 | Stand Netz 0:1 Heur | Elo 996/1004
  #  2/100:   0:32  -> Heuristik(s200)          | Züge 156 | Strength 0.910 | Stand Netz 0:2 Heur | Elo 982/1018
  #  3/100:  20:21  -> Heuristik(s200)          | Züge 165 | Strength 0.366 | Stand Netz 0:3 Heur | Elo 977/1023
  #  4/100:   0:15  -> Heuristik(s200)          | Züge 151 | Strength 0.719 | Stand Netz 0:4 Heur | Elo 967/1033
  #  5/100:  22:30  -> Heuristik(s200)          | Züge 160 | Strength 0.677 | Stand Netz 0:5 Heur | Elo 958/1042
  #  6/100:  32:12  -> v6                       | Züge 163 | Strength 0.910 | Stand Netz 1:5 Heur | Elo 976/1024
  #  7/100:   7:42  -> Heuristik(s200)          | Züge 148 | Strength 1.000 | Stand Netz 1:6 Heur | Elo 962/1038
  #  8/100:  23:23  -> Heuristik(s200)          | Züge 150 | Strength 0.359 | Stand Netz 1:7 Heur | Elo 957/1043
  #  9/100:  13:0   -> v6                       | Züge 157 | Strength 0.636 | Stand Netz 2:7 Heur | Elo 970/1030
  # 10/100:  40:27  -> v6                       | Züge 156 | Strength 0.940 | Stand Netz 3:7 Heur | Elo 988/1012
  # 11/100:  45:35  -> v6                       | Züge 159 | Strength 0.850 | Stand Netz 4:7 Heur | Elo 1003/997
  # 12/100:   0:30  -> Heuristik(s200)          | Züge 156 | Strength 0.888 | Stand Netz 4:8 Heur | Elo 989/1011
  # 13/100:  12:53  -> Heuristik(s200)          | Züge 153 | Strength 1.000 | Stand Netz 4:9 Heur | Elo 974/1026
  # 14/100:  33:53  -> Heuristik(s200)          | Züge 153 | Strength 1.000 | Stand Netz 4:10 Heur | Elo 960/1040
  # 15/100:   8:0   -> v6                       | Züge 155 | Strength 0.430 | Stand Netz 5:10 Heur | Elo 968/1032
  # 16/100:  41:13  -> v6                       | Züge 157 | Strength 1.000 | Stand Netz 6:10 Heur | Elo 987/1013
  # 17/100:  57:46  -> v6                       | Züge 157 | Strength 0.880 | Stand Netz 7:10 Heur | Elo 1002/998
  # 18/100:   0:36  -> Heuristik(s200)          | Züge 165 | Strength 0.955 | Stand Netz 7:11 Heur | Elo 987/1013
  # 19/100:  38:5   -> v6                       | Züge 153 | Strength 0.978 | Stand Netz 8:11 Heur | Elo 1004/996
  # 20/100:  35:13  -> v6                       | Züge 154 | Strength 0.944 | Stand Netz 9:11 Heur | Elo 1019/981
  # 21/100:  41:38  -> v6                       | Züge 154 | Strength 0.640 | Stand Netz 10:11 Heur | Elo 1028/972
  # 22/100:  29:13  -> v6                       | Züge 153 | Strength 0.876 | Stand Netz 11:11 Heur | Elo 1040/960
  # 23/100:  10:5   -> v6                       | Züge 149 | Strength 0.362 | Stand Netz 12:11 Heur | Elo 1044/956
  # 24/100:   0:32  -> Heuristik(s200)          | Züge 167 | Strength 0.910 | Stand Netz 12:12 Heur | Elo 1026/974
  # 25/100:   0:52  -> Heuristik(s200)          | Züge 159 | Strength 1.000 | Stand Netz 12:13 Heur | Elo 1008/992
  # 26/100:  52:16  -> v6                       | Züge 165 | Strength 1.000 | Stand Netz 13:13 Heur | Elo 1023/977
  # 27/100:  45:5   -> v6                       | Züge 160 | Strength 1.000 | Stand Netz 14:13 Heur | Elo 1037/963
  # 28/100:   0:12  -> Heuristik(s200)          | Züge 160 | Strength 0.595 | Stand Netz 14:14 Heur | Elo 1025/975
  # 29/100:  30:48  -> Heuristik(s200)          | Züge 160 | Strength 1.000 | Stand Netz 14:15 Heur | Elo 1007/993
  # 30/100:  38:9   -> v6                       | Züge 160 | Strength 0.978 | Stand Netz 15:15 Heur | Elo 1022/978
  # 31/100:   9:62  -> Heuristik(s200)          | Züge 156 | Strength 1.000 | Stand Netz 15:16 Heur | Elo 1004/996
  # 32/100:  28:17  -> v6                       | Züge 154 | Strength 0.745 | Stand Netz 16:16 Heur | Elo 1016/984
  # 33/100:  40:33  -> v6                       | Züge 164 | Strength 0.760 | Stand Netz 17:16 Heur | Elo 1027/973
  # 34/100:  51:35  -> v6                       | Züge 155 | Strength 1.000 | Stand Netz 18:16 Heur | Elo 1041/959
  # 35/100:  24:11  -> v6                       | Züge 104 | Strength 0.760 | Stand Netz 19:16 Heur | Elo 1050/950
  # 36/100:   0:36  -> Heuristik(s200)          | Züge 156 | Strength 0.955 | Stand Netz 19:17 Heur | Elo 1030/970
  # 37/100:  31:20  -> v6                       | Züge 158 | Strength 0.779 | Stand Netz 20:17 Heur | Elo 1040/960
  # 38/100:  37:5   -> v6                       | Züge 151 | Strength 0.966 | Stand Netz 21:17 Heur | Elo 1052/948
  # 39/100:  16:24  -> Heuristik(s200)          | Züge 158 | Strength 0.610 | Stand Netz 21:18 Heur | Elo 1039/961
  # 40/100:  19:21  -> Heuristik(s200)          | Züge 156 | Strength 0.396 | Stand Netz 21:19 Heur | Elo 1031/969
  # 41/100:   3:53  -> Heuristik(s200)          | Züge 152 | Strength 1.000 | Stand Netz 21:20 Heur | Elo 1012/988
  # 42/100:  13:46  -> Heuristik(s200)          | Züge 157 | Strength 1.000 | Stand Netz 21:21 Heur | Elo 995/1005
  # 43/100:  32:29  -> v6                       | Züge 158 | Strength 0.550 | Stand Netz 22:21 Heur | Elo 1004/996
  # 44/100:  35:19  -> v6                       | Züge 154 | Strength 0.944 | Stand Netz 23:21 Heur | Elo 1019/981
  # 45/100:  20:22  -> Heuristik(s200)          | Züge 154 | Strength 0.408 | Stand Netz 23:22 Heur | Elo 1012/988
  # 46/100:  13:51  -> Heuristik(s200)          | Züge 162 | Strength 1.000 | Stand Netz 23:23 Heur | Elo 995/1005
  # 47/100:  12:37  -> Heuristik(s200)          | Züge 153 | Strength 0.966 | Stand Netz 23:24 Heur | Elo 980/1020
  # 48/100:  11:18  -> Heuristik(s200)          | Züge 152 | Strength 0.513 | Stand Netz 23:25 Heur | Elo 973/1027
  # 49/100:   0:13  -> Heuristik(s200)          | Züge 149 | Strength 0.636 | Stand Netz 23:26 Heur | Elo 964/1036
  # 50/100:  11:29  -> Heuristik(s200)          | Züge 153 | Strength 0.876 | Stand Netz 23:27 Heur | Elo 953/1047
  # 51/100:   0:35  -> Heuristik(s200)          | Züge 150 | Strength 0.944 | Stand Netz 23:28 Heur | Elo 942/1058
  # 52/100:   8:31  -> Heuristik(s200)          | Züge 158 | Strength 0.899 | Stand Netz 23:29 Heur | Elo 932/1068
  # 53/100:   0:34  -> Heuristik(s200)          | Züge 151 | Strength 0.933 | Stand Netz 23:30 Heur | Elo 923/1077
  # 54/100:  33:26  -> v6                       | Züge 159 | Strength 0.681 | Stand Netz 24:30 Heur | Elo 938/1062
  # 55/100:  24:12  -> v6                       | Züge 148 | Strength 0.730 | Stand Netz 25:30 Heur | Elo 954/1046
  # 56/100:   5:0   -> v6                       | Züge 152 | Strength 0.306 | Stand Netz 26:30 Heur | Elo 960/1040
  # 57/100:  57:50  -> v6                       | Züge 152 | Strength 0.760 | Stand Netz 27:30 Heur | Elo 975/1025
  # 58/100:   3:43  -> Heuristik(s200)          | Züge 153 | Strength 1.000 | Stand Netz 27:31 Heur | Elo 961/1039
  # 59/100:   0:42  -> Heuristik(s200)          | Züge 160 | Strength 1.000 | Stand Netz 27:32 Heur | Elo 949/1051
  # 60/100:  21:50  -> Heuristik(s200)          | Züge 153 | Strength 1.000 | Stand Netz 27:33 Heur | Elo 938/1062
  # 61/100:   0:28  -> Heuristik(s200)          | Züge 151 | Strength 0.865 | Stand Netz 27:34 Heur | Elo 929/1071
  # 62/100:  41:40  -> v6                       | Züge 153 | Strength 0.580 | Stand Netz 28:34 Heur | Elo 942/1058
  # 63/100:   3:27  -> Heuristik(s200)          | Züge 156 | Strength 0.854 | Stand Netz 28:35 Heur | Elo 933/1067
  # 64/100:  17:57  -> Heuristik(s200)          | Züge 162 | Strength 1.000 | Stand Netz 28:36 Heur | Elo 923/1077
  # 65/100:  41:18  -> v6                       | Züge 157 | Strength 1.000 | Stand Netz 29:36 Heur | Elo 946/1054
  # 66/100:   0:34  -> Heuristik(s200)          | Züge 159 | Strength 0.933 | Stand Netz 29:37 Heur | Elo 936/1064
  # 67/100:   4:31  -> Heuristik(s200)          | Züge 151 | Strength 0.899 | Stand Netz 29:38 Heur | Elo 927/1073
  # 68/100:  24:11  -> v6                       | Züge 159 | Strength 0.760 | Stand Netz 30:38 Heur | Elo 944/1056
  # 69/100:  32:30  -> v6                       | Züge 152 | Strength 0.520 | Stand Netz 31:38 Heur | Elo 955/1045
  # 70/100:   0:27  -> Heuristik(s200)          | Züge 150 | Strength 0.854 | Stand Netz 31:39 Heur | Elo 945/1055
  # 71/100:   8:0   -> v6                       | Züge 158 | Strength 0.430 | Stand Netz 32:39 Heur | Elo 954/1046
  # 72/100:  29:38  -> Heuristik(s200)          | Züge 160 | Strength 0.797 | Stand Netz 32:40 Heur | Elo 945/1055
  # 73/100:  43:26  -> v6                       | Züge 158 | Strength 1.000 | Stand Netz 33:40 Heur | Elo 966/1034
  # 74/100:  11:31  -> Heuristik(s200)          | Züge 159 | Strength 0.899 | Stand Netz 33:41 Heur | Elo 954/1046
  # 75/100:   8:23  -> Heuristik(s200)          | Züge 158 | Strength 0.809 | Stand Netz 33:42 Heur | Elo 944/1056
  # 76/100:  50:3   -> v6                       | Züge 155 | Strength 1.000 | Stand Netz 34:42 Heur | Elo 965/1035
  # 77/100:  37:9   -> v6                       | Züge 157 | Strength 0.966 | Stand Netz 35:42 Heur | Elo 984/1016
  # 78/100:   2:18  -> Heuristik(s200)          | Züge 155 | Strength 0.753 | Stand Netz 35:43 Heur | Elo 973/1027
  # 79/100:  29:41  -> Heuristik(s200)          | Züge 155 | Strength 0.910 | Stand Netz 35:44 Heur | Elo 961/1039
  # 80/100:  12:12  -> Heuristik(s200)          | Züge 152 | Strength 0.235 | Stand Netz 35:45 Heur | Elo 958/1042
  # 81/100:  21:66  -> Heuristik(s200)          | Züge 151 | Strength 1.000 | Stand Netz 35:46 Heur | Elo 946/1054
  # 82/100:  30:6   -> v6                       | Züge 156 | Strength 0.888 | Stand Netz 36:46 Heur | Elo 964/1036
  # 83/100:  41:55  -> Heuristik(s200)          | Züge 156 | Strength 0.970 | Stand Netz 36:47 Heur | Elo 952/1048
  # 84/100:   8:45  -> Heuristik(s200)          | Züge 158 | Strength 1.000 | Stand Netz 36:48 Heur | Elo 940/1060
  # 85/100:  39:11  -> v6                       | Züge 149 | Strength 0.989 | Stand Netz 37:48 Heur | Elo 961/1039
  # 86/100:   2:0   -> v6                       | Züge 154 | Strength 0.182 | Stand Netz 38:48 Heur | Elo 965/1035
  # 87/100:  26:15  -> v6                       | Züge 157 | Strength 0.722 | Stand Netz 39:48 Heur | Elo 979/1021
  # 88/100:   9:30  -> Heuristik(s200)          | Züge 153 | Strength 0.888 | Stand Netz 39:49 Heur | Elo 967/1033
  # 89/100:  21:14  -> v6                       | Züge 153 | Strength 0.546 | Stand Netz 40:49 Heur | Elo 977/1023
  # 90/100:  60:40  -> v6                       | Züge 161 | Strength 1.000 | Stand Netz 41:49 Heur | Elo 995/1005
  # 91/100:  17:64  -> Heuristik(s200)          | Züge 158 | Strength 1.000 | Stand Netz 41:50 Heur | Elo 979/1021
  # 92/100:  24:15  -> v6                       | Züge 152 | Strength 0.640 | Stand Netz 42:50 Heur | Elo 990/1010
  # 93/100:  47:28  -> v6                       | Züge 161 | Strength 1.000 | Stand Netz 43:50 Heur | Elo 1007/993
  # 94/100:  25:32  -> Heuristik(s200)          | Züge 152 | Strength 0.670 | Stand Netz 43:51 Heur | Elo 996/1004
  # 95/100:  10:24  -> Heuristik(s200)          | Züge 159 | Strength 0.790 | Stand Netz 43:52 Heur | Elo 984/1016
  # 96/100:  38:38  -> Heuristik(s200)          | Züge 154 | Strength 0.527 | Stand Netz 43:53 Heur | Elo 976/1024
  # 97/100:  42:24  -> v6                       | Züge 154 | Strength 1.000 | Stand Netz 44:53 Heur | Elo 994/1006
  # 98/100:  63:25  -> v6                       | Züge 165 | Strength 1.000 | Stand Netz 45:53 Heur | Elo 1011/989
  # 99/100:   0:50  -> Heuristik(s200)          | Züge 154 | Strength 1.000 | Stand Netz 45:54 Heur | Elo 994/1006
  #100/100:  12:23  -> Heuristik(s200)          | Züge 154 | Strength 0.689 | Stand Netz 45:55 Heur | Elo 983/1017
--------------------------------------------------
🏆 ERGEBNIS: v6 45:55 Heuristik(s200) (45% Netz-Siege) in 1289.1s (0.1 Spiele/s)
   Ø Score: v6 21.6 | Heuristik(s200) 27.4
   0:0-Spiele: 0/100 (0.0%)  (Sauberkeits-Indikator)
   Ø Floor-Strafe: v6 23.3 | Heuristik(s200) 21.8
   Elo: v6 983 | Heuristik(s200) 1017
```
