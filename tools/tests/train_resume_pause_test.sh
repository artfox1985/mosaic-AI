#!/usr/bin/env bash
# Funktionstest fuer Zwischenstand je Epoche, --resume und Pause auf Zuruf (train.py).
# Aufruf (Projektordner, Hintergrund, ohne Pipe):  bash tools/tests/train_resume_pause_test.sh
# Mini-Fenster: 12 Dateien aus data/window_v24.txt (6 Val-Pool-Kandidaten, 6 andere), 3 Epochen,
# GPU, rund 2 min. Erzeugt und loescht models/*rtest_*. NICHT neben einer laufenden Messung
# starten (CPU-Nebenlast, working_rules.md "Auslastung").
# Prueft:  A) ununterbrochen  B) simulierter Absturz nach Epoche 1 + --resume  (bitgleich zu A)
#          C) Fingerabdruck-Waechter (falsches Rezept bricht hart ab)
#          D) Pause per Stopp-Datei nach Epoche 1 (Exit 75) + --resume  (bitgleich zu A)
#          E) --fast-loader (batchweises Indizieren, pin_memory)          (bitgleich zu A; Laufzeit im Manifest vergleichen)
set -uo pipefail
cd "$(dirname "$0")/../.."
export PYTHONIOENCODING=utf-8 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2
export MOSAIC_CARRIER_MANIFEST=policy_carrier_manifest_v24.json MOSAIC_IGNORE_POLICY_TARGET_VALID=1 MOSAIC_VAL_POOL='^selfplay_v23-b01-'
LIST="data/window_rtest.txt"
(grep "selfplay_v23-b01-" data/window_v24.txt | head -6; grep -v "selfplay_v23-b01-" data/window_v24.txt | head -6) > "$LIST"
COMMON="--load v23-b01_brierbest --file-list $LIST --encoder 2d --value-target-variant nortv --value-head wdl --ownership-head-2d --ownership-weight 1.0 --endgame-head --opp-points-head --moon-loss-weight 0 --select-by-brier --val-frac 0.1 --epochs 3 --lr 5e-5 --lr-schedule cosine --lr-t-max 3 --seed 20260828 --no-plot --no-snapshot --no-early-stop"
fail=0
echo "== A) ununterbrochen ($(date +%T))"
python -X utf8 -u train.py --name rtest_a $COMMON || fail=1
echo "== B1) simulierter Absturz nach Epoche 1"
MOSAIC_RESUME_TEST_ABORT_AFTER_EPOCH=1 python -X utf8 -u train.py --name rtest_b $COMMON; rc=$?
[ "$rc" = "99" ] || { echo "FEHLER: B1 Exit $rc, erwartet 99"; fail=1; }
echo "== C) Fingerabdruck-Waechter (--epochs 4 gegen Zwischenstand mit 3)"
python -X utf8 -u train.py --name rtest_b ${COMMON/--epochs 3/--epochs 4} --resume; rc=$?
[ "$rc" = "1" ] || { echo "FEHLER: C Exit $rc, erwartet 1"; fail=1; }
echo "== B2) --resume"
python -X utf8 -u train.py --name rtest_b $COMMON --resume || fail=1
[ -f models/alphazero_rtest_b_resume.pth ] && { echo "FEHLER: Zwischenstand b nach Ende nicht geloescht"; fail=1; }
echo "== D1) Pause per Stopp-Datei nach Epoche 1 (Datei vor dem Start anlegen ist verboten, also im Hintergrund nach dem Start)"
( sleep 20; touch models/alphazero_rtest_d.stop ) &
python -X utf8 -u train.py --name rtest_d $COMMON; rc=$?
wait
[ "$rc" = "75" ] || { echo "FEHLER: D1 Exit $rc, erwartet 75"; fail=1; }
[ -f models/alphazero_rtest_d.stop ] && { echo "FEHLER: Stopp-Datei nicht geloescht"; fail=1; }
[ -f models/alphazero_rtest_d_resume.pth ] || { echo "FEHLER: kein Zwischenstand nach Pause"; fail=1; }
echo "== D2) --resume nach Pause"
python -X utf8 -u train.py --name rtest_d $COMMON --resume || fail=1
echo "== E) --fast-loader (batchweises Indizieren) gegen A: Gewichte bitgleich? Epochenzeit?"
python -X utf8 -u train.py --name rtest_e $COMMON --fast-loader || fail=1
echo "== Vergleich A gegen B und D (Gewichte bitgleich?)"
python - <<'PY' || fail=1
import torch, json, glob, sys
a=torch.load('models/alphazero_rtest_a.pth',map_location='cpu',weights_only=False)
ma=json.load(open(sorted(glob.glob('models/manifest_train_rtest_a_*.json'))[-1],encoding='utf-8')); print('rtest_a laufzeit =', ma.get('laufzeit'))
bad=0
for n in ('b','d','e'):
    try:
        x=torch.load(f'models/alphazero_rtest_{n}.pth',map_location='cpu',weights_only=False)
    except Exception as e:
        print(f'FEHLER: rtest_{n} fehlt ({e!r})'); bad=1; continue
    mx=max(float((a['model_state'][k].float()-x['model_state'][k].float()).abs().max())
           for k in a['model_state'] if a['model_state'][k].dtype.is_floating_point)
    m=json.load(open(sorted(glob.glob(f'models/manifest_train_rtest_{n}_*.json'))[-1],encoding='utf-8'))
    print(f"rtest_{n}: epochs {x['epochs']}, max|dW| gegen A = {mx}, fortsetzung = {json.dumps(m.get('fortsetzung'),ensure_ascii=False)}, laufzeit = {m.get('laufzeit')}")
    if mx != 0.0 or x['epochs'] != a['epochs']: bad=1
sys.exit(bad)
PY
rm -f models/*rtest_* "$LIST"
echo "== ERGEBNIS: $([ $fail = 0 ] && echo GRUEN || echo ROT) ($(date +%T))"
exit $fail
