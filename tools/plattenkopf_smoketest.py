# -*- coding: utf-8 -*-
"""Rauchtest fuer den Plattenkopf (`evaluations/PREREG_plattenkopf.md`).

## Was hier geprueft wird -- und was NICHT

Geprueft wird die **Risikofrage vor der Nachtschicht**: sind die 18 Atome
(9 Kuppelslots x Kriterium 3/6) aus den vorhandenen Merkmalen ueberhaupt
lernbar, und schlaegt ein gelernter Kopf die GRUNDRATE? Faellt das durch,
waeren Schema-Bump (~0), Cache-Neubau (~3 h) und Training (~3,5 h) verloren.

NICHT geprueft wird die Endfassung: hier haengt ein kleines MLP direkt an
`state_to_tensor` + `state_to_planes`, nicht an der gemeinsamen Repraesentation
des Champions. Das ist die **schwierigere** Aufgabe (kein gelernter Rumpf) und
damit ein konservativer Test: was hier lernbar ist, ist es dort auch.

## Entscheidungsgroesse: Brier-SKILL-Score, nicht roher Brier

Kriterium 6 hat eine Grundrate von ~83 % (`tools/plattenkopf_labels.py stats`).
Ein Kopf, der konstant 0,83 ausgibt, erreicht einen praechtigen Brier und
unterscheidet nichts. Deshalb:

    Skill = 1 - Brier(Modell) / Brier(Grundrate)

Skill <= 0 heisst: nicht besser als die Grundrate, also wertlos. Der
Trivialitaets-Wachhund ist mitgerechnet und muss bei Skill 0 landen.

## Label-Vorbehalt (aus dem PREREG uebernommen)

Die Labels stammen vom LETZTEN TILING-SCHRITT einer Partie, nicht vom Zustand
nach Spielende -- exakte Endlabels liegen im Bestandskorpus nicht vor. Sie
unterzaehlen Fuellungen leicht. Fuer diesen Test unerheblich (es geht um
Lernbarkeit), fuer einen Champion-Kandidaten nicht.

Aufruf:

    python tools/plattenkopf_smoketest.py --files 30 --epochs 12
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
sys.path.insert(0, str(REPO / "tools"))

NUM_SLOTS = 9
CRITERIA = {"c6": 6, "c3": 3}   # Kopf-Block -> Wertungsplatten-ID


def load_dataset(pattern: str, n_files: int, max_states: int):
    """Zustaende + 18 Atome + Aktiv-Maske. Labels je Partie einmal, dann
    auf alle Datensaetze derselben Partie gestempelt -- wie `scores`."""
    import neural_net as nn_mod
    from plattenkopf_labels import group_games, labels_for_board

    files = sorted(glob.glob(str(REPO / "data" / pattern)))[:n_files]
    if not files:
        raise SystemExit(f"keine Dateien fuer {pattern}")

    feats_flat, feats_planes, targets, masks, game_ids = [], [], [], [], []
    per_criterion_positives = collections.Counter()
    per_criterion_total = collections.Counter()

    for path in files:
        with open(path, "rb") as fh:
            records = pickle.load(fh)
        for gid, recs in group_games(records).items():
            last = recs[-1]["state"]
            active = set(last.get("scoring_tile_ids") or [])
            if not (active & set(CRITERIA.values())):
                continue  # keine der beiden Platten aktiv -> traegt kein Signal
            # Labels je Spieler aus dem Endbrett
            board_labels = [labels_for_board(p) for p in last["players"]]
            for rec in recs:
                if rec["state"].get("phase") != "drafting":
                    continue
                pi = rec.get("player", rec["state"].get("current_player", 0))
                lab = board_labels[pi] if pi < len(board_labels) else board_labels[0]
                tgt, msk = [], []
                for key, crit_id in CRITERIA.items():
                    on = 1.0 if crit_id in active else 0.0
                    for v in lab[key]:
                        tgt.append(float(v))
                        msk.append(on)
                        if on:
                            per_criterion_total[key] += 1
                            per_criterion_positives[key] += v
                st = rec["state"]
                feats_flat.append(nn_mod.state_to_tensor(st))
                feats_planes.append(nn_mod.state_to_planes(st))
                targets.append(tgt)
                masks.append(msk)
                game_ids.append(gid)
                if len(targets) >= max_states:
                    break
            if len(targets) >= max_states:
                break
        if len(targets) >= max_states:
            break

    base_rates = {k: per_criterion_positives[k] / max(1, per_criterion_total[k])
                  for k in CRITERIA}
    return feats_flat, feats_planes, targets, masks, base_rates, game_ids


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pattern", default="selfplay_v20wdl_*.pkl")
    ap.add_argument("--files", type=int, default=30)
    ap.add_argument("--max-states", type=int, default=20000)
    ap.add_argument("--epochs", type=int, default=12)
    ap.add_argument("--batch", type=int, default=256)
    ap.add_argument("--hidden", type=int, default=256)
    args = ap.parse_args()

    import torch
    import torch.nn as nn

    print("Lade Korpus und stempele Labels ...")
    flat, planes, tgt, msk, base, gids = load_dataset(args.pattern, args.files, args.max_states)
    if not tgt:
        raise SystemExit("keine verwertbaren Zustaende gefunden")

    X_flat = torch.stack([f if torch.is_tensor(f) else torch.tensor(f) for f in flat]).float()
    X_pl = torch.stack([p if torch.is_tensor(p) else torch.tensor(p) for p in planes]).float()
    Y = torch.tensor(tgt).float()
    M = torch.tensor(msk).float()
    X = torch.cat([X_flat, X_pl.flatten(1)], dim=1)

    # Schnitt NACH PARTIE, nicht nach Index: alle Zustaende einer Partie tragen
    # DASSELBE Label. Ein Index-Schnitt laesst das Modell die Partie auswendig
    # lernen, und die effektive Stichprobe ist die Zahl der PARTIEN, nicht der
    # Zustaende. Der erste Lauf zeigte genau das (Trainingsverlust 0,005 bei
    # c3-Skill -0,494).
    n = X.shape[0]
    uniq = sorted(set(gids))
    n_val_games = max(1, int(len(uniq) * 0.2))
    val_games = set(uniq[-n_val_games:])
    is_val = torch.tensor([g in val_games for g in gids])
    print(f"{n} Zustaende aus {len(uniq)} Partien, Eingabebreite {X.shape[1]}")
    print(f"Schnitt nach Partie: {len(uniq)-n_val_games} Train / {n_val_games} Val")
    for k, v in base.items():
        print(f"  Grundrate {k}: {v:.3f}  (aktive Atome: {int(M.sum(0)[0 if k=='c6' else NUM_SLOTS].item())})")

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    model = nn.Sequential(
        nn.Linear(X.shape[1], args.hidden), nn.ReLU(),
        nn.Linear(args.hidden, args.hidden), nn.ReLU(),
        nn.Linear(args.hidden, 2 * NUM_SLOTS),
    ).to(dev)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    lossfn = nn.BCEWithLogitsLoss(reduction="none")

    tr, va = ~is_val, is_val
    Xtr, Ytr, Mtr = X[tr].to(dev), Y[tr].to(dev), M[tr].to(dev)
    Xva, Yva, Mva = X[va].to(dev), Y[va].to(dev), M[va].to(dev)

    def val_skill():
        model.eval()
        with torch.no_grad():
            pv = torch.sigmoid(model(Xva))
        out = {}
        for k, off in (("c6", 0), ("c3", NUM_SLOTS)):
            sl = slice(off, off + NUM_SLOTS)
            m = Mva[:, sl]
            if m.sum() == 0:
                continue
            y, p = Yva[:, sl], pv[:, sl]
            brier = (((p - y) ** 2) * m).sum() / m.sum()
            rate = (y * m).sum() / m.sum()
            bb = (((rate - y) ** 2) * m).sum() / m.sum()
            out[k] = 1.0 - (brier / bb).item()
        return out

    # Fruehstopp auf dem MITTLEREN Val-Skill. Ohne ihn misst der Endstand das
    # Ueberlernen statt der Lernbarkeit: alle Zustaende einer Partie tragen
    # dasselbe Label, die effektive Stichprobe ist also die Zahl der PARTIEN.
    best, best_state, patience = -9.9, None, 0
    for ep in range(args.epochs):
        model.train()
        perm = torch.randperm(Xtr.shape[0], device=dev)
        tot = 0.0
        nb = 0
        for i in range(0, Xtr.shape[0], args.batch):
            idx = perm[i:i + args.batch]
            opt.zero_grad()
            out = model(Xtr[idx])
            raw = lossfn(out, Ytr[idx]) * Mtr[idx]
            loss = raw.sum() / Mtr[idx].sum().clamp(min=1)
            loss.backward()
            opt.step()
            tot += loss.item()
            nb += 1
        sk = val_skill()
        mean_sk = sum(sk.values()) / max(1, len(sk))
        marks = " ".join(f"{k} {v:+.3f}" for k, v in sk.items())
        print(f"  Epoche {ep+1:>2}: Verlust {tot/max(1,nb):.4f} | Val-Skill {marks}")
        if mean_sk > best + 1e-4:
            best, patience = mean_sk, 0
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        else:
            patience += 1
            if patience >= 3:
                print(f"  Fruehstopp nach Epoche {ep+1} (bester mittlerer Skill {best:+.3f})")
                break
    if best_state is not None:
        model.load_state_dict(best_state)


    print("\n--- Ergebnis je Kriterium (Validierung) ---")
    verdicts = []
    with torch.no_grad():
        pv = torch.sigmoid(model(Xva))
    for k, off in (("c6", 0), ("c3", NUM_SLOTS)):
        sl = slice(off, off + NUM_SLOTS)
        m = Mva[:, sl]
        if m.sum() == 0:
            print(f"  {k}: keine aktiven Atome in der Validierung")
            continue
        y, p = Yva[:, sl], pv[:, sl]
        brier = (((p - y) ** 2) * m).sum() / m.sum()
        rate = (y * m).sum() / m.sum()
        brier_base = (((rate - y) ** 2) * m).sum() / m.sum()
        skill = 1.0 - (brier / brier_base).item()
        # Trivialitaets-Wachhund: konstanter Kopf MUSS Skill 0 liefern
        watchdog = 1.0 - ((((rate - y) ** 2) * m).sum() / m.sum() / brier_base).item()
        print(f"  {k}: Grundrate {rate.item():.3f} | Brier {brier.item():.4f} "
              f"| Brier(Grundrate) {brier_base.item():.4f} | **Skill {skill:+.3f}** "
              f"| Wachhund {watchdog:+.3f}")
        verdicts.append((k, skill))

    print()
    if all(sk > 0.02 for _, sk in verdicts) and verdicts:
        print("VERDIKT: beide Kriterien schlagen die Grundrate ⇒ die Atome sind aus den")
        print("vorhandenen Merkmalen lernbar. Schema-Bump, Cache-Neubau und Training")
        print("sind gerechtfertigt.")
    elif any(sk > 0.02 for _, sk in verdicts):
        print("VERDIKT: nur EIN Kriterium schlaegt die Grundrate. Das andere gehoert")
        print("vor dem Bau geklaert -- sonst traegt der Kopf einen toten Block mit.")
    else:
        print("VERDIKT: kein Kriterium schlaegt die Grundrate. NICHT bauen -- die Labels")
        print("sind aus diesen Merkmalen nicht vorhersagbar, und ein Nachtlauf waere")
        print("verlorene Zeit. Ursache klaeren (Merkmale? Label-Zuordnung? Spieler-Index?).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
