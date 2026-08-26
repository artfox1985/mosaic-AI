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
import multiprocessing as mp
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
        # PER-ENTSCHEIDUNG-Protokoll (par.8d): EINE Anfrage = EINE
        # Drafting-Entscheidung -- kein `rot_seed` mehr, siehe
        # frozen_champion_worker.py-Doku.
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

    def _roundtrip(self, req: dict) -> dict:
        """Eine Anfrage, eine Antwort -- gemeinsamer Rumpf fuer alle Arten."""
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
        return resp

    def ask_tiling(self, state_json: str) -> dict:
        """Platzierungs-Schritt der gefrorenen Seite.

        Seit 2026-08-26: bis dahin loeste der Referee das Tiling selbst auf,
        ueber einen auf V1 verdrahteten Pfad. Ein `v2huelle`-Artefakt haette
        damit als `v1` gekachelt.
        """
        return self._roundtrip({"kind": "tiling", "state": state_json})["step"]

    def ask_start_placement(self, state_json: str, pi: int, game_seed: int) -> dict:
        """Startsetzung der gefrorenen Seite.

        `pi` kommt aus `pending_start_placement_player()`, nicht aus
        `current_player()` -- in dieser Phase kann der Nicht-Starter zuerst
        dran sein. `game_seed`, weil v2-Varianten unter mehreren Kandidaten
        seed-basiert waehlen.
        """
        return self._roundtrip({"kind": "start_placement", "state": state_json,
                                "pi": pi, "game_seed": game_seed})["placement"]

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


def golden_selbsttest_heuristik(worker_python, artifact_dir, repo) -> None:
    """Golden-Selbsttest eines HEURISTIK-Artefakts: Self-Play-Reproduktion.

    Die Welle-3-Sonde prueft Drafting-Zustaende und deckt fuer eine Heuristik
    damit nur die halbe Identitaet ab (par.9). Hier laeuft stattdessen das
    dafuer gebaute Werkzeug -- mit dem Interpreter des Artefakts, also als
    KONSERVIERUNGS-Pruefung und nicht als Drift-Test.

    Wirft `SystemExit` bei Abweichung. Es gibt bewusst keine Rueckgabe von
    "Abweichungen zum Weiterreichen": ein Artefakt, das seine eigene Probe
    nicht mehr trifft, darf nicht in eine Messung.
    """
    print(f"[referee] Golden-Selbsttest ({artifact_dir.name}): Self-Play-Reproduktion ...",
          file=sys.stderr, flush=True)
    r = subprocess.run(
        [str(worker_python), "-X", "utf8", "-u",
         str(repo / "tools" / "verify_frozen_heuristic.py"),
         "--artifact-dir", str(artifact_dir), "--venv"],
        cwd=str(repo), text=True, encoding="utf-8", capture_output=True)
    if r.returncode != 0:
        raise SystemExit(
            f"GOLDEN-SELBSTTEST ROT ({artifact_dir.name}, Self-Play-Reproduktion). Verweigert."
            + chr(10) + (r.stdout or "")[-1500:] + (r.stderr or "")[-1500:])
    print(f"[referee] Golden-Selbsttest gruen ({artifact_dir.name}).", file=sys.stderr)


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


