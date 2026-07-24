"""
tools/build_frozen_eval_set.py — Task #87: eingefrorenes, generationsuebergreifendes
Eval-Set fuer offline_diagnose.py.

Motivation: offline_diagnose.py::val_files() zieht den Val-Split aus dem
JEWEILS AKTUELLEN data/-Inhalt (glob + Seed-Shuffle). Dadurch sind
Diagnose-Zahlen zwischen Generationen NICHT vergleichbar, sobald sich der
data/-Ordner aendert (altes Korpus rotiert raus, neues rein) -- Verdacht:
das v10-vs-v12-Policy-Top-1-Raetsel (44.0% vs. 39.8%, STATUS.md
"v12-Zyklus (2026-07-23)") ist teilweise Cross-Korpus-Artefakt statt eines
echten Staerke-/Stil-Unterschieds.

Dieses Skript zieht EINMALIG ein festes, stratifiziertes Sample aus
mehreren Korpora und friert es unveraenderlich ein (evaluations/
frozen_eval_set.pkl + Manifest). Ab Version "frozen_v1" wird dieses Set NIE
wieder ueberschrieben -- ein neuer Bedarf bekommt eine neue Versionsnummer
und einen neuen Dateinamen.

Sicherheitsregeln (Nutzer-Vorgabe, laeuft neben einem aktiven 11-Thread-
Self-Play-Batch):
  - data/ wird NUR gelesen, nie geschrieben/verschoben.
  - Dateien aus dem noch laufenden Batch (selfplay_v12_*.pkl) werden nur
    verwendet, wenn ihre mtime seit MIN_FILE_AGE_SECS unveraendert ist
    (Batch schreibt currently aktiv weiter).
  - Kein Torch-Import hier -- reines IO-Skript, keine Netz-Last.

Korpora (siehe Auftrag):
  - v10b: data/selfplay_v10b_*.pkl (v12-Trainingskorpus, netzgefuehrt v10)
  - v12:  data/selfplay_v12_*.pkl  (laufender Batch, nur "abgeschlossene"
          Dateien, s.o.)
  - netcq: data/archive_netcq*/selfplay_netcq_*.pkl (v11-Trainingskorpus).
    RECHERCHE-BEFUND: unter data/, unter dem Projekt-Root archive/ und per
    rekursivem Scan des gesamten Projektbaums (`**/*netcq*`) wurde KEINE
    netcq-Datei und KEIN archive_netcq*-Ordner gefunden -- der Korpus
    existiert auf dieser Maschine aktuell nicht (mehr) auf Platte. Das
    Skript versucht mehrere plausible Pfad-Muster; falls keines greift,
    wird das im Manifest dokumentiert (`netcq_available: false`) und mit
    den verbleibenden Korpora weitergemacht statt den ganzen Lauf zu
    blockieren.

Stratifizierung: pro Korpus x Runde (1-5) ein eigener "Bucket". Innerhalb
eines Buckets wird zufaellig (fester Seed) aus allen gefundenen
Kandidaten-Steps gezogen -- gleichmaessige Rundenabdeckung je Korpus.

Verwendung:
    python tools/build_frozen_eval_set.py
    python tools/build_frozen_eval_set.py --dry-run   # nur Zaehlen, nichts schreiben
"""
import argparse
import glob
import json
import os
import pickle
import random
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import DATA_DIR  # noqa: E402

FROZEN_VERSION = "frozen_v1"
FROZEN_SEED = 20260724  # deterministisch, aendert sich NIE fuer frozen_v1
N_TARGET_TOTAL = 1800   # Ziel-Groesse, Vorgabe ~1500-2000
ROUNDS = (1, 2, 3, 4, 5)
MIN_FILE_AGE_SECS = 600  # 10 Minuten -- Schutz gegen den laufenden v12-Batch
N_FILES_PER_CORPUS = 20   # feste Datei-Stichprobe je Korpus (deterministisch
                           # permutiert) -- bewusst KEIN "stop sobald ein
                           # Bucket voll ist": das wuerde nur die ersten paar
                           # (zufaellig sortierten) Dateien lesen und die
                           # Spiel-/Zeit-Diversitaet im frozen Set unnoetig
                           # einschraenken. 20 Dateien x ~10 Spiele = ~200
                           # Spiele je Korpus, IO bleibt trotzdem leicht
                           # (~300MB/Korpus).

OUT_PKL = ROOT / "evaluations" / "frozen_eval_set.pkl"
OUT_MANIFEST = ROOT / "evaluations" / "frozen_eval_set_manifest.json"


