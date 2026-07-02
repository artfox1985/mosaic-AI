trainiert mit 2000 v4+v8+v9 (gleiches Fenster wie v10), --load v10

512 neuronen pro hidden layer

**Kernänderung ggü. v10: Value-Target umgestellt** (siehe STAGE2_TODO.md Abschnitt D,
Punkt 0) — von reinem Win/Loss `±1` auf Partie-Endergebnis-Punkte
`tanh((eigener − 0.5·gegnerischer Endstand) / 25)`, als Ziel für JEDEN Schritt der
Partie (delayed reward, inkl. Wertungsplatten). `VALUE_WEIGHT` musste dafür von 0.5
auf 2.5 hochskaliert werden (neues Target hat ~4.6x kleinere Streuung als das alte
±1-Ziel). Early-Stopping zusätzlich entkoppelt: stoppt jetzt erst, wenn Policy UND
Value plateauen (vorher nur Policy — hat den Value-Head beim ersten Versuch mitten
in der Konvergenz abgeschnitten, siehe unten).

**Erster Trainingsversuch (verworfen)**

Mit dem alten Early-Stopping (nur Policy-Plateau) brach das Training nach 15 Epochen
ab, während v_pred σ noch am Wachsen war (0.154→0.174, Ziel-Streuung ~0.22) — der
Value-Head war mitten in der Konvergenz. Folge: Stage-2-Sonde verschlechterte sich
deutlich (0:0-Rate 56% statt v10s 39%, Ø Sieger-Score 2.1 statt 3.1). Daraufhin
Early-Stopping-Logik korrigiert (siehe train.py) und neu trainiert.

**Zweiter Trainingsversuch (verwendet)**

```
🚀 Starte PyTorch Training auf: CUDA
🧠 Netz-Architektur: 684→512→512→512
⚙️  Hyperparameter (config.py):
   Learning Rate : 0.0006
   Value Weight  : 2.5
   Batch Size    : 256
   Value-Target  : tanh(Punktediff/20) (Marge statt reinem Win/Loss)
📥 Lade altes Model als Startpunkt: alphazero_v10.pth
   Epochen       : 100
🔄 Warm-Start erkannt: Trainiere für 100 Epochen.
[... Epochen 1-100, kein Early Stopping — Policy sinkt bis zuletzt langsam weiter,
     Value σ wächst kontinuierlich 0.154 → 0.190 ...]

=======================================================
  TRAINING SUMMARY
=======================================================
  Epochen:       100
  Züge:          566,559
  Batches/Epoche:2214
───────────────────────────────────────────────────────
  Policy Loss:   2.2217 / 6.18 max  (36.0%)  🟡 Gut
  Value Loss:    0.0128  🟢 Sehr gut
───────────────────────────────────────────────────────
  🟢 Kein Plateau — Policy sinkt noch. Mehr Epochen möglich.
=======================================================

=======================================================
  NETZAUSLASTUNG (Hidden Size: 512)
───────────────────────────────────────────────────────
  Schicht          Dead   Aktiv-Rate        Eff.Rank
  ───────────────────────────────────────────────────
  layer1     0/512 (0%)          36%   217/512 (42%)
  layer2     0/512 (0%)          29%   214/512 (42%)
  layer3    66/512 (13%)           6%   182/512 (36%)
  ───────────────────────────────────────────────────
  🟢 Gesunde Auslastung (Dead 4%, Rank 40%).
=======================================================

✅ Exportiert: alphazero_v11.onnx  (input=684, hidden=512, value_hidden=128, opset=13)
```

Policy Loss 2.2217 (v10: 2.3166) — leicht besser. Value Loss 0.0128 ist auf der neuen
Skala nicht direkt mit v10s 0.1202 (alte ±1-Skala) vergleichbar.

**Stage 1 vs. Stage 2**

