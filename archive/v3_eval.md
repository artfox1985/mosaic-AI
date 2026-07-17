trainiert mit

- --games 2000 --mode mcts --sims 400
- --games 2000 --mode network --sims 400 --version v1c --stage 1
- --games 7000 --mode network --sims 400 --version v2 --stage 1
- --load v2

**Netzdaten**

```
PS D:\Archiv\Documents\Projekte\mosaic-AI> python train.py --name v3 --epochs 100 --load v2
Lade Daten aus 990 Dateien...
Datensatz geladen: 1487121 Züge. (Features pro Zug: 684) — 609.9s
💾 Speichere HDF5-Cache...
✅ Cache gespeichert: D:\Archiv\Documents\Projekte\mosaic-AI\data\.cache_98559d3b2331.h5
Lade Daten aus 110 Dateien...
Datensatz geladen: 165179 Züge. (Features pro Zug: 684) — 69.1s
💾 Speichere HDF5-Cache...
✅ Cache gespeichert: D:\Archiv\Documents\Projekte\mosaic-AI\data\.cache_1e2f9ee5dd1d.h5
   Val-Split: 990 Trainings-Dateien / 110 Val-Dateien (1,487,121 / 165,179 Züge)
   Value-Ziel-Streuung: σ=0.165 (Varianz=0.0273, zum Vergleich mit v_pred σ unten; Varianz ist die Baseline-MSE bei reiner Mittelwert-Vorhersage)

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
Epoche  1/100 | Total Loss:   2.98 (R²=+0.38, Policy:  2.97) | Val-R²=+0.43 | Policy-Val= 2.18 | v_pred μ=+0.15 σ=0.103
Epoche  2/100 | Total Loss:   2.90 (R²=+0.39, Policy:  2.88) | Val-R²=+0.43 | Policy-Val= 2.18 | v_pred μ=+0.15 σ=0.104
Epoche  3/100 | Total Loss:   2.83 (R²=+0.40, Policy:  2.81) | Val-R²=+0.43 | Policy-Val= 2.18 | v_pred μ=+0.15 σ=0.105
Epoche  4/100 | Total Loss:   2.77 (R²=+0.41, Policy:  2.75) | Val-R²=+0.42 | Policy-Val= 2.18 | v_pred μ=+0.15 σ=0.106
Epoche  5/100 | Total Loss:   2.71 (R²=+0.41, Policy:  2.69) | Val-R²=+0.41 | Policy-Val= 2.19 | v_pred μ=+0.15 σ=0.106
Epoche  6/100 | Total Loss:   2.66 (R²=+0.41, Policy:  2.64) | Val-R²=+0.42 | Policy-Val= 2.19 | v_pred μ=+0.15 σ=0.107
Epoche  7/100 | Total Loss:   2.62 (R²=+0.42, Policy:  2.60) | Val-R²=+0.41 | Policy-Val= 2.19 | v_pred μ=+0.15 σ=0.107
Epoche  8/100 | Total Loss:   2.58 (R²=+0.42, Policy:  2.57) | Val-R²=+0.41 | Policy-Val= 2.19 | v_pred μ=+0.15 σ=0.107
Epoche  9/100 | Total Loss:   2.55 (R²=+0.42, Policy:  2.54) | Val-R²=+0.42 | Policy-Val= 2.19 | v_pred μ=+0.15 σ=0.107
Epoche 10/100 | Total Loss:   2.53 (R²=+0.42, Policy:  2.51) | Val-R²=+0.41 | Policy-Val= 2.19 | v_pred μ=+0.15 σ=0.108
Epoche 11/100 | Total Loss:   2.51 (R²=+0.42, Policy:  2.49) | Val-R²=+0.40 | Policy-Val= 2.19 | v_pred μ=+0.15 σ=0.108
Epoche 12/100 | Total Loss:   2.49 (R²=+0.42, Policy:  2.48) | Val-R²=+0.41 | Policy-Val= 2.19 | v_pred μ=+0.15 σ=0.108
Epoche 13/100 | Total Loss:   2.47 (R²=+0.42, Policy:  2.46) | Val-R²=+0.41 | Policy-Val= 2.19 | v_pred μ=+0.15 σ=0.108
Epoche 14/100 | Total Loss:   2.46 (R²=+0.42, Policy:  2.45) | Val-R²=+0.41 | Policy-Val= 2.20 | v_pred μ=+0.15 σ=0.108
Epoche 15/100 | Total Loss:   2.45 (R²=+0.42, Policy:  2.43) | Val-R²=+0.41 | Policy-Val= 2.20 | v_pred μ=+0.15 σ=0.108
Epoche 16/100 | Total Loss:   2.44 (R²=+0.43, Policy:  2.43) | Val-R²=+0.40 | Policy-Val= 2.20 | v_pred μ=+0.15 σ=0.108
Epoche 17/100 | Total Loss:   2.43 (R²=+0.43, Policy:  2.41) | Val-R²=+0.39 | Policy-Val= 2.20 | v_pred μ=+0.15 σ=0.108
Epoche 18/100 | Total Loss:   2.42 (R²=+0.43, Policy:  2.41) | Val-R²=+0.40 | Policy-Val= 2.20 | v_pred μ=+0.15 σ=0.109
Epoche 19/100 | Total Loss:   2.42 (R²=+0.43, Policy:  2.40) | Val-R²=+0.40 | Policy-Val= 2.20 | v_pred μ=+0.15 σ=0.109
Epoche 20/100 | Total Loss:   2.41 (R²=+0.43, Policy:  2.39) | Val-R²=+0.41 | Policy-Val= 2.20 | v_pred μ=+0.15 σ=0.109
Epoche 21/100 | Total Loss:   2.40 (R²=+0.43, Policy:  2.39) | Val-R²=+0.40 | Policy-Val= 2.20 | v_pred μ=+0.15 σ=0.109
Epoche 22/100 | Total Loss:   2.40 (R²=+0.43, Policy:  2.38) | Val-R²=+0.40 | Policy-Val= 2.20 | v_pred μ=+0.15 σ=0.109
Epoche 23/100 | Total Loss:   2.39 (R²=+0.43, Policy:  2.38) | Val-R²=+0.40 | Policy-Val= 2.20 | v_pred μ=+0.15 σ=0.109
Epoche 24/100 | Total Loss:   2.39 (R²=+0.43, Policy:  2.37) | Val-R²=+0.40 | Policy-Val= 2.20 | v_pred μ=+0.15 σ=0.109
Epoche 25/100 | Total Loss:   2.38 (R²=+0.43, Policy:  2.37) | Val-R²=+0.40 | Policy-Val= 2.20 | v_pred μ=+0.15 σ=0.109
Epoche 26/100 | Total Loss:   2.38 (R²=+0.43, Policy:  2.37) | Val-R²=+0.39 | Policy-Val= 2.20 | v_pred μ=+0.15 σ=0.109
Epoche 27/100 | Total Loss:   2.37 (R²=+0.43, Policy:  2.36) | Val-R²=+0.40 | Policy-Val= 2.20 | v_pred μ=+0.15 σ=0.109
Epoche 28/100 | Total Loss:   2.37 (R²=+0.43, Policy:  2.36) | Val-R²=+0.40 | Policy-Val= 2.20 | v_pred μ=+0.15 σ=0.109
Epoche 29/100 | Total Loss:   2.37 (R²=+0.43, Policy:  2.35) | Val-R²=+0.40 | Policy-Val= 2.20 | v_pred μ=+0.15 σ=0.109  🟡 POLICY-PLATEAU
Epoche 30/100 | Total Loss:   2.37 (R²=+0.43, Policy:  2.35) | Val-R²=+0.39 | Policy-Val= 2.20 | v_pred μ=+0.15 σ=0.110  🟡 POLICY-PLATEAU
Epoche 31/100 | Total Loss:   2.36 (R²=+0.44, Policy:  2.35) | Val-R²=+0.40 | Policy-Val= 2.20 | v_pred μ=+0.15 σ=0.110  🟡 POLICY-PLATEAU
Epoche 32/100 | Total Loss:   2.36 (R²=+0.44, Policy:  2.34) | Val-R²=+0.40 | Policy-Val= 2.20 | v_pred μ=+0.15 σ=0.110  🟡 POLICY-PLATEAU
Epoche 33/100 | Total Loss:   2.36 (R²=+0.44, Policy:  2.34) | Val-R²=+0.39 | Policy-Val= 2.20 | v_pred μ=+0.15 σ=0.110  🟡 POLICY-PLATEAU
Epoche 34/100 | Total Loss:   2.35 (R²=+0.44, Policy:  2.34) | Val-R²=+0.39 | Policy-Val= 2.20 | v_pred μ=+0.15 σ=0.110  🟡 POLICY-PLATEAU

⏹️  Early Stopping: Policy plateaut seit Epoche 29 (5 Epochen ohne Fortschritt).

=======================================================
  PHASE 2: VALUE-KALIBRIERUNG (Trunk/Policy eingefroren)
───────────────────────────────────────────────────────
  Kalibrierung  1/50 | Val-R²=+0.410  (bislang bester: Epoche 1)
  Kalibrierung  2/50 | Val-R²=+0.414  (bislang bester: Epoche 1)
  Kalibrierung  3/50 | Val-R²=+0.411  (bislang bester: Epoche 1)
  Kalibrierung  4/50 | Val-R²=+0.410  (bislang bester: Epoche 1)
  Kalibrierung  5/50 | Val-R²=+0.403  (bislang bester: Epoche 1)
  Kalibrierung  6/50 | Val-R²=+0.396  (bislang bester: Epoche 1)
  Kalibrierung  7/50 | Val-R²=+0.401  (bislang bester: Epoche 1)
  Kalibrierung  8/50 | Val-R²=+0.396  (bislang bester: Epoche 1)
  Kalibrierung  9/50 | Val-R²=+0.395  (bislang bester: Epoche 1)
  ⏹️  Kalibrierung gestoppt: Val-R² seit Epoche 1 nicht mehr verbessert (Bestwert 0.410).
  ✅ Value-Head auf besten Kalibrierungs-Stand zurückgesetzt (Epoche 1, Val-R²=0.410).
=======================================================

=======================================================
  TRAINING SUMMARY
=======================================================
  Epochen:       100
  Züge:          1,487,121  (+165,179 Val, nie trainiert)
  Batches/Epoche:5809
───────────────────────────────────────────────────────
  Policy Loss:   2.3378 / 6.18 max  (37.8%)  🟡 Gut
  Policy Val-Loss: 2.2009  (Gap ggü. Train: -0.1369)
  Value Loss:    0.0164  (R²=0.40 ggü. Mittelwert-Baseline)  🟠 Schwaches Signal
  Value Val-R²:  0.41  (Gap ggü. Train: -0.01)  🟢 Train/Val nah beieinander
───────────────────────────────────────────────────────
  ℹ️  Phase 1 Val-R² war in Epoche 1 am besten (0.43), danach Überfitten (normal — Value trainiert bewusst bis zum Ende mit).
  🎯 Phase 2 (Value-Kalibrierung): bester Stand nach Epoche 1, Val-R²=0.41 — Wert oben spiegelt diesen kalibrierten Value-Head wider.
  ⏹️  Early Stopping (Policy-Plateau) nach Epoche 34/100
  🟡 Plateau ab Epoche 29.
     → Für nächste Generation: mehr Sims im Self-Play.
=======================================================

=======================================================
  NETZAUSLASTUNG (Hidden Size: 512)
───────────────────────────────────────────────────────
  Schicht          Dead   Aktiv-Rate        Eff.Rank
  ───────────────────────────────────────────────────
  layer1     0/512 (0%)          40%   220/512 (43%)
  layer2     0/512 (0%)          42%   201/512 (39%)
  layer3    66/512 (13%)          12%   175/512 (34%)
  ───────────────────────────────────────────────────
  🟢 Gesunde Auslastung (Dead 4%, Rank 39%).
=======================================================

✅ Training beendet! Neues Model gespeichert unter:
📂 D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v3.pth
📈 Loss-Verlauf gespeichert unter:
📂 D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v3_loss.png
✅ Exportiert: D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v3.onnx  (input=684, hidden=512, value_hidden=64, opset=13)
📎 Referenz für Rust-Parität: D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v3.onnx.ref.txt

=======================================================
  STUFE 1 vs. STUFE 2 (max. 50 Spiele, 200 Sims, Early-Stop)
───────────────────────────────────────────────────────
🏟️ Mosaic-AI ARENA — Netz vs Netz (Rust) 🏟️
  v3(Stufe1) (Brett 0, 200 Sims, c_puct=1.5, Stufe 1/DFS-Blatt) vs v3(Stufe2) (Brett 1, 200 Sims, c_puct=1.5, Stufe 2/Netz-Value-Blatt) — 50 Spiele
--------------------------------------------------
  #  1/50:  26:0   -> v3(Stufe1)             | Züge 163 | Strength 0.843 | Stand v3(Stufe1) 1:0 v3(Stufe2) | Elo 1013/987
  #  2/50:  24:3   -> v3(Stufe1)             | Züge 160 | Strength 0.820 | Stand v3(Stufe1) 2:0 v3(Stufe2) | Elo 1025/975
  #  3/50:  35:28  -> v3(Stufe1)             | Züge 162 | Strength 0.704 | Stand v3(Stufe1) 3:0 v3(Stufe2) | Elo 1035/965
  #  4/50:  14:36  -> v3(Stufe2)             | Züge 164 | Strength 0.955 | Stand v3(Stufe1) 3:1 v3(Stufe2) | Elo 1017/983
  #  5/50:  10:38  -> v3(Stufe2)             | Züge 160 | Strength 0.978 | Stand v3(Stufe1) 3:2 v3(Stufe2) | Elo 1000/1000
  #  6/50:  49:10  -> v3(Stufe1)             | Züge 162 | Strength 1.000 | Stand v3(Stufe1) 4:2 v3(Stufe2) | Elo 1016/984
  #  7/50:  24:0   -> v3(Stufe1)             | Züge 159 | Strength 0.820 | Stand v3(Stufe1) 5:2 v3(Stufe2) | Elo 1028/972
  #  8/50:  32:7   -> v3(Stufe1)             | Züge 159 | Strength 0.910 | Stand v3(Stufe1) 6:2 v3(Stufe2) | Elo 1040/960
  #  9/50:   0:0   -> v3(Stufe2)             | Züge 156 | Strength 0.100 | Stand v3(Stufe1) 6:3 v3(Stufe2) | Elo 1038/962
  # 10/50:  39:12  -> v3(Stufe1)             | Züge 163 | Strength 0.989 | Stand v3(Stufe1) 7:3 v3(Stufe2) | Elo 1050/950
  # 11/50:  36:20  -> v3(Stufe1)             | Züge 162 | Strength 0.955 | Stand v3(Stufe1) 8:3 v3(Stufe2) | Elo 1061/939
  # 12/50:  39:32  -> v3(Stufe1)             | Züge 157 | Strength 0.749 | Stand v3(Stufe1) 9:3 v3(Stufe2) | Elo 1069/931
  # 13/50:  38:20  -> v3(Stufe1)             | Züge 155 | Strength 0.978 | Stand v3(Stufe1) 10:3 v3(Stufe2) | Elo 1079/921
  # 14/50:  43:20  -> v3(Stufe1)             | Züge 152 | Strength 1.000 | Stand v3(Stufe1) 11:3 v3(Stufe2) | Elo 1088/912
  ⏹️  Vorzeitig entschieden: v3(Stufe1) hat nach 14 Spielen bereits 11 Siege (95%-Signifikanz für >50% Gewinnchance).
--------------------------------------------------
🏆 ERGEBNIS: v3(Stufe1) 11:3 v3(Stufe2) (79% A-Siege) in 266.2s (0.1 Spiele/s)  [vorzeitig nach 14/50 Spielen]
   Ø Score: v3(Stufe1) 29.2 | v3(Stufe2) 16.1
   0:0-Spiele: 1/14 (7.1%)
   Elo: v3(Stufe1) 1088 | v3(Stufe2) 912
=======================================================
```

