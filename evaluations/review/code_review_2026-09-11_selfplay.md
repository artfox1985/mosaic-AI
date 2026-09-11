# Code-Review 2026-09-11: self_play.rs und serialize.rs

**Datum:** 2026-09-11. **Art:** rein lesend, keine Aenderung, kein Bau, kein Lauf.
**Gelesen:** `engine/src/self_play.rs` (9.196 Zeilen, vollstaendig),
`engine/src/serialize.rs` (2.771 Zeilen, vollstaendig).
**Nur gegriffen (nicht vollstaendig gelesen):** `features.rs:1452-1479`,
`engine/py/neural_net.py:664-720`, `knob_registry.rs`, `mcts.rs:808-957`,
`game.rs:557-596`, `referee.rs`, `lib.rs`, `tools/*.py`.
Jede Aussage hat eine Pruefstelle; was darueber hinausgeht, ist als "ungeprueft"
oder "unklar" markiert.

---

## 1. Bugs und Korrektheitsrisiken

### 1.1 Die Eroeffnungssetzung traegt ihr Policy-Ziel auf einer toten Aktions-ID (schwer)

`start_placement_step` baut Maske und gespielte Aktion mit `"type": "dome"`
(self_play.rs:976-983 und 998-1005). `features::action_to_id` kennt diesen Typ
nicht mehr -- die Arme heissen `choose_dome_slot` / `choose_dome_rotation`
(features.rs:1465-1472), `"dome"` faellt in den Auffang-Arm `_ => 405`
(features.rs:1477), und 405 ist die ID von `dome_stack_peek` (features.rs:1476).
Der Python-Zwilling verhaelt sich gleich: kein `dome`-Arm, `return 405 #
Fallback` (neural_net.py:719); sein eigener Kommentar nennt das alte
`dome`-Schema ausdruecklich abgeloest (neural_net.py:689-691).

Folge am Code: das Policy-Ziel jedes Eroeffnungs-Records zeigt auf "verdeckt vom
Stapel ziehen", und die komplette Maske (Display x freie Slots x 4 Rotationen,
self_play.rs:972-986) kollabiert auf dieselbe eine ID. Der Modulkopf
self_play.rs:10-13 begruendet das agent_env-Schema genau damit, dass
`action_to_id` diese Keys lese -- fuer `dome` stimmt das nicht mehr.
Groessenordnung: 1 bis 2 Records je Partie. **Ungeprueft:** ob `train.py` diese
Records ueberhaupt in den Policy-Verlust nimmt.

### 1.2 `player` und gespielte Aktion gehen bei der Eroeffnung auseinander (mittel)

`recorded_player = game.state.current_player` (self_play.rs:952) wird als
`"player"` geschrieben (self_play.rs:1014), gelegt wird aber auf dem Brett von
`pi`, und `pi` ist beim ERSTEN Aufruf der Nicht-Startspieler
(self_play.rs:955-961). `apply_start_placement` fasst `current_player` nicht an
(game.rs:557-596). Beide Eroeffnungs-Records tragen also `player =
Startspieler`, der erste beschreibt den Zug des anderen. `player` ist die
Perspektive des Wert-Ziels bei mehreren Konsumenten (`tools/platt_fit.py:70`,
`chance_node_pretest.py:162`, `t36_curve_eval.py:94`,
`relabel_drafts_with_net.py:75`); fuer das Wert-Ziel bleibt es konsistent,
auseinander gehen Policy-Ziel und Wert-Perspektive. Der Kommentar
self_play.rs:949-950 stellt das als Python-Paritaet dar, benennt die Divergenz
aber nicht.

### 1.3 Zwei Kommentare behaupten einen v2-Vorzug, den der Code nicht hat (mittel)

