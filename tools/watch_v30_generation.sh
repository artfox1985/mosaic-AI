#!/usr/bin/env bash
# Beobachter fuer EINE Klasse der v30-Erzeugung (2026-09-18, Sitzungsuebernahme 18:10).
#
# WARUM ES IHN GIBT: Sockel und Rest-Kette laufen verwaist bzw. in der Hintergrundaufgabe der
# ALTEN Sitzung; ihre Ausgabe ist fuer die neue Sitzung unerreichbar. Dieser Beobachter stellt
# den Fortschritt ueber die ARTEFAKTE her (Dateizahl in data/, laufzeit-Block im Manifest).
#
# Reine Beobachtung: ein `ls` je 120 s. Der Prozess-Check per PowerShell laeuft NUR, wenn ein
# Stillstand erkannt wurde -- er kostet sonst unnoetig Last neben der Erzeugung.
#
# START ALS DATEI (feedback_chain_waits_on_its_own_wrapper):
#   bash tools/watch_v30_generation.sh <klasse> <ziel>
# z.B.  bash tools/watch_v30_generation.sh v29-b11-policy 400
#
# EXIT-CODES: 0 = Klasse fertig (Ziel erreicht UND laufzeit-Block im Manifest),
#             10 = Stillstand (keine neue Datei in STILL_S bei laufendem Prozess),
#             11 = Erzeugungsprozess weg, Klasse aber unvollstaendig.
set -uo pipefail
cd "$(dirname "$0")/.."

KLASSE="${1:?Klasse fehlt, z.B. v29-b11-policy}"
ZIEL="${2:?Zieldateizahl fehlt}"
INTERVALL=120
STILL_S=1800          # 30 min ohne neue Datei bei laufendem Prozess = Stillstand
ANLAUF_S=3600         # 60 min ohne die ERSTE Datei der Klasse (Klassenwechsel dauert)

zaehle() { ls data 2>/dev/null | grep -c "^selfplay_${KLASSE}_" ; }

laufzeit_block() {
  python -X utf8 - "$KLASSE" <<'PYEOF'
import glob, io, json, sys
try:
    ps = sorted(glob.glob(f"data/manifest_{sys.argv[1]}_*.json"))
    d = json.load(io.open(ps[-1], encoding="utf-8")) if ps else {}
    print("JA" if "laufzeit" in d else "NEIN")
except Exception:
    print("UNKLAR")
PYEOF
}

prozess_laeuft() {
  local out
  out=$(powershell -NoProfile -Command "@(Get-CimInstance Win32_Process | Where-Object { \$_.Name -match 'python' -and \$_.CommandLine -match 'self_play\.py' }).Count" 2>/dev/null | tr -d '\r ')
  case "$out" in
    0) echo NEIN ;;
    ''|*[!0-9]*) echo UNKLAR ;;   # unklare Antwort gilt als BELEGT
    *) echo JA ;;
  esac
}

N0=$(zaehle)
T_LETZTE=$(date +%s)
echo "$(date +%H:%M:%S)  START Beobachter Klasse ${KLASSE}: ${N0}/${ZIEL} Dateien"

while :; do
  sleep "$INTERVALL"
  N=$(zaehle)
  JETZT=$(date +%s)
  if [ "$N" -gt "$N0" ]; then
    T_LETZTE=$JETZT
    N0=$N
  fi
  RUHE=$(( JETZT - T_LETZTE ))

  if [ "$N" -ge "$ZIEL" ]; then
    LZ=$(laufzeit_block)
    echo "$(date +%H:%M:%S)  ${N}/${ZIEL} Dateien, laufzeit-Block: ${LZ}"
    if [ "$LZ" = "JA" ]; then
      echo "$(date +%H:%M:%S)  KLASSE ${KLASSE} FERTIG (${N} Dateien, laufzeit-Block im Manifest)"
      exit 0
    fi
    continue
  fi

  echo "$(date +%H:%M:%S)  ${N}/${ZIEL} Dateien (letzte neue vor ${RUHE}s)"

  GRENZE=$STILL_S
  [ "$N" -eq 0 ] && GRENZE=$ANLAUF_S
  if [ "$RUHE" -ge "$GRENZE" ]; then
    P=$(prozess_laeuft)
    if [ "$P" = "NEIN" ]; then
      echo "$(date +%H:%M:%S)  ABBRUCH: kein self_play.py-Prozess, Klasse ${KLASSE} aber bei ${N}/${ZIEL}"
      exit 11
    fi
    echo "$(date +%H:%M:%S)  STILLSTAND: ${RUHE}s keine neue Datei, Prozess laeuft (${P}) -- Nutzer informieren"
    exit 10
  fi
done
