# -*- coding: utf-8 -*-
"""tools/gating_block_z.py -- Block-z je Tor-1-Seed und gepoolt, aus paired_gating-Artefakten.

Die Rechnung ist die aus `PREREG_v32_window.md` par.10: Siegeranteil von A je Seed-Block
(DIFFERENZIERT -- die Felder in `blocks[]` sind kumulativ, `docs/pitfalls.md`), dann
z = (Mittel - 0,5) / (sd / sqrt(Bloecke)). Die Bloecke kommen aus
`elo_tracker.units_from_paired_artifact`, das sie aus `per_pair_scores` gruppiert und gegen
`a_wins_total`/`n_games_total` prueft -- dieselbe Quelle wie die Registerzeilen.

Anlass (2026-09-25): die gestufte Tor-1-Regel aus `PREREG_v33_window.md` par.2a braucht
Block-z je Seed MASCHINELL, um zu entscheiden, ob ein dritter Seed laeuft. Die Zahlen der
v32-Prereg entstanden mit einer Rechnung ausserhalb des Baums; diese hier ist an ihnen
geeicht. Die Eichung laeuft als `--check-v31-v32` gegen die Artefakte selbst und NICHT als
Test in `tools/tests`: `evaluations/artifacts` ist nicht im Repo, ein frischer Klon haette sie nicht.

    python tools/gating_block_z.py <artefakt.json> [<artefakt.json> ...]
    python tools/gating_block_z.py --check-v31-v32
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from elo_tracker import units_from_paired_artifact  # noqa: E402

# Registriert in PREREG_v31_window.md par.6 und PREREG_v32_window.md par.10.
CALIBRATION = {
    "evaluations/artifacts/gating_v31-b01_vs_v30-b02_s20261400.json": 3.54,
    "evaluations/artifacts/gating_v31-b01_vs_v30-b02_s20261401.json": 2.42,
    "evaluations/artifacts/gating_v32-b01_vs_v31-b01_s20261500.json": 0.10,
    "evaluations/artifacts/gating_v32-b01_vs_v31-b01_s20261501.json": 3.26,
}
CALIBRATION_POOLED = {("v31", 4.24), ("v32", 2.37)}


def block_shares(path: str) -> list[float]:
    """Siegeranteil von A je Seed-Block, in Reihenfolge des Laufs."""
    k, ws = units_from_paired_artifact(path).split(":")
    size = int(k)
    return [int(w) / size for w in ws.split(",")]


def block_z(shares: list[float]) -> dict:
    """Code-Review 2 (2026-10-02) Befund 3: zwei Randfaelle teilten durch null, ausgerechnet beim
    deutlichsten Ergebnis. Ein Block allein hat keine Streuung (z = None, nicht berechenbar); sind alle
    Bloecke gleich (sd = 0), ist z unendlich mit dem Vorzeichen der Abweichung von 0,5 (bzw. 0, wenn
    alle Bloecke genau 0,5 sind). `json.dumps` schreibt das als `Infinity`, das `json.loads` liest."""
    n = len(shares)
    if n == 0:
        return {"blocks": 0, "mean": None, "sd": None, "z": None}
    mean = sum(shares) / n
    if n < 2:
        return {"blocks": n, "mean": mean, "sd": None, "z": None}
    sd = math.sqrt(sum((s - mean) ** 2 for s in shares) / (n - 1))
    if sd == 0:
        z = 0.0 if mean == 0.5 else math.copysign(math.inf, mean - 0.5)
    else:
        z = (mean - 0.5) / (sd / math.sqrt(n))
    return {"blocks": n, "mean": mean, "sd": sd, "z": z}


def _fmt(v, spec: str) -> str:
    return "n/b" if v is None else format(v, spec)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("artifacts", nargs="*")
    ap.add_argument("--check-v31-v32", action="store_true",
                    help="Eichung gegen die registrierten Werte von v31 und v32")
    ap.add_argument("--json", action="store_true", help="Ergebnis als eine JSON-Zeile")
    args = ap.parse_args()

    if args.check_v31_v32:
        bad = 0
        pools = {"v31": [], "v32": []}
        for rel, want in CALIBRATION.items():
            sh = block_shares(str(ROOT / rel))
            got = block_z(sh)["z"]
            pools["v31" if "v31-b01_vs" in rel else "v32"].extend(sh)
            ok = round(got, 2) == want
            bad += not ok
            print(f"{'ok ' if ok else 'ROT'} {rel.split('/')[-1]}: z {got:+.2f} (registriert {want:+.2f})")
        for gen, want in sorted(CALIBRATION_POOLED):
            got = block_z(pools[gen])["z"]
            ok = round(got, 2) == want
            bad += not ok
            print(f"{'ok ' if ok else 'ROT'} {gen} gepoolt: z {got:+.2f} (registriert {want:+.2f})")
        return 1 if bad else 0

    if not args.artifacts:
        ap.error("mindestens ein Artefakt oder --check-v31-v32")
    per, pooled = [], []
    for p in args.artifacts:
        sh = block_shares(p)
        pooled.extend(sh)
        per.append({"artifact": p, **block_z(sh)})
    result = {"per_seed": per, "pooled": block_z(pooled)}
    if args.json:
        print(json.dumps(result))
    else:
        for r in per:
            print(f"{r['artifact']}: Bloecke {r['blocks']}, Mittel {_fmt(r['mean'], '.4f')}, "
                  f"sd {_fmt(r['sd'], '.4f')}, z {_fmt(r['z'], '+.2f')}")
        q = result["pooled"]
        print(f"gepoolt: Bloecke {q['blocks']}, Mittel {_fmt(q['mean'], '.4f')}, sd {_fmt(q['sd'], '.4f')}, "
              f"z {_fmt(q['z'], '+.2f')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
