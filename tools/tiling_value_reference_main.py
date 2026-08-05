# -*- coding: utf-8 -*-
"""tools/tiling_value_reference_main.py -- Task #20, Hauptlauf der Referenz-
Validierung (Doku-Gate vor der Aktivierung, KEIN Uebernahme-Gate mehr --
Nutzer-Entscheidung 2026-07-29: die Regel wird aktiviert).

## Unterschiede zum Piloten (tools/tiling_value_reference_pilot.py)

1. STELLUNGEN AUS data/*.pkl statt aus dem frozen set -- der Pilot hat die 31
   punktgleichen Paare des frozen sets bereits ERSCHOEPFT.
2. UNABHAENGIGE REFERENZ: die Tiefensuche laeuft mit v17_best, die
   Kandidaten-Rangfolge kommt von v18_best. Der Pilot (29/31) nutzte dasselbe
   Netz fuer beides -- ein Teil der Uebereinstimmung war damit selbstbezueglich.
3. M=4 Zufallsziehungen statt 16 -- der Pilot hat gemessen, dass das gepaarte
   Restrauschen (0,0056) ein Viertel des Signals (0,0216) betraegt; bei M=4
   liegt der Standardfehler bei einem Achtel des Signals.

## Was berichtet wird

Richtungsuebereinstimmung gesamt UND je Runde (beantwortet empirisch die
Gewichtungsfrage: traegt der Value-Head in Runde 4 mehr oder weniger als in
Runde 2?), exakter Binomialtest gegen 50 %, und die Referenz-Differenzen
getrennt nach Treffer/Fehlgriff (ein Fehlgriff bei winziger Referenz-Differenz
ist harmloser als einer bei grosser).
"""
from __future__ import annotations

import argparse
import glob
import json
import pickle
import statistics as stats
import sys
from math import comb
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "engine" / "py"))

import torch  # noqa: E402

from config import INPUT_SIZE, MODELS_DIR, NUM_ACTIONS  # noqa: E402
from neural_net import (MosaicNet, points_dist_bins_from_state,  # noqa: E402
                        state_to_tensor, state_to_planes,
                        build_model_from_checkpoint)


