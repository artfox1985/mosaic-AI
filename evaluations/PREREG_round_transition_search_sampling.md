<!-- STATUS: OFFEN | Frage: Bringt es SPIELSTAERKE, den Rundenuebergang in der Suche als Zufallsknoten zu bemustern (ROUND_TRANSITION_SAMPLING) statt ihn mit einem einzelnen Netz-Blattwert zu bewerten -- und ist der Preis (Durchsatz UND unschaerfere Paarung in gepaarten Arenen) das wert? | Beleg: NICHTS GEMESSEN, nichts gebaut. Der Schalter existiert seit 2026-07 und stand nie scharf. Die Sperre in seinem Doc-Kommentar ist ueberholt (Stand 2026-07-17, drei Wochen vor dem WDL-Kopf) UND ihre Bedingung ist erfuellt (v11-TD-Bootstrap hob R1/R2-R2, archive/history.md:7578) -- sie bindet also nicht. Zwei Kosten sind vorab benannt: 8 Netzauswertungen statt einer je pseudo-terminalem Blatt (vermutlich am net_batcher vorbei, ungeprueft) und ein Verlust an Trennschaerfe der GEPAARTEN Arena (KORRIGIERT gegenueber der ersten Fassung: die Wiederholbarkeit bleibt, weil PREREG_search_rng_split.md der Suche bereits einen aus dem Partie-Seed ABGELEITETEN Strom gibt; was leidet, sind gemeinsame Zufallszahlen und der Zustands-Determinismus, siehe par.4.2). Messkette in par.4: Kostentor ZUERST, Staerke danach. -->

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
