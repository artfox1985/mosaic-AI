import os
import glob
import math
import pickle
import torch
import torch.nn as nn
from torch.utils.data import Dataset
from config import NUM_ACTIONS, HIDDEN_SIZE

COLOR_MAP = {"blau": 0, "gelb": 1, "rot": 2, "schwarz": 3, "türkis": 4, None: -1, "special": 5}
PHASE_MAP = {"drafting": 0, "tiling": 1, "end": 2, "final": 3}

# Platzierte-Farbe-ID je Dome-Feld: 0=leer, 1-5=Farbe, 6=Special.
FILLED_ID_MAP = {None: 0, "blau": 1, "gelb": 2, "rot": 3, "schwarz": 4, "türkis": 5, "special": 6}
# Normalisierung der aktuellen Punkte je der 8 Wertungsplatten (grobe Skalen).
SCORE_NORM = [18.0, 42.0, 20.0, 12.0, 20.0, 22.0, 12.0, 24.0]


def _padn(lst, n):
    """Liste auf genau n Einträge bringen (0-gepolstert) — robust gegen alte Daten."""
    lst = list(lst or [])
    return (lst + [0] * n)[:n]

def state_to_tensor(data):
    """Macht aus deinem Serializer-Dict ein flaches Zahlen-Array für PyTorch."""
    features = []
    
    # 1. Globale Infos
    features.append(data.get("round", 0) / 6.0)
    features.append(PHASE_MAP.get(data.get("phase", "drafting"), 0) / 3.0)
    # Beutel-Restbestand (max. 65 Fliesen zu Spielbeginn) — Signal, wie knapp
    # Farben werden könnten (bislang serialisiert, aber ungenutzt).
    features.append(data.get("bag_count", 0) / 65.0)

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

        # Farben des Bonus-Chips (5-dim Maske) — NUR wenn aufgedeckt (sonst
        # wäre das versteckte Information, die kein Spieler kennt). Zeigt dem
        # Netz, ob der Chip 1- oder 2-farbig (= flexibler einsetzbar) ist.
        chip_colors_mask = [0.0] * 5
        if chip_revealed:
            bc = f.get("bonus_chip") or {}
            for c_name in bc.get("colors", []):
                c_id = COLOR_MAP.get(c_name, -1)
                if 0 <= c_id < 5:
                    chip_colors_mask[c_id] = 1.0
        features.extend(chip_colors_mask)

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

            # Musterreihen
            for row in p.get("pattern_lines", []):
                capacity = row.get("capacity", 1)
                features.append(len(row.get("tiles", [])) / capacity)
                color_id = COLOR_MAP.get(row.get("color"), -1)
                features.extend([1.0 if i == color_id else 0.0 for i in range(5)])
                
            # Straffläche
            features.append(len(p.get("floor", [])) / 4.0)   # MAX_BROKEN=4 (nicht 7)

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
                            # placed-color id: 0=leer, 1-5=Farbe, 6=special
                            # (behält belegt/leer UND die platzierte Farbe)
                            filled = space.get("filled")
                            features.append(FILLED_ID_MAP.get(filled, 0) / 6.0)
                            # required_color normalisiert (0=kein, 1-5=farbe)
                            req = space.get("color")
                            features.append(COLOR_ID_MAP.get(req, 0) / 5.0)
                            # space type: NORMAL=0.0, WILD=0.5, SPECIAL=1.0
                            sp_type = space.get("type", "NORMAL")
                            features.append(TYPE_MAP.get(sp_type, 0.0))
                            # locked: nur relevant für SPECIAL (0=offen, 1=gesperrt)
                            locked = space.get("locked", False)
                            features.append(1.0 if locked else 0.0)

        # 6b. Berechnete Endwertungs-/Geometrie-Features (pro Spieler, 37 je Spieler)
        # Damit das Netz lernt, WIE Endpunkte entstehen (Quelle: Rust
        # scoring::player_scoring_features). Endkriterien sind harte geometrische
        # Prädikate, die ein flaches MLP aus der Roh-Kodierung kaum lernt.
        for p in [me, enemy]:
            pts = _padn(p.get("scoring_tile_points"), 8)
            for i in range(8):
                features.append(pts[i] / SCORE_NORM[i])
            geo = p.get("score_geo", {})
            features.extend(v / 6.0 for v in _padn(geo.get("row_fill"), 6))
            features.extend(v / 6.0 for v in _padn(geo.get("col_fill"), 6))
            features.extend(v / 6.0 for v in _padn(geo.get("diag_fill"), 2))
            features.extend(v / 5.0 for v in _padn(geo.get("row_colors"), 6))
            features.append(geo.get("border_fill", 0) / 20.0)
            features.extend(v / 4.0 for v in _padn(geo.get("corner_fill"), 4))
            features.append(geo.get("wild_filled", 0) / 8.0)
            features.append(geo.get("wild_total", 0) / 8.0)
            features.append(geo.get("special_empty", 0) / 8.0)
            features.append(geo.get("special_total", 0) / 8.0)

        # 6c. Linien-Geometrie (offensives Linien-Bauen, 23 je Spieler).
        # Punkte = zusammenhängende orthogonale Läufe → diese Struktur explizit
        # machen, damit das flache MLP Linien-Strategie repräsentieren kann
        # (Quelle: Rust scoring::player_line_features).
        for p in [me, enemy]:
            lg = p.get("line_geo", {})
            features.extend(v / 6.0 for v in _padn(lg.get("h_hist"), 5))   # Läufe len 2-6
            features.extend(v / 6.0 for v in _padn(lg.get("v_hist"), 5))
            features.append(lg.get("cluster_sq", 0) / 150.0)               # Σ länge²
            features.extend(v / 12.0 for v in _padn(lg.get("row_potential"), 6))
            features.extend(v / 12.0 for v in _padn(lg.get("col_potential"), 6))

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