`heuristic_arena_choose_action` sagt im Doc "v2-Vorzug ZUERST, dann Suche"
(self_play.rs:2102) und inline dasselbe (self_play.rs:2114-2116); der Rumpf ruft
nur `mcts::search_drafting_action` (self_play.rs:2117). Gleiche Falschaussage in
`play_arena_game` (self_play.rs:3328-3334) vor einem Rumpf, der ebenfalls nur
sucht (self_play.rs:3335). Geprueft: `search_drafting_action` reicht an
`search_action_inner` durch (mcts.rs:938-957), und in `engine/src/mcts.rs` kommt
weder `provocation` noch `plate_builder` noch `column_build` vor (Grep, 0
Treffer). Es gibt auf dem Heuristik-Pfad keinen Vorzug. Relevanz:
`referee.rs:167` ruft genau diese Funktion als Zugquelle des eingefrorenen
Heuristik-Gegners; wer den Kommentar liest, haelt hv2 dort fuer verdrahtet.

### 1.4 Ein Panic im Self-Play wird als Watchdog-Timeout gemeldet (mittel)

`unified_game_loop` paniked bei `Err` aus `apply_chosen_action`
(self_play.rs:2783-2784) und `apply_drafting` (self_play.rs:2789-2798). Die
Partie laeuft im gespawnten Thread von `run_with_watchdog`
(self_play.rs:4563-4574, `rx.recv_timeout(deadline).ok()`). Ein Panic schliesst
den Kanal; `.ok()` macht daraus dasselbe `None` wie ein echter Timeout, und der
Aufrufer druckt "ueberschritt die harte Deadline" (self_play.rs:4786-4789,
Ausflug 4881-4884). Ein Engine-Bug erscheint im Log als Laufzeitproblem.

### 1.5 Perspektive im Tiling zwischen zwei Nachbarn uneinheitlich (klein)

`net_tiling_tiebreak_value` spiegelt defensiv (`if ... { roh } else { 1.0 - roh
}`, self_play.rs:1152), `net_tiling_margin_value` daneben gar nicht
(self_play.rs:1097-1102) -- beide behaupten dieselbe Invariante per
`debug_assert` (1098, 1105-1108). Bricht ein kuenftiger Aufrufer sie, kippt der
eine Term und der andere nicht. Zusatz: `1.0 - roh` wird auf den BLEND aus
Value- und Punkte-Kopf angewandt (self_play.rs:1133-1151); dass `1 - pp` die
richtige Spiegelung der Punkte-Vorhersage ist, steht nirgends belegt -- unklar.

### 1.6 `dome_pool_view`: `len` und `special + wild` koennen auseinanderfallen (klein)

Das Blockende wird am Pool-Ende gesaettigt (serialize.rs:107), berichtet wird
aber die UNGESAETTIGTE Laenge (`"len": b.len`, serialize.rs:114), waehrend
`special`/`wild`/`types` aus dem verkuerzten Schnitt kommen
(serialize.rs:108-125). Bei verletzter Invariante liefert das Feld im
Release-Bau eine in sich widerspruechliche Sicht; der Kommentar
serialize.rs:104-107 begruendet die Saettigung, nennt diese Folge nicht.

### 1.7 `monochrome_fallback` aus einer hinreichenden, nicht notwendigen Bedingung (klein)

`large_factory_from_json` setzt das Flag bei "nicht leer und alle gleich"
(serialize.rs:936). Eine regulaer gefuellte grosse Fabrik mit zufaellig
einfarbigen Sonnensteinen bekommt es ebenfalls. Der Doku-Block
(serialize.rs:751-755) argumentiert nur in die eine Richtung. `json_to_state_exact`
erbt den Fehler, weil es `json_to_state` aufruft (serialize.rs:1449) und dieses
Feld danach nicht ueberschreibt.

### 1.8 Geprueft und in Ordnung

