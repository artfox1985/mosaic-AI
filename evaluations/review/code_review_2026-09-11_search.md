# Code-Review: engine/src/net_mcts.rs (Suche)

**Datum** 2026-09-11. **Bereich** `engine/src/net_mcts.rs`, 10.795 Zeilen.
**Gelesen** Produktivteil 1-5397 vollstaendig; Testmodul 5399-10795 (169
`#[test]`) ueber Funktionsnamen, `#[ignore]`-Attribute und Stichproben
(5540-5610, 6329-6400), nicht Zeile fuer Zeile -- Aussagen darueber sind unten
so markiert. **Kontext** `knob_registry.rs` (68-188), `net_batcher.rs`
(272-301), `features.rs:1413`, `state.rs:65-111`,
`docs/architecture_reference.md:96-138`, Aufrufer-Greps ueber `engine/src`,
`engine/examples`, `engine/benches`. **Nur lesend**, kein Build, kein Test
gelaufen (laufende Mess-Kette).

---

## 1. Bugs und Korrektheitsrisiken

### 1.1 Netz-Fehler werden an elf Stellen still zu einem 0,5-Blatt (mittel)

`net.eval*()`-Fehler werden per `unwrap_or_else(|_| (vec![0.0; NUM_ACTIONS],
Vec::new(), ...))` abgefangen: 1924, 1947, 2017, 2108, 2121, 2142, 2154, 2165,
3631, 3930, 3949. Ein leerer `value`-Vec ergibt ueber `value_to_win_prob`
(1612-1615, `.first().copied().unwrap_or(0.0)`) exakt 0,5, die Logits sind
uniform. Ein intermittierender Inferenzfehler degradiert die Suche also zu
Zufall -- ohne jede Spur: Grep ueber `engine/src` nach
`eval_fail|EVAL_FAIL|eval_error` liefert **keinen Treffer**, es gibt keinen
solchen Zaehler im Baum. Sichtbar in Arena/Self-Play nur als "unerklaerlich
schwacher Lauf". Vorschlag: `static NET_EVAL_FAILURES: AtomicU64` plus einmalige
stderr-Warnung (Muster `warn_missing_opp_head_once`, 311-319) und
Snapshot-Getter (Muster `denial_tiebreak_stats`, 3133), ins Lauf-Artefakt. Rein
additiv.

### 1.2 Spec-Bereichspruefung asymmetrisch, `score_utility_b = 0` kommt durch (mittel)

`SearchConfig::from_spec_file` (522-730) prueft Bereiche nur fuer
`envelope_flush_w` (598), `special_row6_w` (620), `dead_cell_w`/`out_wild_w`
(643-654) und die zwei Enum-Felder (583-615). Ungeprueft bleiben
`implicit_minimax_alpha`, `long_row_init_shaping_w`, `score_utility_c`,
`score_utility_b`, `envelope_search_c`, `envelope_tiling_w`,
`envelope_tiling_value_w` und die fuenf `envelope_profile`-Werte.

Konkret: `score_utility_b` ist Divisor in `score_utility_term` (1751-1753,
`((x - x0) / b).atan()`). Bei `b = 0` und `c != 0` degeneriert der saettigende
Term zur Vorzeichenfunktion `±c` (`atan(±inf)`), bei `x == x0` wird er `NaN`.
`apply_score_utility` (1762-1791) reicht `NaN` durch -- `f64::clamp` gibt laut
Rust-Doku `NaN` zurueck, wenn `self` `NaN` ist. Ein `NaN`-Blattwert macht jeden
`score > best_score`-Vergleich in `gumbel_select_child` (3067) und `best_puct`
(2999) falsch; die Suche nimmt dann stumm Index 0. **Unklar**, ob `x == x0`
praktisch exakt eintritt (beide aus f32-Koepfen zurueckgerechnet); der
`±c`-Fall tritt sicher ein. Vorschlag: `score_utility_b > 0` erzwingen, uebrige
Felder nach dem `get_optional_non_negative`-Muster (643) pruefen -- vorher
`models/*.spec.json` und `models/frozen_*/*/spec.json` greppen.

