# Mosaic-AI — Status & Fahrplan

**Hier steht nur AKTUELLES und OFFENES.** Alles Abgeschlossene liegt in
**`../archive/history.md`** (zuletzt ausgelagert 2026-08-06: die komplette
#34-Aera inkl. Audits, #36, Nach-#34-Paket, Regelbuch-Audit).

---

## TASK-INDEX (Stand 2026-08-06)

| Nr | Titel | Status | Details |
|---|---|---|---|
| — | **v20-KAMPAGNE (Zwei-Klassen, WDL-Generator)** | **BEREIT — Nutzer startet Self-Plays** | `PREREG_v20_kampagne.md` |
| #34 | Sieg/Niederlage-Ziel (WDL) | **ABGESCHLOSSEN**: Verdikt = WDL + entstauchter Blend + brierbest; Arena ziel-invariant (8 Gatings), Platt-B 0,97 | history |
| #36 | Saettigung ueber Spielzahl | **BEANTWORTET**: Value log-linear hungrig (~0,0012 Brier/Verdopplung), Policy im Warm-Start-Regime satt (flach ab <=2.020 Partien) | history |
| #14 | PCR | **AUFGEGANGEN in Design C**: alle 3 Wiedereroeffnungs-Bedingungen erfuellt (Durchsatz 1,37x), die Wette ist im Zwei-Klassen-Schwarm strukturell besser umgesetzt -- klassisches PCR-mild obsolet | history |
| #35 | root_child_q-Logging | Engine erledigt (Default AN); **#35b Ranking-Loss wartet auf v20-Sockel** (nur Voll-Partien nutzbar, Filter = policy_target_valid) | history |
| #37 | Tiling-Auswahlkriterium (`punkte*P` vs reines P) | vorgemerkt v20-Aera, Arena-entschieden | unten |
| — | R4b/Endspiel-Zone | **BEFUND**: beide Koepfe blind fuer exakte R4-End-Info (R²~0,004 bei Decke 0,967); Ursachenanalyse = v20-Aera-Kandidat, zusammen mit Wertungsplatten-Wiedervorlage (R5-Steigung 0,273) | history |
| — | #29-Instrument | Orakel-Referenzen neu nach frozen-Set-Neubau (v20-Aera); Validierung braucht arena-differenzierte Paare | PREREG_nach34_paket |
| — | Aggressions-Neukartierung | v20-Aera, nach Gating (F1-gefixte Engine); Blend bis dahin UEBERALL 0 | history |
| — | λ (Value-Target-Mix) | vertagt: am echten v20-Mischanteil neu bewerten | history |
| — | U1 Chip-Sperre Apply-Ebene | offen, klein (defensiv, kein Regel-Bug) | history (Engine-Audit) |
| #31 | Schwierigkeitsstufen | geparkt (Arbeitskreis "Spaeter") | unten |
| #38 | Moon-Head-Feinschliff | geparkt (Arbeitskreis "Spaeter") | unten |
| #9 #12 #27 #28 #29 #30 | Aux-/Kalibrier-Serie | alle geschlossen (Details history) | history |

## NAECHSTE SCHRITTE (v20-Pipeline)

1. **Nutzer**: Sockel-Self-Play (4.000 @600, `--version v20wdl`), danach
   Schwarm (8.000 @150, `--version v20wdlsw --value-only`). Kommandos in
   PREREG_v20_kampagne.md.
2. Cache-Neubau Schema 17 (~1h, automatisch beim ersten Training).
3. Training warm von `v19_2d_opp_best` (Rezept siehe PREREG).
4. Champion-Gating vs `v19_2d_best` (Fruehstopp-Regel beachten!),
   Policy-Wacht (Orakel-Metriken vs v19), Saettigungs-Nachfit
   (4. Stuetzpunkt), Pflicht-Diagnostiken (Platt, R5, R4b).
5. Danach eigene Schritte: frozen-Set-Neubau -> #29-Instrument;
   Aggressions-Neukartierung; #37; λ.

## OFFENE ENTSCHEIDUNGEN & GELTENDE REGELN

- **Champion**: `v19_2d_best` bleibt (Nutzer 2026-08-04). Der opp-Kopf
  kommt ueber `v20_2d_opp` in die Linie; v20 warm von
  `v19_2d_opp_best` starten (Kopf bereits trainiert).
- **v20-KAMPAGNEN-DESIGN, drei Optionen (Stand 2026-08-06, Nutzer-Entscheid
  offen)** -- Grundlage: #36-Schere (Policy im Warm-Start-Regime satt,
  Value log-linear hungrig) + Durchsatz 1,37x + Nutzer-Schluss "wenn die
  Policy satt ist, kommt sie mit weniger Policy-Traeger-Partien aus":
  - **A Standard**: 6000+ Partien @600, alles wie gehabt (+20% mehr
    Partien durch Tiling-Cache).
  - **B PCR-mild**: +37% Partien, aber schwaechere Policy-Labels auf der
    Haelfte der Zuege JEDER Partie (Juli-Schwachstelle).
  - **C ZWEI-KLASSEN (Nutzer-Idee 2026-08-06, praeferierter Kandidat)**:
    Sockel voller Partien @600 (Policy-Traeger) + Schwarm reiner
    VALUE-Partien @~150 Sims (~2,5x billiger; `policy_target_valid=false`
    -> pol_w=0, Infrastruktur existiert aus PCR-Bau). Value-Label-Verlust
    minimal: Ziel = bootstrap (netz-, nicht sims-abhaengig) + Ausgang;
    root_q ungenutzt. Vorteil vs B: Policy-Labels des Sockels UNBERUEHRT.
    **Fenster-Zuschnitt (Nutzer 2026-08-06)**: Sockel 4000 @600 (Policy
    aktiv) + Schwarm 8000 @~150 (Policy maskiert) vom v20-Generator;
    Alt-Einfluss: 1350 v18- + 450 v17-Partien als Policy-Traeger
    (Summe 5800 Policy-aktiv), restliche ~7200 v18/v17/v16-Partien als
    reines Value-Material -> ~21.000 Value-Partien gesamt. Nachschub-
    Ventil: bei Gating-Fehlschlag weitere Policy-Partien nachwerfen.
    **Backup-Altbestaende bleiben AUSSEN (Nutzer-Entscheid): ihre
    Verlaeufe tragen die alte Policy** -- Value-Kalibrierung soll auf
    der Zustandsverteilung des aktuellen Spiels stehen (deckt sich mit
    "Alt-Regel-Korpora nie wieder" von 2026-07-21).
    OFFEN: Generator-Wahl (v19_2d_best/tanh = Entstauchung global
    weiter, vs t34_wdldestretch_brierbest/WDL = saubere Bootstraps ab
    sofort + aera-gesteuerte Entstauchung noetig); PREREG vor Start.
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
- **Statistik-Regeln**: (1) Score-basierte Arena-Auswertungen IMMER auf
  Block-Ebene (Paar-SEs unterschaetzen massiv); Win-SPRT milder betroffen,
  Block-Zahlen trotzdem mitberichten. (2) Netz-vs-Heuristik: Effekte <8pp
  liegen im Seed-Satz-Rauschen. (3) **SPRT-Fruehstopps unter ~150 Paaren
  zaehlen NICHT ohne Frisch-Seed-Replikation** (t12-Falsch-Positiv
  2026-08-06: H1 bei n=80, Replikation ueber 400 Partien = Paritaet).
