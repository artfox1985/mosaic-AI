# -*- coding: utf-8 -*-
"""Arm-P-Sperre aus PREREG_reachability_target.md par.12: spreizt der Puffer?

Arm P ersetzt das boolesche Vollendbarkeits-Label in Runde 1-2 durch einen
stetigen VORRATSPUFFER: je offener Normal-Zelle die Zahl der noch erreichbaren
Kopien der geforderten Farbe MINUS dem Bedarf, ueber die Spalte zum Minimum
zusammengefasst (die bindende Zelle bestimmt die Spalte). Zellen ohne
Farbforderung (wild/special/leerer Kuppelplatz) binden nicht.

VORAB-REGEL par.12: der Puffer muss in Runde 1 UND 2 eine Standardabweichung
ueber die 6 Spalten-Atome von > 0 in mindestens 80 % der Stellungen aufweisen,
und der Median darf nicht am Rand der Stauchung liegen (nicht in den obersten
oder untersten 5 % des Wertebereichs). Sonst wird Arm P NICHT gebaut.

Die Stauchung ist ein vorab festzulegender Freiheitsgrad (par.12); diese Sonde
rechnet die Regel fuer eine kleine Kappungs-Kandidatenliste durch
(`squash(b) = clip(b, 0, CAP) / CAP`, b < 0 -> 0 = unvollendbar; Spalte ohne
bindende Zelle -> 1,0). Die getroffene Wahl gehoert in par.12 nachgetragen.

HANDPROBE (par.12, vor der Sperre): einige Runde-1/2-Stellungen mit Fuellstand
und Roh-Puffer je Spalte ausdrucken -- der billige Schutz gegen Vorzeichen-
oder Normierungsfehler, den die Sperre selbst nicht faende.

Anordnung wie par.5/par.10: `data/holdout`, Tiling-Stellungen, je
(Partie, Runde) eine, 150 je Runde. Quelle: `mosaic_rust.
plate_completability_json` (Feld `col_open_cells`, Puffer aus
`provocation::noch_erreichbare_farben` -- nur beobachtbare Information).

    python -X utf8 tools/probes/reachability_buffer_spread.py
"""
from __future__ import annotations

import argparse
import glob
import json
import pickle
import statistics
from collections import defaultdict
from pathlib import Path

BASIS = Path(__file__).resolve().parents[2]

CAP_KANDIDATEN = [4, 8, 12, 16]


def spalten_puffer(d: dict) -> list[float | None]:
    """Bindender Roh-Puffer je Spalte; None = keine bindende Zelle."""
    out: list[float | None] = []
    for zellen in d["col_open_cells"]:
        werte = [z["buffer"] for z in zellen if z.get("kind") == "normal"]
        out.append(min(werte) if werte else None)
    return out