def _git_commit() -> str | None:
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                              capture_output=True, text=True, timeout=10)
        return out.stdout.strip() if out.returncode == 0 else None
    except Exception:
        return None


def _candidate_files(name: str) -> list[str]:
    """Liefert die Kandidaten-Dateiliste je Korpus-Name (nur Existenz-Filter,
    keine Zeit-/Reihenfolge-Auswahl -- das passiert im Aufrufer)."""
    if name == "v10b":
        return sorted(glob.glob(str(DATA_DIR / "selfplay_v10b_*.pkl")))
    if name == "v12":
        now = time.time()
        all_files = sorted(glob.glob(str(DATA_DIR / "selfplay_v12_*.pkl")))
        return [f for f in all_files if now - os.path.getmtime(f) > MIN_FILE_AGE_SECS]
    if name == "netcq":
        patterns = [
            "archive_netcq*/selfplay_netcq_*.pkl",
            "archive_netcq*/*.pkl",
            "selfplay_netcq_*.pkl",
            "**/selfplay_netcq_*.pkl",
        ]
        found = []
        for pat in patterns:
            found.extend(glob.glob(str(DATA_DIR / pat), recursive=True))
        # auch ausserhalb data/ (Projekt-Root archive/) probieren
        found.extend(glob.glob(str(ROOT / "archive" / "**" / "selfplay_netcq_*.pkl"), recursive=True))
        return sorted(set(found))
    raise ValueError(name)


def _eligible_steps(file_path: str):
    """Liest eine .pkl-Datei read-only und liefert alle Steps, die
    offline_diagnose.py::load_val_samples ebenfalls verwenden wuerde
    (Filter: 'scores' und 'winner' vorhanden)."""
    with open(file_path, "rb") as fh:
        game_data = pickle.load(fh)
    out = []
    for step in game_data:
        if "scores" not in step or "winner" not in step:
            continue
        r = int(step["state"].get("round", 0))
        if r not in ROUNDS:
            continue
        out.append((r, step))
    return out


def collect_corpus(name: str, per_stratum: int, seed: int, verbose: bool = True):
    """Liest eine feste, deterministisch permutierte Datei-Stichprobe
    (N_FILES_PER_CORPUS) dieses Korpus komplett ein, bucketet alle
    eligiblen Steps nach Runde, und zieht dann einen festen Zufallszug von
    genau `per_stratum` Steps je Runde (oder weniger, falls nicht genug
    Kandidaten da waren -- wird im Manifest sichtbar)."""
    files = _candidate_files(name)
    if not files:
        if verbose:
            print(f"  [{name}] keine Dateien gefunden -- Korpus wird uebersprungen.")
        return {}, [], 0

    rng_files = random.Random(seed)
    shuffled = files[:]
    rng_files.shuffle(shuffled)
    sample = shuffled[:N_FILES_PER_CORPUS]

    candidates = {r: [] for r in ROUNDS}
    files_used = []

    for f in sample:
        steps = _eligible_steps(f)
        files_used.append(os.path.basename(f))
        for r, step in steps:
            candidates[r].append((os.path.basename(f), step))
        if verbose:
            counts = {r: len(candidates[r]) for r in ROUNDS}
            print(f"  [{name}] gelesen: {os.path.basename(f)} -> Kandidaten je Runde: {counts}")

    selected = {}
    for r in ROUNDS:
        pool = candidates[r]
        rng_pick = random.Random(seed + 1000 * r)
        rng_pick.shuffle(pool)
        take = min(per_stratum, len(pool))
        selected[r] = pool[:take]

    return selected, files_used, len(sample)


