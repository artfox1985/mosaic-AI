"""Policy-Traegersatz eines Trainingslaufs aufloesen und protokollieren.

Eigenes Modul, weil `train.py` die Modularitaetsschwelle aus CLAUDE.md bereits
reisst -- der Konventions-Waechter hat das Wachstum zu Recht geblockt.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "engine" / "py"))
from config import DATA_DIR, MODELS_DIR, VALUE_WEIGHT, POINTS_WEIGHT
from neural_net import (TD_LAMBDA, POLICY_TARGET_SHARPEN_EXPONENT,
                        VALUE_SCHEMA_VERSION)


def policy_carrier_report(all_files, selfplay_filename_re=None) -> dict:
    """Loest die Policy-TRAEGER-Regel schon beim Manifest-Schreiben auf und
    zaehlt je Praefix, wie viele Dateien tatsaechlich Policy-Ziele beitragen.

    WARUM DAS HIER STEHT (Befund 2026-08-16): der gesamte Ownership-Korpus war
    in SIEBEN Trainingslaeufen policy-maskiert, ohne dass es irgendwo sichtbar
    wurde -- die Korpusdateien sind weder im Traeger-Manifest gelistet noch
    beginnen sie mit `V20_CARRIER_SHORTCUT_PREFIXES` (bis 2026-08-27
    `WDL_GENERATOR_PREFIXES`), also galt `pol_w = 0.0`
    (`neural_net.py:1804`). Value-, Punkte- und Ownership-Ziele liefen normal
    durch, die Laeufe sahen also voellig unauffaellig aus. Aufgefallen ist es
    erst ueber eine Nutzer-Frage, nicht ueber eine Messung.

    Eine Zeile "v21_own_k1: 100 Dateien, davon 0 Traeger" im Manifest haette
    das am ersten Tag gezeigt. Genau die schreibt diese Funktion.

    Zusaetzlich festgehalten wird, WELCHES Traeger-Manifest galt: der Default
    (`policy_carrier_manifest_v20.json`) und das v21-Manifest liefern
    unterschiedliche Traegersaetze, und bisher stand in keinem Trainings-
    manifest, welches aktiv war."""
    try:
        from corpus_dataset import _is_policy_carrier
        from neural_net import V20_CARRIER_SHORTCUT_PREFIXES
    except ImportError:                                   # defensiv: nie den Lauf blockieren
        return {"error": "neural_net._is_policy_carrier nicht importierbar"}

    # Default LEER seit 2026-08-29 (Nutzer-Auftrag, Merkliste 1e) -- gleiche
    # Semantik wie corpus_dataset.py: ohne gesetzte Env-Var gibt es kein
    # Manifest, jede Datei traegt Policy.
    mf_name = os.environ.get("MOSAIC_CARRIER_MANIFEST", "")
    mf_path = Path(DATA_DIR) / mf_name if mf_name else None
    carrier_set, carrier_prefixes = None, None
    if mf_path is not None and mf_path.exists():
        try:
            mf = json.loads(mf_path.read_text(encoding="utf-8"))
            carrier_set = frozenset(mf.get("policy_carrier_files", []))
            if "carrier_prefixes" in mf:
                carrier_prefixes = list(mf["carrier_prefixes"])
        except Exception as e:                            # kaputtes Manifest sichtbar machen
            return {"carrier_manifest": mf_name, "error": f"nicht lesbar: {e}"}

    je_praefix: dict[str, int] = {}
    traeger_gesamt = 0
    for f in all_files:
        name = Path(f).name
        m = (selfplay_filename_re or _SELFPLAY_FILENAME_RE).match(name)
        prefix = m.group("prefix") if m else "_unmatched"
        ist = _is_policy_carrier(name, carrier_set, carrier_prefixes,
                                 name.startswith(V20_CARRIER_SHORTCUT_PREFIXES))
        je_praefix[prefix] = je_praefix.get(prefix, 0) + (1 if ist else 0)
        traeger_gesamt += 1 if ist else 0
    return {
        "carrier_manifest": mf_name or None,
        # mf_path ist None, wenn MOSAIC_CARRIER_MANIFEST leer ist (Default
        # seit 2026-08-29) -- Folge-Fix zum Default-Umbau, der diese Stelle
        # ungeschuetzt liess (b05-Startabbruch am selben Tag).
        "carrier_manifest_gefunden": bool(mf_path is not None and mf_path.exists()),
        "carrier_prefixes": carrier_prefixes,
        "gelistete_dateien": len(carrier_set) if carrier_set is not None else None,
        "traeger_dateien_gesamt": traeger_gesamt,
        "traeger_dateien_je_praefix": je_praefix,
        "data_exclude": os.environ.get("MOSAIC_DATA_EXCLUDE"),
        # b23-Manifest hat den Knopf nicht protokolliert, nur der Cache-Key
        # waechterte -- exakt die Fehlerklasse des MOSAIC_CARRIER_MANIFEST-
        # Vorfalls. Roh-Wert (auch "p"/"buf"/"puffer" fuer Arm P, par.12).
        "reach_target_k1": os.environ.get("MOSAIC_REACH_TARGET_K1"),
    }


def _git_commit_hash() -> str | None:
    """Best-effort HEAD-Commit-Hash. None, wenn nicht ermittelbar."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=str(Path(__file__).resolve().parent),
            capture_output=True, text=True, timeout=5, check=True,
        )
        return out.stdout.strip()
    except Exception:
        return None


