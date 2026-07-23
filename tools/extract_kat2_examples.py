"""
tools/extract_kat2_examples.py — Extrahiert konkrete Beispiel-Zustände fuer
"Kategorie 2"-Faelle (Strafleiste als Top-Policy-Wahl TROTZ offener, nicht
aussichtsloser Reihen-Alternative, UND mit deutlicher Prob-Marge > 0.2) aus
den Self-Play-Trainingsdaten -- zum manuellen Nachpruefen im Debug-Log.

Verwendung:
    python tools/extract_kat2_examples.py [data_dir] [--prefix selfplay_v8]
"""
import sys, os, glob, pickle, json, argparse
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine" / "py"))
from config import DATA_DIR
from diagnosis import (
    _dome_row_fully_built,
    _dome_row_has_open_matching_slot,
)


def collect_cases(data_dir: str, prefix: str, margin_threshold: float = 0.2):
    files = sorted(glob.glob(os.path.join(data_dir, f"{prefix}*.pkl")))
    cases = []
    for f in files:
        with open(f, 'rb') as fh:
            data = pickle.load(fh)
        for step in data:
            policy = step.get('policy', [])
            if not policy:
                continue
            state = step.get('state')
            if state is None:
                continue

            best_prob, best_action = -1.0, None
            has_row_alt = False
            best_alt_prob, best_alt_action = -1.0, None
            for entry in policy:
                a = entry.get('action', {})
                p = entry.get('prob', 0.0)
                is_penalty = a.get('type') == 'stone' and a.get('row', 0) == -1
                if not is_penalty and a.get('type') == 'stone' and a.get('row') not in (None, -1):
                    has_row_alt = True
                    if p > best_alt_prob:
                        best_alt_prob, best_alt_action = p, a
                if p > best_prob:
                    best_prob, best_action = p, a

            if best_action is None or not has_row_alt:
                continue
            if not (best_action.get('type') == 'stone' and best_action.get('row', 0) == -1):
                continue

            margin = best_prob - best_alt_prob
            if margin <= margin_threshold:
                continue

            pi = state.get('current_player')
            alt_row = best_alt_action.get('row')
            alt_color = best_alt_action.get('color')
            doomed_alt = None
            if pi is not None and alt_row is not None:
                fully_built = _dome_row_fully_built(state, pi, alt_row)
                has_slot = _dome_row_has_open_matching_slot(state, pi, alt_row, alt_color)
                if fully_built is not None and has_slot is not None:
                    doomed_alt = fully_built and not has_slot
            if doomed_alt:
                continue  # nur "echte" Faelle, Alternative war nicht schon aussichtslos

            cases.append({
                'file': os.path.basename(f),
                'game_id': step.get('game_id'),
                'round': state.get('round'),
                'scoring_tile_ids': sorted(state.get('scoring_tile_ids', [])),
                'penalty_action': best_action,
                'penalty_prob': best_prob,
                'alt_action': best_alt_action,
                'alt_prob': best_alt_prob,
                'margin': margin,
                'state': state,
            })
    return cases


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('data_dir', nargs='?', default=str(DATA_DIR))
    ap.add_argument('--prefix', default='selfplay_v8')
    ap.add_argument('--per-round', type=int, default=3, help='Beispiele je Runde')
    ap.add_argument('--out', default='static/log/kategorie2_examples')
    args = ap.parse_args()

    print(f"Sammle Faelle aus {args.data_dir} (Prefix={args.prefix})...")
    cases = collect_cases(args.data_dir, args.prefix)
    print(f"{len(cases)} hoch-konfidente Kategorie-2-Faelle gefunden (Marge > 0.2, Alternative nicht aussichtslos).")

    by_round = defaultdict(list)
    for c in cases:
        by_round[c['round']].append(c)
    for r in by_round:
        by_round[r].sort(key=lambda c: c['margin'], reverse=True)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_lines = []
    idx = 0
    for r in sorted(by_round):
        for c in by_round[r][:args.per_round]:
            idx += 1
            fname = out_dir / f"kat2_{idx:03d}_r{r}_margin{c['margin']:.2f}.json"
            with open(fname, 'w', encoding='utf-8') as fh:
                json.dump(c, fh, ensure_ascii=False, indent=2)
            pa, aa = c['penalty_action'], c['alt_action']
            summary_lines.append(
                f"{fname.name}: Runde {r}, Wertungsplatten {c['scoring_tile_ids']}, "
                f"Marge {c['margin']:.3f}  |  gewaehlt: {pa.get('color')} -> Strafleiste (p={c['penalty_prob']:.3f})  "
                f"|  Alternative: {aa.get('color')} -> Reihe {aa.get('row')} (p={c['alt_prob']:.3f})"
            )

    summary_path = out_dir / "SUMMARY.txt"
    with open(summary_path, 'w', encoding='utf-8') as fh:
        fh.write("\n".join(summary_lines))
    print(f"{idx} Beispiele geschrieben nach {out_dir}/ (siehe SUMMARY.txt)")
    for line in summary_lines:
        print(" ", line)


if __name__ == "__main__":
    main()
