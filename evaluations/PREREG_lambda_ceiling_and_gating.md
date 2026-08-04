# Vorregistrierung

## NACHTRAG 2026-08-04 (VOR den w-Partien): w-Leiter + Verschiebungs-Monitor

**Nutzer-Auftrag**: den Bereich zwischen w=0,1 (einziger gesunder Messpunkt,
gepoolt 330:270 = 55,7% ueber 3 Seed-Sets) und w=0,5 (v9b-Aera, kaputte
Koepfe, nicht uebertragbar) kartieren.

- **Arme**: w ∈ {0,2; 0,3} bei lambda_aggr=0 (reiner Eigen-Punkte-Blend --
  sauberster Test der Skalen-Kompensations-These), Modell A
  v19_2d_opp_best vs B v19_2d_best, je 75 Paare, --block-size 5,
  Basis-Seed 40260803 (identisch zu den ceil-Armen -> block-paarbar mit
  ceil_la00 als w=0,1-Referenz... KORREKTUR: ceil_la00 lief mit w=0,1;
  als w-Referenz dient DIESER Arm).
- **Regel (VORAB)**: bestes w = hoechste Block-Ebene-Winrate unter
  {0,1; 0,2; 0,3}, sofern nicht signifikant (gepaarter Block-t-Test,
  p<0,05) unter w=0,1. Einbruchs-Kante = kleinstes w, das signifikant
  UNTER w=0,1 liegt.
- **Champion-Gating (Teil 2) laeuft mit der besten gefundenen
  (w, lambda)-Kombination** statt fix mit w=0,1.
