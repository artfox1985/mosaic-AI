# -*- coding: utf-8 -*-
"""Zwischenstand je Block und `--resume` in `tools/paired_gating.py`
(2026-10-07, Nutzer nach einem Rechner-Neustart: "plane ebenfalls einen save
und restore punkt bei arena spielen ein. aehnlich wie der epochen save/restore
punkt").

Keine Engine: `play_pair_block` ist durch eine Attrappe ersetzt, die ihre
Aufrufe (Blockseed, Paarzahl) protokolliert und je Blockseed feste Records
liefert; `mosaic_rust` ist ein leeres Modul in `sys.modules`, der
Trend-Log-Eintrag (`append_run`) ist abgeklemmt.

Geprueft:
  - nach JEDEM Block liegt ein Zwischenstand (atomar, ohne .tmp-Rest);
  - `--resume` uebernimmt genau die fertigen Bloecke, setzt beim richtigen
    Blockseed fort und kommt auf dasselbe Ergebnis wie ein Lauf ohne Abbruch;
  - eine Konfigurations-Abweichung (Sims, Blockgroesse, max-pairs, SPRT,
    Modell-sha256, MOSAIC_*) und ein manipulierter LLR brechen hart ab;
  - ohne `--resume` wird ein liegender Zwischenstand ignoriert und
    ueberschrieben, das Artefakt bleibt Feld fuer Feld das bisherige;
  - die Laufzeitfelder summieren die Segmente;
  - `main` loescht den Zwischenstand nach dem fertigen Artefakt.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))

import paired_gating as pg  # noqa: E402

BASE_SEED = 20261600
STRIDE = 1_000_000
RESULT_KEYS_COMPARED = (
    "done_pairs", "n_games_total", "a_wins_total", "b_wins_total", "pair_a_sweeps_b",
    "pair_b_sweeps_c", "pair_splits", "sprt_verdict", "sprt_llr", "report_mcnemar_p",
    "mean_pair_diff", "ci95", "avg_score_a", "avg_score_b", "avg_floor_a", "avg_floor_b",
    "zerozero_anteil", "per_pair_scores",
)
RUNTIME_KEYS_DEFAULT = {"wanduhr_s", "cpu_s", "threads", "s_je_partie"}


class Interrupted(Exception):
    """Simulierter Abbruch (Neustart, Kill) mitten im Lauf."""


def fake_block_player(calls: list, *, fail_at_block: int | None = None,
                      all_a_sweeps: bool = False):
    """Attrappe fuer `play_pair_block`. Die Records haengen nur vom Blockindex
    (aus dem Blockseed) und vom Paarindex ab, also bekommt Block k bei jedem
    Lauf dieselben Partien -- wie die Engine bei gleichem Seed."""
    def play(mr, model_a, model_b, sims_a, sims_b, c_puct_a, c_puct_b, n, seed, threads,
             spec_a=None, spec_b=None, log_games=False):
        block_index = (seed - BASE_SEED) // STRIDE
        if fail_at_block is not None and block_index == fail_at_block:
            raise Interrupted(f"Abbruch in Block {block_index + 1}")
        calls.append((seed, n))
        g1, g2 = [], []
        for i in range(n):
            k = block_index * 7 + i
            if all_a_sweeps:
                w1, w2 = 0, 1
            else:
                w1, w2 = k % 2, (k // 2) % 2
            g1.append({"winner": w1, "scores": [20 + k % 5, 18 + k % 3],
                       "total_floor": [k % 4, 1], "completed": True, "steps": 100 + k})
            g2.append({"winner": w2, "scores": [19 + k % 4, 21 - k % 3],
                       "total_floor": [2, k % 3], "completed": True, "steps": 90 + k})
        return g1, g2
    return play


def run_gating(directory: Path, player, *, resume: bool = False, **overrides) -> dict:
    kwargs = dict(name_a="A", name_b="B", sims_a=10, sims_b=10, block_size=5, max_pairs=20,
                  sprt_alpha=1e-12, sprt_beta=1e-12, base_seed=BASE_SEED, threads=1,
                  partial_path=directory / "gating.json.partial.json", resume=resume)
    kwargs.update(overrides)
    model_a = kwargs.pop("model_a", "a.onnx")
    model_b = kwargs.pop("model_b", "b.onnx")
    with mock.patch.dict(sys.modules, {"mosaic_rust": types.ModuleType("mosaic_rust")}), \
            mock.patch.object(pg, "append_run", lambda **_: None), \
            mock.patch.object(pg, "play_pair_block", player):
        return pg.run_paired_gating(model_a, model_b, **kwargs)


def interrupted_run(directory: Path, fail_at_block: int = 2, **overrides) -> Path:
    """Erstlauf, der in Block `fail_at_block + 1` abbricht; liefert den Zwischenstand."""
    with mock.patch("sys.stdout", new_callable=io.StringIO):
        try:
            run_gating(directory, fake_block_player([], fail_at_block=fail_at_block), **overrides)
        except Interrupted:
            pass
        else:
            raise AssertionError("der Erstlauf haette abbrechen muessen")
    return directory / "gating.json.partial.json"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def quiet():
    return mock.patch("sys.stdout", new_callable=io.StringIO)


class PartialAfterEveryBlock(unittest.TestCase):
    def test_partial_is_written_after_each_block(self):
        with tempfile.TemporaryDirectory() as d:
            directory = Path(d)
            partial = directory / "gating.json.partial.json"
            seen = []
            inner = fake_block_player([])

            def player(*args, **kwargs):
                # Beim Start von Block k (k > 1) muss der Stand nach Block k-1 liegen.
                seen.append(read_json(partial)["done_pairs"] if partial.exists() else None)
                return inner(*args, **kwargs)

            with quiet():
                run_gating(directory, player)
            self.assertEqual(seen, [None, 5, 10, 15])
            final = read_json(partial)
            self.assertIs(final["partial"], True)
            self.assertEqual(final["done_pairs"], 20)
            self.assertEqual(final["next_block_index"], 4)
            self.assertEqual(final["next_block_seed"], BASE_SEED + 4 * STRIDE)
            self.assertEqual(len(final["block_records"]), 4)
            self.assertEqual([b["seed"] for b in final["blocks"]],
                             [BASE_SEED + k * STRIDE for k in range(4)])
            self.assertEqual(final["config"]["base_seed"], BASE_SEED)
            self.assertEqual(final["config"]["block_size"], 5)
            self.assertEqual(list(directory.glob("*.tmp")), [], "atomar: kein .tmp-Rest")

    def test_without_log_games_only_scoring_fields_are_kept(self):
        with tempfile.TemporaryDirectory() as d:
            with quiet():
                run_gating(Path(d), fake_block_player([]), max_pairs=5)
            rec = read_json(Path(d) / "gating.json.partial.json")["block_records"][0]
            self.assertEqual(set(rec["g1"][0]), set(pg.SCORING_RECORD_FIELDS))
            self.assertEqual(len(rec["g1"]), 5)
            self.assertEqual(len(rec["g2"]), 5)

    def test_without_partial_path_nothing_is_written(self):
        with tempfile.TemporaryDirectory() as d:
            with quiet():
                result = run_gating(Path(d), fake_block_player([]), partial_path=None)
            self.assertEqual(list(Path(d).iterdir()), [])
            self.assertEqual(set(result["laufzeit"]), RUNTIME_KEYS_DEFAULT)


class ResumeContinues(unittest.TestCase):
    def test_resume_takes_over_finished_blocks_and_continues_at_next_seed(self):
        with tempfile.TemporaryDirectory() as d_ref, tempfile.TemporaryDirectory() as d:
            with quiet():
                reference = run_gating(Path(d_ref), fake_block_player([]))
            partial = interrupted_run(Path(d), fail_at_block=2)
            self.assertEqual(read_json(partial)["done_pairs"], 10)
            calls = []
            with quiet():
                resumed = run_gating(Path(d), fake_block_player(calls), resume=True)
        self.assertEqual(calls, [(BASE_SEED + 2 * STRIDE, 5), (BASE_SEED + 3 * STRIDE, 5)])
        for key in RESULT_KEYS_COMPARED:
            self.assertEqual(resumed[key], reference[key], key)

        def strip(blocks):
            return [{k: v for k, v in b.items() if k != "duration_s"} for b in blocks]
        self.assertEqual(strip(resumed["blocks"]), strip(reference["blocks"]))
        self.assertEqual(resumed["laufzeit"]["fortgesetzt_ab_block"], 3)
        self.assertIsNotNone(resumed["laufzeit"]["segment_wanduhr_s"])

    def test_resume_prints_progress_line(self):
        with tempfile.TemporaryDirectory() as d:
            interrupted_run(Path(d), fail_at_block=2)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                run_gating(Path(d), fake_block_player([]), resume=True)
        self.assertIn("Fortgesetzt ab Block 3 (10 Paare uebernommen", buf.getvalue())

    def test_resume_without_partial_runs_normally(self):
        with tempfile.TemporaryDirectory() as d:
            calls = []
            with quiet():
                result = run_gating(Path(d), fake_block_player(calls), resume=True)
        self.assertEqual([c[0] for c in calls], [BASE_SEED + k * STRIDE for k in range(4)])
        self.assertEqual(result["done_pairs"], 20)
        self.assertIsNone(result["laufzeit"]["fortgesetzt_ab_block"])
        self.assertIsNone(result["laufzeit"]["segment_wanduhr_s"])

    def test_resume_without_seed_takes_the_seed_of_the_partial(self):
        with tempfile.TemporaryDirectory() as d:
            interrupted_run(Path(d), fail_at_block=1)
            calls = []
            with quiet():
                result = run_gating(Path(d), fake_block_player(calls), resume=True, base_seed=None)
        self.assertEqual(calls[0], (BASE_SEED + 1 * STRIDE, 5))
        self.assertEqual(result["base_seed"], BASE_SEED)

    def test_partial_with_decision_plays_no_further_block(self):
        # Abbruch NACH dem Zwischenstand des entscheidenden Blocks, VOR dem
        # Artefakt: bei alpha=beta=0,05 reissen 15 A-Sweeps die obere Schranke
        # (15 * ln(0,65/0,5) = 3,94 > ln(19) = 2,94; 10 Sweeps = 2,62 noch nicht).
        real_write = pg.write_json_atomic

        def crashing_write(path, payload, indent=None):
            real_write(path, payload, indent=indent)
            if payload.get("partial") and payload["done_pairs"] == 15:
                raise Interrupted("Abbruch zwischen Zwischenstand und Artefakt")

        with tempfile.TemporaryDirectory() as d:
            with quiet(), mock.patch.object(pg, "write_json_atomic", crashing_write):
                with self.assertRaises(Interrupted):
                    run_gating(Path(d), fake_block_player([], all_a_sweeps=True),
                               sprt_alpha=0.05, sprt_beta=0.05)
            calls = []
            with quiet():
                result = run_gating(Path(d), fake_block_player(calls, all_a_sweeps=True),
                                    sprt_alpha=0.05, sprt_beta=0.05, resume=True)
        self.assertEqual(calls, [])
        self.assertEqual(result["sprt_verdict"], "A")
        self.assertEqual(result["done_pairs"], 15)


class ConfigDeviationAborts(unittest.TestCase):
    def assert_resume_aborts(self, directory: Path, needle: str, **overrides):
        calls = []
        with quiet():
            with self.assertRaises(SystemExit) as ctx:
                run_gating(directory, fake_block_player(calls), resume=True, **overrides)
        self.assertIn(needle, str(ctx.exception))
        self.assertEqual(calls, [], "kein Block darf vor der Pruefung laufen")

    def test_parameter_deviations_abort(self):
        for field, overrides in (("sims_a", {"sims_a": 20}), ("block_size", {"block_size": 10}),
                                 ("max_pairs", {"max_pairs": 40}), ("sprt_alpha", {"sprt_alpha": 0.05}),
                                 ("c_puct_b", {"c_puct_b": 2.0}), ("log_games", {"log_games": True}),
                                 ("base_seed", {"base_seed": BASE_SEED + 1})):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as d:
                interrupted_run(Path(d))
                self.assert_resume_aborts(Path(d), field, **overrides)

    def test_model_file_change_aborts(self):
        with tempfile.TemporaryDirectory() as d:
            directory = Path(d)
            model_a, model_b = directory / "a.onnx", directory / "b.onnx"
            model_a.write_bytes(b"model a, first state")
            model_b.write_bytes(b"model b")
            interrupted_run(directory, model_a=str(model_a), model_b=str(model_b))
            config = read_json(directory / "gating.json.partial.json")["config"]
            self.assertEqual(len(config["model_a_sha256"]), 64)
            model_a.write_bytes(b"model a, retrained")
            self.assert_resume_aborts(directory, "model_a_sha256",
                                      model_a=str(model_a), model_b=str(model_b))

    def test_mosaic_env_change_aborts(self):
        with tempfile.TemporaryDirectory() as d:
            interrupted_run(Path(d))
            with mock.patch.dict(os.environ, {"MOSAIC_RESUME_TEST_KNOB": "1"}):
                self.assert_resume_aborts(Path(d), "mosaic_env")

    def test_tampered_llr_aborts(self):
        with tempfile.TemporaryDirectory() as d:
            partial = interrupted_run(Path(d))
            data = read_json(partial)
            data["sprt_llr"] += 0.5
            partial.write_text(json.dumps(data), encoding="utf-8")
            self.assert_resume_aborts(Path(d), "sprt_llr")

    def test_foreign_file_aborts(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "gating.json.partial.json").write_text('{"done_pairs": 5}', encoding="utf-8")
            self.assert_resume_aborts(Path(d), "kein Zwischenstand im Format")


class WithoutResumeThePartialIsIgnored(unittest.TestCase):
    def test_partial_is_ignored_and_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            partial = interrupted_run(Path(d), fail_at_block=2)
            calls = []
            with quiet():
                result = run_gating(Path(d), fake_block_player(calls), resume=False)
            self.assertEqual([c[0] for c in calls], [BASE_SEED + k * STRIDE for k in range(4)])
            self.assertEqual(result["done_pairs"], 20)
            self.assertEqual(read_json(partial)["done_pairs"], 20, "ueberschrieben")
        self.assertEqual(set(result["laufzeit"]), RUNTIME_KEYS_DEFAULT,
                         "ohne --resume bleibt der laufzeit-Block der bisherige")


class RuntimeSumsSegments(unittest.TestCase):
    def test_wall_and_cpu_add_up_over_segments(self):
        with tempfile.TemporaryDirectory() as d:
            partial = interrupted_run(Path(d), fail_at_block=2)
            data = read_json(partial)
            self.assertEqual(data["laufzeit_so_far"]["segments"], 1)
            data["laufzeit_so_far"]["wanduhr_s"] = 1000.0
            data["laufzeit_so_far"]["cpu_s"] = 500.0
            partial.write_text(json.dumps(data), encoding="utf-8")
            with quiet():
                result = run_gating(Path(d), fake_block_player([]), resume=True)
            self.assertEqual(read_json(partial)["laufzeit_so_far"]["segments"], 2)
        lz = result["laufzeit"]
        self.assertGreaterEqual(lz["wanduhr_s"], 1000.0)
        self.assertGreaterEqual(lz["cpu_s"], 500.0)
        self.assertAlmostEqual(lz["wanduhr_s"], 1000.0 + lz["segment_wanduhr_s"], delta=0.15)
        self.assertAlmostEqual(lz["s_je_partie"], lz["wanduhr_s"] / 40, delta=0.01)
        self.assertEqual(lz["threads"], 1)
        self.assertEqual(lz["fortgesetzt_ab_block"], 3)


class MainHandlesThePartial(unittest.TestCase):
    def _argv(self, out: Path, *extra: str) -> list[str]:
        return ["--model-a", "a.onnx", "--model-b", "b.onnx", "--name-a", "A", "--name-b", "B",
                "--sims", "10", "--block-size", "5", "--max-pairs", "10",
                "--sprt-alpha", "1e-12", "--sprt-beta", "1e-12", "--seed", str(BASE_SEED),
                "--threads", "1", "--no-promote-winner", "--out", str(out), *extra]

    def _main(self, argv, player):
        with mock.patch.dict(sys.modules, {"mosaic_rust": types.ModuleType("mosaic_rust")}), \
                mock.patch.object(pg, "append_run", lambda **_: None), \
                mock.patch.object(pg, "play_pair_block", player), quiet():
            pg.main(argv, recipe_pre=None)

    def test_resume_flag_parses_and_defaults_off(self):
        self.assertIs(pg.build_parser().parse_args(self._argv(Path("x.json"))).resume, False)
        self.assertIs(pg.build_parser().parse_args(self._argv(Path("x.json"), "--resume")).resume, True)

    def test_main_resumes_and_deletes_the_partial_after_the_artifact(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "gating.json"
            partial = pg.partial_path_for(out)
            self.assertEqual(partial.name, "gating.json.partial.json")
            with self.assertRaises(Interrupted):
                self._main(self._argv(out), fake_block_player([], fail_at_block=1))
            self.assertFalse(out.exists())
            self.assertEqual(read_json(partial)["done_pairs"], 5)
            calls = []
            self._main(self._argv(out, "--resume"), fake_block_player(calls))
            self.assertEqual(calls, [(BASE_SEED + STRIDE, 5)])
            artifact = read_json(out)
            self.assertFalse(partial.exists(), "Zwischenstand nach dem Artefakt geloescht")
            self.assertEqual(list(Path(d).glob("*.tmp")), [])
        self.assertEqual(artifact["done_pairs"], 10)
        self.assertEqual(artifact["laufzeit"]["fortgesetzt_ab_block"], 2)

    def test_main_without_resume_deletes_the_partial_too(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "gating.json"
            self._main(self._argv(out), fake_block_player([]))
            self.assertTrue(out.exists())
            self.assertFalse(pg.partial_path_for(out).exists())


if __name__ == "__main__":
    unittest.main()
