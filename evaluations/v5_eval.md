trainiert mit

- --games 1000 --mode mcts --sims 400
- --games 1000 --mode network --sims 400 --version v1c --stage 1
- --games 6000 --mode network --sims 400 --version v2 --stage 1
- --games 2000 --mode network --sims 400 --version v2 --stage 1
- --games 2000 --mode network --sims 400 --version v2 --stage 1
- --games 1400 --mode network --sims 400 --version v2_eval --stage 1
- --load v2

**Netzdaten**

```
PS D:\Archiv\Documents\Projekte\mosaic-AI> python train.py --name v5 --epochs 100 --load v2
Lade Daten aus 1206 Dateien...
Datensatz geladen: 1808739 Züge. (Features pro Zug: 684) — 881.7s
💾 Speichere HDF5-Cache...
✅ Cache gespeichert: D:\Archiv\Documents\Projekte\mosaic-AI\data\.cache_009d9f82b2db.h5
Lade Daten aus 134 Dateien...
Datensatz geladen: 200915 Züge. (Features pro Zug: 684) — 103.3s
💾 Speichere HDF5-Cache...
✅ Cache gespeichert: D:\Archiv\Documents\Projekte\mosaic-AI\data\.cache_00f82fc23d7a.h5
   Val-Split: 1206 Trainings-Dateien / 134 Val-Dateien (1,808,739 / 200,915 Züge)
   Value-Ziel-Streuung: σ=0.160 (Varianz=0.0257, zum Vergleich mit v_pred σ unten; Varianz ist die Baseline-MSE bei reiner Mittelwert-Vorhersage)

🚀 Starte PyTorch Training auf: CUDA
🧠 Netz-Architektur: 684→512→512→512
⚙️  Hyperparameter (config.py):
   Learning Rate : 0.0004
   Value Weight  : 1
   Batch Size    : 256
   Value-Target  : tanh(eigen/50) - 0.1*tanh(gegner/50) (Endergebnis statt Win/Loss)
📥 Lade altes Model als Startpunkt: alphazero_v2.pth
   Epochen       : 100
🔄 Warm-Start erkannt: Trainiere für 100 Epochen.
Epoche  1/100 | Total Loss:   3.00 (R²=+0.37, Policy:  2.98) | Val-R²=+0.39 | Policy-Val= 2.17 | v_pred μ=+0.14 σ=0.098
Epoche  2/100 | Total Loss:   2.96 (R²=+0.39, Policy:  2.95) | Val-R²=+0.40 | Policy-Val= 2.18 | v_pred μ=+0.14 σ=0.100
Epoche  3/100 | Total Loss:   2.95 (R²=+0.40, Policy:  2.94) | Val-R²=+0.40 | Policy-Val= 2.18 | v_pred μ=+0.14 σ=0.102
Epoche  4/100 | Total Loss:   2.94 (R²=+0.41, Policy:  2.92) | Val-R²=+0.40 | Policy-Val= 2.18 | v_pred μ=+0.14 σ=0.103
Epoche  5/100 | Total Loss:   2.92 (R²=+0.41, Policy:  2.91) | Val-R²=+0.39 | Policy-Val= 2.18 | v_pred μ=+0.14 σ=0.103
Epoche  6/100 | Total Loss:   2.90 (R²=+0.42, Policy:  2.89) | Val-R²=+0.39 | Policy-Val= 2.18 | v_pred μ=+0.14 σ=0.104
Epoche  7/100 | Total Loss:   2.88 (R²=+0.42, Policy:  2.87) | Val-R²=+0.39 | Policy-Val= 2.19 | v_pred μ=+0.14 σ=0.104
Epoche  8/100 | Total Loss:   2.86 (R²=+0.42, Policy:  2.85) | Val-R²=+0.39 | Policy-Val= 2.19 | v_pred μ=+0.14 σ=0.104
Epoche  9/100 | Total Loss:   2.84 (R²=+0.42, Policy:  2.83) | Val-R²=+0.39 | Policy-Val= 2.19 | v_pred μ=+0.14 σ=0.104
Epoche 10/100 | Total Loss:   2.83 (R²=+0.42, Policy:  2.81) | Val-R²=+0.39 | Policy-Val= 2.19 | v_pred μ=+0.14 σ=0.105
Epoche 11/100 | Total Loss:   2.81 (R²=+0.42, Policy:  2.79) | Val-R²=+0.39 | Policy-Val= 2.19 | v_pred μ=+0.14 σ=0.105
Epoche 12/100 | Total Loss:   2.79 (R²=+0.42, Policy:  2.78) | Val-R²=+0.38 | Policy-Val= 2.19 | v_pred μ=+0.14 σ=0.105
Epoche 13/100 | Total Loss:   2.77 (R²=+0.42, Policy:  2.76) | Val-R²=+0.38 | Policy-Val= 2.19 | v_pred μ=+0.14 σ=0.105
Epoche 14/100 | Total Loss:   2.76 (R²=+0.42, Policy:  2.74) | Val-R²=+0.38 | Policy-Val= 2.19 | v_pred μ=+0.14 σ=0.105
Epoche 15/100 | Total Loss:   2.74 (R²=+0.42, Policy:  2.73) | Val-R²=+0.38 | Policy-Val= 2.19 | v_pred μ=+0.14 σ=0.105
Epoche 16/100 | Total Loss:   2.73 (R²=+0.43, Policy:  2.71) | Val-R²=+0.38 | Policy-Val= 2.19 | v_pred μ=+0.14 σ=0.105
Epoche 17/100 | Total Loss:   2.71 (R²=+0.43, Policy:  2.70) | Val-R²=+0.38 | Policy-Val= 2.19 | v_pred μ=+0.14 σ=0.105
Epoche 18/100 | Total Loss:   2.70 (R²=+0.43, Policy:  2.68) | Val-R²=+0.38 | Policy-Val= 2.19 | v_pred μ=+0.14 σ=0.105
Epoche 19/100 | Total Loss:   2.69 (R²=+0.43, Policy:  2.67) | Val-R²=+0.38 | Policy-Val= 2.19 | v_pred μ=+0.14 σ=0.105
Epoche 20/100 | Total Loss:   2.67 (R²=+0.43, Policy:  2.66) | Val-R²=+0.38 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.105
Epoche 21/100 | Total Loss:   2.66 (R²=+0.43, Policy:  2.65) | Val-R²=+0.37 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.105
Epoche 22/100 | Total Loss:   2.65 (R²=+0.43, Policy:  2.64) | Val-R²=+0.38 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.106
Epoche 23/100 | Total Loss:   2.64 (R²=+0.43, Policy:  2.62) | Val-R²=+0.38 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.106
Epoche 24/100 | Total Loss:   2.63 (R²=+0.43, Policy:  2.61) | Val-R²=+0.38 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.106
Epoche 25/100 | Total Loss:   2.62 (R²=+0.43, Policy:  2.60) | Val-R²=+0.37 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.106
Epoche 26/100 | Total Loss:   2.61 (R²=+0.43, Policy:  2.59) | Val-R²=+0.37 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.106
Epoche 27/100 | Total Loss:   2.60 (R²=+0.43, Policy:  2.58) | Val-R²=+0.37 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.106
Epoche 28/100 | Total Loss:   2.59 (R²=+0.43, Policy:  2.58) | Val-R²=+0.38 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.106
Epoche 29/100 | Total Loss:   2.58 (R²=+0.43, Policy:  2.56) | Val-R²=+0.37 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.106
Epoche 30/100 | Total Loss:   2.57 (R²=+0.43, Policy:  2.55) | Val-R²=+0.38 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.106
Epoche 31/100 | Total Loss:   2.56 (R²=+0.43, Policy:  2.55) | Val-R²=+0.38 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.106
Epoche 32/100 | Total Loss:   2.56 (R²=+0.43, Policy:  2.54) | Val-R²=+0.38 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.106
Epoche 33/100 | Total Loss:   2.55 (R²=+0.43, Policy:  2.53) | Val-R²=+0.37 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.106
Epoche 34/100 | Total Loss:   2.54 (R²=+0.43, Policy:  2.53) | Val-R²=+0.37 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.106
Epoche 35/100 | Total Loss:   2.53 (R²=+0.43, Policy:  2.52) | Val-R²=+0.38 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.106
Epoche 36/100 | Total Loss:   2.53 (R²=+0.43, Policy:  2.51) | Val-R²=+0.37 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.106
Epoche 37/100 | Total Loss:   2.52 (R²=+0.43, Policy:  2.50) | Val-R²=+0.38 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.106
Epoche 38/100 | Total Loss:   2.51 (R²=+0.43, Policy:  2.50) | Val-R²=+0.37 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.106
Epoche 39/100 | Total Loss:   2.51 (R²=+0.43, Policy:  2.49) | Val-R²=+0.37 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.106
Epoche 40/100 | Total Loss:   2.50 (R²=+0.43, Policy:  2.49) | Val-R²=+0.37 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.106
Epoche 41/100 | Total Loss:   2.50 (R²=+0.43, Policy:  2.48) | Val-R²=+0.37 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.106
Epoche 42/100 | Total Loss:   2.49 (R²=+0.43, Policy:  2.48) | Val-R²=+0.37 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.106
Epoche 43/100 | Total Loss:   2.49 (R²=+0.43, Policy:  2.47) | Val-R²=+0.36 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.106
Epoche 44/100 | Total Loss:   2.48 (R²=+0.43, Policy:  2.47) | Val-R²=+0.37 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.106
Epoche 45/100 | Total Loss:   2.48 (R²=+0.43, Policy:  2.46) | Val-R²=+0.37 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.106
Epoche 46/100 | Total Loss:   2.47 (R²=+0.43, Policy:  2.46) | Val-R²=+0.37 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.106
Epoche 47/100 | Total Loss:   2.47 (R²=+0.43, Policy:  2.45) | Val-R²=+0.37 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.106
Epoche 48/100 | Total Loss:   2.46 (R²=+0.44, Policy:  2.45) | Val-R²=+0.37 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.107
Epoche 49/100 | Total Loss:   2.46 (R²=+0.44, Policy:  2.44) | Val-R²=+0.37 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.107
Epoche 50/100 | Total Loss:   2.45 (R²=+0.44, Policy:  2.44) | Val-R²=+0.37 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.107  🟡 POLICY-PLATEAU
Epoche 51/100 | Total Loss:   2.45 (R²=+0.44, Policy:  2.43) | Val-R²=+0.38 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.107  🟡 POLICY-PLATEAU
Epoche 52/100 | Total Loss:   2.45 (R²=+0.44, Policy:  2.43) | Val-R²=+0.37 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.107  🟡 POLICY-PLATEAU
Epoche 53/100 | Total Loss:   2.44 (R²=+0.44, Policy:  2.43) | Val-R²=+0.37 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.107  🟡 POLICY-PLATEAU
Epoche 54/100 | Total Loss:   2.44 (R²=+0.44, Policy:  2.43) | Val-R²=+0.37 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.107  🟡 POLICY-PLATEAU
Epoche 55/100 | Total Loss:   2.44 (R²=+0.44, Policy:  2.42) | Val-R²=+0.37 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.107  🟡 POLICY-PLATEAU

⏹️  Early Stopping: Policy plateaut seit Epoche 50 (5 Epochen ohne Fortschritt).

=======================================================
  PHASE 2: VALUE-KALIBRIERUNG (Trunk/Policy eingefroren)
───────────────────────────────────────────────────────
  Kalibrierung  1/50 | Val-R²=+0.357  (bislang bester: Epoche 1)
  Kalibrierung  2/50 | Val-R²=+0.388  (bislang bester: Epoche 2)
  Kalibrierung  3/50 | Val-R²=+0.385  (bislang bester: Epoche 2)
  Kalibrierung  4/50 | Val-R²=+0.380  (bislang bester: Epoche 2)
  Kalibrierung  5/50 | Val-R²=+0.378  (bislang bester: Epoche 2)
  Kalibrierung  6/50 | Val-R²=+0.374  (bislang bester: Epoche 2)
  Kalibrierung  7/50 | Val-R²=+0.376  (bislang bester: Epoche 2)
  Kalibrierung  8/50 | Val-R²=+0.372  (bislang bester: Epoche 2)
  Kalibrierung  9/50 | Val-R²=+0.372  (bislang bester: Epoche 2)
  Kalibrierung 10/50 | Val-R²=+0.370  (bislang bester: Epoche 2)
  ⏹️  Kalibrierung gestoppt: Val-R² seit Epoche 2 nicht mehr verbessert (Bestwert 0.388).
  ✅ Value-Head auf besten Kalibrierungs-Stand zurückgesetzt (Epoche 2, Val-R²=0.388).
=======================================================

=======================================================
  TRAINING SUMMARY
=======================================================
  Epochen:       100
  Züge:          1,808,739  (+200,915 Val, nie trainiert)
  Batches/Epoche:7065
───────────────────────────────────────────────────────
  Policy Loss:   2.4224 / 6.18 max  (39.2%)  🟡 Gut
  Policy Val-Loss: 2.2014  (Gap ggü. Train: -0.2210)
  Value Loss:    0.0150  (R²=0.42 ggü. Mittelwert-Baseline)  🟡 Gut
  Value Val-R²:  0.39  (Gap ggü. Train: +0.03)  🟢 Train/Val nah beieinander
───────────────────────────────────────────────────────
  ℹ️  Phase 1 Val-R² war in Epoche 2 am besten (0.40), danach Überfitten (normal — Value trainiert bewusst bis zum Ende mit).
  🎯 Phase 2 (Value-Kalibrierung): bester Stand nach Epoche 2, Val-R²=0.39 — Wert oben spiegelt diesen kalibrierten Value-Head wider.
  ⏹️  Early Stopping (Policy-Plateau) nach Epoche 55/100
  🟡 Plateau ab Epoche 50.
     → Für nächste Generation: mehr Sims im Self-Play.
=======================================================

=======================================================
  NETZAUSLASTUNG (Hidden Size: 512)
───────────────────────────────────────────────────────
  Schicht          Dead   Aktiv-Rate        Eff.Rank
  ───────────────────────────────────────────────────
  layer1     0/512 (0%)          40%   219/512 (43%)
  layer2     0/512 (0%)          41%   200/512 (39%)
  layer3    67/512 (13%)          15%   161/512 (32%)
  ───────────────────────────────────────────────────
  🟢 Gesunde Auslastung (Dead 4%, Rank 38%).
=======================================================

✅ Training beendet! Neues Model gespeichert unter:
📂 D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v5.pth
📈 Loss-Verlauf gespeichert unter:
📂 D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v5_loss.png
✅ Exportiert: D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v5.onnx  (input=684, hidden=512, value_hidden=64, opset=13)
📎 Referenz für Rust-Parität: D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v5.onnx.ref.txt

=======================================================
  STUFE 1 vs. STUFE 2 (max. 100 Spiele, 200 Sims, Early-Stop)
───────────────────────────────────────────────────────
🏟️ Mosaic-AI ARENA — Netz vs Netz (Rust) 🏟️
  v5(Stufe1) (Brett 0, 200 Sims, c_puct=1.5, Stufe 1/DFS-Blatt) vs v5(Stufe2) (Brett 1, 200 Sims, c_puct=1.5, Stufe 2/Netz-Value-Blatt) — 100 Spiele  [SPRT p1=0.64, α=0.05, β=0.1]
--------------------------------------------------
  #  1/100:  28:0   -> v5(Stufe1)             | Züge 158 | LLR_A +0.25 | LLR_B -0.33 | ΔElo~+120 | Stand v5(Stufe1) 1:0 v5(Stufe2) | Elo 1016/984
  #  2/100:  31:17  -> v5(Stufe1)             | Züge 167 | LLR_A +0.49 | LLR_B -0.66 | ΔElo~+191 | Stand v5(Stufe1) 2:0 v5(Stufe2) | Elo 1031/969
  #  3/100:  44:11  -> v5(Stufe1)             | Züge 154 | LLR_A +0.74 | LLR_B -0.99 | ΔElo~+241 | Stand v5(Stufe1) 3:0 v5(Stufe2) | Elo 1044/956
  #  4/100:  42:13  -> v5(Stufe1)             | Züge 154 | LLR_A +0.99 | LLR_B -1.31 | ΔElo~+280 | Stand v5(Stufe1) 4:0 v5(Stufe2) | Elo 1056/944
  #  5/100:  37:30  -> v5(Stufe1)             | Züge 164 | LLR_A +1.23 | LLR_B -1.64 | ΔElo~+311 | Stand v5(Stufe1) 5:0 v5(Stufe2) | Elo 1067/933
  #  6/100:  32:0   -> v5(Stufe1)             | Züge 160 | LLR_A +1.48 | LLR_B -1.97 | ΔElo~+338 | Stand v5(Stufe1) 6:0 v5(Stufe2) | Elo 1077/923
  #  7/100:  36:0   -> v5(Stufe1)             | Züge 161 | LLR_A +1.73 | LLR_B -2.30 | ΔElo~+361 | Stand v5(Stufe1) 7:0 v5(Stufe2) | Elo 1086/914
  #  8/100:  43:17  -> v5(Stufe1)             | Züge 152 | LLR_A +1.97 | LLR_B -2.30 | ΔElo~+382 | Stand v5(Stufe1) 8:0 v5(Stufe2) | Elo 1095/905
  #  9/100:  10:0   -> v5(Stufe1)             | Züge 149 | LLR_A +2.22 | LLR_B -2.30 | ΔElo~+400 | Stand v5(Stufe1) 9:0 v5(Stufe2) | Elo 1103/897
  # 10/100:  39:7   -> v5(Stufe1)             | Züge 159 | LLR_A +2.47 | LLR_B -2.30 | ΔElo~+417 | Stand v5(Stufe1) 10:0 v5(Stufe2) | Elo 1110/890
  # 11/100:  17:27  -> v5(Stufe2)             | Züge 158 | LLR_A +2.14 | LLR_B -2.30 | ΔElo~+296 | Stand v5(Stufe1) 10:1 v5(Stufe2) | Elo 1085/915
  # 12/100:  36:24  -> v5(Stufe1)             | Züge 156 | LLR_A +2.39 | LLR_B -2.30 | ΔElo~+311 | Stand v5(Stufe1) 11:1 v5(Stufe2) | Elo 1094/906
  # 13/100:  59:27  -> v5(Stufe1)             | Züge 163 | LLR_A +2.63 | LLR_B -2.30 | ΔElo~+325 | Stand v5(Stufe1) 12:1 v5(Stufe2) | Elo 1102/898
  # 14/100:  63:27  -> v5(Stufe1)             | Züge 157 | LLR_A +2.88 | LLR_B -2.30 | ΔElo~+338 | Stand v5(Stufe1) 13:1 v5(Stufe2) | Elo 1110/890
  # 15/100:  39:0   -> v5(Stufe1)             | Züge 168 | LLR_A +3.13 | LLR_B -2.30 | ΔElo~+350 | Stand v5(Stufe1) 14:1 v5(Stufe2) | Elo 1117/883
  ⏹️  SPRT-Entscheid nach 15 Spielen: v5(Stufe1) signifikant staerker (LLR_A=+3.13, LLR_B=-2.30).
--------------------------------------------------
🏆 ERGEBNIS: v5(Stufe1) 14:1 v5(Stufe2) (93% A-Siege) in 264.9s (0.1 Spiele/s)  [vorzeitig nach 15/100 Spielen]
   Ø Score: v5(Stufe1) 37.1 | v5(Stufe2) 13.3
   0:0-Spiele: 0/15 (0.0%)
   Elo: v5(Stufe1) 1117 | v5(Stufe2) 883
=======================================================
```

