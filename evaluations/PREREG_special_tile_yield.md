<!-- STATUS: OFFEN | Frage: Die Spezialfliesen sind der groesste unabgeholte Posten auf dem Brett -- ihr Wert steigt genau dort, wo sie am schwersten erreichbar sind. Laesst sich das heben, und an welchem der beiden Hebel? | Beleg: NICHTS GEBAUT, angelegt 2026-08-25 auf Nutzer-Auftrag. NEUE Datei, weil die Substanz bisher in ZWEI Dokumenten liegt, die BEIDE UEBERHOLT sind -- und zwar aus Traeger-Gruenden, nicht weil die Frage beantwortet waere: PREREG_plate_head.md (Kopf gebaut und wieder entfernt) traegt die Messung, PREREG_injection_dose.md (Knopf MOSAIC_UNLOCK_SHAPING_W wirkungslos) traegt den Bau-Versuch. Mechanik am Code geprueft: Punktwert = Musterreihe + 1, also 1..6 (round_end.rs:361-362); Freischaltung erst, wenn die anderen drei Felder des Slots gefuellt sind (dome.rs:139); Kriterium 6 ist -3 je LEEREM Spezialfeld auf GELEGTEN Platten, rein negativ-additiv und gated (scoring.rs:921-923). Gemessene Luecke: ein Spezialfeld der UNTEREN Slot-Reihe bleibt in ~84 Prozent der Partien leer, in der oberen nur in ~13 (monoton, Slot 8 unten rechts 89,8 Prozent). ZWEI HEBEL, die nicht vermengt werden duerfen: (A) Auswahl -- solche Platten gar nicht erst unten legen; (B) Vollendung -- die vorhandenen freischalten. VOR jedem Bau steht eine Neumessung auf hv2, weil alle Zahlen aus plattenblindem Spiel stammen. AN WELCHEM SPIELER (par.4a, Nutzer-Frage 2026-08-25): an der HEURISTIK, als Routing-Vorzug in der Plattenplatzierung -- Slot-Wahl legt slot_row*2+{0,1} fest, die ROTATION verschiebt das Spezialfeld um eine Musterreihe (dome.rs:89-97, Layout [0][1]/[2][3]). Nicht ans Netz: die Netz-Seite hat diese Frage viermal versucht und viermal verloren, und die Uebertragung ist ohnehin die Destillation. -->

# Vorregistrierung: Ertrag der Spezialfliesen

**Angelegt 2026-08-25** auf Nutzer-Auftrag, nichts gebaut.

## par.1 Warum eine neue Datei (Pruefung vor dem Anlegen)

Der Bestand wurde durchsucht; 23 Preregs erwaehnen Spezialfelder, aber keine
LEBENDE hat sie zum Gegenstand. Die Substanz liegt in zwei Dokumenten, die
beide UEBERHOLT sind -- **und beide aus Traeger-Gruenden**:

| Datei | Warum ueberholt | Was darin steckt |
| --- | --- | --- |
| `PREREG_plate_head.md` | der Kopf wurde am 2026-08-10 gebaut und wieder ENTFERNT | die Messung der Leer-Raten je Slot |
| `PREREG_injection_dose.md` | `MOSAIC_UNLOCK_SHAPING_W` ist seit der Zusammenfuehrung WIRKUNGSLOS | der einzige Bau-Versuch |

**In beiden Faellen ist das Vehikel weggefallen, nicht die Frage.** Genau
deshalb ist die Sache heute unbeantwortet statt erledigt.

## par.2 Die Mechanik, am Code geprueft (2026-08-25)

* **Punktwert ist reihenabhaengig**: `pattern_row = slot_row * 2 + sp_idx / 2`,
  `bonus = pattern_row + 1` (round_end.rs:361-362). Also 1 Punkt in der
  obersten Musterreihe, **6 in der untersten**.
* **Freischaltung ist konjunktiv**: der Special-Space entriegelt erst, wenn
  die anderen DREI Felder des Slots gefuellt sind
  (`try_unlock_special`, dome.rs:139-141).
* **Abrechnung kostet zusaetzlich einen weissen Stein**
  (`check_special_trigger`, round_end.rs:324).
