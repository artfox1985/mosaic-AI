# Mosaic-AI AlphaZero-Loop — Status & Fahrplan

Historische Details (alte v1-v9-Zählung vor dem Reset, Bug-Diagnosen,
verworfene Ansätze) stehen in der Git-Historie dieser Datei und in den alten
`v*_eval.md`s — hier nur der aktuelle Stand und die aktiven Regeln.

## Aktueller Stand (Stand: v6, siehe Masterplan unten für die nächsten Schritte)

Der erste Reset (2026-07-07, v1/v1b/v2/v2b/v2c) ist selbst überholt — das
Datenfenster wurde seitdem komplett neu aufgesetzt (~11.000 frische
Heuristik-Spiele), Zählung beginnt wieder bei v1. VALUE_WEIGHT ist final auf
**1** gesetzt (siehe Confounder-Ergebnis unten: das Gewicht ist für Stufe 1
UND Stufe 2 irrelevant, kein weiterer Sweep nötig).

**v2 ist seitdem Champion und hat vier Kandidaten (v3, v4, v5, v6) klar
abgewehrt** — alle vier kamen per SPRT-Arena (siehe Werkzeuge unten) als
"Gleich stark" zurück, keiner hat das +100-Elo-Gate gerissen:

| Netz | Fenster-Zusatz ggü. Vorgänger              | vs. v2 (Stufe 1) | vs. v2 (Stufe 2)   |
| ---- | ------------------------------------------- | ---------------- | ------------------ |
| v3   | +Champion-Self-Play (Warm-Start v2)          | Gleich stark     | —                   |
| v4   | +2300 Champion-Self-Play (Warm-Start v2)     | Gleich stark     | —                   |
| v5   | +Champion-Self-Play (Warm-Start v2)          | 39:37, 51% (Gleich stark) | —          |
| v6   | +4000 Stufe-2-Bootstrapping-Spiele (v2, Warm-Start v2) | 35:37, 49% (Gleich stark) | 45:41, 52% (Gleich stark) |

Details je Generation in `v3_eval.md` bis `v6_eval.md`. **Wichtiger
Nebenbefund (Datenfenster-Kontrolle):** `train.py` lädt beim Training IMMER
alle `.pkl`-Dateien aus `data/` (`glob.glob(*.pkl)`, keine Filterung nach
Version/Herkunft) — es gibt keinen Mechanismus, der sicherstellt, dass nur
die in den "trainiert mit"-Listen dokumentierten Spiele tatsächlich einfließen.
v6 lud beim Training 1735 Dateien (~17.350 Spiele), deutlich mehr als die in
`v6_eval.md` dokumentierten ~13.400 — der `v2`-Self-Play-Anteil allein ist
über v3-v6 unbemerkt auf 1135 Dateien (~11.350 Spiele) angewachsen (statt der
dokumentierten 600/6000), vermutlich weil der Self-Play-Befehl mehrfach
nachgezogen wurde, ohne alte Dateien zu ersetzen. Diagnose-Daten aus der
Stufe-2-Ursachenforschung wurden zwischenzeitlich aus `data/` entfernt
(betraf v3-v6 nicht, da sie erst NACH v6 entstanden) — **vor dem v7-Training
muss der `data/`-Ordner bewusst kontrolliert werden** (siehe Masterplan
Schritt 1 unten), sonst trainiert v7 auf einem unkontrollierten Gemisch statt
dem beabsichtigten ausgedünnten Fenster.

Das ändert nichts an der Kernaussage: **die reine Fenstergröße ist als Hebel
jetzt empirisch ausgereizt** (vier Versuche, ein immer größeres/unklareres
Fenster, nie ein Erfolg) — Zeit für die nächsten Eskalationsstufen.

## Masterplan für die nächsten Generationen (ab v7)

Zwei parallele Spuren — Spur A treibt die eigentliche Spielstärke voran
(Prioritaet), Spur B ist die Stufe-2-Ursachenforschung (kein Blocker für A).

### Spur A: v7 — Champion v2 endlich herausfordern

