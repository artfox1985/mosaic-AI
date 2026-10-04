# -*- coding: utf-8 -*-
"""Tests fuer tools/probes/state_novelty_probe.py (evaluations/PREREG_asymmetric_selfplay.md par.5d2).

Synthetische Mini-Records in der Form von `state_to_json` (serialize.rs: `round`, `phase`, `players[p].dome_grid`
als 3x3-Liste von Platten `{id, bonus, spaces}`, `dome_display`): Kanonisierung (Rotation, Feinheiten),
JS-Distanz, sockelfremde Zustaende, Rauschbezug Sockel-Dateien 1-5 gegen 6-10, Lesen einer Klasse mit
Wuerfel-Seite.
"""
from __future__ import annotations

import math
import os
import time
import sys
import unittest
from collections import Counter
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "probes"))

# Umgebung VOR dem Import des Werkzeugs: weder Import noch Tests duerfen MOSAIC_*-Variablen hinterlassen
# (sonst sehen spaetere Cache-Schluessel-Tests im selben Prozess einen anderen Default, file_cache_key.py)
MOSAIC_ENV_BEFORE = {k: v for k, v in os.environ.items() if k.startswith("MOSAIC_")}

import state_novelty_probe as snp  # noqa: E402

# Katalog-Lagen (ungedreht) zweier Platten: drei Farbfelder plus ein Sonderfeld
LAYOUTS = {
    1: [("COLOR", "red"), ("COLOR", "blue"), ("COLOR", "green"), ("SPECIAL", None)],
    2: [("COLOR", "yellow"), ("WILD", None), ("COLOR", "black"), ("COLOR", "red")],
    3: [("COLOR", "blue"), ("COLOR", "red"), ("WILD", None), ("COLOR", "green")],
    4: [("SPECIAL", None), ("COLOR", "black"), ("COLOR", "blue"), ("COLOR", "yellow")],
    5: [("COLOR", "green"), ("COLOR", "yellow"), ("COLOR", "red"), ("WILD", None)],
}


def tile(tid, deg=0, fills=None):
    lay = LAYOUTS[tid]
    lay = [lay[i] for i in snp.ROTATION_INDICES[deg]]
    fills = fills or [None] * 4
    return {"id": tid, "bonus": 0, "spaces": [{"type": t, "color": c, "filled": f, "locked": t == "SPECIAL"}
                                             for (t, c), f in zip(lay, fills)]}


def grid(placed):
    """placed: {(slot_row, slot_col): tile}"""
    return [[placed.get((r, c)) for c in range(3)] for r in range(3)]


def state(rnd, phase, g0, g1, display=(1, 2, 3, 4, 5)):
    return {"round": rnd, "phase": phase, "dome_display": [tile(t) for t in display],
            "pending_stack_draw": [], "players": [{"dome_grid": grid(g0)}, {"dome_grid": grid(g1)}]}


def record(gid, st, player, winner=0, **extra):
    r = {"game_id": gid, "state": st, "player": player, "winner": winner, "policy": [], "valid_actions": []}
    r.update(extra)
    return r


def game_records(gid, start0, start1, r1_0, r1_1, extra_r2=None, dice_side=None, root_q=0.1):
    """Partie: Startplatten, dann R1 (zwei Platten je Spieler), R2 und R3 Drafting-Records.

    start*: (slot, tile); r1_*: Liste [(slot, tile), (slot, tile)]."""
    recs = []
    e = {} if dice_side is None else {"dome_dice_side": dice_side}
    b0, b1 = {start0[0]: start0[1]}, {}
    recs.append(record(gid, state(1, "drafting", b0, b1), 1, **e, dice_phase=dice_side is not None))
    b1 = {start1[0]: start1[1]}
    recs.append(record(gid, state(1, "drafting", b0, b1), 0, **e, dice_phase=dice_side is not None))
    b0 = {**b0, r1_0[0][0]: r1_0[0][1]}
    recs.append(record(gid, state(1, "drafting", b0, b1), 1, **e, dice_phase=dice_side is not None))
    b0 = {**b0, r1_0[1][0]: r1_0[1][1]}
    b1 = {**b1, r1_1[0][0]: r1_1[0][1], r1_1[1][0]: r1_1[1][1]}
    recs.append(record(gid, state(1, "tiling", b0, b1), 0, **e, dice_phase=dice_side is not None))
    b2_0 = dict(b0)
    if extra_r2 is not None:
        b2_0[extra_r2[0]] = extra_r2[1]  # unaufgezeichneter erzwungener Zug vor dem ersten R2-Record
    for p in (0, 1):
        recs.append(record(gid, state(2, "drafting", b2_0, b1), p, **e, dice_phase=False, root_q=root_q))
    b3_0, b3_1 = fill_to(b2_0, 5), fill_to(b1, 5)  # zwei Platten je Spieler in Runde 2
    recs.append(record(gid, state(3, "drafting", b3_0, b3_1), 0, **e, dice_phase=False, root_q=root_q))
    recs.append(record(gid, state(3, "drafting", b3_0, b3_1), 1, **e, dice_phase=False, root_q=root_q))
    return recs


