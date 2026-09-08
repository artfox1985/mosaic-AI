#!/usr/bin/env bash
# v26-Erzeugung, Klassen 2 und 3 (Schwarm), NACHDEM der Traeger-Lauf durch ist.
# Nutzer-Auftrag 2026-09-09, 00:40: "traeger partie ist gestartet. um die zwei
# schwarm partien kuemmerst du dich sobald die traeger durch sind."
#
# Die Befehle stehen woertlich in PREREG_v26_window.md par.7 (Generator v25-b01,
# Spec v24-b07_brierbest, Seeds 20260912 und 20260913). --games 4000 auch fuer
# den Ausflug: er hat eine eigene game_id und zaehlt mit (par.19a der v25-Prereg).
#
# WARTEBEDINGUNG, gehaertet: gestartet wird erst, wenn (a) das Manifest des
# Traeger-Laufs seinen laufzeit-Block traegt -- den schreibt self_play.py:771 erst
# am Ende -- UND (b) die Prozessabfrage eine KLARE 0 liefert. Alles andere,
# auch eine leere oder unlesbare Antwort, gilt als BELEGT und wartet weiter.
# Zwei Erzeugungen gegeneinander waeren genau die Nebenlast, die Partien
# nichtdeterministisch verstuemmelt (CLAUDE.md, Messungen laufen exklusiv).
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8

MODEL=models/alphazero_v25-b01_brierbest.onnx
SPEC=models/v24-b07_brierbest.spec.json

sockel_fertig() {
  python - <<'EOF'
import glob, io, json
try:
    ps = sorted(glob.glob("data/manifest_v25-b01-policy_*.json"))
    d = json.load(io.open(ps[-1], encoding="utf-8")) if ps else {}
    print("JA" if "laufzeit" in d else "NEIN")
except Exception:
    print("UNKLAR")
EOF
}

keine_erzeugung_laeuft() {
  local n
  n=$(powershell -NoProfile -Command \
      "@(Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match 'self_play\.py' }).Count" \
      2>/dev/null | tr -d '\r' | tail -1)
  [ "$n" = "0" ]
}

echo "== WARTEN auf den Traeger-Lauf $(date +%F' '%H:%M:%S)"
while :; do
  status=$(sockel_fertig)
  n_files=$(ls data/ 2>/dev/null | grep -c '^selfplay_v25-b01-policy_' || true)
  if [ "$status" = "JA" ] && keine_erzeugung_laeuft; then
    echo "   Traeger durch: $n_files Dateien, Manifest traegt laufzeit ($(date +%H:%M:%S))"
    break
  fi
  echo "   noch nicht ($(date +%H:%M:%S)): laufzeit=$status, Dateien=$n_files"
  sleep 300
done

echo "== 2) Schwarm Haelfte a, 4.000 Partien, value-only, temperiert $(date +%F' '%H:%M:%S)"
python -u self_play.py --mode network --model "$MODEL" --spec "$SPEC" \
  --games 4000 --sims 100 --value-only --version v25-b01-value-tempc \
  --threads 11 --chunk 10 --per-file 10 --seed 20260912 \
  --action-temp 2 --deviate-prob 1.0
echo "   Exit $? ($(date +%H:%M:%S)), Dateien: $(ls data/ | grep -c '^selfplay_v25-b01-value-tempc_')"

echo "== 3) Schwarm Haelfte b, 4.000 Identitaeten, value-only, Ausflug $(date +%F' '%H:%M:%S)"
python -u self_play.py --mode network --model "$MODEL" --spec "$SPEC" \
  --games 4000 --sims 100 --value-only --version v25-b01-value-excursion \
  --threads 11 --chunk 10 --per-file 10 --seed 20260913 \
  --excursion-prob 1.0 --tau-argmax-from-move 1 --no-root-noise
echo "   Exit $? ($(date +%H:%M:%S)), Dateien: $(ls data/ | grep -c '^selfplay_v25-b01-value-excursion_')"

echo "== v26-ERZEUGUNG FERTIG $(date +%F' '%H:%M:%S)"
for k in policy value-tempc value-excursion; do
  echo "   $k: $(ls data/ | grep -c "^selfplay_v25-b01-${k}_" || true) Dateien"
done
