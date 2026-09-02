<!-- STATUS: ENTSCHIEDEN | Frage: Unterbietet der Value-Kopf den Plattenlohn, und laesst sich das heilen? | Beleg: JA und NEIN -- die Daempfung ist real und stabil (b01 0,0859, Punkte-Kopf trifft dieselbe Groesse mit 0,97), aber **par.12 (2026-09-01) widerlegt ihre Rolle**: keine Einstellung des Kopfes holt den Spaltenbau in der Tiefe zurueck (B=2,0 schadet -0,125, B=0,5 und Punkte-Blend bewegen nichts; Delle @100 gegen @400 = 0,205). Phase 3 GESCHLOSSEN ohne Bau, Trainingslauf gespart; die Ursache erbt `search_depth_column_optimum` Stufe 4. -->

# Vorregistrierung: Runde-5-Value-/Punkte-Kopf-Kalibrierung gegen exakte Ground Truth

**Angelegt 2026-08-02 (Task #27), VOR dem ersten vollen Lauf.** Nur Design +
Werkzeug + Rauchtest in diesem Schritt (User-Go dafür liegt vor) – der volle
Lauf folgt NACH der Lambda-/PCR-Auswertung, separat freigegeben. Die Regeln
unten dürfen nach Sichtung von Zwischenergebnissen nicht mehr geändert werden
(Präzedenzfall `PREREG_lambda_target.md`).

## Frage

`tools/scoring_tile_sensitivity.py` (2026-07-26) zeigt: der Root-Value über
verschiedene Wertungsplatten-Kombinationen bei FESTEM Zustand streut nur
Ø 0,035–0,043 (`treatment_value_spread_across_combos`, siehe
`evaluations/artifacts/scoring_tile_sensitivity_v18_best.json`/`_v19_best.json`/
`_v19_2d_best.json`) – deutlich über dem Baseline-Rauschen, aber der
Nutzer-Verdacht ist: **unterkalibriert**, nicht nur "klein, aber real". Eine
reine Spread-Zahl beantwortet das nicht – dafür fehlt eine GROUND TRUTH, wie
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

## par.10 KRITERIENWEISE Aufschluesselung (gefahren 2026-08-30)

**Anlass (Nutzer-Einwand).** Aus der Gesamtsteigung 0,0886 war gefolgert
worden, der Kopf unterbiete den Plattenlohn und baue DESHALB keine Spalten.
Die Zahl ist aber ein Mittel ueber alle ACHT Kriterien und kann "speziell
fuer Kriterium 1 taub" (spaltenblind) nicht von "gleichmaessig leise"
(plattensensitiv-schwach) unterscheiden. Der Nutzer hat zusaetzlich
eingewandt, dass wer nach der Dreiecks-Einhuellenden baut, wertvolle Spalten
ohnehin bekommt und auf Plattenwechsel gar nicht stark reagieren muss. Zwei
vorhandene Messungen sprachen ebenfalls dagegen: Geschwister-Tau +0,338
(b05_value_sibling_check.json) und PREREG_human_game_oracle_gap par.9 (keine
spezifische Abwertung menschlicher k1-Zuege, alle drei Schwellen H0).

**Anordnung.** `tools/probes/r5_calibration_per_criterion.py` (neu; importiert
Ground Truth, Kennlinie und Torch-Pfad aus `tools/r5_value_calibration.py`,
kein Logik-Fork). Dieselben 24 Runde-5-Zustaende (gleicher Selektor/Seed) und
dieselbe Kennlinie (a=-0,78786 b=0,39438, McFadden 0,634; in dieser Sitzung
mit 233 Records unabhaengig nachgefittet, Ergebnis ZIFFERNGLEICH zur
b05-Messung -- zugleich der Determinismus-Nachweis unter der parallel
laufenden Erzeugung, ergaenzt um eine 8er-Stichprobe frisch nachgerechneter
`ab_value`, 8/8 identisch). Unterschied zum Bestandswerkzeug: statt 6
repraesentativer laufen ALLE 32 gueltigen Kombinationen je Zustand. Nur so
kommt jedes Kriterium gleich oft vor (12x) und die Indikatormatrix hat vollen
Spaltenrang 8; mit 6 Kombinationen waere die Frage gar nicht beantwortbar.

Zwei Auswertungen nebeneinander, weil ein EINZELNES Kriterium mit gueltigen
Kombinationen prinzipiell nicht isolierbar ist (jede Kombination traegt genau
3 Kriterien aus 3 verschiedenen Ausschluss-Paaren, die symmetrische Differenz
zweier Kombinationen ist also immer mindestens 2):

- **(a) additive Zerlegung je Zustand**, ohne Achsenabschnitt, anschliessend
  ueber die acht Kriterien zentriert (das entfernt die stark streuende
  Grundlast exakt). Mittleres R2 der Zerlegung: `ab_value` 0,990, Value-Kopf
  0,906, Punkte-Kopf 0,993 -- die Naeherung traegt.
- **(b) Tausch innerhalb eines Ausschluss-Paares**, ganz ohne
  Additivitaets-Annahme, 12 Kontraste je Zustand und Paar,
  Standardfehler je Zustand geclustert (CR1).

**Gueltigkeitsnachweis.** Die Aggregat-Gegenprobe auf der 32er-Menge
(Referenz gegen alle uebrigen, wie im Bestandswerkzeug) liefert fuer b05
**0,0852** (SE 0,0426, geclustert, n=744) und die Zerlegung gepoolt 0,0913
(SE 0,0353) -- die berichteten 0,0886 sind reproduziert, die Aufschluesselung
haengt nicht an einer anderen Grundgesamtheit.

### Steigungen je Kriterium, VALUE-Kopf, v22-b05 (Soll ~1, n=24 Zustaende)

| k | Kriterium | Steigung | SE | t | R2 | k gegen die uebrigen sieben (Diff, SE, t) |
|---|-----------|---------:|---:|---:|---:|---|
| 0 | horizontale Reihen (3 Pkt) | 0,2887 | 0,0890 | 3,24 | 0,323 | +0,213, 0,169, 1,25 |
| **1** | **vertikale Reihen = SPALTEN (7 Pkt)** | **0,1747** | **0,0417** | **4,19** | **0,443** | **+0,094, 0,048, 1,97** |
| 2 | Diagonalen (10 Pkt) | -0,2220 | 0,1746 | -1,27 | 0,069 | -0,272, 0,171, -1,59 |
| 3 | mehrfarbige Felder (2 Pkt) | 0,0807 | 0,0322 | 2,51 | 0,223 | -0,015, 0,030, -0,50 |
| 4 | aeussere Felder (1 Pkt) | 0,1090 | 0,1042 | 1,05 | 0,047 | +0,004, 0,082, 0,05 |
| 5 | Eckplatten (3/8 Pkt) | 0,0022 | 0,0656 | 0,03 | 0,000 | -0,084, 0,055, -1,53 |
| 6 | Spezialfelder (-3 Pkt) | 0,0946 | 0,0444 | 2,13 | 0,171 | -0,012, 0,070, -0,17 |
| 7 | farbenreiche Reihen (4 Pkt) | -0,1504 | 0,1060 | -1,42 | 0,084 | -0,144, 0,085, -1,71 |

### Tausch innerhalb der Ausschluss-Paare (annahmefrei, n=288, 24 Cluster)

| Tausch | v22-b05 | SE | t | v21 (plattenblind) | SE | t |
|--------|--------:|---:|---:|-------------------:|---:|---:|
| 0 -> 7 (horizontal -> farbenreich) | 0,3643 | 0,0460 | 7,91 | -0,0290 | 0,0276 | -1,05 |
| 6 -> 3 (Spezialfelder -> mehrfarbig) | 0,1164 | 0,0552 | 2,11 | 0,1542 | 0,0393 | 3,92 |
| **4 -> 1 (aeussere Felder -> SPALTEN)** | **0,1996** | **0,0165** | **12,08** | **0,0152** | **0,0199** | **0,76** |
| 2 -> 5 (Diagonalen -> Eckplatten) | 0,0254 | 0,0840 | 0,30 | 0,0495 | 0,0264 | 1,88 |

### Verdikt zur Leitfrage

**Kriterium 1 ist NICHT staerker gedaempft als die uebrigen sieben -- eher
das Gegenteil.** Es ist mit t 4,19 (R2 0,443) das am besten belegte positive
Kriterium der Zerlegung, liegt im Wechselwirkungstest UEBER den anderen
sieben (+0,094, t 1,97), und der annahmefreie Tausch 4 -> 1 gibt 0,1996
(t 12,08) -- gut das Doppelte des gepoolten Niveaus 0,091. Die Daempfung ist
BREIT: alle acht Kriterien liegen zwischen 0,00 und 0,29 gegen ein Soll von
~1. Der Befund lautet also **plattensensitiv-schwach, nicht spaltenblind**;
die Schlusskette "Kopf unterbietet den Plattenlohn, DESHALB keine Spalten"
traegt in ihrer spaltenspezifischen Form nicht. Die aggregierte
Unterkalibrierung selbst bleibt unberuehrt und bestaetigt.

**Zu duenn besetzt fuer ein Urteil** (Massstab: der Standardfehler muss "nahe
null" von "auf dem gepoolten Niveau ~0,09" trennen koennen, also SE unter
~0,06): **k2 Diagonalen (SE 0,175), k7 farbenreiche Reihen (SE 0,106), k4
aeussere Felder (SE 0,104)** tragen kein Urteil; **k0 horizontale Reihen
(SE 0,089)** nur eingeschraenkt. Die Ursache ist am Hebelarm ablesbar, nicht
an der Fallzahl (die ist bei allen acht gleich, 12 Vorkommen je Kombination):
die Streuung der wahren Wirkung ueber die Zustaende betraegt bei k2/k7/k4/k0
nur 0,037/0,040/0,063/0,073 Gewinnprozentpunkte gegen 0,333/0,203/0,140 bei
k6/k3/k1. Diagonalen und farbenreiche Reihen sind in Runde-5-Endstellungen
schlicht kaum noch beweglich. **Urteilsfaehig sind k1, k3, k6** (SE < 0,05)
und k5 als verlaesslich nahe null.

### Nebenbefund: die Gesamtsteigung sagt nicht, WELCHE Platten der Kopf sieht

v21 (plattenblinder Vergleichsstand, `models/frozen_champions/
v21_2d_brierbest/model.pth`, auf demselben Substrat mitgemessen) hat die
HOEHERE Aggregat-Steigung: 0,1539 (SE 0,0380) gegen b05s 0,0852. Aufgeloest
kommt sie aus einer ANDEREN Ecke: v21s staerkstes Kriterium ist k6
Spezialfelder (0,1479, Wechselwirkung +0,096 bei t 3,07), waehrend seine
Spalten-Steigung 0,0352 (t 0,95) und sein Spalten-Tausch 0,0152 (t 0,76)
nicht von null zu unterscheiden sind. b05 bezieht seine Reaktion umgekehrt
aus der Reihen-/Spalten-Geometrie (k0 0,289, k1 0,175). Die Differenz b05
minus v21 auf dem Tausch 4 -> 1 betraegt 0,184 (konservativ ungepaart
gerechnet: SE 0,026, t ~7,1). **Der Spaltenkanal ist genau die Stelle, an der
b05 gegenueber dem plattenblinden Stand zugelegt hat** -- konsistent mit
Geschwister-Tau +0,338 und mit par.9 der Mensch-Orakel-Prereg. Fuer kuenftige
Berichte heisst das: eine einzelne Kalibrierungs-Steigung ist kein Guetemass,
sie mittelt ueber Kriterien mit voellig verschiedener Traegerschaft.

**Artefakt:** `evaluations/artifacts/r5_calibration_per_criterion.json`
(enthaelt auch die vollstaendige, modellunabhaengige Ground Truth der 24 x 32
Alpha-Beta-Aufrufe, damit eine andere Auswertung ohne neuen Rechenlauf
moeglich ist). Laufzeit: Wanduhr 3.265 s, CPU 2.970 s, 768 frische
Alpha-Beta-Aufrufe zu 4,25 s je Aufruf, 12 Kerne, parallel laufende
12.000-Partien-Erzeugung (vom Nutzer freigegeben; Determinismus separat
belegt, siehe "Anordnung").

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

## par.11 v23-b01 GEMESSEN: die Daempfung bleibt -- der Korpus heilt sie NICHT (2026-08-31)

Gefahren mit demselben Zuschnitt wie die b05-Messung (frozen_eval_set, 24
Zustaende x 6 Plattenkombinationen, 400 Sims, Seed 1000), **beide Netze im
SELBEN Lauf** auf denselben 139 Zustands-Kombinations-Paaren -- gepaart, nicht
gegen eine gespeicherte Zahl verglichen (Artefakt
`r5_value_calibration_v23b01.json`):

| Netz | Value-Steigung | R2 | Punkte-Kopf |
| --- | --- | --- | --- |
| `v23-b01_brierbest` | **0,0859** | 0,147 | 0,9728 |
| `v22-b05` | 0,0886 | 0,115 | 0,9888 |

**Verdikt: die Wette von Zuschnitt D ist NICHT aufgegangen.** Der neue Korpus
sollte die Betrags-Daempfung ueber ON-POLICY-Vollendungsexposition heilen --
eigene Partien, in denen Vollendungen vorkommen und sich im Ausgang
auszahlen. Genau das war die Begruendung, den Schwarm argmax-lastig zu
fahren. Die Steigung steht danach bei 0,0859 statt bei ~1: unveraendert.

**Was das WERTVOLL macht, statt nur enttaeuschend:** b01 ist in derselben
Generation deutlich staerker geworden (119:61 gegen b05, Augenhoehe mit dem
Champion) und baut 66 Prozent mehr Spalten -- **ohne dass der Bewerter
repariert wurde**. Der Fortschritt kam also vollstaendig von woanders, und
der Hebel liegt weiterhin unbenutzt da. Die Betrags-Schiene ist damit nicht
erledigt, sondern erst richtig faellig.

**Und die Diagnose bleibt scharf:** der PUNKTE-Kopf trifft den Plattenlohn mit
Steigung 0,97 fast perfekt. Das Netz KANN die Groesse darstellen -- es ist
spezifisch der Gewinnwahrscheinlichkeits-Kopf, der sie unterbietet. Ein
Kapazitaets- oder Eingabeproblem ist damit weiterhin ausgeschlossen.

**Folge fuer den Strang:** die naechste Stufe ist nicht mehr "abwarten, ob der
Korpus es richtet" -- diese Frage ist beantwortet. Es braucht den Eingriff,
mit dem registrierten Erfolgstest "kippt die Sims-Kurve?" (Nachtrag
2026-08-30).

## par.12 PHASE 3, ENTWURF DES EINGRIFFS (2026-09-01, Nutzer-Auftrag "dann entwirf was")

**Ausgangslage.** Die Daempfung ist gemessen und stabil (Steigung 0,0859 auf
b01 gegen 0,0886 auf b05, par.11), sie ist BREIT ueber die Kriterien (k1 mit
0,1747 am wenigsten gedaempft, par.10), und die Information liegt im Rumpf:
der Punkte-Kopf trifft dieselbe Groesse mit **0,97**.

**Was am Verbraucher bereits gemessen geschlossen ist -- und warum der
Entwurf dort NICHT ansetzt:**

| Weg | Ergebnis |
| --- | --- |
| eigener Plattenkopf | gebaut und wieder entfernt (`PREREG_plate_head.md`, UEBERHOLT) |
| Endgame-/Platten-Aux-Kopf | Arena H0, wurde Trainings-Upgrade (`plate_intervention`) |
| Platten in die Blattbewertung injizieren | NEGATIV ueber den ganzen Dosis-Sweep (`scoring_plate_injection`) |
| Punkte-Kopf in den Blattwert mischen | Richtung schaedlich, NICHT signifikant: w=0,1 verliert 300:321, McNemar p = 0,053 (`points_blend_w`; `paired_arena_env_points_blend_w.json`; Wortlaut berichtigt 2026-09-01) |

Vier Wege, alle am selben Punkt: dem Blattwert mehr Platteninformation
zufuettern.

**EINWAND DES NUTZERS (2026-09-01), und er sticht:** *"die sind aber alle auf
einem plattenblinden spiel gemessen worden. vielleicht hat das einen
einfluss."* An den Quellen geprueft -- alle vier stammen aus dem 9. bis 11.
August und liefen auf `v21_2d_brierbest`:

| Weg | Datum | gemessen an |
| --- | --- | --- |
| Punkte-Blend | 2026-08-10 | `alphazero_v21_2d_brierbest.onnx`, 400 Partien (Artefakt `paired_arena_env_points_blend_w.json`) |
| Platten-Injektion | 2026-08-11 | Champion `v21_2d_brierbest`@400 gegen Heuristik@150 |
| Aux-Kopf (`endgame_margin`) | 2026-08 | Gating gegen den Champion, 97:103 |
| eigener Plattenkopf | 2026-08-09/10 | vor jeder Spalten-Linie gebaut und entfernt |

**v21 schliesst rund 0,10 volle Spalten je Partie, b01 rund 0,6.** Alle vier
Messungen haben also gefragt, ob mehr Platteninformation im Blattwert einem
Agenten hilft, der die Konsequenz daraus gar nicht ziehen kann. Das ist genau
die Fehlerform, die dieses Projekt als Regel notiert hat: *aus "Eingriff X in
Richtung Y verliert" folgt NICHT "Y ist falsch" -- es fehlt die
Kontrollgruppe: ein Agent, der Y KANN.*

**Folge fuer diesen Entwurf:** die vier Wege sind fuer plattenBLINDE Netze
geschlossen, fuer `v23-b01` sind sie UNGEMESSEN. Der billigste davon ist ein
reiner Laufzeit-Knopf und kostet dasselbe wie Stufe 0 -- er wird deshalb dort
mitgefahren, statt einen fuenften Weg zu erfinden.

### Stufe 0 -- der ERFOLGSTEST zuerst, ohne einen einzigen Bau

Der registrierte Erfolgstest lautet "kippt die Sims-Kurve?". **Er ist
fahrbar, BEVOR irgendetwas gebaut wird** -- und er prueft die Kausalkette,
auf der die ganze Phase ruht: dass der flache Value-Kopf der Grund ist,
warum tiefere Suche den Spaltenbau zerstoert (Plateau 25-100 Sims bei ~0,6
volle Spalten, ab 250 Sims 0,34).

**Instrument:** `MOSAIC_VALUE_CAL_B`, die Laufzeit-Logit-Streckung des
Value-Kopfs (net_mcts.rs:329-340, aktiver Knopf). Eine Streckung B>1 macht den
Kopf in genau der Groesse steiler, in der er zu flach misst.

**Wichtige Abgrenzung:** dieser Knopf ist als STAERKE-Hebel bereits
ENTSCHIEDEN (`PREREG_value_scale_correction.md`: Erstlauf +6pp n.s.,
Replikation ohne Effekt). Er wird hier NICHT als Heilmittel vorgeschlagen,
sondern als **Messinstrument fuer eine Mechanismus-Frage**. Das ist zulaessig,
weil die alte Messung "hebt es die Spielstaerke?" gefragt hat, nicht "haengt
der Spaltenbau bei hoher Suchtiefe daran?".

**Anordnung:** argmax-Instrument @400 Sims (dort, wo der Spaltenbau
zusammenbricht), 200 Partien je Arm, gleicher Seed, alles auf `v23-b01` --
also erstmals an einem Agenten, der Spalten bauen KANN.

| Arm | Knopf | Frage |
| --- | --- | --- |
| Kontrolle Tiefe | `VALUE_CAL_B=1,0` @400 | **liegt bereits vor**: Tor-2a-Lauf `tor2a-v23b01`, gleicher Seed 20260931, gleiches Instrument -- **0,5150** |
| Kontrolle flach | `VALUE_CAL_B=1,0` @**100** | **hat b01 die Tiefen-Delle ueberhaupt?** Die Kurve 0,6 gegen 0,34 ist an **b05** gemessen (`search_depth_column_optimum` par.2i), nicht an b01. b01 liegt bei 400 schon bei 0,5150 -- moeglicherweise gibt es bei ihm nichts zu kippen |
| Streckung | `VALUE_CAL_B=2,0` / `3,0` | macht ein steilerer Value-Kopf die Tiefe wieder spaltenfreundlich? |
| **Blend-Wiedervorlage** | `POINTS_UTILITY_W=0,1` | traegt der Punkte-Blend, wenn der Agent die Konsequenz ziehen kann? (auf v21 schaedlich, siehe Einwand oben) |

Kosten: rund 31 min je Arm; da der 400er-Kontrollarm bereits vorliegt, sind **drei
Arme zu fahren, zusammen ~1,6 h**, kein Bau, kein Wheel.

**Berichtigung im selben Zug (2026-09-01):** der Entwurf nannte zuerst 0,34 als
Erwartung des Kontrollarms. Das ist b05s Wert bei hoher Tiefe. b01 misst am selben
Instrument 0,5150. **Die erste Frage ist damit nicht "kippt die Kurve", sondern ob
b01 ueberhaupt eine Delle hat** -- deshalb der flache Kontrollarm bei 100 Sims. Faellt
@100 nicht deutlich ueber @400 aus, ist die Praemisse von Phase 3 fuer den aktuellen
Stand hinfaellig, noch bevor ein Knopf gedreht wird. Der Blend-Arm faehrt dieselbe Dosis w=0,1 wie die alte Messung -- eine
andere Dosis waere ein zweiter Faktor.

**Entscheidungsmass, vorab:** volle Spalten je Partie und Seite am
argmax-Instrument.

**Schwelle NACHGEZOGEN am 2026-09-01, nach dem Kontrollarm und VOR jedem
Eingriffsarm** (die urspruengliche stammte aus b05s Kurve und passte nicht auf
b01): der flache Kontrollarm ist gefahren und misst

```
b01 @100 Sims : 0,7200 (SE 0,0396, 200 Partien)
b01 @400 Sims : 0,5150 (SE 0,0332, Tor-2a-Lauf, gleicher Seed)
Delle also 0,205, t rund 3,97 -- b01 HAT sie, in derselben Groessenordnung
wie b05 (0,6 gegen 0,34)
```

**"Kippt" heisst damit: mindestens die halbe Delle geschlossen, also
>= 0,618 volle Spalten bei 400 Sims**, bei mindestens einem Arm. Die
Zeitpunkt-Angabe steht hier ausdruecklich, weil eine nach den Behandlungsarmen
verschobene Schwelle wertlos waere; die Behandlungsarme laufen erst nach
diesem Absatz.

**Messweg, validiert:** volle Spalten aus dem letzten Record je Partie
(`col_fill_py` je Spieler, Spalte voll bei fill == 6). Gegenprobe: auf dem
Tor-2a-Korpus liefert der Weg **0,5150** und damit die registrierte Zahl
ZIFFERNGLEICH -- kein eigenes Mass, sondern dasselbe. Zusaetzlich als Waechter eine kurze
gepaarte Arena des besten B gegen B=1 -- eine Streckung, die Spalten bringt
und Staerke kostet, ist kein Erfolg, sondern ein Tausch (und der ist als
Muster schon zweimal aufgetreten).

**Und der Wert eines NULL-Ergebnisses ist hier hoeher als der eines
positiven:** faellt Stufe 0 flach aus, ist die Deutung "der gedaempfte
Value-Kopf zerstoert den Spaltenbau in der Tiefe" WIDERLEGT -- und Phase 3
wird geschlossen, statt ein Training zu kosten. Ein positives Ergebnis
lokalisiert dagegen nur grob (eine globale Streckung schaerft ALLE
Wertunterschiede, nicht nur den Plattenanteil).

### Stufe 1 -- nur bei positivem Stufe-0-Befund: Betrags-Bindung im TRAINING

Kein neuer Konsument, sondern eine Konsistenz-Bedingung zwischen zwei
vorhandenen Koepfen. Der Punkte-Kopf sagt die Marge mit 0,97 voraus, die
Kennlinie (a=-0,78786, b=0,39438, McFadden 0,634) bildet Marge auf
Gewinnwahrscheinlichkeit ab. Zusatzverlust:

```
L_cal = ( sigmoid(a + b * m_punkte) - p_value )^2
```

Der Value-Kopf muss also mit der Vorhersage seines eigenen Punkte-Kopfes
uebereinstimmen. Das fuegt KEINE Information hinzu -- es zwingt den Kopf,
die vorhandene auszudruecken. Kosten: ein Trainingslauf (b01-Rezept, 4-6 h)
plus Gating; ein Faktor gegen b01.

**Risiko, benannt:** die Bedingung koennte den Value-Kopf in Richtung des
Punkte-Kopfes ziehen und damit die WDL-Semantik beschaedigen (Remis-Zone,
Endspiel-Sicherheit). Waechter: Brier auf dem Val-Pool darf nicht schlechter
werden als b01s 0,1934.

### Stufe 2 -- Abbruchregel

Faellt Stufe 0 flach aus, wird Phase 3 **geschlossen und nicht gebaut**. Die
Daempfung bleibt dann ein registrierter Befund ohne benannten Nutzniesser --
und genau das ist die Regel, die dieses Projekt fuer Infrastruktur- und
Reparaturvorschlaege gesetzt hat.

### Stufe-0-Ergebnisse, laufend registriert (2026-09-01)

| Arm | volle Spalten je Seite | SE | n Partien |
| --- | --- | --- | --- |
| @400, `B=1,0` (Kontrolle Tiefe, Tor-2a-Lauf) | 0,5150 | 0,0332 | 200 |
| @100, `B=1,0` (Kontrolle flach) | **0,7200** | 0,0396 | 200 |
| @400, `B=2,0` (Streckung) | **0,3900** | 0,0314 | 200 |

**Befund 1: b01 HAT die Delle.** 0,7200 gegen 0,5150, Differenz 0,205
(t rund 3,97). Die Praemisse von Phase 3 gilt also fuer den aktuellen Stand,
nicht nur fuer b05 -- das war vor dem Lauf offen, weil die Kurve an b05
gemessen worden war.

**Befund 2: Streckung macht es SCHLECHTER, nicht besser.** 0,3900 gegen
0,5150, Differenz -0,125 (SE der Differenz rund 0,046, t rund 2,7). Die
Schwelle 0,618 ist damit klar verfehlt, und zwar in der falschen Richtung.

**Was das an der Deutung aendert -- und das ist der eigentliche Ertrag:** die
Erzaehlung war "der Kopf ist zu leise, deshalb setzt sich in der Tiefe sein
gedaempftes Urteil gegen das Spaltenwissen der Policy durch". Waere das der
Mechanismus, muesste eine Streckung dem Spaltenbau helfen oder wenigstens
nichts tun. Sie schadet. **Die Praeferenz des Value-Kopfs zeigt in der Tiefe
GEGEN den Spaltenbau, und Verstaerkung verstaerkt genau das.** Nicht der
Betrag ist das Problem, sondern die Richtung.

**Daraus ein nachtraeglich hinzugefuegter Arm, ausdruecklich als solcher
gekennzeichnet:** `B=0,5` (Stauchung) bei 400 Sims. Wenn Streckung schadet,
sollte Stauchung helfen -- und das waere zugleich die Erklaerung dafuer, warum
wenige Sims mehr Spalten bauen (weniger Value-Einfluss auf die Auswahl). Die
Schwelle 0,618 bleibt unveraendert; der Arm ist explorativ und traegt kein
Verdikt, sondern erzeugt die naechste Vorregistrierung.

### STUFE 0 VOLLSTAENDIG -- PHASE 3 WIRD GESCHLOSSEN (2026-09-01)

| Arm | volle Spalten | SE | gegen Kontrolle |
| --- | --- | --- | --- |
| @100, `B=1,0` | 0,7200 | 0,0396 | +0,205 (t 3,97) |
| @400, `B=1,0` (Kontrolle) | 0,5150 | 0,0332 | -- |
| @400, `B=2,0` | 0,3900 | 0,0314 | -0,125 (t -2,7) |
| @400, `B=0,5` (explorativ) | 0,5325 | 0,0337 | +0,018 (t 0,37) |
| @400, `w=0,1` Punkte-Blend | 0,4850 | 0,0339 | -0,030 (t -0,63) |

Je 200 Partien, gleicher Seed 20260931, argmax-Instrument, Messweg gegen den
Tor-2a-Lauf validiert (0,5150 zifferngleich).

**Fehlermodell, benannt 2026-09-01 (Pruefung der Preregs):** die SE-Spalte ist
`1,96*sd/sqrt(n)/1,96` ueber die 400 SEITEN je Arm (`tools/corpus_sanity_check.py`
Zeilen 29-34), die t-Werte sind die UNGEPAARTE Quadratsumme zweier solcher SE
(0,205/sqrt(0,0396^2+0,0332^2) = 3,97). Zwei Seiten derselben Partie sind
nicht unabhaengig, und die Arme teilen den Seed, waren also gepaart
auswertbar -- so wie par.2a des Suchtiefen-Strangs es blockgepaart tut. Die
Rechnung hier ist damit optimistischer als die Projektregel (Block-Ebene)
erlaubt. Fuer das Verdikt aendert das nichts: die Schwelle 0,618 verlangt
+0,10 ueber der Kontrolle, und kein Arm liegt auch nur im Punktschaetzer
darueber; die t-Werte sind als Naeherung zu lesen, nicht als Test.

**Block-Ebene NACHGERECHNET (2026-09-02, 01:15, Korpora aus dem Backup
wiederhergestellt; `tools/probes/phase3_block_level_probe.py`, Artefakt
`evaluations/artifacts/phase3_block_level.json`).** Alle fuenf Laeufe tragen
Seed 20260931 (Manifeste geprueft), je Datei ein Block von 10 Partien, 20
Bloecke je Arm, gepaarte Differenz je Block gegen die `tor2a`-Kontrolle:

| Arm | volle Spalten | Differenz | Block-SE | t gepaart (df 19) | t Erstfassung |
| --- | --- | --- | --- | --- | --- |
| @100 (`s100`) | 0,7200 | +0,205 | 0,063 | **3,25** | 3,97 |
| @400 `B=2,0` | 0,3900 | -0,125 | 0,044 | **-2,87** | -2,74 |
| @400 `B=0,5` | 0,5325 | +0,018 | 0,048 | 0,36 | 0,37 |
| @400 `w=0,1` | 0,4850 | -0,030 | 0,033 | -0,90 | -0,63 |

Punktschaetzer zifferngleich mit der Erstfassung (Messweg bestaetigt), die
Streckung bleibt auch gepaart signifikant schaedlich, die Tiefen-Delle
bleibt signifikant. Das Verdikt von Stufe 0 steht damit auf dem Fehlermodell,
das die Projektregel verlangt.

**Verdikt: die Schwelle 0,618 wird von KEINEM Arm erreicht.** Nach der
Abbruchregel (Stufe 2) wird Phase 3 damit geschlossen und NICHT gebaut; der
Trainingslauf der Stufe 1 entfaellt.

**Was gelernt ist, und es ist mehr als ein Nein:**

1. **Die Delle existiert auch fuer b01** (0,205), nicht nur fuer b05 -- das war
   vor diesem Lauf offen.
2. **Sie haengt NICHT an der Skala des Value-Kopfs.** Stauchen (B=0,5) muesste
   in Richtung des 100-Sims-Verhaltens ziehen, wenn "zu lautes Value-Urteil in
   der Tiefe" der Mechanismus waere. Es tut nichts.
3. **Streckung schadet asymmetrisch** (-0,125 bei B=2,0, waehrend B=0,5 nichts
   bewegt). Der Kopf traegt in der Tiefe eine Praeferenz GEGEN den Spaltenbau;
   Verstaerkung legt sie frei, Daempfung ersetzt sie aber nicht durch die
   Policy-Praeferenz.
4. **Der Punkte-Blend traegt auch auf einem plattenBEWUSSTEN Netz nicht**
   (Nutzer-Einwand vom selben Tag). Einschraenkung: die alte Schliessung war
   eine STAERKE-Messung, diese hier misst Spalten -- fuer die Staerke sagt
   dieser Arm nichts.

**Die Daempfung bleibt ein registrierter Befund ohne benannten Nutzniesser.**
Sie ist gemessen, stabil und spezifisch fuer den Value-Kopf (Punkte-Kopf 0,97)
-- aber sie erklaert den Spaltenverlust in der Tiefe nicht, und ein Eingriff
ohne benannten Nutzniesser wird in diesem Projekt nicht gebaut.

**Was die Frage erbt:** die optionale Stufe 4 aus
`PREREG_search_depth_column_optimum.md` (Mechanismus-Zaehlung). Diese Messung
grenzt sie ein: die Ursache liegt nicht in der Skalierung des Blattwerts und
nicht in fehlender Punkte-Information, sondern in dem, was die tiefere Suche
mit den Kandidaten TUT.
