"""
Self-Play Datengenerierung für Mosaic-AI — Rust-Hybrid.

Die gesamte Spiel-/Suchschleife läuft jetzt in Rust (`mosaic_rust.self_play_games`,
rayon-parallel, GIL frei). Dieses Skript ist nur noch der schlanke Treiber: es
ruft Rust auf, gruppiert die zurückgelieferten Step-Records nach Spiel und
pickled sie im UNVERÄNDERTEN Format (das `train.py` / `MosaicDataset` liest).

Modi:
  --mode mcts             Heuristik-MCTS in Rust (kein Netz)
  --mode mcts --model X   Heuristik-MCTS, ZUSÄTZLICH mit round_transition_value-
                          Labels aus Modell X (Netz-Chance-Node-Sampling an den
                          vier Rundenübergängen, siehe round_transition_deep.rs)
                          -- Zugentscheidungen bleiben komplett heuristisch
  --mode network          AlphaZero-Netz in Rust (Phase B: benötigt ONNX-Export)

Verwendung:
  python self_play.py --mode mcts --games 1500 --sims 50 --version v0 --threads 8
  python self_play.py --mode mcts --model alphazero_v8c.onnx --games 500 --sims 50 --version v0
"""
import os
import sys
import json
import time
import pickle
import argparse
import multiprocessing as mp
import queue as _queue_mod
from datetime import datetime

# Windows-Konsolen (cp1252) können die Emoji-Ausgaben sonst nicht kodieren.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from config import DATA_DIR, MODELS_DIR, BASE_DIR

try:
    import mosaic_rust as _mr
except ImportError as e:  # pragma: no cover
    raise SystemExit(
        "❌ Rust-Modul 'mosaic_rust' nicht gefunden. Bitte zuerst bauen:\n"
        "   cd engine && maturin build --release  (dann das Wheel installieren)\n"
        f"(Import-Fehler: {e})"
    )

# ── Hänger-Schutz auf Prozessebene ───────────────────────────────────────────
# Fund (round_transition_deep.rs-Debugging, siehe dortige Kommentare zu
# Gamma-Pruning): die internen Rust-Timeouts (heuristic_game_timeout_secs /
# EXTRA_GAME_TIMEOUT_SECS) greifen unter realer Last nicht immer zuverlässig
# -- eine isolierte Wiederholung des exakten Seeds einer 40+ Minuten
# gehängten Partie lief sauber in 77s durch. Ursache: Gamma-Prunings
# Sample-Zahl hängt von Wall-Clock-Deadlines ab, wodurch derselbe Seed unter
# unterschiedlicher Systemlast unterschiedlich viel RNG verbraucht --
# "Seed -> deterministische Partie" gilt nicht mehr uneingeschränkt. Da das
# nicht auf eine einzelne behebbare Zeile zurückgeführt werden konnte, hier
# stattdessen ein externes Sicherheitsnetz: jeder Chunk läuft in einem
# eigenen Subprozess mit Wall-Clock-Timeout; hängt er, wird er hart beendet
# und (mit neuem Seed, da chunk_idx den Seed mitbestimmt) automatisch neu
# versucht, statt den ganzen Lauf zu blockieren.
GAME_HANG_SAFETY_FACTOR = 5  # externe Grenze = Vielfaches des internen Timeouts
MIN_CHUNK_TIMEOUT_SECS = 120
# Harte AUSSEN-Obergrenze (2026-07-21, netcq-Batch), NICHT mehr der primäre
# Kill-Trigger seit Task #71 (siehe HEARTBEAT_TIMEOUT_SECS unten) -- reiner
# Not-Deckel gegen den Fall, dass der Herzschlag selbst aus irgendeinem Grund
# dauerhaft weiterläuft, ohne dass der Chunk je fertig wird. Die Hänger sind
# INTRINSISCH (seltener Spielzustand -> 1 Rust-Thread spinnt auf 100%, alle
# anderen rayon-Worker idle; auch SOLO ohne Parallellast beobachtet, py-spy-
# Dump: Python-Hauptthread parkt in rayons WaitOnAddress).
MAX_CHUNK_TIMEOUT_SECS = 450
# Task #71: primärer Kill-Trigger -- der Supervisor beendet einen Chunk NICHT
# mehr, sobald er insgesamt "zu lange" braucht (das verwechselt "langsam
# unter Last" mit "tot"), sondern nur noch, wenn der Fortschritts-Herzschlag
# (Rust schreibt ihn per Zug, siehe self_play.rs::start_heartbeat_reporter)
# für HEARTBEAT_TIMEOUT_SECS ausbleibt. WICHTIG: der Zug-Zähler tickt NICHT
# während eines laufenden Rundenübergangs-Samplings (das passiert innerhalb
# EINES Zugs, bevor der nächste Zähler-Tick kommt) -- der theoretische
# Worst-Case-Abstand zweier Ticks (falls ALLE Not-Deckel gleichzeitig voll
# ausgeschöpft würden, was die Kalibrierung nie beobachtet hat) liegt bei
# Runde 2/3 bei bis zu ~130s (75s Rundenübergang + 55s Bootstrap-Fortsetzung,
# siehe round_transition_deep.rs-Konstanten). 180s Toleranz lässt dafür
# komfortabel Luft, bleibt aber weit unter dem alten starren 450s-Deckel.
HEARTBEAT_TIMEOUT_SECS = 180
HEARTBEAT_POLL_INTERVAL_SECS = 5
MAX_CONSECUTIVE_CHUNK_FAILURES = 3


