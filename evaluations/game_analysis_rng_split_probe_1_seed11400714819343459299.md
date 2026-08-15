# Spielanalyse: game_rng_schnitt_probe_1_seed11400714819343459299.log

Erzeugt von `tools/analyze_game_log.py` (Commit `a191cd7`), Laufzeit 0s.

- Seed: 11400714819343459299, Startspieler: Heuristik, KI-Spieler: Netz (alphazero_v21_2d_brierbest, 40 Sims)
## (a) Zusammenfassung

Endstand (aus dem Log-Text): **Netz 54 : 57 Heuristik**

Replay-Kreuzvalidierung: jede einzelne erzeugte Log-Zeile (`log_since`) wurde exakt (String-Gleichheit inkl. `[Rn] `-Präfix) gegen die Original-Logdatei geprüft (alle 323 Zeilen bestehen).

| Spieler | oracle-bewertete Züge | Ø Δwin% zum Oracle-Top | Top-1-Treffer | Top-3-Treffer | nicht bewertet |
|---|---|---|---|---|---|
| Netz | 0 | – | – | – | 52 |
| Heuristik | 0 | – | – | – | 54 |

- Netz: nicht bewertete Züge -- 44× --no-oracle, 8× Runde 5 -- exakter Alpha-Beta-Solver (round5.rs), nicht netz-oracle-bewertet
- Heuristik: nicht bewertete Züge -- 45× --no-oracle, 9× Runde 5 -- exakter Alpha-Beta-Solver (round5.rs), nicht netz-oracle-bewertet

`Δwin%` = (Oracle-Top-Q − Q der gespielten Aktion) × 100, aus 5000-Sim-Netzsuche (v16_best) am Zustand VOR dem Zug. 0.0 = die gespielte Aktion WAR der Oracle-Top-Zug.

## (b) Groesste Abweichungen von der Oracle-Empfehlung

### Netz

(keine Abweichung -- jeder oracle-bewertete Zug war Top-1, oder keine Züge bewertet.)

### Heuristik

(keine Abweichung -- jeder oracle-bewertete Zug war Top-1, oder keine Züge bewertet.)

## (c) Wendepunkte (groesste Win%-Sprünge)

(zu wenige oracle-bewertete Zustände fuer eine Wendepunkt-Analyse.)

## (d) Die Wertungsplatten-Story

Punktestand am Ende jeder Runde (reine Text-Extraktion aus dem Log -- unabhaengig vom Replay-Fortschritt, siehe Grenzen):

| Runde | Netz | Heuristik |
|---|---|---|
| 1 | 6 | – |
| 2 | 6 | 14 |
| 3 | 18 | – |
| 4 | – | 28 |
| 5 | 42 | 51 |

(Rohpunktestand direkt vor der Endwertung, aus der `# SPIELENDE:`-Kopfzeile: Netz 54 : 57 Heuristik -- fehlende "–"-Werte oben bedeuten lediglich 0 Pkt Strafe in dieser Runde, keine Lücke.)

Endwertung (Wertungsplatten-Bonus):

- **Netz**: +12 Pkt -> Gesamt 54 Pkt
  - ↕️ Vertikale Reihen: 0 Pkt
  - 🌈 Mehrfarbige Felder: 12 Pkt
  - 🎨 Farbenreiche Reihen: 0 Pkt
- **Heuristik**: +6 Pkt -> Gesamt 57 Pkt
  - ↕️ Vertikale Reihen: 0 Pkt
  - 🌈 Mehrfarbige Felder: 6 Pkt
  - 🎨 Farbenreiche Reihen: 0 Pkt

Vor der Endwertung stand es 54 : 57; nach dem Wertungsplatten-Bonus 54 : 57.

Win%-Verlauf (aus Netz-Sicht) über den oracle-bewerteten Teil der Partie:

(keine Datenpunkte -- oracle-Analyse war deaktiviert oder lieferte keine Ergebnisse.)

## Grenzen und Auffälligkeiten (ehrlich dokumentiert)

- **Entdeckte Logging-Luecke (KI-Bonuschips)**: der Mensch-Pfad `apply_tiling_chips` (py.rs) loggt "🎫 ... komplettiert Reihe N ...", der KI-Pfad (`ai_tiling_step` -> `TilingStep::Chips` -> `apply_bonus_chips_with`, round_end.rs) tut das NICHT. Betroffen in dieser Partie: R2 Heuristik Reihe 3, R2 Netz Reihe 4, R4 Netz Reihe 3, R4 Heuristik Reihe 3, R5 Netz Reihe 5, R5 Heuristik Reihe 4. Das Replay-Werkzeug erkennt die unvollstaendige Zielreihe und holt die Chip-Komplettierung automatisch nach (ohne die dabei entstehende, im Original fehlende "🎫"-Zeile gegen das Log zu pruefen).
- **Determinisierung**: `net_search_state_json` rekonstruiert verdeckte Information (Beutel/Turm/Kuppelstapel/Bonuschip-Pool) aus Zählern/Masken und mischt sie NEU mit einem festen, aus dem Zugindex abgeleiteten Seed -- das Oracle sieht also, wie ein echter Spieler, KEINE verdeckte Information, nur eine andere zufällige Mischung als das tatsächliche Spiel. Ein einzelner 5000-Sim-Lauf ist dadurch eine starke, aber keine perfekte Schätzung (siehe Task #89 fuer die empirisch verifizierte Rekonstruktions-Genauigkeit).
- **Runde 5** läuft über den exakten Alpha-Beta-Solver (kein Informationsgehalt mehr, siehe `round5.rs`) und wurde bewusst NICHT netz-oracle-bewertet (andere Skala/Semantik als die PUCT-Netzsuche der Runden 1-4).
- **Kuppel-Rotation**: die Rotationswahl (Stufe 2 nach Kachel+Slot) wird NICHT separat oracle-bewertet -- `apply_dome`/`apply_dome_stack_choose` bleiben nach aussen atomar, die PendingDomeChoice-Zwischenzustände haben laut Task #89 Serialisierungs-Näherungen.
- **`root_value`-Interpretation**: als Win%-Schätzung des jeweils ziehenden Spielers am Zustand VOR seinem Zug interpretiert (Projekt-Konvention); keine unabhängig re-kalibrierte Wahrscheinlichkeit.
- **Oracle-Zug-Zuordnung** erfolgt über eine geparste Kurzbeschreibung (Farbe/Quelle/Zielreihe bzw. Kachel/Slot/Fabrik) gegen die von der Suche gelabelten Kandidaten; bei der Stapel-Wahl (`choose_draw_stack_slot`) fehlt die Kachel-ID im Label, ein `_(Match evtl. mehrdeutig)_`-Hinweis markiert das im Text.
