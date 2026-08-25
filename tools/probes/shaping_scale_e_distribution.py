# -*- coding: utf-8 -*-
"""Verteilung von `E` je Kriterium und je RUNDE -- Vorbedingung zweier Preregs.

ZWECK 1 (`PREREG_shaping_scale_per_round.md` par.6, deren eigene Vorbedingung):
ein kleinerer Nenner bringt Saettigung mit sich. Entscheidungsregel dort: liegt
das 90-%-Quantil von `E_r / SCALE_r` unter 1,0, traegt ein gemeinsames Profil.

ZWECK 2 (`PREREG_ownership_coupling.md` par.6.3.1, Beifang): in Runde 1 ist `q`
mit und ohne Ownership-Regler BITGLEICH (40/40 Stellungen). Ist `E` dort
ueberhaupt null -- oder ist `E` normal und der Shift kommt nur nicht an? Das
sind zwei sehr verschiedene Ursachen, und nur die erste wuerde ein
rundenabhaengiger Nenner heilen.

FELDINDIZIERUNG NICHT GERATEN: `scoring.rs:422/432` --
`idx(r,c) = (r//2)*12 + (c//2)*4 + (r%2)*2 + (c%2)`. Ein Indexfehler waere hier
still und wuerde als Verteilungsbefund fehlgelesen.

Nur die GEOMETRIE-Kriterien werden gerechnet (k0/k1/k2). k4/k6 haengen an den
gelegten Kuppelslots und brauchen den Brettzustand, k3/k5/k7 an Atomen bzw.
Farbinformation -- die gehoeren in eine eigene Messung.

    python -X utf8 tools/probes/shaping_scale_e_distribution.py --n-states 400
"""
from __future__ import annotations

import argparse
import glob
import json
import pickle
import statistics
import sys
from collections import defaultdict
from pathlib import Path

BASIS = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASIS))
sys.path.insert(0, str(BASIS / "engine" / "py"))

# Profil aus PREREG_shaping_scale_per_round.md par.4
SCALE_FLAT = 50.0
PROFIL = {1: 0.083, 2: 0.172, 3: 0.327, 4: 0.515, 5: 0.825}


