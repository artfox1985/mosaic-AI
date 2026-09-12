<!-- STATUS: OFFEN | Frage: Die Startkuppel ist ein 108-Wege-Entscheid und legt die Brettgeometrie fest; gelegt wird sie von einer Handheuristik, das Trainingsziel ist ein One-Hot darauf. Lohnt es, den Zug zu befreien? | Beleg: Stufe 0 GEMESSEN 2026-09-12 (par.9): die Handregel legt IMMER Slot (0,0) (Code), und genau dieser Slot ist der beste oder gleichbeste (Margin +1,5 [-4,1; +7,0] gegen Bestand, alle anderen Slots schlechter, Reihe 2 um 11-13 Punkte). Hebel SLOTWAHL geschlossen; offen bleibt nur Platte/Rotation (par.9a). hv2-Gegenprobe (Weg 3) laeuft als zweiter Waechter. Plattenwahl (par.6a) im v29-Begleitprogramm. -->

# Vorregistrierung: Wahl der Startkuppel

**Angelegt 2026-08-25**, nichts gebaut.

## par.1 Die Luecke

`start_placement_step` (self_play.rs:902ff) baut die **vollstaendige**
Aktionsmenge auf -- jede Auslage-Platte x jeder freie Slot x vier Rotationen,
bis zu 108 Eintraege -- und schreibt sie als `valid_actions` in den Record.
Gewaehlt wird dann per `choose_start_placement`: Farbhaeufigkeit in den
Fabriken plus Eckbonus. Das Policy-Ziel ist ein **one-hot auf diesen Griff**.

Folge: **auf dem geometrisch folgenreichsten Zug des Spiels klont das Netz
eine Handregel** und bewertet nie eine Alternative -- im Self-Play nicht und in
der Arena nicht. Ausdruecken koennte es den Zug: `ChooseDomeSlot` (328-354)
und `ChooseDomeRotation` (391-394) stehen im Aktionsraum.

## par.2 Der Einwand, der den naiven Zuschnitt erledigt (Nutzer 2026-08-25)

Erster Entwurf: streuen im Self-Play, dann entscheidet die Suche mit dem
Value-Kopf. Nutzer: *"der value head der am anfang nichts taugt weil alles
offen ist?"*

**Er trifft.** Der Value-Kopf ist in Runde 1 am schwaechsten (R2 rund 0,03
gegen 0,62 in Runde 5, [[project_v8d_value_head_root_cause]]), und die
Startkuppel liegt DAVOR. Eine Suche wuerde dort 108 Kandidaten nach Rauschen
ordnen. Der uebliche Ausweg -- tiefer suchen -- traegt auch nicht: die Wirkung
zeigt sich in den Runden 3-5, der Bootstrap spielt EINE Runde aus, und der
tiefere Horizont ist am Kostengate gescheitert
(`PREREG_bootstrap_horizon.md` par.9f).

## par.2a Der Ausweg: der maskierte Ownership-Kopf (Nutzer 2026-08-25)

Nutzer: *"da koennte wieder der maskierte ownership head ins rennen kommen"*.

**Das umgeht den Einwand, statt ihn zu bestreiten.** Der Value-Kopf sagt den
AUSGANG voraus -- der haengt an fuenf Runden Folgespiel und am Gegner, daher
das R2 von 0,03. Der Ownership-Kopf sagt **Feldbelegung am Endbrett** voraus,
und die ist frueh weit besser bestimmt: ein Startslot legt fest, welche
Musterreihen und Spalten ueberhaupt bedient werden. Die Groesse, die einen
Start unterscheidet, ist genau diese -- nicht die Gewinnwahrscheinlichkeit.

**Ablesung ohne neuen Kopf**, per fester Maskenrechnung auf den vorhandenen
72 Ausgaben (`PREREG_heuristic_v2_long_rows.md` par.3b Nachtrag 3a):

```
E[Abweichung_o] = SUM (1 - p(r,c)) ueber die 21 Huellen-Zellen
                + SUM  p(r,c)      ueber die 15 uebrigen
```

Die 108 Startkandidaten werden damit nach erwarteter Endform geordnet, mit je
einem Vorwaertsdurchlauf -- **keine Suche noetig**. Die Huellen-Gewichtung aus
par.3b Option (a) waere die passende Zuspitzung.

**Drei Vorbehalte, die dazugehoeren:**

1. Der Ownership-Kopf hat als STAERKE-Beitrag Gewicht 0 gemessen
   ([[project_ownership_head_closed]]). Hier ist die Nutzung eine andere --
   Rangordnung von Startkandidaten statt Shaping in der Suche -- aber die
   Grundrate mahnt.
2. Sein Ziel ist **politikabhaengig** (Endbrett der gespielten Partie). Auf
   plattenblindem Spiel sagt er, was das heutige Spiel erreicht, und wuerde
   Starts bevorzugen, die zur heutigen Schwaeche passen. Der v22-Korpus ist
   die Wiedervorlage-Bedingung.
3. Ob er auf einem **fast leeren** Brett ueberhaupt trennt, ist ungemessen.
   Das ist die erste Zahl, die par.5 erheben muss.

