# -*- coding: utf-8 -*-
"""Verteilung der Pfad-A-Eingangsgroessen des Wertungs-Shapings je Runde.

Vorbedingung aus `PREREG_shaping_scale_per_round.md` par.6: VOR jeder Zeile
Umbau-Code die Verteilung von `E` je Pfad und je Runde messen. Pfad B
(Ownership-Kopf) ist gemessen (par.3a, `shaping_scale_e_distribution.py`);
diese Sonde liefert die noch fehlende PFAD-A-Seite (Engine-Groessen).

Quelle ist der Read-only-Export `mosaic_rust.wertung_shaping_e_json` -- er
rechnet exakt die Groessen, die in `apply_wertung_shaping_full`
(`net_mcts.rs:1462-1487`) in `bei(x) = tanh(x / WERTUNG_SHAPING_SCALE)`
eingehen: `wertung_progress_per_kriterium` je Kriterium (Laufzeit-Alphas,
`round_gain = 0` wie in der Prereg registriert), `unlock_progress_beta` (k6,
zahlt ungegatet), `projected_unplaceable_penalty` (Strafleisten-Gegenterm,
`MOSAIC_WERTUNG_FLOOR_W` Default 0,0 -- NICHT zu verwechseln mit
`MOSAIC_FLOOR_SHAPING_W` = 0,3, das ist eine andere Korrektur am
Netz-Blattwert; Regel-0-Korrektur 2026-08-19, par.6a) und
`tiling_potenzial`.

Entscheidungsregel par.6: liegt das 90-%-Quantil von `E_r / SCALE_r` in beiden
Pfaden unter 1,0, traegt ein gemeinsames Profil; sonst getrennte Profile.

    python -X utf8 tools/probes/shaping_scale_pfad_a_e.py --n-states 600
"""
from __future__ import annotations

import argparse
import glob
import json
import pickle
import statistics
from collections import defaultdict
from pathlib import Path

BASIS = Path(__file__).resolve().parents[2]

# Profil aus PREREG_shaping_scale_per_round.md par.4
SCALE_FLAT = 50.0
PROFIL = {1: 0.083, 2: 0.172, 3: 0.327, 4: 0.515, 5: 0.825}

# Terme des Pfads A. `wertung_e[k]` zaehlt nur, wenn Platte k liegt
# (`net_mcts.rs:1462`, Schleife ueber `scoring_tile_ids`); `unlock_beta`,
# `floor_penalty` und `tiling_potenzial` gehen plattenunabhaengig ein.
KRITERIEN = [f"k{i}" for i in range(8)]


def q90(xs: list[float]) -> float:
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(0.9 * len(xs)))]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--states", default="data/holdout/*.pkl")
    ap.add_argument("--n-states", type=int, default=600)
    ap.add_argument("--je-partie", type=int, default=1)
    a = ap.parse_args()

    import mosaic_rust as mr  # noqa: PLC0415

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
            g = (f, s.get("game_id"), st.get("round"))
            if gesehen.get(g, 0) >= a.je_partie:
                continue
            gesehen[g] = gesehen.get(g, 0) + 1
            proben.append(st)
            if len(proben) >= a.n_states:
                break
        if len(proben) >= a.n_states:
            break
    print(f"  {len(proben)} Drafting-Zustaende aus {len(gesehen)} (Partie, Runde)-Zellen ({a.states})")
    if not proben:
        raise SystemExit("keine Zustaende")

    je_runde: dict = defaultdict(lambda: defaultdict(list))
    for st in proben:
        pi = st.get("current_player", 0)
        try:
            e = json.loads(mr.wertung_shaping_e_json(json.dumps(st), pi))
        except Exception:  # noqa: BLE001
            continue
        rd = e["round"]
        aktiv = set(int(x) for x in e["active_tile_ids"])
        z = je_runde[rd]
        for k in range(8):
            # nur wenn die Platte liegt -- nur dann geht der Term ins Shaping ein
            if k in aktiv:
                z[f"k{k}"].append(float(e["wertung_e"][k]))
        z["unlock_beta"].append(float(e["unlock_beta"]))
        z["floor_penalty"].append(abs(float(e["floor_penalty"])))
        z["tiling_potenzial"].append(abs(float(e["tiling_potenzial"])))

    print()
    print("  Runde | Term            |   n | Median E |    90%-E | SCALE_r | 90%-E/SCALE_r")
    print("  ------+-----------------+-----+----------+----------+---------+--------------")
    ergebnis = {}
    for rd in sorted(je_runde):
        sc = SCALE_FLAT * PROFIL.get(rd, 1.0)
        for term in KRITERIEN + ["unlock_beta", "floor_penalty", "tiling_potenzial"]:
            xs = je_runde[rd].get(term) or []
            if not xs:
                continue
            verh = q90(xs) / sc
            ergebnis[f"r{rd}_{term}"] = {"n": len(xs), "median": statistics.median(xs),
                                         "q90": q90(xs), "scale_r": sc,
                                         "q90_durch_scale": verh}
            print(f"  {rd:5} | {term:15} | {len(xs):3} | {statistics.median(xs):8.3f} | "
                  f"{q90(xs):8.3f} | {sc:7.1f} | {verh:12.4f}")

    ueber = [k for k, v in ergebnis.items() if v["q90_durch_scale"] >= 1.0]
    print()
    print(f"  Vorabregel par.6, Pfad A (90%-Quantil E_r/SCALE_r < 1,0): "
          f"{'ERFUELLT' if not ueber else 'VERLETZT bei ' + ', '.join(ueber)}")
    print("  Hinweis: alle Pfad-A-Gewichte sind per Default 0 (auch der"
          " Strafleisten-Term, MOSAIC_WERTUNG_FLOOR_W) -- ein Profil aendert"
          " kein Live-Verhalten. Korrektur 2026-08-19, siehe par.6a.")

    (BASIS / "evaluations" / "probe_shaping_e_distribution_pfad_a.json").write_text(
        json.dumps({"states": a.states, "n": len(proben), "profil": PROFIL,
                    "ergebnis": ergebnis}, indent=1, ensure_ascii=False),
        encoding="utf-8")
    print("\n  geschrieben: evaluations/probe_shaping_e_distribution_pfad_a.json")


if __name__ == "__main__":
    main()
