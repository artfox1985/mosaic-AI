import os
import glob
import pickle
import torch
import torch.nn as nn
from torch.utils.data import Dataset
from config import NUM_ACTIONS

COLOR_MAP = {"blau": 0, "gelb": 1, "rot": 2, "schwarz": 3, "weiß": 4, None: -1, "special": 5}
PHASE_MAP = {"drafting": 0, "tiling": 1, "end": 2, "final": 3}

def state_to_tensor(data):
    """Macht aus deinem Serializer-Dict ein flaches Zahlen-Array für PyTorch."""
    features = []
    
    # 1. Globale Infos
    features.append(data.get("round", 0) / 6.0)
    features.append(PHASE_MAP.get(data.get("phase", "drafting"), 0) / 3.0)
    
    # 2. Wertungsplatten (Welche 3 von 8 sind aktiv?)
    scoring_ids = data.get("scoring_tile_ids", [])
    features.extend([1.0 if i in scoring_ids else 0.0 for i in range(8)])
    
    # 3. Kleine Manufakturen (Steine zählen + BONUS CHIPS)
    for f in data.get("factories", []):
        counts = [0] * 5
        for c_str in f.get("sun", []):
            if c_str in COLOR_MAP and COLOR_MAP[c_str] != -1:
                counts[COLOR_MAP[c_str]] += 1
        features.extend([c / 5.0 for c in counts])
        
        # NEU: Hat die Fabrik einen Bonus-Chip?
        has_chip = 1.0 if f.get("bonus_chip") is not None else 0.0
        features.append(has_chip)
        
    # 4. Große Manufaktur
    lf = data.get("large_factory", {})
    lf_sun = [0] * 5
    for c_str in lf.get("sun", []):
        if c_str in COLOR_MAP and COLOR_MAP[c_str] != -1:
            lf_sun[COLOR_MAP[c_str]] += 1
    features.extend([c / 10.0 for c in lf_sun])
    
    # 5. Spieler (Ego-Perspektive)
    curr_pi = data.get("current_player", 0)
    enemy_pi = 1 - curr_pi
    players = data.get("players", [])
    
    if len(players) == 2:
        me = players[curr_pi]
        enemy = players[enemy_pi]
        
        for p in [me, enemy]:
            features.append(p.get("score", 0) / 100.0)
            features.append(p.get("estimated_score", 0) / 100.0)
            features.append(1.0 if p.get("marker", False) else 0.0)
            
            # NEU: Chip-Farben als numerische Features (5-dim Vektor)
            # Mapping der Farben auf 0-4 (deine COLOR_MAP)
            chip_features = [0.0] * 5
    
            # Zugriff auf die Liste aus deinem Serializer
            chip_colors = p.get("unused_chip_colors", [])
            for c_name in chip_colors:
                c_id = COLOR_MAP.get(c_name, -1)
                if 0 <= c_id < 5:
                    chip_features[c_id] += 1.0
            
            # Normalisierung (z.B. durch 5.0, damit das Netz Werte in [0, 1] bekommt)
            features.extend([c / 5.0 for c in chip_features])
            
            # Musterreihen
            for row in p.get("pattern_lines", []):
                capacity = row.get("capacity", 1)
                features.append(len(row.get("tiles", [])) / capacity)
                color_id = COLOR_MAP.get(row.get("color"), -1)
                features.extend([1.0 if i == color_id else 0.0 for i in range(5)])
                
            # Straffläche
            features.append(len(p.get("floor", [])) / 7.0)
            
        # 6. Kuppelzustand (pro Spieler: 9 Slots × 9 Features = 81 Features × 2 = 162)
        COLOR_ID_MAP = {"blau": 1, "gelb": 2, "rot": 3, "schwarz": 4, "türkis": 5}

        for p in [me, enemy]:
            dome = p.get("dome_grid", [])
            for sr in range(3):
                for sc in range(3):
                    row = dome[sr] if sr < len(dome) else []
                    slot = row[sc] if sc < len(row) else None

                    if slot is None:
                        # Slot leer — 9 Nullen
                        features.extend([0.0] * 9)
                    else:
                        features.append(1.0)  # slot existiert
                        for space in slot.get("spaces", [{}, {}, {}, {}]):
                            # is_filled
                            filled = space.get("filled")
                            features.append(1.0 if filled is not None else 0.0)
                            # required_color normalisiert (0=kein, 1-5=farbe)
                            req = space.get("color")
                            features.append(COLOR_ID_MAP.get(req, 0) / 5.0)
            
    return torch.tensor(features, dtype=torch.float32)

