<!-- STATUS: ENTSCHIEDEN | Frage: Macht die Wiederverwendung des Teilbaums unter dem gespielten Zug (Gumbel-Wurzel frisch) die 400-Sim-Suche in der Arena staerker, bei unveraendertem Netz? | Beleg: TRAEGT, KNAPP (par.3c): v35-b17 = v34-b01 + tree_reuse-Spec gegen v34-b01 ohne, drei Seeds 637:563 = 53,1 %, Block-z +2,22 (120 Bloecke), Punkte +1,1 bis +2,1 je Seed; gleiches Netz, Gewinn gehoert der Suche. Kompilat, Wheel cd8995bf, Anker-Drift GRUEN (par.2b). b18 (Spec auf b16) im Schnellblick gegen b16 51,0 %, nicht spannend (par.3e); volle Breite und par.5.6 = Nutzer-Entscheid. -->

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
* **Runde-5-Schalter** (ergaenzt 2026-10-06 nach dem Entscheid par.5.4, ENTWURF, UNKOMPILIERT). Spec-Feld
  `tree_reuse_round5` (OPTIONAL, 0 oder 1 als Zahl; fehlt es, gilt der Env-Default `MOSAIC_TREE_REUSE_ROUND5`,
  ohne Variable **1**). Dasselbe Muster wie `tree_reuse`: `SearchConfig::tree_reuse_round5`,
  `read_tree_reuse_round5_env` (Default `TREE_REUSE_ROUND5_DEFAULT = true`, auch bei ungueltigem Wert, einmalige
  Warnung), `spec_flag(...)`, `KNOWN_FIELDS`, `search_config_off` = Default (bei `tree_reuse` = `false` dort
  wirkungslos), `spec_env.py`, Lauf-Manifest, Registratur. **Wirkt nur bei `tree_reuse` 1:** bei 1 entfaellt der
  Runde-5-Ausschluss in `net_search_drafting_action_reuse`, Runde 5 laeuft mit gehaltenem Baum wie R1-R4; bei 0
  bleibt der Ausschluss ueber `round5::applies` aus dem ersten Entwurf stehen. Der Runde-5-Loeser
  (`r5_solver_takes_over`) bleibt in beiden Faellen ohne Reuse.
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
  verworfen und durch den neuen ersetzt. Ebenso frisch und ohne Halten: Runde-5-Loeser, ISMCTS k > 1,
  Klasse-W-Zufallsknoten, PUCT-Pfad, und Runde 5 nur bei `tree_reuse_round5` 0 (`round5::applies`; Default 1 =
  Runde 5 mit Reuse, par.5.4).
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
   `net_search_drafting_action_reuse`. **Nachtrag 2026-10-06:** entschieden (par.5.4), der Ausschluss haengt jetzt
   am Schalter `tree_reuse_round5` (par.2), Default 1 = Runde 5 mit Reuse.
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

## par.2b KOMPILAT, WHEEL, ANKER, NAMEN UND SMOKE (2026-10-08 15:35-15:55, Nutzer: "zuerst die technisch offenen themen")

**Kompilat.** Der Entwurf aus par.2 (seit 2026-10-05 unkompiliert) hatte genau einen Fehler: E0502 an der Wurzel-Uebernahme
(`net_mcts.rs` um Zeile 6902, `nodes[0].untried.push((act, nodes[cid].prior))` leiht `nodes` doppelt); behoben durch Lesen des
Priors vor dem Push (Commit `1b256d1a`). Danach `cargo test --release --no-run` ohne Warnung (Bibliothek, Tests, Beispiele,
Benches), `cargo test --release` **861 bestanden, 0 fehlgeschlagen, 23 ignoriert** (325 s), darin die Netz-Paritaets-Fixture
`net_parity_hash_matches_champion_fixture` und die Knopfregister-Waechter (`knob_registry::tests`, mit den sechs neuen
Eintraegen aus par.19 der v35-Prereg).

