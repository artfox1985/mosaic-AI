#!/usr/bin/env bash
# Nachtkette nach dem b05-Training (2026-09-05; STATUS Abschnitt 1, Nutzer: "mach weiter im plan"):
#   0) warten: b05-Modell da, kein train.py, keine CPU-Messung (Abnahme b02, CPU-Warteschlange) mehr
#   1) Wheel 744 (mit K3-P2) installieren -- erst jetzt haelt kein Prozess das alte Wheel
#   2) Anker-Drift (tools/verify_frozen_heuristic.py); ROT = Nutzer-Entscheid: Abnahmen werden dann NICHT
#      gefahren (sie wuerden unter einer gedrifteten Engine messen), das b03-Training laeuft trotzdem
#   2b) Mini-Fenster-Test Zwischenstand/resume/Pause/fast-loader (tools/tests, 2 min, GPU und CPU frei)
#   3) config.INPUT_SIZE 744 -> 714 (Nutzer: "lass b03 auf 714"; der Block-Schluessel traegt INPUT_SIZE,
#      der 714er-Monolith 299283d4df61 liegt), Training v24-b03 (b03-Rezept) im HINTERGRUND (GPU),
#      --fast-loader nur, wenn 2b GRUEN war
#   4) parallel auf der CPU: Abnahmen b04, dann b05 (night_v24_acceptance_chain.sh), je danach die
#      Kuppel-Bonus-Sonde auf die Tor-2b-Artefakte
#   5) nach dem b03-Training: config.INPUT_SIZE zurueck auf 744
# Aufruf (Projektordner, Hintergrund, ohne Pipe):  bash tools/night_v24_after_b05_chain.sh
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART="evaluations/artifacts"

procs() {
  powershell -NoProfile -Command "(Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match '$1' -and \$_.Name -match 'python|bash|cargo' }).Count" 2>/dev/null | tr -d '\r'
}

echo "== 0) Warten auf b05-Modell, Ende aller Trainings und der CPU-Messungen ($(date +%H:%M:%S); Deckel 30 h)"
tick=0
while true; do
  t=$(procs 'train\.py'); t=${t:-0}
  m=$(procs 'night_v24_acceptance_chain|cpu_queue_after_b02|self_play\.py|paired_gating|paired_arena|maturin|cargo '); m=${m:-0}
  if [ -f models/alphazero_v24-b05_brierbest.onnx ] && [ "$t" = "0" ] && [ "$m" = "0" ]; then break; fi
  tick=$((tick+1)); [ "$tick" -gt 1800 ] && { echo "STOPP: 30 h ohne Bedingung"; exit 70; }
  [ $((tick % 30)) -eq 0 ] && echo "   warte: b05=$([ -f models/alphazero_v24-b05_brierbest.onnx ] && echo da || echo fehlt), train.py=$t, CPU-Messung=$m ($(date +%H:%M:%S))"
  sleep 60
done
echo "   Bedingung erfuellt $(date +%H:%M:%S)"

echo "== 1) Wheel 744 installieren $(date +%H:%M:%S)"
WHL=$(ls -t engine/target/wheels/mosaic_rust-*.whl | head -1); echo "   Wheel: $WHL ($(stat -c %y "$WHL" | cut -c1-16))"
python -m pip install --force-reinstall --no-deps "$WHL"; rc=$?
echo "   pip Exit $rc"
python -X utf8 - <<'EOF'
import json, mosaic_rust as mr
c = json.loads(mr.engine_config_json())
print("   installiert: input_size", c.get("input_size"), "contract_hash", c.get("contract_hash"), "envelope_slot_w", c.get("envelope_slot_w"))
raise SystemExit(0 if c.get("input_size") == 744 else 71)
EOF
[ $? = 0 ] || { echo "STOPP: Wheel liefert nicht INPUT_SIZE 744"; exit 71; }

echo "== 2) Anker-Drift (hv1_anchor) $(date +%H:%M:%S)"
python -X utf8 -u tools/verify_frozen_heuristic.py --artifact-dir models/frozen_heuristics/hv1_anchor; ANCHOR_RC=$?
if [ "$ANCHOR_RC" = "0" ]; then echo "   Anker GRUEN"; else echo "   ANKER ROT (Exit $ANCHOR_RC) -- Nutzer-Entscheid; Abnahmen b04/b05 werden NICHT gefahren"; fi

