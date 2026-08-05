# 🎲 Mosaic — Offizielle Spielanleitung

Diese Anleitung beschreibt die verbindlichen Spielregeln von Mosaic, basierend auf der tatsächlichen Logik der Engine. *(Vollabgleich Engine ↔ Original-Regelbuch ↔ dieses Manual am 2026-08-06: drei Fehler korrigiert, acht Lücken ergänzt — Details in `evaluations/STATUS.md`, Abschnitt Regelbuch-Audit.)*

## 1. Überblick & Spielziel

Mosaic ist ein abstraktes und taktisches Legespiel für zwei Personen. Eine Partie geht über exakt 5 Runden. Die Spieler sammeln farbige Fliesen, ordnen diese in ihren Musterreihen an und übertragen sie anschließend strategisch auf ihr persönliches Kuppel-Raster. Punkte können sowohl während des Spiels beim Platzieren auf der Kuppel als auch bei der großen Endwertung durch spezielle Wertungsplatten gesammelt werden. Wer am Ende die meisten Punkte vorweisen kann, gewinnt das Spiel.

## 2. Spielmaterial

* **Farbige Fliesen:** Es gibt insgesamt 65 normale Fliesen in 5 verschiedenen Farben (blau, gelb, rot, schwarz, türkis), also exakt 13 Stück pro Farbe. Zusätzlich existiert eine separate Reserve von 9 Spezialfliesen.
* **Beutel & Turm:** Zu Beginn befinden sich alle 65 normalen Fliesen gut gemischt im Beutel. Verbrauchte oder abgeräumte Fliesen fallen in den Turm. Ist der Beutel leer, wird er mit den Fliesen aus dem Turm wieder neu befüllt. Reichen Beutel und Turm zusammen einmal nicht mehr aus (Fliesen auf den Kuppeln verlassen den Kreislauf dauerhaft), startet die Runde mit teilbefüllten oder leeren Fabriken; Bonusplättchen leer gestarteter Fabriken werden sofort aufgedeckt.
* **Fabriken:** Es gibt 4 kleine Fabriken (diese starten mit je 4 Fliesen auf der Sonnenseite) sowie 1 große Fabrik (diese startet mit 5 Fliesen).
* **Das Spieler-Tableau:** Jeder Spieler besitzt ein eigenes Brett. Dieses besteht aus 6 Musterreihen, deren Kapazität sich von oben nach unten von 1 bis 6 Fliesen steigert. Es gibt zudem eine Strafleiste (den "Boden") mit 4 Feldern, die am Ende der Runde Minuspunkte von -1 bis -4 bringen. Das Herzstück ist die Kuppel, ein 3x3-Raster, das im Laufe des Spiels mit bis zu 9 Kuppelplatten gefüllt wird. Da jede Platte aus 2x2 Feldern besteht, entsteht nach und nach ein 6x6-Wertungsraster.
* **Kuppelplatten:** Insgesamt 18 Stück. Jede Platte trägt 3 Farbfelder und 1 Sonderfeld — bei 9 Platten ist das Sonderfeld ein **Spezialfeld** (gesperrt, siehe Abschnitt 5), bei den anderen 9 ein **Wildfeld**, das beim Legen jede beliebige Farbe akzeptiert. 3 Platten liegen offen in der Ablage, der Rest bildet den verdeckten Nachziehstapel. Die offene Ablage wird während einer Runde **nicht** nachgefüllt (einzige Ausnahme: nach den Startkuppel-Platzierungen); erst bei der Rundenvorbereitung wird sie wieder auf 3 aufgefüllt.
* **Bonusplättchen (Chips):** Zu Rundenbeginn wird auf jede der 4 kleinen Fabriken 1 verdecktes Bonusplättchen gelegt (4 pro Runde, Vorrat 20 Stück für 5 Runden). Ein Plättchen wird aufgedeckt, sobald seine Fabrik komplett geleert wurde.
* **Startpunkte:** Jeder Spieler beginnt die Partie mit **5 Punkten**.

