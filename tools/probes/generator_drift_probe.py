# -*- coding: utf-8 -*-
"""Wie gross ist die Erzeuger-Drift? (PREREG_generator_drift.md)

Der heutige Build reproduziert den v22-Korpus nachweislich nicht (STATUS.md
1c). Diese Sonde misst, ob er deshalb ein MATERIELL anderer Spieler ist --
schrittverschieden und verhaltensgleich schliessen sich nicht aus.

GEPAART AUF BLOCK-EBENE. Beide Arme laufen mit demselben Seed (20260826) und
demselben Chunk-Zuschnitt, Datei k des einen entspricht also Datei k des
anderen. Verglichen werden Datei-MITTEL, nicht Einzelpartien: auf Partie-Ebene
sind die Paar-SEs massiv unterschaetzt (stehende Regel seit 2026-08-04).

AEQUIVALENZ, NICHT NULLHYPOTHESE. "Nicht signifikant verschieden" waere kein
Beleg fuer Gleichheit -- bei zu wenig Partien bekommt man ihn geschenkt.
Geprueft wird deshalb, ob das 95%-KI der Differenz VOLLSTAENDIG innerhalb der
vorregistrierten Grenze liegt (par.4).

Die Kennzahl-Extraktion spiegelt `tools/corpus_sanity_check.py` Feld fuer Feld
(`state.players[].score_geo`, `scores`, `floor` je Runde). Wer sie hier
aendert, muss sie dort mitziehen -- sonst vergleichen die beiden Werkzeuge
verschiedene Dinge unter demselben Namen.

Aufruf:
    python -X utf8 -u tools/probes/generator_drift_probe.py \\
        --korpus data --neu <dir> --n-dateien 100
"""
import argparse
import glob
import json
import math
import os
import pathlib
import statistics as st
import sys
import time

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

from corpus_io import load_records  # noqa: E402

# Vorregistrierte Grenze (PREREG_generator_drift.md par.4). Steht als
# Konstante hier, damit sie nicht in der Auswertung "nachgeschaerft" wird.
AEQUIVALENZGRENZE = 0.10
ENTSCHEIDUNGSMASS = "volle_spalten"
# par.4 Waechter: die uebrigen Kennzahlen duerfen nicht um mehr als diesen
# Anteil ihres Korpus-Werts auseinanderlaufen.
WAECHTER_ANTEIL = 0.10


def _blockwerte(path):
    """Kennzahlen EINER Korpusdatei, je Seite gemittelt.

    Spiegelt `corpus_sanity_check.auswerten`: Endzustand ist der Record mit
    gesetztem `winner`, die Strafleiste wird als groesste Laenge JE RUNDE
    aufsummiert (nicht als Endstand -- sie wird zwischendurch geleert).
    """
    last, floor_max = {}, {}
    for r in load_records(path):
        gid = r.get("game_id")
        stt = r.get("state") or {}
        for pi, p in enumerate(stt.get("players", [])):
            k = (gid, pi, stt.get("round"))
            floor_max[k] = max(floor_max.get(k, 0), len(p.get("floor") or []))
        if r.get("winner") is not None:
            last[gid] = r
    floor_je_seite = {}
    for (g, pi_, _r), v in floor_max.items():
        floor_je_seite[(g, pi_)] = floor_je_seite.get((g, pi_), 0) + v

    aus = {k: [] for k in ("volle_spalten", "volle_reihen", "reihen_fuellstand",
                           "teilspalten_ge3", "teilspalten_ge4", "max_hoehe",
                           "strafsteine", "punkte", "margin")}
    platten = {}
    for gid, r in last.items():
        stt = r["state"]
        ids = stt.get("scoring_tile_ids") or []
        sc = r.get("scores") or [p.get("score") for p in stt["players"]]
        for pi, p in enumerate(stt["players"]):
            g = p.get("score_geo") or {}
            rf, cf = g.get("row_fill") or [], g.get("col_fill") or []
            aus["volle_reihen"].append(sum(1 for x in rf if x >= 6))
            aus["reihen_fuellstand"].append(sum(rf) / len(rf) if rf else 0.0)
            aus["volle_spalten"].append(sum(1 for x in cf if x >= 6))
            aus["teilspalten_ge4"].append(sum(1 for x in cf if x >= 4))
            aus["teilspalten_ge3"].append(sum(1 for x in cf if x >= 3))
            aus["max_hoehe"].append(max(cf) if cf else 0)
            aus["strafsteine"].append(floor_je_seite.get((gid, pi), 0))
            aus["punkte"].append(sc[pi])
            aus["margin"].append(sc[pi] - sc[1 - pi])
            stp = p.get("scoring_tile_points") or []
            for i in ids:
                if i < len(stp):
                    platten.setdefault(f"platte_k{i}", []).append(stp[i])
    mittel = {k: (sum(v) / len(v) if v else float("nan")) for k, v in aus.items()}
    for k, v in platten.items():
        mittel[k] = sum(v) / len(v) if v else float("nan")
    mittel["_partien"] = len(last)
    return mittel


