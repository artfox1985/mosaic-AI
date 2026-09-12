#!/usr/bin/env bash
# Elo-Leiter Segment 2, zweite Fassung (2026-09-12, 12:30; ersetzt tools/night_ladder_rungs.sh):
# Teil 0  venv und Referee-Selbsttest fuer die aus dem restic-Repo zurueckgeholten Artefakte
#         models/frozen_champions/v24-b07 (Snapshot bfbe80b1) und v21_2d_brierbest (55623af8);
#         pip lehnt umbenannte Wheel-Dateinamen ab, deshalb Kopie unter kanonischem Namen.
# Teil A  drei Anker-Kanten KORREKT (Anker @150, c_puct 0,3; festes n=150, Seed-Basis 900001).
#         Anlass: tools/night_reanchor.sh lief ohne diese Parameter (Anker @400/1,5), Zeilen
#         in archive/elo_history_segment2_anchor_mislabelled.csv.
# Teil B  Zwischenstufen in ~100-Elo-Schritten (Nutzer: Anker-Kanten gesaettigt, Segment 1:
#         hv2 1100, v21 1190, v24-b07 1283, v26 1364): Bloecke zu 50 Partien mit eigener
#         Seed-Basis, Frueh-Stopp bei zweiseitigem Binomialtest p < 0,05 der gepoolten Bloecke
#         (Nutzer: kein Champion-Tor), spaetestens 150. Heuristik-Seiten @150/0,3, Netze @400/1,5.
# Alle Artefakt-Kanten Cross-Aera per --force-cross-era. Exklusiv.
# Aufruf: bash tools/night_ladder_rungs2.sh   (Hintergrundaufgabe, keine Pipe)
set -u
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
ANCHOR=models/frozen_heuristics/hv1_anchor_v2
HV2=models/frozen_heuristics/hv2_generator
V21=models/frozen_champions/v21_2d_brierbest
V24=models/frozen_champions/v24-b07
V26=models/frozen_champions/v26-b01
SPEC=models/frozen_champions/v27-b01/spec.json
HEUR="--sims-worker 150 --c-puct-worker 0.3"
NETW="--sims-worker 400 --c-puct-worker 1.5"

build_venv() {  # <artefakt-dir> <wheel-datei>
  local D=$1; local W=$2
  if [ -x "$D/venv/Scripts/python.exe" ]; then echo "   venv vorhanden: $D"; return 0; fi
  echo "== venv fuer $D aus $W $(date +%H:%M:%S)"
  cp "$D/$W" "$D/mosaic_rust-0.1.0-cp314-cp314-win_amd64.whl"
  python -m venv "$D/venv" && "$D/venv/Scripts/python.exe" -m pip install --no-deps "$D/mosaic_rust-0.1.0-cp314-cp314-win_amd64.whl" \
    && "$D/venv/Scripts/python.exe" -m pip install numpy onnxruntime
  local RC=$?
  rm -f "$D/mosaic_rust-0.1.0-cp314-cp314-win_amd64.whl"
  "$D/venv/Scripts/python.exe" -c "import mosaic_rust, json; print('venv-Import ok', json.loads(mosaic_rust.engine_config_json()).get('contract_hash'))"
  echo "   venv Exit $RC ($(date +%H:%M:%S))"; return $RC
}

echo "== TEIL 0: Artefakte aus dem Backup betriebsbereit machen $(date +%F' '%H:%M:%S)"
build_venv "$V24" mosaic_rust_wegb_temp2_20260907.whl || { echo "STOPP: venv v24-b07"; exit 11; }
build_venv "$V21" mosaic_rust_searchconfig_wave1_20260823.whl || { echo "STOPP: venv v21"; exit 12; }
for A in "$V24" "$V21"; do
  echo "== Referee-Selbsttest $A (2 Partien, Cross-Aera) $(date +%H:%M:%S)"
  python -X utf8 -u tools/frozen_referee_match.py --artifact-dir "$A" --model-a "$A/model.onnx" --spec-a "$A/spec.json" \
    --sims-a 400 --c-puct-a 1.5 $NETW --n-games 2 --force-cross-era --out "$ART/referee_selftest_$(basename "$A")_restored.json"
  RC=$?; echo "   Exit $RC ($(date +%H:%M:%S))"; [ $RC -eq 0 ] || { echo "STOPP: Selbsttest $A rot"; exit 13; }
done

echo "== TEIL A: Anker-Kanten korrekt (n=150 fest, Anker @150 c_puct 0,3) $(date +%F' '%H:%M:%S)"
for CAND in v28-b02 v28-b01 v27-b01; do
  echo "== ANKER-KANTE $CAND@400 gegen hv1_anchor_v2@150 $(date +%H:%M:%S)"
  python -X utf8 -u tools/frozen_referee_match.py --artifact-dir "$ANCHOR" \
    --model-a "models/alphazero_${CAND}_brierbest.onnx" --spec-a "$SPEC" --sims-a 400 --c-puct-a 1.5 $HEUR \
    --n-games 150 --seed-base 900001 --workers 6 --out "$ART/anchor_v2_arena_${CAND}_c03.json"
  echo "   Exit $? ($(date +%H:%M:%S))"
done

edge() {  # <tag> <seed-base> <referee-args...>
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

echo "== TEIL B: Zwischenstufen $(date +%F' '%H:%M:%S)"
edge hv2_vs_anchor   910001 --artifact-dir "$ANCHOR" $HEUR --artifact-dir-a "$HV2" --sims-a 150 --c-puct-a 0.3
edge v21_vs_hv2      911001 --artifact-dir "$HV2" $HEUR --artifact-dir-a "$V21" --sims-a 400 --c-puct-a 1.5
edge v24_vs_v21      912001 --artifact-dir "$V21" $NETW --artifact-dir-a "$V24" --sims-a 400 --c-puct-a 1.5
edge v26_vs_v24      913001 --artifact-dir "$V24" $NETW --artifact-dir-a "$V26" --sims-a 400 --c-puct-a 1.5
edge v27_vs_v24      914001 --artifact-dir "$V24" $NETW --model-a models/alphazero_v27-b01_brierbest.onnx --spec-a "$SPEC" --sims-a 400 --c-puct-a 1.5
edge v28b02_vs_v24   915001 --artifact-dir "$V24" $NETW --model-a models/alphazero_v28-b02_brierbest.onnx --spec-a "$SPEC" --sims-a 400 --c-puct-a 1.5
edge v21_vs_anchor   916001 --artifact-dir "$ANCHOR" $HEUR --artifact-dir-a "$V21" --sims-a 400 --c-puct-a 1.5
edge v24_vs_hv2      917001 --artifact-dir "$HV2" $HEUR --artifact-dir-a "$V24" --sims-a 400 --c-puct-a 1.5
edge v26_vs_hv2      918001 --artifact-dir "$HV2" $HEUR --artifact-dir-a "$V26" --sims-a 400 --c-puct-a 1.5
echo "== LEITER FERTIG $(date +%F' '%H:%M:%S)"
