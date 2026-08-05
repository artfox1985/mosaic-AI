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
| **#34** | Sieg/Niederlage-Ziel + Kreuzentropie (WDL) wiederherstellen | **VERDIKT GEFAELLT** 2026-08-05: v20 = WDL + destretch-Blend + brierbest-Checkpoint | Umsetzung im v20-Zyklus | unten |
| **#35** | Q je Wurzelkind loggen (Ranking-Loss-Vorlauf) | **Engine-Teil erledigt** 2026-08-04 (root_child_q, Default AN) | #35b wartet auf v20-Self-Play | unten |
| #30 | Value-Skalen-Korrektur (Platt) | **geschlossen**: Effekt repliziert NICHT (p=0,90) | — | unten |
| #33 | Value-/Policy-Loss-Gewicht | wartet | in #34 integriert (Loss-Skala springt ~22x) | unten |
| #35b | Ranking-Loss-Training | wartet | #35-Logging + v20-Self-Play | unten |
| #31 | Schwierigkeitsstufen leicht/mittel/schwer/extrem | **geparkt** (Arbeitskreis "Spaeter", Nutzer) | Champion, der gute Spieler fordert | unten |
| #38 | Moon-Head-Feinschliff (Loss-Gewicht + myopisches Label) | **geparkt** (Arbeitskreis "Spaeter", Nutzer 2026-08-05) | wie #31 | unten |
| **#36** | Saettigt der Value-Kopf ueber die Spielzahl? | **BEANTWORTET 2026-08-06: NEIN -- spielhungrig, log-linear** | — | unten |
| **#37** | Tiling-Auswahlkriterium: `punkte*P(Sieg)` vs reines P(Sieg)-Ranking | **vorgemerkt fuer v20-Aera** (Nutzer 2026-08-05) | v20-Champion mit reifem WDL-Kopf | unten |
| #32 | Self-Play-Kostenprofil | **erledigt** 2026-08-04 | — | history |
| — | v20-Zyklus (Self-Play + Gating) | geplant | **#34-Ausgang + #36 + #14-Entscheid** (Nutzer 2026-08-05: Start erst, wenn klar ist, wie viele Spiele/Sims wirklich sinnvoll sind) | unten |
| — | R4b (Playout-Ground-Truth) | **Lauf 1 (N=24) NICHT INTERPRETIERBAR** per PREREG-Leseregel (beide Koepfe R²<0,1; Steigungen negativ = Rauschen; Werkzeug geprueft: Perspektive+Lader sauber) | Eskalation N=72 im naechsten idle-CPU-Fenster (Betriebsregel: Ground Truth braucht ruhige Maschine) | `r4b_value_calibration_wdl.json` |
| — | GUI: Aggressions-Slider entfernen | **erledigt** 2026-08-05 (kein Startwert -- Blend ueberall 0, s. Regeln) | — | history (Task #28) |
| #29 | Value-Rangmetrik | **geschlossen**: NICHT validiert (2/6) | — | history |
| #28 | Aggressions-Utility (opp-Kopf + Regler) | **ERGEBNISSE UNGUELTIG** (Engine-Audit F1: ownership-Logit als Gegner-Punkte gelesen) | Neumessung nach Fix noetig | unten (Engine-Audit) |
| #14 | PCR (beide Regime) | **geschlossen**, Wiedereroeffnung konditional | #34 + #36 + Durchsatz-Neumessung | unten |
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
- **v20-Kampagne (Nutzer 2026-08-05): Start ERST, wenn Spiel- und
  Sim-Budget belegt sind** -- also nach #36 (Spielzahl: saettigt der
  Value-Kopf?) und dem #14-Entscheid (Sims: lohnt PCR-Sim-Reduktion?).
  Die ~20h-Kampagne wird nicht auf geratenen Budgets gefahren. #36 ist
  damit auf dem KRITISCHEN PFAD zu v20 (laeuft dank `--wdl-hard-only`
  komplett sauber auf dem Bestandskorpus, kein v20 noetig).
- **λ (Value-Target-Mix)**: bis nach #34 ZURUECKGESTELLT -- #34 aendert
  `z` auf eine Gewinnwahrscheinlichkeit, damit mischt λ zwei Groessen
  derselben Art. Befundlage: gewinnt bei 65,7% root_q-Mix, verliert bei
  43,8% (zweimal, quer ueber Regime) -> **Korpus-Mischanteil entscheidet**.
  v20-Fenster entweder root_q-rein bauen oder λ neu messen.
  **Engine-Audit F1: das λ07_opp-Gating (33:47) lief mit w=0,1 und
  opp-Modell auf Kandidatenseite -- der Kandidat spielte mit
  ownership-Logit im Blend, das Ergebnis ist KONTAMINIERT und zaehlt
  nicht als λ-Beleg (weder dafuer noch dagegen).**
- **Aggressions-Blend: UEBERALL AUF 0 / INAKTIV (Nutzer 2026-08-05,
  nach Engine-Audit F1)**: "wir wissen ja nicht was er tut" -- alle
  Blend-Messungen waren ungueltig (ownership-Logit statt Gegner-Prognose
  gelesen). Konkret: Engine-Env-Defaults bleiben 0; die fruehere
  Arena-Konvention w=0,1/λ_aggr=2,0 ist AUFGEHOBEN (Gatings laufen ohne
  Blend); kein Serverstart-Default; **GUI-Slider ENTFERNT** (2026-08-05,
  im Browser verifiziert). Der Engine-Knopf (set_aggression_params,
  POST /api/aggression, Env-Vars) bleibt als inertes Werkzeug fuer die
  Neukartierung im v20-Zyklus -- nichts ruft ihn mehr auf. "Gate what
  you ship" gilt weiter und heisst jetzt: ausgeliefert wird OHNE Blend,
  also wird auch ohne Blend gegatet.
- **Tiling-Cache**: Default AN seit 2026-08-05 (-20,1% Self-Play-Wandzeit,
  bitgleich); `MOSAIC_TILING_CACHE=0` schaltet ab.
- **Statistik-Regel**: Score-basierte Arena-Auswertungen IMMER auf
  Block-Ebene (Paar-SEs unterschaetzen massiv). Win-basierte SPRT sind
  milder betroffen, Block-Zahlen trotzdem mitberichten.
- **Kein validierter Offline-Praediktor fuer die Value-Seite** (#29
  gescheitert, value_r2 viermal widerlegt) -> jede Value-Aenderung
  braucht ein Arena-Gating. **Nach #34 neu zu pruefen** (siehe unten).

## Task #34 ZWISCHENSTAND: Offline-Seite EINDEUTIG -- Stauchung von 1,93 auf 1,20 (2026-08-05)

Drei Arme trainiert (warm von `v19_2d_best`, 2D, Seed 2, Champion-Rezept,
900er-Fenster, neuer Cache `VALUE_SCHEMA_VERSION=16`).

