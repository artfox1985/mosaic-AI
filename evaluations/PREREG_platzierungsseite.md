# Vorregistrierung: die Platzierungsseite plattenbewusst machen

**Angelegt 2026-08-12 nachts, Nutzer-Auftrag** — *"dann überleg dir wie wir
dorthin kommen. wiegesagt das ist die leichteste aufgabe da sie mit dem
basispiel aufbau gut harmoniert"*, nachdem ich 14 Punkte mit `w`/`alpha` allein
für unwahrscheinlich erklärt hatte.

## 1. BEIDE Haelften, nicht die eine statt der anderen

**Nutzer-Korrektur 2026-08-12**: *"es war nicht die falsche haelfte. du brauchst
beide haelften."* Aufgenommen. Die Draftingseite ist notwendig und allein nicht
ausreichend: sie holt die richtigen Fliesen in die Musterreihen, die Platzierung
bringt sie in dieselbe Spalte. Ohne die erste hat die zweite nichts zu verteilen,
ohne die zweite wird die erste verstreut.

Folge fuer die Messung, und sie ist bindend: der Platzierungsknopf wird MIT
aktiver Draftingseite gemessen (bestes Rasterpaar `w`/`alpha`), nicht als deren
Ersatz. Ein Arm mit Platzierung allein gehoert nur als Zerlegung dazu, nicht als
Kandidat.

Spaltenbau harmoniert mit dem Basisspiel: `score_placed_tile` zählt orthogonal
verbundene Linien, eine wachsende Spalte zahlt bei JEDER Fliese, zusammen
1+2+3+4+5+6 = 21 Platzierungspunkte plus 7 Plattenpunkte. Das Spiel belohnt es
von sich aus. Wenn es trotzdem nicht passiert, blockiert etwas anderes.

Gebaut hatte ich bisher nur die **Draftingseite**. Die fehlende zweite Hälfte ist
die **Platzierung**: welche Spalte eine fertige Musterreihe bekommt.

## 2. GEPRÜFT: wer die Platzierung entscheidet

`self_play.rs:1002 resolve_tiling_step` → `best_first_step_exact_or_valued`
(`tiling_solver.rs:953`):

| Runde | Pfad | plattenbewusst? |
| ----- | ---- | --------------- |
| **1** | `best_first_step_exact` → `best_first_step_inner(.., true)` | **NEIN** — nur Platzierungspunkte |
| 2–4 | `best_first_step_valued` (`tiling_solver.rs:922`): `top_k_tilings(.., NET_TILING_TOPK)` dann `select_best_tiling_candidate(.., evaluator)` | nur INNERHALB der Top-K |
| 5 | `best_first_step_round5` (hinter `ROUND5_ENDSCORING_ENABLED`) | ja, exakt |

Die Suche entscheidet den Tiling-Zug also NICHT — der Solver tut es.

## 3. Zwei Blockaden, beide belegt

### (a) Runde 1 ist ausgeschlossen, mit einer Begründung, die nicht trägt

`tiling_solver.rs:943-946`: *"Runde 1 bewusst ausgeschlossen: das Value-Head ist
dort blind (RMSE 0,2531 ~ Zielstreuung 0,2538)"*.

Das rechtfertigt, dort keinen **gelernten** Proxy zu benutzen. Der Plattenwert
(`wertung_progress` bzw. `calculate_end_scoring`) ist aber eine **berechnete**
Größe ohne Schätzfehler. Die Begründung deckt den Ausschluss eines berechneten
Plattenterms nicht — und Runde 1 ist die Runde, in der Spalten angelegt werden.

### (b) Die Kandidatenmenge ist plattenblind vorgefiltert

`best_first_step_valued` nimmt `top_k_tilings(state, pi, NET_TILING_TOPK)` —
gereiht nach Platzierungspunkten. Eine Platzierung, die eine Spalte gründet, aber
einen Punkt weniger bringt, liegt womöglich außerhalb der Top-K und wird nie
bewertet. **Der Plattenwert kann einen einzelnen Platzierungspunkt strukturell
nicht überstimmen.**

Damit ist die Sättigung erklärt, die ich gemessen habe: Drafting lenkt zu den
richtigen Fliesen (0,70 → 1,75), die Platzierung verstreut sie.

## 4. Der Eingriff — ein Knopf, Default AUS, Parität unberührt

`MOSAIC_TILING_PLATTEN_W` (Default 0,0): beim Reihen der Tiling-Kandidaten wird
zu den Platzierungspunkten `w * calculate_end_scoring(Brett nach dem Tiling)`
addiert, und zwar in **allen** Runden 1–4. In Runde 5 bleibt
`best_first_step_round5` unangetastet (dort ist die Endwertung exakt und
strukturell besser).

Drei Eigenschaften, die das von meinen bisherigen Versuchen unterscheiden:

1. Es wirkt auf die **Platzierung**, nicht auf das Drafting — die bisher
   unangetastete Hälfte.
2. Es ist eine **berechnete** Größe, kein Netz-Wert. Der Runde-1-Vorbehalt gegen
   gelernte Proxys greift nicht.
3. Es reiht die Kandidaten **vor** dem Abschneiden auf Top-K, der Plattenwert
   kann also Platzierungspunkte überstimmen statt nur Gleichstände zu brechen.

## 5. Vorhersage, vorab und falsifizierbar

