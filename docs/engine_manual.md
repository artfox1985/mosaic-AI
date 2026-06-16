# 🎲 Mosaic — Offizielle Spielanleitung

Diese Anleitung beschreibt die verbindlichen Spielregeln von Mosaic, basierend auf der tatsächlichen Logik der Engine.

## 1. Überblick & Spielziel

Mosaic ist ein abstraktes und taktisches Legespiel für zwei Personen. Eine Partie geht über exakt 5 Runden. Die Spieler sammeln farbige Fliesen, ordnen diese in ihren Musterreihen an und übertragen sie anschließend strategisch auf ihr persönliches Kuppel-Raster. Punkte können sowohl während des Spiels beim Platzieren auf der Kuppel als auch bei der großen Endwertung durch spezielle Wertungsplatten gesammelt werden. Wer am Ende die meisten Punkte vorweisen kann, gewinnt das Spiel.

## 2. Spielmaterial

* **Farbige Fliesen:** Es gibt insgesamt 65 normale Fliesen in 5 verschiedenen Farben (blau, gelb, rot, schwarz, türkis), also exakt 13 Stück pro Farbe. Zusätzlich existiert eine separate Reserve an besonderen Spezialfliesen.
* **Beutel & Turm:** Zu Beginn befinden sich alle 65 normalen Fliesen gut gemischt im Beutel. Verbrauchte oder abgeräumte Fliesen fallen in den Turm. Ist der Beutel leer, wird er mit den Fliesen aus dem Turm wieder neu befüllt.
* **Fabriken:** Es gibt 4 kleine Fabriken (diese starten mit je 4 Fliesen auf der Sonnenseite) sowie 1 große Fabrik (diese startet mit 5 Fliesen).
* **Das Spieler-Tableau:** Jeder Spieler besitzt ein eigenes Brett. Dieses besteht aus 6 Musterreihen, deren Kapazität sich von oben nach unten von 1 bis 6 Fliesen steigert. Es gibt zudem eine Strafleiste (den "Boden") mit 4 Feldern, die am Ende der Runde Minuspunkte von -1 bis -4 bringen. Das Herzstück ist die Kuppel, ein 3x3-Raster, das im Laufe des Spiels mit bis zu 9 Kuppelplatten gefüllt wird. Da jede Platte aus 2x2 Feldern besteht, entsteht nach und nach ein 6x6-Wertungsraster.
* **Bonusplättchen (Chips):** Pro Runde werden 2 Bonusplättchen verfügbar gemacht. Sie werden sofort aufgedeckt, sobald eine der Fabriken komplett geleert wurde.

## 3. Vorbereitung & Spielaufbau

* Zu Beginn jeder neuen Runde werden die kleinen Fabriken mit je 4 Fliesen und die große Fabrik mit 5 Fliesen (inklusive Startspielerstein) frisch aus dem Beutel befüllt.
* **Sonderregel für die große Fabrik:** Haben zufällig alle 5 gezogenen Fliesen dieselbe Farbe, werden sie zurückgelegt und es wird neu gezogen, bis mindestens zwei verschiedene Farben ausliegen.
* **Startkuppel (Nur vor der 1. Runde):** Vor dem eigentlichen Spielbeginn muss jeder Spieler eine Startkachel auf seiner Kuppel platzieren. Der Nicht-Startspieler legt seine Platte dabei zuerst, danach folgt der Startspieler. Diese Startplatzierung ist kostenlos, Position sowie Drehung sind frei wählbar und sie zählt nicht zu den regulären Zügen der ersten Runde.

## 4. Der Rundenablauf

Jede der 5 Runden ist in zwei aufeinanderfolgende Phasen unterteilt: Drafting (Fliesen nehmen) und Tiling (Auf die Kuppel legen).

### Phase 1: Drafting

Die Spieler sind abwechselnd am Zug und führen eine der folgenden vier Aktionen aus:

* **A) Kuppelplatte legen:** Der Spieler platziert eine von zwei möglichen Kuppelplatten in dieser Runde. Diese kann entweder kostenlos aus der offenen Ablage genommen oder für -1 Punkt blind vom Nachziehstapel gezogen werden.
* **B) Fliesen (Sonnenseite):** Der Spieler nimmt alle Fliesen einer gewünschten Farbe von der Sonnenseite einer Fabrik. Diese werden in exakt eine Musterreihe gelegt. Alle restlichen Fliesen dieser Fabrik wandern danach auf die Mondseite (als Mond-Stapel bei der kleinen Fabrik oder in den Moon-Pool bei der großen Fabrik).
* **C) Fliesen (Mondseite):** Der Spieler sammelt alle oben aufliegenden Fliesen einer bestimmten Farbe aus den Mondbereichen *aller* Fabriken gleichzeitig ein.
* **D) Bonusplättchen nehmen:** Der Spieler darf sich ein aufgedecktes Bonusplättchen einer leeren Fabrik nehmen (maximal 2 pro Runde).

**Wichtige Platzierungsregeln:**