**Wheel und Anker.** `python -m maturin build --release` 36,6 s, Wheel `mosaic_rust-1.1.0-cp314-cp314-win_amd64.whl` sha256
`cd8995bf71c6…db21`, installiert. Anker-Drift gegen `hv4_anchor` (`/mosaic-anchor-invariance`): **GRUEN, 1.763 Schritte Feld
fuer Feld gleich** (`anchor_drift_live_wheel_20261008_treereuse.json`, 25 s). Der Knopf ist per Default aus (`MOSAIC_TREE_REUSE`
ohne Variable 0, `net_mcts.rs:395-405`), der Anker bewegt sich mit dem neuen Wheel nicht; die Konservierungs-Pruefung (`--venv`)
war nicht faellig (kein Umgebungswechsel).

**Namen (gemessene Identitaet = Modell plus Spec, Hausregel):**

| Name | Netz | Spec | Zweck |
| --- | --- | --- | --- |
| **v35-b17** | `alphazero_v34-b01_brierbest.onnx` | `models/v35-b17.spec.json` = Champion-Spec plus `tree_reuse` 1, `tree_reuse_round5` 1 | Arm A von par.3; Gewinn gehoert dem Knopf allein |
| v35-b18 (reserviert) | `alphazero_v35-b10_brierbest.onnx` | dieselbe Spec | nur falls b17 traegt: Knopf auf dem staerksten Netz der Reihe |

Nutzer 2026-10-08: Namen vorgeschlagen, keine Aenderung gewuenscht (Chat "haben wir schon namen registriert", Antwort: nein,
Vorschlag b17/b18).

**Smoke (`smoke_tree_reuse_v35-b17_vs_v34-b01_s20261690.json`, 5 Paare @400, `--fixed-length`, 10 Threads):** laeuft durch,
3:7 (n = 10, keine Aussage), 204,6 s = 20,5 s je Partie. Diagnose je Partie aus dem Log (`[tree_reuse]`, `self_play.rs:6869-6876`,
`TreeReuseDiag` `net_mcts.rs:8035`): die Reuse-Seite uebernimmt den Baum in rund zwei Dritteln ihrer Suchen (Beispiele: 46 von
71, 45 von 70, 47 von 66, 49 von 73 Suchen; Grundmenge Suchen je Partie und Seite), uebernommene Besuche 4.919 bis 8.310 je Partie
gegen 26.400 bis 30.400 neue Sims (also rund 18 bis 29 % Zusatzbesuche), die Gegenseite 0/0 (Knopf wirkt nur ueber die Spec der
Seite A, wie gebaut). Nicht uebernommen wird, wenn der Zustandsvergleich `retained_world_matches` keinen Treffer gibt (Zufallsknoten,
Stapelzuege, andere Mondreihenfolge; par.2); der Anteil der Fehlschlaege (rund ein Drittel) ist damit die erste Zahl zu par.5.6.
**Zugzeit:** 20,5 s je Partie gegen 17,6 bis 18,1 s in den Schnellblick-Laeufen desselben Tages (beide Seiten ohne Reuse); ob der
Aufschlag der Reuse-Seite gehoert (Zustandsvergleich, Baum-Halten) oder der Nebenlast (ein Agent lief Unit-Tests), ist UNGEPRUEFT;
die Arena misst es ohne Nebenlast, aber nicht je Seite getrennt (paired_gating fuehrt keine Zugzeit je Seite).

**Arena par.3** startet als `tools/tree_reuse_arena_chain.sh` (Seeds 20261600/20261601 a 200 Paare, Stufenregel 20261602,
`--resume`, sechs Kennzahlen je Seed, Block-z gepoolt; Kosten HERLEITUNG rund 2 h je Seed bei 18 bis 20 s je Partie).

## par.3 Messung (Tor, vorab)

Gepaarte Arena `tools/paired_gating.py`, A = `v34-b01_brierbest` mit Spec `v34-b01_brierbest` plus `tree_reuse` 1
und `tree_reuse_round5` 1 (Runde 5 MIT Reuse, par.5.4), B = dieselbe Spec ohne; 400 Sims beide, Blockgroesse 5, `--log-games`, Seeds 20261600/20261601 a 200 Paare,
Stufenregel 20261602. Kriterium wie Tor 1: Block-z >= +1,96 oder gepoolt >= 52,5 Prozent ohne Gegenbefund.
Berichtet: die sechs Standard-Kennzahlen, volle Spalten je Seite (Tor 2b), Zugzeit je Seite. Zuordnung vorab:
ein Gewinn gehoert dem Knopf allein (gleiches Netz, gleiche Spec sonst).

