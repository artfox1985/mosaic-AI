# -*- coding: utf-8 -*-
"""Lauf-Manifest des Self-Play (#64 Teil 1, Phase 2a, 2026-07-22).

Herausgeloest aus `self_play.py` am 2026-08-25: die Datei lag bereits ueber
der 40-KB-Modularitaetsschwelle, und der Laufzeit-Nachtrag haette sie weiter
wachsen lassen. Symmetrisch zu `train_manifest.py`, das dieselbe Rolle fuer
das Training spielt.

Ein Self-Play-Lauf soll rueckwirkend rekonstruierbar sein: welche CLI-Args,
welcher Rust-Commit-Stand, welche aktiven Suchkonstanten haben DIESE Daten
erzeugt -- ohne den Rust-Quellcode zum jeweiligen Stand extra auschecken zu
muessen. Alles hier best-effort (git/engine_config_json koennen fehlen, z.B.
in einem isolierten Wheel-Export ohne .git oder mit altem Wheel ohne die neue
pyo3-Funktion) -- ein Manifest-Fehler darf den eigentlichen Self-Play-Lauf NIE
verhindern.
"""
import json

from config import BASE_DIR, DATA_DIR

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
        import mosaic_rust as _mr
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


def _append_laufzeit(version_name: str, run_timestamp: str, laufzeit: dict) -> None:
    """Traegt den `laufzeit`-Block NACHTRAEGLICH ins Lauf-Manifest ein.

    CLAUDE.md, Nutzer-Anweisung 2026-08-25: jeder Messlauf schreibt seine Dauer
    in SEIN EIGENES Artefakt -- nicht (nur) nach STATUS.md, das regelmaessig
    gekuerzt wird. Bis 2026-08-25 hielt das Manifest nur `run_timestamp`, also
    den START; die Dauer stand allein auf stdout und war nach dem Lauf
    verloren. `threads` gehoert laut Regel ausdruecklich dazu, weil dieselbe
    Zahl in verschiedenen Einstiegen Verschiedenes bedeutet (0 = alle Kerne,
    1 = sequenziell).

    Bewusst NACHTRAEGLICH und nicht als zweite Datei: das Manifest bleibt der
    eine Ort, an dem der Lauf beschrieben ist. Faellt der Lauf vorher um, fehlt
    der Block -- und genau das ist dann die richtige Aussage.
    """
    path = DATA_DIR / f"manifest_{version_name}_{run_timestamp}.json"
    try:
        with open(path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        manifest["laufzeit"] = laufzeit
        with open(path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        print(f"⏱️  Laufzeit ins Manifest nachgetragen: {laufzeit['wanduhr_s']:.1f}s "
              f"({laufzeit['s_je_partie']:.2f}s je Partie, threads={laufzeit['threads']})")
    except Exception as e:
        print(f"  ⚠️  Laufzeit konnte nicht nachgetragen werden ({e!r}).")
