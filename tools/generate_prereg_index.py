"""
tools/generate_prereg_index.py -- erzeugt den Tabellenteil von
evaluations/PREREG_INDEX.md deterministisch aus den Status-Koepfen der
einzelnen Prereg-Dateien.

Anlass (Architektur-Fahrplan Punkt 1, 2026-08-15): der Index wurde von Hand
gepflegt; eine veraltete Zeile hat am 2026-08-12 einen unnoetigen
Agenten-Auftrag ausgeloest (STALE-FALLE-Vermerk, vormals in der
`PREREG_gpu_offloading.md`-Zeile). Seither traegt jede
`evaluations/PREREG_*.md` in ihrer ersten Zeile einen maschinenlesbaren
Status-Kopf als HTML-Kommentar:

    <!-- STATUS: OFFEN | Frage: <eine Zeile> | Beleg: <eine Zeile> -->

Gueltige Status: OFFEN / ENTSCHIEDEN / UEBERHOLT. Die Frage-/Beleg-Zellen
duerfen kein `|` und kein `-->` enthalten (Tabellen- bzw. Kommentar-Ende).
Der Status-Kopf in der DATEI ist die Wahrheit; dieser Generator schreibt sie
nur in den Index. Wer einen Status aendert, aendert den Kopf der Datei und
laesst den Generator laufen.

Der Generator ersetzt AUSSCHLIESSLICH den Bereich zwischen den Markern
BEGIN/END GENERATED PREREG TABLES im Index; der erklaerende Vorspann
(Anlass, NAMENSKONVENTION, Alt-Buchstaben-Tabelle) und der historische
Schlussteil bleiben statischer Text.

CLI:
    python tools/generate_prereg_index.py            # Index neu schreiben
    python tools/generate_prereg_index.py --check    # nur pruefen: Exit 1,
                                                     # wenn der Index nicht
                                                     # dem Generat entspricht
Regel A5 (`tools/check_conventions.py`) nutzt --check-Logik per Import.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PREREG_DIR = REPO_ROOT / "evaluations"
INDEX_PATH = PREREG_DIR / "PREREG_INDEX.md"

BEGIN_MARKER = "<!-- BEGIN GENERATED PREREG TABLES (tools/generate_prereg_index.py; nicht von Hand editieren) -->"
END_MARKER = "<!-- END GENERATED PREREG TABLES -->"

STATUS_ORDER = ["OFFEN", "ENTSCHIEDEN", "UEBERHOLT"]

# Kopf muss in den ersten Zeilen der Datei stehen (Byte-Budget grosszuegig:
# die Beleg-Zeile kann lang sein, bleibt aber EIN Kommentar am Dateianfang).
HEADER_SEARCH_LIMIT = 4096
HEADER_RE = re.compile(
    r"<!--\s*STATUS:\s*(OFFEN|ENTSCHIEDEN|UEBERHOLT)\s*\|"
    r"\s*Frage:\s*(.*?)\s*\|"
    r"\s*Beleg:\s*(.*?)\s*-->",
    re.DOTALL,
)


def prereg_files() -> list[Path]:
    return sorted(
        (p for p in PREREG_DIR.glob("PREREG_*.md") if p.name != INDEX_PATH.name),
        key=lambda p: p.name.lower(),
    )


def parse_status_header(text: str) -> tuple[str, str, str] | None:
    """(status, frage, beleg) aus dem Dateianfang, oder None wenn kein
    parsebarer Kopf vorhanden ist. Der Kommentar muss VOR jedem anderen
    Inhalt stehen (fuehrender Whitespace erlaubt) -- ein Kommentar mitten in
    der Datei zaehlt absichtlich nicht als Status-Kopf."""
    head = text[:HEADER_SEARCH_LIMIT]
    m = HEADER_RE.search(head)
    if m is None or head[: m.start()].strip():
        return None
    frage = " ".join(m.group(2).split())
    beleg = " ".join(m.group(3).split())
    if "|" in frage or "|" in beleg:
        return None  # wuerde die Markdown-Tabelle sprengen
    return m.group(1), frage, beleg


def collect() -> tuple[dict[str, list[tuple[str, str, str]]], list[str]]:
    """Liest alle Prereg-Koepfe. Rueckgabe: ({status: [(datei, frage, beleg)]},
    [Dateien ohne parsebaren Kopf])."""
    by_status: dict[str, list[tuple[str, str, str]]] = {s: [] for s in STATUS_ORDER}
    unparsable: list[str] = []
    for p in prereg_files():
        parsed = parse_status_header(p.read_text(encoding="utf-8", errors="replace"))
        if parsed is None:
            unparsable.append(p.name)
            continue
        status, frage, beleg = parsed
        by_status[status].append((p.name, frage, beleg))
    return by_status, unparsable


def render_tables(by_status: dict[str, list[tuple[str, str, str]]]) -> str:
    total = sum(len(v) for v in by_status.values())
    counts = " + ".join(f"{len(by_status[s])} {s}" for s in STATUS_ORDER)
    lines = [
        f"**Stand (automatisch generiert): {total} Dateien = {counts}.**",
        "Sortierung: OFFEN zuerst, dann ENTSCHIEDEN, dann UEBERHOLT; innerhalb",
        "der Abschnitte alphabetisch nach Dateiname. Quelle je Zeile: der",
        "Status-Kopf (HTML-Kommentar) in der ersten Zeile der Datei.",
        "",
    ]
    for status in STATUS_ORDER:
        rows = by_status[status]
        lines.append(f"## {status} ({len(rows)})")
        lines.append("")
        lines.append("| Datei | Frage (1 Zeile) | Belegstelle |")
        lines.append("|---|---|---|")
        for name, frage, beleg in rows:
            lines.append(f"| `{name}` | {frage} | {beleg} |")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def regenerate_index_text(index_text: str) -> tuple[str, list[str]]:
    """Ersetzt den Marker-Bereich im uebergebenen Index-Text. Rueckgabe:
    (neuer Text, Dateien ohne parsebaren Kopf). Wirft ValueError, wenn die
    Marker fehlen oder in falscher Reihenfolge stehen."""
    begin = index_text.find(BEGIN_MARKER)
    end = index_text.find(END_MARKER)
    if begin == -1 or end == -1 or end < begin:
        raise ValueError(
            "PREREG_INDEX.md: BEGIN/END-Marker des generierten Tabellenteils "
            "fehlen oder stehen in falscher Reihenfolge."
        )
    by_status, unparsable = collect()
    # Zeilenende an den Bestand der Index-Datei angleichen (CRLF-Repo-Mix).
    nl = "\r\n" if "\r\n" in index_text else "\n"
    generated = render_tables(by_status).replace("\n", nl)
    new_text = (
        index_text[: begin + len(BEGIN_MARKER)]
        + nl + nl
        + generated
        + nl
        + index_text[end:]
    )
    return new_text, unparsable


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument(
        "--check", action="store_true",
        help="nicht schreiben, nur pruefen (Exit 1 bei Abweichung oder unparsebaren Koepfen)",
    )
    args = parser.parse_args()

    index_text = INDEX_PATH.read_text(encoding="utf-8")
    new_text, unparsable = regenerate_index_text(index_text)

    if unparsable:
        print(
            "Dateien ohne parsebaren Status-Kopf (erste Zeile, "
            "<!-- STATUS: ... | Frage: ... | Beleg: ... -->):\n  "
            + "\n  ".join(unparsable),
            file=sys.stderr,
        )
        return 1

    if args.check:
        if new_text != index_text:
            print(
                "PREREG_INDEX.md ist nicht auf Generator-Stand -- "
                "`python tools/generate_prereg_index.py` laufen lassen und den "
                "Index mitcommitten.",
                file=sys.stderr,
            )
            return 1
        print("PREREG_INDEX.md entspricht dem Generator-Output.")
        return 0

    if new_text != index_text:
        INDEX_PATH.write_text(new_text, encoding="utf-8", newline="")
        print(f"{INDEX_PATH} neu geschrieben.")
    else:
        print(f"{INDEX_PATH} war bereits auf Stand.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
