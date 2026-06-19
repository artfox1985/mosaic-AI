date: 16.06.2026  
status: OUTDATED 🔴<!-- oder VALID 🟢 -->  
git_commit: 1ec9252

## Goal

Bonus Chips order was invalid

## 50 Sims

### Rollout Depth = 0, no dynamic sims

~6s runtime per game

```
=======================================================
  VALUE SIMULATION: data/
  (1000 Spiele aus 100 Datei(en))
───────────────────────────────────────────────────────
  0:0 Spiele:         538 (53.8%)
  Ø Winner-Score:    3.9  (Max: 29)
  Ø Margin:          3.0  (Max: 26)
───────────────────────────────────────────────────────
  📊 EMPFOHLENE PARAMETER:
     --margin_cap       10
     --max_winner_score 10
───────────────────────────────────────────────────────

  [Empfohlen]  margin_cap=10, max_winner=10
  Ø win_val: 0.363  |  Gecappt (=1.0): 125 (12.5%)
  Schwach  (≤0.15):  548 (54.8%)
  Mittel (0.15-0.5): 143 (14.3%)
  Stark    (> 0.5):  309 (30.9%)

  [Standard (15/40)]  margin_cap=15, max_winner=40
  Ø win_val: 0.230  |  Gecappt (=1.0): 0 (0.0%)
  Schwach  (≤0.15):  559 (55.9%)
  Mittel (0.15-0.5): 308 (30.8%)
  Stark    (> 0.5):  133 (13.3%)

=======================================================

=======================================================
  STRAFLEISTEN-BIAS: data/
  (Analyse von 100 Datei(en))
=======================================================
───────────────────────────────────────────────────────
  Schritte analysiert:             128,883
  Strafleisten-Zug angeboten:      115,570
  Ø Prob wenn angeboten:           0.151
  Strafleiste war TOP-Wahl:        11,019 (8.5%)
    davon mit Reihen-Alternative:  0
───────────────────────────────────────────────────────
  → 🟡 Strafleiste meist nur wenn keine Alternative (erzwungen, ok)
=======================================================
```