## par.3 Das zweite Gesicht des Einwands

Niedriges fruehes R2 hat ZWEI Lesarten mit entgegengesetzten Schluessen:

* **(a) Der Kopf kann es nicht.** Dann ist der Start wichtig und wir messen
  ihn nur nicht.
* **(b) Es ist nicht vorhersagbar.** Dann macht der Start wenig aus, und die
  Handheuristik ist gut genug.

**Diese Prereg entscheidet nichts, bevor (a) und (b) getrennt sind.**

## par.4 STUFE 0 (zuerst, netzfrei, gepaart): wie gross ist der Effekt?

**Kein Netz, kein Training, keine Suche.** Dieselbe Partie zweimal, identischer
Seed -- also identische Fabriken, Beutel, Kuppelstapel, Wertungsplatten --
einmal mit erzwungenem Startslot A, einmal B, gespielt von der Heuristik auf
beiden Seiten. Gepaart faellt alles weg, was nicht am Slot haengt.

**Erhoben** (plus die sechs Standard-Kennzahlen):

1. **Eigene Punkte und Margin je Slot** -- die tragende Groesse. NICHT die
   Siegquote: ein Effekt von 1-2 Punkten ist in Sieg/Niederlage unsichtbar.
2. Volle Spalten, volle Reihen, Strafleiste je Slot.
3. Spannweite ueber die neun Slots, mit KI je Slot.

**Vorab festgelegte Lesarten:**

* **Spanne klein** (Slots liegen innerhalb ihrer Intervalle) ⇒ Lesart (b),
  **Arm tot**, Handheuristik bleibt. Vollwertiges Ergebnis, kein Fehlschlag.
* **Spanne gross** ⇒ Lesart (a), erst dann lohnen par.2a und par.5.

**Waechter gegen die Zirkularitaet**, die an diesem Tag dreimal zugeschlagen
hat: gemessen wird mit ZWEI verschieden faehigen Spielern, `v1` und
`v2huelle`. **Kippt die Rangfolge der Slots zwischen ihnen, ist "guter Start"
keine Eigenschaft der Position, sondern der Faehigkeit** -- dann darf keine
feste Wahl eingebaut werden, egal wie gross die Spanne ist.

## par.5 NUR bei grosser Spanne: Exploration und Konsumform

Solange jede Partie gleich beginnt, kann kein Verfahren lernen, welcher Start
taugt -- es gibt keine Gegenbeispiele im Korpus.

* **Self-Play streut den Startslot** (aus dem Partie-Seed; Platte und Rotation
  vorerst weiter per Heuristik, Nutzer-Vorgabe 2026-08-25).
* **Das Policy-Ziel des Start-Records wird als UNGUELTIG markiert**
  (`policy_target_valid = false`). Ohne das trainiert man das Netz darauf, die
  Zufallswahl zu imitieren -- schlechter als der heutige Klon. Die Mechanik
  existiert (neural_net.py:1858).
* **Die Value-Labels bleiben gueltig.** Welcher Start sich ausgezahlt hat,
  steht im Ausgang.
* **Erste Zahl danach:** trennt die Ownership-Ablesung aus par.2a die 108
  Kandidaten ueberhaupt? Spannweite der erwarteten Abweichung ueber die
  Kandidaten, gegen ihre eigene Streuung. Trennt sie nicht, faellt par.2a und
  die Konsumform ist wieder offen.

## par.6 Uebergangs-Auflage fuer die Arena

Solange Self-Play streut und die Arena die Heuristik greifen laesst, wird das
Netz auf einer Verteilung gegatet, auf der es nicht trainiert wurde. **Die
Startverteilung der Arena folgt der des Self-Play** -- am billigsten
seed-abgeleitet, dann bekommen beide Arme automatisch dieselbe Startstellung
(`PREREG_search_rng_split.md`). Stratifiziert (`slot = partie_index mod 9`)
statt gezogen senkt die Varianz zusaetzlich und kostet nichts.

## par.6a DIE PLATTENWAHL IST DER GENERELLE HEBEL -- und sie sieht Spezialfelder als NULL (Nutzer 2026-08-31)

Nutzer, als Berichtigung einer Prioritaeten-Aussage des Koordinators: *"das
ist ein Randfall wenn k6 aktiv ist. das hilft nicht im generellen spiel. da
gilt es eher die Kuppelplatten richtig und aggressiv zu verteilen."*

**Die Berichtigung trifft.** Der Koordinator hatte die Spezialfelder als
groessten unabgeholten Posten bezeichnet. k6 zahlt aber nur, wenn die Platte
gezogen wurde -- im v23-Value-Korpus in **3.028 von 8.000 Partien-Seiten**,
also gut einem Drittel. Ein Hebel, der in zwei von drei Partien gar nicht
existiert, ist kein genereller Hebel. Die PLATTENVERTEILUNG dagegen wirkt in
jeder Partie: sie legt fest, welche Zellen es ueberhaupt gibt, welche Farbe
sie tragen und wo die Spezial- und Wild-Felder liegen.

