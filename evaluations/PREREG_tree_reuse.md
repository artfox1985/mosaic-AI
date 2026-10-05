<!-- STATUS: OFFEN | Frage: Macht die Wiederverwendung des Teilbaums unter dem gespielten Zug (Gumbel-Wurzel frisch) die 400-Sim-Suche in der Arena staerker, bei unveraendertem Netz? | Beleg: nichts gemessen; Code-Lesung par.2a und additiver Entwurf im Code (Spec-Feld `tree_reuse`, UNKOMPILIERT, 2026-10-05); Nutzer-Entscheide par.5 offen. -->

# Vorregistrierung: Tree Reuse unterhalb der Wurzel (Suchknopf, Spieler-Identitaet)

**Angelegt 2026-10-05 00:5x auf Nutzer-Anweisung** (*"registrier das so und auch tree reuse"*), waehrend die
v35-b02-Erzeugung lief. Herkunft: `RESEARCH_search_alternatives_external_2026-08-22.md` Abschnitt S3.1 und
Empfehlung O3 (Z. 498-512): "der Teilbaum unter dem gespielten Zug wird uebernommen; die Gumbel-Ziehung und
Sequential Halving an der Wurzel laufen neu", belegt als Standardpraxis in Engines, +110 Elo fuer die Graph-Variante
in Crazyhouse und 54,8 auf 67,4 Prozent fuer Pondering (Zitate dort mit Quellenmarken). Die Einschaetzung des
Dokuments steht mit: "es gibt mehr Rechenzeit, nicht mehr Absicht" (Z. 511-512). Fuer Tor 1 zaehlt Staerke bei
festem Sim-Budget, und genau dort wirkt der Knopf. Einordnung 2026-10-05: `PREREG_v35_window.md` par.11d (die Suche
ist dem Netz nur bei genug Tiefe voraus) und Rzepecki 2025 (Suchtiefe als groesster Einzelhebel in Azul,
`RESEARCH_heuristic_methodology_external_2026-08-25.md` 6a).

## par.1 Frage

Spielt `v34-b01_brierbest` mit der Champion-Spec PLUS Teilbaum-Wiederverwendung bei 400 Sims je Zug staerker als
dieselbe Spec ohne, gepaart, gegen sich selbst? Das ist eine Spieler-Identitaet (Netz plus Spec), kein Netzarm;
gewinnt sie, ist sie Kandidat fuer die Promotion als Paket, wie v34-b01 (Netz plus Startkuppel-Suche plus Runde 5
per Netz, `PREREG_v34_window.md` par.2a).

## par.2 Bauform (konkret nach der Code-Lesung par.2a, 2026-10-05; ENTWURF im Code, NICHT kompiliert)

**Stand:** der Entwurf steht im Arbeitsbaum (Dateiliste am Ende von par.2a), geschrieben waehrend der exklusiven
v35-b02-Erzeugung ohne jeden Build. Nichts davon ist kompiliert, getestet oder gemessen; alles unten im Praesens
beschreibt den Entwurf, nicht ein aktives Verhalten.

* **Knopf.** Spec-Feld `tree_reuse` (OPTIONAL, 0 oder 1 als Zahl; fehlt es, gilt der Env-Default
  `MOSAIC_TREE_REUSE`, ohne Variable 0). Muster genau wie `r5_net_solver`: `SearchConfig::tree_reuse`,
  `read_tree_reuse_env` ohne `OnceLock` (Seiten-Feld), `spec_flag(...)` in `from_spec_file`, `KNOWN_FIELDS`,
  `search_config_off` = `false`, `spec_env.py`-Zuordnung, Lauf-Manifest `engine_config_json` (Env-Default),
  Registratur `knob_registry.rs` und `docs/knobs.md` (Status aktiv, Default aus, Verdikt OFFEN).
