# -*- coding: utf-8 -*-
"""Spielt ein gefrorenes Agenten-Artefakt VOLLSTAENDIG ueber den Referee-Pfad.

Nutzer-Richtung 2026-08-26: gefrorene Agenten sind nicht nur fuer Self-Play da,
sie sollen gegeneinander spielen.

WAS HIER GEPRUEFT WIRD, UND WARUM ES NICHT SELBSTVERSTAENDLICH IST
------------------------------------------------------------------
Bis 2026-08-26 delegierte der Referee nur die DRAFTING-Entscheidung. Tiling und
Startsetzung loeste er selbst auf -- ueber einen auf `hv1` verdrahteten Pfad.
Ein gefrorenes `hv2`-Artefakt haette in der Referee-Arena also als `hv1`
gekachelt: dieselbe Klasse Fehler wie "Signatur da, Wirkung nicht", nur
teurer, weil das Ergebnis plausibel aussieht.

  A) LAEUFT es -- eine ganze Partie mit externem Tiling ohne Deadlock.
  B) WIRKT die Variante -- hv1 und hv2 nehmen aus derselben Startlage
     einen anderen Verlauf. Ohne B belegt A nur, dass nichts abstuerzt.
  C) PRALLT Unsinn ab -- ein illegaler Schritt wird hart abgewiesen, nicht
     still ersetzt. Das ist die Zusage, die die Regel-Autoritaet beim Referee
     haelt, obwohl die ENTSCHEIDUNG von aussen kommt.

UMGESTELLT 2026-08-26 (B4a): die Sonde fuhr die Agenten IN-PROCESS ueber die
aktuelle Engine, also ueber eine NACHBILDUNG des Artefakts auf dem heutigen
Wheel. Jetzt spricht sie den WORKER des Artefakts an -- denselben Prozess, der
auch in einer Messung laeuft, mit dem Wheel des Artefakts.

Das war ohnehin die staerkere Bauform und wurde durch B4a nur erzwungen: sobald
hv2 aus dem Quellstand verschwindet, KANN die aktuelle Engine `hv2` nicht
mehr spielen. Eine Sonde, die es trotzdem versucht, wuerde entweder scheitern
oder -- schlimmer -- still etwas anderes messen.

Aufruf (Sekunden; braucht die venvs der Artefakte,
`verify_frozen_heuristic.py --build-venv`):
    python -X utf8 -u tools/probes/frozen_agent_referee_probe.py
"""
import json
import pathlib
import sys
import time

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "engine" / "py"))
sys.path.insert(0, str(_ROOT / "tools"))

import mosaic_rust as mr  # noqa: E402

from frozen_referee_match import WorkerProc  # noqa: E402

HV1 = _ROOT / "models/frozen_heuristics/hv1_anchor"
HV2 = _ROOT / "models/frozen_heuristics/hv2_generator"

SIMS, C_PUCT = 150, 0.3

# FESTGENAGELTE Erwartung. Kein Schoenheitsfehler, wenn sie bricht: am
# 2026-08-26 hat eine Aenderung im Worker dazu gefuehrt, dass das
# hv2-Artefakt sein TILING-Netz auch fuers Drafting benutzte -- es
# spielte als Netz statt als Heuristik. Aufgefallen ist das nur, weil die
# Partieergebnisse sich gegenueber dem Lauf davor aenderten, also durch Zufall.
#
# Diese Zahlen sind der Ersatz fuer diesen Zufall. Aendern sie sich, ist das
# ein BEFUND und gehoert erklaert, bevor die Zahl hier angepasst wird.
EXPECTED = {
    "hv1_anchor":   {"scores": [27, 15], "steps": 159},
    "hv2_generator": {"scores": [63, 27], "steps": 163},
}


def _worker(artifact_name: pathlib.Path) -> WorkerProc:
    """Startet den Worker eines Artefakts auf DESSEN venv."""
    py = next((artifact_name / rel for rel in ("venv/Scripts/python.exe", "venv/bin/python")
               if (artifact_name / rel).exists()), None)
    if py is None:
        raise SystemExit(
            f"Keine venv in {artifact_name}. Anlegen mit:" + chr(10) +
            f"  python tools/verify_frozen_heuristic.py --artifact-dir {artifact_name} --build-venv")
    return WorkerProc(py, _ROOT / "tools" / "frozen_champion_worker.py", artifact_name,
                      SIMS, C_PUCT)


