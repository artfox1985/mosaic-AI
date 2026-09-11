<!-- STATUS: OFFEN | Frage: Wie modelliert die Suche den Kuppelstapel als Informationsmenge statt ihn bei jeder Suche ganz zu mischen? | Beleg: VARIANTE A GEBAUT 2026-09-10 (par.15), A/B Live gegen Artefakt 165:135, Fix bleibt (par.15b); Ziehungen in den eigenen Block STEIGEN mit A (+0,69 je Partie, par.15e), regelkonform: Ziehen bei Stand 0 bleibt gratis, Null-Klammer als Regel entschieden (par.15f, PREREG_score_clamp_incentive.md). VARIANTE B GEBAUT 2026-09-11 (elf Merkmale 744..754, INPUT_SIZE 755), Arm v28-b02 gegen b01 in Messung (PREREG_v28_window.md par.9/10), Ergebnis steht aus. -->

# PREREG: Informationsmengen am Kuppelstapel

**Vorregistriert 2026-09-09 auf Nutzer-Auftrag** ("das waere der naechste grosse Brocken
fuer v27. den kannst schon vorregistrieren. da ist ordentlich was im unreinen").

## par.1 DIE FRAGE

Der Kuppelstapel ist die einzige Stelle im Spiel, an der ein Spieler durch BEZAHLTE
Handlung Wissen erwirbt, das er danach behalten koennte. Heute behaelt er es nicht.

**Die Frage ist nicht "zieht die KI zu oft?"** -- das ist beantwortet
(`PREREG_stack_draw_reservation_rule.md` par.5b: die optimale Tiefe ist ueberall 1). Die
Frage ist, ob die Suche ueberhaupt in der Lage IST, die richtige Antwort zu finden, solange
sie den Zustand des Stapels bei jeder Suche neu wuerfelt.

## par.2 DER ANLASS, am Log geprueft

`static/log/game_20260909_004553_seed876496.log`, Nutzer-Befund
("ich versteh auch das Kaufen der Kuppelplatten nicht. einmal alle kaufen ok. dann weiss
ich wo was liegt. aber das zweite Mal macht meiner Meinung nach wenig Sinn"):

| Runde | Ziehungen | Zurueck unter den Stapel | Punktestand der KI danach |
| --- | --- | --- | --- |
| R1 | 13 (Z. 37-49) | 12, Reihenfolge im Log (Z. 50) | 0 (von 4 auf 0 in den ersten vier) |
| R2 | 2 | 1 (Z. 137) | 0 |
| R3 | 5 (Z. 246-250) | 4 (Z. 251) | 0 |
| R4 | 1 (Z. 369) | -- | 0 |

Endstand 0 gegen 69. **Die KI stand ab R1 durchgehend auf 0**, und dort sind sowohl
weitere Ziehungen als auch die Strafleiste gratis (Strafen -2, -6, -12, -10 alle auf 0
geklammert, Z. 103/209/304/387). Das ist ein EIGENER Strang, siehe par.9.

## par.3 WAS DER CODE HEUTE TUT (geprueft 2026-09-09)

| Stueck | Befund | Pruefstelle |
| --- | --- | --- |
| Rueckgabe unter den Stapel | `push` in der vom Ziehenden GEWAEHLTEN Reihenfolge; Ziehung nimmt vorne (`remove(0)`) | `engine/src/game.rs:278`, `:183` |
| Die Reihenfolge ist im Zustand | der Vec traegt sie, das Log druckt sie sogar aus | `engine/src/game.rs:285` |
| Die Suche wuerfelt sie weg | `build_net_tree` ruft an der WURZEL JEDER Suche `determinize_hidden_information`, dort `state.dome_tile_pool.shuffle(rng)` | `engine/src/net_mcts.rs:3952`, `:987` |
| ...und ein zweites Mal je simuliertem Rundenwechsel | `simulate_one_round` mischt den Stapel beim Eintritt, ungeschuetzt | `engine/src/round_transition_deep.rs:623` |
| Der Schalter ist bewusst an | `DETERMINIZE_ROOT_HIDDEN_INFO = true`, Nutzer-Entscheid 2026-07-20, Begruendung KORREKTHEIT (kein Orakelwissen) | `engine/src/net_mcts.rs:976` |
| Was das Netz vom Stapel sieht | `dome_stack_count`, `dome_wild_remaining_frac` UND seit v24-b04 die Plattentyp-Sicht: `[top_is_special, top_is_wild]` plus je Auslage-Slot `[has_special, has_wild]`, acht Werte ans Ende, Teil des Sicht-Arms, der INPUT_SIZE von 714 auf 744 hebt | `engine/src/features.rs:418-455`, `PREREG_stack_top_feature.md` par.6/par.10 |
| Was es NICHT sieht | alles jenseits der obersten Karte: kein Wissensstand, keine Blockgrenze, keine Menge des bekannten Blocks | dieselbe Stelle, keine weiteren Stapelfelder |

**Der Kern in einem Satz:** die Determinisierung ist gebaut, um der Suche Wissen zu NEHMEN,
das ein echter Spieler nicht hat. Sie nimmt aber auch das Wissen, das er rechtmaessig HAT,
naemlich seine eigene Rueckgabe-Reihenfolge. Aus Sicht der Suche ist jede Ziehung die
erste; sie weiss nicht, dass sie es schon weiss.

## par.4 DIE REGELLAGE (Nutzer 2026-09-09, woertlich sinngemaess uebernommen)

**Der Gegner kennt die Reihenfolge beim Zuruecklegen offiziell NICHT.** Was er kennt, ist
mehr als nichts und weniger als alles:

**Beispiel A, Gegner zieht zwei.** Ich kenne die Rueckseiten (Typ: Wild oder Special) der
zwei gezogenen und die Rueckseiten der am Stapel ausliegenden. Der Gegner legt eine auf die
Kuppel: die kenne ich damit vollstaendig (Vorderseite). Also kenne ich auch die letzte
Karte unter dem Stapel vollstaendig, denn es kann nur die andere gezogene sein.

**Beispiel B, Gegner zieht drei.** Ich kenne die Rueckseiten der drei gezogenen und der
ausliegenden. Eine geht auf die Kuppel, die kenne ich. Die zwei uebrigen gehen unter den
Stapel: **ich weiss nicht, in welcher Reihenfolge, aber ich weiss, dass an diesen beiden
Positionen zwei Karten mit mir bekannten Rueckseiten liegen.**

**Verallgemeinert:** nach einem fremden Stapelzug mit k Ziehungen und einer Platzierung
zerfaellt der Stapel fuer den Beobachter in drei Bereiche:

1. **oben, unberuehrt:** unveraendert unbekannt (nur Typ der obersten sichtbar),
2. **unten, ein Block von k-1 Positionen:** die MENGE ist bekannt (die gezogenen minus der
   platzierten), die REIHENFOLGE innerhalb des Blocks nicht,
3. bei k = 2 faellt Fall 2 mit vollstaendigem Wissen zusammen (ein Element, Menge =
   Reihenfolge).

**Fuer den Ziehenden selbst** ist der Block unten vollstaendig bekannt, inklusive
Reihenfolge, weil er sie gewaehlt hat. Die Informationsmengen der beiden Spieler sind
also VERSCHIEDEN -- genau das ist heute nicht modelliert.

## par.4b DAS WISSEN IST EIN GUT, UND DER PREIS IST NIEDRIG (Nutzer 2026-09-09)

**Nutzer, sinngemaess:** den ganzen Stapel neu zu mischen macht keinen Sinn -- die oberste
Karte ist ohnehin teilweise bekannt (Typ), und je mehr Kuppelkarten ich inspiziert habe,
desto bekannter ist der Stapel. *"Wenn ich also 11 zieh und mein Gegner nichts an der
Reihenfolge aendert, hab ich das ultimative Orakelwissen. Fuer ein paar Punkte. Nicht der
schlechteste Tausch."*

Das dreht die Erwartung um, mit der diese Prereg zuerst geschrieben war. Der tiefe Zug ist
dann nicht der Fehler, sondern moeglicherweise die richtige Eroeffnung: er kauft

1. die beste Platte JETZT (das ist der einzige Posten, den die Stopp-Regel bepreist,
   `PREREG_stack_draw_reservation_rule.md` par.3: `V(Platte)` ist der Platzierungswert in
   Punkten, Maximum ueber Slot und Rotation), und
2. **die Kenntnis des Stapels fuer den REST der Partie** -- ein Posten, der in `V`
   ueberhaupt nicht vorkommt.

**Damit ist par.5b jener Prereg ("die optimale Tiefe ist ueberall 1") innerhalb seines
Modells richtig und als Handlungsanweisung unvollstaendig.** Das Modell ist gedaechtnislos:
es preist den Sofortwert und unterstellt implizit, dass das Gesehene danach wertlos ist.
Genau das ist heute wahr -- weil die Suche mischt (par.3). Wird der Umbau gebaut, wird die
Praemisse falsch, und die Regel muss neu gerechnet werden. Ein datierter Hinweis steht dort.

**Und die Stelle, an der dieser Strang den aus par.9 beruehrt:** das Wissen wird in
PUNKTEN bezahlt, und Punkte sind genau dort keine Waehrung mehr, wo der Zaehler klemmt. Im
Anlassspiel haben die Ziehungen 1 bis 4 echte Punkte gekostet, die Ziehungen 5 bis 13 gar
nichts (Log Z. 41-49, alle auf 0). Der Tausch "ein paar Punkte gegen Orakelwissen" ist
also in beide Richtungen unbepreist: oberhalb von null zahlt man einen Preis, den das
Modell nicht gegen den Nutzen haelt, unterhalb zahlt man keinen. Wer den Optionswert
einbaut, sollte im selben Zug wissen, ob die Waehrung traegt.

**Zwei Folgerungen, die dann zum Spiel gehoeren:**

* **Das Wissen waechst monoton.** Jede Inspektion und jede auf die Kuppel gelegte Platte
  verkleinert die Restunsicherheit; der Stapel wird ueber die Partie hinweg immer
  bekannter, nie unbekannter -- ausser durch fremde Zuege.
* **Wissen laesst sich zerstoeren.** Zieht der Gegner selbst und legt neu zurueck, ordnet er
  den unteren Block um; mein Wissen ueber diese Positionen faellt von "Reihenfolge" auf
  "Menge" (par.4, Beispiel B). Das ist eine echte Stoerhandlung und hat Verwandtschaft zum
  Chip-Denial-Strang -- ob die Suche sie je findet, ist eine Frage NACH dem Umbau.

## par.5 WAS DARAUS FOLGT (Anforderung, noch keine Bauentscheidung)

Ein korrektes Modell braucht drei Dinge, die es heute nicht gibt:

1. **Einen Wissensstand JE SPIELER und JE POSITION, mit DREI Stufen** (Nutzer 2026-09-09:
   *"die Wurzeldeterminisierung muss dann unterscheiden: was ist vollkommen unbekannt, wo
   kenn ich die Rueckseite und was kenn ich"*):

   | Stufe | Was der Spieler weiss | Woher |
   | --- | --- | --- |
   | 0 unbekannt | nichts ueber diese Position | nie gesehen |
   | 1 Rueckseite | der TYP (Wild oder Special) | lag oben auf (offen sichtbar) oder wurde vom Gegner gezogen |
   | 2 Identitaet | die Platte selbst | selbst gezogen, oder als einzige Rueckgabe des Gegners erschliessbar (par.4 Beispiel A) |

   Heute gibt es keinen dieser Staende: ein einziger wahrer Stapel und eine
   Determinisierung, die ihn ganz mischt.
2. **Eine Determinisierung unter NEBENBEDINGUNGEN statt eines Vollmischers.** Stufe-2-
   Positionen stehen fest; Stufe-1-Positionen duerfen nur eine Platte des bekannten Typs
   bekommen; nur Stufe 0 ist frei. Bauform: die Restplatten den typgebundenen Positionen
   ohne Zuruecklegen zulosen, dann den Rest frei permutieren. **Ungepruefte Annahme, vor
   dem Bau zu zeigen:** dass das gleichverteilt ueber alle vertraeglichen Welten zieht (die
   Zahl der Vervollstaendigungen haengt nicht davon ab, WELCHE typgleiche Platte eine
   gebundene Position bekommt -- plausibel, aber nicht bewiesen).

   **Praezedenz im selben Code:** `determinize_hidden_information` macht die Unterscheidung
   fuer die BONUSCHIPS bereits -- aufgedeckte Fabrik-Chips sind oeffentliches Wissen und
   bleiben unangetastet, nur die verdeckten werden gemischt (`net_mcts.rs:979-1008`). Der
   Umbau traegt dieselbe Idee an den Stapel, wo sie fehlt; er fuehrt kein neues Konzept ein.
3. **Merkmale, die dem Netz das Bekannte zeigen.** Die OBERSTE Karte sieht es seit v24-b04
   (`features.rs:418-455`, Plattentyp-Sicht); was fehlt, ist alles dahinter -- wie tief der
   bekannte Block reicht und was in ihm liegt. Ohne diese Merkmale kann nur die SUCHE den
   Vorteil nutzen, die Policy nicht.

## par.6 DER ZEITPUNKT IST EINE NUTZER-ENTSCHEIDUNG (Kollision mit par.18)

**`PREREG_v25_window.md` par.18 friert v25, v26 und v27 ein:** fest bleiben Architektur,
Trainingsrezept, Value-Ziel-Mischung, Koepfe und Kopfgewichte; veraendert wird
ausschliesslich das MATERIAL, nach konstanten Erzeugungsregeln. Der Sinn ist die saubere
Attribution: nur so heisst "Generation N+1 schlaegt N" wirklich, dass das Netz besser wurde.

Dieser Umbau beruehrt das in zwei Stufen unterschiedlich stark:

| Stufe | Was sie aendert | Verhaeltnis zu par.18 |
| --- | --- | --- |
| A: nur die Determinisierung | Suchverhalten, keine neuen Merkmale, kein Netz-Umbau | Architektur unberuehrt, aber die ERZEUGUNGSREGEL aendert sich -- und deren Konstanz ist der Zweck des Einfrierens |
| B: A plus Merkmale | Merkmalsvektor waechst -> Eingangsgroesse -> neues Netz | Voller Bruch mit par.18 |

**ENTSCHIEDEN 2026-09-09 (Nutzer):** *"nach v27 ist das Einfrieren beendet. dann sind wir
einmal voll durchrotiert."* Und praezisiert: *"v27-b01 ist der letzte eingefrorene Arm.
dann gehts weiter."*

**Der Ausloeser ist damit ein ARM, keine Generation:** sobald `v27-b01` trainiert ist, ist
die Vergleichskette `v25-b01` / `v26-b01` / `v27-b01` vollstaendig -- drei Arme, gleiches
Rezept, nur rotierendes Material -- und das Einfrieren hat seinen Zweck erfuellt. Der
Umbau darf ab da starten, auch noch innerhalb der Generation v27 (dann als eigener Arm,
`v27-b02` aufwaerts, mit eigener Nummer nach [[feedback_measured_identity_gets_own_bxx]]).
Er muss NICHT auf einen Generationswechsel warten.

**Koordinator-Lesart, als solche markiert:** damit gehoert von den drei Straengen, die als
"Programm fuer v27" gesammelt wurden, nur die G-2-Schwarm-Frage
(`PREREG_v26_window.md` par.6) WIRKLICH nach v27 -- sie ist eine Material-Entscheidung und
vertraegt sich mit dem Einfrieren. Dieser Umbau und die restlichen Sicht-Stufen
(`PREREG_stack_top_feature.md`) liegen dahinter. Wenn das nicht gemeint war, widersprechen.

**Was das fuer die Reihenfolge heisst:** Stufe A und B koennen dann zusammen gebaut werden,
weil kein Einfrieren mehr im Weg steht. Die Anker-Frage bleibt (par.8), und die Aera-Regel
gilt unveraendert.

## par.7 BAUVARIANTEN (Vorschlag, nicht entschieden)

**A) Bekannter Block bleibt bekannt (kleinster Schnitt).** Der Zustand bekommt je Spieler
einen Marker "die untersten n Positionen sind mir bekannt" plus die Sicht darauf (Menge
oder Reihenfolge). `determinize_hidden_information` mischt nur noch den Rest und permutiert
den Block getrennt. Kein neues Merkmal, kein Netz-Umbau. Erwartete Wirkung: die Suche zieht
nicht ein zweites Mal fuer Wissen, das sie hat.

**B) A plus Merkmale.** Zusaetzlich lernt das Netz, was bekannt ist: Groesse des bekannten
Blocks und dessen Zusammensetzung. **Nicht noch einmal die oberste Karte** -- die steht
seit v24-b04 im Vektor (acht Werte, `features.rs:418`; INPUT_SIZE 744). Erst damit kann die
POLICY den Vorteil nutzen statt nur die Suche. Additiv nach der 2D-Encoder-Regel, Alt-ONNX
muessen spielbar bleiben (`net.rs::build_inputs` kuerzt auf die Modellbreite).

**C) Volles Informationsmengen-Modell.** Beide Spieler fuehren ihre Sicht getrennt, die
Suche determinisiert je Wurzelspieler. Groesster Schnitt, groesste Korrektheit; nur
sinnvoll, wenn A und B tragen.