### par.3a ERGEBNIS SEED 1 (2026-10-08 16:24-18:53, `tools/tree_reuse_arena_chain.sh`, Tab c10; Nebenlast: Sekunden-Trockenpruefungen eines Ketten-Agenten, s. u.)

**Seed 20261600: v35-b17 223:177 = 55,8 %** (n = 400, 200 Paare, Deckel), SPRT `UNDECIDED_CAP_REACHED` (LLR +2,26), **Block-z
+2,42** (40 Bloecke, Mittel 0,558, sd 0,150), gepaarte Differenz +0,23, McNemar p = 0,030, A-Sweep 63 / B-Sweep 40 / Split 97.
Laufzeit 7.480,2 s = **18,70 s je Partie** (10 Threads; Schnellblick-Laeufe ohne Reuse am selben Tag 17,6 bis 18,2 s: der Aufschlag
der Reuse-Seite liegt damit HERLEITUNG bei rund 3 bis 6 % der Partiezeit, nicht je Seite getrennt erhoben). Nebenlast: ein Agent
hat waehrend des Laufs Trockenpruefungen von wenigen Sekunden gefahren (Importe, Dry-Runs), gemeldet nach CLAUDE.md; Block-
zeiten unauffaellig.

Die sechs Kennzahlen (Grundmenge Bretter je Modell, n = 400 je Seite; gleiches Netz beidseits, Unterschied allein der Knopf):

| Kennzahl je Brett | v35-b17 (Reuse) | v34-b01 (ohne) | gepaart [KI95] |
| --- | --- | --- | --- |
| Volle Spalten | **1,160 +- 0,037** | 1,048 +- 0,036 | - |
| Spalten >= 4 | 2,34 | 2,34 | - |
| Zeilenfuellung H | 0,620 | 0,598 | - |
| Strafsteine | 8,07 | 7,82 | - |
| Eigene Punkte | 58,62 | 56,55 | - |
| Margin | +2,06 | -2,06 | - |
| Plattenpunkte gesamt | 8,76 | 8,12 | - |
| Platzierungspunkte | 54,94 | 53,22 | - |
| davon Vertikale Reihen (83 Paare) | | | **+1,60 [+0,61; +2,60]** |
| davon Spezialfelder (76 Paare) | | | -0,34 [-1,12; +0,45] |

**Lesung vorab (ohne Verdikt, das faellt gepoolt):** der Knopf aendert nicht die Priorwahl (Spalten >= 4 gleich), sondern die
Vollendung: 0,11 volle Spalten je Brett mehr bei gleichem Netz ist der groesste Spalteneffekt der v35-Reihe (b02 gegen v34-b01:
+0,05 bis +0,08; b09 +0,02 bis +0,08), und die vertikalen Reihen tragen als einziges Kriterium mit CI ueber 0. Passt zur
Erwartung par.1/S3 (Absichtspersistenz: der gehaltene Teilbaum traegt die begonnene Spalte ueber mehrere Zuege). Seed 20261601
laeuft seit 18:53 (Stand nach 40 Paaren 37:43).

### par.3b ERGEBNIS SEED 2 UND STUFENREGEL (2026-10-08 18:53-20:31, exklusiv)

**Seed 20261601: v35-b17 204:196 = 51,0 %** (n = 400, 200 Paare, Deckel), SPRT `UNDECIDED_CAP_REACHED` (LLR -3,29), Block-z **+0,42**
(40 Bloecke, Mittel 0,510, sd 0,150), gepaarte Differenz +0,04, McNemar p = 0,76, A-Sweep 50 / B-Sweep 46 / Split 104. Laufzeit
7.333,0 s = 18,33 s je Partie (Seed 1 18,70 s).

Die sechs Kennzahlen (Bretter je Modell, n = 400 je Seite):

