# -*- coding: utf-8 -*-
"""PREREG_search_depth_column_optimum.md Stufe 4 Teil B -- ist das Verworfene
spaltenrelevant?

DEFINITION (par.6a, VOR der Messung festgelegt): ein Drafting-Zug heisst
SPALTENRELEVANT, wenn er eine Musterreihe r bedient, deren Kuppelzeile r
mindestens eine offene Zelle in einer Spalte mit Fuellstand >= 4 hat.

OPERATIONALISIERUNG (hier festgehalten, weil par.6a sie offen liess):
* Die Reihe steht im Klartext der Kandidaten-`description` ("... -> Reihe k
  [f/k]", execution.rs `dest_label`: k = row_index + 1; "Strafleiste" hat
  keine Reihe und ist nie spaltenrelevant).
* Kuppelzeile und Musterreihe teilen den Index (lib.rs
  `plate_completability_json`: Zelle (r, c) gehoert zu `pattern_lines[r]`),
  also Kuppelzeile r = k - 1 (0-basiert).
* `col_fill` und `col_open_cells` kommen aus demselben Praedikat, fuer den
  Spieler am Zug. "Offene Zelle" = Eintrag in `col_open_cells[c]` mit
  `kind != "empty_slot"` (eine Zelle ohne Kuppelplatte kann eine
  Reihenvollendung nicht aufnehmen). Die Variante MIT leeren Slots wird als
  Sensitivitaet mitgezaehlt.

GEPAART wie Teil A: derselbe Zustand bei 100 und 400 Sims, gleicher Seed,
Dedupe ueber den Zustands-Hash. Messgroesse nach par.5 Teil B: unter den
Verwerfungen je Sims-Stufe, wie oft ist der Prior-Top-1 spaltenrelevant und
die Suchwahl nicht -- und umgekehrt.
"""
import argparse
import glob
import hashlib
import json
import math
import os
import re
import sys
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "tools"))
from corpus_io import load_records  # noqa: E402

ROW_RE = re.compile(r"Reihe\s+(\d)")


def prior_top1(trace):
    cands = trace.get("top_m_selection") or []
    return max(cands, key=lambda c: c.get("prior", 0.0)).get("description") if cands else None


def search_choice(trace):
    finals = trace.get("final_selection") or []
    return max(finals, key=lambda f: f.get("visits", 0)).get("description") if finals else None


def row_of(description):
    m = ROW_RE.search(description or "")
    return int(m.group(1)) if m else None


def relevant_rows(pred, min_fill, include_empty_slots):
    rows = set()
    for c, cells in enumerate(pred.get("col_open_cells") or []):
        if (pred.get("col_fill") or [0] * 6)[c] < min_fill:
            continue
        for cell in cells:
            if cell.get("kind") == "empty_slot" and not include_empty_slots:
                continue
            rows.add(int(cell["r"]) + 1)
    return rows


