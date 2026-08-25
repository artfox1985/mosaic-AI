# -*- coding: utf-8 -*-
"""Teilfrage B des Asym-Curriculums (PREREG_asymmetric_curriculum.md par.6):
bewertet der VALUE-Kopf des Lehr-Arms (S) Geschwister-Nachfolger mit mehr
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

MODELS = {
    "S": BASIS / "models/alphazero_v21-seedk1_best.onnx",
    "N": BASIS / "models/alphazero_v21-asymN_best.onnx",
}
DUMP = BASIS / "evaluations/artifacts/probe_sibling_succ_k1_w1.0.json"
OUT = BASIS / "evaluations/artifacts/seedk1_value_sibling_check.json"


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

    taus = {"S": [], "N": []}
    n_pos = 0
    for eintrag in daten:
        praed, werte = {}, {"S": {}, "N": {}}
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
                werte[arm][desc] = value_for_mover(sess, succ, mover)
        if len(praed) < 3 or len(set(praed.values())) < 2:
            continue
        t_s = kendall(werte["S"], praed)
        t_n = kendall(werte["N"], praed)
        if t_s is None or t_n is None:
            continue
        n_pos += 1
        taus["S"].append(t_s)
        taus["N"].append(t_n)

    diffs = [a - b for a, b in zip(taus["S"], taus["N"])]
    m = statistics.mean(diffs)
    sd = statistics.stdev(diffs) if len(diffs) > 1 else float("nan")
    t = m / (sd / len(diffs) ** 0.5) if sd and sd > 0 else float("nan")
    pos = sum(1 for d in diffs if d > 0)
    neg = sum(1 for d in diffs if d < 0)
    nz = pos + neg
    p_sign = min(1.0, 2 * sum(comb(nz, k) for k in range(0, min(pos, neg) + 1)) / 2 ** nz) if nz else 1.0

    result = {
        "n_stellungen": n_pos,
        "tau_mean_S": statistics.mean(taus["S"]),
        "tau_mean_N": statistics.mean(taus["N"]),
        "diff_mean": m, "diff_sd": sd, "diff_t": t,
        "vorzeichen": {"S_besser": pos, "N_besser": neg, "gleich": len(diffs) - nz},
        "p_vorzeichentest": p_sign,
        "modelle": {k: str(p.name) for k, p in MODELS.items()},
        "dump": DUMP.name,
    }
    OUT.write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Stellungen: {n_pos}")
    print(f"Tau(Value~k1-Puffer)  S: {result['tau_mean_S']:+.3f}   N: {result['tau_mean_N']:+.3f}")
    print(f"Differenz S-N: {m:+.3f} (sd {sd:.3f}, t {t:+.2f}); Vorzeichen S/N/= "
          f"{pos}/{neg}/{len(diffs) - nz}, p(Vorzeichentest) {p_sign:.3f}")
    print(f"Ergebnis: {OUT}")


if __name__ == "__main__":
    main()
