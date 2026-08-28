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
from selfplay_manifest import _write_run_manifest, _append_laufzeit
from corpus_io import dump_records, load_records

# GPU-Inferenzpfad (PREREG_gpu_inference_path.md §19, Nutzer-Auftrag 2026-08-13):
# das mit `--features ort_cuda_probe` gebaute Wheel bringt den ORT-CUDA-
# Kanal mit, der zur Laufzeit CUDA-12-DLLs braucht (cudart64_12, cublas64_12,
# cudnn64_9 u.a. -- siehe net_ort.rs-Modulkommentar). `torch` bringt genau
# diese DLLs in `torch/lib` schon mit (PREREG §11, dieselbe Datei-Liste),
# darum hier best-effort VOR dem `mosaic_rust`-Import bekanntmachen. Wirkt
# nur unter Windows (`add_dll_directory` existiert dort); No-Op, wenn `torch`
# fehlt oder die API nicht existiert (z.B. Linux) -- ein fehlender Zusatzpfad
# darf den Import nicht verhindern, `mosaic_rust` faellt in diesem Fall auf
# tract (CPU) zurueck, wie ohne diesen Knopf auch.
try:
    import torch as _torch_for_dll_path
    os.add_dll_directory(os.path.join(os.path.dirname(_torch_for_dll_path.__file__), "lib"))
except Exception:
    pass

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
                      add_root_noise, deterministic, record_rtv, pcr_full_prob,
                      pcr_cheap_sims, tau_argmax_from_move, queue, progress_path,
                      heartbeat_path, seed_positions=None, seed_positions_offset=0,
                      heuristik_variante="hv1"):  # konvention-ok: Feldname der pyo3-Signatur des eingefrorenen Wheels
    """Läuft im Subprozess (siehe Modul-Kommentar oben) -- reine Rust-Aufruf-
    Weiterleitung, damit sie per multiprocessing.Process spawnbar ist.
    `progress_path`/`heartbeat_path` (Task #71): an die Rust-Seite
    durchgereicht -- Einzelspiel-Flush (JSONL) + periodischer Herzschlag,
    siehe self_play.rs::run_net_self_play & Geschwister. `record_rtv`
    (Task #85): steuert das teure round_transition_value-Sampling, siehe
    --rtv-Flag-Hilfetext. Bei mode == "mcts" ohne Modell irrelevant (rtv
    wurde dort noch nie berechnet).
    `tau_argmax_from_move` (PREREG_search_path_remeasurements.md, Messung 3):
    KEIN pyo3-Parameter -- Rust liest `MOSAIC_TAU_ARGMAX_FROM_MOVE` selbst
    per OnceLock-Env-Var (net_mcts::tau_argmax_from_move), gleiches Muster
    wie MOSAIC_GUMBEL_TOP_M/MOSAIC_FLOOR_SHAPING_W. Deshalb hier VOR dem
    `import mosaic_rust`, in DIESEM Subprozess gesetzt (jeder Chunk läuft in
    einem frischen `mp.Process`, der Prozess-weite OnceLock-Cache der
    Rust-Seite wird also pro Chunk neu initialisiert -- kein Stale-Value-
    Risiko über Chunks hinweg). `0` (Default) setzt den Wert explizit auf
    "0" -- Rust behandelt das identisch zu "ungesetzt" (AUS), siehe
    `tau_argmax_from_move`s `n>=1.0`-Prüfung."""
    os.environ["MOSAIC_TAU_ARGMAX_FROM_MOVE"] = str(tau_argmax_from_move)
    try:
        import mosaic_rust as mr
        if mode == "network":
            raw = mr.net_self_play_games(
                model_path=model, n_games=n, base_sims=simulations, c_puct=c_puct,
                seed=seed, num_threads=threads, prefix=prefix,
                add_root_noise=add_root_noise, deterministic=deterministic,
                record_rtv=record_rtv,
                pcr_full_prob=pcr_full_prob, pcr_cheap_sims=pcr_cheap_sims,
                progress_path=progress_path, heartbeat_path=heartbeat_path,
                seed_positions_path=seed_positions, seed_positions_offset=seed_positions_offset,
            )
        elif mode == "mcts" and model:
            raw = mr.self_play_games_with_net_labels(
                model_path=model, n_games=n, base_sims=simulations,
                seed=seed, num_threads=threads, prefix=prefix,
                record_rtv=record_rtv,
                progress_path=progress_path, heartbeat_path=heartbeat_path,
                heuristik_variante=heuristik_variante,
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
                          add_root_noise, deterministic, record_rtv, timeout_secs,
                          progress_path, heartbeat_path, heuristik_variante="hv1",  # konvention-ok: Feldname der pyo3-Signatur des eingefrorenen Wheels
                          pcr_full_prob=None, pcr_cheap_sims=150,
                          tau_argmax_from_move=0, seed_positions=None,
                          seed_positions_offset=0) -> str | None:
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
              add_root_noise, deterministic, record_rtv, pcr_full_prob,
              pcr_cheap_sims, tau_argmax_from_move, queue,
              str(progress_path), str(heartbeat_path),
              seed_positions, seed_positions_offset, heuristik_variante),
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
    # Komprimiert geschrieben, Endung bleibt .pkl (corpus_io-Doku: der Name
    # haengt an Cache-Schluessel, MOSAIC_DATA_EXCLUDE und allen Globs).
    # Gemessen 2026-08-26: Faktor 35,4 ueber 12 Dateien, 0,06 s Packen.
    dump_records(filename, steps)
    _check_completion(steps, filename)
    print(f"💾 {len(steps)} Züge gespeichert in '{filename}'")



