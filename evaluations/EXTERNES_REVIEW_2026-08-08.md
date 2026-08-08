# Externes Architektur-Review (2026-08-08): Bewertung + abgeleitete Tasks

Nutzer hat eine externe RL-Einschaetzung eingeholt (4 Punkte). Unten je
Punkt: was faktisch zutrifft, was nicht, und was daraus als Task folgt.
Faktenbasis code-/messverifiziert, Belege in history.md.

## Punkt 1 -- "Distribution Shift durch den Alpha-Beta-Solver in Runde 5"

**Vorschlag**: die exakten Solver-Werte nicht nur als harten Cut-off
nutzen, sondern als Auxiliary Loss fuer die Runden 3/4, um den Uebergang
zu glaetten.

**Bewertung: sachlich richtig -- und BEREITS ZWEIFACH UMGESETZT.**
(a) Der Runde-4-Bootstrap nutzt seit der #21-Aera
`round5::exact_round5_outcome`, das Value-Ziel der letzten Netz-Runde
haengt also schon am exakten Endspiel.
(b) Genau der vorgeschlagene Aux-Loss existiert seit 2026-08-08 als
`endgame_margin`-Kopf (PREREG_platten_intervention.md): Ziel ist der
EXAKTE R5-Minimax-Wurzelwert (tanh-normierte Punktedifferenz, also
"genaue Punktedifferenzen statt nur Win/Loss" -- exakt die Empfehlung).
Ergebnis: R5-Plattensteigung 0,349 -> 0,457, Alt-Set-Brier -0,0016,
Arena H0 -> der Kopf ist seither Standard-Rezept-Bestandteil.
Die Overconfidence-Sorge ist ausserdem messbar und gemessen:
Platt-B 0,93 (leicht ueberkonfident, aber die kalibrierteste Generation
bisher; vorher 1,93 = gestaucht).

**Task**: keiner. Der einzige offene Rest -- Labels auch fuer
R4-ENDE-Zustaende -- ist bewusst nicht eingeplant: er braeuchte teure
Refill-Erwartungen (16 Welten je Zustand), und die Trunk-Probe zeigt,
dass die Information dort ohnehin schon linear vorliegt (LOO-R2=0,91).

## Punkt 2 -- "Statisches Floor-Shaping erzeugt lokale Optima"

**Vorschlag**: Gewicht 0,3 nicht statisch lassen, sondern gegen 0
annealen, damit am Ende das reine Gewinn/Verlust-Signal maximiert wird.

**Bewertung: der wertvollste Punkt des Reviews.** Der +14pp-Beleg fuer
das Feature stammt aus der v9/v10-Aera (tanh-Kopf, schwacher Value-Head,
150 Sims) -- nach der Aera-Grenzen-Regel ist er in der WDL-Aera KEIN
Argument mehr. Der WDL-Sweep 2026-08-07 hat 0,15 und 0,6 gegen 0,3
getestet (beide H0), **die im Prereg als "optional" markierte Kontrolle
W=0,0 wurde nie gefahren** -- die Frage "traegt die manuelle Heuristik
ueberhaupt noch?" ist damit offen. Das Annealing ueber die
Trainingsdauer laesst sich nicht direkt uebertragen (unser Shaping ist
ein Suchzeit-Additiv, kein Trainings-Reward), die Substanz aber schon.

**-> TASK A: Floor-Shaping W=0 vs 0,3 in der WDL-Aera** (2 Arme a 400,
MOSAIC_FLOOR_SHAPING_W, Instrument wie im Sweep). H0 -> das Feature
darf ersatzlos entfallen (weniger Handkalibrierung im Blattwert);
signifikant fuer 0,3 -> Feature bleibt, aber diesmal aera-korrekt belegt.

## Punkt 3 -- "Zwei-Stufen-Zerlegung verzerrt PUCT"

**Vorschlag**: statt MCTS-Baum-Hack eine faktorierte Policy oder
Action-Attention.

