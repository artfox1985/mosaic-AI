# Vorregistrierung: Dosis der Wertungsplatten-Injektion

**Angelegt 2026-08-11 auf Nutzer-Auftrag** -- *"wie viel wir injizieren muessen
wir an einem arena spiel verifizieren. geht hier ein sweep gegen den aktuellen
champion?"* / *"ja, so vorregistrieren"*.

## 1. Warum die Arena hier das RICHTIGE Instrument ist

Gemessen wird **derselbe Champion gegen sich selbst, einmal mit und einmal ohne
Knopf**. Kein Training, kein neuer Checkpoint. Damit faellt die groesste
Rauschquelle des Projekts weg: der Trainings-Seed bewegt Metriken 4-6x staerker
als jeder Regler (`project_training_seed_variance`), und genau der ist hier
identisch. Der einzige Unterschied zwischen den Armen ist eine Zahl in einer
Umgebungsvariablen.

**RUECKNAHME einer eigenen Aussage (2026-08-10).** Ich hatte die
Arena-Blindheit auch auf Task #93 angewendet ("gegen ein Geschwisternetz mit
demselben blinden Fleck"). Das war falsch. Blind ist der Vergleich, wenn ZWEI
TRAINIERTE NETZE gegeneinander stehen, die beide die Luecke haben -- das war
das Gating in `elo_history.csv` Zeile 48 (`pi_endgame_s2_brierbest` gegen
`v20_2d_opp_brierbest`, 97:103, p=0,76). Ein Knopf-an-gegen-Knopf-aus mit
demselben Netz ist der SAUBERE Kontrast, und #93 war so gemessen. Fuer dessen
p=0,71 bleibt die strukturelle Erklaerung (marginale statt absolute Form, siehe
STATUS), nicht die Blindheit.

## 2. Gegenstand: EIN Knopf, nicht zwei

Es gibt zwei Injektions-Terme:

- `MOSAIC_WERTUNG_SHAPING_W` -- Wertungsplatten-Kriterien, gegatet auf die
  aktiven Platten, ego-only, absolut (Commit `40eb39b`)
- `MOSAIC_UNLOCK_SHAPING_W` -- gestufter Spezialfeld-Freischaltterm,
  UNGEGATET, je Kuppelplatte gebucht

**Gegenstand dieser Vorregistrierung ist ausschliesslich
`MOSAIC_UNLOCK_SHAPING_W`**, der andere bleibt auf 0. Begruendung: das
gemessene Loch sind die Spezialfelder (9,0 von 14,5 Punkten Differenz je
Partie, ~62 %), und der Freischaltterm ist der einzige, der es adressiert. Ein
gleichzeitiger Sweep beider Knoepfe wuerde die Wirkung konfundieren. Der
`WERTUNG`-Term bekommt eine EIGENE Vorregistrierung, danach.

## 3. Arme -- drei, mit Begruendung fuer die Werte

| Arm | `MOSAIC_UNLOCK_SHAPING_W` | Begruendung |
|---|---|---|
| Kontrolle | 0,0 | Bestandsverhalten |
| A | **0,3** | Hauswert: `floor_shaping_weight` und `PLATE_SHAPING_WEIGHT` benutzen beide 0,3 |
| B | **1,0** | Schwelle, ab der der Term mit echten Q-Differenzen konkurriert: ein zusaetzlich belegtes Feld ergibt ~0,02 in Wert-Einheiten (`tanh(1,03/50)`), Geschwister unterscheiden sich um wenige Hundertstel |

**Bewusst nur zwei Arme.** Task D hatte vier und alle waren H0; die Seed-Skala
liegt bei 5,75pp bei n=400. Mehr Arme kosten Multiplizitaetskorrektur auf
Effekte, die darunter liegen. `MOSAIC_UNLOCK_BETA` bleibt auf dem Default 2,0
-- der Exponent ist NICHT Gegenstand (Praezedenz `wertung_progress`).

## 4. Pflicht-Nebenmessung: die Freischaltrate

**Die Siegquote allein reicht nicht.** Der Prior kann den Term aushebeln:
Gumbel zieht `GUMBEL_TOP_M = 16` Kandidaten nach Prior-Masse, die Injektion
kann nur UMORDNEN, was gezogen wurde. Legt der Champion auf die
freischaltvorbereitenden Zuege fast keine Masse, kommen sie nicht in den
Kandidatensatz.