| Kennzahl je Brett | v35-b17 (Reuse) | v34-b01 (ohne) | gepaart [KI95] |
| --- | --- | --- | --- |
| Volle Spalten | 1,045 +- 0,037 | 1,025 +- 0,037 | - |
| Spalten >= 4 | 2,36 | 2,35 | - |
| Zeilenfuellung H | 0,609 | 0,593 | - |
| Strafsteine | 7,81 | 8,01 | - |
| Eigene Punkte | 57,87 | 56,80 | - |
| Margin | +1,07 | -1,07 | - |
| Plattenpunkte gesamt | 8,41 | 8,55 | - |
| Platzierungspunkte | 54,34 | 53,62 | - |
| davon Vertikale Reihen (84 Paare) | | | -0,25 [-1,30; +0,80] |

Der Spalteneffekt aus Seed 1 (+0,11 volle Spalten, Vertikale +1,6) fehlt auf Seed 2 (+0,02, Vertikale -0,25); Punkte und Margin
bleiben leicht positiv. **Gepoolt nach zwei Seeds: 427:373 = 53,4 %** (n = 800), **Block-z +2,00** (80 Bloecke, Mittel 0,534, sd 0,151).
Seeds einzeln ueber +1,96: genau einer (Seed 1), darum greift die Stufenregel aus par.3: **dritter Seed 20261602 laeuft seit
20:31** (Kette automatisch), Verdikt danach gepoolt ueber drei Seeds nach dem Kriterium Block-z >= +1,96 oder gepoolt >= 52,5 %
ohne Gegenbefund. Lesung vorab: nach zwei Seeds liegt b17 genau an der Schwelle (gepoolt +2,00, 53,4 %); der dritte Seed
entscheidet, ob der Knopf die Suche bei gleichem Netz messbar staerker macht, oder ob Seed 1 ein Ausreisser war. Zum Vergleich auf
denselben beiden Seeds: b02 (anderes Netz, gleiche Spec) 54,6 %, z +2,50.

### par.3c VERDIKT: TREE REUSE TRAEGT, KNAPP (dritter Seed 2026-10-08 20:31-23:12; Kette fertig 23:12:08, 24.480 s = 6,8 h)

**Seed 20261602 (Stufenregel): v35-b17 210:190 = 52,5 %** (n = 400, 200 Paare, Deckel), SPRT `UNDECIDED_CAP_REACHED` (LLR -1,34),
Block-z **+1,01** (40 Bloecke, Mittel 0,525, sd 0,157), gepaarte Differenz +0,10, McNemar p = 0,35, A-Sweep 52 / B-Sweep 42 / Split 106.
Laufzeit 9.656,8 s = **24,14 s je Partie**, deutlich ueber Seed 1 und 2 (18,70 / 18,33 s); Ursache UNGEKLAERT (keine bekannte
Nebenlast ausser den Warteschleifen der drei wartenden Ketten, die alle paar Sekunden die Prozessliste per PowerShell lesen;
HERLEITUNG, nicht gemessen). Die Partien selbst sind davon nicht betroffen (Determinismus unter Last: gleiche Seeds, gleiche Zuege;
nicht einzeln geprueft).

Die sechs Kennzahlen Seed 3 (Bretter je Modell, n = 400 je Seite): volle Spalten 1,032 gegen 1,042, Spalten >= 4 2,38 gegen 2,30,
H 0,595 gegen 0,594, Strafsteine 7,71 gegen 8,23, Punkte 58,05 gegen 56,61, Margin +1,45, Plattenpunkte 8,73 gegen 9,14,
Platzierung 53,98 gegen 53,06; gepaart je Kriterium nur Mehrfarbige Felder mit CI unter 0 (-0,95 [-1,85; -0,04], 76 Paare).

**Gepoolt ueber drei Seeds: 637:563 = 53,1 %** (n = 1.200 Partien, 600 Paare), **Block-z +2,22** (120 Bloecke, Mittel 0,531, sd 0,152).