## 3. Vorbereitung & Spielaufbau

* Zu Beginn jeder neuen Runde werden die kleinen Fabriken mit je 4 Fliesen und die große Fabrik mit 5 Fliesen (inklusive Startspielerstein) frisch aus dem Beutel befüllt.
* **Sonderregel für die große Fabrik:** Haben zufällig alle 5 gezogenen Fliesen dieselbe Farbe, werden sie zurückgelegt und es wird neu gezogen, bis mindestens zwei verschiedene Farben ausliegen. Können Beutel und Turm zusammen keine zwei verschiedenen Farben mehr liefern, wird die monochrome Befüllung akzeptiert — wer diese 5 gleichfarbigen Fliesen nimmt, erhält den Startspielerstein.
* **Startkuppel (Nur vor der 1. Runde):** Vor dem eigentlichen Spielbeginn muss jeder Spieler eine Startkachel auf seiner Kuppel platzieren. Der Nicht-Startspieler legt seine Platte dabei zuerst, danach folgt der Startspieler. Diese Startplatzierung ist kostenlos, Position sowie Drehung sind frei wählbar und sie zählt nicht zu den regulären Zügen der ersten Runde (sie verbraucht auch keines der beiden Runden-Plättchen aus Abschnitt 4A).

## 4. Der Rundenablauf

Jede der 5 Runden ist in zwei aufeinanderfolgende Phasen unterteilt: Drafting (Fliesen nehmen) und Tiling (Auf die Kuppel legen).

### Phase 1: Drafting

Die Spieler sind abwechselnd am Zug und führen eine der folgenden vier Aktionen aus. Wer keine gültige Aktion mehr hat, **muss** passen (freiwilliges Passen ist nicht erlaubt); der andere Spieler zieht dann ggf. mehrfach hintereinander weiter.

* **A) Kuppelplatte legen:** In den Runden 1–4 **muss** jeder Spieler genau 2 Kuppelplatten legen — die Drafting-Phase endet erst, wenn beide Spieler ihre 2 Platten verbaut haben. In Runde 5 werden **keine** Kuppelplatten mehr gelegt. Eine Platte kann entweder kostenlos aus der offenen Ablage genommen oder blind vom Nachziehstapel gezogen werden. **Der Stapel-Zug im Detail:** Jede Ziehung kostet 1 Punkt und darf beliebig oft wiederholt werden (die Rückseite verrät nur den Platten-Typ — Wild oder Spezial); erst nach dem Zieh-Stopp werden die Vorderseiten aufgedeckt, eine Platte wird gewählt und platziert, die übrigen wandern in beliebiger Reihenfolge zurück unter den Stapel. Steht der Punktestand bei 0, sind weitere Ziehungen faktisch kostenlos (der Stand kann nie unter 0 fallen — bewusste Auslegung, siehe Punkteregeln). Einmal gelegte Platten sind fix; Position und Rotation sind frei.
* **B) Fliesen (Sonnenseite):** Der Spieler nimmt alle Fliesen einer gewünschten Farbe von der Sonnenseite einer Fabrik. Diese werden in exakt eine Musterreihe gelegt. Alle restlichen Fliesen dieser Fabrik wandern danach auf die Mondseite (als Mond-Stapel bei der kleinen Fabrik oder in den Moon-Pool bei der großen Fabrik). **Bei der kleinen Fabrik bestimmt der nehmende Spieler die Stapel-Reihenfolge der Restfliesen selbst** — strategisch relevant, denn vom Mond-Stapel sind später nur die obersten Fliesen nehmbar.
* **C) Fliesen (Mondseite):** Der Spieler sammelt alle oben aufliegenden Fliesen einer bestimmten Farbe aus den Mondbereichen *aller* Fabriken gleichzeitig ein (je Stapel zählt nur die oberste Fliese; aus dem Moon-Pool der großen Fabrik alle dieser Farbe).
* **D) Bonusplättchen nehmen:** Der Spieler nimmt sich ein aufgedecktes Bonusplättchen einer leeren Fabrik. Jeder Spieler nimmt **genau 2 pro Runde** — da alle 4 Plättchen aufgedeckt werden und die Runde erst endet, wenn keines mehr ausliegt, ist das keine Option, sondern Pflicht.