Deshalb je Arm zusaetzlich zu protokollieren, aus den Partie-Logs (Methode wie
`watchlist_v20_zwischenlese.md` Abschnitt 2):

- **Freischaltungen je Partie** (Zielwert Nutzer 3,1; KI heute 0,6)
- **Spezialpunkte je Partie** (Zielwert Nutzer 10,3; KI heute 1,3)
- Partien ohne jede Freischaltung (KI heute 6 von 10)

### Lesart -- drei Faelle, die in einer Siegquote GLEICH aussehen

| Rate | Siegquote | Verdikt |
|---|---|---|
| steigt | steigt | Term wirkt und rechnet sich -> Dosis uebernehmen, Stufe 2 (Destillation) folgt |
| steigt | flach | Term wirkt, Punkte wandeln nicht in Siege -> Dosis oder Zielkonflikt mit den Linienpositionen; Kriterium 6 ist der einzige echt gegenlaeufige Fall |
| **steigt nicht** | -- | **Der PRIOR blockiert.** Kein Beleg gegen den Term. Der Arena-Wert ist dann eine UNTERGRENZE fuer das, was nach der Destillation drin ist -- Konsequenz ist Self-Play MIT Injektion, nicht Verwerfen |

Die dritte Zeile ist der Grund, warum diese Nebenmessung Pflicht ist und nicht
Zierde: ohne sie wuerde ein H0 falsch als "Term wirkungslos" gelesen -- derselbe
Fehler, den ich bei #93 und bei Zeile 48 schon gemacht habe.

## 5. Statistik -- stehende Projektregeln, hier ausgeschrieben

1. **Gepaart** ueber den Spielindex, IDENTISCHER Basis-Seed in allen Armen.
   Ungepaarte Vergleiche zwischen zwei Laeufen sind wertlos, auch bei n=400.
2. **Block-Ebene** fuer alle Score-Auswertungen (`feedback_arena_block_correlation`)
   -- Paar-SEs unterschaetzen massiv.
3. n = **200 Paare @400 Sims** je Arm, ~1-1,5 h CPU. SPRT erlaubt; ein
   Fruehstopp unter 150 Paaren zaehlt nur mit **Frisch-Seed-Replikation**.
4. **Bonferroni** ueber die zwei Arme: alpha = 0,025 je Arm.
5. Netz-vs-Netz-Effekte unter 8pp sind Seed-Rauschen -- gilt hier ABGESCHWAECHT,
   weil derselbe Checkpoint auf beiden Seiten steht und nur die Suchkonfiguration
   variiert. Die 8pp-Schwelle stammt aus Netz-vs-Heuristik-Vergleichen; hier ist
   die relevante Schranke die gepaarte Block-SE, die MITZUBERICHTEN ist.

## 6. Vorbedingungen -- in dieser Reihenfolge

1. Das laufende Training (`v21_2d_own02`) ist fertig. Kein `pip install`
   waehrend es laeuft.
2. Wheel neu installieren, **Paritaetsprobe MUSS
   `8c6684ffba06cf3e16e898b83325f3154c04efac555c8e862c079b71155bd423`
   liefern** -- sonst ist die Kontrolle nicht das Bestandsverhalten und der
   ganze Sweep ist wertlos.
3. **ZU VERIFIZIEREN, NICHT ANNEHMEN**: ist der Knopf **je Spieler** setzbar
   oder nur je Prozess? Umgebungsvariablen sind prozessweit -- laufen beide
   Spieler im selben Prozess, bekaeme die Kontrolle die Injektion mit und der
   Kontrast waere null. Praezedenz spricht dafuer, dass es geht (der
   `w>0`-Sweep fuhr Arme als `0,2.0` / `0.1,2.0`, also seitenweise), aber das
   ist am Arena-Code zu PRUEFEN, bevor Rechenzeit fliesst.

## 7. Was dieser Sweep NICHT entscheidet

- Nicht den Champion-Wechsel: es entsteht kein neuer Checkpoint.
- Nicht den `WERTUNG`-Term (eigene Vorregistrierung).
- Nicht das Abschaltkriterium der Injektion -- das braucht mindestens eine
  Generation Self-Play MIT Injektion und dann die zwei Fragen aus STATUS
  (steigt die Prior-Masse auf den Freischaltzuegen; haelt die Rate bei
  gesenktem Gewicht).
- Nicht Arm B des Ownership-Kopfs (Marginalen im Blatt) -- der ist nicht gebaut
  und steht hinter Stufe 1 und 2.
