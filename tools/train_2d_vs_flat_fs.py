# -*- coding: utf-8 -*-
"""tools/train_2d_vs_flat_fs.py -- Task #11 Phase 2 (M3), siehe
evaluations/PREREG_2d_encoder.md fuer die vollstaendige Vorregistrierung.

Faehrt die 12 vorregistrierten FROM-SCRATCH-Traininglaeufe (6 gepaarte Seeds,
`fs_flat` vs `fs_2d`, IDENTISCHES Rezept bis auf `--encoder`/`--seed`, siehe
RECIPE unten), dann `tools/offline_diagnose.py --frozen` ueber alle 12 besten
Checkpoints, dann die vorregistrierte gepaarte Auswertung (t-Test +
Vorzeichentest) auf den beiden arena-validierten Orakel-Metriken
(`prior_mass_on_oracle_top3`, `kendall_tau_policy_vs_oracle_q`).

Vorbild: `tools/train_seed_sweep.py` (Statistik-Muster, Korpus-Stabilitaets-
Check), aber OHNE `--load` (from scratch, siehe PREREG Abschnitt "Arme") und
mit `--encoder`-Durchreichung (Task #11 Phase 2, `train.py`).

Nutzung:
    python tools/train_2d_vs_flat_fs.py --seeds 1 2 3 4 5 6

`--skip-training`: nur Diagnose+Auswertung auf bereits vorhandenen
Checkpoints (Wiederaufnahme nach einem Abbruch waehrend der 12 Laeufe --
`run_training` ueberspringt ohnehin bereits vorhandene `*_best.pth`, das Flag
spart nur den Sweep-Loop selbst).
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import subprocess
import sys
import time
from math import comb
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Identisch fuer beide Arme -- siehe PREREG_2d_encoder.md "Rezept". NUR
# --name/--encoder/--seed unterscheiden die 12 Laeufe voneinander.
RECIPE = ["--epochs", "40", "--lr", "4e-4", "--lr-schedule", "cosine",
          "--value-target-variant", "nortv", "--no-plot", "--no-snapshot"]

ORACLE_KEYS = ("prior_mass_on_oracle_top3", "kendall_tau_policy_vs_oracle_q")


def selfplay_running() -> bool:
    """True, wenn ein self_play.py-Prozess laeuft -- dann waechst `data/`
    waehrend des Sweeps und die 12 Laeufe saehen verschiedene Korpora
    (identisches Muster/Begruendung wie `train_seed_sweep.py`)."""
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


def sign_test_p(n_pos: int, n_neg: int) -> float:
    """Exakter zweiseitiger Vorzeichentest -- gleiche Formel wie
    `train_seed_sweep.py::sign_test_p`/`paired_gating.py::mcnemar_exact_p`."""
    n = n_pos + n_neg
    if n == 0:
        return 1.0
    lo, hi = min(n_pos, n_neg), max(n_pos, n_neg)
    p_le = sum(comb(n, k) for k in range(0, lo + 1)) / (2 ** n)
    p_ge = sum(comb(n, k) for k in range(hi, n + 1)) / (2 ** n)
    return min(1.0, 2 * min(p_le, p_ge))


# ── Gepaarter t-Test ohne scipy (Praezedenzfall PREREG_ownership_gumbel.md:
# "kein scipy im Projekt", t-Verteilung per regularisierter unvollstaendiger
# Betafunktion, Kettenbruch-Naeherung nach Numerical Recipes) ────────────────

def _betacf(a: float, b: float, x: float, max_iter: int = 200, eps: float = 1e-12) -> float:
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < 1e-300:
        d = 1e-300
    d = 1.0 / d
    h = d
    for m in range(1, max_iter + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < 1e-300:
            d = 1e-300
        c = 1.0 + aa / c
        if abs(c) < 1e-300:
            c = 1e-300
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < 1e-300:
            d = 1e-300
        c = 1.0 + aa / c
        if abs(c) < 1e-300:
            c = 1e-300
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return h


def _betai(a: float, b: float, x: float) -> float:
    """Regularisierte unvollstaendige Betafunktion I_x(a,b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    ln_beta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    bt = math.exp(ln_beta + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def paired_ttest_p(diffs: list[float]) -> tuple[float, float, int]:
    """Zweiseitiger gepaarter t-Test. Gibt (t_stat, p_value, df) zurueck."""
    n = len(diffs)
    if n < 2:
        return (float("nan"), 1.0, 0)
    mean = sum(diffs) / n
    var = sum((d - mean) ** 2 for d in diffs) / (n - 1)
    df = n - 1
    if var <= 0:
        return ((float("inf") if mean != 0 else 0.0), (0.0 if mean != 0 else 1.0), df)
    se = math.sqrt(var / n)
    t_stat = mean / se
    p = _betai(df / 2.0, 0.5, df / (df + t_stat * t_stat))
    return (t_stat, p, df)


def run_training(arm: str, seed: int, encoder: str) -> bool:
    name = f"{arm}_s{seed}"
    # Skip-Luecke geschlossen (2026-07-30): laeuft ein Arm ohne Plateau bis zum
    # Epochen-Deckel durch, schreibt train.py NUR alphazero_<name>.pth und kein
    # separates _best.pth -- der reine _best-Check wuerde den fertigen Lauf dann
    # faelschlich wiederholen (geerbt vom train_seed_sweep.py-Vorbild).
    ckpt = BASE_DIR / "models" / f"alphazero_{name}_best.pth"
    if not ckpt.exists():
        ckpt = BASE_DIR / "models" / f"alphazero_{name}.pth"
    if ckpt.exists():
        print(f"  [skip] {name}: Checkpoint existiert schon", flush=True)
        return True
    cmd = ([sys.executable, "-u", str(BASE_DIR / "train.py"),
            "--name", name, "--encoder", encoder, "--seed", str(seed)] + RECIPE)
    print(f"  [run ] {name}  ({' '.join(cmd[4:])})", flush=True)
    t0 = time.time()
    # Bewusst OHNE capture_output: die Live-Ausgabe (Epochen-Fortschritt, ETA)
    # bleibt im Log sichtbar, statt erst am Prozessende gepuffert aufzutauchen
    # (Memory "Agent background-process discipline").
    r = subprocess.run(cmd, cwd=str(BASE_DIR))
    dt = time.time() - t0
    if r.returncode != 0:
        print(f"  [FAIL] {name} rc={r.returncode} nach {dt/60:.1f} min", flush=True)
        return False
    print(f"  [done] {name} nach {dt/60:.1f} min", flush=True)
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3, 4, 5, 6])
    ap.add_argument("--allow-selfplay", action="store_true",
                    help="Sicherheitsabfrage uebergehen (NICHT empfohlen -- siehe Moduldoku).")
    ap.add_argument("--out", default="evaluations/train_2d_vs_flat_fs_result.json")
    ap.add_argument("--diag-out", default="evaluations/offline_diagnose_2d_vs_flat_fs_frozen.json")
    ap.add_argument("--skip-training", action="store_true",
                    help="Nur Diagnose+Auswertung auf bereits vorhandenen Checkpoints.")
    args = ap.parse_args()

    if selfplay_running() and not args.allow_selfplay:
        raise SystemExit(
            "ABBRUCH: Es laeuft ein self_play.py-Prozess. MosaicDataset globt data/*.pkl, "
            "der Korpus waechst also waehrend des Sweeps und die 12 Laeufe waeren nicht auf "
            "demselben Korpus trainiert (siehe PREREG_2d_encoder.md). "
            "Ueberspringen mit --allow-selfplay."
        )

    n_corpus = len(glob.glob(str(BASE_DIR / "data" / "*.pkl")))
    print(f"[sweep] Korpus: {n_corpus} Dateien | Seeds: {args.seeds} | Rezept: {' '.join(RECIPE)}",
          flush=True)
    print(f"[sweep] 12 Laeufe (6 Seeds x 2 Arme, from scratch, kein --load)\n", flush=True)

    if not args.skip_training:
        for seed in args.seeds:
            print(f"=== Seed {seed}: Paar (fs_flat, fs_2d) ===", flush=True)
            t_pair0 = time.time()
            if not run_training("fs_flat", seed, "flat"):
                raise SystemExit(f"fs_flat_s{seed} fehlgeschlagen -- Sweep abgebrochen.")
            if not run_training("fs_2d", seed, "2d"):
                raise SystemExit(f"fs_2d_s{seed} fehlgeschlagen -- Sweep abgebrochen.")
            print(f"[sweep] Seed {seed} fertig nach {(time.time()-t_pair0)/60:.1f} min (beide Arme).\n",
                  flush=True)

    models = [f"fs_flat_s{s}_best" for s in args.seeds] + [f"fs_2d_s{s}_best" for s in args.seeds]
    diag_out = BASE_DIR / args.diag_out
    print(f"[sweep] Diagnose (frozen, Orakel-Metriken) ueber {len(models)} Checkpoints...", flush=True)
    r = subprocess.run([sys.executable, "-u", str(BASE_DIR / "tools" / "offline_diagnose.py"),
                        "--model", *models, "--frozen", "--out", str(diag_out)],
                       cwd=str(BASE_DIR))
    if r.returncode != 0:
        raise SystemExit("offline_diagnose fehlgeschlagen -- siehe Ausgabe oben.")

    blob = json.loads(diag_out.read_text(encoding="utf-8"))
    entries = blob["results"]
    by_name = {e["model"]: e for e in entries}

    vals: dict[str, dict[int, dict]] = {"fs_flat": {}, "fs_2d": {}}
    for arm in vals:
        for seed in args.seeds:
            e = by_name.get(f"{arm}_s{seed}_best")
            if e is not None:
                vals[arm][seed] = {k: e.get(k) for k in ORACLE_KEYS}

    print("\n" + "=" * 78)
    print("  2D-ENCODER vs FLACH, from scratch -- gepaarte Auswertung (PREREG_2d_encoder.md)")
    print("=" * 78)

    summary: dict = {"seeds": args.seeds, "n_corpus_files": n_corpus, "metrics": {}}
    for mk in ORACLE_KEYS:
        common = sorted(s for s in args.seeds
                        if s in vals["fs_flat"] and s in vals["fs_2d"]
                        and vals["fs_flat"][s].get(mk) is not None
                        and vals["fs_2d"][s].get(mk) is not None)
        diffs = [vals["fs_2d"][s][mk] - vals["fs_flat"][s][mk] for s in common]
        print(f"\nMetrik: {mk}")
        print(f"{'Seed':<6}{'fs_flat':>14}{'fs_2d':>14}{'Diff(2d-flat)':>16}")
        for s in common:
            fv, tv = vals["fs_flat"][s][mk], vals["fs_2d"][s][mk]
            print(f"{s:<6}{fv:14.4f}{tv:14.4f}{tv - fv:+16.4f}")
        if not diffs:
            print("  keine auswertbaren Paare")
            continue
        mean_diff = sum(diffs) / len(diffs)
        pos = sum(1 for d in diffs if d > 0)
        neg = sum(1 for d in diffs if d < 0)
        p_sign = sign_test_p(pos, neg)
        t_stat, p_ttest, df = paired_ttest_p(diffs)
        print(f"  Ø Differenz: {mean_diff:+.4f}  (n={len(diffs)})")
        print(f"  Richtung: {pos}x besser / {neg}x schlechter -> Vorzeichentest p={p_sign:.4f}")
        print(f"  Gepaarter t-Test: t={t_stat:.3f}, df={df}, p={p_ttest:.4f}")
        summary["metrics"][mk] = {
            "n": len(diffs), "mean_diff": mean_diff, "n_positive": pos, "n_negative": neg,
            "sign_test_p": p_sign, "t_stat": t_stat, "df": df, "ttest_p": p_ttest,
            "per_seed": {str(s): {"fs_flat": vals["fs_flat"][s][mk], "fs_2d": vals["fs_2d"][s][mk],
                                  "diff": vals["fs_2d"][s][mk] - vals["fs_flat"][s][mk]} for s in common},
        }

    # Automatische Anwendung der PREREG-Abbruchregel (rein deskriptiv -- der
    # Mensch entscheidet trotzdem, das hier ist nur ein Hinweis im Bericht).
    directions = [summary["metrics"][mk]["mean_diff"] > 0 for mk in ORACLE_KEYS if mk in summary["metrics"]]
    if len(directions) == len(ORACLE_KEYS):
        if not any(directions):
            verdict = ("ABBRUCHREGEL GREIFT: fs_2d auf BEIDEN Orakel-Metriken gepaart schlechter -- "
                       "Struktur-Hypothese widerlegt, kein Gating noetig.")
        elif all(directions):
            verdict = ("fs_2d auf BEIDEN Orakel-Metriken gepaart besser -- starker Befund, "
                       "Gating hat hohe Prioritaet.")
        else:
            verdict = ("fs_2d auf MINDESTENS EINER Orakel-Metrik gepaart besser -- Gating lohnt sich "
                       "(siehe PREREG_2d_encoder.md).")
    else:
        verdict = "Nicht alle Metriken auswertbar -- manuelle Pruefung noetig."
    print(f"\n{'=' * 78}\nVERDIKT (automatisch nach PREREG_2d_encoder.md-Regel): {verdict}\n{'=' * 78}")
    summary["verdict"] = verdict

    out_path = BASE_DIR / args.out
    out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nErgebnis: {out_path}")


if __name__ == "__main__":
    main()
