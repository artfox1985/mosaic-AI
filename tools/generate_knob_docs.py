# -*- coding: utf-8 -*-
"""Erzeugt docs/knobs.md aus der MOSAIC_*-Knopf-Registratur.

Zwei Quellen (Architektur-Fahrplan Punkt 3):
  --source (DEFAULT): parst engine/src/knob_registry.rs direkt (Textmuster,
      siehe dortiger FORMAT-VERTRAG im Modulkommentar: ein KnobEntry je
      Zeile). Braucht KEIN installiertes Wheel -- der einzige Weg, der
      waehrend eines laufenden Trainings-Sweeps erlaubt ist (die .pyd ist
      dann vom Sweep-Prozess gesperrt, kein Reinstall moeglich).
  --wheel: importiert mosaic_rust und ruft knob_registry_json() -- die
      autoritative Quelle, aber erst nutzbar, wenn das Wheel nach dem
      Sweep-Ende neu installiert wurde (Paritaetsprobe: beide Wege muessen
      dieselbe Tabelle liefern).

Aufruf:
    python tools/generate_knob_docs.py             # rs-Parse -> docs/knobs.md
    python tools/generate_knob_docs.py --wheel     # via installiertem Wheel
    python tools/generate_knob_docs.py --check     # nur pruefen, ob docs/knobs.md aktuell ist (Exit 1 sonst)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REGISTRY_RS = REPO / "engine" / "src" / "knob_registry.rs"
OUTPUT_MD = REPO / "docs" / "knobs.md"

# FORMAT-VERTRAG mit knob_registry.rs (dortiger Modulkommentar): ein Eintrag
# je Zeile. Feld-Reihenfolge fest: name, default, status, purpose, prereg.
ENTRY_RE = re.compile(
    r'KnobEntry\s*\{\s*name:\s*"(?P<name>[^"]+)",\s*default:\s*"(?P<default>[^"]*)",'
    r'\s*status:\s*KnobStatus::(?P<status>\w+),\s*purpose:\s*"(?P<purpose>[^"]*)",'
    r'\s*prereg:\s*"(?P<prereg>[^"]*)"\s*,?\s*\}'
)

STATUS_MAP = {"Aktiv": "aktiv", "Diagnose": "diagnose", "Tot": "tot", "Geplant": "geplant"}


def knobs_from_source() -> list[dict]:
    text = REGISTRY_RS.read_text(encoding="utf-8")
    # Nur die KNOBS-Tabelle parsen, nicht evtl. Beispiel-Eintraege in Tests.
    start = text.index("pub const KNOBS")
    end = text.index("];", start)
    entries = []
    for m in ENTRY_RE.finditer(text[start:end]):
        d = m.groupdict()
        d["status"] = STATUS_MAP[d.pop("status")]
        entries.append(d)
    if not entries:
        raise SystemExit(f"Keine KnobEntry-Zeilen in {REGISTRY_RS} gefunden -- Format-Vertrag verletzt?")
    return entries


def knobs_from_wheel() -> list[dict]:
    import mosaic_rust  # noqa: F401 -- braucht das installierte Wheel

    payload = json.loads(mosaic_rust.knob_registry_json())
    return payload["knobs"]


def render_markdown(knobs: list[dict], source_label: str) -> str:
    lines = [
        "# MOSAIC_*-Laufzeit-Knoepfe",
        "",
        "GENERIERT -- nicht von Hand editieren. Quelle: `engine/src/knob_registry.rs`",
        f"({source_label}), Generator: `tools/generate_knob_docs.py`.",
        "",
        "Der Waechter-Test `knob_registry::tests::all_mosaic_env_vars_in_code_are_registered`",
        "stellt sicher, dass jeder im Code vorkommende `MOSAIC_*`-Knopf hier steht.",
        "",
        f"Stand: {len(knobs)} Knoepfe "
        f"({sum(1 for k in knobs if k['status'] == 'aktiv')} aktiv, "
        f"{sum(1 for k in knobs if k['status'] == 'diagnose')} diagnose, "
        f"{sum(1 for k in knobs if k['status'] == 'tot')} tot, "
        f"{sum(1 for k in knobs if k['status'] == 'geplant')} geplant).",
        "",
        "| Knopf | Default | Status | Zweck | Beleg |",
        "|---|---|---|---|---|",
    ]
    for k in knobs:
        lines.append(
            f"| `{k['name']}` | {k['default']} | {k['status']} | {k['purpose']} | {k['prereg']} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--wheel", action="store_true", help="Quelle: installiertes Wheel statt rs-Parse")
    ap.add_argument("--check", action="store_true", help="nur pruefen, ob docs/knobs.md aktuell ist")
    args = ap.parse_args()

    if args.wheel:
        knobs, label = knobs_from_wheel(), "via installiertem Wheel, knob_registry_json()"
    else:
        knobs, label = knobs_from_source(), "direkt geparst, kein Wheel noetig"

    md = render_markdown(knobs, label)
    if args.check:
        current = OUTPUT_MD.read_text(encoding="utf-8") if OUTPUT_MD.exists() else ""
        if current != md:
            print(f"{OUTPUT_MD} ist NICHT aktuell -- `python tools/generate_knob_docs.py` laufen lassen.", file=sys.stderr)
            return 1
        print(f"{OUTPUT_MD} ist aktuell ({len(knobs)} Knoepfe).")
        return 0

    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.write_text(md, encoding="utf-8", newline="\n")
    print(f"{OUTPUT_MD} geschrieben ({len(knobs)} Knoepfe, Quelle: {label}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
