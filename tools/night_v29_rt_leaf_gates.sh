#!/usr/bin/env bash
# Fahrplan 35 und 36: Kostentor und A/B fuer Variante B des Rundenuebergangs
# (PREREG_round_transition_search_sampling.md par.5 Schritt 1 und 2, par.9, par.17.5 Punkt 2/3).
#
# KOSTENTOR (Nr. 35), Muster K4 (PREREG_round_estimate_leaf_term.md par.7b, night_v29_20260914.sh):
# zwei Laeufe mit beidseits GLEICHER Spec, einmal Knopf an, einmal aus, je 20 Paare = 40 Partien;
# Messgroesse laufzeit.s_je_partie, Schwelle +25 Prozent (par.4.1). Dazu aus den Logs die
# [rt_leaf]-Zeile: Anteil pseudo-terminaler Blaetter je Suche (par.17.5 Punkt 3).
# EIN GERISSENES TOR BEENDET DEN ARM -- dann laeuft das A/B trotzdem NICHT (Stopp-Punkt Nutzer).
#
# A/B (Nr. 36): DASSELBE Netz gegen sich selbst, Knopf an gegen aus, 200 Paare, Blockgroesse 5,
# ohne Frueh-Stopp (alpha = beta = 0,001), --log-games. Netz = der amtierende Champion
# v28-b02_brierbest (par.5 Schritt 2 "dasselbe Netz gegen sich selbst"; par.9 nennt
# "v29-b01" -- das war die Erwartung vom 2026-09-12, Champion ist geblieben v28-b02).
#
# NEBENLAST: dieses Skript ist eine Wanduhr-Messung und laeuft nur, wenn kein anderer
# CPU-Auftrag laeuft (Cache-Bau, Arena, cargo/maturin, Sonden). Ein GPU-Training (train.py)
# daneben ist erlaubt (docs/working_rules.md, Auslastung) und wird NICHT abgewartet.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
MODELL=models/alphazero_v28-b02_brierbest.onnx
ON=models/rt_leaf_on.spec.json
OFF=models/rt_leaf_off.spec.json
for f in "$MODELL" "$ON" "$OFF"; do [ -f "$f" ] || { echo "ABBRUCH: $f fehlt"; exit 1; }; done

cpu_frei() {
  local n
  n=$(powershell -NoProfile -Command "@(Get-CimInstance Win32_Process | Where-Object { (\$_.CommandLine -match '[p]aired_gating\.py|[f]rozen_referee_match\.py|[b]uild_cache|[w]indow_train_split|[c]ounterfactual_tiling|[o]ffline_diagnosis|[d]ead_unit_probe|[m]aturin' -and \$_.Name -match 'python') -or \$_.Name -match '^(cargo|rustc)' }).Count" 2>/dev/null | tr -d '\r' | tail -1)
  [ "$n" = "0" ]
}
echo "########## RT-LEAF-TORE WARTEN $(date +%F' '%H:%M:%S)"
while :; do
  cpu_frei && { echo "   CPU frei ($(date +%H:%M:%S))"; break; }
  echo "   belegt ($(date +%H:%M:%S))"; sleep 120
done
sleep 20

lauf () {  # name specA specB seed maxpairs
  local NAME=$1 SA=$2 SB=$3 SEED=$4 MP=$5
  local OUT="$ART/${NAME}_s${SEED}.json"
  echo ""
  echo "===== $NAME Seed $SEED, $MP Paare $(date +%F' '%H:%M:%S)"
  python -X utf8 -u tools/paired_gating.py \
    --model-a "$MODELL" --spec-a "$SA" \
    --model-b "$MODELL" --spec-b "$SB" \
    --name-a "${NAME}_a" --name-b "${NAME}_b" \
    --sims-a 400 --sims-b 400 --c-puct 1.5 \
    --block-size 5 --max-pairs "$MP" --sprt-alpha 0.001 --sprt-beta 0.001 \
    --seed "$SEED" --threads 10 --log-games --no-promote-winner --out "$OUT"
  echo "   Exit $? ($(date +%H:%M:%S))"
  python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT"
  python -X utf8 -u tools/plate_points_from_arena.py "$OUT" --block 5 --out "$ART/plate_points_${NAME}_s${SEED}.json"
}

echo ""
echo "== 1) Kostentor Nr. 35: beide Seiten gleich, an gegen aus, je 20 Paare"
lauf rt_leaf_kosten_mit  "$ON"  "$ON"  20261150 20
lauf rt_leaf_kosten_ohne "$OFF" "$OFF" 20261151 20

python -X utf8 - <<'EOF'
import json, re, glob
def sjp(p): return json.load(open(p, encoding="utf-8"))["laufzeit"]["s_je_partie"]
mit = sjp("evaluations/artifacts/rt_leaf_kosten_mit_s20261150.json")
ohne = sjp("evaluations/artifacts/rt_leaf_kosten_ohne_s20261151.json")
auf = (mit / ohne - 1.0) * 100.0
print(f"KOSTENTOR: mit {mit:.3f} s je Partie, ohne {ohne:.3f} s je Partie, Aufschlag {auf:+.1f} Prozent (Schwelle +25)")
d = json.load(open("evaluations/artifacts/rt_leaf_kosten_mit_s20261150.json", encoding="utf-8"))
rx = re.compile(r"\[rt_leaf\] leaves=(\d+) pseudo=(\d+) applied=(\d+)")
L = P = A = 0; n = 0
for g in d.get("games", []):
    for line in g.get("log", []):
        m = rx.search(line)
        if m:
            L += int(m.group(1)); P += int(m.group(2)); A += int(m.group(3)); n += 1
if L:
    print(f"[rt_leaf] Zeilen {n}: Blaetter {L}, pseudo-terminal {P} ({P/L*100:.2f} Prozent), angewandt {A}")
else:
    print("[rt_leaf]-Zeile im Log nicht gefunden -- Format pruefen (self_play.rs)")
open("evaluations/artifacts/rt_leaf_kostentor_verdikt.txt", "w", encoding="utf-8").write(
    f"mit={mit}\nohne={ohne}\naufschlag_prozent={auf}\nleaves={L}\npseudo={P}\napplied={A}\n")
raise SystemExit(0 if auf <= 25.0 else 3)
EOF
RC=$?
if [ "$RC" != "0" ]; then
  echo "########## KOSTENTOR GERISSEN (Exit $RC) -- A/B NICHT gestartet, Nutzer-Entscheid $(date +%H:%M:%S)"
  exit 3
fi

echo ""
echo "== 2) A/B Nr. 36: Champion mit gegen ohne Knopf, 200 Paare ohne Frueh-Stopp"
lauf rt_leaf_on_vs_off "$ON" "$OFF" 20261152 200

echo ""
echo "########## RT-LEAF-TORE FERTIG $(date +%F' '%H:%M:%S)"
echo "   Faellig danach: Verdikt par.5 (Siegquote und Punktemarge auf Block-Ebene), sechs"
echo "   Kennzahlen, Plattenpunkte je Kriterium, Registrierung par.17.8, Fahrplan 35/36."
