# Spielanalyse: game_20260819_141804_seed179429.log

Erzeugt von `tools/analyze_game_log.py` (Commit `0f67b3e`), Laufzeit 201s.

- Seed: 179429, Startspieler: Spieler 1, KI-Spieler: KI (v21_2d_brierbest, 400 Sims)
## (a) Zusammenfassung

Endstand (aus dem Log-Text): **Spieler 1 75 : 73 KI**

Replay-Kreuzvalidierung: jede einzelne erzeugte Log-Zeile (`log_since`) wurde exakt (String-Gleichheit inkl. `[Rn] `-Präfix) gegen die Original-Logdatei geprüft (alle 329 Zeilen bestehen).

Aufloesung der Stein-Zuege: **67 ueber die Aktions-ID** (`#a`-Zeilen im Log, PREREG_action_id_logging.md), **0 ueber den Textweg** (Rueckfall fuer Logs ohne IDs).

| Spieler | oracle-bewertete Züge | Ø Δwin% zum Oracle-Top | Top-1-Treffer | Top-3-Treffer | nicht bewertet |
|---|---|---|---|---|---|
| Spieler 1 | 36 | 4.4 pp | 10/36 (28%) | 18/36 (50%) | 19 |
| KI | 43 | 1.0 pp | 28/43 (65%) | 39/43 (91%) | 10 |

- Spieler 1: nicht bewertete Züge -- 10× gespielte Aktion nicht unter Oracle-Kandidaten identifiziert, 9× Runde 5 -- exakter Alpha-Beta-Solver (round5.rs), nicht netz-oracle-bewertet
- KI: nicht bewertete Züge -- 10× Runde 5 -- exakter Alpha-Beta-Solver (round5.rs), nicht netz-oracle-bewertet

`Δwin%` = (Oracle-Top-Q − Q der gespielten Aktion) × 100, aus 5000-Sim-Netzsuche (v16_best) am Zustand VOR dem Zug. 0.0 = die gespielte Aktion WAR der Oracle-Top-Zug.

## (b) Groesste Abweichungen von der Oracle-Empfehlung

### Spieler 1

- **Runde 4, Zug #82** (dome_display): gespielt `Spieler 1: Kachel 12 → Slot (1,2) rot=0° [Plättchen 1/2]` (Rang 8/8, Q=0.409) vs. Oracle-Top `2× Stein blau vom Mondpool → Reihe 4 [2/4]` (Q=0.810) -- **Δwin% = 40.1**
- **Runde 4, Zug #80** (bonus_chip): gespielt `Spieler 1: Bonusplättchen von Fabrik 4 genommen [1/2 diese Runde]` (Rang 2/10, Q=0.632) vs. Oracle-Top `2× Stein blau vom Mondpool → Reihe 4 [2/4]` (Q=0.807) -- **Δwin% = 17.5**
- **Runde 2, Zug #23** (dome_stack_peek): gespielt `📦 Spieler 1: 1. Kachel vom Stapel gezogen (Rückseite: Wild) −1 Pkt → 4 Gesamt` (Rang 13/75, Q=0.477) vs. Oracle-Top `Kuppel #16 → (0,2)` (Q=0.595) -- **Δwin% = 11.8**

### KI

- **Runde 4, Zug #77** (dome_display): gespielt `KI: Kachel 13 → Slot (2,1) rot=0° [Plättchen 1/2]` (Rang 3/12, Q=0.398) vs. Oracle-Top `Kuppel #8 → (2,1)` (Q=0.476) -- **Δwin% = 7.8**
- **Runde 3, Zug #56** (dome_stack_peek): gespielt `📦 KI: 1. Kachel vom Stapel gezogen (Rückseite: Special) −1 Pkt → 13 Gesamt` (Rang 9/18, Q=0.666) vs. Oracle-Top `1× Stein blau vom Mondpool → Reihe 6 [6/6]` (Q=0.740) -- **Δwin% = 7.4**
- **Runde 4, Zug #69** (stone): gespielt `☀️  KI: 1× gelb von F1 → Reihe 1 [1/1]` (Rang 3/85, Q=0.554) vs. Oracle-Top `1× Stein gelb von F3 → Reihe 1 [1/1]` (Q=0.603) -- **Δwin% = 4.9** _(Match evtl. mehrdeutig)_

## (c) Wendepunkte (groesste Win%-Sprünge)

Win%-Schätzung ist immer aus Sicht von **Spieler 1** normiert (Oracle-`root_value` ist Win% des jeweils ziehenden Spielers am Zustand VOR dem Zug; für Zug-Perspektive KI wird 100−root_value gebildet).

