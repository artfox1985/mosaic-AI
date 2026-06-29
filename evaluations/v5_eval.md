trainiert mit v2+v3+2000 v4, --load v4

256 neuronen pro hidden layer

nicht besser als v4 oder heuristik

**Netzzustand**

```
PS D:\Archiv\Documents\Projekte\mosaic-AI> python train.py --name v5 --epochs 100 --load v4
Lade Daten aus 475 Dateien...
Datensatz geladen: 568763 Züge. (Features pro Zug: 673) — 212.1s
💾 Speichere HDF5-Cache...
✅ Cache gespeichert: D:\Archiv\Documents\Projekte\mosaic-AI\data\.cache_80db6fe4c6fe.h5

🚀 Starte PyTorch Training auf: CUDA
🧠 Netz-Architektur: 673→256→256→256
⚙️  Hyperparameter (config.py):
   Learning Rate : 0.0006
   Value Weight  : 0.5
   Batch Size    : 256
   Value-Target  : ±1 (reines Ergebnis)
📥 Lade altes Model als Startpunkt: alphazero_v4.pth
   Epochen       : 100
🔄 Warm-Start erkannt: Trainiere für 100 Epochen.
Epoche  1/100 | Total Loss:   3.10 (Value:  0.57, Policy:  2.82) | v_pred μ=+0.01 σ=0.855
Epoche  2/100 | Total Loss:   2.95 (Value:  0.44, Policy:  2.73) | v_pred μ=+0.01 σ=0.818
Epoche  3/100 | Total Loss:   2.88 (Value:  0.38, Policy:  2.68) | v_pred μ=+0.01 σ=0.823
Epoche  4/100 | Total Loss:   2.82 (Value:  0.34, Policy:  2.65) | v_pred μ=+0.01 σ=0.834
Epoche  5/100 | Total Loss:   2.78 (Value:  0.31, Policy:  2.62) | v_pred μ=+0.01 σ=0.845
Epoche  6/100 | Total Loss:   2.75 (Value:  0.29, Policy:  2.61) | v_pred μ=+0.01 σ=0.855
Epoche  7/100 | Total Loss:   2.72 (Value:  0.27, Policy:  2.59) | v_pred μ=+0.01 σ=0.864
Epoche  8/100 | Total Loss:   2.70 (Value:  0.26, Policy:  2.57) | v_pred μ=+0.01 σ=0.872
Epoche  9/100 | Total Loss:   2.68 (Value:  0.24, Policy:  2.56) | v_pred μ=+0.01 σ=0.879
Epoche 10/100 | Total Loss:   2.66 (Value:  0.23, Policy:  2.55) | v_pred μ=+0.01 σ=0.885
Epoche 11/100 | Total Loss:   2.65 (Value:  0.22, Policy:  2.54) | v_pred μ=+0.01 σ=0.889
Epoche 12/100 | Total Loss:   2.63 (Value:  0.21, Policy:  2.53) | v_pred μ=+0.01 σ=0.894
Epoche 13/100 | Total Loss:   2.62 (Value:  0.20, Policy:  2.52) | v_pred μ=+0.01 σ=0.898
Epoche 14/100 | Total Loss:   2.61 (Value:  0.20, Policy:  2.51) | v_pred μ=+0.01 σ=0.902
Epoche 15/100 | Total Loss:   2.60 (Value:  0.19, Policy:  2.50) | v_pred μ=+0.01 σ=0.905
Epoche 16/100 | Total Loss:   2.59 (Value:  0.19, Policy:  2.49) | v_pred μ=+0.01 σ=0.907
Epoche 17/100 | Total Loss:   2.58 (Value:  0.18, Policy:  2.49) | v_pred μ=+0.01 σ=0.910
Epoche 18/100 | Total Loss:   2.57 (Value:  0.18, Policy:  2.48) | v_pred μ=+0.01 σ=0.912
Epoche 19/100 | Total Loss:   2.56 (Value:  0.17, Policy:  2.48) | v_pred μ=+0.01 σ=0.915
Epoche 20/100 | Total Loss:   2.55 (Value:  0.17, Policy:  2.47) | v_pred μ=+0.01 σ=0.917
Epoche 21/100 | Total Loss:   2.55 (Value:  0.16, Policy:  2.46) | v_pred μ=+0.01 σ=0.918
Epoche 22/100 | Total Loss:   2.54 (Value:  0.16, Policy:  2.46) | v_pred μ=+0.01 σ=0.920
Epoche 23/100 | Total Loss:   2.54 (Value:  0.16, Policy:  2.46) | v_pred μ=+0.01 σ=0.922
Epoche 24/100 | Total Loss:   2.53 (Value:  0.16, Policy:  2.45) | v_pred μ=+0.01 σ=0.923
Epoche 25/100 | Total Loss:   2.53 (Value:  0.15, Policy:  2.45) | v_pred μ=+0.01 σ=0.925  🔴 PLATEAU + VALUE SINKT (Overfitting-Risiko)
Epoche 26/100 | Total Loss:   2.52 (Value:  0.15, Policy:  2.44) | v_pred μ=+0.01 σ=0.926  🔴 PLATEAU + VALUE SINKT (Overfitting-Risiko)
Epoche 27/100 | Total Loss:   2.51 (Value:  0.15, Policy:  2.44) | v_pred μ=+0.01 σ=0.927  🔴 PLATEAU + VALUE SINKT (Overfitting-Risiko)
Epoche 28/100 | Total Loss:   2.51 (Value:  0.15, Policy:  2.44) | v_pred μ=+0.01 σ=0.928  🔴 PLATEAU + VALUE SINKT (Overfitting-Risiko)
Epoche 29/100 | Total Loss:   2.50 (Value:  0.14, Policy:  2.43) | v_pred μ=+0.01 σ=0.930  🔴 PLATEAU + VALUE SINKT (Overfitting-Risiko)
Epoche 30/100 | Total Loss:   2.50 (Value:  0.14, Policy:  2.43) | v_pred μ=+0.01 σ=0.931  🔴 PLATEAU + VALUE SINKT (Overfitting-Risiko)

⏹️  Early Stopping: Policy plateaut seit Epoche 25 (5 Epochen ohne Fortschritt).

=======================================================
  TRAINING SUMMARY
=======================================================
  Epochen:       100
  Züge:          568,763
  Batches/Epoche:2222
───────────────────────────────────────────────────────
  Policy Loss:   2.4310 / 6.18 max  (39.3%)  🟡 Gut
  Value Loss:    0.1401  🟠 Schwaches Signal
───────────────────────────────────────────────────────
  ⏹️  Early Stopping nach Epoche 30/100
  🟡 Plateau ab Epoche 25.
     → Für nächste Generation: mehr Sims im Self-Play.
=======================================================

=======================================================
  NETZAUSLASTUNG (Hidden Size: 256)
───────────────────────────────────────────────────────
  Schicht          Dead   Aktiv-Rate        Eff.Rank
  ───────────────────────────────────────────────────
  layer1     0/256 (0%)          46%   192/256 (75%)
  layer2     0/256 (0%)          37%   188/256 (73%)
  layer3    11/256 (4%)          20%   175/256 (68%)
  ───────────────────────────────────────────────────
  🟡 Hohe Auslastung (Eff.Rank 72%) — bei Plateau mehr Neuronen erwägen.
=======================================================

✅ Training beendet! Neues Model gespeichert unter:
📂 D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v5.pth
✅ Exportiert: D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v5.onnx  (input=673, hidden=256, value_hidden=128, opset=13)
📎 Referenz für Rust-Parität: D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v5.onnx.ref.txt
```



