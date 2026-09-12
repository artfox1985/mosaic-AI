<!-- STATUS: ENTSCHIEDEN | Frage: Die Startkuppel ist ein 108-Wege-Entscheid und legt die Brettgeometrie fest; gelegt wird sie von einer Handheuristik, das Trainingsziel ist ein One-Hot darauf. Lohnt es, den Zug zu befreien? | Beleg: ABGESCHLOSSEN 2026-09-13 (par.10). Handregel legt immer (0,0), fuer Heuristiken der beste Slot (par.9). Such-Start gebaut, zweimal gemessen (par.9e): 91:99 und 81:89, Punkte und Spalten gleich, andere Praeferenz; Platte/Rotation kein Hebel (par.9f). Streuung 0,15 und Such-Start ins v29-Rezept (v29_window par.6b); Plattenwahl (par.6a) im v29-Begleitprogramm. -->

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

**Kompiliert und im Wheel (Nachtrag 03:50):** Bau-Tor 2026-09-12, 03:44-03:48 (`tools/night_v28_knob_build.sh`, Artefakte `anchor_drift_live_wheel_20260912_knobs.json` / `anchor_conservation_artifact_wheel_20260912_knobs.json`): `cargo test --release --lib` 601 gruen (84 s; darunter Kontrakt-Hash-Literal 39648b95bbba1acf und die Netz-Paritaets-Fixture des Champions UNVERAENDERT), Beispiele/Benches kompilieren, Wheel gebaut und installiert (Kontrakt 39648b95bbba1acf, INPUT_SIZE 755), Anker-Drift gegen hv4_anchor GRUEN und Konservierung GRUEN, Konventions-Check gruen. Zwei Nachbesserungen beim Bau: `#![recursion_limit = "256"]` in lib.rs (das `json!`-Literal von `engine_config_json` riss das Makro-Limit) und die Lesestelle der Startslot-Knoepfe als zwei Literal-Aufrufe (Registratur-Scanner). Alle neuen Knoepfe stehen damit auf Default im Wheel, das die Promotion v28-b02 einfriert. Rauchtest der Sonde (`--limit 4 --pairings 25 --threads 4`, Artefakt `start_dome_slot_probe_smoke.json`): 36 Partien in 18,7 s (0,52 s je Partie @25 Sims, 4 Threads), 0 Partien ohne rekonstruierbares Log, Punkte und Margin variieren je Slot bei gleichen Seeds (n=4, keine Aussage). Der Waechter braucht zwei Paarungen und war im Rauchtest nicht erhoben. Nachgeruestet 03:55, NOCH NICHT gelaufen: `slot_kontrolle` je Slot (gelegter Slot aus der START_TILE-Logzeile gegen den erzwungenen; Abweichungen = Rueckfall auf den Bestand bei belegtem Slot). Volle Messung (60 Partien je Slot, Paarungen 25 und 400 Sims) nach der Master-Kette, exklusiv.

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

**hv2-GEGENPROBE (Weg 3, 2026-09-12, 14:55-15:01, `tools/night_start_dome_hv2.sh`; Rauchtest
18 Partien mit Slot-Kontrolle 18/18, dann voller Lauf):** hv2_generator@150 (Artefakt, eigenes
Wheel, Worker) mit erzwungenem Startslot ueber den Referee (Setzung auf dem lebenden Wheel nach
hv1-Handregel im erzwungenen Slot, benannter Konfund par.8) gegen lebende hv1@150 (Bestand), 20
Partien je Slot, Seed-Basis 20260913, gepaart ueber den Seed, 6 Referee-Prozesse, 180 Partien in
219 s. Slot-Kontrolle 20/20 in jedem Slot. Sicht hv2, Einheit je Partie:

| Slot | Punkte | Margin | KI95 | gepaart gegen Slot 0 |
| --- | --- | --- | --- | --- |
| 0 (0,0) | 48,2 | +8,9 | [+0,3; +17,5] | Bezug |
| 1 (0,1) | 44,0 | -0,5 | [-12,5; +11,5] | -9,4 |
| 2 (0,2) | 43,6 | -0,7 | [-11,3; +10,0] | -9,6 |
| 3 (1,0) | 42,6 | +3,2 | [-6,1; +12,4] | -5,8 |
| 4 (1,1) | 32,4 | -9,2 | [-18,7; +0,3] | -18,1 |
| 5 (1,2) | 37,0 | -4,3 | [-11,3; +2,8] | -13,2 |
| 6 (2,0) | 41,8 | -3,1 | [-12,7; +6,5] | -12,0 |
| 7 (2,1) | 34,1 | -7,3 | [-15,1; +0,5] | -16,2 |
| 8 (2,2) | 38,2 | -3,0 | [-12,2; +6,2] | -11,9 |

**Waechter erfuellt:** Spearman der Slot-Margins hv2@150 gegen hv1@400 = **0,52**, `kippt = False`;
bester Slot bei beiden Spielern (0,0), alle acht anderen Slots gepaart negativ (-5,8 bis -18,1).
"Guter Start" ist damit eine Eigenschaft der Position, bei zwei verschieden faehigen Spielern
(hv1@25/hv1@400/hv2@150) dieselbe. Mit n=20 je Slot sind die Einzelintervalle breit; die
Aussage traegt die Richtung, nicht die Feinordnung innerhalb der Reihen. Artefakt
`start_dome_slot_referee_probe.json`, Einzellaeufe `start_dome_slot_referee_runs/`.

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

