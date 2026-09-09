# -*- coding: utf-8 -*-
"""Erzeugt `docs/tools_index.md`: was liegt in tools/, wozu, und wird es benutzt?

ANLASS (Nutzer 2026-09-09): *"da liegt soviel Zeug herum, wo ich nicht abschaetzen
kann, ob es Leichen sind oder ob es wirklich gebraucht wird."* Eine von Hand
gepflegte Liste beantwortet das nicht -- sie sagt, was jemand mal aufgeschrieben
hat, nicht was der Baum heute tut. Deshalb GENERIERT, mit einem Kriterium, das
nachpruefbar ist: wer nennt die Datei, und ruft er sie auf oder erwaehnt er sie nur?

DIE EINSTUFUNG ist eine Verwendungs-Evidenz, KEIN Loeschvorschlag:

  WIRED        ein anderes Skript, ein Test, ein Haken, ein Skill oder CLAUDE.md
               RUFT die Datei auf (Nennung ausserhalb eines Kommentars).
  DOCUMENTED   nur docs/ oder ein Code-KOMMENTAR nennt sie: Werkzeug mit Anleitung
               oder Quellenangabe, nichts ruft es automatisch. Normalfall fuer Sonden.
  CHRONICLE    nur evaluations/ nennt sie, also ein Messbericht oder eine Prereg.
               Typisch fuer Einmal-Skripte, deren Lauf vorbei ist.
  UNNAMED      niemand nennt sie ausser ihr selbst. Kandidat fuer eine Ruecksprache
               -- oder ein Werkzeug, das man von Hand aufruft und nie zitiert hat.

Absichtlich NICHT automatisiert: das Loeschen. "Unnamed" heisst nicht "tot" (ein
Werkzeug, das man von Hand aufruft, steht nirgends), und CLAUDE.md verlangt fuer
jede Loeschung eine pfadgenaue Freigabe. Der Index liefert die Vorlage dafuer,
nicht die Entscheidung.

Aufruf:
    python -X utf8 tools/generate_tools_index.py
    python -X utf8 tools/generate_tools_index.py --check   # nur pruefen (Exit 1 bei Drift)
"""
from __future__ import annotations

import argparse
import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "tools_index.md"
SUFFIXES = (".py", ".sh", ".ps1")
SCANNED_SUFFIXES = (".py", ".sh", ".ps1", ".rs", ".md", ".json", ".yml", ".yaml", ".txt", "")
CODE_SUFFIXES = (".py", ".sh", ".ps1", ".rs")
# Verzeichnisse, die beim Suchen nach Nennungen nicht zaehlen.
SKIP_DIRS = {".git", "target", "__pycache__", "node_modules", ".pytest_cache",
             "dist", "build", "data", "models", "logs", "venv", ".venv"}
COMMENT_STARTS = ("#", "//", "*", "///")

CLASSES = {
    "WIRED": "Code, Test, Haken, Skill oder CLAUDE.md RUFT es auf (Nennung ausserhalb "
             "eines Kommentars). Haengt im Betrieb.",
    "DOCUMENTED": "nur `docs/` oder ein Code-KOMMENTAR nennt es: Werkzeug mit Anleitung "
                  "oder Quellenangabe, nichts ruft es automatisch. Normalfall fuer Sonden.",
    "CHRONICLE": "nur `evaluations/` nennt es, also ein Messbericht oder eine Prereg. "
                 "Typisch fuer Einmal-Skripte, deren Lauf vorbei ist.",
    "UNNAMED": "niemand nennt es ausser ihm selbst. Kandidat fuer eine Ruecksprache -- "
               "aber nicht automatisch tot: ein Werkzeug, das man von Hand aufruft, "
               "steht nirgends.",
}
BUCKET_LABELS = {"call": "Aufruf", "comment": "Kommentar", "rules": "Regeln",
                 "docs": "docs", "evaluations": "evaluations"}


def purpose(path: pathlib.Path) -> str:
    """Erste inhaltliche Zeile: Modul-Docstring oder Kopfkommentar."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    if path.suffix == ".py":
        match = re.search(r'^\s*(?:#[^\n]*\n)*\s*(?:r?"""|\'\'\')(.*?)(?:"""|\'\'\')',
                          text, re.S)
        if match:
            for line in match.group(1).strip().splitlines():
                if line.strip():
                    return line.strip()
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#!") or stripped.startswith("<#") or not stripped:
            continue
        if stripped.startswith("#"):
            stripped = stripped.lstrip("#").strip()
            if stripped and not stripped.startswith("-*-"):
                return stripped
        elif stripped.startswith(".SYNOPSIS"):
            continue
        else:
            break
    return ""


def collect_files() -> list[pathlib.Path]:
    files = []
    for directory, subdirs, names in os.walk(ROOT / "tools"):
        subdirs[:] = [d for d in subdirs if d not in SKIP_DIRS]
        for name in names:
            path = pathlib.Path(directory) / name
            if path.suffix in SUFFIXES or (path.parent.name == "hooks" and not path.suffix):
                files.append(path)
    return sorted(files, key=lambda p: str(p.relative_to(ROOT)).replace("\\", "/"))


def bucket_of(path: pathlib.Path, rel: str) -> str:
    if rel.startswith("evaluations/"):
        return "evaluations"
    if rel.startswith("docs/"):
        return "docs"
    if rel == "CLAUDE.md" or rel.startswith(".claude/"):
        return "rules"
    if path.suffix in CODE_SUFFIXES or rel.startswith("tools/hooks/"):
        return "code"
    return "docs"


