# Vorregistrierung: Task #28 -- Score-/Denial-Utility (aggressiveres Spiel), Evaluation in der v19-Generation

**Angelegt 2026-08-03, VOR Implementierung und erster Messung.**
Nutzer-Auftrag: die KI soll aktiv Gegnerpunkte verhindern, solange es das
eigene Gewinnen nicht gefaehrdet -- und das noch in DIESER Generation
messbar. Design-Historie und Verdrahtungs-Befunde: STATUS.md Task #28
(2026-08-03). Die Regeln unten duerfen nach Sichtung von
Zwischenergebnissen nicht mehr geaendert werden.

## Minimal-invasiver Zuschnitt (diese Generation)

1. **Kein Eingriff in Bestandsheads/-ziele**: `points_head` behaelt
   ε=0,1-Ziel (die ε=0-Migration ist v20+-Zielbild, siehe STATUS).
2. **Additiver `opp_points_head`**: Ziel = reine GEGNER-Punkteprognose,
   konstruiert mit EXAKT derselben Blending-Struktur wie das
   points-Ziel (nortv-Variante, TD-Bootstrap-Blend), nur auf den
   opp-Groessen:
   `opp_target = TD_LAMBDA*opp_bootstrap + (1-TD_LAMBDA)*tanh(opp_total/VALUE_SCALE)`
   (bzw. ohne Blend, wo `bootstrap_value` fehlt -- identische Fallbacks
   wie beim points-Ziel). NUR mit dieser Struktur-Symmetrie gilt die
   algebraische Rueckgewinnung exakt:
   `own_pts = points_pred + 0,1 * opp_pred`.
   Loss: MSE, Gewicht = `POINTS_WEIGHT` (symmetrisch zum points-Kopf,
   kein neues Tuning). Cache-Feld additiv (Alt-Caches ohne Feld ->
   opp-Loss maskiert, Praezedenz root_q/ownership). KEINE Aenderung an
   `values`/`points_forecast`-Inhalten (kein Schema-Bruch).
3. **Ein Retraining**: `v19_2d_opp` = Warm-Start von `v19_2d_best`
   (Champion-Rezept lr 5e-5 cosine, nortv, Bestandsfenster), neuer Kopf
   frisch initialisiert. ONNX-Export mit zusaetzlichem Output.
4. **Engine (additiv, laufzeit-konfigurierbar)**: Blattwert-Utility
   `u = (1-w)*winprob + w*(own_pts - lambda_aggr*opp_pts)`
   mit `w`/`lambda_aggr` als Laufzeit-Parameter (Praezedenz
   GUMBEL_TOP_M/PCR-Parametrisierung), Defaults `w=0` -> byte-identisches
   Bestandsverhalten; Modelle OHNE opp-Kopf: Legacy-Pfad unveraendert
   (Additiv-Regel, alte ONNX bleiben spielbar). `own_pts` via
   Rueckgewinnungsformel oben.

## Messplan (VORAB festgelegt)

### Gate 1: Kopf-Qualitaet offline (billig, vor jeder Arena)

`opp_points_head`-R² auf dem frozen_eval_set (analog zur points-R²-
Berechnung) muss >0 sein und der `value_r2_rounds_1_4`/Orakel-Metriken-
Stand von `v19_2d_opp` darf nicht sichtbar unter `v19_2d_best` einbrechen
(Orakel-Differenz je Metrik > -0,01 -- der neue Aux-Loss soll den Trunk
nicht beschaedigen). Bruch -> STOPP, Diagnose, keine Arena.

### Gate 2: Staerke-Nichtunterlegenheit des neuen Netzes (w=0)

`paired_gating.py v19_2d_opp (w=0) vs v19_2d_best`, Standard-SPRT,
`--no-promote-winner`. Entscheid faellt NICHT auf "opp muss gewinnen",
sondern Nichtunterlegenheit: SPRT-H1 FUER v19_2d_best (also aktiver Beleg,
dass das neue Netz SCHLECHTER ist) -> STOPP. H0/Unentschieden/H1-fuer-opp
-> weiter (der Aux-Kopf soll nicht staerken, nur nicht schwaechen).