**Arena vs v4**

```
PS D:\Archiv\Documents\Projekte\mosaic-AI> python arena.py
🏟️ Mosaic-AI ARENA — Netz vs Netz (Rust) 🏟️
  v5 (Brett 0, 200 Sims) vs v4 (Brett 1, 200 Sims) — Stufe 1/DFS-Blatt — 100 Spiele
--------------------------------------------------
  #  1/100:  20:21  -> v4                     | Züge 162 | Strength 0.366 | Stand v5 0:1 v4 | Elo 994/1006
  #  2/100:  36:0   -> v5                     | Züge 163 | Strength 0.955 | Stand v5 1:1 v4 | Elo 1010/990
  #  3/100:  17:33  -> v4                     | Züge 156 | Strength 0.921 | Stand v5 1:2 v4 | Elo 994/1006
  #  4/100:  28:0   -> v5                     | Züge 151 | Strength 0.865 | Stand v5 2:2 v4 | Elo 1008/992
  #  5/100:  16:23  -> v4                     | Züge 156 | Strength 0.569 | Stand v5 2:3 v4 | Elo 998/1002
  #  6/100:   3:0   -> v5                     | Züge 155 | Strength 0.224 | Stand v5 3:3 v4 | Elo 1002/998
  #  7/100:  44:51  -> v4                     | Züge 157 | Strength 0.760 | Stand v5 3:4 v4 | Elo 990/1010
  #  8/100:  29:47  -> v4                     | Züge 162 | Strength 1.000 | Stand v5 3:5 v4 | Elo 975/1025
  #  9/100:   0:7   -> v4                     | Züge 157 | Strength 0.389 | Stand v5 3:6 v4 | Elo 970/1030
  # 10/100:  38:26  -> v5                     | Züge 152 | Strength 0.888 | Stand v5 4:6 v4 | Elo 987/1013
  # 11/100:  29:32  -> v4                     | Züge 153 | Strength 0.550 | Stand v5 4:7 v4 | Elo 979/1021
  # 12/100:  13:26  -> v4                     | Züge 153 | Strength 0.782 | Stand v5 4:8 v4 | Elo 968/1032
  # 13/100:  30:23  -> v5                     | Züge 156 | Strength 0.648 | Stand v5 5:8 v4 | Elo 980/1020
  # 14/100:   0:18  -> v4                     | Züge 153 | Strength 0.753 | Stand v5 5:9 v4 | Elo 969/1031
  # 15/100:  51:26  -> v5                     | Züge 155 | Strength 1.000 | Stand v5 6:9 v4 | Elo 988/1012
  # 16/100:  11:19  -> v4                     | Züge 158 | Strength 0.554 | Stand v5 6:10 v4 | Elo 980/1020
  # 17/100:   9:38  -> v4                     | Züge 153 | Strength 0.978 | Stand v5 6:11 v4 | Elo 966/1034
  # 18/100:  38:51  -> v4                     | Züge 161 | Strength 0.940 | Stand v5 6:12 v4 | Elo 954/1046
  # 19/100:   0:25  -> v4                     | Züge 152 | Strength 0.831 | Stand v5 6:13 v4 | Elo 944/1056
  # 20/100:  22:9   -> v5                     | Züge 158 | Strength 0.738 | Stand v5 7:13 v4 | Elo 959/1041
  # 21/100:  17:36  -> v4                     | Züge 161 | Strength 0.955 | Stand v5 7:14 v4 | Elo 947/1053
  # 22/100:   1:9   -> v4                     | Züge 152 | Strength 0.441 | Stand v5 7:15 v4 | Elo 942/1058
  # 23/100:  26:14  -> v5                     | Züge 155 | Strength 0.753 | Stand v5 8:15 v4 | Elo 958/1042
  # 24/100:  27:6   -> v5                     | Züge 154 | Strength 0.854 | Stand v5 9:15 v4 | Elo 975/1025
  # 25/100:  34:35  -> v4                     | Züge 154 | Strength 0.524 | Stand v5 9:16 v4 | Elo 968/1032
  # 26/100:   0:3   -> v4                     | Züge 156 | Strength 0.224 | Stand v5 9:17 v4 | Elo 965/1035
  # 27/100:   5:28  -> v4                     | Züge 153 | Strength 0.865 | Stand v5 9:18 v4 | Elo 954/1046
  # 28/100:  19:45  -> v4                     | Züge 157 | Strength 1.000 | Stand v5 9:19 v4 | Elo 942/1058
  # 29/100:  24:3   -> v5                     | Züge 157 | Strength 0.820 | Stand v5 10:19 v4 | Elo 959/1041
  # 30/100:  41:8   -> v5                     | Züge 163 | Strength 1.000 | Stand v5 11:19 v4 | Elo 979/1021
  # 31/100:  20:8   -> v5                     | Züge 160 | Strength 0.685 | Stand v5 12:19 v4 | Elo 991/1009
  # 32/100:  19:17  -> v5                     | Züge 154 | Strength 0.374 | Stand v5 13:19 v4 | Elo 997/1003
  # 33/100:   0:27  -> v4                     | Züge 151 | Strength 0.854 | Stand v5 13:20 v4 | Elo 984/1016
  # 34/100:  18:9   -> v5                     | Züge 151 | Strength 0.573 | Stand v5 14:20 v4 | Elo 994/1006
  # 35/100:  33:0   -> v5                     | Züge 154 | Strength 0.921 | Stand v5 15:20 v4 | Elo 1009/991
  # 36/100:  52:30  -> v5                     | Züge 159 | Strength 1.000 | Stand v5 16:20 v4 | Elo 1024/976
  # 37/100:   9:20  -> v4                     | Züge 152 | Strength 0.655 | Stand v5 16:21 v4 | Elo 1012/988
  # 38/100:  58:29  -> v5                     | Züge 162 | Strength 1.000 | Stand v5 17:21 v4 | Elo 1027/973
  # 39/100:  26:17  -> v5                     | Züge 155 | Strength 0.663 | Stand v5 18:21 v4 | Elo 1036/964
  # 40/100:  34:34  -> v4                     | Züge 156 | Strength 0.483 | Stand v5 18:22 v4 | Elo 1027/973
  # 41/100:  33:29  -> v5                     | Züge 166 | Strength 0.591 | Stand v5 19:22 v4 | Elo 1035/965
  # 42/100:  23:20  -> v5                     | Züge 152 | Strength 0.449 | Stand v5 20:22 v4 | Elo 1041/959
  # 43/100:   0:9   -> v4                     | Züge 157 | Strength 0.471 | Stand v5 20:23 v4 | Elo 1032/968
  # 44/100:  59:23  -> v5                     | Züge 157 | Strength 1.000 | Stand v5 21:23 v4 | Elo 1045/955
  # 45/100:  25:41  -> v4                     | Züge 148 | Strength 1.000 | Stand v5 21:24 v4 | Elo 1025/975
  # 46/100:  35:32  -> v5                     | Züge 156 | Strength 0.584 | Stand v5 22:24 v4 | Elo 1033/967
  # 47/100:  13:23  -> v4                     | Züge 160 | Strength 0.659 | Stand v5 22:25 v4 | Elo 1020/980
  # 48/100:  32:21  -> v5                     | Züge 158 | Strength 0.790 | Stand v5 23:25 v4 | Elo 1031/969
  # 49/100:  47:38  -> v5                     | Züge 161 | Strength 0.820 | Stand v5 24:25 v4 | Elo 1042/958
  # 50/100:  25:57  -> v4                     | Züge 148 | Strength 1.000 | Stand v5 24:26 v4 | Elo 1022/978
  # 51/100:  53:37  -> v5                     | Züge 160 | Strength 1.000 | Stand v5 25:26 v4 | Elo 1036/964
  # 52/100:  35:50  -> v4                     | Züge 162 | Strength 1.000 | Stand v5 25:27 v4 | Elo 1017/983
  # 53/100:   3:17  -> v4                     | Züge 157 | Strength 0.711 | Stand v5 25:28 v4 | Elo 1005/995
  # 54/100:  43:68  -> v4                     | Züge 160 | Strength 1.000 | Stand v5 25:29 v4 | Elo 989/1011
  # 55/100:  43:15  -> v5                     | Züge 158 | Strength 1.000 | Stand v5 26:29 v4 | Elo 1006/994
  # 56/100:  17:17  -> v4                     | Züge 159 | Strength 0.291 | Stand v5 26:30 v4 | Elo 1001/999
  # 57/100:  27:18  -> v5                     | Züge 151 | Strength 0.674 | Stand v5 27:30 v4 | Elo 1012/988
  # 58/100:  49:21  -> v5                     | Züge 160 | Strength 1.000 | Stand v5 28:30 v4 | Elo 1027/973
  # 59/100:   0:54  -> v4                     | Züge 157 | Strength 1.000 | Stand v5 28:31 v4 | Elo 1009/991
  # 60/100:  12:26  -> v4                     | Züge 154 | Strength 0.812 | Stand v5 28:32 v4 | Elo 995/1005
  # 61/100:   0:39  -> v4                     | Züge 155 | Strength 0.989 | Stand v5 28:33 v4 | Elo 980/1020
  # 62/100:  37:16  -> v5                     | Züge 162 | Strength 0.966 | Stand v5 29:33 v4 | Elo 997/1003
  # 63/100:  40:40  -> v4                     | Züge 158 | Strength 0.550 | Stand v5 29:34 v4 | Elo 988/1012
  # 64/100:  38:10  -> v5                     | Züge 158 | Strength 0.978 | Stand v5 30:34 v4 | Elo 1005/995
  # 65/100:  18:23  -> v4                     | Züge 158 | Strength 0.509 | Stand v5 30:35 v4 | Elo 997/1003
  # 66/100:   0:9   -> v4                     | Züge 155 | Strength 0.471 | Stand v5 30:36 v4 | Elo 990/1010
  # 67/100:   6:23  -> v4                     | Züge 161 | Strength 0.809 | Stand v5 30:37 v4 | Elo 978/1022
  # 68/100:  20:0   -> v5                     | Züge 159 | Strength 0.775 | Stand v5 31:37 v4 | Elo 992/1008
  # 69/100:  17:40  -> v4                     | Züge 158 | Strength 1.000 | Stand v5 31:38 v4 | Elo 977/1023
  # 70/100:  31:12  -> v5                     | Züge 160 | Strength 0.899 | Stand v5 32:38 v4 | Elo 993/1007
  # 71/100:  54:21  -> v5                     | Züge 162 | Strength 1.000 | Stand v5 33:38 v4 | Elo 1010/990
  # 72/100:   0:0   -> v4                     | Züge 152 | Strength 0.100 | Stand v5 33:39 v4 | Elo 1008/992
  # 73/100:   9:33  -> v4                     | Züge 157 | Strength 0.921 | Stand v5 33:40 v4 | Elo 993/1007
  # 74/100:  10:8   -> v5                     | Züge 155 | Strength 0.273 | Stand v5 34:40 v4 | Elo 998/1002
  # 75/100:  45:24  -> v5                     | Züge 159 | Strength 1.000 | Stand v5 35:40 v4 | Elo 1014/986
  # 76/100:  37:42  -> v4                     | Züge 159 | Strength 0.700 | Stand v5 35:41 v4 | Elo 1002/998
  # 77/100:  23:16  -> v5                     | Züge 155 | Strength 0.569 | Stand v5 36:41 v4 | Elo 1011/989
  # 78/100:   0:39  -> v4                     | Züge 150 | Strength 0.989 | Stand v5 36:42 v4 | Elo 994/1006
  # 79/100:   0:25  -> v4                     | Züge 149 | Strength 0.831 | Stand v5 36:43 v4 | Elo 981/1019
  # 80/100:  20:15  -> v5                     | Züge 158 | Strength 0.475 | Stand v5 37:43 v4 | Elo 989/1011
  # 81/100:  31:11  -> v5                     | Züge 159 | Strength 0.899 | Stand v5 38:43 v4 | Elo 1004/996
  # 82/100:  23:45  -> v4                     | Züge 159 | Strength 1.000 | Stand v5 38:44 v4 | Elo 988/1012
  # 83/100:  38:35  -> v5                     | Züge 161 | Strength 0.617 | Stand v5 39:44 v4 | Elo 999/1001
  # 84/100:  46:37  -> v5                     | Züge 153 | Strength 0.820 | Stand v5 40:44 v4 | Elo 1012/988
  # 85/100:   3:0   -> v5                     | Züge 155 | Strength 0.224 | Stand v5 41:44 v4 | Elo 1015/985
  # 86/100:  36:34  -> v5                     | Züge 151 | Strength 0.565 | Stand v5 42:44 v4 | Elo 1023/977
  # 87/100:   0:2   -> v4                     | Züge 153 | Strength 0.182 | Stand v5 42:45 v4 | Elo 1020/980
  # 88/100:   3:16  -> v4                     | Züge 158 | Strength 0.670 | Stand v5 42:46 v4 | Elo 1008/992
  # 89/100:   7:49  -> v4                     | Züge 165 | Strength 1.000 | Stand v5 42:47 v4 | Elo 991/1009
  # 90/100:  39:48  -> v4                     | Züge 150 | Strength 0.820 | Stand v5 42:48 v4 | Elo 979/1021
  # 91/100:  21:11  -> v5                     | Züge 158 | Strength 0.636 | Stand v5 43:48 v4 | Elo 990/1010
  # 92/100:  21:33  -> v4                     | Züge 154 | Strength 0.831 | Stand v5 43:49 v4 | Elo 977/1023
  # 93/100:  17:16  -> v5                     | Züge 157 | Strength 0.321 | Stand v5 44:49 v4 | Elo 983/1017
  # 94/100:  25:0   -> v5                     | Züge 159 | Strength 0.831 | Stand v5 45:49 v4 | Elo 998/1002
  # 95/100:  18:22  -> v4                     | Züge 158 | Strength 0.468 | Stand v5 45:50 v4 | Elo 991/1009
  # 96/100:  43:16  -> v5                     | Züge 156 | Strength 1.000 | Stand v5 46:50 v4 | Elo 1008/992
  # 97/100:  26:0   -> v5                     | Züge 154 | Strength 0.843 | Stand v5 47:50 v4 | Elo 1021/979
  # 98/100:  10:39  -> v4                     | Züge 156 | Strength 0.989 | Stand v5 47:51 v4 | Elo 1003/997
  # 99/100:  38:29  -> v5                     | Züge 161 | Strength 0.797 | Stand v5 48:51 v4 | Elo 1016/984
  #100/100:   0:12  -> v4                     | Züge 159 | Strength 0.595 | Stand v5 48:52 v4 | Elo 1006/994
--------------------------------------------------
🏆 ERGEBNIS: v5 48:52 v4 (48% A-Siege) in 1706.1s (0.1 Spiele/s)
   Ø Score: v5 23.2 | v4 23.6
   0:0-Spiele: 1/100 (1.0%)
   Elo: v5 1006 | v4 994
```



