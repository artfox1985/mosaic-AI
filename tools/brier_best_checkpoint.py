"""Welche Checkpoint-Datei eines Trainingslaufs ist die Brier-beste? (Code-Review 2, Befund 1)

`train.py` schreibt `_brierbest` NUR, wenn die Brier-beste Epoche weder die letzte noch `best_epoch`
(val_combined-Auswahl) ist (`train.py`, Abschnitt "VALUE-optimalen Checkpoint speichern"). Faellt sie
mit `best_epoch` zusammen, IST `_best` das Brier-beste Netz; faellt sie auf die letzte Epoche, der
finale Stand. Eine Kette, die nach `_brierbest.onnx` sucht und sonst das finale Netz nimmt, gatet in
genau diesen Faellen das falsche (2026-10-02 bei `v34-b02` beobachtet: Brier-Minimum Epoche 1 =
`best_epoch`, kein `_brierbest`).

Dieses Werkzeug liest die Auswahl aus dem Trainings-Manifest (`epoch_history`, Felder
`value_val_brier` und `val_combined`) mit derselben Regel wie `train.py` (erstes Minimum, streng
kleiner) und prueft, dass die Datei liegt.

Gemittelter Stand (`train.py --weight-average`, PREREG_v35_window.md par.16): traegt das Manifest den
Block `weight_average` mit `value_val_brier` des GESPEICHERTEN `_avg`-Stands (gemessen nach der
BN-Neuschaetzung) und liegt dieser Wert STRENG unter dem Brier-Minimum der Einzelstaende, ist `_avg`
die Brier-beste Datei. Die Felder `avg_value_val_brier` je Epoche in `epoch_history` beschreiben
Zwischenstaende des Mittels, die nicht als Datei existieren; sie gehen darum nicht in die Wahl ein.
Diese Erweiterung greift NUR mit `--include-avg`: die Arm-Kette (tools/night_v35_arms_chain.sh,
Vorab-Test par.16) holt sich hier ausdruecklich den besten EINZELstand als Referenz und vergleicht den
`_avg` selbst dagegen; ohne den Schalter ist die Wahl darum fuer jedes Manifest unveraendert.

    python tools/brier_best_checkpoint.py v34-b02            # druckt den Modellnamen (z. B. v34-b02_best)
    python tools/brier_best_checkpoint.py v34-b02 --ext onnx # druckt den Pfad models/alphazero_<..>.onnx

Exit 0 mit dem Namen auf stdout; Exit 2, wenn Manifest, Brier-Verlauf oder Datei fehlen.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
MODELS_DIR = BASE_DIR / "models"


def first_argmin(values: list) -> int | None:
    """1-basierte Epoche des ersten Minimums (streng kleiner, wie train.py); None-Werte zaehlen nicht."""
    best, best_i = float("inf"), None
    for i, v in enumerate(values):
        if v is not None and v < best:
            best, best_i = v, i + 1
    return best_i


def choose_suffix(brier: list, combined: list, avg_brier: float | None = None) -> tuple[str, dict]:
    """Suffix der Brier-besten Datei ('' = finaler Stand, '_best', '_brierbest', '_avg') plus Begruendung.

    `avg_brier`: Brier des gespeicherten gemittelten Stands (Manifest-Block `weight_average`);
    None (Default) = Bestandsregel unveraendert. Gleichstand faellt auf den Einzelstand."""
    final_epoch = len(brier)
    brier_epoch = first_argmin(brier)
    best_epoch = first_argmin(combined)
    info = {"final_epoch": final_epoch, "brier_best_epoch": brier_epoch, "best_epoch": best_epoch}
    if brier_epoch is None:
        raise ValueError("kein value_val_brier im Verlauf")
    if avg_brier is not None:
        info["avg_value_val_brier"] = avg_brier
        if avg_brier < brier[brier_epoch - 1]:
            return "_avg", info
    if brier_epoch == final_epoch:
        return "", info
    if brier_epoch == best_epoch:
        return "_best", info
    return "_brierbest", info


def latest_manifest(name: str) -> Path | None:
    found = sorted(MODELS_DIR.glob(f"manifest_train_{name}_*.json"))
    return found[-1] if found else None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("name", help="Laufname (--name von train.py), z. B. v34-b02")
    ap.add_argument("--ext", choices=("pth", "onnx"), default=None,
                    help="statt des Modellnamens den Dateipfad models/alphazero_<name><suffix>.<ext> drucken")
    ap.add_argument("--include-avg", action="store_true",
                    help="den gemittelten Stand (_avg, Manifest-Block weight_average) mitwaehlen; "
                         "Default: nur Einzelstaende (Bestandsverhalten)")
    args = ap.parse_args(argv)
    man = latest_manifest(args.name)
    if man is None:
        print(f"FEHLT: kein models/manifest_train_{args.name}_*.json", file=sys.stderr)
        return 2
    manifest = json.loads(man.read_text(encoding="utf-8"))
    hist = manifest.get("epoch_history") or []
    avg_block = manifest.get("weight_average") or {}
    avg_brier = (avg_block.get("value_val_brier")
                 if (args.include_avg and avg_block.get("checkpoint")) else None)
    try:
        suffix, info = choose_suffix([e.get("value_val_brier") for e in hist], [e.get("val_combined") for e in hist],
                                     avg_brier)
    except ValueError as e:
        print(f"FEHLT: {e} ({man.name})", file=sys.stderr)
        return 2
    model = f"{args.name}{suffix}"
    path = MODELS_DIR / f"alphazero_{model}.{args.ext or 'pth'}"
    if not path.exists():
        print(f"FEHLT: {path} (Auswahl {info}, Manifest {man.name})", file=sys.stderr)
        return 2
    print(f"   Auswahl {info} aus {man.name}", file=sys.stderr)
    print(str(path.relative_to(BASE_DIR)).replace("\\", "/") if args.ext else model)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
