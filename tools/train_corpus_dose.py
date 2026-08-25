# -*- coding: utf-8 -*-
"""tools/train_corpus_dose.py -- Korpus-Dosis-Wirkungs-Vorstudie (Task #14-
Vorstudie), siehe evaluations/PREREG_corpus_dose.md fuer die vollstaendige
Vorregistrierung.

Faehrt die 12 vorregistrierten FROM-SCRATCH-Traininglaeufe (6 gepaarte
Seeds, `voll` [voller Korpus, 900 Dateien] vs. `halb` [stratifizierte
Haelfte, 450 Dateien, Zusammensetzungsverhaeltnis je Versions-Praefix
erhalten], IDENTISCHES Rezept bis auf Korpusgroesse/`--seed`), dann
`tools/offline_diagnosis.py --frozen` ueber alle 12 besten Checkpoints, dann
die vorregistrierte gepaarte Auswertung (t-Test + Vorzeichentest) auf den
beiden arena-validierten Orakel-Metriken.

Vorbild: `tools/train_2d_vs_flat_fs.py` (Sweep-Struktur, Statistikcode,
Skip-Logik, [mem]-Instrumentierung via `-X faulthandler`), aber die Arme
unterscheiden sich hier durch die KORPUSGROESSE statt durch `--encoder`.

Technische Umsetzung der Korpus-Teilmenge (siehe PREREG Abschnitt
"Technische Umsetzung"): `train.py` hat keine Datei-LISTEN-Option, nur
`--train-file-limit` (ein reines Zaehler-Sample mit fest verdrahtetem,
NICHT stratifiziertem Seed, Task #69) -- das reicht fuer eine stratifizierte
Ziehung nicht. Geloest ueber eine additive Env-Var `MOSAIC_DATA_DIR` in
`config.py` (Default unveraendert): BEIDE Arme bekommen einen SEPARATEN,
EINGEFRORENEN Ordner mit HARDLINKS (`os.link`, kein Speicherplatz-/
Kopieraufwand) -- `data_dose_voll/` (alle 900 Manifest-Dateien) und
`data_dose_halb/` (die 450 gezogenen Dateien). `train.py` sieht bei BEIDEN
Armen also nie den echten `data/`-Ordner direkt, sondern nur den
eingefrorenen Split-Manifest-Stand vom 2026-08-01 -- neues Self-Play
(z.B. v19), das PARALLEL neue Dateien nach `data/` schreibt, ist fuer den
Sweep unsichtbar UND unschaedlich (2026-08-01 Nachbesserung: vorher trainierte
der `voll`-Arm direkt gegen `data/`, das haette bei parallelem Self-Play den
Korpus zwischen den 6 `voll`-Seeds inkonsistent gemacht). Der echte
`data/`-Ordner wird NIE verschoben/umbenannt/geloescht, nur GELESEN, um die
beiden Sandboxes einmalig aufzubauen (Memory
`project_onedrive_file_disappearance`: `data/` liegt unter OneDrive-Sync).
`train.py`/`engine/py/neural_net.py` bleiben unangetastet.

Nutzung:
    python tools/train_corpus_dose.py --seeds 1 2 3 4 5 6

`--skip-training`: nur Diagnose+Auswertung auf bereits vorhandenen
Checkpoints (Wiederaufnahme nach einem Abbruch -- `run_training`
ueberspringt ohnehin bereits vorhandene `*_best.pth`/`*.pth`, das Flag
spart nur den Sweep-Loop selbst; die Sandboxes werden dann gar nicht erst
gebraucht/geprueft, die Diagnose laeuft nur gegen Checkpoints +
`evaluations/frozen_eval_set.pkl`).

`--smoke`: Rauchtest der Treiber-Mechanik (Hardlink-Sandbox, Skip-Logik,
Diagnose-Aufruf, gepaarte Auswertung) mit winzigen Korpora (3 `voll`- / 2
`halb`-Dateien, 2 Seeds, 2 Epochen statt 40) -- ruehrt den echten
`data/`-Ordner NICHT an (eigene Sandbox-Ordner), raeumt alle Artefakte
(Checkpoints, Manifeste, Diagnose-/Ergebnis-JSON, Sandbox-Ordner) am Ende
selbst auf.
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import random
import shutil
import subprocess
import sys
import time
from math import comb
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Identisch fuer beide Arme -- siehe PREREG_corpus_dose.md "Rezept". NUR
# --name/--seed und der MOSAIC_DATA_DIR-Env-Override unterscheiden die 12
# Laeufe voneinander.
RECIPE = ["--epochs", "40", "--lr", "4e-4", "--lr-schedule", "cosine",
          "--value-target-variant", "nortv", "--no-plot", "--no-snapshot"]

ORACLE_KEYS = ("prior_mass_on_oracle_top3", "kendall_tau_policy_vs_oracle_q")

# Fester Ziehungs-Seed fuer die stratifizierte Halb-Auswahl -- siehe
# PREREG_corpus_dose.md "Stratifizierte Ziehung". Unabhaengig von train.py's
# eigenen Seeds (Val-Split 20260707, Task-#69-Subsample 20260708).
STRATIFY_SEED = 20260801

# Erwartete Zusammensetzung DES MESSFENSTERS (PREREG-Grundlage, Stichtag
# 2026-08-01) -- diese drei Praefixe UND NUR diese bilden das Universum
# dieser Vorstudie. Ein Abweichen INNERHALB des Fensters (z.B. eine
# geloeschte v17-Datei) bricht die Ziehung hart ab statt still auf
# veraenderter Grundgesamtheit zu ziehen. Dateien AUSSERHALB des Fensters
# (andere Praefixe, z.B. `v19` aus der parallel laufenden Self-Play-Kampagne)
# sind KEIN Abbruchgrund -- sie gehoeren per Definition nicht zum Universum
# und werden von classify_corpus() nur gezaehlt/gemeldet, siehe dort.
EXPECTED_COUNTS = {"v15": 100, "v16": 200, "v17": 600}
VERSION_PREFIXES = tuple(EXPECTED_COUNTS.keys())

DATA_DIR = BASE_DIR / "data"
VOLL_DIR = BASE_DIR / "data_dose_voll"
HALB_DIR = BASE_DIR / "data_dose_halb"
SPLIT_MANIFEST = BASE_DIR / "evaluations" / "artifacts" / "train_corpus_dose_split.json"


def selfplay_running() -> bool:
    """True, wenn ein self_play.py-Prozess laeuft. Seit der 2026-08-01-
    Nachbesserung KEIN Abbruchgrund mehr (beide Arme trainieren gegen
    eingefrorene Hardlink-Sandboxes, die data/-Wachstum ignorieren) -- nur
    noch eine informative Konsolenmeldung in `main()`."""
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
    `train_2d_vs_flat_fs.py::sign_test_p`/`train_seed_sweep.py::sign_test_p`."""
    n = n_pos + n_neg
    if n == 0:
        return 1.0
    lo, hi = min(n_pos, n_neg), max(n_pos, n_neg)
    p_le = sum(comb(n, k) for k in range(0, lo + 1)) / (2 ** n)
    p_ge = sum(comb(n, k) for k in range(hi, n + 1)) / (2 ** n)
    return min(1.0, 2 * min(p_le, p_ge))


