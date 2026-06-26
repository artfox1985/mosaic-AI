import os
import glob
import pickle
import torch
import torch.nn as nn
from torch.utils.data import Dataset
from config import NUM_ACTIONS, HIDDEN_SIZE, MARGIN_CAP, MAX_WINNER_SCORE

COLOR_MAP = {"blau": 0, "gelb": 1, "rot": 2, "schwarz": 3, "türkis": 4, None: -1, "special": 5}
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

            # Chip-Abschließbarkeit pro Musterreihe (Reihen 2-6 = Indizes 1-5).
            # Reihe 1 (Index 0) ausgenommen: sie hat nur 1 Feld, Chip-Mehrfeld-
            # Logik irrelevant. Ein Flag je Reihe, ob sie sich per Bonuschips
            # abschließen lässt (2 gleiche ODER 3 beliebige je fehlendem Feld;
            # deckt auch Mehrfeld-Füllung ab). Quelle: chippable_tiling_rows,
            # bereits in der Engine via can_complete_row_with_chips berechnet.
            pi_real = curr_pi if p is me else enemy_pi
            chippable_rows = {
                entry.get("ri")
                for entry in data.get("chippable_tiling_rows", [])
                if entry.get("pi") == pi_real
            }
            for ri in range(1, 6):   # Reihen-Index 1..5 (Reihe 2..6)
                features.append(1.0 if ri in chippable_rows else 0.0)
            
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

# 0:0-Strafe: geflutete Strafleisten sind ein vermiedenswertes Ergebnis. BEIDE
# Spieler erhalten dieses negative Target (symmetrisch, nicht gespiegelt), damit
# das Netz lernt, 0:0 aktiv zu vermeiden statt sich über den Startspieler-Marker
# in einen "sicheren" Hafen zu mauern.
#   v1f: -0.15 (mild) → senkte Self-Play-0:0 von 58.7% auf ~47%.
#   v1g: -0.30 (stärker) → Test, ob der stärkere Anreiz die Rate weiter drückt,
#        bevor der teurere Auxiliary-Floor-Head nötig wird.
ZEROZERO_PENALTY = -0.15


def is_zerozero(scores, winner) -> bool:
    """True, wenn der Ausgang ein 0:0-Tiebreak-Spiel ist (kein echtes Punkten)."""
    return abs(scores[0] - scores[1]) == 0 and scores[winner] < 5

def compute_win_val(scores, winner, margin_cap=MARGIN_CAP, max_winner_score=MAX_WINNER_SCORE):
    """Berechnet den abgestuften Value-Target aus rohen Scores.
    Entkoppelt — kann beim Training mit anderen Parametern neu berechnet werden.

    Rückgabe ist der Wert AUS SIEGER-SICHT (für echte Siege). Die Trainings-
    Aufrufstelle spiegelt: +wv für den Sieger, -wv für den Verlierer.

    Sonderfall 0:0 (margin==0, winner_score<5): kein echter Sieg, sondern ein
    vermiedenswertes Ergebnis (geflutete Strafleisten — kein Mensch spielt so).
    Gibt direkt ZEROZERO_PENALTY (negativ) zurück — konsistent mit dem
    Trainings-Target. Die Trainings-Aufrufstelle erkennt den Fall zusätzlich über
    is_zerozero() und setzt den Wert für BEIDE Spieler symmetrisch (ohne
    Spiegelung), sodass nicht ein Spieler durch die Spiegelung +0.3 bekäme.
    """
    margin       = abs(scores[0] - scores[1])
    winner_score = scores[winner]
    if margin == 0 and winner_score < 5:
        return ZEROZERO_PENALTY
    margin_part = min(0.45, (margin / margin_cap) * 0.45)
    score_part  = min(0.45, (winner_score / max_winner_score) * 0.45)
    return min(1.0, 0.1 + margin_part + score_part)


