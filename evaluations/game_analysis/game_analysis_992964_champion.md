# Spielanalyse: game_20260819_124709_seed992964.log

Erzeugt von `tools/analyze_game_log.py` (Commit `0f67b3e`), Laufzeit 204s.

- Seed: 992964, Startspieler: Spieler 1, KI-Spieler: KI (v21_2d_brierbest, 400 Sims)
## (a) Zusammenfassung

Endstand (aus dem Log-Text): **Spieler 1 74 : 45 KI**

Replay-Kreuzvalidierung: jede einzelne erzeugte Log-Zeile (`log_since`) wurde exakt (String-Gleichheit inkl. `[Rn] `-Präfix) gegen die Original-Logdatei geprüft (alle 336 Zeilen bestehen).

Aufloesung der Stein-Zuege: **68 ueber die Aktions-ID** (`#a`-Zeilen im Log, PREREG_action_id_logging.md), **0 ueber den Textweg** (Rueckfall fuer Logs ohne IDs).

| Spieler | oracle-bewertete Züge | Ø Δwin% zum Oracle-Top | Top-1-Treffer | Top-3-Treffer | nicht bewertet |
|---|---|---|---|---|---|
| Spieler 1 | 37 | 5.2 pp | 8/37 (22%) | 17/37 (46%) | 19 |
| KI | 45 | 1.0 pp | 24/45 (53%) | 37/45 (82%) | 9 |

- Spieler 1: nicht bewertete Züge -- 11× gespielte Aktion nicht unter Oracle-Kandidaten identifiziert, 8× Runde 5 -- exakter Alpha-Beta-Solver (round5.rs), nicht netz-oracle-bewertet
- KI: nicht bewertete Züge -- 9× Runde 5 -- exakter Alpha-Beta-Solver (round5.rs), nicht netz-oracle-bewertet

`Δwin%` = (Oracle-Top-Q − Q der gespielten Aktion) × 100, aus 5000-Sim-Netzsuche (v16_best) am Zustand VOR dem Zug. 0.0 = die gespielte Aktion WAR der Oracle-Top-Zug.

## (b) Groesste Abweichungen von der Oracle-Empfehlung

### Spieler 1

- **Runde 3, Zug #58** (stone): gespielt `🌙 Spieler 1: 1 (1)× rot von F1 → Reihe 6 [4/6]` (Rang 11/18, Q=0.319) vs. Oracle-Top `Kuppel #0 → (0,2)` (Q=0.528) -- **Δwin% = 20.9**
- **Runde 3, Zug #62** (stone): gespielt `🌙 Spieler 1: 2 (1+1)× rot von F3, F4 → Reihe 2 [2/2]` (Rang 7/15, Q=0.319) vs. Oracle-Top `Bonuschip F1` (Q=0.493) -- **Δwin% = 17.4**
- **Runde 3, Zug #60** (stone): gespielt `🌙 Spieler 1: 1 (1)× rot von F1 → Reihe 6 [5/6]` (Rang 7/14, Q=0.342) vs. Oracle-Top `Kuppel #0 → (1,2)` (Q=0.505) -- **Δwin% = 16.4**

### KI

- **Runde 2, Zug #36** (dome_stack): gespielt `KI: Kachel 17 → Slot (1,1) rot=0° [Plättchen 2/2]` (Rang 6/6, Q=0.561) vs. Oracle-Top `Stapel → (1,2)` (Q=0.619) -- **Δwin% = 5.8**
- **Runde 3, Zug #57** (stone): gespielt `☀️  KI: 2× gelb von F3 → Reihe 5 [5/5] (+1 Strafleiste)` (Rang 14/23, Q=0.571) vs. Oracle-Top `Stapel: verdeckt ziehen` (Q=0.621) -- **Δwin% = 4.9** _(Match evtl. mehrdeutig)_
- **Runde 3, Zug #59** (dome_display): gespielt `KI: Kachel 13 → Slot (1,2) rot=270° [Plättchen 2/2]` (Rang 4/13, Q=0.596) vs. Oracle-Top `Kuppel #0 → (2,2)` (Q=0.641) -- **Δwin% = 4.5**

## (c) Wendepunkte (groesste Win%-Sprünge)

Win%-Schätzung ist immer aus Sicht von **Spieler 1** normiert (Oracle-`root_value` ist Win% des jeweils ziehenden Spielers am Zustand VOR dem Zug; für Zug-Perspektive KI wird 100−root_value gebildet).

