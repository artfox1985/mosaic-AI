# Domänenwissen Mosaic — abgeleitete und gemessene Größen

**Abgrenzung.** `engine_manual.md` gibt die **Regeln** normativ wieder. Dieses
Dokument enthält, was aus ihnen **folgt** und was im Korpus **gemessen** ist.
Die Trennung ist Absicht: sonst liest irgendwann jemand eine Messung als Regel.

**Warum es diese Datei gibt** (angelegt 2026-08-11, Nutzer-Frage *"wo hast das
domänenwissen bisher gespeichert?"*): es war verstreut — Versorgungsrechnung als
Docstring in `tools/musterreihen_verfuegbarkeit.py`, Strategie-Herleitung in
`evaluations/PREREG_plattenkopf.md`, Plattenanteil in `evaluations/STATUS.md`.
Letzteres ist der eigentliche Fehler: STATUS trägt laut eigenem Kopf „nur
AKTUELLES und OFFENES" und wird regelmäßig in `archive/history.md` geleert —
Domänenwissen dort wird also mitarchiviert. Vorregistrierungen sind je
Experiment, ein Tool-Docstring hängt an seinem Tool.

---

## 1. Musterreihen-Durchsatz: was tatsächlich auf der Kuppel landet

**Gemessen** mit `tools/musterreihen_durchsatz.py`, 60 Dateien = **600 Partien**
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
   Beides zusammen erklärt die gemessene Spaltenrate von 0,4–1,2 %.

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
  Brett**; `evaluations/watchlist_v20_zwischenlese.md` zählte für die KI 17,2
  Kuppel-Legungen je Partie. Die Differenz zeigt in die Richtung des
  Unterschätzungs-Vorbehalts.

### Die drei Referenzpunkte

| Punkt | Quelle | Was er sagt |
|---|---|---|
| **DECKE** | `tools/musterreihen_verfuegbarkeit.py` | wie oft *r* gleichfarbige Steine überhaupt verfügbar sind — policy-unabhängig, reine Versorgung |
| **BODEN** | Zufalls-Drafting | was ohne Absicht passiert |
| **IST** | `tools/musterreihen_durchsatz.py` (dieser Abschnitt) | was der Champion-Korpus tatsächlich schafft |

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

## 5. Weitere gemessene Struktur

- **Slot-Gradient der Spezialfelder**: in der unteren Slot-Reihe bleibt das
  Spezialfeld in ~84 % der Partien leer, in der oberen in ~13 % — monoton, und
  über zwei Generator-Ären deckungsgleich, also **Spielstruktur statt
  Champion-Verhalten**. Zusammen mit Abschnitt 2 heißt das: die KI lässt die
  **teuersten** Spezialfelder liegen (untere Reihe = 5–6 Punkte).
  Nutzer-Taktik „keine Spezialkuppeln in Slot-Reihe 3" ist deshalb eine
  ERWARTUNGSWERT-Aussage: hoher Wert, aber von den langsamsten Musterreihen
  gefüttert.
- **Startkuppel-Platzierung ist deterministisch** (`self_play.rs::choose_start_placement`):
  der Farb-Score ist positions- und rotationsunabhängig, der Eckbonus für alle
  vier Ecken identisch → immer Ecke (0,0), immer 0°. Position und Rotation sind
  tote Freiheitsgrade; nur die Platten-WAHL variiert.
- **Mensch gegen Champion** (10 gewertete Partien, `watchlist_v20_zwischenlese.md`):
  Mensch 7:3, Ø +14,5 Punkte. Größter Einzelposten sind die Spezialpunkte —
  **10,3 gegen 1,3 je Partie**, also 9,0 der 14,5 Punkte Differenz. Die KI
  schaltet in **6 von 10** Partien kein einziges Spezialfeld frei, der Mensch in
  9 von 10 schon in Runde 2.
