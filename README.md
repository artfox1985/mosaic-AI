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

**Champion: `v35-b16`, shown in the game as Tessa** (promoted 2026-10-09 after
the full checklist, `evaluations/PREREG_v35_window.md` par.22 and par.22a). The
package is the network `alphazero_v35-b16_brierbest` with a spec byte-identical
to the `v34-b01` spec (start-dome search, round 5 played by the net search); tree
reuse is not part of the spec. **Tessa** is the name the game shows for the
reigning champion; the technical name stays in the ladder and the files
(`models/champion.txt`). This is the final champion: `v35` was the last
generation and the project is closed with it.

Edges measured for `v35-b16`: gate 1 against the reigning champion `v34-b01`
289:161 = 64.2 % (n = 450, both seeds stopped by the SPRT, block-z +6.63,
par.20b); the replication to the cap on a fresh seed (20261603) 249:151 =
62.3 % over 200 pairs, block-z +5.07; the anchor edge against `hv4_anchor`
46:4 (fixed n = 50); the champion-2 edge against the frozen artifact `v32-b01`
107:43 = 71.3 % (n = 150). After the fit `v35-b16@400` stands at **1660** (95% CI [1607, 1713]) from 1,050 rated games, `v34-b01@400` at 1575 [1527, 1624] (the new edges shift the ladder; it was 1595 before) and `v32-b01@400` at 1450 (`evaluations/PREREG_v35_window.md` par.22a). The ladder before this
promotion, anchored at the frozen heuristic artifact
`models/frozen_heuristics/hv4_anchor` (Heuristic@150 = 1000,
`tools/elo_tracker.py report`): `v34-b01` 1595 (95% CI [1546, 1646]),
`v32-b01` 1460, `v31-b01` 1433 (`evaluations/PREREG_v34_window.md` par.10e).

**`v35` was the last generation** (user decision 2026-10-04), and its closing
series measured its arms against `v34-b01` (summary table after par.16 of
`PREREG_v35_window.md`). The first arm, `v35-b01`, trained on a window whose
classes ran at 100 simulations and reached 52.0 % over one seed, no edge; the
value head learned nothing measurable from that window (par.11b to par.11d).
Regenerating the whole window at 400 simulations carried in every arm built on
it: `v35-b02` 56.8 %, `v35-b03` 58.6 %, `v35-b05` 56.4 %, `v35-b06` 56.9 %,
`v35-b04` 56.2 % (par.12 to par.14). The larger step came from the policy
carriers, the set of games the policy head learns from: `v35-b10` (all 1,200
window files as carriers instead of 400, no new generation) 60.9 % at block-z
+6.22 (par.18b), `v35-b09` (4,000 more policy games at 400 simulations) 59.1 %
(par.17c), and `v35-b16`, the two stacked, 64.2 % (par.20b). Without a lever:
`v35-b07` (lambda 1.0, par.15b), weight averaging `v35-b08`/`v35-b08b` (EMA,
par.16a and par.16c), the bootstrap value-target variants `v35-b11` to
`v35-b15` (against `v35-b02`, par.19.6) and `v35-b19` (against `v35-b16`,
par.21a), and `v35-b18`, tree reuse on top of `v35-b16` (51.0 % in a quick look,
`PREREG_tree_reuse.md` par.3e). Tree reuse alone on the `v34-b01` net carried
narrowly, 53.1 % over three seeds at block-z +2.22 (par.3c), but did not show on
the stronger net. The tiling-surprise probe found no systematic room for a
mini-search over the round-end tiling (`PREREG_tiling_surprise_probe.md`
par.3b). The one lesson of the series: the lever sat in the policy carriers,
not in the value target and not in the search. The project closes with
`v35-b16` as Tessa.

**The cold-start question is settled.** `v30-b01` and `v30-b02` trained on the
same replay window with the same seed and the same recipe and differed in a
single factor, the start: 404:396 cold against 443:297 warm, a gap of 9.4
percentage points.

