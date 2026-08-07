# Vorregistrierung: Aggressions-Stilmessung (Punkte-Raub bei gleicher Siegquote)

**Angelegt 2026-08-07, VOR dem Lauf** (Nutzer-Auftrag: "arena spiel mit
dem tendenziell besten sweep der aggressor faktoren; untersuch eigene
Punkte, Gegner-Punkte, Floor-Strafen; Ziel: eigene Gewinnquote gleich
oder besser UND dem Gegner Punkte rauben, wenn es uns nicht schadet").

## Ausgangsbefund (deskriptiv, Erst-Sweep 200 Spiele/Arm, 8 Bloecke)

Block-gepaarte Differenzen vs Kontrolle (0,0): (0,1;2,0) = Siegquote
+6pp (t~1,9), eigene Punkte +2,0; (0,2;2,0) = Gegner-Floor **+2,1
(t~4,5)**, Gegner-Punkte -1,1, Siegquote +3pp. Alle w>0-Arme senken
die eigenen Floor-Strafen. Erst-Sweep-Arena (McNemar): alle H0.

## Design (Bestaetigungslauf, frische Seeds = Replikationsregel)

`tools/paired_arena_env_ab.py`, Env `MOSAIC_POINTS_UTILITY_W,
MOSAIC_AGGR_LAMBDA`; DREI Arme a **400 Spiele** (16 Bloecke a 25),
Champion@400 vs Heuristik@150dyn, Basis-Seed 20260810:
Kontrolle (0,0), Kandidat A (0.1,2.0), Kandidat B (0.2,2.0).
Einplanung: CPU-Bahn NACH dem laufenden τ-Annealing-Batch, VOR dem
v21-Schwarm.

## Entscheidungsregeln (vorab festgelegt)

1. **Siegquoten-Wache** (primaer, je Kandidat): gepaarter McNemar vs
   Kontrolle. Ein Kandidat scheidet aus, wenn er signifikant SCHLECHTER
   ist (p<0,05 in der falschen Richtung) ODER seine Punkt-Schaetzung
   der Siegquote unter der Kontrolle liegt.
2. **Raub-Metriken** (Block-Ebene, 16 gepaarte Bloecke, t-Test):
   Gegner-Punkte-Senkung und/oder Gegner-Floor-Erhoehung mit p<0,05.
3. **Uebernahme als Live-/Stil-Preset**, wenn Regel 1 bestanden UND
   Regel 2 erfuellt. Qualifizieren beide Kandidaten, gewinnt der mit
   der besseren Siegquoten-Differenz; Gleichstand -> (0.1,2.0).
4. Vor Einsatz in BEWERTETEN Partien braucht das gewaehlte Preset eine
   eigene Anker-Kante (Gating Champion+Preset vs Champion w=0,
   Elo-Betrugsschutz-Regel). Self-Play-Generierung bleibt bei w=0
   (Korpus-Stil ist NICHT Gegenstand dieser Messung).
5. Beide Kandidaten scheitern -> w=0 bleibt, Punkt zu; die
   deskriptiven Stil-Befunde werden nur dokumentiert.