# ── Gepaarter t-Test ohne scipy (identischer Code wie
# `tools/train_2d_vs_flat_fs.py`, Praezedenzfall PREREG_ownership_gumbel.md)
# ─────────────────────────────────────────────────────────────────────────

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


# ── Korpus-Stratifizierung ─────────────────────────────────────────────────

def classify_corpus(data_dir: Path) -> tuple[dict[str, list[Path]], int]:
    """Gruppiert *.pkl in `data_dir` nach Versions-Praefix -- NUR v15/v16/v17
    bilden das Messfenster/Universum dieser Vorstudie (PREREG_corpus_dose.md
    "Stratifizierte Ziehung" + Einschraenkung 3: eingefrorenes v15-v17-
    Fenster, spaetere Generationen sind PER DEFINITION ausserhalb).

    2026-08-01 Nachbesserung (2. Runde): Dateien mit anderen Praefixen
    (z.B. `selfplay_v19_*` aus der parallel laufenden v19-Self-Play-Kampagne)
    sind KEIN Fehler mehr -- sie liegen ausserhalb des Universums und werden
    nur gezaehlt/gemeldet (Info-Zeile), nicht als Abbruchgrund behandelt.
    Der harte Abbruch bleibt NUR INNERHALB des Universums bestehen (siehe
    `verify_expected_composition`): weichen die v15/v16/v17-Zaehlungen selbst
    von 600/200/100 ab, ist das weiterhin ein Abbruchgrund (z.B. wenn jemand
    versehentlich v17-Dateien geloescht haette).

    Rueckgabe: (groups [nur v15/v16/v17], n_outside_ignoriert)."""
    groups: dict[str, list[Path]] = {p: [] for p in VERSION_PREFIXES}
    outside: list[str] = []
    for f in sorted(data_dir.glob("*.pkl")):
        hit = next((p for p in VERSION_PREFIXES if f.name.startswith(f"selfplay_{p}_")), None)
        if hit is None:
            outside.append(f.name)
        else:
            groups[hit].append(f)
    if outside:
        # Praefix rein informativ aus dem Dateinamen extrahiert (Schema
        # `selfplay_<praefix>_<datum>_<zeit>_g<n>.pkl`) -- faellt bei
        # unbekanntem Namensschema robust auf "unbekannt" zurueck statt zu
        # crashen, das ist hier nur eine Konsolenmeldung, kein Kontrollfluss.
        found_prefixes = sorted({
            n.split("_")[1] for n in outside if n.startswith("selfplay_") and len(n.split("_")) > 1
        }) or ["unbekannt"]
        print(f"[split] {len(outside)} Datei(en) ausserhalb des Messfensters ignoriert "
              f"(Praefix(e): {', '.join(found_prefixes)} -- laeuft parallel, nicht Teil des "
              f"v15/v16/v17-Universums) -- kein Abbruch.", flush=True)
    return groups, len(outside)