def _ki95(werte):
    """Mittel und halbe 95%-KI-Breite einer Differenzreihe."""
    if len(werte) < 2:
        return (werte[0] if werte else float("nan")), float("nan")
    m = st.mean(werte)
    se = st.stdev(werte) / math.sqrt(len(werte))
    return m, 1.96 * se


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--korpus", default="data", help="Verzeichnis des Originalkorpus")
    ap.add_argument("--neu", required=True, help="Verzeichnis des frisch erzeugten Arms")
    ap.add_argument("--n-dateien", type=int, default=100,
                    help="wie viele Dateien je Arm gepaart werden (Datei = Block)")
    ap.add_argument("--out", default="evaluations/artifacts/generator_drift.json")
    a = ap.parse_args()

    t0, c0 = time.monotonic(), time.process_time()
    k_files = sorted(glob.glob(os.path.join(a.korpus, "selfplay_hv2_*.pkl")))[:a.n_dateien]
    n_files = sorted(glob.glob(os.path.join(a.new, "selfplay_hv2_*.pkl")))[:a.n_dateien]
    if len(k_files) != len(n_files):
        raise SystemExit(
            f"Ungleiche Blockzahl: Korpus {len(k_files)}, neu {len(n_files)}. "
            "Die Paarung Datei-zu-Datei ist die Voraussetzung dieser Messung -- "
            "ohne sie waere der Vergleich ungepaart und deutlich unschaerfer.")
    print(f"Gepaarte Bloecke: {len(k_files)} Dateien je Arm", flush=True)

    diffs, roh_k, roh_n = {}, {}, {}
    for i, (kf, nf) in enumerate(zip(k_files, n_files), 1):
        bk, bn = _blockwerte(kf), _blockwerte(nf)
        for key in bk:
            if key.startswith("_") or key not in bn:
                continue
            diffs.setdefault(key, []).append(bn[key] - bk[key])
            roh_k.setdefault(key, []).append(bk[key])
            roh_n.setdefault(key, []).append(bn[key])
        if i % 10 == 0 or i == len(k_files):
            print(f"   {i}/{len(k_files)} Bloecke ausgewertet", flush=True)

    kennzahlen = {}
    for key, d in sorted(diffs.items()):
        m, halb = _ki95(d)
        kennzahlen[key] = {
            "korpus": st.mean(roh_k[key]), "neu": st.mean(roh_n[key]),
            "delta": m, "ki95_halb": halb,
            "ki_unten": m - halb, "ki_oben": m + halb, "n_bloecke": len(d),
        }

    # --- Vorregistrierte Entscheidungsregel (par.4), wortgetreu angewandt
    h = kennzahlen[ENTSCHEIDUNGSMASS]
    innerhalb = (abs(h["ki_unten"]) < AEQUIVALENZGRENZE
                 and abs(h["ki_oben"]) < AEQUIVALENZGRENZE)
    ausserhalb = (abs(h["delta"]) > AEQUIVALENZGRENZE
                  and (h["ki_unten"] > AEQUIVALENZGRENZE or h["ki_oben"] < -AEQUIVALENZGRENZE))
    verdict = "VERHALTENSGLEICH" if innerhalb else ("MATERIELL VERSCHIEDEN" if ausserhalb
                                                    else "UNENTSCHIEDEN")

    # --- Waechter gegen den Tunnelblick (par.4): der Korpus ist nicht nur
    #     seine Spaltenzahl.
    gerissen = []
    for key, v in kennzahlen.items():
        if key == ENTSCHEIDUNGSMASS:
            continue
        bezug = abs(v["korpus"])
        if bezug > 1e-9 and abs(v["delta"]) > WAECHTER_ANTEIL * bezug:
            gerissen.append({"kennzahl": key, "korpus": v["korpus"],
                             "neu": v["neu"], "delta": v["delta"]})
    if gerissen and verdict == "VERHALTENSGLEICH":
        verdict = "UNENTSCHIEDEN"

    out = {
        "prereg": "PREREG_generator_drift.md par.4",
        "korpus": a.korpus, "neu": a.new, "n_bloecke": len(k_files),
        "entscheidungsmass": ENTSCHEIDUNGSMASS,
        "aequivalenzgrenze": AEQUIVALENZGRENZE,
        "verdikt": verdict,
        "waechter_gerissen": gerissen,
        "kennzahlen": kennzahlen,
        "laufzeit": {"wanduhr_s": round(time.monotonic() - t0, 1),
                     "cpu_s": round(time.process_time() - c0, 1),
                     "threads": 1, "s_je_partie": None},
    }
    target = pathlib.Path(a.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")

    print(f"\n{'Kennzahl':<22}{'Korpus':>10}{'neu':>10}{'Delta':>10}{'95%-KI':>20}")
    print("-" * 72)
    for key, v in sorted(kennzahlen.items()):
        print(f"{key:<22}{v['korpus']:>10.3f}{v['neu']:>10.3f}{v['delta']:>+10.3f}"
              f"   [{v['ki_unten']:+.3f}, {v['ki_oben']:+.3f}]")
    print(f"\nEntscheidungsmass {ENTSCHEIDUNGSMASS}, Grenze +-{AEQUIVALENZGRENZE}")
    print(f"VERDIKT: {verdict}")
    if gerissen:
        print("Waechter gerissen bei:", ", ".join(g["kennzahl"] for g in gerissen))
    print(f"Artefakt: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
