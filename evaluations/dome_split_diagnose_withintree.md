# Zerlegungs-Diagnose: within-tree (TASK B, korrigiertes Design)

Prereg: `evaluations/EXTERNES_REVIEW_2026-08-08.md`, Abschnitt "TASK B: INSTRUMENT-AMENDMENT". Beide Lesarten (zweistufig/flach) kommen aus DEMSELBEN kachel-isolierten Suchbaum -- Budget und Wurzelbreite sind identisch, siehe Moduldoku von `tools/dome_split_diagnose.py`.

## Lauf-Parameter

- Modus: `within-tree`
- Frozen-Set: `evaluations/frozen_eval_set_v2.pkl` (Version `frozen_v2`, 1800 Records gesamt)
- Modell: `models/alphazero_v21_2d_brierbest.onnx`
- Sims/Kachel-Baum: 400 | c_puct: 1.5 (Legacy-Durchreiche, USE_GUMBEL_SEARCH=true)
- Limit: 30 | ausgewaehlte Zustaende: 30
- Laufzeit: 90.0s (1.5 min)
- Git-Commit: `e03ea58c019f0eed62855925643630e255a63c1a`

## Auswahl-Trichter

- Frozen-Records gesamt: 1800
- nicht Phase=drafting (uebersprungen): 24
- Start-Platzierung ausstehend (uebersprungen): 3
- kein choose_dome_slot legal (uebersprungen): 58
- eligible (choose_dome_slot legal, ausgewertet bis --limit): 30

## Kachel-Status-Verteilung

| Status | n Kacheln |
|---|---|
| ok | 66 |

Mittlere Deckung (Slots mit >=1 bewerteter Rotation, gekappt bei 1.0): 100.0%

## Aggregation (a): jede Kachel ein Datenpunkt (mehr Datenpunkte)

### n_tiles_total=66, davon `ok`

- n (auswertbar) = **66**
- Anteil suboptimal (wertbasiert, epsilon=1e-09): **4/66 = 6.06%**
- mittlere Q-Differenz (flach minus zweistufig): **0.000151**
- maximale Q-Differenz: **0.004064**
- davon nur Rotation falsch (struktur. immer 0, s. Konfundierung 2): 0
- davon Slot/Kachel falsch: 4
- Lesart: Anteil < 5% ODER mittlere Q-Differenz < 0,01 erfuellt -> laut Prereg kostet die Zerlegung nichts Messbares. NUR Bericht, keine Selbst-Entscheidung.

## Aggregation (b): kachel-uebergreifend je Zustand ("cross-tile")

| Status | n Zustaende |
|---|---|
| ok | 30 |

### n_selected_states=30, davon cross_tile `ok`

- n (auswertbar) = **30**
- Anteil suboptimal (wertbasiert, epsilon=1e-09): **2/30 = 6.67%**
- mittlere Q-Differenz (flach minus zweistufig): **0.000131**
- maximale Q-Differenz: **0.003796**
- davon nur Rotation falsch (struktur. immer 0, s. Konfundierung 2): 0
- davon Slot/Kachel falsch: 2
- Lesart: Anteil < 5% ODER mittlere Q-Differenz < 0,01 erfuellt -> laut Prereg kostet die Zerlegung nichts Messbares. NUR Bericht, keine Selbst-Entscheidung.

## Verbleibende Konfundierungen (siehe Moduldoku fuer Details)

1. `best_rotation` ist die MEISTBESUCHTE, nicht die hoechst bewertete Rotation (`net_mcts.rs`: `max_by_key(visits)`) -- Rauschgrenze auf BEIDEN Lesarten gleich, keine Asymmetrie zwischen ihnen.
2. Direkte Folge von (1): `n_rotation_only` ist unter dieser Metrik-Definition STRUKTURELL immer 0 (Beleg, keine Ueberraschung) -- sobald derselbe Slot gewinnt, lesen beide Seiten dieselbe `best_rotation`. Echte Rotation-Suboptimalitaet (richtiger Slot, aber nicht die Q-hoechste Rotation) ist mit der aktuellen `net_search_state_json`-Ausgabe nicht messbar.
3. `dome_stack_peek` bleibt Wurzel-Konkurrent in jedem Kachel-Baum -- verkleinert das Slot-Budget etwas, gleich fuer beide Lesarten desselben Baums (Rauschen, keine Verzerrung).
4. Die kachel-uebergreifende Aggregation (b) vergleicht Q-Werte aus VERSCHIEDENEN Suchbaeumen -- setzt Massstabs-Vergleichbarkeit voraus (bestehende Annahme, nicht neu durch dieses Amendment).