| von (Zug#/Runde) | nach (Zug#/Runde) | Δ Win% (Spieler 1) |
|---|---|---|
| #86 (R4, Spieler 1 zieht, 14.5%) | #87 (R4, KI zieht, 52.2%) | +37.6 pp |
| #88 (R4, Spieler 1 zieht, 27.6%) | #89 (R4, KI zieht, 57.3%) | +29.6 pp |
| #87 (R4, KI zieht, 52.2%) | #88 (R4, Spieler 1 zieht, 27.6%) | -24.5 pp |
| #91 (R4, Spieler 1 zieht, 34.9%) | #92 (R4, KI zieht, 58.6%) | +23.7 pp |
| #89 (R4, KI zieht, 57.3%) | #90 (R4, Spieler 1 zieht, 34.8%) | -22.4 pp |

## (d) Die Wertungsplatten-Story

Punktestand am Ende jeder Runde (reine Text-Extraktion aus dem Log -- unabhaengig vom Replay-Fortschritt, siehe Grenzen):

| Runde | Spieler 1 | KI |
|---|---|---|
| 1 | 3 | – |
| 2 | 15 | 17 |
| 3 | 29 | 28 |
| 4 | 34 | 35 |
| 5 | 60 | 45 |

(Rohpunktestand direkt vor der Endwertung, aus der `# SPIELENDE:`-Kopfzeile: Spieler 1 60 : 45 KI -- fehlende "–"-Werte oben bedeuten lediglich 0 Pkt Strafe in dieser Runde, keine Lücke.)

Endwertung (Wertungsplatten-Bonus):

- **Spieler 1**: +14 Pkt -> Gesamt 74 Pkt
  - 🎨 Farbenreiche Reihen: 0 Pkt
  - 🌈 Mehrfarbige Felder: 0 Pkt
  - ↕️ Vertikale Reihen: 14 Pkt
- **KI**: +0 Pkt -> Gesamt 45 Pkt
  - 🎨 Farbenreiche Reihen: 0 Pkt
  - 🌈 Mehrfarbige Felder: 0 Pkt
  - ↕️ Vertikale Reihen: 0 Pkt

Vor der Endwertung stand es 60 : 45; nach dem Wertungsplatten-Bonus 74 : 45.

Win%-Verlauf (aus Spieler 1-Sicht) über den oracle-bewerteten Teil der Partie:

| Zug# | Runde | zieht | Win% (Spieler 1) |
|---|---|---|---|
| 1 | 1 | Spieler 1 | 52.7% |
| 2 | 1 | KI | 45.8% |
| 3 | 1 | Spieler 1 | 54.2% |
| 4 | 1 | KI | 46.1% |
| 5 | 1 | Spieler 1 | 53.7% |
| 6 | 1 | KI | 43.5% |
| 7 | 1 | KI | 42.3% |
| 8 | 1 | Spieler 1 | 51.8% |
| 9 | 1 | KI | 40.3% |
| 10 | 1 | KI | 39.7% |
| 11 | 1 | Spieler 1 | 48.8% |
| 12 | 1 | KI | 43.3% |
| 13 | 1 | Spieler 1 | 51.2% |
| 14 | 1 | KI | 41.9% |
| 15 | 1 | Spieler 1 | 44.4% |
| 16 | 1 | KI | 40.7% |
| 17 | 1 | Spieler 1 | 45.5% |
| 18 | 1 | Spieler 1 | 46.5% |
| 19 | 1 | KI | 41.2% |
| 20 | 1 | Spieler 1 | 48.6% |
| 21 | 1 | KI | 43.5% |
| 22 | 1 | Spieler 1 | 50.0% |
| 23 | 1 | KI | 42.0% |
| 24 | 1 | Spieler 1 | 50.9% |
| 25 | 1 | Spieler 1 | 50.9% |
| 26 | 2 | Spieler 1 | 49.7% |
| 27 | 2 | KI | 50.4% |
| 28 | 2 | Spieler 1 | 46.7% |
| 29 | 2 | KI | 45.7% |
| 30 | 2 | Spieler 1 | 47.8% |
| 31 | 2 | KI | 40.4% |
| 32 | 2 | Spieler 1 | 44.3% |
| 33 | 2 | KI | 39.1% |
| 34 | 2 | Spieler 1 | 43.9% |
| 35 | 2 | KI | 38.5% |
| 36 | 2 | KI | 39.2% |
| 37 | 2 | Spieler 1 | 41.9% |
| 38 | 2 | KI | 50.5% |
| 39 | 2 | Spieler 1 | 31.8% |
| 40 | 2 | KI | 48.3% |
| 41 | 2 | Spieler 1 | 28.1% |
| 42 | 2 | KI | 42.0% |
| 43 | 2 | Spieler 1 | 27.1% |
| 44 | 2 | KI | 38.2% |
| 45 | 2 | Spieler 1 | 23.9% |
| 46 | 2 | KI | 37.0% |
| 47 | 2 | KI | 37.2% |
| 48 | 3 | Spieler 1 | 51.3% |
| 49 | 3 | KI | 37.4% |
| 50 | 3 | Spieler 1 | 38.7% |
| 51 | 3 | KI | 40.0% |
| 52 | 3 | Spieler 1 | 36.8% |
| 53 | 3 | KI | 34.1% |
| 54 | 3 | Spieler 1 | 28.1% |
| 55 | 3 | KI | 33.7% |
| 56 | 3 | Spieler 1 | 27.5% |
| 57 | 3 | KI | 40.5% |
| 58 | 3 | Spieler 1 | 42.7% |
| 59 | 3 | KI | 39.4% |
| 60 | 3 | Spieler 1 | 43.2% |
| 61 | 3 | KI | 39.8% |
| 62 | 3 | Spieler 1 | 40.6% |
| 63 | 3 | KI | 37.0% |
| 64 | 3 | Spieler 1 | 39.7% |
| 65 | 3 | KI | 43.4% |
| 66 | 3 | Spieler 1 | 50.4% |
| 67 | 3 | KI | 45.3% |
| 68 | 3 | Spieler 1 | 51.7% |
| 69 | 3 | Spieler 1 | 41.2% |
| 70 | 3 | Spieler 1 | 41.9% |
| 71 | 3 | Spieler 1 | 29.9% |
| 72 | 4 | Spieler 1 | 35.3% |
| 73 | 4 | KI | 48.2% |
| 74 | 4 | Spieler 1 | 34.1% |
| 75 | 4 | KI | 35.8% |
| 76 | 4 | Spieler 1 | 22.1% |
| 77 | 4 | KI | 35.7% |
| 78 | 4 | Spieler 1 | 16.7% |
| 79 | 4 | KI | 29.5% |
| 80 | 4 | Spieler 1 | 9.3% |
| 81 | 4 | KI | 22.1% |
| 82 | 4 | Spieler 1 | 10.3% |
| 83 | 4 | KI | 20.8% |
| 84 | 4 | Spieler 1 | 9.9% |
| 85 | 4 | KI | 22.7% |
| 86 | 4 | Spieler 1 | 14.5% |
| 87 | 4 | KI | 52.2% |
| 88 | 4 | Spieler 1 | 27.6% |
| 89 | 4 | KI | 57.3% |
| 90 | 4 | Spieler 1 | 34.8% |
| 91 | 4 | Spieler 1 | 34.9% |
| 92 | 4 | KI | 58.6% |
| 93 | 4 | KI | 58.9% |

Das Oracle sah Spieler 1 zu Beginn der bewerteten Zuege bei **52.7%** und am Ende von Runde 4 bei **58.9%** Gewinnwahrscheinlichkeit (jeweils aus Sicht des ziehenden Spielers umgerechnet). Runde 5 (Endwertung inkl. Wertungsplatten) lief ausserhalb dieser Betrachtung über den exakten Solver.

## Grenzen und Auffälligkeiten (ehrlich dokumentiert)

- **Determinisierung**: `net_search_state_json` rekonstruiert verdeckte Information (Beutel/Turm/Kuppelstapel/Bonuschip-Pool) aus Zählern/Masken und mischt sie NEU mit einem festen, aus dem Zugindex abgeleiteten Seed -- das Oracle sieht also, wie ein echter Spieler, KEINE verdeckte Information, nur eine andere zufällige Mischung als das tatsächliche Spiel. Ein einzelner 5000-Sim-Lauf ist dadurch eine starke, aber keine perfekte Schätzung (siehe Task #89 fuer die empirisch verifizierte Rekonstruktions-Genauigkeit).
- **Runde 5** läuft über den exakten Alpha-Beta-Solver (kein Informationsgehalt mehr, siehe `round5.rs`) und wurde bewusst NICHT netz-oracle-bewertet (andere Skala/Semantik als die PUCT-Netzsuche der Runden 1-4).
- **Kuppel-Rotation**: die Rotationswahl (Stufe 2 nach Kachel+Slot) wird NICHT separat oracle-bewertet -- `apply_dome`/`apply_dome_stack_choose` bleiben nach aussen atomar, die PendingDomeChoice-Zwischenzustände haben laut Task #89 Serialisierungs-Näherungen.
- **`root_value`-Interpretation**: als Win%-Schätzung des jeweils ziehenden Spielers am Zustand VOR seinem Zug interpretiert (Projekt-Konvention); keine unabhängig re-kalibrierte Wahrscheinlichkeit.
- **Oracle-Zug-Zuordnung** erfolgt über eine geparste Kurzbeschreibung (Farbe/Quelle/Zielreihe bzw. Kachel/Slot/Fabrik) gegen die von der Suche gelabelten Kandidaten; bei der Stapel-Wahl (`choose_draw_stack_slot`) fehlt die Kachel-ID im Label, ein `_(Match evtl. mehrdeutig)_`-Hinweis markiert das im Text.
