#!/usr/bin/env bash
# Promotion v35-b16 (docs/promotion_checklist.md, PREREG_v35_window.md par.20b). VORLAGE: der Nutzer
# hat noch NICHT entschieden (par.20b: "Promotion NUR nach Nutzer-Entscheid"); erst danach starten.
# Muster tools/v34_promotion_chain.sh. Promoviert wird das PAKET der Tor-1-Kante par.20b: Netz
# v35-b16_brierbest plus models/v34-b01_brierbest.spec.json (beidseits dieselbe Spec; Kopie unter
# models/v35-b16_brierbest.spec.json, byte-gleich, sha256 721e08f0...). Tree Reuse NICHT in der Spec.
# Alles CPU, exklusiv, eins nach dem anderen; die Register-Zeilen traegt der Koordinator danach von
# Hand ein (Kommentar braucht das Ergebnis).
#   2r. Replikation der Gating-Kante bis zum Deckel (beide Seeds frueh gestoppt nach 105/120 Paaren,
#       also unter 150, Checkliste Punkt 2); Gegner v34-b01 mit der Artefakt-Spec
#   3.  Anker-Kante hv4_anchor, festes n=50, Worker 150 Sims / c_puct 0,3 AUSDRUECKLICH
#       (Seed-Basis 20262400 wie v34-b01: gleiche Seeds wie beim Vorgaenger)
#   4.  Champion-2-Kante gegen das Artefakt v32-b01, 150 Partien (Seed-Basis 20262500 wie v34-b01)
#   5.  R4 (eingefrorenes Substrat) + R4b, R5, Platt frozen_v3/frozen_v1, sigma/Prior -- gepaart gegen v34-b01
#   7.  Golden Probe, venv, Referee-Selbsttest des neuen Artefakts models/frozen_champions/v35-b16
# NICHT in dieser Kette: tools/set_champion.py (Punkt 1), server.py _DISPLAY_CAL_A/_B (5b), die
# Netz-Paritaets-Fixture (5d, cargo) und die Manifest-Nachtraege golden_probe_note/selftest/preliminary.
# KEINE PIPE, keine eigene Umleitung; als DATEI starten.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
unset MOSAIC_R5_NET_SOLVER MOSAIC_SINGLE_PASS_OTHER_VAL MOSAIC_STACK_DRAW_RESEARCH
ART=evaluations/artifacts
NEW=v35-b16
ONNX=models/alphazero_v35-b16_brierbest.onnx
PTH=models/alphazero_v35-b16_brierbest.pth
SPEC=models/v35-b16_brierbest.spec.json
ARTDIR=models/frozen_champions/v35-b16
WHEEL=mosaic_rust-1.1.0-cp314-cp314-win_amd64.whl
CHAMP=v34-b01                                                    # amtierender Champion (Champion-1)
CHAMP_ONNX=models/alphazero_v34-b01_brierbest.onnx               # byte-gleich Artefakt model.onnx (b9f5e985...)
CHAMP_PTH=models/alphazero_v34-b01_brierbest.pth
CHAMP_SPEC=models/frozen_champions/v34-b01/spec.json             # eingefrorene Spec, byte-gleich $SPEC
CHAMP2_DIR=models/frozen_champions/v32-b01                       # Champion-2 (Vorvorgaenger)
# R5: derselbe API-ONNX wie im Lauf von v34-b01 (r5_value_calibration_v34-b01.json,
# summary.model_path_for_api = models/alphazero_v32-b01_brierbest.onnx), damit die Paarung haelt.
R5_API_ONNX=models/alphazero_v32-b01_brierbest.onnx
R4_STATES=data/frozen_substrates/r4_states_v30-b02-policy_seed20260803_n72.json

