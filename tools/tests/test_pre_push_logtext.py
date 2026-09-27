# -*- coding: utf-8 -*-
"""Code-Review 2026-09-26 #19: die Logtext-Herabstufung im pre-push-Haken
(`tools/hooks/pre-push`; nur `cargo build` statt `cargo test`, wenn in
engine/src/ allein Logtext und Kommentare geaendert wurden).

Zwei Befunde, je ein Test:

1. Jede geaenderte Zeile mit fuehrendem `"` galt als Logtext -- auch
   Match-Arme (`"x" => ...`) und `json!`-Schluessel (`"key": wert`), also
   Verhalten. Die Muster stehen jetzt als Variablen im Haken; der Test liest
   sie aus der Datei und fuehrt sie gegen Beispielzeilen aus (POSIX-Klasse
   `[[:space:]]` wird fuer Pythons `re` zu `\\s`; sonst sind die Muster in ERE
   und Python gleichbedeutend).
2. `LOGTEXT_ONLY` (bis 2026-09-27 `NUR_LOGTEXT`) wurde je Ref ueberschrieben, die letzte Ref gewann. Jetzt
   faellt das Urteil nach der Schleife ueber alle Refs -- textnah geprueft.

Kein sh-Aufruf: der Haken laeuft unter Git-sh, das in der Testumgebung nicht
verlaesslich im PATH liegt.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "hooks" / "pre-push"


def hook_pattern(text: str, name: str) -> re.Pattern:
    m = re.search(rf"^{name}='(.*)'$", text, re.MULTILINE)
    if m is None:
        raise AssertionError(f"{name} fehlt im Haken")
    return re.compile(m.group(1).replace("[[:space:]]", r"\s"))


def counts_as_logtext(line: str, line_pat: re.Pattern, string_pat: re.Pattern) -> bool:
    """Nachbau der Filterkette im Haken fuer EINE Diff-Zeile: sie zaehlt als
    Logtext, wenn eines der beiden `grep -vE`-Muster sie wegfiltert."""
    return bool(line_pat.search(line) or string_pat.search(line))


class LogtextPatterns(unittest.TestCase):
    def setUp(self):
        text = HOOK.read_text(encoding="utf-8")
        self.line_pat = hook_pattern(text, "LOGTEXT_LINE_PAT")
        self.string_pat = hook_pattern(text, "LOGTEXT_STRING_PAT")

    def check(self, line: str, expected: bool):
        self.assertIs(counts_as_logtext(line, self.line_pat, self.string_pat), expected, line)

    def test_log_lines_and_comments_count(self):
        self.check('+    log_event("Zug {x}", x);', True)
        self.check('-        // Kommentar', True)
        self.check('+    let _ = log_event(&mut log, "text");', True)

    def test_pure_string_continuation_counts(self):
        self.check('+            "Fortsetzung des Logtexts {name}",', True)
        self.check('-            "letzte Zeile");', True)
        self.check('+            "mit \\" escaptem Anfuehrungszeichen",', True)
        self.check('+            "ohne Komma"', True)

    def test_match_arms_and_json_keys_do_not_count(self):
        self.check('+        "stone" => Action::Stone,', False)
        self.check('+        "a" | "b" => 1,', False)
        self.check('+        "input_size": INPUT_SIZE,', False)
        self.check('+        "key": json!({"x": 1}),', False)

    def test_code_does_not_count(self):
        self.check('+    let x = 5;', False)
        self.check('+    "abc".to_string()', False)
        self.check('+            "offener String ohne Ende \\', False)


class VerdictOverAllRefs(unittest.TestCase):
    def setUp(self):
        self.text = HOOK.read_text(encoding="utf-8")

    def test_verdict_is_initialised_before_the_loop(self):
        loop = self.text.index("while read -r local_ref")
        self.assertLess(self.text.index('LOGTEXT_ONLY=""\n'), loop)
        self.assertLess(self.text.index('NON_LOGTEXT_REFS=""'), loop)

    def test_verdict_is_only_set_after_the_loop(self):
        loop_end = self.text.index("\ndone\n")
        sets = [m.start() for m in re.finditer(r'LOGTEXT_ONLY="yes"', self.text)]
        self.assertEqual(len(sets), 1)
        self.assertGreater(sets[0], loop_end, "Urteil je Ref gesetzt -- letzte Ref gewaenne")
        verdict = self.text[loop_end:sets[0]]
        self.assertIn('[ -z "$NON_LOGTEXT_REFS" ]', verdict)

    def test_patterns_are_used_in_the_filter(self):
        self.assertIn('grep -vE "$LOGTEXT_LINE_PAT"', self.text)
        self.assertIn('grep -vE "$LOGTEXT_STRING_PAT"', self.text)
        self.assertNotIn("grep -vE '^[+-][[:space:]]*\"'", self.text)


if __name__ == "__main__":
    unittest.main()
