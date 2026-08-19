# Spielanalyse: game_20260818_221619_seed698355.log

Erzeugt von `tools/analyze_game_log.py` (Commit `0f67b3e`), Laufzeit 194s.

- Seed: 698355, Startspieler: Spieler 1, KI-Spieler: KI (v21_2d_brierbest, 400 Sims)
## (a) Zusammenfassung

Endstand (aus dem Log-Text): **Spieler 1 54 : 43 KI**

Replay-Kreuzvalidierung: jede einzelne erzeugte Log-Zeile (`log_since`) wurde exakt (String-Gleichheit inkl. `[Rn] `-Präfix) gegen die Original-Logdatei geprüft (alle 321 Zeilen bestehen).

Aufloesung der Stein-Zuege: **62 ueber die Aktions-ID** (`#a`-Zeilen im Log, PREREG_action_id_logging.md), **0 ueber den Textweg** (Rueckfall fuer Logs ohne IDs).

| Spieler | oracle-bewertete Züge | Ø Δwin% zum Oracle-Top | Top-1-Treffer | Top-3-Treffer | nicht bewertet |
|---|---|---|---|---|---|
| Spieler 1 | 34 | 2.9 pp | 10/34 (29%) | 19/34 (56%) | 19 |
| KI | 41 | 0.8 pp | 23/41 (56%) | 33/41 (80%) | 8 |

- Spieler 1: nicht bewertete Züge -- 12× gespielte Aktion nicht unter Oracle-Kandidaten identifiziert, 7× Runde 5 -- exakter Alpha-Beta-Solver (round5.rs), nicht netz-oracle-bewertet
- KI: nicht bewertete Züge -- 8× Runde 5 -- exakter Alpha-Beta-Solver (round5.rs), nicht netz-oracle-bewertet

`Δwin%` = (Oracle-Top-Q − Q der gespielten Aktion) × 100, aus 5000-Sim-Netzsuche (v16_best) am Zustand VOR dem Zug. 0.0 = die gespielte Aktion WAR der Oracle-Top-Zug.

## (b) Groesste Abweichungen von der Oracle-Empfehlung

### Spieler 1

- **Runde 3, Zug #57** (stone): gespielt `🌙 Spieler 1: 1 (1)× türkis von F2 → Reihe 5 [5/5]` (Rang 7/11, Q=0.113) vs. Oracle-Top `2× Stein rot vom Mondpool → Reihe 1 [1/1] (+1 Strafleiste)` (Q=0.235) -- **Δwin% = 12.2**
- **Runde 1, Zug #14** (stone): gespielt `🌙 Spieler 1: 4 (1+1+1+1)× rot von F2, F3, F4, GF → Reihe 5 [4/5]` (Rang 11/12, Q=0.222) vs. Oracle-Top `2× Stein schwarz vom Mondpool → Reihe 4 [2/4]` (Q=0.333) -- **Δwin% = 11.1**
- **Runde 3, Zug #59** (stone): gespielt `🌙 Spieler 1: 1 (1)× schwarz von F2 → Reihe 3 [3/3]` (Rang 5/10, Q=0.092) vs. Oracle-Top `Stapel: verdeckt ziehen` (Q=0.160) -- **Δwin% = 6.8**

### KI

- **Runde 4, Zug #69** (stone): gespielt `☀️  KI: 3× schwarz von F4 → Reihe 2 [2/2] (+1 Strafleiste)` (Rang 4/78, Q=0.772) vs. Oracle-Top `Kuppel #12 → (2,2)` (Q=0.820) -- **Δwin% = 4.8**
- **Runde 4, Zug #81** (dome_display): gespielt `KI: Kachel 5 → Slot (2,2) rot=180° [Plättchen 1/2]` (Rang 8/9, Q=0.853) vs. Oracle-Top `Bonuschip F4` (Q=0.900) -- **Δwin% = 4.7**
- **Runde 4, Zug #73** (stone): gespielt `🌙 KI: 1 (1)× blau von F3 → Reihe 5 [4/5]` (Rang 7/25, Q=0.818) vs. Oracle-Top `Kuppel #10 → (2,2)` (Q=0.855) -- **Δwin% = 3.7**

## (c) Wendepunkte (groesste Win%-Sprünge)

Win%-Schätzung ist immer aus Sicht von **Spieler 1** normiert (Oracle-`root_value` ist Win% des jeweils ziehenden Spielers am Zustand VOR dem Zug; für Zug-Perspektive KI wird 100−root_value gebildet).