- **Kein validierter Offline-Praediktor fuer die Value-Seite** (#29
  gescheitert, value_r2 viermal widerlegt) -> jede Value-Aenderung
  braucht ein Arena-Gating. **Nach #34 neu zu pruefen** (siehe unten).

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

**POLICY-GEGENKURVE (PREREG-Sekundaermessung, 2026-08-06)**: dieselben 9
Arme, Orakel-Metriken auf dem frozen-Set: prior_mass 0,7240/0,7250/0,7247,
kendall_tau 0,363/0,361/0,366 -- **FLACH ueber 202->810, beide Metriken,
kein Trend**. Im Warm-Start-Regime ist die Policy also DATEN-GESAETTIGT,
waehrend der Value-Kopf log-linear gewinnt -- die theoretisch erwartete
Schere (145 Ziele/Partie vs 1 Bit/Partie) ist damit direkt gemessen.
Abgrenzung: die Korpus-Dosis-Studie (6/6 Policy-Gewinne 450->900) lief im
From-Scratch-aehnlichen Rezept (lr 4e-4/40 Epochen) -- anderes Regime,
kein Widerspruch. **Games/Sims-Bild fuer v20 damit komplett: die
Spielzahl wird allein vom VALUE-Kopf getrieben; Policy-seitig gibt es im
Warm-Start-Regime keinen Grund gegen mehr Partien und keinen Bedarf nach
mehr.**

**Konsequenzen**: (a) v20-Spielbudget NICHT kuerzen -- mehr Partien sind
der billigste Value-Hebel (Tiling-Cache-Ersparnis -20% direkt in Spiele
umsetzbar); (b) PCR-Bedingung (ii) ERFUELLT -> Durchsatz-Messung
(Bedingung iii) laeuft als naechstes end-to-end.

### Nach-#34-Paket ERGEBNISSE (2026-08-06, PREREG_nach34_paket.md)

Beide Arme offline: t9_own deckungsgleich mit Referenz (0,1970/0,2018);
t12_dist Peak 0,1979, staerkere Erosion (0,2108), Punkte-R² FAELLT
(0,48 vs 0,56 Skalar). Arena (brierbest vs brierbest, je + Champion):

