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
INPUT_SIZE = 708        # state_to_tensor (564 Basis + 74 Endwertungs-/Geometrie + 46 Linien-Features; 60 je Spieler; +5 Beutel/Turm-Farbanteil; +18 Kuppelstapel-Maske; +1 wild_remaining_frac)
                        # (redundantes unused_chip_colors-Feature entfernt: -10; bag_count ergänzt: +1;
                        #  floor-Normierung /7.0 -> /4.0 korrigiert (kein Dim-Effekt);
                        #  Bonuschip-Farbmaske je Fabrik ergänzt: +5*4=+20; 673 -> 664 -> 684;
                        #  wild_remaining_frac ergänzt (Wild-Anteil der verdeckten Kuppelstapel-Restplatten): 707 -> 708)
NUM_ACTIONS = 483       # action_to_id Ausgabebereich (482 = dome_stack_peek: Aktion A Schritt 1, parameterlos)

# --- TRAININGSPARAMETER NN ---
BATCH_SIZE    = 256
HIDDEN_SIZE   = 512   # Neuronen pro Hidden Layer (2^x)
LEARNING_RATE = 0.0004
# Value-Head (Sieg/Niederlage) zurueckgeholt + neuer Punktestand-Aux-Head
# (siehe neural_net.py::VALUE_SCHEMA_VERSION). Beide Gewichte bewusst klein
# ggue. dem Policy-Loss (der bleibt das Trainingsziel, das die Suche/Self-Play
# tatsaechlich nutzt) -- reine Trunk-Zusatzsignale, kein Ersatz fuer Stufe 1/3.
VALUE_WEIGHT  = 1.0
POINTS_WEIGHT = 0.5
