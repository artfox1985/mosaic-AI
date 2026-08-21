# Spielanalyse: game_20260818_224021_seed462727.log

Erzeugt von `tools/analyze_game_log.py` (Commit `0f67b3e`), Laufzeit 294s.

- Seed: 462727, Startspieler: Spielerin, KI-Spieler: KI (v21_2d_brierbest, 400 Sims)
## (a) Zusammenfassung

Endstand (aus dem Log-Text): **Spielerin 74 : 57 KI**

Replay-Kreuzvalidierung: jede einzelne erzeugte Log-Zeile (`log_since`) wurde exakt (String-Gleichheit inkl. `[Rn] `-Präfix) gegen die Original-Logdatei geprüft (alle 307 Zeilen bestehen).

Aufloesung der Stein-Zuege: **63 ueber die Aktions-ID** (`#a`-Zeilen im Log, PREREG_action_id_logging.md), **0 ueber den Textweg** (Rueckfall fuer Logs ohne IDs).

| Spieler | oracle-bewertete Züge | Ø Δwin% zum Oracle-Top | Top-1-Treffer | Top-3-Treffer | nicht bewertet |
|---|---|---|---|---|---|
| Spielerin | 32 | 4.4 pp | 12/32 (38%) | 18/32 (56%) | 22 |
| KI | 41 | 1.2 pp | 21/41 (51%) | 34/41 (83%) | 8 |

- Spielerin: nicht bewertete Züge -- 12× gespielte Aktion nicht unter Oracle-Kandidaten identifiziert, 10× Runde 5 -- exakter Alpha-Beta-Solver (round5.rs), nicht netz-oracle-bewertet
- KI: nicht bewertete Züge -- 8× Runde 5 -- exakter Alpha-Beta-Solver (round5.rs), nicht netz-oracle-bewertet

`Δwin%` = (Oracle-Top-Q − Q der gespielten Aktion) × 100, aus 5000-Sim-Netzsuche (v16_best) am Zustand VOR dem Zug. 0.0 = die gespielte Aktion WAR der Oracle-Top-Zug.

## (b) Groesste Abweichungen von der Oracle-Empfehlung

### Spielerin

- **Runde 3, Zug #53** (stone): gespielt `🌙 Spielerin: 1 (1)× blau von GF → Reihe 5 [4/5]` (Rang 14/35, Q=0.476) vs. Oracle-Top `3× Stein rot von F2 → Reihe 4 [3/4]` (Q=0.677) -- **Δwin% = 20.1**
- **Runde 2, Zug #33** (stone): gespielt `🌙 Spielerin: 3 (1+2)× türkis von F2, GF → Reihe 5 [3/5]` (Rang 10/23, Q=0.563) vs. Oracle-Top `Kuppel #4 → (0,1)` (Q=0.696) -- **Δwin% = 13.2**
- **Runde 4, Zug #76** (dome_display): gespielt `Spielerin: Kachel 2 → Slot (2,2) rot=180° [Plättchen 1/2]` (Rang 10/16, Q=0.459) vs. Oracle-Top `Stapel: verdeckt ziehen` (Q=0.584) -- **Δwin% = 12.5**

### KI

- **Runde 1, Zug #7** (dome_stack): gespielt `KI: Kachel 17 → Slot (0,1) rot=0° [Plättchen 1/2]` (Rang 9/9, Q=0.488) vs. Oracle-Top `Stapel → (2,0)` (Q=0.552) -- **Δwin% = 6.4**
- **Runde 2, Zug #32** (stone): gespielt `🌙 KI: 1 (1)× rot von F4 → Reihe 2 [1/2]` (Rang 11/16, Q=0.342) vs. Oracle-Top `3× Stein türkis vom Mondpool → Reihe 1 [1/1] (+2 Strafleiste)` (Q=0.403) -- **Δwin% = 6.2**
- **Runde 3, Zug #56** (stone): gespielt `🌙 KI: 2 (1+1)× rot von F3, F4 → Reihe 4 [2/4]` (Rang 2/16, Q=0.624) vs. Oracle-Top `Kuppel #9 → (1,2)` (Q=0.679) -- **Δwin% = 5.4**

## (c) Wendepunkte (groesste Win%-Sprünge)

Win%-Schätzung ist immer aus Sicht von **Spielerin** normiert (Oracle-`root_value` ist Win% des jeweils ziehenden Spielers am Zustand VOR dem Zug; für Zug-Perspektive KI wird 100−root_value gebildet).

