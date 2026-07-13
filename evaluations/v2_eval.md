trainiert mit

- --games 4000 --mode mcts --sims 400
- --games 7000 --mode network --sims 400 --version v1c --stage 1
- --load v1c

**Netzdaten**

```
PS D:\Archiv\Documents\Projekte\mosaic-AI> python train.py --name v2 --epochs 100 --load v1c
Lade Daten aus 990 Dateien...
Datensatz geladen: 1490553 Züge. (Features pro Zug: 684) — 875.2s
💾 Speichere HDF5-Cache...
✅ Cache gespeichert: D:\Archiv\Documents\Projekte\mosaic-AI\data\.cache_8b155f61f723.h5
Lade Daten aus 110 Dateien...
Datensatz geladen: 165722 Züge. (Features pro Zug: 684) — 91.2s
💾 Speichere HDF5-Cache...
✅ Cache gespeichert: D:\Archiv\Documents\Projekte\mosaic-AI\data\.cache_cba5d0e8b5d1.h5
   Val-Split: 990 Trainings-Dateien / 110 Val-Dateien (1,490,553 / 165,722 Züge)
   Value-Ziel-Streuung: σ=0.172 (Varianz=0.0295, zum Vergleich mit v_pred σ unten; Varianz ist die Baseline-MSE bei reiner Mittelwert-Vorhersage)

🚀 Starte PyTorch Training auf: CUDA
🧠 Netz-Architektur: 684→512→512→512
⚙️  Hyperparameter (config.py):
   Learning Rate : 0.0004
   Value Weight  : 1
   Batch Size    : 256
   Value-Target  : tanh(eigen/50) - 0.1*tanh(gegner/50) (Endergebnis statt Win/Loss)
📥 Lade altes Model als Startpunkt: alphazero_v1c.pth
   Epochen       : 100
🔄 Warm-Start erkannt: Trainiere für 100 Epochen.
Epoche  1/100 | Total Loss:   2.98 (R²=+0.39, Policy:  2.96) | Val-R²=+0.42 | Policy-Val= 2.17 | v_pred μ=+0.16 σ=0.107
Epoche  2/100 | Total Loss:   2.87 (R²=+0.40, Policy:  2.85) | Val-R²=+0.42 | Policy-Val= 2.18 | v_pred μ=+0.16 σ=0.109
Epoche  3/100 | Total Loss:   2.79 (R²=+0.41, Policy:  2.78) | Val-R²=+0.41 | Policy-Val= 2.18 | v_pred μ=+0.16 σ=0.110
Epoche  4/100 | Total Loss:   2.72 (R²=+0.41, Policy:  2.71) | Val-R²=+0.41 | Policy-Val= 2.19 | v_pred μ=+0.16 σ=0.111
Epoche  5/100 | Total Loss:   2.66 (R²=+0.42, Policy:  2.64) | Val-R²=+0.41 | Policy-Val= 2.19 | v_pred μ=+0.16 σ=0.111
Epoche  6/100 | Total Loss:   2.61 (R²=+0.42, Policy:  2.59) | Val-R²=+0.40 | Policy-Val= 2.19 | v_pred μ=+0.16 σ=0.112
Epoche  7/100 | Total Loss:   2.57 (R²=+0.42, Policy:  2.55) | Val-R²=+0.40 | Policy-Val= 2.19 | v_pred μ=+0.16 σ=0.112
Epoche  8/100 | Total Loss:   2.53 (R²=+0.42, Policy:  2.52) | Val-R²=+0.40 | Policy-Val= 2.20 | v_pred μ=+0.16 σ=0.112
Epoche  9/100 | Total Loss:   2.51 (R²=+0.42, Policy:  2.49) | Val-R²=+0.40 | Policy-Val= 2.20 | v_pred μ=+0.16 σ=0.112
Epoche 10/100 | Total Loss:   2.49 (R²=+0.42, Policy:  2.47) | Val-R²=+0.40 | Policy-Val= 2.20 | v_pred μ=+0.16 σ=0.112
Epoche 11/100 | Total Loss:   2.47 (R²=+0.42, Policy:  2.45) | Val-R²=+0.40 | Policy-Val= 2.20 | v_pred μ=+0.16 σ=0.112
Epoche 12/100 | Total Loss:   2.46 (R²=+0.42, Policy:  2.44) | Val-R²=+0.40 | Policy-Val= 2.20 | v_pred μ=+0.16 σ=0.112
Epoche 13/100 | Total Loss:   2.44 (R²=+0.42, Policy:  2.43) | Val-R²=+0.39 | Policy-Val= 2.20 | v_pred μ=+0.16 σ=0.112
Epoche 14/100 | Total Loss:   2.43 (R²=+0.43, Policy:  2.42) | Val-R²=+0.39 | Policy-Val= 2.20 | v_pred μ=+0.16 σ=0.112
Epoche 15/100 | Total Loss:   2.42 (R²=+0.43, Policy:  2.41) | Val-R²=+0.39 | Policy-Val= 2.20 | v_pred μ=+0.16 σ=0.113
Epoche 16/100 | Total Loss:   2.41 (R²=+0.43, Policy:  2.40) | Val-R²=+0.39 | Policy-Val= 2.20 | v_pred μ=+0.16 σ=0.113
Epoche 17/100 | Total Loss:   2.41 (R²=+0.43, Policy:  2.39) | Val-R²=+0.40 | Policy-Val= 2.20 | v_pred μ=+0.16 σ=0.113
Epoche 18/100 | Total Loss:   2.40 (R²=+0.43, Policy:  2.38) | Val-R²=+0.39 | Policy-Val= 2.20 | v_pred μ=+0.16 σ=0.113
Epoche 19/100 | Total Loss:   2.39 (R²=+0.43, Policy:  2.38) | Val-R²=+0.40 | Policy-Val= 2.21 | v_pred μ=+0.16 σ=0.113
Epoche 20/100 | Total Loss:   2.39 (R²=+0.43, Policy:  2.37) | Val-R²=+0.39 | Policy-Val= 2.21 | v_pred μ=+0.16 σ=0.113
Epoche 21/100 | Total Loss:   2.39 (R²=+0.43, Policy:  2.37) | Val-R²=+0.39 | Policy-Val= 2.21 | v_pred μ=+0.16 σ=0.113
Epoche 22/100 | Total Loss:   2.38 (R²=+0.43, Policy:  2.36) | Val-R²=+0.39 | Policy-Val= 2.21 | v_pred μ=+0.16 σ=0.113
Epoche 23/100 | Total Loss:   2.37 (R²=+0.43, Policy:  2.36) | Val-R²=+0.39 | Policy-Val= 2.21 | v_pred μ=+0.16 σ=0.114
Epoche 24/100 | Total Loss:   2.37 (R²=+0.43, Policy:  2.36) | Val-R²=+0.39 | Policy-Val= 2.21 | v_pred μ=+0.16 σ=0.114
Epoche 25/100 | Total Loss:   2.37 (R²=+0.43, Policy:  2.35) | Val-R²=+0.39 | Policy-Val= 2.21 | v_pred μ=+0.16 σ=0.114
Epoche 26/100 | Total Loss:   2.36 (R²=+0.44, Policy:  2.35) | Val-R²=+0.39 | Policy-Val= 2.21 | v_pred μ=+0.16 σ=0.114
Epoche 27/100 | Total Loss:   2.36 (R²=+0.44, Policy:  2.34) | Val-R²=+0.39 | Policy-Val= 2.21 | v_pred μ=+0.16 σ=0.114  🟡 POLICY-PLATEAU
Epoche 28/100 | Total Loss:   2.36 (R²=+0.44, Policy:  2.34) | Val-R²=+0.39 | Policy-Val= 2.21 | v_pred μ=+0.16 σ=0.114  🟡 POLICY-PLATEAU
Epoche 29/100 | Total Loss:   2.35 (R²=+0.44, Policy:  2.34) | Val-R²=+0.39 | Policy-Val= 2.21 | v_pred μ=+0.16 σ=0.114  🟡 POLICY-PLATEAU
Epoche 30/100 | Total Loss:   2.35 (R²=+0.44, Policy:  2.33) | Val-R²=+0.39 | Policy-Val= 2.21 | v_pred μ=+0.16 σ=0.114  🟡 POLICY-PLATEAU
Epoche 31/100 | Total Loss:   2.35 (R²=+0.44, Policy:  2.33) | Val-R²=+0.39 | Policy-Val= 2.21 | v_pred μ=+0.16 σ=0.114  🟡 POLICY-PLATEAU
Epoche 32/100 | Total Loss:   2.35 (R²=+0.44, Policy:  2.33) | Val-R²=+0.39 | Policy-Val= 2.21 | v_pred μ=+0.16 σ=0.114  🟡 POLICY-PLATEAU

⏹️  Early Stopping: Policy plateaut seit Epoche 27 (5 Epochen ohne Fortschritt).

=======================================================
  PHASE 2: VALUE-KALIBRIERUNG (Trunk/Policy eingefroren)
───────────────────────────────────────────────────────
  Kalibrierung  1/50 | Val-R²=+0.404  (bislang bester: Epoche 1)
  Kalibrierung  2/50 | Val-R²=+0.399  (bislang bester: Epoche 1)
  Kalibrierung  3/50 | Val-R²=+0.395  (bislang bester: Epoche 1)
  Kalibrierung  4/50 | Val-R²=+0.396  (bislang bester: Epoche 1)
  Kalibrierung  5/50 | Val-R²=+0.393  (bislang bester: Epoche 1)
  Kalibrierung  6/50 | Val-R²=+0.390  (bislang bester: Epoche 1)
  Kalibrierung  7/50 | Val-R²=+0.391  (bislang bester: Epoche 1)
  Kalibrierung  8/50 | Val-R²=+0.386  (bislang bester: Epoche 1)
  Kalibrierung  9/50 | Val-R²=+0.387  (bislang bester: Epoche 1)
  ⏹️  Kalibrierung gestoppt: Val-R² seit Epoche 1 nicht mehr verbessert (Bestwert 0.404).
  ✅ Value-Head auf besten Kalibrierungs-Stand zurückgesetzt (Epoche 1, Val-R²=0.404).
=======================================================

=======================================================
  TRAINING SUMMARY
=======================================================
  Epochen:       100
  Züge:          1,490,553  (+165,722 Val, nie trainiert)
  Batches/Epoche:5822
───────────────────────────────────────────────────────
  Policy Loss:   2.3293 / 6.18 max  (37.7%)  🟡 Gut
  Policy Val-Loss: 2.2095  (Gap ggü. Train: -0.1199)
  Value Loss:    0.0172  (R²=0.42 ggü. Mittelwert-Baseline)  🟡 Gut
  Value Val-R²:  0.40  (Gap ggü. Train: +0.01)  🟢 Train/Val nah beieinander
───────────────────────────────────────────────────────
  ℹ️  Phase 1 Val-R² war in Epoche 1 am besten (0.42), danach Überfitten (normal — Value trainiert bewusst bis zum Ende mit).
  🎯 Phase 2 (Value-Kalibrierung): bester Stand nach Epoche 1, Val-R²=0.40 — Wert oben spiegelt diesen kalibrierten Value-Head wider.
  ⏹️  Early Stopping (Policy-Plateau) nach Epoche 32/100
  🟡 Plateau ab Epoche 27.
     → Für nächste Generation: mehr Sims im Self-Play.
=======================================================

=======================================================
  NETZAUSLASTUNG (Hidden Size: 512)
───────────────────────────────────────────────────────
  Schicht          Dead   Aktiv-Rate        Eff.Rank
  ───────────────────────────────────────────────────
  layer1     0/512 (0%)          39%   220/512 (43%)
  layer2     0/512 (0%)          39%   199/512 (39%)
  layer3    69/512 (13%)          11%   181/512 (35%)
  ───────────────────────────────────────────────────
  🟢 Gesunde Auslastung (Dead 4%, Rank 39%).
=======================================================

✅ Training beendet! Neues Model gespeichert unter:
📂 D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v2.pth
📈 Loss-Verlauf gespeichert unter:
📂 D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v2_loss.png
✅ Exportiert: D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v2.onnx  (input=684, hidden=512, value_hidden=64, opset=13)
📎 Referenz für Rust-Parität: D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v2.onnx.ref.txt

=======================================================
  STUFE 1 vs. STUFE 2 (max. 50 Spiele, 200 Sims, Early-Stop)
───────────────────────────────────────────────────────
🏟️ Mosaic-AI ARENA — Netz vs Netz (Rust) 🏟️
  v2(Stufe1) (Brett 0, 200 Sims, c_puct=1.5, Stufe 1/DFS-Blatt) vs v2(Stufe2) (Brett 1, 200 Sims, c_puct=1.5, Stufe 2/Netz-Value-Blatt) — 50 Spiele
--------------------------------------------------
  #  1/50:  46:0   -> v2(Stufe1)             | Züge 162 | Strength 1.000 | Stand v2(Stufe1) 1:0 v2(Stufe2) | Elo 1016/984
  #  2/50:  52:0   -> v2(Stufe1)             | Züge 160 | Strength 1.000 | Stand v2(Stufe1) 2:0 v2(Stufe2) | Elo 1031/969
  #  3/50:  27:0   -> v2(Stufe1)             | Züge 155 | Strength 0.854 | Stand v2(Stufe1) 3:0 v2(Stufe2) | Elo 1042/958
  #  4/50:  37:34  -> v2(Stufe1)             | Züge 164 | Strength 0.606 | Stand v2(Stufe1) 4:0 v2(Stufe2) | Elo 1049/951
  #  5/50:  22:51  -> v2(Stufe2)             | Züge 167 | Strength 1.000 | Stand v2(Stufe1) 4:1 v2(Stufe2) | Elo 1029/971
  #  6/50:  37:0   -> v2(Stufe1)             | Züge 154 | Strength 0.966 | Stand v2(Stufe1) 5:1 v2(Stufe2) | Elo 1042/958
  #  7/50:   5:0   -> v2(Stufe1)             | Züge 148 | Strength 0.306 | Stand v2(Stufe1) 6:1 v2(Stufe2) | Elo 1046/954
  #  8/50:  36:31  -> v2(Stufe1)             | Züge 156 | Strength 0.655 | Stand v2(Stufe1) 7:1 v2(Stufe2) | Elo 1054/946
  #  9/50:  28:0   -> v2(Stufe1)             | Züge 164 | Strength 0.865 | Stand v2(Stufe1) 8:1 v2(Stufe2) | Elo 1064/936
  # 10/50:  21:30  -> v2(Stufe2)             | Züge 162 | Strength 0.708 | Stand v2(Stufe1) 8:2 v2(Stufe2) | Elo 1049/951
  # 11/50:  45:24  -> v2(Stufe1)             | Züge 155 | Strength 1.000 | Stand v2(Stufe1) 9:2 v2(Stufe2) | Elo 1061/939
  ⏹️  Vorzeitig entschieden: v2(Stufe1) hat nach 11 Spielen bereits 9 Siege (95%-Signifikanz für >50% Gewinnchance).
--------------------------------------------------
🏆 ERGEBNIS: v2(Stufe1) 9:2 v2(Stufe2) (82% A-Siege) in 393.8s (0.0 Spiele/s)  [vorzeitig nach 11/50 Spielen]
   Ø Score: v2(Stufe1) 32.4 | v2(Stufe2) 15.5
   0:0-Spiele: 0/11 (0.0%)
   Elo: v2(Stufe1) 1061 | v2(Stufe2) 939
=======================================================
```

