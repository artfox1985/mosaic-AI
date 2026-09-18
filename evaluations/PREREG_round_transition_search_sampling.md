<!-- STATUS: OFFEN | Frage: Soll die Suche das Tiling sehen -- im Blatt (Variante B) oder als Encoder-Eingabe (Variante C)? | Beleg: B NEGATIV (17.9). Stufe-0-Sonde DURCH (16.9), Stichentscheid-A/B: Zweig traegt, bleibt an (16.12). Variante A draussen (16.10). **VARIANTE C TRAEGT (18.12): v29-b07 gegen b03 432:368 von 800, Block-z +2,40, 90 neue Spalten angekoppelt; 884 im v30-Rezept, v30 startet kalt (18.11). Champion-Kanten b07 gemessen (minimal_strength_core 10.11), Champion wurde b09.** Suchseite und Encoder-Seite damit beantwortet; offen nur die v30-Abnahme des Kaltstarts. -->

# PREREG: Rundenuebergang als Zufallsknoten in der SUCHE

**Angelegt 2026-08-25 auf Nutzer-Anweisung.** Ersetzt die Fahrplan-Notiz im
Doc-Kommentar von `ROUND_TRANSITION_SAMPLING`, die aus einer anderen
Mess-Aera stammt.

## par.1 Was der Schalter tut

`net_mcts.rs:84`: `pub const ROUND_TRANSITION_SAMPLING: bool = false`.
Aufgerufen wird er an genau einer Stelle (`net_mcts.rs:2921`), und nur dort,
wo ein Blatt `terminal` ist -- also am Drafting-nach-Tiling-Uebergang. Statt
des einzelnen Netz-Blattwerts laeuft dann
`round_transition::sample_round_transition_value`: die Fabrik-Neubefuellung
wird bemustert und der Blattwert ist das Mittel ueber die Stichprobe.

Parameter (`round_transition.rs:58/66`, in dieser Sitzung nachgesehen):
`N_SAMPLES_SEARCH = 8`, `TIME_BUDGET = 50 ms` je Blatt.

**Warum das ueberhaupt eine Frage ist:** der Suchbaum laeuft bewusst nur
INNERHALB einer Runde. Die Fabrik-Neubefuellung der naechsten Runde ist
nirgends als echter Zufallsknoten dargestellt, der Blattwert muss also
implizit ueber die ganze Verteilung moeglicher kuenftiger Steinzuege mitteln.
Der Modulkopf von `round_transition.rs` nennt genau das als Verdacht fuer das
Val-R2-Plateau bei 0,2-0,3.

## par.2 Warum die alte Sperre nicht bindet

Der Doc-Kommentar sagt "Phase 2 im Fahrplan, erst nach einer belegten
Val-R2-Verbesserung ueber den Trainingsziel-Pfad aktivieren". Zwei Gruende,
warum das heute nichts entscheidet:

