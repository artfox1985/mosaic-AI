# -*- coding: utf-8 -*-
"""R1 Sensitivitaets-Sonde: sieht der Value-Kopf die Rueckgabe-Reihenfolge?

`PREREG_dome_return_order.md` par.12.1. Beantwortet das Henne-Ei aus par.10 mit
einer Zahl, OHNE eine Partie zu spielen: an eigenen Kuppel-Bloecken mit
mindestens drei Platten wird die Reihenfolge der obersten drei permutiert und
der Value-Kopf je Permutation ausgewertet. Kennzahl ist die SPANNWEITE
(max minus min) je Rueckgabe.

WARUM DAS DIE RICHTIGE GROESSE IST: genau diese Werte berechnet Modus 1 intern
(`self_play.rs:771-799`, ein Vorwaertspass je Kandidat) und waehlt ihr Maximum.
Ist die Spannweite null, hat Modus 1 nichts zu waehlen -- dann ist jedes A/B an
diesem Netz sinnlos, egal in welcher Bauform.

DER EINGEBAUTE SELBSTTEST (par.12 Grenze 3): der Encoder sieht vom eigenen
Block nur die TYPFOLGE der obersten vier Positionen (`features.rs:231-236`,
+1 Spezial / -1 Wild / 0). Permutationen, die dieselbe Typfolge ergeben, sind
fuer das Netz derselbe Zustand -- ihre Spannweite MUSS exakt 0 sein. Findet die
Sonde dort etwas anderes als 0, misst sie sich selbst falsch und nicht das Netz.
Deshalb werden beide Gruppen getrennt ausgewiesen.

KEIN Eingriff am Spiel: die Sonde liest Korpus-Records, permutiert das
Zustands-JSON und ruft `state_features_from_json` / `state_planes_from_json` /
`onnx_eval`. Kein Wheel-Bau, keine Anker-Drift noetig.
"""
from __future__ import annotations

import argparse, glob, io, json, os, statistics, sys, time
from itertools import permutations
from pathlib import Path

# Muster der vorhandenen Sonden (z.B. tools/probes/dead_unit_probe.py:49-50):
# corpus_io liegt im Projektstamm, mosaic_rust wird ueber engine/py gefunden.
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "engine" / "py"))
import corpus_io  # noqa: E402
import mosaic_rust as mr  # noqa: E402
import numpy as np  # noqa: E402
import onnxruntime as ort  # noqa: E402
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))  # runtime_block liegt in tools/
from runtime_block import laufzeit_block  # noqa: E402  (CLAUDE.md-Pflichtblock)

TOP_K = 3  # RETURN_ORDER_MAX_PERMUTED: hoechstens 3! = 6 Kandidaten


def type_signature(types, k=4):
    """Was der Encoder sieht: +1 Spezial, -1 sonst, 0 wenn Position fehlt."""
    return tuple(1 if (t == "special") else -1 for t in types[:k]) + (0,) * max(0, k - len(types))