* **Kriterium 6 ist etwas ANDERES** und wird oft damit verwechselt: -3 je
  LEEREM Spezialfeld auf GELEGTEN Platten, rein negativ-additiv und gated
  (scoring.rs:921-923). Es ist ein Abzug, den man verkleinert, kein Ertrag,
  den man einsammelt.

**Daraus die Spannung, um die es geht:** der Wert einer Spezialfliese steigt
mit der Slot-Reihe, und die Erreichbarkeit faellt mit ihr. Die teuerste ist
die schwerste.

## par.3 Die gemessene Luecke (Quelle: `PREREG_plate_head.md`, plattenblinder Korpus)

Leer-Rate je Slot, **monoton von oben nach unten**; unten rechts (Slot 8)
**0,898**. Zusammengefasst: ein Spezialfeld der UNTEREN Slot-Reihe bleibt in
**~84 Prozent** der Partien leer, in der OBEREN nur in **~13 Prozent**.

Das deckt sich mit der Nutzer-Aussage vom 2026-08-10 (*"in reihe 3 der slots
... will ich keine spezialkuppeln haben"*) und mit dem Mechanismus: die
unteren Musterreihen sind die traegsten, und die Freischaltung braucht drei
gefuellte Nachbarfelder.

**Heute gemessen (v22-Pilot, 200 Partien je Arm), Kriterium 6:**

| | `v2huelle` | `v1` |
| --- | --- | --- |
| k6-Punkte je Partie | **-9,98** | -11,72 |

Der Lehrer verbessert es um 1,74 Punkte, **ohne es zu adressieren** -- k6
reagiert also auf Spaltenbau. Das ist der Hinweis, dass der Posten beweglich
ist; es ist kein Beleg, dass er direkt ansteuerbar waere.

## par.4 ZWEI Hebel, die nicht vermengt werden duerfen

* **(A) AUSWAHL.** Platten, deren Spezialfeld in der unteren Slot-Reihe landen
  wuerde, gar nicht erst dort legen. Das ist ein Entscheid bei der
  PLATTEN-PLATZIERUNG, kein Bewertungsterm -- und der Praezedenzfall spricht
  dafuer: der v2-Durchbruch kam durchgehend vom ROUTING, nie von einem
  Bewertungsterm (`PREREG_heuristic_v2_long_rows.md` par.8.6/9.1/9.2).
* **(B) VOLLENDUNG.** Die vorhandenen freischalten. Das ist derselbe Engpass
  wie bei den Spalten (`project_column_completion_structural_weakness`): Bau
  bis kurz vor Schluss da, letzte Zellen nie.

**Sie sind nicht dasselbe und duerfen nicht in einem Arm gemessen werden.**
(A) senkt den k6-Abzug UND vermeidet unerreichbare Punkte; (B) holt Punkte,
die schon auf dem Brett liegen. Ein Arm, der beides bewegt, laesst hinterher
nicht zuordnen, welcher Teil gewirkt hat.

## par.4a AN WELCHEM SPIELER? Die Heuristik (Nutzer-Frage 2026-08-25)

par.4 liess das offen. **Entschieden: der Eingriff gehoert an die HEURISTIK,
nicht ans Netz** -- und zwar nicht als Entweder-oder, sondern als Reihenfolge
Heuristik -> Korpus -> Netz, genau wie sie gerade fuer die Spalten laeuft.

**Der Stellhebel ist die Plattenplatzierung, und er ist zweistufig** (am Code
geprueft 2026-08-25):

* **Slot-Wahl** bestimmt `slot_row * 2 + {0,1}` -- Slot-Reihe 0 ergibt die
  Musterreihen 1-2, Reihe 1 die Reihen 3-4, Reihe 2 die Reihen 5-6.
* **Rotation** verschiebt das Spezialfeld zwischen oberer und unterer
  Slot-Haelfte: die Platte ist 2x2 mit Layout `[0][1] / [2][3]`, und
  `rotation_indices` permutiert die Indizes (dome.rs:89-97). Weil
  `pattern_row = slot_row*2 + sp_idx/2` gilt, aendert eine Drehung die
  Musterreihe um EINS -- also einen Punkt und eine Erreichbarkeitsstufe.

Beides steckt in derselben Aktion (`{type: dome, slot_row, slot_col,
rotation}`), ist also mit einem Routing-Vorzug erreichbar und braucht keinen
neuen Kopf und keinen Bewertungsterm.

**Warum nicht das Netz -- vier Gruende, drei davon aus Messungen:**

1. **Routing hat bei diesem Lehrer jedes Mal gewirkt, Bewertungsterme nie.**
   par.8.6 trennt Struktur (Zielkarte) von Staerke (lineare Terme); zwei
   gerechnete Punktekarten ALS Routing-Ziel waren negativ (par.9.1/9.2). Der
   Durchbruch kam durchgehend vom Routing.
2. **Die Netz-Seite hat diese Frage viermal versucht und viermal verloren:**
   `injection_dose` (Knopf wirkungslos), `plate_head` (gebaut, entfernt),
   Shaping-Skalen-Sweeps (H0, 284:295), Ownership-Kopf (Gewicht 0).
3. **Die Regel ist hart und diskret** ("keine Spezialkuppeln in die untere
   Slot-Reihe"). Eine Routing-Regel drueckt das exakt aus, ein gelernter Term
   naeherungsweise und mit Nebenwirkungen auf alles andere.
4. **Die Uebertragung ans Netz ist ohnehin die Destillation.** Was der Lehrer
   tut, steht im Korpus; genau so traegt hv2 gerade den Spaltenbau ins naechste
   Netz (0,741 gegen 0,050). Ein zusaetzlicher Netz-Eingriff waere ein
   ZWEITER Weg zum selben Ziel und wuerde die Zuordnung zerstoeren.

**Konsequenz fuer den Zeitpunkt:** der Arm gehoert damit an den LEHRER, also
in dieselbe Werkstatt wie `PREREG_heuristic_v2_long_rows.md` -- und sein
Ergebnis erreicht das Netz erst ueber den naechsten Korpus, nicht ueber das
laufende v22.

## par.5 Was VOR jedem Bau zu tun ist

**(1) Neumessung auf hv2.** Alle Zahlen in par.3 stammen aus plattenblindem
Spiel. Die stehende Regel
([[feedback_dont_calibrate_to_plate_blind_play]]) sieht die Wiedervorlage
genau fuer den ersten plattenbewussten Korpus vor -- und der laeuft gerade.
Zu erheben: Leer-Rate je Slot, Zahl der freigeschalteten Spezialfelder je
Partie, Summe der dadurch erzielten Punkte, und k6 getrennt davon.

**(2) Der Grundraten-Waechter.** Kriterium 6 kann per Konstruktion NIE positiv
werden. Eine Kennzahl wie "Anteil Partien mit k6-Ertrag > 0" ist deshalb eine
Tautologie, kein Befund -- dieser Fehler ist am 2026-08-25 einmal gemacht
worden. Die tragenden Groessen sind die ZAHL gefuellter Spezialfelder und ihre
PUNKTSUMME, dazu k6 als getrennter Posten.

**(3) Der Formziel-Waechter.** Vier Arme haben dieselbe Signatur gezeigt --
ein Formziel optimiert, Punkte verloren, Teilspalten hoch, volle Spalten
runter (`PREREG_heuristic_v2_long_rows.md` par.9.1, 9.2, 12, 15). Jeder
Spezialfeld-Arm misst deshalb PFLICHTMAESSIG das Punkteniveau und die
Strafleiste mit, nicht nur die Spezialfeld-Ausbeute.

## par.6 Entscheidungsmass (vorab)

**Primaer: eigene Punkte und Margin** in der gepaarten Arena, Block-Ebene.
Nicht die Spezialfeld-Quote -- die ist die Zwischengroesse, und in diesem
Projekt sind Zwischengroessen schon dreimal gestiegen, ohne dass Staerke
folgte (k1-Baurate beim implicit-minimax-Arm, Teilspalten bei den vier oben,
Orakelmetriken beim 2D-Encoder).

**Begleitend zu berichten** (Standard-Kennzahlen): Reihen-, Spalten- und
Strafleistenauslastung, Punkte je Wertungsplatte, eigene Punkte, Margin.

**Abbruchbedingung:** faellt schon die Neumessung aus par.5(1) so aus, dass
der Lehrer die unteren Spezialfelder bereits weitgehend abholt, ist der Posten
klein geworden und der Arm entfaellt -- das waere ein vollwertiges Ergebnis.
