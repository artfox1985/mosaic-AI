# -*- coding: utf-8 -*-
"""DAS TOR vor der Anker-Umstellung: spielt der Referee-Pfad dieselben Partien
wie der Pfad, auf dem die Elo-Leiter gemessen ist?

FRAGE: die Leiter haengt an Netz gegen Heuristik@150, gemessen ueber
`net_arena_match` (-> `play_net_game` -> `unified_game_loop`). Sollen die
Arenen den Anker kuenftig aus dem ARTEFAKT beziehen, laeuft die Partie ueber
`RefereeGame`. Verschiebt dieser Pfadwechsel den Anker, repariert man eine
Driftquelle und baut dabei eine neue ein.

WARUM DIE REFERENZ SORGFAELTIG GEWAEHLT SEIN MUSS -- der Fehler ist mir am
2026-08-26 zuerst selbst passiert: es gibt MEHRERE In-Process-Heuristikpfade.

  `play_arena_game`      Heuristik gegen Heuristik (arena_match,
                         heuristic_v1_vs_v2_arena)
  `unified_game_loop`    Netz gegen Heuristik -- HIER wird der Anker gemessen
  `RefereeGame`          der Referee-Pfad

Gegen `play_arena_game` gemessen war das Ergebnis 0/6 identisch, mit erster
Abweichung an der Kuppel-Slot-/Rotationswahl nach einem Stapelzug (also genau
dem mehrstufigen Zug, den das PER-ENTSCHEIDUNG-Protokoll aus par.8c/8d anders
zerlegt). Das ist ein echter Befund ueber diese beiden Pfade -- aber es ist
NICHT die Ankerfrage, denn der Anker laeuft nicht darueber.

VERGLICHEN WIRD PARTIE GEGEN PARTIE (Punkte UND Schrittzahl), nicht Mittelwert
gegen Mittelwert: zwei Spieler koennen im Mittel gleich abschneiden und
trotzdem andere Partien spielen. Fuer einen ANKER ist das nicht gut genug.

Die Seeds werden EXPLIZIT gesetzt (`net_arena_match(seeds=...)`), damit beide
Seiten dieselben Partien bekommen und nichts an einer Ableitungsformel haengt.

WAS EIN ROT BEDEUTET: nicht "der Referee ist kaputt", sondern "die
Anker-Umstellung verschiebt den Anker". Dann ist es ein Nutzer-Entscheid
(Anker bewusst neu setzen), keine Reparatur.

Aufruf:
    python -X utf8 -u tools/probes/anchor_referee_parity_probe.py --games 6
"""
import argparse
import json
import pathlib
import sys
import time

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "engine" / "py"))

import mosaic_rust as mr  # noqa: E402

# ACHTUNG, haeufige Fehllesart: von hier kommt nur die SPEC-DATEI, nicht das
# Wheel. Alle `mr.*`-Aufrufe laufen im AKTUELLEN Prozess, also auf dem
# aktuellen Wheel.
#
# Das ist fuer DIESE Frage richtig und keine Nachlaessigkeit: verglichen werden
# zwei PFADE (Referee gegen `net_arena_match`). Liefe eine Seite auf dem Wheel
# des Artefakts, koennte ein Unterschied vom WHEEL statt vom PFAD kommen, und
# das Ergebnis waere nicht mehr zuzuordnen.
#
# Die andere Frage -- spielt der aktuelle Stand noch wie das Artefakt? -- misst
# `tools/verify_frozen_heuristic.py` (Drift-Modus gegen die Golden Probe).
# Beide zusammen decken ab: Pfad hier, Wheel dort.
V1_SPEC = str(_ROOT / "models/frozen_heuristics/v1_anchor/spec.json")


def _spec_pruefen() -> None:
    """Die Spec-Datei ist der REFERENZPUNKT -- sie darf sich nicht still aendern.

    Die Sonde zeigt in ein Artefaktverzeichnis. Wuerde das Artefakt neu
    eingefroren und traege dabei eine andere Konfiguration, verschoebe sich der
    Vergleich lautlos. Deshalb hier eine Zusicherung statt einer Hoffnung.
    """
    spec = json.loads(pathlib.Path(V1_SPEC).read_text(encoding="utf-8"))
    if spec.get("heuristik_variante") != "v1":
        raise SystemExit(
            f"{V1_SPEC} sagt heuristik_variante={spec.get('heuristik_variante')!r}, "
            "erwartet wird 'v1'. Die Sonde vergleicht gegen den ANKER -- mit einer "
            "anderen Variante misst sie etwas anderes, als ihr Name behauptet.")