**Und hier der Code-Befund, der den Punkt scharf macht (geprueft
2026-08-31):** `start_placement_kandidaten` (self_play.rs, gelesen ueber
`choose_start_placement`) bewertet jede Kandidaten-Platzierung als Summe ueber
ihre Zellen:

* `SpaceType::Normal` -> Anzahl dieser Farbe im Vorrat,
* `SpaceType::Wild` -> das Maximum ueber alle Farben,
* **`SpaceType::Special` -> 0.0.**

Die Handheuristik, die seit jeher die Brettgeometrie festlegt, bewertet
Spezialfelder also mit **null** -- ausgerechnet die Felder, an denen der
Mensch seinen gemessenen Vorsprung holt (Spezial-Punkte 4,02 gegen 3,15 je
Seite, PREREG_special_tile_yield par.7). Sie optimiert Farbnachschub, nicht
Ertragspotenzial.

**Was daraus NICHT folgt:** die Heuristik zu aendern. Der Funktionskommentar
sagt "byte-identisch zum Bestand, das ist der Elo-Anker" -- dieselbe Sperre
wie bei `scoring_progress`. Der Weg fuehrt ueber die NETZ-Seite, also genau
ueber den 108-Wege-Aktionsraum, den diese Prereg registriert: das Netz waehlt
die Platzierung, statt ein One-Hot auf die Handregel zu lernen.

**Zeitpunkt:** die Wecker-Abarbeitung (`PREREG_v23_window.md` par.4c) hat die
Startkuppel-Streuung fuer Generation 1 bewusst bei der Handheuristik
gelassen und Stufe 0 auf Generation 2 verschoben. **Generation 2 ist jetzt**
-- die v23-Tore stehen, das v24-Self-Play ist freigegeben. Damit ist die
Wiedervorlage-Bedingung erfuellt, und Stufe 0 (par.4, netzfrei und gepaart)
ist der naechste Schritt dieses Strangs.

## par.7 Wecker

Der Startslot steckt in den Partien UND in den Policy-Zielen, ist also nur am
Generierungsstart entscheidbar. Gehoert auf die Wecker-Liste des
v22-Self-Play (`PREREG_v23_window.md` par.4).

**BERICHTIGUNG 2026-08-27, zwei Punkte:**

1. **"fuer das laufende v22 zu spaet" war unpraezise.** Zu spaet ist es fuer
   den hv2-KORPUS -- der ist seit dem 2026-08-26 01:52 fertig (2.400 pkl,
   24.000 Partien) und traegt in jeder Partie das one-hot auf
   `choose_start_placement`. Fuer das v22-SELF-PLAY, also den Lauf, der das
   v23-Fenster fuellt, ist die Frage OFFEN: er hat noch nicht begonnen.
2. **Der Wecker steht jetzt tatsaechlich dort.** Bis zum 2026-08-27 war der
   Verweis eine Absichtserklaerung -- die Liste in `PREREG_v23_window.md`
   par.4 fuehrte die Startkuppel nicht. Sie ist am 2026-08-27 eingetragen
   worden.


## Nachtrag 2026-08-26: dasselbe Muster steht an DREI Stellen

Beim Nachgehen der Stapelzug-Frage (`PREREG_chance_nodes.md` par.13) gefunden:
die Startkuppel ist kein Einzelfall, sondern die dritte Auspraegung desselben
Musters -- Aktionsraum vorhanden, Entscheidung von einer blinden Handheuristik,
Trainingsziel behauptet trotzdem eine Wahl.

| Stelle | Aktionsraum | wer entscheidet | Trainingsziel |
| --- | --- | --- | --- |
| **Startkuppel** | voll in `valid_actions` (self_play.rs:922-935) | `choose_start_placement` (Farbhaeufigkeit + Eckbonus) | one-hot darauf |
| **Stapelzug** | `DrawStackPeek` als Wurzelaktion, Folgeschritte als eigene Kinder | im NETZ-Self-Play `resolve_and_apply_stack_draw` -> `best_eval_for_tile` | Policy-Ziel auf einer Fortsetzung, die nicht ausgefuehrt wird |
| **Kuppel-Rotation** | `ChooseDomeRotation` im Aktionsraum | im NETZ-Self-Play mit sammelaufgeloest | dito |

**Der Unterschied, den v22 gemacht hat:** die beiden unteren Zeilen gelten nur
noch fuer den NETZ-Pfad. Das Heuristik-Self-Play, aus dem der v22-Korpus
stammt, laeuft auf `apply_via_chosen_action = false` und loest per Entscheidung
auf -- `choose_draw_stack_slot` steht dort in 2,5 Prozent der Datensaetze und
traegt zu 100 Prozent ein gueltiges Policy-Ziel (par.13 der Chance-Nodes-
Prereg, gemessen).

**Die Startkuppel dagegen ist unveraendert**: dort steht weiterhin das one-hot,
in JEDEM Erzeugerpfad. Sie ist damit die einzige der drei Stellen, an der die
Frage dieser Prereg vollstaendig offen bleibt.

