#!/usr/bin/env bash
# Promotion v34-b01 (docs/promotion_checklist.md, Nutzer-Entscheid 2026-10-02, PREREG_v34_window.md
# par.10d). Alles CPU, exklusiv, eins nach dem anderen; die Register-Zeilen traegt der Koordinator
# danach von Hand ein (Kommentar braucht das Ergebnis).
#   2r. Replikation der Gating-Kante bis zum Deckel (Fruehstopp unter 150 Paaren, Checkliste Punkt 2)
#   3.  Anker-Kante hv4_anchor, festes n=50, Worker 150 Sims / c_puct 0,3 AUSDRUECKLICH
#   4.  Champion-2-Kante gegen das Artefakt v31-b01, 150 Partien
#   5.  R4 (eingefrorenes Substrat) + R4b, R5, Platt frozen_v3/frozen_v1, sigma/Prior -- gepaart gegen v32
#   7.  Golden Probe, venv, Referee-Selbsttest des neuen Artefakts
# Die Netz-Paritaets-Fixture (5d, cargo) laeuft danach von Hand.
# KEINE PIPE, keine eigene Umleitung; als DATEI starten.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
unset MOSAIC_R5_NET_SOLVER MOSAIC_SINGLE_PASS_OTHER_VAL MOSAIC_STACK_DRAW_RESEARCH
ART=evaluations/artifacts
NEW=v34-b01
ONNX=models/alphazero_v34-b01_brierbest.onnx
PTH=models/alphazero_v34-b01_brierbest.pth
SPEC=models/v34-b01_brierbest.spec.json
ARTDIR=models/frozen_champions/v34-b01
for f in "$ONNX" "$PTH" "$SPEC" "$ARTDIR/manifest.json" models/alphazero_v32-b01_brierbest.onnx \
         models/frozen_champions/v32-b01/spec.json models/frozen_champions/v31-b01/manifest.json \
         data/frozen_substrates/r4_states_v30-b02-policy_seed20260803_n72.json; do
  [ -f "$f" ] || { echo "ABBRUCH: $f fehlt"; exit 1; }
done
. "$(cd "$(dirname "$0")" && pwd)/lib/cpu_free.sh"
BUSY_PATTERN='[s]elf_play\.py|[p]aired_gating|[p]aired_arena|[f]rozen_referee|[b]uild_cache|[w]indow_train_split|[a]rgmax_profile|[t]rain\.py|[e]lo_tracker' \
  wait_for_free_cpu "Promotion v34-b01"
step() { echo ""; echo "===== $1 $(date +%F' '%H:%M:%S)"; }
done_rc() { echo "   Exit $1 ($(date +%H:%M:%S))"; }

step "2r Replikation Gating gegen v32-b01, Seed 20261603, Deckel 200 Paare"
OUT="$ART/promotion_${NEW}_vs_v32-b01_s20261603_replication.json"
python -X utf8 -u tools/paired_gating.py \
  --model-a "$ONNX" --spec-a "$SPEC" --model-b models/alphazero_v32-b01_brierbest.onnx \
  --spec-b models/frozen_champions/v32-b01/spec.json --name-a "$NEW" --name-b v32-b01 \
  --sims-a 400 --sims-b 400 --c-puct 1.5 --block-size 5 --max-pairs 200 \
  --sprt-alpha 1e-12 --sprt-beta 1e-12 --seed 20261603 --threads 10 --log-games --no-promote-winner --out "$OUT"
done_rc $?
python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT"
python -X utf8 -u tools/plate_points_from_arena.py "$OUT" --block 5 --out "${OUT%.json}_plate_points.json"
python -X utf8 tools/gating_block_z.py "$OUT"

step "3 Anker-Kante hv4_anchor, n=50"
python -X utf8 -u tools/frozen_referee_match.py --artifact-dir models/frozen_heuristics/hv4_anchor \
  --model-a "$ONNX" --spec-a "$SPEC" --sims-a 400 --c-puct-a 1.5 --sims-worker 150 --c-puct-worker 0.3 \
  --n-games 50 --seed-base 20262400 --workers 6 --force-cross-era --out "$ART/anchor_${NEW}_vs_hv4_anchor.json"
done_rc $?

step "4 Champion-2-Kante gegen v31-b01, n=150"
python -X utf8 -u tools/frozen_referee_match.py --artifact-dir models/frozen_champions/v31-b01 \
  --model-a "$ONNX" --spec-a "$SPEC" --sims-a 400 --c-puct-a 1.5 --sims-worker 400 --c-puct-worker 1.5 \
  --n-games 150 --seed-base 20262500 --workers 6 --out "$ART/champion2_${NEW}_vs_v31-b01.json"
done_rc $?

step "5 R4 (eingefrorenes Substrat, gepaart gegen v32-b01)"
R4="$ART/r4_value_calibration_${NEW}_n72.json"
python -X utf8 -u tools/r4_value_calibration.py --models "$PTH" --sims 400 --c-puct 1.5 --n-states 72 \
  --k-refills 16 --states-file data/frozen_substrates/r4_states_v30-b02-policy_seed20260803_n72.json \
  --state-seed 20260803 --n-bootstrap 1000 --out "$R4"
done_rc $?
step "5 R4b"
python -X utf8 -u tools/r4b_zone_probe.py --r4b-json "$R4" --model-key "$PTH" --out "$ART/r4b_zone_probe_${NEW}.json"
done_rc $?
step "5 R5 (Kennlinie des Loesers, API-ONNX v32 wie im Vorgaenger-Lauf)"
python -X utf8 -u tools/r5_value_calibration.py --models "$PTH" \
  --model-path-for-api models/alphazero_v32-b01_brierbest.onnx --out "$ART/r5_value_calibration_${NEW}.json"
done_rc $?
step "5b Platt frozen_v3 und frozen_v1 (beide Modelle)"
python -X utf8 -u tools/platt_fit.py --models "$PTH" models/alphazero_v32-b01_brierbest.pth \
  --eval-set evaluations/frozen_eval_set_v3.pkl --out "$ART/platt_${NEW}_frozenv3.json"
done_rc $?
python -X utf8 -u tools/platt_fit.py --models "$PTH" models/alphazero_v32-b01_brierbest.pth \
  --out "$ART/platt_${NEW}_frozenv1.json"
done_rc $?
step "5c sigma/Prior"
python -X utf8 -u tools/gumbel_scale_calibration.py --model v34-b01_brierbest --sims 400 --n-states 300 \
  --out "$ART/gumbel_scale_calibration_${NEW}.json"
done_rc $?

step "7 Golden Probe des Artefakts"
python -X utf8 -u tools/build_frozen_golden_probe.py --artifact-dir "$ARTDIR" --per-round 2 --sims 400 \
  --c-puct 1.5 --seed-base 916001 --probe-seed-base 916101 --max-games 40
done_rc $?
step "7 venv aus der Wheel-Kopie (ohne Netz)"
[ -d "$ARTDIR/venv" ] || python -m venv "$ARTDIR/venv"
"$ARTDIR/venv/Scripts/python.exe" -m pip install --no-index --no-deps "$ARTDIR/mosaic_rust-1.1.0-cp314-cp314-win_amd64.whl"
done_rc $?
step "7 Referee-Selbsttest"
python -X utf8 -u tools/frozen_referee_match.py --artifact-dir "$ARTDIR" --model-a "$ARTDIR/model.onnx" \
  --spec-a "$ARTDIR/spec.json" --n-games 2 --out "$ART/referee_selftest_${NEW}.json"
done_rc $?
echo "########## Promotion v34-b01 Kette FERTIG $(date +%F' '%H:%M:%S)"
