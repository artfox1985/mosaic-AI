# -*- coding: utf-8 -*-
"""Trajektorien-Bootstrap (PREREG_v35_window.md par.12a, Arm v35-b03).

Prueft die reine Suchfunktion `trajectory_bootstrap_lookup`, ihre Datei-Variante
`trajectory_bootstrap_values`, den Margen-Bootstrap `margin_bootstrap_value`
(par.14, Arm v35-b04) und die Knopf-Leser
`file_cache_key._bootstrap_trajectory_horizon_key` / `_bootstrap_margin_scale_key` auf synthetischen Records im
Speicher, dazu die Varianten b11 bis b15 (par.19: lambda-Pfadmittel, Gegnerstellungen,
Mix mit dem Rollout, MOSAIC_TD_LAMBDA, Konfidenzgewicht) und ihre Knopf-Leser. Kein torch, keine Dateien, kein Korpus: beide Module laden ohne
Netz-Umgebung (`trajectory_bootstrap` nur Standardbibliothek, `file_cache_key`
importiert erst beim Aufruf von `per_file_cache_key`).
"""
from __future__ import annotations

import math
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "engine" / "py"))

from file_cache_key import (  # noqa: E402
    TD_LAMBDA_DEFAULT,
    _bootstrap_margin_scale_key,
    _bootstrap_trajectory_horizon_key,
    _bootstrap_trajectory_lambda_key,
    _bootstrap_trajectory_suffix_key,
    _bootstrap_variant_config,
    td_lambda_from_env,
    td_lambda_marker,
)
from trajectory_bootstrap import (  # noqa: E402
    add_trajectory_counts,
    confidence_bootstrap_value,
    confidence_weight,
    format_margin_counts,
    format_trajectory_counts,
    is_support_record,
    margin_bootstrap_value,
    mixed_bootstrap_value,
    root_child_q_gap,
    trajectory_bootstrap_lookup,
    trajectory_bootstrap_lookup_index,
    trajectory_bootstrap_values,
    trajectory_confidence_values,
    trajectory_lambda_lookup,
    trajectory_lambda_values,
)


def rec(player, rd, root_q=None, dice_phase=None, game_id="g1", root_child_q=None):
    """Synthetischer Record mit genau den Feldern, die die Suche liest."""
    r = {"game_id": game_id, "player": player, "state": {"round": rd}}
    if root_q is not None:
        r["root_q"] = root_q
    if dice_phase is not None:
        r["dice_phase"] = dice_phase
    if root_child_q is not None:
        r["root_child_q"] = root_child_q
    return r


def full_game(game_id="g1"):
    """Zwei Spieler, Runden 1-5, je Runde und Spieler zwei Records im Wechsel.

    root_q kodiert Spieler, Runde und Position: 0.p r i als Zahl, z. B. Spieler
    1, Runde 3, zweiter Record -> 0.132. So ist jeder Treffer eindeutig lesbar.
    """
    out = []
    for rd in range(1, 6):
        for i in range(2):
            for p in (0, 1):
                out.append(rec(p, rd, root_q=q(p, rd, i), game_id=game_id))
    return out


def q(p, rd, i):
    """root_q, das `full_game` dem i-ten Record (0/1) von Spieler p in Runde rd gibt."""
    return round(p * 0.1 + rd * 0.01 + i * 0.001 + 0.001, 4)


def index_of(game, p, rd, i):
    hits = [n for n, r in enumerate(game) if r["player"] == p and r["state"]["round"] == rd]
    return hits[i]