**Nahtbreite vor dem Schnitt messen** (CLAUDE.md-Regel): wie viele Namen stehen ueber der
Naht `dome_tile_pool`? Vor dem Bau zaehlen, nicht schaetzen.

## par.8 WIE ENTSCHIEDEN WIRD (vorregistrierte Metrik)

**Primaer, Staerke:** gepaartes Gating gegen dasselbe Netz OHNE die Aenderung, block-size 5,
zwei unabhaengige Seeds, SPRT; Champion-Strenge wie im Generationsablauf.

**Diagnostisch, und hier liegt die eigentliche Erwartung -- BERICHTIGT nach par.4b:**
gezaehlt wird nicht "Ziehungen je Partie", sondern die **Wiederholungsziehung in einen
BEREITS BEKANNTEN Stapelteil hinein** (aus den Partie-Logs, `tools/analyze_game_log.py`,
Kategorie STACK_PEEK, gegen den mitgefuehrten Wissensstand). Vorregistrierte Richtung: DIESE
Zahl faellt auf nahe null. **Die Gesamtzahl der Ziehungen darf steigen** -- ein tiefer
Erstzug kauft Wissen fuer den Rest der Partie und kann richtig sein.

Die erste Fassung dieser Prereg hat hier "Ziehungen je Partie muessen sinken"
vorregistriert. Das war der Denkfehler des Koordinators, vom Nutzer am selben Tag
korrigiert: er haette den Umbau an genau der Groesse gemessen, die der Umbau erst
wertvoll macht.

