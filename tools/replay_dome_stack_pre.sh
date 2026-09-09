#!/usr/bin/env bash
# Der PRE-Lauf der Referenz-Partie (PREREG_dome_stack_information_sets.md par.12):
# dieselbe Partie, dasselbe Netz, heutiger Stand des Weltmodells. Der POST-Lauf nach dem
# Umbau vergleicht gegen genau dieses Artefakt.
#
# ZEITFENSTER: erst wenn (a) keine Erzeugung mehr laeuft, (b) das Training auf der GPU
# steht, und (c) die G-2-Sonden durch sind. Punkt (c) ist die Exklusivitaetsregel: EIN
# CPU-Auftrag neben der GPU ist erlaubt, zwei gegeneinander nicht.
# Gehaertet wie die anderen Ketten: alles ausser einer klaren Zahl gilt als belegt.
# SELBSTTREFFER (2026-09-09, hier gefunden): das Suchmuster steht auch in der
# Kommandozeile des FRAGENDEN Prozesses. `-match 'self_play'` lieferte deshalb
# nie 0, sondern 4, und die Wartebedingung ging nie auf -- die Kette stand 35
# Minuten still, obwohl die Erzeugung fertig war. Zwei Sperren dagegen: der
# escapte Punkt (`self_play\.py`; die fragende Kommandozeile traegt den
# Backslash, der Zielprozess nicht) UND der Ausschluss der PowerShell-Prozesse.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8

LOG=evaluations/fixtures/game_20260909_004553_seed876496.log
OUT=evaluations/artifacts/replay_dome_stack_pre.json

zaehle() {
  powershell -NoProfile -Command "@(Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match '$1' -and \$_.Name -notmatch 'pwsh|powershell' }).Count" 2>/dev/null | tr -d '\r' | tail -1
}

echo "== WARTEN auf das Fenster (Training laeuft, Sonden durch) $(date +%F' '%H:%M:%S)"
while :; do
  sp=$(zaehle 'self_play\.py'); tr=$(zaehle 'train\.py'); pr=$(zaehle 'corpus_state_diversity_probe|paired_corpus_divergence_probe')
  case "$sp" in ''|*[!0-9]*) sp=BELEGT;; esac
  case "$pr" in ''|*[!0-9]*) pr=BELEGT;; esac
  case "$tr" in ''|*[!0-9]*) tr=0;; esac
  # Zwei Faelle sind gut, nicht einer (berichtigt 2026-09-09): das Training auf
  # der GPU als Deckung ODER eine ganz freie Maschine. Die erste Fassung verlangte
  # ein LAUFENDES Training -- als es um 12:03 fertig war, wartete der Lauf auf
  # einen Zustand, den es nicht mehr gab, obwohl die Maschine frei dalag.
  if [ "$sp" = "0" ] && [ "$pr" = "0" ]; then
    echo "   Fenster offen ($(date +%H:%M:%S)): train=$tr (>=1 heisst Deckung durch die GPU, 0 heisst freie Maschine)"
    break
  fi
  echo "   noch nicht ($(date +%H:%M:%S)): self_play=$sp sonden=$pr train=$tr"
  sleep 300
done

# Pruefsumme der Referenz, bevor sie gelesen wird -- sie ist eingefroren (par.12).
python - <<'PYEOF'
import hashlib, pathlib, sys
p = pathlib.Path("evaluations/fixtures/game_20260909_004553_seed876496.log")
soll = "98c28a92881cd341b8c5cec3c4a24ef3c6babd83602c57d33cacbbccd3b9c002"
ist = hashlib.sha256(p.read_bytes()).hexdigest()
print(f"Referenz sha256 {ist} ({'OK' if ist == soll else 'ABWEICHUNG'})")
sys.exit(0 if ist == soll else 12)
PYEOF
[ $? -eq 0 ] || { echo "STOPP: die Referenz-Partie stimmt nicht mehr mit par.12 ueberein."; exit 12; }

echo "== PRE-Lauf $(date +%F' '%H:%M:%S)"
python -X utf8 -u tools/analyze_game_log.py --log "$LOG" \
  --model models/alphazero_v25-b01_brierbest.onnx --sims 400 \
  --oracle-json "$OUT"
echo "   Exit $? ($(date +%H:%M:%S))"
echo "== PRE-LAUF FERTIG $(date +%F' '%H:%M:%S), Artefakt: $OUT"
echo "   Verglichen wird spaeter an den vier Stellen aus par.12 (R1 Z.37-50, R2 135-137, R3 246-251, R4 369)."
