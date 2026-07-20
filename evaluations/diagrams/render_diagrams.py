"""
Rendert Graphviz-DOT-Diagramme aus diagrams.txt als PNG/SVG (via das
`graphviz`-Python-Paket + die installierte Graphviz-Software, `dot`-Binary).

Format der Eingabedatei (siehe diagrams.txt):
    # ==name==
    digraph Name { ... }

    # ==anderer_name==
    digraph AndererName { ... }

Verwendung:
    python render_diagrams.py                    # rendert alle Diagramme als PNG
    python render_diagrams.py spielablauf         # nur dieses eine Diagramm
    python render_diagrams.py --format svg        # als SVG statt PNG
    python render_diagrams.py --input pfad.txt    # andere Eingabedatei
    python render_diagrams.py --no-open           # nicht automatisch oeffnen

Voraussetzung: Graphviz-Software installiert (nicht nur `pip install graphviz`
-- das ist nur der Python-Wrapper). Falls `dot` nicht gefunden wird: Terminal
neu starten (PATH wird nach der Installation erst in einer neuen Shell-Sitzung
aktualisiert) oder https://graphviz.org/download/ pruefen.
"""
import argparse
import os
import re
import sys
import webbrowser
from pathlib import Path

import graphviz


def parse_diagrams(text: str) -> dict[str, str]:
    """Teilt die Eingabedatei an `# ==name==`-Markierungen in einzelne DOT-Graphen."""
    parts = re.split(r"^# ==(.+?)==\s*$", text, flags=re.MULTILINE)
    # parts[0] ist Text vor der ersten Markierung (Kommentare o.ae.) -- verwerfen.
    diagrams = {}
    for i in range(1, len(parts), 2):
        name = parts[i].strip()
        dot_source = parts[i + 1].strip()
        diagrams[name] = dot_source
    return diagrams


def render(name: str, dot_source: str, out_dir: Path, fmt: str) -> Path:
    src = graphviz.Source(dot_source, filename=name, directory=str(out_dir), format=fmt)
    rendered = src.render(cleanup=True)  # schreibt <name>.<fmt>, loescht die .gv-Zwischendatei
    return Path(rendered)


def open_file(path: Path) -> None:
    if sys.platform == "win32":
        os.startfile(path)  # noqa: S606 -- lokale, selbst erzeugte Datei
    else:
        webbrowser.open(path.as_uri())


def main():
    ap = argparse.ArgumentParser(description="Rendert Graphviz-DOT-Diagramme als PNG/SVG")
    ap.add_argument("name", nargs="?", default=None, help="Nur dieses Diagramm rendern (Standard: alle)")
    ap.add_argument(
        "--input",
        default=str(Path(__file__).parent / "diagrams.txt"),
        help="Eingabedatei mit DOT-Quellen (Standard: diagrams.txt neben diesem Skript)",
    )
    ap.add_argument("--format", default="png", choices=["png", "svg", "pdf"], help="Ausgabeformat (Standard: png)")
    ap.add_argument("--no-open", action="store_true", help="Nicht automatisch oeffnen")
    args = ap.parse_args()

    input_path = Path(args.input)
    diagrams = parse_diagrams(input_path.read_text(encoding="utf-8"))
    if not diagrams:
        raise SystemExit(f"Keine Diagramme in {input_path} gefunden (erwartet '# ==name==' Markierungen).")

    names = [args.name] if args.name else list(diagrams.keys())
    for name in names:
        if name not in diagrams:
            print(f"Warnung: '{name}' nicht gefunden. Verfuegbar: {', '.join(diagrams)}")
            continue
        try:
            out_path = render(name, diagrams[name], input_path.parent, args.format)
        except graphviz.backend.ExecutableNotFound:
            raise SystemExit(
                "Graphviz-'dot'-Binary nicht gefunden. Falls gerade erst installiert: "
                "Terminal neu starten (PATH wird erst in einer neuen Shell-Sitzung aktiv)."
            )
        print(f"Erzeugt: {name} -> {out_path}")
        if not args.no_open:
            open_file(out_path)


if __name__ == "__main__":
    main()
