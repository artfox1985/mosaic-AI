#!/usr/bin/env bash
# K6 "Spezial-Freischaltungs-Fortschritt": Bau-Tore, Kostentor und A/B
# (PREREG_special_tile_yield.md par.13, Zuschnitt 13.1, Messkette 13.2, Baustand 13.3;
# Nutzer 2026-09-17: "lass es bauen und takte es ein").
#
# Der Knopf ist ein additiver Blattterm im NETZ-Blattpfad:
#   shift = special_unlock_w * (U(0) - U(1)) / 18,
#   U = scoring::unlock_progress_beta(player, state.scoring_tile_ids, special_unlock_beta)
# Nullsumme, beide Seiten auf [0,1] geklammert, direkt hinter dem K4-Term. Bei w = 0
# wird der Zweig nicht betreten (bitidentisch); die Heuristik und der Elo-Anker lesen
# den Knopf strukturell nicht (er lebt in SearchConfig, die der Heuristik-Pfad nicht hat).
#
# VORAUSSETZUNG, die der KOORDINATOR VOR dem Start von Hand herstellt: das Wheel ist
# NACH der K6-Aenderung neu gebaut (maturin). Stufe 0 prueft das und bricht sonst ab.
#
# NEBENLAST: jede Stufe ist ein CPU-Auftrag und wartet auf eine freie Maschine. Ein
# GPU-Training daneben ist erlaubt (docs/working_rules.md) und laesst sich mit
# MOSAIC_CHAIN_NO_WAIT=1 uebersteuern. Keine Pipe und keine Umleitung hinter den langen
# Laeufen (CLAUDE.md).
#
# STOPP-PUNKTE (Nutzer-Entscheid, nichts reparieren): Wheel nicht neu gebaut, Manifest
# ohne das Feld, Anker-Drift oder -Konservierung ROT, gerissenes Kostentor.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
WHEEL=engine/target/wheels/mosaic_rust-0.1.0-cp314-cp314-win_amd64.whl
QUELLE=engine/src/net_mcts.rs
ANKER=models/frozen_heuristics/hv4_anchor
MODELL=models/alphazero_v28-b02_brierbest.onnx
W050=models/k6_w050.spec.json
W025=models/k6_w025.spec.json
OFF=models/k6_off.spec.json
SEED_AB=20261210
SEED_AB_KLEIN=20261211
OUT_AB="$ART/k6_w050_vs_off_s${SEED_AB}.json"
# Referenz des Kostentors: 11,5 s je Partie, EXKLUSIV gemessen (Tor 1 b08 gegen b03,
# je 200 Paare mit Logs, 10 Threads -- docs/measured_runtimes.md Zeile 182). Die sonst
# uebliche Referenz "der Aus-Arm desselben Laufs" gibt es hier NICHT: das Kostentor ist
# EIN Lauf mit beiden Seiten, seine s_je_partie mischt an und aus.
KOSTEN_REF_S_JE_PARTIE=11.5
KOSTEN_SCHWELLE=25

echo "########## K6-KETTE (Spezial-Freischaltungs-Fortschritt) START $(date +%F' '%H:%M:%S)"

cpu_frei() {
  local n
  n=$(powershell -NoProfile -Command "@(Get-CimInstance Win32_Process | Where-Object { (\$_.CommandLine -match '[t]rain\.py|[p]aired_gating\.py|[f]rozen_referee_match\.py|[b]uild_cache|[c]ounterfactual_tiling|[o]ffline_diagnosis|[d]ead_unit_probe|[m]aturin|[w]indow_train_split' -and \$_.Name -match 'python') -or \$_.Name -match '^(cargo|rustc)' }).Count" 2>/dev/null | tr -d '\r' | tail -1)
  [ "$n" = "0" ]
}
warte_frei() {
  echo "########## K6-KETTE WARTET ($1) $(date +%F' '%H:%M:%S)"
  while :; do
    cpu_frei && { echo "   Maschine frei ($(date +%H:%M:%S))"; break; }
    echo "   belegt ($(date +%H:%M:%S))"; sleep 120
  done
  sleep 20
}
# MOSAIC_CHAIN_NO_WAIT=1: Start neben einem GPU-Training als der EINE erlaubte CPU-Auftrag
# (CLAUDE.md, Praezisierung 2026-08-31); der Prozessfilter oben wuerde sonst auf train.py warten.
warte_oder_weiter() {
  if [ "${MOSAIC_CHAIN_NO_WAIT:-0}" = "1" ]; then
    echo "   Warteschleife uebersprungen (MOSAIC_CHAIN_NO_WAIT=1, GPU-Training daneben erlaubt) $(date +%H:%M:%S)"
  else
    warte_frei "$1"
  fi
}

