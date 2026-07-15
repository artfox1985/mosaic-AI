trainiert mit

- identisches kuratiertes Fenster wie `v7`: ausschließlich `v2`-Champion-
  Self-Play, 880 Dateien (~8800 Spiele), 792 Trainings-/88 Val-Dateien
  (siehe `v7_eval.md`). Kein neues Self-Play generiert, keine Sims-Änderung
  (weiterhin 400).
- KEIN `--load` (Cold-Start, zufällige Gewichtsinitialisierung) — einziger
  Unterschied zu `v7`, um Warm-Start als limitierenden Faktor zu testen
  (siehe `STAGE2_TODO.md`, Masterplan Spur A).

**Netzdaten**

```
PS D:\Archiv\Documents\Projekte\mosaic-AI> python train.py --name v7cold --epochs 100
Lade Daten aus 792 Dateien...
Datensatz geladen: 1184315 Züge. (Features pro Zug: 684) — 734.2s
Lade Daten aus 88 Dateien...
Datensatz geladen: 131345 Züge. (Features pro Zug: 684) — 87.7s
   Val-Split: 792 Trainings-Dateien / 88 Val-Dateien (1,184,315 / 131,345 Züge)
   Value-Ziel-Streuung: σ=0.153 (Varianz=0.0234)

🚀 Starte PyTorch Training auf: CUDA
🧠 Netz-Architektur: 684→512→512→512
⚙️  Hyperparameter: Learning Rate 0.0004, Value Weight 1, Batch Size 256
🆕 Neues Modell (Cold-Start): Trainiere für 100 Epochen.
...
Epoche 44/100 | ... 🟡 POLICY-PLATEAU

⏹️  Early Stopping: Policy plateaut seit Epoche 39.

=======================================================
  PHASE 2: VALUE-KALIBRIERUNG (Trunk/Policy eingefroren)
───────────────────────────────────────────────────────
  Kalibrierung  1/50 | Val-R²=+0.273  (bislang bester: Epoche 1)
  ⏹️  Kalibrierung gestoppt: Val-R² seit Epoche 1 nicht mehr verbessert (Bestwert 0.273).
  ✅ Value-Head auf besten Kalibrierungs-Stand zurückgesetzt (Epoche 1, Val-R²=0.273).
=======================================================

=======================================================
  TRAINING SUMMARY
=======================================================
  Epochen:       100
  Züge:          1,184,315  (+131,345 Val, nie trainiert)
  Batches/Epoche:4626
───────────────────────────────────────────────────────
  Policy Loss:   2.3380 / 6.18 max  (37.8%)  🟡 Gut
  Policy Val-Loss: 2.2134  (Gap ggü. Train: -0.1246)
  Value Loss:    0.0118  (R²=0.50 ggü. Mittelwert-Baseline)  🟡 Gut
  Value Val-R²:  0.27  (Gap ggü. Train: +0.22)  🟡 spürbarer Train/Val-Abstand — im Auge behalten
───────────────────────────────────────────────────────
  ⏹️  Early Stopping (Policy-Plateau) nach Epoche 44/100
  🟡 Plateau ab Epoche 39.
=======================================================

✅ Exportiert: models/alphazero_v7cold.onnx (input=684, hidden=512, value_hidden=64)
```

Auffällig: 44 Epochen bis zum Plateau (vs. 16 bei `v7` auf demselben Fenster)
— plausibel, da Cold-Start ohne Vorwissen mehr Iterationen braucht, um
überhaupt ein brauchbares Policy-Signal aufzubauen. Value Val-R² (0.27)
liegt niedriger als bei `v7` (0.34) — Cold-Start-Value ist schwächer
kalibriert, was die Arena-Stärke aber offenbar nicht beeinträchtigt.

**Stage 1 vs. Stage 2 (intern)**

```
⏹️  SPRT-Entscheid nach 15 Spielen: v7cold(Stufe1) signifikant staerker (LLR_A=+3.13, LLR_B=-2.38).
🏆 ERGEBNIS: v7cold(Stufe1) 14:1 v7cold(Stufe2) (93% A-Siege) in 280.1s [vorzeitig nach 15/100 Spielen]
   Ø Score: v7cold(Stufe1) 41.7 | v7cold(Stufe2) 13.6
   Elo: v7cold(Stufe1) 1126 | v7cold(Stufe2) 874
```

Noch deutlicher als bei `v7` (73% A-Siege) — beim Cold-Start-Netz ist die
interne Stufe-1-Dominanz sogar stärker ausgeprägt.

**Arena vs. v2 (Stufe 1)**

```
⏹️  SPRT-Entscheid nach 44 Spielen: Gleich stark (beide Seiten nicht signifikant staerker) (LLR_A=-2.46, LLR_B=-2.37).
🏆 ERGEBNIS: v7cold 23:21 v2 (52% A-Siege) in 592.4s  [vorzeitig nach 44/100 Spielen]
   Elo: v7cold 1077 | v2 923
```

Echte Parität mit dem Champion (52%, SPRT bestätigt Gleichstand) — deutlich
näher an v2 als `v7` (42%).

**Arena vs. v7 (Stufe 1) — wichtigster Befund dieser Generation**

```
⏹️  SPRT-Entscheid nach 63 Spielen: v7cold signifikant staerker (LLR_A=-2.54, LLR_B=+2.89).
🏆 ERGEBNIS: v7 22:41 v7cold (35% A-Siege) in 899.1s
   Elo: v7 916 | v7cold 1084
```

Auf IDENTISCHEM Trainingsfenster schlägt Cold-Start Warm-Start SPRT-
signifikant (41:22 aus v7colds Sicht). Erster eindeutiger (nicht "Gleich
stark") Ausgang der ganzen v3-v7-Serie. **v7cold wird nicht Champion**
(v2 bleibt, da nur Parität, kein signifikanter Sieg), aber Cold-Start wird
ab sofort Standard für Kandidaten (siehe `STAGE2_TODO.md`).

**Arena vs. Heuristik**

Nicht getestet in dieser Runde — Fokus lag auf dem Warm-Start-vs-Cold-Start-
Vergleich.
