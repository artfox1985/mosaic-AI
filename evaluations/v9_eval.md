trainiert mit v3+2000 v4+v8, --load v8

512 neuronen pro hidden layer

**Netzzustand**

```
PS D:\Archiv\Documents\Projekte\mosaic-AI> python train.py --name v9 --epochs 100 --load v8
Lade Daten aus 600 Dateien...
Datensatz geladen: 621100 Züge. (Features pro Zug: 684) — 233.2s
💾 Speichere HDF5-Cache...
✅ Cache gespeichert: D:\Archiv\Documents\Projekte\mosaic-AI\data\.cache_6140155b3d61.h5

🚀 Starte PyTorch Training auf: CUDA
🧠 Netz-Architektur: 684→512→512→512
⚙️  Hyperparameter (config.py):
   Learning Rate : 0.0006
   Value Weight  : 0.5
   Batch Size    : 256
   Value-Target  : ±1 (reines Ergebnis)
📥 Lade altes Model als Startpunkt: alphazero_v8.pth
   Epochen       : 100
🔄 Warm-Start erkannt: Trainiere für 100 Epochen.
Epoche  1/100 | Total Loss:   3.02 (Value:  0.41, Policy:  2.81) | v_pred μ=+0.01 σ=0.816
Epoche  2/100 | Total Loss:   2.77 (Value:  0.33, Policy:  2.61) | v_pred μ=+0.01 σ=0.836
Epoche  3/100 | Total Loss:   2.67 (Value:  0.27, Policy:  2.54) | v_pred μ=+0.01 σ=0.866
Epoche  4/100 | Total Loss:   2.61 (Value:  0.23, Policy:  2.49) | v_pred μ=+0.01 σ=0.885
Epoche  5/100 | Total Loss:   2.57 (Value:  0.21, Policy:  2.46) | v_pred μ=+0.01 σ=0.899
Epoche  6/100 | Total Loss:   2.54 (Value:  0.19, Policy:  2.45) | v_pred μ=+0.01 σ=0.908
Epoche  7/100 | Total Loss:   2.52 (Value:  0.18, Policy:  2.43) | v_pred μ=+0.01 σ=0.914
Epoche  8/100 | Total Loss:   2.50 (Value:  0.17, Policy:  2.42) | v_pred μ=+0.01 σ=0.920
Epoche  9/100 | Total Loss:   2.49 (Value:  0.16, Policy:  2.41) | v_pred μ=+0.01 σ=0.923
Epoche 10/100 | Total Loss:   2.48 (Value:  0.15, Policy:  2.40) | v_pred μ=+0.01 σ=0.926
Epoche 11/100 | Total Loss:   2.47 (Value:  0.15, Policy:  2.39) | v_pred μ=+0.01 σ=0.929
Epoche 12/100 | Total Loss:   2.46 (Value:  0.14, Policy:  2.39) | v_pred μ=+0.01 σ=0.931
Epoche 13/100 | Total Loss:   2.45 (Value:  0.14, Policy:  2.38) | v_pred μ=+0.01 σ=0.933
Epoche 14/100 | Total Loss:   2.45 (Value:  0.13, Policy:  2.38) | v_pred μ=+0.01 σ=0.935
Epoche 15/100 | Total Loss:   2.44 (Value:  0.13, Policy:  2.37) | v_pred μ=+0.01 σ=0.937
Epoche 16/100 | Total Loss:   2.43 (Value:  0.13, Policy:  2.37) | v_pred μ=+0.01 σ=0.938
Epoche 17/100 | Total Loss:   2.43 (Value:  0.13, Policy:  2.36) | v_pred μ=+0.01 σ=0.939
Epoche 18/100 | Total Loss:   2.42 (Value:  0.12, Policy:  2.36) | v_pred μ=+0.01 σ=0.940
Epoche 19/100 | Total Loss:   2.41 (Value:  0.12, Policy:  2.35) | v_pred μ=+0.01 σ=0.941
Epoche 20/100 | Total Loss:   2.41 (Value:  0.12, Policy:  2.35) | v_pred μ=+0.01 σ=0.942  🔴 PLATEAU + VALUE SINKT (Overfitting-Risiko)
Epoche 21/100 | Total Loss:   2.41 (Value:  0.12, Policy:  2.35) | v_pred μ=+0.01 σ=0.943  🔴 PLATEAU + VALUE SINKT (Overfitting-Risiko)
Epoche 22/100 | Total Loss:   2.40 (Value:  0.12, Policy:  2.34) | v_pred μ=+0.01 σ=0.944  🔴 PLATEAU + VALUE SINKT (Overfitting-Risiko)
Epoche 23/100 | Total Loss:   2.40 (Value:  0.11, Policy:  2.34) | v_pred μ=+0.01 σ=0.945  🔴 PLATEAU + VALUE SINKT (Overfitting-Risiko)
Epoche 24/100 | Total Loss:   2.40 (Value:  0.11, Policy:  2.34) | v_pred μ=+0.01 σ=0.945  🔴 PLATEAU + VALUE SINKT (Overfitting-Risiko)
Epoche 25/100 | Total Loss:   2.39 (Value:  0.11, Policy:  2.34) | v_pred μ=+0.01 σ=0.946  🔴 PLATEAU + VALUE SINKT (Overfitting-Risiko)

⏹️  Early Stopping: Policy plateaut seit Epoche 20 (5 Epochen ohne Fortschritt).

=======================================================
  TRAINING SUMMARY
=======================================================
  Epochen:       100
  Züge:          621,100
  Batches/Epoche:2427
───────────────────────────────────────────────────────
  Policy Loss:   2.3366 / 6.18 max  (37.8%)  🟡 Gut
  Value Loss:    0.1104  🟠 Schwaches Signal
───────────────────────────────────────────────────────
  ⏹️  Early Stopping nach Epoche 25/100
  🟡 Plateau ab Epoche 20.
     → Für nächste Generation: mehr Sims im Self-Play.
=======================================================

=======================================================
  NETZAUSLASTUNG (Hidden Size: 512)
───────────────────────────────────────────────────────
  Schicht          Dead   Aktiv-Rate        Eff.Rank
  ───────────────────────────────────────────────────
  layer1     0/512 (0%)          35%   218/512 (43%)
  layer2     0/512 (0%)          29%   216/512 (42%)
  layer3    78/512 (15%)           6%   175/512 (34%)
  ───────────────────────────────────────────────────
  🟢 Gesunde Auslastung (Dead 5%, Rank 40%).
=======================================================

✅ Training beendet! Neues Model gespeichert unter:
📂 D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v9.pth
📈 Loss-Verlauf gespeichert unter:
📂 D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v9_loss.png
✅ Exportiert: D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v9.onnx  (input=684, hidden=512, value_hidden=128, opset=13)
📎 Referenz für Rust-Parität: D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v9.onnx.ref.txt
```

