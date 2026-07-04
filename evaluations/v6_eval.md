trainiert mit

+ --games 2000 --mode network --version v1b --sims 400 --stage 1
+ --games 2000 --mode network --version v1c --sims 400 --stage 1
+ --games 2000 --mode network --version v4 --sims 400 --stage 1
+ --games 2000 --mode network --version v4b --sims 400 --stage 1
+ -- load v4

512 neuronen pro hidden layer

**Netzdaten**

```
PS D:\Archiv\Documents\Projekte\mosaic-AI> python train.py --name v6 --epochs 100 --load v4
Lade Daten aus 800 Dateien...
Datensatz geladen: 1210259 Züge. (Features pro Zug: 684) — 459.9s
💾 Speichere HDF5-Cache...
✅ Cache gespeichert: D:\Archiv\Documents\Projekte\mosaic-AI\data\.cache_ce201e7276da.h5

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
Epoche  1/100 | Total Loss:   2.85 (Value:  0.02, Policy:  2.79) | v_pred μ=+0.10 σ=0.105
Epoche  2/100 | Total Loss:   2.64 (Value:  0.02, Policy:  2.58) | v_pred μ=+0.10 σ=0.108
Epoche  3/100 | Total Loss:   2.54 (Value:  0.02, Policy:  2.49) | v_pred μ=+0.10 σ=0.110
Epoche  4/100 | Total Loss:   2.47 (Value:  0.02, Policy:  2.42) | v_pred μ=+0.10 σ=0.111
Epoche  5/100 | Total Loss:   2.42 (Value:  0.02, Policy:  2.37) | v_pred μ=+0.10 σ=0.112
Epoche  6/100 | Total Loss:   2.38 (Value:  0.02, Policy:  2.33) | v_pred μ=+0.10 σ=0.112
Epoche  7/100 | Total Loss:   2.36 (Value:  0.02, Policy:  2.30) | v_pred μ=+0.10 σ=0.113
Epoche  8/100 | Total Loss:   2.33 (Value:  0.02, Policy:  2.28) | v_pred μ=+0.10 σ=0.113
Epoche  9/100 | Total Loss:   2.31 (Value:  0.02, Policy:  2.26) | v_pred μ=+0.10 σ=0.114
Epoche 10/100 | Total Loss:   2.30 (Value:  0.02, Policy:  2.25) | v_pred μ=+0.10 σ=0.114
Epoche 11/100 | Total Loss:   2.29 (Value:  0.02, Policy:  2.23) | v_pred μ=+0.10 σ=0.115
Epoche 12/100 | Total Loss:   2.28 (Value:  0.02, Policy:  2.22) | v_pred μ=+0.10 σ=0.115
Epoche 13/100 | Total Loss:   2.27 (Value:  0.02, Policy:  2.22) | v_pred μ=+0.10 σ=0.115
Epoche 14/100 | Total Loss:   2.26 (Value:  0.02, Policy:  2.21) | v_pred μ=+0.10 σ=0.116
Epoche 15/100 | Total Loss:   2.25 (Value:  0.02, Policy:  2.20) | v_pred μ=+0.10 σ=0.116
Epoche 16/100 | Total Loss:   2.25 (Value:  0.02, Policy:  2.20) | v_pred μ=+0.10 σ=0.116
Epoche 17/100 | Total Loss:   2.24 (Value:  0.02, Policy:  2.19) | v_pred μ=+0.10 σ=0.117
Epoche 18/100 | Total Loss:   2.24 (Value:  0.02, Policy:  2.18) | v_pred μ=+0.10 σ=0.117
Epoche 19/100 | Total Loss:   2.23 (Value:  0.02, Policy:  2.18) | v_pred μ=+0.10 σ=0.117
Epoche 20/100 | Total Loss:   2.23 (Value:  0.02, Policy:  2.18) | v_pred μ=+0.10 σ=0.118
Epoche 21/100 | Total Loss:   2.22 (Value:  0.02, Policy:  2.17) | v_pred μ=+0.10 σ=0.118
Epoche 22/100 | Total Loss:   2.22 (Value:  0.02, Policy:  2.17) | v_pred μ=+0.10 σ=0.118
Epoche 23/100 | Total Loss:   2.21 (Value:  0.02, Policy:  2.16) | v_pred μ=+0.10 σ=0.118
Epoche 24/100 | Total Loss:   2.21 (Value:  0.02, Policy:  2.16) | v_pred μ=+0.10 σ=0.118  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 25/100 | Total Loss:   2.21 (Value:  0.02, Policy:  2.16) | v_pred μ=+0.10 σ=0.119  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 26/100 | Total Loss:   2.20 (Value:  0.02, Policy:  2.15) | v_pred μ=+0.10 σ=0.119  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 27/100 | Total Loss:   2.20 (Value:  0.02, Policy:  2.15) | v_pred μ=+0.10 σ=0.119  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 28/100 | Total Loss:   2.20 (Value:  0.02, Policy:  2.15) | v_pred μ=+0.10 σ=0.120  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 29/100 | Total Loss:   2.19 (Value:  0.02, Policy:  2.14) | v_pred μ=+0.10 σ=0.120  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 30/100 | Total Loss:   2.19 (Value:  0.02, Policy:  2.14) | v_pred μ=+0.10 σ=0.120  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 31/100 | Total Loss:   2.19 (Value:  0.02, Policy:  2.14) | v_pred μ=+0.10 σ=0.120  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 32/100 | Total Loss:   2.19 (Value:  0.02, Policy:  2.14) | v_pred μ=+0.10 σ=0.120  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 33/100 | Total Loss:   2.19 (Value:  0.02, Policy:  2.14) | v_pred μ=+0.10 σ=0.120  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 34/100 | Total Loss:   2.18 (Value:  0.02, Policy:  2.13) | v_pred μ=+0.10 σ=0.121  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 35/100 | Total Loss:   2.18 (Value:  0.02, Policy:  2.13) | v_pred μ=+0.10 σ=0.121  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 36/100 | Total Loss:   2.18 (Value:  0.02, Policy:  2.13) | v_pred μ=+0.10 σ=0.121  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 37/100 | Total Loss:   2.18 (Value:  0.02, Policy:  2.13) | v_pred μ=+0.10 σ=0.121  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 38/100 | Total Loss:   2.18 (Value:  0.02, Policy:  2.13) | v_pred μ=+0.10 σ=0.121  🔵 POLICY-PLATEAU, VALUE LERNT NOCH (kein Stopp)
Epoche 39/100 | Total Loss:   2.17 (Value:  0.02, Policy:  2.13) | v_pred μ=+0.10 σ=0.121  🟡 PLATEAU (Policy+Value)
Epoche 40/100 | Total Loss:   2.17 (Value:  0.02, Policy:  2.12) | v_pred μ=+0.10 σ=0.122  🟡 PLATEAU (Policy+Value)
Epoche 41/100 | Total Loss:   2.17 (Value:  0.02, Policy:  2.12) | v_pred μ=+0.10 σ=0.122  🟡 PLATEAU (Policy+Value)
Epoche 42/100 | Total Loss:   2.17 (Value:  0.02, Policy:  2.12) | v_pred μ=+0.10 σ=0.122  🟡 PLATEAU (Policy+Value)
Epoche 43/100 | Total Loss:   2.17 (Value:  0.02, Policy:  2.12) | v_pred μ=+0.10 σ=0.122  🟡 PLATEAU (Policy+Value)
Epoche 44/100 | Total Loss:   2.16 (Value:  0.02, Policy:  2.11) | v_pred μ=+0.10 σ=0.122  🟡 PLATEAU (Policy+Value)

⏹️  Early Stopping: Policy+Value plateaut seit Epoche 39 (5 Epochen ohne Fortschritt).

=======================================================
  TRAINING SUMMARY
=======================================================
  Epochen:       100
  Züge:          1,210,259
  Batches/Epoche:4727
───────────────────────────────────────────────────────
  Policy Loss:   2.1145 / 6.18 max  (34.2%)  🟡 Gut
  Value Loss:    0.0196  🟢 Sehr gut
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
  layer1     0/512 (0%)          40%   220/512 (43%)
  layer2     0/512 (0%)          31%   208/512 (41%)
  layer3    66/512 (13%)           9%   202/512 (39%)
  ───────────────────────────────────────────────────
  🟢 Gesunde Auslastung (Dead 4%, Rank 41%).
=======================================================

✅ Training beendet! Neues Model gespeichert unter:
📂 D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v6.pth
📈 Loss-Verlauf gespeichert unter:
📂 D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v6_loss.png
⚠️  ONNX-Export übersprungen (manuell nachholbar: python export_onnx.py --version v6): MosaicNet.__init__() got an unexpected keyword argument 'policy_hidden'
PS D:\Archiv\Documents\Projekte\mosaic-AI> python export_onnx.py --version v6
⚠️  Shape-Mismatch (alte Head-Architektur?), startet zufällig: policy_head.0.weight, policy_head.0.bias
D:\Archiv\Documents\Projekte\mosaic-AI\export_onnx.py:54: DeprecationWarning: You are using the legacy TorchScript-based ONNX export. Starting in PyTorch 2.9, the new torch.export-based ONNX exporter has become the default. Learn more about the new export logic: https://docs.pytorch.org/docs/stable/onnx_export.html. For exporting control flow: https://pytorch.org/tutorials/beginner/onnx/export_control_flow_model_to_onnx_tutorial.html
  torch.onnx.export(
✅ Exportiert: D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v6.onnx  (input=684, hidden=512, value_hidden=128, opset=13)
📎 Referenz für Rust-Parität: D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v6.onnx.ref.txt
```

