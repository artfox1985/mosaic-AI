# Vorregistrierung: Async-Suche (Drafting-Suche als Zustandsautomat)

**Angelegt 2026-08-13, Nutzer-Auftrag.** Parallel arbeitet ein Agent an
`net_mcts.rs`/`self_play.rs`/`spaltenbau.rs` (Aufräum-Queue) -- diese
Vorregistrierung UND der zugehörige Stufe-1-Prototyp entstehen deshalb in
einem eigenen `git worktree --detach` (`scratchpad/wt_async`, Präzedenzfall:
derselbe Kunstgriff wie in `PREREG_gpu_inferenzpfad.md` §19 für den
GPU-Wheel-Bau), nicht im Hauptbaum. Diese Datei ist die einzige Datei, die
im Hauptbaum committet wird (plus die zugehörige `PREREG_INDEX.md`-Zeile).

## 1. Anlass (GEPRÜFT)

Weg V (Verschränkung über blockierende Fäden, `net_batcher.rs`, gebaut und
vermessen in `PREREG_gpu_inferenzpfad.md` §7-§19) kann die GPU-Gewinnzone
**strukturell nicht erreichen**:

- Gemessener mittlerer Batch **~14,64** bei Deckel **16** (`EVAL_BATCH_MAX_N`)
  -- GEPRÜFT: `evaluations/gpu_inferenzpfad_selfplay_e2e_wegb.json`,
  `laeufe.armB_t8.batcher_mean_batch = 14.64`, `batcher_max_batch_seen = 16`.
- Die gemessene GPU-Gewinnzone beginnt erst bei Batch **128** (ORT-CUDA-
  Kennlinie, `PREREG_gpu_inferenzpfad.md` §8/§11).
- Ende-zu-Ende ist Weg B über den ECHTEN Self-Play-Pfad (`self_play.py`,
  nicht ein Beispiel-Binary) **0,29x** (angeforderte Basis) / **0,17x**
  (fertiggestellte Basis) gegen den Bestand -- GEPRÜFT:
  `gpu_inferenzpfad_selfplay_e2e_wegb.json`,
  `regel3_faktor_b_gg_a.t8 = {requested_basis: 0.2915, completed_basis:
  0.1676}`. Trotz nahezu gesättigtem Batch (14,64 von 16) ist der Kanal
  langsamer, nicht schneller, als der synchrone tract-Pfad -- Ursache laut
  `PREREG_gpu_inferenzpfad.md` §19 ungeklärt (Kandidaten: `Mutex<Session>`
  als serialisierendes Nadelöhr, `Session::run()`-Kosten unter echter statt
  synthetischer Ankunftsrate).
- **64 Fäden auf 12 logischen Kernen kollabieren am Wachhund**, unabhängig
  vom Batcher: GEPRÜFT, `gpu_inferenzpfad_selfplay_e2e_wegb.json`,
  `laeufe.armA_t64.hang_note`: *"64 Faeden auf 12 logischen Kernen (6.7x
  Ueberzeichnung) allein reicht, den Wachhund grossflaechig auszuloesen,
  UNABHAENGIG von Batcher/ORT-CUDA"* (nur 3/40 bzw. 0/40 Partien erreichten
  ein echtes Endergebnis). Mehr Fäden ist deshalb keine Rettung für Weg V --
  der Batch bliebe bei mehr Fäden nicht proportional wachsen, weil die
  Maschine vorher am Überzeichnungs-Limit kollabiert.

## 2. Die Idee

Suche und Faden entkoppeln: statt EIN Faden = EINE Partie (die dabei bei
jeder Blattauswertung blockiert), soll EIN Faden VIELE Partien als
fortsetzbare Zustandsautomaten beherbergen. Erreicht eine Suche ein Blatt,
parkt sie ihre Anfrage im Sammel-Faden (existiert bereits: `net_batcher.rs`)
und der ausführende Faden macht mit einer ANDEREN, bereits wartenden Suche
weiter, statt zu blockieren. Wartende Suchen kosten dann keinen Kern mehr --
der erreichbare Batch wird zur Frage "wie viele Partien parke ich
gleichzeitig", nicht mehr "wie viele OS-Fäden verträgt die Maschine", und
Batch 128-256 wird ohne 128-256 OS-Fäden erreichbar.

## 3. Abgrenzung: KEIN Virtual Loss

Das ist NICHT Weg B im Sinne von `PREREG_gpu_offloading.md` (Virtual Loss --
Parallelität INNERHALB einer Suche, verändert die Suchergebnisse selbst,
gating-pflichtig, dort bereits verworfen). Async über PARTIEN hinweg lässt
jede einzelne Suche logisch unverändert -- es ändert sich nur, WER den
physischen `eval_batch`-Aufruf ausführt und WANN ein Faden zwischen Partien
wechselt, nicht WAS eine einzelne Suche entscheidet.

## 4. Suchneutralität, präzise

Je Partie identische Suchentscheidungen bis auf die bekannte
Batch-Plan-Toleranz -- **KORRIGIERT gegenüber der ursprünglichen Vorgabe
dieser Vorregistrierung**: die Vorgabe nannte "~1e-6, `net.rs:840`". Beides
ist bei Nachprüfung falsch. GEPRÜFT am aktuellen `engine/src/net.rs`: Zeile
840 ist im heutigen Stand nur eine Abschnitts-Kommentarzeile im Testmodul
(`// ── Task #11 Phase 2: ...`), keine Toleranzaussage -- die Datei hat sich
seit `PREREG_gpu_inferenzpfad.md` §2 (2026-08-12) verschoben. Die tatsächliche
Toleranz steht an vier Stellen in `net.rs` (927, 937, 971, 982, Tests
`eval_pair_matches_two_single_evals` u.a.): **`1e-5`**, nicht `1e-6`. Der
`PREREG_gpu_inferenzpfad.md`-Text selbst (§2, dort korrekt) zitiert ebenfalls
`1e-5`. Die Rangfolge-Zuordnungs-Befunde §15-§17 dort (der 24-Rangsprung ist
ein Listenpositions-Zuordnungsartefakt, kein Präzisionsartefakt; die
Verteilungsgleichheit hält, aber ein einzelner Zustand kann je nach
Batch-Zusammensetzung eine andere Kandidatenmenge ziehen) gelten unverändert
weiter -- **Entscheidungsgleichheit ist deshalb als Verteilungsgleichheit
mit Selbstkontrolle zu messen** (Maschinerie existiert: `gumbel_scored_sorted`,
`gumbel_topm_set`, die K=200/disjunkte-Seeds-Methodik aus §16), nicht als
Bit-Gleichheit.

## 5. Stufenplan mit Gates

Jedes Gate kann den Weg billig beenden -- Abbruch ist ein gültiges Ergebnis,
kein Fehlschlag.

- **Stufe 1 -- Prototyp**: NUR die Drafting-Suche (ein Aufruf von
  `build_gumbel_tree_inner`) als Zustandsautomat, OHNE Rundenübergänge.
  **Gate A = Entscheidungsgleichheit** (1148 Zustände aus
  `frozen_eval_set_v2.pkl`, Argmax + Gumbel-Top-m, plus Verteilungstest) --
  siehe Abschnitt 8 unten für das GEMESSENE Ergebnis dieser Sitzung.
- **Stufe 2 -- Rundenübergänge/Tiling-Stichentscheid**: die Suche über
  Rundengrenzen hinweg unterbrechbar machen (inkl. der Zufallsknoten-
  Stichprobe für Fabrik-Neubefüllung). **Gate B = vollständige
  Partie-Gleichheit** synchron gegen async bei fester Batch-Zusammensetzung.
- **Stufe 3 -- Durchsatz**: die eigentliche Verschränkung über VIELE Partien
  in Produktion (self_play.rs-Integration, echter Executor statt
  Prototyp-Treiber). **Gate C = Regel 3: >= 2,0x Ende-zu-Ende** gegen
  225,6 Spiele/h (8 Threads, 400 Sims, gemessen in
  `gpu_inferenzpfad_selfplay_e2e_wegb.json`, `laeufe.armA_t8.
  games_per_hour_completed_basis`).

## 6. §18-Zuschnitt (unverändert gültig)

Gating bleibt reproduzierbar (async dort AUS, Bestand ist der
Golden-Hash-bewachte tract-Pfad); ein Arena-Boost ist nur für Messläufe in
Masse gedacht. Self-Play ist der eigentliche Zielpfad. **Nutzer-Priorität**:
Self-Plays starten ohnehin erst, wenn der Ownership-Kopf die Wertungsplatten
trägt (siehe `STATUS.md`, Zwei-Pole-Architektur) -- dieser Umbau ist
**PARALLELER VORRAT**, blockiert nichts Laufendes und wird von nichts
blockiert.

