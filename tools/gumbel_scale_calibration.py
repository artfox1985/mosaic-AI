# -*- coding: utf-8 -*-
"""tools/gumbel_scale_calibration.py -- Task #18, Schritt 1: ist GUMBEL_C_SCALE
richtig kalibriert?

## Die Frage

`net_mcts.rs:1290`:  sigma(q) = (GUMBEL_C_VISIT + max_N) * GUMBEL_C_SCALE * q
mit c_visit = 50,0 und c_scale = 1,0.

Fuer die Zugwahl zaehlt nur die DIFFERENZ zwischen Kandidaten. An der Wurzel
konkurriert `sigma` gegen `ln(prior)`:

    score(a) = g(a) + ln(prior(a)) + sigma(q(a))

Der Quellcode begruendet c_scale = 1,0 (statt mctx-Default 0,1) damit, dass
unsere q bereits [0,1]-Gewinnwahrscheinlichkeiten sind und keine
Min-Max-Reskalierung brauchen. Diese Begruendung hat eine Luecke: mctx'
Min-Max-Normalisierung spannt die q der Kinder eines Knotens auf den VOLLEN
[0,1]-Bereich. Unsere ROHEN Gewinnwahrscheinlichkeiten spannen nur so weit, wie
sich die Stellungen tatsaechlich unterscheiden.

    mctx:  delta_sigma = (50+max_N) * 0,1 * delta_q_norm   mit delta_q_norm ~ 1,0
    unser: delta_sigma = (50+max_N) * 1,0 * delta_q_roh    mit delta_q_roh = ?

Bei delta_q_roh ~ 0,05 liegen beide in derselben Groessenordnung, die
Kalibrierung waere vertretbar. Bei ~0,01 ist unser sigma deutlich zu SCHWACH
(der Prior dominiert), bei ~0,3 deutlich zu STARK (q ueberfaehrt den Prior).

Die Antwort haengt also an EINER nie gemessenen Groesse: der tatsaechlichen
Spannweite der completed-q unter den Wurzelkandidaten.

## Was gemessen wird

Ueber `mosaic_rust.net_search_state_json_trace` auf echten Stellungen aus dem
frozen set (dieselbe Quelle wie die Orakel-Labels, also ohne neue Datenerhebung):

  * delta_q       -- Spannweite und IQR der q unter den Kandidaten je Phase
  * delta_lnprior -- Spannweite von ln(prior) unter denselben Kandidaten
  * max_N         -- Besuchszahl zum Entscheidungszeitpunkt (prueft zugleich die
                     Schaetzung max_N ~ 93 aus Sequential Halving:
                     16 Kandidaten, 400 Sims -> 6+12+25+50)
  * Verhaeltnis   -- delta_sigma / delta_lnprior, also wie schwer q gegenueber
                     dem Prior wiegt. Das ist die eigentliche Kennzahl.

Daraus faellt der sinnvolle c_scale-Bereich direkt ab: soll q etwa gleich schwer
wiegen wie der Prior, ist c_scale_ziel = c_scale_ist / Verhaeltnis.

## Danach

EIN gezielter Arena-A/B (c_scale 1,0 gegen den hier abgeleiteten Wert) statt
einer blinden Sprossenleiter. Regeln in evaluations/PREREG_ownership_gumbel.md.
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

FROZEN_PKL = ROOT / "evaluations" / "frozen_eval_set.pkl"
ORACLE_JSON = ROOT / "evaluations" / "artifacts" / "frozen_v1_oracle_labels.json"

# Muss zu net_mcts.rs:1218/1219 passen -- hier nur zum Zurueckrechnen.
C_VISIT = 50.0
C_SCALE = 1.0


def quantile(xs, q):
    if not xs:
        return float("nan")
    s = sorted(xs)
    i = (len(s) - 1) * q
    lo, hi = int(i), min(int(i) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (i - lo)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--model", default="v18_best")
    p.add_argument("--sims", type=int, default=400)
    p.add_argument("--n-states", type=int, default=150)
    p.add_argument("--out", default="evaluations/artifacts/gumbel_scale_calibration.json")
    args = p.parse_args()

    import mosaic_rust as mr

    labels = json.loads(ORACLE_JSON.read_text(encoding="utf-8"))["labels"]
    records = pickle.loads(FROZEN_PKL.read_bytes())["records"]
    # Gleichmaessig ueber die gelabelten (= sauberen Drafting-)Zustaende ziehen,
    # damit alle Runden vertreten sind -- deterministisch, kein RNG.
    step = max(1, len(labels) // args.n_states)
    picked = labels[::step][:args.n_states]
    model_path = str(ROOT / "models" / f"alphazero_{args.model}.onnx")
    print(f"Modell {args.model} @ {args.sims} Sims | {len(picked)} Zustaende "
          f"(aus {len(labels)} gelabelten)\n")

    dq_all, dlp_all, maxn_all, ratio_all, per_round = [], [], [], [], {}
    skipped = 0
    for k, lbl in enumerate(picked):
        state = records[lbl["record_index"]]["state"]
        rnd = state.get("round", 0)
        try:
            res = json.loads(mr.net_search_state_json_trace(
                json.dumps(state), model_path, args.sims, 1.5, 12345 + k))
        except Exception as e:
            skipped += 1
            if skipped <= 3:
                print(f"  [skip] Zustand {k}: {e}")
            continue
        tr = res.get("gumbel_trace")
        if not tr or not tr.get("phases"):
            skipped += 1
            continue
        # LETZTE Phase = Entscheidungszeitpunkt (hoechste Besuchszahlen).
        cands = [c for c in tr["phases"][-1].get("candidates", []) if c.get("visits", 0) > 0]
        if len(cands) < 2:
            skipped += 1
            continue
        qs = [c["q"] for c in cands]
        max_n = max(c["visits"] for c in cands)
        dq = max(qs) - min(qs)
        # ln(prior) MUSS ueber DIESELBE Kandidatenmenge gehen wie delta_q.
        # Erster Anlauf nahm alle 16 top_m -- darin stecken sehr unwahrscheinliche
        # Aktionen mit stark negativem ln(prior), was die Prior-Spannweite
        # aufblaeht und die Prior-Dominanz massiv ueberzeichnet (gemessen:
        # Faktor 20 statt des tatsaechlichen Werts). Daher ueber die
        # `description` auf die Ueberlebenden der letzten Phase einschraenken.
        prior_by_desc = {c["description"]: c.get("ln_prior")
                         for c in tr.get("top_m_selection", [])
                         if c.get("ln_prior") is not None}
        lps = [prior_by_desc[c["description"]] for c in cands
               if c.get("description") in prior_by_desc]
        dlp = (max(lps) - min(lps)) if len(lps) >= 2 else float("nan")

        d_sigma = (C_VISIT + max_n) * C_SCALE * dq
        ratio = d_sigma / dlp if dlp and dlp == dlp and dlp > 1e-9 else float("nan")

        dq_all.append(dq); maxn_all.append(max_n)
        if dlp == dlp:
            dlp_all.append(dlp)
        if ratio == ratio:
            ratio_all.append(ratio)
            per_round.setdefault(rnd, []).append(ratio)
        if (k + 1) % 25 == 0:
            print(f"  {k+1}/{len(picked)} ...", flush=True)

    if not dq_all:
        raise SystemExit("Keine auswertbaren Zustaende.")

    print("\n" + "=" * 68)
    print("  GUMBEL-KALIBRIERUNG (Wurzel, letzte Sequential-Halving-Phase)")
    print("=" * 68)

    def line(name, xs, fmt="{:.4f}"):
        if not xs:
            print(f"  {name:<26} --")
            return
        print(f"  {name:<26} Median {fmt.format(quantile(xs,0.5))}   "
              f"IQR [{fmt.format(quantile(xs,0.25))}, {fmt.format(quantile(xs,0.75))}]   "
              f"Ø {fmt.format(stats.mean(xs))}")

    line("delta_q (Spannweite)", dq_all)
    line("delta_ln(prior)", dlp_all)
    line("max_N", [float(x) for x in maxn_all], "{:.1f}")
    line("delta_sigma / delta_lnprior", ratio_all, "{:.2f}")

    med_ratio = quantile(ratio_all, 0.5) if ratio_all else float("nan")
    med_maxn = quantile([float(x) for x in maxn_all], 0.5)
    print("\n" + "-" * 68)
    print(f"  max_N-Schaetzung aus Sequential Halving war ~93 -> gemessen {med_maxn:.0f}")
    if med_ratio == med_ratio and med_ratio > 0:
        print(f"  q wiegt derzeit das {med_ratio:.2f}-Fache des Priors.")
        print(f"  Fuer GLEICHES Gewicht waere c_scale = {C_SCALE/med_ratio:.3f}")
        if med_ratio > 3:
            print("  -> q DOMINIERT den Prior deutlich. Kandidat fuer den A/B: kleineres c_scale.")
        elif med_ratio < 0.33:
            print("  -> Der PRIOR dominiert q deutlich. Kandidat fuer den A/B: groesseres c_scale.")
        else:
            print("  -> Beide in derselben Groessenordnung. Die Begruendung im Quellcode")
            print("     traegt damit -- ein A/B hat geringe Aussicht, etwas zu finden.")
    if per_round:
        print("\n  Verhaeltnis je Runde (Median):")
        for r in sorted(per_round):
            print(f"    Runde {r}: {quantile(per_round[r],0.5):.2f}   (n={len(per_round[r])})")
    print("=" * 68)
    if skipped:
        print(f"\n  {skipped} Zustaende uebersprungen (kein verwertbarer Trace).")

    out = ROOT / args.out
    out.write_text(json.dumps({
        "model": args.model, "sims": args.sims, "n_used": len(dq_all), "n_skipped": skipped,
        "c_visit": C_VISIT, "c_scale": C_SCALE,
        "delta_q_median": quantile(dq_all, 0.5),
        "delta_lnprior_median": quantile(dlp_all, 0.5) if dlp_all else None,
        "max_n_median": med_maxn,
        "ratio_sigma_over_prior_median": med_ratio,
        "c_scale_for_equal_weight": (C_SCALE / med_ratio) if med_ratio and med_ratio == med_ratio else None,
        "ratio_by_round": {str(r): quantile(v, 0.5) for r, v in per_round.items()},
    }, indent=2), encoding="utf-8")
    print(f"\nErgebnis: {out}")


if __name__ == "__main__":
    main()