Stufe 1 ("+2000 Spiele") ist nach vier Fehlversuchen (v3-v6) empirisch
ausgereizt (siehe oben) — **v7 kombiniert Stufe 2 (Ausdünnen) UND Stufe 3
(mehr Sims) direkt**, statt sie einzeln nacheinander zu probieren (spart
eine ganze Iteration, falls "nur ausdünnen" allein auch nicht gereicht
hätte):

1. **Fenster ausdünnen — konkret in `data/` (nicht nur konzeptionell):**
   `train.py` lädt beim Training ALLE `.pkl`-Dateien aus `data/` ohne
   Filterung (siehe Nebenbefund oben) — Ausdünnen heißt hier also: Dateien
   PHYSISCH aus `data/` entfernen (z.B. in einen Archiv-Ordner verschieben,
   nicht loeschen), nicht nur eine Zahl in der Doku anpassen.
   - Die anfängliche Heuristik-/`v1c`-Beimischung raus (`selfplay_s400_*`,
     `selfplay_v1c_*`, je ~100 Dateien).
   - Den `v2`-Selfplay-Berg (aktuell 1135 Dateien, ~11.350 Spiele) auf ein
     handhabbares Maß kürzen — z.B. die 600 neuesten (per Timestamp im
     Dateinamen) behalten, den Rest archivieren.
   - `selfplay_v2s2_*` (die 4000 Stufe-2-Bootstrapping-Spiele aus v6):
     behalten oder raus — offene Entscheidung, da v6 damit nicht gewonnen
     hat; default: raus, da Spur A jetzt bewusst bei Stufe 1 bleibt.
   - **Vor dem v7-Training außerdem prüfen**: keine Diagnose-Daten aus Spur B
     (`selfplay_v2s2det_*`) mehr in `data/`, sobald deren Auswertung
     abgeschlossen ist — sonst fließen sie unbeabsichtigt mit ein.
   - Direkt danach `ls data/*.pkl | wc -l` gegenchecken, BEVOR `train.py`
     läuft — die Anzahl muss zur beabsichtigten Fenstergröße passen.
2. **Neue Champion-Runde mit erhöhten Sims**: 2000 frische Self-Play-Spiele
   von `v2`, Stufe 1, **`--sims 800`** (statt 400) —
   `python self_play.py --mode network --model alphazero_v2.onnx --stage 1 --games 2000 --sims 800 --version v2`.
3. Zielfenster: ~8000-10.000 Spiele, jetzt mit höherem Anteil an
   800-Sims-Qualität statt immer mehr 400-Sims-Volumen.
4. Training: `python train.py --name v7 --epochs 100 --load v2` (wie
   bisher, Warm-Start vom Champion).
5. Gate: `run_net_vs_net(v7, v2, stage=1, games=100)` — SPRT-Entscheid.
6. **Trigger-Regel für danach** (damit nicht wieder 4x dasselbe Rezept ohne
   Kurskorrektur läuft):
   - **v7 gewinnt** (H1a): v7 wird neuer Champion, Zyklus geht normal weiter
     (v8 mit v7 als Basis, zurück zu Stufe 1 "+2000 Spiele" für die naechste
     Runde).
   - **v7 "Gleich stark"**: Sims nochmal erhöhen (1600) für v8 UND
     ernsthaft prüfen, ob v2 schlicht ein sehr stabiles lokales Optimum ist,
     das mit diesem Rezept (Warm-Start, gleiche Architektur) nicht mehr zu
     verbessern ist — dann Kurswechsel erwägen (z.B. Cold-Start statt
     Warm-Start für einen Kandidaten, oder größeres Netz).
   - **v7 verliert klar** (H1b, v2 gewinnt signifikant): würde bedeuten,
     mehr Sims UND Ausdünnen haben geschadet (z.B. zu aggressiv ausgedünnt,
     zu wenig Spiele) — dann Fenstergröße für v8 wieder anheben, aber Sims
     auf 800 belassen.

### Spur B: Stufe-2-Ursachenforschung — inhaltlich abgeschlossen

Deterministisches (`--deterministic --no-root-noise`) Stufe-2-Self-Play mit
`v2` (900 Spiele, `v2s2det`, siehe `evaluations/stage2_investigation.md`
Schritt 8/9) lieferte ein klares Ergebnis:

