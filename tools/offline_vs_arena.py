# -*- coding: utf-8 -*-
"""tools/offline_vs_arena.py -- Sagen unsere Offline-Metriken die Arena voraus?

## Warum

Dieses Projekt trifft seit Generationen Entscheidungen anhand von
Offline-Metriken (`value_r2_rounds_1_4`, `policy_top1`, ...), OHNE je belegt zu
haben, dass diese Metriken mit Arena-Staerke zusammenhaengen. Es gibt sogar
Gegenbelege: v11 erreichte als erstes Modell ueberhaupt positives R² in Runde
1/2 -- und keinerlei Staerkegewinn. Die 2x2-Kopfattribution zeigte, dass die
Staerke am Value-Kopf haengt, Policy-Offline-Metriken aber nicht als Praediktor
taugen.

Wir haben die Daten, um das zu pruefen: ueber v14..v18 liegen gepaarte
Gating-Ergebnisse (`paired_gating_result_*.json`) UND Frozen-Set-Diagnosen
(`offline_diagnosis_*.json`) vor. Jedes Gating-Paar (A vs B), fuer das beide
Modelle eine Diagnose haben, liefert einen Datenpunkt:

    x = Metrik(A) - Metrik(B)      (offline)
    y = Siegquote von A - 0.5      (Arena)

## Der entscheidende Test

Nicht die Korrelation (bei n<10 kaum belastbar), sondern die
**Richtungsuebereinstimmung**: In wie vielen der ENTSCHIEDENEN Gating-Paare
zeigte die Offline-Metrik auf denselben Sieger wie die Arena? Das ist direkt
interpretierbar und exakt testbar (Binomialtest gegen 50%).

Zusaetzlich Pearson/Spearman mit Permutations-p (kein scipy im Projekt).

## Bekannte Einschraenkung

Die Paare sind NICHT unabhaengig -- dasselbe Modell taucht in mehreren Paaren
auf. Die p-Werte sind daher optimistisch. Bei einem klaren Nullergebnis
schadet das nicht (es wuerde einen Effekt eher vortaeuschen als verdecken);
bei einem positiven Ergebnis ist es ein Vorbehalt.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import random
from math import comb, sqrt
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

METRICS = [
    "value_r2_rounds_1_4",
    "value_r2_global",
    "policy_top1",
    "policy_top3",
]


def binom_p_two_sided(k: int, n: int) -> float:
    """Exakter zweiseitiger Binomialtest gegen p=0.5."""
    if n == 0:
        return 1.0
    lo, hi = min(k, n - k), max(k, n - k)
    p_le = sum(comb(n, i) for i in range(0, lo + 1)) / (2 ** n)
    p_ge = sum(comb(n, i) for i in range(hi, n + 1)) / (2 ** n)
    return min(1.0, 2 * min(p_le, p_ge))


def mcnemar_exact_p(b: int, c: int) -> float:
    return binom_p_two_sided(b, b + c)


def pearson(xs, ys) -> float:
    n = len(xs)
    if n < 3:
        return float("nan")
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    sxx = sum((a - mx) ** 2 for a in xs)
    syy = sum((b - my) ** 2 for b in ys)
    if sxx <= 0 or syy <= 0:
        return float("nan")
    return sxy / sqrt(sxx * syy)


def ranks(v):
    """Durchschnittsraenge (Bindungen korrekt behandelt)."""
    order = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            r[order[k]] = avg
        i = j + 1
    return r


def spearman(xs, ys) -> float:
    return pearson(ranks(xs), ranks(ys))


def perm_p(xs, ys, stat, n_perm=50000, seed=12345) -> float:
    """Zweiseitiger Permutations-p-Wert -- kein scipy noetig."""
    obs = stat(xs, ys)
    if obs != obs:  # NaN
        return float("nan")
    rng = random.Random(seed)
    ys2 = list(ys)
    hits = 0
    for _ in range(n_perm):
        rng.shuffle(ys2)
        s = stat(xs, ys2)
        if s == s and abs(s) >= abs(obs) - 1e-12:
            hits += 1
    return (hits + 1) / (n_perm + 1)


def load_offline() -> tuple[dict, dict]:
    """model -> metriken, nur frozen-set. Zusaetzlich model -> frozen_version."""
    out, versions = {}, {}
    # Auch archive/ scannen: dort liegen die Diagnosen der v10..v13-Generation,
    # deren GEWICHTE beim Datenverlust am 2026-07-24 verlorengingen. Die
    # damaligen Kennzahlen sind damit die einzige verbliebene Quelle -- neu
    # rechnen (und damit value_r2_rounds_1_4 oder die Orakel-Metriken ergaenzen)
    # ist fuer sie unmoeglich. evaluations/ hat Vorrang bei Namensgleichheit.
    sources = (sorted(glob.glob(str(BASE_DIR / "evaluations" / "artifacts" / "offline_diagnosis_*.json")))
               + sorted(glob.glob(str(BASE_DIR / "archive" / "offline_diagnosis_*.json"))))
    for f in sources:
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(d, dict) or not d.get("frozen"):
            continue
        fv = d.get("frozen_version")
        for e in d.get("results", []):
            name = e.get("model")
            if not name:
                continue
            # Spaetere Datei gewinnt nicht blind -- erste Fundstelle behalten,
            # damit ein zufaelliger Reanalyse-Lauf die Referenz nicht kippt.
            if name not in out:
                out[name] = e
                versions[name] = fv
    return out, versions


def load_gatings(min_pairs: int) -> list[dict]:
    rows = []
    seen_gatings = {}
    seen_exact = set()
    for f in (sorted(glob.glob(str(BASE_DIR / "evaluations" / "artifacts" / "paired_gating_result_*.json")))
              + sorted(glob.glob(str(BASE_DIR / "archive" / "paired_gating_result_*.json")))):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        a, b = d.get("name_a"), d.get("name_b")
        aw, bw = d.get("a_wins_total"), d.get("b_wins_total")
        if not (a and b and aw is not None and bw is not None):
            continue
        if (d.get("done_pairs") or 0) < min_pairs:
            continue
        # MEHRERE BLOECKE DERSELBEN FRAGE ZUSAMMENFASSEN. Wird ein Gating
        # nachtraeglich repliziert (v18_dist: 75 Paare, dann 150 mit anderem
        # Seed), liegen zwei Dateien fuer EINEN Vergleich vor. Beide als eigene
        # Datenpunkte zu zaehlen ist doppelt falsch: es blaeht n auf UND es
        # nimmt einen Block, der isoliert "entschieden" aussieht, als
        # Grundwahrheit -- obwohl gerade die Replikation gezeigt hat, dass er es
        # nicht ist. Zusammengefasst wird ueber Siege und diskordante Zaehler,
        # der p-Wert danach EINMAL exakt gerechnet.
        # ZUERST exakte Dubletten aussortieren: dieselbe Datei liegt teils in
        # evaluations/ UND archive/. Ohne diesen Schritt wuerde das Zusammenfassen
        # unten sie ADDIEREN -- die Paarzahl verdoppelt sich und der p-Wert
        # schrumpft scheinbar dramatisch (beobachtet 2026-07-29: v14b vs v14
        # sprang von 200 auf 400 Paare, p von 0.0662 auf 0.0074).
        dup = (a, b, aw, bw, d.get("done_pairs"))
        if dup in seen_exact:
            continue
        seen_exact.add(dup)

        key = (a, b)
        prev = seen_gatings.get(key)
        blk = {"a_wins": aw, "b_wins": bw, "pairs": d.get("done_pairs") or 0,
               "b_disc": d.get("pair_a_sweeps_b"), "c_disc": d.get("pair_b_sweeps_c")}
        if prev is None:
            seen_gatings[key] = blk
            blk["file"] = os.path.basename(f)
            blk["a"], blk["b"] = a, b
            rows.append(blk)
        else:
            prev["a_wins"] += aw
            prev["b_wins"] += bw
            prev["pairs"] += blk["pairs"]
            for k in ("b_disc", "c_disc"):
                if prev.get(k) is not None and blk.get(k) is not None:
                    prev[k] += blk[k]
                else:
                    prev[k] = None
            prev["file"] += " + " + os.path.basename(f)

    for r in rows:
        r["winrate_a"] = r["a_wins"] / max(r["a_wins"] + r["b_wins"], 1)
        # p aus den zusammengefassten diskordanten Zaehlern, sonst aus der Datei.
        if r.get("b_disc") is not None and r.get("c_disc") is not None:
            r["mcnemar_p"] = mcnemar_exact_p(r["b_disc"], r["c_disc"])
        else:
            r["mcnemar_p"] = None
    return rows


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--min-pairs", type=int, default=50,
                   help="Gating-Laeufe mit weniger Paaren ignorieren (Default 50).")
    p.add_argument("--alpha-decisive", type=float, default=0.05,
                   help="Ein Gating gilt als ENTSCHIEDEN, wenn McNemar-p darunter liegt.")
    p.add_argument("--out", default="evaluations/artifacts/offline_vs_arena.json")
    args = p.parse_args()

    offline, versions = load_offline()
    gatings = load_gatings(args.min_pairs)

    print(f"Offline-Diagnosen (frozen): {len(offline)} Modelle")
    vs = sorted({v for v in versions.values() if v is not None})
    if len(vs) > 1:
        print(f"  WARNUNG: gemischte frozen_version {vs} -- nur gleiche Version ist vergleichbar!")
    print(f"Gating-Laeufe (>= {args.min_pairs} Paare): {len(gatings)}\n")

    rows = []
    for g in gatings:
        ea, eb = offline.get(g["a"]), offline.get(g["b"])
        if ea is None or eb is None:
            print(f"  [skip] {g['a']} vs {g['b']}: Offline-Diagnose fehlt fuer "
                  f"{g['a'] if ea is None else g['b']}")
            continue
        if versions.get(g["a"]) != versions.get(g["b"]):
            print(f"  [skip] {g['a']} vs {g['b']}: verschiedene frozen_version")
            continue
        r = dict(g)
        r["deltas"] = {m: (ea.get(m) - eb.get(m))
                       for m in METRICS if ea.get(m) is not None and eb.get(m) is not None}
        rows.append(r)

    if not rows:
        raise SystemExit("Keine auswertbaren Paare gefunden.")

    print(f"\nAuswertbare Paare: {len(rows)}\n")
    print("=" * 100)
    hdr = f"{'A vs B':<34}{'Paare':>6}{'Siegq.A':>9}{'McNemar':>10}  " + \
          "".join(f"{m.replace('value_r2_','R2_').replace('policy_','P_'):>16}" for m in METRICS)
    print(hdr)
    print("-" * 100)
    for r in rows:
        line = f"{r['a']+' vs '+r['b']:<34}{r['pairs']:>6}{r['winrate_a']:>9.3f}" \
               f"{(r['mcnemar_p'] if r['mcnemar_p'] is not None else float('nan')):>10.4f}  "
        line += "".join(f"{r['deltas'].get(m, float('nan')):>+16.4f}" for m in METRICS)
        print(line)
    print("=" * 100)

    decisive = [r for r in rows
                if r["mcnemar_p"] is not None and r["mcnemar_p"] < args.alpha_decisive]
    print(f"\nDavon ENTSCHIEDEN (McNemar p < {args.alpha_decisive}): {len(decisive)}")

    result = {"n_pairs": len(rows), "n_decisive": len(decisive),
              "alpha_decisive": args.alpha_decisive, "metrics": {}}

    print("\n" + "=" * 72)
    print("  RICHTUNGSUEBEREINSTIMMUNG (nur entschiedene Paare)")
    print("=" * 72)
    for m in METRICS:
        sub = [r for r in decisive if m in r["deltas"] and r["deltas"][m] != 0]
        if not sub:
            print(f"{m:<26} -- keine Daten")
            continue
        agree = sum(1 for r in sub
                    if (r["deltas"][m] > 0) == (r["winrate_a"] > 0.5))
        n = len(sub)
        pv = binom_p_two_sided(agree, n)
        print(f"{m:<26} {agree}/{n} richtig  -> Binomialtest p={pv:.4f}")
        result["metrics"][m] = {"agree": agree, "n_decisive": n, "binom_p": pv}

    print("\n" + "=" * 72)
    print("  KORRELATION mit der Siegquote (ALLE Paare, auch unentschiedene)")
    print("=" * 72)
    for m in METRICS:
        sub = [r for r in rows if m in r["deltas"]]
        if len(sub) < 3:
            print(f"{m:<26} -- zu wenige Punkte (n={len(sub)})")
            continue
        xs = [r["deltas"][m] for r in sub]
        ys = [r["winrate_a"] - 0.5 for r in sub]
        rp, rs = pearson(xs, ys), spearman(xs, ys)
        pp = perm_p(xs, ys, pearson)
        ps = perm_p(xs, ys, spearman)
        print(f"{m:<26} n={len(sub)}  Pearson r={rp:+.3f} (p={pp:.4f})   "
              f"Spearman rho={rs:+.3f} (p={ps:.4f})")
        result["metrics"].setdefault(m, {}).update(
            {"n_corr": len(sub), "pearson_r": rp, "pearson_p": pp,
             "spearman_rho": rs, "spearman_p": ps})

    print("\nHINWEIS: Die Paare sind NICHT unabhaengig (dasselbe Modell taucht "
          "mehrfach auf).\nDie p-Werte sind daher optimistisch -- bei einem "
          "Nullergebnis unkritisch, bei\neinem positiven Ergebnis ein Vorbehalt.")

    out = BASE_DIR / args.out
    out.write_text(json.dumps({"result": result, "rows": rows}, indent=2), encoding="utf-8")
    print(f"\nErgebnis: {out}")


if __name__ == "__main__":
    main()
