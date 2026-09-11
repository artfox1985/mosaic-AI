<!-- STATUS: OFFEN | Frage: Die Spezialfliesen sind der groesste unabgeholte Posten auf dem Brett; laesst sich das heben, und an welchem Hebel? | Beleg: Posten LEBT (par.7): auch der Lehrer laesst 81 % der unteren Spezialfelder liegen. K5 gebaut und einfaktoriell gemessen (par.9b-9d), seit 2026-09-07 in der Champion-Spec (v24-b07): hebt die vollen Spalten am staerksten von allem Gemessenen (0,5725 -> 0,6900) und ist siegneutral (243:257), ABER nicht ueber die Spezialfelder -- k6 wird leicht schlechter, die Punkte kommen aus vertikalen Reihen und Eckplatten. Netzseitige Hebel OFFEN: par.4a (Kanaele 77/78 gebaut, Wirkung nie isoliert), par.4c (Slot-Ausloesungs-Kopf, ungebaut); beide auf Nutzer-Priorisierung (par.7). -->

# Vorregistrierung: Ertrag der Spezialfliesen

**Angelegt 2026-08-25** auf Nutzer-Auftrag, nichts gebaut.

**NACHGEFUEHRT 2026-08-29 (Nutzer-Nachfrage "was ist damit passiert" --
der Kopf sagte faelschlich noch NICHTS GEBAUT):** par.4a ist am
2026-08-28 als Schlachtplan-Schritt 1a GEBAUT worden (`e91cd34`, "Zwei
Spezialfeld-Eingaben fuers Netz: Ertrag und Abstand zur Ausloesung";
Kanaele 77/78, NUM_PLANES_CHANNELS 79, features.rs:806-826 mit Verweis
auf diese Prereg, Tests vorhanden, Paritaets-Hash hielt). Jedes
v22-b-Modell (b01-b06) traegt die Eingaben seither. NICHT geschehen:
(1) die par.5-Neumessung auf hv2 (Pflicht vor dem naechsten Schritt,
alle par.3-Zahlen sind weiterhin plattenblind), (2) eine isolierte
Wirkungsmessung der Kanaele (b01 war Kaltstart MIT ihnen, es gibt kein
77-vs-79-A/B; ihr Beitrag ist in der b-Serien-Baseline konfundiert),
(3) der par.4c-Kopf-Entscheid, der laut par.4c/par.5 auf der Neumessung
wartet. Wer den naechsten Schritt faehrt, beginnt bei par.5(1).

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

## par.4 KEIN Vermeidungs-Hebel -- das Spezialfeld ist eine GRATISZELLE

**Die erste Fassung dieses Absatzes nannte als Hebel (A) "solche Platten gar
nicht erst unten legen". Das ist falsch, und zwar aus einem mechanischen
Grund, den zwei Nutzer-Korrekturen am 2026-08-25 aufgedeckt haben:**
*"die regel ist falsch"* und *"ohne der spezialkuppel dort unten werden zwei
spalten eher schwer"*.

**Am Code nachgesehen (round_end.rs:274-316, dome.rs:139-157, dome.rs:54-59):**

* Beim Setzen eines normalen Steins laeuft `try_unlock_special` (Zeile 275)
  und danach `check_special_trigger` (Zeile 316) -- **in DERSELBEN Aktion**.
* Sobald die anderen DREI Felder des Slots gefuellt sind, entriegelt das
  Spezialfeld und wird sofort selbst gefuellt (`placed_special = true`), mit
  Bonus `pattern_row + 1`.
* Fuer die Wertung zaehlt es dann als gefuellt: `is_filled()` liefert bei
  `SpaceType::Special` genau `placed_special` (dome.rs:54-59).
* Es kostet den Spieler dabei NICHTS -- kein zusaetzlicher Zug, kein Stein aus
  dem eigenen Vorrat, kein Vorrats-Risiko (9 Platten, 9 Fliesen, Kommentar
  round_end.rs:352).

**Daraus die Umkehr: ein Spezialfeld ist ein GESCHENKTES viertes Feld.** In
der unteren Slot-Reihe -- wo die anderen drei Zellen in den Musterreihen 5/6
liegen und am schwersten zu fuellen sind -- ist es die BILLIGSTE der sechs
Zellen einer Spalte. Wer die Platte dort vermeidet, ersetzt eine Gratiszelle
durch eine, die eine echte Musterreihe-5/6-Vollendung verlangt, und macht
damit **die beiden Spalten durch diesen Slot schwerer**.

**Und die 84 Prozent messen etwas anderes, als ich sie gelesen habe.** Sie
sagen nicht, dass das Spezialfeld schwer zu erreichen ist -- sie sagen, dass
der SLOT nie fertig wird. Das Spezialfeld ist das Symptom, nicht die Ursache.
Der Fehlschluss ist derselbe wie bei B1
([[project_long_row_avoidance_is_correct]]): "falscher Hebel, nicht falsches
Ziel", und ausdruecklich NICHT als "das Ziel ist schlecht" zu lesen.

**Der Entwurf ging zusaetzlich der selbsterfuellenden Falle auf den Leim**,
die `PREREG_heuristic_v2_long_rows.md` par.3b Nachtrag (3)(b) am selben Tag
beschreibt: eine Regel, die sich an der heutigen Leer-Verteilung orientiert,
schreibt die heutige Schwaeche fest.

## par.4b WAS STATTDESSEN DER GEGENSTAND IST: ein Gefaelle auf der Slot-Vollendung

Wenn sich das Spezialfeld selbst fuellt, ist es **kein eigenstaendiger Hebel**.
Was bleibt, ist praeziser und nuetzlicher: es liefert ein **quantifiziertes
Gefaelle**, WO Slot-Vollendung am meisten wert ist.

