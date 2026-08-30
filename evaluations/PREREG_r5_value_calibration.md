<!-- STATUS: ENTSCHIEDEN | Frage: Reagiert der Value-/Punkte-Kopf in Runde 5 proportional richtig auf Wertungsplatten-Aenderungen (Task #27)? | Beleg: Unterkalibrierung bestaetigt (Steigung 0,06-0,09 statt ~1; archive Z. ~7065). NACHMESSUNG 2026-08-29 auf v22-b05: Steigung 0,0886 -- Daempfung persistiert auf dem spaltenfaehigen Netz, KEIN Korpus-Artefakt; Ordnung dagegen geheilt (Tau +0,338). Punkte-Kopf 0,989. -->

# Vorregistrierung: Runde-5-Value-/Punkte-Kopf-Kalibrierung gegen exakte Ground Truth

**Angelegt 2026-08-02 (Task #27), VOR dem ersten vollen Lauf.** Nur Design +
Werkzeug + Rauchtest in diesem Schritt (User-Go dafür liegt vor) — der volle
Lauf folgt NACH der Lambda-/PCR-Auswertung, separat freigegeben. Die Regeln
unten dürfen nach Sichtung von Zwischenergebnissen nicht mehr geändert werden
(Präzedenzfall `PREREG_lambda_target.md`).

## Frage

`tools/scoring_tile_sensitivity.py` (2026-07-26) zeigt: der Root-Value über
verschiedene Wertungsplatten-Kombinationen bei FESTEM Zustand streut nur
Ø 0,035–0,043 (`treatment_value_spread_across_combos`, siehe
`evaluations/artifacts/scoring_tile_sensitivity_v18_best.json`/`_v19_best.json`/
`_v19_2d_best.json`) — deutlich über dem Baseline-Rauschen, aber der
Nutzer-Verdacht ist: **unterkalibriert**, nicht nur "klein, aber real". Eine
reine Spread-Zahl beantwortet das nicht — dafür fehlt eine GROUND TRUTH, wie
groß die Reaktion SEIN SOLLTE. Diese Vorregistrierung baut genau diese Ground
Truth für Runde 5 (dort exakt berechenbar, kein Zufalls-Rest mehr, siehe
`round5.rs`-Moduldoku) und regressiert die drei Modell-Köpfe (`v18_best`
flach, `v19_best` flach, `v19_2d_best` 2D) dagegen.

## Kern-Erkenntnis, die dieses Design trägt: `round5.rs` liefert die Ground
## Truth BEREITS über einen bestehenden Einstieg

`engine/src/round5.rs::choose_action_with_analysis` (aufgerufen von
`net_mcts.rs::net_search_with_tree`, IMMER wenn `round5::applies(state)` --
also `round_number>=5 && phase==Drafting` -- unabhängig vom übergebenen
Modell) ersetzt die Netz-Suche durch eine **exakte** Alpha-Beta-Suche
(`negamax` über `leaf_value = player_total_exact(eigen) -
player_total_exact(gegner)`, wobei `player_total_exact` den EXAKTEN
Rundenscore via `tiling_solver::solve_round_final_score_endaware` plus die
EXAKTE Wertungsplatten-Endwertung plus die projizierte Strafleiste liefert --
KEINE Heuristik, siehe Moduldoku "Ab Rundenbeginn ist Runde 5 also ein
Full-Information-Endspiel"). Jeder Wurzelkandidat im zurückgegebenen
`moves[]`-Array trägt ein Feld **`ab_value`** = die rohe, UNNORMALISIERTE
Punkte-Marge (eigen − gegner) NACH diesem Zug unter optimalem Folgespiel
(`round5.rs` Zeile ~337, Kommentar: *"val ist eine rohe Punkte-Margin ...
KEINE Gewinnwahrscheinlichkeit"*). `ab_value` des gewählten besten Kandidaten
(`moves[analysis["ai_action"]]["ab_value"]`) ist damit **der exakte Wert DES
AKTUELLEN Zustands** für den Spieler am Zug -- klassische Minimax-Knotenwert-
Semantik, kein Suchrauschen (Budget-Vorbehalt siehe "Bekannte
Einschränkungen" Punkt 1).

Diese Ground Truth ist über den **bereits existierenden** Python-Einstieg
`mosaic_rust.net_search_state_json(state_json, model_path, sims, c_puct,
seed)` erreichbar -- `model_path` muss ein gültiger Modellpfad sein (wird
geladen), ist für Runde-5-Zustände aber FUNKTIONAL IRRELEVANT (nie benutzt,
reiner API-Zwang). Kein neuer Rust-Code nötig für die Ground-Truth-Seite.

## Der Value-/Punkte-KOPF selbst ist für Runde-5-Zustände NICHT über den
## Such-Endpunkt erreichbar -- zweite Kern-Erkenntnis (und wie man sie umgeht)

`net_mcts.rs::net_search_with_tree` prüft `round5::applies(state)` **VOR**
dem Aufruf von `compute_root_value_debug`/`build_net_tree` und gibt bei
Treffer sofort `round5::choose_action_with_analysis` zurück (`value`/
`win_pct`/`value_debug`/`root_value` im JSON dann `null`/fehlend, `tree:
null`) -- das Netz wird für Runde-5-Zustände über `net_search_state_json`/
`net_search_state_json_trace`/`ai_debug_net_json` **gar nicht aufgerufen**,
UNABHÄNGIG davon, ob der Zustand live gespielt oder extern rekonstruiert
wurde (die Prüfung hängt nur an `round_number`/`phase`). Für die
Kalibrierungsfrage brauchen wir also einen **rohen Forward-Pass**, der dieses
Gate umgeht.

**Erster Anlauf verworfen:** `PyGame.features()` + `mosaic_rust.onnx_eval()`
sind such-unabhängig, ABER `features()` liest IMMER `self.game.state` einer
LEBENDEN `PyGame`-Instanz, und es gibt keinen Python-Einstieg, der eine
beliebige extern gespeicherte `state_json` in eine `PyGame`-Instanz
injiziert. Ein zweiter Anlauf (`PyGame.select_scoring(ids)` als generischer
Live-Setter + Autoplay bis Runde 5) funktionierte für die FLACHEN Modelle,
aber `v19_2d_best` (`InputLayout::PlanesPlusFlat`) brauchte zusätzlich einen
Planes-Puffer, der nirgends nach Python exportiert ist
(`state_to_planes_direct`/`features_for_net` sind `pub fn`, aber keine über
`py.rs`/`lib.rs` erreichbar) -- als Vorbedingung benannt.

**GATE-FIX (Koordinator-Feedback, ersetzt beide obigen Anläufe):** statt der
fehlenden Rust→Python-Brücke den bereits vorhandenen TORCH-Pfad nehmen --
`engine/py/neural_net.py::build_model_from_checkpoint` lädt ein `.pth`-
Checkpoint direkt und baut `MosaicNet`/`Mosaic2DNet` passend zum darin
gespeicherten `state_dict` (`encoder_from_state_dict`), UND
`state_to_tensor`/`state_to_planes` bauen die Eingabe-Tensoren DIREKT aus
einem beliebigen State-Dict -- keine `PyGame`-Instanz, kein `round5`-Gate,
kein Autoplay-Umweg nötig. `state_to_planes` ist laut Koordinator die
Python-Parität zu `state_to_planes_direct` (60/60 Zustände geprüft
übereinstimmend) -- das ist exakt der fehlende Planes-Puffer, nur von der
Python- statt der Rust-Seite geliefert. Damit sind alle drei Modelle
(`v18_best`/`v19_best`/`v19_2d_best`) über GENAU denselben Code-Pfad
messbar, die frühere Sonderbehandlung/Vorbedingung für `v19_2d_best` entfällt
vollständig:

```python
model, encoder = build_model_from_checkpoint(torch.load(pth_path, weights_only=False))
model.eval()
s = dict(state); s["scoring_tile_ids"] = list(combo)
x_flat = state_to_tensor(s).unsqueeze(0)
with torch.no_grad():
    if encoder == "2d":
        out = model(state_to_planes(s).unsqueeze(0), x_flat)
    else:
        out = model(x_flat)
raw_value, raw_points = out[1].item(), out[3].item()
```

Wichtiger Nebeneffekt: weil `state_to_tensor`/`state_to_planes` auf einem
BELIEBIGEN State-Dict arbeiten (keine lebende Instanz nötig), entfällt auch
der Grund für den Autoplay-Umweg (siehe "Positions-Auswahl" unten) -- die
Hauptmessung kann wieder direkt auf `frozen_eval_set`-Zuständen laufen, wie
im allerersten Entwurf beabsichtigt.

## Positions-Auswahl: `frozen_eval_set`-Snapshots (Runde 5), NICHT "späte
## Runde 4", KEIN Autoplay mehr nötig

Nach dem Torch-Gate-Fix (siehe oben) braucht weder die Ground-Truth-Seite
(`net_search_state_json`, rekonstruiert selbst) noch die Modell-Meinungs-Seite
(`state_to_tensor`/`state_to_planes`, arbeiten direkt auf dem Dict) eine
lebende `PyGame`-Instanz -- der zwischenzeitliche Autoplay-Umweg (Partien
selbst bis Runde 5 vorspielen, siehe Git-Historie dieses Dokuments) ist damit
hinfällig. Positions-Substrat ist jetzt **einheitlich**
`evaluations/frozen_eval_set.pkl`, Records mit `state["round"]==5 and
state["phase"]=="drafting"` (233 von 1800 verfügbar) -- sowohl für die
Hauptmessung als auch für die Kennlinien-Fitting-Stichprobe (identisches
Substrat, unterschiedliche Records daraus gezogen).

**Runde 5, nicht Runde 4** (unverändert gegenüber dem ersten Entwurf): der
Übergang Runde 4→5 (Beutel-Zug für die neue Fabrikbefüllung,
`state::setup_new_round`) ist die letzte echte Zufallsquelle des Spiels
(`round5.rs`-Moduldoku: *"Sämtliche Zufälligkeit einer Runde ... läuft ... in
`setup_new_round` ab, BEVOR die Drafting-Phase extern erreichbar wird"*) --
ein Runde-4-Zustand hat also KEINEN einzelnen exakten Endwert, nur eine
ERWARTUNG über mögliche Runde-5-Aufstellungen (das Problem, das
`round_transition.rs`/`round_transition_deep.rs` bereits über
SAMPLING/Bootstrap lösen, nicht über exakte Berechnung). Ehrlich gemäß
Auftrag: Runde-4-Zustände sind NICHT Teil dieser Vorregistrierung.

## Ground Truth je (Zustand, Wertungsplatten-Kombination)

Für JEDE Stelle (Hauptmessung UND Kennlinien-Fitting-Stichprobe, identischer
Code, `frozen_eval_set`-Record direkt, keine lebende Instanz):

```python
s = dict(state); s["scoring_tile_ids"] = list(combo)
out = json.loads(mosaic_rust.net_search_state_json(json.dumps(s), model_path_for_api, sims, c_puct, seed))
ab_value = out["moves"][out["ai_action"]]["ab_value"]  # exakte Punkte-Marge (eigen-gegner), Perspektive: current_player
```

`model_path_for_api` ist ein beliebiger gültiger ONNX-Pfad (wird geladen,
aber für Runde-5-Zustände nie benutzt, reiner API-Zwang -- unabhängig davon,
welches der drei `.pth`-Modelle gerade gemessen wird). `sims`/`c_puct` sind
für Runde-5-Zustände ebenfalls funktionslos (Alpha-Beta hat keine MCTS-
Parameter) -- werden trotzdem durchgereicht (API-Zwang).

**Ground-Truth-Delta** zwischen Behandlungs- und Referenz-Kombination
(derselbe Zustand, fester `seed`, um Alpha-Beta-Zugreihenfolge-Rauschen
auszuschließen -- Alpha-Beta ist bei fixem Budget/Deadline NICHT vollständig
deterministisch lastunabhängig, siehe `NODE_BUDGET`-Kommentar, `seed`
beeinflusst hier nur `json_to_state`s Neumischung verdeckter Information,
nicht die Suche selbst):

```
true_delta_pts = ab_value(state, combo_treatment) - ab_value(state, combo_reference)
```

## Modell-Delta je (Zustand, Kombination)

EINHEITLICH für alle drei Modelle (Torch-Gate-Fix, siehe oben):

```python
raw_value_ref, raw_points_ref = raw_value_points_torch(model, encoder, state, combo_reference)
raw_value_t, raw_points_t = raw_value_points_torch(model, encoder, state, combo_treatment)
```

`model_value_delta_winprob = value_to_win_prob(raw_value_t) -
value_to_win_prob(raw_value_ref)` (`value_to_win_prob(v) = (v+1)/2`,
identisch zu `net_mcts.rs`).

`model_points_delta_winprob`: der Punkte-Kopf ist selbst schon
`tanh(Δ-Punkte/50)` -- Rücktransformation in eine Punktzahl
(`50*atanh(clamp(p,-0.999,0.999))`, identisch zu `debug.html`/
`static/debug.html::renderValueBreakdown`), DANN durch dieselbe empirische
Kennlinie wie `true_delta_pts` gejagt (lokale Ableitung, siehe unten) -- so
bleiben Value-Kopf- und Punkte-Kopf-Vergleich auf DERSELBEN Zielskala
(Gewinnwahrscheinlichkeit).

## Empirische Punkte→Sieg-Kennlinie (Herleitung, KEIN Rückgriff auf
## `mcts::normalize_score`/`VALUE_SCALE`)

`round5.rs` normalisiert intern selbst mit `((val/VALUE_SCALE).tanh()+1)/2`
(`VALUE_SCALE=50`) für die `mcts_q`/`mcts_win_pct`-Anzeigefelder -- genau
DIESE Formel für die eigene Kalibrierungsmessung zu verwenden wäre zirkulär
(die Frage "ist der Netz-Kopf realistisch kalibriert" ließe sich dann nur
gegen eine ANDERE, ebenfalls unvalidierte Engine-Konstante beantworten).
Stattdessen: **unabhängige logistische Regression aus dem Korpus selbst.**

Datengrundlage: `evaluations/frozen_eval_set.pkl`, alle Records mit
`state["round"]==5 and state["phase"]=="drafting"` (233 verfügbar). Jeder
Record trägt bereits `state["players"][i]["score"]` (laufender Punktestand
zum Aufnahmezeitpunkt) UND den TATSÄCHLICHEN `winner` des abgeschlossenen
Spiels (`rec["winner"]`, `rec["completed"]`). Für Konsistenz mit `ab_value`
(das die PROJIZIERTE Punkte-Marge ab genau diesem Punkt ist, inkl. Endwertung/
Strafleiste) wird NICHT der rohe `score`-Unterschied als X-Achse verwendet
(unterschätzt systematisch -- Endwertung/Strafleiste-Projektion fehlt darin),
sondern **derselbe `ab_value`** (Ground-Truth-Formel oben, mit der Original-
`scoring_tile_ids` des Records, EIN Alpha-Beta-Aufruf je Record):

```
x_i = ab_value(state_i, state_i["scoring_tile_ids"])   # Perspektive: current_player_i
y_i = 1 if rec["winner"] == state_i["current_player"] else 0
```

Logistische Regression `P(win) = sigmoid(a + b*x)` per Newton-Raphson/IRLS
(reines NumPy, kein `scipy`/`sklearn` -- Projektkonvention, siehe
`tools/`-Historie). Ergebnis: Steigung `b` (Logit pro Punkt),
Achsenabschnitt `a`, Pseudo-R² (McFadden) als Güte-Kennzahl der Kennlinie
selbst -- wird VOR der Hauptregression separat berichtet (ist die Kennlinie
schlecht, ist ALLES Nachfolgende nicht belastbar).

**Umrechnung `true_delta_pts -> erwartetes Δ-Win%` -- LOKALE ABLEITUNG (Gate-
Fix #1, ersetzt die ursprünglich geplante volle Kennlinien-Differenz):**

```
P_ref = sigmoid(a + b*x_ref)
expected_delta_winprob = b * P_ref * (1 - P_ref) * true_delta_pts
```

Grund für den Wechsel: Runde 5 ist (fast) ein Full-Information-Endspiel, die
Kennlinie ist deshalb erwartungsgemäß SEHR steil (Rauchtest-Fund:
`b≈12,2`, McFadden-R²≈1,0 -- `ab_value` sagt den Ausgang schon bei ±20-30
Punkten quasi mit Sicherheit voraus). Die ursprünglich geplante VOLLE
Kennlinien-Differenz `sigmoid(a+b·x_t) - sigmoid(a+b·x_ref)` sättigt für
deutlich entschiedene Stellungen (die in Runde 5 die Mehrheit sind) auf ~0,
UNABHÄNGIG von der Größe von `true_delta_pts` -- zwei separat gesättigte
Sigmoid-Auswertungen subtrahiert ergeben bei kleinen Stichproben oft exakt
identische Werte (0,0) über mehrere Zustände/Kombinationen hinweg, was die
OLS-Regression auf `std(x)=0` (rechnerisch entartet, keine Steigung
bestimmbar) kollabieren lässt -- exakt beobachtet im ersten Rauchtest-Lauf
(2 Zustände × 3 Kombinationen, alle 6 Paare `expected_delta_winprob=0,0`).
Die LOKALE Ableitung (Tangente an der Kennlinie bei `x_ref`) bleibt für JEDE
Größe von `true_delta_pts` linear proportional (keine zusätzliche Sättigung
durch die Differenzbildung selbst) -- Standard-Linearisierung für "erwarteter
Effekt einer moderaten Verschiebung", numerisch stabiler bei kleinen
Stichproben. Bleibt inhaltlich korrekt klein an entschiedenen Stellungen
(dort ändert ein Wertungsplatten-Tausch die Siegwahrscheinlichkeit
tatsächlich kaum) -- verschwindet aber nicht durch zwei unabhängige
Sättigungen exakt auf 0, sondern bleibt eine stetige, informative Zahl.

## Messgrößen (je Modell separat: `v18_best`, `v19_best`, `v19_2d_best` --
## alle drei gleichberechtigt, keine Vorbedingung mehr offen)

1. **Kalibrierungs-Steigung**: OLS-Regression von `model_value_delta_winprob`
   (bzw. separat `model_points_delta_winprob`) auf
   `expected_delta_winprob_from_curve` (siehe Umrechnung oben), OHNE
   Achsenabschnitt-Zwang durch Null (Achsenabschnitt wird mitgeschätzt, aber
   nicht separat interpretiert -- Fokus liegt auf der Steigung).
2. **R²** derselben Regression (erklärte Varianz -- unterscheidet
   "systematisch flach" von "einfach verrauscht").
3. Getrennt für Value-Kopf UND Punkte-Kopf (zwei Regressionen je Modell) --
   Memory `project_v8d_value_head_root_cause`/Forensik vom selben Tag
   (`game_20260802_155431_seed216416`) zeigt, dass beide Köpfe divergieren
   können, insbesondere Runde 5 (frozen_eval_set-Kalibrierung dort: r=0,678
   zwischen den Köpfen selbst, schwächer als Runde 1-4).

## Vorab-Interpretationsregeln

- **Steigung ≈ 1 (95%-KI überdeckt [0,85; 1,15])**: Kopf reagiert in etwa
  proportional richtig auf Wertungsplatten-Änderungen -- die kleine
  `treatment_value_spread`-Zahl aus `scoring_tile_sensitivity.py` ist dann
  KEIN Unterkalibrierungs-Befund, sondern spiegelt einfach wider, dass echte
  Wertungsplatten-Kombinationswechsel bei FESTEM Brett tatsächlich nur kleine
  Punkte-Deltas erzeugen (die Ground Truth selbst ist dann klein).
- **Steigung deutlich <1 (KI-Obergrenze <0,85)**: Unterkalibrierung
  bestätigt -- der Kopf dämpft echte Punkte-Signale. Handlungsempfehlung:
  Kandidat für das Value-Zielrauschen-Thema (Lambda-Kontext), NICHT
  automatisch ein Trainings-Rezept-Wechsel ohne weitere Diagnose.
  Unterscheidung Value- vs. Punkte-Kopf beachten -- reagiert NUR einer
  gedämpft, ist das Zielrauschen wahrscheinlich kopf-spezifisch (Punkte-Ziel
  vs. Value-Ziel haben unterschiedliche Rausch-Historie, siehe
  `PREREG_lambda_target.md`).
- **Steigung ≈ 0 (KI überdeckt 0 UND liegt komplett unter 0,3)**: Kopf
  ignoriert Wertungsplatten faktisch -- eigener, klarer Befund (stärker als
  "unterkalibriert"), separate Ursachenanalyse nötig (z.B. Trunk-Kapazität,
  Feature-Encoding-Bug für `scoring_tile_ids` spezifisch).
- **R² klein (<0,1) UNABHÄNGIG von der Steigung**: Steigung ist nicht
  belastbar interpretierbar (zu viel Rauschen relativ zum Signal) -- als
  "kein Befund", nicht als Bestätigung/Widerlegung werten, mehr Zustände/
  Kombinationen nötig, bevor eine Aussage getroffen wird.
- **Pseudo-R² der Kennlinie selbst <0,3**: die Kennlinie ist zu unsicher, um
  als Umrechnungsgrundlage zu dienen -- gesamte Hauptmessung wird als "nicht
  interpretierbar" eingestuft, unabhängig von den übrigen Ergebnissen
  (Kaskaden-Stop, siehe Ausführungsplan).

## Bekannte Einschränkungen, bewusst akzeptiert

1. **`ab_value` ist "exakt, wenn das Budget nicht bindet"**, nicht
   unbedingt bei JEDEM Knoten (`NODE_BUDGET=200`, `TIME_BUDGET=5s`,
   Kalibrierung laut `round5.rs`-Kommentar: n=92/116 realistische
   Entscheidungen liefen bis zur Deadline, n=24/116 vollständig gelöst --
   d.h. die meisten, aber nicht alle Knoten sind wirklich erschöpfend
   gelöst). Für die Kennlinien-Fitting-Stichprobe (233 Records, EIN
   Alpha-Beta-Aufruf je Record) UND für die Haupt-Ground-Truth (State ×
   Kombination) gilt dieselbe Einschränkung gleichermaßen -- systematischer
   Bias eher unwahrscheinlich (kein Grund, warum Budget-Grenzfälle mit
   Wertungsplatten-Kombination korrelieren sollten), aber nicht bewiesen.
2. **ONNX (Live-Betrieb) vs. Torch (dieses Messwerkzeug) sind zwei
   verschiedene Artefakte** desselben trainierten Modells -- `export_onnx.py`
   exportiert aus dem `.pth`-Checkpoint, beide SOLLTEN bit-äquivalent sein,
   diese Vorregistrierung prüft das aber nicht separat nach (kein
   ONNX-vs-Torch-Paritätstest als Teil dieser Messung -- falls je eine
   Diskrepanz zwischen live beobachtetem Server-Verhalten und dieser
   Kalibrierung auffällt, ist das der erste Verdachtspunkt).
3. **233 Runde-5-Records sind das gesamte verfügbare Substrat** im
   eingefrorenen `frozen_eval_set.pkl` (`frozen_v1`) -- keine Möglichkeit,
   mehr zu ziehen, ohne einen neuen Frozen-Set-Build anzustoßen (außerhalb
   dieses Tasks).
4. **Wertungsplatten-Kombinationen werden wie in
   `scoring_tile_sensitivity.py` aus den 32 gültigen 3er-Kombinationen
   gezogen** (`MUTUALLY_EXCLUSIVE_PAIRS`-Logik) -- Referenz-Kombination je
   Zustand ist die ORIGINALE des live erreichten Zustands (analog zum
   Vorbild), nicht zufällig.
5. **Alpha-Beta-Zugauswahl-Rauschen bei gebundenem Budget**: bei sehr
   komplexen Runde-5-Zuständen kann `ab_value` bei identischer Kombination
   über wiederholte Aufrufe geringfügig schwanken (siehe `round5.rs`-Historie
   zum alten `TIME_BUDGET`-Problem, seit der Knoten-primär-Umstellung
   behoben für IDENTISCHE Läufe, aber `seed`/Prozesslast können minimal
   variieren) -- wird NICHT gesondert gegen-getestet (kein Baseline-Rauschen-
   Doppellauf wie bei `scoring_tile_sensitivity.py`, da `seed` hier nur die
   verdeckte-Info-Neumischung treibt, nicht die Suche selbst innerhalb
   `round5.rs`, das Modul hat kein eigenes Zufalls-Sampling).
6. **Lokale Ableitung statt voller Kennlinien-Differenz** (Gate-Fix #1):
   bleibt an entschiedenen Runde-5-Stellungen (die Mehrheit) klein/nahe 0 --
   inhaltlich korrekt, aber bedeutet auch, dass die Regressions-Aussagekraft
   VOR ALLEM aus Zuständen NAHE der Entscheidungsgrenze kommt (dort ist
   `P_ref*(1-P_ref)` groß). Bei `--n-states 24` sollte das Zufallsziehen aus
   233 Records genug solcher Grenzfälle enthalten, wird aber im vollen Lauf
   explizit geprüft (Verteilung von `ab_value_ref` im Report).

## Werkzeug

`tools/r5_value_calibration.py` (Vorbild: `tools/scoring_tile_sensitivity.py`
-- importiert dessen `all_valid_combos`/`pick_representative_combos` statt sie
zu duplizieren, Memory `feedback_check_existing_tools_first`). CLI:

```
python tools/r5_value_calibration.py \
    --eval-set evaluations/frozen_eval_set.pkl \
    --models models/alphazero_v18_best.pth models/alphazero_v19_best.pth models/alphazero_v19_2d_best.pth \
    --model-path-for-api models/alphazero_v18_best.onnx \
    --n-states 24 --n-combos 6 --sims 400 --c-puct 1.5 \
    --curve-n-states 233 \
    --out evaluations/artifacts/r5_value_calibration_result.json
```

`--models` sind jetzt `.pth`-Torch-Checkpoints (alle drei gleichberechtigt,
`build_model_from_checkpoint` erkennt den Encoder selbst) -- `--model-path-
for-api` ist ein SEPARATER, beliebiger ONNX-Pfad, den `net_search_state_json`
laden MUSS (API-Zwang), inhaltlich für Runde-5-Zustände irrelevant (siehe
"Ground Truth"-Abschnitt).

## Ausführungsplan

1. **Dieser Schritt (User-Go vorliegend)**: PREREG (dieses Dokument) +
   Werkzeug + Rauchtest (2 Zustände × 3 Kombinationen × 1 Modell). Zahlen auf
   Plausibilität prüfen (Vorzeichen sinnvoll? `ab_value`-Größenordnung
   plausibel für Runde-5-Endspiele? Kennlinie hat positive Steigung?).
   **Kein voller Lauf, kein Commit.**
2. Bericht an den Koordinator, STOPP (dieser Task endet hier).
3. NACH separater Freigabe (nach Lambda-/PCR-Auswertung): voller Lauf
   (`--n-states 24 --n-combos 6` über alle 3 Modelle) + Bericht mit den
   vorregistrierten Kennzahlen und Interpretation gemäß den Regeln oben.

---
**STATUS (Stand 2026-08-08): ENTSCHIEDEN** -- der volle Lauf (24 Zustaende
x 6 Kombinationen, Kennlinie aus 233 R5-Records) fand statt: Kennlinie
b=0,128 Logit/Punkt, McFadden-R²=0,316. Value-Kopf-Steigungen: v18_best
0,087, v19_best 0,061, v19_2d_best 0,061 (Soll ~1) -- Unterkalibrierung
fuer v18_best und v19_2d_best bestaetigt (nur ~6-9% der erwarteten
Reaktion). Belegstelle: archive/history.md, Abschnitt "R5-Value-
Kalibrierung (Task #27) ABGESCHLOSSEN: Unterkalibrierung BESTAETIGT",
Zeile ~7065-7089; evaluations/artifacts/r5_value_calibration_result.json.

**NACHMESSUNG 2026-08-29 (Fahrplan Phase 0.1, erste Messung auf der
b-Serie -- die Steigungen oben stammten aus v18/v19):** v22-b05
(spaltenfaehigstes Netz, 0,3375 volle Spalten am Instrument, DAgger-
Linie) misst mit demselben Werkzeug und derselben Anordnung (24
Zustaende x 6 Kombinationen, 139 gueltige Paare): **Value-Kopf-Steigung
0,0886** (r2 0,115), Punkte-Kopf-Steigung 0,989 (r2 0,308). **Die
Plattendaempfung ist damit KEIN Korpus-Artefakt** -- sie persistiert
exakt im 0,06-0,09-Band, obwohl derselbe Kopf Geschwister inzwischen
RICHTIG nach Spaltenfortschritt ordnet (Tau +0,338 gegen -0,08/-0,19
der plattenblinden Netze, b05_value_sibling_check.json): die ORDNUNG
ist geheilt, die GROESSE fehlt weiter. Konsequenz laut Fahrplan: die
Phase-3-Bedingung (Ziel-Chirurgie) ist erfuellt. Artefakt:
evaluations/artifacts/r5_value_calibration_b05.json.

**NACHTRAG 2026-08-30: die Daempfung hat ein SYMPTOM im Spielbetrieb --
und daraus wird ein neuer Test.** PREREG_search_depth_column_optimum
misst an b05, dass mehr Suchtiefe WENIGER volle Spalten produziert
(100 Sims 0,6225 gegen 400 Sims 0,3375, frisch-seed-repliziert; die
Wurzelbreite scheidet als Erklaerung aus). Deutung (Herleitung, kein
Beleg): die Gumbel-Wurzelauswahl sortiert nach Q-Werten, mehr
Simulationen geben also dem Value-Kopf mehr Gewicht gegenueber dem
Prior -- und dieser Kopf unterbietet den Plattenlohn eben um Faktor
~11 (Steigung 0,0886, Nachmessung oben).

**Daraus ein Erfolgstest fuer jede kuenftige Kalibrierungs-Reparatur,
der ueber die Steigung hinausgeht: KIPPT DIE SIMS-KURVE?** Ein Netz mit
korrekt geeichtem Plattenanteil muesste mit MEHR Suche MEHR Spalten
bauen, nicht weniger. Der Test ist billig (zwei Self-Play-Arme a 200
Partien) und misst die Wirkung dort, wo sie zaehlt -- im gespielten
Verlauf statt an einer Regressionssteigung.

**WIDERSPRUCH BENANNT 2026-08-30 (Nutzer-Einwand, gegen die bisherige
Lesart des Koordinators).** Die hier gemessene Steigung ist ein
AGGREGAT ueber Wertungsplatten-Wechsel, KEINE spaltenspezifische
Groesse -- sie sagt "der Kopf reagiert auf Plattenwechsel nur mit ~9
Prozent der wahren Bewegung", nicht "der Kopf unterschaetzt Spalten".
Diese Gleichsetzung stand mehrfach im Chat und ist so nicht belegt.

**Zwei vorhandene, spaltenSPEZIFISCHE Messungen sprechen sogar
dagegen:** (1) Geschwister-Ordnung nach k1-Spaltenfortschritt Tau
+0,338 (b05_value_sibling_check.json) -- der Kopf ORDNET richtig.
(2) PREREG_human_game_oracle_gap par.9: an echtem Menschenspiel
bewertet b05 k1-relevante Zuege NICHT schlechter als neutrale (alle
drei Fuellstand-Schwellen H0, ~0 pp Differenz).

**Der Widerspruch, der daraus folgt und offen bleibt:** trotz richtiger
Ordnung und ohne spezifische Abwertung baut b05 bei 400 Sims nur 0,34
volle Spalten. Eine Bewertungs-Erklaerung traegt das nicht. Besser
passt der Befund aus PREREG_placement_side par.14 ("das Material war
da, der Plan nicht"): eine Spalte verlangt eine MEHRRUNDIGE
Farbzusage, keine Stellungsbewertung -- ein PLANUNGS-, kein
Bewertungsproblem. Dazu passt auch der Nutzer-Einwand, dass ein Netz,
das nach der Dreiecks-Einhuellenden spielt, wertvolle Spalten
praktisch automatisch bekommt und auf Plattenwechsel gar nicht stark
reagieren MUSS.

Die kriterienweise Aufschluesselung dieser Messung (Auftrag
2026-08-30, tools/probes/r5_calibration_per_criterion.py) ist deshalb
eine ABGRENZUNGS-Messung: ist k1 staerker gedaempft als die uebrigen
sieben Kriterien, oder ist der Effekt gleichmaessig? Nur der erste
Fall stuetzte ueberhaupt eine spaltenbezogene Lesart.