- [x] 0:0-Rate auf komplett rauschfreien Daten: **7.0%** — deckungsgleich
      mit den Arena-Ergebnissen (v6(Stufe2) vs. v2(Stufe2): 7.0%). Zweifach
      bestätigt (Arena + Argmax-Selfplay), kein Selfplay-Artefakt.
- [x] Value-Head-Vorhersagen über die Runden zeigen: der Value-Head erkennt
      0:0-bound Partien schon ab Runde 1, aber die Vorhersage eskaliert
      selbst im schlechtesten Fall nie ins klar Negative (bleibt bei
      0.04-0.11, während normale Partien auf 0.19→0.29 steigen) — bestätigt
      die "weiches/wenig trennscharfes Value-Signal"-Hypothese deutlich.
- [ ] NICHT umgesetzt (optional, nur bei Bedarf): direkter Vergleich der
      Value-Head-Vorhersagen an denselben Zuständen gegen die exakte
      Stufe-1-DFS-Solver-Bewertung — waere der naechste Verfeinerungsschritt,
      ist aber fuer die Priorisierungsentscheidung unten nicht mehr
      zwingend noetig, da die Kernursache bereits klar identifiziert ist.

**Entscheidung:** Stufe 1 bleibt der Produktions-Pfad. Eine gezielte
Investition in einen schärfer kalibrierten Stufe-2-Value-Head (größerer
`value_hidden`, mehr Sims nur für Stufe-2-Blattauswertung) ist eine
zurückgestellte Option, keine aktuelle Prioritaet — Spur A (Champion-
Spielstärke) hat Vorrang.

<details>
<summary>Historie: erster Reset-Zyklus (v1/v1b/v2/v2b, überholt)</summary>

| Netz  | Fenster                              | Warm-Start | vs. Vorgänger      | vs. Heuristik | Val-R² |
| ----- | ------------------------------------- | ---------- | ------------------- | ------------- | ------ |
| v1    | 6000 Heuristik (VALUE_WEIGHT=15)      | nein       | —                    | 16:84         | —      |
| v1b   | 6000 Heuristik (VALUE_WEIGHT=2.5)     | nein       | —                    | 10:90         | —      |
| v2    | 4000 Heuristik + 6000×v1              | nein       | **63:37 vs. v1** ✅  | 31:69         | 0.16   |
| v2b   | 4000 Heuristik + 6000×v1              | ja (v1)    | 58:42 vs. v1 (Gate ✗)| —             | 0.41   |

Kernbefunde (aus dieser überholten Runde, aber weiterhin lehrreich):
- v2 schlug v1 63:37 (reißt das 60:40-Gate) — trotz massivem
  Train/Val-Overfitting (Train-R²=0.90, Val-R²=0.16). Mehr Daten halfen der
  reinen Spielstärke, auch wenn der Value-Head sie kaum generalisiert hat.
- v2b (Warm-Start) generalisierte deutlich besser (Val-R²=0.41), spielte aber
  SCHWÄCHER (58:42 statt 63:37) — Val-R² sagt nur etwas über den Value-Head
  aus, der in Stufe 1 beim Spielen gar nicht befragt wird. Was für
  Stufe-1-Stärke zählt, ist der Policy-Head, und der schien unter Warm-Start
  eher an v1s eigene (noch unausgereifte) Präferenzen anzuknüpfen, statt
  unabhängig auf dem größeren Fenster neu zu lernen.
- Stufe 2 weiterhin nicht praxistauglich — v2b hatte mit der ALTEN
  0:0-Raten-Sonde ein grünes 1.45x-Verhältnis (bester Wert der damaligen
  Historie), verlor aber 2:98 in einer echten Stufe-1-vs-Stufe-2-Partie. Die
  alte Sonde maß nur "kollabiert nicht mehr in Nichtangriffs-Partien", nicht
  "gewinnt wirklich" — seitdem durch einen direkten Arena-Test ersetzt (siehe
  Werkzeuge unten).

</details>

**Abgeschlossen (aktueller Reset-Zyklus):** VALUE_WEIGHT-Sweep (15/8/4/2) auf frischem 11.000-Spiele-
Heuristik-Fenster, je Arena vs. Heuristik (200 Sims, Early-Stop):

