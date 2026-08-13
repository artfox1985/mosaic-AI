# Registratur der `#NN`-Task-Nummern

**Zweck**: Das Projekt hat seit Juli 2026 Kennungen der Form `Task #29`,
`#35b`, `#84` usw. vergeben, ohne dass je eine zentrale Registratur
existierte. Die Nummern leben verstreut in `archive/history.md`,
`evaluations/PREREG_*.md`, `evaluations/STATUS.md`, Code-Kommentaren
(`engine/src/*.rs`, `engine/py/neural_net.py`, `train.py`, `self_play.py`,
`server.py`) und `tools/*.py`. Niemand konnte bisher pruefen, welche
Nummer vergeben ist, ob eine doppelt belegt wurde, oder was inhaltlich
hinter einer Nummer steckt. Diese Datei macht den IST-STAND nachvollziehbar
-- sie nummeriert nichts um, sie korrigiert nichts, sie ist reine
Bestandsaufnahme.

**Entstehungsdatum**: 2026-08-09.

**HEAD-Commit, auf dem diese Registratur erstellt wurde**: `3c11ac9`
(`3c11ac9cc629f1e369746a2780fc1d25bef42786`). Zum Zeitpunkt der Erstellung
waren `archive/history.md` und `evaluations/STATUS.md` als lokal
modifiziert markiert (ein anderer Agent lagert parallel Abschnitte aus
STATUS.md nach history.md aus) -- diese beiden Dateien wurden **nur
gelesen**, nie geschrieben. Zeilenangaben unten sind daher **Anhaltspunkte
auf dem genannten Commit-Stand**, keine exakten Koordinaten fuer den
aktuellen Arbeitsstand dieser Dateien.

**Namenskonvention-Hinweis (verbindlich seit 2026-08-09,
`evaluations/PREREG_INDEX.md` Abschnitt "NAMENSKONVENTION")**: Die
`#NN`-Serie ist seit diesem Datum eine reine RUECKWAERTS-Referenz auf
Alt-Befunde. **Es werden keine neuen `#NN` mehr vergeben.** Neue
Entscheidungseinheiten bekommen eine eigene `PREREG_*.md`-Datei als
Kennung (Datei-Slug statt Nummer/Buchstabe). Diese Registratur dokumentiert
ausschliesslich den Alt-Bestand.

## Filter-Verfahren

Durchsucht wurden mit dem Muster `#[0-9]+[a-zA-Z]?`: `archive/history.md`,
`evaluations/*.md`, `docs/*.md`, `README.md`, `CLAUDE.md`,
`engine/src/*.rs`, `engine/py/neural_net.py`, `train.py`, `self_play.py`,
`server.py`, `tools/*.py`. Die Rohtreffer (77 unterschiedliche
Zeichenketten) wurden von Hand nach Kontext sortiert:

**Aufgenommen** als echte Task-Nummer nur, wenn der Kontext eindeutig auf
eine Aufgaben-/Experiment-Kennung deutet (`Task #NN`, `Task-#NN`, `(#NN)`
unmittelbar nach einer Massnahmen-/Befund-Beschreibung, oder ein
Abschnitts-Header `## Task #NN: ...`).

