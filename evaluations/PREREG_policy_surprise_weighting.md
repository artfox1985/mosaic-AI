<!-- STATUS: OFFEN | Frage: Bringt es etwas, Trainings-Stichproben nach der Ueberraschung des Policy-Ziels zu gewichten -- also nach KL(Prior gegen Ziel) -- statt jede Stichprobe gleich zu zaehlen? | Beleg: NICHTS GEBAUT. Der Arm ist **v23-b03**, vom Nutzer am 2026-08-31 im Zyklus-Zuschnitt bestaetigt (par.4a: b01 Warmstart, b02 Kaltstart, b03 dieser Arm); sein Entscheidungsmass braucht Such-Ziele, die es erst im v23-Fenster gibt. Zuschnitt: Loss-Gewichtung in train.py, kein Engine-Eingriff (par.3); Entscheidungsmass sind die Orakelmetriken (par.5). -->

# Vorregistrierung: Policy-Surprise-Weighting

**ENTWURF 2026-08-27 aus dem Recherche-Abgleich. Nutzer-Entscheid ueber den
Bau offen, nichts gebaut.** Diese Datei registriert die Idee, den Zuschnitt
und das Entscheidungsmass, damit beides vor und nicht nach einer Messung
feststeht.

## par.1 Die Idee

Trainings-Stichproben werden im Policy-Verlust nach der **Ueberraschung** ihres
Ziels gewichtet: wie weit weicht das Policy-Ziel vom Prior ab, den das Netz an
derselben Stellung selbst vorschlaegt? Formal die KL-Divergenz
`KL(Prior || Ziel)` je Stichprobe, als Gewicht in den Policy-Verlust.

Die Begruendung der Literatur ist Dateneffizienz: Stellungen, an denen das Netz
das Ziel ohnehin schon trifft, tragen wenig Gradient, kosten aber vollen
Kapazitaets- und Rechenanteil. Stellungen, an denen Prior und Ziel
auseinanderlaufen, sind die, an denen etwas zu lernen ist.

**Quellen, beide im Repo:**

* `RESEARCH_alphazero_improvements_2026-08-01.md`, Fund 7 -- "Samples mit
  ueberraschendem Policy-Target uebergewichten; temperierter Zusatz-Policy-Head;
  optimistischer Policy-Head (40-90 Elo bei KataGo)".