**Arena vs. v1**

```

```

**Arena vs. Heuristik**

```
PS D:\Archiv\Documents\Projekte\mosaic-AI> python arena.py
🏟️ Mosaic-AI ARENA — Netz vs Heuristik (Rust) 🏟️
  v2 (Brett 0, 200 Sims, Stufe 1/DFS-Blatt) vs Heuristik(s200) (Brett 1, 200 Sims) — 100 Spiele  [SPRT p1=0.64, α=0.05, β=0.1]
--------------------------------------------------
  #  1/100:  16:10  -> v2                       | Züge 155 | LLR_Netz +0.25 | LLR_Heur -0.33 | ΔElo~+120 | Stand Netz 1:0 Heur | Elo 1016/984
  #  2/100:  46:47  -> Heuristik(s200)          | Züge 160 | LLR_Netz -0.08 | LLR_Heur -0.08 | ΔElo~-0 | Stand Netz 1:1 Heur | Elo 999/1001
  #  3/100:  49:66  -> Heuristik(s200)          | Züge 163 | LLR_Netz -0.41 | LLR_Heur +0.17 | ΔElo~-70 | Stand Netz 1:2 Heur | Elo 983/1017
  #  4/100:  20:46  -> Heuristik(s200)          | Züge 156 | LLR_Netz -0.74 | LLR_Heur +0.41 | ΔElo~-120 | Stand Netz 1:3 Heur | Elo 969/1031
  #  5/100:  23:69  -> Heuristik(s200)          | Züge 155 | LLR_Netz -1.07 | LLR_Heur +0.66 | ΔElo~-159 | Stand Netz 1:4 Heur | Elo 956/1044
  #  6/100:  47:65  -> Heuristik(s200)          | Züge 162 | LLR_Netz -1.40 | LLR_Heur +0.91 | ΔElo~-191 | Stand Netz 1:5 Heur | Elo 944/1056
  #  7/100:   9:54  -> Heuristik(s200)          | Züge 162 | LLR_Netz -1.72 | LLR_Heur +1.15 | ΔElo~-218 | Stand Netz 1:6 Heur | Elo 933/1067
  #  8/100:  43:71  -> Heuristik(s200)          | Züge 158 | LLR_Netz -2.05 | LLR_Heur +1.40 | ΔElo~-241 | Stand Netz 1:7 Heur | Elo 923/1077
  #  9/100:  33:35  -> Heuristik(s200)          | Züge 158 | LLR_Netz -2.38 | LLR_Heur +1.65 | ΔElo~-261 | Stand Netz 1:8 Heur | Elo 914/1086
  # 10/100:  10:40  -> Heuristik(s200)          | Züge 162 | LLR_Netz -2.38 | LLR_Heur +1.89 | ΔElo~-280 | Stand Netz 1:9 Heur | Elo 905/1095
  # 11/100:  55:67  -> Heuristik(s200)          | Züge 161 | LLR_Netz -2.38 | LLR_Heur +2.14 | ΔElo~-296 | Stand Netz 1:10 Heur | Elo 897/1103
  # 12/100:  12:49  -> Heuristik(s200)          | Züge 168 | LLR_Netz -2.38 | LLR_Heur +2.39 | ΔElo~-311 | Stand Netz 1:11 Heur | Elo 890/1110
  # 13/100:  51:47  -> v2                       | Züge 160 | LLR_Netz -2.38 | LLR_Heur +2.06 | ΔElo~-241 | Stand Netz 2:11 Heur | Elo 915/1085
  # 14/100:  17:40  -> Heuristik(s200)          | Züge 161 | LLR_Netz -2.38 | LLR_Heur +2.31 | ΔElo~-255 | Stand Netz 2:12 Heur | Elo 906/1094
  # 15/100:  26:44  -> Heuristik(s200)          | Züge 158 | LLR_Netz -2.38 | LLR_Heur +2.55 | ΔElo~-268 | Stand Netz 2:13 Heur | Elo 898/1102
  # 16/100:  42:50  -> Heuristik(s200)          | Züge 171 | LLR_Netz -2.38 | LLR_Heur +2.80 | ΔElo~-280 | Stand Netz 2:14 Heur | Elo 890/1110
  # 17/100:  27:34  -> Heuristik(s200)          | Züge 157 | LLR_Netz -2.38 | LLR_Heur +3.05 | ΔElo~-291 | Stand Netz 2:15 Heur | Elo 883/1117
  ⏹️  SPRT-Entscheid nach 17 Spielen: Heuristik(s200) signifikant staerker (LLR_Netz=-2.38, LLR_Heur=+3.05).
--------------------------------------------------
🏆 ERGEBNIS: v2 2:15 Heuristik(s200) (12% Netz-Siege) in 419.1s (0.0 Spiele/s)  [vorzeitig nach 17/100 Spielen]
   Ø Score: v2 30.9 | Heuristik(s200) 49.1
   0:0-Spiele: 0/17 (0.0%)  (Sauberkeits-Indikator)
   Ø Floor-Strafe: v2 17.9 | Heuristik(s200) 9.0
   Elo: v2 883 | Heuristik(s200) 1117
```