def _spiele_block(auftrag: dict) -> list[dict]:
    """Spielt EINEN Seed-Block in einem eigenen Prozess, mit eigenen Workern.

    PARALLELISIERT WIRD AUSSEN, nicht innen: das Protokoll ist je Worker
    seriell (eine Anfrage, eine Antwort), also bringt es nichts, einen Worker
    von mehreren Partien gleichzeitig befragen zu lassen. Partien sind
    dagegen voneinander unabhaengig -- jeder Prozess bekommt deshalb seinen
    eigenen Worker (bzw. sein eigenes Paar) und einen Ausschnitt der Seeds.

    KOSTEN, die man kennen muss: je Block startet ein eigener Worker-Prozess
    und laedt sein Wheel (bei Netz-Artefakten zusaetzlich das ONNX). Bei sehr
    wenigen Partien je Block frisst das den Gewinn wieder auf -- die
    Blockaufteilung unten haelt deshalb einen Mindest-Block ein.

    Der Handshake und der Golden-Selbsttest laufen NICHT hier, sondern EINMAL
    im Elternprozess. Sie pruefen das Artefakt, nicht den Block; je Block
    wiederholt waeren sie reine Wartezeit -- und ein Selbsttest, der in Block 3
    rot wird, waere ohnehin zu spaet.
    """
    import mosaic_rust as mr  # im Kind importieren (spawn-sicher)

    worker = WorkerProc(Path(auftrag["worker_python"]), Path(auftrag["worker_script"]),
                        Path(auftrag["artifact_dir"]), auftrag["sims_worker"],
                        auftrag["c_puct_worker"])
    worker_a = None
    if auftrag["artifact_dir_a"]:
        worker_a = WorkerProc(Path(auftrag["worker_python_a"]), Path(auftrag["worker_script"]),
                              Path(auftrag["artifact_dir_a"]), auftrag["sims_a"],
                              auftrag["c_puct_a"])
    time.sleep(0.2)
    ergebnisse = []
    try:
        for i, seed in auftrag["indizierte_seeds"]:
            first_player = i % 2
            board_a = i % 2  # Brettwechsel-Pflicht, wie paired_arena-Konvention
            externe = []
            if auftrag["externe_b"]:
                externe.append(1 - board_a)
            if auftrag["externe_a"]:
                externe.append(board_a)
            g = play_one_game(
                mr, worker, worker_a, auftrag["model_a"], auftrag["spec_a"],
                auftrag["sims_a"], auftrag["c_puct_a"], auftrag["artefakt_modell"],
                tuple(auftrag["names"]), first_player, seed, board_a,
                externe_seiten=externe,
            )
            # Der Index reist MIT: die Bloecke kommen in beliebiger
            # Reihenfolge zurueck, die Ergebnisliste muss aber der Seed-Folge
            # entsprechen (sonst stimmt jede spaetere Paarung nicht mehr).
            g["_index"] = i
            ergebnisse.append(g)
            print(f"[referee] Partie {i + 1} seed={seed}: {g['scores']} "
                  f"winner={g['winner']} steps={g['steps']}", file=sys.stderr, flush=True)
    finally:
        worker.close()
        if worker_a:
            worker_a.close()
    return ergebnisse


