trainiert mit v2+v3+4000 v4, --load v6

512 neuronen pro hidden layer

**Netzzustand**

```
PS D:\Archiv\Documents\Projekte\mosaic-AI> python train.py --name v7 --epochs 100 --hidden 512 --load v6
Lade Daten aus 675 Dateien...
Datensatz geladen: 790193 Züge. (Features pro Zug: 673) — 325.1s
💾 Speichere HDF5-Cache...
✅ Cache gespeichert: D:\Archiv\Documents\Projekte\mosaic-AI\data\.cache_9ddd4149640e.h5

🚀 Starte PyTorch Training auf: CUDA
🧠 Netz-Architektur: 673→512→512→512
⚙️  Hyperparameter (config.py):
   Learning Rate : 0.0006
   Value Weight  : 0.5
   Batch Size    : 256
   Value-Target  : ±1 (reines Ergebnis)
📥 Lade altes Model als Startpunkt: alphazero_v6.pth
   Epochen       : 100
🔄 Warm-Start erkannt: Trainiere für 100 Epochen.
Epoche  1/100 | Total Loss:   2.76 (Value:  0.33, Policy:  2.59) | v_pred μ=+0.01 σ=0.873
Epoche  2/100 | Total Loss:   2.61 (Value:  0.22, Policy:  2.50) | v_pred μ=+0.01 σ=0.901
Epoche  3/100 | Total Loss:   2.54 (Value:  0.17, Policy:  2.45) | v_pred μ=+0.01 σ=0.922
Epoche  4/100 | Total Loss:   2.50 (Value:  0.15, Policy:  2.42) | v_pred μ=+0.01 σ=0.933
Epoche  5/100 | Total Loss:   2.46 (Value:  0.13, Policy:  2.40) | v_pred μ=+0.01 σ=0.940
Epoche  6/100 | Total Loss:   2.44 (Value:  0.12, Policy:  2.38) | v_pred μ=+0.01 σ=0.946
Epoche  7/100 | Total Loss:   2.42 (Value:  0.11, Policy:  2.37) | v_pred μ=+0.01 σ=0.949
Epoche  8/100 | Total Loss:   2.41 (Value:  0.10, Policy:  2.36) | v_pred μ=+0.01 σ=0.952
Epoche  9/100 | Total Loss:   2.40 (Value:  0.10, Policy:  2.35) | v_pred μ=+0.01 σ=0.954
Epoche 10/100 | Total Loss:   2.38 (Value:  0.09, Policy:  2.34) | v_pred μ=+0.01 σ=0.956
Epoche 11/100 | Total Loss:   2.37 (Value:  0.09, Policy:  2.33) | v_pred μ=+0.01 σ=0.958
Epoche 12/100 | Total Loss:   2.37 (Value:  0.09, Policy:  2.32) | v_pred μ=+0.01 σ=0.960
Epoche 13/100 | Total Loss:   2.36 (Value:  0.08, Policy:  2.31) | v_pred μ=+0.01 σ=0.962
Epoche 14/100 | Total Loss:   2.35 (Value:  0.08, Policy:  2.31) | v_pred μ=+0.01 σ=0.963
Epoche 15/100 | Total Loss:   2.34 (Value:  0.08, Policy:  2.31) | v_pred μ=+0.01 σ=0.964
Epoche 16/100 | Total Loss:   2.34 (Value:  0.07, Policy:  2.30) | v_pred μ=+0.01 σ=0.965
Epoche 17/100 | Total Loss:   2.33 (Value:  0.07, Policy:  2.30) | v_pred μ=+0.01 σ=0.966
Epoche 18/100 | Total Loss:   2.33 (Value:  0.07, Policy:  2.29) | v_pred μ=+0.01 σ=0.967
Epoche 19/100 | Total Loss:   2.32 (Value:  0.07, Policy:  2.29) | v_pred μ=+0.01 σ=0.968
Epoche 20/100 | Total Loss:   2.32 (Value:  0.07, Policy:  2.28) | v_pred μ=+0.01 σ=0.969
Epoche 21/100 | Total Loss:   2.31 (Value:  0.06, Policy:  2.28) | v_pred μ=+0.01 σ=0.970  🔴 PLATEAU + VALUE SINKT (Overfitting-Risiko)
Epoche 22/100 | Total Loss:   2.31 (Value:  0.06, Policy:  2.28) | v_pred μ=+0.01 σ=0.970  🔴 PLATEAU + VALUE SINKT (Overfitting-Risiko)
Epoche 23/100 | Total Loss:   2.30 (Value:  0.06, Policy:  2.27) | v_pred μ=+0.01 σ=0.971  🔴 PLATEAU + VALUE SINKT (Overfitting-Risiko)
Epoche 24/100 | Total Loss:   2.30 (Value:  0.06, Policy:  2.27) | v_pred μ=+0.01 σ=0.972  🔴 PLATEAU + VALUE SINKT (Overfitting-Risiko)
Epoche 25/100 | Total Loss:   2.30 (Value:  0.06, Policy:  2.27) | v_pred μ=+0.01 σ=0.973  🔴 PLATEAU + VALUE SINKT (Overfitting-Risiko)
Epoche 26/100 | Total Loss:   2.29 (Value:  0.06, Policy:  2.26) | v_pred μ=+0.01 σ=0.974  🔴 PLATEAU + VALUE SINKT (Overfitting-Risiko)

⏹️  Early Stopping: Policy plateaut seit Epoche 21 (5 Epochen ohne Fortschritt).

=======================================================
  TRAINING SUMMARY
=======================================================
  Epochen:       100
  Züge:          790,193
  Batches/Epoche:3087
───────────────────────────────────────────────────────
  Policy Loss:   2.2630 / 6.18 max  (36.6%)  🟡 Gut
  Value Loss:    0.0570  🟡 Gut
───────────────────────────────────────────────────────
  ⏹️  Early Stopping nach Epoche 26/100
  🟡 Plateau ab Epoche 21.
     → Für nächste Generation: mehr Sims im Self-Play.
=======================================================

=======================================================
  NETZAUSLASTUNG (Hidden Size: 512)
───────────────────────────────────────────────────────
  Schicht          Dead   Aktiv-Rate        Eff.Rank
  ───────────────────────────────────────────────────
  layer1     0/512 (0%)          38%   221/512 (43%)
  layer2     0/512 (0%)          30%   217/512 (42%)
  layer3    73/512 (14%)           8%   184/512 (36%)
  ───────────────────────────────────────────────────
  🟢 Gesunde Auslastung (Dead 5%, Rank 40%).
=======================================================

✅ Training beendet! Neues Model gespeichert unter:
📂 D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v7.pth
✅ Exportiert: D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v7.onnx  (input=673, hidden=512, value_hidden=128, opset=13)
📎 Referenz für Rust-Parität: D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v7.onnx.ref.txt
```

