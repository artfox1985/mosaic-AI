trainiert mit

- --games 3000 --mode mcts --sims 100
- --games 2000 --mode network --version v1 --sims 400 --stage 1
- --games 2000 --mode network --version v1 --sims 400 --stage 1
- -- load v1

512 neuronen pro hidden layer

warm-start v1 (v1 ist weiterhin Champion), Fenster = Bootstrap (300) + v1 (200) +
v1b (200) = 700 Dateien, 4000 saubere Netz-Self-Play-Spiele

**Netzdaten**

```
Datensatz geladen: 1,062,599 Züge. (Features pro Zug: 684)

🚀 Starte PyTorch Training auf: CUDA
🧠 Netz-Architektur: 684→512→512→512
⚙️  Hyperparameter (config.py):
   Learning Rate : 0.0006
   Value Weight  : 2.5
   Batch Size    : 256
   Value-Target  : tanh((eigen-0.5*gegner)/50) (Endergebnis statt Win/Loss)
📥 Lade altes Model als Startpunkt: alphazero_v1.pth
🔄 Warm-Start erkannt: Trainiere für 100 Epochen.
[... Epoche 1-73 ...]

⏹️  Early Stopping: Policy+Value plateaut seit Epoche 68 (5 Epochen ohne Fortschritt).

=======================================================
  TRAINING SUMMARY
=======================================================
  Epochen:       100
  Züge:          1,062,599
  Batches/Epoche:4150
───────────────────────────────────────────────────────
  Policy Loss:   1.8517 / 6.18 max  (30.0%)  🟡 Gut
  Value Loss:    0.0167  🟢 Sehr gut
───────────────────────────────────────────────────────
  ⏹️  Early Stopping nach Epoche 73/100
  🟡 Plateau ab Epoche 68.
     → Für nächste Generation: mehr Sims im Self-Play.
=======================================================

=======================================================
  NETZAUSLASTUNG (Hidden Size: 512)
───────────────────────────────────────────────────────
  Schicht          Dead   Aktiv-Rate        Eff.Rank
  ───────────────────────────────────────────────────
  layer1     0/512 (0%)          39%   221/512 (43%)
  layer2     0/512 (0%)          32%   208/512 (41%)
  layer3    74/512 (14%)          10%   200/512 (39%)
  ───────────────────────────────────────────────────
  🟢 Gesunde Auslastung (Dead 5%, Rank 41%).
=======================================================

✅ Exportiert: alphazero_v3.onnx  (input=684, hidden=512, value_hidden=128, opset=13)
```

**Stage 1 vs. Stage 2**

```
=======================================================
  STAGE-2-REIFEGRAD-SONDE (100 Spiele je Stufe, 400 Sims)
───────────────────────────────────────────────────────
  Stufe 1 (DFS-Blatt):   0:0   9.0% (9/100) | Ø Sieger-Score  17.2
  Stufe 2 (Netz-Value):  0:0  33.0% (33/100) | Ø Sieger-Score   6.6
  Verhältnis 0:0(Stufe2/Stufe1, geglättet): 3.40x
  🔴 ROT — klar noch nicht reif, in Stufe 1 bleiben
=======================================================
```

Ratio verbessert sich weiter (v1: 5.14x → v2: 3.55x → v3: 3.40x), Ø Sieger-Score
in Stufe 1 steigt deutlich (7.6 → 8.1 → 17.2) — Trend in die richtige Richtung,
aber weiterhin klar Rot.

**Arena vs. Heuristik**

```
🏟️ Mosaic-AI ARENA — Netz vs Heuristik (Rust) 🏟️
  v3 (Brett 0, 200 Sims, Stufe 1/DFS-Blatt) vs Heuristik(s200) (Brett 1, 200 Sims) — 100 Spiele
--------------------------------------------------
🏆 ERGEBNIS: v3 47:53 Heuristik(s200) (47% Netz-Siege) in 1282.6s (0.1 Spiele/s)
   Ø Score: v3 25.6 | Heuristik(s200) 29.9
   0:0-Spiele: 0/100 (0.0%)  (Sauberkeits-Indikator)
   Ø Floor-Strafe: v3 21.7 | Heuristik(s200) 20.8
   Elo: v3 982 | Heuristik(s200) 1018
```

Einseitige Kollaps-Rate: 15%. Irgendeine Seite ≤5: 23%. Beide ≤5: 1%.

**Deutliche Verbesserung ggü. v1/v2:** Sieganteil 43% → 44% → **47%**, Ø-Score
steigt kontinuierlich (19.5 → 19.6 → **25.6**). Mehr Self-Play-Daten (4000 statt
2000) zeigen den erwarteten Effekt — noch nicht über 50%, aber klar im Aufwärtstrend.

**Arena vs. Champion (v1)**

```
🏟️ Mosaic-AI ARENA — Netz vs Netz (Rust) 🏟️
  v3 (Brett 0, 200 Sims) vs v1 (Brett 1, 200 Sims) — Stufe 1/DFS-Blatt — 100 Spiele
--------------------------------------------------
🏆 ERGEBNIS: v3 53:47 v1 (53% A-Siege) in 2103.3s (0.0 Spiele/s)
   Ø Score: v3 22.1 | v1 19.6
   0:0-Spiele: 4/100 (4.0%)
   Elo: v3 1019 | v1 981
```

Einseitige Kollaps-Rate: 15%. Irgendeine Seite ≤5: 30%. Beide ≤5: 6%.

**Gate NICHT bestanden.** 53:47 ist näher an der Schwelle als v2s 50:50 (z=0.6 vs.
z=0.0), aber immer noch weit unter ≥60:40 (z≈2.0 nötig). **v1 bleibt Champion.**
Trend über die drei Kandidaten (v2: 50:50 → v3: 53:47) geht klar in Richtung
"v1 wird zunehmend geschlagen" — mit mehr Daten könnte ein v4 die Schwelle
erreichen. Nächster Schritt: v1 generiert eine dritte Self-Play-Runde (kumulativer
sauberer Netz-Pool wächst auf 6000 — erreicht die vom Nutzer gesetzte Obergrenze).
