#!/usr/bin/env bash
# CHAMPION-KANTEN fuer die beiden v29-Kandidaten v29-b07 und v29-b09.
#
# AUFTRAG (Nutzer 2026-09-17, STATUS Abschnitt 6 Punkt 18): "dann warten wir auf b07 und fahren
# mit dem staerksten arm. v29-b09 nehmen wir ebenfalls mit". Beide Kandidaten bekommen die DREI
# Aufhaengungen der Promotions-Checkliste (docs/promotion_checklist.md Punkte 2-4):
#
#   a) Gating gegen Champion-1 v28-b02_brierbest        (Checkliste Punkt 2)
#   b) Anker-Kante gegen hv4_anchor @150 c_puct 0,3      (Checkliste Punkt 3, festes n=150)
#   c) Champion-2-Kante gegen das Artefakt v27-b01 @400  (Checkliste Punkt 4)
#
# WARUM DREI: die Checkliste verlangt drei VERSCHIEDENE Nachbarn (Punkt 4: "ohne ihn ruht die
# Elo-Schaetzung auf zu wenigen Kanten"). v29-b03 hing bis zur Anker-Kante an einem einzigen
# Gegner (STATUS Abschnitt 1, "Anker-Kante fuer v29-b03: 128:22").
#
# FORM DER STUFEN, jede aus einem Praezedenzfall uebernommen, nicht erfunden:
#
# * Gating: Flags wie tools/night_v29_b08_head_pair.sh Stufe 4 und wie die b03-Kante gegen den
#   Champion (PREREG_v29_window.md par.9, "Flags bitgleich zur b01-Kante": Blockgroesse 5,
#   max-pairs 200, sims 400, c_puct 1,5, Champion-Spec BEIDSEITS). Unterschied zu par.9: dort
#   liefen alpha = beta = 0,05, drei Seeds brachen frueh ab und die Siegquoten sind nach oben
#   verzerrt. Hier alpha = beta = 0,001 -- der SPRT laeuft mit, stoppt praktisch nicht, und die
#   Kante wird ueber den festen Deckel von 200 Paaren gefahren (Muster b08, b09).
# * Anker-Kante: 1:1 der Aufruf aus tools/night_v29_anchor_edge_b03.sh:42-54, der
#   evaluations/artifacts/anchor_edge_v29-b03_vs_hv4_anchor.json erzeugt hat -- nur Modell,
#   Seed-Basis und Ausgabename sind neu. Der Anker laeuft @150 c_puct 0,3, die Netzseite @400
#   c_puct 1,5 mit Champion-Spec, n=150 OHNE Frueh-Stopp, 6 Worker, --force-cross-era
#   (project_anchor_era_rule: das Anker-Wheel wird NIE nachgezogen; der Golden-Selbsttest bleibt
#   an und ist die eigentliche Absicherung).
# * Champion-2-Kante: Form der Kante des amtierenden Champions
#   (evaluations/artifacts/champion2_v28-b02_vs_v26-b01.json: frozen_referee_match, sims_worker
#   400, c_puct_worker 1,5, n_games 150, 6 Prozesse, Cross-Aera; registriert in
#   PREREG_code_cleanup_closeout.md par. "Champion-2-Kante (Promotion Schritt 4)"). n=150 ist
#   damit BELEGT und nicht geschaetzt (auch STATUS Abschnitt 3: "Anker-Kante n=150 /
#   Champion-2-Kante n=150 | rund 22 min / 43 min").
#
# SPEC: beide Kandidaten spielen mit der Champion-Spec models/frozen_champions/v28-b02/spec.json.
# Das ist dieselbe Spec, die par.9 fuer b03 benutzt hat, und sie ist INHALTSGLEICH mit
# models/frozen_champions/v27-b01/spec.json (Feld fuer Feld verglichen 2026-09-17) -- fuer die
# Champion-2-Kante gibt es also keine Spec-Wahl, die das Ergebnis verschiebt.
#
# INPUT_SIZE: beide Kandidaten sind 884 (config.py:49), das Artefakt v27-b01 ist 744
# (models/frozen_champions/v27-b01/manifest.json, Feld input_size). Ein Fallback-Flag ist NICHT
# noetig: tools/frozen_referee_match.py kennt keinen input_size-Schalter (grep ohne Treffer), und
# die Engine schneidet den Flachteil auf die Modellbreite (engine/src/net.rs:979
# split_planes_flat_batch_src -- Planes ab 0 auf die Modellbreite, Flachteil ab der QUELL-Grenze).
# Jede Seite laeuft ausserdem in ihrem eigenen Wheel; das Artefakt bringt seines mit.
#
# SEEDS (Ueberschneidungen bewusst gewaehlt oder bewusst vermieden):
#   Gating      b07 20261230 / 20261231     b09 20261240 / 20261241   (aus dem Auftrag)
#   Anker       b07 Seed-Basis 20261600     b09 Seed-Basis 20261700   (HIER gewaehlt, damit die
#               je 150 fortlaufenden Seeds nicht in die Spanne der b03-Anker-Kante fallen:
#               20261097 bis 20261246)
#   Champion-2  b07 Seed-Basis 20261250     b09 Seed-Basis 20261251   (aus dem Auftrag; die
#               beiden Spannen 20261250-20261399 und 20261251-20261400 teilen 149 von 150 Seeds,
#               die zwei Kanten sind also faktisch gepaart -- gewollt lesbar, nicht zufaellig)
#
# KENNZAHLEN: die sechs Standard-Kennzahlen (CLAUDE.md) laufen auf den Gating-Artefakten mit
# tools/probes/arena_column_probe.py --artifact und tools/plate_points_from_arena.py --block 5.
# Auf den beiden frozen_referee_match-Artefakten laufen sie NICHT, und das ist kein Weglassen:
# arena_column_probe braucht je Partie die Felder names/first_player/game_seed aus --log-games
# (tools/probes/arena_column_probe.py, Docstring _replay_end_state), frozen_referee_match
# schreibt je Partie nur scores/winner/steps/seed/first_player/board_a/log (nachgesehen am
# Artefakt anchor_edge_v29-b03_vs_hv4_anchor.json). Was aus diesen Artefakten ABLESBAR ist --
# eigene Punkte und Margin je Seite -- rechnet die Kette selbst (Stufe Z) aus games[].scores und
# games[].board_a; Reihen-, Spalten- und Strafleistenauslastung bleiben dort unmessbar.
#
# LASTREGEL: die Kette wartet, bis (a) die CPU frei ist UND (b) das Artefakt des K6-A/B
# (k6_w025_vs_off_s20261211.json) existiert. Ohne (b) wuerde sie neben der WARTENDEN K6-Kette
# starten und ihr die Maschine wegnehmen. Danach laeuft alles streng seriell und exklusiv.
# MOSAIC_CHAIN_NO_WAIT=1 ueberspringt die Warteschleife (nur fuer den Fall, dass ein Mensch die
# Reihenfolge selbst sicherstellt).
#
# KEINE PROMOTION, KEIN REGISTER-SCHREIBEN AUS DIESER KETTE: --no-promote-winner ist gesetzt, und
# die elo_tracker-Zeilen werden am Ende nur GEDRUCKT. Der Koordinator prueft die Zahlen und traegt
# ein (Regel 0: Agenten- und Werkzeugbefunde sind Behauptungen, bis die tragende Zahl nachgesehen
# ist). Der Promotions-Entscheid selbst ist ein Nutzer-Entscheid (STATUS Abschnitt 6 Punkt 18).
#
# KOSTEN (Planung):
#   Gating 200 Paare @400, 10 Threads, --log-games: GEMESSEN 4.606,9 s = 77 min
#     (evaluations/artifacts/tor1_v29-b08_vs_b03_s20261160.json, laufzeit.wanduhr_s);
#     Planungsgroesse STATUS Abschnitt 3: 86-91 min. Vier Laeufe.
#   Anker-Kante n=150, 6 Worker: GEMESSEN 1.292,8 s = 22 min (anchor_edge_v29-b03, elapsed_s);
#     docs/measured_runtimes.md:197 nennt fuer Segment-2-Anker-Kanten 1.441-1.491 s. Zwei Laeufe.
#   Champion-2-Kante n=150, 6 Prozesse: GEMESSEN 2.516 s (docs/measured_runtimes.md:202,
#     v28-b02 gegen v26-b01) und 2.578 s (Zeile 241, gegen v25-b01). Zwei Laeufe.
#   SUMME: ANNAHME rund 7,5 bis 8 h Wanduhr, exklusiv. Der 884er Eingang ist in keiner dieser
#     gemessenen Zahlen enthalten -- dass er die Kanten nicht teurer macht, ist ANNAHME.
#
# Registriert in evaluations/PREREG_minimal_strength_core.md par.10.9 (geschrieben 2026-09-17).
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
ART=evaluations/artifacts
CHAMP=models/alphazero_v28-b02_brierbest.onnx
CHAMP_SPEC=models/frozen_champions/v28-b02/spec.json
ANCHOR_DIR=models/frozen_heuristics/hv4_anchor
CHAMP2_DIR=models/frozen_champions/v27-b01
K6_ARTIFACT="$ART/k6_w025_vs_off_s20261211.json"

