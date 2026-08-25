<!-- STATUS: OFFEN | Frage: Bringt eine RISIKOSENSITIVE Blatt-Utility Spielstaerke -- also die Verteilung des Ausgangs statt nur ihres Mittels in die Suche zu ziehen? | Beleg: NICHTS GEMESSEN. Ausgangspunkt war die Nutzer-Idee der Varianz-Penalisierung. Wichtige Korrektur aus der Vorpruefung: der Verteilungs-Kopf points_dist ist ABGESCHALTET (POINTS_DIST_BINS = 0, config.py:134) und der Champion traegt ihn nicht -- seine ONNX-Ausgaenge sind policy/value/moon/points/ownership/value_wdl_logits/opp_points/endgame_margin. Die volle Fassung braucht also ein neues Training. GEGENBEFUND, der eine billige Stufe erlaubt: value_wdl_logits WIRD exportiert, aber net_mcts.rs liest es nirgends -- die Suche kennt die Klassenverteilung des Ausgangs nicht, obwohl sie im Modell steht. Zweistufig: Stufe A ohne Training (P(Niederlage) aus den WDL-Logits), Stufe B mit Training (unteres Quantil von points_dist). Entscheidungsmass ist STAERKE, kein Offline-Mass. -->

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

**EIN Wert fuer LAMBDA, kein Sweep.** Das ist ein Regler am Blattwert, und
diese Bauform hat im Bestand zwei Negative -- allerdings von verschiedener
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