**Waechter:** nach der Engine-Aenderung `/mosaic-anchor-invariance` (Drift-Pruefung gegen
`models/frozen_heuristics/hv1_anchor`), und die Aera-Frage stellen, bevor Elo-Zahlen ueber
die Aenderung hinweg verglichen werden.

**Vorab festgehalten, damit es hinterher nicht verhandelt wird:** das ist ein
KORREKTHEITS-Fix. Eine flache Arena ist kein Grund, ihn zurueckzunehmen
([[feedback_correctness_over_measured_benefit]]); ein Ruecklauf schon.

## par.9 WAS NICHT TEIL DIESER PREREG IST

**Die Null-Klammer-Falle.** Bei Punktestand 0 sind sowohl weitere Ziehungen als auch die
Strafleiste gratis, weil ein Punktestand nie unter null faellt (`engine/src/game.rs:182`,
`apply_paid_cost`; Handbuch: "At a score of 0 further draws are effectively free"). Die
Anreizstruktur der Suche bricht dort zusammen -- im Anlassspiel hat die KI ab R1 auf 0
gestanden und danach vier Runden lang Strafen ohne jede Wirkung genommen. Das ist ein
eigener, mindestens gleich grosser Strang: er betrifft die WERTUNG, nicht die Information,
und gehoert in eine eigene Prereg, sobald der Nutzer ihn aufmacht.

**Die Stopp-Regel selbst** ist beantwortet und liegt als Knopf bereit
(`PREREG_stack_draw_reservation_rule.md` par.5c, `MOSAIC_STACK_DRAW_RESERVATION`, Default
AUS). Ob er im Zuge dieses Umbaus neu bewertet wird, entscheidet sich NACH par.7 -- eine
Stopp-Regel auf einem Zustand, den die Suche vergisst, ist etwas anderes als eine auf einem
Zustand, den sie behaelt.

## par.10 NAHT-AUDIT 2026-09-09 (Kanal 1, durchgefuehrt)

**Die vollstaendige Liste steht in `docs/architecture_reference.md`**, Abschnitt "Wo der
Code Information ABSICHTLICH vernichtet" -- sie betrifft den ganzen Baum (24 Mischstellen)
und nicht nur diese Frage, gehoert also ins Dauerwissen und nicht in eine Prereg. Dort
steht auch die Regel fuer neue Stellen.

**Was der Audit FUER DIESE PREREG geaendert hat, zwei Funde:**

1. **Der Umbau muss ZWEI aktive Stellen abdecken, nicht eine.** Neben der
   Wurzel-Determinisierung mischt `round_transition_deep.rs:623` den Stapel bei jedem
   simulierten Rundenwechsel nach. Ein Fix nur an der Wurzel liesse das Wissen im Baum
   wieder verfallen -- par.3 hatte nur die Wurzel.
2. **Drei ruhende Stellen tragen die Begruendung mit dem blinden Fleck.** Woertlich am
   Code (`net_mcts.rs:4440-4443`): *"`dome_tile_pool` enthaelt an dieser Stelle ohnehin nur
   noch die ungezogenen (= wirklich verdeckten) Platten -- volles Mischen ist daher exakt
   richtig."* Gilt fuer nie gesehene Platten, ist falsch fuer selbst zurueckgelegte.
   Sie ruhen hinter `SHUFFLE_STACK_PEEK_IN_SEARCH = false`; wer den Schalter je wieder
   anfasst, muss sie mitziehen.

**Und die Grenze des Kanals:** er sieht nur, wo Information vernichtet wird -- nicht, wo
sie nie entsteht, und nicht, wo sie falsch bewertet wird. Dafuer par.11.

## par.11 DIE UEBRIGEN DREI KANAELE, eingetaktet (Nutzer 2026-09-09)

| Kanal | Was er kann | Wann |
| --- | --- | --- |
| **2 Sicht-Audit, zweite Achse** | `PREREG_stack_top_feature.md` fragt "sieht das Netz dasselbe wie ein Spieler?" und hat so acht Asymmetrien gefunden. Die zweite Achse fehlt: **was WEISS die Suche, und was vergisst sie zwischen zwei Zuegen?** | mit v27, dort registriert |
| **3 Orakel-Differential** | dieselbe Konfiguration gegen sich selbst, eine Seite OHNE Determinisierung. **Absichtliche Asymmetrie** -- entkommt der Symmetriefalle, an der Arena und Gating hier blind sind. Misst die GROESSENORDNUNG, entscheidet aber nicht ueber den Umbau (siehe unten) | Knopf baubar, sobald die Maschine frei ist |
| **4 Anomalie-Report** | listet aus den Self-Play-Logs Aktionen, die auffaellig oft vorkommen oder Punkte kosten, ohne messbar etwas zu bringen. 13 Stapelziehungen in einer Runde waeren dort oben gestanden, lange vor der Anlasspartie | Werkzeug baubar sofort, Lauf sobald die Maschine frei ist |

**Warum das Instrument ueberhaupt gebraucht wird** (und warum kein Elo-Wert es ersetzt):
Selfplay, Arena, Gating und die Offline-Metriken vergleichen zwei Agenten IM SELBEN
Weltmodell. Ein Fehler im geteilten Modell wirkt auf beide Seiten gleich und kuerzt sich
weg -- die Stapelblindheit kostet in jeder Arena exakt null Elo, bei jeder Partienzahl.
**Symmetrische Defekte sind fuer symmetrische Messung unsichtbar.** Das ist die
Irrtumskosten-Begruendung nach CLAUDE.md, mit benanntem Nutzniesser: diesem Umbau.

### Das Orakel-Differential ist ein MASSSTAB, kein Tor (Nutzer-Berichtigung 2026-09-09)

**Nutzer, woertlich:** *"beim Stapel-Umbau geht es meiner Meinung nach weniger ob es lohnt:
es ist einfach falsch implementiert und nicht vergleichbar mit der Sicht, die ein Mensch
hat. Das gehoert korrigiert."*

