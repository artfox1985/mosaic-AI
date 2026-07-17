trainiert mit

- --games 2000 --mode mcts --sims 400
- --games 2000 --mode network --sims 400 --version v1c --stage 1
- --games 7000 --mode network --sims 400 --version v2 --stage 1
- --games 2300 --mode network --sims 400 --version v2 --stage 1
- --load v2

**Netzdaten**

```
PS D:\Archiv\Documents\Projekte\mosaic-AI> python train.py --name v4 --epochs 100 --load v2
Lade Daten aus 1197 Dateien...
Datensatz geladen: 1796787 Züge. (Features pro Zug: 684) — 746.7s
💾 Speichere HDF5-Cache...
✅ Cache gespeichert: D:\Archiv\Documents\Projekte\mosaic-AI\data\.cache_ef4c399d0ff3.h5
Lade Daten aus 133 Dateien...
Datensatz geladen: 199960 Züge. (Features pro Zug: 684) — 87.8s
💾 Speichere HDF5-Cache...
✅ Cache gespeichert: D:\Archiv\Documents\Projekte\mosaic-AI\data\.cache_0842439e7872.h5
   Val-Split: 1197 Trainings-Dateien / 133 Val-Dateien (1,796,787 / 199,960 Züge)
   Value-Ziel-Streuung: σ=0.163 (Varianz=0.0267, zum Vergleich mit v_pred σ unten; Varianz ist die Baseline-MSE bei reiner Mittelwert-Vorhersage)

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
Epoche  1/100 | Total Loss:   2.99 (R²=+0.38, Policy:  2.97) | Val-R²=+0.39 | Policy-Val= 2.18 | v_pred μ=+0.14 σ=0.101
Epoche  2/100 | Total Loss:   2.93 (R²=+0.39, Policy:  2.92) | Val-R²=+0.38 | Policy-Val= 2.18 | v_pred μ=+0.14 σ=0.102
Epoche  3/100 | Total Loss:   2.89 (R²=+0.40, Policy:  2.87) | Val-R²=+0.38 | Policy-Val= 2.19 | v_pred μ=+0.14 σ=0.103
Epoche  4/100 | Total Loss:   2.84 (R²=+0.40, Policy:  2.82) | Val-R²=+0.38 | Policy-Val= 2.19 | v_pred μ=+0.14 σ=0.104
Epoche  5/100 | Total Loss:   2.79 (R²=+0.41, Policy:  2.77) | Val-R²=+0.37 | Policy-Val= 2.19 | v_pred μ=+0.14 σ=0.105
Epoche  6/100 | Total Loss:   2.74 (R²=+0.41, Policy:  2.73) | Val-R²=+0.37 | Policy-Val= 2.19 | v_pred μ=+0.14 σ=0.105
Epoche  7/100 | Total Loss:   2.70 (R²=+0.41, Policy:  2.69) | Val-R²=+0.37 | Policy-Val= 2.19 | v_pred μ=+0.14 σ=0.105
Epoche  8/100 | Total Loss:   2.67 (R²=+0.41, Policy:  2.65) | Val-R²=+0.37 | Policy-Val= 2.19 | v_pred μ=+0.14 σ=0.105
Epoche  9/100 | Total Loss:   2.64 (R²=+0.41, Policy:  2.62) | Val-R²=+0.37 | Policy-Val= 2.19 | v_pred μ=+0.14 σ=0.105
Epoche 10/100 | Total Loss:   2.61 (R²=+0.41, Policy:  2.59) | Val-R²=+0.37 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.105
Epoche 11/100 | Total Loss:   2.59 (R²=+0.41, Policy:  2.57) | Val-R²=+0.37 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.106
Epoche 12/100 | Total Loss:   2.57 (R²=+0.42, Policy:  2.55) | Val-R²=+0.37 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.106
Epoche 13/100 | Total Loss:   2.55 (R²=+0.42, Policy:  2.53) | Val-R²=+0.36 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.106
Epoche 14/100 | Total Loss:   2.53 (R²=+0.42, Policy:  2.52) | Val-R²=+0.36 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.106
Epoche 15/100 | Total Loss:   2.52 (R²=+0.42, Policy:  2.51) | Val-R²=+0.37 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.106
Epoche 16/100 | Total Loss:   2.51 (R²=+0.42, Policy:  2.49) | Val-R²=+0.36 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.106
Epoche 17/100 | Total Loss:   2.50 (R²=+0.42, Policy:  2.48) | Val-R²=+0.36 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.106
Epoche 18/100 | Total Loss:   2.49 (R²=+0.42, Policy:  2.47) | Val-R²=+0.36 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.106
Epoche 19/100 | Total Loss:   2.48 (R²=+0.42, Policy:  2.46) | Val-R²=+0.36 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.107
Epoche 20/100 | Total Loss:   2.47 (R²=+0.42, Policy:  2.45) | Val-R²=+0.35 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.107
Epoche 21/100 | Total Loss:   2.46 (R²=+0.42, Policy:  2.44) | Val-R²=+0.36 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.107
Epoche 22/100 | Total Loss:   2.45 (R²=+0.42, Policy:  2.44) | Val-R²=+0.36 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.107
Epoche 23/100 | Total Loss:   2.44 (R²=+0.42, Policy:  2.43) | Val-R²=+0.35 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.107
Epoche 24/100 | Total Loss:   2.44 (R²=+0.42, Policy:  2.42) | Val-R²=+0.36 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.107
Epoche 25/100 | Total Loss:   2.43 (R²=+0.42, Policy:  2.42) | Val-R²=+0.35 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.107
Epoche 26/100 | Total Loss:   2.43 (R²=+0.42, Policy:  2.41) | Val-R²=+0.35 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.107
Epoche 27/100 | Total Loss:   2.42 (R²=+0.42, Policy:  2.41) | Val-R²=+0.36 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.107
Epoche 28/100 | Total Loss:   2.41 (R²=+0.42, Policy:  2.40) | Val-R²=+0.35 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.107
Epoche 29/100 | Total Loss:   2.41 (R²=+0.42, Policy:  2.40) | Val-R²=+0.35 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.107
Epoche 30/100 | Total Loss:   2.41 (R²=+0.43, Policy:  2.39) | Val-R²=+0.35 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.107
Epoche 31/100 | Total Loss:   2.40 (R²=+0.43, Policy:  2.39) | Val-R²=+0.35 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.107
Epoche 32/100 | Total Loss:   2.40 (R²=+0.43, Policy:  2.38) | Val-R²=+0.36 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.107
Epoche 33/100 | Total Loss:   2.40 (R²=+0.43, Policy:  2.38) | Val-R²=+0.36 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.107  🟡 POLICY-PLATEAU
Epoche 34/100 | Total Loss:   2.39 (R²=+0.43, Policy:  2.38) | Val-R²=+0.36 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.107  🟡 POLICY-PLATEAU
Epoche 35/100 | Total Loss:   2.39 (R²=+0.43, Policy:  2.37) | Val-R²=+0.35 | Policy-Val= 2.20 | v_pred μ=+0.14 σ=0.107  🟡 POLICY-PLATEAU
Epoche 36/100 | Total Loss:   2.38 (R²=+0.43, Policy:  2.37) | Val-R²=+0.35 | Policy-Val= 2.21 | v_pred μ=+0.14 σ=0.108  🟡 POLICY-PLATEAU
Epoche 37/100 | Total Loss:   2.38 (R²=+0.43, Policy:  2.37) | Val-R²=+0.35 | Policy-Val= 2.21 | v_pred μ=+0.14 σ=0.108  🟡 POLICY-PLATEAU
Epoche 38/100 | Total Loss:   2.38 (R²=+0.43, Policy:  2.36) | Val-R²=+0.36 | Policy-Val= 2.21 | v_pred μ=+0.14 σ=0.108  🟡 POLICY-PLATEAU

⏹️  Early Stopping: Policy plateaut seit Epoche 33 (5 Epochen ohne Fortschritt).

=======================================================
  PHASE 2: VALUE-KALIBRIERUNG (Trunk/Policy eingefroren)
───────────────────────────────────────────────────────
  Kalibrierung  1/50 | Val-R²=+0.368  (bislang bester: Epoche 1)
  Kalibrierung  2/50 | Val-R²=+0.374  (bislang bester: Epoche 2)
  Kalibrierung  3/50 | Val-R²=+0.371  (bislang bester: Epoche 2)
  Kalibrierung  4/50 | Val-R²=+0.366  (bislang bester: Epoche 2)
  Kalibrierung  5/50 | Val-R²=+0.365  (bislang bester: Epoche 2)
  Kalibrierung  6/50 | Val-R²=+0.362  (bislang bester: Epoche 2)
  Kalibrierung  7/50 | Val-R²=+0.356  (bislang bester: Epoche 2)
  Kalibrierung  8/50 | Val-R²=+0.361  (bislang bester: Epoche 2)
  Kalibrierung  9/50 | Val-R²=+0.357  (bislang bester: Epoche 2)
  Kalibrierung 10/50 | Val-R²=+0.348  (bislang bester: Epoche 2)
  ⏹️  Kalibrierung gestoppt: Val-R² seit Epoche 2 nicht mehr verbessert (Bestwert 0.374).
  ✅ Value-Head auf besten Kalibrierungs-Stand zurückgesetzt (Epoche 2, Val-R²=0.374).
=======================================================

=======================================================
  TRAINING SUMMARY
=======================================================
  Epochen:       100
  Züge:          1,796,787  (+199,960 Val, nie trainiert)
  Batches/Epoche:7018
───────────────────────────────────────────────────────
  Policy Loss:   2.3640 / 6.18 max  (38.3%)  🟡 Gut
  Policy Val-Loss: 2.2050  (Gap ggü. Train: -0.1589)
  Value Loss:    0.0157  (R²=0.41 ggü. Mittelwert-Baseline)  🟡 Gut
  Value Val-R²:  0.37  (Gap ggü. Train: +0.04)  🟢 Train/Val nah beieinander
───────────────────────────────────────────────────────
  ℹ️  Phase 1 Val-R² war in Epoche 1 am besten (0.39), danach Überfitten (normal — Value trainiert bewusst bis zum Ende mit).
  🎯 Phase 2 (Value-Kalibrierung): bester Stand nach Epoche 2, Val-R²=0.37 — Wert oben spiegelt diesen kalibrierten Value-Head wider.
  ⏹️  Early Stopping (Policy-Plateau) nach Epoche 38/100
  🟡 Plateau ab Epoche 33.
     → Für nächste Generation: mehr Sims im Self-Play.
=======================================================

=======================================================
  NETZAUSLASTUNG (Hidden Size: 512)
───────────────────────────────────────────────────────
  Schicht          Dead   Aktiv-Rate        Eff.Rank
  ───────────────────────────────────────────────────
  layer1     0/512 (0%)          40%   220/512 (43%)
  layer2     0/512 (0%)          41%   201/512 (39%)
  layer3    62/512 (12%)          12%   174/512 (34%)
  ───────────────────────────────────────────────────
  🟢 Gesunde Auslastung (Dead 4%, Rank 39%).
=======================================================

✅ Training beendet! Neues Model gespeichert unter:
📂 D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v4.pth
📈 Loss-Verlauf gespeichert unter:
📂 D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v4_loss.png
✅ Exportiert: D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v4.onnx  (input=684, hidden=512, value_hidden=64, opset=13)
📎 Referenz für Rust-Parität: D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v4.onnx.ref.txt

=======================================================
  STUFE 1 vs. STUFE 2 (max. 50 Spiele, 200 Sims, Early-Stop)
───────────────────────────────────────────────────────
🏟️ Mosaic-AI ARENA — Netz vs Netz (Rust) 🏟️
  v4(Stufe1) (Brett 0, 200 Sims, c_puct=1.5, Stufe 1/DFS-Blatt) vs v4(Stufe2) (Brett 1, 200 Sims, c_puct=1.5, Stufe 2/Netz-Value-Blatt) — 50 Spiele
--------------------------------------------------
  #  1/50:  40:0   -> v4(Stufe1)             | Züge 155 | Strength 1.000 | Stand v4(Stufe1) 1:0 v4(Stufe2) | Elo 1016/984
  #  2/50:  34:18  -> v4(Stufe1)             | Züge 165 | Strength 0.933 | Stand v4(Stufe1) 2:0 v4(Stufe2) | Elo 1030/970
  #  3/50:  22:22  -> v4(Stufe2)             | Züge 164 | Strength 0.348 | Stand v4(Stufe1) 2:1 v4(Stufe2) | Elo 1023/977
  #  4/50:  23:57  -> v4(Stufe2)             | Züge 161 | Strength 1.000 | Stand v4(Stufe1) 2:2 v4(Stufe2) | Elo 1005/995
  #  5/50:  57:28  -> v4(Stufe1)             | Züge 168 | Strength 1.000 | Stand v4(Stufe1) 3:2 v4(Stufe2) | Elo 1021/979
  #  6/50:  30:5   -> v4(Stufe1)             | Züge 153 | Strength 0.888 | Stand v4(Stufe1) 4:2 v4(Stufe2) | Elo 1033/967
  #  7/50:  34:6   -> v4(Stufe1)             | Züge 165 | Strength 0.933 | Stand v4(Stufe1) 5:2 v4(Stufe2) | Elo 1045/955
  #  8/50:  27:11  -> v4(Stufe1)             | Züge 156 | Strength 0.854 | Stand v4(Stufe1) 6:2 v4(Stufe2) | Elo 1055/945
  #  9/50:  43:15  -> v4(Stufe1)             | Züge 158 | Strength 1.000 | Stand v4(Stufe1) 7:2 v4(Stufe2) | Elo 1066/934
  # 10/50:  42:19  -> v4(Stufe1)             | Züge 156 | Strength 1.000 | Stand v4(Stufe1) 8:2 v4(Stufe2) | Elo 1076/924
  # 11/50:  26:17  -> v4(Stufe1)             | Züge 156 | Strength 0.663 | Stand v4(Stufe1) 9:2 v4(Stufe2) | Elo 1082/918
  ⏹️  Vorzeitig entschieden: v4(Stufe1) hat nach 11 Spielen bereits 9 Siege (95%-Signifikanz für >50% Gewinnchance).
--------------------------------------------------
🏆 ERGEBNIS: v4(Stufe1) 9:2 v4(Stufe2) (82% A-Siege) in 455.8s (0.0 Spiele/s)  [vorzeitig nach 11/50 Spielen]
   Ø Score: v4(Stufe1) 34.4 | v4(Stufe2) 18.0
   0:0-Spiele: 0/11 (0.0%)
   Elo: v4(Stufe1) 1082 | v4(Stufe2) 918
=======================================================
```

**Arena vs. v2**

```

```

**Arena vs. Heuristik**

```

```