| von (Zug#/Runde) | nach (Zug#/Runde) | Δ Win% (Spielerin) |
|---|---|---|
| #76 (R4, Spielerin zieht, 51.4%) | #77 (R4, KI zieht, 7.8%) | -43.6 pp |
| #74 (R4, Spielerin zieht, 60.7%) | #75 (R4, KI zieht, 17.3%) | -43.4 pp |
| #73 (R4, KI zieht, 17.5%) | #74 (R4, Spielerin zieht, 60.7%) | +43.2 pp |
| #75 (R4, KI zieht, 17.3%) | #76 (R4, Spielerin zieht, 51.4%) | +34.1 pp |
| #71 (R4, KI zieht, 11.4%) | #72 (R4, Spielerin zieht, 44.6%) | +33.2 pp |

## (d) Die Wertungsplatten-Story

Punktestand am Ende jeder Runde (reine Text-Extraktion aus dem Log -- unabhaengig vom Replay-Fortschritt, siehe Grenzen):

| Runde | Spielerin | KI |
|---|---|---|
| 1 | 5 | – |
| 2 | 18 | 12 |
| 3 | 21 | 21 |
| 4 | 31 | – |
| 5 | 39 | 43 |

(Rohpunktestand direkt vor der Endwertung, aus der `# SPIELENDE:`-Kopfzeile: Spielerin 39 : 43 KI -- fehlende "–"-Werte oben bedeuten lediglich 0 Pkt Strafe in dieser Runde, keine Lücke.)

Endwertung (Wertungsplatten-Bonus):

- **Spielerin**: +35 Pkt -> Gesamt 74 Pkt
  - ↕️ Vertikale Reihen: 14 Pkt
  - 🔲 Eckplatten: 11 Pkt
  - 🌈 Mehrfarbige Felder: 10 Pkt
- **KI**: +14 Pkt -> Gesamt 57 Pkt
  - ↕️ Vertikale Reihen: 0 Pkt
  - 🔲 Eckplatten: 6 Pkt
  - 🌈 Mehrfarbige Felder: 8 Pkt

Vor der Endwertung stand es 39 : 43; nach dem Wertungsplatten-Bonus 74 : 57.
**Die Wertungsplatten haben das Ergebnis gedreht**: ohne Endwertung hätte KI gewonnen, nach der Endwertung gewinnt Spielerin.

Win%-Verlauf (aus Spielerin-Sicht) über den oracle-bewerteten Teil der Partie:

| Zug# | Runde | zieht | Win% (Spieler 1) |
|---|---|---|---|
| 1 | 1 | Spielerin | 53.1% |
| 2 | 1 | KI | 51.1% |
| 3 | 1 | Spielerin | 51.1% |
| 4 | 1 | KI | 45.8% |
| 5 | 1 | Spielerin | 51.9% |
| 6 | 1 | KI | 44.4% |
| 7 | 1 | KI | 45.7% |
| 8 | 1 | Spielerin | 54.6% |
| 9 | 1 | KI | 48.9% |
| 10 | 1 | Spielerin | 51.6% |
| 11 | 1 | KI | 49.3% |
| 12 | 1 | Spielerin | 51.7% |
| 13 | 1 | KI | 47.0% |
| 14 | 1 | Spielerin | 52.0% |
| 15 | 1 | KI | 47.0% |
| 16 | 1 | Spielerin | 50.8% |
| 17 | 1 | KI | 45.3% |
| 18 | 1 | Spielerin | 53.8% |
| 19 | 1 | KI | 45.7% |
| 20 | 1 | Spielerin | 52.5% |
| 21 | 1 | KI | 43.8% |
| 22 | 1 | Spielerin | 56.3% |
| 23 | 1 | KI | 43.4% |
| 24 | 2 | Spielerin | 52.9% |
| 25 | 2 | KI | 53.9% |
| 26 | 2 | Spielerin | 54.1% |
| 27 | 2 | KI | 48.4% |
| 28 | 2 | Spielerin | 56.4% |
| 29 | 2 | KI | 54.4% |
| 30 | 2 | KI | 49.8% |
| 31 | 2 | Spielerin | 59.0% |
| 32 | 2 | KI | 65.4% |
| 33 | 2 | Spielerin | 64.6% |
| 34 | 2 | KI | 56.7% |
| 35 | 2 | Spielerin | 59.7% |
| 36 | 2 | KI | 69.9% |
| 37 | 2 | Spielerin | 62.7% |
| 38 | 2 | KI | 66.8% |
| 39 | 2 | Spielerin | 62.7% |
| 40 | 2 | KI | 66.5% |
| 41 | 2 | Spielerin | 63.3% |
| 42 | 2 | KI | 67.8% |
| 43 | 2 | Spielerin | 63.9% |
| 44 | 2 | Spielerin | 58.4% |
| 45 | 3 | Spielerin | 69.0% |
| 46 | 3 | KI | 57.2% |
| 47 | 3 | Spielerin | 68.1% |
| 48 | 3 | KI | 56.3% |
| 49 | 3 | Spielerin | 64.8% |
| 50 | 3 | KI | 57.7% |
| 51 | 3 | Spielerin | 53.4% |
| 52 | 3 | KI | 58.6% |
| 53 | 3 | Spielerin | 59.7% |
| 54 | 3 | KI | 43.9% |
| 55 | 3 | Spielerin | 49.0% |
| 56 | 3 | KI | 39.8% |
| 57 | 3 | Spielerin | 50.8% |
| 58 | 3 | KI | 37.3% |
| 59 | 3 | Spielerin | 51.4% |
| 60 | 3 | KI | 30.0% |
| 61 | 3 | Spielerin | 39.5% |
| 62 | 3 | KI | 35.3% |
| 63 | 3 | Spielerin | 41.7% |
| 64 | 3 | Spielerin | 39.9% |
| 65 | 3 | KI | 31.7% |
| 66 | 4 | Spielerin | 40.9% |
| 67 | 4 | KI | 17.5% |
| 68 | 4 | Spielerin | 43.9% |
| 69 | 4 | KI | 18.9% |
| 70 | 4 | Spielerin | 41.8% |
| 71 | 4 | KI | 11.4% |
| 72 | 4 | Spielerin | 44.6% |
| 73 | 4 | KI | 17.5% |
| 74 | 4 | Spielerin | 60.7% |
| 75 | 4 | KI | 17.3% |
| 76 | 4 | Spielerin | 51.4% |
| 77 | 4 | KI | 7.8% |
| 78 | 4 | Spielerin | 33.5% |
| 79 | 4 | KI | 6.9% |
| 80 | 4 | Spielerin | 13.0% |
| 81 | 4 | KI | 5.8% |
| 82 | 4 | Spielerin | 15.6% |
| 83 | 4 | KI | 5.8% |
| 84 | 4 | Spielerin | 22.0% |
| 85 | 4 | Spielerin | 22.1% |

Das Oracle sah Spielerin zu Beginn der bewerteten Zuege bei **53.1%** und am Ende von Runde 4 bei **22.1%** Gewinnwahrscheinlichkeit (jeweils aus Sicht des ziehenden Spielers umgerechnet). Runde 5 (Endwertung inkl. Wertungsplatten) lief ausserhalb dieser Betrachtung über den exakten Solver.

## Grenzen und Auffälligkeiten (ehrlich dokumentiert)

- **Determinisierung**: `net_search_state_json` rekonstruiert verdeckte Information (Beutel/Turm/Kuppelstapel/Bonuschip-Pool) aus Zählern/Masken und mischt sie NEU mit einem festen, aus dem Zugindex abgeleiteten Seed -- das Oracle sieht also, wie ein echter Spieler, KEINE verdeckte Information, nur eine andere zufällige Mischung als das tatsächliche Spiel. Ein einzelner 5000-Sim-Lauf ist dadurch eine starke, aber keine perfekte Schätzung (siehe Task #89 fuer die empirisch verifizierte Rekonstruktions-Genauigkeit).
- **Runde 5** läuft über den exakten Alpha-Beta-Solver (kein Informationsgehalt mehr, siehe `round5.rs`) und wurde bewusst NICHT netz-oracle-bewertet (andere Skala/Semantik als die PUCT-Netzsuche der Runden 1-4).
- **Kuppel-Rotation**: die Rotationswahl (Stufe 2 nach Kachel+Slot) wird NICHT separat oracle-bewertet -- `apply_dome`/`apply_dome_stack_choose` bleiben nach aussen atomar, die PendingDomeChoice-Zwischenzustände haben laut Task #89 Serialisierungs-Näherungen.
- **`root_value`-Interpretation**: als Win%-Schätzung des jeweils ziehenden Spielers am Zustand VOR seinem Zug interpretiert (Projekt-Konvention); keine unabhängig re-kalibrierte Wahrscheinlichkeit.
- **Oracle-Zug-Zuordnung** erfolgt über eine geparste Kurzbeschreibung (Farbe/Quelle/Zielreihe bzw. Kachel/Slot/Fabrik) gegen die von der Suche gelabelten Kandidaten; bei der Stapel-Wahl (`choose_draw_stack_slot`) fehlt die Kachel-ID im Label, ein `_(Match evtl. mehrdeutig)_`-Hinweis markiert das im Text.
