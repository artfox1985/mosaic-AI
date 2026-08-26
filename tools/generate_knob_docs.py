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


PREREG_DIR = REPO / "evaluations"
PREREG_STATUS_RE = re.compile(r"<!--\s*STATUS:\s*(OFFEN|ENTSCHIEDEN|UEBERHOLT)\b")
PREREG_NAME_RE = re.compile(r"PREREG_[a-z0-9_]+\.md")


def prereg_verdicts() -> dict[str, str]:
    """{Dateiname: OFFEN|ENTSCHIEDEN|UEBERHOLT} aus Zeile 1 jeder Prereg.

    Dieselbe Quelle, aus der `tools/generate_prereg_index.py` seinen Index
    baut -- der Zeile-1-Statuskopf. Hier wird nur das Verdikt gebraucht,
    nicht Frage und Beleg.
    """
    out: dict[str, str] = {}
    for path in sorted(PREREG_DIR.glob("PREREG_*.md")):
        head = path.read_text(encoding="utf-8", errors="replace")[:4096]
        m = PREREG_STATUS_RE.search(head)
        if m:
            out[path.name] = m.group(1)
    return out


def verdict_for(prereg_field: str, verdicts: dict[str, str]) -> str:
    """Verdikt der Prereg(s), auf die ein Knopf verweist.

    Das Feld traegt Freitext ("PREREG_x.md par.3", "-", manchmal zwei
    Dateien). Deshalb werden ALLE genannten Dateinamen aufgeloest; nennt ein
    Knopf mehrere und sie sind sich uneinig, steht das auch so da -- raten
    waere hier die falsche Freundlichkeit.
    """
    names = PREREG_NAME_RE.findall(prereg_field or "")
    if not names:
        return "-"
    found = [verdicts.get(n) or "?" for n in names]
    distinct = sorted(set(found))
    return distinct[0] if len(distinct) == 1 else "/".join(distinct)


def stale_knobs(knobs: list[dict]) -> list[dict]:
    """Verdrahtete Knoepfe, deren Frage laut Prereg BEANTWORTET ist.

    Genau die Schnittmenge, die weder die Registratur noch der Prereg-Index
    allein zeigt: der Status sagt "verdrahtet" (er sagt ausdruecklich NICHTS
    darueber, ob der Default an ist), der Prereg-Kopf sagt "entschieden" oder
    "ueberholt". Ein Knopf hier ist nicht automatisch zu loeschen -- ein
    negatives Ergebnis kann "falscher HEBEL, richtiges Ziel" heissen
    (PREREG_long_row_payoff ist genau so ein Fall). Die Liste macht die
    Entscheidung moeglich, sie nimmt sie niemandem ab.
    """
    return [k for k in knobs
            if k["status"] in ("aktiv", "diagnose")
            and k.get("verdict") in ("ENTSCHIEDEN", "UEBERHOLT")]


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


OFF_DEFAULTS = ("0", "0.0", "0,0", "false", "aus", "unset", "none", "nicht gesetzt")


def _default_is_off(default: str) -> bool:
    """Ist der beschriebene Default ein AUS?

    `default` ist laut `KnobEntry` ein BESCHREIBENDER String, kein Wert --
    die Erkennung ist deshalb eine Heuristik und wird im Dokument auch so
    ausgewiesen. Sie soll niemanden ueberzeugen, nur sortieren.
    """
    d = (default or "").strip().lower()
    return any(d == o or d.startswith(o + " ") for o in OFF_DEFAULTS)


