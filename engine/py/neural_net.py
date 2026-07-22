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
    # Farben werden könnten.
    features.append(data.get("bag_count", 0) / 65.0)
    # Beutel+Turm je Farbe (was insgesamt noch "im Umlauf" ist) -- ergänzt das
    # bisher ungenutzte Gesamt-bag_count um eine Farbaufschlüsselung. Der
    # Beutel ist für die KI nicht direkt sichtbar, seine Zusammensetzung ist
    # aber deterministisch aus dem Rest rückrechenbar (feste Gesamtzahl je
    # Farbe minus alles sichtbar Platzierte) -- direktes Auslesen liefert
    # dieselbe Zahl, nur günstiger. /13 = TILES_PER_COLOR.
    bag_colors = data.get("bag_colors", [0] * 5)
    tower_colors = data.get("tower_colors", [0] * 5)
    for i in range(5):
        bc = bag_colors[i] if i < len(bag_colors) else 0
        tc = tower_colors[i] if i < len(tower_colors) else 0
        features.append((bc + tc) / 13.0)
    # Kuppelstapel-Maske (18, tile_id-Reihenfolge): 1, falls das Design noch
    # verdeckt im Stapel liegt -- welche Designs schon verbraucht/ausgelegt
    # sind, verrät dem Netz, was noch "lauert".
    dome_mask = data.get("dome_pool_mask", [0] * 18)
    for i in range(18):
        features.append(float(dome_mask[i]) if i < len(dome_mask) else 0.0)
    # Wild-Anteil der noch verdeckten Stapelplatten -- explizites Aggregat
    # ergänzend zur rohen Maske oben (siehe Rust serialize.rs
    # `dome_wild_remaining_frac` für die Begründung). 0.5 = neutral, falls
    # das Feld fehlt (alte JSON-Snapshots ohne dieses Feld).
    features.append(float(data.get("dome_wild_remaining_frac", 0.5)))

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

MAX_PENDING_STACK_TILES = 4  # muss zu features.rs::MAX_PENDING_STACK_TILES passen

