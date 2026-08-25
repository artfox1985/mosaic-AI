<!-- STATUS: OFFEN | Frage: Bringt eine RISIKOSENSITIVE Blatt-Utility Spielstaerke -- also die Verteilung des Ausgangs statt nur ihres Mittels in die Suche zu ziehen? | Beleg: NICHTS GEMESSEN. Ausgangspunkt war die Nutzer-Idee der Varianz-Penalisierung. Wichtige Korrektur aus der Vorpruefung: der Verteilungs-Kopf points_dist ist ABGESCHALTET (POINTS_DIST_BINS = 0, config.py:134) und der Champion traegt ihn nicht -- seine ONNX-Ausgaenge sind policy/value/moon/points/ownership/value_wdl_logits/opp_points/endgame_margin. Die volle Fassung braucht also ein neues Training. GEGENBEFUND, der eine billige Stufe erlaubt: value_wdl_logits WIRD exportiert, aber net_mcts.rs liest es nirgends -- die Suche kennt die Klassenverteilung des Ausgangs nicht, obwohl sie im Modell steht. Zweistufig: Stufe A ohne Training (P(Niederlage) aus den WDL-Logits), Stufe B mit Training (unteres Quantil von points_dist). Entscheidungsmass ist STAERKE, kein Offline-Mass. EINGETAKTET fuer den v22-Zyklus 2026-08-25 (par.5) mit einer Bau-Entscheidung davor: Stufe A kann die KORPUS-LABELS aendern, weil der Bootstrap ueber net_leaf_eval laeuft (round_transition_deep.rs:594/698/731). Variante A1 (nur an der Gumbel-Blattstelle) laesst die Labels unberuehrt und ist die vorgeschlagene; A2 (in net_leaf_eval) bekaeme Wecker-Charakter wie der Bootstrap-Horizont und ist fuer v22 zu spaet -- die Erzeugung laeuft. Fuer v22 also A1 oder gar nicht. Zu fahren gemeinsam mit PREREG_implicit_minimax_backup.md par.3, beide sind Such-Knoepfe am selben Netz. -->

# PREREG: Risikosensitive Blatt-Utility

**Angelegt 2026-08-25 auf Nutzer-Anweisung.** Anlass ist die Nutzer-Idee, ein
Zug mit gleichem Erwartungswert, aber hohem Risiko solle einem sicheren Zug
NACHGEORDNET werden. Ohne eine Verteilung gibt es keinen Operator, an dem so
etwas haengen koennte -- deshalb geht es hier zuerst darum, ueberhaupt eine
Verteilung in die Suche zu bekommen.

## par.1 Ausgangslage, geprueft

Die such-treibende Utility mischt heute KataGo-artig den Punkte-Kopf mit der
Sieg-Wahrscheinlichkeit (`net_mcts.rs:86-94`). Beides sind PUNKTSCHAETZER --
ein Mittel und eine Wahrscheinlichkeit, keine Verteilung ueber Ausgaenge.

Zwei Befunde aus der Vorpruefung (2026-08-25):

1. **`points_dist` ist abgeschaltet.** `config.py:134`:
   `POINTS_DIST_BINS = 0`. Der Champion `alphazero_v21_2d_brierbest` traegt
   den Kopf nicht -- seine ONNX-Ausgaenge sind `policy`, `value`, `moon`,
   `points`, `ownership`, `value_wdl_logits`, `opp_points`, `endgame_margin`.
   **Eine Verteilung ueber Punkte gibt es heute also nicht zu lesen**, sie
   muesste erst trainiert werden.
2. **`value_wdl_logits` gibt es, und die Suche liest es nicht.** Der Ausgang
   ist im Champion vorhanden; in `net_mcts.rs` kommt der Name NICHT vor
   (`net.rs` fuehrt ihn nur in der Ausgangs-Index-Buchhaltung). Die Suche
   arbeitet mit dem skalaren `value`, obwohl die Klassenverteilung
   Sieg/Remis/Niederlage daneben liegt.

