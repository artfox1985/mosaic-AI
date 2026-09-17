"""Waechter: die Merkmals-FORMEL und die Merkmals-QUELLE stehen in BEIDEN
Cache-Schluesseln -- im Block-Schluessel (`engine/py/file_cache_key.py`) und im
Fenster-Schluessel (`corpus_dataset.window_cache_key`).

DER BEFUND, der das ausgeloest hat (PREREG_rust_data_layer.md par.9/par.9a,
Nutzer-Entscheid 2026-09-17 "Weg (1)"): der A2-Phantom-Fix vom 2026-09-12
(Commit 2a0cf4bf) hat `provocation::remaining_colors` geaendert. Davon haengen
zwei GESPEICHERTE Groessen ab, `cell_reachable_mask` (Planes-Kanal 76) und
`col_f_max` (6 Flachvektor-Werte). Der Python-Zwilling LIEST sie aus dem Record,
`features.rs` RECHNET sie neu -- auf Records von vor dem 2026-09-12 sind die
beiden Bauer damit nicht mehr bit-identisch (2 von 300 Zustaenden; auf frischen
Records 0 von 600). `MOSAIC_FEATURES_FROM_RUST` entscheidet, welcher Bauer den
Inhalt der gecachten Planes liefert, stand aber in KEINEM Schluessel, und
Bloecke werden MEMOISIERT: ein Arm erbte die Semantik dessen, der den Block
zuerst gebaut hat.

WAS DIESER TEST FESTNAGELT:
  (a) beide Schluessel aendern sich, wenn `config.FEATURE_FORMULA_VERSION`
      hochgezogen wird (die Regel dazu steht in `config.py`);
  (b) beide Schluessel unterscheiden `MOSAIC_FEATURES_FROM_RUST=1` von
      ungesetzt -- und zwar aus der UMGEBUNG gelesen, ohne dass ein Aufrufer
      etwas durchreichen muss (Schwesterregel:
      `test_cache_key_knobs_are_env_coupled.py`).

Warum BEIDE: ein Knopf, der nur in einem der zwei Schluessel steht, ist der
Fehler vom 2026-09-14 -- b03 trainierte mit, validierte ohne die
Spezialfeld-Kanaele.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "engine", "py"))

import config  # noqa: E402
import corpus_dataset  # noqa: E402
from file_cache_key import per_file_cache_key  # noqa: E402

FILES = ["selfplay_featfmt_a.pkl", "selfplay_featfmt_b.pkl"]
WINDOW_KW = dict(value_target_variant="nortv", encoder="2d",
                 conjunction_head=False)
BLOCK_KW = dict(value_target_variant="nortv", encoder="2d",
                conjunction_head=False, bootstrap_native=True)

# Knoepfe, die beide Schluessel sonst mitfaerben -- fuer den Test ausgeraeumt,
# damit die Aussage nur an der Formelversion bzw. der Merkmalsquelle haengt.
NEUTRAL = ("MOSAIC_CARRIER_MANIFEST", "MOSAIC_MOON_TARGET_SOURCE",
           "MOSAIC_SPECIAL_PLANES_OFF", "MOSAIC_DATA_EXCLUDE",
           "MOSAIC_FEATURES_FROM_RUST")


class _CleanEnv:
    """Setzt die datenwirksamen Knoepfe auf einen definierten Stand und stellt
    den Bestand danach wieder her (kein Seiteneffekt auf andere Tests)."""

    def __init__(self, **values):
        self.values = values
        self.vorher = {}

    def __enter__(self):
        for name in NEUTRAL:
            self.vorher[name] = os.environ.get(name)
            os.environ.pop(name, None)
        for name, value in self.values.items():
            self.vorher.setdefault(name, os.environ.get(name))
            os.environ[name] = value
        return self

    def __exit__(self, *_):
        for name, value in self.vorher.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        return False


def _block_key():
    return per_file_cache_key(FILES[0], **BLOCK_KW)


def _window_key():
    return corpus_dataset.window_cache_key("data", FILES, **WINDOW_KW).key


class TestFeatureFormulaVersionInBothKeys(unittest.TestCase):
    def test_version_bump_changes_both_keys(self):
        """(a) Eine hochgezogene Formelversion trennt alte von neuer Semantik."""
        original = config.FEATURE_FORMULA_VERSION
        with _CleanEnv():
            vorher_block, vorher_window = _block_key(), _window_key()
            try:
                config.FEATURE_FORMULA_VERSION = original + "-TESTBUMP"
                nachher_block, nachher_window = _block_key(), _window_key()
            finally:
                config.FEATURE_FORMULA_VERSION = original
            again_block, again_window = _block_key(), _window_key()
        self.assertNotEqual(
            vorher_block, nachher_block,
            "Der BLOCK-Schluessel ignoriert FEATURE_FORMULA_VERSION -- eine "
            "Formelaenderung an einer gespeicherten Groesse (cell_reachable_mask, "
            "col_f_max) wuerde still die Alt-Bloecke adressieren.")
        self.assertNotEqual(
            vorher_window, nachher_window,
            "Der FENSTER-Schluessel ignoriert FEATURE_FORMULA_VERSION -- der "
            "Monolith eines Arms mit neuer Formel traegt dann den Namen des "
            "alten (Fehlerklasse vom 2026-09-14, b02s Monolith).")
        self.assertEqual((again_block, again_window),
                         (vorher_block, vorher_window),
                         "Der Schluessel ist nach dem Zuruecksetzen nicht wieder "
                         "derselbe -- der Test hat einen Seiteneffekt.")

    def test_features_from_rust_changes_both_keys(self):
        """(b) Der Bauer-Schalter trennt die beiden Semantiken, aus der Umgebung
        gelesen -- kein Aufrufer muss ihn durchreichen."""
        with _CleanEnv():
            ohne_block, ohne_window = _block_key(), _window_key()
        with _CleanEnv(MOSAIC_FEATURES_FROM_RUST="1"):
            mit_block, mit_window = _block_key(), _window_key()
        self.assertNotEqual(
            ohne_block, mit_block,
            "MOSAIC_FEATURES_FROM_RUST faerbt den BLOCK-Schluessel nicht. "
            "Bloecke werden memoisiert: ein Arm erbt sonst die Semantik "
            "dessen, der den Block zuerst gebaut hat (par.9a).")
        self.assertNotEqual(
            ohne_window, mit_window,
            "MOSAIC_FEATURES_FROM_RUST faerbt den FENSTER-Schluessel nicht -- "
            "zwei Datensaetze unter einem Monolith-Namen.")

    def test_marker_is_in_the_window_material(self):
        """Der Marker steht woertlich im Schluesselmaterial: ein Mensch, der
        einen Cache-Namen nachrechnet, muss ihn sehen koennen."""
        with _CleanEnv():
            material_record = corpus_dataset.window_cache_key(
                "data", FILES, **WINDOW_KW).material
        with _CleanEnv(MOSAIC_FEATURES_FROM_RUST="1"):
            material_rust = corpus_dataset.window_cache_key(
                "data", FILES, **WINDOW_KW).material
        self.assertIn("+featfmt_" + config.FEATURE_FORMULA_VERSION, material_record)
        self.assertIn("+featsrc_record", material_record)
        self.assertIn("+featsrc_rust", material_rust)


if __name__ == "__main__":
    unittest.main()
