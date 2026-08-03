# -*- coding: utf-8 -*-
"""
Mosaic-AI -- Runde-4-Ende-Value-Kalibrierung gegen exakte Ground Truth
(Chance-Knoten-Erwartung ueber die Fabrik-Neubefuellung 4->5)
============================================================================

Siehe `evaluations/PREREG_r4_value_calibration.md` fuer die volle Herleitung
-- hier nur die Kurzfassung der Mechanik (Vorbild + Import-Wiederverwendung
`tools/r5_value_calibration.py`, Memory `feedback_check_existing_tools_first`):

1. SUBSTRAT: Self-Play-Dateien (`--data-glob`, Default `data/selfplay_v18_*.pkl`).
   Je Partie das Paar (letzter R4-Record mit `phase=="tiling"`, erster
   R5-Drafting-Record). Partien ohne diese Konstellation werden ausgeschlossen
   (Quote wird berichtet).

2. GROUND TRUTH je Runde-4-Endzustand: `mosaic_rust.autoplay_to_round5_and_
   resample_json(r4_state_json, K, seed)` -- deterministischer Vorlauf bis
   Rundenende + K unabhaengige Fabrik-Neubefuellungen (Vorwaerts-Sampling,
   PREREG-Redesign 2026-08-03, umgeht die 87,6%-Turm-Ambiguitaet der
   Inversions-Variante `resample_round_transition_json` komplett). Je Sample
   `ab_value = net_search_state_json(sample, model_path_for_api, sims,
   c_puct, seed)["moves"][ai_action]["ab_value"]` -- exakte Punkte-Marge
   unter optimalem Runde-5-Spiel (`round5.rs`-Kurzschluss, identisch zum
   R5-Werkzeug). `true_margin` = Mittel der K `ab_value`, `true_winprob` =
   Anteil `ab_value>0` (Ties zaehlen 0,5).

3. MODELL-MEINUNG: Torch-Forward-Pass auf dem R4-End-Record selbst (KEINE
   Wertungsplatten-Variation wie im R5-Werkzeug -- hier zaehlt der reale
   Zustand) ueber `r5_value_calibration.load_torch_model`/
   `raw_value_points_torch` (identischer Code, direkt importiert statt
   dupliziert).

4. PERSPEKTIVEN-MAPPING (Pflicht, PREREG-Abschnitt "Perspektiven-Mapping"):
   `ab_value` ist aus Sicht des `current_player` des jeweiligen R5-Samples
   (== `first_player_next_round`, fuer alle Samples einer Partie gleich),
   Modell-Rohwerte aus Sicht des `current_player` des R4-End-Records. Beide
   werden auf eine feste Spieler-0-Perspektive gemappt (Vorzeichen-Flip bzw.
   p -> 1-p ueber denselben Flip VOR `value_to_win_prob`).

5. KONSISTENZ-ANKER: (a) `dome_grids` des zurueckgegebenen `r4_end_state`
   muessen mit denen des echten ersten R5-Records uebereinstimmen (NICHT
   Scores/Boden -- Rundenend-Strafen sind im `r4_end_state` noch nicht
   verrechnet, PREREG-Nachtrag "Implementierungs-Detail"); (b) Vorzeichen
   des `ab_value` der ECHTEN Befuellung (17. Sample = der tatsaechliche
   erste R5-Record) vs. tatsaechlicher Partie-Gewinner (`winner`-Feld,
   identisch ueber alle Records einer Partie hinweg verifiziert).

6. MESSGROESSEN (PREREG-Abschnitt "Messgroessen"): (1) OLS-Steigung+R² Value-
   Kopf gegen `true_winprob`, (2) OLS-Steigung+R² Punkte-Kopf gegen
   `true_margin`, (3) `R²_max`-Varianzzerlegung auf Sieg- UND Margen-Skala
   (K/(K-1)- bzw. n-1-Korrekturen) gegen den realisierten Modell-R²
   (einmal gegen einzelne Refill-Ausgaenge, einmal gegen `E[z|s]`/
   `true_margin`) + Bootstrap-Schaetzfehler fuer `R²_max` (Resampling ueber
   Zustaende, Perzentil-Intervall).
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import pickle
import random
import sys
from collections import OrderedDict

import numpy as np

# Windows-Konsole ohne UTF-8 (cp1252): schuetzt Sonderzeichen in Prints
# (Muster aus tools/train_lambda_sweep.py).
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

import mosaic_rust  # noqa: E402

# tools/ liegt bereits in sys.path[0] (Skript-Verzeichnis) -- r5_value_calibration
# kuemmert sich selbst um ROOT/engine/py-Pfade (Memory feedback_check_existing_tools_first:
# Bausteine importieren statt duplizieren).
from r5_value_calibration import (  # noqa: E402
    load_torch_model, raw_value_points_torch, value_to_win_prob, points_to_pts, ols_slope_r2,
)


# ── Positions-Substrat: (letzter R4-Record, erster R5-Record) je Partie ────

def find_r4_r5_pairs_in_file(path: str):
    """Gibt (Liste von (game_id, r4_rec, r5_rec), n_excl_no_tiling, n_excl_no_r5)
    fuer eine Self-Play-Datei zurueck. `recs` ist eine flache Liste von
    Entscheidungspunkten mehrerer Partien -- Reihenfolge innerhalb einer
    Partie ist chronologisch (verifiziert), Partien selbst koennen
    verschraenkt sein."""
    with open(path, "rb") as f:
        recs = pickle.load(f)
    by_game = OrderedDict()
    for r in recs:
        by_game.setdefault(r["game_id"], []).append(r)

    pairs = []
    n_excl_no_tiling = 0
    n_excl_no_r5 = 0
    for gid, game_recs in by_game.items():
        last_r4_idx = None
        for i, r in enumerate(game_recs):
            if r["state"]["round"] == 4:
                last_r4_idx = i
        if last_r4_idx is None:
            continue  # keine R4-Phase in dieser Partie erfasst -- kein PREREG-Ausschlussfall
        r4_rec = game_recs[last_r4_idx]
        if r4_rec["state"]["phase"] != "tiling":
            n_excl_no_tiling += 1
            continue
        r5_rec = None
        for j in range(last_r4_idx + 1, len(game_recs)):
            rj = game_recs[j]
            if rj["state"]["round"] == 5 and rj["state"]["phase"] == "drafting":
                r5_rec = rj
                break
            if rj["state"]["round"] > 5:
                break
        if r5_rec is None:
            n_excl_no_r5 += 1
            continue
        pairs.append((gid, r4_rec, r5_rec))
    return pairs, n_excl_no_tiling, n_excl_no_r5


def select_states(data_glob: str, n_states: int, seed: int, pool_buffer_factor: int = 8):
    """Zufaellige Zustandsauswahl mit festem Seed. Aus Performance-Gruenden
    (der volle Bestand kann hunderte Dateien umfassen) wird die Datei-
    Reihenfolge geseedet gemischt und das Scannen gestoppt, sobald ein
    Kandidaten-Pool von `n_states * pool_buffer_factor` erreicht ist -- die
    finale Auswahl ist dann ein geseedeter Sample aus diesem Pool. Das ist
    eine praktische Naeherung an "voll-zufaellig ueber alle geeigneten
    Partien" (dokumentiert statt verschwiegen); fuer den vollen Lauf (N=24)
    reicht ein Puffer von 8x locker, ohne alle Dateien laden zu muessen."""
    files = sorted(glob.glob(data_glob))
    if not files:
        raise RuntimeError(f"Kein Self-Play-Bestand fuer Glob {data_glob!r} gefunden.")
    rng = random.Random(seed)
    rng.shuffle(files)

    pool = []
    n_excl_no_tiling = 0
    n_excl_no_r5 = 0
    n_games_scanned = 0
    files_scanned = 0
    target_pool = max(n_states * pool_buffer_factor, n_states)
    for path in files:
        pairs, excl_t, excl_r5 = find_r4_r5_pairs_in_file(path)
        n_excl_no_tiling += excl_t
        n_excl_no_r5 += excl_r5
        n_games_scanned += len(pairs) + excl_t + excl_r5
        pool.extend((path, gid, r4, r5) for gid, r4, r5 in pairs)
        files_scanned += 1
        if len(pool) >= target_pool:
            break

    if len(pool) < n_states:
        raise RuntimeError(
            f"Nur {len(pool)} geeignete Zustaende gefunden (n_states={n_states} noetig) -- "
            f"mehr Dateien noetig oder pool_buffer_factor erhoehen."
        )
    rng.shuffle(pool)
    chosen = pool[:n_states]
    excl_total = n_excl_no_tiling + n_excl_no_r5
    stats = {
        "files_matched": len(files),
        "files_scanned": files_scanned,
        "games_scanned": n_games_scanned,
        "excluded_no_r4_tiling_end": n_excl_no_tiling,
        "excluded_no_r5_draft_start": n_excl_no_r5,
        "exclusion_rate": (excl_total / n_games_scanned) if n_games_scanned else None,
        "pool_size_before_final_sample": len(pool),
    }
    return chosen, stats


# ── Ground Truth (round5.rs via net_search_state_json, wie im R5-Werkzeug) ─

def ab_value_for_state(state: dict, model_path_for_api: str, sims: int, c_puct: float, seed: int):
    out = json.loads(mosaic_rust.net_search_state_json(json.dumps(state), model_path_for_api, sims, c_puct, seed))
    ai_action = out.get("ai_action")
    moves = out.get("moves") or []
    if ai_action is None or not moves or ai_action >= len(moves):
        return None
    return moves[ai_action].get("ab_value")


def to_player0(value, current_player: int):
    """Perspektiven-Mapping: current_player==0 -> unveraendert, ==1 -> Vorzeichen-Flip.
    Fuer Value-Kopf-Rohwerte VOR `value_to_win_prob` anwenden (Flip dort
    aequivalent zu p -> 1-p, siehe Moduldoku Punkt 4)."""
    return value if current_player == 0 else -value


def dome_grids_equal(state_a: dict, state_b: dict) -> bool:
    grids_a = [p["dome_grid"] for p in state_a["players"]]
    grids_b = [p["dome_grid"] for p in state_b["players"]]
    return grids_a == grids_b


# ── Je-Zustand-Messung ───────────────────────────────────────────────────

def measure_one_state(game_id: str, r4_rec: dict, r5_rec: dict, k_refills: int,
                       model, encoder: str, model_path_for_api: str, sims: int, c_puct: float,
                       seed: int, state_index: int):
    r4_state = r4_rec["state"]
    r4_cur = r4_state["current_player"]
    actual_winner = r4_rec.get("winner")

    # Modell-Meinung (Torch, identischer Code wie r5_value_calibration) --
    # KEINE Wertungsplatten-Variation, realer Zustand.
    raw_value, raw_points = raw_value_points_torch(model, encoder, r4_state, r4_state["scoring_tile_ids"])
    raw_value_p0 = to_player0(raw_value, r4_cur)
    raw_points_p0 = to_player0(raw_points, r4_cur)
    win_prob_model_p0 = value_to_win_prob(raw_value_p0)
    margin_model_p0 = points_to_pts(raw_points_p0)

    # Vorwaerts-Sampling: deterministischer Vorlauf bis Rundenende + K Neubefuellungen.
    resample_seed = seed + 900000 + state_index
    result = json.loads(mosaic_rust.autoplay_to_round5_and_resample_json(
        json.dumps(r4_state), k_refills, resample_seed))
    r4_end_state = result["r4_end_state"]
    r5_samples = result["r5_samples"]

    # Konsistenz-Anker (a): dome_grids des deterministischen Vorlaufs muessen
    # mit dem echten ersten R5-Record uebereinstimmen (nicht Scores/Boden).
    anchor_dome_ok = dome_grids_equal(r4_end_state, r5_rec["state"])

    # Refill-Ground-Truth (K Samples), auf Spieler-0-Perspektive gemappt.
    refill_ab_p0 = []
    sample_cur_players = set()
    for k, sample in enumerate(r5_samples):
        sample_cur = sample["current_player"]
        sample_cur_players.add(sample_cur)
        ab = ab_value_for_state(sample, model_path_for_api, sims, c_puct, seed + state_index * 1000 + k + 1)
        if ab is None:
            continue
        refill_ab_p0.append(to_player0(ab, sample_cur))
    perspective_consistent = len(sample_cur_players) <= 1

    k_valid = len(refill_ab_p0)
    if k_valid >= 2:
        true_margin = float(np.mean(refill_ab_p0))
        true_winprob = float(np.mean([1.0 if v > 0 else (0.5 if v == 0 else 0.0) for v in refill_ab_p0]))
        var_k_ab = float(np.var(refill_ab_p0, ddof=1))  # Stichproben-Korrektur n-1, PREREG Margen-Skala
    else:
        true_margin = None
        true_winprob = None
        var_k_ab = None

    # Konsistenz-Anker (b): Vorzeichen der ECHTEN Befuellung (17. Sample) vs.
    # tatsaechlicher Partie-Gewinner.
    real_cur = r5_rec["state"]["current_player"]
    ab_real = ab_value_for_state(r5_rec["state"], model_path_for_api, sims, c_puct,
                                  seed + state_index * 1000 + k_refills + 1)
    anchor_sign_match = None
    if ab_real is not None and ab_real != 0:
        predicted_winner = real_cur if ab_real > 0 else (1 - real_cur)
        anchor_sign_match = bool(predicted_winner == actual_winner)

    return {
        "game_id": game_id,
        "state_index": state_index,
        "r4_current_player": r4_cur,
        "raw_value_p0": raw_value_p0, "raw_points_p0": raw_points_p0,
        "win_prob_model_p0": win_prob_model_p0, "margin_model_p0": margin_model_p0,
        "anchor_dome_grids_ok": anchor_dome_ok,
        "refill_ab_value_p0": refill_ab_p0, "k_valid": k_valid,
        "true_margin": true_margin, "true_winprob": true_winprob, "var_k_ab_p0": var_k_ab,
        "perspective_consistent_within_state": perspective_consistent,
        "sample_current_players": sorted(sample_cur_players),
        "real_r5_current_player": real_cur,
        "ab_value_real_refill": ab_real,
        "actual_winner": actual_winner,
        "anchor_sign_match_actual_winner": anchor_sign_match,
    }


# ── R²-Hilfsfunktionen ───────────────────────────────────────────────────

def r2_fixed(pred, target):
    """R² eines FESTEN Praediktors gegen realisierte Ausgaenge -- identische
    Definition wie die bestehende `value_r2`-Metrik (`train.py::_r2`):
    1 - sum((pred-target)^2) / sum((target-mean(target))^2). KEINE OLS-
    Anpassung (im Unterschied zu `ols_slope_r2`)."""
    pred = np.asarray(pred, dtype=np.float64)
    target = np.asarray(target, dtype=np.float64)
    ss_tot = float(np.sum((target - target.mean()) ** 2))
    if ss_tot <= 1e-9:
        return None
    sqerr = float(np.sum((pred - target) ** 2))
    return 1.0 - sqerr / ss_tot


def r2_max_win_scale(p_s: np.ndarray, k: np.ndarray):
    """R²_max = Var_s(2p_s-1) / (Var_s(2p_s-1) + mean_s[4p_s(1-p_s)*K/(K-1)])."""
    var_between = float(np.var(2.0 * p_s - 1.0))  # Populationsvarianz ueber Zustaende
    within = float(np.mean(4.0 * p_s * (1.0 - p_s) * (k / (k - 1.0))))
    denom = var_between + within
    return (var_between / denom) if denom > 1e-12 else float("nan")


def r2_max_margin_scale(true_margin: np.ndarray, var_k_ab: np.ndarray):
    """R²_max = Var_s(true_margin_s) / (Var_s(true_margin_s) + mean_s[Var_k(ab_value_k)])."""
    var_between = float(np.var(true_margin))  # Populationsvarianz ueber Zustaende
    within = float(np.mean(var_k_ab))  # je Zustand bereits n-1-korrigiert
    denom = var_between + within
    return (var_between / denom) if denom > 1e-12 else float("nan")


def bootstrap_r2_max(per_state, n_bootstrap: int, seed: int):
    """Bootstrap-Schaetzfehler fuer R²_max: Resampling MIT Zurueglegen ueber
    die N Zustaende (nicht ueber Refills), Perzentil-Intervall [2.5, 97.5]."""
    rng = np.random.RandomState(seed)
    n = len(per_state)
    p_s = np.array([s["true_winprob"] for s in per_state])
    k = np.array([float(s["k_valid"]) for s in per_state])
    true_margin = np.array([s["true_margin"] for s in per_state])
    var_k_ab = np.array([s["var_k_ab_p0"] for s in per_state])

    win_samples = []
    margin_samples = []
    for _ in range(n_bootstrap):
        idx = rng.randint(0, n, size=n)
        win_samples.append(r2_max_win_scale(p_s[idx], k[idx]))
        margin_samples.append(r2_max_margin_scale(true_margin[idx], var_k_ab[idx]))
    win_samples = np.array(win_samples, dtype=np.float64)
    margin_samples = np.array(margin_samples, dtype=np.float64)
    return {
        "win_scale": {
            "point": r2_max_win_scale(p_s, k),
            "ci_2_5": float(np.nanpercentile(win_samples, 2.5)),
            "ci_97_5": float(np.nanpercentile(win_samples, 97.5)),
        },
        "margin_scale": {
            "point": r2_max_margin_scale(true_margin, var_k_ab),
            "ci_2_5": float(np.nanpercentile(margin_samples, 2.5)),
            "ci_97_5": float(np.nanpercentile(margin_samples, 97.5)),
        },
    }


# ── Modell-Messung ueber N Zustaende ────────────────────────────────────

def measure_model(pth_path: str, chosen_states: list, k_refills: int, model_path_for_api: str,
                   sims: int, c_puct: float, seed: int, n_bootstrap: int, smoke: bool = False):
    model, encoder = load_torch_model(pth_path)
    per_state = []
    for si, (path, gid, r4_rec, r5_rec) in enumerate(chosen_states):
        row = measure_one_state(gid, r4_rec, r5_rec, k_refills, model, encoder,
                                 model_path_for_api, sims, c_puct, seed, si)
        per_state.append(row)
        if smoke:
            print(f"  Zustand {si} (game={gid}, Datei={os.path.basename(path)}):")
            print(f"    R4 current_player={row['r4_current_player']}  raw_value_p0={row['raw_value_p0']:.4f} "
                  f"win_prob_model_p0={row['win_prob_model_p0']:.4f}  margin_model_p0={row['margin_model_p0']:.3f}")
            print(f"    Konsistenz-Anker (a) dome_grids r4_end_state == echter R5-Start: {row['anchor_dome_grids_ok']}")
            print(f"    Perspektiven-Check: sample_current_players={row['sample_current_players']} "
                  f"(alle Refills gleich? {row['perspective_consistent_within_state']}), "
                  f"real_r5_current_player={row['real_r5_current_player']}")
            print(f"    Refill ab_value (Spieler-0-Perspektive, {row['k_valid']}/{k_refills} gueltig): "
                  f"{[round(v, 2) for v in row['refill_ab_value_p0']]}")
            streuung = (np.std(row["refill_ab_value_p0"]) if row["k_valid"] >= 2 else None)
            print(f"    Streuung (std)={streuung}  Streuung>0? {bool(streuung and streuung > 0)}")
            print(f"    true_margin={row['true_margin']}  true_winprob={row['true_winprob']}  "
                  f"vs. Modell win_prob_model_p0={row['win_prob_model_p0']:.4f}")
            print(f"    Konsistenz-Anker (b) echte Befuellung: ab_value_real={row['ab_value_real_refill']}  "
                  f"actual_winner={row['actual_winner']}  Vorzeichen stimmt? {row['anchor_sign_match_actual_winner']}")

    usable = [s for s in per_state if s["k_valid"] >= 2 and s["true_winprob"] is not None]
    n_insufficient = len(per_state) - len(usable)

    result = {
        "pth_path": pth_path, "n_states": len(per_state), "n_usable_states": len(usable),
        "n_insufficient_refills": n_insufficient,
        "n_anchor_dome_ok": sum(1 for s in per_state if s["anchor_dome_grids_ok"]),
        "n_anchor_sign_checked": sum(1 for s in per_state if s["anchor_sign_match_actual_winner"] is not None),
        "n_anchor_sign_match": sum(1 for s in per_state if s["anchor_sign_match_actual_winner"] is True),
        "per_state": per_state,
    }

    if smoke or len(usable) < 3:
        result["regression_skipped"] = "smoke-Modus oder zu wenige verwertbare Zustaende -- keine Regression."
        return result

    true_winprob = np.array([s["true_winprob"] for s in usable])
    win_prob_model = np.array([s["win_prob_model_p0"] for s in usable])
    true_margin = np.array([s["true_margin"] for s in usable])
    margin_model = np.array([s["margin_model_p0"] for s in usable])
    k_arr = np.array([float(s["k_valid"]) for s in usable])
    var_k_ab = np.array([s["var_k_ab_p0"] for s in usable])

    slope_v, intercept_v, r2_v, n_v = ols_slope_r2(true_winprob.tolist(), win_prob_model.tolist())
    slope_p, intercept_p, r2_p, n_p = ols_slope_r2(true_margin.tolist(), margin_model.tolist())

    # Messgroesse 3: R²_max vs. realisierter Modell-R² (Sieg- UND Margen-Skala).
    r2_max_win = r2_max_win_scale(true_winprob, k_arr)
    r2_max_margin = r2_max_margin_scale(true_margin, var_k_ab)

    win_pred_expanded, win_target_expanded = [], []
    margin_pred_expanded, margin_target_expanded = [], []
    for s in usable:
        for ab in s["refill_ab_value_p0"]:
            win_pred_expanded.append(s["win_prob_model_p0"])
            win_target_expanded.append(1.0 if ab > 0 else (0.5 if ab == 0 else 0.0))
            margin_pred_expanded.append(s["margin_model_p0"])
            margin_target_expanded.append(ab)

    model_r2_win_vs_refills = r2_fixed(win_pred_expanded, win_target_expanded)
    model_r2_win_vs_expected = r2_fixed(win_prob_model, true_winprob)
    model_r2_margin_vs_refills = r2_fixed(margin_pred_expanded, margin_target_expanded)
    model_r2_margin_vs_expected = r2_fixed(margin_model, true_margin)

    bootstrap = bootstrap_r2_max(usable, n_bootstrap, seed=seed + 700000)

    result.update({
        "value_head": {"slope": slope_v, "intercept": intercept_v, "r2": r2_v, "n": n_v},
        "points_head": {"slope": slope_p, "intercept": intercept_p, "r2": r2_p, "n": n_p},
        "r2_max": {"win_scale": r2_max_win, "margin_scale": r2_max_margin},
        "model_r2_realized": {
            "win_scale_vs_individual_refills": model_r2_win_vs_refills,
            "win_scale_vs_expected": model_r2_win_vs_expected,
            "margin_scale_vs_individual_refills": model_r2_margin_vs_refills,
            "margin_scale_vs_expected": model_r2_margin_vs_expected,
        },
        "r2_max_bootstrap": bootstrap,
        "gap_luft_nach_oben": {
            "win_scale": (r2_max_win - model_r2_win_vs_expected) if model_r2_win_vs_expected is not None else None,
            "margin_scale": (r2_max_margin - model_r2_margin_vs_expected) if model_r2_margin_vs_expected is not None else None,
        },
    })
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=[
        "models/alphazero_v19_2d_best.pth",  # primaer (Champion)
        "models/alphazero_v18_best.pth", "models/alphazero_v19_best.pth",  # sekundaer
    ], help="Torch-Checkpoints (.pth) -- einheitlicher Messpfad fuer alle Modelle")
    ap.add_argument("--model-path-for-api", default="models/alphazero_v18_best.onnx",
                     help="beliebiger gueltiger ONNX-Pfad, den net_search_state_json laden MUSS (API-Zwang) -- "
                          "fuer Runde-5-Zustaende inhaltlich nie benutzt (round5.rs-Kurzschluss)")
    ap.add_argument("--sims", type=int, default=400)
    ap.add_argument("--c-puct", type=float, default=1.5)
    ap.add_argument("--n-states", type=int, default=24)
    ap.add_argument("--k-refills", type=int, default=16)
    ap.add_argument("--data-glob", default="data/selfplay_v18_*.pkl")
    ap.add_argument("--state-seed", type=int, default=20260803)
    ap.add_argument("--n-bootstrap", type=int, default=1000)
    ap.add_argument("--out", default="evaluations/r4_value_calibration_result.json")
    ap.add_argument("--smoke", action="store_true",
                     help="Rauchtest: 2 Zustaende x 3 Refills x NUR das erste Modell, keine Regression.")
    args = ap.parse_args()

    n_states = 2 if args.smoke else args.n_states
    k_refills = 3 if args.smoke else args.k_refills
    models = args.models[:1] if args.smoke else args.models

    print(f"[r4_value_calibration] {'RAUCHTEST' if args.smoke else 'VOLLER LAUF'}: "
          f"n_states={n_states} k_refills={k_refills} models={models}")
    print(f"[r4_value_calibration] Substrat-Auswahl aus {args.data_glob!r} (seed={args.state_seed}) ...")
    chosen_states, sel_stats = select_states(args.data_glob, n_states, args.state_seed)
    print(f"[r4_value_calibration] Auswahl-Statistik: {json.dumps(sel_stats, indent=2, ensure_ascii=False)}")

    model_results = {}
    for pth_path in models:
        print(f"\n=== Modell: {pth_path} ===")
        measured = measure_model(pth_path, chosen_states, k_refills, args.model_path_for_api,
                                  args.sims, args.c_puct, args.state_seed, args.n_bootstrap, smoke=args.smoke)
        if not args.smoke and "value_head" in measured:
            print(f"  VALUE-Kopf:  Steigung={measured['value_head']['slope']} R2={measured['value_head']['r2']}")
            print(f"  PUNKTE-Kopf: Steigung={measured['points_head']['slope']} R2={measured['points_head']['r2']}")
            print(f"  R2_max: {measured['r2_max']}")
            print(f"  Modell-R2 (realisiert): {measured['model_r2_realized']}")
            print(f"  Luft nach oben: {measured['gap_luft_nach_oben']}")
        model_results[pth_path] = measured

    if args.smoke:
        print("\n[r4_value_calibration] RAUCHTEST beendet -- kein voller Lauf, kein Ergebnis-Schreiben.")
        return

    summary = {
        "data_glob": args.data_glob, "n_states": len(chosen_states), "k_refills": k_refills,
        "sims": args.sims, "c_puct": args.c_puct, "state_seed": args.state_seed,
        "n_bootstrap": args.n_bootstrap, "selection_stats": sel_stats,
        "models": {k: {kk: vv for kk, vv in v.items() if kk != "per_state"} for k, v in model_results.items()},
    }
    print("\n=== ZUSAMMENFASSUNG ===")
    print(json.dumps(summary, indent=2, ensure_ascii=True, default=str))

    result = {"summary": summary, "per_model": model_results}
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print(f"\nErgebnis geschrieben nach {args.out}")


if __name__ == "__main__":
    main()