echo "########## CHAMPION-KANTEN v29 (b07, b09) $(date +%F' '%H:%M:%S)"

# ---------------------------------------------------------------- Stufe 0: Vorbedingungen
echo ""
echo "== 0) Vorbedingungen $(date +%H:%M:%S)"
FAIL=0
for f in \
  models/alphazero_v29-b07_brierbest.onnx \
  models/alphazero_v29-b09_brierbest.onnx \
  "$CHAMP" "$CHAMP_SPEC" \
  "$CHAMP2_DIR/model.onnx" "$CHAMP2_DIR/spec.json" "$CHAMP2_DIR/manifest.json" \
  "$ANCHOR_DIR/spec.json" "$ANCHOR_DIR/manifest.json" \
  tools/paired_gating.py tools/frozen_referee_match.py \
  tools/probes/arena_column_probe.py tools/plate_points_from_arena.py
do
  if [ -f "$f" ]; then echo "   ok   $f"; else echo "   FEHLT $f"; FAIL=1; fi
done
for d in "$ANCHOR_DIR" "$ANCHOR_DIR/venv" "$CHAMP2_DIR" "$CHAMP2_DIR/venv"; do
  if [ -d "$d" ]; then echo "   ok   $d/"; else echo "   FEHLT $d/"; FAIL=1; fi
