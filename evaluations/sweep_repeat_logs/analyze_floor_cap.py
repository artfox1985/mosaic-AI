"""
Prueft, ob ein Spieler in irgendeiner Runde das Boden-Kappungs-Maximum
(floor_count == 4, MAX_BROKEN) erreicht hat -- ab dort sind weitere
Boden-Kacheln in dieser Runde nachweislich strafpunktfrei (`.take(MAX_BROKEN)`
in board.rs::broken_penalty). Das ist der direkte, deterministische Exploit-
Indikator (nicht nur "score wurde geklemmt", was zu unscharf war).

Nutzung: python analyze_floor_cap.py <prefix>
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
    zz_with_cap = zz_without = normal_with_cap = normal_without = 0
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
            cap_hit = False
            for s in gsteps:
                floors = [len(p.get("floor", [])) for p in s["state"].get("players", [])]
                if floors[0] >= MAX_BROKEN or floors[1] >= MAX_BROKEN:
                    cap_hit = True
                    break
            if is_zz:
                if cap_hit:
                    zz_with_cap += 1
                else:
                    zz_without += 1
            else:
                if cap_hit:
                    normal_with_cap += 1
                else:
                    normal_without += 1
        del steps, by_gid

    n_zz = zz_with_cap + zz_without
    n_normal = normal_with_cap + normal_without
    print(f"=== '{prefix}': {len(files)} Dateien, {n_games} Spiele ===")
    if n_zz:
        print(f"0:0-Partien (n={n_zz}): {zz_with_cap} erreichten Boden-Cap=4 "
              f"({zz_with_cap/n_zz*100:.1f}%)")
    if n_normal:
        print(f"normale Partien (n={n_normal}): {normal_with_cap} erreichten Boden-Cap=4 "
              f"({normal_with_cap/n_normal*100:.1f}%)")
    n_total_cap = zz_with_cap + normal_with_cap
    print(f"Gesamt: {n_total_cap}/{n_games} Partien erreichten Boden-Cap=4 irgendwann "
          f"({n_total_cap/n_games*100:.1f}%)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "v2s2")
