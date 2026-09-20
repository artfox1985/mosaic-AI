"""
Mosaic-AI — Release-Build-Skript (Task #96)

Baut das verteilbare Windows-Bundle (PyInstaller onedir) und packt es zu
einer ZIP-Datei, die der Nutzer direkt weitergeben kann (Empfänger: Windows,
kein Python/Rust installiert).

Ablauf:
  1. Alten dist/build-Output für "Mosaic-AI" entfernen.
  2. `pyinstaller mosaic_release.spec` ausführen.
  3. README_GAME.txt + docs/engine_manual.md ins Bundle kopieren.
  4. dist/Mosaic-AI/ zu Mosaic-AI_v<paketversion>-alpha<generation>.zip packen
     (Version aus engine/pyproject.toml, Generation aus models/champion.txt).

Aufruf (im Projekt-Root, mit aktivierter Python-Umgebung, in der
`pip install pyinstaller` bereits lief):

    python tools/build_release.py

Optional: --skip-build, um nur Schritt 3+4 (README-Kopie + Zip) erneut
auf einem bereits vorhandenen dist/Mosaic-AI/ laufen zu lassen.
"""

import argparse
import os
import re
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


def release_name() -> str:
    """Bundle-Name `Mosaic-AI_v<paketversion>-alpha<generation>` (Nutzer 2026-09-21).

    Zwei Quellen, beide bereits im Baum gepflegt, keine dritte Stelle zum Nachziehen:

    * die PAKETVERSION aus `engine/pyproject.toml` -- dieselbe, die im Wheel-Dateinamen
      steht (maturin liest sie von dort, NICHT aus Cargo.toml; der Unterschied hat am
      2026-09-20 einen Versionssprung stillschweigend verschluckt). Auf zwei Stellen
      gekuerzt: 1.0.0 -> "1.0".
    * die GENERATIONSNUMMER aus `models/champion.txt`: `v31-b01_brierbest` -> 31. Damit
      folgt der Name dem Champion von selbst, statt bei jeder Promotion von Hand
      nachgezogen zu werden -- genau die Fehlerklasse, an der die PyInstaller-Spec drei
      Generationen lang vorbeigelaufen ist (`evaluations/PREREG_code_cleanup_closeout.md`
      par.8f/8g).

    KEIN Datum mehr im Namen: ein Release-Artefakt soll bei gleicher Version und gleicher
    Generation DIESELBE Datei sein. Ein Neubau ueberschreibt darum in place.
    """
    champion = (PROJECT_ROOT / "models" / "champion.txt").read_text(encoding="utf-8").strip()
    m = re.match(r"^v(\d+)-", champion)
    if not m:
        raise SystemExit(
            f"ABBRUCH: aus champion.txt ({champion!r}) laesst sich keine Generationsnummer "
            f"lesen; erwartet ist die Form 'v<zahl>-...'.")
    generation = m.group(1)

    pyproject = (PROJECT_ROOT / "engine" / "pyproject.toml").read_text(encoding="utf-8")
    v = re.search(r'^version\s*=\s*"(\d+)\.(\d+)', pyproject, re.MULTILINE)
    if not v:
        raise SystemExit("ABBRUCH: keine Paketversion in engine/pyproject.toml gefunden.")
    return f"Mosaic-AI_v{v.group(1)}.{v.group(2)}-alpha{generation}"


def make_zip() -> Path:
    print("[4/4] Packe ZIP ...")
    zip_path = PROJECT_ROOT / "dist" / f"{release_name()}.zip"
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