**Verworfen** als Fehltreffer (mit Beleg, warum):
- `#0`, `#1`, `#9` in `evaluations/reference_game.md:11` ("Kuppelplatten
  im Display: #9, #0, #1") -- physische Spielplatten-IDs in einem
  Partie-Log, keine Task-Bezuege.
- `#5`, `#6`, `#10` in `evaluations/watchlist_v20_interim_review.md:91`
  ("...in 3 von 10 Partien aktiv (#5, #6, #10)") -- Partienummern
  innerhalb eines 10er-Testsets, keine Tasks.
- `#1`, `#2` in `engine/src/net_mcts.rs:4707-4708` (Testkommentare
  "unbesucht #1"/"#2") -- Kindknoten-Indizes, keine Tasks.
- `#1`, `#2`, `#3` in `evaluations/research_value_head_alternatives_DRAFT.md`
  -- interne, informelle Rueckverweise auf zuvor im selben Dokument
  numerierte "Ideen" (Idee 1.1, 4.1, 3.1 ...), ein lokales Nummernschema
  ohne Bezug zur Task-Registratur.
- `#1`, `#2` ("Wheel #1"/"Wheel #2", `archive/history.md:7198-7280`) --
  Build-/Wheel-Versionsstaende, keine Tasks.
- `#2` ("Kuppel #2", `archive/history.md:4197`) -- Beispiel-Kuppelindex
  in einer Feld-Erlaeuterung, kein Task.
- `#2` ("Koordinator-Fehler #2", `engine/py/neural_net.py:659`) -- ein
  gezaehlter Fehlerfall in einem Namenskonventions-Kommentar, kein Task
  (siehe Beobachtungen unten).
- `#3`, `#4` ("Design-Vorgabe #3"/"#4", `server.py:1025,1112,1557`) --
  eine lokale Nummerierung von Spielregel-/Design-Vorgaben in `server.py`,
  ein eigenes, von der Task-Serie unabhaengiges Schema.
- `#1` ("Gate-Fix #1", `evaluations/PREREG_r5_value_calibration.md:218`,
  `tools/r5_value_calibration.py:45,134`) -- eine lokale Fix-Nummer
  innerhalb einer einzelnen Messung, kein projektweiter Task.
- `#344`, `#833` (`evaluations/research_value_head_alternatives_DRAFT.md:142`)
  und `#1480` (`archive/history.md:189`) -- externe GitHub-Issue-Nummern
  (KataGo/leela-zero-Repos), keine internen Tasks.

**Normalisiert** (nicht separat gezaehlt): Treffer mit deutschem
Genitiv-„s" direkt am Suffix (`#80s`, `#81s`, `#12s`, `#14s`, `#93s`,
z.B. "#80s Prognose" = "des Task #80") wurden ihrer Basisnummer
zugeschlagen, nicht als eigene Nummer gefuehrt. `#63a` und `#35b` sind
dagegen echte eigene Unter-Kennungen (kein Genitiv) und stehen als eigene
Zeilen. `Task #15 A`/`Task #15 B` (mit Leerzeichen statt direkt
angehaengtem Buchstaben) ist eine dritte, uneinheitliche Schreibweise fuer
denselben Zweck -- unten unter Nummer 15 zusammengefasst, mit den beiden
Teilen als A/B benannt.

## Hauptregistratur (65 Nummern, sortiert)

