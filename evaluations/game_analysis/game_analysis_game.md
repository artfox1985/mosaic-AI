# Spielanalyse: game.log

Erzeugt von `tools/analyze_game_log.py` (Commit `1ca379f`), Laufzeit 0s.

- Seed: 20260906, Startspieler: Claude, KI-Spieler: KI (v24-b06_k3p10, 400 Sims)
## (a) Zusammenfassung

Endstand (aus dem Log-Text): **Claude 72 : 42 KI**

Replay-Kreuzvalidierung: jede einzelne erzeugte Log-Zeile (`log_since`) wurde exakt (String-Gleichheit inkl. `[Rn] `-Präfix) gegen die Original-Logdatei geprüft (alle 331 Zeilen bestehen).

Aufloesung der Stein-Zuege: **63 ueber die Aktions-ID** (`#a`-Zeilen im Log, PREREG_action_id_logging.md), **0 ueber den Textweg** (Rueckfall fuer Logs ohne IDs).

⚠️ Chip-Zeile: 5 Zeile(n) nur beim Symbol toleriert (altes 🎫 gegen heutiges 🎴), 5 nur beim fehlenden Plaettchen-Zusatz. Beides sind die benannten Toleranzen fuer Logs von vor dem 2026-09-07; die heutige Engine schreibt `🎴 ... (3 Plättchen: rot, ...)`.

⚠️ Rueckleg-Zeile: 2 Zeile(n) nur bei der Plattenliste toleriert (Logs vor dem 2026-09-10 nennen `(Reihenfolge): #id (Typ), ...`, die heutige Engine nur noch die Anzahl -- die Reihenfolge sieht nur der ziehende Spieler). Reihenfolge aus der `#a`-Zeile uebernommen: 0 Stapelzug/-zuege.

| Spieler | oracle-bewertete Züge | Ø Δwin% zum Oracle-Top | Top-1-Treffer | Top-3-Treffer | nicht bewertet |
|---|---|---|---|---|---|
| Claude | 0 | – | – | – | 49 |
| KI | 0 | – | – | – | 64 |

- Claude: nicht bewertete Züge -- 40× --no-oracle, 9× Runde 5 -- exakter Alpha-Beta-Solver (round5.rs), nicht netz-oracle-bewertet
- KI: nicht bewertete Züge -- 56× --no-oracle, 8× Runde 5 -- exakter Alpha-Beta-Solver (round5.rs), nicht netz-oracle-bewertet

`Δwin%` = (Oracle-Top-Q − Q der gespielten Aktion) × 100, aus 5000-Sim-Netzsuche (v16_best) am Zustand VOR dem Zug. 0.0 = die gespielte Aktion WAR der Oracle-Top-Zug.

## (b) Groesste Abweichungen von der Oracle-Empfehlung

### Claude

(keine Abweichung -- jeder oracle-bewertete Zug war Top-1, oder keine Züge bewertet.)

### KI

(keine Abweichung -- jeder oracle-bewertete Zug war Top-1, oder keine Züge bewertet.)

## (c) Wendepunkte (groesste Win%-Sprünge)

(zu wenige oracle-bewertete Zustände fuer eine Wendepunkt-Analyse.)

## (d) Die Wertungsplatten-Story

Punktestand am Ende jeder Runde (reine Text-Extraktion aus dem Log -- unabhaengig vom Replay-Fortschritt, siehe Grenzen):

| Runde | Claude | KI |
|---|---|---|
| 1 | – | 0 |
| 2 | 13 | 6 |
| 3 | 25 | 12 |
| 4 | 33 | – |
| 5 | 62 | – |

Endwertung (Wertungsplatten-Bonus):

- **Claude**: +10 Pkt -> Gesamt 72 Pkt
  - ⬜ Äußere Felder: 9 Pkt
  - ↗️ Diagonale Reihen: 10 Pkt
- **KI**: +-1 Pkt -> Gesamt 42 Pkt
  - ⬜ Äußere Felder: 11 Pkt
  - ↗️ Diagonale Reihen: 0 Pkt

Win%-Verlauf (aus Claude-Sicht) über den oracle-bewerteten Teil der Partie:

(keine Datenpunkte -- oracle-Analyse war deaktiviert oder lieferte keine Ergebnisse.)

## Grenzen und Auffälligkeiten (ehrlich dokumentiert)

- **Determinisierung**: `net_search_state_json` rekonstruiert verdeckte Information (Beutel/Turm/Kuppelstapel/Bonuschip-Pool) aus Zählern/Masken und mischt sie NEU mit einem festen, aus dem Zugindex abgeleiteten Seed -- das Oracle sieht also, wie ein echter Spieler, KEINE verdeckte Information, nur eine andere zufällige Mischung als das tatsächliche Spiel. Ein einzelner 5000-Sim-Lauf ist dadurch eine starke, aber keine perfekte Schätzung (siehe Task #89 fuer die empirisch verifizierte Rekonstruktions-Genauigkeit).
- **Runde 5** läuft über den exakten Alpha-Beta-Solver (kein Informationsgehalt mehr, siehe `round5.rs`) und wurde bewusst NICHT netz-oracle-bewertet (andere Skala/Semantik als die PUCT-Netzsuche der Runden 1-4).
- **Kuppel-Rotation**: die Rotationswahl (Stufe 2 nach Kachel+Slot) wird NICHT separat oracle-bewertet -- `apply_dome`/`apply_dome_stack_choose` bleiben nach aussen atomar, die PendingDomeChoice-Zwischenzustände haben laut Task #89 Serialisierungs-Näherungen.
- **`root_value`-Interpretation**: als Win%-Schätzung des jeweils ziehenden Spielers am Zustand VOR seinem Zug interpretiert (Projekt-Konvention); keine unabhängig re-kalibrierte Wahrscheinlichkeit.
- **Oracle-Zug-Zuordnung** erfolgt über eine geparste Kurzbeschreibung (Farbe/Quelle/Zielreihe bzw. Kachel/Slot/Fabrik) gegen die von der Suche gelabelten Kandidaten; bei der Stapel-Wahl (`choose_draw_stack_slot`) fehlt die Kachel-ID im Label, ein `_(Match evtl. mehrdeutig)_`-Hinweis markiert das im Text.
