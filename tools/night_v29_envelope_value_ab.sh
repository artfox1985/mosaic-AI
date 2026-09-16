#!/usr/bin/env bash
# ANSCHLUSSKETTE an tools/night_v29_20260914.sh (Nutzer-Auftrag 2026-09-14:
# "takte den A/B term in die kette von heute ein").
#
# WAS HIER GEMESSEN WIRD: der Value-Anteil im Tiling, envelope_tiling_value_w
# (envelope.rs:1398-1400). Die Formel lautet
#     points + w_tile * w_e * cost_delta + w_val * (1 - w_e) * margin
# Der Value-Anteil haengt am KOMPLEMENT des Huellenprofils: mit dem
# Champion-Profil [1,0 0,92 0,67 0,33 0,0] steigt sein Gewicht ueber die Runden
# 0 -> 0,08 -> 0,33 -> 0,67 -> 1,0, waehrend die Huelle abfaellt. Frueh zaehlt,
# was geometrisch erreichbar bleibt, spaet die konkrete Endmarge.
# Eingeschaltet wird er allein durch w_val: is_off() ist
# w_tile == 0 UND w_val == 0 (envelope.rs:1420-1421, Test :1850).
#
# DAS IST EINE WIEDERHOLUNG, KEINE ERSTMESSUNG. par.8.6a der
# PREREG_geometric_envelope.md hat den Term am 2026-09-04 bereits gefahren und
# einen Nullbefund registriert (Arme V 0,5 / V 1,0 / T+V, je 160 Paare am
# v23-b01). Was sich seither geaendert hat und die Wiederholung traegt, steht
# in par.8.6b; die dort registrierte Lesart gilt, insbesondere: ein zweiter
# Nullbefund SCHLIESST den Term, er wiederholt nicht bloss den ersten.
#
# KOSTEN, vorab benannt: bei w_val != 0 ruft der Tiling-Solver je Kandidat den
# margin_evaluator (tiling_solver.rs:1648) -- also Netz-Aufrufe, die bei w_val
# = 0 nicht stattfinden. Die Arme sind darum langsamer als die Basislinie;
# laufzeit.s_je_partie steht in jedem Artefakt und ist Teil der Auswertung.
#
# AUFBAU wie in der Kette davor: beide Seiten dasselbe Modell (amtierender
# Champion v28-b02) auf demselben Wheel, Unterschied GENAU ein Spec-Feld
# (geprueft beim Bau: 13 Felder je Datei, ein Diff), Blockgroesse 5,
# --log-games, SPRT weit (alpha=beta=0,001), damit der Lauf seinen vollen
# Umfang faehrt statt frueh abzubrechen.
#
# ZUERST aber die ANKER-KANTE fuer v29-b03: sie stand schon aus und ist die
# duennste Aufhaengung der Generation (drei Kanten, alle gegen denselben
# Gegner). Sie laeuft vor den A/Bs, weil sie kurz ist (rund 25 min) und weil
# die Elo-Leiter das naechste ist, was der Nutzer ansieht.
#
# KEIN KNOPF INS REZEPT und KEINE PROMOTION aus diesem Skript.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
MODELL=models/alphazero_v28-b02_brierbest.onnx

for f in "$MODELL" models/env_val_off.spec.json models/env_val_05.spec.json \
         models/env_val_10.spec.json tools/night_v29_anchor_edge_b03.sh; do
  [ -f "$f" ] || { echo "ABBRUCH: $f fehlt"; exit 1; }
done