**Nutzer 12:50: "fuers self play sollten wir die position sicherlich variieren. nicht unbedingt in
jedem spiel. aber zumindest so oft dass das netz einen unterschied sieht." Dosis innerhalb dieses
Rahmens als Koordinator-Wahl: p = 0,15 je Spieler. Bau beauftragt 12:55 (Agent, nur Code), Tore
in `tools/night_startslot_build.sh` in der Luecke zwischen den Ketten.**

**Entwurf (Stand 12:45):**

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

## par.9c NUTZER-ENTSCHEID 2026-09-12, 13:00: im Spiel entscheidet die Suche, nicht die Handregel

Nutzer: *"im arena spiel wuerd ich die entscheidung der einhuellenden bzw. der suche ueberlassen.
aehnlich wie die kuppelplatten bereits heute selektiert und gelegt werden."*

**Stand heute (geprueft):** der Start-Record kodiert die Setzung als gewoehnliche Kuppel-Aktion
(`start_placement_step`, `self_play.rs:1330-1340`: `type: dome, is_start: true`, alle Display x
freie Slots x 4 Rotationen, bis zu 108 Eintraege). **BERICHTIGT 2026-09-12 (par.9d):** der
Zusatz "im 406er-Aktionsraum, der Policy-Kopf kennt die Startsetzung also" war FALSCH. Der
Schluessel `"type": "dome"` trifft in `features.rs::action_to_id` keinen Zweig und faellt auf
den Fallback `405` -- alle bis zu 108 Kandidaten liegen auf EINER ID (der von
`dome_stack_peek`). Der Kopf kann die Startsetzung heute weder als Prior trennen noch als Ziel
lernen; dass es nicht auffiel, liegt daran, dass `corpus_dataset.py` Start-Records ohnehin
Policy-Gewicht 0 gibt. Die
Suche selbst sah die Phase nie (Stand VOR par.9d, 2026-09-12): `net_mcts.rs` enthielt keine
Behandlung von `StartPlacement`,
in allen Spielpfaden (Self-Play `self_play.rs:2912`, Arena, Referee `referee.rs:508`,
`round_transition.rs:656`, `py.rs:644`) wird die Setzung VOR der ersten Suche per
`choose_start_placement` aufgeloest.

**Ziel:** die Startsetzung wird ein Suchentscheid wie jede Kuppelplatzierung: Wurzel = Zustand in
der StartPlacement-Phase des Spielers, Kinder = die legalen Start-Aktionen, Prior aus dem
Policy-Kopf (heute Handregel-Klon, mit par.9b-Streuung teilweise ungueltig markiert), Blatt =
Netzwert plus Einhuellenden-Verschiebung (K3-P, Huellenform 2) wie ueberall sonst; damit sieht die
Wahl die Wertungsplatten und die Huelle, nicht nur Farbzaehler und Eckbonus.

**Bauumfang (ANNAHME, ungeprueft):** (1) `net_mcts`: Expansion und Anwendung von Start-Aktionen
in der StartPlacement-Phase, Uebergang in die Drafting-Phase im Baum; (2) Spielpfade: statt
`choose_start_placement` die Suche rufen, wenn ein Netz spielt (Heuristik-Spieler behalten die
Handregel, sonst bewegt sich der Anker); (3) Self-Play: dieselbe Wahl in der Erzeugung
(Traegerprinzip: was die Arena spielt, erzeugt das Self-Play), Streuung par.9b obendrauf;
(4) Referee-Protokoll: der Worker entscheidet die Startsetzung schon extern
(`ask_start_placement`), muss dann die Suche statt der Handregel rufen; Golden-Proben der
NETZ-Artefakte enthalten 2 von 10 Sonden mit `pending_dome_choice` und sind neu zu erzeugen,
falls sich die Startsetzung der Artefakte aendert (sie aendert sich NICHT: die Artefakte
tragen ihre eigenen Wheels). Kosten grob ein Tag Bau plus A/B (200 Paare, Champion mit
Such-Start gegen Champion mit Handregel; Erwartung nach Stufe 0 klein, da (0,0) schon der beste
Slot ist; Platte/Rotation sind der Rest, par.9a Punkt 1). Knopf-Form: `MOSAIC_START_BY_SEARCH`
(Default 0 = Handregel, bitidentisch), Spec-Feld fuer die Artefakt-Identitaet.

**Reihenfolge:** par.9b (Streuung, in Bau) und par.9c BEIDE vor der v29-Erzeugung, damit der
Generator sie traegt; A/B des Such-Starts am Champion hinter der Leiter-Kette. Nutzer 13:05 zur
Erwartung: *"kann gut sein dass die suche/netz dann selbststaendig entscheidet, dass die position
0,0 die stabilste ist. aber zumindest hat es staerkeren hebel einzugreifen."* Das ist auch die
Messfrage des A/B: nicht "mehr Elo", sondern (a) wie oft weicht die Suche von (0,0) ab und in
welchen Auslagen, (b) kostet die Abweichung Punkte oder bringt sie welche (gepaart, gleiche
Seeds), (c) Siege als Waechter. Zeitpunkt ENTSCHIEDEN (Nutzer 13:15: "bau den such-start dann vor v29"); der
Generationswechsel verschiebt sich um rund einen Tag. Nutzer 13:10 zur Erwartung: die Suche darf
auch (0,2) waehlen, das Spaltenspiegelbild von (0,0); Stufe 0 zeigt Reihe 0 als gleichauf.

