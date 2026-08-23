# -*- coding: utf-8 -*-
"""
Vierer-Vergleich R5-Loeser-Kalibrierung (Auftrag 2026-08-23,
`evaluations/PREREG_r5_solver_split.md` par.3d): welcher von vier
vorhandenen "Koepfen" ordnet Runde-5-STARTzustaende am besten nach der
EXAKTEN Solver-Marge?

Vier Koepfe, alle auf DENSELBEN Zustaenden (siehe par.3d):
  (1) endgame_margin des Champions (models/alphazero_v21_2d_brierbest.*)
  (2) points MINUS opp_points desselben Modells
  (3) E_k-Plattenpunkte aus der Ownership-Karte von v21-b18
      (models/alphazero_v21-b18_best.*), Konjunktionspfad PFLICHT
  (4) Value-Kopf des Champions (WDL-Erwartungswert)

Grundwahrheit: der exakte Solver-Wurzelwert (`ab_value`, Punkte-Marge
eigen-gegner) ueber denselben Einstieg wie `tools/r5_value_calibration.py`
(`mosaic_rust.net_search_state_json` -> `round5.rs`-Kurzschluss fuer
Runde-5-Zustaende, `moves[ai_action]["ab_value"]`) -- siehe dortige
Moduldoku fuer die volle Herleitung, hier nur referenziert, nicht neu
geschrieben (Memory `feedback_check_existing_tools_first`).

METHODIK -- Uebertragung des "r5_value_calibration-Musters" auf einen
POPULATIONS- statt einen Kombinations-Paar-Vergleich (par.3d schreibt keine
Formel vor; diese Uebertragung ist eine EIGENE, hier markierte Konstruktion):

  r5_value_calibration.py vergleicht INNERHALB EINES Zustands Modell-Delta
  gegen Solver-Delta ueber mehrere Wertungsplatten-Kombinationen. Hier gibt
  es keine Kombinations-Variation -- jeder der ~200 Zustaende traegt seine
  EIGENEN, echten `scoring_tile_ids`. Die Kennlinien-Idee wird stattdessen
  QUERSCHNITTLICH uebertragen:

  1. Eine empirische logistische Kennlinie `P(win) = sigmoid(a + b*ab_value)`
     wird aus DENSELBEN ~200 Zustaenden gefittet (`ab_value_i`, echter
     Spielausgang `winner_i`) -- reine Wiederverwendung von
     `tools/r5_value_calibration.py::fit_logistic`/`curve_win_prob`.
  2. Kalibrierungs-STEIGUNG je Kopf (`tools/r5_value_calibration.py::
     ols_slope_r2`, Wiederverwendung):
       - Kopf 1 (endgame_margin) und Kopf 4 (value): beide sind tanh-
         skalierte "Kopf sagt 2*P(win)-1 voraus"-Ausgaenge (Kopf 1 GEPRUEFT
         am Code: `train.py` --endgame-head-Hilfetext + `neural_net.py`
         Modulkommentar -- Ziel ist `root_q` in [0,1]-Skala, Tanh-Remap
         `2*root_q-1`; `root_q` fuer Runde-5-Zustaende ist selbst
         `((ab_value/VALUE_SCALE).tanh()+1)/2`, `net_mcts.rs:5126/5139`).
         Regressiert wird der ROHE Kopf-Ausgang (y) gegen `2*curve_win_prob(
         a,b,ab_value_i)-1` (x, die kennlinien-implizite tanh-Erwartung) --
         Steigung ~1 = Kopf reproduziert die Kennlinie.
       - Kopf 2 (points-opp_points) und Kopf 3 (E_k-Marge): beide sind
         bereits in PUNKTE-Einheiten, direkt vergleichbar mit `ab_value`.
         Regressiert wird der Kopf-Wert (y, Punkte) direkt gegen `ab_value_i`
         (x, Punkte) -- Steigung ~1 = Kopf trifft die Punkte-Marge 1:1.
  3. Fuer den Vorzeichentest (gepaarte Differenz je Zustand) werden ALLE
     vier Koepfe auf eine GEMEINSAME Skala projiziert (P(win) via derselben
     Kennlinie fuer Kopf 2/3; nativ fuer Kopf 1/4) und der Fehler gegen
     `P_solver_i = curve_win_prob(a,b,ab_value_i)` gebildet:
     `e_head_i = |P_head_i - P_solver_i|`. Vorzeichentest (exakter
     Zwei-Seiten-Binomialtest, reines Python/`math.comb`, keine
     scipy-Abhaengigkeit -- Projekt-Konvention) auf `e_kandidat_i <
     e_value_i` je Kandidat gegen den Value-Kopf, auf der k1-aktiven
     Teilmenge (par.3d-Lesart).

Kendall-Tau (Rangkorrelation) ist skaleninvariant -- dafuer wird je Kopf
direkt der NATIVE Rohwert gegen `ab_value_i` rangkorreliert (Kopf 1/4:
roher tanh-Ausgang; Kopf 2/3: Punkte-Marge); Wiederverwendung von
`tools/oracle_metrics.py::_kendall_tau_a` (Memory
`feedback_check_existing_tools_first`).

Stichprobe (par.3d): ~200 Runde-5-STARTzustaende (per Spiel der ERSTE
Record mit `round==5 and phase=="drafting", completed==True`) aus
`data/seed_corpus/*.pkl` (v21-seedk1, k1-angereichert) UND
`data/selfplay_v20wdl_*.pkl` (aeltere, nicht k1-angereicherte Korpus-Aera)
-- GEPOOLT (eigene, markierte Entscheidung: die Zustaende selbst sind reine
Brettpositionen, die vom Solver/den Koepfen unabhaengig von der Korpus-
Erzeugungs-Aera bewertet werden; das Pooling vergroessert nur den Pool fuer
die geforderte k1-aktive Teilmenge >=60), stratifiziert nach
Punktedifferenz-Terzilen (Proxy: `score[current_player]-score[other]` am
Runde-5-Start, EIGENE markierte Wahl -- par.3d nennt kein anderes Mass) und
k1-Plattenlage (`scoring_tile_ids` enthaelt Tile-ID 1, "Vertikale Reihen",
K1_TILE_ID aus `tools/probes/column_build_structural_probe.py:249`).

Aufruf:
    python tools/probes/r5_four_head_comparison.py --out evaluations/r5_four_head_comparison.json
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import pickle
import random
import sys
import time
from collections import defaultdict

import numpy as np
import torch

import mosaic_rust

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "engine", "py"))

from neural_net import build_model_from_checkpoint, state_to_tensor, state_to_planes  # noqa: E402
from r5_value_calibration import (  # noqa: E402
    fit_logistic, curve_win_prob, ols_slope_r2,
)
from oracle_metrics import _kendall_tau_a as kendall_tau_a  # noqa: E402

K1_TILE_ID = 1  # ABGELESEN aus tools/probes/column_build_structural_probe.py:249 ("Vertikale Reihen")


# ── Modell-Forward-Pass (Torch, identisches Muster zu r5_value_calibration.py) ──

def load_torch_model(pth_path: str):
    ckpt = torch.load(pth_path, map_location="cpu", weights_only=False)
    model, encoder = build_model_from_checkpoint(ckpt)
    model.eval()
    return model, encoder


def output_names_for_model(model) -> list:
    """Repliziert EXAKT die Anhaenge-Reihenfolge aus `neural_net.py`s
    `MosaicNet.forward`/`Mosaic2DNet.forward` (dort Zeilen ~2511-2533 bzw.
    ~2770-2788, am Code gelesen 2026-08-23) -- keine Index-Arithmetik,
    sondern Namens-Zuordnung, robust gegen die optionalen Koepfe."""
    names = ["policy", "value", "moon", "points", "ownership"]
    if getattr(model, "points_dist_bins", 0) > 0:
        names.append("points_logits")
    if getattr(model, "value_head_variant", "tanh") == "wdl":
        names.append("value_wdl_logits")
    if getattr(model, "has_opp_points_head", False):
        names.append("opp_points")
    if getattr(model, "has_endgame_head", False):
        names.append("endgame_margin")
    return names


def forward_raw(model, encoder: str, state: dict) -> dict:
    x_flat = state_to_tensor(state).unsqueeze(0)
    with torch.no_grad():
        if encoder == "2d":
            out = model(state_to_planes(state).unsqueeze(0), x_flat)
        else:
            out = model(x_flat)
    names = output_names_for_model(model)
    if len(names) != len(out):
        raise RuntimeError(
            f"output_names_for_model liefert {len(names)} Namen, Modell-Forward {len(out)} Tensoren "
            f"-- Kopf-Erkennung ist inkonsistent zum tatsaechlichen Graphen."
        )
    return {n: out[i] for i, n in enumerate(names)}


def points_to_pts(p: float) -> float:
    p = max(-0.999, min(0.999, float(p)))
    return 50.0 * math.atanh(p)


# ── Ground Truth (round5.rs via net_search_state_json, wie r5_value_calibration.py) ──

def ab_value_for_state(state: dict, model_path_for_api: str, sims: int, c_puct: float, seed: int):
    out = json.loads(mosaic_rust.net_search_state_json(json.dumps(state), model_path_for_api, sims, c_puct, seed))
    ai_action = out.get("ai_action")
    moves = out.get("moves") or []
    if ai_action is None or not moves or ai_action >= len(moves):
        return None
    return moves[ai_action].get("ab_value")


# ── Kopf 3: E_k-Plattenpunkte ueber die neue Rust-Bruecke (Aufgabe 2026-08-23) ──

def ek_margin_for_state(state: dict, ownership_raw: list) -> tuple:
    """`mosaic_rust.ownership_ek_plate_points_json` (neu, `engine/src/lib.rs`,
    diese Aufgabe) -- reine Formel-Auswertung von
    `scoring::expected_plate_points_conj` auf einem EXTERN (Torch)
    berechneten rohen Ownership-Kopf-Ausgang, KEIN Produktform-Rueckfall
    (harter Fehler bei <140 Breite, siehe Rust-Funktionsdoku). Gibt
    (e_k_margin_eigen_minus_gegner, e_k_own_total, e_k_opp_total,
    used_conjunction_path=True) zurueck -- `used_conjunction_path` ist
    IMMER True, weil die Funktion sonst hart fehlschlaegt (Beleg fuer den
    Bericht: der Aufruf selbst ist der Beweis, dass der Konjunktionspfad
    griff, nicht der Produktform-Rueckfall)."""
    raw = mosaic_rust.ownership_ek_plate_points_json(json.dumps(state), list(ownership_raw))
    out = json.loads(raw)
    cur = out["current_player"]
    other = 1 - cur
    e_own = sum(out[f"e_k_player{cur}"])
    e_opp = sum(out[f"e_k_player{other}"])
    return e_own - e_opp, e_own, e_opp


# ── Stichprobe: Runde-5-Startzustaende aus fertigen Partien ─────────────────

def list_corpus_files(pattern: str, n_files: int, rng: random.Random) -> list:
    files = sorted(glob.glob(pattern))
    if n_files >= len(files):
        return files
    # deterministisch ueber den ganzen Lauf gestreut (Stride), nicht nur die
    # ersten N Dateien -- vermeidet eine systematische Verzerrung auf den
    # Beginn der jeweiligen Korpus-Generierung.
    stride = len(files) / n_files
    idxs = sorted({int(i * stride) for i in range(n_files)})
    return [files[i] for i in idxs]


def round5_start_candidates_from_file(pkl_path: str, source_tag: str) -> list:
    with open(pkl_path, "rb") as f:
        recs = pickle.load(f)
    if isinstance(recs, dict) and "records" in recs:
        recs = recs["records"]
    by_game: dict = {}
    for r in recs:
        st = r.get("state")
        if st is None or st.get("round") != 5 or st.get("phase") != "drafting":
            continue
        gid = r.get("game_id")
        if gid is None:
            continue
        # erster Treffer je Spiel (Records liegen in Spielreihenfolge vor,
        # gegengeprueft 2026-08-23: `round`-Sequenz innerhalb einer game_id
        # ist monoton nicht-fallend) = Runde-5-STARTzustand.
        by_game.setdefault(gid, r)
    out = []
    for gid, r in by_game.items():
        if not r.get("completed", False):
            continue
        st = r["state"]
        cur = st["current_player"]
        other = 1 - cur
        point_diff = st["players"][cur]["score"] - st["players"][other]["score"]
        k1_active = K1_TILE_ID in (st.get("scoring_tile_ids") or [])
        out.append({
            "source": source_tag, "file": os.path.basename(pkl_path), "game_id": gid,
            "state": st, "winner": r.get("winner"), "point_diff_proxy": point_diff,
            "k1_active": k1_active,
        })
    return out


def stratified_sample(pool: list, n_total: int, n_k1_min: int, rng: random.Random) -> list:
    diffs = sorted(c["point_diff_proxy"] for c in pool)
    n = len(diffs)
    t1 = diffs[n // 3]
    t2 = diffs[(2 * n) // 3]

    def tercile(d):
        if d <= t1:
            return 0
        if d <= t2:
            return 1
        return 2

    strata: dict = defaultdict(list)
    for c in pool:
        strata[(tercile(c["point_diff_proxy"]), c["k1_active"])].append(c)
    for key in strata:
        rng.shuffle(strata[key])

    # Ziel: n_k1_min k1-aktive (moeglichst gleich ueber die 3 Terzile),
    # Rest bis n_total aus den nicht-k1-aktiven Strata (ebenfalls moeglichst
    # gleich ueber die Terzile) -- mit Nachschub-Umlage, wenn ein Stratum zu
    # klein ist. EIGENE, hier dokumentierte Zuteilungsregel (par.3d schreibt
    # nur die beiden Mindestzahlen vor, keinen Zuteilungsalgorithmus).
    def draw_from(strata_keys, target_n):
        picked = []
        remaining_keys = list(strata_keys)
        remaining_target = target_n
        while remaining_target > 0 and remaining_keys:
            share = max(1, remaining_target // len(remaining_keys))
            progressed = False
            for key in list(remaining_keys):
                if remaining_target <= 0:
                    break
                take = min(share, len(strata[key]), remaining_target)
                if take > 0:
                    picked.extend(strata[key][:take])
                    strata[key] = strata[key][take:]
                    remaining_target -= take
                    progressed = True
                if not strata[key]:
                    remaining_keys.remove(key)
            if not progressed:
                break
        return picked

    k1_keys = [(t, True) for t in (0, 1, 2)]
    non_k1_keys = [(t, False) for t in (0, 1, 2)]
    picked_k1 = draw_from(k1_keys, n_k1_min)
    picked_non_k1 = draw_from(non_k1_keys, n_total - len(picked_k1))
    picked = picked_k1 + picked_non_k1
    # falls insgesamt noch Luecke zum Ziel (Pool zu klein): aus allem
    # Restlichen auffuellen, egal welches Stratum.
    if len(picked) < n_total:
        rest = [c for key in strata for c in strata[key]]
        rng.shuffle(rest)
        picked.extend(rest[: n_total - len(picked)])
    rng.shuffle(picked)
    return picked, {"tercile_bounds": [t1, t2]}


# ── Vorzeichentest (exakter Zwei-Seiten-Binomialtest, reines Python) ────────

def sign_test_two_sided(n_pos: int, n_neg: int):
    n = n_pos + n_neg
    if n == 0:
        return {"n_pairs_used": 0, "n_candidate_better": n_pos, "n_value_better": n_neg, "p_value": None}
    k = min(n_pos, n_neg)
    cum = sum(math.comb(n, i) for i in range(0, k + 1)) / (2.0 ** n)
    p = min(1.0, 2.0 * cum)
    return {"n_pairs_used": n, "n_candidate_better": n_pos, "n_value_better": n_neg, "p_value": p}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--champion-onnx", default="models/alphazero_v21_2d_brierbest.onnx")
    ap.add_argument("--champion-pth", default="models/alphazero_v21_2d_brierbest.pth")
    ap.add_argument("--b18-pth", default="models/alphazero_v21-b18_best.pth")
    ap.add_argument("--seed-corpus-glob", default="data/seed_corpus/selfplay_v21_seedk1_*.pkl")
    ap.add_argument("--v20wdl-glob", default="data/selfplay_v20wdl_*.pkl")
    ap.add_argument("--n-files-seed-corpus", type=int, default=45)
    ap.add_argument("--n-files-v20wdl", type=int, default=25)
    ap.add_argument("--n-total", type=int, default=200)
    ap.add_argument("--n-k1-min", type=int, default=70)
    ap.add_argument("--sims", type=int, default=400)
    ap.add_argument("--c-puct", type=float, default=1.5)
    ap.add_argument("--seed", type=int, default=20260823)
    ap.add_argument("--out", default="evaluations/r5_four_head_comparison.json")
    args = ap.parse_args()

    rng = random.Random(args.seed)

    seed_files = list_corpus_files(os.path.join(ROOT, args.seed_corpus_glob), args.n_files_seed_corpus, rng)
    v20_files = list_corpus_files(os.path.join(ROOT, args.v20wdl_glob), args.n_files_v20wdl, rng)
    print(f"[r5_four_head] {len(seed_files)} seed_corpus-Dateien, {len(v20_files)} v20wdl-Dateien geladen.")

    pool = []
    for fp in seed_files:
        pool.extend(round5_start_candidates_from_file(fp, "seed_corpus_v21_seedk1"))
    for fp in v20_files:
        pool.extend(round5_start_candidates_from_file(fp, "selfplay_v20wdl"))
    n_k1_pool = sum(1 for c in pool if c["k1_active"])
    print(f"[r5_four_head] Kandidaten-Pool: {len(pool)} Runde-5-Startzustaende ({n_k1_pool} k1-aktiv).")
    if len(pool) < args.n_total:
        print(f"WARNUNG: Pool ({len(pool)}) kleiner als n_total ({args.n_total}) -- Stichprobe wird kleiner ausfallen.")

    sample, strat_meta = stratified_sample(pool, args.n_total, args.n_k1_min, rng)
    n_k1_sample = sum(1 for c in sample if c["k1_active"])
    print(f"[r5_four_head] Stichprobe: {len(sample)} Zustaende, {n_k1_sample} k1-aktiv.")

    print("[r5_four_head] Lade Torch-Modelle ...")
    champion_model, champion_encoder = load_torch_model(os.path.join(ROOT, args.champion_pth))
    b18_model, b18_encoder = load_torch_model(os.path.join(ROOT, args.b18_pth))
    champ_names = output_names_for_model(champion_model)
    b18_names = output_names_for_model(b18_model)
    print(f"[r5_four_head] Champion-Kopf-Ausgaenge: {champ_names}")
    print(f"[r5_four_head] b18-Kopf-Ausgaenge: {b18_names}")
    if "endgame_margin" not in champ_names:
        raise RuntimeError("Champion-Checkpoint traegt keinen endgame_head -- Kopf 1 nicht messbar.")
    if "opp_points" not in champ_names:
        raise RuntimeError("Champion-Checkpoint traegt keinen opp_points_head -- Kopf 2 nicht messbar.")

    b18_ownership_width = b18_model.ownership_head[-1].out_features
    conj_needed = 2 * (72 // 2 + 34)  # == 140, ausgeschrieben zur Selbstpruefung
    if b18_ownership_width < conj_needed:
        raise RuntimeError(
            f"b18-Ownership-Kopf ist nur {b18_ownership_width} breit, braucht >= {conj_needed} "
            f"fuer den Konjunktionspfad (MOSAIC_OWNERSHIP_CONJ=1 waere wirkungslos) -- ABBRUCH."
        )
    print(f"[r5_four_head] b18-Ownership-Kopf-Breite: {b18_ownership_width} (>= {conj_needed}, Konjunktionspfad moeglich).")

    rows = []
    t0 = time.time()
    for i, cand in enumerate(sample):
        state = cand["state"]
        seed_i = args.seed + 1000 + i

        ab_value = ab_value_for_state(state, os.path.join(ROOT, args.champion_onnx), args.sims, args.c_puct, seed_i)
        if ab_value is None:
            print(f"  [{i}] {cand['file']}/{cand['game_id']}: kein ab_value (uebersprungen)")
            continue

        champ_out = forward_raw(champion_model, champion_encoder, state)
        head4_value_raw = float(champ_out["value"].squeeze().item())
        head1_endgame_raw = float(champ_out["endgame_margin"].squeeze().item())
        head2_points_margin = (
            points_to_pts(float(champ_out["points"].squeeze().item()))
            - points_to_pts(float(champ_out["opp_points"].squeeze().item()))
        )

        b18_out = forward_raw(b18_model, b18_encoder, state)
        ownership_raw = b18_out["ownership"].squeeze().tolist()
        head3_ek_margin, ek_own, ek_opp = ek_margin_for_state(state, ownership_raw)

        winner = cand["winner"]
        cur = state["current_player"]
        outcome = 1.0 if winner == cur else 0.0

        rows.append({
            "source": cand["source"], "file": cand["file"], "game_id": cand["game_id"],
            "k1_active": cand["k1_active"], "point_diff_proxy": cand["point_diff_proxy"],
            "ab_value": ab_value, "outcome_current_player_won": outcome,
            "head1_endgame_raw": head1_endgame_raw,
            "head2_points_margin": head2_points_margin,
            "head3_ek_margin": head3_ek_margin, "head3_ek_own": ek_own, "head3_ek_opp": ek_opp,
            "head4_value_raw": head4_value_raw,
        })
        if (i + 1) % 20 == 0:
            print(f"  [{i + 1}/{len(sample)}] elapsed={time.time() - t0:.0f}s")

    n_used = len(rows)
    print(f"[r5_four_head] {n_used}/{len(sample)} Zustaende ausgewertet (Rest: kein ab_value).")

    # ── Kennlinie (aus DENSELBEN Zustaenden, siehe Moduldoku) ───────────────
    ab_arr = np.array([r["ab_value"] for r in rows])
    outcome_arr = np.array([r["outcome_current_player_won"] for r in rows])
    a, b, mcfadden_r2, n_iter = fit_logistic(ab_arr, outcome_arr)
    print(f"[r5_four_head] Kennlinie: a={a:.5f} b={b:.5f} mcfadden_r2={mcfadden_r2:.3f} n={n_used}")

    for r in rows:
        p_solver = curve_win_prob(a, b, r["ab_value"])
        r["p_solver_curve"] = p_solver
        r["p_head1"] = (r["head1_endgame_raw"] + 1.0) / 2.0
        r["p_head4"] = (r["head4_value_raw"] + 1.0) / 2.0
        r["p_head2"] = curve_win_prob(a, b, r["head2_points_margin"])
        r["p_head3"] = curve_win_prob(a, b, r["head3_ek_margin"])

    def block(subset_rows, label):
        if len(subset_rows) < 3:
            return {"n": len(subset_rows), "note": "zu wenige Zustaende fuer belastbare Metriken (<3)"}
        ab = [r["ab_value"] for r in subset_rows]
        heads_native = {
            "head1_endgame_margin": [r["head1_endgame_raw"] for r in subset_rows],
            "head2_points_minus_opp": [r["head2_points_margin"] for r in subset_rows],
            "head3_ek_margin": [r["head3_ek_margin"] for r in subset_rows],
            "head4_value_wdl": [r["head4_value_raw"] for r in subset_rows],
        }
        tanh_target = [2.0 * r["p_solver_curve"] - 1.0 for r in subset_rows]

        out = {"n": len(subset_rows), "label": label, "heads": {}}
        for name, vals in heads_native.items():
            tau = kendall_tau_a(ab, vals)
            if name in ("head1_endgame_margin", "head4_value_wdl"):
                slope, intercept, r2, n_ols = ols_slope_r2(tanh_target, vals)
                slope_scale = "tanh [-1,1] gegen 2*curve_win_prob(ab_value)-1"
            else:
                slope, intercept, r2, n_ols = ols_slope_r2(ab, vals)
                slope_scale = "Punkte direkt gegen ab_value"
            out["heads"][name] = {
                "kendall_tau_vs_ab_value": tau,
                "calibration_slope": slope, "calibration_intercept": intercept,
                "calibration_r2": r2, "n_ols": n_ols, "slope_scale": slope_scale,
            }

        # Vorzeichentest je Kandidat gegen Kopf 4 (Value), auf gemeinsamer P-Skala.
        p_map = {
            "head1_endgame_margin": [r["p_head1"] for r in subset_rows],
            "head2_points_minus_opp": [r["p_head2"] for r in subset_rows],
            "head3_ek_margin": [r["p_head3"] for r in subset_rows],
        }
        p_value_head = [r["p_head4"] for r in subset_rows]
        p_solver = [r["p_solver_curve"] for r in subset_rows]
        sign_tests = {}
        for name, p_cand in p_map.items():
            n_pos, n_neg = 0, 0
            for pc, pv, ps in zip(p_cand, p_value_head, p_solver):
                e_cand = abs(pc - ps)
                e_value = abs(pv - ps)
                if abs(e_cand - e_value) < 1e-12:
                    continue
                if e_cand < e_value:
                    n_pos += 1
                else:
                    n_neg += 1
            sign_tests[name] = sign_test_two_sided(n_pos, n_neg)
        out["sign_test_vs_value_head"] = sign_tests
        return out

    k1_rows = [r for r in rows if r["k1_active"]]
    result = {
        "auftrag": "Vierer-Vergleich R5-Loeser-Kalibrierung (PREREG_r5_solver_split.md par.3d)",
        "sampling": {
            "seed": args.seed,
            "seed_corpus_files": [os.path.basename(f) for f in seed_files],
            "v20wdl_files": [os.path.basename(f) for f in v20_files],
            "n_pool": len(pool), "n_pool_k1_active": n_k1_pool,
            "n_sample_target": args.n_total, "n_k1_min_target": args.n_k1_min,
            "n_sample_drawn": len(sample), "n_sample_k1_active": n_k1_sample,
            "n_sample_evaluated": n_used,
            "tercile_bounds_point_diff_proxy": strat_meta["tercile_bounds"],
        },
        "solver": {"model_path_for_api": args.champion_onnx, "sims": args.sims, "c_puct": args.c_puct,
                    "note": "model_path_for_api ist fuer Runde-5-Zustaende funktional irrelevant "
                            "(round5.rs-Kurzschluss), siehe tools/r5_value_calibration.py Moduldoku."},
        "curve": {"a": a, "b": b, "mcfadden_r2": mcfadden_r2, "n_iter": n_iter, "n_points": n_used},
        "heads_meta": {
            "champion_pth": args.champion_pth, "champion_onnx": args.champion_onnx,
            "champion_output_names": champ_names,
            "b18_pth": args.b18_pth, "b18_output_names": b18_names,
            "b18_ownership_width": b18_ownership_width,
            "conjunction_path_active": True,
            "conjunction_path_evidence": (
                "ownership_ek_plate_points_json (engine/src/lib.rs, neu) verlangt >=140-breiten "
                "Ownership-Rohvektor und bricht sonst hart ab (kein Produktform-Rueckfall wie im "
                "Suchpfad net_mcts.rs::apply_ownership_shaping_full) -- jede Zeile in 'per_state' "
                "belegt damit den aktiven Konjunktionspfad."
            ),
        },
        "overall": block(rows, "gesamt"),
        "k1_active": block(k1_rows, "k1-aktive Teilmenge"),
        "per_state": rows,
    }

    os.makedirs(os.path.dirname(os.path.join(ROOT, args.out)), exist_ok=True)
    with open(os.path.join(ROOT, args.out), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print(f"\nGeschrieben: {args.out}")

    print("\n=== ZUSAMMENFASSUNG (gesamt / k1-aktiv) ===")
    for label, blk in (("gesamt", result["overall"]), ("k1-aktiv", result["k1_active"])):
        print(f"-- {label} (n={blk.get('n')}) --")
        for name, m in blk.get("heads", {}).items():
            print(f"  {name}: tau={m['kendall_tau_vs_ab_value']:.3f} slope={m['calibration_slope']} "
                  f"r2={m['calibration_r2']}")
        for name, st in blk.get("sign_test_vs_value_head", {}).items():
            print(f"  sign_test {name} vs value: {st}")


if __name__ == "__main__":
    main()
