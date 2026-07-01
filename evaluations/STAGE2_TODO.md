# Roadmap ab v7 — Stufe 1 erreicht → Stufe 2 + Features

## Status (erreicht)

**Stufe 1 ist zufriedenstellend: v7 schlägt die Heuristik klar.**

| Netz | hidden | vs. Heuristik | Ø Score (Netz:Heur) |
|---|---|---|---|
| v4 | 256 | 51 % | 23.4 : 25.0 |
| v5 | 256 (warm v4) | 49 % | 23.8 : 28.4 |
| v6 | 512 (**cold**) | 45 % | 21.6 : 27.4 |
| **v7** | **512 (warm v6, ~790k Züge)** | **61 %** | **27.3 : 26.1** |

- v7 übertrifft die Heuristik **erstmals auch im Ø-Score** (27.3 > 26.1), Elo 1049:951,
  0:0 ~1 %. v7 ≈ v5 im Direktduell (Nicht-Transitivität, ok) — Benchmark ist die
  Heuristik, dort ist v7 klar vorn. **Weiter mit v7.**

## Learnings (validiert)
- **Größeres Netz hilft — aber nur WARM.** 256 gedeckelt (~49–51 %); 512 **cold**
  (v6) fiel ab (45 %); 512 **warm + mehr Daten** (v7) liefert den Sprung (61 %).
  Regel: großes Netz nie kalt starten; `--load` vom Vorgänger + mehr Daten.
  → Punkt „größeres Netz" damit **erledigt** (v7 ist das 512er).
- ±1-Value-Target, rohe Visit-Targets (N/ΣN), DFS-Blatt (Stufe 1), breites
  DFS-verankertes Fenster, v4/v7 als starke Daten-Generatoren.
- Hänger-Schutz: 30s-Wall-Clock je Partie in allen `play_*`-Schleifen (committet).

## A) Stufe 2 — Netz-Value-Blatt, warm von v7 (nächster Hauptschritt)
- Self-Play mit **`--stage 2`** (`dfs_leaf=False`, Netz-Value statt DFS am Blatt)
  → Mehrrunden-Weitblick, um die Ein-Runden-Myopie des DFS zu *übertreffen*.
  (Stage-2-Sims sind billiger: Netz-Forward statt Netz-Forward+DFS pro Sim.)
- Training **warm von v7**: `train.py --name v8 --load v7 --hidden 512` → gleiche
  Architektur, voller Gewichts-Transfer (Priors + Value bleiben).
- Erste Generation: Mix aus altem Stufe-1 (v3 + reduziertes v4) + neuem Stufe-2
  (v7-generiert) — verhindert, dass die DFS-myopischen Alt-Targets die neuen
  Mehrrunden-Targets zahlenmäßig erschlagen. Über folgende Gens Stufe-1-Anteil
  schrittweise rausrollen.
- **Arena-Gating**: v8 (und jede weitere Stufe-2-Gen) nur übernehmen, wenn sie den
  Vorgänger schlägt; sonst in Stufe 1 bleiben. Rückschlag in der ersten Gen ist
  normal (Visit-Targets kommen jetzt vom Netz-Value statt DFS).
- **Gate für Schritt B (Feature-Upgrades): erst wenn sich die Stufe-2-Generationen
  auf v7-Niveau eingependelt haben** (über mehrere Gens stabil ≥ v7 in der Arena,
  nicht nur ein einzelner guter Lauf). Verhindert, dass ein Abfall nicht zuordenbar
  ist (Netz-Value-Blatt vs. neue Features als Ursache).

## B) Feature-Upgrades (Repräsentation) — erst NACH eingependelter Stufe 2 (Gate oben)
Ändern `INPUT_SIZE` bzw. Spielzeit-Logik, nicht den Kern-Loop:
1. **Bonuschip-Farben pro Fabrik** in `state_to_tensor`
   ([engine/py/neural_net.py](../engine/py/neural_net.py)) **+ Rust-Parität**
   ([engine/src/features.rs](../engine/src/features.rs)), `INPUT_SIZE` anpassen.
   Beim *Nehmen* sieht das Netz aktuell nur `has_chip`+`chip_revealed`, nicht die
   Farben (1- vs. 2-Farb-Flexibilität). **Kein Regen nötig** — Farben stehen schon
   in den States (`serialize_chip`), pkl werden neu kodiert. `INPUT_SIZE`-Änderung →
   erste Body-Schicht frisch, tiefere warm-startbar (`strict=False`).
