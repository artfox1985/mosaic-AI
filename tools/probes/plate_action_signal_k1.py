# -*- coding: utf-8 -*-
"""Prototyp: gibt es an der TILING-Entscheidung ein exaktes k1-Aktionssignal?

PREREG_plate_policy_supervision.md par.4/par.5. Der Prototyp beantwortet drei
Fragen an einer Stelle, an der die Wahrheit EXAKT bekannt ist.

WARUM RUNDE 5 UND TILING: der Plattenbau ist eine Tiling-Handlung
(`tiling_solver.rs:990`). In Runde 5 ist das Brett nach dem Abschluss ENDGUELTIG,
also ist die k1-Wertung jedes Kandidaten exakt berechenbar -- kein Orakel, kein
Minimax, keine Schranke. Das ist der einzige Ort im Spiel mit dieser Eigenschaft
(`round5.rs` ist budgetiert, `mcts::evaluate` ist eine Heuristik mit
`scoring_progress` darin, siehe par.2 der Prereg).

DIE DREI GROESSEN je Stellung, ueber die Kandidaten desselben Knotens:

  Label   exakte k1-Punkte des Endbretts  (end_scoring_from_state_json, id==1)
  Kopf    E(k1) des Ownership-Kopfes auf dem Ergebniszustand
  Punkte  `points` des Kandidaten -- WAS HEUTE ENTSCHEIDET (tiling_solver.rs:1079)

Gemessen wird Kendall-Tau(Label, Kopf) und Kendall-Tau(Label, Punkte).

Die dritte Zahl ist die eigentliche Ausbeute: korreliert die heutige
Entscheidungsregel NICHT mit dem k1-Label, dann bleibt die Platte an einer
Entscheidung liegen, an der die Wahrheit bekannt ist.

    python -X utf8 tools/probes/plate_action_signal_k1.py --n-states 120
"""
from __future__ import annotations

import argparse
import glob
import itertools
import json
import math
import pickle
import statistics
import sys
from pathlib import Path

BASIS = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASIS))
sys.path.insert(0, str(BASIS / "engine" / "py"))

K1 = 1  # Kriterien-ID der vertikalen Reihen (scoring.rs:43)