# Value-Target = das TATSÄCHLICHE ENDERGEBNIS der ganzen Partie (inkl.
# Wertungsplatten), als Ziel für JEDEN Schritt der Partie — klassisches
# AlphaZero-Prinzip (delayed reward): der Zielwert für einen Runde-1-Zustand
# ist derselbe wie für den letzten Zug, nämlich wie das Spiel am Ende wirklich
# ausging.
#
# Bewusst NICHT die pro-Runde projizierte Größe (own.score + estimated_score)
# als dichtes Zwischensignal — das wurde probiert und verworfen: die
# Heuristik maximiert bereits gierig die Rundenpunkte, hat aber keine
# Weitsicht (kein strategischer Board-Aufbau, keine Wertungsplatten). Ein
# Rundenprojektions-Ziel hätte dem Netz denselben gierigen Rundenoptimum-Bias
# beigebracht — Runde 1/2 bewusst suboptimal spielen, um in Runde 3/4 durch
# strategischen Aufbau viel mehr zu holen, wäre dann NICHT belohnt worden
# (der Zielwert für Runde-1-Zustände hätte Runde 3/4 gar nicht gesehen).
# Das reine Partie-Endergebnis als Ziel lernt automatisch, dass ein
# scheinbar suboptimaler früher Zustand gut ist, WENN er zuverlässig zu einem
# starken Endergebnis führt.
#
# own_total = step["scores"][eigener Spieler]  (bereits inkl. Wertungsplatten,
#             von apply_end_scoring() in Rust eingerechnet)
# opp_total = step["scores"][Gegner]
# value = tanh((own_total − VALUE_OPP_WEIGHT · opp_total) / VALUE_SCALE)
#
# Gewichtung < 1 auf die gegnerische Seite statt reiner Differenz: ein 10:5
# und ein 65:60 (beide Marge 5) wären bei reiner Differenz identisch bewertet,
# obwohl 65:60 absolut deutlich mehr erreichte Punkte sind (own-0.5·opp:
# 10-2.5=7.5 vs. 65-30=35 — klar unterschieden).
# Kompromiss: das macht das Target nicht mehr exakt antisymmetrisch
# (value(p0) != -value(p1)), was der Zero-Sum-Annahme der Suche (net_mcts.rs:
# 1 Netzquery aus Sicht des Ziehenden, Gegner = 1-win) nur noch näherungsweise
# entspricht — akzeptiert, weil das eigentliche Ziel (hohe absolute Punktzahl,
# nicht nur "irgendwie gewinnen") das explizit verlangt.
# VALUE_SCALE-Kalibrierung: NICHT aus aktuellen Spieldaten abgeleitet (Heuristik
# und Netz spielen beide noch schwach — jede aus dieser Verteilung abgeleitete
# Skala würde nur die aktuelle Schwäche festschreiben, nicht das echte
# Punktepotenzial des Spiels). Stattdessen an einem groben menschlichen
# Referenzwert kalibriert: ab ~100 Punkten gilt ein Ergebnis als sehr gut.
# own_total = own − 0.5·opp; bei own≈100 gegen einen soliden Gegner (opp≈40)
# ergibt das own_total≈80. VALUE_SCALE=50 legt den tanh-Arg bei diesem
# "sehr gut"-Referenzpunkt auf ~1.6 (tanh(1.6)≈0.92) — informativ, aber noch
# nicht voll gesättigt, sodass auch darüber hinaus noch Differenzierung
# möglich bleibt. Deutlich gröber als eine "saubere" Herleitung, aber
# begründeter als eine an aktueller Schwäche kalibrierte Zahl.
# VALUE_SCHEMA_VERSION erzwingt einen Cache-Rebuild bei Änderungen an dieser Formel.
VALUE_SCHEMA_VERSION = 8
VALUE_OPP_WEIGHT = 0.5
VALUE_SCALE = 50.0


