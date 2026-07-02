trainiert mit

- --games 3000 --mode mcts --sims 100
+ --games 2000 --mode network --version v1 --sims 400 --stage 1

512 neuronen pro hidden layer

warm-start v1, Fenster = Bootstrap (300 Dateien) + v1-Self-Play (200 Dateien, 2000 Spiele)

**Netzdaten**

```
Lade Daten aus 500 Dateien...
Datensatz geladen: 643,045 Züge. (Features pro Zug: 684) — 242.7s

🚀 Starte PyTorch Training auf: CUDA
🧠 Netz-Architektur: 684→512→512→512
⚙️  Hyperparameter (config.py):
   Learning Rate : 0.0006
   Value Weight  : 2.5
   Batch Size    : 256
   Value-Target  : tanh((eigen-0.5*gegner)/50) (Endergebnis statt Win/Loss)
📥 Lade altes Model als Startpunkt: alphazero_v1.pth
   Epochen       : 100
🔄 Warm-Start erkannt: Trainiere für 100 Epochen.
[... Epoche 1-49, gleichmäßig fallend, kein auffälliges Value-Loss-Zwischenhoch
     diesmal (v_pred σ wächst stetig 0.131→0.143) ...]

⏹️  Early Stopping: Policy+Value plateaut seit Epoche 44 (5 Epochen ohne Fortschritt).

=======================================================
  TRAINING SUMMARY
=======================================================
  Epochen:       100
  Züge:          643,045
  Batches/Epoche:2512
───────────────────────────────────────────────────────
  Policy Loss:   1.6897 / 6.18 max  (27.4%)  🟡 Gut
  Value Loss:    0.0115  🟢 Sehr gut
───────────────────────────────────────────────────────
  ⏹️  Early Stopping nach Epoche 49/100
  🟡 Plateau ab Epoche 44.
=======================================================

=======================================================
  NETZAUSLASTUNG (Hidden Size: 512)
───────────────────────────────────────────────────────
  Schicht          Dead   Aktiv-Rate        Eff.Rank
  ───────────────────────────────────────────────────
  layer1     0/512 (0%)          39%   222/512 (43%)
  layer2     0/512 (0%)          32%   212/512 (41%)
  layer3    86/512 (17%)          11%   202/512 (40%)
  ───────────────────────────────────────────────────
  🟢 Gesunde Auslastung (Dead 6%, Rank 41%).
=======================================================

✅ Exportiert: alphazero_v2.onnx  (input=684, hidden=512, value_hidden=128, opset=13)
```

**Stage 1 vs. Stage 2**

```
=======================================================
  STAGE-2-REIFEGRAD-SONDE (100 Spiele je Stufe, 400 Sims)
───────────────────────────────────────────────────────
  Stufe 1 (DFS-Blatt):   0:0   7.0% (7/100) | Ø Sieger-Score   8.1
  Stufe 2 (Netz-Value):  0:0  39.0% (39/100) | Ø Sieger-Score   3.5
  Verhältnis 0:0(Stufe2/Stufe1, geglättet): 5.00x
  🔴 ROT — klar noch nicht reif, in Stufe 1 bleiben
=======================================================
```

Vergleichbar mit v1 (35%/5.14x). Weiterhin klar Rot.

**Arena vs. Heuristik**

```
🏟️ Mosaic-AI ARENA — Netz vs Heuristik (Rust) 🏟️
  v2 (Brett 0, 200 Sims, Stufe 1/DFS-Blatt) vs Heuristik(s200) (Brett 1, 200 Sims) — 100 Spiele
--------------------------------------------------
🏆 ERGEBNIS: v2 43:57 Heuristik(s200) (43% Netz-Siege) in 1388.3s (0.1 Spiele/s)
   Ø Score: v2 22.2 | Heuristik(s200) 27.9
   0:0-Spiele: 2/100 (2.0%)  (Sauberkeits-Indikator)
   Ø Floor-Strafe: v2 23.2 | Heuristik(s200) 22.0
   Elo: v2 1008 | Heuristik(s200) 992
```

Einseitige Kollaps-Rate: 19%. Irgendeine Seite ≤5: 24%. Beide ≤5: 2%.

Identischer Sieganteil wie v1 (43%), aber Ø-Score bei v2 höher (22.2 vs. v1s 19.5)
— etwas mehr Substanz im Spiel, auch wenn die Heuristik insgesamt noch klar vorn
liegt (Ø-Score-Rückstand -5.7, ähnlich wie v1s -5.9).

**Arena vs. v1**

```
🏟️ Mosaic-AI ARENA — Netz vs Netz (Rust) 🏟️
  v2 (Brett 0, 200 Sims) vs v1 (Brett 1, 200 Sims) — Stufe 1/DFS-Blatt — 100 Spiele
--------------------------------------------------
🏆 ERGEBNIS: v2 51:49 v1 (51% A-Siege) in 1984.6s (0.1 Spiele/s)
   Ø Score: v2 19.6 | v1 16.9
   0:0-Spiele: 3/100 (3.0%)
   Elo: v2 1017 | v1 983
```

Einseitige Kollaps-Rate: 19%. Irgendeine Seite ≤5: 38%. Beide ≤5: 7%.

**Gate NICHT bestanden.** 51:49 liegt weit unter der vereinbarten ≥60:40-Schwelle
(z=0.2, statistisch Rauschen) — v2 hat v1 nicht klar geschlagen, obwohl der
Ø-Score für v2 spricht (19.6 vs. 16.9). Nach dem vereinbarten Champion-Protokoll
**bleibt v1 Champion**. Nächster Schritt: v1 generiert weitere 2000 Self-Play-
Spiele (kumulativer Netz-Pool wächst auf 4000), v3 wird danach mit einem größeren
v1-Anteil im Fenster trainiert und tritt erneut gegen v1 an.
