"""
Direkter Blick in den Value-Head: fragt das ONNX-Modell (v2, Stufe 2) an
Runden-Beginn-Zustaenden ab (fuer den jeweils aktuellen Spieler) und
verfolgt die Vorhersage ueber den Spielverlauf, getrennt fuer 0:0- und
normale Partien. Ziel: sieht der Value-Head den 0:0-Absturz kommen (Wert
sinkt schon frueh), oder wird er "ueberrascht" (Wert bleibt optimistisch bis
kurz vor Schluss)?

Nutzung: python analyze_value_predictions.py <prefix> <model.onnx> [n_samples]
"""
import sys
import glob
import pickle
import random
from pathlib import Path
from collections import defaultdict

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "engine" / "py"))
from neural_net import state_to_tensor
import mosaic_rust as mr

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
MODELS_DIR = Path(__file__).resolve().parents[2] / "models"


def value_at(model_path, state):
    feats = state_to_tensor(state).numpy().tolist()
    val, _ = mr.onnx_eval(model_path, feats)
    return val


def main(prefix, model_name, n_samples=20):
    model_path = str(MODELS_DIR / model_name)
    files = sorted(glob.glob(str(DATA_DIR / f"selfplay_{prefix}_*.pkl")))
    random.seed(42)
    random.shuffle(files)

    games = {}
    for fp in files:
        with open(fp, "rb") as f:
            steps = pickle.load(f)
        by_gid = defaultdict(list)
        for s in steps:
            by_gid[s["game_id"]].append(s)
        games.update(by_gid)
        if len(games) >= n_samples * 30:  # genug Kandidaten gesammelt
            break

    zz_games = [g for g in games.values() if g[-1]["scores"] == [0, 0]]
    normal_games = [g for g in games.values() if g[-1]["scores"] != [0, 0]]
    random.shuffle(zz_games)
    random.shuffle(normal_games)
    zz_games = zz_games[:n_samples]
    normal_games = normal_games[:n_samples]

    def round_trajectory(gsteps):
        """Fuer jede Runde: erster Step dieser Runde -> Value-Vorhersage
        fuer den aktuellen Spieler an diesem Zustand."""
        seen_rounds = set()
        traj = {}
        for s in gsteps:
            r = s["state"].get("round", 1)
            if r in seen_rounds:
                continue
            seen_rounds.add(r)
            v = value_at(model_path, s["state"])
            traj[r] = v
        return traj

    def avg_by_round(games_list):
        sums = defaultdict(float)
        counts = defaultdict(int)
        for g in games_list:
            traj = round_trajectory(g)
            for r, v in traj.items():
                sums[r] += v
                counts[r] += 1
        return {r: sums[r] / counts[r] for r in sorted(sums)}

    print(f"=== Value-Vorhersage pro Runde ({model_name}, {prefix}) ===")
    print(f"0:0-Partien (n={len(zz_games)}):")
    for r, v in avg_by_round(zz_games).items():
        print(f"  Runde {r}: Ø Value = {v:+.3f}")
    print(f"normale Partien (n={len(normal_games)}):")
    for r, v in avg_by_round(normal_games).items():
        print(f"  Runde {r}: Ø Value = {v:+.3f}")


if __name__ == "__main__":
    prefix = sys.argv[1] if len(sys.argv) > 1 else "v2s2"
    model = sys.argv[2] if len(sys.argv) > 2 else "alphazero_v2.onnx"
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    main(prefix, model, n)