def _git_is_dirty() -> bool | None:
    """Best-effort: gibt es uncommittete Änderungen im Arbeitsbaum? None,
    wenn nicht ermittelbar."""
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain"], cwd=str(Path(__file__).resolve().parent),
            capture_output=True, text=True, timeout=5, check=True,
        )
        return bool(out.stdout.strip())
    except Exception:
        return None


def _engine_config() -> dict:
    """Aktive Rust-Suchkonstanten, siehe `mosaic_rust.engine_config_json`
    (lib.rs, Phase 2a). Best-effort: `train.py` braucht `mosaic_rust`
    ansonsten nicht -- ein fehlendes/altes Wheel darf das Training nicht
    verhindern, nur diesen Manifest-Teil leer/fehlerhaft lassen."""
    try:
        import mosaic_rust as _mr
        return json.loads(_mr.engine_config_json())
    except Exception as e:
        return {"_error": f"engine_config_json nicht verfügbar: {e!r}"}


_SELFPLAY_FILENAME_RE = re.compile(
    r"^selfplay_(?P<prefix>.+)_(?P<date>\d{8})_(?P<time>\d{4})_g(?P<games>\d+)\.pkl$"
)


def corpus_composition(all_files: list[str]) -> list[dict]:
    """Gruppiert die Trainingskorpus-Dateien nach Versions-Präfix (alles vor
    dem eingebetteten Zeitstempel `_<date>_<time>_g<N>.pkl`, siehe
    `self_play.py::_flush`) -- rein aus den DATEINAMEN, kein Pickle-Laden
    nötig. `games`-Schätzung: die kumulative `_g<N>`-Ziffer resettet bei
    JEDEM neuen Self-Play-Lauf auf klein (self_play.py's `done` startet pro
    Aufruf bei 0) -- Dateien je Präfix nach (Zeitstempel, dann g) sortiert,
    ein Sprung `g_i <= g_{i-1}` gilt als Start eines neuen Laufs (eigener
    Beitrag = g_i selbst statt g_i - g_{i-1}). Reduziert sich für den
    Normalfall (ein durchgehender Lauf je Präfix) exakt auf `max(g)`
    (z.B. "180 Dateien netcq (1800 Spiele)" bei per_file=10)."""
    groups: dict[str, list[tuple[str, int]]] = {}
    unmatched = 0
    for f in all_files:
        name = Path(f).name
        m = _SELFPLAY_FILENAME_RE.match(name)
        if not m:
            unmatched += 1
            continue
        prefix = m.group("prefix")
        dt_key = m.group("date") + m.group("time")
        games = int(m.group("games"))
        groups.setdefault(prefix, []).append((dt_key, games))

    composition = []
    for prefix, entries in groups.items():
        # Reihenfolgefreie Schaetzung (Fix 2026-08-21): die alte
        # Lauf-Neustart-Heuristik (g faellt => neuer Lauf) scheiterte, sobald
        # zwei Laeufe desselben Praefixes an der Grenze denselben
        # MINUTEN-Zeitstempel teilten -- der (dt, g)-Sort mischte dann
        # Lauf-Ende und Lauf-Anfang und zaehlte ein Lauf-Ende doppelt
        # (Vorfall v21_asymN: 11990 statt 8000). Stattdessen: je DISTINKTEM
        # g-Wert zaehlt die Spanne zum naechstkleineren g so oft, wie
        # Dateien diesen g-Wert tragen -- exakt fuer beliebig viele
        # sequenzielle Laeufe mit gleicher Datei-Granularitaet, und fuer den
        # Einzellauf identisch zu max(g).
        counts: dict[int, int] = {}
        for _dt_key, g in entries:
            counts[g] = counts.get(g, 0) + 1
        total_games = 0
        prev_g = 0
        for g in sorted(counts):
            total_games += (g - prev_g) * counts[g]
            prev_g = g
        # TEILMENGEN-BERICHTIGUNG (2026-08-31, mit `train.py --file-list`):
        # die kumulative Rechnung oben stimmt fuer VOLLSTAENDIGE Laeufe, aber
        # nicht fuer ein rotierendes Fenster. Faellt eine Datei heraus, erbt
        # ihre Nachfolgerin deren Spanne, und die Summe bleibt max(g) -- das
        # v23-Fenster nimmt 1.745 von 2.400 hv2-Dateien und wurde so als
        # "24000 Spiele" statt 17.450 ausgewiesen (b01-Manifest vom
        # 2026-08-31 traegt noch die alte Zahl).
        # Robuster Ersatz: die Datei-Granularitaet ist der KLEINSTE positive
        # Abstand zwischen benachbarten g-Werten (bei gleichmaessiger
        # Aufteilung genau `--per-file`), und die Partienzahl ist
        # Dateien x Granularitaet. Beide Zahlen bleiben im Manifest, damit
        # ein Leser den Unterschied sieht statt ihn zu raten.
        _gs = sorted(counts)
        _diffs = [b - a for a, b in zip(_gs, _gs[1:]) if b > a]
        stride = min(_diffs) if _diffs else (_gs[0] if _gs else 0)
        games_by_stride = len(entries) * stride if stride else None
        entry = {"prefix": prefix, "files": len(entries),
                 "games": games_by_stride if games_by_stride is not None else total_games,
                 "games_cumulative": total_games, "stride": stride}
        if games_by_stride is not None and games_by_stride != total_games:
            # Kein Fehler, sondern der Normalfall bei einem rotierenden
            # Fenster -- aber er gehoert sichtbar ins Manifest.
            entry["subset_of_run"] = True
        composition.append(entry)
    composition.sort(key=lambda c: -c["files"])
    if unmatched:
        composition.append({"prefix": "_unmatched", "files": unmatched, "games": None})
    return composition


