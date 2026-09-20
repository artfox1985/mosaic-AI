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
# Ein Champion ist seit 0e87ddd Modell PLUS Spec: server.py::_resolve_champion_spec sucht
# models/<name>.spec.json und dann models/frozen_champions/<name ohne Suffix>/spec.json;
# ohne die Spec gelten Env-Defaults und die Champion-Knoepfe (Huelle, K5) fehlen
# (Audit evaluations/review/portable_build_audit_2026-09-13.md, Luecken 1 und 2).
#
# DER NAME KOMMT AUS champion.txt, NICHT aus einem Literal hier (2026-09-20).
# Vorher stand er dreimal fest verdrahtet, zuletzt auf v28-b02 -- waehrend
# champion.txt im selben Bundle laengst einen anderen Champion nannte. Das Bundle
# haette sein eigenes Modell nicht gefunden. Wer den Champion wechselt, denkt an
# tools/set_champion.py; an diese Datei denkt niemand.
_champion = (open(os.path.join(PROJECT_ROOT, 'models', 'champion.txt'),
                  encoding='utf-8').read().strip())
# Suffix nur am ENDE streifen und die DIREKTE Spec zuerst suchen -- beides wie
# server.py::_resolve_champion_spec. Eine fruehere Fassung nahm `.replace()` (trifft
# das Muster ueberall im Namen) und kannte `models/<name>.spec.json` gar nicht; sie
# haette abgebrochen, wo der Server laeuft. Genau dieser Fall ist in server.py:248-251
# als Vorfall vom 2026-09-10 dokumentiert.
_champ_base = _champion
for _suffix in ('_brierbest', '_best'):
    if _champ_base.endswith(_suffix):
        _champ_base = _champ_base[: -len(_suffix)]
_champ_onnx = os.path.join(PROJECT_ROOT, 'models', f'alphazero_{_champion}.onnx')
_direct_spec = os.path.join(PROJECT_ROOT, 'models', f'{_champion}.spec.json')
if os.path.exists(_direct_spec):
    _champ_spec, _spec_ziel = _direct_spec, 'models'
else:
    _champ_spec = os.path.join(PROJECT_ROOT, 'models', 'frozen_champions', _champ_base, 'spec.json')
    _spec_ziel = os.path.join('models', 'frozen_champions', _champ_base)
for _p in (_champ_onnx, _champ_spec):
    if not os.path.exists(_p):
        raise SystemExit(f'ABBRUCH: {_p} fehlt -- das Bundle waere ohne Champion. '
                         f'champion.txt sagt {_champion!r}.')
datas.append((_champ_onnx, 'models'))
datas.append((_champ_spec, _spec_ziel))
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
