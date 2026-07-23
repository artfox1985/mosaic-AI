"""
tools/offline_diagnose.py — Offline-Diagnose eines trainierten Checkpoints:
Value-Val-R² gesamt + pro Runde (1-5), Policy Top-1/Top-3 (nur echte
Drafting-Schritte, pol_w=1) -- auf demselben Val-DATEI-Split wie train.py
(Datei-Ebene-Split, Seed 20260707, val_frac=0.1), damit die Zahlen 1:1 gegen
den v12-Zyklus (evaluations/STATUS.md, "v12-Zyklus (2026-07-23)") vergleichbar
sind.

`tools/diagnosis.py` deckt das NICHT ab (keine Pro-Runde-R²-Aufschlüsselung,
kein Top-1/Top-3) -- Task #77 (v12b) brauchte genau diese Metriken erneut
und das beim v12-Zyklus dafür genutzte Skript war nirgends im Repo abgelegt
(weder committet noch als Arbeitsdatei liegen geblieben) -- dieses Skript
rekonstruiert das Vorgehen laut STATUS.md-Beschreibung ("mirrort MosaicDataset
1:1 inkl. Runden-Index je Schritt") und wird DIESMAL nach tools/ committet.

Value-Ziel-Berechnung ist 1:1 aus `neural_net.py::MosaicDataset.__init__`
kopiert (own_total/opp_total → tanh-Margin, `round_transition_value`-Override,
`bootstrap_value`-TD-Blend) -- bewusst NICHT der HDF5-Cache direkt
wiederverwendet, weil der keine Pro-Schritt-Rundennummer mitführt (nur die
bereits zu Tensoren geflachten Features). Policy-Ziel/Maske ebenfalls 1:1
kopiert (inkl. Selbstkonsistenz-Fix: gespielte Policy-Aktionen immer in die
Maske aufnehmen).

Verwendung:
    python tools/offline_diagnose.py --model v12_best
    python tools/offline_diagnose.py --model v12b_lr_best v12b_scratch_best v12_best
    python tools/offline_diagnose.py --model v12b_lr_best --out evaluations/offline_diagnose_v12b.json
"""
import argparse
import glob
import json
import math
import pickle
import random
import sys
from pathlib import Path

# Windows-Konsolen (cp1252) können die Emoji-Ausgaben sonst nicht kodieren
# (gleiches Muster wie train.py).
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine" / "py"))

from config import DATA_DIR, MODELS_DIR, NUM_ACTIONS, INPUT_SIZE
from neural_net import (
    MosaicNet, state_to_tensor, action_to_id,
    VALUE_SCALE, VALUE_OPP_EPSILON, TD_LAMBDA,
)

# Muss 1:1 zu train.py::train() bleiben (val_frac=0.1-Default, Seed 20260707)
# -- sonst ist der Val-Split hier NICHT derselbe wie beim Training, und die
# Zahlen sind nicht vergleichbar.
VAL_SEED = 20260707
VAL_FRAC = 0.1


def val_files() -> list[str]:
    all_files = sorted(glob.glob(str(DATA_DIR / "*.pkl")))
    shuffled = all_files[:]
    random.Random(VAL_SEED).shuffle(shuffled)
    n_val = max(1, round(len(shuffled) * VAL_FRAC))
    return sorted(shuffled[:n_val])