### 1.3 Panic pro Wurzelentscheid statt einmal beim Agent-Aufbau (klein)

`apply_denial_tiebreak` (3387-3396) ruft
`assert_denial_tiebreak_config_not_conflicting` (3364-3374) bei **jeder**
Wurzelentscheidung (ueber `select_final_root_child`, 3413-3426). Die Pruefung
liest zwei prozessweit gecachte OnceLocks; ihr Ergebnis kann sich nie aendern.
Folgen: der Panic faellt mitten in einen Lauf statt beim Start, und er faellt
in einem Rayon-Worker -- der globale Mutex `perspective_divergence_stats`
(1347) wird dadurch **vergiftet**, jeder weitere `lock().unwrap()` in
1358/1364/1372 panikt nach. Aus einem Konfigurationsfehler wird eine Kaskade.
Vorschlag: Pruefung einmalig in einen `OnceLock` oder an den Agent-Aufbau.

### 1.4 `gumbel_final_root_action` laesst `g(a)` weg -- heute folgenlos (klein)

3081-3099 bewertet die Finalisten mit `ln(prior) + sigma(q)`, **ohne** das in
der Halbierungs-Rangfolge (4282) benutzte `g(a)`; mctx nimmt bei
`gumbel_scale != 0` denselben Score inklusive `g`. Geprueft: alle heutigen
Aufrufstellen von `net_search_drafting_action` uebergeben
`add_root_noise = false` (`self_play.rs:2199, 3861, 5375, 5649, 5765`,
`examples/kernbeweis_910002_probe.rs:114-142`, `examples/profile_clones.rs:42`);
Self-Play spielt ueber die Besuchsverteilung aus
`net_root_child_stats_and_policy` (4779), nicht ueber diese Funktion. **Heute
kein Fehler**, aber eine Falle fuer den naechsten Aufrufer. Vorschlag:
`debug_assert!` oder Kommentar an der Signatur, kein Umbau.

### 1.5 Geprueft und in Ordnung

- **Kein `std::env::var` in einer heissen Schleife**: direkte Zugriffe nur in
  197, 217, 256; alle 17 Knopf-Getter des Suchpfads liegen hinter `OnceLock`
  bzw. `AtomicU64` (167-177, 270-279).
- **Kein Determinismus-Bruch durch `HashMap`**: `p_base` (1552) wird nur per
  `.get()` gelesen, nie iteriert.
- **`plackett_luce_prob`s `unwrap()` (1445)** ist sicher: `counts` wird in
  1431-1436 mit demselben `color_idx5`-Filter gebaut und erst NACH dem
  Nachschlagen dekrementiert (1448).
- **Beide `expect` (2135, 2256)** sind durch `same_net` (2076) bzw.
  `need_other_pass` (2075) gedeckt; die zweite Aufrufstelle 3890 berechnet
  `need_other_pass` identisch.
- **Bonuschip-Umverteilung (1051-1070)** ist laengenkonsistent:
  `split_off(orig_pool_len.min(len))` laesst genau so viele Chips fuer das `zip`
  mit `unrevealed_idxs`, wie es unaufgedeckte Fabrik-Chips gibt.
- **K1 an der Wurzel**: `with_root_margin` (1799) laeuft erst NACH `make_node`
  der Wurzel (4027, 4446), das Wurzelblatt bekommt `x0 = None`. Korrekt, weil
  `score_utility_term(x0, x0, ..) = 0`.

---

## 2. Tote oder ueberholte Pfade

### 2.1 Unerreichbarer Restbudget-Zweig (belegt)

`build_gumbel_tree_inner` 4344-4352 ("Restbudget ... verteilen"). Beleg:
`keep = (current.len() / 2).max(2)` (4286) ist immer `>= 2`, `current` startet
mit `candidates.len() >= 2` (der Fall `<= 1` geht in Zweig 4235). `current.len()`
faellt also nie unter 2; die Schleife 4250 (`current.len() > 1 && budget_used <
sims`) kann nur ueber `budget_used >= sims` enden -- dann ist die Bedingung des
Restblocks falsch. Er laeuft nie.

