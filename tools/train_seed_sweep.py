# -*- coding: utf-8 -*-
"""tools/train_seed_sweep.py -- Trainings-A/B mit MEHREREN Seeds je Arm
(2026-07-28).

## Warum

Alle Trainings-A/Bs dieses Projekts (v12b_lr vs v12, v17_lrfix vs v17,
r5base vs r5excl) verglichen bis 2026-07-28 je EINEN Lauf pro Arm gegen eine
UNBEKANNTE Lauf-zu-Lauf-Varianz -- `train.py` setzte gar keinen Seed. Ein
Unterschied von z.B. +0,0009 im Value-R² war damit prinzipiell nicht
einordenbar.

Dazu kam ein zweiter, groesserer Fehler: `MosaicDataset` globt `data/*.pkl`.
Laeuft parallel ein Self-Play-Batch, sieht JEDER Arm einen anderen Korpus
(gemessen: 382 / 404 / 787 Dateien bei drei Laeufen desselben Tages) -- der
Vergleich ist dann konfundiert, nicht nur verrauscht.

Dieses Werkzeug adressiert beides:
  * je Arm N Seeds, GEPAART ausgewertet (Seed s in Arm A gegen Seed s in
    Arm B -- identische Gewichts-Init und Batch-Reihenfolge, der Unterschied
    ist allein die getestete Aenderung),
  * alle Arme sequenziell im selben Lauf, also auf demselben Korpus
    (Voraussetzung: kein Self-Play schreibt waehrenddessen in `data/`; das
    prueft das Skript und bricht sonst ab).

## Statistik

Kein scipy im Projekt -- daher exakter zweiseitiger VORZEICHENTEST auf den
gepaarten Differenzen (Binomial, dieselbe Formel wie
`paired_gating.py::mcnemar_exact_p`), plus Mittelwert/Streuung der
Differenzen. Bei n Seeds und einheitlicher Richtung gilt p = 2·(1/2)^n --
also erst ab **6 Seeds** ist p < 0,05 ueberhaupt erreichbar. Weniger Seeds
liefern nur eine Tendenz, keinen Beleg; das Skript sagt das im Bericht.

## Nutzung

    python tools/train_seed_sweep.py --seeds 1 2 3 4 5 6 \
        --arm base:"" --arm r5x:"--exclude-round5" --arm own:"--ownership-weight 0.3"

Der Arm `base` (leere Extra-Args) dient ALLEN Vergleichen als gemeinsame
Referenz -- er muss nur EINMAL trainiert werden.

Die Extra-Args eines Arms werden HINTER die Basis-Args gehaengt. Da argparse
bei wiederholten Flags den LETZTEN Wert nimmt (verifiziert), kann ein Arm
damit global gesetzte Werte gezielt ueberschreiben -- z.B.
`--arm lr1e5:"--lr 1e-5 --epochs 40"` setzt fuer diesen Arm eine andere
Lernrate UND einen anderen Epochendeckel, waehrend die uebrigen Arme die
`--lr`/`--epochs` des Sweeps behalten. Gebraucht fuer den LR-Magnituden-Arm:
bei niedrigerer LR greift das Plateau-Early-Stopping spaeter, der Arm braucht
daher einen eigenen Deckel, damit er nicht ausufert.
"""
from __future__ import annotations

import argparse
import glob
import json
import statistics as stats
import subprocess
import sys
from math import comb
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))


def sign_test_p(n_pos: int, n_neg: int) -> float:
    """Exakter zweiseitiger Vorzeichentest -- gleiche Formel wie
    `paired_gating.py::mcnemar_exact_p`."""
    n = n_pos + n_neg
    if n == 0:
        return 1.0
    lo, hi = min(n_pos, n_neg), max(n_pos, n_neg)
    p_le = sum(comb(n, k) for k in range(0, lo + 1)) / (2 ** n)
    p_ge = sum(comb(n, k) for k in range(hi, n + 1)) / (2 ** n)
    return min(1.0, 2 * min(p_le, p_ge))


def selfplay_running() -> bool:
    """True, wenn ein self_play.py-Prozess laeuft -- dann waechst `data/`
    waehrend des Sweeps und die Arme saehen verschiedene Korpora."""
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
             "Where-Object {$_.CommandLine -like '*self_play.py*'} | Measure-Object | "
             "Select-Object -ExpandProperty Count"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
        return int((out.stdout or "0").strip() or 0) > 0
    except Exception:
        return False


