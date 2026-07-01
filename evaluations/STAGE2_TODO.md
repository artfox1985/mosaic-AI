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
- **Erster Stufe-2-Versuch (v7, `--stage 2`) ist kollabiert: 51.8 % 0:0-Spiele
  vs. 17.5 % mit demselben Netz + DFS-Blatt** (isolierender Diagnose-Lauf, kein
  Bug — v7s Value-Head ist als Endergebnis-Klassifikator brauchbar, Loss 0.057,
  aber noch nicht präzise genug als Blattbewertung mitten in der Suche). Siehe
  Abschnitt A — Umstieg jetzt über eine Reifegrad-Sonde statt zu raten.
- **Warm-Start bricht bei `INPUT_SIZE`-Änderungen**, wenn nicht abgefangen:
  `strict=False` toleriert fehlende/zusätzliche Keys, aber KEINE Shape-
  Mismatches bei gleichnamigen Keys (`body.0.weight`). `train.py` filtert
  solche Keys jetzt vorher raus — Rest (Bias, tiefere Schichten, alle Heads)
  bleibt warm-startbar. Bei jeder künftigen `INPUT_SIZE`-Änderung gilt das
  weiterhin (committet, mit State-Dict-Vergleich verifiziert).

## A) Stufe 2 — Netz-Value-Blatt (nächster Hauptschritt, jetzt mit Reifegrad-Sonde)

**Status:** v8 trainiert gerade (512, warm von v7, Daten v2+v3+4000×v4, PLUS die
Features aus Abschnitt B — Chip-Farben + Moon-Order, s.u.). Sobald v8 fertig ist
und das übliche Arena-Gate (vs. v7 + vs. Heuristik) besteht, gilt der folgende
Ablauf für den Stufe-2-Umstieg — **nicht mehr blind versuchen** (der v7-Versuch
kostete einen vollen Self-Play-Zyklus, bevor der Kollaps auffiel).

### Reifegrad-Sonde (nach jeder Stufe-1-Generation, die das Heuristik-Gate besteht)
Billiger, isolierender Vergleich mit **demselben Netz**, einmal Stufe 1 und
einmal Stufe 2 (~40 Spiele reichen — das war die Stichprobe, die v7s Kollaps zeigte):

```
python self_play.py --mode network --model alphazero_<gen>.onnx --stage 1 \
    --games 40 --sims 400 --version <gen>_probe_s1 --threads 0
python self_play.py --mode network --model alphazero_<gen>.onnx --stage 2 \
    --games 40 --sims 400 --version <gen>_probe_s2 --threads 0
# 0:0-Rate + Ø Sieger-Score je Lauf vergleichen; Probe-Daten danach löschen
# (kein Regen-Zyklus, reine Messung).
```

**Ampel** (Verhältnis 0:0(Stufe2) / 0:0(Stufe1) — normalisiert aufs jeweilige
Stufe-1-Grundrauschen der Generation):
- **≤ ~1.5×** → Value-Head trägt, voller Stufe-2-Zyklus lohnt sich.
- **1.5×–3×** → noch nicht reif, Trend über Generationen beobachten, Stufe 1
  weiter iterieren.
- **> 3×** (v7: 3.7×/2.96× — 51.8 % vs. 17.5 %) → klar nicht reif, keinen
  Stufe-2-Zyklus starten, Probe bei der nächsten Gen wiederholen.

### Bei Grün: voller Stufe-2-Zyklus
- Self-Play groß mit `--stage 2` (`dfs_leaf=False`), z. B. 1500–2000 Spiele.
  Mehrrunden-Weitblick statt der Ein-Runden-Myopie des DFS; Stage-2-Sims sind
  billiger (Netz-Forward statt Netz-Forward+DFS pro Sim).
- Training warm vom Reifegrad-Netz (`--load <gen> --hidden 512`).
- Erste Stufe-2-Generation: **Mix** aus Stufe-1-Restfenster (reduziert) + den
  neuen Stufe-2-Daten — verhindert, dass die DFS-myopischen Alt-Targets die
  neuen Mehrrunden-Targets zahlenmäßig erschlagen. Über folgende Gens den
  Stufe-1-Anteil schrittweise rausrollen.
