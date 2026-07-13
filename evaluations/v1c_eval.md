trainiert mit

- --games 11000 --mode mcts --sims 400

value weight 1

**Netzdaten**

```
PS D:\Archiv\Documents\Projekte\mosaic-AI> python train.py --name v1c --epochs 100
📦 Lade HDF5-Cache (990 Dateien)...
Datensatz geladen: 1501066 Züge. (Features pro Zug: 684) — 109.9s
📦 Lade HDF5-Cache (110 Dateien)...
Datensatz geladen: 167036 Züge. (Features pro Zug: 684) — 8.9s
   Val-Split: 990 Trainings-Dateien / 110 Val-Dateien (1,501,066 / 167,036 Züge)
   Value-Ziel-Streuung: σ=0.183 (Varianz=0.0334, zum Vergleich mit v_pred σ unten; Varianz ist die Baseline-MSE bei reiner Mittelwert-Vorhersage)

🚀 Starte PyTorch Training auf: CUDA
🧠 Netz-Architektur: 684→512→512→512
⚙️  Hyperparameter (config.py):
   Learning Rate : 0.0004
   Value Weight  : 1
   Batch Size    : 256
   Value-Target  : tanh(eigen/50) - 0.1*tanh(gegner/50) (Endergebnis statt Win/Loss)
   Epochen       : 100
🆕 Neues Modell: Trainiere für 100 Epochen.
Epoche  1/100 | Total Loss:   3.05 (R²=+0.47, Policy:  3.03) | Val-R²=+0.39 | Policy-Val= 2.23 | v_pred μ=+0.18 σ=0.127
Epoche  2/100 | Total Loss:   2.99 (R²=+0.55, Policy:  2.98) | Val-R²=+0.37 | Policy-Val= 2.21 | v_pred μ=+0.19 σ=0.136
Epoche  3/100 | Total Loss:   2.96 (R²=+0.58, Policy:  2.95) | Val-R²=+0.34 | Policy-Val= 2.20 | v_pred μ=+0.19 σ=0.139
Epoche  4/100 | Total Loss:   2.94 (R²=+0.59, Policy:  2.93) | Val-R²=+0.34 | Policy-Val= 2.20 | v_pred μ=+0.19 σ=0.140
Epoche  5/100 | Total Loss:   2.93 (R²=+0.59, Policy:  2.91) | Val-R²=+0.34 | Policy-Val= 2.21 | v_pred μ=+0.19 σ=0.140
Epoche  6/100 | Total Loss:   2.91 (R²=+0.58, Policy:  2.89) | Val-R²=+0.33 | Policy-Val= 2.21 | v_pred μ=+0.19 σ=0.139
Epoche  7/100 | Total Loss:   2.88 (R²=+0.56, Policy:  2.86) | Val-R²=+0.34 | Policy-Val= 2.21 | v_pred μ=+0.19 σ=0.137
Epoche  8/100 | Total Loss:   2.84 (R²=+0.55, Policy:  2.83) | Val-R²=+0.34 | Policy-Val= 2.22 | v_pred μ=+0.19 σ=0.136
Epoche  9/100 | Total Loss:   2.80 (R²=+0.54, Policy:  2.78) | Val-R²=+0.34 | Policy-Val= 2.22 | v_pred μ=+0.19 σ=0.134
Epoche 10/100 | Total Loss:   2.75 (R²=+0.53, Policy:  2.74) | Val-R²=+0.34 | Policy-Val= 2.22 | v_pred μ=+0.19 σ=0.133
Epoche 11/100 | Total Loss:   2.71 (R²=+0.52, Policy:  2.69) | Val-R²=+0.34 | Policy-Val= 2.23 | v_pred μ=+0.19 σ=0.133
Epoche 12/100 | Total Loss:   2.66 (R²=+0.52, Policy:  2.65) | Val-R²=+0.34 | Policy-Val= 2.23 | v_pred μ=+0.19 σ=0.132
Epoche 13/100 | Total Loss:   2.63 (R²=+0.52, Policy:  2.61) | Val-R²=+0.34 | Policy-Val= 2.23 | v_pred μ=+0.19 σ=0.132
Epoche 14/100 | Total Loss:   2.60 (R²=+0.51, Policy:  2.58) | Val-R²=+0.33 | Policy-Val= 2.23 | v_pred μ=+0.19 σ=0.131
Epoche 15/100 | Total Loss:   2.57 (R²=+0.51, Policy:  2.55) | Val-R²=+0.34 | Policy-Val= 2.23 | v_pred μ=+0.19 σ=0.131
Epoche 16/100 | Total Loss:   2.54 (R²=+0.51, Policy:  2.53) | Val-R²=+0.34 | Policy-Val= 2.23 | v_pred μ=+0.19 σ=0.131
Epoche 17/100 | Total Loss:   2.52 (R²=+0.51, Policy:  2.50) | Val-R²=+0.34 | Policy-Val= 2.23 | v_pred μ=+0.19 σ=0.131
Epoche 18/100 | Total Loss:   2.50 (R²=+0.51, Policy:  2.49) | Val-R²=+0.34 | Policy-Val= 2.23 | v_pred μ=+0.19 σ=0.130
Epoche 19/100 | Total Loss:   2.48 (R²=+0.51, Policy:  2.47) | Val-R²=+0.34 | Policy-Val= 2.23 | v_pred μ=+0.19 σ=0.130
Epoche 20/100 | Total Loss:   2.47 (R²=+0.50, Policy:  2.45) | Val-R²=+0.34 | Policy-Val= 2.23 | v_pred μ=+0.19 σ=0.130
Epoche 21/100 | Total Loss:   2.46 (R²=+0.51, Policy:  2.44) | Val-R²=+0.33 | Policy-Val= 2.23 | v_pred μ=+0.19 σ=0.130
Epoche 22/100 | Total Loss:   2.44 (R²=+0.50, Policy:  2.43) | Val-R²=+0.34 | Policy-Val= 2.24 | v_pred μ=+0.19 σ=0.130
Epoche 23/100 | Total Loss:   2.43 (R²=+0.51, Policy:  2.41) | Val-R²=+0.34 | Policy-Val= 2.23 | v_pred μ=+0.19 σ=0.130
Epoche 24/100 | Total Loss:   2.42 (R²=+0.50, Policy:  2.41) | Val-R²=+0.34 | Policy-Val= 2.23 | v_pred μ=+0.19 σ=0.130
Epoche 25/100 | Total Loss:   2.41 (R²=+0.50, Policy:  2.40) | Val-R²=+0.34 | Policy-Val= 2.24 | v_pred μ=+0.19 σ=0.130
Epoche 26/100 | Total Loss:   2.41 (R²=+0.51, Policy:  2.39) | Val-R²=+0.34 | Policy-Val= 2.24 | v_pred μ=+0.19 σ=0.130
Epoche 27/100 | Total Loss:   2.40 (R²=+0.51, Policy:  2.38) | Val-R²=+0.34 | Policy-Val= 2.24 | v_pred μ=+0.19 σ=0.130
Epoche 28/100 | Total Loss:   2.39 (R²=+0.51, Policy:  2.37) | Val-R²=+0.35 | Policy-Val= 2.24 | v_pred μ=+0.19 σ=0.130
Epoche 29/100 | Total Loss:   2.38 (R²=+0.51, Policy:  2.36) | Val-R²=+0.34 | Policy-Val= 2.24 | v_pred μ=+0.19 σ=0.130
Epoche 30/100 | Total Loss:   2.38 (R²=+0.51, Policy:  2.36) | Val-R²=+0.34 | Policy-Val= 2.24 | v_pred μ=+0.19 σ=0.131
Epoche 31/100 | Total Loss:   2.37 (R²=+0.51, Policy:  2.35) | Val-R²=+0.34 | Policy-Val= 2.24 | v_pred μ=+0.19 σ=0.131
Epoche 32/100 | Total Loss:   2.36 (R²=+0.51, Policy:  2.35) | Val-R²=+0.34 | Policy-Val= 2.24 | v_pred μ=+0.19 σ=0.131
Epoche 33/100 | Total Loss:   2.36 (R²=+0.51, Policy:  2.34) | Val-R²=+0.35 | Policy-Val= 2.24 | v_pred μ=+0.19 σ=0.131
Epoche 34/100 | Total Loss:   2.35 (R²=+0.51, Policy:  2.34) | Val-R²=+0.34 | Policy-Val= 2.24 | v_pred μ=+0.19 σ=0.131
Epoche 35/100 | Total Loss:   2.35 (R²=+0.51, Policy:  2.33) | Val-R²=+0.35 | Policy-Val= 2.24 | v_pred μ=+0.19 σ=0.131
Epoche 36/100 | Total Loss:   2.34 (R²=+0.51, Policy:  2.33) | Val-R²=+0.35 | Policy-Val= 2.24 | v_pred μ=+0.19 σ=0.131
Epoche 37/100 | Total Loss:   2.34 (R²=+0.51, Policy:  2.32) | Val-R²=+0.34 | Policy-Val= 2.24 | v_pred μ=+0.19 σ=0.131
Epoche 38/100 | Total Loss:   2.33 (R²=+0.51, Policy:  2.32) | Val-R²=+0.35 | Policy-Val= 2.24 | v_pred μ=+0.19 σ=0.131
Epoche 39/100 | Total Loss:   2.33 (R²=+0.51, Policy:  2.31) | Val-R²=+0.35 | Policy-Val= 2.24 | v_pred μ=+0.19 σ=0.131
Epoche 40/100 | Total Loss:   2.33 (R²=+0.51, Policy:  2.31) | Val-R²=+0.34 | Policy-Val= 2.24 | v_pred μ=+0.19 σ=0.131
Epoche 41/100 | Total Loss:   2.32 (R²=+0.51, Policy:  2.31) | Val-R²=+0.34 | Policy-Val= 2.24 | v_pred μ=+0.19 σ=0.131  🟡 POLICY-PLATEAU
Epoche 42/100 | Total Loss:   2.32 (R²=+0.51, Policy:  2.30) | Val-R²=+0.34 | Policy-Val= 2.24 | v_pred μ=+0.19 σ=0.131  🟡 POLICY-PLATEAU
Epoche 43/100 | Total Loss:   2.32 (R²=+0.51, Policy:  2.30) | Val-R²=+0.34 | Policy-Val= 2.25 | v_pred μ=+0.19 σ=0.132  🟡 POLICY-PLATEAU
Epoche 44/100 | Total Loss:   2.31 (R²=+0.51, Policy:  2.29) | Val-R²=+0.34 | Policy-Val= 2.25 | v_pred μ=+0.19 σ=0.132  🟡 POLICY-PLATEAU
Epoche 45/100 | Total Loss:   2.31 (R²=+0.52, Policy:  2.29) | Val-R²=+0.35 | Policy-Val= 2.25 | v_pred μ=+0.19 σ=0.132  🟡 POLICY-PLATEAU
Epoche 46/100 | Total Loss:   2.30 (R²=+0.52, Policy:  2.29) | Val-R²=+0.35 | Policy-Val= 2.24 | v_pred μ=+0.19 σ=0.132  🟡 POLICY-PLATEAU

⏹️  Early Stopping: Policy plateaut seit Epoche 41 (5 Epochen ohne Fortschritt).

=======================================================
  PHASE 2: VALUE-KALIBRIERUNG (Trunk/Policy eingefroren)
───────────────────────────────────────────────────────
  Kalibrierung  1/50 | Val-R²=+0.348  (bislang bester: Epoche 1)
  Kalibrierung  2/50 | Val-R²=+0.349  (bislang bester: Epoche 1)
  Kalibrierung  3/50 | Val-R²=+0.344  (bislang bester: Epoche 1)
  Kalibrierung  4/50 | Val-R²=+0.344  (bislang bester: Epoche 1)
  Kalibrierung  5/50 | Val-R²=+0.339  (bislang bester: Epoche 1)
  Kalibrierung  6/50 | Val-R²=+0.341  (bislang bester: Epoche 1)
  Kalibrierung  7/50 | Val-R²=+0.339  (bislang bester: Epoche 1)
  Kalibrierung  8/50 | Val-R²=+0.343  (bislang bester: Epoche 1)
  Kalibrierung  9/50 | Val-R²=+0.338  (bislang bester: Epoche 1)
  ⏹️  Kalibrierung gestoppt: Val-R² seit Epoche 1 nicht mehr verbessert (Bestwert 0.348).
  ✅ Value-Head auf besten Kalibrierungs-Stand zurückgesetzt (Epoche 1, Val-R²=0.348).
=======================================================

=======================================================
  TRAINING SUMMARY
=======================================================
  Epochen:       100
  Züge:          1,501,066  (+167,036 Val, nie trainiert)
  Batches/Epoche:5863
───────────────────────────────────────────────────────
  Policy Loss:   2.2887 / 6.18 max  (37.0%)  🟡 Gut
  Policy Val-Loss: 2.2446  (Gap ggü. Train: -0.0441)
  Value Loss:    0.0165  (R²=0.51 ggü. Mittelwert-Baseline)  🟡 Gut
  Value Val-R²:  0.35  (Gap ggü. Train: +0.16)  🟡 spürbarer Train/Val-Abstand — im Auge behalten
───────────────────────────────────────────────────────
  ℹ️  Phase 1 Val-R² war in Epoche 1 am besten (0.39), danach Überfitten (normal — Value trainiert bewusst bis zum Ende mit).
  🎯 Phase 2 (Value-Kalibrierung): bester Stand nach Epoche 1, Val-R²=0.35 — Wert oben spiegelt diesen kalibrierten Value-Head wider.
  ⏹️  Early Stopping (Policy-Plateau) nach Epoche 46/100
  🟡 Plateau ab Epoche 41.
     → Für nächste Generation: mehr Sims im Self-Play.
=======================================================

=======================================================
  NETZAUSLASTUNG (Hidden Size: 512)
───────────────────────────────────────────────────────
  Schicht          Dead   Aktiv-Rate        Eff.Rank
  ───────────────────────────────────────────────────
  layer1     0/512 (0%)          41%   219/512 (43%)
  layer2     0/512 (0%)          41%   200/512 (39%)
  layer3    87/512 (17%)          11%   180/512 (35%)
  ───────────────────────────────────────────────────
  🟢 Gesunde Auslastung (Dead 6%, Rank 39%).
=======================================================

✅ Training beendet! Neues Model gespeichert unter:
📂 D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v1c.pth
📈 Loss-Verlauf gespeichert unter:
📂 D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v1c_loss.png
✅ Exportiert: D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v1c.onnx  (input=684, hidden=512, value_hidden=64, opset=13)
📎 Referenz für Rust-Parität: D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v1c.onnx.ref.txt

=======================================================
  STUFE 1 vs. STUFE 2 (max. 50 Spiele, 200 Sims, Early-Stop)
───────────────────────────────────────────────────────
🏟️ Mosaic-AI ARENA — Netz vs Netz (Rust) 🏟️
  v1c(Stufe1) (Brett 0, 200 Sims, c_puct=1.5, Stufe 1/DFS-Blatt) vs v1c(Stufe2) (Brett 1, 200 Sims, c_puct=1.5, Stufe 2/Netz-Value-Blatt) — 50 Spiele
--------------------------------------------------
  #  1/50:  18:32  -> v1c(Stufe2)            | Züge 161 | Strength 0.880 | Stand v1c(Stufe1) 0:1 v1c(Stufe2) | Elo 986/1014
  #  2/50:  14:9   -> v1c(Stufe1)            | Züge 151 | Strength 0.407 | Stand v1c(Stufe1) 1:1 v1c(Stufe2) | Elo 993/1007
  #  3/50:  52:17  -> v1c(Stufe1)            | Züge 153 | Strength 1.000 | Stand v1c(Stufe1) 2:1 v1c(Stufe2) | Elo 1010/990
  #  4/50:  36:14  -> v1c(Stufe1)            | Züge 163 | Strength 0.955 | Stand v1c(Stufe1) 3:1 v1c(Stufe2) | Elo 1024/976
  #  5/50:  36:43  -> v1c(Stufe2)            | Züge 160 | Strength 0.760 | Stand v1c(Stufe1) 3:2 v1c(Stufe2) | Elo 1010/990
  #  6/50:  30:3   -> v1c(Stufe1)            | Züge 152 | Strength 0.888 | Stand v1c(Stufe1) 4:2 v1c(Stufe2) | Elo 1023/977
  #  7/50:   6:0   -> v1c(Stufe1)            | Züge 151 | Strength 0.348 | Stand v1c(Stufe1) 5:2 v1c(Stufe2) | Elo 1028/972
  #  8/50:  28:11  -> v1c(Stufe1)            | Züge 156 | Strength 0.865 | Stand v1c(Stufe1) 6:2 v1c(Stufe2) | Elo 1040/960
  #  9/50:  21:0   -> v1c(Stufe1)            | Züge 157 | Strength 0.786 | Stand v1c(Stufe1) 7:2 v1c(Stufe2) | Elo 1050/950
  # 10/50:  26:29  -> v1c(Stufe2)            | Züge 164 | Strength 0.516 | Stand v1c(Stufe1) 7:3 v1c(Stufe2) | Elo 1039/961
  # 11/50:  36:19  -> v1c(Stufe1)            | Züge 159 | Strength 0.955 | Stand v1c(Stufe1) 8:3 v1c(Stufe2) | Elo 1051/949
  # 12/50:  36:46  -> v1c(Stufe2)            | Züge 155 | Strength 0.850 | Stand v1c(Stufe1) 8:4 v1c(Stufe2) | Elo 1034/966
  # 13/50:  38:19  -> v1c(Stufe1)            | Züge 160 | Strength 0.978 | Stand v1c(Stufe1) 9:4 v1c(Stufe2) | Elo 1047/953
  # 14/50:  43:26  -> v1c(Stufe1)            | Züge 163 | Strength 1.000 | Stand v1c(Stufe1) 10:4 v1c(Stufe2) | Elo 1059/941
  # 15/50:   0:0   -> v1c(Stufe2)            | Züge 151 | Strength 0.100 | Stand v1c(Stufe1) 10:5 v1c(Stufe2) | Elo 1057/943
  # 16/50:   5:0   -> v1c(Stufe1)            | Züge 158 | Strength 0.306 | Stand v1c(Stufe1) 11:5 v1c(Stufe2) | Elo 1060/940
  # 17/50:  28:45  -> v1c(Stufe2)            | Züge 160 | Strength 1.000 | Stand v1c(Stufe1) 11:6 v1c(Stufe2) | Elo 1039/961
  # 18/50:  41:8   -> v1c(Stufe1)            | Züge 154 | Strength 1.000 | Stand v1c(Stufe1) 12:6 v1c(Stufe2) | Elo 1051/949
  # 19/50:  33:32  -> v1c(Stufe1)            | Züge 157 | Strength 0.501 | Stand v1c(Stufe1) 13:6 v1c(Stufe2) | Elo 1057/943
  # 20/50:  29:7   -> v1c(Stufe1)            | Züge 161 | Strength 0.876 | Stand v1c(Stufe1) 14:6 v1c(Stufe2) | Elo 1067/933
  # 21/50:  32:9   -> v1c(Stufe1)            | Züge 160 | Strength 0.910 | Stand v1c(Stufe1) 15:6 v1c(Stufe2) | Elo 1076/924
  ⏹️  Vorzeitig entschieden: v1c(Stufe1) hat nach 21 Spielen bereits 15 Siege (95%-Signifikanz für >50% Gewinnchance).
--------------------------------------------------
🏆 ERGEBNIS: v1c(Stufe1) 15:6 v1c(Stufe2) (71% A-Siege) in 391.7s (0.1 Spiele/s)  [vorzeitig nach 21/50 Spielen]
   Ø Score: v1c(Stufe1) 28.0 | v1c(Stufe2) 17.6
   0:0-Spiele: 1/21 (4.8%)
   Elo: v1c(Stufe1) 1076 | v1c(Stufe2) 924
=======================================================
```

