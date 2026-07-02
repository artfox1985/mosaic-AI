trainiert mit 3000x mcts sims 100 daten (reines Heuristik-Bootstrap, `data/archive/selfplay_s100_*.pkl`)

512 neuronen pro hidden layer

**Sauberer Neustart (2026-07-02):** alle bisherigen Self-Play-Daten (v8/v9/v11) und
Modell-Checkpoints (v1-v11) gelöscht, nur die reinen Bootstrap-Daten behalten. Grund:
im Rückblick hat kein Netz nach v8 seinen direkten Vorgänger statistisch signifikant
geschlagen (v9 vs. v8: 54:46, z=0.8; v10 vs. v9: 51:49, z=0.2; v11 vs. v10: 45:55,
z=-1.0 — alle im Rauschbereich bei n=100). Neu vereinbarter Gate-Maßstab: ≥60:40
(z≈2.0, ~95%-Niveau) für einen echten Champion-Wechsel. Cold Start (kein `--load`)
mit allen diese Session gefixten Defaults: Value-Target = Partie-Endergebnis
(`tanh((eigen−0.5·gegner)/50)`, `VALUE_SCHEMA_VERSION=8`), `VALUE_WEIGHT=2.5`,
entkoppeltes Early-Stopping (Policy UND Value müssen plateauen).

`VALUE_SCALE` wurde von 25 auf 50 korrigiert, bevor dieses Training lief — nicht aus
aktuellen (schwachen) Spieldaten abgeleitet, sondern an einem groben menschlichen
Referenzwert kalibriert (ab ~100 Punkten gilt ein Ergebnis als sehr gut).

**Netzdaten**

```
📦 Lade HDF5-Cache (300 Dateien)...
Datensatz geladen: 457076 Züge. (Features pro Zug: 684) — 5.3s

🚀 Starte PyTorch Training auf: CUDA
🧠 Netz-Architektur: 684→512→512→512
⚙️  Hyperparameter (config.py):
   Learning Rate : 0.0006
   Value Weight  : 2.5
   Batch Size    : 256
📥 Kein Warm-Start (Cold Start)
   Epochen       : 100
🆕 Neues Modell: Trainiere für 100 Epochen.
[... Epoche 1-75, Value-Loss fällt schnell auf ~0.0095 (Epoche 4), steigt dann
     wieder auf ~0.0115 (Epoche 15-20, Repräsentations-Drift durch dominante
     Policy-Loss im gemeinsamen Rumpf), sinkt danach langsam weiter ...]

⏹️  Early Stopping: Policy+Value plateaut seit Epoche 70 (5 Epochen ohne Fortschritt).

=======================================================
  TRAINING SUMMARY
=======================================================
  Epochen:       100
  Züge:          457,076
  Batches/Epoche:1786
───────────────────────────────────────────────────────
  Policy Loss:   1.4546 / 6.18 max  (23.5%)  🟢 Sehr gut
  Value Loss:    0.0093  ⚠️  Overfitting-Verdacht
───────────────────────────────────────────────────────
  ⏹️  Early Stopping nach Epoche 75/100
  🟡 Plateau ab Epoche 70.
=======================================================

=======================================================
  NETZAUSLASTUNG (Hidden Size: 512)
───────────────────────────────────────────────────────
  Schicht          Dead   Aktiv-Rate        Eff.Rank
  ───────────────────────────────────────────────────
  layer1     0/512 (0%)          38%   222/512 (43%)
  layer2     0/512 (0%)          35%   211/512 (41%)
  layer3    94/512 (18%)          12%   199/512 (39%)
  ───────────────────────────────────────────────────
  🟢 Gesunde Auslastung (Dead 6%, Rank 41%).
=======================================================

✅ Exportiert: alphazero_v1.onnx  (input=684, hidden=512, value_hidden=128, opset=13)
```

Value-Loss-Verlauf ist im Text-Log (2 Nachkommastellen) nicht sichtbar, im
Loss-Plot (`alphazero_v1_loss.png`) aber deutlich: schneller Abfall auf ~0.0095
(Epoche ~4), Anstieg auf ~0.0115 (Epoche ~15-20), langsame Erholung auf 0.0093.
Klassisches Multi-Task-Lern-Verhalten (Policy dominiert früh den gemeinsamen
Rumpf, Value muss sich auf der sich verschiebenden Repräsentation neu einpendeln)
— kein Bug, erholt sich von selbst.

**Stage 1 vs. Stage 2**

```
=======================================================
  STAGE-2-REIFEGRAD-SONDE (100 Spiele je Stufe, 400 Sims)
───────────────────────────────────────────────────────
  Stufe 1 (DFS-Blatt):   0:0   6.0% (6/100) | Ø Sieger-Score   7.6
  Stufe 2 (Netz-Value):  0:0  35.0% (35/100) | Ø Sieger-Score   3.5
  Verhältnis 0:0(Stufe2/Stufe1, geglättet): 5.14x
  🔴 ROT — klar noch nicht reif, in Stufe 1 bleiben
=======================================================
```

Vergleichbar mit v10/v11 (39%/40%). Weiterhin klar Rot, kein Grund zum Umstieg.

**Arena vs. Heuristik**

```
🏟️ Mosaic-AI ARENA — Netz vs Heuristik (Rust) 🏟️
  v1 (Brett 0, 200 Sims, Stufe 1/DFS-Blatt) vs Heuristik(s200) (Brett 1, 200 Sims) — 100 Spiele
--------------------------------------------------
🏆 ERGEBNIS: v1 43:57 Heuristik(s200) (43% Netz-Siege) in 1153.0s (0.1 Spiele/s)
   Ø Score: v1 19.5 | Heuristik(s200) 25.4
   0:0-Spiele: 0/100 (0.0%)  (Sauberkeits-Indikator)
   Ø Floor-Strafe: v1 23.7 | Heuristik(s200) 21.6
   Elo: v1 935 | Heuristik(s200) 1065
```

Einseitige Kollaps-Rate (eine Seite ≤5, andere ≥15): 17%. Irgendeine Seite ≤5: 32%.
Beide ≤5: 6%.

**Einordnung: erwartungsgemäß schwächer als die Heuristik (43%, Ø-Score-Rückstand
-5.9), kein Warnsignal.** v1 ist reine Imitation der Bootstrap-Daten (Heuristik-
Self-Play bei nur 100 Sims — spürbar schwächer als der 200-Sims-Arena-Gegner).
Eine Imitation kann ihr Vorbild bestenfalls erreichen, strukturell kaum übertreffen;
das war hier auch nicht das Ziel. Entscheidend ist jetzt NICHT "mehr vom gleichen
Bootstrap", sondern der Übergang zu echtem Self-Play: v1 hat gesunde
Trainings-Dynamik (kein Dead-Neuron-Problem, sauberes Plateau, keine
Daten-Hunger-Symptome) — der Engpass ist die Qualität der Bootstrap-Quelle
(100 Sims), nicht die Datenmenge. Mehr s100-Daten würden nur eine genauere Kopie
derselben schwachen Quelle ergeben. **Nächster Schritt: Self-Play mit v1
(Netz-vs-Netz, Stufe 1), um über netzgeführte PUCT-Suche + Policy-Priors
Verbesserungen zu entdecken, die reine Heuristik-Imitation nicht liefern kann.**