for f in "$ONNX" "$PTH" "$SPEC" "$ARTDIR/manifest.json" "$ARTDIR/model.onnx" "$ARTDIR/model.pth" \
         "$ARTDIR/spec.json" "$ARTDIR/wheel.sha256" "$ARTDIR/$WHEEL" "$CHAMP_ONNX" "$CHAMP_PTH" "$CHAMP_SPEC" \
         "$CHAMP2_DIR/manifest.json" "$CHAMP2_DIR/golden_probe.json" "$CHAMP2_DIR/venv/Scripts/python.exe" \
         models/frozen_heuristics/hv4_anchor/manifest.json "$R5_API_ONNX" "$R4_STATES" \
         evaluations/frozen_eval_set_v3.pkl evaluations/frozen_eval_set.pkl; do
  [ -f "$f" ] || { echo "ABBRUCH: $f fehlt"; exit 1; }
done
# Paket-Identitaet: Spec beidseits byte-gleich, Artefakt-Kopien byte-gleich mit den Quellen.
cmp -s "$SPEC" "$CHAMP_SPEC" || { echo "ABBRUCH: $SPEC weicht von $CHAMP_SPEC ab (Kante par.20b lief beidseits mit derselben Spec)"; exit 1; }
cmp -s "$SPEC" "$ARTDIR/spec.json" || { echo "ABBRUCH: $ARTDIR/spec.json weicht von $SPEC ab"; exit 1; }
cmp -s "$ONNX" "$ARTDIR/model.onnx" || { echo "ABBRUCH: $ARTDIR/model.onnx weicht von $ONNX ab"; exit 1; }
cmp -s "$PTH" "$ARTDIR/model.pth" || { echo "ABBRUCH: $ARTDIR/model.pth weicht von $PTH ab"; exit 1; }
# Wheel: Kopie gegen wheel.sha256 UND gegen das live installierte (direct_url.json). Golden Probe und
# Gating laufen auf dem LIVE-Wheel; weicht es ab, ist unklar, worauf das Artefakt geeicht wird.
(cd "$ARTDIR" && sha256sum -c --quiet wheel.sha256) || { echo "ABBRUCH: Wheel-Kopie passt nicht zu $ARTDIR/wheel.sha256"; exit 1; }
WHEEL_SHA=$(cut -d' ' -f1 "$ARTDIR/wheel.sha256")
LIVE_SHA=$(python -c "import importlib.metadata as m, json; print(json.loads(m.distribution('mosaic_rust').read_text('direct_url.json'))['archive_info']['hashes']['sha256'])" | tr -d '\r')
[ "$LIVE_SHA" = "$WHEEL_SHA" ] || { echo "ABBRUCH: live installiertes Wheel $LIVE_SHA != Artefakt-Wheel $WHEEL_SHA"; exit 1; }
echo "   Pruefungen gruen: Spec 721e08f0-Paket, Artefakt-Kopien, Wheel ${WHEEL_SHA:0:8} live = Artefakt"
REPL_OUT="$ART/promotion_${NEW}_vs_${CHAMP}_s20261603_replication.json"
[ -f "$REPL_OUT" ] && { echo "ABBRUCH: $REPL_OUT liegt schon -- wird nicht ueberschrieben"; exit 1; }

. "$(cd "$(dirname "$0")" && pwd)/lib/cpu_free.sh"
BUSY_PATTERN='[s]elf_play\.py|[p]aired_gating|[p]aired_arena|[f]rozen_referee|[b]uild_cache|[w]indow_train_split|[a]rgmax_profile|[t]rain\.py|[e]lo_tracker' \
  wait_for_free_cpu "Promotion v35-b16"
step() { echo ""; echo "===== $1 $(date +%F' '%H:%M:%S)"; }
done_rc() { echo "   Exit $1 ($(date +%H:%M:%S))"; }

step "2r Replikation Gating gegen v34-b01, Seed 20261603, Deckel 200 Paare"
python -X utf8 -u tools/paired_gating.py \
  --model-a "$ONNX" --spec-a "$SPEC" --model-b "$CHAMP_ONNX" \
  --spec-b "$CHAMP_SPEC" --name-a "$NEW" --name-b "$CHAMP" \
  --sims-a 400 --sims-b 400 --c-puct 1.5 --block-size 5 --max-pairs 200 \
  --sprt-alpha 1e-12 --sprt-beta 1e-12 --seed 20261603 --threads 10 --log-games --no-promote-winner --out "$REPL_OUT"
