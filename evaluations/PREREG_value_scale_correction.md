<!-- STATUS: ENTSCHIEDEN | Frage: Hebt eine monotone Value-Skalen-Korrektur (Task #30, `MOSAIC_VALUE_CAL_A/B`) die Spielstaerke? | Beleg: Erstlauf +6pp n.s., Replikation zeigte KEINEN Effekt; `archive/history.md` Z. ~7461-7489 und ~9431-9457 -->

# Vorregistrierung: Task #30 -- monotone Value-Skalen-Korrektur, Arena-A/B

**Angelegt 2026-08-04, NACH dem Platt-Fit (der ist reine Kalibrierung auf
Offline-Daten), aber VOR jeder Arena-Partie dieses Experiments.** Regeln
unten nach Sichtung von Zwischenergebnissen nicht mehr aenderbar.

## Frage

Hebt eine MONOTONE Skalen-Korrektur des Value-Kopf-Outputs die
Spielstaerke? Motivation: Research-Report-Idee 7.3 -- Gumbels
`sigma(q_hat)` ist LINEAR in `q_hat`, die Policy-Improvement-Beweise
verlangen nur Monotonie, aber die praktische Wirkung haengt an der SKALA.
Ein gestauchter Value-Kopf liefert zu kleine Geschwister-Differenzen ->
die Suche zieht sich staerker zum Policy-Prior zurueck, als die wahren
Aktionswert-Unterschiede rechtfertigen.

Dies ist die REINE SKALA-Intervention (Ordnung bleibt per Konstruktion
unveraendert -- 500-Sample-Property-Test in `net_mcts.rs` beweist strikte
Ordnungserhaltung). Das Ordnungs-Gegenstueck (Task #29) ist NICHT
validiert worden (2/6) -- damit ist #30 der verbliebene Test der
Skala-vs-Ordnung-Frage.

## Kalibrierungs-Parameter (Fit ABGESCHLOSSEN, vor der Arena)

`evaluations/artifacts/value_calibration_fit.json`: IRLS-Logistik-Fit von
`P(Sieg) = sigmoid(A + B*logit(win_prob_Netz))` auf dem frozen_eval_set
(v19_2d_best, Torch-Pfad, nur Runden 1-4 -- in Runde 5 konsultiert die
Engine das Netz nie, dort greift die Korrektur konstruktionsbedingt
nicht; nur abgeschlossene Partien; Perspektive `rec["player"]`,
0 Mismatches gegen `state["current_player"]`).

- Fit-Split (n=720): **A=0,0036, B=1,998**
- Holdout (n=720): NLL 0,6574 -> **0,6490**, Brier 0,2328 -> **0,2301**
  (Korrektur verbessert out-of-sample, bescheiden aber konsistent)
- Voller Fit (n=1440), **fuer die Arena verwendet: A=0,00507, B=1,92689**

Einordnung: B~1,93 = globale Stauchung um Faktor ~2. Die
R5-Kalibrierungssteigung (0,06-0,09) haette B~11-16 impliziert -- die
extreme Daempfung ist also ein WERTUNGSPLATTEN-spezifisches Phaenomen,
nicht die globale Kalibrierungslage.

## Design (Praezedenz `paired_arena_shrink_ab.py`, Task #78)

`MOSAIC_VALUE_CAL_A/B` ist ein GLOBALER Engine-Parameter -- in einer
Netz-vs-Netz-Arena bekaemen BEIDE Seiten die Korrektur und der Effekt
hoebe sich weitgehend auf. Deshalb **Netz vs. HEURISTIK**
(`tools/paired_arena_arm_worker.py`, `net_arena_match`): die
Heuristik-MCTS nutzt den Netz-Value-Kopf ueberhaupt nicht und ist damit
ein von der Korrektur UNBEEINFLUSSTER Massstab.

- Netz: `v19_2d_best` @400 Sims; Heuristik @150 Sims (Kader-Standard,
  identisch zur bestehenden Elo-Verankerung).
- **Arm OFF**: `MOSAIC_VALUE_CAL_A=0.0`, `MOSAIC_VALUE_CAL_B=1.0`
  (Bestandsverhalten, byte-identisch per Early-Out).
- **Arm ON**: `A=0.00507`, `B=1.92689`.
- **200 Spiele je Arm** (400 gesamt), IDENTISCHER Seed 70260804 und
  identische Spielzahl in beiden Armen -> `net_arena_match`s
  deterministische Pro-Spiel-Seed-Ableitung erzeugt dieselbe
  Spielsequenz; ausgewertet wird GEPAART je Spielindex i.
- Jeder Arm ein eigener Prozess (Env-Var wird beim ersten Zugriff
  gecacht -- ein Prozess kann nicht beide Arme spielen).

## Auswertung (VORAB festgelegt)

- `b` = Netz gewinnt in ON, verliert in OFF (Beleg FUER die Korrektur);
  `c` = umgekehrt. Konkordante Paare tragen nicht bei.
- **Primaertest**: exakter zweiseitiger McNemar auf (b, c), alpha=0,05.
- **Entscheidungsregel**: NUR bei p<0,05 UND Vorteil fuer ON gilt die
  Korrektur als staerkebelegt und wird als Server-/Trainings-Standard
  vorgeschlagen. Sonst: kein Standardwechsel.
- Sekundaer deskriptiv: Siegquote je Arm, Ø-Score, Ø-Bodenstrafe.
- **Kein sequenzielles Nachziehen**, fixed-n (kein SPRT) -- reine
  Sensitivitaetsmessung wie beim Shrink-Praezedenzfall.

## Bekannte Einschraenkungen, bewusst akzeptiert

1. Gegner-Siegquote liegt bei ~75% fuer das Netz (v19_2d_best vs
   Heuristik@150: 113:37) -- lopsided, dadurch weniger diskordante Paare
   als bei einem 50%-Gegner. Bewusst akzeptiert, weil ein Netz-Gegner
   die Korrektur beidseitig bekaeme (siehe Design). Die gepaarte
   Struktur faengt den Grossteil der Varianz ab.
2. Die Korrektur ist auf `v19_2d_best` gefittet; sie auf andere Netze
   anzuwenden erfordert einen eigenen Fit (die Stauchung ist
   modellspezifisch).
3. Ein Nullergebnis widerlegt die Skalen-These nicht generell -- es
   widerlegt sie fuer diese Korrekturgroesse (B~1,93) in diesem
   Sim-Regime (400).

---
**STATUS (Stand 2026-08-08): ENTSCHIEDEN (Nullbefund nach Replikation)**
-- Erstlauf (2026-08-04): ON 74,0% vs OFF 68,0% Netz-Siege gegen die
Heuristik, +6pp, McNemar p=0,20 -- nach Vorab-Regel kein Staerkebeleg.
Bestaetigungslauf mit frischen Seeds (2026-08-05): OFF sprang auf 76,0%,
ON 77,0%, McNemar p=0,90 -- der Effekt repliziert NICHT. Endverdikt: kein
Effekt; der Laufzeit-Knopf (`MOSAIC_VALUE_CAL_A/B`) bleibt als inerter
Default (0/1) im Code. Belegstelle: archive/history.md, "Task #30
ERGEBNIS: Skalen-Korrektur +6pp, knapp nicht signifikant" (Zeile
~7461-7489) und "Task #30 ABGESCHLOSSEN: Skalen-Korrektur repliziert
NICHT" (Zeile ~9431-9457).
