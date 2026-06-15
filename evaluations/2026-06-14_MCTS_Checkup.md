date: 14.06.2026  
status: VALID 🟢  <!-- oder OUTDATED 🔴 -->  
git_commit: baf8e3d 

## Goal
Check which combination of MCTS parameters are a good pick for AlphaZero Bootstrap 

## 50 Sims
### Rollout Depth = 0, dynamic sims
~2s runtime per game
```
=======================================================
  VALUE SIMULATION: 10 Dateien
  (100 Spiele aus 10 Datei(en))
───────────────────────────────────────────────────────
  0:0 Spiele:          59 (59.0%)
  Ø Winner-Score:    3.3  (Max: 17)
  Ø Margin:          2.5  (Max: 17)
───────────────────────────────────────────────────────
  📊 EMPFOHLENE PARAMETER:
     --margin_cap       10
     --max_winner_score 10
───────────────────────────────────────────────────────

  [Empfohlen]  margin_cap=10, max_winner=10
  Ø win_val: 0.326  |  Gecappt (=1.0): 10 (10.0%)
  Schwach  (≤0.15):   61 (61.0%)
  Mittel (0.15-0.5):  13 (13.0%)
  Stark    (> 0.5):   26 (26.0%)

  [Standard (15/40)]  margin_cap=15, max_winner=40
  Ø win_val: 0.210  |  Gecappt (=1.0): 0 (0.0%)
  Schwach  (≤0.15):   63 (63.0%)
  Mittel (0.15-0.5):  26 (26.0%)
  Stark    (> 0.5):   11 (11.0%)

=======================================================
```
### Rollout Depth = 0, no dynamic sims
~6s runtime per game
```
=======================================================
  VALUE SIMULATION: 10 Dateien
  (100 Spiele aus 10 Datei(en))
───────────────────────────────────────────────────────
  0:0 Spiele:          45 (45.0%)
  Ø Winner-Score:    4.8  (Max: 24)
  Ø Margin:          3.5  (Max: 22)
───────────────────────────────────────────────────────
  📊 EMPFOHLENE PARAMETER:
     --margin_cap       10
     --max_winner_score 10
───────────────────────────────────────────────────────

  [Empfohlen]  margin_cap=10, max_winner=10
  Ø win_val: 0.409  |  Gecappt (=1.0): 13 (13.0%)
  Schwach  (≤0.15):   47 (47.0%)
  Mittel (0.15-0.5):  14 (14.0%)
  Stark    (> 0.5):   39 (39.0%)

  [Standard (15/40)]  margin_cap=15, max_winner=40
  Ø win_val: 0.252  |  Gecappt (=1.0): 0 (0.0%)
  Schwach  (≤0.15):   49 (49.0%)
  Mittel (0.15-0.5):  35 (35.0%)
  Stark    (> 0.5):   16 (16.0%)

=======================================================
```
### Rollout Depth = 1, dynamic sims
~8s runtime per game
```
=======================================================
  VALUE SIMULATION: 10 Dateien
  (100 Spiele aus 10 Datei(en))
───────────────────────────────────────────────────────
  0:0 Spiele:          59 (59.0%)
  Ø Winner-Score:    3.4  (Max: 22)
  Ø Margin:          2.7  (Max: 22)
───────────────────────────────────────────────────────
  📊 EMPFOHLENE PARAMETER:
     --margin_cap       10
     --max_winner_score 10
───────────────────────────────────────────────────────

  [Empfohlen]  margin_cap=10, max_winner=10
  Ø win_val: 0.334  |  Gecappt (=1.0): 7 (7.0%)
  Schwach  (≤0.15):   60 (60.0%)
  Mittel (0.15-0.5):   9 (9.0%)
  Stark    (> 0.5):   31 (31.0%)

  [Standard (15/40)]  margin_cap=15, max_winner=40
  Ø win_val: 0.214  |  Gecappt (=1.0): 0 (0.0%)
  Schwach  (≤0.15):   61 (61.0%)
  Mittel (0.15-0.5):  31 (31.0%)
  Stark    (> 0.5):    8 (8.0%)

=======================================================
```
### Rollout Depth = 1, no dynamic sims
~16s runtime per game
```
=======================================================
  VALUE SIMULATION: 10 Dateien
  (100 Spiele aus 10 Datei(en))
───────────────────────────────────────────────────────
  0:0 Spiele:          53 (53.0%)
  Ø Winner-Score:    3.8  (Max: 23)
  Ø Margin:          2.8  (Max: 19)
───────────────────────────────────────────────────────
  📊 EMPFOHLENE PARAMETER:
     --margin_cap       10
     --max_winner_score 10
───────────────────────────────────────────────────────

  [Empfohlen]  margin_cap=10, max_winner=10
  Ø win_val: 0.355  |  Gecappt (=1.0): 12 (12.0%)
  Schwach  (≤0.15):   54 (54.0%)
  Mittel (0.15-0.5):  17 (17.0%)
  Stark    (> 0.5):   29 (29.0%)

  [Standard (15/40)]  margin_cap=15, max_winner=40
  Ø win_val: 0.224  |  Gecappt (=1.0): 0 (0.0%)
  Schwach  (≤0.15):   56 (56.0%)
  Mittel (0.15-0.5):  31 (31.0%)
  Stark    (> 0.5):   13 (13.0%)

=======================================================
```
### Rollout Depth = 5, dynamic sims
~35s runtime per game
```
=======================================================
  VALUE SIMULATION: 10 Dateien
  (100 Spiele aus 10 Datei(en))
───────────────────────────────────────────────────────
  0:0 Spiele:          50 (50.0%)
  Ø Winner-Score:    3.6  (Max: 19)
  Ø Margin:          2.6  (Max: 16)
───────────────────────────────────────────────────────
  📊 EMPFOHLENE PARAMETER:
     --margin_cap       10
     --max_winner_score 10
───────────────────────────────────────────────────────

  [Empfohlen]  margin_cap=10, max_winner=10
  Ø win_val: 0.348  |  Gecappt (=1.0): 9 (9.0%)
  Schwach  (≤0.15):   53 (53.0%)
  Mittel (0.15-0.5):  18 (18.0%)
  Stark    (> 0.5):   29 (29.0%)

  [Standard (15/40)]  margin_cap=15, max_winner=40
  Ø win_val: 0.217  |  Gecappt (=1.0): 0 (0.0%)
  Schwach  (≤0.15):   55 (55.0%)
  Mittel (0.15-0.5):  35 (35.0%)
  Stark    (> 0.5):   10 (10.0%)

=======================================================
```
### Rollout Depth = 5, no dynamic sims
~80s runtime per game
```
=======================================================
  VALUE SIMULATION: 10 Dateien
  (100 Spiele aus 10 Datei(en))
───────────────────────────────────────────────────────
  0:0 Spiele:          50 (50.0%)
  Ø Winner-Score:    4.1  (Max: 20)
  Ø Margin:          3.3  (Max: 20)
───────────────────────────────────────────────────────
  📊 EMPFOHLENE PARAMETER:
     --margin_cap       10
     --max_winner_score 10
───────────────────────────────────────────────────────

  [Empfohlen]  margin_cap=10, max_winner=10
  Ø win_val: 0.405  |  Gecappt (=1.0): 11 (11.0%)
  Schwach  (≤0.15):   50 (50.0%)
  Mittel (0.15-0.5):  13 (13.0%)
  Stark    (> 0.5):   37 (37.0%)

  [Standard (15/40)]  margin_cap=15, max_winner=40
  Ø win_val: 0.244  |  Gecappt (=1.0): 0 (0.0%)
  Schwach  (≤0.15):   50 (50.0%)
  Mittel (0.15-0.5):  39 (39.0%)
  Stark    (> 0.5):   11 (11.0%)

=======================================================
```
## 100 Sims
### Rollout Depth = 0, dynamic sims
~2s runtime per game
```
=======================================================
  VALUE SIMULATION: 10 Dateien
  (100 Spiele aus 10 Datei(en))
───────────────────────────────────────────────────────
  0:0 Spiele:          54 (54.0%)
  Ø Winner-Score:    4.3  (Max: 23)
  Ø Margin:          3.5  (Max: 23)
───────────────────────────────────────────────────────
  📊 EMPFOHLENE PARAMETER:
     --margin_cap       10
     --max_winner_score 15
───────────────────────────────────────────────────────

  [Empfohlen]  margin_cap=10, max_winner=15
  Ø win_val: 0.346  |  Gecappt (=1.0): 8 (8.0%)
  Schwach  (≤0.15):   54 (54.0%)
  Mittel (0.15-0.5):  18 (18.0%)
  Stark    (> 0.5):   28 (28.0%)

  [Standard (15/40)]  margin_cap=15, max_winner=40
  Ø win_val: 0.247  |  Gecappt (=1.0): 0 (0.0%)
  Schwach  (≤0.15):   54 (54.0%)
  Mittel (0.15-0.5):  30 (30.0%)
  Stark    (> 0.5):   16 (16.0%)

=======================================================
```
### Rollout Depth = 1, dynamic sims
~9s runtime per game
```
=======================================================
  VALUE SIMULATION: 10 Dateien
  (100 Spiele aus 10 Datei(en))
───────────────────────────────────────────────────────
  0:0 Spiele:          44 (44.0%)
  Ø Winner-Score:    4.2  (Max: 17)
  Ø Margin:          3.1  (Max: 15)
───────────────────────────────────────────────────────
  📊 EMPFOHLENE PARAMETER:
     --margin_cap       10
     --max_winner_score 10
───────────────────────────────────────────────────────

  [Empfohlen]  margin_cap=10, max_winner=10
  Ø win_val: 0.402  |  Gecappt (=1.0): 9 (9.0%)
  Schwach  (≤0.15):   44 (44.0%)
  Mittel (0.15-0.5):  19 (19.0%)
  Stark    (> 0.5):   37 (37.0%)

  [Standard (15/40)]  margin_cap=15, max_winner=40
  Ø win_val: 0.239  |  Gecappt (=1.0): 0 (0.0%)
  Schwach  (≤0.15):   46 (46.0%)
  Mittel (0.15-0.5):  45 (45.0%)
  Stark    (> 0.5):    9 (9.0%)

=======================================================
```
### Rollout Depth = 1, no dynamic sims
~50s runtime per game
```
=======================================================
  VALUE SIMULATION: 10 Dateien
  (100 Spiele aus 10 Datei(en))
───────────────────────────────────────────────────────
  0:0 Spiele:          46 (46.0%)
  Ø Winner-Score:    4.5  (Max: 21)
  Ø Margin:          3.4  (Max: 18)
───────────────────────────────────────────────────────
  📊 EMPFOHLENE PARAMETER:
     --margin_cap       10
     --max_winner_score 10
───────────────────────────────────────────────────────

  [Empfohlen]  margin_cap=10, max_winner=10
  Ø win_val: 0.409  |  Gecappt (=1.0): 13 (13.0%)
  Schwach  (≤0.15):   48 (48.0%)
  Mittel (0.15-0.5):  16 (16.0%)
  Stark    (> 0.5):   36 (36.0%)

  [Standard (15/40)]  margin_cap=15, max_winner=40
  Ø win_val: 0.249  |  Gecappt (=1.0): 0 (0.0%)
  Schwach  (≤0.15):   48 (48.0%)
  Mittel (0.15-0.5):  36 (36.0%)
  Stark    (> 0.5):   16 (16.0%)

=======================================================
```