echo ""
echo "== 0) Vorbedingungen $(date +%H:%M:%S)"
grep -q special_unlock_w "$QUELLE" || {
  echo "ABBRUCH: Knopf special_unlock_w fehlt in $QUELLE (Quellstand ohne par.13.3)"
  exit 2
}
for f in "$WHEEL" "$MODELL" "$W050" "$W025" "$OFF"; do
  [ -f "$f" ] || { echo "ABBRUCH: $f fehlt"; exit 1; }
done
[ -d "$ANKER" ] || { echo "ABBRUCH: Anker-Artefakt $ANKER fehlt"; exit 1; }
[ "$WHEEL" -nt "$QUELLE" ] || {
  echo "ABBRUCH: Wheel nicht neu gebaut -- $WHEEL ist NICHT neuer als $QUELLE."
  echo "         Ohne Neubau traegt das installierte Wheel den Knopf nicht, die drei"
  echo "         Spec-Dateien wuerden als 'unbekanntes Feld' hart abgewiesen, und beide"
  echo "         Arme waeren derselbe Spieler."
  exit 2
}
ls -l "$WHEEL" "$QUELLE"

warte_oder_weiter "Wheel-Installation (pip scheitert, solange ein Prozess das .pyd haelt)"

echo ""
echo "== 1) Wheel installieren und Manifest-Export pruefen $(date +%F' '%H:%M:%S)"
python -X utf8 -m pip install --force-reinstall --no-deps "$WHEEL"
RC=$?; echo "   pip Exit $RC ($(date +%H:%M:%S))"
[ "$RC" = "0" ] || { echo "STOPP: Wheel-Installation gescheitert"; exit 10; }
python -X utf8 -u - <<'EOF'
import json, sys
import mosaic_rust
cfg = json.loads(mosaic_rust.engine_config_json())   # engine/src/lib.rs, Felder special_unlock_*
fehlt = [k for k in ("special_unlock_w", "special_unlock_beta") if k not in cfg]
print(f"   engine_config_json: special_unlock_w={cfg.get('special_unlock_w')}  "
      f"special_unlock_beta={cfg.get('special_unlock_beta')}")
print(f"   contract_hash={cfg['contract_hash']}  engine_version={cfg['engine_version']}")
if fehlt:
    print(f"STOPP: Manifest-Export ohne {fehlt} -- altes Wheel installiert?")
    sys.exit(11)
# Der Default MUSS 0 sein (Zusage par.13.1: aus, bitidentisch).
if float(cfg["special_unlock_w"]) != 0.0:
    print(f"STOPP: special_unlock_w ist per Default {cfg['special_unlock_w']}, erwartet 0.0")
    sys.exit(12)
# Und die drei Spec-Dateien muessen mit diesem Wheel laden.
for p in ("models/k6_w050.spec.json", "models/k6_w025.spec.json", "models/k6_off.spec.json"):
    d = json.load(open(p, encoding="utf-8"))
    print(f"   {p}: special_unlock_w={d['special_unlock_w']}  Felder={len(d)}")
sys.exit(0)
EOF
RC=$?; [ "$RC" = "0" ] || { echo "STOPP: Manifest-Pruefung Exit $RC"; exit "$RC"; }

echo ""
echo "== 2) Anker-Invarianz (Skill mosaic-anchor-invariance) $(date +%F' '%H:%M:%S)"
echo "   2a) DRIFT: spielt der heutige Code hv4 noch wie das Artefakt? (Kosten gemessen 22,2 s)"
python -X utf8 -u tools/verify_frozen_heuristic.py --artifact-dir "$ANKER" \
  --out "$ART/anchor_v2_drift_live_wheel_20260917_k6.json"
RC=$?; echo "   Drift Exit $RC ($(date +%H:%M:%S))"
[ "$RC" = "0" ] || { echo "STOPP: Anker-DRIFT ROT -- Nutzer-Entscheid (neues Leitersegment oder Aenderung zurueck), KEINE Reparatur"; exit 20; }
echo "   2b) KONSERVIERUNG: spielt das Artefakt noch wie am Einfriertag? (Kosten gemessen 13,4 s)"
python -X utf8 -u tools/verify_frozen_heuristic.py --artifact-dir "$ANKER" --venv \
  --out "$ART/anchor_v2_conservation_20260917_k6.json"
