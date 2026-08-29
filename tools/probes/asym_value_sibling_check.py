# -*- coding: utf-8 -*-
"""Teilfrage B des Asym-Curriculums (PREREG_asymmetric_curriculum.md par.6):
bevaluest der VALUE-Kopf des Lehr-Arms (S) Geschwister-Nachfolger mit mehr
k1-Spaltenfortschritt hoeher als der Kontroll-Arm (N) -- auf DENSELBEN
Stellungen?

Stellungsbasis: der bestehende Nachfolger-Dump
`evaluations/probe_sibling_succ_k1_w1.0.json` (40 Runde-2-Stellungen mit je
~15 Kandidaten samt `successor_state_json`/`mover`) -- modellunabhaengige
Artefakte, also fuer beide Netze identisch (gepaartes Design, Referenz je
Stellung wie in par.6 verlangt).

Je Kandidat: Praedikat = Summe der gestauchten Spalten-Puffer des Ziehenden
auf dem Nachfolger (`reach_target.reach_buffer_columns`, wie in
`sibling_order_vs_predicate.py`); Wert = roher Value-Kopf des ONNX
(Ausgang 'value', ego-perspektivisch fuer `current_player` des Nachfolgers,
Vorzeichen-Flip wenn der Ziehende dort nicht am Zug ist --
Nullsummen-Semantik wie `net_leaf_eval`, net_mcts.rs:2358). Kendall-Tau je
Stellung, ausgewiesen als Differenz S gegen N (gepaart, Vorzeichentest +
t ueber Stellungen). KEINE vorregistrierte Schwelle -- par.6 verlangt nur
den Ausweis der Differenz.

    python -X utf8 tools/probes/asym_value_sibling_check.py
"""
from __future__ import annotations

import json
import statistics
import sys
from math import comb
from pathlib import Path

BASIS = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASIS))  # config.py liegt im Repo-Root (neural_net importiert es)
sys.path.insert(0, str(BASIS / "engine" / "py"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np  # noqa: E402
import onnxruntime as ort  # noqa: E402

from neural_net import state_to_planes, state_to_tensor  # noqa: E402
from reach_target import reach_buffer_columns  # noqa: E402
from sibling_order_stability import kendall  # noqa: E402

# Nachzug 2026-08-29 (Fahrplan Phase 0.2): Modelle und Ausgabepfad per CLI
# uebersteuerbar, Defaults = urspruengliche Messung (par.15). Mit nur EINEM
# Modell (--model-n '') entfaellt der gepaarte Vergleich; berichtet wird dann
# die Tau-Verteilung dieses Modells gegen die protokollierten Alt-Werte.
import argparse

_ap = argparse.ArgumentParser()
_ap.add_argument("--model-s", default=str(BASIS / "models/alphazero_v21-seedk1_best.onnx"))
_ap.add_argument("--model-n", default=str(BASIS / "models/alphazero_v21-asymN_best.onnx"))
_ap.add_argument("--out", default=str(BASIS / "evaluations/artifacts/seedk1_value_sibling_check.json"))
_args = _ap.parse_args()

MODELS = {"S": Path(_args.model_s)}
if _args.model_n:
    MODELS["N"] = Path(_args.model_n)
DUMP = BASIS / "evaluations/artifacts/probe_sibling_succ_k1_w1.0.json"
OUT = Path(_args.out)


def value_for_mover(sess, succ: dict, mover: int) -> float:
    state = np.asarray(state_to_tensor(succ), dtype=np.float32)[None, :]
    planes = state_to_planes(succ).numpy().astype(np.float32)[None, ...]
    outs = sess.run(["value"], {"planes": planes, "state": state})
    v = float(outs[0].reshape(-1)[0])
    return v if succ["current_player"] == mover else -v


def main() -> None:
    daten = json.loads(DUMP.read_text(encoding="utf-8"))["stellungen"]
    sessions = {k: ort.InferenceSession(str(p), providers=["CPUExecutionProvider"])
                for k, p in MODELS.items()}

    arms = list(MODELS)
    taus = {arm: [] for arm in arms}
    n_pos = 0
    for eintrag in daten:
        praed = {}
        values = {arm: {} for arm in arms}
        for desc, kd in eintrag["kandidaten"].items():
            sj, mover = kd.get("successor_state_json"), kd.get("mover")
            if sj is None or mover is None:
                continue
            succ = json.loads(sj)
            buf = reach_buffer_columns(succ, mover)
            if buf is None:
                continue
            praed[desc] = sum(buf)
            for arm, sess in sessions.items():
                values[arm][desc] = value_for_mover(sess, succ, mover)
        if len(praed) < 3 or len(set(praed.values())) < 2:
            continue
        ts = {arm: kendall(values[arm], praed) for arm in arms}
        if any(v is None for v in ts.values()):
            continue
        n_pos += 1
        for arm in arms:
            taus[arm].append(ts[arm])

    result = {
        "n_stellungen": n_pos,
        "modelle": {k: str(p.name) for k, p in MODELS.items()},
        "dump": DUMP.name,
    }
    for arm in arms:
        result[f"tau_mean_{arm}"] = statistics.mean(taus[arm])
    print(f"Stellungen: {n_pos}")
    print("Tau(Value~k1-Puffer)  " + "   ".join(
        f"{arm}: {result[f'tau_mean_{arm}']:+.3f}" for arm in arms))

    if len(arms) == 2:
        a, b = arms
        diffs = [x - y for x, y in zip(taus[a], taus[b])]
        m = statistics.mean(diffs)
        sd = statistics.stdev(diffs) if len(diffs) > 1 else float("nan")
        t = m / (sd / len(diffs) ** 0.5) if sd and sd > 0 else float("nan")
        pos = sum(1 for d in diffs if d > 0)
        neg = sum(1 for d in diffs if d < 0)
        nz = pos + neg
        p_sign = min(1.0, 2 * sum(comb(nz, k) for k in range(0, min(pos, neg) + 1)) / 2 ** nz) if nz else 1.0
        result.update({
            "diff_mean": m, "diff_sd": sd, "diff_t": t,
            "vorzeichen": {f"{a}_besser": pos, f"{b}_besser": neg,
                           "gleich": len(diffs) - nz},
            "p_vorzeichentest": p_sign,
        })
        print(f"Differenz {a}-{b}: {m:+.3f} (sd {sd:.3f}, t {t:+.2f}); Vorzeichen "
              f"{pos}/{neg}/{len(diffs) - nz}, p(Vorzeichentest) {p_sign:.3f}")

    OUT.write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Ergebnis: {OUT}")


if __name__ == "__main__":
    main()