done
[ "$FAIL" = "0" ] || { echo "ABBRUCH: Vorbedingung fehlt -- kein stiller Leerlauf."; exit 1; }

# Das installierte Wheel muss das 884er vom 2026-09-17, 19:37 sein. Probe wie in
# tools/night_k6_w025_ab.sh: nur dieses Wheel kennt special_unlock_w.
python -X utf8 -c "import mosaic_rust, json, sys; d=json.loads(mosaic_rust.engine_config_json()); sys.exit(0 if 'special_unlock_w' in d else 2)" \
  || { echo "ABBRUCH: installiertes Wheel kennt special_unlock_w nicht -- falsches Wheel"; exit 2; }
grep -q "^INPUT_SIZE = 884" config.py \
  || { echo "ABBRUCH: config.py steht nicht auf INPUT_SIZE 884 -- beide Kandidaten sind 884"; exit 3; }
echo "   Wheel-Probe gruen (special_unlock_w), config.py INPUT_SIZE 884"

# ---------------------------------------------------------------- Warten auf die Maschine
cpu_frei() {
  local n
  n=$(powershell -NoProfile -Command "@(Get-CimInstance Win32_Process | Where-Object { (\$_.CommandLine -match '[t]rain\.py|[p]aired_gating\.py|[f]rozen_referee_match\.py|[b]uild_cache|[c]ounterfactual_tiling|[o]ffline_diagnosis|[d]ead_unit_probe|[m]aturin|[w]indow_train_split|[a]rena_column_probe|[p]late_points_from_arena' -and \$_.Name -match 'python') -or \$_.Name -match '^(cargo|rustc)' }).Count" 2>/dev/null | tr -d '\r' | tail -1)
  [ "$n" = "0" ]
}
warte_frei() {
  echo "########## CHAMPION-KANTEN WARTEN ($1) $(date +%F' '%H:%M:%S)"
  while :; do
    local cpu="belegt" k6="fehlt"
    cpu_frei && cpu="frei"
    [ -f "$K6_ARTIFACT" ] && k6="da"
    if [ "$cpu" = "frei" ] && [ "$k6" = "da" ]; then
      echo "   Maschine frei UND K6-Artefakt da ($(date +%H:%M:%S))"; break
    fi
    echo "   CPU $cpu, K6-Artefakt $k6 ($(date +%H:%M:%S))"
    sleep 120
  done
  sleep 20
}