| Gating | Ergebnis | p |
|---|---|---|
| **t12_dist vs t34_wdldestretch** | **54:26 (67,5%) -- SPRT-H1!** | **0,0066** |
| t12_dist vs v19_2d_best | 33:47 (41,3%), H0 | 0,19 |
| t9_own vs t34_wdldestretch | 197:193 (50,5%), H0 | 0,91 |
| t9_own vs v19_2d_best | 145:145 (50,0%), H0 | 1,00 |

- **#9 ERNEUT GESCHLOSSEN** (vorregistrierte Regel): perfekte Paritaet
  ueber 390+290 Partien -- das Arena-Instrument war da, der Effekt nicht.
- **#12: erster SPRT-H1 der gesamten WDL-Aera** -- und zugleich ein
  WIDERSPRUCH: schlaegt die Referenz klar, verliert (n.s.) gegen den
  Champion, waehrend die Referenz dort Paritaet spielte. Moegliche
  Deutungen: Nicht-Transitivitaet (Stilpaarung), Seed-Satz-Rauschen im
  80-Paare-Champion-Lauf, oder echter Effekt nur gegen WDL-Familie.
  **Frisch-Seed-Replikation (Ergebnis)**: vs Referenz 206:194 ueber
  VOLLE 400 Partien (51,5%, p=0,60), vs Champion 181:179 (50,3%, p=1,0)
  -- BEIDE Erstlauf-Extreme waren Seed-Satz-Rauschen, die Wahrheit ist
  beidseitige Paritaet. Der SPRT-H1 bei n=80 war ein Falsch-Positiv des
  fruehen Stopps (alpha-Fehler); die Replikationsregel hat ihn gefangen.
  **#12 ERNEUT GESCHLOSSEN** per PREREG ("keine Uebernahme ohne
  repliziertes klares Bild + intakten Brier" -- beides verfehlt:
  Paritaet statt Effekt, Erosion 0,2108 + Punkte-R²-Verlust).
  METHODEN-LEHRE (dritter Beleg): SPRT-Fruehstopps bei n<=80 sind bei
  unserer Effektlage anfaellig -- Einzel-H1 ohne Replikation zaehlt
  nicht als Uebernahme-Beleg.
- #29: Instrument-Teil wartet auf frozen-Set-Neubau (siehe PREREG).
- **Paket-Fazit**: #9 zu, #12 zu, #29 vertagt -- das Nach-#34-Paket ist
  ABGESCHLOSSEN. Kein Aux-Kopf-Hebel traegt am neuen Ziel; die
  belegten Hebel bleiben Spielzahl (#36) und die v20-Kampagne selbst.

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

**DURCHSATZ-MESSUNG (Bedingung iii, 2026-08-06)**: end-to-end, je 30
Partien, Champion@600, 11 Threads, Tiling-Cache an: Standard 233s vs
PCR-mild (0,5/300) 170s -> **1,371x**, klar ueber der 1,15x-Schwelle
(Messpartien sofort aus data/ geloescht). **#14 ist damit formal
WIEDEREROEFFNET** -- alle drei Bedingungen erfuellt. WICHTIG:
Wiedereroeffnung heisst NICHT Uebernahme. Die neue PCR-Wette lautet
jetzt praezise: +37% Partien (pro #36: log-linear ~+0,0005 Brier)
GEGEN schwaechere Policy-Ziele auf der Haelfte der Zuege (woran PCR im
Juli auf den Policy-Metriken scheiterte) -- und die Doku-Arena war
damals NEGATIV. Der Entscheid, ob v20 (oder eine Teilkampagne) PCR-mild
faehrt, ist ein v20-Design-Entscheid des Nutzers; PREREG dann als neues
Experiment auf dem neuen Ziel, keine Neulesung alter Zahlen.

---
## Architektur, Stand jetzt (aktualisiert 2026-08-06)

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
- **Value-ZIEL (#34-Verdikt, Schema 17)**: `values_wdl` = TD-Blend aus
  Bootstrap-Gewinnwahrscheinlichkeit und hartem Ausgang; Alt-Datei-
  Bootstraps werden beim Cache-Bau Platt-entstaucht (A=0,0051/B=1,9269),
  `selfplay_v20wdl*`-Bootstraps (WDL-Generator) bleiben roh. Training:
  `--value-head wdl --select-by-brier` (KEIN destretch-Flag mehr noetig).
  Policy-Traeger-Manifest `data/policy_carrier_manifest_v20.json`
  maskiert Alt-Dateien ausser 135 v18 + 45 v17 (im Cache-Key).
  Checkpoints: `_best` (val_combined), `_brierbest` (Value-Peak).
- Champion: `models/champion.txt` -> `v19_2d_best`.

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
