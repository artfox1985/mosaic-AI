#!/usr/bin/env bash
# Abnahme des 714er-Arms v24-b03 NACH dem Wechsel auf das 744er-Wheel (Nutzer 2026-09-05: "du kannst
# eventuell das artefakt champion wheel verwenden"): laeuft in der Mess-venv `venv_measure714/`, in der
# das Wheel des eingefrorenen Champions (models/frozen_champions/v23-b01_k3p10/mosaic_rust_k3p_20260904.whl,
# Kontrakt efd564d87bac2722, INPUT_SIZE 714) plus onnx/numpy installiert ist. `python` im PATH zeigt auf
# diese venv, damit night_v24_acceptance_chain.sh, argmax_profile.sh, paired_gating.py, self_play.py und
# die Sonden unveraendert laufen; der Encoder-Waechter der Kette prueft 714 gegen 714.
# Wartet: b03-Modell da, kein train.py, keine andere CPU-Messung, Nachtkette (after_b05) beendet.
# Aufruf (Projektordner, Hintergrund, ohne Pipe):  bash tools/night_v24_b03_acceptance_714.sh
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
VENV="venv_measure714/Scripts"
[ -x "$VENV/python.exe" ] || { echo "STOPP: $VENV/python.exe fehlt (Mess-venv anlegen, siehe Kopfkommentar)"; exit 80; }
export PATH="$(pwd)/$VENV:$PATH"
python -X utf8 - <<'EOF'
import json, sys, mosaic_rust as mr
c = json.loads(mr.engine_config_json())
print(f"   Mess-venv: {sys.executable} | input_size {c.get('input_size')} | contract {c.get('contract_hash')}")
raise SystemExit(0 if c.get("input_size") == 714 and c.get("contract_hash") == "efd564d87bac2722" else 81)
EOF
[ $? = 0 ] || { echo "STOPP: Mess-venv liefert nicht das 714er-Champion-Wheel"; exit 81; }

procs() {
  # Zaehlt Prozesse, deren Kommandozeile auf das Muster passt. Eine LEERE oder
  # unlesbare Antwort (PowerShell-Fehler, Timeout) heisst NICHT "frei": nach
  # drei Versuchen 999 zurueckgeben, damit der Aufrufer weiter wartet. Falle
  # 2026-09-05: ein leerer Wert waere ueber ${n:-0} als 0 = frei gelesen worden.
  local out
  for _try in 1 2 3; do
    out=$(powershell -NoProfile -Command "(Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match '$1' -and \$_.Name -match 'python|bash|cargo' }).Count" 2>/dev/null | tr -d '\r[:space:]')
    case "$out" in ''|*[!0-9]*) sleep 5 ;; *) echo "$out"; return 0 ;; esac
  done
  echo 999
}
echo "== 0) Warten auf b03-Modell, Ende der Nachtkette und aller CPU-Messungen ($(date +%H:%M:%S); Deckel 40 h)"
tick=0
while true; do
  t=$(procs 'train\.py'); t=${t:-0}
  m=$(procs 'night_v24_after_b05_chain|night_v24_acceptance_chain|cpu_queue_after_b02|self_play\.py|paired_gating|paired_arena|maturin|cargo '); m=${m:-0}
  if [ -f models/alphazero_v24-b03_brierbest.onnx ] && [ "$t" = "0" ] && [ "$m" = "0" ]; then break; fi
  tick=$((tick+1)); [ "$tick" -gt 2400 ] && { echo "STOPP: 40 h ohne Bedingung"; exit 82; }
  [ $((tick % 30)) -eq 0 ] && echo "   warte: b03=$([ -f models/alphazero_v24-b03_brierbest.onnx ] && echo da || echo fehlt), train.py=$t, andere=$m ($(date +%H:%M:%S))"
  sleep 60
done
echo "   Bedingung erfuellt $(date +%H:%M:%S)"

echo "== 1) Abnahme b03 unter dem 714er-Champion-Wheel (Tor 2a/1 ohne und mit Knopf, Tor 2b) $(date +%H:%M:%S)"
bash tools/night_v24_acceptance_chain.sh b03; rc=$?
echo "   Abnahme b03 Exit $rc ($(date +%H:%M:%S))"
python -X utf8 -u tools/probes/arena_points_probe.py --artifact evaluations/artifacts/paired_arena_env_v24b03_vs_b01_first_s14.json evaluations/artifacts/paired_arena_env_v24b03_vs_b01_second_s14.json --out evaluations/artifacts/points_v24b03_vs_b01_s14.json || echo "   Kuppel-Bonus-Sonde b03 fehlgeschlagen"
echo "== FERTIG $(date +%H:%M:%S): das Artefakt-Wheel ist BYTE-IDENTISCH mit dem 714er-Wheel der b01/b02-Abnahmen (sha256 der .pyd fb553c93bf38baa2, geprueft 2026-09-05 20:07) -- Zahlen direkt vergleichbar."
