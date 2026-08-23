"""Wave-3-Referee (PREREG_agent_encapsulation.md par.8): Partie-Serie Seite A
(aktuelle Engine, in-process, mit Spec-Parameter) gegen Seite B (gefrorenes
Artefakt, eigener Worker-Prozess). Der Referee ist Regel-Autoritaet: er haelt
den Zustand ueber `mosaic_rust.RefereeGame` (der AKTUELLEN Engine), validiert
jede Worker-Aktion HART gegen die aktuell legalen Zuege -- eine illegale
Aktion ist ein Abbruch mit Diagnose, keine stille Korrektur.

VOR jeder Serie:
  (a) statischer Handshake: Manifest-`contract_hash` gegen das aktuelle
      `mosaic_rust.engine_config_json()`s `contract_hash`. Mismatch =
      Verweigerung; Override nur per `--force-cross-era` (mit Warntext).
  (b) Golden-Selbsttest: `golden_probe.json` wird gegen den frisch
      gestarteten Worker nachgespielt (exakter Aktions-Vergleich).
      Abweichung = Verweigerung.

Aufruf-Beispiel (Kernbeweis, Artefakt gegen Artefakt auf denselben Spec/Sims
wie `net_vs_net_arena_match`):
    python tools/frozen_referee_match.py \\
        --artifact-dir models/frozen_champions/v21_2d_brierbest \\
        --model-a models/frozen_champions/v21_2d_brierbest/model.onnx \\
        --spec-a models/frozen_champions/v21_2d_brierbest/spec.json \\
        --sims-a 400 --sims-worker 400 --n-games 8 --seeds 900001,900002,...
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def load_manifest(artifact_dir: Path) -> dict:
    return json.loads((artifact_dir / "manifest.json").read_text(encoding="utf-8"))


def static_handshake(manifest: dict, force_cross_era: bool) -> dict:
    import mosaic_rust as mr

    current = json.loads(mr.engine_config_json())
    artifact_hash = manifest["contract_hash"]
    current_hash = current["contract_hash"]
    ok = artifact_hash == current_hash
    result = {"ok": ok, "artifact_contract_hash": artifact_hash, "current_contract_hash": current_hash}
    if not ok and not force_cross_era:
        raise SystemExit(
            "HANDSHAKE ROT: Artefakt-contract_hash={art} != aktuelle Engine {cur}. "
            "Verweigert (par.8: Kanten ueber die Fix-Grenze nie mischen). "
            "Override nur per --force-cross-era (Cross-Aera-Messung, Ergebnis mit "
            "Vorsicht lesen -- Regel-/Kontrakt-Drift zwischen den Seiten ist dann "
            "moeglich).".format(art=artifact_hash, cur=current_hash)
        )
    if not ok:
        print(
            f"[referee] WARNUNG: --force-cross-era aktiv, Handshake ROT "
            f"(artifact={artifact_hash} != current={current_hash}) -- Ergebnis ist eine "
            f"Cross-Aera-Messung, keine reine Champion-Bewertung.",
            file=sys.stderr,
        )
    return result


class WorkerProc:
    """Haelt den persistenten Worker-Subprozess, JSON-Zeilen-Protokoll."""

    def __init__(self, python_exe: Path, worker_script: Path, artifact_dir: Path, sims: int, c_puct: float):
        self.proc = subprocess.Popen(
            [str(python_exe), str(worker_script), str(artifact_dir), "--sims", str(sims), "--c-puct", str(c_puct)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )
        self.n_calls = 0
        self.total_wait_s = 0.0

    def ask(self, state_json: str, seed: int, sims: int | None = None, c_puct: float | None = None):
        req = {"state": state_json, "seed": seed}
        if sims is not None:
            req["sims"] = sims
        if c_puct is not None:
            req["c_puct"] = c_puct
        t0 = time.perf_counter()
        assert self.proc.stdin is not None and self.proc.stdout is not None
        self.proc.stdin.write(json.dumps(req) + "\n")
        self.proc.stdin.flush()
        line = self.proc.stdout.readline()
        self.total_wait_s += time.perf_counter() - t0
        self.n_calls += 1
        if not line:
            err = self.proc.stderr.read() if self.proc.stderr else ""
            raise RuntimeError(f"Worker hat die Verbindung beendet (kein Response). stderr:\n{err}")
        resp = json.loads(line)
        if not resp.get("ok"):
            raise RuntimeError(f"Worker meldet Fehler: {resp.get('error')}")
        return resp["action"], resp.get("value")

    def close(self):
        try:
            if self.proc.stdin:
                self.proc.stdin.close()
        except Exception:
            pass
        try:
            self.proc.wait(timeout=5)
        except Exception:
            self.proc.terminate()


def golden_selftest(worker: WorkerProc, golden_probe: dict) -> list[dict]:
    """Spielt golden_probe.json gegen den Worker nach, exakter Vergleich.
    Gibt die Liste der Abweichungen zurueck (leer = gruen)."""
    mismatches = []
    for p in golden_probe["probes"]:
        state_json = json.dumps(p["state"])
        action, value = worker.ask(state_json, p["seed"], sims=p["sims"], c_puct=p["c_puct"])
        if action != p["expected_action"]:
            mismatches.append(
                {"probe_id": p["probe_id"], "round": p["round"], "expected": p["expected_action"], "got": action}
            )
    return mismatches


def play_one_game(
    mr,
    worker: WorkerProc,
    model_a: str,
    spec_a: str | None,
    sims_a: int,
    c_puct_a: float,
    artifact_model: str,
    names: tuple[str, str],
    first_player: int,
    seed: int,
    board_a: int,
) -> dict:
    rg = mr.RefereeGame(names, first_player, seed, None)
    board_b = 1 - board_a
    model_p0 = model_a if board_a == 0 else artifact_model
    model_p1 = model_a if board_a == 1 else artifact_model
    guard = 0
    worker_calls_this_game = 0
    worker_wait_s = 0.0
    while True:
        guard += 1
        if guard > 100_000:
            raise RuntimeError("Referee: Schritt-Limit ueberschritten (Haenger-Verdacht).")
        status = rg.advance_to_decision(model_p0, model_p1)
        if status == "game_over":
            rg.finalize_scoring()
            break
        if status == "stuck":
            raise RuntimeError(
                f"Referee: Deadlock (advance_to_decision='stuck') bei steps={rg.steps()}, "
                f"phase={rg.phase()} -- Diagnose noetig, kein stiller Fallback."
            )
        cur = rg.current_player()
        if cur == board_a:
            rg.drafting_decide_and_apply_inprocess(model_a, spec_a, sims_a, c_puct_a)
        else:
            seed_for_worker = rg.pending_search_seed()
            state_json = rg.state_json()
            before_calls = worker.n_calls
            before_wait = worker.total_wait_s
            action, _value = worker.ask(state_json, seed_for_worker)
            worker_calls_this_game += worker.n_calls - before_calls
            worker_wait_s += worker.total_wait_s - before_wait
            rg.drafting_apply_external(json.dumps(action))
    scores = rg.scores()
    winner = 0 if scores[0] > scores[1] else (1 if scores[1] > scores[0] else -1)
    return {
        "scores": list(scores),
        "winner": winner,
        "steps": rg.steps(),
        "seed": seed,
        "first_player": first_player,
        "board_a": board_a,
        "worker_calls": worker_calls_this_game,
        "worker_wait_s": worker_wait_s,
        "log": rg.full_log(),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--artifact-dir", required=True)
    ap.add_argument("--model-a", required=True, help="Modellpfad fuer Seite A (aktuelle Engine, in-process)")
    ap.add_argument("--spec-a", default=None, help="Such-Spec fuer Seite A (None = SearchConfig::from_env())")
    ap.add_argument("--sims-a", type=int, default=400)
    ap.add_argument("--c-puct-a", type=float, default=1.5)
    ap.add_argument("--sims-worker", type=int, default=400)
    ap.add_argument("--c-puct-worker", type=float, default=1.5)
    ap.add_argument("--n-games", type=int, default=8)
    ap.add_argument("--seeds", default=None, help="Kommagetrennte Liste; sonst n_games ab --seed-base")
    ap.add_argument("--seed-base", type=int, default=900001)
    ap.add_argument("--force-cross-era", action="store_true")
    ap.add_argument("--skip-golden", action="store_true", help="NUR fuer Debug -- Abnahme braucht den Golden-Test")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    artifact_dir = Path(args.artifact_dir).resolve()
    manifest = load_manifest(artifact_dir)
    worker_python = artifact_dir / manifest["worker_python"]["interpreter_relative"]
    worker_script = REPO / "tools" / "frozen_champion_worker.py"

    sys.path.insert(0, str(REPO))
    import mosaic_rust as mr

    handshake = static_handshake(manifest, args.force_cross_era)
    print(f"[referee] Handshake: {handshake}", file=sys.stderr)

    worker = WorkerProc(worker_python, worker_script, artifact_dir, args.sims_worker, args.c_puct_worker)
    time.sleep(0.2)  # Worker-Startzeit (Modell laden) -- erste Anfrage wartet ohnehin, reine Kulanz

    golden_mismatches = []
    if not args.skip_golden:
        golden_probe = json.loads((artifact_dir / "golden_probe.json").read_text(encoding="utf-8"))
        golden_mismatches = golden_selftest(worker, golden_probe)
        if golden_mismatches:
            worker.close()
            raise SystemExit(
                f"GOLDEN-SELBSTTEST ROT: {len(golden_mismatches)}/{golden_probe['n_probes'] if 'n_probes' in golden_probe else len(golden_probe['probes'])} "
                f"Abweichungen. Verweigert (par.8: 'faengt, was Versions-Stempel nicht sehen'). "
                f"Details: {json.dumps(golden_mismatches, ensure_ascii=False)[:2000]}"
            )
        print(f"[referee] Golden-Selbsttest gruen: {len(golden_probe['probes'])} Sonden, 0 Abweichungen.", file=sys.stderr)

    if args.seeds:
        seeds = [int(s) for s in args.seeds.split(",")]
    else:
        seeds = [args.seed_base + i for i in range(args.n_games)]

    names = ("EngineA", "ArtefaktB")
    games = []
    t_start = time.perf_counter()
    total_move_count = 0
    for i, seed in enumerate(seeds):
        first_player = i % 2
        board_a = i % 2  # Brettwechsel-Pflicht, wie paired_arena-Konvention
        g = play_one_game(
            mr, worker, args.model_a, args.spec_a, args.sims_a, args.c_puct_a,
            str(artifact_dir / "model.onnx"), names, first_player, seed, board_a,
        )
        total_move_count += g["steps"]
        games.append(g)
        print(f"[referee] Partie {i + 1}/{len(seeds)} seed={seed}: {g['scores']} winner={g['winner']} steps={g['steps']}", file=sys.stderr)
    elapsed = time.perf_counter() - t_start
    worker.close()

    result = {
        "artifact_dir": str(artifact_dir),
        "champion": manifest.get("champion"),
        "handshake": handshake,
        "force_cross_era": args.force_cross_era,
        "golden_selftest": {"ran": not args.skip_golden, "mismatches": golden_mismatches},
        "model_a": args.model_a,
        "spec_a": args.spec_a,
        "sims_a": args.sims_a,
        "c_puct_a": args.c_puct_a,
        "sims_worker": args.sims_worker,
        "c_puct_worker": args.c_puct_worker,
        "n_games": len(seeds),
        "seeds": seeds,
        "elapsed_s": elapsed,
        "total_steps": total_move_count,
        "s_per_step": elapsed / total_move_count if total_move_count else None,
        "games": games,
    }
    wins_a = sum(1 for g in games if g["winner"] == g["board_a"])
    wins_b = sum(1 for g in games if g["winner"] == (1 - g["board_a"]))
    draws = sum(1 for g in games if g["winner"] == -1)
    result["wins_a"] = wins_a
    result["wins_b"] = wins_b
    result["draws"] = draws

    out_path = Path(args.out) if args.out else REPO / "evaluations" / f"frozen_referee_match_{manifest.get('champion')}.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[referee] fertig: {wins_a} A / {wins_b} B / {draws} Remis, geschrieben nach {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
