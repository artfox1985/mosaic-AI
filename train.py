# train.py
import sys
import argparse

# Windows-Konsolen (cp1252) können die Emoji-Ausgaben sonst nicht kodieren.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import torch
import math
import glob
import json
import re
import subprocess
import random
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from pathlib import Path
from datetime import datetime
from torch.utils.data import DataLoader


# ── Diagnose-Instrumentierung (2026-07-31, Task #11 Phase 2, fs_2d_s1-
# Absturzuntersuchung) ────────────────────────────────────────────────────
# Kein psutil installiert (Sicherheitsregel: kein pip ins System-Python) --
# direkt ueber die Windows-API (`GetProcessMemoryInfo`, psapi.dll), analog zu
# dem, was `psutil.Process().memory_info()` intern ebenfalls tut. Best-effort:
# auf Nicht-Windows oder bei jedem API-Fehler liefert die Funktion `None`,
# der Aufrufer ueberspringt die Zeile dann einfach -- die Instrumentierung
# darf das eigentliche Training nie gefaehrden.
def _mem_info_gb():
    """(WorkingSetSize, PrivateUsage) in GB, oder None bei Fehler/Nicht-Windows.
    WorkingSetSize ~= RSS (physisch resident), PrivateUsage ~= Commit Charge
    (inkl. reserviertem, noch nicht physisch belegtem virtuellem Speicher --
    die Kennzahl, die bei einem `MemoryError`/Allokationsfehler zuerst an
    ein Limit stoesst)."""
    try:
        import ctypes
        from ctypes import wintypes

        class _PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
                ("PrivateUsage", ctypes.c_size_t),
            ]

        # WICHTIG: `ctypes.windll.kernel32.GetCurrentProcess()` OHNE explizites
        # `restype` truncated das (Pseudo-)Handle stillschweigend auf `c_int`
        # -- `GetProcessMemoryInfo` scheitert dann leise (Rueckgabe 0, keine
        # Python-Exception). Explizite `WinDLL`+`restype`/`argtypes` beheben das.
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        kernel32.GetCurrentProcess.argtypes = []
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        psapi.GetProcessMemoryInfo.argtypes = [
            wintypes.HANDLE, ctypes.POINTER(_PROCESS_MEMORY_COUNTERS_EX), wintypes.DWORD,
        ]

        counters = _PROCESS_MEMORY_COUNTERS_EX()
        counters.cb = ctypes.sizeof(_PROCESS_MEMORY_COUNTERS_EX)
        handle = kernel32.GetCurrentProcess()
        ok = psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb)
        if not ok:
            return None
        return (counters.WorkingSetSize / 1e9, counters.PrivateUsage / 1e9)
    except Exception:
        return None


def _system_mem_info_gb():
    """(TotalPhys, AvailPhys, TotalPageFile/Commit-Limit, AvailPageFile) in GB,
    oder None -- einmalig beim Start geloggt (2026-07-31 Diagnose-Auftrag,
    Arm B/A), damit die Bewertung von Arm A ("laeuft RSS gegen die Commit-
    Grenze?") einen konkreten Nenner hat statt eines geschaetzten Werts."""
    try:
        import ctypes

        class _MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_uint64),
                ("ullAvailPhys", ctypes.c_uint64),
                ("ullTotalPageFile", ctypes.c_uint64),
                ("ullAvailPageFile", ctypes.c_uint64),
                ("ullTotalVirtual", ctypes.c_uint64),
                ("ullAvailVirtual", ctypes.c_uint64),
                ("ullAvailExtendedVirtual", ctypes.c_uint64),
            ]

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.GlobalMemoryStatusEx.restype = ctypes.c_int
        kernel32.GlobalMemoryStatusEx.argtypes = [ctypes.POINTER(_MEMORYSTATUSEX)]
        stat = _MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(_MEMORYSTATUSEX)
        ok = kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        if not ok:
            return None
        return (stat.ullTotalPhys / 1e9, stat.ullAvailPhys / 1e9,
                stat.ullTotalPageFile / 1e9, stat.ullAvailPageFile / 1e9)
    except Exception:
        return None


def plackett_luce_moon_loss(pred_moon, moon_targets):
    """Negative Log-Likelihood der DFS-Referenz-Reihenfolge unter einem
    Plackett-Luce-Modell über die 5 rohen Moon-Head-Scores (sequenzieller
    Softmax über die jeweils noch nicht platzierten, ursprünglich vorhandenen
    Farben — Rust-Pendant: net_mcts.rs::plackett_luce_prob, hier differenzierbar
    fürs Training). `moon_targets`: je Farbe der Rang (0=zuerst…4=zuletzt) oder
    -1 (Farbe nicht in der Restmenge dieses Samples). Gibt (B,) NLL zurück —
    Zeilen ohne jede gültige Farbe (kein Sonnenzug) liefern 0.
    Nutzt -1e9 statt -inf als Masken-Wert: nach der Max-Subtraktion in
    log_softmax bleibt eine vollständig maskierte Zeile ein wohldefiniertes
    Gleichverteilungs-Softmax (kein NaN), unabhängig davon ob ihr Beitrag
    später über `has_rank_t` verworfen wird."""
    present = moon_targets >= 0                      # (B,5) bool
    placed = torch.zeros_like(present)
    total_nll = torch.zeros(moon_targets.shape[0], device=moon_targets.device)
    for t in range(5):
        is_rank_t = present & (moon_targets == t)     # (B,5): genau 1 True je Zeile, falls Rang t existiert
        has_rank_t = is_rank_t.any(dim=1)
        avail = present & (~placed)
        masked_logits = pred_moon.masked_fill(~avail, -1e9)
        log_probs = F.log_softmax(masked_logits, dim=1)
        step_nll = -(log_probs * is_rank_t.float()).sum(dim=1)
        total_nll = total_nll + torch.where(has_rank_t, step_nll, torch.zeros_like(step_nll))
        placed = placed | is_rank_t
    return total_nll


# Unsere dynamischen Pfade aus der Config laden
from config import (MODELS_DIR, DATA_DIR, NUM_ACTIONS, BATCH_SIZE, LEARNING_RATE, VALUE_WEIGHT,
                    POINTS_WEIGHT, OWNERSHIP_WEIGHT, POINTS_DIST_BINS, POINTS_DIST_SIGMA)

# Netz/Dataset (PyTorch) liegen jetzt neben der Rust-Engine in engine/py/.
sys.path.insert(0, str(Path(__file__).resolve().parent / "engine" / "py"))
from neural_net import (
    MosaicNet, Mosaic2DNet, MosaicDataset, TD_LAMBDA, POLICY_TARGET_SHARPEN_EXPONENT,
    VALUE_SCHEMA_VERSION, encoder_from_state_dict,
)


# ── Lauf-Manifest + Korpus-Log (#64 Teil 2, Phase 2b, 2026-07-22) ───────────
# Additiv neben dem bestehenden `--train-file-limit`-Flag (Daten-Skalierungs-
# Ablation, Task #69, unveraendert -- siehe dessen Kommentar unten). Ein
# Trainingslauf soll rueckwirkend rekonstruierbar sein: welche CLI-Args,
# welcher Rust/Python-Konstanten-Stand, welche Korpus-Zusammensetzung gingen
# ein. Nutzer-Wunsch: die Korpus-Zusammensetzung wird NUR geloggt (Konsole +
# Manifest) -- das Replay-Fenster selbst stellt der Nutzer weiterhin manuell
# zusammen (kein automatisches Filtern hier). Alles best-effort (git/
# engine_config_json koennen fehlen) -- ein Manifest-Fehler darf das
# eigentliche Training nie verhindern.

_SELFPLAY_FILENAME_RE = re.compile(
    r"^selfplay_(?P<prefix>.+)_(?P<date>\d{8})_(?P<time>\d{4})_g(?P<games>\d+)\.pkl$"
)


def points_dist_loss(logits, targets, model, rw2, denom):
    """Task #12: Kreuzentropie des Verteilungs-Punktekopfs gegen ein
    HL-Gauss-geglaettetes Ziel.

    `targets` ist der skalare tanh-gestauchte Punktedifferenz-Wert in [-1, 1].
    Statt ihn hart auf ein Bin zu legen (Two-Hot), wird eine Normalverteilung
    um ihn gelegt und ueber die Bin-KANTEN integriert (Differenz der Gauss-CDF)
    -- laut Farebrother et al. 2024 ("Stop Regressing") durchweg besser als
    Two-Hot, weil benachbarte Bins Gradient bekommen und das Ziel damit
    glatt in der Zielgroesse ist.

    Ziele ausserhalb von [-1, 1] koennen nicht auftreten (tanh), die
    Renormierung faengt aber die an den Raendern abgeschnittene
    Wahrscheinlichkeitsmasse ab.
    """
    edges = model.points_bin_edges.to(logits.device)          # (B+1,)
    sigma = POINTS_DIST_SIGMA * (edges[1] - edges[0])
    y = targets.view(-1, 1)                                    # (N, 1)
    # Gauss-CDF an jeder Bin-Kante: Phi(z) = 0.5*(1+erf(z/sqrt(2)))
    cdf = 0.5 * (1.0 + torch.erf((edges.view(1, -1) - y) / (sigma * math.sqrt(2.0))))
    probs = cdf[:, 1:] - cdf[:, :-1]                            # (N, B)
    probs = probs / probs.sum(dim=1, keepdim=True).clamp(min=1e-8)
    ce = -(probs * F.log_softmax(logits, dim=-1)).sum(dim=-1, keepdim=True)
    if rw2 is None:
        return ce.mean()
    return (ce * rw2).sum() / denom