* **Wirkort.** NUR der Arena-Agent `self_play::NetArenaAgent` (paired_gating -> `net_vs_net_arena_match` ->
  `run_net_vs_net_arena` -> `play_net_vs_net_game`, und `play_net_game`). NICHT: Self-Play-Erzeugung (par.5
  Punkt 1 offen), Referee/eingefrorene Worker und GUI (zustandslos "Stellung rein, Zug raus", par.2a Punkt 2),
  Hybrid-Arena, Record-Einstiege.
* **Haltestruktur.** Je Seite und Partie ein `RefCell<Option<RetainedTree>>` im Agenten (Feld `retained_tree`;
  `RefCell`, weil `DraftingAgent::decide` `&self` nimmt). `RetainedTree` haelt den GANZEN `Vec<Node>` der letzten
  eigenen Suche. Lebensdauer = der Agent = eine Partie (Agenten werden je Partie gebaut).
* **Wiederfinden.** Abweichend von der Vorgabe (Kante = eigener Zug, dann Kante = Gegnerzug) sucht
  `take_reuse_start` den Folgezustand ueber den ZUSTAND: Kandidat ist jeder Knoten ausser der alten Wurzel, an dem
  diese Seite in derselben Runde im Drafting zieht (Besuche > 0, kein Zufallsknoten), Treffer nach
  `retained_world_matches` (unten), unter mehreren Treffern der meistbesuchte. Grund: zwischen zwei Entscheiden
  liegen nicht immer genau zwei Kanten (zweistufige Kuppelwahl, Stapelzug, Ein-Aktion-Kurzschluss ohne Suche,
  Bauer-Vorzug ohne Suche, Mondstapel-Nachsuche mit anderer Reihenfolge als die Baumkante), und der Agent kennt
  den Zugverlauf dazwischen nicht. Der Zustandsvergleich ist damit nicht Sicherung, sondern das Kriterium.
* **Zustandsvergleich und Welt.** Es gibt keinen Zustands-Hash (`GameState` leitet nur `Debug, Clone` ab,
  par.2a Punkt 2). Weil jede Suche ihre Wurzel determinisiert (par.2a Punkt 3), traegt der gehaltene Knoten die
  verdeckten Werte SEINER Welt, der echte Zustand die echten. `retained_world_matches` prueft deshalb (a) die
  Struktur des Verdeckten (Stapellaenge, Multimenge der Platten-IDs, `dome_pool_known_blocks`, eigene
  Rueckgabe-Bloecke positionsgleich, Typ der obersten Platte, dieselben Fabriken mit verdecktem Chip, Multimenge
  der verdeckten Chips) und (b) nach Einsetzen der verdeckten Felder der Welt in eine Kopie des echten Zustands
  die Gleichheit von `serialize::state_to_json_exact`. Bei Treffer laeuft die neue Suche in der ALTEN Welt weiter
  (keine neue Wurzel-Determinisierung). Der Vergleich ist konservativ: jede nicht eingesetzte verdeckte Differenz
  gibt "kein Treffer".
* **Nichtuebereinstimmung.** Kein Treffer = frische Suche, Zeile fuer Zeile der Bestandsweg
  (`build_gumbel_tree_inner_for` mit `retained_root = None`, Zugwahl `select_final_root_child`); der alte Baum wird
  verworfen und durch den neuen ersetzt. Ebenso frisch und ohne Halten: Runde 5 (`round5::applies`, Vorgabe; der
  Code zwingt das nicht, par.2a Punkt 7), Runde-5-Loeser, ISMCTS k > 1, Klasse-W-Zufallsknoten, PUCT-Pfad.
