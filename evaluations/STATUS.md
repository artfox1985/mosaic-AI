# Mosaic-AI — Status & Fahrplan

**Hier steht nur AKTUELLES und OFFENES.** Alles Abgeschlossene (gelaufene
Experimente, Messergebnisse, verworfene Ideen, Zyklus-Berichte v9-v19,
Bugfix-Historie) wurde am 2026-08-05 nach **`../archive/history.md`**
ausgelagert -- STATUS war mit >8000 Zeilen nicht mehr benutzbar. Die noch
aeltere Stufe-1-Historie (`STAGE2_TODO_ARCHIVED.md`, war mit dem alten
`archive/`-Ordner geloescht worden) wurde aus der Git-Historie zurueckgeholt
und haengt dort als Anhang.

---

## TASK-INDEX (Stand 2026-08-05)

Spalte "haengt ab von" ist betriebswichtig: alles ohne Abhaengigkeit kann
SOFORT und PARALLEL laufen (Lehre 2026-08-05, ~8h durch unnoetige
Sequenzialisierung verloren).

| Nr | Titel | Status | haengt ab von | Details |
|---|---|---|---|---|
| **#34** | Sieg/Niederlage-Ziel + Kreuzentropie (WDL) wiederherstellen | **laeuft** (Implementierung) | — | unten |
| **#35** | Q je Wurzelkind loggen (Ranking-Loss-Vorlauf) | **laeuft** (Engine) | — (ZEITKRITISCH: vor v20-Self-Play) | unten |
| **#30** | Value-Skalen-Korrektur (Platt) | Bestaetigungslauf laeuft | Neubewertung nach #34 | history + unten |
| #33 | Value-/Policy-Loss-Gewicht | wartet | in #34 integriert (Loss-Skala springt ~22x) | unten |
| #35b | Ranking-Loss-Training | wartet | #35-Logging + v20-Self-Play | unten |
| #31 | Schwierigkeitsstufen leicht/mittel/schwer/extrem | **geparkt** (Nutzer) | Champion, der gute Spieler fordert | unten |
| **#36** | Saettigt der Value-Kopf ueber die Spielzahl? | geplant | #34 (braucht den Brier-Score) | unten |
| #32 | Self-Play-Kostenprofil | **erledigt** 2026-08-04 | — | history |
| — | v20-Zyklus (Self-Play + Gating) | geplant | #34-Ausgang, Fenster-Entscheid | unten |
| — | R4b (Playout-Ground-Truth) | geplant | — | history (#R4-Alarm) |
| — | GUI: Slider raus, Startwert setzen | offen, klein | — | history (Task #28) |
| #29 | Value-Rangmetrik | **geschlossen**: NICHT validiert (2/6) | — | history |
| #28 | Aggressions-Utility (opp-Kopf + Regler) | **geschlossen**: kein Denial-Beleg, Regler nutzbar | — | history |
| #14 | PCR (beide Regime) | **geschlossen**: negativ | — | history |
| #27 | R5-Value-Kalibrierung | **geschlossen**: Unterkalibrierung belegt | — | history |
| #9 | Ownership-Kopf | **geschlossen** 2026-07-28 | Wiedereroeffnung nur mit Arena-Instrument | history |
| #12 | Distributionaler Punkte-Kopf | **geschlossen**: nicht uebernommen | — | history |
| — | Afterstate-Kopf (Stochastic MuZero) | **geparkt**: Vortest ohne Signal | Neubewertung nach #34 | history |
| — | Wertungsplatten-Intervention | **geparkt**: Symptom, nicht Ursache | R5-Diagnostik nach #34 | history |
| — | rtv | **geschlossen**, Bedingung formuliert | arena-erfolgreiches #34 | unten |
| — | Static Folding (2D-Inferenz) | **erledigt ohne Bau**: ~5-7% Gewinn, lohnt nicht | — | history |

## OFFENE ENTSCHEIDUNGEN & GELTENDE REGELN

- **Champion**: `v19_2d_best` bleibt (Nutzer 2026-08-04). Der opp-Kopf
  kommt ueber `v20_2d_opp` in die Linie; v20 warm von
  `v19_2d_opp_best` starten (Kopf bereits trainiert).
- **λ (Value-Target-Mix)**: bis nach #34 ZURUECKGESTELLT -- #34 aendert
  `z` auf eine Gewinnwahrscheinlichkeit, damit mischt λ zwei Groessen
  derselben Art. Befundlage: gewinnt bei 65,7% root_q-Mix, verliert bei
  43,8% (zweimal, quer ueber Regime) -> **Korpus-Mischanteil entscheidet**.
  v20-Fenster entweder root_q-rein bauen oder λ neu messen.
- **Arena-Konvention**: Laeufe kuenftig mit `w=0,1` / `λ_aggr=2,0`
  (Nutzer 2026-08-04) -- gegatet wird, was ausgeliefert wird. Modelle
  ohne opp-Kopf fallen automatisch auf Bestandsverhalten zurueck.
- **Aggressions-Default**: (w=0,1, λ_aggr=2,0), beim Serverstart gesetzt;
  GUI-Slider wird entfernt. Wirksam erst mit einem Modell, das den
  opp-Kopf traegt.
- **Tiling-Cache**: Default AN seit 2026-08-05 (-20,1% Self-Play-Wandzeit,
  bitgleich); `MOSAIC_TILING_CACHE=0` schaltet ab.
- **Statistik-Regel**: Score-basierte Arena-Auswertungen IMMER auf
  Block-Ebene (Paar-SEs unterschaetzen massiv). Win-basierte SPRT sind
  milder betroffen, Block-Zahlen trotzdem mitberichten.
- **Kein validierter Offline-Praediktor fuer die Value-Seite** (#29
  gescheitert, value_r2 viermal widerlegt) -> jede Value-Aenderung
  braucht ein Arena-Gating. **Nach #34 neu zu pruefen** (siehe unten).

## NACH #34 NEU ZU BEWERTEN (Nutzer-Anmerkungen 2026-08-05)

#34 aendert die Semantik des Value-Kopfs von einer gestauchten
PUNKTE-MARGE auf eine GEWINNWAHRSCHEINLICHKEIT. Alles, was am alten Ziel
gemessen oder darauf eingestellt wurde, steht damit zur Nachpruefung --
NICHT automatisch wieder offen, aber mit konkretem Anlass:

1. **Arena-Konvention (w=0,1 / λ_aggr=2,0)**: der Blend ist
   `(1-w)*winprob + w*(own - λ*opp)`. Spreizt `winprob` nach der
   Reparatur staerker, verschiebt sich das Gewicht des Punkte-Terms von
   selbst. Instrument existiert: der vorregistrierte Blend-Balance-Monitor
   (`PREREG_lambda_ceiling_and_gating.md`, Nachtrag) mit Umrechnungsformel
   und Mini-Leiter statt voller Neukartierung.
2. **Offline-Praediktoren allgemein** (`value_r2`, Rangmetrik #29): alle
   vier Gegenbelege und die 2/6-Niederlage wurden am ALTEN Ziel gemessen.
   **Konkreter Verdacht zu #29**: die Rangmetrik verglich die Ordnung der
   Value-Blattwerte mit der **Orakel-Q**-Ordnung -- Orakel-Q ist eine
   Gewinnwahrscheinlichkeit aus einer 5000-Sims-Suche, der Value-Kopf sagte
   aber eine Punkte-Marge vorher. Das war ein Aepfel-Birnen-Vergleich; nach
   #34 sind beide Seiten Gewinnwahrscheinlichkeiten. Die 2/6 koennten also
   ein SEMANTIK-Problem gewesen sein, kein Metrik-Problem -- Wiederholung
   der Validierung ist billig (Werkzeug + Paar-Basis stehen).
3. **#9 Ownership-Kopf**: Effekt (+0,0017) am alten Ziel gemessen.
   Zusatzargument fuer eine Nachpruefung: ein BINAERES Hauptziel liefert
   weniger Gradientensignal als eine kontinuierliche Marge -- Hilfsziele
   koennten danach MEHR beitragen, nicht weniger (KataGo-Begruendung fuer
   zerlegbare Subereignisse). Schliessungsregel bleibt: Wiedereroeffnung
   nur mit ARENA-Instrument, nicht mit Offline-Metriken.
4. **#12 Distributionaler Punkte-Kopf**: bleibender Befund war "mehr
   Punkte in beiden Arena-Bloecken, ohne Siege daraus zu machen". Nach #34
   sind Value- und Punkte-Kopf erstmals WIRKLICH verschiedene Groessen
   (vorher sagten beide eine Punkte-Groesse vorher) -- und die Kombination
   *Gewinnwahrscheinlichkeit + Score-Verteilung* ist exakt die
   KataGo-Architektur (Report-Idee 1.1).

**Reihenfolge**: erst #34-Ergebnis + Pflicht-Diagnostiken abwarten, dann
diese vier Punkte in EINEM Zug bewerten -- nicht einzeln aufmachen.

## Task #36 (NEU, Nutzer 2026-08-05): Saettigt der Value-Kopf ueber die Spielzahl wie die Policy?

**Frage**: Wird der Value-Kopf mit mehr Self-Play-Partien immer besser,
oder saettigt er wie die Policy? Das geht DIREKT in die
Self-Play-Budgetierung (~20h je Kampagne).

**Warum das nie beantwortet wurde**: Die Korpus-Dosis-Studie
(2026-08-01) belegte "Menge hilft" mit **6/6 auf den Orakel-Metriken** --
das sind reine POLICY-Masse. Fuer die Value-Seite lag nur `value_r2` vor,
inzwischen viermal als arena-untauglich belegt. Die Value-Frage ist also
schlicht offen.

**Starkes theoretisches Vorargument (asymmetrische Stichprobengroesse)**:
Die Policy bekommt pro ENTSCHEIDUNG ein eigenes Ziel (~1,3 Mio im
900-Datei-Fenster). Der Value-Kopf bekommt pro PARTIE im Kern EIN BIT
(gewonnen/verloren), das sich alle ~145 Zustaende der Partie teilen --
effektiv ~9.000 unabhaengige Samples, ein Faktor ~145 weniger. Saettigung
der Policy bei 9.000 Partien sagt ueber den Value-Kopf daher NICHTS. Der
TD-Bootstrap-Blend mildert das etwas (er bringt zustandsabhaengige
Information ein), hebt die Asymmetrie aber nicht auf.

**Voraussetzung: NACH #34.** Vorher waere die Saettigungskurve die des
FALSCHEN Ziels (gestauchte Punkte-Marge), und es gaebe kein gueltiges
Mass -- der arm-uebergreifend vergleichbare **Brier-Score** entsteht erst
mit #34.

**Design-Skizze (PREREG bei Angehen)**: 3-4 Korpusgroessen (z.B. 225 /
450 / 900 Dateien, stratifiziert wie `train_corpus_dose.py`), gepaarte
Seeds, je Groesse: Brier (Value) UND Orakel-Metriken (Policy) messen ->
die beiden Saettigungskurven direkt uebereinanderlegen. Entscheidend ist
die FORM, nicht der Absolutwert.
**Kostenhinweis**: die Groessen brauchen je einen eigenen HDF5-Cache
(~50 min je Groesse), das ist der Hauptposten -- Sample-Ebene-Subsampling
geht NICHT, weil das Value-Ziel per PARTIE definiert ist, also muessen
Dateien/Partien subsampled werden.

**Konsequenz je Ausgang**: saettigt der Value-Kopf frueh -> Self-Play-Budget
kann sinken (oder in Qualitaet statt Menge fliessen). Waechst er weiter ->
mehr Partien sind der billigste Value-Hebel ueberhaupt, und die
Tiling-Cache-Ersparnis (-20%) laesst sich direkt in mehr Spiele umsetzen.

---
## Architektur, Stand jetzt (Konstanten am Code verifiziert 2026-08-05)

**Such-/Engine-Seite** (`engine/src/net_mcts.rs`, `engine_config_json()`):
- `ACTIVE_LEAF = LeafEval::Net` -- das Netz liefert den Blattwert; Stufe 1
  (DFS-Blatt, `mcts.rs`) liegt dormant im Code. Rueckfall ist AUSGESCHLOSSEN
  (Rundenweitsicht ist harte Anforderung).
- Gumbel-Suche aktiv, `GUMBEL_TOP_M = 16`, `GUMBEL_C_SCALE = 1,0`,
  `DEFAULT_C_PUCT = 1,5`, `floor_shaping_weight = 0,3`.
- `VALUE_SHRINK_ENABLED = false`; `round_transition_sampling = false`;
  `bootstrap_horizon_rounds = 2`.
- Runde 5 wird NICHT vom Netz gespielt: `round5.rs` uebernimmt ab
  `round_number>=5 && phase==Drafting` mit exaktem Alpha-Beta
  (`NODE_BUDGET=200`), Blattwert = exakter Endscore inkl. Wertungsplatten.
- Laufzeit-Knoepfe (alle Default = Bestandsverhalten):
  `MOSAIC_POINTS_UTILITY_W`/`MOSAIC_AGGR_LAMBDA` (Task #28, Default 0),
  `MOSAIC_VALUE_CAL_A`/`_B` (Task #30, Default 0/1),
  `MOSAIC_TILING_CACHE` (**Default AN** seit 2026-08-05),
  `MOSAIC_PROFILE_SELFPLAY` (Task #32, Default aus).

**Netz-/Trainingsseite** (`config.py`, `engine/py/neural_net.py`):
- `INPUT_SIZE = 708`, `NUM_ACTIONS = 406`.
- Champion-Encoder ist **2D** (`Mosaic2DNet`: Conv-Zweig auf
  `state_to_planes` + Flach-Zweig auf `state_to_tensor`); der flache
  `MosaicNet` bleibt Parallel-/Messarm.
- Koepfe: `policy`, `value`, `moon_order`, `points`, `ownership`
  (inert, Gewicht 0), seit Task #28 zusaetzlich `opp_points` (nur in
  Modellen, die damit trainiert wurden -- Engine erkennt ihn per
  Output-NAME und faellt sonst auf Bestandsverhalten zurueck).
- `VALUE_WEIGHT = 0,2`, `POINTS_WEIGHT = 0,5`, `VALUE_SCALE = 50`,
  `VALUE_OPP_EPSILON = 0,1`, `TD_LAMBDA = 0,5`.
- **Value-ZIEL (in Umstellung durch #34)**: Stand committed
  `VALUE_SCHEMA_VERSION = 15` -- `tanh((own-opp)/VALUE_SCALE)`, per
  `TD_LAMBDA` mit `bootstrap_value` gemischt, `nortv` (kein rtv-Override).
  Das ist eine gestauchte PUNKTE-MARGE, keine Gewinnwahrscheinlichkeit --
  genau das repariert #34 (Details unten).
- Champion: `models/champion.txt` -> `v19_2d_best`.

---

## Tasks #33-#35 (eingetaktet 2026-08-04): drei Value-Head-Hebel aus dem Research-Report

Gemeinsame Randbedingung: Es gibt KEINEN validierten Offline-Praediktor
fuer die Value-Seite (#29 gescheitert, value_r2 4x widerlegt) -- jeder
dieser Hebel braucht ein eigenes Arena-Gating (~1h). Offline-Kennzahlen
werden nur deskriptiv berichtet.

### Task #33: Value-/Policy-Loss-Gewicht-Sweep (Report 5.3) -- BILLIGSTER, zuerst
Leiden-Befund (CoG 2019): reines Value-Loss schlaegt die AlphaZero-Summe
in 3 von 4 Spielen; bei uns nie systematisch variiert
(`VALUE_WEIGHT=0.2`, `POINTS_WEIGHT=0.5`). **Kein Code noetig** --
`train.py` hat bereits `--value-weight`/`--points-weight`.
Arme: value_weight ∈ {0.2 (Kontrolle), 0.5, 1.0}, warm von
`v19_2d_best`, sonst Champion-Rezept.
**FALLE, vorab benannt**: `val_combined` ist die Checkpoint-Auswahl-
Metrik UND enthaelt `value_weight` als Faktor -- zwischen Armen hat sie
also eine ANDERE DEFINITION und ist als Vergleichsgroesse UNGUELTIG
([[feedback-preregister-decision-metric]]). Auswahl je Arm daher intern
per val_combined (Bestandslogik), Vergleich NUR per Arena.

### Task #34 (HOCHGESTUFT 2026-08-04): Sieg/Niederlage-Ziel wiederherstellen -- die Kopf-Trennung ist faktisch aufgehoben

**Nutzer-Einwand 2026-08-04**: "wir haben extra einen value head mit
sieg/niederlage und einen point head mit dem forecast der eigenen
punkte" -- code-geprueft und BESTAETIGT, mit einer Historie, die das
Problem groesser macht als gedacht:

1. **Vor Schema 13 war der Value-Kopf genau das.** Der v13-Kommentar
   (`neural_net.py:538ff`) sagt woertlich: *"points_forecast gewichtet
   own_total stark, values ist reines Sieg/Niederlage"*, gemessen
   `corr(val_true, pts_true)=0,49` -- zwei klar verschiedene Ziele.
2. **Die Umstellung war eine HYPOTHESE, kein A/B**: *"Hypothese: das
   HARTE ±1-Ziel ... treibt den gemeinsamen Trunk staerker Richtung
   Overfitting"*. Ein Test dazu ist nirgends dokumentiert.
3. **Die Diagnose stammt aus der v8e-Aera** -- der Generation mit
   Val-R²<0, in der der Value-Kopf die Suche nachweislich
   VERSCHLECHTERTE.
4. **Es war damals nur der FALLBACK** (*"rtv bleibt unveraendert
   bevorzugt, wo vorhanden"*). Als `nortv` am 2026-07-28 Standard wurde,
   ist dieser Fallback STILLSCHWEIGEND zum Hauptziel befoerdert worden --
   in dieser Rolle nie getestet.

**Konsequenz**: Der Value-Kopf trainiert heute auf
`tanh((own-opp)/SCALE)` -- eine gestauchte PUNKTE-MARGE, also dasselbe
Material wie der Punkte-Kopf. `(v+1)/2` ist damit keine
Gewinnwahrscheinlichkeit, sondern eine umetikettierte Punktedifferenz.
Das erklaert die gemessenen Pathologien zwanglos: Runde-5-Fehlanzeige
(Δ+18 Punkte -> 31-37% angezeigt), Kopf-Uneinigkeit r=0,68, und die
Platten-Blindheit (Steigung 0,06).

**Neuer Zuschnitt**: Hauptarm = hartes Sieg/Niederlage-Ziel
(Kreuzentropie statt MSE), womit die beabsichtigte Kopf-Trennung
wiederhergestellt ist; der WDL-/Klassifikations-Umbau (Report 1.2) ist
dann die technisch saubere Umsetzung davon, kein eigenstaendiges
Experiment. Der v13-Overfitting-Einwand wird dabei mitgetestet (er
koennte in der heutigen, gesunden Kopf-Generation schlicht nicht mehr
gelten) -- Kontrolle ist das aktuelle weiche Ziel, Entscheidung per
Arena. **Prioritaet: vor #33 und #35.**

**PFLICHT-DIAGNOSTIK zu #34 (Nutzer-Entscheid 2026-08-04)**: Nach dem
Training `tools/r5_value_calibration.py` auf dem neuen Netz wiederholen
(identische Parameter wie der Lauf vom 2026-08-03: 24 Zustaende x 6
Kombinationen, 3 Modelle -> hier nur das neue + das weiche Kontrollnetz).
Frage: steigt die Wertungsplatten-Kalibrierungssteigung von heute
**0,06-0,09** Richtung 1? Ausserdem den Platt-Fit
(`value_calibration_fit.json`-Verfahren) wiederholen: faellt B von
**1,93** Richtung 1?

**Damit ist die separat angedachte WERTUNGSPLATTEN-INTERVENTION
ZURUECKGESTELLT** (Symptom vs. Ursache): erst messen, ob die
Platten-Blindheit nach der Ziel-Reparatur ueberhaupt noch existiert.
Nur falls die Steigung flach BLEIBT, ist ein gezielter Eingriff
(Platten-Encoding / Aux-Kopf auf den Platten-Endbonus) gerechtfertigt --
dann aber als eigene Vorregistrierung mit dann bekanntem Ausgangswert.

### ZUSAMMENFUEHRUNG (Nutzer-Frage 2026-08-04): WDL ist NICHT hinfaellig, sondern die UMSETZUNG von #34

Zwei unabhaengige Achsen: (1) ZIEL -- weiche Punkte-Marge vs. hartes
Sieg/Niederlage; (2) KOPF/VERLUST -- Tanh-Regression + MSE vs.
Softmax-Klassifikation + Kreuzentropie.

Vor Schema 13 hatte das Projekt "hartes Ziel + MSE" -- und GENAU das
wurde wegen Overfitting verworfen. Wuerde #34 nur das Ziel zurueckdrehen
und MSE behalten, landen wir exakt in dem gescheiterten Setup.
**Kreuzentropie ist die Standardantwort auf diesen Fehlermodus**: bei
Tanh+MSE verschwinden die Gradienten an den Saettigungsraendern, bei
Klassifikation nicht. Lesart: die v13-DIAGNOSE war vermutlich richtig,
die THERAPIE (Ziel aufweichen) war die falsche der beiden Optionen.

**Bonus-Befund**: der aktuelle TD-Bootstrap-Blend ist semantisch
INKOHAERENT -- er addiert `tanh((own-opp)/SCALE)` (Punkte-Marge) und
`2*win_prob-1` (Gewinnwahrscheinlichkeit) auf derselben Zahlenachse. Mit
einem Wahrscheinlichkeits-Ziel liegen beide Komponenten auf DERSELBEN
Skala und der Blend wird sinnvoll. Kreuzentropie arbeitet auch mit
WEICHEN Labels (Standard bei Label-Smoothing/Distillation) -- der
varianzreduzierende Bootstrap-Anteil muss also nicht geopfert werden.

**#34 damit konkret**: Ziel = Gewinnwahrscheinlichkeit (harter Ausgang,
optional weiter mit dem Bootstrap-Win-Prob geblendet, gleiche Skala),
Verlust = Kreuzentropie, Kopf = 2 Logits statt Tanh-Skalar. Report-Idee
1.2 ist damit die Implementierung, kein eigenes Experiment.

**Falls #34 scheitert**: erst DANN als Diagnose-Arm "hartes Ziel + MSE"
nachziehen, um Ziel- und Verlust-Aenderung zu trennen -- nicht vorab
(spart ein Gating).

### KNOPF-INTERAKTIONEN bei #34 (Nutzer-Warnung 2026-08-04): #33 muss HINEIN, nicht danach

Nutzer: "kann auch ganz schlecht laufen mit unseren derzeitigen
eingestellten Knoepfen" -- beziffert und bestaetigt:

**Loss-Skalen-Sprung (das Hauptrisiko)**: Value-Loss heute (MSE auf
weichem Ziel) ~**0,029**, Policy-Loss ~1,90 (Trainingslogs). Kreuzentropie
auf binaerem Ausgang liegt bei ~**0,65-0,69** -- Faktor ~22. Mit
unveraendertem `VALUE_WEIGHT=0.2` stiege der Value-Anteil am Gesamtverlust
von ~0,3% auf ~6,4%: der Value-Kopf bekaeme **~22x mehr Gewicht im
gemeinsamen Trunk**, ohne dass das beschlossen waere. Das Experiment
teste dann nicht "hartes Ziel + CE", sondern "... + massiv umgewichtetes
Training" -- und ein Fehlschlag waere nicht zuordenbar. Ironie: genau das
ist der v13-Vorwurf (Value-Kopf drueckt den Trunk ins Overfitting), dann
aber von uns selbst verursacht.

**Konsequenz: Task #33 wandert IN #34 hinein** (nicht davor, nicht
danach): `VALUE_WEIGHT` wird mitvariierter Arm, mindestens
"loss-angepasst" (~0,009, haelt den Beitrag konstant) gegen
"unveraendert" (0,2). Anmerkung: Loss-Magnitude != Gradienten-Magnitude
(MSE auf tanh hat den verschwindenden Faktor (1-tanh²), CE auf Logits
den gutartigen (p-y)) -- die "richtige" Invariante ist NICHT offensichtlich,
weshalb sie empirisch aufgespannt statt errechnet wird.

**Weitere gepruefte Knoepfe**:
- `VALUE_SHRINK_ENABLED = false` (net_mcts.rs:361) -- GLUECK GEHABT: waere
  die rundenabhaengige Daempfung an, wuerde sie nach #34 korrekte Werte
  kuenstlich stauchen.
- `val_combined` enthaelt `value_weight * value_val` -> mit CE aendert die
  Checkpoint-AUSWAHL-Metrik ihre Bedeutung (Falle wie bei #33, schaerfer:
  hier aendert sich zusaetzlich die Einheit).
- `DEFAULT_C_PUCT=1.5` / `GUMBEL_C_SCALE=1.0` sind such-seitig fuer den
  GESTAUCHTEN Kopf eingestellt; ein nativ kalibrierter Kopf spreizt
  staerker -- laut #30 (+6pp bei ~2x Streckung) eher hilfreich, bleibt
  aber eine unkontrollierte Aenderung, die im Bericht zu nennen ist.

### rtv: konditionale Wiedereroeffnung (Nutzer-Frage 2026-08-04)

`rtv` ist `2*win_prob-1`, also eine GEWINNWAHRSCHEINLICHKEIT, und hat
den Zielwert an Rundenuebergaengen komplett ueberschrieben -- in einem
Ziel, das ansonsten eine Punkte-Marge ist. Das Trainingsziel war damit
INNERHALB einer Partie inkonsistent (normale Zustaende: Punktedifferenz,
Uebergangszustaende: Wahrscheinlichkeit, auf derselben Zahlenachse) --
dieselbe Inkohaerenz wie beim Bootstrap-Blend und eine plausible
Erklaerung dafuer, warum rtv das Netz nicht nur nicht half, sondern
aktiv verschlechterte (v13 mit rtv scheiterte am Gating, v13_nortv wurde
Champion, [[project-v13-cycle-result]]).

**Bleibt trotzdem GESCHLOSSEN**, mit ausformulierter
Wiedereroeffnungsbedingung (Muster [[project-ownership-head-closed]]):
1. NUR wenn #34 arena-erfolgreich ist (dann ist die Inkohaerenz-These
   bestaetigt und rtv hat ein echtes neues Argument) -- nicht vorher,
   sonst stapeln sich zwei Spekulationen;
2. dann NICHT in der alten Vollform: rtv kostete ~83% der Self-Play-Zeit
   (alte Engine-Generation gemessen) -- bei heutigen ~20h waeren das
   100h+. Nur als billige Teilvariante denkbar (weniger Chance-Samples,
   oder nur in einer kleinen Qualitaetskampagne);
3. Kosten VORHER neu messen ueber die frische Profiling-Infrastruktur
   (`MOSAIC_PROFILE_SELFPLAY=1`), nicht die alte 83%-Zahl fortschreiben.

### (urspruenglicher Zuschnitt) WDL-/Klassifikations-Value-Kopf (Report 1.2)
KataGo/lc0 ersetzen die Tanh-Regression durch Softmax-Klassifikation
ueber Ergebnisklassen; lc0s expliziter Ausloeser war exakt unser
Nichtlinearitaets-Symptom. Aufwand: Python (Kopf 1 Skalar -> 2 Logits,
MSE -> Kreuzentropie) + Rust (`value_to_win_prob` liest P(win) statt
(tanh+1)/2) + ONNX-Vertrag wie beim opp-Kopf (additiv, per Name erkannt,
Alt-Modelle unberuehrt).
**KONZEPTIONELLER VORBEHALT, vorab benannt**: Klassifikation braucht ein
HARTES Ergebnis-Ziel -- das Projekt hat sich mit VALUE_SCHEMA_VERSION=13
bewusst vom harten +-1 zum weichen tanh-Margin bewegt. WDL ist damit
teilweise eine Rueckabwicklung dieser Entscheidung; die Kombination
"weiches Margin-Ziel + Klassifikationsverlust" ist NICHT
literaturgestuetzt. Vor dem Bau ist zu entscheiden, welches Ziel gilt
(Vorschlag: hartes Sieg/Niederlage als eigener Arm, weil genau das der
lc0/KataGo-Praezedenzfall ist).

### Task #35: Ranking-Loss auf Geschwister-Q (Report 7.1) -- BRAUCHT ENGINE-VORLAUF
**Datenlage geprueft 2026-08-04**: Self-Play-Records tragen NUR
`policy[].prob` und ein SKALARES `root_q` -- **kein Q je Wurzelkind**.
Der Ranking-Loss braucht aber genau diese Paare.
**Konsequenz fuer die Reihenfolge**: das additive Logging (completed-Q je
Wurzelkind, analog zum `root_q`-Commit 2718b9a) muss VOR der
v20-Self-Play-Kampagne in die Engine -- sonst kostet das Experiment
spaeter eine eigene Kampagne (~20h) oder eine teure Nachannotation.
Danach: Trainings-Loss (RankNet-Stil auf Geschwisterpaaren) + Arena.
Dass #29 die Rang-METRIK verworfen hat, praejudiziert das Rang-TRAINING
nicht -- nur die Vorauswahl per Metrik faellt weg.

### Reihenfolge
#33 (heute/morgen, kein Code) -> #35-Engine-Logging (VOR v20-Self-Play,
klein und additiv) -> #34 (Code + Ziel-Entscheidung) -> #35-Training
(nach v20-Self-Play, wenn die Labels da sind).

---

## Folgetest-Plan nach #34: was die Ziel-Reparatur alles entwertet (2026-08-04)

Nutzer-Anstoss: #34 ist kein isoliertes Experiment -- die Umstellung des
Value-ZIELS (weiche Punkte-Marge -> hartes Sieg/Niederlage) entwertet
einen Teil der bestehenden Messbasis. Diese Liste ist VOR #34
festgeschrieben, damit hinterher nicht selektiv nachgemessen wird.

### A) Direkt an #34 gekoppelt (billig, Teil der Auswertung)
- **R5-Plattenkalibrierung** (`tools/r5_value_calibration.py`):
  Steigung heute 0,06-0,09 -> ?
- **Platt-Fit** (Verfahren aus `value_calibration_fit.json`): B=1,93 -> ?
- **Chance-Knoten-Vortest** (`tools/chance_node_pretest.py`): lief
  komplett am fehlgeleiteten Kopf, Wiederholung noetig.

### B) Wird durch #34 UNGUELTIG -- Neuentscheidung erforderlich
- **#30 Skalen-Korrektur**: faellt B Richtung 1 -> gegenstandslos.
  Bleibt B~2 -> die +6pp (p=0,20) verdienen eine Bestaetigungsmessung.
- **λ=0,7**: der Mix ist `λ*z + (1-λ)*root_q`. Aendert sich **z** von
  weicher Marge auf hartes Ergebnis, mischt λ etwas ANDERES -- der
  Arena-Sieg vom 2026-08-03 (227:173) gilt fuer den ALTEN z. **Vor der
  v20-Uebernahme neu zu testen.**
- **Deckenwerte R1-R4** (0,0068 / 0,166 / 0,437 / 0,604): zielspezifisch
  berechnet (Schema-15-Formel, `value_noise_floor_diagnostic`). Mit
  hartem Ziel aendern sie sich -> die gesamte "Luft nach oben"-Analyse
  muss neu gerechnet werden. Unangenehmster Posten, weil daran die
  Priorisierung der Value-Agenda haengt (evtl. Rust-seitige Anpassung
  der Diagnostik noetig, sie rechnet auf der aktuellen Zielformel).
- **TD_LAMBDA=0,5**: der Bootstrap-Wert ist bereits win-prob-artig; mit
  hartem z werden beide Mischkomponenten homogener -> Verhaeltnis
  moeglicherweise neu zu justieren.

### C) Reihenfolge-Korrektur
- **#33 (Loss-Gewichte) laeuft NACH #34**, nicht davor: das Optimum
  zwischen Value- und Policy-Gewicht haengt vom Charakter des
  Value-Ziels ab -- vorher zu messen hiesse, fuer ein Ziel zu
  optimieren, das gleich ersetzt wird.

### D) Kostenposten
- #34 aendert die Zielformel -> **`VALUE_SCHEMA_VERSION`-Bump ->
  kompletter Cache-Neubau ueber die 900 Dateien**. KEIN neues Self-Play
  noetig (die Rohdaten tragen `scores`/`winner` bereits), aber eine
  spuerbare Wartezeit vor dem ersten Trainingslauf.

### Ablauf
laufendes λ07-Gating -> #34 bauen -> Cache-Neubau -> #34-Training +
Kontrolle -> Diagnostiken (A) -> Neuentscheidung (B) -> #33 -> v20-Planung.

---

## Task #31 (vorgemerkt): Menschen-Schwierigkeitsstufen leicht/mittel/schwer/extrem (2026-08-03)

**Nutzer-Auftrag**: Staerke-Skalierung fuer Mensch-Spiele; Einschaetzung
"Sims allein richten es nicht" ist KORREKT und hier besonders: (a) R5-
Alpha-Beta + Tiling-DFS spielen sim-unabhaengig exakt -- eine 20-Sims-KI
spielt trotzdem perfekte Endspiele; (b) Gumbel+Policy-Prior traegt auch
Mini-Budgets -- flacher, aber nicht menschlich-fehlbar.

**Design-Skizze (3 Hebel je Stufe)**: Sims-Budget + Endspiel-/Tiling-
Degradation (R5-Knotenbudget-Override bzw. Policy-Sampling statt Solver,
Tiling greedy statt exakt bei "leicht") + Fehler-Injektion via Root-
Temperatur-Sampling mit Q-GAP-DECKEL (nur plausible Fehler <=3-5 Punkte;
menschlich-fehlbar statt gleichmaessig-flach; loest auch Ausrechenbarkeit).
Stufen: extrem=Champion@600-800 (optional lambda_aggr als Stil),
schwer=heutiger Stand @400, mittel=~100-150 Sims + Deckel-Sampling +
reduziertes R5-Budget, leicht=~8-16 Sims + Temperatur hoeher + epsilon +
Greedy-Tiling. ABGERATEN: alte Generationen als Stufen (Wartung,
OneDrive-Risiko, Regel-Fix-Inkompatibilitaeten, "gleichmaessig schwach").

**Kalibrierung**: vorhandene Elo-Leiter + Heuristik-Anker; je Konfiguration
n=150 vs 2 Anker, Ziel-Baender ~leicht 700-800 / mittel ~1000 / schwer
~1150-1200 / extrem=Champion. Umsetzung nach Muster Task #28
(Laufzeit-Parameter + Server-Preset + GUI-Dropdown). OFFEN (Nutzer):
Ziel-Baender ok? Darf "leicht" sichtbar Endspiele verstolpern?

**GATE (Nutzer-Entscheid 2026-08-03): ZURUECKGESTELLT** -- wird erst
angegangen, wenn ein Champion existiert, der auch gute menschliche
Spieler wirklich fordert. Bis dahin bleibt die Prioritaet auf
Staerke-Arbeit (v20-Zyklus, Value-Head-Front #29/#30, lambda=0.7-
Kandidat), nicht auf Schwierigkeits-UX.
