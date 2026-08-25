# -*- coding: utf-8 -*-
"""tools/chance_node_pretest.py -- Billiger Vortest zur Stochastic-MuZero-
Afterstate-Frage (Research-Report Idee 3.1): IST der Chance-Knoten
(Fabrik-Neubefuellung am Rundenuebergang) ueberhaupt der Ort, an dem der
Value-Kopf versagt?

## Warum nicht einfach R² vorher/nachher vergleichen

Ein reiner R²-Vergleich waere WERTLOS: vor einem Chance-Knoten ist der
Spielausgang objektiv unsicherer, dort MUSS R² sinken -- das misst die
Aufgabe, nicht das Modell.

Die eigentliche Signatur der Afterstate-These ist die KALIBRIERUNG: ein
sauber spezifizierter Schaetzer bleibt auch bei hoher Unsicherheit
kalibriert (er sagt dann eben Werte nahe 0,5). Ist der Kopf ausgerechnet
VOR Chance-Knoten systematisch fehlkalibriert -- typischerweise
UEBERKONFIDENT, weil er die zusaetzliche Zufallsvarianz nicht in einem
Skalar unterbringen kann --, dann ist der Chance-Knoten wirklich der
Ort, und ein eigener Afterstate-Kopf ist mechanistisch begruendet.

Operationalisierung: Platt-Steigung B je Gruppe (`sigmoid(A + B*logit(p))`
gegen den tatsaechlichen Ausgang).
  B < 1  -> Modell ist UEBERKONFIDENT (Ausschlaege zu gross)
  B > 1  -> Modell ist UNTERKONFIDENT (Ausschlaege zu klein, gestaucht)
  B ~ 1  -> kalibriert
Erwartung UNTER der Afterstate-These: B_vor deutlich WEITER von 1 entfernt
(Richtung Ueberkonfidenz) als B_nach, INNERHALB derselben Runde.

## Gruppierung

Position innerhalb der Runde ueber den Fuellstand der Fabriken (4 kleine
a 4 + grosse a 5 = 21 Plaettchen bei Rundenbeginn):
  "nach"  = Fuellstand hoch  -> Neubefuellung gerade passiert
  "vor"   = Fuellstand niedrig -> naechster Chance-Knoten steht bevor
Runde 5 ist ausgeschlossen (die Engine konsultiert das Netz dort nie).
Gruppen werden JE RUNDE gebildet, damit Rundeneffekte nicht mit dem
Vorher/Nachher-Effekt verwechselt werden.
"""
from __future__ import annotations

import argparse
import json
import math
import pickle
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "engine" / "py"))

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

EPS = 1e-6


def logit(p: float) -> float:
    p = min(max(p, EPS), 1.0 - EPS)
    return math.log(p / (1.0 - p))


def sigmoid(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-z))


def irls(xs, ys, iters=60):
    """Logistische Regression y ~ sigmoid(a + b*x), Newton/IRLS, reines
    Python (Projektkonvention: kein scipy)."""
    a, b = 0.0, 1.0
    for _ in range(iters):
        s11 = s12 = s22 = g1 = g2 = 0.0
        for xi, yi in zip(xs, ys):
            p = sigmoid(a + b * xi)
            w = max(p * (1.0 - p), 1e-9)
            r = yi - p
            g1 += r
            g2 += r * xi
            s11 += w
            s12 += w * xi
            s22 += w * xi * xi
        det = s11 * s22 - s12 * s12
        if abs(det) < 1e-12:
            break
        da = (s22 * g1 - s12 * g2) / det
        db = (-s12 * g1 + s11 * g2) / det
        a += da
        b += db
        if abs(da) < 1e-10 and abs(db) < 1e-10:
            break
    return a, b


def factory_fill(state: dict) -> int:
    """Anzahl noch liegender Sonnenplaettchen in Fabriken + grosser Fabrik
    (21 bei Rundenbeginn, 0 wenn leergedraftet)."""
    # Feldnamen im Beobachtungs-JSON (serialize.rs): "sun"/"moon", NICHT
    # "sun_tiles" (das ist der interne Rust-Name) -- 2026-08-04 am echten
    # frozen_eval_set verifiziert.
    small = sum(len(f.get("sun", []) or []) + len(f.get("moon", []) or [])
                for f in state.get("factories", []) or [])
    lf = state.get("large_factory", {}) or {}
    large = len(lf.get("sun", []) or []) + len(lf.get("moon", []) or [])
    return small + large


