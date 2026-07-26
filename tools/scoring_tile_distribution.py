"""
Mosaic-AI -- Wertungsplatten-Randomisierungs-Audit (Wertungsplatten-Diagnose,
Teil 2, 2026-07-26)
============================================================================

Reine Lese-Analyse ueber vorhandene Self-Play-Pickles: zaehlt, welche der 8
Wertungsplatten (`engine/src/scoring.rs::ALL_SCORING_TILES`) tatsaechlich in
`sample_valid_scoring_ids(3, rng)` (pro Spiel EINMAL gezogen, siehe
`self_play.rs::run_net_self_play`) gewaehlt werden. Jeder Self-Play-Record
traegt `state["scoring_tile_ids"]` (siehe `serialize.rs::state_to_json`) --
das Feld ist fuer ALLE Records eines Spiels identisch (einmal pro Spiel
gezogen), ein einziger Record pro Spiel reicht also.

Erwartung laut `sample_valid_scoring_ids` (scoring.rs):
  - 4 Ausschluss-Paare, aus JEDEM Paar kommt GENAU EINE Seite in den Pool von
    4 Kandidaten (Muenzwurf pro Paar).
  - Aus diesem 4er-Pool werden 3 zufaellig gezogen (geshuffelt + truncate(3)).
  - Erwartung: jede Platte einzeln ~50% Auswahlrate INNERHALB ihres Paares
    (welche Seite ueberhaupt in den Pool kommt), und von den 4 Pool-Slots
    kommen im Mittel 3/4 = 75% tatsaechlich ins Spiel (unabhaengig davon,
    welche Platte es ist) -- KEIN Grund fuer Uniformitaet ueber alle 8 IDs
    gemeinsam (das waere nur bei einem einzigen Pool aus 8 der Fall).

Startet KEIN Self-Play, KEINE Arena, KEIN Training -- nur pickle.load +
Auszaehlen. Liest data/ NUR (kein Schreibzugriff).
"""
import argparse
import glob
import json
import os
import pickle
from collections import Counter
from itertools import combinations

# Muss mit engine/src/scoring.rs::MUTUALLY_EXCLUSIVE_PAIRS übereinstimmen.
MUTUALLY_EXCLUSIVE_PAIRS = [(0, 7), (6, 3), (4, 1), (2, 5)]
TILE_NAMES = {
    0: "Horizontale Reihen",
    1: "Vertikale Reihen",
    2: "Diagonale Reihen",
    3: "Mehrfarbige Felder",
    4: "Äußere Felder",
    5: "Eckplatten",
    6: "Spezialfelder",
    7: "Farbenreiche Reihen",
}