def load_val_samples(files: list[str]):
    """Läd alle Val-Schritte direkt aus den Pickles -- Value-Ziel/Policy-
    Ziel/Maske sind 1:1-Kopien der Logik aus `MosaicDataset.__init__`
    (neural_net.py), zusätzlich mit Runden-Index je Schritt (der einzige
    Grund, warum hier nicht einfach der bestehende HDF5-Cache
    wiederverwendet wird)."""
    states_l, values_l, rounds_l, polw_l = [], [], [], []
    policy_l, masks_l = [], []

    for f in files:
        with open(f, "rb") as fh:
            game_data = pickle.load(fh)
        for step in game_data:
            if "scores" not in step or "winner" not in step:
                continue
            state = step["state"]
            states_l.append(state_to_tensor(state).numpy())
            rounds_l.append(int(state.get("round", 0)))

            p = step["player"]
            scores_src = step.get("scores_unclamped", step["scores"])
            own_total = float(scores_src[p])
            opp_total = float(scores_src[1 - p])
            val = math.tanh((own_total - opp_total) / VALUE_SCALE)

            rtv = step.get("round_transition_value")
            if rtv is not None:
                val = float(rtv[p]) * 2.0 - 1.0

            bv = step.get("bootstrap_value")
            if bv is not None:
                own_bootstrap = float(bv[p]) * 2.0 - 1.0
                val = TD_LAMBDA * own_bootstrap + (1.0 - TD_LAMBDA) * val
            values_l.append(val)

            t_policy = np.zeros(NUM_ACTIONS, dtype=np.float32)
            for pe in step["policy"]:
                t_policy[action_to_id(pe["action"])] += pe["prob"]
            s = t_policy.sum()
            if s > 0:
                t_policy /= s
            policy_l.append(t_policy)

            mask = np.zeros(NUM_ACTIONS, dtype=np.float32)
            moves = step.get("valid_actions") or state.get("valid_moves", [])
            for mv in moves:
                mask[action_to_id(mv)] = 1.0
            for pe in step["policy"]:
                mask[action_to_id(pe["action"])] = 1.0
            masks_l.append(mask)

            phase = state.get("phase")
            is_start = any(pe["action"].get("is_start") for pe in step["policy"])
            polw_l.append(1.0 if (phase == "drafting" and not is_start) else 0.0)

    return (
        torch.from_numpy(np.array(states_l, dtype=np.float32)),
        np.array(values_l, dtype=np.float32),
        np.array(rounds_l, dtype=np.int64),
        np.array(polw_l, dtype=np.float32),
        np.array(policy_l, dtype=np.float32),
        np.array(masks_l, dtype=np.float32),
    )


def _r2(y_true: np.ndarray, y_pred: np.ndarray) -> float | None:
    if len(y_true) == 0:
        return None
    ss_tot = float(np.sum((y_true - y_true.mean()) ** 2))
    if ss_tot <= 1e-9:
        return None
    ss_res = float(np.sum((y_true - y_pred) ** 2))
    return 1.0 - ss_res / ss_tot


def diagnose(model_name: str, states, values, rounds, pol_w, policy_targets, masks,
             batch_size: int = 4096, hidden_override: int | None = None) -> dict:
    ckpt_path = MODELS_DIR / f"alphazero_{model_name}.pth"
    ckpt = torch.load(str(ckpt_path), map_location="cpu")
    hs = hidden_override if hidden_override is not None else ckpt.get("hidden_size", 512)
    model = MosaicNet(input_size=INPUT_SIZE, num_actions=NUM_ACTIONS, hidden_size=hs)
    model.load_state_dict(ckpt["model_state"], strict=False)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device).eval()

    n = states.shape[0]
    value_preds = np.zeros(n, dtype=np.float32)
    top1_hits = np.zeros(n, dtype=bool)
    top3_hits = np.zeros(n, dtype=bool)

    masks_t = torch.from_numpy(masks)
    target_argmax = policy_targets.argmax(axis=1)  # (n,) -- meist-besuchte Ziel-Aktion

    with torch.no_grad():
        for i in range(0, n, batch_size):
            sl = slice(i, i + batch_size)
            x = states[sl].to(device)
            m = masks_t[sl].to(device)
            pred_p, pred_v, _pred_moon, _pred_points = model(x)
            value_preds[sl] = pred_v.squeeze(-1).cpu().numpy()

            masked_logits = pred_p + (m - 1) * 1e9
            top3_idx = torch.topk(masked_logits, k=3, dim=1).indices.cpu().numpy()
            pred_top1 = top3_idx[:, 0]
            tgt = target_argmax[sl]
            top1_hits[sl] = pred_top1 == tgt
            top3_hits[sl] = (top3_idx == tgt[:, None]).any(axis=1)

    result: dict = {"model": model_name, "n_total": int(n)}

    result["value_r2_global"] = _r2(values, value_preds)
    per_round = {}
    for r in range(1, 6):
        rmask = rounds == r
        per_round[str(r)] = {
            "n": int(rmask.sum()),
            "r2": _r2(values[rmask], value_preds[rmask]),
        }
    result["value_r2_by_round"] = per_round

    draft_mask = pol_w > 0.5
    n_draft = int(draft_mask.sum())
    result["policy_n_drafting"] = n_draft
    if n_draft > 0:
        result["policy_top1"] = float(top1_hits[draft_mask].mean())
        result["policy_top3"] = float(top3_hits[draft_mask].mean())
    else:
        result["policy_top1"] = None
        result["policy_top3"] = None

    return result


