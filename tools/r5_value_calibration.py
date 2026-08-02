# -*- coding: utf-8 -*-
"""
Mosaic-AI -- Runde-5-Value-/Punkte-Kopf-Kalibrierung gegen exakte Ground Truth
(Task #27, 2026-08-02)
============================================================================

Siehe `evaluations/PREREG_r5_value_calibration.md` fuer die volle Herleitung
-- hier nur die Kurzfassung der Mechanik:

1. GROUND TRUTH je (Zustand, Wertungsplatten-Kombination): `round5.rs`
   (exakte Alpha-Beta-Suche, Full-Information-Endspiel ab Runde 5) wird
   automatisch von `net_search_state_json` aufgerufen, sobald
   `round_number>=5 and phase==drafting` -- unabhaengig vom `model_path`
   (nie benutzt, reiner API-Zwang, braucht keine lebende `PyGame`-Instanz,
   rekonstruiert selbst per `json_to_state`). `moves[ai_action]["ab_value"]`
   ist die rohe, EXAKTE Punkte-Marge (eigen-gegner) des Zustands unter
   optimalem Folgespiel.

2. MODELL-MEINUNG je (Zustand, Kombination): fuer Runde-5-Zustaende
   ueberspringt `net_search_state_json`/`ai_debug_net_json` das Netz komplett
   -- der rohe Kopf-Forward-Pass kommt stattdessen EINHEITLICH ueber den
   TORCH-Pfad (Koordinator-Gate-Feedback, ersetzt den fruehren ONNX-
   Zwei-Wege-Ansatz): `engine/py/neural_net.py::build_model_from_checkpoint`
   laedt das `.pth`-Checkpoint direkt (`model_state`-Key), `state_to_tensor`/
   `state_to_planes` bauen die Eingabe-Tensoren DIREKT aus einem
   State-Dict -- KEINE lebende `PyGame`-Instanz noetig (anders als der
   verworfene `PyGame.features()`-Weg), funktioniert identisch fuer alle drei
   Modelle (`v18_best`/`v19_best`/`v19_2d_best`), da `build_model_from_
   checkpoint` den Encoder-Typ selbst aus dem `state_dict` ableitet
   (`encoder_from_state_dict`) und `state_to_planes` (Rust-Parity laut
   Koordinator 60/60 geprueft) den Planes-Puffer liefert, der dem Netz-Pfad
   bisher fehlte. Damit faellt die fruehere `v19_2d_best`-Vorbedingung
   (fehlender `features_for_net`-Python-Export) komplett weg, UND weil keine
   lebende Instanz mehr noetig ist, koennen wieder ECHTE `frozen_eval_set`-
   Zustaende direkt verwendet werden (kein Autoplay-Umweg mehr noetig).

3. EMPIRISCHE PUNKTE->SIEG-KENNLINIE: logistische Regression (reines NumPy,
   kein scipy/sklearn) aus `frozen_eval_set.pkl`s Runde-5-Records: X =
   `ab_value` des Records mit SEINER eigenen `scoring_tile_ids` (Ground-
   Truth-Formel von oben, EIN Alpha-Beta-Aufruf je Record), Y = tatsaechlicher
   Spielausgang (`rec["winner"]`). UNABHAENGIG von
   `mcts::normalize_score`/`VALUE_SCALE` (zirkularitaetsfrei, siehe PREREG).

4. UMRECHNUNG true_delta_pts -> erwartetes Δ-Sieg% -- LOKALE ABLEITUNG (Gate-
   Fix #1, ersetzt die volle Kennlinien-Differenz): `expected_delta_winprob =
   b * P_ref * (1-P_ref) * true_delta_pts`, `P_ref = curve_win_prob(a, b,
   ab_ref)`. Grund: Runde 5 ist (fast) ein Full-Information-Endspiel, die
   Kennlinie daher sehr steil (im Rauchtest: McFadden-R²~1.0) -- die VOLLE
   Kennlinien-Differenz `curve(ab_t) - curve(ab_ref)` saettigt fuer
   deutlich entschiedene Stellungen auf ~0 UNABHAENGIG von `true_delta_pts`
   (zwei separat gesaettigte Sigmoid-Auswertungen subtrahiert), was die
   OLS-Regression bei kleinen Stichproben oft auf `std(x)=0` (entartet)
   kollabieren laesst -- siehe erster Rauchtest-Lauf, 6/6 Paare exakt 0.
   Die LOKALE Ableitung (Tangente an der Kennlinie bei `ab_ref`) bleibt fuer
   JEDE Grosse von `true_delta_pts` linear proportional (keine zweite
   Saettigung durch die Differenzbildung) und ist die Standard-Linearisierung
   fuer "erwarteter Effekt einer kleinen/moderaten Verschiebung" -- bleibt an
   entschiedenen Stellungen weiterhin klein (korrekt: dort AENDERT ein
   Wertungsplatten-Tausch die Siegwahrscheinlichkeit tatsaechlich kaum), aber
   springt nicht mehr durch zwei unabhaengige Saettigungen auf exakt 0.

5. REGRESSION: Modell-Delta (Value-Kopf-Δ-Winprob, Punkte-Kopf-Δ-Winprob ueber
   dieselbe Kennlinie) auf das kennlinien-umgerechnete `true_delta_pts` -- OLS
   mit Achsenabschnitt, Steigung + R² je Modell/Kopf.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import os
import pickle
import sys

import numpy as np
import torch

import mosaic_rust

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "engine", "py"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scoring_tile_sensitivity as sts  # noqa: E402  (all_valid_combos/pick_representative_combos, Memory feedback_check_existing_tools_first)
from neural_net import build_model_from_checkpoint, state_to_tensor, state_to_planes  # noqa: E402


# ── Logistische Regression (reines NumPy, IRLS/Newton-Raphson) ─────────────

def fit_logistic(x: np.ndarray, y: np.ndarray, max_iter: int = 50, tol: float = 1e-9):
    """P(y=1) = sigmoid(a + b*x). Gibt (a, b, mcfadden_r2, n_iter) zurueck.
    Reines Newton-Raphson (IRLS) -- kein scipy/sklearn (Projektkonvention)."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    n = len(x)
    X = np.column_stack([np.ones(n), x])
    beta = np.zeros(2)
    it = 0
    for it in range(max_iter):
        eta = np.clip(X @ beta, -35.0, 35.0)  # exp-Overflow-Schutz
        p = 1.0 / (1.0 + np.exp(-eta))
        w = np.clip(p * (1.0 - p), 1e-9, None)
        grad = X.T @ (y - p)
        XtWX = X.T @ (X * w[:, None])
        try:
            step = np.linalg.solve(XtWX, grad)
        except np.linalg.LinAlgError:
            break
        beta_new = beta + step
        if np.max(np.abs(beta_new - beta)) < tol:
            beta = beta_new
            break
        beta = beta_new

    a, b = beta[0], beta[1]
    eta = np.clip(X @ beta, -35.0, 35.0)
    p = 1.0 / (1.0 + np.exp(-eta))
    p = np.clip(p, 1e-9, 1 - 1e-9)
    loglik_model = float(np.sum(y * np.log(p) + (1 - y) * np.log(1 - p)))
    ybar = float(np.mean(y))
    ybar = min(max(ybar, 1e-9), 1 - 1e-9)
    loglik_null = float(n * (ybar * math.log(ybar) + (1 - ybar) * math.log(1 - ybar)))
    mcfadden_r2 = 1.0 - loglik_model / loglik_null if loglik_null != 0 else float("nan")
    return float(a), float(b), mcfadden_r2, it + 1


