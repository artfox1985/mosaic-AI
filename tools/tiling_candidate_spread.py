# -*- coding: utf-8 -*-
"""tools/tiling_candidate_spread.py -- lohnen sich Task #20 und #21 ueberhaupt?

Beide Vorhaben ersetzen das Auswahlkriterium des Tiling-Solvers. Bevor dafuer
Arena-Zeit ausgegeben wird, ist EINE Frage zu klaeren: waehlt das neue Kriterium
ueberhaupt jemals einen ANDEREN Zug als das alte? Wenn nicht, erledigt sich alles
ohne einen einzigen gespielten Zug.

Gemessen wird auf echten Tiling-Stellungen aus `evaluations/frozen_eval_set.pkl`
ueber `mosaic_rust.tiling_candidates_json`, das bis zu k VOLLSTAENDIGE
Tiling-Abschluesse mit Punkten, Endwertung und Folgezustand liefert.

## Task #21 -- Runde 5, exakte Endwertung

    alt:  argmax( punkte )
    neu:  argmax( punkte + end_scoring(Brett NACH dem Abschluss) )

Berichtet: Anteil der Stellungen, in denen die beiden auseinanderfallen, und wie
viele Endwertungs-Punkte dabei auf dem Spiel stehen. Das ist ein
KORREKTHEITS-Fix (die Groesse ist exakt, kein Proxy) -- der Anteil entscheidet
nur, ob sich eine Arena-Messung lohnt.

## Task #20 -- Runden 2-4, netz-gefuehrt

    alt:  argmax( punkte )
    neu:  argmax( punkte * value(Brett NACH dem Abschluss) )

Berichtet die SPREIZUNG der Value-Werte unter den Kandidaten. Ist sie winzig,
kann die Multiplikation nie einen Punktabstand kippen und das Feature ist tot.
Zur Einordnung: bei einem 20-Punkte-Tiling kippt ein Value-Vorsprung von 0,02
etwa 0,8 Punkte, 0,05 etwa 1,8 Punkte.

Zusaetzlich: wie oft aendert die Multiplikation die Wahl tatsaechlich?
"""
from __future__ import annotations

import argparse
import json
import pickle
import statistics as stats
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "engine" / "py"))

import numpy as np  # noqa: E402
import torch  # noqa: E402

from config import MODELS_DIR  # noqa: E402
from neural_net import (build_model_from_checkpoint, state_to_planes,  # noqa: E402
                        state_to_tensor)

# 2026-09-01 (PREREG_geometric_envelope.md par.3e): das Werkzeug konnte nur den
# Flach-Encoder (`MosaicNet`) laden; die registrierte Messung auf dem
# spaltenfaehigen 2D-Netz b01 war damit nicht fahrbar. Jetzt baut
# `build_model_from_checkpoint` Flach- ODER 2D-Netz aus dem Checkpoint (dieselbe
# Stelle wie r5_value_calibration/oracle_metrics), und der Satz ist waehlbar:
# frozen_v1 (Bestand, Vergleichbarkeit zur Erstmessung) oder frozen_v3
# (b01-Aera). Der Forward-Pass uebernimmt die Kanal-Kuerzung fuer Alt-Modelle
# aus tools/r5_value_calibration.py (2D-Encoder ist additiv).
FROZEN_SETS = {
    "v1": ROOT / "evaluations" / "frozen_eval_set.pkl",
    "v2": ROOT / "evaluations" / "frozen_eval_set_v2.pkl",
    "v3": ROOT / "evaluations" / "frozen_eval_set_v3.pkl",
}


def load_model(name: str):
    ckpt = torch.load(str(MODELS_DIR / f"alphazero_{name}.pth"), map_location="cpu",
                      weights_only=False)
    model, encoder = build_model_from_checkpoint(ckpt)
    model.eval()
    return model, encoder


def _model_plane_channels(model):
    for mod in model.modules():
        if isinstance(mod, torch.nn.Conv2d):
            return mod.weight.shape[1]
    return None


def _model_flat_width(model):
    """Eingangsbreite des Flach-Zweigs aus dem ersten Linear (weight [out, in])."""
    for name, mod in model.named_modules():
        if isinstance(mod, torch.nn.Linear) and ("flat" in name or name.startswith("fc")):
            return mod.weight.shape[1]
    for mod in model.modules():
        if isinstance(mod, torch.nn.Linear):
            return mod.weight.shape[1]
    return None