**Wichtige Platzierungsregeln:**

* Passen aufgenommene Fliesen nicht mehr in die gewählte Musterreihe (oder passt die Farbe nicht), fallen alle überschüssigen Fliesen als Strafe auf die Strafleiste am Boden. Es ist auch erlaubt, Fliesen freiwillig direkt auf die Strafleiste zu legen.
* Ist die Strafleiste mit ihren 4 Plätzen voll, fallen weitere Fliesen direkt in den Turm.
* Der Startspielerstein wird NUR bei der ersten Nahme vom **Mondbereich** der großen Fabrik vergeben — eine Sonnen-Nahme lässt ihn liegen. Die Mitnahme ist nicht ablehnbar. Wer ihn nimmt, beginnt die nächste Runde, kassiert dafür am Rundenende aber feste -2 Punkte. (Einzige Ausnahme: musste die große Fabrik mangels zwei verfügbarer Farben monochrom befüllt werden, geht der Stein bereits mit der Sonnen-Nahme der 5 gleichfarbigen Fliesen.) Da die Runde erst endet, wenn auch die große Fabrik restlos leer ist — den Stein eingeschlossen —, wird er in jeder Runde von einem der Spieler genommen.

### Phase 2: Tiling

Am Ende der Runde werden die vollen Musterreihen ausgewertet.

* Die Reihen werden zwingend von oben nach unten (Reihe 1 bis 6) abgearbeitet. Passt eine Fliesenfarbe zu einer vorhandenen Kuppelplatte, ist diese auch zu legen. Wird eine tiefere Reihe gelegt, sind darüberliegende Reihen für den Rest dieser Phase gesperrt.
* Von jeder fertigen Reihe wird genau ein Stein auf ein passendes Feld der Kuppel übertragen, die restlichen Steine der abgeräumten Reihe wandern in den Turm.
* **Unplatzierbare Reihen:** Sind einer Musterreihe bereits alle 3 Kuppelplatten zugeordnet und gibt es dort kein passendes freies Feld mehr, muss die Reihe (auch eine unvollständige) zwingend geräumt werden; ihre Steine fallen als Strafe Richtung Strafleiste/Turm. Hat die zugehörige Kuppel-Reihe dagegen noch freie Platten-Slots, **bleiben die Fliesen liegen und tragen in die nächste Runde über** — erst eine später gelegte passende Platte (oder das Volllaufen der Slots) entscheidet ihr Schicksal.
* Nicht volle Reihen ohne Platzierungszwang verbleiben ebenfalls unverändert für die nächste Runde.

**Punktevergabe beim Legen:**

* Ein Stein ohne orthogonal angrenzende Nachbarn bringt 1 Punkt.
* Berührt der Stein eine zusammenhängende Linie aus Steinen, gibt es Punkte in Höhe der Gesamtlänge — **die Farben der Steine spielen dabei keine Rolle**, jede belegte Fliese zählt (auch Spezialfliesen). Für eine horizontale Linie der Länge *h* (>1) gibt es *h* Punkte, für eine vertikale Linie der Länge *v* (>1) gibt es *v* Punkte. Ist beides der Fall, wird die Summe aus beidem gebildet.

**Einsatz von Bonusplättchen (Chips):**

* Unvollständige Musterreihen (mit mindestens 1 Fliese) können durch den geschickten Einsatz von Bonusplättchen komplettiert werden — freiwillig, kein Zwang.
* Um ein fehlendes Feld auszugleichen, müssen entweder 2 Chips in der exakt gleichen Farbe wie die Reihe oder 3 Chips in beliebiger Farbe ausgegeben werden (mischbar über mehrere fehlende Felder; zweifarbige Chips gelten als passend, wenn sie die Reihenfarbe zeigen). Auch hier gilt die Top-down-Regel: Gesperrte Reihen können nicht mehr per Chip befüllt werden.