## par.9d BAUSTAND des Such-Starts 2026-09-12 (Agent; NICHTS kompiliert, nichts gemessen)

Alles hier ist Baustand aus Quelltext-Lektuere, kein Kompilat und kein Lauf -- die Messkette
lief waehrend des Baus, `cargo`/`maturin` waren gesperrt. Der Wheel-Durchgang (Tests, Anker-
Invarianz, Netz-Paritaets-Fixture) steht aus.

**Knopf.** `MOSAIC_START_BY_SEARCH` (0 Handregel = Bestand, 1 Suche), Getter
`net_mcts.rs::read_start_by_search_env` (kein OnceLock, Spec-Feld je Seite). Dazu das
OPTIONALE Spec-Feld `start_by_search` in `SearchConfig` -- Muster `return_order_mode`:
eingefrorene Specs ohne das Feld laden weiter und beschreiben bitgenau das Verhalten, das sie
schon immer beschrieben haben. Registratur `knob_registry.rs`, `docs/knobs.md` neu erzeugt.
`SPEC_TO_ENV` in `server.py` und `tools/claude_play.py` nachgezogen.

**Suche** `net_mcts.rs::search_start_placement(net, state, pi, base_sims, add_root_noise, rng,
cfg) -> Option<StartPlacementSearch>`: Wurzel von Hand (der Wurzelzustand ist keine
Drafting-Stellung), Kinder = alle Kandidaten aus `start_placement_kandidaten` (bis zu 108),
Prior aus EINEM Vorwaertspass, Auslese per Gumbel-Top-m und Sequential Halving wie an jeder
anderen Wurzel, Blatt = `make_node` (Netzwert plus Einhuellenden-Verschiebung, K3/K4/Floor).
Unterhalb der Setzung laeuft die gewoehnliche Drafting-Suche weiter; dafuer ist
`descend_and_backprop` aus `build_gumbel_tree_inner` auf Modulebene gehoben worden (reiner
Ortswechsel). Rueckgabe traegt die Besuchsverteilung ueber ALLE Kandidaten plus den
gewaehlten Index.

**Kosten (hergeleitet, nicht gemessen):** ein Vorwaertspass fuer die Priors plus `sims`
Simulationen, also rund EIN Drafting-Zug je Partie und Seite. Expandiert werden nur
`gumbel_top_m_for_budget(sims)` = 4..16 der 108 Kandidaten, nicht alle.

**Umgeschaltet (nur wo ein NETZ zieht):** `unified_game_loop` (Netz-Self-Play, Netz-gegen-
Heuristik-Arena, Netz-gegen-Netz-Arena -- je Seite ueber `PlayerLoopConfig::start_search`),
`play_net_vs_net_hybrid_game`, `referee.rs::advance_to_decision` (in-process, neue optionale
Parameter `spec_p0`/`spec_p1`/`start_sims`), `referee.rs::choose_start_placement_json` (Worker
und `lib.rs::start_placement_choice_state_json`, neue optionale Parameter), `py.rs::
ai_start_tile_json` (GUI). NICHT umgeschaltet und benannt: Heuristik-Seiten (hv1/hv2, der
Anker -- `StartSearchParams::for_net` gibt ohne Netz IMMER `None`), der Heuristik-Self-Play,
`round_transition.rs` (Rundenuebergangs-Simulation) und die netzfreien Diagnose-Schleifen.

**Record-Vertrag (par.9c, nur bei Knopf 1):** `start_by_search: true`,
`policy_target_valid: true`, Policy-Ziel = Besuchsverteilung statt One-Hot. Vorrang bleibt bei
`MOSAIC_START_SLOT_P0/P1` und `MOSAIC_START_SLOT_RANDOM_P`: zieht die Streuung, bleibt es bei
Handregel-im-Slot und `policy_target_valid: false`.

**BEFUND, der die Aktionsform des Records geaendert hat (geprueft an `features.rs::
action_to_id` und dem Python-Spiegel `neural_net.py::action_to_id`):** der bisherige
Record-Schluessel `"type": "dome"` trifft dort KEINEN Zweig und faellt auf den Fallback `405`
-- und zwar fuer jeden der bis zu 108 Kandidaten gleich, ausgerechnet auf die ID von
`dome_stack_peek`. Als Policy-ZIEL mit Gewicht 1 waere das aktiv schaedlich. Der
Such-Record kodiert die Startaktionen deshalb als `choose_dome_slot` (IDs 328..354) mit
`is_start: true`; die vier Rotationen einer (Platte, Slot) fallen auf eine ID und ihre
Besuchsmasse addiert sich. Der Bestandspfad (Handregel, Streuung) behaelt `"type": "dome"`
unveraendert, `NUM_ACTIONS` bleibt 406 und der Vertragshash unberuehrt.

