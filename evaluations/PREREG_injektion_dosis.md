# Vorregistrierung: Dosis der Wertungsplatten-Injektion

**Angelegt 2026-08-11 auf Nutzer-Auftrag** -- *"wie viel wir injizieren muessen
wir an einem arena spiel verifizieren. geht hier ein sweep gegen den aktuellen
champion?"* / *"ja, so vorregistrieren"*.

## 1. Warum die Arena hier das RICHTIGE Instrument ist

> **UEBERHOLT durch das AMENDMENT unten (Befund 1): der Entwurf "derselbe
> Champion gegen sich selbst" ist NICHT durchfuehrbar**, weil die `MOSAIC_*`-
> Knoepfe prozessweit sind (OnceLock) -- beide Bretter bekaemen die Injektion.
> Gueltig ist Weg A des Amendments: Netz+Knopf gegen HEURISTIK, ein Prozess je
> Arm. Der Absatz bleibt stehen, weil seine BEGRUENDUNG (keine
> Trainings-Seed-Varianz) unveraendert gilt -- nur die Umsetzung war falsch.

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
3. **BEANTWORTET 2026-08-11, negativ** (siehe Amendment Befund 1): der Knopf
   ist NUR je Prozess setzbar (OnceLock). Deshalb Weg A mit der Heuristik als
   festem Gegner und einem Prozess je Arm. Ursprungsfrage zur Nachvollziehbarkeit:
   ist der Knopf **je Spieler** setzbar oder nur je Prozess? Umgebungsvariablen sind prozessweit -- laufen beide
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

---

# AMENDMENT 2026-08-11: Design korrigiert, drei Befunde aus der Code-Pruefung

Nutzer: *"damit kannst eigentlich jetzt schon loslegen"*. Alle drei Punkte sind
GEPRUEFT mit Fundstelle (Regel 0), nicht geschlossen.

## Befund 1 -- die Knoepfe sind PROZESSWEIT. Abschnitt 1 war nicht durchfuehrbar.

`tools/paired_arena_env_ab.py`, Modulkopf Zeilen 6-13, woertlich:

> je Arm ein EIGENER Worker-Prozess mit gesetzter Env-Var (**die Knoepfe sind
> prozessweit, OnceLock**), Champion-Netz vs Heuristik@150(dyn) via
> `tools/paired_arena_arm_worker.py` ... **Die Heuristik liest keinen der
> Knoepfe** -- die Arm-Differenz attribuiert sauber auf die Netz-Seite.

Damit ist mein Entwurf "DERSELBE Champion, Knopf an gegen aus, beide Seiten im
selben Spiel" **unmoeglich**: beide Bretter bekaemen die Injektion. Vorbedingung
3 der Erstfassung ist damit beantwortet -- und negativ.

## Befund 2 -- zwei etablierte Designs, mit gegensaetzlichen Schwaechen

**(A) `paired_arena_env_ab.py`: Netz+Knopf gegen HEURISTIK.** Asymmetrisch, weil
die Heuristik keinen Knopf liest -- die Zurechnung ist sauber. Schwaeche: der
Champion gewinnt dort ~76-82 % (STATUS, Seed-Skala-Beispiel), also
Deckenkompression.
*Meine Herleitung, ungemessen*: McNemar rechnet nur auf den DISKORDANTEN
Paaren, nicht auf dem Niveau -- bei 80 % bleibt genug Diskordanz, die Decke ist
also ein Sensitivitaets-, kein Gueltigkeitsproblem.

