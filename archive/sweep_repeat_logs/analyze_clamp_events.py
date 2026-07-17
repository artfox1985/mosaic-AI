"""
Prueft, ob ein Spieler waehrend des Spiels (nach Runde 1) mindestens einmal
auf exakt 0 geklemmt wurde (state['players'][i]['score'] == 0), und
korreliert das mit dem 0:0-Endergebnis. Speichereffizient: verarbeitet
Dateien einzeln, haelt nur Zaehler im Speicher, keine volle Spieleliste.

Nutzung: python analyze_clamp_events.py <prefix>
"""
import sys
import glob
import pickle
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def main(prefix):
    files = sorted(glob.glob(str(DATA_DIR / f"selfplay_{prefix}_*.pkl")))
    zz_with_clamp = zz_without = normal_with_clamp = normal_without = 0
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
            max_round = max(s["state"].get("round", 1) for s in gsteps)
            clamp_hit = False
            for s in gsteps:
                r = s["state"].get("round", 1)
                if r != max_round:
                    continue  # nur die LETZTE Runde ist fuer das Endergebnis entscheidend
                sc = [p["score"] for p in s["state"]["players"]]
                if sc[0] == 0 or sc[1] == 0:
                    clamp_hit = True
                    break
            if is_zz:
                if clamp_hit:
                    zz_with_clamp += 1
                else:
                    zz_without += 1
            else:
                if clamp_hit:
                    normal_with_clamp += 1
                else:
                    normal_without += 1
        del steps, by_gid  # Speicher freigeben

    n_zz = zz_with_clamp + zz_without
    n_normal = normal_with_clamp + normal_without
    print(f"=== '{prefix}': {len(files)} Dateien, {n_games} Spiele ===")
    print(f"0:0-Partien (n={n_zz}): {zz_with_clamp} mit Clamp-Event nach Runde 1 "
          f"({zz_with_clamp/n_zz*100:.1f}%)" if n_zz else "keine 0:0-Partien")
    print(f"Normale Partien (n={n_normal}): {normal_with_clamp} mit Clamp-Event nach Runde 1 "
          f"({normal_with_clamp/n_normal*100:.1f}%)" if n_normal else "keine normalen Partien")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "v2s2")
