# -*- coding: utf-8 -*-
"""Bit-Identitaets-Tor fuer den Merkmalsbauer: Rust gegen Python.

**Das Tor** (`PREREG_rust_data_layer.md` par.2, "Hartes Tor", Punkt 1): der
Merkmalsbauer zieht nach Rust um und wird dort die EINE Wahrheit; der
Python-Zwilling (`neural_net.py::state_to_tensor_python` /
`state_to_planes_python`) degradiert zum Test-Orakel. Vorbedingung fuer die
Umstellung des Produktivpfades ist Bit-Identitaet Feld fuer Feld,
`np.array_equal`, KEINE Toleranz -- und zwar VOR der Umstellung, nicht danach.
Ein "fast gleicher" Cache ist schlechter als ein langsamer (Kill-Kriterium
ebenda).

**Was verglichen wird.** Je Zustand zwei Groessen:

* der FLACHE Vektor (`INPUT_SIZE` Werte): Python `state_to_tensor_python`
  gegen Rust `mosaic_rust.state_features_from_json`. Beide lesen dasselbe
  Zustands-Dict; der Rust-Pfad ist `features::state_to_features`, also genau
  der Bauer des Spielpfades.
* die PLANES (`[C,6,6]`): Python `state_to_planes_python` gegen Rust
  `mosaic_rust.state_planes_from_json`. In Rust gibt es fuer die Planes
  keinen JSON-Pfad; der Export rekonstruiert den Zustand ueber
  `json_to_state` (fester Seed 0) und ruft `state_to_planes_direct` -- die
  Route, die `engine/examples/planes_parity.rs` seit Task #11 Phase 2 fuer
  denselben Vergleich benutzt.

**Zwei Grundmengen, absichtlich:**

* `pygame`: frische Partien ueber `PyGame` mit der Heuristik, Zustand je
  Entscheidung aus `state_json()`. Diese Zustaende TRAGEN das Record-Feld
  `dome_pool_view` und pruefen damit den neuen Abschnitt 15 im vollen
  Wertebereich (eigene und fremde Bloecke, Typenfolge, Praefix).
* `corpus`: Records aus `data/selfplay_v26-b01-policy_*.pkl`. Die sind VOR
  dem Feld entstanden; dort muessen beide Seiten uebereinstimmend elf Nullen
  liefern. Das ist die Rueckwaerts-Vertraeglichkeit, an der das Training des
  v28-Fensters haengt (Sockel-Anteile aus G-1 und G-2).

**Was das Werkzeug NICHT prueft:** die Cache-Bauschleife selbst. Es prueft
den Bauer, den sie ruft. Der Schalter `MOSAIC_FEATURES_FROM_RUST` wird hier
NICHT gesetzt -- beide Fassungen werden direkt gerufen, damit das Ergebnis
nicht von der Schalterstellung abhaengt.

Aufruf (einkernig, ohne Pipe; Wheel muss gebaut sein):

    python -X utf8 -u tools/probes/feature_parity_rust_python.py

Enger oder breiter:

    python -X utf8 -u tools/probes/feature_parity_rust_python.py \\
        --games 6 --sims 40 --corpus-files 3 --max-corpus-states 400

Ergebnis: `evaluations/artifacts/feature_parity_rust_python.json`
(n, Grundmenge, erste Abweichung namentlich, `laufzeit`-Block). Exit-Code 0
nur bei 0 Abweichungen -- das Tor ist bestanden oder es ist nicht bestanden.
"""
import argparse
import glob
import json
import os
import pathlib
import sys
import time

import numpy as np

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "engine" / "py"))

PREREG = "evaluations/PREREG_rust_data_layer.md par.2 (Teil A, hartes Tor Punkt 1)"

#: Grundmenge `corpus`: die Records des v26-b01-Sockels tragen `dome_pool_view`
#: NICHT (das Feld kam am 2026-09-10 dazu) -- genau darum sind sie der
#: Rueckwaerts-Vertraeglichkeitsfall.
CORPUS_GLOB = "data/selfplay_v26-b01-policy_*.pkl"


