# -*- coding: utf-8 -*-
"""Seeding-Baustein 1 (PREREG_start_position_seeding.md par.2): Stellungssatz
plus Kuratierungs-Bericht aus dem Asym-Korpus S -- reine Analyse, keine
Engine-Aenderung.

Kandidaten: Zustaende der ZWANGSSEITE (zwangsseiten_map.txt) mit
Spaltenfortschritt max(col_fill) in {3,4,5} und Runde in {2,3,4}. Auswahl
stratifiziert ueber (Runde x Fortschritt), hoechstens EINE Stellung je Partie,
deterministisch (--seed).

Spaltenzaehlung laeuft aus Tempo-Gruenden in Python (Grid-Mapping: Tile (tr,tc)
deckt Spalten 2*tc..2*tc+1, spaces row-major) und wird VOR jedem Lauf gegen
`mosaic_rust.plate_completability_json` verifiziert (--verify, Pflichtschritt:
0 Abweichungen oder Abbruch) -- Muster "unabhaengig dupliziert + Gegenprobe".

    python -X utf8 tools/seed_position_curation.py --verify 500
    python -X utf8 tools/seed_position_curation.py --run --target 1500

Modus `--mode am-zug` (v24-Arm b03, PREREG_start_position_seeding.md par.7,
2026-09-04): Kandidat ist der Zustand des Spielers AM ZUG (`state.current_player`,
beide Seiten kommen vor), die Zwangsseiten-Map wird nicht gelesen; Quelle per
`--korpus-glob`, Ausgaben per `--out-set` / `--out-report`:

    python -X utf8 tools/seed_position_curation.py --mode am-zug \\
        --korpus-glob "data/selfplay_v23-b01-value-argmax_*.pkl" --verify 500 \\
        --run --target 1500 --seed 20260912 \\
        --out-set data/seed_positions/seed_positions_v2.jsonl \\
        --out-report evaluations/artifacts/seed_positions_curation_report_v2.json
"""
from __future__ import annotations

import argparse
import glob
import json
import pickle
import random
import re
import statistics as stats
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
# Korpusdateien liegen seit der gzip-Umstellung komprimiert (Magic 0x1f);
# `pickle.load` scheitert daran, `corpus_io.load_records` kennt beide Formen.
from corpus_io import load_records  # noqa: E402

KORPUS_GLOB = str(ROOT / "data/asym_corpus/selfplay_v21_asymS_*.pkl")
MAP_PATH = ROOT / "data/asym_corpus/zwangsseiten_map.txt"
OUT_SET = ROOT / "data/seed_positions/seed_positions_v1.jsonl"
OUT_REPORT = ROOT / "evaluations/artifacts/seed_positions_curation_report.json"

ROUNDS = (2, 3, 4)
PROGRESS = (3, 4, 5)
STEP_STRIDE = 2  # jeden 2. Schritt pruefen -- Fortschritt aendert sich langsam


def load_map() -> dict[str, int]:
    zwang = {}
    zeile = re.compile(r"^(\S+) (\d+) (\d) (\d+) (\d+)$")
    for line in MAP_PATH.read_text(encoding="utf-8").splitlines():
        m = zeile.match(line)
        if m:
            zwang[m.group(1)] = int(m.group(3))
    if len(zwang) != 8000:
        raise SystemExit(f"Zwangsseiten-Map unvollstaendig: {len(zwang)} != 8000")
    return zwang


def col_fill_py(player: dict) -> list[int]:
    fill = [0] * 6
    grid = player["dome_grid"]
    for tr in range(3):
        for tc in range(3):
            tile = grid[tr][tc]
            if not tile:
                continue
            for si, sp in enumerate(tile["spaces"]):
                if sp.get("filled") is not None:
                    fill[2 * tc + (si % 2)] += 1
    return fill


def verify(n: int, seed: int, korpus_glob: str = KORPUS_GLOB) -> None:
    import mosaic_rust as mr

    rng = random.Random(seed)
    files = sorted(glob.glob(korpus_glob))
    if not files:
        raise SystemExit(f"Keine Korpusdateien fuer {korpus_glob}")
    checked = mismatch = 0
    while checked < n:
        f = rng.choice(files)
        data = load_records(f)
        step = rng.choice(data)
        st = step["state"]
        for pi in (0, 1):
            eng = json.loads(mr.plate_completability_json(json.dumps(st), pi))["col_fill"]
            py = col_fill_py(st["players"][pi])
            checked += 1
            if eng != py:
                mismatch += 1
                print(f"ABWEICHUNG {f} game={step.get('game_id')} pi={pi}: py={py} eng={eng}")
    print(f"Verifikation: {checked} Vergleiche, {mismatch} Abweichungen")
    if mismatch:
        raise SystemExit("Python-Spaltenzaehlung weicht ab -- NICHT verwenden.")


