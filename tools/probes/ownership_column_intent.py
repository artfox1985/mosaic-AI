"""Sagt der Feld-Kopf die ABSICHT vorher oder die GEOMETRIE?

FRAGE (Nutzer 2026-08-18): der Kopf gibt je Feld P(am Ende belegt) aus. Wenn
eine Spalte gleich weit gebaut ist, sollte die Vorhersage fuer die NOCH
FEHLENDEN Felder dieser Spalte gleich sein -- egal wer spielt. Ist sie im
Spaltenbauer-Arm deutlich hoeher als im ungelenkten Arm, sagt der Kopf die
Absicht der Politik vorher und nicht die Brettlage.

Aufbau: je Zustand und Spielerbrett wird der AKTUELLE Fuellstand jeder Spalte
gezaehlt (0..6). Fuer Fuellstaende 1..5 wird der Mittelwert der Kopf-Vorhersage
ueber die noch LEEREN Felder dieser Spalte gebildet, dazu die tatsaechliche
Vollendungsrate derselben Spalte am Spielende. Verglichen werden die Arme bei
GLEICHEM Fuellstand -- die Brettlage ist damit kontrolliert.

Lesart:
  * Vorhersage im k1-Arm >> in Arm a  UND  Vollendungsrate ebenso hoeher
    -> der Kopf sagt die Absicht vorher, und er hat damit RECHT. Die Groesse
       ist politikabhaengig, wie in STATUS.md beschrieben.
  * Vorhersagen aehnlich, Vollendungsraten verschieden
    -> der Kopf sieht die Absicht NICHT und ist im Bauer-Arm zu pessimistisch.

Aufruf: python ownership_column_intent.py [dateien_je_arm] [checkpoint]
"""
import collections
import glob
import pickle
import re
import sys
from pathlib import Path

import numpy as np
import torch

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "engine" / "py"))
sys.path.insert(0, str(REPO / "tools" / "probes"))
import ownership_gate_a as GA  # noqa: E402
from neural_net import _ownership_from_dome  # noqa: E402

ARME = ("a", "k1", "heur")
RUNDEN = (2, 3, 4)          # mittleres Spiel -- dort faellt die Entscheidung
DATEIEN_JE_ARM = int(sys.argv[1]) if len(sys.argv) > 1 else 30
CHECKPOINT = sys.argv[2] if len(sys.argv) > 2 else "alphazero_v21-b19_best.pth"

# Ownership-Index -> Rasterposition. ABGELESEN aus `_ownership_from_dome`
# (slot_row-major, dann space_index) und `_dome_grids_from_dome`
# (r = sr*2 + si//2, c = sc*2 + si%2), nicht hergeleitet.
SPALTEN = collections.defaultdict(list)
for _sr in range(3):
    for _sc in range(3):
        for _si in range(4):
            _i = (_sr * 3 + _sc) * 4 + _si
            SPALTEN[_sc * 2 + _si % 2].append(_i)
SPALTEN = {c: sorted(v) for c, v in SPALTEN.items()}


def stichprobe(dateien, k):
    d = sorted(dateien)
    if len(d) <= k:
        return d
    schritt = len(d) / k
    return [d[int(i * schritt)] for i in range(k)]