def append_train_laufzeit(version_name, run_timestamp, laufzeit) -> None:
    """Traegt den `laufzeit`-Block NACHTRAEGLICH ins Trainings-Manifest ein.

    CLAUDE.md, Nutzer-Anweisung 2026-08-25: jeder Messlauf schreibt seine Dauer
    in sein EIGENES Artefakt. Bis 2026-08-25 hielt das Manifest nur
    `run_timestamp`, also den Start -- die Dauer stand allein auf stdout und
    war nach dem Lauf verloren. Anders als beim Self-Play laeuft das Training
    im selben Prozess, `cpu_s` ist hier also echt messbar.
    """
    path = MODELS_DIR / f"manifest_train_{version_name}_{run_timestamp}.json"
    try:
        with open(path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        manifest["laufzeit"] = laufzeit
        with open(path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        print(f"⏱️  Laufzeit ins Manifest nachgetragen: {laufzeit['wanduhr_s']:.1f}s "
              f"(davon Datenaufbau {laufzeit.get('datenaufbau_s', float('nan')):.1f}s, "
              f"{laufzeit.get('epochen', '?')} Epochen)")
    except Exception as e:
        print(f"  ⚠️  Laufzeit konnte nicht nachgetragen werden ({e!r}).")


def append_train_cache_file(version_name, run_timestamp, cache_file_info) -> None:
    """Traegt den VALIDIERTEN Fenster-Schluessel des vorab gebauten Caches
    nachtraeglich ins Trainings-Manifest ein (Schlachtplan A0 Schritt 2c).

    Warum nachtraeglich, gleiches Muster wie `append_train_laufzeit`: das
    Manifest entsteht VOR dem Train/Val-Split, der Schluessel steht erst fest,
    wenn der Datensatz gebaut ist. `cli_args["cache_file"]` haelt derweil die
    WAHL fest -- ohne diesen Block wuesste man hinterher nur, dass eine Datei
    angegeben war, nicht welches Fenster sie trug.

    Muster `--load`-Footgun (Memory feedback_num_actions_change_breaks_old_
    checkpoints): der Waechter selbst bricht hart ab, deshalb darf DIESE
    Nachtragung best-effort bleiben -- ein nicht schreibbares Manifest soll
    kein bereits validiertes Training abbrechen."""
    path = MODELS_DIR / f"manifest_train_{version_name}_{run_timestamp}.json"
    try:
        with open(path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        manifest["cache_file"] = cache_file_info
        with open(path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        print(f"📝 Cache-Datei ins Manifest nachgetragen: {cache_file_info.get('cache_file')} "
              f"(Schluessel {cache_file_info.get('cache_key')}, "
              f"{cache_file_info.get('rows')} Zustaende)")
    except Exception as e:
        print(f"  ⚠️  Cache-Datei konnte nicht ins Manifest nachgetragen werden ({e!r}).")


def write_train_manifest(version_name, cli_args, corpus_composition, run_timestamp,
                          policy_carriers=None) -> None:
    """Schreibt `models/manifest_train_<name>_<timestamp>.json` und loggt die
    Korpus-Zusammensetzung auf Konsole."""
    manifest = {
        "version": version_name,
        "run_timestamp": run_timestamp,
        "cli_args": cli_args,
        "git_commit": _git_commit_hash(),
        "git_dirty": _git_is_dirty(),
        "engine_config": _engine_config(),
        "python_constants": {
            "TD_LAMBDA": TD_LAMBDA,
            "POLICY_TARGET_SHARPEN_EXPONENT": POLICY_TARGET_SHARPEN_EXPONENT,
            "VALUE_WEIGHT": VALUE_WEIGHT,
            "POINTS_WEIGHT": POINTS_WEIGHT,
            "VALUE_SCHEMA_VERSION": VALUE_SCHEMA_VERSION,
        },
        "corpus_composition": corpus_composition,
        "policy_carriers": policy_carriers,
    }
    path = MODELS_DIR / f"manifest_train_{version_name}_{run_timestamp}.json"
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        print(f"📝 Trainings-Manifest geschrieben: '{path}'")
    except Exception as e:
        print(f"  ⚠️  Manifest konnte nicht geschrieben werden ({e!r}) -- Training läuft trotzdem weiter.")

    print("📦 Trainingskorpus-Zusammensetzung (nach Versions-Präfix, aus Dateinamen):")
    je_pre = (policy_carriers or {}).get("traeger_dateien_je_praefix") or {}
    for c in corpus_composition:
        games_s = f"{c['games']} Spiele" if c["games"] is not None else "Spiele-Zahl unklar"
        tr = je_pre.get(c["prefix"])
        # Der Traeger-Hinweis ist der Kern des 2026-08-16-Befunds: ohne ihn sieht ein
        # policy-maskierter Korpus im Log genauso aus wie ein wirksamer.
        tr_s = "" if tr is None else (f"  [Policy-Traeger: {tr}/{c['files']}]"
                                       if tr else f"  [KEINE Policy-Traeger -- {c['prefix']} fuettert nur Value/Ownership]")
        print(f"   {c['files']:>4} Dateien {c['prefix']:<28} ({games_s}){tr_s}")
    if policy_carriers:
        print(f"   Traeger-Manifest: {policy_carriers.get('carrier_manifest')}"
              f"{'' if policy_carriers.get('carrier_manifest_gefunden') else ' (NICHT GEFUNDEN -- jede Datei traegt Policy)'}"
              f" | Policy-Traeger gesamt: {policy_carriers.get('traeger_dateien_gesamt')}")
