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
INPUT_SIZE = 684        # state_to_tensor (564 Basis + 74 Endwertungs-/Geometrie + 46 Linien-Features; 60 je Spieler)
                        # (redundantes unused_chip_colors-Feature entfernt: -10; bag_count ergänzt: +1;
                        #  floor-Normierung /7.0 -> /4.0 korrigiert (kein Dim-Effekt);
                        #  Bonuschip-Farbmaske je Fabrik ergänzt: +5*4=+20; 673 -> 664 -> 684)
NUM_ACTIONS = 482       # action_to_id Ausgabebereich

# --- TRAININGSPARAMETER NN ---
BATCH_SIZE    = 256
HIDDEN_SIZE   = 512   # Neuronen pro Hidden Layer (2^x)
LEARNING_RATE = 0.0006
VALUE_WEIGHT  = 15  # war 0.5 — hochskaliert, weil das neue Punkte-Marge-Value-Target
                      # (siehe engine/py/neural_net.py, VALUE_SCHEMA_VERSION) eine deutlich
                      # kleinere charakteristische Streuung hat als das alte ±1-Target:
                      # Stichprobe über ~27k reale Self-Play-Schritte ergab std(target)≈0.22
                      # (vs. std=1.0 beim alten ±1-Ziel) → Faktor ~4.6. Ohne Anpassung würde
                      # der Value-Loss-Beitrag zum Gesamtloss weiter schrumpfen und der
                      # Value-Head faktisch kaum noch trainiert — genau das Gegenteil vom
                      # Ziel dieser Änderung. Erster Ansatz, an frühen Epochen (Value:Policy-
                      # Verhältnis im Log) nachjustieren.
