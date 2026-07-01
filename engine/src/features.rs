//! Port von `engine/py/neural_net.py::state_to_tensor` und `action_to_id` nach Rust
//! (für den Network-Modus / Phase B). Arbeitet auf dem `serialize::state_to_json`-
//! Value — 1:1-Abbild der Python-Dict-Logik, damit die Feature-Reihenfolge und
//! -Normalisierung EXAKT übereinstimmen (per Paritätstest gegen Python verifiziert).

use serde_json::Value;

/// Feature-Vektor-Länge (= `config.INPUT_SIZE`). EINZIGE Quelle der Wahrheit
/// für die ONNX-Eingabegröße — bei jeder Feature-Änderung hier UND in
/// config.py aktualisieren (sonst `Net::load`-Shape-Mismatch beim Inferieren).
pub const INPUT_SIZE: usize = 684;

/// Per-Kriterium-Normalisierung der 8 Wertungsplatten-Punkte (= `SCORE_NORM`).
const SCORE_NORM: [f32; 8] = [18.0, 42.0, 20.0, 12.0, 20.0, 22.0, 12.0, 24.0];

/// Farb-String → COLOR_MAP-Index (blau=0 … türkis=4), sonst -1.
fn color_idx(s: Option<&str>) -> i64 {
    match s {
        Some("blau") => 0,
        Some("gelb") => 1,
        Some("rot") => 2,
        Some("schwarz") => 3,
        Some("türkis") => 4,
        _ => -1,
    }
}

/// COLOR_ID_MAP/DOME_COLOR_MAP: blau=1 … türkis=5, sonst 0.
fn color_id_1based(s: Option<&str>) -> f32 {
    match s {
        Some("blau") => 1.0,
        Some("gelb") => 2.0,
        Some("rot") => 3.0,
        Some("schwarz") => 4.0,
        Some("türkis") => 5.0,
        _ => 0.0,
    }
}

/// FILLED_ID_MAP: leer=0, blau=1 … türkis=5, special=6.
fn filled_id(s: Option<&str>) -> f32 {
    match s {
        Some("blau") => 1.0,
        Some("gelb") => 2.0,
        Some("rot") => 3.0,
        Some("schwarz") => 4.0,
        Some("türkis") => 5.0,
        Some("special") => 6.0,
        _ => 0.0,
    }
}

fn phase_id(s: &str) -> f32 {
    match s {
        "tiling" => 1.0,
        "end" => 2.0,
        "final" => 3.0,
        _ => 0.0, // drafting / start_placement
    }
}

/// Holt ein Zahlenarray `k` aus `obj`, auf Länge `n` (0-gepolstert).
fn arr_n(obj: Option<&Value>, k: &str, n: usize) -> Vec<f64> {
    let mut v: Vec<f64> = obj
        .and_then(|o| o.get(k))
        .and_then(|x| x.as_array())
        .map(|a| a.iter().map(|y| y.as_f64().unwrap_or(0.0)).collect())
        .unwrap_or_default();
    v.resize(n, 0.0);
    v
}

fn num(obj: &Value, k: &str) -> f64 {
    obj.get(k).and_then(|x| x.as_f64()).unwrap_or(0.0)
}