**Ratings live in segments.** Two engine corrections moved the anchor's own
moves, and each opened a new segment: the min-node move ordering in the round-5
solver (`evaluations/PREREG_round5_minfix_elo_reset.md`) and the phantom-tile
fix, which re-anchored the ladder on `hv4_anchor` on 2026-09-12. Ratings are not
comparable across such a boundary; the old registers are kept as
`archive/elo_history_pre_r5fix.csv` and `archive/elo_history_pre_phantomfix.csv`. Since the second segment the anchor ships its
own wheel, so an engine change can no longer move the fixed point of the ladder,
and every change is checked against it move by move.

**Some defects are invisible to the measurement apparatus.** Self-play, arena
and gating compare two agents inside the *same* world model, so an error in the
shared model cancels out and costs zero Elo at any sample size. The dome-stack
bug found in September was of that kind, and a human playing the GUI found it,
not the pipeline. The list of places where the code discards information on
purpose is kept in
[`docs/architecture_reference.md`](docs/architecture_reference.md).

The engine package is version 1.1.0 (contract hash `6ef829e564c58bd5`, 888 inputs, 414 actions).

Full history, all measurements and the methodology rules:
[`evaluations/STATUS.md`](evaluations/STATUS.md); process diagrams:
[`docs/diagrams.txt`](docs/diagrams.txt) (render via
`python docs/render_diagrams.py`).

## Engine Core in Brief

- **Rust search** (`engine/src/net_mcts.rs`): Gumbel AlphaZero (Gumbel-Top-m
  Sequential Halving at the root), deterministic in arena/server. Self-play
  also plays the argmax from move 1; diversity is bought explicitly instead
  of by sampling: one forced deviation or one excursion per game, start-slot
  scatter, and a tie-break mode, all printed in each run manifest. Root width
  follows the budget: `m = clamp(round(sims/16), 4, 16)`, i.e. 16 at 400/600
  sims and 9 at 150 sims (measured strength-neutral). The legacy PUCT path is
  still available behind `USE_GUMBEL_SEARCH`.

- **Network** (`engine/py/neural_net.py`): 2D encoder (`Mosaic2DNet`):
  conv branch over 79 binary 6x6 planes + flat branch over 888 features
  (744 up to `v28-b01`, 755 for `v28-b02`, 794 for the v29 arms; see
  "State Tensor" below), fused into a 512-wide trunk. Both inputs are built
  once, in Rust (`engine/src/features.rs`), and exported to Python via PyO3;
  the Python twin builder remains as a test oracle and is bit-identical
  (`tools/probes/feature_parity_rust_python.py`, gate passed 2026-09-11). Heads: policy (414 actions), value
  (WDL: two logits -> P(win)), moon order, own points, opponent points,
  ownership, and optionally `endgame_margin` (auxiliary target: the
  round-5 solver's root value, recorded free of charge from self-play
  records; a budget-limited expectiminimax value with exact leaf
  scoring, not an exact minimax value; off in the current recipe, the
  v35 training manifests carry `endgame_head: false`). Aux heads are
  training signal only; the search never reads them.
- **Value target**: `VALUE_SCHEMA_VERSION=20`. `values_wdl` is a TD blend
  (`TD_LAMBDA=0.5`) of the bootstrap win probability at the next round
  transition and the actual game outcome. Bootstraps from pre-WDL
  generators are Platt-destretched first (A=0.0051, B=1.9269) so that old
  and new corpora carry the same semantics. The raw outcome is kept
  separately (`wdl_outcome`) and yields the **Brier score**, the only
  cross-arm comparable value metric; it also selects the checkpoint
  (`_brierbest`, re-validated in the arena).
- **Cache**: HDF5, planes and legal-move masks bit-packed (1 bit per field)
  and lzf-compressed. Measured on the v35-b01 monolith: 2,025,784 states in
  577 MB, about 0.28 KB per state.
- **Floor shaping** (`FLOOR_SHAPING_WEIGHT=0.3`, override
  `MOSAIC_FLOOR_SHAPING_W`): exact leaf-value additive against
  floor-penalty spirals; re-validated in the WDL era (0.15/0.6 sweep: H0).
  Plate shaping and value shrinkage were disproved and stay off.
