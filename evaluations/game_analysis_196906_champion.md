# Spielanalyse: game_20260819_153857_seed196906.log

Erzeugt von `tools/analyze_game_log.py` (Commit `0f67b3e`), Laufzeit 182s.

- Seed: 196906, Startspieler: Spieler 1, KI-Spieler: KI (v21_2d_brierbest, 400 Sims)
## (a) Zusammenfassung

Endstand (aus dem Log-Text): **Spieler 1 78 : 72 KI**

Replay-Kreuzvalidierung: jede einzelne erzeugte Log-Zeile (`log_since`) wurde exakt (String-Gleichheit inkl. `[Rn] `-Präfix) gegen die Original-Logdatei geprüft (alle 319 Zeilen bestehen).

Aufloesung der Stein-Zuege: **62 ueber die Aktions-ID** (`#a`-Zeilen im Log, PREREG_action_id_logging.md), **0 ueber den Textweg** (Rueckfall fuer Logs ohne IDs).

| Spieler | oracle-bewertete Züge | Ø Δwin% zum Oracle-Top | Top-1-Treffer | Top-3-Treffer | nicht bewertet |
|---|---|---|---|---|---|
| Spieler 1 | 36 | 5.3 pp | 8/36 (22%) | 18/36 (50%) | 18 |
| KI | 40 | 1.0 pp | 20/40 (50%) | 30/40 (75%) | 8 |

- Spieler 1: nicht bewertete Züge -- 10× gespielte Aktion nicht unter Oracle-Kandidaten identifiziert, 8× Runde 5 -- exakter Alpha-Beta-Solver (round5.rs), nicht netz-oracle-bewertet
- KI: nicht bewertete Züge -- 8× Runde 5 -- exakter Alpha-Beta-Solver (round5.rs), nicht netz-oracle-bewertet

`Δwin%` = (Oracle-Top-Q − Q der gespielten Aktion) × 100, aus 5000-Sim-Netzsuche (v16_best) am Zustand VOR dem Zug. 0.0 = die gespielte Aktion WAR der Oracle-Top-Zug.

## (b) Groesste Abweichungen von der Oracle-Empfehlung

### Spieler 1

- **Runde 2, Zug #36** (bonus_chip): gespielt `Spieler 1: Bonusplättchen von Fabrik 2 genommen [1/2 diese Runde]` (Rang 3/6, Q=0.349) vs. Oracle-Top `Stapel: verdeckt ziehen` (Q=0.536) -- **Δwin% = 18.7**
- **Runde 2, Zug #39** (dome_stack): gespielt `Spieler 1: Kachel 5 → Slot (2,1) rot=0° [Plättchen 2/2]` (Rang 6/6, Q=0.272) vs. Oracle-Top `Stapel → (0,2)` (Q=0.445) -- **Δwin% = 17.3**
- **Runde 2, Zug #34** (stone): gespielt `🌙 Spieler 1: 3 (1+1+1)× gelb von F1, F2, F4 → Reihe 6 [3/6]` (Rang 3/5, Q=0.358) vs. Oracle-Top `Stapel: verdeckt ziehen` (Q=0.511) -- **Δwin% = 15.3**

### KI

- **Runde 4, Zug #65** (stone): gespielt `☀️  KI: 1× gelb von F1 → Reihe 1 [1/1]` (Rang 11/112, Q=0.586) vs. Oracle-Top `1× Stein rot von F3 → Reihe 1 [1/1]` (Q=0.639) -- **Δwin% = 5.3** _(Match evtl. mehrdeutig)_
- **Runde 4, Zug #71** (stone): gespielt `🌙 KI: 1 (1)× gelb von F3 → Reihe 3 [1/3]` (Rang 14/27, Q=0.928) vs. Oracle-Top `3× Stein blau vom Mondpool → Reihe 3 [3/3]` (Q=0.976) -- **Δwin% = 4.8**
- **Runde 3, Zug #51** (stone): gespielt `🌙 KI: 3 (1+1+1)× blau von F1, F2, F3 → Reihe 4 [3/4]` (Rang 4/17, Q=0.568) vs. Oracle-Top `3× Stein schwarz von GF → Reihe 3 [3/3]` (Q=0.605) -- **Δwin% = 3.8**

## (c) Wendepunkte (groesste Win%-Sprünge)

Win%-Schätzung ist immer aus Sicht von **Spieler 1** normiert (Oracle-`root_value` ist Win% des jeweils ziehenden Spielers am Zustand VOR dem Zug; für Zug-Perspektive KI wird 100−root_value gebildet).