RNG-Stroeme: Weg B und Weg C haben eigene Distinguisher (1484, 1828) und
reservierte Zaehler (1835, 1899), der Fruehausstieg bei Default-AUS steht VOR
dem `StdRng`-Bau (1668-1670, 1958-1961); der Suchstrom je Halbzug kommt aus
`derive_search_seed` (2588-2591). Ausschluss des Suchzugs (par.9k) greift fuer
beide Quellen (2678-2688, Filter 1762-1772), Dubletten-Waechter im Aufrufer
(4865-4878). Stopp-Regel der Stapelziehung terminiert beweisbar (`remove(0)`
plus `MAX_STACK_PEEKS = 20`, 615/626). Bootstrap: `round_before < NUM_ROUNDS`
verhindert das bedeutungslose Sample an der Runde-5-Grenze (2806).
Platt-Destretch kommt in beiden Dateien nicht vor (Grep, 0 Treffer) -- der liegt
in `tools/platt_fit.py`. JSON-Rundreise: `json_to_state_exact` ist durch einen
erschoepfenden Struktur-Diff abgesichert (serialize.rs:1661-1930), nicht nur
JSON gegen JSON.

---

## 2. Tote oder ueberholte Pfade

* **`mean_rollout_diff`s Nicht-Alphabeta-Zweig ist unerreichbar.** Einziger
  Aufrufer `stage3_choose_action` (5294) setzt `alphabeta = Some(..)` fest
  (5292); self_play.rs:5179-5188 laeuft nie, samt `move_number = 0`-Platzhalter.
* **`play_net_game`s `net_board != 0`** ist unerreicht (Kommentar 3528,
  `run_net_arena_match` uebergibt hart `0`, 3617).
* **Vier Diagnose-Einstiege ohne Python-Konsumenten:** `sibling_ranking_
  diagnostic` (5559), `draw_stack_peek_impact_diagnostic` (5711),
  `value_noise_floor_diagnostic` (5881), `run_net_vs_net_arena_hybrid` (3945).
  Alle haengen in `lib.rs` (184-241, 375-391, 2027-2031), aber ein Grep ueber
  `tools/`, `agents/`, `*.py` findet keinen Aufrufer; Gegenprobe:
  `run_stage3_vs_stage1_arena` hat einen (`tools/arena.py:483,531`). Zusammen
  rund 900 Zeilen (3773-3994, 5502-6082) plus die nur von Stufe 3 gebrauchte
  Alpha-Beta-Kette (4925-5303, rund 380 Zeilen).
* **Zwei dauerhaft ignorierte Tests,** einer mit als falsch erkannter Praemisse
  (7432-7438) und einer teurer (7339-7341).
* **Knopf-Status:** kein Knopf dieser Dateien ist `KnobStatus::Tot`
  (knob_registry.rs:182-188 listet die toten, keiner liegt hier). Vier stehen
  auf `Diagnose` und halten Verzweigungen offen: `MOSAIC_STACK_DRAW_RESEARCH`
  (Reg. 133 -> self_play.rs:761), `MOSAIC_STACK_DRAW_RESERVATION` (Reg. 151 ->
  629-659), `MOSAIC_ASYM_VORZUG` (Reg. 134 -> 4425-4428, 4515-4522),
  `MOSAIC_ACTION_TEMP` (Reg. 135 -> 4148-4174). `MOSAIC_TILING_PUNKTE_W` steht
  auf `Aktiv`, obwohl der Registratur-Text selbst "gemessen wirkungslos" sagt
  (Reg. 129); die Verzweigung self_play.rs:1133-1151 bleibt dafuer offen.
* **Record-Felder: keines ist konsumentenlos.** Geprueft per Grep ueber
  `tools/`, `agents/`, `engine/py/`, `*.py`: `root_child_q`,
  `policy_target_valid`, `moon_order_target`, `scores_unclamped`,
  `round_transition_value`, `bootstrap_value`, `dome_pool_view`, `col_f_max`,
  `moon_top_counts`, `estimated_score` haben je einen Leser;
  `cell_reachable_mask` und `dome_wild_remaining_frac` nicht in `tools/`, aber in
  `neural_net.py:619` bzw. `:140` und `features.rs:283, 1354`.

---

## 3. Optimierungspotenzial (nur an konkretem Code belegt)