**Trainingsseite.** `engine/py/corpus_dataset.py`: ein Start-Record mit `start_by_search: true`
UND `policy_target_valid != false` bekommt `pol_w = 1`; alle uebrigen Start-Records bleiben bei
0. Cache-Schluessel BEWUSST ohne eigene Komponente, mit Begruendung im Code: `str(files)` steht
schon im Schluesselmaterial, und das Feld kann nur in Dateien stehen, die es vor dem
2026-09-12 nicht gab -- ein Alt-Cache ist nicht erreichbar, waehrend eine unbedingte
Komponente JEDEN vorhandenen Cache entwertet haette. Wiedervorlage im Code vermerkt: wird die
REGEL spaeter geaendert, ist eine Komponente Pflicht.

**Informationsmenge.** Die Suche determinisiert die Wurzel aus Sicht von `pi` -- nicht
`current_player`, denn der Nicht-Starter legt zuerst. Dafuer der Wrapper
`determinize_hidden_information_for`; ohne ihn saehe die Suche die echte verdeckte
Nachziehplatte, die `apply_start_placement` sofort ins Display zieht. Eingetragen in
`docs/architecture_reference.md`, Abschnitt "Wo der Code Information ABSICHTLICH vernichtet".

**Benannte Modellannahme:** steht bei der Suche des Nicht-Starters noch die Setzung des
Gegners aus, loest sie IM BAUM die Handregel auf. Gemessen wird also "wie gut ist meine
Setzung, wenn der Gegner wie die Handregel legt", nicht "gegen die beste Gegensetzung".
Zweite benannte Eigenschaft: Prior und Trainingsziel liegen beide im Ego-Rahmen von
`current_player` (also des Startspielers), auch wenn der Nicht-Starter legt -- das ist der
Bestands-Rahmen des Records, nicht eine neue Entscheidung.

**Tests geschrieben, nicht gelaufen:** Rust -- Knopf 0 ergibt auch mit Netz keine
Such-Parameter (und Knopf 1 ohne Netz ebenso wenig), die Suche liefert eine Setzung AUS der
Kandidatenmenge und besucht hoechstens die Gumbel-Wurzelbreite, der Record traegt die beiden
Vertragsfelder nur bei Knopf 1, die Spec ohne `start_by_search` laedt weiter, der Knopf ist
ungesetzt 0, und die ID-Helfer sind gegen `action_to_id` gespiegelt (inklusive des
405-Kollaps-Befunds). Python: `py_compile` gruen, Konventions-Check gruen.

**Offen:** nichts kompiliert (`cargo test --release --lib`, Beispiele/Benches, Wheel-Bau);
Anker-Invarianz (Drift und Konservierung) nach dem Wheel-Bau; Golden-Proben der
NETZ-Artefakte (`pending_dome_choice`) sind unberuehrt, solange die Artefakte auf ihren
eigenen Wheels spielen und ihre Specs das Feld nicht tragen -- das ist heute der Fall, aber
ungeprueft am Artefakt-Bestand; das A/B (200 Paare, Champion mit Such-Start gegen Champion mit
Handregel) samt der drei Messfragen aus par.9c.

## par.9e A/B DES SUCH-STARTS (2026-09-12, 17:13-18:03, `tools/night_start_by_search_ab.sh`)

Bau-Tore vorab gruen (Lib-Tests 613, Wheel, Fixture und Kontrakt unveraendert, Anker-Drift und
Konservierung gegen hv4_anchor gruen). A/B gepaart: v28-b02 mit `start_by_search 1`
(`models/start_by_search_on.spec.json`) gegen v28-b02 mit Champion-Spec, Seed 20261048,
Blockgroesse 5, `--log-games`, 10 Threads, exklusiv; **SPRT H0 nach 95 Paaren** (LLR -3,50;
2.977 s, 15,7 s je Partie). Artefakt `paired_gating_v28-b02_startsearch_vs_v28-b02_s48.json`.

**Messfrage (a), Abweichungsrate:** aus den START_TILE-Logzeilen, Seitenzuordnung ueber
`side_names` je Partie (die Lognamen NetzA/NetzB sind Brettnamen): die Handregel-Seite legt
190 von 190 auf (0,0); **die Such-Seite legt 177 von 190 (93 %) auf (2,0)**, 12 auf (0,0), 1 auf
(1,0). Die Suche weicht also nicht gelegentlich ab, sie hat eine ANDERE feste Praeferenz: die
untere linke Ecke, zeilengespiegelt zur Handregel.

**Messfrage (b), Kosten der Abweichung:** Punkte gepaart -0,05 [-3,04; +2,94], Marge -0,11
[-6,09; +5,88]; Abweichungspartien der Such-Seite im Mittel Marge -0,1 (n=178) gegen +0,7 bei
den zwoelf (0,0)-Partien (n zu klein). Plattenpunkte gepaart (Such-Start minus Handregel):
**Eckplatten +1,85 [+0,58; +3,11]**, **Aeussere Felder +0,83 [+0,37; +1,30]**, Vertikale Reihen
-0,82 [-2,24; +0,60], Spezialfelder -0,25, Strafleiste -0,45 [-1,71; +0,81]; Summe der
Endwertung +8,71 gegen +8,03 je Partie. Die Suche kauft mit (2,0) Eck- und Aussenfeld-Punkte
und gibt sie bei den vertikalen Reihen wieder ab.

