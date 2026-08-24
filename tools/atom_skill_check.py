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

## Der Konfundierer der 9 Layout-Atome (Indizes 25..33)

Die Layout-Atome fragen "traegt Slot s am ENDE eine Jokerplatte". Eine einmal
gelegte Platte wird nie wieder bewegt (nachgemessen: 13219 belegte
Slot-Beobachtungen, 0 Abweichung von Platten-Id und WILD-Eigenschaft des
Endzustands) -- und der Raumtyp einer gelegten Platte steht in der Eingabe
(`state_to_tensor`: `TYPE_MAP` mit WILD=0,5; `state_to_planes`:
`_SPACE_TYPE_IDX`). Fuer jeden Slot, der im BETRACHTETEN Zustand schon eine
Platte traegt, ist das Label also trivial ABLESBAR: der Kopf schreibt die
sichtbare Platzierung fort und sagt nichts vorher.

Weil die Slots frueh und in fester Reihenfolge belegt werden (Runde 1: 0 Slots,
Runde 4: alle 9), ist der Ablese-Anteil je Slot unterschiedlich gross -- genau
die Achse, entlang der die unbedingten Skills abfallen.

`--conditional-layout` wertet die 9 Layout-Atome deshalb nur auf Zustaenden aus,
in denen der jeweilige Slot noch KEINE Platte traegt (`dome_grid[sr][sc] is
None`), Grundrate und Brier-Referenz eingeschlossen. Bedingt UND unbedingt
kommen dabei aus DEMSELBEN Modell -- der Unterschied ist ausschliesslich die
Bedingung, nicht das Training. `--mask-train-layout` nimmt die abgelesenen
Zellen zusaetzlich aus dem Trainingsverlust; das gibt dem Kopf die reine
Vorhersageaufgabe, ohne Gradientenanteil fuer das Abschreiben.

Bei starker Bedingung sinkt n je Slot deutlich -- entartete Atome sind dann
erwartbar und ein BEFUND, kein Fehler.

## Zuschnitt

Labels kommen aus `neural_net._conjunctions_from_dome` -- dem AUTORITATIVEN
Bauer, nicht aus einer Kopie. Schnitt nach PARTIE (alle Zustaende einer Partie
tragen dasselbe Label, die effektive Stichprobe ist die Zahl der Partien).
Fruehstopp auf dem mittleren Skill der nicht-entarteten Atome -- im bedingten
Modus auf den BEDINGTEN Layout-Skills, damit die Bedingung ihre beste Epoche
bekommt.

## Zweites Ziel: die 36 OWNERSHIP-Zellen (`--target ownership`)

Fuer eine konvexe Aggregation (`(Summe P ueber die Zellen eines Kriteriums / n)^2
x Punktwert`, Muster `scoring_progress`) sind nicht die Konjunktionen die
Grundlage, sondern die RANDwahrscheinlichkeiten je Zelle aus
`_ownership_from_dome`. Die Frage ist, ob die einzelnen Zellen Signal tragen --
auch dort, wo die Vollendung nie eintritt.

Derselbe Konfundierer wirkt hier und wird GETRENNT ausgewiesen, in drei Strata
je Zelle und Zustand:

  * Zelle schon belegt        -> Endlabel trivial 1 (nachgemessen: 11104 belegte
                                Zellen, 0 Ausnahmen) -> ABLESEN, kein Vorhersagen
  * Platte liegt, Zelle leer  -> echte Vorhersage innerhalb der gelegten Platte
  * Slot ohne Platte          -> Vorhersage einschliesslich der Plattenwahl

Zusaetzlich fasst der Bericht die Zellen nach den Kriterien-Geometrien zusammen
(Randzellen, Kuppelreihen, Spalten, Diagonalen, Eckslots; Umrechnung
`r = sr*2 + si//2`, `c = sc*2 + si%2`).

Aufruf:

    python tools/atom_skill_check.py --files 400 --max-states 300000
    python tools/atom_skill_check.py --files 200 --max-states 150000 --conditional-layout
    python tools/atom_skill_check.py --files 200 --max-states 150000 \
        --target both --conditional-layout
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

N_LAYOUT = 9  # die letzten N_LAYOUT Atome sind die Layout-Ausgaenge (25..33)