Zweitens ist das `.max(2)` eine **Abweichung von mctx** (dort wird bis auf einen
Ueberlebenden halbiert), waehrend der Modulkommentar 2456-2460 "Alle Formeln
unten exakt aus der DeepMind-mctx-Referenzimplementierung uebernommen"
behauptet. Die Abweichung ist nirgends kommentiert. Vorschlag: toten Block
loeschen, `.max(2)` begruenden -- **den Wert selbst nicht anfassen**, das waere
eine Verhaltensaenderung mit Anker-Folgen.

### 2.2 PUCT-Legacy-Pfad (behalten)

`USE_GUMBEL_SEARCH = true` (2717) macht rund 260 Zeilen produktiv unerreichbar:
`build_net_tree`s Sim-Schleife (4436-4608), `best_puct` (2984-3005),
`best_root_child` (3018-3028, via 3424), `dirichlet`/`gamma`/`std_normal`
(5365-5396, einziger Aufrufer 4455). Aufrufer ausserhalb der Datei: nur
`lib.rs:703/718` (Manifest-Feld). Behalten -- kostet zur Laufzeit nichts, ist
der dokumentierte Rueckfall, und ein Ausbau hat bei ein bis zwei verbleibenden
Generationen keinen benannten Nutznieser.

### 2.3 Ruhende Toggles mit Messhistorie (behalten)

`ROUND_TRANSITION_SAMPLING` (95), `POINTS_UTILITY_WEIGHT` (119),
`MIRROR_OTHER_VAL` (941), `SHUFFLE_STACK_PEEK_IN_SEARCH` (957),
`BATCH_ROOT_EXPANSION` (991), `VALUE_SHRINK_ENABLED` (865),
`NUM_DETERMINIZATIONS` (1138), `LeafEval::Dfs` (76, Zweig 2414). Jeder traegt
einen GETESTET-Absatz mit Zahlen; der Wert liegt in der Historie, nicht im Code.
`BATCH_ROOT_EXPANSION` kommt ausserhalb der Datei nirgends vor (Grep), ist aber
ueber den Testparameter 4014 und den Paritaetstest 7418 gedeckt.

### 2.4 Doku-Drift auf diese Datei

- `knob_registry.rs:182-185` verweist fuer `MOSAIC_UNLOCK_SHAPING_W`,
  `MOSAIC_UNLOCK_BETA`, `MOSAIC_ENDAWARE_W`, `MOSAIC_MUSTERREIHEN_W` auf
  `net_mcts.rs:1257/1322/1323`. Grep nach `MOSAIC_` in der Datei findet keinen
  dieser vier Namen -- die Stubs sind mit dem Shaping-Umzug (Verweis 25-27) nach
  `shaping.rs` gewandert.
- `docs/architecture_reference.md:111-115` nennt `net_mcts.rs:987/1003/3952/
  4010/4139/4448/904`; heute sind es 1029, 1065, 1049, 4020/4440, 4078/4208/4521
  und 957. Die **Vollstaendigkeit** stimmt: die Tabelle fuehrt genau die vier
  `determinize_dome_pool`-Aufrufe plus den Chip-`shuffle`, mehr gibt es nicht.
- `SearchConfig::from_env`s Doc (488-494) sagt, die Funktion werde "je
  Partie-Einstieg GENAU EINMAL" gerufen; `net_search_with_tree:4982` ruft sie
  **pro Zug** (GUI-/Debug-Pfad). Perf-technisch egal, die Aussage ist falsch.
