"""
tools/check_conventions.py -- Konventions-Linter (Baustein A5).

Siehe docs/DESIGN_conventions_as_checks.md, Abschnitt
"A5 Konventions-Linter" fuer die Herleitung. Laeuft im `pre-commit`-Haken
(tools/hooks/pre-commit), Budget < 3 s -- daher NUR textnahe Pruefungen:
keine Compilierung, kein Netz, keine Korpus-/Modell-Dateien.

Fuenf harte Regeln, jede mit eigener Fehlermeldung (Konsequenz + Ausweg),
plus eine Warn-Regel 5 (stille Test-Skips, nur stderr -- Heuristik zu grob
fuer einen Commit-Blocker, siehe dortiger Kommentar):
  1. Datei-Groessen-RATSCHE   -- tools/size_baseline.json, Schwelle 40 KB,
                                  rot nur bei Wachstum > +2% einer bereits
                                  zu grossen Datei (kein Refactoring-Zwang).
  2. Doku-Sprachkonvention    -- README.md englisch, STATUS.md/history.md
                                  deutsch (Stopwort-Mehrheit, grosszuegig).
  3. Keine neuen `#NN`        -- jede `Task #NN` muss in
                                  evaluations/TASK_NUMBER_REGISTRY.md
                                  als bekannte Nummer stehen (Serie ist seit
                                  2026-08-09 geschlossen, siehe dort).
  4. Prereg-Index-Konsistenz  -- evaluations/PREREG_*.md <-> PREREG_INDEX.md
                                  in beide Richtungen, plus Zaehler in den
                                  Abschnitts-Ueberschriften. Seit 2026-08-15
                                  (Architektur-Fahrplan Punkt 1) zusaetzlich:
                                  jede PREREG_*.md braucht einen parsebaren
                                  Status-Kopf in Zeile 1, und der generierte
                                  Tabellenteil des Index muss dem Output von
                                  tools/generate_prereg_index.py entsprechen.
  6. Knopf-Doku aktuell       -- docs/knobs.md ist GENERIERT aus
                                  engine/src/knob_registry.rs; wer die
                                  Registratur aendert, zieht die Doku im
                                  selben Commit nach (gleiche Bauform wie
                                  Regel 4, Generator per Import).

CLI:
    python tools/check_conventions.py                    # ganzes Repo (manueller Lauf)
    python tools/check_conventions.py --staged            # nur gestagte Dateien (Hook-Modus)
    python tools/check_conventions.py --update-size-baseline
        # Regel 1: tools/size_baseline.json aus dem AKTUELLEN Ist-Stand neu schreiben.
        # Nur manuell aufrufen, wenn ein Wachstum ueber die 40-KB-Schwelle bewusst
        # akzeptiert wird -- kein automatischer Teil von --staged oder dem Default-Lauf.

Exit 0 = alle Regeln gruen. Exit 1 = mindestens ein Verstoss (Details auf stderr).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SIZE_BASELINE_PATH = REPO_ROOT / "tools" / "size_baseline.json"
TASK_REGISTRY_PATH = REPO_ROOT / "evaluations" / "TASK_NUMBER_REGISTRY.md"
PREREG_INDEX_PATH = REPO_ROOT / "evaluations" / "PREREG_INDEX.md"
PREREG_DIR = REPO_ROOT / "evaluations"
KNOB_REGISTRY_PATH = REPO_ROOT / "engine" / "src" / "knob_registry.rs"
KNOB_DOCS_PATH = REPO_ROOT / "docs" / "knobs.md"

# Ab welcher Groesse eine Datei ueberhaupt geratscht wird -- unterhalb darf sie
# frei wachsen. Der Wert ist GESETZT, nicht hergeleitet: das Design-Dok begruendet
# die RATSCHE (statt einer Obergrenze, die "am ersten Tag auf vier Dateien rot"
# waere), nennt aber keine 40 KB. Fuer eine Ratsche ist das vertretbar, weil die
# Schwelle nur bestimmt, ab wann Wachstum beobachtet wird -- nicht, was erlaubt
# ist. Stand 2026-08-11 liegen SECHS Dateien darueber (neural_net.py 161 KB,
# train.py 134, server.py 74, analyze_game_log.py 55, dome_split_diagnosis.py 45,
# self_play.py 41), die im Dok genannten "vier" stimmen also nicht mehr.
SIZE_THRESHOLD_BYTES = 40 * 1024
SIZE_GROWTH_TOLERANCE = 1.02  # +2% Rauschtoleranz -- blosses Reformatieren darf nicht rot werden


# --------------------------------------------------------------------------
# Git-Hilfsfunktionen (fuer --staged)
# --------------------------------------------------------------------------

def get_staged_files() -> list[str]:
    """Pfade (repo-relativ, '/'-getrennt) aller gestagten Added/Copied/Modified/Renamed-Dateien."""
    out = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        cwd=REPO_ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return [line.strip() for line in out.stdout.splitlines() if line.strip()]


def get_staged_content(relpath: str) -> str | None:
    """Liest den GESTAGTEN Inhalt (Index-Blob, nicht den Working-Tree-Stand) einer Datei."""
    result = subprocess.run(
        ["git", "show", f":{relpath}"],
        cwd=REPO_ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode != 0:
        return None
    return result.stdout


# --------------------------------------------------------------------------
# Regel 1: Datei-Groessen-Ratsche
# --------------------------------------------------------------------------

def _size_scope() -> list[Path]:
    """Nur *.py im Repo-Root, engine/py/ und tools/ (nicht rekursiv) -- wie im Design-Dok festgelegt."""
    scope = []
    scope += sorted(REPO_ROOT.glob("*.py"))
    scope += sorted((REPO_ROOT / "engine" / "py").glob("*.py"))
    scope += sorted((REPO_ROOT / "tools").glob("*.py"))
    return scope


def update_size_baseline() -> None:
    baseline = {p.relative_to(REPO_ROOT).as_posix(): p.stat().st_size for p in _size_scope()}
    SIZE_BASELINE_PATH.write_text(
        json.dumps(baseline, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Basislinie neu geschrieben: {SIZE_BASELINE_PATH} ({len(baseline)} Dateien).")


def _size_in_head(rel: str) -> int | None:
    """Groesse der Datei im letzten Commit, oder None wenn nicht ermittelbar.

    Gebraucht fuer die Reduktions-Ausnahme unten: die Basislinie allein kann
    nicht sehen, ob eine Aenderung eine Datei VERKLEINERT.
    """
    try:
        out = subprocess.run(
            ["git", "cat-file", "-s", f"HEAD:{rel}"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=False,
        )
        return int(out.stdout.strip()) if out.returncode == 0 else None
    except Exception:
        return None

def check_file_size_ratchet(staged_only: bool, staged_files: set[str]) -> list[str]:
    if not SIZE_BASELINE_PATH.exists():
        return [
            "REGEL 1 (Datei-Groessen-Ratsche): tools/size_baseline.json fehlt.\n"
            "  Konsequenz: die Ratsche kann nicht pruefen, ob eine bereits grosse Datei weiter waechst --\n"
            "  ungebremstes Wachstum der grossen Python-Module bliebe unsichtbar.\n"
            "  Ausweg: einmalig anlegen mit `python tools/check_conventions.py --update-size-baseline`."
        ]
    baseline = json.loads(SIZE_BASELINE_PATH.read_text(encoding="utf-8"))
    violations = []
    for p in _size_scope():
        rel = p.relative_to(REPO_ROOT).as_posix()
        if staged_only and rel not in staged_files:
            continue
        if rel not in baseline:
            continue  # neue Datei ohne Basislinie -- Ratsche greift erst nach dem naechsten --update-size-baseline
        base_bytes = baseline[rel]
        cur_bytes = p.stat().st_size
        # REDUKTIONS-AUSNAHME (2026-08-10, aus einem echten Vorfall): die Ratsche
        # blockierte einen Commit, der `engine/py/neural_net.py` VERKLEINERT hat --
        # die Datei lag nur deshalb ueber der Basislinie, weil ein FRUEHERER Commit
        # sie hatte wachsen lassen, ohne die Basislinie nachzuziehen. Eine Ratsche
        # soll Wachstum bremsen, nicht Aufraeumen bestrafen. Wer die Datei
        # gegenueber HEAD kleiner macht, kommt durch; die Basislinie bleibt
        # unveraendert stehen, die Ratsche greift also beim naechsten Wachstum
        # weiter gegen den alten Wert.
        head_bytes = _size_in_head(rel)
        if head_bytes is not None and cur_bytes <= head_bytes:
            continue
        if base_bytes > SIZE_THRESHOLD_BYTES and cur_bytes > base_bytes * SIZE_GROWTH_TOLERANCE:
            growth_pct = (cur_bytes / base_bytes - 1) * 100
            violations.append(
                f"REGEL 1 (Datei-Groessen-Ratsche): {rel} ist von {base_bytes / 1024:.1f} KB auf "
                f"{cur_bytes / 1024:.1f} KB gewachsen (+{growth_pct:.1f}%, mehr als die 2%-Rauschtoleranz) "
                f"-- die Basislinie lag bereits ueber der {SIZE_THRESHOLD_BYTES / 1024:.0f}-KB-Schwelle.\n"
                "  Konsequenz: diese Datei verstoesst schon gegen die Modularitaetsregel aus CLAUDE.md; "
                "jedes weitere Wachstum vertieft einen Refactoring-Rueckstand, den niemand beauftragt hat.\n"
                f"  Ausweg: (a) die Aenderung zuschneiden, bis die Datei wieder unter "
                f"{base_bytes * SIZE_GROWTH_TOLERANCE / 1024:.1f} KB liegt (z.B. Funktionsblock in ein "
                "neues Modul auslagern), oder (b) falls das Wachstum bewusst und reviewt ist: Basislinie neu "
                "legen mit `python tools/check_conventions.py --update-size-baseline` und "
                "tools/size_baseline.json mitcommitten."
            )
        elif base_bytes <= SIZE_THRESHOLD_BYTES < cur_bytes:
            # Kein Regelverstoss -- die Datei durfte wachsen, bis sie die Schwelle riss (Design-Dok A5).
            # Informativ, damit die Ratsche ab jetzt tatsaechlich greift.
            print(
                f"[Hinweis] {rel} hat die {SIZE_THRESHOLD_BYTES / 1024:.0f}-KB-Schwelle erstmals "
                f"ueberschritten ({cur_bytes / 1024:.1f} KB). Kein Fehler, aber ab jetzt WIRD die Ratsche "
                "bei weiterem Wachstum greifen -- falls dieser Stand so bleiben soll, jetzt per "
                "`python tools/check_conventions.py --update-size-baseline` als neue Basis eintragen.",
                file=sys.stderr,
            )
    return violations


# --------------------------------------------------------------------------
# Regel 2: Doku-Sprachkonvention
# --------------------------------------------------------------------------

DE_STOPWORDS = {
    "der", "die", "das", "und", "nicht", "werden", "wird", "ist", "sind", "war", "waren",
    "sich", "mit", "auch", "eine", "einen", "einer", "eines", "fuer", "für", "von", "den",
    "dem", "des", "ein", "im", "am", "auf", "zum", "zur", "wurde", "wurden", "als", "aber",
    "oder", "kein", "keine", "noch", "schon", "nur", "bei", "aus", "nach", "vor", "durch",
}
EN_STOPWORDS = {
    "the", "and", "of", "is", "not", "to", "in", "that", "this", "for", "with", "are",
    "was", "were", "be", "been", "by", "on", "as", "it", "from", "an", "but", "or", "no",
    "at", "into", "than", "then", "which", "its", "if", "when", "each",
}
MIN_STOPWORD_SAMPLE = 20  # weniger Stopwoerter -> Heuristik unzuverlaessig, ueberspringen statt raten

DOC_LANGUAGE_RULES = [
    # (repo-relativer Pfad, Klartext-Label, erwartete Sprache "en"/"de")
    ("README.md", "englisch", "en"),
    ("evaluations/STATUS.md", "deutsch", "de"),
    ("archive/history.md", "deutsch", "de"),
]


def _lang_stopword_counts(text: str) -> tuple[int, int]:
    words = re.findall(r"[A-Za-zÄÖÜäöüß]+", text.lower())
    de = sum(1 for w in words if w in DE_STOPWORDS)
    en = sum(1 for w in words if w in EN_STOPWORDS)
    return de, en


def check_doc_language(staged_only: bool, staged_files: set[str]) -> list[str]:
    violations = []
    for relpath, label, expected in DOC_LANGUAGE_RULES:
        if staged_only and relpath not in staged_files:
            continue
        if staged_only:
            text = get_staged_content(relpath)
        else:
            path = REPO_ROOT / relpath
            text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else None
        if text is None:
            continue
        de, en = _lang_stopword_counts(text)
        if de + en < MIN_STOPWORD_SAMPLE:
            continue  # zu wenig Fliesstext fuer eine verlaessliche Aussage
        if expected == "en" and de > en:
            violations.append(
                f"REGEL 2 (Doku-Sprachkonvention): {relpath} soll {label} sein, aber deutsche "
                f"Stopwoerter ({de}) uebertreffen englische ({en}) im Fliesstext.\n"
                "  Konsequenz: das Projekt haelt README.md bewusst englisch (siehe CLAUDE.md / "
                "MEMORY 'Docs language convention') -- ein ueberwiegend deutscher Text hier verfehlt "
                "genau die Leser, fuer die README.md gedacht ist.\n"
                "  Ausweg: den Abschnitt ins Englische zuruecksetzen. Ein einzelnes deutsches Zitat "
                "faellt nicht unter diese Regel (grosszuegige Schwelle) -- rot wird es erst, wenn "
                "Deutsch tatsaechlich ueberwiegt."
            )
        elif expected == "de" and en > de:
            violations.append(
                f"REGEL 2 (Doku-Sprachkonvention): {relpath} soll {label} sein, aber englische "
                f"Stopwoerter ({en}) uebertreffen deutsche ({de}) im Fliesstext.\n"
                "  Konsequenz: STATUS.md/history.md sind die deutschsprachige Betriebsdoku (siehe "
                "CLAUDE.md / MEMORY 'Docs language convention'); ein ueberwiegend englischer Abschnitt "
                "bricht mit dieser Konvention und macht die Datei fuer den Rest inkonsistent.\n"
                "  Ausweg: den Abschnitt ins Deutsche zuruecksetzen. Einzelne englische Fachbegriffe/"
                "Zitate (z.B. Codebezeichner) loesen die Regel nicht aus -- rot wird es erst, wenn "
                "Englisch tatsaechlich ueberwiegt."
            )
    return violations


# --------------------------------------------------------------------------
# Regel 3: Keine neuen `#NN`
# --------------------------------------------------------------------------

# Nur die Form "Task #NN" / "Task-#NN" (auch in Ueberschriften "## Task #NN: ...") zaehlt als
# Kandidat. Das ist bewusst ENGER als der blosse Fund von "#\d+[a-z]?" irgendwo im Text --
# genau dieses engere Muster ist es, das echte Task-Referenzen im Bestand von Farbcodes
# (#003366), Markdown-Anker-Links ([...](#42-abschnitt)) und blossen Zahlen in Kommentaren/
# Partie-Logs unterscheidet (siehe TASK_NUMBER_REGISTRY.md, Abschnitt "Filter-Verfahren" /
# "Verworfen"). Zusaetzlich auf 1-2 Ziffern begrenzt: alle bisher vergebenen Nummern liegen
# zwischen 5 und 99 -- das schliesst nebenbei auch lange externe Referenzen (GitHub-Issues wie
# #1480) und rein numerische Hex-Farben (#123456) aus. Bei mehr als 99 Nummern muesste diese
# Grenze erweitert werden.
TASK_NUMBER_PATTERN = re.compile(r"\bTask[\s-]*#(\d{1,2}[a-zA-Z]?)\b", re.IGNORECASE)

# Derselbe Dateiumfang wie im "Filter-Verfahren"-Kopf der Registratur (Vollstaendigkeits-Scan
# im manuellen ganzes-Repo-Lauf). Im --staged-Modus werden stattdessen genau die gestagten
# Dateien geprueft, unabhaengig vom Typ.
WHOLE_REPO_SCAN_GLOBS = [
    "archive/history.md",
    "evaluations/*.md",
    "docs/*.md",
    "README.md",
    "CLAUDE.md",
    "engine/src/*.rs",
    "engine/py/neural_net.py",
    "train.py",
    "self_play.py",
    "server.py",
    "tools/*.py",
]

# #99 ist dokumentiert (TASK_NUMBER_REGISTRY.md, Abschnitt "REPARATUR 2026-08-09": der
# Rust-Block in engine/src/tiling_solver.rs wurde dorthin umnummeriert), steht aber nicht als
# eigene Zeile in der Hauptregistratur-Tabelle. Bei weiteren Reparaturen dieser Art hier ergaenzen.
KNOWN_TASK_NUMBERS_OUTSIDE_TABLE = {"99"}


def _known_task_numbers() -> set[str]:
    known: set[str] = set()
    if TASK_REGISTRY_PATH.exists():
        text = TASK_REGISTRY_PATH.read_text(encoding="utf-8")
        # Hauptregistratur-Tabelle: "| 35b | Thema | Status | Beleg |" oder "| 15 (A/B) | ..."
        for m in re.finditer(r"^\|\s*(\d{1,2}[a-zA-Z]?)\b", text, re.MULTILINE):
            known.add(m.group(1).lower())
    known |= KNOWN_TASK_NUMBERS_OUTSIDE_TABLE
    return known


def _is_known_number(token: str, known: set[str]) -> bool:
    token = token.lower()
    if token in known:
        return True
    genitive = re.match(r"^(\d{1,2})s$", token)  # z.B. "80s" -> Basisnummer 80 (Genitiv-Normalisierung)
    return bool(genitive and genitive.group(1) in known)


def check_no_new_task_numbers(staged_only: bool, staged_files: set[str]) -> list[str]:
    known = _known_task_numbers()
    if staged_only:
        targets = sorted(staged_files)
    else:
        found: set[str] = set()
        for pattern in WHOLE_REPO_SCAN_GLOBS:
            found.update(p.relative_to(REPO_ROOT).as_posix() for p in REPO_ROOT.glob(pattern) if p.is_file())
        targets = sorted(found)

    violations = []
    for rel in targets:
        if rel == "evaluations/TASK_NUMBER_REGISTRY.md":
            continue  # die Registratur selbst dokumentiert Alt-Nummern -- kein Fund, keine Pruefung
        if staged_only:
            text = get_staged_content(rel)
        else:
            p = REPO_ROOT / rel
            text = p.read_text(encoding="utf-8", errors="replace") if p.exists() else None
        if text is None:
            continue
        reported: set[str] = set()
        for m in TASK_NUMBER_PATTERN.finditer(text):
            token = m.group(1)
            if token in reported or _is_known_number(token, known):
                continue
            reported.add(token)
            line_no = text.count("\n", 0, m.start()) + 1
            violations.append(
                f"REGEL 3 (Keine neuen #NN): {rel}:{line_no} verwendet `Task #{token}`, das in "
                "evaluations/TASK_NUMBER_REGISTRY.md nicht als bekannte Nummer vorkommt.\n"
                "  Konsequenz: die #NN-Serie ist seit 2026-08-09 geschlossen (siehe Registratur-Kopf / "
                "PREREG_INDEX.md Abschnitt NAMENSKONVENTION) -- eine neue Nummer hier kann eine Luecke "
                "belegen, die absichtlich frei ist, oder eine Doppelbelegung wie den historischen "
                "#33-Fall erzeugen, ohne dass es jemand merkt.\n"
                "  Ausweg: keine neue #NN vergeben. Fuer neue Arbeit eine "
                "evaluations/PREREG_<slug>.md anlegen und DIESE als Kennung referenzieren. Falls sich "
                "die Stelle auf einen echten Alt-Task bezieht, der der Registratur nur fehlt: die "
                "Registratur nachpflegen statt eine Nummer neu zu vergeben."
            )
    return violations


# --------------------------------------------------------------------------
# Regel 4: Prereg-Index-Konsistenz
# --------------------------------------------------------------------------

SECTION_HEADER_PATTERN = re.compile(r"^## (OFFEN|ENTSCHIEDEN|UEBERHOLT) \((\d+)\)\s*$", re.MULTILINE)
INDEXED_FILENAME_PATTERN = re.compile(r"`(PREREG_[A-Za-z0-9_]+\.md)`")
TABLE_ROW_PATTERN = re.compile(r"^\|\s*`PREREG_", re.MULTILINE)


def check_prereg_index_consistency(staged_only: bool, staged_files: set[str]) -> list[str]:
    disk_files = {p.name for p in PREREG_DIR.glob("PREREG_*.md") if p.name != "PREREG_INDEX.md"}
    relevant = {"evaluations/PREREG_INDEX.md"} | {f"evaluations/{name}" for name in disk_files}
    if staged_only and not (relevant & staged_files):
        return []  # dieser Commit ruehrt weder den Index noch eine PREREG-Datei an

    if not PREREG_INDEX_PATH.exists():
        return [
            "REGEL 4 (Prereg-Index-Konsistenz): evaluations/PREREG_INDEX.md fehlt.\n"
            "  Konsequenz: niemand kann OFFEN von ENTSCHIEDEN unterscheiden, ohne jede PREREG_*.md "
            "einzeln zu oeffnen -- genau das Problem, das der Index beheben sollte.\n"
            "  Ausweg: Index wiederherstellen (git-Historie) oder neu anlegen."
        ]

    index_text = PREREG_INDEX_PATH.read_text(encoding="utf-8")
    indexed_files = set(INDEXED_FILENAME_PATTERN.findall(index_text))
    missing_from_index = sorted(disk_files - indexed_files)
    stale_in_index = sorted(indexed_files - disk_files)

    violations = []
    if missing_from_index:
        violations.append(
            "REGEL 4 (Prereg-Index-Konsistenz): diese Dateien existieren in evaluations/, fehlen aber "
            f"in PREREG_INDEX.md: {', '.join(missing_from_index)}.\n"
            "  Konsequenz: ein Leser haelt diese Vorregistrierungen faelschlich fuer nicht erfasst -- "
            "genau das Problem, das der Index laut seinem eigenen Kopf beheben sollte.\n"
            "  Ausweg: pro Datei eine Zeile in OFFEN/ENTSCHIEDEN/UEBERHOLT ergaenzen (Frage + "
            "Belegstelle) und den Zaehler in der jeweiligen Abschnitts-Ueberschrift um 1 erhoehen. Ist "
            "eine Datei absichtlich (noch) ausgenommen (wie aktuell PREREG_v22_window.md laut "
            "Kopf-Hinweis in PREREG_INDEX.md), dies im Kopf der Index-Datei explizit vermerken statt "
            "sie kommentarlos wegzulassen."
        )
    if stale_in_index:
        violations.append(
            "REGEL 4 (Prereg-Index-Konsistenz): PREREG_INDEX.md referenziert Dateien, die nicht (mehr) "
            f"in evaluations/ existieren: {', '.join(stale_in_index)}.\n"
            "  Konsequenz: der Index verweist auf eine Geisterdatei -- ein Link ins Leere.\n"
            "  Ausweg: Zeile aus der Tabelle entfernen und den Abschnitts-Zaehler um 1 senken; falls die "
            "Datei nur umbenannt wurde, stattdessen den neuen Namen eintragen."
        )

    # Seit 2026-08-15 (Architektur-Fahrplan Punkt 1): der Tabellenteil des
    # Index ist GENERIERT. Zwei zusaetzliche Pruefungen gegen den Generator
    # (tools/generate_prereg_index.py, per Import -- kein Subprozess, das
    # Hook-Budget von < 3 s bleibt eingehalten):
    #   (a) jede PREREG_*.md braucht einen parsebaren Status-Kopf in Zeile 1;
    #   (b) der Index muss byte-genau dem Generator-Output entsprechen.
    try:
        sys.path.insert(0, str(REPO_ROOT / "tools"))
        import generate_prereg_index as _gpi
        regenerated, unparsable = _gpi.regenerate_index_text(index_text)
    except ValueError as e:
        violations.append(
            f"REGEL 4 (Prereg-Index-Konsistenz): {e}\n"
            "  Konsequenz: ohne die BEGIN/END-Marker kann der Generator den Tabellenteil nicht\n"
            "  ersetzen -- der Index laeuft wieder in den von Hand gepflegten (und damit\n"
            "  veraltbaren) Zustand zurueck, der den 2026-08-12-Fehlauftrag ausgeloest hat.\n"
            "  Ausweg: Marker wiederherstellen (git-Historie von evaluations/PREREG_INDEX.md)."
        )
    else:
        if unparsable:
            violations.append(
                "REGEL 4 (Prereg-Index-Konsistenz): diese PREREG-Dateien haben keinen parsebaren "
                f"Status-Kopf in Zeile 1: {', '.join(unparsable)}.\n"
                "  Konsequenz: der Generator kann sie nicht in den Index aufnehmen -- fuer Leser "
                "sind sie unsichtbar oder veralten still, genau die Fehlerklasse des "
                "2026-08-12-Fehlauftrags.\n"
                "  Ausweg: als ERSTE Zeile der Datei einen Kommentar der Form\n"
                "  <!-- STATUS: OFFEN | Frage: <eine Zeile> | Beleg: <eine Zeile> -->\n"
                "  ergaenzen (Status: OFFEN/ENTSCHIEDEN/UEBERHOLT; kein `|` und kein `-->` in den "
                "Zellen), dann `python tools/generate_prereg_index.py` laufen lassen."
            )
        elif regenerated != index_text:
            violations.append(
                "REGEL 4 (Prereg-Index-Konsistenz): der generierte Tabellenteil von "
                "PREREG_INDEX.md entspricht nicht dem Generator-Output.\n"
                "  Konsequenz: Index und Status-Koepfe der Dateien laufen auseinander -- der Index "
                "wuerde wieder zur veraltbaren Handpflege, die den 2026-08-12-Fehlauftrag "
                "ausgeloest hat.\n"
                "  Ausweg: `python tools/generate_prereg_index.py` laufen lassen und "
                "evaluations/PREREG_INDEX.md mitcommitten (den Tabellenteil nie von Hand "
                "editieren; Statusaenderungen gehoeren in den Kopf der jeweiligen PREREG-Datei)."
            )

    sections = [(m.group(1), int(m.group(2)), m.end()) for m in SECTION_HEADER_PATTERN.finditer(index_text)]
    for name, claimed_count, body_start in sections:
        next_header = index_text.find("\n## ", body_start)
        body = index_text[body_start: next_header if next_header != -1 else len(index_text)]
        row_count = len(TABLE_ROW_PATTERN.findall(body))
        if row_count != claimed_count:
            violations.append(
                f"REGEL 4 (Prereg-Index-Konsistenz): Abschnitt '## {name} ({claimed_count})' nennt "
                f"{claimed_count}, die Tabelle darunter hat aber {row_count} Zeile(n).\n"
                "  Konsequenz: die Kopfzahl ist die schnelle Bestandskontrolle dieses Index -- eine "
                "falsche Zahl taeuscht eine Vollstaendigkeit vor, die nicht da ist.\n"
                f"  Ausweg: Ueberschrift auf '## {name} ({row_count})' korrigieren, oder die fehlende/"
                "ueberzaehlige Tabellenzeile ergaenzen bzw. entfernen -- je nachdem, was tatsaechlich stimmt."
            )
    return violations


# --------------------------------------------------------------------------
# Regel 5 (WARNUNG, kein Fehler): stille Test-Skips
# --------------------------------------------------------------------------

# Architektur-Fahrplan Punkt 2 (2026-08-15). Anlassfall: `load_test_net_for_
# gating` lud ein geloeschtes Modell, und die abhaengigen Tests bestanden
# LEER-GRUEN; das Inventar fand danach 17 weitere Tests, die wegen
# verschwundener Fixtures (v10_best/v18_best) nie liefen. Regel seither:
# eine fehlende Voraussetzung fuehrt zu `panic!`/`assert!` mit klarer
# Meldung oder zu `#[ignore = "Grund"]` -- nie zu stillem `return`.
#
# Die Heuristik hier ist bewusst grob (Textmuster, kein Parser) und darum
# nur eine WARNUNG auf stderr, kein Exit-1: sie sucht in Rust-Quellen nach
# einem fruehen `return` unmittelbar (<= 3 Zeilen) nach einer Zeile, die wie
# eine Voraussetzungs-Pruefung aussieht (`exists()`, `is_err()`,
# `let Ok(..) = .. else`, `uebersprungen`-Meldung). Treffer in Nicht-Test-
# Code sind moeglich (deshalb Warnung). Bekannter, BEGRUENDETER Bestands-
# Treffer (bleibt): net_mcts.rs `plate_shaping_disabled_search_matches_
# pre_task93_tree` -- Skip haengt an der Compile-Zeit-Konstante
# PLATE_SHAPING_ENABLED (Mess-Wheel-Arm), nicht an einer fehlenden Fixture;
# der Test soll in BEIDEN Toggle-Zustaenden gruen bleiben (dortiger
# Kommentar). Jede NEUE Warnung dagegen verdient einen Blick.
SILENT_SKIP_TRIGGER = re.compile(
    r"exists\(\)|\.is_err\(\)|let\s+Ok\(|uebersprungen|übersprungen", re.IGNORECASE
)
SILENT_SKIP_RETURN = re.compile(r"^\s*return(\s+Ok\(\(\)\))?\s*;\s*$")


def check_knob_docs_current(staged_only: bool, staged_files: set[str]) -> list[str]:
    """REGEL 6: docs/knobs.md muss dem Generator-Output entsprechen.

    ANLASS 2026-08-26: der Waechter-Test in `knob_registry.rs` erzwingt, dass
    jeder Knopf im Code REGISTRIERT ist -- aber nichts erzwang, dass die
    daraus GENERIERTE Tabelle mitwaechst. Beim Nachtragen von
    MOSAIC_IGNORE_POLICY_TARGET_VALID und MOSAIC_VAL_POOL war docs/knobs.md
    prompt veraltet, und eine veraltete Knopf-Tabelle ist genau die Sorte
    plausibler Zweitquelle, gegen die STATUS.md-Regel und REGEL 0 gebaut sind.

    Bauform wie Regel 4: der Generator wird IMPORTIERT (kein Subprozess), das
    Hook-Budget von < 3 s bleibt eingehalten. Quelle ist der rs-Parse, nicht
    das Wheel -- der Haken darf keine Installation voraussetzen.
    """
    relevant = {"engine/src/knob_registry.rs", "docs/knobs.md"}
    if staged_only and not (relevant & staged_files):
        return []  # dieser Commit ruehrt weder Registratur noch Knopf-Doku an

    if not KNOB_REGISTRY_PATH.exists():
        return []  # kein Engine-Baum (z.B. Teil-Checkout) -- nichts zu pruefen

    try:
        sys.path.insert(0, str(REPO_ROOT / "tools"))
        import generate_knob_docs as _gkd
        expected = _gkd.render_markdown(_gkd.knobs_from_source(), "direkt geparst, kein Wheel noetig")
    except Exception as e:  # Parse-/Import-Fehler sind selbst ein Befund
        return [
            f"REGEL 6 (Knopf-Doku aktuell): docs/knobs.md nicht pruefbar -- {type(e).__name__}: {e}\n"
            "  Konsequenz: der Format-Vertrag zwischen knob_registry.rs und dem Generator ist "
            "verletzt (typisch: ein KnobEntry ueber mehrere Zeilen umgebrochen).\n"
            "  Ausweg: den Eintrag auf EINE Zeile bringen, dann "
            "`python tools/generate_knob_docs.py` laufen lassen."
        ]

    current = KNOB_DOCS_PATH.read_text(encoding="utf-8") if KNOB_DOCS_PATH.exists() else ""
    if current == expected:
        return []
    return [
        "REGEL 6 (Knopf-Doku aktuell): docs/knobs.md entspricht nicht der Registratur in "
        "engine/src/knob_registry.rs.\n"
        "  Konsequenz: die einzige Uebersicht ueber die MOSAIC_*-Knoepfe zeigt einen "
        "ueberholten Stand -- ein Knopf fehlt dort, traegt einen falschen Default oder einen "
        "falschen Status. Genau die plausible Zweitquelle, die eine Sitzung kostet.\n"
        "  Ausweg: `python tools/generate_knob_docs.py` laufen lassen und docs/knobs.md "
        "mitcommitten (die Datei ist GENERIERT, nicht von Hand zu editieren)."
    ]


def warn_silent_test_skips(staged_only: bool, staged_files: set[str]) -> None:
    if staged_only:
        targets = [f for f in sorted(staged_files) if f.endswith(".rs")]
    else:
        targets = sorted(
            p.relative_to(REPO_ROOT).as_posix() for p in (REPO_ROOT / "engine" / "src").glob("*.rs")
        )
    for rel in targets:
        if staged_only:
            text = get_staged_content(rel)
        else:
            path = REPO_ROOT / rel
            text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else None
        if text is None:
            continue
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if not SILENT_SKIP_RETURN.match(line):
                continue
            window = lines[max(0, i - 3): i]
            trigger = next((w for w in window if SILENT_SKIP_TRIGGER.search(w)), None)
            if trigger is None:
                continue
            print(
                f"[WARNUNG, Regel 5 -- stille Test-Skips] {rel}:{i + 1}: fruehes `return` direkt "
                f"nach einer Voraussetzungs-Pruefung ({trigger.strip()[:80]!r}).\n"
                "  Wenn das ein Test ist: fehlende Voraussetzungen muessen `panic!`en (klare "
                "Meldung) oder der Test traegt `#[ignore = \"Grund\"]` -- ein stiller Skip "
                "besteht leer-gruen und prueft nichts (Anlassfall: load_test_net_for_gating, "
                "17 leer-gruene Tests im Inventar 2026-08-15). Kein Commit-Blocker: die "
                "Heuristik ist grob; Nicht-Test-Treffer bitte ignorieren.",
                file=sys.stderr,
            )


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Konventions-Linter (A5) -- siehe docs/DESIGN_conventions_as_checks.md"
    )
    parser.add_argument("--staged", action="store_true", help="nur gestagte Dateien pruefen (Hook-Modus)")
    parser.add_argument(
        "--update-size-baseline", action="store_true",
        help="Regel 1: tools/size_baseline.json aus dem Ist-Stand neu schreiben (manuell, kein Hook-Bestandteil)",
    )
    args = parser.parse_args()

    if args.update_size_baseline:
        update_size_baseline()
        return 0

    staged_files: set[str] = set()
    staged_mode = args.staged
    if args.staged:
        staged_files = set(get_staged_files())
        if not staged_files:
            # KEIN stiller Durchlauf (Fund 2026-08-09 beim Rauchtest des
            # Hakens): bei einem pfadgebundenen Commit (`git commit -- <pfade>`)
            # baut Git einen temporaeren Index, `git diff --cached` ist leer --
            # der Waechter haette JEDEN solchen Commit ungeprueft durchgelassen
            # und dabei "nichts zu pruefen" gemeldet, also gesund ausgesehen.
            # Genau die Fehlerklasse, gegen die er gebaut wurde. Statt Exit 0
            # daher Rueckfall auf den vollen Repo-Lauf: kostet ~1 s mehr,
            # prueft aber wirklich.
            print("Keine gestagten Dateien -- Rueckfall auf den vollen "
                  "Repo-Lauf (bei pfadgebundenem Commit der Normalfall).")
            staged_mode = False

    violations: list[str] = []
    violations += check_file_size_ratchet(staged_mode, staged_files)
    violations += check_doc_language(staged_mode, staged_files)
    violations += check_no_new_task_numbers(staged_mode, staged_files)
    violations += check_prereg_index_consistency(staged_mode, staged_files)
    violations += check_knob_docs_current(staged_mode, staged_files)
    warn_silent_test_skips(staged_mode, staged_files)  # Regel 5: nur Warnung, kein Exit-1

    if violations:
        print(f"\n{len(violations)} Konventions-Verstoss/Verstoesse:\n", file=sys.stderr)
        for v in violations:
            print(v + "\n", file=sys.stderr)
        return 1

    print("Konventions-Check: alle Regeln gruen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
