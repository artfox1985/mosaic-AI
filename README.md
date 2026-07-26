# 🧩 Mosaic-AI: Tile-Drafting AlphaZero Environment

[![Rust](https://img.shields.io/badge/engine-Rust-orange.svg)](https://www.rust-lang.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-Deep%20Learning-ee4c2c.svg)](https://pytorch.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Mosaic-AI** is a complete reinforcement-learning framework for training
AlphaZero-style neural networks on a two-player tile-drafting and
dome-building board game with hidden information.

> **⚠️ Disclaimer:** This project is a learning/research project around a
> generic tile-drafting/wall-tiling game mechanic. It was built from scratch
> and has no connection to any existing commercial board games, publishers,
> or brands.

---

## Current Status

Reference/champion net: **`v16_best`**, Elo **≈1094** (95% CI [1033, 1164]),
anchored at Heuristic@150 (dyn. ~330 sims) = 1000 (`tools/elo_tracker.py
report`). On 2026-07-24, a worktree incident wiped all model checkpoints up
to and including the champion at the time (code and `data/`/`evaluations/`
were unaffected); `v16_best` is the result of the rebuild line that has been
running since (`v14` → `v14b` → `v15` → `v16`) and has already surpassed the
old champion's Elo. Full history, measurements, and ongoing investigations:
[`evaluations/STATUS.md`](evaluations/STATUS.md).

---

## Engine Core in Brief

- **Rust search** (`engine/src/net_mcts.rs`): Gumbel AlphaZero (Gumbel-Top-m,
  `GUMBEL_TOP_M=16`, + Sequential Halving at the root), deterministic in
  arena/server, Gumbel exploration in self-play. The legacy PUCT path is
  still available behind the `USE_GUMBEL_SEARCH` toggle.
- **Value target**: `VALUE_SCHEMA_VERSION=15` (`engine/py/neural_net.py`) —
  soft symmetric margin target, without `round_transition_value` (rtv) by
  default. rtv is expensive (~81% of self-play cost) and showed no
  measurable strength contribution in the ablation; toggle via
  `self_play.py --rtv` (`record_rtv`, default OFF). `bootstrap_value`
  (TD bootstrap, `TD_LAMBDA=0.5`) stays active in every case.
- **Floor shaping** (`FLOOR_SHAPING_WEIGHT=0.3`): validated, exact leaf-value
  additive against floor-penalty spirals (n=100, no early stop). Plate
  shaping/value shrinkage, by contrast, were **disproved** in an A/B test and
  remain disabled — details/numbers in `STATUS.md`.
- **Round 5**: exact alpha-beta search (`engine/src/round5.rs`), no more
  network decisions once no hidden information remains in the game.

---

## The Generation Cycle (Training Pipeline)

The heart of the project — this is how the next candidate generation is
produced from the reigning champion:

1. **Self-play batch** (generator = reigning champion):
   ```bash
   python -u self_play.py --mode network --games 6000 --sims 400 \
       --version <generator> --model <generator>_best --threads 11
   ```
   ~7–8 h at ~0.22 games/s. Per-game flush (a crash costs at most 1 game),
   heartbeat monitoring, JSON run manifest.
2. **Replay window**: 6000 fresh games + 2000 from one generation back +
   1000 from two generations back, assembled at the file level — the rest
   moves to `data/archive_*/` (old corpora are never mixed back in).
3. **Training**:
   ```bash
   python -u train.py --name vN --load vN-1_best --lr 0.00005 \
       --lr-schedule cosine --epochs 100 --value-target-variant nortv
   ```
   From-scratch runs (no `--load`) use the default LR. After every training
   run, a `train.py` hook automatically writes a model snapshot to the
   OneDrive backup.
4. **Diagnosis**: `tools/offline_diagnose.py --frozen` (the only
   cross-generation comparable metric, fixed eval set) +
   `tools/oracle_metrics.py` (supplementary signal against a deep-search
   reference, **not** a substitute for an actual arena measurement).
5. **Gating**: `tools/paired_gating.py` (paired seed blocks, swapped boards,
   Bernoulli SPRT with `H1: p1=0.65`) — only an `ACCEPT_H1` promotes the
   candidate to the new reference/generator.
6. **Elo**: `tools/elo_tracker.py` (Bradley-Terry over the full match graph)
   + anchor match for the new champion via `tools/arena.py`.
7. **Trends**: every arena/gating run appends a row to
   `evaluations/arena_trends.csv` (avg. points, floor penalties over time —
   complements Elo/win rate with a quality signal beyond "stronger/weaker").

---

## Directory Convention

**"Root führt aus, `tools/` misst, `evaluations/` dokumentiert, `engine/`
rechnet, `docs/` erklärt, `static/` spielt."** — the project's directory
mantra: root executes, `tools/` measures, `evaluations/` documents,
`engine/` computes, `docs/` explains, `static/` plays.

```text
📦 mosaic-AI/
├── 📂 engine/       # Rust crate (mosaic_rust) — game/search/self-play, PyO3 bindings
│   └── 📂 py/       # neural_net.py (MosaicNet, MosaicDataset, value target)
├── 📂 evaluations/  # STATUS.md, elo_history.csv, arena_trends.csv, eval JSONs/reports
├── 📂 data/         # Self-play output (.pkl) + run manifests, data/archive_*/ = retired
├── 📂 models/       # Checkpoints (.pth/.onnx), loss plots, training manifests
├── 📂 static/       # Web UI (index.html, debug.html, css/js, log/ = game logs)
├── 📂 tools/        # Diagnosis/arena/gating/analysis scripts, see table below
├── 📂 docs/         # engine_manual.md, reference CSVs
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
spec, `README_SPIEL.txt` end-user instructions in German). Building the
shippable bundle is one command:

```bash
python tools/build_release.py
```

This produces `dist/Mosaic-AI/` (onedir: exe + engine + web UI + the
current reference net + `engine_manual.md`) and zips it to
`dist/Mosaic-AI_v16_<date>.zip`. Prerequisite: the installed
`mosaic_rust` wheel must be current (the bundle packages the wheel from
site-packages, not from source) — rebuild it first after any engine
change.

### `evaluations/` at a Glance

`STATUS.md` (a living status/roadmap document, kept in German) and
`elo_history.csv` are the primary sources. In addition: `arena_trends.csv`
(points/floor trend per run), `frozen_eval_set.pkl` +
`frozen_v1_oracle_labels.json` (frozen, cross-generation eval/oracle set),
various `offline_diagnose_*`, `paired_gating_result_*`, and
`paired_arena_*` JSONs (individual runs, each mapped to a STATUS.md section
by filename), `render_diagrams.py` plus the `.svg` diagrams it generates,
and `reference_game.md` (sample game). `game_analysis_*.md` reports are
generated by the game-analysis tool (`tools/analyze_game_log.py`).

### `tools/`

| Script | Purpose |
|---|---|
| `analyze_game_log.py` | Analyzes human-vs-AI logs (`static/log/`): parser + replay cross-validation + oracle evaluation of every move, report as Markdown |
| `arena.py` | Round-robin/anchor matches (heuristic configurations and network-vs-heuristic), Rust engine, SPRT |
| `arena_trends.py` | Appends a row (avg. score, floor penalty) to `evaluations/arena_trends.csv` per arena/gating run |
| `build_frozen_eval_set.py` | Builds the frozen, cross-generation eval set (`frozen_eval_set.pkl`) |
| `build_frozen_oracle_labels.py` | Labels the frozen set via deep network search (oracle reference for `oracle_metrics.py`) |
| `build_release.py` | Builds the PyInstaller Windows bundle + ZIP for end users |
| `diagnosis.py` | Sanity check of the training data (zero mask, policy leak, policy sharpness) |
| `elo_tracker.py` | Bradley-Terry Elo bookkeeping over `evaluations/elo_history.csv` (pure evaluation, does not run matches) |
| `extract_kat2_examples.py` | Extracts example states for "floor penalty despite alternative" cases from self-play data |
| `git_tree.py` | Prints a cleaned-up project directory tree |
| `hybrid_paired_arena.py` | Paired arena runner for hybrid search (priors from network A, leaf values from network B) |
| `model_info.py` | Shows metadata of a saved model checkpoint |
| `offline_diagnose.py` | Value validation R² overall + per round, policy top-1/top-3, `--frozen` for cross-generation comparison |
| `oracle_metrics.py` | Offline metrics of candidate networks against the oracle labels + rank correlation with Elo |
| `paired_arena_arm_worker.py` | Single-arm worker for paired speed-bundle A/Bs (thin CLI wrapper around `net_arena_match`) |
| `paired_arena_ismcts.py` | Paired A/B: single vs. multiple determinization (ISMCTS) |
| `paired_arena_round5.py` | Paired A/B for the round-5 budget switch (time vs. node budget) |
| `paired_arena_shrink_ab.py` | Paired A/B for the value shrinkage constant (orchestrator) |
| `paired_arena_shrink_arm_worker.py` | Single-arm worker for the value shrinkage A/B (network vs. network) |
| `paired_arena_speedbundle.py` | Paired A/B for the search speed bundle (inference batching, Gumbel depth fixes) |
| `paired_gating.py` | Standard gating tool: paired seeds/swapped boards, SPRT (`p1=0.65`), sign test |
| `rtv_redundancy_report.py` | Offline analysis: does `round_transition_value` still carry independent information over `bootstrap_value`? |
| `selfplay_diversity_report.py` | Opening/trajectory diversity in the self-play corpus (collapse check) |

---

## Playing & Debugging

```bash
python server.py
# http://localhost:5000
```
Difficulty levels up to `expert` = `v16_best`@400 sims (`server.py`'s
`DIFFICULTY_PRESETS`). The AI debugger (`/debug`) shows a value-head
breakdown (raw value, points forecast, win %, blended utility, floor shift)
as well as a granular Gumbel trace (top-m candidates, Sequential Halving
phases with eliminations, finalists) per move.

Games against the AI are logged under `static/log/game_*.log`.
Analysis/oracle evaluation of these logs is in progress
(`tools/analyze_game_log.py`, maintained separately).

---

## Backup

A daily, non-destructive OneDrive mirror of the repo runs as a scheduled
task. In addition, `train.py` automatically writes a named model snapshot
after every training run to
`<OneDrive>\Backups\mosaic-AI\models_snapshots\` (event-driven, introduced
after the model loss on 2026-07-24 — fails silently with a warning if the
`OneDrive` environment variable is missing, but does not abort training
itself).

---

## Architecture (Quick Reference)

### Neural Network (`MosaicNet`, `engine/py/neural_net.py`)
```
Input (708) → Linear(512) → BN → ReLU
           → Linear(512) → BN → ReLU
           → Linear(512) → ReLU
           ┌→ Policy Head:     Linear(256) → ReLU → Linear(406)   — action logits
           ├→ Value Head:      Linear(64)  → ReLU → Linear(1) → Tanh
           ├→ Moon-Order Head: Linear(32)  → ReLU → Linear(5)     — Plackett-Luce scores
           └→ Points Head:     Linear(64)  → ReLU → Linear(1) → Tanh  — score forecast (aux)
```
The ONNX export carries exactly these 4 output tensors.

### State Tensor (708 Features)
Source of truth: `engine/src/features.rs` ↔ `state_to_tensor` — global
state, active scoring plates (Wertungsplatten), factories, both player
boards in ego perspective, both 3×3 dome grids, moon/dome stacks, hidden
information as masks/shares.

### Action Space (406 Actions)
| Type | IDs | Description |
|---|---|---|
| pass | 0 | No legal move |
| end_tiling | 1 | End tiling phase |
| stone | 10–273 | Take tiles: factory × color × target row |
| tiling | 274–327 | Place tile: pattern row × slot |
| choose_dome_slot | 328–354 | Dome placement stage 1: display tile × slot |
| choose_draw_stack_slot | 355–390 | Draw-stack placement stage 1: drawn tile × slot |
| choose_dome_rotation | 391–394 | Dome placement stage 2: rotation (shared by both paths) |
| use_chips | 395–400 | Complete a pattern row using a bonus chip |
| bonus_chip | 401–404 | Take a revealed bonus chip |
| dome_stack_peek | 405 | Pay 1 point, draw a hidden plate (repeatable) |

---

## Configuration (Selection)

| Parameter | Value | Where | Description |
|---|---|---|---|
| `INPUT_SIZE` | 708 | `config.py` | Size of the state tensor |
| `NUM_ACTIONS` | 406 | `config.py` | Size of the action space |
| `HIDDEN_SIZE` | 512 | `config.py` | Neurons per hidden layer |
| `TD_LAMBDA` | 0.5 | `engine/py/neural_net.py` | TD-bootstrap blend in the value target |
| `VALUE_SCHEMA_VERSION` | 15 | `engine/py/neural_net.py` | Value-target formula version (cache invalidation on change) |
| `USE_GUMBEL_SEARCH` | true | `engine/src/net_mcts.rs` | Gumbel search (false = legacy PUCT) |
| `GUMBEL_TOP_M` | 16 | `engine/src/net_mcts.rs` | Root candidates for Sequential Halving |
| `FLOOR_SHAPING_WEIGHT` | 0.3 | `engine/src/net_mcts.rs` | Exact floor-penalty leaf-value additive (validated) |
| `DETERMINIZE_ROOT_HIDDEN_INFO` | true | `engine/src/net_mcts.rs` | Single determinization of hidden information at the root |

Further constants along with their calibration history are documented as
Rust/Python constants in the code; every self-play/training run also writes
the active configuration to a JSON manifest next to its output.

---

Detailed history, measurements, ablation results, and open questions:
[`evaluations/STATUS.md`](evaluations/STATUS.md).
