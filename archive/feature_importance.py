"""
Feature-Wichtigkeit (Stufe A, grob) — welche Feature-BLÖCKE nutzt das Netz?

Misst per **Permutation-Importance** am bereits trainierten Netz, wie stark der
maskierte Policy-Loss und der Value-Loss steigen, wenn man die Spalten eines
Feature-Blocks über die Samples durchwürfelt. Großes ΔLoss = das Netz hängt an
diesem Block; ΔLoss ≈ 0 = der Block bringt DIESEM Netz nichts.

Drei grobe Blöcke (genau die Frage „bringen die zuletzt ergänzten Features etwas?"):
  - scoring : Endwertungs-/Geometrie-Features (state_to_tensor Sektion 6b, 74 dim)
  - line    : Linien-Geometrie               (state_to_tensor Sektion 6c, 46 dim)
  - base    : alles andere                   (Rest)

WICHTIG (Lehre aus dem Masking-Bug + stale Kommentaren wie „Dome 9×9=81", das in
Wahrheit 17/Slot ist): die Block-Grenzen werden NICHT aus Kommentaren/Offsets
geraten, sondern **empirisch** bestimmt — wir setzen die score_geo/line_geo-Keys
im State-Dict auf zwei verschiedene Sentinel-Werte und nehmen die Indizes, deren
Tensor-Wert sich ändert. Größen werden per Assertion (74/46) abgesichert.

Der Loss spiegelt train.py exakt: maskierte log_softmax-Policy, pro Sample mit
|value|·policy_weight gewichtet (nur echte Drafting-Schritte, pol_w=1), Value-MSE.

Aufruf (vom Projekt-Root):
    python -m utils.feature_importance --model s100
    python -m utils.feature_importance --model s100 --samples 30000 --repeats 5
"""
import sys
import glob
import copy
import pickle
import argparse
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import numpy as np
import torch
import torch.nn.functional as F

from config import BASE_DIR, DATA_DIR, MODELS_DIR, NUM_ACTIONS, HIDDEN_SIZE

# state_to_tensor / MosaicNet / MosaicDataset liegen in engine/py (wie in train.py).
sys.path.insert(0, str(BASE_DIR / "engine" / "py"))
from neural_net import state_to_tensor, MosaicNet, MosaicDataset  # noqa: E402

# Erwartete Blockgrößen (state_to_tensor Sektion 6b/6c, je 2 Spieler).
SCORING_LEN = 74   # 37 je Spieler
LINE_LEN = 46      # 23 je Spieler


# ── Block-Lokalisierung (empirisch, robust gegen Offset-Drift) ────────────────

def _mut_scoring(d, k):
    for p in d.get("players", []):
        p["scoring_tile_points"] = [k] * 8
        p["score_geo"] = {
            "row_fill": [k] * 6, "col_fill": [k] * 6, "diag_fill": [k] * 2,
            "row_colors": [k] * 6, "border_fill": k, "corner_fill": [k] * 4,
            "wild_filled": k, "wild_total": k, "special_empty": k, "special_total": k,
        }


def _mut_line(d, k):
    for p in d.get("players", []):
        p["line_geo"] = {
            "h_hist": [k] * 5, "v_hist": [k] * 5, "cluster_sq": k,
            "row_potential": [k] * 6, "col_potential": [k] * 6,
        }


def _changed_indices(sample_state, mutate):
    """Indizes, deren Feature-Wert sich ändert, wenn der Block auf zwei
    verschiedene Sentinel-Werte gesetzt wird (= genau die Block-Spalten)."""
    a = copy.deepcopy(sample_state); mutate(a, 1.0)
    b = copy.deepcopy(sample_state); mutate(b, 2.0)
    va = state_to_tensor(a).numpy()
    vb = state_to_tensor(b).numpy()
    return np.where(va != vb)[0]


def locate_blocks(sample_state, input_size):
    scoring = _changed_indices(sample_state, _mut_scoring)
    line = _changed_indices(sample_state, _mut_line)
    assert len(scoring) == SCORING_LEN, (
        f"scoring-Block hat {len(scoring)} statt {SCORING_LEN} dim — "
        f"state_to_tensor Sektion 6b hat sich geändert, Skript anpassen.")
    assert len(line) == LINE_LEN, (
        f"line-Block hat {len(line)} statt {LINE_LEN} dim — "
        f"state_to_tensor Sektion 6c hat sich geändert, Skript anpassen.")
    assert not (set(scoring) & set(line)), "scoring/line überlappen — unerwartet."
    special = set(scoring) | set(line)
    base = np.array([i for i in range(input_size) if i not in special])
    return {"base": base, "scoring": scoring, "line": line}


# ── Loss (spiegelt train.py exakt) ────────────────────────────────────────────

@torch.no_grad()
def compute_losses(model, S, P, V, M, W):
    pred_p, pred_v, _ = model(S)
    masked_logits = pred_p + (M - 1) * 1e9            # illegale Aktionen auf -inf
    log_probs = F.log_softmax(masked_logits, dim=1)
    per_sample_ce = -(P * log_probs).sum(dim=1)        # (B,)
    strength = V.detach().abs().squeeze(-1).clamp(min=1e-3)   # (B,)
    w = strength * W                                   # pol_w=0 → Tiling/Start ignoriert
    p_loss = (per_sample_ce * w).sum() / w.sum().clamp(min=1e-6)
    v_loss = F.mse_loss(pred_v, V)
    return p_loss.item(), v_loss.item()