| Seed | b17 : v34-b01 | Block-z | s je Partie | volle Spalten b17 / b01 | Punkte b17 / b01 |
| --- | --- | --- | --- | --- | --- |
| 20261600 | 223:177 = 55,8 % | +2,42 | 18,70 | 1,160 / 1,048 | 58,62 / 56,55 |
| 20261601 | 204:196 = 51,0 % | +0,42 | 18,33 | 1,045 / 1,025 | 57,87 / 56,80 |
| 20261602 | 210:190 = 52,5 % | +1,01 | 24,14 | 1,032 / 1,042 | 58,05 / 56,61 |
| **gepoolt** | **637:563 = 53,1 %** | **+2,22** | | | |

**VERDIKT nach dem Kriterium par.3 (Block-z >= +1,96 ODER gepoolt >= 52,5 %, ohne Gegenbefund): TREE REUSE TRAEGT.** Beide Teile des
Kriteriums sind erfuellt, kein Seed zeigt ein negatives Vorzeichen, die eigenen Punkte liegen in allen drei Seeds 1,1 bis 2,1 ueber
dem Gegner bei gleichem Netz. Die Kante ist KLEIN: 3,1 Punkte Siegquote bei n = 1.200 (95-%-Intervall rund +-2,8 Punkte), die
Zuordnung aber sauber: gleiches Netz, gleiche Spec bis auf den Knopf, der Gewinn gehoert der Suche (par.3, vorab). Zum Massstab
der Reihe: die Netzarme legten 4,6 bis 10,9 Punkte auf v34-b01 (b02 56,8, b09 59,1, b10 60,9 %), aber mit neuem Training; der
Knopf legt 3,1 Punkte ohne Training und laesst sich mit jedem dieser Netze kombinieren (b18, par.2b).

**Was der Knopf tut (ueber die drei Seeds):** der Spalteneffekt aus Seed 1 (+0,11 volle Spalten, Vertikale +1,6) wiederholt sich in
Seed 2 und 3 nicht (+0,02, -0,01); stabil ueber alle drei Seeds sind nur die eigenen Punkte (+1,1 bis +2,1) und die Margin. Die
Lesung "Absichtspersistenz haelt begonnene Spalten" aus par.3a traegt damit nicht als Mechanismus-Befund; was traegt, ist ein kleiner
Punktgewinn aus tieferer Suche bei gleichem Budget (uebernommene Besuche rund 18 bis 29 %, par.2b). Die Reuse-Fehlschlagquote
(rund ein Drittel der Suchen ohne Treffer, Smoke) bleibt der Ansatz fuer par.5.6 (welt-tolerante Variante).

**Offen / Nutzer-Entscheid:** (1) b18 = dieselbe Spec auf dem staerksten Netz der Reihe (b10, oder b16 nach par.20), Tor 1 gegen
v34-b01 mit denselben Seeds; (2) Reuse in der Erzeugung (par.5.1, Sonde Durchlaufzeit/Diversitaet) nur, wenn eine weitere Erzeugung
ansteht; (3) par.5.6 nur, wenn die Fehlschlagquote als Grenze gilt. Laufzeiten in `docs/measured_runtimes.md`.

### par.3d b18 = v35-b16 + Tree-Reuse-Spec, SCHNELLBLICK GEGEN b16 (NUTZER 2026-10-09: "starte b18 und b19 mit schnellblick gegen b16"; REGISTRIERT VOR dem Lauf)

**Arm:** `v35-b18` = Netz `alphazero_v35-b16_brierbest.onnx` (staerkstes Netz der Reihe, `PREREG_v35_window.md` par.20b) mit Spec
`models/v35-b18.spec.json` (= Champion-Spec plus `tree_reuse` 1, `tree_reuse_round5` 1; Inhalt gleich `v35-b17.spec.json`). Gegner B =
dasselbe Netz mit der Champion-Spec. Gleiches Netz, Unterschied allein der Knopf: ein Gewinn gehoert der Suche (wie par.3).

