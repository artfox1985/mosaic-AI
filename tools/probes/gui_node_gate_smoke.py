# -*- coding: utf-8 -*-
"""tools/probes/gui_node_gate_smoke.py -- Rauchtest: spielt die GUI-KI wie gemessen?

`PREREG_dome_return_order.md` par.14/14a (Nutzer 2026-09-25: "die gui muss spielen
wie gemessen"). Bis 2026-09-25 setzte `py.rs` das Tor `extended_action_nodes` nie,
und die GUI-KI spielte an drei Stellen einen anderen Agenten als Arena und Gating:
Mondstapel kanonisch, Stapelzug in einem Stueck, Rueckgabe ohne Suchknoten.

Diese Sonde spielt ganze Partien ueber DENSELBEN Einstieg wie `server.py`
(`PyGame.ai_step_net_json`, aufgerufen von `/api/ai/move`) und prueft beide
Richtungen:

  * Seite 0 = die Netz-KI. Sie MUSS die Knoten erreichen: `choose_moon_top`,
    `choose_return_first` und einen Stapelzug in Teilzuegen
    (`dome_stack_peek` -> `choose_draw_stack_slot` -> `choose_dome_rotation`).
  * Seite 1 = vertritt den Menschen: kein Netz-Einstieg, also `ai_step_json`
    (Heuristik). Ihr Tor bleibt aus; sieht sie je einen der Knoten, ist das Tor
    auf die falsche Seite gelaufen -- ROT.

Dazu die groesste Zahl aufeinanderfolgender KI-Schritte innerhalb EINES Zugs,
gegen den Schrittdeckel des Frontends (`static/js/app.js` triggerAIMove, 200).

Keine Staerkemessung, kein Vergleich zweier Arme: ein Funktionstest gegen eine
lebende Partie. Laeuft einkernig; trotzdem Last -- nie neben einer Messung.

    python -X utf8 -u tools/probes/gui_node_gate_smoke.py --games 4
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys
import time

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

# Knoten, die NUR mit offenem Tor entstehen: `moon_order_node_applies`
# (`game.rs:684`) und `return_order_node_applies` (`game.rs:692`) verlangen beide
# `extended_action_nodes[am Zug]`.
#
# NICHT darunter, obwohl es naheliegt: `choose_draw_stack_slot` und
# `dome_stack_peek`. Der Heuristik-Pfad der GUI (`py.rs` `ai_drafting_step`)
# wendet jede Aktion EINZELN an und spielt den Stapelzug deshalb schon immer in
# Teilzuegen, mit oder ohne Tor. Der erste Lauf am 2026-09-25 hatte den Slot hier
# mitgezaehlt und die Menschenseite faelschlich ROT gemeldet (3 von 4 Partien).
GATED_TYPES = ("choose_moon_top", "choose_return_first")
# Positiv-Beleg fuer die KI: dieselben zwei, plus ein EINZELNER Peek-Schritt. Im
# alten Netz-Pfad loeste `apply_chosen_action_with` den Stapelzug in einem Stueck
# auf und meldete den fertigen Zug -- ein alleinstehender `dome_stack_peek` der
# Netz-KI ist darum der Nachweis, dass sie jetzt Teilzug fuer Teilzug entscheidet.
AI_MUST_REACH = GATED_TYPES + ("dome_stack_peek",)
FRONTEND_STEP_CAP = 200  # static/js/app.js triggerAIMove


def champion_paths() -> tuple[str, str]:
    name = (REPO / "models" / "champion.txt").read_text(encoding="utf-8").strip()
    return (f"models/alphazero_{name}.onnx", f"models/{name}.spec.json")


def main() -> int:
    model_default, spec_default = champion_paths()
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=model_default)
    ap.add_argument("--spec", default=spec_default)
    ap.add_argument("--games", type=int, default=4)
    ap.add_argument("--seed-base", type=int, default=20262500)
    ap.add_argument("--sims", type=int, default=100)
    ap.add_argument("--max-steps", type=int, default=4000,
                    help="Deckel je Partie gegen einen haengenden Treiber")
    ap.add_argument("--out", default="evaluations/artifacts/gui_node_gate_smoke.json")
    args = ap.parse_args()

    # Wie server.py: die Champion-Spec geht VOR dem Import in die Umgebung.
    from spec_env import apply_spec_env
    spec = json.loads((REPO / args.spec).read_text(encoding="utf-8"))
    apply_spec_env(spec, respect_existing=True)
    import mosaic_rust as mr
    from runtime_block import laufzeit_block

    t0, c0 = time.monotonic(), time.process_time()
    games = []
    red = []
    for gi in range(args.games):
        seed = args.seed_base + gi
        first = gi % 2
        g = mr.PyGame(("KI", "Mensch"), first_player=first, seed=seed)
        g.load_net(str(REPO / args.model))
        # Regel: wer NICHT anfaengt, legt die Startkuppel zuerst (die Engine
        # verweigert sonst mit "Nicht-Startspieler muss zuerst ...").
        for p in (1 - first, first):
            g.ai_start_tile_json(p, args.sims)

        types = {0: collections.Counter(), 1: collections.Counter()}
        run, max_run, last_player, steps = 0, 0, None, 0
        stalled = None
        while not g.is_over() and steps < args.max_steps:
            phase, pi = g.phase(), g.current_player()
            if phase not in ("drafting", "tiling"):
                stalled = f"Phase {phase!r} ohne KI-Aktion"
                break
            if pi == 0:
                res = json.loads(g.ai_step_net_json(args.sims, 1.5, False))
            else:
                res = json.loads(g.ai_step_json(args.sims, False))
            steps += 1
            if not res.get("applied"):
                stalled = f"Schritt {steps}, Seite {pi}, Phase {phase}: {res.get('reason')}"
                break
            if phase == "drafting":
                typ = (res.get("action") or {}).get("type", "?")
                types[pi][typ] += 1
                if pi == 0:
                    run = run + 1 if last_player == 0 else 1
                    max_run = max(max_run, run)
                last_player = pi
            else:
                last_player = None

        leaked = {t: types[1][t] for t in GATED_TYPES if types[1][t]}
        if stalled:
            red.append(f"Partie {gi} (seed {seed}) haengt: {stalled}")
        if not g.is_over() and not stalled:
            red.append(f"Partie {gi} (seed {seed}): Schrittdeckel {args.max_steps} erreicht")
        if leaked:
            red.append(f"Partie {gi} (seed {seed}): Tor auf der MENSCHEN-Seite offen: {leaked}")
        if max_run >= FRONTEND_STEP_CAP:
            red.append(f"Partie {gi} (seed {seed}): {max_run} KI-Schritte in einem Zug "
                       f">= Frontend-Deckel {FRONTEND_STEP_CAP}")
        games.append({
            "seed": seed, "steps": steps, "over": g.is_over(),
            "ai_types": dict(types[0]), "human_types": dict(types[1]),
            "max_ai_steps_in_one_turn": max_run,
        })
        print(f"[smoke] Partie {gi + 1}/{args.games} seed={seed} Schritte={steps} "
              f"KI-Knoten: moon={types[0]['choose_moon_top']} "
              f"return={types[0]['choose_return_first']} "
              f"slot={types[0]['choose_draw_stack_slot']} "
              f"peek={types[0]['dome_stack_peek']} | max KI-Folge {max_run}",
              flush=True)

    ai_total = collections.Counter()
    for gm in games:
        ai_total.update(gm["ai_types"])
    # Die positive Richtung: ueber alle Partien muss die KI jeden Knoten
    # mindestens einmal erreicht haben -- sonst belegt der Lauf nichts.
    unreached = [t for t in AI_MUST_REACH if not ai_total[t]]
    if unreached:
        red.append(f"KI hat diese Knoten in {args.games} Partien NIE erreicht: {unreached} "
                   "(Tor zu, oder zu wenige Partien)")

    result = {
        "model": args.model, "spec": args.spec, "sims": args.sims,
        "games": games, "ai_types_total": dict(ai_total),
        "verdict": "GRUEN" if not red else "ROT", "red": red,
        "laufzeit": laufzeit_block(t0, cpu_start=c0, threads=1, n_games=args.games),
    }
    out = REPO / args.out
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[smoke] {result['verdict']}  KI gesamt: {dict(ai_total)}", flush=True)
    for r in red:
        print(f"[smoke] ROT: {r}", flush=True)
    print(f"[smoke] geschrieben: {out}", flush=True)
    return 0 if not red else 1


if __name__ == "__main__":
    raise SystemExit(main())