class MosaicDataset(Dataset):
    def __init__(self, data_dir="data"):
        from config import INPUT_SIZE
        import hashlib, time
        import h5py
        import numpy as np

        # Cache-Datei basierend auf Dateiliste + INPUT_SIZE
        files = sorted(glob.glob(os.path.join(data_dir, "*.pkl")))
        cache_key = hashlib.md5(
            (str(files) + str(INPUT_SIZE) + str(NUM_ACTIONS) + str(VALUE_SCHEMA_VERSION)).encode()
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
                if 'policy_weights' in hf:
                    self.policy_weights = torch.from_numpy(hf['policy_weights'][:])
                else:  # alter Cache ohne Gewicht → alle 1.0
                    self.policy_weights = torch.ones(len(self.states), dtype=torch.float32)
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
            self.policy_weights = torch.ones(len(self.states), dtype=torch.float32)  # Legacy → 1.0
            # Als HDF5 speichern
            with h5py.File(cache_path_h5, 'w') as hf:
                hf.create_dataset('states',             data=self.states.numpy(),             compression='lzf')
                hf.create_dataset('policies',           data=self.policies.numpy(),           compression='lzf')
                hf.create_dataset('values',             data=self.values.numpy(),             compression='lzf')
                hf.create_dataset('masks',              data=self.masks.numpy(),              compression='lzf')
                hf.create_dataset('moon_order_targets', data=self.moon_order_targets.numpy(), compression='lzf')
                hf.create_dataset('policy_weights',     data=self.policy_weights.numpy(),     compression='lzf')
            os.remove(cache_path_pt)
            print(f"Datensatz geladen + migriert: {len(self.states)} Züge. "
                  f"(Features pro Zug: {self.states.shape[1]}) — {time.time()-t0:.1f}s")

        else:
            print(f"Lade Daten aus {len(files)} Dateien...")
            t0 = time.time()
            _CIDX = {'blau':0,'gelb':1,'rot':2,'schwarz':3,'türkis':4}
            states_l, policies_l, values_l, masks_l, moon_l = [], [], [], [], []
            polw_l = []  # Policy-Loss-Gewicht je Sample (1=Drafting, 0=Tiling/Start)

            for f in files:
                with open(f, "rb") as file:
                    game_data = pickle.load(file)
                    for step in game_data:
                        states_l.append(state_to_tensor(step["state"]).numpy())
                        if "scores" in step and "winner" in step:
                            # Partie-Endergebnis als Ziel für JEDEN Schritt (siehe
                            # VALUE_SCHEMA_VERSION oben) — bereits inkl. Wertungsplatten.
                            p = step["player"]
                            own_total = float(step["scores"][p])
                            opp_total = float(step["scores"][1 - p])
                            val = math.tanh((own_total - VALUE_OPP_WEIGHT * opp_total) / VALUE_SCALE)
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
                        # Selbstkonsistenz: die tatsächlich gespielten Policy-Aktionen
                        # sind per Definition legal — immer in die Maske aufnehmen.
                        # Verhindert Policy-Leaks (Target-Masse auf maskierter Aktion →
                        # explodierender Policy-Loss), falls valid_actions unvollständig ist.
                        for p in step["policy"]:
                            mask[action_to_id(p["action"])] = 1.0
                        masks_l.append(mask)

                        moon_target = np.full(5, -1.0, dtype=np.float32)
                        moon_order = step.get("moon_order_target", None)
                        if moon_order:
                            for rank, color_name in enumerate(moon_order):
                                c_idx = _CIDX.get(color_name, -1)
                                if c_idx >= 0:
                                    moon_target[c_idx] = float(rank)
                        moon_l.append(moon_target)

                        # Policy-Loss nur für ECHTE Drafting-Schritte: Tiling/Start-
                        # Steps sind one-hot Solver-/Heuristik-Züge, die das Netz nie
                        # vorhersagen muss (Tiling macht der DFS-Solver). Sie fluten
                        # sonst den Policy-Head mit Tiling-Aktionen → das Netz legt
                        # auch in der Drafting-Phase Masse auf (illegale) Tiling-IDs
                        # und die Drafting-Priors verkommen zu Rauschen.
                        phase = step["state"].get("phase")
                        is_start = any(pe["action"].get("is_start") for pe in step["policy"])
                        pol_w = 1.0 if (phase == "drafting" and not is_start) else 0.0
                        polw_l.append(np.float32(pol_w))

            states_np   = np.array(states_l,   dtype=np.float32)
            policies_np = np.array(policies_l, dtype=np.float32)
            values_np   = np.array(values_l,   dtype=np.float32)
            masks_np    = np.array(masks_l,    dtype=np.float32)
            moon_np     = np.array(moon_l,     dtype=np.float32)
            polw_np     = np.array(polw_l,     dtype=np.float32)
            # Die Python-Listen aus lauter einzelnen kleinen Arrays (ein Objekt pro
            # Zug, viel Overhead ggü. den kompakten *_np-Arrays) werden ab hier nicht
            # mehr gebraucht — explizit freigeben, statt sie bis Funktionsende (inkl.
            # dem folgenden HDF5-Schreiben) im Speicher mitzuschleppen. Bei größeren
            # Fenstern (mehrere hunderttausend Züge) sonst ein echtes Speicher-Nadelöhr.
            del states_l, policies_l, values_l, masks_l, moon_l, polw_l

            print(f"Datensatz geladen: {len(states_np)} Züge. "
                  f"(Features pro Zug: {states_np.shape[1]}) — {time.time()-t0:.1f}s")
            print(f"💾 Speichere HDF5-Cache...")
            with h5py.File(cache_path_h5, 'w') as hf:
                hf.create_dataset('states',             data=states_np,   compression='lzf')
                hf.create_dataset('policies',           data=policies_np, compression='lzf')
                hf.create_dataset('values',             data=values_np,   compression='lzf')
                hf.create_dataset('masks',              data=masks_np,    compression='lzf')
                hf.create_dataset('moon_order_targets', data=moon_np,     compression='lzf')
                hf.create_dataset('policy_weights',     data=polw_np,     compression='lzf')
            print(f"✅ Cache gespeichert: {cache_path_h5}")

            self.states             = torch.from_numpy(states_np)
            self.policies           = torch.from_numpy(policies_np)
            self.values             = torch.from_numpy(values_np)
            self.masks              = torch.from_numpy(masks_np)
            self.moon_order_targets = torch.from_numpy(moon_np)
            self.policy_weights     = torch.from_numpy(polw_np)

        self.input_size = self.states.shape[1] if len(self.states) > 0 else 100

    def __len__(self): return len(self.states)
    def __getitem__(self, idx):
        return (self.states[idx], self.policies[idx], self.values[idx], self.masks[idx],
                self.moon_order_targets[idx], self.policy_weights[idx])


class MosaicNet(nn.Module):
    def __init__(self, input_size, num_actions=NUM_ACTIONS, hidden_size=HIDDEN_SIZE, value_hidden=128,
                 policy_hidden=256):
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
        # Eigene Zwischenschicht für den Policy-Head (vorher: 1 nackter Linear-
        # Layer direkt auf den geteilten Trunk — im Gegensatz zu Value-/Moon-
        # Order-Head, die beide schon eine ReLU-Zwischenschicht hatten. Bei v5
        # blieb der Policy-Loss bei 33% des Max-Werts stehen, während der
        # Value-Loss exzellent konvergierte (siehe evaluations/v5_eval.md) —
        # die Kapazitätsanalyse zeigte einen gesunden, nicht gesättigten Trunk
        # (Dead-Ratio 4%, Eff.Rank ~41%), also lag die Asymmetrie näher am Head
        # selbst als am Trunk. Ab v7 relevant (v6 lief bereits mit dem alten,
        # einlagigen Head).
        # policy_hidden=0 rekonstruiert bewusst die ALTE, einlagige Architektur
        # (kein Linear→ReLU→Linear, sondern nackter Linear-Layer) — nötig, damit
        # export_onnx.py ältere Checkpoints (v1-v6) exakt mit ihren echten
        # trainierten Gewichten neu exportieren kann, statt den neuen Head mit
        # Zufallsgewichten aufzufüllen (das würde den Policy-Head stillschweigend
        # kaputt machen, siehe Vorfall bei v6).
        if policy_hidden and policy_hidden > 0:
            self.policy_head = nn.Sequential(
                nn.Linear(hidden_size, policy_hidden),
                nn.ReLU(),
                nn.Linear(policy_hidden, num_actions)
            )
        else:
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