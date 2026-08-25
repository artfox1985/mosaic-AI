<!-- STATUS: ENTSCHIEDEN | Frage: Traegt w>0 im Punkte-Blend Arena-Staerke, jetzt mechanistisch begruendet? | Beleg: **REGEL 2, GESCHLOSSEN 2026-08-10**: Kontrolle w=0 321/400 (80,25 %) gegen Arm w=0,1 300/400 (75,00 %) -- Block-Delta -5,25pp, t=-2,68, McNemar p=0,0527. Kein Gewinner, Richtung eher schaedlich; w bleibt 0. Die +6pp der Neukartierung sind mit doppelter Stichprobe NICHT reproduziert, sondern umgekehrt. Hebel muss plattenselektiv werden ⇒ Plattenkopf. `evaluations/artifacts/paired_arena_env_points_blend_w.json` -->

# Vorregistrierung: Punkte-Blend-Gewicht w > 0 (plattenmotiviert)

**Angelegt 2026-08-09, VOR jedem Lauf.** Nutzer-Auftrag: *"setz die
vorregistrierung für w>0 auf"*, nach dem Stufe-2-Befund zum Punkte-Kopf.

## Warum das kein Wiederaufguss ist

Der Blend (`MOSAIC_POINTS_UTILITY_W` = w, `MOSAIC_AGGR_LAMBDA` = λ;
Blattwert = (1-w)·P(Sieg) + w·u_pts mit u_pts = f(own - λ·opp)) steht
seit der Aggressions-Neukartierung ueberall auf **w = 0**, weil alle drei
Arme H0 ergaben. Diese Messung war auf die **allgemeine Punkte-Marge**
gerichtet. Neu sind zwei Befunde, die zusammen in dieselbe Richtung
zeigen:

1. **Stufe 2 (heute)**: beide Punkte-Koepfe sortieren die Wurzelkandidaten
   plattenabhaengig UM -- `net_points_forecast` Tau-Median 0,792,
   `net_opp_points_forecast` **0,640** (Regel 2a,
   `points_head_plates_stage2.json`). Der Tau ist hier eindeutig, weil der
   Forward-Pass deterministisch ist: die Null waere exakt 1,0. Beide
   Koepfe haben in der Suche aber **Gewicht Null** -- das Signal wird
   berechnet und verworfen.
2. **Die Neukartierung selbst**: ihr descriptively bester Arm war
   **(w=0,1, λ=2,0) mit +6pp, p=0,169** -- nicht signifikant, aber der
   groesste der drei. Genau dieser Arm gewichtet den GEGNER-Term doppelt.
   Und der Gegner-Kopf ist laut Stufe 2 der **staerker**
   plattendifferenzierende (0,640 gegen 0,792).

Die deskriptive Richtung von damals und der Mechanismus-Befund von heute
zeigen also unabhaengig voneinander auf denselben Arm. Das ist der
Unterschied zu einer Dosis-Wiederholung.

## Die Schwaeche des Hebels, offen benannt

w gewichtet den **gesamten** Skalar der Punkte-Koepfe, nicht selektiv den
Plattenanteil. Ist die Platteninformation nur ein kleiner Teil dieses
Skalars, verstaerkt w>0 ueberwiegend Inhalt, der bereits als H0 gemessen
wurde. Dieser Task ist damit ein Test des VORHANDENEN Knopfes unter einer
neuen Begruendung -- kein plattenselektiver Eingriff. Ein plattenspezifischer
Zuschnitt (z.B. nur die aktiven Kriterien gewichten) waere ein eigener
Task und braeuchte den Plattenkopf (`PREREG_plate_head.md`).

## Design

Instrument `tools/paired_arena_env_ab.py` (Mehr-Var-Modus: der Regler-Name
darf komma-getrennt mehrere Variablen tragen), Champion@400 vs
Heuristik@150dyn, **identische Basis-Seeds ueber die Arme**.

**Ein Faktor, zwei Arme, je 400 Partien** (nicht 200 wie die
Neukartierung -- Begruendung unten), Basis-Seed 20260902:
- **Kontrolle**: `w=0, λ=2.0` (λ ist bei w=0 wirkungslos, wird nur
  mitgefuehrt, damit die Arm-Definition identisch aussieht)
- **Arm**: `w=0.1, λ=2.0`

**Warum n=400 und nicht 200**: die heute gemessene Block-SE liegt bei
~2,2pp auf der Quote (Trenn-Messung, 16 Bloecke a 25). Ein Effekt von
+6pp waere damit ~2,7 SE -- bei n=200 waeren es ~1,9 SE, also genau der
Bereich, in dem die Neukartierung mit p=0,169 haengengeblieben ist. Der
Aufwand verdoppelt sich, die Frage wird aber erst dadurch entscheidbar.

## Entscheidungsregeln (vorab)

