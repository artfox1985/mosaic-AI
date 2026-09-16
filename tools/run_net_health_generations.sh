#!/usr/bin/env bash
# Fahrplan Nr. 20, Punkt 5 der Netz-Gesundheit (PREREG_v29_window.md par.6d):
# Value-R2 (gesamt und je Runde) und Policy Top-1/Top-3 fuer JEDE verfuegbare
# Generation in EINER Tabelle -- ueber die Aeren-Grenzen 744 / 755 / 794 hinweg.
#
# WARUM DAS ERST JETZT GEHT: tools/offline_diagnosis.py baute das Modell mit der
# HEUTIGEN config.INPUT_SIZE (794) und scheiterte an jedem Alt-Checkpoint mit
# "size mismatch for flat_branch.0.weight". Seit dem Umbau vom 2026-09-16 leitet
# es die Breite je Checkpoint ab und KUERZT den Merkmalsvektor darauf -- genau
# das, was der Spielpfad tut (engine/src/net.rs:425 flach, :989 Planes).
#
# WARUM NICHT AUF DEM DEFAULT-VAL-SPLIT: der liegt UNGLEICH stark in den
# Trainingssaetzen der verglichenen Netze (gemessen 2026-09-16, n=360 Dateien:
# 272 in window_v29_train, 224 in window_v28_train, 105 in window_v27_train).
# Eine Reihe darauf misst zu einem wachsenden Teil Auswendiglernen und
# ERZEUGT den Trend, den sie zeigen soll. Innerhalb EINER Aera (Punkt 3/4,
# b03 gegen b05) kuerzt sich das weg, ueber Aeren hinweg nicht.
#
# Die beiden eingefrorenen Saetze sind dagegen fuer ALLE sechs Staende
# zurueckgehalten: ihre Quelldateien schneiden sich mit keinem der drei
# Fenster (geprueft 2026-09-16: 0 von 20 frozen_v3-Quellen in window_v27/28/29,
# keine davon noch in data/).
#
# v24-b04 aus der Prereg-Formulierung existiert nicht mehr als Datei
# (Aufraeumregel "nur die letzten zwei Champions"). v27-b01_brierbest traegt
# dieselbe Breite 744 -- eingefuehrt mit e49eb3c (2026-09-05) GENAU fuer
# v24-b04 -- und vertritt die Aera.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
MODELS="v27-b01_brierbest v28-b01_brierbest v28-b02_brierbest v29-b02_brierbest v29-b03_brierbest v29-b05_brierbest"

BUSY='[p]aired_gating\.py|[f]rozen_referee_match\.py|[o]ffline_diagnosis|[t]rain\.py|[b]uild_cache_incremental\.py|[w]indow_train_split\.py'
maschine_frei() {
  local n
  n=$(powershell -NoProfile -Command "@(Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match '$BUSY' -and \$_.Name -notmatch 'pwsh|powershell' }).Count" 2>/dev/null | tr -d '\r' | tail -1)
  [ "$n" = "0" ]
}

echo "########## NETZ-GESUNDHEIT PUNKT 5 WARTET $(date +%F' '%H:%M:%S)"
while :; do
  maschine_frei && { echo "   Maschine frei ($(date +%H:%M:%S))"; break; }
  echo "   belegt ($(date +%H:%M:%S))"; sleep 5
done

echo ""
echo "== 1) frozen_v3, ZURUECKGEHALTEN fuer alle sechs Staende $(date +%F' '%H:%M:%S)"
python -X utf8 -u tools/offline_diagnosis.py --model $MODELS   --frozen-set v3 --no-oracle --threads 8   --out "$ART/net_health_p5_generations_frozenv3.json"
echo "   Exit $? ($(date +%H:%M:%S))"

echo ""
echo "== 2) Default-Val-Split, die GEGENPROBE zur Kontamination $(date +%H:%M:%S)"
# Bewusst MITgemessen, nicht als zweiter Versuch derselben Frage: die beiden
# Grundmengen unterscheiden sich genau darin, wie stark sie in den
# Trainingssaetzen liegen. Zeigen sie verschiedene RICHTUNGEN, ist die
# Kontamination belegt statt behauptet. 23 Minuten, 582.132 Zuege.
python -X utf8 -u tools/offline_diagnosis.py --model $MODELS   --no-oracle --threads 8   --out "$ART/net_health_p5_generations_valsplit.json"
echo "   Exit $? ($(date +%H:%M:%S))"

# frozen_v1 ist BEWUSST NICHT dabei: jener Satz stammt aus der plattenBLINDEN
# Aera (v10b/v12, PREREG_frozen_v3_eval_set.md par.1). Auf plattenblindes Spiel
# wird in diesem Projekt nicht geeicht.

echo "########## FERTIG $(date +%F' '%H:%M:%S)"