### Hauptmessung: lambda_aggr-Sweep zur Laufzeit (Nutzer-Design)

- **Arme**: `v19_2d_opp` mit festem **w=0,1** und
  `lambda_aggr ∈ {0; 0,5; 1,0; 2,0}` (4 Arme; der 0-Arm misst zugleich
  den reinen w-Effekt). w=0,1 ist bewusst KLEIN gewaehlt (v9b-Lehre:
  0,5/1,0 waren toedlich; das kleine Regime laesst winprob dominieren,
  solange die Partie offen ist).
- **Gegner in ALLEN Armen fix**: `v19_2d_best` (w=0) -- der
  gleichbleibende Gegner aus dem Nutzer-Vorschlag.
- **n=150 Partien je Arm, FESTES n ohne Fruehstopp** (Score-Metriken
  brauchen festes n; Praezedenz Heuristik-Anker-Matches), IDENTISCHE
  Seed-Liste ueber alle 4 Arme -> je Seed gepaarte Vergleiche zwischen
  den Armen.
- **Primaermetrik (Denial-Nachweis)**: Ø-GEGNERPUNKTE je Arm; gepaarter
  t-Test (je Seed) jedes lambda_aggr>0-Arms gegen den lambda_aggr=0-Arm.
  Aggression belegt, wenn mindestens ein Arm die Gegnerpunkte signifikant
  (p<0,05) senkt.
- **Guardrail ("solange es dem Gewinnen nicht im Weg ist")**: Win-Rate
  jedes Arms vs. den lambda_aggr=0-Arm, exakter Vorzeichentest auf den
  gepaarten Seed-Ausgaengen; signifikant SCHLECHTER (p<0,05) ->
  Guardrail gerissen, Arm disqualifiziert.
- **Empfehlungsregel**: bester Arm = groesste signifikante
  Gegnerpunkte-Senkung OHNE gerissenen Guardrail. Kein Arm signifikant ->
  "kein nutzbarer Denial-Effekt bei w=0,1" (eigener Befund; ein
  w-Sweep waere eine NEUE Vorregistrierung, kein stilles Nachfassen).
- Sekundaer berichtet: eigene Punkte, Bodenstrafe, Win-Rate vs. Champion
  absolut je Arm.

## Bekannte Einschraenkungen, bewusst akzeptiert

1. `v19_2d_opp` != Champion (anderes Netz durch Aux-Loss) -- der Sweep
   vergleicht Arme DESSELBEN Netzes, die Empfehlung gilt fuer dieses
   Netz; produktiver Einsatz (GUI-Regler) uebernimmt es nur nach Gate 2.
2. w=0,1 als einziger w-Messpunkt (Kostendeckelung); die
   Dosis-Wirkungs-Form in w bleibt unbekannt.
3. Die algebraische own-Rueckgewinnung erbt beide Kopf-Fehler; bekannte
   R5-Unterkalibrierung der Koepfe (Task #27) gilt unveraendert -- der
   Sweep misst VERHALTENS-Aenderung (Gegnerpunkte), nicht Kopf-Wahrheit.
4. Ergebnis gebunden an 400-Sims-Arena-Regime und v19-Generation.

## Ausfuehrungsplan

1. Python: opp-Kopf + Cache-Feld + Export (NACH Ende des laufenden
   v18only-Sweeps -- kein neural_net.py-Edit bei laufenden
   Trainings-Subprozessen), Rauchtest 2 Epochen.
2. Engine: Utility-Blend + Laufzeit-Parameter + Legacy-Pfad (NACH dem
   R4-Binding-Agenten, gemeinsamer Wheel-Build mit dem R4-Binding),
   cargo-Tests: Legacy-Modell byte-identisch bei w=0, Blend-Formel-Test.
3. Training `v19_2d_opp`, Gate 1, Gate 2.
4. Hauptmessung (4 x 150 Partien), Auswertung nach den Regeln oben,
   elo_tracker-Protokoll der Matches.
5. Bericht; Checkpoint-Aufraeumen erst nach Ergebnis-Diskussion.