* **Wurzel frisch, Kinder uebernommen.** Im Gumbel-Rumpf wandern die Kinder der uebernommenen Wurzel als
  (Aktion, Prior) zurueck in die Kandidatenliste; Gumbel-Top-m (Arena: g = 0, also Top-m nach Prior) und
  Sequential Halving laufen neu ueber ALLE Kandidaten. Gezogene Kandidaten mit vorhandenem Kind starten mit dessen
  Besuchen, Werten, Prioren und Teilbaum; nicht gezogene alte Kinder bleiben als verwaiste Knoten im Vektor
  (unerreichbar). Kein Wurzelrauschen im Arena-Pfad (par.2a Punkt 4).
* **Finale Zugwahl.** Die Bestandsregel `gumbel_final_root_action` nimmt "Kinder mit maximalen Besuchen" als
  die Halving-Ueberlebenden; mit uebernommenen Besuchen gilt das nicht mehr. Die Reuse-Suche reicht die
  Ueberlebenden deshalb ausdruecklich heraus (`survivors_out`) und waehlt mit derselben Formel
  `ln(prior) + sigma(Q)` ueber sie (`gumbel_final_root_action_among`), danach wie im Bestand
  `color_denial_probe` und `apply_denial_tiebreak` (beide im Champion aus).
* **Budget.** `sims` bleibt die Zahl NEUER Simulationen (`budget_used` im Halving, `for _ in 0..sims` bei einem
  Kandidaten). Uebernommene Besuche zaehlen getrennt: thread-lokales `TreeReuseDiag` je Spieler (Suchen, davon
  Treffer, Summe uebernommener Wurzelbesuche, Summe neuer Sims), am Partieende EINE Logzeile `[tree_reuse] p0 ...
  | p1 ...`, nur wenn eine Seite mit Knopf an gesucht hat.
* **Byte-gleich bei 0.** `tree_reuse == false` ruft `net_arena_choose_action` -> unveraenderter
  `net_search_drafting_action`; die zwei neuen Parameter des Gumbel-Rumpfs sind dort `None`, die neuen Bloecke
  sind hinter `reused` (= `false`) und allokieren nicht; der thread-lokale Zaehler wird nur gelesen und bleibt
  null, die Logzeile entfaellt; keine RNG-Ziehung mehr oder weniger. Bei 1 ohne Treffer verbraucht die Suche
  dieselben Zufallszahlen wie der Bestand; mit Treffer entfallen die Ziehungen der Wurzel-Determinisierung (der
  Such-RNG ist je Entscheid frisch aus `derive_search_seed`, die Verschiebung bleibt im Entscheid).
* **Pflichtabnahmen** (unveraendert, ergaenzt): Knopf aus byte-gleich (Lib-Suite, Netz-Paritaets-Fixture, Golden
  Probe), Anker-Drift und -Konservierung (`/mosaic-anchor-invariance`), Determinismus-Probe mit Knopf AN (zwei
  Laeufe gleicher Seeds byte-gleich), Gleichwertigkeit "an, kein Treffer" = Bestand, Unit-Tests zu
  `extract_subtree` (Besuche, Werte, Eltern-Kind-Konsistenz), `take_reuse_start` (Treffer nach eigenem und
  Gegnerzug; Verwerfen bei anders aufgedeckter verdeckter Information) und Budget (neue Wurzelbesuche == `sims`),
  Kostentor (s je Partie mit und ohne Knopf, 2 x 20 Paare) mit Trefferquote und Speicher aus `[tree_reuse]`.
  Der Abnahme-Block steht zusaetzlich als Kommentar in `net_mcts.rs` ueber `RetainedTree`.

*Fassung der Vorgabe vor der Code-Lesung (2026-10-05 00:5x), zur Nachvollziehbarkeit:* Kante = gespielte eigene
Aktion, dann Kante = Gegnerzug, Hash-Pruefung des Zustands; Wirkung im Arena-/GUI-Pfad, optional Erzeugung; kein
Reuse ueber den Rundenuebergang und in Runde 5; Budget = neue Sims. Abweichungen oben: Zustandssuche statt
Kantenweg, kein Hash (es gibt keinen), GUI/Referee nicht verdrahtet, Welt-Uebernahme statt Neudeterminisierung,
Zugwahl ueber die ausdruecklichen Ueberlebenden.