# Namen der 36 Ownership-Zellen in der Reihenfolge von `_ownership_from_dome`:
# slot_row-major, dann space_index. Rasterlage nach `_dome_grids_from_dome`:
# r = sr*2 + si//2, c = sc*2 + si%2.
CELL_NAMES = [f"Slot({sr},{sc}) F{si} -> ({sr*2+si//2},{sc*2+si%2})"
              for sr in range(3) for sc in range(3) for si in range(4)]
CELL_RC = [(sr * 2 + si // 2, sc * 2 + si % 2)
           for sr in range(3) for sc in range(3) for si in range(4)]
CELL_SLOT = [(sr, sc) for sr in range(3) for sc in range(3) for _ in range(4)]

# Zustandsstrata einer Zelle (der Konfundierer, getrennt ausgewiesen)
ST_FILLED, ST_EMPTY_ON_PLATE, ST_NO_PLATE = 0, 1, 2


def _cell_groups():
    """Kriterien-Geometrien -> Zellindizes (0..35). Punktwerte aus scoring.rs
    wie in `_conjunctions_from_dome` dokumentiert."""
    g: list[tuple[str, list[int]]] = []
    g.append(("K4 Randzellen (+1 je Feld)",
              [i for i, (r, c) in enumerate(CELL_RC) if r in (0, 5) or c in (0, 5)]))
    g.append(("K4 Innenzellen (kein Rand)",
              [i for i, (r, c) in enumerate(CELL_RC) if r not in (0, 5) and c not in (0, 5)]))
    for r in range(6):
        g.append((f"K0 Reihe {r+1} (+3)", [i for i, rc in enumerate(CELL_RC) if rc[0] == r]))
    for c in range(6):
        g.append((f"K1 Spalte {c+1} (+7)", [i for i, rc in enumerate(CELL_RC) if rc[1] == c]))
    g.append(("K2 Diagonale H (+10)", [i for i, (r, c) in enumerate(CELL_RC) if r == c]))
    g.append(("K2 Diagonale N (+10)", [i for i, (r, c) in enumerate(CELL_RC) if r + c == 5]))
    for (sr, sc), pts in ((("0", "0"), "+3"), (("0", "2"), "+3"),
                          (("2", "0"), "+8"), (("2", "2"), "+8")):
        sr_i, sc_i = int(sr), int(sc)
        g.append((f"K5 Eckslot ({sr},{sc}) ({pts})",
                  [i for i, s in enumerate(CELL_SLOT) if s == (sr_i, sc_i)]))
    return g


def _cell_status(dome_grid) -> list[int]:
    """36 Statuswerte je Zelle im BETRACHTETEN Zustand -- die Trennung, die der
    Konfundierer verlangt:

      ST_FILLED         Zelle schon belegt -> Endlabel trivial 1 (nachgemessen:
                        11104 belegte Zellen, 0 Ausnahmen)
      ST_EMPTY_ON_PLATE Platte liegt, Zelle leer -> echte Vorhersage
      ST_NO_PLATE       Slot traegt noch keine Platte -> Vorhersage einschliesslich
                        der Plattenwahl

    Reihenfolge und Randfaelle identisch zu `_ownership_from_dome`.
    """
    out: list[int] = []
    for sr in range(3):
        row = dome_grid[sr] if sr < len(dome_grid) else []
        for sc in range(3):
            slot = row[sc] if sc < len(row) else None
            if not slot:
                out += [ST_NO_PLATE] * 4
                continue
            spaces = slot.get("spaces", [])
            for si in range(4):
                sp = spaces[si] if si < len(spaces) else None
                out.append(ST_FILLED if (sp and sp.get("filled") is not None)
                           else ST_EMPTY_ON_PLATE)
    return out


def _slots_filled(dome_grid) -> list[int]:
    """9 Marker (slot_row-major): 1 = Slot traegt im BETRACHTETEN Zustand schon
    eine Platte, damit ist sein Layout-Label trivial ablesbar. Reihenfolge und
    Randfallbehandlung identisch zu `_conjunctions_from_dome` (25..33)."""
    out: list[int] = []
    for sr in range(3):
        row = dome_grid[sr] if sr < len(dome_grid) else []
        for sc in range(3):
            slot = row[sc] if sc < len(row) else None
            out.append(1 if slot else 0)
    return out


def _boot_ci(y, p, g, B: int = 2000, seed: int = 0):
    """95 %-Konfidenzband des Brier-Skills, Bootstrap ueber PARTIEN.

    Der Zustands-Bootstrap waere hier falsch: das Label ist je Partie KONSTANT,
    die Zustaende einer Partie sind praktisch derselbe Datenpunkt. Gezogen wird
    darum ueber Partien (dieselbe Lektion wie bei der Arena-Block-Korrelation).

    Exakt und billig, weil bei binaeren Labels
    `Brier(Grundrate) = rate * (1 - rate)` gilt -- es genuegen drei Summen je
    Partie (n, Summe y, Summe der quadrierten Fehler).
    """
    import numpy as np

    y = np.asarray(y, dtype=np.float64)
    p = np.asarray(p, dtype=np.float64)
    _, inv = np.unique(np.asarray(g), return_inverse=True)
    G = int(inv.max()) + 1 if inv.size else 0
    if G < 2:
        return None
    n_g = np.bincount(inv, minlength=G).astype(np.float64)
    sy_g = np.bincount(inv, weights=y, minlength=G)
    sse_g = np.bincount(inv, weights=(p - y) ** 2, minlength=G)

    rng = np.random.default_rng(seed)
    idx = rng.integers(0, G, size=(B, G))
    n = n_g[idx].sum(1)
    rate = sy_g[idx].sum(1) / np.maximum(n, 1.0)
    sse = sse_g[idx].sum(1)
    bb = rate * (1.0 - rate)
    ok = bb > DEGENERATE_BRIER
    if ok.sum() < B // 2:
        return None
    sk = 1.0 - (sse[ok] / n[ok]) / bb[ok]
    return float(np.percentile(sk, 2.5)), float(np.percentile(sk, 97.5))


def _table_skill(y_tr, r_tr, y_va, r_va, n_rounds: int):
    """Brier-Skill einer 5-Parameter-Tabelle `P(Label | Runde)`.

    Die Referenz gegen den Verdacht "das Netz ist das Problem, nicht das Ziel":
    das MLP hat 1015 UNABHAENGIGE Partien, aber 120.000 fast identische
    Zustaende -- es kann partiespezifisch memorieren und dabei unter die
    Grundrate fallen. Eine geglaettete Rundentabelle kann das nicht. Faellt sie
    positiv aus, wo das Netz negativ ist, liegt es am Probe; ist auch sie null,
    traegt die Zelle ueber die Runde hinaus nichts.
    """
    import numpy as np

    if y_tr.size == 0 or y_va.size == 0:
        return None
    prior = float(y_tr.mean())
    cnt = np.bincount(r_tr, minlength=n_rounds).astype(np.float64)
    pos = np.bincount(r_tr, weights=y_tr, minlength=n_rounds)
    tab = (pos + 2.0 * prior) / (cnt + 2.0)     # Rueckfall auf den Prior bei duennen Runden
    p = tab[r_va]
    rate = float(y_va.mean())
    bb = float(((rate - y_va) ** 2).mean())
    if bb < DEGENERATE_BRIER or y_va.size < MIN_OBS:
        return None
    return 1.0 - float(((p - y_va) ** 2).mean()) / bb


def load(pattern: str, n_files: int, max_states: int):
    import neural_net as nn_mod

    files = sorted(glob.glob(str(REPO / "data" / pattern)))[:n_files]
    if not files:
        raise SystemExit(f"keine Dateien fuer {pattern}")

    flat, planes, targets, gids, occ = [], [], [], [], []
    tgt_own, stat_own, rounds = [], [], []
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
            per_player_own = [nn_mod._ownership_from_dome(p["dome_grid"])
                              for p in last["players"]]
            for rec in recs:
                st = rec["state"]
                if st.get("phase") != "drafting":
                    continue
                pi = st.get("current_player", 0)
                if pi >= len(per_player):
                    pi = 0
                lab = per_player[pi]
                # Slot-Belegung DESSELBEN Spielers im BETRACHTETEN Zustand
                cur = st.get("players", [])
                grid = cur[pi]["dome_grid"] if pi < len(cur) else []
                flat.append(nn_mod.state_to_tensor(st))
                planes.append(nn_mod.state_to_planes(st))
                targets.append([float(v) for v in lab])
                occ.append(_slots_filled(grid))
                tgt_own.append([float(v) for v in per_player_own[pi]])
                stat_own.append(_cell_status(grid))
                rounds.append(int(st.get("round", 0) or 0))
                gids.append(gid)
                if len(targets) >= max_states:
                    break
            if len(targets) >= max_states:
                break
        if len(targets) >= max_states:
            break
    return flat, planes, targets, gids, occ, tgt_own, stat_own, rounds


def run_experiment(tag, X, Y, STRAT, names, is_val, gids, args, groups=None,
                   rounds=None) -> None:
    """Eine Skill-Messung ueber alle Ausgaenge EINES Ziels.

    `STRAT` ist ein [N, n_atoms]-Feld mit dem Zustandsstratum je Ausgang:
    `ST_FILLED` = im betrachteten Zustand schon entschieden und damit trivial
    ABLESBAR, `ST_EMPTY_ON_PLATE` / `ST_NO_PLATE` = noch unentschieden. Die
    bedingte Auswertung laesst genau die abgelesenen Zeilen weg, Grundrate und
    Brier-Referenz eingeschlossen.
    """
    import numpy as np
    import torch
    import torch.nn as nn

    n_atoms = Y.shape[1]
    print(f"\n{'=' * 78}\nZIEL: {tag} -- {n_atoms} Ausgaenge\n{'=' * 78}", flush=True)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    model = nn.Sequential(
        nn.Linear(X.shape[1], args.hidden), nn.ReLU(),
        nn.Linear(args.hidden, args.hidden), nn.ReLU(),
        nn.Linear(args.hidden, n_atoms),
    ).to(dev)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    lossfn = nn.BCEWithLogitsLoss()
    lossfn_cell = nn.BCEWithLogitsLoss(reduction="none")

    Xtr, Ytr = X[~is_val].to(dev), Y[~is_val].to(dev)
    Xva, Yva = X[is_val].to(dev), Y[is_val].to(dev)

    iv = is_val.numpy()
    S_tr, S_va = STRAT[~iv], STRAT[iv]
    yv_np = Yva.cpu().numpy()
    ytr_np = Ytr.cpu().numpy()
    val_gids = np.array([g for g, v in zip(gids, iv.tolist()) if v])
    R = np.asarray(rounds, dtype=np.int64) if rounds is not None else None
    R_tr, R_va = (R[~iv], R[iv]) if R is not None else (None, None)
    n_rounds = int(R.max()) + 1 if R is not None else 0

    # Zeilenauswahl je Ausgang: None = alle (unbedingt)
    KEEP_COND = S_va != ST_FILLED                     # noch unentschieden
    KEEP_PLATE = S_va == ST_EMPTY_ON_PLATE            # leere Zelle, Platte liegt
    KEEP_NOPLATE = S_va == ST_NO_PLATE                # Slot ohne Platte

    # Trainingsmaske: 1 = Zelle zaehlt. Nur unter --mask-train-decided werden die
    # trivial ablesbaren Zellen ausgeblendet.
    Mtr = None
    if args.mask_train_decided:
        Mtr = torch.tensor((S_tr != ST_FILLED).astype("float32")).to(dev)

    def per_atom(keep_mat=None):
        """(Name, n, rate, brier, brier_base, skill|None, grund) je Ausgang.

        `keep_mat` waehlt je Ausgang die Zeilen aus (bool [N_val, n_atoms]).
        Grundrate UND Brier-Referenz werden auf derselben Teilmenge gebildet --
        sonst waere die Referenz falsch und der Skill nicht interpretierbar.
        """
        model.eval()
        with torch.no_grad():
            pv = torch.sigmoid(model(Xva)).cpu().numpy()
        rows = []
        for a in range(n_atoms):
            if keep_mat is None:
                y, p = yv_np[:, a], pv[:, a]
            else:
                k = keep_mat[:, a]
                y, p = yv_np[k, a], pv[k, a]
            n = int(y.size)
            name = names[a] if a < len(names) else f"Ausgang {a}"
            if n == 0:
                rows.append((name, 0, float("nan"), float("nan"), float("nan"),
                             None, "keine Zustaende"))
                continue
            rate = float(y.mean())
            brier = float(((p - y) ** 2).mean())
            bb = float(((rate - y) ** 2).mean())
            if n < MIN_OBS:
                rows.append((name, n, rate, brier, bb, None, f"n<{MIN_OBS}"))
            elif min(rate, 1.0 - rate) < DEGENERATE_RATE:
                rows.append((name, n, rate, brier, bb, None, "konstant"))
            elif bb < DEGENERATE_BRIER:
                rows.append((name, n, rate, brier, bb, None, "keine Varianz"))
            else:
                rows.append((name, n, rate, brier, bb, 1.0 - brier / bb, ""))
        return rows

    keep_sel = KEEP_COND if args.conditional else None

    best, best_state, patience = -9.9, None, 0
    for ep in range(args.epochs):
        model.train()
        perm = torch.randperm(Xtr.shape[0], device=dev)
        tot = nb = 0
        for i in range(0, Xtr.shape[0], args.batch):
            idx = perm[i:i + args.batch]
            opt.zero_grad()
            if Mtr is None:
                loss = lossfn(model(Xtr[idx]), Ytr[idx])
            else:
                m = Mtr[idx]
                cell = lossfn_cell(model(Xtr[idx]), Ytr[idx])
                loss = (cell * m).sum() / m.sum().clamp_min(1.0)
            loss.backward()
            opt.step()
            tot += loss.item(); nb += 1
        sk = [r[5] for r in per_atom(keep_sel) if r[5] is not None]
        mean_sk = sum(sk) / max(1, len(sk))
        print(f"  Epoche {ep+1:>2}: Verlust {tot/max(1,nb):.4f} | "
              f"mittlerer Skill {mean_sk:+.3f} ueber {len(sk)} nicht-entartete Ausgaenge", flush=True)
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

    mode = "BEDINGT (nur noch unentschiedene Zellen)" if args.conditional \
        else "unbedingt (Bestandsverhalten)"
    print(f"\nAuswertung: {mode}"
          + ("  |  Trainingsverlust ohne trivial ablesbare Zellen"
             if args.mask_train_decided else ""))
    print(f"\n{'Ausgang':34} {'n':>7} {'Grundrate':>9} {'Brier':>8} {'Br(Rate)':>9} {'Skill':>8}  Bemerkung")
    pos = neg = degen = 0
    for name, n, rate, brier, bb, skill, why in per_atom(keep_sel):
        if skill is None:
            degen += 1
            print(f"{name:34} {n:>7} {rate:>9.3f} {brier:>8.4f} {bb:>9.5f} {'--':>8}  ENTARTET ({why})")
        else:
            if skill > 0.02: pos += 1
            elif skill < -0.02: neg += 1
            print(f"{name:34} {n:>7} {rate:>9.3f} {brier:>8.4f} {bb:>9.5f} {skill:>+8.3f}")

    print(f"\n{pos} Ausgaenge mit Skill > +0,02 | {neg} mit < -0,02 | {degen} entartet")

    if not args.conditional:
        print("\nLesart: ENTARTET ist ein BEFUND, kein Messfehler -- die Groesse folgt aus")
        print("der Position, eine Tabelle erledigt sie.")
        return

    # ---- unbedingt gegen bedingt, beide aus DEMSELBEN Modell ---------------
    unc, con = per_atom(None), per_atom(KEEP_COND)
    plate, nopl = per_atom(KEEP_PLATE), per_atom(KEEP_NOPLATE)
    model.eval()
    with torch.no_grad():
        pv_np = torch.sigmoid(model(Xva)).cpu().numpy()

    tab_sk = [None] * n_atoms
    print(f"\n{'Ausgang':34} {'Ablese%':>8} {'Skill unb.':>11} {'n bed.':>8} {'Part.':>6} "
          f"{'Skill bed.':>11} {'Delta':>8} {'Tabelle':>8}  95%-KI bedingt (Partie-Bootstrap)")
    n_deg = 0
    for a in range(n_atoms):
        su, sc, nc = unc[a][5], con[a][5], con[a][1]
        keep = KEEP_COND[:, a]
        # effektive Stichprobe: Labels sind je Partie konstant, n zaehlt Zustaende
        n_games = int(np.unique(val_gids[keep]).size) if keep.any() else 0
        share = float((S_va[:, a] == ST_FILLED).mean()) * 100.0
        if sc is None:
            n_deg += 1
        ci = _boot_ci(yv_np[keep, a], pv_np[keep, a], val_gids[keep]) \
            if (sc is not None and keep.any()) else None
        if R is not None:
            ktr = S_tr[:, a] != ST_FILLED
            tab_sk[a] = _table_skill(ytr_np[ktr, a], R_tr[ktr],
                                     yv_np[keep, a], R_va[keep], n_rounds)
        fu = f"{su:+.3f}" if su is not None else f"ENT({unc[a][6]})"
        fc = f"{sc:+.3f}" if sc is not None else f"ENT({con[a][6]})"
        fd = f"{sc - su:+.3f}" if (sc is not None and su is not None) else "--"
        ft = f"{tab_sk[a]:+.3f}" if tab_sk[a] is not None else "--"
        fci = f"[{ci[0]:+.3f}; {ci[1]:+.3f}]" if ci else "--"
        print(f"{names[a]:34} {share:>7.1f}% {fu:>11} {nc:>8} {n_games:>6} "
              f"{fc:>11} {fd:>8} {ft:>8}  {fci}")
    live = [r[5] for r in con if r[5] is not None]
    print(f"\n{n_deg} von {n_atoms} Ausgaengen entarten unter der Bedingung; "
          f"mittlerer bedingter Skill der uebrigen: "
          + (f"{sum(live)/len(live):+.3f}" if live else "--"))
    print("Ablese% = Anteil der Bewertungszustaende, in denen die Zelle schon")
    print("entschieden und das Label damit trivial aus der Eingabe ablesbar ist.")
    tl = [v for v in tab_sk if v is not None]
    if tl:
        print(f"Tabelle = Brier-Skill von `P(Label | Runde)`, auf den Trainingspartien")
        print(f"gefittet, bedingt ausgewertet -- die probe-freie Untergrenze. "
              f"Schnitt {sum(tl)/len(tl):+.3f}, Bester {max(tl):+.3f}.")

    # ---- die zwei UNENTSCHIEDENEN Strata getrennt --------------------------
    if groups and KEEP_PLATE.any() and KEEP_NOPLATE.any():
        print(f"\nDie beiden unentschiedenen Strata getrennt "
              f"(leere Zelle auf LIEGENDER Platte  vs.  Slot ohne Platte):")
        print(f"\n{'Ausgang':34} {'n Platte':>9} {'Rate':>6} {'Skill':>8}   "
              f"{'n ohne':>9} {'Rate':>6} {'Skill':>8}")
        for a in range(n_atoms):
            fp = f"{plate[a][5]:+.3f}" if plate[a][5] is not None else f"ENT({plate[a][6]})"
            fn = f"{nopl[a][5]:+.3f}" if nopl[a][5] is not None else f"ENT({nopl[a][6]})"
            print(f"{names[a]:34} {plate[a][1]:>9} {plate[a][2]:>6.3f} {fp:>8}   "
                  f"{nopl[a][1]:>9} {nopl[a][2]:>6.3f} {fn:>8}")

    # ---- Gruppierung nach Kriterien-Geometrie ------------------------------
    if groups:
        print(f"\nNach Kriterien-Geometrie (bedingt; Zellen -> Kriterium):")
        print(f"\n{'Gruppe':30} {'Zellen':>7} {'entart.':>8} {'Grundrate':>10} "
              f"{'Skill bed.':>11} {'min':>8} {'max':>8} {'Tabelle':>8}   "
              f"{'Platte':>8} {'ohne Pl.':>9}")
        for gname, idxs in groups:
            vals = [con[i][5] for i in idxs if con[i][5] is not None]
            vp = [plate[i][5] for i in idxs if plate[i][5] is not None]
            vn = [nopl[i][5] for i in idxs if nopl[i][5] is not None]
            vt = [tab_sk[i] for i in idxs if tab_sk[i] is not None]
            rates = [con[i][2] for i in idxs]
            nd = sum(1 for i in idxs if con[i][5] is None)
            f = (lambda v: f"{sum(v)/len(v):+.3f}" if v else "--")
            print(f"{gname:30} {len(idxs):>7} {nd:>8} "
                  f"{sum(rates)/len(rates):>10.3f} {f(vals):>11} "
                  f"{(f'{min(vals):+.3f}' if vals else '--'):>8} "
                  f"{(f'{max(vals):+.3f}' if vals else '--'):>8} {f(vt):>8}   "
                  f"{f(vp):>8} {f(vn):>9}")

    print("\nLesart: ENTARTET ist ein BEFUND, kein Messfehler -- die Groesse folgt aus")
    print("der Position, eine Tabelle erledigt sie. Ein Kopf lohnt nur fuer Ausgaenge")
    print("mit positivem BEDINGTEM Skill; alles andere kostet Kapazitaet und")
    print("Gradientenanteil.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pattern", default="selfplay_v20wdl_*.pkl")
    ap.add_argument("--files", type=int, default=400)
    ap.add_argument("--max-states", type=int, default=300000)
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--batch", type=int, default=256)
    ap.add_argument("--hidden", type=int, default=384)
    ap.add_argument("--target", choices=("conjunctions", "ownership", "both"),
                    default="conjunctions",
                    help="conjunctions = die 34 Zusatzziele aus "
                         "_conjunctions_from_dome (Default, Bestandsverhalten); "
                         "ownership = die 36 Zellen aus _ownership_from_dome; "
                         "both = beide aus DEMSELBEN Korpuslauf")
    ap.add_argument("--conditional-layout", "--conditional", dest="conditional",
                    action="store_true",
                    help="nur noch UNENTSCHIEDENE Zellen evaluate: Layout-Atome "
                         "nur auf Slots ohne Platte, Ownership-Zellen nur wenn "
                         "noch leer (Default: Bestandsverhalten, unbedingt)")
    ap.add_argument("--mask-train-decided", "--mask-train-layout",
                    dest="mask_train_decided", action="store_true",
                    help="trivial ablesbare Zellen zusaetzlich aus dem "
                         "Trainingsverlust nehmen (setzt --conditional)")
    args = ap.parse_args()
    if args.mask_train_decided:
        args.conditional = True

    import numpy as np
    import torch

    print("Lade Korpus und baue Labels ueber _conjunctions_from_dome "
          "und _ownership_from_dome ...", flush=True)
    flat, planes, tgt, gids, occ, tgt_own, stat_own, rounds = load(
        args.pattern, args.files, args.max_states)
    if not tgt:
        raise SystemExit("keine verwertbaren Zustaende")

    X = torch.cat([
        torch.stack([f if torch.is_tensor(f) else torch.tensor(f) for f in flat]).float(),
        torch.stack([p if torch.is_tensor(p) else torch.tensor(p) for p in planes]).float().flatten(1),
    ], dim=1)

    uniq = sorted(set(gids))
    n_val = max(1, int(len(uniq) * 0.2))
    val_games = set(uniq[-n_val:])
    is_val = torch.tensor([g in val_games for g in gids])
    print(f"{X.shape[0]} Zustaende aus {len(uniq)} Partien, "
          f"Schnitt {len(uniq)-n_val} / {n_val} Partien")

    if args.target in ("conjunctions", "both"):
        Y = torch.tensor(tgt).float()
        n_atoms = Y.shape[1]
        if n_atoms != len(ATOM_NAMES):
            print(f"WARNUNG: {n_atoms} Atome, aber {len(ATOM_NAMES)} Namen -- "
                  "Namensliste veraltet?")
        # Nur die Layout-Ausgaenge sind bedingbar: dort ist "Platte liegt" der
        # Ablese-Fall. Die Konjunktionen selbst haben keine Zellenzerlegung und
        # bleiben in JEDEM Modus vollstaendig in der Auswertung.
        base = n_atoms - N_LAYOUT
        S = np.full((X.shape[0], n_atoms), ST_EMPTY_ON_PLATE, dtype=np.int8)
        occ_np = np.asarray(occ, dtype=np.int8)
        S[:, base:base + N_LAYOUT] = np.where(occ_np == 1, ST_FILLED, ST_NO_PLATE)
        run_experiment("34 Konjunktionen + Layout (_conjunctions_from_dome)",
                       X, Y, S, ATOM_NAMES, is_val, gids, args, rounds=rounds)

    if args.target in ("ownership", "both"):
        Yo = torch.tensor(tgt_own).float()
        So = np.asarray(stat_own, dtype=np.int8)
        if Yo.shape[1] != len(CELL_NAMES):
            print(f"WARNUNG: {Yo.shape[1]} Zellen, aber {len(CELL_NAMES)} Namen")
        run_experiment("36 Ownership-Zellen (_ownership_from_dome)",
                       X, Yo, So, CELL_NAMES, is_val, gids, args,
                       groups=_cell_groups(), rounds=rounds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
