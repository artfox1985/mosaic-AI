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
import time
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

def _spielername(draft: str, tiling: str | None) -> str:
    """Spiegelt die Namensregel der Engine (self_play.rs, `name_mit_achse`).

    Die Engine haengt die Tiling-Achse an, sobald sie von der Draft-Achse
    abweicht -- sonst traegen beide Seiten eines Routing-Splits denselben Namen
    und die Brett-Rekonstruktion mischt sie. Diese Funktion MUSS der dortigen
    Regel folgen; laufen sie auseinander, findet die Auswertung ihre Seite
    nicht wieder.
    """
    return f"Heuristik_{draft}_tile{tiling}" if tiling and tiling != draft else f"Heuristik_{draft}"


ARM_A, ARM_B = "v2", "v2huelle"
if "--arms" in sys.argv:
    ARM_A, ARM_B = sys.argv[sys.argv.index("--arms") + 1].split(":")

# `--tiling A:B` (PREREG_v22_window.md par.4c): Variante der PLATZIERUNG je
# Seite, getrennt von der des Draftings. Weggelassen = wie `--arms`, also der
# Bestandslauf aus par.8.4 Zeichen fuer Zeichen.
#
# Damit ist der Split-Test ausdrueckbar, der die 0,73 vollen Spalten des
# Lehrers in seine beiden Haelften zerlegt:
#   --arms v1:v2huelle --tiling v1:v1   -> nur die DRAFT-Haelfte wirkt
#   --arms v1:v1 --tiling v1:v2huelle   -> nur die ROUTING-Haelfte wirkt
TILING_A = TILING_B = None
if "--tiling" in sys.argv:
    TILING_A, TILING_B = sys.argv[sys.argv.index("--tiling") + 1].split(":")
NAME_A, NAME_B = _spielername(ARM_A, TILING_A), _spielername(ARM_B, TILING_B)
# Anzeige- und Artefakt-Schluessel. Normalerweise die Armnamen; beim
# Routing-Split heissen aber BEIDE Arme gleich ("v1" gegen "v1"), und dann
# ueberschreibt der zweite Eintrag den ersten -- die Tabelle zeigte zweimal
# dieselbe Zahl. Der tragende Wert (`delta`, je Partie gepaart) war nie
# betroffen, die ROHWERTE je Seite schon.
LABEL_A, LABEL_B = (ARM_A, ARM_B) if ARM_A != ARM_B else (NAME_A, NAME_B)
SIMS, THREADS, C_PUCT = 150, 0, 0.3
SEED = 20260825
OUT_JSON = ROOT / "evaluations" / "artifacts" / "v2_envelope_arena.json"

