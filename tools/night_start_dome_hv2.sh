#!/usr/bin/env bash
# Startkuppel Stufe 0, Gegenprobe nach Weg 3 (Nutzer 2026-09-12, PREREG_start_dome_choice.md par.8):
# hv2-Artefakt per Referee mit erzwungenem Startslot gegen lebende hv1. Erst Rauchtest (2 Partien
# je Slot, 2 Worker; prueft Slot-Kontrolle und Umgebungs-Sichtbarkeit), dann voller Lauf
# (20 Partien je Slot, 6 Worker). Exklusiv, nach tools/night_v28_resume_freeze.sh.
# Aufruf: bash tools/night_start_dome_hv2.sh   (Hintergrundaufgabe, keine Pipe)
set -u
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
echo "== RAUCHTEST hv2-Gegenprobe $(date +%F' '%H:%M:%S)"
python -X utf8 -u tools/probes/start_dome_slot_referee_probe.py --n-games 2 --workers 2 \
  --out "$ART/start_dome_slot_referee_probe_smoke.json" --runs-dir "$ART/start_dome_slot_referee_runs_smoke"
RC=$?; echo "   Exit $RC ($(date +%H:%M:%S))"; [ $RC -eq 0 ] || { echo "STOPP: Rauchtest rot"; exit 21; }
python -X utf8 - <<'PY'
import json, sys
d = json.load(open("evaluations/artifacts/start_dome_slot_referee_probe_smoke.json", encoding="utf-8"))
bad = 0
for slot, v in d.get("je_slot", {}).items():
    k = v.get("slot_kontrolle", {})
    print(f"  slot {slot}: n={v.get('n')} treffer={k.get('treffer')} abweichungen={k.get('abweichungen')} {k.get('abweichungen_nach_slot')}", flush=True)
    if k.get("treffer", 0) == 0 and v.get("n", 0) > 0:
        bad += 1
print("  Slots ohne einen einzigen Treffer:", bad, flush=True)
sys.exit(22 if bad else 0)
PY
RC=$?; echo "   Slot-Kontrolle Exit $RC"; [ $RC -eq 0 ] || { echo "STOPP: Erzwingung greift nicht"; exit 22; }
echo "== VOLLER LAUF hv2-Gegenprobe $(date +%F' '%H:%M:%S)"
python -X utf8 -u tools/probes/start_dome_slot_referee_probe.py
echo "   Exit $? ($(date +%H:%M:%S))"
echo "== hv2-GEGENPROBE FERTIG $(date +%F' '%H:%M:%S)"
