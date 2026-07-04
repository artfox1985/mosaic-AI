trainiert mit

+ --games 2000 --mode network --version v1b --sims 400 --stage 1
+ --games 2000 --mode network --version v1c --sims 400 --stage 1
+ --games 2000 --mode network --version v4 --sims 400 --stage 1
+ -- load v4

512 neuronen pro hidden layer

**Netzdaten**

```
PS D:\Archiv\Documents\Projekte\mosaic-AI> python train.py --name v5 --epochs 100 --load v4
📦 Lade HDF5-Cache (600 Dateien)...
Datensatz geladen: 907954 Züge. (Features pro Zug: 684) — 12.3s

🚀 Starte PyTorch Training auf: CUDA
🧠 Netz-Architektur: 684→512→512→512
⚙️  Hyperparameter (config.py):
   Learning Rate : 0.0006
   Value Weight  : 2.5
   Batch Size    : 256
   Value-Target  : tanh((eigen-0.5*gegner)/50) (Endergebnis statt Win/Loss)
📥 Lade altes Model als Startpunkt: alphazero_v4.pth
   Epochen       : 100
🔄 Warm-Start erkannt: Trainiere für 100 Epochen.
Epoche  1/100 | Total Loss:   2.71 (Value:  0.02, Policy:  2.66) | v_pred μ=+0.10 σ=0.114
Epoche  2/100 | Total Loss:   2.47 (Value:  0.02, Policy:  2.42) | v_pred μ=+0.10 σ=0.116
Epoche  3/100 | Total Loss:   2.38 (Value:  0.02, Policy:  2.33) | v_pred μ=+0.10 σ=0.118
Epoche  4/100 | Total Loss:   2.32 (Value:  0.02, Policy:  2.27) | v_pred μ=+0.10 σ=0.119
Epoche  5/100 | Total Loss:   2.28 (Value:  0.02, Policy:  2.23) | v_pred μ=+0.10 σ=0.120
Epoche  6/100 | Total Loss:   2.25 (Value:  0.02, Policy:  2.21) | v_pred μ=+0.10 σ=0.120
Epoche  7/100 | Total Loss:   2.24 (Value:  0.02, Policy:  2.19) | v_pred μ=+0.10 σ=0.121
Epoche  8/100 | Total Loss:   2.22 (Value:  0.02, Policy:  2.17) | v_pred μ=+0.10 σ=0.122
Epoche  9/100 | Total Loss:   2.21 (Value:  0.02, Policy:  2.16) | v_pred μ=+0.10 σ=0.122
Epoche 10/100 | Total Loss:   2.20 (Value:  0.02, Policy:  2.15) | v_pred μ=+0.10 σ=0.123
Epoche 11/100 | Total Loss:   2.19 (Value:  0.02, Policy:  2.15) | v_pred μ=+0.10 σ=0.123
Epoche 12/100 | Total Loss:   2.19 (Value:  0.02, Policy:  2.14) | v_pred μ=+0.10 σ=0.124
Epoche 13/100 | Total Loss:   2.18 (Value:  0.02, Policy:  2.13) | v_pred μ=+0.10 σ=0.124
Epoche 14/100 | Total Loss:   2.18 (Value:  0.02, Policy:  2.13) | v_pred μ=+0.10 σ=0.125
Epoche 15/100 | Total Loss:   2.17 (Value:  0.02, Policy:  2.12) | v_pred μ=+0.10 σ=0.125
Epoche 16/100 | Total Loss:   2.17 (Value:  0.02, Policy:  2.12) | v_pred μ=+0.10 σ=0.125
Epoche 17/100 | Total Loss:   2.16 (Value:  0.02, Policy:  2.12) | v_pred μ=+0.10 σ=0.126
Epoche 18/100 | Total Loss:   2.16 (Value:  0.02, Policy:  2.11) | v_pred μ=+0.10 σ=0.126
Epoche 19/100 | Total Loss:   2.16 (Value:  0.02, Policy:  2.11) | v_pred μ=+0.10 σ=0.126
Epoche 20/100 | Total Loss:   2.15 (Value:  0.02, Policy:  2.11) | v_pred μ=+0.10 σ=0.126  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 21/100 | Total Loss:   2.15 (Value:  0.02, Policy:  2.11) | v_pred μ=+0.10 σ=0.127  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 22/100 | Total Loss:   2.15 (Value:  0.02, Policy:  2.10) | v_pred μ=+0.10 σ=0.127  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 23/100 | Total Loss:   2.15 (Value:  0.02, Policy:  2.10) | v_pred μ=+0.10 σ=0.127  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 24/100 | Total Loss:   2.15 (Value:  0.02, Policy:  2.10) | v_pred μ=+0.10 σ=0.128  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 25/100 | Total Loss:   2.14 (Value:  0.02, Policy:  2.10) | v_pred μ=+0.10 σ=0.128  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 26/100 | Total Loss:   2.14 (Value:  0.02, Policy:  2.10) | v_pred μ=+0.10 σ=0.128  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 27/100 | Total Loss:   2.14 (Value:  0.02, Policy:  2.09) | v_pred μ=+0.10 σ=0.128  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 28/100 | Total Loss:   2.13 (Value:  0.02, Policy:  2.09) | v_pred μ=+0.10 σ=0.128  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 29/100 | Total Loss:   2.14 (Value:  0.02, Policy:  2.09) | v_pred μ=+0.10 σ=0.129  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 30/100 | Total Loss:   2.13 (Value:  0.02, Policy:  2.09) | v_pred μ=+0.10 σ=0.129  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 31/100 | Total Loss:   2.13 (Value:  0.02, Policy:  2.09) | v_pred μ=+0.10 σ=0.129  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 32/100 | Total Loss:   2.13 (Value:  0.02, Policy:  2.08) | v_pred μ=+0.10 σ=0.129  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 33/100 | Total Loss:   2.13 (Value:  0.02, Policy:  2.08) | v_pred μ=+0.10 σ=0.129  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 34/100 | Total Loss:   2.13 (Value:  0.02, Policy:  2.08) | v_pred μ=+0.10 σ=0.130  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 35/100 | Total Loss:   2.12 (Value:  0.02, Policy:  2.08) | v_pred μ=+0.10 σ=0.130  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 36/100 | Total Loss:   2.12 (Value:  0.02, Policy:  2.08) | v_pred μ=+0.10 σ=0.130  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 37/100 | Total Loss:   2.12 (Value:  0.02, Policy:  2.08) | v_pred μ=+0.10 σ=0.130  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 38/100 | Total Loss:   2.12 (Value:  0.02, Policy:  2.07) | v_pred μ=+0.10 σ=0.131  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 39/100 | Total Loss:   2.12 (Value:  0.02, Policy:  2.08) | v_pred μ=+0.10 σ=0.131  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 40/100 | Total Loss:   2.12 (Value:  0.02, Policy:  2.07) | v_pred μ=+0.10 σ=0.131  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 41/100 | Total Loss:   2.12 (Value:  0.02, Policy:  2.08) | v_pred μ=+0.10 σ=0.131  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 42/100 | Total Loss:   2.11 (Value:  0.02, Policy:  2.07) | v_pred μ=+0.10 σ=0.131  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 43/100 | Total Loss:   2.11 (Value:  0.02, Policy:  2.07) | v_pred μ=+0.10 σ=0.131  🟡 POLICY-PLATEAU
Epoche 44/100 | Total Loss:   2.11 (Value:  0.02, Policy:  2.07) | v_pred μ=+0.10 σ=0.131  🟡 POLICY-PLATEAU
Epoche 45/100 | Total Loss:   2.11 (Value:  0.02, Policy:  2.07) | v_pred μ=+0.10 σ=0.132  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 46/100 | Total Loss:   2.11 (Value:  0.02, Policy:  2.07) | v_pred μ=+0.10 σ=0.132  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 47/100 | Total Loss:   2.11 (Value:  0.02, Policy:  2.07) | v_pred μ=+0.10 σ=0.132  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 48/100 | Total Loss:   2.11 (Value:  0.02, Policy:  2.06) | v_pred μ=+0.10 σ=0.132  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 49/100 | Total Loss:   2.11 (Value:  0.02, Policy:  2.07) | v_pred μ=+0.10 σ=0.132  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 50/100 | Total Loss:   2.10 (Value:  0.02, Policy:  2.06) | v_pred μ=+0.10 σ=0.132  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 51/100 | Total Loss:   2.10 (Value:  0.02, Policy:  2.06) | v_pred μ=+0.10 σ=0.132  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 52/100 | Total Loss:   2.10 (Value:  0.02, Policy:  2.06) | v_pred μ=+0.10 σ=0.132  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 53/100 | Total Loss:   2.10 (Value:  0.02, Policy:  2.06) | v_pred μ=+0.10 σ=0.133  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 54/100 | Total Loss:   2.10 (Value:  0.02, Policy:  2.06) | v_pred μ=+0.10 σ=0.133  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 55/100 | Total Loss:   2.10 (Value:  0.02, Policy:  2.06) | v_pred μ=+0.10 σ=0.133  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 56/100 | Total Loss:   2.10 (Value:  0.02, Policy:  2.06) | v_pred μ=+0.10 σ=0.133  🟡 POLICY-PLATEAU
Epoche 57/100 | Total Loss:   2.10 (Value:  0.02, Policy:  2.06) | v_pred μ=+0.10 σ=0.133  🟡 POLICY-PLATEAU
Epoche 58/100 | Total Loss:   2.10 (Value:  0.02, Policy:  2.06) | v_pred μ=+0.10 σ=0.133  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 59/100 | Total Loss:   2.10 (Value:  0.02, Policy:  2.06) | v_pred μ=+0.10 σ=0.133  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 60/100 | Total Loss:   2.10 (Value:  0.02, Policy:  2.06) | v_pred μ=+0.10 σ=0.134  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 61/100 | Total Loss:   2.10 (Value:  0.02, Policy:  2.05) | v_pred μ=+0.10 σ=0.134  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 62/100 | Total Loss:   2.09 (Value:  0.02, Policy:  2.05) | v_pred μ=+0.10 σ=0.134  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 63/100 | Total Loss:   2.09 (Value:  0.02, Policy:  2.05) | v_pred μ=+0.10 σ=0.134  🟡 PLATEAU (Policy+Value)
Epoche 64/100 | Total Loss:   2.10 (Value:  0.02, Policy:  2.05) | v_pred μ=+0.10 σ=0.134  🟡 PLATEAU (Policy+Value)
Epoche 65/100 | Total Loss:   2.09 (Value:  0.02, Policy:  2.05) | v_pred μ=+0.10 σ=0.134  🟡 PLATEAU (Policy+Value)
Epoche 66/100 | Total Loss:   2.09 (Value:  0.02, Policy:  2.05) | v_pred μ=+0.10 σ=0.134  🟡 PLATEAU (Policy+Value)
Epoche 67/100 | Total Loss:   2.09 (Value:  0.02, Policy:  2.05) | v_pred μ=+0.10 σ=0.135  🟡 PLATEAU (Policy+Value)
Epoche 68/100 | Total Loss:   2.09 (Value:  0.02, Policy:  2.05) | v_pred μ=+0.10 σ=0.135  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)

⏹️  Early Stopping: Policy+Value plateaut seit Epoche 63 (5 Epochen ohne Fortschritt).

=======================================================
  TRAINING SUMMARY
=======================================================
  Epochen:       100
  Züge:          907,954
  Batches/Epoche:3546
───────────────────────────────────────────────────────
  Policy Loss:   2.0493 / 6.18 max  (33.2%)  🟡 Gut
  Value Loss:    0.0163  🟢 Sehr gut
───────────────────────────────────────────────────────
  ⏹️  Early Stopping nach Epoche 68/100
  🟡 Plateau ab Epoche 63.
     → Für nächste Generation: mehr Sims im Self-Play.
=======================================================

=======================================================
  NETZAUSLASTUNG (Hidden Size: 512)
───────────────────────────────────────────────────────
  Schicht          Dead   Aktiv-Rate        Eff.Rank
  ───────────────────────────────────────────────────
  layer1     0/512 (0%)          41%   220/512 (43%)
  layer2     0/512 (0%)          32%   209/512 (41%)
  layer3    64/512 (12%)          10%   202/512 (40%)
  ───────────────────────────────────────────────────
  🟢 Gesunde Auslastung (Dead 4%, Rank 41%).
=======================================================

✅ Training beendet! Neues Model gespeichert unter:
📂 D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v5.pth
📈 Loss-Verlauf gespeichert unter:
📂 D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v5_loss.png
✅ Exportiert: D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v5.onnx  (input=684, hidden=512, value_hidden=128, opset=13)
📎 Referenz für Rust-Parität: D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v5.onnx.ref.txt**Stage 1 vs. Stage 2**
```