def run_training(arm: str, seed: int, extra: str, load: str, epochs: int, lr: float) -> bool:
    name = f"{arm}_s{seed}"
    ckpt = BASE_DIR / "models" / f"alphazero_{name}_best.pth"
    if ckpt.exists():
        print(f"  [skip] {name}: Checkpoint existiert schon", flush=True)
        return True
    cmd = [sys.executable, "-u", str(BASE_DIR / "train.py"),
           "--name", name, "--load", load, "--epochs", str(epochs),
           "--lr", str(lr), "--lr-schedule", "cosine",
           "--seed", str(seed), "--no-plot", "--no-snapshot"]
    if extra.strip():
        cmd += extra.split()
    print(f"  [run ] {name}  ({' '.join(cmd[5:])})", flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print(f"  [FAIL] {name} rc={r.returncode}\n{r.stderr[-1500:]}", flush=True)
        return False
    for line in (r.stdout or "").splitlines():
        if "Bestes Modell" in line:
            print(f"         {line.strip()}", flush=True)
    return True


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--arm", action="append", required=True,
                   help='Arm als "name:extra_args", z.B. own:"--ownership-weight 0.3". '
                        'Mehrfach angebbar; der erste gilt als Referenzarm.')
    p.add_argument("--seeds", type=int, nargs="+", required=True)
    p.add_argument("--load", default="v16_best")
    p.add_argument("--epochs", type=int, default=20)
    p.add_argument("--lr", type=float, default=5e-5)
    p.add_argument("--metric", default="value_r2_rounds_1_4",
                   help="Feld aus offline_diagnosis, das verglichen wird (Default: die "
                        "Entscheidungsmetrik aus Task #15 A -- Runde 5 ausgeschlossen, weil das "
                        "Netz dort nie konsultiert wird).")
    p.add_argument("--out", default="evaluations/train_seed_sweep.json")
    p.add_argument("--allow-selfplay", action="store_true",
                   help="Sicherheitsabfrage uebergehen (NICHT empfohlen -- siehe Modul-Doku).")
    args = p.parse_args()

    arms = []
    for spec in args.arm:
        name, _, extra = spec.partition(":")
        arms.append((name.strip(), extra.strip().strip('"')))

    if selfplay_running() and not args.allow_selfplay:
        raise SystemExit(
            "ABBRUCH: Es laeuft ein self_play.py-Prozess. MosaicDataset globt data/*.pkl, "
            "der Korpus waechst also waehrend des Sweeps und die Arme waeren nicht "
            "vergleichbar (gemessen 2026-07-28: 382/404/787 Dateien bei drei Laeufen). "
            "Erst das Self-Play beenden lassen. Ueberspringen mit --allow-selfplay.")

    n_corpus = len(glob.glob(str(BASE_DIR / "data" / "*.pkl")))
    print(f"[sweep] Korpus: {n_corpus} Dateien | Arme: {[a for a, _ in arms]} | Seeds: {args.seeds}")
    print(f"[sweep] {len(arms) * len(args.seeds)} Trainings\n")

    for arm, extra in arms:
        print(f"--- Arm '{arm}' {extra or '(Referenz, keine Extra-Args)'} ---")
        for seed in args.seeds:
            if not run_training(arm, seed, extra, args.load, args.epochs, args.lr):
                raise SystemExit(f"Arm {arm}, Seed {seed} fehlgeschlagen -- Sweep abgebrochen.")

    models = [f"{arm}_s{seed}_best" for arm, _ in arms for seed in args.seeds]
    diag_out = BASE_DIR / "evaluations" / "offline_diagnosis_seed_sweep.json"
    print(f"\n[sweep] Diagnose ueber {len(models)} Checkpoints (frozen set)...")
    r = subprocess.run([sys.executable, "-u", str(BASE_DIR / "tools" / "offline_diagnosis.py"),
                        "--model", *models, "--frozen", "--out", str(diag_out)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise SystemExit(f"offline_diagnosis fehlgeschlagen:\n{r.stderr[-2000:]}")

    blob = json.loads(diag_out.read_text(encoding="utf-8"))
    entries = blob if isinstance(blob, list) else blob.get("models", blob.get("results", []))
    by_name = {e.get("model", e.get("name")): e for e in entries}

    vals: dict[str, dict[int, float]] = {}
    for arm, _ in arms:
        vals[arm] = {}
        for seed in args.seeds:
            e = by_name.get(f"{arm}_s{seed}_best")
            if e is not None and e.get(args.metric) is not None:
                vals[arm][seed] = float(e[args.metric])

    print("\n" + "=" * 72)
    print(f"  SEED-SWEEP: {args.metric}")
    print("=" * 72)
    hdr = "Seed   " + "".join(f"{a:>14s}" for a, _ in arms)
    print(hdr)
    for seed in args.seeds:
        print(f"{seed:<7d}" + "".join(f"{vals[a].get(seed, float('nan')):14.4f}" for a, _ in arms))
    print("-" * 72)
    print("Ø      " + "".join(
        f"{stats.mean(vals[a].values()) if vals[a] else float('nan'):14.4f}" for a, _ in arms))

    ref = arms[0][0]
    result = {"metric": args.metric, "seeds": args.seeds, "n_corpus_files": n_corpus,
              "arms": {a: vals[a] for a, _ in arms}, "comparisons": {}}
    for arm, _ in arms[1:]:
        common = sorted(set(vals[ref]) & set(vals[arm]))
        diffs = [vals[arm][s] - vals[ref][s] for s in common]
        if not diffs:
            continue
        pos = sum(1 for d in diffs if d > 0)
        neg = sum(1 for d in diffs if d < 0)
        pval = sign_test_p(pos, neg)
        cmp_res = {
            "n_seeds": len(diffs), "mean_diff": stats.mean(diffs),
            "stdev_diff": stats.pstdev(diffs) if len(diffs) > 1 else 0.0,
            "n_positive": pos, "n_negative": neg, "sign_test_p": pval,
            "per_seed_diff": dict(zip(map(str, common), diffs)),
        }
        result["comparisons"][f"{arm}_minus_{ref}"] = cmp_res
        print(f"\n{arm} minus {ref}:")
        print(f"  gepaarte Differenz Ø {stats.mean(diffs):+.4f}  "
              f"(Streuung {cmp_res['stdev_diff']:.4f}, n={len(diffs)})")
        print(f"  Richtung: {pos}x besser / {neg}x schlechter  -> Vorzeichentest p={pval:.4f}")
        if len(diffs) < 6:
            print(f"  HINWEIS: bei n={len(diffs)} Seeds ist p<0.05 selbst bei einheitlicher "
                  f"Richtung unerreichbar (min. p = {2*0.5**len(diffs):.4f}) -- Tendenz, kein Beleg.")

    out = BASE_DIR / args.out
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nErgebnis: {out}")


if __name__ == "__main__":
    main()