Verwandt und als Bezug zu lesen: `PREREG_chance_nodes.md` (Kontrollfluss,
Regel 3/4), `PREREG_stack_draw_reservation_rule.md` (die Stopp-Regel zieht zu
oft, ~10 Punkte je betroffenem Stapelzug), `PREREG_stack_top_feature.md`
(dieselbe blinde Zone auf der Merkmalsseite).

**NICHT zu verwechseln mit `PREREG_start_position_seeding.md`** (Hinweis aus
dem Statuskopf hierher gezogen 2026-08-28): dort geht es darum, HALBFERTIGE
Stellungen als Startpunkt einer Partie zu setzen; hier um die Wahl der
Startkuppel am regulaeren Partiebeginn. Aehnlicher Name, verschiedene Frage.

**Nachtrag 2026-09-09 (Audit):** die Sperre in par.6a ("Aendern darf man sie nicht,
Elo-Anker") ist ueberholt. Seit 2026-08-31 ist der Anker das eingefrorene Artefakt
`models/frozen_heuristics/hv1_anchor` (`ANCHOR_NAME` in `tools/elo_tracker.py`); der
lebende Heuristik-Pfad darf sich bewegen, mit der Zug-fuer-Zug-Pruefung aus CLAUDE.md
(Anker-Invarianz). Der direkte Weg, Spezialfelder in `choose_start_placement` zu
bewerten, ist damit wieder eine Option und nicht mehr aus Anker-Gruenden verworfen. Zwei
weitere Punkte aus dem Audit: die Zahl "4,02 gegen 3,15 Spezialpunkte je Seite" in par.6a
stammt aus `PREREG_special_tile_yield.md` par.7 und vergleicht hv2-Lehrer gegen v22-b06,
nicht Mensch gegen KI (Mensch gegen Netz: 10,3 gegen 1,3 je Partie,
`docs/domain_knowledge.md`); und Stufe 0 misst die Spannweite ueber die SLOTS, ihr
vorregistriertes Verdikt "Spanne klein, Arm tot" schloesse aber auch die Plattenwahl mit,
die par.5 ausdruecklich bei der Heuristik laesst. Vor Stufe 0 ist das Verdikt auf den
Slot-Teil einzugrenzen.

**Eingetaktet 2026-09-11 (Nutzer):** Stufe 0 laeuft als Sonde am v28-Korpus
(`selfplay_v27-b01-policy_*`, 4.000 Partien), sobald die Maschine zwischen zwei Laeufen frei
ist (`PREREG_v28_window.md` par.8, Schritt 5). Gemessen wird die Spannweite des Slot-Wertes
ueber die neun Slots je Startplatte; das vorregistrierte Verdikt gilt nur fuer den Slot-Teil
(Nachtrag 2026-09-09), die Plattenwahl bleibt eine eigene Frage.

## Nachtrag 2026-09-11 (Eintaktung)

Stufe 0 bleibt v28-Schritt 5; die Plattenwahl (Nachtrag 2026-09-09) folgt als zweiter Teil im
v29-Begleitprogramm (Nutzer 2026-09-11, `PREREG_v29_window.md` par.7 Punkt 4). Anlass par.6a: `choose_start_placement` bewertet
`SpaceType::Special` mit 0,0 (`engine/src/self_play.rs:922`, geprueft 2026-09-11).

## par.8 Baustand 2026-09-12 (Stufe 0 gebaut, nichts gemessen)

Gebaut von einem Agenten, vom Koordinator gelesen (Regel 0: Codepruefung durch Lesen, kein
Kompilat, kein Lauf). Alles unten ist Baustand, nicht Messung.

**Knopf.** `MOSAIC_START_SLOT_P0` / `MOSAIC_START_SLOT_P1` (Diagnose, kein Spec-Feld,
`engine/src/knob_registry.rs:155-156`): erzwingt den SLOT der Startkuppel des jeweiligen Spielers,
Index 0..8 = `row*3+col` (Zaehlweise `board.rs::empty_slots`, r aussen, c innen). Platte und
Rotation waehlt weiter die Handregel, eingeschraenkt auf die Kandidaten dieses Slots
(`self_play.rs::choose_start_placement_with_slot`, Zeilen 1268-1296). Ungesetzt oder leer =
Bestand, bitidentisch (dieselbe Schleife, strikt groesser, feste Reihenfolge); ungueltiger Wert =
einmalige Warnung und Bestand; belegter Slot = Rueckfall auf Bestand. Die Variable wird JE
STARTSETZUNG gelesen (kein `OnceLock`), damit die Sonde die neun Slots in einem Prozess faehrt.

**Wirkungsbereich (geprueft per Grep 2026-09-12):** `choose_start_placement` wird aus Self-Play,
Arena, Referee (`referee.rs:122/508`), Round-Transition (`round_transition.rs:656`), `py.rs:644`
und den Serialize-/Game-Tests aufgerufen. Der Knopf greift also in JEDEM Pfad, sobald die
Variable gesetzt ist; deshalb setzt ihn ausschliesslich die Sonde selbst, in-Prozess, zwischen
zwei Arena-Aufrufen, und entfernt `..._P1` aktiv. In Gating, Anker-Kanten und Erzeugung ist er
nie gesetzt.

**Sonde** `tools/probes/start_dome_slot_probe.py` (448 Zeilen): Einstieg `mosaic_rust.arena_match`
(Heuristik-MCTS beide Seiten, netzfrei, keine Records), dafuer neuer Parameter `log_games`
(Default `false`, `lib.rs:174`, `self_play.rs::run_arena_match`), weil volle Spalten und Reihen
nur aus dem Log rekonstruierbar sind. Partie `i` bekommt `seed_base + i*0x9E3779B97F4A7C15`
unabhaengig vom Slot, Startspieler alterniert mit `i % 2`: dieselbe Partie in allen neun Armen,
gepaart gegen Slot 0 mit 95-%-KI. Erhoben je Slot (Sicht Spieler 0, Einheit je Partie, Grundmenge
Partien des Slots): Punkte, Margin, Gegnerpunkte, Strafpunkte, volle Spalten und Reihen,
Spalten-/Reihenprofil, Teilspalten >= 3/4, Plattenpunkte je Kriterium; die sechs
Standard-Kennzahlen sind damit abgedeckt. Defaults: `--n-seeds 60`, `--pairings 25,400`,
Seed-Basis 20260912. JSON mit n/Grundmenge/Einheit, `laufzeit`-Block, `cli_args`.

**ABWEICHUNG von par.4 (Nutzer-Entscheid offen):** der Zirkularitaets-Waechter verlangt zwei
verschieden faehige Spieler `v1`/`v2huelle`. PRAEZISIERT 2026-09-12 (Nutzer-Rueckfrage): hv2 IST
spielbar, als eingefrorenes Artefakt `models/frozen_heuristics/hv2_generator/` im Referee-Pfad
(eigenes Wheel, Protokoll drafting/tiling/start_placement). Nicht spielbar ist hv2 nur auf dem
LEBENDEN Wheel (`SearchConfig::from_spec_file` weist alles ausser hv1 ab, Zweig am 2026-08-26
entfernt). Das Hindernis fuer die Sonde ist enger: im Referee-Pfad berechnet die Startsetzung
der Artefakt-Seite deren WORKER mit dem Artefakt-Wheel (`tools/frozen_referee_match.py:344-349`,
`frozen_champion_worker.py:192-194`), und dieses Wheel kennt `MOSAIC_START_SLOT_P0` nicht; der
Slot laesst sich hv2 also nicht ueber den Knopf aufzwingen. Ausweg (nicht gebaut): der Referee
erzwingt die Startsetzung der Seite A selbst auf dem lebenden Wheel (`--force-start-slot-a`,
Platte/Rotation dann nach hv1-Handregel, ein benannter Konfund) und hv2 spielt den Rest; Kosten
Referee-Partien 9-17 s je Partie. Ersatz in der gebauten Sonde: zwei Faehigkeitsstufen derselben Variante ueber die Suchtiefe (25 gegen 400
Sims, der gemessene Prior/Value-Regler), Spearman-Rangkorrelation der Slot-Margins zwischen den
Stufen, Flag `kippt` bei rho < 0. Im Artefakt als `waechter.abweichung_von_prereg` vermerkt. **Nutzer-Entscheid 2026-09-12 ("Nimm Weg 3"):** die Sims-Stufen bleiben die Hauptmessung, dazu
kommt die hv2-Gegenprobe ueber den Referee mit kleinerem n (20 Partien je Slot): Schalter
`--force-start-slot-artifact` in `tools/frozen_referee_match.py` (Startsetzung der Artefakt-Seite
auf dem lebenden Wheel mit gesetztem Knopf, nur fuer diese eine Anfrage) und Treiber
`tools/probes/start_dome_slot_referee_probe.py` (Spearman der Slot-Margins hv2 gegen hv1@400).
GEBAUT 2026-09-12, 10:10 (Agent, vom Koordinator gegengelesen; nichts gelaufen):
`tools/frozen_referee_match.py` mit `--force-start-slot-artifact N` (Startsetzung der Artefakt-
Seite ueber `mosaic_rust.start_placement_choice_state_json` auf dem lebenden Wheel, Knopf nur um
diesen Aufruf gesetzt und danach entfernt; Partie-Record traegt `start_slot_artifact` aus der
START_TILE-Zeile und `start_slot_forced`) und `--heuristic-a` (Seite A netzlos hv1 ueber
`heuristic_arena_choice_state_json`; `--model-a` ohne Modell spielt KEINE Heuristik,
`referee.rs:689-710` laedt ein Netz). Treiber `tools/probes/start_dome_slot_referee_probe.py`:
hv2_generator@150 gegen lebende hv1@150, 20 Partien je Slot, Seed-Basis 20260913, 6 Worker,
`--force-cross-era` (Kontrakt a3f61f246d9bbf5c gegen 39648b95bbba1acf), c_puct 0,3 wie in der
Heuristik-Arena; Waechter = Spearman der Slot-Margins gegen die Paarung hv1@400 der
Hauptmessung. **Benannter Konfund:** `choose_start_placement_json` ignoriert Spec und Seed
(`referee.rs:121`) und nutzt die hv1-Handregel; gemessen wird "hv2 spielt eine Partie, die in
Slot N beginnt", nicht "hv2 waehlt Slot N". Ungeprueft bis zum Rauchtest: Prozess-Isolation von
`os.environ` je Worker (aus `mp.Pool`/`_play_block` hergeleitet), Sichtbarkeit der Python-
Umgebungsvariable fuer das Rust-`env::var` (in der Hauptsonde gleich gebaut, Slot-Kontrolle
dort noch nicht gelaufen). Lauf nach der Fortsetzungskette, exklusiv.

**Ungeprueft / offen:** nichts kompiliert (Wheel-Durchgang fuer alle neuen Knoepfe folgt nach der
Neuverankerungs-Kette, PREREG_v28_window.md par.8); die Log-Muster der Heuristik-Arena fuer
`reconstruct_game` sind hergeleitet (gleicher Erzeuger `state.log` wie in den Netz-Arenen), nicht
in dieser Sitzung gemessen; fuenf neue Tests im Modul `start_slot_tests` (`self_play.rs:9763ff`)
sind geschrieben, nicht gelaufen. Rauchtest vorgesehen: `--limit 4 --pairings 25 --threads 4`.

**Kompiliert und im Wheel (Nachtrag 03:50):** Bau-Tor 2026-09-12, 03:44-03:48 (`tools/night_v28_knob_build.sh`, Artefakte `anchor_drift_live_wheel_20260912_knobs.json` / `anchor_conservation_artifact_wheel_20260912_knobs.json`): `cargo test --release --lib` 601 gruen (84 s; darunter Kontrakt-Hash-Literal 39648b95bbba1acf und die Netz-Paritaets-Fixture des Champions UNVERAENDERT), Beispiele/Benches kompilieren, Wheel gebaut und installiert (Kontrakt 39648b95bbba1acf, INPUT_SIZE 755), Anker-Drift gegen hv1_anchor_v2 GRUEN und Konservierung GRUEN, Konventions-Check gruen. Zwei Nachbesserungen beim Bau: `#![recursion_limit = "256"]` in lib.rs (das `json!`-Literal von `engine_config_json` riss das Makro-Limit) und die Lesestelle der Startslot-Knoepfe als zwei Literal-Aufrufe (Registratur-Scanner). Alle neuen Knoepfe stehen damit auf Default im Wheel, das die Promotion v28-b02 einfriert. Rauchtest der Sonde (`--limit 4 --pairings 25 --threads 4`, Artefakt `start_dome_slot_probe_smoke.json`): 36 Partien in 18,7 s (0,52 s je Partie @25 Sims, 4 Threads), 0 Partien ohne rekonstruierbares Log, Punkte und Margin variieren je Slot bei gleichen Seeds (n=4, keine Aussage). Der Waechter braucht zwei Paarungen und war im Rauchtest nicht erhoben. Nachgeruestet 03:55, NOCH NICHT gelaufen: `slot_kontrolle` je Slot (gelegter Slot aus der START_TILE-Logzeile gegen den erzwungenen; Abweichungen = Rueckfall auf den Bestand bei belegtem Slot). Volle Messung (60 Partien je Slot, Paarungen 25 und 400 Sims) nach der Master-Kette, exklusiv.

## par.9 ERGEBNIS STUFE 0 (2026-09-12, 11:43-11:51, `tools/night_v28_third_seed.sh` Teil 2)

`tools/probes/start_dome_slot_probe.py`, Defaults: netzfrei, Heuristik-MCTS hv1 auf beiden
Seiten, `mosaic_rust.arena_match(log_games=True)`, Seed-Basis 20260912, 60 Partien je Slot und
Paarung, Partie i in allen neun Slots derselbe Seed (gepaart), Startspieler alterniert; Spieler 0
mit erzwungenem Slot (`MOSAIC_START_SLOT_P0`), Spieler 1 Bestand. Grundmenge je Zeile: 60 Partien
des Slots, Sicht Spieler 0, Einheit je Partie. 1.080 Partien in 429,7 s (threads 0 = alle
Kerne, 0,40 s je Partie). Slot-Kontrolle: in JEDEM Slot 60/60 Partien im erzwungenen Slot, der
Knopf greift (Umgebungsvariable aus Python fuer das Rust-`env::var` sichtbar, damit belegt).
Artefakt `start_dome_slot_probe.json`.

**Paarung hv1@400 gegen hv1@400 (Hauptmessung):**

| Slot (r,c) | Punkte | Margin | KI95 Margin | volle Spalten | Strafpunkte | Slot-Kontrolle |
| --- | --- | --- | --- | --- | --- | --- |
| 0 (0,0) | 48.5 | +1.5 | [-4.1; +7.0] | 0.133 | 10.35 | 60/60 |
| 1 (0,1) | 47.7 | -0.1 | [-6.1; +5.8] | 0.133 | 12.67 | 60/60 |
| 2 (0,2) | 43.2 | -3.4 | [-7.9; +1.2] | 0.150 | 12.92 | 60/60 |
| 3 (1,0) | 41.7 | -3.8 | [-8.9; +1.3] | 0.183 | 10.47 | 60/60 |
| 4 (1,1) | 43.8 | -3.0 | [-7.7; +1.6] | 0.117 | 9.98 | 60/60 |
| 5 (1,2) | 41.2 | -7.0 | [-11.6; -2.4] | 0.150 | 10.85 | 60/60 |
| 6 (2,0) | 33.6 | -11.4 | [-15.9; -6.9] | 0.133 | 13.42 | 60/60 |
| 7 (2,1) | 33.8 | -12.4 | [-16.9; -7.8] | 0.083 | 14.12 | 60/60 |
| 8 (2,2) | 34.0 | -11.4 | [-16.6; -6.2] | 0.083 | 14.05 | 60/60 |

Spannweite: Punkte 14.9 (bester Slot 0, schlechtester 6),
Margin 13.9; Rangfolge nach Margin [0, 1, 4, 2, 3, 5, 6, 8, 7].
Gepaart gegen Slot 0: Slots 6/7/8 (Reihe 2) -12,9 / -13,9 / -12,9 Punkte Margin, Slot 5 -8,5,
Slots 2/3/4 (Reihe 1) -4,5 bis -5,3, Slot 1 -1,6.

**Paarung hv1@25 gegen hv1@25 (Faehigkeitsstufe des Waechters):**

| Slot (r,c) | Punkte | Margin | KI95 Margin | volle Spalten | Strafpunkte | Slot-Kontrolle |
| --- | --- | --- | --- | --- | --- | --- |
| 0 (0,0) | 41.8 | +1.9 | [-2.1; +5.8] | 0.067 | 14.23 | 60/60 |
| 1 (0,1) | 43.2 | +4.9 | [+0.1; +9.7] | 0.050 | 12.20 | 60/60 |
| 2 (0,2) | 40.7 | -0.8 | [-5.6; +3.9] | 0.050 | 12.38 | 60/60 |
| 3 (1,0) | 39.0 | -3.3 | [-8.9; +2.2] | 0.050 | 13.05 | 60/60 |
| 4 (1,1) | 39.5 | -1.0 | [-5.5; +3.6] | 0.083 | 14.40 | 60/60 |
| 5 (1,2) | 36.3 | -2.5 | [-7.8; +2.8] | 0.100 | 15.22 | 60/60 |
| 6 (2,0) | 34.8 | -3.1 | [-7.5; +1.3] | 0.183 | 16.75 | 60/60 |
| 7 (2,1) | 35.8 | -3.5 | [-8.4; +1.4] | 0.150 | 16.23 | 60/60 |
| 8 (2,2) | 36.8 | -2.5 | [-7.0; +2.0] | 0.100 | 16.12 | 60/60 |

Spannweite Punkte 8.4, Margin 8.3; Rangfolge [1, 0, 2, 4, 5, 8, 6, 3, 7].

**Waechter (Sims-Stufen, Ersatz nach par.8):** Spearman der Slot-Margins 25 gegen 400 Sims =
**0,85**, `kippt = False`; bester Slot 1 (@25) bzw. 0 (@400), beide Reihe 0, die drei Slots der
Reihe 2 in beiden Stufen am Ende. Die Rangfolge ist eine Eigenschaft der Position, nicht der
Faehigkeit; die hv2-Gegenprobe ueber den Referee (Weg 3) folgt als zweiter Waechter.

**Lesart nach par.4, KORRIGIERT 12:40 (Nutzer: "die handregel heute legt immer auf slot 0,0"):**
geprueft am Code `engine/src/self_play.rs:1180-1200` (`start_placement_kandidaten`): die Bewertung
eines Kandidaten haengt nur an Platte und Rotation (Farbzaehler der Sonnenfelder plus Eckbonus 0,5
fuer ALLE vier Ecken), die Kandidaten laufen in fester Reihenfolge (Platte, Slot, Rotation), und
`choose_start_placement_with_slot` nimmt strikt "groesser". Slot (0,0) ist die erste Ecke und
gewinnt damit jeden Gleichstand: **die Handregel legt die Startkuppel IMMER auf (0,0)**, gewaehlt
werden nur Platte und Rotation. Folge fuer die Zahlen oben: "Slot 0 erzwungen" IST der Bestand
(Kontrolle: Margin +1,5 [-4,1; +7,0] gegen den unerzwungenen Gegner, mit 0 vertraeglich, wie es
fuer zwei identische Spieler sein muss), und jeder andere Slot ist schlechter oder gleich (Slot 1
-1,6, Reihe 1 -4,5 bis -5,3, Reihe 2 -12,9 bis -13,9 gepaart; @25 Sims Slot 1 nominell vorn, +3,0
gegen Slot 0, Intervall schliesst 0 ein). Die Spanne ist gross, aber sie misst die KOSTEN des
Abweichens vom Bestand, nicht einen offenen Gewinn. **Der Hebel "Slotwahl befreien" ist damit
GESCHLOSSEN: par.2a und par.5 haben fuer den Slot keinen Gegenstand mehr.** Was offen bleibt,
steht in par.9a.

## par.9a Was nach Stufe 0 noch offen ist

1. **Platte und Rotation** (die 12 Kandidaten je Partie im Slot (0,0)): die Handregel waehlt nach
   Farbzaehlern der Sonnenfelder; ob das gut ist, ist ungemessen. Billige Sonde (Muster Stufe 0,
   netzfrei, gepaart): Handregel gegen "zufaellige Platte/Rotation in (0,0)" und gegen "beste
   Platte/Rotation nach Ownership-Ablesung par.2a" (letzteres braucht ein Netz). Erste Zahl:
   Margin der Handregel gegen Zufall; ist sie klein, ist auch dieser Teil des Zugs kein Hebel.
2. **hv2-Gegenprobe** (Weg 3, laeuft): kippt die Slot-Rangfolge bei hv2, waere der Bestandsslot
   fuer einen anderen Spieler nicht der beste; nur dann lebt die Slotfrage wieder.
3. **Plattenwahl par.6a** (Spezialfelder als 0,0 bewertet): eigener Posten, v29-Begleitprogramm.

Randbedingungen: netzfrei (das Netz benutzt dieselbe Handregel `choose_start_placement`, der
Befund gilt fuer seine Startsetzung ebenso, aber die Kosten eines Slots koennen unter Netz-Suche
anders liegen, ungemessen); Sicht Spieler 0 auf Brett 0, Spieler 1 immer Bestand; Zeilen-/
Spaltenindex des 3x3-Rasters wie `board.rs::empty_slots` (r aussen, c innen).

## par.9b NUTZER-ZIEL 2026-09-12: Sichtbarkeit statt Optimierung (Streuung im Self-Play)

Nutzer, 12:45: *"slot 0,0 ist ein konservativ richtiger slot wenn man sich die wertungsplatten
ansieht. es waer nur wichtig dass das netz sieht das auch anders gelegt werden kann und welche
auswirkungen es hat. nicht dass sich das netz dann wundert dass ein spieler mal die startplatte
irgendwo hinlegt."* Das ist par.5 mit anderem Zweck: nicht lernen, welcher Slot besser ist
(Stufe 0: keiner), sondern den Zustandsraum abdecken, den ein Gegner (Mensch, andere Regel)
erzeugen kann, damit Value- und Policy-Kopf dort nicht ins Leere greifen.

**Vorschlag (nicht gebaut, Nutzer-Entscheid zur Dosis offen):**

- Engine-Knopf `MOSAIC_START_SLOT_RANDOM_P` (Default 0 = Bestand bitidentisch): je Partie und je
  Spieler unabhaengig wird mit Wahrscheinlichkeit p der Startslot gleichverteilt aus den neun
  Slots gezogen (aus dem Partie-RNG, reproduzierbar), Platte und Rotation weiter per Handregel
  im gezogenen Slot (`choose_start_placement_with_slot`, existiert). Beide Spieler, weil das
  Netz beide Seiten sehen soll: die eigene Abweichung (Folgen im Value) und die des Gegners
  (Antwort in der Policy).
- **Der Start-Record einer gestreuten Setzung bekommt `policy_target_valid = false`** (Feld
  existiert, `self_play.rs:2376`): sonst lernt der Policy-Kopf, die Zufallswahl zu imitieren.
  Value-Labels bleiben gueltig, genau das ist der Zweck.
- Dosis: Vorschlag **p = 0,15 je Spieler** (rund 28 % der Partien mit mindestens einer
  Abweichung, 2 % mit beiden); Begruendung: Reihe 2 kostet 11-13 Punkte, eine hoehere Dosis
  verschiebt das Punkteniveau des Korpus spuerbar (ungeprueft; Kontrolle per Tor 2a und
  Punkteniveau der Erzeugung gegen v28). Nutzer kann anders entscheiden.
- Arena und Gating: UNVERAENDERT (Bestand beidseits). par.6 verlangte gleiche Verteilung in der
  Arena nur fuer den Fall, dass die Slotwahl gelernt werden soll; hier soll sie es nicht.
- Erzeugung v29 (`PREREG_v29_window.md` par.6): Knopf im Rezept, Spec-Feld nicht noetig (reiner
  Erzeugungsknopf), Manifest-Diff gegen v28 zeigt ihn. Bau vor dem Generationswechsel, Tore:
  Tests, Fixture unveraendert (Default 0), Anker-Drift gruen; Kosten rund 1 h Bau.
- Messbar danach: Value-Fehler des v29-Netzes auf Zustaenden mit abweichendem Startslot gegen
  das v28-Netz (Sonde auf Stufe-0-Partien, gleiche Seeds), und ob der Gegner-Abweichung eine
  andere Antwort folgt (Policy-Entropie am Zug nach der Gegner-Startsetzung).

