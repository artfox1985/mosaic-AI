# Mosaic-AI AlphaZero-Loop — Status & Fahrplan

Historische Details (alte v1-v9-Zählung vor dem Reset, Bug-Diagnosen,
verworfene Ansätze) stehen in der Git-Historie dieser Datei und in den alten
`v*_eval.md`s — hier nur der aktuelle Stand und die aktiven Regeln.

## Aktueller Stand (nach zweitem, kompletten Fenster-Reset)

Der erste Reset (2026-07-07, v1/v1b/v2/v2b/v2c) ist selbst überholt — das
Datenfenster wurde seitdem komplett neu aufgesetzt (~11.000 frische
Heuristik-Spiele), Zählung beginnt wieder bei v1. **Aktuell existiert daher
noch KEIN v2** — VALUE_WEIGHT ist jetzt final auf **1** gesetzt (siehe
Confounder-Ergebnis unten: das Gewicht ist für Stufe 1 UND Stufe 2 irrelevant,
kein weiterer Sweep nötig), die nächsten Generationen (Self-Play mit dem
aktuellen Champion) folgen als nächster Schritt.

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
- **Arena-Early-Stop** (`arena.py::early_stop_wins_needed`): bricht ab,
  sobald eine Seite ab Spiel 10 mit 95%-Signifikanz (z=1.96,
  `ceil(0.5·(n+1.96·√n))` Siege) vorne liegt — spart Zeit bei eindeutigen
  Matchups, ohne bei knappen Ergebnissen zu früh abzubrechen.
- **`net_vs_net_arena_match`**: `dfs_leaf_a`/`dfs_leaf_b` getrennt wählbar
  (z.B. Stufe 1 vs. Stufe 2 in derselben Partie, nicht nur global pro Match).
- **`mcts.rs`/`net_mcts.rs`**: strukturell identische Teile (Force-Reply-
  Garantie, Nachlauf-Schließung, Tiefenberechnung) in `search_common.rs`
  zusammengefasst — die tatsächlich unterschiedlichen Algorithmen (UCB1+
  Widening vs. PUCT+Policy-Masse-Cutoff) bleiben bewusst getrennt.

## Champion/Kandidat-Protokoll

- **Gate:** ein Kandidat wird nur Champion, wenn er den bisherigen Champion mit
  **≥60:40** (z≈2.0, n=100) schlägt. Knappere Ergebnisse sind statistisch
  Rauschen — Champion bleibt bestehen und generiert weitere Self-Play-Runden.
- **Self-Play kommt immer vom aktuellen Champion**, nie vom zuletzt trainierten
  Netz.
- **Fenster-Größe:** max. 2 abgelöste Champions (je 1 repräsentative Runde à
  2000 Spiele = 4000) + aktueller Champion mit = 6000 Spielen.
  Macht standardmäßig **10.000 Spiele** gesamt.
- **Wenn ein Kandidat mit vollen 10.000 Spielen den Champion nicht
  schlägt**, drei Eskalationsstufen, günstigste zuerst:
  1. **+2000 Spiele** (billigste Stufe): das Fenster um 2000 weitere aktuelle
     Champion-Self-Plays auf 12.000 Spiele erweitern (kein Ausdünnen, reines
     Wachstum), mit dieser Zusammensetzung neu trainieren — nur ein
     zusätzlicher Self-Play-Lauf + ein Trainingslauf.
  2. **Erst wenn auch das nicht reicht: Fenster ausdünnen** — die Spiele der
     alten Champions reduzieren (z. B. auf 2000 oder weniger) und mit
     aktuellen Champion-Self-Plays auf die Zielgröße auffüllen, mit dieser
     Zusammensetzung neu trainieren.
  3. **Erst wenn auch das nicht reicht: Sims für neue Champion-Runden
     erhöhen** (z. B. 800 statt 400) — teuerste Stufe (mehrstündige
     Self-Play-Runde), aber ein echter Qualitätsgewinn: mehr Sims verbessert
     die Suche selbst, während Fenster-Anpassungen nur Stichprobenrauschen
     reduzieren bzw. das Mischverhältnis verschieben.

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

- Stage 2 weiterhin nicht praxistauglich — jetzt mit dem direkten Arena-Test
  (statt der alten Sonde) belastbarer messbar, aber noch keine Generation hat
  ihn bestanden.
- Learning Rate kann noch optimiert werden.
- Ob ein Policy-Prior-Bias wie beim alten v8 (konfidente Fehlentscheidungen
  "Strafleiste statt erreichbare Reihe") in der neuen Linie erneut auftritt,
  ist noch nicht untersucht — beobachten, sobald genug Generationen (v2, v3,
  ...) vorliegen.
