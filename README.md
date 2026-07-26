# 🧩 Mosaic-AI: Tile-Drafting AlphaZero Environment

[![Rust](https://img.shields.io/badge/engine-Rust-orange.svg)](https://www.rust-lang.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-Deep%20Learning-ee4c2c.svg)](https://pytorch.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Mosaic-AI** ist ein komplettes Reinforcement-Learning-Framework für das
Training AlphaZero-artiger neuronaler Netze auf einem zweispieligen
Tile-Drafting- und Kuppel-Bau-Brettspiel mit versteckter Information.

> **⚠️ Disclaimer:** Dieses Projekt ist ein Lern-/Forschungsprojekt zu einer
> generischen Tile-Drafting-/Wall-Tiling-Spielmechanik. Es wurde from scratch
> gebaut und steht in keiner Verbindung zu bestehenden kommerziellen
> Brettspielen, Verlagen oder Marken.

---

## Aktueller Stand

Referenz-/Champion-Netz: **`v16_best`**, Elo **≈1094** (95%-KI [1033, 1164]),
verankert bei Heuristik@150(dyn. ~330 Sims) = 1000 (`tools/elo_tracker.py
report`). Am 2026-07-24 gingen durch einen Worktree-Vorfall alle Modell-
Checkpoints bis einschließlich des damaligen Champions verloren (Code und
`data/`/`evaluations/` waren nicht betroffen); `v16_best` ist das Ergebnis
der seitdem laufenden Wiederaufbau-Linie (`v14` → `v14b` → `v15` → `v16`) und
hat den alten Champion-Elo-Wert bereits übertroffen. Volle Historie,
Messwerte und laufende Untersuchungen: [`evaluations/STATUS.md`](evaluations/STATUS.md).

---

## Engine-Kern in Kürze

- **Rust-Suche** (`engine/src/net_mcts.rs`): Gumbel-AlphaZero (Gumbel-Top-m,
  `GUMBEL_TOP_M=16`, + Sequential Halving an der Wurzel), deterministisch in
  Arena/Server, Gumbel-Exploration im Self-Play. Legacy-PUCT-Pfad bleibt
  hinter `USE_GUMBEL_SEARCH` als Toggle erhalten.
- **Value-Ziel**: `VALUE_SCHEMA_VERSION=15` (`engine/py/neural_net.py`) —
  weiches symmetrisches Margin-Ziel, per Default OHNE
  `round_transition_value` (rtv). rtv ist teuer (~81 % der Self-Play-Kosten)
  und trug in der Ablation keine messbare Spielstärke bei; steuerbar über
  `self_play.py --rtv` (`record_rtv`, Standard AUS).
  `bootstrap_value` (TD-Bootstrap, `TD_LAMBDA=0.5`) bleibt in jedem Fall aktiv.
- **Floor-Shaping** (`FLOOR_SHAPING_WEIGHT=0.3`): validiertes, exaktes
  Blattwert-Additiv gegen Bodenstrafen-Spiralen (n=100, kein Early-Stop).
  Plattenshaping/Value-Shrinkage wurden dagegen im A/B **widerlegt** und
  bleiben deaktiviert — Details/Zahlen in `STATUS.md`.
- **Runde 5**: exakte Alpha-Beta-Suche (`engine/src/round5.rs`), kein
  Netz-Entscheid mehr, sobald keine verdeckte Information mehr im Spiel ist.

---

## Der Generations-Zyklus (Trainingspipeline)

Kernstück des Projekts — so entsteht aus dem amtierenden Champion die
nächste Kandidaten-Generation:

1. **Self-Play-Batch** (Generator = amtierender Champion):
   ```bash
   python -u self_play.py --mode network --games 6000 --sims 400 \
       --version <generator> --model <generator>_best --threads 11
   ```
   ~7–8 h bei ~0,22 Spielen/s. Pro-Spiel-Flush (ein Absturz kostet ≤1 Spiel),
   Heartbeat-Überwachung, JSON-Run-Manifest.
2. **Replay-Fenster**: 6000 frische Spiele + 2000 eine Generation zurück +
   1000 zwei Generationen zurück, auf Datei-Ebene zusammengestellt — der Rest
   wandert nach `data/archive_*/` (alte Korpora werden nie wieder gemischt).
3. **Training**:
   ```bash
   python -u train.py --name vN --load vN-1_best --lr 0.00005 \
       --lr-schedule cosine --epochs 100 --value-target-variant nortv
   ```
   From-Scratch-Läufe (kein `--load`) nutzen die Default-LR. Nach jedem
   Trainingslauf schreibt ein `train.py`-Hook automatisch einen
   Modell-Snapshot ins OneDrive-Backup.
4. **Diagnose**: `tools/offline_diagnose.py --frozen` (einziger
   generationsübergreifend vergleichbarer Maßstab, fixes Eval-Set) +
   `tools/oracle_metrics.py` (Zusatzsignal gegen eine Tiefensuche-Referenz,
   **kein** Ersatz für eine echte Arena-Messung).
5. **Gating**: `tools/paired_gating.py` (gepaarte Seed-Blöcke, getauschte
   Bretter, Bernoulli-SPRT mit `H1: p1=0.65`) — nur ein `ACCEPT_H1` macht den
   Kandidaten zur neuen Referenz/zum neuen Generator.
6. **Elo**: `tools/elo_tracker.py` (Bradley-Terry über den vollen
   Match-Graphen) + Anker-Match des neuen Champions via `tools/arena.py`.
7. **Trends**: jeder Arena-/Gating-Lauf hängt eine Zeile an
   `evaluations/arena_trends.csv` (Ø-Punkte, Floor-Strafen über die Zeit —
   ergänzt Elo/Winrate um ein Qualitätssignal jenseits von "stärker/schwächer").

---

## Verzeichnis-Konvention

Root führt aus, `tools/` misst, `evaluations/` dokumentiert, `engine/`
rechnet, `docs/` erklärt, `static/` spielt.

```text
📦 mosaic-AI/
├── 📂 engine/       # Rust-Crate (mosaic_rust) — Spiel/Suche/Self-Play, PyO3-Bindings
│   └── 📂 py/       # neural_net.py (MosaicNet, MosaicDataset, Value-Ziel)
├── 📂 evaluations/  # STATUS.md, elo_history.csv, arena_trends.csv, Eval-JSONs/-Reports
├── 📂 data/         # Self-Play-Output (.pkl) + Run-Manifeste, data/archive_*/ = retired
├── 📂 models/       # Checkpoints (.pth/.onnx), Loss-Plots, Trainings-Manifeste
├── 📂 static/       # Web-UI (index.html, debug.html, css/js, log/ = Spielprotokolle)
├── 📂 tools/        # Diagnose-/Arena-/Gating-/Analyse-Skripte, siehe Tabelle unten
├── 📂 docs/         # engine_manual.md, Referenz-CSVs
├── 📂 archive/      # Legacy: alte Python-Engine/-Agenten, abgelöste Auswertungen
├── 📜 config.py     # INPUT_SIZE, NUM_ACTIONS, HIDDEN_SIZE, LR, ...
├── 📜 self_play.py  # ▶️ Self-Play-Treiber
├── 📜 train.py      # ▶️ Training + Snapshot-Hook + Auto-ONNX-Export
├── 📜 export_onnx.py# ▶️ .pth → .onnx
└── 📜 server.py     # ▶️ Flask-Web-Server
```

Zusätzlich existiert ein Release-Bundle-Pfad für Endnutzer ohne
Python/Rust-Installation: `run_mosaic.py` (Standalone-Launcher),
`mosaic_release.spec` (PyInstaller-Spec) und `tools/build_release.py` bauen
ein `dist/`-onedir-Bundle inkl. `README_SPIEL.txt` (Spielanleitung fürs
gepackte Programm) — separat gepflegt, siehe deren eigene Docstrings.

### `evaluations/` auf einen Blick

`STATUS.md` (lebendes Status-/Fahrplan-Dokument) und `elo_history.csv` sind
die primären Quellen. Daneben: `arena_trends.csv` (Punkte-/Floor-Trend je
Lauf), `frozen_eval_set.pkl` + `frozen_v1_oracle_labels.json` (eingefrorenes,
generationsübergreifendes Eval-/Oracle-Set), diverse `offline_diagnose_*`-,
`paired_gating_result_*`- und `paired_arena_*`-JSONs (Einzelläufe, per
Dateiname einem STATUS.md-Abschnitt zuordenbar), `render_diagrams.py` +
die daraus erzeugten `.svg`-Diagramme, sowie `reference_game.md` (Beispielpartie).
`game_analysis_*.md`-Berichte werden vom Spiel-Analyse-Werkzeug
(`tools/analyze_game_log.py`) erzeugt.

### `tools/`

| Skript | Zweck |
|---|---|
| `analyze_game_log.py` | Analysiert Mensch-vs-KI-Logs (`static/log/`): Parser+Replay-Kreuzvalidierung + Oracle-Bewertung jedes Zugs, Report als Markdown |
| `arena.py` | Round-Robin/Anker-Matches (Heuristik-Konfigurationen und Netz-vs-Heuristik), Rust-Engine, SPRT |
| `arena_trends.py` | Hängt je Arena-/Gating-Lauf eine Zeile (Ø-Score, Floor-Strafe) an `evaluations/arena_trends.csv` |
| `build_frozen_eval_set.py` | Erzeugt das eingefrorene, generationsübergreifende Eval-Set (`frozen_eval_set.pkl`) |
| `build_frozen_oracle_labels.py` | Labelt das Frozen-Set per tiefer Netzsuche (Oracle-Referenz für `oracle_metrics.py`) |
| `build_release.py` | Baut das PyInstaller-Windows-Bundle + ZIP für Endnutzer |
| `diagnosis.py` | Sanity-Check der Trainingsdaten (Zero-Mask, Policy-Leak, Policy-Schärfe) |
| `elo_tracker.py` | Bradley-Terry-Elo-Buchhaltung über `evaluations/elo_history.csv` (reine Auswertung, startet keine Matches) |
| `extract_kat2_examples.py` | Extrahiert Beispielzustände für "Strafleiste trotz Alternative"-Fälle aus Self-Play-Daten |
| `git_tree.py` | Druckt einen bereinigten Projekt-Verzeichnisbaum |
| `hybrid_paired_arena.py` | Gepaarter Arena-Runner für Hybrid-Suche (Priors von Netz A, Blattwerte von Netz B) |
| `model_info.py` | Zeigt Metadaten eines gespeicherten Modell-Checkpoints an |
| `offline_diagnose.py` | Value-Val-R² gesamt + je Runde, Policy-Top-1/Top-3, `--frozen` für generationsübergreifenden Vergleich |
| `oracle_metrics.py` | Offline-Metriken der Kandidaten-Netze gegen die Oracle-Labels + Rangkorrelation mit Elo |
| `paired_arena_arm_worker.py` | Ein-Arm-Worker für gepaarte Speed-Bündel-A/Bs (dünner CLI-Wrapper um `net_arena_match`) |
| `paired_arena_ismcts.py` | Gepaarter A/B: Einzel- vs. Mehrfach-Determinisierung (ISMCTS) |
| `paired_arena_round5.py` | Gepaarter A/B für die Runde-5-Budget-Umstellung (Zeit- vs. Node-Budget) |
| `paired_arena_shrink_ab.py` | Gepaarter A/B für die Value-Shrinkage-Konstante (Orchestrator) |
| `paired_arena_shrink_arm_worker.py` | Ein-Arm-Worker für den Value-Shrinkage-A/B (Netz vs. Netz) |
| `paired_arena_speedbundle.py` | Gepaarter A/B für das Suche-Speed-Bündel (Inferenz-Batching, Gumbel-Tiefe-Fixes) |
| `paired_gating.py` | Standard-Gating-Werkzeug: gepaarte Seeds/getauschte Bretter, SPRT (`p1=0.65`), Vorzeichentest |
| `rtv_redundancy_report.py` | Offline-Analyse: liefert `round_transition_value` noch eigenständige Information ggü. `bootstrap_value`? |
| `selfplay_diversity_report.py` | Öffnungs-/Verlaufs-Diversität im Self-Play-Korpus (Kollaps-Check) |

---

## Spielen & Debuggen

```bash
python server.py
# http://localhost:5000
```
Schwierigkeitsgrade bis `expert` = `v16_best`@400 Sims (`server.py`s
`DIFFICULTY_PRESETS`). Der KI-Debugger (`/debug`) zeigt einen
Value-Head-Breakdown (Roh-Value, Points-Forecast, Win-%, geblendete
Utility, Floor-Shift) sowie einen granularen Gumbel-Trace (Top-m-Kandidaten,
Sequential-Halving-Phasen mit Eliminierungen, Finalisten) pro Zug an.

Partien gegen die KI werden als Log unter `static/log/game_*.log`
mitgeschrieben. Analyse/Oracle-Bewertung dieser Logs ist in Arbeit
(`tools/analyze_game_log.py`, separat betreut).

---

## Backup

Täglicher, nicht-löschender OneDrive-Spiegel des Repos läuft als
geplanter Task. Zusätzlich schreibt `train.py` nach jedem Trainingslauf
automatisch einen benannten Modell-Snapshot nach
`<OneDrive>\Backups\mosaic-AI\models_snapshots\` (ereignisgesteuert,
eingeführt nach dem Modellverlust vom 2026-07-24 — scheitert leise mit
Warnung, falls die `OneDrive`-Umgebungsvariable fehlt, bricht das Training
selbst aber nicht ab).

---

## Architektur (Kurzreferenz)

### Neuronales Netz (`MosaicNet`, `engine/py/neural_net.py`)
```
Input (708) → Linear(512) → BN → ReLU
           → Linear(512) → BN → ReLU
           → Linear(512) → ReLU
           ┌→ Policy Head:     Linear(256) → ReLU → Linear(406)   — Aktionslogits
           ├→ Value Head:      Linear(64)  → ReLU → Linear(1) → Tanh
           ├→ Moon-Order Head: Linear(32)  → ReLU → Linear(5)     — Plackett-Luce-Scores
           └→ Points Head:     Linear(64)  → ReLU → Linear(1) → Tanh  — Punktestand-Prognose (Aux)
```
ONNX-Export trägt genau diese 4 Ausgabe-Tensoren.

### State-Tensor (708 Features)
Quelle der Wahrheit: `engine/src/features.rs` ↔ `state_to_tensor` — globaler
Zustand, aktive Wertungsplatten, Fabriken, beide Spielerboards in
Ego-Perspektive, beide 3×3-Kuppelraster, Mond-/Kuppel-Stapel, verdeckte
Information als Masken/Anteile.

### Aktionsraum (406 Aktionen)
| Typ | IDs | Beschreibung |
|---|---|---|
| pass | 0 | Kein legaler Zug |
| end_tiling | 1 | Tiling-Phase beenden |
| stone | 10–273 | Kacheln nehmen: Fabrik × Farbe × Zielreihe |
| tiling | 274–327 | Kachel legen: Musterreihe × Slot |
| choose_dome_slot | 328–354 | Kuppel-Platzierung Stufe 1: Auslage-Kachel × Slot |
| choose_draw_stack_slot | 355–390 | Stapelzug-Platzierung Stufe 1: gezogene Kachel × Slot |
| choose_dome_rotation | 391–394 | Kuppel-Platzierung Stufe 2: Rotation (beide Pfade gemeinsam) |
| use_chips | 395–400 | Musterreihe per Bonuschip abschließen |
| bonus_chip | 401–404 | Aufgedeckten Bonuschip nehmen |
| dome_stack_peek | 405 | 1 Punkt zahlen, eine verdeckte Platte ziehen (wiederholbar) |

---

## Konfiguration (Auswahl)

| Parameter | Wert | Wo | Beschreibung |
|---|---|---|---|
| `INPUT_SIZE` | 708 | `config.py` | Größe des State-Tensors |
| `NUM_ACTIONS` | 406 | `config.py` | Größe des Aktionsraums |
| `HIDDEN_SIZE` | 512 | `config.py` | Neuronen pro Hidden Layer |
| `TD_LAMBDA` | 0.5 | `engine/py/neural_net.py` | TD-Bootstrap-Blend im Value-Ziel |
| `VALUE_SCHEMA_VERSION` | 15 | `engine/py/neural_net.py` | Value-Ziel-Formel-Version (Cache-Invalidierung bei Änderung) |
| `USE_GUMBEL_SEARCH` | true | `engine/src/net_mcts.rs` | Gumbel-Suche (false = Legacy-PUCT) |
| `GUMBEL_TOP_M` | 16 | `engine/src/net_mcts.rs` | Wurzel-Kandidaten für Sequential Halving |
| `FLOOR_SHAPING_WEIGHT` | 0.3 | `engine/src/net_mcts.rs` | Exaktes Floor-Strafe-Blattwert-Additiv (validiert) |
| `DETERMINIZE_ROOT_HIDDEN_INFO` | true | `engine/src/net_mcts.rs` | Einzel-Determinisierung der verdeckten Information an der Wurzel |

Weitere Konstanten samt Kalibrierungshistorie stehen als dokumentierte
Rust-/Python-Konstanten im Code; jeder Self-Play-/Trainingslauf schreibt die
aktive Konfiguration zusätzlich in ein JSON-Manifest neben seiner Ausgabe.

---

Ausführliche Historie, Messwerte, Ablations-Ergebnisse und offene Fragen:
[`evaluations/STATUS.md`](evaluations/STATUS.md).
