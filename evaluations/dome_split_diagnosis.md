# Zerlegungs-Diagnose: ChooseDomeSlot / ChooseDomeRotation (TASK B)

Prereg: `evaluations/EXTERNES_REVIEW_2026-08-08.md`, Abschnitt "TASK B -- Zerlegungs-Diagnose" (Punkt 3). Werkzeug: `tools/dome_split_diagnosis.py`.

## Lauf-Parameter

- Frozen-Set: `evaluations/frozen_eval_set_v2.pkl` (Version `frozen_v2`, 1800 Records gesamt)
- Modell: `models/alphazero_v21_2d_brierbest.onnx`
- Sims/Zustand: 400 | c_puct: 1.5 (Legacy-Durchreiche, USE_GUMBEL_SEARCH=true)
- Limit: 50 | ausgewaehlte Zustaende: 50
- Laufzeit: 119.7s (2.0 min)
- Git-Commit: `728a61fd04bd317b531b63c61f6c098f21517d5b`

## Auswahl-Trichter

- Frozen-Records gesamt: 1800
- nicht Phase=drafting (uebersprungen): 44
- Start-Platzierung ausstehend (uebersprungen): 3
- kein choose_dome_slot legal (uebersprungen): 97
- eligible (choose_dome_slot legal, ausgewertet bis --limit): 50

## Status-Verteilung (alle ausgewaehlten Zustaende)

| Status | n |
|---|---|
| root_chose_non_dome | 30 |
| ok | 20 |

## Kern-Kennzahlen (nur `status=ok`)

- n (auswertbar) = **20** von 50 ausgewaehlten Zustaenden
- Anteil suboptimal (zweistufig != flach-beste Kombination, wertbasiert, epsilon=1e-09): **11/20 = 55.00%**
- mittlere Q-Differenz (flach-best minus zweistufig): **0.013788**
- maximale Q-Differenz: **0.081149**
- davon nur Rotation falsch (gleiche Kachel+Slot): 0
- davon Slot falsch (andere Kachel oder Slot): 11
- mittlere Deckung der flachen Enumeration (n_scored/n_legal, gekappt bei 1.0): 100.0%

## Lesart (woertlich aus der Prereg, NUR Bericht)

> Weder Anteil < 5% noch mittlere Q-Differenz < 0,01 erfuellt -> laut Prereg wuerde eine faktorierte Policy/Action-Attention ein begruendeter Kandidat (eigenes Prereg, Architektur-Kostenklasse). NUR Bericht, keine Selbst-Entscheidung.

## Vorbehalte (siehe Moduldoku fuer die volle Begruendung)

1. Kein zweiter Suchaufruf auf dem Post-Slot-Zwischenzustand (nicht serialisierbar, `pending_dome_choice` ist nicht Teil des Wire-Formats) -- stattdessen Kachel-isolierte volle Suche pro Kachel im Display.
2. Q-Feld = `best_rotation.q` (Wurzelkind-Wert, dieselbe Spielerperspektive wie die Slot-Entscheidung, kein Vorzeichenwechsel).
3. Zustaende, in denen die zweistufige Suche an der Wurzel gar keinen Kuppelzug waehlt, sind aus der Kern-Metrik ausgeschlossen (Status `root_chose_non_dome`, s. Tabelle oben).
4. `dome_stack_peek` bleibt in den kachel-isolierten Aufrufen als Wurzel-Konkurrent stehen (eigene, hier nicht untersuchte Zerlegung).
5. Deckungsgrad der flachen Enumeration ist NICHT 100% garantiert (s. mittlere Deckung oben) -- Zustaende ohne aufgeloeste Zweistufer-Rotation sind separat gezaehlt (`twostage_rotation_unresolved`).
