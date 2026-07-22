# 🧩 Mosaic-AI: Tile-Drafting AlphaZero Environment

[![Rust](https://img.shields.io/badge/engine-Rust-orange.svg)](https://www.rust-lang.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-Deep%20Learning-ee4c2c.svg)](https://pytorch.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Mosaic-AI** is a complete Reinforcement Learning framework for training AlphaZero-style neural networks on a complex two-player tile-drafting and dome-building board game.

> **⚠️ Disclaimer:** This project is an educational Reinforcement Learning experiment implementing a generic tile-drafting and wall-tiling game mechanic. It was built from scratch for research purposes and is **not** affiliated with, endorsed by, or related to any existing commercial board games, publishers, or registered trademarks.

---

## 🧠 Core Features

- **Rust Game Engine** (`engine/`, PyO3/maturin) — full headless engine covering the whole multi-phase gameplay (sun/moon drafting, two-stage dome placement, hidden-stack draws, bonus chips, pattern rows, floor penalty, exact end scoring). Rulebook-audited (33 rules verified). GIL-free, rayon-parallel self-play/arena.
- **Gumbel AlphaZero Search** (`engine/src/net_mcts.rs`) — Gumbel-Top-m (m=16) + Sequential Halving at the root, mctx-faithful deterministic selection at depth ≥1 (completed-Q over *all* candidates, expansion on demand — no widening caps, no policy-mass cutoff), Plackett-Luce moon-order priors, network-value leaf with exact floor-penalty shaping (paired-test validated: +14 pp, p=0.0075). Deterministic in arena/production (`gumbel_scale=0` equivalent), Gumbel exploration in self-play. Legacy PUCT path kept behind a toggle.
- **Imperfect information handled honestly** — hidden dome stack + unrevealed bonus chips are determinized once per move at the search root (no in-tree oracle knowledge); round transitions are evaluated as sampled chance nodes.
- **Exact endgame** (`engine/src/round5.rs`) — round 5 (no more hidden info) is solved by alpha-beta with an exact tiling/end-scoring evaluator, wired into both search paths.
- **Batched inference** (`engine/src/net.rs`) — both leaf perspectives (mover + flipped) run as one batch=2 ONNX call (tract-onnx, ~1.9× search speedup).
- **Self-Play Pipeline** (`self_play.py`) — network or heuristic mode; per-game flush (a crash costs ≤1 game), heartbeat supervision, preemptive per-game watchdog, Windows keep-awake, and a JSON run manifest (CLI args, git commit, full engine-constant snapshot) per run. Value labels (`round_transition_value`, TD-bootstrap `bootstrap_value`) are node-budgeted → deterministic and load-independent.
- **Training** (`train.py`) — warm-start with shape-mismatch filtering, plateau-based early stopping, combined-metric checkpoint selection (policy+value+points), per-run corpus-composition log (games per version prefix), automatic ONNX export, network-utilization analysis (dead neurons / effective rank).
- **Elo tracking & champion gating** (`evaluations/elo_tracker.py`) — Bradley-Terry Elo over the full match graph, anchored at Heuristik@200 = 1000; roster: current champion@400 + previous champion@400. A new model becomes champion (= next self-play generator) only by beating the incumbent.
- **Diagnostics suite** — sibling-ranking Kendall-tau vs. exact solver, per-round value R², noise-floor variance decomposition (bias-corrected), self-play diversity report, paired-seed arena A/B harness (McNemar).
- **Web Interface** (`server.py` + `static/`) — Flask API on top of the Rust engine, browser UI for playing against the AI and a replay viewer.

---

## 📂 Project Structure

```text
📦 mosaic-AI/  (project root)
├── 📂 engine/                 # Rust crate (mosaic_rust) — all game/search/self-play logic
│   ├── 📂 src/
│   │   ├── 📜 state.rs, board.rs, dome.rs, factory.rs, supply.rs, tile.rs   # Game state
│   │   ├── 📜 game.rs, moves.rs, execution.rs, round_end.rs, validation.rs # Rules/move execution
│   │   ├── 📜 scoring.rs, tiling_solver.rs   # Exact round/end scoring (DFS solver)
│   │   ├── 📜 mcts.rs          # Heuristic MCTS (baseline opponent; Progressive Widening)
│   │   ├── 📜 net_mcts.rs      # Gumbel AlphaZero search (+ legacy PUCT toggle)
│   │   ├── 📜 round5.rs        # Exact alpha-beta endgame (round 5)
│   │   ├── 📜 round_transition*.rs # Chance-node sampling + TD-bootstrap labels (node-budgeted)
│   │   ├── 📜 net.rs           # ONNX inference incl. batch=2 eval_pair (tract-onnx)
│   │   ├── 📜 features.rs      # State → feature vector (Rust mirror of engine/py/neural_net.py)
│   │   ├── 📜 self_play.rs     # Rayon-parallel self-play/arena loops + diagnostics
│   │   ├── 📜 serialize.rs     # State → JSON (UI/Python)
│   │   └── 📜 py.rs / lib.rs   # PyO3 bindings (`mosaic_rust` module, engine_config_json, ...)
│   ├── 📂 py/
│   │   └── 📜 neural_net.py    # MosaicNet (PyTorch), MosaicDataset, state_to_tensor, action_to_id
│   ├── 📜 Cargo.toml
│   └── 📜 pyproject.toml       # maturin build config
├── 📂 evaluations/            # STATUS.md (living status/roadmap), elo_tracker.py + elo_history.csv,
│   │                          #   diversity report, paired-arena harnesses, diagrams.txt, eval reports
├── 📂 data/                   # Self-play output (.pkl) + run manifests + HDF5 training cache
│   └── 📂 archive_*/          # Retired corpora (never mixed back in — regime consistency)
├── 📂 models/                 # Checkpoints (.pth), ONNX exports (.onnx), training manifests, loss plots
├── 📂 static/                 # Web UI (index.html, debug.html, replay viewer, css/js)
├── 📂 utils/                  # diagnosis.py, model_info.py, git_tree.py
├── 📂 docs/                   # engine_manual.md, reference CSVs (bonus chip/dome colors)
├── 📂 archive/                # Legacy: old pure-Python engine/agents, superseded eval reports
├── 📜 config.py               # Hyperparameters (INPUT_SIZE, NUM_ACTIONS, HIDDEN_SIZE, LR, ...)
├── 📜 self_play.py            # ▶️ Self-play driver (calls into Rust, per-game flush, manifests)
├── 📜 train.py                # ▶️ Training (PyTorch/CUDA) + corpus log + auto ONNX export
├── 📜 export_onnx.py          # ▶️ .pth → .onnx (also run automatically at the end of train.py)
├── 📜 arena.py                # ▶️ Net-vs-heuristic / net-vs-net matches
└── 📜 server.py               # ▶️ Flask web server (browser UI)
```

---

## 🚀 Quickstart

### 0. Build the Rust engine (once, then again whenever Rust code changes)
```bash
cd engine
pip install . --force-reinstall --no-deps
```

### 1. Generate self-play data
```bash
# Network self-play (production path: Gumbel search, completed-Q policy targets,
# TD-bootstrap value labels, per-game flush, run manifest):
python self_play.py --mode network --model alphazero_v10_best.onnx --games 2000 --sims 400 --version netcq2 --threads 8

# Heuristic MCTS (bootstrap / no network dependency):
python self_play.py --mode mcts --games 1500 --sims 200 --version v0
```

### 2. Train the neural network
```bash
# Warm-start from the current champion (shape mismatches are filtered automatically);
# logs the corpus composition per version prefix and writes a training manifest:
python train.py --name v12 --load v10 --epochs 100
```
Automatically exports to `.onnx` at the end.

### 3. Elo / champion gate
```bash
# Roster matches (see evaluations/elo_tracker.py header for the workflow), then:
python evaluations/elo_tracker.py report
```
Participants for raw matches are configured in `arena.py`'s `__main__` block. Set
`threads=` explicitly (the Rust default is single-threaded).

### 4. Web interface
```bash
python server.py
# http://localhost:5000
```

---

## 🏗️ Architecture

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
ONNX export carries exactly these 4 output tensors (policy/value/moon/points).

**Value target** (`VALUE_SCHEMA_VERSION = 15`): soft symmetric margin
`tanh((own − opp)/50)` on *unclamped* shadow scores (the visible score floors at 0,
the training label keeps counting penalties below it), overridden by the sampled
round-transition value where available, then blended with a 2-round-ahead
TD-bootstrap value (`TD_LAMBDA = 0.5`).

### State Tensor (708 features)
Coarse layout (exact source of truth: `engine/src/features.rs` ↔ `state_to_tensor`):
global state (round/phase/bag), active scoring tiles, small factories (sun colors +
bonus-chip state), large factory, both player boards in ego perspective (score,
pattern rows, floor, chips, chip-completability), both 3×3 dome grids incl.
end-scoring/geometry/line features, moon-side stacks, dome display, hidden-stack
composition mask + wild fraction, bag/tower color fractions.

### Action Space (406 actions)
| Type | IDs | Description |
|---|---|---|
| pass | 0 | No legal move |
| end_tiling | 1 | End the tiling phase |
| stone | 10–273 | Take tiles: factory × color × target row |
| tiling | 274–327 | Place a tile: pattern row × slot |
| choose_dome_slot | 328–354 | Dome placement **stage 1**: display tile × slot |
| choose_draw_stack_slot | 355–390 | Stack-draw placement **stage 1**: drawn tile × slot |
| choose_dome_rotation | 391–394 | Dome placement **stage 2**: rotation (shared by both paths) |
| use_chips | 395–400 | Complete a pattern row with bonus chips |
| bonus_chip | 401–404 | Take a revealed bonus chip |
| dome_stack_peek | 405 | Pay 1 point, draw one hidden plate (repeatable) |

Dome placement is a genuine **two-stage search node** (tile+slot, then rotation) —
this replaced an earlier prior-factorization approach and shrinks the effective
branching factor inside the tree.

---

## 🔄 Training Pipeline: Champion Protocol

Full history and current numbers in [`evaluations/STATUS.md`](evaluations/STATUS.md) — short version:

```
Self-play: ~2000 games generated by the CURRENT champion (network mode)
        ↓
Training corpus: fresh champion games (+ ~1000 each from the last 2 retired
champions, assembled manually — old-rule/old-label corpora never re-enter)
        ↓
Train candidate (warm-start from the champion, TD_LAMBDA=0.5)
        ↓
Offline diagnostics: per-round value R², sibling Kendall-tau, label histogram
        ↓
Elo roster: candidate vs. Heuristik@200 (anchor=1000) and GATING match vs. the
champion @400 sims — champion only changes on a proven win
        ↓
Champion generates the next round → next candidate
```

Current state: champion **v10_best** (Elo 858 vs. anchor 1000); v11 (first
completed-Q + TD-bootstrap generation) did not gate (43:57). Statistical
ground rules learned the hard way: n=100 arena margins carry a ±6–10 pp noise
band — paired-seed McNemar A/Bs are the standard for tuning decisions, and
single sub-n=100 arms never overwrite reference numbers.

---

## 🛠️ Diagnostics & Tools

```bash
python evaluations/elo_tracker.py report        # Elo table (Bradley-Terry, anchored)
python evaluations/selfplay_diversity_report.py # opening entropy / collapse check
python -m utils.diagnosis                       # policy quality analysis
python -m utils.model_info --version v10        # model metadata
```
Rust-side diagnostics exposed via `mosaic_rust`: `sibling_ranking_diagnostic`,
`value_noise_floor_diagnostic`, `draw_stack_peek_impact_diagnostic`,
`engine_config_json`, profiling counters.

---

## ⚙️ Configuration

| Parameter | Value | Where | Description |
|---|---|---|---|
| `INPUT_SIZE` | 708 | config.py | State tensor size |
| `NUM_ACTIONS` | 406 | config.py | Action space size |
| `HIDDEN_SIZE` | 512 | config.py | Neurons per hidden layer |
| `LEARNING_RATE` | 0.0004 | config.py | Adam learning rate |
| `VALUE_WEIGHT` / `POINTS_WEIGHT` | 0.2 / 0.5 | config.py | Aux-loss weights (policy loss dominates) |
| `TD_LAMBDA` | 0.5 | engine/py/neural_net.py | TD-bootstrap blend in the value target |
| `USE_GUMBEL_SEARCH` | true | engine/src/net_mcts.rs | Gumbel search (false = legacy PUCT) |
| `GUMBEL_TOP_M` | 16 | engine/src/net_mcts.rs | Root candidates for Sequential Halving |
| `FLOOR_SHAPING_WEIGHT` | 0.3 | engine/src/net_mcts.rs | Exact floor-penalty leaf shaping (validated) |
| `DETERMINIZE_ROOT_HIDDEN_INFO` | true | engine/src/net_mcts.rs | One-world root determinization |
| `NUM_DETERMINIZATIONS` | 1 | engine/src/net_mcts.rs | ISMCTS multi-world toggle (tested: 1 is best) |

Search/training constants live as documented Rust/Python constants with their
calibration history in code comments; every self-play and training run snapshots
the active configuration into a JSON manifest next to its output.
