# -*- coding: utf-8 -*-
"""Grund der Ungewertetheit im Historien-Eintrag (Nutzer-Meldung 2026-09-09:
das Endwertungsfenster sagte "ungewertet (KI-Tipps genutzt)" in einer Partie
ohne einen einzigen Tipp).

`record_unrated` schrieb `hints_used: True` fest, egal warum nicht gewertet
wurde -- die Falschaussage stand damit dauerhaft in der Profil-Historie, nicht
nur im Fenster. Geprueft wird, dass der Grund mitwandert und `hints_used` ihm
folgt.

ISOLATION: die Pfade werden NACH dem Import umgebogen, nicht ueber
MOSAIC_PROFILES_PATH. Die Variable wird beim LADEN des Moduls gelesen
(player_profiles.py:51) -- in einem `unittest discover`-Lauf hat ein anderes
Testmodul player_profiles laengst importiert, das os.environ hier kommt zu
spaet und der Test schreibt in die echte player_profiles.json des Nutzers.
Genau das ist am 2026-09-09 einmal passiert (vier Testprofile in der Live-
Datei); die Variable bleibt richtig fuer eigene PROZESSE, taugt aber nicht
innerhalb eines gemeinsamen Testlaufs."""
import json
import pathlib
import sys
import tempfile
import unittest
import uuid

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import player_profiles as pp  # noqa: E402


class UnratedReasonTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmpdir = tempfile.TemporaryDirectory(prefix="mosaic_profiles_test_")
        cls._orig = (pp.PROFILES_PATH, pp.BAK_PATH)
        tmp = pathlib.Path(cls._tmpdir.name) / "player_profiles.json"
        tmp.write_text(json.dumps({"profiles": {}}), encoding="utf-8")
        pp.PROFILES_PATH = tmp
        pp.BAK_PATH = tmp.with_name(tmp.name + ".bak")

    @classmethod
    def tearDownClass(cls):
        pp.PROFILES_PATH, pp.BAK_PATH = cls._orig
        cls._tmpdir.cleanup()

    def setUp(self):
        # Sicherheitsnetz: schreibt der Test doch in den Projektbaum, faellt es
        # HIER auf und nicht erst in der Live-Datei.
        self.assertNotEqual(pp.PROFILES_PATH.parent, ROOT,
                            "Test wuerde in die echte player_profiles.json schreiben")
        self.pid = pp.create_profile(f"Testprofil_{uuid.uuid4().hex[:6]}")["id"]

    def _record(self, reason):
        return pp.record_unrated(self.pid, "v26-b01@400", 1388.9, True, 1.0,
                                 reason=reason)

    def test_hints_reason_sets_hints_used(self):
        entry = self._record(pp.UNRATED_HINTS)
        self.assertEqual(entry["unrated_reason"], pp.UNRATED_HINTS)
        self.assertTrue(entry["hints_used"])
        self.assertFalse(entry["rated"])

    def test_anchor_reason_does_not_claim_hints(self):
        entry = self._record(pp.UNRATED_NO_DIRECT_ANCHOR)
        self.assertEqual(entry["unrated_reason"], pp.UNRATED_NO_DIRECT_ANCHOR)
        self.assertFalse(entry["hints_used"])
        self.assertFalse(entry["rated"])

    def test_default_reason_stays_hints_for_old_callers(self):
        entry = pp.record_unrated(self.pid, "Gegner", 1000.0, False, 0.0)
        self.assertEqual(entry["unrated_reason"], pp.UNRATED_HINTS)

    def test_rating_is_untouched(self):
        before = pp.get_profile(self.pid)["rating"]
        entry = self._record(pp.UNRATED_NO_DIRECT_ANCHOR)
        self.assertEqual(entry["delta"], 0.0)
        self.assertEqual(entry["rating_before"], entry["rating_after"])
        self.assertEqual(pp.get_profile(self.pid)["rating"], before)


if __name__ == "__main__":
    unittest.main()
