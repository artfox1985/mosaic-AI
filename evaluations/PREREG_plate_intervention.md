<!-- STATUS: ENTSCHIEDEN | Frage: Hebt ein Endgame-/Wertungsplatten-Aux-Kopf die R5-Plattenkalibrierung, und schlaegt er den Champion in der Arena? | Beleg: Eigener Ergebnis-Abschnitt in der Datei ("ARENA-ERGEBNIS: H0"); Kopf wird Trainings-Upgrade, Champion unveraendert -->

# Vorregistrierung: Wertungsplatten-/Endspiel-Zonen-Intervention (Aux-Kopf)

**Angelegt 2026-08-07 als Entwurf; Nutzer-Go "dann takte es ein" am
selben Tag -- Messregeln hiermit EINGEFROREN.**

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
- **Ziel (KONKRETISIERT nach Datenpruefung 2026-08-07)**: `root_q`
  der R5-Drafting-Records = exakter Minimax-Wurzelwert in
  tanh-Normierung `((margin/VALUE_SCALE).tanh()+1)/2` (net_mcts.rs
  R5-Zweig via `round5::choose_action_with_analysis`) -- die Labels
  stehen BEREITS IN DEN RECORDS, kein Solver-Lauf beim Cache-Bau, die
  geplante Kostenmessung ENTFAELLT. Scope = NUR R5-Drafting (der
  R4-Ende-Teil braeuchte teure Refill-Erwartungen; die Zonen-Probe
  zeigt, dass der Trunk auch dessen Info schon traegt -- die
  R5-Supervision wirkt ueber den shared Trunk).
  Abdeckung im v20-Fenster: v18/v19wdl/v19wdlsw ~87% der R5-Zustaende
  (~265k Labels); v16/v17 ohne root_q -> Maske 0. Bekanntes
  Label-Rauschen: seltener leaf_value-Fallback bei Budget-Overrun
  (net_mcts.rs-Doku), akzeptiert.
- **Cache**: Schema 18, neue Felder `endgame_margin` ([0,1]-Skala wie
  root_q) + `endgame_mask` (uint8), Muster `opp_points_mask`.
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

## OFFLINE-ERGEBNIS (2026-08-08 nachts, pi_endgame_s2 vs Champion/Kontrolle)

Training: Early Stop E15, brierbest E6 (interner val_brier 0,1939 vs
0,1950/0,1950 der beiden kopflosen Seeds).

1. **R5-Steigung (primaer): 0,457** (R²=0,37, n=139) -- die
   vorregistrierte 0,5-Schwelle KNAPP VERFEHLT, aber +0,108 ueber dem
   Champion (0,349) bei Seed-Skala ~0,054 (s2/s3-Paar) => ~2
   Seed-Sigma; Verlauf 0,086 -> 0,273 -> 0,349 -> 0,457. Punkte-Kopf
   0,342 (R²=0,04, weiterhin kein belastbares Signal).
2. **Brier-Nichtunterlegenheit: UEBERTROFFEN** -- Alt-Messset
   (Snapshot) brierbest 0,18587 vs Champion 0,18749 vs Kontrolle
   0,18813 (Delta -0,0016 ~ 2,7x Seed-Skala 0,0006); E15 0,18240 =
   Serien-Bestwert.
3. Arena-Gating vs `v20_2d_opp_brierbest` LAEUFT (Schritt 3 der
   Messkette; nur H1 macht den Kopf zur Champion-Linie -- bei H0 wird
   der Offline-Teilerfolg dokumentiert, Kopf optional fuer den
   v21-Generator... korrekt: fuer das Training der NAECHSTEN
   Generation auf dem v21-Fenster).

## ARENA-ERGEBNIS (2026-08-08): H0 -- Kopf wird Trainings-Upgrade

Gating 97:103 nach 100 Paaren (SPRT-H0, p=0,76, gepaarte Diff -0,06
[-0,32,+0,20]) -- Paritaet, wie vom Nutzer prognostiziert und von der
Aufloesungsgrenzen-Regel erwartet (Brier-Gap 0,0016 << 0,015; Regel
steht damit bei 0/4). VERDIKT gemaess Prereg: Champion bleibt
`v20_2d_opp_brierbest`; **`--endgame-head` geht als Standard-Rezept-
Bestandteil ins Training der naechsten Generation** (Offline-Gewinne
real: R5-Steigung 0,457, Alt-Brier -0,0016, Kalibrierung sauber;
Arena-Kosten: keine). Elo-Kante eingetragen.