| von (Zug#/Runde) | nach (Zug#/Runde) | Δ Win% (Spieler 1) |
|---|---|---|
| #83 (R4, KI zieht, 59.0%) | #84 (R4, Spieler 1 zieht, 25.4%) | -33.6 pp |
| #67 (R3, Spieler 1 zieht, 34.6%) | #68 (R4, Spieler 1 zieht, 57.9%) | +23.4 pp |
| #71 (R4, KI zieht, 51.9%) | #72 (R4, Spieler 1 zieht, 70.7%) | +18.8 pp |
| #24 (R2, Spieler 1 zieht, 56.6%) | #25 (R2, KI zieht, 37.9%) | -18.7 pp |
| #72 (R4, Spieler 1 zieht, 70.7%) | #73 (R4, KI zieht, 52.1%) | -18.6 pp |

## (d) Die Wertungsplatten-Story

Punktestand am Ende jeder Runde (reine Text-Extraktion aus dem Log -- unabhaengig vom Replay-Fortschritt, siehe Grenzen):

| Runde | Spieler 1 | KI |
|---|---|---|
| 1 | 5 | – |
| 2 | 7 | 14 |
| 3 | 25 | – |
| 4 | 44 | 49 |
| 5 | – | 66 |

(Rohpunktestand direkt vor der Endwertung, aus der `# SPIELENDE:`-Kopfzeile: Spieler 1 61 : 66 KI -- fehlende "–"-Werte oben bedeuten lediglich 0 Pkt Strafe in dieser Runde, keine Lücke.)

Endwertung (Wertungsplatten-Bonus):

- **Spieler 1**: +14 Pkt -> Gesamt 75 Pkt
  - 🎨 Farbenreiche Reihen: 0 Pkt
  - ↕️ Vertikale Reihen: 14 Pkt
  - ↗️ Diagonale Reihen: 0 Pkt
- **KI**: +7 Pkt -> Gesamt 73 Pkt
  - 🎨 Farbenreiche Reihen: 0 Pkt
  - ↕️ Vertikale Reihen: 7 Pkt
  - ↗️ Diagonale Reihen: 0 Pkt

Vor der Endwertung stand es 61 : 66; nach dem Wertungsplatten-Bonus 75 : 73.
**Die Wertungsplatten haben das Ergebnis gedreht**: ohne Endwertung hätte KI gewonnen, nach der Endwertung gewinnt Spieler 1.

Win%-Verlauf (aus Spieler 1-Sicht) über den oracle-bewerteten Teil der Partie:

| Zug# | Runde | zieht | Win% (Spieler 1) |
|---|---|---|---|
| 1 | 1 | Spieler 1 | 52.9% |
| 2 | 1 | KI | 49.2% |
| 3 | 1 | Spieler 1 | 51.2% |
| 4 | 1 | KI | 47.1% |
| 5 | 1 | Spieler 1 | 52.4% |
| 6 | 1 | KI | 45.4% |
| 7 | 1 | Spieler 1 | 49.4% |
| 8 | 1 | KI | 45.7% |
| 9 | 1 | Spieler 1 | 48.4% |
| 10 | 1 | Spieler 1 | 49.8% |
| 11 | 1 | KI | 46.6% |
| 12 | 1 | Spieler 1 | 48.5% |
| 13 | 1 | KI | 44.0% |
| 14 | 1 | Spieler 1 | 47.6% |
| 15 | 1 | KI | 41.9% |
| 16 | 1 | Spieler 1 | 48.6% |
| 17 | 1 | KI | 43.2% |
| 18 | 1 | Spieler 1 | 47.1% |
| 19 | 1 | KI | 41.4% |
| 20 | 1 | Spieler 1 | 43.6% |
| 21 | 2 | Spieler 1 | 54.5% |
| 22 | 2 | KI | 39.1% |
| 23 | 2 | Spieler 1 | 56.0% |
| 24 | 2 | Spieler 1 | 56.6% |
| 25 | 2 | KI | 37.9% |
| 26 | 2 | Spieler 1 | 46.3% |
| 27 | 2 | KI | 35.3% |
| 28 | 2 | Spieler 1 | 42.2% |
| 29 | 2 | KI | 33.4% |
| 30 | 2 | Spieler 1 | 40.3% |
| 31 | 2 | KI | 28.0% |
| 32 | 2 | Spieler 1 | 37.1% |
| 33 | 2 | KI | 32.9% |
| 34 | 2 | Spieler 1 | 34.9% |
| 35 | 2 | KI | 31.9% |
| 36 | 2 | Spieler 1 | 36.2% |
| 37 | 2 | KI | 30.9% |
| 38 | 2 | Spieler 1 | 33.6% |
| 39 | 2 | KI | 36.3% |
| 40 | 2 | Spieler 1 | 33.9% |
| 41 | 2 | KI | 30.1% |
| 42 | 2 | Spieler 1 | 32.2% |
| 43 | 2 | KI | 29.5% |
| 44 | 2 | Spieler 1 | 31.2% |
| 45 | 3 | Spieler 1 | 47.7% |
| 46 | 3 | KI | 31.3% |
| 47 | 3 | Spieler 1 | 46.0% |
| 48 | 3 | KI | 31.3% |
| 49 | 3 | Spieler 1 | 45.8% |
| 50 | 3 | KI | 44.7% |
| 51 | 3 | Spieler 1 | 47.1% |
| 52 | 3 | KI | 36.1% |
| 53 | 3 | Spieler 1 | 46.3% |
| 54 | 3 | KI | 37.0% |
| 55 | 3 | Spieler 1 | 44.7% |
| 56 | 3 | KI | 28.9% |
| 57 | 3 | KI | 27.7% |
| 58 | 3 | Spieler 1 | 42.8% |
| 59 | 3 | KI | 34.4% |
| 60 | 3 | KI | 31.3% |
| 61 | 3 | Spieler 1 | 45.3% |
| 62 | 3 | KI | 32.5% |
| 63 | 3 | Spieler 1 | 43.4% |
| 64 | 3 | KI | 35.4% |
| 65 | 3 | Spieler 1 | 42.7% |
| 66 | 3 | KI | 33.2% |
| 67 | 3 | Spieler 1 | 34.6% |
| 68 | 4 | Spieler 1 | 57.9% |
| 69 | 4 | KI | 45.2% |
| 70 | 4 | Spieler 1 | 58.7% |
| 71 | 4 | KI | 51.9% |
| 72 | 4 | Spieler 1 | 70.7% |
| 73 | 4 | KI | 52.1% |
| 74 | 4 | Spieler 1 | 57.9% |
| 75 | 4 | KI | 72.6% |
| 76 | 4 | Spieler 1 | 71.5% |
| 77 | 4 | KI | 59.9% |
| 78 | 4 | Spieler 1 | 65.3% |
| 79 | 4 | KI | 59.5% |
| 80 | 4 | Spieler 1 | 63.7% |
| 81 | 4 | KI | 58.8% |
| 82 | 4 | Spieler 1 | 58.0% |
| 83 | 4 | KI | 59.0% |
| 84 | 4 | Spieler 1 | 25.4% |
| 85 | 4 | KI | 42.6% |
| 86 | 4 | Spieler 1 | 28.7% |
| 87 | 4 | KI | 36.4% |
| 88 | 4 | KI | 36.5% |
| 89 | 4 | Spieler 1 | 31.5% |

Das Oracle sah Spieler 1 zu Beginn der bewerteten Zuege bei **52.9%** und am Ende von Runde 4 bei **31.5%** Gewinnwahrscheinlichkeit (jeweils aus Sicht des ziehenden Spielers umgerechnet). Runde 5 (Endwertung inkl. Wertungsplatten) lief ausserhalb dieser Betrachtung über den exakten Solver.

## Grenzen und Auffälligkeiten (ehrlich dokumentiert)

- **Determinisierung**: `net_search_state_json` rekonstruiert verdeckte Information (Beutel/Turm/Kuppelstapel/Bonuschip-Pool) aus Zählern/Masken und mischt sie NEU mit einem festen, aus dem Zugindex abgeleiteten Seed -- das Oracle sieht also, wie ein echter Spieler, KEINE verdeckte Information, nur eine andere zufällige Mischung als das tatsächliche Spiel. Ein einzelner 5000-Sim-Lauf ist dadurch eine starke, aber keine perfekte Schätzung (siehe Task #89 fuer die empirisch verifizierte Rekonstruktions-Genauigkeit).
- **Runde 5** läuft über den exakten Alpha-Beta-Solver (kein Informationsgehalt mehr, siehe `round5.rs`) und wurde bewusst NICHT netz-oracle-bewertet (andere Skala/Semantik als die PUCT-Netzsuche der Runden 1-4).
- **Kuppel-Rotation**: die Rotationswahl (Stufe 2 nach Kachel+Slot) wird NICHT separat oracle-bewertet -- `apply_dome`/`apply_dome_stack_choose` bleiben nach aussen atomar, die PendingDomeChoice-Zwischenzustände haben laut Task #89 Serialisierungs-Näherungen.
- **`root_value`-Interpretation**: als Win%-Schätzung des jeweils ziehenden Spielers am Zustand VOR seinem Zug interpretiert (Projekt-Konvention); keine unabhängig re-kalibrierte Wahrscheinlichkeit.
- **Oracle-Zug-Zuordnung** erfolgt über eine geparste Kurzbeschreibung (Farbe/Quelle/Zielreihe bzw. Kachel/Slot/Fabrik) gegen die von der Suche gelabelten Kandidaten; bei der Stapel-Wahl (`choose_draw_stack_slot`) fehlt die Kachel-ID im Label, ein `_(Match evtl. mehrdeutig)_`-Hinweis markiert das im Text.
