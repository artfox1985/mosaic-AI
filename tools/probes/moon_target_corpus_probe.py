# -*- coding: utf-8 -*-
"""Korpus-Sonde fuer v29-b04: wie oft weicht die GESPIELTE Mondstapel-Reihenfolge
von der kanonischen ab?

`PREREG_moon_stack_order.md` par.12.1. Das Tor fuer b04: liegt der Anteil unter
10 Prozent, ist das Ziel "gespielte Reihenfolge" ein Henne-Ei (der Korpus traegt
kaum Abweichungen, also kaum Lernsignal) -- dann faellt B1 und nur B2 mit einem
v30-Korpus bleibt.

DER TRICK, den par.12.0 moeglich macht: `moon_order_target` im Record IST die
kanonische Reihenfolge. Der Bewerter des Labels liest die Fabriken nicht
(`tiling_solver.rs:396-401`), alle Permutationen scoren gleich, und weil die
Aufzaehlung mit der Identitaet beginnt, ist das Label immer die kanonische
Folge. Der No-Op-Befund liefert also gratis den Referenzwert.

Die GESPIELTE Reihenfolge steht im FOLGEZUSTAND: nach dem Sonnenzug liegt der
Rest als Mond-Stapel in der Fabrik (`execution.rs:147-159`). Verglichen wird
also Record N (Label) gegen den Stapel in Record N+1 derselben Partie.
"""
from __future__ import annotations

import argparse, glob, io, json, os, sys, time
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "engine" / "py"))
import corpus_io  # noqa: E402


def stacks_after_move(state):
    """Alle Mond-Stapel als Liste von Farbfolgen, unten zuerst."""
    out = []
    for f in state.get("factories", []) or []:
        # Feldname des SERIALISIERTEN Zustands ist "moon" (serialize.rs:205),
        # nicht "moon_stacks" wie im Rust-Struct.
        for s in f.get("moon", []) or []:
            if s:
                out.append(tuple(s))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pattern", default="data/selfplay_v28-b02-*.pkl")
    ap.add_argument("--max-files", type=int, default=20)
    ap.add_argument("--out", default="evaluations/artifacts/moon_target_corpus_probe.json")
    a = ap.parse_args()

    t0 = time.time()
    files = sorted(glob.glob(a.pattern))[: a.max_files]
    print(f"[moon-korpus] {len(files)} Dateien", flush=True)

    c = Counter()
    lengths = Counter()
    for i, f in enumerate(files):
        recs = corpus_io.load_records(f)
        for n, r in enumerate(recs):
            target_idx = r.get("moon_order_target")
            if not target_idx or len(target_idx) < 2:
                continue
            c["entscheide"] += 1
            lengths[len(target_idx)] += 1
            # Folgezustand derselben Partie suchen
            nxt = None
            for m in range(n + 1, min(n + 3, len(recs))):
                if recs[m].get("game_id") == r.get("game_id"):
                    nxt = recs[m]["state"]
                    break
            if nxt is None:
                c["ohne_folgezustand"] += 1
                continue
            played = [s for s in stacks_after_move(nxt) if len(s) == len(target_idx)]
            if not played:
                c["stapel_nicht_gefunden"] += 1
                continue
            # Die kanonische Folge ist das Label; der Stapel liegt unten-zuerst,
            # das Label ist die Rueckgabe-Reihenfolge in derselben Ordnung.
            if any(list(s) == list(target_idx) for s in played):
                c["kanonisch"] += 1
            else:
                c["abweichend"] += 1
        if (i + 1) % 5 == 0:
            print(f"[moon-korpus] {i+1}/{len(files)} Dateien, {c['entscheide']} Entscheide "
                  f"({time.time()-t0:.0f} s)", flush=True)

    scored = c["kanonisch"] + c["abweichend"]
    result = {
        "prereg": "PREREG_moon_stack_order.md par.12.1 (Korpus-Sonde fuer b04)",
        "grundmenge": "Records mit moon_order_target (Sonnenzug kleine Fabrik, Rest >= 2)",
        "einheit": "Anteil der Entscheide mit nicht-kanonischer gespielter Reihenfolge",
        "dateien": len(files),
        "zaehler": dict(c),
        "laengen_des_ziels": dict(lengths),
        "bewertet": scored,
        "anteil_abweichend": round(c["abweichend"] / scored, 4) if scored else None,
        "tor": "unter 0,10 = Henne-Ei, dann faellt B1 (nur B2 mit v30-Korpus)",
        "laufzeit": {"wanduhr_s": round(time.time() - t0, 1)},
    }
    io.open(a.out, "w", encoding="utf-8").write(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