RC=$?; echo "   Konservierung Exit $RC ($(date +%H:%M:%S))"
[ "$RC" = "0" ] || { echo "STOPP: Anker-KONSERVIERUNG ROT -- Umgebungsdrift, Nutzer-Entscheid"; exit 21; }

warte_oder_weiter "Kostentor"
echo ""
echo "== 3) Kostentor par.13.2 Punkt 2: was kostet der Blattterm? $(date +%F' '%H:%M:%S)"
echo "   Form: Champion gegen sich selbst, k6_w050 (A) gegen k6_off (B), 2 x 20 Paare = 80 Partien."
echo "   Gemessen wird allein die Wanduhr je Partie; die Siegquote ist hier bedeutungslos."
echo "   Erwartung par.13.1: weit unter der Schwelle -- kein Loeser, kein Netzaufruf."
for S in 20261200 20261201; do
  OUT="$ART/k6_kosten_s${S}.json"
  echo ""
  echo "===== Kostenlauf Seed $S $(date +%F' '%H:%M:%S)"
  python -X utf8 -u tools/paired_gating.py \
    --model-a "$MODELL" --spec-a "$W050" --model-b "$MODELL" --spec-b "$OFF" \
    --name-a k6_kosten_w050 --name-b k6_kosten_off \
    --sims-a 400 --sims-b 400 --c-puct 1.5 \
    --block-size 5 --max-pairs 20 --sprt-alpha 0.001 --sprt-beta 0.001 \
    --seed "$S" --threads 10 --log-games --no-promote-winner --out "$OUT"
  echo "   Exit $? ($(date +%H:%M:%S))"
done
python -X utf8 -u - <<EOF
import json, sys
def sjp(p):
    return json.load(open(p, encoding="utf-8"))["laufzeit"]["s_je_partie"]
neu = [sjp(f"evaluations/artifacts/k6_kosten_s{s}.json") for s in (20261200, 20261201)]
mittel = sum(neu) / len(neu)
# Referenz: 11,5 s je Partie, exklusiv gemessen (Tor 1 b08 gegen b03, docs/measured_runtimes.md
# Zeile 182). Der sonst uebliche "Aus-Arm desselben Laufs" ist hier nicht verfuegbar: das
# Kostentor ist EIN Lauf mit beiden Seiten, seine s_je_partie mischt an und aus.
ref = $KOSTEN_REF_S_JE_PARTIE
schwelle = $KOSTEN_SCHWELLE
auf = (mittel / ref - 1.0) * 100.0
print(f"KOSTENTOR K6: neu {neu[0]:.3f} / {neu[1]:.3f} s je Partie, Mittel {mittel:.3f}")
print(f"   gegen Referenz {ref} s je Partie (exklusiv): Aufschlag {auf:+.1f} Prozent (Schwelle +{schwelle})")
open("evaluations/artifacts/k6_kostentor_verdikt.txt", "w", encoding="utf-8").write(
    "prereg=PREREG_special_tile_yield.md par.13.2 Punkt 2\n"
    "form=Champion gegen sich selbst, k6_w050 gegen k6_off, 2 x 20 Paare, 10 Threads, --log-games\n"
    f"neu_s20261200={neu[0]}\nneu_s20261201={neu[1]}\nneu_mittel={mittel}\n"
    f"referenz_s_je_partie={ref}\n"
    "referenz_quelle=docs/measured_runtimes.md Zeile 182 (Tor 1 b08 gegen b03, exklusiv, 10 Threads)\n"
    "referenz_hinweis=kein Aus-Arm desselben Laufs moeglich (ein Lauf, beide Seiten)\n"
    f"aufschlag_prozent={auf}\n"
    f"schwelle_prozent={schwelle}\nverdikt={'HAELT' if auf <= schwelle else 'GERISSEN'}\n")
raise SystemExit(0 if auf <= schwelle else 3)
EOF
RC=$?
if [ "$RC" != "0" ]; then
  echo "########## KOSTENTOR GERISSEN (Exit $RC) -- A/B NICHT gestartet."
  echo "   Nutzer-Entscheid (par.13.2 Punkt 2). Verdikt: $ART/k6_kostentor_verdikt.txt"
  exit 3
fi
echo "   Kostentor HAELT ($(date +%H:%M:%S))"

