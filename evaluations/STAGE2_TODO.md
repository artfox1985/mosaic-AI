# Mosaic-AI AlphaZero-Loop — Status & Fahrplan

Historische Details (alte v1-v9-Zählung vor dem Reset, Bug-Diagnosen,
verworfene Ansätze) stehen in der Git-Historie dieser Datei und in den alten
`v*_eval.md`s — hier nur der aktuelle Stand und die aktiven Regeln.

## Aktueller Stand (nach vollem Reset 2026-07-07)

Die alte v1→v9-Linie (Tabelle mit Champion-Verlauf, v8-Policy-Bias-Analyse
etc.) wurde verworfen — neue Basis ist reine, mit den Suche-Fixes dieses
Zyklus generierte Heuristik-Self-Play statt Fortsetzung der alten Kette.
Zählung beginnt bei v1 neu.

| Netz  | Fenster                              | Warm-Start | vs. Vorgänger      | vs. Heuristik | Val-R² |
| ----- | ------------------------------------- | ---------- | ------------------- | ------------- | ------ |
| v1    | 6000 Heuristik (VALUE_WEIGHT=15)      | nein       | —                    | 16:84         | —      |
| v1b   | 6000 Heuristik (VALUE_WEIGHT=2.5)     | nein       | —                    | 10:90         | —      |
| v2    | 4000 Heuristik + 6000×v1              | nein       | **63:37 vs. v1** ✅  | 31:69         | 0.16   |
| v2b   | 4000 Heuristik + 6000×v1              | ja (v1)    | 58:42 vs. v1 (Gate ✗)| —             | 0.41   |

Kernbefunde:
- **v2 schlägt v1 63:37** (reißt das 60:40-Gate) — trotz massivem
  Train/Val-Overfitting (Train-R²=0.90, Val-R²=0.16). Mehr Daten halfen der
  reinen Spielstärke, auch wenn der Value-Head sie kaum generalisiert hat.
- **v2b (Warm-Start) generalisiert deutlich besser** (Val-R²=0.41), spielt
  aber SCHWÄCHER (58:42 statt 63:37) — Val-R² sagt nur etwas über den
  Value-Head aus, der in Stufe 1 beim Spielen gar nicht befragt wird. Was für
  Stufe-1-Stärke zählt, ist der Policy-Head, und der scheint unter
  Warm-Start eher an v1s eigene (noch unausgereifte) Präferenzen anzuknüpfen,
  statt unabhängig auf dem größeren Fenster neu zu lernen.
- **Stufe 2 weiterhin nicht praxistauglich** — v2b hatte mit der ALTEN
  0:0-Raten-Sonde ein grünes 1.45x-Verhältnis (bester Wert der Historie),
  verlor aber **2:98** in einer echten Stufe-1-vs-Stufe-2-Partie. Die alte
  Sonde maß nur "kollabiert nicht mehr in Nichtangriffs-Partien", nicht
  "gewinnt wirklich" — seitdem durch einen direkten Arena-Test ersetzt (siehe
  Werkzeuge unten).

**Laufend:** kompletter Reset des Datenfensters — v1 wird mit ~11.000
frischen Heuristik-Spielen neu von null trainiert, diesmal als
**systematischer VALUE_WEIGHT-Sweep (15/8/4/2)**: `v1w15`, `v1w8`, `v1w4`,
`v1w2`, jeweils Arena vs. Heuristik. Grund: der bisherige Wert 15 war
zufällig gewählt, keine echte Herleitung — der einzige Datenpunkt-Vergleich
(15 vs. 2.5) zeigte 15 im Vorteil, das reicht nicht für eine fundierte Wahl.

## Werkzeug-Verbesserungen dieser Session

- **Val-Split** (`train.py --val-frac`, Standard 10%, Datei- nicht
  Zug-Ebene): deckt Overfitting auf, das Train-R² allein verdeckt hätte
  (siehe v2 oben). Pro Trainingslauf neu gezogen, kein generationsübergreifend
  fixer Val-Satz (das leistet die Arena vs. Champion/Heuristik).
- **Chirurgisches Value-Head-Freeze**: sobald Val-R² `--val-patience`
  (Standard 8) Epochen nicht mehr verbessert, wird NUR der Value-Head auf
  seinen besten Val-Stand zurückgesetzt und eingefroren
  (`requires_grad=False` + Loss-Anteil 0) — Trunk/Policy trainieren
  unbeeinflusst weiter, kein verschenktes Policy-Potential.
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

`VALUE_WEIGHT` balanciert Value- gegen Policy-Loss — **aktuell im Sweep**
(siehe oben), nicht mehr fix auf 15 gesetzt.

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

- VALUE_WEIGHT-Sweep (v1w15/v1w8/v1w4/v1w2) noch nicht abgeschlossen.
- Stage 2 weiterhin nicht praxistauglich — jetzt mit dem direkten Arena-Test
  (statt der alten Sonde) belastbarer messbar, aber noch keine Generation hat
  ihn bestanden.
- Learning Rate kann noch optimiert werden.
- Ob ein Policy-Prior-Bias wie beim alten v8 (konfidente Fehlentscheidungen
  "Strafleiste statt erreichbare Reihe") in der neuen Linie erneut auftritt,
  ist noch nicht untersucht — beobachten, sobald genug Generationen (v2, v3,
  ...) vorliegen.