def squash(b: float | None, cap: float) -> float:
    if b is None:
        return 1.0
    return max(0.0, min(float(b), cap)) / cap


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--states", default="data/holdout/*.pkl")
    ap.add_argument("--n-per-round", type=int, default=150)
    ap.add_argument("--phase", default="tiling")
    ap.add_argument("--handprobe", type=int, default=25)
    a = ap.parse_args()

    import mosaic_rust as mr  # noqa: PLC0415

    je_runde: dict = defaultdict(list)   # Runde -> Liste von (puffer[6], fill[6], columns[6])
    gesehen: dict = {}
    genug: dict = defaultdict(int)
    parität_bruch = 0
    for f in sorted(glob.glob(str(BASIS / a.states))):
        try:
            data = pickle.load(open(f, "rb"))
        except Exception:  # noqa: BLE001
            continue
        for s in data:
            st = s.get("state") or {}
            if st.get("phase") != a.phase:
                continue
            rd = int(st.get("round") or 0)
            if not 1 <= rd <= 5 or genug[rd] >= a.n_per_round:
                continue
            g = (f, s.get("game_id"), rd)
            if gesehen.get(g):
                continue
            gesehen[g] = True
            pi = st.get("current_player", 0)
            try:
                d = json.loads(mr.plate_completability_json(json.dumps(st), pi))
            except Exception:  # noqa: BLE001
                continue
            genug[rd] += 1
            puf = spalten_puffer(d)
            # Selbsttest: Puffer-Vorzeichen gegen das boolesche Praedikat --
            # `columns[c]` muss genau dann False sein, wenn eine bindende
            # Zelle negativen Puffer hat.
            for c in range(6):
                erwartet = puf[c] is None or puf[c] >= 0
                if bool(d["columns"][c]) != erwartet:
                    parität_bruch += 1
            je_runde[rd].append((puf, d["col_fill"], d["columns"]))
        if all(genug[r] >= a.n_per_round for r in range(1, 6)):
            break

    print(f"  Phase '{a.phase}', je (Partie, Runde) eine Stellung; "
          f"Paritaets-Selbsttest Puffer<->Boolean: {parität_bruch} Brueche\n")

    # ── Handprobe ────────────────────────────────────────────────────────────
    print(f"  HANDPROBE ({a.handprobe} Stellungen aus Runde 1-2): Fuellstand -> Roh-Puffer je Spalte")
    gezeigt = 0
    for rd in (1, 2):
        for puf, fill, _cols in je_runde[rd]:
            if gezeigt >= a.handprobe:
                break
            paare = " ".join(
                f"{fill[c]}/{'-' if puf[c] is None else int(puf[c])}" for c in range(6))
            print(f"    R{rd}  fill/puffer: {paare}")
            gezeigt += 1

    # ── Roh-Verteilung je Runde ──────────────────────────────────────────────
    print("\n  Runde |   n | bindende Spalten je Stellung | Roh-Puffer p10/Median/p90")
    print("  ------+-----+------------------------------+--------------------------")
    roh = {}
    for rd in sorted(je_runde):
        alle = [b for puf, _f, _c in je_runde[rd] for b in puf if b is not None]
        bindend = [sum(1 for b in puf if b is not None) for puf, _f, _c in je_runde[rd]]
        if not alle:
            continue
        xs = sorted(alle)
        p10, med, p90 = xs[int(0.1 * len(xs))], statistics.median(xs), xs[min(len(xs) - 1, int(0.9 * len(xs)))]
        roh[rd] = {"n": len(je_runde[rd]), "p10": p10, "median": med, "p90": p90,
                   "bindend_mittel": statistics.mean(bindend)}
        print(f"  {rd:5} | {len(je_runde[rd]):3} | {statistics.mean(bindend):28.2f} | "
              f"{p10:5.1f} / {med:5.1f} / {p90:5.1f}")

    # ── Sperre je Kappungs-Kandidat ──────────────────────────────────────────
    print("\n  Sperre par.12 (Runde 1 UND 2: std ueber 6 Atome > 0 in >= 80 %, "
          "Median nicht in den aeussersten 5 % des Wertebereichs):")
    print("\n  CAP | R | std>0-Anteil | Median (gestaucht) | im Band [0,05, 0,95] | Sperre")
    print("  ----+---+--------------+--------------------+----------------------+-------")
    ergebnis = {"roh": roh, "paritaet_brueche": parität_bruch, "kandidaten": {}}
    for cap in CAP_KANDIDATEN:
        je_cap = {}
        for rd in (1, 2):
            std_pos = 0
            mediane = []
            for puf, _f, _c in je_runde[rd]:
                werte = [squash(b, cap) for b in puf]
                if statistics.pstdev(werte) > 0:
                    std_pos += 1
                mediane.append(statistics.median(werte))
            n = max(len(je_runde[rd]), 1)
            anteil = std_pos / n
            med = statistics.median(mediane) if mediane else float("nan")
            im_band = 0.05 <= med <= 0.95
            je_cap[rd] = {"std_pos_anteil": anteil, "median_gestaucht": med, "im_band": im_band}
            print(f"  {cap:3} | {rd} | {100*anteil:11.1f}% | {med:18.3f} | "
                  f"{'ja' if im_band else 'NEIN':>20} |", end="")
            print(" --" if rd == 1 else
                  ("  BESTANDEN" if all(v["std_pos_anteil"] >= 0.8 and v["im_band"]
                                        for v in je_cap.values()) else "  nicht bestanden"))
        ergebnis["kandidaten"][cap] = {
            "je_runde": je_cap,
            "bestanden": all(v["std_pos_anteil"] >= 0.8 and v["im_band"] for v in je_cap.values()),
        }

    (BASIS / "evaluations" / "probe_reachability_buffer_spread.json").write_text(
        json.dumps({"states": a.states, "phase": a.phase, **ergebnis},
                   indent=1, ensure_ascii=False), encoding="utf-8")
    print("\n  geschrieben: evaluations/probe_reachability_buffer_spread.json")


if __name__ == "__main__":
    main()