| von (Zug#/Runde) | nach (Zug#/Runde) | Δ Win% (Spieler 1) |
|---|---|---|
| #44 (R2, KI zieht, 9.4%) | #45 (R3, Spieler 1 zieht, 26.0%) | +16.6 pp |
| #45 (R3, Spieler 1 zieht, 26.0%) | #46 (R3, KI zieht, 12.8%) | -13.2 pp |
| #47 (R3, Spieler 1 zieht, 22.6%) | #48 (R3, KI zieht, 9.5%) | -13.0 pp |
| #75 (R4, KI zieht, 23.4%) | #76 (R4, Spieler 1 zieht, 10.7%) | -12.7 pp |
| #5 (R1, Spieler 1 zieht, 44.4%) | #6 (R1, KI zieht, 33.3%) | -11.2 pp |

## (d) Die Wertungsplatten-Story

Punktestand am Ende jeder Runde (reine Text-Extraktion aus dem Log -- unabhaengig vom Replay-Fortschritt, siehe Grenzen):

| Runde | Spieler 1 | KI |
|---|---|---|
| 1 | 5 | – |
| 2 | 8 | 21 |
| 3 | 16 | 35 |
| 4 | 30 | 48 |
| 5 | – | 43 |

(Rohpunktestand direkt vor der Endwertung, aus der `# SPIELENDE:`-Kopfzeile: Spieler 1 44 : 43 KI -- fehlende "–"-Werte oben bedeuten lediglich 0 Pkt Strafe in dieser Runde, keine Lücke.)

Endwertung (Wertungsplatten-Bonus):

- **Spieler 1**: +10 Pkt -> Gesamt 54 Pkt
  - ↔️ Horizontale Reihen: 0 Pkt
  - ↕️ Vertikale Reihen: 0 Pkt
  - ↗️ Diagonale Reihen: 10 Pkt
- **KI**: +0 Pkt -> Gesamt 43 Pkt
  - ↔️ Horizontale Reihen: 0 Pkt
  - ↕️ Vertikale Reihen: 0 Pkt
  - ↗️ Diagonale Reihen: 0 Pkt

Vor der Endwertung stand es 44 : 43; nach dem Wertungsplatten-Bonus 54 : 43.

Win%-Verlauf (aus Spieler 1-Sicht) über den oracle-bewerteten Teil der Partie:

| Zug# | Runde | zieht | Win% (Spieler 1) |
|---|---|---|---|
| 1 | 1 | Spieler 1 | 48.7% |
| 2 | 1 | KI | 45.4% |
| 3 | 1 | Spieler 1 | 45.9% |
| 4 | 1 | KI | 40.3% |
| 5 | 1 | Spieler 1 | 44.4% |
| 6 | 1 | KI | 33.3% |
| 7 | 1 | Spieler 1 | 40.3% |
| 8 | 1 | Spieler 1 | 39.3% |
| 9 | 1 | KI | 30.6% |
| 10 | 1 | Spieler 1 | 34.7% |
| 11 | 1 | KI | 28.8% |
| 12 | 1 | Spieler 1 | 31.7% |
| 13 | 1 | KI | 30.3% |
| 14 | 1 | Spieler 1 | 30.9% |
| 15 | 1 | KI | 28.2% |
| 16 | 1 | Spieler 1 | 26.8% |
| 17 | 1 | KI | 27.1% |
| 18 | 1 | Spieler 1 | 25.8% |
| 19 | 1 | KI | 28.0% |
| 20 | 1 | Spieler 1 | 22.9% |
| 21 | 1 | Spieler 1 | 26.6% |
| 22 | 2 | Spieler 1 | 24.4% |
| 23 | 2 | KI | 21.9% |
| 24 | 2 | Spieler 1 | 24.3% |
| 25 | 2 | KI | 22.0% |
| 26 | 2 | Spieler 1 | 28.1% |
| 27 | 2 | KI | 21.9% |
| 28 | 2 | KI | 20.3% |
| 29 | 2 | Spieler 1 | 25.8% |
| 30 | 2 | KI | 15.7% |
| 31 | 2 | Spieler 1 | 19.6% |
| 32 | 2 | KI | 14.8% |
| 33 | 2 | Spieler 1 | 16.3% |
| 34 | 2 | KI | 17.9% |
| 35 | 2 | Spieler 1 | 15.4% |
| 36 | 2 | KI | 13.1% |
| 37 | 2 | Spieler 1 | 14.3% |
| 38 | 2 | KI | 11.8% |
| 39 | 2 | Spieler 1 | 15.1% |
| 40 | 2 | KI | 9.7% |
| 41 | 2 | Spieler 1 | 13.1% |
| 42 | 2 | KI | 11.3% |
| 43 | 2 | Spieler 1 | 15.0% |
| 44 | 2 | KI | 9.4% |
| 45 | 3 | Spieler 1 | 26.0% |
| 46 | 3 | KI | 12.8% |
| 47 | 3 | Spieler 1 | 22.6% |
| 48 | 3 | KI | 9.5% |
| 49 | 3 | Spieler 1 | 14.0% |
| 50 | 3 | KI | 10.4% |
| 51 | 3 | Spieler 1 | 15.5% |
| 52 | 3 | KI | 8.5% |
| 53 | 3 | Spieler 1 | 13.7% |
| 54 | 3 | KI | 8.1% |
| 55 | 3 | Spieler 1 | 13.4% |
| 56 | 3 | KI | 9.6% |
| 57 | 3 | Spieler 1 | 17.8% |
| 58 | 3 | KI | 7.4% |
| 59 | 3 | Spieler 1 | 12.0% |
| 60 | 3 | KI | 5.2% |
| 61 | 3 | Spieler 1 | 8.6% |
| 62 | 3 | KI | 4.8% |
| 63 | 3 | Spieler 1 | 12.5% |
| 64 | 3 | KI | 4.3% |
| 65 | 3 | Spieler 1 | 12.5% |
| 66 | 3 | Spieler 1 | 17.4% |
| 67 | 3 | Spieler 1 | 14.1% |
| 68 | 4 | Spieler 1 | 14.1% |
| 69 | 4 | KI | 21.9% |
| 70 | 4 | Spieler 1 | 21.1% |
| 71 | 4 | KI | 18.8% |
| 72 | 4 | Spieler 1 | 14.9% |
| 73 | 4 | KI | 16.8% |
| 74 | 4 | Spieler 1 | 21.5% |
| 75 | 4 | KI | 23.4% |
| 76 | 4 | Spieler 1 | 10.7% |
| 77 | 4 | KI | 14.9% |
| 78 | 4 | Spieler 1 | 17.5% |
| 79 | 4 | KI | 13.7% |
| 80 | 4 | Spieler 1 | 15.0% |
| 81 | 4 | KI | 11.4% |
| 82 | 4 | Spieler 1 | 7.5% |
| 83 | 4 | KI | 7.6% |
| 84 | 4 | Spieler 1 | 5.6% |
| 85 | 4 | KI | 6.1% |
| 86 | 4 | KI | 6.0% |
| 87 | 4 | Spieler 1 | 6.5% |

Das Oracle sah Spieler 1 zu Beginn der bewerteten Zuege bei **48.7%** und am Ende von Runde 4 bei **6.5%** Gewinnwahrscheinlichkeit (jeweils aus Sicht des ziehenden Spielers umgerechnet). Runde 5 (Endwertung inkl. Wertungsplatten) lief ausserhalb dieser Betrachtung über den exakten Solver.

## Grenzen und Auffälligkeiten (ehrlich dokumentiert)

- **Determinisierung**: `net_search_state_json` rekonstruiert verdeckte Information (Beutel/Turm/Kuppelstapel/Bonuschip-Pool) aus Zählern/Masken und mischt sie NEU mit einem festen, aus dem Zugindex abgeleiteten Seed -- das Oracle sieht also, wie ein echter Spieler, KEINE verdeckte Information, nur eine andere zufällige Mischung als das tatsächliche Spiel. Ein einzelner 5000-Sim-Lauf ist dadurch eine starke, aber keine perfekte Schätzung (siehe Task #89 fuer die empirisch verifizierte Rekonstruktions-Genauigkeit).
- **Runde 5** läuft über den exakten Alpha-Beta-Solver (kein Informationsgehalt mehr, siehe `round5.rs`) und wurde bewusst NICHT netz-oracle-bewertet (andere Skala/Semantik als die PUCT-Netzsuche der Runden 1-4).
- **Kuppel-Rotation**: die Rotationswahl (Stufe 2 nach Kachel+Slot) wird NICHT separat oracle-bewertet -- `apply_dome`/`apply_dome_stack_choose` bleiben nach aussen atomar, die PendingDomeChoice-Zwischenzustände haben laut Task #89 Serialisierungs-Näherungen.
- **`root_value`-Interpretation**: als Win%-Schätzung des jeweils ziehenden Spielers am Zustand VOR seinem Zug interpretiert (Projekt-Konvention); keine unabhängig re-kalibrierte Wahrscheinlichkeit.
- **Oracle-Zug-Zuordnung** erfolgt über eine geparste Kurzbeschreibung (Farbe/Quelle/Zielreihe bzw. Kachel/Slot/Fabrik) gegen die von der Suche gelabelten Kandidaten; bei der Stapel-Wahl (`choose_draw_stack_slot`) fehlt die Kachel-ID im Label, ein `_(Match evtl. mehrdeutig)_`-Hinweis markiert das im Text.