def mcnemar_exact(a, b):
    n = a + b
    if n == 0:
        return None
    k = min(a, b)
    return min(1.0, 2.0 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--pattern", default="selfplay_s4states-v23b01_*.pkl")
    ap.add_argument("--model", default="models/alphazero_v23-b01_brierbest.onnx")
    ap.add_argument("--n-states", type=int, default=200)
    ap.add_argument("--per-file", dest="per_file_max", type=int, default=25)
    ap.add_argument("--sims", nargs="+", type=int, default=[100, 400])
    ap.add_argument("--rounds", nargs="+", type=int, default=[2, 3, 4])
    ap.add_argument("--seed", type=int, default=20260931)
    ap.add_argument("--min-fill", type=int, default=4)
    ap.add_argument("--out", default="evaluations/artifacts/search_depth_column_label.json")
    a = ap.parse_args()

    import mosaic_rust as mr

    files = sorted(glob.glob(os.path.join(_ROOT, "data", a.pattern)))
    if not files:
        raise SystemExit("Kein Korpus fuer Muster data/" + a.pattern)

    t0 = time.monotonic()
    seen = set()
    n_dup = n_states = n_no_trace = 0
    n_states_with_relevant_row = 0
    per_sims = {s: {"n": 0, "verworfen": 0, "top1_rel_choice_nicht": 0, "top1_nicht_choice_rel": 0,
                    "beide_rel": 0, "keine_rel": 0, "top1_rel": 0, "choice_rel": 0,
                    "choice_strafleiste": 0} for s in a.sims}
    per_sims_sens = {s: {"verworfen": 0, "top1_rel_choice_nicht": 0, "top1_nicht_choice_rel": 0} for s in a.sims}
    paired = []   # je Zustand: {sims: (verworfen, top1_rel, choice_rel)}
    raw = []      # 2026-09-02: Rohdaten je Zustand fuer nachtraegliche Schwellen-Sensitivitaet
                  # (min_fill 1..5, mit/ohne leere Slots), ohne die Traces neu zu rechnen
    per_file_share = {s: [] for s in a.sims}   # Anteil "spaltenrelevanter Top-1 verworfen" je Datei (Block)

    for f in files:
        if n_states >= a.n_states:
            break
        in_file = 0
        file_cnt = {s: [0, 0] for s in a.sims}
        for rec in load_records(f):
            if n_states >= a.n_states or in_file >= a.per_file_max:
                break
            st = rec.get("state") or {}
            if st.get("round") not in a.rounds or st.get("phase") != "drafting":
                continue
            sj = json.dumps(st)
            h = hashlib.md5(json.dumps(st, sort_keys=True).encode("utf-8")).hexdigest()
            if h in seen:
                n_dup += 1
                continue
            seen.add(h)
            pi = st.get("current_player", 0)
            pred = json.loads(mr.plate_completability_json(sj, pi))
            rel = relevant_rows(pred, a.min_fill, False)
            rel_sens = relevant_rows(pred, a.min_fill, True)
            per_state = {}
            for sims in a.sims:
                out = json.loads(mr.net_search_state_json_trace(sj, a.model, sims, 1.5, a.seed))
                tr = out.get("gumbel_trace") or {}
                t1, ch = prior_top1(tr), search_choice(tr)
                if t1 is None or ch is None:
                    per_state = {}
                    break
                per_state[sims] = (t1, ch)
            if not per_state:
                n_no_trace += 1
                continue
            n_states += 1
            in_file += 1
            if rel:
                n_states_with_relevant_row += 1
            entry = {}
            raw.append({"file": os.path.basename(f), "round": st.get("round"),
                        "col_fill": pred.get("col_fill"),
                        "open_rows_by_col": [sorted({int(c["r"]) + 1 for c in cells if c.get("kind") != "empty_slot"})
                                             for cells in (pred.get("col_open_cells") or [])],
                        "open_rows_by_col_incl_empty": [sorted({int(c["r"]) + 1 for c in cells})
                                                        for cells in (pred.get("col_open_cells") or [])],
                        "top1_row": {str(sm): row_of(t1) for sm, (t1, ch) in per_state.items()},
                        "choice_row": {str(sm): row_of(ch) for sm, (t1, ch) in per_state.items()},
                        "top1_desc": {str(sm): t1 for sm, (t1, ch) in per_state.items()},
                        "choice_desc": {str(sm): ch for sm, (t1, ch) in per_state.items()},
                        "verworfen": {str(sm): int(t1 != ch) for sm, (t1, ch) in per_state.items()}})
            for sims, (t1, ch) in per_state.items():
                d = per_sims[sims]
                d["n"] += 1
                r1, rc = row_of(t1), row_of(ch)
                t1_rel, ch_rel = (r1 in rel), (rc in rel)
                t1_rel_s, ch_rel_s = (r1 in rel_sens), (rc in rel_sens)
                d["top1_rel"] += t1_rel
                d["choice_rel"] += ch_rel
                if rc is None:
                    d["choice_strafleiste"] += 1
                verworfen = t1 != ch
                file_cnt[sims][1] += 1
                if verworfen:
                    d["verworfen"] += 1
                    per_sims_sens[sims]["verworfen"] += 1
                    if t1_rel and not ch_rel:
                        d["top1_rel_choice_nicht"] += 1
                        file_cnt[sims][0] += 1
                    elif ch_rel and not t1_rel:
                        d["top1_nicht_choice_rel"] += 1
                    elif t1_rel and ch_rel:
                        d["beide_rel"] += 1
                    else:
                        d["keine_rel"] += 1
                    if t1_rel_s and not ch_rel_s:
                        per_sims_sens[sims]["top1_rel_choice_nicht"] += 1
                    elif ch_rel_s and not t1_rel_s:
                        per_sims_sens[sims]["top1_nicht_choice_rel"] += 1
                entry[sims] = (int(verworfen), int(t1_rel), int(ch_rel))
            paired.append(entry)
            if n_states % 20 == 0:
                print("  " + str(n_states) + " Zustaende, " + str(round(time.monotonic() - t0)) + " s", flush=True)
        for sims in a.sims:
            hits, tot = file_cnt[sims]
            if tot:
                per_file_share[sims].append(hits / tot)

    result = {"prereg": "PREREG_search_depth_column_optimum.md Stufe 4 Teil B (par.5, Definition par.6a)",
              "pattern": a.pattern, "model": a.model, "seed": a.seed, "min_fill": a.min_fill,
              "n_states": n_states, "n_ohne_trace": n_no_trace, "n_duplikate_uebersprungen": n_dup,
              "n_states_mit_relevanter_reihe": n_states_with_relevant_row,
              "je_stufe": {}, "sensitivitaet_mit_leeren_slots": {str(s): v for s, v in per_sims_sens.items()}}
    for sims in a.sims:
        d = dict(per_sims[sims])
        v = d["verworfen"]
        d["anteil_top1_rel_verworfen_an_verwerfungen"] = d["top1_rel_choice_nicht"] / v if v else None
        d["anteil_top1_rel_verworfen_an_zustaenden"] = d["top1_rel_choice_nicht"] / d["n"] if d["n"] else None
        shares = per_file_share[sims]
        if len(shares) > 1:
            m = sum(shares) / len(shares)
            sd = math.sqrt(sum((x - m) ** 2 for x in shares) / (len(shares) - 1))
            d["block_se_anteil_an_zustaenden"] = sd / math.sqrt(len(shares))
            d["n_bloecke"] = len(shares)
        result["je_stufe"][str(sims)] = d
    if len(a.sims) == 2:
        lo, hi = a.sims
        # Ereignis E = "spaltenrelevanter Prior-Top-1 verworfen zugunsten eines nicht-relevanten Zugs"
        e = lambda x: 1 if (x[0] and x[1] and not x[2]) else 0
        only_hi = sum(1 for p in paired if e(p[hi]) and not e(p[lo]))
        only_lo = sum(1 for p in paired if e(p[lo]) and not e(p[hi]))
        both = sum(1 for p in paired if e(p[lo]) and e(p[hi]))
        result["gepaart_ereignis_E"] = {"sims_niedrig": lo, "sims_hoch": hi, "beide": both,
                                        "nur_hoch": only_hi, "nur_niedrig": only_lo,
                                        "mcnemar_exakt_p": mcnemar_exact(only_hi, only_lo)}
    result["rohdaten_je_zustand"] = raw
    result["laufzeit"] = {"wanduhr_s": round(time.monotonic() - t0, 1), "cpu_s": None,
                          "threads": 1, "s_je_partie": None}
    path = os.path.join(_ROOT, a.out)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, ensure_ascii=False)
    for sims in a.sims:
        d = result["je_stufe"][str(sims)]
        print("sims=" + str(sims) + ": n " + str(d["n"]) + ", verworfen " + str(d["verworfen"])
              + ", Top1 relevant & Wahl nicht " + str(d["top1_rel_choice_nicht"])
              + ", Top1 nicht & Wahl relevant " + str(d["top1_nicht_choice_rel"])
              + ", beide " + str(d["beide_rel"]) + ", keine " + str(d["keine_rel"]), flush=True)
    if "gepaart_ereignis_E" in result:
        print("gepaart E:", result["gepaart_ereignis_E"], flush=True)
    print("Zustaende " + str(n_states) + " (Duplikate " + str(n_dup) + ", mit relevanter Reihe "
          + str(n_states_with_relevant_row) + "), Artefakt: " + path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