| Variante | vs. Heuristik   | Value Val-R² (Peak→nach Freeze) |
| -------- | --------------- | -------------------------------- |
| v1w15    | 29% (6:15, n=21)| 0.27 → -0.87                     |
| v1w8     | 10% (1:9, n=10) | 0.28 → -0.46                     |
| v1w4     | 31% (9:20, n=29)| 0.30 → -0.06                     |
| v1w2     | 10% (1:9, n=10) | 0.35 → +0.07                     |

Jedes einzelne Ergebnis ist für sich statistisch abgesichert (Early-Stop
garantiert ≥95%-Konfidenz, dass Heuristik pro Match >50% Gewinnchance hat).
Die RANGFOLGE zwischen den vier Gewichten ist damit aber nicht automatisch
mitgesichert: Zweistichproben-z-Test v1w4 (9/29=31%) vs. v1w8 (1/10=10%)
ergibt z≈1.31 — unter der 95%-Schwelle (z≥1.96), also (noch) nicht
signifikant unterscheidbar trotz des deutlich wirkenden Punkteabstands.
v1w15 (6/21=29%) vs. v1w4 (9/29=31%) sind ohnehin praktisch identisch. Sweep
zeigt also verlässlich "alle vier Gewichte verlieren gegen Heuristik", aber
NICHT verlässlich, welches der vier Gewichte am besten ist — dafür bräuchte
es größere Stichproben pro Variante oder direkte Kandidat-vs-Kandidat-Arenen.
Wichtigster Nebenbefund: **in ALLEN vier Varianten kollabiert der (per
chirurgischem Freeze fixierte) Value-Head trotzdem** (siehe Tabelle) — der
Freeze schützt nur die Head-Gewichte selbst, nicht vor dem weiterhin
driftenden gemeinsamen Trunk, der nach dem Freeze noch dutzende Epochen rein
auf Policy trainiert. **Fix:** Zwei-Phasen-Training ersetzt den Freeze (siehe
Werkzeuge unten) — Sweep-Wiederholung mit dem neuen Mechanismus steht noch
aus, `VALUE_WEIGHT` in `config.py` bleibt bis dahin unentschieden.

**Abgeschlossen:** Confounder-Check zum Sweep-Befund "v1 (Weight 15) schlägt
v1b (Weight 2.5)": weil das Stop-Kriterium erst greift, wenn Policy UND Value
plateauen, trainiert ein hoher VALUE_WEIGHT-Lauf schlicht länger (Value
plateaut später als Policy) — der scheinbare Vorteil könnte reine
Trainingsdauer sein, nicht der Value-Gradient selbst. Test: zwei epochen-
gematchte Läufe auf demselben Fenster, je exakt 50 Epochen
(`--epochs 50 --no-early-stop`), `v1b_w15_e50` (VALUE_WEIGHT=15) vs.
`v1b_w0_e50` (VALUE_WEIGHT=0, reines Policy-Training) — Details in
`evaluations/v1b_w15_e50_eval.md` / `v1b_w0_e50_eval.md`.

Ergebnisse:
- **Stufe 1 (A vs. B, 100 Spiele, kein Early-Stop): exaktes 50:50.** Kein
  messbarer Vorteil von VALUE_WEIGHT=15 gegenüber 0 bei gleicher
  Trainingsdauer — der frühere Sweep-Befund war der Confounder, nicht der
  Value-Gradient.
- Selbst der Value-Head-Kalibrierungswert (Phase 2, gegen den jeweils fixen
  Trunk) ist fast identisch: 0.24 (w15) vs. 0.22 (w0) — der rein
  policy-trainierte Trunk liefert also fast gleich gute Repräsentationen für
  die Value-Vorhersage.
- **Stufe 2 (A vs. B, 100 Spiele, kein Early-Stop): 40:60 — w0 gewinnt sogar
  leicht** (z≈2.0, knapp signifikant), trotz des minimal schlechteren
  Kalibrierungswerts. VALUE_WEIGHT ist also auch für Stufe 2 kein Hebel; wenn
  überhaupt, ist "kein Value-Gradient in Phase 1" leicht im Vorteil. 0:0-Rate
  bei Stufe 2 mit 7% weiterhin auffällig höher als bei Stufe 1 (0%) — Stufe 2
  bleibt insgesamt die schwächere Spielweise, unabhängig vom Gewicht.

