# Mosaic-AI AlphaZero-Loop — Status & Fahrplan

Historische Details (alte Zählung vor dem Neustart, Bug-Diagnosen, verworfene
Ansätze) stehen in der Git-Historie dieser Datei und in den `v*_eval.md`s —
hier nur der aktuelle Stand und die aktiven Regeln.

## Aktueller Stand

**Champion: weiterhin v8.** v9 (2000×v1c+2000×v4d+6000×v8, erste Runde mit den
unten dokumentierten Such-/Value-Target-Fixes live) hat das Gate NICHT
genommen — 55:45 gegen v8 (z≈1.0, unter der 60:40-Schwelle), siehe
`v9_eval.md`. Nächster Schritt laut Eskalationsstufe 1 (Fenster ausdünnen):
mehr v8-Self-Play generieren, altes Fenster ausdünnen, `v10` trainieren.

| Netz   | Fenster                                | Champion?            | vs. Heuristik | Ø Score (Netz:Heur) | vs. Champion      | Ø Score   |
| ------ | --------------------------------------- | -------------------- | ------------- | ------------------- | ----------------- | --------- |
| v1     | 3000 Bootstrap-Spiele (cold)            | ja (einzige Option)  | 43 %          | 19.5:25.4           | —                 | —         |
| v2     | Bootstrap+2000×v1                       | nein — v1 bleibt     | 44 %          | 19.6:28.4           | 50:50 (z=0.0)     | 20.5:17.6 |
| v3     | Bootstrap+2000×v1+2000×v1b              | nein — v1 bleibt     | 47 %          | 25.6:29.9           | 53:47 (z=0.6)     | 22.1:19.6 |
| **v4** | v1+v1b+v1c (6000, kein Bootstrap)       | **✅ neuer Champion** | 48 %          | 22.3:25.5           | **65:35 (z=3.0)** | 19.7:15.2 |
| v5     | v1b+v1c+v4 (gleitend)                    | nein — v4 bleibt     | 47 %          | 22.9:25.7           | 45:55 (z=-1.0)    | 20.0:24.0 |
| v6b    | v1b+v1c+v4+v4b (8000)                    | nein — v4 bleibt     | 58 %          | 27.0:26.6           | 53:47 (z=0.6)     | 21.6:21.7 |
| v7     | v1b+v1c+v4+v4b+v4c (10000, voll)         | nein — v4 bleibt     | 59 %          | 27.2:25.5           | 43:57 (z=-1.4)     | 21.2:21.2 |
| **v8** | v1c+v4+v4b+v4c+v4d (10000, ausgedünnt)  | **✅ neuer Champion** | 55 %          | 25.7:26.6           | **60:40 (z=2.0)** | 26.8:22.4 |
| v9     | v1c+v4d+v8 (10000, Such-/Value-Fixes)   | nein — v8 bleibt     | 15 %¹         | 26.9:46.3¹          | 55:45 (z=1.0)     | 30.8:26.4 |

Trend: durchgehender Fortschritt v1→v4 (mehr Daten half sichtbar auf jeder
Achse), v5/v6b/v7 Ausreißer ohne Gate-Erfolg gegen v4 (vom Protokoll erwartet,
kein Alarmsignal) — v8 (erstes Fenster mit Ausdünnung statt reinem Wachstum,
plus 2-lagiger Policy-Head + höheres `VALUE_WEIGHT=15`) durchbricht die Serie.
v8 vs. v1 zum Vergleich: 68:32 (z≈3.6), deutlich über v4s 65:35 gegen v1.

¹ **"vs. Heuristik" ab v9 nicht mehr mit v1-v8 vergleichbar:** die Heuristik
nutzt die Blattbewertung direkt (kein Prior dazwischen) und profitiert daher
SOFORT von den Such-Fixes dieses Zyklus — "Heuristik(s200)" ist ab v9 ein
spürbar stärkerer Gegner als in den früheren Zeilen dieser Tabelle, kein
v9-Rückschritt (siehe `v9_eval.md`).

**Stage 2 (Netz-Value als Suchblatt): weiterhin 🔴 ROT** bei allen Generationen
(Ratio 3.4×–5.1×, siehe Reifegrad-Sonde unten). Bleibt in Stufe 1 (DFS-Blatt).

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
  1. **Fenster ausdünnen** (billigste Stufe): die
     4000 Spiele der alten Champions reduzieren (z. B. auf 2000 oder weniger) und mit aktuellen Champion Self Plays auf 10000 Spiele auffüllen
     und mit dieser Zusammensetzung neu trainieren — nur ein Trainingslauf.
  2. **Erst wenn auch das nicht reicht: Sims für neue Champion-Runden
     erhöhen** (z. B. 800 statt 400) —
     teuerste Stufe (mehrstündige Self-Play-Runde), aber ein echter
     Qualitätsgewinn: mehr Sims verbessert die Suche selbst (schärfere,
     genauere Zielverteilung), während Stufe 1/2 nur Stichprobenrauschen
     reduzieren bzw. das Mischverhältnis verschieben, ohne die Qualitätsdecke
     der Suche selbst anzuheben.

