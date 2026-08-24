"""Kennlinie des Konjunktions-Kopfes, getrennt nach Quelle.

FRAGE (Nutzer 2026-08-18): helfen zusaetzliche Self-Plays der Plattenbauer-
Heuristiken fuer die Kalibrierung?

Der Mittelwert-Versatz ist bereits gemessen und klein
(`conjunction_marginal_normal_play.py`: k1 0,35 Log-Odds). Was NICHT widerlegt
ist, ist die Fehlkalibrierung im OBEREN Bereich (`PREREG_ownership_selector.md`
par.9.2: Top-Bin Spalten vorhergesagt 0,949). Das ist eine STEIGUNGSfrage, und
sie entscheidet sich dort, wo der Kopf ueberhaupt hohe Werte sagt.

Genau das misst diese Sonde: die Verteilung der VORHERSAGEN und die
tatsaechliche Trefferrate je Vorhersage-Bin, getrennt fuer

  * normales Spiel   -- data/*.pkl
  * Bauer-Arme       -- data/ownership_corpus/*.pkl

Wenn im normalen Spiel oberhalb von 0,5 praktisch keine Faelle liegen, kann
dort keine Steigung gefittet werden -- dann sind die Bauer-Arme die EINZIGE
Quelle fuer diesen Bereich, und die Antwort auf die Frage ist ja. Liegen dort
genug Faelle, braucht es sie nicht.

Aufruf:  python conjunction_reliability_by_source.py [dateien_je_quelle] [checkpoint]
"""
import collections
import glob
import re
import sys
from pathlib import Path

import numpy as np
import torch

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))                      # config.py liegt in der Wurzel
sys.path.insert(0, str(REPO / "engine" / "py"))
sys.path.insert(0, str(REPO / "tools" / "probes"))

import ownership_gate_a as GA  # noqa: E402

GRUPPEN = {"Spalten k1": (6, 12), "Diagonalen k2": (12, 14), "Ecken k5": (14, 18)}
# Grenzen bewusst ungleichmaessig: unten passiert alles, oben entscheidet sich
# die Frage. Der Bin ab 0,5 ist der aus par.9.2.
BINS = [0.0, 0.01, 0.05, 0.2, 0.5, 0.8, 1.0001]
DATEIEN_JE_QUELLE = int(sys.argv[1]) if len(sys.argv) > 1 else 60
CHECKPOINT = sys.argv[2] if len(sys.argv) > 2 else "alphazero_v21-b19_best.pth"


def stichprobe(dateien, k):
    d = sorted(dateien)
    if len(d) <= k:
        return d
    schritt = len(d) / k
    return [d[int(i * schritt)] for i in range(k)]


def normalspiel_dateien(k):
    """Gleichmaessig ueber die fuenf Generator-Praefixe."""
    quellen = collections.defaultdict(list)
    for f in glob.glob(str(REPO / "data" / "*.pkl")):
        m = re.match(r"selfplay_(.+?)_\d{8}_", Path(f).name)
        quellen[m.group(1) if m else "?"].append(f)
    je = max(1, k // max(1, len(quellen)))
    out = []
    for q in sorted(quellen):
        out += stichprobe(quellen[q], je)
    return out


def builder_files(k):
    """Nur die gelenkten Arme -- `heur_own` ist der ungelenkte Heuristik-Arm und
    bleibt draussen, sonst mischt sich normales Spiel unter die Bauer-Seite."""
    quellen = collections.defaultdict(list)
    for f in glob.glob(str(REPO / "data" / "ownership_corpus" / "*.pkl")):
        name = Path(f).name
        if not name.startswith("selfplay_v21_own_"):
            continue
        m = re.match(r"selfplay_(.+?)_\d{8}_", name)
        quellen[m.group(1) if m else "?"].append(f)
    je = max(1, k // max(1, len(quellen)))
    out = []
    for q in sorted(quellen):
        out += stichprobe(quellen[q], je)
    return out


def sammle(dateien, model):
    end_states, mid_states, mid_cp, lab = [], [], [], []
    for f in dateien:
        for _gid, rec, mid in GA.iter_games(f):
            if not rec.get("completed") or mid is None:
                continue
            _o0, _o1, c0, c1 = GA.game_labels(rec)
            lab.append((c0, c1))
            mid_states.append(mid["state"])
            mid_cp.append(mid["state"].get("current_player", 0))
            end_states.append(rec["state"])
    if not mid_states:
        return None, None
    planes, flat = GA.encode_states(mid_states)
    p = GA.predict_ownership(model, planes, flat)
    n = len(mid_states)
    O = 36
    conj_me = p[:, 2 * O: 2 * O + 34]
    conj_op = p[:, 2 * O + 34: 2 * O + 68]
    lab_me = np.stack([lab[i][mid_cp[i]] for i in range(n)])
    lab_op = np.stack([lab[i][1 - mid_cp[i]] for i in range(n)])
    return (np.concatenate([conj_me, conj_op], axis=0),
            np.concatenate([lab_me, lab_op], axis=0))


def main():
    ck = torch.load(REPO / "models" / CHECKPOINT, map_location="cpu", weights_only=False)
    model, _enc = GA.build_model_from_checkpoint(ck)
    model.eval().to(GA.DEVICE)
    print(f"Checkpoint {CHECKPOINT} auf {GA.DEVICE}", flush=True)

    quellen = {"normales Spiel": normalspiel_dateien(DATEIEN_JE_QUELLE),
               "Bauer-Arme": builder_files(DATEIEN_JE_QUELLE)}
    daten = {}
    for name, dateien in quellen.items():
        print(f"{name}: {len(dateien)} Dateien ...", flush=True)
        vorher, label = sammle(dateien, model)
        if vorher is None:
            print(f"  !! {name}: keine auswertbaren Partien")
            continue
        daten[name] = (vorher, label)
        print(f"  {vorher.shape[0]} Bretter", flush=True)

    for g, (a, b) in GRUPPEN.items():
        print("\n" + "=" * 90)
        print(f"{g} -- Kennlinie je Quelle (Runde-3-Zustaende)")
        print("=" * 90)
        print(f"{'Quelle':16s} {'Bin':>14s} {'Faelle':>9s} {'Anteil':>8s} "
              f"{'vorhergesagt':>13s} {'tatsaechlich':>13s} {'Abweichung':>11s}")
        for name, (vorher, label) in daten.items():
            p = vorher[:, a:b].ravel()
            y = label[:, a:b].ravel().astype(float)
            for i in range(len(BINS) - 1):
                lo, hi = BINS[i], BINS[i + 1]
                m = (p >= lo) & (p < hi)
                n = int(m.sum())
                if n == 0:
                    print(f"{name:16s} {f'{lo:.2f}-{min(hi,1.0):.2f}':>14s} "
                          f"{0:9d} {'0.00%':>8s} {'--':>13s} {'--':>13s} {'--':>11s}")
                    continue
                pv, tv = float(p[m].mean()), float(y[m].mean())
                print(f"{name:16s} {f'{lo:.2f}-{min(hi,1.0):.2f}':>14s} {n:9d} "
                      f"{100*n/len(p):7.2f}% {100*pv:12.1f}% {100*tv:12.1f}% "
                      f"{100*(pv-tv):10.1f}%")
            print()

    print("Lesart: die Steigungsfrage (B != 1) entscheidet sich in den Bins ab 0,5.")
    print("Wo dort kaum Faelle liegen, ist sie aus dieser Quelle NICHT fittbar.")


if __name__ == "__main__":
    main()
