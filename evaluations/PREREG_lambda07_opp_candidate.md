# Vorregistrierung: λ=0,7 + opp-Kopf als Champion-Kandidat auf dem Bestandskorpus

**Angelegt 2026-08-04, VOR dem Trainingslauf.** Nutzer-Vorschlag: den
arena-belegten λ=0,7-Kandidaten (`PREREG_lambda_v18only.md`, 227:173,
p=0,0101) nicht bis zum v20-Self-Play warten lassen, sondern JETZT auf dem
vorhandenen 900-Datei-Fenster trainieren und gaten -- "gleich die
opp-Variante", also mit `--opp-points-head` (Nutzer-Entscheid: der
opp-Kopf soll ueber die naechste Champion-Generation in die Linie).
Regeln unten nach Sichtung von Zwischenergebnissen nicht mehr aenderbar.

## Design: exakte Ein-Faktor-Ablation gegen ein BEREITS EXISTIERENDES Kontrollnetz

`v19_2d_opp_best` wurde am 2026-08-03 mit genau diesem Rezept, Korpus,
Seed und Warm-Start trainiert -- nur mit `--value-target-lambda 1.0`
(Default). Der neue Lauf unterscheidet sich davon in GENAU EINEM
Parameter:

| | Kontrolle `v19_2d_opp` (existiert) | Kandidat `v19_2d_opp_l07` (neu) |
|---|---|---|
| `--load` | v19_2d_best | v19_2d_best |
| `--encoder` | 2d | 2d |
| `--opp-points-head` | an | an |
| `--seed` | 2 | 2 |
| `--epochs/--lr/--lr-schedule` | 100 / 5e-5 / cosine | identisch |
| `--value-target-variant` | nortv | nortv |
| Korpus | data/ (900: 100 v16 + 200 v17 + 600 v18) | identisch |
| **`--value-target-lambda`** | **1.0** | **0.7** |

## Bekannte Einschraenkung, VORAB benannt (wichtig fuer die Interpretation)

Das 900-Datei-Fenster hat **43,8% root_q-Sample-Anteil** -- exakt das
Regime, in dem λ=0,7 das Arena-Gating VERLOR (`PREREG_lambda_target.md`,
43:57, SPRT-H0). Gewonnen hat λ=0,7 im reinen v18-Korpus (65,67% Mix,
227:173). Wir testen hier also bewusst im UNGUENSTIGEREN Mix-Regime,
dafuer mit dem groesseren Korpus (Dosis-Effekt ist validiert,
[[project-corpus-dose-result]]). Zusaetzlich anders als beide
Vorexperimente: 2D-Warm-Start statt flach-from-scratch. Ein Nullergebnis
hier widerlegt λ=0,7 daher NICHT fuer das v20-Fenster (das einen
deutlich hoeheren Mix-Anteil haben wird, weil v16/v17 herausrotieren).

## Auswertung (VORAB festgelegt)

1. **Offline (deskriptiv, KEIN Gate)**: `val_combined`, die zwei
   Orakel-Metriken, `value_r2_rounds_1_4`, Opp-R² -- berichtet, aber
   NICHT entscheidungsrelevant (keine dieser Metriken ist fuer die
   Value-Seite arena-validiert; #29 hat auch die Rangmetrik verworfen).
2. **Entscheidend: Arena-Gating gegen den amtierenden Champion**
   `v19_2d_best`, `tools/paired_gating.py --sims 400 --block-size 5
   --max-pairs 200 --no-promote-winner`, Standard-SPRT.
   **AENDERUNG 2026-08-04, VOR der ersten Partie (Nutzer-Entscheid):
   laeuft MIT den produktiven Aggressions-Defaults `w=0,1`,
   `lambda_aggr=2,0`** statt mit w=0. Begruendung: Arenalaeufe werden
   kuenftig generell so gefahren -- gegatet wird also die Konfiguration,
   die auch ausgeliefert wird ("gate what you ship"), womit der frueher
   notierte Vorbehalt "Promotion einer ungetesteten Konfiguration"
   entfaellt. Sauber bleibt der Vergleich, weil die Engine den Blend PRO
   MODELL anwendet: `v19_2d_best` hat keinen opp-Kopf und faellt
   automatisch auf Bestandsverhalten zurueck -- das Gating vergleicht
   also "Kandidat wie er spielen wuerde" gegen "Champion wie er spielt".
   PREIS, bewusst akzeptiert: der reine λ-Effekt ist in diesem Lauf nicht
   isoliert (Punkt 3 liefert die Isolation nach, dort tragen BEIDE Seiten
   den opp-Kopf, der Blend wirkt also symmetrisch).
3. **Zusatz-Arena (nur bei positivem Gating)**: Kandidat vs.
   `v19_2d_opp_best` (die λ=1,0-Kontrolle) -- isoliert den REINEN
   λ-Effekt im 2D-Warm-Start-Regime, ohne Generationsunterschied.
4. **Promotion**: NICHT automatisch. Der Nutzer hat entschieden, dass der
   Champion bis zur naechsten Generation `v19_2d_best` bleibt -- ein
   positives Gating hier ist ein starkes Argument, diese Entscheidung zu
   revidieren, aber die Entscheidung bleibt beim Nutzer
   (`--no-promote-winner` erzwungen).
5. Block-Ebene-Zahlen werden zusaetzlich berichtet (Lehre
   [[feedback-arena-block-correlation]]).

## Kosten

Ein Warm-Start-Training (~15 Epochen bis Early Stop, Praezedenz
v19_2d_opp: ~35 min) + ein Gating (bis 200 Paare, ~60 min).
