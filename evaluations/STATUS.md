# Mosaic-AI — Status & Fahrplan

**Hier steht nur AKTUELLES und OFFENES.** Alles Abgeschlossene liegt in
**`../archive/history.md`** (zuletzt ausgelagert 2026-08-07 abends:
Mensch-vs-KI-Befund, Suchpfad-Inventar, #37-Volltext; #14
geschlossen).

---

## TASK-INDEX (nur OFFEN/LAUFEND, Stand 2026-08-07 abends)

| Task | Status |
|---|---|
| **Platten-Intervention (endgame_head)** | **ABGESCHLOSSEN 2026-08-08: Arena H0 (97:103), Offline-Gewinne real (R5 0,457, Brier -0,0016) -> `--endgame-head` wird Standard-Rezept der naechsten Generation**; Champion bleibt. `PREREG_platten_intervention.md` |
| **τ-Annealing (Messung 3)** | **GESCHLOSSEN 2026-08-08: H0 (112:118, p=0,78) -> τ=1 bleibt, v21-Sockel OHNE Annealing.** Suchpfad-Prereg M1-3 damit KOMPLETT (3x Status quo re-validiert). `PREREG_suchpfad_nachmessungen.md` |
| **v21-Fenster fuellen** | **ZURUECKGESTELLT (Nutzer 2026-08-08: "nicht so auf die self plays stuerzen")**: Generator-Frage geklaert (Champion bleibt), 2.090 Schwarm-Partien zurueck in data/; Generierung erst, wenn die offene Task-Liste abgearbeitet ist (und ohnehin nach τ- und #37-Verdikt). `PREREG_v21_fenster.md` |
| **Messset-Snapshot + v16/v17-Freigabe** | Snapshot ERLEDIGT 2026-08-07 abends (`data/altmess_90files/`, Tool-Flag `--snapshot-dir`, gegen Referenz validiert, Brier bitgenau reproduziert). v16/v17-Backup-Freigabe: NUR noch der τ-Arm-B-Cache-Bau steht davor |
| **Struktur-Watchlist** | wartet auf ~10-15 bewertete Nutzer-Partien vs v20 (Stand: 6); Abgleich gegen das Strategie-Dossier (history) |
| **#35b Ranking-Loss** | **GESCHLOSSEN 2026-08-08**: Loss arbeitet (Val-Ranking-Acc 0,740, Policy-Val 0,47 < 0,49), aber Orakel-Vorpruefung NEGATIV (Top-3-Masse 0,688 vs 0,710) -> per Prereg kein Gating. Lehrsatz: verbessert die NICHT-validierte Metrik, verschlechtert die validierte. `PREREG_t35b_ranking.md` |
| **λ (Value-Target-Mix)** | **UMGESTUFT (Nutzer 2026-08-08, 2. Korrektur): KEIN Replikationskandidat** -- der λ=0,7-Sieg stammt aus der tanh-/Margen-Aera, der Mechanismus uebertraegt sich nicht auf den binaeren WDL-Kopf (Aera-Grenzen-Lektion). Bleibt als NEUES WDL-Aera-Experiment auf Hypothesen-Niveau in der GPU-Queue (root_q ist jetzt immerhin skalengleich zum Ziel); eigenes Prereg mit offener Erwartung vor dem Start, Prioritaet hinter t3ann/#35b -- oder Streichung auf Zuruf |
| **#29-Instrument (Offline-Value-Praediktor)** | OFFEN: braucht frozen-Set-Neubau + arena-differenzierte Paare zur Validierung. `PREREG_nach34_paket` |
| **#37 Tiling-Auswahlkriterium** | **GESCHLOSSEN 2026-08-08: H0 (284 vs 292, p=0,33)** -- Bestand punkte*P bestaetigt, Knopf MOSAIC_TILING_SELECT bleibt inert. `PREREG_t37_tiling_kriterium.md` |
| **frozen-Set-Neubau** | **ERLEDIGT 2026-08-08**: `frozen_eval_set_v2.pkl` (1.800 Zustaende, 4 Aera-Korpora, 0 Duplikate, v1 hash-unveraendert) + `frozen_v2_oracle_labels.json` (1.148 Labels, Orakel = Champion, 0 Fehler) |
| **#29-Instrument** | **WARTET AUF POWER**: Validierung braucht arena-ENTSCHIEDENE Paare; die WDL-Aera hat bisher nur ~3 (v20>v19, E3-Arme signifikant schlechter) -- unter dem 6-Paar-Standard der Policy-Orakel-Validierung. Kandidaten-Metriken (Brier auf frozen_v2, R5-Steigung) werden ab jetzt je Gating MITGEFUEHRT; Verdikt, sobald >=6 entschiedene Paare vorliegen |
| #31 / #38 / #39 | geparkt (Arbeitskreis "Spaeter", Details unten) |

**UEBERGABE-DOKUMENT (2026-08-08): `evaluations/UEBERGABE_v21_spirale.md`** -- vollstaendige Kommandos + Regeln fuer die v21-Spirale, geschrieben fuer den naechsten Koordinator; dort zuerst lesen.

## NAECHSTE SCHRITTE (Reihenfolge-Regel: Modell-Verdikte VOR Korpus-Generierung)

1. **Heute Nacht (automatisch)**: `pi_endgame_s2` fertig -> Verdikt
   (R5-Steigung/Brier) -> bei Bestehen Gating vs `v20_2d_opp_brierbest`
   (Fruehstopp-Regel).
2. **Danach GPU**: τ-Arm-B-Training (v20-Fenster, 2.000 Sockel-Partien
   seed-bestimmt gegen `v19wdlann` getauscht; MOSAIC_DATA_EXCLUDE-
   Pinning!) -> Gating -> τ-Verdikt fuer den Sockel.
3. **Dann CPU**: v20-Schwarm fortsetzen/neu (Generator = finaler
   v20-Aera-Champion; Quarantaene-Entscheid beim Nutzer, falls
   Champion wechselt) -> v20-Sockel gemaess τ-Verdikt.
4. ~~Kleinkram~~ ERLEDIGT 2026-08-07 abends: Messset-Snapshot (s.o.)
   + **R5-Steigungs-Seed-Skala: s2 0,349 vs s3 0,295 -> ~0,05**
   (r5_value_calibration_pi_ctrl.json). Lesart fuers Endgame-Verdikt:
   ±0,05 um 0,349 = Seed-Klasse; die 0,5-Schwelle liegt ~3
   Seed-Sigma darueber.

### v22-FENSTER -- DESIGN AUF HALDE, NICHT EINGEPLANT
**Nutzer-Entscheid 2026-08-08: keine v22-Self-Plays; erst die
v21-Task-Queue abarbeiten.** Der Zuschnitt ist nur festgehalten, damit
er spaeter nicht neu diskutiert werden muss.

`PREREG_v22_fenster.md`: gleiche Form wie v21 (5.800 Policy / 23.650
Value / 29.450 gesamt), alles altert eine Stufe. Juengster Value-Posten
= **3.550 v19wdl-Rest (@600, vollstaendig) + 1.450 v19wdlsw** statt
5.000 Schwarm -> Schwarm-Anteil bleibt bei 74% statt auf 89% zu
steigen. **Ab v22 ist die Rotationsregel stationaer** (v21 war die
letzte Uebergangsgeneration). Vorbehalt fuer v21-Gating-H0: neuer
Batch desselben Generators braucht ein Suffix (`v20wdlb`).

### OFFENES GATING (v20-Aera, hat Vorrang)

**λ-Arm `lam07_wdl2_s2`**: trainiert, gueltig (Zielfeld `values_wdl`
verifiziert), **Gating steht aus** -- Slot = v21-Trainingsfenster (GPU
belegt, CPU frei). Kommando + Regeln: UEBERGABE §5a,
`PREREG_lambda_wdl_arm.md`. Offline: Brier-Paritaet, aber Platt-B
0,9966 (Champion 0,930).

### AUS EXTERNEM REVIEW 2026-08-08 (`EXTERNES_REVIEW_2026-08-08.md`)

| Task | Kurz |
|---|---|
| **A: Floor-Shaping W=0 vs 0,3** | die nie gefahrene Kontrolle des WDL-Sweeps; der +14pp-Beleg ist Alt-Aera -> H0 wuerde eine Handheuristik ersatzlos streichen. 2x400 |
| **D: GEWICHTS-SWEEP (erweitert)** | Loss-Anteile gemessen: Policy 90,1%, **Value nur 6,5%** -- obwohl die Hybrid-Attribution die Staerke dem VALUE-Kopf zuschreibt; VALUE_WEIGHT=0,2 stammt aus der MSE-Aera und wurde beim BCE-Wechsel nie nachgezogen, nach OBEN ist ungemessen. 4 Arme: Kontrolle, vw04, vw08, pw025. **ARENA entscheidet** (Nutzer: Gating ~1,5h CPU < Training ~3,5h GPU und das einzige validierte Instrument): je Arm Gating vs Kontrolle `v21_2d`, Sieger zusaetzlich vs Champion; Brier/Orakel nur deskriptiv -- liefert zugleich die #29 fehlenden entschiedenen Paare |
| **B: Zerlegungs-Diagnose** | zweistufige (Slot,Rotation)-Wahl vs flache Enumeration auf Frozen-Zustaenden; billig, KEINE Arena. Praemisse "PUCT verzerrt" trifft nicht (Gumbel), Kern aber ungemessen |
| ~~C: c_visit-Sweep~~ | **ZURUECKGEZOGEN**: `PREREG_ownership_gumbel.md` B1 hat die sigma-Familie regelkonform geschlossen, nachdem c_scale sich als folgenlos erwies (Task #18) -- ein Sweep waere ein Test gegen die eigene Vorregistrierung |

Abgelehnt/erledigt aus dem Review: Solver-Aux-Loss (Punkt 1) ist bereits
zweifach umgesetzt (R4-Bootstrap + endgame_margin-Kopf); faktorierte
Policy erst nach Task B; tau-Wiederaufnahme ohne neuen Mechanismus nein.

### NACH-v21-QUEUE (Nutzer-Go 2026-08-08)

1. **E3b** (Denial-Tie-Break mit Besuchs-Gate + Zwei-Anteils-SE statt
   roher Q-Differenz): Stufe 1 = Feuerraten-Messung, Abbruch bei <5%;
   Stufe 2 = 2x400 Arena. `PREREG_denial_tiebreak.md`
2. **ISMCTS-k** (Mehrfach-Determinisierung, k=1/2/4, rechen-neutral --
   Sims-Split; greift die PIMC-Strategy-Fusion an):
   `PREREG_ismcts_determinisierungen.md`
Knoepfe (MOSAIC_DENIAL_UNCERT_Z / _MIN_VISIT_FRAC /
MOSAIC_NUM_DETERMINIZATIONS) werden vorab gebaut, Default aus.

## GELTENDE REGELN (kompakt)

- **Champion**: `v21_2d_brierbest` seit 2026-08-09, **Elo 1416**
  [1325, 1510] (Vorgaenger `v20_2d_opp_brierbest` 1336). Gating 75:45
  (SPRT-H1 nach 60 Paaren, p=0,0059) UND Frisch-Seed-Replikation 97:63
  (H1 nach 80 Paaren, p=0,0095) -- die Fruehstopp-Regel ist damit
  erfuellt. Alt-Messset-Brier 0,18636 vs 0,18749. **Erster Champion aus
  reiner Korpus-Skalierung**: identisches Rezept, +40% Fenster
  (29.450 Partien) von einem staerkeren Generator, plus
  `--endgame-head`. champion.txt gesetzt (wirkt nach Server-Neustart).
  Generator-Naming: Dateien/Laeufe IMMER nach dem GENERATOR benennen;
  eine Ziel-Generation existiert erst mit trainiertem Modell.
- **Fenster-Pinning**: Trainings waehrend laufender Generierung IMMER
  mit `MOSAIC_DATA_EXCLUDE` pinnen (Split+Cache-Key haengen an der
  Dateiliste). Verifikation: "Lade HDF5-Cache"-Zeile.
- **Backup-/Alt-Regel-Korpora**: kommen NIE wieder ins Training.
- **PROMOTIONS-CHECKLISTE (Nutzer-Hinweis 2026-08-09: die Kader-Praxis
  wurde bis dato nicht konsequent umgesetzt)** -- bei JEDEM
  Champion-Wechsel vollstaendig abarbeiten, nicht aus dem Gedaechtnis:
  1. `tools/set_champion.py <neu>` (Server-Default, wirkt nach Neustart).
  2. Elo-Kante **Gating** (Champion-1) -- inkl. Replikations-Zeile, falls
     Fruehstopp <150 Paare.
  3. Elo-Kante **Anker**: `Heuristik@150(dyn)`, **festes n=150 ohne
     Fruehstopp** (Praezedenz v18/v19/v20-Verankerung).
  4. Elo-Kante **Champion-2** (der Vorvorgaenger, @400) -- **das ist der
     Punkt, der bei v20 UND v21 zunaechst fehlte**; ohne ihn ruht die
     Elo-Schaetzung auf zu wenigen Kanten (v21 nach dem Gating:
     CI +-90 Punkte).
  5. Pflicht-Diagnostiken am Sieger (Platt, R5, Alt-Set-Brier, R4b) +
     Eintrag in die #29-Buchfuehrung.
  6. STATUS-Champion-Zeile + history-Kapitel.
  Nachtrag-Schuld: v20 fehlt die Kante zu `v19_best` (Champion-2 seiner
  Generation) -- billig nachholbar, Nutzer-Entscheid.
- **LOESCHEN NUR MIT EXPLIZITER RUECKFRAGE (Nutzer-Regel 2026-08-08,
  dritter Vorfall dieser Klasse -- "inakzeptabel")**: Kein Loeschen,
  Verschieben oder Ueberschreiben von Dateien, Ordnern oder Worktrees
  ohne vorherige, den KONKRETEN Pfad benennende Nutzer-Freigabe.
  Ausnahme: das eigene Scratch-Verzeichnis.
  Im Einzelnen:
  1. **Eine FRAGE ist keine Anweisung.** "Ist X noch aktuell?", "kann
     man X weg?", "brauchen wir X?" verlangen eine ANTWORT. Handeln
     erst nach einem Imperativ, der das Ziel nennt.
  2. Als Loeschen gelten auch: `git worktree remove`, `git checkout --`,
     `git reset --hard`, `git clean -fd`, `mv` aus dem Projekt heraus,
     `rm` auf generierte Artefakte (Caches sind KEINE Ausnahme -- die
     Freigabe vom 2026-08-08 galt fuer sechs namentlich genannte Dateien).
  3. Vor jeder freigegebenen Loeschung: Ziel ANSEHEN (Inhalt, Groesse,
     Reparse-Points bei Worktrees -- Junction-Vorfall 2026-07-24), das
     Ergebnis der Pruefung BERICHTEN, und nur dann ausfuehren.
  4. Gilt fuer Sub-Agents identisch und steht in jedem Agent-Prompt.
  5. "Aufraeumen" ist niemals selbst-autorisiert -- auch dann nicht,
     wenn etwas offensichtlich veraltet ist.
- **Statistik**: (1) Score-Auswertungen IMMER auf Block-Ebene;
  (2) Netz-vs-Heuristik-Effekte <8pp = Seed-Rauschen; (3) SPRT-
  Fruehstopps <150 Paare zaehlen nur mit Frisch-Seed-Replikation.
- **Value-Aenderungen brauchen Arena-Gating** (kein validierter
  Offline-Praediktor, solange #29 offen/unvalidiert ist).
- **AUFLOESUNG SCHLAEGT SPARSAMKEIT (Nutzer-Regel 2026-08-08)**: Wenn
  eine Entscheidung an einer Differenz haengt, die UNTERHALB der
  Auflösung des Offline-Instruments liegt (Value-Seite: Brier-Gaps
  <0,015 sagten 0/4 die Arena voraus; gemessene Seed-Skala ~0,0006),
  dann darf das Offline-Mass die Entscheidung NICHT tragen -- auch nicht
  als Spar-Vorfilter ("nur gaten, wenn Brier X schlaegt"). Stattdessen
  die ARENA in die Abwaegung nehmen und die Kosten AUSRECHNEN, nicht
  schaetzen: ein Gating (~1-1,5h CPU, 200 Paare @400) ist regelmaessig
  BILLIGER als das Training, das man sich mit dem Vorfilter sparen
  wollte (~3,5h GPU) -- und es ist das einzige validierte Instrument.
  Wer auf einem blinden Mass spart, spart die billige Ressource und
  riskiert die teure Fehlentscheidung.
  **Ausnahme Policy-Seite**: die Orakel-Metriken (Prior-Masse Top-3,
  Kendall-Tau) sind arena-validiert (7/7) und DUERFEN als Vorfilter
  dienen -- so entschieden bei #35b (beide Metriken schlechter -> kein
  Gating). Der Unterschied ist der Validierungsstand, nicht die
  Bequemlichkeit.
  Zusatznutzen, den man mitnehmen soll: jedes gefahrene Gating liefert
  ein arena-ENTSCHIEDENES Paar -- die Waehrung, in der #29 (Validierung
  eines Offline-Value-Praediktors) bezahlt wird (Stand ~3, noetig >=6).
- **Aggressions-/Denial-Programm GESCHLOSSEN** (2026-08-07): alle
  Knoepfe auf Default (w=0, λ=0, ε=0, bias=1); "gate what you ship";
  Wiedervorlage nur mit messbar schaerferem opp-Kopf
  (PREREG_aggression_stilmessung/PREREG_denial_tiebreak).
- **Heuristik-Anker-Parameterpaket: NICHT ANFASSEN** (definiert den
  Elo-Anker@200; jede Aenderung entwertet die Leiter).
- **Elo-Betrugsschutz (GUI)**: gewertete Spiele nur gegen verankerte
  Konfigurationen (`is_estimate=False`); Abbruch-Verhalten bleibt
  (Nutzer-Entscheid). **Tiling-Cache** Default AN
  (`MOSAIC_TILING_CACHE=0` schaltet ab).
- **Checkpoint-Politik**: brierbest (arena-re-validiert 2026-08-07,
  E15-Alt-Set-Vorsprung uebersetzt nicht in Staerke).

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
  `selfplay_v19wdl*`-Bootstraps (WDL-Generator) bleiben roh. Training:
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

## Task #39 (geparkt, Arbeitskreis "Spaeter" mit #31/#38): Startkuppel-Platzierung (2026-08-06)

Nutzer-Beobachtung "setzt sie gefuehlt immer an dieselbe Position" --
am Code bestaetigt und MECHANISCH erklaert
(`self_play.rs::choose_start_placement`): der Farb-Score ist
POSITIONS-unabhaengig (summiert nur Fabrik-Farbhaeufigkeiten je Feld),
der Eckbonus fuer alle 4 Ecken identisch (0,5), Ties behaelt der erste
Kandidat -> IMMER Ecke (0,0); die Feld-Summe ist zudem
ROTATIONS-invariant -> immer 0 Grad. Position/Rotation sind tote
Freiheitsgrade; nur die Platten-WAHL variiert. Gilt ueberall (GUI,
Arena, Self-Play; Startplatzierung ist policy-maskiert, das Netz lernt
sie nie).

**Nutzer-Einordnung (2026-08-06, schaerft den Zuschnitt)**: die Ecke an
sich ist strategisch RICHTIG (Rand/Diagonale/Eckplatten honorieren sie
alle) -- das Problem ist die MONOTONIE, nicht die Position.
**KORREKTUR (Nutzer 2026-08-06, zweite Runde)**: auch der Ecken-Rang
(3 oben / 8 unten) ist KEIN Bewertungsfehler -- Kuppelzeile 0 wird von
den SCHNELLSTEN Musterreihen (1-2, Kapazitaet 1-2 Steine) gespeist: die
obere Ecke kommt frueher in Wertung + Orthogonal-Bonus und wird
zuverlaessiger ueberhaupt komplett; die 8 Punkte unten haengen an den
traegsten Reihen (5-6). Der (0,0)-Tie-Break loest den Trade-off implizit
RICHTIG auf. Verbleibende Substanz von #39:
(1) ROTATION -- bestimmt Farb-Ausrichtung zur Brettmitte und
Sonderfeld-Lage, heute verschenkt (Score rotationsinvariant);
(2) MONOTONIE/Tie-Break -- Diversitaets-Frage (GUI-Abwechslung +
Korpus-Vielfalt), keine Staerke-Frage.
**Verbesserungs-Optionen (bei Angehen abzuwaegen)**:
a) Heuristik-Upgrade: Rotations-Bewertung + randomisierter Tie-Break
   unter nahezu gleichwertigen Kandidaten; jede Aenderung per Arena
   gegen den Bestand pruefen (die Strategie-Intuition des Koordinators
   lag hier zweimal daneben, die des Nutzers zweimal richtig).
b) Prinzipiell: Platzierung in den Aktionsraum der Suche -- ACHTUNG
   NUM_ACTIONS-Aenderung macht alte Checkpoints unbrauchbar
   ([[num-actions-change-breaks-old-checkpoints]]), teuer.
**Randbedingung**: NICHT waehrend einer laufenden Kampagne aendern
(verschiebt die Self-Play-Zustandsverteilung); fruehestens v21-Setup.
Nebenaspekt: die heutige Uniformitaet kostet auch Zustands-Diversitaet
im Korpus.

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
