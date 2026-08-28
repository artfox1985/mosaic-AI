"""Golden-Probe-Generator fuer eingefrorene Champion-Artefakte
(PREREG_agent_encapsulation.md par.8, Welle 3).

Baut `golden_probe.json` NEU: N Drafting-Zustaende (LIVE `RefereeGame`-
Zustaende, `state_to_json_exact` -- traegt seit par.8d zusaetzlich das
fuenfte Pflichtfeld `pending_dome_choice_exact`) samt der vom eingefrorenen
Modell tatsaechlich gewaehlten Antwort (`net_arena_choice_state_json`, EINE
Drafting-Entscheidung je Aufruf, PER-ENTSCHEIDUNG-Protokoll par.8d). Der
Referee spielt diese Sonden beim Laden eines Worker-Prozesses nach
(`tools/frozen_referee_match.py::golden_selftest`, exakter Aktionsvergleich)
-- faengt ORT-/DLL-/Umgebungsdrift, die ein reiner Versions-Stempel nicht sieht.

Aufruf:
    python tools/build_frozen_golden_probe.py --artifact-dir \
        models/frozen_champions/v21_2d_brierbest --seed-base 916001

Sammelt standardmaessig 2 Sonden je Runde (1-5) = 10 Sonden, UND bevorzugt
dabei -- wo im gleichen Rundenlauf verfuegbar -- Zustaende mit einem
angefangenen Kuppel-/Stapel-Zug (`pending_dome_choice` gesetzt): genau DAS
ist der Zwischenzustand, dessen exakter Rundtrip par.8d neu einfuehrt, eine
Sonde dafuer ist deshalb die wertvollste Regressionsabdeckung fuer dieses
Werkzeug.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--artifact-dir", required=True)
    ap.add_argument("--per-round", type=int, default=2, help="Sonden je Runde 1-5 (Default 2 = 10 gesamt)")
    ap.add_argument("--sims", type=int, default=400)
    ap.add_argument("--c-puct", type=float, default=1.5)
    ap.add_argument("--seed-base", type=int, default=916001, help="Erster Partie-Seed (fortlaufend je Partie)")
    ap.add_argument("--probe-seed-base", type=int, default=916101, help="Erster Such-Seed je Sonde (fortlaufend)")
    ap.add_argument("--max-games", type=int, default=40, help="Sicherheitsdeckel -- genug Partien fuer 2 je Runde")
    args = ap.parse_args()

    artifact_dir = Path(args.artifact_dir).resolve()
    model_path = str(artifact_dir / "model.onnx")
    spec_path = str(artifact_dir / "spec.json")

    sys.path.insert(0, str(REPO))
    import mosaic_rust as mr

    per_round_needed = {r: args.per_round for r in range(1, 6)}
    # Kandidaten je Runde: (hat_pending, state_json_str, seed_for_probe, round_no)
    # -- gesammelt, bevor final ausgewaehlt wird, damit `hat_pending`-
    # Kandidaten bevorzugt werden koennen, statt den ERSTEN Treffer blind zu
    # nehmen.
    candidates: dict[int, list[tuple[bool, str, int]]] = {r: [] for r in range(1, 6)}

    game_seed = args.seed_base
    games_played = 0
    while games_played < args.max_games and any(v > 0 for v in per_round_needed.values()):
        games_played += 1
        first_player = games_played % 2
        rg = mr.RefereeGame(("A", "B"), first_player, game_seed, None)
        game_seed += 1
        guard = 0
        while True:
            guard += 1
            if guard > 100_000:
                raise RuntimeError("Golden-Probe-Generator: Schritt-Limit ueberschritten.")
            status = rg.advance_to_decision(model_path, model_path)
            if status == "game_over":
                rg.finalize_scoring()
                break
            if status == "stuck":
                raise RuntimeError(f"Golden-Probe-Generator: Deadlock bei steps={rg.steps()}")
            round_no = rg.round_number()
            state_json = rg.state_json()
            seed_for_decision = rg.pending_search_seed()
            has_pending = json.loads(state_json).get("pending_dome_choice_exact") is not None
            if 1 <= round_no <= 5 and len(candidates[round_no]) < 6:
                # bis zu 6 Kandidaten je Runde sammeln (genug Auswahl fuer
                # die Pending-Praeferenz unten), dann nicht mehr aufzeichnen.
                candidates[round_no].append((has_pending, state_json, seed_for_decision))
            # Zug tatsaechlich anwenden (treibt die Partie weiter) --
            # dieselbe Entscheidung, die spaeter separat ueber
            # net_arena_choice_state_json fuer die Sonden-Antwort neu
            # berechnet wird (deterministisch, gleicher Seed).
            rg.drafting_decide_and_apply_inprocess(model_path, spec_path, args.sims, args.c_puct)

    probes = []
    probe_id = 0
    next_probe_seed = args.probe_seed_base
    for round_no in range(1, 6):
        pool = candidates[round_no]
        # Pending-Zustaende zuerst (par.8d-Regressionsabdeckung), dann Rest,
        # jeweils in Sammel-Reihenfolge stabil.
        pool_sorted = sorted(pool, key=lambda t: (not t[0],))
        take = pool_sorted[: args.per_round]
        if len(take) < args.per_round:
            raise SystemExit(
                f"Nur {len(take)}/{args.per_round} Kandidaten fuer Runde {round_no} gefunden "
                f"(--max-games erhoehen oder --per-round senken)."
            )
        for has_pending, state_json, _orig_seed in take:
            probe_id += 1
            probe_seed = next_probe_seed
            next_probe_seed += 1
            resp = json.loads(
                mr.net_arena_choice_state_json(state_json, model_path, args.sims, args.c_puct, probe_seed, spec_path)
            )
            probes.append(
                {
                    "probe_id": probe_id,
                    "round": round_no,
                    "has_pending_dome_choice": has_pending,
                    "state": json.loads(state_json),
                    "seed": probe_seed,
                    "sims": args.sims,
                    "c_puct": args.c_puct,
                    "expected_action": resp["action"],
                }
            )
            print(
                f"Sonde {probe_id}: Runde {round_no} pending={has_pending} "
                f"seed={probe_seed} action={resp['action']}"
            )

    # Repo-relativ statt absolut (Codepflege-Audit Befund 25) -- reine
    # Provenienz-Felder, kein Leser loest darueber Pfade auf.
    from pathlib import Path as _P
    _repo = _P(__file__).resolve().parent.parent
    def _rel(x):
        try:
            return str(_P(x).resolve().relative_to(_repo)).replace("\\", "/")
        except (ValueError, OSError):
            return str(x)
    out = {
        "n_probes": len(probes),
        "artifact": _rel(artifact_dir),
        "model": _rel(model_path),
        "spec": _rel(spec_path),
        "generator": "tools/build_frozen_golden_probe.py",
        "protocol": "par.8d PER-ENTSCHEIDUNG (state_to_json_exact fuenftes Feld pending_dome_choice_exact, kein rot_seed mehr)",
        "probes": probes,
    }
    out_path = artifact_dir / "golden_probe.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    n_pending = sum(1 for p in probes if p["has_pending_dome_choice"])
    print(f"geschrieben: {out_path} ({len(probes)} Sonden, davon {n_pending} mit pending_dome_choice gesetzt)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