**Arena vs. v2**

```
🏟️ Mosaic-AI ARENA — Netz vs Netz (Rust) 🏟️
  v5 (Brett 0, 200 Sims, c_puct=1.5, Stufe 1/DFS-Blatt) vs v2 (Brett 1, 200 Sims, c_puct=1.5, Stufe 1/DFS-Blatt) — 100 Spiele  [SPRT p1=0.64, α=0.05, β=0.1]
--------------------------------------------------
  #  1/100:  32:38  -> v2                     | Züge 162 | LLR_A -0.33 | LLR_B +0.25 | ΔElo~-120 | Stand v5 0:1 v2 | Elo 984/1016
  #  2/100:  40:25  -> v5                     | Züge 162 | LLR_A -0.08 | LLR_B -0.08 | ΔElo~-0 | Stand v5 1:1 v2 | Elo 1001/999
  #  3/100:  21:27  -> v2                     | Züge 161 | LLR_A -0.41 | LLR_B +0.17 | ΔElo~-70 | Stand v5 1:2 v2 | Elo 985/1015
  #  4/100:  52:23  -> v5                     | Züge 167 | LLR_A -0.16 | LLR_B -0.16 | ΔElo~-0 | Stand v5 2:2 v2 | Elo 1002/998
  #  5/100:  33:10  -> v5                     | Züge 164 | LLR_A +0.08 | LLR_B -0.49 | ΔElo~+50 | Stand v5 3:2 v2 | Elo 1018/982
  #  6/100:  27:30  -> v2                     | Züge 166 | LLR_A -0.24 | LLR_B -0.24 | ΔElo~-0 | Stand v5 3:3 v2 | Elo 1000/1000
  #  7/100:  41:30  -> v5                     | Züge 161 | LLR_A +0.00 | LLR_B -0.57 | ΔElo~+39 | Stand v5 4:3 v2 | Elo 1016/984
  #  8/100:  44:27  -> v5                     | Züge 160 | LLR_A +0.25 | LLR_B -0.90 | ΔElo~+70 | Stand v5 5:3 v2 | Elo 1031/969
  #  9/100:  22:17  -> v5                     | Züge 157 | LLR_A +0.50 | LLR_B -1.23 | ΔElo~+97 | Stand v5 6:3 v2 | Elo 1044/956
  # 10/100:  34:2   -> v5                     | Züge 164 | LLR_A +0.74 | LLR_B -1.56 | ΔElo~+120 | Stand v5 7:3 v2 | Elo 1056/944
  # 11/100:  43:21  -> v5                     | Züge 167 | LLR_A +0.99 | LLR_B -1.89 | ΔElo~+141 | Stand v5 8:3 v2 | Elo 1067/933
  # 12/100:  49:12  -> v5                     | Züge 160 | LLR_A +1.24 | LLR_B -2.22 | ΔElo~+159 | Stand v5 9:3 v2 | Elo 1077/923
  # 13/100:  43:31  -> v5                     | Züge 164 | LLR_A +1.48 | LLR_B -2.54 | ΔElo~+176 | Stand v5 10:3 v2 | Elo 1086/914
  # 14/100:  32:22  -> v5                     | Züge 163 | LLR_A +1.73 | LLR_B -2.54 | ΔElo~+191 | Stand v5 11:3 v2 | Elo 1095/905
  # 15/100:  42:26  -> v5                     | Züge 160 | LLR_A +1.98 | LLR_B -2.54 | ΔElo~+205 | Stand v5 12:3 v2 | Elo 1103/897
  # 16/100:  11:13  -> v2                     | Züge 157 | LLR_A +1.65 | LLR_B -2.54 | ΔElo~+166 | Stand v5 12:4 v2 | Elo 1078/922
  # 17/100:  31:41  -> v2                     | Züge 161 | LLR_A +1.32 | LLR_B -2.54 | ΔElo~+134 | Stand v5 12:5 v2 | Elo 1055/945
  # 18/100:  23:31  -> v2                     | Züge 161 | LLR_A +0.99 | LLR_B -2.54 | ΔElo~+108 | Stand v5 12:6 v2 | Elo 1034/966
  # 19/100:  31:25  -> v5                     | Züge 167 | LLR_A +1.24 | LLR_B -2.54 | ΔElo~+120 | Stand v5 13:6 v2 | Elo 1047/953
  # 20/100:  62:28  -> v5                     | Züge 171 | LLR_A +1.49 | LLR_B -2.54 | ΔElo~+132 | Stand v5 14:6 v2 | Elo 1059/941
  # 21/100:  22:39  -> v2                     | Züge 159 | LLR_A +1.16 | LLR_B -2.54 | ΔElo~+109 | Stand v5 14:7 v2 | Elo 1038/962
  # 22/100:  31:47  -> v2                     | Züge 158 | LLR_A +0.83 | LLR_B -2.54 | ΔElo~+89 | Stand v5 14:8 v2 | Elo 1019/981
  # 23/100:  42:27  -> v5                     | Züge 161 | LLR_A +1.07 | LLR_B -2.54 | ΔElo~+100 | Stand v5 15:8 v2 | Elo 1033/967
  # 24/100:  45:37  -> v5                     | Züge 160 | LLR_A +1.32 | LLR_B -2.54 | ΔElo~+110 | Stand v5 16:8 v2 | Elo 1046/954
  # 25/100:  48:16  -> v5                     | Züge 161 | LLR_A +1.57 | LLR_B -2.54 | ΔElo~+120 | Stand v5 17:8 v2 | Elo 1058/942
  # 26/100:  41:54  -> v2                     | Züge 157 | LLR_A +1.24 | LLR_B -2.54 | ΔElo~+102 | Stand v5 17:9 v2 | Elo 1037/963
  # 27/100:  15:18  -> v2                     | Züge 164 | LLR_A +0.91 | LLR_B -2.54 | ΔElo~+86 | Stand v5 17:10 v2 | Elo 1018/982
  # 28/100:  34:50  -> v2                     | Züge 161 | LLR_A +0.58 | LLR_B -2.54 | ΔElo~+70 | Stand v5 17:11 v2 | Elo 1000/1000
  # 29/100:  34:17  -> v5                     | Züge 159 | LLR_A +0.83 | LLR_B -2.54 | ΔElo~+80 | Stand v5 18:11 v2 | Elo 1016/984
  # 30/100:  46:49  -> v2                     | Züge 157 | LLR_A +0.50 | LLR_B -2.54 | ΔElo~+66 | Stand v5 18:12 v2 | Elo 999/1001
  # 31/100:   9:27  -> v2                     | Züge 162 | LLR_A +0.17 | LLR_B -2.54 | ΔElo~+53 | Stand v5 18:13 v2 | Elo 983/1017
  # 32/100:  38:23  -> v5                     | Züge 163 | LLR_A +0.42 | LLR_B -2.54 | ΔElo~+62 | Stand v5 19:13 v2 | Elo 1001/999
  # 33/100:  23:47  -> v2                     | Züge 159 | LLR_A +0.09 | LLR_B -2.54 | ΔElo~+50 | Stand v5 19:14 v2 | Elo 985/1015
  # 34/100:  45:39  -> v5                     | Züge 165 | LLR_A +0.34 | LLR_B -2.54 | ΔElo~+58 | Stand v5 20:14 v2 | Elo 1002/998
  # 35/100:  61:88  -> v2                     | Züge 168 | LLR_A +0.01 | LLR_B -2.54 | ΔElo~+47 | Stand v5 20:15 v2 | Elo 986/1014
  # 36/100:  31:34  -> v2                     | Züge 170 | LLR_A -0.32 | LLR_B -2.54 | ΔElo~+37 | Stand v5 20:16 v2 | Elo 971/1029
  # 37/100:  14:34  -> v2                     | Züge 160 | LLR_A -0.65 | LLR_B -2.54 | ΔElo~+27 | Stand v5 20:17 v2 | Elo 958/1042
  # 38/100:  39:28  -> v5                     | Züge 161 | LLR_A -0.40 | LLR_B -2.54 | ΔElo~+35 | Stand v5 21:17 v2 | Elo 978/1022
  # 39/100:  15:17  -> v2                     | Züge 168 | LLR_A -0.73 | LLR_B -2.54 | ΔElo~+25 | Stand v5 21:18 v2 | Elo 964/1036
  # 40/100:  18:11  -> v5                     | Züge 157 | LLR_A -0.48 | LLR_B -2.54 | ΔElo~+33 | Stand v5 22:18 v2 | Elo 983/1017
  # 41/100:  47:56  -> v2                     | Züge 155 | LLR_A -0.81 | LLR_B -2.54 | ΔElo~+24 | Stand v5 22:19 v2 | Elo 969/1031
  # 42/100:   9:5   -> v5                     | Züge 167 | LLR_A -0.56 | LLR_B -2.54 | ΔElo~+32 | Stand v5 23:19 v2 | Elo 988/1012
  # 43/100:  40:9   -> v5                     | Züge 165 | LLR_A -0.32 | LLR_B -2.54 | ΔElo~+39 | Stand v5 24:19 v2 | Elo 1005/995
  # 44/100:  36:27  -> v5                     | Züge 162 | LLR_A -0.07 | LLR_B -2.54 | ΔElo~+46 | Stand v5 25:19 v2 | Elo 1021/979
  # 45/100:  41:44  -> v2                     | Züge 166 | LLR_A -0.40 | LLR_B -2.54 | ΔElo~+37 | Stand v5 25:20 v2 | Elo 1003/997
  # 46/100:  61:50  -> v5                     | Züge 164 | LLR_A -0.15 | LLR_B -2.54 | ΔElo~+44 | Stand v5 26:20 v2 | Elo 1019/981
  # 47/100:  38:16  -> v5                     | Züge 159 | LLR_A +0.10 | LLR_B -2.54 | ΔElo~+50 | Stand v5 27:20 v2 | Elo 1033/967
  # 48/100:  41:0   -> v5                     | Züge 150 | LLR_A +0.34 | LLR_B -2.54 | ΔElo~+56 | Stand v5 28:20 v2 | Elo 1046/954
  # 49/100:  43:64  -> v2                     | Züge 166 | LLR_A +0.01 | LLR_B -2.54 | ΔElo~+48 | Stand v5 28:21 v2 | Elo 1026/974
  # 50/100:  17:41  -> v2                     | Züge 156 | LLR_A -0.32 | LLR_B -2.54 | ΔElo~+40 | Stand v5 28:22 v2 | Elo 1008/992
  # 51/100:  29:26  -> v5                     | Züge 163 | LLR_A -0.07 | LLR_B -2.54 | ΔElo~+46 | Stand v5 29:22 v2 | Elo 1023/977
  # 52/100:  53:27  -> v5                     | Züge 166 | LLR_A +0.18 | LLR_B -2.54 | ΔElo~+52 | Stand v5 30:22 v2 | Elo 1037/963
  # 53/100:  24:46  -> v2                     | Züge 166 | LLR_A -0.15 | LLR_B -2.54 | ΔElo~+44 | Stand v5 30:23 v2 | Elo 1018/982
  # 54/100:  43:44  -> v2                     | Züge 160 | LLR_A -0.48 | LLR_B -2.54 | ΔElo~+37 | Stand v5 30:24 v2 | Elo 1000/1000
  # 55/100:  38:20  -> v5                     | Züge 165 | LLR_A -0.23 | LLR_B -2.54 | ΔElo~+43 | Stand v5 31:24 v2 | Elo 1016/984
  # 56/100:  69:37  -> v5                     | Züge 162 | LLR_A +0.02 | LLR_B -2.54 | ΔElo~+48 | Stand v5 32:24 v2 | Elo 1031/969
  # 57/100:  22:42  -> v2                     | Züge 163 | LLR_A -0.31 | LLR_B -2.54 | ΔElo~+41 | Stand v5 32:25 v2 | Elo 1012/988
  # 58/100:  34:36  -> v2                     | Züge 166 | LLR_A -0.64 | LLR_B -2.54 | ΔElo~+35 | Stand v5 32:26 v2 | Elo 995/1005
  # 59/100:  32:29  -> v5                     | Züge 163 | LLR_A -0.39 | LLR_B -2.54 | ΔElo~+40 | Stand v5 33:26 v2 | Elo 1011/989
  # 60/100:  40:11  -> v5                     | Züge 157 | LLR_A -0.15 | LLR_B -2.54 | ΔElo~+45 | Stand v5 34:26 v2 | Elo 1026/974
  # 61/100:  57:54  -> v5                     | Züge 159 | LLR_A +0.10 | LLR_B -2.54 | ΔElo~+50 | Stand v5 35:26 v2 | Elo 1040/960
  # 62/100:  29:43  -> v2                     | Züge 157 | LLR_A -0.23 | LLR_B -2.54 | ΔElo~+44 | Stand v5 35:27 v2 | Elo 1020/980
  # 63/100:  34:46  -> v2                     | Züge 163 | LLR_A -0.56 | LLR_B -2.54 | ΔElo~+38 | Stand v5 35:28 v2 | Elo 1002/998
  # 64/100:  44:48  -> v2                     | Züge 157 | LLR_A -0.89 | LLR_B -2.54 | ΔElo~+32 | Stand v5 35:29 v2 | Elo 986/1014
  # 65/100:  20:74  -> v2                     | Züge 162 | LLR_A -1.22 | LLR_B -2.54 | ΔElo~+26 | Stand v5 35:30 v2 | Elo 971/1029
  # 66/100:  20:32  -> v2                     | Züge 158 | LLR_A -1.54 | LLR_B -2.54 | ΔElo~+20 | Stand v5 35:31 v2 | Elo 958/1042
  # 67/100:  19:35  -> v2                     | Züge 157 | LLR_A -1.87 | LLR_B -2.54 | ΔElo~+15 | Stand v5 35:32 v2 | Elo 946/1054
  # 68/100:  31:30  -> v5                     | Züge 160 | LLR_A -1.63 | LLR_B -2.54 | ΔElo~+20 | Stand v5 36:32 v2 | Elo 967/1033
  # 69/100:  41:2   -> v5                     | Züge 165 | LLR_A -1.38 | LLR_B -2.54 | ΔElo~+25 | Stand v5 37:32 v2 | Elo 986/1014
  # 70/100:  41:36  -> v5                     | Züge 160 | LLR_A -1.13 | LLR_B -2.54 | ΔElo~+29 | Stand v5 38:32 v2 | Elo 1003/997
  # 71/100:  23:46  -> v2                     | Züge 161 | LLR_A -1.46 | LLR_B -2.54 | ΔElo~+24 | Stand v5 38:33 v2 | Elo 987/1013
  # 72/100:  51:30  -> v5                     | Züge 168 | LLR_A -1.21 | LLR_B -2.54 | ΔElo~+28 | Stand v5 39:33 v2 | Elo 1004/996
  # 73/100:  32:32  -> v2                     | Züge 161 | LLR_A -1.54 | LLR_B -2.54 | ΔElo~+23 | Stand v5 39:34 v2 | Elo 988/1012
  # 74/100:  15:23  -> v2                     | Züge 161 | LLR_A -1.87 | LLR_B -2.54 | ΔElo~+18 | Stand v5 39:35 v2 | Elo 973/1027
  # 75/100:  25:45  -> v2                     | Züge 162 | LLR_A -2.20 | LLR_B -2.54 | ΔElo~+14 | Stand v5 39:36 v2 | Elo 959/1041
  # 76/100:  26:34  -> v2                     | Züge 165 | LLR_A -2.53 | LLR_B -2.54 | ΔElo~+9 | Stand v5 39:37 v2 | Elo 947/1053
  ⏹️  SPRT-Entscheid nach 76 Spielen: Gleich stark (beide Seiten nicht signifikant staerker) (LLR_A=-2.53, LLR_B=-2.54).
--------------------------------------------------
🏆 ERGEBNIS: v5 39:37 v2 (51% A-Siege) in 1012.9s (0.1 Spiele/s)  [vorzeitig nach 76/100 Spielen]
   Ø Score: v5 34.6 | v2 31.9
   0:0-Spiele: 0/76 (0.0%)
   Elo: v5 947 | v2 1053
```

**Arena vs. Heuristik**

```

```
