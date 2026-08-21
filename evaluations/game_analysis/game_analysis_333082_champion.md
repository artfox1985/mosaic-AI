# Spielanalyse: game_20260818_222531_seed333082.log

Erzeugt von `tools/analyze_game_log.py` (Commit `0f67b3e`), Laufzeit 202s.

- Seed: 333082, Startspieler: Spieler 1, KI-Spieler: KI (v21_2d_brierbest, 400 Sims)
## (a) Zusammenfassung

Endstand (aus dem Log-Text): **Spieler 1 80 : 80 KI**

Replay-Kreuzvalidierung: jede einzelne erzeugte Log-Zeile (`log_since`) wurde exakt (String-Gleichheit inkl. `[Rn] `-Präfix) gegen die Original-Logdatei geprüft (alle 332 Zeilen bestehen).

Aufloesung der Stein-Zuege: **66 ueber die Aktions-ID** (`#a`-Zeilen im Log, PREREG_action_id_logging.md), **0 ueber den Textweg** (Rueckfall fuer Logs ohne IDs).

| Spieler | oracle-bewertete Züge | Ø Δwin% zum Oracle-Top | Top-1-Treffer | Top-3-Treffer | nicht bewertet |
|---|---|---|---|---|---|
| Spieler 1 | 37 | 3.4 pp | 11/37 (30%) | 18/37 (49%) | 17 |
| KI | 42 | 0.4 pp | 22/42 (52%) | 33/42 (79%) | 10 |

- Spieler 1: nicht bewertete Züge -- 9× gespielte Aktion nicht unter Oracle-Kandidaten identifiziert, 8× Runde 5 -- exakter Alpha-Beta-Solver (round5.rs), nicht netz-oracle-bewertet
- KI: nicht bewertete Züge -- 10× Runde 5 -- exakter Alpha-Beta-Solver (round5.rs), nicht netz-oracle-bewertet

`Δwin%` = (Oracle-Top-Q − Q der gespielten Aktion) × 100, aus 5000-Sim-Netzsuche (v16_best) am Zustand VOR dem Zug. 0.0 = die gespielte Aktion WAR der Oracle-Top-Zug.

## (b) Groesste Abweichungen von der Oracle-Empfehlung

### Spieler 1

- **Runde 2, Zug #39** (stone): gespielt `🌙 Spieler 1: 1 (1)× rot von F3 → Reihe 5 [4/5]` (Rang 9/11, Q=0.417) vs. Oracle-Top `Kuppel #12 → (0,1)` (Q=0.566) -- **Δwin% = 14.9**
- **Runde 2, Zug #33** (stone): gespielt `🌙 Spieler 1: 2 (1+1)× blau von F1, F4 → Reihe 3 [2/3]` (Rang 14/20, Q=0.406) vs. Oracle-Top `2× Stein gelb vom Mondpool → Reihe 1 [1/1] (+1 Strafleiste)` (Q=0.516) -- **Δwin% = 11.0**
- **Runde 3, Zug #59** (bonus_chip): gespielt `Spieler 1: Bonusplättchen von Fabrik 4 genommen [2/2 diese Runde]` (Rang 10/11, Q=0.163) vs. Oracle-Top `Kuppel #10 → (0,2)` (Q=0.274) -- **Δwin% = 11.0**

### KI

- **Runde 1, Zug #10** (stone): gespielt `🌙 KI: 1 (1)× schwarz von F2 → Reihe 3 [1/3]` (Rang 11/21, Q=0.561) vs. Oracle-Top `1× Stein gelb vom Mondpool → Reihe 3 [1/3]` (Q=0.598) -- **Δwin% = 3.8**
- **Runde 4, Zug #72** (stone): gespielt `🌙 KI: 3 (1+1+1)× türkis von F1, F2, F4 → Reihe 3 [3/3]` (Rang 13/28, Q=0.952) vs. Oracle-Top `2× Stein gelb von F3 → Reihe 6 [5/6]` (Q=0.981) -- **Δwin% = 2.9**
- **Runde 1, Zug #4** (stone): gespielt `☀️  KI: 2× blau von F2 → Reihe 2 [2/2]` (Rang 4/78, Q=0.556) vs. Oracle-Top `2× Stein blau vom Mondpool → Reihe 2 [2/2]` (Q=0.577) -- **Δwin% = 2.1**

## (c) Wendepunkte (groesste Win%-Sprünge)

Win%-Schätzung ist immer aus Sicht von **Spieler 1** normiert (Oracle-`root_value` ist Win% des jeweils ziehenden Spielers am Zustand VOR dem Zug; für Zug-Perspektive KI wird 100−root_value gebildet).