if [ "${MOSAIC_CHAIN_NO_WAIT:-0}" = "1" ]; then
  echo "   Warteschleife uebersprungen (MOSAIC_CHAIN_NO_WAIT=1) $(date +%H:%M:%S)"
else
  warte_frei "Tor 1 v29-b09 gegen b03, danach K6 Dosis 0,25"
fi

# ---------------------------------------------------------------- Stufen je Kandidat
run_gating() {   # $1 Kandidat, $2 Modell, $3 Seed
  local name="$1" model="$2" seed="$3"
  local out="$ART/gating_${name}_vs_v28-b02_s${seed}.json"
  echo ""
  echo "===== a) GATING $name gegen v28-b02, Seed $seed $(date +%F' '%H:%M:%S)"
  python -X utf8 -u tools/paired_gating.py \
    --model-a "$model" --spec-a "$CHAMP_SPEC" \
    --model-b "$CHAMP" --spec-b "$CHAMP_SPEC" \
    --name-a "$name" --name-b v28-b02 \
    --sims-a 400 --sims-b 400 --c-puct 1.5 \
    --block-size 5 --max-pairs 200 --sprt-alpha 0.001 --sprt-beta 0.001 \
    --seed "$seed" --threads 10 --log-games --no-promote-winner --out "$out"
  echo "   Gating Exit $? ($(date +%H:%M:%S))"
  python -X utf8 -u tools/probes/arena_column_probe.py --artifact "$out"
  echo "   Spaltensonde Exit $? ($(date +%H:%M:%S))"
  python -X utf8 -u tools/plate_points_from_arena.py "$out" --block 5 \
    --out "$ART/plate_points_${name}_vs_v28-b02_s${seed}.json"
  echo "   Plattenpunkte Exit $? ($(date +%H:%M:%S))"
}

run_anchor_edge() {   # $1 Kandidat, $2 Modell, $3 Seed-Basis
  local name="$1" model="$2" seed_base="$3"
  local out="$ART/anchor_edge_${name}_vs_hv4_anchor.json"
  echo ""
  echo "===== b) ANKER-KANTE $name gegen hv4_anchor, Seed-Basis $seed_base $(date +%F' '%H:%M:%S)"
  python -X utf8 -u tools/frozen_referee_match.py \
    --artifact-dir "$ANCHOR_DIR" \
    --model-a "$model" --spec-a "$CHAMP_SPEC" \
    --sims-a 400 --c-puct-a 1.5 \
    --sims-worker 150 --c-puct-worker 0.3 \
    --n-games 150 --seed-base "$seed_base" --workers 6 \
    --force-cross-era \
    --out "$out"
  echo "   Anker-Kante Exit $? ($(date +%H:%M:%S))"
}

run_champion2_edge() {   # $1 Kandidat, $2 Modell, $3 Seed-Basis
  local name="$1" model="$2" seed_base="$3"
  local out="$ART/champion2_${name}_vs_v27-b01_s${seed_base}.json"
  echo ""
  echo "===== c) CHAMPION-2-KANTE $name gegen Artefakt v27-b01, Seed-Basis $seed_base $(date +%F' '%H:%M:%S)"
  python -X utf8 -u tools/frozen_referee_match.py \
    --artifact-dir "$CHAMP2_DIR" \
    --model-a "$model" --spec-a "$CHAMP_SPEC" \
    --sims-a 400 --c-puct-a 1.5 \
    --sims-worker 400 --c-puct-worker 1.5 \
    --n-games 150 --seed-base "$seed_base" --workers 6 \
    --force-cross-era \
    --out "$out"
  echo "   Champion-2-Kante Exit $? ($(date +%H:%M:%S))"
}

echo ""
echo "########## KANDIDAT 1 von 2: v29-b07 $(date +%F' '%H:%M:%S)"
run_gating v29-b07 models/alphazero_v29-b07_brierbest.onnx 20261230
run_gating v29-b07 models/alphazero_v29-b07_brierbest.onnx 20261231
run_anchor_edge v29-b07 models/alphazero_v29-b07_brierbest.onnx 20261600
run_champion2_edge v29-b07 models/alphazero_v29-b07_brierbest.onnx 20261250

echo ""
echo "########## KANDIDAT 2 von 2: v29-b09 $(date +%F' '%H:%M:%S)"
run_gating v29-b09 models/alphazero_v29-b09_brierbest.onnx 20261240
run_gating v29-b09 models/alphazero_v29-b09_brierbest.onnx 20261241
run_anchor_edge v29-b09 models/alphazero_v29-b09_brierbest.onnx 20261700
run_champion2_edge v29-b09 models/alphazero_v29-b09_brierbest.onnx 20261251