def fill_to(board, n):
    out = dict(board)
    for slot in [(r, c) for r in range(3) for c in range(3)]:
        if len(out) >= n:
            break
        out.setdefault(slot, tile(5))
    return out


class CanonicalizationTest(unittest.TestCase):
    def setUp(self):
        self.catalog, self.conflicts = {}, set()
        snp.update_catalog(state(1, "drafting", {}, {}), self.catalog, self.conflicts)

    def test_catalog_from_display(self):
        self.assertEqual(set(self.catalog), {1, 2, 3, 4, 5})
        self.assertEqual(self.conflicts, set())

    def test_rotation_recovered_for_all_angles(self):
        for tid in LAYOUTS:
            for deg in (0, 90, 180, 270):
                t = tile(tid, deg)
                self.assertEqual(snp.rotation_of(tid, snp.space_layout(t), self.catalog), deg, (tid, deg))

    def test_unknown_tile_falls_back_to_layout_key(self):
        rot = snp.rotation_of(99, (("COLOR", "red"),), self.catalog)
        self.assertTrue(isinstance(rot, str) and rot.startswith("L"))

    def test_levels(self):
        a = snp.raw_board({"dome_grid": grid({(0, 0): tile(1, 0), (1, 2): tile(2, 90)})})
        b = snp.raw_board({"dome_grid": grid({(0, 0): tile(1, 0), (1, 2): tile(2, 180)})})
        c = snp.raw_board({"dome_grid": grid({(0, 0): tile(1, 0, ["red", None, None, None]), (1, 2): tile(2, 90)})})
        key = lambda x, lv: snp.board_key(x, lv, self.catalog)  # noqa: E731
        self.assertEqual(key(a, "slots"), key(b, "slots"))
        self.assertNotEqual(key(a, "plates"), key(b, "plates"))  # Rotation unterscheidet
        self.assertEqual(key(a, "plates"), key(c, "plates"))      # Belegung erst in full
        self.assertNotEqual(key(a, "full"), key(c, "full"))
        self.assertEqual(key(a, "plates")[5], (2, 90))
        self.assertEqual(sum(key(a, "slots")), 2)


class GameParsingTest(unittest.TestCase):
    def test_round_start_and_round1_placements(self):
        rs = game_records("g", ((1, 1), tile(1)), ((0, 0), tile(2)),
                          [((0, 1), tile(3, 90)), ((2, 2), tile(4))], [((1, 0), tile(5)), ((0, 2), tile(1, 180))])
        b2 = snp.board_at_round_start(rs, 0, 2)
        self.assertEqual(snp.occupied(b2), {4, 1, 8})
        pl = snp.round1_placements(rs, 0)
        self.assertEqual([(t, s) for t, _lay, s in pl], [(3, 1), (4, 8)])  # Startplatte (Platz 4) fehlt
        self.assertEqual(snp.start_slot(rs, 1), 0)

    def test_unrecorded_forced_r2_plate_is_cut(self):
        rs = game_records("g", ((1, 1), tile(1)), ((0, 0), tile(2)),
                          [((0, 1), tile(3)), ((2, 2), tile(4))], [((1, 0), tile(5)), ((0, 2), tile(1))],
                          extra_r2=((2, 0), tile(5)))
        b2 = snp.board_at_round_start(rs, 0, 2)
        self.assertEqual(snp.occupied(b2), {4, 1, 8})  # Platz 6 (Runde-2-Platte) herausgeschnitten


