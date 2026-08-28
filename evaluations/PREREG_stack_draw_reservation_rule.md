<!-- STATUS: OFFEN | Frage: Die Blindziehung ist ein exakt loesbares Stoppproblem. Eine Stopp-Regel IST gebaut (self_play.rs:500-545, Default-Pfad) -- ist sie die richtige? | Beleg: NEIN, sie zieht ZU OFT (par.5b): optimale Tiefe ist ueberall 1, die gebaute Regel zieht bei negativem Brettniveau 9-11 mal. Ursache ist der Einheitenbruch (par.1c), nicht der Optionswert-Fehler. Knopf gebaut, Default AUS (par.5c); Abnahme n=200 zeigt KEINEN Staerkeunterschied in beide Richtungen (par.5d). Wiedervorlage nach v22 nur unter zwei Bedingungen (par.5e). -->

# PREREG: Reservationswert-Regel fuer die Blindziehung (`stack_draw_reservation_rule`)

Stand **2026-08-25**. **GEMESSEN sind par.4b, par.4c, par.5b, par.6b, par.6c und par.6d**;
par.1c und par.2 sind am Code geprueft. **NICHT gebaut** ist jeder Eingriff --
par.5 (SOLL-Seite) und par.6 (Stufe 2) stehen weiter in Plan-Zeitform.
Am Code geaendert wurde nur ein `#[cfg(test)]`-Modul am Ende von
`engine/src/self_play.rs` (die Sonde aus par.6b); der Default-Pfad ist
unberuehrt.

## par.1 Die Frage

Aktion A erlaubt, gegen 1 Punkt je Ziehung beliebig oft verdeckt vom
Kuppelstapel zu ziehen, am Ende genau eine der gezogenen Platten zu behalten
und den Rest zurueckzulegen. Das ist kein Ermessensspielraum, sondern ein
**Stoppproblem mit bekannter Loesung**: sequenzielle Suche mit Rueckgriff und
konstanten Suchkosten (oekonomisch als "Pandora's Box" bekannt, Weitzman 1979;
Herleitung und Quellen in `evaluations/RESEARCH_heuristic_methodology_external_2026-08-25.md` par.3).

Die optimale Politik ist keine Suche, sondern eine Schwelle:

> Zieh weiter, solange `E[max(V_next − V_hand, 0)] > c`.
> `c` = 1 Punkt. `V_hand` = der Wert der besten Option, die man ohne weitere
> Kosten schon hat.

**Diese Prereg fragt zuerst diagnostisch**, nicht baulich: weicht das
tatsaechliche Ziehverhalten des Champions von dieser Schwelle ab, und in
welche Richtung? Erst wenn eine Luecke belegt ist, wird ueber einen Eingriff
entschieden.

### par.1c KORREKTUR am selben Tag: eine Stopp-Regel IST gebaut

Die erste Fassung dieser Prereg schrieb "nichts gebaut". Das war falsch und
ist der Grund, warum par.5 unten anders zugeschnitten ist als geplant.
`self_play.rs:500-545` `resolve_and_apply_stack_draw` loest den ganzen
Stapelzug in EINEM Zug auf -- Pflicht-Peek, dann eine eigene Schleife
"weiterziehen oder aufhoeren", dann Platte, Slot und Rotation. Aufgerufen wird
sie in `apply_chosen_action` (`self_play.rs:620`) auf dem DEFAULT-Pfad
(`MOSAIC_STACK_DRAW_RESEARCH` ist aus), also in jedem Self-Play und jeder
Arena-Partie.

Ihre Schleifenbedingung, zusammengezogen (`cost_so_far` kuerzt sich weg, der
versunkene Aufwand verzerrt also nicht):

> weiterziehen, solange `avg_remaining_type_value(state) − 1 > max(bisher
> gezogene Platten)`

**Drei Mangel, alle am Code geprueft, alle mit bekannter Richtung:**

1. **Niveau statt Verbesserung -- stoppt beweisbar zu frueh.** Die gebaute
   Bedingung ist `E[V_next] − c > V_hand`. Mit Rueckgriff lautet die richtige
   `E[max(V_next − V_hand, 0)] > c`. Wegen
   `E[max(V_next − V_hand, 0)] >= E[V_next] − V_hand` ist die gebaute
   Bedingung strikt SCHAERFER; die Differenz ist genau
   `E[max(V_hand − V_next, 0)]`, also der Wert des Rueckgriffs (man behaelt ja
   die bessere Platte, das Risiko nach unten ist abgeschnitten). Die Regel
   verschenkt diesen Optionswert vollstaendig und zieht deshalb systematisch
   zu selten.
2. **Das gratis sichtbare Typ-Signal wird nicht benutzt.**
   `avg_remaining_type_value` (`self_play.rs:480-492`) mittelt ueber den
   GESAMTEN Restpool, obwohl `dome_tile_pool.first()` die naechste Platte ist
   und ihr Typ vor der Zahlung feststeht (par.2). Statt eines bedingten
   Erwartungswerts steht dort ein unbedingter.
3. **Einheitenbruch gegen die Kosten.** Der Wertterm ist
   `bonus_points + Zahl der Wild-Zellen`, in `best_eval_for_tile` zusaetzlich
   plus `scoring_progress`. `bonus_points` ist laut `engine/src/dome.rs:124`
   ausdruecklich ein DISKRIMINATOR (Special = 3, Wild = 0), kein Punktwert --
   der wirkliche Spezialfeld-Wert ist die Rasterreihe 1..6 und faellt erst bei
   Freischaltung an. Eine Special-Platte zaehlt hier also pauschal 3, eine
   Wild-Platte 1, und diese Summe wird gegen 1 PUNKT Ziehkosten gestellt.
   Ob die 3 je als Wertnaeherung gemeint war, steht nirgends; dokumentiert ist
   sie als Unterscheidungsmerkmal.

Damit verschiebt sich die Frage dieser Prereg von "gibt es eine Regel" zu
**"ist die gebaute Regel die richtige, und was kostet ihr Fehler"**. Mangel 1
und 3 wirken gegenlaeufig: 1 laesst zu selten ziehen, 3 kann je nach
Plattentyp in beide Richtungen irren. Die Nettorichtung ist damit NICHT
vorhersagbar und muss gemessen werden.

### par.1b Abgrenzung gegen zwei bestehende Preregs (wichtig, sonst Doppelarbeit)

Am Kuppelstapel liegen drei verschiedene Fragen, die leicht verwechselt werden:

| Prereg | Frage | Ebene | Status |
| --- | --- | --- | --- |
| `PREREG_chance_nodes.md` Teil B1 | Soll die SUCHE den Peek als echten Zufallsknoten mit gewichteter Rueckgabe bewerten (`MOSAIC_STACK_DRAW_CHANCE`)? | Suche | OFFEN, geparkt, nie gebaut |
| `PREREG_stack_top_feature.md` | Soll das NETZ die sichtbare oberste Rueckseite als Merkmal bekommen? | Merkmale | OFFEN, nichts gebaut |
| **diese hier** | Wie oft ZIEHEN ist richtig, und tut der Champion das? | Politik / Diagnose | OFFEN |

Der Unterschied ist nicht kosmetisch. B1 verbessert die Bewertung EINES
Peek-Knotens im Baum; diese Prereg fragt nach der **Anzahl** der Ziehungen,
und darauf gibt es eine geschlossene Antwort, die ohne Baum auskommt. Beide
koennen sich ergaenzen, keiner ersetzt den anderen. Wer B1 baut, sollte diese
Prereg kennen, weil die Schwelle ein billiger Pruefstein fuer die Ergebnisse
von B1 waere.

