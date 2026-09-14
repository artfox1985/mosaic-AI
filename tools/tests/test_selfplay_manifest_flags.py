# -*- coding: utf-8 -*-
"""Jedes argparse-Flag von self_play.py mit Verhaltenswirkung landet im Lauf-Manifest.

Anlass (2026-09-14): beim Bau des Streu-Knopfs `--return-order-random-p`
(PREREG_dome_return_order.md par.11a) fiel auf, dass der Manifest-Block in
self_play.py HAND-gepflegt ist -- genau wie `_cli_args` in train.py, fuer das es
seit dem Audit 2026-09-06 einen Waechter gibt
(tools/tests/test_train_manifest_flags.py). Fuer den ERZEUGUNGS-Treiber gab es
keinen, obwohl dort mehr auf dem Spiel steht: ein fehlendes Flag macht einen
Korpus im Nachhinein ununterscheidbar von einem ohne den Knopf, und der Korpus
ueberlebt die Generation. Der Kommentar an Ort und Stelle sagt das selbst
("Ohne dieses Feld waere ein fehlendes Flag ein stiller Default, und ein
v29-Korpus waere im Nachhinein nicht von einem v28-Korpus zu unterscheiden").

Dazu die zweite Haelfte, die train.py nicht hat: ein Erzeugungs-Knopf wirkt nur,
wenn seine Umgebungsvariable im WORKER gesetzt wird, VOR `import mosaic_rust`
(Rust liest sie per OnceLock). Wer das Flag ins Manifest eintraegt, aber nicht in
den Worker, bekommt das Gegenteil des stillen Defaults: das Manifest behauptet
Streuung, die nie stattfand. Beide Richtungen sind hier geprueft.

Rein textnah (Regex ueber self_play.py), kein Import, kein Wheel, kein Korpus --
pre-commit-tauglich.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SELF_PLAY = REPO / "self_play.py"

# Flag -> Grund, warum es NICHT als eigener Manifest-Schluessel erscheinen muss.
EXCEPTIONS = {
    "rtv": "Schluessel 'record_rtv' (Flagname und Manifest-Name weichen ab)",
    "value-only": "Sammelschalter; wirkt ueber pcr_full_prob, das im Manifest steht",
    "no-root-noise": "Negation von add_root_noise (Schluessel 'add_root_noise')",
    "depth": "laut eigener Hilfe 'Kompatibilitaet; ignoriert' -- keine Verhaltenswirkung",
}

# Flags, die eine MOSAIC_*-Variable im Worker setzen muessen. Der Wert ist der
# erwartete Variablenname; er muss VOR dem Rust-Import gesetzt werden.
WORKER_ENV = {
    "start-slot-random-p": "MOSAIC_START_SLOT_RANDOM_P",
    "return-order-random-p": "MOSAIC_RETURN_ORDER_RANDOM_P",
    "deviate-prob": "MOSAIC_DEVIATE_PROB",
    "excursion-prob": "MOSAIC_EXCURSION_PROB",
}


def argparse_flags(text: str) -> list[str]:
    return re.findall(r'add_argument\(\s*"--([a-z0-9\-]+)"', text)


def manifest_keys(text: str) -> set[str]:
    start = text.index("_write_run_manifest(version_name, run_timestamp, {")
    end = text.index("\n    })\n", start)  # Ende des Dict-Literals
    body = "\n".join(
        ln for ln in text[start:end].splitlines() if not ln.lstrip().startswith("#")
    )
    return set(re.findall(r'"([a-z_0-9]+)":', body))


class SelfPlayManifestFlags(unittest.TestCase):
    def setUp(self):
        self.text = SELF_PLAY.read_text(encoding="utf-8")

    def test_every_flag_is_in_manifest_or_named_exception(self):
        flags = argparse_flags(self.text)
        keys = manifest_keys(self.text)
        self.assertGreater(len(flags), 20, "argparse-Flags nicht gefunden -- Regex pruefen")
        self.assertGreater(len(keys), 20, "Manifest-Dict nicht gefunden -- Anker pruefen")
        missing = [
            f for f in flags if f.replace("-", "_") not in keys and f not in EXCEPTIONS
        ]
        self.assertEqual(
            missing,
            [],
            "Flags ohne Manifest-Schluessel (ins Dict bei `_write_run_manifest` eintragen "
            f"oder mit Grund in EXCEPTIONS): {missing}",
        )

    def test_exceptions_still_exist_as_flags(self):
        flags = set(argparse_flags(self.text))
        stale = sorted(f for f in EXCEPTIONS if f not in flags)
        self.assertEqual(stale, [], f"EXCEPTIONS nennt Flags, die es nicht mehr gibt: {stale}")

    def test_generation_knobs_reach_the_worker_environment(self):
        """Die zweite Richtung: das Manifest darf nichts behaupten, was im Worker fehlt."""
        flags = set(argparse_flags(self.text))
        for flag, env in WORKER_ENV.items():
            self.assertIn(flag, flags, f"Flag --{flag} fehlt in self_play.py")
            self.assertIn(
                f'os.environ["{env}"]',
                self.text,
                f"--{flag} steht im Manifest, setzt aber {env} nicht im Worker -- "
                "dann behauptet das Manifest eine Wirkung, die nie stattfand",
            )

    def test_worker_sets_environment_before_importing_the_engine(self):
        """Rust liest die Knoepfe per OnceLock: nach dem Import ist es zu spaet."""
        for env in WORKER_ENV.values():
            set_at = self.text.index(f'os.environ["{env}"]')
            import_at = self.text.index("import mosaic_rust as mr")
            self.assertLess(
                set_at,
                import_at,
                f"{env} wird erst NACH `import mosaic_rust` gesetzt -- OnceLock hat den "
                "Wert dann schon gelesen und der Knopf bleibt wirkungslos",
            )


if __name__ == "__main__":
    unittest.main()