class StatisticsTest(unittest.TestCase):
    def test_js_distance_bounds(self):
        a = Counter({"x": 3, "y": 1})
        self.assertAlmostEqual(snp.js_distance(a, a), 0.0)
        self.assertAlmostEqual(snp.js_distance(Counter({"x": 2}), Counter({"y": 5})), 1.0)
        b = Counter({"x": 1, "y": 3, "z": 2})
        self.assertAlmostEqual(snp.js_distance(a, b), snp.js_distance(b, a))
        keys = ["x", "y", "z"]
        self.assertAlmostEqual(snp.js_distance(a, b),
                               snp._js_vec(np.array([a[k] for k in keys], float), np.array([b[k] for k in keys], float)))

    def test_m1_compare_identical_vs_disjoint(self):
        rng = np.random.default_rng(1)
        same = [(f"g{i}", [(1, 0, 0), (2, 0, 1)]) for i in range(20)]
        other = [(f"h{i}", [(3, 90, 4), (4, 0, 5)]) for i in range(20)]
        r = snp.m1_compare(same, same, rng, 50, 50)
        self.assertAlmostEqual(r["js"], 0.0)
        r = snp.m1_compare(same, other, rng, 50, 50)
        self.assertAlmostEqual(r["js"], 1.0)
        self.assertLess(r["perm_null"]["q95"], 1.0)
        self.assertLess(r["perm_null"]["p"], 0.05)

    def test_novelty_and_boot(self):
        self.assertAlmostEqual(snp.novelty(["a", "b", "c", "d"], ["a", "b"]), 0.5)
        rng = np.random.default_rng(2)
        ci = snp.novelty_boot([["a"], ["b"]], [["a", "b"], ["a", "b"]], rng, 100)
        self.assertEqual(ci, [0.0, 0.0])
        ci = snp.novelty_boot([["x"], ["y"]], [["a"], ["b"]], rng, 100)
        self.assertEqual(ci, [1.0, 1.0])

    def test_mean_diff_and_entropy(self):
        rng = np.random.default_rng(3)
        r = snp.mean_diff_boot([[1.0, 1.0], [1.0]], [[0.0], [0.0, 0.0]], rng, 100)
        self.assertAlmostEqual(r["differenz"], 1.0)
        self.assertEqual(r["ci95"], [1.0, 1.0])
        self.assertAlmostEqual(snp.prior_entropy(np.zeros(10), [1, 4, 7, 7]), math.log(3))
        self.assertAlmostEqual(snp.entropy_bits(Counter({"a": 1, "b": 1})), 1.0)


def fake_class(n_files, games_per_file, make, side_field):
    files = [f"f{i}" for i in range(n_files)]
    store = {f: [r for gi in range(games_per_file) for r in make(fi, gi)] for fi, f in enumerate(files)}
    cat, conf = {}, set()
    out = snp.extract_class(files, side_field, cat, conf, store.__getitem__, "t", time.monotonic(),
                            action_id=lambda a: int(a), net_eval=lambda sts: np.zeros((len(sts), 8)))
    return out, cat