class LookupTest(unittest.TestCase):
    def test_first_record_of_same_side_k_rounds_later(self):
        g = full_game()
        self.assertEqual(trajectory_bootstrap_lookup(g, index_of(g, 0, 1, 0), 2), q(0, 3, 0))
        self.assertEqual(trajectory_bootstrap_lookup(g, index_of(g, 1, 1, 1), 2), q(1, 3, 0))
        self.assertEqual(trajectory_bootstrap_lookup(g, index_of(g, 0, 2, 0), 1), q(0, 3, 0))
        self.assertEqual(trajectory_bootstrap_lookup(g, index_of(g, 1, 1, 0), 3), q(1, 4, 0))

    def test_value_is_record_space_without_remap(self):
        g = [rec(0, 1, root_q=0.9), rec(0, 3, root_q=0.25)]
        self.assertEqual(trajectory_bootstrap_lookup(g, 0, 2), 0.25)

    def test_missing_root_q_is_skipped(self):
        g = full_game()
        del g[index_of(g, 0, 3, 0)]["root_q"]
        self.assertEqual(trajectory_bootstrap_lookup(g, index_of(g, 0, 1, 0), 2), q(0, 3, 1))

    def test_dice_phase_is_skipped(self):
        g = full_game()
        g[index_of(g, 0, 3, 0)]["dice_phase"] = True
        self.assertEqual(trajectory_bootstrap_lookup(g, index_of(g, 0, 1, 0), 2), q(0, 3, 1))
        # dice_phase False zaehlt wie fehlend: der Record ist zulaessig.
        g[index_of(g, 0, 3, 1)]["dice_phase"] = False
        g[index_of(g, 0, 3, 0)]["dice_phase"] = False
        self.assertEqual(trajectory_bootstrap_lookup(g, index_of(g, 0, 1, 0), 2), q(0, 3, 0))

    def test_horizon_is_an_upper_bound_not_an_exact_distance(self):
        # Runde 3 der Seite 0 ganz ohne root_q -> der erste zulaessige spaetere
        # Record liegt in Runde 4 (>= rd + k, nicht == rd + k).
        g = full_game()
        for i in range(2):
            del g[index_of(g, 0, 3, i)]["root_q"]
        self.assertEqual(trajectory_bootstrap_lookup(g, index_of(g, 0, 1, 0), 2), q(0, 4, 0))

    def test_opponent_records_are_never_taken(self):
        g = [rec(0, 1, root_q=0.5), rec(1, 3, root_q=0.9), rec(1, 4, root_q=0.8)]
        self.assertIsNone(trajectory_bootstrap_lookup(g, 0, 2))

    def test_game_end_closer_than_k_gives_none(self):
        g = full_game()
        # k = 2 ab Runde 4, k = 3 ab Runde 3, k = 1 in Runde 5: kein Record mehr.
        self.assertIsNone(trajectory_bootstrap_lookup(g, index_of(g, 0, 4, 0), 2))
        self.assertIsNone(trajectory_bootstrap_lookup(g, index_of(g, 1, 3, 1), 3))
        self.assertIsNone(trajectory_bootstrap_lookup(g, index_of(g, 0, 5, 0), 1))
        # Grenzfall: Runde 4 mit k = 1 findet Runde 5.
        self.assertEqual(trajectory_bootstrap_lookup(g, index_of(g, 0, 4, 1), 1), q(0, 5, 0))

    def test_only_later_records_count(self):
        # Ein FRUEHERER Record mit passender Runde (falsche Dateireihenfolge)
        # wird nicht genommen: gesucht wird nur hinter dem Index.
        g = [rec(0, 3, root_q=0.7), rec(0, 1, root_q=0.5)]
        self.assertIsNone(trajectory_bootstrap_lookup(g, 1, 2))

    def test_invalid_horizon_raises(self):
        g = full_game()
        for bad in (0, -1, 2.0, None):
            with self.assertRaises(ValueError):
                trajectory_bootstrap_lookup(g, 0, bad)

    def test_record_without_round_raises(self):
        g = [{"game_id": "g1", "player": 0, "state": {}}, rec(0, 3, root_q=0.4)]
        with self.assertRaises(ValueError):
            trajectory_bootstrap_lookup(g, 0, 2)


class FileLevelTest(unittest.TestCase):
    def test_games_are_grouped_by_game_id_in_file_order(self):
        a, b = full_game("a"), full_game("b")
        # b bekommt eigene Werte, damit eine Vermischung auffiele.
        for r in b:
            r["root_q"] = round(r["root_q"] + 0.5, 4)
        # Verschraenkt ablegen: die Gruppierung darf nicht an Zusammenhang haengen.
        mixed = [r for pair in zip(a, b) for r in pair]
        out = trajectory_bootstrap_values(mixed, 2)
        self.assertEqual(len(out), len(mixed))
        for n, r in enumerate(mixed):
            own = a if r["game_id"] == "a" else b
            expect = trajectory_bootstrap_lookup(own, own.index(r), 2)
            self.assertEqual(out[n], expect)
        first_a = mixed.index(a[0])
        first_b = mixed.index(b[0])
        self.assertEqual(out[first_a], q(0, 3, 0))
        self.assertEqual(out[first_b], round(q(0, 3, 0) + 0.5, 4))

    def test_counts_add_and_format(self):
        total = {}
        add_trajectory_counts(total, {1: [3, 0, 0], 4: [0, 2, 0]})
        add_trajectory_counts(total, None)
        add_trajectory_counts(total, {"1": [1, 0, 0], 5: [0, 0, 4]})
        self.assertEqual(total, {1: [4, 0, 0], 4: [0, 2, 0], 5: [0, 0, 4]})
        lines = format_trajectory_counts(total, 2)
        self.assertEqual(len(lines), 4)
        self.assertIn("Runde 1: 4 / 0 / 0", lines[1])


