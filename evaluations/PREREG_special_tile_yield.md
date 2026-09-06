<!-- STATUS: OFFEN | Frage: Die Spezialfliesen sind der groesste unabgeholte Posten auf dem Brett; ihr Wert steigt dort, wo sie am schwersten erreichbar sind. Laesst sich das heben, und an welchem Hebel? | Beleg: Kanaele 77/78 gebaut (par.4a, e91cd34, in jedem v22-b-Modell aktiv), Wirkung nie isoliert gemessen. Neumessung par.7: Posten LEBT -- auch der Lehrer laesst 81 Prozent der unteren Spezialfelder liegen, Netz ueberall etwas schlechter. Vermeidungs-Hebel widerlegt (par.4/4b). Hebel gehoert in die Gelaender-/Allokations-Familie. par.8 (2026-09-05, 19 Server-Partien): Kuppel-Bonus Mensch 8,9 gegen Netz 1,6 je Partie, Endwertung 19,7 gegen 4,2 -- der gesamte Abstand zum Menschen; Platzierungspunkte gleich. Sicht 744 hebt den Kuppel-Bonus NICHT (v24-Abnahmen 3,5-4,3 je Partie gegen Mensch 8,9; par.9). Nutzer-Regel 2026-09-06: EINE Spezialfliese in Reihe 6 je Partie -- als Baustein K5 registriert (par.9), Bau nach den K3-Armen. -->

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

