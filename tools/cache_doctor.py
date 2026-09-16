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
     Umgebungs-Fingerabdruck (`mosaic_env_fingerprint`, corpus_dataset.py:631).
  2. Stimmt der DATEINAME mit dem eingepraegten Schluessel ueberein? Der Name
     IST per Konvention der Schluessel (`corpus_dataset.py:902`). Wo beides
     auseinanderfaellt, liegt genau der Schaden vom 2026-09-16 vor.
  3. Wem gehoert der Cache? Belege aus `models/manifest_train_*.json`, den
     Split-Artefakten in `evaluations/artifacts/` und den Fensterlisten in
     `data/*.txt`.
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
import json
import os
import pathlib
import re
import sys
import time

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

_ROOT = pathlib.Path(__file__).resolve().parent.parent

# `.cache_<md5[:12]>.h5` -- gebaut in corpus_dataset.py:902, aufgepraegt in
# corpus_dataset.stamp_cache_key_attrs (corpus_dataset.py:652).
CACHE_GLOB = ".cache_*.h5"
CACHE_NAME_RE = re.compile(r"\.cache_([0-9a-f]{12})\.(?:h5|pt)")
# Ausgabezeile von tools/window_train_split.py (dort: "Fenster-Schluessel des
# Trainingsanteils: " + wk.key), wie sie in evaluations/artifacts/*split*.txt liegt.
SPLIT_KEY_RE = re.compile(r"Fenster-Schluessel des Trainingsanteils:\s*([0-9a-f]{12})")
SPLIT_LIST_RE = re.compile(r"Trainingsliste:\s*(\S+)")
HEX_RE = re.compile(r"\b[0-9a-f]{12,32}\b")

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


def _text(v):
    """h5py 3.x liefert Zeichenketten-Attribute als `str`, aeltere Schreiber
    koennen `bytes` hinterlassen haben (gleiche Begruendung wie in
    `corpus_dataset.verify_cache_file`)."""
    if v is None:
        return None
    return v.decode("utf-8", "replace") if isinstance(v, bytes) else str(v)


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
    """Alle Fensterlisten `data/*.txt` als {Name: {n, erste, letzte}}.

    Die Listen tragen Basisnamen, eine Kommentarzeile darf vorangehen (so
    schreibt `window_train_split.py` den Trainingsanteil). Sortiert wird hier,
    weil `window_cache_key` die Dateiliste sortiert (corpus_dataset.py:366 ff.)
    und die Attribute `mosaic_files_first/_last` daher die SORTIERTEN Raender
    sind."""
    out = {}
    for p in sorted(glob.glob(os.path.join(data_dir, "*.txt"))):
        try:
            with open(p, encoding="utf-8", errors="replace") as fh:
                names = sorted(os.path.basename(l.strip()) for l in fh
                               if l.strip() and not l.startswith("#"))
        except OSError:
            continue
        if not names:
            continue
        out[os.path.basename(p)] = {"n": len(names), "erste": names[0], "letzte": names[-1]}
    return out


