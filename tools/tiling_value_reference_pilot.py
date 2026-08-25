# -*- coding: utf-8 -*-
"""tools/tiling_value_reference_pilot.py -- Task #20, Pilot.

## Die Frage

Bei `punkte * value` wirkt der Value-Head nachweislich NUR als Stichentscheid
unter punktgleichen Tiling-Abschluessen (gemessener Punkteverlust: exakt 0 in
allen Faellen). Bleibt die eigentliche Frage: rangiert er dort RICHTIG, oder ist
es Rauschen?

## Warum das nicht direkt messbar ist

Die Kandidaten-Zustaende stehen in der TILING-Phase. `net_search_with_tree`
liefert dort strukturell nichts -- der Orakel-Ansatz, der beim Drafting 8/8
getroffen hat, ist hier nicht anwendbar (geprueft: num_actions_considered=None).

## Der Umweg

Jeden Kandidaten ueber den Rundenuebergang in die naechste DRAFTING-Stellung
weiterschalten (`advance_after_tiling_json`), DORT die Tiefensuche als Referenz
laufen lassen. Der Nachfuell-Wurf ist der einzige Zufall; mit demselben Seed
fuer alle Kandidaten einer Stellung ist der Vergleich GEPAART -- der einzige
Unterschied bleibt das Brett.

## Was dieser Pilot liefert (und was nicht)

Er misst NICHT die Trefferquote -- dafuer ist er zu klein. Er misst die
STREUUNG der gepaarten Differenz ueber die Zufallsziehungen, damit sich
ausrechnen laesst, wie viele Ziehungen der volle Lauf braucht. Ohne diese Zahl
waere ein Nullergebnis nicht interpretierbar: es koennte am fehlenden Effekt
liegen oder an zu wenigen Ziehungen.

Signal zur Einordnung: die Value-Spreizung unter den Kandidaten betraegt im
Median 0,0216 (tools/tiling_candidate_spread.py).

## Vorbehalt

Die Tiefensuche nutzt an ihren Blaettern denselben Value-Head -- sie ist also
nicht unabhaengig, nur erheblich staerker (Suche verstaerkt). Dasselbe gilt fuer
das Drafting-Orakel, dessen Metriken sich trotzdem als Praediktoren bewaehrt
haben.
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

import torch  # noqa: E402

from config import INPUT_SIZE, MODELS_DIR, NUM_ACTIONS  # noqa: E402
from neural_net import (MosaicNet, points_dist_bins_from_state,  # noqa: E402
                        state_to_tensor)

FROZEN_PKL = ROOT / "evaluations" / "frozen_eval_set.pkl"


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
    ap.add_argument("--k", type=int, default=4, help="Kandidaten je Stellung")
    ap.add_argument("--draws", type=int, default=16, help="Zufallsziehungen je Kandidat")
    ap.add_argument("--n-states", type=int, default=25)
    ap.add_argument("--sims", type=int, default=2000)
    ap.add_argument("--out", default="evaluations/artifacts/tiling_value_reference_pilot.json")
    args = ap.parse_args()

    import mosaic_rust as mr

    model_path = str(MODELS_DIR / f"alphazero_{args.model}.onnx")
    ck = torch.load(str(MODELS_DIR / f"alphazero_{args.model}.pth"), map_location="cpu")
    net = MosaicNet(input_size=INPUT_SIZE, num_actions=NUM_ACTIONS,
                    hidden_size=ck.get("hidden_size", 512),
                    points_dist_bins=points_dist_bins_from_state(ck["model_state"]))
    net.load_state_dict(ck["model_state"], strict=False)
    net.eval()

    records = pickle.loads(FROZEN_PKL.read_bytes())["records"]
    til = [r for r in records
           if r["state"].get("phase") == "tiling" and 2 <= int(r["state"].get("round", 0)) <= 4]
    step = max(1, len(til) // args.n_states)
    picked = til[::step][:args.n_states]
    print(f"{len(picked)} Stellungen (Runde 2-4) | k={args.k} | {args.draws} Ziehungen | "
          f"{args.sims} Sims\n")

    paired_sd, per_draw_sd, agree, n_pairs, skipped = [], [], 0, 0, 0
    for idx, rec in enumerate(picked):
        st = rec["state"]
        pi = st.get("current_player", 0)
        try:
            cands = json.loads(mr.tiling_candidates_json(json.dumps(st), pi, args.k, 0))
        except Exception:
            skipped += 1
            continue
        if len(cands) < 2:
            continue
        # Nur PUNKTGLEICHE Kandidaten -- nur dort entscheidet der Value-Head.
        top = max(c["points"] for c in cands)
        cands = [c for c in cands if c["points"] == top]
        if len(cands) < 2:
            continue

        # Rohbewertung des Value-Heads (das, was die Auswahlregel benutzt)
        with torch.no_grad():
            wp = ((net(torch.stack([state_to_tensor(c["state"]) for c in cands]))[1]
                   .squeeze(-1).numpy()) + 1) / 2

        # Referenz: Tiefensuche NACH dem Rundenuebergang, je Ziehung gepaart
        ref = [[] for _ in cands]
        for d in range(args.draws):
            seed = 1000 + d
            for ci, c in enumerate(cands):
                try:
                    nxt = mr.advance_after_tiling_json(json.dumps(c["state"]), seed)
                    res = json.loads(mr.net_search_state_json(nxt, model_path, args.sims, 1.5, seed))
                    v = res.get("root_value")
                    if v is None:
                        ref[ci].append(float("nan"))
                    else:
                        # root_value gilt aus Sicht des im NAECHSTEN Zug ziehenden
                        # Spielers -- auf die Perspektive UNSERES Tiling-Spielers
                        # normieren, sonst waere die Rangfolge invertiert, sobald
                        # der Gegner die naechste Runde eroeffnet.
                        mover = res.get("current_player")
                        ref[ci].append(float(v) if mover == pi else 1.0 - float(v))
                except Exception:
                    ref[ci].append(float("nan"))
        # Nur Kandidatenpaare mit vollstaendigen Referenzen evaluate
        for a in range(len(cands)):
            for b in range(a + 1, len(cands)):
                da = [ref[a][d] - ref[b][d] for d in range(args.draws)
                      if ref[a][d] == ref[a][d] and ref[b][d] == ref[b][d]]
                if len(da) < 3:
                    continue
                n_pairs += 1
                paired_sd.append(stats.pstdev(da))
                per_draw_sd.append(stats.pstdev([x for x in ref[a] if x == x]))
                # stimmt die Richtung des Value-Heads mit der Referenz ueberein?
                if (wp[a] - wp[b]) * stats.mean(da) > 0:
                    agree += 1
        print(f"  {idx+1}/{len(picked)}  (Paare bisher {n_pairs})", flush=True)

    if not paired_sd:
        raise SystemExit("Keine auswertbaren Kandidatenpaare.")

    sd_p = q(paired_sd, 0.5)
    signal = 0.0216  # gemessene Value-Spreizung, tiling_candidate_spread.py
    print("\n" + "=" * 68)
    print("  PILOT: wieviele Ziehungen braucht der volle Lauf?")
    print("=" * 68)
    print(f"  punktgleiche Kandidatenpaare: {n_pairs}"
          f"{f'  ({skipped} Stellungen uebersprungen)' if skipped else ''}")
    print(f"  Streuung EINZELNER Referenzwerte : Median {q(per_draw_sd,0.5):.4f}")
    print(f"  Streuung der GEPAARTEN Differenz : Median {sd_p:.4f}   "
          f"IQR [{q(paired_sd,0.25):.4f}, {q(paired_sd,0.75):.4f}]")
    print(f"  Signal (Value-Spreizung)         : {signal:.4f}")
    if sd_p > 0:
        # Ziehungen, damit der Standardfehler der Differenz unter das halbe Signal faellt
        need = (2.0 * sd_p / signal) ** 2
        print(f"\n  -> Standardfehler < halbes Signal ab etwa M = {need:.0f} Ziehungen")
        print(f"     (bei M=4: SE {sd_p/2:.4f} | M=8: {sd_p/(8**0.5):.4f} | "
              f"M=16: {sd_p/4:.4f} | M=32: {sd_p/(32**0.5):.4f})")
    print(f"\n  Richtungsuebereinstimmung im Piloten: {agree}/{n_pairs} "
          f"({agree/n_pairs:.1%}) -- NUR Indikation, dafuer ist n zu klein.")
    print("=" * 68)

    (ROOT / args.out).write_text(json.dumps({
        "model": args.model, "k": args.k, "draws": args.draws, "sims": args.sims,
        "n_states": len(picked), "n_pairs": n_pairs,
        "paired_diff_sd_median": sd_p, "single_ref_sd_median": q(per_draw_sd, 0.5),
        "signal_value_spread": signal,
        "suggested_draws": (2.0 * sd_p / signal) ** 2 if sd_p > 0 else None,
        "agree": agree,
    }, indent=2), encoding="utf-8")
    print(f"\nErgebnis: {ROOT / args.out}")


if __name__ == "__main__":
    main()
