# -*- coding: utf-8 -*-
"""Bedingte Vielfalt: wie viel Streuung im Korpus kommt vom VERHALTEN, nicht vom Spiel?

Anlass (Nutzer 2026-09-07, 02:15): *"welche werkzeuge oder metrics haben wir um die self
play daten zu analysieren bzgl. diversitaet/entropie unter beruecksichtigung der streuung
aus dem spiel (die anscheinend kein lernsignal ist)"*. Die vorhandenen Masse mischen beides:
`corpus_state_diversity_probe.py` zaehlt distinkte Brettmuster ueber ALLE Partien, und in
denen steckt die Auslagen-Ziehung genauso wie die Zugwahl. `PREREG_uncertainty_guided_selfplay.md`
par.2 nennt die aleatorische Streuung ausdruecklich KEIN Lernsignal.

Diese Sonde trennt die beiden ueber die PAARUNG: mehrere Chargen desselben Generators mit
DEMSELBEN Basis-Seed haben je Spielindex identische Wertungsplatten, Startspieler und
Auslagen-Ziehungen. Jeder Unterschied zwischen den Chargen bei gleichem Index ist damit
Verhalten.

Gemessen wird je Chargen-Paar und je Spielindex:
  1. **Divergenz-Halbzug**: der erste Record-Index, an dem sich die gespielte Aktion
     unterscheidet (aus `policy`-Eintrag mit prob 1.0 bzw. dem hoechsten prob).
  2. **Endbrett-Abstand**: Hamming-Abstand der 36-Bit-Belegungsmasken beider Seiten.
  3. **Bedingte Vielfalt**: distinkte Endbretter je Spielindex UEBER die Chargen (nur
     Verhalten) gegen distinkte Endbretter INNERHALB einer Charge ueber die Indizes
     (Verhalten + Spiel). Das Verhaeltnis ist die eigentliche Antwort.

Aufruf (Projektordner):
    python -X utf8 tools/probes/paired_corpus_divergence_probe.py \\
        "data::selfplay_tempA-tau0_*.pkl" "data::selfplay_tempB-tau12_*.pkl" \\
        --out evaluations/artifacts/paired_divergence_temperature.json
    python -X utf8 tools/probes/paired_corpus_divergence_probe.py --selftest
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import math
import os
import pathlib
import statistics
import sys
import time

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "tools" / "probes"))

PREREG = "Nutzer-Auftrag 2026-09-07 (Diversitaet ohne Spiel-Zufall)"


def fill_mask(player: dict) -> int:
    """36-Bit-Maske der gefuellten Kuppelfelder -- dieselbe kanonische Form wie
    `corpus_state_diversity_probe.fill_mask` (fester Bit-Index je Slot/Space)."""
    m = 0
    grid = player.get("dome_grid") or []
    for sr in range(3):
        row = grid[sr] if sr < len(grid) else []
        for sc in range(3):
            slot = row[sc] if sc < len(row) else None
            spaces = (slot or {}).get("spaces") or []
            for si in range(4):
                sp = spaces[si] if si < len(spaces) else None
                if sp and sp.get("filled"):
                    m |= 1 << (sr * 12 + sc * 4 + si)
    return m


def played_action(rec: dict):
    """Die GESPIELTE Aktion eines Records als vergleichbarer Schluessel.

    Die Policy-Liste traegt die Besuchsverteilung; gespielt wurde bei `--deterministic`
    der erste Eintrag, sonst ein gesampelter. Der Record haelt die Wahl nicht getrennt --
    fuer den Divergenz-Punkt genuegt der Eintrag mit der hoechsten Wahrscheinlichkeit,
    weil sich Chargen mit unterschiedlicher Temperatur schon in der VERTEILUNG
    unterscheiden, sobald sie in verschiedenen Stellungen stehen.
    """
    pol = rec.get("policy") or []
    if not pol:
        return None
    best = max(pol, key=lambda e: e.get("prob", 0.0))
    return json.dumps(best.get("action"), sort_keys=True)


def load_charge(spec: str, limit: int | None = None) -> dict:
    """`dir::glob` -> {spielindex: [records in Reihenfolge]}, Index aus der `game_id`
    (Suffix `_g<N>`), damit die Paarung ueber Chargen hinweg stimmt."""
    from corpus_io import load_records

    directory, pattern = (spec.split("::", 1) + ["*.pkl"])[:2] if "::" in spec else (spec, "*.pkl")
    games: dict[str, list] = collections.defaultdict(list)
    for f in sorted(glob.glob(os.path.join(directory, pattern))):
        for r in load_records(f):
            gid = r.get("game_id") or ""
            # `game_id` = "<version>_<datum>_<zeit>_c<chunk>_g<index>"; der Index allein
            # ist NICHT eindeutig (er zaehlt je Chunk neu). Schluessel ist deshalb
            # "c<chunk>_g<index>" -- bei gleicher Chunk-Groesse und gleichem Basis-Seed
            # bezeichnet er ueber Chargen hinweg dieselbe Startbedingung.
            parts = gid.split("_")
            if len(parts) < 2 or not parts[-1].startswith("g") or not parts[-2].startswith("c"):
                continue
            games["_".join(parts[-2:])].append(r)
    if limit:
        keep = sorted(games)[:limit]
        games = {k: games[k] for k in keep}
    return games


def end_masks(records: list) -> tuple:
    """Endbrett-Masken beider Seiten aus dem letzten Record."""
    if not records:
        return (0, 0)
    st = (records[-1].get("state") or {})
    players = st.get("players") or []
    return tuple(fill_mask(p) for p in players[:2]) or (0, 0)


def policy_entropy(records: list) -> float:
    """Mittlere Entropie der Policy-Ziele (nats). Mass fuer die Schaerfe der ZIELE --
    unabhaengig davon, welcher Zug gespielt wurde."""
    vals = []
    for r in records:
        probs = [e.get("prob", 0.0) for e in (r.get("policy") or [])]
        if len(probs) > 1:
            vals.append(-sum(p * math.log(p + 1e-12) for p in probs if p > 0))
    return statistics.mean(vals) if vals else 0.0


def compare(charges: dict, names: list) -> dict:
    common = sorted(set.intersection(*[set(c) for c in charges.values()])) if charges else []
    out = {"partien_gepaart": len(common), "arme": {}, "paare": {}}
    for name in names:
        g = charges[name]
        recs_all = [r for i in common for r in g[i]]
        distinct_end = {m for i in common for m in end_masks(g[i])}
        out["arme"][name] = {
            "records": len(recs_all),
            "distinkte_endbretter_ueber_partien": len(distinct_end),
            "endbretter_je_seite": round(len(distinct_end) / max(1, 2 * len(common)), 4),
            "policy_entropie_mittel": round(policy_entropy(recs_all), 4),
            "schritte_je_partie": round(len(recs_all) / max(1, len(common)), 1),
        }
    # Bedingte Vielfalt: je Spielindex ueber die Chargen
    per_index_distinct = []
    for i in common:
        masks = {m for name in names for m in end_masks(charges[name][i])}
        per_index_distinct.append(len(masks))
    base = names[0]
    for name in names[1:]:
        div_moves, hamming, identical = [], [], 0
        for i in common:
            a, b = charges[base][i], charges[name][i]
            d = None
            for k in range(min(len(a), len(b))):
                if played_action(a[k]) != played_action(b[k]):
                    d = k
                    break
            if d is None:
                identical += 1
                d = min(len(a), len(b))
            div_moves.append(d)
            ma, mb = end_masks(a), end_masks(b)
            hamming.append(sum(bin(x ^ y).count("1") for x, y in zip(ma, mb)))
        out["paare"][f"{base} vs {name}"] = {
            "divergenz_halbzug_median": statistics.median(div_moves) if div_moves else None,
            "divergenz_halbzug_mittel": round(statistics.mean(div_moves), 2) if div_moves else None,
            "partien_identisch": identical,
            "endbrett_hamming_mittel": round(statistics.mean(hamming), 2) if hamming else None,
        }
    out["bedingte_vielfalt"] = {
        "distinkte_endbretter_je_spielindex_mittel": round(statistics.mean(per_index_distinct), 3) if per_index_distinct else None,
        "maximum_moeglich": 2 * len(names),
        "lesart": ("je Spielindex sind Wertungsplatten, Startspieler und Auslagen identisch -- "
                   "was hier an Vielfalt bleibt, kommt vom VERHALTEN; die Zahl je Arm oben "
                   "enthaelt zusaetzlich die Streuung aus dem Spiel"),
    }
    return out


def selftest() -> int:
    rec = {"players": [{"dome_grid": [[{"spaces": [{"filled": "rot"}, None, None, None]}]]}]}
    assert fill_mask(rec["players"][0]) == 1
    a = [{"policy": [{"action": {"t": 1}, "prob": 1.0}], "state": {"players": [{"dome_grid": []}, {"dome_grid": []}]}}]
    b = [{"policy": [{"action": {"t": 2}, "prob": 1.0}], "state": {"players": [{"dome_grid": []}, {"dome_grid": []}]}}]
    assert played_action(a[0]) != played_action(b[0])
    res = compare({"A": {"c0_g1": a}, "B": {"c0_g1": b}}, ["A", "B"])
    assert res["partien_gepaart"] == 1
    assert res["paare"]["A vs B"]["divergenz_halbzug_median"] == 0
    assert res["paare"]["A vs B"]["partien_identisch"] == 0
    two = [{"policy": [{"action": {"t": 1}, "prob": 0.5}, {"action": {"t": 2}, "prob": 0.5}],
            "state": {"players": [{"dome_grid": []}, {"dome_grid": []}]}}]
    assert abs(policy_entropy(two) - math.log(2)) < 1e-6
    print("selftest ok")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("charges", nargs="*", help="je Arm ein <verzeichnis>::<glob>")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if len(a.charges) < 2 or not a.out:
        ap.error("mindestens zwei Chargen und --out")
    t0 = time.time()
    names, charges = [], {}
    for spec in a.charges:
        name = spec.split("::")[-1].replace("selfplay_", "").replace("_*.pkl", "")
        names.append(name)
        charges[name] = load_charge(spec, a.limit)
        print(f"  {name}: {len(charges[name])} Partien geladen ({time.time()-t0:.0f}s)", flush=True)
    res = compare(charges, names)
    res["prereg"] = PREREG
    res["laufzeit"] = {"wanduhr_s": round(time.time() - t0, 1), "cpu_s": round(time.process_time(), 1),
                       "threads": 1, "s_je_partie": None}
    pathlib.Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nGepaarte Partien: {res['partien_gepaart']}")
    for name, v in res["arme"].items():
        print(f"  {name}: Endbretter je Seite {v['endbretter_je_seite']} | Policy-Entropie "
              f"{v['policy_entropie_mittel']} | Schritte/Partie {v['schritte_je_partie']}")
    for pair, v in res["paare"].items():
        print(f"  {pair}: Divergenz ab Halbzug {v['divergenz_halbzug_median']} (Mittel "
              f"{v['divergenz_halbzug_mittel']}), identisch {v['partien_identisch']}, "
              f"Endbrett-Hamming {v['endbrett_hamming_mittel']}")
    bv = res["bedingte_vielfalt"]
    print(f"  BEDINGT (gleicher Spielindex): {bv['distinkte_endbretter_je_spielindex_mittel']} "
          f"distinkte Endbretter von max {bv['maximum_moeglich']}")
    print(f"Artefakt {a.out} ({res['laufzeit']['wanduhr_s']} s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
