# Domänenwissen Mosaic — abgeleitete und gemessene Größen

**Abgrenzung.** `engine_manual.md` gibt die **Regeln** normativ wieder. Dieses
Dokument enthält, was aus ihnen **folgt** und was im Korpus **gemessen** ist.
Die Trennung ist Absicht: sonst liest irgendwann jemand eine Messung als Regel.

**Warum es diese Datei gibt** (angelegt 2026-08-11, Nutzer-Frage *"wo hast das
domänenwissen bisher gespeichert?"*): es war verstreut — Versorgungsrechnung als
Docstring in `tools/pattern_row_availability.py`, Strategie-Herleitung in
`evaluations/PREREG_plate_head.md`, Plattenanteil in `evaluations/STATUS.md`.
Letzteres ist der eigentliche Fehler: STATUS trägt laut eigenem Kopf „nur
AKTUELLES und OFFENES" und wird regelmäßig in `archive/history.md` geleert —
Domänenwissen dort wird also mitarchiviert. Vorregistrierungen sind je
Experiment, ein Tool-Docstring hängt an seinem Tool.

---

## 1. Musterreihen-Durchsatz: was tatsächlich auf der Kuppel landet

**Gemessen** mit `tools/pattern_row_throughput.py`, 60 Dateien = **600 Partien**
des `selfplay_v20wdl_*`-Korpus, Einheit der Auswertung = **Partie** (über beide
Bretter gemittelt), CI 95 %.

Musterreihe *r* speist Rasterreihe *r*, eine Fliese je Kachelphase. „Gesamt" =
belegte Zellen der Rasterreihe am Ende = **so oft hat Musterreihe r
abgeschlossen** (Maximum wäre 5, eine je Runde).

| Reihe | Kapazität | gesamt | je Runde | Rest in der Musterreihe |
|---|---|---|---|---|
| 1 | 1 | **4,80 ± 0,04** | 0,96 | 0,00 |
| 2 | 2 | **4,77 ± 0,04** | 0,95 | 0,02 |
| 3 | 3 | **2,84 ± 0,05** | 0,57 | 0,19 |
| 4 | 4 | **1,89 ± 0,05** | 0,38 | 0,76 |
| 5 | 5 | **0,84 ± 0,04** | 0,17 | 1,32 |
| 6 | 6 | **0,58 ± 0,03** | 0,12 | 1,62 |

Aufteilung je Runde (Mittel je Partie, CI 95 %):

| Reihe | Runde 1 | Runde 2 | Runde 3 | Runde 4 | Runde 5 |
|---|---|---|---|---|---|
| 1 | 0,88 | 0,93 | 0,91 | 0,95 | 1,13 |
| 2 | 0,84 | 0,96 | 0,97 | 0,94 | 1,07 |
| 3 | 0,05 | 0,63 | 0,70 | 0,64 | 0,82 |
| 4 | 0,02 | 0,43 | 0,50 | 0,40 | 0,53 |
| 5 | 0,00 | 0,03 | 0,23 | 0,32 | 0,26 |
| 6 | 0,00 | 0,01 | 0,15 | 0,23 | 0,19 |

### Was daraus folgt

1. **Reihen 1–2 sättigen** (4,80 und 4,77 von 5) und haben **0,00 bzw. 0,02
   Rest** — sie schließen praktisch jede Runde ab.
2. **Ab Reihe 3 bricht es steil ein**, monoton bis 0,58 bei Reihe 6.
3. **Der Rest-Wert ist die Diagnose**: Reihen 5 und 6 werden gefüttert (1,32 und
   1,62 Steine liegen am Ende dort), werden aber **nie voll**. Das Problem ist
   also nicht „wird nicht bedient", sondern „wird nicht fertig".
4. **Zeitfenster**: Reihen 5–6 liefern vor Runde 3 praktisch nichts (0,00 /
   0,03 / 0,01), Maximum in Runde 4. Ansammeln muss in Runde 1–2 beginnen und
   zahlt erst ab Runde 3 — das ist die rundenübergreifende Bindung, die einer
   Suche mit `bootstrap_horizon_rounds = 2` strukturell fehlt.
5. **Spalten und Diagonalen sind an Reihe 5/6 gefesselt.** Beide brauchen je
   eine Zelle in JEDER Rasterreihe, also je einen Abschluss jeder Musterreihe.
   Bei 0,84 und 0,58 Abschlüssen fehlen die beiden untersten regelmäßig ganz.
   Dazu müssen die sechs Zellen auch noch in DERSELBEN Spalte landen — zweite,
   davon unabhängige Hürde, und sie ist Platzierungswahl, nicht Versorgung.
   **Es gibt eine dritte, die hier lange fehlte: die Farbschranke** (Abschnitt
   7). Alle drei zusammen erklären die gemessene Spaltenrate von 0,4–1,2 %.

### Replikation über zwei Suchbudgets — Reihe 5/6 hängt NICHT am Budget

Dieselbe Messung auf `selfplay_v20wdlsw_*` (**derselbe Generator, 150 statt 600
Sims**), ebenfalls 60 Dateien / 600 Partien:

| Reihe | 600 Sims | 150 Sims | Differenz |
|---|---|---|---|
| 1 | 4,80 ± 0,04 | 4,91 ± 0,04 | +0,11 |
| 2 | 4,77 ± 0,04 | 4,89 ± 0,04 | +0,12 |
| 3 | 2,84 ± 0,05 | 2,86 ± 0,05 | +0,02 |
| 4 | 1,89 ± 0,05 | 2,04 ± 0,05 | +0,15 |
| 5 | **0,84 ± 0,04** | **0,83 ± 0,04** | −0,01 |
| 6 | **0,58 ± 0,03** | **0,54 ± 0,03** | −0,04 |

Rest in der Musterreihe, Reihe 6: 1,62 gegen **1,71**.

**Das schließt eine Erklärungsklasse aus.** Vierfaches Suchbudget bewegt die
Reihen 5 und 6 um −0,01 und −0,04, beides im Rauschen. Es ist also kein „die
Suche findet es mit genug Tiefe schon" — mehr Tiefe findet es nicht, weil nicht
danach gesucht wird. Das stützt die ZIEL-Erklärung (das WDL-Ziel kennt die Marge
nicht) und nicht die Aufwands-Erklärung.

Gegen-Befund, klein aber signifikant: die **billigen** Reihen 1, 2 und 4
schließen bei WENIGER Suche öfter ab (CIs überlappen nicht). Tiefere Suche
verteilt die Fliesen anders. *Deutung (ungemessen): plausibel zugunsten der
Platzierungspunkte langer Linien.*

**Was die Replikation NICHT leistet**: es ist derselbe Generator bei zwei
Budgets, also Budget- und keine Policy-Robustheit. Für letztere wäre
`selfplay_v19wdl_*` der Test (anderer Generator, andere Ära) — offen.

### Grenzen der Messung — nicht überlesen

- **Gesamtzahlen sind leicht UNTERSCHÄTZT**: der letzte Datensatz einer Partie
  ist der letzte Kachel*schritt*, nicht der Endzustand (dieselbe
  Einschränkung, die STATUS für die Plattenkopf-Labels vermerkt).
- **Die Runden-Aufteilung hat einen Grenzfehler**: Reihe 1 zeigt in Runde 5
  **1,13**, was unmöglich ist — je Runde kann eine Reihe höchstens einmal
  abschließen. In einem Teil der Partien wird die Kachelphase von Runde 4 den
  Runde-5-Datensätzen zugeschlagen. Die **Summen** sind unberührt (Endmaximum),
  nur die Zuordnung je Runde ist um bis zu eine Runde unscharf.
- **Regime**: Self-Play MIT Wurzelrauschen, also bewusst schwächeres Spiel als
  der Champion in der Arena. Das IST dieses Regimes, keine Könnens-Obergrenze.
- **Gegencheck zur Größenordnung**: Summe über alle Reihen = **15,72 Fliesen je
  Brett**; `evaluations/watchlist_v20_interim_review.md` zählte für die KI 17,2
  Kuppel-Legungen je Partie. Die Differenz zeigt in die Richtung des
  Unterschätzungs-Vorbehalts.

### Die vier Referenzpunkte

| Punkt | Quelle | Was er sagt |
|---|---|---|
| **DECKE** | `tools/pattern_row_availability.py` | wie oft *r* gleichfarbige Steine überhaupt verfügbar sind — policy-unabhängig, reine Versorgung |
| **BODEN** | Zufalls-Drafting | was ohne Absicht passiert |
| **IST** | `tools/pattern_row_throughput.py` (dieser Abschnitt) | was der Champion-Korpus tatsächlich schafft |
| **MENSCH** | `tools/probes/human_row_profile_probe.py`, Abschnitt 9 | was ein plattenbewusster Spieler daraus macht |

Der vierte Punkt fehlte bis 2026-08-30. Er ist der einzige, der zeigt, dass
die IST-Zeile eine Verhaltens- und keine Versorgungsgrenze beschreibt.

---

## 2. Punktquellen — zwei, die ständig verwechselt werden

| Quelle | Wert | Gilt |
|---|---|---|
| **Platzierungspunkt** (`round_end.rs::score_placed_tile`) | Länge der zusammenhängenden Waagerechten **plus** Senkrechten, je nur wenn > 1, sonst 1 → max **6+6 = 12** je Fliese | immer |
| **⭐ Kuppel-Bonus** (`round_end.rs::check_special_trigger`) | **Rasterreihe 1..6** (`slot_row*2 + sp_idx/2 + 1`) | immer, sobald das Spezialfeld gefüllt wird |
| **Wertungsplatte 7** (Code-Index 6) | **flach −3** je leer gebliebenem Spezialfeld | nur wenn diese Platte im Spiel liegt |

**`bonus_points = 3` in `dome.rs` ist NICHT der Punktwert**, sondern nur der
Typ-Diskriminator Special (`>0`) gegen Wild (`=0`). Wer ihn als Award liest,
bekommt eine flache 3. Das Feld darf auch nicht umgestellt werden — die Platte
kennt ihren Slot nicht, der Wert entsteht erst bei der Platzierung.

Der Platzierungspunkt ist **reihenfolgeabhängig**: die letzte Fliese einer
vollen Reihe holt 6, die erste 1. Das Optimum ist eine SEQUENZ, keine
Zellmenge — eine zeitlose Potenzialkarte gibt eine Richtung, nicht das Optimum.

---

## 3. Wertungsplatten — Werte und Struktur

Aus `docs/engine_manual.md` Abschnitt 6: **3 von 8** Platten kommen ins Spiel,
aus 4 Paaren je höchstens eine (physisch 4 doppelseitige Platten).

| Nr. (Handbuch) | Code-Index | Kriterium | Wert |
|---|---|---|---|
| 1 | 0 | horizontale Reihen | 3 je Reihe |
| 2 | 1 | vertikale Reihen | 7 je Spalte |
| 3 | 2 | Diagonalen | 10 je Diagonale (max. 2) |
| 4 | 3 | mehrfarbige Felder | 2 je Wildfeld, **nur wenn alle belegt** |
| 5 | 4 | äußere Felder | 1 je Randfliese |
| 6 | 5 | Eckplatten | 3 obere / **8 untere**, je komplett |
| 7 | 6 | Spezialfelder | **−3** je leer geblieben |
| 8 | 7 | farbenreiche Reihen | 4 je Reihe mit ≥5 Farben |

**Die Handbuch-Nummerierung ist um eins gegen die Code-Indizes verschoben.**

**Anteil am Ergebnis, und die Falle darin**: über 1.200 Self-Play-Endbretter
sind die Wertungsplatten im **Mittel** 1,71 von 23,39 Punkten (7 %). Dieser
Mittelwert ist irreführend — der Anteil steigt monoton auf **24,7 % im obersten
Fünftel** (r = +0,695) und ist in den unteren zwei Fünfteln negativ. Der Nutzer
erreicht ~17 Plattenpunkte bei ~61 Gesamt = 28 %. Der Mittelwert ist klein,
**weil** das Defizit im Self-Play symmetrisch ist.

Und die Platten sind kein getrennter Topf: eine geschlossene Spalte bringt
**21 Platzierungspunkte plus 7 Plattenpunkte**. Ein Term, der auf
Spaltenabschluss zieht, kassiert beide Währungen.

---

### Die vier Ausschlusspaare, namentlich

`MUTUALLY_EXCLUSIVE_PAIRS` (scoring.rs:60-65, geprüft 2026-08-30):

| Paar (Code-Indizes) | Bedeutung |
|---|---|
| (0, 7) | horizontale Reihen ⟷ farbenreiche Reihen |
| (6, 3) | Spezialfelder ⟷ mehrfarbige Felder |
| (4, 1) | äußere Felder ⟷ vertikale Reihen |
| (2, 5) | Diagonalen ⟷ Eckplatten |

Praktische Folge, die man sich merken kann: **bei aktivem k1 ist k4 garantiert
aus, bei aktivem k2 garantiert kein k5** – und umgekehrt.

### Wie viele Ereignisse jedes Kriterium überhaupt hat

| Kriterium | Atome | je Atom |
|---|---:|---|
| k0 horizontale Reihen | 6 | +3 |
| k1 vertikale Reihen | 6 | +7 |
| k2 Diagonalen | **2** | +10 |
| k3 mehrfarbige Felder | 9 | 2 je Wildfeld, nur wenn ALLE belegt |
| k4 äußere Felder | **20** | +1 |
| k5 Eckplatten | 4 | +3 / +3 / **+8 / +8** |
| k6 Spezialfelder | 9 | **−3** je leer geblieben |
| k7 farbenreiche Reihen | 6 | +4 |

Summe **62 Atome je Spieler** (`PREREG_plate_head.md`, Atomzahl aktualisiert).
Die Zahl ist für die Priorisierung tragend: k2 ist auf **zwei** Ereignisse
gedeckelt, k4 hat **zwanzig** additive Chancen. Ein hoher Einzelwert bei
wenigen Atomen ist etwas anderes als ein kleiner bei vielen.

### Wie oft ein Kriterium ueberhaupt erreicht wird

**Die Plattenziehung ist bias-frei** (`tools/scoring_tile_distribution.py`,
kompletter v16-Korpus, 600 Dateien = 6.000 Spiele): jede der 8 Platten liegt
in **37,0-37,9 %** der Partien im Spiel (Erwartung 3/8 = 37,5 %), je
Ausschlusspaar kommt jede Seite in 49,7-50,5 % in den Pool, alle 32 moeglichen
3er-Kombinationen treten auf, 0 Ausschluss-Konflikte. Fuer jede
Erwartungswert-Rechnung heisst das: **ein Kriterium kostet oder zahlt nur in
gut einem Drittel der Partien.**

**Erreichungsraten im Normalspiel.** Zwei Erhebungen mit VERSCHIEDENEN
Nennern, deshalb getrennt zu lesen:

| Kriterium | je Partie mind. 1x (Arm A, 3.000 Partien) | je Atom (b19_best, 1.500 Partien) |
|---|---|---|
| k0 Zeilen voll | 764 (25 %) | 4,278 % |
| k1 Spalten voll | 95 (**3,2 %**) | **0,517 %** |
| k2 Diagonalen | 11 (0,4 %) | 0,117 % (nur 7 Positive) |
| k3 alle Joker | 1.193 (40 %) | 39,800 % |
| k5 Ecken (3er) | 2.786 (93 %) | 26,650 % |
| k5 Ecken (8er) | 6 (**0,2 %**) | – |
| k6 offene Spezialfelder | 3,72 je Partie | – |
| k7 farbenreiche Reihen | 191 (6 %) | 1,017 % |

Quellen: `PREREG_ownership_corpus.md` §8 (Deckungsbericht Arm A, Seite p0,
p0/p1 nahezu symmetrisch) und `archive/history.md` (Runde-3-Zustaende,
3.000 Bretter). **Die beiden Spalten sind konsistent**: 6 Spalten je Brett mal
0,517 % ergibt rund 3,1 % Bretter mit mindestens einer -- gemessen 3,2 %.

**Vorbehalt, der nicht weggelassen werden darf**: beide Erhebungen laufen auf
Netzen, die die Wertungsplatten nicht beruecksichtigen. Das ist der IST-Zustand
plattenblinden Spiels, **keine Koennensgrenze** -- der `hv2`-Lehrer erreicht
0,73-0,798 volle Spalten je Partie gegen die 0,086-0,10 des Champions. Zur
Einordnung siehe „Nie auf plattenblindes Spiel eichen" in `working_rules.md`.

## 4. Versorgung — die harten Zahlen

Aus dem Code, nicht geschätzt (`tile.rs`, `state.rs`, `board.rs`):

- **5 ziehbare Farben**, `TILES_PER_COLOR = 13` → **65 Steine** im Kreislauf
  (Wild ist kein ziehbarer Stein)
- je Runde **4×4 + 5 = 21 Sonnenfliesen** — das ist die **vollständige**
  Rundenversorgung
- **Mondfliesen sind KEINE zusätzliche Versorgung**: beim Rundenaufbau wird die
  Mondseite geleert, was dorthin kommt ist der Rest eines Sonnen-Zugriffs —
  dieselben Steine, nur umsortiert (`execution.rs`, `moon_order`), und vom Mond
  darf nur der oberste Stein je Stapel genommen werden
- Musterreihe *r* hat Kapazität *r*; Reihen bleiben über den Rundenwechsel
  **liegen** (`execute_end_tiling` räumt nur unplatzierbare Reihen ab)
- **Es gibt KEINE reihenübergreifende Farbeinschränkung** (`board.rs::can_accept`
  prüft nur „Reihe voll?" und „eigene Farbe passt?"). Theoretisch können alle
  sechs Reihen dieselbe Farbe tragen; 13 Steine einer Farbe reichen nur nicht
  für alle sechs (1+2+…+6 = 21).

**Ein Durchgang aller sechs Musterreihen kostet 21 Steine.** Bei ~52,5 Fliesen
Aufnahme je Partie passen zwei Durchgänge (80 %), drei nicht (120 %).

---

### Die zweite Versorgung: Bonus-Chips

**Regellage** (normativ in `engine_manual.md:49-51`, `:104-106`, `:154-156`,
hier nur als Prämisse): 20 Chips im ganzen Spiel, 4 je Runde; jeder Spieler
nimmt **genau 2 je Runde, und zwar als PFLICHT**, nicht als Obergrenze. Eine
fehlende Zelle kostet 2 farbgleiche oder 3 beliebige Chips.

**Was daraus folgt**: der Vorrat für BEIDE Spieler zusammen liegt bei rund 20,
ein einzelner hält selten mehr als eine Handvoll. Im Code fällt
`greedy_chip_indices` (round_end.rs:487) automatisch auf die 3er-Variante
zurück, wenn keine zwei farbgleichen da sind, und deckt Mehrfeld-Füllung ab
(`2*missing <= s <= 3*missing`) – der Ein-Zellen-Fall ist nur der
wahrscheinlichste, nicht der einzige.

**Der Engpass ist damit nicht der Farbzufall, sondern der BESTAND zum
Entscheidungszeitpunkt** (Herleitung der Quelle, ausdrücklich ungemessen): der
Rundenende-Solver verbraucht gehaltene Chips selbst (`TilingStep::Chips`), und
drei ungenutzte Chips plus blockierende Reihe im richtigen Zustand plus
sofortige Platzierbarkeit fallen selten zusammen. In 80 Partien kam keine
einzige Chip-Vollendung von Rasterreihe 6 zustande.

**Das qualifiziert die Entwarnung in Abschnitt 5** („die KI chippt im
Self-Play routiniert", 4,92 Abschlüsse je Partie): ohne die Mengenschranke
liest man 4,92 als Überfluss, obwohl der Vorrat für BEIDE Spieler zusammen bei
rund 20 liegt.

### Die Farbanforderungen beider Spieler sind VERSCHIEDEN

Prämisse aus dem Handbuch (`engine_manual.md:66`, `:91`): jeder Spieler zieht
seine Kuppelplatten selbst aus der Auslage, **Position und Rotation sind
unbeschränkt**.

Daraus folgt: welche Farben eine Spalte verlangt, bestimmt das individuelle
Plattenlayout – **die Farbanforderungen beider Spieler sind verschieden.
Geteilt sind die KRITERIEN, nicht die Farben.**

Daraus folgt direkt, dass Blockade über Farbe kaum greift – und die Messung
bestätigt es: „Farbe nie verfügbar, während Zeile offen" wurde mit **0 %**
gemessen. **Farbknappheit ist in diesem Spiel nicht der Engpass.**

### Blindziehung am Kuppelstapel: die optimale Tiefe ist 1

In jedem geprüften Fall ist Tiefe 1 optimal: nach der Pflichtziehung liegt
bereits eine Platte im Wert von **2,9 bis 9,0 Punkten** in der Hand, und die
erwartete VERBESSERUNG durch eine weitere Ziehung bleibt unter dem einen
Punkt, den sie kostet. Das Spielerverhalten deckt sich damit: Mensch 19 von 20
Serien auf Tiefe 1 (95 %), KI 25 von 25 (100 %).

**Vorbehalt, der mitgehört**: fünf konstruierte Bretter, ein Seed, und die
Potenzial-Näherung `V` ist eine Näherung. Die Arena-Abnahme (n=200) fand
KEINEN Stärkeunterschied; die Quelle lässt offen, ob `V` zu niedrig angesetzt
war. Als Größenordnung belastbar, als Konstante nicht.

## 5. Weitere gemessene Struktur

- **Slot-Gradient der Spezialfelder**: die Slot-Reihe hängt starr an den
  Musterreihen, `pattern_row = slot_row * 2 + sp_idx / 2` (round_end.rs:361,
  geprüft 2026-08-30). Obere Slots werden von den Musterreihen 1-2 gespeist,
  mittlere von 3-4, untere von 5-6; der Trigger zahlt `pattern_row + 1`, also
  1-2 oben und 5-6 unten. **Struktur ist diese Achse.** Die Leer-Raten darauf
  sind REGIMEABHÄNGIG:

  | Leer-Rate je Slot-Reihe | plattenblinde Netze (par.3) | hv2-Lehrer | v22-b06 |
  | --- | --- | --- | --- |
  | oben | ~0,13 | 0,499 | 0,535 |
  | mitte | – | 0,833 | 0,819 |
  | unten | ~0,84 | 0,807 | 0,881 |

  **Berichtigt 2026-08-30.** Hier stand, der Gradient sei „monoton, und über
  zwei Generator-Ären deckungsgleich, also Spielstruktur statt
  Champion-Verhalten". Das Argument trägt nicht: BEIDE Ären waren
  plattenblind, und Übereinstimmung zwischen zwei Agenten mit demselben
  blinden Fleck belegt keine Spieleigenschaft. Die Neumessung am
  spaltenkompetenten Lehrer hebt die obere Rate von ~0,13 auf 0,499 – er
  tauscht kurze Reihen gegen lange, also schließen die oberen Slots seltener.
  Quelle: `PREREG_special_tile_yield.md` par.7 (3.000 hv2-Partien, 200
  b06-Partien).

  **Was über alle drei Regime hält**: die untere Reihe bewegt sich kaum
  (0,84 / 0,807 / 0,881). Die teuersten Spezialfelder bleiben in jedem bisher
  gemessenen Regime der größte unabgeholte Posten. Zur Frage, wann man sie
  meiden sollte und wann nicht, siehe Spielstrategie 8 (gilt nur bei aktivem
  Kriterium 6).

- **Startkuppel-Platzierung ist deterministisch** (`self_play.rs::choose_start_placement`):
  der Farb-Score ist positions- und rotationsunabhängig, der Eckbonus für alle
  vier Ecken identisch → immer Ecke (0,0), immer 0°. Position und Rotation sind
  tote Freiheitsgrade; nur die Platten-WAHL variiert.
- **Zufalls-Boden gemessen** (`plattenkopf_referenzlauf_zufall`, 400 Partien,
  uniformes Drafting): **8,35 von 36** Feldern belegt, Reihen/Spalten/Diagonalen
  vollständig in **0,000–0,001** der Bretter, Spezialfeld-Freischaltungen
  **0,10** je Brett (4,397 von 4,500 vorhandenen bleiben leer). Der Champion mit
  15,72 belegten Feldern ist also klar besser als blindes Ziehen — der Abstand
  nach oben ist trotzdem groß.
- **Das Defizit ist ein PLATZIERUNGS-, kein Mengenproblem.** Innerhalb
  derselben Watchlist-Partien: KI **17,2** Kuppel-Legungen, Mensch **17,5** —
  praktisch gleich viel. Freischaltungen **0,6 gegen 3,1**. Die KI legt genauso
  viele Steine, nur dorthin, wo sie keine Platte vollenden.
- **Der Engpass ist das DRAFTING, nicht das Tiling** (aus
  `archive/history.md:10112-10140`, v19-Ära; von mir dort gelesen, die
  Ursprungsmessungen nicht nachgeprüft): der Tiling-Solver KANN chippen
  (`TilingStep::Chips`), und „chip-abschließbar" ist **bereits ein expliziter
  Netz-Input** (Chip-Farbzähler + Abschließbarkeits-Flag je Musterreihe in
  `state_to_tensor`). Es fehlt also weder Ausführung noch Information. Was fehlt,
  sind **tiefe Reihen**: R5+R6-Nahmen Mensch 37 %, KI 22 % (v19) bzw. 40,4 % zu
  22,7 % (v20, Watchlist) — **über zwei Ären stabil**, die Drafting-Seite
  derselben Sache, die der Musterreihen-Durchsatz von der Ergebnisseite zeigt.
  Ebenfalls dort protokolliert und wichtig, weil es eine naheliegende Erklärung
  ausschließt: die These einer „selbstverstärkenden Schleife" wurde
  ZURÜCKGEZOGEN — der Korpus ist voll mit Chip-Abschlüssen (4,92 je Partie im
  v18-Korpus, 4,85 in frischen v19wdl-Sockeln). Die KI chippt im Self-Play
  routiniert.
- **Mensch gegen Champion v20** (10 gewertete Partien,
  `watchlist_v20_interim_review.md`): Mensch 7:3, Ø +14,5 Punkte. Größter Einzelposten sind die Spezialpunkte —
  **10,3 gegen 1,3 je Partie**, also 9,0 der 14,5 Punkte Differenz. Die KI
  schaltet in **6 von 10** Partien kein einziges Spezialfeld frei, der Mensch in
  9 von 10 schon in Runde 2.
- **Zuege und Verzweigungsgrad je Runde** (uebernommen aus
  `evaluations/actions_per_round.md`): **~11 Zuege pro Runde und Spieler**.
  Gemessen in Runde 1; in spaeteren Runden werden es weniger, weil weniger
  Kuppelplatten zur Verfuegung stehen. Der Verzweigungsgrad faellt dabei stark:

  | Zug | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
  |---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
  | Aktionen | 195 | 152 | 134 | 117 | 83 | 44 | 42 | 7 | 7 | 5 | 2 |

  Die ersten vier Zuege tragen also den Loewenanteil der Entscheidung (195 bis
  117 Optionen), ab Zug 8 ist die Runde praktisch determiniert (<= 7 Optionen).
### Punktestand je Runde — und warum es zwei Zahlenreihen gibt

**Referenz ist der ARENA-Modus, nicht das Self-Play.** Gemessen an den 22
Elo-Logs (`static/log/elo/*.log`, Mensch gegen KI, Modelle `v19_2d_best` und
`v20_2d_opp_brierbest`, 400 Sims), Stand nach der letzten punktewirksamen Zeile
je Runde:

| Runde | Mensch | Zuwachs | KI | Zuwachs | Vorsprung |
|---|---:|---:|---:|---:|---:|
| 1 | 7,0 | 7,0 | 4,0 | 4,0 | 3,0 |
| 2 | 13,3 | 6,3 | 9,2 | 5,2 | 4,1 |
| 3 | 23,0 | 9,7 | 19,2 | 10,0 | 3,8 |
| 4 | 37,7 | 14,7 | 29,2 | 10,0 | 8,5 |
| 5 | 59,2 | 21,5 | 47,6 | 18,4 | 11,6 |
| **nach Endwertung** | **74,4** | | **55,7** | | **18,7** |

Zwei Ablesungen: **der Zuwachs waechst monoton** — die letzte Runde ist drei-
bis fuenfmal so viel wert wie die erste. Und **der Vorsprung des Menschen
entsteht in Runde 4/5**: bis Runde 3 sind es 3,8 Punkte, danach oeffnet sich die
Schere auf 11,6 und mit der Endwertung auf 18,7 — genau dort landen die
Wertungsplatten.

**Im SELF-PLAY liegen dieselben Staende deutlich tiefer** (Bewertungssatz
`data/holdout`, Arm `a`, 300 Partien): 5,8 / 8,8 / 12,1 / 17,3 / **26,6** gegen
die 47,6 der Arena. **Das ist kein Widerspruch, sondern Absicht**
(Nutzer-Erklaerung 2026-08-18): Self-Play laeuft mit Wurzelrauschen und
Besuchs-Sampling und mit 200 statt 400 Sims — der Agent spielt dort bewusst
schlechter, damit der Korpus Vielfalt bekommt. Beleg in den Lauf-Manifesten:
`add_root_noise: true`, `deterministic: false`, `sims: 200`.

**Regel daraus: Punktniveaus nie aus Self-Play-Daten als Referenz fuer echtes
Spiel nehmen.** Wer eine Skala, Schwelle oder Zielgroesse an Punkten festmacht,
nimmt die Arena-Reihe.

**Caveat zur Vergleichbarkeit:** die beiden Reihen haben verschiedene Anker (Log
= tatsaechliche Punktereignisse, Self-Play = `player.score` am letzten Record der
Runde, das innerhalb einer Runde schwankt), und die Zeilen-n der Log-Reihe
schwanken zwischen 14 und 22, weil nicht in jeder Runde eine Punktezeile je
Spieler faellt. Die Groessenordnung traegt, die zweite Stelle nicht.


## 6. Strafleiste

**Regellage** (normativ in `engine_manual.md:38`, `:110-113`, `:161-163`,
hier nur als Prämisse): 4 Slots à −1/−2/−3/−4, Startspielerstein −2,
Punktestand nie unter 0; Steine, die nicht mehr passen, fallen auf die Leiste,
und freiwilliges Ablegen ist ebenfalls erlaubt.

**Was daraus folgt und im Handbuch nicht steht:** es gibt **keine Regel, die
zwischen „abgeladen" und „übergelaufen" unterscheidet** – die beiden Kanäle
sind ökonomisch identisch (`PREREG_floor_action_aversion.md` par.2). Wer den
einen meidet und den anderen nicht, meidet die Aktion, nicht die Kosten.

**Groessenordnung** (407 identische gepaarte Partien, Block-Ebene,
`tools/probes/penalty_track_probe.py`):

| je Partie | Champion | Heuristik |
|---|---|---|
| Strafpunkte | **16,91** | **19,59** |
| abgeladene Steine (Ziel = Strafleiste) | 2,88 | 6,38 |
| Überlauf-Steine | 2,21 | 1,78 |
| Runden mit Strafe | 4,25 | 3,81 |

Bei einem Niveau von rund 47-55 eigenen Punkten frisst die Leiste damit etwa
ein Drittel des Bruttoscores. **Sie ist der groesste einzelne Abzugsposten des
Spiels** und war bis 2026-08-30 in diesem Dokument nur in Strategie-Prosa
vertreten.

**Auslastung** (600 Partien, 97.970 Entscheidungsschritte, `selfplay_v20wdlsw_*`,
CI 95 %): ein reiner Strafleisten-Zug ist TOP-Aktion in **4,40 ± 0,19**
Schritten je Partie -- davon **3,31 erzwungen** (keine legale Reihe) und nur
**1,09 freiwillig**. Eine Reihe MIT Überlauf ist TOP-Aktion in **5,51 ± 0,21**
Schritten (6,17 übergelaufene Steine je Partie). Bezogen auf die 89,08
Schritte je Partie, in denen überhaupt ein Stein-Zug angeboten wird, sind das
4,9 % bzw. 6,2 %, zusammen rund **11 % aller Stein-Entscheidungen**.

**Folge für Aktionsfilter**: ein harter Filter „Strafleisten-Ziel und Überlauf
raus" wäre nicht wirkungslos, er träfe rund 11 % der Entscheidungen. Drei
Viertel der Strafleisten-Fälle sind allerdings erzwungen und müssten ohnehin
stehen bleiben.

**Verhaltensbefund, nicht Spielstruktur**: der Champion meidet die AKTION
massiv (2,88 gegen 6,38 abgeladene Steine) und die KONSEQUENZ gar nicht
(nur 2,68 Strafpunkte weniger, bei mehr Überlauf und mehr Runden mit Strafe).

## 7. Spaltenbau: warum die Spalte bei 5 von 6 stehenbleibt

Abschnitt 1 nennt zwei Hürden für die volle Spalte. Es sind drei, und die
Messlage sagt inzwischen ziemlich genau, welche davon trägt.

### Die dritte Hürde: die Farbschranke

**Jede normale Kuppelzelle verlangt GENAU EINE Farbe** (`dome.rs`,
`required_color`), und **eine Musterreihe trägt nur EINE Farbe**
(`board.rs`, `PatternLine::color`). Eine Spalte zu schließen heißt damit:
sechs Zellen, sechs festgelegte Farben, je eine Musterreihe, deren Kapazität
r+1 Fliesen genau dieser einen Farbe verlangt. Quelle:
`PREREG_placement_side.md` par.14.

### Die 5/6-Mauer

**In 36 von 57 Partien fehlt EINE Fliese zur vollen Spalte.** Das Netz kommt
fast immer bis an den Rand und schließt nicht. Der Befund repliziert über vier
verschiedene Eingriffsmechanismen (`PREREG_provocation.md`).

### Volle Versorgung hebt die Mauer NICHT

Deckenprobe mit dem Knopf „jede Fabrik trägt alle Farben", 20 Partien je Arm:

| Arm | vertikale Plattenpunkte | Verteilung höchster Spaltenstand | volle Spalten |
|---|---:|---|---:|
| Netz, normal | 1,05 | 4→6, 5→12, 6→2 | 2/20 |
| Netz, **volle Versorgung** | 0,70 | 3→1, 4→5, **5→14** | **0/20** |

Die Verteilung verschiebt sich NICHT nach rechts, sie sammelt sich noch
stärker bei 5 von 6. Die Farbschranke war aufgehoben, jede Farbe jederzeit
draftbar. Es half nicht: **das Material war da, der Plan nicht.**

### Der Engpass sitzt nicht am Ende

Legalitäts-Sonde (`tools/probes/column_completion_legality_probe.py`,
2026-08-23): in **0 von 160** stehengelassenen Höhe-5-Fällen existierte im
Restfenster überhaupt eine legale Platzierung, die die Spalte vollendet hätte.
**Der Champion verpasst am Ende nichts** – die Entscheidung fiel früher. 128
der 160 Fälle stammen aus Netz-gegen-Netz-Partien, und die Quote ist in jeder
Gruppe 0.

Blockade-Zusammensetzung: **Musterreihe noch nicht voll 87/160 (54 %)**,
Zielfeld ist Spezialfeld 41 (26 %), keine passende Farbe verfügbar 32 (20 %).
Stehengelassene Höhe-5-Spalten je Partie: 0,55 (Symptom-Maß, kein Tor).

### Wer eine lange Reihe anfängt, bekommt sie nur halb fertig

**Vollendungsquote langer Reihen: 0,534 / 0,514** in beiden Armen einer
gepaarten Netz-gegen-Netz-Arena (407 Seeds × 2 Sitze = 814 Partien). Wer eine
Reihe mit Kapazität 5 oder 6 beginnt und sie in der Hälfte der Fälle nicht
fertigbekommt, spielt lange Reihen schlecht. Zum Vergleich: Heuristik-Lehrer
0,563, `hv2`-Hülle 0,717.

### Wann das Spiel eine Spalte zumacht

Anteil noch VOLLENDBARER Spalten-Atome je Runde (Held-out-Satz, 150
Stellungen je Runde, nur beobachtbare Information):

| Runde | 1 | 2 | 3 | 4 | 5 |
|---|---:|---:|---:|---:|---:|
| k1 Spalten-Atome | 100,0 % | 98,8 % | **85,1 %** | **55,4 %** | **47,2 %** |
| „irgendeine Spalte" | 100,0 % | 100,0 % | 100,0 % | 96,0 % | 96,0 % |

**Das Signal sitzt JE SPALTE, nicht in der Aggregation**: „irgendeine Spalte
vollendbar" bleibt selbst in Runde 5 bei 96 %, während einzelne Spalten bei
47 % liegen. Es ist eine notwendige Bedingung, also eine obere Schranke – nicht
„erreichbar bei gutem Spiel".

### Kein Versorgungs-, sondern ein Verteilungsproblem

Eine volle Spalte kostet **1+2+3+4+5+6 = 21 Zellen**, unabhängig von der
Platzierungsgeschicklichkeit. Über 5 Runden stehen beiden Spielern zusammen
**105 Fliesen-Platzierungen** zur Verfügung.

| | verbrauchte Zellen | trüge bei Gleichverteilung | erreicht |
|---|---:|---:|---:|
| Mensch | 60,9 | 2,90 Spalten | **1,80** |
| Netz | 42,7 | **2,03 Spalten** | **0,10** |

**Mit den Fliesen, die es heute schon nimmt, wären rund zwei volle Spalten
drin – es holt 0,1. Keine einzige zusätzliche Fliese nötig.** Gegenprobe des
Modells: 60,9 + 42,7 = 103,6 der 105 verfügbaren Platzierungen (98,7 %), zwei
unabhängige Wege zu derselben Zahl.

Daraus die Ziel-Kennzahl: **das MINIMUM der Abschlüsse über die sechs Reihen**,
nicht deren Summe und nicht die Länge. Jede Vollendung über dem Minimum ist aus
Spaltensicht Überschuss – **das Zielprofil ist FLACHER, nicht länger.**

## 8. Struktur und Information

### Mosaic ist ein Spiel mit PERFEKTER Information und Zufallsknoten

**Es gibt keine private Information.** Alle Spielerfelder im Zustand sind
öffentlich (`dome_grid`, `pattern_lines`, `floor`, `bonus_chips`,
`unused_chip_colors`, `score`), und das Verdeckte steht als **aggregierte
Zähler** (`bag_colors`, `bag_count`, `tower_colors`, `dome_pool_mask`,
`dome_wild_remaining_frac`) – symmetrisch für beide Spieler.

**Folge: Backgammon, nicht Poker.** Determinisierung und ISMCTS sind Techniken
für Informationsmengen, also für privates Wissen. Wer sie hier misst, misst
Werkzeug aus der falschen Familie – drei Messungen sind daran gescheitert.
Quelle: `PREREG_chance_nodes.md`, „Die strukturelle Grundlage".

**Auch der Kuppelplatten-Pool ist ableitbar.** Prämisse aus dem Handbuch
(`engine_manual.md:44-48`): 18 Platten, 9 mit Spezialfeld und 9 mit Wildfeld,
3 offen in der Auslage, der Rest im verdeckten Stapel. Daraus folgt: es ist
ein offener Satz mit je einem Exemplar (`dome.rs:198-226`), also kennt den
Rest durch Subtraktion, wer Auslage und Bretter sieht. `dome_pool_mask` ist
abgeleitetes öffentliches Wissen, kein Orakel.

### Der Kuppelstapel ist bis Runde 4 abgetragen

| Runde | 1 | 2 | 3 | 4 | 5 |
|---|---:|---:|---:|---:|---:|
| Median Rest | 13,0 | 8,0 | 4,0 | **0,0** | 0,0 |
| Anteil ≤ 3 | 0 % | 0 % | 12,5 % | 100 % | 100 % |

Alles, was in Runde 1-3 nach unten wandert, wird also noch gezogen – eine
zurückgelegte Platte ist nicht aus dem Spiel. Zugleich heißt es: **ab Runde 4
ist die Kuppelgeometrie festgelegt**, die Formbarkeit endet dort.

### Die Machbarkeitshülle ist ein Dreieck

Erlaubt ist `r + c <= 5`, also 6+5+4+3+2+1 = **21 Zellen** – dieselbe 21, die
eine volle Spalte kostet (Abschnitt 7). Die Dreiecksform ist damit keine
ästhetische Wahl. Gespiegelt wird nur um die Spalten-Achse; die unteren
Orientierungen verlangten eine volle Rasterzeile 5, und die ist strukturell
unerreichbar – siehe gleich.

### Eine volle Rasterzeile ist ohne Spezialfliese unmöglich

Rasterzeile *r* wird **nur** von Musterreihe *r* gespeist, und die schließt
höchstens einmal je Runde ab: **fünf Steine für sechs Zellen.** Spalten haben
das Problem nicht, sie ziehen ihre sechs Zellen aus sechs verschiedenen
Musterreihen.

Das ist der eigentliche Grund, warum Kriterium 0 (horizontale Reihen, +3)
praktisch nie angesteuert wird – schärfer als die Ökonomie-Begründung in
Spielstrategie 7. Der Ausweg existiert: ein ausgelöstes Spezialfeld FÜLLT die
Rasterzelle, also braucht eine Rasterreihe mit zwei Spezialfeldern nur noch
vier Lieferungen.

### Wildfelder je Brett: 2 bis 7, nicht konstant

Nachgemessen an 120 Brettern:

| Slots mit Wild-Feld | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---:|---:|---:|---:|---:|---:|
| Bretter | 3 | 14 | 43 | 43 | 14 | 3 |

Symmetrisch um 4,5; die gelegentlich zitierten „exakt 50 %" sind ein
Symmetrieartefakt der Mittelung, kein Konstantwert. **Wild-Slots und
Wild-FELDER stimmen 1:1 überein.** Für k3 heißt das: typisch 4-5 Felder, also
8-10 Punkte – aber alle müssen belegt sein, und die Anzahl hängt an der
eigenen Plattenwahl, ist also gestaltbar.

## 9. Der Mensch als Referenz

Zehn Mensch-gegen-Netz-Partien aus `static/log/` sind die einzige
unkontaminierte empirische Quelle im Repo – ein plattenbewusster Spieler gegen
ein plattenblindes Netz, gepaart je Partie (beide spielen dieselbe), also ohne
Ära- oder Seed-Versatz. **Vorbehalt durchgehend: n=10, ein Spieler, schwacher
Gegner. Als Größenordnung belastbar, als Konstante nicht.**

### Abschlüsse je Musterreihe

| | R1 | R2 | R3 | R4 | R5 | R6 | volle Spalten |
|---|---:|---:|---:|---:|---:|---:|---:|
| Mensch | 4,00 | 4,10 | 3,40 | 3,20 | **2,50** | **2,20** | **1,80** |
| Netz | 4,90 | 4,90 | 3,30 | 2,40 | 1,10 | 0,50 | 0,10 |
| Delta | −0,90 | −0,80 | +0,10 | +0,80 | **+1,40** | **+1,70** | **+1,70** |

**Der Mensch gibt oben ab und kauft unten das Vielfache.** Das ist die direkte
Gegenmessung zur Durchsatztabelle in Abschnitt 1 – und der Referenzpunkt, der
dort neben DECKE, BODEN und IST fehlte.

### Platzierungen je Rasterreihe

| Rasterreihe | Mensch | Netz (v21@400) | v20-Selbstspiel | Mensch / v20 |
|---|---:|---:|---:|---:|
| 1 | 3,60 | 4,70 | 4,80 | 0,75x |
| 2 | 3,30 | 4,70 | 4,77 | 0,69x |
| 3 | 3,20 | 3,30 | 2,84 | 1,13x |
| 4 | 2,60 | 2,30 | 1,89 | 1,38x |
| 5 | **2,30** | 1,10 | 0,84 | **2,74x** |
| 6 | **1,70** | 0,50 | 0,58 | **2,93x** |
| Summe | 16,70 | 16,60 | – | |

**Die Summe ist praktisch gleich, die Verteilung nicht.** Rund ein Viertel
weniger in Reihe 1-2, dafür das Zwei- bis Dreifache in Reihe 5-6. Zusammen mit
Abschnitt 7 ist das der Beleg, dass es ein Verteilungs- und kein
Mengenproblem ist.

Dazu der gemessene **Realisierungsabschlag je Rasterreihe**: 0,72 / 0,66 /
0,64 / 0,52 / 0,46 / 0,34 – wie stark eine geplante Zelle in dieser Reihe
tatsächlich zustande kommt.

### Woher der Vorsprung kommt – und woher nicht

**Die Platzierungspunkte sind ein Gleichstand: 54,9 gegen 55,8.** Der
Vorsprung sitzt vollständig bei den Spezialfliesen (2,70 gegen 0,50
Freischaltungen je Partie, 8,50 gegen 0,90 Punkte) und bei den Spalten
(1,80 gegen 0,10).

Ergänzend gegen den v20-Champion (`watchlist_v20_interim_review.md`, siehe
Abschnitt 5): Ø +14,5 Punkte, davon 9,0 aus den Spezialpunkten.

### Der Rundenverlauf ist stärke-invariant

An 22 Arena-Logs: nach Runde 1 stehen 4 Punkte auf dem Brett, nach Runde 5
47,6, nach Endwertung 55,7 (Mensch: 7,0 / 59,2 / 74,4). **Die Niveaus liegen
33 % auseinander, die Anteile am Endstand stimmen auf 0,02 überein**
(0,083 · 0,172 · 0,327 · 0,515 · 0,825).

Der VERLAUF ist damit Spielstruktur, nicht Spielstärke – ein festes
Rundenprofil ist zulässig, ein festes Punkt-NIVEAU nicht.

## Spielstrategie aus Nutzer-Praxis (2026-08-13, woertlich aufgenommen)

Diese Punkte stammen aus der Spielerfahrung des Nutzers und haben in der
Plattenbauer-Entwicklung jeweils direkt eine Konstruktionsaenderung ausgeloest --
sie sind Domaenenwissen, kein Messergebnis.

### 1. Die Kuppel ist formbar -- Forderungen entstehen, sie bestehen nicht

*"das spielfeld/kuppel laesst sich mehr oder weniger frei an die eigenen
anforderungen anpassen."* Solange ein Slot keine Platte traegt, fordert seine
Zelle nichts (`geforderte_farbe = None`). Die Farbforderungen sind eine
ENTSCHEIDUNG (Kachelwahl + Rotation), keine Vorgabe. Folge fuer jede Strategie:
nicht Farben jagen, die eine frueh festgelegte Platte fordert, sondern
**Material zuerst sichern und die Forderungen hinterher passend waehlen**.

### 2. Die Reihenfolge des Menschen: unten anfangen, Kuppel spaeter

*"ich nehm ueberpraesente farben aus der fabrik und platziere sie in den unteren
reihen. erst dann waehl ich die passende kuppel aus."* Untere Musterreihen
brauchen 4-6 Kopien und die laengste Anlaufzeit -- dort zaehlt Ueberfluss am
meisten, und die Kuppelwahl bleibt flexibel, bis das Material liegt.

### 3. Die einzige echte Unbekannte ist die Fabrik-Befuellung

*"die einzige wirklich unbekannte ist welche farben auf die fabrik kommen mit
jeder runde. dann heisst es plan anpassen/optimieren, schadensbegrenzung
betreiben und den gegner stoeren."* Seit dem RNG-Schnitt (2026-08-13) ist diese
Unbekannte auch technisch der einzige Zufallsstrom des Spiels.

Die Dreiheit, mit Belegstand:
- **Plan anpassen**: Vollendbarkeits-Buchhaltung + Zielwechsel (Plattenbauer
  Runde 4). Eine Spalte ist laut Nutzer *"praktisch immer erreichbar wenn
  vernuenftig darauf hingespielt wird"* -- festhalten an einem toten Ziel ist ein
  Planungsfehler, kein Naturgesetz.
- **Schadensbegrenzung**: der am besten belegte Pfeiler -- der Strafleisten-Term
  war der einzige Eingriff der Injektions-Messreihe mit signifikant positivem
  Effekt; die Beschneidungs-Provokation scheiterte exakt daran, dass sie
  Schadensbegrenzung verbot.
- **Gegner stoeren**: der schwaechste Pfeiler; der einzige gemessene Versuch
  (λ-Denial) replizierte nicht. Siehe naechster Abschnitt.

### 4. BAUSTEIN (Nutzer-Auftrag): Gegner-Stoerung ueber die Farbzaehlung

Dieselbe oeffentliche Zaehlung (`verbleibende_farben`), die die eigene
Vollendbarkeit prueft, verraet auch, welche knappe Farbe der GEGNER fuer seine
Struktur braucht: seine Musterreihen-Farben und Kuppelplatten-Forderungen sind
sichtbar. Ein Bauer, der bei ~gleichwertigen eigenen Zuegen die Fliese nimmt,
die dem Gegner ausgeht, stoert aus reiner Buchhaltung -- kein Kopf, keine
Vorhersage. **Eingeplant als Plattenbauer-Baustein NACH Runde 4** (erst die
eigene Vollendung, dann die Stoerung; beides nutzt dieselbe Zaehlung).
Messgroesse dann: Gegner-Plattenpunkte und Gegner-Endstand gepaart, nicht nur
die eigenen -- die λ-Lehre (Vorzeichenwechsel zwischen Laeufen) mahnt zur
Replikation auf frischen Seeds, bevor daraus ein Befund wird.


### 5. Diagonalen-Taktik (Nutzer 2026-08-13; Koordinaten 1-basiert [Zeile,Spalte], Code 0-basiert)

Fuer die Gegendiagonale [6,1]-[5,2]-[4,3]-[3,4]-[2,5]-[1,6] (Code: (5,0)...(0,5)):

- **Unteres Ende ueber die Spezialplatte in Slotreihe 3**: [5,2] und [6,1] muss
  man fuer die Diagonale ohnehin legen -- damit sind zwei der drei Nachbarzellen
  des Slots (5,0..6,1) schon gefuellt, und das Spezialfeld auf **[6,2] loest
  praktisch von selbst aus und bringt beim Abschluss 6 Bonuspunkte** (Kuppelbonus
  = Rasterreihe, hier 6). Nur [5,1] kommt als Zusatzaufwand dazu.
- **Mittelzellen [4,3]/[3,4]**: Joker- wie Spezialplatte liegen dort sauber;
  Nutzer-Tendenz **Jokerplatte** -- dann ist die Farbe frei waehlbar
  (Formbarkeits-Prinzip aus Abschnitt 1).
- **Oberes Ende [2,5]/[1,6]**: normalerweise einfach zu bedienen. Ist die
  ECKPLATTEN-Wertungskarte aktiv, gern die Spezialfliese hinzunehmen.
- Gilt spiegelbildlich fuer die Hauptdiagonale mit entsprechenden Indizes.

Messbezug: der Diagonal-Bauer (k2) erreichte 2,61 bei signifikantem
Sieg-Verlust (p=0,039, §13) -- diese Taktik ist der designierte Inhalt seiner
Runde 2: Spezial-/Joker-Slots als Diagonalzellen WAEHLEN statt Farben jagen.

### 6. Eckplatten-Taktik (Nutzer 2026-08-13)

*"beim vorhandensein der eckplatten wertungskarte wirklich nur spezialkuppeln in
die ecken legen. schneller fertig und bonuspunkt fuer die spezialfliesen,
insbesondere in kuppelslot [3,1] oder [3,3]."*

Logik: Spezialzellen fuellen sich per Trigger ohne Fliesenlieferung -- eine Ecke
mit Spezialplatte ist schneller komplett, und der Trigger zahlt den
reihenabhaengigen Kuppelbonus obendrauf. Die unteren Eck-Slots [3,1]/[3,3]
(Code slot (2,0)/(2,2)) sind die wertvollen: ihre Eckplatten zahlen je 8 Punkte
(gegen 3 oben), und ihre Spezialtrigger liegen in den hohen Rasterreihen 5-6
(Bonus 5-6). Messbezug: der Ecken-Bauer (k5) hatte in §13 das beste
Kosten-Nutzen-Verhaeltnis (4,73, Orakel 11) -- diese Taktik ist seine Runde 2.


### 7. Welche Platten das Hinspielen wert sind (Nutzer-Oekonomie 2026-08-13)

*"farbenreiche reihen (>= 5 farben) sind meiner meinung den aufwand nicht wert.
auch die horizontalen reihen find ich von den bonuspunkten sehr gering. aber das
ist ein spielarchitektur problem."*

Die Messung (§13 der Provokations-Prereg) bestaetigt beides unabhaengig:
- **k7 Farbenreiche Reihen** (4 Pkt): Bauer brachte +0,52 Punkte bei
  Sieg-Einbruch 17/23 -> 7/23 -- Stopp-Regel ausgeloest, deaktiviert.
- **k0 Horizontale Reihen** (3 Pkt): Bauer lag mit -0,39 UNTER dem Bezug --
  das Normalspiel holt die Reihe fast im Vorbeigehen (Bezug 1,04), gezieltes
  Hinspielen kostet mehr als der Bonus wert ist.

**Konsequenz fuer die Bauer-Familie**: k0 und k7 bleiben OHNE eigenen Bauer --
nicht als Fehlschlag, sondern als Spieloekonomie-Entscheid. Ihr Beitrag zum
Korpus (Label-Ereignisse fuer den Ownership-Kopf) kommt beilaeufig aus dem
Normalspiel und den anderen Bauern (Zeilen fuellen sich als Nebenprodukt von
Spalten-/Diagonal-/Eckenbau); ob die beilaeufige Rate reicht, prueft das
Korpus-Gate im Piloten (Grundraten je Konjunktionsziel).

Der Nutzer ordnet die niedrigen Boni als **Spielarchitektur-Problem** ein --
also eine Eigenschaft des Spiels, nicht der KI. Fuer die KI heisst das nur:
diese Platten VERTEIDIGEN (Punkte mitnehmen, wenn sie anfallen), nie ANSTEUERN.


### 8. Spezialfelder-Wertungsplatte: eine KUPPELDRAFT-Strategie (Nutzer 2026-08-13)

*"einerseits viele jokerkuppeln nehmen (und auf die unteren slots legen) und wenn
eine spezialkuppel dennoch platziert werden muss, dann die unteren slots
vermeiden. dann normaler spielaufbau um die strafpunkte auszugleichen. aber wenn
die nahme der kuppelplatten priorisiert wird dann gibt es mehr strafpunkte beim
gegner."*

**GELTUNGSBEREICH (ergaenzt 2026-08-30, Nutzer-Bestaetigung): die drei Hebel
gelten, WENN die Spezialfelder-Wertungsplatte (Kriterium 6) im Spiel ist.**
Ohne sie kostet ein offenes Spezialfeld nichts, und die Rechnung dreht sich --
siehe die Anmerkung an Hebel 2. Die Platte liegt nicht in jeder Partie: aus
4 Ausschlusspaaren kommen 3 von 8 Platten ins Spiel.

Kriterium 6 (-3 je offenem Spezialfeld) wird also nicht ueber Fliesen gespielt,
sondern ueber die KUPPELWAHL -- drei Hebel:

1. **Joker horten, nach unten legen**: Jokerkuppeln tragen keine Spezialfelder,
   erzeugen also keine -3-Risiken -- und auf den unteren Slots ersetzen sie
   genau die Plaetze, wo ein Spezialfeld am teuersten waere.
2. **Erzwungene Spezialkuppeln nach OBEN**: der Trigger braucht die drei
   Nachbarzellen des Slots, und obere Slots haengen an den billigen Musterreihen
   (1-2 Kopien) -- oben schliesst ein Spezialfeld fast von selbst, unten (Reihen
   5-6, 5-6 Kopien) bleibt es offen und kostet.
   **Nur unter Kriterium 6.** Nutzer-Korrektur 2026-08-25
   (`PREREG_special_tile_yield.md` par.4a): *"die regel ist falsch"* /
   *"ohne der spezialkuppel dort unten werden zwei spalten eher schwer"*. Ohne
   k6 ist das Spezialfeld eine GRATISZELLE -- es entriegelt und fuellt sich in
   derselben Aktion, sobald die drei Nachbarzellen stehen (round_end.rs:275/316),
   ohne eigenen Zug und ohne Stein. In der unteren Slot-Reihe, wo die anderen
   drei Zellen an den Musterreihen 5/6 haengen, ist es damit die BILLIGSTE der
   sechs Zellen einer Spalte; wer die Platte dort vermeidet, macht die beiden
   Spalten durch diesen Slot schwerer.
3. **Kuppeldraft als Stoerung**: wer die Jokerkuppeln priorisiert wegnimmt,
   laesst dem Gegner die spezial-lastigen Platten -- dessen offene Spezialfelder
   werden zu SEINEN Strafpunkten. Zweiter Stoerkanal neben der Farbzaehlung
   (Abschnitt 4), und er braucht nur Platten-Zaehlung, keine Farb-Buchhaltung.

Dazu normaler Spielaufbau als Ausgleich der verbleibenden Strafpunkte --
Kriterium 6 ist Schadensbegrenzung plus Draft-Kontrolle, kein Aufbauziel.

Messbezug: k6-Bauer stand in §13 bei -10,65 gegen Bezug -11,85 (+1,20) -- diese
Strategie ist seine Runde 2, und sie ist die erste, die primaer im KUPPELDRAFT
lebt statt im Fliesendraft.
