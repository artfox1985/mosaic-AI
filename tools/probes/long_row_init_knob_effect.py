#!/usr/bin/env python
"""PREREG_long_row_payoff.md par.3/B1, Messkette Schritt 1:
Direktwirkung des Knopfes auf die ENTSCHEIDUNG, ohne neue Partien.

Derselbe feste Satz Korpus-Stellungen, zweimal durchsucht -- einmal mit
`MOSAIC_LONG_ROW_INIT_W` aus (Bestand), einmal an. Gemessen wird der Anteil
der BESUCHE, der auf Aktionen faellt, die eine LEERE lange Reihe (Musterreihe
5/6, Index 4/5) beginnen.

Warum das VOR der Arena steht (par.4): ein Term, der die Zugwahl nicht in die
gewuenschte Richtung bewegt, muss gar nicht erst in eine Arena. Und der
Smoke-Test der Bau-Abnahme zeigt nur, dass sich UEBERHAUPT etwas aendert
(10 von 60 Zugwahlen) -- nicht, dass sich das RICHTIGE aendert.

Instrument: `mosaic_rust.net_search_state_json`. Dessen `SearchConfig` kommt
aus `SearchConfig::from_env()` und wird bei JEDEM Aufruf frisch gelesen (kein
OnceLock-Cache mehr, Welle 1) -- deshalb ist das Umschalten per `os.environ`
zwischen zwei Aufrufen zulaessig und wirksam. Beide Arme laufen mit
IDENTISCHEM Seed je Stellung, der Vergleich ist also gepaart.

Runde 5 ist ausgeschlossen: dort greift der exakte R5-Loeser, die Suche ist
ein anderes Objekt (dieselbe Einschraenkung wie in
`long_row_prior_gate.py`).

NICHT Gegenstand: die Vollendungsquote. Sie ist Pflicht-Kennzahl der
Messkette, braucht aber gespielte Partien und gehoert damit zu Schritt 2.
"""
import glob
import json
import os
import pickle
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "engine" / "py"))

import mosaic_rust as m  # noqa: E402

EVAL = ROOT / "evaluations"
OUT_JSON = EVAL / "long_row_init_knob_effect.json"
MODEL = str(ROOT / "models" / "alphazero_v21_2d_brierbest.onnx")

SIMS = 200
C_PUCT = 1.5
KNOB = "MOSAIC_LONG_ROW_INIT_W"
W_ON = "0.3"
LONG_IDX = (4, 5)
SHORT_IDX = (0, 1, 2)
RNG = np.random.default_rng(20260824)
N_BOOT = 1000


def stratified_sample(files, stride):
    groups = defaultdict(list)
    for f in files:
        mm = re.search(r"selfplay_([a-zA-Z0-9]+)_", Path(f).name)
        groups[mm.group(1) if mm else "?"].append(f)
    out = []
    for gen in sorted(groups):
        out.extend(sorted(groups[gen])[::stride])
    return sorted(out)


def qualify(rec):
    """Leere lange Reihe UND legale Stein-Aktion dorthin -- sonst kann der
    Term per Konstruktion nichts bewegen und die Stellung waere nur
    Verduennung."""
    st = rec.get("state") or {}
    if st.get("phase") != "drafting" or st.get("round") == 5:
        return None
    p = rec.get("player")
    if p is None:
        return None
    pls = st["players"][p]["pattern_lines"]
    leer_lang = {r["index"] for r in pls if r["index"] in LONG_IDX and not r["tiles"]}
    leer_kurz = {r["index"] for r in pls if r["index"] in SHORT_IDX and not r["tiles"]}
    va = rec.get("valid_actions") or []
    if not any(a.get("type") == "stone" and a.get("row") in leer_lang for a in va):
        return None
    return dict(state=st, leer_lang=leer_lang, leer_kurz=leer_kurz,
                runde=st.get("round"), game_id=rec.get("game_id"))


def collect(files, cap, cap_per_file):
    found = []
    for f in files:
        if len(found) >= cap:
            break
        with open(f, "rb") as fh:
            recs = pickle.load(fh)
        n = 0
        for r in recs:
            if n >= cap_per_file or len(found) >= cap:
                break
            q = qualify(r)
            if q:
                found.append(q)
                n += 1
    return found


def search_shares(state_json, seed, leer_lang, leer_kurz):
    """(Anteil Besuche auf Initiierung-lang, auf Initiierung-kurz)."""
    out = m.net_search_state_json(state_json, MODEL, SIMS, C_PUCT, seed)
    d = json.loads(out) if isinstance(out, str) else out
    moves = [mv for mv in d.get("moves", []) if "action" in mv]
    total = sum(mv.get("mcts_visits") or 0 for mv in moves)
    if total <= 0:
        return None, None
    lang = kurz = 0
    for mv in moves:
        a = mv["action"]
        if a.get("type") != "stone":
            continue
        v = mv.get("mcts_visits") or 0
        if a.get("row") in leer_lang:
            lang += v
        elif a.get("row") in leer_kurz:
            kurz += v
    return lang / total, kurz / total