## par.2 Die Voraussetzungen der Regel, am Code geprueft (2026-08-25)

Die Regel gilt nur, wenn das Spiel ihre vier Annahmen erfuellt. Alle vier
sind nachgesehen, keine ist angenommen:

| Annahme | Befund | Pruefstelle |
| --- | --- | --- |
| Kosten je Ziehung konstant | `apply_paid_cost(-1)`, im Kommentar ausdruecklich ein KAUF, keine Strafe; bei Punktestand 0 gratis | `engine/src/game.rs:182` |
| Rueckgriff auf alle bisher Gezogenen | gezogene Platten sammeln sich in `pending_stack_draw`; `validate_draw_from_stack` akzeptiert JEDE `chosen_id` daraus | `engine/src/game.rs:185`, `:201` |
| Endlicher, abzaehlbarer Vorrat | Ziehung nimmt vorne aus `dome_tile_pool`; Restgroesse offen | `engine/src/game.rs:183`, `engine/src/serialize.rs:265` |
| Typ der naechsten Platte gratis sichtbar | `dome_stack_top_type` meldet Wild oder Special VOR der Zahlung | `engine/src/serialize.rs:270` |

Die vierte Zeile macht die Aufgabe **leichter** als das Lehrbuchproblem: dort
zahlt man, um ueberhaupt etwas zu erfahren, hier ist das Typ-Signal gratis.
Es gibt daher nicht einen Reservationswert, sondern zwei bedingte (Wild und
Special); die Restunsicherheit steckt nur noch in der Farbanordnung.

**Wichtige Einschraenkung zur vierten Zeile:** `dome_stack_top_type` steht in
der SERIALISIERUNG, nicht im Merkmalsvektor. Ein handgeschriebener Bewerter
liest es, das NETZ sieht es nicht -- `features.rs` und `neural_net.py` lesen
es nirgends (unabhaengig geprueft und bereits registriert in
`PREREG_stack_top_feature.md` par.3, in dieser Sitzung an `features.rs`
nachvollzogen: nur `dome_wild_remaining_frac` und `dome_stack_count` sind da).
Die Regel ist damit als handgeschriebene Politik oder als Lehrer sofort
anwendbar, als Erwartung an das heutige Netz dagegen nicht.

### par.2b Korrektur an einer benachbarten Prereg

`PREREG_chance_nodes.md` behauptet an der Stelle zu Teil C: *"Das Netz hat die
noetigen Merkmale: `dome_stack_top_type` ... und `dome_wild_remaining_frac`"*.
Der erste Teil ist heute falsch. Das Teil-C-ERGEBNIS bleibt davon unberuehrt
(es bedingt auf die aktive Wertungsplatte, und die steht als One-hot im
Vektor), aber der Satz wuerde den naechsten Leser in die Irre fuehren. Ein
datierter Korrekturhinweis ist dort eingetragen.

## par.3 Was `V` ist, und warum die Einheit ueber die Regel entscheidet

`c` ist 1 PUNKT. Ein `V` in einer anderen Einheit macht die Schwelle zu einer
Zahl ohne Bedeutung -- dieselbe Fehlerklasse wie die Floor-Shaping-Altlast.

* **Falsch waere** `column_build::cell_value` (`engine/src/column_build.rs:880`):
  Wild 3,0 / Special 2,0 / passende Farbe 2,5 / leere Reihe 1,5 -- reine
  Praeferenz-Einheiten, nie gegen Punkte geeicht.
* **Richtig ist** `plate_builder::points_map` (`engine/src/plate_builder.rs:1039`,
  oeffentlich `expected_points_map`): je Zelle
  `scoring_progress(&probe, ids) − basis + bonus`, mit Spezialfliesen-
  Sofortwert und Linienpunkten aus `round_end::score_placed_tile`.
  Durchgehend Punkte, ueber die Anker-Formel selbst statt ueber einen Nachbau.

`V(Platte)` ist das Maximum ueber Slot und Rotation. Die Parallelsitzung hat
dafuer `plate_builder::best_plate_value(player, tile, zellen, karte, wert)`
gebaut (roher Maximalwert, Legalitaet nur geometrisch, Zellbewertung als
Funktionszeiger).

**`V_hand` ist nicht die beste gezogene Platte allein**, sondern das Maximum
ueber die gezogenen Platten UND die beste LEGAL platzierbare Platte im offenen
Display. Die ist gratis zu haben und damit die eigentliche Ausstiegsoption.
Die Display-Legalitaet ist dabei gegen `validate_dome_move` zu pruefen, weil
`best_plate_value` nur geometrisch prueft.

## par.4 Zwei Skalen-Fallen, vorab benannt

1. **Additivitaet.** Die Summe der Kartenwerte ueber die Zellen einer
   (Slot, Rotation)-Kombination unterstellt Unabhaengigkeit; `scoring_progress`
   ist nicht additiv (zwei Zellen, die gemeinsam eine Spalte schliessen, sind
   zusammen mehr wert, der gemeinsame Anteil wird doppelt vergeben). Der
   Irrtum geht nach OBEN, also in die Richtung, in der die Regel zu oft zieht.
   **Behandlung:** die exakte Variante verwenden (die Zellen auf einem
   Probe-Brett GEMEINSAM belegen, EINE `scoring_progress`-Differenz nehmen).
2. **Potenzial gegen Realisierung.** Eine Platte FUELLT keine Zelle, sie macht
   sie bedienbar; die Steine muessen noch gedraftet und gekachelt werden. Ein
   `V` aus reinen Potenzialpunkten laesst die Regel zu oft ziehen.
   **Behandlung:** Abschlag aus gemessenen Groessen statt aus einer Setzung --
   `docs/domain_knowledge.md:39-46` gibt Abschluesse je Reihe UND Runde. Fuer
   eine Entscheidung in Runde k waere der Erwartungswert der Restabschluesse
   einer Reihe die Summe ueber die Runden k..5, und die Chance einer
   BESTIMMTEN freien Zelle in Rasterreihe r in erster Naeherung dieser Wert
   geteilt durch die Zahl der noch freien Zellen dieser Reihe.
   Groessenordnung: Reihe 6 ueber die Runden 3-5 zusammen 0,57 Abschluesse,
   Reihe 1 im selben Fenster 2,99.

**Vorbehalt gegen die eigene Zahl, vorab registriert:** die Durchsatztabelle
ist das IST eines v20-Self-Play-Korpus MIT Wurzelrauschen, also das Verhalten
eines Spielers, der lange Reihen gerade nicht vollendet. Sie als
Realisierungswahrscheinlichkeit zu nehmen schreibt diese Schwaeche fort
(Hausregel "nie auf plattenblindes Normalspiel eichen"). Fuer die erste
Fassung ist sie die beste verfuegbare Groesse; sie gehoert neu gemessen,
sobald ein Champion die Spalten tatsaechlich schliesst.

## par.4b IST-Seite, bereits gemessen (2026-08-25)

Reines Pickle-Lesen, kein Netz, keine Suche. Korpus `selfplay_v20wdlsw_*`,
60 Dateien = **600 Partien**, Einheit Partie ueber beide Bretter, CI 95 %.

| Groesse | je Partie |
| --- | --- |
| Entscheidungen mit legalem Peek | 45,96 ± 0,52 |
| davon TOP-Aktion = Peek | 6,69 ± 0,30 |
| Policy-Masse auf Peek, wenn legal | 0,1371 ± 0,0052 |
| Platte aus dem Display gewaehlt | 12,70 ± 0,30 |