1. **Er ist aelter als die Architektur, gegen die er sich richtet.** Letzte
   Beruehrung der Zeilen 76-84: `91ccb42`, 2026-07-17. Der WDL-Kopf kam am
   2026-08-05 (`3484585`, Task #34), Schema 17 am 2026-08-06. Der Kommentar
   ist in einer Aera geschrieben, in der der Value-Kopf eine Skalar-Regression
   war und val-R2 das Mass. Heute waehlt die Kampagne nach Brier auf dem
   WDL-Kopf.
2. **Seine Bedingung ist ohnehin erfuellt.** `archive/history.md:7578`:
   "v11-TD-Bootstrap hob R1/R2-R2, keine Staerke". Der Trainingsziel-Pfad hat
   genau das geliefert, was der Schalter verlangt.

**Das ist ausdruecklich KEIN Argument dafuer, dass der Schalter etwas
bringt** -- siehe par.3.

## par.3 Der ernsthafte Einwand, vorab notiert

Derselbe Satz, der die Sperre aufhebt, ist das staerkste Argument gegen den
Arm: "hob R1/R2-R2, **keine Staerke**". Die Groesse wurde bewegt, Spielstaerke
folgte nicht. Dieser Schalter greift dieselbe Groesse -- den Blattwert am
Rundenuebergang -- nur von der Suchseite statt von der Label-Seite.

Es ist also gut moeglich, dass die ganze Linie tot ist und nicht nur ihr
Trainingsziel-Zweig. Wenn der Arm negativ ausfaellt, ist das deshalb kein
Nullergebnis, sondern ein SCHLUSS: die Linie waere dann auf beiden Wegen
geprueft und geschlossen. Das ist der eigentliche Wert dieses Laufs.

## par.4 Zwei Kosten, beide vor der Staerkemessung zu klaeren

### par.4.1 Durchsatz

8 Netzauswertungen statt einer, an jedem pseudo-terminalen Blatt. Das klingt
selten, ist es aber nicht: gegen Rundenende ist das der haeufige Blatttyp.

**Ungeprueft und deshalb zuerst zu messen:** die acht Auswertungen laufen
nacheinander in einer Closure und duerften den `net_batcher` umgehen. Dann
ist der Aufschlag schlechter als Faktor 8. Ein Verdacht, keine Messung.

**Kostentor, VORAB festgelegt:** Aufschlag auf die Wanduhr je Partie bei
sonst identischer Konfiguration. Schwelle **25 Prozent**. Darueber wird der
Arm nicht weiterverfolgt, unabhaengig von jeder Staerkevermutung.

Die 25 sind uebernommen, nicht neu gesetzt: `PREREG_bootstrap_horizon.md`
Stufe 1 hat mit derselben Schwelle gearbeitet und ist an ihr gescheitert
(Aufschlag 60,7 Prozent). Dieselbe Klasse Eingriff bekommt dieselbe Huerde,
damit die Schwelle nicht je Arm passend gewaehlt wird.

### par.4.2 Was am Determinismus wirklich haengt

**KORREKTUR gegenueber der ersten Fassung dieser Prereg (2026-08-25).** Sie
behauptete, der Schalter nehme "den eigentlichen Gewinn" aus
`PREREG_chance_nodes.md` zurueck. Das war zu stark, weil eine bereits
entschiedene Prereg uebersehen wurde.

`PREREG_search_rng_split.md` ist ENTSCHIEDEN und umgesetzt:
`net_mcts::derive_search_seed` (SplitMix64) gibt der Suche einen EIGENEN,
aus dem Partie-Seed ABGELEITETEN Zufallsstrom -- ausdruecklich, damit Partien
replaybar sind und gepaarte Arenen echte gemeinsame Zufallszahlen haben. Ein
scharfer Sampling-Schalter wuerde also aus diesem abgeleiteten Strom ziehen,
nicht aus einer frischen Quelle.

Daraus folgt eine dreiteilige, genauere Kostenrechnung:

| Eigenschaft | Bei scharfem Schalter |
| --- | --- |
| Wiederholbarkeit (gleiche Seeds -> gleiches Ergebnis) | **bleibt** |
| Zustands-Determinismus (gleiche Stellung -> gleicher Zug, unabhaengig vom Pfad) | **faellt** |
| Kraft der PAARUNG in gepaarten Arenen | **leidet** |

Der dritte Posten ist der teure und der am wenigsten offensichtliche.
Gemeinsame Zufallszahlen wirken nur, solange beide Arme dieselbe
Zufaelligkeit auf dieselbe Weise verbrauchen. Sobald die Partien
auseinanderlaufen, ziehen die Arme VERSCHIEDENE Stichproben -- die Paarung
wird unschaerfer. Der Schaden trifft also nicht die Reproduzierbarkeit,
sondern die Trennschaerfe des Messaufbaus, mit dem dieser Arm selbst
beurteilt werden soll.

Der zweite Posten trifft Stellungs-Diagnosen und die Paritaetssonde
(`tools/parity_probe.py`, Hash `8c6684ff`): dieselbe Stellung ueber einen
anderen Pfad erreicht kann einen anderen Zug liefern.

**Verworfen: "nur in Arenen scharf, im Self-Play aus".** Das setzt die
Zufaelligkeit genau dorthin, wo gemessen wird, und laesst den Datenerzeuger
sauber -- verkehrt herum. Self-Play ist ohnehin absichtlich zufaellig
(Dirichlet-Rauschen, Temperatur); die Arena ist das Messgeraet.

**Offen und vor dem Bau zu entscheiden (Nutzer):** ob der Verlust an
Paarungs-Trennschaerfe fuer diesen Arm hingenommen wird, und ob der
Paritaets-Hash unter scharfem Schalter ueberhaupt noch gelten soll oder ob
die Sonde den Schalter explizit aus erzwingt.

**ENTSCHIEDEN 2026-09-05, 18:28 (Nutzer: "ja, trag das als bauvorgabe ein"):
der Tausch wird NICHT in Kauf genommen, sondern per Bauvorgabe vermieden.**
Die Stichprobe am Rundenende-Blatt (gezogene Fabrik-Neubefuellung, bei
Variante A alle N, bei Variante B die eine) zieht ihren Seed NICHT aus dem
laufenden Suchstrom, sondern **stellungsgebunden**: Seed = Hash des
Blatt-Zustands (Bretter, Musterreihen, Strafleisten, Chips, Beutel-/Turm-
Zaehler, Runde, Spieler am Zug) verknuepft mit dem abgeleiteten Such-Seed
der Partie. Folgen, die dadurch gelten:

| Eigenschaft | Mit stellungsgebundenem Seed |
| --- | --- |
| Wiederholbarkeit | bleibt |
| Zustands-Determinismus (gleiche Stellung -> gleicher Zug, pfadunabhaengig) | **bleibt** (dieselbe Stellung zieht dieselbe Neubefuellung) |
| Kraft der Paarung | **bleibt** (beide Arme ziehen in derselben Stellung dieselbe Stichprobe) |
| Paritaetssonde / Hash `8c6684ff` | gilt weiter, ohne den Schalter erzwungen ausschalten zu muessen |

Preis: ein Zustands-Hash je Rundenende-Blatt. Die Engine hat heute KEINE
Hash-Funktion fuer Zustaende (2026-09-05 gegrept: kein Zobrist, kein
`state_hash`); Kandidat ist FNV-1a (`lib.rs::fnv1a_64`, bereits fuer den
Vertragshash im Baum) ueber eine kanonische Serialisierung der oben
genannten Felder. Kosten UNGEPRUEFT, vermutlich klein gegen den
Tiling-Loeser, der am selben Blatt laeuft; das Kostentor par.4.1 misst sie
mit. Schritt 1 der Messkette (par.5) misst die Block-Streuung TROTZDEM gegen
die Referenz 5,75 Prozentpunkte bei n = 400 -- die Vorgabe ist eine
Konstruktion, kein Beleg, dass die Streuung wirklich gleich bleibt.

**Bereits gebaute Praezedenz fuer deterministisch gemachte Zufallsschritte in
der Suche** (nicht stellungsgebunden, aber derselbe Gedanke): Stapel-Peek und
Rundensimulation mischen den verdeckten Restpool einmalig mit dem Suchstrom
(net_mcts.rs um 4314, `round_transition_deep::simulate_one_round`).

### par.4.3 ZUSATZ aus der externen Recherche: robuste Aggregatoren (registriert 2026-08-27)

Bisher stand dieser Zusatz nur in `STATUS.md` (Abschnitt "Weitere offene
Straenge") und damit an einer Stelle, die regelmaessig gekuerzt wird. Hier ist
er registriert; **an der Messkette in par.5 aendert er nichts.**

Der Schalter mittelt heute ARITHMETISCH ueber die Stichprobe
(`sample_round_transition_value`, `N_SAMPLES_SEARCH = 8`). Die Recherche legt
nahe, stattdessen einen ROBUSTEN Aggregator zu pruefen: **Median, gestutztes
oder winsorisiertes Mittel**. Begruendung: bei acht Ziehungen bestimmt ein
einzelner Ausreisser der Fabrik-Neubefuellung das Mittel merklich mit, und
genau diese Schwankung soll der Schalter ja daempfen, nicht durchreichen.

**Als Arm zu behandeln, nicht als Verbesserung:** der Aggregator ist ein
ZWEITER Faktor neben "Schalter an/aus". Wer beide zugleich dreht, kann
hinterher nicht zuordnen -- die Reihenfolge bleibt also Kostentor, dann
Schalter, ein Aggregator erst danach und nur, wenn der Schalter ueberhaupt
etwas bewegt.

## par.5 Messkette (Reihenfolge bindend)

**Schritt 0 -- Entscheid zur Paarungs-Trennschaerfe.** Nutzer entscheidet
par.4.2. Ohne diesen Entscheid wird nicht gebaut. Kein Blocker im Sinne von
"unmoeglich" -- die Wiederholbarkeit bleibt erhalten -- sondern ein bewusster
Tausch: der Arm verschlechtert das Instrument, mit dem er selbst gemessen
wird.

**Schritt 1 -- Kostentor.** Gleiche Konfiguration, Schalter aus gegen an,
Wanduhr je Partie. Schwelle 25 Prozent (par.4.1). Zusaetzlich mitschreiben,
wie oft ein pseudo-terminales Blatt ueberhaupt erreicht wird -- ist der Anteil
klein, ist auch der Effekt klein, und das waere schon hier sichtbar.

**Schritt 2 -- Staerke.** Gepaarte Arena, DASSELBE Netz gegen sich selbst,
einmal mit und einmal ohne Schalter, beide Sitze, gleiche Seeds.

**Entscheidungsmass: Siegquote und Punktemarge auf BLOCK-Ebene.**
Ausdruecklich NICHT val-R2, nicht Brier, keine Offline-Metrik. Genau daran
ist v11 vorbeigelaufen: die Metrik bewegte sich, die Staerke nicht
([[feedback_preregister_decision_metric]]).

**Falsifikator:** keine signifikante Staerkeverbesserung auf Block-Ebene ->
der Arm ist negativ, und die Linie "Rundenuebergangs-Rauschen" gilt zusammen
mit dem v11-Befund als auf beiden Wegen geprueft und geschlossen.

**Mitzuschreiben** (Standard-Kennzahlen je Seite und als Differenz):
Reihenauslastung, Spaltenauslastung, Strafleistenauslastung, Punkte je
Wertungsplatte, eigene Punkte, Marge.

## par.6 Was diese Prereg NICHT ist

- **Keine Wiedereinfuehrung der Determinisierung.** `MOSAIC_NUM_DETERMINIZATIONS`
  und `determinize_hidden_information` sind laut `PREREG_chance_nodes.md` auf
  Nutzer-Anweisung ersatzlos entfallen ("k wert und den shuffle rausnehmen").
  Das bleibt so; hier geht es um den Rundenuebergang, nicht um den
  Kuppelstapel.
- **Keine Aussage ueber Teil B** derselben Prereg (aufgezaehlter Zufallsknoten
  innerhalb der Runde, ZU BAUEN).
- **Kein Trainingsziel-Eingriff.** Der TD-Bootstrap bleibt unangetastet; er
  ist die Label-Seite und laut `PREREG_chance_nodes.md` erledigt.

## par.7 LEITSATZ DES NUTZERS UND AUFSPALTUNG DES ARMS (2026-09-05, 18:08; Aufspaltung)

**Nutzer, woertlich:** *"drafting und tiling gehen hand in hand. das
drafting muss zum teil schon wissen wie das tiling agieren wird um die
fliesen zu legen und punkte zu generieren."* Und davor: *"mir kommt diese
fehlende sicht der suche auf das tiling als schwachpunkt vor."*

**Was der Schalter dieser Prereg dazu leistet und was nicht:** er buendelt
ZWEI Dinge. (a) `resolve_to_pre_chance` spielt das Tiling BEIDER Seiten mit
dem exakten Loeser durch -- das ist die Sicht, die der Nutzer meint, und sie
ist deterministisch. (b) `sample_round_transition_value` bemustert danach
die Fabrik-Neubefuellung (8 Stichproben, 8 Netzaufrufe) -- das ist der
Zufallsanteil, an dem Kostentor (par.4.1) und Paarungs-Schaerfe (par.4.2)
haengen. Die Kosten der Prereg stammen fast ganz aus (b).

**Variante B -- REGISTRIERT 2026-09-05, 18:35 (Nutzer: "ja registrier B"); Basisarm VOR Variante A:**
(a) wie gebaut, dann EINE gezogene Neubefuellung und EIN Netzaufruf. Kosten je
Rundenende-Blatt: zwei Loeser-Laeufe, Netzaufrufe wie heute. Der Blattwert ist
dann eine Stichprobe statt eines Mittels; die Suche mittelt ueber Besuche.
Paarungs-Schaerfe (par.4.2) ist genauso betroffen wie bei A (der RNG wird
gezogen), das Kostentor vermutlich nicht gerissen -- UNGEPRUEFT, der
Loeser hat bei mehreren chippable Reihen ein Knotenbudget
(`tiling_solver.rs`, Haenger-Vorfall), eine greedy Variante fuer das Blatt
waere der billigere Ersatz. Beide Varianten (A, B) laufen durch dieselbe
Messkette par.5: Schritt 0 Nutzer-Entscheid par.4.2, Schritt 1 Kostentor
und Anteil der Rundenende-Blaetter je Suche, Schritt 2 Staerke im
gepaarten Duell desselben Netzes mit gegen ohne Schalter.

**Dritte Variante C, ausserhalb dieser Prereg (Encoder-Seite):** dem Netz
das projizierte Nach-Tiling-Raster und den erwarteten Kuppel-Bonus als
Eingabe geben (Richtung des Sicht-Arms v24-b04). Kostet in der Suche nichts,
braucht ein Training, bleibt eine Schaetzung statt des gespielten Tilings.

**Entschieden (Nutzer, 2026-09-05):** par.4.2 als Bauvorgabe (stellungsgebundener
Seed, oben), Variante B registriert und als Basisarm gesetzt; A folgt nur, wenn B
traegt und die Mittelung ueber N Stichproben eine eigene Frage wird. Bau
fruehestens nach den v24-Abnahmen (Maschine belegt); Reihenfolge der
Such-Knoepfe am v24-Siegernetz: K3-P2 (gebaut), K4 Rundenschaetzer
(`round_estimate_leaf_term`), dann B -- ein Knopf, ein Netz, eine Messung.

**NACHTRAG 2026-09-15: diese Reihenfolge ist abgearbeitet, und K4 ist ENTSCHIEDEN --
negativ.** Beide vorregistrierten Dosen schaden hochsignifikant (20:60 bei C_est 1,0, 45:85
bei 0,5; -14,3 bzw. -8,3 Punkte je Partie, rund -0,9 volle Spalten;
`PREREG_round_estimate_leaf_term.md` par.7c/7d). **Damit ist B an der Reihe.**

**Und der Befund ist mehr als ein abgeraeumter Vorgaenger -- er ist ein ARGUMENT fuer B.** Der
Falsifikator jener Prereg (par.5) sagt woertlich, bei Scheitern gelte: *"die Sicht auf das
Tiling muss ueber die Geometrie kommen (`round_transition_search_sampling` par.7 Variante B/C),
NICHT ueber Punkte."* Genau das ist eingetreten, und die Randgroessen sagen, warum: K4 senkt die
Strafleiste (-1,57) und hebt volle Zeilen (+0,11), waehrend Spalten (-0,84) und Spezialfelder
(-0,59) einbrechen. Ein Term, der den RUNDENSCORE an den Blattwert haengt, macht die Suche
rundenscore-gierig -- er kauft das Sofortige und verkauft das Langfristige.

**B greift anders an:** es rechnet das Tiling IM BLATT durch, der Value-Kopf kommt ueber den
Blattwert ins Spiel statt ueber einen Gewichtsparameter. Der Unterschied ist der zwischen "dem
Solver ein Gewicht geben" und "die Suche das Tiling sehen lassen" (par.7). K4s Scheitern trifft
B also nicht mit, sondern schliesst den konkurrierenden Weg aus.

## par.8 AUDIT 2026-09-09: zwei Praemissen halten nicht mehr

1. **par.6 ("Determinisierung ersatzlos entfallen") ist falsch.** `MOSAIC_NUM_DETERMINIZATIONS`
   steht als aktiver Knopf in `engine/src/knob_registry.rs`, `determinize_hidden_information`
   lebt in `engine/src/net_mcts.rs:986` und wird unter `DETERMINIZE_ROOT_HIDDEN_INFO = true`
   (`:976`) an jeder Wurzel aufgerufen. Es ist genau die Mischstelle, die seit 2026-09-09
   als verdaechtig gefuehrt wird (`docs/architecture_reference.md`, Naht-Audit;
   `PREREG_dome_stack_information_sets.md`). Der Wegfall in `PREREG_chance_nodes.md` war
   eine FOLGE von deren Teil B, und Teil B ist ungebaut.
2. **par.4.2 verspricht als Nutzen den Erhalt einer Paritaetssonde, die es nicht mehr gibt.**
   `tools/parity_probe.py` liegt nicht im Baum; die Aera mit Soll-Hash `8c6684ff` ist am
   2026-08-28 geschlossen (`docs/promotion_checklist.md:84`). Nachfolger ist die
   Champion-Fixture `engine/tests/fixtures/net_parity_champion.txt`. Die Bauvorgabe "Hash
   gilt weiter" ist damit leer; richtig ist: Paritaets-Fixture des amtierenden Champions
   muss gruen bleiben.
3. **Die in par.4.2 zitierte Praezedenz ist ruhend bzw. selbst verdaechtig:** der
   Stapel-Peek-Shuffle ist aus (`SHUFFLE_STACK_PEEK_IN_SEARCH = false`), und der Shuffle
   in `round_transition_deep::simulate_one_round` steht in derselben Verdachtsliste.

Folge: dieser Arm haengt an der Antwort aus `PREREG_dome_stack_information_sets.md`. Wer
die Rundensimulation an Blaettern einschaltet, uebernimmt deren Mischregel; die Prereg
ist vor einem Bau um die dort entschiedene Informationsmenge zu ergaenzen. Zeilendrift:
par.1 Konstante `ROUND_TRANSITION_SAMPLING` (`net_mcts.rs:95`), Aufrufstelle der Grep auf
diesen Namen (2026-09-16: `:3334`; die Zeile wandert, der Name nicht).

## Nachtrag 2026-09-11 (Audit-Querlesung)

Die Reihenfolge-Angabe in par.7 ("K3-P2, K4, B") ist ueberholt: K4
(`round_estimate_leaf_term`) ist am 2026-09-11 als Schritt 7 des v28-Programms
eingetaktet (`PREREG_v28_window.md` par.8) und damit keine Vorstufe dieses Arms
mehr. Variante B bleibt ungebaut und haengt weiter an der Informationsmengen-
Antwort aus `PREREG_dome_stack_information_sets.md` (par.8). Zeile-1-Kopf im
selben Zug nachgezogen.

**UEBERHOLT (Rueckwaerts-Pruefung 2026-09-16):** die Informationsmengen-Antwort
liegt seit par.9 vor (`determinize_dome_pool`, Variante A), und Variante B ist
seit dem 2026-09-16 GEBAUT -- Baustand par.17. Der Absatz bleibt als Chronik
stehen; der Stand steht in par.17.

## par.9 EINGETAKTET FUER v29 (Nutzer 2026-09-12, 17:55: "gerne eintakten fuer v29")

Anlass: Projekt-Rueckschau des Koordinators, der Nutzer hat den Punkt bestaetigt. Der Arm ist
der eine Suchumbau, der die Bewertung dort korrigiert, wo Wertungsplatten entstehen: das Blatt
der Suche ist heute der Netzwert VOR dem Tiling, die Tiling-Aufloesung folgt erst nach der
Runde (par.7, Leitsatz des Nutzers).

**Gebaut wird Variante B (par.7, Basisarm) als Such-Knopf:** Tiling beider Seiten im Rundenende-
Blatt mit dem exakten Loeser (`resolve_to_pre_chance`), dann EINE gezogene Neubefuellung und EIN
Netzaufruf; Knopf `MOSAIC_ROUND_TRANSITION_LEAF` (Default 0 = Bestand bitidentisch, kein RNG-Zug),
Spec-Feld optional. **Die Antwort auf par.8 liegt inzwischen vor:** die Informationsmenge an der
Wurzel ist seit v28 durch `determinize_dome_pool` (Variante A der Kuppelstapel-Prereg,
`PREREG_dome_stack_information_sets.md`) festgelegt; das Rundenende-Blatt uebernimmt GENAU diese
Mischregel (bekannte eigene Rueckgabebloecke bleiben in Reihenfolge, nur unbekannter Praefix und
Gegnerbloecke werden gemischt), keine eigene. Der Eintrag in `docs/architecture_reference.md`
("Wo der Code Information ABSICHTLICH vernichtet") ist Teil des Baus.

**Messkette wie par.5, konkret:** Schritt 1 Kostentor am Champion (argmax-Instrument 200 Partien,
Wanduhr je Partie mit gegen ohne Knopf; Anteil der Rundenende-Blaetter je Suche); Schritt 2 A/B
gepaart am Champion v29-b01 (200 Paare, Blockgroesse 5, Logs, Standard-Kennzahlen), Kanal Punkte
und Wertungsplatten-Punkte je Kriterium neben den Siegen, weil der Knopf genau dort wirken soll.
Kein Training, kein Arm; Aufnahme ins Rezept nur bei positivem Schritt 2 und vertretbarem Kostentor
(Nutzer-Entscheid). Reihenfolge im v29-Begleitprogramm: nach Ziehsucht-Sonde und Mondstapel-
Stufe 1, weil die beiden billiger sind. Kosten grob: ein Tag Bau, 3 h Messung (ANNAHME).


## par.10 BAUVORGABE BEUTEL/TURM (Nutzer 2026-09-13, 02:05: "aber ja trag es mal nach. wir werden dann sehen ob es traegt")

**Anlass:** der Crosscheck `PREREG_stack_top_feature.md` par.14 zeigt, dass ein zaehlender Spieler
die Aufteilung der Fliesen je Farbe zwischen Beutel und Turm an jedem Entscheidungspunkt exakt
kennt (106 von 106 am Server-Log seed946607, zwei Nachfuellungen aus dem Turm vor Runde 4 und 5);
der Encoder kodiert nur die Summe (P.9, Sicht-Arm v29-b03). Die heutige Suche zieht nie aus dem
Beutel, weil ihr Blatt vor dem Tiling liegt; erst Variante B startet im Blatt die neue Runde und
muss die Fabrik-Fuellung BEMUSTERN.

**Vorgabe fuer die Stichprobe der Neubefuellung in Variante B:** sie zieht aus dem Beutel-Vec des
Suchzustands mit dem echten Turm daneben, nur die Reihenfolge im Beutel gewuerfelt, Turm-Nachfuellung
ueber den Spielpfad (`draw_with_refill`); NICHT aus der Summe Beutel plus Turm und NICHT aus einem
zusammengeworfenen Pool. Im Beispiel Runde 3 (Beutel 2 Steine blau/gelb, Turm 18) sind die ersten
zwei der 21 Fliesen damit sicher blau und gelb, der Rest kommt aus dem gemischten Turm plus
Rundenende-Abraum; ein zusammengeworfener Pool wuerde diese Sicherheit wegwuerfeln, die der Spieler
hat. Das ist sichtkonform: mehr als die Zusammensetzung weiss auch der Mensch nicht, die Reihenfolge
ist echter Zufall.

**Bestand, der das schon richtig macht (geprueft 2026-09-13):** `engine/src/round_transition.rs`
Z.200-214 (`advance_one_chance`) und Z.354-372 (Kern von `sample_round_transition_value`): Klon des
echten Zustands mit Beutel und Turm getrennt, `bag.tiles.shuffle`, Bonusplaettchen-Pool gemischt,
dann `EndTiling`; der Bootstrap-Rollout der Erzeugung (`round_transition_deep.rs` Z.815-860) nutzt
genau das. Variante B nimmt diesen Kern wieder; wer einen anderen baut, traegt ihn in
`docs/architecture_reference.md` ("Wo der Code Information ABSICHTLICH vernichtet") ein und
beantwortet dort die zwei Fragen (wessen Informationsmenge, was nimmt sie dem Spieler weg).
Kommentar Z.356-360 ("erreicht so gut wie nie den Turm-Refill-Pfad") ist fuer Runde 4/5 ueberholt
(Nachfuellungen sind dort die Regel, nicht die Ausnahme), der Code ist davon unberuehrt; Kommentar
beim Bau nachziehen.

**Tor dazu (vorab):** Sichttest am Instrument, 300 Blatt-Zustaende aus Runde 3 und 4 mit
`bag_count` < 21: die gezogene Fuellung enthaelt in JEDER Stichprobe alle Beutel-Steine (die
sicheren) und sonst nur Steine aus Turm plus Abraum; ein einziger Verstoss ist ROT. Ob die Vorgabe
Spielstaerke TRAEGT, entscheidet der A/B aus par.9 (200 Paare am Champion), nicht dieses Tor.

## AGENTEN-AUFTRAG (Stand 2026-09-13, fuer eine autonome Abarbeitung durch einen Opus-Agenten)

### 1. Ziel und Verdikt-Regel

Zu beantworten ist, ob die Suche am Rundenende das Tiling sehen soll (exakter Loeser im Blatt)
und die Fabrik-Neubefuellung als Zufallsknoten bemustert werden soll, zu vertretbarem Preis.
**Gebaut wird Variante B** (par.7, Basisarm; par.9, Nutzer 2026-09-12 "gerne eintakten fuer
v29"): Tiling beider Seiten im Rundenende-Blatt mit `resolve_to_pre_chance`, dann EINE gezogene
Neubefuellung und EIN Netzaufruf. Die Verdikt-Regel steht in **par.5**: Entscheidungsmass ist
Siegquote und Punktemarge auf **BLOCK-Ebene**, ausdruecklich NICHT val-R2, nicht Brier, keine
Offline-Metrik (an genau dieser Verwechslung ist v11 vorbeigelaufen). **Falsifikator:** keine
signifikante Staerkeverbesserung auf Block-Ebene -> der Arm ist negativ, und die Linie
"Rundenuebergangs-Rauschen" gilt zusammen mit dem v11-Befund als auf BEIDEN Wegen geprueft und
GESCHLOSSEN -- das ist laut par.3 der eigentliche Wert dieses Laufs. Vorgeschaltet und ebenso
bindend: **Kostentor 25 Prozent** Aufschlag auf die Wanduhr je Partie (par.4.1; die Schwelle ist
uebernommen, nicht neu gesetzt -- `PREREG_bootstrap_horizon.md` Stufe 1 ist mit 60,7 Prozent an
ihr gescheitert), und das **Sichttor** aus par.10 (ein einziger Verstoss ist ROT).

### 2. Voraussetzungen

- ~~**Nichts gebaut** (Kopfzeile, par.9).~~ **ERLEDIGT 2026-09-16, Baustand par.17:** der
  Such-Knopf `MOSAIC_ROUND_TRANSITION_LEAF` steht (Default 0 = Bestand bitidentisch, kein
  RNG-Zug; Spec-Feld optional mit Default 0). Offen bleibt alles ab P2 -- und VOR P2 der
  Wheel-Bau samt Anker-Drift, Anker-Konservierung und Paritaets-Fixture (par.17.5).
- **Maschine frei laut Prozessliste** fuer Bau (Volllast) und Messung; exklusiv, nie neben einer
  Arena.
- **Zwei Praemissen sind mit par.8 bereits berichtigt und gelten nicht mehr:** par.6
  ("Determinisierung ersatzlos entfallen") ist falsch -- `MOSAIC_NUM_DETERMINIZATIONS` und
  `determinize_hidden_information` leben (`net_mcts.rs:986`, `DETERMINIZE_ROOT_HIDDEN_INFO` bei
  `:976`); und die in par.4.2 versprochene Paritaetssonde `tools/parity_probe.py` mit Soll-Hash
  `8c6684ff` liegt nicht mehr im Baum -- **Nachfolger ist die Champion-Fixture
  `engine/tests/fixtures/net_parity_champion.txt`, und sie muss gruen bleiben.**
- **Die Informationsmengen-Antwort liegt vor** (par.9): das Rundenende-Blatt uebernimmt GENAU die
  Mischregel `determinize_dome_pool` (Variante A aus `PREREG_dome_stack_information_sets.md`;
  bekannte eigene Rueckgabebloecke bleiben in Reihenfolge, nur unbekannter Praefix und
  Gegnerbloecke werden gemischt), keine eigene.
- **Bauvorgabe par.4.2 (ENTSCHIEDEN 2026-09-05):** die Stichprobe zieht ihren Seed NICHT aus dem
  laufenden Suchstrom, sondern **stellungsgebunden** -- Seed = Hash des Blatt-Zustands (Bretter,
  Musterreihen, Strafleisten, Chips, Beutel-/Turm-Zaehler, Runde, Spieler am Zug) verknuepft mit
  dem abgeleiteten Such-Seed der Partie. Kandidat fuer den Hash ist `lib.rs::fnv1a_64` (die
  Engine hat kein Zobrist und kein `state_hash`, gegrept 2026-09-05). Damit bleiben
  Wiederholbarkeit, Zustands-Determinismus UND die Kraft der Paarung erhalten.
- **Bauvorgabe par.10 (2026-09-13):** die Fuellung im Blatt kommt aus dem **echten Beutel mit dem
  Turm daneben** (nur die Reihenfolge im Beutel gewuerfelt, Turm-Nachfuellung ueber den
  Spielpfad `draw_with_refill`), NIE aus der Summe Beutel plus Turm und nie aus einem
  zusammengeworfenen Pool. Der Bestand macht das bereits richtig:
  `engine/src/round_transition.rs` Z.200-214 (`advance_one_chance`) und Z.354-372 (Kern von
  `sample_round_transition_value`); der Bootstrap-Rollout der Erzeugung
  (`round_transition_deep.rs` Z.815-860) nutzt genau das. **Variante B nimmt diesen Kern
  wieder.**
- **Vorher durch sein muss:** ein Champion-Stand v29-b01 (par.9: A/B gepaart am Champion
  v29-b01), also Tor 1 der v29-Generation.

### 3. Schritte

**P1 -- Bau des Such-Knopfs (par.9, Bauvorgaben par.4.2 und par.10)**

1. Knopf `MOSAIC_ROUND_TRANSITION_LEAF`, Default 0 (Bestand bitidentisch, kein RNG-Zug),
   Spec-Feld optional. Wirkort ist die eine Stelle, an der der heutige Schalter haengt: das
   pseudo-terminale Blatt in `engine/src/net_mcts.rs` (par.1 nennt Konstante und Aufrufstelle,
   mit Zeilendrift nach par.8: beide ueber den Namen `ROUND_TRANSITION_SAMPLING` suchen --
   Konstante 2026-09-16 bei `net_mcts.rs:95`, Aufrufstelle bei `:3334`).
   Ablauf im Blatt: (a) `resolve_to_pre_chance` spielt das Tiling BEIDER Seiten mit dem exakten
   Loeser durch; (b) EINE gezogene Neubefuellung nach par.10, Seed stellungsgebunden nach
   par.4.2; (c) EIN Netzaufruf. Registratur-Eintrag, `engine_config`, `docs/knobs.md`,
   Tests (Default bitidentisch; gleicher Blatt-Zustand -> gleiche Fuellung, pfadunabhaengig).
   Bezeichner englisch. **Eintrag in `docs/architecture_reference.md` ("Wo der Code Information
   ABSICHTLICH vernichtet") ist Teil des Baus** (par.9), mit beiden Antworten: wessen
   Informationsmenge modelliert die Mischung, und was nimmt sie dem Spieler weg.
   Nebenbei nachziehen: der Kommentar `round_transition.rs` Z.356-360 ("erreicht so gut wie nie
   den Turm-Refill-Pfad") ist fuer Runde 4/5 ueberholt (par.10).
   **Kosten: rund ein Tag Bau** (ANNAHME, par.9).
2. **Tore, Reihenfolge Bau -> Tore -> Messung** (Muster `tools/night_v28_knob_build.sh`,
   gemessene Dauern 84 s / 33 s / 34 s / 19 s / 12 s):

   ```
   $env:PATH = "$(python -c 'import sys,os;print(os.path.dirname(sys.executable))');" + $env:PATH
   cd engine; cargo test --release --lib
   cargo test --release --no-run
   python -m maturin build --release
   python -m pip install --force-reinstall --no-deps engine/target/wheels/mosaic_rust-0.1.0-cp314-cp314-win_amd64.whl
   python -X utf8 -u tools/verify_frozen_heuristic.py --artifact-dir models/frozen_heuristics/hv4_anchor --out evaluations/artifacts/anchor_drift_live_wheel_<datum>_rtleaf.json
   python -X utf8 -u tools/verify_frozen_heuristic.py --artifact-dir models/frozen_heuristics/hv4_anchor --venv --out evaluations/artifacts/anchor_conservation_artifact_wheel_<datum>_rtleaf.json
   python -X utf8 tools/generate_knob_docs.py
   python -X utf8 tools/check_conventions.py
   ```

   **Netz-Paritaets-Fixture des Champions muss bei Default UNVERAENDERT bleiben** (par.8 Punkt 2:
   das ist der Nachfolger des in par.4.2 versprochenen Hashes); Anker-Drift gruen.

**P2 -- Sichttor (par.10, vorab, ein Verstoss ist ROT)**

3. Am Instrument 300 Blatt-Zustaende aus Runde 3 und 4 mit `bag_count` < 21 ziehen und pruefen:
   die gezogene Fuellung enthaelt in JEDER Stichprobe alle Beutel-Steine (die sicheren) und sonst
   nur Steine aus Turm plus Abraum. **Ein einziger Verstoss ist ROT.** Grundmenge
   Blatt-Zustaende, Einheit Verstoesse. Das Tor sagt nichts ueber Staerke -- das entscheidet der
   A/B aus par.9.

**P3 -- Schritt 1 der Messkette: Kostentor (par.5 Schritt 1, par.4.1)**

4. Gleiche Konfiguration, Knopf aus gegen an, Wanduhr je Partie; Schwelle **25 Prozent**.
   Messform nach par.9: argmax-Instrument, 200 Partien, am Champion, exklusiv:

   ```
   python -X utf8 -u self_play.py --mode network --model models/alphazero_<champion>.onnx \
     --spec models/rt_leaf_on.spec.json --games 200 --sims 400 --version rtleaf-on \
     --threads 11 --chunk 10 --per-file 10 --seed 20260931 --no-root-noise --deterministic
   ```

   Zweiter Lauf mit `rt_leaf_off.spec.json`. **Dauer (gemessen):** rund 24 min je Lauf
   (argmax-Instrument 200 Partien @400, threads 11, `docs/measured_runtimes.md`), also rund
   50 min fuer beide.
   **Zusaetzlich mitschreiben** (par.5 Schritt 1): wie oft ein pseudo-terminales Blatt ueberhaupt
   erreicht wird -- ist der Anteil klein, ist auch der Effekt klein, und das waere schon hier
   sichtbar. Grundmenge Blaetter je Suche, Einheit Anteil.
   **Reisst das Tor: Arm nicht weiterverfolgen**, unabhaengig von jeder Staerkevermutung.
   **Die Messdateien `selfplay_rtleaf-*` sind Messmaterial** und gehoeren auf die
   Ausschlussliste, nicht in den Korpus.

**P4 -- Schritt 2 der Messkette: Staerke (par.5 Schritt 2, par.9)**

5. A/B gepaart am Champion **v29-b01**, DASSELBE Netz gegen sich selbst, einmal mit und einmal
   ohne Knopf, beide Sitze, gleiche Seeds, **200 Paare**, Blockgroesse 5, Logs:

   ```
   python -X utf8 -u tools/paired_gating.py \
     --model-a models/alphazero_v29-b01_brierbest.onnx --spec-a models/rt_leaf_on.spec.json \
     --model-b models/alphazero_v29-b01_brierbest.onnx --spec-b models/rt_leaf_off.spec.json \
     --name-a v29-b01_rtleaf_on --name-b v29-b01_rtleaf_off --sims-a 400 --sims-b 400 --c-puct 1.5 \
     --block-size 5 --max-pairs 200 --sprt-alpha 1e-12 --sprt-beta 1e-12 \
     --seed <SEED> --threads 10 --log-games --no-promote-winner \
     --out evaluations/artifacts/rt_leaf_ab_on_vs_off_s<SEED>.json
   ```

   **Dauer (gemessen):** 200 Paare @400 mit Logs 5.182-5.446 s = 86-91 min
   (`docs/measured_runtimes.md`); par.9 schaetzt fuer die ganze Messung 3 h (ANNAHME).
   **Kanal Punkte und Wertungsplatten-Punkte je Kriterium stehen neben den Siegen** (par.9),
   weil der Knopf genau dort wirken soll.
   **Bei Abbruch:** mit demselben Seed wiederholen, Teil-Laeufe nicht mit vollen poolen.
6. Standard-Kennzahlen je Seite und als Differenz (par.5 "Mitzuschreiben"):
   `tools/probes/arena_column_probe.py`, `tools/plate_points_from_arena.py --block 5`,
   dazu Reihen-, Strafleisten- und Punkteniveau aus dem Artefakt.

**P5 -- Robuster Aggregator und Variante A: NICHT jetzt**

7. par.4.3 registriert Median / gestutztes / winsorisiertes Mittel als ZWEITEN Faktor neben
   "Schalter an/aus"; er wird erst danach zum Thema und nur, wenn der Schalter ueberhaupt etwas
   bewegt. Variante A (N Stichproben statt einer) folgt laut par.7 nur, wenn B traegt. **Kein
   Bau ohne eigene Registrierung.**

### 4. Auswertung und Registrierung

- **Zahlen mit n, Grundmenge, Einheit**: Sichttor "n = 300 Blatt-Zustaende aus Runde 3 und 4 mit
  bag_count < 21, Grundmenge Blatt-Zustaende, Einheit Verstoesse" (Soll: 0); Kostentor "n = 200
  Partien je Arm, Grundmenge argmax-Self-Play-Partien, Einheit Sekunden je Partie" plus "Anteil
  pseudo-terminaler Blaetter je Suche"; A/B "n = 400 Partien (200 Paare), Grundmenge gepaarte
  Arena-Partien desselben Netzes mit gegen ohne Knopf, Einheit Siege". Block-Ebene
  (Blockgroesse 5).
- **Die sechs Standard-Kennzahlen** (par.5, CLAUDE.md) je Seite und als Differenz.
- **Registrierung in einem Ergebnis-Absatz dieser Datei**, **Zeile-1-Kopf im selben Zug**
  nachziehen (bei negativem A/B auf ENTSCHIEDEN mit dem Schluss aus par.3: die Linie ist auf
  beiden Wegen geprueft und geschlossen), danach sofort
  `python tools/generate_prereg_index.py`.
- **STATUS.md Abschnitt 1 und Abschnitt 5** sowie `archive/history.md` fortschreiben. Hinweis:
  STATUS Abschnitt 5 fuehrt diese Prereg bislang als "haengt an dome_stack; Kandidat fuer
  UEBERHOLT" -- das ist mit par.9 ueberholt und beim Registrieren zu berichtigen.
- **Rueckwaerts-Pruefung**:
  `grep -rn "ROUND_TRANSITION\|round_transition\|resolve_to_pre_chance\|Tiling im Blatt" evaluations/ docs/ tools/ engine/`
  -- betroffen sind mindestens `PREREG_v29_window.md` par.7 Punkt 2c,
  `PREREG_round_estimate_leaf_term.md` par.2/par.5 (Falsifikator verweist hierher),
  `PREREG_stack_top_feature.md` par.14 (P.9 wirkt erst mit einer Suche, die den Rundenuebergang
  sieht), `docs/architecture_reference.md`, `project_drafting_must_know_tiling`.
- **Laufzeit-Zeilen** in `docs/measured_runtimes.md` (Bau-Tore, Kostentor-Laeufe, A/B).
- **Elo-Register: NICHTS** fuer den A/B. Wird der Knopf Default, ist der Champion eine neue
  gemessene Identitaet (Feedback `measured_identity_gets_own_bxx`).

### 5. Stopp-Punkte fuer den Nutzer

- **Aufnahme ins Rezept nur bei positivem Schritt 2 UND vertretbarem Kostentor -- und das ist
  ausdruecklich Nutzer-Entscheid** (par.9 Schlusssatz).
- **Sichttor ROT: anhalten** und melden; ein Verstoss heisst, die Fuellung nimmt dem Spieler eine
  Sicherheit weg, die er hat.
- **Kostentor gerissen: anhalten**, nicht "trotzdem messen".
- **Anker-Drift ROT oder Paritaets-Fixture veraendert: anhalten**, Nutzer-Entscheid.
- **Variante A und der robuste Aggregator** (par.4.3, par.7): kein Bau ohne eigene Registrierung.
- **Kein Push, keine Loeschung** ohne pfadgenaue Freigabe.

### 6. Abhaengigkeiten und Reihenfolge

**Vorher:** Tor 1 der v29-Generation (der A/B laeuft am Champion v29-b01), und ein freies
CPU-Fenster fuer den Wheel-Bau -- nicht waehrend Erzeugung, Waechter oder Kette
(`PREREG_v29_window.md` par.4 Punkt 6). **Reihenfolge im Begleitprogramm** (par.9 Schlusssatz):
NACH der Ziehsucht-Sonde und der Mondstapel-Stufe 1, weil die beiden billiger sind; der Punkt
steht in `PREREG_v29_window.md` par.7 als Punkt 2c. **Danach:** was traegt, geht ins v30-Rezept
(`PREREG_v29_window.md` par.8 Punkt 3); faellt der Arm negativ aus, ist die Linie geschlossen und
der naechste Weg zur Tiling-Sicht ist Variante C (Encoder-Seite, par.7) -- die waere ein eigener
Arm mit Training, nicht Teil dieser Prereg.

## par.12 ZWEITER NUTZNIESSER: der Spezialfeld-Ertrag (Nutzer 2026-09-14)

Bis hierher war Variante B (Tiling im Blatt) mit der Rundenvoraussicht begruendet. Der Nutzer hat
am 2026-09-14 einen zweiten, unabhaengigen Nutzniesser benannt: *"ich denk es gehoert drafting und
tiling zusammen fuer tile yield. das eine geht nicht ohne das andere"*.

Belegt an `PREREG_special_tile_yield.md` par.2: der Ertrag einer Spezialfliese ist eine Kette --
im Drafting die Steine holen, im Tiling die anderen DREI Felder des Slots fuellen (erst dann
entriegelt `try_unlock_special`, dome.rs:139-141), dann mit einem weiteren weissen Stein
abrechnen (round_end.rs:324). Solange das Blatt VOR dem Tiling endet, kann die Suche beim Ziehen
nicht bewerten, ob eine Platte am Ende einen Slot freischaltet.

**Folge:** der offene Drafting-Hebel aus `special_tile_yield` par.4a ist ohne Variante B nicht
messbar (dort als par.11 registriert). Variante B bekommt damit einen zweiten benannten
Nutzniesser -- was nach CLAUDE.md ("Infrastruktur bewerten: Irrtumskosten, nicht Elo") die
Anforderung an einen Infrastruktur-Vorschlag ist: eine konkrete Messung, die dadurch erst
moeglich wird.

## par.13 DRITTER NUTZNIESSER: die rundenuebergreifende Tiling-Bewertung (Nutzer 2026-09-14)

Beim Durchsehen der Chip-Allokation kam die Frage auf, ob der Tiling-Solver ueber Runden hinweg
zu kurz greift -- ein vielseitiger Bonuschip jetzt verbrannt, spaeter knapp. Der Koordinator
hatte das als Architektur-Grenze beschrieben. **Nutzer-Korrektur:** *"nein er optimiert nicht nur
runden score hoff ich mal. dafuer haben wir den einfluss von value head und einhuellender
eingebaut"* -- und dann: *"doch, es wird ab punkt 33 nochmal angegriffen schaetz ich."*

**Beides trifft zu, und zusammen ergibt es den Punkt:**

* Die Mechanik IST gebaut: `envelope_tiling_w` und `envelope_tiling_value_w`
  (`net_mcts.rs:919/921`) geben dem Solver Einfluss ueber die Einhuellende und den Value-Kopf.
* **Sie steht auf 0,0 in der Champion-Spec**, also auf Default. Faktisch optimiert der Solver im
  laufenden Rezept den RUNDEN-Score.
* **W_VAL IST GEMESSEN, und zwar mit Nullbefund:** `PREREG_geometric_envelope.md` par.8.6a,
  2026-09-04, drei Arme (V 0,5 / V 1,0 / T+V) a 160 Paare am `v23-b01_brierbest`. Siege
  82:78 / 84:76 / 80:80, McNemar p 0,75 / 0,39 / 1,00, Margin und Spalten ohne Richtung.
  Verdikt dort: *"Im Tiling ist zu wenig zu entscheiden (par.3f: Fast-Gleichstaende), und der
  Entscheid liegt im Draft."* Eine Wiederholung am heutigen Netz und an der heutigen
  Basislinie ist als par.8.6b registriert (Nutzer-Auftrag 2026-09-14).
* **ZWEI KORREKTUREN AN DIESER STELLE, beide am 2026-09-14/15 vom Nutzer ausgeloest.**
  (1) Zuerst stand hier, die Mechanik habe "gemessen nicht getragen", mit Verweis auf
  `project_ownership_tiling_consumer_negative`; das war falsch zugeordnet, jene Notiz betrifft
  den OWNERSHIP-Kopf als Tiling-Konsument. (2) Daraufhin stand hier, der Knopf sei
  **"UNGEMESSEN"** -- auch das war falsch, und zwar folgenschwerer: es ist aus einer
  ERGEBNISLOSEN SUCHE geschlossen worden, nicht aus einem Beleg. Der Beleg lag in der Prereg,
  die den Knopf beherbergt, unter der Nummer des Absatzes, der hier zitiert wird (8.6 -> 8.6a).
  **Ein Nullbefund der eigenen Suche ist kein Beleg fuer Abwesenheit**; Regel 0 verlangt dann
  "ich finde keinen Beleg", nicht "es gibt keinen". Die zweite Fassung stand rund einen Tag im
  Baum und hat einen Messlauf ausgeloest, der als Erstmessung beauftragt war und eine
  Wiederholung ist.
* **Der Knopf ist also gebaut, steht auf Default und hat einmal nicht getragen.** Fuer diesen
  Absatz heisst das: Variante B greift etwas an, das in EINER Form schon gescheitert ist --
  aber in einer anderen Form als B sie waehlt (Gewicht im Solver gegen Tiling im Blatt), und
  die Begruendung des Scheiterns (zu wenig zu entscheiden im Tiling) trifft B nicht
  automatisch, weil B die ENTSCHEIDUNG verschiebt statt sie umzugewichten.
* **Variante B greift dasselbe Problem anders an:** sie rechnet das Tiling IM BLATT der Suche
  durch. Der Value-Kopf kommt dann ueber den Blattwert ins Spiel, nicht ueber einen
  Gewichtsparameter im Solver. Das ist der Unterschied zwischen "dem Solver ein Gewicht geben"
  und "die Suche das Tiling sehen lassen".

**Damit hat dieses Paket drei benannte Nutzniesser**, was nach CLAUDE.md ("Infrastruktur
bewerten: Irrtumskosten, nicht Elo") die Anforderung deutlich uebererfuellt:

1. die Rundenvoraussicht (par.7, urspruengliche Begruendung),
2. der Spezialfeld-Drafting-Hebel (par.12, Kette Drafting-Tiling-Freischaltung),
3. **die rundenuebergreifende Tiling-Bewertung** -- der Weg, auf dem der flache Gewichts-Ansatz
   gescheitert ist, hier noch einmal und mit anderer Mechanik.

**Nicht behauptet wird**, dass Variante B den Chip-Fall loest; der Solver bleibt innerhalb der
Runde exakt, und ob die Suche seine Wahl beeinflussen kann, haengt am Bau (par.4.2). Es ist ein
Nutzniesser, kein Versprechen.

## par.14 TOP-K-TILING NACH POSITIVEM VARIANTE-B-BEFUND (Nutzer-Auftrag 2026-09-15)

### 14.1 Abgrenzung: nicht Variante B ein zweites Mal

**Variante B** loest an jedem pseudo-terminalen Drafting-Blatt das Tiling beider Seiten EINMAL
mit dem bestehenden exakten, rundenscore-orientierten Loeser, zieht danach eine sichtkonforme
Fabrik-Neubefuellung und ruft das Netz auf. Sie aendert dadurch die **Bewertung einer
Drafting-Folge**, nicht die Wahl innerhalb des Tilings.

**Top-K-Tiling** waere erst der naechste Schritt: Fuer DENSELBEN Drafting-Blattzustand liefert
der Loeser mehrere strukturell verschiedene, rundenscore-nahe legale Tiling-Endzustaende. Nach
gekoppelter Neubefuellung bewertet das Netz diese Alternativen. Der Zukunftswert kann damit nur
zwischen bereits lokal plausiblen Tiling-Folgen entscheiden. Top-K aendert also die
**Tiling-Wahl selbst**, nicht bloss die Sicht des Drafting-Baums auf das eine bisherige
Tiling-Ergebnis.

Kein Kandidat ist eine andere Zugreihenfolge zum selben Endbrett. Kandidaten unterscheiden sich
am Nach-Tiling-Zustand, insbesondere bei Brett, verbrauchten Chips, Strafleiste, Markern und
den aus der legalen Ausfuehrung folgenden Pool-/Rundenende-Feldern.

### 14.2 Anlass und Hypothese

Der bestehende Loeser ist fuer den unmittelbaren Rundenscore der richtige Spezialist. Die offene
Frage ist enger: Gibt es regelmaessig mehrere lokal gleichwertige oder fast gleichwertige
Endbretter, deren Wert **nach** Tiling und Neubefuellung fuer die weitere Partie verschieden
ist? Falls ja, kann ein Netzwert dort helfen, ohne den ganzen Tiling-Aktionsraum in eine zweite
MCTS zu verwandeln.

**Hypothese:** Eine Auswahl innerhalb einer kleinen, nicht dominierten Menge exakter
Tiling-Endzustaende verbessert den Zukunftswert gegenueber dem einzelnen
Rundenscore-Optimum, ohne die unmittelbaren Tiling-Regeln oder den Policy-Aktionsraum zu
veraendern.

Das ist KEIN Vorschlag, den Rundenscore mit einem freien Value-Gewicht zu mischen. Dieser Weg
(`envelope_tiling_value_w`) ist bereits mit Nullbefund gemessen -- die MESSUNG steht in
`PREREG_geometric_envelope.md` **par.8.6a** (drei Arme, je 160 Paare), der Abschluss in
**par.8.6c**; par.8.6 ist nur der Vorschlagsabsatz. Die Unterscheidung ist hier nicht
Pedanterie: genau an dieser Stelle stand einen Tag lang "gebaut und UNGEMESSEN", weil die
Suche unter 8.6 nichts fand und daraus eine Abwesenheit gemacht wurde
(`feedback_empty_search_is_not_absence_proof`). Hier ist der Rundenscore eine Kandidatenschranke; der Netzwert waehlt nur unter den
verbleibenden Alternativen.

### 14.3 Stufe 0: Mehrdeutigkeits- und Rangsonde VOR jedem Bau

Die Sonde arbeitet auf echten Rundenende-Blattzustaenden, nach Runde stratifiziert. Sie muss
fuer jede Stellung mindestens berichten: n, Grundmenge und Einheit, Anzahl strukturell
verschiedener Kandidaten, Rundenscore-Abstand zum Optimum, Nach-Tiling-Netzwerte und deren
Rangfolge ueber gemeinsame Neubefuellungs-Stichproben.

Vor dem Bau sind vier Fragen zu beantworten:

1. **Mehrdeutigkeit:** Wie oft existiert ueberhaupt mehr als ein nicht dominierter,
   rundenscore-naher Endzustand? Existiert praktisch immer nur einer, endet der Strang ohne
   Bau.
2. **Wirkungsort:** In welchen Runden sowie bei welchen Klassen (Spezialfeld-Freischaltung,
   Chip-Verbrauch, Spalten-/Reihenabschluss) unterscheiden sich die Nach-Runden-Werte?
3. **Frueher Value:** Trifft der Netzwert auf kontrafaktischen Kandidatenpaaren die Richtung
   einer mit gemeinsamen Zufallsseeds fortgesetzten Referenz? Die Auswertung erfolgt getrennt
   fuer R1/R2, R3/R4 und R5. Ein schwacher Value in R1/R2 darf dort keine Tiling-Wahl treffen;
   er ist kein Grund, die Frage in spaeteren Runden zu verwerfen.
4. **Zwei Spieler:** Die Sonde muss die legale Reihenfolge beider Tiling-Aufloesungen und
   etwaige gemeinsame Rundenzustandsfelder pruefen. Es ist verboten, beide Seiten still mit
   demselben Skalar zu maximieren. Erst der Code-Audit entscheidet, ob die Kandidaten getrennt,
   als Kreuzprodukt oder in einer anderen legalen Best-Response-Reihenfolge zu bewerten sind.

Die Vorabsonde setzt weder K, Score-Fenster noch Stichprobenzahl willkuerlich fest. Diese drei
Kostenparameter werden aus der gemessenen Kandidatenzahl, der Rangstabilitaet und dem Anteil
betroffener Blaetter vorgeschlagen und vom Nutzer vor einem Bau entschieden.

### 14.4 Bauform, nur wenn B traegt und Stufe 0 einen Verbraucher zeigt

1. Der exakte Loeser bekommt einen **additiven** Einstieg, der bis zu K
   strukturell verschiedene Endzustaende innerhalb des beschlossenen Score-Fensters liefert.
   Der bisherige Einzelplan bleibt der Default und muss bitidentisch bleiben.
2. Jede Neubefuellungs-Stichprobe ist fuer alle Kandidaten desselben Blatts gekoppelt:
   gleicher sichtkonformer Beutel-/Turm-Zustand, gleicher zustandsgebundener Seed, nur die
   Kandidatenentscheidung unterscheidet sich. Dadurch wird Zufallsrauschen nicht als
   Tiling-Unterschied gelesen.
3. Die Auswahlmetrik wird VOR dem A/B festgelegt. Zulaessig sind nur eine Rangregel ueber den
   Mittelwert oder eine zuvor gemessene Stabilitaetsregel; ein nachtraeglich gewaehlter
   Risikoabschlag ist nicht zulaessig.
4. Die Anwendung ist rundenabhaengig: Stufe 0 legt die frueheste Runde fest, ab der die
   Netzrangfolge ausreichend aufloesend ist. Vorher bleibt der exakte Einzelplan aktiv oder
   eine separat registrierte, rein strukturelle Dominanzregel entscheidet.
5. Kein neuer Policy-Kopf, keine Kreuzprodukt-Action-ID und kein neues Trainingsziel sind Teil
   dieses Baus. Es ist ein Blatt-Selector ueber legale, bereits exakt erzeugte Endzustaende.

### 14.5 Tore, Lesart und Stopp-Punkte

* **Abhaengigkeit:** Variante B besteht Kosten-, Sicht- und Arena-Tor. Ein negativer B-Befund
  schliesst Top-K hier, weil ohne die Nach-Tiling-Sicht kein sauberer Verbraucher bleibt.
* **Korrektheit, KORRIGIERT 2026-09-16 nach par.15 B3 (am Code nachgeprueft):** die
  Bitidentitaet von K=1 zu Variante B ist KEINE Voraussetzung mehr, sondern ein zu ZEIGENDES
  Tor mit eigenem Test. Grund: der Bestand loest das Tiling SCHRITTWEISE auf
  (`round_transition.rs:152` ruft `best_first_step_exact` in einer Schleife, mit
  `pi = state.current_player`, also mit Spielerwechsel zwischen den Schritten), und in Runde 5
  ist das ein anderer Algorithmus als sonst (`tiling_solver.rs:1692-1697` verzweigt bei
  `round_number >= 5` auf `best_first_step_round5`). Dieser Zweig baut zwar selbst schon ueber
  `top_k_tilings(state, pi, MAX_TILING_LEAVES)` und maximiert Punkte plus Endwertung
  (`:829-838`) -- **gibt aber nur `best.first_step` zurueck**: der Plan wird nach JEDEM Schritt
  neu gerechnet. Ein K=1-Kandidat aus `top_k_tilings` ist dagegen der punktemaximale VOLLPLAN
  EINES Spielers, in einem Stueck angewendet. Dass beide denselben Endzustand erreichen, ist
  nicht durch Konstruktion gegeben; es kann zutreffen, muss aber gezeigt werden. Bis dahin gilt
  der Schrittpfad als Default und Top-K als getrennter Zweig. Champion-Paritaet, Anker-Drift und
  Anker-Konservierung muessen unveraendert gruen sein.

  Der Test dazu ist billig und braucht kein Netz: fuer eine Stichprobe von Tiling-Zustaenden je
  Runde beide Wege fahren (Schrittschleife gegen K=1-Vollplan) und die Nachzustaende
  vergleichen -- getrennt ausgewiesen fuer Runde 5 und Runden 1-4, weil nur R5 den
  abweichenden Algorithmus nimmt. Faellt der Vergleich in R1-4 gruen und in R5 rot, ist die
  Stelle benannt statt nur der Verdacht.
* **Kosten, KORRIGIERT 2026-09-16 nach par.15 B5:** die Schwelle wird NICHT erst aus Stufe 0
  vorgeschlagen, sondern ist hiermit vorab gesetzt -- **25 Prozent Aufschlag auf die Wanduhr je
  Partie**, dieselbe wie in par.4.1, par.9 und par.10. par.4.1 haelt ausdruecklich fest, dass
  diese Zahl uebernommen und nicht neu gesetzt ist, "damit die Schwelle nicht je Arm passend
  gewaehlt wird"; eine erst nach der Sonde vorgeschlagene Schwelle waere genau das.
  **Beide Bezuege werden ausgewiesen**, weil ein einzelner den Nenner verschiebt: der Aufschlag
  gegen den BESTAND (kumulativ mit Variante B) entscheidet das Tor, der Aufschlag gegen
  Variante B ALLEIN steht daneben, damit sichtbar bleibt, welcher Teil der Kosten von welcher
  Stufe kommt. Gemessen wird zusaetzlich der Anteil betroffener Blaetter.
* **Arena:** nur mit demselben Netz und sonst identischem Spec gegen Variante B, zwei Seeds,
  je 200 Paare, Blockgroesse 5, ohne Frueh-Stopp und mit Logs. Die sechs Standard-Kennzahlen
  sind Pflicht; besonders Punkte je Wertungsplatte, Spalten, Spezialfelder und Chip-Verbrauch
  werden getrennt ausgewiesen.
* **Stopp:** keine Mehrdeutigkeit, keine rundenweise Rangaufloesung oder ein gerissenes
  Kostentor beendet den Strang vor dem Arena-A/B. Eine Verbesserung nur in einer
  nachtraeglich gewaehlten Kandidatenklasse gilt nicht.

Ein positiver A/B macht Top-K zu einem Rezept-Kandidaten, nicht automatisch zum Default. Die
Aufnahme bleibt ein Nutzer-Entscheid; die Entfernung eines durch Top-K ersetzten Proxys folgt
getrennt nach `PREREG_minimal_strength_core.md` par.4.

## par.15 REVIEW (2026-09-16, Subagent)

Fachliches Review von par.14 (Top-K-Tiling), Kontext par.7/9/10/13. Kein Bau, keine Messung;
alle Code-Stellen in dieser Sitzung am Baum nachgesehen.

**B1. Top-K ist im Kern bereits gebaut und im gespielten Zug AKTIV, nicht "erst der naechste
Schritt" (14.1).** `top_k_tilings` liefert bis zu k strukturell verschiedene Vollabschluesse
(`tiling_solver.rs:768-795`), `NET_TILING_TOPK = 12` (`:863`), `NET_TILING_TIEBREAK_ENABLED =
true` (`:858`), der netz-gefuehrte Stichentscheid laeuft in den Runden 2-4 (`:1603-1610`) ueber
`select_best_tiling_candidate` (`:944-964`, Modus 0 `punkte * P(Sieg)`, Modus 1 reines P(Sieg)
per `MOSAIC_TILING_SELECT`), und die Huellen-Variante K3 (d) nutzt dieselbe Kandidatenliste
(`:1620-1679`). Vorschlag: 14.1 auf den TATSAECHLICHEN Unterschied umschreiben (neu waere der
ORT im Suchblatt und die GEKOPPELTE Neubefuellung, nicht der Selektor als solcher), sonst
beauftragt der Absatz einen vorhandenen Mechanismus ein zweites Mal.

**B2. Stufe 0 (14.3) beauftragt eine Erhebung, die es zum Teil schon gibt.**
`tools/tiling_candidate_spread.py` und `evaluations/artifacts/tiling_candidate_spread_b01_v3.json`
(k = 12) berichten: n = 400 Stellungen, Grundmenge Tiling-Stellungen aus `frozen_eval_set`,
Einheit Stellungen mit mehr als einem Kandidaten = 225 (56,3 Prozent), je Runde 20/48/71/73/13;
Value-Spreizung Median 0,0653 (IQR 0,028-0,110); die Multiplikation aendert die Wahl in 83 von
192 Stellungen der Runden 2-4. Vorschlag: diese Sonde als Ausgangspunkt nennen und nur die
wirklich fehlenden Groessen (gekoppelte Neubefuellung, Rangstabilitaet, Zwei-Spieler-Reihenfolge)
ergaenzen, statt eine Neuerhebung zu registrieren (CLAUDE.md: erst in vorhandenen Skripten
nachsehen).

**B3. "K=1 ist bitidentisch zu Variante B" (14.5) ist eine Behauptung, der der Bestand
widerspricht.** `resolve_to_pre_chance` loest das Tiling SCHRITTWEISE ueber
`best_first_step_exact` mit wechselndem `current_player` auf (`round_transition.rs:137-171`,
Aufruf `:152`), und `best_first_step_exact` ist in Runde 5 ein anderer Algorithmus
(`best_first_step_round5` ueber `top_k_tilings` plus Endwertung, `tiling_solver.rs:1689-1698`
und `:828-839`), sonst `best_first_step_inner`. Ein K=1-Kandidat aus `top_k_tilings` ist
dagegen der punktemaximale VOLLPLAN EINES Spielers; dass die Schrittschleife denselben
Endzustand erreicht, ist nicht durch Konstruktion gegeben. Vorschlag: die Bit-Identitaet als zu
ZEIGENDES Tor mit eigenem Test formulieren oder den Schrittpfad ausdruecklich als Default
festschreiben und Top-K als getrennten Zweig.

**B4. Die Kandidaten-Definition in 14.1 ist weiter als die gebaute Dedup-Signatur.**
`tiling_outcome_signature` (`tiling_solver.rs:646-671`) unterscheidet nur die 36
Kuppel-Belegungen plus die verbliebenen Bonuschips; Strafleiste, Marker und die Pool-/
Rundenende-Felder, die 14.1 ausdruecklich als unterscheidend nennt, fallen zusammen. Vorschlag:
entweder die Signatur im Bau erweitern (dann faellt B3 erst recht) oder 14.1 auf die gebaute
Signatur einschraenken und die Erweiterung als eigenen Punkt fuehren.

**B5. Das Kostentor von 14.5 verlaesst die Disziplin, die par.4.1 aufgestellt hat.** Dort steht
ausdruecklich, die 25 Prozent seien uebernommen und nicht neu gesetzt, "damit die Schwelle nicht
je Arm passend gewaehlt wird"; 14.5 laesst die Schwelle erst NACH Stufe 0 vorschlagen und misst
zusaetzlich gegen Variante B statt gegen den Bestand, also mit verschobenem Nenner. Vorschlag:
die Schwelle VOR Stufe 0 nennen und beide Bezuege ausweisen (Aufschlag gegen Bestand, kumulativ
mit B, und Aufschlag gegen B allein).

**B6. Der gesuchte Nutzen liegt nahe an der Aufloesungsgrenze, und das steht nicht im Absatz.**
Der naechstliegende Vorgaenger ist geschlossen: `PREREG_geometric_envelope.md` par.8.6a/8.6c,
vier Arme, 80:80 und 81:79, p 1,000; die gemessene Value-Spreizung unter den Kandidaten ist
Median 0,0653 (B2), und eine Arena mit 2 x 200 Paaren loest rund 6 Prozentpunkte auf (CLAUDE.md,
"Infrastruktur bewerten": 5,75 Prozentpunkte Streuung bei n = 400 fuer identische
Konfiguration). Vorschlag: Stufe 0 muss eine VORAB bezifferte Mindest-Rangaufloesung liefern
(Anteil der Blaetter mit ueber gekoppelte Stichproben stabilem Netz-Rang), sonst kauft der A/B
einen Zufallsbefund.

**B7. Die vorregistrierte Lesart kennt "traegt" und "traegt nicht", aber nicht "schadet".** 14.5
listet Stopp-Gruende (keine Mehrdeutigkeit, keine Rangaufloesung, Kostentor) und den positiven
A/B; ein signifikant NEGATIVER A/B hat keine Lesart, obwohl genau der in dieser Kampagne
zuletzt zweimal eingetreten ist (`PREREG_round_estimate_leaf_term.md` par.7c/7d mit 20:60 und
45:85; `PREREG_moon_stack_order.md` par.12.6, wo der ablatierte Kopf besser war). Vorschlag:
dritte Lesart eintragen, samt der Aussage, die ein Schaden ueber den Rundenscore-Solver machen
wuerde.

**B8. Zitat-Praezision und Zeilendrift.** 14.2 verweist auf "`PREREG_geometric_envelope.md`
par.8.6", obwohl derselbe Absatz par.13 dieser Datei bereits als Nummernfalle behandelt (8.6 ->
8.6a) und der Strang seit 2026-09-15 als 8.6c geschlossen ist; ausserdem ist die in par.8
korrigierte Aufrufstelle erneut gewandert (Konstante `net_mcts.rs:95` stimmt, die Aufrufstelle
liegt heute bei `net_mcts.rs:3334-3335`, nicht bei `:2329`, was auch der AGENTEN-AUFTRAG P1
weitertraegt). Vorschlag: beide Verweise beim naechsten Anfassen praezisieren.

**Gesamturteil:** Die Frage von par.14 ist echt und mit einer Sonde beantwortbar, aber der
Absatz beauftragt in weiten Teilen einen Mechanismus, der bereits gebaut, aktiv und einmal
gemessen ist; ohne die Korrektur von B1-B3 und ohne vorab bezifferte Kosten- und
Rangschwellen ist er nicht ausfuehrbar.


### 16.8 NACHTRAG des Koordinators: die Stichprobe muss JE RUNDE geplant werden (Antwort auf B2)

par.15 B2 hat gewarnt, dass Stufe 0 eine Erhebung beauftragt, die es zum Teil schon gibt; par.16
nennt sie trotzdem nicht. Nachgeholt, samt der Folge fuer den Laufbefehl.

**Vorhanden ist `tools/tiling_candidate_spread.py`**, Artefakt
`evaluations/artifacts/tiling_candidate_spread_b01_v3.json` vom 2026-09-02. Die Zahlen sind am
Artefakt selbst nachgeprueft (nicht aus dem Review uebernommen): n = 400 Stellungen, Grundmenge
Tiling-Stellungen aus `frozen_eval_set` (v3), Einheit Stellungen; `n_multi` = 225, also 56,3
Prozent mit mehr als einem Kandidaten bei k = 12.

**Was davon fuer par.16 GILT und was NICHT:**

* **Netzunabhaengig und damit uebertragbar:** die Kandidatenzahl je Stellung. Sie kommt aus
  `tiling_candidates_json`, also aus dem SPIEL, nicht aus einem Netz.
* **Netzabhaengig und damit NICHT uebertragbar:** `value_spread_median` 0,0653 (IQR
  0,0284-0,1096) und `mult_changes_choice` 83 von 192. Das Artefakt traegt `"model":
  "v23-b01_brierbest"` -- ein Stand von vor sechs Generationen. Diese beiden Zahlen sind hier
  KEINE Vorabinformation, sondern hoechstens eine Groessenordnung.

**Die Folge, und das ist der eigentliche Nachtrag:** die Verteilung der mehrdeutigen Stellungen
ueber die Runden ist stark ungleich -- 20 / 48 / 71 / 73 / 13 fuer R1 bis R5. In **Runde 1 sind
nur 5,0 Prozent** der Stellungen ueberhaupt mehrdeutig (20 von 400), in R5 nur 3,3 Prozent. Ein
Lauf mit `--max-positions 200` ueber alle Runden trifft in R1 also rund **zehn** auswertbare
Faelle, nicht zweihundert. Die in 16.4 vorab bezifferte Schwelle (Wilson-Untergrenze > 0,50)
ist bei n = 10 nicht erreichbar, egal wie das Netz rangiert.

**Deshalb verbindlich fuer den Volllauf:** die Stellungen werden **je Runde gezogen und je Runde
ausgewiesen**, mit einem Mindest-n je Runde statt eines Gesamtdeckels; Runden, die ihr Mindest-n
nicht erreichen, werden als "nicht entschieden" berichtet und NICHT in eine Gesamtquote
eingerechnet. Die Sonde zaehlt je Datei UND Runde (16.6) -- der Deckel je Runde ist also schon
gebaut, er muss nur gesetzt werden. Ohne diesen Nachtrag waere R1 mit einer Zahl heimgekommen,
die wie ein Befund aussieht und keiner ist -- genau die Falle, gegen die 16.4 die Schwelle
vorab beziffert hat.

### Nachpruefung der Review-Befunde durch den Koordinator (2026-09-16)

Regel 0: Agenten-Befunde sind Behauptungen. Selbst am Code nachgefahren, mit Prueffolge:

| Befund | Stand | Prueffolge |
| --- | --- | --- |
| B1 (Top-K ist gebaut und aktiv) | **BESTAETIGT** | `tiling_solver.rs:1595-1612` (rundenabhaengige Wertung), `NET_TILING_TIEBREAK_ENABLED` (`:858`), `NET_TILING_TOPK = 12` (`:863`) |
| B3 (K=1 nicht bitidentisch) | **BESTAETIGT, und schaerfer** | `round_transition.rs:152`, `tiling_solver.rs:1692-1697`, `:829-838`. Siehe 14.5, dort korrigiert |
| B4 (Dedup-Signatur enger als 14.1) | **BESTAETIGT, und schaerfer** | `tiling_solver.rs:646-671` |
| B2 (Sonde existiert schon) | **BESTAETIGT**, Zahlen am Artefakt nachgeprueft | `tiling_candidate_spread_b01_v3.json`; abgearbeitet in 16.8 |
| B5 (Schwelle je Arm gewaehlt) | **BESTAETIGT** | par.4.1 gegen 14.5; abgearbeitet in 14.5 |
| B6, B7 (Aufloesungsgrenze, Ausgang "schadet") | beantwortet in par.16.5 | -- |
| B8 (Zeilendrift, Zitat 8.6) | **BESTAETIGT** | `net_mcts.rs:95` stimmt, `:2329` ist heute ein Struct-Feld, die Stelle liegt bei `:3334`; beide Verweise auf SYMBOLNAMEN umgestellt, `par.8.6` auf `8.6a`/`8.6c` praezisiert |

**Damit sind alle acht Befunde abgearbeitet.** Keiner war falsch; zwei (B3, B4) waren im
Gegenteil zu schwach formuliert. Der Agent hat sauber gearbeitet -- was fehlte, war der
Anschluss: B2 hat vor einer Neuerhebung gewarnt, und die Sonde aus par.16 nennt die vorhandene
trotzdem nicht. Beim Beauftragen des Baus gehoert der Review also MIT in den Auftrag, nicht nur
die Aufgabe.

**Wo die Nachpruefung ueber den Befund hinausging:**

* **B3:** der Agent nannte den Unterschied "Schrittschleife gegen Vollplan". Dazu kommt, dass
  `best_first_step_round5` auch INNERHALB des R5-Zweigs nur `best.first_step` zurueckgibt --
  der Vollplan wird also nach jedem einzelnen Schritt neu gerechnet, mit einem moeglichen
  Gegnerzug dazwischen. Der Unterschied ist damit nicht nur "andere Berechnung desselben", er
  ist struktureller Art.
* **B4:** die Signatur unterschlaegt nicht nur Strafleiste, Marker und Pool-Felder, sondern
  auch die FARBE: `fill` haelt je Feld nur `placed_color.is_some()`, also belegt ja/nein
  (`:653`). Zwei Plaene, die dieselben Felder mit verschiedenen Farben belegen, sind fuer die
  Deduplizierung identisch. **Ob das ueberhaupt vorkommen kann, ist eine REGELFRAGE** (hat
  jedes Kuppelfeld eine feste Farbe?) und hier ausdruecklich NICHT beantwortet -- nach Regel 0
  gehoert sie ins `engine_manual.md` oder in den Code, nicht in eine Ableitung. Wer B4
  abarbeitet, klaert das zuerst: ist die Farbe feldfest, ist die Verkuerzung verlustfrei und
  B4 schrumpft auf die vier genannten Felder.

## par.16 STUFE 0 GEBAUT: die Counterfactual-Ranking-Sonde (Nutzer-Auftrag 2026-09-16)

Fuehrt par.14.3 aus und beantwortet dabei B6 (vorab bezifferte Mindest-Rangaufloesung) und B7
(dritte Lesart "schadet"). Der Absatz haengt HIER und nicht in einer neuen Prereg, weil die
Frage schon hier wohnt: par.14.3 beauftragt genau diese Erhebung, par.15 B2/B6/B7 nennen genau
die Luecken, die sie schliessen soll. Eine eigene Datei haette die Ergebnisse von ihrem
Vorschlagsabsatz getrennt.

### 16.1 Die Frage, enger als in par.14.3

> Trifft der Value-Kopf die Reihenfolge mehrerer lokal plausibler Tiling-Plaene, und ab welcher
> Runde ist er dabei verlaesslich genug, um eine exakte lokale Entscheidung (mehr Rundenpunkte)
> zu ueberstimmen?

Die zweite Haelfte ist der Teil, den der Bestand NICHT misst.
`tools/tiling_value_reference_main.py:146` schneidet auf `tied = [c for c in cands if
c["points"] == top]` zu, prueft also ausschliesslich PUNKTGLEICHE Abschluesse. Genau die
Ueberstimmung eines Punktvorsprungs ist damit nie gemessen worden, obwohl der gespielte Zug sie
zulaesst: `select_best_tiling_candidate` (`tiling_solver.rs:944-964`, Modus 0) waehlt nach
`punkte * P(Sieg)`, ein Produkt, das einen Punkt kippen KANN.

Und der Zweig ist AKTIV: `NET_TILING_TIEBREAK_ENABLED = true` (`tiling_solver.rs:858`),
`NET_TILING_TOPK = 12` (`:863`), Anwendung in den Runden 2-4 (`:1603-1610`). Runde 1 ist dort
ausdruecklich ausgeschlossen (`:1407-1409`).

### 16.2 Wahrheitsquelle: (c) Tiefensuche nach gekoppelter Neubefuellung, in ZWEI Guetegraden

Die Wahl ist der Punkt, an dem die Sonde steht oder faellt, deshalb die drei Kandidaten
einzeln, mit Pruefstelle:

**(a) Exakter Rundenscore am Ende der FOLGENDEN Runde faellt aus, weil er nicht berechenbar
ist.** Nach `advance_after_tiling_json` (`lib.rs:1930-1944`) steht der Zustand im DRAFTING der
naechsten Runde. Was diese Runde einbringt, haengt daran, wie BEIDE Seiten sie draften; es gibt
aber keinen Python-Einstieg, der von einem BELIEBIGEN Zustand aus weiterspielt.
`PyGame::new` (`py.rs:102`) und `RefereeGame::new` (`referee.rs:465`) starten beide nur eine
frische Partie, und `heuristic_arena_choice_state_json` (`lib.rs:1384`) liefert eine AKTION
ohne Folgezustand. Die exakt berechenbare Restgroesse waere `solve_round_final_score` (ueber
`scoring_shaping_e_json`, `lib.rs:1644-1645`), aber direkt nach einem Rundenuebergang sind die
Musterreihen leer, sie ist dort rund 0. Was bleibt, waere der Rundenscore der AKTUELLEN Runde
(`points` aus `tiling_candidates_json`, `lib.rs:1907`) - das ist die lokale Entscheidung selbst,
also die getestete Groesse, nicht ihre Wahrheit.

**(b) Partieausgang aus dem Korpus faellt aus, weil die Kontrafaktischen keine Etikette
haben.** Fortgesetzt wurde genau EIN Plan je Stellung. Die uebrigen K-1 sind per Konstruktion
unbeschriftet. Dazu kommt, dass der fortgesetzte Plan von dem Kriterium gewaehlt wurde, das hier
geprueft wird (`tiling_solver.rs:944-964`) - ein Vergleich haette die Auswahl im Zaehler.

**(c) Tiefensuche nach gekoppelter Neubefuellung wird genommen** (Vorbild und einziger gebauter
Weg: `tools/tiling_value_reference_main.py:159`,
`mr.net_search_state_json(nxt, ref_path, sims, 1.5, seed)`), aber mit AUSGEWIESENEM Guetegrad,
weil sie nicht ueberall gleich unabhaengig ist:

* **Grad EXAKT, nur Runde-4-Stellungen.** Ein Runde-4-Tiling landet nach einer Neubefuellung im
  Runde-5-Drafting. Dort antwortet der Alpha-Beta-Endspielsolver (`round5.rs`), nicht das
  Value-Kopf-Blatt: `net_search_state_json` traegt dann KEIN `root_value`, und der
  `mcts_q`-Wert des gewaehlten Zugs IST der Alpha-Beta-Wurzelwert.

  **Am Code nachgeprueft (2026-09-16, Koordinator), Kette vollstaendig:**
  `net_mcts.rs:6032-6062` schneidet Runde 5 vor dem Baum ab und holt `root_q` separat aus
  `round5::choose_action_with_analysis`, Feld `mcts_q` des mit `chosen` markierten Zugs;
  `round5.rs:180-187` schaltet den Solver ohne gesetztes `MOSAIC_R5_NET_SOLVER` EIN (Default
  `true`), die Sonde muss den Knopf also nicht setzen, aber auch nicht auf `0` finden.
  Entscheidend war die eine Stelle, an der der Verdacht der Zirkularitaet haette wieder
  hereinkommen koennen: der Kommentar an `net_mcts.rs:6039-6047` nennt fuer den Fall der
  Budget-Ueberschreitung einen Rueckfall auf einen "billigen `leaf_value`-Ersatzwert".
  `round5.rs:357-359` zeigt, dass dieser Ersatzwert `player_total_exact(perspective) -
  player_total_exact(1 - perspective)` ist -- eine EXAKTE Punktezaehlung, kein Netz. Damit ist
  der R4-Zweig auf seinem GANZEN Pfad wertkopf-frei, auch dort, wo das Knotenbudget
  (`NODE_BUDGET`) nicht reicht; die Uebernahme aus
  `tools/tiling_value_reference_main.py:162-173` war richtig, stand aber bis hierher ohne
  eigene Pruefstelle. In dieser Klasse ist die Wahrheit NICHT zirkulaer.

  Die Sonde protokolliert das Fehlen von `root_value` weiter mit -- nicht mehr als Ersatz fuer
  diese Pruefung, sondern als LAUFZEIT-Waechter: faellt der Grad EXAKT in einem kuenftigen Lauf
  still auf `net_search` zurueck (weil jemand den Knopf gesetzt oder `round5::applies`
  verschoben hat), faellt es im Artefaktfeld `ref_grade` auf.
* **Grad NETZ, Runden 1-3.** Dort bleibt nur eine Netz-Suche mit einem UNABHAENGIGEN Gewichts-
  satz. Unabhaengig in den GEWICHTEN, aber NICHT in der ART: das Blatt ist wieder ein
  Value-Kopf, und in Runde 1 ist genau der das geprueft schwache Organ
  (`PREREG_bootstrap_horizon.md`, `project_phase0_value_diagnosis`). Ein positives R1-Ergebnis
  dieser Sonde belegt deshalb hoechstens UEBEREINSTIMMUNG zweier Wertkoepfe, keine Richtigkeit.
  Das ist vorab festgehalten, damit es hinterher nicht anders gelesen wird.

**Der eingebaute Selbsttest, ohne den Grad NETZ wertlos waere** (Bauform aus
`tools/probes/return_order_sensitivity_r1.py:16-22`): die Referenz wird je Kandidat mit M
gekoppelten Neubefuellungen erhoben, und ihre EIGENE Rangstabilitaet ueber diese M Ziehungen
wird berichtet. Kippt das Vorzeichen der Referenz-Differenz ueber ihre eigenen Ziehungen, ist
die Runde mit dem verfuegbaren Instrument NICHT beantwortbar, und die Sonde sagt das, statt eine
Trefferquote gegen Rauschen auszuweisen.

**Gekoppelt heisst hier: gleicher Seed, nicht gleicher Beutel.** `advance_after_tiling_json`
behauptet in seiner Doku (`lib.rs:1926-1929`) "der Nachfuell-Wurf ist dann identisch, der
einzige Unterschied ist das Brett". Das ist eine NAEHERUNG: verschiedene Tiling-Plaene legen
verschieden viele Steine in den Turm, und `tiling_candidates_json` gibt das MASKIERTE
`state_to_json` zurueck (`lib.rs:1913`), das `json_to_state` je Seed neu determinisiert. Die
Kopplung ist damit Seed-Kopplung, keine Beutel-Identitaet. Restunterschied unbekannt; er geht in
die Rangstabilitaet ein und wird dort sichtbar.

### 16.3 Kennzahlen, je mit n, GRUNDMENGE und EINHEIT

Die Sonde berichtet je Runde getrennt (R1, R2, R3, R4) und zusaetzlich gepoolt:

1. **M1 Mehrdeutigkeit** - n = gescannte Stellungen, Grundmenge = Tiling-Stellungen der Runden
   1-4 aus Korpus-Records (`phase == "tiling"`), Einheit = Stellungen. Berichtet Anteil mit >= 2
   strukturell verschiedenen Kandidaten und Median der Kandidatenzahl.
2. **M2 Richtungstreffer** - n = Kandidaten-PAARE, Grundmenge = Paare aus Stellungen mit >= 2
   Kandidaten, Einheit = Paare. `sign(dValue) == sign(dReferenz)`, exakter Binomialtest gegen
   50 Prozent, getrennt nach Punktabstand `dpoints == 0` und `dpoints != 0`.
3. **M3 Rangstabilitaet der Referenz** - n = Paare, Grundmenge = Paare, Einheit = Paare. Anteil
   der Paare, deren Referenz-Vorzeichen ueber ALLE M gekoppelten Neubefuellungen gleich ist.
4. **M4 Ueberstimmung** - n = Paare mit `dpoints != 0`, Grundmenge = ebendiese, Einheit = Paare.
   Wie oft kippt `punkte * P(Sieg)` die Punkte-Reihenfolge tatsaechlich, und wie oft ist ein
   Kippen richtig (Vorzeichen der Referenz). Das ist die Kennzahl, die den AKTIVEN Zweig
   `tiling_solver.rs:1603-1610` beurteilt.
5. **M5 Aggregator-Vergleich** - dieselbe Grundmenge wie M2, dreimal ausgewertet: Mittelwert
   ueber die M Ziehungen, Worst Case (unguenstigste Ziehung fuer den netz-bevorzugten Plan), und
   auf M3-stabile Paare eingeschraenkt. Beantwortet par.14.3 Frage "Mittelwert, Worst-Case oder
   Rang-Stabilitaet".
6. **M6 Fall-Klassen** - n = Paare, Grundmenge = Paare, Einheit = Paare. Klassifiziert ueber den
   EXAKTEN Differenzvektor der Endwertung (`end_scoring_from_state_json`, `lib.rs:1474`, Details
   je Kriterium) plus Strafleisten- und Chip-Differenz aus dem Spieler-JSON. Klassen:
   Spezialfeld, Chip, Spalte, lange Reihe, sonstige.

### 16.4 Mindest-Rangaufloesung, VORAB beziffert (Antwort auf B6)

Eine Runde gilt nur dann als "der Netzwert darf dort waehlen", wenn BEIDE Schwellen halten:

* **(i)** untere Grenze des 95-Prozent-Wilson-Intervalls der M2-Trefferquote > 0,50;
* **(ii)** M3-Stabilitaet >= 0,60.

Die 0,60 ist a priori gesetzt und NICHT aus den Daten: bei M = 6 gekoppelten Ziehungen zeigt ein
Paar mit reinem Rausch-Vorzeichen mit Wahrscheinlichkeit 2 * (1/2)^6 = 0,031 volle Einigkeit.
0,60 liegt rund 19-fach ueber diesem Rauschboden. Wer M aendert, muss die Schwelle mit dem
Rauschboden mitziehen und das hier eintragen.

### 16.5 LESART VORAB, alle vier Ausgaenge

1. **TRAEGT** (beide Schwellen aus 16.4 halten, in R2-R4 bereits bei `dpoints != 0`): der
   aktive Zweig ist in dieser Runde gerechtfertigt, und par.14.4 Punkt 4 bekommt diese Runde als
   frueheste. Ein Bau bleibt trotzdem an Variante B gebunden (par.14.5).
2. **TRAEGT NICHT** (Trefferquote nicht von 50 Prozent unterscheidbar, oder M3 < 0,60): der
   Netzwert darf dort nicht waehlen. Fuer R1 ist das der erwartete Ausgang und nur eine
   Bestaetigung des bestehenden Ausschlusses (`tiling_solver.rs:1407-1409`); fuer R2-R4 ist es
   ein Befund GEGEN den heute laufenden Zweig und geht als solcher in STATUS.md.
3. **SCHADET** (obere Grenze des 95-Prozent-Intervalls < 0,50, also systematisch FALSCHE
   Rangfolge): dann kauft `punkte * P(Sieg)` in dieser Runde nicht Rauschen, sondern
   Verschlechterung. Registriert wird dann der Vorschlag, `NET_TILING_TIEBREAK_ENABLED`
   abzuschalten oder sein Rundenfenster zu verengen - Nutzer-Entscheid, kein stiller Eingriff,
   und mit Anker-Invarianz-Pruefung, weil es Engine-Verhalten aendert (CLAUDE.md, Abschnitt
   "Nach jeder Engine-Aenderung"). Diese Lesart steht hier, weil in dieser Kampagne zweimal ein
   Falsifikator nur "traegt"/"traegt nicht" kannte, waehrend das Ergebnis "schadet" war
   (par.15 B7).
4. **NICHT MESSBAR** (die Referenz ist in dieser Runde selbst nicht rangstabil, M3 nahe dem
   Rauschboden): die Runde bleibt mit dem heutigen Instrument offen. Was dann fehlt, ist
   benannt: ein additiver Engine-Einstieg, der von einem BELIEBIGEN Zustand aus ausspielt
   (heute nicht vorhanden, siehe 16.2 (a)). Erst damit waere ein wertkopf-freier Ausgang als
   Wahrheit erreichbar.

**Stopp vor allem anderen:** faellt M1 so aus, dass praktisch nie mehr als ein Kandidat
existiert, endet der Strang ohne Bau (par.14.3 Frage 1) - unabhaengig von M2.

### 16.6 Bauform

`tools/probes/counterfactual_tiling_ranking.py`. Liest Korpus-Records ueber `corpus_io`,
erzeugt Kandidaten mit `mr.tiling_candidates_json`, bewertet sie mit EINER wiederverwendeten
`onnxruntime.InferenceSession` auf dem NACH-Tiling-Zustand (das ist der Zustand, den
`select_best_tiling_candidate` sieht, `tiling_solver.rs:951` - die Sonde muss denselben
bewerten), setzt jeden Kandidaten mit `mr.advance_after_tiling_json` ueber M gekoppelte Seeds
fort und erhebt dort die Referenz mit `mr.net_search_state_json` und einem ZWEITEN Netz.
Fortschrittszeilen mit `flush=True`, `laufzeit`-Block im Artefakt
(`evaluations/artifacts/counterfactual_tiling_ranking.json`).

### 16.7 STAND 2026-09-16: gebaut und trocken geprueft, VOLLLAUF STEHT AUS

`tools/probes/counterfactual_tiling_ranking.py` liegt im Baum und laeuft
Ende-zu-Ende. Der Volllauf ist NICHT gefahren: die b04-Kette
(`tools/night_v29_b04_moon_played.sh`) belegte die Maschine durchgehend
(Prozessabfrage 16:05 und 16:20, PID 7416, CPU 361 s bzw. 977 s), und eine Sonde
dieser Art ist CPU-Arbeit (CLAUDE.md, "Messungen laufen EXKLUSIV"). Es gibt
deshalb bis hierher KEIN Ergebnis zur Frage aus 16.1, nur einen gepruefte
Apparat.

**Was der Trockenlauf belegt** (n = 3 Stellungen je Lauf, Grundmenge
Tiling-Stellungen aus `data/selfplay_v28-b02-policy_*.pkl`, Einheit Stellungen;
sims = 20, M = 4, max-cands = 3, also AUSDRUECKLICH keine Aussage ueber die
Sache selbst):

1. Die Kette Korpus-Record -> `tiling_candidates_json` -> Netzwert auf dem
   Nach-Tiling-Zustand -> `advance_after_tiling_json` -> Referenz -> Paar-Statistik
   laeuft fehlerfrei durch (Fehler 0).
2. **Der Guetegrad EXAKT aus 16.2 existiert wirklich.** Im Lauf mit
   `--rounds 4` meldet die Sonde `ref_grade: {"exact_ab": 5}` fuer alle
   5 Paare: `root_value` fehlt dort, die Referenz kommt aus dem
   `mcts_q` des gewaehlten Zugs, also vom Runde-5-Alpha-Beta. In den Laeufen
   mit `--rounds 1,2` steht durchgehend `net_search`. Die Zweiteilung aus 16.2
   ist damit nicht nur behauptet, sondern im Instrument sichtbar.
3. **Zwei Instrumentenfallen sind im Bau schon eingetreten und behoben**, beide
   waeren still falsch gelaufen:
   * Die Geometrie-Groessen (`col_fill`, `row_fill`, `special_total`) haengen
     unter `players[i].score_geo`, nicht flach am Spieler, und `col_f_max` ist
     die KAPAZITAET je Spalte, nicht ihr Fuellstand. Flach gelesen liefert
     `.get()` ueberall `None` - die Fall-Klassen waeren sang- und klanglos alle
     "sonstige" geworden.
   * Ein gemeinsamer Deckel je Datei erschoepft sich in Spielreihenfolge, bevor
     Runde 4 drankommt (erster Trockenlauf: 6 R1-Stellungen, 1 R2-Stellung,
     0 R4-Stellungen). Der Deckel zaehlt jetzt je Datei UND Runde. Dieselbe
     Falle hat `tools/tiling_value_reference_main.py:68-72` schon einmal
     getroffen.
4. **Kostenweiche:** der Einzel-Einstieg `net_search_state_json` laedt das ONNX
   bei jedem Aufruf neu und kostete im ersten Trockenlauf rund 3 s je
   Auswertung bei 20 Sims, also fast reine Ladezeit (2 Stellungen, 8
   Auswertungen, 26 s Wanduhr). Die Sonde nutzt deshalb
   `net_search_states_json_batch` (`lib.rs:1100-1117`): EIN Ladevorgang je
   Stellung statt einer je Auswertung. Danach 3,4 s je Stellung bei denselben
   20 Sims (n = 3 Stellungen, `laufzeit.s_je_stellung` im Artefakt).

**UNGEMESSEN und deshalb hier nicht beziffert:** was der Volllauf bei den
registrierten Einstellungen (sims = 400, M = 6, max-cands = 4) kostet. Die
Trockenzahl steht bei 20 Sims und M = 4; sie hochzurechnen waere genau die
Schaetzung, die CLAUDE.md ("Laufzeiten messen, nicht schaetzen") verbietet. Der
erste Volllauf misst sie und traegt sie in seinen `laufzeit`-Block ein.

**Ebenfalls offen, weil nicht gemessen:**
* M1 auf einer tragfaehigen Grundmenge, also der STOPP-Test aus 16.5. Die
  Trockenzahlen (R1: 2 von 6 Stellungen mehrdeutig; R4: 3 von 3) sind zu klein
  fuer jede Aussage.
* Ob die Referenz in R1-R3 rangstabil genug ist, um die Runde ueberhaupt zu
  beantworten (16.5 Ausgang 4). Der R4-Trockenlauf zeigte bei n = 5 Paaren
  `m3_stabilitaet = 0,2`, also haeufiges Kippen des Vorzeichens ueber die
  gekoppelten Neubefuellungen - falls sich das bei ordentlichem n haelt, ist
  es selbst der Befund ("die Plaene sind nicht unterscheidbar"), aber bei n = 5
  ist es nichts.
* Die Behauptung, `mcts_q` des gewaehlten Zugs sei der EXAKTE
  Alpha-Beta-Wurzelwert. Die Sonde belegt nur, dass `root_value` dort fehlt und
  der Ersatzwert existiert; die Exaktheit ist aus
  `tools/tiling_value_reference_main.py:162-173` uebernommen und in dieser
  Sitzung NICHT am `round5.rs`-Code nachgeprueft.

**Lauf-Befehl, sobald die Maschine frei ist** (ohne Pipe, ohne Umleitung,
Fortschritt je 5 Dateien):

```
python -u tools/probes/counterfactual_tiling_ranking.py --max-positions 60 --draws 6 --sims 400 --max-cands 4 --rounds 1,2,3,4
```

**`--max-positions` ist seit par.16.8 das Soll JE RUNDE, nicht die Gesamtzahl** -- 60 je Runde
statt der urspruenglichen 200 gesamt. Die Zahl kommt aus der Verfuegbarkeit, nicht aus dem
Wunsch: mehrdeutig sind gemessen 20 / 48 / 71 / 73 von 400 Stellungen in R1-R4, R1 also 5,0
Prozent. Ein Soll von 60 in R1 verlangt rund 1.200 gescannte Tiling-Stellungen; ob das Fenster
die hergibt, sagt die Sonde selbst im Feld `scanned`. **Erreicht eine Runde ihr Soll nicht,
wird sie als NICHT ENTSCHIEDEN berichtet** und geht in keine Gesamtquote ein (16.4: unter der
Wilson-Untergrenze ist jede Richtung Rauschen). Die Kosten des Volllaufs bei sims = 400 und
M = 6 sind UNGEMESSEN -- der Trockenlauf lief mit 20 Sims und M = 4; hochrechnen waere genau
die Schaetzung, die `CLAUDE.md` verbietet. Der erste Volllauf beginnt deshalb mit `--rounds 4`
allein (Grad EXAKT, die aussagekraeftigste Klasse) und misst dabei seine eigene Laufzeit.

### 16.9 VOLLLAUF (2026-09-17): Runde 4 TRAEGT die Reihenfolge, aber die UEBERSTIMMUNG schadet; Runde 3 ohne Verdikt

Maschine vorher frei geprueft (Prozessabfrage: kein `python`, `cargo`, `rustc`), Wheel mit
Variante B (Default aus, Kontrakt `39994362fba145a6`), Nutzer-Freigabe "fahr die sonde".

#### 16.9a Kostenmessung ZUERST, nicht hochgerechnet (16.7 hatte sie ausdruecklich offen)

Zwei kurze Laeufe mit den registrierten Einstellungen (`--sims 400 --draws 6 --max-cands 4`),
je `--max-positions 3`, `laufzeit`-Block im Artefakt:

| Runde | Artefakt | n | Wanduhr | CPU | Threads | s je Stellung |
| --- | --- | --- | --- | --- | --- | --- |
| R4 | `counterfactual_ranking_cost_probe.json` | 3 Stellungen | 9,4 s | 9,1 s | 1 | **3,132** |
| R3 | `counterfactual_ranking_cost_probe_r3.json` | 3 Stellungen | 35,1 s | 34,5 s | 1 | **11,708** |

**Der Befund der Kostenmessung ist selbst ein Beleg fuer die Zweiteilung aus 16.2:** in R4
kostet `--sims 400` praktisch dasselbe wie die 20 Sims des Trockenlaufs (3,132 gegen 3,4 s je
Stellung), weil dort der Alpha-Beta-Loeser antwortet, der die Sim-Zahl nicht liest; in R3 laeuft
die Baumsuche wirklich und kostet **3,74-mal** so viel. Wer die R4-Zahl auf R3 hochrechnet
(oder umgekehrt), liegt um diesen Faktor daneben.

#### 16.9b Der Volllauf R4

```
python -u tools/probes/counterfactual_tiling_ranking.py --sims 400 --draws 6 --max-cands 4 \
  --rounds 4 --max-files 400 --max-positions 800 --progress-every 20 \
  --out evaluations/artifacts/counterfactual_ranking_r4.json
```

`laufzeit`: `{"wanduhr_s": 2644.5, "cpu_s": 2596.6, "threads": 1, "stellungen": 800,
"paare": 3744, "s_je_stellung": 3.306}`, Fehler 0, Fortschritt je 20 Dateien ablesbar.

**Warum 800 und nicht die 60 aus 16.8:** 60 je Runde ist das MINDEST-Soll. Der Lauf hat
genommen, was der registrierte Deckel je Datei und Runde (`--max-per-file 2`, unveraendert)
ueber alle 400 Fensterdateien hergibt; 800 Stellungen sind das 13-fache des Solls. Der
Deckel blieb absichtlich unveraendert, damit keine Partie die Grundmenge stellt. Dass der
Lauf damit 44 min statt der angepeilten 60-90 min dauert, ist die Folge dieses Deckels und
kein Abbruch: die Angebotsgrenze war erreicht (Datei 400 von 400).

**Guetegrad: `ref_grade` ist `exact_ab` fuer ALLE 3.744 Paare** -- kein einziger stiller
Rueckfall auf `net_search`, der Laufzeit-Waechter aus 16.2 hat nichts gemeldet. Was dieser
Lauf damit selbst belegt, ist das Greifen des Zweigs; dass dieser Zweig auf seinem ganzen Pfad
wertkopf-frei ist, steht in 16.2 mit der Pruefstelle `round5.rs:357-359` und ist dort am
2026-09-16 nachgefahren worden -- **in dieser Sitzung NICHT erneut am Code geprueft,
uebernommen**.

| Kennzahl | n | Grundmenge | Einheit | Wert |
| --- | --- | --- | --- | --- |
| M1 Mehrdeutigkeit | 1.106 | gescannte R4-Tiling-Stellungen des Fensters | Stellungen | **72,33 Prozent** mit >= 2 Kandidaten (800), Median 4,0 Kandidaten, Maximum 12 |
| M2 Richtung, `dpoints != 0` | 1.886 | Paare mit Punktabstand, Gleichstand ausgeschlossen (21) | Paare | **0,8070** Treffer (1.522), Wilson95 **[0,7886; 0,8242]**, Binomial p < 1e-6 |
| M2 Richtung, `dpoints == 0` | 740 | punktgleiche Paare ohne Nullprodukt | Paare | 0,5486 (406), Wilson95 [0,5126; 0,5842], p = 0,0090 |
| M3 Rangstabilitaet, `dpoints != 0` | 1.907 | Paare mit Punktabstand | Paare | **0,7992** |
| M3 Rangstabilitaet, `dpoints == 0` | 1.837 | punktgleiche Paare | Paare | 0,3048 (Rauschboden 0,0312) |
| M4 Ueberstimmung | 1.907 | Paare mit Punktabstand | Paare | **156 Kippungen (8,18 Prozent), davon 46 richtig = 0,2949**, Wilson95 **[0,2289; 0,3707]** |
| M5 Aggregatoren, `dpoints != 0` | 1.886 / 1.810 / 1.524 | dieselbe Grundmenge, drei Lesarten | Paare | Mittelwert 0,8070, Worst Case 0,6674 [0,6454; 0,6887], nur M3-stabile 0,8425 [0,8234; 0,8599] |
| M5 Aggregatoren, `dpoints == 0` | 740 / 492 / 560 | dito | Paare | Mittelwert 0,5486, Worst Case **0,1504**, nur M3-stabile 0,5750 |

**M6 Fall-Klassen** (Mehrfachnennung je Paar, Quote ueber die Mittelwert-Lesart):

| Klasse | Paare | Quote | Wilson95 | M3 |
| --- | --- | --- | --- | --- |
| Spezialfeld | 360 | **0,8667** | [0,8277; 0,8979] | 0,8583 |
| Spalte | 2.340 | 0,7744 | [0,7562; 0,7916] | 0,7316 |
| Reihe | 845 | 0,7160 | [0,6846; 0,7454] | 0,7373 |
| Chip | 731 | 0,5926 | [0,5526; 0,6314] | 0,6019 |
| Lange Reihe | 320 | 0,5938 | [0,5391; 0,6461] | 0,6500 |
| sonstige | 1.084 | 0,5314 | [0,4751; 0,5868] | 0,2131 |

#### 16.9c Verdikt nach der LESART VORAB (16.5)

**Fuer die Runde 4 gilt Ausgang 1, TRAEGT** -- und zwar genau in der Form, in der 16.5 ihn
vorab beschrieben hat ("in R2-R4 bereits bei `dpoints != 0`"): beide Schwellen aus 16.4 halten
dort, Wilson-Untergrenze 0,7886 > 0,50 und M3 0,7992 >= 0,60. Der Value-Kopf trifft die
Reihenfolge zweier lokal plausibler Tiling-Plaene in Runde 4 in vier von fuenf Faellen, gegen
eine wertkopf-freie Wahrheit gemessen.

**Fuer die punktgleiche Teilklasse gilt Ausgang 2, TRAEGT NICHT:** Schwelle (i) haelt knapp
(0,5126 > 0,50), Schwelle (ii) reisst (M3 0,3048 < 0,60), und 16.4 verlangt beide. Zwei
Einschraenkungen dazu, damit die Zahl nicht ueberlesen wird: 0,3048 liegt rund zehnfach ueber
dem Rauschboden 0,0312, ist also kein reines Rauschen; und in **1.097 von 1.837** punktgleichen
Paaren ist das Produkt `dwp * ref_mean` exakt null, diese Paare fallen aus jeder Quote heraus
und zaehlen per Definition (`counterfactual_tiling_ranking.py:395-396,412`) gegen M3. Welcher
der beiden Faktoren null ist, weist das Artefakt nicht getrennt aus -- die naheliegende Lesart
"die Plaene sind exakt gleich viel wert" ist damit NICHT belegt, nur naheliegend.

**Und der Teil, der gegen den heute laufenden Zweig spricht -- Ausgang 3, SCHADET, auf der
Grundmenge von M4:** `punkte * P(Sieg)` kippt die reine Punktereihenfolge in 156 von 1.907
Paaren (8,18 Prozent). Von diesen 156 Kippungen gehen nur **46 in die Richtung der Wahrheit
(0,2949)**, und die OBERE Grenze des 95-Prozent-Intervalls liegt bei **0,3707, also unter
0,50**. Das ist die Signatur, die 16.5 Ausgang 3 vorab beschrieben hat: nicht Rauschen,
sondern systematisch falsche Rangfolge.

**Die beiden Befunde widersprechen sich nicht, sie ergaenzen sich**, und das ist der eigentliche
Ertrag des Laufs: eine Kippung setzt per Konstruktion voraus, dass das Netz den Plan mit den
WENIGEREN Rundenpunkten stark genug bevorzugt, um den Punktabstand zu ueberwiegen
(`counterfactual_tiling_ranking.py:417`). Die hohe Gesamtquote von 0,8070 entsteht also
ueberwiegend dort, wo Netz und Punkte dasselbe sagen; genau dort, wo das Netz den Punkten
widerspricht, hat es in 70,5 Prozent der Faelle unrecht. Die Rangfolge des Value-Kopfs ist in
Runde 4 gut; sein Vetorecht gegen die exakte lokale Rechnung ist es nicht.

**Registrierte Folge (16.5 Ausgang 3), NICHT ausgefuehrt:** Vorschlag,
`NET_TILING_TIEBREAK_ENABLED` (`tiling_solver.rs:858`) abzuschalten oder sein Rundenfenster
(`:1603-1610`) zu verengen. Das ist ein **Nutzer-Entscheid** und kein stiller Eingriff; er
aendert Engine-Verhalten und braucht deshalb die Anker-Invarianz-Pruefung (CLAUDE.md, "Nach
jeder Engine-Aenderung"). Offen bleibt dabei die Frage, die diese Sonde NICHT beantwortet: ob
ein enger gefasstes Kriterium (kippen nur bei grossem `dwp` und kleinem `dpoints`, oder nur in
M3-stabilen Faellen) besser waere als abschalten.

**Der STOPP-Test aus 16.5 ist nicht ausgeloest:** 72,33 Prozent der gescannten
R4-Tiling-Stellungen haben mindestens zwei strukturell verschiedene Kandidaten, Median 4. Die
Frage 1 aus par.14.3 ist damit beantwortet, der Strang endet nicht wegen Eindeutigkeit.
**Nicht vergleichbar mit 16.8:** dort standen 73 von 400 als Zahl ueber ALLE Runden zusammen,
hier ist die Grundmenge ausschliesslich R4, und der Scan bricht ab, sobald das Soll je Runde
gefuellt ist.

**Antwort auf die Aggregator-Frage aus par.14.3** (Mittelwert, Worst Case oder
Rang-Stabilitaet), soweit die Sonde sie misst: in R4 mit Punktabstand tragen alle drei
(0,8070 / 0,6674 / 0,8425); die Einschraenkung auf M3-stabile Paare schaerft am meisten, der
Worst Case ist der strengste Mass und haelt hier noch. In der punktgleichen Klasse dagegen
faellt der Worst Case auf 0,1504 -- dort ist die Reihenfolge eine Muenze, und ein
Worst-Case-Aggregator wuerde das richtig anzeigen.

#### 16.9d Standard-Kennzahlen (CLAUDE.md), n = 2.788 Kandidaten, Grundmenge Nach-Tiling-Bretter der R4-Stellungen, Einheit Kandidaten

| Kennzahl | Median |
| --- | --- |
| Reihenauslastung (Summe `row_fill`) | 13,0 |
| Spaltenauslastung: maximale Spaltenhoehe / volle Spalten / >= 3 / >= 4 | 5,0 / 0,0 / 2,0 / 2,0 |
| Strafleistenauslastung (`floor_len`) | 1,0 |
| Punkte je Wertungsplatte, je Kriterium | 0 / 0 / 0 / 0 / 8 / 3 / -12 / 0 |
| Eigene Punkte | 29,0 |
| Spezialfelder belegt | 1,0 |

**Margin zum Gegner FEHLT mit Begruendung** (keine stille Auslassung): die Sonde bewertet
STELLUNGEN und Plaene, nicht Partien; ohne Fortsetzung bis zum Ende gibt es keinen
Partieausgang und damit keine Punktedifferenz. Das Artefakt traegt dieselbe Begruendung im
Feld `hinweis_margin`.

#### 16.9e Rueckwaerts-Pruefung: wer hat sich auf diesen Zweig berufen?

Gegreppt ueber `evaluations/`, `docs/` und den Code nach `NET_TILING_TIEBREAK_ENABLED` und dem
Namen der Sonde. Die eine Fundstelle, die dieselbe Sache behandelt, ist
**`PREREG_geometric_envelope.md` par.3f** ("kippt aber trotzdem fast nie einen Punktvorsprung",
4 von 192) und die daran haengende Bauentscheidung in par.3f/K3 (:675-682: "par.3f hat gemessen,
dass das nur ein Stichentscheid unter punktgleichen Abschluessen ist").

**Kein Widerspruch, aber drei verschiedene Groessen -- und das muss hier stehen, bevor jemand
die Zahlen gegeneinander rechnet:**

* par.3f zaehlt n = 192 STELLUNGEN, Grundmenge `frozen_eval_set` v3, Einheit Stellungen, und
  zwar die TATSAECHLICHE Argmax-Entscheidung; 16.9 zaehlt n = 1.907 PAARE, Grundmenge
  R4-Kandidatenpaare des v29-Fensters mit Punktabstand, Einheit Paare. 8,18 Prozent je Paar und
  2,1 Prozent je Stellung sind damit nicht dieselbe Quote.
* par.3f steht auf `v23-b01_brierbest`, sechs Generationen vor `v29-b03`, und par.16.8 hat
  dessen netzabhaengige Zahlen ausdruecklich als nicht uebertragbar markiert.
* **Neu und in par.3f nicht enthalten ist die RICHTUNG der Kippungen.** par.3f hat gezaehlt, WIE
  OFT gekippt wird, nie, ob die Kippung recht hatte. Genau das sagt M4: in 70,5 Prozent der
  Faelle nicht.

#### 16.9f Runde 3, GETRENNT GEFUEHRT (zweiter Guetegrad, wertkopfbehaftet)

```
python -u tools/probes/counterfactual_tiling_ranking.py --sims 400 --draws 6 --max-cands 4 \
  --rounds 3 --max-files 400 --max-positions 300 --progress-every 20 \
  --out evaluations/artifacts/counterfactual_ranking_r3.json
```

`laufzeit`: `{"wanduhr_s": 3283.3, "cpu_s": 3229.7, "threads": 1, "stellungen": 300,
"paare": 1461, "s_je_stellung": 10.944}`, Fehler 0. Stellungszahl 300 statt 800: bei 11 s je
Stellung waeren 800 Stellungen 2,4 h gewesen; 300 sind das Fuenffache des Solls aus 16.8.

**`ref_grade` ist `net_search` fuer alle 1.461 Paare** -- also der zweite Guetegrad aus 16.2:
unabhaengige GEWICHTE (`v29-b05` gegen `v29-b03`), aber dieselbe ART von Schaetzer. Ein
positives Ergebnis belegt hier hoechstens UEBEREINSTIMMUNG zweier Wertkoepfe, keine
Richtigkeit. Das steht so schon in 16.2 und wird durch die Zahlen nicht besser.

| Kennzahl | n | Grundmenge | Einheit | Wert |
| --- | --- | --- | --- | --- |
| M1 Mehrdeutigkeit | 377 | gescannte R3-Tiling-Stellungen | Stellungen | 79,58 Prozent (300), Median 4 Kandidaten, Maximum 12 |
| M2, `dpoints != 0` | 579 | Paare mit Punktabstand | Paare | 0,7720, Wilson95 [0,7361; 0,8043] |
| M2, `dpoints == 0` | 882 | punktgleiche Paare | Paare | 0,7449, Wilson95 [0,7151; 0,7726] |
| M3, `dpoints != 0` / `== 0` / alle | 579 / 882 / 1.461 | dito | Paare | **0,5769** / 0,6156 / 0,6003 |
| M4 Ueberstimmung | 579 | Paare mit Punktabstand | Paare | 11 Kippungen (1,90 Prozent), davon 9 richtig (0,8182), Wilson95 [0,5230; 0,9486] |
| M5, `dpoints != 0` | 579 / 579 / 334 | dito | Paare | Mittelwert 0,7720, Worst Case 0,5181 (p = 0,41), nur M3-stabile 0,8982 |

**Verdikt R3 nach 16.4/16.5: Ausgang 2, TRAEGT NICHT -- an der Entscheidungsklasse, die 16.5
benennt.** Bei `dpoints != 0` haelt Schwelle (i) klar (0,7361 > 0,50), Schwelle (ii) reisst
knapp (M3 **0,5769** < 0,60), und 16.4 verlangt beide. Die punktgleiche Klasse haelt dagegen
beide (0,7151 > 0,50 und 0,6156 >= 0,60) -- das ist der Fall, fuer den 16.2 die Warnung vorab
hingeschrieben hat: zwei Wertkoepfe sind sich einig, und Einigkeit ist keine Wahrheit. Als
Befund wird daraus deshalb nichts ueber die Richtigkeit abgeleitet.

**Der Gegensatz zu R4 bei M4 ist NICHT belastbar:** in R3 kippt `punkte * P(Sieg)` nur 11-mal
(1,90 Prozent gegen 8,18 Prozent in R4), und von diesen 11 gehen 9 in die Richtung der
Referenz. Die Wilson-Untergrenze liegt mit 0,5230 zwar knapp ueber 0,50, aber n = 11 Paare bei
wertkopfbehafteter Wahrheit traegt gegen die 156 Paare mit wertkopf-freier Wahrheit aus R4
nicht. Wer daraus "in R3 ist die Ueberstimmung gut" liest, hat die Grundmenge und den Guetegrad
uebersehen.

**M6 Fall-Klassen R3** (Quote / M3): Chip 339 Paare 0,7788 / 0,6106; Spezialfeld 62 Paare
0,7742 / 0,5484; sonstige 497 Paare 0,7445 / 0,5573; Spalte 780 Paare 0,7231 / 0,5910; Reihe
206 Paare 0,6408 / 0,4660; lange Reihe 63 Paare 0,5873 / 0,4921.
**Standard-Kennzahlen R3** (n = 1.067 Kandidaten, Grundmenge Nach-Tiling-Bretter, Einheit
Kandidaten, Mediane): Reihenauslastung 9,0; Spalten maximal 4,0 / voll 0,0 / >= 3 2,0 / >= 4
1,0; Strafleiste 1,0; Plattenpunkte je Kriterium 0 / 0 / 0 / 0 / 6 / 0 / -9 / 0; eigene Punkte
18,0; Spezialfelder belegt 0,0. Margin fehlt aus demselben Grund wie in 16.9d.

**Runden 1 und 2 sind NICHT gefahren** (16.8: R1 ist zu duenn, und beide haetten denselben
zweiten Guetegrad). Sie bleiben offen; was ihnen fehlt, ist in 16.5 Ausgang 4 benannt.

**Folge, nicht ausgefuehrt:** wer K3 (`PREREG_geometric_envelope.md` par.3f/8.4) anfasst, liest
16.9c mit -- die dort gebaute Reihenfolge ("der Value-Stichentscheid rueckt hinter die
Geometrie") zeigt in dieselbe Richtung wie dieser Befund, ihre Begruendung ("faktisch nur ein
Stichentscheid unter Punktgleichen") traegt nach 16.9 aber nur noch je STELLUNG, nicht je Paar.
STATUS.md (Abschnitt zum Tiling-Stichentscheid, "nie gemessen worden, obwohl der Zweig aktiv
ist") ist damit ueberholt; nachgezogen wird das vom Koordinator, nicht hier.

## par.17 BAUSTAND Variante B (2026-09-16)

Fuehrt par.9 aus, mit den Bauvorgaben par.4.2 (stellungsgebundener Seed), par.8 (Mischregel
`determinize_dome_pool`) und par.10 (Beutel mit Turm daneben). **Gebaut ist der KNOPF, nichts
gemessen** -- Kostentor, Sichttor und A/B sind Fahrplan Nr. 34-36 und ausdruecklich NICHT Teil
dieses Zuges.

### 17.1 Kartierung: wo das Blatt heute endet (am Code geprueft 2026-09-16)

| Frage | Antwort | Pruefstelle |
| --- | --- | --- |
| Wann wird ein Blatt pseudo-terminal? | `check_phase_transition` setzt `Phase::Tiling`, sobald alle Fabriken leer sind UND kein aufgedeckter Chip mehr liegt (`check_drafting_complete`) | `game.rs:872-874`, `game.rs:521-536` |
| Woran erkennt die Suche es? | `terminal = state.phase != Phase::Drafting` -- ein Flag, KEINE Rundenpruefung: Runde 5 und Spielende fallen in dieselbe Klasse | `net_mcts.rs:3151` (`make_node`) |
| Was sieht das Netz dort? | den Zustand VOR dem Tiling: Musterreihen noch gefuellt, Fabriken leer, Kuppeln der Runde noch nicht gelegt, Rundenwertung noch nicht verbucht. Der Blattwert ist der gewoehnliche Netzwert dieses Zustands plus die Zustands-Additive (K1, K3, K4, Shaping) | `net_mcts.rs` `make_node`, Zweig `LeafEval::Net`, bis `today_value` |
| Gibt es dort schon einen Ausgang? | ja, GENAU EINEN: `if terminal && ROUND_TRANSITION_SAMPLING` -- Kompilierzeit-Konstante, Default `false`, also toter Zweig | `net_mcts.rs:95` (Konstante), `:3543` (Aufrufstelle; par.8 hatte `:3334`, die Zeile wandert, der Name nicht) |
| Was fehlte fuer Variante B? | der Betrachter und ein Salz: `make_node` kennt weder den Wurzelspieler noch den abgeleiteten Such-Seed der Partie. Beides ist jetzt ein Pro-Suche-Feld der `SearchConfig` (Muster `score_utility_root_margin`/`with_root_margin`) | `net_mcts.rs:765` (`RoundTransitionLeafCtx`), `:2821` (`with_round_transition_leaf_context`) |

Damit ist die Stelle bestaetigt, die par.9 benennt: **das Blatt ist der Netzwert VOR dem
Tiling**, und der Eingriff sitzt an genau dem Ort, an dem der Bestandsschalter haengt.

### 17.2 Bauform

* **Knopf** `MOSAIC_ROUND_TRANSITION_LEAF`, `0` = aus (Bestand), `1` = an; ungueltig fuehrt auf
  `0` plus einmalige Warnung (`net_mcts.rs:502` Default, `read_round_transition_leaf_env`).
  Registratur-Eintrag Status *Diagnose* mit Prereg-Verweis par.9/par.10
  (`knob_registry.rs`), Manifest-Feld `round_transition_leaf` (`lib.rs::engine_config_json`),
  `docs/knobs.md` per Generator nachgezogen (126 Knoepfe).
* **Spec-Feld** `round_transition_leaf`, OPTIONAL mit Default 0 -- jede eingefrorene Spec
  laedt weiter und beschreibt weiter bitgenau dasselbe. Die LEBENDEN `models/*.spec.json`
  bleiben bewusst unangetastet: ein aelteres Wheel lehnt unbekannte Felder hart ab, und die
  Ketten lesen die Specs bei jedem Partiestart neu (`tools/spec_add_field.py`-Kopf).
* **Wirkort** `net_mcts.rs::make_node`, unmittelbar vor dem Bestandsschalter: bei Knopf 1 und
  pseudo-terminalem Blatt der Runden 1-4 liefert `round_transition_leaf_value` den Netzwert
  des Zustands NACH dem Uebergang, sonst `None` und der Bestandspfad laeuft unveraendert.
* **Der Uebergang selbst** (`round_transition.rs::round_transition_leaf_state`, netzfrei und
  damit ohne ONNX pruefbar): `resolve_to_pre_chance` loest das Tiling BEIDER Seiten exakt auf
  (Schrittschleife, Bestand), dann `determinize_dome_pool(.., Some(viewer), ..)` mit dem
  Wurzelspieler als Betrachter, dann `advance_one_chance` -- also Beutel-Reihenfolge und
  Bonuschip-Vorrat gemischt, Turm-Nachfuellung ueber den Spielpfad `draw_with_refill`. Das ist
  der Kern, den par.10 ausdruecklich wiederverwenden wollte, keine zweite Bauform.
* **Seed** stellungsgebunden nach par.4.2: `leaf_fill_seed` = `derive_search_seed(fnv1a_64(
  leaf_fill_key) ^ ROUND_TRANSITION_LEAF_SEED_DISTINGUISHER, salt)`. `leaf_fill_key`
  serialisiert genau die in par.4.2 genannten Felder (Bretter, Musterreihen, Strafleisten,
  Chips, Beutel- und Turm-ZAEHLER, Runde, Spieler am Zug) und ausdruecklich NICHT die verdeckte
  Reihenfolge in Beutel, Turm und Kuppelstapel. Das `salt` ist EINE Zahl aus dem Suchstrom,
  gezogen an der Wurzel jeder Suche -- nicht je Blatt. Folge: dieselbe Stellung zieht dieselbe
  Fuellung, egal ueber welchen Pfad sie erreicht wird; der Hauptstrom verschiebt sich um genau
  einen Zug (Muster `moon_order_post_search`).
* **Drei Suchtreiber setzen den Kontext** (`build_gumbel_tree_inner`, `build_net_tree`,
  `search_start_placement`). Der dritte gehoert dazu, weil unter einer Startsetzung die
  gewoehnliche Drafting-Suche weiterlaeuft und das Rundenende von Runde 1 erreichen kann; dort
  ist der Betrachter `pi`, nicht `current_player` (dieselbe Falle wie bei
  `determinize_hidden_information_for`).
* **Heuristik-Pfad unberuehrt.** Die einzige Lesestelle des Knopfs sitzt im Netz-Blattpfad;
  `mcts.rs`, `heuristic_v3.rs` und `round5.rs` sehen ihn nicht. Der Elo-Anker (hv4) kann sich
  dadurch nicht bewegen -- die Anker-Invarianz-Pruefung bleibt trotzdem Pflicht, sobald das
  Wheel neu gebaut ist (CLAUDE.md).
* **Zaehler fuer das Kostentor** (par.5 Schritt 1): thread-lokal `(leaves, pseudo, applied)`,
  ausgelesen je Partie als Logzeile `[rt_leaf] leaves= pseudo= applied=` (`self_play.rs:4279`,
  Muster `[moon_order]`). Der gesuchte Anteil ist `pseudo / leaves`, die Wirksamkeit
  `applied / pseudo`; die Differenz sind Runde-5-Blaetter und Loeser-Abbrueche. Bei Knopf 0
  wird nicht gezaehlt (der Zaehler sitzt hinter dem Knopf-Vergleich), die Zeile bleibt weg.
* **Eintrag in `docs/architecture_reference.md`** ("Wo der Code Information ABSICHTLICH
  vernichtet") ist gesetzt, mit beiden Antworten: Informationsmenge des WURZELSPIELERS;
  weggenommen werden nur verdeckte Reihenfolgen, nicht die Zusammensetzung -- die Aufteilung
  Beutel/Turm bleibt erhalten, weil ein zaehlender Spieler sie kennt (par.10).

### 17.3 Tests (alle in dieser Sitzung gruen)

Neun neue Tests, `cargo test --release --lib`:

| Test | Zusage |
| --- | --- |
| `round_transition_leaf_off_is_bit_identical_and_draws_no_rng` | (a) Knopf 0: Kontext-Setzer ist Identitaet UND zieht keine Zufallszahl; ein gesetzter Kontext aendert den Blattwert nicht; Zaehler bleiben `(0,0,0)` |
| `round_transition_leaf_on_evaluates_the_next_round_state` | (b) Knopf 1: der Blattwert ist EXAKT `net_leaf_eval` auf dem Zustand nach dem Uebergang; Rundenzaehler +1, Phase Drafting, Fabriken befuellt; Zaehler `(1,1,1)` |
| `leaf_state_advances_the_round_and_refills_the_factories` | (b) netzfrei am echten Runde-1-Blatt |
| `leaf_fill_takes_only_tiles_from_bag_and_tower` | (c) Sichttor par.10 im Kleinen: Beutel auf zwei Steine gekuerzt, Turm leer, Bretter geraeumt -- die Fuellung enthaelt GENAU diese zwei (beide sicheren dabei, kein dritter), `bag_count` faellt auf 0 |
| `leaf_fill_is_deterministic_and_salt_bound` | (d) zweimal derselbe Zustand, dieselbe Fuellung; ein anderes Salz bewegt sie |
| `leaf_fill_key_ignores_hidden_order_but_sees_the_board` | der Schluessel haengt an der sichtbaren Stellung, nicht an der verdeckten Reihenfolge; eine Brettaenderung aendert ihn |
| `leaf_state_is_none_in_last_round_and_outside_tiling` | Wirkort auf Runde 1-4 und Phase Tiling begrenzt (R5-Fix-Grenze) |
| `round_transition_leaf_context_draws_exactly_one_number` | genau EINE Zahl je Suche, Betrachter ist der Wurzelspieler |
| `search_config_spec_round_transition_leaf_is_optional_and_validated` | Spec OHNE das Feld laedt weiter (Default 0), mit `1` kommt der Wert an, `2` ist ein harter Fehler |

**Lauf:** 672 gruen, 1 rot, 19 ignoriert, 99,6 s (n = 692 Tests, Grundmenge `cargo test
--release --lib`, Einheit Tests). **Die rote ist FREMD und lag schon vor diesem Bau an HEAD:**
`knob_registry::tests::all_mosaic_env_vars_in_code_are_registered` meldet
`MOSAIC_MOON_TARGET_SOURCE` ohne Registratur-Eintrag; der Knopf steht seit Commit `6dd8cd47`
in `engine/py/file_cache_key.py` (an HEAD nachgepruefte Fundstelle), gehoert zum
Cache-Schluessel-Strang und wurde hier NICHT angefasst (fremde Spur). `cargo test --release
--no-run` gruen, Beispiele und Benches mitkompiliert (42,4 s) -- `kernbeweis_910002_probe.rs`
braucht die zwei neuen Felder im Struct-Literal und hat sie bekommen.

### 17.4 Was NICHT gebaut wurde (und warum)

* **Kein Wheel.** `maturin build` und `pip install` waren fuer diesen Zug ausgeschlossen (ein
  GPU-Training lief). Solange das Wheel alt ist, wirkt der Knopf in keinem Python-Lauf --
  auch nicht versehentlich.
* **Keine Messung.** Sichttor (par.10, 300 Blatt-Zustaende), Kostentor (par.5 Schritt 1, 25
  Prozent) und der gepaarte A/B (par.9, 200 Paare am Champion) stehen aus.
* **Kein Spec-Feld in den lebenden Specs**, Begruendung in 17.2.
* **Keine Variante A, kein robuster Aggregator** (par.4.3/par.7: eigene Registrierung noetig),
  **kein Top-K** (par.14, haengt am B-Befund).
* **Kein `TIME_BUDGET`, kein Sample-Deckel.** Variante B zieht GENAU EINE Fuellung, der
  Zeitdeckel des Bestandsschalters (`TIME_BUDGET = 50 ms`, `N_SAMPLES_SEARCH = 8`) gilt fuer
  Variante A und wird hier nicht gelesen. Ob der Loeser am Blatt selbst einen Deckel braucht
  (par.7 nennt den Haenger-Vorfall des `tiling_solver`), entscheidet das Kostentor.

### 17.5 Was als naechstes ansteht, in dieser Reihenfolge

1. Wheel bauen und installieren, dann **Anker-Drift und Anker-Konservierung** gegen
   `models/frozen_heuristics/hv4_anchor` sowie die **Netz-Paritaets-Fixture des Champions**
   (`engine/tests/fixtures/net_parity_champion.txt`) -- alle drei muessen bei Default
   UNVERAENDERT sein. Das ist die Abnahme dieses Baus, nicht schon die Messung.
2. Sichttor par.10 (Fahrplan Nr. 34), dann Kostentor par.5 Schritt 1 (Nr. 35), dann A/B (Nr. 36).
3. Beim Kostentor mitschreiben, was die `[rt_leaf]`-Zeile liefert: Anteil pseudo-terminaler
   Blaetter je Suche (Grundmenge Blaetter des Netz-Blattpfads je Partie, Einheit Anteil).

### 17.6 Zwei Stellen, an denen der Bau von der Prereg abweicht -- und warum

1. **par.4.2 sagt "Seed = Hash des Blatt-Zustands verknuepft mit dem abgeleiteten Such-Seed
   der Partie".** Gebaut ist die Verknuepfung mit EINER Zahl, die an der Wurzel der Suche aus
   genau diesem abgeleiteten Strom gezogen wird -- der Strom selbst liegt in `net_mcts` nicht
   offen, `make_node` bekommt nur `rng: &mut R`. Die Zusagen der par.4.2-Tabelle gelten
   dadurch unveraendert INNERHALB einer Suche (dieselbe Stellung, dieselbe Fuellung,
   pfadunabhaengig; beide Arme eines gepaarten A/B ziehen in derselben Stellung dieselbe
   Stichprobe). Was NICHT gilt: dieselbe Stellung in zwei Suchen mit verschiedenem Halbzug-
   Index zieht verschiedene Fuellungen. Das ist gewollt -- ein ueber die ganze Kampagne fester
   Wuerfelwurf je Stellung waere ein systematischer Versatz, kein Determinismus-Gewinn.
2. **Die Fuellung haengt neben dem Seed auch an der ECHTEN verdeckten Beutel-Reihenfolge**
   (`advance_one_chance` mischt den vorhandenen Vec). Innerhalb einer Suche ist die konstant
   (Drafting zieht nie aus dem Beutel), die Zusage aus (1) ist damit erfuellt; ueber zwei
   verschiedene Zufallswelten hinweg ist sie es nicht. Der Schluessel selbst ist bewusst
   sichtkonform und kennt diese Reihenfolge nicht.

Kein Widerspruch INNERHALB der Prereg gefunden, der den Bau blockiert haette. Ein
Zeilendrift-Punkt aus par.8 ist mit 17.1 nachgezogen (Aufrufstelle jetzt `:3543`, Konstante
`:95`).

### 17.7 ABNAHME DES BAUS UND SICHTTOR (2026-09-17, Opus-Agent)

Fuehrt 17.5 Punkt 1 und 2 aus: das Wheel traegt den Knopf jetzt, die drei Abnahme-Pruefungen
sind gefahren, und das Sichttor par.10 ist GRUEN. Kostentor (par.5 Schritt 1, Fahrplan Nr. 35)
und A/B (par.9, Nr. 36) sind AUSDRUECKLICH nicht Teil dieses Zuges.

**(a) Wheel und Kontrakt.** `cargo test --release --no-run` 56 s, `maturin build --release`
28 s, `pip install --force-reinstall --no-deps` 3 s (Muster `tools/night_v29_wheel2.sh`).
**Kontrakt-Hash vorher wie nachher `39994362fba145a6`** (`engine_config_json`), `input_size`
794 gleich `config.INPUT_SIZE`; neu im Manifest steht `round_transition_leaf = 0`. Das ist die
Erwartung aus par.17.2: der Knopf beruehrt keinen Netz-Ein- oder Ausgabevertrag.

**(b) Anker-Invarianz gegen `models/frozen_heuristics/hv4_anchor`** (CLAUDE.md, Skill
`mosaic-anchor-invariance`), beide Modi **GRUEN**, je 1.763 Schritte Feld fuer Feld:
Drift 22,4 s (`evaluations/artifacts/anchor_drift_live_wheel_20260917_rtleaf.json`),
Konservierung 16,6 s (`anchor_conservation_artifact_wheel_20260917_rtleaf.json`). Damit ist
die Zusage aus par.17.2 ("Heuristik-Pfad unberuehrt") gemessen, nicht nur hergeleitet.

**(c) Netz-Paritaets-Fixture und Tests.** `cargo test --release --lib`: **673 bestanden, 0
rot, 19 ignoriert**, 78,1 s Testzeit (108,4 s Wanduhr mit Kompilieren). Darin
`self_play::tests::net_parity_hash_matches_champion_fixture` GRUEN (die Fixture wurde NICHT neu
erzeugt) und alle neun Tests aus 17.3. Die in 17.3 als fremd vermerkte rote Registratur-Zeile
(`MOSAIC_MOON_TARGET_SOURCE`) ist inzwischen nachgetragen und nicht mehr rot; die Zahl 673
statt 672 ist derselbe Test. `tools/check_conventions.py`: alle Regeln gruen (eine Warnung zur
Groessen-Ratsche von `train.py`, kein Blocker).

**(d) Sichttor par.10: GRUEN, n = 300, Grundmenge Blatt-Zustaende (`phase == tiling`) der
Runden 3 und 4 mit `bag_count` < 21 aus `data/selfplay_v28-b02-policy_*.pkl`, Einheit
Zustaende.** 150 je Runde, gezogen aus 1.647 gesehenen Blatt-Zustaenden dieser Runden; kein
Fehlschlag, 41,1 s Wanduhr (40,4 s CPU, 1 Thread, 0,137 s je Zustand). Artefakt
`evaluations/artifacts/rt_leaf_sight_gate.json`, Instrument
`tools/probes/round_transition_leaf_sight_gate.py`. Drei Kriterien, vor dem Lauf im
Sonden-Kopf festgelegt:

| Kriterium | Ergebnis | ROT-Kriterium |
| --- | --- | --- |
| T1 Quelle: Farb-Multimenge der Fuellung ist enthalten in Beutel plus Turm plus Abraum des pre-chance-Zustands | **0 Verstoesse von 300** | ja |
| T2 Bilanz: (Beutel + Turm + Abraum) vorher minus (Beutel + Turm + Abraum) nachher gleich Fuellung, Farbe fuer Farbe | **0 Verstoesse von 300** | ja |
| T3 sichere Steine: die Fuellung enthaelt die GANZE Beutel-Multimenge | **0 Abweichungen von 300** | nein (Regelausnahme unten) |

Die Torgroessen streuen breit genug, dass das Tor nicht leer laeuft: Beutel vor der Ziehung
Median 6 (2 bis 20), Turm Median 24 (2 bis 42), Abraum Median 10 (0 bis 19), Fuellung in ALLEN
300 Faellen genau 21 Steine (5 grosse Manufaktur plus 4 x 4 kleine, `state.rs::fill_factories`).

**Zwei Praezisierungen der Torformel, beide am Code und nicht abgeleitet:**

1. **"bag_count faellt entsprechend" darf nicht auf `bag_count` allein gelesen werden.**
   `draw_with_refill` (`state.rs:304-316`) mischt den Turm in den Beutel, sobald der Beutel die
   verlangte Zahl nicht mehr liefert -- `bag_count` STEIGT dann. Gemessen: Differenz nachher
   minus vorher von -15 bis +24, Median +7. Die pruefbare Fassung ist deshalb T2, die exakte
   Bilanz ueber Beutel, Turm und Abraum.
2. **Der Abraum gehoert in die Quelle, par.10 sagt das ausdruecklich** ("sonst nur Steine aus
   Turm plus Abraum"). `execute_end_tiling` (`game.rs:977-996`) legt unplatzierbare
   Musterreihen und die geleerte Strafleiste in den Turm, BEVOR die Fabriken befuellt werden;
   der Rust-Test in 17.3 raeumt die Bretter genau deshalb vorher. T3 hat eine legitime
   Regelausnahme -- der monochrome Redraw der grossen Manufaktur legt gezogene Steine in den
   Beutel zurueck (`state.rs::fill_large_factory`) -- sie ist in dieser Stichprobe nie
   eingetreten (0 von 300), darum ist T3 hier gleich scharf wie T1.

**(e) EIN BAU in diesem Zug, ausgewiesen:** am HEAD gab es KEINEN Python-Einstieg in
`round_transition_leaf_state` (geprueft: `engine/src/lib.rs` exportiert nur
`resample_round_transition_json` und `advance_after_tiling_json`). Das Sichttor haette sonst
nur den gemeinsamen Kern ueber `advance_after_tiling_json` gemessen, dem der Betrachter, die
Mischregel `determinize_dome_pool` und der stellungsgebundene Seed fehlen. Neu gebaut ist
darum der ADDITIVE Diagnose-Export `round_transition_leaf_fill_diag_json` (`lib.rs`, ruft die
gebaute Funktion selbst auf und liefert die Farblisten; kein Spielpfad liest ihn, er setzt
keinen Knopf). Das Wheel wurde danach ein zweites Mal gebaut (26 s plus 1 s) und **beide
Anker-Modi erneut gefahren, wieder GRUEN** (Drift 22,8 s, Konservierung 16,4 s; Artefakte
`anchor_drift_live_wheel_20260917_rtleaf_sightgate.json` und
`anchor_conservation_artifact_wheel_20260917_rtleaf_sightgate.json`), Kontrakt-Hash wieder
`39994362fba145a6`. Das installierte Wheel ist dieses zweite. `cargo test --release --no-run` danach GRUEN (48,1 s, Beispiele und Benchmarks mitkompiliert) -- die pre-push-Falle aus CLAUDE.md ist damit geprueft, nicht angenommen.

**(f) Ein FREMDER roter Befund am Rand, nicht von diesem Bau.** Die nach dem Wheel-Bau
uebliche Paritaetssonde `tools/probes/feature_parity_rust_python.py` (Schritt 7 in
`tools/night_v29_wheel2.sh`) faellt: Population `pygame` 733 von 733 gleich, Population
`corpus` nur **298 von 300** -- Abweichung in Planes-Kanal 76 (Erreichbarkeit je Zelle,
`features.rs:1733`), ein Wert je betroffenem Zustand (Rust 1.0, Python 0.0). Commit `42167aef`
beruehrt `features.rs` nicht (`git show --stat`), die letzte Aenderung dort ist `36520a31`
(2026-09-14, "Encoder-Korrektur im Wheel"); die Registratur in `docs/knobs.md` nennt das Tor
"bestanden 2026-09-11". Der Befund ist damit AELTER als dieser Bau und hier nur gemeldet, nicht
untersucht -- Artefakt `evaluations/artifacts/feature_parity_rust_python.json`. Wer ihn
aufnimmt, sollte bei der Frage anfangen, ob `remaining_colors` auf rekonstruierten
Korpus-Zustaenden (ohne `dome_pool_view`) beide Seiten gleich sieht.

**NACHTRAG 2026-09-17: untersucht und geschlossen, Registrierung in
`PREREG_rust_data_layer.md` par.9a.** Der Befund gehoert nicht hierher und nicht zu diesem Bau.
Ursache ist der A2-Phantom-Fix vom 2026-09-12 (`2a0cf4bf`): die v26-Records vom 2026-09-09
tragen `cell_reachable_mask` nach der alten Formel, `state_to_planes_direct` rechnet sie frisch.
Beide abweichenden Zustaende tragen Phantom-Fliesen, auf Records nach dem Fix 0 von 600
Abweichungen. Der hier geaeusserte `dome_pool_view`-Verdacht ist WIDERLEGT: das Feld fehlt in
allen 300 Alt-Zustaenden, abweichend sind 2. Die Rekonstruktion ist unbeteiligt --
`remaining_colors` liest nur Felder, die vollstaendig aus dem JSON kommen.

**Damit ist Fahrplan Nr. 33 abgenommen und Nr. 34 durch.** Offen bleibt in der Reihenfolge:
Kostentor par.5 Schritt 1 (Nr. 35), dann der gepaarte A/B par.9 (Nr. 36).

### 17.8 KOSTENTOR (Fahrplan 35) BESTANDEN -- 2026-09-17, 01:55

`tools/night_v29_rt_leaf_gates.sh`, Muster K4 (`PREREG_round_estimate_leaf_term.md` par.7b): zwei
Laeufe mit beidseits GLEICHER Spec am Champion `v28-b02_brierbest` @400, `paired_gating`,
20 Paare = 40 Partien je Lauf, 10 Threads, `--log-games`.

| Lauf | Spec | Seed | Wanduhr | s je Partie | CPU s |
| --- | --- | --- | --- | --- | --- |
| mit Knopf | `models/rt_leaf_on.spec.json` (Champion-Spec plus `round_transition_leaf: 1`) | 20261150 | 568,0 s | **14,200** | 2.408,9 |
| ohne Knopf | `models/rt_leaf_off.spec.json` (`round_transition_leaf: 0`) | 20261151 | 533,1 s | **13,326** | 2.288,2 |

**Aufschlag +6,6 Prozent Wanduhr (+5,3 Prozent CPU) gegen die Schwelle von 25 Prozent (par.4.1):
TOR HAELT**, rund ein Viertel des Erlaubten. Kontrollprobe: beide Laeufe enden 20:20 mit
identischen Punkten je Seite (52,20 / 52,20 bzw. 49,25 / 49,25), die Seiten spielen also
dasselbe -- der Knopf war beidseitig gleich gesetzt.

**Anteil pseudo-terminaler Blaetter (par.5 Schritt 1, par.17.5 Punkt 3), aus den 40
`[rt_leaf]`-Zeilen des mit-Laufs:** 19.132 von 1.165.982 Netz-Blaettern = **1,64 Prozent**
(Grundmenge Blaetter des Netz-Blattpfads ueber 40 Partien, Einheit Blaetter); `applied` =
19.132, also an JEDEM pseudo-terminalen Blatt der Runden 1-4 wurde der Uebergang gerechnet.
Lesart vorab (par.5): der Anteil ist klein, damit ist auch der moegliche Effekt begrenzt -- er
wirkt nur an 1,6 Prozent der Blaetter, aber genau an denen, an denen die Runde faellt.

**Nebenlast offengelegt:** waehrend beider Laeufe lief das Training v29-b06 auf der GPU
(erlaubt nach `docs/working_rules.md` "Auslastung"; sein Lader belegt aber 5-6 Kerne). Beide
Seiten des Tors sind gleich betroffen -- der Quotient traegt, die absoluten 13-14 s je Partie
liegen ueber den 11,5-11,8 s der b04-Arena ohne GPU-Nachbar und sind nicht als Planungsgroesse
zu nehmen. Artefakte `rt_leaf_kosten_mit_s20261150.json`, `rt_leaf_kosten_ohne_s20261151.json`,
`rt_leaf_kostentor_verdikt.txt`.

**Damit laeuft Schritt 2 (par.5, Fahrplan 36):** A/B Champion mit gegen ohne Knopf, 200 Paare,
Seed 20261152, gestartet 01:54:36. Bezug ist `v28-b02_brierbest`, nicht "v29-b01" (par.9 war die
Erwartung vom 2026-09-12; der Champion ist geblieben).

### 17.9 A/B (Fahrplan 36) GEMESSEN -- 2026-09-17, 03:13: Variante B TRAEGT NICHT

**Aufbau (par.5 Schritt 2):** dasselbe Netz gegen sich selbst -- Champion `v28-b02_brierbest` @400,
Champion-Spec plus `round_transition_leaf: 1` (`models/rt_leaf_on.spec.json`) gegen `: 0`
(`rt_leaf_off.spec.json`), gepaart, Blockgroesse 5, Deckel 200 Paare, SPRT alpha = beta = 0,001,
`--log-games`, 10 Threads, Seed 20261152. Nebenlast: GPU-Training v29-b06 bis 02:32 (erlaubt).

| Groesse | Wert |
| --- | --- |
| Siege an : aus | **169 : 191** von 360 Partien (180 Paare; SPRT H0, Schranke bei LLR -6,94 unterschritten) |
| McNemar p | 0,248 |
| gepaarte Differenz | -0,122 je Paar (Partien-Skala) |
| **Block-Ebene** (par.5 Entscheidungsmass) | 36 Bloecke a 10 Partien, Siegdifferenz an minus aus **-0,61 je Block**, SE 0,54, **z = -1,13** |
| eigene Punkte an / aus | 50,37 / 51,69 (**-1,33**) |
| Marge | -1,33 |
| Strafleiste (`boden`) | 8,59 / 7,80 (**+0,79** Strafpunkte mit Knopf) |
| Plattenpunkte gesamt | 6,12 / 6,07 (+0,05) |
| Plattenpunkte je Kriterium, an minus aus | Vertikale Reihen **-0,86** (6,22 / 7,09), Mehrfarbige Felder +1,04 (3,07 / 2,03), Diagonale -0,15, Farbenreiche +0,16, Eckplatten -0,11, Aeussere Felder +0,13, Spezialfelder +0,06 (-10,42 / -10,48), Horizontale -0,05 |
| Laufzeit | 4.704,7 s, 13,07 s je Partie |

**Verdikt nach par.5 Falsifikator:** keine signifikante Staerkeverbesserung auf Block-Ebene,
also **negativ**: Variante B kommt NICHT ins Rezept. Die Richtung ist sogar leicht gegen den
Knopf (z = -1,13, weniger Punkte, mehr Strafleiste, weniger Punkte aus vertikalen Reihen); das
ist kein signifikanter Schaden, aber auch kein Ansatz eines Gewinns. par.5 ("die Linie
'Rundenuebergangs-Rauschen' gilt zusammen mit dem v11-Befund als auf beiden Wegen geprueft und
geschlossen") greift damit fuer die Suchseite.

**Einordnung, am Kostentor abgelesen (17.8):** der Knopf wirkt an 1,64 Prozent der Blaetter.
Selbst ein grosser Effekt je Blatt bliebe an dieser Stelle klein; und was er dort tut, ist das
Tiling mit dem exakten Loeser plus EINE Neubefuellung -- das Netz bewertet danach eine einzelne
Zufallswelt statt eines Erwartungswerts. Ob eine Mittelung ueber mehrere Neubefuellungen
(par.4.3, robuster Aggregator) oder Top-K (par.14) das dreht, ist NICHT gemessen und ohne
Nutzer-Auftrag nicht eingetaktet: v30+ bekommt keine neuen Vorregistrierungen (Nutzer
2026-09-16), beide stehen aber als offene Punkte in DIESER Prereg.

**Kennzahlen-Luecke, begruendet (CLAUDE.md, Standard-Kennzahlen):** Reihen- und
Spaltenauslastung sowie die Strafleisten-Verteilung aus der Spaltensonde FEHLEN fuer den
mit-Knopf-Lauf: `tools/analyze_game_log.py` erkennt die neue Diagnosezeile `[rt_leaf] ...` im
Runde-5-Log nicht als Nicht-Aktionszeile und bricht das Nachspiel ab -- 0 von 360 replaybar
(`arena_columns_rt_leaf_on_vs_off_s20261152.json`, ROT; ebenso 0 von 40 im Kostentor-mit-Lauf,
waehrend der ohne-Lauf 40 von 40 nachspielt). Ersatz oben: Strafleiste als `boden` und
Spaltenbau als Kriterium "Vertikale Reihen" aus `plate_points_from_arena.py`. Reparatur des
Parsers ist beauftragt (Diagnose-Marker-Liste), das Nachspiel wird nach Tor 1 von b06 nachgeholt
und hier als 17.9a nachgetragen.

**Fahrplan:** 33 abgenommen, 34 gruen, 35 haelt, 36 negativ. Offen in dieser Prereg nur noch die
Stufe-0-Sonde (par.16, Volllauf `--rounds 4`) als Diagnostik ohne Rezeptfolge -- ob sie noch
gefahren wird, ist Nutzer-Entscheid.

### 17.9a Nachgeholte Kennzahlen aus der Spaltensonde (2026-09-17, 04:57, nach der Replayer-Reparatur)

`tools/analyze_game_log.py` kennt die Diagnosezeilen jetzt ueber eine Marker-Liste (`[moon_order]`,
`[rt_leaf]`; `docs/pitfalls.md`). Nachspiel des A/B `rt_leaf_on_vs_off_s20261152`: **359 von 360
Partien replaybar** (1 divergiert, Replayer-Grenze Chip-Vollendung), Kostentor-mit-Lauf 40 von 40.

| Kennzahl (an / aus, n = 359 je Seite) | an | aus | Diff |
| --- | --- | --- | --- |
| volle Spalten | 0,919 | 0,967 | -0,047 |
| Spalten >= 3 / >= 4 | 3,251 / 2,279 | 3,195 / 2,226 | +0,056 / +0,053 |
| Zeilen voll / Zeilen-Fuellung | 0,114 / 17,83 | 0,128 / 17,81 | -0,014 / +0,02 |
| Strafleiste | **8,588** | 7,799 | **+0,788** |
| Spezialfelder belegt | 1,287 | 1,309 | -0,022 |
| lange Reihen vollendet | 3,089 | 3,022 | +0,067 |
| Punkte / Margin | 50,40 / -1,36 | 51,76 / +1,36 | -1,36 / -2,72 |

Die Lesart aus 17.9 bleibt: kein Gewinn, die Strafleiste steigt mit Knopf um rund 0,8 Punkte je
Partie, die Vollendung faellt leicht, die Teilspalten (>= 3, >= 4) steigen leicht -- das Netz sieht
nach dem Tiling der Runde offenbar mehr Teilstrukturen, loest sie aber nicht ein. Die
Kennzahlen-Luecke aus 17.9 ist damit geschlossen.

## par.18 VARIANTE C: ZUSCHNITT UND BAU (Nutzer-Auftrag 2026-09-17: "fahr die sonde und variante c")

Variante B ist ENTSCHIEDEN und negativ (17.9): die SUCH-Seite der Linie
"Drafting muss das Tiling kennen" (par.7) ist damit zu. Uebrig bleibt die
ENCODER-Seite, die par.7 unter dem Namen Variante C fuehrt: "dem Netz das
projizierte Nach-Tiling-Raster und den erwarteten Kuppel-Bonus als Eingabe
geben". Sie kostet in der Suche kein Sampling, braucht aber ein Training --
darum ein eigener Fensterarm, **`v29-b07`**. Nutzniesser sind unveraendert
par.12 (Spezialfeld-Ertrag: die Kette Drafting, Tiling, Freischaltung) und
par.13 (rundenuebergreifende Tiling-Bewertung).

### 18.1 ZUSCHNITT (Nutzer-Einwand 2026-09-17: keine Skalare, echte Positionen)

**Nutzer, woertlich:** *"variante c kommt mir vor, als wuerden wir die
geschaetzten punkte (die wir je zug sowieso immer berechnen) an das netz
zurueckgeben. evtl. besser aufgeloest mit echter position."*

Der Einwand trifft, und zwar am Code nachpruefbar: `estimated_score` im
Spielerblock (Abschnitt 5, `features.rs:696` im JSON-Pfad, `features.rs:1202`
im Direktpfad) IST bereits `solve_round_final_score(state, pi) - p.score`, also
genau die Punktevorschau des Loesers, je Spieler, normiert /100. Ein zweiter
Skalar "projizierte Rundenpunkte" waere eine Wiederholung; und ein Skalar, der
den Rundenscore an die Blattbewertung haengt, ist als K4 schon gemessen und
hochsignifikant negativ (`PREREG_round_estimate_leaf_term.md` par.7c/7d).
**Gestrichen sind deshalb die beiden Skalare des ersten Vorschlags**
("Rundenpunkte /30", "Kuppelbonus /10"). Gebaut wird nur, was das Netz aus dem
Bestand NICHT ableiten kann: die Geometrie.

Je Spieler, in Zugreihenfolge (erst der ziehende Spieler, dann der Gegner --
dieselbe Ordnung wie die Abschnitte 5, 6, 13, 14 und 16):

| Block | Werte | Bedeutung | Normierung |
| --- | --- | --- | --- |
| (a) Raster | 36 | Zelle (Slot-Zeile, Slot-Spalte, Space-Index) wird im Tiling DIESER Runde NEU gefuellt | 0/1 |
| (d) Slots | 9 | Kuppelplatte wird in dieser Runde VOLLENDET (alle vier Felder belegt), also auch ihr Spezialfeld freigeschaltet und abgerechnet | 0/1 |

**45 je Spieler, 90 gesamt, `INPUT_SIZE` 794 -> 884.**

**Warum (a) als DELTA und nicht als Nachher-Raster:** der heutige Fuellstand
jeder der 36 Zellen steht schon im Vektor (Abschnitt 6, `filled_id/6` je Space,
`features.rs:744-781` bzw. `:1238-1252`). Ein absolutes Nachher-Raster haette
36 bereits bekannte Werte je Spieler wiederholt; das Delta traegt genau die neue
Information. Zellen ohne Kuppelplatte (`dome_slots[sr][sc] == None`) sind 0.

**Warum (d) ueberhaupt, obwohl es aus (a) fast folgt:** die Vollendung ist der
gemessene Engpass (`project_column_completion_structural_weakness`), und sie ist
aus dem Delta nur zusammen mit dem Bestand rekonstruierbar (Zelle schon voll
plus Zelle wird voll). Ein eigenes Bit je Slot macht daraus ein Merkmal statt
einer Konjunktion, die das Netz erst lernen muss. **Freischaltung und Vollendung
fallen zusammen** und brauchen darum kein zweites Bit: `try_unlock_special`
(`dome.rs:139-157`) entriegelt das Spezialfeld, sobald die anderen drei Felder
belegt sind, und `check_special_trigger` (`round_end.rs:346-389`) setzt im
SELBEN Schritt `placed_special` und schreibt den Kuppel-Bonus -- beide sitzen in
`execute_full_tiling` (`round_end.rs:298-325`), das der Loeser je Platzierung
ruft. Ein Slot, dessen drei Normalfelder in der Projektion voll werden, ist
darin also vollstaendig belegt (`DomeSpace::is_filled`, `dome.rs:53-58`, liest
fuer Spezialfelder `placed_special`).

### 18.2 DIE DESIGNFRAGE IST IM BESTAND BEANTWORTET: der Loeser laeuft mitten im Drafting

**Nutzer, 2026-09-17:** *"das haben wir jetzt auch schon als punktevorschau
waehrend dem drafting."* Am Code bestaetigt, vier Belegstellen:

* `lib.rs:1650-1651` rechnet `tiling_potenzial = solve_round_final_score(&state,
  player) - p.score` auf einem beliebigen, ueber `json_to_state` rekonstruierten
  Zustand -- auch mitten im Drafting.
* `py.rs:1112` ruft denselben Loeser im GUI-Pfad.
* `features.rs:1202` tut es je encodiertem Zustand ohnehin schon (Abschnitt 5).
* Kein Phasen-Gatter auf dem Weg: `legal_steps` -> `generate_tiling_actions`
  (`round_end.rs:677-715`) und `validate_tiling_action`
  (`round_end.rs:135-175`) lesen ausschliesslich `state.players[..]`; das
  einzige Legalitaetskriterium der Reihe ist `row.is_complete()`.

**`resolve_to_pre_chance` ist dafuer NICHT brauchbar** (zwei Gruende, nicht
einer): es hat ein hartes Phasen-Gatter (`round_transition.rs:138`,
`phase != Tiling` -> `None`) und es spielt das Tiling BEIDER Seiten plus den
Rundenwechsel -- es liefert den Zustand der naechsten Runde, nicht das Raster
dieser. Variante C braucht "Tiling JETZT", nicht "naechste Runde".

**Semantik der Projektion, verbindlich:** das punktemaximale Tiling der JETZT
VOLLEN Musterreihen, je Spieler getrennt auf dem eigenen Brett; Teilreihen
bleiben liegen (der Loeser sieht sie nicht als platzierbar); Bonuschips setzt
der Loeser so, wie er sie im Hot-Path setzt (GREEDY-Allokation, `exact = false`,
`legal_steps`-Doku `tiling_solver.rs:144-150`); Reihenfolge oben nach unten und
die `tiled_max_row`-Sperre gelten wie im echten Tiling. Das ist Wert fuer Wert
dieselbe Wahrheitsquelle wie die Punktevorschau der Anzeige und wie
`estimated_score` -- Netz-Eingabe und Anzeige koennen nicht auseinanderlaufen.

**Vorderseiten-Sicht:** die Projektion liest nur, was am Tisch offen liegt --
Musterreihen, Strafleiste, Kuppelraster und Bonuschips BEIDER Spieler
(`serialize::serialize_player` schreibt diese Felder offen; die Chips sind nach
dem Aufdecken offen). Kein verdeckter Bestand geht ein: kein Beutel, kein Turm,
kein Kuppelstapel, keine Ziehreihenfolge. Damit ist sie kein
Netz-sieht-MEHR-Fall im Sinn von `PREREG_stack_top_feature.md` par.10 -- ein
Mensch kann dieselbe Vorschau rechnen, und die GUI zeigt sie ihm bereits.

### 18.3 BAU (additiv, Muster `PREREG_stack_top_feature.md` Abschnitt 16)

1. **`tiling_solver.rs`: `project_max_tiling(state, pi) -> TilingProjection`.**
   Der Bestand liefert nur den PUNKTWERT (`solve_max_tiling_points`), nicht den
   gelegten Plan; `top_k_tilings` liefert fertige Bretter, ist aber der
   exakt-Chip-Enumerator mit eigener Blattgrenze und fuehrt eine
   Diagnose-Statistik (`TILING_BUDGET_STATS`) -- als Encoder-Hot-Path falsch.
   Gebaut ist darum der kleinste Schnitt: DIESELBE Rekursion wie `solve_rec`
   (gleiche Schrittliste, gleiche GREEDY-Chips, gleiches `NODE_BUDGET`, gleiche
   Abbruchbedingungen), die zusaetzlich die Belegungsmaske des punktemaximalen
   Blattes mitfuehrt. Der Punktwert ist damit per Konstruktion identisch zu
   `solve_max_tiling_points`, und ein Test haelt das fest.
2. **Memoisierung** thread-lokal unter demselben Schluessel (`TilingKey`) und
   demselben Knopf (`MOSAIC_TILING_CACHE`) wie der Punkt-Cache: die Projektion
   haengt an genau denselben Feldern (Herleitung `tiling_solver.rs:244-274`).
   Bitgleich mit und ohne Cache (deterministische Funktion).
3. **`features.rs` Abschnitt 17, beide Pfade**, `INPUT_SIZE` 884. Direktpfad aus
   dem `GameState`. JSON-Pfad: der Record traegt kein Projektionsfeld und soll
   keines bekommen (ein Record-Feld wirkte erst eine Generation spaeter,
   Praezedenz P.12 in `PREREG_stack_top_feature.md` par.17) -- der JSON-Pfad
   rekonstruiert den Zustand ueber `serialize::json_to_state` mit festem Seed 0
   und ruft dieselbe Funktion. Das ist die bestehende Route fuer genau diesen
   Fall (`lib.rs:1785` Planes, `lib.rs:1636` Shaping-Export); der RNG treibt
   dort nur verdeckte Bestaende, die die Projektion nicht liest. Scheitert die
   Rekonstruktion (Alt-Schnappschuss ohne ein Pflichtfeld), bleiben alle 90
   Werte 0 -- dieselbe Toleranz wie in den Abschnitten 15 und 16.
4. **Python-Zwilling: dieser EINE Block kommt aus dem Wheel.** Abschnitt 16
   liess sich in Python nachbauen, weil er Record-Felder liest; die Projektion
   braucht den exakten Tiling-Loeser. Ein Python-Nachbau waere eine ZWEITE
   Wahrheitsquelle fuer eine Spielregel (CLAUDE.md: Regelfragen an den Code,
   nicht an eine Ableitung) und die naechste stille Abweichung.
   `state_to_tensor_python` ruft darum fuer die 90 Werte den neuen, additiven
   Export `tiling_projection_values_from_json` des Wheels -- dieselbe Funktion,
   die der Rust-Pfad nutzt, also bitgleich per Konstruktion. Fehlt das Wheel
   oder ist es zu alt, ist das ein HARTER Fehler, kein stiller Nullblock (die
   Umkehrung des Unfalls vom 2026-09-11).
5. **`config.INPUT_SIZE` bleibt bei 794**, bis der Koordinator sie IM SELBEN ZUG
   mit der Wheel-Installation auf 884 setzt (Unfall 2026-09-11; die
   Scharfschaltung beider Python-Wege haengt an dieser einen Zeile, und der
   Fenster-Cache-Schluessel liest sie zur Laufzeit).

### 18.4 KOSTEN -- ANNAHME, nicht gemessen

Der Loeser wird je ENCODIERTEM Zustand zweimal gerufen (ein Spieler, ein
Gegner), also je Blatt der Netzsuche und je Record im Cache-Bau. Bezugspunkt
ist das K4-Kostentor: EIN memoisierter Loeser-Aufruf je Blatt kostete **+4,3
Prozent Wanduhr** (`PREREG_round_estimate_leaf_term.md` par.7b, gemessen).
**Und genau hier ist die K4-Zahl KEINE Prognose, sondern eine Untergrenze:**
K4s zusaetzlicher Aufruf war laut Registratur-Eintrag ein HashMap-TREFFER --
woertlich: "der Feature-Bau desselben Blattes hat den Schluessel fuer beide
Spieler schon gefuellt, es bleibt ein HashMap-Treffer"
(`engine/src/knob_registry.rs:111`, Eintrag `MOSAIC_ROUND_EST_C`, in dieser
Sitzung gelesen). Die
Projektion ist dagegen ein eigener Cache-Eintrag; beim Spieler am Zug aendert
sich das Brett mit jeder Musterreihen-Fuellung, dort ist sie meist ein
FEHLSCHLAG. **ANNAHME (ungeprueft), sauber formuliert:** die Projektion
verdoppelt ungefaehr die Loeser-Arbeit des Encoders (der rechnet je Zustand
schon zweimal `solve_round_final_score`, Abschnitt 5); welcher Anteil der
Blattkosten das ist, ist unbekannt. Beim Gegner greift die Memoisierung fast
immer (sein Brett aendert sich im Drafting nicht). Was sie gar nicht deckt: der
Cache-Bau rekonstruiert je Record einen `GameState` (`json_to_state`). Beides
ist zu MESSEN, nicht zu schaetzen:

* Kostentor der Suche, Schwelle 25 Prozent (par.5 Schritt 1, gleiche Form wie
  Nr. 35),
* Bauzeit eines Blocks gegen die Bestandszeit (`docs/measured_runtimes.md`).

### 18.5 LESART VORAB

* **Tor 1:** gepaart gegen `v29-b03` (der Sicht-Arm ist die Basislinie dieses
  Fensters), **zwei Seeds a 200 Paare, Blockgroesse 5, ohne Frueh-Stopp**, mit
  `--log-games`.
* **Netz-Gesundheit** nach par.6d des Fensters: leben die 90 neuen Spalten
  (Spaltennorm > 0 nach dem Training)? Eine Spalte mit Norm exakt 0 heisst
  "nie gesehen", und dann ist ein Nullbefund kein Befund ueber Variante C.
* **Primaerkanal neben den Siegen sind die beiden benannten Nutzniesser:**
  volle Spalten je Partie (Vollendung, nicht Teilspalten) und belegte
  Spezialfelder je Partie. Dazu die sechs Standard-Kennzahlen (CLAUDE.md).
* **Was die Werte bewegen KANN, ohne dass Staerke folgt:** die Projektion ist
  eine Vorschau auf das punktemaximale Tiling der JETZT vollen Reihen, nicht auf
  das spaeter gespielte -- zwischen Blatt und Rundenende fuellen sich Reihen
  weiter.

### 18.6 WAS DURCH DIESEN BAU ROT WIRD (und was nicht)

* **`contract_hash_matches_pinned_literal`** (`lib.rs`): `INPUT_SIZE` steckt im
  Vertragsstring, der Hash wechselt. Erwartet und bewusst.
* **`feature_golden_hash_matches_fixture`**: der Vektor ist 90 Werte laenger,
  die Fixture hasht die VEKTOREN. Neu zu erzeugen, vom Koordinator.
* **`net_parity_hash_matches_champion_fixture` bleibt GRUEN** -- anders als bei
  Abschnitt 16. Begruendung: sie hasht die RECORDS (`self_play.rs`, Kopf der
  Fixture), und Variante C legt KEIN Record-Feld an; eine Encoder-Verlaengerung
  oder -Normierung bewegt sie nachweislich nicht (dritter Beleg in
  `PREREG_stack_top_feature.md` par.17a). Wird sie trotzdem rot, ist das ein
  Befund und kein Formfehler.
* **Anker-Invarianz:** der Heuristik-Pfad liest den Encoder nicht
  (`mcts.rs`/`heuristic_v3.rs`/`round5.rs` rufen `solve_round_final_score`,
  nicht `features.rs`), und der neue Projektions-Cache ist eine eigene
  thread-lokale Map. Die Pruefung bleibt trotzdem Pflicht, sobald das Wheel
  neu gebaut ist (CLAUDE.md).
* **Reihenfolge-Falle bei der Paritaetssonde:**
  `tools/probes/feature_parity_rust_python.py` vergleicht den ROHEN Rust-Export
  (`state_features_from_json`, dann 884 Werte) gegen den Zwilling, und der
  haengt an `config.INPUT_SIZE`. Zwischen Wheel-Bau und der 884 in `config.py`
  meldet die Sonde darum eine Laengen-Abweichung -- kein Befund, sondern die
  Zwischenstellung. Die Sonde gehoert NACH die `config.py`-Zeile. (Der
  Befund aus par.17.7 (f), Kanal 76 im Korpus, ist davon unabhaengig und
  weiter offen.)

### 18.7 BAUSTAND 2026-09-17 (Opus-Agent): CODE VOLLSTAENDIG, NICHT KOMPILIERT

Der Code steht, aber **kein `cargo` gelaufen**: waehrend des ganzen Zuges lief die
Counterfactual-Sonde eines Parallel-Agenten
(`tools/probes/counterfactual_tiling_ranking.py --sims 400 --draws 6
--max-cands 4 --rounds 4 --max-files 400`, zwei Python-Prozesse, ueber vier
Minuten hinweg mehrfach geprueft). Ein Build ist Volllast und damit Nebenlast
(CLAUDE.md) -- also bewusst nicht gestartet.

| Datei | Was |
| --- | --- |
| `engine/src/tiling_solver.rs` | `PROJECTION_CELLS`/`PROJECTION_SLOTS`, `TilingProjection` (Default manuell, `Copy`), `board_masks`, `project_rec` (Zwilling von `solve_rec`), `compute_projection`, `cached_projection`, `pub fn project_max_tiling`; `PROJECTION_CACHE` im bestehenden `thread_local!`-Block, `clear_tiling_caches_for_test` raeumt sie mit; drei neue Tests |
| `engine/src/features.rs` | `INPUT_SIZE` 794 -> 884; Abschnitt 17 mit `TILING_PROJECTION_VALUES`, `push_tiling_projection`, `tiling_projection_from_state`, `tiling_projection_from_json`, `pub fn tiling_projection_values_from_json`; Anhang in BEIDEN Pfaden; drei neue Tests; `sight_appendix_is_appended_after_755` auf den 16er-Bereich begrenzt (sonst haette die Laengenzusage von Abschnitt 16 den Zuwachs mitgemessen) |
| `engine/src/lib.rs` | additiver Export `tiling_projection_values_from_json` samt Registrierung im Modul; Vertragshash-Literal `39994362fba145a6` -> `cfd94509f0aab102`, NACHGERECHNET (FNV-1a-64 ueber den kanonischen String; dieselbe Rechnung mit 794 reproduziert das alte Literal) |
| `engine/py/neural_net.py` | `TILING_PROJECTION_VALUES`/`LEN_WITH_TILING_PROJECTION`; Abschnitt 17 im Zwilling, der die 90 Werte ueber `_tiling_projection_values` aus dem Wheel holt (harter Fehler, wenn der Export fehlt); Scharfschaltung an `config.INPUT_SIZE` wie bei Abschnitt 16 |
| `docs/architecture_reference.md` | neue Zeile in "Wo der Code Information ABSICHTLICH vernichtet": die `json_to_state`-Rekonstruktion im JSON-Pfad ist eine neue AUFRUFSTELLE einer bestehenden Mischregel, und nichts davon geht in die 90 Werte ein |
| `docs/generation_naming.md` | `v29-b07` reserviert, weitere Arme ab `v29-b08` |
| `evaluations/v29_program_agent_plan.md` | Fahrplan-Zeile 36c |

`python tools/check_conventions.py`: alle Regeln gruen (die drei
Groessen-Ratschen-Warnungen sind Bestand). `python -m py_compile` auf
`neural_net.py` gruen.

**Offen, in dieser Reihenfolge (Koordinator):** `cargo test --release --lib`
und `cargo test --release --no-run` (letzteres wegen der pre-push-Falle);
Feature-Golden-Fixture NEU ERZEUGEN (bewusster Entscheid, der Vektor ist
laenger); Wheel bauen und `config.INPUT_SIZE` auf 884 IM SELBEN ZUG; Anker-Drift
und Anker-Konservierung; die Paritaetssonde ERST danach; Kostentor; Cache-Bloecke;
Training; Tor 1 gegen b03.

### 16.10 ENTSCHIEDEN (Nutzer 2026-09-17, nach 16.9 und 17.9): Variante A draussen, Stichentscheid als Knopf ins A/B, Variante C weiter

Nutzer woertlich: *"variante a bleibt draussen. c weiter wie geplant. tiling stichentscheid als knopf
bauen und im A/B messen"*.

1. **Variante A (N Neubefuellungen am Blatt) wird NICHT gebaut.** Die Prereg koppelt sie selbst an B
   (P5: "folgt laut par.7 nur, wenn B traegt"; "Kein Bau ohne eigene Registrierung"), B ist negativ
   (17.9), und v30+ bekommt keine neuen Vorregistrierungen (Nutzer 2026-09-16). par.4.3 (robuster
   Aggregator) faellt damit mit.
2. **Variante C laeuft weiter wie in par.18** (Arm `v29-b07`): Kompilieren waehrend des b08-Trainings,
   Wheel/INPUT_SIZE/Drift/Kostentor/Bloecke/Training/Tor 1 nach Tor 1 von b08 (Reihenfolge und
   Begruendung in `evaluations/STATUS.md` Abschnitt 1, Stand 08:20).
3. **Netz-Stichentscheid im Tiling wird ein Knopf und kommt ins A/B.** Aus `NET_TILING_TIEBREAK_ENABLED`
   (`tiling_solver.rs:1032`, Leser `:1778` und `:1835`, Runden 2-4) wird `MOSAIC_NET_TILING_TIEBREAK`
   (Spec-Feld `net_tiling_tiebreak`, 0/1, **Default 1 = heutiges Verhalten**, bitidentisch), Muster
   `round_transition_leaf`. Baustand folgt in 16.11 (Agent), Kompilat und Tore beim Koordinator.

**Messung (bindend, Arm aus DIESER offenen Prereg, keine neue Registrierung):** Champion
`v28-b02_brierbest` @400 gegen sich selbst, Champion-Spec plus `net_tiling_tiebreak: 0` (Arm "aus")
gegen `: 1` (Arm "an", Bestand), gepaart, Blockgroesse 5, Deckel 200 Paare, SPRT alpha = beta = 0,001,
`--log-games`, 10 Threads, Seed 20261170, Kette `tools/night_tiling_tiebreak_ab.sh`; Laufzeit ins
Artefakt; sechs Standard-Kennzahlen, dazu als Primaerkanal der Sonde die Plattenpunkte je Kriterium
und die Spaltenvollendungen (der Zweig entscheidet Tiling-Plaene). Vorher Anker-Drift und
-Konservierung auf dem neuen Wheel (Pflicht nach jeder Engine-Aenderung); ob der Anker-Pfad den
Zweig ueberhaupt liest, stellt 16.11 mit Pruefstelle fest.

**Lesart vorab (Entscheidungsmass Block-Ebene wie par.5):**
* "aus" signifikant besser (Block-z >= 1,96 zugunsten aus) -> der Sonden-Befund traegt in der Arena;
  `net_tiling_tiebreak: 0` wird Rezept-Knopf der v30-Spec (Nutzer-Entscheid, Champion behaelt seine
  gemessene Identitaet, neue bXX nach `feedback_measured_identity_gets_own_bxx`).
* flach (|z| < 1,96) -> die Arena sieht den Zweig nicht; dann gilt die Korrektheits-Regel
  (`feedback_correctness_over_measured_benefit`): die Sonde belegt, dass der Zweig die exakte Rechnung
  zu 70 Prozent falsch ueberstimmt (16.9c, 46 von 156). Empfehlung des Koordinators fuer diesen Fall:
  aus. Nutzer-Entscheid.
* "aus" signifikant schlechter -> der Zweig traegt trotz falscher Einzelkippungen (z.B. weil er
  Punktgleichheit bricht, die die Sonde nicht als Kippung zaehlt); bleibt an, 16.9c wird Diagnostik.

Kosten (gemessen an `rt_leaf_on_vs_off`, 17.9): 13,1 s je Partie mit 10 Threads, 400 Partien rund
87 min. Eintaktung: parallel zum b07-Training als der eine CPU-Auftrag (STATUS Abschnitt 1).

### 16.11 Baustand Knopf net_tiling_tiebreak (2026-09-17)

Gebaut nach 16.10 Punkt 3, Muster `round_transition_leaf`. **Default ist der BESTAND** – der
Knopf steht auf 1, also bitidentisch; die Polung ist damit umgekehrt zu seinen Nachbarn (bei
`round_transition_leaf` ist 0 der Bestand, hier 1). Nicht kompiliert (die Messkette lief), der
Koordinator baut.

**Geaenderte Dateien und Zeilen (Quellstand nach dem Bau):**

| Datei | Zeilen | Was |
| --- | --- | --- |
| `engine/src/tiling_solver.rs` | :1046 / :1051 | `NET_TILING_TIEBREAK_DEFAULT = 1` und `NET_TILING_TIEBREAK_OFF = 0` ersetzen `NET_TILING_TIEBREAK_ENABLED: bool = true` |
| | :1058 | `net_tiling_tiebreak_applies(mode, round_number)` – EIN Praedikat fuer beide Leser, damit das Rundenfenster `2..=4` nicht zweimal dasteht |
| | :1761 / :1816 | neuer Parameter an `best_first_step_exact_or_valued_envelope`, Lesestelle 1 (Zweig 2) |
| | :1840 / :1877 | neuer Parameter an `best_first_step_envelope_valued`, Lesestelle 2 (Gleichstand im K3-(d)-Zweig) |
| | :1723 | die Wrapper `best_first_step_exact_or_valued[_ex]` reichen den DEFAULT durch (Bestandsform) |
| `engine/src/net_mcts.rs` | :542 | `read_net_tiling_tiebreak_env()` (`MOSAIC_NET_TILING_TIEBREAK`, ungueltig -> 1 plus einmalige Warnung) |
| | :1026 | `SearchConfig::net_tiling_tiebreak` |
| | :1138 | `from_env` |
| | :1196 | Feld in `KNOWN_FIELDS` |
| | :1500 | Spec-Parsing, OPTIONAL mit Default 1, `2` und `"x"` sind harte Fehler |
| `engine/src/self_play.rs` | :3593 | `PlayerLoopConfig::net_tiling_tiebreak` (je Seite), acht Konstruktionsstellen |
| | :2388 / :2439 / :2498 | `resolve_tiling_step_tiebreak` (neu), `resolve_tiling_step_with_variant` und `tiling_step_with_variant` mit Parameter |
| `engine/src/referee.rs` | :212 / :678 | Worker-Pfad aus `search_config`, In-Process-Pfad aus der Spec DIESER Seite |
| `engine/src/py.rs` | :1151 | GUI-Sitzung aus `SearchConfig::from_env()` |
| `engine/src/lib.rs` | :863 | Lauf-Manifest `net_tiling_tiebreak` |
| `engine/src/knob_registry.rs` | :138 | `KnobEntry` (Waechter `all_mosaic_env_vars_in_code_are_registered`) |
| `engine/examples/kernbeweis_910002_probe.rs` | :128 | Struct-Literal nachgezogen (sonst bricht der pre-push-Hook) |
| `docs/knobs.md` | generiert | `python -X utf8 tools/generate_knob_docs.py`, 128 Knoepfe |
| `models/tiebreak_on.spec.json`, `models/tiebreak_off.spec.json` | neu | Champion-Spec plus `net_tiling_tiebreak: 1` bzw. `0` |
| `tools/night_tiling_tiebreak_ab.sh` | neu | A/B-Kette, `bash -n` gruen |

**Transportweg des Werts (kein Env-Getter im Solver).** Der Wert gehoert der SEITE, nicht dem
Prozess: ein prozessweiter Getter waere fuer das A/B "Champion mit gegen Champion ohne" im
selben Prozess unbrauchbar, genau die Lage, die `PREREG_agent_encapsulation.md` par.1 beschreibt.
Er wandert deshalb als Parameter:

`Spec-Datei / MOSAIC_NET_TILING_TIEBREAK` -> `SearchConfig` (net_mcts.rs:1026) ->
`PlayerLoopConfig.net_tiling_tiebreak` je Seite (self_play.rs, aus `search_config_a` bzw.
`search_config_b` der Netz-gegen-Netz-Arena, aus `search_config` im Self-Play) ->
`tiling_step_with_variant` / `resolve_tiling_step_with_variant` (self_play.rs:2433 und :2492) ->
`best_first_step_exact_or_valued_envelope` (tiling_solver.rs:1761) -> Lesestelle 1 (:1816) und,
ueber den K3-(d)-Zweig, `best_first_step_envelope_valued` (:1840) -> Lesestelle 2 (:1877).
Nebenpfade: Referee-Worker ueber `search_config` (referee.rs:212), Referee in-process ueber die
Spec der Seite (referee.rs:678, nur wenn fuer die Seite ueberhaupt ein Netz geladen ist), GUI
ueber `SearchConfig::from_env()` (py.rs:1151). Alle Bestands-Wrapper (`resolve_tiling_step`,
`tiling_step`, `best_first_step_exact_or_valued[_ex]`) reichen den DEFAULT durch und sind damit
unveraendert.

**Anker-Befund (Punkt 2 des Auftrags, geprueft, nicht abgeleitet): der Heuristik-Pfad erreicht
KEINE der beiden Lesestellen.** Drei unabhaengige Sperren, jede fuer sich ausreichend:

1. Beide Zweige verlangen einen Evaluator: `tiling_solver.rs:1817` und `:1879` sind je ein
   `if let Some(eval) = evaluator`. Ohne Evaluator faellt Lesestelle 1 auf
   `best_first_step_exact` durch und Lesestelle 2 auf den zuerst gefundenen Gleichstands-
   Kandidaten.
2. Der Heuristik-Pfad uebergibt IMMER `None`: `self_play.rs:2460`
   (`None => best_first_step_exact_or_valued(state, pi, None)`), und die Heuristik-Seiten tragen
   `tiling_net: None` (self_play.rs:4469 Heuristik-Self-Play, :5006 Heuristik-Seite der
   Elo-Verankerungs-Arena, :8003 Test).
3. Lesestelle 2 sitzt ueberdies hinter `!envelope.is_off()` (tiling_solver.rs:1805); die
   Heuristik-Pfade uebergeben `EnvelopeTilingParams::OFF` (self_play.rs:2382 und :2395, referee.rs:209),
   und auch die CHAMPION-Spec `models/frozen_champions/v28-b02/spec.json` hat
   `envelope_tiling_w = 0.0` und `envelope_tiling_value_w = 0.0`: im A/B wirkt also allein
   Lesestelle 1. Lesestelle 2 ist trotzdem mitgeschaltet, sonst haette der Knopf eine stille
   Luecke, sobald K3 (d) einmal an ist.

Die Anker-Spec `models/frozen_heuristics/hv4_anchor/spec.json` traegt das neue Feld nicht; weil es
OPTIONAL mit Default 1 ist, laedt sie unveraendert und beschreibt weiter dasselbe Verhalten.
Der Referee-Zweig in-process liest die Spec nur, wenn fuer die Seite ein Netz geladen ist
(referee.rs:675-680): der Anker-Lauf bezahlt keinen zusaetzlichen Dateizugriff.

**Tests (geschrieben, nicht gelaufen):**

* `tiling_solver::tests::net_tiling_tiebreak_default_keeps_todays_behaviour` – Tor (a): mit
  Default 1 kippt der diskriminierende Evaluator die punktegleiche Wahl wie bisher, und zwar
  identisch zum Bestands-Wrapper `best_first_step_exact_or_valued`.
* `…::net_tiling_tiebreak_off_falls_back_to_exact_points` – Tor (b), Lesestelle 1: bei 0
  entscheidet `best_first_step_exact`, der Evaluator kippt nichts mehr.
* `…::net_tiling_tiebreak_off_also_disables_the_envelope_branch_tiebreak` – Tor (b),
  Lesestelle 2: `best_first_step_envelope_valued` mit `w_tile = w_val = 0` (bereinigter Score
  gleich Punktzahl, Gleichstandsgruppe gleich punktegleiche Spitze); an -> Evaluator entscheidet,
  aus -> der zuerst gefundene Kandidat.
* `…::net_tiling_tiebreak_applies_only_in_rounds_2_to_4_and_only_when_on` – Rundenfenster und
  Polung des gemeinsamen Praedikats.
* `net_mcts::tests::search_config_spec_net_tiling_tiebreak_is_optional_and_validated` – Tor (c):
  Feld fehlt -> 1 (der Bestand), 0 kommt an, `2` und `"x"` werden hart abgewiesen und die
  Fehlermeldung nennt das Feld.

**Kette.** `tools/night_tiling_tiebreak_ab.sh`: gehaertete Warteschleife (`cpu_frei`/`warte_frei`
aus `night_v29_b08_head_pair.sh`, PowerShell-Prozessfilter mit dem Namensabgleich auf python),
`set -uo pipefail`, keine Pipe hinter dem langen Lauf, `python -X utf8 -u`. Erste Pruefung ist
`grep -q net_tiling_tiebreak engine/src/net_mcts.rs`: ohne den Knopf waeren beide Arme derselbe
Spieler, und die Spec-Dateien wuerden als unbekanntes Feld abgewiesen. Dann `paired_gating.py`
mit `--sims-a 400 --sims-b 400 --c-puct 1.5 --block-size 5 --max-pairs 200 --sprt-alpha 0.001
--sprt-beta 0.001 --threads 10 --log-games --no-promote-winner`, Seed 20261170, Ausgabe
`evaluations/artifacts/tiebreak_on_vs_off_s20261170.json`, danach `arena_column_probe.py
--artifact` und `plate_points_from_arena.py ... --block 5`. KEIN Kostentor: der abgeschaltete
Knopf spart bis zu `NET_TILING_TOPK` = 12 Vorwaertspaesse je Tiling-Zug, ein Aufschlag ist
strukturell ausgeschlossen.

**Was der Koordinator beim Kompilieren erwarten muss.** Vier Signaturen haben einen Parameter
mehr (`best_first_step_exact_or_valued_envelope`, `best_first_step_envelope_valued`,
`resolve_tiling_step_with_variant`, `tiling_step_with_variant`) und `SearchConfig` ein Feld; die
einzige Aufrufstelle ausserhalb von `src/` ist das Struct-Literal in
`engine/examples/kernbeweis_910002_probe.rs`, sie ist nachgezogen –
`cargo test --release --no-run` bleibt die Pflichtpruefung vor dem Push. Die Netz-Paritaets-
Fixture darf sich NICHT aendern (kein Record-Feld, keine Feature-Aenderung), und Anker-Drift wie
-Konservierung muessen GRUEN sein; ist eines davon rot, liegt es nicht an der Polung des
Defaults, sondern an einem uebersehenen Aufrufer.

### 18.5 Kompilat und Abnahme (Koordinator, 2026-09-17)

**10:12-10:15, `cargo test --release --lib`** (neben dem GPU-Training v29-b08 als der eine CPU-Auftrag;
Build 45 s, Tests 99,8 s): **683 bestanden, 1 rot, 19 ignoriert.** Das eine Rot ist die vorab
angekuendigte `feature_golden_hash_matches_fixture` (Vektor 90 Werte laenger, `features.rs:3501`,
`got=3e0b3d2ef7fbef28 want=4cfafb6867c5f368`), wird bewusst neu erzeugt. Gruen darunter: die neuen
Tests aus par.18 (Projektion, Abschnitt 17) und 16.11 (Stichentscheid-Knopf), das Vertragshash-Literal
`cfd94509f0aab102` (`contract_hash_matches_pinned_literal`) und die Netz-Paritaets-Fixture des Champions
(`net_parity_hash_matches_champion_fixture`, dritter Beleg fuer par.17a: eine reine Encoder-Verlaengerung
bewegt den Record-Hash nicht). Naechste Schritte in der Reihenfolge aus STATUS Abschnitt 1: `--no-run`
(Beispiele, Benches), Fixture-Neubau, Wheel-Bau; Installation, INPUT_SIZE 884, Drift, Kostentor erst
nach Tor 1 von b08.

**10:20-10:24:** `cargo test --release --no-run` gruen (Beispiele und Benches kompilieren, pre-push-Falle
zu); `feature_golden_hash_matches_fixture` mit `MOSAIC_UPDATE_FEATURE_FIXTURE=1` neu erzeugt (130 Zeilen,
`engine/tests/fixtures/feature_contract_v1.txt`, Kopf: INPUT_SIZE=884, Grund 2026-09-17 eingetragen) und
ohne Variable in frischem Prozess gruen. **Wheel GEBAUT 10:14:23** (`python -m maturin build --release`,
`engine/target/wheels/mosaic_rust-0.1.0-cp314-cp314-win_amd64.whl`, 6.567.159 Byte, Fixture-Test plus Bau
72 s), **NICHT installiert** -- Installation, `config.INPUT_SIZE` 884, Drift, Paritaet, Kostentor, Bloecke,
Training und Tor 1 laufen als Kette `tools/night_v29_b07_variante_c.sh` nach Tor 1 von b08 (18.6).

### 18.6 Kette zur Abnahme und Messung (geschrieben 2026-09-17, nicht gestartet)

`tools/night_v29_b07_variante_c.sh`, `bash -n` gruen, noch NIE gelaufen. Sie faehrt genau die
Reihenfolge aus STATUS Abschnitt 1 (Koordinator-Entscheid 08:20) und stoppt bei jedem roten Tor;
ROT ist ueberall ein Nutzer-Entscheid, die Kette repariert nichts.

**Vorbedingung, die die Kette NICHT selbst herstellt:** `config.py` Zeile 49 muss von Hand auf
`INPUT_SIZE = 884` stehen (par.18.3 Punkt 5). Stufe 0 bricht sonst ab. Grund ist die
Reihenfolge-Falle aus par.18.6 oben: zwischen Wheel und `config.py` meldet die Paritaetssonde nur
die Zwischenstellung.

**Stufen, Exit-Codes in Klammern:**

0. Vorbedingungen (1/2): `INPUT_SIZE = 884`, `FEATURE_FORMULA_VERSION` in `config.py`, Wheel
   `engine/target/wheels/mosaic_rust-0.1.0-cp314-cp314-win_amd64.whl` (gebaut 10:14, nicht
   installiert), Champion, Champion-Spec, b03-Modell, Fenster, Traeger-Manifest,
   Anker-Artefakt, Kostentor-Referenz. Danach `warte_frei` (dieselbe Prozessliste wie
   `night_v29_b08_head_pair.sh`) -- das Warten steht VOR der Installation, weil `pip install`
   scheitert, solange ein Python-Prozess das `.pyd` haelt.
1. Wheel installieren (10), Vertrag pruefen (11/12): der Export
   `tiling_projection_values_from_json` muss da sein (`lib.rs:1787`, registriert `lib.rs:2342`),
   `engine_config_json()` (`lib.rs:753`) muss `input_size` 884 melden (Feld `lib.rs:768`), und
   `config.INPUT_SIZE` muss ebenfalls 884 sein. Contract-Hash und Engine-Version werden gedruckt
   (Erwartung `cfd94509f0aab102`, 18.5).
2. Anker-Invarianz nach Skill `mosaic-anchor-invariance`, Artefakt
   `models/frozen_heuristics/hv4_anchor` (Leitersegment 2): DRIFT (20) im Default-Modus,
   KONSERVIERUNG (21) mit `--venv`, beide mit `--out`. Erwartung GRUEN: der Heuristik-Pfad liest
   den Encoder nicht (par.18.6 oben). Kosten gemessen 22,2 s und 13,4 s.
3. Paritaetssonde `tools/probes/feature_parity_rust_python.py` (Aufruf ohne Argumente, wie im
   Dateikopf). Die Kette stoppt NUR bei `kind == "shape"` (30), also bei einem Laengenfehler.
   Wertabweichungen werden namentlich berichtet und laufen weiter: erwartet ist der bekannte
   Kanal-76-Befund in der Grundmenge `corpus` (Planes, Erreichbarkeit je Zelle, 2 von 300
   Zustaenden, Ursache A2-Phantom-Fix, `PREREG_rust_data_layer.md` par.9a) -- er ist aelter als
   Variante C und unabhaengig von ihr.
4. **Kostentor par.18.4 (3).** Form: Champion `v28-b02_brierbest` gegen sich selbst, Champion-Spec
   BEIDSEITS, 2 x 20 Paare (Seeds 20261180 / 20261181), Blockgroesse 5, 10 Threads, `--log-games`.
   Gemessen wird allein `laufzeit.s_je_partie`; Variante C hat keinen Knopf, also gibt es keinen
   Aus-Arm im selben Prozess -- verglichen wird gegen die vor der Installation gemessene Zahl.
   **Referenz, gleiche Form: 13,326 s je Partie** (`evaluations/artifacts/rt_leaf_kosten_ohne_s20261151.json`,
   `laufzeit.s_je_partie`, 20 Paare, 10 Threads, Logs, Spec = Champion-Spec plus abgeschalteter
   rt-leaf-Knopf; in dieser Sitzung am Artefakt gelesen). Zweite Orientierung, ANDERE Form (200
   Paare): 13,069 s je Partie (`rt_leaf_on_vs_off_s20261152.json`, par.17.9). Schwelle **+25
   Prozent** auf die 20-Paare-Referenz. Verdikt-Datei
   `evaluations/artifacts/variante_c_kostentor_verdikt.txt` mit beiden Prozentsaetzen. Riss heisst
   STOPP VOR dem Blockbau. *Ungeprueft/Vorbehalt:* die Referenzlaeufe liefen am 2026-09-17 um 01:35
   neben dem b06-GPU-Training, die neuen Laeufe warten auf eine freie CPU -- die Lastbedingungen
   sind aehnlich, aber nicht identisch.
5. Split (13/17): `tools/window_train_split.py` mit denselben Argumenten wie die b08-Kette, Listen
   `data/window_v29_b07_train.txt` / `_val.txt`, Schluessel aus der Ausgabe. Die Kette bricht ab,
   wenn der Schluessel `421448d12eb8` herauskommt: das ist der 794er Schluessel von b08, dann waere
   die 884 nicht im Schluessel angekommen (`file_cache_key.py:158` und `corpus_dataset.py:490`
   lesen `config.INPUT_SIZE`).
6. Bloecke und Monolith unter dem neuen Schluessel (14/16), `--workers 6`, `--merge-out`, Bauzeit
   in Sekunden gedruckt, Stempel `mosaic_cache_key` gegen den Schluessel geprueft.
   Bestandsvergleich: 1.964 s fuer 2.800 Dateien unter 794 (`docs/measured_runtimes.md`, b08-Kette).
7. **Training `v29-b07` = GENAU das b03-Rezept** (`models/manifest_train_v29-b03_20260914_111513.json`,
   `cli_args` in dieser Sitzung gelesen): `--epochs 12 --lr 5e-05 --lr-schedule cosine --lr-t-max 12
   --val-frac 0.05 --encoder 2d --value-head wdl --value-target-variant nortv
   --value-target-lambda 0.7 --ownership-head-2d --ownership-weight 1.0 --opp-points-head
   --endgame-head --moon-loss-weight 1.0 --destretch-a 0.0051 --destretch-b 1.9269
   --select-by-brier --fast-loader --seed 20260941 --load v28-b02_brierbest
   --file-list data/window_v29.txt`; die einzigen Abweichungen sind `--name v29-b07` und
   `--cache-file` (b03 hatte `cache_file: null`).
   **Warmstart 794 auf 884 ist GEBAUT und geprueft** (`train.py:1684-1698`, in dieser Sitzung
   gelesen): ist `flat_branch.0.weight` im Checkpoint schmaler als im neuen Modell (gleiche
   Zeilenzahl, kleinere Spaltenzahl), werden die fehlenden Eingangsspalten mit NULL aufgefuellt
   statt die Schicht frisch zu starten -- `torch.cat([_o, _pad], dim=1)`, `train.py:1695-1696`.
   Der Flach-Zweig ist `nn.Linear(input_size, hidden_size)` (`neural_net.py:2101`), die
   Gewichtsform also `[hidden, input]`; die 90 neuen Werte haengen hinten (par.18.3 Punkt 3), also
   greift genau dieser Zweig. Das Netz ist im ersten Schritt exakt das alte, die neuen Merkmale
   wirken erst, wenn das Training sie ankoppelt. Dasselbe Muster hat 755 auf 794 getragen
   (Kommentar ebenda: `PREREG_stack_top_feature.md` par.7, v24-b04, 2026-09-05). Die Kette druckt
   vorher, dass die Zeile "Eingangsbreite 794 -> 884, 90 neue Spalten null-initialisiert" in der
   Trainingsausgabe erscheinen MUSS; bleibt sie aus, faellt der Flach-Zweig unter
   "Shape-Mismatch, startet frisch" (`train.py:1699-1702`) und der Arm waere gegen b03 nicht
   vergleichbar.
8. **Tor 1 (15):** `v29-b07` gegen `models/alphazero_v29-b03_brierbest.onnx`, Champion-Spec
   beidseits, zwei Seeds **20261190 / 20261191**, je 200 Paare, Blockgroesse 5, SPRT 0,001/0,001
   (also ohne Frueh-Stopp), `--threads 10 --log-games --no-promote-winner`, Artefakte
   `evaluations/artifacts/tor1_v29-b07_vs_b03_s<seed>.json`; danach je Lauf
   `tools/probes/arena_column_probe.py --artifact` und `tools/plate_points_from_arena.py ... --block 5`.
9. Abschlusszeile "faellig danach": Manifest-Diff b07 gegen b03 (erwartet GENAU `name`,
   `cache_file` und die INPUT_SIZE-abhaengigen Felder; jedes weitere abweichende Feld ist ein
   Befund), Verdikt nach par.18.5 auf Block-Ebene mit den beiden benannten Nutzniessern,
   Netz-Gesundheit der 90 neuen Spalten (Spaltennorm > 0), die sechs Standard-Kennzahlen,
   Laufzeiten nach `docs/measured_runtimes.md`, Registrierung samt Zeile-1-Kopf und
   Index-Generator.

**Was die Kette bewusst NICHT tut:** sie setzt `config.INPUT_SIZE` nicht, sie baut kein Wheel, sie
promoviert nichts (`--no-promote-winner` in jedem Arena-Aufruf), und sie loescht nichts.

### 18.7 Abnahme auf dem installierten Wheel (2026-09-17, 13:59-14:01)

Kette `tools/night_v29_b07_variante_c.sh`, Start 13:59:30 nach Tor 1 von b08, `config.INPUT_SIZE` vorher von
Hand auf 884 (Z.49, Kommentar um Abschnitt 17 ergaenzt). Maschine frei.

* **Wheel installiert** (`mosaic_rust-0.1.0-cp314-cp314-win_amd64.whl` vom 10:14), Vertragspruefung gruen:
  Export `tiling_projection_values_from_json` vorhanden, `engine_config_json().input_size` = 884,
  `config.INPUT_SIZE` = 884 (Kettenausgabe Stufe 1).
* **Anker-Drift GRUEN** (14:00:17, "1/1 Dateien Feld fuer Feld gleich", Live-Wheel gegen Artefakt hv4_anchor)
  und **Anker-Konservierung GRUEN** (14:00:36, Artefakt-venv). Die Engine-Aenderung (Encoder 884, Projektion,
  Stichentscheid-Knopf) bewegt den Anker nicht; kein neues Leitersegment noetig.
* **Paritaetssonde Rust gegen Python** (`feature_parity_rust_python.json`, 14,3 s): Flachvektor **884 Werte
  gleich in 1.033 von 1.033 Zustaenden** (733 frische pygame-Zustaende plus 300 Korpus-Zustaende aus
  `selfplay_v26-b01-policy_*`), also liefert der Wheel-Export fuer Abschnitt 17 im Python-Zwilling genau
  dieselben 90 Werte wie der Rust-Pfad; Planes 733 von 733 frisch gleich, im Korpus 298 von 300 -- die
  zwei Abweichungen sind der bekannte Kanal-76-Befund (`index_unraveled [76, 5, 1]`, Python 0 gegen Rust 1,
  A2-Phantom-Fix, `PREREG_rust_data_layer.md` par.9a, dort ebenfalls 2 von 300). Nichts Neues durch
  Variante C; `gate_passed=False` der Sonde ist dieser Altbefund, Kette laeuft weiter (nur Laengenfehler
  stoppen).
* Kostentor (18.4) laeuft seit 14:01:12; Ergebnis folgt in 18.8.

### 18.8 Kostentor GEMESSEN (2026-09-17, 14:01-14:16): HAELT

Champion `v28-b02_brierbest` @400 gegen sich selbst, Champion-Spec beidseits, 2 x 20 Paare (Seeds
20261180/20261181), Blockgroesse 5, 10 Threads, `--log-games`, exklusiv. Ergebnis je Lauf 20:20 mit 20 Splits
(gleiche Spec beidseits, wie erwartet). Grundmenge Partien, Einheit Sekunden je Partie (`laufzeit.s_je_partie`).

| Lauf | s je Partie |
| --- | --- |
| neu, 884-Wheel mit Projektion, Seed 20261180 | 11,837 |
| neu, Seed 20261181 | 11,339 |
| **neu, Mittel** | **11,588** |
| Referenz par.18.6 (20 Paare, `rt_leaf_kosten_ohne_s20261151.json`, 01:35 neben GPU-Training b06) | 13,326 |
| Orientierung (200 Paare, `rt_leaf_on_vs_off_s20261152.json`, Aus-Arm) | 13,069 |
| **exklusive Vergleichsgroesse, alter 794-Wheel: Tor 1 b08 gegen b03, 11:21-13:58, 800 Partien** | **11,515** |

**Verdikt:** Aufschlag gegen die registrierte Referenz **-13,0 Prozent**, Schwelle +25 -> **HAELT**
(`variante_c_kostentor_verdikt.txt`). Die registrierte Referenz lief aber NEBEN einem GPU-Training und ist
damit langsamer als der exklusive Lauf; der ehrlichere Vergleich ist die exklusive Zahl vom selben Tag auf dem
alten Wheel (Tor 1 b08, 11,5 s je Partie, gleiche Netzarchitektur 2d/794-Eingang, andere Modelle): dagegen
**+0,6 Prozent**. Der Loeser im Encoder kostet in der Suche also praktisch nichts Messbares -- vereinbar
mit dem Kostentor-Befund von K4 (dort +4,3 Prozent mit Loeser-Aufruf, `knob_registry.rs:111`: der
Tiling-Cache faengt die meisten Aufrufe). Die ANNAHME aus 18.4 ("verdoppelt grob die Loeser-Arbeit") war
zu pessimistisch. Was NICHT gemessen ist: die Kosten je Record im Blockbau (`json_to_state`-Rekonstruktion
plus Projektion); die kommen mit der Bauzeit in 18.9.

### 18.9 Bloecke und Monolith unter 884 (2026-09-17, 14:17-14:52)

Split byte-gleich mit b08 und b03; Schluessel `790ac07353a6` (884, Formel-Version, FROM_RUST=1); Bloecke plus
Merge fuer 2.800 Dateien mit 6 Workern **2.144 s** (exklusiv), Stempel gleich dem Schluessel. Vergleich am
selben Tag unter gleichen Bedingungen: b08 unter 794 **1.964 s** (par.10.5 der Minimalkern-Prereg). **Die
Projektion kostet im Blockbau +180 s = +9,2 Prozent** (Grundmenge 2.800 Dateien, 4.538.842 Zustaende; je
Zustand rund 40 Mikrosekunden zusaetzlich, Herleitung aus der Differenz) -- das ist die
`json_to_state`-Rekonstruktion plus Projektion je Record (18.4, dort ungemessen). Training `v29-b07` seit
14:52:49 (Monolith per `--cache-file` bestaetigt, 2800 Dateien, 4.538.842 Zustaende), CUDA. **Warmstart-Zeile
(train.py:1697): `flat_branch.0.weight: Eingangsbreite 755 -> 884, 129 neue Spalten null-initialisiert`** --
nicht 90, weil der Warmstart `v28-b02_brierbest` ein 755er-Modell ist (Engine der v28-Zeit, STATUS Abschnitt 4);
b03 hat von demselben Checkpoint aus die 39 Spalten des Sicht-Anbaus (755 -> 794) genauso null-initialisiert
bekommen. Die 129 = 39 Sicht-Anbau (wie b03) + 90 Projektion (neu). Der Mechanismus greift wie in 18.6 gepruft;
kein Shape-Mismatch, kein Frischstart einer Schicht.

### 16.12 A/B Stichentscheid GEMESSEN (2026-09-17, 14:56-16:41): der Zweig TRAEGT, bleibt an

Aufbau wie 16.10: Champion `v28-b02_brierbest` @400 gegen sich selbst, Champion-Spec plus `net_tiling_tiebreak: 1`
(A = an, Bestand) gegen `: 0` (B = aus), 200 Paare, Blockgroesse 5, SPRT-Schranken +-6,91 nicht erreicht,
`--log-games`, 10 Threads, Seed 20261170. Nebenlast: GPU-Training v29-b07 (erlaubt), dadurch 15,5 s je Partie
statt 11,5 exklusiv; Laufzeit 6.183,2 s. Grundmenge Partien, Einheit Siege.

| Groesse | Wert |
| --- | --- |
| Siege an : aus | **224 : 176 von 400 = 56,0 Prozent** |
| Sweeps an / aus (Paare) | 45 / 21, Split 134; exakter Vorzeichentest **p 0,0043** |
| Diff je Paar, KI95 | +0,240 [+0,084; +0,396] |
| **Block-Ebene** (par.5 Entscheidungsmass) | 40 Bloecke a 10 Partien, Siegdiff an minus aus **+1,20 je Block, SE 0,35, z = +3,43** |
| eigene Punkte an / aus | 54,18 / 52,60 (**+1,59**) |
| Marge | +1,59 / -1,59 |

**Verdikt nach der Lesart 16.10, dritter Ausgang: "aus" ist signifikant schlechter (z +3,43).** Der Zweig
traegt in der Arena, obwohl die Sonde (16.9c) seine Einzelkippungen gegen die exakte Rechnung zu 70 Prozent
als falsch ausweist. **`net_tiling_tiebreak` bleibt auf 1 (Bestand), kein Rezept-Knopf; 16.9c ist ab jetzt
Diagnostik.** Die vorab benannte Aufloesung des Widerspruchs traegt: die Sonde zaehlt nur Paare MIT
Punktabstand als Kippung (M4, `counterfactual_tiling_ranking.py:417`); in der Partie wirkt der Stichentscheid
aber ueberwiegend dort, wo er Punktgleichheit bricht (Split 134 von 200 Paaren sind ohnehin Paare, in denen die
Seite den Ausschlag gibt), und dort ist "exakte Punkte" kein Massstab, weil beide Plaene gleich viele Punkte
haben. Was die Sonde als Fehler zaehlt, sind 8,2 Prozent der Paare mit Punktabstand; was der Zweig gewinnt,
ist die Wahl unter Gleichen. Ausserdem misst die Sonde gegen den Runde-5-Alpha-Beta in Runde 4 -- der
Stichentscheid wirkt in den Runden 2-4, wo die Rundenpunkte nur ein Teil des Spielwerts sind.

**Sechs Standard-Kennzahlen** (`arena_columns_tiebreak_on_vs_off_s20261170.json`, 400 von 400 nachgespielt;
`plate_points_tiebreak_on_vs_off_s20261170.json`; Mittel je Seite, Grundmenge Bretter):

| Kennzahl | an | aus | Diff |
| --- | --- | --- | --- |
| Reihen: volle Zeilen / Fuellungssumme / lange Reihen vollendet | 0,160 / 18,00 / 2,99 | 0,172 / 17,82 / 3,01 | -0,012 / +0,18 / -0,03 |
| Spalten: volle / max. Hoehe / >= 3 / >= 4 | 1,008 / 5,69 / 3,19 / 2,24 | 0,973 / 5,68 / 3,11 / 2,28 | +0,035 / +0,01 / +0,09 / -0,04 |
| Strafleiste gesamt (Strafpunkte) | 8,16 | 8,47 | **-0,31** |
| Plattenpunkte gesamt / je Kriterium | 7,73; Eckplatten 8,72, Diagonale 0,40, Vertikale 6,61, Mehrfarbige 2,53, Spezialfelder -10,28 | 7,54; 8,04, 0,16, 6,85, 2,74, -10,35 | +0,19; **+0,68**, **+0,24**, -0,24, -0,21, +0,07 |
| Eigene Punkte | 54,18 | 52,60 | **+1,59** |
| Marge | +1,59 | -1,59 | +3,17 |

Lesart der Kennzahlen: der Gewinn des Zweigs liegt im Plazierungs-Pfad (+1,0 Tiling-Punkte), in weniger
Strafleiste (-0,3) und bei den Eckplatten (+0,7); "aus" baut geringfuegig mehr Punkte aus vertikalen Reihen
(+0,24), verliert aber unterm Strich 1,6 Punkte. Der Stichentscheid des Value-Kopfs waehlt unter punktgleichen
Plaenen also den, der die spaetere Wertung besser stellt -- genau die Aufgabe, fuer die er 2026-08 gebaut
wurde (Modulkommentar `tiling_solver.rs` ueber `NET_TILING_TIEBREAK_DEFAULT`).

**Folgen:** (1) Fahrplan 36f DURCH, Knopf bleibt Default 1, Spec-Dateien `tiebreak_on/off` bleiben als
Messbelege. (2) Der Sondenbefund 16.9c wird nicht zur Rezeptaenderung; die Sonde misst eine andere Grundmenge
als die Arena (Rueckwaerts-Pruefung: `PREREG_geometric_envelope.md` par.3f behaelt seine Stuetze, STATUS Punkt
17 wird geschlossen). (3) Kein neuer Arm: die verengte Variante (b) aus 16.10 waere nur dann ein Kandidat,
wenn "aus" unentschieden gewesen waere.

### 18.10 Training v29-b07 DURCH (2026-09-17, 14:52-16:45), Tor 1 laeuft

**Training:** 14:52:49 bis 16:45:26, **6.757 s = 113 min**, CUDA, GEBREMST (daneben 14:56-16:41 das
Stichentscheid-A/B mit 10 Threads und um 14:55 der Commit-Hook; b08 mit leichterer Nebenlast 74 min, b06
exklusiv 57 min). Bestes `val_brier` **0,1779 in Epoche 7** (letzte 0,1780; b03 0,17967, b08 0,1794, b04
0,17915 -- b07 ist der beste Wert der v29-Serie, der Abstand zu b03 von 0,0018 liegt aber innerhalb der
Aufloesung der Offline-Metrik, `project_offline_metric_resolution_limit`), Val-R2 Value 0,555 (b08 0,545),
Policy-Val 0,40, Endgame-Val-MSE 0,0147. Export `models/alphazero_v29-b07_brierbest.onnx`, **flat_input 884**,
79 Planes, 11.637.699 Byte.

**Manifest-Diff b07 gegen b03** (`cli_args`): `cache_file` 'data/.cache_790ac07353a6.h5' gegen None; `moon_target_source` 'label' gegen None; `name` 'v29-b07' gegen 'v29-b03'. `python_constants` ohne Unterschied; `engine_config`: `input_size` 884 gegen 794, `contract_hash` `cfd94509f0aab102` gegen `39994362fba145a6`, dazu die seit b03 neu ins Manifest aufgenommenen Knopf-Felder mit ihren Defaults (`net_tiling_tiebreak` 1, `round_transition_leaf` 0, `moon_order_*`, `return_order_random_p` 0,0; bei b03 noch nicht geschrieben). Rezept sonst identisch (b03 1:1,
einschliesslich Seed 20260941, Warmstart, Koepfe).

**Offen bis nach Tor 1 (keine CPU-Last waehrend der Messung):** Netz-Gesundheit der 90 neuen Spalten
(Spaltennormen `flat_branch.0.weight[:, 794:884]` gegen die 39 Sicht-Spalten `[:, 755:794]` und den Altbestand),
der Nachweis, dass Abschnitt 17 angekoppelt ist (18.5).

**Tor 1 b07 gegen b03 laeuft seit 16:45:47** (Seed 20261190, dann 20261191, je 200 Paare ohne Frueh-Stopp,
Champion-Spec beidseits, 10 Threads, exklusiv), Ende erwartet gegen 19:20 (2 x rund 77 min bei 11,5 s je Partie).

### 18.11 ENTSCHIEDEN VORAB (Nutzer 2026-09-17, waehrend Tor 1 laeuft): 884 geht in v30, und v30 startet KALT

Zwischenstand Tor 1 bei 75 Paaren 71:79 ("wird wohl ein tie"). Der Koordinator hatte fuer den Fall eines
Unentschiedens mit lebenden Spalten 794 empfohlen und als Gegenargument die ungedeckte Wette genannt, dass ein
Warmstart mit 12 Epochen neuen Eingaengen wenig Zeit gibt und ein Kaltstart in v30 mehr Chance haette. Nutzer
woertlich: *"dann gehen wir die wette fuer v30 und kaltstart ein."*

**Entscheid:** (1) `INPUT_SIZE` bleibt 884, Abschnitt 17 (Tiling-Projektion) geht ins v30-Rezept; (2) das
v30-Training startet KALT (kein `--load v28-b02_brierbest`), damit die 90 Projektions-Spalten (und die 39
Sicht-Spalten aus v29) von Anfang an gelernt werden statt als Null-Polster hinter einem eingespielten Netz.
Gilt fuer den Fall "Tor 1 flach"; schlaegt b07 den Sicht-Arm signifikant, gilt er ohnehin. Reisst b07 die
5-Prozentpunkte-Marge signifikant, wird der Entscheid dem Nutzer erneut vorgelegt.

**Was das kostet und was es riskiert (markiert, keine Messung):** Kaltstart 12 Epochen auf 4,7 Mio Zustaenden
hat 2026-09-02 8.164 s = 2,27 h gebraucht (`docs/measured_runtimes.md`, v23-b06), gegen 57-74 min Warmstart. Die
Kampagne hat einen negativen Kaltstart-Praezedenzfall (v14, Kaltstart-Destillation verlor den Value-Kopf,
`project_v14_rebuild`) und einen positiven (v23-b06 belegt die Linie, `project_prereg_audit_2026-09-01`). Das
Tor fuer v30 bleibt das Gating gegen den Champion; faellt der Kaltstart durch, ist der Rueckfall NICHT der Warmstart von
v28-b02, sondern **ein Afterburner auf dem kalt gestarteten v30-Netz** (Nutzer 2026-09-17: *"ansonsten halt
afterburner auf den kalt gestarten v30"*): Warmstart vom v30-Kaltstart-Checkpoint, kurze Nachschulung im
DAgger-Muster (Vorbild v22-b05/b06: 600 Zusatzpartien, 6-12 Epochen, 8-11 min, `docs/measured_runtimes.md`
Z.52-53) oder weitere Epochen auf dem v30-Fenster; die 884 Eingaenge bleiben in jedem Fall. Die Wette waere
dann nur um die Trainingszeit verloren, nicht um das Rezept. **Rueckfall 2 (Nutzer 2026-09-17, "ja trag es als
rueckfall 2 ein"):** hebt auch der Afterburner das Netz nicht ueber das Gating, dann Warmstart von
`v29-b09` (884, identisches Rezept, auf dem v29-Fenster eingespielt; `minimal_strength_core` 10.7) auf dem
v30-Fenster -- naechstbeste Quelle, deutlich naeher am v30-Netz als v28-b02 mit 755 Eingaengen. Voraussetzung:
b09 haelt sein Tor 1 gegen b03. **Folge fuer b09:** faehrt mit 884 auf dem liegenden Monolithen
`790ac07353a6`, als v29-Arm weiter mit Warmstart (Vergleichbarkeit zu b03/b07).

### 18.12 Tor 1 v29-b07 gegen b03 GEMESSEN (2026-09-17, 16:45-19:32): Variante C TRAEGT auf Block-Ebene

Aufbau 18.6/18.10: `alphazero_v29-b07_brierbest.onnx` (884) gegen `alphazero_v29-b03_brierbest.onnx` (794),
Champion-Spec beidseits, 400 Sims, zwei Seeds a 200 Paare ohne Frueh-Stopp (Schranken +-6,91 nie erreicht),
Blockgroesse 5, 10 Threads, `--log-games`, exklusiv auf dem 884-Wheel (b03 bekommt dort die ersten 794 Werte,
`net.rs:990`). Grundmenge Partien, Einheit Siege.

| Groesse | Seed 20261190 | Seed 20261191 | gepoolt |
| --- | --- | --- | --- |
| Siege b07 : b03 | 203 : 197 | 229 : 171 | **432 : 368 von 800 = 54,0 Prozent** |
| Vorzeichentest (Sweeps) | p 0,84 | p 0,0031 | Sweeps 109 / 77, **p 0,023** |
| Diff je Paar, KI95 | +0,030 [-0,161; +0,221] | +0,290 [+0,107; +0,473] | |
| eigene Punkte b07 / b03 | 52,72 / 52,66 | 54,87 / 52,82 | +1,06 |
| **Block-Ebene** (par.5 Entscheidungsmass) | | | 80 Bloecke a 10 Partien, Siegdiff **+0,80 je Block, SE 0,33, z = +2,40** |
| Laufzeit | 4.971,5 s (12,43 s je Partie) | 4.794,2 s (11,99 s je Partie) | |

**Verdikt:** auf Block-Ebene signifikant (z +2,40 > 1,96), gepoolt 54,0 Prozent, Marge haelt mit Abstand ->
**Variante C traegt; INPUT_SIZE 884 mit Abschnitt 17 ist damit gemessen, nicht nur gewettet (18.11).** Ehrlich
dazu: die beiden Seeds sind heterogen (ein Unentschieden, ein klarer Sieg); das ist die im Projekt bekannte
Seed-Streuung (5,75 Prozentpunkte bei n = 400), und das gepoolte Urteil traegt sie. Ein dritter Seed waere die
Replikation, die die Promotions-Checkliste ohnehin verlangt (Gating-Kante mit Replikationszeile) -- b07 ist
damit der staerkste Einzelarm und der Kandidat fuer die Champion-Kanten (STATUS Punkt 18).

**Netz-Gesundheit der 90 neuen Spalten (par.6d-Pruefung, `flat_branch.0.weight` des Checkpoints):**
Spaltennorm der Projektion **mittel 0,668, min 0,290, max 1,035, keine Spalte bei 0** -- gegen die 39
Sicht-Spalten desselben Netzes 0,284 (21 von 39 bei 0) und bei b03 0,137 (22 von 39 bei 0); Altbestand 3,02
(beide). Je Block: Zellen Spieler am Zug 0,669, Slots 0,591, Gegner 0,698 / 0,617. **Das Netz hat die
Projektion in 12 Warmstart-Epochen staerker angekoppelt als jede fruehere Encoder-Erweiterung**; der
Nullbefund-Vorbehalt aus 18.3 greift nicht.

**Sechs Standard-Kennzahlen** (Mittel je Seite ueber beide Seeds; `arena_columns_tor1_v29-b07_vs_b03_s*.json`,
794 von 800 nachgespielt; `plate_points_tor1_b07_s*.json`):

| Kennzahl | b07 | b03 | Diff |
| --- | --- | --- | --- |
| Reihen: volle Zeilen / lange Reihen vollendet | 0,175 / 3,03 | 0,128 / 3,07 | **+0,047** / -0,05 |
| Spalten: volle / max. Hoehe / >= 3 / >= 4 | **0,982** / 5,66 / 3,16 / 2,22 | 0,929 / 5,63 / 3,19 / 2,24 | **+0,053** / +0,03 / -0,02 / -0,02 |
| Strafleiste gesamt (Strafpunkte) | 8,18 | 8,55 | **-0,37** |
| Plattenpunkte gesamt / je Kriterium | 7,87; Vertikale 7,17, Horizontale 0,68, Mehrfarbige 2,70, Aeussere 10,56, Spezialfelder -10,63 | 7,65; 6,70, 0,43, 3,09, 10,38, -10,61 | +0,22; **+0,47**, **+0,25**, -0,38, +0,18, -0,03 |
| Spezialfelder belegt je Partie / Kuppelbonus | 1,30 / 5,39 | 1,23 / 5,15 | +0,07 / +0,24 |
| Eigene Punkte / Marge | 53,80 / +1,06 | 52,74 / -1,06 | +1,06 / +2,11 |

Lesart: die beiden vorab benannten Nutzniesser bewegen sich in der erwarteten Richtung -- **volle Spalten +0,05
je Partie** (Vollendung, der Engpass aus `project_column_completion_structural_weakness`) und belegte
Spezialfelder +0,07, dazu vertikale Reihen +0,47 Punkte, weniger Strafleiste (-0,37) und mehr Kuppelbonus. Das
ist das Bild eines Netzes, das das Tiling vor dem Ziehen kennt: es zieht so, dass die Runde mehr vollendet und
weniger ueberlaeuft. Gegenposten: Mehrfarbige Felder -0,38.

**Folgen:** Fahrplan 36c DURCH; 18.11 (884 + Kaltstart) bleibt und ist jetzt gedeckt; b07 ist Kandidat 1 fuer
die Champion-Kanten; die Encoder-Kosten sind erneut belegt (12,0-12,4 s je Partie gegen 11,5 auf dem 794-Wheel,
+4 bis +8 Prozent, unter der Schwelle). Bestand `docs/measured_runtimes.md`.
