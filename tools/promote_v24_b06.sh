#!/usr/bin/env bash
# Champion-Promotion v24-b06_k3p10 (Nutzer 2026-09-06 17:05: "Mach vor dem agenten spiel die Champion
# Promotion lt. Skill"; docs/promotion_checklist.md, Umfang wie am 2026-09-04 fuer v23-b01_k3p10).
# Gating-Kante (Punkt 2) liegt im Register: 117:83 und 202:158 gegen v23-b01_k3p10 (beide SPRT).
# Wartet auf das Ende der b06-Abnahme, dann exklusiv:
#   1) set_champion            3) Anker-Kante n=150 (anchor_arena, Cross-Aera)
#   4) Champion-2-Kante gegen v21_2d_brierbest (Spec alle Knoepfe 0 = k3v_off), Deckel 200 Paare
#   5c) sigma/Prior-Balance    5b) Platt-Fit frozen_v3 und frozen_v1 (Trend)
#   5d) Paritaets-Fixture (cargo test, Python-DLL im PATH)
#   7) Artefakt models/frozen_champions/v24-b06_k3p10/: Modell, Spec, Wheel (sha256), venv, Golden Probe
#      (rund 22 min), Referee-Selbsttest 2 Partien. Manifest, server.py A/B, Elo-Zeilen, STATUS: Koordinator.
# Aufruf (Projektordner, Hintergrund, ohne Pipe):  bash tools/promote_v24_b06.sh
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
NEW="v24-b06_k3p10"; ART="evaluations/artifacts"; DIR="models/frozen_champions/$NEW"
procs() {
  local out
  for _try in 1 2 3; do
    out=$(powershell -NoProfile -Command "(Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match '$1' -and \$_.Name -match 'python|bash|cargo' }).Count" 2>/dev/null | tr -d '\r[:space:]')
    case "$out" in ''|*[!0-9]*) sleep 5 ;; *) echo "$out"; return 0 ;; esac
  done
  echo 999
}
echo "== 0) Warten auf das Ende der b06-Abnahme $(date +%H:%M:%S)"
tick=0
while true; do
  m=$(procs 'night_v24_b06_chai[n]|night_v24_acceptance_chai[n]|paired_gating|paired_arena|self_play\.py|argmax_profile|arena_points_prob[e]'); m=${m:-999}
  [ "$m" = "0" ] && break
  tick=$((tick+1)); [ "$tick" -gt 300 ] && { echo "STOPP: 5 h ohne freie CPU"; exit 65; }
  [ $((tick % 15)) -eq 0 ] && echo "   warte: CPU-Messung=$m ($(date +%H:%M:%S))"
  sleep 60
done
echo "   CPU frei $(date +%H:%M:%S)"
echo "== 1) set_champion $NEW $(date +%H:%M:%S)"; python -X utf8 tools/set_champion.py "$NEW"; echo "   Exit $?"
echo "== 3) Anker-Kante n=150 (Cross-Aera) $(date +%H:%M:%S)"
python -X utf8 -u tools/anchor_arena.py --model models/alphazero_$NEW.onnx --spec models/$NEW.spec.json --n-games 150 --seed-base 900001 --workers 6 --force-cross-era --out "$ART/anchor_arena_$NEW.json"; echo "   Exit $? ($(date +%H:%M:%S))"
echo "== 4) Champion-2-Kante gegen v21_2d_brierbest (Spec alle Knoepfe 0) $(date +%H:%M:%S)"
python -X utf8 -u tools/paired_gating.py --model-a models/alphazero_$NEW.onnx --model-b models/frozen_champions/v21_2d_brierbest/model.onnx --name-a "$NEW" --name-b v21_2d_brierbest --spec-a models/$NEW.spec.json --spec-b models/k3v_off.spec.json --sims 400 --max-pairs 200 --seed 20261011 --no-promote-winner --out "$ART/paired_gating_result_${NEW}_vs_v21_2d_brierbest_s11.json"; echo "   Exit $? ($(date +%H:%M:%S))"
echo "== 5c) sigma/Prior-Balance $(date +%H:%M:%S)"
python -X utf8 -u tools/gumbel_scale_calibration.py --model "$NEW" --sims 400 --n-states 300 --out "$ART/gumbel_scale_calibration_$NEW.json"; echo "   Exit $? ($(date +%H:%M:%S))"
echo "== 5b) Platt-Fit frozen_v3 (Anzeige) und frozen_v1 (Trend) $(date +%H:%M:%S)"
python -X utf8 -u tools/platt_fit.py --models models/alphazero_$NEW.pth --eval-set evaluations/frozen_eval_set_v3.pkl --out "$ART/platt_fit_${NEW}_v3.json"; echo "   Exit $?"
python -X utf8 -u tools/platt_fit.py --models models/alphazero_$NEW.pth --eval-set evaluations/frozen_eval_set.pkl --out "$ART/platt_fit_${NEW}_v1.json"; echo "   Exit $? ($(date +%H:%M:%S))"
echo "== 5d) Paritaets-Fixture $(date +%H:%M:%S)"
PYDIR="${MOSAIC_PYTHON_DIR:-}"; [ -z "$PYDIR" ] && PYDIR="$(python -c 'import sys; print(sys.base_prefix)' 2>/dev/null)"
command -v cygpath >/dev/null 2>&1 && PYDIR="$(cygpath -u "$PYDIR" 2>/dev/null || printf '%s' "$PYDIR")"
ls "$PYDIR"/python3*.dll >/dev/null 2>&1 && export PATH="$PYDIR:$PATH"
( cd engine && MOSAIC_UPDATE_NET_PARITY_FIXTURE=1 cargo test --release net_parity_hash_matches_champion_fixture -- --nocapture ); echo "   Fixture-Update Exit $?"
( cd engine && cargo test --release net_parity_hash_matches_champion_fixture ); echo "   Fixture-Pruefung frisch Exit $? ($(date +%H:%M:%S))"
echo "== 7) Artefakt $DIR $(date +%H:%M:%S)"
mkdir -p "$DIR"
cp models/alphazero_$NEW.onnx "$DIR/model.onnx"; cp models/alphazero_$NEW.pth "$DIR/model.pth"; cp models/$NEW.spec.json "$DIR/spec.json"
WHL=engine/target/wheels/mosaic_rust-0.1.0-cp314-cp314-win_amd64.whl; cp "$WHL" "$DIR/mosaic_rust_k3f_20260906.whl"; sha256sum "$DIR/mosaic_rust_k3f_20260906.whl" | tee "$DIR/wheel.sha256"
python -m venv "$DIR/venv" && "$DIR/venv/Scripts/python.exe" -m pip install --no-deps "$WHL" 2>&1 | grep -v notice | tail -1
"$DIR/venv/Scripts/python.exe" -m pip install onnx numpy 2>&1 | grep -v notice | tail -1
"$DIR/venv/Scripts/python.exe" -X utf8 -c "import mosaic_rust as mr, json; print('   venv-Wheel:', json.loads(mr.engine_config_json()).get('contract_hash'))"
echo "== 7b) Golden Probe (rund 22 min) $(date +%H:%M:%S)"
python -X utf8 -u tools/build_frozen_golden_probe.py --artifact-dir "$DIR" --seed-base 916001; echo "   Exit $? ($(date +%H:%M:%S))"
echo "== FERTIG $(date +%H:%M:%S): Manifest, Referee-Selbsttest, server.py A/B, Elo-Zeilen (Anker, Champion-2), STATUS/History durch den Koordinator."