def referee_partie(model: str, spec_net: str | None, game_seed: int, first_player: int,
                   net_sims: int, heur_sims: int, c_puct: float, c: float,
                   heuristik_extern: bool) -> dict:
    """Netz auf Brett 0 (in-process), Heuristik auf Brett 1.

    `heuristik_extern` schaltet Platzierung und Startsetzung der Heuristik-Seite
    auf den EXTERNEN Weg -- so, wie ein gefrorenes Artefakt spielen wuerde.
    Beides wird gemessen, weil es zwei verschiedene Fragen sind.
    """
    rg = mr.RefereeGame(("Netz", "Heuristik"), first_player, game_seed, None)
    # DER SCHALTER, an dem die Wege auseinanderliefen: die Arena gibt der
    # NETZ-Seite `apply_via_chosen_action = true` (Sammelaufloesung des
    # Stapelzugs) und der HEURISTIK-Seite `false` (nur der Peek, die
    # Folgeschritte werden gesucht). Der Referee wandte bis 2026-08-26 immer
    # sammelaufloesend an und gab der Heuristik damit das Netz-Verhalten.
    rg.set_apply_modes((True, False))
    extern = [1] if heuristik_extern else []
    guard = 0
    while True:
        guard += 1
        if guard > 100_000:
            raise RuntimeError("Schrittlimit -- Haenger-Verdacht")
        st = rg.advance_to_decision(model, None, extern)
        if st == "game_over":
            rg.finalize_scoring()
            break
        if st == "stuck":
            raise RuntimeError(f"Deadlock bei steps={rg.steps()}, phase={rg.phase()}")
        if st == "start_placement":
            pi = rg.pending_start_placement_player()
            rg.start_placement_apply_external(
                mr.start_placement_choice_state_json(rg.state_json(), pi,
                                                     rg.game_seed(), V1_SPEC))
            continue
        if st == "tiling":
            rg.tiling_apply_external(
                mr.tiling_choice_state_json(rg.state_json(), V1_SPEC, None))
            continue
        if rg.current_player() == 0:
            rg.drafting_decide_and_apply_inprocess(model, spec_net, net_sims, c_puct)
        else:
            act = json.loads(mr.heuristic_arena_choice_state_json(
                rg.state_json(), heur_sims, c, rg.pending_search_seed(), V1_SPEC))["action"]
            rg.drafting_apply_external(json.dumps(act))
    return {"scores": list(rg.scores()), "steps": rg.steps()}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--games", type=int, default=6)
    ap.add_argument("--model", default="models/alphazero_v21_2d_brierbest.onnx")
    ap.add_argument("--spec-net", default="models/champion_frozen.spec.json")
    ap.add_argument("--net-sims", type=int, default=100)
    ap.add_argument("--heur-sims", type=int, default=150)
    ap.add_argument("--c-puct", dest="c_puct", type=float, default=1.5)
    ap.add_argument("--c", type=float, default=0.3)
    ap.add_argument("--seed-base", type=int, default=20260826)
    ap.add_argument("--out", default="evaluations/artifacts/anchor_referee_parity.json")
    a = ap.parse_args()

    _spec_pruefen()
    t0 = time.monotonic()
    seeds = [a.seed_base + i for i in range(a.games)]

    # --- Referenz: DER PFAD, AUF DEM DIE LEITER GEMESSEN IST
    roh = json.loads(mr.net_arena_match(
        a.model, a.net_sims, a.heur_sims, len(seeds), None, 1, a.c, a.c_puct,
        False, seeds, a.spec_net))
    print(f"Anker-Pfad (net_arena_match): {len(roh)} Partien", flush=True)

    befunde = {"extern": [], "inprocess": []}
    for modus in ("inprocess", "extern"):
        for i, (g, s) in enumerate(zip(roh, seeds)):
            r = referee_partie(a.model, a.spec_net, s, i % 2, a.net_sims, a.heur_sims,
                               a.c_puct, a.c, heuristik_extern=(modus == "extern"))
            gleich = (list(g["scores"]) == r["scores"]) and (int(g["steps"]) == r["steps"])
            befunde[modus].append({
                "partie": i, "seed": s, "identisch": gleich,
                "anker": {"scores": list(g["scores"]), "steps": int(g["steps"])},
                "referee": r,
            })
        n_gl = sum(1 for x in befunde[modus] if x["identisch"])
        print(f"  Referee, Heuristik {'EXTERN' if modus == 'extern' else 'in-process'}: "
              f"{n_gl}/{len(seeds)} identisch", flush=True)

    gleich_extern = sum(1 for x in befunde["extern"] if x["identisch"])
    verdikt = "GRUEN" if gleich_extern == len(seeds) else "ROT"
    erg = {
        "frage": ("Spielt der Referee-Pfad dieselben Partien wie net_arena_match "
                  "(der Pfad, auf dem die Elo-Leiter gemessen ist)?"),
        "referenz": "net_arena_match -> play_net_game -> unified_game_loop",
        "bedeutung_rot": ("Nicht 'der Referee ist kaputt', sondern 'die Anker-Umstellung "
                          "verschiebt den Anker'. Das ist ein Nutzer-Entscheid, keine "
                          "Reparatur."),
        "partien": len(seeds), "net_sims": a.net_sims, "heur_sims": a.heur_sims,
        "seeds": seeds, "verdikt": verdikt,
        "identisch": {"extern": gleich_extern,
                      "inprocess": sum(1 for x in befunde["inprocess"] if x["identisch"])},
        "befunde": befunde,
        "laufzeit": {"wanduhr_s": round(time.monotonic() - t0, 1), "cpu_s": None,
                     "threads": 1,
                     "s_je_partie": round((time.monotonic() - t0) / max(1, 2 * len(seeds)), 2)},
    }
    ziel = pathlib.Path(a.out)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(json.dumps(erg, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    print(f"\n{verdikt}\nArtefakt: {ziel}")
    if verdikt == "ROT":
        for d in befunde["extern"][:3]:
            if not d["identisch"]:
                print(f"  Partie {d['partie']} (seed {d['seed']}): Anker {d['anker']} "
                      f"gegen Referee {d['referee']}", file=sys.stderr)
    return 0 if verdikt == "GRUEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