**Messung:** Schnellblick nach par.19.0 der v35-Prereg: `paired_gating.py --fixed-length`, 2 Seeds a 50 Paare @400, Seeds 20261700/20261701,
Blockgroesse 5, `--log-games`, `--resume`, Artefakte `quicklook_v35-b18_vs_v35-b16_s<seed>.json`, sechs Kennzahlen, Block-z gepoolt.
Kette `tools/quicklook_b18_chain.sh`. **Lesart vorab:** gepoolt >= 55 % oder Block-z >= +1,5 = "spannend" -> volle Breite gegen b16
(2 x 200 Paare, Nutzer-Entscheid); 45 bis 55 % ohne Block-z >= +1,5 = der Knopf legt auf b16 nichts Sichtbares (Aufloesung +-7
Punkte bei n = 200; die +3 Punkte aus par.3c liegen darunter, ein "nicht spannend" widerlegt sie also nicht); unter 45 % = Gegenbefund
auf dem starken Netz. Erwartung (HERLEITUNG): wie par.3c rund +3 Punkte, also voraussichtlich "nicht spannend" bei dieser Aufloesung;
der Schnellblick ist die vom Nutzer gewaehlte Vorsortierung. Kosten rund 1 h.

### par.3e ERGEBNIS b18 SCHNELLBLICK GEGEN b16: NICHT SPANNEND (2026-10-09 07:54-08:50, `tools/quicklook_b18_chain.sh`, exklusiv)

| Seed | b18 : b16 | Block-z (10 Bloecke) | gepaarte Diff | McNemar p | Laufzeit |
| --- | --- | --- | --- | --- | --- |
| 20261700 | 47:53 = 47,0 % | -0,67 | -0,12 | 0,664 | 1.667 s (16,7 s je Partie) |
| 20261701 | 55:45 = 55,0 % | +1,12 | +0,20 | 0,424 | 1.652 s (16,5 s je Partie) |
| **gepoolt** | **102:98 = 51,0 %** | **+0,29 (20 Bloecke, sd 0,152)** | | | 3.319 s |

Die sechs Kennzahlen (Bretter je Modell, n = 100 je Seed und Seite): volle Spalten 0,89 / 0,98 gegen 0,90 / 1,03, Spalten >= 4 2,35 / 2,39
gegen 2,36 / 2,32, H 0,584 / 0,594 gegen 0,600 / 0,593, Strafsteine 8,36 / 8,17 gegen 7,77 / 7,58, Punkte 55,38 / 58,26 gegen 55,13 / 56,87,
Margin +0,25 / +1,39, Plattenpunkte 7,15 / 9,15 gegen 6,68 / 8,23. Die Reuse-Seite hat in beiden Seeds mehr Strafsteine und mehr
Plattenpunkte; Punkte und Margin leicht positiv, Spalten leicht negativ.

**Lesart par.3d: zwischen 45 und 55 % ohne Block-z >= +1,5 = NICHT SPANNEND.** Der Knopf legt auf dem staerksten Netz der Reihe
nichts, was der Schnellblick sieht. Das ist mit par.3c vertraeglich (dort +3,1 Punkte bei n = 1.200 gegen ein schwaecheres Netz; hier
Aufloesung +-7 Punkte bei n = 200), stuetzt aber die vorab genannte Erwartung, dass die Suche bei besserem Netz weniger zu korrigieren
hat. Eine volle Breite b18 gegen b16 (4 h, Aufloesung +-3,5) wuerde die Frage "+1 bis +3 Punkte oder 0" klaeren; nach Regel nicht
faellig, Nutzer-Entscheid. Laufzeit je Partie mit Reuse auf einer Seite 16,5 bis 16,7 s, also kein messbarer Aufschlag gegen die
Schnellblicke ohne Reuse (17,2 bis 18,2 s); der Aufschlag aus par.2b/3c war Nebenlast.

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
   **ENTSCHIEDEN (Nutzer 2026-10-06 06:5x: *"Mach den runde 5 schalter mit default an"*):** eigener Schalter
   `tree_reuse_round5` (par.2), Default 1 = Runde 5 wird mitgenommen; der Ausschluss bleibt als Wert 0 erhalten.
   Begruendung (aus dem Chat): in Runde 5 hat die Suche dem Netz am meisten voraus. Beleg `PREREG_v35_window.md`
   par.12f, "Netz gegen Wurzel-Q" (Grundmenge b02-Val-Satz, 120 Dateien, 225.789 Zustaende aus @400-Partien;
   Einheit Brier-Differenz Netz minus Wurzel-Q, > 0 = Suche besser): R5 +0,0264 (Warmstart `v34-b01_brierbest`)
   und +0,0243 (`v35-b02_brierbest`), gegen R2-R4 +0,0031 bis +0,0145 (beide Netze). Folge fuer par.3: die erste
   Arena faehrt Runde 5 MIT Reuse; die Variante ohne (`tree_reuse_round5` 0) laeuft nur, wenn das Ergebnis nahe
   an der Linie liegt. Zuordnung damit: ein Gewinn gehoert dem Knopf einschliesslich Runde 5.
   Hinweis aus dem Einbau (Agent, geprueft am Entwurf): `take_reuse_start` verlangt dieselbe `round_number`, der
   erste eigene Entscheid in Runde 5 findet also keinen Treffer; Reuse greift in Runde 5 ab dem zweiten eigenen
   Entscheid. Ob Runde-5-spezifische Teile der Suche (`r5_net_sims` als Budget, Blattwert bei `r5_net_solver` 0) mit
   uebernommenem Teilbaum anders rechnen, ist UNGELESEN (HERLEITUNG: Budget = neue Sims wie R1-R4); vor der Arena pruefen.