**NAMENS-KORREKTUR (Nutzer 2026-08-05)**: die Arme hiessen zunaechst
`v20_*` -- falsch, denn Versionsnummern bezeichnen in diesem Projekt
GENERATIONEN, und eine Generation entsteht aus einer NEUEN
Self-Play-Kampagne. Diese Arme laufen auf dem BESTEHENDEN 900-Datei-
Fenster (v16/v17/v18-Partien), also demselben Korpus, aus dem schon v19
entstand. Es sind Ablationen, keine Generation -- umbenannt nach dem
Ablations-Muster des Projekts (`lam07_s3`, `pcrkontrolle_s6`, `fs_2d_s2`):
`v20_ctrl_tanh` -> **`t34_tanh`**, `v20_wdl_w02` -> **`t34_wdl02`**,
`v20_wdl_lossadj` -> **`t34_wdladj`**; Runde 2 entsprechend `t34b_*`.
Die Gating-Ergebnis-JSONs tragen weiterhin die alten Namen (datierte
Aufzeichnungen, bewusst unveraendert). Ein echtes v20 gibt es erst mit
einer neuen Self-Play-Kampagne.

| Arm | Ziel | VALUE_WEIGHT | **Brier** | **Platt-B** |
|---|---|---|---|---|
| `v20_ctrl_tanh` | weich (Bestand) | 0,2 | 0,2157 | 1,9055 |
| `v20_wdl_lossadj` | **Sieg/Niederlage** | 0,009 | 0,2048 | **1,2134** |
| `v20_wdl_w02` | **Sieg/Niederlage** | 0,2 | **0,2030** | **1,2037** |
| (Referenz `v19_2d_best`) | weich | 0,2 | -- | 1,9269 |

*(AUDIT-Anmerkung 2026-08-05: die B-Werte der WDL-Zeilen gehoeren zu den
`_best`-Checkpoints = **Epoche 1**, also fast untrainierten Koepfen; der
TRAINIERTE finale wdl02-Kopf hat **B=0,98**. Brier-Spalte = Endstaende.)*

**Die Stauchung faellt von 1,93 auf 1,20** -- der Rest-Fehler schrumpft um
zwei Drittel (B=1 waere perfekt kalibriert). Die Kontrolle bleibt bei
1,91, praktisch identisch zum Champion: es liegt WEDER am neuen Cache
NOCH am Warm-Start, sondern am ZIEL. Brier verbessert sich parallel
(0,2157 -> 0,2030, -5,9% relativ).

**Damit ist die Diagnose quantitativ bestaetigt**: der Value-Kopf war
gestaucht, WEIL er eine Punkte-Marge lernte und als
Gewinnwahrscheinlichkeit gelesen wurde. Ziel repariert -> Kalibrierung
repariert.

**Einordnung gegen die vier gescheiterten Offline-Signale**: das hier ist
keine Fit-Metrik, die zufaellig besser aussieht, sondern eine aus erster
Ursache VORHERGESAGTE Groesse, die exakt dort landet, wo die Theorie sie
erwartet. Das ist eine andere Qualitaet von Befund -- macht es aber NICHT
automatisch zu Spielstaerke. Gatings laufen.

**Nebenbefund**: die WDL-Arme starteten mit FRISCH initialisiertem
Value-Kopf (Shape-Mismatch gegen den tanh-Checkpoint), die Kontrolle
uebernahm ihren warm -- der WDL-Vorteil ist also eher unter- als
ueberschaetzt. Der hoehere VALUE_WEIGHT (0,2) liefert den besseren
Value-Fit (Brier 0,2030 vs 0,2048); ob er der Gesamtstaerke schadet,
entscheidet die Arena.

### Arena-Runde 1: ALLE VIER Gatings negativ -- aber alle konfundiert

| Vergleich | Ergebnis | Anmerkung |
|---|---|---|
| wdl_w02_best vs ctrl_tanh_best | 12:28 (30%) | Epoche-1-Checkpoints |
| wdl_w02_best vs v19_2d_best | 28:42 (40%) | Epoche-1-Checkpoints |
| wdl_lossadj_best vs ctrl_tanh_best | 47:63 (43%) | Epoche-1-Checkpoints |
| **wdl_w02_final vs ctrl_tanh_final** | **43:57 (43%)** | Endstaende, p=0,23 |

**Zwei Konstruktionsfehler, beide von mir**:
1. Die `_best`-Checkpoints waren **Epoche 1** -- `val_combined` waehlt bei
   WDL-Armen faktisch den untrainierten frischen Kopf (Value-Term
   entweder vernachlaessigbar bei w=0,009 oder unit-fremd bei w=0,2/BCE).
   Die ersten drei Gatings pruefen also nicht das ZIEL.
2. Der Value-Kopf startete FRISCH (Shape-Mismatch tanh->wdl) und das
   Early Stopping (nur Policy-Plateau) stoppte nach 15 Epochen -- der
   neue Kopf war also untertrainiert.

**KORREKTUR meiner Einordnung (Nutzer 2026-08-05)**: Ich hatte den
Kontrollarm als "ueber ~10 Generationen gereiften Kopf" beschrieben. Das
ist FALSCH -- so einen Kopf gibt es nicht. Die Historie
(`archive/history.md`) sagt das Gegenteil: der binaere +-1-Value-Kopf
hatte ueber VIER Generationen durchgehend NEGATIVES Val-R² (v8 -0,43 ->
v8d -0,25, schlechter als der blosse Mittelwert) und verschlechterte die
Suche AKTIV (0% Siegquote gegen die Heuristik; der Diagnose-Flip auf
DFS-Blatt sprang sofort auf 26%). Der `points_forecast`-Kopf am SELBEN
Trunk kam gleichzeitig auf 0,27-0,34. **Genau deshalb wurde der
Punkte-Kopf ueberhaupt etabliert.** Die damalige Erklaerung steht
woertlich im Archiv: das binaere Ziel kollabiert bei knappen Ergebnissen
zu einem "reinen Vorzeichen-Zufall", waehrend die kontinuierliche Marge
Abstufungen transportiert.

**Folge fuer die Deutung**: Das WDL-Arena-Ergebnis ist KEIN
Konfound-Artefakt, sondern die **Wiederholung eines dokumentierten
Befunds**. Neu ist nur die bessere Verlustgeometrie (Kreuzentropie statt
MSE) plus TD-Blend -- das hat die KALIBRIERUNG dramatisch verbessert
(B 1,93 -> 0,98), am LERNSIGNAL-Problem aber nichts geaendert.

**Damit ist die eigentliche Spannung benannt**: die architektonisch
korrekte Trennung (Sieg/Niederlage vs. Punkte) und das
trainingseffektivste Ziel sind NICHT dasselbe. Der weiche Margin war kein
Fehler, sondern ein Workaround fuer ein reales Problem.