class MosaicDataset(Dataset):
    def __init__(self, data_dir="data", margin_cap=MARGIN_CAP, max_winner_score=MAX_WINNER_SCORE, target_zerozero_ratio=None):
        from config import INPUT_SIZE
        import hashlib, time
        import h5py
        import numpy as np

        # Cache-Datei basierend auf Dateiliste + INPUT_SIZE
        files = sorted(glob.glob(os.path.join(data_dir, "*.pkl")))
        self.margin_cap       = margin_cap
        self.max_winner_score = max_winner_score
        cache_key = hashlib.md5(
            (str(files) + str(INPUT_SIZE) + str(NUM_ACTIONS)
             + str(margin_cap) + str(max_winner_score)
             + str(target_zerozero_ratio)).encode()
        ).hexdigest()[:12]
        cache_path_h5 = os.path.join(data_dir, f".cache_{cache_key}.h5")
        cache_path_pt = os.path.join(data_dir, f".cache_{cache_key}.pt")

        if os.path.exists(cache_path_h5):
            # HDF5 Cache laden — deutlich schneller als .pt
            print(f"📦 Lade HDF5-Cache ({len(files)} Dateien)...")
            t0 = time.time()
            with h5py.File(cache_path_h5, 'r') as hf:
                self.states             = torch.from_numpy(hf['states'][:])
                self.policies           = torch.from_numpy(hf['policies'][:])
                self.values             = torch.from_numpy(hf['values'][:])
                self.masks              = torch.from_numpy(hf['masks'][:])
                self.moon_order_targets = torch.from_numpy(hf['moon_order_targets'][:])
            print(f"Datensatz geladen: {len(self.states)} Züge. "
                  f"(Features pro Zug: {self.states.shape[1]}) — {time.time()-t0:.1f}s")

        elif os.path.exists(cache_path_pt):
            # Alten .pt Cache laden und nach HDF5 migrieren
            print(f"📦 Migriere .pt → HDF5 Cache...")
            t0 = time.time()
            bundle = torch.load(cache_path_pt, weights_only=False)
            self.states             = bundle["states"] if isinstance(bundle["states"], torch.Tensor) else torch.stack(bundle["states"])
            self.policies           = bundle["policies"] if isinstance(bundle["policies"], torch.Tensor) else torch.stack(bundle["policies"])
            self.values             = bundle["values"] if isinstance(bundle["values"], torch.Tensor) else torch.stack(bundle["values"])
            self.masks              = bundle["masks"] if isinstance(bundle["masks"], torch.Tensor) else torch.stack(bundle["masks"])
            mot = bundle.get("moon_order_targets")
            if mot is None:
                mot = [torch.full((5,), -1.0) for _ in self.states]
            self.moon_order_targets = mot if isinstance(mot, torch.Tensor) else torch.stack(mot)
            # Als HDF5 speichern
            with h5py.File(cache_path_h5, 'w') as hf:
                hf.create_dataset('states',             data=self.states.numpy(),             compression='lzf')
                hf.create_dataset('policies',           data=self.policies.numpy(),           compression='lzf')
                hf.create_dataset('values',             data=self.values.numpy(),             compression='lzf')
                hf.create_dataset('masks',              data=self.masks.numpy(),              compression='lzf')
                hf.create_dataset('moon_order_targets', data=self.moon_order_targets.numpy(), compression='lzf')
            os.remove(cache_path_pt)
            print(f"Datensatz geladen + migriert: {len(self.states)} Züge. "
                  f"(Features pro Zug: {self.states.shape[1]}) — {time.time()-t0:.1f}s")

        else:
            print(f"Lade Daten aus {len(files)} Dateien...")
            t0 = time.time()
            _CIDX = {'blau':0,'gelb':1,'rot':2,'schwarz':3,'türkis':4}
            states_l, policies_l, values_l, masks_l, moon_l = [], [], [], [], []

            import random as _rnd
            keep_prob = 1.0
            if target_zerozero_ratio is not None and target_zerozero_ratio < 1.0:
                # Erst-Scan: 0:0 vs non-0:0 Spiele zählen (Trennung über game_id)
                n_zz = n_nonzz = 0
                prev_g = None
                for f in files:
                    with open(f, "rb") as file:
                        gd = pickle.load(file)
                    for step in gd:
                        gid = step.get("game_id")
                        if gid is None:
                            gid = (tuple(step["scores"]), step["winner"]) if "scores" in step else id(step)
                        if gid != prev_g:
                            prev_g = gid
                            if "scores" in step and "winner" in step:
                                is_zz = (step["scores"][0] == step["scores"][1] == 0)
                            elif "value" in step:
                                is_zz = abs(step["value"]) <= 0.1
                            else:
                                is_zz = False
                            if is_zz: n_zz += 1
                            else:     n_nonzz += 1
                if n_nonzz > 0 and n_zz > 0:
                    target_zz = int((target_zerozero_ratio / (1 - target_zerozero_ratio)) * n_nonzz)
                    target_zz = min(target_zz, n_zz)
                    keep_prob = target_zz / n_zz
                    print(f"  🎯 0:0-Reduktion: {n_zz} 0:0-Spiele (von {n_zz+n_nonzz} total) "
                          f"→ behalte ~{target_zz} (Ziel {target_zerozero_ratio*100:.0f}%, keep_prob {keep_prob:.2f})")

            prev_g_load = None
            keep_current = True

            for f in files:
                with open(f, "rb") as file:
                    game_data = pickle.load(file)
                    for step in game_data:
                        # Spielgrenze über game_id
                        gid = step.get("game_id")
                        if gid is None:
                            gid = (tuple(step["scores"]), step["winner"]) if "scores" in step else id(step)
                        if gid != prev_g_load:
                            prev_g_load = gid
                            if keep_prob < 1.0:
                                if "scores" in step and "winner" in step:
                                    is_zz = (step["scores"][0] == step["scores"][1] == 0)
                                elif "value" in step:
                                    is_zz = abs(step["value"]) <= 0.1
                                else:
                                    is_zz = False
                                keep_current = (not is_zz) or (_rnd.random() < keep_prob)
                            else:
                                keep_current = True

                        if not keep_current:
                            continue

                        states_l.append(state_to_tensor(step["state"]).numpy())
                        if "scores" in step and "winner" in step:
                            if is_zerozero(step["scores"], step["winner"]):
                                # 0:0 → beide Spieler bestraft (symmetrisch, KEINE
                                # Spiegelung). Nimmt dem Marker-Halter den sicheren
                                # +0.1-Hafen und gibt einen Gradienten gegen 0:0.
                                val = ZEROZERO_PENALTY
                            else:
                                wv  = compute_win_val(step["scores"], step["winner"],
                                                      margin_cap, max_winner_score)
                                val = wv if step["player"] == step["winner"] else -wv
                        else:
                            val = float(step["value"])
                        values_l.append([val])

                        t_policy = np.zeros(NUM_ACTIONS, dtype=np.float32)
                        for p in step["policy"]:
                            t_policy[action_to_id(p["action"])] += p["prob"]
                        s = t_policy.sum()
                        if s > 0: t_policy /= s
                        policies_l.append(t_policy)

                        mask = np.zeros(NUM_ACTIONS, dtype=np.float32)
                        moves = step.get("valid_actions") or step["state"].get("valid_moves", [])
                        for move in moves:
                            mask[action_to_id(move)] = 1.0
                        masks_l.append(mask)

                        moon_target = np.full(5, -1.0, dtype=np.float32)
                        moon_order = step.get("moon_order_target", None)
                        if moon_order:
                            for rank, color_name in enumerate(moon_order):
                                c_idx = _CIDX.get(color_name, -1)
                                if c_idx >= 0:
                                    moon_target[c_idx] = float(rank)
                        moon_l.append(moon_target)

            states_np   = np.array(states_l,   dtype=np.float32)
            policies_np = np.array(policies_l, dtype=np.float32)
            values_np   = np.array(values_l,   dtype=np.float32)
            masks_np    = np.array(masks_l,    dtype=np.float32)
            moon_np     = np.array(moon_l,     dtype=np.float32)

            print(f"Datensatz geladen: {len(states_np)} Züge. "
                  f"(Features pro Zug: {states_np.shape[1]}) — {time.time()-t0:.1f}s")
            print(f"💾 Speichere HDF5-Cache...")
            with h5py.File(cache_path_h5, 'w') as hf:
                hf.create_dataset('states',             data=states_np,   compression='lzf')
                hf.create_dataset('policies',           data=policies_np, compression='lzf')
                hf.create_dataset('values',             data=values_np,   compression='lzf')
                hf.create_dataset('masks',              data=masks_np,    compression='lzf')
                hf.create_dataset('moon_order_targets', data=moon_np,     compression='lzf')
            print(f"✅ Cache gespeichert: {cache_path_h5}")

            self.states             = torch.from_numpy(states_np)
            self.policies           = torch.from_numpy(policies_np)
            self.values             = torch.from_numpy(values_np)
            self.masks              = torch.from_numpy(masks_np)
            self.moon_order_targets = torch.from_numpy(moon_np)

        self.input_size = self.states.shape[1] if len(self.states) > 0 else 100

    def __len__(self): return len(self.states)
    def __getitem__(self, idx): return self.states[idx], self.policies[idx], self.values[idx], self.masks[idx], self.moon_order_targets[idx]


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
        return (self.policy_head(shared), self.value_head(shared),
                self.moon_order_head(shared))

    @torch.no_grad()
    def analyze_capacity(self, x):
        """
        Misst Netzauslastung über einen Batch:
        - Dead-Neuron-Ratio pro ReLU-Schicht (Neuronen die für ALLE Samples 0 sind)
        - Effective Rank der Aktivierungen (wie viele Dimensionen real genutzt werden)
        """
        self.eval()
        layer_out = []
        h = x
        for layer in self.body:
            h = layer(h)
            if isinstance(layer, nn.ReLU):
                layer_out.append(h.clone())

        results = {}
        for idx, a in enumerate(layer_out):
            n_neurons = a.shape[1]
            active_per_neuron = (a > 1e-6).any(dim=0)
            dead = (~active_per_neuron).sum().item()
            dead_ratio = dead / n_neurons
            active_rate = (a > 1e-6).float().mean().item()
            a_centered = a - a.mean(dim=0, keepdim=True)
            try:
                sv = torch.linalg.svdvals(a_centered)
                sv = sv[sv > 1e-10]
                if len(sv) > 0:
                    p = sv / sv.sum()
                    entropy = -(p * torch.log(p)).sum()
                    eff_rank = torch.exp(entropy).item()
                else:
                    eff_rank = 0.0
            except Exception:
                eff_rank = float('nan')
            results[f"layer{idx+1}"] = {
                "n_neurons":   n_neurons,
                "dead":        dead,
                "dead_ratio":  dead_ratio,
                "active_rate": active_rate,
                "eff_rank":    eff_rank,
                "rank_pct":    eff_rank / n_neurons if n_neurons else 0,
            }
        return results