Verteilung der Peek-Gelegenheiten ueber die Runden 1-4: 6467 / 6479 / 7219 /
7413 -- gleichmaessig. Die TOP-Wahl faellt dagegen stark ab: 1490 / 1180 /
878 / 466. **Der Champion zieht also vor allem frueh**, obwohl die
Gelegenheiten spaeter eher zunehmen.

**Was in diesem Korpus NICHT messbar ist, und warum** (wichtig, sonst wird ein
Artefakt als Befund gelesen): Zwischenzustaende einer laufenden Ziehserie
kommen nicht vor -- `pending_stack_draw` ist in allen 97.970 Datensaetzen
leer, und die Aktion `choose_draw_stack_slot` taucht in keiner Policy auf.
Das ist kein Fehler der Auswertung, sondern die direkte Signatur der
Sammelaufloesung aus par.1c: `resolve_and_apply_stack_draw` erledigt Peek,
Wahl, Slot und Rotation ohne Zwischenentscheidung. **Die tatsaechliche
Ziehtiefe (wie viele Platten je Serie) steht damit in keinem vorhandenen
Korpus** und braucht entweder ein Log oder einen Lauf mit
`MOSAIC_STACK_DRAW_RESEARCH=1`.

Zweite Folge derselben Sammelaufloesung, im Code selbst dokumentiert
(`self_play.rs:591-601`): die Suche bewertet an der Wurzel EINEN Peek, danach
zieht die Schleife bis zu 20-mal weiter und waehlt selbst. *"KOSTEN und
ERGEBNIS weichen beide vom Bewerteten ab, und dadurch ist auch der Vergleich
der Wurzelaktion Ziehen gegen die anderen Wurzelzuege auf falscher
Grundlage getroffen."* Die 6,69 TOP-Wahlen je Partie stehen also auf einer
Bewertung, die nicht das bewertet, was ausgefuehrt wird.

## par.4c ERGEBNIS Schritt 1 (2026-08-25): die Regel laeuft bei Platte 6 das Konto leer

**Vorhergesagt aus dem Code** (par.1c, Mangel 3/4): `best_eval_for_tile`
liefert ein ABSOLUTES Brettniveau (`scoring_progress`, `scoring.rs:160` --
Spalten bis 42, Rand bis 20, und **Kriterium 6 als einziges NEGATIV**), die Weiterzieh-Seite
`avg_remaining_type_value` dagegen einen Typmittelwert in [1, 3].

> **KORREKTUR 2026-08-25, noch am selben Tag.** Eine fruehere Fassung dieses
> Absatzes schrieb "Kriterium 6 bis −27" und an anderer Stelle, der Term
> "starte bei −27". Das ist falsch. `special_empty` zaehlt nur Spezialfelder
> auf **bereits gelegten** Platten (`collect_spaces(player, SpaceType::Special)`,
> `scoring.rs:921-923`) -- in Runde 1 sind hoechstens drei Platten gelegt
> (eine Startplatte plus zwei), der Term liegt dort also bei hoechstens −9,
> und −27 ist eine theoretische Obergrenze fuer ein spaetes Brett mit neun
> gelegten Special-Platten, von denen keine gefuellt ist.
> **Der Mechanismus bleibt, die Begruendung wird eine andere**: frueh sind die
> POSITIVEN Kriterien nahe null (Reihen-, Spalten-, Randfuellung fangen bei 0
> an), also kippt schon ein kleiner negativer Beitrag die Summe unter null.
> Spaeter ueberwiegen die positiven Terme, und die Regel stoppt wieder sofort.
> Welche Groesse tatsaechlich zur Ziehzeit anliegt, ist NICHT gemessen -- genau
> das beantwortet der konstruierte Test in par.6b.

Erwartung:
ohne Platte 6 bricht die Schleife nach dem Pflicht-Peek ab; MIT Platte 6 ist
die Stopp-Seite frueh stark negativ, die Regel zieht weiter.

**Beobachter** (kein Netz, keine Suche): waehrend der Drafting-Phase aendert
sich der Punktestand NUR durch Blindziehungen -- `apply_paid_cost` hat genau
EINE Aufrufstelle im ganzen Code (`engine/src/game.rs:182`, per Grep geprueft).
Ein Rueckgang um k zwischen zwei Datensaetzen derselben Runde ist also eine
Ziehserie der Tiefe k. Korpus `selfplay_v20wdlsw_*`, 60 Dateien = 600 Partien
(235 mit Platte 6, 365 ohne -- erwartet waeren 37,5 %, gemessen 39,2 %,
passt). Einheit Partie ueber beide Bretter, CI 95 %.

| je Partie | mit Platte 6 | ohne |
| --- | --- | --- |
| **Punkte fuer Blindziehungen** | **11,22 ± 0,42** | **3,93 ± 0,15** |
| sichtbare Ziehserien | 3,60 ± 0,16 | 3,50 ± 0,11 |
| Peek-Gelegenheiten | 48,22 ± 0,83 | 44,51 ± 0,63 |

**Die Zahl der Serien ist praktisch gleich -- die TIEFE ist es nicht.**

| Ziehtiefe | 1 | 2 | 3 | 4 | 5 | 6-9 |
| --- | --- | --- | --- | --- | --- | --- |
| mit Platte 6 | 286 | 92 | 98 | 58 | **273** | 38 |
| ohne | **1175** | 64 | 25 | 9 | 4 | 0 |

Ohne Platte 6 haben 92 % der Serien die Tiefe 1, ab Runde 3 sind es 100 %
(275/275 und 207/207) -- genau das vorhergesagte "bricht nach dem Pflicht-Peek
ab".

**Der Gipfel bei genau 5 ist kein Zufall, sondern der Kontostand.** Der
Startwert ist 5 Punkte (`engine_manual.md` §2). In Runde 1 mit Platte 6 haben
223 von 402 Serien die Tiefe 5: die Regel zieht, bis nichts mehr da ist. Ab da
sind weitere Ziehungen gratis und fuer diesen Beobachter unsichtbar -- **die
wahren Tiefen sind also UNTERGRENZEN**. Direkt gezaehlt: **59,8 % der Serien
mit Platte 6 enden bei Punktestand 0**, ohne Platte 6 nur 6,0 %. Umgekehrt
sind in Runde 4 mit Platte 6 alle 134 Serien wieder Tiefe 1 -- bis dahin sind
Spezialfelder gefuellt, `scoring_progress` ist nicht mehr stark negativ, und
die Regel stoppt sofort. Das Verhalten folgt dem vorhergesagten Mechanismus
ueber alle vier Runden.

### Zwei Folgen

1. **Groessenordnung.** 11,22 Punkte je Partie ueber beide Bretter sind rund
   5,6 Punkte je Spieler, allein an dieser einen Regel, in 39 % aller Partien.
   Zum Vergleich: das Score-Niveau liegt bei ~40-48 je Spieler. Ob der Kauf
   sich lohnt, ist damit NICHT beantwortet -- eine Wild-Platte kann mehr wert
   sein als 5 Punkte. Beantwortet ist nur, dass die Entscheidung nicht auf
   einer sauberen Rechnung beruht, sondern auf einem Skalenbruch.
2. **Konfundierungs-Verdacht fuer `PREREG_chance_nodes.md` Teil C**
   `[HERLEITUNG, ungeprueft]`. Dort ist eine erhoehte Ziehquote bei Platte 6
   gemessen (Policy-Masse +0,079) und als GELERNTE Interaktion registriert.
   Dieselbe Korrelation entstuende aber auch reinmechanisch: der Resolver
   zieht bei Platte 6 tiefer, das praegt Kosten und Ergebnis der Partien und
   damit die Labels, aus denen das Netz lernt. Der Teil-C-Befund ist damit
   nicht widerlegt, aber er hat einen unausgeschlossenen Alternativerklaerer.