def r2(preds, ys):
    n = len(ys)
    mean = sum(ys) / n
    ss_tot = sum((y - mean) ** 2 for y in ys)
    ss_res = sum((p - y) ** 2 for p, y in zip(preds, ys))
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default="models/alphazero_v19_2d_best.pth")
    ap.add_argument("--eval-set", default="evaluations/frozen_eval_set.pkl")
    ap.add_argument("--hi", type=int, default=15,
                    help="Fuellstand >= hi -> Gruppe 'nach' (Default 15 von 21)")
    ap.add_argument("--lo", type=int, default=6,
                    help="Fuellstand <= lo -> Gruppe 'vor' (Default 6 von 21)")
    ap.add_argument("--out", default="evaluations/artifacts/chance_node_pretest.json")
    args = ap.parse_args()

    import torch
    from neural_net import build_model_from_checkpoint, state_to_tensor, state_to_planes

    recs = pickle.load(open(BASE_DIR / args.eval_set, "rb"))
    recs = recs["records"] if isinstance(recs, dict) and "records" in recs else recs

    blob = torch.load(BASE_DIR / args.model, weights_only=False)
    model, encoder = build_model_from_checkpoint(blob)[:2]
    model.eval()

    # gruppe -> runde -> (logit-Liste, y-Liste, winprob-Liste)
    data: dict = {}
    fill_hist: dict = {}
    with torch.no_grad():
        for rec in recs:
            s = rec["state"]
            if not rec.get("completed") or rec.get("winner") is None:
                continue
            if s.get("phase") != "drafting":
                continue
            rnd = int(s.get("round", 0))
            if rnd not in (1, 2, 3, 4):      # R5: Netz wird nie konsultiert
                continue
            fill = factory_fill(s)
            fill_hist[fill] = fill_hist.get(fill, 0) + 1
            if fill >= args.hi:
                grp = "nach_chance"
            elif fill <= args.lo:
                grp = "vor_chance"
            else:
                continue                      # Mittelfeld bewusst weggelassen
            x = state_to_tensor(s).unsqueeze(0)
            out = model(state_to_planes(s).unsqueeze(0), x) if encoder == "2d" else model(x)
            p = (float(out[1].item()) + 1.0) / 2.0
            y = 1.0 if rec["winner"] == rec["player"] else 0.0
            d = data.setdefault(grp, {}).setdefault(rnd, {"x": [], "y": [], "p": []})
            d["x"].append(logit(p))
            d["y"].append(y)
            d["p"].append(p)

    print(f"Modell: {args.model}   Fuellstand-Schwellen: nach>={args.hi}, vor<={args.lo}")
    print(f"Fuellstand-Verteilung (Top 8): "
          f"{sorted(fill_hist.items(), key=lambda kv: -kv[1])[:8]}\n")

    result = {"model": args.model, "hi": args.hi, "lo": args.lo, "gruppen": {}}
    print(f"{'Gruppe':<13}{'Runde':>6}{'n':>6}{'Ø pred':>9}{'Ø real':>9}"
          f"{'Platt-B':>10}{'Platt-A':>9}{'Brier':>8}{'R²':>8}")
    print("-" * 78)
    for grp in ("nach_chance", "vor_chance"):
        for rnd in sorted(data.get(grp, {})):
            d = data[grp][rnd]
            n = len(d["y"])
            if n < 30:
                continue
            a, b = irls(d["x"], d["y"])
            brier = sum((p - y) ** 2 for p, y in zip(d["p"], d["y"])) / n
            print(f"{grp:<13}{rnd:>6}{n:>6}{sum(d['p'])/n:>9.3f}{sum(d['y'])/n:>9.3f}"
                  f"{b:>10.3f}{a:>9.3f}{brier:>8.4f}{r2(d['p'], d['y']):>8.3f}")
            result["gruppen"].setdefault(grp, {})[str(rnd)] = {
                "n": n, "mean_pred": sum(d["p"]) / n, "mean_actual": sum(d["y"]) / n,
                "platt_A": a, "platt_B": b, "brier": brier, "r2": r2(d["p"], d["y"]),
            }

    # Gepoolt ueber die Runden (Runden-Effekt bleibt in den Einzelzeilen sichtbar)
    print()
    for grp in ("nach_chance", "vor_chance"):
        xs = [v for rnd in data.get(grp, {}) for v in data[grp][rnd]["x"]]
        ys = [v for rnd in data.get(grp, {}) for v in data[grp][rnd]["y"]]
        ps = [v for rnd in data.get(grp, {}) for v in data[grp][rnd]["p"]]
        if len(ys) < 30:
            continue
        a, b = irls(xs, ys)
        brier = sum((p - y) ** 2 for p, y in zip(ps, ys)) / len(ys)
        print(f"GEPOOLT {grp:<13} n={len(ys):>5}  Platt-B={b:.3f}  A={a:+.3f}  "
              f"Brier={brier:.4f}  R²={r2(ps, ys):.3f}")
        result["gruppen"].setdefault(grp, {})["gepoolt"] = {
            "n": len(ys), "platt_A": a, "platt_B": b, "brier": brier, "r2": r2(ps, ys),
        }

    print("\nLESEART: B<1 = ueberkonfident, B>1 = gestaucht/unterkonfident, B~1 = kalibriert.")
    print("Afterstate-These gestuetzt, wenn B_vor DEUTLICH weiter von 1 entfernt ist")
    print("(Richtung Ueberkonfidenz) als B_nach -- NICHT schon, wenn nur R² faellt.")
    (BASE_DIR / args.out).write_text(json.dumps(result, indent=2, ensure_ascii=False),
                                     encoding="utf-8")
    print(f"\nErgebnis: {args.out}")


if __name__ == "__main__":
    main()