def binom_p(k: int, n: int) -> float:
    if n == 0:
        return 1.0
    lo, hi = min(k, n - k), max(k, n - k)
    return min(1.0, 2 * min(sum(comb(n, i) for i in range(0, lo + 1)) / 2 ** n,
                            sum(comb(n, i) for i in range(hi, n + 1)) / 2 ** n))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rank-model", default="v18_best",
                    help="Netz, dessen Value-Rangfolge geprueft wird (die Auswahlregel).")
    ap.add_argument("--ref-model", default="v17_best",
                    help="UNABHAENGIGES Netz fuer die Referenz-Tiefensuche.")
    ap.add_argument("--k", type=int, default=12)
    ap.add_argument("--draws", type=int, default=4)
    ap.add_argument("--sims", type=int, default=2000)
    ap.add_argument("--max-pairs", type=int, default=250)
    ap.add_argument("--max-states-per-file", type=int, default=30)
    ap.add_argument("--only-round", type=int, default=None,
                    help="Nur Stellungen dieser Runde. NOETIG geworden, weil der erste "
                         "Hauptlauf Runde 4 komplett verfehlte: Dateien werden in "
                         "Spielreihenfolge gelesen, das Pro-Datei-Limit war erschoepft, "
                         "bevor Runde-4-Zustaende drankamen.")
    ap.add_argument("--out", default="evaluations/tiling_value_reference_main.json")
    args = ap.parse_args()

    import mosaic_rust as mr

    ref_path = str(MODELS_DIR / f"alphazero_{args.ref_model}.onnx")
    # Aufgeruestet 2026-08-05: Checkpoint-basierter Lader statt hart
    # verdrahtetem Flach-MosaicNet -- das Original stammte aus der
    # Flach-Aera und haette 2D-/WDL-Checkpoints mit `strict=False` STILL
    # falsch geladen (2D-Trunk-Gewichte einfach uebersprungen).
    ck = torch.load(str(MODELS_DIR / f"alphazero_{args.rank_model}.pth"),
                    map_location="cpu", weights_only=False)
    net, rank_encoder = build_model_from_checkpoint(ck)[:2]
    net.eval()

    def rank_win_probs(states):
        """[0,1]-Value je Zustand -- Encoder-korrekt (2D: Planes+Flat).
        Beim WDL-Kopf liefert `forward()` an der Value-Position bereits
        `2*P(Sieg)-1`, die (v+1)/2-Formel unten gilt also fuer BEIDE
        Kopfarten unveraendert."""
        flat = torch.stack([state_to_tensor(s) for s in states])
        if rank_encoder == "2d":
            planes = torch.stack([state_to_planes(s) for s in states])
            out = net(planes, flat)
        else:
            out = net(flat)
        return ((out[1].squeeze(-1).numpy()) + 1) / 2

    files = sorted(glob.glob(str(ROOT / "data" / "*.pkl")))
    # Deterministisch ueber den Korpus streuen (jede ~10. Datei), damit
    # verschiedene Spielverlaeufe statt 30 Zustaende derselben Partie kommen.
    files = files[:: max(1, len(files) // 60)]
    print(f"Rangfolge: {args.rank_model} | Referenz: {args.ref_model}@{args.sims} Sims | "
          f"M={args.draws} | Ziel {args.max_pairs} Paare | {len(files)} Dateien\n")

    agree_tot, n_tot = 0, 0
    n_states = n_exc = 0  # Stufenzaehler -- ein stilles Null-Ergebnis muss diagnostizierbar sein
    per_round: dict[int, list[int]] = {2: [], 3: [], 4: []}
    refdiff_agree: list[float] = []
    refdiff_disagree: list[float] = []
    tie_tot = 0                      # Instrument-Fix 2026-08-05, s.u.
    per_round_ties: dict[int, int] = {}
    pair_log: list[dict] = []
    done = False

    for fi, f in enumerate(files):
        if done:
            break
        try:
            game_data = pickle.load(open(f, "rb"))
        except Exception:
            continue
        n_file = 0
        for step in game_data:
            if done or n_file >= args.max_states_per_file:
                break
            st = step.get("state") or {}
            rnd = int(st.get("round", 0))
            if st.get("phase") != "tiling" or not (2 <= rnd <= 4):
                continue
            if args.only_round is not None and rnd != args.only_round:
                continue
            n_file += 1
            n_states += 1
            pi = st.get("current_player", 0)
            try:
                cands = json.loads(mr.tiling_candidates_json(json.dumps(st), pi, args.k, 0))
            except Exception:
                n_exc += 1
                continue
            if len(cands) < 2:
                continue
            top = max(c["points"] for c in cands)
            tied = [c for c in cands if c["points"] == top]
            if len(tied) < 2:
                continue

            with torch.no_grad():
                wp = rank_win_probs([c["state"] for c in tied])

            ref = [[] for _ in tied]
            for d in range(args.draws):
                seed = 1000 + d
                for ci, c in enumerate(tied):
                    try:
                        nxt = mr.advance_after_tiling_json(json.dumps(c["state"]), seed)
                        res = json.loads(mr.net_search_state_json(nxt, ref_path, args.sims, 1.5, seed))
                        v = res.get("root_value")
                        if v is None:
                            # Runde-4-Kandidaten landen nach dem Uebergang in
                            # Runde-5-DRAFTING -- dort antwortet der Alpha-Beta-
                            # Solver (round5.rs), dessen Analyse KEIN root_value
                            # traegt (derselbe Grund, aus dem Task #89 Runde 5
                            # vom Orakel ausschloss; entdeckt, als der erste
                            # R4-Lauf 1800 Zustaende scannte und 0 Paare fand).
                            # Ersatz: das mcts_q des GEWAEHLTEN Zugs = der
                            # Alpha-Beta-Wurzelwert, seit dem Lehrer-Fix eine
                            # normalisierte [0,1]-Gewinnwahrscheinlichkeit --
                            # fuer Runde 4 sogar eine EXAKTE Referenz statt
                            # einer Such-Schaetzung.
                            mv = res.get("moves") or []
                            v = next((m.get("mcts_q") for m in mv if m.get("chosen")), None)
                        if v is None:
                            ref[ci].append(float("nan"))
                        else:
                            mover = res.get("current_player")
                            ref[ci].append(float(v) if mover == pi else 1.0 - float(v))
                    except Exception:
                        ref[ci].append(float("nan"))

            for a in range(len(tied)):
                for b in range(a + 1, len(tied)):
                    da = [ref[a][d] - ref[b][d] for d in range(args.draws)
                          if ref[a][d] == ref[a][d] and ref[b][d] == ref[b][d]]
                    if len(da) < 2:
                        continue
                    m = stats.mean(da)
                    dwp = float(wp[a] - wp[b])
                    # Instrument-Fix 2026-08-05: REFERENZ-GLEICHSTAENDE (m==0,
                    # in R4 haeufig -- die Referenz ist dort der EXAKTE
                    # Alpha-Beta-Wert und oft identisch) zaehlten vorher als
                    # Fehlgriff (`(wp_a-wp_b)*0 > 0` ist False) und drueckten
                    # die Trefferquote kuenstlich unter 50% -- das betraf auch
                    # die Juli-Zahlen (R4 "48,3%"). Jetzt eigene Kategorie,
                    # nicht in agree/n enthalten; Pro-Paar-Rohdaten werden
                    # mitgeschrieben, damit Nachanalysen ohne Re-Lauf gehen.
                    if m == 0.0 or dwp == 0.0:
                        tie_tot += 1
                        per_round_ties[rnd] = per_round_ties.get(rnd, 0) + 1
                        pair_log.append({"round": rnd, "m": m, "dwp": dwp, "tie": True})
                        continue
                    ok = dwp * m > 0
                    agree_tot += int(ok)
                    n_tot += 1
                    per_round[rnd].append(int(ok))
                    (refdiff_agree if ok else refdiff_disagree).append(abs(m))
                    pair_log.append({"round": rnd, "m": m, "dwp": dwp, "tie": False, "ok": ok})
                    if n_tot >= args.max_pairs:
                        done = True
        if (fi + 1) % 10 == 0:
            print(f"  Datei {fi+1}/{len(files)} | Zustaende {n_states} | Fehler {n_exc} | Paare {n_tot}", flush=True)

    if n_tot == 0:
        raise SystemExit(f"Keine punktgleichen Kandidatenpaare gefunden -- Diagnose: "
                         f"{n_states} Zustaende gescannt, {n_exc} Kandidaten-Exceptions.")

    print("\n" + "=" * 70)
    print("  HAUPTLAUF: rangiert v18s Value-Head punktgleiche Abschluesse richtig?")
    print("  (Referenz: UNABHAENGIGES Netz -- der Selbstbezug des Piloten ist raus)")
    print("=" * 70)
    print(f"  GESAMT: {agree_tot}/{n_tot} richtig ({agree_tot/n_tot:.1%})   "
          f"Binomialtest gegen 50%: p = {binom_p(agree_tot, n_tot):.2e}")
    for r in (2, 3, 4):
        v = per_round[r]
        if v:
            print(f"  Runde {r}: {sum(v)}/{len(v)} ({sum(v)/len(v):.1%})   "
                  f"p = {binom_p(sum(v), len(v)):.4f}")
    print(f"  Referenz-Gleichstaende (eigene Kategorie, NICHT in agree/n): {tie_tot} "
          f"{ {r: c for r, c in sorted(per_round_ties.items())} }")
    if refdiff_agree and refdiff_disagree:
        print(f"\n  |Referenz-Differenz| bei Treffern:    Median {stats.median(refdiff_agree):.4f}")
        print(f"  |Referenz-Differenz| bei Fehlgriffen: Median {stats.median(refdiff_disagree):.4f}")
        print("  (Fehlgriffe bei kleiner Differenz sind praktisch folgenlos.)")
    print("=" * 70)

    (ROOT / args.out).write_text(json.dumps({
        "rank_model": args.rank_model, "ref_model": args.ref_model,
        "k": args.k, "draws": args.draws, "sims": args.sims,
        "agree": agree_tot, "n_pairs": n_tot, "binom_p": binom_p(agree_tot, n_tot),
        "ties": tie_tot, "per_round_ties": {str(r): c for r, c in per_round_ties.items()},
        "per_round": {str(r): [sum(v), len(v)] for r, v in per_round.items() if v},
        "refdiff_agree_median": stats.median(refdiff_agree) if refdiff_agree else None,
        "refdiff_disagree_median": stats.median(refdiff_disagree) if refdiff_disagree else None,
        "pairs": pair_log,
    }, indent=2), encoding="utf-8")
    print(f"\nErgebnis: {ROOT / args.out}")


if __name__ == "__main__":
    main()
