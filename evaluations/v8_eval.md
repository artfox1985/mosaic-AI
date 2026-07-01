trainiert mit v2+v3+4000 v4, --load v7

feature count unterschiedlich zu v7, moon order implementiert sowie bonuschip farben.

512 neuronen pro hidden layer

**Netzzustand**

```
PS D:\Archiv\Documents\Projekte\mosaic-AI> python train.py --name v8 --epochs 100 --hidden 512 --load v7
Lade Daten aus 675 Dateien...
Datensatz geladen: 790193 Züge. (Features pro Zug: 684) — 321.9s
💾 Speichere HDF5-Cache...
✅ Cache gespeichert: D:\Archiv\Documents\Projekte\mosaic-AI\data\.cache_41c776bf339f.h5

🚀 Starte PyTorch Training auf: CUDA
🧠 Netz-Architektur: 684→512→512→512
⚙️  Hyperparameter (config.py):
   Learning Rate : 0.0006
   Value Weight  : 0.5
   Batch Size    : 256
   Value-Target  : ±1 (reines Ergebnis)
📥 Lade altes Model als Startpunkt: alphazero_v7.pth
   ⚠️  Shape-Mismatch, startet frisch: body.0.weight
   Epochen       : 100
🔄 Warm-Start erkannt: Trainiere für 100 Epochen.
Epoche  1/100 | Total Loss:   3.41 (Value:  0.69, Policy:  3.06) | v_pred μ=+0.00 σ=0.631
Epoche  2/100 | Total Loss:   3.17 (Value:  0.29, Policy:  3.02) | v_pred μ=+0.01 σ=0.841
Epoche  3/100 | Total Loss:   3.10 (Value:  0.20, Policy:  3.01) | v_pred μ=+0.01 σ=0.895
Epoche  4/100 | Total Loss:   3.07 (Value:  0.17, Policy:  2.99) | v_pred μ=+0.01 σ=0.913
Epoche  5/100 | Total Loss:   3.04 (Value:  0.15, Policy:  2.97) | v_pred μ=+0.01 σ=0.921
Epoche  6/100 | Total Loss:   3.01 (Value:  0.14, Policy:  2.94) | v_pred μ=+0.01 σ=0.925
Epoche  7/100 | Total Loss:   2.97 (Value:  0.14, Policy:  2.90) | v_pred μ=+0.01 σ=0.929
Epoche  8/100 | Total Loss:   2.93 (Value:  0.14, Policy:  2.86) | v_pred μ=+0.01 σ=0.929
Epoche  9/100 | Total Loss:   2.88 (Value:  0.13, Policy:  2.81) | v_pred μ=+0.01 σ=0.930
Epoche 10/100 | Total Loss:   2.84 (Value:  0.13, Policy:  2.77) | v_pred μ=+0.01 σ=0.932
Epoche 11/100 | Total Loss:   2.80 (Value:  0.13, Policy:  2.73) | v_pred μ=+0.01 σ=0.932
Epoche 12/100 | Total Loss:   2.76 (Value:  0.13, Policy:  2.69) | v_pred μ=+0.01 σ=0.932
Epoche 13/100 | Total Loss:   2.72 (Value:  0.13, Policy:  2.65) | v_pred μ=+0.01 σ=0.933
Epoche 14/100 | Total Loss:   2.69 (Value:  0.13, Policy:  2.62) | v_pred μ=+0.01 σ=0.934
Epoche 15/100 | Total Loss:   2.66 (Value:  0.13, Policy:  2.60) | v_pred μ=+0.01 σ=0.935
Epoche 16/100 | Total Loss:   2.64 (Value:  0.13, Policy:  2.58) | v_pred μ=+0.01 σ=0.935
Epoche 17/100 | Total Loss:   2.62 (Value:  0.13, Policy:  2.56) | v_pred μ=+0.01 σ=0.936
Epoche 18/100 | Total Loss:   2.60 (Value:  0.12, Policy:  2.54) | v_pred μ=+0.01 σ=0.936
Epoche 19/100 | Total Loss:   2.59 (Value:  0.12, Policy:  2.53) | v_pred μ=+0.01 σ=0.937
Epoche 20/100 | Total Loss:   2.57 (Value:  0.12, Policy:  2.51) | v_pred μ=+0.01 σ=0.937
Epoche 21/100 | Total Loss:   2.56 (Value:  0.12, Policy:  2.50) | v_pred μ=+0.01 σ=0.939
Epoche 22/100 | Total Loss:   2.55 (Value:  0.12, Policy:  2.49) | v_pred μ=+0.01 σ=0.940
Epoche 23/100 | Total Loss:   2.54 (Value:  0.12, Policy:  2.48) | v_pred μ=+0.01 σ=0.940
Epoche 24/100 | Total Loss:   2.53 (Value:  0.12, Policy:  2.47) | v_pred μ=+0.01 σ=0.940
Epoche 25/100 | Total Loss:   2.52 (Value:  0.11, Policy:  2.46) | v_pred μ=+0.01 σ=0.942
Epoche 26/100 | Total Loss:   2.51 (Value:  0.11, Policy:  2.45) | v_pred μ=+0.01 σ=0.942
Epoche 27/100 | Total Loss:   2.50 (Value:  0.11, Policy:  2.44) | v_pred μ=+0.01 σ=0.943
Epoche 28/100 | Total Loss:   2.49 (Value:  0.11, Policy:  2.44) | v_pred μ=+0.01 σ=0.943
Epoche 29/100 | Total Loss:   2.49 (Value:  0.11, Policy:  2.43) | v_pred μ=+0.01 σ=0.943
Epoche 30/100 | Total Loss:   2.48 (Value:  0.11, Policy:  2.42) | v_pred μ=+0.01 σ=0.944
Epoche 31/100 | Total Loss:   2.47 (Value:  0.11, Policy:  2.42) | v_pred μ=+0.01 σ=0.945
Epoche 32/100 | Total Loss:   2.47 (Value:  0.11, Policy:  2.41) | v_pred μ=+0.01 σ=0.945
Epoche 33/100 | Total Loss:   2.46 (Value:  0.11, Policy:  2.41) | v_pred μ=+0.01 σ=0.946
Epoche 34/100 | Total Loss:   2.45 (Value:  0.11, Policy:  2.40) | v_pred μ=+0.01 σ=0.946
Epoche 35/100 | Total Loss:   2.45 (Value:  0.10, Policy:  2.40) | v_pred μ=+0.01 σ=0.947
Epoche 36/100 | Total Loss:   2.45 (Value:  0.10, Policy:  2.39) | v_pred μ=+0.01 σ=0.947
Epoche 37/100 | Total Loss:   2.44 (Value:  0.10, Policy:  2.39) | v_pred μ=+0.01 σ=0.948
Epoche 38/100 | Total Loss:   2.44 (Value:  0.10, Policy:  2.39) | v_pred μ=+0.01 σ=0.948
Epoche 39/100 | Total Loss:   2.43 (Value:  0.10, Policy:  2.38) | v_pred μ=+0.01 σ=0.948  🟡 PLATEAU
Epoche 40/100 | Total Loss:   2.43 (Value:  0.10, Policy:  2.38) | v_pred μ=+0.01 σ=0.949  🟡 PLATEAU
Epoche 41/100 | Total Loss:   2.43 (Value:  0.10, Policy:  2.37) | v_pred μ=+0.01 σ=0.949  🔴 PLATEAU + VALUE SINKT (Overfitting-Risiko)
Epoche 42/100 | Total Loss:   2.42 (Value:  0.10, Policy:  2.37) | v_pred μ=+0.01 σ=0.950  🔴 PLATEAU + VALUE SINKT (Overfitting-Risiko)
Epoche 43/100 | Total Loss:   2.41 (Value:  0.10, Policy:  2.36) | v_pred μ=+0.01 σ=0.950  🔴 PLATEAU + VALUE SINKT (Overfitting-Risiko)
Epoche 44/100 | Total Loss:   2.41 (Value:  0.10, Policy:  2.36) | v_pred μ=+0.01 σ=0.951  🔴 PLATEAU + VALUE SINKT (Overfitting-Risiko)

⏹️  Early Stopping: Policy plateaut seit Epoche 39 (5 Epochen ohne Fortschritt).

=======================================================
  TRAINING SUMMARY
=======================================================
  Epochen:       100
  Züge:          790,193
  Batches/Epoche:3087
───────────────────────────────────────────────────────
  Policy Loss:   2.3613 / 6.18 max  (38.2%)  🟡 Gut
  Value Loss:    0.0978  🟡 Gut
───────────────────────────────────────────────────────
  ⏹️  Early Stopping nach Epoche 44/100
  🟡 Plateau ab Epoche 39.
     → Für nächste Generation: mehr Sims im Self-Play.
=======================================================

=======================================================
  NETZAUSLASTUNG (Hidden Size: 512)
───────────────────────────────────────────────────────
  Schicht          Dead   Aktiv-Rate        Eff.Rank
  ───────────────────────────────────────────────────
  layer1     0/512 (0%)          35%   218/512 (43%)
  layer2     0/512 (0%)          29%   216/512 (42%)
  layer3    95/512 (19%)           6%   172/512 (34%)
  ───────────────────────────────────────────────────
  🟢 Gesunde Auslastung (Dead 6%, Rank 39%).
=======================================================

✅ Training beendet! Neues Model gespeichert unter:
📂 D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v8.pth
✅ Exportiert: D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v8.onnx  (input=684, hidden=512, value_hidden=128, opset=13)
📎 Referenz für Rust-Parität: D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v8.onnx.ref.txt
```

