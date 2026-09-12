#!/usr/bin/env bash
# hv3 = hv2-Verhalten auf dem heutigen Motor mit Phantom-Fix A2 (Nutzer 2026-09-12): Bau-Tore fuer
# den Port und den Aktions-ID-Waechter (tools/night_startslot_build.sh: Lib-Tests, Beispiele, Wheel,
# Anker-Drift, Konservierung, Konventionen), Python-Spiegeltest der Aktions-IDs, dann Einfrieren als
# Artefakt models/frozen_heuristics/hv3_generator (Golden Probe, kein Label-Netz: am Spiel
# entscheidet es nichts, hv2-Manifest), venv, Konservierungspruefung, dann zwei Heuristik-Kanten in
# Bloecken mit Frueh-Stopp: hv3@150 gegen hv4-Anker@150 und hv3@150 gegen hv2@150 (alle c_puct 0,3).
# Exklusiv, nach tools/night_v28_tail8.sh.
# Aufruf: bash tools/night_hv3_freeze_edges.sh   (Hintergrundaufgabe, keine Pipe)
set -u
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
ANCHOR=models/frozen_heuristics/hv4_anchor
HV2=models/frozen_heuristics/hv2_generator
HV3=models/frozen_heuristics/hv3_generator
HEUR="--sims-worker 150 --c-puct-worker 0.3"
bash tools/night_startslot_build.sh; RC=$?; echo "== BAU Exit $RC"; [ $RC -eq 0 ] || { echo "STOPP: Bau rot"; exit 21; }
echo "== Python-Spiegeltest Aktions-IDs $(date +%H:%M:%S)"
python -X utf8 -m unittest tools/tests/test_action_id_mirror.py; echo "   Exit $?"
[ -d "$HV3" ] && { echo "STOPP: $HV3 existiert schon"; exit 22; }
echo "== EINFRIEREN hv3_generator $(date +%F' '%H:%M:%S)"
python -X utf8 -u tools/freeze_heuristic.py --name hv3_generator --variante hv3 \
  --rolle "Huellen-Lehrer hv2 auf dem Motor mit Phantom-Fix A2 (Port 2026-09-12); Leiter-Knoten und Anfaenger-Stufe"
RC=$?; echo "   Exit $RC ($(date +%H:%M:%S))"; [ $RC -eq 0 ] || { echo "STOPP: Einfrieren rot"; exit 23; }
python -X utf8 -u tools/verify_frozen_heuristic.py --artifact-dir "$HV3" --build-venv --venv --out "$ART/frozen_verify_hv3_generator.json"
RC=$?; echo "   Konservierung Exit $RC ($(date +%H:%M:%S))"; [ $RC -eq 0 ] || { echo "STOPP: hv3-Artefakt spielt nicht wie eingefroren"; exit 24; }
edge() {
  local TAG=$1; local SEED=$2; shift 2
  local BLOCK=0
  for OFF in 0 50 100; do
    BLOCK=$((BLOCK+1))
    echo "== KANTE $TAG Block $BLOCK (Seed-Basis $((SEED+OFF))) $(date +%F' '%H:%M:%S)"
    python -X utf8 -u tools/frozen_referee_match.py "$@" --n-games 50 --seed-base $((SEED+OFF)) \
      --workers 6 --force-cross-era --out "$ART/rung_${TAG}_b${BLOCK}.json"
    echo "   Exit $? ($(date +%H:%M:%S))"
    python -X utf8 - "$ART" "$TAG" $BLOCK <<'PY'
import json, sys, math, pathlib
art, tag, nb = pathlib.Path(sys.argv[1]), sys.argv[2], int(sys.argv[3])
wa = wb = 0
for b in range(1, nb + 1):
    d = json.loads((art / f"rung_{tag}_b{b}.json").read_text(encoding="utf-8"))
    wa += d["wins_a"]; wb += d["wins_b"]
n = wa + wb
k = min(wa, wb)
p = min(1.0, 2 * sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n) if n else 1.0
print(f"   gepoolt {tag}: {wa}:{wb} aus {n}, Binomial zweiseitig p={p:.4f}", flush=True)
sys.exit(0 if p < 0.05 else 3)
PY
    if [ $? -eq 0 ]; then echo "   Frueh-Stopp nach Block $BLOCK"; break; fi
  done
}
edge hv3_vs_anchor 924001 --artifact-dir "$ANCHOR" $HEUR --artifact-dir-a "$HV3" --sims-a 150 --c-puct-a 0.3
edge hv3_vs_hv2    925001 --artifact-dir "$HV2" $HEUR --artifact-dir-a "$HV3" --sims-a 150 --c-puct-a 0.3
echo "== HV3 FERTIG $(date +%F' '%H:%M:%S)"