| Slot-Reihe | Musterreihen | Bonus beim Schliessen | dazu vermiedener k6-Abzug |
| --- | --- | --- | --- |
| 0 (oben) | 1-2 | +1 oder +2 | 3 |
| 1 (mitte) | 3-4 | +3 oder +4 | 3 |
| 2 (unten) | 5-6 | **+5 oder +6** | 3 |

Der Entwurf des Spiels ist damit sichtbar: **die Belohnung ist genau dort am
groessten, wo die Vollendung am schwersten faellt.** Ein Slot in der unteren
Reihe zu schliessen bringt bis zu 6 Bonuspunkte, 3 vermiedene Strafpunkte und
zwei Spalten-Zellen auf einmal.

**Das ist der registrierbare Gegenstand:** ob sich Slot-Vollendung nach diesem
Gefaelle gewichten laesst -- unten zuerst -- statt die Slots gleich zu
behandeln. Es ist damit kein eigener Arm neben der Vollendungsschwaeche,
sondern eine PRIORISIERUNG innerhalb von ihr.

## par.4a IN WELCHER FORM INS NETZ (Nutzer-Vorgabe 2026-08-25)

**Die erste Fassung empfahl die HEURISTIK. Nutzer-Vorgabe: *"wir fassen die
heuristik nicht mehr an"*. Damit ist jene Empfehlung gegenstandslos; der Weg
muss netzseitig sein.**

**Erst der Ort, denn er ist enger als gedacht.** Der Tiling-Loeser kennt den
Spezial-Bonus BEREITS EXAKT: `check_special_trigger` gehoert zu den in
`tiling_solver.rs` gespiegelten Engine-Funktionen (Kommentar Zeile 244),
`placed_special`/`is_locked` sind Teil des Tiling-Keys (Zeile 310), und es
gibt einen Test dafuer (`solver_counts_special_bonus_and_neighbor`,
Zeile 1750). Die PLATZIERUNG holt den Bonus also schon optimal ab, sobald sie
ihn erreichen kann.

**Die Luecke sitzt im DRAFTING** -- welche Steine mehrere Runden vorher
genommen werden, damit die drei Nachbarfelder eines unteren Slots ueberhaupt
zusammenkommen. Genau dort ist auch die Vollendungsschwaeche verortet.

**Was das Netz heute sieht** (features.rs): den Feldtyp `Special`
(Zeile 651/879), `placed_special` (452/862) und die Aggregate `special_empty`
/ `special_total`, beide durch 8 normiert (310-311, 691-692).

**Was es NICHT gereicht bekommt:** je Slot den ABSTAND zur Ausloesung und den
BETRAG, der dann faellt. Beides ist aus dem Brett ableitbar -- aber genau das
war auch bei der Spalten-Erreichbarkeit der Fall, und sie wurde trotzdem
explizit gemacht.

**Vorgeschlagene Form: eine ADDITIVE EINGABE, kein Kopf und kein
Shaping-Term.** Die Begruendung ist die Erfolgsbilanz dieses Projekts:

| Form | Bilanz |
| --- | --- |
| Hilfskoepfe | **0 von 4** (endgame, ownership, plate, conjunction) |
| Shaping-Terme auf Platten | `injection_dose` Knopf wirkungslos, Skalen-Sweeps H0 (284:295) |
| **additive Eingaben** | am 2026-08-25 gebaut (`col_f_max`, `cell_reachable_mask`), Champion bitgleich, Suite gruen |

**Zuschnitt (ungebaut, Vorschlag):** zwei zusaetzliche 6x6-Kanaele, je Slot
ueber seine 2x2 Zellen ausgelegt, damit der Conv-Zweig sie raeumlich sieht:

1. **Ausstehender Spezial-Ertrag** je Slot: `pattern_row + 1`, 0 wenn der Slot
   kein Spezialfeld hat oder es schon ausgeloest ist.
2. **Abstand zur Ausloesung**: Zahl der noch fehlenden der drei Nachbarfelder
   (0-3), 0 wenn kein ausstehendes Spezialfeld.

Das ist genau das Paar **Betrag x Abstand**, aus dem das Gefaelle aus par.4b
besteht -- und es ist dieselbe Bauform wie `col_f_max`, also mit bekanntem
Aufwand und bekannter Paritaets-Pruefung.

**Ehrlicher Vorbehalt, der vor den Bau gehoert:** die Erreichbarkeits-Eingaben
vom selben Tag haben noch KEIN Staerkeergebnis -- sie sind gebaut und
paritaetsgeprueft, mehr nicht. Der Praezedenzfall stuetzt also den AUFWAND und
die Bauform, nicht die Wirkungserwartung. Und die Information ist
prinzipiell ableitbar; die Wette ist Lesbarkeit, nicht Neuheit.

**Wirksam wird das erst ab dem naechsten Netz**, das mit erweiterter
Eingabegroesse trainiert wird -- fuer das laufende v22 kommt es zu spaet
(`INPUT_SIZE` steckt im Korpus-Cache und im Modell).

**BERICHTIGUNG (2026-08-27): der Absatz oben ist UEBERHOLT.** Er hat "zu
spaet" an die KORPUS-Erzeugung gehaengt; die Frist ist aber der
TRAININGS-START, und der steht noch aus (v22 laeuft als Kaltstart,
Nutzer-Entscheid 2026-08-27). Vier Punkte, die zusammen zeigen, dass fuer die
beiden Kanaele kein Korpus-Neubau noetig waere:

1. **Die Rohdaten liegen vor.** `dome_grid` wird seit jeher VOLL serialisiert,
   je Feld `type`/`color`/`filled`/`locked` (`engine/src/serialize.rs:182`) --
   die 2.400 vorhandenen pkl tragen also alles, was die Kanaele brauchen.
