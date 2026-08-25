# -*- coding: utf-8 -*-
"""Stufe 0 Punkte 2+3 fuer PREREG_ownership_selector.md (par.5): Kalibrierung
und Verteilung von p_atom fuer die drei ZIEL-Konjunktionsgruppen einer
moeglichen Selektor-Vorzugsroute (Umbau A, par.3.1) -- Spalten (Index 6..11),
Diagonalen (12..13), Ecken (14..17) im 34-breiten Konjunktionsblock je Spieler
(`_conjunctions_from_dome`, `engine/py/neural_net.py:932`, Docstring dort ist
die geprüfte Quelle der Index-Reihenfolge).

Unterschied zu `tools/probes/ownership_gate_a.py` (Tor A): Gate A misst
Feld-/Konjunktions-AUC auf dem KOMPLETTEN Endzustand (Input == der Zustand,
dessen eigene Labels vorhergesagt werden -- der Konfundierungsfall aus par.8
Punkt 3 kann dort gar nicht auftreten, weil Runde/Fuellgrad am Ende praktisch
fix sind). Diese Sonde bewertet stattdessen GENAU DIE ZUSTAENDE, an denen die
geplante Route lesen wuerde: `state.phase == "tiling"` (par.3.1 "einmal je
Tiling-Zug"), ueber alle Runden verteilt -- damit lassen sich Kalibrierung und
Konfundierung nach Runde/Fuellgrad ueberhaupt trennen (par.8 Punkt 3).

Ego-Zuordnung (GEPRUEFT, nicht angenommen):
  - `state_to_tensor`/`state_to_planes` (neural_net.py:30/358) kodieren IMMER
    aus Sicht von `current_player` -- Kopf-Ausgabe [72:106] ist deshalb schon
    am Encoder-Eingang "ich", nicht spielerindex-fest (bestaetigt durch den
    Trainings-Kommentar neural_net.py:1826-1831: "Ego-Perspektive: erst der
    Spieler am Zug ... dieselbe Reihenfolge wie in state_to_tensor").
  - Das TRUE-Label ist dagegen spielerindex-fest (`_conjunctions_from_dome`
    liefert je EINEN Vektor pro `players[0]`/`players[1]`), muss also beim
    Zusammenfuehren mit `state["current_player"]` an DIESEM Tiling-Schritt neu
    zugeordnet werden -- exakt wie neural_net.py:1832-1834
    (`first, second = (fo[0], fo[1]) if c == 0 else (fo[1], fo[0])`) und wie
    `ownership_gate_a.py`s `own_lab_me`/`conj_lab_me` es fuer den Endzustand
    bereits tut.

Checkpoints (Nutzer-Auftrag): F1 = alphazero_v21_2d_own_f1.pth (voraussichtl.
Vehikel, Policy intakt), W1 = alphazero_v21_2d_own_w1.pth (FINAL-Epoche, nicht
`_w1_best` -- geprueft gegen evaluations/ownership_gate_a_w1.json: `final`
Epoche 15 hat AUC 0,974/0,987/0,981 fuer Spalten/Diagonalen/Ecken gegen
0,782/0,814/0,859 bei `best` Epoche 1 -- "final, bester Kopf" bezieht sich auf
den FINAL-Tag).

Held-out-Split: identisch zu Gate A (`reconstruct_split()` importiert), weil
F1- und W1-Manifest dieselbe `corpus_composition` (3745 Dateien, 11 Gruppen)
tragen wie das W0-Manifest, gegen das `reconstruct_split()` prueft -- verifiziert
in dieser Sitzung per `python -c` Vergleich der drei Manifeste.

Usage:  python tools/probes/ownership_route_calibration.py
Output: evaluations/ownership_route_calibration_results.json (+ Konsole).
"""
import glob
import json
import pickle
import sys
import time
from pathlib import Path

import numpy as np
import torch

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "engine" / "py"))
sys.path.insert(0, str(REPO / "tools" / "probes"))

from neural_net import _dome_grids_from_dome, build_model_from_checkpoint  # noqa: E402
from ownership_gate_a import (  # noqa: E402
    auc_score,
    brier,
    collect_base_rates,
    game_labels,
    is_corpus_file,
    reconstruct_split,
    spearman,
)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
OUT_JSON = REPO / "evaluations" / "artifacts" / "ownership_route_calibration_results.json"

CHECKPOINTS = [
    ("f1", "alphazero_v21_2d_own_f1.pth"),
    ("w1", "alphazero_v21_2d_own_w1.pth"),
]

# Slices within the 34-wide conjunction block, GEPRUEFT gegen
# neural_net.py:932 Docstring (siehe Modul-Docstring oben).
TARGET_GROUPS = {
    "columns_k1": slice(6, 12),
    "diagonals_k2": slice(12, 14),
    "corners_k5": slice(14, 18),
}
BINS = np.linspace(0.0, 1.0, 11)  # 10 Bins
QUANTILES = [50, 75, 90, 95, 99]
THRESH_CHECK = [0.3, 0.5, 0.7, 0.9]


