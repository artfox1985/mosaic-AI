# -*- coding: utf-8 -*-
"""Doktor fuer die FENSTER-Caches (`data/.cache_<schluessel>.h5`): wem gehoert
welcher Monolith, und sagt die Datei dasselbe wie ihr Name?

ANLASS (Vorfall 2026-09-16): der Arm v29-b04 hat den Monolithen des Arms
v29-b03 ueberschrieben (rund 1,1 GB), weil `tools/window_train_split.py` den
Knopf `moon_target_source` nicht an `corpus_dataset.window_cache_key`
durchreichte und der Default "label" den Schluessel eines FREMDEN Datensatzes
ergab. Gewarnt hat nichts; aufgefallen ist es einem Menschen an der
Dateigroesse. Nutzer dazu: "das ist mir alles viel zu fragil und
fehleranfaellig und laesst sich als normaler Bediener nicht mehr handhaben."

WAS DAS WERKZEUG TUT: es liest die HDF5-DATEI-Attribute (kein Datensatz wird
geladen, die Monolithen sind ueber 1 GB) und stellt vier Fragen:

  1. Was steht drin -- Schluessel, Dateizahl, erste/letzte Korpusdatei,
     Umgebungs-Fingerabdruck (`corpus_dataset.mosaic_env_fingerprint`).
  2. Stimmt der DATEINAME mit dem eingepraegten Schluessel ueberein? Der Name
     IST per Konvention der Schluessel (gebaut in
     `corpus_dataset.MosaicDataset.__init__` als `.cache_<key>.h5`,
     aufgepraegt in `corpus_dataset.stamp_cache_key_attrs`). Wo beides
     auseinanderfaellt, liegt genau der Schaden vom 2026-09-16 vor.
  3. Wem gehoert der Cache? Belege aus `models/manifest_train_*.json`, den
     Split-Artefakten in `evaluations/artifacts/` und den Dateilisten in
     `data/*.txt`. Dazu die beiden Faelle, die bis zum 2026-09-16 als
     "VERWAIST" durchgingen, obwohl sie es nicht sind: der VAL-Monolith (jeder
     Lauf mit `val_frac > 0` baut einen zweiten, und KEIN Manifest nennt
     dessen Schluessel) und der Cache eines LAUFENDEN Trainings (Manifest ohne
     `laufzeit`-Block).
  4. Was ist auffaellig -- mit je einer Handlungsempfehlung im Klartext.

WAS ES NICHT TUT: es loescht nichts, es benennt nichts um, es schreibt kein
Attribut. Loeschung ist im Projekt ausnahmslos Nutzer-Entscheid mit
pfadgenauer Freigabe. Zum Aufpraegen eines fehlenden Schluessels gibt es
`tools/stamp_cache_key.py` (und der GLAUBT seiner Kommandozeile, siehe dort).

ABGRENZUNG zu `tools/cache_inventory.py`: das dort ist die Ansicht auf die
DATEI-Bloecke `.filecache_<inhaltsschluessel>.h5` (Frage: existiert die
Quelldatei noch?). Disjunkte Grundmenge, andere Frage, anderer Besitzbegriff.
Dieses Werkzeug fasst die MONOLITHEN an und verweist fuer die Bloecke dorthin,
statt deren Logik zu kopieren.

Aufruf:
    python -X utf8 -u tools/cache_doctor.py
    python -X utf8 -u tools/cache_doctor.py --json evaluations/artifacts/cache_doctor.json
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import time

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

_ROOT = pathlib.Path(__file__).resolve().parent.parent

# `.cache_<md5[:12]>.h5` -- gebaut in `corpus_dataset.MosaicDataset.__init__`,
# aufgepraegt in `corpus_dataset.stamp_cache_key_attrs`.
CACHE_GLOB = ".cache_*.h5"
CACHE_NAME_RE = re.compile(r"\.cache_([0-9a-f]{12})\.(?:h5|pt)")
# Ausgabezeile von tools/window_train_split.py (dort: "Fenster-Schluessel des
# Trainingsanteils: " + wk.key), wie sie in evaluations/artifacts/*split*.txt liegt.
SPLIT_KEY_RE = re.compile(r"Fenster-Schluessel des Trainingsanteils:\s*([0-9a-f]{12})")
SPLIT_LIST_RE = re.compile(r"Trainingsliste:\s*(\S+)")
# Lookaround statt `\b` (Befund 2026-09-16): der Unterstrich ist ein WORTZEICHEN,
# darum hat `\b[0-9a-f]{12,32}\b` genau die Form nicht getroffen, in der ein
# Schluessel im Baum normalerweise steht -- `.cache_7ebef2449837.h5`. Folge war,
# dass belegte Caches als "VERWAIST" gemeldet wurden.
HEX_RE = re.compile(r"(?<![0-9a-f])[0-9a-f]{12,32}(?![0-9a-f])")

# Dateilisten in `data/`: welche sind Fensterlisten, welche davon VAL-Listen?
# `window_train_split.py --val-list-out` schreibt `window_<fenster>_val.txt`.
WINDOW_LIST_RE = re.compile(r"^window_.*\.txt$")
VAL_LIST_RE = re.compile(r"^window_.*_val\.txt$")

# Textquellen, die einen Schluessel nennen koennen. Bewusst eine LISTE statt
# eines Baumlaufs: `models/frozen_champions/*/venv` enthaelt zehntausende
# Fremddateien, und ein Doktor, der Minuten braucht, wird nicht benutzt.
TEXT_GLOBS = [
    "models/manifest_train_*.json",
    "evaluations/artifacts/*.txt",
    "evaluations/artifacts/*.json",
    "evaluations/*.md",
    "docs/*.md",
    "tools/*.sh",
    "tools/*.py",
    "tools/probes/*.py",
    "*.md",
    "*.py",
]
MAX_TEXT_BYTES = 4 * 1024 * 1024

# Ein Manifest OHNE `laufzeit`-Block ist entweder ein laufender oder ein
# abgestuerzter Lauf. Die Grenze trennt beide Faelle; 24 h, weil ein
# Trainingslauf dieser Generation gemessen 4-12 h dauert (STATUS.md,
# Abschnitt "Laufzeiten (gemessen)") und ein aelteres kopfloses Manifest kein
# laufender Lauf mehr sein kann.
RUNNING_MAX_AGE_S = 24 * 3600
MANIFEST_TS_FMT = "%Y%m%d_%H%M%S"


def _text(v):
    """h5py 3.x liefert Zeichenketten-Attribute als `str`, aeltere Schreiber
    koennen `bytes` hinterlassen haben (gleiche Begruendung wie in
    `corpus_dataset.verify_cache_file`)."""
    if v is None:
        return None
    return v.decode("utf-8", "replace") if isinstance(v, bytes) else str(v)


def _size(mb: float) -> str:
    """Groesse mit deutschem Dezimalkomma und richtiger Einheit.

    Befund 2026-09-16: `{:,.0f} MB` hat "2,372 MB" gedruckt -- deutsch gelesen
    2,372 statt 2372 --, und die Zahl war ohnehin MiB, nicht MB."""
    if mb >= 1024:
        return f"{mb / 1024:.2f}".replace(".", ",") + " GiB"
    return f"{mb:.1f}".replace(".", ",") + " MiB"


def read_cache_attrs(path: str) -> dict:
    """Datei-Attribute eines Monolithen. NUR Attribute und Formen -- kein
    Datensatz wird gelesen (`.shape` ist Metadatum im HDF5-Header)."""
    import h5py
    out = {"fehler": None}
    try:
        with h5py.File(path, "r") as hf:
            attrs = dict(hf.attrs)
            out["datasets"] = sorted(hf.keys())
            out["rows"] = int(hf["values"].shape[0]) if "values" in hf else None
    except Exception as e:  # noqa: BLE001 -- unlesbar ist ein Befund, kein Absturz
        out["fehler"] = repr(e)
        return out
    out["attr_key"] = _text(attrs.get("mosaic_cache_key"))
    out["attr_key_full"] = _text(attrs.get("mosaic_cache_key_full"))
    out["attrs_version"] = attrs.get("mosaic_cache_key_attrs_version")
    if out["attrs_version"] is not None:
        out["attrs_version"] = int(out["attrs_version"])
    n = attrs.get("mosaic_files_n")
    out["files_n"] = int(n) if n is not None else None
    out["files_first"] = _text(attrs.get("mosaic_files_first"))
    out["files_last"] = _text(attrs.get("mosaic_files_last"))
    out["env_fingerprint"] = _text(attrs.get("mosaic_env_fingerprint"))
    return out


def parse_fingerprint(fp: str | None) -> dict:
    """"K=V;K=V" -> dict. Gleiche Zerlegung wie in `verify_cache_file`."""
    if not fp:
        return {}
    return dict(x.split("=", 1) for x in str(fp).split(";") if "=" in x)


def list_index(data_dir: str) -> dict:
    """Die Dateilisten in `data/*.txt`, zu INHALTSGRUPPEN zusammengefasst.
    Rueckgabe: {gruppen_id: {n, erste, letzte, dateien, roh_md5, val, window}}.

    ZUSAMMENFASSUNG nach Inhalt (Befund 2026-09-16): jeder Lauf schreibt sich
    eine eigene, inhaltsgleiche Kopie derselben Liste -- gemessen sind vier
    byte-gleiche Trainingslisten (md5 91f322786fe0927bbafc7b0dc2b781c6) und
    vier byte-gleiche Val-Listen (70e7476c07d84521e9c25937e8459aac) im
    v29-Fenster. Ohne die Zusammenfassung ist JEDER Cache "MEHRDEUTIG", und
    damit war der ROT-Detektor 'listenkonflikt' strukturell tot: er haengt an
    `listen_eindeutig`.

    Die Gruppen-Id ist md5 ueber die SORTIERTEN Basisnamen, nicht ueber die
    Rohbytes -- zwei Listen mit gleicher Menge in anderer Reihenfolge sind
    dasselbe Fenster. Die Rohbyte-md5 wird je Gruppe mitgefuehrt, damit ein
    Befund mit `md5sum` nachpruefbar bleibt.

    Grundmenge bleibt `data/*.txt` und nicht nur `window_*.txt`: auch eine
    Traeger- oder Schwarmliste kann das Fenster eines Caches gewesen sein, und
    ein verlorener Treffer waere teurer als eine Zeile mehr im Bericht. Der
    Bericht nennt beide Zaehlungen (`listen_n` / `listen_window_n`).

    Sortiert wird, weil `corpus_dataset.window_cache_key` die Dateiliste
    sortiert und die Attribute `mosaic_files_first/_last` daher die SORTIERTEN
    Raender sind. Eine Kommentarzeile darf vorangehen (so schreibt
    `window_train_split.py` den Trainingsanteil)."""
    groups: dict = {}
    for p in sorted(glob.glob(os.path.join(data_dir, "*.txt"))):
        base = os.path.basename(p)
        try:
            with open(p, "rb") as fh:
                raw = fh.read()
        except OSError:
            continue
        names = sorted(os.path.basename(x.strip())
                       for x in raw.decode("utf-8", "replace").splitlines()
                       if x.strip() and not x.startswith("#"))
        if not names:
            continue
        gid = hashlib.md5("\n".join(names).encode("utf-8")).hexdigest()[:12]
        g = groups.setdefault(gid, {"n": len(names), "erste": names[0],
                                    "letzte": names[-1], "dateien": [],
                                    "roh_md5": [], "val": False, "window": False})
        g["dateien"].append(base)
        digest = hashlib.md5(raw).hexdigest()
        if digest not in g["roh_md5"]:
            g["roh_md5"].append(digest)
        if VAL_LIST_RE.match(base):
            g["val"] = True
        if WINDOW_LIST_RE.match(base):
            g["window"] = True
    return groups


def _manifest_time(ts) -> float | None:
    """`run_timestamp` ("20260916_210750") -> Unix-Sekunden (lokale Zeit, so
    wie `time.strftime` es geschrieben hat)."""
    try:
        return time.mktime(time.strptime(str(ts), MANIFEST_TS_FMT))
    except (TypeError, ValueError):
        return None


def scan_manifests(root: pathlib.Path, now: float | None = None) -> list:
    """Trainings-Manifeste: welcher Lauf hat welche Fensterliste und welche
    datenrelevanten Knoepfe benutzt -- und LAEUFT er noch?

    GEPRUEFT am Dateiinhalt (2026-09-16): die Manifeste tragen `version`,
    `run_timestamp`, `cli_args`, `git_commit`, `engine_config`,
    `python_constants`, `corpus_composition`, `policy_carriers`; erst nach
    Lauf-Ende kommen `epoch_history` und `laufzeit` dazu. Ein Feld `cache_key`
    gibt es NICHT, `cli_args.cache_file` ist bei Selbstbau `null` -- deshalb
    ist die Zuordnung ueber die Fensterliste der Hauptweg und der explizite
    Pfad der Ausnahmefall.

    `laeuft_vermutlich` nutzt genau diese Beobachtung: kein `laufzeit`-Block
    UND ein `run_timestamp` juenger als RUNNING_MAX_AGE_S heisst, der Lauf ist
    noch unterwegs. Bis zum 2026-09-16 wurde `hat_laufzeit` erhoben und
    nirgends ausgewertet -- der Val-Cache des laufenden Trainings hiess darum
    "VERWAIST"."""
    if now is None:
        now = time.time()
    rows = []
    for p in sorted(glob.glob(str(root / "models" / "manifest_train_*.json"))):
        try:
            with open(p, encoding="utf-8", errors="replace") as fh:
                d = json.load(fh)
        except (OSError, ValueError) as e:
            rows.append({"pfad": relpath(p), "fehler": repr(e),
                         "laeuft_vermutlich": False})
            continue
        ca = d.get("cli_args") or {}
        pc = d.get("policy_carriers") or {}
        start = _manifest_time(d.get("run_timestamp"))
        rows.append({
            "pfad": relpath(p),
            "version": d.get("version"),
            "run_timestamp": d.get("run_timestamp"),
            "start_ts": start,
            "file_list": ca.get("file_list"),
            "cache_file": ca.get("cache_file"),
            "encoder": ca.get("encoder"),
            "value_target_variant": ca.get("value_target_variant"),
            "conjunction_head": ca.get("conjunction_head"),
            "moon_target_source": ca.get("moon_target_source"),
            "val_frac": ca.get("val_frac"),
            "val_pool": ca.get("val_pool"),
            "data_exclude": pc.get("data_exclude"),
            "hat_laufzeit": "laufzeit" in d,
            "laeuft_vermutlich": ("laufzeit" not in d and start is not None
                                  and 0 <= now - start <= RUNNING_MAX_AGE_S),
        })
    return rows


ARM_RE = re.compile(r"v\d+[-_]b\d+")


def arm_from_name(name: str | None) -> str | None:
    """Armname aus einem Datei- oder Listennamen (z.B. 'window_v29_b04_train.txt'
    -> 'v29-b04'). NAMENSINDIZ, kein Beleg: die Ausgabe wird als solche
    markiert. Bei mehreren Treffern gewinnt der letzte, weil die Bestandsnamen
    das Muster '<fenster>_split_<arm>' benutzen."""
    if not name:
        return None
    hits = ARM_RE.findall(str(name))
    return hits[-1].replace("_", "-") if hits else None


def scan_build_artifacts(root: pathlib.Path) -> list:
    """Bau-Artefakte in `evaluations/artifacts/*.json`, die einen Cache-
    Schluessel FUEHREN.

    GEPRUEFT am Dateiinhalt (2026-09-16, cache_build_incremental.json): die
    Felder heissen `cache_key`, `cache_key_full`, `merge_out`, `file_list`.
    Das ist der einzige Ort im Baum, an dem ein gebauter Monolith seinen
    Schluessel MIT Fensterliste hinterlaesst -- die Trainings-Manifeste tun
    das nicht (dort ist `cli_args.cache_file` bei Selbstbau null)."""
    rows = []
    for p in sorted(glob.glob(str(root / "evaluations" / "artifacts" / "*.json"))):
        try:
            if os.path.getsize(p) > MAX_TEXT_BYTES:
                continue
            with open(p, encoding="utf-8", errors="replace") as fh:
                d = json.load(fh)
        except (OSError, ValueError):
            continue
        if not isinstance(d, dict):
            continue
        if not (d.get("cache_key") or d.get("merge_out")):
            continue
        rows.append({
            "pfad": relpath(p),
            "cache_key": d.get("cache_key"),
            "cache_key_full": d.get("cache_key_full"),
            "merge_out": os.path.basename(str(d["merge_out"])) if d.get("merge_out") else None,
            "file_list": os.path.basename(str(d["file_list"])) if d.get("file_list") else None,
            "encoder": d.get("encoder"),
            "value_target_variant": d.get("value_target_variant"),
            "traeger_manifest": d.get("traeger_manifest"),
        })
    return rows


def relpath(p) -> str:
    """Pfad relativ zur Projektwurzel -- das Repo ist oeffentlich, neue
    Ausgaben tragen keine Rechnerstruktur (CLAUDE.md, Nutzer-Entscheid
    2026-08-17)."""
    try:
        return str(pathlib.Path(p).resolve().relative_to(_ROOT)).replace("\\", "/")
    except ValueError:
        return str(p).replace("\\", "/")


def scan_text_sources(root: pathlib.Path, keys_of_interest: set) -> tuple:
    """Alle Nennungen eines Schluessels im Baum, plus alle als
    `.cache_<key>.h5` REFERENZIERTEN Schluessel (auch die ohne Datei).

    Rueckgabe: (nennungen, referenziert, split_zeilen)
      nennungen   : {key12: [{datei, zeile, text}]}
      referenziert: {key12: [{datei, zeile}]}
      split_zeilen: [{datei, key, liste}] aus den Split-Artefakten
    """
    mentions: dict = {}
    referenced: dict = {}
    split_lines: list = []
    seen = set()
    for g in TEXT_GLOBS:
        for p in sorted(glob.glob(str(root / g))):
            rp = relpath(p)
            # Die eigene Ausgabe ist KEIN Beleg. Ohne diesen Ausschluss macht
            # der zweite Lauf jede Waise des ersten zu einem "benannten" Cache,
            # weil der Bericht selbst den Schluessel nennt (beobachtet beim
            # zweiten Lauf am 2026-09-16).
            if os.path.basename(rp).startswith("cache_doctor"):
                continue
            if rp in seen:
                continue
            seen.add(rp)
            try:
                if os.path.getsize(p) > MAX_TEXT_BYTES:
                    continue
                with open(p, encoding="utf-8", errors="replace") as fh:
                    lines = fh.readlines()
            except OSError:
                continue
            open_split = None
            for i, line in enumerate(lines, 1):
                for m in CACHE_NAME_RE.finditer(line):
                    referenced.setdefault(m.group(1), []).append({"datei": rp, "zeile": i})
                for tok in HEX_RE.findall(line):
                    k = tok[:12]
                    if k in keys_of_interest:
                        mentions.setdefault(k, []).append(
                            {"datei": rp, "zeile": i, "text": line.strip()[:160]})
                sm = SPLIT_KEY_RE.search(line)
                if sm:
                    open_split = {"datei": rp, "key": sm.group(1), "liste": None}
                    split_lines.append(open_split)
                lm = SPLIT_LIST_RE.search(line)
                if lm and open_split is not None and open_split["liste"] is None:
                    open_split["liste"] = os.path.basename(lm.group(1))
    return mentions, referenced, split_lines


def val_owner(cache: dict, manifests: list) -> dict | None:
    """Welcher Lauf hat diesen VAL-Monolithen gebaut?

    `train.py` baut in JEDEM Lauf mit `val_frac > 0` einen zweiten Monolithen
    aus der Val-Liste (zweite `MosaicDataset(...)`-Konstruktion, `files=
    val_files`), und KEIN Manifest nennt dessen Schluessel: `cli_args.
    cache_file` zeigt auf den TRAININGS-Monolithen. Zuordnung darum ueber die
    Zeit plus die datenrelevanten Knoepfe -- ZEITINDIZ, kein Beleg.

    Regel: unter allen Manifesten mit `val_frac > 0`, deren `run_timestamp`
    VOR der mtime des Caches liegt und deren Knoepfe dem Fingerabdruck des
    Caches nicht widersprechen, gewinnt das JUENGSTE. Der Val-Monolith
    entsteht kurz nach dem Manifest (das schreibt `train.py` vor dem Bau der
    Datensaetze), ein aelterer Lauf kann ihn nicht geschrieben haben."""
    mtime = cache.get("mtime_ts")
    knobs = cache.get("env_knoepfe") or {}
    best = None
    for m in manifests:
        if (m.get("val_frac") or 0) <= 0:
            continue
        start = m.get("start_ts")
        if start is None or mtime is None or start > mtime:
            continue
        agree, conflict = [], []
        for attr, knob in (("moon_target_source", "MOSAIC_MOON_TARGET_SOURCE"),
                           ("val_pool", "MOSAIC_VAL_POOL")):
            seen_value, want = knobs.get(knob), m.get(attr)
            if seen_value is None or want is None:
                continue  # Knopf war zur Bauzeit noch nicht im Fingerabdruck
            (agree if str(seen_value) == str(want) else conflict).append(attr)
        if conflict:
            continue
        if best is None or start > best["manifest"]["start_ts"]:
            best = {"manifest": m, "agree": agree, "abstand_s": mtime - start}
    return best


def running_train_processes() -> dict:
    """Prozessblick: laeuft wirklich ein `train.py`? Kostet einen
    PowerShell-Start und wird darum NUR gefragt, wenn ein Manifest ohne
    `laufzeit`-Block frisch genug ist, um ein laufender Lauf zu sein.

    Kein Beleg fuer die Zuordnung, sondern die Gegenprobe zur Manifest-Regel:
    kein Prozess plus kopfloses Manifest heisst ABGESTUERZT, nicht laufend."""
    ps = ("@(Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'python' "
          "-and $_.CommandLine -match 'train\\.py' } | ForEach-Object { $_.ProcessId }) "
          "-join ','")
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=30, check=False)
    except (OSError, ValueError, subprocess.SubprocessError) as e:
        return {"gefragt": True, "pids": None, "fehler": repr(e)}
    pids = [x for x in (r.stdout or "").strip().split(",") if x.strip()]
    return {"gefragt": True, "pids": pids, "fehler": None}


def build_report(data_dir: str, root: pathlib.Path, quiet: bool = False,
                 probe_processes: bool = True) -> dict:
    t0, c0 = time.perf_counter(), time.process_time()
    caches_paths = sorted(glob.glob(os.path.join(data_dir, CACHE_GLOB)))
    caches = []
    for i, p in enumerate(caches_paths, 1):
        if not quiet:
            print(f"  [{i}/{len(caches_paths)}] lese Attribute: {os.path.basename(p)}",
                  flush=True)
        st = os.stat(p)
        nm = CACHE_NAME_RE.search(os.path.basename(p))
        info = read_cache_attrs(p)
        row = {
            "datei": os.path.basename(p),
            "pfad": relpath(p),
            "mb": round(st.st_size / (1024 * 1024), 1),
            "datum": time.strftime("%Y-%m-%d %H:%M", time.localtime(st.st_mtime)),
            "mtime_ts": st.st_mtime,
            "name_key": nm.group(1) if nm else None,
        }
        row.update(info)
        row["name_stimmt"] = (row.get("attr_key") is not None
                              and row["name_key"] == row.get("attr_key"))
        row["env_knoepfe"] = parse_fingerprint(row.get("env_fingerprint"))
        caches.append(row)

    lists = list_index(data_dir)
    manifests = scan_manifests(root)
    manifest_by_path = {m["pfad"]: m for m in manifests}
    keys = {c["name_key"] for c in caches if c["name_key"]}
    keys |= {c.get("attr_key") for c in caches if c.get("attr_key")}
    keys.discard(None)
    if not quiet:
        print(f"  durchsuche Textquellen nach {len(keys)} Schluesseln ...", flush=True)
    mentions, referenced, split_lines = scan_text_sources(root, keys)
    build_artifacts = scan_build_artifacts(root)

    running_manifests = [m for m in manifests if m.get("laeuft_vermutlich")]
    processes = (running_train_processes() if (running_manifests and probe_processes)
                 else {"gefragt": False, "pids": None, "fehler": None})

    # --- Zuordnung je Cache -------------------------------------------------
    for c in caches:
        evidence = []
        own = {c["name_key"], c.get("attr_key")} - {None}
        # (a) EXPLIZIT: ein Manifest nennt genau diese Datei als --cache-file.
        for m in manifests:
            cf = m.get("cache_file")
            if cf and os.path.basename(str(cf)) == c["datei"]:
                evidence.append({"art": "explizit", "arm": m.get("version"),
                                 "quelle": m["pfad"],
                                 "detail": "cli_args.cache_file zeigt auf diese Datei"})
        # (b) BAU-ARTEFAKT: ein Bau-Lauf hat genau diesen Schluessel gemeldet.
        for b in build_artifacts:
            if b["cache_key"] in own or (b["merge_out"] and b["merge_out"] == c["datei"]):
                evidence.append({"art": "bau-artefakt",
                                 "arm": arm_from_name(b["file_list"]),
                                 "quelle": b["pfad"],
                                 "detail": f"cache_key={b['cache_key']}, "
                                           f"file_list={b['file_list']}, "
                                           f"merge_out={b['merge_out']}"})
        # (c) Welche Dateiliste hat exakt diese (n, erste, letzte)? Verglichen
        # werden INHALTSGRUPPEN (list_index): die vier byte-gleichen Kopien
        # einer Liste sind EIN Kandidat, nicht vier. Ein Treffer traegt nur,
        # wenn er eindeutig ist -- zwei inhaltlich VERSCHIEDENE Fenster koennen
        # dieselben sortierten Raender haben und sich nur in der Mitte
        # unterscheiden.
        matching_groups = [g for g in lists.values()
                           if g["n"] == c.get("files_n")
                           and g["erste"] == c.get("files_first")
                           and g["letzte"] == c.get("files_last")]
        matching_lists = [nm2 for g in matching_groups for nm2 in g["dateien"]]
        c["passende_listen"] = matching_lists
        c["passende_listen_gruppen"] = [g["dateien"] for g in matching_groups]
        c["listen_eindeutig"] = len(matching_groups) == 1
        # (d) KETTE: Split-Artefakt nennt Schluessel UND Trainingsliste.
        for s in split_lines:
            if s["key"] in own:
                # Der Arm steckt im LISTENNAMEN, nicht im Namen des Artefakts
                # (Befund 2026-09-16: `v29_split.txt` traegt kein Armmuster,
                # `window_v29_b04_train.txt` schon).
                evidence.append({"art": "kette",
                                 "arm": arm_from_name(s["liste"]) or arm_from_name(s["datei"]),
                                 "quelle": s["datei"],
                                 "detail": f"Split-Artefakt vergibt {s['key']} an Liste "
                                           f"{s['liste']}"})
            elif (c["listen_eindeutig"] and s["liste"]
                  and s["liste"] in matching_lists):
                evidence.append({"art": "listenkonflikt", "arm": None, "quelle": s["datei"],
                                 "detail": f"Liste {s['liste']} passt eindeutig zu den "
                                           f"Attributen, das Artefakt vergibt dafuer aber "
                                           f"{s['key']}"})
        # (e) Manifest, dessen Fensterliste zu den Attributen passt (nur bei
        # eindeutiger Liste; sonst waere es geraten).
        if c["listen_eindeutig"]:
            for m in manifests:
                fl = m.get("file_list")
                if fl and os.path.basename(str(fl)) in matching_lists:
                    evidence.append({"art": "indiziell", "arm": m.get("version"),
                                     "quelle": m["pfad"],
                                     "detail": f"cli_args.file_list = "
                                               f"{os.path.basename(str(fl))}"})
        # (f) VAL-CACHE: die Attribute passen zu einer VAL-Liste. Ohne diesen
        # Zweig hiessen die Val-Monolithen "VERWAIST" oder "nur benannt" --
        # kein Manifest NENNT sie, und das ist kein Defekt, sondern die
        # Bauweise von train.py.
        is_val = bool(matching_groups) and all(g["val"] for g in matching_groups)
        c["val_cache"] = is_val
        if is_val:
            owner = val_owner(c, manifests)
            if owner:
                m = owner["manifest"]
                arm = m.get("version")
                detail = (f"Val-Liste {matching_lists[0]} passt zu den Attributen "
                          f"({c.get('files_n')} Dateien, {c.get('files_first')} .. "
                          f"{c.get('files_last')}); Manifest val_frac={m.get('val_frac')}, "
                          f"val_pool={m.get('val_pool')}, "
                          f"moon_target_source={m.get('moon_target_source')}, encoder="
                          f"{m.get('encoder')}, value_target_variant="
                          f"{m.get('value_target_variant')}; run_timestamp "
                          f"{m.get('run_timestamp')} liegt {int(owner['abstand_s'])} s vor "
                          f"der mtime des Caches")
                if owner["agree"]:
                    detail += ("; Fingerabdruck des Caches bestaetigt "
                               + ", ".join(owner["agree"]))
                detail += (" -- ZEITINDIZ, kein Beleg: train.py schreibt den Val-Monolithen "
                           "ohne Manifest-Eintrag")
                evidence.append({"art": f"val-zu-{arm}", "arm": arm,
                                 "quelle": m["pfad"], "detail": detail})
            else:
                evidence.append({
                    "art": "val-zu-unbekannt", "arm": None, "quelle": None,
                    "detail": f"Val-Liste {matching_lists[0]} passt zu den Attributen, aber "
                              f"kein Manifest mit val_frac > 0 liegt zeitlich und in den "
                              f"Knoepfen davor"})
        c["belege"] = evidence
        # Nennungen: HEX-Treffer PLUS die `.cache_<key>.h5`-Referenzen. Letztere
        # wurden bis zum 2026-09-16 verworfen (der Fehlende-Schluessel-Zweig
        # ueberging jeden vorhandenen Cache), obwohl sie die direkteste Nennung
        # ueberhaupt sind.
        raw_mentions = list(mentions.get(c["name_key"], []))
        if c.get("attr_key") and c.get("attr_key") != c["name_key"]:
            raw_mentions += mentions.get(c["attr_key"], [])
        for k in own:
            for place in referenced.get(k, []):
                raw_mentions.append({"datei": place["datei"], "zeile": place["zeile"],
                                     "text": f".cache_{k}.h5"})
        deduped, seen_places = [], set()
        for mention in raw_mentions:
            sig = (mention["datei"], mention["zeile"])
            if sig in seen_places:
                continue
            seen_places.add(sig)
            deduped.append(mention)
        c["nennungen"] = sorted(deduped, key=lambda x: (x["datei"], x["zeile"]))
        arms = sorted({b["arm"] for b in evidence if b.get("arm")})
        c["arme"] = arms
        # (g) LAEUFT: gehoert der Cache einem Manifest OHNE `laufzeit`-Block,
        # dessen `run_timestamp` frisch ist? Dann ist weder "verwaist" noch ein
        # GELB angebracht -- der Lauf schreibt gerade hinein.
        live = [manifest_by_path[b["quelle"]] for b in evidence
                if b.get("quelle") in manifest_by_path
                and manifest_by_path[b["quelle"]].get("laeuft_vermutlich")]
        c["laeuft_manifest"] = live[0]["pfad"] if live else None
        if live:
            newest = max(live, key=lambda m: m.get("start_ts") or 0)
            c["status"] = (f"LAEUFT ({newest.get('version')} seit "
                           f"{newest.get('run_timestamp')})")
        elif is_val:
            c["status"] = "val-cache"
        elif arms:
            c["status"] = "zugeordnet"
        elif evidence or c["nennungen"]:
            c["status"] = "nur benannt"
        else:
            c["status"] = "VERWAIST"

    # --- referenziert, aber nicht vorhanden ---------------------------------
    present = {c["name_key"] for c in caches} | {c.get("attr_key") for c in caches}
    expected = {s["key"] for s in split_lines} | {b["cache_key"] for b in build_artifacts
                                                  if b.get("cache_key")}
    missing = []
    for k, places in sorted(referenced.items()):
        if k in present:
            continue  # vorhandene Caches: die Nennung steht oben bei der Datei
        missing.append({"key": k, "stellen": places[:6], "n_stellen": len(places),
                        # "erwartet" heisst: ein Split- oder Bau-Artefakt hat
                        # diesen Schluessel als ZIEL eines Laufs vergeben. Alles
                        # andere ist blosse Erwaehnung (oft Alt-Teilcaches aus
                        # der Zeit vor den Datei-Bloecken).
                        "erwartet_von_einem_lauf": k in expected})

    findings = build_findings(caches, missing, build_artifacts)

    wall = time.perf_counter() - t0
    cpu = time.process_time() - c0
    list_files = [f for g in lists.values() for f in g["dateien"]]
    return {
        "werkzeug": "tools/cache_doctor.py",
        "erzeugt": time.strftime("%Y-%m-%d %H:%M:%S"),
        "data_dir": relpath(data_dir),
        "caches": caches,
        "listen_n": len(list_files),
        "listen_grundmenge": "data/*.txt (nicht-leere Zeilen, Kommentare weg)",
        "listen_window_n": sum(1 for f in list_files if WINDOW_LIST_RE.match(f)),
        "listen_gruppen_n": len(lists),
        "manifeste_n": len(manifests),
        "bau_artefakte_n": len(build_artifacts),
        "laufende_manifeste": [{"pfad": m["pfad"], "version": m.get("version"),
                                "run_timestamp": m.get("run_timestamp")}
                               for m in running_manifests],
        "prozesse_train_py": processes,
        "referenziert_ohne_datei": missing,
        "befunde": findings,
        "bloecke": block_summary(data_dir),
        "laufzeit": {
            "wanduhr_s": round(wall, 2),
            "cpu_s": round(cpu, 2),
            "threads": 1,
            "s_je_datei": round(wall / len(caches), 3) if caches else None,
        },
    }


def block_summary(data_dir: str) -> dict:
    """Nur Anzahl und Platz der DATEI-Bloecke -- ohne sie zu oeffnen. Die
    inhaltliche Ansicht (Waisen, Quelldatei je Block) hat
    `tools/cache_inventory.py`; sie hier zu wiederholen waere eine zweite
    Wahrheit ueber dieselbe Grundmenge."""
    bl = glob.glob(os.path.join(data_dir, ".filecache_*.h5"))
    size = sum(os.path.getsize(b) for b in bl) if bl else 0
    return {"n": len(bl), "mb": round(size / (1024 * 1024), 1),
            "werkzeug": "tools/cache_inventory.py"}


def build_findings(caches: list, missing: list, build_artifacts: list) -> list:
    """Auffaelligkeiten, je mit einer Handlungsempfehlung im Klartext."""
    out = []

    for c in caches:
        running = str(c.get("status", "")).startswith("LAEUFT")
        if c.get("fehler"):
            out.append({
                "art": "unlesbar", "schwere": "ROT", "datei": c["datei"],
                "text": f"{c['datei']} laesst sich nicht als HDF5 oeffnen ({c['fehler']}).",
                "empfehlung": "Meist ein abgebrochener Bau oder Merge. Der Waechter in "
                              "corpus_dataset.verify_cache_file bricht darauf ohnehin ab. "
                              "Neu bauen; Loeschen bleibt Nutzer-Entscheid.",
            })
            continue
        if running:
            out.append({
                "art": "laufender_lauf", "schwere": "GRAU", "datei": c["datei"],
                "text": f"{c['datei']} ({_size(c['mb'])}) gehoert einem LAUFENDEN Training: "
                        f"{c['status']} ({c.get('laeuft_manifest')}).",
                "empfehlung": "Nichts tun. Solange das Manifest keinen `laufzeit`-Block hat "
                              "und sein run_timestamp frisch ist, schreibt der Lauf hier "
                              "hinein -- fehlende Attribute oder eine noch unvollstaendige "
                              "Datei sind in diesem Zustand erwartbar, und 'verwaist' waere "
                              "eine Falschauskunft. Nach Lauf-Ende erneut pruefen.",
            })
        if c.get("attr_key") is None and not running:
            out.append({
                "art": "kein_schluessel", "schwere": "GELB", "datei": c["datei"],
                "text": f"{c['datei']} traegt kein Attribut 'mosaic_cache_key'.",
                "empfehlung": "train.py --cache-file lehnt so eine Datei ab "
                              "(corpus_dataset.verify_cache_file). Nachruesten mit "
                              "tools/stamp_cache_key.py, aber NUR mit den Parametern des "
                              "Bau-Laufs: das Werkzeug prueft den Inhalt nicht, es glaubt "
                              "der Kommandozeile.",
            })
        elif c.get("attr_key") is not None and not c["name_stimmt"]:
            out.append({
                "art": "name_ungleich_schluessel", "schwere": "ROT", "datei": c["datei"],
                "text": f"{c['datei']} heisst nach Schluessel {c['name_key']}, sagt aber "
                        f"selbst {c['attr_key']} ({_size(c['mb'])}, zuletzt {c['datum']}).",
                "empfehlung": "Das ist die Signatur des Vorfalls vom 2026-09-16. Ein Lauf, "
                              f"der {c['name_key']} sucht, WAEHLT diese Datei und bricht "
                              "dann am Schluessel-Waechter ab; ein Lauf, der "
                              f"{c['attr_key']} sucht, findet sie nie und baut neu. "
                              "Zuerst klaeren, welcher Lauf zuletzt hineingeschrieben hat "
                              "(Datum oben, Belege unten), und ob der INHALT zum Namen "
                              "oder zum Attribut gehoert. Nicht umbenennen, bevor das "
                              "geklaert ist: der Name ist die einzige Adresse, unter der "
                              "ein Training den Cache findet.",
            })
        if c["status"] == "VERWAIST":
            out.append({
                "art": "verwaist", "schwere": "GELB", "datei": c["datei"],
                "text": f"{c['datei']} ({_size(c['mb'])}): kein Manifest und kein Artefakt "
                        f"nennt "
                        + " oder ".join(sorted({c['name_key'], c.get('attr_key')} - {None}))
                        + ", und die Attribute passen zu keiner Val-Liste.",
                "empfehlung": "Entweder der erzeugende Lauf wurde nie registriert, oder der "
                              "Cache ist Rest einer verworfenen Reihe. Vor jeder "
                              "Entscheidung die Attribute oben lesen (Dateizahl, erste/"
                              "letzte Korpusdatei) -- sie sagen, welches Fenster darin "
                              "steckt. Loeschung ist Nutzer-Entscheid mit pfadgenauer "
                              "Freigabe.",
            })
        # Listenkonflikte gebuendelt: bei vier inhaltsgleichen Listenkopien und
        # drei Split-Artefakten waeren es sonst sieben gleichlautende Absaetze.
        conflicts = [b for b in c.get("belege", []) if b["art"] == "listenkonflikt"]
        if conflicts:
            out.append({
                "art": "listenkonflikt", "schwere": "ROT", "datei": c["datei"],
                "text": f"{c['datei']} (Schluessel {c['name_key']}): dieselbe Dateiliste "
                        f"traegt in {len(conflicts)} Artefakt(en) einen ANDEREN Schluessel.",
                "zeilen": [f"{b['quelle']}: {b['detail']}" for b in conflicts],
                "empfehlung": "Dieselbe Dateiliste mit zwei verschiedenen Schluesseln "
                              "heisst: zwischen den Laeufen hat ein DATEN-Knopf "
                              "gewechselt (Encoder, value-target-variant, "
                              "conjunction-head, Traeger-Manifest, "
                              "MOSAIC_MOON_TARGET_SOURCE ...) ODER der Listenpfad, denn "
                              "der Schluessel haengt an den ABSOLUTEN Pfaden der "
                              "Korpusdateien. Genau richtig so, wenn die Knoepfe im "
                              "Schluessel stehen; ein Befund, wenn einer davon nur in "
                              "EINEM der beiden Schluessel steckt.",
            })

    # Bau-Artefakt gegen sich selbst: `merge_out` nennt eine Datei, deren Name
    # ein anderer Schluessel ist als das Feld `cache_key` desselben Artefakts.
    # Gefunden 2026-09-16 in cache_build_incremental.json (merge_out
    # .cache_fd13f54061cd.h5 gegen cache_key 4dd9f020b232).
    for b in build_artifacts:
        if not (b.get("cache_key") and b.get("merge_out")):
            continue
        nm = CACHE_NAME_RE.search(str(b["merge_out"]))
        if nm and nm.group(1) != b["cache_key"]:
            out.append({
                "art": "bau_artefakt_widerspruch", "schwere": "ROT", "datei": b["merge_out"],
                "text": f"{b['pfad']} widerspricht sich selbst: merge_out = "
                        f"{b['merge_out']} (Name sagt {nm.group(1)}), Feld cache_key = "
                        f"{b['cache_key']}, file_list = {b['file_list']}.",
                "empfehlung": "Der Name IST der Schluessel -- ein Bau, der unter dem einen "
                              "Namen schreibt und den anderen protokolliert, macht jede "
                              "Zuordnung ueber dieses Artefakt falsch (und ein Training, "
                              "das den protokollierten Schluessel sucht, baut neu). "
                              "Klaeren, welches Feld den tatsaechlichen Bau beschreibt, "
                              "und das Artefakt korrigieren; der Datei nicht trauen, "
                              "solange das offen ist.",
            })

    without_fp = [c["datei"] for c in caches
                  if not c.get("fehler") and c.get("env_fingerprint") is None]
    if without_fp:
        out.append({
            "art": "kein_fingerabdruck", "schwere": "GRAU", "datei": None,
            "text": f"{len(without_fp)} Cache(s) ohne Umgebungs-Fingerabdruck: "
                    + ", ".join(without_fp) + ".",
            "empfehlung": "Erwartbar fuer alles, was vor der Einfuehrung des Attributs gebaut "
                          "wurde ('mosaic_env_fingerprint', datiert 2026-09-16, gesetzt in "
                          "corpus_dataset.stamp_cache_key_attrs). Kein "
                          "Schaden, aber bei einem Schluessel-Streit fehlt diesen Caches "
                          "die Selbstauskunft ueber ihre MOSAIC_*-Knoepfe.",
        })

    # Fingerabdruecke gegeneinander: welcher MOSAIC_*-Knopf unterscheidet sich?
    with_fp = [c for c in caches if c.get("env_knoepfe")]
    if len(with_fp) >= 2:
        all_entries = set()
        for c in with_fp:
            all_entries |= set(c["env_knoepfe"])
        disputed = [k for k in sorted(all_entries)
                    if len({c["env_knoepfe"].get(k) for c in with_fp}) > 1]
        if disputed:
            out.append({
                "art": "fingerabdruck_konflikt", "schwere": "GELB", "datei": None,
                "text": "Die Caches mit Fingerabdruck wurden unter verschiedenen "
                        "MOSAIC_*-Knoepfen gebaut: " + ", ".join(disputed) + ".",
                "empfehlung": "Pro Knopf pruefen, ob er die DATEN veraendert. Wenn ja, "
                              "muss er im Fenster-Schluessel stehen (corpus_dataset."
                              "window_cache_key) UND im Block-Schluessel "
                              "(engine/py/file_cache_key.py) -- sonst teilen sich zwei "
                              "Datensaetze einen Namen. Wenn nein, ist die Abweichung "
                              "harmlos.",
            })

    # Fehlende Schluessel: einzeln nur die, die ein Lauf als ZIEL vergeben hat.
    # Der Rest wird JE QUELLE zu einem Befund gebuendelt -- ein Bau-Artefakt von
    # 2026-08 nennt 42 laengst ersetzte Teilcaches, und 42 gleichlautende
    # Absaetze machen den Bericht unlesbar (erster Lauf, 2026-09-16).
    assigned = [x for x in missing if x["erwartet_von_einem_lauf"]]
    if assigned:
        lines = []
        for f in assigned:
            places = ", ".join(f"{s['datei']}:{s['zeile']}" for s in f["stellen"][:2])
            lines.append(f"{f['key']}  <-  {places}")
        out.append({
            "art": "erwarteter_cache_fehlt", "schwere": "GELB", "datei": None,
            "text": f"{len(assigned)} Schluessel wurden einem Lauf als Monolith "
                    f"ZUGETEILT, aber data/.cache_<schluessel>.h5 existiert nicht:",
            "zeilen": lines,
            "empfehlung": "Fuer abgeschlossene Generationen ist das der Normalfall: der "
                          "Generationswechsel loescht die Monolithen. Zu pruefen ist nur "
                          "der Schluessel der LAUFENDEN Reihe. Dort gibt es drei "
                          "Moeglichkeiten -- nie gebaut, geloescht, oder ueberschrieben "
                          "und jetzt unter anderem Namen. Die dritte ist die teure: dann "
                          "steht oben ein Cache, dessen Name nicht zu seinem Schluessel "
                          "passt. Harmlos ist die erste: ein Training auf diesen "
                          "Schluessel BAUT neu (Stunden), es laedt nichts Falsches.",
        })
    rest: dict = {}
    for f in [x for x in missing if not x["erwartet_von_einem_lauf"]]:
        for s in f["stellen"]:
            rest.setdefault(s["datei"], set()).add(f["key"])
    for source, ks in sorted(rest.items()):
        kl = sorted(ks)
        out.append({
            "art": "alt_referenz", "schwere": "GRAU", "datei": None,
            "text": f"{source} nennt {len(kl)} Cache-Schluessel ohne Datei "
                    f"(z.B. {', '.join(kl[:4])}).",
            "empfehlung": "Blosse Erwaehnung, kein Lauf hat einen davon als Ziel "
                          "vergeben. Im Normalfall Alt-Teilcaches aus der Zeit vor den "
                          "Datei-Bloecken -- nichts zu tun.",
        })
    return out


def render_text(rep: dict) -> None:
    caches = rep["caches"]
    print()
    print("=" * 78)
    print(f"CACHE-DOKTOR -- Fenster-Monolithen in {rep['data_dir']}")
    print("=" * 78)
    print(f"Monolithen: {len(caches)}  "
          f"({_size(sum(c['mb'] for c in caches))})   "
          f"Manifeste: {rep['manifeste_n']}")
    print(f"Dateilisten in data/: {rep['listen_n']} "
          f"(Grundmenge {rep['listen_grundmenge']}; davon "
          f"{rep['listen_window_n']} window_*.txt, "
          f"{rep['listen_gruppen_n']} Inhaltsgruppen)")
    b = rep["bloecke"]
    print(f"Datei-Bloecke (.filecache_*.h5): {b['n']} ({_size(b['mb'])}) "
          f"-- Detailansicht: {b['werkzeug']}")
    for m in rep.get("laufende_manifeste") or []:
        print(f"LAEUFT VERMUTLICH: {m['version']} seit {m['run_timestamp']} "
              f"({m['pfad']}, kein laufzeit-Block)")
    pr = rep.get("prozesse_train_py") or {}
    if pr.get("gefragt"):
        if pr.get("pids"):
            print(f"Prozessblick     : train.py laeuft, PID(s) {', '.join(pr['pids'])}")
        elif pr.get("fehler"):
            print(f"Prozessblick     : nicht moeglich ({pr['fehler']})")
        else:
            print("Prozessblick     : KEIN train.py-Prozess -- das kopflose Manifest oben "
                  "gehoert zu einem ABGESTUERZTEN Lauf, nicht zu einem laufenden")

    for c in caches:
        print()
        print("-" * 78)
        mark = "OK " if c.get("name_stimmt") else "!!!"
        print(f"{mark} {c['datei']}   {_size(c['mb'])}   {c['datum']}")
        if c.get("fehler"):
            print(f"    UNLESBAR: {c['fehler']}")
            continue
        print(f"    Name sagt        : {c['name_key']}")
        print(f"    Datei sagt       : {c.get('attr_key') or '(kein Attribut)'}"
              f"   (voll: {c.get('attr_key_full') or '-'})")
        if c.get("attr_key") is None:
            print("    >>> DIE DATEI MACHT KEINE SELBSTAUSKUNFT <<<")
        elif not c.get("name_stimmt"):
            print("    >>> NAME UND SCHLUESSEL FALLEN AUSEINANDER <<<")
        if c.get("files_n") is None:
            print("    Fenster          : (kein Attribut mosaic_files_n)")
        else:
            print(f"    Fenster          : {c.get('files_n')} Dateien, "
                  f"{c.get('files_first')} .. {c.get('files_last')}")
        print(f"    Zustaende        : {c.get('rows')}   Datasets: "
              f"{len(c.get('datasets') or [])}")
        knobs = c.get("env_knoepfe") or {}
        if knobs:
            print("    MOSAIC-Knoepfe   : " + ", ".join(
                f"{k.replace('MOSAIC_', '')}={v[:40]}" for k, v in sorted(knobs.items())))
        else:
            print("    MOSAIC-Knoepfe   : (kein Fingerabdruck, vor dem 2026-09-16 gebaut)")
        groups = c.get("passende_listen_gruppen") or []
        if len(groups) == 1 and len(groups[0]) == 1:
            print(f"    Passende Liste   : {groups[0][0]} (eindeutig)")
        elif len(groups) == 1:
            print(f"    Passende Liste   : {groups[0][0]} (eindeutig; inhaltsgleiche "
                  f"Kopien: {', '.join(groups[0][1:])})")
        elif groups:
            heads = ", ".join(g[0] for g in groups[:4])
            print(f"    Passende Listen  : {len(groups)} inhaltlich VERSCHIEDENE Gruppen "
                  f"MEHRDEUTIG ({heads}{' ...' if len(groups) > 4 else ''}) -- gleiche "
                  f"Raender, Unterschied steckt in der Mitte")
        else:
            print("    Passende Listen  : (keine)")
        print(f"    Status           : {c['status']}"
              + (f"   Arm(e): {', '.join(c['arme'])}" if c["arme"] else ""))
        for bl in c["belege"]:
            print(f"      - [{bl['art']}] {bl['quelle']}: {bl['detail']}")
        for n in c["nennungen"][:6]:
            print(f"      - [nennung] {n['datei']}:{n['zeile']}  {n['text']}")
        if len(c["nennungen"]) > 6:
            print(f"      - ... und {len(c['nennungen']) - 6} weitere Nennungen")

    print()
    print("=" * 78)
    print("AUFFAELLIGKEITEN")
    print("=" * 78)
    if not rep["befunde"]:
        print("  Keine. Jeder Monolith heisst wie sein Schluessel und hat einen Besitzer.")
    _rank = {"ROT": 0, "GELB": 1, "GRAU": 2}
    for f in sorted(rep["befunde"], key=lambda x: _rank.get(x["schwere"], 3)):
        print()
        print(f"[{f['schwere']}] {f['art']}")
        for line in _wrap(f["text"], 74):
            print(f"  {line}")
        for line in f.get("zeilen", []):
            print(f"     {line}")
        for i, line in enumerate(_wrap(f["empfehlung"], 72)):
            print(f"  -> {line}" if i == 0 else f"     {line}")
    print()
    print(f"Laufzeit: {rep['laufzeit']['wanduhr_s']} s Wanduhr, "
          f"{rep['laufzeit']['cpu_s']} s CPU, {rep['laufzeit']['threads']} Thread, "
          f"{rep['laufzeit']['s_je_datei']} s je Datei")
    print("Dieses Werkzeug loescht nichts, benennt nichts um und schreibt kein Attribut.")


def _wrap(s: str, width: int) -> list:
    words, lines, cur = s.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    return lines


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data-dir", default=str(_ROOT / "data"))
    ap.add_argument("--json", default=None, help="Bericht zusaetzlich maschinenlesbar")
    ap.add_argument("--quiet", action="store_true", help="ohne Fortschrittszeilen")
    ap.add_argument("--no-process-probe", action="store_true",
                    help="den PowerShell-Prozessblick auslassen (er kostet einen "
                         "Prozessstart und wird ohnehin nur bei einem kopflosen, "
                         "frischen Manifest gefragt)")
    a = ap.parse_args()

    if not os.path.isdir(a.data_dir):
        raise SystemExit(f"❌ '{a.data_dir}' ist kein Ordner.")
    rep = build_report(a.data_dir, _ROOT, quiet=a.quiet,
                       probe_processes=not a.no_process_probe)
    render_text(rep)
    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)) or ".", exist_ok=True)
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(rep, fh, ensure_ascii=False, indent=1)
        print(f"JSON geschrieben: {relpath(a.json)}")
    # Rueckgabewert: 1, sobald ein ROTER Befund dabei ist -- so kann ein Skript
    # den Doktor als Tor benutzen, ohne die Ausgabe zu parsen.
    return 1 if any(f["schwere"] == "ROT" for f in rep["befunde"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