def print_table(results: list[dict]) -> None:
    names = [r["model"] for r in results]
    print("\n" + "=" * 70)
    print("  OFFLINE-DIAGNOSE (Val-Split Datei-Ebene, Seed 20260707, val_frac=0.1)")
    print("=" * 70)
    header = "Metrik".ljust(28) + "".join(n.rjust(16) for n in names)
    print(header)
    print("-" * len(header))

    def row(label, values):
        print(label.ljust(28) + "".join(v.rjust(16) for v in values))

    row("n (Val-Züge gesamt)", [str(r["n_total"]) for r in results])
    row("Policy Top-1 (Drafting)",
        [f"{r['policy_top1']*100:.1f}%" if r["policy_top1"] is not None else "n/a" for r in results])
    row("Policy Top-3 (Drafting)",
        [f"{r['policy_top3']*100:.1f}%" if r["policy_top3"] is not None else "n/a" for r in results])
    row("  (n Drafting)", [str(r["policy_n_drafting"]) for r in results])
    row("Value Val-R² global",
        [f"{r['value_r2_global']:.4f}" if r["value_r2_global"] is not None else "n/a" for r in results])
    for rd in range(1, 6):
        row(f"R² Runde {rd}",
            [(f"{r['value_r2_by_round'][str(rd)]['r2']:.4f}"
              if r['value_r2_by_round'][str(rd)]['r2'] is not None else "n/a") for r in results])
    print("=" * 70)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--model", nargs="+", required=True,
                    help="Version-Name(en) OHNE 'alphazero_'-Präfix/'.pth'-Endung, z.B. v12_best")
    p.add_argument("--hidden", type=int, default=None, help="Hidden-Size-Override (Standard: aus Checkpoint)")
    p.add_argument("--batch-size", type=int, default=4096)
    p.add_argument("--out", type=str, default=None,
                    help="Ziel-JSON-Pfad (Standard: evaluations/offline_diagnose_<model1>_vs_....json)")
    args = p.parse_args()

    files = val_files()
    print(f"📦 Val-Split: {len(files)} Dateien (Seed {VAL_SEED}, val_frac={VAL_FRAC})")
    states, values, rounds, pol_w, policy_targets, masks = load_val_samples(files)
    print(f"   {len(states):,} Val-Züge geladen.")

    results = []
    for name in args.model:
        print(f"\n🔎 Diagnose: {name}")
        res = diagnose(name, states, values, rounds, pol_w, policy_targets, masks,
                        batch_size=args.batch_size, hidden_override=args.hidden)
        results.append(res)

    print_table(results)

    out_path = args.out
    if out_path is None:
        base = Path(__file__).resolve().parent.parent / "evaluations"
        out_path = str(base / f"offline_diagnose_{'_vs_'.join(args.model)}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "val_seed": VAL_SEED, "val_frac": VAL_FRAC, "n_val_files": len(files),
            "results": results,
        }, f, indent=2, ensure_ascii=False)
    print(f"\n📝 Ergebnis gespeichert unter: {out_path}")


if __name__ == "__main__":
    main()
