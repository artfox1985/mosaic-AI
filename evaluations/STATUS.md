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
| **τ-Annealing (Messung 3)** | Arm-B-Training `t3ann_s2` LAEUFT (Swap-Fenster 200 raus/200 rein via Manifest+Exclude, Cache baut); danach Gating vs Champion -> Sockel-Entscheid. `PREREG_suchpfad_nachmessungen.md` |
| **v21-Fenster fuellen** | **ZURUECKGESTELLT (Nutzer 2026-08-08: "nicht so auf die self plays stuerzen")**: Generator-Frage geklaert (Champion bleibt), 2.090 Schwarm-Partien zurueck in data/; Generierung erst, wenn die offene Task-Liste abgearbeitet ist (und ohnehin nach τ- und #37-Verdikt). `PREREG_v21_fenster.md` |
| **Messset-Snapshot + v16/v17-Freigabe** | Snapshot ERLEDIGT 2026-08-07 abends (`altmess_90files/`, Tool-Flag `--snapshot-dir`, gegen Referenz validiert, Brier bitgenau reproduziert). v16/v17-Backup-Freigabe: NUR noch der τ-Arm-B-Cache-Bau steht davor |
| **Struktur-Watchlist** | wartet auf ~10-15 bewertete Nutzer-Partien vs v20 (Stand: 6); Abgleich gegen das Strategie-Dossier (history) |
| **#35b Ranking-Loss** | Implementierung beim Agent (--ranking-loss-weight, Default aus; ggf. Schema 19 fuer root_child_q-Cache-Feld); Trainings danach in die GPU-Queue (Seed-Varianz-Regel) |
| **λ (Value-Target-Mix)** | **AKTIVIERT (Nutzer-Anstoss 2026-08-08)**: v20/v21-Fenster hat ~95% root_q-Anteil, weit ueber den 66%, bei denen λ=0,7 GEWANN -> λ=0,7-Arm in die GPU-Queue hinter t3ann_s2 |
| **#29-Instrument (Offline-Value-Praediktor)** | OFFEN: braucht frozen-Set-Neubau + arena-differenzierte Paare zur Validierung. `PREREG_nach34_paket` |
| **#37 Tiling-Auswahlkriterium (punkte*P vs reines P)** | **VORGEZOGEN (Nutzer-Anstoss 2026-08-08): VOR die Schwarm-Fortsetzung** (Kriterium wirkt im Tiling jedes Self-Plays -> ganzer v21-Korpus soll das Sieger-Kriterium nutzen). Knopf beim Agent (MOSAIC_TILING_SELECT); danach Zwei-Arm-A/B (#30-Muster -- Solver ist prozessglobal, wirkt auf BEIDE Seiten) |
| **frozen-Set-Neubau** | **AKTIVIERT**: in die CPU-Queue nach dem Stark-Gegner-Nachtest und #37-A/B (Orakel-Labels CPU-schwer; Korpus-Generierung wartet ohnehin) -> danach #29-Validierung an den Aera-Gating-Paaren |
| #31 / #38 / #39 | geparkt (Arbeitskreis "Spaeter", Details unten) |

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

## GELTENDE REGELN (kompakt)

- **Champion**: `v20_2d_opp_brierbest` (Elo 1349, seit 2026-08-07).
  Generator-Naming: Dateien/Laeufe IMMER nach dem GENERATOR benennen;
  eine Ziel-Generation existiert erst mit trainiertem Modell.
- **Fenster-Pinning**: Trainings waehrend laufender Generierung IMMER
  mit `MOSAIC_DATA_EXCLUDE` pinnen (Split+Cache-Key haengen an der
  Dateiliste). Verifikation: "Lade HDF5-Cache"-Zeile.
- **Backup-/Alt-Regel-Korpora**: kommen NIE wieder ins Training.
- **Statistik**: (1) Score-Auswertungen IMMER auf Block-Ebene;
  (2) Netz-vs-Heuristik-Effekte <8pp = Seed-Rauschen; (3) SPRT-
  Fruehstopps <150 Paare zaehlen nur mit Frisch-Seed-Replikation.
- **Value-Aenderungen brauchen Arena-Gating** (kein validierter
  Offline-Praediktor, solange #29 offen/unvalidiert ist).
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
