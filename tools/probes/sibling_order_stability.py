# -*- coding: utf-8 -*-
"""Ordnet der Ownership-Kopf die GESCHWISTERZUEGE stabil -- oder ist es Rauschen?

PREREG_ownership_coupling.md par.6.3 Stufe 1, Sperre vor B4. Die bekannte
Konjunktions-AUC 0,83-0,91 gilt fuer die Frage, OB ein Feld gefuellt wird. Ob der
Kopf die ZUEGE eines Knotens ordnet, ist damit NICHT belegt -- und genau das
braucht die geplante Ordinalnutzung.

MESSPRINZIP: dieselbe Stellung, ZWEI Determinisierungs-Seeds. Bleibt die
Kandidaten-Ordnung erhalten, traegt sie Signal; kippt sie, war es Rauschen, und
eine Rangtransformation wuerde dieses Rauschen auf VOLLE Staerke heben.

KOPF-ERWARTUNG JE KANDIDAT OHNE NACHBAU: der Trace liefert je Kandidat `q`, aber
nicht `e[k]`. Also wird der Regler auf EIN Kriterium gestellt
(`MOSAIC_OWNERSHIP_GEW`) und je Kandidat `q_an - q_aus` gebildet. Wegen
`shift = gew[k]*tanh(e[k]/50)` ist das streng monoton in `e[k]` -- die ORDNUNG
ist exakt die des Kriteriums, ohne `expected_plate_points` in Python nachzubauen.

ZWEI PROZESSE SIND PFLICHT: `MOSAIC_OWNERSHIP_W` haengt an einem `OnceLock` und
wird EINMAL je Prozess gelesen. Zwei Dosen in einem Prozess fahren still
dieselbe -- der Fehler ist beim ersten Versuch genau so passiert.

    python -X utf8 tools/probes/sibling_order_stability.py --krit 1 --w 0
    python -X utf8 tools/probes/sibling_order_stability.py --krit 1 --w 1.0
    python -X utf8 tools/probes/sibling_order_stability.py --krit 1 --w 1.0 --compare

ZUSATZ (2026-08-20, additiv, PREREG_reachability_target.md par.6 "Ordnung
gegen das Praedikat selbst" -- `tools/probes/sibling_order_vs_predicate.py`):
`--dump-successors` haengt an jeden Kandidaten zusaetzlich seinen
NACHFOLGEZUSTAND (`successor_state_json`, aus dem neuen Trace-Feld
`GumbelPhaseCandidate::successor_state_json`/`mover`, engine/src/net_mcts.rs)
und schreibt EINEN Seed (`--seed-a`) nach `probe_sibling_succ_k{krit}_w{w}.json`
-- eigener Dateiname, bestehende `--compare`/Zwei-Seed-Dumps unveraendert:

    python -X utf8 tools/probes/sibling_order_stability.py --krit 1 --w 1.0 --dump-successors
"""
from __future__ import annotations

import argparse
import glob
import itertools
import json
import os
import pickle
import statistics
from pathlib import Path

BASIS = Path(__file__).resolve().parents[2]


def zustaende(muster, n, phase, krit, je_partie=1, min_runde=1):
    """EINE Stellung je Partie, und nur wo das Kriterium AKTIV ist.

    Der erste Entwurf nahm die ersten n Drafting-Stellungen in Dateireihenfolge.
    Ergebnis: alle 40 kamen aus EINER Partie mit fester Plattenkombination --
    k2 war nie aktiv, und die k1-Statistik war Pseudoreplikation (36
    korrelierte Stellungen statt 36 Stichproben). Deshalb hier: nach game_id
    gruppieren, je Partie hoechstens `je_partie` Stellungen, und
    `scoring_tile_ids` muss das Kriterium enthalten -- sonst ist e[k] fuer ALLE
    Kandidaten 0 und es gibt gar keine Ordnung zu messen."""
    out, gesehen = [], {}
    for f in sorted(glob.glob(muster)):
        try:
            data = pickle.load(open(f, "rb"))
        except Exception:  # noqa: BLE001
            continue
        for s in data:
            st = s.get("state") or {}
            if st.get("phase") != phase:
                continue
            if krit not in (st.get("scoring_tile_ids") or []):
                continue
            # Runde 1 gemessen inert: dort ist q mit und ohne Regler BITGLEICH
            # (40/40 Stellungen, Delta exakt 0). Ursache ungeprueft.
            if (st.get("round") or 0) < min_runde:
                continue
            gid = (f, s.get("game_id"))
            if gesehen.get(gid, 0) >= je_partie:
                continue
            gesehen[gid] = gesehen.get(gid, 0) + 1
            out.append(st)
            if len(out) >= n:
                return out
    return out


