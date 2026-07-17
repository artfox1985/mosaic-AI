"""
Diagnose-Skript fuer die 0:0-Partien-Untersuchung (Stufe 2). Laedt alle
selfplay_<prefix>_*.pkl-Dateien, gruppiert nach game_id (scores/winner sind
je Spiel konstant ueber alle Steps -- Endergebnis, rueckwaerts propagiert),
und berichtet 0:0-Rate + Boden-/Runden-Statistik, getrennt fuer 0:0- und
normale Partien.

Nutzung: python analyze_zerozero.py <prefix> [max_files]
  z.B. python analyze_zerozero.py s400        (Heuristik-Baseline)
       python analyze_zerozero.py v2          (Stufe-1-Netz-Baseline)
       python analyze_zerozero.py v2s2        (Stufe-2-Testlauf)
"""
import sys
import glob
import pickle
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def load_games(prefix, max_files=None):
    files = sorted(glob.glob(str(DATA_DIR / f"selfplay_{prefix}_*.pkl")))
    if max_files:
        files = files[:max_files]
    games = {}
    for fp in files:
        with open(fp, "rb") as f:
            steps = pickle.load(f)
        by_gid = defaultdict(list)
        for s in steps:
            by_gid[s["game_id"]].append(s)
        for gid, gsteps in by_gid.items():
            games[gid] = gsteps
    return games, len(files)


def floor_counts(state):
    return [len(p.get("floor", [])) for p in state.get("players", [])]


def analyze(prefix, max_files=None):
    games, n_files = load_games(prefix, max_files)
    n = len(games)
    if n == 0:
        print(f"Keine Spiele fuer Praefix '{prefix}' gefunden ({n_files} Dateien).")
        return

    zerozero = []
    normal = []
    incomplete = 0
    for gid, gsteps in games.items():
        last = gsteps[-1]
        if not last.get("completed", True):
            incomplete += 1
            continue
        scores = last["scores"]
        rounds = last["state"].get("round", None)
        if scores[0] == 0 and scores[1] == 0:
            zerozero.append((gid, gsteps, rounds))
        else:
            normal.append((gid, gsteps, rounds))

    print(f"=== Praefix '{prefix}' ({n_files} Dateien, {n} Spiele, {incomplete} unvollstaendig) ===")
    print(f"0:0-Partien: {len(zerozero)}/{n} ({len(zerozero)/n*100:.1f}%)")
    if normal:
        avg_rounds_normal = sum(r for _, _, r in normal if r) / len(normal)
        avg_len_normal = sum(len(g) for _, g, _ in normal) / len(normal)
        print(f"  Normale Partien: Ø Runden={avg_rounds_normal:.2f}  Ø Steps={avg_len_normal:.1f}")
    if zerozero:
        avg_rounds_zz = sum(r for _, _, r in zerozero if r) / len(zerozero)
        avg_len_zz = sum(len(g) for _, g, _ in zerozero) / len(zerozero)
        print(f"  0:0-Partien:     Ø Runden={avg_rounds_zz:.2f}  Ø Steps={avg_len_zz:.1f}")
        # Boden-Belegung am Spielende (beide Spieler)
        end_floors = [floor_counts(g[-1]["state"]) for _, g, _ in zerozero]
        avg_floor_p0 = sum(f[0] for f in end_floors) / len(end_floors)
        avg_floor_p1 = sum(f[1] for f in end_floors) / len(end_floors)
        print(f"  0:0 Boden am Ende: P0 Ø={avg_floor_p0:.2f}  P1 Ø={avg_floor_p1:.2f}")
    print()
    return zerozero, normal


if __name__ == "__main__":
    prefix = sys.argv[1] if len(sys.argv) > 1 else "s400"
    max_files = int(sys.argv[2]) if len(sys.argv) > 2 else None
    analyze(prefix, max_files)