def value_batch(model, encoder: str, states):
    """Roh-Value (tanh-Skala [-1,1]) je Zustand, Flach- oder 2D-Netz.
    Alt-Modelle mit schmalerer Flach-Eingabe (v18_2d: 708 gegen heute 714)
    bekommen die Eingabe wie im Rust-Pfad (net.rs, "auf die Modellbreite
    kuerzen") HINTEN gekuerzt -- der Flach-Encoder ist additiv. Nie auffuellen."""
    x_flat = torch.stack([state_to_tensor(st) for st in states])
    want_flat = _model_flat_width(model)
    if want_flat is not None and want_flat < x_flat.shape[1]:
        x_flat = x_flat[:, :want_flat]
    with torch.no_grad():
        if encoder == "2d":
            x_planes = torch.stack([state_to_planes(st) for st in states])
            want = _model_plane_channels(model)
            if want is not None and want < x_planes.shape[1]:
                x_planes = x_planes[:, :want, :, :]
            out = model(x_planes, x_flat)
        else:
            out = model(x_flat)
    return out[1].reshape(len(states)).numpy()


def q(xs, p):
    if not xs:
        return float("nan")
    s = sorted(xs)
    i = (len(s) - 1) * p
    lo, hi = int(i), min(int(i) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (i - lo)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default="v18_best")
    ap.add_argument("--k", type=int, default=12)
    ap.add_argument("--max-states", type=int, default=400)
    ap.add_argument("--out", default="evaluations/artifacts/tiling_candidate_spread.json")
    ap.add_argument("--frozen", default="v1", choices=sorted(FROZEN_SETS),
                    help="Zustandssatz: v1 (Bestand), v2, v3 (b01-Aera)")
    args = ap.parse_args()
    FROZEN_PKL = FROZEN_SETS[args.frozen]

    import mosaic_rust as mr

    records = pickle.loads(FROZEN_PKL.read_bytes())["records"]
    tiling = [r for r in records if r["state"].get("phase") == "tiling"]
    print(f"Frozen set: {len(records)} Records, davon {len(tiling)} in der Tiling-Phase")
    if not tiling:
        raise SystemExit("Keine Tiling-Stellungen im frozen set -- Messung nicht moeglich.")
    step = max(1, len(tiling) // args.max_states)
    picked = tiling[::step][:args.max_states]
    model, encoder = load_model(args.model)
    print(f"Modell {args.model} ({encoder}) | Satz frozen_{args.frozen} | k={args.k} | "
          f"{len(picked)} Stellungen" + chr(10), flush=True)

    n_multi = 0            # Stellungen mit >1 Kandidat (nur dort ist etwas zu entscheiden)
    r5_diff, r5_gain = 0, []          # Task #21
    val_spread, mult_diff, n_r24 = [], 0, 0   # Task #20
    # 2026-09-02: `mult_diff` zaehlt auch Wechsel zwischen PUNKTGLEICHEN
    # Kandidaten (argmax nimmt den ersten). Die Frage der Gelaender-Prereg ist
    # aber, ob der Value einen PUNKTVORSPRUNG kippt -- das zaehlt
    # `strict_override` (gewaehlter Kandidat hat WENIGER Punkte als das
    # Maximum), mit der gekippten Punktdifferenz.
    strict_override, override_margins = 0, []
    by_round = {}
    skipped = 0

    for i, rec in enumerate(picked):
        st = rec["state"]
        pi = st.get("current_player", 0)
        rnd = int(st.get("round", 0))
        try:
            cands = json.loads(mr.tiling_candidates_json(json.dumps(st), pi, args.k, 0))
        except Exception as e:
            skipped += 1
            if skipped <= 3:
                print(f"  [skip] Stellung {i} (Runde {rnd}): {e}")
            continue
        if len(cands) < 2:
            continue
        n_multi += 1
        by_round[rnd] = by_round.get(rnd, 0) + 1

        pts = [c["points"] for c in cands]
        best_pts_i = max(range(len(cands)), key=lambda j: pts[j])

        # --- Task #21: Punkte + exakte Endwertung ---
        if rnd >= 5:
            tot = [c["points"] + c["end_scoring"] for c in cands]
            best_tot_i = max(range(len(cands)), key=lambda j: tot[j])
            if best_tot_i != best_pts_i:
                r5_diff += 1
                r5_gain.append(tot[best_tot_i] - tot[best_pts_i])

        # --- Task #20: Punkte x Value ---
        if 2 <= rnd <= 4:
            n_r24 += 1
            v = value_batch(model, encoder, [c["state"] for c in cands])  # tanh in [-1,1]
            wp = (v + 1.0) / 2.0                        # -> Gewinnwahrscheinlichkeit
            val_spread.append(float(wp.max() - wp.min()))
            prod = [pts[j] * float(wp[j]) for j in range(len(cands))]
            j_star = max(range(len(cands)), key=lambda j: prod[j])
            if j_star != best_pts_i:
                mult_diff += 1
                if pts[j_star] < pts[best_pts_i]:
                    strict_override += 1
                    override_margins.append(pts[best_pts_i] - pts[j_star])
        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{len(picked)} ...", flush=True)

    print("\n" + "=" * 70)
    print("  TILING-KANDIDATEN: aendert ein neues Kriterium ueberhaupt die Wahl?")
    print("=" * 70)
    print(f"  Stellungen mit >1 Kandidat: {n_multi} von {len(picked)}"
          f"{f' ({skipped} uebersprungen)' if skipped else ''}")
    print(f"  davon je Runde: {dict(sorted(by_round.items()))}")

    print("\n  --- Task #21: Runde 5, Punkte + EXAKTE Endwertung ---")
    n5 = by_round.get(5, 0)
    if n5 == 0:
        print("  KEINE Runde-5-Tiling-Stellungen im frozen set -- separat erheben noetig.")
    else:
        print(f"  andere Wahl als punktegierig: {r5_diff}/{n5} ({r5_diff/n5:.1%})")
        if r5_gain:
            print(f"  dabei gewonnene Punkte: Median {q(r5_gain,0.5):.1f}, "
                  f"Max {max(r5_gain)}, Ø {stats.mean(r5_gain):.2f}")

    print("\n  --- Task #20: Runden 2-4, Punkte x Value ---")
    if not val_spread:
        print("  KEINE Runde-2-4-Tiling-Stellungen mit Auswahl gefunden.")
    else:
        print(f"  Value-Spreizung unter den Kandidaten: Median {q(val_spread,0.5):.4f}, "
              f"IQR [{q(val_spread,0.25):.4f}, {q(val_spread,0.75):.4f}], Max {max(val_spread):.4f}")
        print(f"  andere Wahl als punktegierig: {mult_diff}/{n_r24} ({mult_diff/max(n_r24,1):.1%})")
        print(f"  davon ECHTE Kippungen eines Punktvorsprungs: {strict_override}/{n_r24} "
              f"(Rest sind Wechsel unter punktgleichen Kandidaten)"
              + (f", gekippte Differenz Median {q(override_margins,0.5):.1f}, Max {max(override_margins)}" if override_margins else ""))
        m = q(val_spread, 0.5)
        print(f"  Einordnung: eine Spreizung von {m:.3f} kippt bei einem 20-Punkte-Tiling "
              f"~{20 - 20/((0.5+m/2)/(0.5-m/2)) if m < 1 else float('nan'):.1f} Punkte")
    print("=" * 70)

    out = ROOT / args.out
    out.write_text(json.dumps({
        "model": args.model, "encoder": encoder, "frozen_set": args.frozen,
        "k": args.k, "n_states": len(picked), "n_multi": n_multi,
        "by_round": by_round, "n_skipped": skipped,
        "round5_diff": r5_diff, "round5_n": n5,
        "round5_gain_median": q(r5_gain, 0.5) if r5_gain else None,
        "round5_gain_max": max(r5_gain) if r5_gain else None,
        "value_spread_median": q(val_spread, 0.5) if val_spread else None,
        "value_spread_iqr": [q(val_spread, 0.25), q(val_spread, 0.75)] if val_spread else None,
        "mult_changes_choice": mult_diff, "n_rounds_2_4": n_r24,
        "strict_point_lead_overrides": strict_override,
        "override_margin_median": q(override_margins, 0.5) if override_margins else None,
        "override_margin_max": max(override_margins) if override_margins else None,
    }, indent=2), encoding="utf-8")
    print(f"\nErgebnis: {out}")


if __name__ == "__main__":
    main()
