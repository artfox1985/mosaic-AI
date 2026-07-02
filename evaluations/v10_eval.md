trainiert mit 2000 v4+v8+v9, --load v9

512 neuronen pro hidden layer

**Netzzustand**

```
Lade Daten aus 600 Dateien...
Datensatz geladen: 566559 Züge. (Features pro Zug: 684) — 216.7s

🚀 Starte PyTorch Training auf: CUDA
🧠 Netz-Architektur: 684→512→512→512
⚙️  Hyperparameter (config.py):
   Learning Rate : 0.0006
   Value Weight  : 0.5
   Batch Size    : 256
   Value-Target  : ±1 (reines Ergebnis)
📥 Lade altes Model als Startpunkt: alphazero_v9.pth
   Epochen       : 100
🔄 Warm-Start erkannt: Trainiere für 100 Epochen.
[... Epochen 1-24, Value/Policy fallend, ab Epoche 19 PLATEAU + VALUE SINKT ...]
⏹️  Early Stopping: Policy plateaut seit Epoche 19 (5 Epochen ohne Fortschritt).

=======================================================
  TRAINING SUMMARY
=======================================================
  Epochen:       100
  Züge:          566,559
  Batches/Epoche:2214
───────────────────────────────────────────────────────
  Policy Loss:   2.3166 / 6.18 max  (37.5%)  🟡 Gut
  Value Loss:    0.1202  🟠 Schwaches Signal
───────────────────────────────────────────────────────
  ⏹️  Early Stopping nach Epoche 24/100
  🟡 Plateau ab Epoche 19.
=======================================================

=======================================================
  NETZAUSLASTUNG (Hidden Size: 512)
───────────────────────────────────────────────────────
  Schicht          Dead   Aktiv-Rate        Eff.Rank
  ───────────────────────────────────────────────────
  layer1     0/512 (0%)          35%   219/512 (43%)
  layer2     0/512 (0%)          29%   217/512 (42%)
  layer3    70/512 (14%)           6%   180/512 (35%)
  ───────────────────────────────────────────────────
  🟢 Gesunde Auslastung (Dead 5%, Rank 40%).
=======================================================

✅ Exportiert: alphazero_v10.onnx  (input=684, hidden=512, value_hidden=128, opset=13)
```

Value-Loss steigt weiter (v8 0.098 → v9 0.110 → v10 0.120) — kein Einzelausreißer,
sondern ein Trend über 3 Generationen.

**Stage 1 vs. Stage 2**

```
=======================================================
  STAGE-2-REIFEGRAD-SONDE (100 Spiele je Stufe, 400 Sims)
───────────────────────────────────────────────────────
  Stufe 1 (DFS-Blatt):   0:0   6.0% (6/100) | Ø Sieger-Score   5.8
  Stufe 2 (Netz-Value):  0:0  39.0% (39/100) | Ø Sieger-Score   3.1
  Verhältnis 0:0(Stufe2/Stufe1, geglättet): 5.71x
  🔴 ROT — klar noch nicht reif, in Stufe 1 bleiben
=======================================================
```

Absolute Stufe-2-Rate über die Generationen: v7 51.8% → v8 28.0% → v9 75.0%
(n=40, unsicher) → **v10 39.0%** (n=100, 95%-CI ~30-48%) — deutlich besser als
v9, aber die Ratio (5.71x) ist trotzdem schlechter als v9s 4.43x, weil v10s
Stufe-1-Basisrate (6%) niedriger ist als v9s (15%). Weiterhin klar Rot, kein
Grund zum Umstieg.

**Arena vs. Heuristik**

```
🏟️ Mosaic-AI ARENA — Netz vs Heuristik (Rust) 🏟️
  v10 (Brett 0, 200 Sims, Stufe 1/DFS-Blatt) vs Heuristik(s200) (Brett 1, 200 Sims) — 100 Spiele
--------------------------------------------------
🏆 ERGEBNIS: v10 47:53 Heuristik(s200) (47% Netz-Siege) in 239.2s (0.4 Spiele/s)
   Ø Score: v10 23.6 | Heuristik(s200) 26.4
   0:0-Spiele: 0/100 (0.0%)  (Sauberkeits-Indikator)
   Ø Floor-Strafe: v10 23.1 | Heuristik(s200) 20.7
   Elo: v10 1016 | Heuristik(s200) 984
```

**WARNSIGNAL: erste Generation unter 50% gegen die Heuristik.** Monotoner
Abwärtstrend über 4 Generationen: v7 61% → v8 60% → v9 57% → v10 47%. Kein
Einzelausreißer. Ø-Score-Rückstand (-2.8) ist der größte bisher gemessene.
Arbeitshypothese: das Fenster hat sich seit v8 zunehmend von der ursprünglich
heuristik-geprägten v4-Basis entfernt (v2/v3 komplett raus) — das Netz trainiert
immer mehr auf eigenem Self-Play und könnte sich von der Heuristik-Spielweise
wegdriften, ohne dagegen gegengesteuert zu werden.

**Arena vs. v9**

```
🏟️ Mosaic-AI ARENA — Netz vs Netz (Rust) 🏟️
  v9 (Brett 0, 200 Sims) vs v10 (Brett 1, 200 Sims) — Stufe 1/DFS-Blatt — 100 Spiele
--------------------------------------------------
🏆 ERGEBNIS: v9 49:51 v10 (49% A-Siege) in 306.9s (0.3 Spiele/s)
   Ø Score: v9 13.1 | v10 12.4
   0:0-Spiele: 0/100 (0.0%)
   Elo: v9 1004 | v10 996
```

Arena-Gate technisch bestanden (v10 schlägt v9), aber NUR knapp — 51:49 bei
n=100 ist statistisch praktisch eine Münzwurf-Marge, kein überzeugender Sieg.
Zusammen mit dem Heuristik-Rückgang eher ein Warnsignal als eine Bestätigung:
v10 könnte sich auf "v9 schlagen" spezialisiert haben, ohne generell stärker
zu sein.
