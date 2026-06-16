## Übersicht

- v1a -> 256er netz mit E Shaping

- v1b -> 512er netz mit E Shaping

- v1_noe_vw05 -> 256er netz ohne e Shaping, value weight 0.5

- v1_noe_vw01 -> 256er netz ohne e Shaping, value weight 0.1

- v1c -> 256er netz ohne e Shaping, value weight 0.5, gewichteter Policy Loss

- v1d -> 256er netz ohne e Shaping, value weight 0.5, gewichteter Policy Loss, Bonus chip engine update, 4000 spiele

### v1a, v1b

```
🏆 ARENA ERGEBNISSE 🏆
Siege AlphaZero v1-256: 50
Siege AlphaZero v1-512: 50
0:0 Spiele: 71 / 100 (71.0%)
FINALE ELO RATINGS:

- AlphaZero v1-512: 1006 Elo
- AlphaZero v1-256: 994 Elo
```

> keine signifikante Verbesserung mit 512er Netz

### v1a, v1_noe_vw05

```
🏆 ARENA ERGEBNISSE 🏆
Siege AlphaZero v1-256: 46
Siege AlphaZero v1 newshaping: 54
0:0 Spiele: 63 / 100 (63.0%)

FINALE ELO RATINGS:

- AlphaZero v1 newshaping: 1006 Elo
- AlphaZero v1-256: 994 Elo
```

> keine signifikante Verbesserung wenn die Synergien weggelassen werden. aber zumindest weniger 0:0 spiele

### v1_noe_vw05, v1_noe_vw01

```
🏆 ARENA ERGEBNISSE 🏆
Siege AlphaZero v1 NS VW0.1: 51
Siege AlphaZero v1 NS VW0.5: 49
0:0 Spiele: 72 / 100 (72.0%)

FINALE ELO RATINGS:

- AlphaZero v1 NS VW0.1: 1015 Elo
- AlphaZero v1 NS VW0.5: 985 Elo
```

> keine signifikanter Einfluss des Value weight. Hohe Anzahl von 0:0 spielen

### v1c

```
🏆 ARENA ERGEBNISSE 🏆
Siege AlphaZero v1c s50: 78
Siege MCTS s50-d0: 122
0:0 Spiele: 107 / 200 (53.5%)

📉 DURCHSCHNITTLICHE STRAFPUNKTE (BODEN):

- AlphaZero v1c s50: Ø 9.14 Pkt pro Runde
- MCTS s50-d0 : Ø 5.95 Pkt pro Runde

FINALE ELO RATINGS:

- MCTS s50-d0 : 1113 Elo
- AlphaZero v1c s50: 887 Elo
```

```
🏆 ARENA ERGEBNISSE 🏆
Siege AlphaZero v1c s50: 1
Siege MCTS s50-d0: 1
0:0 Spiele: 2 / 2 (100.0%)

📉 DURCHSCHNITTLICHE STRAFPUNKTE (BODEN) pro Runde:
 R 1 R 2 R 3 R 4 R 5 | Gesamt

- AlphaZero v1c s50: 6.50 10.00 10.00 10.00 10.00 | 9.30
- MCTS s50-d0 : 0.00 8.00 8.00 8.00 10.00 | 6.80
  (Werte = Ø Strafpunkte in dieser Runde über alle Spiele)
```

> Verliert noch immer oft und das Elo Rating ist auch weit auseinander. Aber zumindest weniger 0:0 spiele. Viele Strafpunkte jede Runde

```
=======================================================
  MODEL: alphazero_v1c.pth
=======================================================
  Erstellt am            2026-06-16T00:02:27.537819
  Epochen (tatsächlich)  46
  Epochen (angefragt)    100
  Early Stop             True
  Early Stop ab Epoche   41
  Züge                   258,878
  Input Size             553
  Hidden Size            256
  Num Actions            482
  Batch Size             256
  Learning Rate          0.0006
  Value Weight           0.5
  Policy Loss (final)    1.9123
  Policy Loss %          31.0%  🟡 Gut
  Value Loss (final)     0.0344  🟢 Sehr gut
=======================================================
```

### v1d

```
🏆 ARENA ERGEBNISSE 🏆
Siege AlphaZero v1d s50: 36
Siege MCTS s50-d0: 64
0:0 Spiele: 52 / 100 (52.0%)

📉 DURCHSCHNITTLICHE STRAFPUNKTE (BODEN) pro Runde:

- AlphaZero v1d s50: 5.91 9.77 9.83 9.96 9.55 | 9.00
- MCTS s50-d0 : 0.84 5.93 7.26 8.82 7.38 | 6.05
  (Werte = Ø Strafpunkte in dieser Runde über alle Spiele)

FINALE ELO RATINGS:

- MCTS s50-d0 : 1151 Elo
- AlphaZero v1d s50: 849 Elo
```

> Ähnlich wie v1c, mehr Trainingsspiele haben (noch) nichts gebracht

```
=======================================================
  MODEL: alphazero_v1d.pth
=======================================================
  Erstellt am            2026-06-16T08:18:57.269423
  Epochen (tatsächlich)  48
  Epochen (angefragt)    100
  Early Stop             True
  Early Stop ab Epoche   43
  Züge                   515,445
  Input Size             553
  Hidden Size            256
  Num Actions            482
  Batch Size             256
  Learning Rate          0.0006
  Value Weight           0.5
  Policy Loss (final)    1.9777
  Policy Loss %          32.0%  🟡 Gut
  Value Loss (final)     0.0617  🟡 Gut
=======================================================
```