def curve_win_prob(a: float, b: float, margin: float) -> float:
    eta = max(-35.0, min(35.0, a + b * margin))
    return 1.0 / (1.0 + math.exp(-eta))


def local_expected_delta_winprob(a: float, b: float, ab_ref: float, true_delta_pts: float) -> float:
    """Gate-Fix #1: lokale Ableitung statt gesaettigter Kennlinien-Differenz
    (siehe Moduldoku Punkt 4)."""
    p_ref = curve_win_prob(a, b, ab_ref)
    return b * p_ref * (1.0 - p_ref) * true_delta_pts


def ols_slope_r2(x: list, y: list):
    """Einfache OLS-Regression y = a + b*x MIT Achsenabschnitt. Gibt
    (slope, intercept, r2, n) zurueck (Nones bei zu wenig/entarteten Daten)."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    n = len(x)
    if n < 3 or np.std(x) == 0:
        return None, None, None, n
    xbar, ybar = x.mean(), y.mean()
    sxx = np.sum((x - xbar) ** 2)
    sxy = np.sum((x - xbar) * (y - ybar))
    slope = sxy / sxx
    intercept = ybar - slope * xbar
    yhat = intercept + slope * x
    ss_res = np.sum((y - yhat) ** 2)
    ss_tot = np.sum((y - ybar) ** 2)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return float(slope), float(intercept), float(r2), n


# ── Ground Truth (round5.rs via net_search_state_json) ─────────────────────

def ab_value_for_combo(state: dict, combo, model_path_for_api: str, sims: int, c_puct: float, seed: int):
    """Exakte Punkte-Marge (eigen-gegner) via `round5.rs`s Alpha-Beta-
    Kurzschluss in `net_search_state_json` (siehe Moduldoku oben).
    `model_path_for_api` wird geladen, aber fuer Runde-5-Zustaende nie
    benutzt -- reiner API-Zwang, ein beliebiger gueltiger ONNX-Pfad genuegt."""
    s = dict(state)
    s["scoring_tile_ids"] = list(combo)
    out = json.loads(mosaic_rust.net_search_state_json(json.dumps(s), model_path_for_api, sims, c_puct, seed))
    ai_action = out.get("ai_action")
    moves = out.get("moves") or []
    if ai_action is None or not moves or ai_action >= len(moves):
        return None
    return moves[ai_action].get("ab_value")


# ── Modell-Forward-Pass (torch, einheitlich fuer alle 3 Modelle) ───────────

def load_torch_model(pth_path: str):
    ckpt = torch.load(pth_path, map_location="cpu", weights_only=False)
    model, encoder = build_model_from_checkpoint(ckpt)
    model.eval()
    return model, encoder


def raw_value_points_torch(model, encoder: str, state: dict, combo) -> tuple:
    """(raw_value, raw_points), beide tanh-Skala [-1,1], fuer `state` mit
    `combo` als Wertungsplatten -- direkter Torch-Forward-Pass, KEINE lebende
    `PyGame`-Instanz noetig (`state_to_tensor`/`state_to_planes` arbeiten
    direkt auf dem Dict)."""
    s = copy.deepcopy(state)
    s["scoring_tile_ids"] = list(combo)
    x_flat = state_to_tensor(s).unsqueeze(0)
    with torch.no_grad():
        if encoder == "2d":
            x_planes = state_to_planes(s).unsqueeze(0)
            out = model(x_planes, x_flat)
        else:
            out = model(x_flat)
    raw_value = float(out[1].squeeze().item())
    raw_points = float(out[3].squeeze().item())
    return raw_value, raw_points


def value_to_win_prob(v: float) -> float:
    return (v + 1.0) / 2.0


def points_to_pts(p: float) -> float:
    p = max(-0.999, min(0.999, p))
    return 50.0 * math.atanh(p)


# ── Positions-Auswahl (frozen_eval_set, Runde-5-Drafting-Records) ──────────

def select_round5_states(records, n_states, rng_seed=7):
    pool = [(i, r) for i, r in enumerate(records) if r["state"]["round"] == 5 and r["state"]["phase"] == "drafting"]
    import random
    rng = random.Random(rng_seed)
    rng.shuffle(pool)
    return pool[:n_states]


def fit_curve(records, model_path_for_api: str, sims: int, c_puct: float, n_states: int, seed_base: int = 500000):
    """Baut die empirische Punkte->Sieg-Kennlinie aus bis zu `n_states`
    Runde-5-Records (Original-`scoring_tile_ids`, EIN Alpha-Beta-Aufruf je
    Record, KEINE lebende Instanz noetig)."""
    pool = [r for r in records if r["state"]["round"] == 5 and r["state"]["phase"] == "drafting" and r.get("completed")]
    pool = pool[:n_states]
    xs, ys = [], []
    for i, rec in enumerate(pool):
        state = rec["state"]
        ab = ab_value_for_combo(state, state["scoring_tile_ids"], model_path_for_api, sims, c_puct, seed_base + i)
        if ab is None:
            continue
        winner = rec.get("winner")
        cur = state["current_player"]
        xs.append(ab)
        ys.append(1.0 if winner == cur else 0.0)
    if len(xs) < 10:
        raise RuntimeError(f"Zu wenige verwertbare Kennlinien-Punkte ({len(xs)}) -- Kennlinie nicht belastbar.")
    a, b, mcfadden_r2, n_iter = fit_logistic(np.array(xs), np.array(ys))
    return {
        "n_points": len(xs), "a": a, "b": b, "mcfadden_r2": mcfadden_r2, "n_iter": n_iter,
        "x_range": [min(xs), max(xs)], "y_mean": float(np.mean(ys)),
    }


def measure_model(pth_path: str, states: list, combos: list, curve: dict,
                   model_path_for_api: str, sims: int, c_puct: float, seed: int):
    model, encoder = load_torch_model(pth_path)
    value_true, value_model, points_true, points_model = [], [], [], []
    per_pair_rows = []
    for si, (record_index, rec) in enumerate(states):
        state = rec["state"]
        ref_combo = tuple(sorted(state["scoring_tile_ids"]))

        ab_ref = ab_value_for_combo(state, ref_combo, model_path_for_api, sims, c_puct, seed + si)
        raw_value_ref, raw_points_ref = raw_value_points_torch(model, encoder, state, ref_combo)
        if ab_ref is None:
            continue
        win_prob_ref = value_to_win_prob(raw_value_ref)
        pts_ref = points_to_pts(raw_points_ref)

        n_compared = 0
        for combo in combos:
            if tuple(sorted(combo)) == ref_combo:
                continue
            ab_t = ab_value_for_combo(state, combo, model_path_for_api, sims, c_puct, seed + si)
            if ab_t is None:
                continue
            raw_value_t, raw_points_t = raw_value_points_torch(model, encoder, state, combo)
            win_prob_t = value_to_win_prob(raw_value_t)
            pts_t = points_to_pts(raw_points_t)

            true_delta_pts = ab_t - ab_ref
            expected_delta_winprob = local_expected_delta_winprob(curve["a"], curve["b"], ab_ref, true_delta_pts)

            model_value_delta = win_prob_t - win_prob_ref
            model_points_delta_pts = pts_t - pts_ref
            model_points_delta_winprob = local_expected_delta_winprob(
                curve["a"], curve["b"], ab_ref, model_points_delta_pts
            )

            value_true.append(expected_delta_winprob)
            value_model.append(model_value_delta)
            points_true.append(expected_delta_winprob)
            points_model.append(model_points_delta_winprob)
            per_pair_rows.append({
                "state_index_in_eval_set": record_index, "combo": list(combo),
                "ab_value_ref": ab_ref, "ab_value_treatment": ab_t, "true_delta_pts": true_delta_pts,
                "expected_delta_winprob": expected_delta_winprob,
                "model_value_delta_winprob": model_value_delta,
                "model_points_delta_pts": model_points_delta_pts,
                "model_points_delta_winprob": model_points_delta_winprob,
            })
            n_compared += 1
        print(f"  Zustand {si} (eval_set idx={record_index}): ab_ref={ab_ref:.2f} win_prob_ref={win_prob_ref:.3f} "
              f"-- {n_compared} Kombinationen verglichen")

    slope_v, intercept_v, r2_v, n_v = ols_slope_r2(value_true, value_model)
    slope_p, intercept_p, r2_p, n_p = ols_slope_r2(points_true, points_model)
    return {
        "value_head": {"slope": slope_v, "intercept": intercept_v, "r2": r2_v, "n": n_v},
        "points_head": {"slope": slope_p, "intercept": intercept_p, "r2": r2_p, "n": n_p},
        "per_pair": per_pair_rows,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval-set", default="evaluations/frozen_eval_set.pkl")
    ap.add_argument("--models", nargs="+", default=[
        "models/alphazero_v18_best.pth", "models/alphazero_v19_best.pth", "models/alphazero_v19_2d_best.pth",
    ], help="Torch-Checkpoints (.pth) -- einheitlicher Messpfad fuer alle Modelle, siehe Moduldoku Punkt 2")
    ap.add_argument("--model-path-for-api", default="models/alphazero_v18_best.onnx",
                     help="beliebiger gueltiger ONNX-Pfad, den net_search_state_json laden MUSS (API-Zwang) -- "
                          "fuer Runde-5-Zustaende inhaltlich nie benutzt (round5.rs-Kurzschluss)")
    ap.add_argument("--sims", type=int, default=400)
    ap.add_argument("--c-puct", type=float, default=1.5)
    ap.add_argument("--n-states", type=int, default=24)
    ap.add_argument("--n-combos", type=int, default=6)
    ap.add_argument("--curve-n-states", type=int, default=233)
    ap.add_argument("--out", default="evaluations/r5_value_calibration_result.json")
    ap.add_argument("--seed", type=int, default=1000)
    args = ap.parse_args()

    with open(args.eval_set, "rb") as f:
        data = pickle.load(f)
    records = data["records"]
    n_r5 = sum(1 for r in records if r["state"]["round"] == 5 and r["state"]["phase"] == "drafting")
    print(f"[r5_value_calibration] {n_r5} Runde-5-Drafting-Records im eval-set verfuegbar.")

    states = select_round5_states(records, args.n_states)
    print(f"[r5_value_calibration] {len(states)} Zustaende fuer die Hauptmessung gewaehlt.")
    combos = sts.pick_representative_combos(args.n_combos)
    print(f"[r5_value_calibration] {len(combos)} Kombinationen: {combos}")

    print("[r5_value_calibration] Kennlinie wird gefittet (frozen_eval_set) ...")
    curve = fit_curve(records, args.model_path_for_api, args.sims, args.c_puct, args.curve_n_states,
                       seed_base=args.seed + 500000)
    print(f"[r5_value_calibration] Kennlinie: a={curve['a']:.5f} b={curve['b']:.5f} "
          f"mcfadden_r2={curve['mcfadden_r2']:.3f} n={curve['n_points']} y_mean={curve['y_mean']:.3f}")

    model_results = {}
    for pth_path in args.models:
        print(f"\n=== Modell: {pth_path} ===")
        measured = measure_model(pth_path, states, combos, curve, args.model_path_for_api,
                                  args.sims, args.c_puct, args.seed)
        print(f"  VALUE-Kopf:  Steigung={measured['value_head']['slope']} R2={measured['value_head']['r2']} n={measured['value_head']['n']}")
        print(f"  PUNKTE-Kopf: Steigung={measured['points_head']['slope']} R2={measured['points_head']['r2']} n={measured['points_head']['n']}")

        model_results[pth_path] = {
            "n_state_combo_pairs": len(measured["per_pair"]),
            "value_head": measured["value_head"], "points_head": measured["points_head"],
            "per_pair": measured["per_pair"],
        }

    summary = {
        "eval_set": args.eval_set, "n_states": len(states), "n_combos": args.n_combos,
        "sims": args.sims, "c_puct": args.c_puct, "curve_n_states": args.curve_n_states,
        "curve": curve,
        "models": {k: {kk: vv for kk, vv in v.items() if kk != "per_pair"} for k, v in model_results.items()},
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