| Nummer | Thema | Status | Belegstelle |
|---|---|---|---|
| 5 | Gumbel-Rang-Invarianz vs. Wertungsplatten (Plate-Shaping-Rang-Effekt) | entschieden -- Shaping-Hebel blieb folgenlos (+2,4pp, n.s.) | `archive/history.md:4741` |
| 6 | Kader-Komplettierung `v17_best` (nachgeholte Elo-/Gating-Kanten aus dem v17-Zyklus) | entschieden -- durchgefuehrt, `v17_best` signifikant staerker als Heuristik | `archive/history.md:5119` |
| 8 | Marginal-Delta-Plate-Shaping (Korrektur-Ansatz zu #93) | entschieden -- verworfen | `archive/history.md:5330` |
| 9 | Ownership-Head (Hilfsziel: 72 Binaerlabels je Kuppelfeld) | entschieden -- zweimal geschlossen (2026-07-28, erneut nach dem Nach-#34-Paket, jeweils Paritaet/kein Effekt) | `archive/history.md:5411`, `archive/history.md:10018` |
| 10 | Gumbel-Kalibrierung `GUMBEL_TOP_M` 16 vs. 8 | entschieden -- Nullergebnis | `archive/history.md:5671` |
| 11 | 2D-Conv-Encoder (Phase 1+2, Engine-Verdrahtung) | entschieden -- from-scratch-Arena ein Wash (416:384, p=0,30), aber als Champion-Encoder uebernommen (spaeter durch Korpus-Dosis-Befund gestuetzt) | `archive/history.md:6659`, `docs/design_2d_encoder.md:1` |
| 12 | Distributionaler Punkte-Kopf (C51-artiger Verteilungskopf statt Skalarregression) | entschieden -- nicht uebernommen, im Nach-#34-Paket erneut geschlossen | `archive/history.md:6212`, `archive/history.md:10018` |
| 13 | Play-Regel (visit-proportionales Sampling der Zugwahl) -- Rauschquelle? | entschieden -- Hypothese widerlegt | `archive/history.md:5568` |
| 14 | Playout-Cap-Randomization (PCR) | entschieden -- als eigenstaendiges Experiment NICHT produktiv eingesetzt; spaeter "aufgegangen in Design C", aus dem Index entfernt | `archive/history.md:7008`, `archive/history.md:10102` |
| 15 (A/B) | Entscheidungsmetrik-Wahl (A: globale Metrik ohne Runde-5-Ausschluss) / Runde-5-Ausschluss im Loss (B) | entschieden -- Metrik A sofort bewaehrt und uebernommen; Teil B ("Wash", nicht interpretierbar wegen Dedup-Konfundierung) | `archive/history.md:5617`, `archive/history.md:5716` |
| 16 | Tiling-Solver-Endwertungs-Shaping (Endwertungsbewusstsein in der Tiling-Zugwahl) | entschieden -- verworfen (1600 Spiele, p=0,5404) | `archive/history.md:6055`, `engine/src/tiling_solver.rs:47` |
| 18 | Gumbel `c_scale`-Kalibrierung | entschieden -- bleibt 1,0 trotz hoeherer Siegquote bei 0,3 (Score-Einbruch beidseits) | `archive/history.md:6133` |
| 19 | Orakel-Metriken in `offline_diagnosis.py` integriert, Orakel-Quelle = v18 | entschieden -- umgesetzt, harte Regel "Quelle darf kein Kandidat sein" seither in Kraft | `archive/history.md:6291` |
| 20 | Tiling-Zugwahl Runden 2-4: netzgefuehrter Stichentscheid (`punkte * value`) | entschieden -- validiert und aktiviert | `archive/history.md:6405`, `engine/src/tiling_solver.rs:596` |
| 21 | Tiling-Zugwahl Runde 5: exakte Endwertung statt Naeherung | entschieden -- validiert und aktiviert (gemeinsam mit #20) | `archive/history.md:6405`, `engine/src/tiling_solver.rs:100` |
| 27 | Runde-5-Value-Kalibrierung (reagiert der Kopf proportional auf Wertungsplatten-Aenderungen?) | entschieden -- Unterkalibrierung bestaetigt (Steigung 0,06-0,09 statt ~1) | `archive/history.md:7065` |
| 28 | Score-/Denial-Utility (aggressiveres Spiel, `opp_points_head` + `lambda_aggr`-Blend) inkl. Power-Erweiterung | entschieden -- kein Arm p<0,05; Aggressions-/Denial-Programm am 2026-08-07 vollstaendig geschlossen (Regler auf Default) | `archive/history.md:7140`, `archive/history.md:7195` |
| 29 | Offline-Value-Praediktor (Rangmetrik `value_kendall_tau_vs_oracle_q` gegen das Orakel) | **OFFEN** -- Rangmetrik selbst 2026-08-04 nicht validiert (2/6); als Instrument seither "wartet auf Power" (>=6 arena-entschiedene Paare, Stand ~3), laut `evaluations/STATUS.md` aktuell noch offen | `archive/history.md:7532`, `evaluations/STATUS.md:20` |
| 30 | Monotone Value-Skalen-Korrektur (`MOSAIC_VALUE_CAL_A/B`) | entschieden -- Erstlauf +6pp n.s., Replikation zeigte KEINEN Effekt | `archive/history.md:7461`, `archive/history.md:9431` |
| 31 | Menschen-Schwierigkeitsstufen leicht/mittel/schwer/extrem | offen -- zurueckgestellt (Nutzer-Entscheid 2026-08-03, "erst wenn ein Champion existiert, der gute Spieler wirklich fordert") | `evaluations/STATUS.md:403` |
| 32 | Self-Play-Zeitprofil (`MOSAIC_PROFILE_SELFPLAY`) -- traegt Runde 5 die Suchkosten? | entschieden -- gemessen: Netz-Inferenz dominiert, Runde-5-Hypothese widerlegt | `archive/history.md:7418` |
| 33 | **Kollision -- siehe eigener Abschnitt unten.** (a) Value-/Policy-Loss-Gewicht-Sweep; (b) Transpositions-Memoisierung im Tiling-Solver | (a) entschieden -- aufgegangen in #34, nicht separat gefahren; (b) entschieden -- umgesetzt (Cache-Mechanismus im Code) | `archive/history.md:9597` (a); `engine/src/tiling_solver.rs:228` (b) |
| 34 | Sieg/Niederlage-Ziel (WDL) statt margen-basiertem Value-Kopf wiederherstellen | entschieden -- VERDIKT final (2026-08-05), WDL ist seither das Standard-Value-Ziel (Champion-Architektur) | `archive/history.md:9020`, `archive/history.md:9221` |
| 35 | Ranking-Loss-Vorlauf: `root_child_q`-Logging im Suchbaum (Engine-Seite) | entschieden -- Engine-Logging erledigt (Default AN) | `archive/history.md:9772`, `engine/src/self_play.rs:1959` |
| 35b | Ranking-Loss-Trainingsarm auf Geschwister-Q (WDL-Aera) | entschieden -- GESCHLOSSEN 2026-08-08, Orakel-Vorpruefung negativ (Top-3-Masse 0,688 vs 0,710), kein Gating gefahren | `evaluations/PREREG_t35b_ranking.md:1`, `archive/history.md:10351` |
| 36 | Saettigt der Value-Kopf über die Spielzahl (analog zur Policy)? | entschieden -- "spielhungrig" bestaetigt, monotone Verbesserung 202/405/810 Dateien, kein Saettigungs-Deckel | `archive/history.md:9554`, `archive/history.md:9965` |
| 37 | Tiling-Auswahlkriterium: reines P(Sieg) statt `punkte * P(Sieg)`? | entschieden -- H0, GESCHLOSSEN (284 vs 292, p=0,33), Bestandskriterium bleibt | `archive/history.md:10218`, `evaluations/PREREG_t37_tiling_criterion.md:31` |
| 38 | Moon-Head-Feinschliff (Loss-Gewicht des `moon_nll`-Terms, Label-Horizont) | offen -- geparkt (Arbeitskreis "Spaeter" mit #31), kein akuter Bedarf | `evaluations/STATUS.md:340` |
| 39 | Startkuppel-Platzierung (Positions-/Rotations-Monotonie) | offen -- geparkt (Arbeitskreis "Spaeter" mit #31/#38); Kernbefund bereits erklaert (Position/Rotation sind tote Freiheitsgrade), Verbesserungsoptionen unentschieden | `evaluations/STATUS.md:363` |
| 62 | Elo-Tracking-Infrastruktur (`tools/elo_tracker.py`) | entschieden -- Infrastruktur fertiggestellt, spaeter durch gepaartes Gating (#76) als Standardpraxis abgeloest | `tools/elo_tracker.py:2`, `archive/history.md:1409` |
| 63 | Inferenz-Batching (`Net::eval_pair`, beide Blatt-Perspektiven in einem Forward-Pass) | entschieden -- umgesetzt, Teil des validierten Speedbundles | `tools/paired_arena_arm_worker.py:2`, `tools/paired_arena_speedbundle.py:2` |
| 63a | Inferenz-Batching, konkrete Implementierungs-Notiz zu #63 | entschieden -- siehe #63 (dieselbe Massnahme, keine eigenstaendige Frage) | `archive/history.md:1305` |
| 64 | Lauf-Manifest + Korpus-Log (Trainingsstart protokolliert Datenzusammensetzung) | entschieden -- Infrastruktur fertiggestellt | `archive/history.md:1322`, `engine/src/lib.rs:498` |
| 65 | ISMCTS-Mehrfach-Determinisierung | entschieden im Vor-WDL-/Vor-Gumbel-Regime (2026-07-22, arena-widerlegt); 2026-08-08 unter neuem Namen/Regime REAKTIVIERT und laut `PREREG_ismcts_determinizations.md` aktuell **OFFEN** (Messung steht in der NACH-v21-QUEUE aus) | `archive/history.md:1456`, `evaluations/PREREG_ismcts_determinizations.md:83` |
| 67 | Self-Play-Diversitaets-Monitoring | entschieden -- fertig, Urteil "GESUND, kein Kollaps" | `tools/selfplay_diversity_report.py:2`, `archive/history.md:1400` |
| 68 | Gumbel-Suche Tiefe >=1 mctx-treu (`gumbel_select_child`) | entschieden -- umgesetzt, Teil des Speedbundles. Der Merkposten "Validierung Phase 2" ist am 2026-08-09 aufgearbeitet: GUMBEL_TOP_M 16 vs 32 durch `PREREG_prior_blind_spot.md` beantwortet (Miss-Rate 1,21%); NET_SIMS 400 vs 800 durch das Zwei-Klassen-Design faktisch entschieden (600 Sockel / 150 Schwarm); und die Aussage "MAX_ACTIONS/WIDEN_FACTOR/POLICY_MASS_CUTOFF ENTFERNT statt getunt" ist im Netzpfad KORREKT -- im Code nachgeprueft: `skip_cutoff = parent.is_none() || USE_GUMBEL_SEARCH` (net_mcts.rs:1651) setzt den Cutoff ueberall aus, und der Widening-Cap (Zeile 3447) liegt hinter dem Gumbel-Early-Return (Zeile 3387), also im toten PUCT-Zweig. In `crate::mcts` (Heuristik) bleiben die Konstanten live. Merkposten damit GESCHLOSSEN | `archive/history.md:1309`, `archive/history.md:1425` |
| 69 | Daten-Skalierungs-Ablation (`--train-file-limit`) | entschieden -- fertig, differenziertes Ergebnis | `archive/history.md:1327` |
| 70 | R6-Nachtrag Peek-Kosten-Fix (`PlayerBoard::apply_paid_cost`) | entschieden -- umgesetzt | `archive/history.md:1315` |
| 71 | Knoten-Budgets statt Zeitbudgets, Einzelspiel-Flush, Heartbeat (Determinismus-Fix) | entschieden -- umgesetzt, seither vielfach als Regressionsschutz-Muster referenziert | `archive/history.md:1435`, `engine/src/round_transition_deep.rs:64` |
| 72 | TD-Lambda-Sweep | entschieden -- Empfehlung λ=0,7 (aber siehe #73: im Arena-Test NICHT bestaetigt) | `archive/history.md:1345` |
| 73 | td07-Arena-Test (λ=0,7 gegen Champion) | entschieden -- λ=0,7 NICHT uebernommen (`v11_td07` 30:70 verloren) | `archive/history.md:1382` |
| 74 | Build-Gate (Testsuite vor Zyklusabschluss) | entschieden -- 151/151 gruen | `archive/history.md:1720` |
| 76 | Gepaartes Gating als Standard-Champion-Ablösungsverfahren | entschieden -- eingefuehrt, seither Standardpraxis | `archive/history.md:1649`, `tools/paired_gating.py:2` |
| 77 | LR-Schedule/Warm-Start-Feintuning (`--lr`/`--lr-schedule`, v12b) | entschieden -- wurde Bestandteil des Standard-Trainingsrezepts | `archive/history.md:1817` |
| 78 | Rundenabhaengige Value-Shrinkage (`VALUE_SHRINK_ENABLED`, v12c) | entschieden -- Mechanismus gebaut, Default bleibt AUS (inert) | `engine/src/net_mcts.rs:419`, `evaluations/STATUS.md:306` |
| 79 | VALUE_WEIGHT/POINTS_WEIGHT-Sweep-Infrastruktur (v12d) | entschieden -- `--value-weight`/`--points-weight` gebaut und genutzt | `train.py:2056` |
| 80 | Self-Play-Kostenprofil (Gumbel-Suche vs. rtv vs. Bootstrap) | entschieden -- gemessen: rtv ~81% der Self-Play-Kosten | `archive/history.md:2142` |
| 80b | **Fehlbezeichnung, keine eigene Nummer** -- gemeint war das Gating `v13_nortv_best` vs `v12b_lr_best` (171:129), inhaltlich **#85** (rtv-Ablation Phase 2, dort wurde `v13_nortv_best` Champion). #80 ist das Self-Play-Kostenprofil und hat damit nichts zu tun. | erfasst 2026-08-10 -- der historische Kommentar bleibt UNVERAENDERT stehen (ein Protokolleintrag von damals soll nicht nachtraeglich stimmen), die Registratur fuehrt die Nummer als bekannte Fehlbezeichnung | `evaluations/elo_history.csv:7`, Sache siehe #85 |
| 81 | Amdahl-Split fuer den geplanten GPU-Umbau (Netz-Eval-Anteil je Kostenkategorie) | entschieden -- gemessen | `archive/history.md:2291` |
| 82 | Zentraler GPU-Inferenz-Batcher (RTX 3060) | **AUFGEGRIFFEN 2026-08-09**: Machbarkeitsprobe vorregistriert (`PREREG_gpu_inference_batcher.md`), damit kein UNKLAR mehr. Anlass: der Inferenz-Anteil ist mit 62-81% der Self-Play-Zeit HOEHER als die Registratur-Vermutung annahm | `archive/history.md:2293` |
| 84 | rtv-Ablation Phase 1 (traegt `round_transition_value` ueberhaupt Staerke bei?) | entschieden -- abgeschlossen, Grundlage fuer #85 | `archive/history.md:2735` |
| 85 | rtv-Ablation Phase 2 (rtv default abschalten) | entschieden -- rtv seither standardmaessig AUS, `v13_nortv_best` wurde Champion | `archive/history.md:2940` |
| 86 | Gepaartes Gating `v13_best` vs. `v12b_lr_best` | entschieden -- SPRT harter Deckel ohne Entscheid (p=0,2615), kein Champion-Wechsel | `archive/history.md:2595`, `archive/history.md:2703` |
| 87 | Eingefrorenes, generationsuebergreifendes Eval-Set (`build_frozen_eval_set.py`) | entschieden -- gebaut, seither Standardinstrument fuer Offline-Diagnose | `archive/history.md:2471`, `tools/build_frozen_eval_set.py:2` |
| 88 | Hybrid-Suche 2x2 (kausaler Kopf-Test: traegt Policy- oder Value-Kopf die Staerke?) | entschieden -- Value-Kopf traegt die Staerke (kausal bestaetigt) | `archive/history.md:3094`, `tools/hybrid_paired_arena.py:1` |
| 89 | Oracle-Metriken (Teil A: Suchzugang; Teil B: Labels + Offline-Metriken) | entschieden -- gebaut und validiert (7/7 Vorhersagen bei Prior-Masse/Kendall-Tau) | `archive/history.md:3831`, `archive/history.md:3908` |
| 91 | v15-Zyklus + Frischdaten-Ablation | entschieden -- durchgefuehrt | `archive/history.md:3445` |
| 92 | Arena-Trend-Log fuer Ø-Score/Floor | entschieden -- implementiert, im Einsatz | `archive/history.md:3402`, `tools/arena_trends.py:1` |
| 93 | Wertungsplatten-Shaping A/B (Blattwert-Additiv fuer Plattenfortschritt) | entschieden -- Shaping bleibt folgenlos (siehe auch #5 Teil 1c), Toggle bleibt aus | `archive/history.md:3620`, `engine/src/net_mcts.rs:914` |
| 94 | v16-Zyklus | entschieden -- durchgefuehrt | `archive/history.md:3719` |
| 95 | KI-Debugger: Value-Head-Anzeige + granularer Gumbel-Trace | entschieden -- implementiert | `archive/history.md:4107` |
| 96 | PyInstaller-Release-Build | entschieden -- implementiert | `tools/build_release.py:2`, `server.py:37` |
| 97 | Lehrer-Modus (GUI-Feedback zu Zuegen) | entschieden -- implementiert | `server.py:132`, `archive/history.md:4327` |
| 98 | v17-Zyklus | entschieden -- durchgefuehrt (`v17_best` wurde Champion) | `archive/history.md:4174` |

## KOLLISIONEN

**Ein harter Befund**: **`#33`** bezeichnet an zwei Stellen zwei
**voellig unabhaengige** Themen, beide mit Datum 2026-08-04:

1. `archive/history.md:9597`, Abschnitt "Task #33: Value-/Policy-Loss-
   Gewicht-Sweep (Report 5.3)" -- ein geplantes Trainings-Experiment
   (Sweep von `--value-weight`/`--points-weight`), das laut
   `archive/history.md:9712` ("Task #33 wandert IN #34 hinein") NIE
   eigenstaendig gelaufen ist, sondern in die Task-#34-Messung integriert
   wurde.
2. `engine/src/tiling_solver.rs:228`, Kommentarblock "── Task #33:
   Transpositions-Memoisierung ───" -- ein Caching-Mechanismus fuer den
   Tiling-Solver (Rust-Engine-Code), mit eigener Herleitung des
   Cache-Schluessels, "Auftrag Schritt 1a, Code gelesen 2026-08-04".

Beide Verwendungen sind durch das Datum 2026-08-04 zeitlich benachbart,
haben aber nichts miteinander zu tun (Trainings-Loss-Gewichtung vs.
Suchbaum-Caching im Tiling-Solver) -- ein Beleg dafuer, dass parallel
arbeitende Agenten/Sessions unabhaengig voneinander dieselbe freie Nummer
gezogen haben. Genau das Risiko, das die neue Namenskonvention
(`PREREG_INDEX.md`) beheben soll.

### REPARATUR 2026-08-09 (Nutzer-Entscheid: "duplikate sind nicht aktzeptabel")

Die Kollision ist aufgeloest: der **Rust-Block wurde auf `#99`
umnummeriert** (`engine/src/tiling_solver.rs`, drei Stellen, mit
Reparatur-Notiz im Code). Die history.md-Bedeutung behaelt `#33`.

Warum diese Richtung: die Loss-Sweep-Bedeutung steckt an **fuenf**
Stellen in einer Entscheidungs-Erzaehlung (`#33 VOR #34` -> korrigiert
zu `#33 IN #34`, "Prioritaet: vor #33 und #35") -- ein Umschreiben
haette den dokumentierten Ablauf verfaelscht. Die Memoisierung stand an
**drei** Stellen in einer einzigen Datei.

Warum `#99` und nicht eine der freien Luecken: die Luecken sind NICHT
beweisbar frei. Nummern koennen im Chat vergeben worden sein, ohne Spur
in den Dateien zu lassen (siehe Warnhinweis im LUECKEN-Abschnitt) --
eine Interior-Luecke zu recyceln koennte eine NEUE Kollision erzeugen.
Oberhalb des bisherigen Maximums `#98` ist das ausgeschlossen.
`cargo build --release` nach der Umnummerierung gruen.

**Dies ist die einzige zulaessige Vergabe einer neuen `#NN`**: eine
Reparatur an einem bestehenden Widerspruch, keine Kennung fuer neue
Arbeit. Fuer neue Arbeit gilt unveraendert die Namenskonvention
(Prereg-Datei ist die Kennung).

**Ein weicher, historischer Fund**: **`#5`** wurde laut
`archive/history.md:5452` ("**Liga-Selfplay gegen Alt-Champions**
(urspruenglich als #5 vorgeschlagen)") zunaechst fuer eine Idee
vorgeschlagen, die noch VOR jeder Umsetzung vom Nutzer verworfen wurde
("die Policy-Targets der schwaecheren Seite ziehen das Netz aktiv
Richtung schwaecheres Spiel"). Die Nummer #5 wurde danach fuer das
tatsaechlich durchgefuehrte "Task #5: Gumbel-Rang-Invarianz vs.
Wertungsplatten" (`archive/history.md:4741`, chronologisch sogar EIN TAG
FRUEHER dokumentiert als der verworfene Vorschlag) vergeben. Da die
"Liga-Selfplay"-Idee nie unter dieser Nummer umgesetzt oder mit einem
Ergebnis versehen wurde, ist dies keine echte Doppelbelegung wie bei #33,
aber ein Beleg dafuer, dass die Nummer informell mehrfach im Umlauf war,
bevor sie sich auf ein Thema festlegte. Aufgenommen, weil ein Leser, der
nur "#5" im Text sucht, sonst faelschlich beide Stellen fuer dasselbe
Experiment haelt.

**Sonst keine weiteren Kollisionen gefunden.** Alle uebrigen 63 Nummern
bezeichnen an jeder gefundenen Stelle konsistent dasselbe Thema (auch dort,
wo eine Nummer mehrere chronologische Stufen durchlief, z.B. #28, #30, #34,
#65, #89 -- das sind Fortschritts-Updates desselben Themas, keine
Kollisionen).

## LUECKEN

Bereich der gefundenen Nummern: **5 bis 98**. Innerhalb dieses Bereichs
NICHT belegt (keine Interpretation -- es kann Nummern geben, die nur im
Chat vergeben und nie in eine Datei geschrieben wurden):

**7, 17, 22, 23, 24, 25, 26, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50,
51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 66, 75, 83, 90**

Auffaellig ist der grosse zusammenhaengende Block 40-61 (22 fehlende
Nummern) zwischen der Tiling-/2D-Encoder-Serie (bis ~39) und der
Engine-Infrastruktur-Serie (ab 62) -- moeglicherweise ein Serienwechsel
oder ein Zeitraum, der nicht (mehr) in den durchsuchten Dateien dokumentiert
ist.

## UNKLAR

**`#82` -- Zentraler GPU-Inferenz-Batcher (RTX 3060).** Das Thema ist klar
(`archive/history.md:2293`: "Task #82 plant einen zentralen
GPU-Inferenz-Batcher"), aber in keiner der durchsuchten Dateien findet
sich ein Abschluss -- weder ein Umsetzungs-Nachweis noch eine explizite
Absage/Zurueckstellung. Alle Fundstellen (`archive/history.md:2380-2435`)
sind vorbereitende Ueberlegungen ("relevant fuer #82", "Konsequenz fuer
#82") aus der Amdahl-Split-Analyse (#81) vom 2026-07-24; danach taucht die
Nummer nirgends mehr auf. Da die spaetere rtv-Abschaltung (#85) den
Self-Play deutlich beschleunigte, ist denkbar, dass der GPU-Batcher
dadurch an Dringlichkeit verlor und informell fallengelassen wurde --
das ist aber eine Vermutung, keine belegte Aussage. Status daher **unklar**
statt "zurueckgezogen".

**NACHTRAG 2026-08-09**: aufgeklaert und eingetaktet. Die Vermutung
"durch die rtv-Abschaltung an Dringlichkeit verloren" ist WIDERLEGT --
der Inferenz-Anteil liegt in der aktuellen Aera bei ~81% der
Self-Play-Zeit (`PREREG_v20_campaign.md:71`), gegen 62% in der
frueheren Profilmessung. Machbarkeitsprobe vorregistriert in
`PREREG_gpu_inference_batcher.md`; entscheidende Frage ist nicht der
GPU-Spitzendurchsatz, sondern der real erreichbare Batch.

Alle anderen 64 Nummern liessen sich eindeutig einem Thema zuordnen.