def scan_manifests(root: pathlib.Path) -> list:
    """Trainings-Manifeste: welcher Lauf hat welche Fensterliste und welche
    datenrelevanten Knoepfe benutzt?

    GEPRUEFT am Dateiinhalt (2026-09-16): die Manifeste tragen `version`,
    `run_timestamp`, `cli_args`, `git_commit`, `engine_config`,
    `python_constants`, `corpus_composition`, `policy_carriers`; erst nach
    Lauf-Ende kommen `epoch_history` und `laufzeit` dazu. Ein Feld `cache_key`
    gibt es NICHT, `cli_args.cache_file` ist bei Selbstbau `null` -- deshalb
    ist die Zuordnung ueber die Fensterliste der Hauptweg und der explizite
    Pfad der Ausnahmefall."""
    rows = []
    for p in sorted(glob.glob(str(root / "models" / "manifest_train_*.json"))):
        try:
            with open(p, encoding="utf-8", errors="replace") as fh:
                d = json.load(fh)
        except (OSError, ValueError) as e:
            rows.append({"pfad": relpath(p), "fehler": repr(e)})
            continue
        ca = d.get("cli_args") or {}
        pc = d.get("policy_carriers") or {}
        rows.append({
            "pfad": relpath(p),
            "version": d.get("version"),
            "run_timestamp": d.get("run_timestamp"),
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
    nennungen: dict = {}
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
            offene_liste = None
            for i, line in enumerate(lines, 1):
                for m in CACHE_NAME_RE.finditer(line):
                    referenced.setdefault(m.group(1), []).append({"datei": rp, "zeile": i})
                for tok in HEX_RE.findall(line):
                    k = tok[:12]
                    if k in keys_of_interest:
                        nennungen.setdefault(k, []).append(
                            {"datei": rp, "zeile": i, "text": line.strip()[:160]})
                sm = SPLIT_KEY_RE.search(line)
                if sm:
                    offene_liste = {"datei": rp, "key": sm.group(1), "liste": None}
                    split_lines.append(offene_liste)
                lm = SPLIT_LIST_RE.search(line)
                if lm and offene_liste is not None and offene_liste["liste"] is None:
                    offene_liste["liste"] = os.path.basename(lm.group(1))
    return nennungen, referenced, split_lines


def build_report(data_dir: str, root: pathlib.Path, quiet: bool = False) -> dict:
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
            "name_key": nm.group(1) if nm else None,
        }
        row.update(info)
        row["name_stimmt"] = (row.get("attr_key") is not None
                              and row["name_key"] == row.get("attr_key"))
        row["env_knoepfe"] = parse_fingerprint(row.get("env_fingerprint"))
        caches.append(row)

    listen = list_index(data_dir)
    manifeste = scan_manifests(root)
    keys = {c["name_key"] for c in caches if c["name_key"]}
    keys |= {c.get("attr_key") for c in caches if c.get("attr_key")}
    keys.discard(None)
    if not quiet:
        print(f"  durchsuche Textquellen nach {len(keys)} Schluesseln ...", flush=True)
    nennungen, referenced, split_lines = scan_text_sources(root, keys)
    bau_artefakte = scan_build_artifacts(root)

    # --- Zuordnung je Cache -------------------------------------------------
    for c in caches:
        belege = []
        own = {c["name_key"], c.get("attr_key")} - {None}
        # (a) EXPLIZIT: ein Manifest nennt genau diese Datei als --cache-file.
        for m in manifeste:
            cf = m.get("cache_file")
            if cf and os.path.basename(str(cf)) == c["datei"]:
                belege.append({"art": "explizit", "arm": m.get("version"),
                               "quelle": m["pfad"],
                               "detail": "cli_args.cache_file zeigt auf diese Datei"})
        # (b) BAU-ARTEFAKT: ein Bau-Lauf hat genau diesen Schluessel gemeldet.
        for b in bau_artefakte:
            if b["cache_key"] in own or (b["merge_out"] and b["merge_out"] == c["datei"]):
                belege.append({"art": "bau-artefakt",
                               "arm": arm_from_name(b["file_list"]),
                               "quelle": b["pfad"],
                               "detail": f"cache_key={b['cache_key']}, "
                                         f"file_list={b['file_list']}, "
                                         f"merge_out={b['merge_out']}"})
        # (c) Welche Fensterliste hat exakt diese (n, erste, letzte)?
        # ACHTUNG Mehrdeutigkeit: mehrere Fenster koennen dieselben SORTIERTEN
        # Raender haben und sich nur in der Mitte unterscheiden. Ein Treffer
        # traegt hier deshalb nur, wenn er EINDEUTIG ist.
        passende_listen = [nm for nm, v in listen.items()
                           if v["n"] == c.get("files_n")
                           and v["erste"] == c.get("files_first")
                           and v["letzte"] == c.get("files_last")]
        c["passende_listen"] = passende_listen
        c["listen_eindeutig"] = len(passende_listen) == 1
        # (d) KETTE: Split-Artefakt nennt Schluessel UND Trainingsliste.
        for s in split_lines:
            if s["key"] in own:
                belege.append({"art": "kette", "arm": arm_from_name(s["datei"]),
                               "quelle": s["datei"],
                               "detail": f"Split-Artefakt vergibt {s['key']} an Liste "
                                         f"{s['liste']}"})
            elif (c["listen_eindeutig"] and s["liste"]
                  and s["liste"] in passende_listen):
                belege.append({"art": "listenkonflikt", "arm": None, "quelle": s["datei"],
                               "detail": f"Liste {s['liste']} passt eindeutig zu den "
                                         f"Attributen, das Artefakt vergibt dafuer aber "
                                         f"{s['key']}"})
        # (e) Manifest, dessen Fensterliste zu den Attributen passt (nur bei
        # eindeutiger Liste; sonst waere es geraten).
        if c["listen_eindeutig"]:
            for m in manifeste:
                fl = m.get("file_list")
                if fl and os.path.basename(str(fl)) in passende_listen:
                    belege.append({"art": "indiziell", "arm": m.get("version"),
                                   "quelle": m["pfad"],
                                   "detail": f"cli_args.file_list = "
                                             f"{os.path.basename(str(fl))}"})
        c["belege"] = belege
        c["nennungen"] = (nennungen.get(c["name_key"], [])
                          + (nennungen.get(c.get("attr_key"), [])
                             if c.get("attr_key") != c["name_key"] else []))
        arms = sorted({b["arm"] for b in belege if b.get("arm")})
        c["arme"] = arms
        if arms:
            c["status"] = "zugeordnet"
        elif belege or c["nennungen"]:
            c["status"] = "nur benannt"
        else:
            c["status"] = "VERWAIST"

    # --- referenziert, aber nicht vorhanden ---------------------------------
    vorhanden = {c["name_key"] for c in caches} | {c.get("attr_key") for c in caches}
    expected = {s["key"] for s in split_lines} | {b["cache_key"] for b in bau_artefakte
                                                  if b.get("cache_key")}
    fehlende = []
    for k, stellen in sorted(referenced.items()):
        if k in vorhanden:
            continue
        fehlende.append({"key": k, "stellen": stellen[:6], "n_stellen": len(stellen),
                         # "erwartet" heisst: ein Split- oder Bau-Artefakt hat
                         # diesen Schluessel als ZIEL eines Laufs vergeben. Alles
                         # andere ist blosse Erwaehnung (oft Alt-Teilcaches aus
                         # der Zeit vor den Datei-Bloecken).
                         "erwartet_von_einem_lauf": k in expected})

    findings = build_findings(caches, fehlende, data_dir)

    wand = time.perf_counter() - t0
    cpu = time.process_time() - c0
    return {
        "werkzeug": "tools/cache_doctor.py",
        "erzeugt": time.strftime("%Y-%m-%d %H:%M:%S"),
        "data_dir": relpath(data_dir),
        "caches": caches,
        "listen_n": len(listen),
        "manifeste_n": len(manifeste),
        "bau_artefakte_n": len(bau_artefakte),
        "referenziert_ohne_datei": fehlende,
        "befunde": findings,
        "bloecke": block_summary(data_dir),
        "laufzeit": {
            "wanduhr_s": round(wand, 2),
            "cpu_s": round(cpu, 2),
            "threads": 1,
            "s_je_datei": round(wand / len(caches), 3) if caches else None,
        },
    }


def block_summary(data_dir: str) -> dict:
    """Nur Anzahl und Platz der DATEI-Bloecke -- ohne sie zu oeffnen. Die
    inhaltliche Ansicht (Waisen, Quelldatei je Block) hat
    `tools/cache_inventory.py`; sie hier zu wiederholen waere eine zweite
    Wahrheit ueber dieselbe Grundmenge."""
    bl = glob.glob(os.path.join(data_dir, ".filecache_*.h5"))
    groesse = sum(os.path.getsize(b) for b in bl) if bl else 0
    return {"n": len(bl), "mb": round(groesse / (1024 * 1024), 1),
            "werkzeug": "tools/cache_inventory.py"}


def build_findings(caches: list, fehlende: list, data_dir: str) -> list:
    """Auffaelligkeiten, je mit einer Handlungsempfehlung im Klartext."""
    out = []

    for c in caches:
        if c.get("fehler"):
            out.append({
                "art": "unlesbar", "schwere": "ROT", "datei": c["datei"],
                "text": f"{c['datei']} laesst sich nicht als HDF5 oeffnen ({c['fehler']}).",
                "empfehlung": "Meist ein abgebrochener Bau oder Merge. Der Waechter in "
                              "corpus_dataset.verify_cache_file bricht darauf ohnehin ab. "
                              "Neu bauen; Loeschen bleibt Nutzer-Entscheid.",
            })
            continue
        if c.get("attr_key") is None:
            out.append({
                "art": "kein_schluessel", "schwere": "GELB", "datei": c["datei"],
                "text": f"{c['datei']} traegt kein Attribut 'mosaic_cache_key'.",
                "empfehlung": "train.py --cache-file lehnt so eine Datei ab "
                              "(corpus_dataset.py:721). Nachruesten mit "
                              "tools/stamp_cache_key.py, aber NUR mit den Parametern des "
                              "Bau-Laufs: das Werkzeug prueft den Inhalt nicht, es glaubt "
                              "der Kommandozeile.",
            })
        elif not c["name_stimmt"]:
            out.append({
                "art": "name_ungleich_schluessel", "schwere": "ROT", "datei": c["datei"],
                "text": f"{c['datei']} heisst nach Schluessel {c['name_key']}, sagt aber "
                        f"selbst {c['attr_key']} ({c['mb']} MB, zuletzt {c['datum']}).",
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
                "text": f"{c['datei']} ({c['mb']} MB): kein Manifest und kein Artefakt "
                        f"nennt "
                        + " oder ".join(sorted({c['name_key'], c.get('attr_key')} - {None}))
                        + ".",
                "empfehlung": "Entweder der erzeugende Lauf wurde nie registriert, oder der "
                              "Cache ist Rest einer verworfenen Reihe. Vor jeder "
                              "Entscheidung die Attribute oben lesen (Dateizahl, erste/"
                              "letzte Korpusdatei) -- sie sagen, welches Fenster darin "
                              "steckt. Loeschung ist Nutzer-Entscheid mit pfadgenauer "
                              "Freigabe.",
            })
        for b in c.get("belege", []):
            if b["art"] == "listenkonflikt":
                out.append({
                    "art": "listenkonflikt", "schwere": "ROT", "datei": c["datei"],
                    "text": f"{c['datei']}: {b['detail']} (Quelle {b['quelle']}).",
                    "empfehlung": "Dieselbe Dateiliste mit zwei verschiedenen Schluesseln "
                                  "heisst: zwischen den beiden Laeufen hat ein DATEN-Knopf "
                                  "gewechselt (Encoder, value-target-variant, "
                                  "conjunction-head, Traeger-Manifest, "
                                  "MOSAIC_MOON_TARGET_SOURCE ...). Genau richtig so, wenn "
                                  "die Knoepfe im Schluessel stehen; ein Befund, wenn "
                                  "einer davon nur in EINEM der beiden Schluessel steckt.",
                })

    ohne_fp = [c["datei"] for c in caches
               if not c.get("fehler") and c.get("env_fingerprint") is None]
    if ohne_fp:
        out.append({
            "art": "kein_fingerabdruck", "schwere": "GRAU", "datei": None,
            "text": f"{len(ohne_fp)} Cache(s) ohne Umgebungs-Fingerabdruck: "
                    + ", ".join(ohne_fp) + ".",
            "empfehlung": "Erwartbar fuer alles, was vor der Einfuehrung des Attributs gebaut "
                          "wurde ('mosaic_env_fingerprint', datiert 2026-09-16, "
                          "corpus_dataset.py:670-676). Kein "
                          "Schaden, aber bei einem Schluessel-Streit fehlt diesen Caches "
                          "die Selbstauskunft ueber ihre MOSAIC_*-Knoepfe.",
        })

    # Fingerabdruecke gegeneinander: welcher MOSAIC_*-Knopf unterscheidet sich?
    mit_fp = [c for c in caches if c.get("env_knoepfe")]
    if len(mit_fp) >= 2:
        all_entries = set()
        for c in mit_fp:
            all_entries |= set(c["env_knoepfe"])
        strittig = [k for k in sorted(all_entries)
                    if len({c["env_knoepfe"].get(k) for c in mit_fp}) > 1]
        if strittig:
            out.append({
                "art": "fingerabdruck_konflikt", "schwere": "GELB", "datei": None,
                "text": "Die Caches mit Fingerabdruck wurden unter verschiedenen "
                        "MOSAIC_*-Knoepfen gebaut: " + ", ".join(strittig) + ".",
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
    zugeteilt = [x for x in fehlende if x["erwartet_von_einem_lauf"]]
    if zugeteilt:
        lines = []
        for f in zugeteilt:
            st = ", ".join(f"{s['datei']}:{s['zeile']}" for s in f["stellen"][:2])
            lines.append(f"{f['key']}  <-  {st}")
        out.append({
            "art": "erwarteter_cache_fehlt", "schwere": "GELB", "datei": None,
            "text": f"{len(zugeteilt)} Schluessel wurden einem Lauf als Monolith "
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
    for f in [x for x in fehlende if not x["erwartet_von_einem_lauf"]]:
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
          f"({sum(c['mb'] for c in caches):,.0f} MB)   "
          f"Fensterlisten: {rep['listen_n']}   Manifeste: {rep['manifeste_n']}")
    b = rep["bloecke"]
    print(f"Datei-Bloecke (.filecache_*.h5): {b['n']} ({b['mb']:,.0f} MB) "
          f"-- Detailansicht: {b['werkzeug']}")

    for c in caches:
        print()
        print("-" * 78)
        marke = "OK " if c.get("name_stimmt") else "!!!"
        print(f"{marke} {c['datei']}   {c['mb']:,.1f} MB   {c['datum']}")
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
        knoepfe = c.get("env_knoepfe") or {}
        if knoepfe:
            print("    MOSAIC-Knoepfe   : " + ", ".join(
                f"{k.replace('MOSAIC_', '')}={v[:40]}" for k, v in sorted(knoepfe.items())))
        else:
            print("    MOSAIC-Knoepfe   : (kein Fingerabdruck, vor dem 2026-09-16 gebaut)")
        pl = c["passende_listen"]
        if len(pl) == 1:
            print(f"    Passende Liste   : {pl[0]} (eindeutig)")
        elif pl:
            print(f"    Passende Listen  : {len(pl)} MEHRDEUTIG "
                  f"({', '.join(pl[:4])}{' ...' if len(pl) > 4 else ''}) -- gleiche "
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
    _rang = {"ROT": 0, "GELB": 1, "GRAU": 2}
    for f in sorted(rep["befunde"], key=lambda x: _rang.get(x["schwere"], 3)):
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
    worte, lines, akt = s.split(), [], ""
    for w in worte:
        if len(akt) + len(w) + 1 > width:
            lines.append(akt)
            akt = w
        else:
            akt = (akt + " " + w).strip()
    if akt:
        lines.append(akt)
    return lines


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data-dir", default=str(_ROOT / "data"))
    ap.add_argument("--json", default=None, help="Bericht zusaetzlich maschinenlesbar")
    ap.add_argument("--quiet", action="store_true", help="ohne Fortschrittszeilen")
    a = ap.parse_args()

    if not os.path.isdir(a.data_dir):
        raise SystemExit(f"❌ '{a.data_dir}' ist kein Ordner.")
    rep = build_report(a.data_dir, _ROOT, quiet=a.quiet)
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