class MarginBootstrapTest(unittest.TestCase):
    """par.14 (Arm v35-b04): sigmoid(Endmarge des Ziehers / b)."""

    def test_zero_margin_is_one_half(self):
        self.assertEqual(margin_bootstrap_value(0.0, 20.0), 0.5)

    def test_plus_b_is_sigmoid_one(self):
        s1 = 1.0 / (1.0 + math.exp(-1.0))
        self.assertAlmostEqual(margin_bootstrap_value(20.0, 20.0), s1, places=12)
        self.assertAlmostEqual(margin_bootstrap_value(-20.0, 20.0), 1.0 - s1, places=12)
        self.assertAlmostEqual(margin_bootstrap_value(12.5, 12.5), s1, places=12)

    def test_sign_follows_the_mover(self):
        # Gleiche Partie, Endstand 50:30. Spieler 0 sieht +20, Spieler 1 -20;
        # Margen wie final_margin_of_step: scores_unclamped[p] - scores_unclamped[1-p].
        scores = [50.0, 30.0]
        for p in (0, 1):
            margin = scores[p] - scores[1 - p]
            value = margin_bootstrap_value(margin, 20.0)
            if p == 0:
                self.assertGreater(value, 0.5)
            else:
                self.assertLess(value, 0.5)
        self.assertAlmostEqual(margin_bootstrap_value(20.0, 20.0) + margin_bootstrap_value(-20.0, 20.0),
                               1.0, places=12)

    def test_large_margins_do_not_overflow(self):
        self.assertEqual(margin_bootstrap_value(1e6, 1.0), 1.0)
        self.assertEqual(margin_bootstrap_value(-1e6, 1.0), 0.0)

    def test_invalid_scale_or_margin_raises(self):
        for bad in (0.0, -5.0, float("nan"), float("inf")):
            with self.subTest(scale=bad), self.assertRaises(ValueError):
                margin_bootstrap_value(10.0, bad)
        with self.assertRaises(ValueError):
            margin_bootstrap_value(float("nan"), 20.0)

    def test_margin_counts_format(self):
        lines = format_margin_counts({2: [7, 0, 1]}, "20")
        self.assertIn("b = 20", lines[0])
        self.assertIn("Runde 2: 7 / 0 / 1", lines[1])


SOURCE = "MOSAIC_BOOTSTRAP_SOURCE"
HORIZON = "MOSAIC_BOOTSTRAP_HORIZON_ROUNDS"
SCALE = "MOSAIC_BOOTSTRAP_MARGIN_SCALE"