def iter_game_scoring_ids(filepath):
    """Ein `scoring_tile_ids`-Tripel je Spiel (erster angetroffener Record je
    game_id reicht -- das Feld ist über das ganze Spiel konstant)."""
    with open(filepath, "rb") as f:
        data = pickle.load(f)
    seen = set()
    out = []
    for r in data:
        gid = r["game_id"]
        if gid in seen:
            continue
        seen.add(gid)
        ids = tuple(sorted(r["state"]["scoring_tile_ids"]))
        out.append((gid, ids))
    del data
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-glob", default="data/selfplay_v16_*.pkl")
    ap.add_argument("--limit-files", type=int, default=None, help="None = alle Dateien")
    ap.add_argument("--out", default="evaluations/scoring_tile_distribution_v16.json")
    args = ap.parse_args()

    files = sorted(glob.glob(args.data_glob))
    if args.limit_files:
        files = files[: args.limit_files]
    if not files:
        raise SystemExit(f"Keine Dateien für Glob {args.data_glob!r} gefunden.")

    tile_count = Counter()          # Einzelplatte -> Anzahl Spiele, in denen gewählt
    combo_count = Counter()         # 3er-Kombination -> Anzahl Spiele
    pool_side_count = Counter()     # (paar_index, seite) -> Anzahl Spiele, in denen diese Seite im Pool war
    n_games = 0
    n_conflicts = 0  # sollte 0 bleiben (sample_valid_scoring_ids garantiert das)

    for i, fp in enumerate(files):
        for gid, ids in iter_game_scoring_ids(fp):
            n_games += 1
            assert len(ids) == 3, f"{gid}: erwartet 3 IDs, war {ids}"
            for t in ids:
                tile_count[t] += 1
            combo_count[ids] += 1
            for pair_idx, (a, b) in enumerate(MUTUALLY_EXCLUSIVE_PAIRS):
                has_a, has_b = a in ids, b in ids
                if has_a and has_b:
                    n_conflicts += 1
                if has_a:
                    pool_side_count[(pair_idx, a)] += 1
                if has_b:
                    pool_side_count[(pair_idx, b)] += 1
        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(files)} Dateien, {n_games} Spiele bisher...")

    print(f"\n=== Wertungsplatten-Verteilung ({n_games} Spiele aus {len(files)} Dateien, glob={args.data_glob}) ===")
    print(f"Ausschluss-Konflikte (sollte 0 sein): {n_conflicts}")

    print("\n-- Einzelplatte: Anteil der Spiele, in denen sie GEWÄHLT wurde (von 3 aus 8) --")
    print("   Erwartung bei 4 fairen Münzwürfen × 3-aus-4-Ziehung: 0.5 (Pool) × 0.75 (Ziehung) = 0.375 pro Platte")
    per_tile = {}
    for t in range(8):
        share = tile_count[t] / n_games if n_games else 0.0
        per_tile[t] = {"name": TILE_NAMES[t], "n_chosen": tile_count[t], "share": share}
        print(f"   {t} {TILE_NAMES[t]:22s}: {tile_count[t]:5d}/{n_games} = {share:.1%}")

    print("\n-- Pro Ausschluss-Paar: welche Seite kam in den Pool (sollte je ~50/50 sein) --")
    per_pair = {}
    for pair_idx, (a, b) in enumerate(MUTUALLY_EXCLUSIVE_PAIRS):
        na, nb = pool_side_count[(pair_idx, a)], pool_side_count[(pair_idx, b)]
        total = na + nb
        share_a = na / total if total else 0.0
        per_pair[pair_idx] = {
            "pair": [a, b],
            "names": [TILE_NAMES[a], TILE_NAMES[b]],
            "n_a": na, "n_b": nb, "share_a": share_a, "n_total": total,
        }
        print(f"   Paar {pair_idx} ({TILE_NAMES[a]} vs {TILE_NAMES[b]}): "
              f"{a}={na} ({share_a:.1%})  {b}={nb} ({1-share_a:.1%})  (total={total}, erwartet ~{n_games})")

    print("\n-- Häufigste 3er-Kombinationen --")
    n_possible_combos = 0
    # Zulaessige Kombinationen: 3 aus dem 4er-Pool (1 pro Paar) -> C(4,3)=4 moegliche
    # AUSWAHLEN pro konkreter Pool-Realisierung, aber ueber alle 2^4=16 Pool-
    # Realisierungen hinweg gibt es potenziell viele verschiedene 3er-Sets.
    combo_items = combo_count.most_common(15)
    for combo, cnt in combo_items:
        share = cnt / n_games
        names = [TILE_NAMES[t] for t in combo]
        print(f"   {combo} {names}: {cnt} ({share:.1%})")
    n_unique_combos = len(combo_count)
    print(f"\n   Insgesamt {n_unique_combos} unterschiedliche 3er-Kombinationen beobachtet "
          f"(bei fairer Ziehung theoretisch bis zu {4 * 2**4} = 64 durch Paar-Munzwurf x 4-Wahl, "
          f"praktisch weniger durch Symmetrien).")

    result = {
        "data_glob": args.data_glob,
        "n_files": len(files),
        "n_games": n_games,
        "n_exclusion_conflicts": n_conflicts,
        "per_tile": per_tile,
        "per_pair": per_pair,
        "top_combos": [{"ids": list(c), "names": [TILE_NAMES[t] for t in c], "count": cnt, "share": cnt / n_games}
                        for c, cnt in combo_items],
        "n_unique_combos": n_unique_combos,
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\nErgebnis geschrieben nach {args.out}")


if __name__ == "__main__":
    main()
