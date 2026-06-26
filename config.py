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

# --- NETZWERK PARAMETER ---
INPUT_SIZE = 627        # state_to_tensor Ausgabegröße (553 Basis + 74 Endwertungs-/Geometrie-Features, 37 je Spieler)
NUM_ACTIONS = 482       # action_to_id Ausgabebereich

# --- TRAININGSPARAMETER NN ---
BATCH_SIZE    = 256
HIDDEN_SIZE   = 256   # Neuronen pro Hidden Layer (2^x)
LEARNING_RATE = 0.0006
VALUE_WEIGHT  = 0.5

# --- VALUE-TARGET PARAMETER (abgestuftes Signal) ---
# Steuern wie scores → win_val umgerechnet werden (compute_win_val).
# Früh: kleine Werte (mehr Signal aus wenig Punkten), später hochsetzen.
MARGIN_CAP       = 15   # Punktedifferenz ab der die Margin-Komponente maximal ist
MAX_WINNER_SCORE = 40   # Winner-Score ab dem die Score-Komponente maximal ist