def first_difference(a: np.ndarray, b: np.ndarray) -> dict | None:
    """Erste Abweichung NAMENTLICH: flacher Index, beide Werte, Gesamtzahl.

    Kein `np.allclose`, keine Toleranz -- das Tor verlangt `np.array_equal`.
    """
    if a.shape != b.shape:
        return {"kind": "shape", "python": list(a.shape), "rust": list(b.shape)}
    if np.array_equal(a, b):
        return None
    flat_a, flat_b = a.reshape(-1), b.reshape(-1)
    diff = np.flatnonzero(flat_a != flat_b)
    i = int(diff[0])
    return {
        "kind": "value",
        "index": i,
        "index_unraveled": [int(x) for x in np.unravel_index(i, a.shape)],
        "python": float(flat_a[i]),
        "rust": float(flat_b[i]),
        "n_differing": int(diff.size),
        "n_total": int(flat_a.size),
    }


def states_from_pygame(n_games: int, sims: int, seed_base: int, progress_every: int) -> list[dict]:
    """Zustaende je Entscheidung aus frischen Heuristik-Partien.

    Fahrschleife wie `tools/claude_play.py::drive_ai`, nur mit der Heuristik
    auf BEIDEN Seiten und ohne Log-Ausgabe: Startkacheln zuerst, dann je
    Zustand VOR dem Zug einsammeln und `ai_step_json` anwenden.
    """
    import mosaic_rust

    out: list[dict] = []
    for gi in range(n_games):
        game = mosaic_rust.PyGame(("A", "B"), 0, seed_base + gi, None)
        for _ in range(4000):
            st = json.loads(game.state_json())
            phase = st.get("phase")
            if phase in ("end", "final"):
                break
            pending = [v for v in st.get("valid_moves", []) if v.get("type") == "start_tile_pending"]
            if pending:
                game.ai_start_tile_json(pending[0]["player"])
                continue
            if phase not in ("drafting", "tiling"):
                break
            out.append(st)
            res = json.loads(game.ai_step_json(sims, False))
            if not res.get("applied"):
                break
        if progress_every and (gi + 1) % progress_every == 0:
            print(f"  pygame: {gi + 1}/{n_games} Partien, {len(out)} Zustaende", flush=True)
    return out


def states_from_corpus(n_files: int, max_states: int, progress_every: int) -> list[dict]:
    """Zustaende aus den ersten `n_files` Sockel-Dateien von v26-b01."""
    from corpus_io import load_records

    files = sorted(glob.glob(str(_ROOT / CORPUS_GLOB)))[:n_files]
    if not files:
        raise SystemExit(
            f"Keine Korpus-Dateien unter {CORPUS_GLOB} -- Grundmenge 'corpus' waere leer "
            "(Nutzer-Regel: nie leer gruen)."
        )
    out: list[dict] = []
    for fi, path in enumerate(files):
        for step in load_records(path):
            state = step.get("state")
            if isinstance(state, dict):
                out.append(state)
            if len(out) >= max_states:
                break
        if progress_every and (fi + 1) % progress_every == 0:
            print(f"  corpus: {fi + 1}/{len(files)} Dateien, {len(out)} Zustaende", flush=True)
        if len(out) >= max_states:
            break
    return out


