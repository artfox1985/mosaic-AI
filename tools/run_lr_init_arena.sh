#!/usr/bin/env bash
# PREREG_long_row_payoff.md par.3/B1, Messkette Schritt 2:
# gepaarte Arena NETZ-GEGEN-NETZ, 407 Kampagnen-Seeds, --log-games.
#
# Konfiguration exakt gespiegelt von der Referenzmessung
# `paired_arena_env_imm_netvnet.json` (dieselben 407 Seeds, dasselbe Modell
# beidseitig, 400/400 Sims) -- nur die Specs unterscheiden sich. Dadurch ist
# das Ergebnis direkt mit dem Implicit-Minimax-Lauf vergleichbar.
#
# Brettwechsel ist PFLICHT (zwei Laeufe mit getauschten Specs) -- siehe
# PREREG_agent_encapsulation.md par.6a: der Pflichtteil hat dort den
# Paritaets-Befund erst belastbar gemacht.
#
# NICHT starten, solange irgendetwas anderes CPU zieht: CPU-Nebenlast
# verstuemmelt Arena-Partien nichtdeterministisch (Signatur: Endstand 3:1).
set -euo pipefail

cd "$(dirname "$0")/.."
# Python-Verzeichnis aus der Umgebung, sonst ableiten -- KEIN fester Pfad
# (oeffentliches Repo, CLAUDE.md "keine Rechnerstruktur"). Gleiche Ableitung
# wie tools/hooks/pre-push: sys.base_prefix, danach cygpath, weil ein
# Windows-Pfad im POSIX-PATH am Doppelpunkt zerfaellt.
PYDIR="${MOSAIC_PYTHON_DIR:-}"
if [ -z "$PYDIR" ] && command -v python >/dev/null 2>&1; then
    PYDIR="$(python -c 'import sys; print(sys.base_prefix)' 2>/dev/null)"
fi
if [ -n "$PYDIR" ] && command -v cygpath >/dev/null 2>&1; then
    PYDIR="$(cygpath -u "$PYDIR" 2>/dev/null || printf '%s' "$PYDIR")"
fi
[ -n "$PYDIR" ] && export PATH="$PYDIR:$PATH"

MODEL=models/alphazero_v21_2d_brierbest.onnx
SEEDS=evaluations/kampagnen_seeds_407.txt
ON=models/lr_init_on.spec.json
OFF=models/lr_init_off.spec.json

echo "=== Arm 1: Initiierungs-Term auf Brett 0 ==="
python -u tools/paired_arena_env_ab.py \
  --env-name MOSAIC_DUMMY_UNUSED --arms 0 --control 0 \
  --model "$MODEL" --model-b "$MODEL" \
  --net-sims 400 --sims-b 400 \
  --seeds "$SEEDS" \
  --spec-a "$ON" --spec-b "$OFF" \
  --log-games \
  --out-prefix lrinit_netvnet

echo "=== Arm 2: Brettwechsel (Pflichtteil) ==="
python -u tools/paired_arena_env_ab.py \
  --env-name MOSAIC_DUMMY_UNUSED --arms 0 --control 0 \
  --model "$MODEL" --model-b "$MODEL" \
  --net-sims 400 --sims-b 400 \
  --seeds "$SEEDS" \
  --spec-a "$OFF" --spec-b "$ON" \
  --log-games \
  --out-prefix lrinit_netvnet_swap

echo "=== fertig ==="
