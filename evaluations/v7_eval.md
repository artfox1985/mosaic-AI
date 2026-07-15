trainiert mit

- kuratiertes Fenster: ausschließlich `v2`-Champion-Self-Play, 880 Dateien
  (~8800 Spiele) — altes Bootstrap-Material (`v1c`, `s400`), die Stufe-2-
  Bootstrapping-Spiele (`v2s2`) sowie Diagnose-Daten aus Spur B (`v2s2det`)
  bewusst entfernt (siehe `STAGE2_TODO.md`, Masterplan Spur A). Kein neues
  Self-Play generiert, keine Sims-Änderung (weiterhin 400).
- `--load v2` (Warm-Start)

**Netzdaten**

```
PS D:\Archiv\Documents\Projekte\mosaic-AI> python train.py --name v7 --epochs 100 --load v2
Lade Daten aus 792 Dateien...
Datensatz geladen: 1184315 Züge. (Features pro Zug: 684) — 734.2s
Lade Daten aus 88 Dateien...
Datensatz geladen: 131345 Züge. (Features pro Zug: 684) — 87.7s
   Val-Split: 792 Trainings-Dateien / 88 Val-Dateien (1,184,315 / 131,345 Züge)
   Value-Ziel-Streuung: σ=0.153 (Varianz=0.0234)

🚀 Starte PyTorch Training auf: CUDA
🧠 Netz-Architektur: 684→512→512→512
⚙️  Hyperparameter: Learning Rate 0.0004, Value Weight 1, Batch Size 256
📥 Lade altes Model als Startpunkt: alphazero_v2.pth
🔄 Warm-Start erkannt: Trainiere für 100 Epochen.
Epoche  1/100 | Total Loss:   3.03 (R²=+0.35, Policy:  3.02) | Val-R²=+0.35 | Policy-Val= 2.17
...
Epoche 16/100 | Total Loss:   2.90 (R²=+0.47, Policy:  2.89) | Val-R²=+0.33 | Policy-Val= 2.19  🟡 POLICY-PLATEAU

⏹️  Early Stopping: Policy plateaut seit Epoche 11 (5 Epochen ohne Fortschritt).

=======================================================
  PHASE 2: VALUE-KALIBRIERUNG (Trunk/Policy eingefroren)
───────────────────────────────────────────────────────
  Kalibrierung  2/50 | Val-R²=+0.342  (bislang bester: Epoche 2)
  ⏹️  Kalibrierung gestoppt: Val-R² seit Epoche 2 nicht mehr verbessert (Bestwert 0.342).
  ✅ Value-Head auf besten Kalibrierungs-Stand zurückgesetzt (Epoche 2, Val-R²=0.342).
=======================================================

=======================================================
  TRAINING SUMMARY
=======================================================
  Epochen:       100
  Züge:          1,184,315  (+131,345 Val, nie trainiert)
  Batches/Epoche:4626
───────────────────────────────────────────────────────
  Policy Loss:   2.8905 / 6.18 max  (46.8%)  🟠 Schwaches Signal
  Policy Val-Loss: 2.1865  (Gap ggü. Train: -0.7040)
  Value Loss:    0.0132  (R²=0.44 ggü. Mittelwert-Baseline)  🟡 Gut
  Value Val-R²:  0.34  (Gap ggü. Train: +0.09)  🟢 Train/Val nah beieinander
───────────────────────────────────────────────────────
  ⏹️  Early Stopping (Policy-Plateau) nach Epoche 16/100
=======================================================

✅ Exportiert: models/alphazero_v7.onnx (input=684, hidden=512, value_hidden=64)
```

Auffällig: nur 16 Epochen bis zum Plateau (vs. 55-60 bei v5/v6 auf dem
unkuratierten, größeren Fenster) — das kleinere, saubere Fenster konvergiert
deutlich schneller, plausibel weil weniger/keine widersprüchliche
Legacy-Daten mehr im Spiel sind.

**Stage 1 vs. Stage 2 (intern)**

```
🏆 ERGEBNIS: v7(Stufe1) 24:9 v7(Stufe2) (73% A-Siege) [vorzeitig nach 33/100 Spielen]
   Elo: v7(Stufe1) 1076 | v7(Stufe2) 924
```

**Arena vs. v2 (Stufe 1)**

```
⏹️  Ressourcenlimit erreicht (Spiel 100) ohne SPRT-Entscheidung -> Gleich stark (LLR_A=-2.54, LLR_B=+0.52).
🏆 ERGEBNIS: v7 42:58 v2 (42% A-Siege) in 1354.2s
   Ø Score: v7 31.7 | v2 35.2
   0:0-Spiele: 0/100 (0.0%)
   Elo: v7 987 | v2 1013
```

**Arena vs. v7cold (Stufe 1) — wichtigster Befund dieser Generation**

```
⏹️  SPRT-Entscheid nach 63 Spielen: v7cold signifikant staerker (LLR_A=-2.54, LLR_B=+2.89).
🏆 ERGEBNIS: v7 22:41 v7cold (35% A-Siege) in 899.1s
   Elo: v7 916 | v7cold 1084
```

Auf IDENTISCHEM Trainingsfenster ist Cold-Start (siehe `v7cold_eval.md`)
signifikant stärker als Warm-Start — erster eindeutiger (nicht "Gleich
stark") Ausgang der ganzen v3-v7-Serie. Deutet stark darauf hin, dass
Warm-Start selbst der limitierende Faktor war, nicht Fenstergröße/-qualität.
**v7 wird nicht Champion** (v2 bleibt), aber der Vergleich liefert die
wichtigste Erkenntnis dieser Runde: Cold-Start wird ab sofort Standard für
Kandidaten (siehe `STAGE2_TODO.md`).

**Arena vs. Heuristik**

Nicht getestet in dieser Runde — Fokus lag auf dem Warm-Start-vs-Cold-Start-
Vergleich.