## par.6b Netzfreier Gegentest (Nutzer-Auftrag 2026-08-25, GESCHRIEBEN, NICHT GELAUFEN)

**Anlass ist ein berechtigter Nutzer-Einwand** zu par.4c: dort ist an Partien
EINES (schwachen) Netzes gemessen und daraus allgemein geschlossen worden.
Die Trennung, die dabei gefehlt hat:

* **Nicht vom Netz**: die Ziehtiefe ist ueberhaupt keine Netz-Entscheidung.
  `resolve_and_apply_stack_draw` benutzt nur `best_eval_for_tile` und
  `avg_remaining_type_value`, beide handgeschrieben, kein Netzaufruf. Das Netz
  waehlt nur, OB ein Stapelzug beginnt. Auch der Skalenbruch selbst steht im
  Code.
* **Sehr wohl vom Netz**: die Zustaende, an denen gezogen wird. Damit haengt
  der BETRAG (11,22 Punkte je Partie) am Regime und ist keine Konstante.

**Stabilitaetspruefung, bereits gefahren** (je 30 Dateien = 300 Partien je
Korpus, gleiches Verfahren wie par.4c):

| Korpus | Tiefe-1-Anteil ohne Platte 6 | Serien auf 0 mit Platte 6 | Punkte/Partie mit Platte 6 |
| --- | --- | --- | --- |
| v18 | 91,6 % | 65,9 % | 9,54 |
| v19wdl | 91,9 % | 65,3 % | 10,41 |
| v19wdlsw | 94,7 % | 64,2 % | 11,02 |
| v20wdl | 93,0 % | 58,3 % | 10,17 |
| v20wdlsw | 91,6 % | 57,8 % | 11,36 |

Das Muster ist ueber fuenf Generationen stabil, haengt also nicht an einem
einzelnen Netz. Die Drift der Spalte "auf 0" von 65,9 % auf 57,8 % zeigt in
die vom Mechanismus vorhergesagte Richtung: staerkere Netze fuellen
Spezialfelder frueher, das Brettniveau ist frueher weniger negativ, der
Aderlass kleiner. **Alle fuenf Korpora stammen jedoch aus derselben Linie und
aus plattenblindem Spiel** -- fuer einen wirklich starken Spieler bleibt der
Betrag offen.

**Der Test, der das Netz ganz herausnimmt.** Geschrieben und bereitgelegt als
`stack_draw_depth_probe.rs` (Anhang fuer das Dateiende von
`engine/src/self_play.rs`, `#[cfg(test)]`-Modul, kein Eingriff in
Bestandscode). Er konstruiert Bretter statt sie zu spielen und variiert genau
zwei Groessen: ob Kriterium 6 in `scoring_tile_ids` steht, und wie viele
Spezialfelder gelegt bzw. schon gefuellt sind. Zwei Dinge kann er, die der
Korpus nicht kann:

1. **Wahre Tiefe statt Untergrenze.** Der Punktestand startet bei 60, der
   Null-Boden schneidet also nichts ab.
2. **Brettniveau als Spalte.** `scoring_progress` wird je Fall mit ausgegeben,
   die Erklaerung wird damit pruefbar statt plausibel.

Ausgegeben wird eine Tabelle (Platten gelegt, leere Spezialfelder, Niveau,
Tiefe mit Platte 6, Tiefe ohne). Die Zusicherungen sind bewusst schwach
gehalten -- die Tabelle ist das Ergebnis, nicht der Assert.

**Plattenwahl** (Nutzer-Freigabe 2026-08-25: hier frei setzbar, die
Fokus-Regel "nur k1" gilt fuer diesen Diagnose-Test nicht): die beiden Arme
unterscheiden sich in GENAU EINER Groesse, naemlich welche Seite des Paares
(6, 3) im Spiel ist -- **[0, 4, 6] gegen [0, 4, 3]**. Das ist zugleich die
Variation, die das echte Spiel selbst vornimmt.

> **Fehler beim Bau, hier festgehalten, weil er fast durchgerutscht waere:**
> der erste Entwurf verglich [0, 4, 6] gegen **[0, 4, 1]**. Das ist ein
> UNGUELTIGER Plattensatz -- (4, 1) ist selbst ein Ausschlusspaar
> (`MUTUALLY_EXCLUSIVE_PAIRS`, `scoring.rs:60-65`: (0,7), (6,3), (4,1),
> (2,5)). Der Kontrollarm haette eine Konstellation gemessen, die im Spiel
> nicht vorkommt. Der Test prueft die Gueltigkeit beider Saetze jetzt selbst
> ueber `scoring::exclusion_partner`, statt sie anzunehmen.

### par.6c Drittes Regime, ohne Netz-Selbstspiel: die Mensch-gegen-KI-Logs

Waehrend der Wartezeit gefahren, weil es weder Maschine noch Kompilat
braucht. Die Engine protokolliert JEDE Blindziehung mitsamt ihrer laufenden
Nummer (`game.rs:190-192`: *"{n}. Kachel vom Stapel gezogen (Rueckseite:
{typ}) −1 Pkt"*). In `static/log/` liegen 10 Partien Mensch gegen KI -- ein
voellig anderes Regime als das Self-Play: kein Wurzelrauschen, ein starker
menschlicher Gegner (er gewinnt 8 von 9, `STATUS.md`), und die Tiefe steht
**direkt im Log** statt ueber den Punktestand erschlossen.

| Seite | Serien | Tiefe-1-Anteil | Verteilung |
| --- | --- | --- | --- |
| KI | 25 | **100 %** | {1: 25} |
| Mensch | 20 | **95 %** | {1: 19, 2: 1} |

> **KORREKTUR 2026-08-25 (Nutzer-Hinweis, die Logs noch einmal anzusehen).**
> Die erste Fassung nannte fuer den Menschen "14 Serien, 100 %". Das war ein
> PARSING-Fehler: in 3 der 10 Partien heisst der menschliche Spieler laut
> Log-Kopf **"Spielerin"** statt "Spieler 1", mein Muster hat diese drei
> Partien fuer die Menschen-Seite komplett uebersehen. Korrigiert, indem der
> Name je Partie aus dem Log-Kopf gelesen wird (`players`/`ai_player`) statt
> fest verdrahtet. Die KI-Seite war nie betroffen. Am Befund aendert sich
> nichts Wesentliches -- der Mensch zieht in 19 von 20 Serien genau einmal --,
> aber die Zahl stimmt jetzt.

**Das bestaetigt die eine Haelfte und sagt zur anderen nichts.** Ohne
Kriterium 6 zieht die Regel genau einmal -- hier in 25 von 25 Serien, im
Korpus 92-95 %. Das haelt ueber drei Regime (Self-Play mit Rauschen, fuenf
Generationen, Mensch-gegen-KI). Der Mensch tut in denselben Partien dasselbe
(14 von 14), das Verhalten ist ohne Platte 6 also nicht offensichtlich falsch.