/// Vollständiger Feature-Vektor aus dem State-Dict (`state_to_json`).
pub fn state_to_features(v: &Value) -> Vec<f32> {
    let mut f: Vec<f32> = Vec::with_capacity(INPUT_SIZE);

    // 1. Globale Infos
    f.push((num(v, "round") / 6.0) as f32);
    let phase = v.get("phase").and_then(|x| x.as_str()).unwrap_or("drafting");
    f.push(phase_id(phase) / 3.0);
    // Beutel-Restbestand (max. 65 Fliesen zu Spielbeginn).
    f.push((num(v, "bag_count") / 65.0) as f32);

    // 2. Wertungsplatten one-hot (8)
    let sids: Vec<i64> = v
        .get("scoring_tile_ids")
        .and_then(|x| x.as_array())
        .map(|a| a.iter().filter_map(|x| x.as_i64()).collect())
        .unwrap_or_default();
    for i in 0..8 {
        f.push(if sids.contains(&i) { 1.0 } else { 0.0 });
    }

    // 3. Kleine Manufakturen: 5 Sun-Counts /5 + has_chip + chip_revealed
    let empty = Vec::new();
    let factories = v.get("factories").and_then(|x| x.as_array()).unwrap_or(&empty);
    for fac in factories {
        let mut counts = [0f32; 5];
        if let Some(sun) = fac.get("sun").and_then(|x| x.as_array()) {
            for c in sun {
                let id = color_idx(c.as_str());
                if (0..5).contains(&id) {
                    counts[id as usize] += 1.0;
                }
            }
        }
        for c in counts {
            f.push(c / 5.0);
        }
        f.push(if fac.get("bonus_chip").map_or(false, |x| !x.is_null()) { 1.0 } else { 0.0 });
        let revealed = fac.get("chip_revealed").and_then(|x| x.as_bool()).unwrap_or(false);
        f.push(if revealed { 1.0 } else { 0.0 });

        // Farben des Bonus-Chips (5-dim Maske) — NUR wenn aufgedeckt (sonst
        // versteckte Information, die kein Spieler kennt).
        let mut chip_mask = [0f32; 5];
        if revealed {
            if let Some(cols) = fac.get("bonus_chip").and_then(|x| x.get("colors")).and_then(|x| x.as_array()) {
                for c in cols {
                    let id = color_idx(c.as_str());
                    if (0..5).contains(&id) {
                        chip_mask[id as usize] = 1.0;
                    }
                }
            }
        }
        f.extend_from_slice(&chip_mask);
    }

    // 4. Große Manufaktur: 5 Sun-Counts /10
    let lf = v.get("large_factory").cloned().unwrap_or(Value::Null);
    let mut lf_sun = [0f32; 5];
    if let Some(sun) = lf.get("sun").and_then(|x| x.as_array()) {
        for c in sun {
            let id = color_idx(c.as_str());
            if (0..5).contains(&id) {
                lf_sun[id as usize] += 1.0;
            }
        }
    }
    for c in lf_sun {
        f.push(c / 10.0);
    }

    // Spieler (Ego-Perspektive)
    let players = v.get("players").and_then(|x| x.as_array()).unwrap_or(&empty);
    let curr_pi = v.get("current_player").and_then(|x| x.as_i64()).unwrap_or(0) as usize;
    let enemy_pi = 1 - curr_pi;
    if players.len() == 2 {
        let order = [(&players[curr_pi], curr_pi), (&players[enemy_pi], enemy_pi)];
        let chippable = v.get("chippable_tiling_rows").and_then(|x| x.as_array()).unwrap_or(&empty);

        // 5. Spielerblock (57 je Spieler)
        for (p, pi) in &order {
            f.push((num(p, "score") / 100.0) as f32);
            f.push((num(p, "estimated_score") / 100.0) as f32);
            f.push(if p.get("marker").and_then(|x| x.as_bool()).unwrap_or(false) { 1.0 } else { 0.0 });

            if let Some(rows) = p.get("pattern_lines").and_then(|x| x.as_array()) {
                for row in rows {
                    let cap = row.get("capacity").and_then(|x| x.as_f64()).unwrap_or(1.0);
                    let cap = if cap < 1.0 { 1.0 } else { cap };
                    let n = row.get("tiles").and_then(|x| x.as_array()).map_or(0, |a| a.len()) as f64;
                    f.push((n / cap) as f32);
                    let cid = color_idx(row.get("color").and_then(|x| x.as_str()));
                    for i in 0..5i64 {
                        f.push(if i == cid { 1.0 } else { 0.0 });
                    }
                }
            }

            let floor_n = p.get("floor").and_then(|x| x.as_array()).map_or(0, |a| a.len()) as f32;
            f.push(floor_n / 4.0); // MAX_BROKEN=4 (nicht 7)
            f.push((num(p, "tokens_used") / 2.0) as f32);
            f.push((num(p, "chips_taken") / 2.0) as f32);

            let mut chip_cnt = [0f32; 5];
            if let Some(chips) = p.get("bonus_chips").and_then(|x| x.as_array()) {
                for chip in chips {
                    if let Some(cols) = chip.get("colors").and_then(|x| x.as_array()) {
                        for c in cols {
                            let id = color_idx(c.as_str());
                            if (0..5).contains(&id) {
                                chip_cnt[id as usize] += 1.0;
                            }
                        }
                    }
                }
            }
            for c in chip_cnt {
                f.push(c / 4.0);
            }

            // Chip-Abschließbarkeit Reihen 1..5
            for ri in 1..6i64 {
                let has = chippable.iter().any(|e| {
                    e.get("pi").and_then(|x| x.as_i64()) == Some(*pi as i64)
                        && e.get("ri").and_then(|x| x.as_i64()) == Some(ri)
                });
                f.push(if has { 1.0 } else { 0.0 });
            }
        }

        // 6. Kuppelzustand (9 Slots × 17, je Spieler)
        for (p, _) in &order {
            let dome = p.get("dome_grid").and_then(|x| x.as_array());
            for sr in 0..3 {
                for sc in 0..3 {
                    let slot = dome
                        .and_then(|d| d.get(sr))
                        .and_then(|r| r.as_array())
                        .and_then(|r| r.get(sc));
                    match slot {
                        Some(s) if !s.is_null() => {
                            f.push(1.0);
                            let spaces = s.get("spaces").and_then(|x| x.as_array());
                            for si in 0..4 {
                                let sp = spaces.and_then(|sp| sp.get(si));
                                let filled = sp.and_then(|x| x.get("filled")).and_then(|x| x.as_str());
                                f.push(filled_id(filled) / 6.0);
                                let req = sp.and_then(|x| x.get("color")).and_then(|x| x.as_str());
                                f.push(color_id_1based(req) / 5.0);
                                let typ = sp.and_then(|x| x.get("type")).and_then(|x| x.as_str()).unwrap_or("NORMAL");
                                f.push(match typ {
                                    "WILD" => 0.5,
                                    "SPECIAL" => 1.0,
                                    _ => 0.0,
                                });
                                let locked = sp.and_then(|x| x.get("locked")).and_then(|x| x.as_bool()).unwrap_or(false);
                                f.push(if locked { 1.0 } else { 0.0 });
                            }
                        }
                        _ => {
                            for _ in 0..17 {
                                f.push(0.0);
                            }
                        }
                    }
                }
            }
        }

        // 6b. Endwertungs-Features (37 je Spieler)
        for (p, _) in &order {
            let pts = p.get("scoring_tile_points");
            for i in 0..8 {
                let val = pts.and_then(|a| a.get(i)).and_then(|x| x.as_f64()).unwrap_or(0.0) as f32;
                f.push(val / SCORE_NORM[i]);
            }
            let geo = p.get("score_geo");
            for x in arr_n(geo, "row_fill", 6) {
                f.push((x / 6.0) as f32);
            }
            for x in arr_n(geo, "col_fill", 6) {
                f.push((x / 6.0) as f32);
            }
            for x in arr_n(geo, "diag_fill", 2) {
                f.push((x / 6.0) as f32);
            }
            for x in arr_n(geo, "row_colors", 6) {
                f.push((x / 5.0) as f32);
            }
            let g = |k: &str| geo.and_then(|o| o.get(k)).and_then(|x| x.as_f64()).unwrap_or(0.0);
            f.push((g("border_fill") / 20.0) as f32);
            for x in arr_n(geo, "corner_fill", 4) {
                f.push((x / 4.0) as f32);
            }
            f.push((g("wild_filled") / 8.0) as f32);
            f.push((g("wild_total") / 8.0) as f32);
            f.push((g("special_empty") / 8.0) as f32);
            f.push((g("special_total") / 8.0) as f32);
        }

        // 6c. Linien-Geometrie (23 je Spieler)
        for (p, _) in &order {
            let lg = p.get("line_geo");
            for x in arr_n(lg, "h_hist", 5) {
                f.push((x / 6.0) as f32);
            }
            for x in arr_n(lg, "v_hist", 5) {
                f.push((x / 6.0) as f32);
            }
            let cs = lg.and_then(|o| o.get("cluster_sq")).and_then(|x| x.as_f64()).unwrap_or(0.0);
            f.push((cs / 150.0) as f32);
            for x in arr_n(lg, "row_potential", 6) {
                f.push((x / 12.0) as f32);
            }
            for x in arr_n(lg, "col_potential", 6) {
                f.push((x / 12.0) as f32);
            }
        }
    }

    // 7. Mondseite kleine Fabriken (4 × 15)
    for fac in factories {
        let mut mf = [0f32; 15];
        if let Some(stacks) = fac.get("moon").and_then(|x| x.as_array()) {
            if let Some(stack) = stacks.first().and_then(|x| x.as_array()) {
                for (pos, stone) in stack.iter().rev().enumerate() {
                    if pos >= 3 {
                        break;
                    }
                    let id = color_idx(stone.as_str());
                    if id >= 0 {
                        mf[pos * 5 + id as usize] = 1.0;
                    }
                }
            }
        }
        for x in mf {
            f.push(x);
        }
    }

    // 8. GF Moon-Pool /10
    let mut pool = [0f32; 5];
    if let Some(m) = lf.get("moon").and_then(|x| x.as_array()) {
        for c in m {
            let id = color_idx(c.as_str());
            if id >= 0 {
                pool[id as usize] += 1.0;
            }
        }
    }
    for c in pool {
        f.push(c / 10.0);
    }

    // 9. Kuppel-Display (3 × 4 × 2)
    let display = v.get("dome_display").and_then(|x| x.as_array());
    for slot_idx in 0..3 {
        let plate = display.and_then(|d| d.get(slot_idx));
        let spaces = plate
            .and_then(|p| if p.is_null() { None } else { p.get("spaces") })
            .and_then(|x| x.as_array());
        for space_idx in 0..4 {
            match spaces.and_then(|s| s.get(space_idx)) {
                Some(space) => {
                    let filled = space.get("filled");
                    f.push(if filled.map_or(true, |x| x.is_null()) { 0.0 } else { 1.0 });
                    let req = space.get("color").and_then(|x| x.as_str());
                    f.push(color_id_1based(req) / 5.0);
                }
                None => {
                    f.push(0.0);
                    f.push(0.0);
                }
            }
        }
    }

    // 10. Kuppel-Stapel
    f.push((num(v, "dome_stack_count") / 20.0) as f32);

    f
}

