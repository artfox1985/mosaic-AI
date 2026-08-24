#!/usr/bin/env bash
# Kann der HEURISTIK-LEHRER lange Musterreihen, oder kann es niemand?
#
# Anlass (Nutzer-Frage 2026-08-24, "ist es das richtige Netz und was muessen
# wir tun damit es lernbar ist"): B1 hat gezeigt, dass sich die Initiierung
# langer Reihen such-seitig erzwingen laesst, die FAEHIGKEIT sie zu fuehren
# aber nicht -- die Vollendungsquote lag in BEIDEN Armen bei nur ~0,53.
# Damit steht die Gabel:
#
#   Lehrer deutlich besser  -> die Kompetenz existiert im System und muss nur
#                              uebertragen werden (Destillation auf genau
#                              dieser Dimension).
#   Lehrer ebenfalls ~0,6   -> NIEMAND kann es. Self-Play kann nicht lernen,
#                              was im Korpus nicht vorkommt; die Kompetenz
#                              muss erzeugt werden (Seeding auf Vollendungs-
#                              Endphasen, oder eine Heuristik v2, die lange
#                              Reihen beherrscht -- Nutzer-Vorgabe).
#
# Eine Machbarkeitsprobe ueber 12 Partien deutete auf den ZWEITEN Fall
# (Heuristik 0,600 gegen Netz 0,553) -- das ist keine Messung, genau dafuer
# laeuft dieser Lauf.
#
# Konfiguration gespiegelt von der Referenz `paired_arena_env_imm_a02.json`
# (dieselben 407 Kampagnen-Seeds, net_sims 400, heur_sims 150), damit der
# Lauf in dieselbe Reihe gehoert.
#
# KEIN Brettwechsel noetig, anders als beim Netz-gegen-Netz-Lauf:
# `run_net_arena_match` setzt das Netz IMMER auf Brett 0
# (self_play.rs, `play_net_game(&net, 0, ...)`), und der Startspieler
# alterniert ohnehin ueber `first = i % 2`. Ein zweiter Lauf mit getauschten
# Seiten ist hier also nicht konstruierbar und auch nicht noetig.
#
# `--log-games` ist gesetzt, obwohl die Vollendungsquote allein aus den
# Zaehlerfeldern folgt: die sechs Standard-Kennzahlen (CLAUDE.md) brauchen
# die Logs, und sie gehoeren in JEDEN Messbericht.
#
# NICHT starten, solange etwas anderes CPU zieht: CPU-Nebenlast verstuemmelt
# Arena-Partien nichtdeterministisch.
set -euo pipefail

cd "$(dirname "$0")/.."

# Python-Verzeichnis aus der Umgebung, sonst ableiten -- KEIN fester Pfad
# (oeffentliches Repo). Gleiche Ableitung wie tools/hooks/pre-push.
PYDIR="${MOSAIC_PYTHON_DIR:-}"
if [ -z "$PYDIR" ] && command -v python >/dev/null 2>&1; then
    PYDIR="$(python -c 'import sys; print(sys.base_prefix)' 2>/dev/null)"
fi
if [ -n "$PYDIR" ] && command -v cygpath >/dev/null 2>&1; then
    PYDIR="$(cygpath -u "$PYDIR" 2>/dev/null || printf '%s' "$PYDIR")"
fi
[ -n "$PYDIR" ] && export PATH="$PYDIR:$PATH"

MODEL="$PWD/models/alphazero_v21_2d_brierbest.onnx"
SEEDS=evaluations/kampagnen_seeds_407.txt

echo "=== Netz@400 gegen Heuristik@150, 407 Kampagnen-Seeds ==="
python -u tools/paired_arena_env_ab.py \
  --env-name MOSAIC_DUMMY_UNUSED --arms 0 --control 0 \
  --model "$MODEL" \
  --net-sims 400 --heur-sims 150 \
  --seeds "$SEEDS" \
  --log-games \
  --out-prefix netvheur_longrow

echo "=== fertig ==="