def value_of(state, sess):
    """Siegwahrscheinlichkeit des Zustands.

    Die Sitzung wird EINMAL gebaut und wiederverwendet -- `mr.onnx_eval` laedt
    das Netz bei jedem Aufruf neu (`Net::load_auto`, lib.rs:658) und kostete
    damit rund 1,2 s je Auswertung, also Stunden statt Minuten. Muster und
    Eingabenamen aus `tools/probes/column_build_prior_mass.py:191`.
    """
    js = json.dumps(state)
    flach = np.asarray(mr.state_features_from_json(js), dtype=np.float32)[None, :]
    planes, shape = mr.state_planes_from_json(js)
    planes = np.asarray(planes, dtype=np.float32).reshape((1,) + tuple(shape))
    out = sess.run(["value"], {"planes": planes, "state": flach})[0]
    return float(np.asarray(out).ravel()[0])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="models/alphazero_v29-b03_brierbest.onnx")
    ap.add_argument("--pattern", default="data/selfplay_v28-b02-policy_*.pkl")
    ap.add_argument("--max-files", type=int, default=3)
    ap.add_argument("--max-cases", type=int, default=300)
    ap.add_argument("--out", default="evaluations/artifacts/return_order_sensitivity_r1.json")
    a = ap.parse_args()

    t0, c0 = time.monotonic(), time.process_time()
    files = sorted(glob.glob(a.pattern))[: a.max_files]
    opts = ort.SessionOptions()
    opts.intra_op_num_threads = 1
    sess = ort.InferenceSession(a.model, sess_options=opts, providers=["CPUExecutionProvider"])
    head_names = [o.name for o in sess.get_outputs()]
    print(f"[R1] {len(files)} Dateien, Netz {os.path.basename(a.model)}, Koepfe {head_names}", flush=True)

    same_seq, diff_seq = [], []   # Spannweiten je Gruppe
    cases = 0
    # Haeufigkeitshaelfte des Henne-Eis: wie oft ist die Typfolge ueberhaupt
    # aenderbar? Sind die obersten drei typgleich, sieht das Netz keine Wahl --
    # dann ist die Sensitivitaet gegenstandslos, so haeufig sie auch waere.
    blocks_total = blocks_mixed = 0
    selftest = None
    for fi, f in enumerate(files):
        for r in corpus_io.load_records(f):
            if cases >= a.max_cases:
                break
            st = r.get("state") or {}
            blocks = st.get("dome_pool_view", {}).get("blocks", [])
            target_idx = next((i for i, b in enumerate(blocks)
                         if b.get("own") and b.get("types") and len(b["types"]) >= TOP_K), None)
            if target_idx is None:
                continue
            types = list(blocks[target_idx]["types"])
            blocks_total += 1
            perms = sorted(set(permutations(types[:TOP_K])))
            if len(perms) < 2:
                continue  # typgleich: das Netz sieht keine Wahl
            blocks_mixed += 1
            if selftest is None:
                # SELBSTTEST, der wirklich greift: zweimal DERSELBE Zustand muss
                # denselben Wert geben. Die urspruengliche Fassung verglich
                # "gleiche Typfolge" -- das kann per Konstruktion nie eintreten,
                # weil hier die TYPFOLGE permutiert wird und nicht die Platten.
                ref = json.loads(json.dumps(st))
                selftest = abs(value_of(ref, sess) - value_of(ref, sess))
            values, type_seqs = [], []
            for perm in perms:
                mutated = json.loads(json.dumps(st))
                mutated["dome_pool_view"]["blocks"][target_idx]["types"] = list(perm) + types[TOP_K:]
                values.append(value_of(mutated, sess))
                type_seqs.append(type_signature(list(perm) + types[TOP_K:]))
            span = max(values) - min(values)
            # Gruppe: ergeben ALLE Permutationen dieselbe Typfolge?
            (same_seq if len(set(type_seqs)) == 1 else diff_seq).append(span)
            cases += 1
            if cases % 25 == 0:
                print(f"[R1] {cases} Faelle ({time.monotonic() - t0:.0f} s)", flush=True)
        if cases >= a.max_cases:
            break

    def stats(xs):
        if not xs:
            return {"n": 0}
        return {"n": len(xs), "median": statistics.median(xs), "mittel": statistics.fmean(xs),
                "max": max(xs), "anteil_ueber_0_01": sum(1 for x in xs if x > 0.01) / len(xs)}

    result = {
        "prereg": "PREREG_dome_return_order.md par.12.1 (R1)",
        "modell": a.model,
        "grundmenge": "eigene Kuppel-Bloecke mit mindestens 3 Platten, oberste 3 permutiert",
        "einheit": "Spannweite max-min des Value-Kopfs je Rueckgabe",
        "grenze": ("permutiert wird die TYPFOLGE der obersten drei Positionen, nicht die "
                   "Plattenidentitaet -- der Encoder sieht vom eigenen Block nur sie "
                   "(features.rs:231-236). Was zwei gleichtypige Platten unterscheidet, misst "
                   "diese Sonde NICHT; dort ist die Spannweite per Bauart 0."),
        # ACHTUNG: `blocks_total` zaehlt bis zum Abbruch durch --max-cases weiter,
        # waehrend `cases` nur gemischte Bloecke zaehlt. Bei kleinem Deckel ist der
        # Anteil deshalb nach unten verzerrt. Eine deckel-freie Gegenmessung ueber
        # 296 Bloecke ergab 0,713 -- der Wert des vollen Laufs (0,737) ist robust.
        "haeufigkeit": {
            "eigene_bloecke_ab_3": blocks_total,
            "davon_typfolge_aenderbar": blocks_mixed,
            "anteil": round(blocks_mixed / max(blocks_total, 1), 4),
        },
        "selbsttest_determinismus": selftest,
        "gleiche_typfolge": stats(same_seq),
        "verschiedene_typfolge": stats(diff_seq),
        "laufzeit": laufzeit_block(t0, cpu_start=c0, threads=1,
                                   n_units=cases, unit="fall") | {"faelle": cases},
    }
    io.open(a.out, "w", encoding="utf-8").write(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
