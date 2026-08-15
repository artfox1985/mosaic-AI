# -*- coding: utf-8 -*-
"""Vergleicht zwei golden_game_loop_capture-JSON-Ausgaben (VOR/NACH) je Pfad
auf Record-/Feld-Ebene. Muster wie PREREG_unified_game_loop.md §5.3 (0/N-
Zaehlung je Pfad, Feld-Zuordnung bei Abweichung).

Aufruf: python scratchpad/golden_diff.py <vor.json> <nach.json>
"""
import json
import sys
from collections import Counter


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    vor_path, nach_path = sys.argv[1], sys.argv[2]
    vor = load(vor_path)
    nach = load(nach_path)

    if len(vor) != len(nach):
        print(f"WARNUNG: unterschiedliche Record-Zahl: VOR={len(vor)} NACH={len(nach)}")

    n = min(len(vor), len(nach))
    n_diff_records = 0
    field_diff_counts = Counter()
    example_diffs = {}

    for i in range(n):
        a, b = vor[i], nach[i]
        if a == b:
            continue
        n_diff_records += 1
        keys = set(a.keys()) | set(b.keys())
        for k in keys:
            if a.get(k) != b.get(k):
                field_diff_counts[k] += 1
                if k not in example_diffs:
                    example_diffs[k] = (i, a.get(k), b.get(k))

    print(f"{vor_path} vs {nach_path}")
    print(f"n={n} Records, {n_diff_records} abweichend ({100.0*n_diff_records/max(1,n):.4f}%)")
    if field_diff_counts:
        print("\nAbweichungen je Feld:")
        for k, c in field_diff_counts.most_common():
            ex_i, ex_a, ex_b = example_diffs[k]
            ex_a_s = json.dumps(ex_a)[:200]
            ex_b_s = json.dumps(ex_b)[:200]
            print(f"  {k}: {c}/{n} ({100.0*c/n:.4f}%)  Beispiel Record {ex_i}: {ex_a_s} -> {ex_b_s}")
    else:
        print("Byte-identisch (keine Feld-Abweichung in irgendeinem Record).")


if __name__ == "__main__":
    main()