def generate_data(mode: str, num_games: int, simulations: int, version_name: str,
                  tag: str = None, threads: int = 0, chunk: int = 10, seed: int = None,
                  per_file: int = 10, model: str = None, c_puct: float = 1.5,
                  add_root_noise: bool = True, deterministic: bool = False,
                  record_rtv: bool = False,
                  pcr_full_prob: float | None = None, pcr_cheap_sims: int = 150,
                  tau_argmax_from_move: int = 0, seed_positions: str = None,
                  heuristik_variante: str = "hv1"):  # konvention-ok: Feldname der pyo3-Signatur des eingefrorenen Wheels
    # PCR (Task #14): pcr_full_prob=None -> AUS (Bestandsverhalten). Aktiv nur
    # im network-Modus; Details siehe self_play.rs::play_net_self_play_game.
    # pcr_full_prob=0.0 ist der VALUE-ONLY-Modus (v20-Zwei-Klassen-Schwarm,
    # via --value-only gesetzt): JEDER Mehrfach-Aktions-Zug laeuft mit
    # pcr_cheap_sims und traegt `policy_target_valid=false` -- die Partie
    # liefert nur Value-Material (Ausgang + Bootstrap), keine Policy-Ziele.
    # Rust-seitig sauber definiert: `rng.random::<f64>() < 0.0` ist nie wahr
    # (self_play.rs::pcr_decide_full), kein Epsilon-Hack noetig.
    if pcr_full_prob is not None and not (0.0 <= pcr_full_prob <= 1.0):
        raise SystemExit(f"❌ --pcr-full-prob muss in [0,1] liegen (0 = value-only), ist {pcr_full_prob}.")
    # τ-Annealing (PREREG_search_path_remeasurements.md, Messung 3): wirkt nur im
    # netzgeführten Self-Play-Pfad (net_drafting_policy, siehe self_play.rs).
    # --mode mcts liest MOSAIC_TAU_ARGMAX_FROM_MOVE gar nicht -- kein Fehler,
    # nur ein wirkungsloses Flag, deshalb Warnung statt SystemExit.
    if tau_argmax_from_move < 0:
        raise SystemExit(f"❌ --tau-argmax-from-move darf nicht negativ sein, ist {tau_argmax_from_move}.")
    if tau_argmax_from_move and mode != "network":
        print(f"  ⚠️  --tau-argmax-from-move={tau_argmax_from_move} wirkt nur bei --mode network "
              f"(net_drafting_policy) -- bei --mode {mode!r} ist es ein No-Op.")
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
        # Auflösungsreihenfolge (Kurzname genügt, wie bei train.py --load):
        # 1. wörtlicher Pfad, 2. models/<name>, 3. models/<name>.onnx,
        # 4. models/alphazero_<name>.onnx (z.B. --model v14b_best)
        candidates = [Path(model), MODELS_DIR / model,
                      MODELS_DIR / f"{model}.onnx",
                      MODELS_DIR / f"alphazero_{model}.onnx"]
        model_path = next((p for p in candidates if p.exists()), None)
        if model_path is None:
            raise SystemExit(
                f"❌ Modell nicht gefunden: '{model}' — geprüft wurden: "
                + ", ".join(str(p) for p in candidates))
        if str(model_path) != model:
            print(f"🔎 Modell aufgelöst: {model} -> {model_path}")
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
        "record_rtv": record_rtv, "tau_argmax_from_move": tau_argmax_from_move,
        "heuristik_variante": heuristik_variante,
    })

    # Nur der Rust-Aufruf unterscheidet sich je Modus; Fortschritt/Gruppierung/
    # Pickle teilen sich beide Pfade. MCTS = Heuristik-Suche; network = Netz-PUCT
    # (Priors vom Netz, Blatt immer per exaktem DFS-Solver), Policy-Target =
    # rohe Visit-Verteilung N/ΣN.
    has_model = bool(model)
    timeout_secs = _chunk_timeout_secs(chunk, threads, simulations, has_model and mode == "mcts")
    # Task #85 (rtv-Ablation Phase 2): rtv wirkt nur, wenn ueberhaupt ein
    # Netz beteiligt ist (--mode network oder --mode mcts --model) -- ohne
    # Modell wurde rtv nie berechnet, das Flag ist dort ein No-Op.
    rtv_status = "an (--rtv)" if record_rtv else "AUS (Standard, Task #85)"
    # τ-Annealing (PREREG Messung 3): nur informativ, solange --deterministic
    # nicht gesetzt ist -- dieses Flag argmaxt ohnehin die GANZE Partie, der
    # Zug-Schwellenwert waere dann wirkungslos (net_drafting_policy prüft
    # `deterministic` zuerst).
    if deterministic:
        tau_status = "irrelevant (--deterministic argmaxt bereits die ganze Partie)"
    elif tau_argmax_from_move:
        tau_status = f"ab Zug {tau_argmax_from_move} ARGMAX (Messung 3)"
    else:
        tau_status = "AUS (Standard, τ=1/Sampling durchgehend)"
    if mode == "network":
        print(f"🚀 Starte Netz-Self-Play (Rust): {num_games} Spiele | Modell {model} | "
              f"base_sims {simulations} | c_puct {c_puct} | "
              f"Root-Noise {'an' if add_root_noise else 'AUS'} | "
              f"Zugwahl {'ARGMAX (deterministisch)' if deterministic else 'Sampling (Standard)'} | "
              f"τ-Annealing {tau_status} | "
              f"rtv-Labels {rtv_status} | "
              f"Threads {threads or 'alle Kerne'} | Chunk {chunk} | {per_file} Spiele/Datei | "
              f"Chunk-Hänger-Timeout {timeout_secs}s")
    elif mode == "mcts" and model:
        # Heuristik entscheidet WEITERHIN ausschließlich über Züge -- optional
        # (Standard AUS, siehe --rtv) werden die vier Rundenübergänge
        # zusätzlich per Netz-Chance-Node-Sampling gelabelt
        # (round_transition_value, siehe round_transition_deep.rs). Kein
        # Vertrauen in die Netz-Suchqualität nötig, nur in dessen
        # Blattbewertung an den Übergängen. ~20s/Partie zusätzlich, wenn an
        # (Stand dieser Kalibrierung, siehe round_transition_deep.rs-Kommentar).
        print(f"🚀 Starte MCTS Self-Play (Rust) mit Netz-Rundenübergangs-Labels {rtv_status}: "
              f"{num_games} Spiele | "
              f"Modell {model} | Sims {simulations} | Threads {threads or 'alle Kerne'} | "
              f"Chunk {chunk} | {per_file} Spiele/Datei | "
              f"Chunk-Hänger-Timeout {timeout_secs}s")
    else:
        print(f"🚀 Starte MCTS Self-Play (Rust): {num_games} Spiele "
              f"(Sims: {simulations} | Threads: {threads or 'alle Kerne'} | "
              f"Chunk: {chunk} | {per_file} Spiele/Datei | Chunk-Hänger-Timeout {timeout_secs}s)")

    def make_chunk(n, chunk_idx, pos_offset=0):
        # Task #71: je Chunk-VERSUCH eigene Zwischendateien (chunk_idx macht
        # den Pfad pro Versuch eindeutig) -- Rust schreibt hier den
        # Einzelspiel-Flush (JSONL) + Herzschlag hinein, der Supervisor kann
        # sie bei einem Kill zur Wiederherstellung lesen (siehe unten).
        progress_path = DATA_DIR / f".progress_{prefix}_c{chunk_idx}.jsonl"
        heartbeat_path = DATA_DIR / f".heartbeat_{prefix}_c{chunk_idx}.json"
        raw = _run_chunk_supervised(
            mode, model, n, simulations, c_puct, base_seed + chunk_idx, threads,
            f"{prefix}_c{chunk_idx}", add_root_noise, deterministic, record_rtv, timeout_secs,
            progress_path, heartbeat_path, heuristik_variante,
            pcr_full_prob=pcr_full_prob, pcr_cheap_sims=pcr_cheap_sims,
            tau_argmax_from_move=tau_argmax_from_move,
            seed_positions=seed_positions, seed_positions_offset=pos_offset,
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
            # Seeding: pos_offset=done haelt die Stellungs-Zuordnung global.
            raw, progress_path, heartbeat_path = make_chunk(n, chunk_idx, pos_offset=done)
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
            # GPU-Inferenzpfad-Messung (PREREG §19): gleiches additives Muster --
            # `batcher_diagnostics` ist nur angehängt, wenn `MOSAIC_INTERLEAVE_
            # ENABLED=1` einen Sammel-Faden fuer dieses Netz registriert hat
            # (siehe self_play.rs::run_net_self_play), sonst fehlt der Record
            # komplett und diese Zeile ist ein No-Op. Ausgabe hier statt stillem
            # Verwerfen, weil die Abnahme-Messung genau diese Zahl braucht
            # ("berichte den TATSAECHLICH erreichten mittleren Batch").
            for s in steps:
                if s.get("batcher_diagnostics"):
                    print(f"  📊 [Batcher] batches={s.get('batches')} rows={s.get('rows')} "
                          f"mean_batch={s.get('mean_batch'):.2f} max_batch_seen={s.get('max_batch_seen')}")
            steps = [s for s in steps if "batcher_diagnostics" not in s]

            # Chunk in Spiele aufteilen und je `per_file` Spiele eine .pkl schreiben.
            _absorb_games(_group_by_game(steps))

            elapsed = time.time() - t_start
            rate = done / elapsed if elapsed > 0 else 0.0
            eta_min = (num_games - done) / rate / 60 if rate > 0 else 0.0
            print(f"  ⏳ {done}/{num_games} Spiele | {rate:.2f} Spiele/s | "
                  f"{total_steps} Züge | ETA {eta_min:.1f} min")

        if buffer:   # Rest (< per_file Spiele) sichern
            _flush(buffer, version_name, tag, done)

        _wanduhr = time.time() - t_start
        print(f"\n✅ Fertig: {num_games} Spiele, {total_steps} Züge nach {_wanduhr:.1f}s")
        # cpu_s: die Partien laufen in `mp.Process`-KINDERN, `time.process_time()`
        # misst aber nur diesen Prozess -- eine Zahl daraus waere um eine
        # Groessenordnung zu klein. `os.times()` fuehrt Kinderzeiten, auf Windows
        # aber als 0. Also nur eintragen, wo sie wirklich gemessen ist, sonst
        # None. Eine plausible falsche Zahl ist schlechter als eine fehlende.
        _t = os.times()
        _kinder = _t.children_user + _t.children_system
        _append_laufzeit(version_name, run_timestamp, {
            "wanduhr_s": round(_wanduhr, 1),
            "cpu_s": round(_kinder + _t.user + _t.system, 1) if _kinder > 0 else None,
            "cpu_s_hinweis": None if _kinder > 0 else
                "nicht gemessen: os.times() fuehrt auf dieser Plattform keine Kinderzeiten",
            "threads": threads,
            "s_je_partie": round(_wanduhr / max(1, done), 3),
            "partien": done,
            "zuege": total_steps,
        })
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
    parser.add_argument("--heuristik-variante", dest="heuristik_variante", type=str,
                        default="hv1",
                        # KEIN `choices=`. Die Verengung gehoert in die ENGINE, nicht in
                        # argparse: dieses Skript ist auch der Treiber, mit dem ein
                        # EINGEFRORENES Artefakt seine Golden Probe reproduziert
                        # (tools/verify_frozen_heuristic.py --venv ruft genau diese Datei
                        # mit dem Python UND dem Wheel des Artefakts). Ein hv2-Artefakt
                        # bringt ein Wheel mit, das seine Variante kann -- eine
                        # argparse-Schranke im Repo haette es trotzdem abgewiesen und dem
                        # Artefakt seinen staerksten Beleg genommen. Genau das ist am
                        # 2026-08-27 passiert. Wer entscheidet: das GELADENE Wheel.
                        #
                        # Deshalb steht hier auch die NAMENS-UEBERSETZUNG nicht (Umbenennung
                        # 2026-08-28, tools/frozen_name_dialect.py): welchen Dialekt ein
                        # Artefakt-Wheel spricht, weiss nur der Treiber, der es startet.
                        # Er uebersetzt und uebergibt hier den fertigen Namen.
                        help="Heuristik-Variante fuer den mcts-Modus. Seit dem 2026-08-26 "
                             "gibt es nur noch eine spielbare: hv1 (bis zur Umbenennung am "
                             "2026-08-28 hiess sie 'v1'). Der zweite Zweig ist aus dem "
                             "Quellstand entfernt (PREREG_heuristic_v2_long_rows.md par.19). "
                             "Die mit hv2 (frueher 'v2huelle') erzeugten Korpora liegen "
                             "unveraendert in data/, und das Erzeuger-Artefakt laeuft auf "
                             "seinem mitgelieferten Wheel weiter "
                             "(models/frozen_heuristics/hv2_generator/). "
                             "Das Flag BLEIBT, damit ein alter Kampagnen-Aufruf laut "
                             "scheitert statt still etwas anderes zu erzeugen.")
    parser.add_argument("--rtv", action="store_true",
                        help="Task #85 (rtv-Ablation Phase 2): das teure "
                             "round_transition_value-Sampling an den vier Rundenübergängen "
                             "(Netz-Chance-Node-Sampling, ~81%% der Self-Play-Kosten laut "
                             "Task #80/#81) REAKTIVIEREN. Standard: AUS -- die #84/#85-Gating-"
                             "Evidenz zeigt, dass rtv im aktuellen Setup keine messbare "
                             "Spielstärke beiträgt (v13_nortv_best schlägt Champion "
                             "v12b_lr_best 171:129), aber ~3x Durchsatz kostet. Nur bei "
                             "--mode network oder --mode mcts --model wirksam (ohne Modell "
                             "wurde rtv nie berechnet). bootstrap_value bleibt in jedem Fall "
                             "erhalten.")
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
    parser.add_argument("--seed-positions", dest="seed_positions", default=None,
                        help="JSONL kuratierter Startstellungen (PREREG_start_position_seeding.md); "
                             "nur --mode network.")
    parser.add_argument("--depth", type=int, default=0,
                        help="(Kompatibilität; ignoriert — Rust bewertet Blätter exakt per Tiling-Solver)")
    parser.add_argument("--pcr-full-prob", dest="pcr_full_prob", type=float, default=None,
                        help="Task #14 PCR: Anteil Voll-Suche pro Zug (z.B. 0.25); "
                             "None/weggelassen = AUS (Bestandsverhalten). Nur --mode network.")
    parser.add_argument("--value-only", dest="value_only", action="store_true",
                        help="v20-Zwei-Klassen-Schwarm: Partie liefert NUR Value-Material -- "
                             "jeder Zug laeuft mit dem --sims-Budget, alle Policy-Ziele werden "
                             "als ungueltig markiert (policy_target_valid=false). Aequivalent zu "
                             "--pcr-full-prob 0 --pcr-cheap-sims <--sims>; nicht mit "
                             "--pcr-full-prob kombinierbar. Nur --mode network.")
    parser.add_argument("--pcr-cheap-sims", dest="pcr_cheap_sims", type=int, default=150,
                        help="Task #14 PCR: Sim-Budget der Sparsuche (Default 150; "
                             "GUMBEL_TOP_M skaliert automatisch mit).")
    parser.add_argument("--no-root-noise", action="store_true",
                        help="Dirichlet-Wurzel-Rauschen abschalten (nur --mode network; Standard: an). "
                             "Diagnose-Flag fuer den Stufe-2-0:0-Test, siehe evaluations/stage2_investigation.md")
    parser.add_argument("--deterministic", action="store_true",
                        help="Immer den meistbesuchten Zug spielen statt visit-proportional zu sampeln "
                             "(nur --mode network; Standard: aus, also normales Sampling). Diagnose-Flag, "
                             "um rauschfreie Trajektorien wie in der Arena aufzuzeichnen -- siehe "
                             "evaluations/stage2_investigation.md. NICHT fuer reguläre Trainingsdaten-"
                             "Generierung gedacht (weniger Zustandsvielfalt).")
    parser.add_argument("--tau-argmax-from-move", dest="tau_argmax_from_move", type=int, default=0,
                        help="PREREG_search_path_remeasurements.md, Messung 3 (τ-Annealing): ab dem N-ten "
                             "Halbzug EINER Partie (1-basiert, beide Spieler zusammen gezählt) wird "
                             "statt visit-proportional zu sampeln der argmax der Besuchsverteilung "
                             "gespielt -- frühe Züge bleiben τ=1 (Sampling, Bestandsverhalten). "
                             "Vorab-Festlegung im PREREG: 30 (grob Runde 1+). Default 0 = AUS "
                             "(Bestandsverhalten, durchgehend Sampling). Setzt NUR "
                             "MOSAIC_TAU_ARGMAX_FROM_MOVE für den Rust-Aufruf, siehe net_mcts.rs. "
                             "Nur bei --mode network wirksam; Runde 5 bleibt davon unberührt "
                             "(Alpha-Beta-exakt, round5.rs).")
    args = parser.parse_args()

    # --value-only (v20-Zwei-Klassen-Schwarm): expliziter Modus statt
    # Epsilon-Hack -- pcr_full_prob=0.0 heisst "kein Zug voll", das
    # --sims-Budget wird zum Cheap-Budget jedes Zugs.
    _resolved_pcr_full_prob = args.pcr_full_prob
    _resolved_pcr_cheap_sims = args.pcr_cheap_sims
    if args.value_only:
        if args.pcr_full_prob is not None:
            raise SystemExit("❌ --value-only und --pcr-full-prob schliessen sich aus.")
        if args.mode != "network":
            raise SystemExit("❌ --value-only ist nur mit --mode network sinnvoll.")
        _resolved_pcr_full_prob = 0.0
        _resolved_pcr_cheap_sims = args.sims

    if args.seed_positions and args.mode != "network":
        raise SystemExit("❌ --seed-positions: nur --mode network.")
    if args.seed_positions and not os.path.exists(args.seed_positions):
        raise SystemExit(f"❌ --seed-positions fehlt: {args.seed_positions}")

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
        record_rtv=args.rtv,
        pcr_full_prob=_resolved_pcr_full_prob,
        pcr_cheap_sims=_resolved_pcr_cheap_sims,
        tau_argmax_from_move=args.tau_argmax_from_move,
        seed_positions=args.seed_positions,
        heuristik_variante=args.heuristik_variante,
    )
