# -*- coding: utf-8 -*-
"""Spielt ein gefrorenes Agenten-Artefakt VOLLSTAENDIG ueber den Referee-Pfad.

Nutzer-Richtung 2026-08-26: gefrorene Agenten sind nicht nur fuer Self-Play da,
sie sollen gegeneinander spielen. Erst dann darf die Variante aus dem
Engine-Code verschwinden.

WAS HIER GEPRUEFT WIRD, UND WARUM ES NICHT SELBSTVERSTAENDLICH IST
------------------------------------------------------------------
Bis 2026-08-26 delegierte der Referee nur die DRAFTING-Entscheidung. Tiling und
Startsetzung loeste er selbst auf -- ueber `resolve_tiling_step`, und das ist
auf `V1` verdrahtet (self_play.rs). Ein gefrorenes `v2huelle`-Artefakt haette
in der Referee-Arena also als `v1` gekachelt: dieselbe Klasse Fehler wie
"Signatur da, Wirkung nicht", nur teurer, weil das Ergebnis plausibel aussieht.

Die Sonde prueft deshalb drei getrennte Dinge:

  A) LAEUFT es -- eine ganze Partie mit externem Tiling ohne Deadlock.
  B) WIRKT die Variante -- v1 und v2huelle nehmen aus derselben Startlage
     einen anderen Verlauf. Ohne B belegt A nur, dass nichts abstuerzt.
  C) PRALLT Unsinn ab -- ein illegaler Schritt wird hart abgewiesen, nicht
     still ersetzt. Das ist die Zusage, die die Regel-Autoritaet beim Referee
     haelt, obwohl die ENTSCHEIDUNG von aussen kommt.

Aufruf (netzfrei bis auf das Tiling-Netz des Artefakts, Sekunden):
    python -X utf8 -u tools/probes/frozen_agent_referee_probe.py
"""
import json
import pathlib
import sys
import time

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "engine" / "py"))

import mosaic_rust as mr  # noqa: E402

V1 = _ROOT / "models/frozen_heuristics/v1_anchor/spec.json"
V2H = _ROOT / "models/frozen_heuristics/v2huelle_generator/spec.json"
NET = _ROOT / "models/frozen_heuristics/v2huelle_generator/tiling_net.onnx"

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
    "v1":       {"scores": [27, 15], "steps": 159},
    "v2huelle": {"scores": [63, 27], "steps": 163},
}


def partie(spec, netz, seed, extern_seite=1):
    """Eine Partie; `extern_seite` liefert Drafting UND Tiling von aussen.

    Der Referee bleibt Regel-Autoritaet: er haelt den Zustand, sagt wann eine
    Entscheidung ansteht, und prueft jede eingereichte Aktion.
    """
    rg = mr.RefereeGame(("A", "B"), 0, seed, None)
    tiling_extern = 0
    start_extern = 0
    guard = 0
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
            rg.tiling_apply_external(
                mr.tiling_choice_state_json(rg.state_json(), str(spec),
                                            str(netz) if netz else None))
            tiling_extern += 1
            continue
        if st == "start_placement":
            # `pending_start_placement_player()`, NICHT `current_player()`:
            # in dieser Phase kann der Nicht-Starter zuerst dran sein.
            pi = rg.pending_start_placement_player()
            rg.start_placement_apply_external(
                mr.start_placement_choice_state_json(rg.state_json(), pi,
                                                     rg.game_seed(), str(spec)))
            start_extern += 1
            continue
        act = json.loads(mr.heuristic_arena_choice_state_json(
            rg.state_json(), SIMS, C_PUCT, rg.pending_search_seed(), str(spec)))["action"]
        rg.drafting_apply_external(json.dumps(act))
    return {"scores": list(rg.scores()), "steps": rg.steps(),
            "tiling_extern": tiling_extern, "start_extern": start_extern}


def main() -> int:
    t0 = time.monotonic()
    befunde = {}
    versagt = []

    # --- A) laeuft es
    a = partie(V1, None, 4242)
    befunde["a_v1"] = a
    print(f"A) v1 ueber den Referee: {a['scores']}, {a['steps']} Schritte, "
          f"{a['tiling_extern']} externe Tiling-Schritte, "
          f"{a['start_extern']} externe Startsetzungen", flush=True)
    if a["tiling_extern"] == 0:
        versagt.append("kein einziger externer Tiling-Schritt -- der Referee hat selbst gekachelt")
    if a["start_extern"] == 0:
        versagt.append("keine externe Startsetzung -- der Referee hat selbst gesetzt")

    # --- B) wirkt die Variante
    b = partie(V2H, NET, 4242)
    befunde["b_v2huelle"] = b
    print(f"B) v2huelle ueber den Referee: {b['scores']}, {b['steps']} Schritte, "
          f"{b['tiling_extern']} externe Tiling-Schritte, "
          f"{b['start_extern']} externe Startsetzungen", flush=True)
    # Gegen die festgenagelte Erwartung pruefen, nicht nur gegeneinander.
    for name, ist in (("v1", a), ("v2huelle", b)):
        soll = ERWARTET[name]
        if [ist["scores"], ist["steps"]] != [soll["scores"], soll["steps"]]:
            versagt.append(
                f"{name} weicht von der festgenagelten Erwartung ab: "
                f"{ist['scores']}/{ist['steps']} statt {soll['scores']}/{soll['steps']} "
                "-- ERST erklaeren, dann die Zahl hier anpassen")
    wirkt = (a["scores"] != b["scores"]) or (a["steps"] != b["steps"])
    befunde["variante_wirkt"] = wirkt
    print(f"   Verlaeufe unterschiedlich? {wirkt}", flush=True)
    if not wirkt:
        versagt.append("v1 und v2huelle nehmen denselben Verlauf -- die Variante kommt nicht an")

    # --- C) prallt Unsinn ab
    rg = mr.RefereeGame(("A", "B"), 0, 4242, None)
    while True:
        st = rg.advance_to_decision(None, None, [1])
        if st == "tiling":
            break
        if st in ("game_over", "stuck"):
            raise RuntimeError("keine Tiling-Entscheidung erreicht")
        if st == "start_placement":
            pi = rg.pending_start_placement_player()
            rg.start_placement_apply_external(
                mr.start_placement_choice_state_json(rg.state_json(), pi,
                                                     rg.game_seed(), str(V1)))
            continue
        act = json.loads(mr.heuristic_arena_choice_state_json(
            rg.state_json(), SIMS, C_PUCT, rg.pending_search_seed(), str(V1)))["action"]
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