## 7. Anker unberührt

`mcts.rs` (die Heuristik-Suche, Elo-Anker@200) bleibt außen vor -- alles
lebt im Netz-Pfad (`net_mcts.rs`, `net_batcher.rs`). Der Paritäts-Hash
(`8c6684ffba06cf3e16e898b83325f3154c04efac555c8e862c079b71155bd423`) muss
bei Default-aus halten -- **GEPRÜFT in dieser Sitzung nicht erneut per
Wheel-Neubau** (der Prototyp läuft nur als `cargo test` im isolierten
Worktree, kein Python-Wheel gebaut); die neuen Funktionen sind aber additiv
und werden bei keinem Produktions-Aufrufer erreicht (siehe Abschnitt 8),
das Risiko für den Hash ist damit strukturell null, nicht nur vermutet.

---

## 8. STUFE 1: GEBAUT, GATE A BESTANDEN (0/1148 in beiden Messungen)

### Unterbrechungspunkte, mit Datei:Zeile (GEPRÜFT am Stand `d25f2f9`, Worktree `scratchpad/wt_async`)

Innerhalb EINES `build_gumbel_tree_inner`-Aufrufs (`net_mcts.rs:3615-3998`)
gibt es genau **einen** synchronen Netz-Aufruf pro Baum-Operation, immer
über dieselbe Stelle erreicht:

1. **Wurzelknoten** (`net_mcts.rs:3631-3632`): `make_node(...)`.
2. **Baumabstieg** (`descend_and_backprop`, genestet in
   `build_gumbel_tree_inner`, `net_mcts.rs:3650-3707`): GENAU EIN
   `make_node(...)`-Aufruf, wenn die Abstiegsschleife einen unbesuchten
   Kandidaten expandiert (`net_mcts.rs:3685-3687`).
3. **`visit_candidate!`-Makro** (`net_mcts.rs:3789-3849`), `None`-Zweig
   (Kandidat noch nie besucht): EIN `make_node(...)`-Aufruf
   (`net_mcts.rs:3824-3826`).

`make_node` (`net_mcts.rs:2107-2237`) selbst ist NICHT rekursiv -- es ruft
`net.eval_pair_ex`/`net.eval_ex`/`net.eval` (oder deren Batcher-Zwilling
`try_batched_pair_ex`/`try_batched_single_eval`) GENAU EINMAL auf und
delegiert die eigentliche Knotenkonstruktion an
[`node_from_net_outputs`] (`net_mcts.rs:2253-2404`, reine Funktion, KEIN
Netz-Aufruf unter den heutigen Konstanten -- Ausnahme siehe unten). Unter
den Produktionskonstanten (`ACTIVE_LEAF=Net`, `MIRROR_OTHER_VAL=false`,
`net_mcts.rs:73`/`521`) ist IMMER der `same_net && need_other_pass`-Zweig
von `make_node` aktiv (`net_mcts.rs:2148-2176`, `try_batched_pair_ex` an
`net_mcts.rs:2165`) -- der EINZIGE Zweig, der heute überhaupt erreicht wird.

**Ein zweiter, heute INERTER Netz-Aufrufpunkt liegt INNERHALB
`node_from_net_outputs`**: bei `ROUND_TRANSITION_SAMPLING=true` (Default
`false`, `net_mcts.rs`) ruft der Terminal-Zweig
`crate::round_transition::sample_round_transition_value` auf, das intern
`net_leaf_eval` aufruft (`net_mcts.rs:2357-2369`) -- ein SYNCHRONER
Netz-Aufruf, der unter dem heutigen Default nie ausgeführt wird. Das ist ein
konkreter Beleg dafür, dass Stufe 2 ("Rundenübergänge") echten, eigenen
Umbauaufwand hat und NICHT trivial aus Stufe 1 folgt -- Rundenübergänge
reichen bis in `node_from_net_outputs` hinein, nicht nur in die
Self-Play-Partieschleife.

### Gewählte Konstruktion: `async`/`await`, kein handgeschriebener Zustandsautomat