| von (Zug#/Runde) | nach (Zug#/Runde) | Δ Win% (Spieler 1) |
|---|---|---|
| #66 (R4, Spieler 1 zieht, 41.0%) | #67 (R4, KI zieht, 19.8%) | -21.2 pp |
| #26 (R2, Spieler 1 zieht, 52.8%) | #27 (R2, KI zieht, 33.0%) | -19.9 pp |
| #64 (R4, Spieler 1 zieht, 22.3%) | #65 (R4, KI zieht, 39.9%) | +17.6 pp |
| #25 (R2, KI zieht, 36.6%) | #26 (R2, Spieler 1 zieht, 52.8%) | +16.2 pp |
| #39 (R2, Spieler 1 zieht, 38.6%) | #40 (R2, KI zieht, 23.5%) | -15.0 pp |

## (d) Die Wertungsplatten-Story

Punktestand am Ende jeder Runde (reine Text-Extraktion aus dem Log -- unabhaengig vom Replay-Fortschritt, siehe Grenzen):

| Runde | Spieler 1 | KI |
|---|---|---|
| 1 | 7 | – |
| 2 | 14 | 15 |
| 3 | 26 | – |
| 4 | 39 | – |
| 5 | 54 | 58 |

(Rohpunktestand direkt vor der Endwertung, aus der `# SPIELENDE:`-Kopfzeile: Spieler 1 54 : 58 KI -- fehlende "–"-Werte oben bedeuten lediglich 0 Pkt Strafe in dieser Runde, keine Lücke.)

Endwertung (Wertungsplatten-Bonus):

- **Spieler 1**: +24 Pkt -> Gesamt 78 Pkt
  - 🌈 Mehrfarbige Felder: 0 Pkt
  - ↕️ Vertikale Reihen: 14 Pkt
  - ↗️ Diagonale Reihen: 10 Pkt
- **KI**: +14 Pkt -> Gesamt 72 Pkt
  - 🌈 Mehrfarbige Felder: 14 Pkt
  - ↕️ Vertikale Reihen: 0 Pkt
  - ↗️ Diagonale Reihen: 0 Pkt

Vor der Endwertung stand es 54 : 58; nach dem Wertungsplatten-Bonus 78 : 72.
**Die Wertungsplatten haben das Ergebnis gedreht**: ohne Endwertung hätte KI gewonnen, nach der Endwertung gewinnt Spieler 1.

Win%-Verlauf (aus Spieler 1-Sicht) über den oracle-bewerteten Teil der Partie:

| Zug# | Runde | zieht | Win% (Spieler 1) |
|---|---|---|---|
| 1 | 1 | Spieler 1 | 49.1% |
| 2 | 1 | KI | 46.7% |
| 3 | 1 | Spieler 1 | 46.9% |
| 4 | 1 | KI | 44.6% |
| 5 | 1 | Spieler 1 | 47.5% |
| 6 | 1 | KI | 42.4% |
| 7 | 1 | KI | 40.9% |
| 8 | 1 | Spieler 1 | 44.8% |
| 9 | 1 | KI | 40.2% |
| 10 | 1 | Spieler 1 | 47.5% |
| 11 | 1 | KI | 37.8% |
| 12 | 1 | Spieler 1 | 44.1% |
| 13 | 1 | KI | 37.7% |
| 14 | 1 | Spieler 1 | 38.0% |
| 15 | 1 | KI | 36.2% |
| 16 | 1 | Spieler 1 | 37.5% |
| 17 | 1 | KI | 35.2% |
| 18 | 1 | Spieler 1 | 35.4% |
| 19 | 1 | KI | 34.7% |
| 20 | 1 | Spieler 1 | 36.8% |
| 21 | 1 | Spieler 1 | 35.0% |
| 22 | 2 | Spieler 1 | 49.1% |
| 23 | 2 | KI | 39.3% |
| 24 | 2 | Spieler 1 | 49.7% |
| 25 | 2 | KI | 36.6% |
| 26 | 2 | Spieler 1 | 52.8% |
| 27 | 2 | KI | 33.0% |
| 28 | 2 | Spieler 1 | 47.8% |
| 29 | 2 | KI | 36.5% |
| 30 | 2 | Spieler 1 | 42.6% |
| 31 | 2 | KI | 35.6% |
| 32 | 2 | Spieler 1 | 38.9% |
| 33 | 2 | KI | 38.5% |
| 34 | 2 | Spieler 1 | 44.1% |
| 35 | 2 | KI | 32.6% |
| 36 | 2 | Spieler 1 | 41.5% |
| 37 | 2 | KI | 30.2% |
| 38 | 2 | Spieler 1 | 37.0% |
| 39 | 2 | Spieler 1 | 38.6% |
| 40 | 2 | KI | 23.5% |
| 41 | 2 | Spieler 1 | 20.6% |
| 42 | 2 | Spieler 1 | 18.2% |
| 43 | 3 | KI | 31.1% |
| 44 | 3 | Spieler 1 | 33.7% |
| 45 | 3 | KI | 36.6% |
| 46 | 3 | Spieler 1 | 37.6% |
| 47 | 3 | KI | 34.2% |
| 48 | 3 | Spieler 1 | 40.5% |
| 49 | 3 | KI | 41.6% |
| 50 | 3 | Spieler 1 | 48.5% |
| 51 | 3 | KI | 43.4% |
| 52 | 3 | Spieler 1 | 41.7% |
| 53 | 3 | KI | 27.1% |
| 54 | 3 | Spieler 1 | 19.5% |
| 55 | 3 | KI | 16.0% |
| 56 | 3 | Spieler 1 | 22.2% |
| 57 | 3 | KI | 12.6% |
| 58 | 3 | Spieler 1 | 19.0% |
| 59 | 3 | Spieler 1 | 15.5% |
| 60 | 3 | KI | 11.3% |
| 61 | 3 | Spieler 1 | 8.1% |
| 62 | 3 | Spieler 1 | 7.4% |
| 63 | 3 | Spieler 1 | 7.4% |
| 64 | 4 | Spieler 1 | 22.3% |
| 65 | 4 | KI | 39.9% |
| 66 | 4 | Spieler 1 | 41.0% |
| 67 | 4 | KI | 19.8% |
| 68 | 4 | Spieler 1 | 28.0% |
| 69 | 4 | KI | 13.2% |
| 70 | 4 | Spieler 1 | 20.3% |
| 71 | 4 | KI | 5.5% |
| 72 | 4 | Spieler 1 | 16.5% |
| 73 | 4 | KI | 6.5% |
| 74 | 4 | Spieler 1 | 11.9% |
| 75 | 4 | KI | 4.1% |
| 76 | 4 | Spieler 1 | 8.8% |
| 77 | 4 | KI | 3.3% |
| 78 | 4 | Spieler 1 | 6.5% |
| 79 | 4 | KI | 2.2% |
| 80 | 4 | Spieler 1 | 4.6% |
| 81 | 4 | KI | 2.1% |
| 82 | 4 | Spieler 1 | 2.7% |
| 83 | 4 | KI | 2.9% |
| 84 | 4 | Spieler 1 | 3.9% |
| 85 | 4 | KI | 0.9% |
| 86 | 4 | KI | 0.9% |

Das Oracle sah Spieler 1 zu Beginn der bewerteten Zuege bei **49.1%** und am Ende von Runde 4 bei **0.9%** Gewinnwahrscheinlichkeit (jeweils aus Sicht des ziehenden Spielers umgerechnet). Runde 5 (Endwertung inkl. Wertungsplatten) lief ausserhalb dieser Betrachtung über den exakten Solver.

## Grenzen und Auffälligkeiten (ehrlich dokumentiert)

- **Determinisierung**: `net_search_state_json` rekonstruiert verdeckte Information (Beutel/Turm/Kuppelstapel/Bonuschip-Pool) aus Zählern/Masken und mischt sie NEU mit einem festen, aus dem Zugindex abgeleiteten Seed -- das Oracle sieht also, wie ein echter Spieler, KEINE verdeckte Information, nur eine andere zufällige Mischung als das tatsächliche Spiel. Ein einzelner 5000-Sim-Lauf ist dadurch eine starke, aber keine perfekte Schätzung (siehe Task #89 fuer die empirisch verifizierte Rekonstruktions-Genauigkeit).
- **Runde 5** läuft über den exakten Alpha-Beta-Solver (kein Informationsgehalt mehr, siehe `round5.rs`) und wurde bewusst NICHT netz-oracle-bewertet (andere Skala/Semantik als die PUCT-Netzsuche der Runden 1-4).
- **Kuppel-Rotation**: die Rotationswahl (Stufe 2 nach Kachel+Slot) wird NICHT separat oracle-bewertet -- `apply_dome`/`apply_dome_stack_choose` bleiben nach aussen atomar, die PendingDomeChoice-Zwischenzustände haben laut Task #89 Serialisierungs-Näherungen.
- **`root_value`-Interpretation**: als Win%-Schätzung des jeweils ziehenden Spielers am Zustand VOR seinem Zug interpretiert (Projekt-Konvention); keine unabhängig re-kalibrierte Wahrscheinlichkeit.
- **Oracle-Zug-Zuordnung** erfolgt über eine geparste Kurzbeschreibung (Farbe/Quelle/Zielreihe bzw. Kachel/Slot/Fabrik) gegen die von der Suche gelabelten Kandidaten; bei der Stapel-Wahl (`choose_draw_stack_slot`) fehlt die Kachel-ID im Label, ein `_(Match evtl. mehrdeutig)_`-Hinweis markiert das im Text.