**RAHMUNG (Nutzer 2026-08-05, wichtiger als das Einzelergebnis)**: Es war
nie zu erwarten, dass der binaere Kopf den etablierten Champion sofort
schlaegt -- **zu viele Knoepfe sind auf den Champion hin optimiert**. Der
Champion ist kein einzelnes Modell, sondern das Zentrum eines
CO-ADAPTIERTEN Systems:
- `VALUE_WEIGHT=0,2` eingestellt fuer MSE auf weichem Ziel,
- `TD_LAMBDA=0,5` ebenso,
- `c_puct=1,5` und `GUMBEL_C_SCALE=1,0` kalibriert (Task #18), ALS die
  Werte um ~Faktor 2 gestaucht waren,
- selbst der KORPUS stammt von Netzen mit weichem Ziel.
Eine Ein-Faktor-Aenderung gegen ein vollstaendig abgestimmtes System muss
verlieren. Erfolgsmassstab fuer #34 ist daher NICHT "schlaegt den
Champion sofort", sondern "ist die bessere Grundlage" -- die Entscheidung
dafuer ist gefallen (Nutzer: "#34 wird so oder so kommen").

**KONKRETER, BILLIG PRUEFBARER VERDACHT**: die SUCHPARAMETER sind fuer den
neuen Kopf fehlkalibriert. Gumbels `sigma(q)` ist LINEAR in q; der
WDL-Kopf spreizt ~2x weiter als der alte (Platt-B 1,93 -> 0,98), die
effektive Perturbation ist damit ~2x staerker als die, fuer die
`c_scale=1,0` eingestellt wurde -- und laut Gumbel-Paper (Atari-Ablation)
schadet ZU GROSSES c_scale. Test ohne jeden Umbau: `MOSAIC_VALUE_CAL_B`
(Task-#30-Knopf, monotone Logit-Skalierung) auf **~0,55** setzen bringt
die Spreizung des WDL-Netzes auf das Niveau zurueck, fuer das die Suche
eingestellt ist. **Hilft das, ist nicht das ZIEL das Problem, sondern die
SUCH-Parametrierung** -- und der richtige Fix waere, c_scale/c_puct fuer
das neue Regime neu zu kalibrieren, statt das Ziel aufzugeben.

**Naheliegender naechster Arm statt Rueckzug**: unser WDL-Ziel ist bereits
HALB kontinuierlich (`TD_LAMBDA*bootstrap_winprob + (1-TD_LAMBDA)*harter
Ausgang`, TD_LAMBDA=0,5). Ein HOEHERES TD_LAMBDA behaelt die
Wahrscheinlichkeits-Semantik und holt Informationsreichtum zurueck --
das ist der Hebel, den die v8-Aera nicht hatte (dort war das Ziel rein
binaer). **AUDIT-KORREKTUR 2026-08-05: erst NACH sauberem Bootstrap
umsetzbar -- der heutige bootstrap_value traegt Alt-Semantik (Befund 1
im Audit unten); ein hoeheres TD_LAMBDA erhoehte JETZT den kontaminierten
Anteil.**

**Inhaltlich bemerkenswert bleibt trotzdem**: der WDL-Kopf ist praktisch
perfekt kalibriert (Platt-B **0,98** vs 1,70 der Kontrolle) und spielt
dennoch schlechter. Kein Widerspruch, sondern ein Hinweis auf einen
Zielkonflikt -- und die v13-Begruendung liest sich rueckblickend
plausibler: das weiche Margin-Ziel transportiert MEHR Information pro
Sample ("knapp gewonnen" vs "klar gewonnen"), das harte kollabiert das
auf ein Vorzeichen. Fuer den gemeinsamen Trunk ist die reichere Groesse
offenbar das bessere Lernsignal, auch wenn sie als Wahrscheinlichkeit
schlechter kalibriert ist.

**Behoben (Commit 6c01eb7)**: doppeltes Early Stopping (Policy UND
Value/Brier) + `--select-by-brier`. Arena-Runde 2 laeuft mit beiden
Schaltern und fairem Reifegrad.

### Arena-Runde 3 (2026-08-05): brierbest-Checkpoint spielt PARITAET

| Vergleich | Ergebnis | p (Fixed-n) |
|---|---|---|
| wdlhard_brierbest (E2) vs t34_tanh (final) | 65:75 (46,4%) | 0,47 |
| **wdlhard_brierbest (E2) vs v19_2d_best (Champion)** | **106:114 (48,2%)** | **0,65** |

Beide SPRT-H0, beide KIs decken 0 ab. Bemerkenswert: ein Kopf mit ZWEI
Epochen sauberem Sieg/Niederlage-Training (Brier 0,1970, bester Wert
aller Arme) spielt statistische PARITAET mit dem Champion. Damit steht
nach 6 Gatings ueber 3 Runden ein konsistentes Bild: **das Value-Ziel
bewegt die Spielstaerke bei 400 Sims nicht messbar** (Aufloesungsgrenze
~8pp beachtet) -- die Kalibrierung verbessert sich drastisch, die
Staerke ist invariant. Fuer das #34-Verdikt heisst das: die Ziel-Wahl
entscheidet sich an Kalibrierung/Nutzbarkeit (GUI-Anzeige,
Blend-Semantik, kuenftige Suche mit korrekten Wahrscheinlichkeiten)
und an der TRAININGS-Stabilitaet (Erosions-Arme), nicht an der Arena.

### Erosions-Arme (PREREG_task34_erosion_arms.md) -- ERGEBNIS 2026-08-05

| Arm | Ziel | Peak-Brier (Ep.) | Final E15 | Erosion |
|---|---|---|---|---|
| tanh (Bestand) | weiche Marge | 0,2147 (E2) | 0,2157 | +0,001 |
| wdl02 | Blend kontaminiert | 0,1990 (E3) | 0,2030 | +0,004 |
| wdlhard | hart pur | 0,1970 (E2) | 0,2440 | +0,047 |
| wdlsmooth | hart + eps=0,1 | 0,1971 (E3) | 0,2148 | +0,018 |
| **wdldestretch** | **Blend entstaucht** | **0,1971 (E3/4)** | **0,2018** | **+0,005** |

Beide Hypothesen bestaetigt, klare Rangfolge: Label-Smoothing daempft
die Erosion um ~60% (Memorisierung ist ein realer Hauptmechanismus),
aber der ENTSTAUCHTE BLEND schlaegt alles -- bester Peak (zugleich
hoechstes Val-R² aller WDL-Arme: 0,346), mildeste Erosion, bester
Endstand. Die pro-Zustand-Information des Bootstraps ist der eigentliche
Stabilisator; entstaucht liefert er sie ohne Alt-Kontamination.

### Pflicht-Diagnostiken am Verdikts-Kandidaten (t34_wdldestretch_brierbest)

- **Platt-Fit**: B = **0,97** (praktisch perfekt; der erodierte
  E15-Endstand kippt auf B=0,81 = UEBERkonfident -- passt zur
  Memorisierungs-Drift). Frozen-Set-Vorbehalt (v12-Aera) gilt.
- **R5-Plattenkalibrierung** (`r5_value_calibration_wdl.json`):
  tanh-Kontrolle reproduziert den Altbefund (Steigung 0,086); der
  WDL-Kandidat kommt auf **0,273** -- Faktor ~3 besser, aber weiterhin
  WEIT von 1. Die Ziel-Reparatur erklaert die Platten-Blindheit also nur
  TEILWEISE. Wertungsplatten-Intervention bleibt GEPARKT, aber die
  Wiedervorlage-Bedingung ist jetzt konkret: nach v20 (nativer sauberer
  Blend + laengeres Value-Training) neu messen; bleibt die Steigung
  dann flach, ist der gezielte Eingriff (Platten-Encoding/Aux-Kopf)
  gerechtfertigt.

### destretch-Gatings (2026-08-05, Abschluss): 75:85 vs tanh (p=0,51),
65:75 vs Champion (p=0,52) -- beide H0, KIs decken 0. Damit **acht
Gatings, acht Mal Ziel-Invarianz** der Arena.

**#34-VERDIKT (FINAL 2026-08-05)**:
v20-Zielkonfiguration = **WDL (2-Logit-CE) + entstauchter
Bootstrap-Blend** (`--value-head wdl --wdl-bootstrap-destretch`),
Checkpoint-Politik: `_brierbest` zusaetzlich sichern (Peak vor der
Erosion). Ab der v20-Kampagne liefert der WDL-Generator native
[0,1]-Bootstraps -- die Entstauchung entfaellt dann von selbst.
Begruendung: Arena ist ziel-invariant (6 Gatings), also entscheiden
Kalibrierung (B 1,93 -> 0,97), Trainings-Stabilitaet (Erosionstabelle)
und Semantik-Nutzbarkeit.

## AUDIT 2026-08-05 (Nutzer-Auftrag): Konsistenz aller Tasks & Messketten nach dem Soft-Head-Fund

Der eher zufaellige Fund des weichen Value-Ziels wirft Annahmen und
Messketten durcheinander -- systematisch geprueft, sechs Befunde:

### Befund 1 (SCHWERSTER): auch das NEUE WDL-Ziel ist zur Haelfte kontaminiert
`values_wdl = 0,5*bootstrap_value + 0,5*harter Ausgang` -- aber
`bootstrap_value` wurde beim Self-Play von den GENERATOR-Netzen (v16-v18,
tanh-Kopf, Platt-B~1,9) berechnet: eine gestauchte Punkte-Marge, per
`value_to_win_prob` als "Wahrscheinlichkeit" etikettiert. **#34 hat also
noch nie ein sauberes Wahrscheinlichkeits-Ziel getestet** -- die Haelfte
des Ziels ist Richtung 0,5 verzerrtes Alt-Material. Dasselbe gilt fuer
`root_q` in ALLEN Bestandskorpora (betrifft die λ-Mix-Ergebnisse: auch
der "Arena-Sieger" λ=0,7 mischte margen-artige root_q).
**Konsequenzen**: (a) neuer Arm **`t34_wdlhard`** (`--wdl-hard-only`,
trainiert auf dem ROHEN `wdl_outcome`) -- laeuft; (b) "hoeheres
TD_LAMBDA" erst nach einer Kampagne mit WDL-Generator (oder mit
Platt-entstauchtem Bootstrap als Cache-Option -- nicht gebaut);
(c) erst die v20-Kampagne mit WDL-Kopf liefert unkontaminierte
bootstrap/root_q-Labels.

### Befund 2: "WDL spielt schlechter" ist NICHT belegt
Einziges sauberes Gating: 43:57, p=0,23, EIN Seed-Satz -- bei ~8pp
dokumentierter Seed-Streuung kein Beleg. Die drei anderen Gatings waren
Epoche-1-konfundiert. Ehrliche Lage: **kein nachweisbarer
Staerke-Unterschied in beide Richtungen**, nicht "WDL verliert".

### Befund 3: "Runde 2" war KEINE Replikation, sondern ein deterministischer Re-Run
Seed 2 identisch zu Runde 1 -> Brier-Trajektorien zahlengleich
(0,2157/0,2030), Stopp wieder E15, Auswahl wieder E1 (der Policy-Term
~1,16 dominiert val_combined auch mit `--select-by-brier`; der
Brier-Term traegt nur ~0,04). Die `t34b_*`-Dateien waren Duplikate ->
geloescht. Ein Gating "Runde 2 vs Kontrolle" haette NULL neue
Information geliefert -> entfaellt.

### Befund 4: der WDL-Value-Fit DEGRADIERT ab Epoche ~3 (neuer Primaerbefund)
wdl02: Brier 0,1990 (E3) -> 0,2030 (E15), MONOTON schlechter; tanh:
flach (0,2147->0,2157). Fortgesetztes Policy-Training erodiert den
harten Value-Fit -- ein direkt messbarer Trunk-Konflikt, den das weiche
Ziel nicht zeigt. Die v13-Konflikt-DIAGNOSE bekommt damit erstmals ein
Messbild (Richtung umgekehrt: Policy erodiert Value). Der value-optimale
Zustand (E3) existierte nie als Datei -> `train.py` speichert jetzt
zusaetzlich einen **`_brierbest`**-Checkpoint (+ONNX).

### Befund 5: Brier-Aufloesung -- und zwei sich widersprechende Brier-Messungen
Effektive Value-Stichprobe = PARTIEN, nicht Zustaende (~162 Zustaende
teilen sich EIN Ausgangs-Bit). Frozen-Set (385 Partien): wdl-tanh =
-0,0030, 95%-KI [-0,0077, +0,0018] -> nicht aufloesbar. Val-Split (~900
Partien, aktuelle Verteilung): Luecke 0,0127 >> geschaetzte SE ~0,003 ->
dort real. Plausibelste Deutung: VERTEILUNGS-SHIFT -- das
`frozen_eval_set` stammt aus der **v12-Aera** (gebaut 2026-07-24, 5
Generationen alt). **Alle darauf gerechneten Diagnostiken (Platt-Fits,
Chance-Knoten-Vortest, Brier-Vergleiche) tragen diesen Vorbehalt; nach
#34 neu bauen** (`tools/build_frozen_eval_set.py` existiert).

### Befund 6: Konsistenzfehler in diesem Dokument (korrigiert)
Platt-B-Tabelle: 1,20 = Epoche-1-Checkpoint, trainierter Kopf = 0,98
(Anmerkung ergaenzt); #35-Engine-Teil war laengst erledigt (Index
korrigiert); die alte "Reihenfolge"-Zeile (#33 VOR #34) widersprach der
beschlossenen Korrektur C (#33 IN #34) -- bereinigt.

### Kontaminationskarte: was der Soft-Head-Fund entwertet -- und was nicht
- **GUELTIG bleiben**: alle Arena-/Elo-Ergebnisse (ausgangsbasiert), die
  Champion-Kette, die Orakel-POLICY-Validierung 7/7 (empirisch gegen die
  Arena), Korpus-Dosis (Policy-Metriken), Profiling/Tiling-Cache.
- **UMZUDEUTEN (Messung ok, Interpretation neu)**: R5-Steigung 0,06-0,09,
  Kopf-Uneinigkeit r=0,68, B=1,93, rtv-Scheitern, #30-Nullbefund --
  alles Symptome der Ziel-Semantik, keine "Defekte" des Kopfes.
- **ENTWERTET / NEU NOETIG**: Chance-Knoten-Vortest (Kalibrier-Signatur
  am falschen Kopf -- Wiederholung nach #34 steht schon im Plan);
  Rauschboden-Serie R1-R4 (Schema-15-Formel; daran haengt die gesamte
  "Luft nach oben"-Priorisierung); #29-2/6 (Aepfel-Birnen, siehe "NACH
  #34"); **Orakel-Q-Referenzen fuer kuenftige VALUE-Validierungen** (die
  5000-Sim-Suchen liefen mit Alt-Kopf -- vor einer #29-Wiederholung neu
  erzeugen; die POLICY-seitige 7/7-Validierung bleibt davon unberuehrt).
- **VERSTECKT KONTAMINIERT**: `bootstrap_value` und `root_q` in allen
  Bestandskorpora (Befund 1) -- heilt erst die v20-Kampagne mit WDL-Kopf.

**c_scale-Diagnose ERLEDIGT (2026-08-05)**: WDL-Netz vs Heuristik,
identische Seeds, gepaart: B=1,0 -> 62,5%, B=0,55 -> 64,5%, diskordant
49:45, McNemar p=0,76 -- **kein Effekt, die Suchparametrierungs-These
faellt**. Zusammen mit dem #30-Nullbefund (Streckung am ALTEN Netz:
nichts) ist die Gumbel-sigma-Linearitaets-These in BEIDE Richtungen
widerlegt: die Suche ist robust gegen die Value-Spreizung,
c_scale/c_puct muessen fuer den WDL-Kopf NICHT neu kalibriert werden.
Verbleibende Erklaerungskandidaten fuer die Arena-Paritaet des sauberen
Ziels: Korpus-Co-Adaption und/oder das weiche Ziel als real besseres
Trunk-Lernsignal (Befund 4).

**Laufend**: `t34_wdlhard`-Training + Engine-Gegenpruefungs-Agent.

## ENGINE-GEGENPRUEFUNG (Agent-Audit, Nutzer-Auftrag 2026-08-05): 3 bestaetigte Fehler, alle gefixt

Vollpruefung von Suchbaum-Perspektive, Wertebereichen, Encoding, Masken,
ONNX-Vertrag, Regelkonsistenz, Arena-Werkzeugen und Loss-Arithmetik --
mit dem Soft-Head-Fund als Fehler-Muster. Alle Agent-Befunde vor
Uebernahme selbst am Code verifiziert.

### F1 (HOCH, GEFIXT): opp_points las den ownership-Head -- ONNX-Index-Fehler
`net.rs` extrahierte `out[4]` als Gegner-Punkte-Prognose; laut
Export-Vertrag ist `out[4]` aber der 72-dim `ownership`-Head, `opp_points`
haengt dahinter (real Index 5). Der #28-Blend las damit den **rohen
ownership-Logit von Feld (0,0)** als "Gegner-Punkte" -- kein Crash, nur
leise falsch. Der Rust-Vertragstest kodierte die Output-Liste OHNE
ownership und dokumentierte damit exakt den Vertrag, den der Export nie
erfuellt hat.
**Fix**: Extraktion jetzt ueber den beim Laden erkannten Namens-Index
(`opp_head_index`), Tests auf die reale Export-Reihenfolge umgestellt,
Wheel neu gebaut + installiert, Smoke-Test am echten opp-Modell gruen.
**ENTWERTET sind alle Messungen mit w>0 + opp-Modell**:
- die komplette λ_aggr-Kartierung nach oben ("bis 2,0 ohne
  Winprob-Verlust") und die w-Leiter (0,2/0,3),
- der #28-Befund "kein Denial-Beleg",
- das λ07_opp-Champion-Gating (33:47),
- die Zahlenbasis der Arena-Konvention w=0,1/λ_aggr=2,0.
**NICHT betroffen**: alle #34-Gatings und -Trainings (Modelle ohne
opp-Kopf, Blend inert), alle w=0-Laeufe, das reine opp-Kopf-TRAINING
(Python-seitig, korrekt). **Neumessung der Aggressions-Kartierung:
Nutzer-Entscheid 2026-08-05 -- erst im NAECHSTEN Korpus/Generation
(v20-Zyklus), NICHT im Nach-#34-Paket.** Bis dahin bleibt der Blend in
Arena-Laeufen faktisch ohne belegte Parameter; das Nach-#34-Paket
schrumpft auf #9, #12, #29 (+Offline-Praediktoren).

### F2 (MITTEL, GEFIXT): Abbruch-Partien lieferten harte Sieg-Labels
Rust stempelt `scores`/`winner` auch bei Timeout-Abbruch; der versprochene
Downstream-Filter existierte nie (self_play.py warnt nur). Der
`-1`-Sentinel fuer `wdl_outcome` war auf Rust-Korpora UNERREICHBAR --
Abbruch-Zwischenstaende wurden zu harten Labels (auch fuer Brier und
`--wdl-hard-only`). **Gemessen: aktueller 900er-Korpus 0% betroffen**
(Stichprobe 90 Dateien, alle 900 Partien completed) -- Korrektheits-Fix
fuer kuenftige Kampagnen, kein Label-Shift, daher kein Schema-Bump.
Fix in neural_net.py: `completed=False` -> wdl_outcome=-1,
opp_points_mask=0, value_wdl=weiche Projektion.

### F3 (KLEIN, GEFIXT): Nenner/Val-Inkonsistenz im neuen --wdl-hard-only
Gewichteter Trainingspfad teilte durch die UNmaskierte Gewichtssumme;
Val-Zweig ignorierte `v_rw` (bei `--exclude-round5` haette val_combined
andere Samples enthalten als der Loss). Beides behoben; der gelaufene
wdlhard-Lauf war nicht betroffen (rw=None-Pfad).

### Verdachtsfaelle
- **V1 (offen, klein)**: Arena-Partien tragen kein `completed`-Flag --
  ein Timeout-Abbruch zaehlt als normaler Sieg im SPRT. Kein Beleg fuer
  konkreten Schaden; additives Flag + Zaehlung als kleiner Folgetask.
- **V2 (GEFIXT)**: stille Champion-Fallbacks -- arena.py fiel bei
  fehlendem Champion-ONNX kommentarlos auf v18_best zurueck (jetzt
  Hard-Error), server.py startete kommentarlos ohne Modell (jetzt laute
  Warnung).
- **V3 (GEPRUEFT, SAUBER)**: placed_color/placed_special-Praezedenz
  zwischen den Encodern -- per Konstruktion exklusiv (Special-Felder
  akzeptieren nie Farben, Normal/Wild nie Weiss), unerreichbar.

### Geprueft und sauber (Agent + Stichproben-Gegenpruefung)
Ply-Paritaet/Backup-Perspektive, root_q/root_child_q-Konventionen,
Kalibrierungs-Knopf-Achse, #28-Blend-Skalen (abgesehen von F1s falscher
Quelle), Gumbel-sigma/v_mix, Beobachtungs-Encoding (JSON- und
Direct-Pfad, 1D+2D), Masken-Nenner (ausser F3), WDL-ONNX-Vertrag,
Regelkonsistenz-Stichprobe (alle Zuege via Game::apply_*), Tiling-Memo-
Key, paired_gating-Zuordnung/SPRT, bootstrap/rtv-Perspektive.
NICHT abgedeckt: Voll-Audit der 4 Regel-Fixes gegen das Regelbuch,
~35 weitere tools/-Skripte, py.rs-Bindungsschicht, profiling.rs.

