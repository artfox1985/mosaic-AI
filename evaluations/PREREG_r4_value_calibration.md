<!-- STATUS: ENTSCHIEDEN | Frage: Wie kalibriert ist der Value-/Punkte-Kopf am Runde-4-Ende gegen gesampelte exakte Ground Truth (Task #27-Folge)? | Beleg: v20-Aera "kein Befund". AM SCHLUSS-CHAMPION NACHGEFAHREN 2026-09-21: par.20 Kalibrierung (Value-Kopf R2 0,414 statt 0,008, Vorzeichen-Anker 71,4 statt 50,0 Prozent; NEU: der Punkte-Kopf UEBERSCHIESST, Steigung 1,19, sd 40,2 gegen wahre 18,8). par.21 Zonen-Sonde: eindeutig Hypothese (b) -- der TRUNK traegt die Information fast vollstaendig (LOO-R2 0,940 gegen Decke 0,983), die Roh-Eingabe linear nicht (0,087), die Koepfe liefern -2,18. Der Engpass ist der AUSLESEPFAD, nicht Encoder oder Kapazitaet -- und das war bei v20 schon so (Trunk 0,912). Nicht gepaart, n=72 indikativ. -->

# Vorregistrierung: Runde-4-Ende-Value-Kalibrierung gegen gesampelte exakte Ground Truth (Chance-Knoten-Erwartung)

**Angelegt 2026-08-03, VOR jeder Messung.** Ausführung gated: NACH dem vollen
Lauf der Runde-5-Kalibrierung (`PREREG_r5_value_calibration.md`, Task #27),
separat freigegeben. Die Regeln unten dürfen nach Sichtung von
Zwischenergebnissen nicht mehr geändert werden (Präzedenzfälle
`PREREG_lambda_target.md`/`PREREG_r5_value_calibration.md`).

## Übergeordnetes Ziel (Nutzer-Vorgabe 2026-08-03, präzisiert)

Den Value-Head **an den maximal möglichen R² heranführen** — ab Runde 2 ist
da "noch ordentlich Luft nach oben" (gemeint: der gemessene Value-R² je
Runde, vgl. `value_r2_rounds_1_4`/die Runden-Spalten von
`offline_diagnosis.py`, liegt deutlich unter dem, was angesichts des
Restzufalls überhaupt erreichbar wäre). Der maximal mögliche R² ist wegen
der Chance-Knoten (Rundenübergänge, in R2/R3 zusätzlich verdeckte
Kuppelplatten) STRIKT kleiner als 1 — selbst ein perfekter Schätzer von
`E[Ausgang | Zustand]` erreicht nur

```
R²_max = Var(E[z|s]) / ( Var(E[z|s]) + E[Var(z|s)] )
```

(Varianzzerlegung; `E[Var(z|s)]` = irreduzibler Zufallsanteil).

**Diese Decke wurde für Runden 1–3 BEREITS gemessen** (STATUS.md,
2026-07-21, `self_play::value_noise_floor_diagnostic`, bias-korrigierte
Varianzzerlegung, n=120 Zustände / K=16 Heuristik-Fortsetzungen je Runde):

| Runde | R²_max (korrigiert) | Modell damals (v10_best) |
|---|---|---|
| 1 | 0,0068 | −0,063 |
| 2 | 0,166 | 0,017 |
| 3 | 0,437 | 0,195 |

Genau DIESE Serie ist die Quelle des "ab Runde 2 Luft nach oben"-Befunds.
Dieses Dokument setzt die Serie am **Runde-4-Ende** fort — mit einer
METHODISCH SCHÄRFEREN Decke: die alte Messung nutzt K Heuristik-Rollouts
bis Spielende (deren Spielzug-Zufall zählt mit ins "irreduzible" Rauschen
— die Decke ist damit eine UNTERSCHÄTZUNG der unter optimalem Spiel
erreichbaren), das R4-Design ersetzt die Fortsetzung durch EXAKTES
Optimal-Spiel (`round5.rs`) — als Rauschquelle bleibt allein der echte
Chance-Knoten (Fabrik-Neubefüllung). Erwartung daher: exakte R4-Decke ≥
eine heuristische R4-Decke. Zusätzlich misst dieses Experiment die
KALIBRIERUNG des Modells gegen `E[z|s]` selbst — das konnte die alte
Methode nicht (sie lieferte nur die Zerlegungs-Terme, keinen
Zustand-für-Zustand-Ground-Truth-Vergleich). Runde 3/2 sind Ausblick
(verschachtelte Chance-Knoten, siehe unten), nicht Teil dieser
Vorregistrierung.

## Kern-Erkenntnis, die dieses Design trägt (Nutzer-Fund, code-verifiziert)

**Ab dem Runde-4-Ende ist das Brett vollständig bekannt.** Der Nutzer-Hinweis
(2026-08-03): schon beim Start in Runde 4 liegen keine unbekannten
Kuppelplatten mehr im Stapel. An echten Self-Play-Daten verifiziert
(v19-Kampagne, letzte R4-Records je Partie): `dome_stack_count=0`,
`dome_display=0` durchgängig. Die EINZIGE verbleibende Unsicherheit am
Runde-4-Ende ist die Fabrik-Neubefüllung des Übergangs 4→5
(`state.rs::setup_new_round` → `fill_factories`): welche Sonnenplättchen aus
dem (als Multiset zählbaren, aber in der Fabrik-Zuordnung zufälligen) Beutel
auf welche Fabrik fallen, plus die Bonus-Chip-Zuteilung aus dem verdeckten
Pool.

Ein Runde-4-Endzustand hat also **keinen exakten Einzelwert** (das war die
ehrliche Ausgrenzung in `PREREG_r5_value_calibration.md`), aber eine **exakt
definierte Erwartung über eine bekannte Verteilung**: jeder gesampelte
Refill erzeugt einen Runde-5-Startzustand, und DER ist per `round5.rs`
exakt lösbar (Full-Information-Endspiel, `ab_value` wie im R5-Dokument).

## Ground Truth je Runde-4-Endzustand

K gesampelte Neubefüllungen desselben Runde-4-Endbretts; je Sample s_k der
exakte Alpha-Beta-Wert des entstehenden Runde-5-Startzustands über den
BESTEHENDEN Einstieg (identisch zu `PREREG_r5_value_calibration.md`,
Abschnitt "Ground Truth"):

```
ab_value_k = net_search_state_json(refill_k, model_path_for_api, sims, c_puct, seed)
             -> moves[ai_action]["ab_value"]     # exakte Punkte-Marge
```

Daraus ZWEI Ground-Truth-Größen je Zustand:

1. **`true_margin` = Mittel der `ab_value_k`** — erwartete Punkte-Marge
   unter optimalem Runde-5-Spiel (Skala des Punkte-Kopfs).
2. **`true_winprob` = Anteil der Refills mit `ab_value_k > 0`**
   (`== 0` zählt 0,5, Tie-Break-Regeln stecken bereits in
   `player_total_exact`) — exakte Gewinnwahrscheinlichkeit unter
   beidseitig optimalem Runde-5-Spiel. **Direkt auf der
   Gewinnwahrscheinlichkeits-Skala des Value-Kopfs — die empirische
   Punkte→Sieg-Kennlinie des R5-Designs wird hier NICHT gebraucht**
   (methodischer Vorteil dieses Experiments: die Sättigungs-/
   Kennlinien-Problematik aus dem R5-Dokument entfällt komplett).

## Positions-Substrat: Paare (letzter R4-Record, erster R5-Record) aus Self-Play

`evaluations/frozen_eval_set.pkl` scheidet aus — geprüft 2026-08-03: die 233
R5-Drafting-Records sind ALLE mid-Drafting (0 Rundenstart-Zustände mit
unberührten Fabriken), eine Rekonstruktion des Vor-Befüllungs-Zustands ist
daraus nicht möglich. Stattdessen **Self-Play-Dateien des amtierenden
Champions** (neuester verfügbarer Bestand zum Ausführungszeitpunkt; Stand
heute: v19-Kampagne in `data/`): dort trägt jede abgeschlossene Partie

- den **letzten R4-Record** (Zustand VOR der letzten R4-Aktion) — das ist
  der **Modell-Input** (in-distribution: genau solche Zustände sieht das
  Netz in Training und Suche), Regel: `phase=="tiling"` verlangt, sonst
  Partie ausschließen (Ausschlussquote wird berichtet);
- den **ersten R5-Record** (Zustand NACH der echten Befüllung, VOR dem
  ersten R5-Zug) — dient als Konsistenz-Anker des deterministischen
  Vorlaufs und liefert die reale Befüllung als 17. Sample (siehe
  Vorbedingung unten; Redesign 2026-08-03: Vorwärts-Sampling statt
  Inversion).

**Konsistenz der beiden Seiten**: zwischen letztem R4-Record und Rundenende
liegt nur noch Solver-Tiling (beide Spieler, DFS-Solver, exakt/optimal und
deterministisch) — das tatsächliche R4-Endbrett (== Brett des ersten
R5-Records minus Befüllung) ist damit die deterministische, optimale
Fortsetzung des Modell-Input-Zustands. Die Ground Truth ist also konditional
auf optimales Rest-R4-Spiel — exakt die Semantik, die ein idealer Value-Head
an dieser Stelle hätte.

**Perspektiven-Mapping** (Pflicht, sonst Vorzeichenfehler): `ab_value` ist
aus Sicht des R5-Startspielers (`current_player` des ersten R5-Records,
== `first_player_next_round`), Modell-Value aus Sicht des `current_player`
des R4-End-Records — beide werden auf eine feste Spieler-0-Perspektive
gemappt (Margin-Vorzeichen flippen bzw. p → 1−p, wo nötig).

## Vorbedingung (Rust, additiv) — REDESIGN 2026-08-03, VOR jeder Messung

**Erster Entwurf (Inversion vom R5-Start aus,
`resample_round_transition_json`) ist implementiert und getestet, aber
für den Messpfad VERWORFEN**: Die Turm-Reshuffle-Ausschlussregel (leerer
Turm nach Befüllung = nicht eindeutig invertierbar) trifft auf dem
vollen Korpus **87,6% aller Partien** (9000 gescannt; ein früherer
0%-Befund war ein Messfehler — `tower_colors` ist ein Farb-Zähl-Array,
leer heißt Summe==0). Ein 12%-Rest-Substrat wäre zudem systematisch
verzerrt (Partien ohne Turm-Reshuffle am Übergang).

**Messpfad-Binding (Vorwärts-Sampling, vermeidet die Ambiguität
vollständig):**

```
mosaic_rust.autoplay_to_round5_and_resample_json(r4_state_json, n_samples, seed)
```

Semantik: `json_to_state` auf dem LETZTEN R4-Record (Beutel/Turm sind
dort als exakte Zähl-Multisets öffentlich bekannt), dann DETERMINISTISCHER
Vorlauf bis zum Rundenende (Solver-Tiling beider Spieler +
Rundenende-Wertung/Abwürfe — bestehende Engine-Pfade, kein RNG), dann
n-mal `setup_new_round` mit per-Sample-RNG auf Kopien — der natürliche
Beutel-leer→Turm-Reshuffle-Pfad läuft dabei regelkonform mit. KEIN
Ausschluss, 100% Substrat, und Modell-Input (letzter R4-Record) und
Ground-Truth-Ausgangspunkt sind DERSELBE Zustand (die frühere
Rekonstruktions-Brücke über den ersten R5-Record entfällt als
Fehlerquelle; der erste echte R5-Record dient weiterhin als
Konsistenz-Anker: der deterministische Vorlauf muss sein Brett modulo
Befüllung reproduzieren). Wheel-Build nötig (Koordinator).
Implementierungs-Detail (Agent-Befund): der zurückgegebene `r4_end_state`
liegt VOR dem finalen `EndTiling` — Rundenend-Strafen/Bodenräumung sind
dort noch nicht verrechnet (passieren je Sample in `advance_one_chance`).
Der Konsistenz-Anker vergleicht daher KUPPEL-BRETTER (dome_grids), nicht
Scores/Bodenreihen.

## Messgrößen (je Modell separat: `v19_2d_best` primär [Champion],
## `v18_best`/`v19_best` sekundär zur Generationen-Einordnung)

Je Modell zwei Regressionen über die N Zustände (beide Köpfe getrennt, wie
im R5-Dokument):

1. **Value-Kopf**: OLS-Steigung + R² von `value_to_win_prob(raw_value)`
   (Torch-Pfad, identischer Code wie `tools/r5_value_calibration.py`) gegen
   `true_winprob`.
2. **Punkte-Kopf**: OLS-Steigung + R² von `50*atanh(clamp(raw_points))`
   gegen `true_margin`.
3. **Decken-Quantifizierung: maximal möglicher R² am R4-Ende** (das
   Kernstück der Nutzer-Agenda). Über die N Zustände, je Skala:
   - **Sieg-Skala** (`z_k = ±1` je Refill, Value-Kopf-Ziel):
     `R²_max = Var_s(2·p_s−1) / ( Var_s(2·p_s−1) + mean_s[4·p_s(1−p_s)·K/(K−1)] )`
     mit `p_s` = Refill-Gewinnquote des Zustands (K/(K−1) =
     Endlichkeits-Korrektur des Binnen-Varianz-Schätzers).
   - **Margen-Skala** (Punkte-Kopf):
     `R²_max = Var_s(true_margin_s) / ( Var_s(true_margin_s) + mean_s[Var_k(ab_value_k)] )`
     (Binnen-Varianz mit Stichproben-Korrektur n−1).
   Dagegen gestellt: der **realisierte Modell-R²** auf denselben N
   Zuständen, je Kopf auf seiner Skala — einmal gegen die EINZELNEN
   Refill-Ausgänge (direkt vergleichbar mit R²_max, gleiche Definition wie
   die bestehende `value_r2`-Metrik: Prädiktor vs. realisierter Ausgang)
   und einmal gegen `E[z|s]`/`true_margin` (misst den reinen
   Schätzfehler-Anteil, frei vom irreduziblen Term). Die Differenz
   `R²_max − R²_modell` ist die **beziffbare "Luft nach oben"** am
   R4-Ende.

### Anschlussmessung an die bestehende Noise-Floor-Serie (sekundär)

Zur Serien-Vergleichbarkeit mit den R1–R3-Werten läuft ZUSÄTZLICH die
BESTEHENDE Diagnostik `self_play::value_noise_floor_diagnostic` mit
`target_round=4` (identische Parameter wie 2026-07-21: n_states=120,
k_rollouts=16 — vorhandenes Werkzeug, Memory
`feedback_check_existing_tools_first`). Erwartung: heuristische R4-Decke
zwischen R3-Wert (0,437) und der exakten Decke dieses Experiments. Eine
DEUTLICHE Abweichung von dieser Ordnung (exakt < heuristisch, außerhalb der
Schätzfehler) wäre ein Methoden-Alarm (eine der beiden Messungen hätte dann
ein Problem) und wird VOR jeder inhaltlichen Interpretation geklärt.

## Parameter (VORAB festgelegt)

- **N = 24 Zustände** (zufällig aus den geeigneten Partien, fester Seed im
  Werkzeug), **K = 16 Refills** je Zustand, PLUS die reale Befüllung als
  17. Sample (Konsistenz-Anker: ihr `ab_value`-Vorzeichen wird gegen den
  tatsächlichen Partie-Ausgang geprüft und berichtet — grobe Validierung
  der gesamten Rekonstruktions-Kette).
- Kosten: ≤ 24×17 ≈ 408 Alpha-Beta-Aufrufe à ≤5s ≈ ~35 min (Torch-Forwards
  vernachlässigbar). Läuft auf idler Maschine (Alpha-Beta ist
  zeitbudgetiert, CPU-Konkurrenz würde die Ground Truth verrauschen —
  gleiche Betriebsregel wie beim R5-Lauf).
- Binomial-Auflösung bei K=16: SE ≈ 0,125 bei p=0,5 — reicht für die
  Steigungs-/R²-Aussage ÜBER 24 Zustände (der Regressionsfehler mittelt
  sich), NICHT für Einzelzustands-Feinurteile (ehrlich benannt, keine
  Einzelfall-Interpretation).

## Vorab-Interpretationsregeln

- **Steigung ≈ 1 (95%-KI überdeckt [0,85; 1,15]) und R² ≥ 0,5**: Kopf am
  R4-Ende gut kalibriert — die "Luft nach oben" liegt dann NICHT an dieser
  Stelle, Fokus auf frühere Runden verschieben.
- **Steigung deutlich <1 (KI-Obergrenze <0,85)**: Unterkalibrierung am
  R4-Ende bestätigt — konsistent mit dem R5-Befund wäre das ein
  struktureller "Endspiel-Zonen"-Befund über beide Runden; Diagnose-
  Kandidaten wie im R5-Dokument (Zielrauschen/λ-Kontext vor
  Rezeptwechsel).
- **Steigung ≈ 0 (KI überdeckt 0 UND komplett unter 0,3)**: Kopf ignoriert
  die R4-End-Information faktisch — eigener, stärkerer Befund, separate
  Ursachenanalyse.
- **R² < 0,1**: kein interpretierbarer Befund (mehr Zustände/Refills nötig,
  bevor irgendeine Aussage getroffen wird).
- **Decken-Regel** (unabhängig von den obigen, auf der Sieg-Skala des
  Value-Kopfs): `R²_modell ≥ 0,8 · R²_max` → als "nahe an der Decke"
  einstufen, R3/R2 priorisieren (siehe Ausblick); `R²_modell < 0,5 · R²_max`
  → große schließbare Lücke, R4-Ende bleibt eigener Hebel. Dazwischen:
  beides berichten, keine automatische Priorisierung. (Die Schwellen sind
  bewusst grob — bei N=24/K=16 trägt `R²_max` selbst einen Schätzfehler,
  der per Bootstrap über die Zustände mitberichtet wird.)

## Bekannte Einschränkungen, bewusst akzeptiert

1. **`ab_value` ist "exakt, wenn das Budget nicht bindet"** — von
   RUNDENSTART-Zuständen aus bindet das `NODE_BUDGET`/`TIME_BUDGET` eher
   häufiger als mid-Round (R5-Dokument, Einschränkung 1). Anteil
   Deadline-Läufe wird berichtet; systematischer Bias zwischen den Refills
   desselben Zustands unwahrscheinlich (gleiche Brettkomplexität).
2. **Optimal-Spiel-Annahme**: `true_winprob` gilt unter beidseitig
   optimalem R5-Spiel. Die Self-Play-Partien spielen Runde 5 mit demselben
   `round5.rs`-Solver — Substrat und Ground Truth sind damit konsistent.
3. **Rest-R4 = Solver-Tiling als deterministisch/optimal angenommen** —
   trifft auf das Substrat konstruktionsbedingt zu (Ausschlussregel oben).
4. **ONNX (Live) vs. Torch (Messung)** — identische Einschränkung wie im
   R5-Dokument (kein separater Paritätstest).
5. **Substrat gebunden an den Generator-Checkpoint-Stand** der verwendeten
   Self-Play-Kampagne — kein für alle Zukunft gültiger Absolutwert.

## Ausblick Runde 3/2 (Nutzer-Ziel "ab Runde 2", NICHT Teil dieser Vorregistrierung)

Für Runde 2/3 existieren bereits HEURISTISCHE Decken (Serie 2026-07-21,
siehe oben) — dort ist die Lücke zum Modell der eigentliche Befund (R2:
0,166 möglich vs. 0,017 erreicht). Eine SCHÄRFERE (exakte) Ground Truth wie
in diesem R4-Design ist dort nicht direkt übertragbar: Runde 3-/2-Zustände
haben VERSCHACHTELTE Chance-Knoten (jeder weitere Rundenübergang einer)
plus echte verdeckte Kuppelplatten — exaktere Decken dort gingen nur per
rekursivem Sampling + Suche (Kostenexplosion: jedes R3-Sample bräuchte
selbst wieder eine R4-Bewertung wie oben). Der näherliegende R2/R3-Hebel
ist laut damaligem Befund ohnehin TRAINING (Lücke schließen), nicht
Decken-Messung (Lücke neu vermessen). Ob und wie das angegangen wird,
entscheidet sich NACH dem Ergebnis dieses Experiments (Decken-Regel oben
liefert genau dafür die Priorisierung).

## Ausführungsplan

1. Rust-Vorbedingung (`resample_round_transition_json`) + Wheel-Build
   (Koordinator).
2. Werkzeug `tools/r4_value_calibration.py` (Vorbild + Import-Wiederverwendung
   `tools/r5_value_calibration.py`, Memory `feedback_check_existing_tools_first`).
3. Rauchtest: 2 Zustände × 3 Refills × 1 Modell — Plausibilität
   (Vorzeichen, Perspektiven-Mapping am Konsistenz-Anker, Refill-Streuung
   > 0). Kein voller Lauf, kein Ergebnis-Blick über den Rauchtest hinaus.
4. STOPP — Bericht an den Koordinator.
5. NACH separater Freigabe (nach dem vollen R5-Lauf): voller Lauf
   (N=24, K=16+1, alle 3 Modelle) → `evaluations/artifacts/r4_value_calibration_result.json`.
6. Bericht mit den vorregistrierten Kennzahlen; danach Entscheidung über
   die R3/R2-Folge-Vorregistrierung.

---
**STATUS (Stand 2026-08-08): ENTSCHIEDEN** -- der volle Lauf (N=24, K=16,
3 Modelle) fand statt und erzeugte `evaluations/artifacts/r4_value_calibration_result.json`.
Formales Ergebnis nach eigener Regel: "kein Befund" (Modell-R² aller drei
Netze negativ, -0,15 bis -0,21). Der eingebaute Vorzeichen-Anker-Check
deckte zusaetzlich einen METHODEN-ALARM auf: nur 9/24 korrekt (statt
hoher Trefferquote) -- `NODE_BUDGET=200` bindet am Rundenstart praktisch
immer, `ab_value` ist dort nur eine flache Naeherung statt exakt (erklaert
rueckwirkend auch die schwache R5-Kennlinie, McFadden 0,316). Konsequenz:
eine methodisch schaerfere Nachfolge-Messung ("R4b", Playout-Ground-Truth,
N=72) wurde initiiert. Belegstelle: Git-Commit `cb4773d` ("R4-Kalibrierung
+ Noise-Floor-R4: METHODEN-ALARM durch eigenen Anker-Check", 2026-08-03) --
in archive/history.md selbst gibt es dazu KEINEN Prosa-Absatz, nur
Vorbereitung (Zeile ~6941-6958); die Commit-Message ist die einzige
textuelle Verdikt-Quelle. Nicht zu verwechseln mit dem spaeteren, separaten
"R4b"-Task (`evaluations/artifacts/r4b_value_calibration_wdl.json`, N=72, andere
Methodik, eigene Vorregistrierung/eigenes Werkzeug).

## par.20 R4b AM SCHLUSS-CHAMPION GEFAHREN (2026-09-21, Nutzer-Auftrag)

**Nutzer: *"dann zieh das auch am aktuellen champion"*** -- im Anschluss an die Feststellung, dass
die R5-Sonde wieder lauffaehig ist, R4b aber nicht.

### Warum das kein Nachziehen war, sondern eine neue Messung

Meine erste Auskunft war die halbe Wahrheit. Ich hatte gesagt, `r4b_zone_probe` sei an
`alphazero_v20_2d_opp_brierbest.pth` gebunden, weil derselbe Name Schluessel der Referenzwerte im
eingefrorenen JSON ist. Das stimmt, ist aber nicht der harte Blocker. **Der harte Blocker ist das
SUBSTRAT:** `r4b_value_calibration_v20_n72.json` traegt als `data_glob` den Wert
`data/selfplay_v18_*.pkl` -- **0 Dateien im Baum**, der Korpus ist geloescht. Und die 72 Zustaende
selbst stehen NICHT im Artefakt (`per_state` traegt nur Kennzahlen, keinen Zustand). Die
Zustands-Reproduktion, die das Werkzeug als erstes prueft, kann also gar nicht gelingen.

**Der gangbare Weg ist deshalb eine frische Messung**, und sie ist vollwertig: die Grundwahrheit
(`true_margin`/`true_winprob`, exakte Alpha-Beta-Marge ueber 16 Neubefuellungen) ist
MODELLUNABHAENGIG. Neue Zustaende aus einem aktuellen Korpus, frische Grundwahrheit, Champion
darauf gemessen.

### Lauf

`tools/r4_value_calibration.py`, Modell `models/frozen_champions/v31-b01/model.pth`, Substrat
`data/selfplay_v30-b02-policy_*.pkl` (die v31-Erzeugung), n = 72 Zustaende, k = 16 Refills,
400 Sims, c_puct 1,5, `state_seed` 20260803 -- dieselben Stellgroessen wie die v20-Referenz.
Auswahl: 58 Dateien gescannt, 580 Partien, **0 Ausschluesse**.
Artefakt: `evaluations/artifacts/r4_value_calibration_v31-b01_n72.json`.
**Laufzeit 2.693,7 s (44 min 55 s), 37,4 s je Zustand.**

### Ergebnis

| Kennzahl | v20 (2026-08) | **v31-b01 (2026-09-21)** |
| --- | --- | --- |
| Value-Kopf Steigung | 0,0562 | **0,4540** |
| Value-Kopf R2 | 0,0078 | **0,4142** |
| Punkte-Kopf Steigung | 0,3235 | **1,1930** |
| Punkte-Kopf R2 | 0,1786 | **0,3116** |
| Decke `r2_max` win / margin | 0,9672 / 0,9742 | 0,9139 / 0,9827 |
| realisiert `win_scale_vs_expected` | -0,3375 | **+0,4104** |
| realisiert `margin_scale_vs_expected` | +0,0309 | **-2,1830** |
| Vorzeichen-Anker | 36 von 72 = 50,0 % | **50 von 70 = 71,4 %** |

**Die Steigung ist d(Modell)/d(Wahrheit)** (`ols_slope_r2(x=Wahrheit, y=Modell)`, am Code
geprueft) -- Werte unter 1 heissen GEDAEMPFT, ueber 1 UEBERSCHIESSEND.

**Lesart, vorsichtig:**

1. **Der R4b-Befund der v20-Aera gilt fuer den Schluss-Champion nicht mehr.** Er lautete "beide
   Koepfe blind fuer exakte R4-End-Info, R2 ~ 0". Der Value-Kopf liegt jetzt bei R2 = 0,414 gegen
   eine EXAKTE Grundwahrheit, und der Vorzeichen-Anker trifft 71,4 statt 50,0 Prozent -- 50 Prozent
   war der Muenzwurf, der damals den Methoden-Alarm ausgeloest hat.
2. **Der Betrag hat die Seite gewechselt.** Die v20-Koepfe waren gedaempft (0,056 / 0,323); der
   Champion ueberschiesst beim Punkte-Kopf (1,193). Gemessen an den Streuungen: die wahre Marge
   hat sd 18,80, die Modell-Marge sd 40,17 -- **Faktor 2,1 zu weit**. Genau das erklaert das stark
   negative `margin_scale_vs_expected` von -2,18: ohne Nachskalierung ist die absolute Marge
   schlechter als der Mittelwert-Vorhersager, obwohl sie mit r = 0,56 klar korreliert. Die
   Information IST da, die Skala stimmt nicht.
3. **Kein Widerspruch zu den beiden Zahlen:** R2 = 0,3116 ist der Wert NACH Anpassung von Steigung
   und Achsenabschnitt, -2,18 der Wert OHNE. Rechnerisch konsistent
   (r = 0,556; 0,556 x 40,17/18,80 = 1,19 = die Steigung).

### Was diese Zahlen NICHT sind

**Kein gepaarter Vergleich.** Die v20-Messung lief auf Zustaenden aus dem v18-Korpus, diese auf
Zustaenden aus der v31-Erzeugung. Andere Stellungen, andere Decke (`r2_max` win 0,967 gegen
0,914 -- die Decke ist substrat-, nicht modellabhaengig). **Die Spalten stehen nebeneinander, sie
sind nicht voneinander abgezogen.** Ein sauberer Delta-Wert braeuchte beide Modelle auf DEMSELBEN
Substrat; das v18-Modell dafuer liegt nicht mehr im Baum. Die Richtung ist bei diesen Abstaenden
belastbar, die zweite Stelle nicht.

**Zweiter Vorbehalt, n = 72.** Das war schon in der v20-Messung als "nur indikativ" vermerkt und
gilt unveraendert.

### Zwei Maengel am Werkzeug, mitbehoben

* **Dieselben toten Defaults wie bei R5** (`--models` auf drei geloeschte Checkpoints,
  `--data-glob` auf den geloeschten v18-Korpus, `--model-path-for-api` auf ein geloeschtes ONNX).
  Die beiden ersten sind jetzt `required`, der dritte loest auf den amtierenden Champion auf --
  laut Moduldoku wird sein Inhalt fuer Runde-5-Zustaende nie benutzt, nur seine Ladbarkeit.
* **Der Lauf war STUMM**: zwischen Auswahl-Statistik und Ergebnis kam 45 Minuten lang keine Zeile,
  derselbe Regelverstoss wie bei `build_frozen_golden_probe.py`. Jetzt eine Zeile je Zustand mit
  Laufzeit und `flush`. Und er schrieb **keinen `laufzeit`-Block** -- jetzt ueber
  `runtime_block.laufzeit_block` mit Einheit `s_je_zustand`, weil dieses Werkzeug keine Partien
  spielt. Die Laufzeit DIESES Laufs ist aus den Harness-Zeitstempeln nachgetragen und im Artefakt
  als solche gekennzeichnet, statt sie verfallen zu lassen.

### Offen

`r4b_zone_probe.py` (die URSACHEN-Analyse: Ridge von Trunk-Embedding bzw. Roh-Eingabe auf die
Grundwahrheit) ist damit wieder fahrbar -- sie braucht nur `R4B_JSON` und `MODEL_KEY` auf das neue
Artefakt gezogen. Ihre Frage "wo geht die Information verloren" ist durch dieses Ergebnis aber
verschoben: sie war fuer R2 ~ 0 gestellt, und der Value-Kopf liegt jetzt bei 0,414 gegen eine
Decke von 0,914. Die schaerfere Frage waere die SKALA des Punkte-Kopfs (Faktor 2,1 zu weit), nicht
mehr die Blindheit. Nicht gefahren, Nutzer-Entscheid.

## par.21 ZONEN-SONDE AM CHAMPION (2026-09-21, Nutzer-Auftrag "dann fahr die zonen sonde")

`tools/r4b_zone_probe.py` gegen das neue Artefakt aus par.20. Die Sonde fragt, WO die exakte
R4-End-Information verloren geht: (a) der EINGANG traegt sie nicht, (b) der TRUNK traegt sie und
die Koepfe nutzen sie nicht, (c) sie ist ueberhaupt nicht linear zugaenglich.

**Laufzeit 44,4 s**, 72 Zustaende Feld fuer Feld reproduziert (`game_id`s identisch zum
Kalibrierlauf), Trunk-Embedding (72, 512), Eingabe-Merkmale (72, 3.732).

| LOO-Ridge-Probe | v20 (2026-08) | **v31-b01 (heute)** |
| --- | --- | --- |
| Trunk -> `true_margin` | 0,9115 | **0,9400** |
| Trunk -> `true_winprob` | 0,9159 | **0,9270** |
| Roh-Eingabe -> `true_margin` | -0,0085 | +0,0870 |
| Roh-Eingabe -> `true_winprob` | -0,0266 | +0,0340 |
| **Koepfe realisiert** win / margin | -0,3375 / +0,0309 | **+0,4104 / -2,1830** |
| Decke win / margin | 0,9672 / 0,9742 | 0,9139 / 0,9827 |

### Befund: Hypothese (b), und zwar unveraendert seit v20

**Der Trunk traegt die Information fast vollstaendig.** 0,940 gegen eine Decke von 0,983 auf der
Margen-Skala -- eine LINEARE Probe auf dem 512er-Embedding holt praktisch alles heraus, was
ueberhaupt herauszuholen ist. **Die Roh-Eingabe gibt sie linear NICHT her** (0,087 / 0,034). Das
Netz hat die Repraesentation also selbst gebaut; sie liegt nicht schon im Encoder bereit.

Nach der vorab formulierten Lesart der Sonde ist das eindeutig **(b): Ziel-/Kopf-Problem.** Nicht
(a) -- der Eingang traegt sie, sonst koennte der Trunk sie nicht bilden. Nicht (c) -- sie ist
linear zugaenglich, nur eben erst NACH dem Trunk.

**Und das war schon bei v20 so.** 0,9115 damals, 0,9400 heute: der Trunk war nie das Nadeloehr.
Was sich zwischen den Generationen bewegt hat, ist der AUSLESEPFAD, nicht die Repraesentation.

### Die Schere ist das eigentliche Ergebnis

Trunk 0,940, Kopf -2,183 auf derselben Groesse. **Die Information ist da und wird beim Auslesen
zerstoert** -- passend zu par.20: der Punkte-Kopf ueberschiesst um Faktor 2,1 in der Streuung
(sd 40,2 gegen wahre 18,8). Auf der Gewinn-Skala hat der Auslesepfad zwischen v20 und v31
deutlich aufgeholt (-0,338 -> +0,410), auf der Margen-Skala ist er ABSOLUT schlechter geworden
(+0,031 -> -2,183), obwohl er relativ besser ordnet (R2 nach Anpassung 0,179 -> 0,312).

**Was das fuer eine Fortsetzung hiesse** (nicht gebaut, keine Empfehlung ohne Messung): der Hebel
sitzt nicht im Encoder und nicht in der Trunk-Kapazitaet, sondern in der SKALIERUNG des
Margen-Ziels. Das deckt sich mit `feedback_value_head_capacity` ("Plateau erst auf
Kapazitaets-Hunger pruefen") nur zur Haelfte: Kapazitaet ist hier nachweislich NICHT der Engpass.

### Vorbehalte, ausdruecklich

1. **Nicht gepaart.** Wie in par.20: der v20-Lauf sass auf Zustaenden aus dem geloeschten
   v18-Korpus, dieser auf Zustaenden der v31-Erzeugung. Andere Stellungen, andere Decke. Die
   Spalten stehen nebeneinander.
2. **n = 72 bei 512 Merkmalen**, also p >> n. Die LOO-Ridge ist eine echte Kreuzvalidierung (exakt
   ueber die Hut-Matrix, kein Refit je Sample), aber **das beste Alpha liegt in BEIDEN Laeufen am
   unteren Rand des Suchgitters** (1,0 von 1,0/10/100/1.000/10.000). Ein Randwert heisst: das
   Gitter hat das Optimum nicht eingeschlossen, noch weniger Regularisierung waere moeglicherweise
   besser gewesen. Die Hoehe von 0,94 ist damit nach oben nicht abgesichert; die AUSSAGE (Trunk
   >> Kopf) traegt trotzdem, weil zwischen 0,94 und -2,18 kein Gitterproblem liegt.
3. Die Sonde war schon in der v20-Fassung als "bei n = 72 nur indikativ" markiert. Das gilt
   unveraendert.

### Werkzeug

Die Sonde hing an zwei KONSTANTEN (`R4B_JSON`, `MODEL_KEY`) und war damit an einen Lauf genagelt,
dessen Substrat nicht mehr existiert. Jetzt Argumente (`--r4b-json`, `--model-key`, `--out`) mit
Default auf das Champion-Artefakt; der Modellschluessel wird, wenn nicht angegeben, aus dem JSON
gelesen (bei mehreren Modellen bricht sie ab statt zu raten). Der Ausgabename war auf `_v20`
genagelt -- er haette den naechsten Lauf still ueberschrieben oder falsch etikettiert und wird
jetzt aus dem Modellnamen abgeleitet. Dazu Herkunftsfelder (`referenz_json`, `model_key`,
`substrat`) und der `laufzeit`-Block.