def idx(r: int, c: int) -> int:
    return (r // 2) * 12 + (c // 2) * 4 + (r % 2) * 2 + (c % 2)


def e_geometrie(p) -> dict[str, float]:
    """k0 Reihen (+3), k1 Spalten (+7), k2 Diagonalen (+10) -- Formen aus
    `scoring.rs::expected_plate_points`, Zweige 0/1/2."""
    prod = lambda xs: statistics.prod(xs) if hasattr(statistics, "prod") else __import__("math").prod(xs)
    k0 = sum(prod([p[idx(r, c)] for c in range(6)]) for r in range(6)) * 3.0
    k1 = sum(prod([p[idx(r, c)] for r in range(6)]) for c in range(6)) * 7.0
    d0 = prod([p[idx(i, i)] for i in range(6)])
    d1 = prod([p[idx(i, 5 - i)] for i in range(6)])
    k2 = (d0 + d1) * 10.0
    return {"k0": k0, "k1": k1, "k2": k2}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default="models/alphazero_v21-b18_best.pth")
    ap.add_argument("--states", default="data/holdout/*.pkl")
    ap.add_argument("--n-states", type=int, default=400)
    ap.add_argument("--je-partie", type=int, default=3)
    a = ap.parse_args()

    import torch  # noqa: PLC0415
    from neural_net import build_model_from_checkpoint, state_to_planes, state_to_tensor  # noqa: PLC0415

    ck = torch.load(str(BASIS / a.model), map_location="cpu", weights_only=False)
    modell, _enc = build_model_from_checkpoint(ck)
    modell.eval()

    proben = []
    gesehen: dict = {}
    for f in sorted(glob.glob(str(BASIS / a.states))):
        try:
            data = pickle.load(open(f, "rb"))
        except Exception:  # noqa: BLE001
            continue
        for s in data:
            st = s.get("state") or {}
            if st.get("phase") != "drafting":
                continue
            # Je (Partie, RUNDE) begrenzen -- sonst liefert der Lauf nur Runde 1,
            # weil die ersten Drafting-Stellungen einer Partie alle dort liegen.
            g = (f, s.get("game_id"), st.get("round"))
            if gesehen.get(g, 0) >= a.je_partie:
                continue
            gesehen[g] = gesehen.get(g, 0) + 1
            proben.append(st)
            if len(proben) >= a.n_states:
                break
        if len(proben) >= a.n_states:
            break
    print(f"  {len(proben)} Drafting-Zustaende aus {len(gesehen)} Partien ({a.states})")
    if not proben:
        raise SystemExit("keine Zustaende")

    je_runde = defaultdict(lambda: defaultdict(list))
    with torch.no_grad():
        for st in proben:
            flat = state_to_tensor(st).float().unsqueeze(0)
            planes = state_to_planes(st).float().unsqueeze(0)
            out = modell(planes, flat)
            own = torch.sigmoid(out[4])[0].cpu().numpy()
            cp = st.get("current_player", 0)
            p = own[0:36]  # Ego-Haelfte, ego-perspektivisch (neural_net.py:1825-1840)
            for k, v in e_geometrie(p).items():
                je_runde[st.get("round") or 0][k].append(float(v))
            je_runde[st.get("round") or 0]["_cp"].append(cp)

    def q90(xs):
        xs = sorted(xs)
        return xs[min(len(xs) - 1, int(0.9 * len(xs)))]

    print()
    print("  Runde |   n | Kriterium |   Median E |    90%-E | SCALE_r | 90%-E/SCALE_r")
    print("  ------+-----+-----------+------------+----------+---------+--------------")
    ergebnis = {}
    for rd in sorted(je_runde):
        sc = SCALE_FLAT * PROFIL.get(rd, 1.0)
        n = len(je_runde[rd]["k1"])
        for k in ("k0", "k1", "k2"):
            xs = je_runde[rd][k]
            if not xs:
                continue
            verh = q90(xs) / sc
            ergebnis[f"r{rd}_{k}"] = {"n": n, "median": statistics.median(xs),
                                      "q90": q90(xs), "scale_r": sc, "q90_durch_scale": verh}
            print(f"  {rd:5} | {n:3} | {k:9} | {statistics.median(xs):10.4f} | "
                  f"{q90(xs):8.4f} | {sc:7.1f} | {verh:12.4f}")

    ueber = [k for k, v in ergebnis.items() if v["q90_durch_scale"] >= 1.0]
    print()
    print(f"  Vorabregel par.6 (90%-Quantil E_r/SCALE_r < 1,0): "
          f"{'ERFUELLT' if not ueber else 'VERLETZT bei ' + ', '.join(ueber)}")
    r1 = [v for k, v in ergebnis.items() if k.startswith("r1_")]
    if r1:
        print(f"  Runde-1-Frage: E ist dort NICHT null (Median k1 "
              f"{ergebnis.get('r1_k1', {}).get('median', float('nan')):.4f}) "
              f"-- die Bitgleichheit hat also eine ANDERE Ursache als E=0."
              if ergebnis.get("r1_k1", {}).get("median", 0) > 1e-9 else
              "  Runde-1-Frage: E ist dort ~0 -- Nenner-Profil koennte greifen.")

    (BASIS / "evaluations" / "artifacts" / "probe_shaping_e_distribution.json").write_text(
        json.dumps({"model": a.model, "states": a.states, "n": len(proben),
                    "profil": PROFIL, "ergebnis": ergebnis}, indent=1, ensure_ascii=False),
        encoding="utf-8")
    print("\n  geschrieben: evaluations/probe_shaping_e_distribution.json")


if __name__ == "__main__":
    main()