* **`best_eval_for_tile` klont den ganzen `GameState` je Slot mal Rotation.**
  `Game { state: state.clone() }` steht INNEN in der doppelten Schleife
  (self_play.rs:548-550) -- bis zu 9 x 4 = 36 volle Zustandsklone je
  Kandidatenplatte. Aufgerufen je Platte in der Hand (623), mit aktiver
  Reservationsregel zusaetzlich ueber alle Pool-Platten desselben Typs (647-649)
  und noch einmal zur Endauswahl (669). Bei 18 Pool-Platten sind das im
  Reservations-Arm mehrere hundert Klone je Stapelzug. Billigster Hebel: den
  Klon aus der Rotationsschleife ziehen. **Ungeprueft**, ob
  `execute_draw_from_stack` ausser `players[pi]` und `pending_stack_draw` noch
  etwas anfasst.
* **`state_to_json` je aufgezeichnetem Zug** (self_play.rs:997, 1320, 2758).
  Jeder Aufruf laeuft je Spieler durch `serialize_player`, und das ruft den
  exakten Tiling-Solver `solve_round_final_score` (serialize.rs:208), 36 x
  `cell_is_completable` (216-221), `player_scoring_features` und
  `player_line_features` (226-227). **Kosten nicht gemessen**, aber es ist die
  einzige Stelle in beiden Dateien, an der ein exakter Solver je Record je
  Spieler laeuft.
* **`valid_actions` baut je Drafting-Record ein JSON-Objekt je legaler Aktion**
  (2592-2596), obwohl mit `action_to_id_direct` (288-322) der JSON-freie
  Zwilling existiert. Der Record braucht die Dicts, also kein Fehler, aber der
  groesste Allokationsposten je Zug im Aufzeichnungspfad.
* **Kein doppelter Netzaufruf gefunden:** `ownership_tiling_marginals` laeuft
  bewusst einmal je Tiling-Zug vor der Kandidatenschleife (1284-1285), und die
  Gates davor (1223-1226) sparen den Pass bei Default-AUS ganz.

---

## 4. Struktur und Nachvollziehbarkeit

### 4.1 Dateigroesse und Schnittvorschlag

`self_play.rs`: 9.196 Zeilen, Produktionscode bis 6082, danach vier Testmodule
(6084-8802, 8820-8993, 8995-9165, 9167-9196), zusammen rund 3.100 Zeilen.

Die Phasen-Verzweigung `Phase::StartPlacement | Phase::Drafting =>` kommt
**14-mal** vor (2538, 3297, 3821, 5165, 5341, 5592, 5736, 5909, 5986, 6162,
6265, 7227, 8005, 8069). `PREREG_unified_game_loop.md` hat vier Kopien
zusammengefuehrt (Kommentar 1360-1371); neun blieben stehen, davon fuenf in
Produktions- oder Diagnose-Code (3297 `play_arena_game`, 3821
`play_net_vs_net_hybrid_game`, 5165 `mean_rollout_diff`, 5341
`play_stage3_vs_stage1_game`, dazu die drei Diagnosen 5592/5736/5909).

**Schnitte nach Nahtbreite (schmalste zuerst):**

1. `self_play_diagnostics.rs` -- 4925-6082 (Alpha-Beta-Kette, Stufe 3,
   `kendall_tau`, die drei Diagnosen), rund 1.160 Zeilen. Naht: 9 Namen
   (`choose_start_placement`, `start_placement_step`, `tiling_step`,
   `resolve_tiling_step`, `apply_chosen_action`, `net_drafting_policy`,
   `action_to_env_dict`, `net_effective_sims`, `dynamic_sims`), davon 5 heute
   modul-privat. Schmalster sinnvoller Schnitt.
2. Die drei Stapel-Testmodule am Dateiende (8804-9196, rund 390 Zeilen) haengen
   nur an 4 Namen (`resolve_and_apply_stack_draw`, `stack_draw_reservation`,
   `Game`, `scoring_progress`).