class NoiseAndClassTest(unittest.TestCase):
    def test_extract_class_with_dice_side_and_analysis(self):
        # Sockel: Dateien 0-4 legen Platte 3 auf Platz 1, Dateien 5-9 Platte 4 auf Platz 8 (Rauschbezug = 1)
        def base(fi, gi):
            r1 = [((0, 1), tile(3))] if fi < 5 else [((2, 2), tile(4))]
            r1 = r1 + [((2, 0), tile(5))]
            return game_records(f"b{fi}_{gi}", ((1, 1), tile(1)), ((1, 1), tile(2)), r1,
                                [((0, 1), tile(3)), ((2, 0), tile(5))])

        # W-Klasse: W = Spieler 0 legt sockelfremd (Platte 2 gedreht), G = Spieler 1 wie der Sockel
        def dice(fi, gi):
            rs = game_records(f"d{fi}_{gi}", ((1, 1), tile(1)), ((1, 1), tile(2)),
                              [((0, 0), tile(2, 270)), ((0, 2), tile(2, 90))],
                              [((0, 1), tile(3)), ((2, 0), tile(5))], dice_side=0, root_q=0.3)
            for r in rs:
                r["valid_actions"] = [1, 2]
            return rs

        base_d, cat = fake_class(10, 2, base, None)
        dice_d, cat2 = fake_class(10, 2, dice, snp.SIDE_FIELD)
        cat.update(cat2)
        self.assertEqual(dice_d["unresolved"], {})
        self.assertTrue(all(g["special"] == 0 for g in dice_d["games"]))
        # M3: nur G-Entscheide (Spieler 1), Runde 2-4, Prior-Entropie aus dem Netz-Ersatz ueber 2 IDs
        decs = [d for g in dice_d["games"] for d in g["decisions"]]
        self.assertTrue(decs and all(d["player"] == 1 and d["round"] in (2, 3) for d in decs))
        self.assertAlmostEqual(decs[0]["prior_entropy"], math.log(2))

        rng = np.random.default_rng(4)
        res = snp.analyze({snp.BASELINE: base_d, "dice": dice_d}, ["dice"], cat, rng, 50, 50)
        m1 = res["M1"]
        self.assertAlmostEqual(m1["zeilen"]["dice/W"]["js"], 1.0)
        self.assertLess(m1["zeilen"]["dice/G"]["js"], m1["zeilen"]["dice/W"]["js"])
        noise = m1["rauschbezug_sockel_1-5_gegen_6-10"]
        self.assertEqual(noise["haelfte_a"]["n_partien"], 10)
        self.assertGreater(noise["js"], 0.0)
        m2 = res["M2"]
        self.assertAlmostEqual(m2["zeilen"]["dice/W"]["runde2/plates"]["anteil_sockelfremd"], 1.0)
        self.assertAlmostEqual(m2["zeilen"]["dice/G"]["runde2/plates"]["anteil_sockelfremd"], 0.0)
        self.assertAlmostEqual(m2["rauschbezug_sockel_1-5_gegen_6-10"]["runde2/plates"]["anteil_a_fremd_in_b"], 0.5)
        # Feinheit slots: Haelfte A belegt bei beiden Spielern {1, 4, 6}, Haelfte B {4, 6, 8} (Spieler 0) und
        # {1, 4, 6} (Spieler 1) -> kein Platzmuster aus A fehlt in B
        self.assertAlmostEqual(m2["rauschbezug_sockel_1-5_gegen_6-10"]["runde2/slots"]["anteil_a_fremd_in_b"], 0.0)
        m3 = res["M3"]["zeilen"]["dice/G"]
        self.assertAlmostEqual(m3["je_feinheit"]["plates"]["anteil_sockelfremd"], 1.0)  # Gegnerbrett W ist neu
        self.assertAlmostEqual(m3["je_runde"]["2"]["root_q"]["differenz"], 0.2)


class MainSmokeTest(unittest.TestCase):
    def test_main_writes_artifact(self):
        import gzip
        import json
        import pickle
        import tempfile
        from unittest import mock

        with tempfile.TemporaryDirectory(dir=REPO / "tools" / "tests") as tmp:
            tmp = Path(tmp)
            for fi in range(10):
                recs = game_records(f"b{fi}", ((1, 1), tile(1)), ((1, 1), tile(2)),
                                    [((0, 1), tile(3)), ((2, 0), tile(5))], [((0, 1), tile(3)), ((2, 0), tile(5))])
                with gzip.open(tmp / f"selfplay_probe-v35-policy_20261003_g{fi:02d}.pkl", "wb") as f:
                    pickle.dump(recs, f)
                recs = game_records(f"d{fi}", ((1, 1), tile(1)), ((1, 1), tile(2)),
                                    [((0, 0), tile(2, 90)), ((0, 2), tile(4))],
                                    [((0, 1), tile(3)), ((2, 0), tile(5))], dice_side=0)
                with gzip.open(tmp / f"selfplay_probe-v35-policy-dice-r1_20261004_g{fi:02d}.pkl", "wb") as f:
                    pickle.dump(recs, f)
            out = tmp / "out.json"
            argv = ["x", "--data-dir", str(tmp), "--classes", "policy-dice-r1", "--no-prior",
                    "--n-boot", "20", "--n-perm", "20", "--out", str(out)]
            with mock.patch.object(sys, "argv", argv):
                snp.main()
            res = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(res["klassen"]["policy"]["n_partien"], 10)
        self.assertIn("policy-dice-r1/G", res["M3"]["zeilen"])
        for m in ("M1", "M2", "M3"):
            self.assertIn("grundmenge", res[m])
            self.assertIn("einheit", res[m])
        self.assertIn("s_je_datei", res["laufzeit"])
        self.assertAlmostEqual(res["M2"]["zeilen"]["policy-dice-r1/G"]["runde2/full"]["anteil_sockelfremd"], 0.0)


class EnvironmentLeakTest(unittest.TestCase):
    def test_no_mosaic_env_left_behind(self):
        MainSmokeTest("test_main_writes_artifact").test_main_writes_artifact()
        after = {k: v for k, v in os.environ.items() if k.startswith("MOSAIC_")}
        self.assertEqual(after, MOSAIC_ENV_BEFORE)


if __name__ == "__main__":
    unittest.main()
