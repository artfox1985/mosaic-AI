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
   -3, siehe `PREREG_scoring_plate_injection.md`). In den Runden 1-4 sind fast
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

---

## 8. Stufe 3 (Differenz + Gewicht je Kriterium): ALLES-ODER-NICHTS hat keinen Gradienten

Acht Zellen, Draftingseite in jeder auf w=1 / alpha=1 (Bezug 2,10 vertikal =
6 Spalten in 20 Partien, Endstand 45,30):

| Gewichtsvariante | Plattengewicht | vertikal | Spalten/20 | Endstand |
| ---------------- | -------------: | -------: | ---------: | -------: |
| ALLE | 0,3 | 0,35 | 1 | 44,65 |
| ALLE | 1 / 3 / 10 | 0,35 | 1 | 43,70 |
| GEO (nur Kriterium 1) | 0,3 / 1 / 3 / 10 | 0,35 | 1 | 44,55 |

**Alle acht Zellen exakt 0,35, und die GEO-Variante bit-identisch ueber vier
Gewichte.** Vierter Zahlengleichheits-Alarm des Abends, und wieder ein echter
Mechanismus.

### Zwei Hypothesen geprueft, eine widerlegt

**Widerlegt**: "der neue Zweig faellt auf eine GREEDY-Chip-Politik zurueck".
`top_k_tilings` ruft `collect_tilings`, und das nutzt `legal_steps(.., true)`
(`tiling_solver.rs:690`) -- die exakte Chip-Allokation ist drin.