**Stage 1 vs. Stage 2**

```
=======================================================
  STAGE-2-REIFEGRAD-SONDE (40 Spiele je Stufe, 400 Sims)
───────────────────────────────────────────────────────
  Stufe 1 (DFS-Blatt):   0:0  15.0% (6/40) | Ø Sieger-Score   8.0
  Stufe 2 (Netz-Value):  0:0  75.0% (30/40) | Ø Sieger-Score   1.9
  Verhältnis 0:0(Stufe2/Stufe1, geglättet): 4.43x
  🔴 ROT — klar noch nicht reif, in Stufe 1 bleiben
=======================================================
```

Verbessert sich gegenüber v8 (~7.25x geglättet, aus einer 100-Spiele-Stichprobe
mit niedrigerer Basisrate) — Trend geht Richtung v7-Niveau (~2.7x), aber
weiterhin klar Rot. Diesmal mit höherer Stufe-1-Basisrate (15% statt v8s 3%)
gemessen, also verlässlicher als der v8-Wert.

**Arena vs. Heuristik**

```
🏟️ Mosaic-AI ARENA — Netz vs Heuristik (Rust) 🏟️
  v9 (Brett 0, 200 Sims, Stufe 1/DFS-Blatt) vs Heuristik(s200) (Brett 1, 200 Sims) — 100 Spiele
--------------------------------------------------
🏆 ERGEBNIS: v9 57:43 Heuristik(s200) (57% Netz-Siege) in 248.9s (0.4 Spiele/s)
   Ø Score: v9 25.5 | Heuristik(s200) 25.2
   0:0-Spiele: 0/100 (0.0%)  (Sauberkeits-Indikator)
   Ø Floor-Strafe: v9 22.4 | Heuristik(s200) 22.0
   Elo: v9 1000 | Heuristik(s200) 1000
```

Kein klarer Fortschritt ggü. v8 (60%, 24.7:23.9) — leicht schwächer im
Sieganteil (57%), Marge im Ø-Score nur noch +0.3 statt +0.8. Bei 100 Spielen im
Rauschbereich, aber jedenfalls keine Verbesserung gegen den externen Maßstab.

**Arena vs. v8**

```
🏟️ Mosaic-AI ARENA — Netz vs Netz (Rust) 🏟️
  v8 (Brett 0, 200 Sims) vs v9 (Brett 1, 200 Sims) — Stufe 1/DFS-Blatt — 100 Spiele
--------------------------------------------------
🏆 ERGEBNIS: v8 46:54 v9 (46% A-Siege) in 304.8s (0.3 Spiele/s)
   Ø Score: v8 14.9 | v9 16.1
   0:0-Spiele: 0/100 (0.0%)
   Elo: v8 985 | v9 1015
```

v9 schlägt v8 klar im direkten Duell (54:46, Elo 1015:985) — Arena-Gate
(Sieg gegen Vorgänger) bestanden, v9 wird neuer Ausgangspunkt für v10.
Auffällig: der Sieg gegen v8 übersetzt sich (noch) nicht in einen klareren
Vorsprung gegen die Heuristik — klassisches Muster, dass eine Generation ihren
direkten Vorgänger schlägt (z.T. auf dessen Spielweise trainiert), ohne dass
sich das 1:1 auf den externen Maßstab überträgt.