def iter_tiling_records(pkl_path):
    """Je Spiel: (gid, last_record, [tiling-phase Zwischenzustaende])."""
    data = pickle.load(open(pkl_path, "rb"))
    by_gid = {}
    for step in data:
        by_gid.setdefault(step["game_id"], []).append(step)
    for gid, steps in by_gid.items():
        last = steps[-1]
        if not last.get("completed"):
            continue
        tiling = [s for s in steps if s["state"].get("phase") == "tiling"]
        yield gid, last, tiling


def ego_fill_fraction(state, cp):
    dome = state["players"][cp]["dome_grid"]
    filled, _ = _dome_grids_from_dome(dome)
    return sum(sum(row) for row in filled) / 36.0


def collect_tiling_dataset(val_corpus):
    """Ueber alle Held-out-Ownership-Korpus-Dateien: je Tiling-Zug ein
    Sample (state, round, ego fill fraction, 34-wide ego-Label)."""
    states, rounds, fills, ego_labels = [], [], [], []
    n_games = n_incomplete = n_tiling_steps = 0
    for f in val_corpus:
        for gid, last, tiling in iter_tiling_records(f):
            if not tiling:
                continue
            o0, o1, c0, c1 = game_labels(last)
            n_games += 1
            for step in tiling:
                st = step["state"]
                cp = st.get("current_player", 0)
                ego_lab = c0 if cp == 0 else c1
                states.append(st)
                rounds.append(st.get("round"))
                fills.append(ego_fill_fraction(st, cp))
                ego_labels.append(ego_lab)
                n_tiling_steps += 1
    return states, np.array(rounds), np.array(fills), np.array(ego_labels, dtype=np.int8), n_games, n_tiling_steps


def encode_all(states):
    from neural_net import state_to_planes, state_to_tensor
    t0 = time.time()
    flat = torch.stack([state_to_tensor(s) for s in states]).float()
    planes = torch.stack([state_to_planes(s) for s in states]).float()
    print(f"  Encoding {len(states)} Tiling-Zustaende: {time.time() - t0:.1f}s")
    return planes, flat


def predict_all(model, planes, flat, batch=512):
    outs = []
    with torch.no_grad():
        for i in range(0, planes.shape[0], batch):
            o = model(planes[i:i + batch].to(DEVICE), flat[i:i + batch].to(DEVICE))
            outs.append(torch.sigmoid(o[4]).cpu().numpy())
    return np.concatenate(outs, axis=0)


def reliability_curve(p, y, bins=BINS):
    out = []
    for i in range(len(bins) - 1):
        lo, hi = bins[i], bins[i + 1]
        mask = (p >= lo) & (p < hi) if i < len(bins) - 2 else (p >= lo) & (p <= hi)
        n = int(mask.sum())
        if n == 0:
            out.append({"lo": float(lo), "hi": float(hi), "n": 0,
                        "mean_pred": None, "mean_actual": None})
            continue
        out.append({"lo": float(lo), "hi": float(hi), "n": n,
                    "mean_pred": float(p[mask].mean()),
                    "mean_actual": float(y[mask].mean())})
    return out


def per_round_metrics(p_flat_per_atom, y_flat_per_atom, rounds_rep, base_mean):
    """p/y sind (N, W); rounds_rep ist (N,) -- fuer jede Runde ueber alle W
    Atome der Gruppe gepoolt Brier/AUC gegen die konstante Basisrate."""
    out = {}
    for r in sorted(set(int(x) for x in rounds_rep.tolist())):
        m = rounds_rep == r
        n = int(m.sum())
        if n == 0:
            continue
        pr, yr = p_flat_per_atom[m], y_flat_per_atom[m]
        aucs = [auc_score(yr[:, j], pr[:, j]) for j in range(pr.shape[1])]
        defined = [a for a in aucs if a is not None]
        out[str(r)] = {
            "n_states": n,
            "brier": brier(yr, pr),
            "brier_base": brier(yr, np.tile(base_mean, (n, 1))),
            "auc_macro": float(np.mean(defined)) if defined else None,
        }
    return out