| von (Zug#/Runde) | nach (Zug#/Runde) | Δ Win% (Spieler 1) |
|---|---|---|
| #53 (R3, Spieler 1 zieht, 38.6%) | #54 (R3, KI zieht, 10.0%) | -28.6 pp |
| #51 (R3, Spieler 1 zieht, 38.8%) | #52 (R3, KI zieht, 13.8%) | -25.0 pp |
| #52 (R3, KI zieht, 13.8%) | #53 (R3, Spieler 1 zieht, 38.6%) | +24.8 pp |
| #39 (R2, Spieler 1 zieht, 52.4%) | #40 (R2, KI zieht, 27.7%) | -24.7 pp |
| #50 (R3, KI zieht, 15.3%) | #51 (R3, Spieler 1 zieht, 38.8%) | +23.5 pp |

## (d) Die Wertungsplatten-Story

Punktestand am Ende jeder Runde (reine Text-Extraktion aus dem Log -- unabhaengig vom Replay-Fortschritt, siehe Grenzen):

| Runde | Spieler 1 | KI |
|---|---|---|
| 1 | 9 | – |
| 2 | 9 | 14 |
| 3 | 26 | 32 |
| 4 | 41 | – |
| 5 | 66 | 80 |

(Rohpunktestand direkt vor der Endwertung, aus der `# SPIELENDE:`-Kopfzeile: Spieler 1 66 : 80 KI -- fehlende "–"-Werte oben bedeuten lediglich 0 Pkt Strafe in dieser Runde, keine Lücke.)

Endwertung (Wertungsplatten-Bonus):

- **Spieler 1**: +14 Pkt -> Gesamt 80 Pkt
  - 🎨 Farbenreiche Reihen: 0 Pkt
  - 🌈 Mehrfarbige Felder: 0 Pkt
  - ↕️ Vertikale Reihen: 14 Pkt
- **KI**: +0 Pkt -> Gesamt 80 Pkt
  - 🎨 Farbenreiche Reihen: 0 Pkt
  - 🌈 Mehrfarbige Felder: 0 Pkt
  - ↕️ Vertikale Reihen: 0 Pkt

Vor der Endwertung stand es 66 : 80; nach dem Wertungsplatten-Bonus 80 : 80.

Win%-Verlauf (aus Spieler 1-Sicht) über den oracle-bewerteten Teil der Partie:

| Zug# | Runde | zieht | Win% (Spieler 1) |
|---|---|---|---|
| 1 | 1 | Spieler 1 | 55.3% |
| 2 | 1 | KI | 45.5% |
| 3 | 1 | Spieler 1 | 51.3% |
| 4 | 1 | KI | 44.6% |
| 5 | 1 | Spieler 1 | 52.7% |
| 6 | 1 | KI | 45.1% |
| 7 | 1 | Spieler 1 | 54.0% |
| 8 | 1 | KI | 43.8% |
| 9 | 1 | Spieler 1 | 49.1% |
| 10 | 1 | KI | 43.9% |
| 11 | 1 | Spieler 1 | 47.1% |
| 12 | 1 | Spieler 1 | 45.5% |
| 13 | 1 | KI | 41.9% |
| 14 | 1 | Spieler 1 | 45.6% |
| 15 | 1 | KI | 42.0% |
| 16 | 1 | Spieler 1 | 48.6% |
| 17 | 1 | KI | 41.1% |
| 18 | 1 | Spieler 1 | 49.6% |
| 19 | 1 | KI | 39.2% |
| 20 | 1 | Spieler 1 | 49.2% |
| 21 | 1 | KI | 39.9% |
| 22 | 1 | KI | 39.4% |
| 23 | 2 | Spieler 1 | 54.9% |
| 24 | 2 | KI | 45.5% |
| 25 | 2 | Spieler 1 | 50.8% |
| 26 | 2 | KI | 42.6% |
| 27 | 2 | Spieler 1 | 52.2% |
| 28 | 2 | KI | 37.1% |
| 29 | 2 | Spieler 1 | 49.3% |
| 30 | 2 | KI | 34.6% |
| 31 | 2 | Spieler 1 | 47.1% |
| 32 | 2 | KI | 30.8% |
| 33 | 2 | Spieler 1 | 47.2% |
| 34 | 2 | KI | 30.4% |
| 35 | 2 | Spieler 1 | 47.4% |
| 36 | 2 | KI | 30.6% |
| 37 | 2 | Spieler 1 | 50.4% |
| 38 | 2 | KI | 32.2% |
| 39 | 2 | Spieler 1 | 52.4% |
| 40 | 2 | KI | 27.7% |
| 41 | 2 | Spieler 1 | 42.5% |
| 42 | 2 | KI | 28.2% |
| 43 | 2 | Spieler 1 | 39.4% |
| 44 | 2 | Spieler 1 | 37.7% |
| 45 | 3 | Spieler 1 | 18.3% |
| 46 | 3 | KI | 9.2% |
| 47 | 3 | Spieler 1 | 22.0% |
| 48 | 3 | KI | 13.0% |
| 49 | 3 | Spieler 1 | 33.8% |
| 50 | 3 | KI | 15.3% |
| 51 | 3 | Spieler 1 | 38.8% |
| 52 | 3 | KI | 13.8% |
| 53 | 3 | Spieler 1 | 38.6% |
| 54 | 3 | KI | 10.0% |
| 55 | 3 | Spieler 1 | 27.3% |
| 56 | 3 | KI | 8.3% |
| 57 | 3 | Spieler 1 | 26.0% |
| 58 | 3 | KI | 7.8% |
| 59 | 3 | Spieler 1 | 25.1% |
| 60 | 3 | KI | 7.2% |
| 61 | 3 | Spieler 1 | 21.2% |
| 62 | 3 | KI | 7.4% |
| 63 | 3 | Spieler 1 | 20.4% |
| 64 | 3 | Spieler 1 | 18.7% |
| 65 | 3 | KI | 5.2% |
| 66 | 3 | Spieler 1 | 17.1% |
| 67 | 4 | Spieler 1 | 15.3% |
| 68 | 4 | KI | 4.1% |
| 69 | 4 | Spieler 1 | 12.1% |
| 70 | 4 | KI | 3.9% |
| 71 | 4 | Spieler 1 | 9.6% |
| 72 | 4 | KI | 3.7% |
| 73 | 4 | Spieler 1 | 6.0% |
| 74 | 4 | KI | 3.1% |
| 75 | 4 | Spieler 1 | 4.2% |
| 76 | 4 | KI | 3.7% |
| 77 | 4 | Spieler 1 | 2.9% |
| 78 | 4 | KI | 1.6% |
| 79 | 4 | Spieler 1 | 4.8% |
| 80 | 4 | KI | 2.0% |
| 81 | 4 | Spieler 1 | 4.3% |
| 82 | 4 | KI | 1.7% |
| 83 | 4 | Spieler 1 | 1.2% |
| 84 | 4 | KI | 0.7% |
| 85 | 4 | KI | 0.3% |
| 86 | 4 | Spieler 1 | 0.7% |
| 87 | 4 | KI | 0.2% |
| 88 | 4 | Spieler 1 | 0.1% |

Das Oracle sah Spieler 1 zu Beginn der bewerteten Zuege bei **55.3%** und am Ende von Runde 4 bei **0.1%** Gewinnwahrscheinlichkeit (jeweils aus Sicht des ziehenden Spielers umgerechnet). Runde 5 (Endwertung inkl. Wertungsplatten) lief ausserhalb dieser Betrachtung über den exakten Solver.

## Grenzen und Auffälligkeiten (ehrlich dokumentiert)

- **Determinisierung**: `net_search_state_json` rekonstruiert verdeckte Information (Beutel/Turm/Kuppelstapel/Bonuschip-Pool) aus Zählern/Masken und mischt sie NEU mit einem festen, aus dem Zugindex abgeleiteten Seed -- das Oracle sieht also, wie ein echter Spieler, KEINE verdeckte Information, nur eine andere zufällige Mischung als das tatsächliche Spiel. Ein einzelner 5000-Sim-Lauf ist dadurch eine starke, aber keine perfekte Schätzung (siehe Task #89 fuer die empirisch verifizierte Rekonstruktions-Genauigkeit).
- **Runde 5** läuft über den exakten Alpha-Beta-Solver (kein Informationsgehalt mehr, siehe `round5.rs`) und wurde bewusst NICHT netz-oracle-bewertet (andere Skala/Semantik als die PUCT-Netzsuche der Runden 1-4).
- **Kuppel-Rotation**: die Rotationswahl (Stufe 2 nach Kachel+Slot) wird NICHT separat oracle-bewertet -- `apply_dome`/`apply_dome_stack_choose` bleiben nach aussen atomar, die PendingDomeChoice-Zwischenzustände haben laut Task #89 Serialisierungs-Näherungen.
- **`root_value`-Interpretation**: als Win%-Schätzung des jeweils ziehenden Spielers am Zustand VOR seinem Zug interpretiert (Projekt-Konvention); keine unabhängig re-kalibrierte Wahrscheinlichkeit.
- **Oracle-Zug-Zuordnung** erfolgt über eine geparste Kurzbeschreibung (Farbe/Quelle/Zielreihe bzw. Kachel/Slot/Fabrik) gegen die von der Suche gelabelten Kandidaten; bei der Stapel-Wahl (`choose_draw_stack_slot`) fehlt die Kachel-ID im Label, ein `_(Match evtl. mehrdeutig)_`-Hinweis markiert das im Text.