## REGELBUCH-AUDIT (Agent-Dreiecksvergleich Manual/Original-PDF/Engine, 2026-08-06)

Nutzer-Auftrag; Agent-Befunde stichprobenartig selbst verifiziert (A1/A2/O1
am Code bestaetigt). **Kern-Fazit: KEIN Engine-Fehler gegenueber dem
Manual gefunden -- in allen drei Konfliktfaellen stand der Code auf der
Seite des Original-Regelbuchs, das MANUAL war falsch.** Manual korrigiert
(Commit dieses Stands): Linien-Wertung ist farbUNabhaengig (nicht
"gleichfarbig"), 4 Chips je Runde / genau 2 je Spieler Pflicht (nicht
"2 verfuegbar, max 2 optional"), Unplatzierbarkeits-Bedingung (3 Platten
voll + kein passendes Feld; Carry-over in Folgerunde) -- plus 8 ergaenzte
Luecken (Kuppelplatten-Pflicht 2/Runde + R5-Verbot, Start=5 Punkte,
Stapel-Zug-Mechanik, Ablage=3 ohne Nachfuellen, Wildfelder, Mond-Stapel-
Reihenfolge waehlt der Nehmer, Pass-Pflicht, Vorrats-Erschoepfung).

**O1 ENTSCHIEDEN + GEFIXT (Nutzer 2026-08-06, Commit 3aacf2a)**:
Befuellungs-Reihenfolge auf Original umgestellt -- grosse Fabrik ZUERST,
dann die kleinen. Wirkt nur bei Vorratsknappheit (Beutel+Turm < 21);
Regeltest `fill_factories_scarcity_feeds_large_factory_first`, alle 279
Engine-Tests gruen, Wheel neu installiert. Nebenwirkung dokumentiert:
gleiche Seeds ziehen jetzt eine andere Fliesen-Verteilung (RNG-Strom-
Reihenfolge) -- alte Partie-Replays sind nicht bit-identisch, laufende
Messreihen (Trainings) unbetroffen (nutzen fertige Korpora). Der
900er-Bestandskorpus traegt die alte Reihenfolge nur in seltenen
Knappheits-Situationen -- vernachlaessigbar, v20 wird voll konsistent.