**Stage 1 vs. Stage 2**

```
Stage 1
=======================================================
  ERGEBNIS-ÜBERSICHT: 10 Dateien
  (100 Spiele aus 10 Datei(en))
───────────────────────────────────────────────────────
  0:0 Spiele:           3 (3.0%)
  Ø Winner-Score:    5.9  (Max: 14)
  Ø Margin:          2.9  (Max: 12)

=======================================================

=======================================================
  STRAFLEISTEN-BIAS: 10 Dateien
  (Analyse von 10 Datei(en))
=======================================================
───────────────────────────────────────────────────────
  Schritte analysiert:             4,177
  Strafleisten-Zug angeboten:      4,072
  Ø Prob wenn angeboten:           0.044
  Strafleiste war TOP-Wahl:        92 (2.2%)
    davon mit Reihen-Alternative:  0
───────────────────────────────────────────────────────
  → ✅ HARMLOS: angeboten, aber kaum bevorzugt (niedrige Prob)
=======================================================
```

```
Stage 2
=======================================================
  ERGEBNIS-ÜBERSICHT: 10 Dateien
  (100 Spiele aus 10 Datei(en))
───────────────────────────────────────────────────────
  0:0 Spiele:          28 (28.0%)
  Ø Winner-Score:    3.4  (Max: 10)
  Ø Margin:          2.4  (Max: 10)

=======================================================

=======================================================
  STRAFLEISTEN-BIAS: 10 Dateien
  (Analyse von 10 Datei(en))
=======================================================
───────────────────────────────────────────────────────
  Schritte analysiert:             6,317
  Strafleisten-Zug angeboten:      7,277
  Ø Prob wenn angeboten:           0.059
  Strafleiste war TOP-Wahl:        254 (4.0%)
    davon mit Reihen-Alternative:  0
───────────────────────────────────────────────────────
  → ✅ HARMLOS: angeboten, aber kaum bevorzugt (niedrige Prob)
=======================================================
```

