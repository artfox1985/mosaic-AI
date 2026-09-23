#!/usr/bin/env bash
# Historien-Umschrieb: die AUSFUEHRBAREN Teile der eingefrorenen Artefakte aus
# der gesamten Git-Historie entfernen (*.onnx, *.pth, *.whl unter
# models/frozen_champions/ und models/frozen_heuristics/).
#
# ================== NICHT UNBEAUFSICHTIGT LAUFEN LASSEN ======================
#
# **Dies ist die eine Ausnahme von CLAUDE.md "Die Historie wird NICHT
# umgeschrieben".** Nutzer-Entscheid 2026-09-23: *"die frozen champs kannst
# umschreiben"* und *"nein soll er nicht. bei bedarf stell ich die netze zur
# verfuegung"*. Ohne diesen Entscheid gilt die Regel unveraendert weiter --
# dieses Skript ist kein Praezedenzfall fuer andere Umschriebe.
#
# GEMESSEN am Stand 2026-09-23 (`git count-objects -vH`: 17.631 Objekte,
# 227,5 MiB Pack; Blob-Summe mit Pfad 234,9 MB):
#
#   Champions schwer   166,3 MB   ONNX, Gewichte, Wheels aus 10 Artefakten
#   Heuristiken GANZ    36,1 MB   32,2 schwer + 3,9 Metadaten, 7 Artefakte
#   ---------------------------------------------------------------------
#   bleibt              32,6 MB   Code, Preregs, Chronik, GUI, Champion-Metadaten
#
# CHAMPIONS behalten ihre Metadaten (spec.json, manifest.json,
# golden_probe.json, wheel.sha256) -- 0,2 MB fuer ALLE zehn zusammen. Sie
# bleiben damit IDENTIFIZIERBAR (Vertragshash, Herkunft, Golden Probe als
# Nachweis), nur nicht mehr ausfuehrbar.
#
# HEURISTIKEN fallen VOLLSTAENDIG, auch die Metadaten (Nutzer-Entscheid
# 2026-09-23). Ihre Elo-Zahlen stehen im Register elo_history.csv.
#
# ------------------------------------------------------------------ FOLGEN --
#
# 1. JEDER Commit-Hash aendert sich. Jeder bestehende Klon wird ungueltig und
#    muss neu geklont werden. Ein Force-Push ist noetig -- NUR auf ausdrueckliche
#    Anweisung (CLAUDE.md "Kein Push ohne Anweisung").
# 2. Ein frischer Klon hat danach KEIN lauffaehiges Netz mehr, auch nicht das
#    des amtierenden Champions. Das ist gewollt (Nutzer-Entscheid oben).
# 3. **Der Elo-Anker `hv4_anchor` verschwindet VOLLSTAENDIG aus der Historie**,
#    samt Spec, Manifest und Golden Probe -- er ist eine Heuristik. Die
#    Leiter selbst haengt daran nicht -- `evaluations/elo_history.csv` traegt die
#    Zahlen, das Artefakt liegt im Arbeitsbaum und in restic. Aber ein frischer
#    Klon kann eine Anker-Kante nicht mehr nachfahren, ohne dass der Nutzer das
#    Artefakt bereitstellt. Das gehoert vor dem Lauf gewusst.
#
# ------------------------------------------------------- VORBEDINGUNGEN -----
#
# a) **Keine zweite Sitzung auf dem Baum.** Ein Umschrieb waehrend einer
#    Parallelsitzung setzt deren HEAD auf verwaiste Commits.
# b) **restic-Snapshot unmittelbar vorher** (`tools/mosaic_backup.ps1`, Tag
#    daily) -- der Umschrieb ist nicht rueckholbar, der Snapshot ist der
#    einzige Rueckweg.
# c) `git-filter-repo` installiert: `pip install git-filter-repo`.
# d) Baum sauber (`git status --short` leer ausser player_profiles.json).
#
# GIT-CRYPT: `player_profiles.json` haengt am Smudge/Clean-Filter
# (.gitattributes). `git filter-repo` arbeitet auf der OBJEKTdatenbank und
# laesst die Blobs dieser Datei unberuehrt, solange sie nicht im Pfadfilter
# steht -- sie steht es nicht. Nach dem Lauf trotzdem pruefen, dass die Datei
# im Arbeitsbaum weiterhin Klartext ist und `git-crypt status` sie als
# verschluesselt fuehrt.
#
# ============================================================================
set -uo pipefail
cd "$(dirname "$0")/.."