def verify_expected_composition(groups: dict[str, list[Path]]) -> None:
    """Harter Abbruch NUR bei Abweichung INNERHALB des v15/v16/v17-Universums
    (siehe classify_corpus) -- Dateien ausserhalb (z.B. v19) sind bereits vor
    diesem Aufruf herausgefiltert und loesen hier nichts mehr aus. Ein
    Treffer hier bedeutet also eine Aenderung AN v15/v16/v17 selbst (z.B.
    versehentlich geloeschte/umbenannte Dateien), nicht neues Self-Play einer
    anderen Generation."""
    actual = {p: len(files) for p, files in groups.items()}
    if actual != EXPECTED_COUNTS:
        raise SystemExit(
            f"ABBRUCH: v15/v16/v17-Zusammensetzung in {DATA_DIR} weicht vom PREREG-Stand ab.\n"
            f"  erwartet: {EXPECTED_COUNTS}\n"
            f"  gefunden: {actual}\n"
            f"(Dateien ausserhalb dieses Universums, z.B. v19, sind bereits ausgeschlossen und "
            f"NICHT die Ursache.) KEINE automatische Neuziehung -- siehe PREREG_corpus_dose.md "
            f"Einschraenkung 3. Manuelle Entscheidung noetig (neue Vorregistrierung schreiben)."
        )


def stratified_halb_split(groups: dict[str, list[Path]]) -> tuple[list[Path], list[Path]]:
    """Zieht je Praefix GENAU DIE HAELFTE (fester Seed STRATIFY_SEED) --
    erhaelt das Zusammensetzungsverhaeltnis exakt (300 v17 + 100 v16 + 50
    v15 von 600+200+100). Rueckgabe (halb, ausgeschlossen)."""
    rng = random.Random(STRATIFY_SEED)
    halb: list[Path] = []
    rest: list[Path] = []
    for prefix in VERSION_PREFIXES:
        pool = sorted(groups[prefix])
        rng.shuffle(pool)
        n_half = len(pool) // 2
        halb.extend(pool[:n_half])
        rest.extend(pool[n_half:])
    return sorted(halb), sorted(rest)


def load_or_build_split() -> tuple[list[str], list[str]]:
    """Persistiert die Ziehung einmalig nach SPLIT_MANIFEST -- ein
    Wiederaufnahme-Lauf (z.B. nach Abbruch waehrend der 12 Laeufe) verwendet
    dann garantiert denselben Split, statt bei jedem Skriptstart neu (wenn
    auch deterministisch) zu ziehen. Das Manifest friert BEIDE Dateimengen
    ein (`voll_files` = alle 900 zum Stichtag, `halb_files` = die 450
    gezogenen) -- spaeter dazukommende Dateien (neues Self-Play) stehen NICHT
    im Manifest und werden dadurch fuer den gesamten Sweep unsichtbar, auch
    fuer den `voll`-Arm. Gibt (halb_files, voll_files) zurueck (nur Namen,
    kein Pfad -- VOLL_DIR/HALB_DIR werden relativ dazu befuellt)."""
    if SPLIT_MANIFEST.exists():
        blob = json.loads(SPLIT_MANIFEST.read_text(encoding="utf-8"))
        print(f"[split] Wiederverwendet aus {SPLIT_MANIFEST.name} "
              f"(Seed {blob['stratify_seed']}, {len(blob['voll_files'])} Voll-/"
              f"{len(blob['halb_files'])} Halb-Dateien).")
        return blob["halb_files"], blob["voll_files"]

    groups, n_outside = classify_corpus(DATA_DIR)
    verify_expected_composition(groups)
    halb, excluded = stratified_halb_split(groups)
    voll = sorted(halb + excluded)
    manifest = {
        "stratify_seed": STRATIFY_SEED,
        "expected_counts": EXPECTED_COUNTS,
        "voll_files": [p.name for p in voll],
        "halb_files": [p.name for p in halb],
        "excluded_files": [p.name for p in excluded],
        "n_halb": len(halb),
        "n_voll": len(voll),
        "n_outside_window_ignored_at_build_time": n_outside,
    }
    SPLIT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    SPLIT_MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[split] Neu gezogen (Seed {STRATIFY_SEED}): {len(halb)} von "
          f"{manifest['n_voll']} Dateien -> {SPLIT_MANIFEST}")
    for prefix in VERSION_PREFIXES:
        n = sum(1 for p in halb if p.name.startswith(f"selfplay_{prefix}_"))
        print(f"   {prefix}: {n} von {EXPECTED_COUNTS[prefix]}")
    return manifest["halb_files"], manifest["voll_files"]


