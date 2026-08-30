<!-- STATUS: OFFEN | Frage: Gibt es fuer den Spaltenbau ein OPTIMUM mittlerer Suchtiefe -- baut b05 bei 150 Sims mehr volle Spalten als bei 400, und kostet das Spielstaerke? | Beleg: ANLASS 2026-08-30, ein Punktpaar aus VERSCHIEDENEN Modi (value-only@150 0,4425 gegen self-play@400 0,3375) plus der Sims-1-Kollaps (0,0075, par.3b.8 Stufe C). Nichts entschieden; Stufe 1 schliesst die Modus-Luecke, die Arena entscheidet Gewinn gegen Tausch. -->

# Vorregistrierung: Suchtiefe und Spaltenbau -- gibt es ein Optimum?

**Angelegt 2026-08-30** auf Nutzer-Auftrag ("wie schliessen wir den
Strang sauber ab"), VOR jeder Messung dieses Strangs.

## par.1 Der Anlass, ehrlich als Punktpaar benannt

Bei der Sims-Probe fuer den v22-b05-Schwarm fiel auf:

| Lauf | Modus | Sims | volle Spalten je Seite | Punkte |
| --- | --- | --- | --- | --- |
| simsprobe150 | value-only, argmax | 150 | **0,4425 +- 0,042** | 41,0 |
| otw22b05w00 | Self-Play, argmax | 400 | 0,3375 | 37,2 |
| par.3b.8 Stufe C | Self-Play, argmax | 1 | 0,0075 | 11,1 |

**Die beiden oberen Zeilen stammen aus VERSCHIEDENEN Modi** -- der
Vergleich traegt nicht. Er ist der Anlass, nicht der Befund. Die
Sims-1-Zeile zeigt aber, dass die Kurve nicht monoton fallend sein
kann: irgendwo zwischen 1 und 400 liegt ein Maximum.

**Warum das interessant ist (Hypothese, ungeprueft):** Phase 0 hat
gemessen, dass die POLICY das Spaltenwissen traegt (Prior-Ratio 1,23,
Draft-Erbe) und der VALUE-Kopf den Plattenlohn mit Steigung 0,0886
unterbietet. Mehr Suche heisst mehr Gewicht fuer den gedaempften
Bewerter gegen den spaltenkundigen Prior. Dann waere die Suchtiefe ein
Regler zwischen beiden -- und der heutige Betriebspunkt (400) laege auf
der falschen Seite des Maximums.

## par.2 Stufenplan mit vorab festgelegten Entscheidungsregeln

**Stufe 1 -- die fehlende Kontrollzelle (Pflicht, ~42 min).**
value-only, argmax, **400 Sims**, 200 Partien, Seed 20260902 (identisch
zur 150er-Probe), Stack-Draw EIN. Damit variiert NUR die Sims-Zahl.
*Regel:* liegt @400 im selben Modus auf oder ueber @150, ist der
Anlass-Effekt ein MODUS-Artefakt -- Strang GESCHLOSSEN, Eintrag in
STATUS, keine weitere Messung.

**Stufe 2 -- die Kurve (nur wenn Stufe 1 den Effekt bestaetigt, ~1 h).**
Dieselbe Anordnung mit 50 / 100 / 250 Sims, je 200 Partien, gleicher
Seed. Ergebnis ist eine Kurve mit lokalisiertem Maximum.
*Regel:* das Maximum wird BERICHTET, nicht sofort uebernommen -- die
Uebernahme entscheidet Stufe 3.

**Stufe 3 -- der Haertetest (Arena, entscheidet Gewinn gegen Tausch).**
Gepaarte Arena b05@Optimum gegen b05@400, `tools/paired_gating.py
--no-promote-winner` (block-size 5 = Default), Seed 20260920.
*Regeln:*
* kein signifikanter Staerkeverlust => **echter Gewinn**: weniger Suche
  ist billiger UND spaltenreicher; Konsequenz fuer Erzeugung und
  moeglicherweise fuer den Spielbetrieb (eigener Entscheid).
* signifikanter Verlust => **Tausch**, kein Gewinn: der Spaltenzuwachs
  ist mit Spielstaerke bezahlt. Dann gilt er nur dort, wo Spalten das
  Produkt sind (Korpus-Erzeugung fuer die Value-Klasse), NICHT im
  Spielbetrieb -- und das ist ausdruecklich zu trennen.

**Stufe 4 -- Mechanismus (Datenpassage, nur bei bestaetigtem Effekt).**
Auf denselben Korpora: Anteil der Wurzelentscheidungen, in denen die
Suche den Policy-Top-1 VERWIRFT, je Sims-Stufe; dazu das
Q/Prior-Verhaeltnis (`tools/gumbel_scale_calibration.py`, dessen
Schwellenregel aus PREREG_prior_blind_spot ohnehin je Champion faellig
ist). *Erwartung bei zutreffender Hypothese:* der Verwerfungsanteil
steigt mit den Sims, und die verworfenen Zuege sind ueberproportional
spaltenbauend.

## par.3 Was dieser Strang NICHT ist

* **Keine Wiederaufnahme der Q-Skalierungs-Familie** (geschlossen). Hier
  wird kein Regler zwischen Q und Prior gedreht, sondern die Sims-Zahl
  variiert -- ein Erzeugungs- und Betriebsparameter.
* **Kein Ersatz fuer Phase 3.** Faende sich ein Optimum, waere das eine
  Umgehung der Betrags-Daempfung, keine Heilung: der Value-Kopf bliebe
  falsch geeicht, man wuerde ihn nur weniger fragen.
* ~~Kein Kriterium fuer den laufenden v22-b05-Schwarm.~~ **BERICHTIGT
  im selben Zug (Nutzer-Entscheid 2026-08-30): die v22-Self-Plays sind
  AUSGESETZT, bis dieser Strang abgeschlossen ist.** Damit ist er kein
  Nebenstrang mehr, sondern der Taktgeber: die Erzeugung startet
  danach mit einem GEMESSENEN Betriebspunkt statt mit einem
  plausiblen. Faellt in Stufe 2/3 ein anderes Optimum als 150, faehrt
  der Schwarm dieses -- die Sims-Wahl ist bis zum Start offen.

## par.4 Erwartungswert, damit die Kosten eingeordnet sind

Stufe 1 kostet 42 Minuten und kann den Strang komplett schliessen --
das ist der billigste denkbare Ausgang. Der teure Ausgang (Stufen 2+3,
zusammen ~3 h) tritt nur ein, wenn der Effekt real ist; dann ist er
auch die Kosten wert, weil er einen Betriebsparameter betrifft, der
JEDEN kuenftigen Lauf und moeglicherweise die Spielstaerke selbst
beruehrt.