### Rundenende-Abrechnung

* Die Strafleiste wird abgerechnet: -1, -2, -3 und -4 Punkte für die jeweiligen belegten Slots.
* Der Startspielerstein bringt weitere -2 Punkte.
* Die Gesamtpunktzahl eines Spielers kann durch Strafen jedoch niemals unter 0 fallen (der Deckel gilt bei jeder Verrechnung auf den Gesamtstand).

## 5. Spezialfliesen & Spezialfelder

* Auf 9 der 18 Kuppelplatten befindet sich ein gesperrtes Spezialfeld.
* Ein solches Feld wird erst dann (und nur in der Tiling-Phase) freigeschaltet, wenn die restlichen drei regulären Felder derselben Platte erfolgreich belegt wurden.
* Die Spezialfliese aus der separaten Reserve wird dann **sofort und automatisch** auf das freie Feld gelegt (keine Option). Die Reserve von 9 Fliesen kann nie ausgehen (9 Spezialfelder im Spiel).
* **Wertung:** Die Spezialfliese bringt sofort Punkte entsprechend der Reihe (1 bis 6), in der sie platziert wird. Sie selbst erhält keinen Linien-Bonus, zählt aber in den Linien anderer, angrenzender Fliesen als normale belegte Fliese mit.

## 6. Spielende & Endwertung

Nach der 5. Runde endet das Spiel. Zu den erspielten Punkten kommt nun die Endwertung hinzu, für die 3 von 8 möglichen Wertungsplatten herangezogen werden. Von 4 festgelegten Paaren darf jeweils nur maximal eine Platte gewählt werden, da sie sich thematisch ausschließen (physisch: 4 doppelseitige Platten — je Paar wird zufällig eine Seite bestimmt, davon kommen 3 der 4 Platten ins Spiel).

**Die 8 Wertungsplatten:**

1. ↔️ **Horizontale Reihen:** 3 Pkt. je kompletter horizontaler Reihe. *(Schließt Nr. 8 aus)*
2. ↕️ **Vertikale Reihen:** 7 Pkt. je kompletter vertikaler Reihe. *(Schließt Nr. 5 aus)*
3. ↗️ **Diagonale Reihen:** 10 Pkt. je kompletter Diagonale (max. 2 Stück möglich). *(Schließt Nr. 6 aus)*
4. 🌈 **Mehrfarbige Felder:** 2 Pkt. je Wildcard-Feld, vorausgesetzt *alle* sind belegt. *(Schließt Nr. 7 aus)*
5. ⬜ **Äußere Felder:** 1 Pkt. je Fliese am äußersten Rand der Kuppel. *(Schließt Nr. 2 aus)*
6. 🔲 **Eckplatten:** 3 Pkt. je kompletter oberer Eckplatte, 8 Pkt. je kompletter unterer Eckplatte (alle 4 Felder belegt). *(Schließt Nr. 3 aus)*
7. ⭐ **Spezialfelder:** -3 Pkt. je leer gebliebenem Spezialfeld. *(Schließt Nr. 4 aus)*
8. 🎨 **Farbenreiche Reihen:** 4 Pkt. je horizontaler Reihe, die mindestens 5 verschiedene Farben enthält (Spezialfliesen zählen nicht als Farbe; Lücken in der Reihe sind erlaubt). *(Schließt Nr. 1 aus)*

Wer nach der Endwertung die höchste Gesamtpunktzahl erreicht hat, ist der Sieger. Bei einem Gleichstand gewinnt der Spieler, der den Startspielerstein besitzt (also der Spieler, der ihn in Runde 5 genommen hat — genommen wird er in jeder Runde, siehe Phase 1).