## par.2a CODE-LESUNG (2026-10-05)

Gelesen in dieser Sitzung; Zeilen nach dem Entwurf (net_mcts.rs ist dadurch gewachsen), Funktionsnamen tragen.

1. **Baum je Zug: anlegen und freigeben.** Der Baum ist ein lokaler `Vec<Node>`, angelegt in
   `build_gumbel_tree_inner_for` (net_mcts.rs:6792; Bestand `vec![make_node(..)]` fuer die Wurzel, jetzt im
   `match retained_root`), Kinder per `nodes.push` bei der Expansion (`descend_and_backprop` net_mcts.rs:6339 und
   `visit_candidate!` im Rumpf). Er wird per Wert an `net_search_drafting_action` (net_mcts.rs:7861, Aufruf
   :7886 ueber `build_net_tree` :7228) zurueckgegeben, dort ausgewertet und am Funktionsende fallen gelassen.
   Keine Arena-/Pool-Struktur, kein Wiederverwenden von Speicher: Lebensdauer = ein Aufruf. `Node`
   (net_mcts.rs:3116) haelt Eltern-/Kind-INDIZES, `untried`, `visits`, `value`, `prior`, eine VOLLE
   `GameState`-Kopie, Blattwerte und Diagnose-Akkumulatoren. Damit ist ein additiver Bau moeglich: der Vektor
   laesst sich herausreichen, umnummerieren und wieder einsetzen.
2. **Wurzelzustand, Zustands-Identitaet.** Uebergabe als `&GameState`, im Rumpf geklont, Log geleert,
   determinisiert (net_mcts.rs:6807-6813). `GameState` leitet nur `Debug, Clone` ab (state.rs:64), kein
   `PartialEq`, kein `Hash`; im Suchpfad gibt es keine Zustands-Identitaet. Kanten tragen `Node::action`
   (`Action` ist vergleichbar). Vollstaendiger Vergleich ist ueber `serialize::state_to_json_exact`
   (serialize.rs:1509, mit Reihenfolgen von Beutel, Turm, Stapel, Chip-Vorrat, Wissensbloecken, `pending_*`)
   moeglich; UNGEPRUEFT, ob er jedes Feld traegt, das die Suche liest. Arena-Agenten sind zustandslos
   (`NetArenaAgent`, self_play.rs:5425); der Worker-Einstieg fuer Referee und eingefrorene Artefakte ist
   ausdruecklich "Stellung rein, Zug raus" (lib.rs ab 1390), die Referee-Aufrufe (referee.rs:262, :902) bauen je
   Entscheid einen frischen RNG und halten nichts. Reuse dort braucht einen Halter in `RefereeGame`, nicht gebaut.
3. **Determinisierung.** Ja, EINE Welt je Suche: `DETERMINIZE_ROOT_HIDDEN_INFO = true` (net_mcts.rs:2530)
   mischt an der Wurzel das unbekannte Stapelpraefix und fremde Rueckgabe-Bloecke (`state::determinize_dome_pool`,
   Betrachter = Suchender) und die verdeckten Bonuschips (`determinize_hidden_information_for`, :2562).
   ISMCTS mit mehreren Welten nur bei `MOSAIC_NUM_DETERMINIZATIONS` > 1 (`num_determinizations` :2677, Default
   `NUM_DETERMINIZATIONS = 1` :2656). Folge: ein Teilbaum gilt nur in seiner Welt; unter einer frisch gezogenen
   Welt sind auch die Kindstatistiken des sichtbaren Zustands nicht uebertragbar, weil Zuege im Teilbaum (Stapel
   ziehen, Chip aufdecken) Werte der alten Welt sichtbar gemacht haben. Ausweg im Entwurf: die alte Welt
   behalten, solange sie mit dem Gesehenen vereinbar ist (par.2, "Zustandsvergleich und Welt"). HERLEITUNG
   (ungeprueft): eine Stichprobe aus der alten Informationsmenge, bedingt auf die seitdem gesehenen
   Beobachtungen, ist eine Stichprobe aus der neuen; offen, ob das Gegnerverhalten (es haengt am Gegnerwissen)
   diese Bedingung verzerrt. Gefuehrt in `docs/architecture_reference.md`, Abschnitt "Wo der Code Information
   ABSICHTLICH vernichtet" (Tabelle ab Zeile 103); neue Zeile 140 fuer den Entwurf.