Daraus folgt die Zweiteilung: Stufe A braucht kein Training, Stufe B schon.

## par.2 Stufe A -- Risiko aus den WDL-Logits (KEIN Training noetig)

`value_wdl_logits` im Blattwert mitlesen und die Utility um einen expliziten
Risiko-Term ergaenzen:

```
utility = bisherige_utility - LAMBDA * P(Niederlage)
```

`P(Niederlage)` ist die dritte Klasse der Softmax ueber die Logits. Der Term
trennt zwei Stellungen, die heute denselben Blattwert bekommen: eine mit
70 Prozent Sieg / 30 Prozent Niederlage und eine mit 70 Prozent Sieg /
25 Prozent Remis / 5 Prozent Niederlage.

**EIN Wert fuer LAMBDA, kein Sweep.** Das ist ein Regler an der
NETZ-BLATTBEWERTUNG -- und HIER traegt der Praezedenzfall, weil er denselben
Eingriffspunkt betrifft (`PREREG_scoring_plate_injection.md` injiziert
woertlich in die Blattbewertung, `PREREG_long_row_payoff.md` B1 ist
`net_mcts.rs::long_row_init_shaping_w`, ein additiver Term ebendort). Fuer
Eingriffe an anderer Stelle -- etwa im Routing der Heuristik -- gilt er NICHT;
das ist am 2026-08-25 einmal falsch herangezogen worden
(`PREREG_heuristic_v2_long_rows.md` par.11.1).

Diese Bauform hat im Bestand zwei Negative -- allerdings von verschiedener
Art, und das gehoert genau gesagt: `PREREG_scoring_plate_injection.md` ist ein
ECHTER Dosis-Sweep (w = 0,03/0,1/0,3/1,0) und negativ entschieden;
`PREREG_long_row_payoff.md` B1 ist negativ, war aber ausdruecklich KEIN Sweep
("ein Wert genuegt zum Testen"). Es gibt also einen Praezedenzfall gegen die
Dosis-Antwort, nicht zwei. Der Wert ist trotzdem vor dem Lauf zu setzen und zu
begruenden -- ein Sweep waere hier die Wiederholung des einen Falles, den es
gibt.

**Vertraeglichkeit ist Pflicht, nicht Kuer:** Modelle ohne
`value_wdl_logits` muessen byte-identisch weiterlaufen. Vorbild ist die
`opp_points`-Erkennung (`net.rs`: Kopf per Ausgangs-NAME erkennen, sonst
Bestandsverhalten). Der Paritaets-Hash `8c6684ff` muss halten.

## par.3 Stufe B -- Verteilung ueber Punkte (Training noetig)

`POINTS_DIST_BINS > 0` setzen, ein Modell damit trainieren, und in der Suche
statt des Mittels ein unteres Quantil verwenden.

**Erst NACH Stufe A**, und nur wenn Stufe A einen Effekt zeigt. Ein
Trainingslauf fuer eine Idee, deren billige Fassung nichts bewegt, ist die
teure Reihenfolge.

Vorab festzulegen, falls es dazu kommt: Zahl der Bins, das Quantil, und ob
die Verteilung eigene Punkte oder die Marge beschreibt.

## par.4 Messung

Gepaarte Arena, DASSELBE Netz gegen sich selbst, einmal mit und einmal ohne
Risiko-Term, beide Sitze, gleiche Seeds.

**Entscheidungsmass: Siegquote und Punktemarge auf BLOCK-Ebene.** Auf
Partie-Ebene sind die Paar-SEs massiv unterschaetzt (stehende Regel seit
2026-08-04).

**Falsifikator:** keine signifikante Staerkeverbesserung -> Stufe A negativ,
Stufe B entfaellt ersatzlos.

**Waechter:** der Risiko-Term darf die Suche nicht passiv machen. Mitgemessen
wird die Strafleistenauslastung und das absolute Punkteniveau -- ein Agent,
der Niederlagen vermeidet, indem er nichts mehr riskiert, faellt im Niveau,
und das waere an denselben Kennzahlen sichtbar wie bei den Punktekarten aus
`PREREG_heuristic_v2_long_rows.md` par.9 (dort: weniger Strafpunkte, weniger
Struktur).

