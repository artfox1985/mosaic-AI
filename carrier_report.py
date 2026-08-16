"""Policy-Traegersatz eines Trainingslaufs aufloesen und protokollieren.

Eigenes Modul, weil `train.py` die Modularitaetsschwelle aus CLAUDE.md bereits
reisst -- der Konventions-Waechter hat das Wachstum zu Recht geblockt.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "engine" / "py"))
from config import DATA_DIR


def policy_carrier_report(all_files, selfplay_filename_re) -> dict:
    """Loest die Policy-TRAEGER-Regel schon beim Manifest-Schreiben auf und
    zaehlt je Praefix, wie viele Dateien tatsaechlich Policy-Ziele beitragen.

    WARUM DAS HIER STEHT (Befund 2026-08-16): der gesamte Ownership-Korpus war
    in SIEBEN Trainingslaeufen policy-maskiert, ohne dass es irgendwo sichtbar
    wurde -- die Korpusdateien sind weder im Traeger-Manifest gelistet noch
    beginnen sie mit `WDL_GENERATOR_PREFIXES`, also galt `pol_w = 0.0`
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
        from neural_net import _is_policy_carrier, WDL_GENERATOR_PREFIXES
    except ImportError:                                   # defensiv: nie den Lauf blockieren
        return {"error": "neural_net._is_policy_carrier nicht importierbar"}

    mf_name = os.environ.get("MOSAIC_CARRIER_MANIFEST", "policy_carrier_manifest_v20.json")
    mf_path = Path(DATA_DIR) / mf_name
    carrier_set, carrier_prefixes = None, None
    if mf_path.exists():
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
        m = selfplay_filename_re.match(name)
        prefix = m.group("prefix") if m else "_unmatched"
        ist = _is_policy_carrier(name, carrier_set, carrier_prefixes,
                                 name.startswith(WDL_GENERATOR_PREFIXES))
        je_praefix[prefix] = je_praefix.get(prefix, 0) + (1 if ist else 0)
        traeger_gesamt += 1 if ist else 0
    return {
        "carrier_manifest": mf_name,
        "carrier_manifest_gefunden": mf_path.exists(),
        "carrier_prefixes": carrier_prefixes,
        "gelistete_dateien": len(carrier_set) if carrier_set is not None else None,
        "traeger_dateien_gesamt": traeger_gesamt,
        "traeger_dateien_je_praefix": je_praefix,
        "data_exclude": os.environ.get("MOSAIC_DATA_EXCLUDE"),
    }
