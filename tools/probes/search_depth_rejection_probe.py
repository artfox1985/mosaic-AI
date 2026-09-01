# -*- coding: utf-8 -*-
"""PREREG_search_depth_column_optimum.md Stufe 4 Teil A -- Verwerfungsanteil.

FRAGE: wie oft weicht die Zugwahl der Suche vom Prior-Top-1 ab, und STEIGT der
Anteil mit der Suchtiefe? Anlass ist die Tiefen-Delle im Spaltenbau (b01:
0,7200 volle Spalten bei 100 Sims gegen 0,5150 bei 400), nachdem ein Eingriff
an der Wurzelbalance und drei an der Blattwert-Skala gemessen wirkungslos
blieben (Zuordnung berichtigt 2026-09-01).

DEDUPE (seit 2026-09-01): der Erstlauf las zwei identische Paritaetslaeufe und
zaehlte jeden Zustand doppelt (89 distinkte von 200). Seither wird jeder
Zustand ueber einen Hash seines JSON nur einmal gezaehlt, auch innerhalb einer
Datei; Anzahl der uebersprungenen Duplikate steht im Artefakt. Dazu der exakte
zweiseitige Binomialtest auf den diskordanten Paaren (McNemar exakt).

INSTRUMENT: `net_search_state_json_trace` liefert `top_m_selection` (je
Wurzelkandidat `prior`, `ln_prior`, `description`) und `final_selection` (die
Finalisten mit `visits`). Der Prior-Top-1 ist der Kandidat mit dem hoechsten
`prior`, die Zugwahl der Finalist mit den meisten `visits`; verglichen wird
ueber `description`, weil das die einzige stabile Kandidaten-Identitaet im
Trace ist.

GEPAART: derselbe Zustand wird mit beiden Sims-Stufen getract, gleicher Seed.
Block-SE auf Dateiebene (Lehre aus dem Reachability-Erstlauf).
"""
import argparse
import glob
import hashlib
import json
import math
import os
import sys
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT)

from corpus_io import load_records  # noqa: E402


def mean_se(values):
    if not values:
        return None, None
    mean = sum(values) / len(values)
    if len(values) < 2:
        return mean, None
    var = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return mean, math.sqrt(var) / math.sqrt(len(values))


def prior_top1(trace):
    """Kandidat mit dem hoechsten rohen Prior."""
    cands = trace.get("top_m_selection") or []
    if not cands:
        return None
    return max(cands, key=lambda c: c.get("prior", 0.0)).get("description")


