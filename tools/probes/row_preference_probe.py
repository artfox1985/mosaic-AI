# -*- coding: utf-8 -*-
"""Musterreihen-Praeferenz-Sonde (Auftrag 2026-08-23): prueft die Nutzer-
Hypothese "Policy ist auf Reihen statt Spalten getrimmt, weil die Heuristik
so spielt -- schnelle Punkte ueber die oberen (kurzen) Musterreihen, Spalten
muss man ueber 3-4 Runden aufbauen."

WICHTIGE BEGRIFFS-KLAERUNG (docs/engine_manual.md Abschnitt 4, Phase 2
"Tiling", Zeile 127): "Rows are worked strictly top to bottom (1 through 6)
... Each completed row sends exactly one tile to the Kuppel." Die hier
gemessene "Reihe" ist die MUSTERREIHE (Draft-Ziel, Kapazitaet 1..6 je
Reihenindex 1..6) -- Reihenindex und Kuppel-ZEILE sind namensgleich UND
funktional gekoppelt: Musterreihe N speist Kuppel-Zeile N. Die Sonde bleibt
damit direkt an den STATUS.md-Strukturbefund ("0,55 Spalten je Partie exakt
auf Hoehe 5 stehen gelassen") anschlussfaehig.

Quelle des Zeilenwahl-Musters: tools/analyze_game_log.py PATTERNS["SUN_TAKE"]
und PATTERNS["MOON_GLOBAL_TAKE"] (1:1 aus den log_event(...)-Aufrufen der
Engine transkribiert, siehe dortiger Modul-Docstring) -- hier NUR importiert,
nicht nachgebaut. Beide matchen ausschliesslich Zeilen der Form
"NAME: n× FARBE von QUELLE(N) -> Reihe N [f/c]" bzw. "Strafleiste"; die
Kollisionsgefahr mit TILING_SCORE ("Reihe N -> Kuppel ...", umgekehrte
Pfeilrichtung) besteht nicht, weil hier nur auf "-> Reihe" gematcht wird.

LASTSPERRE: reines Datei-Lesen + Single-Thread-Python. Kein mosaic_rust-
Import, kein Engine-Replay, kein Build.

Datenquellen:
  1. evaluations/paired_arena_env_imm_netvnet.json  -- Champion beidseitig
     (model == model_b, geprueft unten per Assertion).
  2. evaluations/paired_arena_env_imm_a02.json       -- Champion (Netz) vs.
     Heuristik, direkter Abstammungsvergleich, zwei Arme (0 / 0.2), hier
     kombiniert UND einzeln ausgewiesen.
  3. evaluations/paired_arena_env_seedk1_nullarm.json -- seedk1 (NetzA) vs.
     Champion (NetzB).
  4. data/holdout/selfplay_hold_heur_*.pkl -- reine Heuristik-Selbstspiel-
     Partien ("Bauer"), verifiziert gegen engine/src/self_play.rs:2002-2024/
     2057 (`HeuristicSelfPlayAgent` auf BEIDEN Spielerslots, `names =
     ["Spieler 1", "Spieler 2"]`) -- NICHT Netz-Selbstspiel.

     GRENZE (im Bericht auszuweisen): das `state.log`-Feld je Record ist NUR
     der Log der LAUFENDEN RUNDE (reset bei Rundenwechsel, geprueft an einem
     Beispielspiel: letzter Record von Runde 5 enthaelt ausschliesslich
     "[R5] ..."-Zeilen). Es gibt kein kumulatives Ganzspiel-Log in den pkl-
     Records. Rekonstruktion hier: je Spiel und Runde der Record mit dem
     LAENGSTEN Log wird herangezogen (= der informativste Stand dieser
     Runde). Da jeder Record den Log-Stand VOR seiner eigenen Aktion traegt,
     fehlt in dieser Rekonstruktion die allerletzte Log-Zeile der jeweiligen
     Runde (die Aktion, die den Rundenwechsel ausloest) -- ein kleiner,
     bekannter Randverlust (< 1 Zeile von typischerweise 15-25 Aktionen je
     Rundenhaelfte), keine systematische Verzerrung der Reihenverteilung.

Aufruf:
    python -X utf8 tools/probes/row_preference_probe.py
"""
from __future__ import annotations

import glob
import json
import pickle
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from analyze_game_log import PATTERNS, ROUND_PREFIX  # noqa: E402
from plate_points_from_arena import game_list  # noqa: E402

EVAL = ROOT / "evaluations"
OUT_JSON = EVAL / "row_preference_probe.json"

ROW_CATS = ("SUN_TAKE", "MOON_GLOBAL_TAKE")