**Zur Platte-6-Haelfte koennen diese Logs grundsaetzlich nichts sagen** --
nicht durch Zufall, sondern durch Anlage. **Nutzer-Auskunft 2026-08-25: das
waren bewusst nur Partien mit vertikalen Wertungsplatten.** Nachgezaehlt an
den Log-Koepfen: Kriterium 1 (vertikale Reihen) liegt in ALLEN 10 Partien --
[3,5,1], [0,1,2], [7,3,1], [1,5,3], [7,3,1], [7,1,2], [3,1,2], [1,3,7],
[1,5,7], [7,2,1]. Das ist die Fokus-Regel "NUR k1" (`STATUS.md`), kein Los.

Verschaerfend kommt die Paarstruktur dazu: die Ausschlusspaare sind in
Code-Indizes 0-7, 1-4, 2-5 und **3-6**. In 6 der 10 Partien liegt Kriterium 3
(mehrfarbige Felder), womit Kriterium 6 dort **strukturell unmoeglich** war;
in den uebrigen vier war das Paar 3/6 gar nicht im Spiel.

**Eine fruehere Fassung dieses Absatzes rechnete stattdessen vor, 0 von 10
sei unter zufaelliger Auswahl ein Ein-Prozent-Ereignis.** Die Rechnung war
zwar als ungeprueft markiert, aber sie unterstellte eine Losung, wo eine
Setzung vorlag -- und eine Wahrscheinlichkeitsaussage ueber ein gesetztes
Design ist gegenstandslos, nicht bloss unsicher.

Der teure Arm der Regel bleibt in diesem Regime also unbeobachtet, und der
konstruierte Test aus par.6b bleibt noetig.

### ERGEBNIS par.6b (2026-08-25, gelaufen)

Angehaengt an `engine/src/self_play.rs` als
`stack_draw_depth_probe::ziehtiefe_haengt_an_wertungsplatte_6_und_am_brettniveau`,
`cargo test --release --lib`, Laufzeit 0,04 s. Kein Netz, kein Korpus, kein
Wurzelrauschen.

| Platten gelegt | Spezialfelder leer | `scoring_progress` | Tiefe MIT Krit. 6 | Tiefe OHNE |
| --- | --- | --- | --- | --- |
| 0 | 0 | 0,00 | 2 | 1 |
| 2 | 2 | **−6,00** | **13** | 1 |
| 4 | 4 | **−12,00** | **11** | 1 |
| 4 | 2 | **−4,83** | **11** | 1 |
| 4 | 0 | **+3,50** | **1** | 1 |
| 6 | 0 | +4,83 | 1 | 1 |
| 8 | 0 | +4,83 | 1 | 1 |

**Der Mechanismus ist damit belegt, und zwar praeziser als vermutet: nicht die
Platte entscheidet, sondern das VORZEICHEN des Brettniveaus.**

* Ohne Kriterium 6 ist die Tiefe in JEDEM Fall 1 -- unabhaengig davon, wie das
  Brett aussieht. Das deckt sich mit allen drei Beobachtungsregimen
  (Self-Play 92-95 %, Mensch-gegen-KI 25/25).
* Mit Kriterium 6 kippt das Verhalten exakt am Nulldurchgang: bei −6,00,
  −12,00 und −4,83 zieht die Regel 13, 11 und 11 mal; sobald dieselbe
  Brett-Fuellung ein positives Niveau ergibt (+3,50 bei vier Platten ohne
  leere Spezialfelder), faellt die Tiefe auf 1. Der Umschlag liegt zwischen
  −4,83 und +3,50, also am Vorzeichen -- nicht an der Zahl der Platten, nicht
  an der Zahl der Spezialfelder.
* Die Zeile "0 Platten, Niveau 0,00, Tiefe 2" ist der Grenzfall und passt ins
  Bild.

**Damit ist auch die Untergrenzen-Frage aus par.4c beantwortet.** Im Korpus
brach die sichtbare Tiefe bei 5 ab, weil der Punktestand bei 5 startet und
Ziehungen bei 0 gratis werden. Hier steht das Konto auf 60 -- und die Regel
zieht **11 bis 13 mal**, also 11 bis 13 Punkte fuer EINEN Stapelzug. Die
Korpuszahlen waren nicht nur formal Untergrenzen, sie waren es deutlich; im
echten Spiel wird der Aderlass allein durch die Kontogrenze gestoppt, nicht
durch die Regel.

**Was der Test NICHT sagt**: ob 11 Ziehungen an dieser Stelle falsch waren.
Dazu braucht es `V` in Punkten (par.3) und den Realisierungsabschlag (par.4).
Belegt ist der Mechanismus und seine Groessenordnung, nicht das Urteil.

### par.6d Stellt der Spaltenbau die Pathologie von selbst ab? NEIN (2026-08-25)

**Nutzer-Frage**, nachdem der Korpus-Einwand geklaert war: mein Messkorpus
stammt von einem Spieler, der keine Spalten schliesst -- wuerde ein
spaltenkompetenter Spieler das Brettniveau schnell genug ins Positive heben,
um die tiefen Ziehungen von selbst zu beenden? Die Vermutung lag nahe, weil
Spezialfelder sich durch das Fuellen der drei Nachbarzellen freischalten.

Gemessen im selben netzfreien Aufbau, zwei Arme mit identischem Brett und
identischem Spezialfeld-Defizit, die sich NUR darin unterscheiden, ob
Spaltenfortschritt belohnt wird: **[0, 1, 6] gegen [0, 4, 6]** (Kriterium 1 =
vertikale Reihen, Gewicht 7, quadratisch; Kriterium 4 = aeussere Felder,
Gewicht 1, linear). `special_empty` fest auf 2, Platten ohne Special-Vorzug
gelegt, variiert wird nur der Spalten-Fuellstand:

| Spalte gefuellt | Spez. leer | Niveau k1 | Tiefe k1 | Niveau k4 | Tiefe k4 |
| --- | --- | --- | --- | --- | --- |
| 0 | 2 | −5,72 | 9 | −5,92 | 9 |
| 2 | 2 | −4,61 | 9 | −3,58 | 9 |
| 3 | 2 | −3,56 | 9 | −2,50 | 9 |
| 4 | 2 | −2,11 | 9 | −1,42 | 9 |

**Die Antwort ist nein, und der Grund ist die Kurvenform.** Kriterium 1 zahlt
`7 * (f/6)^2`, also QUADRATISCH im Fuellstand; das Spezialfeld-Defizit kostet
`-3` je Feld, also LINEAR und sofort. Partieller Spaltenbau hebt das Niveau
daher kaum: vier von sechs Zellen bringen 3,11 Punkte. Der lineare Rand-Arm
liegt in jeder Zeile HOEHER als der Spalten-Arm -- fuer Teilfuellungen ist
"aeussere Felder" die staerkere Gegenkraft als "vertikale Reihen".

Und die Rechnung fuer den nicht erreichten Bereich, aus der Formel und nicht
aus dem Test: eine VOLLE Spalte bringt 7,0 und gleicht damit gerade zwei leere
Spezialfelder (−6) aus. Ein Spieler mit drei offenen Spezialfeldern kaeme also
auch mit einer kompletten Spalte nicht ins Positive.

**Einschraenkung, ausdruecklich:** der Test saettigt bei vier gefuellten
Zellen -- Spezialzellen und Farbforderungen blockieren den Rest der
konstruierten Spalte, die Zeilen fuer 5 und 6 fehlen deshalb. Die Aussage
ueber f = 5 und f = 6 ist Arithmetik aus `scoring.rs:166`, keine Messung. Die
Tiefe blieb ueber den gesamten gemessenen Bereich bei 9, es gab also nicht
einmal eine teilweise Entspannung.