def run(target: int, seed: int, mode: str = "zwangsseite", korpus_glob: str = KORPUS_GLOB,
        out_set: Path = OUT_SET, out_report: Path = OUT_REPORT) -> None:
    # Modus "zwangsseite" (v1, par.2): die Seite kommt aus der Map je Partie.
    # Modus "am-zug" (v24-b03, par.7): die Seite ist der Spieler am Zug des
    # jeweiligen Zustands (`state.current_player`; im Korpus identisch mit
    # `record.player`, 1.784 von 1.784 geprueft 2026-09-04), keine Map.
    if mode not in ("zwangsseite", "am-zug"):
        raise SystemExit(f"unbekannter --mode {mode!r}")
    zwang = load_map() if mode == "zwangsseite" else None
    files = sorted(glob.glob(korpus_glob))
    if not files:
        raise SystemExit(f"Keine Korpusdateien fuer {korpus_glob}")
    kandidaten = []  # (stratum, game_id, file, step_idx, meta)
    je_partie: dict[str, list] = defaultdict(list)
    steps_total: dict[str, int] = {}

    for f in files:
        data = load_records(f)
        per_game: dict[str, list] = defaultdict(list)
        for idx, step in enumerate(data):
            per_game[step["game_id"]].append((idx, step))
        for gid, steps in per_game.items():
            if zwang is not None:
                side_fixed = zwang.get(gid)
                if side_fixed is None:
                    continue
            steps_total[gid] = len(steps)
            for pos, (idx, step) in enumerate(steps):
                if pos % STEP_STRIDE:
                    continue
                st = step["state"]
                rd = st.get("round")
                if rd not in ROUNDS or st.get("phase") != "drafting":
                    continue
                side = side_fixed if zwang is not None else st.get("current_player")
                if side not in (0, 1):
                    continue
                prog = max(col_fill_py(st["players"][side]))
                if prog not in PROGRESS:
                    continue
                meta = {
                    "game_id": gid, "source_file": Path(f).name, "step_in_game": pos,
                    "round": rd, "progress": prog, "zwangsseite": side,
                    "seite_modus": mode,
                    "k1_active": 1 in st["scoring_tile_ids"],
                    "scoring_tile_ids": st["scoring_tile_ids"],
                    "remaining_steps": len(steps) - pos,
                    "steps_total": len(steps),
                }
                je_partie[gid].append(((rd, prog), meta, st))

    # je Partie EIN Kandidat (deterministisch), dann stratifizierte Auswahl
    rng = random.Random(seed)
    pro_stratum: dict[tuple, list] = defaultdict(list)
    for gid in sorted(je_partie):
        stratum, meta, st = rng.choice(je_partie[gid])
        pro_stratum[stratum].append((meta, st))

    kandidaten_zahl = {f"r{r}_p{p}": len(pro_stratum.get((r, p), [])) for r in ROUNDS for p in PROGRESS}
    rate = max(1, target // (len(ROUNDS) * len(PROGRESS)))
    auswahl = []
    for stratum in sorted(pro_stratum):
        pool = pro_stratum[stratum]
        rng.shuffle(pool)
        auswahl.extend(pool[:rate])
    rest = [x for stratum in sorted(pro_stratum) for x in pro_stratum[stratum][rate:]]
    rng.shuffle(rest)
    auswahl.extend(rest[: max(0, target - len(auswahl))])

    out_set.parent.mkdir(parents=True, exist_ok=True)
    with out_set.open("w", encoding="utf-8") as fh:
        for meta, st in auswahl:
            fh.write(json.dumps({**meta, "state": st}, ensure_ascii=False) + "\n")

    rem_frac = [m["remaining_steps"] / m["steps_total"] for m, _ in auswahl]
    sel_zahl = Counter(f"r{m['round']}_p{m['progress']}" for m, _ in auswahl)
    report = {
        "quelle": {"dateien": len(files), "partien_mit_kandidat": len(je_partie),
                    "step_stride": STEP_STRIDE, "seed": seed,
                    "korpus_glob": korpus_glob, "seite_modus": mode},
        "seiten_in_auswahl": dict(Counter(str(m["zwangsseite"]) for m, _ in auswahl)),
        "kandidaten_je_stratum (je Partie 1)": kandidaten_zahl,
        "auswahl_gesamt": len(auswahl),
        "auswahl_je_stratum": dict(sorted(sel_zahl.items())),
        "k1_aktiv_in_auswahl": sum(1 for m, _ in auswahl if m["k1_active"]),
        "restlaenge_frac": {"mean": stats.mean(rem_frac), "median": stats.median(rem_frac),
                             "min": min(rem_frac), "max": max(rem_frac)},
        "kostenrechnung": {
            "annahme_durchsatz_vollpartien_pro_s": [0.21, 0.29],
            "kommentar": "Seed-Partie ~ Vollpartie x restlaenge_frac.mean; Stunden je k",
            "stunden_bei_k": {
                str(k): [round(len(auswahl) * k * stats.mean(rem_frac) / d / 3600, 1)
                          for d in (0.29, 0.21)]
                for k in (4, 6, 8)
            },
        },
    }
    out_report.parent.mkdir(parents=True, exist_ok=True)
    out_report.write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=1, ensure_ascii=False))
    print(f"\nStellungssatz: {out_set} ({len(auswahl)} Stellungen)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--verify", type=int, default=0, help="N Zufalls-Vergleiche Python gegen Engine")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--target", type=int, default=1500)
    ap.add_argument("--seed", type=int, default=20260822)
    ap.add_argument("--mode", choices=("zwangsseite", "am-zug"), default="zwangsseite",
                    help="zwangsseite = v1 (Map je Partie); am-zug = Spieler am Zug je Zustand (b03, par.7)")
    ap.add_argument("--korpus-glob", default=KORPUS_GLOB, help="Quelle der Zustaende (Glob)")
    ap.add_argument("--out-set", default=str(OUT_SET))
    ap.add_argument("--out-report", default=str(OUT_REPORT))
    a = ap.parse_args()
    if a.verify:
        verify(a.verify, a.seed, a.korpus_glob)
    if a.run:
        run(a.target, a.seed, mode=a.mode, korpus_glob=a.korpus_glob,
            out_set=Path(a.out_set), out_report=Path(a.out_report))
    if not a.verify and not a.run:
        ap.error("--verify N und/oder --run angeben")


if __name__ == "__main__":
    main()