/// Port von `action_to_id` (für Masken/Prior-Zuordnung). Erwartet ein
/// env-Action-Dict (agent_env-Schema).
pub fn action_to_id(a: &Value) -> usize {
    let t = a.get("type").and_then(|x| x.as_str()).unwrap_or("");
    let geti = |k: &str| a.get(k).and_then(|x| x.as_i64()).unwrap_or(0);
    match t {
        "pass" => 0,
        "end_tiling" => 1,
        "stone" => {
            let c_id = color_idx(a.get("color").and_then(|x| x.as_str())).max(0);
            let r_id = geti("row") + 1;
            let f_idx = geti("factory_index");
            (10 + c_id * 48 + r_id * 6 + f_idx).min(273) as usize
        }
        "tiling" => (274 + geti("pattern_row") * 9 + geti("slot_row") * 3 + geti("slot_col")) as usize,
        "dome" => {
            (328 + geti("display_index") * 36 + geti("slot_row") * 12 + geti("slot_col") * 4
                + geti("rotation") / 90) as usize
        }
        "dome_stack" => {
            (436 + geti("slot_row") * 12 + geti("slot_col") * 4 + geti("rotation") / 90) as usize
        }
        "use_chips" => (472 + geti("pattern_row")) as usize,
        "bonus_chip" => (478 + geti("factory_index")) as usize,
        _ => 481,
    }
}