def _stale_block(knobs: list[dict]) -> str:
    """Abschnitt fuer verdrahtete Knoepfe, deren Prereg beantwortet ist.

    WICHTIGE EINSCHRAENKUNG, die hier stehen muss, weil das Dokument sonst in
    die Irre fuehrt: der Zeile-1-Kopf einer Prereg sagt ENTSCHIEDEN, aber
    nicht die RICHTUNG. `MOSAIC_FLOOR_SHAPING_W` ist entschieden UND mit
    Default 0,3 der einzige Shaping-Knopf, der im Champion wirklich laeuft --
    eine Liste, die ihn neben die verworfenen Terme stellt, ist falsch.
    Deshalb wird nach dem Default getrennt.
    """
    answered = stale_knobs(knobs)
    if not answered:
        return "Kein verdrahteter Knopf haengt an einer beantworteten Prereg.\n"
    off = [k for k in answered if _default_is_off(k.get("default", ""))]
    on = [k for k in answered if not _default_is_off(k.get("default", ""))]
    lines = [
        f"**{len(answered)} verdrahtete Knoepfe haengen an einer BEANTWORTETEN Prereg** "
        "(entschieden oder ueberholt).",
        "",
        "Der Statuskopf sagt ENTSCHIEDEN, aber NICHT die Richtung -- deshalb die",
        "Trennung nach Default. Kein Loeschauftrag: ein negatives Ergebnis kann",
        "\"falscher Hebel, richtiges Ziel\" heissen (`PREREG_long_row_payoff` ist",
        "genau so ein Fall). Es ist die Liste, an der die Frage stellbar wird.",
        "",
        f"**Beantwortet UND Default aus ({len(off)})** -- hier lohnt die Nachfrage,",
        "ob der Knopf noch etwas offen haelt:",
        "",
    ]
    for k in off:
        lines.append(f"- `{k['name']}` ({k['verdict']}, {k['prereg']})")
    lines += ["",
              f"**Beantwortet, Default AN ({len(on)})** -- in Benutzung, hier ist "
              "\"entschieden\" das Ergebnis, nicht das Ende:", ""]
    for k in on:
        lines.append(f"- `{k['name']}` = {k['default']} ({k['verdict']}, {k['prereg']})")
    lines.append("")
    return "\n".join(lines)


def attach_verdicts(knobs: list[dict]) -> list[dict]:
    """Haengt jedem Knopf das Verdikt seiner Prereg an.

    Bewusst in BEIDEN Quellwegen (rs-Parse und Wheel) derselbe Schritt: die
    Verdikte kommen aus den Prereg-Dateien, nicht aus der Registratur -- die
    Paritaetsprobe zwischen beiden Wegen bleibt damit gueltig.
    """
    verdicts = prereg_verdicts()
    for k in knobs:
        k["verdict"] = verdict_for(k.get("prereg", ""), verdicts)
    return knobs


def render_markdown(knobs: list[dict], source_label: str) -> str:
    # Die Verdikte werden HIER angeheftet, nicht beim Aufrufer. Grund, beim
    # Bau aufgefallen: `check_conventions.py` Regel 6 ruft `render_markdown`
    # direkt, um docs/knobs.md gegen die Registratur zu pruefen -- ein
    # Anheften in `main()` haette diesen Weg uebersprungen, und die Regel
    # haette die Datei bei JEDEM Lauf als veraltet gemeldet.
    knobs = attach_verdicts(knobs)
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
        "**Status** sagt, ob der Knopf VERDRAHTET ist -- ausdruecklich nicht, ob sein",
        "Default an ist (`knob_registry.rs`: \"Default kann an ODER aus sein\").",
        "**Verdikt** ist der Zeile-1-Status der zitierten Prereg. Erst beide zusammen",
        "trennen \"aus, weil noch niemand ihn eingeschaltet hat\" von \"aus, weil die",
        "Messung ihn erledigt hat\" -- in der Registratur allein sehen die gleich aus.",
        "",
        _stale_block(knobs),
        "| Knopf | Default | Status | Verdikt | Zweck | Beleg |",
        "|---|---|---|---|---|---|",
    ]
    for k in knobs:
        lines.append(
            f"| `{k['name']}` | {k['default']} | {k['status']} | {k.get('verdict', '-')} "
            f"| {k['purpose']} | {k['prereg']} |"
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
