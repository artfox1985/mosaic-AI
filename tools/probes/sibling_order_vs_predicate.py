# -*- coding: utf-8 -*-
"""Ordnet der Ownership-Kopf die Geschwisterzuege wie das PRAEDIKAT selbst?

PREREG_reachability_target.md par.6, zweite Offline-Pruefung ("Ordnung gegen
das Praedikat selbst" -- die erste ist die Seed-Stabilitaet aus
`sibling_order_stability.py`, Bezug dort k1 Tau +0,942). Diese Sonde fragt
etwas anderes: stimmt die vom Kopf gelernte ORDNUNG der Geschwisterzuege
ueberhaupt mit der Groesse ueberein, die sein Trainingsziel war -- der
Vorratspuffer/Vollendbarkeit aus `engine/py/reach_target.py`?

DATENLAGE (geprueft, 2026-08-20): `sibling_order_stability.py` speicherte
bisher je Kandidat NUR `q` (Beschreibung -> float), keinen Zustand. Ohne
Nachfolgezustand ist das Praedikat nicht rechenbar -- Kandidatenzuege aus der
Beschreibung ("Kuppel #2 -> (0,2)") zurueckzuparsen waere Rate statt Pruefung.
Deshalb (additiv, siehe Docstring-Zusatz dort) neues Trace-Feld
`GumbelPhaseCandidate::successor_state_json`/`mover`
(engine/src/net_mcts.rs) und ein `--dump-successors`-Modus, der es
mitschreibt. `cargo test --release`: 460/0 gruen nach der Aenderung,
`tools/parity_probe.py` unveraendert (Default-Suchpfad unberuehrt, das Feld
wird nur befuellt, wenn `collect_trace=true` -- Self-Play/Arena rufen immer
mit `trace=None`).

KOPF-ORDNUNG je Kandidat: `q(w=1) - q(w=0)`, Seite "a" (Seed `seed_a`) aus den
BESTEHENDEN Dumps `probe_sibling_k1_w0.0.json`/`probe_sibling_k1_w1.0.json`
(`sibling_order_stability.py`-Docstring: wegen
`shift = gew[k]*tanh(e[k]/50)` streng monoton in `e[k]`, also exakt die
Kriteriums-Ordnung ohne `expected_plate_points`-Nachbau).

PRAEDIKAT-ORDNUNG je Kandidat: Kandidatenzug anwenden (das leistet jetzt der
Nachfolgezustand aus `probe_sibling_succ_k1_w1.0.json`, `--dump-successors`,
seed_a) und auf dem NACHFOLGEZUSTAND fuer den ZIEHENDEN Spieler (`mover`-Feld,
Node::player_who_acted) zwei Skalare rechnen -- beide aus
`mosaic_rust.plate_completability_json`:
  - PUFFER (stetig): Summe der 6 gestauchten Spalten-Puffer
    (`reach_target.reach_buffer_columns`, CAP=12, wie im Arm-P-Trainingsziel).
  - BOOLEAN (Runde >= 3, das eigentliche k1-Trainingsziel dort):
    Zahl vollendbarer Spalten (`reach_target.reach_columns`, Summe von 6
    Booleans).

Kendall-Tau je Stellung zwischen Kopf-Ordnung und je Praedikat-Skalar (gleiche
`kendall()`-Funktion wie `sibling_order_stability.py`, per Import
wiederverwendet -- keine zweite Fassung). Mittel/Std/t gegen 0 je Runde und
gesamt.

VORAUSSETZUNG: `tools/probes/sibling_order_stability.py --krit 1 --w 0` /
`--w 1.0` (bestehend) UND `--w 1.0 --dump-successors` (neu) muessen mit
DENSELBEN Standardparametern gelaufen sein (40 Zustaende, `--phase drafting`,
`--min-runde 2`, `--seed-a 11111`) -- `zustaende()` ist bei gleichem Korpus-
Glob deterministisch, die drei Dumps referenzieren dieselben 40 Stellungen in
derselben Reihenfolge.

    python -X utf8 tools/probes/sibling_order_vs_predicate.py
"""
from __future__ import annotations

import itertools
import json
import statistics
import sys
from pathlib import Path

BASIS = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASIS / "engine" / "py"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from reach_target import reach_buffer_columns, reach_columns  # noqa: E402  -- nach sys.path
from sibling_order_stability import kendall, pfad, succ_pfad  # noqa: E402  -- Wiederverwendung, kein Nachbau


def kopf_ordnung(krit, w_an=1.0, w_aus=0.0, seite="a"):
    """`q(w=1) - q(w=0)` je Stellung, Seite `seite` -- exakt der Docstring-Beweis
    aus `sibling_order_stability.py` (monoton in e[k])."""
    n_aus = json.loads(pfad(krit, w_aus).read_text(encoding="utf-8"))["stellungen"]
    n_an = json.loads(pfad(krit, w_an).read_text(encoding="utf-8"))["stellungen"]
    out = []
    for s_aus, s_an in zip(n_aus, n_an):
        gem = set(s_aus[seite]) & set(s_an[seite])
        out.append({k: s_an[seite][k] - s_aus[seite][k] for k in gem})
    return out