def action_to_id(action: dict) -> int:
    """Python-Mirror von `features.rs::action_to_id` -- MUSS bei jeder Änderung
    dort synchron gehalten werden (kein automatischer Abgleich, siehe Vorfall
    2026-07-19: `dome`/`dome_stack` kollabierten Slot+Rotation NICHT mehr in
    die ID, der Python-Mirror war noch auf dem alten 108/36-ID-Schema)."""
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

    if t == "choose_dome_slot":
        # Baustein B: Kachel (Auslage-Index 0-2) + Slot ZUSAMMEN, Rotation ist
        # eine separate Stufe-2-Aktion (choose_dome_rotation) -- ersetzt das
        # frühere kollabierte "dome"-Schema (dome_slot_head/dome_rotation_head).
        d_idx = action.get("display_index", 0)
        sr = action.get("slot_row", 0)
        sc = action.get("slot_col", 0)
        return 328 + (d_idx * 9) + (sr * 3) + sc  # 328-354

    if t == "choose_draw_stack_slot":
        # `pending_index`: Position der gewaehlten Platte in der deduplizierten
        # Pending-Liste (self_play.rs::action_to_env_dict), gedeckelt statt
        # Kachel-kodiert. + Slot zusammen, Rotation separat (siehe oben).
        p_idx = min(action.get("pending_index", 0), MAX_PENDING_STACK_TILES - 1)
        sr = action.get("slot_row", 0)
        sc = action.get("slot_col", 0)
        return 355 + (p_idx * 9) + (sr * 3) + sc  # 355-390

    if t == "choose_dome_rotation":
        # EINE gemeinsame ID-Familie fuer beide Pfade (Display/Stapel).
        rot_idx = max(0, min(3, action.get("rotation", 0) // 90))
        return 391 + rot_idx  # 391-394

    if t == "use_chips":
        return 395 + action.get("pattern_row", 0)  # 395-400

    if t == "bonus_chip":
        return 401 + action.get("factory_index", 0)  # 401-404

    if t == "dome_stack_peek":
        return 405

    return 405  # Fallback

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
# value = tanh(own_total/VALUE_SCALE) − VALUE_OPP_EPSILON · tanh(opp_total/VALUE_SCALE)
#
# Getrennt gesättigt statt Differenzbildung VOR dem tanh (wie zuvor
# `own − 0.5·opp`, dann erst tanh): eine Differenz sättigt bei großem Abstand
# für BEIDE Terme gemeinsam — das Netz verliert dann jede Fähigkeit, zwischen
# "gut" und "noch besser" bzw. "schlecht" und "noch schlechter" zu
# unterscheiden, obwohl Priorität 1 (maximale eigene Punktzahl) in jeder
# Stellung weiterhin gilt. Genau das Problem, das `mcts.rs::evaluate()` schon
# durch rein absolute Pro-Spieler-Bewertung behoben hat — konsistent dazu
# bekommt jetzt auch das Value-Head-Ziel einen eigenen, unabhängig sättigenden
# own-Term (volle Differenzierung über den ganzen Bereich).
# Der Gegner-Term bildet Priorität 2 ("wenn möglich dem Gegner schaden") ab,
# aber additiv NACH der Sättigung statt als Abzug davor: er kann den
# Gesamtwert nur um max. ±VALUE_OPP_EPSILON verschieben, niemals das
# Eigenpunkte-Signal überstimmen — ein Zug, der dem Gegner schadet OHNE die
# eigene Punktzahl zu beeinflussen, bekommt einen kleinen Bonus, kann aber nie
# eine eigene Einbuße aufwiegen.
# VALUE_SCALE-Kalibrierung: NICHT aus aktuellen Spieldaten abgeleitet (Heuristik
# und Netz spielen beide noch schwach — jede aus dieser Verteilung abgeleitete
# Skala würde nur die aktuelle Schwäche festschreiben, nicht das echte
# Punktepotenzial des Spiels). Stattdessen an einem groben menschlichen
# Referenzwert kalibriert: ab ~100 Punkten gilt ein Ergebnis als sehr gut.
# VALUE_SCALE=50 legt den tanh-Arg bei own_total=100 auf 2.0 (tanh(2.0)≈0.96)
# — informativ, aber noch nicht voll gesättigt, sodass auch darüber hinaus
# noch Differenzierung möglich bleibt. Deutlich gröber als eine "saubere"
# Herleitung, aber begründeter als eine an aktueller Schwäche kalibrierte Zahl.
# VALUE_SCHEMA_VERSION erzwingt einen Cache-Rebuild bei Änderungen an dieser Formel.
#
# Zwei getrennte Ziele, zwei Köpfe (Value-Head zurückgeholt, siehe
# evaluations/stage2_investigation.md fuer die Historie). KORREKTUR ggue.
# frueheren Kommentarstand hier: `values` ist NICHT tot in der Suche --
# net_mcts.rs::make_node liest bei ACTIVE_LEAF=Net (aktueller Standard)
# ausschliesslich `value_to_win_prob(value)` fuer den PUCT-Blattwert, `points`
# wird dort explizit verworfen (Kommentar "reines Trainings-Zusatzsignal, hier
# nie gebraucht"). D.h. `values` treibt die Suche, `points_forecast` ist reines
# Trunk-Zusatzsignal ohne Sucheinfluss -- umgekehrt zu dem, was man aus dem
# Namen "Aux-Head" vermuten wuerde.
#   - `values`     : reines Sieg/Niederlage-Ziel (+1/-1, wer hat GEWONNEN),
#                    der klassische AlphaZero-Value-Head. Einfacher/robuster
#                    als ein Punktestand-Regressionsziel (siehe
#                    feedback_value_head_capacity.md: die alte reine
#                    Punktestand-Variante blieb bei Val-R² 0.27-0.34 haengen,
#                    vermutlich irreduzibles Ziel-Rauschen).
#   - `points_forecast`: die alte Punktestand-Formel als separater Aux-Head
#                    (tanh(eigen/SCALE) - EPSILON*tanh(gegner/SCALE)) -- liefert
#                    dem Trunk ein feineres, kontinuierliches Zusatzsignal
#                    ohne dass die SUCHE je darauf zugreift.
#                    Ab Version 11: wo vorhanden, nutzt `points_forecast`
#                    das gemittelte Rundenübergangs-Sampling
#                    (`round_transition_value`) statt der einzelnen,
#                    verrauschten Partie-Endpunktzahl (siehe
#                    round_transition.rs -- Versuch, das dokumentierte
#                    Val-R²-Plateau ueber ein rauschaermeres Ziel
#                    anzugehen). Half beim points_forecast-Head (Val-R²
#                    0.27->0.34, v8->v8b).
#                    Ab Version 12: `round_transition_value` (wo vorhanden)
#                    ersetzt jetzt AUCH `values` selbst, nicht nur
#                    `points_forecast` -- v8/v8b zeigten trotz gesenktem
#                    VALUE_WEIGHT weiterhin Val-R²<0 fuer `values` (den Head,
#                    der tatsaechlich die Suche treibt), waehrend
#                    `points_forecast` mit derselben Rauschreduktion bereits
#                    auf Val-R²=0.34 kam. Gleiche Ursache: das reine
#                    Partie-Endergebnis haengt fuer fruehe Zustaende von noch
#                    ungezogenen Fabrik-Neubefuellungen ab (siehe oben), das
#                    trifft `values` genauso wie `points_forecast`.
#                    Ab Version 13 (2026-07-19): Kalibrierungs-Diagnose auf
#                    v8e zeigte corr(val_true, pts_true) nur 0.49 (die beiden
#                    ZIELE selbst stimmen nur maessig ueberein -- points_forecast
#                    gewichtet own_total stark, values ist reines Sieg/
#                    Niederlage), UND beide Koepfe fitten die (ueberwiegend
#                    gesehenen) Trainingsdaten aehnlich gut (corr(pred,true)
#                    ~0.68-0.69) -- das Problem ist also eine echte
#                    Generalisierungsluecke, kein grundsaetzlich ungelernbares
#                    Ziel. Hypothese: das HARTE ±1-Ziel (Fallback ohne rtv)
#                    ist "schaerfer" als das weiche, kontinuierliche
#                    points_forecast-Ziel und treibt den gemeinsamen Trunk
#                    staerker Richtung Overfitting (v8e: Val-R² startet bei
#                    Epoche 1 positiv (+0.135), zerfaellt danach monoton --
#                    klassisches Overfitting-Muster). Fallback (ohne rtv)
#                    daher von hartem sign(own_total-opp_total) auf ein
#                    weiches, SYMMETRISCHES Margin-Ziel umgestellt:
#                    tanh((own_total-opp_total)/VALUE_SCALE) -- selbe
#                    zugrundeliegende Information wie zuvor, nur nicht mehr
#                    an den Raendern gesaettigt/binarisiert. `rtv` bleibt
#                    unveraendert bevorzugt, wo vorhanden.
# Ab Version 14 (Fund 7, externe Bugfix-Review Bugfixes.txt Abschnitt C):
#                    `scores` klemmt regelkonform bei 0 (PlayerBoard::apply_score)
#                    -- das verwischt im Fallback-Zweig (kein rtv) "schlecht"
#                    (0) und "desastroes" (eigentlich weit im Minus) zum
#                    selben Label. own_total/opp_total nutzen daher jetzt
#                    `scores_unclamped` (nie geklemmt, self_play.rs), mit
#                    Fallback auf `scores` falls das Feld in aelteren Daten
#                    fehlt (gleiches Graceful-Degradation-Muster wie
#                    policy_weights/points_forecast oben). `rtv`-Zweig bleibt
#                    unveraendert (eigene, bereits ungeklemmte Quelle).
# Ab Version 15 (Punkt 6, evaluations/value head tests.txt): TD-Bootstrap-
#                    Blend. Der Noise-Floor-Test (STATUS.md, 2026-07-20/21,
#                    bias-korrigiert) zeigt fuer Runde 1 einen praktisch
#                    nicht von Null unterscheidbaren Deckel fuers
#                    Endergebnis-Ziel (auch `rtv` zielt darauf, nur variance-
#                    reduziert -- gleiche niedrige Decke). `bootstrap_value`
#                    (self_play.rs::bootstrap_value_after_rounds, NUR
#                    BOOTSTRAP_HORIZON_ROUNDS Runden vorausgeschaut statt bis
#                    zum echten Spielende) zielt auf eine NAEHERE, laut der
#                    Runde-fuer-Runde-R²-Tabelle deutlich hoehere Decke.
#                    Wo vorhanden, wird es TD(lambda)-artig mit dem
#                    bisherigen Ziel gemischt (TD_LAMBDA, siehe unten) --
#                    ERSETZT `val`/`points_val` NICHT vollstaendig wie `rtv`,
#                    sondern mischt hinein. Erster, ungetesteter Wert.
VALUE_SCHEMA_VERSION = 15
VALUE_OPP_EPSILON = 0.1
VALUE_SCALE = 50.0
# Mischgewicht fuer `bootstrap_value` (Punkt 6) -- 0.0 = nur bisheriges Ziel
# (Endergebnis bzw. rtv-Override), 1.0 = nur der kurze Bootstrap-Horizont.
# 0.5 als erster, ungetesteter Startwert (gleichgewichtiger Blend) -- noch
# keine Arena-/R²-Validierung, bei Bedarf anpassen.
TD_LAMBDA = 0.5

# Policy-Ziel-Schärfung (Experiment, 2026-07-19): die rohen MCTS-Visit-Anteile
# (`step["policy"]`s `prob`-Werte, Heuristik-Selfplay) sind selbst oft recht
# flach (Stone-only-Diagnose: Ø Max-Prob nur 0.503, 41.7% "sehr flach") --
# das gemessene Policy-Top-1 des trainierten Netzes (61.8%) liegt nah an
# dieser Ziel-eigenen Unschärfe, nicht klar darunter (siehe
# project_v8d_value_head_root_cause-Memory). Exponent >1 schärft die
# Ziel-Verteilung vor dem Training nach (p → p^k, renormiert), OHNE neues
# Self-Play zu brauchen -- reiner Trainings-Loss-Hebel auf dem bestehenden
# Korpus. 1.0 = unveraendert (bisheriges Verhalten).
POLICY_TARGET_SHARPEN_EXPONENT = 2.0


class MosaicDataset(Dataset):
    def __init__(self, data_dir="data", files=None):
        """`files`: optionale explizite Dateiliste (z.B. ein Train- oder
        Val-Split desselben `data_dir`) -- ohne Angabe werden wie bisher ALLE
        `*.pkl` im Ordner geladen. Der Cache-Key haengt von der tatsaechlich
        uebergebenen Liste ab, Train- und Val-Split bekommen also automatisch
        getrennte HDF5-Caches im selben Ordner."""
        from config import INPUT_SIZE
        import hashlib, time
        import h5py
        import numpy as np

        # Cache-Datei basierend auf Dateiliste + INPUT_SIZE
        # TD_LAMBDA fehlte hier bisher im Hash (Retrain-Sweep-Audit,
        # 2026-07-22): der TD-Bootstrap-Blend wird in `val`/`points_val`
        # VOR dem Caching eingerechnet (siehe unten), ein Lambda-Sweep haette
        # also stillschweigend den Cache der ersten je Dateiliste gebauten
        # Lambda-Variante wiederverwendet und NICHTS gemessen. Jetzt Teil des
        # Keys, gleiche Stelle wie POLICY_TARGET_SHARPEN_EXPONENT.
        files = sorted(files) if files is not None else sorted(glob.glob(os.path.join(data_dir, "*.pkl")))
        cache_key = hashlib.md5(
            (str(files) + str(INPUT_SIZE) + str(NUM_ACTIONS) + str(VALUE_SCHEMA_VERSION)
             + str(POLICY_TARGET_SHARPEN_EXPONENT) + str(TD_LAMBDA)).encode()
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
                if 'points_forecast' in hf:
                    self.points_forecast = torch.from_numpy(hf['points_forecast'][:])
                else:  # alter Cache ohne Aux-Ziel → 0.0 (wird durch VALUE_SCHEMA_VERSION eh selten erreicht)
                    self.points_forecast = torch.zeros_like(self.values)
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
            self.points_forecast = torch.zeros_like(self.values)  # Legacy .pt kennt kein Aux-Ziel
            # Als HDF5 speichern
            with h5py.File(cache_path_h5, 'w') as hf:
                hf.create_dataset('states',              data=self.states.numpy(),              compression='lzf')
                hf.create_dataset('policies',            data=self.policies.numpy(),            compression='lzf')
                hf.create_dataset('values',               data=self.values.numpy(),              compression='lzf')
                hf.create_dataset('masks',               data=self.masks.numpy(),               compression='lzf')
                hf.create_dataset('moon_order_targets',  data=self.moon_order_targets.numpy(),  compression='lzf')
                hf.create_dataset('policy_weights',      data=self.policy_weights.numpy(),      compression='lzf')
                hf.create_dataset('points_forecast',     data=self.points_forecast.numpy(),     compression='lzf')
            os.remove(cache_path_pt)
            print(f"Datensatz geladen + migriert: {len(self.states)} Züge. "
                  f"(Features pro Zug: {self.states.shape[1]}) — {time.time()-t0:.1f}s")

        else:
            print(f"Lade Daten aus {len(files)} Dateien...")
            t0 = time.time()
            _CIDX = {'blau':0,'gelb':1,'rot':2,'schwarz':3,'türkis':4}
            states_l, policies_l, values_l, masks_l, moon_l = [], [], [], [], []
            polw_l = []  # Policy-Loss-Gewicht je Sample (1=Drafting, 0=Tiling/Start)
            points_l = []  # Aux-Ziel: Punktestand-Prognose (siehe VALUE_SCHEMA_VERSION oben)

            for f in files:
                with open(f, "rb") as file:
                    game_data = pickle.load(file)
                    for step in game_data:
                        states_l.append(state_to_tensor(step["state"]).numpy())
                        if "scores" in step and "winner" in step:
                            p = step["player"]
                            scores_src = step.get("scores_unclamped", step["scores"])
                            own_total = float(scores_src[p])
                            opp_total = float(scores_src[1 - p])
                            # Weiches, symmetrisches Margin-Ziel statt hartem
                            # ±1 (siehe VALUE_SCHEMA_VERSION=13-Kommentar oben)
                            # -- dieselbe own_total/opp_total-Information wie
                            # bisher, nur nicht mehr an den Raendern
                            # gesaettigt/binarisiert.
                            val = math.tanh((own_total - opp_total) / VALUE_SCALE)
                            # Punktestand-Formel bleibt als separates Aux-Ziel
                            # erhalten (bereits inkl. Wertungsplatten).
                            points_val = (math.tanh(own_total / VALUE_SCALE)
                                          - VALUE_OPP_EPSILON * math.tanh(opp_total / VALUE_SCALE))
                            # Rundenübergangs-Ziel (siehe round_transition.rs/
                            # self_play.rs::play_net_self_play_game): über
                            # mehrere Chance-Node-Samples (verschiedene mögliche
                            # Fabrik-Neubefüllungen) gemittelte NETZ-
                            # Gewinnwahrscheinlichkeit ([0,1], nicht Punkte --
                            # daher NICHT in die own_total/opp_total-Formel
                            # oben eingesetzt, sondern direkt auf den
                            # tanh-Wertebereich [-1,1] reskaliert). Nur
                            # vorhanden, wenn dieser Schritt tatsächlich einen
                            # Rundenübergang erreicht hat (nicht Runde 5, keine
                            # abgebrochenen Partien) -- sonst Fallback auf die
                            # obigen Formeln (hartes ±1 bzw. Punktestand).
                            #
                            # Ab Version 12 ersetzt own_rtv sowohl `val` (das
                            # Hauptziel, das net_mcts.rs tatsächlich für PUCT
                            # liest) als auch `points_val` -- own_rtv ist
                            # bereits exakt auf `val`s Skala (2*win_prob-1),
                            # daher direkt übernommen statt über die
                            # own_total/opp_total-Punkteformel geschickt.
                            rtv = step.get("round_transition_value")
                            if rtv is not None:
                                own_rtv = float(rtv[p]) * 2.0 - 1.0
                                opp_rtv = float(rtv[1 - p]) * 2.0 - 1.0
                                val = own_rtv
                                points_val = own_rtv - VALUE_OPP_EPSILON * opp_rtv
                            # Punkt 6 (VALUE_SCHEMA_VERSION=15): TD-Bootstrap-
                            # Blend, siehe Kommentar oben -- mischt HINEIN
                            # (ersetzt `val`/`points_val` nicht komplett wie
                            # `rtv`), da der kurze Horizont eine andere,
                            # naehere Groesse schaetzt als das bisherige Ziel.
                            bv = step.get("bootstrap_value")
                            if bv is not None:
                                own_bootstrap = float(bv[p]) * 2.0 - 1.0
                                opp_bootstrap = float(bv[1 - p]) * 2.0 - 1.0
                                points_bootstrap = own_bootstrap - VALUE_OPP_EPSILON * opp_bootstrap
                                val = TD_LAMBDA * own_bootstrap + (1.0 - TD_LAMBDA) * val
                                points_val = TD_LAMBDA * points_bootstrap + (1.0 - TD_LAMBDA) * points_val
                        else:
                            val = float(step["value"])
                            points_val = val
                        values_l.append([val])
                        points_l.append([points_val])

                        t_policy = np.zeros(NUM_ACTIONS, dtype=np.float32)
                        for pe in step["policy"]:
                            t_policy[action_to_id(pe["action"])] += pe["prob"]
                        s = t_policy.sum()
                        if s > 0: t_policy /= s
                        if POLICY_TARGET_SHARPEN_EXPONENT != 1.0:
                            t_policy = np.power(t_policy, POLICY_TARGET_SHARPEN_EXPONENT, dtype=np.float32)
                            s2 = t_policy.sum()
                            if s2 > 0: t_policy /= s2
                        policies_l.append(t_policy)

                        mask = np.zeros(NUM_ACTIONS, dtype=np.float32)
                        moves = step.get("valid_actions") or step["state"].get("valid_moves", [])
                        for move in moves:
                            mask[action_to_id(move)] = 1.0
                        # Selbstkonsistenz: die tatsächlich gespielten Policy-Aktionen
                        # sind per Definition legal — immer in die Maske aufnehmen.
                        # Verhindert Policy-Leaks (Target-Masse auf maskierter Aktion →
                        # explodierender Policy-Loss), falls valid_actions unvollständig ist.
                        for pe in step["policy"]:
                            mask[action_to_id(pe["action"])] = 1.0
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

            states_np    = np.array(states_l,    dtype=np.float32)
            policies_np  = np.array(policies_l,  dtype=np.float32)
            values_np    = np.array(values_l,    dtype=np.float32)
            masks_np     = np.array(masks_l,     dtype=np.float32)
            moon_np      = np.array(moon_l,      dtype=np.float32)
            polw_np      = np.array(polw_l,      dtype=np.float32)
            points_np    = np.array(points_l,    dtype=np.float32)
            # Die Python-Listen aus lauter einzelnen kleinen Arrays (ein Objekt pro
            # Zug, viel Overhead ggü. den kompakten *_np-Arrays) werden ab hier nicht
            # mehr gebraucht — explizit freigeben, statt sie bis Funktionsende (inkl.
            # dem folgenden HDF5-Schreiben) im Speicher mitzuschleppen. Bei größeren
            # Fenstern (mehrere hunderttausend Züge) sonst ein echtes Speicher-Nadelöhr.
            del states_l, policies_l, values_l, masks_l, moon_l, polw_l, points_l

            print(f"Datensatz geladen: {len(states_np)} Züge. "
                  f"(Features pro Zug: {states_np.shape[1]}) — {time.time()-t0:.1f}s")
            print(f"💾 Speichere HDF5-Cache...")
            with h5py.File(cache_path_h5, 'w') as hf:
                hf.create_dataset('states',               data=states_np,    compression='lzf')
                hf.create_dataset('policies',             data=policies_np,  compression='lzf')
                hf.create_dataset('values',               data=values_np,    compression='lzf')
                hf.create_dataset('masks',                data=masks_np,     compression='lzf')
                hf.create_dataset('moon_order_targets',   data=moon_np,      compression='lzf')
                hf.create_dataset('policy_weights',       data=polw_np,      compression='lzf')
                hf.create_dataset('points_forecast',      data=points_np,    compression='lzf')
            print(f"✅ Cache gespeichert: {cache_path_h5}")

            self.states             = torch.from_numpy(states_np)
            self.policies           = torch.from_numpy(policies_np)
            self.values             = torch.from_numpy(values_np)
            self.masks              = torch.from_numpy(masks_np)
            self.moon_order_targets = torch.from_numpy(moon_np)
            self.policy_weights     = torch.from_numpy(polw_np)
            self.points_forecast    = torch.from_numpy(points_np)

        self.input_size = self.states.shape[1] if len(self.states) > 0 else 100

    def __len__(self): return len(self.states)
    def __getitem__(self, idx):
        return (self.states[idx], self.policies[idx], self.values[idx], self.masks[idx],
                self.moon_order_targets[idx], self.policy_weights[idx], self.points_forecast[idx])


class MosaicNet(nn.Module):
    def __init__(self, input_size, num_actions=NUM_ACTIONS, hidden_size=HIDDEN_SIZE,
                 policy_hidden=256, value_hidden=64):
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
        # Moon-Order Head: 5 Logits (eine pro Farbe)
        # Hoher Wert = Farbe tief im Stapel (defensiv versteckt)
        # Niedriger Wert = Farbe oben (weniger strategisch wichtig)
        # Nur aktiv/trainiert bei Sonnenzügen
        self.moon_order_head = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Linear(32, 5)   # 5 Farben: blau, gelb, rot, schwarz, türkis
        )
        # Value-Head: Sieg/Niederlage (+1/-1), klassisches AlphaZero-Ziel --
        # zurueckgeholt, aber NICHT mehr fuer die Suche gedacht (Stufe 2 bleibt
        # tot, siehe evaluations/stage2_investigation.md), sondern als
        # Trainings-Zusatzsignal fuer den gemeinsamen Trunk.
        self.value_head = nn.Sequential(
            nn.Linear(hidden_size, value_hidden),
            nn.ReLU(),
            nn.Linear(value_hidden, 1),
            nn.Tanh()
        )
        # Punktestand-Prognose-Head (Aux-Ziel): dieselbe tanh-gestauchte
        # Punktedifferenz-Formel, die frueher der einzige Value-Head war --
        # jetzt als separater, feinerer Regressions-Kopf NEBEN dem robusteren
        # Sieg/Niederlage-Ziel (siehe VALUE_SCHEMA_VERSION in neural_net.py).
        self.points_head = nn.Sequential(
            nn.Linear(hidden_size, value_hidden),
            nn.ReLU(),
            nn.Linear(value_hidden, 1),
            nn.Tanh()
        )

    def forward(self, x):
        shared = self.body(x)
        return (
            self.policy_head(shared),
            self.value_head(shared),
            self.moon_order_head(shared),
            self.points_head(shared),
        )

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