class KnobReaderTest(unittest.TestCase):
    def _read(self, **env):
        clean = {k: v for k, v in os.environ.items() if k not in ALL_BOOTSTRAP_KNOBS}
        clean.update(env)
        with mock.patch.dict(os.environ, clean, clear=True):
            return _bootstrap_trajectory_horizon_key()

    def _read_margin(self, **env):
        clean = {k: v for k, v in os.environ.items() if k not in ALL_BOOTSTRAP_KNOBS}
        clean.update(env)
        with mock.patch.dict(os.environ, clean, clear=True):
            return _bootstrap_margin_scale_key()

    def test_margin_source_valid_and_canonical(self):
        self.assertEqual(self._read_margin(**{SOURCE: "margin", SCALE: "20"}), "20")
        self.assertEqual(self._read_margin(**{SOURCE: "margin", SCALE: "20.0"}), "20")
        self.assertEqual(self._read_margin(**{SOURCE: "margin", SCALE: "12.50"}), "12.5")
        # Die beiden Leser schliessen sich aus.
        self.assertIsNone(self._read(**{SOURCE: "margin", SCALE: "20"}))
        self.assertIsNone(self._read_margin(**{SOURCE: "trajectory", HORIZON: "2"}))
        self.assertIsNone(self._read_margin())

    def test_margin_invalid_settings_raise(self):
        bad = [
            {SOURCE: "margin"},
            {SOURCE: "margin", SCALE: "0"},
            {SOURCE: "margin", SCALE: "-3"},
            {SOURCE: "margin", SCALE: "nan"},
            {SOURCE: "margin", SCALE: "inf"},
            {SOURCE: "margin", SCALE: "zwanzig"},
            {SOURCE: "margin", SCALE: "20", HORIZON: "2"},
            {SOURCE: "trajectory", HORIZON: "2", SCALE: "20"},
            {SCALE: "20"},
        ]
        for env in bad:
            for reader in (self._read, self._read_margin):
                with self.subTest(env=env, reader=reader.__name__), self.assertRaises(ValueError):
                    reader(**env)

    def test_unset_and_empty_mean_stock(self):
        self.assertIsNone(self._read())
        self.assertIsNone(self._read(**{SOURCE: "", HORIZON: ""}))

    def test_valid_settings(self):
        for k in (1, 2, 3):
            self.assertEqual(self._read(**{SOURCE: "trajectory", HORIZON: str(k)}), k)
        self.assertEqual(self._read(**{SOURCE: " Trajectory ", HORIZON: " 2 "}), 2)

    def test_invalid_settings_raise(self):
        bad = [
            {SOURCE: "rollout", HORIZON: "2"},
            {SOURCE: "trajectory"},
            {SOURCE: "trajectory", HORIZON: "0"},
            {SOURCE: "trajectory", HORIZON: "4"},
            {SOURCE: "trajectory", HORIZON: "two"},
            {SOURCE: "trajectory", HORIZON: "2.0"},
            {HORIZON: "2"},
        ]
        for env in bad:
            with self.subTest(env=env), self.assertRaises(ValueError):
                self._read(**env)


TRAJ_LAMBDA = "MOSAIC_BOOTSTRAP_TRAJ_LAMBDA"
TRAJ_OPPONENT = "MOSAIC_BOOTSTRAP_TRAJ_OPPONENT"
TRAJ_MIX = "MOSAIC_BOOTSTRAP_TRAJ_MIX"
TRAJ_CONF = "MOSAIC_BOOTSTRAP_TRAJ_CONF_SCALE"
TD = "MOSAIC_TD_LAMBDA"
ALL_BOOTSTRAP_KNOBS = (SOURCE, HORIZON, SCALE, TRAJ_LAMBDA, TRAJ_OPPONENT, TRAJ_MIX, TRAJ_CONF, TD)


def clean_env(**env):
    """Umgebung ohne alle Bootstrap-Knoepfe, plus `env`."""
    clean = {k: v for k, v in os.environ.items() if k not in ALL_BOOTSTRAP_KNOBS}
    clean.update(env)
    return mock.patch.dict(os.environ, clean, clear=True)


def mixed_game():
    """Zwei Seiten, verschraenkte Records mit Luecken: Ein-Aktion-Zuege ohne
    root_q, ein Wuerfelphasen-Record, unregelmaessige Zugfolge (Seite 0
    zieht zweimal hintereinander). root_q-Werte paarweise verschieden."""
    seq = [
        (0, 1, 0.61), (1, 1, 0.42), (0, 1, 0.58), (0, 1, None), (1, 1, 0.37),
        (0, 2, 0.66), (1, 2, 0.31), (1, 2, 0.29), (0, 2, 0.70), (1, 3, 0.25),
        (0, 3, 0.74), (1, 3, None), (0, 4, 0.81), (1, 4, 0.18), (0, 5, 0.88), (1, 5, 0.12),
    ]
    out = [rec(p, rd, root_q=q) for p, rd, q in seq]
    out[9]["dice_phase"] = True
    return out


def explicit_lambda(records, index, lam, opponent):
    """Unabhaengige Nachrechnung der Formel aus par.19.1/19.2."""
    player = records[index]["player"]
    terms = []
    for later in records[index + 1:]:
        if later.get("root_q") is None or later.get("dice_phase") is True:
            continue
        same = later["player"] == player
        if not same and not opponent:
            continue
        terms.append(later["root_q"] if same else 1.0 - later["root_q"])
    if not terms:
        return None
    if opponent:
        weights = [lam ** (h / 2.0) for h in range(len(terms))]
    else:
        weights = [lam ** j for j in range(len(terms))]
    return sum(w * v for w, v in zip(weights, terms)) / sum(weights)