1. **Gewinner** = exakter zweiseitiger McNemar p<0,05 gegen die Kontrolle
   **UND** Block-SE-t > 2 (Pflichtregel: Paar-SEs unterschaetzen massiv)
   **UND** Frisch-Seed-Replikation (Statistik-Regel 3, weil eine
   Preset-Aenderung folgt).
2. **H0** ⇒ w bleibt 0, und der Punkt gilt als **zweifach** gemessen:
   einmal auf der Punkte-Marge (Neukartierung), einmal mit
   Mechanismus-Begruendung und doppelter Stichprobe. Dann ist der Blend
   als Weg fuer Plattenwirkung erledigt, und der Hebel muss
   plattenselektiv werden (Plattenkopf) oder trainingsseitig.
3. **Ein replizierter Gewinner wird NICHT direkt Live-Preset**: er
   braucht erst eine eigene Anker-Kante (Gating Champion+Blend vs
   Champion w=0), damit bewertete Partien Elo-regelkonform bleiben --
   uebernommen aus Regel 2 der Neukartierung.
4. **Deskriptiv, keine Entscheidungsgroesse**: eigene Punkte,
   Gegner-Punkte und Floor-Strafen je Arm auf Block-Ebene. Sie sind der
   Grund, aus dem der Nutzer den Blend ueberhaupt wollte ("dem Gegner
   Punkte rauben"), aber sie entscheiden nicht -- die Siegquote tut es.
5. **Kein Dosis-Sweep in diesem Task.** Bei einem Sieg waere w=0,2 ein
   naechster Punkt, bei H0 nicht. Mehrere Arme gleichzeitig wuerden die
   Multiplizitaets-Korrektur erzwingen, die bei ISMCTS-k heute schon
   knapp gebraucht wurde.

## Kosten

2x400 Partien @400 Sims, CPU-Bahn, ~50-60 min; Replikation bei Erfolg
noch einmal so viel. Einplanung: nach dem dritten Gewichts-Gating
(`pw025`), damit die CPU-Bahn nicht dreifach belegt ist.

## ERGEBNIS 2026-08-10: REGEL 2 -- w bleibt 0, und zwar deutlicher als H0

`tools/paired_arena_env_ab.py`, Mehr-Var-Modus
(`MOSAIC_POINTS_UTILITY_W,MOSAIC_AGGR_LAMBDA`), Champion
`v21_2d_brierbest`@400 vs Heuristik@150dyn, Basis-Seed 20260902, je 400
Partien, identische Seeds ueber die Arme, 16 Bloecke a 25.

| Arm | Netz-Siege | Quote |
|-----|-----------|-------|
| Kontrolle `w=0, lambda=2.0` | 321/400 | **80,25 %** |
| Arm `w=0.1, lambda=2.0` | 300/400 | **75,00 %** |

- **Block-Delta -5,25pp, SE 1,96pp, t = -2,68** (Pflichtinstrument)
- exakter McNemar **p = 0,0527**, diskordant 43 (nur Arm) / 64 (nur Kontrolle)

### Lesart

Regel 1 (Gewinner) verlangt p<0,05 UND Block-t>2 UND Frisch-Seed-Replikation
-- der Arm ist kein Gewinner. **Regel 2 greift: w bleibt 0.**

Es ist aber MEHR als H0: beide Instrumente zeigen in dieselbe Richtung, und
das Block-Instrument ist mit t=-2,68 signifikant. Die Vorregistrierung hatte
diesen Zweig nicht vorgesehen (nur "Gewinner" und "H0"), deshalb hier
ausdruecklich: **w=0,1 schadet vermutlich**, und ein einzelner Lauf ohne
Replikation traegt diese Aussage nur als Richtung, nicht als Befund. Die
ENTSCHEIDUNG ist in beiden Lesarten dieselbe.

Bemerkenswert: die deskriptive Richtung der Aggressions-Neukartierung
(+6pp fuer genau diesen Arm, p=0,169) ist damit **nicht reproduziert, sondern
umgekehrt**. Das ist ein Lehrstueck zur Seed-Skala: ein +6pp-Befund bei
n=200 und ~2,2pp Block-SE war nie belastbar, und die doppelte Stichprobe
dreht das Vorzeichen. Wer aus solchen Zwischenstaenden Rezepte baut, baut auf
Rauschen.

### Vorregistrierte Konsequenz, unveraendert uebernommen

"Dann ist der Blend als Weg fuer Plattenwirkung erledigt, und der Hebel muss
**plattenselektiv** werden (Plattenkopf) oder trainingsseitig." Genau das
laeuft: `PREREG_plate_head.md`, Kriterium 6 als 9 Atome, Rauchtest mit
Skill +0,574 bestanden.

Der Punkt gilt damit als **zweifach gemessen** -- einmal auf der
Punkte-Marge (Aggressions-Neukartierung), einmal mit Mechanismus-Begruendung
und doppelter Stichprobe. Der Blend wird nicht wieder aufgerollt.