- 2468-2515 ist **ein** Doc-Kommentar am `GUMBEL_C_SCALE_CELL` (2516), in dem
  zwei Aeren verschmolzen sind: der Kopf "GEMESSEN UND BESTAETIGT (2026-07-29)
  -- bleibt 1.0" dokumentiert eine nicht mehr existierende Konstante, ab 2497
  folgt die Zellen-Doku mit der Gegenmessung ("Fuer Gleichgewicht waere
  `c_scale` rund 0,36"). Der Leser bekommt erst "bestaetigt 1,0", drei Absaetze
  spaeter "0,36 waere richtig".

---

## 3. Optimierungspotenzial (belegt am Codepfad)

### 3.1 Globaler Mutex im Blattpfad, obwohl der Knopf aus ist (groesster Posten)

`try_batched_pair_ex` (1874-1890) laeuft bei jedem Knoten des dominanten Pfads
(`make_node` 2105, `net_leaf_eval` 1944). Es steigt frueh nur bei
`points_utility_w() != 0.0` aus (1882) -- Default ist 0,0, also nicht. Danach
`net_batcher::lookup(net)` (1885), und das ist
`registry().lock().unwrap().get(&key)` (`net_batcher.rs:298-301`) auf einem
prozessglobalen `Mutex<HashMap<..>>` (`net_batcher.rs:272`). `lookup` prueft
`interleave_enabled()` nicht; bei ausgeschaltetem Knopf ist die Registry laut
`ensure_batcher_for` (`net_batcher.rs:283-291`) **beweisbar leer**. Die Sperre
wird also je expandiertem Knoten, in jedem Rayon-Faden, fuer ein garantiert
leeres Nachschlagen genommen. Vorschlag:
`if !crate::net_batcher::interleave_enabled() { return None; }` am Anfang von
`try_batched_pair_ex` und `try_batched_single_eval` (1838);
`interleave_enabled` ist `pub(crate)`. Ergebnis beweisbar identisch. **Unklar**,
wie gross der Gewinn ist -- nicht gemessen (Kette laeuft).

### 3.2 Vermeidbarer `GameState`-Klon je expandiertem Knoten

`make_node` (2044) bekommt `state: GameState` als **Eigentum** und klont ihn
trotzdem, nur um `current_player` zu spiegeln (2090, im Hybrid-Zweig 2147).
`features_for_net` gibt laut `features.rs:1413` einen eigenen `Vec<f32>` zurueck
und haelt keine Referenz -- der Klon laesst sich durch Umschalten im eigenen
Zustand und Zuruecksetzen ersetzen. `GameState` (`state.rs:65-111`) traegt neun
`Vec` plus `Bag`, `Tower`, `LargeFactory` und zwei `PlayerBoard`; ein Klon sind
zweistellig viele Heap-Allokationen. Der Zaehler existiert bereits
(`note_gamestate_clone()`, 2089, samt `examples/profile_clones.rs`). In
`net_leaf_eval` (1932) ist derselbe Klon nicht vermeidbar (`&GameState`).

### 3.3 `HashMap` je Knotenexpansion in `build_untried_actions`

1552 baut `HashMap<usize, f32>` aus `unique_ids`/`base_probs` -- in Runde 1 laut
Modulkommentar 2454 rund 150-195 Eintraege, pro Knoten gebaut und verworfen.
`unique_ids` ist unmittelbar davor sortiert (1545); ein `binary_search` mit
Index in `base_probs` liefert denselben `f32` ohne Allokation.

### 3.4 Kleinere, der Vollstaendigkeit halber

`gumbel_select_child` (3052) -> `improved_policy` (2959) allokiert vier `Vec`
je Aufruf (2821, 2962, 2946-2949), einmal je Baumebene je Sim (4064) -- bei 400
Sims und Tiefe 3 rund 5.000 Allokationen je Zug, **klein gegen die
Netz-Kosten**. Gleiche Klasse: `&current.clone()` je Halbierungsphase (4258,
4345). Zweiter globaler Sperrpunkt je Knoten neben 3.1:
`record_perspective_divergence` (1355-1361) nimmt bei **jedem** netzbewerteten
Blatt (2264, 1962) unbedingt einen Mutex, per Entwurf ohne Feature-Flag
(Modulkommentar 1338-1343). Ein Umbau auf `thread_local`-Akkumulation waere
bis auf die Summationsreihenfolge zahlengleich, also **nicht** als bitidentisch
verkaufbar.

---

## 4. Struktur und Nachvollziehbarkeit

### 4.1 Dateigroesse und der einzige risikofreie Schnitt

10.795 Zeilen, davon 5.396 Testmodul (5399-10795, exakt die Haelfte).
**Vorschlag mit Nahtbreite null:** das Testmodul per
`#[cfg(test)] #[path = "net_mcts_tests.rs"] mod tests;` in eine Nachbardatei
verschieben. Ein `#[path]`-Kindmodul behaelt exakt dieselbe
Sichtbarkeitsbeziehung zum Elternmodul wie ein Inline-Modul -- kein Item muss
`pub(super)` werden, `use super::*` (5405) bleibt unveraendert.

**Gegen einen echten Modulschnitt des Produktivteils:** die Naht laeuft in jedem
plausiblen Zuschnitt durch `struct Node` (1453-1509) und seine **16 Felder**.
Gumbel-Kern (2450-3099), Tie-Break (3101-3551), Debug-Trace (3553-3827) und die
Analyse-Dicts (5006-5334) lesen alle direkt Node-Felder: 17 Namen ueber der
Naht, jeder heute privat. Zu breit fuer den Restnutzen.

Der einzige Produktiv-Block mit schmaler Naht ist die reine Blattwert-Arithmetik
(`calibrate_win_prob*` 747-762, `opp_aware_points_utility` 779,
`value_to_win_prob` 1612, `blended_leaf_win_prob*` 1644-1695,
`score_margin_points`/`score_utility_term`/`apply_score_utility` 1740-1791,
`apply_value_shrink` 897-916): sie kennt `Node` nicht -- bis auf
`with_root_margin` (1799), das aus `&Node` nur drei Werte liest und sie ebenso
als Parameter nehmen koennte. Danach waere die Naht drei Namen breit.

### 4.2 Deutsche Bezeichner (Regel 2026-08-24)

Produktivteil, sechs Stellen, alle in der Farb-Denial-Sonde: 3441
`COLOR_DENIAL_PROBE_FENSTER`, 3442 `COLOR_DENIAL_PROBE_STOERBAR`, 3510
`bedarf`, 3514 `stoer_b`/`floor_b`, 3518 `fenster`, 3519 `stoerbar`, 3529
`stoer_a`/`floor_a`. Vorschlag: `..._WINDOW`/`..._DISRUPTABLE`, `demand`,
`disruption_b`, `window`, `disruptable`. `color_denial_probe_stats` (3467) gibt
ein anonymes Tupel zurueck -- die Namen sind rein intern, risikoloser Umbau.
Testmodul: `env_knoepfe_defaults_sind_bestandsverhalten` (5544),
`alte_unlock_knoepfe_sind_zurueckgebaut` (8665),
`ownership_scale_je_kriterium_aendert_den_shift_gegenueber_flachem_default`
(10772). **Nicht umbenennbar:** das Spec-Feld `heuristik_variante` (545, 691)
ist ein externes Dateiformat -- ein Umbenennen macht jede eingefrorene Spec in
`models/frozen_*/*/spec.json` ungueltig.

### 4.3 Prozessglobale Knoepfe gegen die Pro-Seite-`SearchConfig`

`SearchConfig` traegt 14 Pro-Seite-Felder (379-475). Daneben liest der Suchpfad
17 prozessglobale Getter: 249, 270, 277, 357, 363, 822, 839, 1159, 2520, 2587,
2613, 2661, 2683, 2697, 2706, 3449, 3456. Der Code benennt das Problem selbst an
einer Stelle (2510-2515: "prozessglobal, also NICHT pro Seite setzbar ...
braucht die Migration in `SearchConfig`"). Von den 17 aendert nur
`gumbel_c_scale` (2520) die Blattwert-Ordnung direkt und hat einen benannten
Nutznieser (`PREREG_prior_blind_spot.md` par.G3); die uebrigen 16 sind
Diagnose- oder Aus-Default-Knoepfe.

### 4.4 Tests: Namen halten; zwei Sonden sind keine Tests

Stichprobe von acht Namen gegen ihren Rumpf (5544, 5578, 6096, 6164, 6362,
6384, 6921, 6940): alle pruefen, was ihr Name sagt, keine Luecke gefunden --
**nicht Zeile fuer Zeile geprueft**. Zwei `#[ignore]`-Eintraege sind
Einmal-Messsonden, keine Tests (5449, 7253), ein dritter ein Benchmark (7498, im
Kommentar 7490-7493 selbst so bezeichnet). Vorschlag: Sonden nach
`engine/examples/` (Praezedenz `profile_clones.rs`), Benchmark nach
`engine/benches/`. Ein vierter ist seit dem Fixture-Wechsel dauerhaft
abgeschaltet (7786, Grund im `#[ignore]`-Text: "Schwelle stammt aus der
v10-Aera ... erst neu kalibrieren") -- offene Wiedervorlage, entweder neu eichen
oder loeschen.

---

## 5. Priorisiert: was vor Projektende gemacht werden sollte

Grundhaltung: bei ein bis zwei verbleibenden Generationen ist fast alles hier
Doku- und Beobachtbarkeitsarbeit, keine Suchchirurgie. Jede
Verhaltensaenderung zieht einen Anker-Invarianz-Lauf nach sich
(`/mosaic-anchor-invariance`).

| # | Punkt | Stelle | Aufwand | Risiko |
| --- | --- | --- | --- | --- |
| 1 | Netz-Eval-Fehler zaehlen, einmalige Warnung, Zaehler ins Artefakt | 1.1 | 1-2 h | niedrig, rein additiv |
| 2 | Toten Restbudget-Block loeschen, mctx-Abweichung `.max(2)` kommentieren | 2.1 | 0,5 h | niedrig, Block nachweislich unerreichbar |
| 3 | Doku-Drift beheben (knob_registry 182-185, architecture_reference 111-115, from_env-Doc 488-494, Doppel-Doku 2468-2515) | 2.4 | 1 h | null |
| 4 | Testmodul per `#[path]` auslagern | 4.1 | 0,5 h | sehr niedrig, Sichtbarkeit unveraendert |
| 5 | `interleave_enabled`-Waechter vor `net_batcher::lookup` | 3.1 | 0,5 h | niedrig, Anker-Invarianz-Lauf als Beleg |
| 6 | Spec-Bereichspruefungen ergaenzen, zuerst `score_utility_b > 0` | 1.2 | 1 h | mittel, erst bestehende Specs greppen |
| 7 | E3/E3b-Konfliktpruefung einmalig statt je Wurzelentscheid | 1.3 | 0,5 h | niedrig |
| 8 | Deutsche Bezeichner der Farb-Sonde umbenennen | 4.2 | 0,5 h | niedrig, alle datei-intern |
| 9 | Flip-Klon in `make_node` entfernen | 3.2 | 1 h | mittel, Byte-Identitaet muss belegt werden |
| 10 | `HashMap` in `build_untried_actions` durch `binary_search` ersetzen | 3.3 | 1 h | mittel, gleiche Begruendung wie 9 |

**Kann bleiben, bewusst:** PUCT-Legacy samt `dirichlet`/`gamma`/`std_normal`
(2.2, kein Nutznieser); alle ruhenden Toggles mit GETESTET-Absatz (2.3, die
Kommentare sind das Artefakt); ein Modulschnitt des Produktivteils (4.1, Naht 17
Namen breit); `heuristik_variante` als Spec-Feldname (4.2); der
`record_perspective_divergence`-Mutex (3.4, ein Umbau waere nicht
bitidentisch). **Grenzfall:** `gumbel_c_scale` nach `SearchConfig` migrieren
(4.3) ist sachlich richtig, lohnt aber nur, wenn eine Arena damit noch geplant
ist -- dann als OPTIONALES Spec-Feld mit Default 1,0 (Muster `dead_cell_w`,
643-654), sonst brechen alle bestehenden Specs. 2-3 h, Risiko mittel.
