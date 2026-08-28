<!-- STATUS: ENTSCHIEDEN | Frage: Werden die Trainingsziel-Felder (bootstrap/round_transition) maschinenlast-unabhängig, wenn die Task-#71-Not-Deckel bei Feuern auf deterministischen Fallback degradieren statt still zu kappen? | Beleg: ENTSCHIEDEN 2026-08-14 (Details Datei-§4): Stufe 1 gemessen, Stufe 2 gebaut, Stress-Abnahme byte-identisch bestanden, 0 Not-Deckel-Feuerungen; der Gate-B-Retest ist seit 2026-08-21 gegenstandslos (Async-Strang geschlossen, §4.3). -->

# PREREG: Deterministische Trainingslabels (Task-#71-Not-Deckel, "Baustein 2b")

Stand 2026-08-14, PLAN (Nutzer-Go: *"go, häng es als 2b an"*). Läuft NACH der
Schleifen-Vereinheitlichung (PREREG_unified_game_loop.md) und VOR der
Korpus-Generierung (PREREG_ownership_corpus.md). Durchgehend Plan-Zeitform.

## §1 Geprüfter Ist-Stand

- Task #71 hat die PRIMÄREN Abbruchkriterien der Rundenübergangs-Bewertung
  bereits deterministisch gemacht (`POLICY_NODE_BUDGET` als "PRIMÄRER
  Cutoff", round_transition_deep.rs:188).
- Wall-Clock-Deadlines existieren aber weiter als "Not-Deckel" auf JEDER
  Ebene (`overall_deadline`/`heuristic_deadline`/Sample-Deadlines,
  round_transition_deep.rs:412-:597) — und wenn einer feuert, ist das dem
  Label NICHT anzusehen: ein gekapptes `bootstrap_value`/
  `round_transition_value` sieht aus wie ein volles.
- Beleg der Wirkung: Gate B (PREREG_async_search.md) fand Spielverlauf
  bit-identisch, aber Trainingsziel-Felder sync↔async divergent — die Deckel
  binden je nach Ausführungsgeschwindigkeit. Dieselbe Mechanik macht
  Produktions-Labels von der MASCHINENLAST abhängig.

## §2 Stufen (vorab festgelegt)

**Stufe 1 — Feuerraten-Messung (Diagnose, kein Verhaltenseingriff):**
Zähler je Not-Deckel-Stelle (Diagnose-Ausgabe analog batcher_diagnostics),
~50-Partien-Probe über run_net_self_play unter normaler Last. Bericht:
Feuerrate je Stelle. Deutung vorab: Rate ≈ 0 → Makel im Sync-Normalbetrieb
theoretisch (dann wirkt Stufe 2 nur als Versicherung); Rate > 0 → Anteil
heute betroffener Labels ist beziffert.

**Stufe 2 — Ehrliche Deckel:**
1. Not-Deckel feuert ⇒ betroffenes Trainingsziel-Feld bekommt den
   DETERMINISTISCHEN Fallback (reiner Spielausgang statt lastabhängigem
   Teilergebnis) — Labels sind dann entweder voll deterministisch oder
   ehrlich-konservativ, nie heimlich maschinenabhängig. BEWUSST ohne neues
   Record-Feld: ein Schema-Bump würde den gemeinsamen HDF5-Cache
   invalidieren (Kostenpunkt aus der Plattenkopf-Planung).
2. Not-Deckel auf Ausnahme-Niveau heben (~10× heutige Kalibrierung) — als
   reine Hänger-Versicherung; der äußere Watchdog existiert zusätzlich.

## §3 Abnahme

1. Unbelastete Maschine: Golden-Labels VOR/NACH der Änderung identisch auf
   festen Seeds (die deterministischen Budgets binden zuerst, kein Deckel
   feuert ⇒ nichts darf sich ändern).
2. Unter Last (künstliche CPU-Last oder Async-Pfad): Labels jetzt identisch
   zum unbelasteten Lauf ODER nachweislich auf Fallback gesetzt — nie ein
   drittes, lastabhängiges Ergebnis.
3. Paritäts-Hash, cargo test, Wheel-Neubau wie immer.
4. Gate-B-Retest der Trainingsziel-Felder (sync↔async) als Abschluss: die
   §-Divergenz aus PREREG_async_search.md muss damit verschwinden oder
   vollständig als Fallback-Fälle erklärbar sein.

## §4 Ergebnis (2026-08-14)

### §4.1 Stufe 1 — Feuerraten-Messung

`round_transition::NOT_DECKEL_STATS` (`round_transition.rs:231`, `AtomicU64`-
Zaehler, Muster `net_batcher.rs::BatcherStats`) + zwei pyo3-Funktionen
(`not_deckel_diagnostics_json`/`reset_not_deckel_diagnostics`,
`lib.rs`) zaehlen je Not-Deckel-Stelle Pruefungen UND Feuerungen, isoliert
von den deterministischen Mit-Bedingungen (node_budget/guard/Tiefe) --
GEPRUEFT per Code-Lese: `negamax_progress` (`round_transition_deep.rs:338`),
`choose_drafting_action_pruned` (Zeile `434`, zwei Stellen: Kandidatenschleife
+ Gamma-Voll-Sample), `simulate_one_round` (Zeile `593`),
`sample_round_transition_value` (`round_transition.rs:326`, EIN gemeinsamer
Ort fuer ALLE "Sample-Deadlines" aus §1 -- Befund gegen die urspruengliche
Auftrags-Annahme: die Zeilen `:492`/`:557`-`:597` in
`round_transition_deep.rs` ERZEUGEN nur die jeweilige `deadline`, GEPRUEFT
wird sie an EINER Stelle in der Nachbardatei, nicht an jeder Erzeugungsstelle
einzeln).

~50-Partien-Probe (`tools/probes/emergency_cap_fire_rates.py`, `run_net_self_play`,
Champion `v21_2d_brierbest`, sims=400, 8 Threads, `record_rtv=true`, Seed
20260814, normale Last): 8204 Step-Records, 50 Partien.

| Stelle | Pruefungen | Feuerungen | Rate |
|---|---:|---:|---:|
| `sample_transition` | 6509 | 0 | 0,0000 % |
| `drafting_loop` | 127335 | 0 | 0,0000 % |
| `gamma_full` | 2076 | 0 | 0,0000 % |
| `negamax_entry` | 1988436 | 941 | 0,0473 % |
| `negamax_loop` | 1997345 | 594 | 0,0297 % |
| `simulate_round` (Deadline) | 63862 | 0 | 0,0000 % |
| `simulate_round` (Guard, Kontext) | 63862 | 0 | 0,0000 % |

**Deutung**: die Mechanik ist bestaetigt (`negamax_progress` feuert real,
wenn auch selten, SCHON unter normaler 8-Thread-Selbstspiel-Last) -- Stufe 2
wird gebaut, nicht nur als Versicherung fuer die anderen (in dieser
Stichprobe 0%) Stellen, sondern als tatsaechliche Korrektur fuer
`negamax_progress`.

### §4.2 Stufe 2 — Gebaut

1. **Konstanten ~10× angehoben** (`round_transition_deep.rs`:
   `POLICY_TIME_BUDGET_PER_DECISION` 200ms→2s, `POLICY_OVERALL_TIME_BUDGET_
   PER_DECISION` 15s→150s, `ROUND_SIM_TIME_BUDGET` 15s→150s,
   `INNER_SAMPLE_TIME_BUDGET` 20s→200s, `GAMMA_SAMPLE_TIME_BUDGET`
   500ms→5s, `TIME_BUDGET_TRAIN_ROUND{1,2,3}` 45/75/75s→450/750/750s;
   `round_transition.rs`: `TIME_BUDGET_TRAIN` 5s→50s, `TIME_BUDGET_TRAIN_
   ROUND4` 60s→600s; `EXTRA_GAME_TIMEOUT_SECS` (Zeile `195`) auf die neue
   Worst-Case-Summe 2550s nachgezogen, referenziert von `self_play.rs` per
   Konstantenname, dort NICHTS angefasst). PRIMAERE deterministische Budgets
   (`POLICY_NODE_BUDGET`, `POLICY_DEPTH`, alle `N_SAMPLES_TRAIN*`,
   `N_MIN_/N_FULL_ROUND_END`, `guard=300`) UNVERAENDERT. `net_mcts.rs`s
   `TIME_BUDGET` (Live-Suche, hinter `ROUND_TRANSITION_SAMPLING=false`
   inaktiv) bewusst NICHT angefasst -- ausserhalb des in `round_transition_
   deep.rs`s eigenem Modul-Kommentar erklaerten Zuschnitts ("Nur fuer den
   Trainingsziel-Pfad ... NICHT fuer die Live-Suche").
2. **Ehrliche Deckel, zwei Stellen** (kein neues Record-Feld):
   - `sample_round_transition_value`: feuert die Deadline VOR `cap`
     erreichten Samples (auch mit `n>0`, nicht nur `n==0`), wird das
     Teil-Mittel VERWORFEN -- Fallback ist in JEDEM Fall derselbe
     `evaluator(&pre.state, rng)`-Kurzpfad, nie ein load-abhaengiges
     Teil-Mittel. Test `deadline_mid_loop_discards_partial_samples_not_
     just_zero` (per `thread::sleep` erzwungener Teil-Abbruch, 1 von 8
     Samples) -- GEPRUEFT dass er etwas prueft: Fix testweise entfernt →
     Test schlaegt mit `[0.0, 0.0]` statt `[1.0, 1.0]` fehl; restauriert →
     gruen.
   - `choose_drafting_action_pruned`: feuert `overall_deadline` (nicht
     `node_budget`) in der Kandidatenschleife, faellt die Wahl auf den
     PRE-SORTIERTEN ersten Kandidaten (`ordered_children_pruned`s billige
     `leaf_value_progress`-Rangfolge) zurueck statt auf das load-abhaengige
     "bislang beste unter den geschafften Kandidaten"-Ergebnis. Kein
     dedizierter Unit-Test gebaut (Stufe-1-Messung fand hier 0 Feuerungen,
     Umsetzung ist reine Vorab-Korrektheit fuer den Lastfall; die
     End-zu-Ende-Golden-Vergleiche in §4.3 pruefen den Gesamtpfad mit) --
     selbst geflaggte Luecke.

### §4.3 Abnahme

**cargo test --lib**: 419/0/20 (418 Bestand + 1 neuer Test).
**Wheel neu gebaut+installiert, Paritaetsprobe**: Hash
`8c6684ffba06cf3e16e898b83325f3154c04efac555c8e862c079b71155bd423` haelt.

**Punkt 1 (unbelastete Maschine) -- Befund weicht vom Ideal-Bild ab, MIT
geklaerter Ursache, kein Fehlschlag der Aenderung selbst.** VOR-Baseline
(Commit `d9c49e6`, isolierter `git worktree scratchpad/wt_2b_vor`) vs. NACH
(dieser Stand), `engine/examples/golden_game_loop_capture.rs`, Pfade p4+p1n,
12 Partien, Seed 20260814, `num_threads=1`, Modell `v21_2d_brierbest`:
- **p1n**: 2068/2068 Records byte-identisch.
- **p4**: NUR 1630/1956 Records byte-identisch, ab da kaskadierende
  Abweichung (Spielverlauf, Scores, Record-Zahl 1959 vs. 1956) -- ZU GROSS
  fuer die erwartete "0 Bit ausser rtv"-Erwartung.
- **Diese Maschine ist NICHT unbelastet**: `Get-Process` zeigte waehrend
  BEIDER Captures mehrere parallele `claude`-Sessions (Zehntausende
  CPU-Sekunden) und einen aktiven `async_selfplay_throughput_probe`-Prozess
  (GPU-Agent, `wt_async2`) -- ein geteilter Rechner mit mehreren
  gleichzeitigen Agenten-Sitzungen, kein isolierter Messstand.
- **Ursache empirisch verifiziert, nicht nur vermutet**: (a) VOR zweimal in
  SEPARATEN Prozessen wiederholt (`golden_vor` vs. `golden_vor_repeat`,
  p4) -- **byte-identisch** (0/1959) trotz derselben Maschinenlast --
  schliesst Cross-Prozess-ASLR-Rauschen (der dokumentierte "Restbefund" in
  `round_transition_deep.rs`s Modul-Kommentar) als Ursache aus. (b) NACH
  mit den ALTEN (nicht angehobenen) Konstanten neu gebaut und unter
  identischen Bedingungen (Seed/Sims/Threads) erneut gemessen: liefert
  EXAKT 1959 Records (= VOR-Zahl) UND zeigt am eigenen Zaehler ECHTE
  Feuerungen (`negamax_entry_deadline_fires=24`, `negamax_loop_deadline_
  fires=14`) -- auf DIESER Maschine, JETZT, feuerte der alte (enge)
  Not-Deckel also tatsaechlich, nicht nur theoretisch. Mit den NEUEN
  (angehobenen) Konstanten: 0 Feuerungen, 1956 Records, reproduzierbar
  (siehe Punkt 2). **Schlussfolgerung**: die VOR/NACH-Abweichung ist die
  BEABSICHTIGTE Wirkung von Stufe 2 (ein damals bereits real feuernder
  Not-Deckel wird beseitigt), keine Regression -- der Praemisse "auf einer
  unbelasteten Maschine feuert kein Deckel" widerspricht dieser geteilte
  Rechner selbst, nicht die Aenderung.

**Punkt 2 (unter Last) -- BESTANDEN.** NACH-Capture (kein `--paths`-Wechsel,
identischer Seed) einmal ohne und einmal MIT zusaetzlichem kuenstlichem
CPU-Stress (`tools/probes/cpu_stress.py`, 12 Dauerlast-Prozesse zusaetzlich
zur ohnehin schon vorhandenen Fremdlast) ueber `mosaic_rust.
net_self_play_games`: **1956/1956 Records byte-identisch**, 0 Not-Deckel-
Feuerungen in BEIDEN Laeufen. Der geforderte Repro-Massstab (§3 Punkt 2:
"0/1308 in ALLEN Feldern") ist damit fuer p4 sogar unter zusaetzlichem
kuenstlichem Stress erreicht (0/1956, staerkerer Test als gefordert).

**Punkt 3**: siehe oben (cargo test/Wheel/Paritaet).

**Punkt 4 (Gate-B-Retest) -- ZURUECKGESTELLT, wie angewiesen.** Nicht
selbst in `wt_async2` gearbeitet; der Retest der sync↔async-Trainingsziel-
Divergenz aus `PREREG_async_search.md` bleibt offen, bis der GPU-Agent
`wt_async2` freigibt (siehe Auftrag). Erwartung (unverifiziert, als Annahme
markiert): da der jetzt behobene Mechanismus (`negamax_progress`-Feuern
unter Last) genau die Art von last-abhaengiger Divergenz ist, die Gate B
zwischen sync/async fand, sollte der Retest die dortige Trainingsziel-
Divergenz deutlich reduzieren oder aufloesen -- das ist eine Erwartung,
keine Messung.

### §4.4 Offene/selbst geflaggte Punkte

- `choose_drafting_action_pruned`s Kandidatenschleifen-Fix hat keinen
  dedizierten Unit-Test (siehe §4.2) -- Stufe-1-Feuerrate dort war 0%,
  Risiko als gering eingeschaetzt, aber nicht durch einen erzwungenen
  Feuerfall bewiesen wie bei `sample_round_transition_value`.
  `scratchpad/wt_2b_vor` (Worktree) und `scratchpad/target_decke_vor`
  (Cargo-Target) bleiben auf der Platte (kein Loeschen ohne Freigabe) --
  reiner Mess-Aufbau, nichts committet.
- Die Stufe-1-Messung (§4.1) fand 0% Feuerrate bei `sample_transition`/
  `drafting_loop`/`gamma_full`/`simulate_round` unter NORMALER 8-Thread-
  Last -- die spaeter (§4.3) unter erzwungenem Einzel-Thread-Betrieb auf
  DERSELBEN Maschine beobachteten `negamax`-Feuerungen zeigen, dass die
  tatsaechliche Rate stark vom Zeitpunkt/der Fremdlast abhaengt. Die
  Stufe-1-Zahlen sind ein Schnappschuss, kein oberer Grenzwert.
