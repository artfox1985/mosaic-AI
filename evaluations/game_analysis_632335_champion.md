# Spielanalyse: game_20260818_214620_seed632335.log

Erzeugt von `tools/analyze_game_log.py` (Commit `47d36f7`), Laufzeit 220s.

- Seed: 632335, Startspieler: Spieler 1, KI-Spieler: KI (v21_2d_brierbest, 400 Sims)
## (a) Zusammenfassung

Endstand (aus dem Log-Text): **Spieler 1 97 : 59 KI**

Replay-Kreuzvalidierung: jede einzelne erzeugte Log-Zeile (`log_since`) wurde exakt (String-Gleichheit inkl. `[Rn] `-Präfix) gegen die Original-Logdatei geprüft (alle 320 Zeilen bestehen).

Aufloesung der Stein-Zuege: **61 ueber die Aktions-ID** (`#a`-Zeilen im Log, PREREG_action_id_logging.md), **0 ueber den Textweg** (Rueckfall fuer Logs ohne IDs).

| Spieler | oracle-bewertete Züge | Ø Δwin% zum Oracle-Top | Top-1-Treffer | Top-3-Treffer | nicht bewertet |
|---|---|---|---|---|---|
| Spieler 1 | 33 | 3.7 pp | 14/33 (42%) | 21/33 (64%) | 17 |
| KI | 43 | 1.3 pp | 21/43 (49%) | 28/43 (65%) | 8 |

- Spieler 1: nicht bewertete Züge -- 9× Runde 5 -- exakter Alpha-Beta-Solver (round5.rs), nicht netz-oracle-bewertet, 8× gespielte Aktion nicht unter Oracle-Kandidaten identifiziert
- KI: nicht bewertete Züge -- 8× Runde 5 -- exakter Alpha-Beta-Solver (round5.rs), nicht netz-oracle-bewertet

`Δwin%` = (Oracle-Top-Q − Q der gespielten Aktion) × 100, aus 5000-Sim-Netzsuche (v16_best) am Zustand VOR dem Zug. 0.0 = die gespielte Aktion WAR der Oracle-Top-Zug.

## (b) Groesste Abweichungen von der Oracle-Empfehlung

### Spieler 1

- **Runde 3, Zug #49** (stone): gespielt `🌙 Spieler 1: 3 (1+2)× gelb von F1, GF → Reihe 2 [2/2] (+1 Strafleiste)` (Rang 15/40, Q=0.436) vs. Oracle-Top `1× Stein türkis von F4 → Reihe 1 [1/1]` (Q=0.611) -- **Δwin% = 17.5**
- **Runde 3, Zug #54** (stone): gespielt `🌙 Spieler 1: 3 (1+1+1)× schwarz von F1, F2, GF → Reihe 3 [3/3]` (Rang 8/10, Q=0.463) vs. Oracle-Top `Kuppel #4 → (0,2)` (Q=0.601) -- **Δwin% = 13.8**
- **Runde 4, Zug #71** (dome_display): gespielt `Spieler 1: Kachel 2 → Slot (0,2) rot=180° [Plättchen 2/2]` (Rang 13/37, Q=0.791) vs. Oracle-Top `2× Stein blau von F3 → Reihe 4 [4/4]` (Q=0.927) -- **Δwin% = 13.7**

### KI

- **Runde 3, Zug #51** (dome_stack): gespielt `KI: Kachel 11 → Slot (1,2) rot=0° [Plättchen 2/2]` (Rang 4/4, Q=0.429) vs. Oracle-Top `Stapel: verdeckt ziehen` (Q=0.523) -- **Δwin% = 9.4**
- **Runde 3, Zug #53** (stone): gespielt `🌙 KI: 2 (1+1)× rot von F1, F2 → Reihe 4 [2/4]` (Rang 7/12, Q=0.373) vs. Oracle-Top `2× Stein blau vom Mondpool → Reihe 3 [2/3]` (Q=0.439) -- **Δwin% = 6.6**
- **Runde 2, Zug #31** (dome_stack): gespielt `KI: Kachel 6 → Slot (1,1) rot=0° [Plättchen 2/2]` (Rang 5/6, Q=0.441) vs. Oracle-Top `Stapel: verdeckt ziehen` (Q=0.496) -- **Δwin% = 5.5**

## (c) Wendepunkte (groesste Win%-Sprünge)

Win%-Schätzung ist immer aus Sicht von **Spieler 1** normiert (Oracle-`root_value` ist Win% des jeweils ziehenden Spielers am Zustand VOR dem Zug; für Zug-Perspektive KI wird 100−root_value gebildet).

