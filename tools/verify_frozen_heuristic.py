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
from generator_repro_probe import _erste_abweichung  # noqa: E402


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
    rezept = manifest["golden_probe"]["rezept"]
    spec = json.loads((artifact / "spec.json").read_text(encoding="utf-8"))

    # Die Variante kommt aus der SPEC des Artefakts, nicht aus dem Aufruf.
    # Genau das ist der Punkt der Kapselung -- und der Fehler vom 2026-08-26
    # (Rezept dokumentiert, Aufruf hat es nicht mitgenommen) kann hier nicht
    # mehr passieren. Gegenprobe trotzdem, weil zwei Quellen zwei Wahrheiten
    # sind: Spec und Rezept muessen uebereinstimmen.
    if spec["heuristik_variante"] != rezept["heuristik_variante"]:
        raise SystemExit(
            f"Artefakt widerspruechlich: spec.json sagt "
            f"'{spec['heuristik_variante']}', das Probe-Rezept sagt "
            f"'{rezept['heuristik_variante']}'. Kein Lauf, bis das geklaert ist.")

    if a.build_venv:
        py = _build_venv(artifact)
        a.venv = True
    elif a.venv:
        py = _venv_python(artifact)
    else:
        py = pathlib.Path(sys.executable)
    modus = "Artefakt-venv (Konservierung)" if a.venv else "aktueller Interpreter (Drift)"
    print(f"Pruefmodus: {modus}\n  Interpreter: {py}", flush=True)

    t0 = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="frozen_verify_") as tmp:
        cmd = [str(py), "-X", "utf8", "-u", str(_ROOT / "self_play.py"),
               "--mode", rezept["mode"], "--games", str(rezept["games"]),
               "--sims", str(rezept["sims"]), "--version", rezept["version"],
               "--threads", str(rezept["threads"]), "--chunk", str(rezept["chunk"]),
               "--per-file", str(rezept["per_file"]), "--seed", str(rezept["seed"]),
               "--c-puct", str(rezept["c_puct"]),
               "--tau-argmax-from-move", str(rezept["tau_argmax_from_move"]),
               "--heuristik-variante", spec["heuristik_variante"]]
        if rezept.get("model"):
            cmd += ["--model", str(artifact / rezept["model"])]
        env = dict(os.environ, MOSAIC_DATA_DIR=tmp)
        r = subprocess.run(cmd, cwd=str(_ROOT), env=env, text=True, encoding="utf-8",
                           capture_output=True)
        if r.returncode != 0:
            print(r.stdout[-2000:], file=sys.stderr)
            print(r.stderr[-2000:], file=sys.stderr)
            raise SystemExit(f"Wiederholungslauf fehlgeschlagen (Code {r.returncode}).")

        neu = sorted(pathlib.Path(tmp).glob("*.pkl"))
        ref = sorted((artifact / "golden_probe").glob("*.pkl"))
        if len(neu) != len(ref):
            raise SystemExit(f"Dateizahl verschieden: Probe {len(ref)}, Lauf {len(neu)}.")

        befunde, alle_gleich = [], True
        for rf, nf in zip(ref, neu):
            ra, rb = load_records(rf), load_records(nf)
            abw = _erste_abweichung(ra, rb)
            gleich = abw is None and len(ra) == len(rb)
            alle_gleich &= gleich
            befunde.append({"probe": rf.name, "schritte": len(ra), "identisch": gleich,
                            "erste_abweichung": None if abw is None else
                            {"schritt": abw[0], "feld": abw[1]}})
            print(f"  {'IDENTISCH ' if gleich else 'ABWEICHUNG'} {rf.name}  {len(ra)} Schritte",
                  flush=True)

    erg = {
        "artefakt": str(artifact).replace("\\", "/"),
        "variante": spec["heuristik_variante"],
        "modus": modus,
        "verdikt": "GRUEN" if alle_gleich else "ROT",
        "dateien": befunde,
        "laufzeit": {"wanduhr_s": round(time.monotonic() - t0, 1), "cpu_s": None,
                     "threads": rezept["threads"], "s_je_partie": None},
    }
    ziel = pathlib.Path(a.out or f"evaluations/artifacts/frozen_verify_{artifact.name}.json")
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(json.dumps(erg, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")

    print(f"\n{erg['verdikt']}: {sum(b['identisch'] for b in befunde)}/{len(befunde)} Dateien "
          f"Feld fuer Feld gleich ({modus})")
    print(f"Artefakt: {ziel}")
    return 0 if alle_gleich else 1


if __name__ == "__main__":
    raise SystemExit(main())