echo "== Vorbedingungen"
# `git filter-repo` als UNTERBEFEHL setzt voraus, dass `git-filter-repo` im PATH
# liegt. Der pip-Install legt die .exe nach `<python>/Scripts`, und das ist hier
# NICHT im PATH -- geprueft am 2026-09-23: `command -v git-filter-repo` leer,
# `python -m git_filter_repo --version` liefert a40bce54. Darum wird ueber das
# MODUL aufgerufen; der Unterbefehl waere nach bestandener Pruefung gescheitert.
FR="python -m git_filter_repo"
$FR --version >/dev/null 2>&1 || {
  echo "ABBRUCH: git-filter-repo fehlt -> pip install git-filter-repo"; exit 1; }

# Vorbedingung a) ueber die EINE gehaertete Warteschleife (tools/lib/cpu_free.sh).
# Hier stand bis zum 2026-09-23 eine eigene Kopie des Prozessfilters, und sie war
# defekt: das Muster `[w]indow` trifft die Kommandozeile fast jedes
# Windows-Systemprozesses. Gemessen an einer FREIEN Maschine zaehlte diese Kopie
# 48 Prozesse (svchost, explorer, StartMenuExperienceHost), die gehaertete
# Fassung 0 -- der Waechter haette also dauerhaft blockiert. Genau die
# Bauform-Vielfalt, die par.8h Fund 5 abgeschafft hat; diese Kopie war
# uebersehen worden, weil sie nach jener Durchsicht entstand.
. "$(cd "$(dirname "$0")" && pwd)/lib/cpu_free.sh"
n=$(cpu_busy_count)
[ "$n" = "0" ] || { echo "ABBRUCH: $n Prozesse laufen -- keine zweite Sitzung auf dem Baum (Vorbedingung a)"; exit 2; }

schmutz=$(git status --short | grep -v "player_profiles" | wc -l)
[ "$schmutz" = "0" ] || { echo "ABBRUCH: Baum nicht sauber ($schmutz Eintraege)"; git status --short; exit 3; }

echo "   vorher:"; git count-objects -vH | sed 's/^/     /'
echo ""
echo "== HINWEIS: restic-Snapshot muss unmittelbar vorher gelaufen sein (Vorbedingung b)."
echo "   Weiter mit ENTER, Abbruch mit Strg-C."
read -r _

$FR --force \
  --path-glob 'models/frozen_champions/*/*.onnx' \
  --path-glob 'models/frozen_champions/*/*.pth' \
  --path-glob 'models/frozen_champions/*/*.whl' \
  --path 'models/frozen_heuristics/' \
  --invert-paths

echo ""
echo "== nachher"
git reflog expire --expire=now --all && git gc --prune=now
git count-objects -vH | sed 's/^/     /'

echo ""
echo "== Nachkontrolle (von Hand pruefen, nicht ueberfliegen)"
echo "   1. git log --oneline -5          -- Historie steht, Reihenfolge stimmt"
echo "   2. git-crypt status | grep player_profiles"
echo "   3. git remote -v                 -- filter-repo ENTFERNT origin; neu setzen:"
echo "        git remote add origin https://github.com/artfox1985/mosaic-AI.git"
echo "   4. Force-Push NUR auf ausdrueckliche Anweisung des Nutzers."