def action_to_id(action: dict) -> int:
    t = action.get("type", "")
    if t == "pass":       return 0
    if t == "end_tiling": return 1

    if t == "stone":
        c_id   = max(0, COLOR_MAP.get(action.get("color"), 0))
        r_id   = action.get("row", 0) + 1          # -1..6 → 0..7
        src_str = action.get("source", "")
        if "SMALL_FACTORY_MOON" in src_str and action.get("factory_id") is None:
            src_id = 6                              # globaler Mond-Zug
        elif "LARGE" in src_str:
            src_id = 7
        else:
            src_id = action.get("factory_id", 0) or 0
        return min(10 + (c_id * 50) + (r_id * 8) + src_id, 273)

    if t == "tiling":
        pr = action.get("pattern_row", 0)
        sr = action.get("slot_row", 0)
        sc = action.get("slot_col", 0)
        return 274 + (pr * 9) + (sr * 3) + sc      # 274–327

    if t in ("dome", "dome_stack"):
        sr      = action.get("slot_row", 0)
        sc      = action.get("slot_col", 0)
        rot_idx = action.get("rotation", 0) // 90
        return 328 + (sr * 12) + (sc * 4) + rot_idx  # 328–363

    if t == "use_chips":
        return 364 + action.get("pattern_row", 0)  # 364–369

    if t == "bonus_chip":
        return 370 + (action.get("factory_id", 1) - 1)  # 370–373

    return 373  # Fallback auf letzte gültige ID

# --- 2. DATENSATZ & NETZWERK ---
class MosaicDataset(Dataset):
    def __init__(self, data_dir="data"):
        self.states, self.policies, self.values, self.masks = [], [], [], []
        files = glob.glob(os.path.join(data_dir, "*.pkl"))
        print(f"Lade Daten aus {len(files)} Dateien...")
        
        for f in files:
            with open(f, "rb") as file:
                game_data = pickle.load(file)
                for step in game_data:
                    self.states.append(state_to_tensor(step["state"]))
                    self.values.append(torch.tensor([step["value"]], dtype=torch.float32))
                    
                    t_policy = torch.zeros(NUM_ACTIONS, dtype=torch.float32)
                    for p in step["policy"]:
                        a_id = action_to_id(p["action"])
                        t_policy[a_id] += p["prob"]
                        
                    # Sicherheit: Array auf exakt 1.0 (100%) normalisieren
                    if t_policy.sum() > 0:
                        t_policy /= t_policy.sum()
                    self.policies.append(t_policy)
                    
                    # Action Mask — 1.0 für legale Aktionen, 0.0 für illegale
                    mask = torch.zeros(NUM_ACTIONS, dtype=torch.float32)
                    for move in step["state"].get("valid_moves", []):
                        mask[action_to_id(move)] = 1.0
                    self.masks.append(mask)
                    
        self.input_size = len(self.states[0]) if self.states else 100
        print(f"Datensatz geladen: {len(self.states)} Züge. (Features pro Zug: {self.input_size})")

    def __len__(self): return len(self.states)
    def __getitem__(self, idx): return self.states[idx], self.policies[idx], self.values[idx], self.masks[idx]


class MosaicNet(nn.Module):
    def __init__(self, input_size, num_actions=400):
        super(MosaicNet, self).__init__()
        self.body = nn.Sequential(
            nn.Linear(input_size, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU()
        )
        self.policy_head = nn.Sequential(
            nn.Linear(128, num_actions),
            nn.Softmax(dim=1)
        )
        self.value_head = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Tanh()
        )

    def forward(self, x):
        shared = self.body(x)
        return self.policy_head(shared), self.value_head(shared)
