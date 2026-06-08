# 🧩 Mosaic-AI: Tile-Drafting AlphaZero Environment

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PyTorch](https://img.shields.io/badge/PyTorch-Deep%20Learning-ee4c2c.svg)](https://pytorch.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Mosaic-AI** is a complete Reinforcement Learning framework for training AlphaZero-style neural networks on a complex two-player tile-drafting and dome-building board game.

> **⚠️ Disclaimer:** This project is an educational Reinforcement Learning experiment implementing a generic tile-drafting and wall-tiling game mechanic. It was built from scratch for research purposes and is **not** affiliated with, endorsed by, or related to any existing commercial board games, publishers, or registered trademarks.

---

## 🧠 Core Features

- **Custom Game Engine** — Full headless Python engine with multi-phase gameplay: tile drafting (sun/moon sides), dome placement, bonus chips, pattern rows, floor penalty, and end scoring
- **MCTS** — Monte Carlo Tree Search with heuristic rollouts, greedy-bias exploration, and lazy action expansion
- **AlphaZero Agent** — PUCT-based search with neural network priors stored directly on tree nodes (no global cache, no RAM leak)
- **Self-Play Pipeline** — MCTS bootstrap → Network self-play loop with temperature scheduling and policy caching
- **The Arena** — Automated tournament with ELO ratings, branching factor tracking, and detailed game logs
- **Web Interface** — Flask server with browser UI for playing against the AI and replaying games

---

## 📂 Project Structure

```text
📦 mosaic-AI/  (Hauptordner)
├── 📂 agents/
│   ├── 📜 __init__.py
│   ├── 📜 agent_env.py       # MosaicEnv: OpenAI Gym-style wrapper, abstract action representation
│   ├── 📜 agents.py          # RandomAgent, GreedyAgent
│   ├── 📜 alphazero.py       # AlphaZeroAgent: PUCT search with node-based priors
│   ├── 📜 mcts.py            # MCTSAgent, HeuristicMCTSAgent, MCTSNode, run_episode_mcts
│   ├── 📜 neural_net.py      # MosaicNet (399→512→512→512), state_to_tensor, action_to_id, MosaicDataset
│   └── 📜 shaping.py         # Reward shaping: pattern rows, floor penalty, dome bonus
├── 📂 archive/
│   └── 📜 self_play_v0.py    # Legacy self-play script
├── 📂 docs/
│   ├── 📜 bonus_chips_colors.csv
│   └── 📜 dome_colors.csv
├── 📂 engine/
│   ├── 📜 __init__.py
│   ├── 📜 board.py           # PlayerBoard, DomeGrid
│   ├── 📜 dome.py            # DomeTile, DomeSlot, SpaceType (NORMAL/WILD/SPECIAL)
│   ├── 📜 execution.py       # execute_move, _execute_moon_take, bonus chip reveal, log formatting
│   ├── 📜 factory.py         # SmallFactory, LargeFactory, moon stacks, bonus chips
│   ├── 📜 game.py            # Game class: apply(), valid_moves(), phase transitions
│   ├── 📜 moves.py           # Move, TakeAction, PlaceAction, PlaceDomeTileMove, DrawFromStackMove
│   ├── 📜 round_end.py       # check_drafting_complete, can_complete_row_with_chips, process_unplaceable_rows
│   ├── 📜 scoring.py         # ScoringTile subclasses, calculate_end_scoring
│   ├── 📜 serializer.py      # serialize_state → obs dict for neural net
│   ├── 📜 setup.py           # GameState dataclass, new_game()
│   ├── 📜 supply.py          # Tile bag, tower
│   ├── 📜 tile.py            # TileColor enum
│   └── 📜 validation.py      # generate_valid_moves, validate_tiling_action
├── 📂 models/                # Trained model checkpoints (.pth)
├── 📂 static/
│   ├── 📂 css/
│   │   └── 📜 style.css
│   ├── 📂 js/
│   │   └── 📜 app.js
│   ├── 📜 index.html         # Main game UI
│   └── 📜 replay.html        # Game replay viewer
├── 📂 utils/
│   ├── 📜 __init__.py
│   ├── 📜 debug_data.py      # Training data inspector
│   ├── 📜 debug_game.py      # Game state debugger
│   ├── 📜 diagnosis.py       # Policy quality analysis, sanity checks (options 1-4)
│   ├── 📜 git_tree.py        # Project tree printer
│   ├── 📜 model_info.py      # Model metadata viewer
│   └── 📜 replay_server.py   # Replay file server
├── 📜 .gitignore
├── 📜 README.md
├── 📜 arena.py               # ▶️ Tournament runner with ELO ratings
├── 📜 config.py              # Hyperparameters: INPUT_SIZE=399, NUM_ACTIONS=482, HIDDEN_SIZE=512
├── 📜 self_play.py           # ▶️ Generate training data (MCTS or Network self-play)
├── 📜 server.py              # ▶️ Flask web server for browser UI
└── 📜 train.py               # ▶️ Train neural network (PyTorch, CUDA)
```

---

## 🚀 Quickstart

### 1. Generate Training Data (MCTS Bootstrap)
```bash
python self_play.py --mode mcts --games 500 --sims 50 --version v0a --depth 0
```

### 2. Train Neural Network
```bash
python train.py --name v1 --epochs 30
# Warm-start from previous version (same architecture required):
python train.py --name v2 --load v1 --epochs 30
```

### 3. Network Self-Play
```bash
python self_play.py --mode network --games 500 --sims 40 --version v1 --depth 0
```

### 4. Arena
```bash
python arena.py
```

### 5. Web Interface
```bash
python server.py
# Open http://localhost:5000
```

---

## 🏗️ Architecture

### Neural Network (`MosaicNet`)
```
Input (399) → Linear(512) → BN → ReLU
           → Linear(512) → BN → ReLU
           → Linear(512) → ReLU
           ┌→ Policy Head: Linear(482) — action logits
           └→ Value Head:  Linear(128) → ReLU → Linear(1) → Tanh
```

### State Tensor (399 features)
| Block | Features | Description |
|---|---|---|
| Global | 2 | round/6, phase/3 |
| Scoring Tiles | 8 | active scoring tile IDs (one-hot) |
| Small Factories ×4 | 28 | sun colors(5) + has_chip(1) + chip_revealed(1) = 7 each |
| Large Factory | 5 | sun color counts/10 |
| Players ×2 | 114 | score, estimated_score, marker, chip colors, pattern lines ×6, floor, tokens_used, chips_taken, bonus_chip colors |
| Dome Grid ×2 | 162 | 9 slots × 9 features each |
| Moon Stacks ×4 | 60 | 3 positions × 5 colors per factory |
| GF Moon Pool | 5 | color counts/10 |
| Dome Display | 24 | 3 plates × 4 spaces × (filled + required_color) |
| Dome Stack | 1 | remaining plates/20 |

### Action Space (482 actions)
| Type | IDs | Description |
|---|---|---|
| pass | 0 | No valid moves |
| end_tiling | 1 | End tiling phase |
| stone | 10–249 | Take stones: factory_index(0-5) × color(5) × row(-1..6) |
| tiling | 274–327 | Place tile: pattern_row × slot_row × slot_col |
| dome | 328–435 | Place dome from display: display_index × slot × rotation |
| dome_stack | 436–471 | Draw from stack: slot × rotation |
| use_chips | 472–477 | Use bonus chips for pattern row |
| bonus_chip | 478–481 | Take bonus chip from factory |

---

## 🔄 Training Pipeline

```
MCTS Bootstrap (depth=0, 50 sims)
        ↓
   ~1000 games → train V1
        ↓
Network Self-Play V1 (40 sims)
        ↓
   ~500 games → train V2 (warm-start)
        ↓
Network Self-Play V2 (40 sims)
        ↓
   ~500 games → train V3 (warm-start)
        ↓
        ...
```

### Current Results

| Model | Architecture | Policy Loss | Value Loss | vs MCTS(50,d=5) |
|---|---|---|---|---|
| V1 | 399→256→256→256 | 31.6% | 0.025 | **60%** (40 games) |
| V2 | 399→512→512→512 | 27.1% | 0.020 | **60%** (40 games) |

> `AlphaZeroAgent(sims=40)` vs `HeuristicMCTSAgent(sims=50, rollout_depth=d)`

---

## 🛠️ Diagnosis & Tools

```bash
# Policy quality analysis
python -m utils.diagnosis

# Model metadata
python -m utils.model_info --version v2

# Project file tree
python utils/git_tree.py
```

---

## ⚙️ Configuration (`config.py`)

| Parameter | Value | Description |
|---|---|---|
| `INPUT_SIZE` | 399 | State tensor size |
| `NUM_ACTIONS` | 482 | Action space size |
| `HIDDEN_SIZE` | 512 | Hidden layer neurons |
| `BATCH_SIZE` | 256 | Training batch size |
| `LEARNING_RATE` | 0.001 | Adam optimizer LR |
| `VALUE_WEIGHT` | 0.15 | Value loss weight in total loss |