def praedikat_ordnung(krit, w=1.0):
    """Je Stellung: Runde sowie je Kandidat (Puffer-Summe, vollendbare Spalten)
    auf dem NACHFOLGEZUSTAND fuer den ziehenden Spieler (`mover`)."""
    daten = json.loads(succ_pfad(krit, w).read_text(encoding="utf-8"))["stellungen"]
    out = []
    for eintrag in daten:
        rd = eintrag.get("round")
        puffer, boolean = {}, {}
        for desc, kd in eintrag["kandidaten"].items():
            sj = kd.get("successor_state_json")
            mover = kd.get("mover")
            if sj is None or mover is None:
                continue
            succ = json.loads(sj)
            buf = reach_buffer_columns(succ, mover)
            vol = reach_columns(succ, mover)
            if buf is None or vol is None:
                continue
            puffer[desc] = sum(buf)
            boolean[desc] = sum(vol)
        out.append({"round": rd, "puffer": puffer, "boolean": boolean})
    return out


def tau_row(kopf, praed_key, praedikate):
    """Kendall-Tau je Stellung zwischen Kopf-Ordnung und einem Praedikat-Skalar,
    gruppiert nach der Runde der jeweiligen Stellung."""
    zeilen = []
    for k, p in zip(kopf, praedikate):
        gem = sorted(set(k) & set(p[praed_key]))
        if len(gem) < 3:
            continue
        t = kendall(k, p[praed_key])
        if t is None:
            continue
        zeilen.append((p["round"], t, len(gem)))
    return zeilen


def zusammenfassung(zeilen):
    taus = [t for _, t, _ in zeilen]
    if not taus:
        return None
    m = statistics.mean(taus)
    sd = statistics.pstdev(taus) if len(taus) > 1 else 0.0
    denom = (sd / len(taus) ** 0.5) or 1e-12
    tstat = m / denom
    return {"n": len(taus), "tau_mittel": m, "tau_std": sd, "t": tstat}


def main() -> None:
    krit = 1
    kopf = kopf_ordnung(krit)
    praed = praedikat_ordnung(krit)
    if len(kopf) != len(praed):
        raise SystemExit(
            f"Stellungszahl weicht ab (Kopf {len(kopf)} vs Praedikat {len(praed)}) -- "
            "Dumps stammen nicht aus demselben Lauf, siehe Docstring-Voraussetzung.")

    ergebnis = {"kriterium": krit, "je_runde": {}, "gesamt": {}}
    print(f"  {len(kopf)} Stellungen, Kriterium k{krit}\n")

    for praed_key, label in (("puffer", "Puffer-Summe (stetig, CAP=12)"),
                              ("boolean", "vollendbare Spalten (boolesch, Runde>=3-Ziel)")):
        zeilen = tau_row(kopf, praed_key, praed)
        n_konstant = sum(1 for k, p in zip(kopf, praed)
                          if len(set(k) & set(p[praed_key])) >= 3
                          and kendall(k, p[praed_key]) is None)
        print(f"  Praedikat: {label}")
        print("  Runde |  n | gemeins. Kandidaten (Mittel) | Tau Mittel (std) |   t")
        print("  ------+----+------------------------------+-------------------+-------")
        je_runde = {}
        for rd in sorted({r for r, _, _ in zeilen}):
            zr = [(t, nk) for r, t, nk in zeilen if r == rd]
            zs = zusammenfassung([(rd, t, nk) for t, nk in zr])
            nk_mittel = statistics.mean(nk for _, nk in zr)
            je_runde[rd] = zs
            print(f"  {rd:5} | {zs['n']:2} | {nk_mittel:28.1f} | "
                  f"{zs['tau_mittel']:+.3f} ({zs['tau_std']:.3f})   | {zs['t']:+.2f}")
        gesamt = zusammenfassung(zeilen)
        if gesamt is None:
            print(f"  GESAMT|   0 | {'':28} | kein Tau berechenbar -- Praedikat innerhalb "
                  f"JEDER Stellung konstant ({n_konstant}/{len(kopf)} Stellungen ohne Spreizung)\n")
        else:
            print(f"  GESAMT|  {gesamt['n']:2} | {'':28} | "
                  f"{gesamt['tau_mittel']:+.3f} ({gesamt['tau_std']:.3f})   | {gesamt['t']:+.2f}"
                  f"   ({n_konstant} Stellungen ohne Spreizung ausgeschlossen)\n")
        ergebnis["je_runde"][praed_key] = {str(rd): v for rd, v in je_runde.items()}
        ergebnis["gesamt"][praed_key] = gesamt
        ergebnis.setdefault("konstant_ausgeschlossen", {})[praed_key] = n_konstant

    out_path = BASIS / "evaluations" / "probe_sibling_vs_predicate_k1.json"
    out_path.write_text(json.dumps(ergebnis, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"  geschrieben: evaluations/{out_path.name}")


if __name__ == "__main__":
    main()