**Damit ist der Umbau nicht an eine Messung gebunden.** Ein frueherer Absatz an dieser
Stelle hat das Orakel-Differential als Abbruchkriterium vorregistriert ("liegt die
Obergrenze im Rauschen, wird der Umbau gestrichen") -- das widersprach par.8 derselben
Prereg, die den Umbau schon als Korrektheits-Fix eingeordnet hatte, und ist gestrichen.

**Die Praezedenz ist die Determinisierung selbst.** Sie wurde am 2026-07-20 mit genau
diesem Argument BEHALTEN, obwohl ihr Arena-Delta unklar war (`net_mcts.rs:968-977`,
woertlich: *"es geht nicht nur um gemessenen Vorteil, sondern auch um KORREKTHEIT: die
Suche soll kein Wissen nutzen, das ein echter Spieler nicht hat"*). Heute nimmt dieselbe
Funktion der Suche Wissen, das ein echter Spieler SEHR WOHL hat. Der Umbau kehrt den
Entscheid von damals nicht um, er vollendet ihn: dieselbe Regel, konsequent in beide
Richtungen angewandt.

**Wozu das Differential dann noch dient:** als Groessenordnung, nicht als Tor. Es sagt,
wieviel an dieser Information ueberhaupt haengt -- eine OBERGRENZE, denn das Orakel weiss
mehr, als ein Spieler je wissen kann. Das ist zweierlei wert: es priorisiert gegen die
anderen Straenge, und es gibt der Arena NACH dem Umbau einen Massstab, an dem ein flaches
Ergebnis lesbar wird (flach bei kleiner Obergrenze heisst etwas anderes als flach bei
grosser). Gebraucht wird dafuer ein Knopf, denn `DETERMINIZE_ROOT_HIDDEN_INFO` ist heute
eine Konstante (`net_mcts.rs:976`); Default AUS laesst das Bestandsverhalten unberuehrt,
danach `/mosaic-anchor-invariance`.

## par.12 DIE REFERENZ-PARTIE (Nutzer-Auftrag 2026-09-09)

**Nutzer:** *"als Referenz kannst das Log anfuehren. Das kannst bei Bedarf nachspielen und
dann laesst sich abschaetzen, wann/ob mit welchen Massnahmen sich das Netz anders
entscheidet."*

**Eingefroren, weil sie ab jetzt eine Rolle traegt**
([[feedback_freeze_when_it_becomes_a_reference]]): `static/log/` ist gitignoriert
(`.gitignore:50`), die Partie liegt deshalb als Kopie im Baum.

**Erweitert 2026-09-09 auf VIER Partien** (Nutzer nannte drei weitere). Alle vier tragen
`#a`-Zeilen, sind also exakt nachspielbar, und alle vier enthalten Stapelzuege.

| Datei in `evaluations/fixtures/` | sha256 (Kopf) | Zeilen | Stapelziehungen | Platten |
| --- | --- | --- | --- | --- |
| `game_20260904_194912_seed771522.log` | `d866a71a29ccd3e7` | 434 | 8 | 0, 6, 2 |
| `game_20260904_202338_seed180879.log` | `135b44e5bae419bc` | 458 | 28 | 6, 0, 5 |
| `game_20260905_224028_seed300512.log` | `b3a79cde6f5d4058` | 462 | 24 | 1, 0, 6 |
| `game_20260909_004553_seed876496.log` | `98c28a92881cd341` | 483 | 21 | 1, 5, 6 |

Die vollen Pruefsummen liegen als `<name>.sha256` daneben. Motor der letzten Partie: Wheel
vom 2026-09-07 (Weg B/C), Netz `v25-b01_brierbest`, Champion-Spec; die drei aelteren
stammen aus der v24-Aera.

**Warum genau diese Partie taugt:** sie ist exakt nachspielbar, nicht heuristisch. Seit
`PREREG_action_id_logging.md` traegt jede Aktion ihre ID im Log (`#a`-Zeilen), und
`tools/analyze_game_log.py` loest Stein-Zuege ueber diese ID auf statt aus der Prosa; nach
JEDER Aktion wird `log_since` gegen den Original-Abschnitt gekreuzt und bricht bei
Divergenz ab. Die Partie enthaelt zudem alle vier Stapelzuege in einem Stueck.

**Die Entscheidungsstellen** (Zeilen der eingefrorenen Kopie):

| Runde | Zeilen | Was dort geschah |
| --- | --- | --- |
| R1 | 37-50 | 13 Ziehungen, 12 zurueck, Reihenfolge im Log -- ab hier ist der Stapel dem Ziehenden bekannt |
| R2 | 135-137 | 2 Ziehungen, 1 zurueck |
| R3 | 246-251 | 5 Ziehungen, 4 zurueck |
| R4 | 369 | 1 Ziehung |

**Das Protokoll, vorregistriert:**

```
python -X utf8 -u tools/analyze_game_log.py   --log evaluations/fixtures/game_20260909_004553_seed876496.log   --model models/alphazero_v25-b01_brierbest.onnx --sims 400   --oracle-json evaluations/artifacts/replay_dome_stack_<STAND>.json
```

Gefahren wird er ZWEIMAL mit demselben Netz und denselben Seeds: einmal auf dem heutigen
Stand (`<STAND>` = `pre`), einmal nach dem Umbau (`post`). **Verglichen wird die
Entscheidung an den vier Stellen oben**, nicht die Partie -- gleiche Stellung, gleiches
Netz, nur ein anderes Weltmodell.

**Was der Vergleich zeigen soll und was nicht.** Er beantwortet die Frage des Nutzers:
*wann und mit welcher Massnahme entscheidet sich das Netz anders?* Er ist damit die
DIAGNOSTIK des Umbaus und ersetzt keine Arena -- eine einzelne Partie traegt keine
Staerkeaussage. Erwartung, vorab benannt: in R2 bis R4 faellt die Ziehtiefe, weil der
Stapel dort bereits bekannt ist; in R1 muss sie NICHT fallen (par.4b: der tiefe Erstzug
kauft Wissen und kann richtig sein).

**Zweiter Nutzen, der nichts kostet:** derselbe Aufruf mit `--no-oracle` ist ein
Regressionstest. Laeuft die Partie nach einer Engine-Aenderung nicht mehr byte-gleich
durch, hat die Aenderung Regelverhalten veraendert -- gemerkt an einer echten Partie statt
an einem Kunstzustand.

## par.13 EIN MUSTER UEBER ALLE VIER PARTIEN (Nutzer-Hypothese 2026-09-09)

**Nutzer:** *"da hast auch viele Kuppelzuege. Haengt vielleicht mit der Wertungsplatte
Spezialfliesen zusammen."* Nachgesehen -- und das Muster ist deutlicher als erwartet.

**GRUNDMENGE: 4 Mensch-gegen-KI-Partien aus `static/log`, EINHEIT: Punkte der Endwertung.**
n = 4, keine Korpus-Messung.

| Partie | Platten | Stapelziehungen | Spezialfelder Mensch | Spezialfelder KI | Endstand |
| --- | --- | --- | --- | --- | --- |
| `..._771522` | 0, 6, 2 | 8 | -6 | **-12** | 37 : 36 |
| `..._180879` | 6, 0, 5 | 28 | -6 | **-12** | 43 : 42 |
| `..._300512` | 1, 0, 6 | 24 | -9 | **-12** | 40 : 25 |
| `..._876496` | 1, 5, 6 | 21 | -6 | **-12** | 69 : 0 |

**Platte 6 ist in ALLEN VIER aktiv** (`scoring.rs:48`: *"Spezialfelder, -3 Pkt je leeres
Spezialfliesenfeld"*), und die KI kassiert **jedes Mal exakt -12**, also das Maximum von
vier offenen Feldern. Der Mensch liegt bei -6 oder -9. Vier von vier, gleicher Wert,
gleiche Richtung.

**Die Hypothese, ausdruecklich als solche markiert und NICHT gemessen:** die Platte macht
den Stapelzug zur Wild-gegen-Special-Lotterie. Die Rueckseite verraet den Typ, und ein
SPECIAL-Feld kostet am Ende -3, wenn es leer bleibt -- die KI zieht also tief, um Wild zu
bekommen, und endet trotzdem beim Maximalabzug. Genau fuer diese Frage existiert das
Merkmal `dome_wild_remaining_frac` (`serialize.rs:58-65`, Kommentar nennt die
"-3 je offenes Spezialfeld"-Platte als Anlass).

**Warum das hierher gehoert und nicht in eine eigene Prereg:** wenn die Hypothese traegt,
ist die Stapelblindheit teurer als bisher angenommen -- die Suche wuerfelt genau die
Information weg, die ueber diesen Posten entscheidet, und kauft sie in jeder Runde neu.
Der Zusammenhang ist damit ein Argument IN dieser Prereg, kein eigener Strang.

### par.13a NACHGEMESSEN ueber ALLE Mensch-Partien (2026-09-09, noch in derselben Nacht)

Der Nutzer wies darauf hin, dass die Logs vollstaendig unter `static/log/` liegen -- also
nicht vier Partien, sondern **23**. Reines Textparsen, keine Erzeugung, keine Engine.

**GRUNDMENGE: 23 Mensch-gegen-KI-Partien in `static/log/` (2026-08-18 bis 2026-09-09),
EINHEIT: Ziehungen je Partie, gezaehlt als Zeilen "vom Stapel gezogen".**

| | Partien | Ziehungen je Partie |
| --- | --- | --- |
| **ohne** Wertungsplatte 6 | 19 | 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 6, 6, 7, 8, 8 |
| **mit** Wertungsplatte 6 | 4 | **8, 21, 24, 28** |

**Die Trennung ist sauber:** keine einzige Partie ohne Platte 6 kommt ueber 8 Ziehungen;
drei der vier Partien mit Platte 6 liegen bei 21 bis 28. Median 4 gegen 22,5.

**Damit ist Pruefschritt 3 auf Mensch-Partien beantwortet: JA, die Ziehtiefe haengt an der
Platte.** Die Hypothese des Nutzers ist auf dieser Grundmenge beschreibend bestaetigt.

**Was das NICHT zeigt, und das bleibt offen:**

* **Nicht die Ursache.** Dass die Platte die Tiefe TREIBT, ist plausibel (Wild rettet, ein
  leeres Spezialfeld kostet -3), aber die vier Partien unterscheiden sich auch in den
  anderen zwei Platten und im Netz-Stand (die Alt-Partien vom August laufen auf frueheren
  Netzen). n = 4 auf der einen Seite.
* **Nicht, ob die Tiefe falsch ist.** Bei aktiver Platte 6 KANN tiefes Ziehen richtig sein.
  Falsch ist nur das Wiederholen in einen bereits bekannten Stapel hinein -- und das misst
  erst der Vergleich aus par.12.
* **Aber es verschiebt das Gewicht dieser Prereg:** die Pathologie sitzt nicht ueberall,
  sondern konzentriert in rund einem Sechstel der Partien -- dort dafuer heftig. Das
  Punkteniveau jener vier Partien liegt auffallend tief (37:36, 43:42, 40:25, 69:0 gegen
  sonst 70-80 : 45-60), und die KI nimmt in allen vieren den Maximalabzug von -12.

**Zu pruefen, wenn die Maschine frei ist** (keine Erzeugung noetig, alles liegt vor):

1. **Ist -12 wirklich das Maximum?** Vier leere Spezialfelder je Spieler, also Deckel bei
   -12 -- am Code nachsehen, nicht ableiten (`score_empty_special_fields`, `scoring.rs:33`).
2. **Gilt das ueber den Korpus?** Verteilung der Spezialfeld-Punkte je Seite in den
   Self-Play-Records, nicht nur in vier Mensch-Partien. Werkzeug steht:
   `tools/plate_points_from_arena.py` (Punkte je Kriterium).
3. **Haengt die Ziehtiefe an der Platte?** Ziehungen je Partie mit aktiver Platte 6 gegen
   ohne. Das ist die eigentliche Frage des Nutzers.

## par.12a PRE-LAUF GEFAHREN (2026-09-09, 13:27-13:32)

`tools/replay_dome_stack_pre.sh`, Netz `v25-b01_brierbest` bei 400 Sims, auf der
eingefrorenen Partie (sha256 vor dem Lesen geprueft). Artefakt:
`evaluations/artifacts/replay_dome_stack_pre.json` (130 bewertete Entscheidungen, davon
**21 Stapelzuege**), Bericht in `evaluations/game_analysis/`. Wanduhr 266 s.

**Der Befund an der R1-Serie** -- Rang des tatsaechlich gespielten Zuges in der
Bewertung des HEUTIGEN Netzes, plus dessen Q gegen den Wurzelwert:

| Ziehung | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Rang | 16 | 1 | 3 | 8 | 2 | **1** | **1** | **1** | **1** | **1** | **1** | **1** | **1** |
| Q(gespielt) | 0,580 | 0,652 | 0,639 | 0,568 | 0,583 | 0,596 | 0,634 | 0,635 | 0,627 | 0,629 | 0,637 | 0,640 | 0,640 |
| Wurzelwert | 0,608 | 0,627 | 0,634 | 0,581 | 0,569 | 0,560 | 0,567 | 0,565 | 0,567 | 0,565 | 0,563 | 0,565 | 0,568 |

**Ab der sechsten Ziehung ist "nochmal ziehen" durchgehend die Nummer eins**, mit einem
Q, das den Wurzelwert um rund 0,07 uebersteigt -- und zwar STABIL, ueber acht Zuege
hinweg. Genau das ist die vorhergesagte Signatur: nach dem Mischen sieht jede Ziehung
wieder aus wie ein frisches Los mit positivem Erwartungswert. Dass der Stapel zu diesem
Zeitpunkt bereits vollstaendig gesehen war, kann die Suche nicht wissen (par.3), und
kosten tut es nichts, weil der Punktestand auf 0 steht (par.9).

**Lesart, eng gehalten:** das ist EINE Partie und der Rang ist die Bewertung des heutigen
Netzes bei 400 Sims, nicht die Entscheidung, die im Spiel getroffen wurde. Als
Staerkeaussage taugt es nicht. Als BASISLINIE fuer den Vergleich nach dem Umbau ist es
genau richtig: dieselbe Stellung, dasselbe Netz, nur ein anderes Weltmodell -- faellt der
Rang der Wiederholungsziehung dann, hat der Umbau seine Wirkung; bleibt er bei 1, nicht.

## par.14 AUDIT 2026-09-09 (vor dem Bau; Befunde, die par.7 bis par.13 beruehren)

Nachgeprueft am Code, je Punkt mit Pruefstelle. Nichts davon aendert den Anlass (par.3
bleibt richtig: `net_mcts.rs:976` `DETERMINIZE_ROOT_HIDDEN_INFO = true`, `:987`
Vollmischung), aber vier Stellen der Prereg tragen Aussagen, die so nicht halten.

1. **Die Kauf-Seite der Null-Klammer hat keinen Eigentuemer.** par.9 verweist sie an
   `PREREG_score_clamp_incentive.md`; deren par.4 verweist sie hierher (par.4b), und
   par.4b formuliert nur eine Warnung. Dazu kommt: `apply_paid_cost`
   (`engine/src/board.rs:361-364`) bucht bei Kaeufen auf `score` UND `score_unclamped` nur
   den tatsaechlich bezahlten Betrag. Die Gratisziehungen des Anlassspiels (Ziehungen 6 bis
   13 bei Stand 0) tauchen damit in KEINER Differenz der beiden Zaehler auf. Wer sie messen
   will, braucht eine eigene Zaehlung (Ziehungen bei Stand 0 je Partie), und eine der beiden
   Preregs muss sie tragen. Vorschlag: hier, weil der Stapel hier modelliert wird.
2. **par.13 nennt "-12 = Maximum von vier offenen Feldern" als Befund, die Zahl ist
   unbelegt.** `score_empty_special_fields` (`engine/src/scoring.rs:771-775`) zaehlt ueber
   `collect_spaces` (`:804-814`) die leeren Spezialfelder ALLER gelegten Platten im
   3x3-Raster, mit -3 je Feld. Die Obergrenze ist also 3 mal die Zahl der Spezialfelder
   auf dem Brett, nicht 12. par.13a Punkt 1 stellt die Frage richtig; par.13 darf die
   Zahl bis dahin nicht als Befund fuehren.
3. **par.4 widerspricht einem registrierten Nutzer-Entscheid (berichtigt 2026-09-10;
   die erste Fassung dieses Punktes nannte es ein "Leck", das war falsch hergeleitet).**
   `game.rs:262-269` traegt den Entscheid vom 2026-08-09 im Kommentar: das Regelwerk
   laesst die Sichtbarkeit offen (`docs/engine_manual.md`, Abschnitt A: "the rest go back
   under the stack in any order you choose", ohne Aussage zur Sicht), und der Nutzer hat
   festgelegt, dass der Gegner die Platzierung UND die Rueckgabe-Reihenfolge SIEHT. Genau
   deshalb schreibt `game.rs:282-286` die Reihenfolge mit Kachel-ID ins Log, das Frontend
   zeigt sie an, und `tools/analyze_game_log.py:164` (Kategorie `DOME_RETURN_TO_STACK`)
   liest sie fuer das Replay. Par.4 modelliert die Reihenfolge dagegen als "offiziell NICHT
   bekannt". Eines von beiden muss weichen, und das ist ein Nutzer-Entscheid:
   (a) Entscheid vom 2026-08-09 bleibt: dann ist die Reihenfolge OEFFENTLICHE Information
   fuer beide Seiten, par.4 und die Bauvarianten par.7 sind darauf umzustellen (die
   Determinisierung darf die zurueckgelegten Platten dann fuer KEINEN Spieler mischen),
   und das Log ist korrekt. (b) Entscheid wird zurueckgenommen: dann muss die Zeile aus der
   Anzeige (und aus `game.log` der Claude-Partien) verschwinden, waehrend der Replayer sie
   weiter braucht; Bauform: Maschinenzeile nach dem Muster der `#a`-Zeilen
   (`serialize.rs:240-250` filtert sie aus der Anzeige) plus getrennte Ablage in
   `tools/claude_play.py`. Die vier Referenzpartien (par.12/13) wurden unter Lesart (a)
   gespielt.
   **ENTSCHIEDEN 2026-09-10 (Nutzer, woertlich): "die reihenfolge der zurueckgelegten
   kuppelplatten ist nur fuer den spieler sichtbar der sie auch erstellt."** Das ist
   Lesart (b) mit Praezisierung: der Ausfuehrende kennt seine Reihenfolge, der Gegner nicht;
   der Gegner sieht weiterhin die aufgedeckten Fronten der gezogenen Platten und die
   Platzierung. Damit gilt par.4 so, wie es steht, und der Entscheid vom 2026-08-09 in
   `game.rs:262-269` ist abgeloest. Folgen: sichtbare Logzeile nur noch mit der Anzahl,
   Replayer-Kompatibilitaet fuer Alt-Logs, `claude_play.py` trennt Anzeige- und
   Maschinenzeilen (Patch 2026-09-10 vorbereitet; Build, Anker-Invarianz und Rauchtest
   erst auf freier Maschine). Fuer die Informationsmengen (par.4) heisst das ausserdem:
   die vom GEGNER zurueckgelegten Platten sind ihm als MENGE bekannt (Fronten lagen offen),
   ihre Reihenfolge im Stapel nicht; die selbst zurueckgelegten sind in Reihenfolge bekannt.
4. **par.8 beschreibt Geplantes im Praesens:** ein "mitgefuehrter Wissensstand" in
   `tools/analyze_game_log.py` existiert nicht (Agentenbefund, Grep ueber
   bekannt/known/return_order: nur Prosa-Treffer; nicht unabhaengig nachgeprueft). Die Zahl
   ist baubar, weil die Reihenfolge mit IDs im Log steht, aber sie ist zu BAUEN. Ausserdem
   nennt par.8 fuer das gepaarte Gating weder n noch SPRT-Grenzen; "faellt auf nahe null"
   ist keine Schwelle. Beides vor dem PRE/POST-Vergleich festlegen.

Kleineres, ebenfalls aus dem Audit: par.3 zeigt auf `build_net_tree` bei 3952, die
aktive Determinisierung des Gumbel-Pfads liegt bei `net_mcts.rs:4371` (Funktion richtig,
Zeile nicht); par.4b sagt "Ziehungen 1 bis 4 bezahlt", im Log kostet auch Ziehung 5 einen
Punkt (Fixture Z.41, Agentenbefund); par.12a "130 bewertete Entscheidungen" sind 130
Zeilen, davon 99 mit `evaluated: true` (Agentenbefund am Artefakt); das Artefakt
`replay_dome_stack_pre.json` traegt keinen `laufzeit`-Block.

**Zeiger-Nachzug 2026-09-10 (nach dem Logzeilen-Patch):** `game.rs:262-269` (alter
Entscheid) ist jetzt der Kommentarblock ab `game.rs:263`, die Logzeile steht bei
`game.rs:285`, die Replayer-Regex bei `analyze_game_log.py:171`. Die Verweise in
par.3 und par.14 oben sind Stand vor dem Patch und werden nicht rueckwirkend umgeschrieben.

## par.15 VARIANTE A GEBAUT (2026-09-10, 16:05-16:25); POST-Lauf und A/B-Kante laufen

**Entscheid (Koordinator, unter dem Auftrag "Nach-v27-Programm starten"): A zuerst, B additiv
danach, falls A traegt.** Nahtbreite vor dem Schnitt gemessen: 144 Nennungen von
`dome_tile_pool` in 16 Dateien; Zieh-/Rueckgabestellen `game.rs` 183/280/571/984, aktive
Mischstellen `net_mcts.rs:987` und `round_transition_deep.rs:623`, drei ruhende hinter
`SHUFFLE_STACK_PEEK_IN_SEARCH`, Roundtrip-Neumischung `serialize.rs:1014`.

**Bauform** (Opus-Agent, gegengelesen): `GameState::dome_pool_known_blocks: Vec<KnownPoolBlock
{len, returner}>` beschreibt das SUFFIX des Stapels (aeltester Block zuerst); Pflege vor jedem
`remove(0)` (game.rs 186/584/998) und nach jeder Rueckgabe (game.rs 292, ein Block je
Rueckgabe). `determinize_dome_pool(state, viewer, rng)` (state.rs) mischt das unbekannte
Praefix, laesst den eigenen Block in Reihenfolge stehen und permutiert fremde Bloecke nur in
sich, exakt die Sicht aus par.4 mit dem Entscheid aus par.14 Punkt 3. Wurzel-Determinisierung
(`net_mcts.rs:996`) mit viewer = Suchender; `round_transition_deep.rs:634` mit viewer = None
(Label-/Bootstrap-Rollouts fuer beide Seiten: Blockgrenzen und -mengen bleiben, Reihenfolge in
jedem Block faellt; dokumentiert). Chip-Determinisierung unveraendert. JSON: nur im
exact-Pfad (`state_to_json_exact`, Referee/Golden-Probe), tolerant fuer Alt-Artefakte; das
Frontend-JSON traegt das Feld NICHT (keine viewer-abhaengige Sicht dort; Anzeige der eigenen
Blockgroessen waere ein eigener additiver Schnitt). Bestandsfall (keine Bloecke) byte-identisch
zum alten `shuffle`, als Test festgeschrieben. Mischstellen-Liste in
`docs/architecture_reference.md` nachgezogen, `MOSAIC_NUM_DETERMINIZATIONS`-Text auch.

**Tests:** 9 neue (40 Partien mit Konsistenzpruefung nach jeder Aktion; 200 Seeds je
Richtung fuer eigener Block identisch / fremder Block Permutation / Praefix Permutation /
Multimenge gleich; exact-Roundtrip), Suite 563 gruen + 1 erwartet rot: die
Netz-Paritaets-Fixture, weil die Suche sich absichtlich aendert (Kausalitaet per Schalter
belegt: mit Vollmischung alter Hash 9232a97d1267875e). Fixture neu erzeugt und frisch
geprueft: **5e3b1362ddc65fa6**. Wheel gebaut, **Anker-Drift GRUEN**
(`anchor_drift_live_wheel_20260910c.json`, 1.763 Schritte; `mcts.rs` mischt den Pool nicht).

**Laeuft seit 16:26:** POST-Lauf der Referenzpartie (par.12, gleiches Netz v25-b01 @400,
`replay_dome_stack_post.json`) und die Staerke-Kante nach par.8 in der einzigen sauberen Form:
Live-Engine MIT Umbau gegen das v27-b01-Artefakt OHNE Umbau (Wheel vom Vormittag), gleiches
Netz, `frozen_referee_match`, 150 Partien, Seed-Basis 20261060
(`dome_stack_ab_v27-b01_live_vs_artifact_s60.json`). Par.8 verlangt gepaartes Gating mit
Bloecken zu 5 und zwei Seeds; der Referee pairt nicht. Bei einem Ergebnis nahe 50 % folgt
ein zweiter Seed; das Verdikt "Korrektheits-Fix bleibt, Ruecklauf nicht" gilt.

**Nebenbefund des Agenten:** die "24 Mischstellen" in `docs/architecture_reference.md` sind
ein datierter Stand (2026-09-09); ein roher Grep ueber `.shuffle(|choose_multiple` liefert
heute 39 inklusive Testcode. Die Grundmenge der 24 ist nicht reproduziert.

### par.15a POST-Lauf war blind, erste A/B-Kante (2026-09-10, 16:30-17:15)

**POST-Lauf (par.12) byte-gleich zum PRE-Lauf, an allen 99 bewerteten Entscheidungen,
Rang und Q bis auf die dritte Stelle.** Das ist kein Nullbefund, sondern ein Messfehler im
Instrument: `analyze_game_log.evaluate_oracle` reicht das Frontend-JSON (`PyGame.state_json`,
Pool als MASKE) an `net_search_state_json`, und das rekonstruiert den Zustand ueber
`serialize::json_to_state` mit Neumischung des Pools (`serialize.rs:1010-1014`). Die
Wissensbloecke konnten dort per Konstruktion nie ankommen; die verdeckte Reihenfolge ebenso
wenig. Der PRE-Lauf hatte also nie den Stapel gesehen, den die Partie hatte. Behoben
(ungebaut, wartet auf freie Maschine): `PyGame::state_json_exact` (py.rs, exakte Reihenfolgen
plus Bloecke), `net_search_state_json` rekonstruiert bei vorhandenen `*_exact`-Feldern exakt
(lib.rs), `analyze_game_log.py` nutzt es, Feld `state_exact` im Orakel-Record. Danach
PRE und POST beide auf dem exakten Zustand neu fahren (der alte PRE-Lauf bleibt als
Artefakt liegen, wird aber nicht mehr verglichen).

**A/B-Kante, Seed-Basis 20261060, 150 Partien, Referee** (Live-Engine MIT Variante A gegen
das v27-b01-Artefakt OHNE, gleiches Netz, Handshake gruen, Golden-Selbsttest 10/10,
Erstspieler 75/75, 2.515 s): **83:67 fuer die Live-Seite** (55,3 %), zweiseitig binomial
p 0,22. Kein Ruecklauf, nicht signifikant; zweiter Seed (20261300) laeuft seit 17:12.

### par.15b A/B-Kante komplett (2026-09-10, 16:30-17:57): kein Ruecklauf, Richtung positiv

| Seed-Basis | Live MIT Variante A : Artefakt OHNE | Anteil | zweiseitig binomial p |
| --- | --- | --- | --- |
| 20261060 | 83:67 | 0,553 | 0,22 |
| 20261300 | 82:68 | 0,547 | 0,29 |
| **gepoolt** | **165:135** | **0,550** | **0,094** |

Gleiches Netz `v27-b01_brierbest` @400 auf beiden Seiten, Champion-Spec, Referee mit dem
Wheel des Artefakts vom 2026-09-10 10:10 (ohne Umbau) gegen die Live-Engine (mit Umbau),
Handshake gruen, Golden-Selbsttest 10/10 in beiden Laeufen, Erstspieler je 75/75, je rund
43 min auf 6 Prozessen. Einheit: Partien, ungepaart (der Referee pairt nicht; par.8 hatte
gepaartes Gating mit Bloecken zu 5 vorgesehen, das geht mit zwei Engines in einem Prozess
nicht). **Verdikt nach par.8: Korrektheits-Fix bleibt; kein Ruecklauf, beide Seeds vorn,
gepoolt 55 % bei p 0,09.** Die Staerkefrage ist damit nicht entschieden, aber sie war
nicht das Kriterium. Die eigentliche Erwartung (Wiederholungsziehung in bekannten Stapelteil
faellt) misst der exakte POST-Lauf (par.15a); Variante B (Merkmale) bleibt vorgemerkt.

### par.15c PRE/POST auf dem EXAKTEN Zustand (2026-09-10, 18:01-18:11): Wissen allein bewegt die Ziehungen kaum

Instrument repariert (par.15a): `PyGame::state_json_exact`, exakte Rekonstruktion im
Orakel-Einstieg, Knopf `MOSAIC_DOME_POOL_KNOWLEDGE` (=0 Vollmischung) fuer den PRE-Lauf auf
demselben Wheel; Wheel gebaut, Anker-Drift GRUEN (`anchor_drift_live_wheel_20260910d.json`),
Suite 564 gruen. Beide Laeufe: Referenzpartie, Netz `v25-b01_brierbest` @400, exakter Zustand
in 98/98 bewerteten Entscheidungen (`replay_dome_stack_pre_exact.json`,
`replay_dome_stack_post_exact.json`, Vergleich `dome_stack_pre_post_compare.json`, Werkzeug
`tools/probes/dome_stack_pre_post_compare.py`).

| Stelle | Rang PRE / POST | Q PRE / POST | Wurzel PRE / POST |
| --- | --- | --- | --- |
| R1, Ziehungen 1-13 (turn 11-23) | identisch (13, 1, 3, 1, 2, 1 x 8) | identisch | identisch |
| R2, Spieler 1 zieht 2 (turn 46-47) | identisch (16, 3) | identisch | identisch |
| R3, KI zieht 5 in den EIGENEN bekannten Block (turn 75-79) | 2, 1, 1, **5 -> 6**, 5 | 0,306 / 0,306; **0,329 -> 0,308**; 0,318 -> 0,314; 0,295 -> 0,290; 0,288 / 0,288 | 0,283 -> 0,278; 0,268 -> 0,263; 0,265 -> 0,259; 0,295 -> 0,290; 0,270 / 0,270 |
| R4 (turn 110-111) | identisch | identisch | identisch |

31 von 98 Entscheidungen aendern sich irgendwo in Rang oder Q (die uebrigen Aenderungen
liegen ausserhalb der Stapelzuege, nach R3). Rang-1-Anteil der Stapelzuege 15/25 in beiden
Laeufen, mittlerer Rang 2,80 gegen 2,84.

**Lesart.** R1 und R2 sind per Konstruktion gleich: in R1 gibt es noch keinen Block, in R2
ist der ganze Stapel EIN fremder Block (Permutation in sich = Vollmischung). Der einzige
Ort, an dem Variante A etwas wissen kann, ist R3: die KI zieht fuenfmal in den Stapel, dessen
Oberseite ihr eigener Rueckgabe-Block aus R1 ist. Dort sinkt der Wert des Weiterziehens um
0,005 bis 0,02 und ein Rang rutscht um eins; die Ziehungen 2 und 3 bleiben Rang 1. **Die
vorregistrierte Erwartung aus par.8 (Wiederholungsziehung in bekannten Stapelteil "faellt auf
nahe null") tritt an dieser Partie NICHT ein.** Das Wissen ist jetzt in der Suche, aber die
Suche haelt das Ziehen trotzdem fuer richtig; ob wegen des Preises (par.4b: Ziehen kauft
die beste Platte JETZT, in R3 bezahlt die KI von 6 auf 1) oder weil der Value-Kopf den
Vorteil einer bekannten Reihenfolge nicht sieht (er hat kein Merkmal dafuer, Variante B),
trennt diese eine Partie nicht. n = 1 Partie, 5 Entscheidungen im Wirkbereich.

**Folgen.** (1) Der Korrektheits-Fix bleibt (par.8, A/B ohne Ruecklauf, par.15b). (2) Die
Diagnostik aus par.8 braucht eine breitere Grundmenge: dieselbe Messung ueber die 30
Mensch-Logs und eine Stichprobe Self-Play-Partien, gezaehlt als "Ziehung, waehrend die
Oberseite zum eigenen Block gehoert" gegen den Wissensstand aus `dome_pool_known_blocks`
(Werkzeug fehlt noch, par.14 Punkt 4). (3) Variante B (Merkmale: Groesse und Zusammensetzung
des eigenen Blocks) ist der naechste Hebel, damit die POLICY das Wissen nutzt, nicht nur die
Suche; Bau erst nach (2). (4) Kopplung zur Null-Klammer (`score_clamp` par.10): die
Gratis-Ziehungen bei Stand 0 sind die andere Haelfte derselben Frage.

### par.15d VORBEHALT zur Referenzpartie (gefunden 2026-09-10, 18:20)

Die Referenzpartie (par.12, 2026-09-09 00:45, KI `v25-b01_brierbest` im Browser) wurde sehr
wahrscheinlich OHNE die Champion-Spec gespielt: `server.py` las die Spec nur unter
`models/<name>.spec.json`, die es seit dem Einfrieren nicht gibt, und fiel still auf die
Env-Defaults zurueck (Huelle aus, hull_form 1, special_row6_w 0). Die Log-Koepfe tragen keine
Knoepfe, ein Beleg in beide Richtungen fehlt. Fuer die PRE/POST-Laeufe hier ist das
zweitrangig (beide bewerten dieselbe Partie mit demselben Netz), fuer die Lesart der
13er-Ziehserie nicht: sie stammt von einem Champion ohne seine Suchknoepfe. Die naechsten
Referenzpartien (Claude-Partien, Mensch-Partien) laufen mit dem Rueckfall auf das Artefakt.

### par.15e DIAGNOSTIK auf 300 Partien (2026-09-10, 19:00): Ziehungen in den eigenen Block STEIGEN mit Variante A

Werkzeug `tools/probes/dome_stack_known_block_draw_probe.py` (Replay mit dem heutigen Wheel,
Zustand VOR jeder Stapelziehung aus `state_json_exact`, Klassifikation der obersten
Pool-Position: unbekanntes Praefix / eigener Block / fremder Block; Konsistenz gegen die
`📦`-Zeilen 0 Abweichungen in 731 Partien). Artefakte
`dome_stack_known_block_draws_{ab_s60,ab_s1300,gating_s35,human}.json`.

| Grundmenge | Seite | Partien | Ziehungen | Anteil eigener Block | eigener Block je Partie | davon bei Stand 0 |
| --- | --- | --- | --- | --- | --- | --- |
| A/B s60 | Live MIT A | 150 | 1.192 | **0,271** | 2,15 | 214 / 323 |
| A/B s60 | Artefakt OHNE | 150 | 1.073 | 0,189 | 1,35 | 155 / 203 |
| A/B s1300 | Live MIT A | 149 | 1.173 | **0,276** | 2,17 | 215 / 324 |
| A/B s1300 | Artefakt OHNE | 149 | 1.140 | 0,209 | 1,60 | 163 / 238 |
| Tor 1 s35 (beide OHNE) | v27-b01 / v26-b01 | 394 | | 0,214 / 0,221 | 1,45 / 1,76 | |
| Mensch-Logs | KI / Mensch | 30 | 159 / 67 | 0,277 / 0,015 | 1,47 / 0,03 | alle 59 KI-Ziehungen bei 0 / keine |

**Gepaart je Partie (dieselbe Partie, beide Seiten), gepoolt ueber 299 Partien: Live minus
Artefakt = +0,689 Ziehungen in den eigenen Block je Partie, 95 %-KI [-0,009; +1,387],
Vorzeichentest +70 / -48 (p rund 0,05).** Einheit Ziehungen je Partie und Seite, nachgerechnet
am Artefakt. Runde 1 ist per Konstruktion frei von eigenen Bloecken; die Masse liegt in R2 (Live
s60: 211 von 520 Ziehungen), R3 und R4.

**Antwort auf par.8: die vorregistrierte Richtung tritt NICHT ein, die Zahl steigt.** Die Suche
kennt jetzt ihren Block und zieht eher OEFTER hinein. Der groesste Posten sind Gratis-Ziehungen
bei Stand 0 (zwei Drittel der eigenen-Block-Ziehungen der Live-Seite), also die Kaufseite der
Null-Klammer (`score_clamp` par.10). Lesart nach par.4b: Wissen ist ein Gut, und wenn es
nichts kostet, kauft die Suche es. Das ist kein Fehler des Umbaus (Korrektheits-Fix bleibt,
A/B ohne Ruecklauf), sondern zeigt, dass par.8 die falsche Groesse vorregistriert hatte: nicht
"Ziehungen in Bekanntes fallen", sondern "Ziehungen, die nichts Neues bringen UND etwas
kosten, fallen". Bei Stand 0 kosten sie nichts. Die Diagnostik trennt weiterhin nicht, ob die
Ziehungen bei positivem Stand richtig sind (Value) oder ob dem Kopf das Merkmal fehlt (B).

**Folgen fuer das Programm:** (1) `score_clamp` Stufe 1 rueckt VOR Variante B: solange
Ziehungen bei 0 gratis sind, misst jede Merkmalsaenderung gegen einen Anreiz, der nicht der
des Spiels ist (Nutzer-Frage: Regel oder Nutzenterm, `score_clamp` par.6). (2) par.8 ist um
die Groesse "Ziehungen in eigenen Block bei positivem Stand je Partie" zu ergaenzen; heute
Live 109 / 109 gegen Artefakt 48 / 75 (s60 / s1300, aus den Tabellen oben abgeleitet). Auch
die steigt, also bleibt die Frage an den Value-Kopf offen. (3) Ungeprueft: ob die Live-Seite
der A/B-Artefakte wirklich mit dem Knopf AN lief (kein Knopf-Feld im Artefakt; folgt aus dem
Wheel-Stand 16:24, der den Knopf noch nicht hatte und Variante A fest AN), und 9 Partien mit
Replay-Divergenz (Chip-Vollendung), nicht auf Verzerrung geprueft.

### par.15f Regelentscheid und Neufassung der Diagnostik (Nutzer 2026-09-10, 19:15)

Nutzer: Ziehen bei Stand 0 bleibt gratis und legal (Regelbuch S.4 und S.9, `score_clamp`
par.11). Damit ist der Anstieg aus par.15e regelkonformes Verhalten: die Suche kauft Wissen,
wenn es nichts kostet. **Die Diagnostik aus par.8 wird ersetzt** durch "Ziehungen in den
eigenen bekannten Block bei POSITIVEM Stand je Partie" (kosten 1 Punkt und bringen keine neue
Information ueber die Reihenfolge). Aus par.15e abgeleitet: Live 109 / 109 (s60 / s1300)
gegen Artefakt 48 / 75, also je Partie 0,73 / 0,73 gegen 0,32 / 0,50; auch diese Zahl steigt
mit A. Offen bleibt, ob das der Value-Kopf richtig bewertet (die Ziehung kauft die beste
Platte JETZT, par.4b) oder ob ihm das Merkmal fehlt. Das ist die Frage an Variante B:
Merkmale fuer den eigenen Block (Groesse, Zusammensetzung), Training, dann dieselbe Sonde
auf einem A/B-Lauf B gegen A. Kosten wie ein Arm (Training rund 1,5 h, Gating rund 1,5 h,
Sonde Minuten).

### par.15g Eine Browser-Partie mit Spec (2026-09-10, 22:56, KI v27-b01, Nutzer-Frage "mehr gezogen als notwendig?")

`static/log/game_20260910_225625_seed576088.log`, Sonde aus par.15e auf dieser einen Partie
(`dome_stack_known_block_draws_human_20260910_2256.json`, n = 1 Partie, illustrativ):

| Runde | Ziehungen der KI | Klassifikation | Kosten |
| --- | --- | --- | --- |
| R2 | 9 (Stand 5 -> 0) | 9 x unbekanntes Praefix | 5 Punkte, Ziehungen 6-9 gratis |
| R3 | 5 (Stand 16 -> 11) | **5 x eigener Block** | 5 Punkte |
| R4 | 1 | 1 x eigener Block | 1 Punkt |

Nach der R2-Serie war der ganze Stapel ihr eigener Block (9 gezogen, 8 zurueckgelegt, kein
unbekanntes Praefix mehr). In R3 zog sie fuenf Platten, deren Identitaet und Reihenfolge sie
kannte: das ist keine Informationssuche, sondern der Weg zu einer bekannten Platte an
Position 5 (ziehen geht nur von oben, zurueck gehen die vier anderen), bezahlt mit fuenf
Punkten statt einer Auslage-Platte gratis. In R4 dasselbe fuer die oberste Platte fuer einen
Punkt. Variante A wirkt also wie gebaut: die Suche kennt die Reihenfolge und plant die
Ziehtiefe danach; keine Ziehung ueber das Ziel hinaus. Ob fuenf Punkte fuer diese Platte
richtig waren, ist die Value-Frage (par.15f, Variante B); die Partie ging 72:81 verloren,
Mensch zog einmal.

### Nachtrag 2026-09-11 (Audit-Querlesung): Null-Klammer entschieden, Variante B gebaut und in Messung

Zwei Punkte aus par.15f sind seither weitergezogen, standen aber nur in anderen Preregs:

1. **Null-Klammer.** Der Vorrang "`score_clamp` Stufe 1 VOR Variante B" (par.15e Folge 1) ist
   erledigt, aber nicht als Bau: `PREREG_score_clamp_incentive.md` steht auf ENTSCHIEDEN --
   Nutzer-Entscheid 2026-09-10, Ziehen bei Stand 0 bleibt gratis und legal (Regelbuch S.4/S.9),
   die Strafseite ist mit 0,5 Punkten je Partie zu klein fuer einen Arm. Der Anreiz, gegen den
   Variante B gemessen wird, ist damit der des Spiels.
2. **Variante B gebaut (2026-09-11, 00:15-00:50).** Elf Werte an den Indizes 744..754 (Praefix,
   eigener Block nach Laenge/Spezial/Wild, Typen der obersten vier Positionen, fremde Bloecke),
   beide Rust-Pfade plus Python-Zwilling, INPUT_SIZE 744 -> 755, Kontrakt-Hash
   20b442a8164f748d -> c65768636c0560a7 (kuenftige Anker-Kanten gegen v25-v27 laufen Cross-Aera).
   Registriert in `PREREG_v28_window.md` par.9; Training `v28-b02` durch (ebd. par.9, Nachtrag
   14:37-16:52; Offline-Metrik unbewegt, Brier-Kurve auf der von b01), Tor 1 b02 gegen b01 seit
   16:52 in Messung. Die Sonde aus par.15e auf einem A/B-Lauf B gegen A (par.15f) steht noch aus.

## par.15h VARIANTE B GEMESSEN (2026-09-11, 16:52-19:44): NULLBEFUND

Arm `v28-b02` (elf Merkmale 744..754 aus `dome_pool_view`, Rezept sonst wie `v28-b01`, Warmstart
mit null-initialisierten Spalten, Training in `PREREG_v28_window.md` par.9) gegen `v28-b01` im
gepaarten Gating: 207:193 und 209:191, beide Seeds am Deckel ohne SPRT-Entscheid, McNemar p 0,52
und 0,42, Elo 1461 [1403; 1521] gegen 1447 [1395; 1500]. Die vorregistrierte Diagnostik (par.15f:
Ziehungen in den eigenen bekannten Block bei positivem Stand) zeigt b02 mit 0,57 und 0,63 je
Partie gegen 0,53 und 0,55 bei b01, also eher mehr, bei gleicher Staerke. Lesart nach par.15f:
das Merkmal traegt nicht messbar; ob der Value-Kopf die bekannten Ziehungen richtig bewertet,
bleibt offen, und par.8 (Ziehsucht) ist durch Variante B NICHT behoben. Variante A bleibt der
Korrektheitsfix; die Kanaele bleiben aus Kompatibilitaet im Vektor. Naechste Adresse fuer die
Ziehsucht: die Stopp-Regel und die Peek-Bewertung (`PREREG_stack_draw_reservation_rule.md`
par.7, `PREREG_chance_nodes.md` Teil B1, v29-Begleitprogramm) und die Ziehsucht-Sonde
(`PREREG_claude_play_interface.md` par.9). Zahlen: `PREREG_v28_window.md` par.10.
