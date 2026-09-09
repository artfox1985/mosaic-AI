<!-- STATUS: OFFEN | Frage: Wie wird das Wissen ueber den Kuppelstapel je Spieler modelliert, sodass die Suche weder Orakelwissen hat noch ihr EIGENES Wissen vergisst? | Beleg: nichts gebaut. Ursache am Code geprueft: die Suche mischt den ganzen dome_tile_pool und vergisst damit die Rueckgabe-Reihenfolge, die sie selbst gewaehlt hat (net_mcts.rs:987, game.rs:278). Naht-Audit gefahren: ZWEI aktive Mischstellen (par.10). Ueber 23 Mensch-Partien gemessen: die Ziehtiefe haengt an Wertungsplatte 6 -- Median 4 ohne, 22,5 mit (par.13a). Drei Wissensstufen und Regellage: par.4/par.5. KORREKTHEITS-Fix, haengt nicht an einer Messung (Nutzer 2026-09-09). Start: nach dem Arm v27-b01 (par.6). Offen: Bauvariante. -->

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

