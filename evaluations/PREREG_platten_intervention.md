# Vorregistrierung (ENTWURF): Wertungsplatten-/Endspiel-Zonen-Intervention

**Angelegt 2026-08-07 als ENTWURF** -- Trainings-Kostenklasse, finales
Go + Prioritaet liegt beim Nutzer. Messregeln werden vor dem ersten
Lauf eingefroren; bis dahin duerfen sich nur Design-Details aendern.

## Ausgangslage (zwei konvergierende Befunde, beide 2026-08-07)

1. **R5-Plattenkalibrierung**: Value-Kopf reagiert nur mit Steigung
   0,349 (Soll ~1) auf Wertungsplatten-Tausch -- Verlauf 0,086 -> 0,273
   -> 0,349 ueber die Kopf-Generationen; die Ziel-Reparatur (#34)
   verbesserte, loeste aber nicht. Wiedervorlage-Bedingung erfuellt.
2. **Zonen-Probe (r4b_zone_probe_v20.json)**: der fusion-Trunk traegt
   die exakte R4-End-Information LINEAR abgreifbar mit LOO-R²=0,91
   (Decke 0,97) -- die Koepfe realisieren -0,34/+0,03. Es ist ein
   ZIEL-Problem (Outcome+Bootstrap belohnen Endspiel-Exaktheit nie),
   kein Encoding-/Kapazitaets-Problem.

**Konsequenz**: Ein Platten-Encoding-Umbau (2D-Encoder-Erweiterung)
ist NICHT der erste Hebel -- die Information ist schon da. Der
direkteste Hebel ist ein **Aux-Kopf mit exakten, billig berechenbaren
Zonen-Zielen** (Destillation aus round5.rs), der den Trunk-Inhalt in
die Wert-Schaetzung zwingt.

## Intervention (ein Arm, ein Faktor)

Neuer Aux-Kopf `endgame_margin` (Skalar, MLP auf `shared`, Muster
`opp_points_head`/Task #28):
- **Ziel**: exakte Alpha-Beta-Marge (eigen-gegner, /VALUE_SCALE) aus
  `round5::exact_round5_outcome` -- Label NUR fuer Zustaende der Zone
  (Runde >= 4-Ende bis Runde 5), Maske 0 sonst (Muster
  `opp_points_mask`).
- **Label-Erzeugung**: beim Cache-Bau (Schema 18) fuer Zonen-Zustaende
  den exakten Solver rufen. Kostenabschaetzung VOR dem Go messen
  (Stichprobe 1.000 Zustaende); Fallback bei zu teuer: Labels nur fuer
  R5-Zustaende (dort ist der Solver ohnehin der Spielpfad).
- **Loss**: MSE, Gewicht analog points_forecast; ONNX-Ausgang HINTEN
  angehaengt (net.rs-Indizes stabil, 2D-additiv-Regel beachtet:
  bestehende Modelle bleiben ladbar).
- **Suche**: Kopf wird zunaechst NICHT im Blattwert verwendet (reines
  Trainingssignal) -- die Hypothese ist, dass der Gradientendruck den
  VALUE-Kopf mitzieht (shared-Trunk-Regularisierung), wie bei
  points_forecast/#28.

## Messkette (Instrumente existieren alle)

1. Offline: R5-Steigung (`tools/r5_value_calibration.py`) und R4b-N=72
   (`tools/r4_value_calibration.py`) VALUE-Kopf vor/nach -- primaere
   Zielmetrik: R5-Steigung des Value-Kopfs steigt deutlich (>0,5 als
   Erfolgsschwelle, vorregistriert).
2. Brier auf dem 90-Dateien-Altmessset (`tools/t36_curve_eval.py`) +
   internes Val (darf sich nicht verschlechtern: Nichtunterlegenheit).
3. Arena: Standard-Gating vs Champion (Fruehstopp-Regel). Nur bei
   H1 wird der Kopf Teil der Champion-Linie; bei H0 aber
   Offline-Erfolg -> dokumentieren, Kopf optional fuer v21-Generator.

Seed-Varianz-Regel beachten: das Training laeuft als EIN Arm warm vom
Champion-Rezept; wenn die Offline-Differenz klein ist (<~0,015
value_r2-Aequivalent), VOR dem Arena-Schritt paarige Seeds nachziehen.

## Kosten

Cache-Neubau Schema 18 (Solver-Labels: messen!), 1 Training (~3-4h
GPU), 1 Gating (~1-2h CPU). Kein neuer Self-Play-Korpus noetig.