def main():
    for c, idx in SPALTEN.items():
        assert len(idx) == 6, f"Spalte {c} hat {len(idx)} Felder -- Indexplan falsch"

    arme = collections.defaultdict(list)
    for f in glob.glob(str(REPO / "data" / "holdout" / "*.pkl")):
        m = re.match(r"selfplay_hold_([a-z0-9]+)_", Path(f).name)
        if m and m.group(1) in ARME:
            arme[m.group(1)].append(f)

    ck = torch.load(REPO / "models" / CHECKPOINT, map_location="cpu", weights_only=False)
    model, _enc = GA.build_model_from_checkpoint(ck)
    model.eval().to(GA.DEVICE)
    print(f"Checkpoint {CHECKPOINT} auf {GA.DEVICE}", flush=True)

    # arm -> fuellstand -> [summe_p, n, vollendet]
    # je Fuellstand: [summe p_leer, n, vollendet, summe Produkt ueber ALLE 6,
    #                 summe p der bereits BELEGTEN Felder]
    stat = {a: collections.defaultdict(lambda: [0.0, 0, 0, 0.0, 0.0]) for a in ARME}

    for arm in ARME:
        dateien = stichprobe(arme[arm], DATEIEN_JE_ARM)
        states, cps, cur_boards, end_boards = [], [], [], []
        for f in dateien:
            with open(f, "rb") as fh:
                daten = pickle.load(fh)
            je_spiel = collections.defaultdict(list)
            for s in daten:
                je_spiel[s["game_id"]].append(s)
            for _gid, recs in je_spiel.items():
                if not recs[-1].get("completed"):
                    continue
                sp_end = recs[-1]["state"]["players"]
                ende = [np.array(_ownership_from_dome(sp_end[i]["dome_grid"]), dtype=np.int8)
                        for i in (0, 1)]
                nach_runde = collections.defaultdict(list)
                for r in recs:
                    nach_runde[r["state"].get("round")].append(r)
                for rnd in RUNDEN:
                    gruppe = nach_runde.get(rnd)
                    if not gruppe:
                        continue
                    rec = gruppe[len(gruppe) // 2]
                    sp = rec["state"]["players"]
                    states.append(rec["state"])
                    cps.append(rec["state"].get("current_player", 0))
                    cur_boards.append([np.array(_ownership_from_dome(sp[i]["dome_grid"]),
                                                dtype=np.int8) for i in (0, 1)])
                    end_boards.append(ende)
        planes, flat = GA.encode_states(states)
        p_all = GA.predict_ownership(model, planes, flat)
        print(f"  Arm {arm}: {len(dateien)} Dateien -> {len(states)} Zustaende", flush=True)

        for n, cp in enumerate(cps):
            for seite, pi in ((0, cp), (1, 1 - cp)):     # 0 = Ego-Haelfte [0:36]
                p = p_all[n, seite * 36:(seite + 1) * 36]
                cur = cur_boards[n][pi]
                ende = end_boards[n][pi]
                for _c, idx in SPALTEN.items():
                    fuell = int(cur[idx].sum())
                    if not 1 <= fuell <= 5:
                        continue
                    leer = [i for i in idx if cur[i] == 0]
                    belegt = [i for i in idx if cur[i] == 1]
                    z = stat[arm][fuell]
                    z[0] += float(p[leer].mean())
                    z[1] += 1
                    z[2] += int(ende[idx].all())
                    z[3] += float(np.prod(p[idx]))
                    z[4] += float(p[belegt].mean())

    print()
    print("=" * 92)
    print(f"KOPF-VORHERSAGE FUER DIE NOCH FEHLENDEN FELDER, je Fuellstand der Spalte")
    print(f"(Runden {RUNDEN}, beide Spielerbretter, Fuellstand kontrolliert)")
    print("=" * 92)
    for a in ARME:
        print()
        print(f"--- Arm {a}")
        print(f"{'Fuell':>6s} {'p_belegt':>10s} {'p_leer':>9s} {'Produkt':>9s} "
              f"{'tatsaechlich':>13s} {'Faktor':>8s} {'n':>7s}")
        for fuell in range(1, 6):
            s, n, v, pr, pb = stat[a][fuell]
            if n == 0:
                continue
            prod, echt = pr / n, v / n
            fak = echt / prod if prod > 0 else float("inf")
            print(f"{fuell:6d} {100*pb/n:9.1f}% {100*s/n:8.1f}% {100*prod:8.2f}% "
                  f"{100*echt:12.1f}% {fak:7.1f}x {n:7d}")

    print()
    print("p_leer = mittlere Kopf-Vorhersage fuer die noch LEEREN Felder der Spalte.")
    print("voll   = Anteil der Spalten, die am Spielende tatsaechlich voll waren.")
    print("Gleicher Fuellstand = gleiche Brettlage. Weicht p_leer zwischen den Armen")
    print("ab, sieht der Kopf die ABSICHT und nicht nur die Geometrie.")


if __name__ == "__main__":
    main()