# ── Windows Keep-Awake (verhindert System-Standby während eines Laufs) ──────
# Fund (2026-07-22): der Nacht-Batch (--mode network, 2000 Spiele) brach nach
# 300/2000 Spielen mitten im Fortschritt ab -- Log endet fehlerlos (kein
# Chunk-Hänger, kein Traceback), Harness meldet den Prozess um ~00:30 Uhr als
# "killed". Ursache: Windows-Standby, nicht der Chunk-Supervisor. Diese
# Prozess-lokale API haelt das System wach, SOLANGE dieser Python-Prozess
# lebt (ES_SYSTEM_REQUIRED) -- bewusst OHNE ES_DISPLAY_REQUIRED, der Monitor
# darf ausgehen. Kein Eingriff in Systemeinstellungen/Registry, wirkt nur für
# diesen Prozess und wird beim Lauf-Ende (auch bei Fehlern, via `finally`)
# wieder auf ES_CONTINUOUS zurückgesetzt.
_ES_CONTINUOUS = 0x80000000
_ES_SYSTEM_REQUIRED = 0x00000001


def _keep_system_awake() -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.kernel32.SetThreadExecutionState(_ES_CONTINUOUS | _ES_SYSTEM_REQUIRED)
    except Exception:
        pass  # Best-effort -- ein fehlender Keep-Awake darf den Lauf nicht verhindern.


def _allow_system_sleep() -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.kernel32.SetThreadExecutionState(_ES_CONTINUOUS)
    except Exception:
        pass


