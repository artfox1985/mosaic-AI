#!/usr/bin/env python
"""PREREG_heuristic_v2_long_rows.md par.8.4: Prio-Leiter (`V2Huelle`) gegen das
bisherige v2-Routing.

Aufbau wie Messkette Schritt 2, damit die Zahlen mit der Bauschritt-Tabelle
vergleichbar bleiben: `V2` gegen `V2Huelle`, je 80 gepaarte Partien, BEIDE
Sitze, 150 Sims je Seite, gleiche Seeds, `log_games`.

Die BEWERTUNG beider Varianten ist byte-identisch (`player_total_variante`),
der einzige Unterschied ist die Zielzellen-Karte im Routing -- der Lauf misst
also genau das Routing.

**Vorregistriert (par.8.4), vor dem Lauf festgelegt:**

* Entscheidungsmass: volle Spalten je Partie, gepaart, auf BLOCK-Ebene.
* Falsifikator: steigen die vollen Spalten nicht signifikant, ist die Leiter
  als Routing-Bauform negativ entschieden.
* Waechter: faellt die Vollendungsquote langer Musterreihen unter 0,53,
  wiederholt der Arm `PREREG_long_row_payoff.md` B1 und gilt als negativ,
  auch bei mehr vollen Spalten.

Ausgewiesen werden zusaetzlich die sechs Standard-Kennzahlen (CLAUDE.md) je
Seite und als Differenz, plus die Spezialfeld-Freischaltungen -- Prio 5 zielt
genau darauf, und der Posten ist mit -11,94 Punkten der groesste
Einzelposten der Plattenwertung.

Auswertung auf BLOCK-Ebene, nicht je Partie: auf Partie-Ebene sind die
Paar-SEs massiv unterschaetzt (stehende Regel seit 2026-08-04).
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "engine" / "py"))
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "probes"))

import mosaic_rust as mr  # noqa: E402
from analyze_game_log import PATTERNS, ROUND_PREFIX  # noqa: E402
from column_build_structural_probe import (  # noqa: E402
    column_fill,
    reconstruct_game,
    struktur_kennzahlen,
)
from plate_points_from_arena import block_mean, t_value  # noqa: E402

ARM_A, ARM_B = "v2", "v2huelle"
NAME_A, NAME_B = f"Heuristik_{ARM_A}", f"Heuristik_{ARM_B}"
SIMS, THREADS, C_PUCT = 150, 0, 0.3
SEED = 20260825
OUT_JSON = ROOT / "evaluations" / "v2_envelope_arena.json"

# Vorregistriert: 80 gepaarte Partien JE SITZ. `--games` ist ausschliesslich
# fuer den Rauchtest da -- ein Messlauf mit anderer Zahl waere ein anderer
# Lauf als der in par.8.4 registrierte.
GAMES_PER_SEAT = 80
BLOCK = 16
if "--games" in sys.argv:
    GAMES_PER_SEAT = int(sys.argv[sys.argv.index("--games") + 1])
    BLOCK = max(1, GAMES_PER_SEAT // 5)
    OUT_JSON = ROOT / "evaluations" / "v2_envelope_arena_smoke.json"
# `--tag` fuer die Ablationen (par.8.4): gleicher Aufbau, gleicher Seed, nur
# eine Konstante im Code auf 0 -- die Ergebnisse muessen nebeneinander liegen.
if "--tag" in sys.argv:
    tag = sys.argv[sys.argv.index("--tag") + 1]
    OUT_JSON = OUT_JSON.with_name(f"{OUT_JSON.stem}_{tag}.json")


def _texte(log: list[str]):
    """Log-Zeilen ohne `[Rn] `-Praefix, Kommentarzeilen entfernt."""
    for roh in log or []:
        if roh.startswith("#"):
            continue
        m = ROUND_PREFIX.match(roh)
        yield m.group(2) if m else roh


def per_side_metrics(game: dict) -> dict[str, dict]:
    """Alle Kennzahlen je Spielername aus EINER Partie."""
    log = game.get("log") or []
    cells = reconstruct_game(log)

    rows = defaultdict(Counter)      # Reihenauslastung: Ziel-Rasterzeile je Zug
    unlocks = Counter()              # Spezialfeld-Freischaltungen
    strafe = Counter()               # Strafpunkte (negativ)
    for text in _texte(log):
        tp = PATTERNS["TILING_PLACE"].match(text)
        if tp:
            name = tp.group("name")
            # Slot (r,c) + Space-Index -> Rasterzeile 2*r + si//2 (board.rs)
            rows[name][2 * int(tp.group("r")) + int(tp.group("si")) // 2] += 1
            if tp.group("special"):
                unlocks[name] += 1
            continue
        rs = PATTERNS["ROUND_STRAFE"].match(text)
        if rs:
            strafe[rs.group("name")] += int(rs.group("pen"))

    out: dict[str, dict] = {}
    for name in (NAME_A, NAME_B):
        fill = column_fill(cells.get(name, set()))
        out[name] = {
            **struktur_kennzahlen(fill),
            "reihen": dict(rows.get(name, Counter())),
            "spezial_freischaltungen": unlocks.get(name, 0),
            "strafpunkte": strafe.get(name, 0),
        }
    return out


def run_seat(swap: bool) -> list[dict]:
    roh = mr.heuristic_v1_vs_v2_arena(
        SIMS, SIMS, GAMES_PER_SEAT, SEED, THREADS, C_PUCT, swap, True, ARM_A, ARM_B
    )
    spiele = json.loads(roh)
    if isinstance(spiele, dict) and "error" in spiele:
        raise SystemExit(f"Arena-Fehler: {spiele['error']}")
    for g in spiele:
        g["_swap"] = swap
    return spiele


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    spiele: list[dict] = []
    for swap in (False, True):
        print(f"[lauf] Sitz swap={swap}: {GAMES_PER_SEAT} Partien, {SIMS} Sims", flush=True)
        spiele += run_seat(swap)
    print(f"[lauf] fertig, {len(spiele)} Partien", flush=True)

    # Gepaarte Differenzen HUELLE minus v2, in Laufreihenfolge.
    diffs: dict[str, list[float]] = defaultdict(list)
    roh_a: dict[str, list[float]] = defaultdict(list)
    roh_b: dict[str, list[float]] = defaultdict(list)
    reihen_a, reihen_b = Counter(), Counter()
    siege_b = 0
    fehlend = 0

    for g in spiele:
        m = per_side_metrics(g)
        if not m[NAME_A]["fill"] or not m[NAME_B]["fill"]:
            fehlend += 1
        # Brett-Index je Variante: `v2_board` ist das Brett der Variante B.
        b_idx = int(g["v2_board"])
        a_idx = 1 - b_idx
        punkte = {NAME_A: float(g["scores"][a_idx]), NAME_B: float(g["scores"][b_idx])}
        if g.get("winner") == b_idx:
            siege_b += 1

        for key in ("volle_spalten", "max_hoehe", "teilspalten_ge3", "teilspalten_ge4",
                    "spezial_freischaltungen", "strafpunkte"):
            a, b = float(m[NAME_A][key]), float(m[NAME_B][key])
            roh_a[key].append(a)
            roh_b[key].append(b)
            diffs[key].append(b - a)
        roh_a["punkte"].append(punkte[NAME_A])
        roh_b["punkte"].append(punkte[NAME_B])
        diffs["punkte"].append(punkte[NAME_B] - punkte[NAME_A])
        diffs["marge"].append((punkte[NAME_B] - punkte[NAME_A]))

        reihen_a.update(m[NAME_A]["reihen"])
        reihen_b.update(m[NAME_B]["reihen"])

    # Vollendungsquote (B1-Waechter) aus den Arena-Zaehlern, je Seite.
    def quoten(idx_key: str) -> float:
        ges_start = ges_voll = 0
        for g in spiele:
            b_idx = int(g["v2_board"])
            i = b_idx if idx_key == "b" else 1 - b_idx
            ges_start += int(g["long_rows_started"][i])
            ges_voll += int(g["long_rows_completed"][i])
        return (ges_voll / ges_start) if ges_start else 0.0

    n = len(spiele)
    ergebnis = {
        "arme": [ARM_A, ARM_B], "n_partien": n, "sims": SIMS, "block": BLOCK,
        "seed": SEED, "fehlende_bretter": fehlend,
        "siegquote_huelle": siege_b / n if n else 0.0,
        "vollendungsquote": {ARM_A: quoten("a"), ARM_B: quoten("b")},
        "reihenauslastung": {
            ARM_A: {str(k): reihen_a[k] / n for k in sorted(reihen_a)},
            ARM_B: {str(k): reihen_b[k] / n for k in sorted(reihen_b)},
        },
        "kennzahlen": {},
    }
    for key in ("volle_spalten", "max_hoehe", "teilspalten_ge3", "teilspalten_ge4",
                "spezial_freischaltungen", "strafpunkte", "punkte"):
        bl = block_mean(diffs[key], BLOCK)
        mittel, t = t_value(bl)
        ergebnis["kennzahlen"][key] = {
            ARM_A: sum(roh_a[key]) / n if n else 0.0,
            ARM_B: sum(roh_b[key]) / n if n else 0.0,
            "delta": mittel, "t_block": t, "n_bloecke": len(bl),
        }

    OUT_JSON.write_text(json.dumps(ergebnis, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n{'Kennzahl':<26}{ARM_A:>10}{ARM_B:>12}{'Delta':>10}{'t(Block)':>10}")
    print("-" * 68)
    for key, v in ergebnis["kennzahlen"].items():
        print(f"{key:<26}{v[ARM_A]:>10.3f}{v[ARM_B]:>12.3f}{v['delta']:>10.3f}{v['t_block']:>10.2f}")
    print(f"\nSiegquote {ARM_B}: {ergebnis['siegquote_huelle']:.3f}")
    print(f"Vollendungsquote: {ARM_A} {ergebnis['vollendungsquote'][ARM_A]:.3f}  "
          f"{ARM_B} {ergebnis['vollendungsquote'][ARM_B]:.3f}  (B1-Waechter: >= 0,53)")
    print("Reihenauslastung je Partie (Rasterzeile: Zuege)")
    for arm in (ARM_A, ARM_B):
        z = ergebnis["reihenauslastung"][arm]
        print(f"  {arm:<10}" + "  ".join(f"{k}:{v:.2f}" for k, v in z.items()))
    if fehlend:
        print(f"\nWARNUNG: {fehlend} Partien ohne rekonstruierbares Brett")
    print(f"\ngeschrieben: {OUT_JSON}")


if __name__ == "__main__":
    main()
