# Mosaic — Spielanleitung (abgeleitet aus der Engine)

> **Zweck dieses Dokuments:** Diese Anleitung beschreibt die Spielregeln **so, wie sie
> im Code (`engine/`) tatsächlich implementiert sind**. Sie ist als Grundlage für einen
> Quervergleich mit der offiziellen Spielanleitung gedacht. Abweichungen zwischen diesem
> Dokument und der echten Anleitung deuten auf mögliche Implementierungsfehler hin.
>
> Jeder Abschnitt nennt in Klammern die Code-Quelle, damit du gezielt prüfen kannst.

---

## 1. Überblick & Spielziel

Mosaic ist ein abstraktes Legespiel für **2 Spieler** *(engine geht durchgängig von genau 2 Spielern aus, `players: list[PlayerBoard] # immer 2 Spieler`)*. Über **5 Runden** *(`NUM_ROUNDS = 5`)* sammeln die Spieler Fliesen, legen sie auf Musterreihen und übertragen sie von dort auf ihre **Kuppel** (ein Plattenraster). Punkte gibt es beim Legen auf die Kuppel sowie in einer Endwertung über **Wertungsplatten**. Wer am Ende die meisten Punkte hat, gewinnt.

---

## 2. Material

### Fliesen (Steine)
- **5 normale Farben:** blau, gelb, rot, schwarz, türkis *(`TileColor`, `NORMAL_COLORS`)*
- **13 Fliesen pro Farbe** *(`TILES_PER_COLOR = 13`)* → **65 normale Fliesen** insgesamt *(`NORMAL_TILES = 65`)*
- Dazu eine separate Reserve an **Spezialfliesen** *(`special_supply`, `place_special_tile`)*

### Beutel & Turm
- Alle 65 normalen Fliesen starten im **Beutel** (`Bag`), gemischt.
- Verbrauchte/abgeräumte Fliesen wandern in den **Turm** (`Tower`).
- Läuft der Beutel beim Ziehen leer, wird er aus dem Turm nachgefüllt *(`_draw_with_refill`, `refill_from_tower`)*.

### Fabriken
- **4 kleine Fabriken** *(`NUM_SMALL_FACTORIES = 4`)*, jede zu Rundenbeginn mit **4 Fliesen** auf der Sonnenseite *(`TILES_PER_SMALL_FACTORY = 4`)*.
- **1 große Fabrik / Tischmitte** (`LargeFactory`) mit **5 Fliesen** zu Rundenbeginn *(`TILES_PER_LARGE_FACTORY = 5`)*.

### Spielerbrett (je Spieler)
- **6 Musterreihen** mit Kapazität 1 bis 6 *(`PatternLine`, row 0 hat Kapazität 1, row 5 hat Kapazität 6)*.
- Eine **Strafleiste** (Boden) mit 4 Slots: **−1 / −2 / −3 / −4** *(`BROKEN_PENALTIES = [-1, -2, -3, -4]`)*.
- Eine **Kuppel**: ein 3×3-Raster von **Kuppelplatten** *(`DomeGrid`, `dome_slots: 3×3`)*, jede Platte mit 4 Feldern (2×2). Das ergibt das **6×6-Wertungsraster** *(Koordinaten `row6 = slot_row*2 + ...`)*.
- **9 Kuppelplatten pro Spieler** *(`DOME_TILES_EACH = 9`)*.

### Bonusplättchen (Chips)
- Pro Runde werden **2 Bonusplättchen** verfügbar *(`BONUS_CHIPS_PER_ROUND = 2`)*, aufgedeckt sobald eine Fabrik leer ist *(„Bonusplättchen aufgedeckt!")*.

---

## 3. Spielaufbau (Runde 1)

Zu Beginn jeder Runde:
1. Jede kleine Fabrik wird mit 4 Fliesen aus dem Beutel gefüllt *(`_fill_small_factory`)*.
2. Die große Fabrik wird mit 5 Fliesen gefüllt *(`_fill_large_factory`)*. **Sonderregel:** Sind alle 5 dieselbe Farbe, gehen sie zurück und es wird neu gezogen, bis mindestens 2 Farben dabei sind.
3. **Startkuppel (nur Runde 1):** Jeder Spieler legt zu Beginn eine **Startkachel** auf seine Kuppel *(`start_dome_tile`, „Startkachel … → (slot) rot=…°")*. Diese Platzierung zählt als **einer der 2 Plättchen-Züge** der Runde *(„Startkachel (Runde 1) zählt als einer der 2 Züge")*.

> **Quervergleich-Hinweis:** Prüfe die genaue Reihenfolge, wer die Startkachel zuerst legt
> (Engine: Nicht-Startspieler legt zuerst), und ob die Startkachel-Drehung/Position frei wählbar ist.

---

## 4. Rundenablauf

Jede Runde besteht aus zwei Phasen: **Drafting** (Fliesen nehmen) und **Tiling** (auf die Kuppel legen).

### 4.1 Drafting-Phase

Spieler wechseln sich ab. Es gibt zwei Arten von Zügen:

**A) Kuppelplatten legen (Plättchen-Zug)**
- Jeder Spieler legt pro Runde **2 Kuppelplatten** *(`DOME_TILES_PER_ROUND = 2`, `TOKENS_PER_ROUND = 2`)*.
- In Runde 1 zählt die Startkachel als eine davon.