**Klein, defensiv (U1)**: `apply_tiling_chips` (game.rs/py.rs) prueft die
Chip-Top-down-Sperre nicht auf Apply-Ebene (nur Solver/UI-seitig
durchgesetzt; regulaeres Spiel nicht betroffen, direkter API-Aufruf
koennte sie umgehen). Als kleiner Defensiv-Task offen.

Nebenbefunde: Gratis-Stapelziehung bei 0 Punkten ist KEINE Hausregel,
sondern die Auslegung einer REGELLUECKE (Nutzer-Klarstellung 2026-08-06:
das Original spezifiziert den 0-Punkte-Fall schlicht nicht; die
Engine-Loesung folgt konsistent aus "nie unter 0", dokumentiert
82e8a88 R6); Tie-Break-Verdachtsfall aufgeloest (Marker wird
strukturell in jeder Runde genommen, `factory.rs:214` +
`check_drafting_complete` -- Manual, Original und Code deckungsgleich).

## Task #30 ABGESCHLOSSEN: Skalen-Korrektur repliziert NICHT (2026-08-05)

Bestaetigungslauf mit FRISCHEN Seeds (90260805, sonst identisches Design:
Netz vs. Heuristik, 2x200, gepaart je Spielindex):

| | OFF | ON | diskordant b/c | McNemar p |
|---|---|---|---|---|
| Erstlauf (2026-08-04) | 68,0% | 74,0% | 43 / 31 | 0,20 |
| **Bestaetigung** | **76,0%** | **77,0%** | **31 / 29** | **0,90** |
| gepoolt (nur deskriptiv) | 72,0% | 75,5% | 74 / 60 | 0,26 |

