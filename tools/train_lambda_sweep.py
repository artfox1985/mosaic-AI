# -*- coding: utf-8 -*-
"""tools/train_lambda_sweep.py -- λ-Misch-Value-Target-Sweep (soft-Z,
Willemsen et al. 2021), siehe evaluations/PREREG_lambda_target.md fuer die
vollstaendige Vorregistrierung.

Faehrt die 24 vorregistrierten FROM-SCRATCH-Traininglaeufe (6 gepaarte Seeds
je Arm, 4 Arme `lam10`/`lam07`/`lam05`/`lam03` = `--value-target-lambda`
1.0/0.7/0.5/0.3, IDENTISCHES Rezept bis auf `--value-target-lambda`/`--seed`),
dann `tools/offline_diagnose.py --frozen` ueber alle 24 besten Checkpoints,
dann die vorregistrierte gepaarte Auswertung (t-Test + Vorzeichentest) --
JEDER Nicht-Baseline-Arm (`lam07`/`lam05`/`lam03`) einzeln gegen den
Baseline-Arm (`lam10`, λ=1.0) -- auf der Primaermetrik `value_r2_rounds_1_4`
und den 2 Orakel-Metriken (sekundaer/Sanity-Check, siehe PREREG).

Vorbild: `tools/train_corpus_dose.py` (Sweep-Struktur, Hardlink-Sandbox,
Skip-Logik, gepaarte Statistik) -- UNTERSCHIED: hier gibt es nur EINE
Korpusgroesse (eine einzige eingefrorene Sandbox `data_lambda_sweep/`, alle 4
Arme trainieren auf DEMSELBEN Korpus), die Arme unterscheiden sich durch
`--value-target-lambda` statt `MOSAIC_DATA_DIR`.

Abgrenzung zum toten `rtv`-Experiment (Task #84/#85): siehe
PREREG_lambda_target.md Abschnitt "Abgrenzung zum rtv-Experiment" -- dieses
Skript hat DAMIT nichts zu tun, `--value-target-variant nortv` bleibt fuer
ALLE 4 Arme identisch (Projektstandard), der λ-Mix wirkt AUF das
`nortv`-Ergebnis obendrauf (train.py::MosaicDataset.apply_value_target_lambda).

Nutzung:
    python tools/train_lambda_sweep.py --build-only   # Sandbox + Misch-Anteil
    python tools/train_lambda_sweep.py --seeds 1 2 3 4 5 6

`--skip-training`: nur Diagnose+Auswertung auf bereits vorhandenen
Checkpoints (Wiederaufnahme nach einem Abbruch).

`--smoke`: Rauchtest der Treiber-Mechanik (Hardlink-Sandbox, Skip-Logik,
Diagnose-Aufruf, gepaarte Auswertung, UND dass der Misch-Anteil-Log in
train.py > 0 ist, wenn v18-Dateien im Spiel sind) mit winzigen, EIGENEN
Sandbox-Korpora (2 Seeds, 2 Arme λ∈{1.0, 0.5}, 3 Dateien -- mindestens eine
`v18`-Datei erzwungen, sonst waere der Misch-Anteil trivial 0 --, 2 Epochen
statt 40) -- ruehrt den echten `data/`-Ordner NICHT an, raeumt alle Artefakte
selbst auf.
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import pickle
import random
import re
import shutil
import subprocess
import sys
import time
from math import comb
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Windows-Konsole ohne UTF-8 (cp1252, z.B. Hintergrund-Prozesse): die
# λ-Zeichen in den Auswertungs-Prints wuerfen sonst UnicodeEncodeError --
# live passiert am 2026-08-03 NACH 24 fertigen Laeufen+Diagnose, der Crash
# kostete nur den letzten (billigen) Auswertungsschritt.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

# Identisch fuer alle 4 Arme -- siehe PREREG_lambda_target.md "Rezept". NUR
# --name/--seed/--value-target-lambda unterscheiden die 24 Laeufe voneinander.
RECIPE = ["--epochs", "40", "--lr", "4e-4", "--lr-schedule", "cosine",
          "--value-target-variant", "nortv", "--no-plot", "--no-snapshot"]

# Arm-Name -> --value-target-lambda-Wert. `lam10` (λ=1.0) ist die Baseline
# (Bestandsverhalten, kein Mix) -- gegen SIE werden die drei anderen Arme
# je einzeln gepaart ausgewertet (siehe PREREG "Primaer").
ARM_LAMBDAS = {"lam10": 1.0, "lam07": 0.7, "lam05": 0.5, "lam03": 0.3}
BASELINE_ARM = "lam10"

ORACLE_KEYS = ("prior_mass_on_oracle_top3", "kendall_tau_policy_vs_oracle_q")
# Primaermetrik dieses Experiments (siehe PREREG "Entscheidungsmetriken") --
# ANDERS als bei train_corpus_dose.py, wo value_r2_rounds_1_4 nur informativ
# ist: hier misst es direkt die Zielvarianz-Hypothese, die Orakel-Metriken
# sind hier der Sekundaer-/Sanity-Check (Policy-Seite, sollte UNVERAENDERT
# bleiben).
PRIMARY_KEY = "value_r2_rounds_1_4"
# Bekannte Aufloesungsgrenze (Memory project_offline_metric_resolution_limit)
# -- nur Abstaende darueber gelten als Signal, siehe PREREG.
PRIMARY_RESOLUTION_LIMIT = 0.015

# Erwartete Zusammensetzung DES MESSFENSTERS (PREREG-Grundlage, Stichtag
# 2026-08-02) -- analog train_corpus_dose.py::EXPECTED_COUNTS, aber neueres
# Fenster (v16/v17/v18 statt v15/v16/v17 -- die Zeit ist seit der
# Korpus-Dosis-Vorstudie weitergelaufen, v15 ist inzwischen aus dem
# 900-Datei-Fenster gefallen). NUR `v18`-Dateien tragen `root_q` (Commit
# 2718b9a, 2026-08-01) -- `v16`/`v17` sind aeltere Generationen ohne dieses
# Feld.
EXPECTED_COUNTS = {"v16": 100, "v17": 200, "v18": 600}
VERSION_PREFIXES = tuple(EXPECTED_COUNTS.keys())
ROOT_Q_CAPABLE_PREFIXES = ("v18",)  # einzige Praefixe, die root_q tragen KOENNEN

DATA_DIR = BASE_DIR / "data"
SWEEP_DIR = BASE_DIR / "data_lambda_sweep"
SPLIT_MANIFEST = BASE_DIR / "evaluations" / "train_lambda_sweep_split.json"


def selfplay_running() -> bool:
    """True, wenn ein self_play.py-Prozess laeuft -- rein informativ (siehe
    train_corpus_dose.py::selfplay_running, gleiche Nachbesserungs-Historie:
    die eingefrorene Sandbox macht paralleles Self-Play unschaedlich)."""
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
    """Exakter zweiseitiger Vorzeichentest -- identische Formel wie
    `train_corpus_dose.py::sign_test_p`."""
    n = n_pos + n_neg
    if n == 0:
        return 1.0
    lo, hi = min(n_pos, n_neg), max(n_pos, n_neg)
    p_le = sum(comb(n, k) for k in range(0, lo + 1)) / (2 ** n)
    p_ge = sum(comb(n, k) for k in range(hi, n + 1)) / (2 ** n)
    return min(1.0, 2 * min(p_le, p_ge))


# ── Gepaarter t-Test ohne scipy (identischer Code wie
# `tools/train_corpus_dose.py`/`tools/train_2d_vs_flat_fs.py`) ─────────────

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


# ── Korpus-Klassifikation + Misch-Anteil-Messung ────────────────────────────

def classify_corpus(data_dir: Path) -> tuple[dict[str, list[Path]], int]:
    """Gruppiert *.pkl in `data_dir` nach Versions-Praefix -- NUR v16/v17/v18
    bilden das Messfenster (siehe EXPECTED_COUNTS). Dateien mit anderen
    Praefixen (z.B. `v19` aus parallel laufendem Self-Play) werden nur
    gezaehlt/gemeldet, kein Abbruchgrund (identisches Muster wie
    train_corpus_dose.py::classify_corpus)."""
    groups: dict[str, list[Path]] = {p: [] for p in VERSION_PREFIXES}
    outside: list[str] = []
    for f in sorted(data_dir.glob("*.pkl")):
        hit = next((p for p in VERSION_PREFIXES if f.name.startswith(f"selfplay_{p}_")), None)
        if hit is None:
            outside.append(f.name)
        else:
            groups[hit].append(f)
    if outside:
        found_prefixes = sorted({
            n.split("_")[1] for n in outside if n.startswith("selfplay_") and len(n.split("_")) > 1
        }) or ["unbekannt"]
        print(f"[split] {len(outside)} Datei(en) ausserhalb des Messfensters ignoriert "
              f"(Praefix(e): {', '.join(found_prefixes)} -- laeuft parallel, nicht Teil des "
              f"v16/v17/v18-Universums) -- kein Abbruch.", flush=True)
    return groups, len(outside)


def verify_expected_composition(groups: dict[str, list[Path]]) -> None:
    """Harter Abbruch NUR bei Abweichung INNERHALB des v16/v17/v18-Universums
    -- identisches Muster wie train_corpus_dose.py::verify_expected_composition."""
    actual = {p: len(files) for p, files in groups.items()}
    if actual != EXPECTED_COUNTS:
        raise SystemExit(
            f"ABBRUCH: v16/v17/v18-Zusammensetzung in {DATA_DIR} weicht vom PREREG-Stand ab.\n"
            f"  erwartet: {EXPECTED_COUNTS}\n"
            f"  gefunden: {actual}\n"
            f"(Dateien ausserhalb dieses Universums, z.B. v19, sind bereits ausgeschlossen und "
            f"NICHT die Ursache.) KEINE automatische Neuziehung -- siehe PREREG_lambda_target.md. "
            f"Manuelle Entscheidung noetig (neue Vorregistrierung schreiben)."
        )


def compute_sample_root_q_fraction(files: list[Path]) -> tuple[int, int]:
    """Scannt ALLE uebergebenen Dateien mit `v18`-Praefix (einzige Praefixe,
    die `root_q` ueberhaupt tragen KOENNEN, siehe ROOT_Q_CAPABLE_PREFIXES --
    `v16`/`v17` tragen garantiert 0 root_q-Records, ein Scan waere nur
    verschwendete I/O) und zaehlt (n_mit_root_q, n_gesamt) UEBER DAS GESAMTE
    900-Datei-FENSTER (v16+v17+v18 zusammen, `n_gesamt` beruecksichtigt auch
    die v16/v17-Dateien, die garantiert 0 beitragen -- der Nenner ist das
    ganze Trainingsfenster, nicht nur die v18-Teilmenge). Das ist die
    SAMPLE-Ebene-Zahl, die PREREG_lambda_target.md unter "Datengrundlage"
    verlangt (Datei-Anteil 600/900 ist NUR eine grobe Obergrenze, da root_q
    selbst innerhalb v18 nur bei Mehr-Aktionen-Drafting-Zuegen geloggt wird).

    Kann bei allen 900 Dateien mehrere Minuten dauern (reines Pickle-Laden,
    kein HDF5-Cache-Bau) -- nur beim `--build-only`-Schritt einmalig
    aufgerufen, nicht Teil jedes Sweep-Starts."""
    n_with, n_total = 0, 0
    v18_files = [f for f in files if any(f.name.startswith(f"selfplay_{p}_") for p in ROOT_Q_CAPABLE_PREFIXES)]
    other_files = [f for f in files if f not in v18_files]
    for f in other_files:
        with open(f, "rb") as fh:
            game_data = pickle.load(fh)
        n_total += len(game_data)
    for f in v18_files:
        with open(f, "rb") as fh:
            game_data = pickle.load(fh)
        n_total += len(game_data)
        n_with += sum(1 for step in game_data if step.get("root_q") is not None)
    return n_with, n_total


def stratified_pull_min_one_v18(all_files: list[Path], n: int, seed: int) -> list[Path]:
    """Fuer den Rauchtest: zieht `n` Dateien aus `all_files`, garantiert
    MINDESTENS eine `v18`-Datei (sonst waere der Misch-Anteil im Rauchtest
    trivial 0 und der geforderte '>0'-Check koennte nie greifen). Fester Seed
    fuer Reproduzierbarkeit."""
    rng = random.Random(seed)
    v18 = [f for f in all_files if f.name.startswith("selfplay_v18_")]
    non_v18 = [f for f in all_files if not f.name.startswith("selfplay_v18_")]
    if not v18:
        raise SystemExit("ABBRUCH (smoke): keine v18-Datei in data/ gefunden -- "
                          "Misch-Anteil-Check des Rauchtests braucht mindestens eine.")
    rng.shuffle(v18)
    rng.shuffle(non_v18)
    picked = [v18[0]] + non_v18[: max(0, n - 1)]
    if len(picked) < n:
        picked += v18[1: 1 + (n - len(picked))]
    return sorted(picked[:n])


def load_or_build_split() -> tuple[list[str], int, int]:
    """Persistiert die Ziehung + den gemessenen Misch-Anteil einmalig nach
    SPLIT_MANIFEST -- ein Wiederaufnahme-Lauf verwendet garantiert denselben
    900-Datei-Stand (identisches Prinzip wie
    train_corpus_dose.py::load_or_build_split, hier aber nur EINE Dateimenge
    statt voll/halb). Gibt (file_names, n_mit_root_q, n_gesamt) zurueck."""
    if SPLIT_MANIFEST.exists():
        blob = json.loads(SPLIT_MANIFEST.read_text(encoding="utf-8"))
        print(f"[split] Wiederverwendet aus {SPLIT_MANIFEST.name} "
              f"({blob['n_files']} Dateien, Misch-Anteil "
              f"{blob['sample_root_q_frac']*100:.2f}% von {blob['n_samples_total']:,} Samples).")
        return blob["files"], blob["n_samples_root_q"], blob["n_samples_total"]

    groups, n_outside = classify_corpus(DATA_DIR)
    verify_expected_composition(groups)
    all_files = sorted(f for files in groups.values() for f in files)
    print(f"[split] Messe Sample-Misch-Anteil ueber {len(all_files)} Dateien "
          f"(scannt nur die {EXPECTED_COUNTS.get('v18', 0)} v18-Dateien tatsaechlich, "
          f"v16/v17 zaehlen nur die Record-Anzahl) -- kann einige Minuten dauern...", flush=True)
    t0 = time.time()
    n_with, n_total = compute_sample_root_q_fraction(all_files)
    frac = (n_with / n_total) if n_total else 0.0
    print(f"[split] Misch-Anteil: {n_with:,} von {n_total:,} Samples haben root_q "
          f"({frac*100:.2f}%) -- {time.time()-t0:.1f}s.", flush=True)

    manifest = {
        "expected_counts": EXPECTED_COUNTS,
        "files": [f.name for f in all_files],
        "n_files": len(all_files),
        "n_outside_window_ignored_at_build_time": n_outside,
        "n_samples_root_q": n_with,
        "n_samples_total": n_total,
        "sample_root_q_frac": frac,
    }
    SPLIT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    SPLIT_MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[split] Neu gebaut -> {SPLIT_MANIFEST}")
    return manifest["files"], n_with, n_total


def ensure_hardlink_mirror(file_names: list[str], target_dir: Path, source_dir: Path) -> None:
    """Identisch zu `train_corpus_dose.py::ensure_hardlink_mirror`."""
    target_dir.mkdir(parents=True, exist_ok=True)
    wanted = set(file_names)
    for existing in target_dir.glob("*.pkl"):
        if existing.name not in wanted:
            existing.unlink()
    for name in file_names:
        dst = target_dir / name
        if not dst.exists():
            os.link(str(source_dir / name), str(dst))
    n = len(list(target_dir.glob("*.pkl")))
    if n != len(file_names):
        raise SystemExit(f"ABBRUCH: {target_dir} hat {n} Dateien, erwartet {len(file_names)}.")


def verify_sandbox_consistency(file_names: list[str], target_dir: Path, source_dir: Path,
                                label: str) -> None:
    """Identisch zu `train_corpus_dose.py::verify_sandbox_consistency` (Anzahl
    + Hardlink-Identitaet ueber `st_ino`)."""
    if not target_dir.exists():
        raise SystemExit(
            f"ABBRUCH: {label}-Sandbox {target_dir} existiert nicht -- erst "
            f"ensure_hardlink_mirror() aufrufen (ohne --skip-training)."
        )
    actual = sorted(p.name for p in target_dir.glob("*.pkl"))
    expected = sorted(file_names)
    if actual != expected:
        missing = sorted(set(expected) - set(actual))
        extra = sorted(set(actual) - set(expected))
        raise SystemExit(
            f"ABBRUCH: {label}-Sandbox {target_dir} weicht vom Split-Manifest ab "
            f"(fehlend: {len(missing)} z.B. {missing[:3]}, ueberzaehlig: {len(extra)} "
            f"z.B. {extra[:3]}). Neu aufbauen (ensure_hardlink_mirror) statt blind weiterzulaufen."
        )
    mismatched = []
    for name in file_names:
        src, dst = source_dir / name, target_dir / name
        if not src.exists():
            mismatched.append(f"{name} (fehlt in {source_dir}!)")
            continue
        if os.stat(src).st_ino != os.stat(dst).st_ino:
            mismatched.append(name)
    if mismatched:
        raise SystemExit(
            f"ABBRUCH: {label}-Sandbox {target_dir}: {len(mismatched)} Datei(en) sind KEINE "
            f"Hardlinks (mehr) auf die Quelle in {source_dir} (z.B. {mismatched[:3]}). "
            f"Neu aufbauen (ensure_hardlink_mirror)."
        )
    print(f"[check] {label}-Sandbox {target_dir}: {len(file_names)} Dateien, "
          f"Anzahl+Hardlink-Identitaet OK.", flush=True)


def remove_sandbox_dir(d: Path, label: str) -> None:
    """Identisch zu `train_corpus_dose.py::remove_sandbox_dir` (fehlertolerant
    -- ein haengendes Windows-Datei-Handle darf ein bereits geschriebenes
    Messergebnis nie verhindern)."""
    assert d != DATA_DIR and d.resolve() != DATA_DIR.resolve(), \
        f"SICHERHEITSSTOPP: remove_sandbox_dir() sollte NIE data/ selbst loeschen ({d})."
    if not d.exists():
        return
    try:
        shutil.rmtree(d)
        print(f"[cleanup] {label}-Sandbox entfernt: {d}", flush=True)
    except OSError as e:
        print(f"[cleanup][WARNUNG] {label}-Sandbox {d} konnte nicht vollstaendig entfernt werden "
              f"({e!r}) -- vermutlich haengt noch ein Datei-Handle. KEIN Abbruch (das Messergebnis "
              f"ist zu diesem Zeitpunkt laengst geschrieben) -- Ordner manuell nachraeumen oder beim "
              f"naechsten Lauf erneut versuchen.", flush=True)


# ── Trainings-Sweep ──────────────────────────────────────────────────────

def run_training(arm: str, seed: int, data_dir_override: Path, recipe: list[str],
                  lam: float, capture: bool = False) -> tuple[bool, str]:
    """Startet EINEN `train.py`-Subprozess. `capture=True` (nur vom Rauchtest
    genutzt) faengt stdout/stderr fuer den Misch-Anteil-Log-Check ab, gibt es
    aber trotzdem auf der Konsole aus (kein stiller Lauf) -- der reale Sweep
    laeuft weiterhin OHNE Capture (Memory "Agent background-process
    discipline": Live-Ausgabe sichtbar halten, capture_output nur fuer den
    winzigen Rauchtest vertretbar)."""
    name = f"{arm}_s{seed}"
    ckpt = BASE_DIR / "models" / f"alphazero_{name}_best.pth"
    if not ckpt.exists():
        ckpt = BASE_DIR / "models" / f"alphazero_{name}.pth"
    if ckpt.exists():
        print(f"  [skip] {name}: Checkpoint existiert schon", flush=True)
        return True, ""
    cmd = ([sys.executable, "-X", "faulthandler", "-u", str(BASE_DIR / "train.py"),
            "--name", name, "--seed", str(seed), "--value-target-lambda", str(lam)] + recipe)
    env = os.environ.copy()
    env["MOSAIC_DATA_DIR"] = str(data_dir_override)
    print(f"  [run ] {name}  [MOSAIC_DATA_DIR={data_dir_override}]  ({' '.join(cmd[5:])})", flush=True)
    t0 = time.time()
    if capture:
        r = subprocess.run(cmd, cwd=str(BASE_DIR), env=env, capture_output=True,
                           text=True, encoding="utf-8", errors="replace")
        print(r.stdout)
        if r.stderr:
            print(r.stderr, file=sys.stderr)
        out_text = r.stdout + "\n" + r.stderr
    else:
        r = subprocess.run(cmd, cwd=str(BASE_DIR), env=env)
        out_text = ""
    dt = time.time() - t0
    if r.returncode != 0:
        print(f"  [FAIL] {name} rc={r.returncode} nach {dt/60:.1f} min", flush=True)
        return False, out_text
    print(f"  [done] {name} nach {dt/60:.1f} min", flush=True)
    return True, out_text


def resolve_checkpoint_name(name: str) -> str:
    """`_best` wenn vorhanden, sonst der Plain-Checkpoint -- identisch zu
    `train_corpus_dose.py::resolve_checkpoint_name`."""
    if (BASE_DIR / "models" / f"alphazero_{name}_best.pth").exists():
        return f"{name}_best"
    return name


def run_diagnose_and_eval(seeds: list[int], diag_out: Path, result_out: Path,
                           n_corpus_files: int, arm_lambdas: dict[str, float] | None = None) -> dict:
    """Diagnostiziert alle len(arm_lambdas)*len(seeds) Checkpoints, wertet
    dann JEDEN Nicht-Baseline-Arm EINZELN gepaart gegen `lam10` aus (je
    (PRIMARY_KEY + ORACLE_KEYS)). `arm_lambdas` default None -> das volle
    4-Arm-`ARM_LAMBDAS` (echter Sweep) -- der Rauchtest uebergibt seine
    eigene, kleinere 2-Arm-Teilmenge, damit `offline_diagnose.py` nicht nach
    im Rauchtest nie erzeugten `lam07`/`lam03`-Checkpoints sucht."""
    if arm_lambdas is None:
        arm_lambdas = ARM_LAMBDAS
    non_baseline = tuple(a for a in arm_lambdas if a != BASELINE_ARM)

    all_names = [f"{arm}_s{s}" for arm in arm_lambdas for s in seeds]
    resolved = [resolve_checkpoint_name(n) for n in all_names]

    # Wiederaufnahme-Guard (2026-08-03): deckt ein BEREITS geschriebenes
    # Diagnose-JSON alle benoetigten Modelle ab, wird es wiederverwendet
    # statt die teure 24-Checkpoint-Diagnose zu wiederholen (der
    # UnicodeEncodeError-Crash oben passierte NACH fertiger Diagnose --
    # nur der billige Auswertungsschritt fehlte). Rein mechanisch, keine
    # Metrik-/Regelaenderung (PREREG-konform).
    reuse = False
    if diag_out.exists():
        try:
            existing = {e["model"] for e in json.loads(diag_out.read_text(encoding="utf-8"))["results"]}
            reuse = set(resolved) <= existing
        except Exception:
            reuse = False
    if reuse:
        print(f"\n[diag] Wiederverwendet: {diag_out.name} deckt alle {len(resolved)} "
              f"Checkpoints ab -- keine Neu-Diagnose.", flush=True)
    else:
        print(f"\n[diag] Diagnose (frozen, Orakel-Metriken + value_r2) ueber {len(resolved)} "
              f"Checkpoints...", flush=True)
        r = subprocess.run([sys.executable, "-u", str(BASE_DIR / "tools" / "offline_diagnose.py"),
                            "--model", *resolved, "--frozen", "--out", str(diag_out)],
                           cwd=str(BASE_DIR))
        if r.returncode != 0:
            raise SystemExit("offline_diagnose fehlgeschlagen -- siehe Ausgabe oben.")

    blob = json.loads(diag_out.read_text(encoding="utf-8"))
    by_name = {e["model"]: e for e in blob["results"]}

    # vals[arm][seed] = {metric: wert}
    vals: dict[str, dict[int, dict]] = {arm: {} for arm in arm_lambdas}
    metric_keys = (PRIMARY_KEY,) + ORACLE_KEYS
    for arm in arm_lambdas:
        for s in seeds:
            resolved_name = resolve_checkpoint_name(f"{arm}_s{s}")
            e = by_name.get(resolved_name)
            if e is not None:
                vals[arm][s] = {k: e.get(k) for k in metric_keys}

    print("\n" + "=" * 78)
    print("  λ-MISCH-VALUE-TARGET: gepaarte Auswertung (PREREG_lambda_target.md)")
    print("=" * 78)

    summary: dict = {
        "seeds": seeds, "n_corpus_files": n_corpus_files, "arm_lambdas": arm_lambdas,
        "baseline_arm": BASELINE_ARM, "comparisons": {},
    }

    for arm in non_baseline:
        comp: dict = {"lambda": ARM_LAMBDAS[arm], "metrics": {}}
        print(f"\n--- {arm} (λ={ARM_LAMBDAS[arm]}) vs {BASELINE_ARM} (Baseline, λ=1.0) ---")
        for mk in metric_keys:
            common = sorted(s for s in seeds
                            if s in vals[arm] and s in vals[BASELINE_ARM]
                            and vals[arm][s].get(mk) is not None
                            and vals[BASELINE_ARM][s].get(mk) is not None)
            diffs = [vals[arm][s][mk] - vals[BASELINE_ARM][s][mk] for s in common]
            label = "PRIMAER" if mk == PRIMARY_KEY else "sekundaer/Sanity"
            print(f"\n  Metrik: {mk} ({label})")
            print(f"  {'Seed':<6}{BASELINE_ARM:>14}{arm:>14}{'Diff(arm-base)':>18}")
            for s in common:
                bv, av = vals[BASELINE_ARM][s][mk], vals[arm][s][mk]
                print(f"  {s:<6}{bv:14.4f}{av:14.4f}{av - bv:+18.4f}")
            if not diffs:
                print("    keine auswertbaren Paare")
                comp["metrics"][mk] = {"n": 0}
                continue
            mean_diff = sum(diffs) / len(diffs)
            pos = sum(1 for d in diffs if d > 0)
            neg = sum(1 for d in diffs if d < 0)
            p_sign = sign_test_p(pos, neg)
            t_stat, p_ttest, df = paired_ttest_p(diffs)
            print(f"    Ø Differenz ({arm}-{BASELINE_ARM}): {mean_diff:+.4f}  (n={len(diffs)})")
            print(f"    Richtung: {pos}x {arm} besser / {neg}x {BASELINE_ARM} besser -> "
                  f"Vorzeichentest p={p_sign:.4f}")
            print(f"    Gepaarter t-Test: t={t_stat:.3f}, df={df}, p={p_ttest:.4f}")
            if mk == PRIMARY_KEY:
                above = abs(mean_diff) > PRIMARY_RESOLUTION_LIMIT
                print(f"    Aufloesungsgrenze ({PRIMARY_RESOLUTION_LIMIT}): "
                      f"{'UEBER -- Signal' if above else 'unter -- kein interpretierbarer Befund'}")
            comp["metrics"][mk] = {
                "n": len(diffs), "mean_diff": mean_diff, "n_positive": pos, "n_negative": neg,
                "sign_test_p": p_sign, "t_stat": t_stat, "df": df, "ttest_p": p_ttest,
                "per_seed": {str(s): {BASELINE_ARM: vals[BASELINE_ARM][s][mk], arm: vals[arm][s][mk],
                                      "diff": vals[arm][s][mk] - vals[BASELINE_ARM][s][mk]} for s in common},
            }
        summary["comparisons"][arm] = comp

    # Automatische Anwendung der PREREG-Interpretationsregel (deskriptiv --
    # der Mensch entscheidet trotzdem, siehe PREREG "Interpretationsregeln").
    candidates = []
    for arm in non_baseline:
        pm = summary["comparisons"][arm]["metrics"].get(PRIMARY_KEY, {})
        md = pm.get("mean_diff")
        if md is not None and md > PRIMARY_RESOLUTION_LIMIT:
            candidates.append((arm, md))
    if candidates:
        best_arm, best_diff = max(candidates, key=lambda t: t[1])
        verdict = (
            f"Bester λ-Arm: '{best_arm}' (λ={arm_lambdas[best_arm]}), Ø-Differenz "
            f"{PRIMARY_KEY}={best_diff:+.4f} > Aufloesungsgrenze {PRIMARY_RESOLUTION_LIMIT} -- "
            f"naechster Schritt: Arena-Gating '{best_arm}' vs '{BASELINE_ARM}' "
            f"(siehe PREREG_lambda_target.md Abschnitt 'Entscheidend fuers Uebernehmen'):\n"
            f"  python tools/paired_gating.py "
            f"--model-a models/alphazero_{best_arm}_best.onnx "
            f"--model-b models/alphazero_{BASELINE_ARM}_best.onnx "
            f"--name-a {best_arm}_best --name-b {BASELINE_ARM}_best "
            f"--sims 400 --no-promote-winner"
        )
        summary["best_arm"] = best_arm
    else:
        verdict = (f"KEIN Arm ueber der Aufloesungsgrenze ({PRIMARY_RESOLUTION_LIMIT}) auf "
                   f"{PRIMARY_KEY} gepaart besser als '{BASELINE_ARM}' -- Hypothese in diesem "
                   f"Datenregime (600/900 Dateien mit root_q) nicht bestaetigt. KEIN Arena-Schritt "
                   f"(siehe PREREG_lambda_target.md Interpretationsregeln).")
        summary["best_arm"] = None
    print(f"\n{'=' * 78}\nVERDIKT (automatisch nach PREREG_lambda_target.md-Regel): {verdict}\n{'=' * 78}")
    summary["verdict"] = verdict

    result_out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nErgebnis: {result_out}")
    return summary


# ── Rauchtest ────────────────────────────────────────────────────────────

_MIX_LOG_RE = re.compile(r"([\d.]+)% der (?:Trainings|Val)-Samples (?:haben|HAETTEN) root_q")


def _extract_mix_fractions(log_text: str) -> list[float]:
    return [float(m) for m in _MIX_LOG_RE.findall(log_text)]


def run_smoke() -> None:
    """Testet die Treiber-Mechanik (Hardlink-Sandbox, Skip-Logik,
    Diagnose-Aufruf, gepaarte Auswertung) end-to-end mit winzigem,
    EIGENEM Sandbox-Korpus (3 Dateien, davon GARANTIERT mindestens eine
    `v18`-Datei) -- ruehrt den echten `data/`-Ordner NICHT an. 2 Seeds, 2
    Arme (λ=1.0/0.5), 2 Epochen. Prueft ZUSAETZLICH, dass train.py selbst im
    Log einen Misch-Anteil >0 meldet (der lam05-Lauf mischt aktiv, der
    lam10-Lauf loggt den Anteil nur informativ -- beide Zeilen muessen >0
    zeigen, weil die Sandbox mindestens eine v18-Datei enthaelt). Raeumt alle
    Artefakte im finally-Block auf, auch bei Fehlschlag."""
    print("[smoke] Rauchtest: 2 Seeds, 2 Arme (λ=1.0/0.5), 3 Sandbox-Dateien (>=1 v18), 2 Epochen.")
    print("[smoke] Ruehrt den echten data/-Ordner NICHT an (eigene Sandbox).\n", flush=True)

    if selfplay_running():
        print("[smoke][info] self_play.py laeuft parallel -- unkritisch, der Rauchtest baut "
              "eine eigene eingefrorene Sandbox.", flush=True)

    groups, _n_outside = classify_corpus(DATA_DIR)
    all_files = sorted(f for files in groups.values() for f in files)
    if len(all_files) < 5:
        raise SystemExit("ABBRUCH (smoke): weniger als 5 passende Dateien in data/.")

    smoke_names = [f.name for f in stratified_pull_min_one_v18(all_files, n=3, seed=20260802)]
    n_v18_in_smoke = sum(1 for n in smoke_names if n.startswith("selfplay_v18_"))
    print(f"[smoke] Gezogen: {smoke_names} ({n_v18_in_smoke} v18-Datei(en)).", flush=True)

    smoke_dir = BASE_DIR / "data_lambda_sweep_smoke"
    smoke_recipe = ["--epochs", "2", "--lr", "4e-4", "--lr-schedule", "cosine",
                     "--value-target-variant", "nortv", "--no-plot", "--no-snapshot"]
    smoke_arms = {"lam10": 1.0, "lam05": 0.5}
    seeds = [1, 2]
    diag_out = BASE_DIR / "evaluations" / "_smoke_lambda_sweep_diag.json"
    result_out = BASE_DIR / "evaluations" / "_smoke_lambda_sweep_result.json"
    ok = False
    mix_fracs_seen: list[float] = []
    try:
        ensure_hardlink_mirror(smoke_names, smoke_dir, DATA_DIR)
        verify_sandbox_consistency(smoke_names, smoke_dir, DATA_DIR, "smoke")
        print(f"[smoke] Sandbox aufgebaut: {smoke_dir.name} ({len(smoke_names)} Dateien)", flush=True)

        for seed in seeds:
            for arm, lam in smoke_arms.items():
                success, out_text = run_training(arm, seed, smoke_dir, smoke_recipe, lam,
                                                  capture=True)
                if not success:
                    raise SystemExit(f"[smoke] {arm}_s{seed}-Lauf fehlgeschlagen.")
                mix_fracs_seen.extend(_extract_mix_fractions(out_text))

        if not mix_fracs_seen:
            raise SystemExit("[smoke] KEIN Misch-Anteil-Log in irgendeinem Lauf gefunden -- "
                              "train.py-Log-Format hat sich vermutlich geaendert "
                              "(erwartetes Muster: 'X.X% der Trainings-Samples ...root_q').")
        if not any(f > 0.0 for f in mix_fracs_seen):
            raise SystemExit(f"[smoke] Misch-Anteil ist bei JEDEM Lauf 0.0% "
                              f"({mix_fracs_seen}), obwohl die Sandbox {n_v18_in_smoke} "
                              f"v18-Datei(en) enthaelt -- root_q kommt nicht im Cache an.")
        print(f"\n[smoke] Misch-Anteil-Log-Check OK -- gefundene Werte: {mix_fracs_seen} "
              f"(mind. einer > 0).", flush=True)

        summary = run_diagnose_and_eval(seeds, diag_out, result_out, n_corpus_files=len(smoke_names),
                                        arm_lambdas=smoke_arms)
        assert "verdict" in summary and summary["comparisons"], "[smoke] Auswertung lieferte keine Metriken."
        print("\n[smoke] ERFOLG -- Treiber-Mechanik (Sandbox, Training, Misch-Anteil-Log, "
              "Diagnose, Auswertung) funktioniert.")
        ok = True
    finally:
        print("\n[smoke] Raeume Artefakte auf...", flush=True)
        remove_sandbox_dir(smoke_dir, "smoke")
        for arm in smoke_arms:
            for seed in seeds:
                name = f"{arm}_s{seed}"
                for stem in (name, f"{name}_best"):
                    for ext in (".pth", ".onnx", ".onnx.ref.txt"):
                        p = BASE_DIR / "models" / f"alphazero_{stem}{ext}"
                        if p.exists():
                            p.unlink()
                for m in (BASE_DIR / "models").glob(f"manifest_train_{name}_*.json"):
                    m.unlink()
        for f in (diag_out, result_out):
            if f.exists():
                f.unlink()
        print(f"[smoke] Aufgeraeumt. Echter data/-Ordner unveraendert "
              f"({len(list(DATA_DIR.glob('*.pkl')))} Dateien).")
    if not ok:
        raise SystemExit("[smoke] Rauchtest fehlgeschlagen.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3, 4, 5, 6])
    ap.add_argument("--out", default="evaluations/train_lambda_sweep_result.json")
    ap.add_argument("--diag-out", default="evaluations/offline_diagnose_lambda_target_frozen.json")
    ap.add_argument("--skip-training", action="store_true",
                    help="Nur Diagnose+Auswertung auf bereits vorhandenen Checkpoints.")
    ap.add_argument("--smoke", action="store_true",
                    help="Rauchtest der Treiber-Mechanik mit winzigem Sandbox-Korpus (ruehrt "
                         "data/ NICHT an, raeumt sich selbst auf) -- siehe Moduldoku.")
    ap.add_argument("--build-only", action="store_true",
                    help="Nur Split-Manifest + Hardlink-Sandbox (data_lambda_sweep/) aufbauen und "
                         "den Sample-Misch-Anteil messen, KEINE Trainingslaeufe starten. Zum "
                         "Vorbereiten VOR dem eigentlichen Sweep-Start.")
    args = ap.parse_args()

    if args.smoke:
        run_smoke()
        return

    if args.build_only and args.skip_training:
        raise SystemExit("--build-only und --skip-training schliessen sich aus.")

    if selfplay_running():
        print("[info] self_play.py laeuft parallel -- unkritisch: alle 4 Arme trainieren gegen "
              "die eingefrorene Hardlink-Sandbox (data_lambda_sweep/), data/-Wachstum wird "
              "ignoriert.", flush=True)

    file_names, n_root_q, n_total = load_or_build_split()
    n_files = len(file_names)

    if not args.skip_training:
        missing_source = [n for n in file_names if not (DATA_DIR / n).exists()]
        if missing_source:
            raise SystemExit(
                f"ABBRUCH: {len(missing_source)} Manifest-Datei(en) fehlen in {DATA_DIR} "
                f"(z.B. {missing_source[:3]}) -- {SPLIT_MANIFEST.name} passt nicht mehr zum "
                f"echten Korpus. Manuelle Pruefung noetig, KEINE automatische Neuziehung."
            )
        ensure_hardlink_mirror(file_names, SWEEP_DIR, DATA_DIR)
        verify_sandbox_consistency(file_names, SWEEP_DIR, DATA_DIR, "lambda_sweep")
        print(f"[sweep] Korpus bereit: {SWEEP_DIR} ({n_files} Dateien, Hardlinks, eingefroren, "
              f"Misch-Anteil {n_root_q/n_total*100:.2f}% von {n_total:,} Samples).")

    if args.build_only:
        print(f"\n[build-only] Fertig -- Split-Manifest + Sandbox stehen, KEIN Training gestartet. "
              f"Sample-Misch-Anteil: {n_root_q:,}/{n_total:,} = {n_root_q/n_total*100:.2f}% -- "
              f"trag diesen Wert in evaluations/PREREG_lambda_target.md Abschnitt 'Datengrundlage' "
              f"nach. Sweep spaeter starten mit: python {Path(__file__).name} --seeds ...", flush=True)
        return

    print(f"[sweep] Korpus (eingefroren, immun gegen data/-Wachstum): {n_files} Dateien | "
          f"Arme: {ARM_LAMBDAS} | Seeds: {args.seeds} | Rezept: {' '.join(RECIPE)}", flush=True)
    print(f"[sweep] {len(ARM_LAMBDAS) * len(args.seeds)} Laeufe "
          f"({len(args.seeds)} Seeds x {len(ARM_LAMBDAS)} Arme, from scratch, kein --load)\n",
          flush=True)

    if not args.skip_training:
        for seed in args.seeds:
            print(f"=== Seed {seed}: {tuple(ARM_LAMBDAS)} ===", flush=True)
            t_pair0 = time.time()
            for arm, lam in ARM_LAMBDAS.items():
                success, _ = run_training(arm, seed, SWEEP_DIR, RECIPE, lam)
                if not success:
                    raise SystemExit(f"{arm}_s{seed} fehlgeschlagen -- Sweep abgebrochen.")
            print(f"[sweep] Seed {seed} fertig nach {(time.time()-t_pair0)/60:.1f} min "
                  f"(alle {len(ARM_LAMBDAS)} Arme).\n", flush=True)

    # Diagnose+Auswertung ZUERST, Sandbox-Cleanup ALS LETZTER SCHRITT (Lektion
    # aus train_corpus_dose.py, 2026-08-01-Nachbesserung, 3. Runde: ein
    # PermissionError beim Sandbox-Cleanup darf das laengst geschriebene
    # Messergebnis nie verhindern -- Diagnose/Auswertung muss VOR jedem
    # Cleanup-Schritt laufen, egal ob das Cleanup danach klappt oder nicht).
    run_diagnose_and_eval(args.seeds, BASE_DIR / args.diag_out, BASE_DIR / args.out,
                          n_corpus_files=n_files)

    if not args.skip_training:
        remove_sandbox_dir(SWEEP_DIR, "lambda_sweep")


if __name__ == "__main__":
    main()