**Messfrage (c), Siege:** 91:99, McNemar p 0,67, gepaarte Differenz -0,08 [-0,37; +0,20].
**Gleichwertig** (Nutzer 18:00: "schaut gleichwertig aus. das ist gut").

**Lesart, und was sie an Stufe 0 korrigiert:** fuer die Heuristiken (hv1@25, hv1@400, hv2@150)
kostet Reihe 2 elf bis dreizehn Punkte (par.9); fuer das Netz mit Huelle kostet (2,0) nichts.
"Guter Start ist eine Eigenschaft der Position" gilt also innerhalb der Heuristik-Familie und
NICHT fuer den Spieler, um den es geht: das Netz spielt von (2,0) aus einen anderen Plan
(Ecken und Aussenfelder statt vertikaler Reihen) mit gleichem Ergebnis. Genau das ist der
Grund, den Startzug der Suche zu ueberlassen (par.9c): nicht Elo, sondern dass die Wahl zum Plan
des Spielers passt. Fuer die v29-Erzeugung mit Such-Start heisst das: der Korpus wird zu rund
93 % (2,0)-Starts tragen, die Streuung (par.9b, p 0,15) liefert die uebrigen Slots; der
Policy-Kopf lernt damit erstmals einen Start-Prior, der nicht die Handregel ist.

**Werkzeug-Befund:** `tools/probes/arena_column_probe.py` konnte 190 von 190 Partien NICHT
nachspielen (Replayer loest die Startsetzung mit der Handregel auf und divergiert dann);
volle Spalten je Seite fehlen deshalb fuer dieses A/B und sind aus den Logs per
`reconstruct_game` (Muster Stufe-0-Sonde) nachzuziehen; der Replayer braucht die Startsetzung aus
der START_TILE-Zeile (Aufgabe, nicht gebaut).

**Offene Zahl (Nutzer 18:25, "mach das"):** welcher Term treibt die (2,0)-Praeferenz, der auf
(2,0)-Brettern untrainierte Value-Kopf oder die Huellen-Verschiebung (Dreieck geometrisch unten)?
Diagnose `tools/night_start_search_hull_off.sh` nach `tail9`: zwei Instrument-Laeufe (100 Partien
@400 deterministisch, Seed 20260931) mit Such-Start, einmal Champion-Spec, einmal `k3v_off` plus
`start_by_search`; Zielgroesse Slotverteilung der Startsetzungen je Lauf (aus den Records,
`start_by_search`-Feld). Lesart vorab: kehrt die Suche ohne Huelle zu (0,0) zurueck, treibt die
Huelle; bleibt (2,0), treibt der Value-Kopf (und dann ist die v29-Streuung die Korrektur, weil er
dort extrapoliert).

**Diagnose GEMESSEN (21:10-21:40, `tools/night_start_search_hull_off.sh`; je 100 Partien @400
deterministisch, Seed 20260931, 400 Startsetzungen je Lauf, alle `start_by_search`, Policy-Ziel
gueltig; Artefakte `c2_v28b02_startsearch_hull.json`, `c2_v28b02_startsearch_nohull.json`,
`start_search_hull_off_slots.json`):**

| Einstellung | (2,0) | (0,0) | (1,0) | volle Spalten je Seite | Punkte |
| --- | --- | --- | --- | --- | --- |
| Such-Start mit Huelle (Champion-Spec) | 350 (87,5 %) | 42 | 8 | 0,905 | 52,8 |
| Such-Start ohne Huelle (k3v_off) | 338 (84,5 %) | 48 | 14 | 0,735 | 51,2 |

**Lesart nach der vorab festgelegten Regel: die Praeferenz fuer (2,0) bleibt ohne Huelle, also
treibt sie NICHT die Huellen-Verschiebung, sondern das Netz selbst** (Value-Kopf auf Brettern,
die es nie gesehen hat, plus der auf den Start uebertragene Kuppelplatzierungs-Prior; welcher
der beiden Anteile ueberwiegt, trennt dieses Instrument nicht). Die v29-Streuung (par.9b) und die
Such-Start-Records mit gueltigem Policy-Ziel sind genau die Korrektur: ab v29 sieht der Value-Kopf
alle Slots, und der Prior lernt den Start. Nebenbefund: die Huelle bringt auch am Such-Start
+0,17 volle Spalten und +1,6 Punkte (Instrument, gleicher Seed), konsistent mit C2.

## par.9f BAUSTAND Platte/Rotation (2026-09-12, Agent; NICHTS kompiliert, nichts gemessen)

Auftrag: par.9a Punkt 1, die erste Haelfte (Handregel gegen Zufall, netzfrei; die
Ownership-Ablesung par.2a braucht ein Netz und ist nicht Teil dieses Baus). Alles hier ist
Baustand aus Quelltext, kein Kompilat und kein Lauf -- `cargo` und `maturin` waren gesperrt.

