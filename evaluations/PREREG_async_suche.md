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

Das ist NICHT Weg B im Sinne von `PREREG_gpu_verlagerung.md` (Virtual Loss --
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