def row_choices_from_log(log_lines: list[str]):
    """Liefert (runde:int, name:str, reihe:int) je Musterreihen-Zuweisung in
    `log_lines`. Strafleiste-Ziele werden NICHT gezaehlt (keine Reihenwahl)."""
    out = []
    for roh in log_lines:
        if roh.startswith("#"):
            continue
        m = ROUND_PREFIX.match(roh)
        text = m.group(2) if m else roh
        rnd = int(m.group(1)) if m else None
        for cat in ROW_CATS:
            mm = PATTERNS[cat].match(text)
            if mm:
                dest = mm.group("dest")
                if dest.startswith("Reihe"):
                    out.append((rnd, mm.group("name"), int(dest.split()[1])))
                break
    return out


class RowStats:
    """Sammelt Reihenwahlen je Quelle/Seite: Gesamt-Histogramm (1..6),
    Histogramm je Runden-Bucket (fruh=R1-2, spaet=R4-5), Partien-/Zug-
    Zaehler."""

    def __init__(self):
        self.hist = Counter()
        self.hist_by_round = defaultdict(Counter)  # round -> Counter(row)
        self.n_moves = 0
        self.n_games = 0

    def add(self, rnd, row):
        self.hist[row] += 1
        if rnd is not None:
            self.hist_by_round[rnd][row] += 1
        self.n_moves += 1

    def summary(self):
        total = sum(self.hist.values())
        kurz = sum(self.hist[r] for r in (1, 2, 3))
        lang = sum(self.hist[r] for r in (4, 5, 6))
        fruh = sum(self.hist_by_round[r][x] for r in (1, 2) for x in range(1, 7))
        spaet = sum(self.hist_by_round[r][x] for r in (4, 5) for x in range(1, 7))
        fruh_kurz = sum(self.hist_by_round[r][x] for r in (1, 2) for x in (1, 2, 3))
        spaet_kurz = sum(self.hist_by_round[r][x] for r in (4, 5) for x in (1, 2, 3))
        return dict(
            n_games=self.n_games,
            n_moves=total,
            row_hist={str(r): self.hist[r] for r in range(1, 7)},
            row_pct={str(r): round(100.0 * self.hist[r] / total, 2) if total else None
                     for r in range(1, 7)},
            share_kurz_1_3=round(100.0 * kurz / total, 2) if total else None,
            share_lang_4_6=round(100.0 * lang / total, 2) if total else None,
            share_kurz_R1_2=round(100.0 * fruh_kurz / fruh, 2) if fruh else None,
            share_kurz_R4_5=round(100.0 * spaet_kurz / spaet, 2) if spaet else None,
            n_moves_R1_2=fruh,
            n_moves_R4_5=spaet,
            row_hist_by_round={
                str(r): {str(x): self.hist_by_round[r][x] for x in range(1, 7)}
                for r in sorted(self.hist_by_round)
            },
        )


def add_arena_source(stats: dict, key: str, path: Path, arm: str | None, side_filter=None):
    """`side_filter(name:str) -> label|None` waehlt/labelt die Seite; `None`
    ueberspringt die Zeile (z.B. wenn eine Quelle nur eine Seite tragen soll)."""
    games = game_list(path, arm)
    seen_games_per_label: dict[str, set] = defaultdict(set)
    for sp in games:
        seed = sp.get("game_seed")
        log = sp.get("log") or []
        for rnd, name, row in row_choices_from_log(log):
            label = side_filter(name)
            if label is None:
                continue
            full_key = f"{key}/{label}"
            st = stats.setdefault(full_key, RowStats())
            st.add(rnd, row)
            seen_games_per_label[full_key].add(seed)
    for full_key, seeds in seen_games_per_label.items():
        stats[full_key].n_games = len(seeds)


def add_heur_pkl_source(stats: dict, key: str, pkl_glob: str):
    files = sorted(glob.glob(pkl_glob))
    st = stats.setdefault(key, RowStats())
    games_seen = set()
    for f in files:
        with open(f, "rb") as fh:
            data = pickle.load(fh)
        by_game = defaultdict(list)
        for rec in data:
            by_game[rec["game_id"]].append(rec)
        for gid, recs in by_game.items():
            games_seen.add(gid)
            # je Runde: Record mit dem laengsten Log (siehe Modul-Doc: Log
            # resettet bei Rundenwechsel, laengster Log = informativster
            # Stand dieser Runde).
            best_by_round: dict[int, list[str]] = {}
            for rec in recs:
                rnd = rec["state"]["round"]
                lg = rec["state"]["log"]
                if rnd not in best_by_round or len(lg) > len(best_by_round[rnd]):
                    best_by_round[rnd] = lg
            for rnd, lg in best_by_round.items():
                for r2, name, row in row_choices_from_log(lg):
                    st.add(r2 if r2 is not None else rnd, row)
    st.n_games = len(games_seen)