**Arena vs. v2**

```

```

**Arena vs. Heuristik**

```
PS D:\Archiv\Documents\Projekte\mosaic-AI> python arena.py
🏟️ Mosaic-AI ARENA — Netz vs Heuristik (Rust) 🏟️
  v3 (Brett 0, 200 Sims, Stufe 1/DFS-Blatt) vs Heuristik(s200) (Brett 1, 200 Sims) — 100 Spiele
--------------------------------------------------
  #  1/100:  29:56  -> Heuristik(s200)          | Züge 163 | Strength 1.000 | Stand Netz 0:1 Heur | Elo 984/1016
  #  2/100:  27:50  -> Heuristik(s200)          | Züge 163 | Strength 1.000 | Stand Netz 0:2 Heur | Elo 969/1031
  #  3/100:  18:34  -> Heuristik(s200)          | Züge 157 | Strength 0.933 | Stand Netz 0:3 Heur | Elo 957/1043
  #  4/100:  33:46  -> Heuristik(s200)          | Züge 158 | Strength 0.940 | Stand Netz 0:4 Heur | Elo 946/1054
  #  5/100:  67:43  -> v3                       | Züge 162 | Strength 1.000 | Stand Netz 1:4 Heur | Elo 967/1033
  #  6/100:  31:54  -> Heuristik(s200)          | Züge 158 | Strength 1.000 | Stand Netz 1:5 Heur | Elo 954/1046
  #  7/100:  49:52  -> Heuristik(s200)          | Züge 159 | Strength 0.640 | Stand Netz 1:6 Heur | Elo 946/1054
  #  8/100:  68:62  -> v3                       | Züge 160 | Strength 0.730 | Stand Netz 2:6 Heur | Elo 961/1039
  #  9/100:  10:36  -> Heuristik(s200)          | Züge 161 | Strength 0.955 | Stand Netz 2:7 Heur | Elo 949/1051
  # 10/100:  32:33  -> Heuristik(s200)          | Züge 157 | Strength 0.501 | Stand Netz 2:8 Heur | Elo 943/1057
  # 11/100:  41:54  -> Heuristik(s200)          | Züge 159 | Strength 0.940 | Stand Netz 2:9 Heur | Elo 933/1067
  ⏹️  Vorzeitig entschieden: Heuristik(s200) hat nach 11 Spielen bereits 9 Siege (95%-Signifikanz für >50% Gewinnchance).
--------------------------------------------------
🏆 ERGEBNIS: v3 2:9 Heuristik(s200) (18% Netz-Siege) in 276.7s (0.0 Spiele/s)  [vorzeitig nach 11/100 Spielen]
   Ø Score: v3 36.8 | Heuristik(s200) 47.3
   0:0-Spiele: 0/11 (0.0%)  (Sauberkeits-Indikator)
   Ø Floor-Strafe: v3 13.0 | Heuristik(s200) 11.8
   Elo: v3 933 | Heuristik(s200) 1067
```
