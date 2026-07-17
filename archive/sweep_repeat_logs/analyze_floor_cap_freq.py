"""
Zaehlt, in WIE VIELEN der 5 Runden ein Spieler das Boden-Cap (floor>=4)
erreicht hat (Haeufigkeit statt nur "irgendwann"), getrennt fuer 0:0- und
normale Partien.

Nutzung: python analyze_floor_cap_freq.py <prefix>
"""
import sys
import glob
import pickle
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
MAX_BROKEN = 4


def main(prefix):
    files = sorted(glob.glob(str(DATA_DIR / f"selfplay_{prefix}_*.pkl")))
    zz_counts = []
    normal_counts = []
    n_games = 0

    for fp in files:
        with open(fp, "rb") as f:
            steps = pickle.load(f)
        by_gid = defaultdict(list)
        for s in steps:
            by_gid[s["game_id"]].append(s)
        for gid, gsteps in by_gid.items():
            n_games += 1
            final = gsteps[-1]["scores"]
            is_zz = (final[0] == 0 and final[1] == 0)

            # pro Runde: hat irgendein Spieler in dieser Runde floor>=4 erreicht?
            rounds_with_cap = set()
            for s in gsteps:
                r = s["state"].get("round", 1)
                floors = [len(p.get("floor", [])) for p in s["state"].get("players", [])]
                if floors[0] >= MAX_BROKEN or floors[1] >= MAX_BROKEN:
                    rounds_with_cap.add(r)
            cnt = len(rounds_with_cap)
            if is_zz:
                zz_counts.append(cnt)
            else:
                normal_counts.append(cnt)
        del steps, by_gid

    def avg(lst):
        return sum(lst) / len(lst) if lst else 0

    print(f"=== '{prefix}': {len(files)} Dateien, {n_games} Spiele ===")
    print(f"0:0-Partien (n={len(zz_counts)}): Ø {avg(zz_counts):.2f} von 5 Runden mit Boden-Cap")
    print(f"normale Partien (n={len(normal_counts)}): Ø {avg(normal_counts):.2f} von 5 Runden mit Boden-Cap")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "v2s2")