def main() -> None:
    stats: dict[str, RowStats] = {}

    # 1) Champion beidseitig (imm_netvnet.json) -- model==model_b PRUEFEN.
    p1 = EVAL / "paired_arena_env_imm_netvnet.json"
    d1 = json.load(open(p1, encoding="utf-8"))
    assert d1["model"] == d1["model_b"], (
        f"{p1.name}: model != model_b ({d1['model']} vs {d1['model_b']}) -- "
        f"Quelle ist NICHT Champion-beidseitig, Annahme im Docstring falsch."
    )
    add_arena_source(stats, "champion_selfplay_both_sides", p1, arm=None,
                      side_filter=lambda n: "Champion")

    # 2) Champion (Netz) vs Heuristik, zwei Arme (0 / 0.2), kombiniert +
    #    einzeln.
    p2 = EVAL / "paired_arena_env_imm_a02.json"
    for arm in ("0", "0.2"):
        add_arena_source(stats, f"champion_vs_heuristik_arm{arm}", p2, arm=arm,
                          side_filter=lambda n: "Champion" if n == "Netz" else
                          ("Heuristik" if n == "Heuristik" else None))
    add_arena_source(stats, "champion_vs_heuristik_combined", p2, arm="0",
                      side_filter=lambda n: "Champion" if n == "Netz" else
                      ("Heuristik" if n == "Heuristik" else None))
    add_arena_source(stats, "champion_vs_heuristik_combined", p2, arm="0.2",
                      side_filter=lambda n: "Champion" if n == "Netz" else
                      ("Heuristik" if n == "Heuristik" else None))

    # 3) seedk1 (NetzA) vs Champion (NetzB).
    p3 = EVAL / "paired_arena_env_seedk1_nullarm.json"
    d3 = json.load(open(p3, encoding="utf-8"))
    assert "seedk1" in d3["model"] and "seedk1" not in d3["model_b"], (
        f"{p3.name}: erwartete Anordnung NetzA=seedk1 NetzB=Champion nicht "
        f"bestaetigt (model={d3['model']}, model_b={d3['model_b']})"
    )
    add_arena_source(stats, "seedk1_vs_champion", p3, arm=None,
                      side_filter=lambda n: "seedk1" if n == "NetzA" else
                      ("Champion" if n == "NetzB" else None))

    # 4) Heuristik-Selbstspiel ("Bauer") aus data/holdout/.
    add_heur_pkl_source(stats, "heuristik_selfplay_bauer",
                         str(ROOT / "data" / "holdout" / "selfplay_hold_heur_*.pkl"))

    out = {k: v.summary() for k, v in sorted(stats.items())}
    out["_meta"] = dict(
        row_note="Reihe = Musterreihe (Draft-Zielreihe, Kapazitaet 1..6); "
                 "docs/engine_manual.md Abschnitt 4 Phase 2: Musterreihe N "
                 "speist Kuppel-Zeile N 1:1.",
        heur_pkl_limitation="state.log je Record ist nur der Log der laufenden "
                             "Runde (Reset bei Rundenwechsel); je Runde wird der "
                             "laengste verfuegbare Log-Stand verwendet, die "
                             "jeweils letzte Aktion der Runde fehlt.",
    )
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"geschrieben: {OUT_JSON}\n")
    hdr = f"{'Quelle/Seite':<42}{'n_Partien':>10}{'n_Zuege':>9}" + \
          "".join(f"{'R'+str(r):>7}" for r in range(1, 7)) + \
          f"{'kurz%':>8}{'lang%':>8}{'kurzR12%':>10}{'kurzR45%':>10}"
    print(hdr)
    print("-" * len(hdr))
    for k, v in out.items():
        if k == "_meta":
            continue
        pct = v["row_pct"]
        line = f"{k:<42}{v['n_games']:>10}{v['n_moves']:>9}" + \
               "".join(f"{(pct[str(r)] or 0):>6.1f}%" for r in range(1, 7)) + \
               f"{(v['share_kurz_1_3'] or 0):>7.1f}%{(v['share_lang_4_6'] or 0):>7.1f}%" + \
               f"{(v['share_kurz_R1_2'] or 0):>9.1f}%{(v['share_kurz_R4_5'] or 0):>9.1f}%"
        print(line)


if __name__ == "__main__":
    main()
