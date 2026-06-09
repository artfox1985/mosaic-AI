import os
import glob
import pickle
import torch
import torch.nn as nn
from torch.utils.data import Dataset
from config import NUM_ACTIONS, HIDDEN_SIZE

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
        
        # Hat die Fabrik einen Bonus-Chip + ist er bereits aufgedeckt?
        has_chip = 1.0 if f.get("bonus_chip") is not None else 0.0
        features.append(has_chip)
        chip_revealed = 1.0 if f.get("chip_revealed", False) else 0.0
        features.append(chip_revealed)
        
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

            # Spielerplättchen (wie viele bereits genutzt: 0/1/2)
            features.append(p.get("tokens_used", 0) / 2.0)

            # Bonusplättchen diese Runde bereits genommen (0/1/2)
            features.append(p.get("chips_taken", 0) / 2.0)

            # Bonus-Chips: welche Farben sind verfügbar (5-dim Count-Vektor)
            chip_color_counts = [0.0] * 5
            for chip in p.get("bonus_chips", []):
                for c_name in chip.get("colors", []):
                    c_id = COLOR_MAP.get(c_name, -1)
                    if 0 <= c_id < 5:
                        chip_color_counts[c_id] += 1.0
            features.extend([c / 4.0 for c in chip_color_counts])  # max 2 chips × 2 farben = 4
            
        # 6. Kuppelzustand (pro Spieler: 9 Slots × 9 Features = 81 Features × 2 = 162)
        COLOR_ID_MAP = {"blau": 1, "gelb": 2, "rot": 3, "schwarz": 4, "türkis": 5}
        TYPE_MAP     = {"NORMAL": 0.0, "WILD": 0.5, "SPECIAL": 1.0}

        for p in [me, enemy]:
            dome = p.get("dome_grid", [])
            for sr in range(3):
                for sc in range(3):
                    row = dome[sr] if sr < len(dome) else []
                    slot = row[sc] if sc < len(row) else None

                    if slot is None:
                        # Slot leer — 17 Nullen
                        features.extend([0.0] * 17)
                    else:
                        features.append(1.0)  # slot existiert
                        for space in slot.get("spaces", [{}, {}, {}, {}]):
                            # is_filled
                            filled = space.get("filled")
                            features.append(1.0 if filled is not None else 0.0)
                            # required_color normalisiert (0=kein, 1-5=farbe)
                            req = space.get("color")
                            features.append(COLOR_ID_MAP.get(req, 0) / 5.0)
                            # space type: NORMAL=0.0, WILD=0.5, SPECIAL=1.0
                            sp_type = space.get("type", "NORMAL")
                            features.append(TYPE_MAP.get(sp_type, 0.0))
                            # locked: nur relevant für SPECIAL (0=offen, 1=gesperrt)
                            locked = space.get("locked", False)
                            features.append(1.0 if locked else 0.0)
            
    # 7. Mondseite kleine Fabriken (pro Fabrik: 3 Positionen × 5 Farben = 15 Features)
    # Position 0 = oben (abholbar), Position 1 = darunter, Position 2 = ganz unten
    for f in data.get("factories", []):
        moon_features = [0.0] * 15
        stacks = f.get("moon", [])
        if stacks:
            stack = stacks[0]  # max 1 Stapel pro kleiner Fabrik
            for pos, stone in enumerate(reversed(stack)):
                if pos >= 3:
                    break
                c_id = COLOR_MAP.get(stone, -1)
                if c_id >= 0:
                    moon_features[pos * 5 + c_id] = 1.0
        features.extend(moon_features)

    # 8. GF Moon-Pool (flach — Farb-Counts, keine Reihenfolge relevant)
    pool = data.get("large_factory", {}).get("moon", [])
    pool_counts = [0] * 5
    for c_str in pool:
        c_id = COLOR_MAP.get(c_str, -1)
        if c_id >= 0:
            pool_counts[c_id] += 1
    features.extend([c / 10.0 for c in pool_counts])

    # 9. Kuppel-Display (max 3 Platten × 4 Spaces × 2 Features = 24)
    # Pro Space: is_filled (1) + required_color normalisiert (1)
    DOME_COLOR_MAP = {"blau": 1, "gelb": 2, "rot": 3, "schwarz": 4, "türkis": 5}
    dome_display = data.get("dome_display", [])
    for slot_idx in range(3):
        if slot_idx < len(dome_display):
            plate = dome_display[slot_idx]
            spaces = plate.get("spaces", []) if plate else []
            for space_idx in range(4):
                if space_idx < len(spaces):
                    space = spaces[space_idx]
                    filled = space.get("filled")
                    features.append(1.0 if filled is not None else 0.0)
                    req = space.get("color")
                    features.append(DOME_COLOR_MAP.get(req, 0) / 5.0)
                else:
                    features.extend([0.0, 0.0])
        else:
            features.extend([0.0] * 8)  # leerer Slot: 4 Spaces × 2 Features

    # 10. Kuppel-Stapel (Anzahl verbleibende Platten)
    features.append(data.get("dome_stack_count", 0) / 20.0)

    return torch.tensor(features, dtype=torch.float32)