**Entscheidung:** `VALUE_WEIGHT` in `config.py` auf **1** gesetzt (statt dem
zufällig gewählten alten Standard 15) — der Sweep mit dem korrigierten
Zwei-Phasen-Training (der wegen eines Skript-Bugs nur mit 15 statt ~100
Epochen lief, siehe Git-Historie) wird NICHT wiederholt, da der Confounder-
Test die eigentliche Frage bereits klar beantwortet hat: das Gewicht ist für
Stufe 1 und Stufe 2 gleichermaßen irrelevant. Nächste Generationen laufen mit
diesem Wert.

## Werkzeug-Verbesserungen dieser Session

- **Val-Split** (`train.py --val-frac`, Standard 10%, Datei- nicht
  Zug-Ebene): deckt Overfitting auf, das Train-R² allein verdeckt hätte
  (siehe v2 oben). Pro Trainingslauf neu gezogen, kein generationsübergreifend
  fixer Val-Satz (das leistet die Arena vs. Champion/Heuristik).
- **Zwei-Phasen-Training** (ersetzt das frühere chirurgische Value-Head-
  Freeze, das den Val-R²-Kollaps im Sweep NICHT verhindert hat — der Trunk
  driftete nach dem Freeze unter dem fixen Head weiter weg): Phase 1
  trainiert Value+Policy bis zum bestehenden Policy+Value-Plateau komplett
  gemeinsam (voller `VALUE_WEIGHT`, kein Freeze mehr — der Trunk profitiert
  nachweislich vom Value-Signal, siehe v1 vs. v1b). Danach Phase 2:
  Trunk/Policy/Moon-Head einfrieren, Value-Head NEU initialisieren und
  ausschließlich gegen den jetzt fixen Trunk kalibrieren (bis zu 50 Epochen,
  `--val-patience`-Patience als Stop). Kann nicht mehr kollabieren, weil sich
  der Trunk während der Kalibrierung nicht mehr bewegt.
- **Policy-Val-Loss** (`train.py`, `val_ploss_history`): zusätzlich zum
  Value-Val-R² jetzt auch Policy-Verlust auf dem nie trainierten Val-Split
  gemessen (gleiche Masking/Gewichtung wie Training) — bislang nur ein
  Nice-to-have-Signal, die Arena bleibt der eigentliche Entscheider.
- **`value_hidden` 128→64**: die Value-Regression ist eigentlich einfach,
  weniger Kapazität dürfte dem Overfitting zusätzlich entgegenwirken.
- **Direkter Stufe-1-vs-Stufe-2-Arena-Test** (`train.py::run_readiness_probe`)
  ersetzt die alte 0:0-Raten-Sonde: dasselbe Netz tritt in einer echten Partie
  gegen sich selbst an (Stufe 1 vs. Stufe 2), max. 50 Spiele, mit Early-Stop.
- **Arena-Early-Stop → truncated SPRT** (`arena.py::sprt_bounds`/
  `sprt_llr_delta`, ersetzt die fruehere Bonferroni-korrigierte
  Wiederholungstest-Loesung): zwei parallele Wald-SPRTs pro Match — H1a
  "A signifikant staerker", H1b "B signifikant staerker", je p1=0.64
  (~+100 Elo), α=0.05, β=0.10. Bricht ab, sobald EINE Seite ihre H1
  annimmt (Sieger); "Gleich stark" gilt erst, wenn BEIDE H1 verwerfen oder
  das Ressourcenlimit (Standard 100 Spiele) erreicht ist. Ein einseitiger
  Test haette knapp-eindeutige Ergebnisse faelschlich als Paritaet gemeldet
  (siehe v1c-Log, Git-Historie) — der Dual-Test behebt das. Elo-Berechnung
  ist jetzt rein sieg-/niederlage-basiert (kein Siegstaerke-Multiplikator
  mehr), korreliert direkt mit der SPRT-Gewinnwahrscheinlichkeit.
- **`net_vs_net_arena_match`**: `dfs_leaf_a`/`dfs_leaf_b` getrennt wählbar
  (z.B. Stufe 1 vs. Stufe 2 in derselben Partie, nicht nur global pro Match).