- **Round 5**: the network path plays round 5 with the same Gumbel search
  as rounds 1 to 4 (spec field `r5_net_solver` 0 in the champion and in
  the generator spec, which also sets `r5_net_sims` 400). That is a
  measured decision: the net search beat the expectiminimax solver at the
  playing point 480:320 and at the generation point as well
  (`evaluations/PREREG_r5_net_vs_solver.md` par.6d/6f). The solver
  (`engine/src/round5.rs`: alpha-beta over the decision nodes plus chance
  nodes where the four fresh, still-hidden bonus chips get revealed;
  exact leaf evaluation under a fixed dome grid, node budget 200) stays
  in the tree for the heuristic lane, the frozen anchor, and the round-4
  bootstrap label (`round5::exact_round5_outcome`). A side can still opt
  into it per spec (`r5_net_solver` 1).
- **Runtime knobs**: every experimental lever is an `MOSAIC_*` environment
  variable, or a per-side spec field with the environment value as its
  default, and its default reproduces the previous behaviour bit-for-bit
  (verified by a hash probe before use). The registry is the code
  (`engine/src/knob_registry.rs`); `docs/knobs.md` is generated from it
  (`python tools/generate_knob_docs.py --check`) and currently lists 152
  knobs: 70 active in the recipe, 79 diagnostic, 3 dead. Each one names the
  pre-registration that answered it.

## The Generation Cycle (Training Pipeline)

The heart of the project: how the next candidate generation is produced
from the reigning champion. Every step has a written pre-registration in
`evaluations/PREREG_*.md`: design **and** decision rule are fixed *before*
the run, so a result cannot be reinterpreted afterwards. `v35` was the last
generation; the steps below describe the cycle as it ran for it.

1. **Self-play in four classes** (generator = the reigning champion). The value
   classes buy diversity (a forced deviation or an excursion per game). In the
   last generation's window (`v35-b02`) every class ran at 400 simulations, so a
   game cost the same in every class and the search targets of the value classes
   had the same budget as those of the policy classes (`PREREG_v35_window.md` par.18):

   ```bash
   # Since v35 the classes come from a recipe file; the chain is tools/v35_b02_generate.sh
   python -u self_play.py --recipe models/v35_b02.recipe.json --class policy-s400
   python -u self_play.py --recipe models/v35_b02.recipe.json --class policy-dice-v2-r1-s400
   python -u self_play.py --recipe models/v35_b02.recipe.json --class value-deviate-s400
   python -u self_play.py --recipe models/v35_b02.recipe.json --class value-excursion-s400
   ```

   Four classes: a policy-carrying base class, a policy class with the
   dome-dice opening, and two value-only swarm classes (one forced deviation
   per game, one excursion per game). Which files feed the policy head is
   decided by the carrier manifest (`data/policy_carrier_manifest_<window>.json`),
   not by the class: the `v35-b02` baseline used only the policy classes, the
   promoted `v35-b16` used every file (par.18, par.20). Measured on the
   v35-b02 run at 400 simulations for every class: 6.9 s per game for both policy classes with the cache
   watcher running alongside (`docs/measured_runtimes.md`); the v34 window
   with its 100-simulation classes ran those at 3.2 s per game. Note that
   `--games` counts excursion identities as well, so the excursion class
   needs the full number, not half of it.

2. **Replay window** (v35: the `v35-b02` window of 1,200 files, 12,000 games at
   10 games per file, all generated by the champion of the time, `v34-b01`). In
   the `v35-b02` baseline the 400 files of the policy classes were the policy
   carriers (`data/policy_carrier_manifest_v35_b02.json`) and the 800 swarm files
   entered as value-only data. The promoted `v35-b16` trained on 1,600 files
   (those 1,200 plus 400 files of an extra policy class at 400 simulations) with
   all 1,600 as policy carriers (`data/policy_carrier_manifest_v35_b16.json`,
   `PREREG_v35_window.md` par.20). Carrier status is applied as a
   mask when the window is assembled, not in the per-file cache key. Older
   generations are no longer mixed in, and legacy-rule corpora never were
   again. The validation split is 120 files drawn from the same pool
   (`MOSAIC_VAL_POOL`), held fixed across the arms of a generation so that
   their Brier scores stay comparable.