def play_one_game(
    mr,
    worker: WorkerProc,
    # Ist gesetzt, wenn auch die A-Seite ein gefrorenes Artefakt ist. Dann
    # laeuft die Partie ARTEFAKT gegen ARTEFAKT, moeglicherweise auf zwei
    # verschiedenen Wheels -- der Fall, fuer den die Prozess-Isolation aus
    # par.8 ueberhaupt gebaut wurde (zwei Engine-Versionen passen nicht in
    # einen Prozess). `model_a`/`spec_a` sind dann unbenutzt.
    worker_a: WorkerProc | None,
    model_a: str | None,
    spec_a: str | None,
    sims_a: int,
    c_puct_a: float,
    artifact_model: str | None,
    names: tuple[str, str],
    first_player: int,
    seed: int,
    board_a: int,
    # Seiten, die ihre Startsetzung und ihr Tiling SELBST entscheiden. Leer =
    # Bestandsverhalten (der Referee loest beides auf), und das bleibt der
    # Default fuer Netz-Artefakte aus Welle 3.
    externe_seiten=None,
) -> dict:
    externe_seiten = externe_seiten or []
    # Die Namen MIT dem Brett tauschen. `wins_a` rechnet korrekt ueber
    # `board_a`, die Namen gingen aber ungetauscht hinein -- bei `board_a == 1`
    # sass die A-Seite auf dem Brett, das im Log den B-Namen trug. Fuer die
    # blosse Sieg-Zaehlung war das folgenlos; sobald jemand die Log-NAMEN
    # auswertet (Kennzahlen je Seite, tools/anchor_arena.py), vertauscht es die
    # Seiten. Gefunden am 2026-08-26 an einem Margin, der dem Siegverhaeltnis
    # widersprach.
    namen_im_spiel = names if board_a == 0 else (names[1], names[0])
    rg = mr.RefereeGame(namen_im_spiel, first_player, seed, None)
    board_b = 1 - board_a
    model_p0 = model_a if board_a == 0 else artifact_model
    model_p1 = model_a if board_a == 1 else artifact_model

    def worker_fuer(pi: int) -> WorkerProc:
        """Der Worker der Seite `pi`.

        Mit zwei Artefakten haengt an JEDER Anfrage, WELCHE Seite gefragt
        wird -- die Seiten haben verschiedene Specs und moeglicherweise
        verschiedene Wheels. Eine feste Zuordnung auf `worker` waere der
        stille Fehler, bei dem ein Agent die Zuege des anderen bekommt.
        """
        if pi == board_a:
            if worker_a is None:
                raise RuntimeError(
                    f"Seite {pi} ist in-process, wurde aber extern gefragt -- "
                    "Widerspruch zwischen `externe_seiten` und der Besetzung.")
            return worker_a
        return worker
    guard = 0
    worker_calls_this_game = 0
    worker_wait_s = 0.0
    while True:
        guard += 1
        if guard > 100_000:
            raise RuntimeError("Referee: Schritt-Limit ueberschritten (Haenger-Verdacht).")
        # `externe_seiten`: die gefrorene Seite entscheidet Startsetzung und
        # Tiling SELBST -- aber NUR, wenn ihr Worker das erweiterte Protokoll
        # kennt (Manifest-Feld `typ`, gesetzt seit 2026-08-26).
        #
        # Ein Welle-3-Netz-Artefakt bringt sein EIGENES, aelteres Wheel und
        # seinen eigenen Worker mit; der ignoriert ein `kind`-Feld und
        # antwortete auf eine Tiling-Anfrage mit einer Drafting-Aktion. Der
        # Treiber wuerde `step` erwarten und mit KeyError sterben -- ein
        # Regressionsschaden an genau dem Pfad, der seit par.8f gruen ist.
        # Fuer solche Artefakte bleibt es beim Bestandsverhalten: der Referee
        # loest Platzierung und Startsetzung selbst auf. Das ist fuer ein Netz
        # auch inhaltlich richtig, seine Identitaet ist das ONNX.
        status = rg.advance_to_decision(model_p0, model_p1, externe_seiten)
        if status == "game_over":
            rg.finalize_scoring()
            break
        if status == "tiling":
            pi_t = rg.current_player()
            rg.tiling_apply_external(json.dumps(worker_fuer(pi_t).ask_tiling(rg.state_json())))
            continue
        if status == "start_placement":
            # `pending_start_placement_player()`, NICHT `current_player()`:
            # in dieser Phase kann der Nicht-Starter zuerst dran sein.
            pi_start = rg.pending_start_placement_player()
            rg.start_placement_apply_external(json.dumps(
                worker_fuer(pi_start).ask_start_placement(
                    rg.state_json(), pi_start, rg.game_seed())))
            continue
        if status == "stuck":
            raise RuntimeError(
                f"Referee: Deadlock (advance_to_decision='stuck') bei steps={rg.steps()}, "
                f"phase={rg.phase()} -- Diagnose noetig, kein stiller Fallback."
            )
        cur = rg.current_player()
        if cur == board_a and worker_a is None:
            rg.drafting_decide_and_apply_inprocess(model_a, spec_a, sims_a, c_puct_a)
        elif cur == board_a:
            action, _v = worker_a.ask(rg.state_json(), rg.pending_search_seed())
            rg.drafting_apply_external(json.dumps(action))
        else:
            # PER-ENTSCHEIDUNG-Protokoll (par.8d): EINE Anfrage = EINE
            # Drafting-Entscheidung. `advance_to_decision` ist billig, wenn
            # nichts aufzuloesen ist (kehrt sofort mit "drafting" zurueck) --
            # der Aussenschleife ueberlaesst deshalb JEDEN einzelnen Schritt
            # eines mehrstufigen Kuppel-/Stapel-Zugs (Peek, Stapel-Slot,
            # Rotation) derselben Behandlung wie eine neue Entscheidung,
            # keine Sonderbehandlung nach Aktionstyp.
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
    ap.add_argument("--model-a", default=None,
                    help="Modellpfad fuer Seite A (aktuelle Engine, in-process). "
                         "Entfaellt bei --artifact-dir-a.")
    ap.add_argument("--artifact-dir-a", default=None,
                    help="Seite A ist ebenfalls ein gefrorenes Artefakt (eigener Worker, "
                         "eigenes Wheel). Damit spielen zwei Artefakte GEGENEINANDER -- der "
                         "Fall, fuer den die Prozess-Isolation gebaut wurde.")
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
    ap.add_argument("--workers", type=int, default=1,
                    help="gleichzeitige Referee-Prozesse. Partien sind unabhaengig; je Prozess "
                         "startet ein eigener Worker (bzw. ein Paar). 1 = seriell wie bisher.")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    artifact_dir = Path(args.artifact_dir).resolve()
    manifest = load_manifest(artifact_dir)
    ist_heuristik = manifest.get("typ") == "heuristik"
    # Welle-3-Netz-Artefakte tragen ihren Interpreter im Manifest. Ein
    # Heuristik-Artefakt tut das nicht -- seine venv wird bei Bedarf gebaut
    # (verify_frozen_heuristic.py --build-venv) und ist bewusst nicht
    # versioniert.
    if "worker_python" in manifest:
        worker_python = artifact_dir / manifest["worker_python"]["interpreter_relative"]
    else:
        eigene = [artifact_dir / "venv/Scripts/python.exe", artifact_dir / "venv/bin/python"]
        gefunden = next((p for p in eigene if p.exists()), None)
        if gefunden is None:
            # KEIN stiller Rueckfall: das Artefakt auf dem AKTUELLEN Wheel zu
            # fahren beantwortet die Drift-Frage, nicht die Konservierungs-
            # Frage. Beides ist nuetzlich, aber es sind verschiedene Fragen,
            # und ein Bericht, der sie vermengt, ist wertlos.
            raise SystemExit(
                f"Keine venv in {artifact_dir}. Anlegen mit:\n"
                f"  python tools/verify_frozen_heuristic.py --artifact-dir {artifact_dir} "
                f"--build-venv\n"
                "Ohne sie liefe das Artefakt auf dem heutigen Wheel -- das waere ein "
                "Drift-Test, kein Match gegen den eingefrorenen Agenten.")
        worker_python = gefunden
    worker_script = REPO / "tools" / "frozen_champion_worker.py"

    sys.path.insert(0, str(REPO))
    import mosaic_rust as mr

    handshake = static_handshake(manifest, args.force_cross_era)
    print(f"[referee] Handshake: {handshake}", file=sys.stderr)

    if not args.artifact_dir_a and not args.model_a:
        raise SystemExit(
            "Seite A ist unbesetzt: entweder --model-a (aktuelle Engine, in-process) "
            "oder --artifact-dir-a (zweites gefrorenes Artefakt).")

    worker = WorkerProc(worker_python, worker_script, artifact_dir, args.sims_worker, args.c_puct_worker)
    time.sleep(0.2)  # Worker-Startzeit (Modell laden) -- erste Anfrage wartet ohnehin, reine Kulanz

    # --- Seite A als zweites Artefakt (optional)
    worker_a = None
    manifest_a = None
    artifact_dir_a = None
    if args.artifact_dir_a:
        artifact_dir_a = Path(args.artifact_dir_a).resolve()
        manifest_a = load_manifest(artifact_dir_a)
        # DIESELBEN Tore wie fuer die B-Seite. Ein zweites Artefakt ohne
        # Handshake und ohne Golden-Selbsttest waere die Haelfte der Zusage:
        # die Verweigerung bei Aera-Mismatch ist genau das, was die Leiter
        # zusammenhaelt.
        handshake_a = static_handshake(manifest_a, args.force_cross_era)
        print(f"[referee] Handshake A: {handshake_a}", file=sys.stderr)
        eigene_a = [artifact_dir_a / "venv/Scripts/python.exe", artifact_dir_a / "venv/bin/python"]
        py_a = next((q for q in eigene_a if q.exists()), None)
        if "worker_python" in manifest_a:
            py_a = artifact_dir_a / manifest_a["worker_python"]["interpreter_relative"]
        if py_a is None:
            worker.close()
            raise SystemExit(
                f"Keine venv in {artifact_dir_a}. Anlegen mit:" + chr(10) +
                f"  python tools/verify_frozen_heuristic.py --artifact-dir {artifact_dir_a} "
                "--build-venv")
        if not args.skip_golden and manifest_a.get("typ") == "heuristik":
            try:
                golden_selbsttest_heuristik(py_a, artifact_dir_a, REPO)
            except SystemExit:
                worker.close()
                raise
        worker_a = WorkerProc(py_a, worker_script, artifact_dir_a, args.sims_a, args.c_puct_a)
        time.sleep(0.2)

    golden_mismatches = []
    if not args.skip_golden and ist_heuristik:
        try:
            golden_selbsttest_heuristik(worker_python, artifact_dir, REPO)
        except SystemExit:
            worker.close()
            raise
    elif not args.skip_golden:
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

    names = (manifest_a.get("artefakt", "ArtefaktA") if manifest_a else "EngineA",
             manifest.get("artefakt") or manifest.get("champion") or "ArtefaktB")
    # Nur Artefakte, deren Worker das erweiterte Protokoll kennt, entscheiden
    # Startsetzung und Tiling selbst. Das Manifest-Feld `typ` gibt es seit
    # 2026-08-26; ein Welle-3-Netz-Artefakt hat es nicht und bleibt beim
    # Bestandsverhalten -- sein Worker laeuft auf einem aelteren Wheel und
    # wuerde eine Tiling-Anfrage als Drafting missverstehen.
    # Eine Heuristik MUSS ihre Platzierung selbst entscheiden -- sonst kachelt
    # sie ueber den auf V1 verdrahteten Referee-Pfad und ist ein anderer
    # Spieler als der eingefrorene. Kann ihr Wheel das nicht, wird verweigert.
    kinds = set((manifest.get("protokoll") or {}).get("kinds") or [])
    if ist_heuristik and not {"tiling", "start_placement"} <= kinds:
        worker.close()
        raise SystemExit(
            f"Artefakt {artifact_dir.name} deklariert das erweiterte Protokoll nicht "
            f"(protokoll.kinds={sorted(kinds) or 'fehlt'}).\n"
            "Sein Wheel stammt aus der Zeit vor Bausteinen 3/4 und kann Platzierung und "
            "Startsetzung nicht selbst entscheiden. Es hier trotzdem zu fahren hiesse, es "
            "ueber den auf V1 verdrahteten Referee-Pfad kacheln zu lassen -- also gegen einen "
            "ANDEREN Spieler zu messen als den eingefrorenen.\n"
            "Abhilfe: das Artefakt mit dem heutigen Wheel neu einfrieren.")
    externe_seiten_aktiv = ist_heuristik
    # Auch die A-Seite entscheidet selbst, wenn sie ein protokollfaehiges
    # Heuristik-Artefakt ist. Sonst kachelte SIE ueber den auf V1
    # verdrahteten Referee-Pfad -- derselbe Fehler, nur auf der anderen Seite.
    kinds_a = set(((manifest_a or {}).get("protokoll") or {}).get("kinds") or [])
    a_ist_heuristik = (manifest_a or {}).get("typ") == "heuristik"
    if a_ist_heuristik and not {"tiling", "start_placement"} <= kinds_a:
        worker.close()
        if worker_a:
            worker_a.close()
        raise SystemExit(
            f"Artefakt A {artifact_dir_a.name} deklariert das erweiterte Protokoll nicht "
            f"(protokoll.kinds={sorted(kinds_a) or 'fehlt'}). Neu einfrieren.")
    externe_seiten_a_aktiv = a_ist_heuristik
    # Eine Heuristik hat kein `model.onnx`. Der Pfad wuerde zwar nie geladen
    # (fuer externe Seiten kehrt `advance_to_decision` vorher zurueck), aber
    # einen Pfad mitzugeben, der nicht existiert, ist eine Falle fuer den
    # naechsten Leser.
    artefakt_modell = None if ist_heuristik else str(artifact_dir / "model.onnx")
    print(f"[referee] externe Platzierung/Startsetzung: "
          f"{'AN' if externe_seiten_aktiv else 'aus (Netz-Artefakt)'}", file=sys.stderr)
    # --- Blockaufteilung. Mindestens MIN_JE_BLOCK Partien je Prozess, sonst
    # frisst der Worker-Start (Wheel laden, bei Netzen zusaetzlich das ONNX)
    # den Gewinn wieder auf. Der Wert ist gesetzt, nicht hergeleitet: bei
    # gemessenen ~3,3 s je Partie und ~1-2 s Worker-Start ist ab vier Partien
    # je Block der Overhead unter 15 Prozent.
    MIN_JE_BLOCK = 4
    n_proz = max(1, min(args.workers, max(1, len(seeds) // MIN_JE_BLOCK)))
    indiziert = list(enumerate(seeds))
    bloecke = [indiziert[k::n_proz] for k in range(n_proz)]
    bloecke = [b for b in bloecke if b]
    print(f"[referee] {len(seeds)} Partien auf {len(bloecke)} Prozess(e)", file=sys.stderr)

    basis = {
        "worker_python": str(worker_python), "worker_script": str(worker_script),
        "artifact_dir": str(artifact_dir), "sims_worker": args.sims_worker,
        "c_puct_worker": args.c_puct_worker,
        "artifact_dir_a": str(artifact_dir_a) if artifact_dir_a else None,
        "worker_python_a": str(py_a) if artifact_dir_a else None,
        "model_a": args.model_a, "spec_a": args.spec_a,
        "sims_a": args.sims_a, "c_puct_a": args.c_puct_a,
        "artefakt_modell": artefakt_modell, "names": list(names),
        "externe_b": externe_seiten_aktiv, "externe_a": externe_seiten_a_aktiv,
    }

    t_start = time.perf_counter()
    if len(bloecke) == 1:
        # Seriell im ELTERNPROZESS -- die bereits gestarteten Worker werden
        # weiterbenutzt, kein zweiter Start. Bestandsverhalten.
        games = []
        for i, seed in bloecke[0]:
            first_player = i % 2
            board_a = i % 2
            externe = []
            if externe_seiten_aktiv:
                externe.append(1 - board_a)
            if externe_seiten_a_aktiv:
                externe.append(board_a)
            g = play_one_game(
                mr, worker, worker_a, args.model_a, args.spec_a, args.sims_a,
                args.c_puct_a, artefakt_modell, names, first_player, seed, board_a,
                externe_seiten=externe,
            )
            g["_index"] = i
            games.append(g)
            print(f"[referee] Partie {i + 1}/{len(seeds)} seed={seed}: {g['scores']} "
                  f"winner={g['winner']} steps={g['steps']}", file=sys.stderr)
    else:
        # Die Eltern-Worker werden hier NICHT gebraucht -- jeder Kindprozess
        # bringt seine eigenen mit. Vorher schliessen, sonst laufen sie
        # waehrend der ganzen Serie leer mit.
        worker.close()
        if worker_a:
            worker_a.close()
        with mp.Pool(len(bloecke)) as pool:
            teile = pool.map(_spiele_block, [dict(basis, indizierte_seeds=b) for b in bloecke])
        games = [g for teil in teile for g in teil]

    # Reihenfolge wiederherstellen: die Bloecke kommen unsortiert zurueck,
    # jede spaetere Paarung haengt aber an der Seed-Folge.
    games.sort(key=lambda g: g["_index"])
    for g in games:
        g.pop("_index", None)
    total_move_count = sum(g["steps"] for g in games)

    elapsed = time.perf_counter() - t_start
    worker.close()
    if worker_a:
        worker_a.close()

    result = {
        "artifact_dir": str(artifact_dir),
        # `champion` gibt es nur bei Netz-Artefakten, eine Heuristik traegt
        # `artefakt`. Beide mitschreiben, statt eines davon zu erzwingen --
        # das Artefakt beschreibt sich selbst, der Bericht verbiegt es nicht.
        "champion": manifest.get("champion"),
        "artefakt": manifest.get("artefakt"),
        "typ": manifest.get("typ", "netz"),
        "seite_a": ({"artefakt": manifest_a.get("artefakt"), "typ": manifest_a.get("typ")}
                    if manifest_a else {"modell": args.model_a, "typ": "aktuelle Engine"}),
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

    # Name aus dem Artefakt, nicht aus einem Feld, das nur eine Sorte kennt:
    # ein Heuristik-Manifest hat kein `champion`, die Datei hiess deshalb
    # `..._None.json`.
    bezeichner = manifest.get("champion") or manifest.get("artefakt") or artifact_dir.name
    out_path = Path(args.out) if args.out else REPO / "evaluations" / f"frozen_referee_match_{bezeichner}.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[referee] fertig: {wins_a} A / {wins_b} B / {draws} Remis, geschrieben nach {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