**Stage 1**

```
PS D:\Archiv\Documents\Projekte\mosaic-AI> python -m utils.diagnosis

📋 DIAGNOSIS — Trainingsdaten Analyse
───────────────────────────────────────────────────────
  [1] Sanity Check  — alle Daten im data/ Ordner
  [2] Sanity Check  — Datei(en) auswählen (mehrere möglich)
  [3] Policy Qualität — alle Daten im data/ Ordner
  [4] Policy Qualität — Datei(en) auswählen (mehrere möglich)
  [5] Ergebnis-Übersicht + Strafleisten-Bias — alle Daten
  [6] Ergebnis-Übersicht + Strafleisten-Bias — Datei(en) auswählen
───────────────────────────────────────────────────────
  Auswahl (1/2/3/4/5/6): 6
  Öffne Datei-Dialog (Mehrfach-Auswahl mit Strg/Shift)...
  ✓ 10 Datei(en) gewählt.

=======================================================
  ERGEBNIS-ÜBERSICHT: 10 Dateien
  (100 Spiele aus 10 Datei(en))
───────────────────────────────────────────────────────
  0:0 Spiele:          16 (16.0%)
  Ø Winner-Score:    14.2  (Max: 46)
  Ø Margin:          8.0  (Max: 31)

=======================================================

=======================================================
  STRAFLEISTEN-BIAS: 10 Dateien
  (Analyse von 10 Datei(en))
=======================================================
───────────────────────────────────────────────────────
  Schritte analysiert:             15,080
  Strafleisten-Zug angeboten:      16,900
  Ø Prob wenn angeboten:           0.065
  Strafleiste war TOP-Wahl:        658 (4.4%)
    davon mit Reihen-Alternative:  0
───────────────────────────────────────────────────────
  → ✅ HARMLOS: angeboten, aber kaum bevorzugt (niedrige Prob)
=======================================================
```

