"""Wave-3-Worker (PREREG_agent_encapsulation.md par.8): persistenter Prozess
fuer einen eingefrorenen Champion. JSON-Zeilen-Protokoll auf stdin/stdout --
"Stellung rein, Zug raus" (Schach-Engine-Muster).

Aufruf:
    <artefakt>/venv/Scripts/python.exe tools/frozen_champion_worker.py <artefakt_dir>

Laedt model.onnx + spec.json AUS dem Artefaktverzeichnis, dann je Zeile auf
stdin ein Request-JSON:
    {"state": <state_json-String>, "seed": <int>, "sims": <int optional>,
     "c_puct": <float optional>}
und schreibt EINE Antwortzeile auf stdout:
    {"ok": true, "action": <dict>, "value": <float|null>}
oder bei Fehlern:
    {"ok": false, "error": "<text>"}

Encoding-Falle (Merkzettel): stdin/stdout IMMER als UTF-8 behandeln --
Windows' Konsolen-Default ist cp1252 und wuerde deutsche Kommentare in
Fehlermeldungen stillschweigend verstuemmeln oder crashen.

Der Worker fuehrt KEIN eigenes Spielregelwissen -- er beantwortet nur
Drafting-Entscheidungen (net_arena_choice_state_json verweigert alles
andere hart). Start-Platzierung und Tiling loest der Referee-Prozess selbst
auf (Regel-Autoritaet bleibt bei der aktuellen Engine, siehe par.8).
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("artifact_dir", help="Pfad zum Artefaktverzeichnis (models/frozen_champions/<name>/)")
    ap.add_argument("--sims", type=int, default=400, help="Default-Simulationszahl je Zug (Request kann ueberschreiben)")
    ap.add_argument("--c-puct", type=float, default=1.5, help="Default c_puct (Request kann ueberschreiben)")
    args = ap.parse_args()

    artifact = Path(args.artifact_dir).resolve()
    model_path = artifact / "model.onnx"
    spec_path = artifact / "spec.json"
    manifest_path = artifact / "manifest.json"
    if not model_path.exists():
        print(json.dumps({"ok": False, "error": f"Modell fehlt: {model_path}"}), flush=True)
        return 2
    if not spec_path.exists():
        print(json.dumps({"ok": False, "error": f"Spec fehlt: {spec_path}"}), flush=True)
        return 2

    # UTF-8 hart erzwingen (Encoding-Falle, siehe Modul-Doku) -- unabhaengig
    # von der Windows-Konsolen-Codepage des Elternprozesses.
    stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", newline="\n")
    stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", newline="\n")

    try:
        import mosaic_rust as mr
    except ImportError as exc:
        print(json.dumps({"ok": False, "error": f"mosaic_rust nicht importierbar: {exc}"}), flush=True)
        return 2

    # Handshake-Info EINMALIG auf stderr (nicht Teil des stdout-Protokolls) --
    # hilft beim Debuggen, ohne die Zeilenprotokoll-Kontrakt zu stoeren.
    engine_config = json.loads(mr.engine_config_json())
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    print(
        f"[worker] artifact={artifact.name} contract_hash={engine_config.get('contract_hash')} "
        f"manifest_contract_hash={manifest.get('contract_hash')} mosaic_rust={mr.version()}",
        file=sys.stderr,
        flush=True,
    )

    # `FrozenWorkerEngine` laedt Modell+Spec EINMAL hier -- Performance-Fix
    # (gemessen 2026-08-23: `net_arena_choice_state_json` laedt das ~9 MB
    # ONNX-Modell bei JEDEM Zug neu, ein 3-Partien-Testlauf schaffte in 20
    # Minuten nicht mal die erste Partie). `engine.choose()` haelt Modell+Spec
    # ueber die gesamte Prozesslaufzeit.
    engine = mr.FrozenWorkerEngine(str(model_path), str(spec_path))

    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            state_json = req["state"]
            seed = int(req["seed"])
            sims = int(req.get("sims", args.sims))
            c_puct = float(req.get("c_puct", args.c_puct))
            resp = json.loads(engine.choose(state_json, sims, c_puct, seed))
            out = {"ok": True, "action": resp["action"], "value": resp.get("value")}
        except Exception as exc:  # noqa: BLE001 -- Protokollantwort statt Traceback
            out = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        stdout.write(json.dumps(out, ensure_ascii=False) + "\n")
        stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
