# -*- coding: utf-8 -*-
"""Wirkungs-Probe (PREREG_ownership_corpus.md, Anti-Stillstand-Beweis fuer die
neu verdrahtete Bauer-Vorzug-Einspeisung in run_net_self_play).

EIN Arm pro Prozessaufruf (Pflicht, nicht Bequemlichkeit): MOSAIC_SPALTENBAU/
MOSAIC_PLATTENBAU werden in Rust je per `OnceLock` EINMAL je Prozess gelesen
(siehe spaltenbau.rs::active_env, plattenbauer.rs::modus_env) -- ein zweiter Arm
im selben Prozess wuerde den Knopf des ERSTEN Arms einfrieren. Deshalb: env
VOR dem `import mosaic_rust` setzen, ein Python-Interpreter je Arm.

Speichert die rohen Step-Records als .pkl nach data/corpus_probe/ (gleiches
Format wie self_play.py::_flush, aber bewusst NICHT in data/ oder
data/ownership_corpus/ -- Messdaten-Regel des laufenden Auftrags) und
zusaetzlich eine kompakte JSON-Zusammenfassung der End-Zustaende.
"""
from __future__ import annotations

import argparse
import json
import os
import pickle
import sys
from pathlib import Path

BASIS = Path(__file__).resolve().parent.parent
OUT_DIR = BASIS / "data" / "corpus_probe"


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--arm", required=True, help="Kuerzel, z.B. A/B/C/E/F")
    p.add_argument("--plattenbau", default=None, help="Wert fuer MOSAIC_PLATTENBAU (unset = aus)")
    p.add_argument("--spaltenbau", action="store_true", help="setzt MOSAIC_SPALTENBAU=1")
    p.add_argument("--model", default="models/alphazero_v21_2d_brierbest.onnx")
    p.add_argument("--n-games", type=int, default=30)
    p.add_argument("--sims", type=int, default=200)
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--threads", type=int, default=8)
    args = p.parse_args()

    # WICHTIG: vor jedem mosaic_rust-Import setzen (OnceLock-Cache s.o.).
    # MOSAIC_WERTUNG_STREUUNG_MAX bewusst NICHT gesetzt (Koordinator-Vorgabe:
    # "ein Faktor" -- Streuung bleibt fuer diese Probe aus).
    if args.plattenbau is not None:
        os.environ["MOSAIC_PLATTENBAU"] = args.plattenbau
    if args.spaltenbau:
        os.environ["MOSAIC_SPALTENBAU"] = "1"
    os.environ.pop("MOSAIC_WERTUNG_STREUUNG_MAX", None)

    import mosaic_rust as mr

    print(f"[{args.arm}] MOSAIC_SPALTENBAU={os.environ.get('MOSAIC_SPALTENBAU')!r} "
          f"MOSAIC_PLATTENBAU={os.environ.get('MOSAIC_PLATTENBAU')!r} "
          f"seed={args.seed} n_games={args.n_games} sims={args.sims}", file=sys.stderr)

    raw = mr.net_self_play_games(
        model_path=args.model,
        n_games=args.n_games,
        base_sims=args.sims,
        c_puct=1.5,
        seed=args.seed,
        num_threads=args.threads,
        prefix=f"corpusprobe_{args.arm}",
        add_root_noise=True,
        deterministic=False,
        record_rtv=False,
    )
    records = json.loads(raw)
    print(f"[{args.arm}] {len(records)} Step-Records erhalten.", file=sys.stderr)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pkl_path = OUT_DIR / f"selfplay_wirkungsprobe_{args.arm}_g{args.n_games}.pkl"
    with open(pkl_path, "wb") as f:
        pickle.dump(records, f)
    print(f"[{args.arm}] {len(records)} Records -> {pkl_path}", file=sys.stderr)

    # Letzter Record je Spiel (siehe tools/scoring_tile_impact.py-Moduldoku:
    # per Konstruktion der Zustand mit fertigem dome_grid, exakt fuer
    # end_scoring_from_state_json).
    games: dict = {}
    order: list = []
    for r in records:
        gid = r.get("game_id")
        if gid is None:
            # run_net_self_play haengt einen reinen Diagnose-Record ohne
            # game_id ans JSON-Array (siehe self_play.py:621 Kommentar) --
            # ueberspringen, kein echtes Spiel.
            continue
        if gid not in games:
            games[gid] = []
            order.append(gid)
        games[gid].append(r)

    finals = []
    n_incomplete = 0
    for gid in order:
        last = games[gid][-1]
        if not last.get("completed", True):
            n_incomplete += 1
            continue
        finals.append(last)

    summary_path = OUT_DIR / f"summary_wirkungsprobe_{args.arm}_g{args.n_games}.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({
            "arm": args.arm,
            "plattenbau_env": os.environ.get("MOSAIC_PLATTENBAU"),
            "spaltenbau_env": os.environ.get("MOSAIC_SPALTENBAU"),
            "seed": args.seed, "n_games": args.n_games, "sims": args.sims,
            "n_completed": len(finals), "n_incomplete": n_incomplete,
            "final_states": [
                {"game_id": r["game_id"], "state": r["state"],
                 "scores": r["scores"], "scores_unclamped": r["scores_unclamped"]}
                for r in finals
            ],
        }, f)
    print(f"[{args.arm}] {len(finals)}/{len(order)} komplett -> {summary_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