**VERDIKT: kein Effekt.** Die +6pp des Erstlaufs replizieren nicht.
Die Gumbel-sigma-Linearitaets-These (Report-Idee 7.3) ist damit ueber
diesen Weg NICHT gestuetzt. Der Laufzeit-Knopf `MOSAIC_VALUE_CAL_A/B`
bleibt im Code (Default 0/1 = inert, bitgleich) -- falls nach #34 noch
eine Restfehlkalibrierung messbar ist, ist er sofort einsetzbar.

**WICHTIGER METHODEN-BEFUND, ueber #30 hinaus**: die OFF-Referenz sprang
zwischen den Seed-Saetzen von **68,0% auf 76,0%** -- identisches Modell,
identische Einstellungen, nur andere Seeds. Ein 8-Prozentpunkte-Schwung
allein in der Referenz. Ein 6-Punkte-Unterschied zwischen Armen liegt
damit im Rauschen dieses Aufbaus. **Konsequenz fuer alle kuenftigen
Netz-vs-Heuristik-Messungen**: Effekte unter ~8pp brauchen entweder
deutlich mehr Spiele oder mehrere Seed-Saetze; die gepaarte Struktur
faengt die Streuung NICHT vollstaendig ab (sie paart Spielindizes, nicht
Seed-Saetze). Zusammen mit der Block-Korrelations-Lektion (2026-08-04)
das zweite Mal, dass unsere Arena-Statistik zu optimistisch war.

## NACH #34 NEU ZU BEWERTEN (Nutzer-Anmerkungen 2026-08-05)

#34 aendert die Semantik des Value-Kopfs von einer gestauchten
PUNKTE-MARGE auf eine GEWINNWAHRSCHEINLICHKEIT. Alles, was am alten Ziel
gemessen oder darauf eingestellt wurde, steht damit zur Nachpruefung --
NICHT automatisch wieder offen, aber mit konkretem Anlass:

