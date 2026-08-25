# -*- coding: utf-8 -*-
"""Wie GROSS ist der Beitrag des Ownership-Reglers an der Wurzelentscheidung?

PREREG_ownership_coupling.md par.6 Punkt 4: "Delta-q je Handlung MESSEN, nicht
rechnen." Die Rechnung in par.3 war eine Herleitung mit einer Annahme (max_N)
und einer FALSCHEN Vergleichsgroesse (Gumbel-Rauschen 1,28) -- in der Arena ist
`add_root_noise=false` und damit `gumbel_scale=0`, es gibt dort gar kein
Rauschen (`net_mcts.rs:3842`). Der richtige Massstab ist die Streuung der
LOG-PRIORS ueber die Kandidaten.

WARUM NICHT NACHBAUEN: `expected_plate_points` in Python zu reimplementieren
waere genau die Divergenz, die die Messung entwerten wuerde. Statt dessen liefert
`net_search_state_json_trace` (Task #95) je Kandidat `q`, `sigma_q` und `score`
aus der Engine selbst. `max_N` kommt damit aus der Messung statt aus einer
Annahme.

MESSPRINZIP: dieselbe Stellung, derselbe Seed, zweimal gesucht -- einmal mit
abgeschaltetem und einmal mit eingeschaltetem Regler. Verglichen wird, wie stark
sich `sigma_q` je Kandidat verschiebt (das ist das eingespeiste Signal) und wie
diese Verschiebung zur Log-Prior-Spreizung derselben Kandidatenmenge steht (das
ist, was sie ueberstimmen muesste).

VORBEHALT (2026-08-18, nach dem ersten Einsatz): diese Sonde vergleicht den
argmax von `q`. GEWAEHLT wird bei Gumbel aber ueber `score = logit + sigma_q` --
ein unveraenderter q-Bestkandidat heisst also NICHT, dass die Entscheidung steht.
Genau dieser Fehlschluss steht als Korrektur in PREREG_ownership_coupling.md
par.6.2. Fuer die Frage "kippen Entscheidungen?" ist der Vergleich der
Draft-Folgen aus den ARENA-LOGS das bessere Instrument (dort: 400/407 Partien
weichen ab, ~17 % Kipp-Rate je Entscheidung). Diese Sonde bleibt nuetzlich fuer
die GROESSE des Reglerbeitrags und fuer max_N, nicht fuer seine Wirksamkeit.

Aufruf:
    python -X utf8 tools/probes/ownership_shift_magnitude.py --n-states 60
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import pickle
import statistics
import sys
from pathlib import Path

BASIS = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASIS / "engine" / "py"))


def sammle_zustaende(muster: str, n: int, phase: str):
    """Zustaende aus Self-Play-Records ziehen, ohne die .pkl komplett zu halten."""
    out = []
    for f in sorted(glob.glob(muster)):
        try:
            data = pickle.load(open(f, "rb"))
        except Exception as e:  # noqa: BLE001 -- eine kaputte Datei darf nicht alles stoppen
            print(f"  uebersprungen {Path(f).name}: {e}")
            continue
        for step in data:
            st = step.get("state") or {}
            if st.get("phase") != phase:
                continue
            out.append(st)
            if len(out) >= n:
                return out
    return out


def kandidaten(trace: dict) -> list[dict]:
    """Erste Phase des Gumbel-Traces = die Top-m-Kandidatenmenge."""
    gt = trace.get("gumbel_trace") or {}
    phasen = gt.get("phases") or gt.get("phasen") or []
    if phasen:
        erste = phasen[0]
        return erste.get("candidates") or erste.get("kandidaten") or []
    return gt.get("candidates") or gt.get("top_m") or []


def spreizung(werte: list[float]) -> tuple[float, float]:
    if len(werte) < 2:
        return 0.0, 0.0
    return max(werte) - min(werte), statistics.pstdev(werte)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default="models/alphazero_v21-b18_best.onnx")
    ap.add_argument("--states", default="data/ownership_corpus/selfplay_v21_own_a_*.pkl")
    ap.add_argument("--phase", default="drafting")
    ap.add_argument("--n-states", type=int, default=60)
    ap.add_argument("--sims", type=int, default=400)
    ap.add_argument("--seed", type=int, default=31415926)
    ap.add_argument("--dose", default="0.1,0.3", help="MOSAIC_OWNERSHIP_W,MOSAIC_OWNERSHIP_TILING_W")
    ap.add_argument("--conj", default="1")
    ap.add_argument("--tag", default="d1", help="Namensteil der Ausgabedatei")
    a = ap.parse_args()

    zust = sammle_zustaende(str(BASIS / a.states), a.n_states, a.phase)
    print(f"  {len(zust)} Zustaende der Phase '{a.phase}' geladen")
    if not zust:
        raise SystemExit("keine Zustaende gefunden -- Muster/Phase pruefen")

    w_own, w_til = a.dose.split(",")
    modell = str(BASIS / a.model)

    # Regler AUS zuerst, dann AN -- beide Male derselbe Seed, dieselbe Stellung.
    laeufe = {}
    for name, env in (("aus", {"MOSAIC_OWNERSHIP_W": "0", "MOSAIC_OWNERSHIP_TILING_W": "0",
                               "MOSAIC_OWNERSHIP_CONJ": "0"}),
                      ("an", {"MOSAIC_OWNERSHIP_W": w_own, "MOSAIC_OWNERSHIP_TILING_W": w_til,
                              "MOSAIC_OWNERSHIP_CONJ": a.conj})):
        for k, v in env.items():
            os.environ[k] = v
        # Der OnceLock-Cache in der Engine liest die Env-Var EINMAL je Prozess.
        # Zwei Konfigurationen in EINEM Prozess wuerden also stillschweigend
        # dieselbe Dosis fahren -- deshalb je Lauf ein eigener Subprozess.
        laeufe[name] = env
    print("  HINWEIS: zwei Konfigurationen brauchen zwei Prozesse (OnceLock-Cache).")
    print("           Dieser Lauf misst nur die Konfiguration aus --dose.")

    import mosaic_rust  # noqa: PLC0415 -- erst NACH dem Setzen der Env-Vars

    zeilen, roh = [], []
    for i, st in enumerate(zust):
        try:
            res = mosaic_rust.net_search_state_json_trace(
                json.dumps(st), modell, a.sims, 1.5, a.seed + i)
        except Exception as e:  # noqa: BLE001
            print(f"  Zustand {i}: {e}")
            continue
        kand = kandidaten(res if isinstance(res, dict) else json.loads(res))
        if len(kand) < 2:
            continue
        q = [float(c.get("q", 0.0)) for c in kand]
        sq = [float(c.get("sigma_q", 0.0)) for c in kand]
        sc = [float(c.get("score", 0.0)) for c in kand]
        # score = logit + gumbel + sigma_q; in der Arena ist gumbel = 0,
        # also logit = score - sigma_q.
        logit = [s - g for s, g in zip(sc, sq)]
        zeilen.append({
            "n_kand": len(kand),
            "sigma_q_spanne": spreizung(sq)[0], "sigma_q_std": spreizung(sq)[1],
            "logit_spanne": spreizung(logit)[0], "logit_std": spreizung(logit)[1],
            "q_spanne": spreizung(q)[0],
            "max_visits": max((int(c.get("visits", 0)) for c in kand), default=0),
        })
        # Pro-Kandidat-Rohwerte fuer den Differenzlauf (Regler aus gegen an).
        # Schluessel ist die Aktion, nicht der Listenindex -- die Top-m-Menge
        # kann sich zwischen den Laeufen umsortieren.
        roh.append({"stellung": i, "q": {
            str(c.get("description", j)): float(c.get("q", 0.0))
            for j, c in enumerate(kand)}})

    if not zeilen:
        raise SystemExit("kein Trace lieferte >= 2 Kandidaten -- Trace-Format pruefen")

    def avg(k):
        return statistics.mean(z[k] for z in zeilen)

    print(f"\n  {len(zeilen)} Stellungen mit >= 2 Kandidaten, Sims {a.sims}")
    print(f"  Kandidaten je Stellung (Mittel): {avg('n_kand'):.1f}")
    print(f"  Spannweite sigma_q ueber die Kandidaten: {avg('sigma_q_spanne'):.4f}"
          f"   (std {avg('sigma_q_std'):.4f})")
    print(f"  Spannweite log-Prior ueber die Kandidaten: {avg('logit_spanne'):.4f}"
          f"   (std {avg('logit_std'):.4f})")
    print(f"  Spannweite q ueber die Kandidaten: {avg('q_spanne'):.4f}")
    print(f"  max_N (gemessen, nicht angenommen): {avg('max_visits'):.1f}")
    verh = avg("sigma_q_spanne") / avg("logit_spanne") if avg("logit_spanne") else float("inf")
    print(f"\n  VERHAELTNIS sigma_q-Spanne zu log-Prior-Spanne: {verh:.2f}")
    print("  Deutung: < 1 heisst, die Suche kann den Prior nicht umsortieren;")
    print("           die Ownership-Anteil DARIN ist noch kleiner (Differenzlauf noetig).")

    ziel = BASIS / "evaluations" / "artifacts" / f"probe_ownership_shift_{a.tag}.json"
    ziel.write_text(json.dumps({
        "model": a.model, "sims": a.sims, "phase": a.phase, "dose": a.dose,
        "conj": a.conj, "n_stellungen": len(zeilen),
        "avg": {k: avg(k) for k in zeilen[0]},
        "verhaeltnis_sigma_zu_logit": verh,
        "roh": roh,
    }, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\n  geschrieben: {ziel}")


if __name__ == "__main__":
    main()
