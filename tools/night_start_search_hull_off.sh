#!/usr/bin/env bash
# Welcher Term treibt die Such-Start-Praeferenz fuer (2,0)? (Nutzer 2026-09-12, 18:25; PREREG_start_dome_choice.md
# par.9e). Instrument: v28-b02 am argmax-Instrument (200 Partien @400 deterministisch, Seed 20260931, wie C2)
# mit Such-Start UND Huelle AUS (models/start_by_search_on_k3v_off.spec.json) gegen den vorhandenen Lauf
# mit Such-Start und Huelle AN (aus dem A/B, Logs) ist nicht paarbar; deshalb hier ZWEI Instrument-Laeufe
# gleichen Seeds: Such-Start mit Huelle (start_by_search_on.spec.json) und Such-Start ohne Huelle.
# Zielgroesse: Slotverteilung der Startsetzungen je Lauf (START_TILE-Zeilen in den Records/Logs) plus
# volle Spalten/Punkte aus corpus_sanity_check. Exklusiv, nach tools/night_v28_tail9.sh.
# Aufruf: bash tools/night_start_search_hull_off.sh   (Hintergrundaufgabe, keine Pipe)
set -u
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
export MOSAIC_STACK_DRAW_RESEARCH=1
ART=evaluations/artifacts
for PAIR in "startsearch-hull:models/start_by_search_on.spec.json" "startsearch-nohull:models/start_by_search_on_k3v_off.spec.json"; do
  TAG=${PAIR%%:*}; SPEC=${PAIR#*:}; RUN="c2-v28b02-${TAG}"
  echo "== argmax-Instrument $RUN (Spec $SPEC) $(date +%F' '%H:%M:%S)"
  python -X utf8 -u self_play.py --mode network --model models/alphazero_v28-b02_brierbest.onnx \
    --spec "$SPEC" --games 100 --sims 400 --version "$RUN" --threads 11 --chunk 10 \
    --seed 20260931 --per-file 10 --no-root-noise --deterministic
  echo "   Exit $? ($(date +%H:%M:%S))"
  python -X utf8 tools/corpus_sanity_check.py data --pattern "selfplay_${RUN}_*.pkl" --out "$ART/${RUN//-/_}.json"
  echo "   sanity Exit $? ($(date +%H:%M:%S))"
done
echo "== Slotverteilung der Startsetzungen je Lauf $(date +%H:%M:%S)"
python -X utf8 - <<'PY'
import glob, sys, collections, json
sys.path.insert(0, ".")
from corpus_io import load_records
out = {}
for tag in ("startsearch-hull", "startsearch-nohull"):
    c = collections.Counter(); n = 0; by_search = 0
    for f in sorted(glob.glob(f"data/selfplay_c2-v28b02-{tag}_*.pkl")):
        for r in load_records(f):
            if not isinstance(r, dict): continue
            pol = r.get("policy") or []
            best = max(pol, key=lambda e: e.get("prob", 0.0)) if pol else None
            a = (best or {}).get("action") or {}
            if isinstance(a, dict) and a.get("is_start"):
                c[(a.get("slot_row"), a.get("slot_col"))] += 1; n += 1
                by_search += 1 if r.get("start_by_search") else 0
    out[tag] = {"n": n, "start_by_search_records": by_search, "slots": {f"{k[0]},{k[1]}": v for k, v in c.items()}}
    print(f"  {tag}: n={n} start_by_search={by_search} slots={dict(c)}", flush=True)
json.dump(out, open("evaluations/artifacts/start_search_hull_off_slots.json", "w", encoding="utf-8"), indent=2)
PY
echo "== SUCH-START HUELLE-AUS FERTIG $(date +%F' '%H:%M:%S)"