4. **Wurzel.** Gumbel-Werte g je Kandidat nur bei `add_root_noise` (net_mcts.rs:6874); der Arena-Pfad ruft mit
   `false` (self_play.rs `net_arena_choose_action_with_tree`), also g = 0 und Top-m nach Prior. m =
   `gumbel_top_m_for_budget(sims)` = round(sims/16) begrenzt auf 4 bis `GUMBEL_TOP_M` = 16 (:4866, :4828), bei
   400 also 16. Sequential Halving :7035, Restverteilung :7129, Zugwahl `select_final_root_child` (:5737) ->
   `gumbel_final_root_action` (:5405) unter den Kindern mit maximalen Besuchen. Dirichlet-Rauschen gibt es nur
   im PUCT-Altpfad (:7290), `USE_GUMBEL_SEARCH = true` (:5010). Frisch je Suche gehoeren zur Wurzel: g, die
   Top-m-Menge, das Budget, `halving_min_visits`, die K1-Wurzelmarge (`with_root_margin` :3705) und das Salz der
   Variante B (`with_round_transition_leaf_context` :3732). Uebertragbar sind die Knotengroessen unterhalb der
   Wurzel (Besuche, Wertsummen, Prior, `im_value`, `own_value_sum`, `untried`). Einschraenkung: Blattwerte, die
   unter K1 (`score_utility_c != 0`) oder Variante B (`round_transition_leaf = 1`) entstanden, haengen an der
   ALTEN Wurzelmarge bzw. am alten Salz. Im Champion beide aus (`models/v34-b01_brierbest.spec.json`:
   `score_utility_c` 0,0; `round_transition_leaf` fehlt, Env-Default 0, net_mcts.rs:608).
5. **Sims-Zaehlung.** Das Budget ist der Parameter `sims`; gezaehlt wird im Halving per `budget_used`
   (:7035-7140), bei einem einzigen Kandidaten per `for _ in 0..sims`. In der Arena ist `sims` =
   `net_effective_sims(r5_adjusted_base_sims(..), n)` = Basis-Sims (`DECOUPLE_NET_SIMS_FROM_ACTIONS = true`,
   :5029; `r5_adjusted_base_sims` :7803). Uebernommene Besuche gehen nicht durch `budget_used` und werden im
   Entwurf getrennt gezaehlt (`TreeReuseDiag::retained_visits`, Logzeile `[tree_reuse]`).
6. **Threads.** Eine Suche ist einfaedig (kein rayon im Suchpfad von net_mcts.rs); parallel sind die PARTIEN
   (`run_net_vs_net_arena`, self_play.rs:7987 `into_par_iter`). Der optionale Sammel-Faden (Weg V,
   net_batcher.rs Kopf) buendelt nur Netzauswertungen mehrerer Partie-Faeden, jede Suche hat hoechstens ein
   offenes Blatt und besitzt ihren Baum allein. Agenten werden je Partie gebaut (self_play.rs:7860), also kann der
   Baum im Agenten leben, ohne Sperren; `decide(&self, ..)` (self_play.rs:5268) erzwingt `RefCell`.
