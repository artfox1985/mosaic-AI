<!-- STATUS: OFFEN | Frage: FLOOR_SHAPING_SCALE steht auf 50, geerbt von VALUE_SCALE, obwohl sein Zaehler nur ueber -10 bis 0 laeuft statt ueber 0 bis 100+. Der Term verlaesst damit nie den linearen Bereich der tanh -- ist die Konstante falsch kalibriert, und bringt eine Kalibrierung etwas? | Beleg: nichts gebaut, angelegt 2026-08-24 auf Nutzer-Entscheid ("50 ist einfach falsch"). Rechnung geprueft: max Argument 10/50 = 0,2, tanh weicht dort nur 1,3 Prozent von linear ab, maximaler Blattwert-Shift 0,059 auf der [0,1]-Skala. Daraus der tragende Strukturbefund: im linearen Bereich sind W und 1/SCALE DASSELBE Knopf, der bereits gefahrene W-Sweep 0,15/0,3/0,6 hat also effektiv SCALE 100/50/25 abgedeckt und war zweimal H0. NEU ist nur SCALE unter etwa 10, wo echte Saettigung beginnt -- und dort muss W mitgesenkt werden, also eine ZWEIDIMENSIONALE Kalibrierung. Praezedenzfall mahnt: dieselbe Diagnose an WERTUNG_SHAPING_SCALE wurde gebaut und gemessen, Ergebnis NICHT-ERFOLG (284:295, p=0,34) -->

# Vorregistrierung: Kalibrierung von `FLOOR_SHAPING_SCALE`

**Angelegt 2026-08-24, VOR jeder Messung.** Nutzer-Entscheid: *"nimm auf,
dass wir diesen shaping scale kalibrieren sollten. 50 ist einfach falsch."*

## par.1 Der Befund: der Nenner ist von einer anderen Groesse geerbt

`FLOOR_SHAPING_SCALE = 50.0` (`net_mcts.rs:460`). Der Kommentar direkt
darueber nennt die einzige Begruendung:

> "gleiche **Groessenordnung wie `VALUE_SCALE`** in `neural_net.py` (dort
> 50.0) -- macht die Korrektur direkt vergleichbar mit dem
> own-minus-opp-Score-Margin, den `value`/`points_forecast` schon als
> Trainingsziel verwenden."

