"""Wave-3-Worker (PREREG_agent_encapsulation.md par.8): persistenter Prozess
fuer einen eingefrorenen Champion. JSON-Zeilen-Protokoll auf stdin/stdout --
"Stellung rein, Zug raus" (Schach-Engine-Muster).

Aufruf:
    <artefakt>/venv/Scripts/python.exe tools/frozen_champion_worker.py <artefakt_dir>

Laedt model.onnx + spec.json AUS dem Artefaktverzeichnis, dann je Zeile auf
stdin ein Request-JSON:
    {"state": <state_json-String>, "seed": <int>,
     "sims": <int optional>, "c_puct": <float optional>}

PER-ENTSCHEIDUNG-Protokoll (KERNBEWEIS-FIX par.8d, PREREG_agent_encapsulation.md,
loest die atomare Kuppel-Sonderbehandlung aus par.8a/8c ab): jede Anfrage
beantwortet GENAU EINE Drafting-Entscheidung -- auch jeder Peek-Schritt, die
Stapel-Slot-Wahl und die Kuppel-Rotationsstufe sind eigene Anfragen mit dem
regulaeren `pending_search_seed()` des jeweiligen Schritts. Der fruehere
zweite `rot_seed`-Parameter ist damit ersatzlos entfallen -- der Treiber
(`tools/frozen_referee_match.py`) fragt stattdessen einfach erneut an, solange
die gefrorene Seite noch am Zug ist.
und schreibt EINE Antwortzeile auf stdout:
    {"ok": true, "action": <dict>, "value": <float|null>}
oder bei Fehlern:
    {"ok": false, "error": "<text>"}

Encoding-Falle (Merkzettel): stdin/stdout IMMER als UTF-8 behandeln --
Windows' Konsolen-Default ist cp1252 und wuerde deutsche Kommentare in
Fehlermeldungen stillschweigend verstuemmeln oder crashen.

Der Worker fuehrt KEIN eigenes Spielregelwissen -- er waehlt nur Zuege. Ob
ein Zug legal ist, entscheidet weiterhin der Referee, und er weist eine
unzulaessige Antwort hart ab (Regel-Autoritaet, par.8).

SEIT 2026-08-26 beantwortet er DREI Arten von Anfragen, unterschieden ueber
das Feld `kind` (fehlt es, gilt "drafting" -- Bestandsaufrufer bleiben
unveraendert):

    {"kind": "drafting",        "state": ..., "seed": ..., "sims":?, "c_puct":?}
    {"kind": "tiling",          "state": ...}
    {"kind": "start_placement", "state": ..., "pi": ..., "game_seed": ...}

Der Grund ist die Heuristik-Kapselung (Nutzer-Richtung: gefrorene Agenten
sollen gegeneinander spielen). Vorher loeste der Referee Tiling und
Startsetzung selbst auf -- ueber einen auf V1 verdrahteten Pfad. Ein
gefrorenes `v2huelle`-Artefakt haette damit als `v1` gekachelt, also als ein
anderer Spieler, mit plausibel aussehendem Ergebnis.

NETZLOSE ARTEFAKTE: fehlt `model.onnx`, ist das Artefakt eine Heuristik --
ihr Verhalten steckt vollstaendig im Wheel. Die Drafting-Antwort kommt dann
aus `heuristic_arena_choice_state_json` statt aus der Netzsuche. Ein
`tiling_net.onnx` im Artefakt wird fuer den Tiling-Durchfall-Pfad benutzt.
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
    tiling_net_path = artifact / "tiling_net.onnx"
    spec_path = artifact / "spec.json"
    manifest_path = artifact / "manifest.json"
    # `model.onnx` ist NICHT mehr Pflicht: ein Heuristik-Artefakt hat keins.
    # Die Spec dagegen schon -- sie sagt, WAS der Agent ist, und ohne sie
    # waere die Variante wieder eine Sache des Aufrufers.
    ist_heuristik = not model_path.exists()
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
    # Nur fuer NETZ-Artefakte: haelt Modell+Spec ueber die Prozesslaufzeit.
    # Ein Heuristik-Artefakt braucht das nicht -- es gibt kein Modell zu
    # halten, und die Suche liest die Variante je Aufruf aus der Spec.
    # EINE Engine fuer alles, auch fuer Heuristiken: sie haelt das (optionale)
    # Tiling-Netz ueber die Prozesslaufzeit. Ohne das laedt jede
    # Tiling-Anfrage das ~9 MB ONNX neu -- gemessen 2.023 ms je Entscheidung
    # gegen 3 ms mit Cache.
    engine_modell = None if ist_heuristik else str(model_path)
    if engine_modell is None and tiling_net_path.exists():
        engine_modell = str(tiling_net_path)
    # `heuristik_drafting` EXPLIZIT, nicht aus dem Vorhandensein des Netzes
    # abgeleitet: ein v2huelle-Artefakt hat ein Netz, draftet aber
    # heuristisch. Das Netz ist dort NUR fuer den Tiling-Durchfall da.
    engine = mr.FrozenWorkerEngine(engine_modell, str(spec_path), ist_heuristik)
    tiling_net = str(tiling_net_path) if tiling_net_path.exists() else None
    print(f"[worker] typ={'heuristik' if ist_heuristik else 'netz'} "
          f"tiling_net={'ja' if tiling_net else 'nein'}", file=sys.stderr, flush=True)

    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            state_json = req["state"]
            # `kind` fehlt = "drafting": Bestandsaufrufer (Welle 3) senden es
            # nicht, und ihr Verhalten bleibt Zeichen fuer Zeichen dasselbe.
            kind = req.get("kind", "drafting")
            if kind == "drafting":
                seed = int(req["seed"])
                sims = int(req.get("sims", args.sims))
                c_puct = float(req.get("c_puct", args.c_puct))
                resp = json.loads(engine.choose(state_json, sims, c_puct, seed))
                out = {"ok": True, "action": resp["action"], "value": resp.get("value")}
            elif kind == "tiling":
                out = {"ok": True, "step": json.loads(engine.tiling(state_json))}
            elif kind == "start_placement":
                out = {"ok": True, "placement": json.loads(
                    engine.start_placement(state_json, int(req["pi"]), int(req["game_seed"])))}
            else:
                raise ValueError(
                    f"unbekannte Anfrageart '{kind}' (drafting/tiling/start_placement). "
                    "Kein Rueckfall auf drafting -- eine falsch verstandene Anfrage waere "
                    "ein stiller Zugwechsel.")
        except Exception as exc:  # noqa: BLE001 -- Protokollantwort statt Traceback
            out = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        stdout.write(json.dumps(out, ensure_ascii=False) + "\n")
        stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
