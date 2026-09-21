"""Waechter fuer die EINE Spec-Feld-Abbildung (Durchsicht 2026-09-21, par.8h Fund 6).

Anlass: die Abbildung Spec-Feld -> Env-Knopf stand zweimal wortgleich im Baum
(`server.py`, `tools/claude_play.py`), `tools/oracle_metrics.py` bezog sie ueber
einen Import aus `claude_play` -- und alle drei lagen ZWOELF Felder hinter
`net_mcts.rs::KNOWN_FIELDS`. Fuenf davon sind echte Suchknoepfe mit eigenem
Env-Namen (K6, Mondstapel-Skalierung, Rundenuebergang, Tiling-Stichentscheid).

Registriert wurde keine falsche Zahl: die neun A/B-Specs, die diese Felder
tragen, liefen ausnahmslos ueber `paired_gating`, also ueber den RUST-Leser, der
alle Felder kennt. Gefaehrlich war es fuer `oracle_metrics`, das A/B als zwei
Laeufe mit verschiedenen `--spec`-Dateien faehrt: ein nicht abgebildetes Feld
haette dort zwei IDENTISCHE Arme ergeben, ohne dass die Zahlen es zeigen.

**Der zentrale Test ist `test_every_known_field_is_decided`.** Er liest
`KNOWN_FIELDS` aus dem Rust-Code und verlangt fuer jedes Feld eine ENTSCHEIDUNG:
abgebildet oder ausdruecklich begruendet nicht abgebildet. Damit kann die Liste
nicht mehr still auseinanderlaufen -- genau das ist zwoelfmal passiert.

Bezeichner englisch (CLAUDE.md 2026-08-24), Inhaltssprache deutsch.
"""

import pathlib
import re
import sys
import unittest

_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))

from spec_env import (  # noqa: E402
    SPEC_TO_ENV,
    UNMAPPED_ON_PURPOSE,
    apply_spec_env,
    env_text,
)

_NET_MCTS = _ROOT / "engine" / "src" / "net_mcts.rs"
_KNOB_REGISTRY = _ROOT / "engine" / "src" / "knob_registry.rs"


def known_fields() -> list[str]:
    """`KNOWN_FIELDS` aus dem Rust-Quelltext -- die einzige Wahrheit darueber,
    welche Felder eine Spec tragen darf (`net_mcts.rs` weist alle anderen ab)."""
    text = _NET_MCTS.read_text(encoding="utf-8")
    m = re.search(r"const KNOWN_FIELDS: &\[&str\] = &\[(.*?)\];", text, re.S)
    assert m, "KNOWN_FIELDS nicht gefunden -- hat sich net_mcts.rs geaendert?"
    return re.findall(r'"([a-z0-9_]+)"', m.group(1))


class TheMappingTracksTheRustContract(unittest.TestCase):
    def test_known_fields_is_readable(self):
        """Ohne diese Lesestelle ist der Test unten eine leere Behauptung."""
        self.assertGreater(len(known_fields()), 20)

    def test_every_known_field_is_decided(self):
        """DER Test: jedes Spec-Feld ist abgebildet ODER begruendet ausgenommen."""
        undecided = [f for f in known_fields()
                     if f not in SPEC_TO_ENV and f not in UNMAPPED_ON_PURPOSE]
        self.assertEqual(undecided, [], (
            "Spec-Felder ohne Entscheidung: entweder in SPEC_TO_ENV aufnehmen "
            "oder in UNMAPPED_ON_PURPOSE mit Grund eintragen (spec_env.py)."
        ))

    def test_mapping_invents_no_fields(self):
        """Die andere Richtung: ein Env-Knopf fuer ein Feld, das Rust abweist,
        waere eine Spec, die gar nicht ladbar ist."""
        invented = sorted(set(SPEC_TO_ENV) - set(known_fields()))
        self.assertEqual(invented, [])

    def test_exceptions_are_real_fields(self):
        """Eine Ausnahme fuer ein Feld, das es nicht gibt, ist toter Text."""
        invented = sorted(set(UNMAPPED_ON_PURPOSE) - set(known_fields()))
        self.assertEqual(invented, [])

    def test_every_exception_carries_a_reason(self):
        for field, reason in UNMAPPED_ON_PURPOSE.items():
            with self.subTest(field=field):
                self.assertTrue(reason and len(reason) > 10)

    def test_env_names_exist_in_the_knob_registry(self):
        """Ein Env-Name mit Tippfehler setzt eine Variable, die niemand liest."""
        registry = _KNOB_REGISTRY.read_text(encoding="utf-8")
        missing = sorted(e for e in SPEC_TO_ENV.values() if f'"{e}"' not in registry)
        self.assertEqual(missing, [])

    def test_the_five_fields_from_par8h_are_mapped(self):
        """Der Anlassfall, festgenagelt: diese fuenf fehlten am 2026-09-21."""
        for field in ("special_unlock_w", "special_unlock_beta",
                      "moon_order_search_scale", "round_transition_leaf",
                      "net_tiling_tiebreak"):
            with self.subTest(field=field):
                self.assertIn(field, SPEC_TO_ENV)


