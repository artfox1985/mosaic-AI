# -*- coding: utf-8 -*-
"""Tore (a) und (b) aus PREREG_moon_stack_order.md par.12.1 fuer den Arm v29-b04.

Frage: hat der `moon`-Kopf das REPARIERTE Ziel gelernt (Suchverteilung statt
No-Op-Label), und ist seine Prior-Masse von der kanonischen Reihenfolge
weggewandert?

Gemessen wird an Records des Val-Splits (Standard: `data/window_v29_b04_val.txt`,
byte-gleich mit `window_v29_v29-b03_val.txt`, 147 Dateien). Grundmenge:
Drafting-Records, deren `policy` fuer die Basisaktion mit der groessten
Gesamtmasse (Farbe, Fabrik, Reihe -- genau die Wahl von
`corpus_dataset.moon_target_from_policy`) mindestens ZWEI verschiedene
Mondreihenfolgen traegt. Nur dort gibt es etwas zu lernen. Je Modell und Record:

* `nll_played`  -- Plackett-Luce-NLL des b04-Trainingsziels (Suchverteilung,
  `moon_target_from_policy`) unter den 5 Kopf-Scores. Formel und
  Rang-Semantik EXAKT wie im Training: Rang je Farbe (`corpus_dataset.py:1490`,
  bei Farb-Wiederholung ueberschreibt der spaetere Rang) und
  `train.py::plackett_luce_moon_loss` (sequenzieller Softmax ueber die noch
  nicht platzierten Farben, Schritte ohne Rang werden uebersprungen).
* `nll_canonical` -- dieselbe NLL fuer die kanonische Reihenfolge DERSELBEN
  Basisaktion (Sonnenseite ohne die genommene Farbe, `validation.rs:177-183`).
* `p_canonical` -- exp(-nll_canonical), die Prior-Masse auf der kanonischen
  Reihenfolge (Tor b). b03 hat laut par.12.0 eine Konstante gelernt, sein Wert
  sollte hoch sein; bei b04 muss er fallen.
* `nll_label` -- NLL des ALTEN Labels `moon_order_target` (gehoert zur
  tatsaechlich gespielten Aktion, die von der massereichsten Basis abweichen
  kann -- deshalb getrennt ausgewiesen).
* Vergleich: Gleichverteilung ueber die eindeutigen Reihenfolgen, NLL = ln(k).

Tor (a) laut par.12.1: `nll_played` von b04 UNTER dem b03-Wert.
Tor (b): `p_canonical` von b04 UNTER dem b03-Wert.

Selbsttest 1 (par.12.0 je Record): das alte Label muss die kanonische
Reihenfolge IRGENDEINER (Fabrik, Farbe) des Zustands sein -- passt die
Multimenge, aber nicht die Reihenfolge, waere par.12.0 widerlegt.
Selbsttest 2: derselbe Zustand zweimal bewertet gibt dieselben Scores.

Kein Eingriff am Spiel, keine Suche, kein Wheel-Bau.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "engine" / "py"))
import corpus_io  # noqa: E402
from corpus_dataset import moon_target_from_policy  # noqa: E402
import mosaic_rust as mr  # noqa: E402
import numpy as np  # noqa: E402
import onnxruntime as ort  # noqa: E402
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))  # runtime_block liegt in tools/
from runtime_block import laufzeit_block  # noqa: E402  (CLAUDE.md-Pflichtblock)

# Spiegel von corpus_dataset.py:1143 (dort lokal in der Bau-Schleife definiert):
# Reihenfolge der fuenf Kopf-Ausgaenge.
_CIDX = {'blau': 0, 'gelb': 1, 'rot': 2, 'schwarz': 3, 'türkis': 4}


def rank_vector(order):
    """corpus_dataset.py:1488-1492: Rang je Farbe, -1 = Farbe nicht im Rest;
    bei Wiederholung einer Farbe bleibt der SPAETERE Rang stehen."""
    v = [-1] * 5
    for rank, c in enumerate(order):
        i = _CIDX.get(c, -1)
        if i >= 0:
            v[i] = rank
    return v


def pl_nll(scores, order):
    """train.py::plackett_luce_moon_loss fuer EINE Zeile, auf dem Rang-Vektor."""
    ranks = rank_vector(order)
    present = [r >= 0 for r in ranks]
    placed = [False] * 5
    nll = 0.0
    for t in range(5):
        is_t = [present[i] and ranks[i] == t for i in range(5)]
        if not any(is_t):
            continue
        avail = [present[i] and not placed[i] for i in range(5)]
        logits = np.array([scores[i] if avail[i] else -1e9 for i in range(5)], dtype=np.float64)
        logits -= logits.max()
        logz = math.log(np.exp(logits).sum())
        idx = is_t.index(True)
        nll -= float(logits[idx] - logz)
        placed[idx] = True
    return nll


def canonical_order(state, color, factory_index):
    """Sonnenseite ohne die genommene Farbe, in Sonnenseiten-Reihenfolge
    (validation.rs:177-183; factory_index = Position in state.factories,
    self_play.rs::factory_pos)."""
    facs = state.get("factories") or []
    if factory_index is None or factory_index >= len(facs):
        return None
    return [t for t in facs[factory_index].get("sun", []) if t != color]


def label_check(state, label):
    """Selbsttest 1: ist das alte Label die kanonische Reihenfolge einer
    (Fabrik, Farbe) dieses Zustands? Rueckgabe: 'kanonisch', 'multimenge_aber_andere_reihenfolge',
    'keine_fabrik_passt'."""
    label = list(label)
    multiset_hit = False
    for fac in state.get("factories") or []:
        sun = fac.get("sun", [])
        for color in set(sun):
            canon = [t for t in sun if t != color]
            if canon == label:
                return "kanonisch"
            if sorted(canon) == sorted(label):
                multiset_hit = True
    return "multimenge_aber_andere_reihenfolge" if multiset_hit else "keine_fabrik_passt"


def best_base_group(policy):
    """Dieselbe Gruppierung wie moon_target_from_policy: Basis mit der groessten
    Gesamtmasse, dazu alle Reihenfolgen dieser Basis."""
    groups = {}
    for pe in policy or []:
        a = pe.get("action") or {}
        if a.get("type") != "stone" or not a.get("moon_order"):
            continue
        base = (a.get("color"), a.get("factory_index"), a.get("row"))
        groups.setdefault(base, []).append((float(pe.get("prob", 0.0)), tuple(a["moon_order"])))
    if not groups:
        return None, None
    base, entries = max(groups.items(), key=lambda kv: sum(p for p, _ in kv[1]))
    return base, entries


def moon_scores(state, sess, cache):
    js = json.dumps(state, sort_keys=True)
    if js in cache:
        return cache[js]
    flach = np.asarray(mr.state_features_from_json(js), dtype=np.float32)[None, :]
    planes, shape = mr.state_planes_from_json(js)
    planes = np.asarray(planes, dtype=np.float32).reshape((1,) + tuple(shape))
    out = sess.run(["moon"], {"planes": planes, "state": flach})[0]
    scores = np.asarray(out, dtype=np.float64).ravel()[:5]
    cache[js] = scores
    return scores


def summ(xs):
    xs = np.asarray(xs, dtype=np.float64)
    if not xs.size:
        return {"n": 0}
    return {"mean": round(float(xs.mean()), 5), "median": round(float(np.median(xs)), 5), "n": int(xs.size)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", required=True,
                    help="name=pfad.onnx, z. B. v29-b03=models/alphazero_v29-b03_brierbest.onnx")
    ap.add_argument("--val-list", default="data/window_v29_b04_val.txt")
    ap.add_argument("--max-files", type=int, default=0, help="0 = alle Dateien der Liste")
    ap.add_argument("--max-records", type=int, default=0, help="0 = alle passenden Records")
    ap.add_argument("--out", default="evaluations/artifacts/moon_head_target_probe.json")
    a = ap.parse_args()
    t0, c0 = time.monotonic(), time.process_time()

    files = [ln.strip() for ln in open(a.val_list, encoding="utf-8") if ln.strip() and not ln.startswith("#")]
    files = [f if os.path.isabs(f) or f.startswith("data") else os.path.join("data", f) for f in files]
    if a.max_files:
        files = files[: a.max_files]
    opts = ort.SessionOptions()
    opts.intra_op_num_threads = 1
    sessions = {}
    for spec in a.models:
        name, path = spec.split("=", 1)
        sessions[name] = ort.InferenceSession(path, sess_options=opts, providers=["CPUExecutionProvider"])
    print(f"[moon_probe] {len(files)} Val-Dateien, Modelle {list(sessions)}", flush=True)

    per_model = {n: {"nll_played": [], "nll_canonical": [], "nll_label": [], "p_canonical": [],
                     "p_played": [], "top_is_canonical": 0, "top_is_played": 0} for n in sessions}
    uniform_nll = []
    n_records = n_sun = 0
    n_played_ne_canon = 0
    label_stats = {"kanonisch": 0, "multimenge_aber_andere_reihenfolge": 0, "keine_fabrik_passt": 0, "kein_label": 0}
    selftest = None
    caches = {n: {} for n in sessions}
    done = False
    for f in files:
        for r in corpus_io.load_records(f):
            base, entries = best_base_group(r.get("policy"))
            if base is None:
                continue
            n_sun += 1
            orders = {seq for _, seq in entries}
            if len(orders) < 2:
                continue
            played = moon_target_from_policy(r)
            if not played:
                continue
            state = r["state"]
            color, fi, _row = base
            canon = canonical_order(state, color, fi)
            if canon is None:
                continue
            label = r.get("moon_order_target")
            label_stats[label_check(state, label) if label else "kein_label"] += 1
            n_records += 1
            n_played_ne_canon += int(list(played) != canon)
            uniform_nll.append(math.log(len(orders)))
            for name, sess in sessions.items():
                sc = moon_scores(state, sess, caches[name])
                if selftest is None:
                    selftest = float(np.abs(sc - moon_scores(state, sess, {})).max())
                d = per_model[name]
                nl_p = pl_nll(sc, played)
                nl_c = pl_nll(sc, canon)
                d["nll_played"].append(nl_p)
                d["nll_canonical"].append(nl_c)
                d["p_played"].append(math.exp(-nl_p))
                d["p_canonical"].append(math.exp(-nl_c))
                if label:
                    d["nll_label"].append(pl_nll(sc, list(label)))
                # Kopf-Favorit unter den eindeutigen Reihenfolgen der Basis:
                fav = min(orders, key=lambda seq: pl_nll(sc, list(seq)))
                d["top_is_canonical"] += int(list(fav) == canon)
                d["top_is_played"] += int(list(fav) == list(played))
            if n_records % 250 == 0:
                print(f"[moon_probe] {n_records} Records ({time.monotonic() - t0:.0f} s)", flush=True)
            if a.max_records and n_records >= a.max_records:
                done = True
                break
        if done:
            break

    result = {
        "prereg": "PREREG_moon_stack_order.md par.12.1 Tore (a) und (b), Arm v29-b04",
        "val_list": a.val_list,
        "dateien": len(files),
        "grundmenge": "Val-Records, deren massereichste Basisaktion (Farbe, Fabrik, Reihe) in der "
                      "Suchverteilung mindestens zwei eindeutige Mondreihenfolgen traegt",
        "einheit": "Plackett-Luce-NLL je Record in nats (Rang-Semantik wie im Training); p = exp(-NLL)",
        "n_records": n_records,
        "n_records_mit_sonnenzug_in_policy": n_sun,
        "anteil_played_ungleich_kanonisch": round(n_played_ne_canon / n_records, 4) if n_records else None,
        "selbsttest_altes_label_gegen_kanonisch": label_stats,
        "selbsttest_determinismus_max_abs": selftest,
        "gleichverteilung_nll": summ(uniform_nll),
        "modelle": {},
        "laufzeit": laufzeit_block(t0, cpu_start=c0, threads=1,
                                   n_units=n_records, unit="record") | {"n_records": n_records},
    }
    for name, d in per_model.items():
        result["modelle"][name] = {
            "nll_played": summ(d["nll_played"]),
            "nll_canonical": summ(d["nll_canonical"]),
            "nll_label_alt": summ(d["nll_label"]),
            "p_played": summ(d["p_played"]),
            "p_canonical": summ(d["p_canonical"]),
            "anteil_kopf_favorit_kanonisch": round(d["top_is_canonical"] / n_records, 4) if n_records else None,
            "anteil_kopf_favorit_played": round(d["top_is_played"] / n_records, 4) if n_records else None,
        }
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    print(json.dumps({k: v for k, v in result.items() if k not in ("val_list",)}, ensure_ascii=False, indent=1), flush=True)


if __name__ == "__main__":
    main()