7. **Rundenuebergang und Runde 5.** Ein Knoten ist terminal, sobald die Phase nicht mehr Drafting ist
   (`make_node` net_mcts.rs:4165); der Baum endet also am Rundenende, und kein Knoten liegt jenseits des
   Uebergangs: ein Treffer ueber die Runde hinweg ist strukturell ausgeschlossen. Runde 5:
   `r5_solver_takes_over` (:7777) gibt bei `r5_net_solver` an an den Loeser ab; der Champion faehrt
   `r5_net_solver: 0`, sucht in Runde 5 also mit demselben Gumbel-Baum (Sims aus `r5_net_sims`, fehlt in der
   Spec, also Basis-Sims). Der Code laesst Reuse in Runde 5 technisch zu; der Entwurf schliesst sie trotzdem aus
   (Vorgabe par.2, `round5::applies`, round5.rs:106). Nutzer-/Koordinator-Entscheid offen; eine Zeile in
   `net_search_drafting_action_reuse`.
8. **Speicher.** Jede Simulation legt hoechstens einen Entscheidungsknoten an (Expansion in
   `descend_and_backprop` bzw. `visit_candidate!`, ohne Klasse-W-Zufallsknoten), also hoechstens sims + 1 = 401
   Knoten je Suche @400 (HERLEITUNG aus dem Code, nicht gezaehlt). Jeder Knoten traegt eine volle
   `GameState`-Kopie; deren Bytegroesse ist NICHT gemessen (gemessen ist nur die Klonzeit, 4,61 us Mittelspiel,
   docs/measured_runtimes.md:212). Mit Reuse haelt eine Seite den ganzen letzten Baum, die naechste Suche
   startet mit dem Teilbaum des Treffers plus hoechstens 400 neuen Knoten; verwaiste alte Wurzelkinder bleiben
   bis zum naechsten Ausschnitt im Vektor. Speicher je Partie gehoert ins Kostentor.

**Geaenderte Dateien (Entwurf, ungebaut):** `engine/src/net_mcts.rs` (Feld, Env-Leser, Spec, Rumpf-Parameter,
Reuse-Block mit Abnahme-Kommentar), `engine/src/self_play.rs` (Agentenfeld, `net_arena_choose_action_with_tree`,
Diagnosezeile), `engine/src/lib.rs` (Manifest), `engine/examples/kernbeweis_910002_probe.rs` (Literal),
`engine/src/knob_registry.rs`, `docs/knobs.md` (von Hand im Generatorformat, `python
tools/generate_knob_docs.py --check` steht aus), `spec_env.py`, `docs/architecture_reference.md`.

**Unsicherheiten (markiert):** (a) nicht kompiliert; (b) Vollstaendigkeit von `state_to_json_exact` als
Gleichheitstest; (c) die Welt-Uebernahme als Stichprobe (Punkt 3); (d) mit uebernommenen Besuchen waechst
`max_n` in `gumbel_sigma`, Q wiegt im Halving staerker als im Bestand, ungemessen; (e) Top-m nach Prior verwirft
gut besuchte alte Kinder mit kleinem Prior; (f) Trefferquote unbekannt: ein Treffer braucht den echten Gegnerzug
als expandierten Knoten unter dem gespielten Kind; (g) Entscheide werden verlaufsabhaengig: eine Einzelstellung
nachzusuchen (Replay, Diagnose-Sonden) reproduziert den Arena-Zug mit Knopf an nicht mehr.

## par.3 Messung (Tor, vorab)

Gepaarte Arena `tools/paired_gating.py`, A = `v34-b01_brierbest` mit Spec `v34-b01_brierbest` plus `tree_reuse` 1,
B = dieselbe Spec ohne; 400 Sims beide, Blockgroesse 5, `--log-games`, Seeds 20261600/20261601 a 200 Paare,
Stufenregel 20261602. Kriterium wie Tor 1: Block-z >= +1,96 oder gepoolt >= 52,5 Prozent ohne Gegenbefund.
Berichtet: die sechs Standard-Kennzahlen, volle Spalten je Seite (Tor 2b), Zugzeit je Seite. Zuordnung vorab:
ein Gewinn gehoert dem Knopf allein (gleiches Netz, gleiche Spec sonst).

