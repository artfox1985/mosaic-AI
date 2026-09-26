# -*- coding: utf-8 -*-
"""Volle Spalten und Fuellung JE SPALTENINDEX c0..c5, Self-Play-Sockel und Tor-1-Arena v33.

Ad-hoc-Rechnung vom 2026-09-26 (PREREG_tie_mirror.md par.1), in den Baum uebernommen, damit die
Zahlen eine Quelle haben. Aus dem Projektordner aufrufen: python -X utf8 tools/probes/column_by_index_probe.py
Kein Artefakt: die Werte stehen in der Konsolenausgabe (JSON-Ausgabe beim naechsten Einsatz nachruesten).
"""
import glob, json, random, sys, pathlib, math
REPO = pathlib.Path.cwd()
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "tools" / "probes")); sys.path.insert(0, str(REPO / "tools"))
from corpus_io import load_records
from arena_column_probe import _end_state_from_artifact

def summarize(label, fills):
    n = len(fills)
    print(f"{label}: n = {n} Seiten")
    rates = []
    for c in range(6):
        k = sum(1 for cf in fills if len(cf) > c and cf[c] >= 6)
        p = k / n
        rates.append(p)
        print(f"   Spalte c{c}: voll {p:.3f} (+- {1.96*math.sqrt(p*(1-p)/n):.3f})   mittlere Fuellung {sum(cf[c] for cf in fills if len(cf)>c)/n:.2f}/6")
    print(f"   Summe = {sum(rates):.3f} volle Spalten je Seite")

# Self-Play Sockel v33-Erzeugung: 100 Dateien, Seed fest
files = sorted(glob.glob("data/selfplay_v32-b01-policy_*.pkl"))
random.Random(20260926).shuffle(files)
fills = []
for f in files[:100]:
    last = {}
    for r in load_records(f):
        if r.get("winner") is not None:
            last[r.get("game_id")] = r
    for r in last.values():
        for p in r["state"]["players"]:
            fills.append((p.get("score_geo") or {}).get("col_fill") or [])
summarize("SELF-PLAY Sockel v32-b01-policy (100 Dateien)", fills)

for model in ("v33-b01", "v32-b01"):
    fills = []
    for s in ("20261600", "20261601"):
        d = json.load(open(f"evaluations/artifacts/gating_v33-b01_vs_v32-b01_s{s}.json", encoding="utf-8"))
        games = d.get("games") or d.get("game_logs") or []
        for g in games:
            st = _end_state_from_artifact(g)
            if st is None: continue
            names = g.get("side_names") or g.get("names")
            for pi in (0, 1):
                if names[pi] == model:
                    fills.append((st["players"][pi].get("score_geo") or {}).get("col_fill") or [])
    summarize(f"ARENA Tor 1 v33, Seite {model} (2 Seeds)", fills)