class SupportRecordTest(unittest.TestCase):
    def test_support_predicate_matches_b03_conditions(self):
        self.assertTrue(is_support_record(rec(0, 1, root_q=0.5)))
        self.assertFalse(is_support_record(rec(0, 1)))
        self.assertFalse(is_support_record(rec(0, 1, root_q=0.5, dice_phase=True)))
        self.assertTrue(is_support_record(rec(0, 1, root_q=0.5, dice_phase=False)))

    def test_lookup_index_points_at_the_lookup_value(self):
        g = full_game()
        for i in range(len(g)):
            for k in (1, 2, 3):
                j = trajectory_bootstrap_lookup_index(g, i, k)
                v = trajectory_bootstrap_lookup(g, i, k)
                self.assertEqual(v, None if j is None else g[j]["root_q"])


class TrajectoryLambdaTest(unittest.TestCase):
    """par.19.1 (b11) und par.19.2 (b12)."""

    def test_weights_and_normalisation_by_hand(self):
        # Seite 0 hat hinter Index 0 drei eigene Stuetzstellen 0.6, 0.8, 0.4.
        g = [rec(0, 1, root_q=0.5), rec(0, 1, root_q=0.6), rec(1, 1, root_q=0.3),
             rec(0, 2, root_q=0.8), rec(0, 3, root_q=0.4)]
        want = (1.0 * 0.6 + 0.5 * 0.8 + 0.25 * 0.4) / (1.0 + 0.5 + 0.25)
        self.assertAlmostEqual(trajectory_lambda_lookup(g, 0, 0.5), want, places=15)
        self.assertAlmostEqual(trajectory_lambda_values(g, 0.5)[0], want, places=15)

    def test_opponent_mirror_and_half_move_weights_by_hand(self):
        # h = 1: eigene 0.6; h = 2: Gegner 0.3 -> 0.7; h = 3: eigene 0.8.
        g = [rec(0, 1, root_q=0.5), rec(0, 1, root_q=0.6), rec(1, 1, root_q=0.3),
             rec(0, 2, root_q=0.8)]
        lam = 0.49
        w = [1.0, lam ** 0.5, lam ** 1.0]
        want = (w[0] * 0.6 + w[1] * 0.7 + w[2] * 0.8) / sum(w)
        self.assertAlmostEqual(trajectory_lambda_lookup(g, 0, lam, opponent=True), want, places=15)
        self.assertAlmostEqual(trajectory_lambda_values(g, lam, opponent=True)[0], want, places=15)
        # Aus Sicht von Seite 1 (Index 2): nur noch 0.8 der Gegenseite -> 0.2.
        self.assertAlmostEqual(trajectory_lambda_values(g, lam, opponent=True)[2], 0.2, places=15)
        # Ohne Gegnerstellungen hat Seite 1 dort keine spaetere Stuetzstelle.
        self.assertIsNone(trajectory_lambda_values(g, lam)[2])

    def test_recursion_equals_reference_and_independent_formula(self):
        g = mixed_game()
        for lam in (0.0, 0.3, 0.5, 0.9, 1.0):
            for opponent in (False, True):
                fast = trajectory_lambda_values(g, lam, opponent=opponent)
                for i in range(len(g)):
                    ref = trajectory_lambda_lookup(g, i, lam, opponent=opponent)
                    ind = explicit_lambda(g, i, lam, opponent)
                    with self.subTest(lam=lam, opponent=opponent, i=i):
                        if ind is None:
                            self.assertIsNone(ref)
                            self.assertIsNone(fast[i])
                        else:
                            self.assertAlmostEqual(ref, ind, places=12)
                            self.assertAlmostEqual(fast[i], ind, places=12)

    def test_skips_missing_root_q_and_dice_phase(self):
        g = [rec(0, 1, root_q=0.5), rec(0, 1), rec(0, 2, root_q=0.9, dice_phase=True),
             rec(0, 3, root_q=0.4)]
        self.assertEqual(trajectory_lambda_lookup(g, 0, 0.5), 0.4)
        self.assertEqual(trajectory_lambda_values(g, 0.5)[0], 0.4)

    def test_lambda_zero_is_next_support_lambda_one_is_plain_mean(self):
        g = [rec(0, 1, root_q=0.5), rec(0, 1, root_q=0.6), rec(0, 2, root_q=0.8), rec(0, 3, root_q=0.1)]
        self.assertEqual(trajectory_lambda_values(g, 0.0)[0], 0.6)
        self.assertAlmostEqual(trajectory_lambda_values(g, 1.0)[0], (0.6 + 0.8 + 0.1) / 3, places=15)

    def test_without_later_support_is_none_fallback(self):
        g = full_game()
        last0 = max(n for n, r in enumerate(g) if r["player"] == 0)
        self.assertIsNone(trajectory_lambda_lookup(g, last0, 0.5))
        self.assertIsNone(trajectory_lambda_values(g, 0.5)[last0])
        # Mit Gegnerstellungen hat der letzte Record der Seite 0 noch den
        # spaeteren der Seite 1 (full_game: Seite 1 zieht zuletzt).
        self.assertIsNotNone(trajectory_lambda_values(g, 0.5, opponent=True)[last0])
        self.assertIsNone(trajectory_lambda_values(g, 0.5, opponent=True)[len(g) - 1])

    def test_games_are_kept_apart(self):
        a, b = full_game("a"), full_game("b")
        for r in b:
            r["root_q"] = round(1.0 - r["root_q"], 4)
        mixed = [r for pair in zip(a, b) for r in pair]
        out = trajectory_lambda_values(mixed, 0.5, opponent=True)
        for n, r in enumerate(mixed):
            own = a if r["game_id"] == "a" else b
            ref = trajectory_lambda_lookup(own, own.index(r), 0.5, opponent=True)
            if ref is None:
                self.assertIsNone(out[n])
            else:
                self.assertAlmostEqual(out[n], ref, places=12)

    def test_invalid_lambda_raises(self):
        g = full_game()
        for bad in (-0.1, 1.5, float("nan"), float("inf")):
            with self.subTest(lam=bad):
                with self.assertRaises(ValueError):
                    trajectory_lambda_values(g, bad)
                with self.assertRaises(ValueError):
                    trajectory_lambda_lookup(g, 0, bad)


