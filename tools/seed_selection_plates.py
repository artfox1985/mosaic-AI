# -*- coding: utf-8 -*-
"""tools/seed_selection_plates.py -- Seed-Auswahl fuer den Plattenkopf-Versuch
(`evaluations/PREREG_plate_head.md`, 2026-08-11).

Hintergrund: `MOSAIC_WERTUNG_ALPHA` nimmt acht kommagetrennte Werte, einen je
Wertungsplatten-Kriterium (`net_mcts.rs::wertung_shaping_alphas`). Um den
Effekt EINER Platte auf ihr eigenes Alpha zurechenbar zu messen -- statt auf
irgendeine der immer 3 gleichzeitig liegenden Platten --, braucht der Versuch
je Kriterium Partien, in denen GENAU dieses Kriterium aktiv ist. Welche
Kriterien in einer Partie aktiv sind, ist vollstaendig durch den Seed
bestimmt (siehe `scoring_ids_for_seed`) -- man muss also geeignete Seeds
AUSWAEHLEN statt eine fortlaufende Spanne zu spielen.

Dieses Werkzeug:
  1. Durchsucht eine Seed-Spanne und liest je Seed `scoring_tile_ids`, OHNE
     eine Partie zu spielen.
  2. Baut daraus eine GREEDY Abdeckung: so wenige Seeds wie moeglich, so dass
     jedes gewuenschte Kriterium in mindestens `--pro-kriterium` (Default 20)
     der ausgewaehlten Seeds vorkommt.
  3. Berichtet je Kriterium, wie viele Partien es TATSAECHLICH abdeckt (durch
     die Ueberschneidung -- immer 3 Platten je Partie -- kommt es bei manchen
     Kriterien zu Ueberdeckung; das ist gewollt, muss aber sichtbar bleiben).
  4. Schreibt die Auswahl als JSON nach `evaluations/`, damit der Versuch
     reproduzierbar ist.

Startet KEIN Self-Play, KEINE Arena, KEIN Training -- nur `PyGame`-Konstruktion
(Setup, kein Zug) je durchsuchtem Seed.

Nutzung:
    python tools/seed_selection_plates.py --seed-start 0 --seed-count 600 \
        --pro-kriterium 20 --out evaluations/seed_selection_plates.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Windows-Default fuer stdout ist cp1252 -- "Äußere Felder" u.ae. brechen sonst
# beim Print (gleiches Muster wie paired_arena_arm_worker.py/paired_arena_env_ab.py).
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent

# Muss mit engine/src/scoring.rs::ALL_SCORING_TILES uebereinstimmen (gleiche
# Duplizierung wie in tools/scoring_tile_distribution.py -- dort ebenfalls per
# Kommentar an die Rust-Quelle gebunden statt importiert, weil es kein
# Python-Binding fuer die Namenstabelle gibt).
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
ALL_CRITERIA: tuple[int, ...] = tuple(sorted(TILE_NAMES.keys()))


def scoring_ids_for_seed(seed: int) -> tuple[int, ...]:
    """Liest `scoring_tile_ids` fuer einen Seed, OHNE zu spielen.

    `PyGame.__new__` zieht die Platten als ALLERERSTES aus dem seed-eigenen
    `StdRng` (`sample_valid_scoring_ids`), bevor irgendein Zug angewendet wird
    (`py.rs::PyGame::new`) -- exakt dieselbe Ableitung wie in den
    Arena-Funktionen, die dieselben Seeds spielen wuerden
    (`self_play.rs::run_net_arena_match`/`run_net_vs_net_arena`: beide seeden
    `StdRng::seed_from_u64(game_seed)` und ziehen `sample_valid_scoring_ids(3, ..)`
    als ersten RNG-Verbrauch). Ein `PyGame`-Konstruktoraufruf reicht daher, um
    vorherzusagen, welche Platten eine ECHTE Partie mit demselben Seed tragen
    wird -- vom Nutzer 2026-08-11 selbst so verifiziert (600 Seeds, ~37% Anteil
    je Kriterium, 32 Kombinationen)."""
    import mosaic_rust  # spaet importiert -- nur beim ersten Aufruf faellig
    g = mosaic_rust.PyGame(("A", "B"), 0, seed)
    state = json.loads(g.state_json())
    return tuple(sorted(state["scoring_tile_ids"]))


def greedy_cover(
    seed_to_ids: dict[int, tuple[int, ...]],
    pro_kriterium: int,
    criteria: tuple[int, ...] = ALL_CRITERIA,
) -> tuple[list[int], dict[int, int]]:
    """Greedy Mehrfachabdeckung (kein exaktes Set-Cover-Optimum, aber die
    uebliche Naeherung dafuer): waehlt wiederholt den Seed, der die meisten
    NOCH FEHLENDEN Kriterien bedient. Ein Seed, der nur bereits erfuellte
    Kriterien traegt, zaehlt dabei 0 -- so werden nicht mehr Seeds gewaehlt
    als noetig, nur weil sie irgendein Kriterium tragen.

    Bricht ab, sobald jedes Kriterium `>= pro_kriterium` erreicht hat, ODER
    wenn kein verbleibender Seed noch etwas zu einem offenen Kriterium
    beitraegt (dann bleiben Kriterien unter dem Ziel -- das MUSS sichtbar
    bleiben, siehe Rueckgabewert `coverage`, das die TATSAECHLICHE, nicht auf
    das Ziel gekappte Abdeckung zaehlt).

    Rueckgabe: (gewaehlte Seeds in Auswahlreihenfolge, {kriterium: n_partien}).
    """
    remaining_need = {c: pro_kriterium for c in criteria}
    coverage = {c: 0 for c in criteria}
    picked: list[int] = []
    candidates = dict(seed_to_ids)  # wird abgebaut, damit jeder Seed nur 1x gewaehlt wird

    while any(v > 0 for v in remaining_need.values()) and candidates:
        best_seed, best_gain = None, -1
        for seed in sorted(candidates):  # deterministische Reihenfolge fuer Tie-Break
            ids = candidates[seed]
            gain = sum(1 for c in ids if remaining_need.get(c, 0) > 0)
            if gain > best_gain:
                best_seed, best_gain = seed, gain
        if best_gain <= 0:
            break  # kein Kandidat bedient noch ein offenes Kriterium
        picked.append(best_seed)
        for c in candidates[best_seed]:
            if c in coverage:
                coverage[c] += 1
                remaining_need[c] = max(0, remaining_need[c] - 1)
        del candidates[best_seed]

    return picked, coverage


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed-start", type=int, default=0)
    ap.add_argument("--seed-count", type=int, default=600,
                     help="Anzahl durchsuchter Seeds, Spanne [seed-start, seed-start+seed-count)")
    ap.add_argument("--pro-kriterium", type=int, default=20,
                     help="Mindestanzahl Partien je Kriterium (Default 20)")
    ap.add_argument("--kriterien", default=None,
                     help="Kommagetrennte Kriterien-IDs (Default: alle 8, 0-7)")
    ap.add_argument("--out", default=None,
                     help="Default: evaluations/seed_selection_plates.json")
    args = ap.parse_args()

    criteria = ALL_CRITERIA
    if args.kriterien:
        criteria = tuple(sorted(int(x.strip()) for x in args.kriterien.split(",") if x.strip()))
        unknown = [c for c in criteria if c not in TILE_NAMES]
        if unknown:
            raise SystemExit(f"Unbekannte Kriterien-IDs: {unknown} (gueltig: 0-7)")

    seed_range = range(args.seed_start, args.seed_start + args.seed_count)
    print(f"Lese scoring_tile_ids fuer {len(seed_range)} Seeds "
          f"({args.seed_start}..{seed_range[-1]}) -- keine Partie wird gespielt.")
    seed_to_ids: dict[int, tuple[int, ...]] = {}
    for i, seed in enumerate(seed_range):
        seed_to_ids[seed] = scoring_ids_for_seed(seed)
        if (i + 1) % 100 == 0:
            print(f"  {i + 1}/{len(seed_range)} Seeds gelesen...")

    picked, coverage = greedy_cover(seed_to_ids, args.pro_kriterium, criteria)

    print(f"\n=== Greedy-Auswahl: {len(picked)} Seeds fuer >= {args.pro_kriterium} "
          f"Partien je Kriterium ({len(criteria)} Kriterien) ===")
    under_target = []
    for c in criteria:
        meets = coverage[c] >= args.pro_kriterium
        if not meets:
            under_target.append(c)
        print(f"  {c} {TILE_NAMES[c]:22s}: {coverage[c]:3d}/{args.pro_kriterium}  "
              f"[{'OK' if meets else 'UNTER ZIEL'}]")

    if under_target:
        print(f"\nWARNUNG: {len(under_target)} Kriterien erreichen das Ziel in dieser Spanne "
              f"nicht -- --seed-count vergroessern oder --pro-kriterium senken.")

    result = {
        "seed_start": args.seed_start,
        "seed_count": args.seed_count,
        "pro_kriterium": args.pro_kriterium,
        "kriterien": list(criteria),
        "n_seeds_scanned": len(seed_range),
        "n_seeds_selected": len(picked),
        "selected_seeds": picked,
        "selected_seeds_scoring_tile_ids": {str(s): list(seed_to_ids[s]) for s in picked},
        "coverage_per_criterion": {
            str(c): {
                "name": TILE_NAMES[c],
                "n_games": coverage[c],
                "target": args.pro_kriterium,
                "meets_target": coverage[c] >= args.pro_kriterium,
            }
            for c in criteria
        },
        "criteria_under_target": under_target,
    }
    out_path = Path(args.out) if args.out else (BASE_DIR / "evaluations" / "seed_selection_plates.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nAuswahl geschrieben nach {out_path}")
    print(f"Seeds (fuer --seeds von paired_arena_env_ab.py/paired_arena_arm_worker.py): "
          f"{','.join(str(s) for s in picked)}")
    return 1 if under_target else 0


if __name__ == "__main__":
    raise SystemExit(main())
