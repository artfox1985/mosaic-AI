trainiert mit

- --games 2000 --mode network --version v1c --sims 400 --stage 1
- --games 2000 --mode network --version v4 --sims 400 --stage 1
- --games 2000 --mode network --version v4b --sims 400 --stage 1
- --games 2000 --mode network --version v4c --sims 400 --stage 1
- --games 2000 --mode network --version v4d --sims 400 --stage 1
- -- load v4

512 neuronen pro hidden layer, 2-lagiger Policy-Head, `LEARNING_RATE=0.0004`, `VALUE_WEIGHT=15`
(gleiche Hyperparameter wie der gewählte v7-Lauf).

**Netzdaten**

```
PS D:\Archiv\Documents\Projekte\mosaic-AI> python train.py --name v8 --epochs 100 --load v4
Lade Daten aus 1000 Dateien...
Datensatz geladen: 1511620 Züge. (Features pro Zug: 684) — 609.9s
💾 Speichere HDF5-Cache...
   Value-Ziel-Streuung: σ=0.185 (Varianz=0.0341, zum Vergleich mit v_pred σ unten; Varianz ist die Baseline-MSE bei reiner Mittelwert-Vorhersage)

🚀 Starte PyTorch Training auf: CUDA
🧠 Netz-Architektur: 684→512→512→512
⚙️  Hyperparameter (config.py):
   Learning Rate : 0.0004
   Value Weight  : 15
   Batch Size    : 256
   Value-Target  : tanh((eigen-0.5*gegner)/50) (Endergebnis statt Win/Loss)
📥 Lade altes Model als Startpunkt: alphazero_v4.pth
   ⚠️  Shape-Mismatch, startet frisch: policy_head.0.weight, policy_head.0.bias
   Epochen       : 100
🔄 Warm-Start erkannt: Trainiere für 100 Epochen.
... (100 Epochen, kein Plateau — Policy sinkt bis zum Schluss weiter) ...

=======================================================
  TRAINING SUMMARY
=======================================================
  Epochen:       100
  Züge:          1,511,620
  Batches/Epoche:5904
───────────────────────────────────────────────────────
  Policy Loss:   2.1252 / 6.18 max  (34.4%)  🟡 Gut
  Value Loss:    0.0091  (R²=0.73 ggü. Mittelwert-Baseline)  🟢 Sehr gut
───────────────────────────────────────────────────────
  🟢 Kein Plateau — Policy sinkt noch. Mehr Epochen möglich.
=======================================================

=======================================================
  NETZAUSLASTUNG (Hidden Size: 512)
───────────────────────────────────────────────────────
  Schicht          Dead   Aktiv-Rate        Eff.Rank
  ───────────────────────────────────────────────────
  layer1     0/512 (0%)          42%   219/512 (43%)
  layer2     0/512 (0%)          36%   209/512 (41%)
  layer3    66/512 (13%)          13%   193/512 (38%)
  ───────────────────────────────────────────────────
  🟢 Gesunde Auslastung (Dead 4%, Rank 40%).
=======================================================

✅ Exportiert: D:\Archiv\Documents\Projekte\mosaic-AI\models\alphazero_v8.onnx  (input=684, hidden=512, value_hidden=128, opset=13)
```

Stufe 1 vs Stufe 2 (Reifegrad-Sonde, 100 Spiele je Stufe, 400 Sims)

```
=======================================================
  STAGE-2-REIFEGRAD-SONDE (100 Spiele je Stufe, 400 Sims)
───────────────────────────────────────────────────────
  Stufe 1 (DFS-Blatt):   0:0  16.0% (16/100) | Ø Sieger-Score  13.6
  Stufe 2 (Netz-Value):  0:0  43.0% (43/100) | Ø Sieger-Score   5.7
  Verhältnis 0:0(Stufe2/Stufe1, geglättet): 2.59x
  🟡 GELB — noch nicht reif, Trend über Generationen beobachten
=======================================================
```



**Arena vs. aktuellen Champion v4** (100 Spiele, 200 Sims, Stufe 1/DFS-Blatt)

```
🏆 ERGEBNIS: v8 60:40 v4 (60% A-Siege) in 1889.8s (0.1 Spiele/s)
   Ø Score: v8 26.8 | v4 22.4
   0:0-Spiele: 0/100 (0.0%)
   Elo: v8 996 | v4 1004
```

**Gate bestanden!** 60:40 (z≈2.0, exakt an der Schwelle) — und klar besserer Ø-Score (26.8 vs.
22.4, nicht nur knapp mehr Siege). **v8 ist neuer Champion.** Erste Generation seit v4, die den
Champion signifikant schlägt.

**Arena vs. Heuristik** (100 Spiele, 200 Sims, Stufe 1/DFS-Blatt)

```
🏆 ERGEBNIS: v8 55:45 Heuristik(s200) (55% Netz-Siege) in 1132.2s (0.1 Spiele/s)
   Ø Score: v8 25.7 | Heuristik(s200) 26.6
   0:0-Spiele: 1/100 (1.0%)  (Sauberkeits-Indikator)
   Ø Floor-Strafe: v8 21.7 | Heuristik(s200) 21.3
   Elo: v8 1012 | Heuristik(s200) 988
```

55% (z≈1.0) — schwächer als v7s 59% und Ø-Score diesmal leicht zugunsten der Heuristik
(25.7 vs. 26.6), obwohl v8 den eigentlichen Champion klar schlägt. Kein Widerspruch: die
Heuristik ist ein anderer Gegnertyp als v4 (reine Suche statt gelernter Priors) — das
Champion-Gate (Netz vs. Netz) bleibt das primäre Entscheidungskriterium fürs Protokoll, die
Heuristik-Arena ist ein Gesundheitscheck, kein Ersatz dafür.

**Arena vs. alten Champion v1** (100 Spiele, 200 Sims, Stufe 1/DFS-Blatt — gespielt, weil v8
Champion wurde)

```
🏆 ERGEBNIS: v8 68:32 v1 (68% A-Siege) in 1928.5s (0.1 Spiele/s)
   Ø Score: v8 22.8 | v1 15.1
   0:0-Spiele: 3/100 (3.0%)
   Elo: v8 1073 | v1 927
```

68:32 (z≈3.6), klar, mit deutlich höherem Ø-Score (22.8 vs. 15.1). Bestätigt den
Gesamtfortschritt seit dem Bootstrap-Netz (v4 hatte v1 mit 65:35 geschlagen — v8 übertrifft das
nochmal).

---

**Fazit:** v8 ist neuer Champion (erster Gate-Erfolg seit v4). Champion generiert jetzt eine
neue Self-Play-Runde: `python self_play.py --mode network --model alphazero_v8.onnx --stage 1
--games 6000 --sims 400 --version v8 --threads 0` (läuft). Stage 2 weiterhin 🟡 (Verhältnis
2.59×, leicht besser als v7s Wert, aber noch nicht grün).