def ensure_hardlink_mirror(file_names: list[str], target_dir: Path, source_dir: Path) -> None:
    """Baut `target_dir` als HARDLINK-Spiegel der uebergebenen Dateinamen aus
    `source_dir` auf -- idempotent (raeumt ueberzaehlige/veraltete Eintraege
    zuerst auf). Ruehrt NIE die Originaldateien an: `os.link` legt nur einen
    zusaetzlichen Verzeichniseintrag an (NTFS-Referenzzaehler +1), das
    Loeschen eines Hardlinks entfernt nur DIESEN Eintrag, nie den Inhalt."""
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
    """Prueft, dass `target_dir` exakt der eingefrorene Hardlink-Spiegel von
    `file_names` (aus dem Split-Manifest) ist -- (1) Anzahl/Namen exakt wie
    im Manifest, (2) je Datei Hardlink-IDENTITAET gegen `source_dir` (data/)
    ueber `os.stat().st_ino`: Hardlinks auf NTFS teilen sich den physischen
    Datei-Index (File ID), ein Treffer beweist also, dass die Sandbox wirklich
    denselben Byte-Inhalt referenziert und nicht z.B. nach einer manuellen
    Aufraeumaktion nur zufaellig gleich benannt ist. Volle Pruefung (nicht
    nur Stichprobe, wie urspruenglich vom Koordinator vorgeschlagen) -- bei
    <=900 Dateien vernachlaessigbare Kosten (Millisekunden), lohnt sich fuer
    diese Sicherheitsgarantie, gerade weil sie den Selfplay-Hartabbruch
    ersetzt (siehe Modul-/main()-Kommentar 2026-08-01-Nachbesserung)."""
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
    """Entfernt eine Hardlink-Sandbox samt HDF5-Cache (`train.py`/
    `MosaicDataset` legt den Cache INNERHALB des Verzeichnisses an, auf das
    `MOSAIC_DATA_DIR` zeigt -- `rmtree` statt gezieltem `*.pkl`-Unlink+`rmdir`,
    sonst schlaegt `rmdir()` mit WinError 145 [Verzeichnis nicht leer] fehl).
    Assert als Sicherheitsnetz: `d` darf NIE der echte `data/`-Ordner sein --
    diese Funktion loescht rekursiv, ein Vertipper hier waere sonst
    katastrophal (Memory `project_onedrive_file_disappearance`).

    FEHLERTOLERANT (2026-08-01 Nachbesserung, 3. Runde): `shutil.rmtree` kann
    unter Windows mit `PermissionError` scheitern, wenn irgendein Prozess
    (Explorer, ein haengender Dateihandle, Virenscanner) noch eine Datei in
    `d` offen haelt. Das ist reines Aufraeumen NACH dem eigentlichen Sweep --
    ein haengendes Handle darf niemals ein bereits fertiges Messergebnis
    verhindern (Praezedenzfall: genau das brach den ersten echten Sweep-Lauf,
    `run_diagnose_and_eval` lief nie durch, musste per `--skip-training`
    nachgeholt werden). Deshalb: Warnung statt Absturz, Aufruf-Reihenfolge in
    `main()` stellt zusaetzlich sicher, dass die Diagnose/Auswertung IMMER
    VOR dem Cleanup laeuft, unabhaengig davon, ob das Cleanup klappt."""
    assert d != DATA_DIR and d.resolve() != DATA_DIR.resolve(), \
        f"SICHERHEITSSTOPP: remove_sandbox_dir() sollte NIE data/ selbst loeschen ({d})."
    if not d.exists():
        return
    try:
        shutil.rmtree(d)
        print(f"[cleanup] {label}-Sandbox entfernt: {d}", flush=True)
    except OSError as e:
        print(f"[cleanup][WARNUNG] {label}-Sandbox {d} konnte nicht vollstaendig entfernt werden "
              f"({e!r}) -- vermutlich haengt noch ein Datei-Handle (Explorer/Virenscanner/o.ae.). "
              f"KEIN Abbruch (das Messergebnis ist zu diesem Zeitpunkt laengst geschrieben) -- "
              f"Ordner manuell nachraeumen oder beim naechsten Lauf erneut versuchen "
              f"(ensure_hardlink_mirror/remove_sandbox_dir sind beide idempotent).", flush=True)


# ── Trainings-Sweep ──────────────────────────────────────────────────────

def run_training(arm: str, seed: int, data_dir_override: Path | None, recipe: list[str]) -> bool:
    name = f"{arm}_s{seed}"
    # Skip-Luecke (siehe train_2d_vs_flat_fs.py-Vorbild): laeuft ein Arm ohne
    # Plateau bis zum Epochen-Deckel durch, schreibt train.py NUR
    # alphazero_<name>.pth und kein separates _best.pth.
    ckpt = BASE_DIR / "models" / f"alphazero_{name}_best.pth"
    if not ckpt.exists():
        ckpt = BASE_DIR / "models" / f"alphazero_{name}.pth"
    if ckpt.exists():
        print(f"  [skip] {name}: Checkpoint existiert schon", flush=True)
        return True
    cmd = ([sys.executable, "-X", "faulthandler", "-u", str(BASE_DIR / "train.py"),
            "--name", name, "--seed", str(seed)] + recipe)
    env = os.environ.copy()
    data_desc = "data/ (voller echter Korpus)"
    if data_dir_override is not None:
        env["MOSAIC_DATA_DIR"] = str(data_dir_override)
        data_desc = str(data_dir_override)
    print(f"  [run ] {name}  [MOSAIC_DATA_DIR={data_desc}]  ({' '.join(cmd[5:])})", flush=True)
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
    """`_best` wenn vorhanden, sonst der Plain-Checkpoint (Lauf ohne
    Plateau) -- fuer die Diagnose-Modell-Liste."""
    if (BASE_DIR / "models" / f"alphazero_{name}_best.pth").exists():
        return f"{name}_best"
    return name


