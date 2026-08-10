# -*- coding: utf-8 -*-
"""Bedingte Skill-Pruefung je Atom fuer die 34 Zusatzziele des Ownership-Kopfs.

## Warum es dieses Werkzeug gibt

Am 2026-08-10 hat die aggregierte Auswertung des c6-Ziels einen Skill von
+0,637 gezeigt -- und die Aufschlüsselung je Slot ergab, dass **jeder einzelne
Slot NEGATIV** war. Der aggregierte Wert war ein reiner Poolungs-Effekt: gegen
die GEPOOLTE Grundrate gewinnt ein Modell schon dadurch, dass es lernt, WELCHES
Atom es ist -- und das steht in der Eingabe. Gegen die Grundrate des jeweiligen
Atoms gewann es nirgends.

Dieses Werkzeug prueft deshalb **je Atom einzeln**, mit dem Atom als eigener
Referenz, und beantwortet die einzige Frage, die vor einem `OWNERSHIP_WEIGHT`
> 0 zaehlt: traegt das Ziel Signal, oder ist es positionsbestimmt?

## Der Waechter gegen entartete Grundraten

Slot 7 lieferte in derselben Messung einen Skill von -3,7e27. Ursache: die
Grundrate war exakt 1,000, damit ist `Brier(Grundrate) = 0` und der Skill
dividiert durch Null. Solche Atome sind **nicht schlecht vorhergesagt, sie sind
konstant** -- und ein Skill ist auf ihnen nicht definiert. Der Waechter meldet
sie als ENTARTET, statt eine Zahl zu erfinden:

  * `min(rate, 1-rate) < DEGENERATE_RATE`  -> praktisch konstant
  * `Brier(Grundrate) < DEGENERATE_BRIER`  -> keine Varianz zu erklaeren
  * `n < MIN_OBS`                          -> zu wenige Beobachtungen

Ein entartetes Atom ist ein BEFUND, kein Messfehler: es sagt, dass die Groesse
aus der Position folgt und eine Tabelle sie erledigt.

## Zuschnitt

Labels kommen aus `neural_net._conjunctions_from_dome` -- dem AUTORITATIVEN
Bauer, nicht aus einer Kopie. Schnitt nach PARTIE (alle Zustaende einer Partie
tragen dasselbe Label, die effektive Stichprobe ist die Zahl der Partien).
Fruehstopp auf dem mittleren Skill der nicht-entarteten Atome.

Aufruf:

    python tools/atom_skill_check.py --files 400 --max-states 300000
"""
from __future__ import annotations

import argparse
import collections
import glob
import pickle
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "engine" / "py"))

DEGENERATE_RATE = 0.01     # naeher als 1 % an 0 oder 1 -> konstant
DEGENERATE_BRIER = 1e-4    # keine Varianz zu erklaeren
MIN_OBS = 200              # zu wenige Beobachtungen fuer eine Aussage

# Namen in der Reihenfolge von `_conjunctions_from_dome`
ATOM_NAMES = (
    [f"Reihe {r+1} vollst." for r in range(6)]
    + [f"Spalte {c+1} vollst." for c in range(6)]
    + ["Diagonale H", "Diagonale N"]
    + [f"Ecke {n}" for n in ("(0,0)", "(0,2)", "(2,0)", "(2,2)")]
    + ["ALLE Jokerfelder belegt"]
    + [f"Reihe {r+1} >=5 Farben" for r in range(6)]
    + [f"Layout: Slot {s} traegt Joker" for s in range(9)]
)


