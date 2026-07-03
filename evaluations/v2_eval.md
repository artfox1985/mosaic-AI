trainiert mit

- --games 3000 --mode mcts --sims 100
+ --games 2000 --mode network --version v1 --sims 400 --stage 1
+ -- load v1

512 neuronen pro hidden layer

warm-start v1, Fenster = Bootstrap (300 Dateien) + v1-Self-Play (200 Dateien, 2000 Spiele)

---

## ⚠️ ERSTER VERSUCH VERWORFEN — korrumpierte Daten

Der erste v2-Trainingslauf (unten dokumentiert) beruhte auf v1-Self-Play-Daten, die
zu 98% durch einen Timeout-Bug abgebrochen wurden (siehe STAGE2_TODO.md — 30s-
Wallclock-Guard zu knapp für netzgeführte Suche, nur 35/2000 Partien erreichten
Runde 5). Die aufgezeichneten `scores`/`winner` waren damit größtenteils kein
echtes Ergebnis. Nach dem Fix (Timeout 30s→180s) wurde v1-Self-Play neu generiert
und v2 neu trainiert — **die korrigierten Ergebnisse stehen weiter unten, die
ursprünglichen Zahlen bleiben nur als historische Referenz erhalten.**

**Netzdaten (verworfener Versuch)**

```
Lade Daten aus 500 Dateien...
Datensatz geladen: 643,045 Züge. (Features pro Zug: 684) — 242.7s
...
Policy Loss:   1.6897 / 6.18 max  (27.4%)  🟡 Gut
Value Loss:    0.0115  🟢 Sehr gut
⏹️  Early Stopping nach Epoche 49/100
```

**Arena vs. Heuristik (verworfen):** 43:57, Ø-Score 22.2:27.9
**Arena vs. v1 (verworfen):** 51:49, Ø-Score 19.6:16.9 — Gate nicht bestanden

---

## Korrigierter Versuch (v1-Self-Play neu generiert, Timeout- + BatchNorm-Fix)

Zusätzlicher Fix nötig: `train.py`s DataLoader crashte mit `BatchNorm`-Fehler, weil
die letzte Batch einer Epoche zufällig genau 1 Sample enthielt (Datensatzgröße mod
256 == 1) — behoben mit `drop_last=True`.

**Netzdaten**

```
Datensatz geladen: 759,809 Züge. (Features pro Zug: 684)

🚀 Starte PyTorch Training auf: CUDA
🧠 Netz-Architektur: 684→512→512→512
⚙️  Hyperparameter (config.py):
   Learning Rate : 0.0006
   Value Weight  : 2.5
   Batch Size    : 256
   Value-Target  : tanh((eigen-0.5*gegner)/50) (Endergebnis statt Win/Loss)
📥 Lade altes Model als Startpunkt: alphazero_v1.pth
🔄 Warm-Start erkannt: Trainiere für 100 Epochen.
[... Epoche 1-76 ...]

⏹️  Early Stopping: Policy+Value plateaut seit Epoche 71 (5 Epochen ohne Fortschritt).

=======================================================
  TRAINING SUMMARY
=======================================================
  Epochen:       100
  Züge:          759,809
  Batches/Epoche:2968
───────────────────────────────────────────────────────
  Policy Loss:   1.6941 / 6.18 max  (27.4%)  🟡 Gut
  Value Loss:    0.0134  🟢 Sehr gut
───────────────────────────────────────────────────────
  ⏹️  Early Stopping nach Epoche 76/100
  🟡 Plateau ab Epoche 71.
=======================================================

=======================================================
  NETZAUSLASTUNG (Hidden Size: 512)
───────────────────────────────────────────────────────
  Schicht          Dead   Aktiv-Rate        Eff.Rank
  ───────────────────────────────────────────────────
  layer1     0/512 (0%)          39%   222/512 (43%)
  layer2     0/512 (0%)          32%   210/512 (41%)
  layer3    81/512 (16%)          11%   202/512 (39%)
  ───────────────────────────────────────────────────
  🟢 Gesunde Auslastung (Dead 5%, Rank 41%).
=======================================================

✅ Exportiert: alphazero_v2.onnx  (input=684, hidden=512, value_hidden=128, opset=13)
```

**Stage 1 vs. Stage 2**

```
=======================================================
  STAGE-2-REIFEGRAD-SONDE (100 Spiele je Stufe, 400 Sims)
───────────────────────────────────────────────────────
  Stufe 1 (DFS-Blatt):   0:0  10.0% (10/100) | Ø Sieger-Score  15.5
  Stufe 2 (Netz-Value):  0:0  38.0% (38/100) | Ø Sieger-Score   6.0
  Verhältnis 0:0(Stufe2/Stufe1, geglättet): 3.55x
  🔴 ROT — klar noch nicht reif, in Stufe 1 bleiben
=======================================================
```

Ratio verbessert sich ggü. dem verworfenen Versuch (3.55x vs. 5.00x), Ø Sieger-
Score deutlich höher (15.5/6.0 vs. 8.1/3.5) — plausibel: DFS-Blatt-Basis (Stufe 1)
selbst spielt jetzt auf sauberen Daten trainiert bereits weniger kollapsanfällig.

**Arena vs. Heuristik**

```
🏟️ Mosaic-AI ARENA — Netz vs Heuristik (Rust) 🏟️
  v2 (Brett 0, 200 Sims, Stufe 1/DFS-Blatt) vs Heuristik(s200) (Brett 1, 200 Sims) — 100 Spiele
--------------------------------------------------
🏆 ERGEBNIS: v2 44:56 Heuristik(s200) (44% Netz-Siege) in 1283.1s (0.1 Spiele/s)
   Ø Score: v2 19.6 | Heuristik(s200) 28.4
   0:0-Spiele: 0/100 (0.0%)  (Sauberkeits-Indikator)
   Ø Floor-Strafe: v2 24.1 | Heuristik(s200) 21.5
   Elo: v2 973 | Heuristik(s200) 1027
```

Einseitige Kollaps-Rate: 26%. Irgendeine Seite ≤5: 33%. Beide ≤5: 1%.

44% — vergleichbar mit v1 (43%), Ø-Score etwas niedriger als beim verworfenen
Versuch (19.6 vs. 22.2), aber jetzt auf sauberer Datengrundlage. Kein Fortschritt
ggü. v1 gegen die Heuristik erkennbar.

**Arena vs. v1**

```
🏟️ Mosaic-AI ARENA — Netz vs Netz (Rust) 🏟️
  v2 (Brett 0, 200 Sims) vs v1 (Brett 1, 200 Sims) — Stufe 1/DFS-Blatt — 100 Spiele
--------------------------------------------------
🏆 ERGEBNIS: v2 50:50 v1 (50% A-Siege) in 1988.0s (0.1 Spiele/s)
   Ø Score: v2 20.5 | v1 17.6
   0:0-Spiele: 4/100 (4.0%)
   Elo: v2 1001 | v1 999
```

Einseitige Kollaps-Rate: 17%. Irgendeine Seite ≤5: 33%. Beide ≤5: 6%.

**Gate NICHT bestanden.** Exakt 50:50 (z=0.0) — noch eindeutiger im Rauschbereich
als der verworfene Versuch (51:49). v2 hat v1 nicht geschlagen, trotz besserem
Ø-Score (20.5 vs. 17.6). **v1 bleibt Champion.** Nächster Schritt: v1 generiert
eine weitere Self-Play-Runde (kumulativer sauberer Netz-Pool wächst auf 4000).
