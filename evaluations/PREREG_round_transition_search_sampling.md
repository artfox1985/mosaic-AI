<!-- STATUS: OFFEN | Frage: Soll die Suche am Rundenende das Tiling sehen (Loeser im Blatt) und die Fabrik-Neubefuellung als Zufallsknoten bemustern, zu vertretbarem Preis? | Beleg: Variante B ist GEBAUT (par.17): Knopf `MOSAIC_ROUND_TRANSITION_LEAF`, Default 0 bitidentisch, Spec-Feld optional, 9 Tests gruen -- aber NOCH NICHT im Wheel, und Sichttor (par.10), Kostentor 25 Prozent (par.5) und der gepaarte A/B (par.9) stehen aus. Stufe-0-Sonde gebaut (par.16), Volllauf offen. Review par.15 abgearbeitet: Top-K ist im R5-Pfad BEREITS gebaut (B1), K=1 nicht bitidentisch (B3, 14.5). -->

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