Die 50 ist also nicht kalibriert, sondern **uebernommen**. `VALUE_SCALE = 50`
selbst stammt aus einem menschlichen Referenzwert ("ab ~100 Punkten gilt ein
Ergebnis als sehr gut", `neural_net.py:502-509`) und ist bewusst NICHT aus
Spieldaten abgeleitet -- ein sinnvoller Wert **fuer einen Punktestand**.

**Der Zaehler des Floor-Terms ist aber keine Punktzahl.** `floor_penalties`
(`net_mcts.rs:966`) summiert `broken_penalty` plus
`projected_unplaceable_penalty`, und `BROKEN_PENALTIES = [-1,-2,-3,-4]`
(`board.rs:228`) ist bei `MAX_BROKEN = 4` gedeckelt -- der Wert kann nie
unter −10. Die Differenz `(mine − theirs)` liegt damit in [−10, +10].

Derselbe Nenner fuer eine Groesse mit **zehnfach kleinerer Spanne**.

## par.2 Was das numerisch bedeutet (gerechnet 2026-08-24)

Maximales `tanh`-Argument: `10/50 = 0,2`.

| `SCALE` | max. Argument | `tanh` | linear | Abweichung | max. Shift bei `W=0,3` |
|---|---|---|---|---|---|
| 100 | 0,100 | 0,0997 | 0,100 | 0,3 % | 0,030 |
| **50 (Bestand)** | **0,200** | **0,1974** | 0,200 | **1,3 %** | **0,059** |
| 25 | 0,400 | 0,3799 | 0,400 | 5,0 % | 0,114 |
| 10 | 1,000 | 0,7616 | 1,000 | 23,8 % | 0,229 |
| 5 | 2,000 | 0,9640 | 2,000 | 51,8 % | 0,289 |

**Erster Befund: die `tanh` ist im Bestand dekorativ.** Ueber den GESAMTEN
erreichbaren Bereich weicht sie um 1,3 % von der Geraden ab. Der Term ist
faktisch linear; die Saettigungsfunktion, die ihn nichtlinear machen soll,
tut nichts.

**Zweiter Befund, und er ist der tragende: im linearen Bereich sind `W` und
`1/SCALE` DASSELBE Knopf.** `W · tanh(d/S) ≈ W·d/S`. Damit gilt:

| Arm des gefahrenen W-Sweeps | entspricht effektiv |
|---|---|
| `W = 0,15`, `S = 50` | `W = 0,3`, `S = 100` |
| `W = 0,3`, `S = 50` | Bestand |
| `W = 0,6`, `S = 50` | `W = 0,3`, `S = 25` |

(Nachgerechnet: max. Shift 0,0296 / 0,0592 / 0,1184 gegen 0,0299 / 0,0592 /
0,1140 -- Abweichung < 4 %.)

**Der Sweep aus `PREREG_search_path_remeasurements.md` Messung 1 hat den
Nenner also bereits mitgemessen, ohne es zu wissen: effektiv `SCALE` 100,
50 und 25.** Beide Abweichungen vom Bestand waren H0 (p=0,31 / p=0,36).

**Konsequenz fuer diesen Zuschnitt: eine reine `SCALE`-Kalibrierung im
Bereich 25-100 kann nichts finden, was der W-Sweep nicht schon abgesucht
hat.** Neu ist ausschliesslich `SCALE` unterhalb von etwa 10, wo echte
Saettigung einsetzt (Abweichung von linear >= 24 %). Dort wird der Term
aber gleichzeitig sehr gross (Shift 0,23 bei `W=0,3`) -- **`W` muss
mitgesenkt werden. Es ist eine ZWEIDIMENSIONALE Kalibrierung, keine
eindimensionale.**

## par.3 Die Umdeutung, die daraus folgt

Der registrierte Strukturbefund "Floor-Shaping ist ein SCHALTER, kein
Regler" (aus dem W-Sweep) ist praeziser zu fassen:

- Was gemessen wurde: die **Verstaerkung** eines linearen Terms aendert
  nichts (Faktor 4 zwischen 0,15 und 0,6, beide H0).
- Was daraus folgt: der Nutzen der 11,25 pp (Task A, `W=0` gegen `W=0,3`,
  McNemar p=0,0001) kommt aus dem **VORZEICHEN** -- die Rangfolge fast
  gleichwertiger Zuege kippt --, nicht aus der Groesse des Shifts.
- Was NICHT gemessen wurde: ob eine andere **FORM** (echte Saettigung
  statt linearem Zipfel) etwas aendert.

Das ist die einzige offene Frage dieses Zuschnitts, und sie ist deutlich
enger als "die 50 ist falsch".

## par.4 Praezedenzfall, der zur Vorsicht mahnt

`PREREG_shaping_scale_per_round.md` ist **ENTSCHEIDEN** und stellte
dieselbe Diagnose an der Schwesterkonstante: `WERTUNG_SHAPING_SCALE = 50`
sei "rundenblind und frueh um mehr als eine Groessenordnung" falsch. Der
Fix wurde gebaut (Rundenprofil 4,2 / 8,6 / 16,3 / 25,8 / 41,3 statt flach
50) und gemessen.

**Ergebnis: NICHT-ERFOLG.** k1 −0,23 (Block-t −1,27), k2 +0,13 (t 1,58),
Siege 284:295 (p=0,34). Verdikt dort: "der rundenblinde Nenner ist als
Erklaerung ausgeschieden".

Wichtig: jenes Profil senkte den Nenner in fruehen Runden bis auf 4,2, ging
also sehr wohl in die Saettigung -- **genau die Richtung, die hier als
"neu" uebrig bleibt, ist an der Schwesterkonstante schon einmal ohne Effekt
geblieben.** Das widerlegt diesen Zuschnitt nicht (anderer Term, andere
Groesse, anderer Verbraucher), aber es ist der ehrliche Prior.

## par.5 Arme, falls freigegeben

Der Bestandswert bleibt in jedem Fall Default, bis eine Messung etwas
anderes belegt (der Term traegt 11,25 pp, siehe par.3).

| Arm | `SCALE` | `W` | max. Shift | Zweck |
|---|---|---|---|---|
| **R** | 50 | 0,3 | 0,059 | Bestand |
| **S1** | 10 | 0,08 | 0,061 | echte Saettigung bei GLEICHEM max. Shift -- isoliert die FORM |
| **S2** | 5 | 0,06 | 0,058 | starke Saettigung, gleicher max. Shift |

**`S1`/`S2` sind so gewaehlt, dass der maximale Shift dem Bestand
entspricht.** Nur so misst der Arm die Form und nicht die Verstaerkung --
sonst wiederholt er den W-Sweep unter anderem Namen, und das ist der Fehler,
den par.2 gerade aufgedeckt hat.

## par.6 Entscheidungsregeln, vorab festgelegt

- **Alle Arme H0:** die Form ist irrelevant, der Term wirkt allein ueber
  das Vorzeichen. Dann ist `SCALE = 50` zwar konzeptionell unsauber
  (dekorative `tanh`), aber **praktisch folgenlos** -- und der richtige
  Abschluss ist ein Code-Kommentar, der das festhaelt, keine Aenderung.
- **Ein Saettigungs-Arm signifikant besser (gepaart, netz-gegen-netz,
  Replikation mit frischem Seed-Satz):** die Form traegt. Dann ist die
  Konstante zu aendern, und zwar zusammen mit `W`.
- **Ein Saettigungs-Arm signifikant schlechter:** ebenfalls ein Befund --
  der lineare Zipfel ist dann nicht Zufall, sondern das, was funktioniert.

Kein SPRT-Fruehstopp. Auswertung auf Block-Ebene. Gegner netz-gegen-netz,
nicht Heuristik (Gegnerspezifitaets-Lehre 2026-08-23/24).

## par.7 Waechter

1. **`W` und `SCALE` nie einzeln variieren.** Sie sind im Bestandsbereich
   degeneriert (par.2); ein Arm, der nur einen von beiden dreht, misst
   Verstaerkung statt Form.
2. **Der Elo-Anker bleibt unberuehrt.** `FLOOR_SHAPING_SCALE` sitzt im
   Netz-Suchpfad; die Heuristik-Blattbewertung (`mcts.rs`) und
   `wertung_progress` werden nicht angefasst.
3. **Default bleibt 50/0,3**, bis eine Replikation etwas anderes traegt.
4. Wheel-Neubau vor jeder Messung, Arena exklusiv.

## par.8 Aufwand und Prioritaet

Der Knopf `MOSAIC_FLOOR_SHAPING_W` existiert; `SCALE` ist bisher eine
`const` ohne Env-Override, muesste also erst als solcher gebaut werden
(kleiner Eingriff, `#30`-Muster, `SearchConfig`-Kandidat wie in
`PREREG_agent_encapsulation.md`).

**Ehrliche Einordnung der Prioritaet: niedrig.** par.2 zeigt, dass der
plausible Bereich bereits abgesucht ist, und par.4 zeigt, dass die
verbleibende Richtung an der Schwesterkonstante schon einmal folgenlos
blieb. Der Zuschnitt ist registriert, weil die Konstante nachweislich
unsauber begruendet ist und das festgehalten gehoert -- nicht, weil eine
Staerkewirkung erwartet wird.

## par.9 Verhaeltnis zu den Nachbar-Zuschnitten

- **`PREREG_search_path_remeasurements.md`** (ENTSCHIEDEN): dessen
  Messung 1 hat den Nenner effektiv mitgemessen (par.2). Dieser Zuschnitt
  eroeffnet die Staerkefrage des GEWICHTS nicht wieder.
- **`PREREG_shaping_scale_per_round.md`** (ENTSCHIEDEN): derselbe Verdacht
  an der Schwesterkonstante, gebaut und gemessen, Nicht-Erfolg (par.4).
- **`PREREG_floor_action_aversion.md`** (ENTSCHIEDEN): erklaert, warum der
  Term die Aktions-Ebenen-Asymmetrie nicht korrigiert -- er sitzt hinter
  dem Nadeloehr der Wurzelauswahl. Das ist unabhaengig von seiner Skala.
- **`PREREG_long_row_payoff.md`** par.3/B1: erbt die Lehre aus par.2 --
  dort laeuft der Zaehler nur ueber 0-2, der Nenner darf also erst recht
  nicht ungeprueft von 50 uebernommen werden.