2. **Der Bauer sitzt schon an dieser Quelle.** `_board_channels`
   (`engine/py/neural_net.py:353`) rechnet die heutigen 6x6-Kanaele direkt aus
   `dome_grid`; zwei weitere entstuenden an derselben Stelle.
3. **Beide Formeln sind reine Geometrie und Brettzustand**, nichts
   Aufgezeichnetes: der Ertrag ist `pattern_row + 1`
   (`engine/src/round_end.rs:361-362`), die Ausloesung sind die drei
   gefuellten Nachbarfelder des Slots (`engine/src/dome.rs:139-141`).
4. **Der Preis ist ein CACHE-Neubau, kein Korpus-Neubau** -- parallel 36,1 min
   fuer den vollen Korpus (`PREREG_cache_build_time.md` par.8).

**Der Zuschnitt aendert sich damit auch technisch:** die beiden 6x6-Ebenen
waeren PLANE-Kanaele (`NUM_PLANES_CHANNELS` 77 -> 79, `features.rs:804`),
nicht flache Eingaben; `INPUT_SIZE` (714, `config.py:38`) bliebe unberuehrt.
Additiv nach dem 29fb1f1-Muster, Altmodelle bleiben bitgleich, weil
`net::split_planes_flat_batch_src` (`engine/src/net.rs:972ff`) den
Planes-Block auf die vom MODELL deklarierte Kanalzahl kuerzt.

## par.4c ANSCHLUSS an den Shaping-2D-Kopf (Nutzer 2026-08-25)

Nutzer: *"und somit haben wir wieder futter fuer den shaping 2d head"*. Der
Anschluss traegt, und er loest ein Problem, an dem der Kopf in
`PREREG_heuristic_v2_long_rows.md` par.3b haengt.

**Das dortige Ziel war schwach begruendet.** Nachtrag (2) hat gezeigt: die
Dreiecks-Abweichung je Zelle ist `erlaubt_o XOR belegt`, und `erlaubt_o` ist
eine FESTE Maske -- das Ziel ist also eine deterministische Umkodierung von
"belegt". Der Kopf haette nichts vorherzusagen gehabt.

**Die Slot-Ausloesung ist genau das Gegenteil.** "Wird dieses Spezialfeld bis
Partieende ausgeloest?" ist keine Umkodierung des heutigen Bretts, sondern
eine Vorhersage -- und zwar ueber die Groesse, bei der der Value-Kopf frueh am
schwaechsten ist. Dazu drei Eigenschaften, die kein bisheriges Shaping-Ziel
hatte:

* **Es ist 3x3.** Die Slot-Ebene ist von Haus aus zweidimensional -- der
  natuerlichste 2D-Kopf im ganzen Spiel, und einer, der beim heutigen flachen
  `Linear(hidden,128) -> Linear(128,72)` nichts von seiner Geometrie behaelt.
* **Es rechnet in PUNKTEN, nicht in Form.** Der Ertrag ist `pattern_row + 1`,
  die Vorhersage laesst sich also direkt in erwartete Punkte umrechnen. Damit
  faellt der Einwand weg, an dem vier Arme gescheitert sind -- "Formziel
  optimiert, Punkte verloren" (par.9.1/9.2/12/15): hier IST das Formziel der
  Punktestand.
* **Es ist klein.** 9 Ausgaben, nicht 36 oder 72.

**Der Einwand, der bleibt und benannt gehoert: das Ziel ist
POLITIKABHAENGIG.** "Wird ausgeloest" haengt am gespielten Verlauf, nicht am
Brett -- dieselbe Bauform, an der der Konjunktions-Kopf gescheitert ist
([[project_conjunction_head_predicts_occurrence]]: vier
Kalibrierungsvarianten, alle schlechter). Was den Fall hier unterscheidet, ist
allein der KORPUS: auf plattenblindem Spiel war "wird nicht ausgeloest" die
korrekte Vorhersage und der Kopf haette die Schwaeche festgeschrieben; auf
einem Lehrer-Korpus ist sie es nicht mehr. Das ist genau die Wiedervorlage,
die par.3b Nachtrag (3)(b) beschreibt -- und sie ist unbewiesen, bis die
Neumessung aus par.5 vorliegt.

**Verhaeltnis zur Eingabe aus par.4a:** die beiden sind KEINE Alternativen und
duerfen nicht in einem Arm laufen. Die Eingabe sagt dem Netz, was auf dem
Brett STEHT (Betrag und Abstand); der Kopf laesst es vorhersagen, was daraus
WIRD. Wer beides gleichzeitig einbaut, kann hinterher nicht zuordnen.
Reihenfolge-Vorschlag: erst die Eingabe (billiger, kein neues Ziel, bekannte
Bauform), der Kopf danach und nur, wenn die Neumessung das Ziel traegt.

## par.5 Was VOR jedem Bau zu tun ist

**(1) Neumessung auf hv2.** Alle Zahlen in par.3 stammen aus plattenblindem
Spiel. Die stehende Regel
([[feedback_dont_calibrate_to_plate_blind_play]]) sieht die Wiedervorlage
genau fuer den ersten plattenbewussten Korpus vor -- und der ist seit dem
2026-08-26 01:52 FERTIG (2.400 pkl = 24.000 Partien,
`data/manifest_hv2_20260825_172710.json`; "laeuft gerade" war der Stand vom
2026-08-25, BERICHTIGT 2026-08-27). Die Neumessung ist damit sofort fahrbar
und haengt an keinem Lauf mehr.
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

