date: 15.06.2026  
status: OUTDATED 🔴  <!-- oder VALID 🟢 -->  
git_commit: d72762b 

## Goal
Shaping has changed, we removed the E Synergy Bonus

## 50 Sims
### Rollout Depth = 0, no dynamic sims
~6s runtime per game
```
=======================================================
  VALUE SIMULATION: 50 Dateien
  (500 Spiele aus 50 Datei(en))
───────────────────────────────────────────────────────
  0:0 Spiele:         277 (55.4%)
  Ø Winner-Score:    3.3  (Max: 22)
  Ø Margin:          2.5  (Max: 19)
───────────────────────────────────────────────────────
  📊 EMPFOHLENE PARAMETER:
     --margin_cap       10
     --max_winner_score 10
───────────────────────────────────────────────────────

  [Empfohlen]  margin_cap=10, max_winner=10
  Ø win_val: 0.342  |  Gecappt (=1.0): 44 (8.8%)
  Schwach  (≤0.15):  283 (56.6%)
  Mittel (0.15-0.5):  69 (13.8%)
  Stark    (> 0.5):  148 (29.6%)

  [Standard (15/40)]  margin_cap=15, max_winner=40
  Ø win_val: 0.212  |  Gecappt (=1.0): 0 (0.0%)
  Schwach  (≤0.15):  290 (58.0%)
  Mittel (0.15-0.5): 165 (33.0%)
  Stark    (> 0.5):   45 (9.0%)

=======================================================

=======================================================
  STRAFLEISTEN-BIAS: 50 Dateien
  (Analyse von 50 Datei(en))
=======================================================
───────────────────────────────────────────────────────
  Schritte analysiert:             64,726
  Strafleisten-Zug angeboten:      57,400
  Ø Prob wenn angeboten:           0.151
  Strafleiste war TOP-Wahl:        5,451 (8.4%)
    davon mit Reihen-Alternative:  0
───────────────────────────────────────────────────────
  → 🟡 Strafleiste meist nur wenn keine Alternative (erzwungen, ok)
=======================================================
```
