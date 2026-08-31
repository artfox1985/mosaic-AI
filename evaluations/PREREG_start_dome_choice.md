<!-- STATUS: OFFEN | Frage: Die Startkuppel ist ein 108-Wege-Entscheid (Auslage x Slot x Rotation) und legt die Brettgeometrie fest -- gelegt wird sie aber von einer Handheuristik, und das Trainingsziel ist ein One-Hot darauf. Lohnt es, den Zug zu befreien? | Beleg: NICHTS GEBAUT. **Nutzer 2026-08-31: die Plattenverteilung ist der GENERELLE Hebel** (k6 ist nur in einem Drittel der Partien aktiv). Dazu der Code-Befund par.6a: die Handheuristik bewertet Spezialfelder mit NULL -- sie optimiert Farbnachschub, nicht Ertrag. Aendern darf man sie nicht (Elo-Anker), der Weg fuehrt ueber die Netz-Seite. Stufe 0 ist jetzt faellig (Generation 2). -->

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