class MixedBootstrapTest(unittest.TestCase):
    """par.19.3 (b13)."""

    def test_formula_and_edges(self):
        self.assertAlmostEqual(mixed_bootstrap_value(0.8, 0.4, 0.5), 0.6, places=15)
        self.assertAlmostEqual(mixed_bootstrap_value(0.8, 0.4, 0.25), 0.25 * 0.8 + 0.75 * 0.4, places=15)
        self.assertEqual(mixed_bootstrap_value(0.8, 0.4, 1.0), 0.8)
        self.assertEqual(mixed_bootstrap_value(0.8, 0.4, 0.0), 0.4)

    def test_invalid_mix_raises(self):
        for bad in (-0.01, 1.01, float("nan")):
            with self.subTest(mix=bad), self.assertRaises(ValueError):
                mixed_bootstrap_value(0.5, 0.5, bad)


class ConfidenceBootstrapTest(unittest.TestCase):
    """par.19.5 (b15)."""

    def test_gap_of_best_and_second_best(self):
        self.assertAlmostEqual(root_child_q_gap({"root_child_q": [0.40, 0.55, 0.52, 0.1]}), 0.03, places=15)
        self.assertEqual(root_child_q_gap({"root_child_q": [0.5, 0.5, 0.2]}), 0.0)
        self.assertIsNone(root_child_q_gap({"root_child_q": [0.7]}))
        self.assertIsNone(root_child_q_gap({}))

    def test_weight_is_clipped(self):
        self.assertEqual(confidence_weight(0.0, 0.01), 0.0)
        self.assertAlmostEqual(confidence_weight(0.005, 0.01), 0.5, places=15)
        self.assertEqual(confidence_weight(0.02, 0.01), 1.0)
        for bad in (0.0, -1.0, float("nan"), float("inf")):
            with self.subTest(scale=bad), self.assertRaises(ValueError):
                confidence_weight(0.01, bad)

    def test_value_blends_later_q_toward_outcome(self):
        self.assertAlmostEqual(confidence_bootstrap_value(0.7, 0.25, 1.0), 0.25 * 0.7 + 0.75, places=15)
        self.assertEqual(confidence_bootstrap_value(0.7, 1.0, 0.0), 0.7)
        self.assertEqual(confidence_bootstrap_value(0.7, 0.0, 0.0), 0.0)

    def test_file_level_uses_the_later_record_of_the_b03_lookup(self):
        g = [rec(0, 1, root_q=0.5, root_child_q=[0.5, 0.49]),
             rec(0, 1, root_q=0.6, root_child_q=[0.6, 0.1]),          # gleiche Runde: nicht der Treffer
             rec(0, 2, root_q=0.7, root_child_q=[0.70, 0.695, 0.2]),  # Treffer fuer k = 1, Abstand 0.005
             rec(0, 3, root_q=0.8, root_child_q=[0.8]),               # ein Eintrag: w = 1
             rec(0, 4, root_q=0.9, root_child_q=[0.9, 0.9])]          # Gleichstand: w = 0
        out = trajectory_confidence_values(g, 1, 0.01)
        self.assertEqual(out[0][0], 0.7)
        self.assertAlmostEqual(out[0][1], 0.5, places=12)
        self.assertEqual(out[2], (0.8, 1.0))
        self.assertEqual(out[3], (0.9, 0.0))
        self.assertIsNone(out[4])
        # Die Treffer sind genau die von b03.
        values = trajectory_bootstrap_values(g, 1)
        self.assertEqual([None if o is None else o[0] for o in out], values)

    def test_missing_root_child_q_on_the_later_record_raises(self):
        g = [rec(0, 1, root_q=0.5, root_child_q=[0.5, 0.4]), rec(0, 2, root_q=0.7)]
        with self.assertRaises(ValueError):
            trajectory_confidence_values(g, 1, 0.01)