* Passen aufgenommene Fliesen nicht mehr in die gewählte Musterreihe (oder passt die Farbe nicht), fallen alle überschüssigen Fliesen als Strafe auf die Strafleiste am Boden. Es ist auch erlaubt, Fliesen freiwillig direkt auf die Strafleiste zu legen.
* Ist die Strafleiste mit ihren 4 Plätzen voll, fallen weitere Fliesen direkt in den Turm.
* Nimmt ein Spieler den Startspielerstein aus der großen Fabrik, beginnt er die nächste Runde, kassiert dafür am Rundenende aber feste -2 Punkte.

### Phase 2: Tiling

Am Ende der Runde werden die vollen Musterreihen ausgewertet.

* Die Reihen werden zwingend von oben nach unten (Reihe 1 bis 6) abgearbeitet. Passt eine Fliesenfarbe zu einer vorhandenen Kuppelplatte, ist diese auch zu legen. Wird eine tiefere Reihe gelegt, sind darüberliegende Reihen für den Rest dieser Phase gesperrt.
* Von jeder fertigen Reihe wird genau ein Stein auf ein passendes Feld der Kuppel übertragen, die restlichen Steine der abgeräumten Reihe wandern in den Turm.
* Unplatzierbare volle Reihen (für die es kein freies Feld auf der Kuppel gibt) müssen zwingend geräumt werden; ihre Steine fallen als Strafe auf den Boden in Richtung Turm.

**Punktevergabe beim Legen:**

* Ein Stein ohne orthogonal angrenzende Nachbarn bringt 1 Punkt.
* Berührt der Stein eine Linie aus gleichfarbigen Steinen, gibt es Punkte in Höhe der Gesamtlänge. Für eine horizontale Linie der Länge *h* (>1) gibt es *h* Punkte, für eine vertikale Linie der Länge *v* (>1) gibt es *v* Punkte. Ist beides der Fall, wird die Summe aus beidem gebildet.

**Einsatz von Bonusplättchen (Chips):**

* Unvollständige Musterreihen können durch den geschickten Einsatz von Bonusplättchen komplettiert werden.
* Um ein fehlendes Feld auszugleichen, müssen entweder 2 Chips in der exakt gleichen Farbe oder 3 Chips in beliebiger Farbe ausgegeben werden. Auch hier gilt die Top-down-Regel: Gesperrte Reihen können nicht mehr per Chip befüllt werden.

### Rundenende-Abrechnung

* Die Strafleiste wird abgerechnet: -1, -2, -3 und -4 Punkte für die jeweiligen belegten Slots.
* Der Startspielerstein bringt weitere -2 Punkte.
* Die Gesamtpunktzahl eines Spielers kann durch Strafen jedoch niemals unter 0 fallen.

## 5. Spezialfliesen & Spezialfelder

* Auf den Kuppelplatten befinden sich gesperrte Spezialfelder.
* Ein solches Feld wird erst dann (und nur in der Tiling-Phase) freigeschaltet, wenn die restlichen drei regulären Felder derselben Platte erfolgreich belegt wurden.
* Auf ein nun freies Spezialfeld darf eine Spezialfliese aus der separaten Reserve gelegt werden.
* **Wertung:** Die Spezialfliese bringt sofort Punkte entsprechend der Reihe (1 bis 6), in der sie platziert wird. Sie selbst profitiert nicht von Linien-Boni, wird aber von anderen, angrenzenden Fliesen als Joker-Nachbar mitgewertet.

## 6. Spielende & Endwertung

Nach der 5. Runde endet das Spiel. Zu den erspielten Punkten kommt nun die Endwertung hinzu, für die 3 von 8 möglichen Wertungsplatten herangezogen werden. Von 4 festgelegten Paaren darf jeweils nur maximal eine Platte gewählt werden, da sie sich thematisch ausschließen.

**Die 8 Wertungsplatten:**

1. ↔️ **Horizontale Reihen:** 3 Pkt. je kompletter horizontaler Reihe. *(Schließt Nr. 8 aus)*
2. ↕️ **Vertikale Reihen:** 7 Pkt. je kompletter vertikaler Reihe. *(Schließt Nr. 5 aus)*
3. ↗️ **Diagonale Reihen:** 10 Pkt. je kompletter Diagonale (max. 2 Stück möglich). *(Schließt Nr. 6 aus)*
4. 🌈 **Mehrfarbige Felder:** 2 Pkt. je Wildcard-Feld, vorausgesetzt *alle* sind belegt. *(Schließt Nr. 7 aus)*
5. ⬜ **Äußere Felder:** 1 Pkt. je Fliese am äußersten Rand der Kuppel. *(Schließt Nr. 2 aus)*
6. 🔲 **Eckplatten:** 3 Pkt. je kompletter oberer Eckplatte, 8 Pkt. je kompletter unterer Eckplatte (alle 4 Felder belegt). *(Schließt Nr. 3 aus)*
7. ⭐ **Spezialfelder:** -3 Pkt. je leer gebliebenem Spezialfeld. *(Schließt Nr. 4 aus)*
8. 🎨 **Farbenreiche Reihen:** 4 Pkt. je horizontaler Reihe, die mindestens 5 verschiedene Farben enthält. *(Schließt Nr. 1 aus)*

Wer nach der Endwertung die höchste Gesamtpunktzahl erreicht hat, ist der Sieger. Bei einem Gleichstand gewinnt der Spieler, der den Startspielerstein besitzt.