**Arena vs. Heuristik**

```
PS D:\Archiv\Documents\Projekte\mosaic-AI> python arena.py
🏟️ Mosaic-AI ARENA — Netz vs Heuristik (Rust) 🏟️
  v1c (Brett 0, 200 Sims, Stufe 1/DFS-Blatt) vs Heuristik(s200) (Brett 1, 200 Sims) — 100 Spiele  [SPRT p1=0.64, α=0.05, β=0.1]
--------------------------------------------------
  #  1/100:  32:48  -> Heuristik(s200)          | Züge 166 | LLR_Netz -0.33 | LLR_Heur +0.25 | ΔElo~-120 | Stand Netz 0:1 Heur | Elo 984/1016
  #  2/100:  44:32  -> v1c                      | Züge 167 | LLR_Netz -0.08 | LLR_Heur -0.08 | ΔElo~-0 | Stand Netz 1:1 Heur | Elo 1001/999
  #  3/100:  33:42  -> Heuristik(s200)          | Züge 158 | LLR_Netz -0.41 | LLR_Heur +0.17 | ΔElo~-70 | Stand Netz 1:2 Heur | Elo 985/1015
  #  4/100:  23:12  -> v1c                      | Züge 164 | LLR_Netz -0.16 | LLR_Heur -0.16 | ΔElo~-0 | Stand Netz 2:2 Heur | Elo 1002/998
  #  5/100:  30:26  -> v1c                      | Züge 157 | LLR_Netz +0.08 | LLR_Heur -0.49 | ΔElo~+50 | Stand Netz 3:2 Heur | Elo 1018/982
  #  6/100:  25:45  -> Heuristik(s200)          | Züge 160 | LLR_Netz -0.24 | LLR_Heur -0.24 | ΔElo~-0 | Stand Netz 3:3 Heur | Elo 1000/1000
  #  7/100:  44:60  -> Heuristik(s200)          | Züge 162 | LLR_Netz -0.57 | LLR_Heur +0.00 | ΔElo~-39 | Stand Netz 3:4 Heur | Elo 984/1016
  #  8/100:  50:33  -> v1c                      | Züge 156 | LLR_Netz -0.33 | LLR_Heur -0.33 | ΔElo~-0 | Stand Netz 4:4 Heur | Elo 1001/999
  #  9/100:  22:57  -> Heuristik(s200)          | Züge 158 | LLR_Netz -0.66 | LLR_Heur -0.08 | ΔElo~-32 | Stand Netz 4:5 Heur | Elo 985/1015
  # 10/100:  58:54  -> v1c                      | Züge 159 | LLR_Netz -0.41 | LLR_Heur -0.41 | ΔElo~-0 | Stand Netz 5:5 Heur | Elo 1002/998
  # 11/100:  33:46  -> Heuristik(s200)          | Züge 162 | LLR_Netz -0.74 | LLR_Heur -0.16 | ΔElo~-27 | Stand Netz 5:6 Heur | Elo 986/1014
  # 12/100:  24:13  -> v1c                      | Züge 162 | LLR_Netz -0.49 | LLR_Heur -0.49 | ΔElo~-0 | Stand Netz 6:6 Heur | Elo 1003/997
  # 13/100:   0:25  -> Heuristik(s200)          | Züge 162 | LLR_Netz -0.82 | LLR_Heur -0.24 | ΔElo~-23 | Stand Netz 6:7 Heur | Elo 987/1013
  # 14/100:  25:49  -> Heuristik(s200)          | Züge 162 | LLR_Netz -1.15 | LLR_Heur +0.00 | ΔElo~-44 | Stand Netz 6:8 Heur | Elo 972/1028
  # 15/100:  39:63  -> Heuristik(s200)          | Züge 160 | LLR_Netz -1.48 | LLR_Heur +0.25 | ΔElo~-62 | Stand Netz 6:9 Heur | Elo 959/1041
  # 16/100:  50:70  -> Heuristik(s200)          | Züge 168 | LLR_Netz -1.80 | LLR_Heur +0.50 | ΔElo~-79 | Stand Netz 6:10 Heur | Elo 947/1053
  # 17/100:   6:35  -> Heuristik(s200)          | Züge 164 | LLR_Netz -2.13 | LLR_Heur +0.74 | ΔElo~-94 | Stand Netz 6:11 Heur | Elo 936/1064
  # 18/100:  43:29  -> v1c                      | Züge 163 | LLR_Netz -1.89 | LLR_Heur +0.42 | ΔElo~-70 | Stand Netz 7:11 Heur | Elo 958/1042
  # 19/100:  30:26  -> v1c                      | Züge 155 | LLR_Netz -1.64 | LLR_Heur +0.09 | ΔElo~-50 | Stand Netz 8:11 Heur | Elo 978/1022
  # 20/100:  11:44  -> Heuristik(s200)          | Züge 168 | LLR_Netz -1.97 | LLR_Heur +0.33 | ΔElo~-64 | Stand Netz 8:12 Heur | Elo 964/1036
  # 21/100:  68:57  -> v1c                      | Züge 166 | LLR_Netz -1.72 | LLR_Heur +0.01 | ΔElo~-46 | Stand Netz 9:12 Heur | Elo 983/1017
  # 22/100:  58:43  -> v1c                      | Züge 163 | LLR_Netz -1.47 | LLR_Heur -0.32 | ΔElo~-29 | Stand Netz 10:12 Heur | Elo 1001/999
  # 23/100:  29:37  -> Heuristik(s200)          | Züge 167 | LLR_Netz -1.80 | LLR_Heur -0.08 | ΔElo~-42 | Stand Netz 10:13 Heur | Elo 985/1015
  # 24/100:   9:45  -> Heuristik(s200)          | Züge 157 | LLR_Netz -2.13 | LLR_Heur +0.17 | ΔElo~-54 | Stand Netz 10:14 Heur | Elo 970/1030
  # 25/100:  48:49  -> Heuristik(s200)          | Züge 159 | LLR_Netz -2.46 | LLR_Heur +0.42 | ΔElo~-65 | Stand Netz 10:15 Heur | Elo 957/1043
  # 26/100:  30:41  -> Heuristik(s200)          | Züge 166 | LLR_Netz -2.46 | LLR_Heur +0.66 | ΔElo~-76 | Stand Netz 10:16 Heur | Elo 945/1055
  # 27/100:  27:40  -> Heuristik(s200)          | Züge 162 | LLR_Netz -2.46 | LLR_Heur +0.91 | ΔElo~-86 | Stand Netz 10:17 Heur | Elo 934/1066
  # 28/100:   8:32  -> Heuristik(s200)          | Züge 160 | LLR_Netz -2.46 | LLR_Heur +1.16 | ΔElo~-95 | Stand Netz 10:18 Heur | Elo 924/1076
  # 29/100:  60:86  -> Heuristik(s200)          | Züge 154 | LLR_Netz -2.46 | LLR_Heur +1.41 | ΔElo~-104 | Stand Netz 10:19 Heur | Elo 915/1085
  # 30/100:  27:66  -> Heuristik(s200)          | Züge 161 | LLR_Netz -2.46 | LLR_Heur +1.65 | ΔElo~-112 | Stand Netz 10:20 Heur | Elo 906/1094
  # 31/100:  26:22  -> v1c                      | Züge 160 | LLR_Netz -2.46 | LLR_Heur +1.32 | ΔElo~-97 | Stand Netz 11:20 Heur | Elo 930/1070
  # 32/100:  59:50  -> v1c                      | Züge 164 | LLR_Netz -2.46 | LLR_Heur +1.00 | ΔElo~-83 | Stand Netz 12:20 Heur | Elo 952/1048
  # 33/100:  32:48  -> Heuristik(s200)          | Züge 164 | LLR_Netz -2.46 | LLR_Heur +1.24 | ΔElo~-91 | Stand Netz 12:21 Heur | Elo 940/1060
  # 34/100:  47:41  -> v1c                      | Züge 168 | LLR_Netz -2.46 | LLR_Heur +0.91 | ΔElo~-79 | Stand Netz 13:21 Heur | Elo 961/1039
  # 35/100:  34:57  -> Heuristik(s200)          | Züge 164 | LLR_Netz -2.46 | LLR_Heur +1.16 | ΔElo~-86 | Stand Netz 13:22 Heur | Elo 949/1051
  # 36/100:  34:54  -> Heuristik(s200)          | Züge 165 | LLR_Netz -2.46 | LLR_Heur +1.41 | ΔElo~-94 | Stand Netz 13:23 Heur | Elo 938/1062
  # 37/100:  47:35  -> v1c                      | Züge 161 | LLR_Netz -2.46 | LLR_Heur +1.08 | ΔElo~-82 | Stand Netz 14:23 Heur | Elo 959/1041
  # 38/100:  12:28  -> Heuristik(s200)          | Züge 161 | LLR_Netz -2.46 | LLR_Heur +1.33 | ΔElo~-89 | Stand Netz 14:24 Heur | Elo 947/1053
  # 39/100:   9:30  -> Heuristik(s200)          | Züge 161 | LLR_Netz -2.46 | LLR_Heur +1.57 | ΔElo~-96 | Stand Netz 14:25 Heur | Elo 936/1064
  # 40/100:  32:77  -> Heuristik(s200)          | Züge 162 | LLR_Netz -2.46 | LLR_Heur +1.82 | ΔElo~-102 | Stand Netz 14:26 Heur | Elo 926/1074
  # 41/100:  37:71  -> Heuristik(s200)          | Züge 162 | LLR_Netz -2.46 | LLR_Heur +2.07 | ΔElo~-108 | Stand Netz 14:27 Heur | Elo 916/1084
  # 42/100:  45:40  -> v1c                      | Züge 154 | LLR_Netz -2.46 | LLR_Heur +1.74 | ΔElo~-97 | Stand Netz 15:27 Heur | Elo 939/1061
  # 43/100:  45:21  -> v1c                      | Züge 150 | LLR_Netz -2.46 | LLR_Heur +1.41 | ΔElo~-87 | Stand Netz 16:27 Heur | Elo 960/1040
  # 44/100:  19:28  -> Heuristik(s200)          | Züge 156 | LLR_Netz -2.46 | LLR_Heur +1.66 | ΔElo~-93 | Stand Netz 16:28 Heur | Elo 948/1052
  # 45/100:  29:29  -> Heuristik(s200)          | Züge 161 | LLR_Netz -2.46 | LLR_Heur +1.90 | ΔElo~-99 | Stand Netz 16:29 Heur | Elo 937/1063
  # 46/100:  43:59  -> Heuristik(s200)          | Züge 157 | LLR_Netz -2.46 | LLR_Heur +2.15 | ΔElo~-104 | Stand Netz 16:30 Heur | Elo 927/1073
  # 47/100:  32:51  -> Heuristik(s200)          | Züge 157 | LLR_Netz -2.46 | LLR_Heur +2.40 | ΔElo~-110 | Stand Netz 16:31 Heur | Elo 917/1083
  # 48/100:  42:39  -> v1c                      | Züge 158 | LLR_Netz -2.46 | LLR_Heur +2.07 | ΔElo~-100 | Stand Netz 17:31 Heur | Elo 940/1060
  # 49/100:  43:48  -> Heuristik(s200)          | Züge 156 | LLR_Netz -2.46 | LLR_Heur +2.31 | ΔElo~-105 | Stand Netz 17:32 Heur | Elo 929/1071
  # 50/100:  11:55  -> Heuristik(s200)          | Züge 165 | LLR_Netz -2.46 | LLR_Heur +2.56 | ΔElo~-110 | Stand Netz 17:33 Heur | Elo 919/1081
  # 51/100:  48:58  -> Heuristik(s200)          | Züge 165 | LLR_Netz -2.46 | LLR_Heur +2.81 | ΔElo~-116 | Stand Netz 17:34 Heur | Elo 910/1090
  # 52/100:   6:40  -> Heuristik(s200)          | Züge 159 | LLR_Netz -2.46 | LLR_Heur +3.06 | ΔElo~-120 | Stand Netz 17:35 Heur | Elo 902/1098
  ⏹️  SPRT-Entscheid nach 52 Spielen: Heuristik(s200) signifikant staerker (LLR_Netz=-2.46, LLR_Heur=+3.06).
--------------------------------------------------
🏆 ERGEBNIS: v1c 17:35 Heuristik(s200) (33% Netz-Siege) in 1045.1s (0.0 Spiele/s)  [vorzeitig nach 52/100 Spielen]
   Ø Score: v1c 33.0 | Heuristik(s200) 44.0
   0:0-Spiele: 0/52 (0.0%)  (Sauberkeits-Indikator)
   Ø Floor-Strafe: v1c 16.1 | Heuristik(s200) 10.8
   Elo: v1c 902 | Heuristik(s200) 1098
```
