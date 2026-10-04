#!/usr/bin/env bash
# v35-Vorbereitung, Kette 1 (PREREG_asymmetric_selfplay.md par.5e/par.5e1, Auftrag 2026-10-04):
# Lib-Suite, --no-run, Wheel bauen und installieren, Anker-Drift und -Konservierung; dann
#   1. par.5e1 Frage 1: `tie_frequency_report` (Gleichstand der tau-Zugwahl, 20 Partien, nur Bericht),
#   2. Vortest policy-s400 (100 Partien @400 Sims nach data/probe_asym, Rezept models/v35_probes2.recipe.json),
#   3. KL-Auswertung policy-s400 gegen policy nach evaluations/artifacts/probe_policy_s400_kl.json,
#   4. par.5e1 Frage 3 (GEAENDERT): Klassen policy-tb1 und policy-tb2 (je 200 Partien, asymmetrisches
#      Self-Play, Stichentscheid auf einer Seite je Partie) und je eine Seitenauswertung nach
#      evaluations/artifacts/tiebreak_side_tb1.json bzw. _tb2.json.
# Jeder rote Schritt stoppt.
#
# Keine gepaarte Arena zu Frage 3: der Knopf `tau_tiebreak_q` wirkt nur im tau-Zweig der Self-Play-Zugwahl
# (self_play.rs net_drafting_policy_with_own_gap); die Arena zieht ueber net_arena_choose_action ->
# net_search_drafting_action und betritt diesen Zweig nie (par.5e1 "GEAENDERT"). Die Specs
# models/v35_generation_tiebreak1/2.spec.json bleiben liegen, werden hier nicht benutzt.
#
# KEINE PIPE hinter einem Lauf, keine eigene Umleitung; als DATEI starten.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
PYDIR="${MOSAIC_PYTHON_DIR:-$(python -c 'import sys,os;print(os.path.dirname(sys.executable))')}"
export PATH="$(cygpath -u "$PYDIR"):$PATH"
STAMP=$(date +%Y%m%d)
RECIPE=models/v35_probes2.recipe.json
step() { echo ""; echo "===== $1 $(date +%F' '%H:%M:%S)"; }
fail() { echo "STOPP: $1"; exit "${2:-10}"; }

. "$(cd "$(dirname "$0")" && pwd)/lib/cpu_free.sh"
wait_for_free_cpu "v35-Vorbereitung Kette 1"

# Vorbedingungen: der Bezug `policy` muss liegen, policy-s400 darf noch nicht liegen.
ls data/probe_asym/selfplay_probe-v35-policy_*.pkl >/dev/null 2>&1 || fail "Bezugsklasse policy fehlt in data/probe_asym" 3
for C in policy-s400 policy-tb1 policy-tb2; do
  if ls data/probe_asym/selfplay_probe-v35-${C}_*.pkl >/dev/null 2>&1; then fail "${C}-Dateien liegen schon" 4; fi
done

step "cargo test --release --lib"
(cd engine && cargo test --release --lib) || fail "Lib-Suite rot" 11
step "cargo test --release --no-run"
(cd engine && cargo test --release --no-run) || fail "--no-run rot" 12
step "Wheel bauen"
(cd engine && python -m maturin build --release) || fail "maturin rot" 13
WHEEL=$(ls -t engine/target/wheels/mosaic_rust-*.whl | head -1)
python -m pip install --force-reinstall --no-deps "$WHEEL" || fail "pip install rot" 14
sha256sum "$WHEEL"
step "Anker-Drift"
python -X utf8 -u tools/verify_frozen_heuristic.py --artifact-dir models/frozen_heuristics/hv4_anchor \
  --out "evaluations/artifacts/anchor_v2_drift_live_wheel_${STAMP}_chain1.json" || fail "Anker-Drift ROT" 15
step "Anker-Konservierung"
python -X utf8 -u tools/verify_frozen_heuristic.py --artifact-dir models/frozen_heuristics/hv4_anchor --venv \
  --out "evaluations/artifacts/anchor_v2_conservation_${STAMP}_chain1.json" || fail "Anker-Konservierung ROT" 16

