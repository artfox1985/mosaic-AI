# -*- coding: utf-8 -*-
"""Stufe 0, Teil 2 der Startkuppel-Frage: taugt die Handregel bei PLATTE und
ROTATION? (`evaluations/PREREG_start_dome_choice.md` par.9a Punkt 1)

Stufe 0 (par.9) hat den SLOT geschlossen: die Handregel legt immer (0,0), und
das ist fuer Heuristiken der beste Slot. Offen blieb der Rest desselben Zugs --
die bis zu ZWOELF Kandidaten in diesem Slot (3 Platten der Auslage x 4
Rotationen), unter denen die Handregel nach Farbzaehlern der Sonnenfelder
waehlt (`self_play.rs::start_placement_kandidaten`, Spezialfelder mit 0,0
bewertet).

NETZFREI, GEPAART, HEURISTIK AUF BEIDEN SEITEN. Dieselbe Partie wird zweimal
gespielt -- identischer Seed, also identische Fabriken, Beutel, Kuppelstapel
und Wertungsplatten -- und unterscheidet sich NUR darin, ob Spieler 0 seine
Startkuppel nach der Handregel oder gleichverteilt aus den Kandidaten desselben
Slots waehlt (`MOSAIC_START_TILE_RANDOM_P0`, Diagnoseknopf,
`self_play.rs::sample_random_start_tile`). Spieler 1 bleibt im Bestand:
`MOSAIC_START_TILE_RANDOM_P1` wird von dieser Sonde nie gesetzt.

VORAB-LESART (vor dem Lauf festgelegt, par.9a Punkt 1)
-----------------------------------------------------
Zielgroesse ist die gepaarte Differenz **Handregel minus Zufall** in Marge und
Punkten, je Paarung.

* **Differenz klein** (das 95-%-Intervall schliesst 0 ein) => auch Platte und
  Rotation sind KEIN Hebel. Der ganze Startzug -- Slot wie Platte wie Rotation
  -- ist dann als Handregel so gut wie irgendetwas anderes, und der Such-Start
  (par.9c) hat an dieser Stelle nichts zu holen. Vollwertiges Ergebnis.
* **Differenz gross** => die Handregel TRAEGT. Dann ist sie die Messlatte: der
  Such-Start muss mindestens diesen Abstand zum Zufall erreichen, sonst ist er
  an dieser Stelle eine Verschlechterung, auch wenn die Arena flach aussieht.

KONTROLLEN (ohne sie ist die Messung nicht lesbar)
--------------------------------------------------
1. **Gelegter Slot** aus der START_TILE-Logzeile: er muss in BEIDEN Armen
  (0,0) bleiben. Der Knopf streut ausdruecklich nur innerhalb des Slots, den
  die Handregel gewaehlt haette; eine Abweichung hiesse, dass etwas anderes den
  Slot bewegt, und der Arm maesse dann nicht, was auf dem Etikett steht.
2. **Verteilung von Platte und Rotation** im Zufallsarm, ebenfalls aus der
  START_TILE-Zeile (`tile` und `rot`). Entartet sie (nur eine Rotation, nur
  eine Platte), hat der Zufallsarm den Bestand unter falschem Etikett gespielt.
  Der Handregel-Arm wird mitgezaehlt, weil seine Verteilung die zweite Haelfte
  der Aussage ist: sie zeigt, WIE einseitig die Handregel waehlt.

WELCHER PARTIE-EINSTIEG und warum
---------------------------------
`mosaic_rust.arena_match(sims_a, sims_b, n_games, seed, num_threads, c,
log_games)` -- dieselbe Begruendung wie in `start_dome_slot_probe.py`:
Heuristik-MCTS gegen Heuristik-MCTS, komplett in Rust, kein Netz, keine Records
auf der Platte. Partie `i` bekommt den abgeleiteten Seed
`seed + i * 0x9E3779B97F4A7C15` (`self_play.rs::run_arena_match`), unabhaengig
vom Arm -- Partie `i` im Handregel-Arm und Partie `i` im Zufallsarm sind
dieselbe Ausgangslage. Brett 0 ist Agent A, also die gestreute Seite; der
Startspieler alterniert mit `i % 2` und ist in beiden Armen derselbe.

DER ZUFALL VERSCHIEBT DIE PARTIE NICHT
--------------------------------------
Im Arena-Pfad zieht die Streuung aus einem EIGENEN, aus `game_seed`
abgeleiteten Strom (`self_play.rs::play_arena_game`, Muster
`PREREG_search_rng_split.md`), nicht aus dem Partie-RNG. Der Zufallsstrom der
Nachziehplatten bleibt damit Zug fuer Zug derselbe wie im Handregel-Arm --
trifft die Ziehung zufaellig die Wahl der Handregel, ist die Partie identisch.
Ohne diese Trennung waere der "gepaarte" Vergleich an der Wurzel entpaart.

Aufruf (die Maschine muss frei sein, CLAUDE.md "Messungen laufen EXKLUSIV"):
    python -X utf8 -u tools/probes/start_dome_tile_probe.py

Rauchtest (wenige Partien, kurze Suche):
    python -X utf8 -u tools/probes/start_dome_tile_probe.py --limit 4 \
        --pairings 25 --threads 4
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "probes"))

import mosaic_rust as mr  # noqa: E402

# Wiederverwendet statt nachgebaut (CLAUDE.md "Schau in vorhandene scripts"):
# die Stufe-0-Sonde hat Kennzahlen, KI und Slot-Kontrolle schon gebaut, und
# beide Sonden muessen dieselben Groessen meinen.
from start_dome_slot_probe import (  # noqa: E402
    METRICS,
    game_metrics,
    mean_ci,
    realised_start_slot,
)
from analyze_game_log import PATTERNS, ROUND_PREFIX  # noqa: E402

OUT_DEFAULT = ROOT / "evaluations" / "artifacts" / "start_dome_tile_probe.json"

# Brett 0 = Agent A = die gestreute Seite (run_arena_match vergibt die Namen
# "A"/"B" in Brettreihenfolge).
NAME_SELF, NAME_OPP = "A", "B"
KNOB_SELF = "MOSAIC_START_TILE_RANDOM_P0"
KNOB_OPP = "MOSAIC_START_TILE_RANDOM_P1"
SLOT_KNOB_SELF = "MOSAIC_START_SLOT_P0"
SLOT_KNOB_OPP = "MOSAIC_START_SLOT_P1"

ARM_HAND = "handregel"
ARM_RANDOM = "zufall"
ARMS = [ARM_HAND, ARM_RANDOM]


def realised_start_tile(log: list[str], name: str) -> tuple[int, int] | None:
    """`(tile_id, rotation)` der Startkuppel von Spieler `name` aus der
    START_TILE-Logzeile; `None`, wenn keine gefunden.

    Gegenstueck zu `realised_start_slot` (dort der Slot): zusammen sind die
    beiden die vollstaendige Kontrolle ueber das, was der Knopf tun soll --
    Slot fest, Platte und Rotation gestreut.
    """
    for raw_line in log or []:
        if raw_line.startswith("#"):
            continue
        m = ROUND_PREFIX.match(raw_line)
        text = m.group(2) if m else raw_line
        mm = PATTERNS["START_TILE"].match(text)
        if mm and mm.group("name") == name:
            return int(mm.group("tile")), int(mm.group("rot"))
    return None


def run_arm(arm: str, sims: int, n_games: int, seed_base: int, threads: int,
            c: float, slot: int | None) -> list[dict]:
    """Eine Arena ueber `n_games` Partien in einem Arm.

    Die Knoepfe werden HIER gesetzt, also zwischen zwei Arena-Aufrufen und
    damit zu einem Zeitpunkt, an dem keine Rust-Partie laeuft (nebenlaeufiges
    Schreiben der Prozessumgebung waere sonst der Fehler). Gelesen werden sie
    in der Engine je Startsetzung, kein `OnceLock`.
    """
    if arm == ARM_RANDOM:
        os.environ[KNOB_SELF] = "1"
    else:
        os.environ.pop(KNOB_SELF, None)
    os.environ.pop(KNOB_OPP, None)  # Gegenseite bleibt ausdruecklich im Bestand
    if slot is None:
        os.environ.pop(SLOT_KNOB_SELF, None)
    else:
        os.environ[SLOT_KNOB_SELF] = str(slot)
    os.environ.pop(SLOT_KNOB_OPP, None)
    raw = mr.arena_match(sims, sims, n_games, seed=seed_base, num_threads=threads,
                         c=c, log_games=True)
    return json.loads(raw)


def collect_arm(games: list[dict], erwarteter_slot: int) -> dict:
    """Kennzahlen, Kontrollen und Rohwerte EINES Arms.

    Rohwerte (`_werte`, `_kriterien`) bleiben in Partienreihenfolge stehen --
    die gepaarte Differenz unten braucht sie Partie fuer Partie.
    """
    values: dict[str, list[float]] = defaultdict(list)
    kriterien: list[dict] = []
    krit_summe: Counter = Counter()
    rsum = [0.0] * 6
    csum = [0.0] * 6
    n_ok = 0
    fehlende_logs = 0
    slot_hits = 0
    slot_misses: Counter = Counter()
    platten: Counter = Counter()
    rotationen: Counter = Counter()
    paare: Counter = Counter()

    for g in games:
        m = game_metrics(g)
        if m is None:
            fehlende_logs += 1
            continue
        n_ok += 1
        for key in METRICS:
            values[key].append(m[key])
        kriterien.append(dict(m["_plattenpunkte"]))
        for k, v in m["_plattenpunkte"].items():
            krit_summe[k] += v
        for i in range(6):
            rsum[i] += m["_reihenfuellstand"][i]
            csum[i] += m["_spaltenfuellstand"][i]
        if m["_start_slot"] == erwarteter_slot:
            slot_hits += 1
        else:
            slot_misses[str(m["_start_slot"])] += 1
        tile_rot = realised_start_tile(g.get("log") or [], NAME_SELF)
        if tile_rot is not None:
            platten[str(tile_rot[0])] += 1
            rotationen[str(tile_rot[1])] += 1
            paare[f"{tile_rot[0]}@{tile_rot[1]}"] += 1

    teiler = max(1, n_ok)
    return {
        "n": n_ok,
        "partien_ohne_rekonstruierbares_log": fehlende_logs,
        "kennzahlen": {k: mean_ci(values[k]) for k in METRICS},
        "reihenauslastung_mittel": [round(x / teiler, 3) for x in rsum],
        "spaltenauslastung_mittel": [round(x / teiler, 3) for x in csum],
        "plattenpunkte_je_kriterium": {
            k: round(v / teiler, 3) for k, v in sorted(krit_summe.items())
        },
        # Kontrolle 1: der Slot darf sich nicht bewegen.
        "slot_kontrolle": {
            "erwartet": erwarteter_slot,
            "treffer": slot_hits,
            "abweichungen": n_ok - slot_hits,
            "abweichungen_nach_slot": dict(slot_misses),
        },
        # Kontrolle 2: waehlt der Arm ueberhaupt verschiedene Platten und
        # Rotationen? (Im Handregel-Arm ist eine schmale Verteilung das
        # ERWARTETE Bild, im Zufallsarm waere sie ein Befund.)
        "start_tile_verteilung": {
            "platten": dict(sorted(platten.items())),
            "rotationen": dict(sorted(rotationen.items())),
            "platte_rotation": dict(sorted(paare.items())),
            "verschiedene_kandidaten": len(paare),
        },
        "_werte": {k: values[k] for k in METRICS},
        "_kriterien": kriterien,
    }


def paired_diff(a: dict, b: dict) -> dict:
    """Gepaarte Differenz `a` minus `b`, Partie fuer Partie, je Kennzahl und
    je Wertungskriterium. Kuerzere Liste gewinnt (ein fehlendes Log auf einer
    Seite darf die Paarung nicht verschieben -- es verkuerzt sie).
    """
    out: dict[str, dict] = {}
    for key in METRICS:
        va, vb = a["_werte"].get(key, []), b["_werte"].get(key, [])
        k = min(len(va), len(vb))
        out[key] = mean_ci([va[i] - vb[i] for i in range(k)])
    krit: dict[str, dict] = {}
    ka, kb = a["_kriterien"], b["_kriterien"]
    k = min(len(ka), len(kb))
    names = sorted({n for d in ka[:k] for n in d} | {n for d in kb[:k] for n in d})
    for name in names:
        krit[name] = mean_ci([ka[i].get(name, 0.0) - kb[i].get(name, 0.0) for i in range(k)])
    return {"kennzahlen": out, "plattenpunkte_je_kriterium": krit, "n_paare": k}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed-base", type=int, default=20260912,
                    help="Basis-Seed; Partie i spielt seed_base + i*0x9E3779B97F4A7C15")
    ap.add_argument("--n-seeds", type=int, default=200, help="Partien je Arm und Paarung")
    ap.add_argument("--pairings", default="25,400",
                    help="Sims-Stufen wie in Stufe 0, kommagetrennt (beide Seiten "
                         "derselben Paarung spielen mit derselben Stufe)")
    ap.add_argument("--threads", type=int, default=0,
                    help="0 = alle Kerne, 1 = sequenziell, n = Pool mit n Threads "
                         "(self_play.rs::thread_plan)")
    ap.add_argument("--c", type=float, default=0.3, help="UCT-Konstante der Heuristik-Suche")
    ap.add_argument("--slot", type=int, default=None,
                    help="optional: Startslot von Spieler 0 erzwingen (0..8). Ungesetzt = "
                         "Bestand, und der ist laut Stufe 0 immer (0,0)")
    ap.add_argument("--limit", type=int, default=None,
                    help="Rauchtest: ueberschreibt --n-seeds mit wenigen Partien")
    ap.add_argument("--out", default=str(OUT_DEFAULT))
    a = ap.parse_args()

    n_games = a.limit if a.limit else a.n_seeds
    sims_stufen = [int(x) for x in a.pairings.split(",") if x.strip()]
    if not sims_stufen:
        raise SystemExit("--pairings braucht mindestens eine Sims-Stufe")
    if a.slot is not None and not (0 <= a.slot <= 8):
        raise SystemExit("--slot ist ein Index 0..8 (row*3+col)")
    erwarteter_slot = 0 if a.slot is None else a.slot

    t0, cpu0 = time.monotonic(), time.process_time()
    games_total = 0
    fehlende_logs = 0
    ergebnis: dict[str, dict] = {}

    for sims in sims_stufen:
        paarung = f"hv1@{sims}_vs_hv1@{sims}"
        print(f"[paarung] {paarung}: 2 Arme x {n_games} Partien, threads={a.threads}",
              flush=True)
        je_arm: dict[str, dict] = {}
        for arm in ARMS:
            t_arm = time.monotonic()
            games = run_arm(arm, sims, n_games, a.seed_base, a.threads, a.c, a.slot)
            games_total += len(games)
            block = collect_arm(games, erwarteter_slot)
            fehlende_logs += block["partien_ohne_rekonstruierbares_log"]
            je_arm[arm] = block
            kz = block["kennzahlen"]
            print(f"  [{arm}] n={block['n']}  points_mean={kz['punkte']['mittel']}  "
                  f"margin={kz['margin']['mittel']}  "
                  f"Kandidaten={block['start_tile_verteilung']['verschiedene_kandidaten']}  "
                  f"({time.monotonic() - t_arm:.1f} s)", flush=True)
            if block["slot_kontrolle"]["abweichungen"]:
                print(f"  [{arm}] WARNUNG: {block['slot_kontrolle']['abweichungen']} von "
                      f"{block['n']} Partien legen NICHT auf Slot {erwarteter_slot} "
                      f"({block['slot_kontrolle']['abweichungen_nach_slot']})", flush=True)

        gepaart = paired_diff(je_arm[ARM_HAND], je_arm[ARM_RANDOM])
        margin_mean = gepaart["kennzahlen"]["margin"]
        print(f"  [gepaart] Handregel minus Zufall: margin {margin_mean['mittel']} "
              f"KI95 {margin_mean['ki95']}, punkte {gepaart['kennzahlen']['punkte']['mittel']} "
              f"KI95 {gepaart['kennzahlen']['punkte']['ki95']}", flush=True)

        # Rohwerte nicht ins Artefakt -- sie sind Zwischenstand, nicht Befund.
        for block in je_arm.values():
            block.pop("_werte", None)
            block.pop("_kriterien", None)
        ergebnis[paarung] = {
            "sims": sims,
            "je_arm": je_arm,
            "gepaart_handregel_minus_zufall": gepaart,
        }

    wanduhr = time.monotonic() - t0
    out = {
        "frage": "Traegt die Handregel bei PLATTE und ROTATION der Startkuppel? "
                 "(PREREG_start_dome_choice.md par.9a Punkt 1)",
        "vorab_lesart": (
            "Zielgroesse ist die gepaarte Differenz Handregel minus Zufall in Marge und "
            "Punkten. Schliesst das 95-%-Intervall 0 ein, ist auch Platte/Rotation kein "
            "Hebel; ist die Differenz gross, traegt die Handregel und ist die Messlatte "
            "fuer den Such-Start (par.9c)."
        ),
        "aufbau": {
            "netzfrei": True,
            "beide_seiten": "Heuristik-MCTS (hv1), gleiche Sims je Paarung",
            "namen": {"gestreute_seite": NAME_SELF, "gegenseite": NAME_OPP},
            "einstieg": "mosaic_rust.arena_match(log_games=True)",
            "knopf": KNOB_SELF,
            "knopf_gegenseite": f"{KNOB_OPP} ungesetzt (Bestand)",
            "slot": ("Bestand (Handregel, laut Stufe 0 immer (0,0))" if a.slot is None
                     else f"erzwungen ueber {SLOT_KNOB_SELF}={a.slot}"),
            "seed_base": a.seed_base,
            "seed_ableitung": "seed_base + i*0x9E3779B97F4A7C15 (self_play.rs::run_arena_match)",
            "gepaart": "Partie i ist in beiden Armen dieselbe Ausgangslage",
            "zufallsstrom": ("eigener, aus game_seed abgeleiteter Strom je Startsetzung "
                             "(self_play.rs::play_arena_game) -- der Partie-RNG der "
                             "Nachziehplatten bleibt unberuehrt"),
            "c": a.c,
        },
        "grundmenge": {
            "n_je_arm_und_paarung": n_games,
            "grundmenge": "Partien eines Arms in einer Paarung, Sicht Spieler 0 (Brett 0)",
            "einheit": "je Partie",
            "partien_gesamt": games_total,
            "partien_ohne_rekonstruierbares_log": fehlende_logs,
        },
        "paarungen": ergebnis,
        "laufzeit": {
            "wanduhr_s": round(wanduhr, 1),
            "cpu_s": round(time.process_time() - cpu0, 1),
            "threads": a.threads,
            "s_je_partie": round(wanduhr / max(1, games_total), 3),
        },
        "cli_args": vars(a),
    }

    target = Path(a.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    print(f"\n[fertig] {games_total} Partien in {wanduhr:.1f} s -> {target}", flush=True)
    for name, block in ergebnis.items():
        g = block["gepaart_handregel_minus_zufall"]["kennzahlen"]
        print(f"  {name}: margin {g['margin']['mittel']} KI95 {g['margin']['ki95']}, "
              f"punkte {g['punkte']['mittel']} KI95 {g['punkte']['ki95']}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
