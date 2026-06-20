date: 19.06.2026  
status: OUTDATED 🔴<!-- oder VALID 🟢 -->  
git_commit: 2aa5b85

## Goal

## 100 Sims

### Rollout Depth = 0, dynamic sims = "play"

~35s runtime per game

```
=======================================================
  VALUE SIMULATION: data/
  (10 Spiele aus 1 Datei(en))
───────────────────────────────────────────────────────
  0:0 Spiele:           2 (20.0%)
  Ø Winner-Score:    7.6  (Max: 18)
  Ø Margin:          3.8  (Max: 11)
───────────────────────────────────────────────────────
  📊 EMPFOHLENE PARAMETER:
     --margin_cap       10
     --max_winner_score 15
───────────────────────────────────────────────────────

  [Empfohlen]  margin_cap=10, max_winner=15
  Ø win_val: 0.480  |  Gecappt (=1.0): 0 (0.0%)
  Schwach  (≤0.15):    3 (30.0%)
  Mittel (0.15-0.5):   2 (20.0%)
  Stark    (> 0.5):    5 (50.0%)

  [Standard (15/40)]  margin_cap=15, max_winner=40
  Ø win_val: 0.298  |  Gecappt (=1.0): 0 (0.0%)
  Schwach  (≤0.15):    3 (30.0%)
  Mittel (0.15-0.5):   5 (50.0%)
  Stark    (> 0.5):    2 (20.0%)

=======================================================

=======================================================
  STRAFLEISTEN-BIAS: data/
  (Analyse von 1 Datei(en))
=======================================================
───────────────────────────────────────────────────────
  Schritte analysiert:             1,420
  Strafleisten-Zug angeboten:      1,362
  Ø Prob wenn angeboten:           0.073
  Strafleiste war TOP-Wahl:        93 (6.5%)
    davon mit Reihen-Alternative:  0
───────────────────────────────────────────────────────
  → ✅ HARMLOS: angeboten, aber kaum bevorzugt (niedrige Prob)
=======================================================
```

```

```