**Folge fuer die Arbeitsteilung:** die Hoffnung, die Spalten-Huelle der
Parallelsitzung repariere die Ziehregel nebenbei, ist damit unbegruendet. Ihre
1,512 Spezialfeld-Freischaltungen je Partie (gegen 0,713) wirken auf DIESELBE
Groesse und in die richtige Richtung, aber sie fallen am ENDE der Partie an --
die teuren Ziehserien liegen in Runde 1-3. Der Befund macht die Wirkungs-
Messung der Parallelsitzung nicht ueberfluessig, sondern wichtiger.

### par.4d Der Realisierungsabschlag, gemessen an einem plattenbewussten Spieler

Der Abschlag aus par.4 (2) sollte laut damaligem Stand auf das v22-Korpus
warten, weil die v20-Zahlen aus plattenblindem Spiel stammen. **Das war
unnoetig**: die zehn Mensch-gegen-Netz-Partien in `static/log/` sind bereits
ein plattenbewusstes Regime (der Mensch gewinnt 8 von 9 und schliesst 1,80
volle Spalten je Partie gegen 0,10 des Netzes, `STATUS.md`). Die Logs
protokollieren jede Platzierung auf der Kuppel mitsamt Musterreihe
(`[Rn] ... +X Pkt (Reihe r -> Kuppel ...)`), das Profil ist also direkt
auszaehlbar.

Platzierungen je Rasterreihe und Partie, 10 Partien, Menschname je Partie aus
dem Log-Kopf gelesen:

| Reihe | Mensch | Netz (v21, 400 Sims) | v20-Selbstspiel | Mensch / v20 |
| --- | --- | --- | --- | --- |
| 1 | 3,60 | 4,70 | 4,80 | 0,75x |
| 2 | 3,30 | 4,70 | 4,77 | 0,69x |
| 3 | 3,20 | 3,30 | 2,84 | 1,13x |
| 4 | 2,60 | 2,30 | 1,89 | 1,38x |
| 5 | **2,30** | 1,10 | 0,84 | **2,74x** |
| 6 | **1,70** | 0,50 | 0,58 | **2,93x** |
| Summe | 16,70 | 16,60 | – | |

**Die Summe ist praktisch gleich (16,70 gegen 16,60), die Verteilung nicht.**
Der Mensch tauscht kurze Reihen gegen lange: rund ein Viertel weniger in Reihe
1-2, dafuer das Zwei- bis Dreifache in Reihe 5-6.

**Folge fuer die Reservationsregel:** ein Abschlag, der auf dem v20-Korpus
geeicht ist, unterschaetzt die Realisierung einer TIEFEN Zelle um etwa den
Faktor 3. Genau diese Zellen sind es, die eine Kuppelplatte wertvoll machen --
`V` waere also systematisch zu klein, und die Regel wuerde zu selten ziehen.
Das wirkt der Richtung von Mangel 1 aus par.1c gleichsinnig entgegen, macht
die Netto-Aussage also nicht eindeutiger, sondern die Eichung wichtiger.

**Kreuzprobe gegen STATUS.md** (weil die Zahlen dort anders aussehen und ein
stiller Widerspruch teurer waere als eine Zeile Erklaerung): STATUS nennt ein
"Abschlussprofil" 4,00/4,10/3,40/3,20/2,50/2,20 gegen 4,90/4,90/3,30/2,40/
1,10/0,50. Das ist eine ANDERE Groesse -- belegte Rasterzellen am Ende, also
Musterreihen-Platzierungen PLUS automatisch gelegte Spezialfliesen. Rechnung:
16,70 + 2,70 Freischaltungen = 19,4 und 16,60 + 0,50 = 17,1, und das sind
exakt die Summen der beiden STATUS-Profile. Die Platzierungspunkte stimmen
ohnehin auf die Stelle (54,9 gegen 55,8). Beide Messungen sind also
konsistent, sie zaehlen Verschiedenes.

**Einschraenkung:** n = 10 Partien, ein einzelner Mensch, und die
Plattenwahl war in allen zehn auf Kriterium 1 gesetzt (par.6c). Als
Groessenordnung belastbar, als Konstante nicht.

## par.5b ERGEBNIS SOLL-SEITE (2026-08-25): die Regel zieht ZU OFT

**Vorpruefung, die den Weg geaendert hat.** Die uebergebene Paarung
`best_plate_value` + `expected_points_map` kann eine noch nicht gelegte Platte
NICHT bewerten: die Karte liest je Zelle `dome_grid.get_space(r, c)` und
ueberspringt jede Zelle ohne Space -- auf einem LEEREN Slot gibt es keine, und
`best_plate_value` laeuft genau ueber die leeren Slots. Gemessen
(`plate_value_anschluss_check`): Kartensumme **15,33** auf belegten Zellen,
**0,00** auf leeren, `best_plate_value` fuer eine Pool-Platte **Some(0.0)**.
Kein Fehler der beiden Bausteine -- sie passen an dieser Stelle nicht
zusammen: die Karte bewertet VORHANDENE Zellen, die Regel braucht den Wert
NEU ENTSTEHENDER.

**Stattdessen der Weg, den der Doc-Kommentar von `best_plate_value` selbst
nennt**: je (Slot, Rotation) ein Probe-Brett, Platte legen, DANACH die
Punktekarte rechnen und ueber die vier neu entstandenen Zellen summieren --
mit Realisierungsabschlag je Rasterreihe aus par.4d (0,72 / 0,66 / 0,64 /
0,52 / 0,46 / 0,34).

**Die Reservationsregel** darauf: weiterziehen, solange
`E[max(V_next − V_hand, 0)] > 1 Punkt`, Erwartungswert ueber die Pool-Platten
GLEICHEN TYPS wie die oberste (deren Ruecken ist gratis sichtbar).

| Platten | Spez. leer | V_hand roh | SOLL roh | V_hand abgeschlagen | SOLL abg. | IST (gebaute Regel) |
| --- | --- | --- | --- | --- | --- | --- |
| 2 | 0 | 9,00 | 1 | 6,27 | 1 | 1 |
| 4 | 0 | 7,33 | 1 | 3,89 | 1 | 1 |
| 4 | 2 | 7,33 | 1 | 3,67 | 1 | **11** |
| 4 | 4 | 7,33 | 1 | 3,67 | 1 | **11** |
| 6 | 6 | 7,33 | 1 | 2,87 | 1 | **9** |

**Verdikt: die gebaute Regel zieht ZU OFT, nicht zu selten.** Die optimale
Tiefe ist in JEDEM geprueften Fall 1 -- nach der Pflichtziehung liegt bereits
eine Platte im Wert von 2,9 bis 9,0 Punkten in der Hand, und die erwartete
VERBESSERUNG durch eine weitere Ziehung bleibt unter dem einen Punkt, den sie
kostet. Wo das Brettniveau negativ ist, zieht die Regel stattdessen 9 bis 11
mal: **rund 10 verschenkte Punkte je betroffenem Stapelzug.**

**Das entscheidet die in par.1c offengelassene Nettorichtung.** Dort standen
Mangel 1 (Niveau statt Verbesserung, laesst zu SELTEN ziehen) und Mangel 3
(Einheitenbruch, Richtung unklar) gegeneinander, und die Nettorichtung war
nicht vorhersagbar. Gemessen dominiert Mangel 3: sobald `best_eval_for_tile`
ein negatives Brettniveau liefert, ist `avg_remaining_type_value − 1 >
max(gezogene)` fast immer erfuellt, weil die rechte Seite stark negativ ist.
Der Einheitenbruch ueberfaehrt den Optionswert-Fehler um Groessenordnungen.

