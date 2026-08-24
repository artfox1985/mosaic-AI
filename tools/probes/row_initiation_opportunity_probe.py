#!/usr/bin/env python
"""PREREG_long_row_payoff.md par.2a: Initiierung langer Reihen, auf
GELEGENHEIT bedingt -- aus dem Korpus, ohne Rekonstruktion.

VORGESCHICHTE (zwei Stufen, beide dokumentiert statt entsorgt):

  Stufe 1 (`row_initiation_probe.py`, Arena-Logs) fand einen scharfen
  Zickzack im Anteil "Initiierung geht in eine lange Reihe" -- Champion
  R1-R5: 21,8 / 27,7 / 2,1 / 13,7 / 20,5 %. Der Anteil ist aber
  KONFUNDIERT: initiieren kann nur, wessen lange Reihe gerade leer ist.

  Stufe 2 (`row_opportunity_probe.py`) wollte die Belegung aus dem Log
  rekonstruieren, um darauf zu normieren. Ihr eingebauter Selbsttest hat
  die Rekonstruktion in ueber der Haelfte der Partien als FALSCH
  entlarvt. Ursache am Code gefunden: `round_end.rs::process_unplaceable_
  rows` (Z.87) leert Musterreihen am Rundenende und schreibt dafuer KEINE
  Logzeile. Eine belegungs-genaue Rekonstruktion aus Arena-Logs ist damit
  prinzipiell unmoeglich, ohne `find_unplaceable_rows` samt Kuppel-Zustand
  nachzubauen -- also Spielregeln in einer Sonde zu reimplementieren.

DIESE Stufe umgeht das Problem, statt es zu loesen: der SELF-PLAY-KORPUS
traegt den Zustand exakt (`state.players[p].pattern_lines` mit `tiles`/
`capacity`/`color`) und die legalen Zuege (`valid_actions`) direkt. Keine
Rekonstruktion, kein Regel-Nachbau, keine stille Annahme.

Metrik, auf Gelegenheit bedingt:

    Gelegenheit  = mindestens eine LEERE lange Reihe (Index 4/5) UND
                   mindestens eine legale Stein-Aktion, die genau dorthin
                   zielt
    Rate         = Wahrscheinlichkeitsmasse der `policy` auf genau diesen
                   Aktionen, gemittelt ueber Gelegenheits-Entscheidungen

`policy` ist die Besuchsverteilung der jeweiligen Suche -- fuer den
Champion-Korpus die des Netzes, fuer `data/holdout/selfplay_hold_heur_*`
die der Heuristik. Das ist der Agentenvergleich, den par.2 gebraucht haette
und den die erste Fassung faelschlich mit zwei Champion-Spalten gefuehrt
hat (dort korrigiert).

Zusaetzlich berichtet: wie oft die Gelegenheit ueberhaupt besteht -- das ist
der Konfundierer aus Stufe 1, hier als eigene Zahl sichtbar statt versteckt.
"""
import glob
import json
import pickle
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
EVAL = ROOT / "evaluations"
OUT_JSON = EVAL / "row_initiation_opportunity_probe.json"

LONG_IDX = (4, 5)     # 0-indexiert -> Musterreihe 5/6
SHORT_IDX = (0, 1, 2)  # -> Musterreihe 1/2/3
RNG = np.random.default_rng(20260824)
N_BOOT = 1000


def stratified_sample(files, stride):
    groups = defaultdict(list)
    for f in files:
        mm = re.search(r"selfplay_([a-zA-Z0-9]+)_", Path(f).name)
        groups[mm.group(1) if mm else "?"].append(f)
    out = []
    for gen in sorted(groups):
        out.extend(sorted(groups[gen])[::stride])
    return sorted(out)


def analyse_record(rec):
    """None, wenn keine Gelegenheit; sonst dict mit Masse und Kontext."""
    st = rec.get("state") or {}
    if st.get("phase") != "drafting":
        return None
    p = rec.get("player")
    if p is None:
        return None
    pls = st["players"][p]["pattern_lines"]
    by_idx = {row["index"]: row for row in pls}
    leer_lang = {i for i in LONG_IDX if len(by_idx[i]["tiles"]) == 0}
    leer_kurz = {i for i in SHORT_IDX if len(by_idx[i]["tiles"]) == 0}

    va = rec.get("valid_actions") or []
    ziel_lang = any(a.get("type") == "stone" and a.get("row") in leer_lang for a in va)
    ziel_kurz = any(a.get("type") == "stone" and a.get("row") in leer_kurz for a in va)
    if not ziel_lang:
        return dict(gelegenheit=False, runde=st.get("round"),
                    game_id=rec.get("game_id"), leer_lang=len(leer_lang))

    pol = rec.get("policy") or []
    masse_lang, masse_kurz, masse_gesamt = 0.0, 0.0, 0.0
    for e in pol:
        a, prob = e.get("action") or {}, float(e.get("prob", 0.0))
        masse_gesamt += prob
        if a.get("type") != "stone":
            continue
        if a.get("row") in leer_lang:
            masse_lang += prob
        elif a.get("row") in leer_kurz:
            masse_kurz += prob
    if masse_gesamt <= 0:
        return None
    return dict(gelegenheit=True, runde=st.get("round"), game_id=rec.get("game_id"),
                masse_lang=masse_lang / masse_gesamt,
                masse_kurz=masse_kurz / masse_gesamt,
                kurz_moeglich=ziel_kurz, leer_lang=len(leer_lang))