echo "== 2b) Mini-Fenster-Test Zwischenstand/resume/Pause/fast-loader $(date +%H:%M:%S)"
bash tools/tests/train_resume_pause_test.sh; TEST_RC=$?
FAST=""; [ "$TEST_RC" = "0" ] && FAST="--fast-loader"
echo "   Test Exit $TEST_RC -> b03 laeuft mit: ${FAST:-Standard-Lader}"

echo "== 3) config.INPUT_SIZE 744 -> 714 und Training v24-b03 (714er-Arm) $(date +%H:%M:%S)"
python -X utf8 - <<'EOF'
from pathlib import Path
p = Path("config.py"); s = p.read_text(encoding="utf-8")
old = "INPUT_SIZE = 744        #"
assert old in s, "config.py: INPUT_SIZE-Zeile nicht wie erwartet"
p.write_text(s.replace(old, "INPUT_SIZE = 714        #", 1), encoding="utf-8")
import importlib, config; importlib.reload(config); print("   config.INPUT_SIZE =", config.INPUT_SIZE)
raise SystemExit(0 if config.INPUT_SIZE == 714 else 72)
EOF
[ $? = 0 ] || { echo "STOPP: config-Wechsel fehlgeschlagen"; exit 72; }
export MOSAIC_CARRIER_MANIFEST=policy_carrier_manifest_v24.json MOSAIC_IGNORE_POLICY_TARGET_VALID=1 MOSAIC_VAL_POOL='^selfplay_v23-b01-'
python -X utf8 -u train.py --name v24-b03 --load v23-b01_brierbest --file-list data/window_v24_b03.txt --encoder 2d --value-target-variant nortv --value-head wdl --ownership-head-2d --ownership-weight 1.0 --endgame-head --opp-points-head --moon-loss-weight 0 --select-by-brier --val-frac 0.05 --epochs 12 --lr 5e-5 --lr-schedule cosine --lr-t-max 12 --seed 20260828 $FAST &
TRAIN_PID=$!
echo "   b03-Training laeuft (PID $TRAIN_PID); bei Abbruch: derselbe Befehl plus --resume (config muss dabei 714 sein)"

if [ "$ANCHOR_RC" = "0" ]; then
  for ARM in b04 b05; do
    echo "== 4) Abnahme $ARM (CPU, parallel zum b03-Training) $(date +%H:%M:%S)"
    bash tools/night_v24_acceptance_chain.sh "$ARM"; rc=$?
    echo "   Abnahme $ARM Exit $rc ($(date +%H:%M:%S))"
    python -X utf8 -u tools/probes/arena_points_probe.py --artifact "$ART/paired_arena_env_v24${ARM}_vs_b01_first_s14.json" "$ART/paired_arena_env_v24${ARM}_vs_b01_second_s14.json" --out "$ART/points_v24${ARM}_vs_b01_s14.json" || echo "   Kuppel-Bonus-Sonde $ARM fehlgeschlagen"
  done
else
  echo "== 4) uebersprungen (Anker ROT)"
fi

echo "== 5) Warten auf das Ende des b03-Trainings $(date +%H:%M:%S)"
wait $TRAIN_PID; TRC=$?
echo "   b03-Training Exit $TRC ($(date +%H:%M:%S))"
python -X utf8 - <<'EOF'
from pathlib import Path
p = Path("config.py"); s = p.read_text(encoding="utf-8")
old = "INPUT_SIZE = 714        #"
assert old in s, "config.py: 714er-Zeile nicht gefunden -- von Hand pruefen"
p.write_text(s.replace(old, "INPUT_SIZE = 744        #", 1), encoding="utf-8")
import importlib, config; importlib.reload(config); print("   config.INPUT_SIZE zurueck auf", config.INPUT_SIZE)
EOF
echo "== NACHTKETTE FERTIG $(date +%H:%M:%S): Anker $([ "$ANCHOR_RC" = "0" ] && echo GRUEN || echo ROT), Test $TEST_RC, b03 $TRC. Abnahme b03 (714!) braucht das 714er-Wheel -- Nutzer-Entscheid, wie gemessen wird."