**Robustheit gegen die eigene Modellwahl:** roh und abgeschlagen liefern
DIESELBE SOLL-Tiefe von 1, obwohl `V_hand` sich zwischen beiden um bis zu
Faktor 2,6 unterscheidet. Das Ergebnis haengt also nicht an der Wahl des
Realisierungsabschlags -- die Groesse, um die ich zuvor das v22-Korpus
abwarten wollte, ist fuer dieses Verdikt gar nicht ausschlaggebend.

**Einschraenkungen, ausdruecklich:**

1. `V` ist eine Potenzial-Naeherung: Karte auf dem Probe-Brett MIT der Platte
   gerechnet (das raeumt die Additivitaets-Naeherung teilweise ab), aber immer
   noch als Summe ueber vier Zellen statt als eine gemeinsame
   `scoring_progress`-Differenz.
2. Fuenf konstruierte Bretter, ein Seed. Die Richtung ist eindeutig, die
   genaue Zahl der verschenkten Punkte ist es nicht.
3. Die Regel bilanziert Punkte gegen Punkte und ignoriert Tempo (par.7).

## par.5c GEBAUT 2026-08-25: der Knopf `MOSAIC_STACK_DRAW_RESERVATION`

Nutzer-Auftrag nach dem Urteil in par.5b. **Default AUS** = bit-identisches
Bestandsverhalten; der Bestand bleibt der Elo-Bezug, und die Arena kann beide
Arme fahren.

**Was der Knopf aendert** (`self_play.rs::resolve_and_apply_stack_draw`):
statt `avg_remaining_type_value` (Typmittelwert in [1,3]) gegen
`best_eval_for_tile` (absolutes Brettniveau) zu stellen, rechnen jetzt BEIDE
Seiten mit derselben Funktion, und verglichen wird die erwartete
VERBESSERUNG statt des Niveaus:

> weiterziehen, solange `E[max(best_eval(V_next) − V_hand, 0)] > 1 Punkt`

Der Erwartungswert laeuft nur ueber die Pool-Platten des Typs, den die
sichtbare Rueckseite ansagt (`dome_tile_pool.first()`) -- das Gratis-Signal
aus par.2, das der Bestand nicht nutzt.

**Wirkung und Kosten, netzfrei auf denselben Brettern wie par.6b** (der Knopf
haelt seinen Wert in einem `OnceLock`, ein Prozess sieht also nur EINEN Arm --
die Zahlen stammen aus zwei Laeufen):

| Platten / Spez. leer | Tiefe Bestand | Tiefe repariert | Zeit Bestand | Zeit repariert |
| --- | --- | --- | --- | --- |
| 2 / 0 | 1 | 1 | 638 us | 1,8 ms |
| **4 / 2** | **11** | **1** | **13,8 ms** | **1,2 ms** |
| 4 / 0 | 1 | 1 | 334 us | 1,2 ms |
| 6 / 0 | 1 | 1 | 227 us | 740 us |

**Die Kostenfrage aus dem Zuschnitt faellt anders aus als erwartet.** In den
gutartigen Faellen kostet die Reparatur das Zwei- bis Dreifache (sie rechnet
ueber den Restpool statt einen Mittelwert), im pathologischen Fall aber ein
ELFTEL -- sie hoert nach der Pflichtziehung auf, statt elfmal zu ziehen und
dabei jedes Mal alle bisher gezogenen Platten neu zu bewerten. Da der teure
Fall genau in den ~39 % Partien mit Kriterium 6 auftritt und dort die
Rechenzeit dominiert, ist eine Verlangsamung des Self-Play unwahrscheinlich.

**Ausdruecklich NICHT belegt:** dass der Knopf Spielstaerke bringt. Vier
konstruierte Bretter zeigen Mechanismus und Kosten, nicht Elo. Dafuer steht
die Abnahme aus par.6 an: gepaarte Arena, Block-Ebene, SPRT auf informativen
Paaren, **getrennt nach Plattensatz** -- in Partien ohne Kriterium 6 ist die
Tiefe in allen Regimen 1, dort kann kein Unterschied entstehen.

## par.5d ABNAHME GEFAHREN 2026-08-25: KEIN Staerkegewinn

Gepaarter Zwei-Arm-A/B (`tools/paired_arena_env_ab.py`), Champion@400 gegen
Heuristik@150, 200 Partien auf identischen Basis-Seeds, Knopf 0 gegen 1;
Artefakt `paired_arena_env_stackdraw2.json`.

| | Netz | Heuristik | Netz-Siege |
| --- | --- | --- | --- |
| gesamt (n=200) | −0,97 ± 1,59 (t=−1,20) | +0,06 ± 1,80 (t=+0,07) | 151/200 -> 141/200, McNemar p=0,1539 |
| **mit Kriterium 6** (n=76) | −1,26 ± 3,34 (t=−0,74) | +0,97 ± 3,87 (t=+0,49) | 49/76 -> 41/76 |
| ohne Kriterium 6 (n=124) | −0,80 ± 1,55 (t=−1,01) | −0,50 ± 1,68 (t=−0,58) | 102/124 -> 100/124 |

**Verdikt: kein Arm ist besser.** Weder in der Siegquote noch im Punkteniveau,
weder gesamt noch in der Teilmenge, in der die Regel ueberhaupt greifen kann.
Alle t-Werte liegen im Rauschen. Der Knopf bleibt auf Default AUS.

### Zwei Einschraenkungen des Instruments, vorab benannt und hier bestaetigt

1. **Der Knopf wirkt auf BEIDE Seiten.** `resolve_and_apply_stack_draw` sitzt
   in `apply_chosen_action`; die Doku von `paired_arena_env_ab.py` unterstellt
   dagegen "die Heuristik liest keinen der Knoepfe -- die Arm-Differenz
   attribuiert sauber auf die Netz-Seite". Fuer diesen Knopf gilt das NICHT.
   Ein symmetrischer Effekt ist im Duell unsichtbar; deshalb war das
   Punkteniveau vorab als primaeres Mass benannt -- und auch dort bewegt sich
   nichts.
2. **Power.** In der Platte-6-Teilmenge (n=76) ist das KI der Punktedifferenz
   ±3,3. Ein Effekt von 1-2 Punkten waere hier nicht auffindbar. Das Ergebnis
   heisst "nicht nachweisbar", nicht "null".

### KORREKTUR einer eigenen Vorregistrierung

par.6 und STATUS trugen die Begruendung, in Partien OHNE Kriterium 6 "kann
kein Unterschied entstehen". **Das ist falsch, und die Daten zeigen es**: dort
stehen −0,80 Punkte und zwei gekippte Partien. Der Grund ist Arithmetik, die
ich zu grob genommen hatte -- ohne Kriterium 6 ist das Brettniveau zwar
positiv, aber `avg_remaining_type_value` liegt in [1, 3]; bei kleinem
`max_drawn` zieht auch die Bestandsregel weiter. Die gemessenen 92-95 Prozent
Tiefe 1 hiessen nie "immer", sie liessen 5-8 Prozent uebrig. Richtig ist:
*dort ist der Unterschied SELTEN*, nicht *dort gibt es keinen*.

### Was das inhaltlich offen laesst

Der erwartete Punktegewinn bleibt aus. Nach par.5b haette die Bestandsregel in
Platte-6-Partien mehrere Punkte je Partie verschenken muessen (11,22 gegen
3,93 Punkte je Partie in Blindziehungen). Zwei Erklaerungen bleiben, und
DIESE Daten trennen sie nicht:

* **Die gekauften Platten waren ihren Preis wert** -- dann ist das `V` aus
  par.5b zu niedrig angesetzt, und der Fehler liegt in der Potenzial-
  Naeherung, nicht in der Regel.