* `RESEARCH_plate_intent_external_2026-08-22.md`, F2.4 (weitere belegte
  Eingriffe an derselben Stelle) und F5, Punkt 5 ("Optimistic-Policy-Kopf plus
  Policy-Surprise-Weighting").

## par.2 Warum JETZT -- und warum die alte Abwertung nicht mehr bindet

Fund 7 traegt in der Recherche die Note **NIEDRIG-MITTEL**, und die Begruendung
steht woertlich dort: "Alles Policy-Hebel -- 2x2-Attribution zeigt: bei 400
Sims traegt der Value-Head die Staerke; Policy-Verbesserungen ohne
Value-Verbesserung enden im Arena-Gleichstand."

Die Abwertung ist korrekt fuer die Aera, aus der sie stammt
([[project_hybrid_head_attribution]]): dort waren die Policy-Ziele
NETZ-Besuchsverteilungen, das Netz lernte also seine eigene, leicht
verbesserte Meinung nach. Eine bessere Anpassung an das eigene Echo ist
plausibel staerkefrei.

**In v22 ist die Lage anders, und das ist der ganze Punkt dieser
Registrierung.** Die Policy-Ziele stammen aus dem hv2-Lehrer, und der
Split-Test in `PREREG_v22_window.md` par.4f hat gemessen, dass der
**Spaltenbau ueber das DRAFTING transportiert wird**: die Huelle allein im
Drafting bringt 0,756 volle Spalten gegen 0,044 der Kontrolle (Delta +0,713,
t=10,29), waehrend das Routing allein exakt nichts bringt (0,113 gegen 0,113).
Der Drafting-Kanal ist der Policy-Kopf. Die Policy ist in dieser Generation
also nicht ein Nebenkanal neben dem Value-Kopf, sondern **der Kanal, ueber den
die einzige neue Faehigkeit ueberhaupt ins Netz kommt**.

**Als Herleitung markiert, nicht gemessen:** genau deshalb sollten die
Lehrer-Vorzugszuege die ueberraschendsten Stichproben des Korpus sein -- ein
frisch initialisiertes Netz hat keinen Prior auf Spaltenbau. Ein Gewicht, das
KL(Prior gegen Ziel) folgt, wuerde die Kapazitaet dorthin lenken. Ob das
stimmt, ist Teil der Messung und nicht ihre Voraussetzung.

## par.3 Zuschnitt, absichtlich klein

* **Ort:** `train.py`, Policy-Verlust. Dort steht bereits eine
  Maskenrechnung im Ownership-Zweig (`own_loss = (own_bce * own_m).sum() /
  own_m.sum()`), die Bauform ist also im Haus.
* **KEIN Engine-Eingriff.** Der Prior wird im Training gerechnet, nicht in der
  Suche. Damit ist der Arm label-neutral, erzeugungs-neutral und ohne
  Paritaets-Gate an der Engine fahrbar.
* **Kein Neu-Erzeugen, kein Neu-Labeln.** Derselbe Korpus, dasselbe Fenster.
* **Cache:** die Gewichtung aendert den Verlust, nicht die Zieldaten -- der
  Fenster-Cache bleibt gueltig. (Zu pruefen beim Bau: ob die
  Gewichts-Berechnung Zusatzfelder braucht; braucht sie welche, gehoert eine
  Cache-Key-Komponente dazu, gleiche Auflage wie bei Arm K der Lehrer-Prereg.)

**Offen und ausdruecklich NICHT hier entschieden:** die Form des Gewichts
(linear in KL, gedeckelt, temperiert), die Normierung ueber den Batch, und ob
der optimistische Policy-Kopf aus derselben Quelle mitgenommen wird. Das sind
eigene Entscheide beim Bau.

## par.4 Frist

**Trainingsstart des v22-Kaltstarts.** Danach ist der Arm nicht verloren, aber
er wird zum **v22b**-Retrain auf demselben Korpus -- also ein zweiter
Trainingslauf statt einer Variante im ersten. Das ist kein Ausschlussgrund; es
ist der Preis, und er gehoert vor dem Entscheid genannt.

## par.4a BESTAETIGT 2026-08-31: der Arm ist v23-b03

Nutzer-Zuschnitt des v23-Zyklus (im selben Zug wie der Kaltstart-Arm,
`PREREG_capacity_sim_frontier.md` par.9): **b01 Warmstart aus den Self-Plays,
b02 Kaltstart, b03 Ueberraschungs-Gewichtung.** Damit ist die par.8-Empfehlung
angenommen und der Platz im Zyklus vergeben; par.4 ("Frist: Trainingsstart des
v22-Kaltstarts") ist erledigt -- der Arm ist nicht verfallen, er ist
verschoben und benannt.

Was das an Arbeit bedeutet: der Zuschnitt aus par.3 (Loss-Gewichtung in
train.py, kein Engine-Eingriff) ist weiterhin UNGEBAUT. Er kann gebaut
werden, waehrend b01/b02 rechnen -- der Bau ist reine Python-Arbeit am
Trainer, und das Entscheidungsmass (par.5) braucht ohnehin erst den
fertigen b01/b02-Vergleich als Bezug.

## par.5 Entscheidungsmass, VORAB festgelegt

**Primaer: die beiden validierten Orakelmetriken.**
`prior_mass_on_oracle_top3` und `kendall_tau` sagen die Arena in diesem Projekt
7/7 richtig voraus ([[project_oracle_metrics_validated]]) -- und sie sind, im
Unterschied zu `policy_top3`, gerade fuer die Policy-Seite validiert
(`policy_top3` zeigte 6/6 auf den VERLIERER).

**Bei Gleichstand: die Arena**, gepaart, Block-Ebene
([[feedback_arena_block_correlation]]).

**Ausdruecklich NICHT das Entscheidungsmass:** `val_combined` (bei
unterschiedlichen Epochenbudgets ungueltig,
[[feedback_preregister_decision_metric]]) und `policy_top3`.

**Waechter gegen die Selbstbestaetigung:** die Gewichts-Parameter duerfen NICHT
an der Metrik getunt werden, an der der Arm beurteilt wird. Wird die Form des
Gewichts variiert, ist das ein Sweep und braucht eine eigene Registrierung des
Auswahlkriteriums.

## par.6 Registriertes Risiko

Die Grundrate spricht nicht fuer den Arm: Policy-seitige Eingriffe haben in
diesem Projekt wiederholt die Offline-Masse bewegt und die Arena nicht
([[project_2d_encoder_phase2_result]]: Policy 6/6 besser, Staerke 416:384,
p=0,30). Wer den Arm faehrt, sollte das vorher wissen. Der Unterschied, auf den
diese Registrierung setzt, ist par.2 -- und wenn der Arm negativ ausfaellt,
ist DAS der Befund: dann traegt auch der Transportkanal-Zuschnitt die
Policy-Hebel nicht.

## par.8 Zeitpunkt (Nutzer-Frage 2026-08-28, Empfehlung des Koordinators, Entscheid offen)

Nutzer: *"die frage ist ob wir das schon bei v22 machen, oder erst bei echten
netz self plays."* Empfehlung: **NICHT im v22-Erstlauf** (v22-b01/b02). Die
Kampagne traegt bereits vier neue Faktoren gleichzeitig (Lehrerkorpus,
Traeger-Arm B, Ownership-Gewicht, neue Eingaben), und der w0-Kontrollarm
kontrolliert genau EINE Achse -- ein fuenfter Faktor waere unzuordenbar.
Stattdessen zwei benannte Zeitfenster:

1. **Als v22-bNN-Folgearm**, falls das Spalten-Tor (par.3b.2 der
   Lehrer-Prereg) zeigt, dass der Lehrer-Transfer SCHWACH ankommt -- genau
   dafuer ist dieser Hebel gebaut (seltene Bauzuege uebergewichten). Billig:
   gleicher Korpus, gleicher Cache, ein Loss-Knopf.
2. **Beim v23-Training** mit echten Netz-Self-Play-Zielen, wo die klassische
   Form (Suchverteilung gegen Prior) ohne Sonderfall gilt.

Im v22-Erstlauf ist der Knopf damit ausdruecklich AUS.
