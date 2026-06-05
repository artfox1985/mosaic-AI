# 🧩 Mosaic-AI: Tile-Drafting AlphaZero Environment

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PyTorch](https://img.shields.io/badge/PyTorch-Deep%20Learning-ee4c2c.svg)](https://pytorch.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Mosaic-AI** is a custom-built Reinforcement Learning environment and AI framework designed to train neural networks playing a complex, drafting- and pattern-building board game. 

> **⚠️ Disclaimer:** This project is an educational Reinforcement Learning experiment. It implements a generic tile-drafting and wall-tiling game mechanic. It was built completely from scratch for research purposes (AlphaZero-style AI training) and is **not** affiliated with, endorsed by, or related to any existing commercial board games, publishers, or registered trademarks.

## 🧠 Core Features

* **Custom Game Engine:** A highly optimized, headless Python engine handling complex game states, tile drafting from a central supply, and multi-phase scoring.
* **MCTS (Monte Carlo Tree Search):** A fully functional MCTS implementation with heuristic fallbacks and UCB1 exploration.
* **AlphaZero Architecture:** A deep neural network (`neural_net.py`) evaluating board states (Value) and predicting move probabilities (Policy).
* **Self-Play Pipeline:** Automated data generation through self-play, balancing exploration (temperature) and exploitation.
* **The Arena:** An automated tournament script to match different AI generations against each other and calculate ELO ratings.

## 📂 Project Structure

```text
📦 mosaic-AI/ 
├── 📂 agents/          # AI logic (MCTS, AlphaZero Agent, Neural Net)
├── 📂 engine/          # Core game rules, state validation & mechanics
├── 📂 server/          # Backend server for web replay visualization
├── 📂 static/          # HTML/JS/CSS for the browser interface
├── 📂 utils/           # Development & debugging tools
├── 📜 config.py        # Global paths and training hyperparameters
├── 📜 self_play.py     # ▶️ Run to generate training data via self-play
├── 📜 train.py         # ▶️ Run to train the Neural Network (PyTorch)
└── 📜 arena.py         # ▶️ Run to battle AI agents against each other