@torch.no_grad()
def permuted_losses(model, S, P, V, M, W, idx, repeats, rng):
    """Mittlerer Loss, wenn die Spalten `idx` über die Samples durchgewürfelt sind."""
    pls, vls = [], []
    for _ in range(repeats):
        perm = torch.from_numpy(rng.permutation(S.shape[0]))
        Sp = S.clone()
        Sp[:, idx] = S[perm][:, idx]
        pl, vl = compute_losses(model, Sp, P, V, M, W)
        pls.append(pl); vls.append(vl)
    return float(np.mean(pls)), float(np.mean(vls))


def main():
    ap = argparse.ArgumentParser(description="Feature-Block-Wichtigkeit (Permutation-Importance)")
    ap.add_argument("--model", type=str, default="s100",
                    help="Versionsname (models/alphazero_<name>.pth), z.B. s100")
    ap.add_argument("--samples", type=int, default=20000,
                    help="Zufalls-Stichprobe an Samples für die Messung")
    ap.add_argument("--repeats", type=int, default=3, help="Permutationen je Block (Mittelung)")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    torch.manual_seed(args.seed)

    # 1. Daten (gecachte, bereits kodierte Tensoren) + Stichprobe.
    print("📦 Lade Dataset (baut ggf. den Cache neu — kann beim ersten Mal dauern) …")
    ds = MosaicDataset(str(DATA_DIR))
    if len(ds) == 0:
        raise SystemExit(f"❌ Keine Daten in {DATA_DIR}.")
    n = min(args.samples, len(ds))
    sel = torch.from_numpy(rng.choice(len(ds), size=n, replace=False))
    S = ds.states[sel].float()
    P = ds.policies[sel].float()
    V = ds.values[sel].float()
    M = ds.masks[sel].float()
    W = ds.policy_weights[sel].float().view(-1)
    input_size = ds.input_size
    draft_n = int((W > 0).sum())
    print(f"   Stichprobe: {n} Samples ({draft_n} echte Drafting-Schritte, pol_w=1) "
          f"| input_size {input_size}")

    # 2. Blöcke empirisch lokalisieren (an einem echten State-Dict).
    pkls = sorted(glob.glob(str(DATA_DIR / "*.pkl")))
    sample_state = pickle.load(open(pkls[0], "rb"))[0]["state"]
    blocks = locate_blocks(sample_state, input_size)
    print(f"   Blöcke: base {len(blocks['base'])} | scoring {len(blocks['scoring'])} "
          f"| line {len(blocks['line'])}")

    # 3. Modell laden (eval — BatchNorm nutzt die gespeicherten Running-Stats).
    mp = MODELS_DIR / f"alphazero_{args.model}.pth"
    if not mp.exists():
        raise SystemExit(f"❌ Modell nicht gefunden: {mp}")
    model = MosaicNet(input_size=input_size, num_actions=NUM_ACTIONS, hidden_size=HIDDEN_SIZE)
    ckpt = torch.load(str(mp), map_location="cpu")
    model.load_state_dict(ckpt["model_state"], strict=False)
    model.eval()
    print(f"🧠 Modell: {mp.name}")

    # 4. Baseline + Permutation je Block.
    base_p, base_v = compute_losses(model, S, P, V, M, W)
    W1 = model.body[0].weight.detach()   # (hidden, input): erste Linear-Schicht

    rows = []
    for name in ("base", "scoring", "line"):
        idx = blocks[name]
        pl, vl = permuted_losses(model, S, P, V, M, W, idx, args.repeats, rng)
        dp = pl - base_p
        dv = vl - base_v
        # Cross-Check: mittlere L2-Spaltennorm der ersten Layer-Gewichte je Feature.
        wnorm = W1[:, idx].norm(dim=0).mean().item()
        rows.append((name, len(idx), dp, dp / base_p * 100, dv, dv / base_v * 100,
                     dp / len(idx), wnorm))

    # 5. Ausgabe.
    print("\n" + "=" * 92)
    print(f"FEATURE-BLOCK-WICHTIGKEIT  (Baseline: Policy {base_p:.4f} | Value {base_v:.4f})")
    print("=" * 92)
    print(f"{'Block':<8} {'dim':>4} | {'ΔPolicy':>9} {'(%)':>7} | {'ΔValue':>9} {'(%)':>7} "
          f"| {'ΔP/dim':>9} | {'|W1|':>6}")
    print("-" * 92)
    for name, dim, dp, dpp, dv, dvp, dpd, wn in rows:
        flag = "  ⚠️ kaum genutzt" if (dpp < 1.0 and dvp < 1.0) else ""
        print(f"{name:<8} {dim:>4} | {dp:>9.4f} {dpp:>6.1f}% | {dv:>9.4f} {dvp:>6.1f}% "
              f"| {dpd:>9.5f} | {wn:>6.3f}{flag}")
    print("-" * 92)
    print("Lesart: höheres ΔLoss = wichtiger. ΔP/dim normiert auf die Blockgröße "
          "(fairer Vergleich base↔scoring↔line).")
    print("        |W1| = mittlere Spaltennorm der 1. Layer-Gewichte (grober "
          "'benutzt das Netz die Spalte'-Indikator).")
    print("Hinweis: misst, was DIESES Netz nutzt — nicht, ob ein Block bei Neutraining "
          "helfen würde. Verdächtige Blöcke per Retrain-Ablation + Arena bestätigen.")


if __name__ == "__main__":
    main()
