"""
Mosaic-AI — Release-Build-Skript (Task #96)

Baut das verteilbare Windows-Bundle (PyInstaller onedir) und packt es zu
einer ZIP-Datei, die der Nutzer direkt weitergeben kann (Empfänger: Windows,
kein Python/Rust installiert).

Ablauf:
  1. Alten dist/build-Output für "Mosaic-AI" entfernen.
  2. `pyinstaller mosaic_release.spec` ausführen.
  3. README_GAME.txt + docs/engine_manual.md ins Bundle kopieren.
  4. dist/Mosaic-AI/ zu Mosaic-AI_<champion>_<datum>.zip packen (Name aus models/champion.txt).

Aufruf (im Projekt-Root, mit aktivierter Python-Umgebung, in der
`pip install pyinstaller` bereits lief):

    python tools/build_release.py

Optional: --skip-build, um nur Schritt 3+4 (README-Kopie + Zip) erneut
auf einem bereits vorhandenen dist/Mosaic-AI/ laufen zu lassen.
"""

import argparse
import datetime
import os
import shutil
import stat
import subprocess
import sys
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = PROJECT_ROOT / "dist" / "Mosaic-AI"
BUILD_DIR = PROJECT_ROOT / "build" / "Mosaic-AI"
# Spec + Launcher liegen seit 2026-07-26 in dist/ (Root aufgeraeumt); das
# fertige Zip landet ebenfalls dort statt im Projektroot.
SPEC_FILE = PROJECT_ROOT / "dist" / "mosaic_release.spec"


def _force_rmtree(path: Path) -> None:
    """rmtree, das an OneDrive-ReadOnly-Attributen nicht scheitert.

    Unter OneDrive tragen zurueckgeschriebene Dateien haeufig das
    ReadOnly-Flag; `shutil.rmtree` wirft darauf PermissionError (WinError 5)
    und der PyInstaller-Lauf bricht ab, BEVOR er baut (mehrfach passiert,
    zuletzt 2026-08-15). Der Handler nimmt das Flag und versucht es erneut.
    """
    def onexc(func, target, exc):
        try:
            os.chmod(target, stat.S_IWRITE)
            func(target)
        except Exception:
            pass
    shutil.rmtree(path, onexc=onexc)


def run_pyinstaller() -> None:
    print(f"[1/4] Entferne alten Build-Output ({DIST_DIR}, {BUILD_DIR}) ...")
    for d in (DIST_DIR, BUILD_DIR):
        if d.exists():
            _force_rmtree(d)

    print("[2/4] Starte PyInstaller (mosaic_release.spec) ...")
    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", "--noconfirm", str(SPEC_FILE)],
        cwd=str(PROJECT_ROOT),
    )
    if result.returncode != 0:
        raise SystemExit(f"PyInstaller-Build fehlgeschlagen (Exit {result.returncode}).")
    if not DIST_DIR.exists():
        raise SystemExit(f"Build-Output fehlt unerwartet: {DIST_DIR}")


def copy_docs() -> None:
    print("[3/4] Kopiere README_GAME.txt + Anleitung ins Bundle ...")
    shutil.copy2(PROJECT_ROOT / "dist" / "README_GAME.txt", DIST_DIR / "README_GAME.txt")
    manual_src = PROJECT_ROOT / "docs" / "engine_manual.md"
    if manual_src.exists():
        shutil.copy2(manual_src, DIST_DIR / "engine_manual.md")
    else:
        print(f"  Warnung: {manual_src} nicht gefunden -- übersprungen.")


def make_zip() -> Path:
    print("[4/4] Packe ZIP ...")
    date_str = datetime.datetime.now().strftime("%Y%m%d")
    champion = (PROJECT_ROOT / "models" / "champion.txt").read_text(encoding="utf-8").strip()
    zip_path = PROJECT_ROOT / "dist" / f"Mosaic-AI_{champion}_{date_str}.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in DIST_DIR.rglob("*"):
            if f.is_file():
                zf.write(f, arcname=Path("Mosaic-AI") / f.relative_to(DIST_DIR))
    return zip_path


def _dir_size(path: Path) -> int:
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-build", action="store_true",
                         help="PyInstaller-Lauf überspringen (nur README-Kopie + Zip erneuern).")
    args = parser.parse_args()

    if not args.skip_build:
        run_pyinstaller()
    elif not DIST_DIR.exists():
        raise SystemExit(f"--skip-build gesetzt, aber {DIST_DIR} existiert nicht.")

    copy_docs()
    zip_path = make_zip()

    unpacked_mb = _dir_size(DIST_DIR) / (1024 * 1024)
    zip_mb = zip_path.stat().st_size / (1024 * 1024)
    print()
    print("=" * 60)
    print(f"Bundle:        {DIST_DIR}")
    print(f"  entpackt:    {unpacked_mb:.1f} MB")
    print(f"ZIP:           {zip_path}")
    print(f"  gepackt:     {zip_mb:.1f} MB")
    print("=" * 60)


if __name__ == "__main__":
    main()