- **Self-Play-Diagnose-Flags** (`self_play.py --no-root-noise`,
  `--deterministic`, siehe `evaluations/stage2_investigation.md`): erlauben
  rauschfreies (`--deterministic`, immer meistbesuchter Zug statt
  visit-proportionalem Sampling) bzw. teilrauschfreies (`--no-root-noise`)
  Self-Play mit vollen Zug-fuer-Zug-Trajektorien fuer Diagnosezwecke — NICHT
  fuer reguläre Trainingsdaten-Generierung (weniger Zustandsvielfalt).
- **`mcts.rs`/`net_mcts.rs`**: strukturell identische Teile (Force-Reply-
  Garantie, Nachlauf-Schließung, Tiefenberechnung) in `search_common.rs`
  zusammengefasst — die tatsächlich unterschiedlichen Algorithmen (UCB1+
  Widening vs. PUCT+Policy-Masse-Cutoff) bleiben bewusst getrennt.

## Champion/Kandidat-Protokoll

- **Gate:** ein Kandidat wird nur Champion, wenn er den bisherigen Champion in
  der SPRT-Arena (siehe Werkzeuge oben) signifikant schlägt (H1a angenommen,
  ~+100 Elo / 64% Gewinnwahrscheinlichkeit). "Gleich stark" (SPRT-Ausgang
  PARITY) heißt: Champion bleibt bestehen, Kandidat wird verworfen.
- **Self-Play kommt immer vom aktuellen Champion**, nie vom zuletzt trainierten
  Netz.
- **Fenster-Größe — Soll vs. Ist:** urspruenglich gedacht als max. 2 abgelöste
  Champions (je 1 Runde à 2000 Spiele = 4000) + aktueller Champion (6000) =
  **10.000 Spiele**. **Tatsächlich ist das Fenster über v3→v6 unbemerkt auf
  ~17.000 Spiele gewachsen** (v6 lud 1735 Dateien) — teils weil die billigste
  Eskalationsstufe ("+2000 Spiele") mehrfach gezogen wurde, teils weil
  `train.py` grundsätzlich ALLE `.pkl`-Dateien aus `data/` laedt
  (`glob.glob(*.pkl)`, keine Versions-Filterung) und der `v2`-Self-Play-Anteil
  dadurch unbemerkt auf 1135 Dateien (~11.350 Spiele statt der dokumentierten
  600/6000) angewachsen ist. **Konsequenz: "Fenster" ist aktuell gleichbedeutend
  mit "was gerade in `data/` liegt"** — vor JEDEM Training muss der Ordner
  bewusst kontrolliert werden, sonst driftet die tatsaechliche Trainingsmenge
  unbemerkt von der Dokumentation weg (wie hier geschehen). Ab v7 gilt zudem:
  **Eskalationsstufe 1 gilt als ausgereizt** (siehe Masterplan unten) — nicht
  mehr automatisch ziehen, stattdessen zu Stufe 2/3 wechseln.
- **Eskalationsstufen bei erfolglosem Kandidaten, ab jetzt in dieser
  Reihenfolge (Stufe 1 gilt als verbraucht):**
  1. ~~+2000 Spiele~~ — **4x versucht (v3-v6), 4x erfolglos. Nicht mehr
     wiederholen, bevor nicht Stufe 2 oder 3 probiert wurde.**
  2. **Fenster ausdünnen**: alte, vorreset-fremde Spiele (die anfängliche
     Heuristik-/v1c-Beimischung, die seit dem Reset in jedem Fenster
     mitgeschleppt wird) rauswerfen, nur noch aktuelle Champion-Qualität +
     eine begrenzte, frische Champion-Runde behalten. Ziel: zurück auf
     ~10.000-12.000 Spiele, aber mit höherem Anteil aktueller Qualität statt
     immer mehr Gesamtvolumen.
  3. **Sims für neue Champion-Runden erhöhen** (z. B. 800 statt 400) — ein
     echter Qualitätsgewinn (verbessert die Suche selbst), teuerste Stufe.

## Value-Target-Formel (`engine/py/neural_net.py`, `VALUE_SCHEMA_VERSION=9`)