def idx(r: int, c: int) -> int:
    """Feldindex im Ownership-Vektor, aus scoring.rs:422/432 uebernommen."""
    return (r // 2) * 12 + (c // 2) * 4 + (r % 2) * 2 + (c % 2)


def e_k1(p) -> float:
    """E(k1) = Summe ueber die 6 Spalten des Produkts ihrer 6 Feldwahrschein-
    lichkeiten, mal 7 -- Zweig 1 aus `expected_plate_points`."""
    return sum(math.prod([p[idx(r, c)] for r in range(6)]) for c in range(6)) * 7.0


def kendall(a: list[float], b: list[float]):
    kon = dis = 0
    for i, j in itertools.combinations(range(len(a)), 2):
        s = (a[i] - a[j]) * (b[i] - b[j])
        if s > 0:
            kon += 1
        elif s < 0:
            dis += 1
    return (kon - dis) / (kon + dis) if kon + dis else None


def t_gegen_null(xs: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    sd = statistics.pstdev(xs) or 1e-12
    return statistics.mean(xs) / (sd / len(xs) ** 0.5)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default="models/alphazero_v21-b18_best.pth")
    ap.add_argument("--states", default="data/holdout/*.pkl")
    ap.add_argument("--n-states", type=int, default=120)
    ap.add_argument("--runde", type=int, default=5)
    ap.add_argument("--min-fill", type=int, default=5, dest="min_fill",
                    help="mindestens so viele der 6 Spaltenfelder gefuellt")
    ap.add_argument("--k", type=int, default=8, help="max. Tiling-Kandidaten je Stellung")
    a = ap.parse_args()

    import torch  # noqa: PLC0415
    import mosaic_rust as mr  # noqa: PLC0415
    from neural_net import build_model_from_checkpoint, state_to_planes, state_to_tensor  # noqa: PLC0415

    ck = torch.load(str(BASIS / a.model), map_location="cpu", weights_only=False)
    modell, _enc = build_model_from_checkpoint(ck)
    modell.eval()

    # WICHTIG (Fehler beim ersten Lauf, 2026-08-18): "je Partie die erste
    # Tiling-Stellung" liefert systematisch die FRUEHESTE -- dort steht nie eine
    # Spalte kurz vor dem Abschluss, und das Label ist in 100 % der Faelle 0.
    # Gesucht sind die entscheidungsrelevanten Stellungen: mindestens eine Spalte
    # mit >= `min_fill` von 6 gefuellten Feldern. Der Filter ist billig (liest
    # nur das Kuppelraster) und laeuft VOR der teuren Kandidaten-Aufzaehlung.
    from neural_net import _dome_grids_from_dome  # noqa: PLC0415

    def best_column_fill(st) -> int:
        pi = st.get("current_player", 0)
        dome = ((st.get("players") or [{}])[pi]).get("dome_grid")
        if not dome:
            return 0
        gefuellt, _ = _dome_grids_from_dome(dome)
        return max(sum(gefuellt[r][c] for r in range(6)) for c in range(6))

    proben, gesehen = [], {}
    for f in sorted(glob.glob(str(BASIS / a.states))):
        try:
            data = pickle.load(open(f, "rb"))
        except Exception:  # noqa: BLE001
            continue
        for s in data:
            st = s.get("state") or {}
            if st.get("phase") != "tiling" or int(st.get("round") or 0) != a.runde:
                continue
            if K1 not in (st.get("scoring_tile_ids") or []):
                continue
            if best_column_fill(st) < a.min_fill:
                continue
            g = (f, s.get("game_id"))
            if gesehen.get(g):
                continue
            gesehen[g] = True
            proben.append(st)
            if len(proben) >= a.n_states:
                break
        if len(proben) >= a.n_states:
            break
    print(f"  {len(proben)} Tiling-Stellungen (Runde {a.runde}, k1 aktiv, "
          f"beste Spalte >= {a.min_fill}/6 gefuellt) aus ebenso vielen Partien")
    if not proben:
        raise SystemExit("keine Zustaende")

    tau_kopf, tau_punkte, spannen, n_kand, ohne_spreizung = [], [], [], [], 0
    for st in proben:
        pi = st.get("current_player", 0)
        ids = st.get("scoring_tile_ids") or []
        try:
            cands = json.loads(mr.tiling_candidates_json(json.dumps(st), pi, a.k, 0))
        except Exception as e:  # noqa: BLE001
            print(f"  [skip] {e}")
            continue
        if len(cands) < 3:
            continue

        label, punkte, kopf = [], [], []
        for c in cands:
            roh = mr.end_scoring_from_state_json(json.dumps(c["state"]), ids)
            d = json.loads(roh) if isinstance(roh, str) else roh
            det = (d.get(f"player_{pi}") or {}).get("details") or []
            k1 = next((x["score"] for x in det if x.get("id") == K1), 0)
            label.append(float(k1))
            punkte.append(float(c["points"]))
            with torch.no_grad():
                flat = state_to_tensor(c["state"]).float().unsqueeze(0)
                planes = state_to_planes(c["state"]).float().unsqueeze(0)
                own = torch.sigmoid(modell(planes, flat)[4])[0].cpu().numpy()
            kopf.append(e_k1(own[0:36]))

        spanne = max(label) - min(label)
        spannen.append(spanne)
        n_kand.append(len(cands))
        if spanne == 0.0:
            ohne_spreizung += 1
            continue
        tk, tp = kendall(label, kopf), kendall(label, punkte)
        if tk is not None:
            tau_kopf.append(tk)
        if tp is not None:
            tau_punkte.append(tp)

    n = len(spannen)
    print(f"\n  {n} Stellungen mit >= 3 Kandidaten, im Mittel {statistics.mean(n_kand):.1f} Kandidaten")
    print(f"  Label-Spreizung (max-min k1-Punkte je Stellung): Mittel {statistics.mean(spannen):.2f}")
    print(f"  Stellungen OHNE Spreizung (alle Kandidaten gleich): {ohne_spreizung}/{n}"
          f" = {100*ohne_spreizung/max(n,1):.0f} %")
    if not tau_kopf:
        print("\n  VORABREGEL (A): keine Stellung mit Label-Spreizung -- auf dieser Ebene")
        print("  gibt es nichts zu lernen. Prototyp endet ohne Aussage ueber die Methode.")
        return
    print(f"\n  n mit Spreizung = {len(tau_kopf)}")
    print(f"  Kendall-Tau(Label, KOPF-Ordnung)  : {statistics.mean(tau_kopf):+.3f}   t={t_gegen_null(tau_kopf):+.2f}")
    print(f"  Kendall-Tau(Label, PUNKTE-Ordnung): {statistics.mean(tau_punkte):+.3f}   t={t_gegen_null(tau_punkte):+.2f}")
    print("  (PUNKTE ist die heutige Entscheidungsregel des Tiling-Solvers)")

    tk = statistics.mean(tau_kopf)
    tkt = t_gegen_null(tau_kopf)
    if tkt > 1.68 and tk > 0:
        urteil = "(B) KOPF WEISS ES -- Information vorhanden, erreicht die Zugwahl nicht"
    else:
        urteil = "(B) KOPF WEISS ES NICHT -- stabile Ordnung ist stabil FALSCH"
    print(f"\n  VORABREGEL par.5: {urteil}")

    (BASIS / "evaluations" / "probe_plate_action_signal_k1.json").write_text(json.dumps({
        "model": a.model, "runde": a.runde, "n_stellungen": n,
        "n_mit_spreizung": len(tau_kopf),
        "anteil_ohne_spreizung": ohne_spreizung / max(n, 1),
        "label_spreizung_mittel": statistics.mean(spannen),
        "tau_kopf": tk, "t_kopf": tkt,
        "tau_punkte": statistics.mean(tau_punkte), "t_punkte": t_gegen_null(tau_punkte),
        "urteil": urteil,
    }, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
