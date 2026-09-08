#!/usr/bin/env bash
# Welche der beiden v24-b07-Schwarmhaelften traegt den G-2-Posten in v27?
# PREREG_v26_window.md par.6 Punkt 1 (Nutzer-Entscheid: kein Split, und die Wahl wird
# GEMESSEN statt geraten). Kandidaten: die temperierte Haelfte (value-tempc) gegen die
# Ausflug-Haelfte (value-excursion). Beide Korpora liegen fertig im Baum, es wird nichts
# neu erzeugt.
#
# ZEITFENSTER, und warum ausgerechnet dieses: die Sonden sind CPU-Arbeit und duerfen
# deshalb nicht neben die Erzeugung. Gestartet wird erst, wenn (a) KEIN self_play mehr
# laeuft und (b) das Training v26-b01 laeuft -- dann liegt die Last auf der GPU, und
# EIN CPU-Auftrag daneben ist ausdruecklich erlaubt (docs/working_rules.md, "Auslastung:
# GPU und CPU duerfen parallel laufen"). Zugleich ist damit der CPU-schwere Blockbau der
# Kette vorbei, der vor dem Training laeuft.
#
# Gehaertet wie die anderen Ketten: alles ausser einer klaren Zahl gilt als belegt.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts

zaehle() {
  powershell -NoProfile -Command "@(Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match '$1' }).Count" 2>/dev/null | tr -d '\r' | tail -1
}

echo "== WARTEN auf das Training v26-b01 $(date +%F' '%H:%M:%S)"
while :; do
  sp=$(zaehle 'self_play')
  tr=$(zaehle 'train\.py')
  case "$sp" in ''|*[!0-9]*) sp=BELEGT;; esac
  case "$tr" in ''|*[!0-9]*) tr=0;; esac
  if [ "$sp" = "0" ] && [ "$tr" -ge 1 ] 2>/dev/null; then
    echo "   Training laeuft, Erzeugung ist durch ($(date +%H:%M:%S))"
    break
  fi
  echo "   noch nicht ($(date +%H:%M:%S)): self_play=$sp train=$tr"
  sleep 300
done

A="data::selfplay_v24-b07-value-tempc_*.pkl"
B="data::selfplay_v24-b07-value-excursion*_*.pkl"

echo "== 1) Zustandsvielfalt beider Haelften $(date +%H:%M:%S)"
python -X utf8 -u tools/probes/corpus_state_diversity_probe.py "$A" "$B" \
  --out "$ART/g2_swarm_choice_diversity.json"
echo "   Exit $? ($(date +%H:%M:%S))"

echo "== 2) Bedingte Vielfalt (Verhalten gegen Spiel) $(date +%H:%M:%S)"
python -X utf8 -u tools/probes/paired_corpus_divergence_probe.py "$A" "$B" \
  --out "$ART/g2_swarm_choice_divergence.json"
echo "   Exit $? ($(date +%H:%M:%S))"

echo "== G-2-MESSUNG FERTIG $(date +%F' '%H:%M:%S)"
echo "   Artefakte: $ART/g2_swarm_choice_diversity.json, $ART/g2_swarm_choice_divergence.json"
echo "   Verdikt gehoert nach PREREG_v26_window.md par.6 Punkt 1."