def all_mentions(files: list[pathlib.Path]) -> dict[str, dict[str, int]]:
    """EIN Durchgang ueber den Baum fuer ALLE Werkzeuge.

    Die naive Fassung lief je Werkzeug einmal ueber den Baum -- 90 Werkzeuge mal
    tausende Dateien, und der Lauf war nach zwei Minuten nicht fertig. Gezaehlt
    wird jetzt umgekehrt: jede Datei wird EINMAL gelesen und gegen alle
    Werkzeugnamen geprueft.
    """
    by_name = {p.name: p for p in files}
    hits = {name: dict.fromkeys(BUCKET_LABELS, 0) for name in by_name}
    for directory, subdirs, names in os.walk(ROOT):
        subdirs[:] = [d for d in subdirs if d not in SKIP_DIRS]
        for name in names:
            path = pathlib.Path(directory) / name
            if path.suffix not in SCANNED_SUFFIXES:
                continue
            # Die erzeugte Datei selbst zaehlt NICHT: sie listet jedes Werkzeug,
            # also haette nach dem ersten Lauf jedes eine docs-Nennung und die
            # Stufen CHRONICLE und UNNAMED waeren fuer immer leer. Beim ersten
            # Durchgang nicht aufgefallen, beim zweiten sofort.
            if path == OUT:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            rel = str(path.relative_to(ROOT)).replace("\\", "/")
            bucket = bucket_of(path, rel)
            lines = text.splitlines()
            for tool_name in by_name:
                if tool_name not in text or by_name[tool_name] == path:
                    continue
                if bucket != "code":
                    hits[tool_name][bucket] += 1
                    continue
                # In CODE zaehlt nur, was AUFRUFT. Eine Nennung im Kommentar ist
                # eine Quellenangabe, kein Verdrahten -- ohne die Unterscheidung
                # sah fast alles verdrahtet aus, auch abgeschlossene Sonden.
                calls = any(tool_name in line
                            and not line.lstrip().startswith(COMMENT_STARTS)
                            for line in lines)
                hits[tool_name]["call" if calls else "comment"] += 1
    return hits


def classify(hits: dict[str, int]) -> str:
    if hits["call"] or hits["rules"]:
        return "WIRED"
    if hits["docs"] or hits["comment"]:
        return "DOCUMENTED"
    if hits["evaluations"]:
        return "CHRONICLE"
    return "UNNAMED"


def last_commit(rel: str) -> str:
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ad", "--date=short", "--", rel],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
        return result.stdout.strip() or "-"
    except OSError:
        return "-"


def build() -> str:
    files = collect_files()
    mentions = all_mentions(files)
    rows = []
    for path in files:
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        hits = mentions[path.name]
        text = purpose(path)
        rows.append({"rel": rel, "purpose": text or "(kein Kopfkommentar)",
                     "cls": classify(hits), "hits": hits, "date": last_commit(rel)})
    order = list(CLASSES)
    rows.sort(key=lambda r: (order.index(r["cls"]), r["rel"]))
    counts = {c: sum(1 for r in rows if r["cls"] == c) for c in order}

    out = ["# Werkzeug-Index (GENERIERT)", "",
           "**Diese Datei wird erzeugt, nicht von Hand gepflegt:**",
           "`python -X utf8 tools/generate_tools_index.py`. Wer sie editiert, verliert die",
           "Aenderung beim naechsten Lauf; `--check` meldet Drift.", "",
           "Sie beantwortet die Frage, die eine gepflegte Liste nicht beantworten kann:",
           "**wird das Ding noch gebraucht?** Das Kriterium ist nachpruefbar -- wer nennt die",
           "Datei, und ruft er sie auf oder erwaehnt er sie nur? -- und ausdruecklich eine",
           "Verwendungs-Evidenz, KEIN Loeschvorschlag.", "",
           "| Stufe | Bedeutung |", "| --- | --- |"]
    out += [f"| **{name}** | {text} |" for name, text in CLASSES.items()]
    out += ["",
            f"**Stand: {len(rows)} Dateien** = "
            + " + ".join(f"{counts[c]} {c}" for c in order) + ".", ""]
    for cls in order:
        part = [r for r in rows if r["cls"] == cls]
        if not part:
            continue
        out += [f"## {cls} ({len(part)})", "",
                "| Datei | Zweck | Genannt von | Letzter Commit |", "| --- | --- | --- | --- |"]
        for row in part:
            sources = ", ".join(f"{BUCKET_LABELS[k]} {v}"
                                for k, v in row["hits"].items() if v) or "niemand"
            short = row["purpose"].replace("|", "/")
            if len(short) > 150:
                short = short[:147] + "..."
            out.append(f"| `{row['rel']}` | {short} | {sources} | {row['date']} |")
        out.append("")
    return "\n".join(out) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true",
                        help="nur pruefen, ob die Datei aktuell ist (Exit 1 bei Drift)")
    args = parser.parse_args()
    text = build()
    if args.check:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current.replace("\r\n", "\n") != text:
            print(f"{OUT} ist nicht aktuell -- `python -X utf8 tools/generate_tools_index.py`",
                  file=sys.stderr)
            return 1
        print(f"{OUT} ist aktuell.")
        return 0
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"{OUT} geschrieben ({text.count(chr(10))} Zeilen).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