def search_choice(trace):
    """Zugwahl der Suche: Finalist mit den meisten Besuchen."""
    finals = trace.get("final_selection") or []
    if not finals:
        return None
    return max(finals, key=lambda f: f.get("visits", 0)).get("description")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--pattern", default="selfplay_paritycheck-*.pkl")
    ap.add_argument("--model", default="models/alphazero_v23-b01_brierbest.onnx")
    ap.add_argument("--n-states", type=int, default=200)
    ap.add_argument("--per-file", dest="per_file_max", type=int, default=50)
    ap.add_argument("--sims", nargs="+", type=int, default=[100, 400])
    ap.add_argument("--rounds", nargs="+", type=int, default=[2, 3, 4])
    ap.add_argument("--seed", type=int, default=20260931)
    ap.add_argument("--out", default="evaluations/artifacts/search_depth_rejection.json")
    ap.add_argument("--no-dedupe", dest="dedupe", action="store_false",
                    help="Duplikat-Zustaende NICHT ueberspringen (Verhalten des Erstlaufs)")
    a = ap.parse_args()

    import mosaic_rust as mr

    files = sorted(glob.glob(os.path.join(_ROOT, "data", a.pattern)))
    if not files:
        raise SystemExit("Kein Korpus fuer Muster data/" + a.pattern + " gefunden.")

    t0 = time.monotonic()
    per_file_rej = {s: [] for s in a.sims}      # Verwerfungsanteil je Datei
    paired = []                                  # (rejected@sims0, rejected@sims1) je Zustand
    n_states_done = 0
    n_no_trace = 0
    seen_states = set()
    n_duplicates = 0

    for f in files:
        if n_states_done >= a.n_states:
            break
        file_counter = {s: [0, 0] for s in a.sims}
        in_this_file = 0
        for rec in load_records(f):
            if n_states_done >= a.n_states or in_this_file >= a.per_file_max:
                break
            state = rec.get("state") or {}
            if state.get("round") not in a.rounds or state.get("phase") != "drafting":
                continue
            state_json = json.dumps(state)
            if a.dedupe:
                h = hashlib.md5(json.dumps(state, sort_keys=True).encode("utf-8")).hexdigest()
                if h in seen_states:
                    n_duplicates += 1
                    continue
                seen_states.add(h)
            per_state = {}
            for sims in a.sims:
                out = json.loads(mr.net_search_state_json_trace(
                    state_json, a.model, sims, 1.5, a.seed))
                trace = out.get("gumbel_trace") or {}
                top1, choice = prior_top1(trace), search_choice(trace)
                if top1 is None or choice is None:
                    per_state = {}
                    break
                per_state[sims] = 1 if top1 != choice else 0
            if not per_state:
                n_no_trace += 1
                continue
            n_states_done += 1
            in_this_file += 1
            for sims in a.sims:
                file_counter[sims][0] += per_state[sims]
                file_counter[sims][1] += 1
            paired.append(tuple(per_state[s] for s in a.sims))
        for sims in a.sims:
            hits, total = file_counter[sims]
            if total:
                per_file_rej[sims].append(hits / total)

    result = {
        "prereg": "PREREG_search_depth_column_optimum.md Stufe 4 Teil A (par.5)",
        "pattern": a.pattern, "model": a.model, "seed": a.seed,
        "n_states": n_states_done, "n_ohne_trace": n_no_trace,
        "dedupe": a.dedupe, "n_duplikate_uebersprungen": n_duplicates,
        "n_dateien_gelesen": len([f for f in files]),
        "rounds": a.rounds, "sims_stufen": a.sims, "je_stufe": {},
    }
    for sims in a.sims:
        mean, se = mean_se(per_file_rej[sims])
        result["je_stufe"][str(sims)] = {
            "verwerfungsanteil": mean, "block_se": se, "n_dateien": len(per_file_rej[sims]),
        }
    if len(a.sims) == 2 and paired:
        lo, hi = a.sims
        diffs = [b - c for c, b in paired]     # hoehere Stufe minus niedrigere
        mean, se = mean_se(diffs)
        both = sum(1 for c, b in paired if c and b)
        only_hi = sum(1 for c, b in paired if b and not c)
        only_lo = sum(1 for c, b in paired if c and not b)
        n_disc = only_hi + only_lo
        k = min(only_hi, only_lo)
        p_exact = (min(1.0, 2.0 * sum(math.comb(n_disc, i) for i in range(k + 1)) / 2 ** n_disc)
                   if n_disc else None)
        result["gepaart"] = {
            "sims_niedrig": lo, "sims_hoch": hi, "n_paare": len(paired),
            "differenz_hoch_minus_niedrig": mean, "se": se,
            "beide_verworfen": both, "nur_hoch": only_hi, "nur_niedrig": only_lo,
            "mcnemar_exakt_p": p_exact, "n_diskordant": n_disc,
        }
    result["laufzeit"] = {"wanduhr_s": round(time.monotonic() - t0, 1), "cpu_s": None,
                          "threads": 1, "s_je_partie": None}
    target_path = os.path.join(_ROOT, a.out)
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, ensure_ascii=False)

    for sims in a.sims:
        e = result["je_stufe"][str(sims)]
        print("sims=" + str(sims) + ": Verwerfungsanteil " + str(round(e["verwerfungsanteil"], 4))
              + " (Block-SE " + str(e["block_se"]) + ", " + str(e["n_dateien"]) + " Dateien)", flush=True)
    if "gepaart" in result:
        g = result["gepaart"]
        print("gepaart: Differenz " + str(round(g["differenz_hoch_minus_niedrig"], 4))
              + " (SE " + str(g["se"]) + ") | beide " + str(g["beide_verworfen"])
              + ", nur@" + str(g["sims_hoch"]) + " " + str(g["nur_hoch"])
              + ", nur@" + str(g["sims_niedrig"]) + " " + str(g["nur_niedrig"]), flush=True)
    print("Zustaende " + str(n_states_done) + " (ohne Trace: " + str(n_no_trace)
          + ", Duplikate uebersprungen: " + str(n_duplicates) + "), Artefakt: " + target_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
