#!/usr/bin/env python
"""PREREG_heuristic_v2_long_rows.md par.5.3 (Messkette Schritt 3):
Champion gegen HEURISTIK V2.

Frage laut Prereg: "ist v2 als LEHRER stark genug, um ein brauchbares Korpus
zu erzeugen?" Ein Lehrer, der lange Reihen kann und dabei deutlich schwaecher
ist, erzeugt ein Korpus, das die Zielfaehigkeit traegt und das Niveau senkt.

**Kein vorregistrierter Schwellenwert.** Die Prereg beschreibt eine Abwaegung,
keinen Schnitt (dort 2026-08-24 ausdruecklich nachgetragen). Diese Sonde
liefert die Zahlen, das Urteil faellt danach.

Ausgewiesen (par.5.5): Vollendungsquote, Initiierungsrate und die sechs
Standard-Kennzahlen je Seite (CLAUDE.md), Auswertung auf BLOCK-Ebene.

Als Bezug laeuft derselbe Lauf mit v1 (`net_arena_match`) auf DENSELBEN Seeds
-- sonst waere "v2 verliert X" nicht von "die Heuristik verliert ohnehin X"
zu trennen.
"""
from __future__ import annotations

import json
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "engine" / "py"))
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "probes"))

import mosaic_rust as mr  # noqa: E402
from analyze_game_log import PATTERNS, ROUND_PREFIX  # noqa: E402
from column_build_structural_probe import (  # noqa: E402
    rekonstruiere_partie,
    spalten_fuellung,
    struktur_kennzahlen,
)
from plate_points_from_arena import block_mittel, t_wert  # noqa: E402

MODELL = str(ROOT / "models" / "alphazero_v21_2d_brierbest.onnx")
SEEDS_DATEI = ROOT / "evaluations" / "kampagnen_seeds_407.txt"
OUT_JSON = ROOT / "evaluations" / "v2_teacher_arena.json"
NET_SIMS, HEUR_SIMS, THREADS, BLOCK = 400, 150, 0, 25
K1_TILE_ID = 1
TAKE_CATS = ("SUN_TAKE", "MOON_GLOBAL_TAKE")