**Stage 2**

```
PS D:\Archiv\Documents\Projekte\mosaic-AI> python -m utils.diagnosis 
📋 DIAGNOSIS — Trainingsdaten Analyse
───────────────────────────────────────────────────────
 [1] Sanity Check — alle Daten im data/ Ordner
 [2] Sanity Check — Datei(en) auswählen (mehrere möglich)
 [3] Policy Qualität — alle Daten im data/ Ordner
 [4] Policy Qualität — Datei(en) auswählen (mehrere möglich)
 [5] Ergebnis-Übersicht + Strafleisten-Bias — alle Daten
 [6] Ergebnis-Übersicht + Strafleisten-Bias — Datei(en) auswählen
───────────────────────────────────────────────────────
 Auswahl (1/2/3/4/5/6): 6
 Öffne Datei-Dialog (Mehrfach-Auswahl mit Strg/Shift)...
 ✓ 10 Datei(en) gewählt.
ERGEBNIS-ÜBERSICHT: 10 Dateien
 (100 Spiele aus 10 Datei(en))
───────────────────────────────────────────────────────
 0:0 Spiele: 36 (36.0%)
 Ø Winner-Score: 6.0 (Max: 37)
 Ø Margin: 3.5 (Max: 28) 
======================================================= 
=======================================================
 STRAFLEISTEN-BIAS: 10 Dateien
 (Analyse von 10 Datei(en))
=======================================================
───────────────────────────────────────────────────────
 Schritte analysiert: 14,733
 Strafleisten-Zug angeboten: 17,510
 Ø Prob wenn angeboten: 0.076
 Strafleiste war TOP-Wahl: 635 (4.3%)
 davon mit Reihen-Alternative: 0
───────────────────────────────────────────────────────
 → ✅ HARMLOS: angeboten, aber kaum bevorzugt (niedrige Prob)
=======================================================
```

-> Verhältnis Stage 1 zu Stage 2: 2.25 -> gelbe Ampel

  



**Arena vs. Heuristik**

```

```

**Arena vs. Champion (v4)**

```

```
