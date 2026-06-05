# config.py
import os
from pathlib import Path

# Der absolute Pfad zu deinem Hauptordner (mosaic-AI)
BASE_DIR = Path(__file__).resolve().parent

# --- DYNAMISCHE PFADE ---
# (Egal, von wo du das Skript startest, die Pfade stimmen immer!)
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"

# --- ORDNER AUTOMATISCH ERSTELLEN ---
# Verhindert "File Not Found"-Fehler, wenn jemand das Repo frisch klont oder
# die Ordner durch die .gitignore-Datei noch nicht existieren.
DATA_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# --- GLOBALE TRAININGSPARAMETER ---
# Ändere diese Werte hier, und das gesamte Projekt verhält sich anders!
MCTS_SIMULATIONS_TRAINING = 40     # Schnellere Simulation für Datengenerierung
MCTS_SIMULATIONS_ARENA = 150       # Volle Denkkraft für das Titel-Match
TEMPERATURE_MOVES = 15             # Nach wie vielen Zügen wird Exploitation forciert?