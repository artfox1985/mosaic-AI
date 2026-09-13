# -*- mode: python ; coding: utf-8 -*-
# Mosaic-AI — PyInstaller-Spec für das verteilbare Release-Bundle (Task #96).
#
# Bewusst onedir (nicht onefile): Antivirus-freundlicher (kein selbst-
# entpackendes Archiv) und deutlich schnellerer Start. README_GAME.txt und
# docs/engine_manual.md werden NICHT hier eingebunden, sondern von
# tools/build_release.py nach dem PyInstaller-Lauf ins dist-Verzeichnis
# kopiert (einfacher als Datei-Umbenennung über Analysis-datas).
#
# Aufruf: pyinstaller mosaic_release.spec  (siehe tools/build_release.py)

import os

# Spec liegt seit 2026-07-26 in dist/ (Nutzer-Wunsch: Root aufgeraeumt) --
# der Projekt-Root ist daher das ELTERN-Verzeichnis des Spec-Ordners.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(SPEC)), '..'))


def collect_static_datas():
    """Alle Dateien unter static/ außer static/log/* (transiente Spiel-
    protokolle -- der Ordner wird zur Laufzeit von server.py neu angelegt,
    siehe LOG_DIR.mkdir(parents=True, exist_ok=True))."""
    datas = []
    static_root = os.path.join(PROJECT_ROOT, 'static')
    for dirpath, dirnames, filenames in os.walk(static_root):
        dirnames[:] = [d for d in dirnames if d != 'log']
        if os.path.basename(dirpath) == 'log':
            continue
        rel_dir = os.path.relpath(dirpath, PROJECT_ROOT)
        for f in filenames:
            datas.append((os.path.join(dirpath, f), rel_dir))
    return datas


datas = collect_static_datas()

# Nur das aktive Referenz-Netz (Task #96): kein .pth, keine anderen Versionsstände.
# Champion-Stand 2026-08-15 war v21_2d_brierbest (Elo 1358). champion.txt MUSS
# mit ins Bundle -- server.py::_load_champion_model liest sie und fiele ohne
# sie auf den Namen "v16_best" zurueck, dessen ONNX hier gar nicht mitgeliefert
# wird. (KORREKTUR 2026-08-15: eine fruehere Fassung dieses Kommentars nannte
# v16 "engine-inkompatibel" -- das ist FALSCH und war ungeprueft. NUM_ACTIONS
# 406 und INPUT_SIZE 708 sind zwischen dem v16-Tag und heute identisch
# (git show v0.1-alpha16:config.py); v16 ist nur ein flaches, viel schwaecheres
# Netz, kein unladbares.)
# Champion-Stand 2026-09-13: v28-b02_brierbest (Elo 1353, Leitersegment 2). Ein Champion
# ist seit 0e87ddd Modell PLUS Spec: server.py::_resolve_champion_spec sucht
# models/<name>.spec.json und dann models/frozen_champions/<name ohne Suffix>/spec.json;
# ohne die Spec gelten Env-Defaults und die Champion-Knoepfe (Huelle, K5) fehlen
# (Audit evaluations/review/portable_build_audit_2026-09-13.md, Luecken 1 und 2).
datas.append((os.path.join(PROJECT_ROOT, 'models', 'alphazero_v28-b02_brierbest.onnx'), 'models'))
datas.append((os.path.join(PROJECT_ROOT, 'models', 'frozen_champions', 'v28-b02', 'spec.json'),
              os.path.join('models', 'frozen_champions', 'v28-b02')))
datas.append((os.path.join(PROJECT_ROOT, 'models', 'champion.txt'), 'models'))
# Elo-Historie mitliefern: ohne sie hat estimate_ai_anchor keine Arena-Kanten
# und JEDES KI-Spiel waere ungewertet (Rauchtest-Befund 2026-08-15).
datas.append((os.path.join(PROJECT_ROOT, 'evaluations', 'elo_history.csv'), 'evaluations'))

a = Analysis(
    ['run_mosaic.py'],
    pathex=[PROJECT_ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=['mosaic_rust', 'flask_cors'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Schwere ML-/Dev-Pakete, die server.py/run_mosaic.py NICHT importieren
        # (Rust-Engine nutzt tract-onnx statisch einkompiliert, kein Python-
        # onnxruntime/torch zur Laufzeit nötig) -- hält das Bundle klein.
        'torch', 'torchvision', 'torchaudio', 'onnx', 'onnxruntime',
        'matplotlib', 'pandas', 'scipy', 'sklearn', 'IPython', 'notebook',
        'jupyter', 'tkinter', 'PyQt5', 'PySide2',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Mosaic-AI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Mosaic-AI',
)