**Knopf.** `MOSAIC_START_TILE_RANDOM_P0` / `..._P1` (Diagnose, kein Spec-Feld, Registratur
`knob_registry.rs`, `docs/knobs.md` neu erzeugt): waehlt fuer den jeweiligen Spieler PLATTE und
ROTATION der Startkuppel GLEICHVERTEILT aus den Kandidaten des Slots, den die Handregel gewaehlt
haette -- also (0,0), oder der erzwungene Slot aus `MOSAIC_START_SLOT_P0/P1`. Werte 0 und 1;
ungesetzt, leer oder ungueltig = Bestand, bitidentisch und ohne jeden RNG-Zug (einmalige Warnung
bei ungueltigem Wert). Je Startsetzung gelesen (kein `OnceLock`), damit der Treiber beide Arme in
EINEM Prozess faehrt. Bausteine in `engine/src/self_play.rs`: `parse_start_tile_random` (rein),
`random_start_tile_enabled` (Env-Huelle), `sample_random_start_tile` (reiner Kern, RNG von
aussen) und die neue Huelle `choose_start_placement_rng(state, pi, rng)`.

**Signatur.** `choose_start_placement(state, pi)` bleibt unveraendert und delegiert mit
`rng = None` -- kein Bestands-Aufrufer war anzufassen, also auch keiner in `engine/examples/`
oder `engine/benches/` (beide rufen die `pub(crate)`-Funktion ohnehin nicht).
`choose_start_placement_with_slot` ist unberuehrt.

**Wirkungsbereich (geprueft per Grep 2026-09-12).** Den Knopf sieht nur, wo ein RNG
durchgereicht wird: die Heuristik-Arena `play_arena_game` (das ist `mosaic_rust.arena_match`,
der Einstieg der Sonde) und das aufzeichnende Self-Play `start_placement_step`. Referee
(`referee.rs:122/508`), Rundenuebergang (`round_transition.rs`), `py.rs`, die Diagnose-Schleife
`play_stage3_vs_stage1_game` und jede GESUCHTE Startsetzung (par.9c) rufen weiter ohne RNG und
bleiben Bestand. In Gating, Anker-Kanten und Erzeugung ist der Knopf nie gesetzt.

**Zufallsquelle, und warum sie in der Arena NICHT der Partie-RNG ist:** `play_arena_game` zieht
aus einem eigenen, aus `game_seed` abgeleiteten Strom
(`derive_search_seed(game_seed, (1 << 40) + pi)`, Muster `PREREG_search_rng_split.md`, zwei
Zeilen weiter unten fuer die Drafting-Suche schon so gebaut). Aus dem Partie-RNG zu ziehen waere
reproduzierbar, wuerde aber ALLE spaeteren Nachziehplatten verschieben -- der gepaarte Vergleich
Handregel gegen Zufall waere dann an der Wurzel entpaart, und die Partien, in denen die Ziehung
zufaellig die Wahl der Handregel trifft, waeren nicht mehr identisch. Im Self-Play zieht die
Streuung dagegen aus dem Partie-RNG, genau wie die Slot-Streuung par.9b.

**Record-Vertrag (Self-Play, nur bei gesetztem Knopf):** `policy_target_valid: false` und
`start_tile_randomized: true` -- eigener Schluessel neben `start_slot_randomized`, damit eine
Sonde die beiden Streuquellen nicht verwechselt. Bei ungesetztem Knopf wird kein Feld
geschrieben, der Record ist byte-gleich zum Bestand.

**Sonde** `tools/probes/start_dome_tile_probe.py`: Einstieg
`mosaic_rust.arena_match(log_games=True)`, hv1 auf beiden Seiten, netzfrei; zwei Arme (Handregel,
Zufall) ueber demselben Seed, Spieler 1 immer Bestand; Defaults `--n-seeds 200`,
`--pairings 25,400`, Seed-Basis 20260912, `--slot` optional. Je Arm die Kennzahlen der
Stufe-0-Sonde (dieselben Helfer `game_metrics`, `mean_ci`, `METRICS`, `realised_start_slot`, also
dieselben Groessen), dazu Reihen- und Spaltenprofil und Plattenpunkte je Kriterium; gepaarte
Differenz Handregel minus Zufall mit 95-%-KI, je Kennzahl UND je Wertungskriterium. Zwei
Kontrollen aus dem Log: der gelegte Slot muss in beiden Armen (0,0) bleiben, und die Verteilung
von Platte und Rotation (neuer Helfer `realised_start_tile` aus der START_TILE-Zeile) darf im
Zufallsarm nicht entarten -- sonst haette er den Bestand unter falschem Etikett gespielt. JSON
mit n/Grundmenge/Einheit, `laufzeit`-Block und `cli_args`.

**Vorab-Lesart (im Docstring der Sonde und im Artefakt):** gepaarte Differenz Handregel minus
Zufall in Marge und Punkten. Schliesst das 95-%-Intervall 0 ein, ist auch Platte/Rotation kein
Hebel und par.9a Punkt 1 ist geschlossen; ist die Differenz gross, traegt die Handregel und ist
die Messlatte, die der Such-Start (par.9c) an dieser Stelle mindestens erreichen muss.