class StockPathTest(unittest.TestCase):
    """Standardweg bitgleich: ohne Varianten-Knoepfe liefern die Leser genau
    den Bestand (kein Zusatz, keine lambda-Quelle, TD_LAMBDA 0.5, kein
    TD-Marker), und die b03-Werte kommen unveraendert aus der Index-Suche."""

    def test_no_knobs_means_stock(self):
        with clean_env():
            self.assertIsNone(_bootstrap_variant_config())
            self.assertEqual(_bootstrap_trajectory_suffix_key(), "")
            self.assertIsNone(_bootstrap_trajectory_lambda_key())
            self.assertIsNone(_bootstrap_trajectory_horizon_key())
            self.assertEqual(td_lambda_from_env(), 0.5)
            self.assertEqual(str(td_lambda_from_env()), "0.5")
            self.assertIsNone(td_lambda_marker(td_lambda_from_env()))
        self.assertEqual(TD_LAMBDA_DEFAULT, 0.5)

    def test_plain_trajectory_has_no_suffix_and_unchanged_values(self):
        with clean_env(**{SOURCE: "trajectory", HORIZON: "1"}):
            self.assertEqual(_bootstrap_trajectory_suffix_key(), "")
            cfg = _bootstrap_variant_config()
        self.assertEqual(cfg, {"source": "trajectory", "horizon": 1, "mix": None, "conf_scale": None,
                               "traj_lambda": None, "opponent": False, "margin_scale": None})
        g = full_game()
        self.assertEqual(trajectory_bootstrap_values(g, 1)[index_of(g, 0, 2, 0)], q(0, 3, 0))


