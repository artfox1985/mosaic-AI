"""
Self-Play Datengenerierung für Mosaic-AI — Rust-Hybrid.

Die gesamte Spiel-/Suchschleife läuft jetzt in Rust (`mosaic_rust.self_play_games`,
rayon-parallel, GIL frei). Dieses Skript ist nur noch der schlanke Treiber: es
ruft Rust auf, gruppiert die zurückgelieferten Step-Records nach Spiel und
pickled sie im UNVERÄNDERTEN Format (das `train.py` / `MosaicDataset` liest).

Modi:
  --mode mcts      Heuristik-MCTS in Rust (kein Netz, erste Generation)
  --mode network   AlphaZero-Netz in Rust (Phase B: benötigt ONNX-Export)

Verwendung:
  python self_play.py --mode mcts --games 1500 --sims 50 --version v0 --threads 8
"""
import os
import sys
import json
import time
import pickle
import argparse
from datetime import datetime

# Windows-Konsolen (cp1252) können die Emoji-Ausgaben sonst nicht kodieren.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from config import DATA_DIR, MODELS_DIR

try:
    import mosaic_rust as _mr
except ImportError as e:  # pragma: no cover
    raise SystemExit(
        "❌ Rust-Modul 'mosaic_rust' nicht gefunden. Bitte zuerst bauen:\n"
        "   cd engine && maturin build --release  (dann das Wheel installieren)\n"
        f"(Import-Fehler: {e})"
    )


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
    STAGE2_TODO.md), deshalb hier ein Sanity-Check bei jeder generierten Datei."""
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


def generate_data(mode: str, num_games: int, simulations: int, version_name: str,
                  tag: str = None, threads: int = 0, chunk: int = 50, seed: int = None,
                  per_file: int = 10, model: str = None, c_puct: float = 1.5,
                  add_root_noise: bool = True, deterministic: bool = False):
    if mode not in ("mcts", "network"):
        raise SystemExit(f"❌ Unbekannter Modus: {mode}. Verwende 'mcts' oder 'network'.")
    if mode == "network" and not model:
        raise SystemExit(
            "❌ --mode network benötigt --model (z.B. alphazero_s100.onnx). "
            "Vorher 'export_onnx.py <version>' bzw. train.py ausführen."
        )
    if mode == "network":
        # --model gegen den models/-Ordner auflösen: der bloße Dateiname genügt
        # (z.B. "alphazero_s100.onnx"). Ein existierender expliziter Pfad bleibt.
        from pathlib import Path
        mp = Path(model)
        if not mp.exists():
            mp = MODELS_DIR / model
        if not mp.exists():
            raise SystemExit(f"❌ Modell nicht gefunden: '{model}' (auch nicht in {MODELS_DIR}/)")
        model = str(mp)

    import random as _random
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = f"{version_name}{('_' + tag) if tag else ''}_{run_timestamp}"
    base_seed = seed if seed is not None else _random.randint(0, 2**31 - 1)
    chunk = max(1, chunk)
    per_file = max(1, per_file)

    # Nur der Rust-Aufruf unterscheidet sich je Modus; Fortschritt/Gruppierung/
    # Pickle teilen sich beide Pfade. MCTS = Heuristik-Suche; network = Netz-PUCT
    # (Priors vom Netz, Blatt immer per exaktem DFS-Solver), Policy-Target =
    # rohe Visit-Verteilung N/ΣN.
    if mode == "network":
        def make_chunk(n, chunk_idx):
            return _mr.net_self_play_games(
                model_path=model, n_games=n, base_sims=simulations, c_puct=c_puct,
                seed=base_seed + chunk_idx, num_threads=threads,
                prefix=f"{prefix}_c{chunk_idx}", add_root_noise=add_root_noise,
                deterministic=deterministic,
            )
        print(f"🚀 Starte Netz-Self-Play (Rust): {num_games} Spiele | Modell {model} | "
              f"base_sims {simulations} | c_puct {c_puct} | "
              f"Root-Noise {'an' if add_root_noise else 'AUS'} | "
              f"Zugwahl {'ARGMAX (deterministisch)' if deterministic else 'Sampling (Standard)'} | "
              f"Threads {threads or 'alle Kerne'} | Chunk {chunk} | {per_file} Spiele/Datei")
    else:
        def make_chunk(n, chunk_idx):
            return _mr.self_play_games(
                n_games=n, base_sims=simulations, seed=base_seed + chunk_idx,
                num_threads=threads, prefix=f"{prefix}_c{chunk_idx}",
            )
        print(f"🚀 Starte MCTS Self-Play (Rust): {num_games} Spiele "
              f"(Sims: {simulations} | Threads: {threads or 'alle Kerne'} | "
              f"Chunk: {chunk} | {per_file} Spiele/Datei)")

    # WICHTIG: In Chunks generieren statt in EINEM riesigen Rust-Aufruf. Das gibt
    # laufenden Fortschritt + ETA und hält den Speicher klein (sonst lägen bei
    # z.B. 3000 Spielen mehrere GB JSON im RAM). Die .pkl-Granularität (per_file,
    # Standard 10 Spiele/Datei) ist davon ENTKOPPELT.
    t_start = time.time()
    done = 0
    total_steps = 0
    chunk_idx = 0
    buffer: list[dict] = []      # akkumulierte Steps für die nächste .pkl
    buffer_games = 0             # Anzahl Spiele im Buffer
    while done < num_games:
        n = min(chunk, num_games - done)
        raw = make_chunk(n, chunk_idx)
        steps = json.loads(raw)
        total_steps += len(steps)
        chunk_idx += 1

        # Chunk in Spiele aufteilen und je `per_file` Spiele eine .pkl schreiben.
        for game_steps in _group_by_game(steps):
            buffer.extend(game_steps)
            buffer_games += 1
            done += 1
            if buffer_games >= per_file:
                _flush(buffer, version_name, tag, done)
                buffer, buffer_games = [], 0

        elapsed = time.time() - t_start
        rate = done / elapsed if elapsed > 0 else 0.0
        eta_min = (num_games - done) / rate / 60 if rate > 0 else 0.0
        print(f"  ⏳ {done}/{num_games} Spiele | {rate:.2f} Spiele/s | "
              f"{total_steps} Züge | ETA {eta_min:.1f} min")

    if buffer:   # Rest (< per_file Spiele) sichern
        _flush(buffer, version_name, tag, done)

    print(f"\n✅ Fertig: {num_games} Spiele, {total_steps} Züge nach {time.time() - t_start:.1f}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mosaic-AI Self-Play (Rust-Hybrid)")
    parser.add_argument("--mode", type=str, required=True, choices=["mcts", "network"],
                        help="'mcts' für Heuristik-MCTS, 'network' für AlphaZero-Netz-PUCT")
    parser.add_argument("--model", type=str, default=None,
                        help="ONNX-Modell (Pflicht bei --mode network). Dateiname genügt — wird "
                             "im models/-Ordner gesucht, z.B. alphazero_s100.onnx (oder ein voller Pfad)")
    parser.add_argument("--c-puct", dest="c_puct", type=float, default=1.5,
                        help="PUCT-Explorationskonstante (nur --mode network)")
    parser.add_argument("--games", type=int, default=100, help="Anzahl Spiele")
    parser.add_argument("--sims", type=int, default=100,
                        help="Basis-Simulationen pro Zug (Rust skaliert im Frühspiel dynamisch)")
    parser.add_argument("--version", type=str, required=True, help="Versionsname, z.B. v0")
    parser.add_argument("--tag", type=str, default=None,
                        help="Optionaler Tag für parallele Läufe (z.B. 'a', 'b')")
    parser.add_argument("--threads", type=int, default=0,
                        help="Rust-Worker-Threads (0 = alle Kerne). Ersetzt das alte --terminals.")
    parser.add_argument("--chunk", type=int, default=50,
                        help="Spiele pro Rust-Aufruf (Fortschritts-Granularität + Speicherlimit)")
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