**Arena vs v5**

```

```

**Arena vs. heuristik**

```
PS D:\Archiv\Documents\Projekte\mosaic-AI> python arena.py
🏟️ Mosaic-AI ARENA — Netz vs Heuristik (Rust) 🏟️
  v7 (Brett 0, 200 Sims, Stufe 1/DFS-Blatt) vs Heuristik(s200) (Brett 1, 200 Sims) — 100 Spiele
--------------------------------------------------
  #  1/100:  17:2   -> v7                       | Züge 154 | Strength 0.741 | Stand Netz 1:0 Heur | Elo 1012/988
  #  2/100:  64:50  -> v7                       | Züge 152 | Strength 0.970 | Stand Netz 2:0 Heur | Elo 1026/974
  #  3/100:  38:34  -> v7                       | Züge 162 | Strength 0.647 | Stand Netz 3:0 Heur | Elo 1035/965
  #  4/100:  27:58  -> Heuristik(s200)          | Züge 156 | Strength 1.000 | Stand Netz 3:1 Heur | Elo 1016/984
  #  5/100:  19:29  -> Heuristik(s200)          | Züge 155 | Strength 0.726 | Stand Netz 3:2 Heur | Elo 1003/997
  #  6/100:   0:33  -> Heuristik(s200)          | Züge 148 | Strength 0.921 | Stand Netz 3:3 Heur | Elo 988/1012
  #  7/100:  46:43  -> v7                       | Züge 158 | Strength 0.640 | Stand Netz 4:3 Heur | Elo 999/1001
  #  8/100:  37:0   -> v7                       | Züge 158 | Strength 0.966 | Stand Netz 5:3 Heur | Elo 1015/985
  #  9/100:  43:27  -> v7                       | Züge 149 | Strength 1.000 | Stand Netz 6:3 Heur | Elo 1030/970
  # 10/100:  52:45  -> v7                       | Züge 162 | Strength 0.760 | Stand Netz 7:3 Heur | Elo 1040/960
  # 11/100:   0:0   -> Heuristik(s200)          | Züge 161 | Strength 0.100 | Stand Netz 7:4 Heur | Elo 1038/962
  # 12/100:  47:19  -> v7                       | Züge 161 | Strength 1.000 | Stand Netz 8:4 Heur | Elo 1051/949
  # 13/100:  36:11  -> v7                       | Züge 155 | Strength 0.955 | Stand Netz 9:4 Heur | Elo 1062/938
  # 14/100:   8:14  -> Heuristik(s200)          | Züge 153 | Strength 0.438 | Stand Netz 9:5 Heur | Elo 1053/947
  # 15/100:  38:28  -> v7                       | Züge 160 | Strength 0.828 | Stand Netz 10:5 Heur | Elo 1062/938
  # 16/100:  44:9   -> v7                       | Züge 151 | Strength 1.000 | Stand Netz 11:5 Heur | Elo 1073/927
  # 17/100:  25:17  -> v7                       | Züge 149 | Strength 0.621 | Stand Netz 12:5 Heur | Elo 1079/921
  # 18/100:  28:5   -> v7                       | Züge 155 | Strength 0.865 | Stand Netz 13:5 Heur | Elo 1087/913
  # 19/100:  23:16  -> v7                       | Züge 154 | Strength 0.569 | Stand Netz 14:5 Heur | Elo 1092/908
  # 20/100:   3:37  -> Heuristik(s200)          | Züge 154 | Strength 0.966 | Stand Netz 14:6 Heur | Elo 1069/931
  # 21/100:  37:26  -> v7                       | Züge 162 | Strength 0.846 | Stand Netz 15:6 Heur | Elo 1077/923
  # 22/100:  32:23  -> v7                       | Züge 163 | Strength 0.730 | Stand Netz 16:6 Heur | Elo 1084/916
  # 23/100:  22:15  -> v7                       | Züge 153 | Strength 0.558 | Stand Netz 17:6 Heur | Elo 1089/911
  # 24/100:  20:9   -> v7                       | Züge 158 | Strength 0.655 | Stand Netz 18:6 Heur | Elo 1095/905
  # 25/100:  24:26  -> Heuristik(s200)          | Züge 155 | Strength 0.453 | Stand Netz 18:7 Heur | Elo 1084/916
  # 26/100:  28:45  -> Heuristik(s200)          | Züge 158 | Strength 1.000 | Stand Netz 18:8 Heur | Elo 1061/939
  # 27/100:  38:11  -> v7                       | Züge 151 | Strength 0.978 | Stand Netz 19:8 Heur | Elo 1071/929
  # 28/100:  31:25  -> v7                       | Züge 157 | Strength 0.629 | Stand Netz 20:8 Heur | Elo 1077/923
  # 29/100:  26:4   -> v7                       | Züge 151 | Strength 0.843 | Stand Netz 21:8 Heur | Elo 1085/915
  # 30/100:   4:19  -> Heuristik(s200)          | Züge 154 | Strength 0.764 | Stand Netz 21:9 Heur | Elo 1067/933
  # 31/100:  49:53  -> Heuristik(s200)          | Züge 157 | Strength 0.670 | Stand Netz 21:10 Heur | Elo 1052/948
  # 32/100:  33:49  -> Heuristik(s200)          | Züge 157 | Strength 1.000 | Stand Netz 21:11 Heur | Elo 1031/969
  # 33/100:  30:26  -> v7                       | Züge 154 | Strength 0.557 | Stand Netz 22:11 Heur | Elo 1038/962
  # 34/100:  43:32  -> v7                       | Züge 161 | Strength 0.880 | Stand Netz 23:11 Heur | Elo 1049/951
  # 35/100:   0:32  -> Heuristik(s200)          | Züge 157 | Strength 0.910 | Stand Netz 23:12 Heur | Elo 1030/970
  # 36/100:   0:20  -> Heuristik(s200)          | Züge 149 | Strength 0.775 | Stand Netz 23:13 Heur | Elo 1015/985
  # 37/100:  32:10  -> v7                       | Züge 156 | Strength 0.910 | Stand Netz 24:13 Heur | Elo 1028/972
  # 38/100:  34:36  -> Heuristik(s200)          | Züge 156 | Strength 0.565 | Stand Netz 24:14 Heur | Elo 1018/982
  # 39/100:  17:36  -> Heuristik(s200)          | Züge 153 | Strength 0.955 | Stand Netz 24:15 Heur | Elo 1001/999
  # 40/100:   3:36  -> Heuristik(s200)          | Züge 151 | Strength 0.955 | Stand Netz 24:16 Heur | Elo 986/1014
  # 41/100:  12:23  -> Heuristik(s200)          | Züge 145 | Strength 0.689 | Stand Netz 24:17 Heur | Elo 976/1024
  # 42/100:  24:0   -> v7                       | Züge 153 | Strength 0.820 | Stand Netz 25:17 Heur | Elo 991/1009
  # 43/100:  18:21  -> Heuristik(s200)          | Züge 156 | Strength 0.426 | Stand Netz 25:18 Heur | Elo 985/1015
  # 44/100:  24:23  -> v7                       | Züge 149 | Strength 0.400 | Stand Netz 26:18 Heur | Elo 992/1008
  # 45/100:  33:11  -> v7                       | Züge 151 | Strength 0.921 | Stand Netz 27:18 Heur | Elo 1007/993
  # 46/100:   1:60  -> Heuristik(s200)          | Züge 161 | Strength 1.000 | Stand Netz 27:19 Heur | Elo 990/1010
  # 47/100:  34:28  -> v7                       | Züge 157 | Strength 0.663 | Stand Netz 28:19 Heur | Elo 1001/999
  # 48/100:  35:22  -> v7                       | Züge 152 | Strength 0.884 | Stand Netz 29:19 Heur | Elo 1015/985
  # 49/100:  14:62  -> Heuristik(s200)          | Züge 153 | Strength 1.000 | Stand Netz 29:20 Heur | Elo 998/1002
  # 50/100:  55:30  -> v7                       | Züge 154 | Strength 1.000 | Stand Netz 30:20 Heur | Elo 1014/986
  # 51/100:  12:27  -> Heuristik(s200)          | Züge 159 | Strength 0.854 | Stand Netz 30:21 Heur | Elo 999/1001
  # 52/100:  17:47  -> Heuristik(s200)          | Züge 161 | Strength 1.000 | Stand Netz 30:22 Heur | Elo 983/1017
  # 53/100:  20:42  -> Heuristik(s200)          | Züge 154 | Strength 1.000 | Stand Netz 30:23 Heur | Elo 969/1031
  # 54/100:  30:16  -> v7                       | Züge 152 | Strength 0.858 | Stand Netz 31:23 Heur | Elo 985/1015
  # 55/100:  34:25  -> v7                       | Züge 160 | Strength 0.752 | Stand Netz 32:23 Heur | Elo 998/1002
  # 56/100:  34:39  -> Heuristik(s200)          | Züge 153 | Strength 0.689 | Stand Netz 32:24 Heur | Elo 987/1013
  # 57/100:  13:0   -> v7                       | Züge 157 | Strength 0.636 | Stand Netz 33:24 Heur | Elo 998/1002
  # 58/100:  33:11  -> v7                       | Züge 162 | Strength 0.921 | Stand Netz 34:24 Heur | Elo 1013/987
  # 59/100:  34:21  -> v7                       | Züge 158 | Strength 0.873 | Stand Netz 35:24 Heur | Elo 1026/974
  # 60/100:  28:34  -> Heuristik(s200)          | Züge 156 | Strength 0.663 | Stand Netz 35:25 Heur | Elo 1014/986
  # 61/100:  18:74  -> Heuristik(s200)          | Züge 157 | Strength 1.000 | Stand Netz 35:26 Heur | Elo 997/1003
  # 62/100:  41:21  -> v7                       | Züge 152 | Strength 1.000 | Stand Netz 36:26 Heur | Elo 1013/987
  # 63/100:  41:34  -> v7                       | Züge 158 | Strength 0.760 | Stand Netz 37:26 Heur | Elo 1024/976
  # 64/100:  63:33  -> v7                       | Züge 162 | Strength 1.000 | Stand Netz 38:26 Heur | Elo 1038/962
  # 65/100:  14:41  -> Heuristik(s200)          | Züge 153 | Strength 1.000 | Stand Netz 38:27 Heur | Elo 1019/981
  # 66/100:  56:24  -> v7                       | Züge 157 | Strength 1.000 | Stand Netz 39:27 Heur | Elo 1033/967
  # 67/100:  16:7   -> v7                       | Züge 152 | Strength 0.550 | Stand Netz 40:27 Heur | Elo 1040/960
  # 68/100:  34:27  -> v7                       | Züge 151 | Strength 0.693 | Stand Netz 41:27 Heur | Elo 1049/951
  # 69/100:   3:35  -> Heuristik(s200)          | Züge 156 | Strength 0.944 | Stand Netz 41:28 Heur | Elo 1030/970
  # 70/100:  42:23  -> v7                       | Züge 152 | Strength 1.000 | Stand Netz 42:28 Heur | Elo 1043/957
  # 71/100:  25:42  -> Heuristik(s200)          | Züge 158 | Strength 1.000 | Stand Netz 42:29 Heur | Elo 1023/977
  # 72/100:  34:35  -> Heuristik(s200)          | Züge 156 | Strength 0.524 | Stand Netz 42:30 Heur | Elo 1014/986
  # 73/100:  29:37  -> Heuristik(s200)          | Züge 152 | Strength 0.756 | Stand Netz 42:31 Heur | Elo 1001/999
  # 74/100:   0:22  -> Heuristik(s200)          | Züge 155 | Strength 0.798 | Stand Netz 42:32 Heur | Elo 988/1012
  # 75/100:  51:42  -> v7                       | Züge 158 | Strength 0.820 | Stand Netz 43:32 Heur | Elo 1002/998
  # 76/100:  21:0   -> v7                       | Züge 156 | Strength 0.786 | Stand Netz 44:32 Heur | Elo 1014/986
  # 77/100:  24:10  -> v7                       | Züge 155 | Strength 0.790 | Stand Netz 45:32 Heur | Elo 1026/974
  # 78/100:  28:21  -> v7                       | Züge 153 | Strength 0.625 | Stand Netz 46:32 Heur | Elo 1035/965
  # 79/100:  28:10  -> v7                       | Züge 151 | Strength 0.865 | Stand Netz 47:32 Heur | Elo 1046/954
  # 80/100:  10:49  -> Heuristik(s200)          | Züge 162 | Strength 1.000 | Stand Netz 47:33 Heur | Elo 1026/974
  # 81/100:  17:6   -> v7                       | Züge 157 | Strength 0.621 | Stand Netz 48:33 Heur | Elo 1034/966
  # 82/100:  11:5   -> v7                       | Züge 155 | Strength 0.404 | Stand Netz 49:33 Heur | Elo 1039/961
  # 83/100:  31:21  -> v7                       | Züge 156 | Strength 0.749 | Stand Netz 50:33 Heur | Elo 1048/952
  # 84/100:  38:34  -> v7                       | Züge 157 | Strength 0.647 | Stand Netz 51:33 Heur | Elo 1056/944
  # 85/100:  32:42  -> Heuristik(s200)          | Züge 154 | Strength 0.850 | Stand Netz 51:34 Heur | Elo 1038/962
  # 86/100:  33:18  -> v7                       | Züge 155 | Strength 0.921 | Stand Netz 52:34 Heur | Elo 1050/950
  # 87/100:  37:35  -> v7                       | Züge 156 | Strength 0.576 | Stand Netz 53:34 Heur | Elo 1057/943
  # 88/100:  24:27  -> Heuristik(s200)          | Züge 163 | Strength 0.494 | Stand Netz 53:35 Heur | Elo 1047/953
  # 89/100:   0:35  -> Heuristik(s200)          | Züge 151 | Strength 0.944 | Stand Netz 53:36 Heur | Elo 1028/972
  # 90/100:  17:5   -> v7                       | Züge 152 | Strength 0.651 | Stand Netz 54:36 Heur | Elo 1037/963
  # 91/100:  44:29  -> v7                       | Züge 156 | Strength 1.000 | Stand Netz 55:36 Heur | Elo 1050/950
  # 92/100:  22:0   -> v7                       | Züge 153 | Strength 0.798 | Stand Netz 56:36 Heur | Elo 1059/941
  # 93/100:  34:41  -> Heuristik(s200)          | Züge 153 | Strength 0.760 | Stand Netz 56:37 Heur | Elo 1043/957
  # 94/100:  23:17  -> v7                       | Züge 158 | Strength 0.539 | Stand Netz 57:37 Heur | Elo 1050/950
  # 95/100:   7:29  -> Heuristik(s200)          | Züge 148 | Strength 0.876 | Stand Netz 57:38 Heur | Elo 1032/968
  # 96/100:  50:49  -> v7                       | Züge 155 | Strength 0.580 | Stand Netz 58:38 Heur | Elo 1040/960
  # 97/100:  23:4   -> v7                       | Züge 151 | Strength 0.809 | Stand Netz 59:38 Heur | Elo 1050/950
  # 98/100:  28:0   -> v7                       | Züge 158 | Strength 0.865 | Stand Netz 60:38 Heur | Elo 1060/940
  # 99/100:  55:30  -> v7                       | Züge 149 | Strength 1.000 | Stand Netz 61:38 Heur | Elo 1071/929
  #100/100:  24:44  -> Heuristik(s200)          | Züge 156 | Strength 1.000 | Stand Netz 61:39 Heur | Elo 1049/951
--------------------------------------------------
🏆 ERGEBNIS: v7 61:39 Heuristik(s200) (61% Netz-Siege) in 1247.7s (0.1 Spiele/s)
   Ø Score: v7 27.3 | Heuristik(s200) 26.1
   0:0-Spiele: 1/100 (1.0%)  (Sauberkeits-Indikator)
   Ø Floor-Strafe: v7 22.0 | Heuristik(s200) 22.5
   Elo: v7 1049 | Heuristik(s200) 951
```
