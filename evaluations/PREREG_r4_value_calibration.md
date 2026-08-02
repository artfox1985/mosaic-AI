# Vorregistrierung: Runde-4-Ende-Value-Kalibrierung gegen gesampelte exakte Ground Truth (Chance-Knoten-Erwartung)

**Angelegt 2026-08-03, VOR jeder Messung.** Ausführung gated: NACH dem vollen
Lauf der Runde-5-Kalibrierung (`PREREG_r5_value_calibration.md`, Task #27),
separat freigegeben. Die Regeln unten dürfen nach Sichtung von
Zwischenergebnissen nicht mehr geändert werden (Präzedenzfälle
`PREREG_lambda_target.md`/`PREREG_r5_value_calibration.md`).

## Übergeordnetes Ziel (Nutzer-Vorgabe 2026-08-03)

Den Value-Head **an die maximal mögliche Vorhersagequalität heranführen** —
ab Runde 2 ist da "noch ordentlich Luft nach oben". Dieses Dokument ist der
Runde-4-Baustein dieser Agenda: es misst nicht nur, WIE gut der Value-Head
am Runde-4-Ende kalibriert ist, sondern quantifiziert erstmals auch die
**theoretische Obergrenze** (den irreduziblen Zufallsanteil des
Rundenübergangs), gegen die "maximal möglich" überhaupt definiert ist.
Runde 3/2 sind Ausblick (verschachtelte Chance-Knoten, siehe unten), nicht
Teil dieser Vorregistrierung.

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
  ersten R5-Zug) — aus ihm wird die Befüllung invertiert und neu gesampelt
  (siehe Vorbedingung unten).

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

## Vorbedingung (Rust, additiv — noch NICHT gebaut)

Es gibt keinen Python-Einstieg fürs Übergangs-Sampling (geprüft:
`lib.rs`/`py.rs` exportieren nur `net_search_state_json`/`_trace` u.ä.).
Nötig ist ein kleiner additiver Binding-Einstieg:

```
mosaic_rust.resample_round_transition_json(r5_start_state_json, n_samples, seed)
  -> Liste von n_samples R5-Start-state_jsons
```

Semantik: `json_to_state` (mit Neumischung verdeckter Information wie
gehabt), dann Fabrik-Inhalte + Bonus-Chips zurücklegen (Beutel/Pool),
dann `fill_factories` n-mal mit frisch geseedetem RNG. Wheel-Build nötig
(Koordinator). **Turm-Reshuffle-Grenzfall**: Partien, bei denen die
ORIGINAL-Befüllung einen Turm-Reshuffle in den Beutel auslöste, sind nicht
eindeutig invertierbar — solche Zustände werden AUSGESCHLOSSEN (Detektion
konservativ, z.B. über das Log-Ereignis bzw. die Beutel-Zählung; Umsetzung
beim Implementierer, Ausschlussquote wird berichtet).

## Messgrößen (je Modell separat: `v19_2d_best` primär [Champion],
## `v18_best`/`v19_best` sekundär zur Generationen-Einordnung)

Je Modell zwei Regressionen über die N Zustände (beide Köpfe getrennt, wie
im R5-Dokument):

1. **Value-Kopf**: OLS-Steigung + R² von `value_to_win_prob(raw_value)`
   (Torch-Pfad, identischer Code wie `tools/r5_value_calibration.py`) gegen
   `true_winprob`.
2. **Punkte-Kopf**: OLS-Steigung + R² von `50*atanh(clamp(raw_points))`
   gegen `true_margin`.
3. **Decken-Quantifizierung ("Luft nach oben")**: je Zustand die
   Refill-Streuung (`std(ab_value_k)`; Binomial-SE der Winrate
   `sqrt(p̂(1−p̂)/K)`), gemittelt über Zustände = **irreduzibler
   Unsicherheitsanteil am R4-Ende**. Dagegen gestellt: RMSE des
   Modell-Value gegen `true_winprob`. Modell-RMSE ≫ Sampling-Rauschen
   → echte, schließbare Lücke; Modell-RMSE ≲ 1,5× Sampling-Rauschen
   → "nahe an der Decke" (dann ist die R3/R2-Erweiterung der
   wichtigere nächste Hebel, nicht weiteres R4-Tuning).

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
- **Decken-Regel** (unabhängig von den obigen): Modell-RMSE ≤ 1,5× des
  mittleren Sampling-Rauschens → als "nahe an der Decke" einstufen, R3/R2
  priorisieren (siehe Ausblick).

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

Runde 3-/2-Zustände haben VERSCHACHTELTE Chance-Knoten (jeder weitere
Rundenübergang einer) plus in R2/R3 noch echte verdeckte Kuppelplatten —
eine Ground Truth dort ist nur per rekursivem Sampling + Suche statt exakter
Rechnung erreichbar (Kostenexplosion: jedes R3-Sample bräuchte selbst wieder
eine R4-Bewertung wie oben). Ob und wie das angegangen wird, entscheidet
sich NACH dem Ergebnis dieses Experiments (Decken-Regel oben liefert genau
dafür die Priorisierung).

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
   (N=24, K=16+1, alle 3 Modelle) → `evaluations/r4_value_calibration_result.json`.
6. Bericht mit den vorregistrierten Kennzahlen; danach Entscheidung über
   die R3/R2-Folge-Vorregistrierung.