def kand_q(res):
    gt = (res if isinstance(res, dict) else json.loads(res)).get("gumbel_trace") or {}
    ph = gt.get("phases") or []
    if not ph:
        return {}
    return {str(c.get("description", i)): float(c.get("q", 0.0))
            for i, c in enumerate(ph[0].get("candidates") or [])}


def kendall(a: dict, b: dict):
    gem = sorted(set(a) & set(b))
    if len(gem) < 3:
        return None
    kon = dis = 0
    for x, y in itertools.combinations(gem, 2):
        s = (a[x] - a[y]) * (b[x] - b[y])
        if s > 0:
            kon += 1
        elif s < 0:
            dis += 1
    return (kon - dis) / (kon + dis) if kon + dis else None


def pfad(krit, w):
    return BASIS / "evaluations" / "artifacts" / f"probe_sibling_k{krit}_w{w}.json"


def succ_pfad(krit, w):
    """Eigener Dateiname fuer `--dump-successors` -- ueberschreibt nie `pfad()`."""
    return BASIS / "evaluations" / "artifacts" / f"probe_sibling_succ_k{krit}_w{w}.json"


def kand_full(res):
    """Wie `kand_q`, aber je Kandidat zusaetzlich `successor_state_json`/`mover`
    (neue Trace-Felder, engine/src/net_mcts.rs::GumbelPhaseCandidate)."""
    gt = (res if isinstance(res, dict) else json.loads(res)).get("gumbel_trace") or {}
    ph = gt.get("phases") or []
    if not ph:
        return {}
    out = {}
    for i, c in enumerate(ph[0].get("candidates") or []):
        out[str(c.get("description", i))] = {
            "q": float(c.get("q", 0.0)),
            "successor_state_json": c.get("successor_state_json"),
            "mover": c.get("mover"),
        }
    return out