def run_diagnose_and_eval(model_pairs: list[tuple[str, str]], diag_out: Path, result_out: Path,
                           n_corpus_voll: int, n_corpus_halb: int) -> dict:
    """model_pairs: Liste von (voll_name, halb_name) OHNE _best-Suffix --
    wird hier zu _best/Plain aufgeloest. Schreibt die Diagnose- und die
    gepaarte Auswertungs-JSON, gibt die summary zurueck."""
    voll_models = [resolve_checkpoint_name(v) for v, _ in model_pairs]
    halb_models = [resolve_checkpoint_name(h) for _, h in model_pairs]
    models = voll_models + halb_models

    print(f"\n[diag] Diagnose (frozen, Orakel-Metriken) ueber {len(models)} Checkpoints...", flush=True)
    r = subprocess.run([sys.executable, "-u", str(BASE_DIR / "tools" / "offline_diagnosis.py"),
                        "--model", *models, "--frozen", "--out", str(diag_out)],
                       cwd=str(BASE_DIR))
    if r.returncode != 0:
        raise SystemExit("offline_diagnosis fehlgeschlagen -- siehe Ausgabe oben.")

    blob = json.loads(diag_out.read_text(encoding="utf-8"))
    by_name = {e["model"]: e for e in blob["results"]}

    seeds = [int(v.rsplit("_s", 1)[1]) for v, _ in model_pairs]
    vals: dict[str, dict[int, dict]] = {"voll": {}, "halb": {}}
    for (v_raw, h_raw), seed in zip(model_pairs, seeds):
        v_resolved, h_resolved = resolve_checkpoint_name(v_raw), resolve_checkpoint_name(h_raw)
        ve, he = by_name.get(v_resolved), by_name.get(h_resolved)
        if ve is not None:
            vals["voll"][seed] = {k: ve.get(k) for k in ORACLE_KEYS + ("value_r2_rounds_1_4",)}
        if he is not None:
            vals["halb"][seed] = {k: he.get(k) for k in ORACLE_KEYS + ("value_r2_rounds_1_4",)}

    print("\n" + "=" * 78)
    print("  KORPUS-DOSIS-WIRKUNG: voll vs. halb -- gepaarte Auswertung (PREREG_corpus_dose.md)")
    print("=" * 78)

    summary: dict = {
        "seeds": seeds, "n_corpus_files_voll": n_corpus_voll, "n_corpus_files_halb": n_corpus_halb,
        "metrics": {},
    }
    for mk in ORACLE_KEYS:
        common = sorted(s for s in seeds
                        if s in vals["voll"] and s in vals["halb"]
                        and vals["voll"][s].get(mk) is not None
                        and vals["halb"][s].get(mk) is not None)
        diffs = [vals["voll"][s][mk] - vals["halb"][s][mk] for s in common]
        print(f"\nMetrik: {mk}")
        print(f"{'Seed':<6}{'halb':>14}{'voll':>14}{'Diff(voll-halb)':>18}")
        for s in common:
            hv, vv = vals["halb"][s][mk], vals["voll"][s][mk]
            print(f"{s:<6}{hv:14.4f}{vv:14.4f}{vv - hv:+18.4f}")
        if not diffs:
            print("  keine auswertbaren Paare")
            continue
        mean_diff = sum(diffs) / len(diffs)
        pos = sum(1 for d in diffs if d > 0)
        neg = sum(1 for d in diffs if d < 0)
        p_sign = sign_test_p(pos, neg)
        t_stat, p_ttest, df = paired_ttest_p(diffs)
        print(f"  Ø Differenz (voll-halb): {mean_diff:+.4f}  (n={len(diffs)})")
        print(f"  Richtung: {pos}x voll besser / {neg}x halb besser -> Vorzeichentest p={p_sign:.4f}")
        print(f"  Gepaarter t-Test: t={t_stat:.3f}, df={df}, p={p_ttest:.4f}")
        summary["metrics"][mk] = {
            "n": len(diffs), "mean_diff": mean_diff, "n_positive": pos, "n_negative": neg,
            "sign_test_p": p_sign, "t_stat": t_stat, "df": df, "ttest_p": p_ttest,
            "per_seed": {str(s): {"halb": vals["halb"][s][mk], "voll": vals["voll"][s][mk],
                                  "diff": vals["voll"][s][mk] - vals["halb"][s][mk]} for s in common},
        }

    # value_r2_rounds_1_4: NUR informativ (siehe PREREG "Sekundaer/informativ").
    mk = "value_r2_rounds_1_4"
    common = sorted(s for s in seeds
                    if s in vals["voll"] and s in vals["halb"]
                    and vals["voll"][s].get(mk) is not None and vals["halb"][s].get(mk) is not None)
    if common:
        diffs = [vals["voll"][s][mk] - vals["halb"][s][mk] for s in common]
        summary["value_r2_rounds_1_4_informational"] = {
            "n": len(diffs), "mean_diff": sum(diffs) / len(diffs),
            "per_seed": {str(s): {"halb": vals["halb"][s][mk], "voll": vals["voll"][s][mk]} for s in common},
        }

    # Automatische Anwendung der PREREG-Interpretationsregel (rein
    # deskriptiv -- der Mensch entscheidet trotzdem).
    directions = [summary["metrics"][mk]["mean_diff"] > 0 for mk in ORACLE_KEYS if mk in summary["metrics"]]
    if len(directions) == len(ORACLE_KEYS):
        if not any(directions):
            verdict = ("voll auf BEIDEN Orakel-Metriken gepaart schlechter/gleich -- Korpusmenge traegt in "
                       "dieser Engine-Aera nichts (mehr) bei. Task #14s Grundannahme (Menge kompensiert "
                       "Suchqualitaetsverlust) wird unwahrscheinlicher, NICHT priorisieren ohne weitere Pruefung.")
        elif all(directions):
            verdict = ("voll auf BEIDEN Orakel-Metriken gepaart besser -- starker Befund fuer Menge-hilft. "
                       "Erhoeht die Prioritaet von Task #14 (Test B2) deutlich.")
        else:
            verdict = ("voll auf MINDESTENS EINER Orakel-Metrik gepaart besser -- Trend fuer Menge-hilft, "
                       "spricht tendenziell fuer Task #14s Grundannahme, beantwortet aber NICHT die eigentliche "
                       "Trajektorienqualitaets-Frage (Test B2, gleiche Rechenzeit) noetig.")
    else:
        verdict = "Nicht alle Metriken auswertbar -- manuelle Pruefung noetig."
    print(f"\n{'=' * 78}\nVERDIKT (automatisch nach PREREG_corpus_dose.md-Regel): {verdict}\n{'=' * 78}")
    summary["verdict"] = verdict

    result_out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nErgebnis: {result_out}")
    return summary