done_rc $?
python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$REPL_OUT"
python -X utf8 -u tools/plate_points_from_arena.py "$REPL_OUT" --block 5 --out "${REPL_OUT%.json}_plate_points.json"
python -X utf8 tools/gating_block_z.py "$REPL_OUT"

step "3 Anker-Kante hv4_anchor, n=50"
python -X utf8 -u tools/frozen_referee_match.py --artifact-dir models/frozen_heuristics/hv4_anchor \
  --model-a "$ONNX" --spec-a "$SPEC" --sims-a 400 --c-puct-a 1.5 --sims-worker 150 --c-puct-worker 0.3 \
  --n-games 50 --seed-base 20262400 --workers 6 --force-cross-era --out "$ART/anchor_${NEW}_vs_hv4_anchor.json"
done_rc $?

step "4 Champion-2-Kante gegen v32-b01, n=150"
python -X utf8 -u tools/frozen_referee_match.py --artifact-dir "$CHAMP2_DIR" \
  --model-a "$ONNX" --spec-a "$SPEC" --sims-a 400 --c-puct-a 1.5 --sims-worker 400 --c-puct-worker 1.5 \
  --n-games 150 --seed-base 20262500 --workers 6 --out "$ART/champion2_${NEW}_vs_v32-b01.json"
done_rc $?

step "5 R4 (eingefrorenes Substrat, gepaart gegen v34-b01)"
R4="$ART/r4_value_calibration_${NEW}_n72.json"
python -X utf8 -u tools/r4_value_calibration.py --models "$PTH" --sims 400 --c-puct 1.5 --n-states 72 \
  --k-refills 16 --states-file "$R4_STATES" \
  --state-seed 20260803 --n-bootstrap 1000 --out "$R4"
done_rc $?
step "5 R4b"
python -X utf8 -u tools/r4b_zone_probe.py --r4b-json "$R4" --model-key "$PTH" --out "$ART/r4b_zone_probe_${NEW}.json"
done_rc $?
step "5 R5 (Kennlinie des Loesers, API-ONNX v32-b01 wie im Lauf von v34-b01)"
python -X utf8 -u tools/r5_value_calibration.py --models "$PTH" \
  --model-path-for-api "$R5_API_ONNX" --out "$ART/r5_value_calibration_${NEW}.json"
done_rc $?
step "5b Platt frozen_v3 und frozen_v1 (beide Modelle)"
python -X utf8 -u tools/platt_fit.py --models "$PTH" "$CHAMP_PTH" \
  --eval-set evaluations/frozen_eval_set_v3.pkl --out "$ART/platt_${NEW}_frozenv3.json"
done_rc $?
python -X utf8 -u tools/platt_fit.py --models "$PTH" "$CHAMP_PTH" \
  --out "$ART/platt_${NEW}_frozenv1.json"
done_rc $?
step "5c sigma/Prior"
python -X utf8 -u tools/gumbel_scale_calibration.py --model v35-b16_brierbest --sims 400 --n-states 300 \
  --out "$ART/gumbel_scale_calibration_${NEW}.json"
done_rc $?

step "7 Golden Probe des Artefakts"
python -X utf8 -u tools/build_frozen_golden_probe.py --artifact-dir "$ARTDIR" --per-round 2 --sims 400 \
  --c-puct 1.5 --seed-base 916001 --probe-seed-base 916101 --max-games 40
done_rc $?
step "7 venv aus der Wheel-Kopie (ohne Netz)"
[ -d "$ARTDIR/venv" ] || python -m venv "$ARTDIR/venv"
"$ARTDIR/venv/Scripts/python.exe" -m pip install --no-index --no-deps "$ARTDIR/$WHEEL"
done_rc $?
step "7 Referee-Selbsttest"
python -X utf8 -u tools/frozen_referee_match.py --artifact-dir "$ARTDIR" --model-a "$ARTDIR/model.onnx" \
  --spec-a "$ARTDIR/spec.json" --n-games 2 --out "$ART/referee_selftest_${NEW}.json"
done_rc $?
echo "########## Promotion v35-b16 Kette FERTIG $(date +%F' '%H:%M:%S)"