def vergleiche(krit, w):
    n0 = json.loads(pfad(krit, 0.0).read_text(encoding="utf-8"))
    n1 = json.loads(pfad(krit, w).read_text(encoding="utf-8"))
    taus, spannen, nk = [], [], []
    for s0, s1 in zip(n0["stellungen"], n1["stellungen"]):
        d = {}
        for seite in ("a", "b"):
            gem = set(s0[seite]) & set(s1[seite])
            d[seite] = {k: s1[seite][k] - s0[seite][k] for k in gem}
        t = kendall(d["a"], d["b"])
        if t is None:
            continue
        taus.append(t)
        spannen.append(max(d["a"].values()) - min(d["a"].values()))
        nk.append(len(set(d["a"]) & set(d["b"])))
    if not taus:
        raise SystemExit("kein verwertbares Paar -- Dumps pruefen")
    m = statistics.mean(taus)
    sd = statistics.pstdev(taus) or 1e-12
    tstat = m / (sd / len(taus) ** 0.5)
    print(f"  {len(taus)} Stellungen, gemeinsame Kandidaten je Stellung {statistics.mean(nk):.1f}")
    print(f"  Kendall-Tau der Ordnung zwischen zwei Seeds: Mittel {m:+.3f}  (std {sd:.3f})")
    print(f"  t gegen 0: {tstat:+.2f}   (einseitig signifikant ab ~1,68)")
    print(f"  numerische Spannweite des Delta je Stellung: {statistics.mean(spannen):.2e}")
    urteil = "TRAEGT SIGNAL" if tstat > 1.68 else "RAUSCHEN -- B4 nicht bauen"
    print()
    print(f"  VORAB-REGEL par.6.3 Stufe 1: {urteil}")
    (BASIS / "evaluations" / "artifacts" / f"probe_sibling_order_k{krit}.json").write_text(json.dumps({
        "kriterium": krit, "n": len(taus), "tau_mittel": m, "t": tstat,
        "spanne_mittel": statistics.mean(spannen), "urteil": urteil,
    }, indent=1, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default="models/alphazero_v21-b18_best.onnx")
    ap.add_argument("--states", default="data/ownership_corpus/selfplay_v21_own_a_*.pkl")
    ap.add_argument("--phase", default="drafting")
    ap.add_argument("--n-states", type=int, default=40)
    ap.add_argument("--sims", type=int, default=400)
    ap.add_argument("--krit", type=int, default=1)
    ap.add_argument("--w", type=float, default=1.0)
    ap.add_argument("--seed-a", type=int, default=11111)
    ap.add_argument("--seed-b", type=int, default=99999)
    ap.add_argument("--min-runde", type=int, default=2, dest="min_runde")
    ap.add_argument("--compare", action="store_true")
    ap.add_argument("--dump-successors", action="store_true", dest="dump_successors",
                     help="zusaetzlich additiv: Nachfolgezustand+mover je Kandidat, EIN "
                          "Seed (--seed-a), eigene Ausgabedatei (siehe Docstring-Zusatz)")
    a = ap.parse_args()

    if a.compare:
        vergleiche(a.krit, a.w)
        return

    gew = ",".join("1.0" if i == a.krit else "0.0" for i in range(8))
    zust = zustaende(str(BASIS / a.states), a.n_states, a.phase, a.krit,
                     je_partie=1, min_runde=a.min_runde)
    print(f"  {len(zust)} Zustaende aus ebenso vielen Partien, k{a.krit} aktiv, "
          f"w={a.w}, Gewichte {gew}")
    if not zust:
        raise SystemExit("keine Zustaende")

    os.environ["MOSAIC_OWNERSHIP_W"] = str(a.w)
    os.environ["MOSAIC_OWNERSHIP_GEW"] = gew
    import mosaic_rust  # noqa: PLC0415 -- erst NACH den Env-Vars

    modell = str(BASIS / a.model)

    if a.dump_successors:
        aus = {"w": a.w, "krit": a.krit, "sims": a.sims, "seed": a.seed_a, "stellungen": []}
        for i, st in enumerate(zust):
            try:
                res = mosaic_rust.net_search_state_json_trace(
                    json.dumps(st), modell, a.sims, 1.5, a.seed_a)
            except Exception as ex:  # noqa: BLE001
                print(f"  Stellung {i}: {ex}")
                continue
            aus["stellungen"].append({"round": st.get("round"), "kandidaten": kand_full(res)})
        succ_pfad(a.krit, a.w).write_text(json.dumps(aus, ensure_ascii=False), encoding="utf-8")
        print(f"  {len(aus['stellungen'])} Stellungen (mit Nachfolgezustaenden) -> "
              f"{succ_pfad(a.krit, a.w).name}")
        return

    aus = {"w": a.w, "krit": a.krit, "sims": a.sims, "stellungen": []}
    for i, st in enumerate(zust):
        e = {}
        for name, seed in (("a", a.seed_a), ("b", a.seed_b)):
            try:
                e[name] = kand_q(mosaic_rust.net_search_state_json_trace(
                    json.dumps(st), modell, a.sims, 1.5, seed))
            except Exception as ex:  # noqa: BLE001
                print(f"  Stellung {i} Seed {name}: {ex}")
        if len(e) == 2:
            aus["stellungen"].append(e)
    pfad(a.krit, a.w).write_text(json.dumps(aus, ensure_ascii=False), encoding="utf-8")
    print(f"  {len(aus['stellungen'])} Stellungen gedumpt -> {pfad(a.krit, a.w).name}")


if __name__ == "__main__":
    main()