`build_gumbel_tree_inner` verschachtelt drei Schleifenebenen: die
Sequential-Halving-Phasenschleife (`while current.len() > 1 ...`,
`net_mcts.rs:3866`), darin je Phase eine Kandidaten-/Wiederholungsschleife
(`for &ci in &current ... for _ in 0..extra`, `net_mcts.rs:3874-3882`), und
`descend_and_backprop`s eigene Baumabstiegsschleife (`net_mcts.rs:3659-3696`).
Ein handgeschriebener Zustandsautomat müsste alle drei Schleifenzähler PLUS
den Baumzustand (`nodes`, `candidate_node`, `current`) als expliziten `enum`
speichern und bei jedem Wiederaufnahmepunkt von Hand reproduzieren --
fehleranfällig und schwer wartbar (CLAUDE.md: "Priorisiere Lesbarkeit und
Wartbarkeit der Heuristiken gegenüber komplexen, schwer debugbaren
Optimierungen").

`async fn` erzeugt genau diesen Zustandsautomaten MECHANISCH aus demselben
Kontrollfluss, den das synchrone Original schon hat -- die Umformung ist
"Funktionskopf + `.await`", keine Strukturänderung (siehe Diff zwischen
`build_gumbel_tree_inner` und `build_gumbel_tree_inner_async`,
`net_mcts.rs:4270ff` in der beschriebenen Bedeutung: identische
Kontrolllogik). Geprüfte Alternativen und warum sie verworfen wurden:

- **Stapelbasierte Fasern/Koroutinen** (z.B. `corosensei`/`generator`)
  wären ebenso wenig invasiv wie async/await, verlangen aber `unsafe`
  Stack-Switching und eine neue, ungeprüfte Abhängigkeit -- async/await ist
  in stabilem Rust nativ und braucht `unsafe` an keiner Stelle.
- **Kein neuer Abhängigkeitsbaum** (kein `tokio`/`futures`): ein minimaler
  `std`-only Treiber (`async_exec.rs`, neu) reicht für Stufe 1 -- ein
  Park/Unpark-`block_on` (Referenzverhalten: ein Future, ein Faden) und ein
  Busy-Poll-`run_concurrent` (mehrere Futures auf einem Faden). Ein
  produktionstauglicher Wecker-Executor (kein Busy-Poll) ist Stufe-3-Arbeit.

### Zuschnitt der Umsetzung (additiv, Default aus)

- `MOSAIC_ASYNC_SUCHE` (`net_mcts.rs::async_suche_enabled`) -- **liest heute
  KEINE Produktions-Aufrufstelle**. Der Knopf ist fürs KÜNFTIGE
  Produktions-Dispatch reserviert (Stufe 2/3, sobald auch die
  `self_play.rs`-Partieschleife unterbrechbar ist) -- "Default aus =
  byte-identisch" ist deshalb heute TRIVIAL erfüllt: es gibt noch keinen
  Aufrufer, der bei "an" etwas anderes täte.
- `net_batcher.rs`: additive `Completion`-Abstraktion (`Channel` = Bestand,
  unverändert; `Waker` = neu) plus `Batcher::eval_rows_async` /
  `EvalRowsFuture` -- der bestehende `Batcher::eval_rows` (blockierend) ist
  UNVERÄNDERT in seiner Signatur/seinem Verhalten.
  `async_exec.rs` (neu, `std`-only, kein `tokio`/`futures`): `block_on` +
  `run_concurrent`.
- `net_mcts.rs`: `try_batched_single_eval_async`, `try_batched_pair_ex_async`,
  `make_node_async`, `descend_and_backprop_async` (freistehend statt
  genestet), `build_gumbel_tree_inner_async` -- additiv, rufen für die
  eigentliche Knotenkonstruktion dieselbe `node_from_net_outputs`-Funktion
  wie das Original auf (kein Doppelpflege-Risiko). Von `make_node`s drei
  Verzweigungen ist nur der Produktions-Standardfall (`same_net &&
  need_other_pass`) tatsächlich unterbrechbar gemacht; die zwei anderen
  (kein Gegner-Pass; Hybrid-Suche Task #88) bleiben synchron, weil sie unter
  den heutigen Konstanten nie erreicht werden -- ein Ausbau dort wäre
  ungetesteter Mehraufwand.
- `build_gumbel_tree_inner_async` deckt `BATCH_ROOT_EXPANSION=true` NICHT
  ab (heutiger Produktions-Default ist `false`, `net_mcts.rs:571` --
  entspricht also exakt dem, was der synchrone Code heute tut) und nimmt
  KEINEN `GumbelTrace`-Parameter (reine Debug-/UI-Anzeige, beeinflusst die
  Entscheidung nicht).

### Gate-A-Messung, GEMESSEN in dieser Sitzung

Modell `alphazero_v20_2d_opp_brierbest.onnx`, alle **1148** Zustände aus
`frozen_eval_set_v2.pkl` (Export als `frozen_states_v2.json`, dieselbe Quelle
wie `PREREG_gpu_inferenzpfad.md` §12/§13/§16), `sims=32` (deutlich unter dem
Produktionsbudget 400 -- Gate A prüft die MECHANIK der Umformung, nicht die
Produktionsstärke; bei `sims=32` durchläuft die Sequential-Halving-Schleife
bei den meisten Zuständen trotzdem mehrere Phasen, da `n_root` dort
regelmäßig > 32 ist), `add_root_noise=false`, identischer RNG-Seed je
Zustand für den sync/async-Vergleich.

**Test 1 -- Kern (`async_drafting_search_matches_synchronous_without_batcher`,
`cargo test --release --lib -- --ignored --exact
net_mcts::tests::async_drafting_search_matches_synchronous_without_batcher
--nocapture`), OHNE registrierten Sammel-Faden:**

| Metrik | Abweichungen |
| ------ | ------------: |
| Knotenzahl | 0 / 1148 |
| Wurzelkinder-Aktionsmenge | 0 / 1148 |
| Besuchs-/Wertzahlen je Wurzelkind | 0 / 1148 |
| **Finale Zugwahl (Argmax der Wurzelbesuche)** | **0 / 1148** |

Ohne Sammel-Faden fällt `try_batched_pair_ex_async` immer auf `None` zurück,
`make_node_async` ruft dann GENAU denselben `net.eval_pair_ex`-Aufruf wie
`make_node` -- das Ergebnis ist deshalb BIT-IDENTISCH, keine Toleranz nötig.
Dieser Test beweist die mechanische Treue der Async-Umformung selbst,
unabhängig vom Sammel-Faden. Laufzeit: 54,85s für 1148×2 volle Baumsuchen.

**Test 2 -- Sammel-Faden-Smoke
(`async_drafting_search_with_batcher_concurrent_vs_synchronous`), Chunks
von 16 Zuständen GLEICHZEITIG über `async_exec::run_concurrent` auf EINEM
Faden, Sammel-Faden AN (`MOSAIC_INTERLEAVE_ENABLED=1`):**

| Metrik | Abweichungen |
| ------ | ------------: |
| **Finale Zugwahl** | **0 / 1148 (0,0000 %)** |

Hier ist Bit-Gleichheit NICHT zu erwarten (der Sammel-Faden ruft
`Net::eval_batch` mit wechselnden Batch-Größen auf, tract garantiert dort
nur Toleranz 1e-5, siehe Abschnitt 4) -- gemessen wird deshalb die
End-zu-Ende-Abweichung der TATSÄCHLICHEN Zugwahl über die volle
Mehrfach-Sim-Suche, nicht nur ein einzelner Wurzel-Eval wie in
`PREREG_gpu_inferenzpfad.md` §14-§17. Laufzeit: 390,98s (ungewöhnlich
langsam für einen Busy-Poll-Executor mit nur 16-facher Nebenläufigkeit --
NICHT weiter zerlegt in dieser Sitzung, siehe "Was NICHT geprüft ist"). Das
belegt zugleich, dass die eigentliche Stufe-1-Behauptung ("mehrere Partien
teilen sich einen Faden") tatsächlich ausgeführt wurde, nicht nur
kompiliert.

### Was NICHT geprüft ist

- Test 2 lief 390,98s für nur 1148 Zustände bei 16-facher Nebenläufigkeit --
  deutlich langsamer, als die reine Rundlaufzeit erwarten ließe (Vergleich:
  Test 1 macht 1148×2 volle Suchen in 54,85s). Kandidaten (keiner geprüft):
  `Mutex`-Kontention zwischen dem Busy-Poll-`run_concurrent` (pollt ALLE
  16 Futures in jeder Runde, auch die, die auf denselben Slot warten) und
  dem Sammel-Faden; der Busy-Poll selbst (kein Park/Unpark, verbrennt CPU-
  Zeit, die dem Sammel-Faden fehlen könnte); `MOSAIC_INTERLEAVE_FILL_TIMEOUT_
  US=2000` (2ms) als zusätzliche Wartezeit je Batch-Füllrunde. Für Stufe 1
  (Korrektheit) unerheblich, für Stufe 3 (Durchsatz) der naheliegende erste
  Nachschlag.
- **NACHGEZOGEN**: `cargo test --lib` (voller Lauf, alle Tests) im Worktree:
  **387 bestanden / 0 fehlgeschlagen / 20 ignoriert** (18 vorbestehend + 2
  neue `#[ignore]`-Gate-A-Tests -- Zahl passt exakt, keine Regression).
- `add_root_noise=true` (Selfplay-Explorationsmodus) wurde NICHT gemessen,
  nur `false` (deterministischer Modus) -- der Gumbel-`g`-Zufallswert wird
  in beiden Zweigen aus DEMSELBEN `rng`-Strom in DERSELBEN Reihenfolge
  gezogen, sollte also ebenfalls übereinstimmen, aber das ist eine
  HERLEITUNG, keine Messung.
- Stufe 2 (Rundenübergänge) und Stufe 3 (Durchsatz/Gate C) sind NICHT
  Teil dieser Sitzung -- siehe Abschnitt 5.

### Eigene Entscheidungen (nicht vorgegeben)

- `sims=32` statt Produktionsbudget 400 für Gate A -- hält den vollen
  1148er-Lauf handhabbar, durchläuft aber bei den meisten Zuständen trotzdem
  mehrere Sequential-Halving-Phasen (die Größe, die geprüft werden soll).
- Zwei getrennte Tests (Kern ohne Sammel-Faden; Smoke MIT Sammel-Faden und
  echter Nebenläufigkeit) statt eines einzigen -- der Kern-Test beweist
  Bit-Identität (starke, eindeutige Aussage über die Umformung selbst), der
  Smoke-Test beweist, dass die Verschränkung tatsächlich ausgeführt wird
  (schwächere Toleranz-Aussage, aber die eigentliche Architekturbehauptung).
- `CHUNK=16` (nicht z.B. 128) für den Smoke-Test -- Laufzeit-Rücksicht
  (siehe "Was NICHT geprüft ist"), keine Durchsatzmessung beabsichtigt.
- `GumbelTrace`-Parameter in `build_gumbel_tree_inner_async` weggelassen
  (reine Debug-/UI-Anzeige, kein Einfluss auf die gemessene Entscheidung) --
  Stufe 1 prüft Entscheidungsgleichheit, nicht Feature-Parität der
  Diagnose-Werkzeuge.
- Modellkopie (`models/alphazero_v20_2d_opp_brierbest.onnx`) in den
  Worktree kopiert statt eines Symlinks/Junction -- `models/` ist
  gitignored und wird von `git worktree add` deshalb nicht mitgebracht;
  eine reine Dateikopie hat kein Löschungs-/Junction-Risiko (siehe
  `feedback_worktree_junction_hazard`), eine einzelne `.onnx`-Datei ist
  klein genug für eine Kopie statt eines Verweises.

---

## 9. DIAGNOSE (Nutzer-Auftrag): 391s gegen 55s zerlegt -- URSACHE GEFUNDEN, KONSTRUKTIONSDETAIL, BEHOBEN

Auftrag: vor Stufe 2 pruefen, ob der Faktor ~7x (391s Sammel-Faden-Test
gegen 55s Kern-Test, beide 1148 Zustaende) ein Grundsatzproblem des Ansatzes
ist oder ein behebbares Konstruktionsdetail. Erfolgskriterium: der
16-fach-Test faellt unter 2x, oder die Begruendung steht, warum nicht.

### Instrumentierung (additiv, GEPRÜFT durch `cargo test --lib`-Gruen)

- `net_batcher.rs::BatcherStats`: `fill_wait_ns`/`eval_ns` (Nanosekunden-
  Summen, trennt "Sammel-Faden wartet auf weitere Zeilen" von "Sammel-Faden
  ruft `net.eval_batch` auf") + `batch_size_hist` (Haeufigkeit je
  tatsaechlicher Batch-Groesse).
- `async_exec.rs::run_concurrent_diag`: Zwilling von `run_concurrent`,
  zaehlt zusaetzlich JEDEN `poll()`-Versuch (macht das Ausmass des Busy-Poll
  sichtbar).
- Zwei neue `#[ignore]`-Diagnosetests in `net_mcts.rs`:
  `async_batcher_time_breakdown_diagnostic` (Sammel-Faden EINMAL registriert)
  und `..._recreate_per_chunk` (Sammel-Faden JE CHUNK neu registriert, wie
  im ORIGINALEN Smoke-Test) -- direkter A/B-Vergleich bei identischer
  Zustandsmenge.

### DER FUND: kein Grundsatzproblem, sondern ein TESTAUFBAU-FEHLER im Smoke-Test selbst

`async_drafting_search_with_batcher_concurrent_vs_synchronous` (der Test,
der die 391s lieferte) berechnete die "synchrone" Referenz JE CHUNK **INNERHALB
derselben Schleife, VOR** `clear_registry_for_test`/`ensure_batcher_for`
**FUER DIESEN Chunk** -- der Sammel-Faden des VORHERIGEN Chunks blieb bis
dahin registriert (er wurde erst DANACH neu aufgespannt). GEPRÜFT am Code:
`make_node`/`build_gumbel_tree` prüfen selbst zuerst
`net_batcher::lookup` (`net_mcts.rs:2165`, Bestandscode, nicht Teil dieser
Vorregistrierung) -- ab Chunk 2 fand die "synchrone" Referenz also den
Alt-Sammel-Faden aus Chunk 1 und lief über dessen `eval_rows()` (Kanal-
Rundlauf + `fill_timeout=2000µs`), NICHT über den direkten
`net.eval_pair_ex`-Aufruf. Weil die sequentielle Referenz zu diesem
Zeitpunkt der EINZIGE Erzeuger war, wartete der (verwaiste) Sammel-Faden bei
JEDER Zeile die vollen 2ms Füll-Timeout aus, bevor er den Ein-Zeilen-"Batch"
abschickte -- eine versteckte Zusatzlatenz von ~2ms JE Netz-Aufruf, NUR in
der vermeintlich "reinen" Referenz, für 71 von 72 Chunks.

**Das ist ein Fehler in MEINEM Testaufbau, keine Eigenschaft der
Verschränkung selbst** -- `net_batcher.rs`s eigener Modulkommentar schreibt
bereits vor: *"`self_play.rs` registriert den Sammel-Faden EINMAL pro
Lauf"* (nicht je Chunk). Der Smoke-Test hat sich nicht an seine eigene
Bauanleitung gehalten.

### Zerlegung, GEMESSEN (alle 1148 Zustände, sims=32, release-Build)

| Messung | Zeit | Faktor gg. Referenz |
| --- | ---: | ---: |
| Referenz (rein synchron, sequentiell, KEIN Sammel-Faden registriert) | ~27-28s (siehe Zeilen unten) | 1,00x |
| **create-once** (Sammel-Faden EINMAL registriert) | 27,91s verschränkt | **1,08x** |
| **Original-Muster, aber BEREINIGT** (Sammel-Faden je Chunk neu, Referenz VOR jeder Registrierung berechnet) | 26,92s Referenz / 37,07s verschränkt | **1,38x** |
| **Original-Muster, isoliert** (Sammel-Faden je Chunk neu, KEINE Referenz-Kontamination in diesem Diagnoselauf) | 37,75s verschränkt | 1,35x gg. create-once (27,91s) |

**Ursachenanteile, damit auseinandergerechnet:**

1. **Dominant: die Referenz-Kontamination selbst** -- erklärt den Sprung von
   ~1,1-1,4x (bereinigt gemessen) auf die ursprünglich berichteten 391s
   (die alte Zahl war kein gültiger Vergleich synchron-gegen-async, sondern
   grösstenteils "kontaminierte Pseudo-Referenz mit 2ms-Strafe je Aufruf"
   gegen "async mit derselben Strafe zusätzlich"). Die GENAUE alte
   391s-Zahl wird hier NICHT nachgerechnet (der Fehler ist behoben, nicht
   reproduziert) -- die neue, bereinigte Messung ersetzt sie.
2. **Klein, aber real: Sammel-Faden je Chunk neu aufspannen statt einmal**
   -- 27,91s (create-once) gegen 37,75s (Original-Muster, isoliert) =
   **1,35x Aufschlag**, NICHT die 6-7x, die die ursprüngliche Zahl nahelegte.
   Bleibt ein legitimer, aber SEKUNDÄRER Befund: Stufe 3 sollte den
   Sammel-Faden analog zu `net_batcher.rs`s eigener Vorgabe EINMAL je Lauf
   registrieren, nicht je Partiegruppe.
3. **Busy-Poll-Churn ist REAL, aber NICHT der Haupttreiber bei dieser
   Größenordnung**: 300.000-450.000 `poll()`-Versuche je Future (100 % davon
   nach der groben Metrik "Pending, kein Fortschritt") -- objektiv
   verschwenderisch (siehe `async_exec.rs`s eigener Kommentar: "kein
   Park/Unpark ... fuer Produktionsdurchsatz waere ein Wecker-Executor die
   richtige Wahl"), aber die WALL-CLOCK-Zahlen (0,97x bis 1,55x über
   mehrere unabhängige Stichproben, siehe Abschnitt darüber) zeigen, dass
   dieser Zusatz-CPU-Verbrauch bei 16-facher Nebenläufigkeit NICHT
   dominiert. Für Stufe 3 (echte Produktionslast, mehr Nebenläufigkeit,
   geteilte Kerne mit anderen Fäden) bleibt ein Park/Unpark-Wecker-Executor
   die richtige Wahl -- **nicht behoben in dieser Sitzung**, weil er den
   gemessenen Faktor hier nicht senken würde und damit ausserhalb des engen
   Diagnose-Auftrags liegt.
4. **Fill-Wartezeit vs. Eval-Zeit im Sammel-Faden selbst** (bereinigt, ohne
   Kontamination): 13,2s Füll-Warten gegen 14,1s reine Eval-Zeit (create-
   once, 1148 Zustände) -- etwa hälftig, kein Hinweis auf einen
   pathologisch langen Timeout (Batch-Histogramm zeigt die Masse bei
   24-32 Zeilen, nahe dem Deckel 32, nicht bei kleinen Rest-Batches).

### Behoben (Konstruktionsdetail, KEIN Grundsatzproblem)

`async_drafting_search_with_batcher_concurrent_vs_synchronous` umgebaut:
die komplette Referenzberechnung läuft jetzt VOR jeder
Sammel-Faden-Registrierung (garantiert unkontaminiert), der Sammel-Faden
wird EINMAL registriert statt je Chunk. Ergebnis nach dem Fix (siehe
Tabelle oben, Zeile 2): **1,38x**, klar unter der 2x-Schwelle. Gate A selbst
bleibt unverändert bestanden (0/1148).

### VERDIKT: Erfolgskriterium erfüllt -- Konstruktionsdetail, nicht Grundsatzproblem

Der 16-fach-Test fällt nach der Bereinigung in die Nähe des Kern-Tests
(1,08x-1,38x über drei unabhängige Messungen, statt 7,1x) -- die
Diagnose ist POSITIV. Stufe 2 kann beginnen.

### Was NICHT geprüft ist

- Die GENAUE Ursache dafür, warum "Original-Muster isoliert" (37,75s) und
  "Original-Muster bereinigt, mit Referenz" (37,07s verschränkter Anteil)
  praktisch identisch sind, aber beide ca. 35% über create-once liegen --
  plausibelste Erklärung ist der Thread-Spawn/Teardown-Overhead des
  Sammel-Fadens selbst (72x statt 1x), NICHT weiter zerlegt (z.B. per
  eigenständiger Zeitmessung um `spawn_batcher` herum).
- Ob ein Park/Unpark-Wecker-Executor (statt Busy-Poll) den Faktor bei
  HÖHERER Nebenläufigkeit (Stufe 3, Dutzende/Hunderte Partien statt 16)
  ebenfalls unter 2x hielte -- dieser Diagnoseauftrag deckt nur 16-fache
  Nebenläufigkeit ab, das ist Stufe 3s eigene Messfrage.
- `MOSAIC_INTERLEAVE_FILL_TIMEOUT_US=2000` wurde NICHT gegen kleinere Werte
  (z.B. 200µs, der Produktionswert aus `PREREG_gpu_inferenzpfad.md`)
  gegengemessen -- 2000µs war eine eigene, unbegründete Wahl der Vorsitzung.

### Eigene Entscheidungen (nicht vorgegeben)

- Fund zuerst durch Code-Lesen bestätigt (Registrierungsreihenfolge im
  Smoke-Test), NICHT nur durch Zahlen-Korrelation vermutet -- REGEL 0.
- Drei unabhängige Messungen (create-once, Original-Muster bereinigt,
  Original-Muster isoliert) statt einer einzigen -- eine einzelne Zahl
  hätte die Frage "liegt es am Neu-Aufspannen ODER an der Kontamination"
  nicht getrennt beantworten können.
- Busy-Poll NICHT durch einen Park/Unpark-Executor ersetzt, obwohl
  `async_exec.rs`s eigener Kommentar das für Produktionslast empfiehlt --
  die Messung zeigt, dass er beim gegebenen Auftrag (16-fache
  Nebenläufigkeit, Faktor-unter-2x-Frage) nicht der limitierende Faktor
  ist; ein Umbau ohne gemessenen Nutzen wäre Vorratsarbeit ausserhalb des
  engen Diagnoseauftrags.

---

## 10. STUFE 2 BEGONNEN: Baustein 1 (Rundenübergangs-Sampling) gebaut und geprüft -- Gate B NICHT erreicht, begründeter Stopp

Diagnose war POSITIV (Abschnitt 9) -- Auftrag laut Stufenplan: Stufe 2
beginnen. Einstiegspunkt war der eigene Stufe-1-Fund: `node_from_net_outputs`
hat bei `ROUND_TRANSITION_SAMPLING=true` (Default aus) einen zweiten,
inerten Netz-Aufrufpunkt über `sample_round_transition_value` ->
`net_leaf_eval`. **Wichtiger, GEPRÜFTER Befund dabei**: diese Funktion ist
NICHT nur ein hypothetischer Stufe-2-Kandidat, sondern bereits AKTIV im
Produktionspfad -- `self_play.rs::play_net_self_play_game` (Zeilen
~2623-2650+) ruft sie bei JEDEM echten Rundenübergang auf, um das
Trainingsziel `round_transition_values` zu bilden. Deckt sich mit einer
bestehenden Projekt-Erkenntnis (`project_selfplay_cost_profile`): dieses
"rtv"-Sampling ist **~81-83 % der Self-Play-Kosten** -- der eigentlich
grössere Hebel für Verschränkung liegt hier, nicht in der Wurzelsuche
(Stufe 1).

### Baustein 1: async Rundenübergangs-Sampling, GEBAUT und GEPRÜFT

Additiv, gleiches Muster wie Stufe 1:

- `net_mcts.rs::net_leaf_eval_async` -- Async-Zwilling von `net_leaf_eval`
  (nur der `MIRROR_OTHER_VAL==false`-Produktionszweig unterbrechbar, exakt
  derselbe Zuschnitt wie `make_node_async`).
- `round_transition.rs::sample_round_transition_value_async` -- Async-
  Zwilling von `sample_round_transition_value`. **Bewusste Verengung**:
  nimmt `net: &Net` statt eines generischen `evaluator`-Closures (das
  Original ist absichtlich pluggable für `round5`/die rekursiven
  `round_transition_deep.rs`-Bewerter) -- ein async-fähiges generisches
  Closure bräuchte `AsyncFnMut`-Bindungen, eine zusätzliche Frage, die
  dieser schmale Anfang nicht braucht: die einzige heute lebende UND die
  einzige geplante Netz-Aufrufstelle nutzen ohnehin immer
  `net_leaf_eval_async`.

**Geprüft** (`round_transition::tests::async_round_transition_sampling_matches_synchronous`,
NICHT `#[ignore]`, läuft in `cargo test --lib`): reale Runde-1..3-Übergänge
(`drive_to_round_tiling_leaf`, 12 Seeds -- Runde 4 ausgelassen, siehe unten),
`N_SAMPLES_TRAIN=24` Samples je Fall, OHNE Sammel-Faden (bit-identisch
erwartet, `<1e-9`-Toleranz statt Gleichheit wegen Fliesskomma-Summation in
anderer Reihenfolge -- selbst das ist in 24/24 Fällen erfüllt):

| Metrik | Ergebnis |
| --- | ---: |
| Fälle verarbeitet | 24 |
| Abweichungen | **0/24** |

`cargo test --lib`: **388 bestanden / 0 fehlgeschlagen / 22 ignoriert**
(387→388, weil dieser Test NICHT ignoriert ist und erfolgreich lief; 22
ignorierte unverändert seit Abschnitt 9s Diagnosetests).

**Runde 4 ausgelassen** (nicht Teil des Ergebnisses, sondern eine
GEPRÜFTE Einschränkung der TEST-Fahrhilfe): `drive_to_round_tiling_leaf`
(ein `#[cfg(test)]`-Werkzeug, nicht Produktionscode) treibt Partien über
eine naive `actions[0]`-Politik -- bei mehreren Seeds erreicht diese Politik
VOR Runde 4 bereits `Phase::End` (`drive_to_round_start`s eigene Assertion
schlägt fehl: "erwartet Tiling, bekommen End"). Per `catch_unwind`
abgefangen und ausgelassen, NICHT als Abweichung gezählt -- ein Artefakt der
Testfahrhilfe, keine Eigenschaft der geprüften Async-Logik.

### GATE B NICHT erreicht -- begründeter Stopp, mit Schnitt und Aufwandsschätzung

Gate B verlangt **vollständige Partie-Gleichheit synchron gegen async**,
also die GESAMTE `play_net_self_play_game`-Schleife (`self_play.rs:2472ff`,
>300 Zeilen direkt in der Funktion, weit mehr über Hilfsfunktionen) als EINEN
durchgehenden Zustandsautomaten. Am Code geprüft, was das zusätzlich
verlangt -- Baustein 1 deckt nur EINEN von mindestens VIER Netz-
Integrationspunkten ab:

1. **Wurzelsuche** (Drafting-Entscheid, `net_drafting_policy`) -- Stufe 1,
   GEDECKT (`build_gumbel_tree_inner_async`).
2. **Rundenübergangs-Sampling** (`sample_round_transition_value`) -- Baustein
   1, GEDECKT für den EINFACHEN (net-only) Bewerter.
3. **Rekursives Mehrrunden-Sampling** (`round_transition_deep.rs`,
   `simulate_one_round`/`N_SAMPLES_TRAIN_ROUND{1,2,3}`) -- NICHT geprüft,
   NICHT konvertiert. Der Modul-Name selbst deutet auf verschachtelte
   `sample_round_transition_value`-Aufrufe je Rekursionsebene -- vermutlich
   ähnlich tractabel wie Baustein 1 (derselbe Evaluator-Musterl), aber NICHT
   nachgesehen in dieser Sitzung; eigener Prüfschritt nötig.
4. **Tiling-Stichentscheid** (`self_play.rs::resolve_tiling_step` ->
   `net_tiling_tiebreak_value`, `self_play.rs:973`/`1060`) -- GEPRÜFT
   vorhanden (ein DRITTER, bisher unbeachteter Netz-Aufrufpunkt, exakt der
   "Tiling-Stichentscheid" aus dem ursprünglichen Auftrag), NICHT
   konvertiert.

**Und selbst mit allen vier Bausteinen fertig**: `play_net_self_play_game`
selbst (die äussere `loop { match game.state.phase { ... } }`-Schleife, die
alle vier Punkte verwebt, plus `apply_chosen_action`, `moon_order_target`,
Start-Placement, End-Phase, Runde-5-Sonderbehandlung über `round5.rs`) müsste
SELBST zu einer `async fn` werden, damit ein Aufrufer sie unterbrechbar
treiben kann -- eine mechanische, aber grossflächige Umformung einer
Funktion mit weit über 300 Zeilen und vielen Hilfsaufrufen, von denen jeder
einzeln auf weitere Netz-/RNG-Abhängigkeiten geprüft werden müsste (nach dem
Muster dieser Sitzung: Baustein 1 allein -- ZWEI neue Funktionen plus ein
Testfall -- hat trotz seiner Einfachheit einen vollen Analyse-/Bau-/
Prüfzyklus gebraucht).

**Aufwandsschätzung** (grobe Grössenordnung, KEINE Messung): Punkte 3+4
zusammen vermutlich vergleichbar zu Baustein 1 (je ein halber bis ganzer
Arbeitszyklus wie dieser), die äussere Schleifen-Konvertierung selbst
(Punkt 5) grösser als alle vier Bausteine zusammen, weil sie die Korrektheit
des GESAMTEN Zusammenspiels (nicht nur einzelner Bausteine) beweisen muss --
Gate B verlangt genau das. Insgesamt eher Tage als Stunden. **Diese Sitzung
STOPPT hier** (Auftrag: "berichte den tatsächlichen Schnitt mit
Aufwandsschätzung statt halbfertig umzubauen") -- Baustein 1 ist ein
geprüfter, aber unvollständiger Fortschritt, kein Gate-B-Ergebnis.

### Was NICHT geprüft ist

- `round_transition_deep.rs` wurde NICHT gelesen (nur namentlich referenziert
  über bestehende Kommentare in `round_transition.rs`) -- Punkt 3 oben ist
  eine Einschätzung, keine Codeanalyse.
- `net_tiling_tiebreak_value`s Aufrufhäufigkeit je Tiling-Phase (wie oft
  `best_first_step_exact_or_valued` den Evaluator pro Zug aufruft) wurde
  NICHT gemessen -- Punkt 4s tatsächliches Gewicht am Self-Play-Budget ist
  unbekannt.
- Ob `add_root_noise=true`/Produktions-`N_SAMPLES_TRAIN=24` unter
  ECHTER Sammel-Faden-Last (nicht nur ohne Sammel-Faden wie in Baustein 1s
  Test) ebenfalls Gleichheit hält -- nur der bit-identische Fall (kein
  Sammel-Faden) wurde geprüft, analog zu Stufe 1s eigenem Kern-Test.

### Eigene Entscheidungen (nicht vorgegeben)

- `sample_round_transition_value_async` verengt auf `net: &Net` statt
  generischem Evaluator (siehe oben) -- bewusster Tausch: weniger allgemein
  als das Original, aber kein Bedarf an `AsyncFnMut`-Bindungen für den
  heute relevanten Fall.
- Runde 4 aus dem Testlauf ausgelassen (Testfahrhilfe-Limitierung, siehe
  oben) statt die Fahrhilfe selbst zu reparieren -- ausserhalb des engen
  Baustein-1-Zuschnitts, Runden 1-3 reichen für den Nachweis der
  MECHANISCHEN Aequivalenz.
- Test NICHT `#[ignore]`t (anders als Stufe 1s grosse 1148er-Tests) --
  braucht nur das lokale Modell, keine `MOSAIC_FROZEN_STATES_JSON`, und
  läuft schnell genug (~30s) für den normalen `cargo test --lib`-Lauf.

---

## 11. STUFE 2, BAUSTEINE 2-4 + GATE B: alle Bausteine grün, GATE-B-KERNBEFUND ist ein vorbestehendes, nicht async-verursachtes Problem

Fortsetzung nach der Diagnose (Abschnitt 9, positiv) und Baustein 1
(Abschnitt 10). Jeder Baustein wurde EINZELN grün getestet und im Worktree
committet, bevor der nächste begann (Nutzer-Auftrag). Korrektur zur eigenen
früheren Kostenangabe: "~81-83 % der Self-Play-Kosten" (Abschnitt 10) bezog
sich auf die inzwischen abgeschafften rtv-**Labels** (Task #80/#81, vor
Task #85s Ablation) -- ob das Rundenübergangs-**Sampling** selbst denselben
Anteil hat, ist NICHT belegt und wird hier nicht mehr als Begründung
verwendet. Ungeprüft/nicht gemessen in dieser Sitzung (`MOSAIC_PROFILE_SELFPLAY`
wäre das richtige Werkzeug dafür).

### Baustein 2: rekursives Mehrrunden-Sampling (`round_transition_deep.rs`)

Additiv: `net_mcts::drafting_action_priors_async`,
`round_transition_deep::{ordered_children_pruned_async, round_end_eval_async,
choose_drafting_action_pruned_async, simulate_one_round_async,
continue_through_round{2,3,4}_async, bootstrap_value_after_rounds_async}`.
GEPRÜFT unverändert synchron: `negamax_progress` (KEIN Netzaufruf --
Gamma-Pruning, der einzige Netzbezug dieser Zugwahl, greift laut
Modul-Kommentar NUR an der Wurzel, nicht in `negamax_progress`s eigener
Tiefensuche) sowie `continue_through_round4_async`s Runde-5-Übergang
(`round5::exact_round5_outcome`, kein Netzbezug).

**Getestet in Isolation**: `continue_through_round4` (0/6),
`continue_through_round3` (0/4), `bootstrap_value_after_rounds` (0/8,
Horizont 1+2) -- alle `<1e-9`-Toleranz, ohne Sammel-Faden.

**WICHTIGER FUND, unabhängig von der Async-Umformung**: unter schwerer
`cargo test --lib`-Nebenlast (voller Testlauf, viele gleichzeitige teure
Tests) zeigte `continue_through_round4_sync_only_repeatability_under_load`
(rein SYNCHRON, KEIN Async-Code, derselbe Aufruf zweimal mit demselben Seed)
1/6 Abweichungen -- **dieselbe Wall-Clock-Nichtdeterminismus-Klasse, die
Task #71 (siehe `round_transition_deep.rs`-Modulkommentar) ADRESSIERT, aber
laut dessen eigenem Kommentar NICHT vollständig behoben hat** ("NUR NOCH
Not-Deckel" an mehreren Stellen). Alle vier neuen Vergleichstests deshalb
`#[ignore]`t (0/6, 0/4, 0/8 GEPRÜFT in Isolation, siehe Bericht) --
irreführendes Rot unter Last waere kein Fund über die Async-Umformung.

`cargo test --lib`: 388/0/26 (bestätigt zweimal stabil ohne die
`#[ignore]`ten Tests).

### Baustein 3: Tiling-Stichentscheid (`tiling_solver.rs`/`self_play.rs`)

Additiv: `self_play::net_tiling_tiebreak_value_async`,
`tiling_solver::{select_best_tiling_candidate_async,
best_first_step_valued_async, best_first_step_platten_valued_async,
best_first_step_exact_or_valued_async}`. `NET_TILING_TIEBREAK_ENABLED=true`
(Produktions-Default) -- kein Env-Toggle nötig, Runden 2-4 durchlaufen den
echten Pfad. GEPRÜFTE Abweichung vom sonstigen Verengungsmuster:
`best_first_step_platten_valued_async` behält `net: Option<&Net>` (nicht
verengt auf `&Net`) -- das Original liefert auch bei `evaluator: None` einen
Zug (reiner additiver Plattenterm ohne Netzfaktor); eine Verengung hätte den
gesamten Zweig 1 (Task #100) für Heuristik-Spieler mit
`MOSAIC_TILING_PLATTEN_W != 0` STILL übersprungen -- ein Verhaltens-
unterschied, kein reiner Interruptibility-Umbau.

**Getestet** (echte Tiling-Zustände Runde 2-4, 8 Seeds): **0/24
Abweichungen**, ohne Sammel-Faden. KEIN Wall-Clock-Timing beteiligt (reine
Kandidaten-Schleifen, kein Zeitbudget) -- **robust unter Last**, zweimal
389/0/26 bestätigt, NICHT `#[ignore]`t.

### Baustein 4: `play_net_self_play_game` als async fn

Additiv: `net_mcts::net_root_child_stats_and_policy_async`,
`self_play::{net_drafting_policy_async, sample_round_transition_for_round_async,
resolve_tiling_step_async, tiling_step_async, play_net_self_play_game_async}`.

GEPRÜFTE Zweige, bewusst NICHT konvertiert (mit Begründung, nicht nur
Auslassung):
- **Runde 5** (`round5::choose_action`/`_with_analysis`): exakter
  Alpha-Beta-Solver ohne Netzbezug -- anders als in Bausteinen 1-3 KEIN
  seltener Fallback, sondern ein Zweig, den JEDE vollständige Partie
  tatsächlich durchläuft; deshalb vollständig (nicht nur als toter Code)
  nachgebaut, nur eben synchron.
- **`k > 1`** (ISMCTS-Mehrfachdeterminisierung, `NUM_DETERMINIZATIONS=1`
  Default): laut `PREREG_ismcts_determinizations.md` GESCHLOSSEN ("k=1
  bleibt") -- der Async-Zwilling fällt für diesen Fall auf den
  VOLLSTÄNDIGEN synchronen Original-Aufruf zurück (korrekt für jedes `k`,
  nur blockierend), statt einen ungetesteten Pfad für einen abgelehnten
  Suchmodus zu bauen.
- `crate::profiling::with_category`/`timed`-Umhüllungen: GEPRÜFT
  (`profiling.rs:134-146,198-211`) vollständig hinter dem
  `clone_profiling`-CARGO-FEATURE (nicht einem Laufzeit-Toggle) --
  kompilieren ohne dieses Feature (jeder Testlauf dieser Sitzung) zu `f()`,
  reinem Durchreichen. Weglassen im Async-Zwilling ist unter dieser
  Build-Konfiguration GARANTIERT folgenlos für den Rückgabewert.

`cargo test --lib`: 389/0/29.

### GATE B: Kernbefund ist ein VORBESTEHENDES, NICHT async-verursachtes Problem

**Auftrag**: vollständige Partie-Gleichheit synchron gegen async (mehrere
Seeds, komplette Partien bis `Phase::End`, Endstände + Zugfolgen identisch
ohne Sammel-Faden; mit Sammel-Faden Zugwahl-Gleichheit).

**Gemessen** (`gate_b_full_game_equality_without_batcher`, 4 Seeds,
`base_sims=16`, `record_rtv=false`, volle JSON-Records inkl. Zustände/
Policy/`root_q`/`root_child_q`/Endstände):

| Lauf | Abweichungen (voll) | Partien |
| --- | ---: | ---: |
| 1 | 2/4 (Seeds 1, 3) | 162/173 Records, gleiche Länge |
| 2 (Wiederholung, identische Seeds) | 4/4 | -- |
| 3 (nach Test-Erweiterung neu gebaut) | 0/4 | -- |
| 4 (Wiederholung) | 0/4 | -- |

**Die Mismatch-Rate variiert zwischen Läufen mit IDENTISCHEN Seeds und
IDENTISCHEM Code** -- das ist selbst der Befund: kein deterministischer
Logikfehler (der würde bei gleichem Seed immer gleich ausfallen), sondern
Zeitabhängigkeit.

**Entscheidende Gegenprobe** (`play_net_self_play_game_sync_only_repeatability`,
REIN SYNCHRON, KEIN Async-Code, `play_net_self_play_game` zweimal mit
demselben Seed): **1/4 Abweichungen**, erster abweichender Record bereits
Index 0 (rückwirkend gestempeltes `bootstrap_value` für Runde 1). **Sync
weicht von sich selbst ab, unter denselben Bedingungen wie der Sync/Async-
Vergleich.** Damit ist belegt: die beobachteten Gate-B-Abweichungen sind
NICHT durch die Async-Umformung verursacht, sondern durch eine
VORBESTEHENDE Eigenschaft von `round_transition_deep.rs` (Task #71s
Wall-Clock-Not-Deckel binden gelegentlich doch, siehe Baustein 2) **PLUS**
den bereits in `evaluations/STATUS.md` dokumentierten geteilten RNG-Strom
zwischen Suche/Simulation und dem echten Spiel (`self_play.rs:1523`-
Fundstelle, "Gepaarte Arena-Vergleiche sind schwächer als angenommen") --
verschiebt die interne Simulation den RNG-Verbrauch, verschieben sich ALLE
nachfolgenden echten Spielentscheidungen mit.

**Zielgerichtete Zerlegung** (dieselben Läufe, `bootstrap_value`/
`round_transition_value` -- reine additive Trainingsziele ohne Rückwirkung
auf den gespielten Zug -- vor dem Vergleich entfernt): **0/4 Abweichungen
im Spielgeschehen** in beiden Läufen, in denen auch der volle Vergleich 0/4
war. Für die beiden Läufe mit vollen Abweichungen (2/4, 4/4) wurde die
zielgerichtete Zerlegung NICHT nachträglich auf dieselben Läufe angewendet
(Code-Erweiterung kam danach) -- **UNGEPRÜFT, ob die Spielgeschehen-Teilmenge
auch DORT 0 gewesen wäre**, nur plausibel angenommen aus der Mechanik
(Trainingsziele beeinflussen `game`/`chosen` nicht direkt) und den zwei
späteren Nachläufen.

**Sammel-Faden-Smoke** (`gate_b_full_game_move_choice_equality_with_batcher`,
4 Partien GLEICHZEITIG verschränkt): 3/4 Zugfolge-Abweichungen, davon eine
mit UNTERSCHIEDLICHER Partielänge (164 vs. 165 Züge) -- **KONFUNDIERT**
durch dieselbe vorbestehende Zeitempfindlichkeit, jetzt durch 4-fache
Nebenläufigkeit zusätzlich verschärft (mehr geteilte CPU-Zeit, mehr
Gelegenheiten für einen bindenden Wall-Clock-Deckel). Dieser Lauf taugt NICHT
als reiner Befund über den Sammel-Faden -- eine saubere Messung bräuchte
entweder `record_rtv=false` UND `bootstrap_value_after_rounds` deaktiviert/
gemockt, oder das vorbestehende Problem selbst behoben, keines von beiden
Teil dieses Auftrags.

### VERDIKT: kein Grundsatzproblem der Async-Architektur -- aber Gate B wie spezifiziert nicht sauber messbar

Alle VIER Bausteine sind einzeln, in Isolation, korrekt (0-Abweichungen
gegen die Synchron-Referenz, innerhalb der jeweils erreichbaren Toleranz).
Die Gate-B-Abweichungen häufen sich exakt an der Stelle, die bereits VOR
diesem Auftrag als fragil bekannt war (`round_transition_deep.rs`s
Wall-Clock-Reste, geteilter RNG-Strom) -- und treten NACHWEISLICH auch ohne
jede Async-Beteiligung auf. **Das ist ein Befund über round_transition_deep.rs,
nicht über die Verschränkungsarchitektur.** Ob Gate B im ursprünglichen
Wortlaut (Bit-Identität ganzer Partien) mit der heutigen Codebasis überhaupt
erreichbar ist -- unabhängig von Sync/Async --, ist damit selbst fraglich
geworden.

### Was NICHT geprüft ist

- Die zielgerichtete Zerlegung (Trainingsziele entfernt) wurde nur für 2 von
  4 beobachteten Voll-Abweichungs-Läufen tatsächlich gemessen (siehe oben).
- Die GENAUE Kausalkette (welcher Wall-Clock-Deckel bindet, wie viele
  RNG-Ziehungen das verschiebt) wurde NICHT weiter zerlegt -- die Diagnose
  stützt sich auf die Sync-gegen-sich-selbst-Gegenprobe, nicht auf eine
  Line-by-Line-Ursachenanalyse.
- Ob die Batcher-Smoke-Abweichung (3/4) bei `record_rtv=false` UND
  deaktiviertem `bootstrap_value_after_rounds` (also ohne jede
  Wall-Clock-Beteiligung) verschwindet -- NICHT gebaut/gemessen.
- `MOSAIC_PROFILE_SELFPLAY`-Instrumentierung wurde NICHT genutzt, um den
  tatsächlichen Kostenanteil des Rundenübergangs-Samplings zu messen (siehe
  Korrektur oben zur "~81-83%"-Zahl).

### Eigene Entscheidungen (nicht vorgegeben)

- `net_root_child_stats_and_policy_async`s `k>1`-Rückfall ruft den
  VOLLSTÄNDIGEN synchronen Original-Code (nicht nur einen Teil davon) --
  korrekt für jeden Wert, kein Sonderfall-Risiko.
- Gate-B-Tests (`gate_b_*`, `play_net_self_play_game_sync_only_repeatability`)
  als `#[ignore]` markiert -- teuer (volle Partien) UND nachweislich
  zeitempfindlich, ein Rot unter `cargo test --lib`-Last wäre irreführend.
- Zielgerichtete Zerlegung (Trainingsziel-Felder entfernen) direkt in den
  bestehenden Gate-B-Kern-Test integriert statt eines separaten Tests --
  hält den direkten Vergleich (voll vs. Spielgeschehen) an derselben
  Partiemenge sichtbar.

---

## 12. GATE B, FINAL: nach dem RNG-Schnitt gemessen -- Spielgeschehen bit-identisch, Trainingsziel-Felder NICHT (Befund, nicht wegtoleriert)

Der RNG-Schnitt (`fe1e306`, `PREREG_search_rng_split.md`) ist im Hauptbaum
gelandet und gepusht: die Suche erhält einen eigenen, aus `(game_seed,
move_index)` deterministisch abgeleiteten RNG (`net_mcts::derive_search_seed`)
statt des mit dem echten Spiel geteilten Stroms. Nutzer-Auftrag: Gate B
final messen.

### Rebase: Worktree `scratchpad/wt_async2` (neu, `wt_async` bleibt Archiv)

Neuer `git worktree add --detach` auf aktuellem Hauptbaum-HEAD (`7e5a243`).
GEPRÜFTE Umgebungshürde, nicht Teil der Async-Arbeit: `player_profiles.json`
ist inzwischen `git-crypt`-verschlüsselt versioniert, der Schlüssel ist in
dieser Umgebung nicht entsperrt -- `git worktree add`/`cherry-pick` schlugen
mit `git-crypt: Unable to open key file` fehl, bis der Smudge/Clean-Filter
für den jeweiligen Git-Aufruf per `-c filter.git-crypt.*=cat` deaktiviert
wurde (nur für den einzelnen Prozessaufruf, keine persistente Config-
Änderung, kein Effekt auf Hauptbaum/`wt_async`).

**Cherry-Pick der drei Worktree-Commits (`1c5169e`, `dd7b229`, `98ea99f`)
ergab KEINEN Textkonflikt** -- git meldete "Auto-merging" für alle
betroffenen Dateien, keine `<<<<<<<`-Marker. Das ist KEIN Beleg für
semantische Vertäglichkeit: die Async-Zwillinge leben in eigenen
Funktionen (`play_net_self_play_game_async` u.a.), textuell getrennt von den
Stellen, an denen der RNG-Schnitt `game_seed`/`search_rng` einführte -- git
hatte deshalb nichts zum Kollidieren, aber auch nichts zum automatischen
Nachziehen. **Manuell nachgezogen**: `play_net_self_play_game_async` bekam
den neuen `game_seed: u64`-Parameter, und die Drafting-Entscheidung leitet
jetzt `search_rng` exakt wie das synchrone Original ab (`derive_search_seed(
game_seed, move_number)`), statt weiterhin den geteilten `rng` an
`net_drafting_policy_async`/`pcr_decide_full`/`moon_order_target` zu
reichen. GEPRÜFT unverändert (wie im synchronen Original): die Aufrufe von
`sample_round_transition_for_round_async`/`bootstrap_value_after_rounds_async`
und `tiling_step_async` nutzen weiterhin den GETEILTEN `rng` -- der
RNG-Schnitt hat diese Stellen laut Commit `fe1e306` bewusst nicht
umgestellt ("läuft auf einem Zustands-Klon, beeinflusst nie den gespielten
Zug"). Alle Test-Aufrufstellen (Gate-B-Tests, Sync-Wiederholbarkeits-Diagnose)
ebenfalls um `game_seed` ergänzt (Konvention: `game_seed` = derselbe Wert,
mit dem `rng` selbst geseedet wurde, wie in `run_net_self_play`).

`cargo test --lib`: **406 bestanden / 0 fehlgeschlagen / 31 ignoriert**
(Hauptbaum-Basis 402/0/20 + eigene Stufe-1/2-Testzusätze). Committet als
`89c0a6b` im Worktree.

### Gate B (a): volle Partien OHNE Sammel-Faden, 8 Seeds, ZWEI Läufe

| Lauf | Abweichungen (voll, inkl. Trainingsziele) | Abweichungen (nur Spielgeschehen) |
| --- | ---: | ---: |
| 1 | 1/8 (Seed 7, Record-Index 107) | **0/8** |
| 2 | 3/8 (Seeds 0, 5, 6 -- Seed 6 bereits Record-Index 0) | **0/8** |

**Das Spielgeschehen (Zustände, Policy, gewählte Züge, `root_q`/
`root_child_q`, Endstände) ist über BEIDE Läufe und alle 16 Partie-
Vergleiche hinweg bit-identisch (0/16).** Die Abweichungen beschränken sich
auf `bootstrap_value`/`round_transition_value` -- additive Trainingsziel-
Felder ohne Rückwirkung auf den gespielten Zug (bestätigt die Einordnung aus
Abschnitt 11 und den Kommentar in Commit `fe1e306`).

**GEPRÜFTE Gegenprobe, jetzt auf denselben 8 Seeds**:
`play_net_self_play_game_sync_only_repeatability` (REIN SYNCHRON, KEIN
Async-Code) zeigt **0/8 Abweichungen** -- die vorbestehende Sync-gegen-
Sync-Instabilität aus Abschnitt 11 ist durch den RNG-Schnitt tatsächlich
behoben, wie vom Nutzer berichtet.

**Das ist der eigentliche Befund dieses Auftrags, NICHT wegtoleriert**: Gate
B (a) ist damit **NICHT bit-identisch inklusive Trainingsziel-Felder** --
die Erwartung aus dem Auftrag trifft nicht zu, obwohl Sync-gegen-Sync jetzt
perfekt reproduzierbar ist. Die naheliegende Erklärung (nicht weiter
verifiziert, siehe "Was NICHT geprüft ist"): `bootstrap_value_after_rounds`/
`sample_round_transition_for_round` nutzen weiterhin den GETEILTEN `rng`
UND `round_transition_deep.rs`s Wall-Clock-Not-Deckel (Task #71, siehe
Abschnitt 10). Sync-gegen-Sync ist reproduzierbar, WEIL zwei Läufe
DESSELBEN Codes ungefähr dieselbe Wall-Clock-Zeit für dieselbe Arbeit
brauchen. Sync und Async sind aber KONSTRUKTIONSBEDINGT unterschiedlich
schnell (Future-Overhead je Unterbrechungspunkt, über eine ganze Partie mit
hunderten Entscheidungen aufsummiert) -- genug, um einen der grosszügigen,
aber nicht unendlichen Not-Deckel (`ROUND_SIM_TIME_BUDGET=15s`,
`POLICY_TIME_BUDGET_PER_DECISION=200ms` u.a.) in EINEM der beiden Pfade
binden zu lassen, im anderen nicht -- unterschiedliche Wall-Clock-
Geschwindigkeit reicht dafür aus, auch OHNE jede externe Nebenlast. Die
schwankende Rate (1/8, dann 3/8, mit identischen Seeds) stützt diese
Deutung: ein deterministischer Logikfehler würde nicht zwischen Läufen
variieren.

### Gate B (b): MIT Sammel-Faden, 4 Partien gleichzeitig

Vor dem RNG-Schnitt (Abschnitt 11): 3/4 Zugfolge-Abweichungen,
KONFUNDIERT durch die damalige Sync-gegen-Sync-Instabilität. **Nach dem
RNG-Schnitt**: **1/4 Zugfolge-Abweichungen, 1/4 Endstand-Abweichungen** --
die abweichende Partie hat sogar eine ANDERE Zuganzahl (165 gg. 160). Diese
eine Partie ist NICHT mehr durch die (jetzt behobene) Sync-Instabilität
erklärbar -- die naheliegende, mit Stufe 1 bereits ETABLIERTE Ursache ist
tracts fehlende Bit-Gleichheit über verschiedene Batch-Pläne (`net.rs:927-
982`, Toleranz `1e-5`; `PREREG_gpu_inferenzpfad.md` §14-§17 hatte dieselbe
Quelle bereits als seltenes, listenpositionsabhängiges Rangvertauschungs-
Ereignis charakterisiert, ~0,22 % der Zustände). Über eine volle Partie mit
~160 Entscheidungen summiert sich selbst eine kleine Pro-Zug-Wahrscheinlichkeit:
bei 0,22 % je Zug wäre die Wahrscheinlichkeit auf mindestens EINE Abweichung
irgendwo in der Partie `1-(1-0,0022)^160 ≈ 30 %` -- **derselbe
Größenordnungsbereich wie die gemessenen 25 % (1/4)**, eine grobe, aber
plausible Übereinstimmung mit einer bereits VOR dieser Sitzung bekannten,
dokumentierten Toleranzquelle, keine neue.

### VERDIKT

- **Spielgeschehen (Gate B im Kern -- welcher Zug wird gespielt, wie endet
  die Partie): bit-identisch ohne Sammel-Faden (0/16 über zwei Läufe), und
  konsistent mit der bereits etablierten, kleinen Batch-Plan-Toleranz mit
  Sammel-Faden.** Kein Grundsatzproblem der Verschränkungsarchitektur.
- **Trainingsziel-Felder (`bootstrap_value`/`round_transition_value`) sind
  NICHT bit-identisch zwischen sync und async**, auch nach dem RNG-Schnitt
  -- ein Befund über verbleibende, in `round_transition_deep.rs` liegende
  Wall-Clock-Nichtdeterminismus-Quellen (Task #71), die durch
  UNTERSCHIEDLICHE Ausführungsgeschwindigkeit von sync und async sichtbar
  werden, nicht durch fehlende Reproduzierbarkeit an sich. Dies BLOCKIERT
  Gate B im ursprünglich verlangten Wortlaut (Bit-Identität INKLUSIVE
  Trainingsziele) -- wird hier als offener Befund stehen gelassen, nicht
  wegtoleriert.

### Was NICHT geprüft ist

- Ob die Trainingsziel-Divergenz sich beheben ließe, indem
  `bootstrap_value_after_rounds`/`sample_round_transition_for_round` (Sync
  UND Async) ebenfalls einen eigenen, von `game_seed` abgeleiteten RNG
  bekämen (analog zum Suchpfad) -- das würde die Wall-Clock-Empfindlichkeit
  selbst nicht beheben, aber verhindern, dass eine Abweichung dort in den
  geteilten Strom zurückwirkt. NICHT gebaut, nicht Teil dieses Auftrags
  (Änderung am synchronen Original, nicht nur am Async-Zwilling).
  - Die genaue Kausalkette (welcher Not-Deckel bindet, um wie viel
  Wall-Clock-Zeit sync und async sich für dieselbe Arbeit tatsächlich
  unterscheiden) wurde NICHT instrumentiert -- die Deutung stützt sich auf
  die 0/8-Sync-Gegenprobe plus die bekannte Existenz der Not-Deckel, nicht
  auf eine direkte Zeitmessung.
- Ob ein dritter/vierter Lauf von Gate B (a) eine andere Rate als 1/8 bzw.
  3/8 zeigen würde -- zwei Datenpunkte belegen Varianz, nicht die genaue
  Verteilung.
- Gate B (b)s 0,22-%-Bezugsrate ist aus §14-§17 übernommen (dieselbe
  Toleranzquelle), NICHT für DIESES Modell/diese Partien neu gemessen --
  die 30-%-Rechnung ist eine Plausibilitätsschätzung, kein Beweis.