## par.7 NEUMESSUNG GEFAHREN 2026-08-29 (par.5(1); special_tile_yield_remeasure.json, Sonde tools/probes/special_tile_yield_measurement.py; 300 hv2-Dateien = 3.000 Partien/6.000 Seiten, dazu die b06-Messdateien = 200 Partien/400 Seiten; Leer-Rate ueber Spezialfelder GELEGTER Platten am Endbrett, Ertragsformel wie par.2)

| | hv2-Lehrer | v22-b06 |
| --- | --- | --- |
| Leer-Rate Slot-Reihe oben | 0,499 | 0,535 |
| Leer-Rate mitte | 0,833 | 0,819 |
| Leer-Rate unten | **0,807** | **0,881** |
| ausgeloeste Spezialfelder je Seite | 1,17 | 0,98 |
| Spezial-Punkte je Seite | 4,02 | 3,15 |
| k6 je Seite (wenn aktiv) | -9,97 | -11,26 |

**Abbruchbedingung NICHT erfuellt -- der Posten lebt.** Auch der
spaltenkompetente Lehrer laesst 81 Prozent der unteren Spezialfelder
liegen (und die liegen dort gehaeuft: 12.375 der ~27.000 gelegten
Spezialfelder sitzen in der unteren Slot-Reihe); das Netz ist ueberall
etwas schlechter (unten 0,881, k6 -1,3 schlechter). Zwei Befunde gegen
die plattenblinde par.3-Basis: (1) die OBERE Reihe ist beim Lehrer viel
LEERER als damals (0,50 gegen ~0,13) -- der Lehrer tauscht kurze Reihen
gegen lange, die oberen Slots schliessen seltener; die par.3-Skala ist
damit endgueltig als Korpus-Artefakt bestaetigt. (2) Unten bewegt sich
fast nichts (0,81 gegen ~0,84): die teuersten Felder bleiben in JEDEM
Regime der groesste unabgeholte Posten -- dieselbe Kosten-Scheu wie
D2-Huelle und Chip-Allokation (par.3b.8 Stufen D2/E der Lehrer-Prereg).
**Konsequenz fuer par.4c:** das Kopf-Ziel "wird ausgeloest" bleibt auch
auf dem Lehrer-Korpus stark unbalanciert (untere Reihe ~0,19 positiv);
der politikabhaengig-Einwand steht. Der Hebel gehoert damit in dieselbe
Gelaender-/Allokations-Familie wie Chip-Fuehrung und Huellen-Trimm --
Nutzer-Priorisierung der naechsten Sitzung, kein Automatismus.

## par.8 Der Posten am Tisch, 19 Server-Partien (14:53): Kuppel-Bonus 8,9 gegen 1,6 je Partie

`tools/probes/server_log_points_probe.py` ueber alle Server-Logs (13 gegen v21,
6 gegen den Champion v23-b01_k3p10), Tabelle in `docs/domain_knowledge.md`
Abschnitt 9 (Replikation). Der Mensch holt 8,9 Kuppel-Bonus-Punkte je Partie,
das Netz 1,6 (Champion 2,3); dazu Endwertung 19,7 gegen 4,2 (Spalten 9,6 gegen
0,7, Eckplatten 5,1 gegen 1,4). Die Platzierungspunkte sind gleich (54,9 gegen
56,8). Der Kuppel-Bonus ist gleich der Rasterreihe (1..6): der Posten sitzt
unten, wo par.7 die 81 Prozent liegen gebliebenen Spezialfelder gemessen hat.
Zusammenhang mit dem Sicht-Arm: das Netz konnte Spezial- und Jokerplatten in
der Auslage nicht unterscheiden (`PREREG_stack_top_feature.md` par.10); ob die
Sicht allein den Posten hebt, zeigt die Abnahme von v24-b04 -- Messgroesse
dafuer hier: Kuppel-Bonus je Partie aus den Arena-Logs (Zeile ⭐), nicht nur
die k6-Wertung.

## par.9 NUTZER-REGEL "EINE SPEZIALFLIESE IN REIHE 6" (2026-09-06, 17:43) und der Stand nach den v24-Abnahmen

**Nutzer, woertlich:** *"Vereinfacht gesprochen: soweit moeglich wuerd ich immer eine
spezialfliese in Reihe 6 aktivieren. Mehr geht sich nicht aus."* Vorher (17:35):
*"Die koennte den spalten und Punkten ebenfalls helfen."*

**Mechanik, am Code und im Handbuch geprueft:** das Spezialfeld einer Platte
schaltet in der Tiling-Phase frei, sobald die drei anderen Zellen der Platte
gefuellt sind (`round_end.rs:275` `try_unlock_special`, `docs/engine_manual.md`
Abschnitt 5); die Spezialfliese kommt sofort und automatisch aus dem Vorrat und
zahlt Punkte gleich der Rasterzeile (1 bis 6), zaehlt danach als belegte Zelle
(Spalten, Nachbarschaft). "Reihe 6" heisst: eine Spezialplatte im unteren Slot
(Slot-Zeile 2) so gedreht, dass ihr Spezialfeld in Rasterzeile 6 liegt, und ihre
drei Normalzellen gefuellt -- Ertrag +6 Kuppel-Bonus, zwei Spaltenzellen in den
Zeilen 5/6 und das Feld selbst. Neun der 18 Platten tragen ein Spezialfeld
(`dome.rs` Katalog: Designs 0, 4, 6, 7, 8, 10, 12, 15, 17); welche in Reihe 6
liegt, entscheidet die Draft-Phase (Plattenwahl und Rotation, `apply_dome`),
ob sie freischaltet, entscheiden Draft (Farben fuer Reihen 5/6) und Tiling.

