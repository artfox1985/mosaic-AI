# -*- coding: utf-8 -*-
"""Spielt ein gefrorenes Agenten-Artefakt VOLLSTAENDIG ueber den Referee-Pfad.

Nutzer-Richtung 2026-08-26: gefrorene Agenten sind nicht nur fuer Self-Play da,
sie sollen gegeneinander spielen.

WAS HIER GEPRUEFT WIRD, UND WARUM ES NICHT SELBSTVERSTAENDLICH IST
------------------------------------------------------------------
Bis 2026-08-26 delegierte der Referee nur die DRAFTING-Entscheidung. Tiling und
Startsetzung loeste er selbst auf -- ueber einen auf `V1` verdrahteten Pfad.
Ein gefrorenes `v2huelle`-Artefakt haette in der Referee-Arena also als `v1`
gekachelt: dieselbe Klasse Fehler wie "Signatur da, Wirkung nicht", nur
teurer, weil das Ergebnis plausibel aussieht.

  A) LAEUFT es -- eine ganze Partie mit externem Tiling ohne Deadlock.
  B) WIRKT die Variante -- v1 und v2huelle nehmen aus derselben Startlage
     einen anderen Verlauf. Ohne B belegt A nur, dass nichts abstuerzt.
  C) PRALLT Unsinn ab -- ein illegaler Schritt wird hart abgewiesen, nicht
     still ersetzt. Das ist die Zusage, die die Regel-Autoritaet beim Referee
     haelt, obwohl die ENTSCHEIDUNG von aussen kommt.

UMGESTELLT 2026-08-26 (B4a): die Sonde fuhr die Agenten IN-PROCESS ueber die
aktuelle Engine, also ueber eine NACHBILDUNG des Artefakts auf dem heutigen
Wheel. Jetzt spricht sie den WORKER des Artefakts an -- denselben Prozess, der
auch in einer Messung laeuft, mit dem Wheel des Artefakts.

Das war ohnehin die staerkere Bauform und wurde durch B4a nur erzwungen: sobald
v2 aus dem Quellstand verschwindet, KANN die aktuelle Engine `v2huelle` nicht
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

V1 = _ROOT / "models/frozen_heuristics/v1_anchor"
V2H = _ROOT / "models/frozen_heuristics/v2huelle_generator"

SIMS, C_PUCT = 150, 0.3

# FESTGENAGELTE Erwartung. Kein Schoenheitsfehler, wenn sie bricht: am
# 2026-08-26 hat eine Aenderung im Worker dazu gefuehrt, dass das
# v2huelle-Artefakt sein TILING-Netz auch fuers Drafting benutzte -- es
# spielte als Netz statt als Heuristik. Aufgefallen ist das nur, weil die
# Partieergebnisse sich gegenueber dem Lauf davor aenderten, also durch Zufall.
#
# Diese Zahlen sind der Ersatz fuer diesen Zufall. Aendern sie sich, ist das
# ein BEFUND und gehoert erklaert, bevor die Zahl hier angepasst wird.
ERWARTET = {
    "v1_anchor":          {"scores": [27, 15], "steps": 159},
    "v2huelle_generator": {"scores": [63, 27], "steps": 163},
}


def _worker(artefakt: pathlib.Path) -> WorkerProc:
    """Startet den Worker eines Artefakts auf DESSEN venv."""
    py = next((artefakt / rel for rel in ("venv/Scripts/python.exe", "venv/bin/python")
               if (artefakt / rel).exists()), None)
    if py is None:
        raise SystemExit(
            f"Keine venv in {artefakt}. Anlegen mit:" + chr(10) +
            f"  python tools/verify_frozen_heuristic.py --artifact-dir {artefakt} --build-venv")
    return WorkerProc(py, _ROOT / "tools" / "frozen_champion_worker.py", artefakt,
                      SIMS, C_PUCT)


def partie(artefakt: pathlib.Path, seed: int, extern_seite: int = 1) -> dict:
    """Eine Partie, BEIDE Seiten aus demselben Artefakt.

    EIN Worker genuegt fuer beide: er ist zustandslos je Anfrage -- der
    Zustand kommt mit. `extern_seite` bestimmt nur, fuer welche Seite der
    Referee auch Platzierung und Startsetzung abfragt.
    """
    w = _worker(artefakt)
    rg = mr.RefereeGame(("A", "B"), 0, seed, None)
    tiling_extern = start_extern = 0
    guard = 0
    try:
        while True:
            guard += 1
            if guard > 100_000:
                raise RuntimeError("Schrittlimit -- Haenger-Verdacht")
            st = rg.advance_to_decision(None, None, [extern_seite])
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
    befunde, versagt = {}, []

    for artefakt in (V1, V2H):
        r = partie(artefakt, 4242)
        befunde[artefakt.name] = r
        print(f"{artefakt.name}: {r['scores']}, {r['steps']} Schritte, "
              f"{r['tiling_extern']} externe Tiling-Schritte, "
              f"{r['start_extern']} externe Startsetzungen", flush=True)
        if r["tiling_extern"] == 0:
            versagt.append(f"{artefakt.name}: kein externer Tiling-Schritt")
        if r["start_extern"] == 0:
            versagt.append(f"{artefakt.name}: keine externe Startsetzung")
        soll = ERWARTET[artefakt.name]
        if [r["scores"], r["steps"]] != [soll["scores"], soll["steps"]]:
            versagt.append(
                f"{artefakt.name} weicht von der festgenagelten Erwartung ab: "
                f"{r['scores']}/{r['steps']} statt {soll['scores']}/{soll['steps']} "
                "-- ERST erklaeren, dann die Zahl hier anpassen")

    a, b = befunde[V1.name], befunde[V2H.name]
    wirkt = (a["scores"] != b["scores"]) or (a["steps"] != b["steps"])
    befunde["variante_wirkt"] = wirkt
    print(f"Verlaeufe unterschiedlich? {wirkt}", flush=True)
    if not wirkt:
        versagt.append("v1 und v2huelle nehmen denselben Verlauf -- die Variante kommt nicht an")

    # --- C) prallt Unsinn ab
    w = _worker(V1)
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
        boese = json.dumps({"type": "place", "pattern_row": 99, "slot_row": 99,
                            "slot_col": 99, "space_index": 99})
        try:
            rg.tiling_apply_external(boese)
            print("C) ROT -- illegaler Schritt wurde ANGENOMMEN", flush=True)
            versagt.append("illegaler Tiling-Schritt wurde angenommen")
            befunde["c_abgewiesen"] = False
        except ValueError as e:
            print(f"C) illegaler Schritt abgewiesen: {str(e)[:90]}...", flush=True)
            befunde["c_abgewiesen"] = True
    finally:
        w.close()

    befunde["verdikt"] = "GRUEN" if not versagt else "ROT"
    befunde["versagt"] = versagt
    befunde["laufzeit"] = {"wanduhr_s": round(time.monotonic() - t0, 1), "cpu_s": None,
                           "threads": 1, "s_je_partie": None}
    ziel = pathlib.Path("evaluations/artifacts/frozen_agent_referee.json")
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(json.dumps(befunde, indent=2, ensure_ascii=False), encoding="utf-8",
                    newline="\n")
    print(f"\n{befunde['verdikt']}\nArtefakt: {ziel}")
    if versagt:
        for v in versagt:
            print(f"  - {v}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
