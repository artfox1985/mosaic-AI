# -*- coding: utf-8 -*-
"""32c Zugriffs-Bilanz: WER nimmt den oben gelegten Mondstein, und wann?

`PREREG_moon_stack_order.md` par.12.3. Instrument, kein Bau am Spiel: liest
vorhandene `--log-games`-Artefakte und beantwortet, wie gross der Hebel der
Mondstapel-Reihenfolge ueberhaupt ist.

DIE FRAGE DAHINTER: die Reihenfolge steuert, WELCHE Farbe obenauf liegt -- nur
der oberste Stein eines Stapels ist ziehbar (`factory.rs:76/96-97`). Wenn der
Gegner den frisch oben gelegten Stein praktisch nie nimmt, steuert die Wahl
niemanden, und weder ein laengerer Horizont (Weg C) noch ein eigener Baumknoten
(Weg A) koennen daran etwas aendern.

LESART VORAB (par.12.3): nimmt der Gegner ihn in unter einem Viertel der Faelle
im naechsten Halbzug, ist der Hebel klein; ueber der Haelfte ist er real.

LOGFORMAT (execution.rs):
  Sonnenzug   "[R1] (Sonne) NetzA: 2x schwarz von F2 -> Reihe 2"
  Stapel      "[R1] (Mond) F2 Mond-Stapel: (tuerkis->rot)"   <- oberster nach dem Pfeil
  Mondzug     "[R1] (Mond) NetzB: 2 (1+1)x rot von F1, F2 -> Reihe 5"
Die Stapelzeile ist eine ZUSTANDSANZEIGE aller Stapel der Fabrik (par.9i), kein
Ereignis -- gezaehlt wird deshalb je Zeile der OBERSTE Stein des zuletzt
gelegten Stapels, und nur, wenn die Zeile direkt auf einen Sonnenzug folgt.
"""
from __future__ import annotations

import argparse, glob, io, json, re, statistics, time
from collections import Counter

RUNDE = re.compile(r"^\[R(\d+)\]")
SONNE = re.compile(r"\u2600\ufe0f?\s+(\S+):\s+\d+\u00d7\s+(\S+)\s+von\s+(\S+)")
STAPEL = re.compile(r"\U0001F319\s+(\S+)\s+Mond-Stapel:\s*(.+)$")
MONDZUG = re.compile(r"\U0001F319\s+(\S+):\s+\d+\s*\([^)]*\)\u00d7\s+(\S+)\s+von\s+([^\u2192]+)")
STACK = re.compile(r"\(([^()]*?)\u2192([^()]*?)\)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifacts", nargs="+", required=True)
    ap.add_argument("--out", default="evaluations/artifacts/moon_access_balance.json")
    a = ap.parse_args()
    t0 = time.time()

    c = Counter()
    distances = []
    for pattern in a.artifacts:
        for path in sorted(glob.glob(pattern)):
            d = json.load(io.open(path, encoding="utf-8"))
            for g in d.get("games", []):
                log = g.get("log", [])
                for i, line in enumerate(log):
                    ms = STAPEL.search(line)
                    if not ms:
                        continue
                    # nur Stapel, die GERADE entstanden sind: die Zeile davor ist
                    # der Sonnenzug, der sie erzeugt hat.
                    prev = SONNE.search(log[i - 1]) if i else None
                    if not prev:
                        continue
                    placer, factory = prev.group(1), ms.group(1)
                    rm = RUNDE.match(line)
                    runde = rm.group(1) if rm else None
                    st = STACK.search(ms.group(2))
                    if not st:
                        continue  # Einzelstein oder "leer": keine Wahl
                    top_colour = st.group(2).strip()
                    c["gelegte_stapel"] += 1
                    # Wer nimmt diese Farbe als naechstes aus DIESER Fabrik?
                    for j in range(i + 1, len(log)):
                        # NUR innerhalb derselben Runde: nach dem Rundenende
                        # werden die Fabriken neu befuellt, dieselbe Farbe aus
                        # derselben Fabrik ist dann ein ANDERER Stein. Ohne
                        # diese Grenze wird jeder Stapel irgendwann "genommen"
                        # und `nie_genommen` ist systematisch 0.
                        rj = RUNDE.match(log[j])
                        if rj and runde and rj.group(1) != runde:
                            break
                        mz = MONDZUG.search(log[j])
                        if not mz:
                            continue
                        taker, colour, sources = mz.group(1), mz.group(2), mz.group(3)
                        if colour == top_colour and factory in [q.strip() for q in sources.split(",")]:
                            who = "leger" if taker == placer else "gegner"
                            c[f"genommen_{who}"] += 1
                            half_moves = sum(1 for k in range(i + 1, j)
                                            if SONNE.search(log[k]) or MONDZUG.search(log[k]))
                            distances.append(half_moves)
                            if who == "gegner" and half_moves <= 1:
                                c["gegner_im_naechsten_halbzug"] += 1
                            break
                    else:
                        c["nie_genommen"] += 1

    n = c["gelegte_stapel"]
    result = {
        "prereg": "PREREG_moon_stack_order.md par.12.3 (Zugriffs-Bilanz)",
        "grundmenge": "frisch gelegte Mondstapel mit mindestens zwei Steinen",
        "quellen": a.artifacts,
        "zaehler": dict(c),
        "anteile": {k: round(c[k] / n, 4) for k in
                    ("genommen_leger", "genommen_gegner", "nie_genommen",
                     "gegner_im_naechsten_halbzug") if n} if n else {},
        "halbzuege_bis_zugriff": {
            "n": len(distances),
            "median": statistics.median(distances) if distances else None,
            "mittel": round(statistics.fmean(distances), 2) if distances else None,
        },
        "lesart": "Gegner im naechsten Halbzug unter 0,25 = Hebel klein; ueber 0,50 = real",
        "laufzeit": {"wanduhr_s": round(time.time() - t0, 1)},
    }
    io.open(a.out, "w", encoding="utf-8").write(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