```
=======================================================
  STAGE-2-REIFEGRAD-SONDE (100 Spiele je Stufe, 400 Sims)
───────────────────────────────────────────────────────
  Stufe 1 (DFS-Blatt):   0:0  14.0% (14/100) | Ø Sieger-Score  15.1
  Stufe 2 (Netz-Value):  0:0  38.0% (38/100) | Ø Sieger-Score   5.6
  Verhältnis 0:0(Stufe2/Stufe1, geglättet): 2.60x
  🟡 GELB — noch nicht reif, Trend über Generationen beobachten
=======================================================
```

**Arena vs. Heuristik**

```
PS D:\Archiv\Documents\Projekte\mosaic-AI> python arena.py
🏟️ Mosaic-AI ARENA — Netz vs Heuristik (Rust) 🏟️
  v5 (Brett 0, 200 Sims, Stufe 1/DFS-Blatt) vs Heuristik(s200) (Brett 1, 200 Sims) — 100 Spiele
--------------------------------------------------
  #  1/100:  26:23  -> v5                       | Züge 154 | Strength 0.483 | Stand Netz 1:0 Heur | Elo 1008/992
  #  2/100:  18:11  -> v5                       | Züge 149 | Strength 0.513 | Stand Netz 2:0 Heur | Elo 1016/984
  #  3/100:  29:25  -> v5                       | Züge 148 | Strength 0.546 | Stand Netz 3:0 Heur | Elo 1024/976
  #  4/100:  27:32  -> Heuristik(s200)          | Züge 150 | Strength 0.610 | Stand Netz 3:1 Heur | Elo 1013/987
  #  5/100:   8:62  -> Heuristik(s200)          | Züge 157 | Strength 1.000 | Stand Netz 3:2 Heur | Elo 996/1004
  #  6/100:  31:20  -> v5                       | Züge 151 | Strength 0.779 | Stand Netz 4:2 Heur | Elo 1009/991
  #  7/100:   0:18  -> Heuristik(s200)          | Züge 153 | Strength 0.753 | Stand Netz 4:3 Heur | Elo 996/1004
  #  8/100:  23:30  -> Heuristik(s200)          | Züge 158 | Strength 0.648 | Stand Netz 4:4 Heur | Elo 986/1014
  #  9/100:  53:27  -> v5                       | Züge 148 | Strength 1.000 | Stand Netz 5:4 Heur | Elo 1003/997
  # 10/100:   0:36  -> Heuristik(s200)          | Züge 154 | Strength 0.955 | Stand Netz 5:5 Heur | Elo 987/1013
  # 11/100:  23:2   -> v5                       | Züge 152 | Strength 0.809 | Stand Netz 6:5 Heur | Elo 1001/999
  # 12/100:  19:33  -> Heuristik(s200)          | Züge 161 | Strength 0.891 | Stand Netz 6:6 Heur | Elo 987/1013
  # 13/100:  16:1   -> v5                       | Züge 145 | Strength 0.730 | Stand Netz 7:6 Heur | Elo 1000/1000
  # 14/100:   0:1   -> Heuristik(s200)          | Züge 148 | Strength 0.141 | Stand Netz 7:7 Heur | Elo 998/1002
  # 15/100:  19:7   -> v5                       | Züge 157 | Strength 0.674 | Stand Netz 8:7 Heur | Elo 1009/991
  # 16/100:  43:23  -> v5                       | Züge 157 | Strength 1.000 | Stand Netz 9:7 Heur | Elo 1024/976
  # 17/100:  12:22  -> Heuristik(s200)          | Züge 149 | Strength 0.648 | Stand Netz 9:8 Heur | Elo 1012/988
  # 18/100:  12:9   -> v5                       | Züge 146 | Strength 0.325 | Stand Netz 10:8 Heur | Elo 1017/983
  # 19/100:  21:36  -> Heuristik(s200)          | Züge 154 | Strength 0.955 | Stand Netz 10:9 Heur | Elo 1000/1000
  # 20/100:  20:45  -> Heuristik(s200)          | Züge 157 | Strength 1.000 | Stand Netz 10:10 Heur | Elo 984/1016
  # 21/100:  33:19  -> v5                       | Züge 161 | Strength 0.891 | Stand Netz 11:10 Heur | Elo 1000/1000
  # 22/100:  37:21  -> v5                       | Züge 155 | Strength 0.966 | Stand Netz 12:10 Heur | Elo 1015/985
  # 23/100:  42:35  -> v5                       | Züge 158 | Strength 0.760 | Stand Netz 13:10 Heur | Elo 1026/974
  # 24/100:  30:15  -> v5                       | Züge 157 | Strength 0.888 | Stand Netz 14:10 Heur | Elo 1038/962
  # 25/100:  35:41  -> Heuristik(s200)          | Züge 151 | Strength 0.730 | Stand Netz 14:11 Heur | Elo 1024/976
  # 26/100:  62:30  -> v5                       | Züge 154 | Strength 1.000 | Stand Netz 15:11 Heur | Elo 1038/962
  # 27/100:  14:62  -> Heuristik(s200)          | Züge 152 | Strength 1.000 | Stand Netz 15:12 Heur | Elo 1019/981
  # 28/100:  25:25  -> Heuristik(s200)          | Züge 157 | Strength 0.381 | Stand Netz 15:13 Heur | Elo 1012/988
  # 29/100:   0:27  -> Heuristik(s200)          | Züge 156 | Strength 0.854 | Stand Netz 15:14 Heur | Elo 997/1003
  # 30/100:  11:20  -> Heuristik(s200)          | Züge 151 | Strength 0.595 | Stand Netz 15:15 Heur | Elo 988/1012
  # 31/100:  19:26  -> Heuristik(s200)          | Züge 151 | Strength 0.603 | Stand Netz 15:16 Heur | Elo 979/1021
  # 32/100:  34:17  -> v5                       | Züge 149 | Strength 0.933 | Stand Netz 16:16 Heur | Elo 996/1004
  # 33/100:  54:59  -> Heuristik(s200)          | Züge 157 | Strength 0.700 | Stand Netz 16:17 Heur | Elo 985/1015
  # 34/100:   0:39  -> Heuristik(s200)          | Züge 156 | Strength 0.989 | Stand Netz 16:18 Heur | Elo 971/1029
  # 35/100:  16:28  -> Heuristik(s200)          | Züge 157 | Strength 0.775 | Stand Netz 16:19 Heur | Elo 961/1039
  # 36/100:  38:29  -> v5                       | Züge 152 | Strength 0.797 | Stand Netz 17:19 Heur | Elo 977/1023
  # 37/100:  13:43  -> Heuristik(s200)          | Züge 150 | Strength 1.000 | Stand Netz 17:20 Heur | Elo 963/1037
  # 38/100:   5:19  -> Heuristik(s200)          | Züge 147 | Strength 0.734 | Stand Netz 17:21 Heur | Elo 954/1046
  # 39/100:  15:60  -> Heuristik(s200)          | Züge 150 | Strength 1.000 | Stand Netz 17:22 Heur | Elo 942/1058
  # 40/100:  24:28  -> Heuristik(s200)          | Züge 152 | Strength 0.535 | Stand Netz 17:23 Heur | Elo 936/1064
  # 41/100:  36:7   -> v5                       | Züge 149 | Strength 0.955 | Stand Netz 18:23 Heur | Elo 957/1043
  # 42/100:   0:25  -> Heuristik(s200)          | Züge 154 | Strength 0.831 | Stand Netz 18:24 Heur | Elo 947/1053
  # 43/100:   3:20  -> Heuristik(s200)          | Züge 150 | Strength 0.775 | Stand Netz 18:25 Heur | Elo 938/1062
  # 44/100:  43:42  -> v5                       | Züge 164 | Strength 0.580 | Stand Netz 19:25 Heur | Elo 950/1050
  # 45/100:  12:0   -> v5                       | Züge 145 | Strength 0.595 | Stand Netz 20:25 Heur | Elo 962/1038
  # 46/100:  15:7   -> v5                       | Züge 154 | Strength 0.509 | Stand Netz 21:25 Heur | Elo 972/1028
  # 47/100:  31:4   -> v5                       | Züge 159 | Strength 0.899 | Stand Netz 22:25 Heur | Elo 989/1011
  # 48/100:  17:0   -> v5                       | Züge 157 | Strength 0.741 | Stand Netz 23:25 Heur | Elo 1002/998
  # 49/100:  50:39  -> v5                       | Züge 161 | Strength 0.880 | Stand Netz 24:25 Heur | Elo 1016/984
  # 50/100:  42:46  -> Heuristik(s200)          | Züge 160 | Strength 0.670 | Stand Netz 24:26 Heur | Elo 1004/996
  # 51/100:  12:35  -> Heuristik(s200)          | Züge 153 | Strength 0.944 | Stand Netz 24:27 Heur | Elo 989/1011
  # 52/100:  25:46  -> Heuristik(s200)          | Züge 152 | Strength 1.000 | Stand Netz 24:28 Heur | Elo 974/1026
  # 53/100:  11:2   -> v5                       | Züge 151 | Strength 0.494 | Stand Netz 25:28 Heur | Elo 983/1017
  # 54/100:  21:13  -> v5                       | Züge 157 | Strength 0.576 | Stand Netz 26:28 Heur | Elo 993/1007
  # 55/100:  26:23  -> v5                       | Züge 155 | Strength 0.483 | Stand Netz 27:28 Heur | Elo 1001/999
  # 56/100:  18:7   -> v5                       | Züge 157 | Strength 0.632 | Stand Netz 28:28 Heur | Elo 1011/989
  # 57/100:   3:6   -> Heuristik(s200)          | Züge 157 | Strength 0.258 | Stand Netz 28:29 Heur | Elo 1007/993
  # 58/100:  34:55  -> Heuristik(s200)          | Züge 163 | Strength 1.000 | Stand Netz 28:30 Heur | Elo 990/1010
  # 59/100:  27:17  -> v5                       | Züge 160 | Strength 0.704 | Stand Netz 29:30 Heur | Elo 1002/998
  # 60/100:  42:30  -> v5                       | Züge 163 | Strength 0.910 | Stand Netz 30:30 Heur | Elo 1016/984
  # 61/100:   8:0   -> v5                       | Züge 157 | Strength 0.430 | Stand Netz 31:30 Heur | Elo 1022/978
  # 62/100:  28:20  -> v5                       | Züge 157 | Strength 0.655 | Stand Netz 32:30 Heur | Elo 1031/969
  # 63/100:   1:18  -> Heuristik(s200)          | Züge 156 | Strength 0.753 | Stand Netz 32:31 Heur | Elo 1017/983
  # 64/100:   3:54  -> Heuristik(s200)          | Züge 151 | Strength 1.000 | Stand Netz 32:32 Heur | Elo 999/1001
  # 65/100:  25:0   -> v5                       | Züge 167 | Strength 0.831 | Stand Netz 33:32 Heur | Elo 1012/988
  # 66/100:   4:31  -> Heuristik(s200)          | Züge 158 | Strength 0.899 | Stand Netz 33:33 Heur | Elo 997/1003
  # 67/100:  17:5   -> v5                       | Züge 159 | Strength 0.651 | Stand Netz 34:33 Heur | Elo 1008/992
  # 68/100:  19:19  -> Heuristik(s200)          | Züge 153 | Strength 0.314 | Stand Netz 34:34 Heur | Elo 1003/997
  # 69/100:   6:15  -> Heuristik(s200)          | Züge 157 | Strength 0.539 | Stand Netz 34:35 Heur | Elo 994/1006
  # 70/100:  50:26  -> v5                       | Züge 154 | Strength 1.000 | Stand Netz 35:35 Heur | Elo 1011/989
  # 71/100:   8:24  -> Heuristik(s200)          | Züge 155 | Strength 0.820 | Stand Netz 35:36 Heur | Elo 997/1003
  # 72/100:  18:0   -> v5                       | Züge 146 | Strength 0.753 | Stand Netz 36:36 Heur | Elo 1009/991
  # 73/100:  56:13  -> v5                       | Züge 156 | Strength 1.000 | Stand Netz 37:36 Heur | Elo 1024/976
  # 74/100:  56:59  -> Heuristik(s200)          | Züge 155 | Strength 0.640 | Stand Netz 37:37 Heur | Elo 1012/988
  # 75/100:  33:57  -> Heuristik(s200)          | Züge 158 | Strength 1.000 | Stand Netz 37:38 Heur | Elo 995/1005
  # 76/100:  34:6   -> v5                       | Züge 152 | Strength 0.933 | Stand Netz 38:38 Heur | Elo 1010/990
  # 77/100:   0:0   -> Heuristik(s200)          | Züge 153 | Strength 0.100 | Stand Netz 38:39 Heur | Elo 1008/992
  # 78/100:  13:49  -> Heuristik(s200)          | Züge 153 | Strength 1.000 | Stand Netz 38:40 Heur | Elo 991/1009
  # 79/100:  45:21  -> v5                       | Züge 158 | Strength 1.000 | Stand Netz 39:40 Heur | Elo 1008/992
  # 80/100:  29:52  -> Heuristik(s200)          | Züge 156 | Strength 1.000 | Stand Netz 39:41 Heur | Elo 991/1009
  # 81/100:  21:14  -> v5                       | Züge 163 | Strength 0.546 | Stand Netz 40:41 Heur | Elo 1000/1000
  # 82/100:  38:33  -> v5                       | Züge 156 | Strength 0.677 | Stand Netz 41:41 Heur | Elo 1011/989
  # 83/100:  24:8   -> v5                       | Züge 150 | Strength 0.820 | Stand Netz 42:41 Heur | Elo 1023/977
  # 84/100:   0:30  -> Heuristik(s200)          | Züge 152 | Strength 0.888 | Stand Netz 42:42 Heur | Elo 1007/993
  # 85/100:  14:22  -> Heuristik(s200)          | Züge 157 | Strength 0.588 | Stand Netz 42:43 Heur | Elo 997/1003
  # 86/100:  10:10  -> Heuristik(s200)          | Züge 156 | Strength 0.213 | Stand Netz 42:44 Heur | Elo 994/1006
  # 87/100:   0:31  -> Heuristik(s200)          | Züge 157 | Strength 0.899 | Stand Netz 42:45 Heur | Elo 980/1020
  # 88/100:  51:59  -> Heuristik(s200)          | Züge 156 | Strength 0.790 | Stand Netz 42:46 Heur | Elo 969/1031
  # 89/100:  63:42  -> v5                       | Züge 159 | Strength 1.000 | Stand Netz 43:46 Heur | Elo 988/1012
  # 90/100:  25:27  -> Heuristik(s200)          | Züge 157 | Strength 0.464 | Stand Netz 43:47 Heur | Elo 981/1019
  # 91/100:   0:18  -> Heuristik(s200)          | Züge 159 | Strength 0.753 | Stand Netz 43:48 Heur | Elo 970/1030
  # 92/100:  24:0   -> v5                       | Züge 157 | Strength 0.820 | Stand Netz 44:48 Heur | Elo 985/1015
  # 93/100:  13:26  -> Heuristik(s200)          | Züge 158 | Strength 0.782 | Stand Netz 44:49 Heur | Elo 974/1026
  # 94/100:   7:49  -> Heuristik(s200)          | Züge 157 | Strength 1.000 | Stand Netz 44:50 Heur | Elo 960/1040
  # 95/100:   9:55  -> Heuristik(s200)          | Züge 150 | Strength 1.000 | Stand Netz 44:51 Heur | Elo 948/1052
  # 96/100:  31:16  -> v5                       | Züge 161 | Strength 0.899 | Stand Netz 45:51 Heur | Elo 967/1033
  # 97/100:  18:14  -> v5                       | Züge 152 | Strength 0.422 | Stand Netz 46:51 Heur | Elo 975/1025
  # 98/100:  17:30  -> Heuristik(s200)          | Züge 152 | Strength 0.828 | Stand Netz 46:52 Heur | Elo 964/1036
  # 99/100:  46:37  -> v5                       | Züge 154 | Strength 0.820 | Stand Netz 47:52 Heur | Elo 980/1020
  #100/100:  46:46  -> Heuristik(s200)          | Züge 164 | Strength 0.550 | Stand Netz 47:53 Heur | Elo 972/1028
--------------------------------------------------
🏆 ERGEBNIS: v5 47:53 Heuristik(s200) (47% Netz-Siege) in 1548.4s (0.1 Spiele/s)
   Ø Score: v5 22.9 | Heuristik(s200) 25.7
   0:0-Spiele: 1/100 (1.0%)  (Sauberkeits-Indikator)
   Ø Floor-Strafe: v5 23.3 | Heuristik(s200) 21.4
   Elo: v5 972 | Heuristik(s200) 1028
```

