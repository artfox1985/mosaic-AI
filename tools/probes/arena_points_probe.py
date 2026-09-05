# -*- coding: utf-8 -*-
"""Punktbilanz je Seite aus den Partie-Logs eines Arena-Artefakts (`--log-games`),
nach Runde und Kategorie -- Kuppel-Bonus je Partie als Abnahme-Kennzahl
(PREREG_geometric_envelope.md par.8.10/8.11, Nutzer 2026-09-05: der Abstand zum
Menschen sitzt beim Kuppel-Bonus und der Endwertung, nicht bei den
Platzierungspunkten).

Schwester von `server_log_points_probe.py` (dort Server-Logs Mensch gegen KI,
Namen 'Spieler 1'/'KI'); hier `paired_arena_env_ab.py`-Artefakte, in denen beide
Seiten 'NetzA'/'NetzB' heissen: NetzA = Brett 0 = `model`/`spec_a`, NetzB =
Brett 1 = `model_b`/`spec_b` (self_play.rs: names[0] = "NetzA"). Gezaehlt je
Seite und Runde: Tiling-Punkte (🎯), Kuppel-Bonus (⭐ Spezial-Punkte), Strafe,
Ziehkosten (📦), Startspielerstein (❖); dazu Endwertung gesamt und nach
Kategorie (Zeilen der Aufschluesselung) und der Endstand aus `scores`.

Aufruf:
    python -X utf8 -u tools/probes/arena_points_probe.py \
        --artifact evaluations/artifacts/paired_arena_env_<name>.json [weitere ...] \
        --out evaluations/artifacts/points_<name>.json
Mehrere Artefakte (z.B. beide Richtungen eines Tor-2b-Paars) werden je Datei UND
gepoolt ausgewiesen; die Zuordnung NetzA/NetzB zum Modell steht je Datei dabei.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
from collections import defaultdict

NAME = r"(?P<name>[^:]+?)"
PATTERNS = {
    "tiling": (re.compile(rf"^\[R(?P<r>\d)\] 🎯 {NAME}: \+(?P<v>\d+) Pkt \(Reihe"), +1),
    "kuppelbonus": (re.compile(rf"^\[R(?P<r>\d)\] ⭐ {NAME}: \+(?P<v>\d+) Spezial-Punkte"), +1),
    "strafe": (re.compile(rf"^\[R(?P<r>\d)\] {NAME}: Strafe -(?P<v>\d+) Pkt"), -1),
    "ziehen": (re.compile(rf"^\[R(?P<r>\d)\] 📦 {NAME}: .*−(?P<v>\d+) Pkt"), -1),
    "marker": (re.compile(rf"^\[R(?P<r>\d)\] ❖ {NAME}: Startspielerstein genommen \(−(?P<v>\d+) Pkt"), -1),
}
END = re.compile(rf"^\[R5\] 🏆 {NAME}: Endwertung (?P<v>-?\d+) Pkt → Gesamt: (?P<g>\d+) Pkt")
END_CAT = re.compile(r"^\[R5\]\s+(?P<cat>\S+ [^:]+): (?P<v>-?\d+) Pkt")


def games_of(artifact: dict) -> list[dict]:
    g = artifact.get("games") or {}
    out = []
    for arm, lst in (g.items() if isinstance(g, dict) else [("", g)]):
        for sp in lst:
            out.append(sp)
    return out


def tally(games: list[dict]) -> dict:
    """Summen je Name (NetzA/NetzB) ueber alle Partien mit Endwertung."""
    agg = defaultdict(lambda: defaultdict(float))
    endcat = defaultdict(lambda: defaultdict(float))
    finals = defaultdict(list)
    n = 0
    for sp in games:
        log = sp.get("log") or []
        if not any("Endwertung" in l for l in log):
            continue
        n += 1
        names = sp.get("names") or ["NetzA", "NetzB"]
        scores = sp.get("scores") or [None, None]
        for who, sc in zip(names, scores):
            if sc is not None:
                finals[who].append(sc)
        current = None
        for l in log:
            if l.startswith("#"):
                continue  # Maschinenzeilen (`#a {...}`), wie analyze_game_log.load_log
            hit = False
            for key, (pat, sign) in PATTERNS.items():
                m = pat.match(l)
                if m:
                    agg[m.group("name")][f"R{m.group('r')} {key}"] += sign * int(m.group("v"))
                    hit = True
                    break
            if hit:
                continue
            m = END.match(l)
            if m:
                agg[m.group("name")]["Endwertung"] += int(m.group("v"))
                current = m.group("name")
                continue
            m = END_CAT.match(l)
            if m and current:
                endcat[current][m.group("cat")] += int(m.group("v"))
    return {"n": n, "agg": agg, "endcat": endcat, "finals": finals}


def summarize(t: dict) -> dict:
    n = t["n"]
    out = {"partien": n, "seiten": {}}
    if n == 0:
        return out
    for who in sorted(t["agg"].keys() | t["finals"].keys()):
        d = t["agg"][who]
        fin = t["finals"][who]
        rows = {}
        cum = 0.0
        for r in range(1, 6):
            vals = {k: d.get(f"R{r} {k}", 0.0) / n for k in PATTERNS}
            net = sum(vals.values())
            cum += net
            rows[f"R{r}"] = {**{k: round(v, 2) for k, v in vals.items()}, "netto": round(net, 2), "kumuliert": round(cum, 2)}
        out["seiten"][who] = {
            "endstand_mittel": round(sum(fin) / len(fin), 2) if fin else None,
            "je_runde": rows,
            "tiling_gesamt": round(sum(d.get(f"R{r} tiling", 0.0) for r in range(1, 6)) / n, 2),
            "kuppelbonus_gesamt": round(sum(d.get(f"R{r} kuppelbonus", 0.0) for r in range(1, 6)) / n, 2),
            "strafe_gesamt": round(sum(d.get(f"R{r} strafe", 0.0) for r in range(1, 6)) / n, 2),
            "endwertung_mittel": round(d.get("Endwertung", 0.0) / n, 2),
            "endwertung_nach_kategorie": {k: round(v / n, 2) for k, v in t["endcat"][who].items()},
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--artifact", nargs="+", required=True, help="paired_arena_env_*.json (eins oder mehrere)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    t0 = time.time()
    out = {"prereg": "PREREG_geometric_envelope.md par.8.10/8.11 (Kuppel-Bonus je Partie als Abnahme-Kennzahl)",
           "dateien": [], "gepoolt": None}
    pooled: list[dict] = []
    for path in a.artifact:
        art = json.load(open(path, encoding="utf-8"))
        games = games_of(art)
        s = summarize(tally(games))
        s["zuordnung"] = {"NetzA": {"model": art.get("model"), "spec": art.get("spec_a")},
                          "NetzB": {"model": art.get("model_b"), "spec": art.get("spec_b")}}
        s["artefakt"] = path
        out["dateien"].append(s)
        pooled.extend(games)
        print(f"{os.path.basename(path)}: {s['partien']} Partien")
        for who, side in s["seiten"].items():
            print(f"   {who}: Endstand {side['endstand_mittel']} | Tiling {side['tiling_gesamt']} | "
                  f"Kuppelbonus {side['kuppelbonus_gesamt']} | Strafe {side['strafe_gesamt']} | "
                  f"Endwertung {side['endwertung_mittel']} {side['endwertung_nach_kategorie']}")
    if len(a.artifact) > 1:
        out["gepoolt"] = summarize(tally(pooled))
        out["gepoolt"]["hinweis"] = ("Pooling nach NAME: nur sinnvoll, wenn NetzA in allen Dateien dasselbe "
                                     "Modell ist (bei beiden Richtungen eines Paars NICHT der Fall -- dann je Datei lesen)")
    out["laufzeit"] = {"wanduhr_s": round(time.time() - t0, 2), "cpu_s": round(time.process_time(), 2), "threads": 1}
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print(f"Artefakt: {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