```
Kämpfer: ['MCTS 1 s100-d0', 'MCTS 2 s100-d0']
--------------------------------------------------

⚔️ NEUES MATCHUP: MCTS 1 s100-d0 vs MCTS 2 s100-d0 (100 Spiele)
  #1/100:  35.8s | Züge: 149 | Strength: 1.000 |  17:1   -> Sieger: MCTS 1 s100-d0
  #2/100:  32.8s | Züge: 141 | Strength: 1.000 |  34:8   -> Sieger: MCTS 2 s100-d0
  #3/100:  36.0s | Züge: 152 | Strength: 0.100 |   2:2   -> Sieger: MCTS 2 s100-d0
  #4/100:  34.5s | Züge: 143 | Strength: 1.000 |  29:3   -> Sieger: MCTS 2 s100-d0
  #5/100:  32.3s | Züge: 141 | Strength: 0.100 |   0:0   -> Sieger: MCTS 2 s100-d0
  #6/100:  35.6s | Züge: 150 | Strength: 0.685 |  20:23  -> Sieger: MCTS 1 s100-d0
  #7/100:  32.6s | Züge: 136 | Strength: 0.100 |   0:0   -> Sieger: MCTS 2 s100-d0
  #8/100:  33.7s | Züge: 147 | Strength: 1.000 |   8:42  -> Sieger: MCTS 1 s100-d0
  #9/100:  35.9s | Züge: 143 | Strength: 0.775 |  12:7   -> Sieger: MCTS 1 s100-d0
  #10/100:  43.6s | Züge: 143 | Strength: 0.370 |   0:3   -> Sieger: MCTS 1 s100-d0
  #11/100:  41.7s | Züge: 143 | Strength: 0.370 |   3:0   -> Sieger: MCTS 1 s100-d0
  #12/100:  35.1s | Züge: 137 | Strength: 0.100 |   0:0   -> Sieger: MCTS 1 s100-d0
  #13/100:  36.3s | Züge: 144 | Strength: 1.000 |   0:23  -> Sieger: MCTS 2 s100-d0
  #14/100:  38.8s | Züge: 145 | Strength: 0.460 |   4:0   -> Sieger: MCTS 2 s100-d0
  #15/100:  37.4s | Züge: 145 | Strength: 0.595 |   6:1   -> Sieger: MCTS 1 s100-d0
  #16/100:  35.7s | Züge: 141 | Strength: 0.100 |   0:0   -> Sieger: MCTS 1 s100-d0
  #17/100:  35.4s | Züge: 142 | Strength: 0.730 |   7:0   -> Sieger: MCTS 1 s100-d0
  #18/100:  34.5s | Züge: 142 | Strength: 0.820 |   8:0   -> Sieger: MCTS 2 s100-d0
  #19/100:  34.3s | Züge: 144 | Strength: 1.000 |  41:8   -> Sieger: MCTS 1 s100-d0
  #20/100:  34.1s | Züge: 144 | Strength: 0.775 |   9:3   -> Sieger: MCTS 2 s100-d0
  #21/100:  35.5s | Züge: 142 | Strength: 0.280 |   0:2   -> Sieger: MCTS 2 s100-d0
  #22/100:  37.0s | Züge: 149 | Strength: 0.730 |  11:15  -> Sieger: MCTS 1 s100-d0
  #23/100:  32.0s | Züge: 139 | Strength: 1.000 |  29:2   -> Sieger: MCTS 1 s100-d0
  #24/100:  35.5s | Züge: 144 | Strength: 1.000 |   5:20  -> Sieger: MCTS 1 s100-d0
  #25/100:  36.1s | Züge: 146 | Strength: 1.000 |   0:14  -> Sieger: MCTS 2 s100-d0
  #26/100:  36.4s | Züge: 150 | Strength: 1.000 |   0:19  -> Sieger: MCTS 1 s100-d0
  #27/100:  35.7s | Züge: 149 | Strength: 1.000 |  18:44  -> Sieger: MCTS 2 s100-d0
  #28/100:  34.5s | Züge: 144 | Strength: 0.100 |   0:0   -> Sieger: MCTS 1 s100-d0
  #29/100:  34.4s | Züge: 139 | Strength: 1.000 |  19:0   -> Sieger: MCTS 1 s100-d0
  #30/100:  33.0s | Züge: 143 | Strength: 1.000 |   0:18  -> Sieger: MCTS 1 s100-d0
  #31/100:  35.4s | Züge: 139 | Strength: 0.100 |   0:0   -> Sieger: MCTS 2 s100-d0
  #32/100:  36.7s | Züge: 144 | Strength: 0.100 |   0:0   -> Sieger: MCTS 1 s100-d0
  #33/100:  35.5s | Züge: 144 | Strength: 0.325 |   4:3   -> Sieger: MCTS 1 s100-d0
  #34/100:  36.1s | Züge: 139 | Strength: 0.100 |   0:0   -> Sieger: MCTS 1 s100-d0
  #35/100:  33.2s | Züge: 138 | Strength: 1.000 |   8:18  -> Sieger: MCTS 2 s100-d0
  #36/100:  37.0s | Züge: 145 | Strength: 1.000 |  21:6   -> Sieger: MCTS 2 s100-d0
  #37/100:  33.4s | Züge: 144 | Strength: 1.000 |   9:24  -> Sieger: MCTS 2 s100-d0
  #38/100:  36.1s | Züge: 147 | Strength: 1.000 |  37:12  -> Sieger: MCTS 2 s100-d0
  #39/100:  32.6s | Züge: 138 | Strength: 0.370 |   3:0   -> Sieger: MCTS 1 s100-d0
  #40/100:  34.3s | Züge: 139 | Strength: 0.280 |   2:0   -> Sieger: MCTS 2 s100-d0
  #41/100:  35.5s | Züge: 142 | Strength: 0.820 |   5:11  -> Sieger: MCTS 2 s100-d0
  #42/100:  34.1s | Züge: 134 | Strength: 0.100 |   0:0   -> Sieger: MCTS 1 s100-d0
  #43/100:  35.5s | Züge: 148 | Strength: 0.820 |  17:11  -> Sieger: MCTS 1 s100-d0
  #44/100:  33.8s | Züge: 145 | Strength: 0.640 |  10:8   -> Sieger: MCTS 2 s100-d0
  #45/100:  34.4s | Züge: 141 | Strength: 0.100 |   0:0   -> Sieger: MCTS 2 s100-d0
  #46/100:  32.1s | Züge: 140 | Strength: 1.000 |  25:0   -> Sieger: MCTS 2 s100-d0
  #47/100:  32.1s | Züge: 140 | Strength: 0.100 |   0:0   -> Sieger: MCTS 2 s100-d0
  #48/100:  34.9s | Züge: 145 | Strength: 0.100 |   0:0   -> Sieger: MCTS 1 s100-d0
  #49/100:  33.8s | Züge: 143 | Strength: 1.000 |   0:35  -> Sieger: MCTS 2 s100-d0
  #50/100:  33.6s | Züge: 134 | Strength: 0.100 |   0:0   -> Sieger: MCTS 1 s100-d0
  #51/100:  35.7s | Züge: 141 | Strength: 0.640 |   6:0   -> Sieger: MCTS 1 s100-d0
  #52/100:  35.1s | Züge: 143 | Strength: 0.550 |   4:7   -> Sieger: MCTS 1 s100-d0
  #53/100:  35.7s | Züge: 141 | Strength: 1.000 |  18:5   -> Sieger: MCTS 1 s100-d0
  #54/100:  32.9s | Züge: 143 | Strength: 0.820 |   0:8   -> Sieger: MCTS 1 s100-d0
  #55/100:  31.0s | Züge: 137 | Strength: 1.000 |  21:8   -> Sieger: MCTS 1 s100-d0
  #56/100:  35.4s | Züge: 136 | Strength: 1.000 |  12:0   -> Sieger: MCTS 2 s100-d0
  #57/100:  38.0s | Züge: 148 | Strength: 0.100 |   0:0   -> Sieger: MCTS 2 s100-d0
  #58/100:  36.7s | Züge: 141 | Strength: 1.000 |  10:38  -> Sieger: MCTS 1 s100-d0
  #59/100:  35.2s | Züge: 135 | Strength: 0.550 |   6:2   -> Sieger: MCTS 1 s100-d0
  #60/100:  34.6s | Züge: 147 | Strength: 0.460 |   7:6   -> Sieger: MCTS 2 s100-d0
  #61/100:  36.8s | Züge: 150 | Strength: 0.640 |   8:10  -> Sieger: MCTS 2 s100-d0
  #62/100:  37.7s | Züge: 147 | Strength: 1.000 |  10:22  -> Sieger: MCTS 1 s100-d0
  #63/100:  35.7s | Züge: 146 | Strength: 1.000 |   4:16  -> Sieger: MCTS 2 s100-d0
  #64/100:  31.4s | Züge: 140 | Strength: 0.100 |   0:0   -> Sieger: MCTS 1 s100-d0
  #65/100:  36.4s | Züge: 144 | Strength: 0.550 |   5:0   -> Sieger: MCTS 1 s100-d0
  #66/100:  37.3s | Züge: 144 | Strength: 0.190 |   0:1   -> Sieger: MCTS 1 s100-d0
  #67/100:  35.7s | Züge: 141 | Strength: 0.820 |  10:4   -> Sieger: MCTS 1 s100-d0
  #68/100:  36.1s | Züge: 147 | Strength: 0.190 |   0:1   -> Sieger: MCTS 1 s100-d0
  #69/100:  34.2s | Züge: 143 | Strength: 0.460 |   0:4   -> Sieger: MCTS 2 s100-d0
  #70/100:  34.7s | Züge: 144 | Strength: 0.685 |  15:12  -> Sieger: MCTS 2 s100-d0
  #71/100:  35.1s | Züge: 140 | Strength: 1.000 |   0:30  -> Sieger: MCTS 2 s100-d0
  #72/100:  31.9s | Züge: 138 | Strength: 1.000 |   0:10  -> Sieger: MCTS 1 s100-d0
  #73/100:  36.5s | Züge: 139 | Strength: 0.100 |   0:0   -> Sieger: MCTS 2 s100-d0
  #74/100:  34.0s | Züge: 139 | Strength: 0.100 |   0:0   -> Sieger: MCTS 1 s100-d0
  #75/100:  35.9s | Züge: 153 | Strength: 1.000 |  19:0   -> Sieger: MCTS 1 s100-d0
  #76/100:  36.4s | Züge: 146 | Strength: 0.550 |   5:0   -> Sieger: MCTS 2 s100-d0
  #77/100:  37.9s | Züge: 147 | Strength: 0.100 |   2:2   -> Sieger: MCTS 2 s100-d0
  #78/100:  37.4s | Züge: 145 | Strength: 0.820 |  10:4   -> Sieger: MCTS 2 s100-d0
  #79/100:  34.9s | Züge: 141 | Strength: 1.000 |  15:0   -> Sieger: MCTS 1 s100-d0
  #80/100:  34.9s | Züge: 146 | Strength: 0.685 |   9:12  -> Sieger: MCTS 1 s100-d0
  #81/100:  33.3s | Züge: 139 | Strength: 0.955 |  10:19  -> Sieger: MCTS 2 s100-d0
  #82/100:  32.2s | Züge: 134 | Strength: 0.100 |   0:0   -> Sieger: MCTS 1 s100-d0
  #83/100:  38.0s | Züge: 143 | Strength: 0.820 |  12:6   -> Sieger: MCTS 1 s100-d0
  #84/100:  34.3s | Züge: 149 | Strength: 0.820 |   8:14  -> Sieger: MCTS 1 s100-d0
  #85/100:  38.4s | Züge: 142 | Strength: 0.100 |   0:0   -> Sieger: MCTS 2 s100-d0
  #86/100:  34.5s | Züge: 147 | Strength: 0.730 |   7:0   -> Sieger: MCTS 2 s100-d0
  #87/100:  36.3s | Züge: 146 | Strength: 0.775 |   3:9   -> Sieger: MCTS 2 s100-d0
  #88/100:  36.0s | Züge: 145 | Strength: 0.865 |   7:14  -> Sieger: MCTS 1 s100-d0
  #89/100:  33.6s | Züge: 142 | Strength: 1.000 |   5:27  -> Sieger: MCTS 2 s100-d0
  #90/100:  32.1s | Züge: 142 | Strength: 0.370 |   4:5   -> Sieger: MCTS 1 s100-d0
  #91/100:  34.9s | Züge: 139 | Strength: 0.865 |   1:9   -> Sieger: MCTS 2 s100-d0
  #92/100:  36.5s | Züge: 154 | Strength: 1.000 |  21:40  -> Sieger: MCTS 1 s100-d0
  #93/100:  32.9s | Züge: 141 | Strength: 1.000 |  29:12  -> Sieger: MCTS 1 s100-d0
  #94/100:  36.9s | Züge: 154 | Strength: 0.685 |  11:8   -> Sieger: MCTS 2 s100-d0
  #95/100:  37.4s | Züge: 147 | Strength: 1.000 |  30:8   -> Sieger: MCTS 1 s100-d0
  #96/100:  34.9s | Züge: 141 | Strength: 0.100 |   0:0   -> Sieger: MCTS 1 s100-d0
  #97/100:  36.6s | Züge: 146 | Strength: 1.000 |   7:37  -> Sieger: MCTS 2 s100-d0
  #98/100:  33.8s | Züge: 142 | Strength: 0.550 |   8:9   -> Sieger: MCTS 1 s100-d0
  #99/100:  32.5s | Züge: 134 | Strength: 0.100 |   0:0   -> Sieger: MCTS 2 s100-d0
  #100/100:  39.0s | Züge: 149 | Strength: 0.100 |   0:0   -> Sieger: MCTS 1 s100-d0

==================================================
🏆 ARENA ERGEBNISSE 🏆
Siege MCTS 1 s100-d0: 55
Siege MCTS 2 s100-d0: 45
0:0 Spiele:    22 / 100 (22.0%)

📉 DURCHSCHNITTLICHE STRAFPUNKTE (BODEN) pro Runde:
 - MCTS 1 s100-d0   :   0.48   5.14   7.44   7.68   7.45   |    5.64
 - MCTS 2 s100-d0   :   0.51   5.11   7.01   7.66   7.60   |    5.58
   (Werte = Ø Strafpunkte in dieser Runde über alle Spiele)

FINALE ELO RATINGS:
 - MCTS 1 s100-d0 : 1016 Elo
 - MCTS 2 s100-d0 : 984 Elo
```
