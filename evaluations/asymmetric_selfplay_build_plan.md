# BAUPLAN: asymmetrisches Self-Play (Klasse W "Wuerfel-Kuppelplatten", Klasse S "Stoerer")

Stand 2026-10-01, NUR Plan, nichts gebaut, nichts ausgefuehrt (keine Builds, keine Tests, keine
Skripte). Grundlage: `evaluations/PREREG_asymmetric_selfplay.md` (ganz gelesen), `CLAUDE.md`,
`docs/engine_manual.md` (ganz gelesen), Code in `engine/src` (Stellen unten), Auszuege aus
`PREREG_dome_stack_information_sets.md` (par.4, par.4b, par.15e-g), `PREREG_search_rng_split.md`
(Kopf), `models/v34.recipe.json`, `models/v33_generation.spec.json`,
`evaluations/review/code_review_2026-09-26_verification.md` (#11).

**Legende (REGEL 0):**
* `datei:zeile` = in dieser Sitzung gelesen.
* **HERLEITUNG** = aus gelesenen Stellen abgeleitet, nicht gemessen.
* **UNGEPRUEFT** = Annahme, beim Bau zu pruefen.
* **VORSCHLAG** = Bauentscheid dieses Plans, nicht vom Nutzer festgelegt.

---

## 0. Kurzfassung

1. **Platte und Rotation festnageln ueber einen Zustands-Pin** (`GameState::dome_dice_pin`),
   den `drafting_actions` (game.rs:809, laut Kommentar "Single Source of Truth fuer Game-Loop und
   MCTS", game.rs:807-808) auswertet. Die Suche baut ihre Kandidaten an JEDEM Knoten aus
   `drafting_actions(state)` (net_mcts.rs:2881), also wirken Wurzel-Beschraenkung UND
   Rotationsnagel im Baum ohne einen einzigen Eingriff in `net_mcts.rs`. Vorbild fuer ein
   Nicht-Spiel-Feld im `GameState`: `extended_action_nodes` (state.rs:116-134).
2. **Der erzwungene Plattenzug laeuft innerhalb EINER Schleifeniteration** von
   `unified_game_loop` (self_play.rs:4244), so wie heute der Sammelaufloeser
   `resolve_and_apply_stack_draw_with` (self_play.rs:1118-1284) mehrere `apply_drafting`-Aufrufe in
   einer Iteration macht. Damit zaehlt er weder `move_number` noch `round_move_index` hoch und
   schreibt keinen Record.
3. **Ausloeser (VORSCHLAG, Nutzerfrage F1):** das WANN eines Plattenzugs entscheidet weiter die
   normale Suche der W-Seite (100 Sims). Waehlt sie eine Plattenaktion (`ChooseDomeSlot` oder
   `DrawStackPeek`), ersetzt der Wuerfel Quelle, Platte, Tiefe und Rotation; den Platz sucht eine
   eigene 600-Sims-Suche.
4. **Stapeltiefe ueber den GANZEN Stapel wuerfeln, wie festgelegt** (VORSCHLAG, Nutzerfrage F3).
   Die Alternative "nur ueber den unbekannten Teil" entartet nach dem ersten tiefen Zug, weil der
   unbekannte Teil dann fuer den Rest der Partie 0 ist (Abschnitt 3.3).
5. **Korrektur an der Prereg-Herleitung:** die Kosten eines Stapelzugs in Runde 1 sind nicht 7,
   sondern durch den Startstand 5 gedeckelt (board.rs:286, board.rs:345-349): erwartet rund 4,2
   Punkte fuer den ersten R1-Stapelzug, und ein zweiter R1-Stapelzug ist nach d >= 5 gratis
   (Abschnitt 11).
6. **Klasse S:** der lambda-Blend wirkt heute nur bei `w != 0` (net_mcts.rs:3061-3063) und immer
   fuer den ZIEHENDEN am Blatt (net_mcts.rs:3779), also in der Suche fuer beide Seiten. Fuer S
   braucht es `w` UND `lambda` je Seite in `SearchConfig` und einen Blend nur aus Sicht des
   Stoerers; Review #11 (net_mcts.rs:3352-3359) haengt am prozessweiten `w`-Waechter und muss mit.

---

## 1. Code-Lage (geprueft)

### 1.1 Plattenzug in Teilschritten

* `Action` (moves.rs:156-191): `ChooseDomeSlot(PlaceDomeTileMove)` (Auslage: Platte plus Platz,
  Rotation Platzhalter 0), `DrawStackPeek` (eine Platte ziehen, -1 Punkt), `ChooseDrawStackSlot`
  (gezogene Platte plus Platz, `return_order` mit), `ChooseReturnFirst(usize)`,
  `ChooseDomeRotation(u32)`.
* Ablauf Auslage: `ChooseDomeSlot` setzt `pending_dome_choice = FromDisplay` ohne Spielerwechsel
  (game.rs:1096-1107), `ChooseDomeRotation` fuehrt aus und ruft `switch_player` (game.rs:1141-1164).
* Ablauf Stapel: `DrawStackPeek` je Platte (game.rs:1108-1112, Ausfuehrung game.rs:218-242), dann
  `ChooseDrawStackSlot` (game.rs:1113-1140). Bei >= 2 Restplatten UND aktivem Knotentor oeffnet es
  `pending_return_order` (game.rs:1123-1131, Tor game.rs:756-758), sonst direkt
  `pending_dome_choice = FromDrawStack` mit dem eingereichten `return_order` (game.rs:1132-1138).
  `ChooseReturnFirst` setzt den Kopf, Rest in Ziehreihenfolge (game.rs:1067-1095), Kandidaten
  `0..min(rest, 3)` (game.rs:781-784, `RETURN_ORDER_MAX_PERMUTED = 3` self_play.rs:651).
  `ChooseDomeRotation` fuehrt `execute_draw_from_stack` aus (game.rs:1154-1160).
* Rangfolge der offenen Zustaende in `drafting_actions` und in der Pruefung von `apply_drafting`:
  Mondknoten, Rueckgabeknoten, Rotation, laufender Stapelzug (game.rs:817-880 und 978-1004).
  Waehrend eines laufenden Stapelzugs sind NUR `DrawStackPeek` und `ChooseDrawStackSlot` legal
  (game.rs:869-880).
* Legalitaet: jede Auslage-Platte auf jeden freien Platz, alle vier Rotationen (game.rs:129-174,
  Kommentar "aktuell immer alle 4"). Dasselbe fuer gezogene Platten (game.rs:432-497).
* Policy-IDs: `choose_dome_slot` 328 + Auslage-Index*9 + Platz, `choose_draw_stack_slot`
  355 + min(pending_index, 3)*9 + Platz, Rotation 391 + rot/90, Peek 405 (features.rs:2145-2156,
  `MAX_PENDING_STACK_TILES = 4` features.rs:2009). **Folge:** ab der 4. gezogenen Platte teilen sich
  alle gezogenen Platten dieselben 9 IDs.

### 1.2 Der Stapel als Datenstruktur

* `dome_tile_pool: Vec<DomeTile>`, Index 0 = OBEN (Ziehseite): gezogen wird mit `remove(0)`
  (game.rs:231), zurueckgelegt mit `push` ans Ende = UNTEN (game.rs:349-355).
* Reihenfolge innerhalb einer Rueckgabe: erster Eintrag von `return_order` wird zuerst
  zurueckgelegt und liegt damit am naechsten zur Ziehseite (moves.rs:59-66; mechanisch:
  aufeinanderfolgende `push`, game.rs:350-354).
* Wissensstand: `dome_pool_known_blocks` beschreibt lueckenlos das SUFFIX des Pools, aeltester Block
  zuerst (state.rs:74-86). Unbekanntes Praefix = Poollaenge minus Summe der Blocklaengen
  (state.rs:169-172). Ziehen von oben frisst bei leerem Praefix eine Position des AELTESTEN Blocks
  (state.rs:178-188), jede Rueckgabe legt EINEN neuen Block mit `returner` = Ziehender an
  (state.rs:194-199, Aufruf game.rs:361).
* Auffuellen der Auslage: nach jeder Startsetzung von oben an dieselbe Stelle (game.rs:668-673),
  bei der Rundenvorbereitung von oben bis 3 (game.rs:1361-1366), beide mit
  `note_dome_pool_draw_from_top`. Waehrend der Runde KEIN Nachfuellen (engine_manual.md Abschnitt 2).
* Kosten: `apply_paid_cost(-1)` je Peek (game.rs:226), zahlt nur den vorhandenen Rest, auch
  `score_unclamped` (board.rs:345-349). Startstand 5 (board.rs:286). Punkte entstehen sonst nur
  im Tiling (round_end.rs:311 in `execute_full_tiling`, round_end.rs:385 in
  `check_special_trigger`), bei der Rundenstrafe (game.rs:1338-1350) und der Endwertung
  (game.rs:1381). Waehrend des Draftings aendert sich der Stand also nur durch eigene Peeks
  (HERLEITUNG aus der vollstaendigen Liste der Aufrufstellen, grep `apply_score|apply_paid_cost`).

### 1.3 Was die Suche vom Stapel sieht

* Einmal je Suche wird an der Wurzel determinisiert, Betrachter = `current_player`
  (net_mcts.rs:2222-2231, `DETERMINIZE_ROOT_HIDDEN_INFO = true` net_mcts.rs:2210).
* `determinize_dome_pool` (state.rs:265-306): unbekanntes Praefix voll gemischt, EIGENE Bloecke
  unveraendert, FREMDE Bloecke nur in sich permutiert, Typ der obersten Platte wiederhergestellt
  (state.rs:308-334). Das entspricht der Regel engine_manual.md 4A ("order ... known only to the
  player who returned them; the opponent sees the fronts") und PREREG_dome_stack_information_sets
  par.4.
* Im Baum wird beim simulierten Peek NICHT neu gemischt (`SHUFFLE_STACK_PEEK_IN_SEARCH = false`,
  net_mcts.rs:2138): ein Peek im Baum liest die oberste Platte der determinisierten Welt.
* Das Netz sieht den Wissensstand als elf Werte (Praefixlaenge, eigene/fremde Blocklaengen und
  Typzaehler, Typen der obersten 4 Positionen des obersten eigenen Blocks), features.rs:89-162.
  Identitaeten sieht es nicht.

### 1.4 Die Schleife und ihre Zufallsstroeme

* `unified_game_loop` (self_play.rs:4244-5070): je Drafting-Entscheid `move_number += 1`,
  `round_move_index += 1` (4417-4426), Such-RNG aus `derive_search_seed(game_seed, move_number)`
  (4441-4444), Entscheid `pcfg.agent.decide` (4450), dann Rueckgabe-Streuung im Knotenweg
  (4473-4494), Weg C / Ausflug-Abweichung (4545-4614), Ausflug-Reservoir (4632-4667),
  Record-Vorbereitung VOR dem Apply (4671-4676), Apply ueber `apply_chosen_action_with`
  (4725-4737), Record-Bau (4789-4835).
* `apply_chosen_action_with` (self_play.rs:1389-1407): bei `DrawStackPeek` entweder Sammelaufloeser
  oder (Knotentor an bzw. `MOSAIC_STACK_DRAW_RESEARCH=1`) nur EIN Peek, Rest per Schleife. Das
  v34-Rezept setzt `MOSAIC_STACK_DRAW_RESEARCH=1` (models/v34.recipe.json, `env`). Heute ist ein
  Plattenzug im Sockel also eine FOLGE von Schleifenentscheiden, jeder mit Suche und Record.
* Rueckgabe-Streuung im Knotenweg: nur `recording`, nur reine `ChooseReturnFirst`-Liste, nur
  Runde 1-4, nur ab 3 Restplatten, eigener Strom `game_seed ^ RETURN_ORDER_NODE_SEED_DISTINGUISHER`;
  ersetzt `d.chosen` und setzt `return_order_randomized` (self_play.rs:4473-4494), Policy-Maske in
  corpus_dataset.py:1669-1670. Rezept: `return_order_random_p 0.81` (models/v34.recipe.json).
* Distinguisher heute: self_play.rs:896, 903, 2717, 2751, 3095, 3976 plus der Eindeutigkeitstest
  self_play.rs:13135-13158. Helfer `derive_search_seed` und `game_weight_from_seed` in
  shaping.rs:368 bzw. shaping.rs:344.
* Sims: `net_effective_sims` gibt bei Gumbel die Basis-Sims unveraendert zurueck
  (net_mcts.rs:4335, 4356-4358). 600 Sims sind also 600 Sims.
* Startspieler je Partie: `rng.random_range(0..2)` aus dem Partie-RNG (self_play.rs:7018).
* Vorbild Seitenwahl: `asym_preference_side` (self_play.rs:2716-2724), Hash aus
  `game_seed ^ Distinguisher`, Partie-RNG unberuehrt.

---

## 2. Regeln, auf die der Plan sich stuetzt (engine_manual.md)

* 18 Platten, 3 offen, Rest verdeckt; Auslage waehrend der Runde nicht nachgefuellt, Ausnahme nach
  den Startsetzungen (Abschnitt 2).
* Stapelzug: je Ziehung 1 Punkt, beliebig oft, eine behalten, Rest in beliebiger Reihenfolge unter
  den Stapel; Reihenfolge kennt nur der Zuruecklegende, der Gegner sieht die Vorderseiten; bei 0
  Punkten weitere Ziehungen gratis, ausdruecklich so belassen (Abschnitt 4A).
* Je Spieler genau 2 Platten in Runde 1-4, keine in Runde 5; Position und Rotation frei
  (Abschnitt 4A). Startsetzung vor Runde 1 zaehlt nicht mit (Abschnitt 3).
* Kuppel 3x3 Plaetze (Abschnitt 2), also 1 Startplatte plus 8 Platten je Spieler.

**HERLEITUNG Stapelgroesse zu Rundenbeginn** (aus state.rs:555-556 "15 verdeckt",
game.rs:668-673 zwei Nachzuege nach den Startsetzungen, game.rs:1361-1366 Auffuellen auf 3, und
genau 4 gelegten Platten je Runde): Platten ausserhalb der Kuppeln zu Beginn von Runde r =
16 - 4(r-1), davon 3 in der Auslage. **Stapel R1 13, R2 9, R3 5, R4 1**, unabhaengig davon, wie
gezogen wurde, weil zurueckgelegte Platten im Umlauf bleiben. Innerhalb einer Runde sinkt der
Stapel um jede vom Stapel GELEGTE Platte. Die Prereg (par.2 "Folgen") nennt dieselben Zahlen.

**HERLEITUNG "nie beide Quellen leer, solange die W-Seite eine Platte schuldet":** in Runde r
liegen 3 + S_r Platten aus, gebraucht werden 4, und jede Platzierung verbraucht genau eine. In
Runde 4 gilt Gleichheit (4 = 4). Also ist bei jeder offenen Pflicht mindestens eine Quelle
nicht leer. Beim Bau als `debug_assert` absichern, nicht als stillen Rueckfall.

**HERLEITUNG Plaetze:** die i-te Pflichtplatte (i = 1..8) der W-Seite hat 9 - i freie Plaetze
(8, 7, ..., 1). Die letzte Platte in Runde 4 hat genau EINEN Platz: dort braucht es keine Suche.

---

## 3. Der Stapelaufbau unter der Wuerfel-Klasse (Analyse)

### 3.1 Bild des Stapels

```
oben (Index 0, Ziehseite)                                       unten (Vec-Ende)
[ unbekanntes Praefix | Block 1 (aeltester) | Block 2 | ... | Block k (juengster) ]
  niemand kennt es       returner X           returner Y        returner Z
  (Typ der obersten      eigener Block: Reihenfolge bekannt
   Platte oeffentlich)   fremder Block: nur Menge bekannt
```

Ziehen frisst zuerst das Praefix, danach den aeltesten Block von oben (state.rs:178-188).
Rueckgaben haengen unten an (state.rs:194-199). Das Auffuellen der Auslage zur Rundenvorbereitung
zieht ebenfalls von oben (game.rs:1361-1366): **zurueckgelegte Platten kommen also ueber die
Auslage wieder ans Licht, sobald das Praefix aufgebraucht ist.**

### 3.2 Das Beispiel des Nutzers, Schritt fuer Schritt

Annahme: die G-Seite hat in R1 vorher nicht vom Stapel gelegt (sonst kleinere Zahlen).

1. R1, erste W-Platte, Muenze "Stapel", max = min(keine Obergrenze, 13) = 13, Wuerfel d = 13
   (Wahrscheinlichkeit 1/2 * 1/13, rund 3,8 Prozent der ersten W-Platten in R1, HERLEITUNG).
2. 13 Peeks. Kosten: Stand 5 -> 0 nach 5 Peeks, Peeks 6-13 gratis (board.rs:345-349). Pool leer.
3. Behalten: die 13. gezogene = die unterste Platte des urspruenglichen Stapels. Platzsuche
   @600 ueber 8 freie Plaetze, Rotation festgenagelt.
4. 12 Restplatten. Knotentor an (414er-Netz, UNGEPRUEFT fuer v33-b01, siehe F-Liste) und
   Rest >= 2: `ChooseReturnFirst` ueber die Positionen 0..2 der Ziehreihenfolge (game.rs:781-784).
   Mit `return_order_random_p = 0.81` faellt die Streumuenze (Rest 12 >= 3, Runde 1).
5. Danach: Pool = 12 Platten, EIN Block {len 12, returner W}, Praefix 0. W kennt die Reihenfolge,
   G die Menge (beide haben alle 13 Vorderseiten gesehen, engine_manual 4A). **Fuer den Rest der
   Partie gibt es kein unbekanntes Praefix mehr** (Praefix waechst nie, nur Bloecke kommen hinzu).
6. Zweite W-Platte in R1, Muenze "Stapel": max = min(keine, 12) = 12, d gleichverteilt 1..12.
   Gezogen wird aus dem EIGENEN Block in bekannter Reihenfolge. Kosten 0 (Stand schon 0).
   d = 12 zieht den ganzen eigenen Block erneut, behaelt dessen letzte Platte und legt 11 als
   neuen Block {11, W} zurueck. Regelkonform (4A: "beliebig oft"), fuer einen echten Spieler
   sinnlos (er zieht Bekanntes), fuer W aber ohne Wahl und hier gratis.
7. Rundenvorbereitung R2: die Auslage bekommt die obersten 3 des W-Blocks. Deren Reihenfolge hat W
   (mit dem Rueckgabeknoten bzw. der Streumuenze) bestimmt: **die W-Seite bestimmt damit mit, welche
   Platten in R2 offen liegen**. Der Pool R2 hat 9 Platten, alle aus bekannten Bloecken.

### 3.3 Was die Variante "d nur ueber den unbekannten Teil" anrichten wuerde

Nach Schritt 5 ist das Praefix fuer immer 0. Mit max = min(Obergrenze, Praefix) gaebe es fuer W
keinen Stapelzug mehr; die Muenze muesste auf die Auslage ausweichen (bzw. bei leerer Auslage
gegen die Variante verstossen). Das veraendert die Quellenverteilung der W-Seite in genau den
Partien mit einem fruehen tiefen Zug und koppelt sie an den Wuerfel des ersten Zugs.
**HERLEITUNG**, ungemessen.

### 3.4 Wie oft der "sinnlose" Fall ueberhaupt eintritt (HERLEITUNG, Annahmen genannt)

Annahmen: beide W-Platten der R1 vom Stapel (Wahrscheinlichkeit 1/4 bei Muenze 50:50), G zieht
dazwischen nicht vom Stapel. Erste Tiefe d1 gleichverteilt 1..13, danach Praefix 13 - d1, Pool 12.
* P(zweite Ziehung erreicht den eigenen Block) = E[(d1 - 1)/12] = 0,5.
* P(Stand schon 0 bei der zweiten Ziehung) = P(d1 >= 5) = 9/13, rund 0,69.

Also: in rund der Haelfte dieser Faelle zieht W in R1 in Bekanntes, und meist gratis. In R2 und
R3 begrenzen die Obergrenzen 7 bzw. 3 die Tiefe, aber ab R2 ist der Stapel nach einem tiefen
R1-Zug ganz bekannt; jeder W-Stapelzug dort ist ein Zug in einen bekannten Block und kostet
(Stand nach R1-Tiling meist > 0, UNGEPRUEFT) echte Punkte.

### 3.5 Bezug zum heutigen Verhalten der Live-Suche

`PREREG_dome_stack_information_sets.md` par.15e/15g: die Live-Suche zieht schon heute in ihren
eigenen Block (gemessen +0,689 Ziehungen je Partie mit Variante A; Browser-Partie: R3 fuenf
Ziehungen in den eigenen Block, um eine bekannte Platte an Position 5 zu erreichen). "In den
eigenen Block ziehen" ist also keine Stellung, die nur der Wuerfel erzeugt.

---

## 4. Bauentwurf Klasse W

### 4.1 Zustands-Pin (game.rs, state.rs)

Neuer Typ (VORSCHLAG, Namen englisch):

```rust
pub enum DiceSource { Display { tile_id: usize }, Stack { chosen_id: usize } }
pub struct DomeDicePin {
    pub player: usize,
    pub source: DiceSource,
    pub rotation: u32,             // 0/90/180/270
    pub return_first: Option<usize>, // vorab gewuerfelter Rueckgabekopf (siehe 4.4 Schritt 6)
}
// GameState: pub dome_dice_pin: Option<DomeDicePin>,  // None = Bestand
```

* Gesetzt NUR in der Schleife (4.4), geloescht in `apply_drafting` beim erfolgreichen
  `ChooseDomeRotation` (game.rs:1141-1164) und vorsorglich beim Rundenwechsel.
* `drafting_actions` (game.rs:809-897), nur wenn `pin.player == current_player`:
  * offener Rueckgabeknoten und `pin.return_first = Some(p)`: nur `ChooseReturnFirst(p)`;
  * offene Rotation: nur `ChooseDomeRotation(pin.rotation)`;
  * laufender Stapelzug: nur `ChooseDrawStackSlot(m)` mit `m.chosen_id == chosen_id`, KEIN
    `DrawStackPeek`;
  * nichts offen und `Display`: nur `ChooseDomeSlot(m)` mit `m.dome_tile_id == tile_id`.
  * Ergibt die Filterung eine leere Liste, ist das ein Engine-Fehler: `debug_assert!` plus
    Rueckfall auf die ungefilterte Liste (nie stilles `Pass`).
* `apply_drafting` (game.rs:938-1004): zusaetzlicher Waechter vor dem `match`, der jede Aktion
  ablehnt, die `drafting_actions` unter dem Pin nicht anbietet (Projektregel "Aenderungen am
  Spielbrett validieren"). Zustand bleibt bei Ablehnung unveraendert.
* Konstruktionsstellen: genau zwei `GameState { ... }` (state.rs:558, serialize.rs:1271), beide
  `dome_dice_pin: None`. Nicht in `state_to_json` (Records und Netz-Eingabe unveraendert);
  optional in `state_to_json_exact` als `dome_dice_pin_exact` wie `extended_action_nodes_exact`
  (serialize.rs:1445, 1762), damit ein Mitten-im-Zug-Schnappschuss rund laeuft.
* **Warum ein Zustandsfeld und keine Such-Option:** die Wurzel nimmt ihre Kandidaten aus
  `drafting_actions(state)` (net_mcts.rs:2881, ueber `build_untried_actions` aus `make_node`,
  net_mcts.rs:3761), und jeder Baumknoten traegt einen Klon des Zustands (Node.state,
  net_mcts.rs:2807). Der Pin wandert deshalb automatisch bis zum Rotationsknoten mit und
  verschwindet mit dessen Anwendung. Die Wurzel-Kandidatenliste bleibt weltunabhaengig (der Pin
  haengt nicht an der Stapelreihenfolge), die Annahme in net_mcts.rs:2289-2305 bleibt also wahr.
  Der Softmax der Priors laeuft ueber die verbliebenen legalen IDs (net_mcts.rs:2889-2905), die
  Priors sind damit normiert.
* **UNGEPRUEFT:** ob ein Auswertungs-Cache der Suche (falls aktiv, `SearchConfig`-Cache laut
  CLAUDE.md) Kandidatenlisten oder nur Netzausgaben speichert. Nur Netzausgaben waeren
  unproblematisch, weil der Pin die Merkmale nicht aendert.

### 4.2 Der Wuerfel als reine Funktionen (self_play.rs, neuer Abschnitt)

```rust
fn dome_dice_side(game_seed: u64) -> usize                  // Hash wie asym_preference_side
fn dice_depth_cap(round: u32) -> Option<usize>              // R1 None, R2 Some(7), R3 Some(3), R4 None
fn roll_dome_dice<R: Rng>(state: &GameState, player: usize, rng: &mut R) -> Option<DiceRoll>
// DiceRoll { source: Display{tile_id} | Stack{depth}, rotation: u32 }
```

* Reihenfolge der Zuege aus dem Wuerfelstrom fest (fuer Reproduzierbarkeit): Muenze Quelle
  (`random::<bool>()`), dann Platte bzw. Tiefe (`random_range`), dann Rotation (`random_range(0..4)`),
  dann (4.4 Schritt 6) Rueckgabe-Muenze. Muenze faellt IMMER, auch wenn eine Quelle leer ist
  (Rueckfall danach), damit der Strom nicht vom Zustand abhaengt.
* Stapeltiefe: `max = min(cap.unwrap_or(usize::MAX), pool_len)`, d in `1..=max`. Runde 4 ohne Cap
  ergibt sich aus dem Pool (Nutzer: "Runde 4 hat sowieso nur noch 1 im stapel").
* Rueckfaelle: Auslage leer -> Stapel; Stapel leer -> Auslage (Prereg par.2 Punkt 1). Beide leer:
  `None` plus `debug_assert` (laut 2. nicht erreichbar).
* Keine Wirkung ausserhalb Runde 1-4 (`validate_draw_stack_peek` lehnt Runde 5 ohnehin ab,
  game.rs:190-192).

### 4.3 Einhaengepunkt in der Schleife (Ausloeser)

VORSCHLAG T1 (Nutzerfrage F1): nach dem kompletten Entscheid des Halbzugs, also NACH
`decide` (self_play.rs:4450), Rueckgabe-Streuung (4473-4494), Weg C/Ausflug (4545-4614) und
Ausflug-Reservoir (4632-4667), wird geprueft:

```
dice_active && player == dice_side && round in 1..=4
  && d.chosen ist ChooseDomeSlot oder DrawStackPeek
  && kein offener Teilzug (pending_* alle leer)
```

Trifft das zu, ersetzt `apply_forced_dome_move` (4.4) den Aufruf von `apply_chosen_action_with`
(self_play.rs:4725-4737). Damit gilt "Wuerfel ueber die TATSAECHLICH gespielte Plattenaktion":
waehlt Weg C fuer W eine Plattenaktion, wird gewuerfelt; ersetzt Weg C eine von der Suche gewaehlte
Plattenaktion durch etwas anderes, wird in diesem Halbzug nicht gewuerfelt.

**Der Ausloser-Record** (der Entscheid "jetzt eine Platte", Zustand vor dem Plattenzug, Suche
@100 ueber ALLE Aktionen): VORSCHLAG behalten mit Policy- und Wertziel, Feld `dice_trigger: true`
(Nutzerfrage F2). Begruendung: es ist eine echte Suche in einer echten Stellung; nur die
gespielte Aktion wird ersetzt, genau die Semantik von Weg C ("`d.policy` bleibt die
Besuchsverteilung der regulaeren Suche", self_play.rs:4507-4514). Ohne diesen Record fehlten der
W-Seite systematisch alle Stellungen, in denen sie sich fuer eine Platte entschied
(Auswahlverzerrung, HERLEITUNG). Mit dem Feld bleibt eine spaetere Maske ohne Neuerzeugung
moeglich (Record-Feld-Regel).

Die Record-Vorbereitung (`moon_order_target`, `state_to_json`, self_play.rs:4671-4676) laeuft wie
heute VOR dem Apply und beschreibt damit den Ausloser-Zustand. `moon_order_target` ist fuer
Plattenaktionen `None` (UNGEPRUEFT, Funktion self_play.rs:1415 nicht gelesen; beim Bau pruefen).

### 4.4 `apply_forced_dome_move` Schritt fuer Schritt

Ort: neue Funktion in self_play.rs, Aufruf nur aus `unified_game_loop`. Alle Teilzuege ueber
`game.apply_drafting` direkt, NICHT ueber `apply_chosen_action_with` (dessen Peek-Zweig koennte den
Sammelaufloeser starten, self_play.rs:1397-1401).

1. **Wuerfeln** (4.2) aus dem Strom `derive_search_seed(game_seed ^ DOME_DICE_SEED_DISTINGUISHER,
   forced_index)`, `forced_index` = Zahl der bisher erzwungenen Platten dieser Partie (0..7).
   VORSCHLAG Zaehler = `forced_index` statt `move_number`: die k-te erzwungene Platte bekommt immer
   denselben Strom, unabhaengig davon, wie viele Entscheide davor lagen.
2. **Stapelquelle:** d-mal `apply_drafting(DrawStackPeek)`. Die d-te gezogene Platte ist
   `pending_stack_draw[d-1]` (push-Reihenfolge, game.rs:233). Pin `Stack{chosen_id}` setzen.
   **Auslagequelle:** Pin `Display{tile_id}` setzen.
3. **Rueckgabe-Muenze vorab** (nur Stapel, nur Rest >= 3, nur Runde 1-4, nur bei aktivem
   Knotentor; dieselben Bedingungen wie self_play.rs:4473-4480): mit `return_order_random_p()`
   zufaelliger Kopf aus `0..min(rest, 3)`, eingetragen als `pin.return_first`. So sieht die
   Platzsuche schon den Kopf, der tatsaechlich kommt (gleiches Prinzip wie die Rotation: "die
   zufaellige Auswahl muss schon kommen bevor die Blattbewertung kommt", Prereg par.1).
   VORSCHLAG, Nutzerfrage F4.
4. **Rotation** in den Pin.
5. **Platzsuche:** gibt es nur einen legalen Platz (letzte Platte, 2.), direkt anwenden. Sonst
   `net_drafting_policy_with_fallback_flag(net, state, actions, 600, c_puct, &mut dice_search_rng,
   add_root_noise, deterministic, move_number, None, &search_config)` (self_play.rs:6279) mit
   `actions = drafting_actions(state)` (schon gefiltert). Eigener Strom
   `derive_search_seed(game_seed ^ DOME_DICE_SEARCH_SEED_DISTINGUISHER, forced_index)`. Wurzel:
   nur Plaetze der Wuerfelplatte; im Baum: (Rueckgabeknoten, frei oder festgenagelt) und
   Rotationsknoten mit genau einem Kind. Ergebnis anwenden. Die Policy der Suche wird verworfen.
   `move_number` geht nur fuer den tau-Umschaltpunkt mit (Rezept `tau_argmax_from_move 1` ->
   argmax, self_play.rs:6388-6407).
6. **Rueckgabeknoten** (nur falls er sich oeffnet, game.rs:1123-1131): mit vorab gewuerfeltem Kopf
   gibt `drafting_actions` genau eine Aktion; sonst eine Suche mit den Sockel-Sims (100) auf dem
   Knoten, ohne Record, eigener Strom (`..._SEARCH_SEED_DISTINGUISHER`, Zaehler
   `forced_index * 2 + 1` o.ae.). Bei AUS geschaltetem Knotentor (406er-Netz, Heuristik) traegt
   `ChooseDrawStackSlot` die Rueckgabereihenfolge selbst: Ziehreihenfolge, bei gefallener Muenze
   gemischt (Muster `sample_random_return_order`, self_play.rs:1024-1038).
7. **Rotation:** `apply_drafting(ChooseDomeRotation(pin.rotation))`, Pin wird geloescht,
   `switch_player` passiert dort (game.rs:1162-1163).
8. Zaehler `forced_index += 1`, Diagnose-Tupel fuer die Partiezeile (4.6) sammeln.

Kein Teilschritt erhoeht `move_number`/`round_move_index`/`steps`, keiner schreibt einen Record.
Der Partie-RNG wird nicht beruehrt (alle Zufallszahlen aus eigenen Stroemen).

### 4.5 Folgen fuer die Suche (HERLEITUNG)

* **Die Suche weiss nicht, dass kuenftige W-Platten gewuerfelt werden.** Im Baum (eigene Suchen
  der W-Seite wie Suchen der G-Seite) waehlt W seine spaeteren Platten frei. Die Suche der W-Seite
  ist darum beim Ausloser optimistisch ("jetzt eine Platte" wird mit der BESTEN Platte bewertet).
  Ein Zufallsknoten fuer W-Platten im Baum waere die korrekte Modellierung, ist aber ein grosser
  Umbau in `net_mcts.rs`; VORSCHLAG: nicht bauen, in S2/S3 beobachten. Fuer die G-Seite ist das
  sogar realistisch (sie kennt die Wuerfel-Regel nicht).
* **Determinisierung der Platzsuche:** Betrachter W (net_mcts.rs:2229). Eigene Bloecke exakt,
  fremde in sich gemischt, Praefix gemischt, oberster Typ fest. Die gezogenen Platten
  (`pending_stack_draw`) sind echt.
* **Priors tiefer Ziehungen:** ab d >= 4 nutzt jede Kandidaten-ID den Index 3
  (features.rs:2149). An der Wurzel stoert das nicht (alle Kandidaten gehoeren zur selben Platte,
  die 9 Plaetze haben 9 verschiedene IDs), die Priors stammen aber aus einer im Training seltenen
  Lage. 600 Sims gleichen das teilweise aus.
* **Gumbel-Breite:** laut Registereintrag `gumbel_top_m_for_budget(sims) = clamp(round(sims/16),
  4, 16)` (knob_registry.rs:119, Code nicht gelesen), bei 600 also 16, mehr als die hoechstens 8
  Plaetze.

### 4.6 Records

* **Kein Record** fuer die Teilschritte 2-7 (sie laufen nicht durch den Record-Bau).
* `dome_dice_side` (usize) auf JEDEM Record einer W-Partie: nach der Partie gestempelt, Muster
  `stamp_tie_mirrored` (tie_mirror.rs:151-158, Aufruf self_play.rs:7110). Schliesst Start- und
  Tiling-Records ein.
* `forced_domes_before` (u32) auf JEDEM Record: Wert ist je Record verschieden, darum an den drei
  `records.push`-Stellen der Schleife einsetzen (Startsetzung self_play.rs:4379, Drafting 4834,
  Tiling 4850), nicht nachtraeglich.
* `dice_trigger: true` nur am Ausloser-Record (VORSCHLAG, F2).
* Felder NUR bei aktivem Knopf: ohne Knopf byte-gleicher Record, Netz-Paritaets-Fixture und
  Golden-Records unberuehrt (Fixture hasht Records, Memory-Eintrag "Record-Feld muss VOR die
  Erzeugung").
* **Diagnose ohne Schemaeingriff:** eine Zeile je Partie per `eprintln!` wie `[deviate]`
  (self_play.rs:4598-4609): `[dome_dice] game_id seed side forced=n` plus je Platte
  `(runde, quelle, d, max, aus_praefix, aus_eigenem_block, aus_fremdem_block, gezahlt, rot,
  plaetze, rueckgabe=zufall|suche|keine)`. Daraus liest S3 die Kosten und die Zuege in Bekanntes,
  ohne neues Record-Feld. Die Klassifikation der gezogenen Positionen geht aus
  `dome_pool_unknown_prefix_len` und den Bloecken VOR dem ersten Peek (state.rs:169-172).

### 4.7 Zufallsstroeme (PREREG_search_rng_split.md)

| Strom | Ableitung (VORSCHLAG) | Zaehler |
| --- | --- | --- |
| Wuerfel-Seite | `game_weight_from_seed(game_seed ^ DOME_DICE_SIDE_DISTINGUISHER, 1.0) < 0.5` | keiner |
| Wuerfel (Quelle, Platte/Tiefe, Rotation, Rueckgabe-Muenze) | `derive_search_seed(game_seed ^ DOME_DICE_SEED_DISTINGUISHER, k)` | k = forced_index |
| Platz- und Rueckgabesuche | `derive_search_seed(game_seed ^ DOME_DICE_SEARCH_SEED_DISTINGUISHER, 2k / 2k+1)` | forced_index |
| Stoerer-Seite (S) | `game_weight_from_seed(game_seed ^ AGGR_SIDE_DISTINGUISHER, 1.0) < 0.5` | keiner |

Alle neuen Konstanten in den Eindeutigkeitstest (Muster self_play.rs:13135-13158). Die
Seitenwahl ist ein Hash, der Startspieler kommt aus dem Partie-RNG (self_play.rs:7018): die beiden
sind nicht per Konstruktion balanciert, S1 meldet die 2x2-Tafel Seite x Startspieler.

### 4.8 Knoepfe, Rezept, Manifest, Waechter

* Env (alle Default AUS, OnceLock-Getter wie `return_order_random_p`, self_play.rs:959-971):
  `MOSAIC_DOME_DICE` (0/1), `MOSAIC_DOME_DICE_SIMS` (Default 600). Obergrenzen 7/3 als Konstante im
  Code (Nutzer-Festlegung, kein Knopf), aber im Manifest gemeldet.
* `knob_registry.rs`: je ein `KnobEntry` (einzeilig, Format-Vertrag knob_registry.rs:20-22);
  sonst schlaegt `all_mosaic_env_vars_in_code_are_registered` fehl (knob_registry.rs:377-378).
* `engine_config_json` (lib.rs:754ff): `dome_dice`, `dome_dice_sims`, `dome_dice_caps`
  (`[null, 7, 3, null]`), spaeter `aggr_side`, `aggr_side_w`, `aggr_side_lambda`.
* `self_play.py`: Flags `--dome-dice`, `--dome-dice-sims`, `--aggr-side`, `--aggr-side-w`,
  `--aggr-side-lambda`, Env-Zuordnung wie Zeile 64-65 (`MOSAIC_RETURN_ORDER_RANDOM_P` ->
  `return_order_random_p`). Kombination mit `--excursion-prob > 0` ablehnen (E19).
* Rezept `models/v35...recipe.json` (Name beim Bau): Klassen `policy`, `policy-dice`,
  `policy-dice-aggr`, `policy-aggr`, `value-deviate` (bis v34 `value-wegc`), `value-excursion`.
  `expect_engine_config` JE KLASSE (Lehre aus models/v34.recipe.json `description`: rezeptweit
  brach eine Erwartung die policy-Klasse), z. B.
  * `policy`: `{"dome_dice": 0, "aggr_side": 0}`
  * `policy-dice`: `{"dome_dice": 1, "dome_dice_sims": 600, "aggr_side": 0}`
  * `policy-dice-aggr`: `{"dome_dice": 1, "dome_dice_sims": 600, "aggr_side": 1, "aggr_side_w": w, "aggr_side_lambda": l}`
  * `policy-aggr`: `{"dome_dice": 0, "aggr_side": 1, ...}`
  Die Knoepfe sind Env-Knoepfe, keine Spec-Felder: der Waechter bleibt damit aussagekraeftig (die
  v34-Rezeptbeschreibung warnt, dass er bei Spec-Feldern blind wird).

### 4.9 Seitenwahl und Paarungen

| Klasse | Seite 0/1 | Regel |
| --- | --- | --- |
| `policy` (G-G) | beide normal | Bestand |
| `policy-dice` (G-W) | W = Hash(seed, DICE_SIDE) | andere Seite normal |
| `policy-aggr` (G-S) | S = Hash(seed, AGGR_SIDE) | andere Seite normal |
| `policy-dice-aggr` (W-S) | W = Hash(seed, DICE_SIDE), S = 1 - W | NICHT zwei unabhaengige Muenzen |

"Beide Seiten Wuerfel" ist strukturell ausgeschlossen (ein Index). Der Pin traegt trotzdem den
Spieler, damit eine solche Erweiterung nichts bricht.

---

## 5. Edge-Case-Katalog Klasse W

Je Fall: **heute** (was der Code tut), **regel** (konform?), **sinn**, **Vorschlag**, **Frage**.

**E1 Zweiter Stapelzug in den eigenen bekannten Block (Beispiel des Nutzers).**
heute: erlaubt, zieht von oben aus dem aeltesten Block (state.rs:178-188), Kosten je Peek bis 0
(board.rs:345-349). regel: konform (4A "beliebig oft"). sinn: fuer einen echten Spieler nur als
Weg zu einer bekannten Platte (par.15g), als Wuerfelzug ohne Wahl, in R1 meist gratis (3.4).
Vorschlag: zulassen wie festgelegt, in S3 aus der `[dome_dice]`-Zeile zaehlen
(Anteil Ziehungen aus eigenem Block, bei Stand > 0 und bei Stand 0). Frage: F3.

**E2 Tiefe in einen FREMDEN Block.** heute: der G-Block liegt unter dem W-Block bzw. dem Praefix;
W kennt die Menge, nicht die Reihenfolge, und die Suche von W mischt ihn in sich
(state.rs:300-302). regel: konform. sinn: ja (echte Information fuer W). Vorschlag: zulassen.

**E3 Ganzer Stapel (d = Pool).** heute: Pool danach leer bis zur Rueckgabe; die Rueckgabe legt
d-1 Platten als einen Block. Praefix danach dauerhaft 0 (3.2 Schritt 5). regel: konform.
Vorschlag: zulassen; Test E3 (Wissensstand konsistent, `dome_pool_knowledge_is_consistent`
state.rs:212-222).

**E4 Rueckgabe-Reihenfolge der Wuerfel-Seite.** heute (Sockel, Knotentor an): Kopf per Knoten aus
den ersten 3 der Ziehreihenfolge, Rest in Ziehreihenfolge (game.rs:1079-1093); bei Rest >= 3 in
R1-R4 mit p = 0,81 zufaelliger Kopf (self_play.rs:4473-4494). Gemessene Wirkung im Sockel:
28 von 200 Partien gestreut (knob_registry.rs:116, Eintrag fuer v32). regel: konform.
Vorschlag: Muenze VOR der Platzsuche, Kopf in den Pin; ohne Muenze sucht die Platzsuche den Kopf
mit, danach eigene Suche @100 ohne Record. Frage: F4.

**E5 Rueckgabe beeinflusst die Auslage der naechsten Runde.** heute: Auffuellen von oben
(game.rs:1361-1366); ist das Praefix leer, kommen die obersten Platten des aeltesten Blocks in die
Auslage. regel: konform. sinn: ja, das ist der Grund, warum die Reihenfolge ueberhaupt zaehlt.
Vorschlag: keine Sonderbehandlung; S2 kann pruefen, ob G-Records nach solchen Auffuellungen
anders aussehen.

**E6 Auslage leer, Muenze "Auslage".** heute: `generate_dome_moves` liefert nichts
(game.rs:161). Vorschlag: Rueckfall Stapel (Prereg par.2). Test.

**E7 Stapel leer, Muenze "Stapel".** heute: `validate_draw_stack_peek` lehnt ab (game.rs:212-214).
Vorschlag: Rueckfall Auslage. Test.

**E8 Beide Quellen leer.** heute: kann bei offener Pflicht nicht eintreten (HERLEITUNG Abschnitt 2);
sonst greift der Deadlock-Abbruch (game.rs:535-577, 618-620). Vorschlag: `debug_assert` im Wuerfel,
kein Rueckfall.

**E9 Punktestand 0.** heute: Peeks gratis, `score` und `score_unclamped` bleiben 0
(board.rs:345-349; game.rs:204-211 Kommentar). regel: konform, ausdruecklich (4A, par.11 der
score_clamp-Prereg laut Handbuch). sinn: fuer W egal (keine Wahl). Vorschlag: nichts tun, in S3 die
gezahlten Punkte je Partie ausweisen.

**E10 Runde 1: Startstand 5 deckelt die Kosten.** heute: Startstand 5 (board.rs:286), Drafting
bringt keine Punkte (1.2). Folge: Prereg-Herleitung "Runde 1 7 Punkte" ist zu hoch, siehe
Abschnitt 11. Vorschlag: Prereg-Text korrigieren.

**E11 Runde 4.** heute: Pool zu Rundenbeginn 1 (HERLEITUNG Abschnitt 2), max = 1. Ist die Auslage
leer, MUSS die letzte Platte der Runde vom Stapel kommen; ist der Stapel leer, aus der Auslage.
Vorschlag: keine Obergrenze noetig (Nutzer). Test mit konstruiertem Zustand.

**E12 Letzte Platte, nur ein Platz.** heute: Kandidatenliste hat einen Eintrag. Vorschlag: keine
600er-Suche, direkt anwenden (spart rund 1/8 der Platzsuchen, HERLEITUNG).

**E13 Platzsuche will weiterziehen.** heute: waehrend eines Stapelzugs ist `DrawStackPeek` weiter
legal (game.rs:869-872). Vorschlag: der Pin entfernt es; sonst koennte die Suche "noch eine
ziehen" bewerten, was der Wuerfel nicht zulaesst.

**E14 Pin leckt in die Suche des Gegners oder ueber den Zug hinaus.** heute: kein Pin. Vorschlag:
Pin traegt `player`, wird bei `ChooseDomeRotation` und beim Rundenwechsel geloescht; Test, dass
nach dem erzwungenen Zug `dome_dice_pin == None` und `state_to_json` unveraendert ist.

**E15 Determinisierung bei W.** heute: W sieht seine Bloecke exakt (state.rs:300-302). Nach einem
tiefen R1-Zug kennt W den ganzen Stapel; seine Suchen im Baum "wissen", was ein Peek bringt
(Baum liest die oberste Platte, net_mcts.rs:2138). regel: konform (4A). sinn: ja, genau das
"Dafuer kennt sie aber auch den Stapel" des Nutzers. Vorschlag: nichts tun.

**E16 Suche modelliert kuenftige W-Platten als frei.** Siehe 4.5. Vorschlag: nicht bauen,
beobachten (S3: Wert-Verzerrung). Keine Nutzerfrage, aber im Bericht nennen.

**E17 Policy-ID-Kollision bei d >= 4.** heute: features.rs:2149. An der Wurzel der Platzsuche
unschaedlich (4.5). Fuer Records ohne Belang (kein Record). Vorschlag: nichts tun.

**E18 Weg C in derselben Partie** (falls `deviate_prob` in den W-Klassen bleibt, Frage F5).
heute: Abweichung ersetzt `d.chosen` an einer Stelle aus der gemessenen Verteilung
(self_play.rs:4545-4614), zaehlt ueber `round_move_index`. Vorschlag: Wuerfel-Pruefung NACH der
Abweichung (4.3). Die Teilschritte des Wuerfelzugs zaehlen nicht mit; die Abweichungsstelle kann
deshalb nie mitten in einem Wuerfelzug liegen. HERLEITUNG: weil Plattenteilzuege der W-Seite als
Schleifenentscheide wegfallen, verschiebt sich die Verteilung der `round_move_index` gegenueber der
Messgrundlage von `DEVIATE_ROUND_MASS` leicht; vernachlaessigbar, aber im Bericht nennen.

**E19 Ausflug (Weg B) in derselben Partie.** heute: Ausfluege nur in `value-excursion` (G-G).
Ein Ausflug-Klon entsteht vor dem Apply (self_play.rs:4660-4663), also nie mitten in einem
Wuerfelzug. Vorschlag: Kombination in `self_play.py` ablehnen, solange die Ausflug-Fortsetzung die
Wuerfel-Seite nicht erbt (sonst wuerde der Ausflug als G-G weiterlaufen). Frage: F8.

**E20 Bauer-/Kuppel-Vorzug.** heute: `NetSelfPlayAgent` mit `vorzug: true` kann ein Ein-Hot-Ziel
auf eine Plattenaktion liefern (`dome_preference`, self_play.rs:2644-2648, 3899-3901), nur bei
gesetztem `MOSAIC_PLATTENBAU`/`MOSAIC_SPALTENBAU` (plate_builder.rs:72-100). Im v34-Rezept ist
keins gesetzt (models/v34.recipe.json `env`; UNGEPRUEFT, ob die Kette sie anderswo setzt).
Vorschlag: greift der Vorzug UND wird gewuerfelt, Ausloser-Record ohne Policy-Ziel
(`policy_target_valid=false` ist unwirksam unter `MOSAIC_IGNORE_POLICY_TARGET_VALID=1`,
corpus_dataset.py:1635-1647; darum eigenes Feld `dice_trigger` maskieren).

**E21 Nur eine legale Aktion beim Ausloser.** heute: keine Suche, Ein-Hot-Ziel
(self_play.rs:3895-3898). Vorschlag: Wuerfel wirkt trotzdem; der Ein-Hot-Record ist der
Bestandsfall.

**E22 Startplatte.** heute: Startsetzung per Suche (Spec `start_by_search: 1`,
models/v33_generation.spec.json) mit Auffuellen vom Stapel (game.rs:668-673). Vorschlag: unveraendert
(Nutzer "Start normal").

**E23 Knotentor aus (406er-Netz, Heuristik-Seite).** heute: `ChooseDrawStackSlot` uebernimmt
`m.return_order` direkt (game.rs:1132-1138). Vorschlag: der Wuerfelzug reicht die Ziehreihenfolge
bzw. die gestreute Reihenfolge selbst ein (4.4 Schritt 6). Fuer die Erzeugung mit v33-b01 ist das
Tor laut Rezept an (UNGEPRUEFT am ONNX).

**E24 Zeitdeckel der Partie.** heute: `net_game_timeout_secs(100)` = 45 s plus
`EXTRA_GAME_TIMEOUT_SECS` = 2.550 s (self_play.rs:89-91, round_transition_deep.rs:194).
Vorschlag: kein Handlungsbedarf (HERLEITUNG: sieben Suchen @600 sind klein gegen den Deckel).

**E25 Spiegelknopf und Huellenterm.** heute: thread-lokal je Partie (tie_mirror.rs Kopf), wirkt
auch in der Platzsuche der W-Seite. Vorschlag: so lassen; Wuerfel-Seite und Spiegelmuenze sind
verschiedene Distinguisher.

**E26 Beide Spieler als Wuerfel-Seite.** Siehe 4.9: nicht vorgesehen, strukturell ausgeschlossen.
Waere es gewollt, haetten beide eigene Bloecke; Determinisierung und Pin tragen das bereits
(Pin je Spieler). Kein Bau.

---

## 5a. Nachtrag: Punkte-Edge-Cases der Stapelzuege (Koordinator, 2026-10-01)

Nutzer: *"ich finde auch keine edge cases in bezug auf die kuppelplatten aus dem nachziehstapel und den
daraus resultierenden punkten."* E9/E10 oben deckten nur Stand 0 und den Startstand ab. Gelesen:
`docs/engine_manual.md` 4A (Stapelkosten), 4 "Round-End Settlement" (Strafen, Untergrenze 0),
5 (Spezialfelder), 6 (Wertungsplatten); `engine/src/board.rs:336-348` (Zahlung gedeckelt,
`score_unclamped` bei Zahlungen nie negativ, bei Strafen schon), `features.rs:1382-1384` (Netzeingabe:
`score/100` und geschaetzte Rundenwertung je Spieler).

**E27 Kosten nach Runde 1.** Ein Stapelzug kostet min(d, Punktestand); nach den Wertungen ist der
Stand hoeher, der Deckel greift kaum. Obergrenzen je Zug: R1 Stand (5 beim ersten Zug), R2 7, R3 3,
R4 1. Obere Schranke je Partie bei zwei Stapelzuegen je Runde und ausreichendem Stand (HERLEITUNG):
5 + 14 + 6 + 2 = 27 Punkte. Erwartung bei Muenze 50:50 grob 9-10 Punkte (HERLEITUNG: R1 rund 2,1,
R2 4, R3 2, R4 1, Deckel durch den Stand nicht gerechnet). Vorschlag: so lassen (Nutzer-Entscheid
Obergrenzen), S3 weist die gezahlten Punkte je Runde aus.

**E28 Stand 0 macht ALLES gratis.** Bei 0 kosten weder Stapelzuege noch Strafleiste noch der
Startspielerstein (-2) etwas (Handbuch 4 "Round-End Settlement": *"can never fall below 0 through
penalties"*). Die Suche der W-Seite sieht den Stand als Eingabe und kann daraus lernen, bei 0 die
Strafleiste und den Startspielerstein billig zu nehmen. Regelkonform; genau eine provozierte
Stellung, die im Selbstspiel fast nie entsteht. Vorschlag: zulassen, in S3 Strafleiste und
Startspielerstein der W-Seite getrennt nach "Stand 0" / "Stand > 0" ausweisen.

**E29 `score_unclamped` verschluckt die Wuerfelkosten bei niedrigem Stand.** Strafen laufen in
`score_unclamped` ins Minus, bezahlte Stapelkosten nicht (`board.rs:336-348`). Zieht W bei Stand 2
d = 7, ist der Verlust in beiden Feldern 2, nicht 7. Folge fuer Labels, die die Endmarge lesen (E2-Arm,
`scores_unclamped`): die Behinderung der W-Seite erscheint kleiner, als die Wuerfel sie verlangt
haetten. Vorschlag: Record-Feld `dome_dice_cost` = [verlangte Tiefe d, tatsaechlich bezahlt] am
ersten Record NACH jedem erzwungenen Zug, VOR der Erzeugung (Record-Feld-Regel). Neue Nutzerfrage F9.

**E30 Zustaende ausserhalb der gewohnten Verteilung.** W bei Stand 0 in Runde 2-4, mit hoher
geschaetzter Rundenwertung, kommt im Selbstspiel praktisch nicht vor. Der Wertkopf sieht dort
Eingaben, auf denen er nie trainiert wurde. Das ist der Zweck der Klasse; S3 misst den Brier des
Generator-Kopfs auf W-Records getrennt nach Stand 0 / > 0.

**E31 Spezialfelder unter Zufallsplatte und Zufallsrotation.** 9 der 18 Platten tragen ein
Spezialfeld; es wird erst frei, wenn die drei anderen Felder der Platte belegt sind, und zahlt dann
die Reihennummer 1-6 (Handbuch 5). Die Rotation bestimmt, in welcher Reihe des 2x2-Feldes es liegt,
die Platzsuche nur den Slot. Folgen: Spezialpunkte der W-Seite verschieben sich zufaellig; ist
Wertungsplatte 7 im Spiel (-3 je leeres Spezialfeld), kostet eine gewuerfelte Spezialplatte, die W
nicht vollenden kann, zusaetzlich 3. Vorschlag: zulassen; S3 weist Spezialpunkte und k7-Abzuege der
W-Seite aus (Kennzahl 4 "Punkte je Wertungsplatte" ohnehin Pflicht).

**E32 Wildfelder und Wertungsplatte 4.** 9 Platten tragen ein Wildfeld; Wertungsplatte 4 zahlt
2 Punkte je Wildfeld NUR, wenn alle gefuellt sind (Handbuch 6). Zufallsplatten aendern die Zahl der
Wildfelder der W-Seite; ein einziges ungefuelltes kippt den ganzen Posten. Vorschlag: zulassen,
berichten wie E31.

**E33 Eckplatten (Wertungsplatte 6) und Rotation.** 3 bzw. 8 Punkte je vollstaendige Eckplatte.
Den Eckslot kann die Platzsuche waehlen, die Rotation nicht; ob die Farben einer gewuerfelten
Rotation dort vollendbar sind, entscheidet der Zufall. Vorschlag: zulassen, berichten.

**E34 Information fuer G.** Der Gegner sieht die Vorderseiten aller gezogenen Platten (Handbuch 4A),
nur die Rueckgabe-Reihenfolge nicht. Tiefe W-Zuege decken G also viel vom Stapel auf; G gewinnt
Information, ohne zu zahlen. Regelkonform. Vorschlag: zulassen; in S2 sichtbar als geringere
Unsicherheit der G-Suche ueber den Stapel (nicht eigens messen).

**E35 Kosten treffen G nicht, aber G spielt gegen einen armen Gegner.** Mit W bei 0 verschieben sich
G's Anreize (Stoeren lohnt nicht, Rennen genuegt). Das gehoert zur Wert-Verzerrung aus par.2 der
Prereg; S3 berichtet Punkte und Marge der G-Seite gegen die G-G-Klasse.

## 6. Klasse S (kurz)

### 6.1 Heutiger Stand (geprueft)

* `w` und `lambda` prozessweit als Atomics, Env `MOSAIC_POINTS_UTILITY_W`/`MOSAIC_AGGR_LAMBDA`,
  GUI-Regler klemmt w in [0,1], lambda in [0,5] (net_mcts.rs:181-203, 774-803).
* Blend nur bei `w != 0` (net_mcts.rs:3061-3063): `(1-w)*wr + w*clamp(pts - lambda*opp, -1, 1)`
  (net_mcts.rs:3068-3071, 1952-1954). lambda allein bewirkt NICHTS.
* Angewandt fuer den ZIEHENDEN am Blatt (net_mcts.rs:3779); mit E1 (`single_pass_other_val`,
  Rezept-Env `MOSAIC_SINGLE_PASS_OTHER_VAL=1`) ist der Wert des anderen `1 - mover`
  (net_mcts.rs:3783-3784). Folge (HERLEITUNG): mit prozessweitem lambda sind in jeder Suche BEIDE
  Seiten "Stoerer", jeweils am Blatt, an dem sie ziehen.
* Review #11: `try_batched_pair_ex` gibt `opp_points` leer zurueck (net_mcts.rs:3357-3359),
  geschuetzt nur durch den prozessweiten Waechter `points_utility_w() != 0` (net_mcts.rs:3352-3354);
  der Sammel-Faden ist per Default aus (Review #11, code_review_2026-09-26_verification.md:105).
* Jeder Knoten speichert `points_forecast`, `opp_points_forecast`, `raw_value` (net_mcts.rs:2815-2839),
  hochgereicht wird ein gemischtes `value` je Knoten aus Sicht von `player_who_acted`
  (net_mcts.rs:2802-2804), Blattwerte je Spieler `leaf_value: [f64; 2]` (net_mcts.rs:2810).

### 6.2 Bau (VORSCHLAG)

1. `SearchConfig` bekommt `aggr_w: Option<f64>`, `aggr_lambda: Option<f64>` (None = prozessweiter
   Wert, Bestand). Spec-Feld OPTIONAL (Muster `moon_order_variants`), damit eingefrorene Specs laden.
2. Fuer die Erzeugung: NetSelfPlayAgent der S-Seite bekommt eine Kopie der `SearchConfig` mit
   gesetzten Feldern aus `MOSAIC_AGGR_SIDE_W`/`MOSAIC_AGGR_SIDE_LAMBDA` (zwei Agenten gibt es
   bereits, self_play.rs:6719-6742). Seitenwahl 4.7/4.9.
3. Blend AUS SICHT DES STOERERS, unabhaengig davon, wer am Blatt zieht (Frage FS1):
   `leaf_value[S] = (1-w)*wr_S + w*clamp(pts_S - lambda*opp_S)`, `leaf_value[G] = wr_G`
   (unvermischt). Zieht am Blatt G, kommen `pts_S`/`opp_S` aus dessen Ego-Koepfen vertauscht
   (`opp_raw` bzw. `pts_raw`) und `wr_S = 1 - wr_G`. Der Baum ist dann nicht mehr Nullsumme; die
   Datenstruktur traegt das bereits (Werte je Spieler, net_mcts.rs:2810, 3800-3801).
4. Zweiter Akkumulator: `Node.own_value_sum: f64` mit dem UNVERMISCHTEN `wr` des
   `player_who_acted`, im Backprop neben `value` mitgefuehrt (kein Netzaufruf). An der Wurzel:
   `Q_own(c) = own_value_sum/visits`, `own_q_gap = max_c Q_own(c) - Q_own(gewaehlt)` ueber Kinder
   mit mindestens N_min Besuchen (Frage FS3). Neuer Einstieg statt Signaturaenderung an
   `net_root_child_stats_policy_and_prior` (CLAUDE.md: oeffentliche Signaturen brechen
   `engine/examples` und `engine/benches` beim pre-push).
5. Review #11 im selben Zug: Waechter auf das `w` der suchenden Seite umstellen und `_oppa`/`_oppb`
   durchreichen.
6. Records: `aggr_side` auf jedem Record einer S-Partie (gestempelt wie `tie_mirrored`),
   `own_q_gap` auf jedem Drafting-Record der S-Seite mit echter Suche. Policy-Maske
   (`own_q_gap > eps` -> Gewicht 0) in corpus_dataset.py neben den bestehenden Masken
   (corpus_dataset.py:1646-1694), eps aus Env `MOSAIC_AGGR_OWN_Q_EPS`, **im Cache-Schluessel**
   (Memory "Feature-Knopf gehoert in BEIDE Cache-Schluessel").
7. Wirkort: Drafting-Suche der S-Seite. Startsetzung per Suche nutzt dieselbe `SearchConfig`
   (wirkt also mit), Tiling nutzt `net_leaf_eval` mit Env-Werten (net_mcts.rs:3376-3378) und bleibt
   unvermischt. Frage FS4.

---

## 7. Python und Training

* `self_play.py`: Flags und Env (4.8), Ablehnung der Kombination Ausflug + Wuerfel, Manifest
  traegt die neuen engine_config-Felder automatisch.
* `engine/py/corpus_dataset.py`: (a) S-Maske (6.2 Punkt 6); (b) optionale Maske
  `dice_trigger` hinter Env `MOSAIC_MASK_DICE_TRIGGER` (Default aus, im Cache-Schluessel);
  (c) nichts fuer `forced_domes_before`/`dome_dice_side` (nur Analyse). Wertziele: alle behalten
  (Nutzer, Prereg par.2).
* UNGEPRUEFT: ob alle Python-Konsumenten unbekannte Record-Felder tolerieren. Praezedenz:
  `tie_mirrored`, `return_order_randomized`, `fallback_random_action` sind additiv eingefuehrt
  worden.

---

## 8. Tests

### 8.1 Rust-Unit-Tests W (je Edge Case)

1. `dome_dice_pin_display_offers_only_pinned_tile_slots` (E13/4.1).
2. `dome_dice_pin_stack_offers_only_chosen_tile_and_no_peek` (E13).
3. `dome_dice_pin_rotation_offers_single_rotation_and_clears_on_apply` (inkl. `switch_player`).
4. `dome_dice_pin_return_first_offers_single_position`.
5. `apply_drafting_rejects_actions_outside_the_pin_and_leaves_state_unchanged`.
6. `dice_depth_respects_round_caps_and_pool` (R1 1..=pool, R2 <= 7, R3 <= 3, R4 = pool) plus
   Gleichverteilungsprobe ueber viele Seeds der reinen Funktion.
7. `dice_source_falls_back_when_display_or_stack_empty` (E6/E7), `..._none_when_both_empty` (E8).
8. `dice_full_stack_draw_round_one` (Beispiel des Nutzers): Stand 5 -> 0, Pool 12, Bloecke
   `[{12, W}]`, Praefix 0, Konsistenz (E3/E9/E10).
9. `dice_second_draw_into_own_block_is_legal_and_free_at_zero` (E1): d = 12, neuer Block {11, W}.
10. `opponent_determinization_permutes_dice_block_in_itself` (E2/E15): Viewer G mischt in sich,
    Viewer W laesst stehen, Multimenge gleich, oberster Typ gleich.
11. `round_refill_takes_top_of_dice_block` (E5): Auslage = erste drei der Rueckgabe, Block 12 -> 9.
12. `round_four_single_stack_plate` (E11).
13. `single_slot_skips_the_search` (E12, Zaehler-Hook im Testbau wie `OTHER_PASS_CALLS`,
    net_mcts.rs:3384-3398).
14. `forced_dome_move_writes_no_records_and_stamps_fields` (4.6): keine Records mit offenem
    W-Teilzug im Zustand, `forced_domes_before` monoton, Endwert <= 8, `dome_dice_side` ueberall.
15. `dome_dice_reproducible_and_partie_rng_untouched` (4.7), Distinguisher-Eindeutigkeit erweitert.
16. `dome_dice_side_balance` (50 Prozent +- Toleranz ueber 10.000 Seeds, plus Kreuztafel mit
    einer Startspieler-Ziehung aus dem Partie-RNG).
17. `dice_off_is_byte_identical`: Schleife mit Knopf aus gegen Golden-Record (Gate-B-Methodik,
    self_play.rs:2636-2638).
18. `pin_never_serialized_in_records` (E14).
19. `deviation_choosing_plate_triggers_dice` (E18) mit konstruiertem Zustand.

### 8.2 Rust-Unit-Tests S

1. `aggr_none_is_byte_identical` (Env-Pfad unveraendert).
2. `aggr_blend_applies_to_aggressor_perspective_only` (Blatt mit S am Zug und mit G am Zug).
3. `own_accumulator_equals_value_when_blend_off`.
4. `batched_pair_keeps_opp_points` (Review #11).
5. `own_q_gap_only_on_aggressor_records`.

### 8.3 Python

* corpus_dataset: S-Maske nach eps, Cache-Schluessel aendert sich mit eps; `dice_trigger`-Maske.
* Rezept-Waechter: je Klasse `expect_engine_config` gegen ein simuliertes engine_config.

### 8.4 Abnahmen (in dieser Reihenfolge, alle EXKLUSIV auf der Maschine)

1. `cargo test --release --no-run` aus `engine/` (CLAUDE.md: Beispiele und Benches kompilieren mit).
2. Wheel-Bau (`python -m maturin`, nie in einer Pipe).
3. Golden-Records und Netz-Paritaets-Fixture mit Knoepfen AUS: byte-gleich.
4. `/mosaic-anchor-invariance`: Anker hv4 Zug fuer Zug (Engine-Aenderung an `drafting_actions` und
   `apply_drafting` betrifft den Heuristik-Pfad, auch wenn der Pin dort nie gesetzt ist).
5. Smoke je Klasse (z. B. 20 Partien, Muster v34-Smoke), `/mosaic-measurement-run`.

---

## 9. Sonden S1-S4 (Leseregeln als VORSCHLAG, vor dem Lauf in die Prereg)

* **S1 Kosten:** 100 Partien `policy` gegen 100 `policy-dice`, gleiche Seeds, Muster
  `tools/v34_cost_gate.sh`. Grundmenge Partien, Einheit s je Partie (Wanduhr, CPU, Threads im
  Artefakt). Zusaetzlich je Partie: Zahl der 600er-Suchen, Zahl der Rueckgabesuchen. Lesart:
  Mehrkosten <= 25 Prozent je W-Partie (HERLEITUNG-Erwartung rund +15 bis +20 Prozent, Abschnitt 10)
  -> Plan haelt; deutlich darueber -> Sims der Platzsuche mit dem Nutzer neu festlegen.
* **S2 Andere Stellungen?** `tools/probes/targeted_branching_pretest.py`: KL(Ziel || Prior) an
  Entscheiden beider Seiten nach erzwungenen Platten gegen Sockel, getrennt nach Seite und Runde.
  Dazu die sechs Standard-Kennzahlen je Seite (CLAUDE.md). Zusaetzlich aus der `[dome_dice]`-Zeile:
  Quellenanteile, Tiefenverteilung je Runde, Anteil Ziehungen aus eigenem/fremdem Block
  (Vorbild `tools/probes/dome_stack_known_block_draw_probe.py`).
* **S3 Wert-Verzerrung:** Siegquote, Punkte und Marge der W-Seite; Brier des Generator-Kopfs auf
  W-Records gegen Sockel-Records, getrennt nach Seite und nach `forced_domes_before`; gezahlte
  Wuerfel-Punkte je Partie (bei Stand > 0 und bei 0).
* **S4 Stoerer-Pilot:** lambda-Reihe (z. B. 0; 0,5; 1; 2 bei festem w, Frage FS2), Punkte beider
  Seiten je lambda, Verteilung von `own_q_gap`, daraus eps als Quantil "Anteil der S-Zuege, die
  durchkommen".

Blockgroesse 5 in jeder Arena (Memory), Auswertung auf Blockebene.

---

## 10. Bauschritte und Aufwand

| Schritt | Inhalt | Aufwand (HERLEITUNG, grob) |
| --- | --- | --- |
| 0 | Nutzerfragen F1-F8, FS1-FS4 klaeren; Prereg par.2/par.6 und Zeile-1-Kopf nachziehen (`/mosaic-prereg`, Index neu generieren) | 1 h |
| 1 | Pin in state.rs/game.rs, Serialisierung, Tests 8.1/1-5, 18 | 0,5 Tag |
| 2 | Wuerfel-Funktionen, Stroeme, Seitenwahl, Tests 8.1/6-7, 15-16 | 0,5 Tag |
| 3 | `apply_forced_dome_move` und Schleifen-Einhaengung, Record-Felder, Diagnosezeile, Tests 8.1/8-14, 17, 19 | 1 Tag |
| 4 | Knoepfe: Getter, knob_registry, engine_config, self_play.py, Rezept mit Klassen-Waechtern | 0,5 Tag |
| 5 | S: SearchConfig-Felder, Blend je Perspektive, Akkumulator, own_q_gap, Review #11, Tests 8.2 | 1 Tag |
| 6 | corpus_dataset-Masken, Cache-Schluessel, Python-Tests | 0,5 Tag |
| 7 | Abnahmen 8.4 (Maschine exklusiv), dann S1-S3, nach Schritt 5 S4 | Laufzeit siehe unten |

Laufzeit-HERLEITUNG: v34-Satz rund 8,8 h fuer 12.000 Partien bei 11 Threads (Prereg par.4, aus
PREREG_v34_window par.8a zitiert, dort nicht nachgelesen), also rund 2,6 s Wanduhr je Partie im
Mittel; 100 Partien rund 4-5 min je Arm. Mehrkosten W je Partie: hoechstens 7 Platzsuchen @600 =
4.200 Sims gegen rund 200 Entscheide @100 = 20.000 Sims (Prereg par.2 nennt 3.953 Zuege auf 20
Partien), also rund +21 Prozent, abzueglich der Plattenteilzuege der W-Seite, die heute eigene
Suchen sind und kuenftig entfallen (Rotation, Peeks, Platz, Rueckgabe). Ungemessen, S1 liefert
die Zahl.

Reihenfolge-Begruendung: W zuerst (Nutzer-Schwerpunkt, unabhaengig von S); S in derselben
Wheel-Runde (Prereg par.6), weil Review #11 und der Blend dieselben Funktionen beruehren.

---

## 11. Korrekturen und Ergaenzungen zur Prereg (vor dem Bau eintragen)

1. **R1-Kosten:** "Runde 1 **7** Punkte (1..13)" (Prereg par.2 Folgen) unterstellt unbegrenzten
   Stand. Startstand 5 (board.rs:286), keine Punkte im Drafting (1.2), Zahlung gedeckelt
   (board.rs:345-349): erster R1-Stapelzug kostet E[min(d, 5)] = (1+2+3+4+5*9)/13 = 55/13, rund
   **4,2** Punkte (HERLEITUNG, unter der Annahme, dass W vorher nicht gezogen hat); danach ist W in
   9 von 13 Faellen auf 0 und weitere R1-Stapelzuege sind gratis. NUR fuer den ersten R1-Zug:
   spaeter kostet ein Zug min(d, Punktestand), und nach den Wertungen ist der Stand hoeher (Nutzer
   2026-10-01: mit 12 Punkten nach einer Wertung bringen zwei tiefe Zuege in Runde 2 den Stand schnell
   auf 0; Obergrenze R2 = 7, Mittel 4 je Zug, HERLEITUNG).
2. **Zahl der Platzsuchen:** "rund 8 Platzsuchen @600" -> hoechstens 7, weil die letzte Platte nur
   einen Platz hat (HERLEITUNG Abschnitt 2).
3. **"Rueckgabe-Reihenfolge wie im Sockel":** im Sockel ist die Rueckgabe seit 2026-09-18 ein
   eigener Suchknoten mit Streumuenze im Knotenweg (self_play.rs:4451-4494,
   knob_registry.rs:116). Im W-Zug gibt es keinen Record; die Muenze sollte vor die Platzsuche
   (F4).
4. **Neue Mischstellen:** keine (Prereg par.6 bestaetigt): der Wuerfel ersetzt Wahlen, er mischt
   nichts Verdecktes. Die Platzsuche nutzt die bestehende Determinisierung. Eintrag in
   `docs/architecture_reference.md` nicht noetig (beim Bau gegenlesen).

---

## 11a. Nachpruefung der Code-Belege durch den Koordinator (2026-10-01)

Auf Nutzer-Wunsch die Belege hinter F2, F8, FS2, FS4 selbst gelesen:

* **F2 BESTAETIGT:** `self_play.rs:4507-4514`, Weg C ersetzt nur die gespielte Aktion, `d.policy`
  bleibt die Besuchsverteilung der regulaeren Suche.
* **F8 BESTAETIGT:** `self_play.rs:4660-4663`, der Ausflug-Abzweig speichert nur `state` und
  `branch_kl`; eine je Partie gewuerfelte Seite erbt er nicht ohne eigenen Bau.
* **FS2 BESTAETIGT:** `net_mcts.rs:3061-3063`, bei `w == 0` kehrt der Blend vor jeder
  lambda-Verrechnung zurueck; der Doku-Kommentar von `set_aggression_params` (`net_mcts.rs:785-796`)
  nennt w = 0,1 als gemessenen Betriebspunkt und den lambda-Sweep {0; 0,5; 1; 2}. Folge: ein Stoerer
  braucht w UND lambda je Seite, lambda allein wirkt nicht.
* **FS4 TEILWEISE:** Startsetzung bestaetigt (`search_start_placement` nimmt die `SearchConfig`,
  `net_mcts.rs:7826-7833`). Beim Tiling stimmt die SCHLUSSFOLGERUNG (unvermischt), die zitierte
  Stelle nicht: der Tiling-Stichentscheid liest den rohen Wertkopf in `net_tiling_tiebreak_value`
  (`self_play.rs:2300-2310`), nicht `net_leaf_eval`. `net_leaf_eval` (`net_mcts.rs:3376`) ruft
  dagegen `blended_leaf_win_prob` mit den PROZESSWEITEN Werten (`net_leaf_eval_with`, rund Zeile
  3431) und bedient Label-Pfade und `round_transition_deep.rs:593/709/742`: wer lambda prozessweit
  setzt statt je Seite, vermischt auch diese Labels.

## 12. Offene Nutzerfragen

**F1 WANN legt die W-Seite eine Platte?** VORSCHLAG T1: die normale Suche (100 Sims) entscheidet
den Zeitpunkt; waehlt sie eine Plattenaktion, uebernimmt der Wuerfel. Alternative T2: der Wuerfel
entscheidet auch den Zeitpunkt (z. B. Platten zu festen oder gewuerfelten Halbzuegen der Runde);
das veraendert das Drafting der W-Seite viel staerker.

**F2 Der Ausloser-Record** (Zustand direkt vor dem Plattenzug, Suche ueber alle Aktionen, gespielte
Aktion ersetzt): behalten mit Policy und Wert und als `dice_trigger` markieren (VORSCHLAG, wie
Weg C), oder als Teil des "erzwungenen Plattenzugs" ohne Record?

**F3 Stapeltiefe:** ueber den ganzen Stapel wie festgelegt (VORSCHLAG; Zuege in eigene bekannte
Bloecke zulassen und in S3 zaehlen), oder einschraenken? Eine Einschraenkung auf den unbekannten
Teil entartet nach dem ersten tiefen Zug (3.3).

**F4 Rueckgabekopf im Wuerfelzug:** Streumuenze (p = 0,81 wie Sockel) VOR der Platzsuche wuerfeln
und festnageln, sonst sucht die Suche den Kopf (VORSCHLAG)? Oder immer zufaellig, oder immer Suche?

**F5 Weg C in den W-Klassen** (`deviate_prob` 1,0 wie `policy`): behalten (VORSCHLAG, dann
unterscheiden sich `policy` und `policy-dice` nur in der Behinderung) oder abschalten? (Prereg
par.2 fragt das selbst.)

**F6 Platzsuche @600:** Root-Noise und argmax wie im Sockel (VORSCHLAG, gleiche Einstellung) oder
deterministisch ohne Noise (staerkster Platz)?

**F7 Ausloser bei Muenze "Auslage", aber die Suche wollte ziehen** (oder umgekehrt): einfach
ueberschreiben (VORSCHLAG, so steht es in par.2) ist geklaert; offen nur, ob der Ausloser auch
dann als `dice_trigger` gilt, wenn die Suche `DrawStackPeek` und der Wuerfel "Auslage" waehlt
(VORSCHLAG ja, gleiche Behandlung).

**F8 Ausflug plus Wuerfel:** Kombination verbieten (VORSCHLAG), oder soll ein Ausflug die
Wuerfel-Seite erben?

**F9 Kosten der Wuerfelzuege mitschreiben** (E29): Record-Feld `dome_dice_cost` = [verlangte
Tiefe, bezahlte Punkte] am ersten Record nach jedem erzwungenen Zug (VORSCHLAG), damit die volle
Behinderung auch bei gedeckelten Zahlungen rekonstruierbar bleibt?

**FS1 Gegnermodell in der Suche des Stoerers:** G als normaler Spieler (nicht Nullsumme,
VORSCHLAG, entspricht der Erzeugung) oder Nullsumme auf den Stoerer-Nutzen (alte Task-#28-Semantik)?

**FS2 w fuer den Stoerer:** lambda wirkt nur bei w > 0 (net_mcts.rs:3061-3063). Betriebspunkt laut
Doku w = 0,1 (net_mcts.rs:790-791). lambda-Reihe in S4 bei festem w = 0,1?

**FS3 Bester Zug fuer `own_q_gap`:** ueber welche Wurzelkinder (alle besuchten, Mindestbesuche,
completed-Q)? VORSCHLAG Mindestbesuche gleich der Besuchszahl der letzten Halving-Stufe, beim Bau
festlegen und mitschreiben.

**FS4 Startsetzung und Tiling des Stoerers:** Blend nur im Drafting (VORSCHLAG), oder auch in der
Startsetzung, wo er ueber die `SearchConfig` automatisch mitwirken wuerde?

**Technisch zu pruefen (keine Nutzerfrage):** Policy-Breite von v33-b01 = 414 (Knotentor an); ob
`MOSAIC_PLATTENBAU`/`MOSAIC_SPALTENBAU` in der Kette gesetzt sind; ob ein Such-Cache
Kandidatenlisten speichert; ob `moon_order_target` fuer Plattenaktionen `None` liefert.