def _git_commit_hash() -> str | None:
    """Best-effort HEAD-Commit-Hash. None, wenn nicht ermittelbar."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=str(Path(__file__).resolve().parent),
            capture_output=True, text=True, timeout=5, check=True,
        )
        return out.stdout.strip()
    except Exception:
        return None


def _git_is_dirty() -> bool | None:
    """Best-effort: gibt es uncommittete Änderungen im Arbeitsbaum? None,
    wenn nicht ermittelbar."""
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain"], cwd=str(Path(__file__).resolve().parent),
            capture_output=True, text=True, timeout=5, check=True,
        )
        return bool(out.stdout.strip())
    except Exception:
        return None


def _engine_config() -> dict:
    """Aktive Rust-Suchkonstanten, siehe `mosaic_rust.engine_config_json`
    (lib.rs, Phase 2a). Best-effort: `train.py` braucht `mosaic_rust`
    ansonsten nicht -- ein fehlendes/altes Wheel darf das Training nicht
    verhindern, nur diesen Manifest-Teil leer/fehlerhaft lassen."""
    try:
        import mosaic_rust as _mr
        return json.loads(_mr.engine_config_json())
    except Exception as e:
        return {"_error": f"engine_config_json nicht verfügbar: {e!r}"}


def _corpus_composition(all_files: list[str]) -> list[dict]:
    """Gruppiert die Trainingskorpus-Dateien nach Versions-Präfix (alles vor
    dem eingebetteten Zeitstempel `_<date>_<time>_g<N>.pkl`, siehe
    `self_play.py::_flush`) -- rein aus den DATEINAMEN, kein Pickle-Laden
    nötig. `games`-Schätzung: die kumulative `_g<N>`-Ziffer resettet bei
    JEDEM neuen Self-Play-Lauf auf klein (self_play.py's `done` startet pro
    Aufruf bei 0) -- Dateien je Präfix nach (Zeitstempel, dann g) sortiert,
    ein Sprung `g_i <= g_{i-1}` gilt als Start eines neuen Laufs (eigener
    Beitrag = g_i selbst statt g_i - g_{i-1}). Reduziert sich für den
    Normalfall (ein durchgehender Lauf je Präfix) exakt auf `max(g)`
    (z.B. "180 Dateien netcq (1800 Spiele)" bei per_file=10)."""
    groups: dict[str, list[tuple[str, int]]] = {}
    unmatched = 0
    for f in all_files:
        name = Path(f).name
        m = _SELFPLAY_FILENAME_RE.match(name)
        if not m:
            unmatched += 1
            continue
        prefix = m.group("prefix")
        dt_key = m.group("date") + m.group("time")
        games = int(m.group("games"))
        groups.setdefault(prefix, []).append((dt_key, games))

    composition = []
    for prefix, entries in groups.items():
        entries.sort(key=lambda e: (e[0], e[1]))  # (Zeitstempel, dann g) aufsteigend
        total_games = 0
        prev_g = 0
        for _dt_key, g in entries:
            total_games += g if g <= prev_g else g - prev_g
            prev_g = g
        composition.append({"prefix": prefix, "files": len(entries), "games": total_games})
    composition.sort(key=lambda c: -c["files"])
    if unmatched:
        composition.append({"prefix": "_unmatched", "files": unmatched, "games": None})
    return composition


def _write_train_manifest(version_name, cli_args, corpus_composition, run_timestamp) -> None:
    """Schreibt `models/manifest_train_<name>_<timestamp>.json` und loggt die
    Korpus-Zusammensetzung auf Konsole."""
    manifest = {
        "version": version_name,
        "run_timestamp": run_timestamp,
        "cli_args": cli_args,
        "git_commit": _git_commit_hash(),
        "git_dirty": _git_is_dirty(),
        "engine_config": _engine_config(),
        "python_constants": {
            "TD_LAMBDA": TD_LAMBDA,
            "POLICY_TARGET_SHARPEN_EXPONENT": POLICY_TARGET_SHARPEN_EXPONENT,
            "VALUE_WEIGHT": VALUE_WEIGHT,
            "POINTS_WEIGHT": POINTS_WEIGHT,
            "VALUE_SCHEMA_VERSION": VALUE_SCHEMA_VERSION,
        },
        "corpus_composition": corpus_composition,
    }
    path = MODELS_DIR / f"manifest_train_{version_name}_{run_timestamp}.json"
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        print(f"📝 Trainings-Manifest geschrieben: '{path}'")
    except Exception as e:
        print(f"  ⚠️  Manifest konnte nicht geschrieben werden ({e!r}) -- Training läuft trotzdem weiter.")

    print("📦 Trainingskorpus-Zusammensetzung (nach Versions-Präfix, aus Dateinamen):")
    for c in corpus_composition:
        games_s = f"{c['games']} Spiele" if c["games"] is not None else "Spiele-Zahl unklar"
        print(f"   {c['files']:>4} Dateien {c['prefix']:<28} ({games_s})")


def train(version_name, load_version=None, input_epoch=None, hidden_size=None, early_stop=True,
          show_plot=True, val_frac=0.1, train_file_limit=None, lr=None, lr_schedule="none",
          exclude_round5=False, ownership_weight=None, seed=None, snapshot=True,
          value_weight=None, points_weight=None, value_target_variant="default",
          points_dist_bins=None, reinit_points_head=False, encoder="flat"):
    # Warm-Start-Checkpoint sofort validieren (vor dem teuren Daten-Laden).
    # --load hängt selbst "alphazero_" an; wer versehentlich den vollen
    # Dateinamen übergibt, landet bei alphazero_alphazero_*.pth. Das doppelte
    # Präfix wird erkannt und mit Warnung korrigiert. Fehlt der aufgelöste
    # Checkpoint, bricht das Training hart ab: der frühere stille
    # From-Scratch-Fallback hat im v13-Zyklus 6 Epochen gekostet, weil er nur
    # am zu niedrigen Epoche-1-Val-R² erkennbar war.
    if encoder not in ("flat", "2d"):
        sys.exit(f"❌ Unbekannter --encoder '{encoder}' -- erlaubt: 'flat', '2d'.")
    # Diagnose-Instrumentierung (2026-07-31, Arm A/B): einmalig physisches
    # Gesamt-RAM + Commit-Limit der Maschine loggen -- Nenner fuer die
    # RSS/Commit-Log-Interpretation waehrend des Laufs (siehe _mem_info_gb).
    _sys_mem = _system_mem_info_gb()
    if _sys_mem is not None:
        total_phys, avail_phys, total_commit, avail_commit = _sys_mem
        print(f"🖥️  System-RAM: {total_phys:.1f} GB gesamt, {avail_phys:.1f} GB frei beim Start "
              f"| Commit-Limit: {total_commit:.1f} GB, {avail_commit:.1f} GB frei beim Start")
    load_path = None
    if load_version:
        if load_version.startswith("alphazero_"):
            corrected = load_version[len("alphazero_"):]
            if (MODELS_DIR / f"alphazero_{corrected}.pth").exists():
                print(f"⚠️  --load '{load_version}' enthält bereits das Präfix 'alphazero_' — "
                      f"verwende '{corrected}'.")
                load_version = corrected
        load_path = MODELS_DIR / f"alphazero_{load_version}.pth"
        if not load_path.exists():
            sys.exit(
                f"❌ Start-Modell nicht gefunden: {load_path}\n"
                f"   --load erwartet den Versionsnamen OHNE 'alphazero_'-Präfix "
                f"(z.B. --load v12b_lr_best für alphazero_v12b_lr_best.pth).\n"
                f"   Abbruch, um stilles Training von null zu verhindern."
            )
        # Task #11 Phase 2: im 2D-Modus darf NUR von einem 2D-Checkpoint warm
        # gestartet werden -- ein stiller Teil-Load (Flach-Checkpoint hat
        # z.B. kein `conv.*`, aber teils gleich benannte `policy_head.*`/
        # `value_head.*`-Keys, die load_state_dict(strict=False) klaglos
        # uebernehmen wuerde) wuerde den Conv-Zweig zufaellig lassen, OHNE
        # dass das auffiele -- harter Fehler statt stillem Teil-Load.
        _load_ckpt_encoder = encoder_from_state_dict(
            torch.load(str(load_path), map_location="cpu")["model_state"]
        )
        if _load_ckpt_encoder != encoder:
            sys.exit(
                f"❌ --encoder {encoder!r}, aber --load '{load_version}' ist ein "
                f"{_load_ckpt_encoder!r}-Checkpoint. Warm-Start ueber Encoder-Grenzen "
                f"hinweg ist nicht sinnvoll (Architektur passt nicht) -- Abbruch statt "
                f"stillem Teil-Load."
            )

    # 1. Daten laden (Nutzt jetzt dynamisch den DATA_DIR Pfad)
    # Val-Split auf DATEI-Ebene (nicht Zug-Ebene!): Zuege derselben Partie sind
    # stark korreliert, ein Zug-Split wuerde nahezu identische Zustaende in
    # Training UND Validierung streuen und ein zu gutes Val-R² vortaeuschen.
    # Bewusst PRO TRAININGSLAUF neu gezogen (kein ueber Generationen fixer
    # Val-Satz) -- das Val-Ergebnis soll nur beantworten "ueberfittet DIESES
    # Modell auf sein eigenes aktuelles Fenster", nicht als generations-
    # uebergreifendes Benchmark dienen (das leistet schon die Arena vs.
    # Champion/Heuristik).
    all_files = sorted(glob.glob(str(DATA_DIR / "*.pkl")))

    # Lauf-Manifest + Korpus-Log (#64 Teil 2) -- siehe Funktionskommentare
    # oben. Additiv, rührt die train_file_limit-Logik unten nicht an.
    _run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    _cli_args = {
        "name": version_name, "load": load_version, "epochs": input_epoch, "hidden": hidden_size,
        "early_stop": early_stop, "show_plot": show_plot, "val_frac": val_frac,
        "train_file_limit": train_file_limit, "lr": lr, "lr_schedule": lr_schedule,
        "exclude_round5": exclude_round5, "ownership_weight": ownership_weight,
        "seed": seed, "snapshot": snapshot,
        "value_weight": value_weight, "points_weight": points_weight,
        "value_target_variant": value_target_variant, "encoder": encoder,
    }
    _write_train_manifest(version_name, _cli_args, _corpus_composition(all_files), _run_timestamp)

    val_files = []
    train_files = None  # None == MosaicDataset laedt wie bisher den ganzen Ordner
    if val_frac > 0 and len(all_files) >= 10:
        shuffled = all_files[:]
        random.Random(20260707).shuffle(shuffled)
        n_val = max(1, round(len(shuffled) * val_frac))
        val_files = sorted(shuffled[:n_val])
        train_files = sorted(shuffled[n_val:])

    # Daten-Skalierungs-Ablation (Task #69): Trainings-Dateien NACH dem
    # Val-Split auf train_file_limit kappen -- der Val-Split oben ist davon
    # unberuehrt (bleibt identisch zu v11/vollem Korpus), nur die Trainings-
    # menge schrumpft. Eigener, vom Val-Split-Seed getrennter Seed (+1), damit
    # die Auswahl nicht zufaellig mit dem Val-Split-Shuffle korreliert.
    if train_file_limit is not None and train_files is not None and len(train_files) > train_file_limit:
        subsample_rng = random.Random(20260707 + 1)
        pool = train_files[:]
        subsample_rng.shuffle(pool)
        orig_n = len(train_files)
        train_files = sorted(pool[:train_file_limit])
        print(f"   Subsampling (Task #69): {len(train_files)} von {orig_n} Trainings-Dateien "
              f"(Seed 20260708, Val-Split unveraendert)")

    if value_target_variant != "default":
        print(f"🧪 Value-Target-Variante (Task #84, rtv-Ablation): '{value_target_variant}'")
    if encoder == "2d":
        print(f"🧩 Encoder: '2d' (Task #11 Phase 2, Mosaic2DNet -- Conv-Zweig auf state_to_planes "
              f"+ Flach-Zweig auf state_to_tensor)")
    dataset = MosaicDataset(str(DATA_DIR), files=train_files, value_target_variant=value_target_variant,
                            encoder=encoder)
    if len(dataset) == 0:
        print(f"❌ Fehler: Keine Daten im Ordner '{DATA_DIR}' gefunden!")
        return

    val_dataset = None
    if val_files:
        val_dataset = MosaicDataset(str(DATA_DIR), files=val_files, value_target_variant=value_target_variant,
                                    encoder=encoder)
        print(f"   Val-Split: {len(train_files)} Trainings-Dateien / {len(val_files)} Val-Dateien "
              f"({len(dataset):,} / {len(val_dataset):,} Züge)")

    # drop_last=True: ohne das kann die letzte Batch einer Epoche zufällig auf
    # Größe 1 fallen (Datensatzgröße mod BATCH_SIZE == 1) — BatchNorm im Netz
    # verlangt >1 Sample pro Kanal im Training und crasht sonst hart.
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True, drop_last=True)
    val_dataloader = (DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)
                      if val_dataset is not None else None)

    # 2. Hardware Setup
    # Reproduzierbarkeit (Task #9, 2026-07-28): bis dahin setzte train.py
    # KEINEN Seed -- zwei Laeufe mit identischen Flags unterschieden sich durch
    # Gewichts-Init UND Batch-Shuffling. Damit war jeder Trainings-A/B auf
    # Einzellaeufen (v12b_lr, v17_lrfix, r5base/r5excl) nur bis auf eine
    # UNBEKANNTE Lauf-zu-Lauf-Varianz interpretierbar. Mit --seed laufen zwei
    # Arme auf identischer Init und identischer Batch-Reihenfolge, der
    # Unterschied ist dann allein die getestete Aenderung.
    # Default None = altes Verhalten (unseeded), damit Alt-Rezepte unveraendert
    # bleiben. torch.manual_seed deckt Init UND DataLoader-Shuffle ab.
    if seed is not None:
        torch.manual_seed(seed)
        random.seed(seed)
        print(f"   Seed          : {seed} (reproduzierbar)")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n🚀 Starte PyTorch Training auf: {device.type.upper()}")

    # 3. Modell Setup
    from config import HIDDEN_SIZE as DEFAULT_HIDDEN
    hs = hidden_size if hidden_size is not None else DEFAULT_HIDDEN
    print(f"🧠 Netz-Architektur: {dataset.input_size}→{hs}→{hs}→{hs}")
    # --lr/--lr-schedule (Task #77, v12b): additiv zum bisherigen Verhalten --
    # ohne --lr bleibt LEARNING_RATE aus config.py unveraendert massgeblich,
    # ohne --lr-schedule bleibt Adam mit konstanter LR wie bisher (kein
    # Scheduler-Objekt, kein zusaetzlicher .step()-Aufruf).
    effective_lr = lr if lr is not None else LEARNING_RATE
    # --value-weight/--points-weight (Task #79, v12d): additiv analog zu
    # --lr -- ohne die Flags bleiben VALUE_WEIGHT/POINTS_WEIGHT aus config.py
    # unveraendert massgeblich (Bestandsverhalten). Beeinflussen NUR den
    # Trainings-Loss (loss = p_loss + value_weight*v_loss + points_weight*
    # points_loss) und die Checkpoint-Auswahl (dieselbe gewichtete Val-Metrik,
    # siehe unten) -- NICHT die Targets selbst, der HDF5/Pickle-Cache bleibt
    # deshalb fuer diesen Sweep unveraendert wiederverwendbar.
    effective_value_weight = value_weight if value_weight is not None else VALUE_WEIGHT
    effective_points_weight = points_weight if points_weight is not None else POINTS_WEIGHT
    effective_ownership_weight = ownership_weight if ownership_weight is not None else OWNERSHIP_WEIGHT
    # Task #12: 0 = Skalar-Regression (Bestandsverhalten), >0 = Verteilungs-Kopf.
    effective_points_dist_bins = (points_dist_bins if points_dist_bins is not None
                                  else POINTS_DIST_BINS)
    if effective_points_dist_bins > 0:
        print(f"   Punkte-Kopf   : VERTEILUNG ueber {effective_points_dist_bins} Bins "
              f"(HL-Gauss sigma={POINTS_DIST_SIGMA} Bin-Breiten, Task #12) -- "
              f"Ausgabe bleibt der Erwartungswert")
    print(f"⚙️  Hyperparameter (config.py, ggf. per CLI überschrieben):")
    print(f"   Learning Rate : {effective_lr}" + (f"  (Default {LEARNING_RATE})" if lr is not None else ""))
    print(f"   LR-Schedule   : {lr_schedule}")
    print(f"   Ownership-W   : {effective_ownership_weight}"          f"{'  (Kopf aus)' if effective_ownership_weight <= 0.0 else ''}")
    print(f"   Batch Size    : {BATCH_SIZE}")
    print(f"   Value Weight  : {effective_value_weight}  (Sieg/Niederlage, Aux-Signal fuer den Trunk)"
          + (f"  (Default {VALUE_WEIGHT})" if value_weight is not None else ""))
    print(f"   Points Weight : {effective_points_weight}  (Punktestand-Prognose, Aux-Signal)"
          + (f"  (Default {POINTS_WEIGHT})" if points_weight is not None else ""))
    if encoder == "2d":
        model = Mosaic2DNet(input_size=dataset.input_size, num_actions=NUM_ACTIONS, hidden_size=hs,
                            points_dist_bins=effective_points_dist_bins)
    else:
        model = MosaicNet(input_size=dataset.input_size, num_actions=NUM_ACTIONS, hidden_size=hs,
                          points_dist_bins=effective_points_dist_bins)

    # Warm Start? (Existenz von load_path wurde oben bereits hart validiert)
    if load_version:
        print(f"📥 Lade altes Model als Startpunkt: {load_path.name}")
        ckpt = torch.load(str(load_path), map_location=device)
        old_state = ckpt["model_state"]
        new_state = model.state_dict()
        # strict=False allein reicht NICHT bei INPUT_SIZE-Änderungen: es
        # toleriert fehlende/zusätzliche Keys, aber KEINE Shape-Mismatches
        # bei gleichnamigen Keys (z.B. body.0.weight bei geändertem
        # INPUT_SIZE) — das würde crashen. Shape-inkompatible Keys daher
        # vorher explizit rausfiltern; der Rest (tiefere Body-Schichten,
        # alle Heads) startet weiterhin warm. Alte Checkpoints mit einem
        # value_head.* haben automatisch keine Entsprechung mehr in
        # new_state (Head existiert nicht mehr) -- werden einfach ignoriert.
        if reinit_points_head:
            # Task #12, FAIRER KONTROLLARM: der Verteilungs-Kopf KANN nicht warm
            # starten (andere Ausgabebreite) -- er beginnt zwangslaeufig zufaellig.
            # Ein Kontrollarm, dessen Skalar-Kopf warm startet, waere deshalb im
            # Vorteil, und der A/B wuerde "Verteilung vs. Skalar" mit "frisch vs.
            # warm" vermischen. Mit dieser Option startet auch der Skalar-Kopf
            # frisch, der Unterschied ist dann allein die Kopf-ART.
            drop = [k for k in old_state if k.startswith("points_head.")]
            print(f"   ↻ points_head wird NEU initialisiert ({len(drop)} Tensoren) "
                  f"-- fairer Kontrollarm zu --points-dist-bins")
            old_state = {k: v for k, v in old_state.items() if k not in drop}
        skipped = [k for k in old_state if k in new_state and old_state[k].shape != new_state[k].shape]
        if skipped:
            print(f"   ⚠️  Shape-Mismatch, startet frisch: {', '.join(skipped)}")
            old_state = {k: v for k, v in old_state.items() if k not in skipped}
        model.load_state_dict(old_state, strict=False)

    model.to(device)

    # 4. Training Parameter
    optimizer = optim.Adam(model.parameters(), lr=effective_lr)

    # Epochen-Anzahl ---
    epochs = input_epoch
    print(f"   Epochen       : {epochs}")

    # LR-Scheduler (Task #77, v12b_lr): Cosine-Annealing ueber die angeforderten
    # Epochen (`epochs`, NICHT die evtl. durch Early Stopping tatsaechlich
    # gelaufenen -- T_max ist der volle Deckel, ein frueher Stopp bricht die
    # Kurve einfach vorzeitig ab, das ist unproblematisch). `eta_min=0`
    # (Standard-Verhalten von CosineAnnealingLR) -- die LR faellt bis Epoche
    # `epochs` gegen 0. Kein Scheduler (None) reproduziert exakt das alte
    # Verhalten (konstante LR).
    lr_scheduler = None
    if lr_schedule == "cosine":
        lr_scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    elif lr_schedule not in (None, "none"):
        print(f"   ⚠️  Unbekanntes --lr-schedule '{lr_schedule}' -- ignoriert (konstante LR).")
    if load_version:
        print(f"🔄 Warm-Start erkannt: Trainiere für {epochs} Epochen.")
    else:
        print(f"🆕 Neues Modell: Trainiere für {epochs} Epochen.")
    # --------------------------------------

    # 5. DIE SCHLEIFE
    mse_loss = nn.MSELoss()
    n_batches = len(dataloader)
    policy_history  = []
    value_history   = []
    points_history  = []
    val_ploss_history = []
    # Value/Points hatten bisher KEINEN Val-Split-Loss/R² -- nur der rohe
    # Trainings-Loss wurde reported (siehe TRAINING SUMMARY unten). Für den
    # Runden-Übergangs-Sampling-Vergleich (evaluations/STATUS.md, Phase-1-
    # Gate: points_forecast-Val-R² gegen die archivierte 0.2-0.3-Baseline)
    # braucht es einen echten Held-out-Wert -- Trainings-Loss allein sagt
    # nichts über Generalisierung aus.
    val_vloss_history = []
    val_pointsloss_history = []
    val_value_r2_history = []
    val_points_r2_history = []
    plateau_window    = 5
    plateau_threshold = 0.01
    early_stop_patience = 5 if early_stop else 999999
    policy_plateau_since = None
    stopped_early = False
    stop_reason = None
    total_history = []

    # Best-Checkpoint-Tracking: bisher wurde NUR der letzte Epochenstand
    # gespeichert, auch wenn Early Stopping (Patience-Fenster) erst einige
    # Epochen nach dem eigentlichen Optimum greift (siehe v8c: Minimum bei
    # Epoche 5, Stop typischerweise erst bei Epoche plateau_since+patience).
    # Bestes Modell nach GEWICHTETER Kombination aus Policy-/Value-/Points-
    # Val-Loss (Fallback Train-Loss ohne Val-Split), dieselbe Gewichtung wie
    # der Trainings-Loss selbst -- siehe Kommentar an der Vergleichsstelle
    # unten (Fund 8, Bugfixes.txt: reine Policy-Val-Loss-Auswahl ignorierte
    # den Value-Head, den erklärten Engpass dieser Session) -- zusätzlich als
    # *_best.pth/.onnx sichern.
    best_combined_metric = float("inf")
    best_epoch = None
    best_state_dict = None

    # ── Live-Plot (zusätzlich zur Textausgabe) ──────────────────────────────
    plot = None
    if show_plot:
        try:
            import matplotlib
            import matplotlib.pyplot as plt
            plt.ion()
            fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
            fig.suptitle(f"Training {version_name}")
            ax_top.set_ylabel("Policy Loss")
            ax_bot.set_ylabel("Value / Points Loss (Aux)")
            ax_bot.set_xlabel("Epoche")
            (line_policy,) = ax_top.plot([], [], label="Policy (Train)", color="tab:orange")
            (line_value,) = ax_bot.plot([], [], label="Value (Train)", color="tab:green")
            (line_points,) = ax_bot.plot([], [], label="Points (Train)", color="tab:purple")
            # Val-Kurven (gestrichelt, gleiche Farbe) -- der ganze Grund fuer
            # diese Ergaenzung: das v8-Overfitting (Value Train/Val-Verhaeltnis
            # 48.6x) war an der finalen Zahl allein erkennbar, aber NICHT, AB
            # WELCHER Epoche die Schere aufgeht -- nur sichtbar, wenn Train-
            # und Val-Kurve gemeinsam im Verlauf geplottet werden.
            (line_policy_val,) = ax_top.plot([], [], label="Policy (Val)", color="tab:orange", linestyle="--")
            (line_value_val,) = ax_bot.plot([], [], label="Value (Val)", color="tab:green", linestyle="--")
            (line_points_val,) = ax_bot.plot([], [], label="Points (Val)", color="tab:purple", linestyle="--")
            ax_top.legend(loc="upper right")
            ax_bot.legend(loc="upper right")
            plot = {
                "fig": fig, "ax": ax_top, "ax_bot": ax_bot,
                "line_policy": line_policy, "line_value": line_value, "line_points": line_points,
                "line_policy_val": line_policy_val, "line_value_val": line_value_val, "line_points_val": line_points_val,
                "plateau_line": None,
            }
        except Exception as e:
            print(f"⚠️  Live-Plot deaktiviert (kein Display?): {e}")
            plot = None

    # Diagnose-Instrumentierung (2026-07-31): alle 100 Batches eine RSS/Commit-
    # Zeile, MIT flush=True -- falls der Prozess stirbt, bevor der naechste
    # Puffer-Flush ohnehin faellig waere, steht die letzte Messung trotzdem
    # in der Log-Datei. Absichtlich unabhaengig vom Encoder (auch im Flach-
    # Pfad aktiv) fuer eine direkte Vergleichsbasis.
    _mem_log_every = 100

    for epoch in range(epochs):
        t_loss, t_ploss, t_vloss, t_pointsloss = 0, 0, 0, 0

        for _batch_idx, _batch in enumerate(dataloader):
            if _batch_idx % _mem_log_every == 0:
                _mi = _mem_info_gb()
                if _mi is not None:
                    print(f"  [mem] epoch={epoch+1} batch={_batch_idx}/{n_batches} "
                          f"rss={_mi[0]:.2f}GB commit={_mi[1]:.2f}GB", flush=True)
            # Task #11 Phase 2: MosaicDataset liefert bei encoder="2d" ein
            # 10-Tupel (planes VORAN), bei encoder="flat" (Standard) weiterhin
            # das bestehende 9-Tupel byte-identisch -- siehe
            # `neural_net.py::MosaicDataset.__getitem__`.
            if encoder == "2d":
                planes, states, targets_p, targets_v, masks, moon_targets, pol_w, targets_points, s_rounds, s_own = _batch
                planes = planes.to(device)
            else:
                states, targets_p, targets_v, masks, moon_targets, pol_w, targets_points, s_rounds, s_own = _batch
            states    = states.to(device)
            targets_p = targets_p.to(device)
            targets_v = targets_v.to(device)
            targets_points = targets_points.to(device)
            masks     = masks.to(device)
            pol_w     = pol_w.to(device)

            optimizer.zero_grad()
            _out = model(planes, states) if encoder == "2d" else model(states)
            pred_p, pred_v, pred_moon, pred_points, pred_own = _out[:5]
            pred_points_logits = _out[5] if len(_out) > 5 else None

            # Policy Loss mit Masking:
            # Illegale Aktionen aus pred_p rausrechnen, dann renormalisieren
            masked_logits = pred_p + (masks - 1) * 1e9   # illegale Aktionen auf -inf
            log_probs = F.log_softmax(masked_logits, dim=1)

            per_sample_ce = -torch.sum(targets_p * log_probs, dim=1)   # (B,)
            # Policy-Loss NUR auf echten Drafting-Schritten (pol_w=1); Tiling/Start-
            # One-Hot-Steps (pol_w=0) macht der DFS-Solver — sie würden sonst den
            # Policy-Head mit Tiling-Aktionen fluten und die Drafting-Priors ruinieren.
            # Task #15 B (2026-07-28): Runde-5-Samples optional komplett aus
            # dem Loss nehmen. Das Netz wird in Runde 5 NIE konsultiert
            # (net_mcts.rs:2265 bypassed den Suchpfad zu round5::choose_action,
            # der R4-Bootstrap nutzt round5::exact_round5_outcome) -- ~17% der
            # Value- und ~15% der Policy-Samples gehen dort in Entscheidungen,
            # die ein exakter Alpha-Beta-Solver trifft. Praezedenzfall: pol_w=0
            # fuer Tiling-Schritte, weil das der DFS-Solver macht.
            rw = (s_rounds.to(device) != 5).float() if exclude_round5 else None

            w = pol_w if rw is None else pol_w * rw
            p_loss = (per_sample_ce * w).sum() / w.sum().clamp(min=1e-6)

            # Moon-Order Loss direkt zu Policy-Loss — kein extra Hyperparameter.
            # Plackett-Luce-NLL statt MSE-auf-Rängen: der moon_order_head liefert
            # jetzt echte Präferenz-SCORES, die net_mcts.rs zur Suchzeit direkt als
            # P(Order)-Verteilung nutzt (statt einer bloßen Rang-Regression).
            moon_targets = moon_targets.to(device)
            # BUGFIX: sun_mask prüfte zuvor nur Spalte 0 (blau) auf >=0 — das
            # schloss gültige Sonnenzug-Samples aus, deren Restfarben blau nicht
            # enthielten (z.B. remaining=[gelb,rot]), und verzerrte den Loss
            # systematisch zugunsten blau-haltiger Samples. Jetzt: irgendeine Spalte.
            sun_mask = (moon_targets >= 0).any(dim=1)
            if sun_mask.any():
                moon_nll = plackett_luce_moon_loss(pred_moon, moon_targets)
                p_loss = p_loss + moon_nll[sun_mask].mean()

            # Value-/Punkte-Aux-Losses: reines Trainings-Zusatzsignal fuer den
            # Trunk (Suche/Self-Play nutzt weiterhin nur die Policy, siehe
            # evaluations/stage2_investigation.md) -- klein gewichtet, damit
            # sie den Policy-Loss nicht dominieren.
            rw2 = rw.view(-1, 1) if rw is not None else None
            denom = rw2.sum().clamp(min=1e-6) if rw2 is not None else None
            if rw is None:
                v_loss = mse_loss(pred_v, targets_v)
            else:
                v_loss = (((pred_v - targets_v) ** 2) * rw2).sum() / denom

            # Task #12: bei aktivem Verteilungs-Kopf ist der Punkte-Verlust eine
            # KREUZENTROPIE gegen ein HL-Gauss-geglaettetes Ziel statt MSE auf
            # dem Erwartungswert -- reicheres Gradientensignal, robuster gegen
            # Ausreisser (Farebrother et al. 2024). Der ausgegebene Skalar
            # bleibt der Erwartungswert, die Schnittstelle also unveraendert.
            if pred_points_logits is not None:
                points_loss = points_dist_loss(
                    pred_points_logits, targets_points, model, rw2, denom)
            elif rw is None:
                points_loss = mse_loss(pred_points, targets_points)
            else:
                points_loss = (((pred_points - targets_points) ** 2) * rw2).sum() / denom

            # Ownership-Loss (Task #9): dichtes Hilfsziel, 72 Binaerlabels je
            # Position statt eines Skalars. -1 = unbekannt (unvollstaendiges
            # Spiel) und wird maskiert. Bei Gewicht 0.0 wird der Term komplett
            # uebersprungen -- kein Gradient, Bestandsverhalten unveraendert.
            own_loss = torch.zeros((), device=device)
            if effective_ownership_weight > 0.0:
                own_t = s_own.to(device).float()
                own_m = (own_t >= 0).float()
                if own_m.sum() > 0:
                    own_bce = F.binary_cross_entropy_with_logits(
                        pred_own, own_t.clamp(min=0.0), reduction="none")
                    own_loss = (own_bce * own_m).sum() / own_m.sum()

            loss = (p_loss + effective_value_weight * v_loss
                    + effective_points_weight * points_loss
                    + effective_ownership_weight * own_loss)
            loss.backward()
            optimizer.step()

            t_loss       += loss.item()
            t_ploss      += p_loss.item()
            t_vloss      += v_loss.item()
            t_pointsloss += points_loss.item()

        epoch_ploss = t_ploss / n_batches
        epoch_vloss = t_vloss / n_batches
        epoch_pointsloss = t_pointsloss / n_batches
        epoch_tloss = t_loss / n_batches
        policy_history.append(epoch_ploss)
        value_history.append(epoch_vloss)
        points_history.append(epoch_pointsloss)
        total_history.append(epoch_tloss)

        # ── Validierung (Policy + Value + Points) auf dem NIE trainierten
        # Datei-Split. R² (nicht bloß MSE) je Kopf: 1 - SS_res/SS_tot über
        # den GESAMTEN Val-Split (nicht Mittel über Batch-R²s -- R² ist eine
        # globale Kennzahl, die von der Gesamtvarianz des Val-Sets abhängt,
        # ein Batch-Mittel würde das verzerren). SS_tot/SS_res daher als
        # laufende Summen über alle Batches akkumuliert, R² erst danach
        # einmalig berechnet.
        epoch_val_ploss = None
        epoch_val_vloss = None
        epoch_val_pointsloss = None
        epoch_val_value_r2 = None
        epoch_val_points_r2 = None
        if val_dataloader is not None:
            model.eval()
            val_ploss_sum, val_vloss_sum, val_pointsloss_sum, val_batches = 0.0, 0.0, 0.0, 0
            v_sum, v_sumsq, v_sqerr_sum, n_v = 0.0, 0.0, 0.0, 0
            pts_sum, pts_sumsq, pts_sqerr_sum, n_pts = 0.0, 0.0, 0.0, 0
            with torch.no_grad():
                for _v_batch in val_dataloader:
                    if encoder == "2d":
                        (v_planes, v_states, v_targets_p, v_targets_v, v_masks, _vmoon, v_pol_w,
                         v_targets_points, v_rounds, v_own) = _v_batch
                        v_planes = v_planes.to(device)
                    else:
                        (v_states, v_targets_p, v_targets_v, v_masks, _vmoon, v_pol_w,
                         v_targets_points, v_rounds, v_own) = _v_batch
                    v_states = v_states.to(device)
                    v_targets_p = v_targets_p.to(device)
                    v_targets_v = v_targets_v.to(device)
                    v_targets_points = v_targets_points.to(device)
                    v_masks = v_masks.to(device)
                    v_pol_w = v_pol_w.to(device)
                    _vout = model(v_planes, v_states) if encoder == "2d" else model(v_states)
                    v_pred_p, v_pred_v, _v_pred_moon, v_pred_points, v_pred_own = _vout[:5]
                    v_masked_logits = v_pred_p + (v_masks - 1) * 1e9
                    v_log_probs = F.log_softmax(v_masked_logits, dim=1)
                    v_per_sample_ce = -torch.sum(v_targets_p * v_log_probs, dim=1)
                    v_rw = (v_rounds.to(device) != 5).float() if exclude_round5 else None
                    v_w = v_pol_w if v_rw is None else v_pol_w * v_rw
                    v_p_loss = (v_per_sample_ce * v_w).sum() / v_w.sum().clamp(min=1e-6)
                    # Task #12, WICHTIG: der VALIDIERUNGS-Punkteverlust bleibt
                    # auch bei aktivem Verteilungs-Kopf MSE auf dem
                    # ERWARTUNGSWERT -- absichtlich NICHT die Kreuzentropie des
                    # Trainings. Grund: `val_combined` ist zugleich die
                    # Auswahlmetrik fuer den besten Checkpoint. Waere sie in den
                    # beiden A/B-Armen eine andere GROESSE, waeren die Arme nicht
                    # vergleichbar -- genau der Fehler, der am 2026-07-28 beim
                    # lr1e5-Arm beinahe zur falschen Entscheidung gefuehrt haette
                    # (siehe STATUS.md "Seed-Sweep", Abschnitt val_combined).
                    if v_rw is None:
                        v_v_loss = mse_loss(v_pred_v, v_targets_v)
                        v_points_loss = mse_loss(v_pred_points, v_targets_points)
                    else:
                        v_rw2 = v_rw.view(-1, 1)
                        v_den = v_rw2.sum().clamp(min=1e-6)
                        v_v_loss = (((v_pred_v - v_targets_v) ** 2) * v_rw2).sum() / v_den
                        v_points_loss = (((v_pred_points - v_targets_points) ** 2) * v_rw2).sum() / v_den
                    val_ploss_sum += v_p_loss.item()
                    val_vloss_sum += v_v_loss.item()
                    val_pointsloss_sum += v_points_loss.item()
                    val_batches += 1

                    v_sum += v_targets_v.sum().item()
                    v_sumsq += (v_targets_v ** 2).sum().item()
                    v_sqerr_sum += ((v_targets_v - v_pred_v) ** 2).sum().item()
                    n_v += v_targets_v.numel()

                    pts_sum += v_targets_points.sum().item()
                    pts_sumsq += (v_targets_points ** 2).sum().item()
                    pts_sqerr_sum += ((v_targets_points - v_pred_points) ** 2).sum().item()
                    n_pts += v_targets_points.numel()
            model.train()
            epoch_val_ploss = val_ploss_sum / max(val_batches, 1)
            epoch_val_vloss = val_vloss_sum / max(val_batches, 1)
            epoch_val_pointsloss = val_pointsloss_sum / max(val_batches, 1)

            def _r2(sum_y, sumsq_y, sqerr, n):
                if n == 0:
                    return None
                ss_tot = sumsq_y - (sum_y ** 2) / n
                if ss_tot <= 1e-9:  # entartet: Val-Targets praktisch konstant
                    return None
                return 1.0 - sqerr / ss_tot

            epoch_val_value_r2 = _r2(v_sum, v_sumsq, v_sqerr_sum, n_v)
            epoch_val_points_r2 = _r2(pts_sum, pts_sumsq, pts_sqerr_sum, n_pts)
        val_ploss_history.append(epoch_val_ploss)
        val_vloss_history.append(epoch_val_vloss)
        val_pointsloss_history.append(epoch_val_pointsloss)
        val_value_r2_history.append(epoch_val_value_r2)
        val_points_r2_history.append(epoch_val_points_r2)

        # Fund 8 (externer Hinweis, Bugfixes.txt Abschnitt C): "bestes Modell"
        # wurde bisher NUR nach Policy-Val-Loss gewählt -- der Value-Head
        # (dieser Session zentraler Engpass) lief dabei unbeachtet mit, ein
        # Checkpoint konnte also als "best" markiert werden, waehrend der
        # Value-Head an genau diesem Punkt bereits schlechter war als an
        # einem anderen Epochenstand. Fix: dieselbe gewichtete Kombination
        # wie der Trainings-Loss selbst (`p_loss + VALUE_WEIGHT*v_loss +
        # POINTS_WEIGHT*points_loss`), nur auf den Val-Metriken -- "best"
        # bedeutet jetzt "bestes GESAMTZIEL", nicht mehr "bestes Policy-Val
        # allein". Fallback (kein Val-Split) nutzt dieselbe Formel auf den
        # Trainings-Losses, konsistent mit dem bisherigen Fallback-Muster.
        if epoch_val_ploss is not None:
            current_metric = epoch_val_ploss + effective_value_weight * epoch_val_vloss + effective_points_weight * epoch_val_pointsloss
        else:
            current_metric = epoch_ploss + effective_value_weight * epoch_vloss + effective_points_weight * epoch_pointsloss
        if current_metric < best_combined_metric:
            best_combined_metric = current_metric
            best_epoch = epoch + 1
            best_state_dict = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}

        # ── Plateau-Erkennung (auf Val-Policy-Loss wenn vorhanden, sonst
        # Fallback auf Train-Loss) ───────────────────────────────────────────
        # WARUM Val statt Train: v8b zeigte, dass die Train-Policy-Loss noch
        # bis Epoche 56 weiter sank, waehrend die Val-Policy-Loss bereits ab
        # ~Epoche 15-18 ihr Minimum hatte und danach durchgehend STIEG (2.2 ->
        # 2.67) -- Train-Loss-Plateau-Erkennung haette das nie bemerkt, weil
        # sie ja gar nicht plateaut, sondern normal weiter faellt. `rel < 0`
        # (Val-Loss steigt) unterschreitet plateau_threshold automatisch und
        # loest Early Stopping korrekt aus, auch wenn "PLATEAU" fuer einen
        # tatsaechlich divergierenden Verlauf untertrieben ist.
        has_val_ploss = val_dataloader is not None
        plateau_series = val_ploss_history if has_val_ploss else policy_history
        plateau_marker = ""
        policy_plateaued = False
        if len(plateau_series) >= plateau_window * 2:
            recent   = sum(plateau_series[-plateau_window:]) / plateau_window
            previous = sum(plateau_series[-plateau_window*2:-plateau_window]) / plateau_window
            rel = (previous - recent) / previous if previous > 0 else 0
            if rel < plateau_threshold:
                policy_plateaued = True

        plateau_label = "VAL-POLICY-PLATEAU" if has_val_ploss else "POLICY-PLATEAU"
        if policy_plateaued:
            if policy_plateau_since is None:
                policy_plateau_since = epoch + 1
            plateau_marker = f"  🟡 {plateau_label}"

        # ── Live-Plot aktualisieren (zusätzlich zur Textzeile unten) ────────
        if plot is not None:
            try:
                xs = list(range(1, len(total_history) + 1))
                plot["line_policy"].set_data(xs, policy_history)
                plot["line_value"].set_data(xs, value_history)
                plot["line_points"].set_data(xs, points_history)
                nan = float("nan")
                plot["line_policy_val"].set_data(xs, [v if v is not None else nan for v in val_ploss_history])
                plot["line_value_val"].set_data(xs, [v if v is not None else nan for v in val_vloss_history])
                plot["line_points_val"].set_data(xs, [v if v is not None else nan for v in val_pointsloss_history])
                if policy_plateau_since is not None and plot["plateau_line"] is None:
                    plot["plateau_line"] = plot["ax"].axvline(
                        policy_plateau_since, color="red", linestyle="--", alpha=0.5, label="Plateau")
                    plot["ax"].legend(loc="upper right")
                plot["ax"].relim()
                plot["ax"].autoscale_view()
                plot["ax_bot"].relim()
                plot["ax_bot"].autoscale_view()
                plot["fig"].canvas.draw()
                plot["fig"].canvas.flush_events()
                import matplotlib.pyplot as _plt
                _plt.pause(0.001)
            except Exception:
                plot = None  # Fenster evtl. geschlossen o.ä. — Rest ohne Plot weiterlaufen

        val_p_str = f" | Policy-Val={epoch_val_ploss:5.2f}" if epoch_val_ploss is not None else ""
        val_r2_str = ""
        if epoch_val_value_r2 is not None or epoch_val_points_r2 is not None:
            v_r2_s = f"{epoch_val_value_r2:.3f}" if epoch_val_value_r2 is not None else "n/a"
            p_r2_s = f"{epoch_val_points_r2:.3f}" if epoch_val_points_r2 is not None else "n/a"
            val_r2_str = f" | Val-R² Value={v_r2_s} Points={p_r2_s}"
        lr_str = f" | LR={optimizer.param_groups[0]['lr']:.2e}" if lr_scheduler is not None else ""
        print(f"Epoche {epoch+1:2d}/{epochs} | Policy Loss: {epoch_ploss:6.2f}{val_p_str} "
              f"| Value: {epoch_vloss:.3f} | Points: {epoch_pointsloss:.3f}{val_r2_str}{plateau_marker}{lr_str}")

        # LR-Schedule-Schritt NACH der Epoche (Standard-PyTorch-Reihenfolge:
        # optimizer.step() viele Male innerhalb der Epoche, scheduler.step()
        # einmal danach) -- bleibt bei lr_scheduler=None ein no-op.
        if lr_scheduler is not None:
            lr_scheduler.step()

        # ── Early Stopping (nur bei Policy-Plateau) ──────────────────────────
        if policy_plateau_since is not None:
            since = (epoch + 1) - policy_plateau_since
            if since >= early_stop_patience:
                print(f"\n⏹️  Early Stopping: {plateau_label} seit Epoche {policy_plateau_since} "
                      f"({since} Epochen ohne Fortschritt).")
                stopped_early = True
                stop_reason = "plateau"
                break

    max_loss = math.log(NUM_ACTIONS)
    final_p = epoch_ploss
    pct = final_p / max_loss * 100

    if pct < 8:
        quality = "⚠️  Overfitting-Verdacht"
    elif pct < 25:
        quality = "🟢 Sehr gut"
    elif pct < 40:
        quality = "🟡 Gut"
    elif pct < 70:
        quality = "🟠 Schwaches Signal"
    else:
        quality = "🔴 Nichts gelernt"

    print(f"\n{'='*55}")
    print(f"  TRAINING SUMMARY")
    print(f"{'='*55}")
    print(f"  Epochen:       {epochs}")
    print(f"  Züge:          {len(dataset):,}"
          + (f"  (+{len(val_dataset):,} Val, nie trainiert)" if val_dataset is not None else ""))
    print(f"  Batches/Epoche:{n_batches}")
    print(f"{'─'*55}")
    def _last_valid(history):
        for v in reversed(history):
            if v is not None:
                return v
        return None

    print(f"  Policy Loss:   {final_p:.4f} / {max_loss:.2f} max  ({pct:.1f}%)  {quality}")
    print(f"  Value Loss:    {value_history[-1]:.4f}  (Aux, Sieg/Niederlage +1/-1, Training)")
    print(f"  Points Loss:   {points_history[-1]:.4f}  (Aux, Punktestand-Prognose, Training)")
    final_val_ploss = _last_valid(val_ploss_history)
    final_val_vloss = _last_valid(val_vloss_history)
    final_val_pointsloss = _last_valid(val_pointsloss_history)
    final_value_r2 = _last_valid(val_value_r2_history)
    final_points_r2 = _last_valid(val_points_r2_history)
    if final_val_ploss is not None:
        policy_val_gap = final_val_ploss - final_p
        print(f"  Policy Val-Loss: {final_val_ploss:.4f}  (Gap ggü. Train: {policy_val_gap:+.4f})")
    # Val-R² (nicht bloß Val-Loss) ist die Kennzahl, gegen die die archivierte
    # 0.2-0.3-Plateau-Baseline (evaluations/STATUS.md) vergleichbar ist --
    # Loss allein sagt ohne Referenz-Skala wenig aus.
    if final_val_vloss is not None:
        r2_s = f"{final_value_r2:.4f}" if final_value_r2 is not None else "n/a"
        print(f"  Value Val-Loss:  {final_val_vloss:.4f}  (Val-R²: {r2_s})")
    if final_val_pointsloss is not None:
        r2_s = f"{final_points_r2:.4f}" if final_points_r2 is not None else "n/a"
        print(f"  Points Val-Loss: {final_val_pointsloss:.4f}  (Val-R²: {r2_s})")
    print(f"{'─'*55}")
    if stopped_early:
        print(f"  ⏹️  Early Stopping (Policy-Plateau) nach Epoche {len(policy_history)}/{epochs}")
    if policy_plateau_since:
        print(f"  🟡 Plateau ab Epoche {policy_plateau_since}.")
        print(f"     → Für nächste Generation: mehr Sims im Self-Play.")
    else:
        print(f"  🟢 Kein Plateau — Policy sinkt noch. Mehr Epochen möglich.")
    print(f"{'='*55}")

    # 5b. Netzauslastung (Dead Neurons + Effective Rank)
    try:
        sample_batch = next(iter(dataloader))[0][:512].to(device)
        if sample_batch.shape[0] >= 2:
            cap = model.analyze_capacity(sample_batch)
            print(f"\n{'='*55}")
            print(f"  NETZAUSLASTUNG (Hidden Size: {hs})")
            print(f"{'─'*55}")
            print(f"  {'Schicht':<9} {'Dead':>11} {'Aktiv-Rate':>12} {'Eff.Rank':>15}")
            print(f"  {'─'*51}")
            for ln, m in cap.items():
                dead_str = f"{m['dead']}/{m['n_neurons']} ({m['dead_ratio']*100:.0f}%)"
                rank_str = f"{m['eff_rank']:.0f}/{m['n_neurons']} ({m['rank_pct']*100:.0f}%)"
                print(f"  {ln:<9} {dead_str:>11} {m['active_rate']*100:>11.0f}% {rank_str:>15}")
            print(f"  {'─'*51}")
            avg_dead = sum(m['dead_ratio'] for m in cap.values()) / len(cap)
            avg_rank = sum(m['rank_pct'] for m in cap.values()) / len(cap)
            if avg_dead > 0.4:
                print(f"  🔴 Viele tote Neuronen ({avg_dead*100:.0f}%) — Netz unterausgelastet.")
            elif avg_rank > 0.7:
                print(f"  🟡 Hohe Auslastung (Eff.Rank {avg_rank*100:.0f}%) — bei Plateau mehr Neuronen erwägen.")
            else:
                print(f"  🟢 Gesunde Auslastung (Dead {avg_dead*100:.0f}%, Rank {avg_rank*100:.0f}%).")
            print(f"{'='*55}")
        model.train()
    except Exception as e:
        print(f"  ⚠️  Auslastungsanalyse übersprungen: {e}")

    # 6. Speichern
    model.cpu()
    save_path = MODELS_DIR / f"alphazero_{version_name}.pth"
    actual_epochs = len(policy_history)
    checkpoint = {
        "model_state":       model.state_dict(),
        "version":           version_name,
        "timestamp":         __import__("datetime").datetime.now().isoformat(),
        "epochs":            actual_epochs,
        "epochs_requested":  epochs,
        "early_stopped":     stopped_early,
        "stop_reason":       stop_reason,
        "early_stop_epoch":  policy_plateau_since if stopped_early else None,
        "num_games":         len(dataset),  # Züge
        "input_size":        dataset.input_size,
        "num_actions":       NUM_ACTIONS,
        "hidden_size":       hs,
        "batch_size":        BATCH_SIZE,
        "lr":                effective_lr,
        "lr_schedule":       lr_schedule,
        "final_policy_loss": round(final_p, 4),
        "final_policy_val_loss": round(final_val_ploss, 4) if final_val_ploss is not None else None,
        "final_value_loss":  round(value_history[-1], 4),
        "final_points_loss": round(points_history[-1], 4),
        "final_value_val_loss": round(final_val_vloss, 4) if final_val_vloss is not None else None,
        "final_points_val_loss": round(final_val_pointsloss, 4) if final_val_pointsloss is not None else None,
        "final_value_val_r2": round(final_value_r2, 4) if final_value_r2 is not None else None,
        "final_points_val_r2": round(final_points_r2, 4) if final_points_r2 is not None else None,
        "value_weight":      effective_value_weight,
        "points_weight":     effective_points_weight,
        "val_frac":          val_frac,
        "num_val_games":     len(val_dataset) if val_dataset is not None else 0,
        "policy_pct":        round(pct, 1),
        "load_version":      load_version,
        "value_target_variant": value_target_variant,
        # Task #11 Phase 2: nur ein Bequemlichkeits-/Dokumentationsfeld --
        # `neural_net.py::encoder_from_state_dict` bleibt die maßgebliche,
        # rückwirkend funktionierende Quelle (Erkennung aus `model_state`).
        "encoder":           encoder,
    }
    torch.save(checkpoint, str(save_path))
    print(f"\n✅ Training beendet! Neues Model gespeichert unter:\n📂 {save_path}")

    best_version_name = None
    if best_state_dict is not None and best_epoch != actual_epochs:
        best_idx = best_epoch - 1
        best_checkpoint = dict(checkpoint)
        best_checkpoint["model_state"]      = best_state_dict
        best_checkpoint["epochs"]           = best_epoch
        best_checkpoint["is_best_checkpoint"] = True
        best_checkpoint["selected_by"]      = ("val_combined(p+v*value_w+pts*points_w)" if val_dataloader is not None
                                                else "train_combined(p+v*value_w+pts*points_w)")
        best_checkpoint["final_policy_loss"] = round(policy_history[best_idx], 4)
        best_checkpoint["final_policy_val_loss"] = (
            round(val_ploss_history[best_idx], 4) if val_ploss_history[best_idx] is not None else None)
        best_checkpoint["final_value_loss"]  = round(value_history[best_idx], 4)
        best_checkpoint["final_points_loss"] = round(points_history[best_idx], 4)
        best_checkpoint["final_value_val_loss"] = (
            round(val_vloss_history[best_idx], 4) if val_vloss_history[best_idx] is not None else None)
        best_checkpoint["final_points_val_loss"] = (
            round(val_pointsloss_history[best_idx], 4) if val_pointsloss_history[best_idx] is not None else None)
        best_checkpoint["final_value_val_r2"] = (
            round(val_value_r2_history[best_idx], 4) if val_value_r2_history[best_idx] is not None else None)
        best_checkpoint["final_points_val_r2"] = (
            round(val_points_r2_history[best_idx], 4) if val_points_r2_history[best_idx] is not None else None)
        best_version_name = f"{version_name}_best"
        best_save_path = MODELS_DIR / f"alphazero_{best_version_name}.pth"
        torch.save(best_checkpoint, str(best_save_path))
        print(f"⭐ Bestes Modell (Epoche {best_epoch}, {best_checkpoint['selected_by']}="
              f"{best_combined_metric:.4f}) zusätzlich gespeichert unter:\n📂 {best_save_path}")
    elif best_state_dict is not None:
        print(f"ℹ️  Letzte Epoche ({actual_epochs}) war bereits die beste — kein separater Best-Checkpoint nötig.")

    if plot is not None:
        try:
            plot_path = MODELS_DIR / f"alphazero_{version_name}_loss.png"
            plot["fig"].savefig(str(plot_path))
            print(f"📈 Loss-Verlauf gespeichert unter:\n📂 {plot_path}")
        except Exception as e:
            print(f"⚠️  Loss-Plot konnte nicht gespeichert werden: {e}")

    # 7. ONNX direkt mitexportieren (Rust-Inferenz für Self-Play/Arena), damit
    #    kein manueller export_onnx.py-Schritt nötig ist.
    try:
        from export_onnx import export
        export(version_name)
    except Exception as e:
        print(f"⚠️  ONNX-Export übersprungen (manuell nachholbar: python export_onnx.py --version {version_name}): {e}")
    if best_version_name is not None:
        try:
            from export_onnx import export
            export(best_version_name)
        except Exception as e:
            print(f"⚠️  ONNX-Export (Best) übersprungen "
                  f"(manuell nachholbar: python export_onnx.py --version {best_version_name}): {e}")

    # 8. Modell-Snapshot ins OneDrive-Backup (Nutzer-Entscheid 2026-07-24 nach
    #    dem models/-Datenverlust: ereignisgesteuert nach JEDEM Training statt
    #    nur zeitgesteuert). Scheitert leise mit Warnung — ein Backup-Problem
    #    darf nie ein fertiges Training entwerten.
    if snapshot:
        _snapshot_models_to_backup(version_name)
    else:
        print("💾 Modell-Snapshot uebersprungen (--no-snapshot): fuer Ablations-/Sweep-Laeufe, "
              "deren Checkpoints per --seed reproduzierbar und keine Champions sind. "
              "Ein Snapshot je Lauf zippt den GESAMTEN models/-Ordner (>140 MB).")


def _snapshot_models_to_backup(version_name: str) -> None:
    """Zippt den kompletten models/-Ordner als datierten, nach dem Training
    benannten Snapshot nach <OneDrive>\\Backups\\mosaic-AI\\models_snapshots\\."""
    try:
        import os
        import shutil
        from datetime import datetime
        onedrive = os.environ.get("OneDrive")
        if not onedrive:
            print("⚠️  Modell-Snapshot übersprungen: OneDrive-Umgebungsvariable nicht gesetzt.")
            return
        snap_dir = Path(onedrive) / "Backups" / "mosaic-AI" / "models_snapshots"
        snap_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
        target = snap_dir / f"models_{stamp}_{version_name}"
        archive = shutil.make_archive(str(target), "zip", str(MODELS_DIR))
        size_mb = os.path.getsize(archive) / 1e6
        print(f"💾 Modell-Snapshot gesichert: {archive} ({size_mb:.0f} MB)")
    except Exception as e:
        print(f"⚠️  Modell-Snapshot fehlgeschlagen (Training davon unberührt): {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trainiere das Mosaic-AI Neuronale Netz")
    parser.add_argument("--name", type=str, required=True, help="Name der neuen Version, z.B. v2")
    parser.add_argument("--load", type=str, default=None, help="Name der alten Version für Warm Start, z.B. v1")
    parser.add_argument("--epochs", type=int, default=15, help="Wieviele Epochen")
    parser.add_argument("--hidden", type=int, default=None, help="Hidden Layer Größe (Standard: aus config.py)")
    parser.add_argument("--no-early-stop", action="store_true", help="Early Stopping deaktivieren")
    parser.add_argument("--no-plot", action="store_true",
                        help="Live-Loss-Plot deaktivieren (z.B. ohne Display)")
    parser.add_argument("--val-frac", type=float, default=0.1,
                        help="Anteil der Spiele-DATEIEN (nicht Züge), der als Val-Split nie "
                             "trainiert wird (Standard: 0.1). 0 deaktiviert den Split.")
    parser.add_argument("--train-file-limit", type=int, default=None,
                        help="Begrenzt die TRAININGS-Dateien (nach Abzug des Val-Splits) auf N "
                             "(Daten-Skalierungs-Ablation, Task #69). Val-Split bleibt unveraendert "
                             "identisch zu einem Lauf ohne dieses Flag.")
    parser.add_argument("--lr", type=float, default=None,
                        help="Start-Learning-Rate fuer Adam (Standard: LEARNING_RATE aus config.py, "
                             "aktuell 0.0004). Task #77 (v12b_lr): Warm-Start-Feintuning-Kontrolle "
                             "mit niedrigerer Start-LR.")
    parser.add_argument("--no-snapshot", action="store_true",
                        help="Den OneDrive-Modell-Snapshot nach dem Training auslassen. "
                             "Gedacht fuer Ablations-/Seed-Sweep-Laeufe: der Hook zippt den "
                             "GESAMTEN models/-Ordner (>140 MB) je Lauf, was bei einem Sweep "
                             "mehrere GB fast identischer Archive erzeugt. Fuer echte "
                             "Generationen NICHT setzen -- der Hook ist die Absicherung nach "
                             "dem models/-Datenverlust vom 2026-07-24.")
    parser.add_argument("--seed", type=int, default=None,
                        help="Seed fuer Gewichts-Init und Batch-Shuffling. Default None = "
                             "altes, unseeded Verhalten. Zwei Arme eines A/B mit DEMSELBEN "
                             "Seed unterscheiden sich allein durch die getestete Aenderung "
                             "-- ohne Seed vermischt sich der Effekt mit der Lauf-zu-Lauf-"
                             "Varianz (die in diesem Projekt bis 2026-07-28 nie gemessen wurde).")
    parser.add_argument("--reinit-points-head", action="store_true",
                        help="Den points_head beim Warm-Start NEU initialisieren statt ihn zu "
                             "uebernehmen. Fairer Kontrollarm zu --points-dist-bins: der "
                             "Verteilungs-Kopf kann nicht warm starten (andere Ausgabebreite), "
                             "ein Vergleich gegen einen warm gestarteten Skalar-Kopf vermischt "
                             "sonst 'Verteilung vs Skalar' mit 'frisch vs warm'.")
    parser.add_argument("--points-dist-bins", type=int, default=None,
                        help="Task #12: Anzahl Bins fuer den DISTRIBUTIONALEN Punkte-Kopf. "
                             "0 = aus (Skalar-Regression, Standard). Typisch 51 (C51). Der Kopf "
                             "sagt dann eine Verteilung der tanh-gestauchten Punktedifferenz "
                             "vorher und wird per Kreuzentropie gegen ein HL-Gauss-geglaettetes "
                             "Ziel trainiert; nach aussen wird weiterhin der ERWARTUNGSWERT als "
                             "Skalar ausgegeben, die ONNX-Schnittstelle out[0..3] bleibt also "
                             "unveraendert. ACHTUNG: warm-gestartete points_head-Gewichte passen dann nicht mehr (Shape-Mismatch) und starten frisch -- die Warnung dazu ist erwuenscht.")
    parser.add_argument("--ownership-weight", type=float, default=None,
                        help="Task #9: Gewicht des Ownership-Hilfsziels (72 Binaerlabels je "
                             "Position: wird dieses Kuppelfeld am SPIELENDE belegt sein?). "
                             "Standard OWNERSHIP_WEIGHT aus config.py (aktuell 0.0 = Kopf aus, "
                             "Bestandsverhalten byte-identisch). Motivation: der beste "
                             "Checkpoint lag bei v15/v16/v17 stets bei Epoche 1-3, dem Netz "
                             "fehlt lernbares Signal pro Sample, nicht Sample-Anzahl -- dieser "
                             "Kopf liefert 72 Gradienten statt eines Skalars. Zielbalance "
                             "gemessen 41/59.")
    parser.add_argument("--exclude-round5", action="store_true",
                        help="Task #15 B: Runde-5-Samples komplett aus Value-, Points- UND "
                             "Policy-Loss nehmen (Training UND Validierung, damit die "
                             "Checkpoint-Auswahl konsistent ist). Begruendung: das Netz wird "
                             "in Runde 5 nie konsultiert -- net_mcts.rs:2265 bypassed den "
                             "Suchpfad zu round5::choose_action (exakte Alpha-Beta-Suche), "
                             "und der Runde-4-Bootstrap nutzt round5::exact_round5_outcome. "
                             "~17%% der Value- und ~15%% der Policy-Samples liegen dort.")
    parser.add_argument("--lr-schedule", type=str, default="none", choices=["none", "cosine"],
                        help="LR-Verlauf ueber die Epochen. 'none' (Standard): konstante LR wie bisher. "
                             "'cosine': torch.optim.lr_scheduler.CosineAnnealingLR mit T_max=--epochs.")
    parser.add_argument("--value-weight", type=float, default=None,
                        help="Gewicht des Value-Aux-Loss im Gesamt-Loss (Standard: VALUE_WEIGHT aus "
                             "config.py, aktuell 0.2). Task #79 (v12d): VALUE_WEIGHT/POINTS_WEIGHT-Sweep. "
                             "Wirkt nur im Loss/der Checkpoint-Auswahl, nicht im Cache/Targets.")
    parser.add_argument("--points-weight", type=float, default=None,
                        help="Gewicht des Punktestand-Aux-Loss im Gesamt-Loss (Standard: POINTS_WEIGHT "
                             "aus config.py, aktuell 0.5). Siehe --value-weight.")
    parser.add_argument("--value-target-variant", type=str, default="nortv",
                        choices=["default", "nortv", "nortv_r1"],
                        help="Task #84 (rtv-Ablation Phase 1). STANDARD SEIT 2026-07-28: 'nortv' "
                             "(vorher 'default'). Begruendung: v13_nortv_best schlug den Champion "
                             "v12b_lr_best 171:129 allein durch das Weglassen des rtv-Overrides im "
                             "Value-Target, bei zugleich ~3x guenstigerem Self-Play -- und JEDE "
                             "Generation seit v15 wurde ohnehin explizit mit 'nortv' trainiert, der "
                             "alte Default wurde faktisch nie genutzt. Ihn stehen zu lassen war nur "
                             "ein Footgun (Flag vergessen = stillschweigend schlechteres Netz). "
                             "'default' bleibt waehlbar, um Alt-Laeufe byte-identisch zu "
                             "reproduzieren (rtv-Override bevorzugt, wo vorhanden); 'nortv_r1' "
                             "ignoriert den Override nur fuer Runde-1-Zustaende. Aendert den "
                             "HDF5-Cache-Key (siehe neural_net.py::MosaicDataset).")
    parser.add_argument("--encoder", type=str, default="flat", choices=["flat", "2d"],
                        help="Task #11 Phase 2. 'flat' (Standard, Bestandsverhalten byte-identisch): "
                             "MosaicNet auf state_to_tensor (708 Features). '2d': Mosaic2DNet -- "
                             "Conv-Zweig auf state_to_planes ([76,6,6]) + Flach-Zweig auf demselben "
                             "708er-Vektor, spaete Fusion (siehe docs/design_2d_encoder.md). "
                             "Aendert den HDF5-Cache-Key (Suffix '+enc2d_v1', der Flach-Cache derselben "
                             "Dateiliste bleibt unberuehrt). --load erwartet dann einen 2D-Checkpoint "
                             "(harter Fehler bei Encoder-Mismatch statt stillem Teil-Load).")

    args = parser.parse_args()

    train(points_dist_bins=args.points_dist_bins, reinit_points_head=args.reinit_points_head,
          version_name=args.name, load_version=args.load, input_epoch=args.epochs,
          hidden_size=args.hidden, early_stop=not args.no_early_stop,
          show_plot=not args.no_plot, val_frac=args.val_frac,
          train_file_limit=args.train_file_limit, lr=args.lr, lr_schedule=args.lr_schedule,
          exclude_round5=args.exclude_round5, ownership_weight=args.ownership_weight,
          seed=args.seed, snapshot=not args.no_snapshot,
          value_weight=args.value_weight, points_weight=args.points_weight,
          value_target_variant=args.value_target_variant, encoder=args.encoder)
