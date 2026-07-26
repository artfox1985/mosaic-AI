"""tools/set_champion.py -- setzt den amtierenden Champion fuer das Server-
Spiel (`models/champion.txt`, gelesen von `server.py::_load_champion_model`).

Nutzer-Anstoss (2026-07-27): "schreib noch v17_best als neuen KI-Agenten in
den Server-Default. Das kannst auch gleich automatisieren. Sobald neuer
Champ da ist, sofort in das Server-Game ruebernehmen." -- dieses Skript ist
der Standard-Schritt, den jede kuenftige Champion-Ablösung (gepaartes
Gating gewonnen, siehe evaluations/STATUS.md-Konvention "X_best loest
Y_best als Champion/Self-Play-Generator ab") nach `tools/elo_tracker.py add`
zusaetzlich ausfuehren sollte.

Verwendung:
    python tools/set_champion.py v17_best
    python tools/set_champion.py v17_best --dry-run   # nur pruefen, nicht schreiben

Validiert, dass das ONNX-Modell tatsaechlich existiert (verhindert einen
Server-Default, der ins Leere zeigt) -- sonst identisch zu einem einfachen
`echo v17_best > models/champion.txt`.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import MODELS_DIR


def set_champion(name: str, dry_run: bool = False) -> Path:
    onnx_path = MODELS_DIR / f"alphazero_{name}.onnx"
    if not onnx_path.exists():
        raise SystemExit(
            f"Abgebrochen: {onnx_path} existiert nicht -- Champion NICHT gesetzt. "
            f"(Modellname ohne 'alphazero_'-Praefix/'.onnx'-Suffix erwartet, z.B. 'v17_best'.)"
        )
    champion_path = MODELS_DIR / "champion.txt"
    old = champion_path.read_text(encoding="utf-8").strip() if champion_path.exists() else None
    if dry_run:
        print(f"[dry-run] wuerde {champion_path} von {old!r} auf {name!r} setzen ({onnx_path} gefunden).")
        return champion_path
    champion_path.write_text(name + "\n", encoding="utf-8")
    print(f"Champion gesetzt: {old!r} -> {name!r} ({champion_path}).")
    print("Wirkt erst nach einem Server-Neustart (DIFFICULTY_PRESETS wird beim Modul-Import gelesen).")
    return champion_path


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("name", help="Versionsname des neuen Champions, z.B. v17_best")
    p.add_argument("--dry-run", action="store_true", help="nur validieren, nichts schreiben")
    args = p.parse_args()
    set_champion(args.name, dry_run=args.dry_run)
