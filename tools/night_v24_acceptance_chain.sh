#!/usr/bin/env bash
# Abnahme eines v24-Trainingsarms (docs/generation_loop.md Tor 1, 2a, 2b; PREREG_v24_window.md par.6e/par.8).
# Aufruf (Projektordner, Hintergrund, ohne Pipe):  bash tools/night_v24_acceptance_chain.sh b01
# Wartet, bis models/alphazero_v24-<ARM>_brierbest.onnx existiert UND drei Minuten lang kein Self-Play-
# und kein Cache-Bau-Prozess laeuft (die Kette b03 belegt die CPU nach dem b01-Trainingsstart mit
# Seeding-Schwarm, Bloecken und Monolith); ein GPU-Training darf parallel laufen (working_rules.md).
# Beide Seiten spielen dieselbe Spec (Champion-Spec models/v23-b01_k3p10.spec.json, Knopf an),
# sonst misst die Kante den Knopf statt das Netz (v24-Prereg par.6e, berichtigt 2026-09-04).
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ARM="${1:-b01}"
NEW="models/alphazero_v24-${ARM}_brierbest.onnx"
REF="models/alphazero_v23-b01_brierbest.onnx"
SPEC="models/v23-b01_k3p10.spec.json"
ART="evaluations/artifacts"

procs() {
  powershell -NoProfile -Command "(Get-CimInstance Win32_Process | Where-Object { \$_.Name -eq 'python.exe' -and \$_.CommandLine -match '$1' }).Count" 2>/dev/null | tr -d '\r'
}

echo "== 0) Warten auf $NEW und eine freie CPU ($(date +%H:%M:%S); Deckel 30 h)"
quiet=0; tick=0
while true; do
  sp=$(procs 'self_play\.py'); sp=${sp:-0}
  cb=$(procs 'build_cache_incremental'); cb=${cb:-0}
  if [ -f "$NEW" ] && [ "$sp" = "0" ] && [ "$cb" = "0" ]; then quiet=$((quiet+1)); else quiet=0; fi
  [ "$quiet" -ge 3 ] && break
  tick=$((tick+1)); [ "$tick" -gt 1800 ] && { echo "STOPP: nach 30 h keine Abnahme-Bedingung"; exit 30; }
  [ $((tick % 30)) -eq 0 ] && echo "   warte: modell=$([ -f "$NEW" ] && echo da || echo fehlt), self_play=$sp, cache=$cb ($(date +%H:%M:%S))"
  sleep 60
done
echo "   Abnahme $ARM beginnt $(date +%H:%M:%S)"
# Encoder-Waechter (Sicht-Arm, PREREG_stack_top_feature.md par.10): ein Modell mit 744
# Flachwerten braucht das Wheel mit INPUT_SIZE 744 -- ein 714er-Wheel wuerde es NICHT
# kuerzen, sondern die Eingabe zu kurz liefern (nur kuerzen, nie auffuellen).
python - "$NEW" <<'EOF'
import json, sys, onnx
import mosaic_rust as mr
m = onnx.load(sys.argv[1])
dims = [i for i in m.graph.input]
flat = None
for i in dims:
    shape = [d.dim_value for d in i.type.tensor_type.shape.dim]
    if len(shape) == 2:
        flat = shape[1]
eng = json.loads(mr.engine_config_json()).get("input_size")
print(f"Modell-Flachbreite {flat}, Engine INPUT_SIZE {eng}")
if flat is not None and eng is not None and flat > eng:
    raise SystemExit(f"STOPP: Modell verlangt {flat} Flachwerte, installiertes Wheel liefert {eng} -- Wheel installieren, dann Abnahme neu starten")
EOF

echo "== 1a) Tor 2a OHNE Knopf (par.9b: trennt Netz von Knopf-Wechselwirkung; Bezug b01 ohne Knopf 0,510 / v24-b01 0,518)"
bash tools/argmax_profile.sh "tor2a-v24${ARM}nk" "$NEW"
python - "$ARM" <<'EOF'
import json,sys
arm=sys.argv[1]
a=json.load(open(f'evaluations/artifacts/tor2a_v24{arm}nk.json',encoding='utf-8'))['arme'][0]
print(f"TOR 2a OHNE KNOPF v24-{arm}: volle Spalten {a['sp_voll']:.4f} (KI +-{a['sp_voll_ci']:.4f}), Punkte {a['punkte']:.2f}, Zeilen {a['zeilen_voll']:.4f} -- Bezug b01 ohne Knopf 0,510")
EOF

echo "== 1b) Tor 1 OHNE Knopf (beide Seiten k3v_off; par.9b), Deckel 200 Paare, keine Promotion"
python -X utf8 -u tools/paired_gating.py --model-a "$NEW" --model-b "$REF" --name-a "v24-${ARM}" --name-b "v23-b01_brierbest" --spec-a models/k3v_off.spec.json --spec-b models/k3v_off.spec.json --sims 400 --max-pairs 200 --seed 20261016 --no-promote-winner --out "$ART/paired_gating_result_v24-${ARM}_vs_v23-b01_noknob_s16.json"
python - "$ARM" <<'EOF'
import json,sys
arm=sys.argv[1]
d=json.load(open(f'evaluations/artifacts/paired_gating_result_v24-{arm}_vs_v23-b01_noknob_s16.json',encoding='utf-8'))
print(f"TOR 1 OHNE KNOPF (Seed 20261016): {d['a_wins_total']}:{d['b_wins_total']} nach {d['done_pairs']} Paaren, SPRT {d['sprt_verdict']}, McNemar p {d['report_mcnemar_p']:.4f}, Diff {d['mean_pair_diff']:+.2f}, Punkte {d['avg_score_a']:.1f} gegen {d['avg_score_b']:.1f}")
EOF

