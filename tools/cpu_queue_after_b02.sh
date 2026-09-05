#!/usr/bin/env bash
# CPU-Warteschlange nach der b02-Abnahme (Nutzer 2026-09-05, 20:05: "knopf dosis kannst eintakten").
# Wartet, bis KEIN Prozess mehr die Abnahme-Kette traegt (bash mit night_v24_acceptance_chain in der
# Kommandozeile), und faehrt dann nacheinander -- ein CPU-Auftrag zu jeder Zeit, GPU-Training darf
# parallel laufen (working_rules.md "Auslastung"):
#   1) cargo test --release (Python-DLL im PATH wie tools/hooks/pre-push) -- K3-P2 und der 744er-Encoder
#   2) Wheel bauen (python -m maturin build --release), NICHT installieren: train.py (b04/b05) haelt
#      das alte Wheel; Installation ueber Kette 4 nach den Trainings (STATUS Abschnitt 1)
#   3) Knopf-Dosis: argmax v24-b01 bei K3-P C 0,5 (PREREG_v24_window.md par.9b; Bezug ohne Knopf 0,518,
#      C 1,0 0,443)
# Aufruf (Projektordner, Hintergrund, ohne Pipe):  bash tools/cpu_queue_after_b02.sh
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8

busy() {
  # Zaehlt Prozesse, deren Kommandozeile auf das Muster passt. Eine LEERE oder
  # unlesbare Antwort (PowerShell-Fehler, Timeout) heisst NICHT "frei": nach
  # drei Versuchen 999 zurueckgeben, damit der Aufrufer weiter wartet. Falle
  # 2026-09-05: ein leerer Wert waere ueber ${n:-0} als 0 = frei gelesen worden.
  local out
  for _try in 1 2 3; do
    out=$(powershell -NoProfile -Command "(Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match 'night_v24_acceptance_chain' -and \$_.Name -match 'python|bash|cargo' }).Count" 2>/dev/null | tr -d '\r[:space:]')
    case "$out" in ''|*[!0-9]*) sleep 5 ;; *) echo "$out"; return 0 ;; esac
  done
  echo 999
}

echo "== 0) Warten auf das Ende der Abnahme-Kette ($(date +%H:%M:%S); Deckel 12 h)"
tick=0
while true; do
  n=$(busy); n=${n:-0}
  [ "$n" = "0" ] && break
  tick=$((tick+1)); [ "$tick" -gt 720 ] && { echo "STOPP: Abnahme-Kette nach 12 h noch aktiv"; exit 60; }
  [ $((tick % 30)) -eq 0 ] && echo "   warte: Abnahme-Kette aktiv ($n) ($(date +%H:%M:%S))"
  sleep 60
done
echo "   Abnahme-Kette beendet, Warteschlange startet $(date +%H:%M:%S)"

echo "== 1) cargo test --release (K3-P2, Encoder 744) $(date +%H:%M:%S)"
PYDIR="${MOSAIC_PYTHON_DIR:-}"
[ -z "$PYDIR" ] && PYDIR="$(python -c 'import sys; print(sys.base_prefix)' 2>/dev/null)"
command -v cygpath >/dev/null 2>&1 && PYDIR="$(cygpath -u "$PYDIR" 2>/dev/null || printf '%s' "$PYDIR")"
if ls "$PYDIR"/python3*.dll >/dev/null 2>&1; then export PATH="$PYDIR:$PATH"; echo "   PATH-Prefix: $PYDIR"; else echo "   WARNUNG: keine python3*.dll unter '$PYDIR'"; fi
( cd engine && cargo test --release ); rc=$?
echo "   cargo test Exit $rc ($(date +%H:%M:%S))"
if [ "$rc" != "0" ]; then
  echo "STOPP: cargo test rot -- kein Wheel, keine weiteren Schritte; Nutzer entscheidet."
  exit 61
fi

echo "== 2) Wheel bauen (nicht installieren) $(date +%H:%M:%S)"
( cd engine && python -m maturin build --release ); rc=$?
echo "   maturin Exit $rc ($(date +%H:%M:%S))"; ls -la engine/target/wheels/
[ "$rc" = "0" ] || { echo "STOPP: Wheel-Bau rot"; exit 62; }

echo "== 3) Knopf-Dosis: argmax v24-b01 bei K3-P C 0,5 (200 Partien @400, Seed 20260931) $(date +%H:%M:%S)"
bash tools/argmax_profile.sh "tor2a-v24b01c05" models/alphazero_v24-b01_brierbest.onnx MOSAIC_ENVELOPE_PROJECTED=1 MOSAIC_ENVELOPE_SEARCH_C=0.5; rc=$?
echo "   argmax Exit $rc ($(date +%H:%M:%S))"
python - <<'EOF'
import json
a=json.load(open('evaluations/artifacts/tor2a_v24b01c05.json',encoding='utf-8'))['arme'][0]
print(f"KNOPF-DOSIS v24-b01 C 0,5: volle Spalten {a['sp_voll']:.4f} (KI +-{a['sp_voll_ci']:.4f}), Punkte {a['punkte']:.2f}, Zeilen {a['zeilen_voll']:.4f} -- Bezug ohne Knopf 0,518, C 1,0 0,443, b01+C 1,0 0,555")
EOF

echo "== WARTESCHLANGE FERTIG $(date +%H:%M:%S): Ergebnisse registriert der Koordinator (par.9b Knopf-Dosis, K3-P2 par.8.11 cargo/Wheel)."
