# -*- coding: utf-8 -*-
"""Jedes argparse-Flag von train.py mit Verhaltenswirkung landet im Manifest (`_cli_args`).

Anlass (Audit 2026-09-06): `_cli_args` in train.py ist eine HAND-gepflegte Auswahl
(train.py, Kommentar "ein neues Flag MUSS hier eingetragen werden"); acht
Verhaltens-Flags fehlten, darunter --wdl-label-smooth und --no-head-warmstart.
Ein fehlendes Flag ist ein stiller Default im Lauf-Manifest (CLAUDE.md, Regel
"Lauf-Manifest gegen Referenz"). Dieser Test haelt die argparse-Flags gegen die
Schluessel des Dicts; Ausnahmen stehen NAMENTLICH mit Grund in EXCEPTIONS.

Rein textnah (Regex ueber train.py), kein Import von train.py, kein Wheel, kein
Korpus -- pre-commit-tauglich (< 50 ms).
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TRAIN = REPO / "train.py"

# Flag -> Grund, warum es NICHT als eigener Manifest-Schluessel erscheinen muss.
EXCEPTIONS = {
    "no-early-stop": "Negation von early_stop (Schluessel 'early_stop')",
    "no-plot": "Negation von show_plot (Schluessel 'show_plot')",
    "no-snapshot": "Negation von snapshot (Schluessel 'snapshot')",
    "no-epoch-checkpoint": "Negation von epoch_checkpoint (Schluessel 'epoch_checkpoint')",
    "no-head-warmstart": "Negation von head_warmstart (Schluessel 'head_warmstart')",
    "resume": "Prozess-Schalter; das Manifest traegt die Fortsetzung im Block 'fortsetzung'",
}


def argparse_flags(text: str) -> list[str]:
    return re.findall(r'add_argument\(\s*"--([a-z0-9\-]+)"', text)


def manifest_keys(text: str) -> set[str]:
    start = text.index("_cli_args = {")
    end = text.index("\n    }\n", start)  # Ende des Dict-Literals
    # Mehrere Schluessel je Zeile sind ueblich ("name": ..., "load": ...); Kommentarzeilen raus.
    body = "\n".join(ln for ln in text[start:end].splitlines() if not ln.lstrip().startswith("#"))
    return set(re.findall(r'"([a-z_0-9]+)":', body))


class TrainManifestFlags(unittest.TestCase):
    def setUp(self):
        self.text = TRAIN.read_text(encoding="utf-8")

    def test_every_flag_is_in_manifest_or_named_exception(self):
        flags = argparse_flags(self.text)
        keys = manifest_keys(self.text)
        self.assertGreater(len(flags), 30, "argparse-Flags nicht gefunden -- Regex pruefen")
        self.assertGreater(len(keys), 30, "_cli_args nicht gefunden -- Anker pruefen")
        missing = [f for f in flags if f.replace("-", "_") not in keys and f not in EXCEPTIONS]
        self.assertEqual(missing, [], f"Flags ohne Manifest-Schluessel (in _cli_args eintragen oder mit Grund in EXCEPTIONS): {missing}")

    def test_exceptions_still_exist_as_flags(self):
        flags = set(argparse_flags(self.text))
        stale = sorted(f for f in EXCEPTIONS if f not in flags)
        self.assertEqual(stale, [], f"EXCEPTIONS nennt Flags, die es nicht mehr gibt: {stale}")

    def test_exception_targets_exist(self):
        keys = manifest_keys(self.text)
        for flag, reason in EXCEPTIONS.items():
            m = re.search(r"Schluessel '([a-z_]+)'", reason)
            if m:
                self.assertIn(m.group(1), keys, f"{flag}: Zielschluessel '{m.group(1)}' fehlt in _cli_args")


if __name__ == "__main__":
    unittest.main()