5. Verlaufsabhaengigkeit (par.2a): mit Knopf an haengt ein Entscheid vom Verlauf ab; Einzelstellungs-Werkzeuge
   (Replays, Sonden, GUI) liefern dann nicht mehr den Arena-Zug. Fuer Sonden gilt darum Knopf aus, und die
   Determinismus-Pruefung laeuft als ganze Partie bei gleichem Seed.

6. **Fehltreffer durch falsch geratene Welt (Nutzer-Vorschlag 2026-10-06 07:2x: *"Ich wuerd nicht den gesamten ast
   loeschen wenn falsch geraten wurde. Sondern nur den weg danach nicht den weg dorthin"*).** Stand des Entwurfs
   (`net_mcts.rs`, `take_reuse_start`, `retained_world_matches`): gesucht wird ein Knoten, dessen Zustand EINSCHLIESSLICH
   der geratenen verdeckten Teile zum echten Zustand passt; gibt es keinen, faellt die Suche komplett frisch an, der
   gehaltene Baum ist weg. "Der Weg dorthin" (die Vorfahren der aktuellen Stellung) wird ohnehin nie wiederverwendet;
   verwertbar ist nur der Teilbaum UNTER der aktuellen Stellung, und der liegt zeitlich komplett nach der Aufdeckung.
   Der Vorschlag heisst darum praezise: den Teilbaum unter dem SICHTBAR passenden Knoten behalten, seine verdeckten
   Zustandsteile auf die Wirklichkeit setzen (neu determinisieren), Aeste streichen, deren Aktionen im echten Zustand
   nicht mehr legal sind (sie haengen an der falschen Annahme), und die uebrigen Statistiken als Naeherung behalten
   (welt-tolerante Wiederverwendung). Preis: Besuchszahlen und Q dieser Aeste stammen aus einer Welt, die so nicht
   eingetreten ist; wie gross der Fehler ist, haengt davon ab, wie tief die Abweichung lag (ein anderer Stapelpraefix
   weit hinten aendert fast nichts, ein anderes verdecktes Plaettchen in der Auslage viel). Vorgehen: (a) die erste
   Arena faehrt die STRENGE Variante des Entwurfs; (b) der Entwurf bekommt vorher zwei Zaehler in `TreeReuseDiag`,
   Fehltreffer "kein passender Knoten" gegen "Knoten sichtbar passend, Welt falsch", damit die Logzeile
   `[tree_reuse]` sagt, wie viel die tolerante Variante ueberhaupt holen kann; (c) dominieren die Welt-Fehltreffer,
   wird die tolerante Variante als eigener Spec-Wert (`tree_reuse` 2) gebaut und gegen Variante 1 gemessen (gleicher
   Aufbau wie par.3). Noch nicht gebaut; Nutzer-Entscheid ueber (c) nach den Zahlen aus (b).
