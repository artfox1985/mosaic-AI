trainiert mit

- --games 11000 --mode mcts --sims 400

value weight 15

50 epochen ohne early stop

**Netzdaten**

```
PS D:\Archiv\Documents\Projekte\mosaic-AI> python train.py --name v1w15_e50 --epochs 50 --no-early-stop
📦 Lade HDF5-Cache (990 Dateien)...
Datensatz geladen: 1501066 Züge. (Features pro Zug: 684) — 17.7s
📦 Lade HDF5-Cache (110 Dateien)...
Datensatz geladen: 167036 Züge. (Features pro Zug: 684) — 1.8s
   Val-Split: 990 Trainings-Dateien / 110 Val-Dateien (1,501,066 / 167,036 Züge)
   Value-Ziel-Streuung: σ=0.183 (Varianz=0.0334, zum Vergleich mit v_pred σ unten; Varianz ist die Baseline-MSE bei reiner Mittelwert-Vorhersage)

🚀 Starte PyTorch Training auf: CUDA
🧠 Netz-Architektur: 684→512→512→512
⚙️  Hyperparameter (config.py):
   Learning Rate : 0.0004
   Value Weight  : 15
   Batch Size    : 256
   Value-Target  : tanh(eigen/50) - 0.1*tanh(gegner/50) (Endergebnis statt Win/Loss)
   Epochen       : 50
🆕 Neues Modell: Trainiere für 50 Epochen.
Epoche  1/50 | Total Loss:   3.21 (R²=+0.68, Policy:  3.05) | Val-R²=+0.29 | v_pred μ=+0.19 σ=0.151
Epoche  2/50 | Total Loss:   3.09 (R²=+0.86, Policy:  3.01) | Val-R²=+0.26 | v_pred μ=+0.19 σ=0.169
Epoche  3/50 | Total Loss:   3.05 (R²=+0.88, Policy:  2.99) | Val-R²=+0.27 | v_pred μ=+0.19 σ=0.172
Epoche  4/50 | Total Loss:   3.02 (R²=+0.89, Policy:  2.97) | Val-R²=+0.26 | v_pred μ=+0.19 σ=0.173
Epoche  5/50 | Total Loss:   3.00 (R²=+0.88, Policy:  2.94) | Val-R²=+0.26 | v_pred μ=+0.19 σ=0.172
Epoche  6/50 | Total Loss:   2.97 (R²=+0.88, Policy:  2.90) | Val-R²=+0.24 | v_pred μ=+0.19 σ=0.171
Epoche  7/50 | Total Loss:   2.92 (R²=+0.87, Policy:  2.86) | Val-R²=+0.26 | v_pred μ=+0.19 σ=0.171
Epoche  8/50 | Total Loss:   2.87 (R²=+0.86, Policy:  2.80) | Val-R²=+0.24 | v_pred μ=+0.19 σ=0.170
Epoche  9/50 | Total Loss:   2.82 (R²=+0.86, Policy:  2.75) | Val-R²=+0.24 | v_pred μ=+0.19 σ=0.170
Epoche 10/50 | Total Loss:   2.77 (R²=+0.86, Policy:  2.70) | Val-R²=+0.25 | v_pred μ=+0.19 σ=0.169
Epoche 11/50 | Total Loss:   2.73 (R²=+0.85, Policy:  2.66) | Val-R²=+0.24 | v_pred μ=+0.19 σ=0.169
Epoche 12/50 | Total Loss:   2.69 (R²=+0.85, Policy:  2.62) | Val-R²=+0.25 | v_pred μ=+0.19 σ=0.169
Epoche 13/50 | Total Loss:   2.66 (R²=+0.85, Policy:  2.58) | Val-R²=+0.25 | v_pred μ=+0.19 σ=0.169
Epoche 14/50 | Total Loss:   2.63 (R²=+0.85, Policy:  2.56) | Val-R²=+0.25 | v_pred μ=+0.19 σ=0.169
Epoche 15/50 | Total Loss:   2.61 (R²=+0.85, Policy:  2.53) | Val-R²=+0.24 | v_pred μ=+0.19 σ=0.169
Epoche 16/50 | Total Loss:   2.59 (R²=+0.85, Policy:  2.51) | Val-R²=+0.25 | v_pred μ=+0.19 σ=0.169
Epoche 17/50 | Total Loss:   2.57 (R²=+0.85, Policy:  2.49) | Val-R²=+0.25 | v_pred μ=+0.19 σ=0.169
Epoche 18/50 | Total Loss:   2.56 (R²=+0.85, Policy:  2.48) | Val-R²=+0.23 | v_pred μ=+0.19 σ=0.169
Epoche 19/50 | Total Loss:   2.54 (R²=+0.85, Policy:  2.47) | Val-R²=+0.25 | v_pred μ=+0.19 σ=0.169
Epoche 20/50 | Total Loss:   2.53 (R²=+0.85, Policy:  2.45) | Val-R²=+0.24 | v_pred μ=+0.19 σ=0.169
Epoche 21/50 | Total Loss:   2.52 (R²=+0.85, Policy:  2.44) | Val-R²=+0.25 | v_pred μ=+0.19 σ=0.169
Epoche 22/50 | Total Loss:   2.51 (R²=+0.85, Policy:  2.43) | Val-R²=+0.25 | v_pred μ=+0.19 σ=0.169
Epoche 23/50 | Total Loss:   2.50 (R²=+0.85, Policy:  2.42) | Val-R²=+0.23 | v_pred μ=+0.19 σ=0.169
Epoche 24/50 | Total Loss:   2.49 (R²=+0.85, Policy:  2.41) | Val-R²=+0.25 | v_pred μ=+0.19 σ=0.169
Epoche 25/50 | Total Loss:   2.48 (R²=+0.85, Policy:  2.41) | Val-R²=+0.22 | v_pred μ=+0.19 σ=0.169
Epoche 26/50 | Total Loss:   2.47 (R²=+0.85, Policy:  2.40) | Val-R²=+0.23 | v_pred μ=+0.19 σ=0.169
Epoche 27/50 | Total Loss:   2.46 (R²=+0.85, Policy:  2.39) | Val-R²=+0.24 | v_pred μ=+0.19 σ=0.169
Epoche 28/50 | Total Loss:   2.46 (R²=+0.86, Policy:  2.38) | Val-R²=+0.23 | v_pred μ=+0.19 σ=0.169
Epoche 29/50 | Total Loss:   2.45 (R²=+0.86, Policy:  2.38) | Val-R²=+0.23 | v_pred μ=+0.19 σ=0.169
Epoche 30/50 | Total Loss:   2.44 (R²=+0.86, Policy:  2.37) | Val-R²=+0.24 | v_pred μ=+0.19 σ=0.169
Epoche 31/50 | Total Loss:   2.44 (R²=+0.86, Policy:  2.37) | Val-R²=+0.23 | v_pred μ=+0.19 σ=0.170
Epoche 32/50 | Total Loss:   2.43 (R²=+0.86, Policy:  2.36) | Val-R²=+0.25 | v_pred μ=+0.19 σ=0.170
Epoche 33/50 | Total Loss:   2.42 (R²=+0.86, Policy:  2.35) | Val-R²=+0.25 | v_pred μ=+0.19 σ=0.170
Epoche 34/50 | Total Loss:   2.42 (R²=+0.86, Policy:  2.35) | Val-R²=+0.23 | v_pred μ=+0.19 σ=0.170
Epoche 35/50 | Total Loss:   2.41 (R²=+0.86, Policy:  2.34) | Val-R²=+0.23 | v_pred μ=+0.19 σ=0.170
Epoche 36/50 | Total Loss:   2.41 (R²=+0.86, Policy:  2.34) | Val-R²=+0.23 | v_pred μ=+0.19 σ=0.170
Epoche 37/50 | Total Loss:   2.40 (R²=+0.86, Policy:  2.33) | Val-R²=+0.23 | v_pred μ=+0.19 σ=0.170
Epoche 38/50 | Total Loss:   2.40 (R²=+0.86, Policy:  2.33) | Val-R²=+0.23 | v_pred μ=+0.19 σ=0.170
Epoche 39/50 | Total Loss:   2.40 (R²=+0.86, Policy:  2.33) | Val-R²=+0.24 | v_pred μ=+0.19 σ=0.170
Epoche 40/50 | Total Loss:   2.39 (R²=+0.86, Policy:  2.32) | Val-R²=+0.22 | v_pred μ=+0.19 σ=0.170  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 41/50 | Total Loss:   2.38 (R²=+0.86, Policy:  2.32) | Val-R²=+0.22 | v_pred μ=+0.19 σ=0.170  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 42/50 | Total Loss:   2.38 (R²=+0.86, Policy:  2.32) | Val-R²=+0.23 | v_pred μ=+0.19 σ=0.170  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 43/50 | Total Loss:   2.38 (R²=+0.86, Policy:  2.31) | Val-R²=+0.22 | v_pred μ=+0.19 σ=0.170  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 44/50 | Total Loss:   2.37 (R²=+0.87, Policy:  2.31) | Val-R²=+0.23 | v_pred μ=+0.19 σ=0.170  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 45/50 | Total Loss:   2.37 (R²=+0.87, Policy:  2.31) | Val-R²=+0.24 | v_pred μ=+0.19 σ=0.170  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 46/50 | Total Loss:   2.36 (R²=+0.87, Policy:  2.30) | Val-R²=+0.24 | v_pred μ=+0.19 σ=0.171  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 47/50 | Total Loss:   2.36 (R²=+0.87, Policy:  2.30) | Val-R²=+0.23 | v_pred μ=+0.19 σ=0.171  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 48/50 | Total Loss:   2.36 (R²=+0.87, Policy:  2.30) | Val-R²=+0.23 | v_pred μ=+0.19 σ=0.171  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 49/50 | Total Loss:   2.36 (R²=+0.87, Policy:  2.29) | Val-R²=+0.23 | v_pred μ=+0.19 σ=0.171  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 50/50 | Total Loss:   2.35 (R²=+0.87, Policy:  2.29) | Val-R²=+0.23 | v_pred μ=+0.19 σ=0.171  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)

=======================================================
  PHASE 2: VALUE-KALIBRIERUNG (Trunk/Policy eingefroren)
───────────────────────────────────────────────────────
  Kalibrierung  1/50 | Val-R²=+0.230  (bislang bester: Epoche 1)
  Kalibrierung  2/50 | Val-R²=+0.226  (bislang bester: Epoche 1)
  Kalibrierung  3/50 | Val-R²=+0.231  (bislang bester: Epoche 1)
  Kalibrierung  4/50 | Val-R²=+0.239  (bislang bester: Epoche 4)
  Kalibrierung  5/50 | Val-R²=+0.226  (bislang bester: Epoche 4)
  Kalibrierung  6/50 | Val-R²=+0.231  (bislang bester: Epoche 4)
  Kalibrierung  7/50 | Val-R²=+0.234  (bislang bester: Epoche 4)
  Kalibrierung  8/50 | Val-R²=+0.228  (bislang bester: Epoche 4)
  Kalibrierung  9/50 | Val-R²=+0.227  (bislang bester: Epoche 4)
  Kalibrierung 10/50 | Val-R²=+0.223  (bislang bester: Epoche 4)
  Kalibrierung 11/50 | Val-R²=+0.227  (bislang bester: Epoche 4)
  Kalibrierung 12/50 | Val-R²=+0.226  (bislang bester: Epoche 4)
  ⏹️  Kalibrierung gestoppt: Val-R² seit Epoche 4 nicht mehr verbessert (Bestwert 0.239).
  ✅ Value-Head auf besten Kalibrierungs-Stand zurückgesetzt (Epoche 4, Val-R²=0.239).
=======================================================

=======================================================
  TRAINING SUMMARY
=======================================================
  Epochen:       50
  Züge:          1,501,066  (+167,036 Val, nie trainiert)
  Batches/Epoche:5863
───────────────────────────────────────────────────────
  Policy Loss:   2.2878 / 6.18 max  (37.0%)  🟡 Gut
  Value Loss:    0.0041  (R²=0.88 ggü. Mittelwert-Baseline)  🟢 Sehr gut
  Value Val-R²:  0.24  (Gap ggü. Train: +0.64)  ⚠️  großer Train/Val-Abstand — Overfitting wahrscheinlich
───────────────────────────────────────────────────────
  ℹ️  Phase 1 Val-R² war in Epoche 1 am besten (0.29), danach Überfitten (normal — Value trainiert bewusst bis zum Ende mit).
  🎯 Phase 2 (Value-Kalibrierung): bester Stand nach Epoche 4, Val-R²=0.24 — Wert oben spiegelt diesen kalibrierten Value-Head wider.
  🟢 Kein Plateau — Policy sinkt noch. Mehr Epochen möglich.
=======================================================

=======================================================
  NETZAUSLASTUNG (Hidden Size: 512)
───────────────────────────────────────────────────────
  Schicht          Dead   Aktiv-Rate        Eff.Rank
  ───────────────────────────────────────────────────
  layer1     0/512 (0%)          42%   220/512 (43%)
  layer2     0/512 (0%)          36%   217/512 (42%)
  layer3    47/512 (9%)          13%   203/512 (40%)
  ───────────────────────────────────────────────────
  🟢 Gesunde Auslastung (Dead 3%, Rank 42%).
=======================================================

✅ Training beendet! Neues Model gespeichert unter:
📂 D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v1w15_e50.pth
📈 Loss-Verlauf gespeichert unter:
📂 D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v1w15_e50_loss.png
✅ Exportiert: D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v1w15_e50.onnx  (input=684, hidden=512, value_hidden=64, opset=13)
📎 Referenz für Rust-Parität: D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v1w15_e50.onnx.ref.txt

=======================================================
  STUFE 1 vs. STUFE 2 (max. 50 Spiele, 200 Sims, Early-Stop)
───────────────────────────────────────────────────────
🏟️ Mosaic-AI ARENA — Netz vs Netz (Rust) 🏟️
  v1w15_e50(Stufe1) (Brett 0, 200 Sims, c_puct=1.5, Stufe 1/DFS-Blatt) vs v1w15_e50(Stufe2) (Brett 1, 200 Sims, c_puct=1.5, Stufe 2/Netz-Value-Blatt) — 50 Spiele
--------------------------------------------------
  #  1/50:  21:0   -> v1w15_e50(Stufe1)      | Züge 160 | Strength 0.786 | Stand v1w15_e50(Stufe1) 1:0 v1w15_e50(Stufe2) | Elo 1013/987
  #  2/50:  37:0   -> v1w15_e50(Stufe1)      | Züge 155 | Strength 0.966 | Stand v1w15_e50(Stufe1) 2:0 v1w15_e50(Stufe2) | Elo 1027/973
  #  3/50:  29:8   -> v1w15_e50(Stufe1)      | Züge 159 | Strength 0.876 | Stand v1w15_e50(Stufe1) 3:0 v1w15_e50(Stufe2) | Elo 1039/961
  #  4/50:  22:3   -> v1w15_e50(Stufe1)      | Züge 156 | Strength 0.798 | Stand v1w15_e50(Stufe1) 4:0 v1w15_e50(Stufe2) | Elo 1049/951
  #  5/50:  44:6   -> v1w15_e50(Stufe1)      | Züge 159 | Strength 1.000 | Stand v1w15_e50(Stufe1) 5:0 v1w15_e50(Stufe2) | Elo 1061/939
  #  6/50:  39:17  -> v1w15_e50(Stufe1)      | Züge 159 | Strength 0.989 | Stand v1w15_e50(Stufe1) 6:0 v1w15_e50(Stufe2) | Elo 1071/929
  #  7/50:   0:0   -> v1w15_e50(Stufe2)      | Züge 150 | Strength 0.100 | Stand v1w15_e50(Stufe1) 6:1 v1w15_e50(Stufe2) | Elo 1069/931
  #  8/50:  43:7   -> v1w15_e50(Stufe1)      | Züge 152 | Strength 1.000 | Stand v1w15_e50(Stufe1) 7:1 v1w15_e50(Stufe2) | Elo 1079/921
  #  9/50:   9:0   -> v1w15_e50(Stufe1)      | Züge 152 | Strength 0.471 | Stand v1w15_e50(Stufe1) 8:1 v1w15_e50(Stufe2) | Elo 1083/917
  # 10/50:  21:16  -> v1w15_e50(Stufe1)      | Züge 158 | Strength 0.486 | Stand v1w15_e50(Stufe1) 9:1 v1w15_e50(Stufe2) | Elo 1087/913
  ⏹️  Vorzeitig entschieden: v1w15_e50(Stufe1) hat nach 10 Spielen bereits 9 Siege (95%-Signifikanz für >50% Gewinnchance).
--------------------------------------------------
🏆 ERGEBNIS: v1w15_e50(Stufe1) 9:1 v1w15_e50(Stufe2) (90% A-Siege) in 138.8s (0.1 Spiele/s)  [vorzeitig nach 10/50 Spielen]
   Ø Score: v1w15_e50(Stufe1) 26.5 | v1w15_e50(Stufe2) 5.7
   0:0-Spiele: 1/10 (10.0%)
   Elo: v1w15_e50(Stufe1) 1087 | v1w15_e50(Stufe2) 913
=======================================================
```

