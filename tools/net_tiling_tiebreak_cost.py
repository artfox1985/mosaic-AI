# -*- coding: utf-8 -*-
"""tools/net_tiling_tiebreak_cost.py -- Task #20, Kostenmessung.

Misst die reale Wanduhrzeit EINES `PyGame.ai_tiling_step()`-Aufrufs (der
tatsaechliche Python-Bindungspfad, `engine/src/py.rs::ai_tiling_step`) an
echten Runde-2-4-Tiling-Entscheidungspunkten, mit geladenem Netz.

Erwartung laut Implementierungsplan: `NET_TILING_TIEBREAK_ENABLED=true` fuegt
bis zu `NET_TILING_TOPK` (12) zusaetzliche Netz-Forward-Paesse pro Tiling-Zug
hinzu (ueber `top_k_tilings`/`best_first_step_valued`) -- sollte im
einstelligen ms-Bereich zusaetzlich liegen.

## Warum kein direkter State-Import aus `frozen_eval_set.pkl`

`PyGame` (py.rs) hat keinen Konstruktor, der einen beliebigen JSON-Zustand
laedt (`PyGame::new` startet immer eine frische Partie) -- anders als die
`*_json`-freien Funktionen (`tiling_candidates_json` etc.), die einen rohen
`state_json`-String nehmen. Um den ECHTEN `ai_tiling_step`-Pfad zu treffen
(darum geht es hier, nicht um den Solver isoliert), wird deshalb eine echte
Partie bis zum ersten Runde-2-4-Tiling-Entscheidungspunkt netzgefuehrt
durchgespielt (`ai_start_tile_json` + `ai_drafting_net_step`), dort GENAU EIN
`ai_tiling_step()`-Aufruf gestoppt und gestoppt gemessen, dann die naechste
Partie (naechster Seed) gestartet. Der Drafting-Anteil davor ist NICHT Teil
der Messung (nur Mittel zum Zweck, um realistische Stellungen zu erreichen).

## Nutzung

Zwei separate Wheel-Builds noetig (Toggle in `tiling_solver.rs` von Hand
umschalten, `pip install . --force-reinstall --no-deps`, dann je einmal
laufen lassen):

    python tools/net_tiling_tiebreak_cost.py --label off --out evaluations/_cost_off.json
    # Toggle auf true, Wheel neu bauen
    python tools/net_tiling_tiebreak_cost.py --label on --out evaluations/_cost_on.json

Die beiden Rohdateien werden anschliessend von Hand zu
`evaluations/net_tiling_tiebreak_cost.json` zusammengefuehrt.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import MODELS_DIR  # noqa: E402


def reach_tiling_round_2_to_4(g, sims: int, c_puct: float, max_steps: int) -> bool:
    """Spielt netzgefuehrt bis zum ERSTEN Tiling-Entscheidungspunkt in Runde
    2-4. Gibt True zurueck, wenn erreicht (dann steht `g` genau davor,
    `ai_step_net_json()` -- der einzige exportierte Netz-Zug-Endpunkt, der
    intern fuer `Phase::Tiling` auf `ai_tiling_step` dispatcht, siehe
    `py.rs::ai_step_net_json` -- wurde noch NICHT fuer diesen Punkt
    aufgerufen). `ai_drafting_net_step`/`ai_tiling_step` selbst sind KEINE
    PyO3-Methoden (liegen in einem `impl PyGame`-Block ohne `#[pymethods]`,
    Kommentar dort: "kein PyO3-Export") -- von Python aus nur ueber
    `ai_step_net_json`/`ai_step_json` erreichbar."""
    import json as _json

    guard = 0
    while not g.both_start_placed():
        guard += 1
        if guard > 20:
            return False
        st = _json.loads(g.state_json())
        vm = st["valid_moves"]
        if not vm:
            return False
        g.ai_start_tile_json(vm[0]["player"])

    steps = 0
    while steps < max_steps:
        steps += 1
        phase = g.phase()
        if phase == "tiling" and 2 <= g.round_number() <= 4:
            return True
        if phase in ("drafting", "tiling"):
            g.ai_step_net_json(sims, c_puct, False)
        else:
            return False
    return False


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default="alphazero_v18_best.onnx")
    ap.add_argument("--n-states", type=int, default=20)
    ap.add_argument("--sims", type=int, default=100)
    ap.add_argument("--c-puct", type=float, default=0.3)
    ap.add_argument("--seed-start", type=int, default=1000)
    ap.add_argument("--max-drafting-steps", type=int, default=800)
    ap.add_argument("--label", required=True, help="z.B. 'on' oder 'off' -- nur zur Beschriftung der Ausgabe")
    ap.add_argument("--out", default="evaluations/net_tiling_tiebreak_cost.json")
    args = ap.parse_args()

    import mosaic_rust as mr

    model_path = str(MODELS_DIR / args.model)
    print(f"Modell: {model_path}")
    print(f"Label: {args.label} | Ziel: {args.n_states} Runde-2-4-Tiling-Messungen\n")

    durations_ms: list[float] = []
    skipped = 0
    seed = args.seed_start
    while len(durations_ms) < args.n_states and seed < args.seed_start + args.n_states * 10:
        g = mr.PyGame(("A", "B"), first_player=0, seed=seed)
        g.load_net(model_path)
        seed += 1
        ok = reach_tiling_round_2_to_4(g, args.sims, args.c_puct, args.max_drafting_steps)
        if not ok:
            skipped += 1
            continue
        t0 = time.perf_counter()
        g.ai_step_net_json(args.sims, args.c_puct, False)
        dt_ms = (time.perf_counter() - t0) * 1000.0
        durations_ms.append(dt_ms)
        print(f"  Messung {len(durations_ms)}/{args.n_states}: Runde {g.round_number()} "
              f"(vor dem Zug) -> {dt_ms:.2f} ms")

    if not durations_ms:
        raise SystemExit("Keine Runde-2-4-Tiling-Entscheidungspunkte erreicht -- Messung fehlgeschlagen.")

    durations_ms.sort()
    n = len(durations_ms)
    median = durations_ms[n // 2] if n % 2 else (durations_ms[n // 2 - 1] + durations_ms[n // 2]) / 2.0
    mean = sum(durations_ms) / n

    print("\n" + "=" * 60)
    print(f"  ai_tiling_step() Kosten (Label={args.label}, n={n}, {skipped} Partien uebersprungen)")
    print(f"  Median: {median:.2f} ms | Mittel: {mean:.2f} ms | Max: {max(durations_ms):.2f} ms "
          f"| Min: {min(durations_ms):.2f} ms")
    print("=" * 60)

    out = ROOT / args.out
    out.write_text(json.dumps({
        "label": args.label,
        "model": args.model,
        "n_states": n,
        "n_skipped": skipped,
        "sims": args.sims,
        "c_puct": args.c_puct,
        "median_ms": median,
        "mean_ms": mean,
        "max_ms": max(durations_ms),
        "min_ms": min(durations_ms),
        "raw_ms": durations_ms,
    }, indent=2), encoding="utf-8")
    print(f"\nErgebnis: {out}")


if __name__ == "__main__":
    main()