warte_oder_weiter "A/B Dosis 0,5"
echo ""
echo "== 4) A/B Dosis 0,5 par.13.2 Punkt 3: Champion mit gegen ohne K6, 200 Paare, Seed $SEED_AB $(date +%F' '%H:%M:%S)"
echo "   A = special_unlock_w 0,5 ($W050), B = aus ($OFF); beide Arme tragen dieselbe Feldmenge."
python -X utf8 -u tools/paired_gating.py \
  --model-a "$MODELL" --spec-a "$W050" \
  --model-b "$MODELL" --spec-b "$OFF" \
  --name-a k6_w050 --name-b k6_off \
  --sims-a 400 --sims-b 400 --c-puct 1.5 \
  --block-size 5 --max-pairs 200 --sprt-alpha 0.001 --sprt-beta 0.001 \
  --seed "$SEED_AB" --threads 10 --log-games --no-promote-winner --out "$OUT_AB"
echo "   Exit $? ($(date +%H:%M:%S))"

echo ""
echo "== 4b) Standard-Kennzahlen: Spalten und Plattenpunkte je Kriterium $(date +%H:%M:%S)"
python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT_AB"
python -X utf8 -u tools/plate_points_from_arena.py "$OUT_AB" --block 5 \
  --out "$ART/plate_points_k6_w050_s${SEED_AB}.json"

echo ""
echo "== 5) Dosis 0,25 nur, wenn 0,5 SCHADET (par.13.2 Punkt 3) $(date +%H:%M:%S)"
python -X utf8 -u - <<EOF
import json, sys
d = json.load(open("$OUT_AB", encoding="utf-8"))
a, b, p = d["a_wins_total"], d["b_wins_total"], d["report_mcnemar_p"]
print(f"   A (w=0,5) {a} : {b} B (aus), McNemar p={p:.4f}")
schadet = (a < b) and (p < 0.05)
print(f"   schadet={schadet} (Bedingung: A < B UND p < 0,05)")
sys.exit(0 if schadet else 7)
EOF
RC=$?
if [ "$RC" = "0" ]; then
  warte_oder_weiter "A/B Dosis 0,25"
  OUT_KLEIN="$ART/k6_w025_vs_off_s${SEED_AB_KLEIN}.json"
  echo ""
  echo "===== A/B Dosis 0,25, 200 Paare, Seed $SEED_AB_KLEIN $(date +%F' '%H:%M:%S)"
  python -X utf8 -u tools/paired_gating.py \
    --model-a "$MODELL" --spec-a "$W025" \
    --model-b "$MODELL" --spec-b "$OFF" \
    --name-a k6_w025 --name-b k6_off \
    --sims-a 400 --sims-b 400 --c-puct 1.5 \
    --block-size 5 --max-pairs 200 --sprt-alpha 0.001 --sprt-beta 0.001 \
    --seed "$SEED_AB_KLEIN" --threads 10 --log-games --no-promote-winner --out "$OUT_KLEIN"
  echo "   Exit $? ($(date +%H:%M:%S))"
  python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$OUT_KLEIN"
  python -X utf8 -u tools/plate_points_from_arena.py "$OUT_KLEIN" --block 5 \
    --out "$ART/plate_points_k6_w025_s${SEED_AB_KLEIN}.json"
elif [ "$RC" = "7" ]; then
  echo "   Dosis 0,25 entfaellt (0,5 schadet nicht im Sinne von par.13.2 Punkt 3)"
else
  echo "   WARNUNG: Lesbarkeit des A/B-Artefakts unklar (Exit $RC) -- Dosis 0,25 nicht gestartet"
fi

echo ""
echo "########## K6-KETTE FERTIG $(date +%F' '%H:%M:%S)"
echo "   Faellig danach:"
echo "   1. Verdikt nach par.13.2 Punkt 5 (a-d): Siege auf BLOCK-Ebene plus Punktemarge,"
echo "      dazu der PRIMAERKANAL par.13.2 Punkt 4 -- belegte Spezialfelder je Partie UND"
echo "      die Plattenpunkte des Kriteriums 'Spezialfelder' aus plate_points_k6_*.json."
echo "      (d) 'Spezialfelder unbewegt' heisst Diagnose VOR jeder Dosisaenderung."
echo "   2. Die K4-Falle zuerst ansehen (par.13.1): Strafleiste und volle Spalten je Partie --"
echo "      ein rundenscore-gieriger Term zeigt sich dort, bevor er sich in den Siegen zeigt."
echo "   3. Sechs Standard-Kennzahlen (CLAUDE.md) je Seite und als Differenz."
echo "   4. Laufzeiten nach docs/measured_runtimes.md: Kostentor je Seed, A/B je Dosis,"
echo "      plus das Verdikt aus $ART/k6_kostentor_verdikt.txt."
echo "   5. Registrierung in PREREG_special_tile_yield.md par.13 samt Zeile-1-Kopf,"
echo "      danach python -X utf8 tools/generate_prereg_index.py."