**Bewertung: Praemisse trifft unsere Suche nicht.** Wir fahren seit der
Gumbel-Umstellung an der Wurzel Gumbel-Top-m + Sequential Halving und
ab Tiefe 1 eine deterministische completed-Q-Regel -- PUCT ist im
Netzpfad ein toter Legacy-Zweig (`USE_GUMBEL_SEARCH=true`). Das
"mathematische Ideal der Upper Confidence Bounds" ist also nicht die
Referenz, gegen die wir verzerren. Der berechtigte Kern bleibt: die
Rotation ist an der Wurzel keine eigene Aktion, sondern erst auf Tiefe 1
-- die Wurzelbreite vergleicht nie vollstaendige (Slot, Rotation)-Paare.
Ob das etwas kostet, ist bisher UNGEMESSEN. Der Umbau auf eine
faktorierte Policy waere eine Architektur-Aenderung ohne gemessenes
Symptom -- also erst messen.

**-> TASK B: Zerlegungs-Diagnose (billig, keine Arena)**: auf
Frozen-Set-Zustaenden mit Kuppelplatten-Zug die von der zweistufigen
Suche gewaehlte (Slot, Rotation)-Kombination gegen eine FLACHE
Enumeration aller Kombinationen bei gleichem Gesamtbudget vergleichen
(Netzbewertung je Kombination). Metrik: Anteil der Zustaende, in denen
die Zerlegung eine schlechter bewertete Kombination waehlt, und die
mittlere Q-Differenz. Bleibt der Anteil klein (<5%) bzw. die Differenz
im Rauschen -> Punkt mit Beleg geschlossen. Sonst: faktorierte Policy
als begruendeter Kandidat.

## Punkt 4 -- "Gumbel-Hyperparameter (Samples, c_visit) untergetunt"

**Bewertung: teilweise berechtigt.** Die Sample-/Breiten-Seite ist
gemessen (m-Formel vs feste 16 bei 150 Sims: H0, p=0,54; 16-vs-8 bei
400 Sims: Wash). **`GUMBEL_C_VISIT = 50` ist dagegen bis heute
unverifiziert** -- unser eigenes Suchpfad-Inventar fuehrt es als "nur
indirekt via c_scale gedeckt". Das ist eine echte Luecke und der zweite
brauchbare Fund des Reviews.
Die Anregung, tau-Annealing im Gumbel-Kontext neu zu bewerten, greift
hingegen daneben: unser tau-Test war ein KORPUS-Test (Label-Qualitaet,
2.000 getauschte Sockel-Partien, H0), keine Suchparameter-Frage. Ohne
neuen Mechanismus wird er nicht wieder aufgemacht.

**-> TASK C: c_visit-Sweep** (Env-Knopf nach Standardmuster, 3 Arme
25/50/100 a 400 Spiele bei 600 Sims). Default-Wechsel nur mit
Signifikanz + Frisch-Seed-Replikation (Such-Default).

## Zusatz-Task aus der Nutzer-Frage (2026-08-08)

**-> TASK D: POINTS_WEIGHT-Re-Sweep in der WDL-Aera.** Der einzige
Gewichts-Sweep (v12d, 2026-07-23) lief im tanh-Regime, wurde nach
value_r2 beurteilt (Metrik seither vierfach widerlegt) und endete mit
H0 im Gating (pw05: 42:58). Zwei Dinge haben sich seither GEAENDERT:
(a) der Value-Loss ist BCE auf P(Sieg) statt MSE auf eine Marge,
(b) **POINTS_WEIGHT gewichtet inzwischen DREI Aux-Verluste** (Punkte,
Gegner-Punkte, endgame_margin -- train.py:1174-1177), der effektive
Aux-Druck auf den gemeinsamen Trunk hat sich also verdreifacht, ohne je
neu gemessen zu werden. Design: 3 Arme (0,25 / 0,5 / 1,0) auf dem
v21-Fenster, Entscheidungsmetrik **Brier** (arm-vergleichbar), danach
Gating nur fuer den besten Arm. VALUE_WEIGHT bleibt bei 0,2 (in der
WDL-Aera indirekt bestaetigt: 0,2 schlug 0,009 im #34-Vergleich).

## Einordnung fuer den naechsten Zyklus

Reihenfolge nach Ertrag/Kosten: **TASK A** (Floor W=0: billig, koennte
eine Handheuristik ersatzlos streichen), **TASK D** (Gewichte: ein
Trainings-Faktor, der sich verdreifacht hat), **TASK B** (Diagnose ohne
Arena), **TASK C** (letzter unverifizierter Gumbel-Parameter).
Alle vier hinter der bestehenden Nach-v21-Queue (E3b, ISMCTS-k).