class EnvText(unittest.TestCase):
    def test_a_list_becomes_comma_separated(self):
        self.assertEqual(env_text([1.0, 0.92, 0.0]), "1.0,0.92,0.0")

    def test_a_scalar_becomes_its_text(self):
        self.assertEqual(env_text(2), "2")
        self.assertEqual(env_text(0.25), "0.25")


class ApplySpecEnv(unittest.TestCase):
    def test_sets_mapped_fields(self):
        env = {}
        report = apply_spec_env({"score_utility_b": 20.0}, environ=env)
        self.assertEqual(env["MOSAIC_SCORE_UTILITY_B"], "20.0")
        self.assertEqual(report["gesetzt"], ["MOSAIC_SCORE_UTILITY_B=20.0"])

    def test_missing_fields_are_left_alone(self):
        """Aeltere Specs ohne die optionalen Felder bleiben unveraendert."""
        env = {}
        apply_spec_env({"score_utility_b": 1.0}, environ=env)
        self.assertNotIn("MOSAIC_NET_TILING_TIEBREAK", env)

    def test_deliberate_exception_is_reported_apart(self):
        report = apply_spec_env({"heuristik_variante": "hv1"}, environ={})
        self.assertEqual(report["unbekannt"], [])
        self.assertEqual(len(report["uebergangen"]), 1)
        self.assertIn("heuristik_variante", report["uebergangen"][0])

    def test_unknown_field_is_reported_loudly(self):
        """Der Fall, der still war: ein Feld ohne Knopf wirkt nicht."""
        report = apply_spec_env({"erfundenes_feld": 1}, environ={})
        self.assertEqual(report["unbekannt"], ["erfundenes_feld"])

    def test_existing_environment_wins_when_asked(self):
        """So macht es die GUI: ein selbst gesetzter Knopf sticht die Spec."""
        env = {"MOSAIC_SCORE_UTILITY_B": "99"}
        report = apply_spec_env({"score_utility_b": 20.0}, environ=env, respect_existing=True)
        self.assertEqual(env["MOSAIC_SCORE_UTILITY_B"], "99")
        self.assertEqual(report["gesetzt"], [])
        self.assertEqual(len(report["ueberstimmt"]), 1)

    def test_spec_wins_by_default(self):
        """Ohne `respect_existing` ist die Spec die Quelle -- so brauchen es
        die Werkzeuge, die je Lauf EINE Spec fahren."""
        env = {"MOSAIC_SCORE_UTILITY_B": "99"}
        apply_spec_env({"score_utility_b": 20.0}, environ=env)
        self.assertEqual(env["MOSAIC_SCORE_UTILITY_B"], "20.0")


class TheNineAbSpecsInTheTreeAreFullyMapped(unittest.TestCase):
    """Die Probe aufs Exempel: genau diese Dateien haetten zwei gleiche Arme
    ergeben, waere eine von ihnen durch `oracle_metrics` gelaufen."""

    def test_no_ab_spec_carries_an_unmapped_field(self):
        import json
        affected = {}
        for p in sorted((_ROOT / "models").glob("*.spec.json")):
            try:
                spec = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if not isinstance(spec, dict):
                continue
            undecided = [k for k in spec
                         if k not in SPEC_TO_ENV and k not in UNMAPPED_ON_PURPOSE]
            if undecided:
                affected[p.name] = undecided
        self.assertEqual(affected, {})