# Gehaertete Wartebedingung (Muster aus tools/night_v29_chain.sh): NUR eine
# klare 0 gilt als frei, jede andere Antwort als belegt. Der Klammer-Trick
# '[p]aired' und der PowerShell-Ausschluss verhindern den Selbsttreffer.
# HAERTUNG 2026-09-16: der Prozess muss PYTHON sein. Ein per Heredoc
# geschriebenes UND im selben Befehl gestartetes Kettenskript traegt seinen
# GANZEN Text in der Kommandozeile des Wrapper-bash -- der Filter fand dort
# `train.py` und wartete auf sich selbst (30 min Stillstand, dazu blockierte
# Nachbarsitzung). Die [t]rain-Klammer hilft dagegen nicht.
maschine_frei() {
  local n
  n=$(powershell -NoProfile -Command "@(Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match '[p]aired_gating\.py|[n]ight_v29_20260914|[f]rozen_referee_match\.py' -and \$_.Name -match 'python' }).Count" 2>/dev/null | tr -d '\r' | tail -1)
  [ "$n" = "0" ]
}

echo "########## ANSCHLUSSKETTE WARTET $(date +%F' '%H:%M:%S)"
while :; do
  if maschine_frei; then
    echo "   Maschine frei ($(date +%H:%M:%S))"
    break
  fi
  echo "   Kette laeuft noch ($(date +%H:%M:%S))"
  sleep 300
done
sleep 20

echo ""
echo "########## 1) ANKER-KANTE v29-b03 $(date +%F' '%H:%M:%S)"
bash tools/night_v29_anchor_edge_b03.sh
echo "   Anker-Kante Exit $? ($(date +%H:%M:%S))"

lauf () {  # name specA specB seed maxpairs
  local NAME="$1" SA="$2" SB="$3" SEED="$4" PAIRS="$5"
  local OUT="$ART/${NAME}_s${SEED}.json"
  echo ""
  echo "===== $NAME (Seed $SEED, $PAIRS Paare) $(date +%F' '%H:%M:%S)"
  python -X utf8 -u tools/paired_gating.py \
    --model-a "$MODELL" --spec-a "$SA" \
    --model-b "$MODELL" --spec-b "$SB" \
    --name-a "${NAME}_a" --name-b "${NAME}_b" \
    --sims-a 400 --sims-b 400 --c-puct 1.5 \
    --block-size 5 --max-pairs "$PAIRS" --sprt-alpha 0.001 --sprt-beta 0.001 \
    --seed "$SEED" --threads 10 --log-games \
    --no-promote-winner --out "$OUT"
  echo "   Exit $? ($(date +%H:%M:%S))"
  python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT"
  python -X utf8 -u tools/plate_points_from_arena.py "$OUT" --block 5 \
    --out "$ART/plate_points_${NAME}_s${SEED}.json"
  echo "   Kennzahlen Exit $? ($(date +%H:%M:%S))"
}

# ACHTUNG BEIM LESEN: die a-Seite traegt den KNOPF, die b-Seite ist die
# Basislinie. Gewinnt a, traegt der Term.
echo ""
echo "########## 2) Value-Anteil im Tiling, Dosis 0,5 $(date +%F' '%H:%M:%S)"
lauf env_val_05_vs_off models/env_val_05.spec.json models/env_val_off.spec.json 20261098 80

echo ""
echo "########## 3) Value-Anteil im Tiling, Dosis 1,0 $(date +%F' '%H:%M:%S)"
lauf env_val_10_vs_off models/env_val_10.spec.json models/env_val_off.spec.json 20261099 80

echo ""
echo "########## ANSCHLUSSKETTE FERTIG $(date +%F' '%H:%M:%S)"
echo "   Faellig danach: Anker-Kante ins Register (tools/elo_tracker.py add,"
echo "   OHNE --early-stop, Cross-Aera-Vermerk), Verdikt zu beiden Dosen nach"
echo "   PREREG_geometric_envelope.md par.8.6b, Zeile-1-Kopf und STATUS im"
echo "   selben Zug, dann tools/generate_prereg_index.py."
echo "   Und in die Auswertung gehoert laufzeit.s_je_partie: die Arme rufen"
echo "   den margin_evaluator je Tiling-Kandidat, die Basislinie nicht."