3. `self_play_arena.rs` (3256-3994): Naht rund 20 Namen (`unified_game_loop`,
   `GameLoopConfig`, `PlayerLoopConfig`, `LoopMode`, `LoopOutput`,
   `LabelSamplingConfig`, `DraftingAgent` plus vier Agenten-Structs,
   `thread_plan`, `ThreadPlan`, beide Timeout-Funktionen und vier weitere). Zu
   breit -- der Loop und seine Konfiguration muessten praktisch komplett
   oeffentlich werden.

`serialize.rs` braucht keinen Schnitt: Produktionscode endet bei 1616 bzw. 2239,
der Rest sind vier Testmodule (1618-2186, 2241-2360, 2362-2647, 2653-2771).

### 4.2 Deutsche Bezeichner (Verstoss gegen CLAUDE.md, Regel 2026-08-24)

*Produktionscode self_play.rs:* `start_placement_kandidaten` (892),
`tiling_punkte_weight` (1162), `warne_fehlenden_punkte_kopf_einmal` (1167),
`warne_unbrauchbaren_ownership_kopf_einmal` (1256), `DraftingDecision::vorzug`
(2018), `vorzug_kandidat` (2162/2196/2255), `vorzug_kandidat_tiling` (2901),
`GameLoopConfig::vorzug_greift` (2383), `NetArenaAgent::vorzug` (2145),
`NetSelfPlayAgent::vorzug` (2222), `ThreadPlan::Sequenziell` (3433), `roh`
(2134), `quelle` (2660) mit den Zeichenketten `"ausflug"`/`"wegc"` (2653/2656),
`summe` (2645), `typ` (2644/2767), `vorzug_seite`/`vorzug_p0`/`vorzug_p1`
(4426-4428), `greif_counter` (4474), `seite` (4517). Rund 20 Namen.

*Testmodule self_play.rs (durchgaengig deutsch):* `ziehbereites_spiel` (8835),
`brett_vorbereiten` (8851), `ziehtiefe` (8905),
`ziehtiefe_haengt_an_wertungsplatte_6_und_am_brettniveau` (8940),
`spalte_fuellen` (9015), `brett_gemischt` (9049),
`spaltenfuellstand_gegen_festes_spezialfeld_defizit` (9094),
`spaltenbau_beendet_die_tiefen_ziehungen_von_selbst` (9120),
`tiefe_und_kosten_der_aktiven_fassung` (9183) samt allen Lokalen.

*serialize.rs:* nur `log_sichtbar`/`sichtbar` (307-310) und `feld` (461).

### 4.3 Tests, die etwas anderes pruefen als ihr Name sagt

* `spaltenbau_beendet_die_tiefen_ziehungen_von_selbst` (9120) prueft nur
  `tiefen_k1.iter().all(|&t| t >= 1)` (9160-9163) -- per Konstruktion wahr, weil
  jede Aufloesung mindestens den Pflicht-Peek zieht (602). Kann nicht
  fehlschlagen.
* `spaltenfuellstand_gegen_festes_spezialfeld_defizit` (9094) und
  `tiefe_und_kosten_der_aktiven_fassung` (9183) enthalten **kein einziges
  `assert`**, sie drucken nur Tabellen.
* `run_self_play_returns_valid_json` (6523) prueft nur "Array nicht leer" (6526).
* `roundtrip_exact_many_real_games` (serialize.rs:2116) laeuft ueber `1..=80`
  (2120), die Meldungen sprechen von "40 Partien" (2182, 2184). Stale.

### 4.4 Widerspruechliche Doc-Kommentare (ueber 1.1 und 1.3 hinaus)

`resolve_tiling_step`-Doku nennt das Gate-Fenster "Runden 2-4"
(self_play.rs:1186), 30 Zeilen weiter steht `plate_branch_applies` mit `1..=4`
(1216-1218). **Ungeprueft**, welches gilt -- die Pruefstelle liegt in
`tiling_solver.rs`. Nebenbefund ausserhalb des Auftrags: `mcts.rs:947` nennt
`search_drafting_action_inner` "mit ausdruecklicher Heuristik-Variante", die
Signatur hat keinen solchen Parameter (mcts.rs:948-953).