```
own_total = step["scores"][eigener Spieler]   # inkl. Wertungsplatten
opp_total = step["scores"][Gegner]
value = tanh(own_total / 50) − 0.1 · tanh(opp_total / 50)
```

Ziel für JEDEN Schritt der Partie (delayed reward, wie in AlphaZero) — nicht
Win/Loss ±1, sondern das tatsächliche Punkte-Endergebnis. Getrennt gesättigte
Terme: der eigene Term ist unabhängig vom Gegner voll differenzierend
(Priorität 1 "maximale eigene Punktzahl"), der Gegner-Term ist separat
gesättigt und verschiebt den Gesamtwert nur um max. ±0.1 (Priorität 2 "wenn
möglich dem Gegner schaden", begrenzter Bonus, kann nie eine eigene Einbuße
aufwiegen).

`VALUE_WEIGHT` balanciert Value- gegen Policy-Loss — der ursprüngliche Sweep
(15/8/4/2) war durch den alten Freeze-Mechanismus verfälscht; der Confounder-
Test (siehe oben, epochengematcht mit Zwei-Phasen-Training) zeigt aber klar,
dass das Gewicht weder für Stufe 1 (50:50) noch für Stufe 2 (40:60, tendenziell
sogar zugunsten Weight=0) einen Unterschied macht. Final auf **1** gesetzt,
kein weiterer Sweep nötig.

## Bekannte Bugs (in früheren Zyklen gefunden und gefixt, Referenz)

- Self-Play-Timeout: fix (30s) auf reine Heuristik-Suche kalibriert, riss bei
  höheren Sims/netzgeführter Suche → jetzt dynamisch sims-skaliert
  (`heuristic_game_timeout_secs`/`net_game_timeout_secs` in `self_play.rs`).
- BatchNorm-Crash bei Batch-Größe 1 (Restbatch einer Epoche) → `drop_last=True`.
- Tiling-Solver-Kombinatorik-Explosion (`chip_allocations`) → Node-Budget +
  Bitmasken-Signatur statt String-Dedup.
- Wertungsplatten-Blindheit + Unplaceable-Row-Blindheit in der Blattbewertung
  (`solve_round_final_score` kannte weder Wertungsplatten-Fortschritt noch
  drohende Strafleisten-Buße) → `scoring::wertung_progress` +
  `round_end::projected_unplaceable_penalty`, beide in `player_total`
  eingerechnet. Bestätigt wirksam: Anteil "konfident falscher"
  Strafleisten-Entscheidungen der Heuristik 75.9%→15.1%.
- JSON-Umweg im Netz-Feature-Pfad (`state_to_json` statt direktem Struct-Zugriff)
  kostete ~34% der Suchzeit → `state_to_features_direct`, −35 bis −48%
  Gesamt-Suchzeit.
- Force-Reply griff nicht zuverlässig (nur bei erneutem PUCT/UCB-Besuch) →
  Nachlauf-Pass am Ende von `build_tree`/`build_net_tree`.

## Offene Punkte

- **v7 (Spur A des Masterplans) noch nicht gestartet** — Fenster ausdünnen +
  Sims auf 800 erhöhen, dann trainieren und gegen v2 testen.
- **Stufe-2-Ursachenforschung (Spur B) inhaltlich abgeschlossen** (siehe
  `evaluations/stage2_investigation.md`): 0:0-Rate ist ein Score-Klemm-
  Mechanik-Effekt; Stufe 2 hat real ~7% davon (rauschfrei, zweifach
  bestätigt über Arena UND Argmax-Selfplay) vs. 0% bei Stufe 1; Ursache ist
  das weichere/weniger trennscharfe Value-Signal (Value-Head erkennt
  0:0-bound Partien früh, eskaliert aber nie ins klar Negative). Stufe 1
  bleibt Produktions-Pfad, gezielte Stufe-2-Kalibrierung zurückgestellt.
- Learning Rate kann noch optimiert werden.
- Ob ein Policy-Prior-Bias wie beim alten v8 (konfidente Fehlentscheidungen
  "Strafleiste statt erreichbare Reihe") in der neuen Linie auftritt, ist
  noch nicht systematisch untersucht.