class VariantKnobReaderTest(unittest.TestCase):
    def test_lambda_source_default_and_canonical(self):
        with clean_env(**{SOURCE: "trajectory_lambda"}):
            self.assertEqual(_bootstrap_trajectory_lambda_key(), "l0.5")
            self.assertIsNone(_bootstrap_trajectory_horizon_key())
            self.assertIsNone(_bootstrap_margin_scale_key())
            self.assertEqual(_bootstrap_variant_config()["traj_lambda"], 0.5)
        with clean_env(**{SOURCE: "trajectory_lambda", TRAJ_LAMBDA: "0.50"}):
            self.assertEqual(_bootstrap_trajectory_lambda_key(), "l0.5")
        with clean_env(**{SOURCE: "trajectory_lambda", TRAJ_LAMBDA: "0.7", TRAJ_OPPONENT: "1"}):
            self.assertEqual(_bootstrap_trajectory_lambda_key(), "l0.7_opp1")
            self.assertTrue(_bootstrap_variant_config()["opponent"])
        with clean_env(**{SOURCE: "trajectory_lambda", TRAJ_OPPONENT: "0"}):
            self.assertEqual(_bootstrap_trajectory_lambda_key(), "l0.5")
        with clean_env(**{SOURCE: "trajectory_lambda", TRAJ_LAMBDA: "1"}):
            self.assertEqual(_bootstrap_trajectory_lambda_key(), "l1")

    def test_mix_and_conf_suffixes(self):
        with clean_env(**{SOURCE: "trajectory", HORIZON: "1", TRAJ_MIX: "0.5"}):
            self.assertEqual(_bootstrap_trajectory_suffix_key(), "_mix0.5")
            self.assertEqual(_bootstrap_trajectory_horizon_key(), 1)
            self.assertEqual(_bootstrap_variant_config()["mix"], 0.5)
        with clean_env(**{SOURCE: "trajectory", HORIZON: "1", TRAJ_CONF: "0.0116"}):
            self.assertEqual(_bootstrap_trajectory_suffix_key(), "_conf0.0116")
            self.assertEqual(_bootstrap_variant_config()["conf_scale"], 0.0116)
        with clean_env(**{SOURCE: "trajectory", HORIZON: "2", TRAJ_CONF: "0.020"}):
            self.assertEqual(_bootstrap_trajectory_suffix_key(), "_conf0.02")

    def test_invalid_variant_settings_raise(self):
        bad = [
            {TRAJ_LAMBDA: "0.5"},
            {TRAJ_OPPONENT: "1"},
            {TRAJ_MIX: "0.5"},
            {TRAJ_CONF: "0.01"},
            {SOURCE: "trajectory_lambda", HORIZON: "1"},
            {SOURCE: "trajectory_lambda", TRAJ_MIX: "0.5"},
            {SOURCE: "trajectory_lambda", TRAJ_CONF: "0.01"},
            {SOURCE: "trajectory_lambda", SCALE: "20"},
            {SOURCE: "trajectory_lambda", TRAJ_LAMBDA: "1.5"},
            {SOURCE: "trajectory_lambda", TRAJ_LAMBDA: "-0.1"},
            {SOURCE: "trajectory_lambda", TRAJ_LAMBDA: "nan"},
            {SOURCE: "trajectory_lambda", TRAJ_OPPONENT: "2"},
            {SOURCE: "trajectory", HORIZON: "1", TRAJ_LAMBDA: "0.5"},
            {SOURCE: "trajectory", HORIZON: "1", TRAJ_OPPONENT: "1"},
            {SOURCE: "trajectory", HORIZON: "1", TRAJ_MIX: "0.5", TRAJ_CONF: "0.01"},
            {SOURCE: "trajectory", HORIZON: "1", TRAJ_MIX: "1.2"},
            {SOURCE: "trajectory", HORIZON: "1", TRAJ_CONF: "0"},
            {SOURCE: "trajectory", HORIZON: "1", TRAJ_CONF: "-0.01"},
            {SOURCE: "trajectory", TRAJ_MIX: "0.5"},
            {SOURCE: "margin", SCALE: "20", TRAJ_MIX: "0.5"},
            {SOURCE: "margin", SCALE: "20", TRAJ_LAMBDA: "0.5"},
        ]
        readers = (_bootstrap_trajectory_horizon_key, _bootstrap_trajectory_suffix_key,
                   _bootstrap_trajectory_lambda_key, _bootstrap_margin_scale_key, _bootstrap_variant_config)
        for env in bad:
            for reader in readers:
                with self.subTest(env=env, reader=reader.__name__):
                    with clean_env(**env), self.assertRaises(ValueError):
                        reader()


class TdLambdaKnobTest(unittest.TestCase):
    """par.19.4 (b14): MOSAIC_TD_LAMBDA."""

    def test_values_and_marker(self):
        with clean_env(**{TD: "0.7"}):
            self.assertEqual(td_lambda_from_env(), 0.7)
        with clean_env(**{TD: "0.50"}):
            self.assertEqual(td_lambda_from_env(), 0.5)
        with clean_env(**{TD: " 1 "}):
            self.assertEqual(td_lambda_from_env(), 1.0)
        self.assertEqual(td_lambda_marker(0.7), "tdlambda0.7")
        self.assertEqual(td_lambda_marker(1.0), "tdlambda1")
        self.assertIsNone(td_lambda_marker(0.5))

    def test_invalid_values_raise(self):
        for bad in ("0", "-0.2", "1.1", "nan", "inf", "hoch"):
            with self.subTest(value=bad), clean_env(**{TD: bad}), self.assertRaises(ValueError):
                td_lambda_from_env()


if __name__ == "__main__":
    unittest.main()