```
=======================================================
  STAGE-2-REIFEGRAD-SONDE (100 Spiele je Stufe, 400 Sims)
───────────────────────────────────────────────────────
  Stufe 1 (DFS-Blatt):   0:0   5.0% (5/100) | Ø Sieger-Score   7.3
  Stufe 2 (Netz-Value):  0:0  40.0% (40/100) | Ø Sieger-Score   3.5
  Verhältnis 0:0(Stufe2/Stufe1, geglättet): 6.83x
  🔴 ROT — klar noch nicht reif, in Stufe 1 bleiben
=======================================================
```

Vergleichbar mit v10 (39.0% / 5.71x) — leicht besserer Ø Sieger-Score (3.5 vs. 3.1).
Weiterhin klar Rot, kein Grund zum Umstieg auf Stufe 2.

**Arena vs. Heuristik**

```
🏟️ Mosaic-AI ARENA — Netz vs Heuristik (Rust) 🏟️
  v11 (Brett 0, 200 Sims, Stufe 1/DFS-Blatt) vs Heuristik(s200) (Brett 1, 200 Sims) — 100 Spiele
--------------------------------------------------
🏆 ERGEBNIS: v11 55:45 Heuristik(s200) (55% Netz-Siege) in 1296.0s (0.1 Spiele/s)
   Ø Score: v11 24.6 | Heuristik(s200) 26.1
   0:0-Spiele: 0/100 (0.0%)  (Sauberkeits-Indikator)
   Ø Floor-Strafe: v11 23.4 | Heuristik(s200) 21.2
   Elo: v11 1032 | Heuristik(s200) 968
```

Einseitige Kollaps-Rate (eine Seite ≤5, andere ≥15): 15% (v10: 18%). Irgendeine
Seite ≤5: 25% (v10: 21%, leicht schlechter). Beide ≤5: 3% (v10: 0%).

**Deutliche Verbesserung ggü. v10:** erstmals seit v8 wieder über 50% (v7 61% →
v8 60% → v9 57% → v10 47% → **v11 55%**). Ø-Score-Rückstand verkleinert sich von
-2.8 (v10) auf -1.5. Ø-Score selbst steigt (24.6 vs. v10s 23.6) — passt zur Zielsetzung
("mehr Punkte", nicht nur "öfter gewinnen").

**Arena vs. v10**

```
🏟️ Mosaic-AI ARENA — Netz vs Netz (Rust) 🏟️
  v11 (Brett 0, 200 Sims) vs v10 (Brett 1, 200 Sims) — Stufe 1/DFS-Blatt — 100 Spiele
--------------------------------------------------
🏆 ERGEBNIS: v11 45:55 v10 (45% A-Siege) in 2005.7s (0.0 Spiele/s)
   Ø Score: v11 21.4 | v10 23.4
   0:0-Spiele: 2/100 (2.0%)
   Elo: v11 978 | v10 1022
```

Einseitige Kollaps-Rate: 22% (v10 vs. v9 war 20%, ähnlich). Irgendeine Seite ≤5:
36% (v10 vs. v9 war 46% — verbessert). Beide ≤5: 3%.

**Klassisches Arena-Gate ("schlägt den Vorgänger") NICHT bestanden** — v11 verliert
45:55 gegen v10, auch im Ø-Score (21.4 vs. 23.4). Gemischtes Bild: gegen die
Heuristik (der breitere, strukturell andere Gegner) ist v11 klar besser geworden,
im direkten Duell mit dem unmittelbaren Vorgänger schlechter. Das deckt sich mit der
Beobachtung aus v10 (STAGE2_TODO.md): "Sieg gegen den unmittelbaren Vorgänger" ist
ein instabiles, teils nicht-transitives Signal (spezifische Netz-vs-Netz-Matchups
können von allgemeiner Spielstärke abweichen) — genau der Grund, warum das
Lösungskonzept in Abschnitt D vorschlägt, das Gate um Ø-Score und Kollaps-Rate zu
erweitern statt nur Win/Loss zu betrachten. Nach den erweiterten Kriterien (Ø-Score
vs. Heuristik ↑, Kollaps-Rate stabil/leicht verbessert, Value-Head strukturell
gesünder als beim ersten v11-Versuch) spricht mehr für v11 als dagegen — die
Entscheidung, ob v11 die neue Baseline wird, ist aber ein Nutzer-Call.
