#!/usr/bin/env bash
# ANKER-KANTE fuer v29-b03 (Nutzer-Auftrag 2026-09-14: "hast sonst noch elo
# kanten die schwach dastehen?").
#
# BEFUND, der diesen Lauf ausloest: v29-b03 haengt im Elo-Register an DREI
# Kanten, und alle drei gehen gegen denselben Gegner (v28-b02@400). Eine
# Anker-Kante fehlt. Die Promotions-Checkliste verlangt aber drei
# VERSCHIEDENE Aufhaengungen -- Gating, Anker, Champion-2
# (`docs/promotion_checklist.md`). Fuer den einzigen Kandidaten der Generation
# ist das die Luecke, die als naechstes zu schliessen ist; sie kostet rund
# 25 min, weil der Anker netzlos spielt.
#
# AUFBAU exakt wie bei der letzten Anker-Kante des Champions (Register-Zeile
# 2026-09-12, "Anker-Kante KORREKT wiederholt"): der Anker laeuft @150 mit
# c_puct 0,3, die Netzseite @400 mit 1,5 und Champion-Spec, festes n=150 OHNE
# Fruehstopp, 6 Worker. Nur so ist die neue Kante mit der des Champions
# vergleichbar -- eine andere Sims-Zahl auf der Ankerseite waere ein anderer
# Knoten.
#
# CROSS-AERA IST HIER DER NORMALFALL, kein Fehler: das Anker-Artefakt traegt
# den Kontrakt 39648b95bbba1acf, das Live-Wheel 39994362fba145a6. Das
# Anker-Wheel wird NIE nachgezogen (`project_anchor_era_rule`), deshalb
# --force-cross-era. Der Golden-Selbsttest bleibt an; er ist die eigentliche
# Absicherung, dass das Artefakt im eigenen Wheel noch dasselbe spielt.
#
# KEINE PROMOTION aus diesem Lauf: die Kante wird eingetragen, der Champion
# bleibt v28-b02. Ein Champion-Wechsel ist ein eigener Ablauf und ein
# Nutzer-Entscheid (ans Ende der Generationsarbeit verschoben, Fahrplan Nr. 21).
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
NEU=models/alphazero_v29-b03_brierbest.onnx
CHAMP_SPEC=models/frozen_champions/v28-b02/spec.json
ANKER=models/frozen_heuristics/hv4_anchor

for f in "$NEU" "$CHAMP_SPEC"; do
  [ -f "$f" ] || { echo "ABBRUCH: $f fehlt"; exit 1; }
done
[ -d "$ANKER" ] || { echo "ABBRUCH: $ANKER fehlt"; exit 1; }

OUT="$ART/anchor_edge_v29-b03_vs_hv4_anchor.json"
echo "== ANKER-KANTE v29-b03 gegen hv4_anchor START $(date +%F' '%H:%M:%S)"
python -X utf8 -u tools/frozen_referee_match.py \
  --artifact-dir "$ANKER" \
  --model-a "$NEU" --spec-a "$CHAMP_SPEC" \
  --sims-a 400 --c-puct-a 1.5 \
  --sims-worker 150 --c-puct-worker 0.3 \
  --n-games 150 --seed-base 20261097 --workers 6 \
  --force-cross-era \
  --out "$OUT"
echo "   Exit $? ($(date +%H:%M:%S))"

echo "== FERTIG $(date +%F' '%H:%M:%S)"
echo "   Danach: Kante ins Register eintragen (tools/elo_tracker.py add,"
echo "   OHNE --early-stop, denn dieser Lauf faehrt festes n), Kommentar mit"
echo "   Cross-Aera-Vermerk. Damit haengt v29-b03 an zwei verschiedenen"
echo "   Gegnern statt nur am Champion."