Zwei-Phasen-Training funktioniert wie erwartet: Value trainiert in Phase 1
bewusst bis zum Ende mit (kein Freeze, kein Kollaps), Phase-2-Kalibrierung
konvergiert sauber und bleibt stabil bei Val-R²=0.24 (Bestwert Epoche 4 von
50 Kalibrierungs-Epochen, danach kein Verfall mehr — anders als der alte
chirurgische Freeze, der in jeder Sweep-Variante kollabierte).

**Confounder-Arena (v1b_w15_e50 vs. v1b_w0_e50, A-vs-B, 100 Spiele, kein
Early-Stop, 200 Sims, Stufe 1)**

```
🏆 ERGEBNIS: v1b_w15_e50 50:50 v1b_w0_e50 (50% A-Siege) in 1877.4s
   Ø Score: v1b_w15_e50 32.7 | v1b_w0_e50 31.0
   0:0-Spiele: 0/100 (0.0%)
   Elo: v1b_w15_e50 1020 | v1b_w0_e50 980
```

Exaktes 50:50 bei n=100 — bei gleicher Trainingsdauer (50 Epochen, kein
Early-Stop) bringt VALUE_WEIGHT=15 gegenüber VALUE_WEIGHT=0 keinen messbaren
Vorteil für Stufe-1-Spielstärke. Details und Interpretation siehe
`v1b_w0_e50_eval.md` und `STAGE2_TODO.md`.


**Arena vs. Heuristik**

Nicht getestet — dieses Modell wurde nur im direkten Confounder-Vergleich
gegen v1b_w0_e50 eingesetzt, nicht gegen die Heuristik.