def collect(files, cap_records=None):
    rows, n_drafting, n_gelegenheit = [], 0, 0
    for f in files:
        with open(f, "rb") as fh:
            recs = pickle.load(fh)
        for r in recs:
            a = analyse_record(r)
            if a is None:
                continue
            n_drafting += 1
            if not a["gelegenheit"]:
                continue
            n_gelegenheit += 1
            rows.append(a)
        if cap_records and len(rows) >= cap_records:
            break
    return rows, n_drafting, n_gelegenheit


def bootstrap_mean(rows, key, group_key="game_id"):
    by_g = defaultdict(list)
    for r in rows:
        by_g[r[group_key]].append(r[key])
    gs = list(by_g)
    if len(gs) < 10:
        return None
    vals = []
    for _ in range(N_BOOT):
        pick = RNG.choice(len(gs), size=len(gs), replace=True)
        flat = [v for i in pick for v in by_g[gs[i]]]
        if flat:
            vals.append(float(np.mean(flat)))
    a = np.array(vals)
    return dict(mean=round(float(a.mean()), 4), p2_5=round(float(np.percentile(a, 2.5)), 4),
                p97_5=round(float(np.percentile(a, 97.5)), 4))


def summarize(rows, n_drafting, n_gelegenheit, label):
    out = dict(label=label, n_drafting_entscheidungen=n_drafting,
               n_gelegenheiten=n_gelegenheit,
               gelegenheits_quote=round(n_gelegenheit / n_drafting, 4) if n_drafting else None,
               n_partien=len({r["game_id"] for r in rows}))
    for rnd in (None, 1, 2, 3, 4, 5):
        sel = rows if rnd is None else [r for r in rows if r["runde"] == rnd]
        lbl = "gesamt" if rnd is None else f"R{rnd}"
        if not sel:
            out[lbl] = dict(n=0)
            continue
        out[lbl] = dict(
            n=len(sel),
            masse_auf_lang_init=round(float(np.mean([r["masse_lang"] for r in sel])), 4),
            masse_auf_kurz_init=round(float(np.mean([r["masse_kurz"] for r in sel])), 4),
            bootstrap_95ci_lang=bootstrap_mean(sel, "masse_lang"),
        )
    return out


def main():
    stride = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    net_files = stratified_sample(sorted(glob.glob(str(ROOT / "data" / "selfplay_*.pkl"))), stride)
    heur_files = sorted(glob.glob(str(ROOT / "data" / "holdout" / "selfplay_hold_heur_*.pkl")))
    print(f"Netz: {len(net_files)} Dateien | Heuristik: {len(heur_files)} Dateien",
          file=sys.stderr)

    net_rows, net_nd, net_ng = collect(net_files)
    print(f"Netz: {net_nd} Drafting-Entscheidungen, {net_ng} mit Gelegenheit", file=sys.stderr)
    heur_rows, h_nd, h_ng = collect(heur_files)
    print(f"Heuristik: {h_nd} Drafting-Entscheidungen, {h_ng} mit Gelegenheit", file=sys.stderr)

    result = dict(
        netz=summarize(net_rows, net_nd, net_ng, "netz_selfplay"),
        heuristik=summarize(heur_rows, h_nd, h_ng, "heuristik_selfplay"),
        _meta=dict(
            metrik="Policy-Masse auf Aktionen, die eine LEERE lange Reihe "
                   "(Index 4/5) beginnen, bedingt auf Gelegenheit "
                   "(solche Aktion legal). Aus dem Korpus-Zustand, ohne "
                   "Rekonstruktion.",
            warum_nicht_aus_logs="round_end.rs:87 process_unplaceable_rows "
                                 "leert Musterreihen ohne Logzeile -- eine "
                                 "belegungsgenaue Log-Rekonstruktion ist "
                                 "unmoeglich (Selbsttest in "
                                 "row_opportunity_probe.py hat das gefangen).",
            caveat="Nicht gepaart: jede Seite in ihrer EIGENEN "
                   "Zustandsverteilung. Das ist fuer eine Verhaltensfrage "
                   "die richtige Rahmung, aber kein Same-Game-Vergleich.",
        ),
    )
    OUT_JSON.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n{'Seite':22s} {'Gelegenh.-Quote':>16s} " + " ".join(f"{b:>8s}" for b in
          ("gesamt", "R1", "R2", "R3", "R4", "R5")))
    for k in ("netz", "heuristik"):
        e = result[k]
        cells = []
        for b in ("gesamt", "R1", "R2", "R3", "R4", "R5"):
            v = e[b].get("masse_auf_lang_init")
            cells.append(f"{v:.1%}" if v is not None else "-")
        print(f"{k:22s} {e['gelegenheits_quote']:>16.1%} " + " ".join(f"{c:>8s}" for c in cells))
    print(f"\n-> {OUT_JSON}")


if __name__ == "__main__":
    main()
