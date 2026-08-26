# -*- coding: utf-8 -*-
"""Prueft ein eingefrorenes Heuristik-Artefakt gegen seine Golden Probe.

Die Probe ist ein SELF-PLAY-Lauf (siehe `tools/freeze_heuristic.py`): das
Rezept steht im Manifest, der Lauf wird wiederholt und RECORD FUER RECORD
verglichen. Damit deckt die Pruefung Drafting, Tiling und Runde 5 ab -- nicht
nur die Drafting-Entscheidung wie die Welle-3-Probe der Netz-Champions.

ZWEI PRUEFMODI, und der Unterschied ist wichtig:

  (Default) mit dem AKTUELLEN Interpreter/Wheel
      Beantwortet: "erzeugt der heutige Stand noch dasselbe wie das Artefakt?"
      Das ist die Drift-Frage. Rot heisst nicht, dass das Artefakt kaputt ist,
      sondern dass der heutige Code sich davon entfernt hat.

  --venv  mit dem Wheel AUS dem Artefakt (eigene venv)
      Beantwortet: "spielt das Artefakt noch so, wie es eingefroren wurde?"
      Das ist die Konservierungs-Frage. Rot heisst: Umgebungsdrift (ORT, DLL,
      Interpreter) -- das Artefakt selbst ist unbrauchbar geworden.

Beide sind nuetzlich, aber sie beantworten NICHT dasselbe, und ein Bericht,
der sie vermengt, ist wertlos.

Verglichen wird ueber `corpus_io`, nicht auf Dateibytes: Korpusdateien werden
komprimiert geschrieben, und ein Byte-Diff meldete Unterschiede, die nichts
mit dem Verhalten zu tun haben. `game_id` traegt einen Zeitstempel und ist
ausgenommen (siehe `generator_repro_probe.IDENTITAETS_FELDER`).

Aufruf:
    python -X utf8 -u tools/verify_frozen_heuristic.py \\
        --artifact-dir models/frozen_heuristics/v1_anchor
    python -X utf8 -u tools/verify_frozen_heuristic.py \\
        --artifact-dir models/frozen_heuristics/v1_anchor --venv
"""
import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "tools" / "probes"))

from corpus_io import load_records  # noqa: E402
from generator_repro_probe import _first_divergence  # noqa: E402


def _venv_python(artifact: pathlib.Path) -> pathlib.Path:
    """Pfad zum Interpreter der Artefakt-venv (Windows- und POSIX-Form)."""
    for rel in ("venv/Scripts/python.exe", "venv/bin/python"):
        p = artifact / rel
        if p.exists():
            return p
    raise SystemExit(
        f"Keine venv in {artifact}. Mit --build-venv anlegen -- sie wird bewusst NICHT "
        "versioniert (33 MB, maschinenspezifische Pfade, aus dem Wheel neu herstellbar).")