**Tests geschrieben, nicht gelaufen** (Rust, Modul `start_slot_tests` in `self_play.rs`): der
Knopf nimmt nur 0 und 1; ungesetzt ist er fuer beide Spieler aus; bei ungesetztem Knopf liefert
der RNG-Pfad die Bestandswahl UND verschiebt den gereichten Strom nicht (16 Zuege verglichen);
die Ziehung bleibt im Slot und liefert immer einen echten Kandidaten; ueber 200 Ziehungen je
Kandidat kommt JEDER Kandidat des Slots vor (nicht entartet, grobe Gleichverteilungs-Schranke);
leere Auswahl zieht nichts. Python: `py_compile` gruen, Konventions-Check gruen.

**Offen / ungeprueft:** nichts kompiliert (`cargo test --release --lib`, Beispiele/Benches,
Wheel-Bau) und damit auch die Anker-Invarianz nicht; die Bitidentitaet bei ungesetztem Knopf ist
am Quelltext begruendet (der Zweig wird nicht betreten), nicht gemessen; die Sonde ist nicht
gelaufen. Rauchtest vorgesehen:
`python -X utf8 -u tools/probes/start_dome_tile_probe.py --limit 4 --pairings 25 --threads 4`;
voller Lauf: `python -X utf8 -u tools/probes/start_dome_tile_probe.py` (exklusiv).

**KORREKTUR 22:05 (Replayer-Befund, Agent, vom Koordinator uebernommen; Regel
`PREREG_search_rng_split.md`):** der Replayer liest die Startsetzung schon aus der START_TILE-Zeile
(`analyze_game_log.py:1196-1199` -> `py.rs:344 apply_start_tile`); die 190 nicht nachspielbaren
Partien kommen nicht von der Handregel, sondern von einem RNG-Leck: die Startsetzungs-SUCHE zog
aus dem geteilten Partie-RNG (Determinisierung plus jede Simulation), den der Replay aus dem Seed
nachbaut; ab der ersten Turm-Nachfuellung (`supply.rs:43/50`, `state.rs:354`) divergieren Log und
Replay. Dieselbe Verschiebung entpaart gepaarte Arenen ab dieser Stelle: **das A/B par.9e ist ab
der ersten Nachfuellung nur nominell gepaart** (jede Partie fuer sich bleibt fair, beide Spieler
sehen dieselben Fabriken; Siege 91:99 und Punkte gelten als ungepaarter Vergleich, die gepaarten
Intervalle sind zu eng gerechnet). Fix: eigener seed-abgeleiteter Strom fuer die Start-Suche
(`derive_search_seed(game_seed, START_SEARCH_STREAM + start_step)`), Arena-Zweig gefixt, Self-Play-
und Diagnose-Zweig in Arbeit (Agent), dann Bau-Tore und WIEDERHOLUNG des A/B mit echter Paarung
(`tools/night_tile_probe_replay.sh` erweitert). Die 93-%-Praeferenz fuer (2,0) ist von dem Leck
nicht betroffen (sie ist die Wahl der Suche, nicht der Partie).

## par.9f ERGEBNIS Platte/Rotation (2026-09-12, 22:18-22:24, `tools/night_tile_probe_replay.sh`)

Bau-Tore vorab gruen (637 Lib-Tests, Beispiele/Benches, Wheel, Anker-Drift und Konservierung
gegen hv4_anchor, Python-Spiegeltest der Aktions-IDs 8/8); Rauchtest 4 Partien gruen; voller
Lauf exklusiv: 200 Seeds x 2 Arme x 2 Paarungen = **800 Partien in 322 s** (0,40 s je Partie,
alle Kerne), Artefakt `evaluations/artifacts/start_dome_tile_probe.json`. Grundmenge: Partien
eines Arms je Paarung, Sicht Spieler 0, Einheit je Partie; n = 200 Paare je Paarung.

**Beide Kontrollen bestanden:** der gelegte Slot ist in allen 800 Partien (0,0) (Treffer 200/200
je Arm und Paarung, keine Abweichung); die Handregel legt 18 verschiedene Platten, alle mit
Rotation 0 (200 von 200); der Zufallsarm legt 68 verschiedene Platte-Rotations-Kandidaten mit
Rotationen 0/90/180/270 = 44/55/47/54. Der Zufallsarm hat also wirklich anders gelegt, und die
Handregel waehlt nie eine gedrehte Platte.

**Gepaarte Differenz Handregel minus Zufall (Spieler 0, 95-%-KI):**

| Paarung | Punkte | Marge | volle Spalten | Strafpunkte |
| --- | --- | --- | --- | --- |
| hv1@25 | +1,84 [-0,71; +4,39] | +2,73 [-0,51; +5,97] | +0,03 [-0,03; +0,08] | -1,37 [-2,71; -0,02] |
| hv1@400 | +1,60 [-1,16; +4,37] | +0,89 [-2,89; +4,67] | +0,04 [-0,03; +0,10] | -0,39 [-1,74; +0,96] |

Plattenpunkte je Kriterium: einzig **Mehrfarbige Felder** traegt in beiden Paarungen fuer die
Handregel (+0,72 [+0,20; +1,24] @25, +0,56 [+0,04; +1,08] @400); Eckplatten @400 -0,29
[-0,47; -0,11] gegen die Handregel, volle Reihen @400 -0,16 [-0,30; -0,02]; alle uebrigen
Kriterien und alle Reihen-/Spalten-Profile schliessen 0 ein.

