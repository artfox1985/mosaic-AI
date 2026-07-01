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
- **Arena-Gating**: v8 nur übernehmen, wenn es v7 schlägt; sonst in Stufe 1 bleiben.
  Erste Stufe-2-Generation eng beobachten (kann anfangs abfallen, da die Visit-
  Targets nun vom Netz-Value statt DFS kommen). Value-Head trägt (v7 Value-Loss 0.057).

## B) Feature-Upgrades (Repräsentation) — parallel/danach
Ändern `INPUT_SIZE` bzw. Spielzeit-Logik, nicht den Kern-Loop:
1. **Bonuschip-Farben pro Fabrik** in `state_to_tensor`
   ([engine/py/neural_net.py](../engine/py/neural_net.py)) **+ Rust-Parität**
   ([engine/src/features.rs](../engine/src/features.rs)), `INPUT_SIZE` anpassen.
   Beim *Nehmen* sieht das Netz aktuell nur `has_chip`+`chip_revealed`, nicht die
   Farben (1- vs. 2-Farb-Flexibilität). **Kein Regen nötig** — Farben stehen schon
   in den States (`serialize_chip`), pkl werden neu kodiert. `INPUT_SIZE`-Änderung →
   erste Body-Schicht frisch, tiefere warm-startbar (`strict=False`).
2. **Moon-Order aktiv wählen** (liegt brach): gespielt wird immer Default-`remaining`
   (`validation.rs:175`); `moon_order_head` wird zur Spielzeit verworfen
   (`net_mcts.rs` ignoriert `_moon`). Das Netz *sieht* die Order (state_to_tensor
   Sektion 7), *setzt* sie nicht. Pro Spiel nur **4×** → Rechenzeit lohnt. Billigster
   Fix: `self_play.rs::moon_order_target`-DFS-Logik zur Spielzeit die `moon_order`
   des gewählten Zuges setzen. Besseres Target würde den *Gegnerzugriff* mitbewerten.

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