**Bestaetigt, und es ist die Ursache**: `calculate_end_scoring` ist
**ALLES-ODER-NICHTS** (`scoring.rs:43`: "7 Pkt je vollstaendige vertikale Reihe
(6 Fliesen)"). In den Runden 1-4 wird praktisch nie eine Spalte VOLLENDET, also
ist die Differenz `nachher - vorher` fuer fast jeden Kandidaten **exakt 0** -- und
dann ist jedes Gewicht gleichgueltig. Der Term hat keinen GRADIENTEN, an dem eine
Platzierung "naeher an einer Spalte" erkennbar waere.

Das ist derselbe Fehler, den `wertung_progress` auf der Draftingseite bereits
loest: sein Modulkommentar (`scoring.rs:150-158`) sagt es woertlich -- *"die
Alles-oder-nichts-Platten geben bei Teilfuellung einen quadratisch skalierten
Teil-Bonus statt hartem 0"*. Ich habe auf der Draftingseite die stetige Form
benutzt und auf der Platzierungsseite die harte. Der Fehler ist meiner, nicht der
des Agenten -- die Spezifikation, die ich ihm gegeben habe, nannte
`calculate_end_scoring`.

### Naechster Schritt, klar umrissen

Im Platzierungsterm `calculate_end_scoring` durch
`wertung_progress_per_kriterium` ersetzen (dieselbe stetige Form, dieselben
alphas, dieselbe Gewichtung je Kriterium). Erst dann ist die Frage "ist die
Platzierung die Blockade" tatsaechlich gestellt -- die drei bisherigen Stufen
haben drei FORMFEHLER aufgedeckt und die Frage nicht beantwortet:

1. multiplikativ statt additiv (Produktform, Nutzer-Hinweis)
2. Absolutwert statt Differenz, und `.total` statt je Kriterium
3. alles-oder-nichts statt stetig -- kein Gradient

Bemerkenswert daran: keiner der drei war eine Frage der DOSIS. Alle drei waren
Fragen der FORM, und jede sah in den Zahlen wie ein Null-Befund aus.

---

## 9. KORREKTUR (Nutzer, 2026-08-12): "in Runden 1-4 praktisch nie" war falsch

Ich hatte behauptet, in den Runden 1-4 werde praktisch nie eine Spalte vollendet,
und das als Erklaerung fuer den Null-Befund benutzt -- ungepruefte Zahl in einer
Schlussfolgerung, also ein REGEL-0-Bruch. Nutzer: *"das ist nicht korrekt."*

Gemessen an den 57 Nullpunkt-Partien (Spalten aus den Platzierungszeilen
rekonstruiert; UNTERGRENZE, weil das Log fuer Spezialfelder die Spalte nicht
nennt):

| Runde | Spaltenabschluesse |
| ----: | -----------------: |
| 3 | 1 |
| 4 | 2 |
| 5 | 2 |

**Drei von fuenf Abschluessen fallen in die Runden 1-4, also 60 %.** "Praktisch
nie" ist widerlegt.

### Der eigentliche Fund: das Potenzial liegt bereit

Hoechster erreichter Spaltenstand je Partie:

| Stand | Partien |
| ----: | ------: |
| 3 von 6 | 1 |
| 4 von 6 | 16 |
| **5 von 6** | **36** |
| 6 von 6 | 4 |

**In 36 von 57 Partien fehlt EINE Fliese zur vollen Spalte.** Das Netz kommt fast
immer bis an den Rand und schliesst nicht. Der Nutzer-Zielwert ist damit sehr viel
naeher, als 0,70 Plattenpunkte suggerieren -- es fehlt nicht an Aufbau, sondern am
letzten Schritt.

### Was von meiner Schlussfolgerung bleibt

Der Teil "kein Gradient" haelt, aber aus einem PRAEZISEREN Grund als dem, den ich
genannt habe: nicht weil Abschluesse in Runden 1-4 nicht vorkommen, sondern weil
ABSCHLUSSEREIGNISSE als solche selten sind (drei in 57 Partien). Ein Reihungsmass,
das bei JEDER Tiling-Entscheidung ausgewertet wird, sieht die Differenz also in
der ueberwiegenden Mehrheit der Kandidatenvergleiche als 0 -- und eine 0 gibt
keine Richtung.

**Genau deshalb ist die stetige Form der richtige Eingriff, und die Messung**
**oben sagt, wo sie ansetzen muss**: 36 Partien bei 5 von 6. Ein Term mit
quadratischer Teilgutschrift bewertet den Unterschied zwischen 5/6 und 6/6 mit
(6/6)^2 - (5/6)^2 = 0,306 mal dem Plattenwert 7 = **2,14 Punkte** -- gross genug,
um einen einzelnen Platzierungspunkt zu ueberstimmen, und er faellt bei JEDER
Kandidatenwahl an, nicht nur bei den drei Abschluessen.

---

## 10. FALLS die Platzierung es nicht ist: Deckenprobe auf die VERSORGUNG

**Nutzer-Aufbau 2026-08-12**: *"dann musst in der versorgung eventuell einen dummy
test fahren. etwas in der art alle steine verfuegbar, kein gegner. was macht das
netz und der solver dann."*

Das ist eine Deckenprobe: nimmt man die Versorgungsschranke weg und es entstehen
trotzdem keine Spalten, liegt es nicht an der Versorgung. Der Zusatz "und der
Solver" trennt zusaetzlich, ob die BEWERTUNG es nicht sieht oder die
ENTSCHEIDUNGSMASCHINERIE es nicht umsetzt.

### Zuschnitt: ein Eingriff statt eines Umbaus

GEPRUEFT: `NUM_PLAYERS = 2` ist eine Kompilierzeit-Konstante (`state.rs:14`) --
einen Solo-Modus gibt es nicht, und ihn einzufuehren waere ein Eingriff in den
Spielerbegriff, also teuer und risikoreich. Versorgungs-Knoepfe existieren keine
(grep ueber `MOSAIC_*`: kein Treffer fuer Supply/Factory/Bag).

**Nicht noetig**: traegt JEDE Fabrik ALLE Farben, ist der Gegner fuer die
VERFUEGBARKEIT gegenstandslos. Er zieht weiter Steine, aber dem Netz fehlt nie
eine Farbe. Damit ist "alle Steine verfuegbar, kein Gegner" mit einem Eingriff an
genau einer Stelle abgedeckt -- `fill_factories` (`state.rs:203`) -- statt mit
einem Umbau am Spielerbegriff.

Knopf `MOSAIC_VOLLE_VERSORGUNG` (Default aus, Paritaet unberuehrt): bei 1 wird
jede Fabrik mit allen Farben befuellt statt aus dem Beutel gezogen.

### Zwei Arme, und der zweite ist der aufschlussreichere

1. **Netz** @400 Sims gegen Heuristik @150, volle Versorgung.
2. **Nur Solver** (Heuristik auf beiden Seiten, `net: None`), volle Versorgung.

Arm 2 ist der Bezug, an dem sich Arm 1 messen muss: der Solver maximiert
Platzierungspunkte exakt und ist plattenblind ausserhalb Runde 5. Baut ER unter
voller Versorgung Spalten, entstehen sie als NEBENPRODUKT der
Platzierungsmaximierung -- dann braucht es gar keine Injektion, sondern nur
Versorgung. Baut er keine und das Netz auch nicht, ist die Ursache die Bewertung.

### Vier Ausgaenge, alle vorab gedeutet

| Netz | Solver | Deutung |
| ---- | ------ | ------- |
| viele Spalten | viele Spalten | **Versorgung war die Blockade.** Spaltenbau folgt aus der Platzierungsmaximierung, sobald die Farben da sind. |
| viele Spalten | wenige | Die Bewertung des Netzes kann es, der Solver nicht -- die Injektion greift, ihr fehlte nur das Material. |
| wenige | viele | Das Netz VERHINDERT, was der Solver von sich aus tut. Dann liegt es an der Blattbewertung, nicht an Versorgung oder Platzierung. |
| wenige | wenige | Weder Versorgung noch Platzierung. Dann bleibt der DURCHSATZ: 21 Fliesen fuer alle sechs Musterreihen einmal, 42 fuer zwei Spalten -- und die Frage, ob das in fuenf Runden ueberhaupt draftbar ist. |

**Der vierte Fall ist der, den ich fuer wahrscheinlich halte**, und er waere kein
Fehlschlag: er wuerde den Zielwert 14 als Durchsatzfrage entlarven statt als
Bewertungsfrage, und das ist eine andere Baustelle (Musterreihen-Kapazitaet,
Rundenzahl) als alles, was diese Nacht gemessen wurde. **Ausdruecklich als
Erwartung markiert, nicht als Befund** -- die Messung entscheidet.

### Messgroesse

Dieselbe wie durchgehend: Plattenpunkte des Kriteriums 1, plus die Verteilung des
hoechsten Spaltenstands. Letztere ist hier die wichtigere -- im Nullpunkt stehen
36 von 57 Partien bei 5 von 6 Feldern (Abschnitt 9). Unter voller Versorgung muss
sich diese Verteilung verschieben, wenn Versorgung die Ursache war; bleibt sie bei
5/6 stehen, ist sie es nicht.

---

## 11. VERDIKT: die Platzierungsseite ist NICHT die Blockade

Korrigierte Fassung (Plattenterm ADDITIV in Punkten, stetige Form, je Kriterium
gewichtbar, Netz-Stichentscheid als Faktor daneben statt verdraengt).
Draftingseite in allen Zellen auf w=1 / alpha=1.

| Konfiguration | vertikal | Spalten/20 | Endstand |
| ------------- | -------: | ---------: | -------: |
| **Draftingseite allein (Bezug)** | **2,10** | **6** | 45,30 |
| GEO (nur Kriterium 1), w=0,3-10 | 1,75 | 5 | 45,75 |
| ALLE, w=0,3 / 1 | 1,40 | 4 | 41,80 / 43,10 |
| ALLE, w=3 / 10 | 1,05 | 3 | 42,65 / 43,30 |

**Kein Zugewinn.** Die beste Fassung liegt bei 1,75 gegen 2,10 -- eine Spalte
Unterschied bei n=20, also Rauschen, und um Groessenordnungen entfernt von dem
Faktor 8, der zum Zielwert fehlt. Die in Abschnitt 5 vorab gesetzte
Falsifikationsschwelle ("bleiben die vertikalen Punkte unter 3") ist erreicht.

Bemerkenswert: GEO ist auf dem ENDSTAND leicht besser als der Bezug (45,75 gegen
45,30) bei einer Spalte weniger. Der Term schadet also nicht, er traegt nur nichts
zum Spaltenbau bei.

### Was diese Vorregistrierung geleistet hat, und was nicht

Die Hypothese ist WIDERLEGT, und das ist ein Ergebnis. Der Weg dorthin brauchte
aber vier Anlaeufe, weil jeder eine andere FORM des Terms falsch hatte -- keine
davon eine Dosisfrage, und jede sah in den Zahlen wie ein Sachbefund aus:

| # | Fehler | Symptom |
| - | ------ | ------- |
| 1 | `w` kuerzte sich zweimal heraus (Normierung + `max`) | bit-identische Rasterzellen |
| 2 | multiplikativ statt additiv (`punkte * p_win`) | bit-identische Punkte-Kopf-Zellen |
| 3 | alles-oder-nichts statt stetig | acht Zellen exakt 0,35 |
| 4 | Vorrang statt Ergaenzung (meine Auftragsformulierung) | 0,70 statt 2,10 |

**Drei der vier hat der Nutzer aufgedeckt, nicht meine Messung.** Die Lehre ist
nicht "mehr Zellen fahren", sondern: bei einem Null-Befund zuerst die FORM des
Eingriffs pruefen, nicht die Dosis. Der billigste Test dafuer bleibt die
Zahlengleichheit bei gleichen Seeds.

### Naechster Schritt: die Versorgungs-Deckenprobe (Abschnitt 10)

Damit sind Drafting UND Platzierung als Blockade ausgeschlossen. Was bleibt, ist
die in Abschnitt 10 vorregistrierte Deckenprobe -- und die dort notierte Erwartung
(weder Versorgung noch Platzierung, sondern DURCHSATZ) hat nach diesem Ergebnis
mehr Gewicht, bleibt aber eine Erwartung.

Die tragende Zahl fuer den Durchsatz-Verdacht steht in Abschnitt 9: **36 von 57
Partien erreichen 5 von 6 Feldern.** Das Netz baut auf und schliesst nicht -- und
weder eine bessere Draftinglenkung noch eine plattenbewusste Platzierung aendert
das. Genau dieses Muster erwartet man, wenn die letzte Fliese schlicht nicht
verfuegbar ist.

---

## 12. Deckenprobe GEBAUT und GEFAHREN (2026-08-12, Nutzer-Auftrag "mach das und halte es im prereg auch fest")

### Der Eingriff

`MOSAIC_VOLLE_VERSORGUNG=1` in `state.rs::fill_factories` (Default aus, Paritaet
geprueft unveraendert): die Fabriken werden deterministisch aus dem vollen
Farbkreis befuellt statt aus Beutel und Turm. Jede kleine Fabrik traegt 4 Fliesen
(`TILES_PER_SMALL_FACTORY`) bei 5 Farben -- "alle verfuegbar" gilt also UEBER die
Fabriken hinweg: jede bekommt einen um ihren Index versetzten Ausschnitt, sodass
jede Farbe in jeder Runde mehrfach vorkommt. Beutel und Turm werden umgangen, es
erschoepft also nichts.

**Damit ist der Gegner fuer die VERFUEGBARKEIT gegenstandslos** -- er zieht weiter
Steine, aber dem Netz fehlt nie eine Farbe. Das ersetzt den vom Nutzer genannten
"kein Gegner"-Teil, ohne `NUM_PLAYERS` anzutasten (Kompilierzeit-Konstante,
`state.rs:14`).

**Ausdruecklich ein DIAGNOSE-Knopf**: eine Partie damit ist nicht regelkonform und
darf nie in ein Gating oder einen Trainingskorpus geraten. Der Kommentar an der
Codestelle sagt das ebenfalls.

### Die vier Arme

| Arm | Sims | Versorgung | Frage |
| --- | ---: | ---------- | ----- |
| `netz_normal` | 400 | normal | der bekannte Bezug |
| `netz_voll` | 400 | **voll** | hilft Versorgung dem Netz? |
| `solver_normal` | 1 | normal | was tut der Solver ohnehin? |
| `solver_voll` | 1 | **voll** | hilft Versorgung dem Solver? |

Der Solver-Arm ist der aussagekraeftigere: er maximiert Platzierungspunkte exakt
und ist ausserhalb Runde 5 plattenblind. Baut ER unter voller Versorgung Spalten,
entstehen sie als NEBENPRODUKT der Platzierungsmaximierung -- dann braucht es gar
keine Injektion, nur Versorgung.

`--net-sims 1` als Solver-Naeherung, nicht als reiner Heuristik-Arm: bei einer
Simulation entscheidet praktisch der Solver/die Priors, und der Messpfad bleibt
derselbe (dieselben Seeds, dieselbe Auswertung). **Als Naeherung markiert** -- ein
echter Heuristik-gegen-Heuristik-Arm liefe ueber einen anderen Einstiegspunkt und
waere nicht seedgepaart mit den Netz-Armen.

### Messgroesse: die VERTEILUNG, nicht der Mittelwert

Entscheidend ist der hoechste erreichte Spaltenstand je Partie, nicht der
Plattenpunkt-Mittelwert. Grund steht in Abschnitt 9: im Nullpunkt stehen **36 von
57 Partien bei 5 von 6 Feldern**. War die Versorgung die Ursache, MUSS sich diese
Verteilung nach rechts verschieben. Bleibt sie bei 5/6 stehen, ist sie es nicht --
und dann bleibt der Durchsatz als letzte Erklaerung (21 Fliesen fuer alle sechs
Musterreihen einmal, 42 fuer zwei Spalten, in fuenf Runden).

Die Schwelle fuer "Versorgung hilft" ist vorab auf **+0,70 vertikale Punkte**
gesetzt (= zwei Spalten mehr in 20 Partien); alles darunter ist bei der auf 0,35
gequantelten Metrik nicht unterscheidbar.

---

## 13. DURCHSATZ-ERWARTUNG ZURUECKGEZOGEN (Nutzer, 2026-08-12)

*"ist möglich und wird regelmäßig von menschlichen spielern so gemacht"* -- zu zwei
geschlossenen Spalten (14 Punkte) in einer Partie.

Ich hatte in Abschnitt 10 notiert, ich hielte den DURCHSATZ fuer die
wahrscheinlichste Ursache, und das mit "21 Fliesen fuer alle sechs Musterreihen
einmal, 42 fuer zwei Spalten" begruendet. **Die Rechnung war falsch, in zwei
Punkten, und beide haette ich wissen muessen:**

1. **Spezialfelder fuellen Zellen OHNE Fliese.** `dome.rs:54-59`: `is_filled()`
   liefert fuer `SpaceType::Special` den Wert `placed_special`. Ich habe das in
   Abschnitt 9 selbst belegt und in der Oekonomie-Rechnung dann nicht angewandt.
   Mit zwei Spezialfeldern in einer Spalte braucht sie VIER Lieferungen, nicht
   sechs.
2. **Die billigen Musterreihen sind waehlbar.** Reihe 0 kostet 1 Fliese, Reihe 5
   kostet 6 (`board.rs:31-33`: `capacity = row_index + 1`). Vier billige Reihen
   sind 1+2+3+4 = **10 Fliesen**, nicht 21 -- und ueber fuenf Runden liefert jede
   Reihe mehrfach. Meine Rechnung hat die TEUERSTE mögliche Route angesetzt und
   sie dann fuer die einzige gehalten.

**Folge**: der Zielwert 14 ist erreichbar, und zwar nach Nutzer-Auskunft aus dem
tatsaechlichen Spiel routinemaessig. Damit ist die Durchsatz-Erklaerung
gestrichen, bevor sie gemessen wurde -- und mit ihr meine letzte oekonomische
Ausrede.

### Was nach Drafting, Platzierung und Durchsatz noch bleibt

Die Deckenprobe (§12) laeuft und klaert die Versorgung. Faellt auch die weg, bleibt
die Ursache im Lernen und in der Sichtweite, nicht im Spiel:

1. **Die Suchtiefe reicht ueber Rundengrenzen nicht.** Eine Spalte zu bauen ist
   eine Absicht ueber drei bis fuenf Runden. Das ist genau die
   "Rundenvorausschau", die im Projekt als HARTE Anforderung gilt (siehe
   `feedback_dfs_leaf_ruled_out`: rundenuebergreifende Weitsicht ist nicht
   verhandelbar). 400 Simulationen mit Rundenuebergangs-Sampling sehen eine
   Absicht ueber vier Runden womoeglich nicht.
2. **Das Netz hat solches Spiel nie gesehen.** Der Korpus stammt aus Self-Play
   eines Champions, der keine Spalten baut -- die Politik kann nicht bewerten, was
   in ihrer eigenen Erfahrung nicht vorkommt. Das ist ein
   Verteilungs-Henne-Ei-Problem, und es ist GENAU das, wofuer der Nutzer-Plan die
   Injektion vorgesehen hat: injizieren, damit die Zuege ueberhaupt vorkommen,
   daraus Self-Play mit gestreutem Gewicht erzeugen
   (`PREREG_scoring_plate_injection.md` N2), den Ownership-Kopf daran lernen
   lassen, dann die Injektion abschalten.

**Punkt 2 ist die Lesart, die zu allen Messungen dieser Nacht passt**: die
Injektion HAT das Verhalten bewegt (1,05 -> 2,10, also verdoppelt), aber sie kann
in einer einzigen Arena-Partie nur die Zugwahl verschieben, nicht die Bewertung
neu lernen. Der Sprung auf 14 waere dann kein Injektions-Ergebnis, sondern ein
TRAININGS-Ergebnis -- und die Injektion nur das Werkzeug, das den Korpus dafuer
erzeugt. **Als Lesart markiert, nicht gemessen.**

---

## 14. ERGEBNIS DER DECKENPROBE + die Farbschranke (2026-08-12)

### Versorgung ist NICHT die Blockade -- gemessen

| Arm | vertikal | Verteilung hoechster Spaltenstand | 6/6 | Endstand |
| --- | -------: | --------------------------------- | --: | -------: |
| Netz, normal | 1,05 | 4->6, **5->12**, 6->2 | 2/20 | 47,80 |
| Netz, **volle Versorgung** | 0,70 | 3->1, 4->5, **5->14** | **0/20** | 46,20 |

Die Verteilung verschiebt sich NICHT nach rechts -- sie sammelt sich noch staerker
bei 5 von 6. Die vorab gesetzte Schwelle (+0,70) ist klar verfehlt.

### Der Solver-Arm ist GESCHEITERT, nicht nur ungenau

`--net-sims 1` lieferte Endstand **8,30** bei 0 von 20 Siegen -- das ist kein
Solver, sondern ein Spieler ohne Suche. Der vom Nutzer gewuenschte Vergleich
("was macht das netz UND der solver dann") hat damit **nicht stattgefunden**. Ich
hatte es als "Naeherung" markiert; das war zu milde. Ein echter Solver-Arm braucht
den Heuristik-Einstiegspunkt, nicht ein kastriertes Netz.

Ein Nebenbefund aus genau diesem kaputten Arm ist aber verwertbar: selbst er
erreicht in 14 von 20 Partien 4 von 6 Feldern. **Bis 4/6 kommt man fast von
allein; die letzten ein bis zwei Felder kommen nie.**

### DIE FARBSCHRANKE -- was ich die ganze Nacht nicht geprueft habe

`dome.rs:61-70`:

```text
match self.space_type {
    SpaceType::Normal => Some(color) == self.required_color,
    SpaceType::Wild   => true,
    SpaceType::Special => false,
}
```

**Jede normale Kuppelzelle verlangt GENAU EINE Farbe.** Eine Spalte zu schliessen
heisst damit: fuer jede ihrer sechs Zellen muss die zuliefernde Musterreihe mit
exakt der Farbe gefuellt sein, die diese Zelle fordert -- und eine Musterreihe
traegt nur EINE Farbe (`board.rs`, `PatternLine::color`). Sechs Zellen, sechs
festgelegte Farben, je eine Musterreihe, deren Kapazitaet r+1 Fliesen dieser
einen Farbe verlangt.

### Die Kette schliesst sich, und die Ursache ist keine Bewertungsfrage

**Volle Versorgung hat die Farbschranke aufgehoben** -- jede Farbe war jederzeit
draftbar. Es half NICHT. Das Material war da, der Plan nicht.

Eine Spalte verlangt eine **Farbfestlegung je Musterreihe, auf eine bestimmte
Spalte gerichtet, ueber mehrere Runden gehalten**. Das ist eine ABSICHT, keine
Stellungsbewertung -- und deshalb war sie mit keiner der vier Termformen dieser
Nacht erreichbar. Alle vier bewerten einen Zustand; keine kann eine mehrrundige
Farbzusage darstellen.

### Was daraus folgt -- und es ist der Nutzer-Plan von Anfang an

Ausgeschlossen sind jetzt, jeweils gemessen: Drafting-Dosis (Decke 2,10),
Platzierung (kein Zugewinn), Versorgung (kein Zugewinn), Durchsatz
(Nutzer-Auskunft: Menschen tun es routinemaessig, und meine Rechnung war falsch,
§13).

Was bleibt, ist die **rundenuebergreifende Absicht** -- und die ist im Projekt als
harte Anforderung bekannt (`feedback_dfs_leaf_ruled_out`). Zwei Wege, und der
zweite ist der vom Nutzer geplante:

1. **Sichtweite**: 400 Simulationen mit Rundenuebergangs-Sampling sehen eine
   Absicht ueber vier Runden womoeglich nicht. Pruefbar ueber einen Sim-Sweep
   (400 / 1600 / 6400) auf denselben Seeds -- steigen die Spaltenabschluesse mit
   dem Budget, ist es Sichtweite.
2. **Lernen**: der Korpus stammt aus Self-Play eines Champions, der keine Spalten
   baut. Die Politik kann nicht bewerten, was in ihrer Erfahrung nicht vorkommt.
   Genau dafuer ist die Injektion im Nutzer-Plan gedacht: sie erzeugt Partien, in
   denen die Zuege VORKOMMEN, das gestreute Gewicht je Partie sorgt fuer Vielfalt
   (`PREREG_scoring_plate_injection.md` N2), der Ownership-Kopf lernt daran, und
   danach kann die Injektion abgeschaltet werden.

**Der Sprung auf 14 waere demnach kein Injektions-Ergebnis, sondern ein
TRAININGS-Ergebnis** -- und die Injektion nur das Werkzeug, das den Korpus dafuer
erzeugt. Dass sie das Verhalten messbar bewegt (1,05 -> 2,10, also verdoppelt),
ist unter dieser Lesart genau ihre Aufgabe und kein Fehlschlag. **Als Lesart
markiert; Weg 1 ist der billigere Test und sollte zuerst laufen.**
