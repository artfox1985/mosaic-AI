trainiert mit

- --games 1000 --mode mcts --sims 400
- --games 1000 --mode network --sims 400 --version v1c --stage 1
- --games 6000 --mode network --sims 400 --version v2 --stage 1
- --games 4000 --mode network --sims 400 --version v2s2 --stage 2
- --games 1400 --mode network --sims 400 --version v2_eval --stage 1
- --load v2

Bootstrapping-Test (siehe evaluations/stage2_investigation.md): 4000 der Spiele
wurden bewusst mit Stufe 2 (Netz-Value-Blatt statt DFS-Blatt) generiert, um zu
prüfen, ob der Value-Head von Zuständen profitiert, die seine eigene Suche
tatsächlich besucht (statt nur DFS-generierte Zustände zu sehen).

**Netzdaten**

```
PS D:\Archiv\Documents\Projekte\mosaic-AI> python train.py --name v6 --epochs 100 --load v2
Lade Daten aus 1561 Dateien...
Datensatz geladen: 2323860 Züge. (Features pro Zug: 684) — 985.4s
💾 Speichere HDF5-Cache...
✅ Cache gespeichert: D:\Archiv\Documents\Projekte\mosaic-AI\data\.cache_41684f3d5171.h5
Lade Daten aus 174 Dateien...
Datensatz geladen: 258887 Züge. (Features pro Zug: 684) — 112.0s
💾 Speichere HDF5-Cache...
✅ Cache gespeichert: D:\Archiv\Documents\Projekte\mosaic-AI\data\.cache_d83fda8b658d.h5
   Val-Split: 1561 Trainings-Dateien / 174 Val-Dateien (2,323,860 / 258,887 Züge)
   Value-Ziel-Streuung: σ=0.149 (Varianz=0.0222, zum Vergleich mit v_pred σ unten; Varianz ist die Baseline-MSE bei reiner Mittelwert-Vorhersage)

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
Epoche  1/100 | Total Loss:   3.00 (R²=+0.37, Policy:  2.99) | Val-R²=+0.33 | Policy-Val= 2.19 | v_pred μ=+0.12 σ=0.091
Epoche  2/100 | Total Loss:   2.97 (R²=+0.39, Policy:  2.96) | Val-R²=+0.34 | Policy-Val= 2.19 | v_pred μ=+0.12 σ=0.094
...
Epoche 55/100 | Total Loss:   2.58 (R²=+0.44, Policy:  2.56) | Val-R²=+0.32 | Policy-Val= 2.21 | v_pred μ=+0.12 σ=0.099  🟡 POLICY-PLATEAU
Epoche 56/100 | Total Loss:   2.57 (R²=+0.44, Policy:  2.56) | Val-R²=+0.31 | Policy-Val= 2.21 | v_pred μ=+0.12 σ=0.099  🟡 POLICY-PLATEAU
Epoche 57/100 | Total Loss:   2.57 (R²=+0.44, Policy:  2.56) | Val-R²=+0.31 | Policy-Val= 2.22 | v_pred μ=+0.12 σ=0.100  🟡 POLICY-PLATEAU
Epoche 58/100 | Total Loss:   2.56 (R²=+0.44, Policy:  2.55) | Val-R²=+0.31 | Policy-Val= 2.21 | v_pred μ=+0.12 σ=0.100  🟡 POLICY-PLATEAU
Epoche 59/100 | Total Loss:   2.56 (R²=+0.44, Policy:  2.55) | Val-R²=+0.32 | Policy-Val= 2.22 | v_pred μ=+0.12 σ=0.100  🟡 POLICY-PLATEAU
Epoche 60/100 | Total Loss:   2.56 (R²=+0.44, Policy:  2.54) | Val-R²=+0.31 | Policy-Val= 2.22 | v_pred μ=+0.12 σ=0.100  🟡 POLICY-PLATEAU

⏹️  Early Stopping: Policy plateaut seit Epoche 55 (5 Epochen ohne Fortschritt).

=======================================================
  PHASE 2: VALUE-KALIBRIERUNG (Trunk/Policy eingefroren)
───────────────────────────────────────────────────────
  Kalibrierung  1/50 | Val-R²=+0.285  (bislang bester: Epoche 1)
  Kalibrierung  2/50 | Val-R²=+0.330  (bislang bester: Epoche 2)
  Kalibrierung  3/50 | Val-R²=+0.329  (bislang bester: Epoche 2)
  ...
  Kalibrierung 10/50 | Val-R²=+0.319  (bislang bester: Epoche 2)
  ⏹️  Kalibrierung gestoppt: Val-R² seit Epoche 2 nicht mehr verbessert (Bestwert 0.330).
  ✅ Value-Head auf besten Kalibrierungs-Stand zurückgesetzt (Epoche 2, Val-R²=0.330).
=======================================================

=======================================================
  TRAINING SUMMARY
=======================================================
  Epochen:       100
  Züge:          2,323,860  (+258,887 Val, nie trainiert)
  Batches/Epoche:9077
───────────────────────────────────────────────────────
  Policy Loss:   2.5430 / 6.18 max  (41.2%)  🟠 Schwaches Signal
  Policy Val-Loss: 2.2150  (Gap ggü. Train: -0.3279)
  Value Loss:    0.0131  (R²=0.41 ggü. Mittelwert-Baseline)  🟡 Gut
  Value Val-R²:  0.33  (Gap ggü. Train: +0.08)  🟢 Train/Val nah beieinander
───────────────────────────────────────────────────────
  ℹ️  Phase 1 Val-R² war in Epoche 2 am besten (0.34), danach Überfitten (normal — Value trainiert bewusst bis zum Ende mit).
  🎯 Phase 2 (Value-Kalibrierung): bester Stand nach Epoche 2, Val-R²=0.33 — Wert oben spiegelt diesen kalibrierten Value-Head wider.
  ⏹️  Early Stopping (Policy-Plateau) nach Epoche 60/100
  🟡 Plateau ab Epoche 55.
     → Für nächste Generation: mehr Sims im Self-Play.
=======================================================

=======================================================
  NETZAUSLASTUNG (Hidden Size: 512)
───────────────────────────────────────────────────────
  Schicht          Dead   Aktiv-Rate        Eff.Rank
  ───────────────────────────────────────────────────
  layer1     0/512 (0%)          40%   219/512 (43%)
  layer2     0/512 (0%)          40%   202/512 (39%)
  layer3    67/512 (13%)          18%   147/512 (29%)
  ───────────────────────────────────────────────────
  🟢 Gesunde Auslastung (Dead 4%, Rank 37%).
=======================================================

✅ Training beendet! Neues Model gespeichert unter:
📂 D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v6.pth
📈 Loss-Verlauf gespeichert unter:
📂 D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v6_loss.png
✅ Exportiert: D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v6.onnx  (input=684, hidden=512, value_hidden=64, opset=13)
📎 Referenz für Rust-Parität: D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v6.onnx.ref.txt

=======================================================
  STUFE 1 vs. STUFE 2 (max. 100 Spiele, 200 Sims, Early-Stop)
───────────────────────────────────────────────────────
🏟️ Mosaic-AI ARENA — Netz vs Netz (Rust) 🏟️
  v6(Stufe1) (Brett 0, 200 Sims, c_puct=1.5, Stufe 1/DFS-Blatt) vs v6(Stufe2) (Brett 1, 200 Sims, c_puct=1.5, Stufe 2/Netz-Value-Blatt) — 100 Spiele  [SPRT p1=0.64, α=0.05, β=0.1]
--------------------------------------------------
  #  1/100:  26:0   -> v6(Stufe1)             | Züge 161 | LLR_A +0.25 | LLR_B -0.33 | ΔElo~+120 | Stand v6(Stufe1) 1:0 v6(Stufe2) | Elo 1016/984
  ...
  # 19/100:  36:8   -> v6(Stufe1)             | Züge 156 | LLR_A +2.96 | LLR_B -2.54 | ΔElo~+251 | Stand v6(Stufe1) 16:3 v6(Stufe2) | Elo 1116/884
  ⏹️  SPRT-Entscheid nach 19 Spielen: v6(Stufe1) signifikant staerker (LLR_A=+2.96, LLR_B=-2.54).
--------------------------------------------------
🏆 ERGEBNIS: v6(Stufe1) 16:3 v6(Stufe2) (84% A-Siege) in 374.8s (0.1 Spiele/s)  [vorzeitig nach 19/100 Spielen]
   Ø Score: v6(Stufe1) 38.7 | v6(Stufe2) 15.5
   0:0-Spiele: 0/19 (0.0%)
   Elo: v6(Stufe1) 1116 | v6(Stufe2) 884
=======================================================
```

