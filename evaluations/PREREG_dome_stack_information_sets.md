<!-- STATUS: OFFEN | Frage: Wie wird das Wissen ueber den Kuppelstapel je Spieler modelliert, sodass die Suche weder Orakelwissen hat noch ihr EIGENES Wissen vergisst? | Beleg: nichts gebaut, nichts gemessen. Anlass am Log geprueft (game_20260909_004553_seed876496: 13 Ziehungen in R1, danach 2/5/1 in R2-R4). Ursache am Code geprueft: net_mcts.rs:3952 mischt bei JEDER Suche den ganzen dome_tile_pool (determinize_hidden_information), waehrend die Rueckgabe-Reihenfolge in game.rs:278 bewusst gewaehlt wird. Regellage vom Nutzer 2026-09-09 (par.4). Offen: Zeitfenster (Kollision mit dem Einfrieren v25-v27, par.6) und Bauvariante. -->

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
| Die Suche wuerfelt sie weg | `build_net_tree` ruft an der WURZEL JEDER Suche `determinize_hidden_information`, dort `state.dome_tile_pool.shuffle(rng)` | `engine/src/net_mcts.rs:3952`, `:986` |
| Der Schalter ist bewusst an | `DETERMINIZE_ROOT_HIDDEN_INFO = true`, Nutzer-Entscheid 2026-07-20, Begruendung KORREKTHEIT (kein Orakelwissen) | `engine/src/net_mcts.rs:976` |
| Das Netz sieht den Stapel ohnehin kaum | nur `dome_wild_remaining_frac` und `dome_stack_count`; `dome_stack_top_type` steht in der Serialisierung, NICHT im Merkmalsvektor | `PREREG_stack_top_feature.md` par.3, `PREREG_stack_draw_reservation_rule.md` par.2 |

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

1. **Einen Wissensstand JE SPIELER ueber den Stapel** (Positionsblock -> bekannte Menge,
   fuer den Ziehenden zusaetzlich die Reihenfolge). Heute gibt es einen einzigen wahren
   Stapel und eine Determinisierung, die ihn ganz mischt.
2. **Eine Determinisierung, die nur den UNBEKANNTEN Teil mischt** -- aus Sicht des Spielers
   am Zug. Ein Block mit bekannter Menge, aber unbekannter Reihenfolge wird INNERHALB des
   Blocks permutiert, nicht mit dem Rest vermengt.
3. **Merkmale, die dem Netz das Bekannte zeigen.** Ohne das kann nur eine handgeschriebene
   Politik den Vorteil nutzen (par.3, letzte Zeile).

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

**Zu entscheiden (Nutzer):** ob v27 dafuer geoeffnet wird -- der Nutzer hat den Brocken
ausdruecklich fuer v27 benannt -- oder ob er nach v27 faellt, wenn das stationaere Fenster
einmal sauber durchgelaufen ist. **Diese Prereg trifft die Entscheidung nicht.** Sie haelt
nur fest, dass der Widerspruch existiert und beim Start beantwortet sein muss; die Linie
ungeprueft weiterzuschreiben ist genau der Fehler, gegen den die Rueckwaerts-Pruefung in
CLAUDE.md steht.

## par.7 BAUVARIANTEN (Vorschlag, nicht entschieden)

**A) Bekannter Block bleibt bekannt (kleinster Schnitt).** Der Zustand bekommt je Spieler
einen Marker "die untersten n Positionen sind mir bekannt" plus die Sicht darauf (Menge
oder Reihenfolge). `determinize_hidden_information` mischt nur noch den Rest und permutiert
den Block getrennt. Kein neues Merkmal, kein Netz-Umbau. Erwartete Wirkung: die Suche zieht
nicht ein zweites Mal fuer Wissen, das sie hat.

**B) A plus Merkmale.** Zusaetzlich lernt das Netz, was bekannt ist (Groesse des bekannten
Blocks, dessen Wild-Anteil, `dome_stack_top_type`). Erst damit kann die POLICY den Vorteil
nutzen statt nur die Suche. Additiv nach der 2D-Encoder-Regel, Alt-ONNX muessen spielbar
bleiben.

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