Der Plattenanteil an einer geschlossenen Spalte ist 7 Punkte, der typische
Unterschied zwischen zwei Platzierungskandidaten 1–3 Punkte. Ein `w` um 0,3–1,0
sollte also reichen, die Wahl zu kippen, wo eine Spalte in Reichweite ist, ohne
das Basisspiel umzuwerfen. Bleiben die vertikalen Punkte auch damit unter 3
(= 8 Spalten in 20 Partien), ist die Platzierungsseite NICHT die Blockade und die
Erklärung liegt tiefer — dann ist der nächste Verdacht die Versorgung
(bekommt das Netz die Farben überhaupt, die eine bestimmte Spalte braucht).

## 6. Messung

Dieselben 20 k1-Seeds, 400 gegen 150 Sims, Metrik Plattenpunkte des Kriteriums 1.
`w` in {0,1 / 0,3 / 1,0 / 3,0}, Draftingseite dabei auf dem besten Rasterpaar.
Mitberichtet: Endstand, Strafleiste, Siegquote — ein Plattengewinn, der den
Endstand kostet, ist kein Gewinn.

**Gequantelte Metrik beachten**: bei n=20 sind Schritte kleiner als 0,35
(= eine Spalte) nicht darstellbar. Für die Entscheidung zählt nur ein Sprung über
mehrere Spalten.

---

## 7. GEMESSEN 2026-08-12 nachts: der Deckel ist die PRODUKTFORM

Draftingseite in allen Zellen auf dem besten Rasterpaar (w=1 / alpha=1, gemessene
Decke allein: 2,10 vertikale Punkte = 6 Spalten in 20 Partien, Endstand 45,30).

### Stufe 1 -- Punkte-Kopf im Tiling-Stichentscheid: WIRKUNGSLOS, und zwar strukturell

| Gewicht | vertikal | Spalten/20 | Endstand | Siege |
| ------: | -------: | ---------: | -------: | ----: |
| 0,2 | 1,75 | 5 | 44,95 | 11/20 |
| 0,4 | 1,75 | 5 | 44,95 | 11/20 |
| 0,7 | 1,75 | 5 | 44,95 | 11/20 |
| 1,0 | 1,75 | 5 | 44,95 | 11/20 |

**Bit-identisch ueber den ganzen Bereich** -- nach der stehenden Regel ein Alarm,
kein Befund. Ursache am Code gefunden, `tiling_solver.rs:891-894`:

```text
let val = match mode {
    1 => p_win,
    _ => f64::from(c.points) * p_win,     // Default-Modus: PRODUKT
};
```

Die Netzbewertung wirkt **multiplikativ** als Faktor in [0,1] auf die
Platzierungspunkte. `p_win` liegt typisch in einem engen Band (~0,5-0,7), das
Verhaeltnis zwischen Kandidaten also bei hoechstens ~1,4 -- ein Kandidat mit 40 %
mehr Platzierungspunkten gewinnt IMMER. Ein Blend INNERHALB dieses Faktors
verschiebt ihn leicht und kann den Argmax nicht kippen.

**Damit ist der Nutzer-Hinweis auf die Multiplikation die Erklaerung fuer drei
Messnullen an einem Abend**: derselbe Deckel traf den Plattenterm im Blatt, den
Punkte-Kopf hier, und er ist der Grund, warum 7 Plattenpunkte einen einzelnen
Platzierungspunkt nicht ueberstimmen koennen. **Eine Bewertung, die die Wahl
kippen soll, muss ADDITIV in Punkteinheiten eingehen.**

### Stufe 2 -- additiv, aber mit der falschen Groesse: SCHLECHTER als der Bezug

| Plattengewicht | vertikal | Spalten/20 | Endstand |
| -------------: | -------: | ---------: | -------: |
| 0,3 | 0,35 | 1 | 44,65 |
| 1,0 | 0,35 | 1 | 43,70 |
| 3,0 | 0,35 | 1 | 43,70 |

Die additive Form (Task #100: `punkte + w * calculate_end_scoring(..).total`)
wirkt -- und schadet. Zwei Fehler in der GROESSE, nicht in der Form:

1. **`.total` summiert ALLE aktiven Kriterien**, und darin dominiert der
   Spezialfeld-Posten: gemessen **-11,70** im Mittel (3,9 leere Spezialkuppeln a
   -3, siehe `PREREG_injektion_wertungsplatten.md`). In den Runden 1-4 sind fast
   alle Spezialfelder leer, der Term ist also ein grosser negativer Brocken, der
   die Wahl in Richtung "Spezialfelder fuellen" zieht statt Spalten zu bauen.
2. **Absolutwert statt Differenz.** Interessant ist, was die Platzierung am
   Plattenwert AENDERT (`nachher - vorher`), nicht der Absolutstand -- der ist
   fuer alle Kandidaten desselben Zuges in weiten Teilen gleich und traegt nur
   Rauschen bei.

### Folge fuer den naechsten Schritt

Der Term muss (a) additiv in Punkten sein -- das ist er jetzt --, (b) die
**Differenz** vor/nach dem Tiling nehmen, und (c) **je Kriterium gewichtbar**
sein, damit der Spezialfeld-Posten nicht die Geometrie ueberdeckt. Erst dann ist
gemessen, ob die Platzierungsseite die Blockade war; die bisherigen zwei Stufen
haben das NICHT beantwortet, sie haben zwei Formfehler aufgedeckt.