**Arena vs. v2 (Stufe 1)**

```
🏟️ Mosaic-AI ARENA — Netz vs Netz (Rust) 🏟️
  v6 (Brett 0, 200 Sims, c_puct=1.5, Stufe 1/DFS-Blatt) vs v2 (Brett 1, 200 Sims, c_puct=1.5, Stufe 1/DFS-Blatt) — 100 Spiele  [SPRT p1=0.64, α=0.05, β=0.1]
--------------------------------------------------
  #  1/100:  33:46  -> v2                     | Züge 164 | LLR_A -0.33 | LLR_B +0.25 | ΔElo~-120 | Stand v6 0:1 v2 | Elo 984/1016
  ...
  # 72/100:  26:15  -> v6                     | Züge 168 | LLR_A -2.46 | LLR_B -2.36 | ΔElo~-9 | Stand v6 35:37 v2 | Elo 1043/957
  ⏹️  SPRT-Entscheid nach 72 Spielen: Gleich stark (beide Seiten nicht signifikant staerker) (LLR_A=-2.46, LLR_B=-2.36).
--------------------------------------------------
🏆 ERGEBNIS: v6 35:37 v2 (49% A-Siege) in 1166.0s (0.1 Spiele/s)  [vorzeitig nach 72/100 Spielen]
   Ø Score: v6 36.3 | v2 35.3
   0:0-Spiele: 0/72 (0.0%)
   Elo: v6 1043 | v2 957
```

