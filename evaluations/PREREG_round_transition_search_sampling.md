<!-- STATUS: OFFEN | Frage: Soll die Suche am Rundenende das Tiling sehen (Loeser im Blatt) und die Fabrik-Neubefuellung als Zufallsknoten bemustern, zu vertretbarem Preis? | Beleg: Variante B ist fuer v29 eingetaktet, aber ungebaut (par.9/10). Top-K-Tiling ist nur als Folgestufe nach positivem B und Mehrdeutigkeits-Sonde registriert (par.14); kein Bau. -->

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
par.1 Konstante `net_mcts.rs:95`, Aufrufstelle `:2329`.

## Nachtrag 2026-09-11 (Audit-Querlesung)

Die Reihenfolge-Angabe in par.7 ("K3-P2, K4, B") ist ueberholt: K4
(`round_estimate_leaf_term`) ist am 2026-09-11 als Schritt 7 des v28-Programms
eingetaktet (`PREREG_v28_window.md` par.8) und damit keine Vorstufe dieses Arms
mehr. Variante B bleibt ungebaut und haengt weiter an der Informationsmengen-
Antwort aus `PREREG_dome_stack_information_sets.md` (par.8). Zeile-1-Kopf im
selben Zug nachgezogen.

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

- **Nichts gebaut** (Kopfzeile, par.9). Zu bauen ist der Such-Knopf `MOSAIC_ROUND_TRANSITION_LEAF`
  mit Default 0 = Bestand bitidentisch, kein RNG-Zug; Spec-Feld optional.
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
   mit Zeilendrift nach par.8: Konstante um `net_mcts.rs:95`, Aufrufstelle um `:2329`).
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
(`envelope_tiling_value_w`) ist bereits mit Nullbefund gemessen (`PREREG_geometric_envelope.md`
par.8.6). Hier ist der Rundenscore eine Kandidatenschranke; der Netzwert waehlt nur unter den
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
* **Korrektheit:** K=1 ist bitidentisch zu Variante B; jeder K-Kandidat ist legal,
  der vorregistrierten Tiling-Reihenfolge zuordenbar und erzeugt ueber den normalen Spielpfad
  denselben Nachzustand wie der Selector. Champion-Paritaet, Anker-Drift und
  Anker-Konservierung muessen gruen sein.
* **Kosten:** Ein eigenes Kostentor wird vor dem Bau aus Stufe 0 vorgeschlagen. Es misst
  Wanduhr je Partie und Anteil betroffener Blaetter gegen Variante B, nicht gegen den alten
  Pfad ohne Tiling-im-Blatt.
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