## par.4 Kosten (HERLEITUNG)

Engine-Bau rund ein Tag inklusive Wheel-Runde, Anker, Fixture, Smoke; Arena 2 x rund 1,5 h exklusiv. Erwartung
des Koordinators (Schaetzung, keine Messung): die beste Einzelchance unter den ungebauten Research-Empfehlungen,
weil sie die Suche bei gleichem Budget tiefer macht; der externe Beleg stammt aus Schachvarianten, die
Uebertragung auf ein Spiel mit Zufallsknoten je Runde ist ungemessen.

## par.5 Offen (Nutzer-Entscheide vor dem Bau)

1. Reuse auch in der Erzeugung oder nur in der Arena. **Nutzer 2026-10-05 01:2x gibt die Frage zurueck mit den
   Kriterien Diversitaet und Durchlaufzeit.** Vorgehen daraus (Koordinator, vorab): ZUERST die Arena (par.3,
   saubere Zuordnung), DANN eine Erzeugungs-Sonde mit und ohne Knopf bei gleichen Sims und gleichem Seed
   (je 100 Partien Klasse `policy`-Form, Modus 2): (a) Durchlaufzeit s je Partie; (b) Diversitaet mit den
   vorhandenen Instrumenten (zustandsbasierte Neuheitsmessung `tools/probes/*novelty*`, Anteil distinkter
   Bretter zu Rundenbeginn, KL der Policy-Ziele gegen den Prior wie par.8b1 der Asym-Prereg, erste
   Abweichung gegen die Bezugspartie); (c) Zielqualitaet: `root_q_compare` auf den erzeugten Records. HERLEITUNG
   vorab: Reuse macht aufeinanderfolgende Zuege derselben Seite konsistenter (weniger Rauschen zwischen
   Suchen, mehr Absichtspersistenz, S3 des Such-Dokuments) und schwaecht das frische Wurzelrauschen, weil
   uebernommene Besuche es verduennen; die expliziten Diversitaetsknoepfe (Weg C, Ausflug, Startslot,
   Spiegel, Stichentscheid) bleiben. Leseregel: Erzeugung mit Knopf nur, wenn s je Partie nicht steigt UND
   die Neuheitsmasse nicht unter den Bestand fallen (CI) UND root_q-Vorsprung in Runde 1-3 nicht kleiner wird.
2. Reihenfolge gegen die Netzarme b03 bis b07 (`PREREG_v35_window.md` par.13-15): der Bau kann parallel zur
   Erzeugung laufen (keine Last), Kompilat und Arena erst nach der Kette.
3. Zaehlweise des Budgets (siehe par.2, "Sims je Zug").
4. Runde 5 (aus der Code-Lesung par.2a, Punkt 7): der Champion faehrt `r5_net_solver` 0 und sucht in Runde 5 mit
   demselben Gumbel-Baum; Reuse waere dort technisch moeglich. Der Entwurf SCHLIESST Runde 5 aus (eine Zeile in
   `net_search_drafting_action_reuse`, `round5::applies`), gemaess der urspruenglichen Vorgabe. Nutzer-Entscheid:
   Ausschluss behalten (Vorschlag des Koordinators fuer die erste Arena: ja, damit der Knopf nur eine Sache
   aendert) oder Runde 5 mitnehmen.
5. Verlaufsabhaengigkeit (par.2a): mit Knopf an haengt ein Entscheid vom Verlauf ab; Einzelstellungs-Werkzeuge
   (Replays, Sonden, GUI) liefern dann nicht mehr den Arena-Zug. Fuer Sonden gilt darum Knopf aus, und die
   Determinismus-Pruefung laeuft als ganze Partie bei gleichem Seed.
