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

from config import DATA_DIR

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


def _flush(steps: list[dict], version_name: str, tag: str, game_count: int) -> None:
    """Schreibt die akkumulierten Steps in eine .pkl (Dateinamens-Schema wie bisher)."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    file_tag = f"_{tag}" if tag else ""
    filename = DATA_DIR / f"selfplay_{version_name}{file_tag}_{timestamp}_g{game_count}.pkl"
    with open(filename, "wb") as f:
        pickle.dump(steps, f)
    print(f"💾 {len(steps)} Züge gespeichert in '{filename}'")


def generate_data(mode: str, num_games: int, simulations: int, version_name: str,
                  tag: str = None, threads: int = 0):
    if mode == "network":
        raise SystemExit(
            "ℹ️  --mode network läuft über die ONNX-Inferenz in Rust (Phase B) und ist "
            "noch nicht aktiv. Zuerst 'export_onnx.py' ausführen und den Network-Pfad in "
            "mosaic_rust.self_play_games aktivieren."
        )
    if mode != "mcts":
        raise SystemExit(f"❌ Unbekannter Modus: {mode}. Verwende 'mcts' oder 'network'.")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_tag = f"_{tag}" if tag else ""
    prefix = f"{version_name}{file_tag}_{run_timestamp}"

    print(f"🚀 Starte MCTS Self-Play (Rust): {num_games} Spiele "
          f"(Sims: {simulations} | Threads: {threads or 'alle Kerne'})")

    t_start = time.time()
    raw = _mr.self_play_games(
        n_games=num_games,
        base_sims=simulations,
        num_threads=threads,
        prefix=prefix,
    )
    steps = json.loads(raw)
    gen_dur = time.time() - t_start
    print(f"✅ Rust fertig: {len(steps)} Züge in {gen_dur:.1f}s "
          f"({num_games / gen_dur:.1f} Spiele/s)")

    # Nach Spielen gruppieren und in 10er-Blöcken pickeln (wie bisher).
    games = _group_by_game(steps)
    buffer: list[dict] = []
    written_games = 0
    for gi, game_steps in enumerate(games, start=1):
        buffer.extend(game_steps)
        written_games = gi
        if gi % 10 == 0 or gi == len(games):
            _flush(buffer, version_name, tag, written_games)
            buffer = []

    print(f"\n✅ Fertig: {len(games)} Spiele, {len(steps)} Züge nach {time.time() - t_start:.1f}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mosaic-AI Self-Play (Rust-Hybrid)")
    parser.add_argument("--mode", type=str, required=True, choices=["mcts", "network"],
                        help="'mcts' für Heuristik-MCTS, 'network' für AlphaZero-Netz (Phase B)")
    parser.add_argument("--games", type=int, default=100, help="Anzahl Spiele")
    parser.add_argument("--sims", type=int, default=100,
                        help="MCTS-Basis-Simulationen pro Zug (Rust skaliert im Frühspiel dynamisch)")
    parser.add_argument("--version", type=str, required=True, help="Versionsname, z.B. v0")
    parser.add_argument("--tag", type=str, default=None,
                        help="Optionaler Tag für parallele Läufe (z.B. 'a', 'b')")
    parser.add_argument("--threads", type=int, default=0,
                        help="Rust-Worker-Threads (0 = alle Kerne). Ersetzt das alte --terminals.")
    parser.add_argument("--depth", type=int, default=0,
                        help="(Kompatibilität; ignoriert — Rust bewertet Blätter exakt per Tiling-Solver)")
    args = parser.parse_args()

    generate_data(
        mode=args.mode,
        num_games=args.games,
        simulations=args.sims,
        version_name=args.version,
        tag=args.tag,
        threads=args.threads,
    )