# ---------------------------------------------------------------- Stufe Z: Zusammenfassung
echo ""
echo "########## Z) ZUSAMMENFASSUNG, LAUFZEITEN UND ELO-ZEILEN $(date +%F' '%H:%M:%S)"
echo "   Die folgenden Zeilen werden NICHT ausgefuehrt. Der Koordinator prueft die Zahlen"
echo "   gegen die Artefakte und traegt sie ein (Regel 0)."
python -X utf8 - "$ART" <<'PY'
import json, sys, pathlib

art = pathlib.Path(sys.argv[1])
KNOBS = "spec:frozen_champions/v28-b02/spec.json"


def load(name):
    p = art / name
    if not p.is_file():
        print(f"   FEHLT: {p} -- Stufe nicht gelaufen?")
        return None
    with p.open(encoding="utf-8") as fh:
        return json.load(fh)


def gating_line(cand, seed):
    name = f"gating_{cand}_vs_v28-b02_s{seed}.json"
    d = load(name)
    if d is None:
        return
    pairs = d.get("done_pairs")
    wa, wb = d.get("a_wins_total"), d.get("b_wins_total")
    n = d.get("n_games_total")
    rt = d.get("laufzeit") or {}
    early = " --early-stop" if isinstance(pairs, int) and pairs < 200 else ""
    print(f"\n-- GATING {cand} Seed {seed}: {wa}:{wb} in {n} Partien ({pairs} Paare), "
          f"SPRT {d.get('sprt_verdict')} LLR {d.get('sprt_llr')}, McNemar p {d.get('report_mcnemar_p')}, "
          f"gepaarte Diff {d.get('mean_pair_diff')} {d.get('ci95')}, "
          f"Punkte {d.get('avg_score_a')} / {d.get('avg_score_b')}, "
          f"Strafleiste {d.get('avg_floor_a')} / {d.get('avg_floor_b')}")
    print(f"   Laufzeit {rt.get('wanduhr_s')} s Wanduhr, {rt.get('s_je_partie')} s je Partie, "
          f"threads {rt.get('threads')}, cpu {rt.get('cpu_s')} s")
    print(f"python tools/elo_tracker.py add --player-a {cand} --sims-a 400 "
          f"--player-b v28-b02 --sims-b 400 --wins-a {wa} --wins-b {wb} --n {n} "
          f"--knobs {KNOBS} --units-from-paired-artifact evaluations/artifacts/{name}{early} "
          f'--comment "Segment 2: {cand} @400 c_puct 1,5 gegen Champion v28-b02_brierbest @400, '
          f"Champion-Spec beidseits, paired_gating Blockgroesse 5, Deckel 200 Paare, "
          f"alpha = beta = 0,001 (SPRT ohne Frueh-Stopp-Wirkung), 10 Threads, Seed {seed}; "
          f"SPRT {d.get('sprt_verdict')}, McNemar p {d.get('report_mcnemar_p')}; "
          f'{rt.get("wanduhr_s")} s"')