**Arena vs. v2 (Stufe 2, Stufe-2-Champion-Referenz da v5(Stufe2) vs. v2(Stufe2) selbst "Gleich stark" war)**

```
🏟️ Mosaic-AI ARENA — Netz vs Netz (Rust) 🏟️
  v6(Stufe2) (Brett 0, 200 Sims, c_puct=1.5, Stufe 2/Netz-Value-Blatt) vs v2(Stufe2) (Brett 1, 200 Sims, c_puct=1.5, Stufe 2/Netz-Value-Blatt) — 100 Spiele  [SPRT p1=0.64, α=0.05, β=0.1]
--------------------------------------------------
  #  1/100:  26:34  -> v2(Stufe2)             | Züge 159 | LLR_A -0.33 | LLR_B +0.25 | ΔElo~-120 | Stand v6(Stufe2) 0:1 v2(Stufe2) | Elo 984/1016
  ...
  # 86/100:   7:33  -> v2(Stufe2)             | Züge 159 | LLR_A -2.36 | LLR_B -2.46 | ΔElo~+16 | Stand v6(Stufe2) 45:41 v2(Stufe2) | Elo 936/1064
  ⏹️  SPRT-Entscheid nach 86 Spielen: Gleich stark (beide Seiten nicht signifikant staerker) (LLR_A=-2.36, LLR_B=-2.46).
--------------------------------------------------
🏆 ERGEBNIS: v6(Stufe2) 45:41 v2(Stufe2) (52% A-Siege) in 3513.3s (0.0 Spiele/s)  [vorzeitig nach 86/100 Spielen]
   Ø Score: v6(Stufe2) 18.2 | v2(Stufe2) 14.2
   0:0-Spiele: 6/86 (7.0%)
   Elo: v6(Stufe2) 936 | v2(Stufe2) 1064
```

Auffällig: 0:0-Rate 7.0% OHNE Explorations-Noise (echtes Arena-Spiel, kein
Self-Play) — bestätigt den in `evaluations/stage2_investigation.md`
dokumentierten Rest-Effekt: auch bei bester Spielstärke (argmax-Visits,
kein Rauschen) bleibt eine reale Stufe-2-Schwäche sichtbar, unabhängig vom
Selfplay-Explorations-Artefakt.

**Fazit v6:** wie schon v3, v4, v5 kann auch v6 den Champion v2 nicht
schlagen — weder auf Stufe 1 (49%) noch auf Stufe 2 (52%, gegen v2 als
Stufe-2-Referenz). Der Bootstrapping-Versuch (4000 Stufe-2-Spiele ins
Fenster gemischt) hat also for sich genommen keinen messbaren
Stärkegewinn gebracht — passt zur Erkenntnis aus der Ursachensuche, dass
die Stufe-2-Schwäche eher an der Kombination aus weichem Value-Signal und
Explorations-Rauschen als an fehlenden Trainingsdaten aus eigener Suche
liegt. **v2 bleibt Champion.**

**Arena vs. Heuristik**

Nicht getestet in dieser Runde — Fokus lag auf dem Stufe-2-Bootstrapping-
Vergleich gegen v2.