**Mitzuschreiben** (Standard-Kennzahlen je Seite und als Differenz):
Reihenauslastung, Spaltenauslastung, Strafleistenauslastung, Punkte je
Wertungsplatte, eigene Punkte, Marge.

## par.5 Was diese Prereg NICHT ist

- **Kein zweiter Blattwert-Knopf im alten Sinn.** Die negativen
  Praezedenzfaelle drehten an einem BESTEHENDEN Term (einmal als Dosis-Sweep,
  einmal als Einzelwert -- siehe par.2). Hier kommt eine Groesse HINZU, die
  die Suche bisher gar nicht sieht: die Klassenverteilung. Ob das den
  Unterschied macht, entscheidet die Messung und nicht dieses Argument.
- **Keine Aenderung am Trainingsziel in Stufe A.** Der WDL-Kopf bleibt, wie
  er ist; nur der Konsument aendert sich.
- **Keine Aussage ueber die Heuristik.** `heuristic_v2` und der
  Plattenbau-Layer bleiben unberuehrt.


## par.5 STUFE A EINGETAKTET fuer den v22-Zyklus (Nutzer 2026-08-25)

**Der Befund, der den Zuschnitt bestimmt, und er ist am Code geprueft:
Stufe A kann die KORPUS-LABELS veraendern.** Die Bootstrap-Labels laufen ueber
`crate::net_mcts::net_leaf_eval` (round_transition_deep.rs:594, 698, 731). Wer
die Blatt-Utility dort risikosensitiv macht, aendert nicht nur die Suche,
sondern auch das aufgezeichnete Value-Ziel.

Daraus folgt eine Bau-Entscheidung, die VOR dem Bau fallen muss:

* **(A1) Nur in der Suche** -- die risikosensitive Utility wird an der
  Gumbel-Blattstelle angewandt, `net_leaf_eval` bleibt unveraendert. Labels
  unberuehrt, Bestandskorpora bleiben vergleichbar, der Knopf ist jederzeit
  ein- und ausschaltbar. **Das ist die vorgeschlagene Variante.**
* **(A2) In `net_leaf_eval`** -- wirkt zusaetzlich auf die Labels. Damit
  bekommt sie denselben Wecker-Charakter wie der Bootstrap-Horizont: nur am
  GENERIERUNGSSTART entscheidbar, spaeter nur durch Neu-Labeln aenderbar. Fuer
  v22 ist dieser Zug bereits vorbei -- die Erzeugung laeuft seit 17:20.

**Fuer v22 heisst das: A1, oder gar nicht.** Ein Wechsel auf A2 mitten im
laufenden Korpus wuerde eine Datei-Haelfte mit einer anderen Zieldefinition
erzeugen als die andere -- ein stiller Messfehler im Artefakt, genau die
Bauform, vor der die Exklusivitaets-Regel warnt.

**Warum die Stufe trotzdem billig ist:** `value_wdl_logits` WIRD vom Champion
exportiert, aber `net_mcts.rs` liest es nirgends. Die Information ist bereits
bezahlt und liegt ungenutzt im Modell; A1 ist eine Leseoperation plus eine
Utility-Mischung, kein Training.

**Entscheidungsmass bleibt wie im Kopf registriert: STAERKE, kein
Offline-Mass.** Gepaarte Arena, Block-Ebene. Das ist hier nicht
Formalitaet -- eine Blatt-Utility, die den Erwartungswert verlaesst, kann
Offline-Kalibrierung verbessern und die Zugwahl trotzdem verschlechtern.

**Reihenfolge im Zyklus:** nach dem v23-Training, gemeinsam mit dem
implicit-minimax-Arm (`PREREG_implicit_minimax_backup.md` par.3) -- beide sind
Such-Knoepfe am selben Netz und lassen sich auf denselben Seeds fahren.