def main():
    train_files, val_files = reconstruct_split()
    val_corpus = [f for f in val_files if is_corpus_file(f)]
    print(f"Split (identisch zu Gate A, W0-Manifest-Assert): {len(train_files)} train / "
          f"{len(val_files)} val Dateien, davon Ownership-Korpus: {len(val_corpus)}")

    print("Basisraten (TRAIN-Split, END-Zustaende, wie Gate A) ...")
    _base_own, base_conj, n_base = collect_base_rates(train_files)
    print(f"  {n_base} Spielerbretter; base_conj[6:12]={np.round(base_conj[6:12], 4)} "
          f"(Spalten) [12:14]={np.round(base_conj[12:14], 4)} (Diagonalen) "
          f"[14:18]={np.round(base_conj[14:18], 4)} (Ecken)")

    print("Sammle Tiling-Zwischenzustaende aus dem Held-out-Ownership-Korpus ...")
    states, rounds, fills, ego_labels, n_games, n_steps = collect_tiling_dataset(val_corpus)
    print(f"  {n_games} vollstaendige Held-out-Partien, {n_steps} Tiling-Zuege insgesamt "
          f"({n_steps / max(n_games, 1):.1f} je Partie)")
    print(f"  Rundenverteilung: {dict(zip(*np.unique(rounds, return_counts=True)))}")

    planes, flat = encode_all(states)

    results = {
        "n_heldout_games_with_tiling": n_games,
        "n_tiling_states": n_steps,
        "round_distribution": {str(k): int(v) for k, v in zip(*np.unique(rounds, return_counts=True))},
        "base_rate_conj_full34": base_conj.tolist(),
        "device": DEVICE,
        "checkpoints": {},
    }

    for tag, fname in CHECKPOINTS:
        path = REPO / "models" / fname
        if not path.exists():
            print(f"  FEHLT: {fname} -- uebersprungen")
            continue
        ck = torch.load(path, map_location="cpu", weights_only=False)
        model, _enc = build_model_from_checkpoint(ck)
        model.eval().to(DEVICE)
        print(f"\n=== {tag} ({fname}, Epoche {ck.get('epochs')}) ===")

        p_all = predict_all(model, planes, flat)
        ego_pred = p_all[:, 72:106]  # (N, 34) -- current_player wegen Encoder-Ego (s.o.)

        ck_out = {"checkpoint": fname, "epochs": ck.get("epochs"), "groups": {}}

        for gname, sl in TARGET_GROUPS.items():
            p_g = ego_pred[:, sl]          # (N, W)
            y_g = ego_labels[:, sl]        # (N, W)
            base_g = base_conj[sl]         # (W,)
            w = p_g.shape[1]

            aucs = [auc_score(y_g[:, j], p_g[:, j]) for j in range(w)]
            g_out = {
                "n_atoms": w,
                "base_rate_per_atom": base_g.tolist(),
                "base_rate_mean": float(base_g.mean()),
                "brier_overall": brier(y_g, p_g),
                "brier_base_overall": brier(y_g, np.tile(base_g, (y_g.shape[0], 1))),
                "auc_per_atom": aucs,
                "auc_macro": float(np.mean([a for a in aucs if a is not None]))
                if any(a is not None for a in aucs) else None,
            }

            # gepoolt ueber Atome UND Zustaende (Verteilung, Item 3)
            p_pool = p_g.ravel()
            y_pool = y_g.ravel()
            g_out["reliability_curve_pooled"] = reliability_curve(p_pool, y_pool)
            g_out["quantiles_pooled_pct"] = {
                str(q): float(np.percentile(p_pool, q)) for q in QUANTILES
            }
            g_out["share_over_pooled"] = {
                str(t): float((p_pool >= t).mean()) for t in THRESH_CHECK
            }

            # Zustands-Ebene: MAX ueber die Atome der Gruppe je Zustand -- Annaeherung
            # an "wuerde die Route hier ueberhaupt in Erwaegung ziehen" OHNE die
            # `scoring_tile_ids`-Aktivkriterien-Einschraenkung aus par.3.1 Schritt 1
            # (die ist Stufe-1-Maschinerie, hier NICHT gebaut) -- ausdruecklich als
            # Naeherung markiert.
            p_state_max = p_g.max(axis=1)
            g_out["quantiles_state_max_pct"] = {
                str(q): float(np.percentile(p_state_max, q)) for q in QUANTILES
            }
            g_out["share_over_state_max"] = {
                str(t): float((p_state_max >= t).mean()) for t in THRESH_CHECK
            }

            # Konfundierung: nach Spielrunde (par.8 Punkt 3)
            g_out["per_round"] = per_round_metrics(p_g, y_g, rounds, base_g)

            # Rohkorrelation p_atom (gepoolt je Zustand: Mittel ueber Atome der
            # Gruppe) gegen Fuellgrad -- Kontext-Kennzahl, kein Kalibrierungswert.
            p_state_mean = p_g.mean(axis=1)
            g_out["spearman_p_vs_fill_degree"] = spearman(p_state_mean, fills)

            ck_out["groups"][gname] = g_out

            print(f"  {gname:12s} n_atoms={w} Basisrate(mean)={g_out['base_rate_mean']:.4f} "
                  f"Brier {g_out['brier_overall']:.4f} (Basis {g_out['brier_base_overall']:.4f}) "
                  f"AUC(macro) {g_out['auc_macro']}")
            print(f"    Quantile p_atom (gepoolt) 50/75/90/95/99%: "
                  f"{[round(g_out['quantiles_pooled_pct'][str(q)], 3) for q in QUANTILES]}")
            print(f"    Anteil >= 0.3/0.5/0.7/0.9 (gepoolt): "
                  f"{[round(g_out['share_over_pooled'][str(t)], 4) for t in THRESH_CHECK]}")
            print(f"    Runden-Brier/AUC: " +
                  ", ".join(f"r{r}: brier={v['brier']:.4f}(base {v['brier_base']:.4f}) "
                            f"auc={v['auc_macro']}" for r, v in g_out["per_round"].items()))

        results["checkpoints"][tag] = ck_out

    OUT_JSON.write_text(json.dumps(results, indent=1), encoding="utf-8")
    print(f"\nRohzahlen -> {OUT_JSON}")


if __name__ == "__main__":
    main()