**(B) `paired_arena_plate_ab.py`: `net_vs_net_arena_match`, naher Gegner,
sequenziell mit Rebuild zwischen den Armen.** Identische Seeds, Paarung ueber
den Spielindex, McNemar auf diskordanten Paaren. Sensitiver Gegner (dort
v15_best gegen v14b_best, ~68 Elo Abstand).
**Schwaeche, und das ist ein FUND**: `PLATE_SHAPING_ENABLED` ist eine
Compile-Zeit-Konstante, steckt also im Binary -- in Arm ON bekommen **BEIDE**
Bretter das Shaping. Gemessen wurde "beide geformt gegen beide ungeformt".
*Meine Herleitung aus dem Toggle-Typ, ungemessen*: hilft die Formung beiden
gleich, hebt sich der Effekt auf. Das ist eine **dritte** moegliche Erklaerung
fuer das p=0,71 von Task #93 -- diesmal das Symmetrie-Argument korrekt
angewendet (nicht "Geschwisternetze teilen den blinden Fleck", sondern "beide
Spieler des Arms haben denselben Eingriff bekommen").

**Entscheidung: Weg A.** Nur er erzeugt die ASYMMETRIE, auf die es ankommt --
die Frage ist "hilft die Injektion dem, der sie hat", nicht "was passiert, wenn
beide sie haben". Weg B wuerde denselben Fehler wiederholen, an dem #93
vermutlich gescheitert ist.

**Korrigierte Arme** (Instrument `paired_arena_env_ab.py`, ein Prozess je Arm):

    --env-name MOSAIC_UNLOCK_SHAPING_W --arms 0.0 0.3 1.0 --control 0.0
    --net-sims 400 --n-games 200 --seed <fix> --out-prefix unlockw

Gegner Heuristik@150(dyn) in ALLEN Armen, identischer Basis-Seed, Paarung ueber
den Spielindex, exakter zweiseitiger McNemar auf den diskordanten Paaren.

## Befund 3 -- die Freischaltrate liefert das Instrument NICHT

`tools/paired_arena_arm_worker.py` Zeile 8: je Partie wird
`{scores, winner, steps, total_floor, floor_per_round}` zurueckgegeben. **Keine
Partie-Logs, keine Spezialfeld-Daten.** Die Pflicht-Nebenmessung aus Abschnitt 4
ist damit aus dem Arena-Lauf allein NICHT zu gewinnen.

`tools/analyze_game_log.py` kann sie lesen (`[Special freigeschaltet!]`
Zeile 112, `SPECIAL_BONUS`-Regex Zeile 136), ist aber auf
`static/log/game_*.log` gebaut -- die schreibt der Server, nicht die Arena.
**KEIN zweites Werkzeug bauen.**

Zwei Wege, Entscheidung offen (Nutzer-Vorlage):

**(i)** Das Arena-Ergebnis-Array um Spezialfeld-Zahlen erweitern. Sauber am
Ort der Messung, kostet aber eine Aenderung auf der RUST-Seite
(`net_arena_match`) plus Python -- und damit einen Wheel-Neubau mit
Paritaetspruefung.
**(ii)** Verhalten aus den ENDBRETTERN eines kurzen Self-Play-Laufs MIT
gesetztem Knopf zaehlen. Die Daten liegen dort bereits: `_ownership_from_dome`
liest `dome_grid` aus den `.pkl`-Dateien, und `tools/plate_head_labels.py` /
`tools/atom_skill_check.py` werten Endbretter schon aus. Kein Rust-Eingriff,
vorhandene Werkzeuge. Nachteil: Self-Play statt Arena, also ein anderes Regime
als die Siegquote.

**Vorschlag: (ii)**, weil es ohne Wheel-Neubau auskommt und die
Verhaltensfrage ("steuert der Term die Freischaltung ueberhaupt an?") kein
Arena-Regime braucht. Die Siegquote kommt aus Weg A, das Verhalten aus (ii);
die Drei-Faelle-Tabelle aus Abschnitt 4 bleibt anwendbar, weil sie die zwei
Groessen nur nebeneinander liest und nicht aus demselben Lauf verlangt.

## Nachtrag zu Befund 3: Weg (ii) ist gedeckt, kein neues Werkzeug

GEPRUEFT an `tools/plate_head_labels.py`:

- `atoms_criterion6` (Zeile 71): je Slot "hat ein Spezialfeld, das am Ende LEER
  ist", 1/0.
- `existence_criterion6` (Zeile 85): je Slot "traegt am Ende UEBERHAUPT ein
  Spezialfeld", 1/0 -- die Maske, die es ohnehin schon gibt.
- Gelesen wird `player["dome_grid"]` aus den Korpus-Dateien (Zeile 60).

**Freischaltungen je Partie = Summe(existenz) - Summe(leer)** -- direkt aus den
Endbrettern, mit dem vorhandenen Werkzeug, ohne Rust-Eingriff.

Was fehlt, ist nur die REIHENGEWICHTETE Punktsumme (Kriterium 6 ist flach, die
Spezialpunkte sind es nicht). Das Werkzeug iteriert Slots und Spaces, die
Rasterreihe ist daraus `slot_row * 2 + space_index / 2`; also eine kleine
ERGAENZUNG an `plate_head_labels.py`, **kein zweites Werkzeug**.

`paired_arena_env_ab.py` braucht keine Aenderung: `--env-name` ist generisch
(Nutzungsbeispiele im Modulkopf zeigen `MOSAIC_FLOOR_SHAPING_W` und
`MOSAIC_GUMBEL_TOP_M`).