**B) Fliesen nehmen — Sonnenseite (Sun)**
- Man nimmt **alle Fliesen einer Farbe** von der Sonnenseite einer Fabrik.
- Die genommenen Fliesen kommen auf **genau eine Musterreihe** (0–5) *(`moves.py`)*.
- Die **übrigen** Fliesen der Fabrik werden auf die **Mondseite** gelegt:
  - Kleine Fabrik: übrige Steine bilden den **Mond-Stapel** derselben Fabrik *(„F2 Mond-Stapel: …")*.
  - Große Fabrik: übrige Steine landen im **Moon-Pool** der großen Fabrik *(„GF Moon-Pool: …")*.

**C) Fliesen nehmen — Mondseite (Moon)**
- Man kann Fliesen von der Mondseite/dem Moon-Pool nehmen, wenn die gewünschte Farbe **oben** auf mindestens einem Stapel liegt *(`_validate_small_moon`)*.

**Platzierung & Überlauf**
- Passt eine Fliese nicht in die gewählte Reihe (Reihe voll oder Farbe passt nicht zur bereits liegenden Farbe), wandert der **Überschuss auf die Strafleiste** *(`moves.py`)*.
- Ist die Strafleiste (4 Slots) voll, gehen weitere Steine direkt in den **Turm** *(„Stein(e) → Turm (Strafleiste voll)")*.
- Man darf Fliesen auch **direkt auf die Strafleiste** legen *(row_index = -1)*.

**Startspielerstein**
- Wer ihn nimmt, beginnt die nächste Runde, erhält aber am Rundenende **−2 Punkte** *(`first_player_marker_penalty = -2`, „Startspielerstein genommen (−2 Pkt am Rundenende)")*.

**Bonusplättchen**
- Sobald eine Fabrik leer ist, wird ihr Bonusplättchen aufgedeckt.
- Spieler können pro Runde bis zu **2 Bonusplättchen** nehmen *(`BONUS_CHIPS_PER_ROUND = 2`)*.

### 4.2 Tiling-Phase

Am Rundenende werden vollständige Musterreihen auf die Kuppel übertragen.

- Das Tiling läuft **von oben nach unten** (Reihe 1 → 6). Sobald eine spätere Reihe gelegt wurde, sind frühere Reihen **gesperrt** *(`tiled_max_row`, Reihenfolge-Regel in `serializer`/`agent_env`/`server`)*.
- Von einer abgeschlossenen Musterreihe wird **1 Stein auf die Kuppel** gelegt; die übrigen Steine der Reihe gehen in den **Turm** *(`execute_tiling_action`: `row.tiles = []`)*.
- **Unplatzierbare Reihen** (vollständig, aber kein passendes Kuppelfeld frei) werden geräumt; ihre Steine gehen über die Strafleiste in den Turm *(„Reihe X unplatzierbar → N Fliesen auf Straffeld")*.

**Punkte beim Legen auf die Kuppel** *(`score_placed_tile`)*
- Ein **alleinstehender** Stein (keine orthogonalen Nachbarn): **1 Punkt**.
- Ist der Stein Teil einer horizontalen und/oder vertikalen Linie verbundener Steine, zählt er **die Länge der Linie(n)**:
  - horizontale Linie der Länge *h* (>1): **+h Punkte**
  - vertikale Linie der Länge *v* (>1): **+v Punkte**
  - beides möglich → Summe *(„+5 Pkt … 3 horizontal + 2 vertikal")*.

**Bonusplättchen beim Tiling (Chips)** *(`can_complete_row_with_chips`)*
- Mit Bonusplättchen kann eine **unvollständige** Musterreihe komplettiert werden.
- Regel pro fehlendem Feld: **2 Chips derselben Farbe** ODER **3 Chips beliebiger Farbe** *(`len(same_color) >= missing*2` bzw. `len(unused) >= missing*3`; Misch-Auflösung pro fehlendem Feld)*.
- Auch hier gilt die Top-down-Reihenfolge: gesperrte (frühere) Reihen können nicht mehr per Chip abgeschlossen werden.

### 4.3 Rundenende-Strafen

- **Strafleiste:** −1 / −2 / −3 / −4 je belegtem Slot *(`broken_penalty`)*.
- **Startspielerstein:** zusätzlich −2 *(`first_player_marker_penalty`)*.
- Der Punktestand fällt **nicht unter 0** *(im Log: „Strafe −12 Pkt → 0 Gesamt")*.

---

## 5. Spezialfliesen & Spezialfelder

- Manche Kuppelplattenfelder sind **Spezialfelder**, die zunächst **gesperrt** sind (`is_locked`).
- Durch das Platzieren auf der Kuppel können Spezialfelder **freigeschaltet** werden *(`try_unlock_special`, „[Special freigeschaltet!]")*.
- Auf freigeschaltete Spezialfelder kann eine **Spezialfliese** aus der separaten Reserve gelegt werden *(`place_special_tile`, `accepts_special`)*.

> **Quervergleich-Hinweis:** Die genaue Bedingung zum Freischalten und das Timing der
> Spezialfliesen-Platzierung lohnen einen sorgfältigen Abgleich mit der echten Anleitung.

---

## 6. Endwertung — Wertungsplatten

Am Spielende *(nach Runde 5)* werden **3 von 8 möglichen Wertungsplatten** gewertet *(`ALL_SCORING_TILES`, Auswahl von 3)*. Die Wertungsplatten gehören zu **4 sich gegenseitig ausschließenden Paaren** — aus jedem Paar darf höchstens eine gewählt werden *(`MUTUALLY_EXCLUSIVE_PAIRS`)*.

### Die 8 Wertungsplatten

| # | Name | Wertung |
|---|------|---------|
| 0 | ↔️ Horizontale Reihen | **3 Pkt** je vollständige horizontale Reihe (6 Fliesen) |
| 1 | ↕️ Vertikale Reihen | **7 Pkt** je vollständige vertikale Reihe (6 Fliesen) |
| 2 | ↗️ Diagonale Reihen | **10 Pkt** je vollständige Diagonale (6 Fliesen, max. 2 möglich) |
| 3 | 🌈 Mehrfarbige Felder | **2 Pkt** je Wildcard-Feld, wenn **alle** belegt sind |
| 4 | ⬜ Äußere Felder | **1 Pkt** je Fliese am **Rand** der Kuppel (Zeile 0, Zeile 5, Spalte 0, Spalte 5) |
| 5 | 🔲 Eckplatten | **3 Pkt** je vollständige **obere** Eckplatte, **8 Pkt** je vollständige **untere** Eckplatte (alle 4 Felder belegt) |
| 6 | ⭐ Spezialfelder | **−3 Pkt** je **leeres** Spezialfliesenfeld |
| 7 | 🎨 Farbenreiche Reihen | **4 Pkt** je horizontale Reihe mit **≥ 5 verschiedenen Farben** |

### Die 4 Ausschlusspaare *(`MUTUALLY_EXCLUSIVE_PAIRS`)*
- ↔️ Horizontale Reihen ⟷ 🎨 Farbenreiche Reihen *(0 ⟷ 7)*
- ⭐ Spezialfelder ⟷ 🌈 Mehrfarbige Felder *(6 ⟷ 3)*
- ⬜ Äußere Felder ⟷ ↕️ Vertikale Reihen *(4 ⟷ 1)*
- ↗️ Diagonale Reihen ⟷ 🔲 Eckplatten *(2 ⟷ 5)*

---

## 7. Spielende & Sieger

- Das Spiel endet nach **Runde 5** *(`round_number >= NUM_ROUNDS`)*.
- Zu den über die Runden erspielten Punkten kommt die Endwertung der 3 Wertungsplatten hinzu.
- Der Spieler mit der höheren Gesamtpunktzahl gewinnt.

> **Sonderregel Runde 5:** Die Engine deutet an, dass in Runde 5 die Begrenzung auf 2
> Plättchen-Züge entfällt *(`TOKENS_PER_ROUND = 2 # Außer Runde 5`)*. Dies unbedingt
> gegen die echte Anleitung prüfen — der genaue Mechanismus ist im Kommentar nur angedeutet.

---

## 8. Punkte-Schnellübersicht

**Während des Spiels (Tiling):**
- Alleinstehender Stein: 1 Pkt
- Stein in Linie: Länge der horizontalen + vertikalen Linie

**Strafen (Rundenende):**
- Strafleiste: −1/−2/−3/−4 pro Slot
- Startspielerstein: −2
- (Punktestand minimal 0)

**Endwertung:** 3 gewählte Wertungsplatten (siehe Tabelle, beachte Ausschlusspaare)

---

## 9. Punkte zum besonders sorgfältigen Quervergleich

Diese Aspekte sind aus dem Code nicht vollständig eindeutig und sollten gegen die
offizielle Anleitung geprüft werden:

1. **Startkuppel-Reihenfolge** — wer legt zuerst, ist die Position/Drehung frei?
2. **Runde-5-Sonderregel** — entfällt wirklich die 2-Plättchen-Grenze, und wie genau?
3. **Spezialfliesen** — exakte Freischalt-Bedingung und Platzierungs-Timing.
4. **Mond-Mechanik** — Detailregeln, welche Farben wann von der Mondseite genommen werden dürfen.
5. **Diagonale Wertung** — die Engine erlaubt „max. 2" Diagonalen; prüfe welche 2.
6. **Bonusplättchen-Regel** — „2 gleich / 3 beliebig pro fehlendem Feld" gegen die echte Regel abgleichen.
7. **Anzahl Spieler** — die Engine ist fest auf 2 Spieler ausgelegt; unterstützt das echte Spiel mehr?
