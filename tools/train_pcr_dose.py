# -*- coding: utf-8 -*-
"""tools/train_pcr_dose.py -- PCR-A/B-Auswertung (Task #14), siehe
evaluations/PREREG_pcr.md fuer die vollstaendige Vorregistrierung.

Faehrt die 12 vorregistrierten FROM-SCRATCH-Traininglaeufe (6 gepaarte Seeds,
`pcrkontrolle` [klassisches Self-Play, jeder Zug Voll-Suche @600 Sims] vs.
`pcrpcr` [PCR: p=0.25 Voll-Suche, Rest Cheap-Suche @150 Sims], IDENTISCHES
Rezept, flacher Encoder), dann `tools/offline_diagnosis.py --frozen` ueber
alle 12 besten Checkpoints, dann die vorregistrierte gepaarte Auswertung
(t-Test primaer + Vorzeichentest berichtet) auf den beiden arena-validierten
Orakel-Metriken.

Vorbild: `tools/train_corpus_dose.py` (Sweep-Struktur, Hardlink-Sandbox,
Skip-Logik, gepaarte Statistik) -- UNTERSCHIED: die Quelle ist NICHT `data/`,
sondern der separate Mess-Korpus `data_pcr_ab/` (Praefixe
`selfplay_pcrkontrolle_*` / `selfplay_pcrpcr_*`, je eigener 4h-Wandzeit-Lauf
gegen `v19_2d_best`, siehe Manifeste dort), und es gibt KEINE stratifizierte
Ziehung -- jeder Arm bekommt schlicht ALLE Dateien seines Praefixes.

VORAUSSETZUNG (2026-08-02 nachgeruestet): `engine/py/neural_net.py` setzt
beim Cache-Bau `policy_weights=0` fuer Records mit `policy_target_valid=false`
(Cheap-Suche-Zuege) -- ohne diese Maske wuerde der `pcrpcr`-Arm ~75% seiner
Drafting-Entscheide mit unzuverlaessigen 150-Sim-Visit-Zielen in den
Policy-Loss speisen und das PREREG-Design ("nur der Voll-Suche-Anteil
liefert ein verlaessliches Policy-Ziel") verfehlen. Der Rauchtest (`--smoke`)
verifiziert diese Maske end-to-end gegen den echten HDF5-Cache.

Nutzung:
    python tools/train_pcr_dose.py --build-only   # Sandboxes + Quoten-Messung
    python tools/train_pcr_dose.py --seeds 1 2 3 4 5 6

`--skip-training`: nur Diagnose+Auswertung auf bereits vorhandenen
Checkpoints (Wiederaufnahme nach einem Abbruch).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import pickle
import shutil
import subprocess
import sys
import time
from math import comb
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Identisch fuer beide Arme -- siehe PREREG_pcr.md "6 gepaarte Flach-Encoder-
# Seeds je Korpus". NUR --name/--seed und der MOSAIC_DATA_DIR-Env-Override
# unterscheiden die 12 Laeufe voneinander.
RECIPE = ["--epochs", "40", "--lr", "4e-4", "--lr-schedule", "cosine",
          "--value-target-variant", "nortv", "--no-plot", "--no-snapshot"]

ORACLE_KEYS = ("prior_mass_on_oracle_top3", "kendall_tau_policy_vs_oracle_q")
SECONDARY_KEY = "value_r2_rounds_1_4"  # nur informativ (Aufloesungsgrenze ~0.015)

# Arm -> Datei-Praefix in SOURCE_DIR. `pcrkontrolle` ist die Baseline -- die
# gepaarte Differenz wird als (pcrpcr - pcrkontrolle) berichtet.
ARMS = ("pcrkontrolle", "pcrpcr")
BASELINE_ARM = "pcrkontrolle"
TREATMENT_ARM = "pcrpcr"

# Erwartete Zusammensetzung des Mess-Korpus (Stichtag 2026-08-02, siehe
# data_pcr_ab/manifest_*.json: 1170 bzw. 2100 Spiele, per_file=10) -- harter
# Abbruch bei Abweichung, analog train_corpus_dose.py.
EXPECTED_COUNTS = {"pcrkontrolle": 117, "pcrpcr": 210}

SOURCE_DIR = BASE_DIR / "data_pcr_ab"
SANDBOX_DIRS = {"pcrkontrolle": BASE_DIR / "data_pcr_kontrolle",
                "pcrpcr": BASE_DIR / "data_pcr_pcr"}
SPLIT_MANIFEST = BASE_DIR / "evaluations" / "artifacts" / "train_pcr_dose_split.json"


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


# ── Korpus-Klassifikation + PCR-Quoten-Messung ─────────────────────────────

def classify_corpus(source_dir: Path) -> dict[str, list[Path]]:
    """Gruppiert *.pkl in `source_dir` nach Arm-Praefix. Harter Abbruch bei
    Abweichung von EXPECTED_COUNTS oder bei Dateien ausserhalb der beiden
    Praefixe (anders als bei train_corpus_dose.py ist data_pcr_ab/ ein
    dedizierter Mess-Ordner -- dort hat NICHTS anderes etwas zu suchen)."""
    if not source_dir.exists():
        raise SystemExit(f"ABBRUCH: Quell-Ordner {source_dir} existiert nicht.")
    groups: dict[str, list[Path]] = {a: [] for a in ARMS}
    outside: list[str] = []
    for f in sorted(source_dir.glob("*.pkl")):
        hit = next((a for a in ARMS if f.name.startswith(f"selfplay_{a}_")), None)
        if hit is None:
            outside.append(f.name)
        else:
            groups[hit].append(f)
    if outside:
        raise SystemExit(f"ABBRUCH: {len(outside)} unerwartete Datei(en) in {source_dir} "
                         f"(z.B. {outside[:3]}) -- data_pcr_ab/ darf nur "
                         f"selfplay_pcrkontrolle_*/selfplay_pcrpcr_* enthalten.")
    actual = {a: len(files) for a, files in groups.items()}
    if actual != EXPECTED_COUNTS:
        raise SystemExit(
            f"ABBRUCH: Zusammensetzung in {source_dir} weicht vom PREREG-Stand ab.\n"
            f"  erwartet: {EXPECTED_COUNTS}\n  gefunden: {actual}\n"
            f"KEINE automatische Fortsetzung -- siehe PREREG_pcr.md."
        )
    return groups


def measure_pcr_stats(groups: dict[str, list[Path]]) -> dict:
    """Scannt BEIDE Korpora vollstaendig und misst die vorregistrierten
    Sekundaer-Kennzahlen (PREREG_pcr.md "Sekundaer/informativ"):
    - `policy_target_valid`-Quote im pcr-Korpus (Soll ~25% auf echten
      Mehr-Aktionen-Entscheiden),
    - Record-/Spielzahlen je Arm (der Mengen-Hebel des Experiments),
    - Konsistenzpruefung: der Kontroll-Korpus darf das Feld NIRGENDS tragen
      (PCR war dort aus), der pcr-Korpus muss es tragen."""
    stats: dict = {}
    for arm, files in groups.items():
        n_rec = n_field = n_true = n_multi = n_multi_true = n_root_q = 0
        game_ids = set()
        for f in files:
            with open(f, "rb") as fh:
                game_data = pickle.load(fh)
            for step in game_data:
                n_rec += 1
                game_ids.add((f.name, step.get("game_id")))
                if step.get("root_q") is not None:
                    n_root_q += 1
                v = step.get("policy_target_valid")
                if v is not None:
                    n_field += 1
                    if v:
                        n_true += 1
                    if len(step.get("valid_actions") or []) > 1:
                        n_multi += 1
                        if v:
                            n_multi_true += 1
        stats[arm] = {
            "n_files": len(files), "n_records": n_rec, "n_games": len(game_ids),
            "n_policy_target_valid_field": n_field, "n_policy_target_valid_true": n_true,
            "n_multi_action_decisions_with_field": n_multi,
            "n_multi_action_full_search": n_multi_true,
            "full_search_rate_on_decisions": (n_multi_true / n_multi) if n_multi else None,
            "n_records_with_root_q": n_root_q,
        }
    if stats[BASELINE_ARM]["n_policy_target_valid_field"] != 0:
        raise SystemExit("ABBRUCH: Kontroll-Korpus traegt policy_target_valid-Felder -- "
                         "PCR war dort offenbar AN, das verletzt das Arm-Design (PREREG_pcr.md).")
    if stats[TREATMENT_ARM]["n_policy_target_valid_field"] == 0:
        raise SystemExit("ABBRUCH: pcr-Korpus traegt KEINE policy_target_valid-Felder -- "
                         "PCR war dort offenbar AUS, das verletzt das Arm-Design (PREREG_pcr.md).")
    return stats


def load_or_build_split() -> dict:
    """Persistiert Dateilisten + PCR-Quoten-Messung einmalig nach
    SPLIT_MANIFEST (identisches Wiederaufnahme-Prinzip wie
    train_corpus_dose.py::load_or_build_split)."""
    if SPLIT_MANIFEST.exists():
        blob = json.loads(SPLIT_MANIFEST.read_text(encoding="utf-8"))
        counts = ", ".join(f"{a}: {len(blob['files'][a])} Dateien" for a in ARMS)
        print(f"[split] Wiederverwendet aus {SPLIT_MANIFEST.name} ({counts}).")
        return blob

    groups = classify_corpus(SOURCE_DIR)
    print(f"[split] Messe PCR-Quoten ueber {sum(len(v) for v in groups.values())} Dateien "
          f"(voller Scan, einmalig) ...", flush=True)
    t0 = time.time()
    stats = measure_pcr_stats(groups)
    rate = stats[TREATMENT_ARM]["full_search_rate_on_decisions"]
    print(f"[split] pcr-Korpus: Voll-Suche-Quote auf Mehr-Aktionen-Entscheiden = "
          f"{rate*100:.1f}% (Soll ~25%) -- {time.time()-t0:.1f}s.", flush=True)

    manifest = {
        "expected_counts": EXPECTED_COUNTS,
        "files": {a: [f.name for f in groups[a]] for a in ARMS},
        "pcr_stats": stats,
    }
    SPLIT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    SPLIT_MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[split] Neu gebaut -> {SPLIT_MANIFEST}")
    return manifest


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
        raise SystemExit(f"ABBRUCH: {label}-Sandbox {target_dir} existiert nicht.")
    actual = sorted(p.name for p in target_dir.glob("*.pkl"))
    expected = sorted(file_names)
    if actual != expected:
        missing = sorted(set(expected) - set(actual))
        extra = sorted(set(actual) - set(expected))
        raise SystemExit(
            f"ABBRUCH: {label}-Sandbox {target_dir} weicht vom Split-Manifest ab "
            f"(fehlend: {len(missing)} z.B. {missing[:3]}, ueberzaehlig: {len(extra)} "
            f"z.B. {extra[:3]})."
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
            f"Hardlinks (mehr) auf die Quelle (z.B. {mismatched[:3]})."
        )
    print(f"[check] {label}-Sandbox {target_dir}: {len(file_names)} Dateien, "
          f"Anzahl+Hardlink-Identitaet OK.", flush=True)


def remove_sandbox_dir(d: Path, label: str) -> None:
    """Fehlertolerant, identisch zu `train_corpus_dose.py::remove_sandbox_dir`."""
    assert d.resolve() != SOURCE_DIR.resolve() and d.resolve() != (BASE_DIR / "data").resolve(), \
        f"SICHERHEITSSTOPP: remove_sandbox_dir() darf nie Quell-Daten loeschen ({d})."
    if not d.exists():
        return
    try:
        shutil.rmtree(d)
        print(f"[cleanup] {label}-Sandbox entfernt: {d}", flush=True)
    except OSError as e:
        print(f"[cleanup][WARNUNG] {label}-Sandbox {d} konnte nicht vollstaendig entfernt "
              f"werden ({e!r}) -- KEIN Abbruch (Messergebnis ist laengst geschrieben).", flush=True)


# ── Trainings-Sweep ──────────────────────────────────────────────────────

def run_training(arm: str, seed: int, data_dir_override: Path, recipe: list[str]) -> bool:
    name = f"{arm}_s{seed}"
    ckpt = BASE_DIR / "models" / f"alphazero_{name}_best.pth"
    if not ckpt.exists():
        ckpt = BASE_DIR / "models" / f"alphazero_{name}.pth"
    if ckpt.exists():
        print(f"  [skip] {name}: Checkpoint existiert schon", flush=True)
        return True
    cmd = ([sys.executable, "-X", "faulthandler", "-u", str(BASE_DIR / "train.py"),
            "--name", name, "--seed", str(seed)] + recipe)
    env = os.environ.copy()
    env["MOSAIC_DATA_DIR"] = str(data_dir_override)
    print(f"  [run ] {name}  [MOSAIC_DATA_DIR={data_dir_override}]  ({' '.join(cmd[5:])})", flush=True)
    t0 = time.time()
    # Bewusst OHNE capture_output: Live-Ausgabe bleibt sichtbar (Memory
    # "Agent background-process discipline").
    r = subprocess.run(cmd, cwd=str(BASE_DIR), env=env)
    dt = time.time() - t0
    if r.returncode != 0:
        print(f"  [FAIL] {name} rc={r.returncode} nach {dt/60:.1f} min", flush=True)
        return False
    print(f"  [done] {name} nach {dt/60:.1f} min", flush=True)
    return True


def resolve_checkpoint_name(name: str) -> str:
    if (BASE_DIR / "models" / f"alphazero_{name}_best.pth").exists():
        return f"{name}_best"
    return name


def run_diagnose_and_eval(seeds: list[int], diag_out: Path, result_out: Path,
                           pcr_stats: dict | None) -> dict:
    """Diagnostiziert alle 12 Checkpoints, wertet dann (pcrpcr - pcrkontrolle)
    gepaart je Seed auf den beiden Orakel-Metriken aus (primaer, t-Test) und
    wendet die PREREG-Abbruch-/Fortsetzungsregel deskriptiv an."""
    models = ([resolve_checkpoint_name(f"{BASELINE_ARM}_s{s}") for s in seeds]
              + [resolve_checkpoint_name(f"{TREATMENT_ARM}_s{s}") for s in seeds])

    print(f"\n[diag] Diagnose (frozen, Orakel-Metriken + value_r2) ueber {len(models)} "
          f"Checkpoints...", flush=True)
    r = subprocess.run([sys.executable, "-u", str(BASE_DIR / "tools" / "offline_diagnosis.py"),
                        "--model", *models, "--frozen", "--out", str(diag_out)],
                       cwd=str(BASE_DIR))
    if r.returncode != 0:
        raise SystemExit("offline_diagnosis fehlgeschlagen -- siehe Ausgabe oben.")

    blob = json.loads(diag_out.read_text(encoding="utf-8"))
    by_name = {e["model"]: e for e in blob["results"]}

    metric_keys = ORACLE_KEYS + (SECONDARY_KEY,)
    eval_arms = (BASELINE_ARM, TREATMENT_ARM)
    vals: dict[str, dict[int, dict]] = {a: {} for a in eval_arms}
    for arm in eval_arms:
        for s in seeds:
            e = by_name.get(resolve_checkpoint_name(f"{arm}_s{s}"))
            if e is not None:
                vals[arm][s] = {k: e.get(k) for k in metric_keys}

    print("\n" + "=" * 78)
    print("  PCR (Task #14): pcrpcr vs. pcrkontrolle -- gepaarte Auswertung (PREREG_pcr.md)")
    print("=" * 78)

    summary: dict = {"seeds": seeds, "baseline_arm": BASELINE_ARM, "treatment_arm": TREATMENT_ARM,
                     "pcr_stats": pcr_stats, "metrics": {}}
    for mk in metric_keys:
        common = sorted(s for s in seeds
                        if s in vals[TREATMENT_ARM] and s in vals[BASELINE_ARM]
                        and vals[TREATMENT_ARM][s].get(mk) is not None
                        and vals[BASELINE_ARM][s].get(mk) is not None)
        diffs = [vals[TREATMENT_ARM][s][mk] - vals[BASELINE_ARM][s][mk] for s in common]
        label = "PRIMAER" if mk in ORACLE_KEYS else "sekundaer/informativ"
        print(f"\nMetrik: {mk} ({label})")
        print(f"{'Seed':<6}{'kontrolle':>14}{'pcr':>14}{'Diff(pcr-kont)':>18}")
        for s in common:
            bv, tv = vals[BASELINE_ARM][s][mk], vals[TREATMENT_ARM][s][mk]
            print(f"{s:<6}{bv:14.4f}{tv:14.4f}{tv - bv:+18.4f}")
        if not diffs:
            print("  keine auswertbaren Paare")
            summary["metrics"][mk] = {"n": 0}
            continue
        mean_diff = sum(diffs) / len(diffs)
        pos = sum(1 for d in diffs if d > 0)
        neg = sum(1 for d in diffs if d < 0)
        p_sign = sign_test_p(pos, neg)
        t_stat, p_ttest, df = paired_ttest_p(diffs)
        print(f"  Ø Differenz (pcr-kontrolle): {mean_diff:+.4f}  (n={len(diffs)})")
        print(f"  Richtung: {pos}x pcr besser / {neg}x kontrolle besser -> "
              f"Vorzeichentest p={p_sign:.4f}")
        print(f"  Gepaarter t-Test: t={t_stat:.3f}, df={df}, p={p_ttest:.4f}")
        summary["metrics"][mk] = {
            "n": len(diffs), "mean_diff": mean_diff, "n_positive": pos, "n_negative": neg,
            "sign_test_p": p_sign, "t_stat": t_stat, "df": df, "ttest_p": p_ttest,
            "per_seed": {str(s): {BASELINE_ARM: vals[BASELINE_ARM][s][mk],
                                  TREATMENT_ARM: vals[TREATMENT_ARM][s][mk],
                                  "diff": vals[TREATMENT_ARM][s][mk] - vals[BASELINE_ARM][s][mk]}
                         for s in common},
        }

    # Abbruch-/Fortsetzungsregel (PREREG_pcr.md, VORAB festgelegt) -- rein
    # deskriptiv angewendet, der Mensch entscheidet trotzdem.
    oracle_metrics = [summary["metrics"].get(mk, {}) for mk in ORACLE_KEYS]
    if all(m.get("n", 0) >= 2 for m in oracle_metrics):
        better = [m["mean_diff"] > 0 for m in oracle_metrics]
        sig = [m["ttest_p"] < 0.05 for m in oracle_metrics]
        if not any(better):
            verdict = ("pcr auf BEIDEN Orakel-Metriken gepaart schlechter/gleich -- der Tausch "
                       "Suchqualitaet-gegen-Menge lohnt sich fuer dieses Design NICHT. Kein "
                       "Arena-Gating, Task #14 wird nicht produktiv eingesetzt (PREREG_pcr.md).")
        elif all(better) and any(s for b, s in zip(better, sig) if b):
            verdict = ("pcr auf BEIDEN Orakel-Metriken gepaart besser UND p<0.05 auf mindestens "
                       "einer -- STARKER Befund fuer Task #14. Arena-Gating hat hohe Prioritaet, "
                       "Zwei-Kampagnen-Produktionsbetrieb ab v20 vorbereiten (PREREG_pcr.md).")
        else:
            verdict = ("pcr auf MINDESTENS EINER Orakel-Metrik gepaart besser -- das Arena-Gating "
                       "(bester pcr- vs. bester kontrolle-Checkpoint, 400 gepaarte Partien) "
                       "lohnt sich als naechster Schritt (PREREG_pcr.md).")
    else:
        verdict = "Nicht alle Orakel-Metriken auswertbar -- manuelle Pruefung noetig."
    print(f"\n{'=' * 78}\nVERDIKT (automatisch nach PREREG_pcr.md-Regel): {verdict}\n{'=' * 78}")
    summary["verdict"] = verdict

    result_out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nErgebnis: {result_out}")
    return summary


# ── Rauchtest ────────────────────────────────────────────────────────────

def run_smoke() -> None:
    """Testet die Treiber-Mechanik end-to-end mit winzigen, EIGENEN Sandbox-
    Korpora (je 2 Dateien pro Arm, 1 Seed, 2 Epochen) -- und verifiziert
    ZUSAETZLICH die PCR-Policy-Maske gegen den echten HDF5-Cache: im
    pcr-Sandbox-Cache muss die Zahl der Samples mit policy_weight>0 exakt
    der Zahl der Drafting-Nicht-Start-Records MINUS der als
    `policy_target_valid=false` markierten entsprechen. Raeumt alle Artefakte
    im finally-Block auf."""
    global BASELINE_ARM, TREATMENT_ARM
    print("[smoke] Rauchtest: 1 Seed, 2 Arme, je 2 Sandbox-Dateien, 2 Epochen "
          "+ Policy-Masken-Verifikation gegen den HDF5-Cache.\n", flush=True)
    groups = classify_corpus(SOURCE_DIR)
    smoke_names = {a: [f.name for f in groups[a][:2]] for a in ARMS}
    smoke_dirs = {a: BASE_DIR / f"data_pcr_smoke_{a}" for a in ARMS}
    smoke_recipe = ["--epochs", "2", "--lr", "4e-4", "--lr-schedule", "cosine",
                     "--value-target-variant", "nortv", "--no-plot", "--no-snapshot"]
    seeds = [1]
    diag_out = BASE_DIR / "evaluations" / "artifacts" / "_smoke_pcr_dose_diag.json"
    result_out = BASE_DIR / "evaluations" / "artifacts" / "_smoke_pcr_dose_result.json"
    ok = False
    try:
        for a in ARMS:
            ensure_hardlink_mirror(smoke_names[a], smoke_dirs[a], SOURCE_DIR)
            verify_sandbox_consistency(smoke_names[a], smoke_dirs[a], SOURCE_DIR, f"smoke_{a}")

        # Erwartete Maskenzahlen direkt aus den pkl-Dateien des pcr-Arms
        # (VOR dem Training, unabhaengig vom Cache-Baucode berechnet).
        n_draft = n_masked = 0
        for name in smoke_names[TREATMENT_ARM]:
            with open(SOURCE_DIR / name, "rb") as fh:
                for step in pickle.load(fh):
                    phase = step["state"].get("phase")
                    is_start = any(pe["action"].get("is_start") for pe in step["policy"])
                    if phase == "drafting" and not is_start:
                        n_draft += 1
                        if step.get("policy_target_valid") is False:
                            n_masked += 1
        expected_polw_sum = n_draft - n_masked
        print(f"[smoke] pcr-Sandbox: {n_draft} Drafting-Records, davon {n_masked} "
              f"cheap-maskiert -> erwartete polw-Summe {expected_polw_sum}.", flush=True)

        for seed in seeds:
            for a in ARMS:
                if not run_training(f"smoke_{a}", seed, smoke_dirs[a], smoke_recipe):
                    raise SystemExit(f"[smoke] smoke_{a}-Lauf fehlgeschlagen.")

        # Masken-Verifikation gegen die vom Training gebauten HDF5-Caches
        # (Train- UND Val-Split zusammen muessen die Gesamtzahlen ergeben).
        import h5py  # lokal, wie in neural_net.py ueblich
        import numpy as np
        total_polw = 0.0
        cache_files = sorted(smoke_dirs[TREATMENT_ARM].glob("*.h5"))
        if not cache_files:
            raise SystemExit(f"[smoke] Kein HDF5-Cache in {smoke_dirs[TREATMENT_ARM]} gefunden.")
        for cf in cache_files:
            with h5py.File(cf, "r") as hf:
                total_polw += float(np.asarray(hf["policy_weights"]).sum())
        if int(round(total_polw)) != expected_polw_sum:
            raise SystemExit(f"[smoke] POLICY-MASKEN-FEHLER: polw-Summe im pcr-Cache = "
                              f"{total_polw:.0f}, erwartet {expected_polw_sum} "
                              f"({n_masked} von {n_draft} Drafting-Records cheap-maskiert).")
        print(f"[smoke] Policy-Masken-Check OK: polw-Summe {total_polw:.0f} == "
              f"{expected_polw_sum} (ueber {len(cache_files)} Cache-Datei(en)).", flush=True)

        smoke_seeds = seeds
        orig_arms = (BASELINE_ARM, TREATMENT_ARM)
        BASELINE_ARM, TREATMENT_ARM = "smoke_pcrkontrolle", "smoke_pcrpcr"
        try:
            summary = run_diagnose_and_eval(smoke_seeds, diag_out, result_out, pcr_stats=None)
        finally:
            BASELINE_ARM, TREATMENT_ARM = orig_arms
        assert "verdict" in summary, "[smoke] Auswertung lieferte kein Verdikt."
        print("\n[smoke] ERFOLG -- Treiber-Mechanik + PCR-Policy-Maske funktionieren.")
        ok = True
    finally:
        print("\n[smoke] Raeume Artefakte auf...", flush=True)
        for a in ARMS:
            remove_sandbox_dir(smoke_dirs[a], f"smoke_{a}")
        for a in ARMS:
            for seed in seeds:
                name = f"smoke_{a}_s{seed}"
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
        print("[smoke] Aufgeraeumt.")
    if not ok:
        raise SystemExit("[smoke] Rauchtest fehlgeschlagen.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3, 4, 5, 6])
    ap.add_argument("--out", default="evaluations/artifacts/train_pcr_dose_result.json")
    ap.add_argument("--diag-out", default="evaluations/artifacts/offline_diagnosis_pcr_dose_frozen.json")
    ap.add_argument("--skip-training", action="store_true",
                    help="Nur Diagnose+Auswertung auf bereits vorhandenen Checkpoints.")
    ap.add_argument("--smoke", action="store_true",
                    help="Rauchtest inkl. PCR-Policy-Masken-Verifikation -- siehe Moduldoku.")
    ap.add_argument("--build-only", action="store_true",
                    help="Nur Split-Manifest + beide Hardlink-Sandboxes aufbauen und die "
                         "PCR-Quoten messen, KEINE Trainingslaeufe starten.")
    args = ap.parse_args()

    if args.smoke:
        run_smoke()
        return
    if args.build_only and args.skip_training:
        raise SystemExit("--build-only und --skip-training schliessen sich aus.")

    manifest = load_or_build_split()
    files_by_arm = manifest["files"]

    if not args.skip_training:
        for a in ARMS:
            missing = [n for n in files_by_arm[a] if not (SOURCE_DIR / n).exists()]
            if missing:
                raise SystemExit(f"ABBRUCH: {len(missing)} Manifest-Datei(en) fehlen in "
                                 f"{SOURCE_DIR} (z.B. {missing[:3]}).")
            ensure_hardlink_mirror(files_by_arm[a], SANDBOX_DIRS[a], SOURCE_DIR)
            verify_sandbox_consistency(files_by_arm[a], SANDBOX_DIRS[a], SOURCE_DIR, a)
        print(f"[sweep] Korpora bereit: "
              f"{', '.join(f'{a}={len(files_by_arm[a])} Dateien' for a in ARMS)} "
              f"(Hardlinks, eingefroren).")

    if args.build_only:
        rate = manifest["pcr_stats"][TREATMENT_ARM]["full_search_rate_on_decisions"]
        print(f"\n[build-only] Fertig -- Sandboxes stehen, KEIN Training gestartet. "
              f"Voll-Suche-Quote pcr-Korpus: {rate*100:.1f}% (Soll ~25%).", flush=True)
        return

    print(f"[sweep] Seeds: {args.seeds} | Rezept: {' '.join(RECIPE)}", flush=True)
    print(f"[sweep] {2 * len(args.seeds)} Laeufe ({len(args.seeds)} Seeds x 2 Arme, "
          f"from scratch, flacher Encoder, kein --load)\n", flush=True)

    if not args.skip_training:
        for seed in args.seeds:
            print(f"=== Seed {seed}: Paar (pcrkontrolle, pcrpcr) ===", flush=True)
            t_pair0 = time.time()
            for a in ARMS:
                if not run_training(a, seed, SANDBOX_DIRS[a], RECIPE):
                    raise SystemExit(f"{a}_s{seed} fehlgeschlagen -- Sweep abgebrochen.")
            print(f"[sweep] Seed {seed} fertig nach {(time.time()-t_pair0)/60:.1f} min "
                  f"(beide Arme).\n", flush=True)

    # Diagnose+Auswertung ZUERST, Sandbox-Cleanup ALS LETZTER SCHRITT
    # (Lektion aus train_corpus_dose.py, 2026-08-01-Nachbesserung).
    run_diagnose_and_eval(args.seeds, BASE_DIR / args.diag_out, BASE_DIR / args.out,
                          pcr_stats=manifest.get("pcr_stats"))

    if not args.skip_training:
        for a in ARMS:
            remove_sandbox_dir(SANDBOX_DIRS[a], a)


if __name__ == "__main__":
    main()