| von (Zug#/Runde) | nach (Zug#/Runde) | Δ Win% (Spieler 1) |
|---|---|---|
| #34 (R2, Spieler 1 zieht, 72.7%) | #35 (R2, KI zieht, 51.1%) | -21.7 pp |
| #64 (R3, Spieler 1 zieht, 77.2%) | #65 (R4, Spieler 1 zieht, 95.7%) | +18.4 pp |
| #40 (R2, Spieler 1 zieht, 62.5%) | #41 (R2, KI zieht, 45.3%) | -17.2 pp |
| #38 (R2, Spieler 1 zieht, 63.0%) | #39 (R2, KI zieht, 46.4%) | -16.6 pp |
| #39 (R2, KI zieht, 46.4%) | #40 (R2, Spieler 1 zieht, 62.5%) | +16.1 pp |

## (d) Die Wertungsplatten-Story

Punktestand am Ende jeder Runde (reine Text-Extraktion aus dem Log -- unabhaengig vom Replay-Fortschritt, siehe Grenzen):

| Runde | Spieler 1 | KI |
|---|---|---|
| 1 | 9 | 7 |
| 2 | 21 | 12 |
| 3 | 34 | – |
| 4 | 41 | 36 |
| 5 | 66 | – |

(Rohpunktestand direkt vor der Endwertung, aus der `# SPIELENDE:`-Kopfzeile: Spieler 1 66 : 56 KI -- fehlende "–"-Werte oben bedeuten lediglich 0 Pkt Strafe in dieser Runde, keine Lücke.)

Endwertung (Wertungsplatten-Bonus):

- **Spieler 1**: +31 Pkt -> Gesamt 97 Pkt
  - 🌈 Mehrfarbige Felder: 6 Pkt
  - 🔲 Eckplatten: 11 Pkt
  - ↕️ Vertikale Reihen: 14 Pkt
- **KI**: +3 Pkt -> Gesamt 59 Pkt
  - 🌈 Mehrfarbige Felder: 0 Pkt
  - 🔲 Eckplatten: 3 Pkt
  - ↕️ Vertikale Reihen: 0 Pkt

Vor der Endwertung stand es 66 : 56; nach dem Wertungsplatten-Bonus 97 : 59.

Win%-Verlauf (aus Spieler 1-Sicht) über den oracle-bewerteten Teil der Partie:

| Zug# | Runde | zieht | Win% (Spieler 1) |
|---|---|---|---|
| 1 | 1 | Spieler 1 | 51.5% |
| 2 | 1 | KI | 46.9% |
| 3 | 1 | Spieler 1 | 45.9% |
| 4 | 1 | KI | 46.0% |
| 5 | 1 | Spieler 1 | 45.0% |
| 6 | 1 | KI | 41.3% |
| 7 | 1 | Spieler 1 | 46.9% |
| 8 | 1 | KI | 44.6% |
| 9 | 1 | Spieler 1 | 49.7% |
| 10 | 1 | KI | 46.4% |
| 11 | 1 | Spieler 1 | 47.6% |
| 12 | 1 | KI | 40.3% |
| 13 | 1 | Spieler 1 | 44.4% |
| 14 | 1 | KI | 40.2% |
| 15 | 1 | Spieler 1 | 45.5% |
| 16 | 1 | KI | 44.6% |
| 17 | 1 | Spieler 1 | 48.9% |
| 18 | 1 | KI | 38.6% |
| 19 | 1 | Spieler 1 | 50.0% |
| 20 | 1 | KI | 37.5% |
| 21 | 1 | Spieler 1 | 50.3% |
| 22 | 1 | Spieler 1 | 46.3% |
| 23 | 2 | Spieler 1 | 56.2% |
| 24 | 2 | KI | 45.8% |
| 25 | 2 | Spieler 1 | 51.7% |
| 26 | 2 | KI | 47.6% |
| 27 | 2 | Spieler 1 | 58.3% |
| 28 | 2 | KI | 51.5% |
| 29 | 2 | Spieler 1 | 57.3% |
| 30 | 2 | KI | 53.3% |
| 31 | 2 | KI | 54.7% |
| 32 | 2 | Spieler 1 | 69.0% |
| 33 | 2 | KI | 56.9% |
| 34 | 2 | Spieler 1 | 72.7% |
| 35 | 2 | KI | 51.1% |
| 36 | 2 | Spieler 1 | 59.7% |
| 37 | 2 | KI | 48.1% |
| 38 | 2 | Spieler 1 | 63.0% |
| 39 | 2 | KI | 46.4% |
| 40 | 2 | Spieler 1 | 62.5% |
| 41 | 2 | KI | 45.3% |
| 42 | 2 | KI | 44.6% |
| 43 | 3 | Spieler 1 | 59.0% |
| 44 | 3 | KI | 56.8% |
| 45 | 3 | Spieler 1 | 50.1% |
| 46 | 3 | KI | 46.2% |
| 47 | 3 | Spieler 1 | 54.1% |
| 48 | 3 | KI | 47.1% |
| 49 | 3 | Spieler 1 | 56.0% |
| 50 | 3 | KI | 51.0% |
| 51 | 3 | KI | 52.4% |
| 52 | 3 | Spieler 1 | 56.6% |
| 53 | 3 | KI | 65.5% |
| 54 | 3 | Spieler 1 | 56.8% |
| 55 | 3 | KI | 56.2% |
| 56 | 3 | Spieler 1 | 70.4% |
| 57 | 3 | KI | 76.7% |
| 58 | 3 | Spieler 1 | 69.8% |
| 59 | 3 | KI | 76.6% |
| 60 | 3 | Spieler 1 | 72.5% |
| 61 | 3 | KI | 77.7% |
| 62 | 3 | Spieler 1 | 74.1% |
| 63 | 3 | KI | 74.4% |
| 64 | 3 | Spieler 1 | 77.2% |
| 65 | 4 | Spieler 1 | 95.7% |
| 66 | 4 | KI | 91.9% |
| 67 | 4 | Spieler 1 | 94.1% |
| 68 | 4 | KI | 94.4% |
| 69 | 4 | Spieler 1 | 91.4% |
| 70 | 4 | KI | 91.0% |
| 71 | 4 | Spieler 1 | 89.2% |
| 72 | 4 | KI | 88.7% |
| 73 | 4 | Spieler 1 | 91.6% |
| 74 | 4 | KI | 92.9% |
| 75 | 4 | Spieler 1 | 91.7% |
| 76 | 4 | KI | 92.7% |
| 77 | 4 | Spieler 1 | 93.5% |
| 78 | 4 | KI | 96.8% |
| 79 | 4 | Spieler 1 | 92.8% |
| 80 | 4 | KI | 98.5% |
| 81 | 4 | KI | 97.1% |
| 82 | 4 | Spieler 1 | 91.3% |
| 83 | 4 | KI | 97.1% |
| 84 | 4 | KI | 97.1% |

Das Oracle sah Spieler 1 zu Beginn der bewerteten Zuege bei **51.5%** und am Ende von Runde 4 bei **97.1%** Gewinnwahrscheinlichkeit (jeweils aus Sicht des ziehenden Spielers umgerechnet). Runde 5 (Endwertung inkl. Wertungsplatten) lief ausserhalb dieser Betrachtung über den exakten Solver.

## Grenzen und Auffälligkeiten (ehrlich dokumentiert)

- **Determinisierung**: `net_search_state_json` rekonstruiert verdeckte Information (Beutel/Turm/Kuppelstapel/Bonuschip-Pool) aus Zählern/Masken und mischt sie NEU mit einem festen, aus dem Zugindex abgeleiteten Seed -- das Oracle sieht also, wie ein echter Spieler, KEINE verdeckte Information, nur eine andere zufällige Mischung als das tatsächliche Spiel. Ein einzelner 5000-Sim-Lauf ist dadurch eine starke, aber keine perfekte Schätzung (siehe Task #89 fuer die empirisch verifizierte Rekonstruktions-Genauigkeit).
- **Runde 5** läuft über den exakten Alpha-Beta-Solver (kein Informationsgehalt mehr, siehe `round5.rs`) und wurde bewusst NICHT netz-oracle-bewertet (andere Skala/Semantik als die PUCT-Netzsuche der Runden 1-4).
- **Kuppel-Rotation**: die Rotationswahl (Stufe 2 nach Kachel+Slot) wird NICHT separat oracle-bewertet -- `apply_dome`/`apply_dome_stack_choose` bleiben nach aussen atomar, die PendingDomeChoice-Zwischenzustände haben laut Task #89 Serialisierungs-Näherungen.
- **`root_value`-Interpretation**: als Win%-Schätzung des jeweils ziehenden Spielers am Zustand VOR seinem Zug interpretiert (Projekt-Konvention); keine unabhängig re-kalibrierte Wahrscheinlichkeit.
- **Oracle-Zug-Zuordnung** erfolgt über eine geparste Kurzbeschreibung (Farbe/Quelle/Zielreihe bzw. Kachel/Slot/Fabrik) gegen die von der Suche gelabelten Kandidaten; bei der Stapel-Wahl (`choose_draw_stack_slot`) fehlt die Kachel-ID im Label, ein `_(Match evtl. mehrdeutig)_`-Hinweis markiert das im Text.
