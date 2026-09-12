# -*- coding: utf-8 -*-
"""Stufe 0 der Startkuppel-Frage: wie gross ist die Spannweite ueber die neun
Startslots? (`evaluations/PREREG_start_dome_choice.md` par.4)

NETZFREI, GEPAART, HEURISTIK AUF BEIDEN SEITEN. Dieselbe Partie wird neunmal
gespielt -- identischer Seed, also identische Fabriken, Beutel, Kuppelstapel
und Wertungsplatten -- und unterscheidet sich NUR im erzwungenen Startslot von
Spieler 0 (`MOSAIC_START_SLOT_P0`, Diagnoseknopf,
`self_play.rs::choose_start_placement_with_slot`). Spieler 1 bleibt im
Bestand: `MOSAIC_START_SLOT_P1` wird von dieser Sonde nie gesetzt.

Gepaart faellt alles weg, was nicht am Slot haengt: Bezugsgroesse ist die
Differenz zu Slot 0, Partie fuer Partie.

WELCHER PARTIE-EINSTIEG und warum
---------------------------------
`mosaic_rust.arena_match(sims_a, sims_b, n_games, seed, num_threads, c,
log_games)` -- Heuristik-MCTS gegen Heuristik-MCTS, komplett in Rust, kein
Netz, keine Records auf der Platte. Partie `i` bekommt den abgeleiteten Seed
`seed + i * 0x9E3779B97F4A7C15` (`self_play.rs::run_arena_match`), und diese
Ableitung haengt NICHT am Slot -- Partie `i` in Slot A und Partie `i` in
Slot B sind damit dieselbe Ausgangslage. Brett 0 ist Agent A, also der
Spieler, dessen Startslot erzwungen wird; der Startspieler alterniert mit
`i % 2` und ist in allen neun Armen derselbe.

Die anderen Kandidaten scheiden aus: `net_arena_match`/`net_vs_net_arena_match`
brauchen ein ONNX (die Prereg verlangt netzfrei), `self_play_games` schreibt
Record-Dateien, und der Referee-Pfad (`tools/frozen_referee_match.py`) startet
je Partie Kindprozesse mit eigenem Wheel -- teuer und fuer eine reine
Heuristik-Messung ohne Nutzen.

DER KNOPF WIRD JE PARTIE GELESEN
--------------------------------
`self_play.rs::forced_start_slot` liest die Umgebungsvariable bei JEDER
Startsetzung, nicht einmalig per `OnceLock`. Darum genuegt es, sie zwischen
zwei Arena-Aufrufen im selben Prozess umzusetzen; Kindprozesse je Slot sind
nicht noetig. Gesetzt wird ausschliesslich, waehrend keine Partie laeuft.

ZIRKULARITAETS-WAECHTER (par.4)
-------------------------------
par.4 verlangt zwei VERSCHIEDEN FAEHIGE Spieler und nennt `v1`/`v2huelle`
(heute `hv1`/`hv2`). **hv2 ist in diesem Build nicht spielbar**: der zweite
Zweig wurde am 2026-08-26 aus dem Quellstand entfernt, `SearchConfig::
from_spec_file` weist eine hv2-Spec hart ab (`engine/src/net_mcts.rs`, Pruefung
`variant_name != "hv1"`), ebenso der Self-Play-Einstieg (`engine/src/lib.rs`,
`heuristik_variante`). hv2 lebt nur noch als eingefrorenes Artefakt
(`models/frozen_heuristics/hv2_generator/`) mit seinem EIGENEN, aelteren
Wheel -- und dieses Wheel kennt `MOSAIC_START_SLOT_P0` nicht, kann den Slot
also gar nicht erzwingen.

Der Waechter faehrt deshalb ueber die FAEHIGKEITSSTUFE statt ueber die
Variante: zwei Paarungen hv1 gegen hv1 mit unterschiedlicher Suchtiefe
(Default 25 und 400 Sims). Die Suchtiefe ist der gemessene Regler zwischen
Prior und Value-Kopf und veraendert das Spiel strukturell (~0,6 Spalten bei
25-100 Sims gegen 0,34 ab 250). Kippt die Rangfolge der Slots zwischen den
Stufen, ist "guter Start" eine Eigenschaft der Faehigkeit und nicht der
Position -- dieselbe Lesart wie in par.4.

**Das ist eine ABWEICHUNG von par.4 und als solche im Artefakt vermerkt**
(`waechter`-Block, Feld `abweichung_von_prereg`).

Aufruf (die Maschine muss frei sein, CLAUDE.md "Messungen laufen EXKLUSIV"):
    python -X utf8 -u tools/probes/start_dome_slot_probe.py

Rauchtest (wenige Partien, kurze Suche):
    python -X utf8 -u tools/probes/start_dome_slot_probe.py --limit 4 \
        --pairings 25 --threads 4
"""
from __future__ import annotations