# ── Rauchtest ────────────────────────────────────────────────────────────

def run_smoke() -> None:
    """Testet die Treiber-Mechanik (Hardlink-Sandbox, Skip-Logik,
    Diagnose-Aufruf, gepaarte Auswertung) end-to-end mit winzigen, EIGENEN
    Sandbox-Korpora -- ruehrt den echten `data/`-Ordner zu keinem Zeitpunkt
    an. 2 Seeds, 3 `voll`-/2 `halb`-Sandbox-Dateien, 2 Epochen. Raeumt alle
    Artefakte (Checkpoints, Manifeste, Diagnose-/Ergebnis-JSON, Sandbox-
    Ordner) im finally-Block wieder auf, auch bei Fehlschlag."""
    print("[smoke] Rauchtest: 2 Seeds, 3 Voll-/2 Halb-Sandbox-Dateien, 2 Epochen.")
    print("[smoke] Ruehrt den echten data/-Ordner NICHT an (eigene Sandbox-Ordner).\n", flush=True)

    # 2026-08-01 Nachbesserung: KEIN Abbruch mehr bei laufendem self_play.py
    # -- nur noch eine informative Meldung (identisch zu main(), siehe dort).
    # Der Rauchtest baut seine eigenen eingefrorenen Sandboxen (unten), die
    # sind gegen data/-Wachstum genauso immun wie der echte Sweep.
    if selfplay_running():
        print("[smoke][info] self_play.py laeuft parallel -- unkritisch, der Rauchtest baut "
              "eigene eingefrorene Sandboxen.", flush=True)

    # classify_corpus() ist seit der 2. Nachbesserung lenient (Dateien
    # ausserhalb des v15/v16/v17-Universums, z.B. v19, werden nur gemeldet,
    # nicht als Abbruchgrund behandelt) -- fuer den Rauchtest reicht das,
    # OHNE verify_expected_composition() (die 600/200/100-Pruefung ist nur
    # fuer den ECHTEN Split relevant, der Rauchtest braucht nur irgendein
    # paar reale v15/v16/v17-Dateien als Sandbox-Fuellmaterial).
    groups, _n_outside = classify_corpus(DATA_DIR)
    all_files = sorted(p for files in groups.values() for p in files)
    if len(all_files) < 5:
        raise SystemExit("ABBRUCH (smoke): weniger als 5 passende Dateien in data/ -- Rauchtest braucht 3+2.")

    smoke_voll_dir = BASE_DIR / "data_dose_smoke_voll"
    smoke_halb_dir = BASE_DIR / "data_dose_smoke_halb"
    voll_names = [p.name for p in all_files[:3]]
    halb_names = [p.name for p in all_files[3:5]]

    smoke_recipe = ["--epochs", "2", "--lr", "4e-4", "--lr-schedule", "cosine",
                     "--value-target-variant", "nortv", "--no-plot", "--no-snapshot"]
    seeds = [1, 2]
    diag_out = BASE_DIR / "evaluations" / "artifacts" / "_smoke_corpus_dose_diag.json"
    result_out = BASE_DIR / "evaluations" / "artifacts" / "_smoke_corpus_dose_result.json"
    ok = False
    try:
        ensure_hardlink_mirror(voll_names, smoke_voll_dir, DATA_DIR)
        ensure_hardlink_mirror(halb_names, smoke_halb_dir, DATA_DIR)
        # Dieselben Konsistenzpruefungen wie der echte Sweep (main()) --
        # testet damit auch verify_sandbox_consistency() end-to-end, nicht
        # nur ensure_hardlink_mirror().
        verify_sandbox_consistency(voll_names, smoke_voll_dir, DATA_DIR, "smoke_voll")
        verify_sandbox_consistency(halb_names, smoke_halb_dir, DATA_DIR, "smoke_halb")
        print(f"[smoke] Sandbox aufgebaut: {smoke_voll_dir.name} ({len(voll_names)}), "
              f"{smoke_halb_dir.name} ({len(halb_names)})", flush=True)

        for seed in seeds:
            if not run_training("smoke_voll", seed, smoke_voll_dir, smoke_recipe):
                raise SystemExit("[smoke] smoke_voll-Lauf fehlgeschlagen.")
            if not run_training("smoke_halb", seed, smoke_halb_dir, smoke_recipe):
                raise SystemExit("[smoke] smoke_halb-Lauf fehlgeschlagen.")

        model_pairs = [(f"smoke_voll_s{s}", f"smoke_halb_s{s}") for s in seeds]
        summary = run_diagnose_and_eval(model_pairs, diag_out, result_out,
                                        n_corpus_voll=len(voll_names), n_corpus_halb=len(halb_names))
        assert "verdict" in summary and summary["metrics"], "[smoke] Auswertung lieferte keine Metriken."
        print("\n[smoke] ERFOLG -- Treiber-Mechanik (Sandbox, Training, Diagnose, Auswertung) funktioniert.")
        ok = True
    finally:
        print("\n[smoke] Raeume Artefakte auf...", flush=True)
        remove_sandbox_dir(smoke_voll_dir, "smoke_voll")
        remove_sandbox_dir(smoke_halb_dir, "smoke_halb")
        for name in [f"smoke_voll_s{s}" for s in seeds] + [f"smoke_halb_s{s}" for s in seeds]:
            # Alles unter diesem Namen -- .pth/.onnx/.onnx.ref.txt, je mit
            # optionalem _best-Suffix (train.py exportiert bei jedem Lauf
            # automatisch ONNX + Rust-Paritaetsreferenz mit, siehe Log).
            # Explizite Endungen statt Wildcard-Suffix, um Praefix-Kollisionen
            # zu vermeiden (z.B. s1 vs. s10 bei groesseren Seed-Listen).
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
    ap.add_argument("--out", default="evaluations/artifacts/train_corpus_dose_result.json")
    ap.add_argument("--diag-out", default="evaluations/artifacts/offline_diagnosis_corpus_dose_frozen.json")
    ap.add_argument("--skip-training", action="store_true",
                    help="Nur Diagnose+Auswertung auf bereits vorhandenen Checkpoints "
                         "(Sandboxes werden dafuer nicht gebraucht/geprueft).")
    ap.add_argument("--smoke", action="store_true",
                    help="Rauchtest der Treiber-Mechanik mit winzigen Sandbox-Korpora "
                         "(ruehrt data/ NICHT an, raeumt sich selbst auf) -- siehe Moduldoku.")
    ap.add_argument("--build-only", action="store_true",
                    help="Nur Split-Manifest + beide Hardlink-Sandboxes (data_dose_voll/, "
                         "data_dose_halb/) aufbauen und konsistenzpruefen, KEINE Trainingslaeufe "
                         "starten. Zum Vorbereiten/Einfrieren des Korpus VOR dem eigentlichen "
                         "Sweep-Start (die Sandboxes bleiben danach stehen, kein Cleanup).")
    args = ap.parse_args()

    if args.smoke:
        run_smoke()
        return

    if args.build_only and args.skip_training:
        raise SystemExit("--build-only und --skip-training schliessen sich aus "
                         "(--skip-training ueberspringt genau den Sandbox-Aufbau, den --build-only will).")

    # 2026-08-01 Nachbesserung: KEIN Hartabbruch mehr bei laufendem
    # self_play.py (z.B. v19) -- beide Arme trainieren gegen eingefrorene
    # Hardlink-Sandboxes (data_dose_voll/, data_dose_halb/), die einmalig aus
    # dem Split-Manifest gebaut werden und danach nie wieder aus data/ lesen.
    # Neue Self-Play-Dateien sind fuer den Sweep unsichtbar UND unschaedlich.
    # Nur noch eine informative Meldung, kein Abbruch, kein Flag mehr noetig.
    if selfplay_running():
        print("[info] self_play.py laeuft parallel -- unkritisch: beide Arme trainieren gegen "
              "eingefrorene Hardlink-Sandboxes (data_dose_voll/, data_dose_halb/), data/-Wachstum "
              "wird ignoriert (siehe PREREG_corpus_dose.md / Nachbesserung 2026-08-01).", flush=True)

    halb_file_names, voll_file_names = load_or_build_split()
    n_voll, n_halb = len(voll_file_names), len(halb_file_names)

    if not args.skip_training:
        # Sicherheitspruefung ERSETZT den fruehen Selfplay-Hartabbruch: die
        # 900 Manifest-Dateien muessen noch real in data/ existieren (data/
        # WAECHST durch Self-Play, schrumpft dadurch aber nie -- diese
        # Pruefung faengt stattdessen z.B. eine manuelle Aufraeumaktion ab),
        # und beide Sandboxes muessen danach exakt und per Hardlink-Identitaet
        # zum Manifest passen (verify_sandbox_consistency, siehe dort).
        missing_source = [n for n in voll_file_names if not (DATA_DIR / n).exists()]
        if missing_source:
            raise SystemExit(
                f"ABBRUCH: {len(missing_source)} Manifest-Datei(en) fehlen in {DATA_DIR} "
                f"(z.B. {missing_source[:3]}) -- {SPLIT_MANIFEST.name} passt nicht mehr zum "
                f"echten Korpus. Manuelle Pruefung noetig, KEINE automatische Neuziehung."
            )
        ensure_hardlink_mirror(voll_file_names, VOLL_DIR, DATA_DIR)
        ensure_hardlink_mirror(halb_file_names, HALB_DIR, DATA_DIR)
        verify_sandbox_consistency(voll_file_names, VOLL_DIR, DATA_DIR, "voll")
        verify_sandbox_consistency(halb_file_names, HALB_DIR, DATA_DIR, "halb")
        print(f"[sweep] Voll-Korpus bereit: {VOLL_DIR} ({n_voll} Dateien, Hardlinks, eingefroren).")
        print(f"[sweep] Halb-Korpus bereit: {HALB_DIR} ({n_halb} Dateien, Hardlinks, eingefroren).")

    if args.build_only:
        print(f"\n[build-only] Fertig -- Split-Manifest + beide Sandboxes stehen, KEIN Training "
              f"gestartet. Sweep spaeter starten mit: python {Path(__file__).name} --seeds ...", flush=True)
        return

    print(f"[sweep] Korpus (eingefroren zum Split-Manifest-Stand, immun gegen data/-Wachstum): "
          f"voll={n_voll} Dateien, halb={n_halb} Dateien | Seeds: {args.seeds} | "
          f"Rezept: {' '.join(RECIPE)}", flush=True)
    print(f"[sweep] 12 Laeufe (6 Seeds x 2 Arme, from scratch, kein --load)\n", flush=True)

    if not args.skip_training:
        for seed in args.seeds:
            print(f"=== Seed {seed}: Paar (voll, halb) ===", flush=True)
            t_pair0 = time.time()
            if not run_training("voll", seed, VOLL_DIR, RECIPE):
                raise SystemExit(f"voll_s{seed} fehlgeschlagen -- Sweep abgebrochen.")
            if not run_training("halb", seed, HALB_DIR, RECIPE):
                raise SystemExit(f"halb_s{seed} fehlgeschlagen -- Sweep abgebrochen.")
            print(f"[sweep] Seed {seed} fertig nach {(time.time()-t_pair0)/60:.1f} min (beide Arme).\n",
                  flush=True)

    # Diagnose+Auswertung ZUERST, Sandbox-Cleanup ALS LETZTER SCHRITT (2026-
    # 08-01 Nachbesserung, 3. Runde: die urspruengliche Reihenfolge raeumte
    # VOR der Diagnose auf -- ein PermissionError in remove_sandbox_dir()
    # [Windows-Handle auf data_dose_voll] liess den Sweep dort abstuerzen,
    # `run_diagnose_and_eval` lief nie, musste per `--skip-training`
    # nachgeholt werden. Das eigentliche Messergebnis (Diagnose+Auswertung)
    # ist der Grund fuer den ganzen Sweep -- es muss VOR jedem Aufraeumschritt
    # feststehen, egal ob das Cleanup danach klappt oder nicht (siehe
    # remove_sandbox_dir()-Fehlertoleranz).
    model_pairs = [(f"voll_s{s}", f"halb_s{s}") for s in args.seeds]
    run_diagnose_and_eval(model_pairs, BASE_DIR / args.diag_out, BASE_DIR / args.out,
                          n_corpus_voll=n_voll, n_corpus_halb=n_halb)

    if not args.skip_training:
        # Cleanup NACH dem GESAMTEN Sweep UND nach der Diagnose/Auswertung
        # (siehe Kommentar oben) -- beide eingefrorenen Sandboxes samt ihrer
        # je eigenen HDF5-Caches werden entfernt, data/ selbst bleibt zu
        # jedem Zeitpunkt unangetastet (remove_sandbox_dir() hat einen
        # eigenen Assert-Schutz dagegen UND ist jetzt fehlertolerant --
        # ein haengendes Datei-Handle warnt nur noch, statt abzubrechen).
        remove_sandbox_dir(VOLL_DIR, "voll")
        remove_sandbox_dir(HALB_DIR, "halb")


if __name__ == "__main__":
    main()
