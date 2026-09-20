# 🧩 Mosaic-AI: Tile-Drafting AlphaZero Environment

[![Rust](https://img.shields.io/badge/engine-Rust-orange.svg)](https://www.rust-lang.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-Deep%20Learning-ee4c2c.svg)](https://pytorch.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Mosaic-AI** is a complete reinforcement-learning framework for training
AlphaZero-style neural networks on a two-player tile-drafting and
dome-building board game with hidden information.

> **⚠️ Disclaimer (credit where credit is due):** This is a non-commercial
> learning and research project: a private digital reimplementation of the
> **_Azul Duel_** ruleset (game design by Michael Kiesling, © Plan B Games /
> Next Move Games), written from scratch to serve as a training environment
> for reinforcement learning. **The game design is not mine**; only the
> engine, the neural network and the training pipeline are. This project is
> not affiliated with, endorsed by, or connected to the publisher in any way,
> and it contains none of their artwork, rulebook text, or other assets; all
> trademarks belong to their respective owners. It is no substitute for the
> physical game: if you enjoy it, buy the original.

---

## Current Status

Champion: **`v31-b01`**, shown in the game as **Tessa** (promoted 2026-09-20),
Elo **1458** (95% CI [1414, 1510]) from 1,000 rated games, anchored at the frozen
heuristic artifact `models/frozen_heuristics/hv4_anchor` (Heuristic@150 = 1000,
`tools/elo_tracker.py report`). None of its four edges was stopped early. It beat
the previous champion 461:339 over two seeds, the anchor 45:5, and `v29-b09` two
generations back 79:71 -- the last of those well below what the other two would
predict, and recorded as such rather than smoothed over. `v31` is the final
generation; the technical name stays in the ladder and the files, `Tessa` is the
name the game shows.

**The cold-start question is settled.** `v30-b01` and `v30-b02` trained on the
same replay window with the same seed and the same recipe and differed in a
single factor, the start: 404:396 cold against 443:297 warm, a gap of 9.4
percentage points.

**Ratings live in segments.** Two engine corrections (the round-5 solver, then a
hull-evaluation fix) moved the anchor's own moves, and ratings are not
comparable across such a boundary; earlier segments are kept in
`archive/elo_history_pre_*.csv`. Since the second segment the anchor ships its
own wheel, so an engine change can no longer move the fixed point of the ladder,
and every change is checked against it move by move.

**Some defects are invisible to the measurement apparatus.** Self-play, arena
and gating compare two agents inside the *same* world model, so an error in the
shared model cancels out and costs zero Elo at any sample size. The dome-stack
bug found in September was of that kind, and a human playing the GUI found it,
not the pipeline. The list of places where the code discards information on
purpose is kept in
[`docs/architecture_reference.md`](docs/architecture_reference.md).

The engine ships as version 1.0.0 with this champion.

Full history, all measurements and the methodology rules:
[`evaluations/STATUS.md`](evaluations/STATUS.md); process diagrams:
[`docs/diagrams.txt`](docs/diagrams.txt) (render via
`python docs/render_diagrams.py`).

## Engine Core in Brief

- **Rust search** (`engine/src/net_mcts.rs`): Gumbel AlphaZero (Gumbel-Top-m Sequential Halving at the root), deterministic in arena/server, sampled
  in self-play (τ = 1 throughout; annealing was measured and brought no
  gain). Root width follows the budget: `m = clamp(round(sims/16), 4, 16)`,
  i.e. 16 at 400/600 sims and 9 at 150 sims (measured strength-neutral).
  The legacy PUCT path is still available behind `USE_GUMBEL_SEARCH`.

- **Network** (`engine/py/neural_net.py`): 2D encoder (`Mosaic2DNet`):
  conv branch over 79 binary 6x6 planes + flat branch over 755 features
  (744 up to `v28-b01`), fused into a 512-wide trunk. Both inputs are built
  once, in Rust (`engine/src/features.rs`), and exported to Python via PyO3;
  the Python twin builder remains as a test oracle and is bit-identical
  (`tools/probes/feature_parity_rust_python.py`, gate passed 2026-09-11). Heads: policy (406 actions), value
  (WDL: two logits -> P(win)), moon order, own points, opponent points,
  ownership, and optionally `endgame_margin` (auxiliary target: the
  round-5 solver's root value, recorded free of charge from self-play
  records; a budget-limited expectiminimax value with exact leaf
  scoring, not an exact minimax value). Aux heads are training signal
  only; the search never reads them.
- **Value target**: `VALUE_SCHEMA_VERSION=20`. `values_wdl` is a TD blend
  (`TD_LAMBDA=0.5`) of the bootstrap win probability at the next round
  transition and the actual game outcome. Bootstraps from pre-WDL
  generators are Platt-destretched first (A=0.0051, B=1.9269) so that old
  and new corpora carry the same semantics. The raw outcome is kept
  separately (`wdl_outcome`) and yields the **Brier score**, the only
  cross-arm comparable value metric; it also selects the checkpoint
  (`_brierbest`, re-validated in the arena).
- **Cache**: HDF5, planes and legal-move masks bit-packed (1 bit per field),
  ~2.7 KB per state; a 4.8 M-state window fits in ~13 GB.
- **Floor shaping** (`FLOOR_SHAPING_WEIGHT=0.3`, override
  `MOSAIC_FLOOR_SHAPING_W`): exact leaf-value additive against
  floor-penalty spirals; re-validated in the WDL era (0.15/0.6 sweep: H0).
  Plate shaping and value shrinkage were disproved and stay off.
- **Round 5**: Expectiminimax (`engine/src/round5.rs`): alpha-beta over
  the decision nodes plus chance nodes where the four fresh, still-hidden
  bonus chips get revealed (`MOSAIC_R5_CHANCE_NODES`, default on since
  2026-08-10). No network decisions in round-5 drafting, but the round is
  *not* full-information, and the search is *not* exact; exact is the
  leaf evaluation (optimal tiling plus plate scoring under a fixed dome
  grid; the node budget is 200). Its values feed training: the round-4
  bootstrap uses `round5::exact_round5_outcome`, and the optional
  `endgame_margin` head distils the round-5 root value.
- **Runtime knobs**: every experimental lever is an `MOSAIC_*` environment
  variable whose default reproduces the previous behaviour bit-for-bit
  (verified by a hash probe before use). Currently all of them are inert
  by measurement: aggression blend (w/λ), denial tie-break, floor-opponent
  bias, root-width override, tiling criterion, τ annealing.

## The Generation Cycle (Training Pipeline)

The heart of the project: how the next candidate generation is produced
from the reigning champion. Every step has a written pre-registration in
`evaluations/PREREG_*.md`: design **and** decision rule are fixed *before*
the run, so a result cannot be reinterpreted afterwards.

1. **Self-play in three classes** (generator = the champion of the previous
   generation). Policy targets are expensive, value targets are cheap, so they
   are bought separately, and the value half is split again by *how* the moves
   are chosen:

   ```bash
   # Base class: policy-carrying, greedy from move 1, one forced deviation
   python -u self_play.py --mode network --model models/alphazero_<gen>_brierbest.onnx        --spec models/<champion>.spec.json --games 4000 --sims 100        --version <gen>-policy --threads 11 --chunk 10 --per-file 10 --seed <s1>        --tau-argmax-from-move 1 --deviate-prob 1.0
   # Swarm a: value only, smooth action temperature (coverage)
   python -u self_play.py ... --value-only --version <gen>-value-tempc --seed <s2>        --action-temp 2 --deviate-prob 1.0
   # Swarm b: value only, one excursion per game, otherwise greedy (unbiased targets)
   python -u self_play.py ... --value-only --version <gen>-value-excursion --seed <s3>        --excursion-prob 1.0 --tau-argmax-from-move 1 --no-root-noise
   ```

   Measured on the v31 production run: 4.24 s per game for the base class,
   14.7 h for all three classes on one machine (`docs/measured_runtimes.md`);
   the eight search nodes added in v30 are most of the growth against the 9.9 h
   of v28. Note that `--games` counts excursion identities as well, so the
   excursion half needs the full number, not half of it.

2. **Replay window with generation rotation** (2,947 files, ~29,450 games):
   the new base class plus a seed-determined subset of the two previous
   generations as additional policy carriers (`data/policy_carrier_manifest_v<N>.json`,
   whose content no longer enters the per-file cache key but is applied as a
   mask when the window is assembled), plus all older swarm material as masked
   value-only data. Each generation ages one step; the oldest rotates out.
   Legacy-rule corpora are never mixed back in.

3. **Training** (warm start from the champion):

   ```bash
   MOSAIC_CARRIER_MANIFEST=policy_carrier_manifest_v<N>.json    MOSAIC_IGNORE_POLICY_TARGET_VALID=1 MOSAIC_VAL_POOL='^selfplay_<gen>-'    python -u train.py --name v<N>-b01 --load <champion>_brierbest        --file-list data/window_v<N>.txt --epochs 12 --lr 5e-05        --lr-schedule cosine --lr-t-max 12 --encoder 2d --value-head wdl        --value-target-variant nortv --value-target-lambda 0.7        --ownership-head-2d --opp-points-head --endgame-head --select-by-brier
   ```

   Early stopping requires a plateau on *both* sides (policy and value); the
   shipped checkpoint is the best Brier, not the best combined loss. Several
   options that look like flags are read from the environment instead
   (`--val-pool`, `--ignore-policy-target-valid`); the manifest logs them
   either way. `MOSAIC_DATA_EXCLUDE` pins the window while other generation
   runs are still writing to `data/`.

   The per-file cache blocks can be built *while* self-play is still running
   (`tools/build_cache_incremental.py --watch`); the window monolith is then
   assembled from those blocks in minutes instead of hours. The build
   environment must match the training environment exactly, because variables
   such as `MOSAIC_IGNORE_POLICY_TARGET_VALID` and the feature width
   `INPUT_SIZE` are part of the block key; and nothing a worker imports
   (`config.py`, `neural_net.py`) may change while the watcher runs, because
   its workers re-import on every start while the parent keeps the key it
   computed at launch. The merge refuses blocks of differing shape before it
   writes anything.

4. **Offline diagnosis**, with an explicit resolution limit. On the policy
   side, `tools/offline_diagnosis.py --frozen` reports the two *arena-
   validated* predictors (prior mass on the oracle top-3, Kendall tau vs.
   oracle Q; correct direction in 7 of 7 decided pairs). On the value side
   there is **no** validated offline predictor: gaps below ~0.015 predicted
   the arena outcome in 0 of 4 cases, so the arena decides.

5. **Gating**: `tools/paired_gating.py` with paired seed blocks (block size 5,
   the seed changes per block, so score analyses have to run at block level),
   swapped boards, Bernoulli SPRT (`H1: p1=0.65`), cap 200 pairs. An early stop
   below ~150 pairs only counts after a fresh-seed replication (a false
   positive taught us that). Only `ACCEPT_H1` promotes.

6. **Promotion & bookkeeping**: `tools/set_champion.py` (server default for
   human games), `tools/elo_tracker.py add` (Bradley-Terry over the whole
   match graph, cadre names only, never file names), and a **frozen artifact**
   for the new champion under `models/frozen_champions/<name>/`: model, spec,
   the wheel it was measured with, a golden probe and a manifest. The wheel
   travels with the artifact so that an old champion still plays the way it did
   when its Elo was measured. The artifact set holds the reigning champion and
   its predecessor (today `v30-b02` and `v29-b09`); older ones are retired once
   their edges are in the register. The full list is `docs/promotion_checklist.md`.

7. **Diagnostics on the winner**: Platt calibration (`tools/platt_fit.py`),
   Brier on a frozen legacy measurement set, the sigma/prior balance, and a
   fresh net-parity fixture. Two further probes are on the checklist but have
   not been run since v24 because their tooling still points at a retired model
   era: that gap is recorded rather than quietly skipped
   (`docs/promotion_checklist.md`).

A failed gating does **not** trigger more self-play games ("no top-up
valve"): a candidate that only wins with additional data is not evidence
for the change under test. Instead its measured components go into the
recipe for the next generation; this is how the `endgame_margin` head
entered the standard recipe despite a drawn arena result.

## Directory Convention

the project's directory mantra: root executes, `tools/` measures, `evaluations/` documents,`engine/` computes, `docs/` explains, `static/` human interface for games.

```text
📦 mosaic-AI/
├── 📂 engine/       # Rust crate (mosaic_rust): game/search/self-play, PyO3 bindings
│   └── 📂 py/       # neural_net.py (MosaicNet), corpus_dataset.py (MosaicDataset, value target)
├── 📂 evaluations/  # STATUS.md, elo_history.csv, arena_trends.csv, eval JSONs/reports
├── 📂 data/         # Self-play output (.pkl) + run manifests, data/archive_*/ = retired
├── 📂 models/       # Checkpoints (.pth/.onnx), loss plots, training manifests
├── 📂 static/       # Web UI (index.html, debug.html, css/js, log/ = game logs)
├── 📂 tools/        # Diagnosis/arena/gating/analysis scripts, see table below
├── 📂 docs/         # engine_manual.md, project_overview.md (plain-language summary, German), reference CSVs, process diagrams
├── 📂 archive/      # Legacy: old Python engine/agents, superseded analyses
├── 📜 config.py     # INPUT_SIZE, NUM_ACTIONS, HIDDEN_SIZE, LR, ...
├── 📜 self_play.py  # ▶️ Self-play driver
├── 📜 train.py      # ▶️ Training + snapshot hook + auto ONNX export
├── 📜 export_onnx.py# ▶️ .pth → .onnx
└── 📜 server.py     # ▶️ Flask web server
```

Additionally, there is a release-bundle path for end users without a
Python/Rust installation. The build sources live in `dist/`
(`run_mosaic.py` standalone launcher, `mosaic_release.spec` PyInstaller
spec, `README_GAME.txt` end-user instructions in German). Building the
shippable bundle is one command:

```bash
python tools/build_release.py
```

This produces `dist/Mosaic-AI/` (onedir: exe + engine + web UI + the
current reference net + `engine_manual.md`) and zips it to
`dist/Mosaic-AI_<version>_<date>.zip`. Prerequisite: the installed
`mosaic_rust` wheel must be current (the bundle packages the wheel from
site-packages, not from source); rebuild it first after any engine
change.

### `evaluations/` at a Glance

`STATUS.md` (a living status/roadmap document, kept in German) and
`elo_history.csv` are the primary sources. In addition: `arena_trends.csv`
(points/floor trend per run), `frozen_eval_set.pkl` and its successors plus the matching
`artifacts/frozen_v<N>_oracle_labels.json` (frozen, cross-generation
eval/oracle sets; `frozen_v3` is the current one, `frozen_v1` is kept as a
trend metric only),
various `offline_diagnosis_*`, `paired_gating_result_*`, and
`paired_arena_*` JSONs (individual runs, each mapped to a STATUS.md section
by filename). `game_analysis/` holds the reports generated by the
game-analysis tool (`tools/analyze_game_log.py`), and `fixtures/` holds frozen
human-vs-AI games with their checksums: they are exactly replayable through the
action IDs in the log and serve as reference positions when a change is
supposed to alter a decision. The process diagrams live in `docs/`
(`diagrams.txt` plus `render_diagrams.py` and the `.svg` files it renders).

### `tools/`

The tool collection has grown past 200 files, and a hand-kept table in this
README could not answer the question that matters: **is this still used, or is
it a leftover?** So the list is generated instead and lives in
[`docs/tools_index.md`](docs/tools_index.md)
(`python -X utf8 tools/generate_tools_index.py`, `--check` verifies it is
current). Each entry carries its purpose, its last commit, and who names it,
classified by evidence rather than opinion: whether something *calls* it,
only documents it, or no longer names it at all.

---

## Playing & Debugging

```bash
python server.py
# http://localhost:5000
```

The opponent is the reigning champion from `models/champion.txt`, played
with its own spec (search knobs) from the frozen artifact; the new-game
dialog exposes the simulation count (default 400) and the model name. The
server-side `DIFFICULTY_PRESETS` (`easy`/`medium`/`hard`/`expert`) are not
reachable from the web UI; a measured ladder of four levels (frozen heuristic
anchor, then the champion in three search styles) is pre-registered in
`evaluations/PREREG_difficulty_levels.md` and scheduled for v29. The AI
debugger (`/debug`) shows a value-head
breakdown (raw value, points forecast, win %, blended utility, floor shift)
as well as a granular Gumbel trace (top-m candidates, Sequential Halving
phases with eliminations, finalists) per move.

Games against the AI are logged under `static/log/game_*.log`; the final
score is the per-player `Endwertung ... Gesamt` line (the `# SPIELENDE`
summary is written before the end scoring is applied). `tools/analyze_game_log.py`
replays a log exactly through its action IDs and evaluates every move against
the net; `tools/claude_play.py` drives the same engine from the command line.

---

## Architecture (Quick Reference)

### Neural Network (`Mosaic2DNet`, `engine/py/neural_net.py`)

```
planes (79×6×6) → [Conv3×3(48) → BN → ReLU] ×2 → flatten ─┐
state  (888)    → Linear(512) → BN → ReLU ────────────────┴→ concat
    → Fusion: Linear(512) → BN → ReLU → Linear(512) → ReLU
       ┌→ Policy Head:      Linear(256) → ReLU → Linear(414)  (action logits)
       ├→ Value Head (WDL): Linear(64)  → ReLU → Linear(2)    (logits → P(win))
       ├→ Moon-Order Head:  Linear(32)  → ReLU → Linear(5)    (Plackett-Luce scores)
       ├→ Points Heads:     own + opponent score forecast (aux, Tanh)
       ├→ Ownership Head:   Linear(128) → ReLU → Linear(72)   (2×36 fields, aux)
       └→ Endgame Head:     round-5 solver root margin (aux, Tanh)
```

The champion ONNX export (`alphazero_v30-b02_brierbest.onnx`)
carries two inputs (`planes`, `state`) and eight outputs (`policy`,
`value`, `moon`, `points`, `ownership`, `value_wdl_logits`, `opp_points`,
`endgame_margin`). Aux heads are training signal only; the search reads
none of them. The legacy flat `MosaicNet` (708 -> 3×512 trunk, Tanh value)
remains loadable: the input layout is detected from the model file
(`detect_layout`, `engine/src/net.rs`), never assumed.

### State Tensor (888 Features)

Source of truth: `engine/src/features.rs` (the constant there is the single
source, `config.py` mirrors it); global state, active scoring plates
(Wertungsplatten), factories, both player boards in ego perspective, both 3×3
dome grids, moon/dome stacks, hidden information as masks/shares, and since
2026-09-11 (section 15, `v28-b02`) eleven values describing the acting
player's knowledge of the dome-plate stack: the unknown prefix, the own
returned block (length, special and wild counts, the types of its top four
positions) and the opponent's returned blocks. Features are only ever
appended, never reordered: indices 0..743 are unchanged since 2026-09-05, so
older ONNX models stay playable (`net.rs::build_inputs` truncates to the
model width), and a warm start pads the input layer with zero columns
(`train.py`). Three blocks were appended after that: 39 values for what the
acting player can see of the stacks (755..794), 90 values projecting which
cells this round's tiling will fill and which slots it completes (794..884),
and 4 for the player's own returned designs in order (884..888).

### Action Space (414 Actions)

| Type                   | IDs     | Description                                             |
| ---------------------- | ------- | ------------------------------------------------------- |
| pass                   | 0       | No legal move                                           |
| end_tiling             | 1       | End tiling phase                                        |
| stone                  | 10-273  | Take tiles: factory × color × target row                |
| tiling                 | 274-327 | Place tile: pattern row × slot                          |
| choose_dome_slot       | 328-354 | Dome placement stage 1: display tile × slot             |
| choose_draw_stack_slot | 355-390 | Draw-stack placement stage 1: drawn tile × slot         |
| choose_dome_rotation   | 391-394 | Dome placement stage 2: rotation (shared by both paths) |
| use_chips              | 395-400 | Complete a pattern row using a bonus chip               |
| bonus_chip             | 401-404 | Take a revealed bonus chip                              |
| dome_stack_peek        | 405     | Pay 1 point, draw a hidden plate (repeatable)           |
| choose_moon_top        | 406-410 | Order the moon stacks: which colour goes on top          |
| choose_return_first    | 411-413 | Order of dome plates returned under the stack            |

---

## Configuration (Selection)

| Parameter                      | Value | Where                     | Description                                                 |
| ------------------------------ | ----- | ------------------------- | ----------------------------------------------------------- |
| `INPUT_SIZE`                   | 888   | `config.py`               | Size of the state tensor                                    |
| `NUM_ACTIONS`                  | 414   | `config.py`               | Size of the action space                                    |
| `HIDDEN_SIZE`                  | 512   | `config.py`               | Neurons per hidden layer                                    |
| `TD_LAMBDA`                    | 0.5   | `engine/py/neural_net.py` | TD-bootstrap blend in the value target                      |
| `VALUE_SCHEMA_VERSION`         | 20    | `engine/py/neural_net.py` | Value-target formula version (cache invalidation on change) |
| `USE_GUMBEL_SEARCH`            | true  | `engine/src/net_mcts.rs`  | Gumbel search (false = legacy PUCT)                         |
| `GUMBEL_TOP_M`                 | 16    | `engine/src/net_mcts.rs`  | Root candidates for Sequential Halving                      |
| `FLOOR_SHAPING_WEIGHT`         | 0.3   | `engine/src/net_mcts.rs`  | Exact floor-penalty leaf-value additive (validated)         |
| `DETERMINIZE_ROOT_HIDDEN_INFO` | true  | `engine/src/net_mcts.rs`  | Single determinization of hidden information at the root; since 2026-09-10 it keeps the acting player's own returned dome-plate blocks in order (`state.rs::determinize_dome_pool`, `MOSAIC_DOME_POOL_KNOWLEDGE=0` restores the full shuffle for A/B checks) |

Further constants along with their calibration history are documented as
Rust/Python constants in the code; every self-play/training run also writes
the active configuration to a JSON manifest next to its output.

---

Detailed history, measurements, ablation results, and open questions:
[`evaluations/STATUS.md`](evaluations/STATUS.md).
