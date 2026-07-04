trainiert mit

+ --games 2000 --mode network --version v1b --sims 400 --stage 1
+ --games 2000 --mode network --version v1c --sims 400 --stage 1
+ --games 2000 --mode network --version v4 --sims 400 --stage 1
+ --games 2000 --mode network --version v4b --sims 400 --stage 1
+ -- load v4

512 neuronen pro hidden layer

value weight = 4

**Netzdaten**

```
=======================================================
  MODEL: alphazero_v6b.pth
=======================================================
  Erstellt am            2026-07-04T12:37:14.024086
  Epochen (tatsächlich)  100
  Epochen (angefragt)    100
  Early Stop             False
  Züge                   1,210,259
  Input Size             684
  Hidden Size            512
  Num Actions            482
  Batch Size             256
  Learning Rate          0.0006
  Value Weight           4
  Policy Loss (final)    2.0538
  Policy Loss %          33.2%  🟡 Gut
  Value Loss (final)     0.0150  🟢 Sehr gut
  Warm-Start von         v4
=======================================================
```

**Stage 1**

```

```

**Stage 2**

```

```

-> Verhältnis Stage 1 zu Stage 2: 2.25 -> gelbe Ampel

**Arena vs. Heuristik**

```
58:42	27.0 : 26.6
```

**Arena vs. Champion (v4)**

```

```