def game(artifact_name: pathlib.Path, seed: int, external_side: int = 1) -> dict:
    """Eine Partie, BEIDE Seiten aus demselben Artefakt.

    EIN Worker genuegt fuer beide: er ist zustandslos je Anfrage -- der
    Zustand kommt mit. `extern_seite` bestimmt nur, fuer welche Seite der
    Referee auch Platzierung und Startsetzung abfragt.
    """
    w = _worker(artifact_name)
    rg = mr.RefereeGame(("A", "B"), 0, seed, None)
    tiling_extern = start_extern = 0
    guard = 0
    try:
        while True:
            guard += 1
            if guard > 100_000:
                raise RuntimeError("Schrittlimit -- Haenger-Verdacht")
            st = rg.advance_to_decision(None, None, [external_side])
            if st == "game_over":
                rg.finalize_scoring()
                break
            if st == "stuck":
                raise RuntimeError(f"Deadlock bei steps={rg.steps()}, phase={rg.phase()}")
            if st == "tiling":
                rg.tiling_apply_external(json.dumps(w.ask_tiling(rg.state_json())))
                tiling_extern += 1
                continue
            if st == "start_placement":
                # `pending_start_placement_player()`, NICHT `current_player()`:
                # in dieser Phase kann der Nicht-Starter zuerst dran sein.
                pi = rg.pending_start_placement_player()
                rg.start_placement_apply_external(json.dumps(
                    w.ask_start_placement(rg.state_json(), pi, rg.game_seed())))
                start_extern += 1
                continue
            act, _v = w.ask(rg.state_json(), rg.pending_search_seed())
            rg.drafting_apply_external(json.dumps(act))
    finally:
        w.close()
    return {"scores": list(rg.scores()), "steps": rg.steps(),
            "tiling_extern": tiling_extern, "start_extern": start_extern}


def main() -> int:
    t0 = time.monotonic()
    findings, failures = {}, []

    for artifact_name in (HV1, HV2):
        r = game(artifact_name, 4242)
        findings[artifact_name.name] = r
        print(f"{artifact_name.name}: {r['scores']}, {r['steps']} Schritte, "
              f"{r['tiling_extern']} externe Tiling-Schritte, "
              f"{r['start_extern']} externe Startsetzungen", flush=True)
        if r["tiling_extern"] == 0:
            failures.append(f"{artifact_name.name}: kein externer Tiling-Schritt")
        if r["start_extern"] == 0:
            failures.append(f"{artifact_name.name}: keine externe Startsetzung")
        expected = EXPECTED[artifact_name.name]
        if [r["scores"], r["steps"]] != [expected["scores"], expected["steps"]]:
            failures.append(
                f"{artifact_name.name} weicht von der festgenagelten Erwartung ab: "
                f"{r['scores']}/{r['steps']} statt {expected['scores']}/{expected['steps']} "
                "-- ERST erklaeren, dann die Zahl hier anpassen")

    a, b = findings[HV1.name], findings[HV2.name]
    effective = (a["scores"] != b["scores"]) or (a["steps"] != b["steps"])
    findings["variante_wirkt"] = effective
    print(f"Verlaeufe unterschiedlich? {effective}", flush=True)
    if not effective:
        failures.append("hv1 und hv2 nehmen denselben Verlauf -- die Variante kommt nicht an")

    # --- C) prallt Unsinn ab
    w = _worker(HV1)
    rg = mr.RefereeGame(("A", "B"), 0, 4242, None)
    try:
        while True:
            st = rg.advance_to_decision(None, None, [1])
            if st == "tiling":
                break
            if st in ("game_over", "stuck"):
                raise RuntimeError("keine Tiling-Entscheidung erreicht")
            if st == "start_placement":
                pi = rg.pending_start_placement_player()
                rg.start_placement_apply_external(json.dumps(
                    w.ask_start_placement(rg.state_json(), pi, rg.game_seed())))
                continue
            act, _v = w.ask(rg.state_json(), rg.pending_search_seed())
            rg.drafting_apply_external(json.dumps(act))
        bogus = json.dumps({"type": "place", "pattern_row": 99, "slot_row": 99,
                            "slot_col": 99, "space_index": 99})
        try:
            rg.tiling_apply_external(bogus)
            print("C) ROT -- illegaler Schritt wurde ANGENOMMEN", flush=True)
            failures.append("illegaler Tiling-Schritt wurde angenommen")
            findings["c_abgewiesen"] = False
        except ValueError as e:
            print(f"C) illegaler Schritt abgewiesen: {str(e)[:90]}...", flush=True)
            findings["c_abgewiesen"] = True
    finally:
        w.close()

    findings["verdikt"] = "GRUEN" if not failures else "ROT"
    findings["versagt"] = failures
    findings["laufzeit"] = {"wanduhr_s": round(time.monotonic() - t0, 1), "cpu_s": None,
                           "threads": 1, "s_je_partie": None}
    target = pathlib.Path("evaluations/artifacts/frozen_agent_referee.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(findings, indent=2, ensure_ascii=False), encoding="utf-8",
                    newline="\n")
    print(f"\n{findings['verdikt']}\nArtefakt: {target}")
    if failures:
        for v in failures:
            print(f"  - {v}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