def build_records(corpora_selected: dict) -> list[dict]:
    records = []
    for corpus_name, per_round in corpora_selected.items():
        for r, items in per_round.items():
            for source_file, step in items:
                state = step["state"]
                valid_actions = step.get("valid_actions") or state.get("valid_moves", [])
                records.append({
                    "state": state,
                    "valid_actions": valid_actions,
                    "policy": step.get("policy", []),
                    "player": step.get("player"),
                    "scores": step.get("scores"),
                    "scores_unclamped": step.get("scores_unclamped"),
                    "bootstrap_value": step.get("bootstrap_value"),
                    "round_transition_value": step.get("round_transition_value"),
                    "winner": step.get("winner"),
                    "completed": step.get("completed"),
                    "round": r,
                    "source_corpus": corpus_name,
                    "source_file": source_file,
                    "game_id": step.get("game_id"),
                })
    return records


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="nur zaehlen/planen, nichts schreiben")
    ap.add_argument("--n-total", type=int, default=N_TARGET_TOTAL)
    args = ap.parse_args()

    corpora_names = ["v10b", "v12", "netcq"]
    available = {name: bool(_candidate_files(name)) for name in corpora_names}
    active_corpora = [n for n in corpora_names if available[n]]
    if not active_corpora:
        raise SystemExit("Keine der drei Korpora hat verfuegbare Dateien -- Abbruch.")

    n_buckets = len(active_corpora) * len(ROUNDS)
    per_stratum = args.n_total // n_buckets

    print(f"Frozen-Eval-Set-Build ({FROZEN_VERSION}, Seed {FROZEN_SEED})")
    print(f"Verfuegbare Korpora: {active_corpora} (netcq gefunden: {available['netcq']})")
    print(f"Ziel: {args.n_total} Zustaende / {n_buckets} Buckets = {per_stratum} je Bucket (Korpus x Runde)")

    corpora_selected = {}
    manifest_corpora = {}
    for name in active_corpora:
        print(f"\n== Korpus {name} ==")
        selected, files_used, n_scanned = collect_corpus(name, per_stratum, FROZEN_SEED)
        corpora_selected[name] = selected
        manifest_corpora[name] = {
            "n_files_scanned": n_scanned,
            "files_used": files_used,
            "per_round": {str(r): len(selected.get(r, [])) for r in ROUNDS},
            "requested_per_round": per_stratum,
        }

    for name in corpora_names:
        if name not in active_corpora:
            manifest_corpora[name] = {"available": False, "note": "keine Dateien gefunden (siehe Docstring)"}

    records = build_records(corpora_selected)
    print(f"\nGesamt gesammelt: {len(records)} Zustaende")

    # Zusammensetzung je Korpus/Runde fuer Manifest + Konsole
    comp = defaultdict(lambda: defaultdict(int))
    for rec in records:
        comp[rec["source_corpus"]][rec["round"]] += 1
    print("\nZusammensetzung:")
    for name in active_corpora:
        row = [comp[name][r] for r in ROUNDS]
        print(f"  {name:8s} Runde1-5: {row}  Summe={sum(row)}")

    manifest = {
        "version": FROZEN_VERSION,
        "build_date_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit(),
        "seed": FROZEN_SEED,
        "n_target_total": args.n_total,
        "n_buckets": n_buckets,
        "per_stratum_requested": per_stratum,
        "n_records_actual": len(records),
        "rounds": list(ROUNDS),
        "n_files_per_corpus_sampled": N_FILES_PER_CORPUS,
        "min_file_age_secs_v12_filter": MIN_FILE_AGE_SECS,
        "corpora": manifest_corpora,
        "composition_corpus_x_round": {
            name: {str(r): comp[name][r] for r in ROUNDS} for name in active_corpora
        },
        "netcq_available": available["netcq"],
        "notes": (
            "netcq-Korpus (v11-Trainingsdaten, selfplay_netcq_*.pkl) wurde nicht "
            "gefunden -- weder unter data/, noch unter archive/, noch per "
            "rekursivem Scan des Projektbaums. Vermutlich bereits geloescht "
            "oder ausserhalb dieser Maschine archiviert. Set besteht daher aus "
            "v10b + v12."
        ) if not available["netcq"] else "alle drei Korpora verfuegbar.",
        "immutable": True,
    }

    if args.dry_run:
        print("\n--dry-run: nichts geschrieben.")
        print(json.dumps(manifest, indent=2, ensure_ascii=False)[:2000])
        return

    if OUT_PKL.exists():
        raise SystemExit(
            f"ABBRUCH: {OUT_PKL} existiert bereits -- {FROZEN_VERSION} ist UNVERAENDERLICH. "
            "Fuer ein neues Set eine neue Versionsnummer/Dateinamen verwenden."
        )

    OUT_PKL.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PKL, "wb") as fh:
        pickle.dump({
            "version": FROZEN_VERSION,
            "seed": FROZEN_SEED,
            "records": records,
        }, fh, protocol=pickle.HIGHEST_PROTOCOL)
    with open(OUT_MANIFEST, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)

    print(f"\nGeschrieben: {OUT_PKL} ({len(records)} Records)")
    print(f"Manifest: {OUT_MANIFEST}")


if __name__ == "__main__":
    main()