# Vorregistriert: 80 gepaarte Partien JE SITZ. `--games` ist ausschliesslich
# fuer den Rauchtest da -- ein Messlauf mit anderer Zahl waere ein anderer
# Lauf als der in par.8.4 registrierte.
GAMES_PER_SEAT = 80
BLOCK = 16
if "--games" in sys.argv:
    GAMES_PER_SEAT = int(sys.argv[sys.argv.index("--games") + 1])
    BLOCK = max(1, GAMES_PER_SEAT // 5)
    OUT_JSON = ROOT / "evaluations" / "artifacts" / "v2_envelope_arena_smoke.json"
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
    # Blindziehungen je Seite. GEZAEHLT, nicht aus dem Punktestand abgeleitet:
    # bei Punktestand 0 ist eine Ziehung gratis und damit im Punktestand
    # unsichtbar, und zwar UNGLEICHMAESSIG -- der tiefer ziehende Arm wird
    # staerker abgeschnitten, ein Armvergleich unterschaetzt den Unterschied
    # also systematisch. Hinweis der Parallelsitzung, Ursache in game.rs:182
    # (Score kann nie unter 0 fallen).
    ziehungen = Counter()
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
            continue
        sp = PATTERNS["STACK_PEEK"].match(text)
        if sp:
            ziehungen[sp.group("name")] += 1

    out: dict[str, dict] = {}
    for name in (NAME_A, NAME_B):
        fill = column_fill(cells.get(name, set()))
        out[name] = {
            **struktur_kennzahlen(fill),
            "reihen": dict(rows.get(name, Counter())),
            "spezial_freischaltungen": unlocks.get(name, 0),
            "strafpunkte": strafe.get(name, 0),
            "ziehungen": ziehungen.get(name, 0),
        }
    return out


def run_seat(swap: bool) -> list[dict]:
    roh = mr.heuristic_v1_vs_v2_arena(
        SIMS, SIMS, GAMES_PER_SEAT, SEED, THREADS, C_PUCT, swap, True, ARM_A, ARM_B,
        TILING_A, TILING_B
    )
    spiele = json.loads(roh)
    if isinstance(spiele, dict) and "error" in spiele:
        raise SystemExit(f"Arena-Fehler: {spiele['error']}")
    for g in spiele:
        g["_swap"] = swap
    return spiele


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    # Laufzeit ist Pflichtfeld im Artefakt (CLAUDE.md, "Laufzeiten messen,
    # nicht schaetzen"). `process_time` erfasst auch die Rust-Arbeit, weil sie
    # im selben Prozess laeuft.
    t0, c0 = time.monotonic(), time.process_time()
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
                    "spezial_freischaltungen", "strafpunkte", "ziehungen"):
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

    # Aufspaltung nach Wertungsplatte. k1 liegt nur in rund 40 Prozent der
    # Partien an, und `scoring_progress` kreditiert Spaltenfuellung
    # ausschliesslich dann -- eine Karte aus Plattenpunkten muesste dort ohne
    # Spaltensignal dastehen.
    # Kriterium 1 = Spalten, Kriterium 6 = leere Spezialfelder. Die 6 ist
    # zusaetzlich aufgespalten, weil `resolve_and_apply_stack_draw`
    # (self_play.rs:500-545) bei aktiver 6 deutlich tiefer blind zieht und
    # jede Ziehung 1 Punkt kostet -- ein Punkte-Vorsprung, der sich DORT
    # konzentriert, kaeme aus dem Ziehmechanismus und nicht aus besserem Spiel.
    k1_split = {}
    for kid, kname, key in ((1, "k1", "volle_spalten"), (6, "k6", "punkte"),
                            (6, "k6zieh", "ziehungen")):
        for label, pred in ((f"{kname}_aktiv", True), (f"{kname}_inaktiv", False)):
            idx = [i for i, g in enumerate(spiele) if (kid in g.get("scoring_tile_ids", [])) is pred]
            if not idx:
                continue
            d = [diffs[key][i] for i in idx]
            bl = block_mean(d, max(1, len(d) // 5))
            m, tw = t_value(bl)
            k1_split[label] = {
                "n": len(idx), "mass": key, f"delta_{key}": m, "t_block": tw,
                ARM_A: sum(roh_a[key][i] for i in idx) / len(idx),
                ARM_B: sum(roh_b[key][i] for i in idx) / len(idx),
            }

    n = len(spiele)
    ergebnis = {
        "k1_split": k1_split,
        "arme": [ARM_A, ARM_B], "n_partien": n, "sims": SIMS, "block": BLOCK,
        "laufzeit": {
            "wanduhr_s": round(time.monotonic() - t0, 1),
            "cpu_s": round(time.process_time() - c0, 1),
            "threads": THREADS,
            "s_je_partie": round((time.monotonic() - t0) / n, 3) if n else None,
        },
        "seed": SEED, "fehlende_bretter": fehlend,
        "arme": {"draft": [ARM_A, ARM_B],
                 "tiling": [TILING_A or ARM_A, TILING_B or ARM_B]},
        "siegquote_huelle": siege_b / n if n else 0.0,
        "vollendungsquote": {LABEL_A: quoten("a"), LABEL_B: quoten("b")},
        "reihenauslastung": {
            LABEL_A: {str(k): reihen_a[k] / n for k in sorted(reihen_a)},
            LABEL_B: {str(k): reihen_b[k] / n for k in sorted(reihen_b)},
        },
        "kennzahlen": {},
    }
    for key in ("volle_spalten", "max_hoehe", "teilspalten_ge3", "teilspalten_ge4",
                "spezial_freischaltungen", "strafpunkte", "ziehungen", "punkte"):
        bl = block_mean(diffs[key], BLOCK)
        mittel, t = t_value(bl)
        ergebnis["kennzahlen"][key] = {
            LABEL_A: sum(roh_a[key]) / n if n else 0.0,
            LABEL_B: sum(roh_b[key]) / n if n else 0.0,
            "delta": mittel, "t_block": t, "n_bloecke": len(bl),
        }

    OUT_JSON.write_text(json.dumps(ergebnis, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n{'Kennzahl':<26}{LABEL_A:>10}{LABEL_B:>12}{'Delta':>10}{'t(Block)':>10}")
    print("-" * 68)
    for key, v in ergebnis["kennzahlen"].items():
        print(f"{key:<26}{v[LABEL_A]:>10.3f}{v[LABEL_B]:>12.3f}{v['delta']:>10.3f}{v['t_block']:>10.2f}")
    print("\nAufspaltung nach Wertungsplatte (k1 = Spalten, k6 = leere Spezialfelder):")
    for label, v in ergebnis["k1_split"].items():
        key = v["mass"]
        print(f"  {label:<12} n={v['n']:<4} [{key}] {LABEL_A} {v[LABEL_A]:.3f}  {LABEL_B} {v[LABEL_B]:.3f}  "
              f"delta {v['delta_' + key]:+.3f}  t {v['t_block']:.2f}")
    print(f"\nSiegquote {ARM_B}: {ergebnis['siegquote_huelle']:.3f}")
    print(f"Vollendungsquote: {LABEL_A} {ergebnis['vollendungsquote'][LABEL_A]:.3f}  "
          f"{LABEL_B} {ergebnis['vollendungsquote'][LABEL_B]:.3f}  (B1-Waechter: >= 0,53)")
    print("Reihenauslastung je Partie (Rasterzeile: Zuege)")
    for arm in (LABEL_A, LABEL_B):
        z = ergebnis["reihenauslastung"][arm]
        print(f"  {arm:<10}" + "  ".join(f"{k}:{v:.2f}" for k, v in z.items()))
    if fehlend:
        print(f"\nWARNUNG: {fehlend} Partien ohne rekonstruierbares Brett")
    print(f"\ngeschrieben: {OUT_JSON}")


if __name__ == "__main__":
    main()