import argparse
import json
import math
import os
import statistics
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
# dieselben Rekonstruktions-Helfer, die jede andere Arena-Auswertung benutzt.
from column_build_structural_probe import (  # noqa: E402
    column_fill,
    final_scoring_criteria_per_player,
    reconstruct_game,
    struktur_kennzahlen,
)
from analyze_game_log import PATTERNS, ROUND_PREFIX  # noqa: E402


def realised_start_slot(log: list[str], name: str) -> int | None:
    """Slot-Index (row*3+col) der Startkuppel von Spieler `name` aus der
    START_TILE-Logzeile; None, wenn keine gefunden. Dient als KONTROLLE, dass
    der erzwungene Slot wirklich gelegt wurde (sonst waere die Messung eine
    Messung des Bestands unter falschem Etikett)."""
    for raw_line in log or []:
        if raw_line.startswith("#"):
            continue
        m = ROUND_PREFIX.match(raw_line)
        text = m.group(2) if m else raw_line
        mm = PATTERNS["START_TILE"].match(text)
        if mm and mm.group("name") == name:
            return int(mm.group("row")) * 3 + int(mm.group("col"))
    return None

OUT_DEFAULT = ROOT / "evaluations" / "artifacts" / "start_dome_slot_probe.json"

# Brett 0 = Agent A = der Spieler mit erzwungenem Slot (run_arena_match
# vergibt die Namen "A"/"B" in Brettreihenfolge).
NAME_SELF, NAME_OPP = "A", "B"
SLOTS = list(range(9))
KNOB_SELF = "MOSAIC_START_SLOT_P0"
KNOB_OPP = "MOSAIC_START_SLOT_P1"

# Tragende Groessen zuerst (par.4 Punkt 1), danach die Struktur- und
# Standard-Kennzahlen. Einheit je Eintrag = je Partie, Grundmenge = die
# Partien dieses Slots.
METRICS = [
    "punkte",
    "margin",
    "volle_spalten",
    "volle_reihen",
    "max_spaltenhoehe",
    "teilspalten_ge3",
    "teilspalten_ge4",
    "max_reihenhoehe",
    "gefuellte_zellen",
    "strafpunkte",
    "gegner_punkte",
]


