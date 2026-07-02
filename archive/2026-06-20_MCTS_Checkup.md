date: 20.06.2026  
status: VALID 🟢<!-- oder VALID 🟢 -->  
git_commit: 89a9584 

### 100 Sims, Rollout Depth = 0, dynamic sims = "play"

~35s runtime per game

```
=======================================================
  POLICY QUALITÄT: data/
  (Analyse von 100 Datei(en))
=======================================================
───────────────────────────────────────────────────────
  Analysierte Schritte: 141,965
───────────────────────────────────────────────────────
  Ø Entropie:     1.130 / 6.18 (18.3%)  🟢 Sehr scharf (gut für Training)
  Ø Max-Prob:     0.644  🟡 Moderate Präferenz
  Ø Aktionen >10%:1.6
  Konzentriert (>90%): 45.1%
  Sehr flach   (<30%): 27.2%
───────────────────────────────────────────────────────
  Top 10 Action-IDs (häufig >10% Prob):
    ID    1: 10465×
    ID  481:  8335×
    ID  479:  8308×
    ID  478:  8250×
    ID  480:  8206×
    ID    0:  3012×
    ID  135:  2794×
    ID   39:  2791×
    ID   87:  2759×
    ID   51:  2716×
=======================================================

=======================================================
  STONE-ONLY ANALYSE (strategische Züge)
  (Pflichtaktionen herausgefiltert: Chips, Kuppel, Pass)
───────────────────────────────────────────────────────
  Analysierte Schritte: 69,802 / 141,965 (49%)
───────────────────────────────────────────────────────
  Ø Entropie:     1.356 / 5.48 (24.7%)  🟡 Moderat scharf
  Ø Max-Prob:     0.557
  Konzentriert (>90%): 28.6%
  Sehr flach   (<30%): 31.3%
───────────────────────────────────────────────────────
  Top 10 Stone-IDs (häufig >10% Prob):
    ID  135:  2713×  (rot von Mond → Reihe 4)
    ID   39:  2706×  (blau von Mond → Reihe 4)
    ID   87:  2679×  (gelb von Mond → Reihe 4)
    ID  231:  2665×  (türkis von Mond → Reihe 4)
    ID  183:  2617×  (schwarz von Mond → Reihe 4)
    ID  237:  2561×  (türkis von Mond → Reihe 5)
    ID   45:  2542×  (blau von Mond → Reihe 5)
    ID  195:  2523×  (schwarz von Mond → Reihe 6)
    ID   51:  2516×  (blau von Mond → Reihe 6)
    ID  243:  2498×  (türkis von Mond → Reihe 6)
=======================================================
```

```
=======================================================
  VALUE SIMULATION: data/
  (1000 Spiele aus 100 Datei(en))
───────────────────────────────────────────────────────
  0:0 Spiele:         309 (30.9%)
  Ø Winner-Score:    8.0  (Max: 43)
  Ø Margin:          5.1  (Max: 33)
───────────────────────────────────────────────────────
  📊 EMPFOHLENE PARAMETER:
     --margin_cap       10
     --max_winner_score 15
───────────────────────────────────────────────────────

  [Empfohlen]  margin_cap=10, max_winner=15
  Ø win_val: 0.497  |  Gecappt (=1.0): 126 (12.6%)
  Schwach  (≤0.15):  314 (31.4%)
  Mittel (0.15-0.5): 204 (20.4%)
  Stark    (> 0.5):  482 (48.2%)

  [Standard (15/40)]  margin_cap=15, max_winner=40
  Ø win_val: 0.334  |  Gecappt (=1.0): 1 (0.1%)
  Schwach  (≤0.15):  332 (33.2%)
  Mittel (0.15-0.5): 411 (41.1%)
  Stark    (> 0.5):  257 (25.7%)

=======================================================

=======================================================
  STRAFLEISTEN-BIAS: data/
  (Analyse von 100 Datei(en))
=======================================================
───────────────────────────────────────────────────────
  Schritte analysiert:             141,840
  Strafleisten-Zug angeboten:      132,007
  Ø Prob wenn angeboten:           0.067
  Strafleiste war TOP-Wahl:        7,919 (5.6%)
    davon mit Reihen-Alternative:  0
───────────────────────────────────────────────────────
  → ✅ HARMLOS: angeboten, aber kaum bevorzugt (niedrige Prob)
=======================================================
```

```

```