* **Die reparierte Regel zieht jetzt zu wenig** -- dieselbe Ursache, andere
  Richtung.

Beides waere ein Befund ueber die BEWERTUNG einer Kuppelplatte, nicht ueber
die Stopp-Regel. Ein Zuschnitt dafuer braucht ein `V`, das an realisierten
Punkten geeicht ist -- also das v22-Korpus.

### par.5e WIEDERVORLAGE nach dem v22-Korpus (Nutzer-Entscheid 2026-08-25)

Der Knopf bleibt AUS, auch waehrend der v22-Erzeugung -- den Korpus unter der
Regel zu erzeugen, die er erst validieren soll, waere zirkulaer. Nach dem
Korpus wird der Arm wieder aufgenommen, aber **nur mit diesen beiden
Bedingungen**; ohne sie liefert eine Wiederholung dasselbe Nichtergebnis.

**Bedingung 1: die Eichung von `V` braucht einen Vergleichspunkt von
AUSSERHALB der v22-Verteilung.** v22 wird von Spielern erzeugt, die Platten
schlecht verwerten. Eicht man `V` an deren realisierten Punkten, misst man den
Wert einer Kuppelplatte gegen die Unfaehigkeit, sie zu nutzen, und bekommt
zwangslaeufig "nicht ziehen" heraus -- zirkulaer in der Gegenrichtung zu dem,
was oben abgelehnt wird. Dieselbe Signatur wie die Plattenblind-Falle. Der
Kandidat fuer den zweiten Punkt sind die Mensch-Logs aus par.6c.

**Bedingung 2: ein EINSEITIGER Knopf.** Der heutige wirkt auf beide Seiten
(`resolve_and_apply_stack_draw` sitzt in `apply_chosen_action`), und ein
symmetrischer Effekt ist im Duell unsichtbar -- bei JEDEM n. Die ±3,3 Punkte
Power in der Platte-6-Teilmenge sind also nur die halbe Erklaerung fuer das
Nichtergebnis aus par.5d; mehr Partien heilen die andere Haelfte nicht.
Mechanisch moeglich ist es: die Funktion bekommt das ganze `Game`
(self_play.rs:500), der handelnde Spieler ist damit in Reichweite. **Nicht
gebaut.**

**Was die Wiedervorlage NICHT ist:** eine Wiederholung derselben Arena mit
mehr Partien. Solange Bedingung 2 offen ist, kauft zusaetzliches Budget nur
engere Intervalle um eine Groesse, die strukturell auf Null liegt.

**Fuer die v22-Vorbereitung heisst das:** die Frage "mit oder ohne Reparatur
erzeugen" ist damit NICHT entschieden, sondern gegenstandslos geworden -- es
gibt keinen belegten Staerkeunterschied in beide Richtungen. Der Korpus kann
mit dem Bestand erzeugt werden; der Vorbehalt bleibt, dass ein symmetrischer
Fehler im Duell unsichtbar ist und im Label trotzdem steht.

## par.5 STUFE 1 (zuerst, ohne Arena-Budget): weicht der Champion ab?

Reine Korpus-Auswertung auf vorhandenen Self-Play-Records, kein Netzlauf, kein
Arena-Lauf. Einheit der Auswertung ist die **PARTIE** (Block-Regel), CI 95 %
ueber Partien.

Je Zustand, in dem `dome_stack_peek` legal ist, wuerden erhoben:

1. **IST**: die Zahl der tatsaechlich gezogenen Platten in dieser Ziehserie
   (aus `pending_stack_draw` bzw. der Aktionsfolge), und der Anteil der
   Policy-Masse auf `dome_stack_peek`.
2. **SOLL**: die von der Regel vorgeschriebene Zahl, mit `V` nach par.3 und
   den beiden Behandlungen aus par.4.
3. **Differenz** IST − SOLL, je Runde und je Punktestand-Klasse (weil bei
   Punktestand 0 die Kosten auf 0 fallen und die Regel dort "weiterziehen"
   sagt, solange der Stapel etwas hergibt).

Zusaetzlich die sechs Standard-Kennzahlen jedes Messberichts
(Reihen-/Spalten-/Strafleistenauslastung, Punkte je Wertungsplatte, eigene
Punkte, Margin), soweit im Korpus vorhanden.

**Vorab festgelegte Lesarten:**

* **|IST − SOLL| klein und ohne Vorzeichen-Systematik** ⇒ der Champion zieht
  bereits naeherungsweise optimal. Kein Eingriff; die Regel bleibt als
  Diagnose-Instrument stehen. Das ist ein vollwertiges Ergebnis, kein
  Fehlschlag.
* **IST < SOLL systematisch** (zieht zu selten) ⇒ dieselbe Signatur wie bei
  der Strafleisten-Aversion: eine legale, rechnerisch lohnende Aktion wird
  gemieden. Dann waere Stufe 2 gerechtfertigt.
* **IST > SOLL systematisch** (zieht zu oft) ⇒ Punkte werden verschenkt.
  Vor jedem Eingriff waere hier zuerst par.4 zu pruefen, weil beide Fallen
  genau in diese Richtung irren -- ein zu hohes `V` erzeugt dieses Bild auch
  bei einem korrekt spielenden Champion.

**Wichtiger Waechter (Lehre aus dem Strafleisten-Tor vom selben Tag):** die
Stellungen sind ORDNUNGSFREI je Datei zu ziehen und die Rundenverteilung ist
im Bericht auszuweisen. Ein Deckel "erste N je Datei" liefert eine
Runde-1-Stichprobe und damit eine Scheinaussage.

## par.6 STUFE 2 (nur bei belegter Luecke): Eingriff

Erst nach Stufe 1 und nur bei einer Luecke mit Vorzeichen. Zwei Formen stehen
zur Wahl, die Entscheidung faellt der Nutzer:

* **Als Vorzug** in der bestehenden Kette (`plate_builder::drafting_preference`)
  -- Praeferenz statt Verbot, dieselbe Bauform wie die Plattenbauer.
* **Als Lehrer-Signal** fuer die Destillation, ohne Eingriff in die Live-Suche.

Bewertet wuerde nach der Hauslatte: gepaarte Arena, Block-Ebene, SPRT auf
informativen Paaren (`tools/paired_gating.py`).

## par.7 Bekannte Einschraenkungen, vorab

1. **Myopie.** Die Ein-Schritt-Regel ist im klassischen Fall unabhaengiger,
   gleichverteilter Ziehungen mit Rueckgriff exakt optimal. Hier wird ohne
   Zuruecklegen aus einem endlichen Vorrat gezogen; die Regel bleibt die
   naheliegende Naeherung, ihre Optimalitaet braucht den Monotonie-Nachweis
   (ist die Stopp-Menge geschlossen?) und der ist NICHT gefuehrt.
2. **Rueckwirkung auf spaetere Runden.** Nicht behaltene Platten gehen unter
   den Stapel zurueck; die Ziehung veraendert also den Vorrat kuenftiger
   Runden und die Optionen des Gegners. Die Regel ignoriert das.
3. **Reihenfolge-Wahl.** Die Regel sagt nichts darueber, in welcher
   Reihenfolge zurueckgelegt wird. Die Engine legt kanonisch zurueck und
   faechert die Permutationen nicht auf (`engine/src/game.rs:391`).
4. **Der Gegner zieht auch.** Ein Zug an dieser Stelle kostet Tempo im
   Drafting; die Regel bilanziert nur Punkte gegen Punkte.