def _internal_game_timeout_secs(sims: int, has_model: bool) -> int:
    """Spiegelt self_play.rs::heuristic_game_timeout_secs/EXTRA_GAME_TIMEOUT_SECS,
    um die externe Supervisor-Grenze proportional dazu zu skalieren.
    Task #71: EXTRA_GAME_TIMEOUT_SECS neu kalibriert (12+75+75+45=207 statt
    5+30+30+30=95, siehe round_transition_deep.rs -- die alten Zeitbudgets
    waren als primärer Cutoff zu knapp bemessen, jetzt nur noch Not-Deckel)."""
    base = max(30, (sims * 3) // 10)
    if has_model:
        base += 12 + 75 + 75 + 45  # EXTRA_GAME_TIMEOUT_SECS (Runde 4..1)
    return base


def _chunk_timeout_secs(n_games: int, threads: int, sims: int, has_model: bool) -> int:
    workers = threads if threads and threads > 0 else (os.cpu_count() or 1)
    waves = -(-n_games // max(1, workers))  # ceil
    per_game = _internal_game_timeout_secs(sims, has_model)
    return min(MAX_CHUNK_TIMEOUT_SECS,
               max(MIN_CHUNK_TIMEOUT_SECS, waves * per_game * GAME_HANG_SAFETY_FACTOR))


def _worker_run_chunk(mode, model, n, simulations, c_puct, seed, threads, prefix,
                      add_root_noise, deterministic, queue, progress_path, heartbeat_path):
    """Läuft im Subprozess (siehe Modul-Kommentar oben) -- reine Rust-Aufruf-
    Weiterleitung, damit sie per multiprocessing.Process spawnbar ist.
    `progress_path`/`heartbeat_path` (Task #71): an die Rust-Seite
    durchgereicht -- Einzelspiel-Flush (JSONL) + periodischer Herzschlag,
    siehe self_play.rs::run_net_self_play & Geschwister."""
    try:
        import mosaic_rust as mr
        if mode == "network":
            raw = mr.net_self_play_games(
                model_path=model, n_games=n, base_sims=simulations, c_puct=c_puct,
                seed=seed, num_threads=threads, prefix=prefix,
                add_root_noise=add_root_noise, deterministic=deterministic,
                progress_path=progress_path, heartbeat_path=heartbeat_path,
            )
        elif mode == "mcts" and model:
            raw = mr.self_play_games_with_net_labels(
                model_path=model, n_games=n, base_sims=simulations,
                seed=seed, num_threads=threads, prefix=prefix,
                progress_path=progress_path, heartbeat_path=heartbeat_path,
            )
        else:
            raw = mr.self_play_games(
                n_games=n, base_sims=simulations, seed=seed,
                num_threads=threads, prefix=prefix,
                progress_path=progress_path, heartbeat_path=heartbeat_path,
            )
        queue.put(("ok", raw))
    except Exception as e:  # pragma: no cover
        queue.put(("error", repr(e)))


def _recover_partial_progress(progress_path) -> list[list[dict]]:
    """Liest eine (möglicherweise durch einen harten Kill mitten im Schreiben
    abgebrochene) JSONL-Fortschrittsdatei -- eine Zeile je fertigem Spiel
    (siehe self_play.rs::append_game_progress). Toleriert eine unvollständige
    LETZTE Zeile (Kill mitten im Schreibvorgang, trotz Flush ein theoretisch
    möglicher Rest-Fall bei OS-Puffergrenzen) -- überspringt sie stumm statt
    abzustürzen. Gibt eine Liste bereits vollständiger Spiele zurück (je eine
    Step-Liste, direkt kompatibel mit `_group_by_game`s Rückgabeformat)."""
    games: list[list[dict]] = []
    if progress_path is None or not progress_path.exists():
        return games
    with open(progress_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                game_steps = json.loads(line)
            except json.JSONDecodeError:
                continue  # unvollständige/kaputte letzte Zeile -- verwerfen, nicht crashen
            if isinstance(game_steps, list) and game_steps:
                games.append(game_steps)
    return games


def _cleanup_progress_files(progress_path, heartbeat_path) -> None:
    """Räumt die Zwischendateien eines Chunk-Versuchs auf (best-effort) --
    weder auf Erfolg (Inhalt bereits im `raw`-JSON enthalten) noch auf
    Wiederherstellung (Inhalt bereits ins `buffer` übernommen) wird die
    JSONL/Heartbeat-Datei noch gebraucht."""
    for p in (progress_path, heartbeat_path):
        if p is not None:
            try:
                p.unlink(missing_ok=True)
            except OSError:
                pass


def _run_chunk_supervised(mode, model, n, simulations, c_puct, seed, threads, prefix,
                          add_root_noise, deterministic, timeout_secs,
                          progress_path, heartbeat_path) -> str | None:
    """Führt einen Chunk in einem Subprozess aus. Task #71: der primäre
    Kill-Trigger ist jetzt der Fortschritts-HERZSCHLAG (`heartbeat_path`s
    mtime), nicht mehr ein starres Gesamt-Timeout -- unterscheidet "läuft
    noch, nur langsam unter Last" von "hängt/ist tot". `timeout_secs` bleibt
    als äußerer Not-Deckel (MAX_CHUNK_TIMEOUT_SECS-basiert) zusätzlich aktiv.
    Gibt das rohe JSON zurück, oder None bei Hänger/Timeout (Aufrufer liest
    dann `progress_path` für die bereits geflushten Spiele und retried nur
    den fehlenden Rest -- siehe `generate_data`)."""
    queue: mp.Queue = mp.Queue()
    proc = mp.Process(
        target=_worker_run_chunk,
        args=(mode, model, n, simulations, c_puct, seed, threads, prefix,
              add_root_noise, deterministic, queue,
              str(progress_path), str(heartbeat_path)),
    )
    proc.start()
    t_start = time.time()
    last_heartbeat_seen = t_start  # Prozessstart zaehlt als initialer Herzschlag
    while True:
        # WICHTIG: das Ergebnis MUSS aus der Queue gelesen werden, während wir
        # warten, nicht erst nach proc.join() -- der Payload (JSON mehrerer
        # Partien) kann den OS-Pipe-Puffer überschreiten; der Feeder-Thread des
        # Kindprozesses blockiert dann beim Schreiben, und der Prozess bleibt
        # "am Leben", bis jemand aus der Queue liest. Ein join() VOR dem get()
        # würde also bei jedem größeren Chunk fälschlich als Hänger erkannt
        # (klassische multiprocessing-Falle, siehe Queue-Doku). Kurzes Poll-
        # Intervall statt eines einzigen langen `get(timeout=...)`, damit wir
        # zwischendurch den Herzschlag prüfen können.
        try:
            status, payload = queue.get(timeout=HEARTBEAT_POLL_INTERVAL_SECS)
            proc.join()
            if status == "error":
                raise RuntimeError(f"Rust-Self-Play-Fehler im Subprozess: {payload}")
            return payload
        except _queue_mod.Empty:
            pass

        try:
            hb_mtime = heartbeat_path.stat().st_mtime
            if hb_mtime > last_heartbeat_seen:
                last_heartbeat_seen = hb_mtime
        except FileNotFoundError:
            pass  # Noch kein Herzschlag geschrieben -- Prozessstart bleibt Referenz.

        stale_secs = time.time() - last_heartbeat_seen
        elapsed_secs = time.time() - t_start
        if stale_secs > HEARTBEAT_TIMEOUT_SECS:
            print(f"  ⚠️  Herzschlag ausgeblieben (Seed {seed}, {stale_secs:.0f}s ohne Fortschritt) -- "
                  f"beende Subprozess und versuche mit neuem Seed erneut.")
        elif elapsed_secs > timeout_secs:
            print(f"  ⚠️  Chunk-Notdeckel erreicht (Seed {seed}, > {timeout_secs}s trotz Herzschlag) -- "
                  f"beende Subprozess und versuche mit neuem Seed erneut.")
        else:
            continue
        proc.terminate()
        proc.join(10)
        if proc.is_alive():  # pragma: no cover
            proc.kill()
            proc.join()
        return None


def _group_by_game(steps: list[dict]) -> list[list[dict]]:
    """Gruppiert die flache Step-Liste nach `game_id` (Reihenfolge bleibt erhalten)."""
    games: list[list[dict]] = []
    current_id = object()  # Sentinel
    for step in steps:
        gid = step.get("game_id")
        if gid != current_id:
            current_id = gid
            games.append([])
        games[-1].append(step)
    return games


def _check_completion(steps: list[dict], filename) -> None:
    """Prüft je Datei, wie viele Partien wirklich Phase::End erreicht haben
    (Rust-Feld 'completed', siehe self_play.rs). Abgebrochene Partien (Hänger-
    Schutz-Timeout) haben KEIN echtes Endergebnis in scores/winner — wurde als
    echter Bug beobachtet (30s-Timeout bei netzgeführter Suche zu knapp, siehe
    archive/STAGE2_TODO_ARCHIVED.md), deshalb hier ein Sanity-Check bei jeder
    generierten Datei."""
    games = _group_by_game(steps)
    if not games:
        return
    n = len(games)
    n_complete = sum(1 for g in games if g and g[-1].get("completed", True))
    if n_complete < n:
        print(f"  ⚠️  {filename.name}: nur {n_complete}/{n} Partien komplett "
              f"(Rest durch Hänger-Schutz abgebrochen — scores/winner unzuverlässig!)")


def _flush(steps: list[dict], version_name: str, tag: str, game_count: int) -> None:
    """Schreibt die akkumulierten Steps in eine .pkl (Dateinamens-Schema wie bisher)."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    file_tag = f"_{tag}" if tag else ""
    filename = DATA_DIR / f"selfplay_{version_name}{file_tag}_{timestamp}_g{game_count}.pkl"
    with open(filename, "wb") as f:
        pickle.dump(steps, f)
    _check_completion(steps, filename)
    print(f"💾 {len(steps)} Züge gespeichert in '{filename}'")


# ── Lauf-Manifest (#64 Teil 1, Phase 2a, 2026-07-22) ─────────────────────────
# Ein Self-Play-Lauf soll rückwirkend rekonstruierbar sein: welche CLI-Args,
# welcher Rust-Commit-Stand, welche aktiven Suchkonstanten haben DIESE Daten
# erzeugt -- ohne den Rust-Quellcode zum jeweiligen Stand extra auschecken zu
# müssen. Alles hier best-effort (git/engine_config_json können fehlen, z.B.
# in einem isolierten Wheel-Export ohne .git oder mit altem Wheel ohne die
# neue pyo3-Funktion) -- ein Manifest-Fehler darf den eigentlichen
# Self-Play-Lauf NIE verhindern.

def _git_commit_hash() -> str | None:
    """Best-effort HEAD-Commit-Hash. None, wenn nicht ermittelbar."""
    import subprocess
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=str(BASE_DIR),
            capture_output=True, text=True, timeout=5, check=True,
        )
        return out.stdout.strip()
    except Exception:
        return None


def _git_is_dirty() -> bool | None:
    """Best-effort: gibt es uncommittete Änderungen im Arbeitsbaum? None,
    wenn nicht ermittelbar -- wichtig fürs Manifest, sonst sieht ein Lauf
    gegen einen unsauberen Stand fälschlich wie ein sauberer Commit aus."""
    import subprocess
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain"], cwd=str(BASE_DIR),
            capture_output=True, text=True, timeout=5, check=True,
        )
        return bool(out.stdout.strip())
    except Exception:
        return None


def _engine_config() -> dict:
    """Aktive Rust-Suchkonstanten, siehe `mosaic_rust.engine_config_json`
    (lib.rs). Best-effort: ein altes Wheel ohne diese Funktion (AttributeError)
    darf das Manifest nicht verhindern, nur diesen Teil leer/fehlerhaft lassen."""
    try:
        return json.loads(_mr.engine_config_json())
    except Exception as e:
        return {"_error": f"engine_config_json nicht verfügbar: {e!r}"}


def _write_run_manifest(version_name: str, run_timestamp: str, cli_args: dict) -> None:
    """Schreibt `data/manifest_<version>_<timestamp>.json` neben die
    generierten .pkl-Dateien."""
    manifest = {
        "version": version_name,
        "run_timestamp": run_timestamp,
        "cli_args": cli_args,
        "git_commit": _git_commit_hash(),
        "git_dirty": _git_is_dirty(),
        "engine_config": _engine_config(),
    }
    path = DATA_DIR / f"manifest_{version_name}_{run_timestamp}.json"
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        print(f"📝 Lauf-Manifest geschrieben: '{path}'")
    except Exception as e:
        print(f"  ⚠️  Manifest konnte nicht geschrieben werden ({e!r}) -- Self-Play läuft trotzdem weiter.")


def generate_data(mode: str, num_games: int, simulations: int, version_name: str,
                  tag: str = None, threads: int = 0, chunk: int = 10, seed: int = None,
                  per_file: int = 10, model: str = None, c_puct: float = 1.5,
                  add_root_noise: bool = True, deterministic: bool = False):
    if mode not in ("mcts", "network"):
        raise SystemExit(f"❌ Unbekannter Modus: {mode}. Verwende 'mcts' oder 'network'.")
    if mode == "network" and not model:
        raise SystemExit(
            "❌ --mode network benötigt --model (z.B. alphazero_s100.onnx). "
            "Vorher 'export_onnx.py <version>' bzw. train.py ausführen."
        )
    if model:
        # --model gegen den models/-Ordner auflösen: der bloße Dateiname genügt
        # (z.B. "alphazero_s100.onnx"). Ein existierender expliziter Pfad bleibt.
        # Gilt jetzt auch für --mode mcts (siehe unten, Netz-Rundenübergangs-
        # Labels) -- nicht mehr nur für --mode network.
        from pathlib import Path
        model_path = Path(model)
        if not model_path.exists():
            model_path = MODELS_DIR / model
        if not model_path.exists():
            raise SystemExit(f"❌ Modell nicht gefunden: '{model}' (auch nicht in {MODELS_DIR}/)")
        model = str(model_path)

    import random as _random
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = f"{version_name}{('_' + tag) if tag else ''}_{run_timestamp}"
    base_seed = seed if seed is not None else _random.randint(0, 2**31 - 1)
    chunk = max(1, chunk)
    per_file = max(1, per_file)

    _write_run_manifest(version_name, run_timestamp, {
        "mode": mode, "games": num_games, "sims": simulations, "version": version_name,
        "tag": tag, "threads": threads, "chunk": chunk, "seed": base_seed,
        "per_file": per_file, "model": model, "c_puct": c_puct,
        "add_root_noise": add_root_noise, "deterministic": deterministic,
    })

    # Nur der Rust-Aufruf unterscheidet sich je Modus; Fortschritt/Gruppierung/
    # Pickle teilen sich beide Pfade. MCTS = Heuristik-Suche; network = Netz-PUCT
    # (Priors vom Netz, Blatt immer per exaktem DFS-Solver), Policy-Target =
    # rohe Visit-Verteilung N/ΣN.
    has_model = bool(model)
    timeout_secs = _chunk_timeout_secs(chunk, threads, simulations, has_model and mode == "mcts")
    if mode == "network":
        print(f"🚀 Starte Netz-Self-Play (Rust): {num_games} Spiele | Modell {model} | "
              f"base_sims {simulations} | c_puct {c_puct} | "
              f"Root-Noise {'an' if add_root_noise else 'AUS'} | "
              f"Zugwahl {'ARGMAX (deterministisch)' if deterministic else 'Sampling (Standard)'} | "
              f"Threads {threads or 'alle Kerne'} | Chunk {chunk} | {per_file} Spiele/Datei | "
              f"Chunk-Hänger-Timeout {timeout_secs}s")
    elif mode == "mcts" and model:
        # Heuristik entscheidet WEITERHIN ausschließlich über Züge -- zusätzlich
        # werden die vier Rundenübergänge per Netz-Chance-Node-Sampling
        # gelabelt (round_transition_value, siehe round_transition_deep.rs).
        # Kein Vertrauen in die Netz-Suchqualität nötig, nur in dessen
        # Blattbewertung an den Übergängen. ~20s/Partie zusätzlich (Stand
        # dieser Kalibrierung, siehe round_transition_deep.rs-Kommentar).
        print(f"🚀 Starte MCTS Self-Play (Rust) MIT Netz-Rundenübergangs-Labels: {num_games} Spiele | "
              f"Modell {model} | Sims {simulations} | Threads {threads or 'alle Kerne'} | "
              f"Chunk {chunk} | {per_file} Spiele/Datei | ~20s/Partie zusätzlich fürs Sampling | "
              f"Chunk-Hänger-Timeout {timeout_secs}s")
    else:
        print(f"🚀 Starte MCTS Self-Play (Rust): {num_games} Spiele "
              f"(Sims: {simulations} | Threads: {threads or 'alle Kerne'} | "
              f"Chunk: {chunk} | {per_file} Spiele/Datei | Chunk-Hänger-Timeout {timeout_secs}s)")

    def make_chunk(n, chunk_idx):
        # Task #71: je Chunk-VERSUCH eigene Zwischendateien (chunk_idx macht
        # den Pfad pro Versuch eindeutig) -- Rust schreibt hier den
        # Einzelspiel-Flush (JSONL) + Herzschlag hinein, der Supervisor kann
        # sie bei einem Kill zur Wiederherstellung lesen (siehe unten).
        progress_path = DATA_DIR / f".progress_{prefix}_c{chunk_idx}.jsonl"
        heartbeat_path = DATA_DIR / f".heartbeat_{prefix}_c{chunk_idx}.json"
        raw = _run_chunk_supervised(
            mode, model, n, simulations, c_puct, base_seed + chunk_idx, threads,
            f"{prefix}_c{chunk_idx}", add_root_noise, deterministic, timeout_secs,
            progress_path, heartbeat_path,
        )
        return raw, progress_path, heartbeat_path

    # WICHTIG: In Chunks generieren statt in EINEM riesigen Rust-Aufruf. Das gibt
    # laufenden Fortschritt + ETA und hält den Speicher klein (sonst lägen bei
    # z.B. 3000 Spielen mehrere GB JSON im RAM). Die .pkl-Granularität (per_file,
    # Standard 10 Spiele/Datei) ist davon ENTKOPPELT.
    #
    # Keep-Awake (siehe Modul-Kommentar oben) umspannt GENAU den lang laufenden
    # Teil -- ab hier bis zum Lauf-Ende, auch bei Fehlern/Abbruch (`finally`),
    # damit Windows-Standby diesen mehrstündigen Batch nicht mehr killt.
    _keep_system_awake()
    try:
        t_start = time.time()
        done = 0
        total_steps = 0
        chunk_idx = 0
        consecutive_failures = 0
        buffer: list[dict] = []      # akkumulierte Steps für die nächste .pkl
        buffer_games = 0             # Anzahl Spiele im Buffer

        def _absorb_games(games: list[list[dict]]) -> None:
            """Übernimmt bereits gruppierte Spiele (aus `raw` ODER aus einer
            geretteten JSONL) ins gemeinsame `buffer`/`done`/`total_steps`-
            Tracking und flusht bei Bedarf -- EIN Pfad für beide Quellen
            (Task #71), damit sich Erfolgs- und Recovery-Fall nicht
            auseinanderentwickeln."""
            nonlocal done, total_steps, buffer, buffer_games
            for game_steps in games:
                buffer.extend(game_steps)
                buffer_games += 1
                done += 1
                total_steps += len(game_steps)
                if buffer_games >= per_file:
                    _flush(buffer, version_name, tag, done)
                    buffer, buffer_games = [], 0

        while done < num_games:
            n = min(chunk, num_games - done)
            raw, progress_path, heartbeat_path = make_chunk(n, chunk_idx)
            chunk_idx += 1  # Seed für den nächsten Versuch (auch bei Retry) ändert sich immer.
            if raw is None:
                # Chunk gehängt/getötet -- Task #71: statt den GESAMTEN Chunk zu
                # verwerfen, die bereits per Einzelspiel-Flush geschriebenen
                # Partien aus der JSONL retten und nur noch den fehlenden Rest
                # neu anfordern (nächste Schleifen-Iteration verkleinert `n`
                # automatisch über `num_games - done`).
                recovered = _recover_partial_progress(progress_path)
                _cleanup_progress_files(progress_path, heartbeat_path)
                if recovered:
                    print(f"  ♻️  {len(recovered)}/{n} Spiele aus dem unterbrochenen Chunk "
                          f"gerettet -- fordere nur den Rest neu an.")
                    _absorb_games(recovered)
                    consecutive_failures = 0  # echter Fortschritt zählt nicht als Fehlschlag
                    continue
                consecutive_failures += 1
                if consecutive_failures > MAX_CONSECUTIVE_CHUNK_FAILURES:
                    raise SystemExit(
                        f"❌ {MAX_CONSECUTIVE_CHUNK_FAILURES} Chunks in Folge gehängt/abgebrochen -- "
                        "wahrscheinlich ein systematisches Problem (Modell, Threads), kein Einzelfall-Hänger. Abbruch."
                    )
                continue  # gleiche Ziel-Spielezahl `n`, aber neuer Seed durch bumped chunk_idx
            consecutive_failures = 0
            # Erfolgreicher Chunk: `raw` enthält bereits ALLES -- die parallel
            # geschriebene JSONL wird nicht mehr gebraucht.
            _cleanup_progress_files(progress_path, heartbeat_path)
            steps = json.loads(raw)
            # run_net_self_play hängt ans JSON einen reinen Diagnose-Record an
            # (perspective_divergence_diagnostics, gleiches Muster wie
            # stage3_diagnostics in arena.py) -- der ist KEIN Spielschritt: er hat
            # kein "state"-Feld (MosaicDataset würde beim Training mit KeyError
            # crashen) und würde von _group_by_game als eigenes Pseudo-Spiel
            # gezählt (verfälscht `done` und das per_file-Chunking). Hier
            # rausfiltern, bevor gruppiert/gepickelt wird.
            steps = [s for s in steps if "perspective_divergence_diagnostics" not in s]

            # Chunk in Spiele aufteilen und je `per_file` Spiele eine .pkl schreiben.
            _absorb_games(_group_by_game(steps))

            elapsed = time.time() - t_start
            rate = done / elapsed if elapsed > 0 else 0.0
            eta_min = (num_games - done) / rate / 60 if rate > 0 else 0.0
            print(f"  ⏳ {done}/{num_games} Spiele | {rate:.2f} Spiele/s | "
                  f"{total_steps} Züge | ETA {eta_min:.1f} min")

        if buffer:   # Rest (< per_file Spiele) sichern
            _flush(buffer, version_name, tag, done)

        print(f"\n✅ Fertig: {num_games} Spiele, {total_steps} Züge nach {time.time() - t_start:.1f}s")
    finally:
        _allow_system_sleep()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mosaic-AI Self-Play (Rust-Hybrid)")
    parser.add_argument("--mode", type=str, required=True, choices=["mcts", "network"],
                        help="'mcts' für Heuristik-MCTS, 'network' für AlphaZero-Netz-PUCT")
    parser.add_argument("--model", type=str, default=None,
                        help="ONNX-Modell (Pflicht bei --mode network; bei --mode mcts optional -- "
                             "aktiviert dann Netz-Rundenübergangs-Labels, Zugentscheidungen bleiben "
                             "heuristisch). Dateiname genügt — wird im models/-Ordner gesucht, "
                             "z.B. alphazero_s100.onnx (oder ein voller Pfad)")
    parser.add_argument("--c-puct", dest="c_puct", type=float, default=1.5,
                        help="PUCT-Explorationskonstante (nur --mode network)")
    parser.add_argument("--games", type=int, default=100, help="Anzahl Spiele")
    parser.add_argument("--sims", type=int, default=100,
                        help="Basis-Simulationen pro Zug. Bei --mode mcts weiterhin dynamisch "
                             "skaliert (mehr Optionen -> mehr Sims). Bei --mode network seit "
                             "DECOUPLE_NET_SIMS_FROM_ACTIONS=true (2026-07-21) die TATSAECHLICHE, "
                             "unskalierte Sims-Zahl -- dort explizit --sims 400 verwenden (Nutzer-"
                             "Budget-Vorgabe, ersetzt das alte dynamic_sims-Hochskalieren eines "
                             "kleineren Basiswerts).")
    parser.add_argument("--version", type=str, required=True, help="Versionsname, z.B. v0")
    parser.add_argument("--tag", type=str, default=None,
                        help="Optionaler Tag für parallele Läufe (z.B. 'a', 'b')")
    parser.add_argument("--threads", type=int, default=8,
                        help="Rust-Worker-Threads (0 = alle Kerne, Standard jetzt 8 statt alle Kerne -- "
                             "reduziert die Wahrscheinlichkeit lastabhängiger Gamma-Pruning-Hänger, "
                             "siehe round_transition_deep.rs-Fund). Ersetzt das alte --terminals.")
    parser.add_argument("--chunk", type=int, default=10,
                        help="Spiele pro Rust-Aufruf (Fortschritts-Granularität + Speicherlimit). "
                             "Bewusst klein (Standard 10, vorher 50) seit round_transition_deep.rs: "
                             "Gamma-Pruning macht einzelne Partien teuer/variabel (~100s+ im Schnitt, "
                             "live beobachtete Nachzügler deutlich länger) -- ein 50er-Chunk lieferte "
                             "keinerlei Fortschrittsanzeige, bis ALLE 50 Partien durch waren.")
    parser.add_argument("--per-file", dest="per_file", type=int, default=10,
                        help="Spiele pro .pkl-Datei (Standard 10, entkoppelt von --chunk)")
    parser.add_argument("--seed", type=int, default=None,
                        help="Basis-Seed (für reproduzierbare Läufe). Standard: zufällig.")
    parser.add_argument("--depth", type=int, default=0,
                        help="(Kompatibilität; ignoriert — Rust bewertet Blätter exakt per Tiling-Solver)")
    parser.add_argument("--no-root-noise", action="store_true",
                        help="Dirichlet-Wurzel-Rauschen abschalten (nur --mode network; Standard: an). "
                             "Diagnose-Flag fuer den Stufe-2-0:0-Test, siehe evaluations/stage2_investigation.md")
    parser.add_argument("--deterministic", action="store_true",
                        help="Immer den meistbesuchten Zug spielen statt visit-proportional zu sampeln "
                             "(nur --mode network; Standard: aus, also normales Sampling). Diagnose-Flag, "
                             "um rauschfreie Trajektorien wie in der Arena aufzuzeichnen -- siehe "
                             "evaluations/stage2_investigation.md. NICHT fuer reguläre Trainingsdaten-"
                             "Generierung gedacht (weniger Zustandsvielfalt).")
    args = parser.parse_args()

    generate_data(
        mode=args.mode,
        num_games=args.games,
        simulations=args.sims,
        version_name=args.version,
        tag=args.tag,
        threads=args.threads,
        chunk=args.chunk,
        seed=args.seed,
        per_file=args.per_file,
        model=args.model,
        c_puct=args.c_puct,
        add_root_noise=not args.no_root_noise,
        deterministic=args.deterministic,
    )