def boot_paired(rows, key_on, key_off, group="game_id"):
    by_g = defaultdict(list)
    for r in rows:
        by_g[r[group]].append(r[key_on] - r[key_off])
    gs = list(by_g)
    if len(gs) < 10:
        return None
    vals = []
    for _ in range(N_BOOT):
        pick = RNG.choice(len(gs), size=len(gs), replace=True)
        flat = [v for i in pick for v in by_g[gs[i]]]
        if flat:
            vals.append(float(np.mean(flat)))
    a = np.array(vals)
    return dict(mean=round(float(a.mean()), 5),
                p2_5=round(float(np.percentile(a, 2.5)), 5),
                p97_5=round(float(np.percentile(a, 97.5)), 5))


def main():
    stride = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    cap = int(sys.argv[2]) if len(sys.argv) > 2 else 150
    cap_per_file = int(sys.argv[3]) if len(sys.argv) > 3 else 10

    files = stratified_sample(sorted(glob.glob(str(ROOT / "data" / "selfplay_*.pkl"))), stride)
    print(f"Scanne {len(files)} Dateien ...", file=sys.stderr)
    found = collect(files, cap, cap_per_file)
    print(f"{len(found)} qualifizierende Stellungen.", file=sys.stderr)
    if len(found) < 20:
        print("zu wenige Stellungen", file=sys.stderr)
        sys.exit(1)

    rows = []
    for i, q in enumerate(found):
        sj = json.dumps(q["state"])
        seed = 771000 + i
        os.environ.pop(KNOB, None)
        off_l, off_k = search_shares(sj, seed, q["leer_lang"], q["leer_kurz"])
        os.environ[KNOB] = W_ON
        on_l, on_k = search_shares(sj, seed, q["leer_lang"], q["leer_kurz"])
        os.environ.pop(KNOB, None)
        if off_l is None or on_l is None:
            continue
        rows.append(dict(runde=q["runde"], game_id=q["game_id"],
                         off_lang=off_l, on_lang=on_l,
                         off_kurz=off_k, on_kurz=on_k))
        if (i + 1) % 25 == 0:
            print(f"  {i+1}/{len(found)} ...", file=sys.stderr)

    def mean(k):
        return round(float(np.mean([r[k] for r in rows])), 5)

    n_hoch = sum(1 for r in rows if r["on_lang"] > r["off_lang"])
    n_runter = sum(1 for r in rows if r["on_lang"] < r["off_lang"])
    n_gleich = len(rows) - n_hoch - n_runter

    result = dict(
        n_stellungen=len(rows), sims=SIMS, w_on=float(W_ON),
        # relativ, nicht absolut: oeffentliches Repo, keine Rechnerstruktur
        model=str(Path(MODEL).relative_to(ROOT).as_posix()),
        anteil_init_lang_aus=mean("off_lang"),
        anteil_init_lang_an=mean("on_lang"),
        delta_lang=round(mean("on_lang") - mean("off_lang"), 5),
        delta_lang_bootstrap_95ci=boot_paired(rows, "on_lang", "off_lang"),
        anteil_init_kurz_aus=mean("off_kurz"),
        anteil_init_kurz_an=mean("on_kurz"),
        delta_kurz=round(mean("on_kurz") - mean("off_kurz"), 5),
        delta_kurz_bootstrap_95ci=boot_paired(rows, "on_kurz", "off_kurz"),
        n_stellungen_lang_hoch=n_hoch, n_stellungen_lang_runter=n_runter,
        n_stellungen_unveraendert=n_gleich,
        je_runde={
            str(rd): dict(
                n=len([r for r in rows if r["runde"] == rd]),
                delta_lang=round(float(np.mean([r["on_lang"] - r["off_lang"]
                                                for r in rows if r["runde"] == rd])), 5),
            )
            for rd in sorted({r["runde"] for r in rows if r["runde"] is not None})
        },
        meta=dict(
            gepaart="identischer Seed je Stellung in beiden Armen",
            nicht_gegenstand="Vollendungsquote -- braucht gespielte Partien, Schritt 2",
            runde5="ausgeschlossen (exakter R5-Loeser, andere Suche)",
        ),
    )
    OUT_JSON.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "je_runde"},
                     indent=2, ensure_ascii=False))
    print("\nje Runde:", json.dumps(result["je_runde"], ensure_ascii=False))
    print(f"\n-> {OUT_JSON}")


if __name__ == "__main__":
    main()