**Stand nach den sechs v24-Abnahmen (Kuppel-Bonus je Partie aus den Tor-2b-Arenen,
`points_v24bXX_vs_b01_s14.json`, beide Richtungen):** v24-b01 3,8 (b01 3,6),
b02 4,0 / 3,5 (4,1 / 3,8), b03 4,15 / 4,16 (3,5 / 3,6), b04 3,9 / 4,3 (3,6 / 3,9),
b05 3,8 / 3,7 (3,5 / 4,1), b06 3,6 / 4,2 (4,0 / 4,5). Mensch am Tisch 8,9 (par.8).
**Die Sicht 744 (b04, b05, b06) hebt den Posten nicht** -- die offene Frage aus
par.8 ist damit mit nein beantwortet; der Abstand zum Menschen bleibt bei rund
fuenf Punkten je Partie. Der Seeding-Arm b03 liegt mit 4,2 am hoechsten.

**Baustein K5 "Reihe-6-Spezialfeld" (registriert, NICHT gebaut):** ein Knopf der
Gelaender-Familie (Default aus, bitidentisch; Spec-Pflichtfeld je Seite wie
`envelope_flush_w`), der die Nutzer-Regel in die Suche traegt:
1. **Plattenwahl (Draft), in SYMBIOSE mit der Einhuellenden** (Nutzer 17:43: "Das
   kannst bei der kuppelplatzierung eventuell ebenfalls Priorisieren in Symbiose
   mit der einhuellenden"): die Dreiecks-Huelle hat in Rasterzeile 6 genau EINE
   Zelle, links (5,0) bzw. rechts (5,5) (`envelope.rs` `Hull::contains`); der
   Zielplatz ist daher der untere Eckslot der bestpassenden Orientierung, das
   Spezialfeld per Rotation auf diese Huellenzelle. Eine so gelegte Spezialplatte
   erfuellt die Huelle und den Bonus mit derselben Platte. Bauform: Erweiterung
   der K3-P-Projektion (`projected_occupancy`-Familie), nicht ein zweiter Term --
   das Spezialfeld auf der Huellenzelle zaehlt als kuenftig belegt mit Gewicht
   `w_k5` (wird gefuellt, sobald die drei Normalzellen gefuellt sind), solange
   noch KEINE solche Platte liegt; "mehr geht sich nicht aus": die zweite zaehlt
   nichts. Damit zieht der bestehende Such-Term (e) die Platte an den richtigen
   Platz, ohne neuen Blattwert-Zuschlag.
2. **Fuellen (Draft und Tiling):** die drei Normalzellen dieser einen Platte
   bekommen in der Projektion (K3-P-Mechanik, `projected_occupancy`) ein hoeheres
   Gewicht, damit Reihen 5/6 mit den passenden Farben bevorzugt werden; die
   Freischaltung selbst macht die Engine.
3. **Messung** wie die K3-Arme (par.8.11 der Einhuellenden): argmax-Instrument
   und gepaarte Arena am Champion, Kennzahlen Siege, Punkte, volle Spalten,
   Kuppel-Bonus je Partie (Zeile 6 getrennt), lange Reihen begonnen/vollendet.
   Entscheidungsmass bleibt par.6 (Punkte und Marge, nicht die Quote).
Reihenfolge: NACH den vier K3-Armen am Champion (Kette laeuft 2026-09-06),
damit die Knoepfe nicht zusammenfallen; Bau nach den K3-Ergebnissen.

**GEZAEHLT (2026-09-06, 23:35; Nutzer-Frage "ist das auch ein verstaerker oder wieder ein
neues verhalten?"; Log-Zeilen `+N Spezial-Punkte (Kuppel-Bonus)`, N = Rasterzeile der
Spezialfliese; Quellen: b06-Arenen `paired_arena_env_v24b06_vs_b01_{first,second}_s14.json`
und `..._k3p2_b06_vs_k3p_{first,second}_s14.json` (je 160 Seiten je Spec), Server-Logs
`static/log/game_*.log` (22 Partien mit Endwertung; das `ai_model` wechselt ueber die Logs):**

| Seite | Seiten | Aktivierungen je Partie | davon Zeile 6 (+6) je Partie | Zeile 5 (+5) | Verteilung Zeile 1..6 |
| --- | --- | --- | --- | --- | --- |
| Mensch | 22 | 2,55 (8,8 Punkte) | **0,68** | 0,14 | 6 / 22 / 2 / 8 / 3 / 15 |
| Server-KI gegen Mensch | 22 | 0,50 (1,5 Punkte) | 0,05 | 0,00 | 2 / 4 / 0 / 4 / 0 / 1 |
| v24-b06 Champion-Spec (Arena) | 160 | 1,16 | **0,29** | 0,00 | 41 / 45 / 5 / 49 / 0 / 46 |
| v24-b06 mit K3-P2 (Arena) | 160 | 1,11 | 0,29 | 0,00 | 42 / 46 / 7 / 36 / 0 / 47 |
| v23-b01 Champion-Spec (Arena) | 160 | 1,21 | 0,35 | 0,00 | 41 / 45 / 3 / 49 / 0 / 56 |

Lesart: **K5 ist ueberwiegend ein VERSTAERKER.** Die Netze aktivieren in rund jeder dritten
Partie ein Spezialfeld in Zeile 6 (0,29-0,35 je Partie) und 1,1-1,2 Spezialfelder je Partie
insgesamt; das Verhalten liegt also im Korpus, nur seltener als beim Menschen (0,68 und
2,55). Neu waere die Kopplung an die Huelle (Spezialfeld auf der Huellenzelle der Zeile 6,
par.9 Punkt 1) und die Plattenwahl nach Spezialfeld statt nach Sofortpassung. Zwei
Nebenbefunde: (1) in 640 Netz-Seiten KEINE Aktivierung in Zeile 5 (Mensch 3 von 22
Partien) -- ob das Geometrie (Spezialfeld einer Platte im unteren Slot liegt in Zeile 5
oder 6, je nach Rotation) oder Vermeidung ist, ist ungeprueft; (2) die Server-KI gegen den
Menschen aktiviert deutlich weniger (0,50) als dieselbe Spec in der Netz-Arena (1,21) --
Gegnerabhaengigkeit der Plattenverfuegbarkeit, nicht weiter verfolgt.

### par.9a K5 WIRD GEBAUT UND GEGEN DIE HUELLENFORM GEMESSEN (Nutzer 2026-09-07, 06:07: "dann bau und miss das gemeinsam mit der form. gehoert ja zusammen")

**Was sich seit der Registrierung von par.9 geaendert hat:** die Huellenform 2
(`geometric_envelope` par.8.15b/8.15c) ist gebaut, ueber zwei Seeds gemessen und hebt den
Kuppel-Bonus von 3,6-3,8 auf **4,5-5,0 je Partie** -- den hoechsten je fuer ein Netz
gemessenen Wert (Mensch 8,9, alle sechs v24-Arme 3,5-4,3). Sie liefert damit bereits einen
Teil dessen, wofuer K5 gedacht war, aber auf anderem Weg: **die Form macht den Platz
VERFUEGBAR** (zwei Huellenzellen in Zeile 6 statt einer), **K5 zieht die Platte GEZIELT
dorthin** (Zuschlag in der Plattenwahl). Das sind zwei verschiedene Mechanismen auf
dieselbe Zelle.

**Bau (2026-09-07, 06:07 beauftragt):** Knopf `MOSAIC_SPECIAL_ROW6_W` / Spec-Pflichtfeld
`special_row6_w`, Default 0 = bitidentisch; Wirkung als Erweiterung der K3-P-Projektion
(par.9 Punkt 1), nicht als eigener Blattwert-Term; "mehr geht sich nicht aus" als
Ein-Platten-Regel; die Huellenform kommt als Parameter herein, damit K5 bei Form 2 ihre
ZWEI Zielplaetze kennt.

**Messung, vorab festgelegt:** Arm = Form 2 PLUS K5, **Kontrolle = Form 2 ALLEIN** (nicht
der Champion). Begruendung: der Form-Anteil ist ueber zwei Seeds bereits gemessen
(par.8.15b/c), eine Messung gegen den Champion wuerde zwei Faktoren mischen und den
bekannten Teil noch einmal bezahlen. So ist K5 einfaktoriell isoliert und die Frage lautet
genau: **bringt das gezielte Ziehen ueber die Geometrie hinaus noch etwas?**
Aufbau wie die uebrigen Arme (argmax-Instrument @400 mit 200 Partien Seed 20260931; gepaarte
Arena 2 x 80 Seed 20261014; Spalten-, Punkte- und Reihen-Alter-Sonde), Kennzahl im
Vordergrund ist der **Kuppel-Bonus je Partie**, dazu Siege, Punkte und volle Spalten.

**Lesart, vorab:** haelt K5 den Kuppel-Bonus der Form und hebt ihn weiter, ohne Siege oder
Spalten zu kosten, ist es ein Kandidat fuer die Champion-Spec. Bleibt der Bonus gleich, hat
die Geometrie den Posten bereits gehoben und der gezielte Zuschlag ist entbehrlich -- dann
faellt K5 wie die vier Knopf-Arme der Nacht. Kostet er Siege oder Spalten, faellt er
ebenfalls.

### par.9b K5 GEBAUT UND GEPRUEFT (2026-09-07, 09:20; Subagent, Koordinator hat Bericht und Kernstellen geprueft)

**Knopf `MOSAIC_SPECIAL_ROW6_W` / Spec-Pflichtfeld `special_row6_w`** (Default 0,0 = aus,
bitidentisch), Bauform parallel zu `envelope_flush_w`. **`cargo test --release --lib`:
543 Tests, 0 rot.** Wheel gebaut und installiert, Kontrakt unveraendert
`20b442a8164f748d`; die 13 lebenden Specs tragen das Feld
(`tools/spec_add_field.py special_row6_w 0.0`). **Anker-Drift und Konservierung je GRUEN**
(`anchor_drift_20260907_k5.json`, `anchor_conservation_20260907_k5.json`).

**Wirkung, wie in par.9 Punkt 1 verlangt (Erweiterung der Projektion, kein eigener
Blattwert-Term):** auf der fertigen Belegung je Orientierung (a) die Huellenzelle der
Zeile 6 zaehlt mit `w_k5` als kuenftig belegt, (b) die noch leeren Normalzellen derselben
Platte, die IN der Huelle liegen, werden mit `1 + w_k5` verstaerkt, gedeckelt auf 1.
Zellen ausserhalb der Huelle bleiben unberuehrt, weil eine Verstaerkung dort den
Aussen-Abzug vertiefen wuerde.

**Der tragende Befund des Baus, am Code geprueft:** beide Huellenzellen der Zeile 6 einer
Orientierung liegen im SELBEN Slot (`cell_to_dome_space(5,0)` und `(5,1)` -> Slot (2,0)).
**Form 2 gibt K5 also zwei ROTATIONSLAGEN derselben Platte, nicht zwei Platten.** Damit ist
die Kopplung zwischen Huellenform und K5 enger als in par.9 angenommen: die Form erweitert
nicht die Plattenwahl, sondern die Zahl der Drehungen, mit denen dieselbe Platte ihr
Spezialfeld ins Ziel bringt. Ausserdem verifiziert: 9 der 18 Designs tragen ein Spezialfeld
(Indizes 0, 4, 6, 7, 8, 10, 12, 15, 17, `dome.rs:209-227`), Freischaltung
`dome.rs:140 try_unlock_special`.

**Ein-Platten-Regel** ("mehr geht sich nicht aus"): `row6_special_target` liefert genau EINE
Spalte je Orientierung und gibt `None`, sobald auf einer Huellenzelle der Zeile 6 bereits
eine Spezialfliese LIEGT.

**Vom Bau benannte Unsicherheiten (uebernommen, nicht ausgeraeumt):** (a) die Verstaerkung
wirkt multiplikativ auf projizierte Masse, greift also erst nach dem ersten Stein in
Reihe 5/6; ein additiver Sockel waere der Alternativentwurf, haette aber die LEERE Platte
belohnt. (b) In Modus 4 laeuft die Orientierungswahl auf der bereits K5-veraenderten
Belegung, K5 kann dort die Huellenwahl kippen (in Modus 1 nicht). (c) Die
Laufzeit-Gegenprobe der Bitidentitaet am echten Suchpfad steht aus -- der Anker deckt sie
indirekt ab (hv1 ist netzlos, laeuft also nicht durch diesen Zweig), eine gezielte Probe
waere ein argmax-Instrument mit `w = 0` gegen den Bestandswert 0,4975.

**Messung** wie in par.9a festgelegt: Arm = Form 2 plus K5 gegen Kontrolle = Form 2 allein.

### par.9c K5 GEMESSEN: Spalten deutlich hoch, Siege nicht -- und die Wirkung kommt NICHT aus den Spezialfeldern (2026-09-07, 09:50-11:21)

Aufbau nach par.9a, einfaktoriell: Arm `models/hullform2_k5w10.spec.json` gegen Kontrolle
`models/hullform2.spec.json` -- vor dem Lauf geprueft, dass sich die beiden Specs in GENAU
einem Feld unterscheiden (`special_row6_w`) und die Kontrolle sich vom Champion in genau
einem (`envelope_hull_form`). Kette `tools/night_k5_row6_special.sh`, exklusiv.

**Das argmax-Instrument (200 Partien je Seite, Seed 20260931, @400): K5 hebt die Spalten
deutlich.**

| Instrument | Form 2 | Form 2 + K5 | Diff |
| --- | --- | --- | --- |
| **volle Spalten** | 0,5725 | **0,6900** | **+0,1175** |
| Punkte | 48,71 | 50,49 | +1,78 |
| Seiten mit voller Spalte | 173 | 201 | +28 |
| volle Zeilen | 0,165 | 0,158 | -0,008 |
| Strafleiste | 5,80 | 5,78 | -0,02 |

Zum Vergleich der Bezug derselben Skala: der Champion (Dreieck, kein K5) liegt bei
**0,4975** (`tor2a_v24b06.json`). Die Huellenform allein bringt +0,075, K5 obendrauf
+0,1175. **Das ist der groesste Spaltenzuwachs, den ein einzelner Knopf in dieser Kampagne
gezeigt hat.**

**Der Mechanismus ist aber NICHT der gebaute.** Die Aufschluesselung je Wertungsplatte
zeigt, dass ausgerechnet das Kriterium, auf das K5 zielt, leicht SCHLECHTER wird:

| Wertungsplatte | Form 2 | + K5 | Diff |
| --- | --- | --- | --- |
| k1 Vertikale Reihen (7 Pkt je Spalte) | 4,53 | 5,37 | **+0,84** |
| k5 Eckplatten (3/8 Pkt) | 5,40 | 7,06 | **+1,66** |
| k3 Mehrfarbige Felder | 4,91 | 4,39 | -0,52 |
| **k6 Spezialfelder (-3 je leerem Feld)** | **-9,67** | **-10,08** | **-0,42** |

**Lesart:** der Zuschlag zieht die Platte nach Zeile 6 und baut damit HOEHE. Hoehe zahlt auf
die vertikalen Reihen und auf die unteren Eckplatten (8 Punkte je Stueck) -- nicht auf die
Spezialfelder, deren Freischaltung offenbar an etwas anderem haengt. K5 wirkt also
geometrisch, nicht ueber den Posten, fuer den er gebaut wurde. Die Vorab-Lesart in par.9a
("haelt K5 den Kuppel-Bonus und hebt ihn weiter") trifft den Fall nicht: sie hat einen
Wirkungsweg unterstellt, den die Messung widerlegt.

**Die gepaarte Arena gegen die Kontrolle sagt dagegen: kein Unterschied.**

| Arena (2 x 80, Seed 20261014) | Arm | Kontrolle |
| --- | --- | --- |
| Siege Richtung first | 37 | 43 |
| Siege Richtung second | 34 | 46 |
| **gepoolt** | **71** | **89** (44,4 %) |
| volle Spalten je Richtung | 0,7375 / 0,7375 | 0,675 / 0,675 |
| belegte Spezialfelder je Partie | 1,31 / 1,21 | 1,09 / 1,10 |

Auf BLOCKEBENE gerechnet (32 Bloecke zu 5 Partien, der Seed faellt je Block): Siegquote des
Arms 0,444, 95%-KI **[0,366; 0,522]**; Punktedifferenz je Block **-1,19**, 95%-KI
**[-3,88; +1,50]**. Beide Intervalle schliessen den Nullpunkt ein. **Es gibt also weder
einen belegten Vorteil noch einen belegten Schaden im direkten Duell.**

**Der Widerspruch ist kein Messfehler, sondern ein bekanntes Muster.** Im Instrument spielt
der Arm gegen SICH SELBST: beide Seiten bauen hoch, und Hoehe zahlt sich in Punkten aus. Im
direkten Duell trifft er auf einen Gegner, der anders baut, und der Vorteil verschwindet.
Dieselbe Signatur wie beim Suchtiefen-Tausch ([[project_search_depth_column_tradeoff]]) und
bei der Gegner-Spezifitaet des Minimax-Knopfs.

**Verdikt: UNENTSCHIEDEN, Nutzer-Entscheid.** Die Vorab-Lesart in par.9a deckt den Fall
nicht ab -- sie sah "Bonus haelt und steigt" (Aufnahme) oder "Bonus bleibt gleich"
(Verwerfen) vor, nicht "anderer Posten steigt deutlich, Zielposten faellt leicht, Duell
neutral". Wer den Fall unter die alte Regel presst, entscheidet per Etikett statt per
Befund. Die Abwaegung steht in `PREREG_geometric_envelope.md` par.8.15e.

**Kosten:** Arena 2 x rund 1.060 s, Instrumente 2 x rund 24 min, gesamt 91 min.

### par.9d NACHMESSUNG: das negative Vorzeichen war Rauschen, K5 ist siegneutral (2026-09-07, 13:24-14:34)

Nutzer-Entscheid 2026-09-07 auf den unentschiedenen Befund in par.9c: *"K5 erst nachmessen,
dann entscheiden."* Gefahren mit `tools/gate_hull_form_spec.sh` (um eine freie
Kontroll-Spec erweitert), Arm `hullform2_k5w10` gegen Kontrolle `hullform2`, **dritter,
unabhaengiger Seed 20261016**, Deckel 200 Paare, @400, Blockgroesse 5. Das Skript hat vor
dem Lauf selbst belegt, dass sich die Specs in genau einem Feld unterscheiden
(`special_row6_w`).

| Messung | Arm : Kontrolle | Quote | Vorzeichentest |
| --- | --- | --- | --- |
| Arena Seed 20261014 (par.9c) | 71 : 89 | 0,444 | p 0,179 |
| **Gating Seed 20261016** | **172 : 168** | **0,506** | **p 0,913** |
| **gepoolt, 500 Partien** | **243 : 257** | **0,486** | **p 0,561** |

Gepoolte Siegquote mit 95%-KI **[0,442; 0,530]**, gepaarte Differenz des Gatings **+0,024**
mit KI [-0,188; +0,235]. SPRT-Entscheid nach 170 Paaren: H0 -- also **kein Beleg, dass der
Arm besser ist**, was bei einer Alternativhypothese von 0,65 und einer wahren Quote um 0,50
genau das erwartete Ergebnis ist und keinen Schaden belegt (Lesart vorab in
`PREREG_geometric_envelope.md` par.8.15d).

**Das negative Vorzeichen der ersten Messung hat sich NICHT repliziert.** 0,444 gegen 0,506
auf zwei Seeds ist genau die Streuungsgroesse, die fuer diese Kampagne gemessen ist
(5,75 Prozentpunkte bei n=400 fuer identische Konfiguration,
[[project_training_seed_variance]]). Wer nach der ersten Messung entschieden haette -- so
wie der Koordinator es um 11:30 im Chat getan hat --, haette Rauschen fuer einen Befund
gehalten. **Die Nachmessung war die richtige Entscheidung.**

### Damit steht der Befund vollstaendig

| Frage | Antwort | Beleg |
| --- | --- | --- |
| Hebt K5 die Spalten? | **Ja, deutlich** | Instrument 0,5725 -> 0,6900; Arena 0,675 -> 0,7375 in beiden Richtungen |
| Kostet K5 Siege? | **Nein** | 500 Partien, 0,486, KI [0,442; 0,530] |
| Wirkt K5 ueber die Spezialfelder? | **Nein** | Kriterium k6 leicht schlechter (-9,67 -> -10,08); die Punkte kommen aus vertikalen Reihen (+0,84) und Eckplatten (+1,66) |

**Nach der in par.8.15d vorab festgelegten Lesart ist das eine AUFNAHME** -- Spalten in
allen gemessenen Vergleichen ueber der Kontrolle, Siegquote nicht signifikant unter 50 %,
also ein Spalten-Knopf ohne Staerke-Anspruch. Die Regel war fuer die Huellenform
geschrieben; sie auf K5 anzuwenden ist konsequent, weil beide dieselbe Bauart sind.

**Der Vorbehalt, der mit in die Entscheidung gehoert:** der Wirkungsweg ist nicht der
gebaute. Wir wuerden einen Effekt drei Generationen lang einfrieren, dessen Ursache wir
nur geometrisch plausibel machen (Hoehe zahlt auf vertikale Reihen und untere Eckplatten),
nicht gemessen haben. Dasselbe gilt allerdings auch fuer die Huellenform. **Nutzer-Entscheid.**

**Laufzeit:** 170 Paare, rund 70 min, 125 s je Block, threads 10, exklusiv.
Artefakt `evaluations/artifacts/paired_gating_k5vshf2_s16.json`.

## Nachtrag 2026-09-11, 19:00: isolierte Wirkungsmessung der Kanaele 77/78 EINGETAKTET als v29-b02

Nutzer-Entscheid ("dann fahren wir die ablation als v29-b02"): Rezept v29-b01 mit den
Planes-Kanaelen 77 (Spezialfeld-Ertrag) und 78 (Abstand zur Ausloesung) auf Null, Tor 1 gegen
v29-b01, Leserichtung und Zusatzkennzahlen in `PREREG_v29_window.md` par.6. Damit bekommt der
seit 2026-08-29 offene Punkt (2) des Kopfbereichs (kein 77-gegen-79-A/B) seine Messung; par.4c
bleibt ungebaut und haengt am Ausgang. Anlass der Wiedervorlage: Audit-Querlesung 2026-09-11
und der Spezialfeld-Posten in Tor 1 v28 (-9,73 gegen -10,61 Punkte je Partie, 160 von 400
Brettern, `PREREG_v28_window.md` par.10).