echo "== 1) Tor 2a: argmax-Instrument @400, 200 Partien, Seed 20260931, Knopf wie Spielbetrieb (Bezug b01 + K3-P: 0,555; b01 ohne Knopf 0,515)"
bash tools/argmax_profile.sh "tor2a-v24${ARM}" "$NEW" MOSAIC_ENVELOPE_PROJECTED=1 MOSAIC_ENVELOPE_SEARCH_C=1.0
python - "$ARM" <<'EOF'
import json,sys
arm=sys.argv[1]
a=json.load(open(f'evaluations/artifacts/tor2a_v24{arm}.json',encoding='utf-8'))['arme'][0]
ref=json.load(open('evaluations/artifacts/tor2a_k3p10_v23b01.json',encoding='utf-8'))['arme'][0]
print(f"TOR 2a v24-{arm}: volle Spalten {a['sp_voll']:.4f} (KI +-{a['sp_voll_ci']:.4f}), Punkte {a['punkte']:.2f}, Zeilen {a['zeilen_voll']:.4f}, Strafleiste {a['floor']:.2f}")
print(f"        Bezug b01+K3-P: {ref['sp_voll']:.4f}, Punkte {ref['punkte']:.2f} -> {'NICHT GEFALLEN' if a['sp_voll'] >= ref['sp_voll'] else 'GEFALLEN (Punktschaetzer) -- Vorlage'}")
EOF

echo "== 2) Tor 1: paired_gating v24-${ARM} gegen v23-b01_brierbest @400, beide Seiten Champion-Spec, Deckel 200 Paare, KEINE Promotion"
python -X utf8 -u tools/paired_gating.py --model-a "$NEW" --model-b "$REF" --name-a "v24-${ARM}" --name-b "v23-b01_brierbest" --spec-a "$SPEC" --spec-b "$SPEC" --sims 400 --max-pairs 200 --seed 20261012 --no-promote-winner --out "$ART/paired_gating_result_v24-${ARM}_vs_v23-b01_s12.json"
# set -e: der Pruefblock steht als Bedingung im if, damit ein Exit 1 (Fruehstopp) die Kette nicht reisst.
if python - "$ARM" <<'EOF'
import json,sys
arm=sys.argv[1]
d=json.load(open(f'evaluations/artifacts/paired_gating_result_v24-{arm}_vs_v23-b01_s12.json',encoding='utf-8'))
print(f"TOR 1 (Seed 20261012): {d['a_wins_total']}:{d['b_wins_total']} nach {d['done_pairs']} Paaren, SPRT {d['sprt_verdict']}, McNemar p {d['report_mcnemar_p']:.4f}, Diff {d['mean_pair_diff']:+.2f}, Punkte {d['avg_score_a']:.1f} gegen {d['avg_score_b']:.1f}")
raise SystemExit(0 if d['done_pairs'] >= 150 else 1)
EOF
then
  echo "   n >= 150 Paare: Tor-1-Messung in Champion-Strenge vollstaendig"
else
  echo "   Fruehstopp unter 150 Paaren -> Replikation mit eigenem Seed (Champion-Strenge)"
  python -X utf8 -u tools/paired_gating.py --model-a "$NEW" --model-b "$REF" --name-a "v24-${ARM}" --name-b "v23-b01_brierbest" --spec-a "$SPEC" --spec-b "$SPEC" --sims 400 --max-pairs 200 --seed 20261013 --no-promote-winner --out "$ART/paired_gating_result_v24-${ARM}_vs_v23-b01_s13.json"
fi

echo "== 3) Tor 2b: gepaarte Arena mit Logs, beide Richtungen 2 x 80, Seed 20261014, Spalten aus der Brettgeometrie"
python -X utf8 -u tools/paired_arena_env_ab.py --env-name MOSAIC_ENVELOPE_SEARCH_C --arms 1.0 --control 1.0 --model "$NEW" --model-b "$REF" --spec-a "$SPEC" --spec-b "$SPEC" --net-sims 400 --n-games 80 --seed 20261014 --log-games --out-prefix "v24${ARM}_vs_b01_first_s14"
python -X utf8 -u tools/paired_arena_env_ab.py --env-name MOSAIC_ENVELOPE_SEARCH_C --arms 1.0 --control 1.0 --model "$REF" --model-b "$NEW" --spec-a "$SPEC" --spec-b "$SPEC" --net-sims 400 --n-games 80 --seed 20261014 --log-games --out-prefix "v24${ARM}_vs_b01_second_s14"
python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$ART/paired_arena_env_v24${ARM}_vs_b01_first_s14.json" --out "$ART/columns_v24${ARM}_vs_b01_first_s14.json"
python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$ART/paired_arena_env_v24${ARM}_vs_b01_second_s14.json" --out "$ART/columns_v24${ARM}_vs_b01_second_s14.json"

echo "== ABNAHME $ARM DURCH $(date +%H:%M:%S): Artefakte tor2a_v24${ARM}.json, paired_gating_result_v24-${ARM}_vs_v23-b01_s1*.json, paired_arena_env_v24${ARM}_vs_b01_*_s14.json, columns_v24${ARM}_vs_b01_*_s14.json -- Verdikt registriert der Koordinator (par.6e, Generatorwahl)."