- **Arena-Gating**: die neue Gen nur übernehmen, wenn sie den Vorgänger schlägt;
  sonst **zurück auf Stufe 1** für die nächste Generation — kein zweiter
  blinder Stufe-2-Versuch in Folge.

### Bei Gelb/Rot
Normale Stufe-1-Daten erzeugen (wie bisher), nächste Generation trainieren,
Sonde dort wiederholen. Iterieren, bis Grün.

## B) Feature-Upgrades (Repräsentation) — ✅ ERLEDIGT (in v8 eingeflossen)
Ursprünglich als „erst nach eingependelter Stufe 2" geplant, aber vorgezogen
und direkt gemeinsam mit v8 umgesetzt:
1. **Bonuschip-Farben pro Fabrik** — 5-dim Farbmaske je kleiner Fabrik, NUR wenn
   `chip_revealed=true` (sonst versteckte Information). `INPUT_SIZE` 664→684.
   Verifiziert: verdeckte Chips liefern Null-Maske trotz echter Farben im
   rohen JSON, aufgedeckte matchen exakt. (Commit `fddc221`)
2. **Moon-Order aktiv wählen, suche-getrieben (Geminis Ansatz)** — umgesetzt
   OHNE `NUM_ACTIONS` aufzublähen: 482-dim Head bleibt auf Farbe+Reihe
   beschränkt (maskierte Softmax über eindeutige IDs), Permutations-Priors
   kommen separat aus dem `moon_order_head` per **Plackett-Luce** (sequenzieller
   Softmax über die 5 rohen Farb-Scores), kombiniert beim Expandieren eines
   `SmallFactorySun`-Knotens: `P(Zug) = P(Basis) × P(Order)`. Lokal in
   `net_mcts.rs::build_untried_actions` (pur testbar, 4 neue Tests), `generate_valid_moves`
   unverändert (betrifft nur die Netz-Suche). `moon_order_head`-Loss von
   MSE-Rang-Regression auf Plackett-Luce-NLL umgestellt (`train.py`); dabei
   einen echten Bug gefunden+behoben (`sun_mask` prüfte nur Spalte „blau").
   End-to-end verifiziert: Self-Play erkundet aktiv mehrere Moon-Order-
   Varianten (bis zu 6/Gruppe). (Commits `c01c305`, `c27b951`)

Damit sind auch die Chip-/Moon-Order-Daten in v8 bereits die volle Baseline für
die Reifegrad-Sonde oben — kein separater Feature-Rollout mehr nötig.

## C) Daten/Fenster (Begleitthema)
- DFS-verankerte Daten → altes bleibt brauchbar, breites Fenster günstig.
- Ab ~Gen 5 die **älteste** Generation rausrollen; fürs 512er Richtung
  **3000–5000 Spiele** im Fenster (v7 lief auf ~790k Züge / ~5000 Spiele).

## Gating / Verifikation
- Je Generation: `run_net_arena(v_neu vs Heuristik, 200/200, 100)` +
  `run_net_vs_net(v_neu vs Vorgänger)`; übernehmen nur bei Sieg gegen den Vorgänger.
- Vor jedem vollen Stufe-2-Zyklus zusätzlich: **Reifegrad-Sonde** (Abschnitt A) —
  nur bei grüner Ampel den großen Self-Play+Training-Zyklus starten.
- Feature-Änderung: `len(state_to_tensor(sample)) == INPUT_SIZE`, Rust/Python-Parität
  bit-genau, `cargo test` grün, `MosaicDataset` baut fehlerfrei.
- 0:0-Indikator beobachten (~1 % Arena / ~14 % Self-Play, stabil); falls steigend →
  gezielter 0:0-Sonderfall (Draw=0), nicht die alte abgestufte Skala.

## Offene Baustelle
- Seltener Nicht-Terminierungs-Bug (~1/800 Partien, durch 30s-Timeout abgefangen,
  Root-Cause offen) — irgendwann sauber diagnostizieren.
