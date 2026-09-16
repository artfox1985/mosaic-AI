# -*- coding: utf-8 -*-
"""32c, kontrafaktisch: um wie viel aendert die Reihenfolge-Wahl das PAKET,
das ein Gegnerzug abraeumen kann?

`PREREG_moon_stack_order.md` par.12.3b. Schliesst die Luecke aus par.12.3a: die
Zugriffs-Bilanz mass, ob GENAU DIESER Stein geholt wird (enge Frage). Die
eigentliche Hebelgroesse ist eine andere, weil ein Mondzug AKTION C ist und alle
Oberseiten einer Farbe auf einmal nimmt (`validation.rs:214`, `factory_id: None`).

DIE GROESSE: Ein Sonnenzug legt die Reststeine als Stapel auf den Mond. Welcher
davon OBEN liegt, ist die Wahl. Liegt Farbe c oben, waechst das Paket der Farbe c
um eins -- und das Paket ist danach `moon_top_counts[c] + 1`. Der Hebel einer
Entscheidung ist die SPANNWEITE dieser Paketgroesse ueber die waehlbaren Farben.

WARUM KEIN ZAEHLER IM CODE noetig war: der serialisierte Zustand traegt
`moon_top_counts` bereits (`serialize.rs:385`) -- die Zahl der Stapel je
Oberseiten-Farbe ueber ALLE Fabriken. Damit ist die kontrafaktische Rechnung aus
dem Korpus moeglich, ohne den Spielpfad anzufassen: kein Wheel-Bau, keine
Anker-Drift, Sekunden statt Stunden.

GRUNDMENGE: Records mit `moon_order_target` (Sonnenzug aus kleiner Fabrik mit
Rest >= 2). Dass dieses Feld die KANONISCHE Reihenfolge traegt, ist hier
gleichgueltig -- gebraucht wird nur die MENGE der Reststeine.
"""
from __future__ import annotations

import argparse, glob, io, json, statistics, sys, time
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "engine" / "py"))
import corpus_io  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pattern", default="data/selfplay_v28-b02-*.pkl")
    ap.add_argument("--max-files", type=int, default=20)
    ap.add_argument("--out", default="evaluations/artifacts/moon_bundle_leverage.json")
    args = ap.parse_args()
    t0 = time.time()

    files = sorted(glob.glob(args.pattern))[: args.max_files]
    print(f"[buendel-hebel] {len(files)} Dateien", flush=True)

    spans, choices, best_sizes = [], Counter(), []
    no_choice = 0
    for i, f in enumerate(files):
        for r in corpus_io.load_records(f):
            rest = r.get("moon_order_target")
            if not rest or len(rest) < 2:
                continue
            counts = r["state"].get("moon_top_counts") or {}
            colours = sorted(set(rest))
            choices[len(colours)] += 1
            if len(colours) < 2:
                no_choice += 1
                continue
            # Paketgroesse, wenn Farbe c oben liegt: die bereits oben liegenden
            # Stapel dieser Farbe plus der neue.
            sizes = [counts.get(c, 0) + 1 for c in colours]
            spans.append(max(sizes) - min(sizes))
            best_sizes.append(max(sizes))
        if (i + 1) % 5 == 0:
            print(f"[buendel-hebel] {i+1}/{len(files)} Dateien, {len(spans)} Entscheide "
                  f"({time.time()-t0:.0f} s)", flush=True)

    n = len(spans)
    verteilung = Counter(spans)
    result = {
        "prereg": "PREREG_moon_stack_order.md par.12.3b (kontrafaktischer Buendel-Hebel)",
        "grundmenge": "Sonnenzuege aus kleiner Fabrik mit Rest >= 2 UND mindestens zwei Farben",
        "einheit": "Spannweite der Paketgroesse (max minus min) ueber die waehlbaren Oberseiten",
        "dateien": len(files),
        "entscheide_mit_wahl": n,
        "entscheide_ohne_wahl_alle_gleich": no_choice,
        "farben_je_entscheid": dict(sorted(choices.items())),
        "spannweite": {
            "verteilung": dict(sorted(verteilung.items())),
            "median": statistics.median(spans) if spans else None,
            "mittel": round(statistics.fmean(spans), 4) if spans else None,
            "anteil_ueber_0": round(sum(1 for s in spans if s > 0) / n, 4) if n else None,
            "anteil_ab_2": round(sum(1 for s in spans if s >= 2) / n, 4) if n else None,
        },
        "groesstes_erreichbares_paket": {
            "median": statistics.median(best_sizes) if best_sizes else None,
            "mittel": round(statistics.fmean(best_sizes), 4) if best_sizes else None,
            "max": max(best_sizes) if best_sizes else None,
        },
        "lesart": ("Spannweite 0 heisst: die Wahl aendert das Paket nicht, der Hebel ist an "
                   "dieser Stelle null. Je hoeher der Anteil ueber 0, desto haeufiger steuert "
                   "die Reihenfolge, wie viel ein einziger Gegnerzug abraeumen kann."),
        "laufzeit": {"wanduhr_s": round(time.time() - t0, 1)},
    }
    io.open(args.out, "w", encoding="utf-8").write(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
