# config.py
import os
from pathlib import Path

# Der absolute Pfad zu deinem Hauptordner (mosaic-AI)
BASE_DIR = Path(__file__).resolve().parent

# --- DYNAMISCHE PFADE ---
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"

# --- ORDNER AUTOMATISCH ERSTELLEN ---
# Verhindert "File Not Found"-Fehler, wenn jemand das Repo frisch klont oder
# die Ordner durch die .gitignore-Datei noch nicht existieren.
DATA_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# --- GLOBALE TRAININGSPARAMETER ---
MCTS_SIMULATIONS_TRAINING = 40     # Schnellere Simulation für Datengenerierung
MCTS_SIMULATIONS_ARENA = 150       # Volle Denkkraft für das Titel-Match
TEMPERATURE_MOVES = 15             # Nach wie vielen Zügen wird Exploitation forciert?

# --- NETZWERK PARAMETER ---
INPUT_SIZE = 291        # state_to_tensor Ausgabegröße (129 Basis + 162 Kuppel)
NUM_ACTIONS = 410       # action_to_id Ausgabebereich

# --- TRAININGSPARAMETER NN ---
BATCH_SIZE    = 256
LEARNING_RATE = 0.001
VALUE_WEIGHT  = 0.1