Einseitige Kollaps-Rate: 21%. Irgendeine Seite ≤5: 27%. Beide ≤5: 2%. Leichter
Rückgang ggü. v4 (48%→47%, Ø-Score 22.3→22.9 aber Heuristik auch höher 25.5→25.7)
— innerhalb der Schwankungsbreite, kein klares Signal in eine Richtung.

**Arena vs. Champion (v4)**

```
PS D:\Archiv\Documents\Projekte\mosaic-AI> python arena.py
🏟️ Mosaic-AI ARENA — Netz vs Netz (Rust) 🏟️
  v5 (Brett 0, 200 Sims) vs v4 (Brett 1, 200 Sims) — Stufe 1/DFS-Blatt — 100 Spiele
--------------------------------------------------
  #  1/100:   0:20  -> v4                     | Züge 158 | Strength 0.775 | Stand v5 0:1 v4 | Elo 988/1012
  #  2/100:  23:17  -> v5                     | Züge 149 | Strength 0.539 | Stand v5 1:1 v4 | Elo 997/1003
  #  3/100:   3:11  -> v4                     | Züge 158 | Strength 0.464 | Stand v5 1:2 v4 | Elo 990/1010
  #  4/100:  44:36  -> v5                     | Züge 154 | Strength 0.790 | Stand v5 2:2 v4 | Elo 1003/997
  #  5/100:  20:36  -> v4                     | Züge 148 | Strength 0.955 | Stand v5 2:3 v4 | Elo 987/1013
  #  6/100:  38:21  -> v5                     | Züge 157 | Strength 0.978 | Stand v5 3:3 v4 | Elo 1004/996
  #  7/100:  49:23  -> v5                     | Züge 156 | Strength 1.000 | Stand v5 4:3 v4 | Elo 1020/980
  #  8/100:   0:24  -> v4                     | Züge 162 | Strength 0.820 | Stand v5 4:4 v4 | Elo 1005/995
  #  9/100:  46:33  -> v5                     | Züge 157 | Strength 0.940 | Stand v5 5:4 v4 | Elo 1020/980
  # 10/100:  16:15  -> v5                     | Züge 151 | Strength 0.310 | Stand v5 6:4 v4 | Elo 1024/976
  # 11/100:  28:34  -> v4                     | Züge 163 | Strength 0.663 | Stand v5 6:5 v4 | Elo 1012/988
  # 12/100:  26:22  -> v5                     | Züge 153 | Strength 0.513 | Stand v5 7:5 v4 | Elo 1020/980
  # 13/100:  28:63  -> v4                     | Züge 166 | Strength 1.000 | Stand v5 7:6 v4 | Elo 1002/998
  # 14/100:  32:52  -> v4                     | Züge 158 | Strength 1.000 | Stand v5 7:7 v4 | Elo 986/1014
  # 15/100:  17:45  -> v4                     | Züge 159 | Strength 1.000 | Stand v5 7:8 v4 | Elo 971/1029
  # 16/100:  28:42  -> v4                     | Züge 157 | Strength 0.970 | Stand v5 7:9 v4 | Elo 958/1042
  # 17/100:  13:17  -> v4                     | Züge 150 | Strength 0.411 | Stand v5 7:10 v4 | Elo 953/1047
  # 18/100:  29:3   -> v5                     | Züge 152 | Strength 0.876 | Stand v5 8:10 v4 | Elo 971/1029
  # 19/100:  28:53  -> v4                     | Züge 164 | Strength 1.000 | Stand v5 8:11 v4 | Elo 958/1042
  # 20/100:  48:14  -> v5                     | Züge 151 | Strength 1.000 | Stand v5 9:11 v4 | Elo 978/1022
  # 21/100:  36:29  -> v5                     | Züge 153 | Strength 0.715 | Stand v5 10:11 v4 | Elo 991/1009
  # 22/100:  19:32  -> v4                     | Züge 156 | Strength 0.850 | Stand v5 10:12 v4 | Elo 978/1022
  # 23/100:  11:15  -> v4                     | Züge 153 | Strength 0.389 | Stand v5 10:13 v4 | Elo 973/1027
  # 24/100:   1:34  -> v4                     | Züge 156 | Strength 0.933 | Stand v5 10:14 v4 | Elo 960/1040
  # 25/100:  30:18  -> v5                     | Züge 153 | Strength 0.798 | Stand v5 11:14 v4 | Elo 976/1024
  # 26/100:  44:4   -> v5                     | Züge 157 | Strength 1.000 | Stand v5 12:14 v4 | Elo 994/1006
  # 27/100:  51:39  -> v5                     | Züge 160 | Strength 0.910 | Stand v5 13:14 v4 | Elo 1009/991
  # 28/100:  40:3   -> v5                     | Züge 153 | Strength 1.000 | Stand v5 14:14 v4 | Elo 1024/976
  # 29/100:   0:34  -> v4                     | Züge 156 | Strength 0.933 | Stand v5 14:15 v4 | Elo 1007/993
  # 30/100:   6:42  -> v4                     | Züge 163 | Strength 1.000 | Stand v5 14:16 v4 | Elo 990/1010
  # 31/100:   6:3   -> v5                     | Züge 155 | Strength 0.258 | Stand v5 15:16 v4 | Elo 994/1006
  # 32/100:  30:38  -> v4                     | Züge 154 | Strength 0.767 | Stand v5 15:17 v4 | Elo 982/1018
  # 33/100:   4:12  -> v4                     | Züge 155 | Strength 0.475 | Stand v5 15:18 v4 | Elo 975/1025
  # 34/100:  30:18  -> v5                     | Züge 154 | Strength 0.798 | Stand v5 16:18 v4 | Elo 990/1010
  # 35/100:  17:8   -> v5                     | Züge 157 | Strength 0.561 | Stand v5 17:18 v4 | Elo 999/1001
  # 36/100:  29:0   -> v5                     | Züge 164 | Strength 0.876 | Stand v5 18:18 v4 | Elo 1013/987
  # 37/100:  21:21  -> v4                     | Züge 157 | Strength 0.336 | Stand v5 18:19 v4 | Elo 1007/993
  # 38/100:   0:42  -> v4                     | Züge 151 | Strength 1.000 | Stand v5 18:20 v4 | Elo 990/1010
  # 39/100:  33:34  -> v4                     | Züge 164 | Strength 0.512 | Stand v5 18:21 v4 | Elo 982/1018
  # 40/100:  23:9   -> v5                     | Züge 155 | Strength 0.779 | Stand v5 19:21 v4 | Elo 996/1004
  # 41/100:   0:8   -> v4                     | Züge 161 | Strength 0.430 | Stand v5 19:22 v4 | Elo 989/1011
  # 42/100:   0:28  -> v4                     | Züge 158 | Strength 0.865 | Stand v5 19:23 v4 | Elo 976/1024
  # 43/100:  30:39  -> v4                     | Züge 152 | Strength 0.809 | Stand v5 19:24 v4 | Elo 965/1035
  # 44/100:  41:15  -> v5                     | Züge 158 | Strength 1.000 | Stand v5 20:24 v4 | Elo 984/1016
  # 45/100:   8:37  -> v4                     | Züge 153 | Strength 0.966 | Stand v5 20:25 v4 | Elo 970/1030
  # 46/100:   4:32  -> v4                     | Züge 159 | Strength 0.910 | Stand v5 20:26 v4 | Elo 958/1042
  # 47/100:   1:11  -> v4                     | Züge 156 | Strength 0.524 | Stand v5 20:27 v4 | Elo 952/1048
  # 48/100:  13:30  -> v4                     | Züge 154 | Strength 0.888 | Stand v5 20:28 v4 | Elo 942/1058
  # 49/100:  49:49  -> v4                     | Züge 164 | Strength 0.550 | Stand v5 20:29 v4 | Elo 936/1064
  # 50/100:   1:14  -> v4                     | Züge 151 | Strength 0.647 | Stand v5 20:30 v4 | Elo 929/1071
  # 51/100:  29:24  -> v5                     | Züge 158 | Strength 0.576 | Stand v5 21:30 v4 | Elo 942/1058
  # 52/100:   6:0   -> v5                     | Züge 158 | Strength 0.348 | Stand v5 22:30 v4 | Elo 949/1051
  # 53/100:  24:38  -> v4                     | Züge 158 | Strength 0.948 | Stand v5 22:31 v4 | Elo 938/1062
  # 54/100:  10:0   -> v5                     | Züge 142 | Strength 0.513 | Stand v5 23:31 v4 | Elo 949/1051
  # 55/100:   8:0   -> v5                     | Züge 162 | Strength 0.430 | Stand v5 24:31 v4 | Elo 958/1042
  # 56/100:   2:24  -> v4                     | Züge 160 | Strength 0.820 | Stand v5 24:32 v4 | Elo 948/1052
  # 57/100:   0:47  -> v4                     | Züge 148 | Strength 1.000 | Stand v5 24:33 v4 | Elo 937/1063
  # 58/100:  13:7   -> v5                     | Züge 158 | Strength 0.426 | Stand v5 25:33 v4 | Elo 946/1054
  # 59/100:  35:49  -> v4                     | Züge 159 | Strength 0.970 | Stand v5 25:34 v4 | Elo 935/1065
  # 60/100:  13:14  -> v4                     | Züge 150 | Strength 0.287 | Stand v5 25:35 v4 | Elo 932/1068
  # 61/100:   7:26  -> v4                     | Züge 155 | Strength 0.843 | Stand v5 25:36 v4 | Elo 924/1076
  # 62/100:  42:27  -> v5                     | Züge 147 | Strength 1.000 | Stand v5 26:36 v4 | Elo 947/1053
  # 63/100:   3:34  -> v4                     | Züge 160 | Strength 0.933 | Stand v5 26:37 v4 | Elo 936/1064
  # 64/100:  25:38  -> v4                     | Züge 157 | Strength 0.917 | Stand v5 26:38 v4 | Elo 926/1074
  # 65/100:  50:44  -> v5                     | Züge 158 | Strength 0.730 | Stand v5 27:38 v4 | Elo 942/1058
  # 66/100:  12:18  -> v4                     | Züge 158 | Strength 0.483 | Stand v5 27:39 v4 | Elo 937/1063
  # 67/100:   7:0   -> v5                     | Züge 153 | Strength 0.389 | Stand v5 28:39 v4 | Elo 945/1055
  # 68/100:  21:46  -> v4                     | Züge 151 | Strength 1.000 | Stand v5 28:40 v4 | Elo 934/1066
  # 69/100:  30:28  -> v5                     | Züge 152 | Strength 0.498 | Stand v5 29:40 v4 | Elo 945/1055
  # 70/100:   7:34  -> v4                     | Züge 156 | Strength 0.933 | Stand v5 29:41 v4 | Elo 935/1065
  # 71/100:  52:43  -> v5                     | Züge 162 | Strength 0.820 | Stand v5 30:41 v4 | Elo 953/1047
  # 72/100:  15:16  -> v4                     | Züge 159 | Strength 0.310 | Stand v5 30:42 v4 | Elo 949/1051
  # 73/100:  30:16  -> v5                     | Züge 155 | Strength 0.858 | Stand v5 31:42 v4 | Elo 967/1033
  # 74/100:  32:49  -> v4                     | Züge 154 | Strength 1.000 | Stand v5 31:43 v4 | Elo 954/1046
  # 75/100:  26:3   -> v5                     | Züge 152 | Strength 0.843 | Stand v5 32:43 v4 | Elo 971/1029
  # 76/100:  47:19  -> v5                     | Züge 153 | Strength 1.000 | Stand v5 33:43 v4 | Elo 990/1010
  # 77/100:   0:40  -> v4                     | Züge 158 | Strength 1.000 | Stand v5 33:44 v4 | Elo 975/1025
  # 78/100:  17:28  -> v4                     | Züge 154 | Strength 0.745 | Stand v5 33:45 v4 | Elo 965/1035
  # 79/100:   8:14  -> v4                     | Züge 153 | Strength 0.438 | Stand v5 33:46 v4 | Elo 959/1041
  # 80/100:   0:53  -> v4                     | Züge 148 | Strength 1.000 | Stand v5 33:47 v4 | Elo 947/1053
  # 81/100:   0:22  -> v4                     | Züge 144 | Strength 0.798 | Stand v5 33:48 v4 | Elo 938/1062
  # 82/100:   0:28  -> v4                     | Züge 152 | Strength 0.865 | Stand v5 33:49 v4 | Elo 929/1071
  # 83/100:   0:9   -> v4                     | Züge 153 | Strength 0.471 | Stand v5 33:50 v4 | Elo 924/1076
  # 84/100:  15:0   -> v5                     | Züge 152 | Strength 0.719 | Stand v5 34:50 v4 | Elo 940/1060
  # 85/100:  24:23  -> v5                     | Züge 157 | Strength 0.400 | Stand v5 35:50 v4 | Elo 949/1051
  # 86/100:  41:3   -> v5                     | Züge 148 | Strength 1.000 | Stand v5 36:50 v4 | Elo 970/1030
  # 87/100:   9:18  -> v4                     | Züge 156 | Strength 0.573 | Stand v5 36:51 v4 | Elo 962/1038
  # 88/100:  14:4   -> v5                     | Züge 152 | Strength 0.557 | Stand v5 37:51 v4 | Elo 973/1027
  # 89/100:  18:22  -> v4                     | Züge 157 | Strength 0.468 | Stand v5 37:52 v4 | Elo 967/1033
  # 90/100:  24:20  -> v5                     | Züge 151 | Strength 0.490 | Stand v5 38:52 v4 | Elo 976/1024
  # 91/100:  18:0   -> v5                     | Züge 153 | Strength 0.753 | Stand v5 39:52 v4 | Elo 990/1010
  # 92/100:  22:27  -> v4                     | Züge 146 | Strength 0.554 | Stand v5 39:53 v4 | Elo 982/1018
  # 93/100:   0:37  -> v4                     | Züge 149 | Strength 0.966 | Stand v5 39:54 v4 | Elo 968/1032
  # 94/100:  23:18  -> v5                     | Züge 154 | Strength 0.509 | Stand v5 40:54 v4 | Elo 978/1022
  # 95/100:  21:16  -> v5                     | Züge 154 | Strength 0.486 | Stand v5 41:54 v4 | Elo 987/1013
  # 96/100:  26:0   -> v5                     | Züge 159 | Strength 0.843 | Stand v5 42:54 v4 | Elo 1001/999
  # 97/100:  34:30  -> v5                     | Züge 155 | Strength 0.603 | Stand v5 43:54 v4 | Elo 1011/989
  # 98/100:  37:24  -> v5                     | Züge 164 | Strength 0.906 | Stand v5 44:54 v4 | Elo 1025/975
  # 99/100:   4:0   -> v5                     | Züge 161 | Strength 0.265 | Stand v5 45:54 v4 | Elo 1029/971
  #100/100:   8:38  -> v4                     | Züge 148 | Strength 0.978 | Stand v5 45:55 v4 | Elo 1011/989
--------------------------------------------------
🏆 ERGEBNIS: v5 45:55 v4 (45% A-Siege) in 3119.3s (0.0 Spiele/s)
   Ø Score: v5 20.0 | v4 24.0
   0:0-Spiele: 0/100 (0.0%)
   Elo: v5 1011 | v4 989
```

Einseitige Kollaps-Rate: 24%. Irgendeine Seite ≤5: 37%. Beide ≤5: 1%.

**Gate NICHT bestanden.** 45:55 (z=-1.0) — v5 hat v4 nicht nur nicht signifikant
geschlagen, sondern liegt sogar numerisch dahinter (anders als v2/v3, die
wenigstens knapp vorne lagen). Auch Ø-Score spricht für v4 (20.0 vs. 24.0).
**v4 bleibt Champion.** Erste Generation in diesem Zyklus, die gegenüber
ihrem eigenen Vorgänger (v4, der wiederum aus demselben Fenster-Typ trainiert
wurde) keinen Fortschritt zeigt — anders als der bisher makellose Aufwärtstrend
v1→v4. Kein Grund zur Sorge: entspricht genau dem erwarteten Verhalten des
Champion/Kandidat-Protokolls (nicht jeder Kandidat muss gewinnen) — v4
generiert eine weitere Self-Play-Runde (v4b, bereits gestartet), v6 wird mit
größerem Fenster (v1b+v1c+v4+v4b) erneut versuchen.