3. **Training** (warm start from the champion):

   ```bash
   MOSAIC_CARRIER_MANIFEST=policy_carrier_manifest_v<N>.json    MOSAIC_IGNORE_POLICY_TARGET_VALID=1 MOSAIC_VAL_POOL='^selfplay_<gen>-'    python -u train.py --name v<N>-b01 --load <champion>_brierbest        --file-list data/window_v<N>.txt --epochs 12 --lr 5e-05        --lr-schedule cosine --lr-t-max 12 --encoder 2d --value-head wdl        --value-target-variant nortv --value-target-lambda 0.7        --ownership-head-2d --opp-points-head --select-by-brier --fast-loader
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
   swapped boards, 200 pairs per seed and two seeds. The SPRT bounds stay
   armed (alpha = beta = 0.001), but the decision rule since v34 is the
   pooled block-z (`tools/gating_block_z.py`): a candidate carries at block-z
   >= +1.96 or a pooled win rate >= 52.5 % without counter-evidence; if exactly
   one seed clears the block-z line, a third seed runs
   (`evaluations/PREREG_v34_window.md` par.2). An early SPRT stop only counts
   after a fresh-seed replication to the cap (a false positive taught us that).

6. **Promotion & bookkeeping**: `tools/set_champion.py` (server default for
   human games), `tools/elo_tracker.py add` (Bradley-Terry over the whole
   match graph, cadre names only, never file names), and a **frozen artifact**
   for the new champion under `models/frozen_champions/<name>/`: model, spec,
   the wheel it was measured with, a golden probe and a manifest. The wheel
   travels with the artifact so that an old champion still plays the way it did
   when its Elo was measured. The artifact set holds the reigning champion and
   its predecessor; older ones are retired once their edges are in the register.
   With the `v35-b16` promotion the set is to move from `v34-b01`/`v32-b01` to
   `v35-b16`/`v34-b01` (`PREREG_v35_window.md` par.22). The full list is
   `docs/promotion_checklist.md`.

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
entered the standard recipe despite a drawn arena result (it has since
been dropped again; the current recipe trains without it).

## Directory Convention

the project's directory mantra: root executes, `tools/` measures, `evaluations/` documents,`engine/` computes, `docs/` explains, `static/` human interface for games.

```text
📦 mosaic-AI/
├── 📂 engine/       # Rust crate (mosaic_rust): game/search/self-play, PyO3 bindings
│   └── 📂 py/       # neural_net.py (Mosaic2DNet), corpus_dataset.py (MosaicDataset, value target)
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

The tool collection has grown past 150 entries, and a hand-kept table in this
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
`evaluations/PREREG_difficulty_levels.md` and deferred to the project close,
so that it is calibrated on the model that ships. The AI
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
       ├→ Ownership Head:   Linear(32×36) → reshape 32×6×6 → Conv3×3(32) → ReLU → Conv1×1(2) → 72 (2×36 fields, aux)
       └→ Endgame Head:     Linear(64) → ReLU → Linear(1) → Tanh (aux, optional; not in the champion)
```

The ONNX export of `v34-b01` (`alphazero_v34-b01_brierbest.onnx`)
carries two inputs (`planes` 79×6×6, `state` 888) and seven outputs (`policy`
414, `value` 1, `moon` 5, `points` 1, `ownership` 72, `value_wdl_logits` 2,
`opp_points` 1); the diagram above was checked against the export's weight
shapes on 2026-10-05 (fusion input 2,240 = 48×36 conv features + 512). `v35-b16`
is a warm start from that checkpoint with the same training recipe
(`evaluations/PREREG_v35_window.md` par.20); its own export has not been
shape-checked for this README. Aux heads are training signal only;
the search reads none of them. The legacy flat `MosaicNet` (708 -> 3×512 trunk, Tanh value)
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