# par.5e1 Frage 1. Der Test liest `SearchConfig::from_env()`; damit das die Erzeugung beschreibt, setzt
# dieser Schritt die Umgebung, die self_play.py fuer models/v35.recipe.json setzt: die Rezept-Flags
# (self_play.py RECIPE_ENV-Abbildung, u.a. MOSAIC_TAU_ARGMAX_FROM_MOVE=1), den env-Block des Rezepts
# und die von 0 verschiedenen Felder von models/v35_generation.spec.json ueber ihre Env-Namen
# (spec_env.py SPEC_TO_ENV). Ausnahme: `r5_net_sims` 400 hat keinen Env-Knopf, Runde 5 sucht hier mit 100.
step "par.5e1 Frage 1: tie_frequency_report"
(cd engine && env \
  MOSAIC_TAU_ARGMAX_FROM_MOVE=1 MOSAIC_DEVIATE_PROB=1.0 MOSAIC_START_SLOT_RANDOM_P=0.15 \
  MOSAIC_RETURN_ORDER_RANDOM_P=0.81 MOSAIC_TIE_MIRROR_P=0.5 MOSAIC_LABEL_RNG_SPLIT=1 MOSAIC_EXCURSION_RESHUFFLE=1 \
  MOSAIC_STACK_DRAW_RESEARCH=1 MOSAIC_SINGLE_PASS_OTHER_VAL=1 MOSAIC_R5_NET_SOLVER=0 \
  MOSAIC_ENVELOPE_HULL_FORM=2 MOSAIC_ENVELOPE_PROFILE=1.0,0.92,0.67,0.33,0.0 MOSAIC_ENVELOPE_PROJECTED=1 \
  MOSAIC_ENVELOPE_SEARCH_C=1.0 MOSAIC_SCORE_UTILITY_B=20.0 MOSAIC_SPECIAL_ROW6_W=1.0 \
  MOSAIC_START_BY_SEARCH=1 MOSAIC_RETURN_ORDER_MODE=1 \
  cargo test --release --lib tie_frequency_report -- --ignored --nocapture) || fail "tie_frequency_report rot" 17

step "Vortest policy-s400, 100 Partien @400 Sims"
MOSAIC_DATA_DIR=data/probe_asym python -X utf8 -u self_play.py --recipe "$RECIPE" --class policy-s400 \
  || fail "Klasse policy-s400 rot" 18

step "KL-Auswertung policy-s400 gegen policy"
python -X utf8 -u tools/probes/asym_probe_report.py --kl-class policy-s400 \
  --out evaluations/artifacts/probe_policy_s400_kl.json || fail "KL-Auswertung rot" 19

# par.5e1 Frage 3 (GEAENDERT): asymmetrisches Self-Play statt Arena. Je Klasse 200 Partien, eine Seite
# je Partie mit dem Stichentscheid-Modus (Record-Feld tiebreak_side), Auswertung je Klasse.
for TB in 1 2; do
  step "par.5e1 Frage 3: Klasse policy-tb${TB}, 200 Partien"
  if ls data/probe_asym/selfplay_probe-v35-policy-tb${TB}_*.pkl >/dev/null 2>&1; then fail "policy-tb${TB}-Dateien liegen schon" 5; fi
  MOSAIC_DATA_DIR=data/probe_asym python -X utf8 -u self_play.py --recipe "$RECIPE" --class "policy-tb${TB}" \
    || fail "Klasse policy-tb${TB} rot" 20
  step "Auswertung policy-tb${TB}"
  python -X utf8 -u tools/probes/asym_probe_report.py --side-class "policy-tb${TB}" --side-field tiebreak_side \
    --out "evaluations/artifacts/tiebreak_side_tb${TB}.json" || fail "Auswertung policy-tb${TB} rot" 21
done

echo ""
echo "########## v35-Vorbereitung Kette 1 FERTIG $(date +%F' '%H:%M:%S)"