**Arena vs. Heuristik**

```
PS D:\Archiv\Documents\Projekte\mosaic-AI> python arena.py
🏟️ Mosaic-AI ARENA — Netz vs Heuristik (Rust) 🏟️
  AlphaZero(alphazero_v5.onnx) (Brett 0, 200 Sims, Stufe 1/DFS-Blatt) vs Heuristik(s200) (Brett 1, 200 Sims) — 100 Spiele
--------------------------------------------------
  #  1/100:   6:35  -> Heuristik(s200)          | Züge 151 | Strength 0.944 | Stand Netz 0:1 Heur | Elo 985/1015
  #  2/100:  35:20  -> AlphaZero(alphazero_v5.onnx) | Züge 153 | Strength 0.944 | Stand Netz 1:1 Heur | Elo 1001/999
  #  3/100:  20:30  -> Heuristik(s200)          | Züge 143 | Strength 0.738 | Stand Netz 1:2 Heur | Elo 989/1011
  #  4/100:  21:13  -> AlphaZero(alphazero_v5.onnx) | Züge 160 | Strength 0.576 | Stand Netz 2:2 Heur | Elo 999/1001
  #  5/100:  41:18  -> AlphaZero(alphazero_v5.onnx) | Züge 156 | Strength 1.000 | Stand Netz 3:2 Heur | Elo 1015/985
  #  6/100:   0:31  -> Heuristik(s200)          | Züge 150 | Strength 0.899 | Stand Netz 3:3 Heur | Elo 999/1001
  #  7/100:  30:25  -> AlphaZero(alphazero_v5.onnx) | Züge 153 | Strength 0.588 | Stand Netz 4:3 Heur | Elo 1008/992
  #  8/100:  41:22  -> AlphaZero(alphazero_v5.onnx) | Züge 152 | Strength 1.000 | Stand Netz 5:3 Heur | Elo 1023/977
  #  9/100:  29:40  -> Heuristik(s200)          | Züge 153 | Strength 0.880 | Stand Netz 5:4 Heur | Elo 1007/993
  # 10/100:  44:37  -> AlphaZero(alphazero_v5.onnx) | Züge 152 | Strength 0.760 | Stand Netz 6:4 Heur | Elo 1019/981
  # 11/100:  46:26  -> AlphaZero(alphazero_v5.onnx) | Züge 161 | Strength 1.000 | Stand Netz 7:4 Heur | Elo 1033/967
  # 12/100:   3:0   -> AlphaZero(alphazero_v5.onnx) | Züge 155 | Strength 0.224 | Stand Netz 8:4 Heur | Elo 1036/964
  # 13/100:  60:55  -> AlphaZero(alphazero_v5.onnx) | Züge 162 | Strength 0.700 | Stand Netz 9:4 Heur | Elo 1045/955
  # 14/100:  15:7   -> AlphaZero(alphazero_v5.onnx) | Züge 153 | Strength 0.509 | Stand Netz 10:4 Heur | Elo 1051/949
  # 15/100:   3:48  -> Heuristik(s200)          | Züge 161 | Strength 1.000 | Stand Netz 10:5 Heur | Elo 1030/970
  # 16/100:  34:12  -> AlphaZero(alphazero_v5.onnx) | Züge 150 | Strength 0.933 | Stand Netz 11:5 Heur | Elo 1042/958
  # 17/100:  15:85  -> Heuristik(s200)          | Züge 158 | Strength 1.000 | Stand Netz 11:6 Heur | Elo 1022/978
  # 18/100:  14:0   -> AlphaZero(alphazero_v5.onnx) | Züge 155 | Strength 0.677 | Stand Netz 12:6 Heur | Elo 1031/969
  # 19/100:  43:31  -> AlphaZero(alphazero_v5.onnx) | Züge 156 | Strength 0.910 | Stand Netz 13:6 Heur | Elo 1043/957
  # 20/100:   3:45  -> Heuristik(s200)          | Züge 162 | Strength 1.000 | Stand Netz 13:7 Heur | Elo 1023/977
  # 21/100:  30:8   -> AlphaZero(alphazero_v5.onnx) | Züge 155 | Strength 0.888 | Stand Netz 14:7 Heur | Elo 1035/965
  # 22/100:   5:57  -> Heuristik(s200)          | Züge 153 | Strength 1.000 | Stand Netz 14:8 Heur | Elo 1016/984
  # 23/100:  30:33  -> Heuristik(s200)          | Züge 160 | Strength 0.561 | Stand Netz 14:9 Heur | Elo 1006/994
  # 24/100:  28:53  -> Heuristik(s200)          | Züge 150 | Strength 1.000 | Stand Netz 14:10 Heur | Elo 989/1011
  # 25/100:  52:29  -> AlphaZero(alphazero_v5.onnx) | Züge 158 | Strength 1.000 | Stand Netz 15:10 Heur | Elo 1006/994
  # 26/100:  24:32  -> Heuristik(s200)          | Züge 156 | Strength 0.700 | Stand Netz 15:11 Heur | Elo 994/1006
  # 27/100:  41:17  -> AlphaZero(alphazero_v5.onnx) | Züge 154 | Strength 1.000 | Stand Netz 16:11 Heur | Elo 1011/989
  # 28/100:   0:56  -> Heuristik(s200)          | Züge 161 | Strength 1.000 | Stand Netz 16:12 Heur | Elo 994/1006
  # 29/100:  49:31  -> AlphaZero(alphazero_v5.onnx) | Züge 155 | Strength 1.000 | Stand Netz 17:12 Heur | Elo 1011/989
  # 30/100:  41:57  -> Heuristik(s200)          | Züge 164 | Strength 1.000 | Stand Netz 17:13 Heur | Elo 994/1006
  # 31/100:  35:13  -> AlphaZero(alphazero_v5.onnx) | Züge 154 | Strength 0.944 | Stand Netz 18:13 Heur | Elo 1010/990
  # 32/100:  31:34  -> Heuristik(s200)          | Züge 159 | Strength 0.573 | Stand Netz 18:14 Heur | Elo 1000/1000
  # 33/100:  42:46  -> Heuristik(s200)          | Züge 160 | Strength 0.670 | Stand Netz 18:15 Heur | Elo 989/1011
  # 34/100:   8:3   -> AlphaZero(alphazero_v5.onnx) | Züge 150 | Strength 0.340 | Stand Netz 19:15 Heur | Elo 995/1005
  # 35/100:  30:27  -> AlphaZero(alphazero_v5.onnx) | Züge 160 | Strength 0.528 | Stand Netz 20:15 Heur | Elo 1004/996
  # 36/100:  25:19  -> AlphaZero(alphazero_v5.onnx) | Züge 158 | Strength 0.561 | Stand Netz 21:15 Heur | Elo 1013/987
  # 37/100:  25:17  -> AlphaZero(alphazero_v5.onnx) | Züge 155 | Strength 0.621 | Stand Netz 22:15 Heur | Elo 1022/978
  # 38/100:   0:35  -> Heuristik(s200)          | Züge 152 | Strength 0.944 | Stand Netz 22:16 Heur | Elo 1005/995
  # 39/100:  24:26  -> Heuristik(s200)          | Züge 149 | Strength 0.453 | Stand Netz 22:17 Heur | Elo 998/1002
  # 40/100:   0:6   -> Heuristik(s200)          | Züge 157 | Strength 0.348 | Stand Netz 22:18 Heur | Elo 993/1007
  # 41/100:  31:16  -> AlphaZero(alphazero_v5.onnx) | Züge 151 | Strength 0.899 | Stand Netz 23:18 Heur | Elo 1008/992
  # 42/100:  10:17  -> Heuristik(s200)          | Züge 155 | Strength 0.501 | Stand Netz 23:19 Heur | Elo 1000/1000
  # 43/100:  35:46  -> Heuristik(s200)          | Züge 150 | Strength 0.880 | Stand Netz 23:20 Heur | Elo 986/1014
  # 44/100:   0:51  -> Heuristik(s200)          | Züge 159 | Strength 1.000 | Stand Netz 23:21 Heur | Elo 971/1029
  # 45/100:   0:76  -> Heuristik(s200)          | Züge 155 | Strength 1.000 | Stand Netz 23:22 Heur | Elo 958/1042
  # 46/100:   4:0   -> AlphaZero(alphazero_v5.onnx) | Züge 153 | Strength 0.265 | Stand Netz 24:22 Heur | Elo 963/1037
  # 47/100:  16:19  -> Heuristik(s200)          | Züge 152 | Strength 0.404 | Stand Netz 24:23 Heur | Elo 958/1042
  # 48/100:  17:17  -> Heuristik(s200)          | Züge 154 | Strength 0.291 | Stand Netz 24:24 Heur | Elo 954/1046
  # 49/100:  21:16  -> AlphaZero(alphazero_v5.onnx) | Züge 154 | Strength 0.486 | Stand Netz 25:24 Heur | Elo 964/1036
  # 50/100:   3:22  -> Heuristik(s200)          | Züge 150 | Strength 0.798 | Stand Netz 25:25 Heur | Elo 954/1046
  # 51/100:  19:14  -> AlphaZero(alphazero_v5.onnx) | Züge 155 | Strength 0.464 | Stand Netz 26:25 Heur | Elo 963/1037
  # 52/100:   0:8   -> Heuristik(s200)          | Züge 144 | Strength 0.430 | Stand Netz 26:26 Heur | Elo 958/1042
  # 53/100:  74:44  -> AlphaZero(alphazero_v5.onnx) | Züge 162 | Strength 1.000 | Stand Netz 27:26 Heur | Elo 978/1022
  # 54/100:  50:47  -> AlphaZero(alphazero_v5.onnx) | Züge 159 | Strength 0.640 | Stand Netz 28:26 Heur | Elo 990/1010
  # 55/100:  14:40  -> Heuristik(s200)          | Züge 153 | Strength 1.000 | Stand Netz 28:27 Heur | Elo 975/1025
  # 56/100:  18:0   -> AlphaZero(alphazero_v5.onnx) | Züge 158 | Strength 0.753 | Stand Netz 29:27 Heur | Elo 989/1011
  # 57/100:   3:25  -> Heuristik(s200)          | Züge 161 | Strength 0.831 | Stand Netz 29:28 Heur | Elo 977/1023
  # 58/100:   4:37  -> Heuristik(s200)          | Züge 152 | Strength 0.966 | Stand Netz 29:29 Heur | Elo 964/1036
  # 59/100:  20:41  -> Heuristik(s200)          | Züge 155 | Strength 1.000 | Stand Netz 29:30 Heur | Elo 951/1049
  # 60/100:  24:21  -> AlphaZero(alphazero_v5.onnx) | Züge 156 | Strength 0.460 | Stand Netz 30:30 Heur | Elo 960/1040
  # 61/100:  14:19  -> Heuristik(s200)          | Züge 157 | Strength 0.464 | Stand Netz 30:31 Heur | Elo 954/1046
  # 62/100:   7:34  -> Heuristik(s200)          | Züge 155 | Strength 0.933 | Stand Netz 30:32 Heur | Elo 943/1057
  # 63/100:  12:29  -> Heuristik(s200)          | Züge 153 | Strength 0.876 | Stand Netz 30:33 Heur | Elo 933/1067
  # 64/100:  49:29  -> AlphaZero(alphazero_v5.onnx) | Züge 153 | Strength 1.000 | Stand Netz 31:33 Heur | Elo 955/1045
  # 65/100:  37:33  -> AlphaZero(alphazero_v5.onnx) | Züge 149 | Strength 0.636 | Stand Netz 32:33 Heur | Elo 968/1032
  # 66/100:  59:37  -> AlphaZero(alphazero_v5.onnx) | Züge 157 | Strength 1.000 | Stand Netz 33:33 Heur | Elo 987/1013
  # 67/100:  21:18  -> AlphaZero(alphazero_v5.onnx) | Züge 147 | Strength 0.426 | Stand Netz 34:33 Heur | Elo 994/1006
  # 68/100:  23:3   -> AlphaZero(alphazero_v5.onnx) | Züge 161 | Strength 0.809 | Stand Netz 35:33 Heur | Elo 1007/993
  # 69/100:  10:50  -> Heuristik(s200)          | Züge 158 | Strength 1.000 | Stand Netz 35:34 Heur | Elo 990/1010
  # 70/100:  62:40  -> AlphaZero(alphazero_v5.onnx) | Züge 159 | Strength 1.000 | Stand Netz 36:34 Heur | Elo 1007/993
  # 71/100:   0:5   -> Heuristik(s200)          | Züge 149 | Strength 0.306 | Stand Netz 36:35 Heur | Elo 1002/998
  # 72/100:   5:4   -> AlphaZero(alphazero_v5.onnx) | Züge 162 | Strength 0.186 | Stand Netz 37:35 Heur | Elo 1005/995
  # 73/100:   8:7   -> AlphaZero(alphazero_v5.onnx) | Züge 149 | Strength 0.220 | Stand Netz 38:35 Heur | Elo 1008/992
  # 74/100:  22:69  -> Heuristik(s200)          | Züge 164 | Strength 1.000 | Stand Netz 38:36 Heur | Elo 991/1009
  # 75/100:  10:46  -> Heuristik(s200)          | Züge 157 | Strength 1.000 | Stand Netz 38:37 Heur | Elo 976/1024
  # 76/100:   0:10  -> Heuristik(s200)          | Züge 154 | Strength 0.513 | Stand Netz 38:38 Heur | Elo 969/1031
  # 77/100:  26:25  -> AlphaZero(alphazero_v5.onnx) | Züge 152 | Strength 0.423 | Stand Netz 39:38 Heur | Elo 977/1023
  # 78/100:  34:15  -> AlphaZero(alphazero_v5.onnx) | Züge 153 | Strength 0.933 | Stand Netz 40:38 Heur | Elo 994/1006
  # 79/100:  31:39  -> Heuristik(s200)          | Züge 152 | Strength 0.779 | Stand Netz 40:39 Heur | Elo 982/1018
  # 80/100:  33:20  -> AlphaZero(alphazero_v5.onnx) | Züge 162 | Strength 0.861 | Stand Netz 41:39 Heur | Elo 997/1003
  # 81/100:   1:7   -> Heuristik(s200)          | Züge 157 | Strength 0.359 | Stand Netz 41:40 Heur | Elo 991/1009
  # 82/100:  24:24  -> Heuristik(s200)          | Züge 161 | Strength 0.370 | Stand Netz 41:41 Heur | Elo 985/1015
  # 83/100:  14:23  -> Heuristik(s200)          | Züge 154 | Strength 0.629 | Stand Netz 41:42 Heur | Elo 976/1024
  # 84/100:  55:57  -> Heuristik(s200)          | Züge 163 | Strength 0.610 | Stand Netz 41:43 Heur | Elo 968/1032
  # 85/100:  27:23  -> AlphaZero(alphazero_v5.onnx) | Züge 155 | Strength 0.524 | Stand Netz 42:43 Heur | Elo 978/1022
  # 86/100:  46:30  -> AlphaZero(alphazero_v5.onnx) | Züge 159 | Strength 1.000 | Stand Netz 43:43 Heur | Elo 996/1004
  # 87/100:  26:32  -> Heuristik(s200)          | Züge 157 | Strength 0.640 | Stand Netz 43:44 Heur | Elo 986/1014
  # 88/100:  34:30  -> AlphaZero(alphazero_v5.onnx) | Züge 149 | Strength 0.603 | Stand Netz 44:44 Heur | Elo 996/1004
  # 89/100:  27:32  -> Heuristik(s200)          | Züge 150 | Strength 0.610 | Stand Netz 44:45 Heur | Elo 986/1014
  # 90/100:  16:14  -> AlphaZero(alphazero_v5.onnx) | Züge 148 | Strength 0.340 | Stand Netz 45:45 Heur | Elo 992/1008
  # 91/100:  23:32  -> Heuristik(s200)          | Züge 158 | Strength 0.730 | Stand Netz 45:46 Heur | Elo 981/1019
  # 92/100:  31:45  -> Heuristik(s200)          | Züge 160 | Strength 0.970 | Stand Netz 45:47 Heur | Elo 967/1033
  # 93/100:  30:29  -> AlphaZero(alphazero_v5.onnx) | Züge 159 | Strength 0.468 | Stand Netz 46:47 Heur | Elo 976/1024
  # 94/100:  19:38  -> Heuristik(s200)          | Züge 154 | Strength 0.978 | Stand Netz 46:48 Heur | Elo 963/1037
  # 95/100:  39:30  -> AlphaZero(alphazero_v5.onnx) | Züge 158 | Strength 0.809 | Stand Netz 47:48 Heur | Elo 979/1021
  # 96/100:  11:32  -> Heuristik(s200)          | Züge 157 | Strength 0.910 | Stand Netz 47:49 Heur | Elo 966/1034
  # 97/100:  15:6   -> AlphaZero(alphazero_v5.onnx) | Züge 158 | Strength 0.539 | Stand Netz 48:49 Heur | Elo 976/1024
  # 98/100:  31:36  -> Heuristik(s200)          | Züge 153 | Strength 0.655 | Stand Netz 48:50 Heur | Elo 967/1033
  # 99/100:  41:31  -> AlphaZero(alphazero_v5.onnx) | Züge 157 | Strength 0.850 | Stand Netz 49:50 Heur | Elo 983/1017
  #100/100:  17:20  -> Heuristik(s200)          | Züge 152 | Strength 0.415 | Stand Netz 49:51 Heur | Elo 977/1023
--------------------------------------------------
🏆 ERGEBNIS: AlphaZero(alphazero_v5.onnx) 49:51 Heuristik(s200) (49% Netz-Siege) in 1055.2s (0.1 Spiele/s)
   Ø Score: AlphaZero(alphazero_v5.onnx) 23.8 | Heuristik(s200) 28.4
   0:0-Spiele: 0/100 (0.0%)  (Sauberkeits-Indikator)
   Ø Floor-Strafe: AlphaZero(alphazero_v5.onnx) 22.7 | Heuristik(s200) 21.6
   Elo: AlphaZero(alphazero_v5.onnx) 977 | Heuristik(s200) 1023
```






