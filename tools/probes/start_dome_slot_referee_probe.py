# -*- coding: utf-8 -*-
"""Gegenprobe zum Zirkularitaets-Waechter der Startkuppel-Sonde: dieselben neun
Slots, aber mit dem eingefrorenen hv2-Artefakt als gemessener Seite
(`evaluations/PREREG_start_dome_choice.md` par.4/par.8, Nutzer-Entscheid
2026-09-12 "Weg 3").

WOZU
----
Die Hauptmessung (`tools/probes/start_dome_slot_probe.py`) faehrt den Waechter
ueber zwei FAEHIGKEITSSTUFEN derselben Variante (hv1@25 gegen hv1@400), weil
hv2 auf dem lebenden Wheel nicht spielbar ist. Das ist eine Abweichung von
par.4, der zwei VERSCHIEDENE Spieler verlangt. Diese Sonde liefert den
fehlenden zweiten Spieler: hv2 lebt als eingefrorenes Artefakt
(`models/frozen_heuristics/hv2_generator/`, eigenes Wheel, Protokoll
drafting/tiling/start_placement) und spielt hier ueber den Referee-Pfad gegen
die lebende hv1-Heuristik.

Der Waechter dieser Sonde ist die Spearman-Rangkorrelation der Slot-Margins
zwischen dieser hv2-Messung und der hv1@400-Reihe der Hauptmessung. Kippt die
Rangfolge (rho < 0), ist "guter Start" eine Eigenschaft des Spielers und nicht
der Position.

AUFBAU, und was daran erzwungen ist
-----------------------------------
Je Slot EIN Referee-Lauf (`tools/frozen_referee_match.py`), Artefakt-Seite =
hv2 mit erzwungenem Startslot (`--force-start-slot-artifact`), Gegenseite =
lebende hv1, netzlos (`--heuristic-a`). Dieselben Partie-Seeds in allen neun
Slots (`--seed-base` + i), also gepaart: Bezugsgroesse ist die Differenz zu
Slot 0, Partie fuer Partie.

BENANNTER KONFUND (aus dem Code, nicht vermutet): das Wheel des Artefakts
kennt `MOSAIC_START_SLOT_P0/P1` nicht, deshalb rechnet die Startsetzung der
hv2-Seite fuer diese eine Anfrage das LEBENDE Wheel
(`start_placement_choice_state_json`). Dort ignoriert
`choose_start_placement_json` die Spec (`let _ = (search_config, game_seed);`,
engine/src/referee.rs:121) und ruft die hv1-Handregel. hv2 setzt seine
Startkuppel unter dieser Sonde also nach hv1-Handregel IM ERZWUNGENEN SLOT;
alles danach (Drafting, Tiling, Startsetzung-Rest) ist hv2 aus seinem eigenen
Wheel. Gemessen wird "hv2 spielt eine Partie, die in Slot N beginnt", nicht
"hv2 waehlt Slot N". Fuer die Waechter-Frage (kippt die Rangfolge der
Positionen, wenn der Spieler wechselt?) ist genau das die richtige Anlage.

Cross-Aera: das Artefakt traegt `contract_hash` a3f61f246d9bbf5c, das lebende
Wheel 39648b95bbba1acf. Der Referee verweigert den Lauf ohne
`--force-cross-era`; die Sonde setzt das Flag und schreibt es ins Artefakt.

Aufruf (Maschine muss frei sein, CLAUDE.md "Messungen laufen EXKLUSIV"):
    python -X utf8 -u tools/probes/start_dome_slot_referee_probe.py

Rauchtest (2 Partien je Slot, 2 Worker):
    python -X utf8 -u tools/probes/start_dome_slot_referee_probe.py \
        --n-games 2 --workers 2 \
        --out evaluations/artifacts/start_dome_slot_referee_probe_smoke.json
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "probes"))

# Wiederverwendet statt nachgebaut (CLAUDE.md "Schau in vorhandene scripts"):
# die Rekonstruktions- und Statistik-Helfer der Hauptmessung und der
# Struktur-Sonde. Nur die SEITE ist hier eine andere.
from column_build_structural_probe import (  # noqa: E402
    column_fill,
    final_scoring_criteria_per_player,
    reconstruct_game,
    struktur_kennzahlen,
)
from penalty_track_probe import penalties_from_log  # noqa: E402
from start_dome_slot_probe import METRICS, mean_ci, row_fill, spearman  # noqa: E402

SLOTS = list(range(9))
OUT_DEFAULT = ROOT / "evaluations" / "artifacts" / "start_dome_slot_referee_probe.json"
RUNS_DEFAULT = ROOT / "evaluations" / "artifacts" / "start_dome_slot_referee_runs"
MAIN_DEFAULT = ROOT / "evaluations" / "artifacts" / "start_dome_slot_probe.json"
ARTIFACT_DEFAULT = ROOT / "models" / "frozen_heuristics" / "hv2_generator"
REFEREE = ROOT / "tools" / "frozen_referee_match.py"


def run_referee(slot: int, args, out_path: Path) -> dict:
    """Ein Referee-Lauf fuer EINEN Slot; gibt das gelesene Ergebnis-JSON.

    SUBPROZESS, nicht Import: `frozen_referee_match.main()` waere zwar
    importierbar (das Modul hat ausser Importen und der Konstante `REPO`
    keinen Seiteneffekt, der Einstieg steht hinter `if __name__ ...`), aber
    es parst `sys.argv`, beendet per `SystemExit` und startet bei
    `--workers > 1` einen `mp.Pool`, dessen Kinder unter spawn das `__main__`
    des Elternprozesses neu importieren -- das waere dann DIESE Sonde. Der
    Subprozess haelt die Grenze sauber und liefert einen echten Exit-Code.

    KEINE Pipe und KEINE Umleitung (CLAUDE.md "Lange Laeufe NIE in eine
    Pipe"): stdout/stderr des Referees erben die Kanaele dieser Sonde, seine
    Fortschrittszeilen je Partie bleiben also sichtbar. Das Ergebnis kommt
    ueber die `--out`-Datei zurueck, nicht ueber die Ausgabe.
    """
    cmd = [
        sys.executable, "-X", "utf8", "-u", str(REFEREE),
        "--artifact-dir", str(args.artifact_dir),
        "--heuristic-a",
        "--force-cross-era",
        "--force-start-slot-artifact", str(slot),
        "--sims-a", str(args.sims_a),
        "--sims-worker", str(args.sims_worker),
        "--c-puct-a", str(args.c_puct),
        "--c-puct-worker", str(args.c_puct),
        "--n-games", str(args.n_games),
        "--seed-base", str(args.seed_base),
        "--workers", str(args.workers),
        "--out", str(out_path),
    ]
    if args.skip_golden:
        cmd.append("--skip-golden")
    proc = subprocess.run(cmd, cwd=str(ROOT))
    if proc.returncode != 0:
        raise SystemExit(
            f"[slot {slot}] Referee-Lauf beendet mit Exit-Code {proc.returncode}. "
            "Kein Teilergebnis -- die Sonde bricht ab, statt einen Slot fehlen zu lassen.")
    return json.loads(out_path.read_text(encoding="utf-8"))


def game_metrics(game: dict, name: str, board: int) -> dict | None:
    """Kennzahlen EINER Partie aus Sicht der Artefakt-Seite.

    Gegenstueck zu `start_dome_slot_probe.game_metrics`, mit zwei
    Unterschieden, die aus dem Record-Format des Referees folgen: die Seite
    steht nicht fest auf Brett 0 (`board_a` alterniert), und es gibt kein
    `total_floor` -- die Strafpunkte kommen deshalb aus den
    ROUND_STRAFE-Zeilen (`penalty_track_probe.penalties_from_log`, dieselbe
    Summe wie in jeder anderen Strafleisten-Auswertung).
    """
    log = game.get("log") or []
    cells = reconstruct_game(log)
    own = cells.get(name)
    if not own:
        return None
    cfill = column_fill(own)
    rfill = row_fill(own)
    scores = game["scores"]
    penalties = penalties_from_log(log)
    out = {
        "punkte": float(scores[board]),
        "margin": float(scores[board] - scores[1 - board]),
        "gegner_punkte": float(scores[1 - board]),
        "strafpunkte": float(penalties[name]["strafpunkte"]),
        "volle_reihen": float(sum(1 for f in rfill if f == 6)),
        "max_reihenhoehe": float(max(rfill)),
        "gefuellte_zellen": float(len(own)),
    }
    kz = struktur_kennzahlen(cfill)
    out["volle_spalten"] = float(kz["volle_spalten"])
    out["max_spaltenhoehe"] = float(kz["max_hoehe"])
    out["teilspalten_ge3"] = float(kz["teilspalten_ge3"])
    out["teilspalten_ge4"] = float(kz["teilspalten_ge4"])
    out["_spaltenfuellstand"] = cfill
    out["_reihenfuellstand"] = rfill
    out["_plattenpunkte"] = final_scoring_criteria_per_player(log).get(name, {})
    out["_seed"] = game.get("seed")
    out["_start_slot"] = game.get("start_slot_artifact")
    return out


def main_reference(path: Path, pairing: str) -> dict:
    """Slot-Margins der HAUPTMESSUNG, oder ein Block, der sagt warum nicht.

    Struktur laut Erzeuger (`start_dome_slot_probe.main`):
    `paarungen[<paarung>]["je_slot"][<slot>]["kennzahlen"]["margin"]["mittel"]`.
    """
    if not path.exists():
        return {"verfuegbar": False, "grund": f"Hauptmessung fehlt: {path.as_posix()}"}
    doc = json.loads(path.read_text(encoding="utf-8"))
    block = (doc.get("paarungen") or {}).get(pairing)
    if block is None:
        return {"verfuegbar": False,
                "grund": f"Paarung {pairing!r} fehlt in {path.name} "
                         f"(vorhanden: {sorted((doc.get('paarungen') or {}).keys())})"}
    margins = []
    for slot in SLOTS:
        entry = (block.get("je_slot") or {}).get(str(slot))
        value = None if entry is None else entry["kennzahlen"]["margin"]["mittel"]
        margins.append(value)
    if any(v is None for v in margins):
        return {"verfuegbar": False,
                "grund": f"Paarung {pairing!r} hat nicht fuer alle neun Slots ein Margin-Mittel"}
    return {"verfuegbar": True, "paarung": pairing, "quelle": path.name, "margins": margins}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--artifact-dir", default=str(ARTIFACT_DEFAULT),
                    help="gefrorenes Heuristik-Artefakt der gemessenen Seite")
    ap.add_argument("--n-games", type=int, default=20, help="Partien je Slot")
    ap.add_argument("--seed-base", type=int, default=20260913,
                    help="Partie i spielt seed_base + i -- in allen neun Slots dieselbe Folge")
    ap.add_argument("--workers", type=int, default=6,
                    help="gleichzeitige Referee-Prozesse JE SLOT (die Slots laufen "
                         "nacheinander, nicht parallel)")
    # 150 Sims: hv2@150 ist die Anfaenger-Stufe der Schwierigkeitsleiter
    # (PREREG_difficulty_levels.md). UNGEPRUEFT, ob 150 fuer diese Frage die
    # richtige Stufe ist -- die Hauptmessung faehrt 25 und 400, und ob der
    # Waechter bei 150 oder bei 400 schaerfer ist, ist nicht gemessen.
    ap.add_argument("--sims-worker", type=int, default=150, help="Sims der hv2-Artefakt-Seite")
    ap.add_argument("--sims-a", type=int, default=150, help="Sims der lebenden hv1-Seite")
    # 0.3 statt der Referee-Voreinstellung 1.5: beide Seiten sind hier eine
    # HEURISTIK-Suche, und deren Konstante ist im Projekt 0.3
    # (`arena_match`-Signatur c=0.3, engine/src/lib.rs:180; derselbe Wert geht
    # in tools/anchor_arena.py:119 an den gefrorenen Heuristik-Worker).
    ap.add_argument("--c-puct", type=float, default=0.3,
                    help="UCT-Konstante beider Heuristik-Seiten")
    ap.add_argument("--slots", default=",".join(str(s) for s in SLOTS),
                    help="Slots, die gefahren werden (kommagetrennt). Der Waechter braucht alle neun.")
    ap.add_argument("--skip-golden", action="store_true",
                    help="NUR fuer Debug -- die Abnahme braucht den Golden-Selbsttest des Artefakts")
    ap.add_argument("--main-artifact", default=str(MAIN_DEFAULT),
                    help="Artefakt der Hauptmessung fuer den Waechter-Vergleich")
    ap.add_argument("--main-pairing", default="hv1@400_vs_hv1@400",
                    help="Paarung in der Hauptmessung, gegen die verglichen wird")
    ap.add_argument("--runs-dir", default=str(RUNS_DEFAULT),
                    help="Ablage der neun Referee-Ergebnis-JSONs")
    ap.add_argument("--out", default=str(OUT_DEFAULT))
    a = ap.parse_args()

    slots = [int(x) for x in a.slots.split(",") if x.strip()]
    if not slots:
        raise SystemExit("--slots braucht mindestens einen Slot")
    runs_dir = Path(a.runs_dir)
    runs_dir.mkdir(parents=True, exist_ok=True)

    t0, cpu0 = time.monotonic(), time.process_time()
    games_total = 0
    missing_logs = 0
    per_slot: dict[str, dict] = {}
    raw_values: dict[int, dict[str, list[float]]] = {}
    seeds_per_slot: dict[int, list[int]] = {}
    artifact_name = None
    handshake = None

    for slot in slots:
        t_slot = time.monotonic()
        print(f"[slot {slot}] Referee-Lauf: {a.n_games} Partien, hv2@{a.sims_worker} "
              f"gegen hv1@{a.sims_a}, workers={a.workers}", flush=True)
        result = run_referee(slot, a, runs_dir / f"slot_{slot}.json")
        handshake = result.get("handshake")
        # Name der Artefakt-Seite im Log: der Referee schreibt ihn seit dem
        # Zusatz von 2026-09-12 ausdruecklich mit; der Rueckfall deckt aeltere
        # Ergebnis-Dateien ab (gleiche Herleitung wie im Referee selbst).
        artifact_name = ((result.get("namen") or {}).get("artefakt")
                         or result.get("artefakt") or result.get("champion") or "ArtefaktB")
        if result.get("force_start_slot_artifact") != slot:
            raise SystemExit(
                f"[slot {slot}] Ergebnis-JSON meldet force_start_slot_artifact="
                f"{result.get('force_start_slot_artifact')!r} -- der Lauf hat nicht das "
                "gemessen, was hier registriert wuerde.")

        values: dict[str, list[float]] = defaultdict(list)
        criteria = Counter()
        rsum = [0.0] * 6
        csum = [0.0] * 6
        n_ok = 0
        slot_hits = 0
        slot_misses: Counter = Counter()
        seeds: list[int] = []
        for g in result["games"]:
            board = g.get("board_artifact")
            if board is None:
                board = 1 - g["board_a"]
            m = game_metrics(g, artifact_name, board)
            if m is None:
                missing_logs += 1
                continue
            n_ok += 1
            seeds.append(m["_seed"])
            if m["_start_slot"] == slot:
                slot_hits += 1
            else:
                slot_misses[str(m["_start_slot"])] += 1
            for key in METRICS:
                values[key].append(m[key])
            for k, v in m["_plattenpunkte"].items():
                criteria[k] += v
            for i in range(6):
                rsum[i] += m["_reihenfuellstand"][i]
                csum[i] += m["_spaltenfuellstand"][i]
        games_total += len(result["games"])
        raw_values[slot] = dict(values)
        seeds_per_slot[slot] = seeds
        divisor = max(1, n_ok)
        per_slot[str(slot)] = {
            "slot_index": slot,
            "slot_rc": [slot // 3, slot % 3],
            "n": n_ok,
            "kennzahlen": {k: mean_ci(values[k]) for k in METRICS},
            "reihenauslastung_mittel": [round(x / divisor, 3) for x in rsum],
            "spaltenauslastung_mittel": [round(x / divisor, 3) for x in csum],
            "plattenpunkte_je_kriterium": {k: round(v / divisor, 3)
                                           for k, v in sorted(criteria.items())},
            # Kontrolle: wurde der erzwungene Slot wirklich gelegt? Ein
            # belegter Slot faellt in der Engine auf die Bestandswahl zurueck.
            "slot_kontrolle": {
                "erzwungen": slot,
                "treffer": slot_hits,
                "abweichungen": n_ok - slot_hits,
                "abweichungen_nach_slot": dict(slot_misses),
            },
            "referee_lauf": {
                "datei": (runs_dir / f"slot_{slot}.json").relative_to(ROOT).as_posix(),
                "elapsed_s": result.get("elapsed_s"),
                "wins_a": result.get("wins_a"),
                "wins_b": result.get("wins_b"),
            },
        }
        if n_ok - slot_hits:
            print(f"  [slot {slot}] WARNUNG: {n_ok - slot_hits} von {n_ok} Partien liegen NICHT "
                  f"im erzwungenen Slot ({dict(slot_misses)})", flush=True)
        print(f"  [slot {slot}] n={n_ok}  points_mean="
              f"{per_slot[str(slot)]['kennzahlen']['punkte']['mittel']}  margin="
              f"{per_slot[str(slot)]['kennzahlen']['margin']['mittel']}  "
              f"({time.monotonic() - t_slot:.1f} s)", flush=True)

    # Gepaarte Differenz zu Slot 0, Partie fuer Partie. Gepaart wird ueber den
    # SEED, nicht ueber die Listenposition: eine Partie ohne rekonstruierbares
    # Log verschiebt sonst alle folgenden gegeneinander.
    paired: dict[str, dict] = {}
    base_slot = slots[0]
    if base_slot in raw_values:
        base_index = {seed: i for i, seed in enumerate(seeds_per_slot[base_slot])}
        for slot in slots[1:]:
            pairs = [(base_index[s], i) for i, s in enumerate(seeds_per_slot[slot])
                     if s in base_index]
            diffs = {}
            for key in METRICS:
                base_values = raw_values[base_slot].get(key, [])
                arm_values = raw_values[slot].get(key, [])
                diffs[key] = mean_ci([arm_values[j] - base_values[i] for i, j in pairs])
            diffs["_n_paare"] = len(pairs)
            paired[str(slot)] = diffs

    def mean_of(slot: int, key: str) -> float:
        value = per_slot[str(slot)]["kennzahlen"][key]["mittel"]
        return float("-inf") if value is None else value

    spread = {}
    for key in METRICS:
        means = [per_slot[str(s)]["kennzahlen"][key]["mittel"] for s in slots]
        means = [m for m in means if m is not None]
        if not means:
            continue
        spread[key] = {
            "min": round(min(means), 4),
            "max": round(max(means), 4),
            "spanne": round(max(means) - min(means), 4),
            "bester_slot": max(slots, key=lambda s, k=key: mean_of(s, k)),
            "schlechtester_slot": min(slots, key=lambda s, k=key: mean_of(s, k)),
        }

    ranking_margin = sorted(slots, key=lambda s: mean_of(s, "margin"), reverse=True)
    ranking_points = sorted(slots, key=lambda s: mean_of(s, "punkte"), reverse=True)

    reference = main_reference(Path(a.main_artifact), a.main_pairing)
    guard = {
        "weg": "3 (Sims-Stufen als Hauptmessung, hv2-Artefakt per Referee als Gegenprobe)",
        "frage": "Kippt die Rangfolge der Startslots, wenn der SPIELER wechselt? (par.4)",
        "vergleich": f"hv2@{a.sims_worker} (diese Sonde) gegen {a.main_pairing} (Hauptmessung)",
        "referenz": reference,
        "konfund": (
            "Die Startsetzung der hv2-Seite rechnet das LEBENDE Wheel "
            "(start_placement_choice_state_json), weil das Artefakt-Wheel den Knopf nicht "
            "kennt; choose_start_placement_json ignoriert dort die Spec (referee.rs:121) und "
            "benutzt die hv1-Handregel. Platte und Rotation im erzwungenen Slot sind damit "
            "hv1, alles danach ist hv2."
        ),
    }
    if reference["verfuegbar"] and len(slots) == len(SLOTS):
        own = [mean_of(s, "margin") for s in slots]
        rho = spearman(own, reference["margins"])
        guard["spearman_margin"] = rho
        guard["bester_slot"] = {
            f"hv2@{a.sims_worker}": ranking_margin[0],
            a.main_pairing: max(SLOTS, key=lambda s: reference["margins"][s]),
        }
        guard["kippt"] = (rho is not None and rho < 0.0)
    else:
        guard["spearman_margin"] = None
        guard["kippt"] = None
        guard["hinweis"] = (
            "Waechter NICHT erhoben: " + (reference.get("grund") or "")
            if not reference["verfuegbar"]
            else "Waechter NICHT erhoben: es wurden nicht alle neun Slots gefahren")

    wall = time.monotonic() - t0
    out = {
        "frage": "Kippt die Slot-Rangfolge zwischen hv1 und dem eingefrorenen hv2? "
                 "(PREREG_start_dome_choice.md par.4, Gegenprobe zum Zirkularitaets-Waechter)",
        "aufbau": {
            "gemessene_seite": f"hv2-Artefakt ({Path(a.artifact_dir).name}), eigenes Wheel, "
                               f"{a.sims_worker} Sims",
            "gegenseite": f"lebende hv1-Heuristik, netzlos, {a.sims_a} Sims (--heuristic-a)",
            "einstieg": "tools/frozen_referee_match.py (Subprozess je Slot)",
            "knopf": "MOSAIC_START_SLOT_P{pi der Artefakt-Seite}, gesetzt nur fuer die "
                     "einzelne Startsetzungs-Anfrage auf dem lebenden Wheel",
            "cross_aera": True,
            "handshake": handshake,
            "seed_base": a.seed_base,
            "seed_ableitung": "seed_base + i (frozen_referee_match: seeds ab --seed-base)",
            "gepaart": "Partie i ist in allen gefahrenen Slots dieselbe Ausgangslage; "
                       "gepaarte Differenz gegen den ersten Slot ueber den Seed",
            "c_puct": a.c_puct,
            "brettwechsel": "board_a = i % 2, die Artefakt-Seite sitzt auf 1 - board_a",
        },
        "grundmenge": {
            "n_je_slot": a.n_games,
            "grundmenge": "Partien eines Slots, Sicht der hv2-Artefakt-Seite",
            "einheit": "je Partie",
            "partien_gesamt": games_total,
            "partien_ohne_rekonstruierbares_log": missing_logs,
            "slots": slots,
        },
        "waechter": guard,
        "je_slot": per_slot,
        "gepaart_gegen_slot0": paired,
        "spannweite_ueber_slots": spread,
        "rangfolge_nach_margin": ranking_margin,
        "rangfolge_nach_punkten": ranking_points,
        "laufzeit": {
            "wanduhr_s": round(wall, 1),
            "cpu_s": round(time.process_time() - cpu0, 1),
            "threads": a.workers,
            "s_je_partie": round(wall / max(1, games_total), 3),
            "hinweis": (
                "cpu_s zaehlt NUR diesen Treiberprozess. Die Rechenzeit steckt in den "
                "Referee- und Worker-Kindprozessen; os.times() meldet deren CPU unter "
                "Windows nicht. Vergleichbar ist wanduhr_s zusammen mit threads "
                "(= Referee-Prozesse je Slot)."
            ),
        },
        "cli_args": vars(a),
    }

    target = Path(a.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    print(f"\n[fertig] {games_total} Partien in {wall:.1f} s -> {target}", flush=True)
    if "margin" in spread:
        print(f"  Spanne margin {spread['margin']['spanne']} "
              f"(bester Slot {spread['margin']['bester_slot']}, "
              f"schlechtester {spread['margin']['schlechtester_slot']})", flush=True)
    print(f"  Waechter: spearman(margin) = {guard.get('spearman_margin')}, "
          f"kippt = {guard.get('kippt')}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