def row_fill(cells: set[tuple[int, int, int]]) -> list[int]:
    """Zeilenfuellstand des 6x6-Bretts, Gegenstueck zu `column_fill`.

    Slot `(tr, tc)` plus lokaler Space-Index `si` (0=oben-links, 1=oben-rechts,
    2=unten-links, 3=unten-rechts) -> Brettzeile `2 * tr + si // 2`. Dieselbe
    Zerlegung, die `column_fill` fuer die Spalte mit `si % 2` benutzt.
    """
    fill = [0] * 6
    for (r, _c, si) in cells:
        fill[2 * r + (si // 2)] += 1
    return fill


def game_metrics(game: dict) -> dict | None:
    """Kennzahlen EINER Partie aus Sicht von Spieler 0 (Brett 0).

    Gibt `None`, wenn das Log fehlt oder die Rekonstruktion leer bleibt -- so
    ein Fall wird gezaehlt, nicht stillschweigend uebersprungen.
    """
    log = game.get("log") or []
    cells = reconstruct_game(log)
    own = cells.get(NAME_SELF)
    if not own:
        return None
    cfill = column_fill(own)
    rfill = row_fill(own)
    scores = game["scores"]
    out = {
        "punkte": float(scores[0]),
        "margin": float(scores[0] - scores[1]),
        "gegner_punkte": float(scores[1]),
        "strafpunkte": float(game["total_floor"][0]),
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
    out["_plattenpunkte"] = final_scoring_criteria_per_player(log).get(NAME_SELF, {})
    out["_game_seed"] = game.get("game_seed")
    out["_start_slot"] = realised_start_slot(log, NAME_SELF)
    return out


def mean_ci(values: list[float]) -> dict:
    """Mittelwert mit 95-%-Intervall (normal, sd/sqrt(n)). n < 2 -> kein KI."""
    n = len(values)
    if n == 0:
        return {"n": 0, "mittel": None, "sd": None, "ki95": None}
    m = statistics.fmean(values)
    if n < 2:
        return {"n": n, "mittel": round(m, 4), "sd": None, "ki95": None}
    sd = statistics.stdev(values)
    halb = 1.96 * sd / math.sqrt(n)
    return {
        "n": n,
        "mittel": round(m, 4),
        "sd": round(sd, 4),
        "ki95": [round(m - halb, 4), round(m + halb, 4)],
    }


def ranks(values: list[float]) -> list[float]:
    """Raenge 1..k, Bindungen bekommen den Mittelrang."""
    pairs = sorted(range(len(values)), key=lambda i: values[i])
    out = [0.0] * len(values)
    i = 0
    while i < len(pairs):
        j = i
        while j + 1 < len(pairs) and values[pairs[j + 1]] == values[pairs[i]]:
            j += 1
        mittel = (i + j) / 2 + 1
        for k in range(i, j + 1):
            out[pairs[k]] = mittel
        i = j + 1
    return out


def spearman(a: list[float], b: list[float]) -> float | None:
    """Rang-Korrelation (Pearson auf den Raengen), vertraegt Bindungen."""
    if len(a) != len(b) or len(a) < 2:
        return None
    ra, rb = ranks(a), ranks(b)
    ma, mb = statistics.fmean(ra), statistics.fmean(rb)
    za = sum((x - ma) ** 2 for x in ra)
    zb = sum((x - mb) ** 2 for x in rb)
    if za == 0 or zb == 0:
        return None
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    return round(cov / math.sqrt(za * zb), 4)


def run_slot(slot: int, sims: int, n_games: int, seed_base: int, threads: int, c: float) -> list[dict]:
    """Eine Arena ueber `n_games` Partien mit erzwungenem Slot fuer Spieler 0.

    Der Knopf wird HIER gesetzt, also zwischen zwei Arena-Aufrufen und damit zu
    einem Zeitpunkt, an dem keine Rust-Partie laeuft (nebenlaeufiges Schreiben
    der Prozessumgebung waere sonst der Fehler).
    """
    os.environ[KNOB_SELF] = str(slot)
    os.environ.pop(KNOB_OPP, None)  # Gegenseite bleibt ausdruecklich im Bestand
    raw = mr.arena_match(sims, sims, n_games, seed=seed_base, num_threads=threads,
                         c=c, log_games=True)
    return json.loads(raw)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed-base", type=int, default=20260912,
                    help="Basis-Seed; Partie i spielt seed_base + i*0x9E3779B97F4A7C15")
    ap.add_argument("--n-seeds", type=int, default=60, help="Partien je Slot und Paarung")
    ap.add_argument("--pairings", default="25,400",
                    help="Sims-Stufen des Zirkularitaets-Waechters, kommagetrennt "
                         "(beide Seiten derselben Paarung spielen mit derselben Stufe)")
    ap.add_argument("--threads", type=int, default=0,
                    help="0 = alle Kerne, 1 = sequenziell, n = Pool mit n Threads "
                         "(self_play.rs::thread_plan)")
    ap.add_argument("--c", type=float, default=0.3, help="UCT-Konstante der Heuristik-Suche")
    ap.add_argument("--limit", type=int, default=None,
                    help="Rauchtest: ueberschreibt --n-seeds mit wenigen Partien")
    ap.add_argument("--out", default=str(OUT_DEFAULT))
    a = ap.parse_args()

    n_games = a.limit if a.limit else a.n_seeds
    sims_stufen = [int(x) for x in a.pairings.split(",") if x.strip()]
    if not sims_stufen:
        raise SystemExit("--pairings braucht mindestens eine Sims-Stufe")

    t0, cpu0 = time.monotonic(), time.process_time()
    games_total = 0
    fehlende_logs = 0
    ergebnis: dict[str, dict] = {}

    for sims in sims_stufen:
        paarung = f"hv1@{sims}_vs_hv1@{sims}"
        print(f"[paarung] {paarung}: 9 Slots x {n_games} Partien, threads={a.threads}",
              flush=True)
        je_slot: dict[str, dict] = {}
        raw_values: dict[int, dict[str, list[float]]] = {}
        plattenpunkte: dict[int, Counter] = {}
        reihenprofil: dict[int, list[float]] = {}
        spaltenprofil: dict[int, list[float]] = {}

        for slot in SLOTS:
            t_slot = time.monotonic()
            games = run_slot(slot, sims, n_games, a.seed_base, a.threads, a.c)
            games_total += len(games)
            values: dict[str, list[float]] = defaultdict(list)
            krit = Counter()
            rsum = [0.0] * 6
            csum = [0.0] * 6
            n_ok = 0
            slot_hits = 0
            slot_misses: Counter = Counter()
            for g in games:
                m = game_metrics(g)
                if m is None:
                    fehlende_logs += 1
                    continue
                n_ok += 1
                if m["_start_slot"] == slot:
                    slot_hits += 1
                else:
                    slot_misses[str(m["_start_slot"])] += 1
                for key in METRICS:
                    values[key].append(m[key])
                for k, v in m["_plattenpunkte"].items():
                    krit[k] += v
                for i in range(6):
                    rsum[i] += m["_reihenfuellstand"][i]
                    csum[i] += m["_spaltenfuellstand"][i]
            raw_values[slot] = dict(values)
            plattenpunkte[slot] = krit
            teiler = max(1, n_ok)
            reihenprofil[slot] = [round(x / teiler, 3) for x in rsum]
            spaltenprofil[slot] = [round(x / teiler, 3) for x in csum]
            je_slot[str(slot)] = {
                "slot_index": slot,
                "slot_rc": [slot // 3, slot % 3],
                "n": n_ok,
                "kennzahlen": {k: mean_ci(values[k]) for k in METRICS},
                "reihenauslastung_mittel": reihenprofil[slot],
                "spaltenauslastung_mittel": spaltenprofil[slot],
                "plattenpunkte_je_kriterium": {
                    k: round(v / teiler, 3) for k, v in sorted(krit.items())
                },
                # Kontrolle: wurde der erzwungene Slot wirklich gelegt?
                # Abweichungen = Partien, in denen die Startkuppel von Spieler 0
                # laut START_TILE-Logzeile woanders liegt (Slot belegt -> Rueckfall
                # auf den Bestand, self_play.rs::choose_start_placement_with_slot).
                "slot_kontrolle": {
                    "erzwungen": slot,
                    "treffer": slot_hits,
                    "abweichungen": n_ok - slot_hits,
                    "abweichungen_nach_slot": dict(slot_misses),
                },
            }
            if n_ok - slot_hits:
                print(f"  [slot {slot}] WARNUNG: {n_ok - slot_hits} von {n_ok} Partien liegen "
                      f"NICHT im erzwungenen Slot ({dict(slot_misses)})", flush=True)
            margin_mean = je_slot[str(slot)]["kennzahlen"]["margin"]["mittel"]
            points_mean = je_slot[str(slot)]["kennzahlen"]["punkte"]["mittel"]
            print(f"  [slot {slot}] n={n_ok}  points_mean={points_mean}  margin={margin_mean}  "
                  f"({time.monotonic() - t_slot:.1f} s)", flush=True)

        # Gepaarte Differenz zu Slot 0, Partie fuer Partie (par.4: gepaart
        # faellt alles weg, was nicht am Slot haengt).
        gepaart: dict[str, dict] = {}
        for slot in SLOTS[1:]:
            diffs = {}
            for key in METRICS:
                basis = raw_values[0].get(key, [])
                arm = raw_values[slot].get(key, [])
                k = min(len(basis), len(arm))
                diffs[key] = mean_ci([arm[i] - basis[i] for i in range(k)])
            gepaart[str(slot)] = diffs

        # Ein leerer Slot (keine rekonstruierbare Partie) hat kein Mittel --
        # er darf die Sortierung nicht sprengen, sondern faellt ans Ende.
        def mittel_von(slot: int, key: str) -> float:
            m = je_slot[str(slot)]["kennzahlen"][key]["mittel"]
            return float("-inf") if m is None else m

        # Spannweite ueber die neun Slots, je Kennzahl.
        spannweite = {}
        for key in METRICS:
            mittel = [je_slot[str(s)]["kennzahlen"][key]["mittel"] for s in SLOTS]
            mittel = [m for m in mittel if m is not None]
            if not mittel:
                continue
            hoch = max(mittel)
            tief = min(mittel)
            spannweite[key] = {
                "min": round(tief, 4),
                "max": round(hoch, 4),
                "spanne": round(hoch - tief, 4),
                "bester_slot": max(SLOTS, key=lambda s, k=key: mittel_von(s, k)),
                "schlechtester_slot": min(SLOTS, key=lambda s, k=key: mittel_von(s, k)),
            }

        ergebnis[paarung] = {
            "sims": sims,
            "je_slot": je_slot,
            "gepaart_gegen_slot0": gepaart,
            "spannweite_ueber_slots": spannweite,
            "rangfolge_nach_margin": sorted(
                SLOTS, key=lambda s: mittel_von(s, "margin"), reverse=True
            ),
            "rangfolge_nach_punkten": sorted(
                SLOTS, key=lambda s: mittel_von(s, "punkte"), reverse=True
            ),
        }

    # Waechter: kippt die Rangfolge zwischen den Faehigkeitsstufen?
    waechter = {
        "frage": "Ist 'guter Start' eine Eigenschaft der Position oder der Faehigkeit? (par.4)",
        "abweichung_von_prereg": (
            "par.4 nennt hv1 gegen hv2. hv2 ist in diesem Build NICHT spielbar "
            "(net_mcts.rs weist eine hv2-Spec ab, lib.rs weist heuristik_variante != hv1 ab; "
            "der zweite Zweig ist seit 2026-08-26 aus dem Quellstand entfernt), und das "
            "eingefrorene Artefakt models/frozen_heuristics/hv2_generator laeuft auf einem "
            "aelteren Wheel, das MOSAIC_START_SLOT_P0 nicht kennt. Ersatz: zwei "
            "Faehigkeitsstufen derselben Variante ueber die Suchtiefe."
        ),
        "paarungen": list(ergebnis.keys()),
    }
    names = list(ergebnis.keys())
    if len(names) >= 2:
        a_name, b_name = names[0], names[-1]
        def _m(name: str, s: int) -> float:
            v = ergebnis[name]["je_slot"][str(s)]["kennzahlen"]["margin"]["mittel"]
            return 0.0 if v is None else v

        ma = [_m(a_name, s) for s in SLOTS]
        mb = [_m(b_name, s) for s in SLOTS]
        rho = spearman(ma, mb)
        waechter["spearman_margin"] = rho
        waechter["bester_slot"] = {
            a_name: ergebnis[a_name]["rangfolge_nach_margin"][0],
            b_name: ergebnis[b_name]["rangfolge_nach_margin"][0],
        }
        waechter["kippt"] = (rho is not None and rho < 0.0)
    else:
        waechter["spearman_margin"] = None
        waechter["kippt"] = None
        waechter["hinweis"] = "nur EINE Paarung gefahren -- der Waechter ist damit NICHT erhoben"

    wanduhr = time.monotonic() - t0
    out = {
        "frage": "Wie gross ist die Spannweite der neun Startslots? "
                 "(PREREG_start_dome_choice.md par.4, Stufe 0)",
        "aufbau": {
            "netzfrei": True,
            "beide_seiten": "Heuristik-MCTS (hv1), gleiche Sims je Paarung",
            "namen": {"erzwungene_seite": NAME_SELF, "gegenseite": NAME_OPP},
            "einstieg": "mosaic_rust.arena_match(log_games=True)",
            "knopf": KNOB_SELF,
            "knopf_gegenseite": f"{KNOB_OPP} ungesetzt (Bestand)",
            "seed_base": a.seed_base,
            "seed_ableitung": "seed_base + i*0x9E3779B97F4A7C15 (self_play.rs::run_arena_match)",
            "gepaart": "Partie i ist in allen neun Slots dieselbe Ausgangslage",
            "c": a.c,
        },
        "grundmenge": {
            "n_je_slot_und_paarung": n_games,
            "grundmenge": "Partien eines Slots in einer Paarung, Sicht Spieler 0 (Brett 0)",
            "einheit": "je Partie",
            "partien_gesamt": games_total,
            "partien_ohne_rekonstruierbares_log": fehlende_logs,
        },
        "waechter": waechter,
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
        sp = block["spannweite_ueber_slots"]
        print(f"  {name}: Spanne margin {sp['margin']['spanne']} "
              f"(bester Slot {sp['margin']['bester_slot']}, "
              f"schlechtester {sp['margin']['schlechtester_slot']}), "
              f"Spanne punkte {sp['punkte']['spanne']}", flush=True)
    print(f"  Waechter: spearman(margin) = {waechter.get('spearman_margin')}, "
          f"kippt = {waechter.get('kippt')}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
