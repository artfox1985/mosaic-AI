# -*- coding: utf-8 -*-
"""Sanity-Check eines Self-Play-Korpus auf den sechs Standard-Kennzahlen
(CLAUDE.md, Nutzer-Anweisung 2026-08-23) plus der Plattenfrage:
werden die Wertungsplatten ueberhaupt angespielt?

ERGAENZT `tools/diagnosis.py`, ersetzt es nicht -- dort stehen Policy-Schaerfe,
Strafleisten-Bias und Ergebnis-Uebersicht; hier Reihen, Spalten und Platten.
Quelle ist das strukturierte `score_geo` / `scoring_tile_points` aus dem
Endzustand jeder Partie, KEIN Log-Regex.

Aufruf:
    python -X utf8 tools/corpus_sanity_check.py <verzeichnis> [<verzeichnis2> ...]
    python -X utf8 tools/corpus_sanity_check.py data --pattern 'selfplay_v22-b05-value-*.pkl'         --out evaluations/artifacts/corpus_sanity_v22b05_value.json
"""
import glob, json, os, pickle, sys
import pathlib as _pl
import sys as _sys
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent.parent))
from corpus_io import load_records

KRIT = {0: "k0", 1: "k1", 2: "k2", 3: "k3", 4: "k4",
        5: "k5", 6: "k6 Spezialfelder", 7: "k7"}


def mw(v):
    return sum(v) / len(v) if v else float("nan")


def ci(v):
    if len(v) < 2:
        return float("nan")
    m = mw(v)
    sd = (sum((x - m) ** 2 for x in v) / (len(v) - 1)) ** 0.5
    return 1.96 * sd / len(v) ** 0.5


def auswerten(verzeichnis, *, pattern="*.pkl"):
    """Standard-Kennzahlen eines Korpus-Verzeichnisses.

    `pattern` (2026-08-30) filtert INNERHALB des Verzeichnisses. Grund: die
    v22-b05-Erzeugung legt drei KLASSEN nebeneinander in `data/`
    (`selfplay_v22-b05-policy_*`, `-value-argmax_*`, `-value-sampled_*`), und
    die Waechter aus PREREG_heuristic_v2_long_rows.md par.3b.12 gelten je
    Klasse. Der Bestandsweg dafuer war `stage_arm` in
    tools/probes/implicit_minimax_selfplay_corpus_eval.py -- eine KOPIE der
    Arm-Dateien in ein eigenes Verzeichnis; bei 600 Dateien a 2,2 MB waeren
    das rund 1,3 GB Kopie fuer eine reine Leseauswertung. Keyword-only und
    mit Default `*.pkl`, damit der vorhandene Aufrufer (ebendieser
    stage_arm-Pfad) unveraendert weiterlaeuft.
    """
    files = sorted(glob.glob(os.path.join(verzeichnis, pattern)))
    partien = {}       # game_id -> letzter Record
    # (game_id, spieler) -> Summe der groessten Strafleisten-Laenge JE RUNDE.
    # ACHTUNG, Fehler vom 2026-08-26: erst stand hier ein Dict mit dem Schluessel
    # (game_id, spieler, runde), und die Summe je Partie wurde am Ende per
    # Filterlauf ueber ALLE Eintraege gebildet -- quadratisch. Bei 270 Partien
    # unauffaellig, bei 24.000 laeuft es Stunden. Jetzt wird direkt auf die
    # (Partie, Seite) aggregiert und die Runde nur im Zwischenspeicher gehalten.
    floor_max = {}     # (game_id, spieler, runde) -> groesste Laenge, wird gleich aggregiert
    for f in files:
        recs = load_records(f)
        for r in recs:
            gid = r.get("game_id")
            st = r.get("state") or {}
            for pi, p in enumerate(st.get("players", [])):
                k = (gid, pi, st.get("round"))
                floor_max[k] = max(floor_max.get(k, 0), len(p.get("floor") or []))
            if r.get("winner") is not None:
                partien[gid] = r

    # EINMAL auf (Partie, Seite) aggregieren statt je Partie zu filtern.
    floor_je_seite = {}
    for (g, pi_, _r), v in floor_max.items():
        floor_je_seite[(g, pi_)] = floor_je_seite.get((g, pi_), 0) + v

    # Je Partie und Seite die Endgroessen einsammeln.
    zeilen_voll, zeilen_fuell, sp_voll, sp_ge4, sp_ge3, sp_max = [], [], [], [], [], []
    punkte, margin, floor_steine = [], [], []
    platten = {i: [] for i in range(8)}
    aktiv = {i: 0 for i in range(8)}
    partien_gesamt = 0
    for gid, r in partien.items():
        st = r["state"]
        ids = st.get("scoring_tile_ids") or []
        partien_gesamt += 1
        for i in ids:
            aktiv[i] += 1
        sc = r.get("scores") or [p.get("score") for p in st["players"]]
        for pi, p in enumerate(st["players"]):
            g = p.get("score_geo") or {}
            rf = g.get("row_fill") or []
            cf = g.get("col_fill") or []
            zeilen_voll.append(sum(1 for x in rf if x >= 6))
            zeilen_fuell.append(mw(rf) if rf else 0.0)
            sp_voll.append(sum(1 for x in cf if x >= 6))
            sp_ge4.append(sum(1 for x in cf if x >= 4))
            sp_ge3.append(sum(1 for x in cf if x >= 3))
            sp_max.append(max(cf) if cf else 0)
            punkte.append(sc[pi])
            margin.append(sc[pi] - sc[1 - pi])
            floor_steine.append(floor_je_seite.get((gid, pi), 0))
            stp = p.get("scoring_tile_points") or []
            for i in ids:
                if i < len(stp):
                    platten[i].append(stp[i])

    print(f"\n=== {verzeichnis} ===")
    print(f"Partien: {partien_gesamt}   Seiten: {len(punkte)}")
    print(f"1) Reihenauslastung : volle Reihen {mw(zeilen_voll):.3f} +- {ci(zeilen_voll):.3f} "
          f"| mittlerer Fuellstand {mw(zeilen_fuell):.2f}/6")
    # Waechter (b) aus PREREG_heuristic_v2_long_rows.md par.3b.12: nicht die
    # RATE, sondern die EREIGNISZAHL -- wieviele Partien-Seiten ueberhaupt
    # mindestens eine volle Spalte tragen (Schwelle 1.500 auf der
    # Value-Klasse). Eine Rate ignoriert die Korpusgroesse, die Zahl nicht.
    sides_with_full_column = sum(1 for x in sp_voll if x >= 1)
    print(f"2) Spaltenauslastung: volle Spalten {mw(sp_voll):.3f} +- {ci(sp_voll):.3f} "
          f"| >=4 {mw(sp_ge4):.2f} | >=3 {mw(sp_ge3):.2f} | hoechste {mw(sp_max):.2f}/6")
    print(f"   Seiten mit >= 1 voller Spalte: {sides_with_full_column} "
          f"von {len(sp_voll)}")
    print(f"3) Strafleiste      : {mw(floor_steine):.2f} +- {ci(floor_steine):.2f} Steine je Partie und Seite")
    print(f"5) Eigene Punkte    : {mw(punkte):.2f} +- {ci(punkte):.2f}")
    print(f"6) Margin           : {mw(margin):.2f} (per Konstruktion 0 im Mittel ueber beide Seiten)")
    print("4) Punkte je Wertungsplatte (nur wo aktiv):")
    for i in range(8):
        if not platten[i]:
            continue
        v = platten[i]
        anteil = 100.0 * sum(1 for x in v if x > 0) / len(v)
        print(f"     {KRIT[i]:18s} aktiv in {aktiv[i]:4d} Partien | "
              f"{mw(v):+7.2f} +- {ci(v):.2f} Pkt | mit Ertrag > 0: {anteil:5.1f} %")
    # Die vier Bestandsfelder bleiben unveraendert (Aufrufer haengen daran);
    # der Rest kommt DAZU, weil die Funktion ihn ohnehin ausrechnet und bisher
    # nur druckte -- ein Artefakt mit vier von sechs Standard-Kennzahlen ist
    # kein Beleg, sondern eine Erinnerungsstuetze.
    return dict(zeilen_voll=mw(zeilen_voll), sp_voll=mw(sp_voll),
                floor=mw(floor_steine), punkte=mw(punkte),
                verzeichnis=verzeichnis, partien=partien_gesamt, seiten=len(punkte),
                zeilen_voll_ci=ci(zeilen_voll), zeilen_fuell=mw(zeilen_fuell),
                sp_voll_ci=ci(sp_voll), sp_ge4=mw(sp_ge4), sp_ge3=mw(sp_ge3),
                sp_max=mw(sp_max), floor_ci=ci(floor_steine),
                sides_with_full_column=sides_with_full_column,
                punkte_ci=ci(punkte), margin=mw(margin),
                platten={KRIT[i]: {"aktiv_in_partien": aktiv[i], "punkte": mw(platten[i]),
                                   "punkte_ci": ci(platten[i]),
                                   "anteil_ertrag_positiv":
                                       100.0 * sum(1 for x in platten[i] if x > 0) / len(platten[i])}
                         for i in range(8) if platten[i]})