def compare(states: list[dict], population: str, check_planes: bool, progress_every: int) -> dict:
    """Vergleicht beide Bauer ueber `states` und meldet die erste Abweichung."""
    import mosaic_rust
    from neural_net import state_to_planes_python, state_to_tensor_python

    n_flat_ok = n_planes_ok = 0
    n_with_view = 0
    first_flat = first_planes = None
    for i, state in enumerate(states):
        if isinstance(state.get("dome_pool_view"), dict):
            n_with_view += 1
        state_json = json.dumps(state)
        py_flat = state_to_tensor_python(state).numpy()
        rs_flat = np.asarray(mosaic_rust.state_features_from_json(state_json), dtype=np.float32)
        d = first_difference(py_flat, rs_flat)
        if d is None:
            n_flat_ok += 1
        elif first_flat is None:
            first_flat = dict(d, state_index=i, population=population)
        if check_planes:
            py_planes = state_to_planes_python(state).numpy()
            raw, shape = mosaic_rust.state_planes_from_json(state_json)
            rs_planes = np.asarray(raw, dtype=np.float32).reshape(shape)
            d = first_difference(py_planes, rs_planes)
            if d is None:
                n_planes_ok += 1
            elif first_planes is None:
                first_planes = dict(d, state_index=i, population=population)
        if progress_every and (i + 1) % progress_every == 0:
            print(
                f"  {population}: {i + 1}/{len(states)} Zustaende, "
                f"flach ok {n_flat_ok}, planes ok {n_planes_ok}",
                flush=True,
            )
    return {
        "population": population,
        "n_states": len(states),
        "n_states_with_dome_pool_view": n_with_view,
        "unit": "Zustaende",
        "flat": {"n_equal": n_flat_ok, "first_difference": first_flat},
        "planes": {
            "n_equal": n_planes_ok,
            "first_difference": first_planes,
            "checked": bool(check_planes),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--games", type=int, default=4, help="Heuristik-Partien fuer die Grundmenge 'pygame'")
    ap.add_argument("--sims", type=int, default=30, help="Simulationen je Heuristik-Zug (nur Fahrschleife)")
    ap.add_argument("--seed-base", type=int, default=20260911)
    ap.add_argument("--corpus-files", type=int, default=3, help="wieviele Sockel-Dateien von v26-b01")
    ap.add_argument("--max-corpus-states", type=int, default=300)
    ap.add_argument("--no-planes", action="store_true", help="nur den Flachvektor pruefen")
    ap.add_argument("--progress-every", type=int, default=50)
    ap.add_argument("--out-dir", default="evaluations/artifacts")
    args = ap.parse_args()

    if os.environ.get("MOSAIC_FEATURES_FROM_RUST") == "1":
        # Der Vergleich ruft beide Fassungen NAMENTLICH; ein gesetzter Schalter
        # aendert am Ergebnis nichts, waere aber ein Hinweis auf ein
        # Missverstaendnis ueber das, was hier geprueft wird.
        print("HINWEIS: MOSAIC_FEATURES_FROM_RUST=1 gesetzt -- ohne Wirkung auf diese Sonde.", flush=True)

    import mosaic_rust
    from config import INPUT_SIZE

    t0, c0 = time.time(), time.process_time()
    print(f"Paritaets-Tor {PREREG}", flush=True)
    print(f"mosaic_rust {mosaic_rust.version()}, INPUT_SIZE (config.py) {INPUT_SIZE}", flush=True)

    print(f"Grundmenge pygame: {args.games} Partien, sims={args.sims} ...", flush=True)
    pygame_states = states_from_pygame(args.games, args.sims, args.seed_base, 1)
    print(f"Grundmenge corpus: {args.corpus_files} Dateien aus {CORPUS_GLOB} ...", flush=True)
    corpus_states = states_from_corpus(args.corpus_files, args.max_corpus_states, 1)

    results = [
        compare(pygame_states, "pygame", not args.no_planes, args.progress_every),
        compare(corpus_states, "corpus", not args.no_planes, args.progress_every),
    ]

    n_states = sum(r["n_states"] for r in results)
    n_diff = sum(
        (1 if r["flat"]["first_difference"] else 0) + (1 if r["planes"]["first_difference"] else 0)
        for r in results
    )
    wall, cpu = time.time() - t0, time.process_time() - c0
    out = {
        "prereg": PREREG,
        "engine_version": mosaic_rust.version(),
        "input_size_config": INPUT_SIZE,
        "n_states": n_states,
        "unit": "Zustaende",
        "populations": results,
        "gate_passed": n_diff == 0,
        "cli_args": vars(args),
        "laufzeit": {
            "wanduhr_s": round(wall, 2),
            "cpu_s": round(cpu, 2),
            "threads": 1,
            "s_je_partie": round(wall / max(args.games, 1), 4),
            "s_je_zustand": round(wall / n_states, 6) if n_states else None,
        },
    }
    out_dir = pathlib.Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = _ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "feature_parity_rust_python.json"
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    for r in results:
        print(
            f"{r['population']}: {r['n_states']} Zustaende "
            f"(mit dome_pool_view: {r['n_states_with_dome_pool_view']}), "
            f"flach gleich {r['flat']['n_equal']}, planes gleich {r['planes']['n_equal']}",
            flush=True,
        )
        for key in ("flat", "planes"):
            if r[key]["first_difference"]:
                print(f"  ABWEICHUNG {key}: {json.dumps(r[key]['first_difference'], ensure_ascii=False)}", flush=True)
    print(f"Tor {'BESTANDEN' if out['gate_passed'] else 'NICHT bestanden'} -- {path}", flush=True)
    print(f"laufzeit: Wanduhr {wall:.1f}s, CPU {cpu:.1f}s, 1 Thread", flush=True)
    return 0 if out["gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
