# -*- coding: utf-8 -*-
"""PREREG_heuristic_v2_long_rows.md par.3b.11 -- Messung DAgger-Runde 2.

Liest den Messkorpus `data/selfplay_otw22b06w00_*.pkl` (200 Partien
argmax-Instrument, Seed 20260828, 10 Bloecke a 20 Partien) und paart ihn
blockweise gegen die GESPEICHERTEN b05-w0-Bloecke aus
`evaluations/artifacts/gelaender_ladder_b05.json` (Seeds identisch;
Lehre 2026-08-29: Blockwerte gehoeren ins Artefakt, damit eine
quer-Modell-Paarung die Rohdaten nicht braucht).

Tor (par.3b.11, wie par.3b.9): volle Spalten Block-t > 2,262 (df=9) OHNE
signifikanten Punkteverlust; der Punkte-t wird beidseitig berichtet.
Dazu die sechs Standard-Kennzahlen (CLAUDE.md 2026-08-23) via
`eval_arm` aus ownership_tiling_consumer_eval.

Aufruf (reine Datenpassage, kein Netz, keine Engine):
    python -u tools/probes/dagger_round2_eval.py
Smoke:
    python -u tools/probes/dagger_round2_eval.py --limit 2
(Smoke rechnet keine Paarung -- Blockzahl passt dann nicht.)
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "tools" / "probes"))

from ownership_tiling_consumer_eval import eval_arm, paired_t, T_THRESHOLD  # noqa: E402

PREFIX = "selfplay_otw22b06w00_"
REFERENCE = _ROOT / "evaluations" / "artifacts" / "gelaender_ladder_b05.json"
REFERENCE_ARM = "w0"
ARTIFACT = _ROOT / "evaluations" / "artifacts" / "dagger_round2_b06.json"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--limit", type=int, default=None,
                    help="nur die ersten N Dateien (Smoke, ohne Paarung)")
    args = ap.parse_args()
    t0 = time.time()

    ref = json.load(open(REFERENCE, encoding="utf-8"))
    ref_arm = ref["arme"][REFERENCE_ARM]
    ref_full = ref_arm["blocks_full"]
    ref_pts = ref_arm["blocks_pts"]

    print(f"Messkorpus {PREFIX}*:", flush=True)
    r = eval_arm(PREFIX, args.limit)
    if r is None:
        raise SystemExit(f"keine Dateien fuer {PREFIX}")
    blocks = r.pop("_blocks")

    result = {
        "prereg": "PREREG_heuristic_v2_long_rows.md par.3b.11",
        "modell": "alphazero_v22-b06",
        "referenz": {
            "artefakt": REFERENCE.name,
            "arm": REFERENCE_ARM,
            "volle_spalten": ref_arm["full"],
            "punkte": ref_arm["pts"],
        },
        "instrument": "self_play.py --mode network --deterministic "
                      "--no-root-noise --sims 400 --games 200 --per-file 20 "
                      "--seed 20260828 --threads 11 (argmax, wie par.3b.2)",
        "schwelle_t": T_THRESHOLD,
        "b06": r,
        "b06_blocks": blocks,
    }

    if len(blocks) == len(ref_full):
        cmp_out = {}
        for metric, vals, ref_vals in (
                ("volle_spalten", [b["full_cols"] for b in blocks], ref_full),
                ("punkte", [b["points"] for b in blocks], ref_pts)):
            t, d, se = paired_t(vals, ref_vals)
            cmp_out[f"{metric}_vs_b05"] = {"delta": d, "se": se, "t": t}
        identical = all(abs(b["full_cols"] - rf) < 1e-12
                        and abs(b["points"] - rp) < 1e-12
                        for b, rf, rp in zip(blocks, ref_full, ref_pts))
        cmp_out["waechter_zahlengleich_mit_b05"] = identical
        vs = cmp_out["volle_spalten_vs_b05"]
        pt = cmp_out["punkte_vs_b05"]
        cmp_out["tor_bestanden"] = (vs["t"] > T_THRESHOLD
                                    and pt["t"] > -T_THRESHOLD)
        result["vergleich"] = cmp_out
    else:
        result["vergleich"] = {
            "fehler": f"Blockzahl {len(blocks)} != Referenz {len(ref_full)}"}

    result["laufzeit"] = {
        "wanduhr_s": round(time.time() - t0, 1), "cpu_s": None,
        "threads": 1, "s_je_partie": None,
    }

    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    with open(ARTIFACT, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=1, ensure_ascii=False)
    print(f"\nArtefakt geschrieben: {ARTIFACT}", flush=True)

    if "fehler" not in result["vergleich"]:
        vs = result["vergleich"]["volle_spalten_vs_b05"]
        pt = result["vergleich"]["punkte_vs_b05"]
        print(f"b06 vs b05: volle Spalten {r['volle_spalten']:.4f} "
              f"(delta {vs['delta']:+.4f}, t {vs['t']:+.2f}) | Punkte "
              f"{r['standard_kennzahlen']['eigene_punkte']:.2f} "
              f"(delta {pt['delta']:+.2f}, t {pt['t']:+.2f}) | Tor: "
              f"{result['vergleich']['tor_bestanden']}", flush=True)


if __name__ == "__main__":
    main()