- **Verschiebungs-Monitor** (fuer die Zukunft, keine Messung jetzt):
  Blend-Balance := (w*Steigung_points)/((1-w)*Steigung_value) aus den
  R5-Kalibrierungs-Steigungen (heute ~0,44 bei w=0,1). Trigger-Regel:
  bei jeder Kopf-AEnderung (neuer Champion, #30-Korrektur aktiv, neues
  Rezept) Balance neu berechnen; verlaesst sie das Band [0,5x..2x] des
  beim Leiter-Optimum gemessenen Werts, laeuft eine Mini-Leiter (2 Arme
  um w' mit w'/(1-w') = w/(1-w) * Steigung_value_alt/Steigung_value_neu)
  statt blindem Weiterbetrieb. Arena bleibt Schiedsrichter, die
  Stauchung ist der Fruehindikator.: lambda_aggr-Kartierung nach oben (block-basierte Sicherheitsregel) + Champion-Kandidaten-Gating v19_2d_opp@w=0,1

**Angelegt 2026-08-04, VOR dem ersten Spiel dieser Messung.** Grundlage:
`evaluations/STATUS.md` Abschnitte "Task #28 DURCHGEFUEHRT", "Task #28
Power-Erweiterung: WIDERSPRUCH" und "AUFLOESUNG des Stichproben-
Widerspruchs: BLOCK-KORRELATION, nicht Wheel" (2026-08-04). Kernlehre der
Aufloesung: Paare innerhalb eines Arena-Blocks sind korreliert (ein
Block-Seed formt die Spiel-Population); Paar-Ebene-Statistik unterschaetzt
Standardfehler systematisch. Alle score-basierten Aussagen dieser Messung
laufen daher auf BLOCK-Ebene; win-basierte Fragen werden bevorzugt, mit
kleinen Bloecken (5 Paare) fuer moeglichst viele unabhaengige Bloecke bei
festem Gesamtumfang. Die Regeln unten werden nach Sichtung von
Zwischenergebnissen NICHT mehr geaendert.

## Teil 1 -- Kartierung nach oben: sicherstes lambda_aggr aus einer Leiter

**Ziel**: nicht "wo bricht die Guardrail", sondern "welches lambda_aggr
ist auf Win-Basis, block-ausgewertet, sicher" -- als Eingabe fuer das
Champion-Kandidaten-Gating in Teil 2.

- **3 Arme** `lambda_aggr ∈ {0; 3,0; 5,0}` bei festem **w=0,1**.
  Modell A ist in JEDEM Arm `models/alphazero_v19_2d_opp_best.onnx`
  (w wirkt nur auf A -- A traegt den opp-Kopf). Modell B ist in JEDEM
  Arm `models/alphazero_v19_2d_best.onnx` (w=0, kein opp-Kopf vorhanden,
  daher fuer B ohnehin wirkungslos).
- **Je Arm 75 Paare**, `--block-size 5` (= 15 Bloecke je Arm),
  **identischer Basis-Seed 40260803 fuer alle drei Arme** (Paare damit
  ueber Arme hinweg blockweise vergleichbar), **kein Fruehstopp**
  (`--sprt-alpha 1e-9 --sprt-beta 1e-9 --max-pairs 75`).
- **Auswertung NUR win-basiert auf Block-Ebene**: je Arm 15
  Block-Winraten (Anteil A-Paarsiege je 5er-Block; Split-Paare zaehlen
  als 0,5, analog zur ueblichen Paar-Auswertung, aus `per_pair_scores`
  via `block_seed` aggregiert).
- **Sicherheits-Regel (VORAB, bindend)**: ein lambda-Arm gilt als
  **SICHER**, wenn seine Block-Winraten-Differenzen zum lambda=0-Arm
  (gepaart je Block-Seed, gepaarter t-Test ueber die 15 Bloecke,
  zweiseitig, `paired_ttest_p` aus `tools/train_pcr_dose.py`) NICHT
  signifikant negativ sind. Formal: **UNSICHER** nur wenn (p<0,05) UND
  (mittlere Differenz<0) gleichzeitig gelten -- jeder andere Fall
  (p>=0,05, oder mittlere Differenz>=0) gilt als SICHER.
- **Ergebnis**: hoechstes sicheres lambda aus der Leiter {5; 3; 2}.
  lambda=2 gilt aus den bisherigen 225 Paaren (Erst-Sweep + Power-
  Erweiterung, siehe STATUS-Historie) bereits als etabliert-sicher und
  ist der **Fallback**, falls weder lambda=5 noch lambda=3 die
  Sicherheits-Regel erfuellen.

## Teil 2 -- Champion-Kandidaten-Gating

- `models/alphazero_v19_2d_opp_best.onnx` @ (w=0,1, lambda=hoechstes-
  sicheres-lambda aus Teil 1) **gegen** `models/alphazero_v19_2d_best.onnx`
  (w=0, unveraendert).
- **Standard-SPRT** (Defaults `h1=0,65`, `alpha=beta=0,05`),
  `--block-size 5`, `--max-pairs 200`, **`--no-promote-winner`**
  (Champion-Promotion ist Nutzer-Entscheid am Morgen -- die
  Laufzeit-Konfiguration w/lambda ist in `models/champion.txt` nicht
  abbildbar; das braucht eine bewusste Server-Konfigurations-
  Entscheidung, kein automatisches Umschreiben).
- **Zusaetzlich zum SPRT-Ergebnis ein BLOCK-Ebene-Bericht**:
  Block-Winraten (je Block Anteil A-Paarsiege), gepaarter Block-t-Test
  der Block-Winraten gegen 0,5 (`paired_ttest_p` auf den Differenzen
  `block_winrate - 0.5`).
- **Score-Aussagen NUR deskriptiv auf Block-Ebene** (z.B. mittlere
  Gegner-/Eigenpunkte je Block als Kontext) -- KEINE Paar-Ebene-p-Werte,
  keine Score-basierte Entscheidungsregel (die Champion-Entscheidung ist
  rein win-/SPRT-basiert, konsistent mit der Aufloesungs-Lehre, dass
  win-basierte Gatings milder von der Block-Korrelation betroffen sind).

## Ausfuehrung

Teil 1 zuerst, komplett (3 Arme, la00 zuerst als Referenz), dann
Block-Auswertung und lambda-Wahl. Teil 2 erst danach, mit dem gewaehlten
lambda. Bei einem Crash: Fehlerausgabe sichern, nachfolgende Schritte
NICHT blind fortsetzen -- der Koordinator entscheidet nach Sichtung des
Fehlers ueber Fortsetzung/Wiederholung.

## Artefakte

- `evaluations/lambda_ceiling_result.json` -- Teil 1: Block-Winraten je
  Arm, Differenzen zu la00, t/p je lambda-Arm, gewaehltes lambda.
- `evaluations/gating_opp_block_report.json` -- Teil 2: Block-Winraten,
  Block-t-Test gegen 0,5, deskriptive Block-Score-Kontextzahlen.
- `evaluations/paired_gating_result_ceil_la*_vs_v19_2d_best.json` --
  Rohergebnisse Teil 1 (ein File je Arm, vom Tool selbst geschrieben).
- `evaluations/paired_gating_result_v19_2d_opp_w01_la<lambda>_vs_v19_2d_best.json`
  -- Rohergebnis Teil 2 (vom Tool selbst geschrieben).
- elo_tracker-Eintrag fuer Teil 2 (Kommando-Muster vom Tool ausgegeben,
  Kommentar "Champion-Kandidaten-Gating v19_2d_opp@w=0.1/la<lambda>,
  block-size 5, keine Promotion").