2. **Moon-Order aktiv wählen, suche-getrieben (Geminis Ansatz)** (liegt brach):
   gespielt wird immer Default-`remaining` (`validation.rs:175`); `moon_order_head`
   wird zur Spielzeit verworfen (`net_mcts.rs` ignoriert `_moon`). Das Netz *sieht*
   die Order (state_to_tensor Sektion 7), *setzt* sie nicht. Pro Spiel nur **4×**
   → volle MCTS-Behandlung lohnt sich; die Value-Backups (bei Stufe 2 implizit
   inkl. Mehrrunden-/Gegner-Effekte) sollen die Order-Wahl validieren, statt eine
   handgestrickte Heuristik zu raten.
   - **Zugerzeugung** (`validation.rs:175`, nur `TakeSource::SmallFactorySun`):
     statt einem Move mit `moon_order=remaining` alle Permutationen der Restfliesen
     als separate Moves erzeugen (≤ 3 Restfliesen → ≤ 6 Permutationen, wie in
     `moon_order_target` bereits gededupelt/begrenzt). Nur diese eine Quelle
     betroffen — `LargeFactorySun`/Mond-Pool sind ungeordnet, keine Änderung nötig.
   - **KRITISCH — Aktions-ID-Konflikt:** `action_to_id` kodiert `moon_order`
     **nicht** (Stone-ID hängt nur an `color/row/factory_index`,
     [engine/py/neural_net.py:248](../engine/py/neural_net.py),
     [engine/src/features.rs:354](../engine/src/features.rs)). Alle Permutationen
     desselben Base-Zugs fallen also auf dieselbe ID → der 482-dim Policy-Head kann
     ihnen keine unterschiedlichen Priors geben. **`NUM_ACTIONS` NICHT aufblähen**
     (würde alle bisherigen Checkpoints v1–v7 invalidieren). Stattdessen
     hierarchisch bleiben: der 482-dim Head bestimmt weiter nur Farbe+Reihe; die
     Permutations-Priors kommen **separat** aus dem `moon_order_head` und werden
     nur beim Expandieren eines `SmallFactorySun`-Knotens mit dem Base-Prior
     multipliziert (`P(Zug) = P(Base) × P(Order)`), in `net_mcts.rs::make_node`.
   - **Head-Redesign nötig:** `moon_order_head` liefert aktuell 5 MSE-Rang-Werte
     (kein Softmax, keine Verteilung). Für `P(Order)` braucht es eine echte
     Verteilung über Permutationen — z. B. **Plackett-Luce**: sequenzieller Softmax
     über die Restfarben (erst wahrscheinlichste Farbe oben wählen, dann aus dem
     Rest die nächste, usw.). Loss entsprechend von MSE auf Ranking-Likelihood
     umstellen; betrifft `MosaicNet.moon_order_head` + den Trainings-Loss in
     `train.py`. Trainings-Target: weiterhin `moon_order_target`
     (`self_play.rs`) als Referenz-Reihenfolge, aber als Permutations-Likelihood
     statt Rang-Regression codiert.
   - **Kosten:** bis zu 6× Branching, aber nur an den (≤4/Spiel)
     `SmallFactorySun`-Entscheidungen — **akzeptiert**, da so selten (durch
     Progressive Widening zusätzlich gedämpft). Sauber testen (cargo test:
     Aktionszahl an SmallFactorySun-Knoten, Prior-Summe=1 nach
     Kombination) und per Arena-Gating wie jede andere Generation validieren.

## C) Daten/Fenster (Begleitthema)
- DFS-verankerte Daten → altes bleibt brauchbar, breites Fenster günstig.
- Ab ~Gen 5 die **älteste** Generation rausrollen; fürs 512er Richtung
  **3000–5000 Spiele** im Fenster (v7 lief auf ~790k Züge / ~5000 Spiele).

## Gating / Verifikation
- Je Generation: `run_net_arena(v_neu vs Heuristik, 200/200, 100)` +
  `run_net_vs_net(v_neu vs Vorgänger)`; übernehmen nur bei Sieg gegen den Vorgänger.
- Feature-Änderung: `len(state_to_tensor(sample)) == INPUT_SIZE`, Rust/Python-Parität
  bit-genau, `cargo test` grün, `MosaicDataset` baut fehlerfrei.
- 0:0-Indikator beobachten (~1 % Arena / ~14 % Self-Play, stabil); falls steigend →
  gezielter 0:0-Sonderfall (Draw=0), nicht die alte abgestufte Skala.

## Offene Baustelle
- Seltener Nicht-Terminierungs-Bug (~1/800 Partien, durch 30s-Timeout abgefangen,
  Root-Cause offen) — irgendwann sauber diagnostizieren.