1. **Arena-Konvention (w=0,1 / λ_aggr=2,0)** -- **VERSCHOBEN in den
   v20-Zyklus (Nutzer 2026-08-05, nach Audit-F1)**: der Blend ist
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
4. **NEU (Nutzer 2026-08-05): Task-#20-Kopplung Value-Kopf <-> Tiling-Solver**.
   Der Value-Kopf ist seit #20 in die TILING-AUSWAHL eingebaut (Runden 2-4,
   `NET_TILING_TIEBREAK_ENABLED=true`): unter den Top-12 punktbesten
   Tiling-Abschluessen gewinnt der mit maximalem **`punkte *
   value(Folgezustand)`** (tiling_solver.rs:793, roh `(v+1)/2`, kein Blend).
   Drei Gruende fuer die Nachpruefung, VOR der v20-Kampagne:
   a) **Stille Semantik-Verschiebung durch #34**: mit dem Margen-Kopf war
      `punkte * (v+1)/2` ein doppelt punkte-lastiges Kriterium; mit
      WDL-Kopf wird es `punkte * P(Sieg)` -- ein ANDERES Kriterium bei
      unveraendertem Code (exakt die Audit-Fehlerklasse). Design-Frage:
      unter einem kalibrierten Kopf ist vermutlich reines P(Sieg)-Ranking
      das sauberere Kriterium (das Produkt zaehlt Punkte doppelt).
   b) **Validierung ist ziel-veraltet**: Referenz-Lauf 2026-07-29 (v18,
      R2 71%/R3 82% belegt, **R4 48% = Muenze**) lief am alten Kopf; die
      damalige Entscheidung "Fenster 2-4 bleibt" beruhte auf "erbt
      automatisch jede Value-Head-Verbesserung" -- #34 IST dieser Sprung,
      die vorgesehene Wiederholungsmessung ist faellig.
   c) Die alte Referenz (v17_best@2000) ist geloescht; Neuauflage mit
      Champion-Referenz + WDL-Kandidat (`tiling_value_reference_main.py
      --rank-model ... --ref-model v19_2d_best`), ein Abendlauf (CPU).
   Relevanz: `resolve_tiling_step` laeuft im SELF-PLAY -- die v20-Kampagne
   wuerde sonst mit unvermessenem, semantisch verschobenem
   Tiling-Verhalten generieren.

   **WIEDERHOLUNGSMESSUNG DURCHGEFUEHRT (2026-08-05, Original-Referenz
   v17_best@2000 aus Nutzer-Backup)** -- mit INSTRUMENT-FIX: Referenz-
   Gleichstaende (m=0; in R4 37% aller Paare, weil die Referenz dort der
   EXAKTE Alpha-Beta-Wert ist) zaehlten bisher als Fehlgriff und
   drueckten die Quote kuenstlich -- auch die Juli-"Muenze" (48,3%) war
   grossteils dieses Artefakt. Bereinigt, identische Zustaende/Paare:

   | R4 (267 Paare + 157 Ties) | Quote | p |
   |---|---|---|
   | t34_wdldestretch_brierbest | **74,5%** | 4e-16 |
   | t34_tanh (Kontrolle) | 68,2% | 3e-9 |

   **Gepaart: 19:2 diskordant fuer WDL, McNemar p=0,0002** -- der
   reparierte Kopf rangiert R4-Tilings signifikant besser; ERSTER
   Befund, in dem das neue Ziel einen funktionalen Vorteil jenseits der
   Kalibrierung zeigt. R2: 81,5% (Juli 71,2%). R3-AUFKLAERUNG (tanh-Kontrolle,
   identische Paare): R2 -- beide Koepfe treffen IDENTISCHE
   Entscheidungen (0 diskordant, je 81,5%). R3 -- tanh 65,2% vs WDL
   50,0%, diskordant 9:39, p<0,0001. ABER: die R2/R3-Referenz ist eine
   v17-SUCHE, also ein Alt-Familien-Margen-Kopf -- sie misst
   FAMILIEN-NAEHE, nicht Qualitaet (dieselbe Verzerrung steckte in der
   Juli-Validierung v18-vs-v17). Nur die R4-Referenz ist exakt (Alpha-
   Beta-Ground-Truth), und dort gewinnt WDL 19:2.

   **#20-ENTSCHEID (Beleg-Lage)**: Fenster 2-4 BLEIBT -- R2 identisch,
   R4 klar pro WDL, R3 nicht valide arbitrierbar (Referenz-Familien-
   Bias; die Arena, die den Tiebreak in den laufenden Gatings ja
   MITSPIELT, zeigt Paritaet -> kein Alarmsignal). Kriteriums-Frage
   (`punkte * P(Sieg)` vs reines P(Sieg)) bleibt offen fuer die
   v20-Aera; eine kuenftige R2/R3-Neuvalidierung braucht eine
   familien-neutrale Referenz (z.B. Playout-Ground-Truth wie R4b statt
   Alt-Netz-Suche).
5. **#12 Distributionaler Punkte-Kopf**: bleibender Befund war "mehr
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

## Task #37 (NEU, Nutzer 2026-08-05): Tiling-Auswahlkriterium fuer die naechste Generation