Faktor 0:0 Stage 2 / Stage 1 -> 9.333 -> weiter mit Stufe 1

**Arena vs. heuristik**

```
🏟️ Mosaic-AI ARENA — Netz vs Heuristik (Rust) 🏟️
  v8 (Brett 0, 200 Sims, Stufe 1/DFS-Blatt) vs Heuristik(s200) (Brett 1, 200 Sims) — 100 Spiele
--------------------------------------------------
  #  1/100:   6:3   -> v8                       | Züge  47 | Strength 0.258 | Stand Netz 1:0 Heur | Elo 1004/996
  #  2/100:  12:27  -> Heuristik(s200)          | Züge 105 | Strength 0.854 | Stand Netz 1:1 Heur | Elo 990/1010
  #  3/100:  22:0   -> v8                       | Züge 158 | Strength 0.798 | Stand Netz 2:1 Heur | Elo 1003/997
  #  4/100:  34:19  -> v8                       | Züge 159 | Strength 0.933 | Stand Netz 3:1 Heur | Elo 1018/982
  #  5/100:  44:39  -> v8                       | Züge 159 | Strength 0.700 | Stand Netz 4:1 Heur | Elo 1028/972
  #  6/100:   0:55  -> Heuristik(s200)          | Züge 149 | Strength 1.000 | Stand Netz 4:2 Heur | Elo 1009/991
  #  7/100:   8:11  -> Heuristik(s200)          | Züge 161 | Strength 0.314 | Stand Netz 4:3 Heur | Elo 1004/996
  #  8/100:  31:28  -> v8                       | Züge 156 | Strength 0.539 | Stand Netz 5:3 Heur | Elo 1012/988
  #  9/100:  21:24  -> Heuristik(s200)          | Züge 150 | Strength 0.460 | Stand Netz 5:4 Heur | Elo 1004/996
  # 10/100:   0:37  -> Heuristik(s200)          | Züge 159 | Strength 0.966 | Stand Netz 5:5 Heur | Elo 988/1012
  # 11/100:  35:8   -> v8                       | Züge 160 | Strength 0.944 | Stand Netz 6:5 Heur | Elo 1004/996
  # 12/100:  36:24  -> v8                       | Züge 161 | Strength 0.865 | Stand Netz 7:5 Heur | Elo 1018/982
  # 13/100:  50:43  -> v8                       | Züge 155 | Strength 0.760 | Stand Netz 8:5 Heur | Elo 1029/971
  # 14/100:  10:26  -> Heuristik(s200)          | Züge 155 | Strength 0.843 | Stand Netz 8:6 Heur | Elo 1013/987
  # 15/100:  24:25  -> Heuristik(s200)          | Züge 146 | Strength 0.411 | Stand Netz 8:7 Heur | Elo 1006/994
  # 16/100:  26:24  -> v8                       | Züge 151 | Strength 0.453 | Stand Netz 9:7 Heur | Elo 1013/987
  # 17/100:  37:43  -> Heuristik(s200)          | Züge 162 | Strength 0.730 | Stand Netz 9:8 Heur | Elo 1000/1000
  # 18/100:  39:21  -> v8                       | Züge 154 | Strength 0.989 | Stand Netz 10:8 Heur | Elo 1016/984
  # 19/100:  37:11  -> v8                       | Züge 158 | Strength 0.966 | Stand Netz 11:8 Heur | Elo 1030/970
  # 20/100:  31:30  -> v8                       | Züge 154 | Strength 0.479 | Stand Netz 12:8 Heur | Elo 1036/964
  # 21/100:   1:0   -> v8                       | Züge 153 | Strength 0.141 | Stand Netz 13:8 Heur | Elo 1038/962
  # 22/100:  42:53  -> Heuristik(s200)          | Züge 155 | Strength 0.880 | Stand Netz 13:9 Heur | Elo 1021/979
  # 23/100:  46:8   -> v8                       | Züge 152 | Strength 1.000 | Stand Netz 14:9 Heur | Elo 1035/965
  # 24/100:  10:9   -> v8                       | Züge 157 | Strength 0.242 | Stand Netz 15:9 Heur | Elo 1038/962
  # 25/100:  20:24  -> Heuristik(s200)          | Züge 157 | Strength 0.490 | Stand Netz 15:10 Heur | Elo 1028/972
  # 26/100:  54:39  -> v8                       | Züge 156 | Strength 1.000 | Stand Netz 16:10 Heur | Elo 1041/959
  # 27/100:   7:41  -> Heuristik(s200)          | Züge 156 | Strength 1.000 | Stand Netz 16:11 Heur | Elo 1021/979
  # 28/100:  12:70  -> Heuristik(s200)          | Züge 153 | Strength 1.000 | Stand Netz 16:12 Heur | Elo 1003/997
  # 29/100:  14:9   -> v8                       | Züge 154 | Strength 0.407 | Stand Netz 17:12 Heur | Elo 1009/991
  # 30/100:  13:1   -> v8                       | Züge 154 | Strength 0.606 | Stand Netz 18:12 Heur | Elo 1018/982
  # 31/100:  17:9   -> v8                       | Züge 153 | Strength 0.531 | Stand Netz 19:12 Heur | Elo 1026/974
  # 32/100:  30:25  -> v8                       | Züge 158 | Strength 0.588 | Stand Netz 20:12 Heur | Elo 1034/966
  # 33/100:  31:31  -> Heuristik(s200)          | Züge 150 | Strength 0.449 | Stand Netz 20:13 Heur | Elo 1025/975
  # 34/100:  57:28  -> v8                       | Züge 164 | Strength 1.000 | Stand Netz 21:13 Heur | Elo 1039/961
  # 35/100:  35:40  -> Heuristik(s200)          | Züge 161 | Strength 0.700 | Stand Netz 21:14 Heur | Elo 1025/975
  # 36/100:  36:19  -> v8                       | Züge 147 | Strength 0.955 | Stand Netz 22:14 Heur | Elo 1038/962
  # 37/100:  25:19  -> v8                       | Züge 153 | Strength 0.561 | Stand Netz 23:14 Heur | Elo 1045/955
  # 38/100:  36:42  -> Heuristik(s200)          | Züge 159 | Strength 0.730 | Stand Netz 23:15 Heur | Elo 1030/970
  # 39/100:  37:12  -> v8                       | Züge 153 | Strength 0.966 | Stand Netz 24:15 Heur | Elo 1043/957
  # 40/100:   2:6   -> Heuristik(s200)          | Züge 151 | Strength 0.287 | Stand Netz 24:16 Heur | Elo 1037/963
  # 41/100:   3:0   -> v8                       | Züge 150 | Strength 0.224 | Stand Netz 25:16 Heur | Elo 1040/960
  # 42/100:  21:15  -> v8                       | Züge 150 | Strength 0.516 | Stand Netz 26:16 Heur | Elo 1046/954
  # 43/100:  18:0   -> v8                       | Züge 157 | Strength 0.753 | Stand Netz 27:16 Heur | Elo 1055/945
  # 44/100:  23:19  -> v8                       | Züge 153 | Strength 0.479 | Stand Netz 28:16 Heur | Elo 1060/940
  # 45/100:  43:43  -> Heuristik(s200)          | Züge 159 | Strength 0.550 | Stand Netz 28:17 Heur | Elo 1048/952
  # 46/100:   0:21  -> Heuristik(s200)          | Züge 150 | Strength 0.786 | Stand Netz 28:18 Heur | Elo 1032/968
  # 47/100:  33:21  -> v8                       | Züge 163 | Strength 0.831 | Stand Netz 29:18 Heur | Elo 1043/957
  # 48/100:   0:35  -> Heuristik(s200)          | Züge 157 | Strength 0.944 | Stand Netz 29:19 Heur | Elo 1024/976
  # 49/100:  23:1   -> v8                       | Züge 151 | Strength 0.809 | Stand Netz 30:19 Heur | Elo 1035/965
  # 50/100:  24:3   -> v8                       | Züge 155 | Strength 0.820 | Stand Netz 31:19 Heur | Elo 1046/954
  # 51/100:   5:35  -> Heuristik(s200)          | Züge 155 | Strength 0.944 | Stand Netz 31:20 Heur | Elo 1027/973
  # 52/100:  22:34  -> Heuristik(s200)          | Züge 152 | Strength 0.843 | Stand Netz 31:21 Heur | Elo 1011/989
  # 53/100:  12:21  -> Heuristik(s200)          | Züge 159 | Strength 0.606 | Stand Netz 31:22 Heur | Elo 1001/999
  # 54/100:  39:32  -> v8                       | Züge 158 | Strength 0.749 | Stand Netz 32:22 Heur | Elo 1013/987
  # 55/100:  21:8   -> v8                       | Züge 156 | Strength 0.726 | Stand Netz 33:22 Heur | Elo 1024/976
  # 56/100:   0:3   -> Heuristik(s200)          | Züge 153 | Strength 0.224 | Stand Netz 33:23 Heur | Elo 1020/980
  # 57/100:   0:12  -> Heuristik(s200)          | Züge 150 | Strength 0.595 | Stand Netz 33:24 Heur | Elo 1009/991
  # 58/100:  56:34  -> v8                       | Züge 160 | Strength 1.000 | Stand Netz 34:24 Heur | Elo 1024/976
  # 59/100:  13:63  -> Heuristik(s200)          | Züge 165 | Strength 1.000 | Stand Netz 34:25 Heur | Elo 1006/994
  # 60/100:  33:40  -> Heuristik(s200)          | Züge 162 | Strength 0.760 | Stand Netz 34:26 Heur | Elo 993/1007
  # 61/100:  37:14  -> v8                       | Züge 158 | Strength 0.966 | Stand Netz 35:26 Heur | Elo 1009/991
  # 62/100:  42:36  -> v8                       | Züge 153 | Strength 0.730 | Stand Netz 36:26 Heur | Elo 1020/980
  # 63/100:  30:15  -> v8                       | Züge 159 | Strength 0.888 | Stand Netz 37:26 Heur | Elo 1033/967
  # 64/100:  34:23  -> v8                       | Züge 157 | Strength 0.812 | Stand Netz 38:26 Heur | Elo 1044/956
  # 65/100:  37:28  -> v8                       | Züge 157 | Strength 0.786 | Stand Netz 39:26 Heur | Elo 1053/947
  # 66/100:  16:0   -> v8                       | Züge 155 | Strength 0.730 | Stand Netz 40:26 Heur | Elo 1061/939
  # 67/100:  40:44  -> Heuristik(s200)          | Züge 153 | Strength 0.670 | Stand Netz 40:27 Heur | Elo 1047/953
  # 68/100:  12:18  -> Heuristik(s200)          | Züge 154 | Strength 0.483 | Stand Netz 40:28 Heur | Elo 1037/963
  # 69/100:  10:4   -> v8                       | Züge 151 | Strength 0.393 | Stand Netz 41:28 Heur | Elo 1042/958
  # 70/100:  34:28  -> v8                       | Züge 156 | Strength 0.663 | Stand Netz 42:28 Heur | Elo 1050/950
  # 71/100:  34:32  -> v8                       | Züge 150 | Strength 0.542 | Stand Netz 43:28 Heur | Elo 1056/944
  # 72/100:  24:43  -> Heuristik(s200)          | Züge 161 | Strength 1.000 | Stand Netz 43:29 Heur | Elo 1035/965
  # 73/100:  59:37  -> v8                       | Züge 152 | Strength 1.000 | Stand Netz 44:29 Heur | Elo 1048/952
  # 74/100:  19:16  -> v8                       | Züge 148 | Strength 0.404 | Stand Netz 45:29 Heur | Elo 1053/947
  # 75/100:  25:18  -> v8                       | Züge 150 | Strength 0.591 | Stand Netz 46:29 Heur | Elo 1060/940
  # 76/100:  48:39  -> v8                       | Züge 156 | Strength 0.820 | Stand Netz 47:29 Heur | Elo 1069/931
  # 77/100:   0:41  -> Heuristik(s200)          | Züge 148 | Strength 1.000 | Stand Netz 47:30 Heur | Elo 1047/953
  # 78/100:   4:10  -> Heuristik(s200)          | Züge 160 | Strength 0.393 | Stand Netz 47:31 Heur | Elo 1039/961
  # 79/100:  22:13  -> v8                       | Züge 160 | Strength 0.618 | Stand Netz 48:31 Heur | Elo 1047/953
  # 80/100:  14:6   -> v8                       | Züge 157 | Strength 0.497 | Stand Netz 49:31 Heur | Elo 1053/947
  # 81/100:  52:21  -> v8                       | Züge 155 | Strength 1.000 | Stand Netz 50:31 Heur | Elo 1064/936
  # 82/100:  19:40  -> Heuristik(s200)          | Züge 148 | Strength 1.000 | Stand Netz 50:32 Heur | Elo 1042/958
  # 83/100:  41:12  -> v8                       | Züge 152 | Strength 1.000 | Stand Netz 51:32 Heur | Elo 1054/946
  # 84/100:   7:17  -> Heuristik(s200)          | Züge 157 | Strength 0.591 | Stand Netz 51:33 Heur | Elo 1042/958
  # 85/100:  35:26  -> v8                       | Züge 150 | Strength 0.764 | Stand Netz 52:33 Heur | Elo 1051/949
  # 86/100:  15:31  -> Heuristik(s200)          | Züge 152 | Strength 0.899 | Stand Netz 52:34 Heur | Elo 1033/967
  # 87/100:  12:0   -> v8                       | Züge 155 | Strength 0.595 | Stand Netz 53:34 Heur | Elo 1041/959
  # 88/100:  35:34  -> v8                       | Züge 157 | Strength 0.524 | Stand Netz 54:34 Heur | Elo 1047/953
  # 89/100:  28:24  -> v8                       | Züge 151 | Strength 0.535 | Stand Netz 55:34 Heur | Elo 1053/947
  # 90/100:  25:13  -> v8                       | Züge 160 | Strength 0.741 | Stand Netz 56:34 Heur | Elo 1061/939
  # 91/100:  30:8   -> v8                       | Züge 156 | Strength 0.888 | Stand Netz 57:34 Heur | Elo 1070/930
  # 92/100:  39:16  -> v8                       | Züge 149 | Strength 0.989 | Stand Netz 58:34 Heur | Elo 1080/920
  # 93/100:  28:44  -> Heuristik(s200)          | Züge 158 | Strength 1.000 | Stand Netz 58:35 Heur | Elo 1057/943
  # 94/100:  22:13  -> v8                       | Züge 144 | Strength 0.618 | Stand Netz 59:35 Heur | Elo 1064/936
  # 95/100:  10:51  -> Heuristik(s200)          | Züge 153 | Strength 1.000 | Stand Netz 59:36 Heur | Elo 1042/958
  # 96/100:   8:22  -> Heuristik(s200)          | Züge 111 | Strength 0.768 | Stand Netz 59:37 Heur | Elo 1027/973
  # 97/100:  44:22  -> v8                       | Züge 154 | Strength 1.000 | Stand Netz 60:37 Heur | Elo 1041/959
  # 98/100:  26:41  -> Heuristik(s200)          | Züge 162 | Strength 1.000 | Stand Netz 60:38 Heur | Elo 1021/979
  # 99/100:  24:33  -> Heuristik(s200)          | Züge 154 | Strength 0.741 | Stand Netz 60:39 Heur | Elo 1008/992
  #100/100:   8:35  -> Heuristik(s200)          | Züge 158 | Strength 0.944 | Stand Netz 60:40 Heur | Elo 992/1008
--------------------------------------------------
🏆 ERGEBNIS: v8 60:40 Heuristik(s200) (60% Netz-Siege) in 1305.0s (0.1 Spiele/s)
   Ø Score: v8 24.7 | Heuristik(s200) 23.9
   0:0-Spiele: 0/100 (0.0%)  (Sauberkeits-Indikator)
   Ø Floor-Strafe: v8 22.2 | Heuristik(s200) 21.9
   Elo: v8 992 | Heuristik(s200) 1008
```