---

## 5. Priorisiert: vor Projektende

| # | Was | Aufwand | Risiko |
|---|-----|---------|--------|
| 1 | 1.3: die beiden falschen "v2-Vorzug ZUERST"-Kommentare (2102, 2114-2116, 3328-3334) loeschen oder richtigstellen | 0,25 h | keins, reiner Kommentar |
| 2 | 1.1 zuerst MESSEN: Sonde, die zaehlt, wie viele Records mit ID 405 aus `"type": "dome"` stammen und ob `train.py` sie in den Policy-Verlust nimmt | 1 h | keins, nur lesend |
| 3 | 1.1 entscheiden: `action_to_id` bekommt einen `dome`-Arm (features.rs:1455 UND neural_net.py:669) oder `start_placement_step` emittiert `choose_dome_slot` + `choose_dome_rotation` | 2-4 h | **hoch**: Policy-Ziele, Anker-Invarianz, neuer Netz-Paritaets-Hash |
| 4 | 1.4: `run_with_watchdog` gibt `Result` statt `Option` (4563-4574), Aufrufer melden Panic und Timeout getrennt (4786-4789, 4881-4884) | 1 h | klein, kein Spielverhalten |
| 5 | 4.3: die drei assertionslosen bzw. trivialen Tests (9094, 9120, 9183) mit echter Zusicherung versehen oder nach `examples/` verschieben | 1 h | klein |
| 6 | 2: die vier konsumentenlosen Diagnose-Einstiege loeschen (3773-3994, 5502-6082) samt Alpha-Beta-Kette, falls Stufe 3 mitentfaellt | 1-2 h | mittel: `lib.rs` und `tools/arena.py:483` mitziehen, **nur nach pfadgenauer Freigabe** |
| 7 | 1.5: `net_tiling_margin_value` dieselbe Spiegelung geben wie `net_tiling_tiebreak_value` oder beide auf `debug_assert` reduzieren (1097-1152) | 0,5 h | klein, Default-AUS unberuehrt |
| 8 | 1.6: `dome_pool_view` berichtet die gesaettigte Laenge (serialize.rs:114) | 0,25 h | klein, aendert das Feld nur im Fehlerfall |
| 9 | 2: `mean_rollout_diff`s toten `alphabeta = None`-Zweig entfernen (5179-5188) | 0,25 h | keins |
| 10 | 4.2: die rund 20 deutschen Bezeichner im PRODUKTIONS-Teil umbenennen; Testmodule getrennt oder gar nicht | 1,5 h | klein, mechanisch, breiter Diff |

### Kann bleiben

* Die vier `Diagnose`-Knoepfe dieser Dateien: Default AUS ist an jeder Stelle
  mit Fruehausstieg belegt, die Verzweigungen kosten bei AUS nichts.
* Der Schnitt `self_play_arena.rs` (4.1, Vorschlag 3): 20 Namen ueber der Naht
  sind zu viel fuer den Nutzen bei ein bis zwei verbleibenden Generationen.
* `serialize.rs` insgesamt: der exact-Pfad ist durch den erschoepfenden
  Struktur-Diff (1661-1930) besser abgesichert als der Rest des Baums.
* 1.7 (`monochrome_fallback`): betrifft nur den naeherungsweisen
  `json_to_state`-Pfad, dessen Bestandsverhalten laut serialize.rs:1204-1206
  bewusst unangetastet bleibt (Basislinien-Schutz).
* Die 14 Kopien der Phasen-Verzweigung: fuenf verschwinden groesstenteils mit
  Punkt 6, die restlichen liegen in Tests, wo eine eigene Kopie die
  Unabhaengigkeit der Pruefung ausmacht.
* `MOSAIC_TILING_PUNKTE_W` auf `Aktiv` trotz "gemessen wirkungslos":
  Definitionsfrage, kein Handlungsbedarf solange der Default 0,0 bleibt (1164).