**Frage**: Welches Kriterium waehlt unter den Top-12-Tiling-Abschluessen
(Task-#20-Kopplung, `tiling_solver.rs::best_first_step_valued`):
(a) Bestand `punkte * P(Sieg)`, (b) reines P(Sieg)-Ranking,
(c) P(Sieg) mit Punkte-Tiebreak nur bei nahezu gleichem P?

**Hintergrund** (Diskussion 2026-08-05): Mit dem kalibrierten WDL-Kopf
fliesst die Punkte-Information beim Produkt ZWEIMAL ein -- einmal korrekt
dosiert via P(Sieg|Folgezustand), einmal als eigener Faktor mit
willkuerlichem Wechselkurs (ob die bessere Siegchance sich durchsetzt,
haengt vom absoluten Punkteniveau ab). Mit dem ALTEN Margen-Kopf war das
Produkt in sich stimmig und wirkte wegen der Stauchung de facto als
reiner Punkte-Stichentscheid -- der kalibrierte Kopf spreizt ~2x weiter
und kann Punktunterschiede real ueberstimmen (stille
Verhaltensverschiebung ohne Codeaenderung).

**GEGENARGUMENT, vorab notiert**: der Punkte-Faktor wirkt derzeit als
robuster PRIOR, der Value-Rauschen baendigt (Kopf nach 2-3 Epochen noch
verrauscht) -- moeglicherweise ist das Produkt genau deshalb praktisch
robust. Entscheid daher NUR per Arena, nicht am Schreibtisch.

**Zuschnitt**: v20-Aera (reifer WDL-Kopf im Champion), Arena-A/B der
Varianten (a) vs (b), ggf. (c) als dritter Arm; Laufzeit-Schalter analog
Task-#30-Muster, damit kein Rebuild je Arm noetig ist. Bis dahin bleibt
(a) Bestandsverhalten.

### Task #36 ERGEBNIS (2026-08-06): Value-Kopf saettigt NICHT -- Spielzahl ist ein echter Hebel

Externe Brier-Auswertung aller 18 Checkpoints auf dem gemeinsamen
90-Dateien-Messset (900 Partien, `tools/t36_curve_eval.py`):

| Pool | brierbest (Mittel 3 Seeds) | Peak-Epochen |
|---|---|---|
| 202 | 0,19934 | 2-4 |
| 405 | 0,19813 | 4-6 |
| 810 | **0,19695** | 2-4 |

- **Monoton in ALLEN drei Seeds** (9/9 Ordnungen korrekt), Endstaende
  zeigen dieselbe Ordnung.
- **Gepaart signifikant**: 202-810 in allen drei Seeds ausserhalb des
  95%-Partie-Bootstrap-KI (+0,0020..+0,0030); 405-810 dreimal positiv,
  einmal signifikant. PREREG-Leseregel "spielhungrig" ist mit 3/3 erfuellt.
- **Form: log-linear** -- jede VERDOPPLUNG bringt ~0,0012 Brier, kein
  Knick im gemessenen Bereich. Extrapolation (vorsichtig): auch jenseits
  von 8.100 Partien ist weiterer Gewinn zu erwarten.
- Nebenbefund: die Peak-Epoche wandert mit weniger Daten leicht nach
  hinten (405: E4-6) -- konsistent mit dem Erosions-/Memorisierungsbild.

**Konsequenzen**: (a) v20-Spielbudget NICHT kuerzen -- mehr Partien sind
der billigste Value-Hebel (Tiling-Cache-Ersparnis -20% direkt in Spiele
umsetzbar); (b) PCR-Bedingung (ii) ERFUELLT -> Durchsatz-Messung
(Bedingung iii) laeuft als naechstes end-to-end.

### PCR (Task #14): konditionale WIEDEREROEFFNUNG (Nutzer-Frage 2026-08-05)

Zwei unabhaengige Gruende, warum das geschlossene PCR neu zu bewerten ist:

1. **Das Verdikt fiel auf POLICY-Metriken.** Die Abbruchregel griff, weil
   beide Orakel-Metriken schlechter waren -- reine Policy-Masse. Die
   Value-Seite war bei pcr sogar BESSER (+0,04 `value_r2`), nur zu Recht
   nicht gewichtet, weil das Mass untauglich ist. Die eigentliche
   PCR-Wette ("mehr, aber schwaechere Value-Masse gegen weniger, aber
   verlaessliche Policy-Masse") wurde damit NIE mit einem gueltigen
   Value-Mass bewertet. Nach #34 gibt es eines (Brier), nach #36 wissen
   wir zusaetzlich, ob der Value-Kopf ueberhaupt spielhungrig ist.
2. **Der Tiling-Cache hat die OEKONOMIE verschoben** (seit 2026-08-05).
   PCR-mild scheiterte am Wandzeit-Kriterium (1,118x < 1,15x) -- gemessen,
   als der Tiling-Solver 30% der Zeit fraß. Jetzt sind es 4,8%, der
   Netz-Anteil stieg dadurch von ~60% auf **~81%** der Thread-Zeit.
   Sim-Reduktion hat entsprechend mehr Hebel: dieselbe 25%-Kuerzung
   spart rechnerisch ~20% statt ~11% (Faktor ~1,25x) -- ueber der
   Schwelle, an der PCR-mild scheiterte.

**Gegengewichte, ehrlich**: (a) die PCR-Doku-Arena war NEGATIV (67:83,
SPRT-H0) -- ein Arena-Ergebnis, kein Proxy, und damit das staerkste
Argument dagegen; allerdings mit Netzen auf dem ALTEN Value-Ziel.
(b) Die Oekonomie-Rechnung oben ist PROFIL-ARITHMETIK, keine Messung --
genau diese Sorte Rechnung lag am 2026-08-04 schon einmal daneben
(S/F-Herleitung 42/58, widerlegt durch direkte Messung). Der Durchsatz
ist end-to-end neu zu messen, nicht hochzurechnen.

**Bedingungen fuer eine Wiedereroeffnung** (alle drei, sonst bleibt zu):
(i) #34 abgeschlossen und der Value-Kopf auf Wahrscheinlichkeits-Ziel;
(ii) #36 zeigt, dass der Value-Kopf mit mehr Partien weiter besser wird
(saettigt er frueh, ist PCRs ganze Wette wertlos);
(iii) Durchsatz mit aktivem Tiling-Cache END-TO-END nachgemessen (nicht
aus dem Profil abgeleitet), Kriterium unveraendert >=1,15x.
Dann als NEUES Experiment mit neu trainierten Armen auf dem neuen Ziel --
keine Neulesung der alten Zahlen.

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

### Reihenfolge (bereinigt im Audit 2026-08-05)
#34 laeuft (mit #33 als integriertem Arm, siehe Korrektur C oben);
#35-Engine-Logging ist erledigt (Default AN); #35b-Training folgt nach
dem v20-Self-Play, wenn die Labels da sind.

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

## Task #38 (geparkt, Arbeitskreis "Spaeter" mit #31): Moon-Head-Feinschliff (2026-08-05)

Befund aus einer Interesse-Frage des Nutzers, Code verifiziert. Der Kopf
selbst ist solide (Plackett-Luce-Faktorisierung der Mond-Reihenfolge aus
dem Policy-Raum, Labels vom exakten Rundensolver, Prior-Aufteilung in der
Expansion). Zwei nie untersuchte Punkte fuer spaeter:
1. **Loss-Gewicht**: `moon_nll` wird mit VOLLEM Gewicht 1,0 in den
   Policy-Loss addiert (train.py, `p_loss + moon_nll[sun_mask].mean()`)
   -- bei NLL ~0,5-1 gegen Policy ~1,9 beansprucht ein Teilproblem, das
   nur Sonnenzuege betrifft, potenziell ~1/3 des Policy-Gradienten. Nie
   gesweept (VALUE_WEIGHT-Blindfleck-Muster). Als Arm in einen
   kuenftigen Loss-Gewichts-Sweep.
2. **Label-Horizont** (Nutzer-Einordnung 2026-08-05, RELATIVIERT):
   Referenz maximiert den RUNDENendstand (`solve_round_final_score`).
   Da die Fabriken zu Rundenbeginn NEU befuellt werden, ist der
   Wirkhorizont einer Reihenfolge im Wesentlichen die laufende Runde --
   das Solver-Label ist also naeher am Optimum als zunaechst vermutet,
   Restpunkt sind allenfalls Randeffekte. Falls Labels je aus der Suche
   kommen (root_child_q aus #35 liefert die Q-Ordnung der Varianten ab
   v20 gratis), waere das ein billiger A/B, kein Pflichtumbau.
Kein akuter Bedarf: Policy-Seite ist ueber die Orakel-Metriken
arena-validiert, inkl. PL-Aufteilung.

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