if __name__ == "__main__":
    import argparse
    import json
    import pathlib
    import time

    ap = argparse.ArgumentParser(
        description="Standard-Kennzahlen eines oder mehrerer Korpus-Verzeichnisse.")
    ap.add_argument("verzeichnisse", nargs="+", help="Korpus-Verzeichnis(se)")
    # Ein Muster JE Verzeichnis waere die allgemeinere Form, aber jeder heutige
    # Anwendungsfall wertet EINE Klasse aus -- ein globales Muster reicht und
    # bleibt in der Kommandozeile lesbar.
    ap.add_argument("--pattern", default="*.pkl",
                    help="Dateimuster INNERHALB der Verzeichnisse (Default *.pkl); "
                         "z.B. 'selfplay_v22-b05-value-*.pkl' fuer eine Korpus-Klasse")
    ap.add_argument("--out", default="evaluations/artifacts/corpus_sanity_check.json",
                    help="Artefakt-Pfad; eigener Pfad je Klasse, sonst ueberschreiben "
                         "sich zwei Laeufe gegenseitig")
    args = ap.parse_args()

    t0 = time.time()
    ergebnisse = [auswerten(v, pattern=args.pattern) for v in args.verzeichnisse]
    wand = time.time() - t0
    print(f"\nLaufzeit {wand:.1f} s")

    # Laufzeit ins eigene Artefakt (CLAUDE.md, Nutzer-Anweisung 2026-08-25) --
    # beim ersten Bau dieses Werkzeugs vergessen, am selben Tag nachgetragen.
    erg = {"arme": ergebnisse,
           "laufzeit": {"wanduhr_s": round(wand, 1),
                        "cpu_s": round(time.process_time(), 1),
                        "threads": 1,
                        "s_je_partie": None}}
    erg["pattern"] = args.pattern
    target = pathlib.Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    for _ in range(5):
        try:
            target.write_text(json.dumps(erg, indent=2, ensure_ascii=False),
                            encoding="utf-8", newline="\n")
            print(f"Artefakt: {target}")
            break
        except OSError as e:
            print("Retry:", e, flush=True)
            time.sleep(1)