def action_to_id(action: dict) -> int:
    t = action.get("type", "")
    if t == "pass":       return 0
    if t == "end_tiling": return 1

    if t == "stone":
        # factory_index: 0-3=kleine Fabriken, 4=GF, 5=Mondaktion
        # color: 0-4, row: -1..6 → 0..7
        c_id  = max(0, COLOR_MAP.get(action.get("color"), 0))
        r_id  = action.get("row", 0) + 1           # -1..6 → 0..7
        f_idx = action.get("factory_index", 0)     # 0-5
        return min(10 + (c_id * 48) + (r_id * 6) + f_idx, 273)
        # max: 10 + (4*48) + (7*6) + 5 = 10 + 192 + 42 + 5 = 249 ✅ < 274

    if t == "tiling":
        pr = action.get("pattern_row", 0)
        sr = action.get("slot_row", 0)
        sc = action.get("slot_col", 0)
        return 274 + (pr * 9) + (sr * 3) + sc      # 274–327

    if t == "dome":
        # display_index: 0-2, slot_row: 0-2, slot_col: 0-2, rotation: 0-3
        d_idx   = action.get("display_index", 0)   # 0-2
        sr      = action.get("slot_row", 0)
        sc      = action.get("slot_col", 0)
        rot_idx = action.get("rotation", 0) // 90
        return 328 + (d_idx * 36) + (sr * 12) + (sc * 4) + rot_idx  # 328–435... clip:
        # max: 328 + 2*36 + 2*12 + 2*4 + 3 = 328 + 72 + 24 + 8 + 3 = 435 → brauchen mehr Raum

    if t == "dome_stack":
        sr      = action.get("slot_row", 0)
        sc      = action.get("slot_col", 0)
        rot_idx = action.get("rotation", 0) // 90
        return 436 + (sr * 12) + (sc * 4) + rot_idx  # 436-471

    if t == "use_chips":
        return 472 + action.get("pattern_row", 0)  # 472-477

    if t == "bonus_chip":
        return 478 + action.get("factory_index", 0)  # 478-481

    return 481  # Fallback

# --- 2. DATENSATZ & NETZWERK ---
class MosaicDataset(Dataset):
    def __init__(self, data_dir="data"):
        from config import INPUT_SIZE
        import hashlib, time

        # Cache-Datei basierend auf Dateiliste + INPUT_SIZE
        files = sorted(glob.glob(os.path.join(data_dir, "*.pkl")))
        cache_key = hashlib.md5(
            (str(files) + str(INPUT_SIZE) + str(NUM_ACTIONS)).encode()
        ).hexdigest()[:12]
        cache_path = os.path.join(data_dir, f".cache_{cache_key}.pt")

        if os.path.exists(cache_path):
            print(f"📦 Lade Cache ({len(files)} Dateien)...")
            t0 = time.time()
            bundle = torch.load(cache_path, weights_only=False)
            self.states   = bundle["states"]
            self.policies = bundle["policies"]
            self.values   = bundle["values"]
            self.masks    = bundle["masks"]
            print(f"Datensatz geladen: {len(self.states)} Züge. "
                  f"(Features pro Zug: {len(self.states[0])}) — {time.time()-t0:.1f}s")
        else:
            print(f"Lade Daten aus {len(files)} Dateien...")
            t0 = time.time()
            states, policies, values, masks = [], [], [], []

            for f in files:
                with open(f, "rb") as file:
                    game_data = pickle.load(file)
                    for step in game_data:
                        states.append(state_to_tensor(step["state"]))
                        values.append(torch.tensor([step["value"]], dtype=torch.float32))

                        t_policy = torch.zeros(NUM_ACTIONS, dtype=torch.float32)
                        for p in step["policy"]:
                            a_id = action_to_id(p["action"])
                            t_policy[a_id] += p["prob"]
                        if t_policy.sum() > 0:
                            t_policy /= t_policy.sum()
                        policies.append(t_policy)

                        mask = torch.zeros(NUM_ACTIONS, dtype=torch.float32)
                        moves = step.get("valid_actions") or step["state"].get("valid_moves", [])
                        for move in moves:
                            mask[action_to_id(move)] = 1.0
                        masks.append(mask)

            self.states   = states
            self.policies = policies
            self.values   = values
            self.masks    = masks

            print(f"Datensatz geladen: {len(self.states)} Züge. "
                  f"(Features pro Zug: {len(self.states[0])}) — {time.time()-t0:.1f}s")
            print(f"💾 Speichere Cache...")
            torch.save({
                "states":   self.states,
                "policies": self.policies,
                "values":   self.values,
                "masks":    self.masks,
            }, cache_path)
            print(f"✅ Cache gespeichert: {cache_path}")

        self.input_size = len(self.states[0]) if self.states else 100

    def __len__(self): return len(self.states)
    def __getitem__(self, idx): return self.states[idx], self.policies[idx], self.values[idx], self.masks[idx]


class MosaicNet(nn.Module):
    def __init__(self, input_size, num_actions=NUM_ACTIONS, hidden_size=HIDDEN_SIZE, value_hidden=128):
        super(MosaicNet, self).__init__()
        self.body = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.BatchNorm1d(hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size),
            nn.BatchNorm1d(hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU()
        )
        self.policy_head = nn.Sequential(
            nn.Linear(hidden_size, num_actions)
        )
        self.value_head = nn.Sequential(
            nn.Linear(hidden_size, value_hidden),
            nn.ReLU(),
            nn.Linear(value_hidden, 1),
            nn.Tanh()
        )
        # Moon-Order Head: 5 Logits (eine pro Farbe)
        # Hoher Wert = Farbe tief im Stapel (defensiv versteckt)
        # Niedriger Wert = Farbe oben (weniger strategisch wichtig)
        # Nur aktiv/trainiert bei Sonnenzügen
        self.moon_order_head = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Linear(32, 5)   # 5 Farben: blau, gelb, rot, schwarz, türkis
        )

    def forward(self, x):
        shared = self.body(x)
        return self.policy_head(shared), self.value_head(shared), self.moon_order_head(shared)