def _build_venv(artifact: pathlib.Path) -> pathlib.Path:
    wheels = sorted(artifact.glob("*.whl"))
    if len(wheels) != 1:
        raise SystemExit(f"Erwarte GENAU ein Wheel in {artifact}, gefunden: {len(wheels)}")
    venv = artifact / "venv"
    if venv.exists():
        shutil.rmtree(venv)
    print(f"venv anlegen ...", flush=True)
    subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
    py = _venv_python(artifact)
    print(f"Wheel installieren: {wheels[0].name}", flush=True)
    subprocess.run([str(py), "-m", "pip", "install", "--quiet", "--no-deps", str(wheels[0])],
                   check=True)
    # Der Self-Play-Treiber braucht mehr als das Wheel.
    subprocess.run([str(py), "-m", "pip", "install", "--quiet", "numpy"], check=True)
    return py


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--artifact-dir", required=True)
    ap.add_argument("--venv", action="store_true",
                    help="mit dem Wheel AUS dem Artefakt pruefen (Konservierungs-Frage)")
    ap.add_argument("--build-venv", action="store_true",
                    help="die venv vorher neu anlegen (impliziert --venv)")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    artifact = pathlib.Path(a.artifact_dir)
    manifest = json.loads((artifact / "manifest.json").read_text(encoding="utf-8"))
    recipe = manifest["golden_probe"]["rezept"]
    spec = json.loads((artifact / "spec.json").read_text(encoding="utf-8"))

    # Die Variante kommt aus der SPEC des Artefakts, nicht aus dem Aufruf.
    # Genau das ist der Punkt der Kapselung -- und der Fehler vom 2026-08-26
    # (Rezept dokumentiert, Aufruf hat es nicht mitgenommen) kann hier nicht
    # mehr passieren. Gegenprobe trotzdem, weil zwei Quellen zwei Wahrheiten
    # sind: Spec und Rezept muessen uebereinstimmen.
    if spec["heuristik_variante"] != recipe["heuristik_variante"]:
        raise SystemExit(
            f"Artefakt widerspruechlich: spec.json sagt "
            f"'{spec['heuristik_variante']}', das Probe-Rezept sagt "
            f"'{recipe['heuristik_variante']}'. Kein Lauf, bis das geklaert ist.")

    if a.build_venv:
        py = _build_venv(artifact)
        a.venv = True
    elif a.venv:
        py = _venv_python(artifact)
    else:
        py = pathlib.Path(sys.executable)
    run_mode = "Artefakt-venv (Konservierung)" if a.venv else "aktueller Interpreter (Drift)"
    print(f"Pruefmodus: {run_mode}\n  Interpreter: {py}", flush=True)

    t0 = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="frozen_verify_") as tmp:
        cmd = [str(py), "-X", "utf8", "-u", str(_ROOT / "self_play.py"),
               "--mode", recipe["mode"], "--games", str(recipe["games"]),
               "--sims", str(recipe["sims"]), "--version", recipe["version"],
               "--threads", str(recipe["threads"]), "--chunk", str(recipe["chunk"]),
               "--per-file", str(recipe["per_file"]), "--seed", str(recipe["seed"]),
               "--c-puct", str(recipe["c_puct"]),
               "--tau-argmax-from-move", str(recipe["tau_argmax_from_move"]),
               "--heuristik-variante", spec["heuristik_variante"]]
        if recipe.get("model"):
            cmd += ["--model", str(artifact / recipe["model"])]
        env = dict(os.environ, MOSAIC_DATA_DIR=tmp)
        r = subprocess.run(cmd, cwd=str(_ROOT), env=env, text=True, encoding="utf-8",
                           capture_output=True)
        if r.returncode != 0:
            print(r.stdout[-2000:], file=sys.stderr)
            print(r.stderr[-2000:], file=sys.stderr)
            raise SystemExit(f"Wiederholungslauf fehlgeschlagen (Code {r.returncode}).")

        new = sorted(pathlib.Path(tmp).glob("*.pkl"))
        ref = sorted((artifact / "golden_probe").glob("*.pkl"))
        if len(new) != len(ref):
            raise SystemExit(f"Dateizahl verschieden: Probe {len(ref)}, Lauf {len(new)}.")

        findings, all_same = [], True
        for rf, nf in zip(ref, new):
            ra, rb = load_records(rf), load_records(nf)
            div = _first_divergence(ra, rb)
            same = div is None and len(ra) == len(rb)
            all_same &= same
            findings.append({"probe": rf.name, "schritte": len(ra), "identisch": same,
                            "erste_abweichung": None if div is None else
                            {"schritt": div[0], "feld": div[1]}})
            print(f"  {'IDENTISCH ' if same else 'ABWEICHUNG'} {rf.name}  {len(ra)} Schritte",
                  flush=True)

    out = {
        "artefakt": str(artifact).replace("\\", "/"),
        "variante": spec["heuristik_variante"],
        "modus": run_mode,
        "verdikt": "GRUEN" if all_same else "ROT",
        "dateien": findings,
        "laufzeit": {"wanduhr_s": round(time.monotonic() - t0, 1), "cpu_s": None,
                     "threads": recipe["threads"], "s_je_partie": None},
    }
    target = pathlib.Path(a.out or f"evaluations/artifacts/frozen_verify_{artifact.name}.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")

    print(f"\n{out['verdikt']}: {sum(b['identisch'] for b in findings)}/{len(findings)} Dateien "
          f"Feld fuer Feld gleich ({run_mode})")
    print(f"Artefakt: {target}")
    return 0 if all_same else 1


if __name__ == "__main__":
    raise SystemExit(main())
