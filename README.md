# 🧩 Mosaic-AI: Tile-Drafting AlphaZero Environment

[![Rust](https://img.shields.io/badge/engine-Rust-orange.svg)](https://www.rust-lang.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-Deep%20Learning-ee4c2c.svg)](https://pytorch.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Mosaic-AI** is a complete Reinforcement Learning framework for training AlphaZero-style neural networks on a complex two-player tile-drafting and dome-building board game.

> **⚠️ Disclaimer:** This project is an educational Reinforcement Learning experiment implementing a generic tile-drafting and wall-tiling game mechanic. It was built from scratch for research purposes and is **not** affiliated with, endorsed by, or related to any existing commercial board games, publishers, or registered trademarks.

---

## 🧠 Core Features

- **Rust Game Engine** (`engine/`, PyO3/maturin) — full headless engine covering the whole multi-phase gameplay (sun/moon drafting, dome placement, bonus chips, pattern rows, floor penalty, exact end scoring). GIL-free, rayon-parallel self-play/arena.
- **Heuristic MCTS** (`engine/src/mcts.rs`) — Progressive Widening with a depth-dependent cap (full breadth at the root, capped breadth + UCB-driven depth from depth 1 onward), leaf evaluation via an exact tiling solver (no rollouts).
- **AlphaZero Agent** (`engine/src/net_mcts.rs`) — PUCT search with network priors (including Plackett-Luce moon-order priors), Stage 1 (DFS leaf) and Stage 2 (network-value leaf, gated behind a readiness probe).
- **Self-Play Pipeline** (`self_play.py`) — thin Python driver over the Rust self-play loop; MCTS and network modes, chunked for live progress reporting.
- **Champion/Candidate Training** (`train.py`) — warm-start with shape-mismatch filtering (architecture can change between generations, e.g. the policy head), plateau-based early stopping, R² tracking for the value head, automatic network-utilization analysis (dead neurons / effective rank), and a Stage-2 readiness probe after every run.
- **The Arena** (`arena.py`) — network-vs-network, network-vs-heuristic, and pure-heuristic round robins with Elo ratings and a significance gate for the champion protocol.
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
│   │   ├── 📜 mcts.rs          # Heuristic MCTS (depth-dependent Progressive Widening)
│   │   ├── 📜 net_mcts.rs      # AlphaZero PUCT search (network priors + Plackett-Luce moon order)
│   │   ├── 📜 net.rs           # ONNX inference (tract-onnx)
│   │   ├── 📜 features.rs      # State → feature vector (Rust mirror of engine/py/neural_net.py)
│   │   ├── 📜 self_play.rs     # Rayon-parallel self-play/arena loops
│   │   ├── 📜 serialize.rs     # State → JSON (UI/Python)
│   │   └── 📜 py.rs            # PyO3 bindings (`mosaic_rust` module)
│   ├── 📂 py/
│   │   └── 📜 neural_net.py    # MosaicNet (PyTorch), MosaicDataset, state_to_tensor, action_to_id
│   ├── 📜 Cargo.toml
│   └── 📜 pyproject.toml       # maturin build config
├── 📂 evaluations/            # Per-generation eval reports (v*_eval.md) + STAGE2_TODO.md (champion protocol, roadmap)
├── 📂 data/                   # Self-play output (.pkl) + HDF5 training cache
├── 📂 models/                 # Trained checkpoints (.pth), ONNX exports (.onnx), loss plots
├── 📂 static/                 # Web UI (index.html, debug.html, replay viewer, css/js)
├── 📂 utils/                  # diagnosis.py, model_info.py, git_tree.py
├── 📂 docs/                   # engine_manual.md, reference CSVs (bonus chip/dome colors)
├── 📂 archive/                # Legacy: old pure-Python engine/agents (python_engine/, python_agents/), history notes
├── 📜 config.py               # Hyperparameters (INPUT_SIZE, NUM_ACTIONS, HIDDEN_SIZE, LR, VALUE_WEIGHT, ...)
├── 📜 self_play.py            # ▶️ Self-play driver (calls into Rust, groups/pickles step records)
├── 📜 train.py                # ▶️ Training (PyTorch/CUDA) + auto ONNX export + readiness probe
├── 📜 export_onnx.py          # ▶️ .pth → .onnx (also run automatically at the end of train.py)
├── 📜 arena.py                # ▶️ Tournaments/comparisons with Elo rating
└── 📜 server.py               # ▶️ Flask web server (browser UI)
```

---

## 🚀 Quickstart

### 0. Build the Rust engine (once, then again whenever Rust code changes)
```bash
cd engine
python -m maturin build --release
python -m pip install --force-reinstall target/wheels/mosaic_rust-*.whl
```

### 1. Generate self-play data
```bash
# Heuristic MCTS (e.g. bootstrap, no network dependency)
python self_play.py --mode mcts --games 1500 --sims 100 --version v0

# AlphaZero network self-play (Stage 1 = DFS leaf, Stage 2 = network-value leaf)
python self_play.py --mode network --model alphazero_v4.onnx --stage 1 --games 2000 --sims 400 --version v4b
```

### 2. Train the neural network
```bash
python train.py --name v1 --epochs 100
# Warm-start from a previous generation (shape mismatches, e.g. from architecture
# changes, are filtered automatically and only those layers start fresh):
python train.py --name v2 --load v1 --epochs 100
```
Automatically exports to `.onnx` at the end and runs the Stage-2 readiness probe right after.

### 3. Arena (Elo, champion gate)
Participants are configured in the `if __name__ == "__main__"` block of `arena.py` (no CLI flags):
```bash
python arena.py
```

### 4. Web interface
```bash
python server.py
# http://localhost:5000
```

---

## 🏗️ Architecture

### Neural Network (`MosaicNet`, `engine/py/neural_net.py`)
```
Input (684) → Linear(512) → BN → ReLU
           → Linear(512) → BN → ReLU
           → Linear(512) → ReLU
           ┌→ Policy Head: Linear(256) → ReLU → Linear(482)   — action logits
           ├→ Value Head:  Linear(128) → ReLU → Linear(1) → Tanh
           └→ Moon-Order Head: Linear(32) → ReLU → Linear(5)   — Plackett-Luce scores
```
`policy_hidden=0` reconstructs the old, single-layer policy head (for older checkpoints,
auto-detected by `export_onnx.py`).

### State Tensor (684 features)
| Block | Description |
|---|---|
| Global | Round, phase, bag count |
| Scoring tiles | 8-dim one-hot of active tiles |
| Small factories ×4 | Sun colors, bonus-chip status + color mask |
| Large factory | Sun color counts |
| Players ×2 (ego perspective) | Score, estimated_score, pattern lines, floor, bonus chips, per-row chip-completability |
| Dome grid ×2 | 9 slots × 9 features (filled/color/type/locked) |
| End-scoring/geometry features ×2 | Scoring-tile points, row/column/diagonal fill, corners, wild/special state |
| Line geometry ×2 | Contiguous row/column runs, cluster score, growth potential |
| Small-factory moon side ×4 | Stack order per position |
| Large-factory moon pool | Color counts |
| Dome display + stack | Scoring slots, remaining plates |

### Action Space (482 actions)
| Type | IDs | Description |
|---|---|---|
| pass | 0 | No legal move |
| end_tiling | 1 | End the tiling phase |
| stone | 10–249 | Take a tile: factory index × color × target row |
| tiling | 274–327 | Place a tile: pattern row × slot |
| dome | 328–435 | Place a dome plate from the display: display index × slot × rotation |
| dome_stack | 436–471 | Draw a dome plate from the stack: slot × rotation |
| use_chips | 472–477 | Use bonus chips to complete a pattern row |
| bonus_chip | 478–481 | Take a bonus chip from a factory |

---

## 🔄 Training Pipeline: Champion/Candidate Protocol

Full details in [`evaluations/STAGE2_TODO.md`](evaluations/STAGE2_TODO.md) — short version:

```
Self-play (current champion, Stage 1 / DFS leaf)
        ↓
Training window: max. 2 retired champions (2000 games each) + current champion (up to 3×2000)
        ↓
Train candidate (warm-start from the champion)
        ↓
Arena gate: candidate vs. champion, 100 games — needs ≥60:40 (z≈2.0), otherwise champion stays
        ↓
Champion generates another self-play round → next candidate
```

If the champion stays unbeaten with the full 10,000-game window: thin the window first
(cheapest step), then generate another round from the champion at the same sim count, and
only as a last resort raise the sim count for new rounds. Stage 2 (network value as the
search leaf) is only unlocked once the Stage-2 readiness probe (0:0 ratio Stage2/Stage1
≤1.5×) turns green — currently still 🔴/🟡 across all generations.

Current champion, generation history, and arena results: see `evaluations/*.md`.

---

## 🛠️ Diagnostics & Tools

```bash
# Policy quality analysis
python -m utils.diagnosis

# Model metadata
python -m utils.model_info --version v4

# Project file tree
python utils/git_tree.py
```

---

## ⚙️ Configuration (`config.py`)

| Parameter | Current value | Description |
|---|---|---|
| `INPUT_SIZE` | 684 | State tensor size |
| `NUM_ACTIONS` | 482 | Action space size |
| `HIDDEN_SIZE` | 512 | Neurons per hidden layer |
| `BATCH_SIZE` | 256 | Training batch size |
| `LEARNING_RATE` | 0.0004 | Adam learning rate |
| `VALUE_WEIGHT` | 15 | Weight of the value loss in the combined loss (compensates for the narrow spread of the score-margin target vs. the old ±1 target) |

`LEARNING_RATE` and `VALUE_WEIGHT` are currently under active parameter sweeps
(see `evaluations/v6*_eval.md`) — values may change between generations.
