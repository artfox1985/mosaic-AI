#!/usr/bin/env python
"""PREREG_long_row_payoff.md par.2a: Reihen-INITIIERUNG gegen -FORTSETZUNG.

Offene Spannung nach der Nacht vom 2026-08-23/24:

  - `row_preference_probe.py` vergleicht GESPIELTE Zuege beider Agenten und
    findet einen klaren Unterschied: Champion 55,5-56,1 % kurze Reihen,
    FLACH ueber alle Runden; Heuristik-Lehrer 46,0 % (R1-2) auf 33,4 %
    (R4-5), adaptiert also spaet.
  - `long_row_prior_gate.py` (par.2) misst PRIOR-Masse des Champions auf
    einer engeren Klasse -- Fortsetzung einer bereits begonnenen langen
    Reihe -- und findet dort Verhaeltnis ~0,22.

Beides ist vereinbar, wenn der Agentenunterschied im BEGINNEN langer
Reihen liegt statt im FORTSETZEN. Diese Sonde prueft genau das, und zwar
an GESPIELTEN Zuegen beider Agenten (nicht an Prior-Masse eines Netzes) --
der Fehler der ersten par.2-Deutung war, zwei Champion-Spalten fuer einen
Agentenvergleich zu halten.

Klassifikation je Stein-Zug, rein aus dem Log, ohne Zustands-Rekonstruktion:
`[f/c]` gibt den Fuellstand NACH dem Zug, `n×` die Entnahmegroesse,
`(+N Strafleiste)` den Ueberlauf. Daraus:

    platziert    = n - overflow
    fill_vorher  = fill_nachher - platziert
    INITIIERUNG  <=> fill_vorher == 0

Gegenprobe an echten Zeilen beim Bau: `n=4 dest=Reihe 3 fill=3 overflow=1`
-> platziert 3, vorher 0 -> Initiierung. `n=1 dest=Reihe 2 fill=2` ->
platziert 1, vorher 1 -> Fortsetzung.

Quelle: `paired_arena_env_imm_a02.json` (Champion und Heuristik in DENSELBEN
Partien auf denselben Seeds -- der einzige saubere Agentenvergleich im
Bestand) plus `imm_netvnet`/`_swap` als Netz-gegen-Netz-Kontext.

Auswertung auf BLOCK-Ebene (je Partie), Bootstrap ueber Partien.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from analyze_game_log import PATTERNS, ROUND_PREFIX  # noqa: E402
from plate_points_from_arena import partien  # noqa: E402

EVAL = ROOT / "evaluations"
OUT_JSON = EVAL / "row_initiation_probe.json"

TAKE_CATS = ("SUN_TAKE", "MOON_GLOBAL_TAKE")
LONG_ROWS = (5, 6)
SHORT_ROWS = (1, 2, 3)
RNG = np.random.default_rng(20260824)
N_BOOT = 1000


def classify_moves(log_lines):
    """[(runde, name, reihe, ist_initiierung)] je Musterreihen-Zug."""
    out = []
    for roh in log_lines:
        if roh.startswith("#"):
            continue
        m = ROUND_PREFIX.match(roh)
        text = m.group(2) if m else roh
        rnd = int(m.group(1)) if m else None
        for cat in TAKE_CATS:
            mm = PATTERNS[cat].match(text)
            if not mm:
                continue
            dest = mm.group("dest")
            if not dest.startswith("Reihe"):
                break  # Strafleisten-Ziel: keine Reihenwahl
            fill = mm.group("fill")
            if fill is None:
                break  # ohne Fuellstand nicht klassifizierbar
            n = int(mm.group("n"))
            overflow = int(mm.group("overflow") or 0)
            platziert = n - overflow
            fill_vorher = int(fill) - platziert
            out.append((rnd, mm.group("name"), int(dest.split()[1]),
                        fill_vorher == 0, fill_vorher))
            break
    return out


class SideStats:
    def __init__(self):
        self.per_game = defaultdict(lambda: defaultdict(int))

    def add(self, seed, rnd, row, is_init):
        g = self.per_game[seed]
        bucket = "lang" if row in LONG_ROWS else ("kurz" if row in SHORT_ROWS else "mitte")
        kind = "init" if is_init else "fort"
        g[f"{bucket}_{kind}"] += 1
        g["alle"] += 1
        if is_init:
            g["init_alle"] += 1
        if rnd is not None:
            # Sowohl die Bucket-Sicht (vergleichbar mit row_preference_probe)
            # ALS AUCH je Einzelrunde -- der R3-Einbruch beim ersten Lauf
            # verlangt die feinere Aufloesung.
            rb = "R1_2" if rnd <= 2 else ("R4_5" if rnd >= 4 else "R3")
            for key in (rb, f"R{rnd}"):
                g[f"{key}_{bucket}_{kind}"] += 1
                if is_init:
                    g[f"{key}_init_alle"] += 1

    def totals(self, keys):
        return {k: sum(g.get(k, 0) for g in self.per_game.values()) for k in keys}

    def n_games(self):
        return len(self.per_game)


def share_of_initiations_to_long(stats, prefix=""):
    p = f"{prefix}_" if prefix else ""
    t = stats.totals([f"{p}lang_init", f"{p}init_alle"])
    lang, alle = t[f"{p}lang_init"], t[f"{p}init_alle"]
    return (lang / alle if alle else None), lang, alle


def bootstrap_share(stats, prefix=""):
    p = f"{prefix}_" if prefix else ""
    games = list(stats.per_game.values())
    if len(games) < 10:
        return None
    idx = np.arange(len(games))
    vals = []
    for _ in range(N_BOOT):
        pick = RNG.choice(idx, size=len(idx), replace=True)
        lang = sum(games[i].get(f"{p}lang_init", 0) for i in pick)
        alle = sum(games[i].get(f"{p}init_alle", 0) for i in pick)
        if alle > 0:
            vals.append(lang / alle)
    if not vals:
        return None
    a = np.array(vals)
    return dict(mean=round(float(a.mean()), 4), p2_5=round(float(np.percentile(a, 2.5)), 4),
                p97_5=round(float(np.percentile(a, 97.5)), 4), n_boot=len(a))


def collect(path, arm, side_filter):
    stats = defaultdict(SideStats)
    for sp in partien(path, arm):
        seed = sp.get("game_seed")
        for rnd, name, row, is_init, _fv in classify_moves(sp.get("log") or []):
            lab = side_filter(name)
            if lab is not None:
                stats[lab].add(seed, rnd, row, is_init)
    return stats


def paired_delta(stats_a, stats_b, prefix=""):
    """Gepaarte Differenz (A minus B) des Anteils Initiierung->lang JE PARTIE,
    ueber gemeinsame Seeds. Nur moeglich, wenn beide Seiten in denselben
    Partien spielen (imm_a02: Netz gegen Heuristik)."""
    p = f"{prefix}_" if prefix else ""
    seeds = sorted(set(stats_a.per_game) & set(stats_b.per_game))
    diffs = []
    for s in seeds:
        ga, gb = stats_a.per_game[s], stats_b.per_game[s]
        aa, ab = ga.get(f"{p}init_alle", 0), gb.get(f"{p}init_alle", 0)
        if aa == 0 or ab == 0:
            continue
        diffs.append(ga.get(f"{p}lang_init", 0) / aa - gb.get(f"{p}lang_init", 0) / ab)
    if len(diffs) < 10:
        return dict(n_paare=len(diffs), hinweis="zu wenige verwertbare Paare")
    d = np.array(diffs)
    se = d.std(ddof=1) / np.sqrt(len(d))
    return dict(n_paare=len(d), mittel=round(float(d.mean()), 4),
                sd=round(float(d.std(ddof=1)), 4), se=round(float(se), 4),
                t=round(float(d.mean() / se), 2) if se > 0 else None)


def summarize(stats):
    out = dict(n_partien=stats.n_games())
    for prefix, label in (("", "gesamt"), ("R1_2", "R1_2"), ("R3", "R3"), ("R4_5", "R4_5"),
                          ("R1", "R1"), ("R2", "R2"), ("R4", "R4"), ("R5", "R5")):
        share, lang, alle = share_of_initiations_to_long(stats, prefix)
        t = stats.totals([f"{prefix + '_' if prefix else ''}{b}_{k}"
                          for b in ("lang", "kurz", "mitte") for k in ("init", "fort")])
        out[label] = dict(
            anteil_initiierungen_in_lange_reihe=round(share, 4) if share is not None else None,
            n_initiierungen_lang=lang, n_initiierungen_gesamt=alle,
            bootstrap_95ci=bootstrap_share(stats, prefix),
            rohzaehler={k.replace(f"{prefix}_", "") if prefix else k: v for k, v in t.items()},
        )
    return out


def main():
    result = {}

    p_a02 = EVAL / "paired_arena_env_imm_a02.json"
    for arm in ("0", "0.2"):
        st = collect(p_a02, arm,
                     lambda n: "Champion" if n == "Netz" else
                     ("Heuristik" if n == "Heuristik" else None))
        block = {lab: summarize(s) for lab, s in st.items()}
        if "Champion" in st and "Heuristik" in st:
            block["_gepaart_Champion_minus_Heuristik"] = {
                lbl: paired_delta(st["Champion"], st["Heuristik"], pre)
                for pre, lbl in (("", "gesamt"), ("R1_2", "R1_2"), ("R3", "R3"),
                                 ("R4_5", "R4_5"), ("R1", "R1"), ("R2", "R2"),
                                 ("R4", "R4"), ("R5", "R5"))
            }
        result[f"champion_vs_heuristik_arm{arm}"] = block

    for fname, key in (("paired_arena_env_imm_netvnet.json", "netvnet"),
                       ("paired_arena_env_imm_netvnet_swap.json", "netvnet_swap")):
        p = EVAL / fname
        if not p.exists():
            continue
        d = json.load(open(p, encoding="utf-8"))

        def lab_of(spec):
            s = str(spec)
            return "alpha0.2" if "imm_a02" in s else ("frozen" if "frozen" in s else f"?{s}")

        la, lb = lab_of(d["spec_a"]), lab_of(d["spec_b"])
        st = collect(p, None, lambda n, a=la, b=lb: a if n == "NetzA" else (b if n == "NetzB" else None))
        result[key] = {lab: summarize(s) for lab, s in st.items()}

    result["_meta"] = dict(
        frage="Liegt der Agenten-Unterschied bei langen Reihen im BEGINNEN "
              "oder im FORTSETZEN? Bezugswerte row_preference_probe: Champion "
              "55,5-56,1 % kurz FLACH, Heuristik 46,0 % (R1-2) auf 33,4 % (R4-5).",
        klassifikation="fill_vorher = fill_nachher - (n - overflow); "
                       "Initiierung <=> fill_vorher == 0. Rein aus dem Log, "
                       "keine Zustands-Rekonstruktion.",
        ebene="Block-Ebene (je Partie), Bootstrap ueber Partien",
    )
    OUT_JSON.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    buckets = ("gesamt", "R1", "R2", "R3", "R4", "R5")
    print(f"{'Quelle/Seite':38s} " + " ".join(f"{b:>7s}" for b in buckets))
    for src in sorted(k for k in result if k != "_meta"):
        for lab in sorted(k for k in result[src] if not k.startswith("_")):
            cells = []
            for b in buckets:
                s = result[src][lab][b]["anteil_initiierungen_in_lange_reihe"]
                cells.append(f"{s:.1%}" if s is not None else "-")
            print(f"{src + '/' + lab:38s} " + " ".join(f"{c:>7s}" for c in cells))
        gp = result[src].get("_gepaart_Champion_minus_Heuristik")
        if gp:
            cells = []
            for b in buckets:
                v = gp[b]
                cells.append(f"{v['mittel']:+.3f}" if "mittel" in v else "-")
            print(f"{src + '/GEPAART (C-H)':38s} " + " ".join(f"{c:>7s}" for c in cells))
            cells = []
            for b in buckets:
                v = gp[b]
                cells.append(f"t={v['t']:+.1f}" if v.get("t") is not None else "-")
            print(f"{'':38s} " + " ".join(f"{c:>7s}" for c in cells))
    print(f"\n-> {OUT_JSON}")


if __name__ == "__main__":
    main()