## Value-Target (aktuelle Formel, `engine/py/neural_net.py`, `VALUE_SCHEMA_VERSION=9`)

```
own_total = step["scores"][eigener Spieler]   # inkl. Wertungsplatten
opp_total = step["scores"][Gegner]
value = tanh(own_total / 50) − 0.1 · tanh(opp_total / 50)
```

Ziel für JEDEN Schritt der Partie (delayed reward, wie in AlphaZero) — nicht
Win/Loss ±1, sondern das tatsächliche Punkte-Endergebnis. **Geändert von der
alten Differenz-Formel** `tanh((own − 0.5·opp)/50)`: die sättigte bei großem
Punkteabstand für BEIDE Terme gemeinsam (dasselbe Problem, das
`mcts.rs::evaluate()` schon durch rein absolute Pro-Spieler-Bewertung behoben
hat) — das Netz verlor dann jede Fähigkeit, zwischen "gut" und "noch besser"
zu unterscheiden. Jetzt getrennt gesättigt: der eigene Term ist unabhängig
vom Gegner voll differenzierend (Priorität 1 "maximale eigene Punktzahl"),
der Gegner-Term ist separat gesättigt und verschiebt den Gesamtwert nur um
max. ±0.1 (Priorität 2 "wenn möglich dem Gegner schaden", als begrenzter
Bonus, der nie eine eigene Einbuße aufwiegen kann). Skala 50 ist an einem
groben menschlichen Referenzwert kalibriert (~100 Punkte = sehr gut), nicht
an aktuellen (noch schwachen) Spieldaten.

`VALUE_WEIGHT = 15` (config.py) balanciert Value- gegen Policy-Loss — nötig,
weil das neue Target eine ~4.6× kleinere Streuung hat als das alte ±1-Ziel.

## Stage-2-Reifegrad-Sonde

Läuft automatisch nach jedem `train.py`-Lauf (100 Spiele je Stufe, 400 Sims):
vergleicht die 0:0-Rate desselben Netzes mit DFS-Blatt (Stufe 1) vs.
Netz-Value-Blatt (Stufe 2).

Ampel (Verhältnis 0:0(Stufe2)/0:0(Stufe1), Laplace-geglättet):

- ≤1.5× → 🟢 Value-Head trägt, voller Stufe-2-Zyklus lohnt sich
- 1.5–3× → 🟡 noch nicht reif
- \>3× → 🔴 klar noch nicht reif, in Stufe 1 bleiben

Bei Grün: Self-Play mit `--stage 2`, warm vom Reifegrad-Netz, Mix aus
Stufe-1-Restfenster + neuen Stufe-2-Daten, Arena-Gate wie gewohnt (Champion-
Protokoll gilt genauso für Stufe 2).

## Bekannte Bugs (in diesem Zyklus gefunden und gefixt)

- **Self-Play-Timeout zu knapp für netzgeführte Suche** (30s war auf reine
  Heuristik-Suche kalibriert) → separate Timeouts, `NET_GAME_TIMEOUT_SECS=180`.
- **BatchNorm-Crash bei Batch-Größe 1** (Restbatch einer Epoche zufällig Größe
  1) → `drop_last=True`.
- **Tiling-Solver-Kombinatorik-Explosion**: `chip_allocations` kann pro Aufruf
  bis zu 2^14 Teilmengen prüfen, wird rekursiv sehr oft aufgerufen → Node-Budget
  eingeführt (200.000 zu hoch, auf 2.000 korrigiert) + Performance-Fix
  (Bitmasken-Signatur statt String-Dedup).
- **Speicher-Nadelöhr beim Datensatz-Laden**: Zwischen-Listen wurden nicht
  freigegeben, bevor der HDF5-Cache geschrieben wurde → `del` direkt nach
  Konvertierung.
- **Completion-Check**: `self_play.py` prüft jetzt automatisch je `.pkl`-Datei,
  ob alle Partien wirklich Runde 5 erreicht haben (`completed`-Feld aus Rust),
  warnt sichtbar bei Abbrüchen.

Wahrscheinlich betraf der Timeout-Bug auch die GESAMTE alte Zählung vor dem
Neustart (v4-v11) — nicht mehr rekonstruierbar, da die Daten gelöscht sind.

### Neuer Zyklus (v8→v9, Suche + Value-Target)