def frozen_line(cand, kind, opponent, sims_worker, seed_base, fname):
    d = load(fname)
    if d is None:
        return
    wa, wb = d.get("wins_a"), d.get("wins_b")
    n = d.get("n_games")
    hs = d.get("handshake") or {}
    gold = d.get("golden_selftest") or {}
    scores_a, scores_b = [], []
    for g in d.get("games") or []:
        sc, ba = g.get("scores"), g.get("board_a")
        if isinstance(sc, list) and len(sc) == 2 and ba in (0, 1):
            scores_a.append(sc[ba])
            scores_b.append(sc[1 - ba])
    pa = sum(scores_a) / len(scores_a) if scores_a else float("nan")
    pb = sum(scores_b) / len(scores_b) if scores_b else float("nan")
    el = d.get("elapsed_s")
    per = (el / n) if (el and n) else float("nan")
    print(f"\n-- {kind} {cand} gegen {opponent}: {wa}:{wb} in {n} Partien "
          f"({(wa / n * 100):.1f} Prozent), Punkte {pa:.2f} gegen {pb:.2f}, "
          f"Margin {pa - pb:+.2f} (n = {n} Partien, Grundmenge Partien, Einheit Punkte je Partie)")
    print(f"   Handshake ok={hs.get('ok')} (Artefakt {hs.get('artifact_contract_hash')} gegen Live "
          f"{hs.get('current_contract_hash')}), Golden-Selbsttest ran={gold.get('ran')} "
          f"mismatches={gold.get('mismatches')}")
    print(f"   Laufzeit {el} s, {per:.2f} s je Partie (das Artefakt fuehrt keinen laufzeit-Block, "
          f"nur elapsed_s/s_per_step -- offener Punkt)")
    print(f"python tools/elo_tracker.py add --player-a {cand} --sims-a 400 "
          f"--player-b {opponent} --sims-b {sims_worker} --wins-a {wa} --wins-b {wb} --n {n} "
          f"--knobs {KNOBS} "
          f'--comment "Segment 2: {cand} @400 c_puct 1,5 (Champion-Spec) gegen {opponent}, '
          f"frozen_referee_match 6 Worker, Seed-Basis {seed_base}, {n} Partien OHNE Frueh-Stopp; "
          f"Golden-Selbsttest mismatches {gold.get('mismatches')}, Cross-Aera "
          f"(Artefakt {hs.get('artifact_contract_hash')} gegen Live {hs.get('current_contract_hash')}); "
          f'{el} s"')


for cand, gseeds, anchor_base, c2_base in (
    ("v29-b07", (20261230, 20261231), 20261600, 20261250),
    ("v29-b09", (20261240, 20261241), 20261700, 20261251),
):
    print(f"\n================ {cand}")
    for s in gseeds:
        gating_line(cand, s)
    frozen_line(cand, "ANKER-KANTE", "Heuristik_hv4_anchor", 150, anchor_base,
                f"anchor_edge_{cand}_vs_hv4_anchor.json")
    frozen_line(cand, "CHAMPION-2-KANTE", "v27-b01", 400, c2_base,
                f"champion2_{cand}_vs_v27-b01_s{c2_base}.json")
PY
echo "   Zusammenfassung Exit $? ($(date +%H:%M:%S))"

echo ""
echo "########## CHAMPION-KANTEN FERTIG $(date +%F' '%H:%M:%S)"
echo ""
echo "FAELLIG DANACH (nichts davon macht diese Kette):"
echo " 1. Zahlen gegen die Artefakte pruefen, dann die gedruckten elo_tracker-Zeilen eintragen;"
echo "    --early-stop nur, wo das Gating vor 200 Paaren abbrach. Register ist"
echo "    evaluations/elo_history.csv (Merkregel der Checkliste: Elo-Fragen am Primaerregister)."
echo " 2. Verdikt je Kandidat in evaluations/PREREG_minimal_strength_core.md par.10.9 registrieren,"
echo "    Zeile-1-Kopf im selben Zug, dann python tools/generate_prereg_index.py. STATUS Abschnitt 1"
echo "    und Abschnitt 2 (Champion und Leiter) sowie Punkt 18 in Abschnitt 6 nachziehen."
echo " 3. Sechs Standard-Kennzahlen je Kandidat berichten (Gating-Artefakte tragen alle sechs; die"
echo "    beiden frozen-Kanten nur Punkte und Margin, Begruendung im Kopf dieser Datei)."
echo " 4. Laufzeiten nach docs/measured_runtimes.md nachtragen (vier Gatings, zwei Anker-, zwei"
echo "    Champion-2-Kanten) -- die erste Messung dieser Stufen mit INPUT_SIZE 884."
echo " 5. NUR beim Sieger und NUR auf Nutzer-Entscheid der Promotions-Ablauf"
echo "    (/mosaic-champion-promotion, docs/promotion_checklist.md): Punkt 1 set_champion plus"
echo "    Spec unter dem Champion-Namen, Punkt 5 Pflicht-Diagnostiken (platt_fit,"
echo "    gumbel_scale_calibration, Alt-Set-Brier, R4b) mit 5b Anzeige-Kalibrierung in server.py,"
echo "    5c sigma/Prior-Balance, 5d Netz-Paritaets-Fixture, Punkt 6 STATUS und history, Punkt 7"
echo "    Einfrieren von models/frozen_champions/<neu>/ samt Golden Probe und Referee-Selbsttest."
echo " 6. Der Promotions-Entscheid selbst bleibt Nutzer-Entscheid (STATUS Abschnitt 6 Punkt 18)."
