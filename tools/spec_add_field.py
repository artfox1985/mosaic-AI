# -*- coding: utf-8 -*-
"""Ein Pflichtfeld in lebende Spec-Dateien nachziehen (models/*.spec.json).

Anlass (2026-09-06, K3-F): jeder neue Such-Knopf ist nach der Welle-1-Regel ein
Spec-PFLICHTFELD (net_mcts.rs SearchConfig::from_spec_file: kein stiller Default),
und ein Wheel lehnt UNBEKANNTE Felder hart ab. Beides zusammen heisst: die lebenden
Specs duerfen das Feld erst bekommen, wenn kein Lauf mehr mit einem aelteren Wheel
darauf zugreift (laufende Ketten lesen die Specs bei jedem Partie-Start neu), und
sie MUESSEN es bekommen, bevor das neue Wheel installiert wird. Eingefrorene
Artefakte (models/frozen_*/**/spec.json) bleiben unangetastet -- sie laufen auf
ihrem mitgelieferten Wheel.

Aufruf (Projektordner):
    python tools/spec_add_field.py envelope_flush_w 0.0            # alle models/*.spec.json
    python tools/spec_add_field.py envelope_flush_w 0.0 --check    # nur pruefen, Exit 1 wenn etwas fehlt
    python tools/spec_add_field.py envelope_flush_w 0.5 models/k3f_c10.spec.json  # gezielt
    python tools/spec_add_field.py envelope_hull_form 1             # par.8.15 Teil B (Bau-Fenster)

Das Feld wird VOR "heuristik_variante" eingefuegt (Konvention der Spec-Dateien:
Knoepfe zuerst, Variante zuletzt); vorhandene Werte werden nicht ueberschrieben.
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent


def add_field(path: Path, name: str, value, check_only: bool) -> str:
    spec = json.loads(path.read_text(encoding="utf-8"))
    if name in spec:
        return "vorhanden"
    if check_only:
        return "FEHLT"
    items = list(spec.items())
    pos = next((i for i, (k, _) in enumerate(items) if k == "heuristik_variante"), len(items))
    items.insert(pos, (name, value))
    path.write_text(json.dumps(dict(items), indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return "ergaenzt"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("name")
    ap.add_argument("value", help="JSON-Wert, z.B. 0.0, 1, \"hv1\"")
    ap.add_argument("files", nargs="*", help="Spec-Dateien; ohne Angabe alle models/*.spec.json (nicht frozen_*)")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    value = json.loads(a.value)
    files = [Path(f) for f in a.files] or sorted(Path(p) for p in glob.glob(str(HERE / "models" / "*.spec.json")))
    missing = 0
    for f in files:
        res = add_field(f, a.name, value, a.check)
        missing += res == "FEHLT"
        print(f"  {res:10s} {f.relative_to(HERE) if f.is_absolute() else f}")
    if a.check and missing:
        print(f"{missing} Spec-Datei(en) ohne '{a.name}'")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