- **Wertungsplatten-Blindheit**: die Blattbewertung (`solve_round_final_score`,
  von Heuristik-MCTS UND net_mcts' Stage-1-DFS-Blatt geteilt) kannte
  `state.scoring_tile_ids` gar nicht — konkret beobachtet: KI nahm −15 Pkt
  Spezialfelder-Strafe, die während der ganzen Partie unsichtbar war. Fix:
  `scoring::wertung_progress` (stetiger Ersatz für `calculate_end_scoring`,
  quadratische Teil-Belohnung statt hartem 0 vor Fertigstellung).
- **Unplaceable-Row-Blindheit** (gleicher Fehler-Typ): eine volle Musterreihe,
  deren Dome-Reihe keinen offenen passenden Space mehr hat, wird automatisch
  auf die Strafleiste verschoben (`process_unplaceable_rows`) — der DFS-Solver
  sah dafür 0 Punkte, zog aber nie die resultierende Strafe ab. Fix:
  `round_end::projected_unplaceable_penalty`, ebenfalls in `player_total`
  eingerechnet. Beide Fixes bestätigt wirksam per Heuristik-Vergleich (Anteil
  "konfident falsche" Strafleisten-Entscheidungen 75.9%→15.1%), zeigen sich
  aber NICHT in v8s eigenem Self-Play (siehe unten, Prior-Problem).
- **JSON-Umweg im Netz-Feature-Pfad**: `net_mcts.rs::make_node` ging über
  `state_to_json` (volle JSON-Serialisierung), obwohl alle 684 Features
  bereits als typisierte Struct-Felder vorlagen — kostete ~34% der Suchzeit,
  fast so viel wie der Netz-Forward-Pass selbst. Fix: `state_to_features_direct`
  liest direkt aus `GameState`, byte-identisch (3 Paritätstests). Effekt:
  Gesamt-Suchzeit −35 bis −48% bei gleichem Sim-Budget.
- **Force-Reply griff nicht zuverlässig**: die Garantie "Wurzelkandidat bekommt
  mind. eine Antwort, bevor gebreitert wird" (Tiefe 0/1) griff nur, wenn PUCT/UCB
  den Knoten je wieder besuchte — Kandidaten mit sehr niedrigem Prior blieben
  sonst dauerhaft unbeantwortet. Fix: Nachlauf-Pass am Ende von
  `build_tree`/`build_net_tree`, schließt offene Enden auch über das
  Sim-Budget hinaus (nur Tiefe 0/1, tiefer gemessen zu teuer: +50-100%
  Sim-Overhead je zusätzlicher Ankerebene).
- **Value-Target-Sättigung**: siehe Abschnitt oben.

### v8-Policy-Prior scheint einen strukturellen Bias zu haben (ungelöst)

Empirisch nachgewiesen (Kategorie-2-Diagnose in `utils/diagnosis.py`, siehe
`run_penalty_bias`): v8 wählt in bestimmten Situationen ("Strafleiste statt
eine erreichbare, punktende Reihe vervollständigen") konfident die
schlechtere Option — und zwar **unabhängig davon**, ob die Blattbewertung
korrekt ist:

- v8-Self-Play OHNE die obigen Fixes vs. MIT Fixes: identische Kategorie-2-Statistik
  (0.63% vs. 0.67% der Schritte, 87-89% "Alternative war noch offen", ~21-23%
  "konfident falsch") — der Fix ändert an v8s EIGENEM Verhalten nichts messbar.
- 4× mehr Sims: keine Verbesserung. Root-Noise aus: keine Verbesserung (eher
  leicht schlechter). `c_puct` 1.5→2.5: Kategorie-2-Konfidenz sinkt
  (22.7%→16.5%, an 500 Spielen bestätigt), aber **Gesamtstärke sinkt klar**
  (Arena v8@1.5 vs. v8@2.5: 62:38, Elo 1057:943) — kein Nettogewinn.
- Cutoff-Ausschluss (`POLICY_MASS_CUTOFF=0.95`) als Ursache ausgeschlossen
  (0% betroffene Fälle, `run_policy_cutoff_exclusion`).

**Diagnose:** v8s Policy-Prior wurde mit der ALTEN, fehlerhaften Blattbewertung
trainiert (geerbt über die ganze v1→v4→v8-Linie) und lenkt PUCT strukturell zu
selten in diese Situationen — die Suche kann einen schlechten Prior mit mehr
Explorationsdruck kaschieren (c_puct), aber nicht korrigieren, ohne insgesamt
zu verlieren. Braucht mehrere Trainingsgenerationen mit den jetzt korrekten
Zielen (v9, v10, ...), keine Suchparameter-Anpassung.

## Offene Punkte

- Stage 2 weiterhin rot — keine Prognose, wann sich das ändert.
- Learning Rate kann noch optimiert werden
- v8-Policy-Prior-Bias (siehe oben) — beobachten, ob sich die Kategorie-2-Quote
  über v9/v10/... graduell verbessert, jetzt wo die Blattbewertung stimmt.
- **Für später (nur falls v4 nach v8 Champion bleibt):** testweise ein `v4b`
  (Name kollidiert mit der bestehenden Self-Play-Runde `v4b` — bei Umsetzung
  neu benennen) mit dem neuen 2-lagigen Policy-Head trainieren, aber auf den
  ALTEN, frühen Trainingsdaten (`v1+v1b+v1c`) statt dem aktuellen Fenster.
  Gegen `v1` in der Arena testen — schlägt es weiterhin `v1`, daraus einen
  Herausforderer mit vollständigem Warm-Start (kompletter aktueller
  Datenstand) generieren.