def seiten_kennzahlen(sp, i):
    """Alle Kennzahlen EINER Partie-Seite (Brett `i`)."""
    name = sp["names"][i]
    log = sp.get("log") or []

    punkte = sp["scores"][i]
    marge = punkte - sp["scores"][1 - i]

    reihen = Counter()
    strafpunkte = straf_ziele = ueberlauf = 0
    for roh in log:
        if roh.startswith("#"):
            continue
        m = ROUND_PREFIX.match(roh)
        text = m.group(2) if m else roh
        mm = PATTERNS["ROUND_STRAFE"].match(text)
        if mm and mm.group("name") == name:
            strafpunkte += abs(int(mm.group("pen")))
            continue
        for cat in TAKE_CATS:
            mm = PATTERNS[cat].match(text)
            if not mm or mm.group("name") != name:
                continue
            dest = mm.group("dest")
            if dest.startswith("Reihe"):
                reihen[int(dest.split()[1])] += 1
            else:
                straf_ziele += 1
            ov = mm.group("overflow")
            if ov:
                ueberlauf += int(ov)
            break

    zellen = rekonstruiere_partie(log).get(name, set())
    kz = struktur_kennzahlen(spalten_fuellung(zellen))
    zeilen_fill = [0] * 6
    for (tr, _tc, si) in zellen:
        zeilen_fill[2 * tr + si // 2] += 1

    return dict(
        punkte=punkte, marge=marge, sieg=1 if sp["winner"] == i else 0,
        strafpunkte=strafpunkte, straf_ziele=straf_ziele, ueberlauf_steine=ueberlauf,
        reihen_kurz_1_3=sum(reihen[r] for r in (1, 2, 3)),
        reihen_lang_4_6=sum(reihen[r] for r in (4, 5, 6)),
        volle_spalten=kz["volle_spalten"], max_spaltenhoehe=kz["max_hoehe"],
        teilspalten_ge4=kz["teilspalten_ge4"],
        volle_zeilen=sum(1 for f in zeilen_fill if f == 6),
        k1_aktiv=K1_TILE_ID in (sp.get("scoring_tile_ids") or []),
        lr_started=sp["long_rows_started"][i],
        lr_completed=sp["long_rows_completed"][i],
        lr_cleared=sp["long_rows_cleared_unplaceable"][i],
    )


SKALARE = ["punkte", "marge", "sieg", "strafpunkte", "straf_ziele", "ueberlauf_steine",
           "reihen_kurz_1_3", "reihen_lang_4_6", "volle_spalten", "max_spaltenhoehe",
           "teilspalten_ge4", "volle_zeilen", "lr_started", "lr_completed", "lr_cleared"]


def mittel(v):
    return round(statistics.mean(v), 4) if v else None


def gepaart(diffs):
    """Block-Ebene: erst Blockmittel in Laufreihenfolge, dann t.

    Stehende Regel seit 2026-08-04: auf Partie-Ebene sind die Paar-SEs massiv
    unterschaetzt, weil die Partien eines Blocks korreliert sind.
    """
    if len(diffs) < 2:
        return None
    bl = block_mittel(diffs, BLOCK)
    if len(bl) < 2:
        return None
    m, tv = t_wert(bl)
    return dict(n_partien=len(diffs), n_bloecke=len(bl), mittel=round(m, 4), t=round(tv, 2))


def lauf(fn, seeds, label):
    print("  " + label + " ...", file=sys.stderr, flush=True)
    roh = fn(MODELL, net_sims=NET_SIMS, heur_sims=HEUR_SIMS, n_games=len(seeds),
             seed=0, num_threads=THREADS, log_games=True, seeds=seeds)
    return json.loads(roh)


def auswerten(spiele, heur_label):
    netz, heur = [], []
    for sp in spiele:
        nb = sp["net_board"]
        netz.append(seiten_kennzahlen(sp, nb))
        heur.append(seiten_kennzahlen(sp, 1 - nb))
    out = {
        "n_partien": len(spiele),
        "Netz": {k: mittel([x[k] for x in netz]) for k in SKALARE},
        heur_label: {k: mittel([x[k] for x in heur]) for k in SKALARE},
        "gepaart_heur_minus_netz": {
            k: gepaart([h[k] - n[k] for h, n in zip(heur, netz)]) for k in SKALARE
        },
    }
    for label, seiten in (("Netz", netz), (heur_label, heur)):
        s = sum(x["lr_started"] for x in seiten)
        c = sum(x["lr_completed"] for x in seiten)
        out[label]["vollendungsquote"] = round(c / s, 4) if s else None
        akt = [x for x in seiten if x["k1_aktiv"]]
        out[label]["volle_spalten_bei_k1_aktiv"] = mittel([x["volle_spalten"] for x in akt])
        out[label]["n_k1_aktiv"] = len(akt)
    return out


def main():
    seeds = [int(z) for z in SEEDS_DATEI.read_text().split() if z.strip()]
    print("%d Kampagnen-Seeds, Netz@%d gegen Heuristik@%d"
          % (len(seeds), NET_SIMS, HEUR_SIMS), file=sys.stderr, flush=True)

    v2 = auswerten(lauf(mr.net_vs_heuristic_v2_arena, seeds, "v2 als Lehrer"), "HeuristikV2")
    v1 = auswerten(lauf(mr.net_arena_match, seeds, "v1 als Bezug (dieselben Seeds)"), "HeuristikV1")

    ergebnis = {"v2_lauf": v2, "v1_bezug": v1,
                "hinweis": ("Kein vorregistrierter Schwellenwert fuer par.5.3 -- die Prereg "
                            "beschreibt eine Abwaegung. Diese Zahlen sind die Grundlage, "
                            "nicht das Urteil.")}
    OUT_JSON.write_text(json.dumps(ergebnis, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n=== Schritt 3: v2 als Lehrer (%d Partien) ===" % v2["n_partien"])
    for label, daten, hk in (("v2", v2, "HeuristikV2"), ("v1 (Bezug)", v1, "HeuristikV1")):
        h, n = daten[hk], daten["Netz"]
        print("\n  %s: Heuristik-Seite gegen Champion" % label)
        print("    Siege Heuristik %.3f   Punkte %.1f gegen %.1f   Marge %+.1f"
              % (h["sieg"], h["punkte"], n["punkte"], h["marge"]))
        print("    volle SPALTEN %.3f (Netz %.3f)   bei k1 aktiv %.3f   n=%d"
              % (h["volle_spalten"], n["volle_spalten"],
                 h["volle_spalten_bei_k1_aktiv"], h["n_k1_aktiv"]))
        print("    volle ZEILEN %.3f   maxHoehe %.2f   Vollendungsquote %s"
              % (h["volle_zeilen"], h["max_spaltenhoehe"], h["vollendungsquote"]))
        print("    Strafpunkte %.1f   Reihen lang %.2f   kurz %.2f"
              % (h["strafpunkte"], h["reihen_lang_4_6"], h["reihen_kurz_1_3"]))
    print("\n  gepaart (Heuristik minus Netz, Block-Ebene) im v2-Lauf:")
    for k in ("punkte", "sieg", "volle_spalten", "volle_zeilen", "strafpunkte"):
        g = v2["gepaart_heur_minus_netz"][k]
        if g:
            print("    %-16s %+8.3f  t=%+6.2f  (%d Bloecke)"
                  % (k, g["mittel"], g["t"], g["n_bloecke"]))
    print("\n-> " + str(OUT_JSON))


if __name__ == "__main__":
    main()