def load(pattern: str, n_files: int, max_states: int):
    import neural_net as nn_mod

    files = sorted(glob.glob(str(REPO / "data" / pattern)))[:n_files]
    if not files:
        raise SystemExit(f"keine Dateien fuer {pattern}")

    flat, planes, targets, gids = [], [], [], []
    for path in files:
        with open(path, "rb") as fh:
            records = pickle.load(fh)
        by = collections.defaultdict(list)
        for rec in records:
            by[rec["game_id"]].append(rec)
        for gid, recs in by.items():
            last = recs[-1]["state"]
            if not recs[-1].get("completed"):
                continue  # unvollstaendige Partie -> kein Endbrett (Muster ownership)
            per_player = [nn_mod._conjunctions_from_dome(p["dome_grid"])
                          for p in last["players"]]
            for rec in recs:
                st = rec["state"]
                if st.get("phase") != "drafting":
                    continue
                pi = st.get("current_player", 0)
                lab = per_player[pi] if pi < len(per_player) else per_player[0]
                flat.append(nn_mod.state_to_tensor(st))
                planes.append(nn_mod.state_to_planes(st))
                targets.append([float(v) for v in lab])
                gids.append(gid)
                if len(targets) >= max_states:
                    break
            if len(targets) >= max_states:
                break
        if len(targets) >= max_states:
            break
    return flat, planes, targets, gids


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pattern", default="selfplay_v20wdl_*.pkl")
    ap.add_argument("--files", type=int, default=400)
    ap.add_argument("--max-states", type=int, default=300000)
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--batch", type=int, default=256)
    ap.add_argument("--hidden", type=int, default=384)
    args = ap.parse_args()

    import torch
    import torch.nn as nn

    print("Lade Korpus und baue Labels ueber _conjunctions_from_dome ...", flush=True)
    flat, planes, tgt, gids = load(args.pattern, args.files, args.max_states)
    if not tgt:
        raise SystemExit("keine verwertbaren Zustaende")

    X = torch.cat([
        torch.stack([f if torch.is_tensor(f) else torch.tensor(f) for f in flat]).float(),
        torch.stack([p if torch.is_tensor(p) else torch.tensor(p) for p in planes]).float().flatten(1),
    ], dim=1)
    Y = torch.tensor(tgt).float()
    n_atoms = Y.shape[1]
    if n_atoms != len(ATOM_NAMES):
        print(f"WARNUNG: {n_atoms} Atome, aber {len(ATOM_NAMES)} Namen -- Namensliste veraltet?")

    uniq = sorted(set(gids))
    n_val = max(1, int(len(uniq) * 0.2))
    val_games = set(uniq[-n_val:])
    is_val = torch.tensor([g in val_games for g in gids])
    print(f"{X.shape[0]} Zustaende aus {len(uniq)} Partien, {n_atoms} Atome, "
          f"Schnitt {len(uniq)-n_val} / {n_val} Partien")

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    model = nn.Sequential(
        nn.Linear(X.shape[1], args.hidden), nn.ReLU(),
        nn.Linear(args.hidden, args.hidden), nn.ReLU(),
        nn.Linear(args.hidden, n_atoms),
    ).to(dev)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    lossfn = nn.BCEWithLogitsLoss()

    Xtr, Ytr = X[~is_val].to(dev), Y[~is_val].to(dev)
    Xva, Yva = X[is_val].to(dev), Y[is_val].to(dev)

    def per_atom():
        """(Name, n, rate, brier, brier_base, skill|None, grund) je Atom."""
        model.eval()
        with torch.no_grad():
            pv = torch.sigmoid(model(Xva))
        rows = []
        for a in range(n_atoms):
            y, p = Yva[:, a], pv[:, a]
            n = int(y.numel())
            rate = y.mean().item()
            brier = ((p - y) ** 2).mean().item()
            bb = ((rate - y) ** 2).mean().item()
            name = ATOM_NAMES[a] if a < len(ATOM_NAMES) else f"Atom {a}"
            if n < MIN_OBS:
                rows.append((name, n, rate, brier, bb, None, f"n<{MIN_OBS}"))
            elif min(rate, 1.0 - rate) < DEGENERATE_RATE:
                rows.append((name, n, rate, brier, bb, None, "konstant"))
            elif bb < DEGENERATE_BRIER:
                rows.append((name, n, rate, brier, bb, None, "keine Varianz"))
            else:
                rows.append((name, n, rate, brier, bb, 1.0 - brier / bb, ""))
        return rows

    best, best_state, patience = -9.9, None, 0
    for ep in range(args.epochs):
        model.train()
        perm = torch.randperm(Xtr.shape[0], device=dev)
        tot = nb = 0
        for i in range(0, Xtr.shape[0], args.batch):
            idx = perm[i:i + args.batch]
            opt.zero_grad()
            loss = lossfn(model(Xtr[idx]), Ytr[idx])
            loss.backward()
            opt.step()
            tot += loss.item(); nb += 1
        sk = [r[5] for r in per_atom() if r[5] is not None]
        mean_sk = sum(sk) / max(1, len(sk))
        print(f"  Epoche {ep+1:>2}: Verlust {tot/max(1,nb):.4f} | "
              f"mittlerer Skill {mean_sk:+.3f} ueber {len(sk)} nicht-entartete Atome", flush=True)
        if mean_sk > best + 1e-4:
            best, patience = mean_sk, 0
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        else:
            patience += 1
            if patience >= 3:
                print(f"  Fruehstopp nach Epoche {ep+1} (bester Schnitt {best:+.3f})")
                break
    if best_state is not None:
        model.load_state_dict(best_state)

    print(f"\n{'Atom':30} {'Grundrate':>9} {'Brier':>8} {'Br(Rate)':>9} {'Skill':>8}  Bemerkung")
    pos = neg = degen = 0
    for name, n, rate, brier, bb, skill, why in per_atom():
        if skill is None:
            degen += 1
            print(f"{name:30} {rate:>9.3f} {brier:>8.4f} {bb:>9.5f} {'--':>8}  ENTARTET ({why})")
        else:
            if skill > 0.02: pos += 1
            elif skill < -0.02: neg += 1
            print(f"{name:30} {rate:>9.3f} {brier:>8.4f} {bb:>9.5f} {skill:>+8.3f}")

    print(f"\n{pos} Atome mit Skill > +0,02 | {neg} mit < -0,02 | {degen} entartet")
    print("\nLesart: ENTARTET ist ein BEFUND, kein Messfehler -- die Groesse folgt aus")
    print("der Position, eine Tabelle erledigt sie. Ein Kopf lohnt nur fuer Atome mit")
    print("positivem Skill; alles andere kostet Kapazitaet und Gradientenanteil.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