**Verdikt nach der Vorab-Lesart: das Intervall schliesst 0 ein, Platte/Rotation ist fuer die
Heuristik kein Hebel; par.9a Punkt 1 ist GESCHLOSSEN.** Die Handregel ist etwa 1,5 bis 2 Punkte
je Partie wert (Punktmittel beider Paarungen, nicht signifikant), und der Betrag sitzt in den
mehrfarbigen Feldern: die Handregel legt die Platte so, dass mehr Farben nebeneinander liegen,
und kauft das bei @400 mit weniger Eckplatten-Punkten. Fuer den Such-Start (par.9c) heisst das:
die Messlatte an dieser Stelle ist niedrig; das A/B par.9e (Siege gleich, Punkte gleich) hat sie
erreicht. Fuer v29 bleibt die Streuung auf den SLOT beschraenkt (par.9b); eine Streuung ueber
Platte/Rotation wird nicht eingebaut, weil der Zufallsarm hier zeigt, dass der Ertrag klein ist,
und die Such-Seite die Rotation ohnehin frei waehlt (Kandidatenmenge <= 108 in par.9c).

## par.9e WIEDERHOLUNG MIT ECHTER PAARUNG (2026-09-12, 22:26-23:09, `tools/night_tile_probe_replay.sh`)

Nach dem RNG-Leck-Fix (Start-Suche zieht in allen Pfaden aus einem eigenen seed-abgeleiteten
Strom, `START_SEARCH_STREAM` in shaping.rs; Bau-Tore gruen, Anker-Drift und Konservierung gruen)
derselbe Aufbau wie oben mit Seed 20261049: v28-b02 `start_by_search 1` gegen v28-b02 Champion-
Spec, Blockgroesse 5, `--log-games`, 10 Threads, exklusiv. **SPRT H0 nach 85 Paaren** (LLR -3,03),
**Siege 81:89**, McNemar p 0,63, gepaarte Differenz -0,09 [-0,38; +0,19]; 2.545 s, 15,0 s je
Partie. Artefakt `paired_gating_v28-b02_startsearch_vs_v28-b02_s49.json`.

**Replay traegt jetzt:** `arena_column_probe` spielt 169 von 170 Partien nach (vorher 0 von 190);
die eine Divergenz ist die bekannte Chip-Vollendungs-Grenze des Replayers ("Reihe 6 nicht mit
Chips" nach 60 Versuchen), nicht die Startsetzung. Das Leck ist damit als Ursache bestaetigt und
geschlossen; das A/B oben (Seed 20261048) bleibt als ungepaarter Vergleich stehen.

**Praeferenz unveraendert:** Such-Seite 158 von 170 (93 %) auf (2,0), 12 auf (0,0); Handregel-Seite
170 von 170 auf (0,0). **Volle Spalten je Brett** (Replay, n=169): Such-Start 0,95 +- 0,12,
Handregel 0,98 +- 0,11; Huellenanteil H 0,55 gegen 0,60. **Gepaart, Such-Start minus Handregel
(85 Paare):** Punkte +1,09 [-1,75; +3,94], Marge +2,19 [-3,50; +7,88], Plattenpunkte gesamt +0,92
[-0,26; +2,10]; je Kriterium Eckplatten +1,85 [+0,37; +3,33], Aeussere Felder +0,57 [+0,11; +1,03],
Vertikale Reihen +0,50 [-0,63; +1,63], Mehrfarbige Felder -0,47 [-2,12; +1,18]; Kuppel-Boni
(`spezial_bonus`) +2,25 [+1,52; +2,99], Platzierungspunkte -1,87 [-3,95; +0,23].

**Lesart:** beide Seeds sagen dasselbe, jetzt sauber gepaart: gleichwertig in Siegen und Punkten,
andere Plan-Signatur (Ecken, Aussenfelder und Kuppel-Boni statt Platzierungspunkte). Die Spalten
bleiben gleich (0,95 gegen 0,98, Intervalle ueberlappen), der Such-Start kostet also auch beim
Spaltenbau nichts. Entscheid par.9c (Such-Start ins v29-Rezept) bleibt.

## par.10 ABSCHLUSS (2026-09-13, 01:15; Nutzer: "schliess auch die 3 preregs von vorhin")

Die Frage "lohnt es, den Startzug zu befreien?" ist beantwortet: die Suche legt anders (93 Prozent
auf (2,0) statt (0,0)), spielt aber gleich stark und baut gleich viele Spalten (par.9e, zwei Seeds,
der zweite echt gepaart); Platte und Rotation sind kein Hebel (par.9f). Was daraus ins Rezept geht,
ist entschieden und in `PREREG_v29_window.md` par.6b registriert (Slot-Streuung 0,15 je Spieler,
Such-Start in der Erzeugung). Der einzige Rest, die Plattenwahl (par.6a: `choose_start_placement`
bewertet Spezialfelder mit 0,0), laeuft im v29-Begleitprogramm (`PREREG_v29_window.md` par.7
Punkt 4) und wird dort registriert, nicht hier.
