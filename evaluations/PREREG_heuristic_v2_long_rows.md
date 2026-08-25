<!-- STATUS: OFFEN | Frage: Kann ein ZWEITER Heuristik-Lehrer, dessen Bewertung die Musterreihen sieht, langes-Reihen-Spiel ueberhaupt erst erzeugen -- und laesst er sich neben den eingefrorenen Elo-Anker stellen, ohne ihn anzufassen? | Beleg: JA, BELEGT (par.10.1, 2026-08-25, 407 Kampagnen-Seeds je Arm gegen Champion@400). Die Prio-Leiter des Nutzers als Routing-Huelle (HeuristikVariante::V2Huelle) schlaegt v1 UND das alte v2: Siegquote 0,373 gegen 0,256 und 0,128, volle Spalten 0,798 gegen 0,086 und 0,302 (Netz selbst 0,106), Marge -5,5 gegen -12,2 und -19,4, Strafpunkte 13,6 gegen 19,3, Vollendungsquote 0,717; gepaart +0,700 volle Spalten (t=+13,73 auf 16 Bloecken). Der Tausch Faehigkeit-gegen-Niveau, den v2 in par.5.3 machen musste, ist damit AUFGEHOBEN, und die Voraussetzung von par.3b (Korpus mit Dreiecksform) ist erstmals erfuellbar. Preis: volle Zeilen 0,432 auf 0,216, echte Verschiebung und kein Aufbau-Artefakt. Der Durchbruch kam durchgehend vom ROUTING, nie von einem Bewertungsterm: Ablationen (par.8.6) trennen Struktur (Zielkarte) von Staerke (lineare Terme), und zwei gerechnete Punktekarten als Routing-Ziel sind negativ (par.9.1/9.2) -- eine additive Punktekarte ist ein BREITEN-Signal, volle Spalten brauchen FOKUS. Paritaets-Hash 8c6684ff haelt, Suite 520/0. OFFEN: par.11 (rundenabhaengige Spalten-Gewichte, GEBAUT, ungemessen), par.12 (Vollendbarkeit als Filter, registriert, ungebaut), par.5.4 Korpus und Training, Self-Play-Einstieg. par.3b ENTSCHEID: die Abkling-Kurve laeuft ueber die RUNDENNUMMER. -->

# Prereg: Heuristik v2 mit musterreihen-sichtigem Fortschritt

**Status: ENTWURF. Nichts gebaut. Alle par.6-Entscheide offen.**

Diese Prereg entsteht aus der Nutzer-Frage vom 2026-08-24 ("ist es das
richtige Netz und was muessen wir tun damit es lernbar ist und auch gelernt
wird") und der Nutzer-Vorgabe, eine Heuristik v2 als **zusaetzlichen** Anker
zu bauen, nicht als Ersatz.

## par.1 Anlass: die Luecke sitzt am Entscheidungspunkt

Alle Stellen in dieser Sitzung an der Quelle geprueft.

| Signal | sieht `pattern_lines`? | Richtung |
| --- | --- | --- |
| `wertung_progress` (Plattenfortschritt) | **nein**, nur `dome_slots` (`scoring.rs:876-882`) | keine: innerhalb einer Runde fuer jeden Drafting-Zug gleich |
| `projected_unplaceable_penalty` | **ja** (`round_end.rs:116-120`) | **gegen** lange Reihen |
| Tiling-Solver-Score | Endstand der Tiling-Phase, nicht der Zwischenstand | keine Lenkung der Reihenwahl |

`player_total` (`mcts.rs:80-84`) setzt sich aus genau diesen drei Teilen
zusammen. **Die Bewertung des Lehrers enthaelt damit einen Grund, lange
Musterreihen zu meiden, und keinen, sie zu bauen.** Der Befund ist nicht neu
erschlossen, sondern steht seit dem Injektions-Versuch woertlich im Code
(`net_mcts.rs:1456-1461`): "`wertung_progress` liest nur das Kuppelraster und
ist deshalb innerhalb einer Runde fuer JEDEN Drafting-Zug gleich -- es kann
die Wahl gar nicht lenken".

Dass weder Lehrer noch Schueler lange Reihen vollendet, ist damit keine
offene Frage mehr, sondern die direkte Folge dieser Luecke.

**Zwei bereits entschiedene Negative derselben Klasse** zeigen, dass der
Suchweg ausgereizt ist und der Eingriff eine Ebene tiefer gehoert:

- `PREREG_scoring_plate_injection.md`: ENTSCHIEDEN NEGATIV. Sweep ueber
  w = 0,03 / 0,1 / 0,3 / 1,0 (30-facher Dosisbereich), Vertikale Reihen
  bewegten sich 0,70 auf 1,05 Plattenpunkte.
- `PREREG_long_row_payoff.md` B1: ENTSCHIEDEN NEGATIV. Die Initiierung liess
  sich erzwingen (+0,310 je Partie, t=+7,57), die Staerke fiel um 14,5 pp,
  und die Vollendungsquote lag in BEIDEN Armen bei nur ~0,53.

B1 sah die Musterreihen, aber als **Stufenfunktion 0 auf 1**. Es belohnte das
Anfangen, nicht das Vorankommen -- deshalb kamen mehr Starts und keine
bessere Fuehrung. Das ist die Lehre, auf der par.3 aufsetzt.

**Diese beiden Negative sprechen NICHT gegen einen Term in der HEURISTIK
(Nutzer-Einwand 2026-08-24, und er trifft).** Beide Fehlschlaege sitzen am
NETZ-Blatt, und dort greift ein Mechanismus, den die Heuristik nicht hat:
**"Priors kommen IMMER vom Netz"** (`net_mcts.rs:57`) -- ein Shaping-Term
bewegt dort nur den Blattwert, waehrend die Zugreihenfolge aus dem trainierten
Prior kommt. Schlaegt der Prior die Initiierung langer Reihen praktisch nie
vor (gemessen: 0,32 Prozent Besuchsanteil), hat ein Blatt-Anstupser fast
nichts, woran er ansetzen kann.

Die Heuristik hat keinen konkurrierenden Prior. Ihr Verhalten IST ihre
Bewertung: `player_total` (`mcts.rs:80-84`) ist die einzige Quelle der
Zugwahl. Ein Term dort **steuert**, statt zu stupsen. Formal heisst beides
"ein Term in der Bewertung", mechanisch ist es nicht dieselbe Klasse
Eingriff -- und genau deshalb ist der Lehrer der richtige Ort.

## par.2 Zahlenstand, gegen den v2 sich messen muss

Aus `evaluations/long_row_init_arena_eval.json` (814 gepaarte Partien,
Champion beidseitig, 400 Sims):

| Groesse | Wert |
| --- | --- |
| Spalten je Partie bei >= 4 von 6 | **2,0** |
| volle Spalten je Partie | **0,10 bis 0,14** |
| maximale Spaltenhoehe | 4,65 bis 4,72 |
| Vollendungsquote langer Musterreihen | **0,53** |
| k1-Rate (Vertikale Reihen getroffen) | 13,8 Prozent, 0,99 Punkte je k1-aktiver Partie |

Zwei Spalten je Partie stehen kurz vor der Vollendung, ein Zehntel wird
fertig. Musterreihen-Kapazitaet ist `row_index + 1` (`board.rs:31-33`), die
langen Reihen fassen also 5 und 6 Fliesen.

**WARNUNG zur Lesart dieser Zahlen (Nutzer-Ruege 2026-08-24, vierter Vorfall
derselben Klasse):** sie stammen aus Partien von Netzen, die lange Reihen
nachweislich nicht koennen. Als NIVEAU oder Zielprofil sind sie **wertlos** --
sie messen die Unfaehigkeit des Erzeugers, nicht die Struktur des Spiels.
Belastbar sind sie nur als **Ist-Zustand** und als **gepaarte Differenz**
(dort steht dasselbe unfaehige Netz auf beiden Seiten). Dasselbe gilt fuer
`docs/domain_knowledge.md` §1 (Durchsatz je Musterreihe, gemessen auf
`selfplay_v20wdl_*`): als Beschreibung des Status quo brauchbar, als Referenz
nicht.

**Folge: die einzige zulaessige Referenz ist ANALYTISCH.** Solange kein Agent
existiert, der lange Reihen kann, muss das Zielprofil aus der Versorgung
gerechnet werden (65 Normalfliesen in 5 Farben, 4 kleine Fabriken mit je 4
Sonnenseiten-Fliesen plus eine grosse mit 5, Zug = alle Fliesen EINER Farbe
von einer Sonnenseite, `docs/engine_manual.md:26-35` und Zug B ebd.:93).
Das ist eine Versorgungs-SCHRANKE, nicht das Optimum -- das haengt an der
Politik -- aber es ist die einzige Zahl, die nicht am Ist-Zustand geeicht ist.

### ENTSCHIEDEN (2026-08-24): der Lehrer kann es auch nicht

`tools/run_longrow_teacher_arena.sh`, Netz@400 gegen Heuristik@150, 407
Kampagnen-Seeds, Artefakt `paired_arena_env_netvheur_longrow.json`.

| | Vollendungsquote R5/6 | volle Spalten je Partie |
| --- | --- | --- |
| Netz | 0,538 | 0,101 |
| Heuristik | 0,563 | 0,098 |
| **Mensch (10 Server-Logs)** | - | **1,80** |

Abschluesse je Musterreihe und Partie: Netz 5,05 / 5,06 / 3,49 / 2,50 / 1,13 /
0,74, Heuristik 5,11 / 4,93 / 3,03 / 2,08 / 1,28 / 0,88. Beide brechen unten
ein. Netz gewinnt 296/407 = 72,7 Prozent, deckungsgleich mit der
Referenzmessung.

**Der Lehrer ist marginal besser beim Vollenden und exakt gleich schlecht bei
den Spalten.** Damit ist die Gabel aus par.5 entschieden: **Destillation
scheidet aus, es gibt nichts zu uebertragen.** Die Kompetenz existiert nirgends
im System und muss erzeugt werden. Diese Prereg wird gebraucht.

**Die Gegenreferenz** liefert `tools/probes/human_row_profile_probe.py` aus
den zehn Mensch-gegen-Netz-Partien in `static/log/` (Nutzer gewinnt 8 von 9,
also die einzige unkontaminierte empirische Quelle im Repo):

| | R1 | R2 | R3 | R4 | R5 | R6 | volle Spalten |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Mensch | 4,00 | 4,10 | 3,40 | 3,20 | 2,50 | 2,20 | **1,80** |
| Netz | 4,90 | 4,90 | 3,30 | 2,40 | 1,10 | 0,50 | 0,10 |
| Delta | -0,90 | -0,80 | +0,10 | +0,80 | +1,40 | +1,70 | +1,70 |

Der Mensch gibt oben ab und kauft unten das Vielfache. Gepaart je Partie
(beide spielen dieselbe), also ohne Aera- oder Seed-Versatz. Vorbehalt: n=10,
ein Spieler, schwacher Gegner.

### Die Ziel-Kennzahl folgt aus einer Identitaet, nicht aus einer Messung

`tools/probes/row_supply_ceiling_probe.py`: **eine volle Spalte kostet
1+2+3+4+5+6 = 21 Zellen**, unabhaengig davon, wie geschickt platziert wird.
Daraus folgt der schaerfste Befund der ganzen Kette:

| | verbrauchte Zellen | truege bei Gleichverteilung | erreicht |
| --- | --- | --- | --- |
| Mensch | 60,9 | 2,90 Spalten | 1,80 |
| Netz | 42,7 | **2,03 Spalten** | **0,10** |

**Das Netz hat kein Versorgungsproblem, sondern ein Verteilungsproblem.** Mit
den Fliesen, die es heute schon nimmt, waeren rund zwei volle Spalten drin --
es holt 0,1. Keine einzige zusaetzliche Fliese noetig.

**Damit ist die Ziel-Kennzahl fuer v2 bestimmt: das MINIMUM der Abschluesse
ueber die sechs Reihen**, nicht deren Summe und nicht die Laenge. Jede
Vollendung ueber dem Minimum ist aus Spaltensicht Ueberschuss. Das Zielprofil
ist FLACHER, nicht laenger.

Gegenprobe des Modells: Mensch 60,9 plus Netz 42,7 ergibt 103,6 der 105
analytisch verfuegbaren Fliesen-Platzierungen (98,7 Prozent). Zwei
unabhaengige Wege, dieselbe Zahl.

### Der uebersehene dritte Kanal: Spezialfliesen

Aufgefallen an einer Diskrepanz (belegte Zellen 5,05 in Rasterreihe 1, obwohl
die Rundenschranke 5 erspielte Zellen erlaubt), benannt vom Nutzer.
`docs/engine_manual.md:166-177`: 9 Spezialfliesen in einer SEPARATEN Reserve,
gesetzt sobald die drei anderen regulaeren Zellen ihrer Kuppelplatte voll
sind, zaehlend als gewoehnliche belegte Zelle **auch fuer Spalten**, zahlend
Punkte in Hoehe der Rasterreihe 1..6.

**Nicht "gratis" (Nutzer-Korrektur):** die drei anderen Zellen kosten je einen
Musterreihen-Abschluss. Richtig ist **die vierte Zelle einer Platte zum Preis
von dreien**, gebunden an eine LOKALE Figur (ein 2x2-Slot) statt an eine
globale wie eine Spalte.

Gemessen lassen beide Seiten rund **4 Spezialfelder je Partie leer**
(Kriterium 7: -11,94 und -12,23 Punkte, also -4 Felder mal 3). Das ist
zugleich der groesste Einzelposten der Plattenwertung. **Fuer v2 ist das der
billigere Einstieg als die Spalte:** die Freischaltbedingung ist lokal, der
Ertrag ist eine zusaetzliche Zelle plus 1..6 Punkte plus die vermiedene
Strafe.

## par.3 Vorschlag fuer den fehlenden Term (NICHT entschieden)

Gesucht ist das **Gegenstueck zu `projected_unplaceable_penalty`**: ein
Term, der `pattern_lines` liest und Kredit fuer **erreichbare Vollendung**
gibt, nicht fuer Laenge.

Die Bauform, die aus der B1-Lehre folgt:

- **stetig im Fuellstand, nicht Stufenfunktion.** B1s 0-auf-1 belohnte das
  Anfangen. Der Kredit muss mit jeder weiteren Fliese wachsen, damit er das
  Fortfuehren lenkt.
- **an die ERREICHBARKEIT gebunden, nicht an die Reihe.** Eine Reihe 6, deren
  Zielfeld auf der Kuppel gar nicht mehr legbar ist, verdient keinen Kredit.
  Der bestehende Vetter dafuer ist `row_has_open_matching_slot`
  (`round_end.rs`), der genau diese Pruefung schon macht.
- **an den PLATTEN-Ertrag gebunden.** Kredit dafuer, dass das Zielfeld eine
  Spalte schliesst, die ohnehin fast voll ist -- nicht dafuer, dass irgendwo
  eine Fliese mehr liegt. Die Spalten-Zuordnung existiert bereits
  (`spalten_fuellung`: Slot (tr,tc), Space si -> Spalte 2*tc + si%2, dort
  gegen die Engine verifiziert).

Das ist ausdruecklich ein VORSCHLAG. Der Zuschnitt ist Nutzer-Entscheid
(par.6).

**Registriertes Risiko mit Falsifikator, vorab festgelegt:** derselbe wie bei
B1, und aus demselben Grund. Wenn v2 die Initiierung hebt, ohne die
**Vollendungsquote deutlich ueber 0,53** zu bringen, wiederholt sie B1 und
gilt als NICHT-Erfolg -- auch bei guenstiger Arena. Die Vollendungsquote ist
Pflicht-Kennzahl jedes Berichts zu diesem Arm; sie steht seit dem 2026-08-24
direkt im Arena-Artefakt (`long_rows_started` / `long_rows_completed` /
`long_rows_cleared_unplaceable`).

### v2 GEBAUT (2026-08-24) -- Abnahme NICHT bestanden: der Term ist zu klein

**Nutzer-Entscheide, beide umgesetzt:** eigener Agent-Typ (nicht Spec-Kanal,
nicht Env-Knopf) und alle vier Bausteine aus par.3.

Gebaut:

- `engine/src/heuristic_v2.rs`: `row_completion_progress`, alle vier
  Bausteine. Spalten-Posten als MARGINALER Zuwachs
  (`(f+1)^2 - f^2` mal 7/36), damit nichts doppelt zaehlt, was
  `wertung_progress` schon fuer bereits gelegte Zellen kreditiert.
- `mcts::HeuristikVariante::{V1, V2}` mit `player_total_variante`,
  `evaluate_variante`, `search_action_variante`,
  `search_drafting_action_variante`. **Alle Bestandssignaturen bleiben
  unveraendert und laufen ueber V1** -- Paritaets-Hash `8c6684ff...` haelt
  nach Wheel-Neubau, Suite 509/0.
- `self_play::run_heuristic_v1_vs_v2_arena` plus Python-Bindung
  `heuristic_v1_vs_v2_arena`, mit Brettwechsel-Schalter und `v2_board` im
  Ergebnis.
- Der exakte R5-Anker bleibt UNBERUEHRT: dort rechnet der Loeser den
  Rundenausgang exakt aus, eine Heuristik-Formung koennte nur schaden.

**Abnahme (40 Partien, 150 Sims je Seite, v2 auf Brett 1):**

| | Start | vollendet | Quote | Punkte je Partie |
| --- | --- | --- | --- | --- |
| v1 | 156 | 94 | 0,603 | 48,5 |
| v2 | 157 | 93 | 0,592 | 45,2 |

Siege v2 15/40. **Der Term bewegt das Verhalten praktisch nicht** (157 gegen
156 Starts) und kostet leicht Staerke.

**Kein Bug, sondern die Groessenordnung.** Drei Unit-Tests belegen, dass der
Term auf einer angefangenen, erreichbaren Reihe strikt positiv ist und auf
leeren und unerreichbaren Reihen null -- der Zweifel "liefert er ueberhaupt
etwas" ist damit ausgeraeumt, bevor der Befund gemeldet wurde.

Die Diagnose folgt aus der Formel selbst: der marginale Spalten-Zuwachs ist
`(2f+1)/36 * 7`, bei Spaltenhoehe f. Gemessene Hoehen liegen bei 2 bis 4, das
sind **0,97 bis 1,75 Punkte**, mal `(fuellstand/kapazitaet)^2 <= 1`. Gegen
einen `player_total` im Bereich mehrerer Dutzend Punkte ist das Rauschen.
Hinzu kommt: der Spalten-Posten ist auf ein aktives k1 gegatet, und k1 ist
nur in rund 38 Prozent der Partien aktiv (312 von 814 Partie-Seiten
gemessen) -- in der Mehrheit der Partien traegt der groessere der beiden
Posten also gar nichts.

**Was der Befund fuer den Zuschnitt heisst.** Die marginale Lesart ist
konservativ und zahlenmaessig korrekt, aber sie kann die eigentliche
Struktur nicht sehen: nach der 21-Zellen-Identitaet (par.2) ist die
Spaltenzahl durch das **MINIMUM** der Abschluesse ueber die sechs Reihen
gedeckelt. Der Wert eines Abschlusses in der heute schwaechsten Reihe ist
deshalb nicht sein marginaler Zellbeitrag, sondern der Engpasswert -- er hebt
die Decke fuer ALLE Spalten. Ein Term, der das abbildet, waere ein anderer
Zuschnitt, kein groesserer Faktor auf diesen.

**Ausdruecklich NICHT getan:** dem Term einen Verstaerkungsfaktor
vorschalten. Das waere die Dosis-Antwort auf ein Struktur-Problem und
wiederholt die Bauform, die `PREREG_scoring_plate_injection` (Sweep ueber
30-fachen Dosisbereich) und B1 bereits zweimal verworfen haben. Der naechste
Zuschnitt ist Nutzer-Entscheid.

### ENTSCHEIDUNGSMETRIK, vorab festgelegt (2026-08-24, Nutzer-Ruege)

**Primaermetrik ist die Zahl der VOLLEN SPALTEN je Partie.** Nichts anderes.

Anlass ist ein Verfahrensfehler in der ersten Abnahme: dort wurde die
**Musterreihen-Vollendungsquote** (`long_rows_completed / long_rows_started`)
gemessen und als Ergebnis berichtet. Nutzer: "wollten wir uns nicht auf die
fertiggestellten Spalten fokussieren?" -- ja, und die Fokus-Regel in
`STATUS.md` sagt es auch. Die beiden Groessen sind NICHT dasselbe:

- eine volle Musterreihe legt **einen** Stein auf die Kuppel;
- eine volle Spalte braucht **sechs**, je einen in jeder Rasterreihe.

Die Vollendungsquote ist eine Zwischengroesse. Sie kann steigen, ohne dass
eine einzige Spalte mehr fertig wird -- etwa wenn die zusaetzlichen
Abschluesse in Rasterreihen landen, die ohnehin schon bedient waren. Genau
das ist nach der 21-Zellen-Identitaet der Normalfall: die Spaltenzahl haengt
am MINIMUM der Abschluesse ueber die sechs Reihen, nicht an ihrer Summe.

**Verbindlich fuer jede v2-Abnahme:**

| Rang | Kennzahl |
| --- | --- |
| **Primaer** | volle Spalten je Partie, gepaart, BEIDE Sitzpositionen |
| Sekundaer | Musterreihen-Vollendungsquote (die bisherige Zahl, jetzt als Zwischengroesse gefuehrt) |
| Sekundaer | freigeschaltete Spezialfliesen je Partie und ihre Rasterreihe |
| Sekundaer | Strafleiste, unplatzierbar geraeumte Reihen |
| Pflicht | die sechs Standard-Kennzahlen je Seite (CLAUDE.md), Block-Ebene |

**Erfolgsschwelle, vorab:** v2 gilt nur dann als Erfolg, wenn die vollen
Spalten je Partie steigen UND die Staerke nicht faellt. Steigt die
Vollendungsquote, ohne dass die Spalten folgen, ist das ein NICHT-Erfolg --
dieselbe Bauform wie der B1-Falsifikator, und aus demselben Grund: ein
bewegter Zwischenwert ist kein Ergebnis.

**Messbarkeit:** die Spaltenzahl ist aus den Zaehlern NICHT ableitbar, sie
braucht das Partie-Log (`rekonstruiere_partie` in
`tools/probes/column_build_structural_probe.py`). `play_arena_game` und
`run_heuristic_v1_vs_v2_arena` haben dafuer seit dem 2026-08-24 einen
`log_games`-Schalter (Default aus).

### Abnahme gegen die PRIMAERMETRIK (2026-08-24): Zwischengroesse bewegt, Ziel nicht

80 Partien, beide Sitzpositionen, 150 Sims je Seite, saettigende Form mit
handgesetztem Reihen-Kredit.

| | volle Spalten je Partie | max Spaltenhoehe | Musterreihen-Quote | geraeumt | Punkte | Siege |
| --- | --- | --- | --- | --- | --- | --- |
| v1 | 0,125 | 4,70 | 0,571 | 15 | 40,1 | 38/80 |
| v2 | **0,163** | 4,79 | **0,675** | **1** | 43,4 | 42/80 |

**Verdikt nach der vorab festgelegten Regel: NICHT-Erfolg.** Die
Zwischengroessen bewegen sich deutlich -- die Musterreihen-Vollendungsquote
steigt um 10 Prozentpunkte, die unplatzierbar geraeumten Reihen fallen von 15
auf 1. Die Primaermetrik bewegt sich nicht messbar: 0,125 gegen 0,163 sind
**10 gegen 13 volle Spalten in 80 Partien**. Das liegt unter der Aufloesung
dieses Laufs, und ein Anteil von 30 Prozent auf so kleinen Zahlen ist keine
Aussage. Die Staerke ist unauffaellig (42/80).

**Die Diagnose steht schon in par.2 und bestaetigt sich hier:** die maximale
Spaltenhoehe bewegt sich von 4,70 auf 4,79. Der Engpass ist unveraendert,
weil eine Spalte ALLE sechs Rasterreihen braucht und v2 die zusaetzlichen
Abschluesse nicht dorthin lenkt, wo sie fehlen. Genau das sagt die
21-Zellen-Identitaet: die Spaltenzahl haengt am MINIMUM ueber die Reihen,
nicht an ihrer Summe -- und ein Term, der jede angefangene Reihe belohnt,
hebt die Summe.

**Wert dieses Laufs, trotz Nicht-Erfolg:** er zeigt, dass die saettigende
Form (Nutzer-Vorgabe) das Verhalten sehr wohl bewegen kann -- die erste,
konvexe Fassung tat das nicht. Der Hebel wirkt, er zeigt nur in die falsche
Richtung. Und die Zahl 1 gegen 15 bei den geraeumten Reihen belegt, dass der
B1-Fehler (angefangene Ruinen) diesmal NICHT auftritt.

### par.3a DREIECKS-ABWEICHUNG als Zielfunktion (Nutzer-Formulierung 2026-08-24, VOR der Messung registriert)

Der Nutzer hat das Zielbild in eine Fehler-Metrik ueberfuehrt: das Brett als
reine **Binaermatrix** (belegt 1 / leer 0), Abweichung von der idealen
Dreiecksform als Abzaehlung.

```
Abweichung = leere Felder im ERLAUBTEN Bereich
           + belegte Felder im VERBOTENEN Bereich
```

Fuer das 6x6-Raster ist der erlaubte Bereich `r + c <= 5`, also
6+5+4+3+2+1 = **21 Zellen**. Score 0 heisst perfekte Dreiecksform.

**Warum ausgerechnet diese Form (Nutzer-Praezisierung 2026-08-24):
"theoretisch sind alle bedienbar, praktisch sind nur zwei bedienbar, deshalb
Dreiecksform als Shaping-Agent".** Die Dreiecksform ist keine aesthetische
Wahl, sondern die MACHBARKEITSHUELLE. Eine Spalte braucht theoretisch je
einen Abschluss aus jeder der sechs Musterreihen -- praktisch liefern nur die
oberen zuverlaessig: gemessen 4,88 / 4,70 / 2,88 / 2,23 / 1,71 / 1,31 belegte
Zellen je Rasterzeile. Das Dreieck gibt von oben nach unten 6 / 5 / 4 / 3 /
2 / 1 Zellen frei, hat also exakt dieselbe Neigung. Es beschreibt damit, was
erreichbar IST, statt ein Ideal vorzuschreiben, das an der Frequenz
scheitert.

**Warum das die richtige Zielfunktion ist -- und was sie loest.** Die
bisherige Zielzellen-Menge war eine undifferenzierte VEREINIGUNG aus einer
Spalte und einer Zeile, und die Spalte gewann darin jeden Konflikt: ihre
sechs Zellen sind aus sechs verschiedenen Musterreihen bedienbar, die der
Zeile nur aus einer. Gemessen kostete jeder Spaltengewinn Zeilen:

| Bauschritt | volle Spalten | volle Zeilen |
| --- | --- | --- |
| v1 (Anker) | 0,163 | 0,438 |
| Routing (Draft + Tiling) | 0,362 | 0,250 |
| + plattenunabhaengiger L-Wert | 0,438 | 0,400 |
| + gestreute Start-Ecke | 0,450 | 0,263 |
| + Kuppelplatten-Wahl | 0,588 | 0,200 |

Ein EINZELNER Skalar ueber das ganze Brett hat diesen Konflikt strukturell
nicht. Und die 21 ist keine Koinzidenz: es ist dieselbe 21, die eine volle
Spalte kostet (1+2+3+4+5+6). Die Dreiecksform IST die Spalte-plus-Zeile-
Struktur, nur vollstaendig ausformuliert -- ihre Kanten sind eine volle
Rasterzeile und eine volle Rasterspalte, und alles dazwischen ist
zusammenhaengend, zahlt also Platzierungspunkte nach Linienlaenge.

**Vorab festgelegt, damit die Zahl nicht nachtraeglich passend gemacht wird:**

- Gewicht `DREIECK_GEWICHT = 1.0` PUNKT je Abweichungs-Zelle. Bewusst
  konservativ: eine Platzierung bringt gemessen 2,3 bis 4,3 Punkte, der
  Formterm kann sie also nie ueberstimmen, sondern nur Gleichstaende in
  Richtung Form brechen.
- Gespiegelt wird NUR um die Spalten-Achse: zwei Orientierungen (volle
  Spalte links oder rechts), das Minimum zaehlt. Die volle Zeile liegt immer
  oben. KORREKTUR 2026-08-24 (Nutzer): die erste Fassung nahm alle vier
  Ecken und haette damit ein Brett belohnt, das auf eine nie erreichbare
  Form zulaeuft -- die unteren Orientierungen verlangen eine volle
  Rasterzeile 5, gespeist von Musterreihe 6 mit 1,3 Abschluessen je Partie.
- **Primaermetrik bleibt unveraendert** (volle Spalten je Partie, gepaart,
  beide Sitze). Die Abweichung ist die ZIELFUNKTION des Agenten, nicht das
  Erfolgsmass -- sonst misst sich der Arm an sich selbst.
- **Zusaetzlich auszuweisen:** volle Zeilen. Der Zweck dieses Zuschnitts ist
  gerade, dass Spalten nicht mehr auf Kosten der Zeilen steigen. Steigen die
  Spalten und fallen die Zeilen erneut, hat der Skalar sein Versprechen
  NICHT eingeloest, auch wenn die Primaermetrik guenstig aussieht.

#### par.3a ERGEBNIS (2026-08-24): als HEURISTIK-Suchterm wirkungslos -- Netzseite UNGEPRUEFT

80 Partien, beide Sitze, Gewicht 1,0 je Abweichungs-Zelle wie vorab
festgelegt:

| | volle Spalten | volle Zeilen | Punkte | Siege |
| --- | --- | --- | --- | --- |
| ohne Dreiecksterm | 0,588 | 0,200 | 40,8 | 31/80 |
| mit Dreiecksterm | 0,550 | **0,200** | 39,8 | 32/80 |

**Nicht-Erfolg nach der vorab festgelegten Regel -- ABER NUR FUER DIE
HEURISTIK.** Die Zeilen bleiben unveraendert bei 0,200, die Spalten steigen
nicht, die Punkte fallen. Der Skalar hat den Spalte-gegen-Zeile-Konflikt
hier nicht aufgeloest.

**Nicht auf die Netzseite uebertragen (Nutzer-Einwand 2026-08-24: "wuerd ich
so noch nicht festsetzen, waere erst am Netz wirklich zu pruefen").** Der
Einwand trifft, und der Mechanismus ist derselbe, der schon par.1 traegt --
nur umgekehrt: in der HEURISTIK IST das Verhalten die Bewertung, ein Term
dort steuert unmittelbar. Am NETZ kommen die Priors aus dem Netz
(`net_mcts.rs:57`), ein Blattterm wirkt also gegen eine trainierte Zugordnung
statt mit ihr. Dass er hier nichts bewegt, sagt ueber dort nichts. Die
Netzseite ist UNGEPRUEFT.

**Diagnose: die Hebelwirkung, nicht die Metrik.** Der Score aendert sich je
Zug um hoechstens 1, waehrend die Platzierungen selbst 2,3 bis 4,3 Punkte
auseinanderliegen. Ein additiver Term mit Gewicht 1,0 kann damit nur
Gleichstaende brechen, und die sind selten. Das Gewicht hochzudrehen waere
die Dosis-Antwort auf ein Strukturproblem -- dieselbe Bauform, die
`PREREG_scoring_plate_injection` (30-facher Dosisbereich) und
`PREREG_long_row_payoff` B1 bereits verworfen haben. Bewusst NICHT getan.

**Die Metrik bleibt gueltig, sie ist nur am falschen Ort.** Der Code bleibt
als `heuristic_v2::dreiecks_abweichung` erhalten (mit Test), weil par.3b ihn
als LERNZIEL braucht: 36 binaere Zellen, eine Funktion des BRETTES statt des
gespielten Ausgangs, klarer Nullpunkt. Das ist dieselbe Lehre wie bei B1 --
such-seitig ist der Weg zu, ziel-seitig nicht.

### par.3b Folgearm: SHAPING-KOPF statt Ownership-Kopf (Nutzer-Idee 2026-08-24, NICHT gebaut)

Nutzer: "vielleicht bauen wir auch statt dem Ownership-Head so etwas
Aehnliches ein wie ein Shaping-Head, der umso hoeher wird, je eher das Netz
an die Dreiecksform kommt."

Die Idee passt zu einem bereits registrierten Befund: der Ownership-Kopf
traegt gemessen NICHTS zur Staerke bei (Gewicht 0), aber seine 36 Feldlabels
sind das richtige Ziel-FORMAT ([[project_ownership_head_closed]]). Ein Kopf,
der die Dreiecks-Abweichung vorhersagt, haette genau dieses Format -- 36
Zellen, binaer -- und ein Ziel, das im Unterschied zum Konjunktions-Kopf
NICHT politikabhaengig ist: die Abweichung ist eine Funktion des Brettes,
nicht des gespielten Ausgangs ([[project_conjunction_head_predicts_occurrence]]).

**Voraussetzung, und deshalb Folgearm:** ein Korpus, in dem die Dreiecksform
ueberhaupt vorkommt. Den soll v2 erst erzeugen. Vorher waere der Kopf auf
plattenblindes Spiel geeicht -- derselbe Fehler wie viermal zuvor
([[feedback_dont_calibrate_to_plate_blind_play]]).

**Abklingender Beitrag (Nutzer-Erweiterung 2026-08-24):** der Shaping-Kopf
soll den Value-Kopf in den FRUEHEN Runden stuetzen und dann zurueckgenommen
werden -- "dann koennen wir den Shaping-Head decayen und der Value-Head
uebernimmt immer mehr".

Das trifft eine gemessene Luecke, es ist kein allgemeines Curriculum-Argument:

- Der Value-Kopf ist gerade frueh am schwaechsten (v14-Zyklus: "value head
  weak early rounds"; die Runde-1/2-R2 waren lange negativ, siehe
  [[project_v8d_value_head_root_cause]]).
- Und der TD-Bootstrap kann eine frueh begonnene Investition strukturell
  nicht tragen: `bootstrap_value_after_rounds` spielt EINE Runde aus und
  bewertet dann per Netz (`round_transition_deep.rs:852`). Eine lange Reihe,
  die in Runde 3-4 zahlt, liegt hinter diesem Punkt. Der naheliegende Ausweg
  -- tieferer Horizont -- ist am Kostengate gescheitert
  (`PREREG_bootstrap_horizon.md` Stufe 1: Aufschlag 60,7 Prozent gegen eine
  Schwelle von 25).

Der Shaping-Kopf greift also dieselbe Stelle mit anderen Mitteln an: er
liefert frueh ein Signal, das nicht auf den Ausgang warten muss, weil die
Dreiecks-Abweichung eine Funktion des BRETTES ist.

**Ausgabe-Struktur: ZWEI Kanaele, nicht einer und nicht vier**
(Nutzer-Vorschlag 2026-08-24: "vielleicht brauchst ja zwei Layer beim
Shaping-Head, einmal mit Spalte 0 als Startwert und einmal mit Spalte 5").

Der Heuristik-Term nimmt das MINIMUM ueber vier Orientierungen. Fuer einen
gelernten Kopf ist das die falsche Form, aus zwei Gruenden:

- Ein Minimum zerstoert die Richtungsinformation. Der Kopf koennte nur noch
  sagen, WIE WEIT das Brett von einer Dreiecksform weg ist, nicht WOHIN es
  laeuft -- und genau das soll er der Suche liefern.
- Ein Min-Ziel ist nicht glatt: welche Orientierung fuehrt, kann von Zug zu
  Zug kippen, und das Lernziel springt mit.

**Warum zwei und nicht vier:** die beiden UNTEREN Orientierungen verlangen
eine volle Rasterzeile 5. Die wird ausschliesslich von Musterreihe 6
gespeist, und die schliesst gemessen 1,3-mal je Partie ab -- sechs Zellen
sind dort strukturell unerreichbar (dieselbe Asymmetrie, die schon die
Zeilenziele auf die obersten zwei Rasterzeilen begrenzt hat, s. par.3a).
Uebrig bleiben oben-links und oben-rechts, also genau Spalte 0 und Spalte 5
als Startpunkte. Ein Kanal je Orientierung, beide gegen dieselbe
Binaermatrix gerechnet.

Geprueft (2026-08-24): alle vier Orientierungen haben exakt 21 Zellen und je
eine volle Zeile plus eine volle Spalte an ihrer Ecke -- oben links (Z0/S0),
oben rechts (Z0/S5), unten links (Z5/S0), unten rechts (Z5/S5).

**Vorab festzulegen, BEVOR gebaut wird (sonst wird der Zeitplan hinterher
passend gemacht):**

1. Die Abkling-Kurve (Form, Start- und Endgewicht, ueber welche Groesse sie
   laeuft -- Trainingsepochen, Generationen oder Rundennummer). Der Nutzer
   hat "decayen" gesagt, nicht welche Kurve; das ist ein eigener Entscheid.

   **ENTSCHIEDEN 2026-08-25 (Nutzer): die Kurve laeuft ueber die RUNDENNUMMER.**
   Anlass war die Frage nach einer rundenabhaengigen Gewichtung des
   Value-Loss; der Nutzer hat sie ausdruecklich hierher gezogen ("das wuerd
   ich gern mit dem shaping/heatmap term machen, dafuer gibt es schon eine
   prereg") statt sie als eigenen Arm zu fuehren. Damit faellt eine geplante
   Extra-Vorregistrierung weg.

   Das passt zur Begruendung des Abklingens oben: der Value-Kopf ist gerade
   FRUEH am schwaechsten, und "frueh" heisst hier Runde, nicht Epoche. Die
   Groessenordnung steht schon im Bestand -- das Runden-R2 des Value-Kopfes
   liegt bei rund 0,03 in Runde 1 gegen rund 0,62 in Runde 5
   (`net_mcts.rs`-Kopf zur geblendeten Utility). Der Shaping-Beitrag traegt
   also dort am meisten, wo der Value-Kopf am wenigsten weiss.

   Form, Start- und Endgewicht bleiben offen und sind VOR dem Bau
   festzulegen. Punkt 3 unten gilt unveraendert: nicht an der Metrik tunen,
   an der der Arm beurteilt wird.
2. Der Waechter dagegen, dass der Kopf zur Kruecke wird: gemessen wird die
   Value-Qualitaet OHNE Shaping-Beitrag, sonst verdeckt der Kopf genau die
   Schwaeche, die er beheben soll.
3. Die Abkling-Parameter duerfen NICHT an der Metrik getunt werden, an der
   der Arm beurteilt wird ([[feedback_preregister_decision_metric]]).

Eigene Vorregistrierung vor dem Bau, eigene Nutzer-Freigabe.

### par.3c Bonuschips auf die blockierende Reihe -- gebaut, korrekt, WIRKUNGSLOS (Chip-Knappheit)

`plate_builder::v2_chip_vorzug`: vollendet per Bonuschip die Musterreihe, die
eine Zielzelle blockiert, sobald das mit der Engine-Regel (2 farbgleiche oder
3 beliebige Chips je fehlende Zelle, `round_end::greedy_chip_alloc`) moeglich
und die Zielzelle sofort platzierbar ist.

**Erster Befund war ein Test-Fehler, kein Funktions-Fehler.** Ein isolierter
Rust-Test (`plate_builder::v2_chip_vorzug_tests`) mit konstruiertem
Zustand -- Kuppelplatte, angefangene Reihe, zwei farbgleiche Chips --
bestaetigt: die Funktion findet die Vollendung. Erst dabei fiel auf, dass
mein erster Test die falsche Farbe ansetzte (Zelle (1,0) verlangt Tuerkis,
nicht Rot, laut Kuppelplatte 0) -- REGEL 0: der Fehler waere ohne den
isolierten Test als "Funktion kaputt" fehlgemeldet worden.

**Live-Wirkung dennoch null** (80 Partien, beide Sitze): weiterhin 0
Chip-Vollendungen von Rasterreihe 6, 7,5 Prozent Partien ohne jeden
R6-Abschluss, Spaltenquote unveraendert bei 0,550. Das ist nach der
Chip-Oekonomie plausibel, nicht widerspruechlich: `greedy_chip_alloc`
verlangt 2 FARBGLEICHE Chips je fehlender Zelle. Insgesamt sind nur rund 20
Chips im gesamten Spiel im Umlauf (`docs/engine_manual.md`: "4 je Runde ueber
5 Runden"), geteilt zwischen beiden Spielern -- ein einzelner Spieler haelt
selten mehr als eine Handvoll, und je zwei davon muessen zufaellig dieselbe
Farbe tragen UND die Reihe muss auf genau eine fehlende Zelle heruntergefuellt
sein, damit der Vorzug ueberhaupt greift. Diese Kombination trat in 80
Partien kein einziges Mal ein.

**Kein Ruecknahme-Fall wie par.3a:** der Term kostet nichts (er greift nur,
wenn er zuschlaegt) und bleibt im Code -- er wird wirksam, sobald ein Korpus
mehr Chip-Reserven zulaesst oder die Bedingung gelockert wird (z.B. 3
beliebige statt 2 farbgleiche zulassen, was `greedy_chip_alloc` bereits als
Fallback kennt). Fuer diese Kampagne ist er eine korrekte, aber seltene
Randbedingung -- nicht der Hebel, der die 7,5 Prozent Null-R6-Partien
schliesst.

### par.5.3 ERGEBNIS (2026-08-24): Faehigkeit belegt, Preis hoch -- URTEIL STEHT AUS

`tools/run_v2_teacher_arena.sh` -> `tools/probes/v2_teacher_arena.py`,
Artefakt `evaluations/v2_teacher_arena.json`. 407 Kampagnen-Seeds je Arm,
Champion@400 gegen Heuristik@150, mit v1-Bezug auf DENSELBEN Seeds -- ohne
den waere "v2 verliert X" nicht von "die Heuristik verliert ohnehin X" zu
trennen.

| | Siege | Punkte | Marge | volle Spalten | Vollendungsquote | max Hoehe |
| --- | --- | --- | --- | --- | --- | --- |
| v1 (Bezug) | 0,256 | 37,6 | -12,2 | 0,086 | 0,564 | 4,58 |
| **v2** | **0,128** | 34,8 | **-19,4** | **0,302** | **0,686** | 5,08 |

Gepaart gegen das Netz (Block-Ebene, 16 Bloecke) im v2-Lauf: volle Spalten
+0,175 (t=+7,79), Punkte -19,610 (t=-18,94), Siege -0,755 (t=-20,09),
Strafpunkte +7,567 (t=+11,83).

**Die Faehigkeit ist belegt.** v2 baut 3,5-mal so viele volle Spalten wie v1
und hebt die Vollendungsquote von 0,564 auf 0,686 -- die B1-Vorgabe
("deutlich ueber 0,53") ist erfuellt. Damit ist erstmals ein Agent im System,
der lange Reihen nicht nur anfaengt, sondern zu Ende bringt.

**Und der Preis ist hoch.** Die Siegquote gegen den Champion halbiert sich
(25,6 auf 12,8 Prozent), die Marge verschlechtert sich um 7,2 Punkte. Ein
v2-Korpus traege die Zielfaehigkeit also auf einem deutlich schwaecheren
Niveau als der heutige Erzeuger.

**Nebenbefund, der eine frueher registrierte Sorge entkraeftet:** die vollen
ZEILEN brechen hier NICHT ein (0,403 gegen 0,432). Im
Heuristik-gegen-Heuristik-Lauf waren sie von 0,438 auf 0,200 gefallen und
standen seither als ungeloeste Regression in der Prereg. Gegen ein NETZ tritt
das nicht auf -- die Regression war ein Artefakt des v1-gegen-v2-Aufbaus, in
dem beide Seiten um dieselbe Zellenmenge konkurrieren. Der offene Posten ist
damit kleiner als angenommen, aber nicht verschwunden: im Selbstspiel-Aufbau
bleibt er.

**URTEIL STEHT AUS -- und das ist kein Versaeumnis.** par.5.3 hat bewusst
keinen Schwellenwert vorregistriert (s. Klarstellung bei par.5.4). Die
Abwaegung lautet: ein Korpus mit 3,5-mal mehr Spaltenvollendungen -- der
Faehigkeit, die im System nirgends vorkommt und die weder Destillation noch
vier Such-Eingriffe erzeugen konnten -- erkauft mit einem Erzeuger auf 12,8
Prozent Siegquote. Ob das ein guter Tausch ist, haengt daran, ob das Netz die
FAEHIGKEIT uebernehmen kann, ohne das NIVEAU mitzuuebernehmen. Diese Frage
ist mit der Messung nicht beantwortet, sondern erst gestellt -- sie gehoert
zu par.5.4 (Korpus und Training).

## par.4 Anker-Integritaet: die ERSTE Bauentscheidung, vor der Formel

Der Nutzer-Entscheid lautet "v2 als ZUSAETZLICHER Anker". Daraus folgen harte
Randbedingungen:

1. **Die bestehende Heuristik bleibt byte-identisch.** Sie ist der Elo-Anker
   der gesamten Leiter. Jede Aenderung an `player_total` oder
   `wertung_progress` bricht sie. Das ist keine Stilfrage: eine gebrochene
   Verankerung entwertet jeden Elo-Wert der Kampagne rueckwirkend.
2. **Die Heuristik-Seite ist heute ausdruecklich SPEC-FREI.**
   `play_net_game` traegt den Kommentar "die Heuristik-Gegenseite bleibt
   spec-frei (par.6a Entscheid 3, Heuristik-Anker eingefroren)". Ein zweiter
   Lehrer braucht also erst einen Weg, ueberhaupt als eigener Agent zu
   existieren. **Das ist zu entscheiden, bevor eine einzige Zeile Formel
   geschrieben wird.**
3. **Eigene Kennung im Korpus.** Self-Play-Dateien werden nach dem ERZEUGER
   benannt. v2-Partien muessen von v1-Partien unterscheidbar sein, sonst ist
   das Fenster still gemischt und keine spaetere Auswertung kann die Arme
   trennen.
4. **Paritaets-Gate.** Wie bei jedem Knopf der Kapselung: der
   Paritaets-Hash der Bestandskonfiguration muss nach dem Bau unveraendert
   halten (`tools/parity_probe.py`), sonst ist v2 kein Zusatz, sondern eine
   Aenderung.

## par.5 Messkette (Reihenfolge bindend)

1. **Vorbedingung:** der laufende Netz-gegen-Heuristik-Lauf. Liegt die
   Vollendungsquote des Lehrers deutlich ueber der des Netzes, ist v2 nicht
   der billigste Weg und diese Prereg ruht.
2. **v1 gegen v2, Heuristik gegen Heuristik, ohne Netz.** Kann v2 lange
   Reihen? Pflicht-Kennzahl Vollendungsquote. Das kostet keine
   Netz-Inferenz und ist die billigste Abnahme des Terms selbst.
3. **v2 gegen den Champion.** Erst wenn (2) die Faehigkeit belegt: ist v2 als
   LEHRER stark genug, um ein brauchbares Korpus zu erzeugen? Ein Lehrer, der
   lange Reihen kann und dabei deutlich schwaecher ist, erzeugt ein Korpus,
   das die Zielfaehigkeit traegt und das Niveau senkt -- diese Abwaegung
   gehoert gemessen, nicht geschaetzt.
4. **Korpus und Training.** Erst danach, eigener Zuschnitt, eigene Freigabe.

   **Kein vorregistrierter Schwellenwert fuer par.5.3 (Nutzer-Nachfrage
   2026-08-24: "warum sollte der Lehrer nicht ueberzeugen, was sind die
   Kriterien"):** die Formulierung oben ist eine Abwaegung, kein Zahlenwert.
   Ausgewiesen werden Punkte/Margin (Staerkeverlust gegen den Champion) und
   Vollendungsquote/volle Spalten (Faehigkeitsgewinn); ob das Verhaeltnis
   "brauchbar" ist, ist ein NACHTRAEGLICHES Urteil, kein vorab gesetzter
   Schnitt. Wer diesen Abschnitt spaeter als bereits entschieden zitiert,
   zitiert falsch.
5. **Ausgewiesen** in jedem Schritt: Vollendungsquote (Falsifikator),
   Initiierungsrate, sowie die sechs Standard-Kennzahlen je Seite (CLAUDE.md).
   Auswertung auf BLOCK-Ebene.

## par.6 OFFENE NUTZER-ENTSCHEIDE (vor Baubeginn)

1. **Wie existiert v2 technisch?** Spec-Kanal auch fuer die Heuristik-Seite
   (kehrt par.6a Entscheid 3 der Kapselung um), eigener Agent-Typ neben
   `HeuristicArenaAgent`, oder env-gegatete Zweitfassung. Die Wahl bestimmt,
   wie teuer spaetere Duelle v1 gegen v2 sind.
2. **Zuschnitt des Terms** (par.3): stetiger Fuellstands-Kredit, Bindung an
   `row_has_open_matching_slot`, Bindung an den Spalten-Fuellstand -- alle
   drei, oder eine Teilmenge?
3. **Bekommt v2 einen eigenen Elo-Leitereintrag?** Als "zusaetzlicher Anker"
   spricht vieles dafuer; es kostet aber Ankerpartien.
4. **Rolle im Korpus:** Lehrer fuer Destillation, reine Korpus-Quelle
   (Seeding-artig), oder beides?

## par.7 Was diese Prereg NICHT ist

- **Kein Ersatz der Heuristik.** Siehe par.4.1.
- **Kein weiterer Blattwert-Knopf am NETZ.** Zwei Negative derselben Klasse
  (par.1) sind genug. v2 aendert die Bewertung eines LEHRERS, um Korpus zu
  erzeugen -- nicht die Blattbewertung des Netzes.
- **Keine Aussage darueber, ob lange Reihen stark sind.** Das ist genau die
  Frage, die mangels eines kompetenten Spielers bisher niemand beantworten
  kann; v2 soll den Spieler liefern, der sie beantwortbar macht.

## par.8 Prio-Leiter als Routing-Huelle (`V2Huelle`, VORREGISTRIERT 2026-08-24)

**Anlass.** Nutzer-Vorgabe 2026-08-24, zwei Zuege: erst "in eine
Dreiecksmatrix einhuellen mit shaping faktoren der unteren reihen", dann
ausformuliert als Prioritaeten-Leiter ("ansonsten machen wir es relativ
stupide") mit dem Implementierungs-Hinweis, sie als lineares Scoring mit
phasenabhaengigen Gewichten zu bauen statt als `if`-Kaskade. Die Leiter
beschreibt das Spiel des Nutzers ("so aehnlich spiel ich") und ist damit die
erste Zielvorgabe im Strang, die aus einer kompetenten Referenz stammt und
nicht aus dem heutigen Self-Play.

**Warum als ROUTING und nicht als Bewertungsterm.** Zwei Messungen im selben
Strang zeigen in dieselbe Richtung: die Dreiecks-Abweichung als Suchskalar war
wirkungslos (80 Partien, volle Spalten 0,588 auf 0,550, Punkte fallen,
Commit `19405f8`), waehrend alle vier Fortschritte des Strangs aus dem
Platzierungs-Routing kamen (volle Spalten 0,163 auf 0,562). Die Diagnose dort
war die Hebelwirkung: der Skalar bewegt hoechstens 1 Punkt je Zug, waehrend
Platzierungen 2,3 bis 4,3 Punkte auseinanderliegen.

### par.8.1 Was gebaut ist

Eigene Variante `mcts::HeuristikVariante::V2Huelle`. Die BEWERTUNG ist
byte-identisch zu `V2` (dieselben Summanden in `player_total_variante`), der
einzige Unterschied ist die Zielzellen-Menge im Routing. Damit misst ein
Vergleich `V2` gegen `V2Huelle` genau das Routing und nicht ein Buendel.

Die Karte (`plate_builder::zielkarte`) bildet die Leiter als Gewicht je
Rasterzelle ab, zwei Orientierungen (Randspalte links oder rechts;
Spiegelung NUR um die Spalten-Achse, gleiche Begruendung wie bei
`dreiecks_abweichung`):

| Prio | Inhalt | Gewicht |
| --- | --- | --- |
| 3 | Randspalte 0 oder 5 | 5,0 |
| 4 | zweite Spalte 1 oder 4 | 4,0 |
| 5 | Spezialfeld freischalten, Joker halten | 3,0 (Auflage, hebt nie ab) |
| 6 | Rasterzeile 0 und 1 | 2,0 |
| 7 | Nachbarn Rasterzeile 2 und 3 | 1,0; 0,5 bei aktiver Diagonale |

Rasterzeile 4 und 5 ausserhalb der beiden Spalten bekommen im Grundbild 0:
jede Zelle dort kostet einen Abschluss von Musterreihe 5 bzw. 6. Die
Prio-5-Auflage hebt sie nur an, wo sie ein Spezialfeld freischalten -- deren
Ertrag haengt an keinem weiteren Abschluss, weil
`round_end::check_special_trigger` das Feld automatisch belegt und abrechnet,
sobald die drei anderen Zellen der Platte liegen.

Drei Entscheidungspunkte lesen die Karte:

1. **Drafting** (`plate_builder::huellen_drafting_vorzug`) als linearer Score
   `Zielgewicht + W_STOER * Eskalation * Stoerung + W_STRAF * Eskalation *
   Strafpunkte`, Eskalation `[1, 2, 4, 8]` je Runde 1-4.
2. **Kuppelplatten-Wahl** (`dome_vorzug_fuer_zellen_gewichtet`) mit
   `huellen_zellen_wert`: auf Rasterzeile 5 schlaegt Special den Joker und
   beide jede Normalfarbe.
3. **Tiling** (`tiling_vorzug_fuer_zellen_gewichtet`) summiert Kartengewichte
   statt Zellen zu zaehlen.

Die Festnagelung ab Runde 3 bleibt, nur auf der Orientierung statt auf der
Spalte -- sie war der Bauschritt, der die Partien mit voller Spalte von 35 auf
50 Prozent hob.

### par.8.2 Was NICHT gebaut ist, und warum

- **Prio 0 (Endspiel)**: der TRIGGER-Teil hat keinen Anknuepfungspunkt --
  das Spiel endet nach genau 5 Runden (`game.rs:687`), eine volle Reihe
  beendet es nicht. Der RECHEN-Teil ist teilweise gedeckt: der Heuristik-Pfad
  schaltet in Runde 5 auf den EINGEFRORENEN Anker-Loeser um
  (`round5_anchor::applies`, in `mcts.rs` kurzgeschlossen), ein
  Expectiminimax mit Zufallsknoten ueber die verdeckten Bonuschips und
  exaktem Blattwert. **Kein geloestes Endspiel:** Knotenbudget 200 reicht
  fuer effektiv ~3 Halbzuege und trifft die Wahl eines tiefen Orakels in
  81,4 Prozent der Faelle (`round5_anchor.rs:44-59`); die Runde ist zudem
  nicht vollinformiert. Das Routing hoert nach Runde 4 auf und uebergibt
  dorthin. Ob der exakte Blattwert den gelernten schlaegt, ist in
  `PREREG_chance_nodes.md` Teil E ausdruecklich noch offen.
- **Prio 1 (Strafleiste)** ist als `projected_unplaceable_penalty` bereits
  Summand der Bewertung. Neu ist nur die ROUTING-Seite: ein Vorzug, der die
  eigene Strafleiste ueber `-4` Punkte treibt, wird nicht mehr ausgesprochen
  (`STRAF_SCHWELLE_PUNKTE`), die Entscheidung faellt an die Suche zurueck.
  Kein Verbot auf der Zugmenge -- die Beschneidungs-Bauform ist in
  `PREREG_provocation.md` §7/§9 als spielzerstoerend gemessen.
- **Prio 2 (Gegner-Stoerung)** ist neu verdrahtet, aber NICHT neu gerechnet:
  `provocation::gegner_bedarf_akut` und `stoer_bewertung` existieren seit
  `PREREG_opponent_disruption_v2.md` (dort UEBERHOLT, nichts verdrahtet).
  Der Suchwert bleibt unberuehrt: `normalize_score` ist weiterhin bewusst
  KEINE Differenz zum Gegner. Die Stoerung wirkt nur in der Zugpraeferenz.

### par.8.3 Die gesetzten Zahlen

`PRIO_GEWICHT`, `PRIO7_AUFGEWEICHT`, `W_STRAF`, `W_STOER`,
`STRAF_SCHWELLE_PUNKTE` sind SETZUNGEN, keine Ableitungen -- dieselbe Regel
wie bei `REIHEN_KREDIT`: eine aus dem heutigen Spiel geschaetzte Groesse
wuerde die Schwaeche festschreiben, die sie beheben soll. Gefordert ist nur
die strenge Rangfolge; die Kalibrierung steht je Konstante im Code.

`W_STOER = 0,10` ist bewusst am unteren Rand (Stoerung erreicht in Runde 4
hoechstens 4,8 und bleibt damit unter Prio 3). Grund ist gemessen:
`PREREG_long_row_payoff.md` B1 hat mit einem zu starken Zusatzanreiz
14,5 Prozentpunkte Siegquote gekostet. Ablation ist je eine Zeile
(`W_STOER = 0.0`, `W_STRAF = 0.0`).

### par.8.4 Messung (vorregistriert, VOR dem Lauf festgelegt)

Aufbau wie Messkette Schritt 2, damit die Zahlen mit der Bauschritt-Tabelle
vergleichbar bleiben: `V2` gegen `V2Huelle`, je 80 gepaarte Partien, BEIDE
Sitze (`swap`), 150 Sims je Seite, `--log-games`, gleiche Seeds. Einstieg:
`mosaic_rust.heuristic_v1_vs_v2_arena(..., variante_a="v2",
variante_b="v2huelle")`.

**Entscheidungsmass (primaer):** volle Spalten je Partie der Huellen-Seite
gegen die v2-Seite, gepaart und auf BLOCK-Ebene ausgewertet (Paar-SEs
unterschaetzen massiv, siehe die Arena-Block-Korrelation).

**Falsifikator:** steigen die vollen Spalten nicht signifikant, ist die Leiter
als Routing-Bauform negativ entschieden -- und zwar unabhaengig davon, wie
plausibel das Zielbild ist. Ein "sieht besser aus"-Befund zaehlt nicht.

**Waechter (dieselbe Klasse wie die B1-Vorgabe):** faellt die Vollendungsquote
langer Musterreihen unter 0,53, wiederholt der Arm B1 und gilt als negativ,
auch bei mehr vollen Spalten.

**Mitzuschreiben** (Standard-Kennzahlen, je Seite und als Differenz):
Reihenauslastung, Spaltenauslastung (volle Spalten, max Hoehe, Teilspalten
>= 3/>= 4), Strafleistenauslastung, Punkte je Wertungsplatte, eigene Punkte,
Marge. Zusaetzlich fuer diesen Arm: Freischaltungen von Spezialfeldern je
Partie (Prio 5 zielt genau darauf, und der Posten ist mit -11,94 Punkten der
groesste Einzelposten der Plattenwertung).

**Ablations-Reihenfolge, falls der Arm gewinnt:** `W_STOER = 0` zuerst
(Prio 2 ist der einzige Baustein ohne jede Vormessung), dann `W_STRAF = 0`,
dann Prio-5-Auflage aus. Bei einem Gesamtbefund ohne Ablation ist NICHT
entscheidbar, welcher Baustein traegt.

### par.8.5 ERGEBNIS des Laufs (2026-08-25, n=160)

`tools/probes/v2_envelope_arena.py`, Ergebnis in
`evaluations/v2_envelope_arena.json`. Aufbau genau wie in par.8.4 vorab
festgelegt: 80 gepaarte Partien je Sitz, 150 Sims je Seite, Seed 20260825,
Auswertung auf 10 Bloecken zu je 16 Partien.

| Kennzahl | v2 | v2huelle | Delta | t (Block) |
| --- | --- | --- | --- | --- |
| volle Spalten | 0,425 | **0,950** | +0,525 | **9,12** |
| max Spaltenhoehe | 5,306 | 5,612 | +0,306 | 10,17 |
| Teilspalten >= 3 | 2,919 | 3,094 | +0,175 | 1,83 |
| Teilspalten >= 4 | 1,837 | 2,237 | +0,400 | 4,25 |
| Spezialfeld-Freischaltungen | 0,713 | **1,512** | +0,800 | **9,32** |
| Strafpunkte | -15,04 | -13,40 | +1,64 | 2,31 |
| eigene Punkte | 40,14 | **48,21** | +8,07 | **4,80** |

Siegquote der Huelle im direkten Duell **0,706**. Vollendungsquote langer
Musterreihen 0,667 gegen 0,743 -- der B1-Waechter ist erfuellt, und zwar von
BEIDEN Armen.

Reihenauslastung je Partie (Zuege je Rasterzeile 0..5):

* v2: 4,36 / 4,07 / 2,47 / 1,93 / 1,46 / 1,31
* Huelle: 3,91 / 3,95 / 2,74 / 2,25 / 2,14 / 1,52

Die Verschiebung geht genau dorthin, wo die Leiter sie haben will: Rasterzeile
3, 4 und 5 gewinnen (+0,32 / +0,68 / +0,21), die breiten oberen Zeilen geben
ab. Marge und Punkte sind hier dieselbe Groesse, weil beide Arme im selben
Spiel sitzen.

**Das Entscheidungsmass ist erfuellt, der Falsifikator greift nicht, der
Waechter haelt.** Bemerkenswert ist der Punkte-Posten: JEDER bisherige
v2-Bauschritt hat Spalten mit Punkten bezahlt (Schritt 3: volle Spalten 0,086
auf 0,302, dafuer Punkte 37,6 auf 34,8 und Siegquote halbiert). Hier steigen
Spalten UND Punkte, und die Strafleiste sinkt zusaetzlich.

**VORBEHALT, nachgetragen 2026-08-25 (Befund der Parallelsitzung, von mir am
Code nachgeprueft):** ein Teil der Punktedifferenz koennte aus einer anderen
Quelle stammen als aus besserem Spiel. `self_play.rs:500-545`
(`resolve_and_apply_stack_draw`, DEFAULT-Pfad) entscheidet ueber die Tiefe der
Blindziehungen, indem es `best_eval_for_tile` -- ein absolutes BRETTNIVEAU --
gegen `avg_remaining_type_value` stellt, und letzteres mittelt
`bonus_points + Anzahl Wild-Felder` je Restplatte, liegt also rund zwischen 1
und 3 (beide Funktionen in dieser Sitzung gelesen). Das ist ein
Einheitenbruch, und die Tiefe haengt damit am Brettzustand des ziehenden
Spielers.

Beide Arme sitzen zwar in DERSELBEN Partie mit denselben Wertungsplatten --
ein Plattenverteilungs-Effekt scheidet also aus. Aber sie haben verschiedene
Bretter, koennen deshalb verschieden tief ziehen und verschieden viel dafuer
bezahlen. Ein Teil der +8,07 Punkte kann "die Huelle kauft weniger Platten"
heissen statt "die Huelle spielt besser".

Die Parallelsitzung misst den Posten am v20wdlsw-Korpus mit 11,22 +- 0,42
Punkten je Partie bei aktiver Wertungsplatte 6 gegen 3,93 +- 0,15 ohne
(600 Partien; von mir NICHT nachgerechnet).

**Pruefbar ohne neuen Aufbau:** die Sonde spaltet ab jetzt zusaetzlich nach
aktiver Platte 6 auf. Konzentriert sich der Punktevorsprung dort, ist der
Ziehmechanismus beteiligt; ist er flach, nicht. Der Lauf steht aus -- die
Aufspaltung wurde erst nach der Messung eingebaut, und die Zahlen oben sind
deshalb bis dahin MIT diesem Vorbehalt zu lesen. Die Struktur-Kennzahlen
(volle Spalten, Freischaltungen, Reihenauslastung) sind davon nicht beruehrt,
sie haengen nicht am Punktestand.

**Was der Lauf NICHT sagt.** Er ist Heuristik gegen Heuristik bei 150 Sims.
Schritt 3 hat gezeigt, dass eine im Heuristik-Duell belegte Faehigkeit gegen
den Champion einbrechen kann. Die Frage "taugt die Huelle als LEHRER" ist
damit gestellt und nicht beantwortet -- dafuer braucht es denselben Aufbau
wie par.5.3 (Champion@400 gegen Huelle@150), und der Einstieg
`net_vs_heuristic_v2_arena` ist bisher fest auf `V2` verdrahtet.

### par.8.6 ABLATIONEN (2026-08-25, Reihenfolge wie in par.8.4 festgelegt)

Je Arm derselbe Aufbau, derselbe Seed, dieselben 160 Partien; geaendert wurde
jeweils EINE Konstante im Code, danach Wheel neu gebaut. Alle Werte sind
Differenzen Huelle minus v2.

| Arm | volle Spalten | t | Spezialfelder | Strafpunkte | Punkte | Siegquote | Vollendungsquote |
| --- | --- | --- | --- | --- | --- | --- | --- |
| voll | 0,525 | 9,12 | 0,800 | +1,637 | **+8,069** | **0,706** | 0,743 |
| `W_STOER = 0` | 0,506 | 7,81 | 0,706 | +1,300 | +5,506 | 0,606 | 0,738 |
| `W_STRAF = 0` | 0,512 | 8,22 | 0,694 | **-1,438** | +2,975 | 0,575 | 0,733 |
| Prio-5-Auflage aus | 0,425 | 8,36 | 0,625 | +1,319 | +5,475 | 0,600 | 0,723 |

**Struktur und Staerke haengen an verschiedenen Bausteinen.** Die vollen
Spalten kommen fast vollstaendig aus der Zielkarte selbst: sie bleiben bei
0,506-0,525, egal ob Stoerung oder Strafleiste im Score stehen. Nur die
Prio-5-Auflage bewegt sie (0,525 auf 0,425) -- sie ist der einzige der drei
Zusatzbausteine, der auf die FORM wirkt, und sie tut es ueber genau den Weg,
fuer den sie gebaut ist (Freischaltungen 0,800 auf 0,625).

Die Punkte-Marge dagegen zerfaellt sauber in drei Beitraege: `W_STRAF` traegt
5,09, die Prio-5-Auflage 2,59, `W_STOER` 2,56. `W_STRAF = 0` dreht ausserdem
das Vorzeichen der Strafleiste (-1,438): ohne den Term nimmt die Huelle MEHR
Strafpunkte als v2, weil das Routing dann ungebremst in die Zielzellen zieht.

**Keine Dosis-Erhoehung abgeleitet.** Dass `W_STOER` bei 0,10 schon 2,56
Punkte traegt, ist kein Argument fuer mehr davon -- das waere die
Dosis-Antwort, an der `scoring_plate_injection` und `long_row_payoff` B1
gescheitert sind. Wer die Dosis anfasst, registriert vorher.

**Kontrolllauf:** nach dem Zurueckbauen reproduziert der Hauptlauf seine
Zahlen exakt (Spezialfelder 1,512, Punkte 48,212, Siegquote 0,706;
`v2_envelope_arena_restore_check.json`) -- die drei Ablationen haben den
Bestand nicht verschoben.

## par.9 Punkte-Heatmap statt Prio-Leiter (`V2Heatmap`, VORREGISTRIERT 2026-08-25)

**Anlass.** Nutzer-Vorschlag 2026-08-25: "wir koennen ihn auch als punkte
heatmap verwenden. dann ist er weniger starr in die dreiecksform gepresst."
Der Nutzer merkt dazu an, die Karte sei urspruenglich fuer das NETZ gedacht;
der Heuristik-Test hier ist der billige Vorlauf (22 Sekunden je Messung),
nicht der eigentliche Einsatzort.

Die Ablation par.8.6 macht den Vorschlag dringlich: die STRUKTUR haengt an der
Zielkarte, nicht an den linearen Zusatztermen. Die Karte ist der Hebel, und
die aktuelle ist eine handgesetzte Stufenleiter.

**Was gebaut ist.** `plate_builder::points_heatmap`: Wert je Rasterzelle =
marginaler Zuwachs der AKTIVEN Wertungsplatten, exakt gemessen (Zelle
probeweise belegen, `scoring::scoring_progress` neu rechnen, Differenz), plus
der Spezialfliesen-Sofortbonus, wenn die Belegung ein Spezialfeld
freischaltet. Unerreichbare Zellen fallen auf 0
(`column_build::cell_is_completable` gegen `provocation::remaining_colors`) --
das ist zugleich die Knappheits-Kopplung, die `heuristic_v2` fehlt, und macht
eine Runden-Abklingkurve ueberfluessig.

Platzierungspunkte nach Linienlaenge sind bewusst NICHT enthalten: die
maximiert `best_first_step_inner` ohnehin, und ihre Alleinherrschaft war der
Anlass fuer v2.

Alles andere ist identisch zu `V2Huelle` (Bewertung, linearer Drafting-Score,
Plattenwahl, Tiling-Vorzug), damit der Vergleich genau die KARTE misst.

**Messung.** `V2Huelle` gegen `V2Heatmap`, sonst Aufbau wie par.8.4:
je 80 gepaarte Partien, beide Sitze, 150 Sims, Seed 20260825, Bloecke zu 16.

**Entscheidungsmass:** volle Spalten je Partie, gepaart, auf Block-Ebene.
**Waechter:** Vollendungsquote >= 0,53 (B1-Vorgabe).

**VORHERGESAGT, vor dem Lauf (der eigentliche Zweck dieses Arms):** die
Heatmap verliert Spaltenbau in Partien OHNE aktive Spalten-Wertungsplatte.
`scoring_progress` kreditiert Spaltenfuellung ausschliesslich bei aktivem k1
(`scoring.rs`, Zweig 1), und k1 liegt nur in rund 40 Prozent der Partien an --
genau die Luecke, fuer die `heuristic_v2::plate_independent_l_value` gebaut
wurde. Die Sonde spaltet deshalb nach `k1_aktiv`/`k1_inaktiv` auf.

Trifft die Vorhersage zu, ist der Befund NICHT "Heatmap schlecht", sondern
"Heatmap braucht einen plattenunabhaengigen Sockel" -- und die Reparatur ist
eine Zeile. Trifft sie nicht zu, war meine Ursachenkette falsch und das ist
das wertvollere Ergebnis.

### par.9.1 ERGEBNIS (2026-08-25, n=160): Heatmap VERLIERT, Vorhersage WIDERLEGT

`evaluations/v2_envelope_arena_heatmap.json`. Differenzen Heatmap minus Huelle.

| Kennzahl | Huelle | Heatmap | Delta | t (Block) |
| --- | --- | --- | --- | --- |
| volle Spalten | 0,650 | **0,281** | **-0,369** | **-4,89** |
| max Spaltenhoehe | 5,438 | 4,925 | -0,512 | -6,24 |
| Teilspalten >= 3 | 2,906 | **3,281** | **+0,375** | **+6,07** |
| Teilspalten >= 4 | 2,019 | 1,906 | -0,113 | -1,68 |
| Spezialfeld-Freischaltungen | 1,150 | 0,613 | -0,537 | -5,12 |
| Strafpunkte | -16,36 | **-13,69** | **+2,675** | +3,79 |
| eigene Punkte | 40,99 | 38,31 | -2,675 | -2,79 |

Siegquote der Heatmap 0,463. Vollendungsquote 0,718 (Waechter erfuellt).

**Die vorregistrierte Vorhersage ist WIDERLEGT, und zwar im Vorzeichen.**
Registriert war: die Heatmap verliert Spaltenbau dort, wo k1 INAKTIV ist, weil
`scoring_progress` Spalten nur dann kreditiert. Gemessen ist das Gegenteil --
der Verlust ist groesser, wo k1 AKTIV ist:

| | n | Huelle | Heatmap | Delta | t |
| --- | --- | --- | --- | --- | --- |
| k1 aktiv | 52 | 0,750 | 0,250 | -0,520 | -4,06 |
| k1 inaktiv | 108 | 0,602 | 0,296 | -0,324 | -5,48 |

**Die Ursache steht seit dem ersten v2-Bauschritt im Code und ich habe sie
uebersehen** (`heuristic_v2::plate_independent_l_value`, Modul-Doku):
"`scoring_progress` summiert ueber alle sechs Spalten und belohnt damit
BREITE. Eine volle Spalte braucht aber FOKUS -- die 21-Zellen-Identitaet
haengt am Minimum ueber die Rasterzeilen, nicht an der Summe."

Genau das zeigt die Messung: Teilspalten >= 3 steigen hoch signifikant
(+0,375, t=6,07), waehrend volle Spalten und maximale Hoehe fallen. Die
Heatmap verteilt die Fuellung auf MEHR Spalten und bringt keine zu Ende. Das
ist keine Kalibrierungsfrage, sondern die Bauform: **eine additive
Punktekarte ist konstruktionsbedingt ein Breiten-Signal.** Fokus laesst sich
daraus nicht gewinnen, indem man die Zahlen anders skaliert.

**Was der Arm sonst zeigt.** Die Heatmap spielt sauberer: Strafpunkte -13,69
gegen -16,36 (t=3,79) und Vollendungsquote 0,718 gegen 0,677. Sie ist der
bessere GREEDY-Spieler und der schlechtere BAUMEISTER.

**Was NICHT widerlegt ist.** Der Nutzer hat die Karte fuer das NETZ gedacht,
nicht fuer das Routing. Als Eingabeebene ist sie ein FEATURE, kein Ziel -- ein
Netz kann aus einem Breiten-Signal Fokus lernen, ein Greedy-Routing nicht.
Dieser Lauf entscheidet nur die Routing-Verwendung, negativ.

### par.9.2 Erwartete PUNKTE je Zelle (`V2PointMap`) -- ebenfalls negativ

Nutzer-Praezisierung 2026-08-25: die Karte war nicht fuer die Wertungsplatten
allein gedacht, sondern fuer die erwarteten End- bzw. Rundenpunkte beim Legen
auf diese Zelle. par.9.1 hat also eine ENGERE Karte gemessen als gemeint.

Nachgebaut als `plate_builder::expected_points_map`: wie par.9, plus die
Platzierungspunkte nach Linienlaenge (`round_end::score_placed_tile`, auf dem
Probe-Brett nach dem Legen). Gleicher Aufbau, n=160, gegen `V2Huelle`:

| Kennzahl | Huelle | PointMap | Delta | t |
| --- | --- | --- | --- | --- |
| volle Spalten | 0,762 | **0,219** | **-0,544** | -6,12 |
| max Spaltenhoehe | 5,513 | 4,862 | -0,650 | -7,35 |
| Teilspalten >= 3 | 2,981 | **3,306** | **+0,325** | +4,63 |
| Spezialfeld-Freischaltungen | 1,219 | 0,650 | -0,569 | -5,71 |
| Strafpunkte | -15,39 | -13,02 | +2,369 | +3,85 |
| eigene Punkte | 43,42 | 39,76 | -3,656 | -2,49 |

Siegquote 0,400. k1-Aufspaltung diesmal ohne Unterschied (-0,540 gegen
-0,562), die Karte verliert unabhaengig von der Spalten-Wertungsplatte.

**Meine Hypothese war wieder falsch, und zwar dieselbe Sorte Fehler.** Ich
hatte erwartet, dass Linienpunkte als SUPERADDITIVE Groesse den Fokus liefern,
der par.9.1 fehlte. Gemessen ist das Gegenteil: die Breiten-Signatur wird
staerker, nicht schwaecher (Teilspalten >= 3 wieder +0,325, volle Spalten und
max Hoehe fallen deutlicher als in par.9.1).

Die Erklaerung steht in der Bauform: Linienpunkte belohnen die Nachbarschaft
zu IRGENDEINEM bestehenden Stein. Jeder angefangene Klumpen zieht damit
gleich stark an, und das Routing landet auf genau dem Kriterium, das
`best_first_step_inner` ohnehin maximiert -- der Alleinherrschaft, deren
Ueberwindung der Anlass fuer v2 war. Das Risiko stand vor dem Lauf im Code
vermerkt; die Messung hat es bestaetigt.

**Gemeinsamer Befund aus par.9.1 und par.9.2:** beide Punktekarten machen
denselben Tausch -- weniger Strafpunkte (+2,4 bis +2,7) gegen weniger
Struktur. Eine gerechnete Punktekarte erzeugt den besseren GREEDY-Spieler und
den schlechteren BAUMEISTER. Volle Spalten verlangen eine Vorgabe, die dem
lokalen Punktgradienten widerspricht; genau das leistet die handgesetzte
Leiter und keine der beiden Karten.

**Unberuehrt bleibt die Netz-Verwendung.** Als Eingabeebene ist eine
Punktekarte ein FEATURE; ein Netz kann aus einem Breiten-Signal Fokus lernen,
ein Greedy-Routing nicht. Beide Laeufe entscheiden ausschliesslich die
Routing-Verwendung, negativ.

## par.10 Lehrer-Test der Prio-Leiter (VORREGISTRIERT 2026-08-25)

par.8.5 hat die Frage gestellt und offen gelassen: die Huelle ist im
Heuristik-Duell belegt, aber Schritt 3 hat gezeigt, dass eine dort belegte
Faehigkeit gegen den Champion einbrechen kann. Dieser Lauf beantwortet sie im
GLEICHEN Aufbau wie par.5.3, damit die Zahlen nebeneinander stehen:
`alphazero_v21_2d_brierbest`@400 gegen die Heuristik@150, 407 Kampagnen-Seeds
(`kampagnen_seeds_407.txt`), `--log-games`, plus v1 auf denselben Seeds als
Bezug.

Einstieg: `tools/probes/v2_teacher_arena.py --variante v2huelle`. Der
Rust-Einstieg nimmt die Variante seit heute als Parameter; vorher war er fest
auf `V2` verdrahtet.

**Kein vorregistrierter Schwellenwert** -- dieselbe Regel wie par.5.3: die
Abwaegung Faehigkeit gegen Niveau ist ein Nutzer-Entscheid, kein Schnitt. Die
Bezugszahlen aus par.5.3 (n=407) sind:

| | Siege | Punkte | Marge | volle Spalten | Vollendungsquote |
| --- | --- | --- | --- | --- | --- |
| v1 | 0,256 | 37,6 | -12,2 | 0,086 | 0,564 |
| v2 | 0,128 | 34,8 | -19,4 | 0,302 | 0,686 |

**Was der Lauf entscheidet:** ob die Huelle den Tausch aufhebt, den v2 machen
musste. v2 hat Faehigkeit mit Niveau bezahlt; im Heuristik-Duell tut die
Huelle das nicht (par.8.5). Ob das gegen ein NETZ haelt, ist genau die Frage,
die par.5.4 offen laesst.

**Vorlauf, ausdruecklich keine Messung:** ein 20-Seed-Anlauf zeigte 0,450
Siege, 1,200 volle Spalten und 55,0 Punkte. n=20 ist unter jeder
Aussagekraft und wird durch den vollen Lauf ersetzt, nicht ergaenzt.

## par.11 Rundenabhaengige Spalten-Gewichte (`V2HuellePhase`, VORREGISTRIERT 2026-08-25)

**Anlass ist eine EXTERNE Quelle, keine eigene Messung.** Rzepecki 2025
(Wroclaw, `docs/Rzepecki2025ImplementingSuperhuman.pdf`, von der
Parallelsitzung im Volltext gelesen, von mir NICHT nachgeprueft) beschreibt
einen Azul-Agenten auf Platz 1 beider BGA-Ranglisten. Zwei Punkte daraus sind
fuer diesen Strang einschlaegig:

1. Seine beste Handheuristik fuehrt die Spaltenvollendung als eigenen
   POTENZIAL-Term ("the biggest potential of completing a yet not completed
   column"), nicht als Punktesumme. Das stuetzt par.9.1/9.2 von der anderen
   Seite: eine Punktesumme ist dort gemessen negativ.
2. Seine Koeffizienten haengen von der Spielphase ab, und die Spalten-Terme
   tragen ihr HOECHSTES Gewicht in den mittleren Runden.

Meine Zielkarte ist heute rundenkonstant; rundenabhaengig ist nur die
Eskalation der linearen Zusatzterme (`ESKALATION`). Punkt 2 ist damit eine
billige Variation mit externer Stuetze.

**Gebaut:** `plate_builder::SPALTEN_PHASE = [1,0 / 1,4 / 1,4 / 1,0 / 1,0]` als
Faktor auf die Grundstufen von Prio 3 und Prio 4, je Runde. Zellen, die die
Prio-5-Auflage angehoben hat, bleiben unberuehrt -- sonst verschoebe der
Faktor zwei Bausteine zugleich.

**Uebernommen ist die FORM, nicht der WERT.** Die Quelle ist anderes Spiel
(Azul-Grundspiel), andere Suchtiefe, andere Termmenge; ihre Koeffizienten sind
hier nicht uebertragbar. `1,4` ist eine SETZUNG.

**Messung:** `V2Huelle` gegen `V2HuellePhase`, Aufbau wie par.8.4 (je 80
gepaarte Partien, beide Sitze, 150 Sims, Seed 20260825, Bloecke zu 16).

**Entscheidungsmass:** volle Spalten je Partie, gepaart, Block-Ebene.
**Waechter:** Vollendungsquote >= 0,53.

**Erwartung, ausdruecklich als schwach markiert:** ich habe keine eigene
Vorhersage mit Begruendung. Die letzten zwei Vorhersagen in diesem Strang
waren im Vorzeichen falsch (par.9.1, par.9.2); eine dritte Vermutung ohne
neuen Beleg waere Rauschen. Der Lauf ist ein Test der externen Form, nicht
meiner Ursachenkette.

## par.12 Vollendbarkeit als FILTER auf der Zielkarte (VORREGISTRIERT 2026-08-25)

**Anlass.** `evaluations/RESEARCH_heuristic_methodology_external_2026-08-25.md` §4.5 und Kandidat 1: die
Planungsliteratur baut Heuristiken durch Vereinfachen und exaktes Loesen der
Vereinfachung (Delete-Relaxation), und §4.4 sagt, dass Wissen ueber die
ZUGFILTERUNG staerker wirkt als ueber Bewertungsterme. Beides zusammen zeigt
auf eine Luecke, die im eigenen Code offen liegt.

**Die Luecke, geprueft.** `column_build::cell_is_completable` und
`column_is_completable` existieren und pruefen genau die Relaxation "reicht
die Restversorgung dieser Farbe noch?". Benutzt werden sie heute in
`points_heatmap`/`expected_points_map` (beide gemessen negativ) und im
Sicherheitsnetz des Spaltenbauers (Default aus). **Die Prio-Leiter selbst
filtert nicht:** `target_map` vergibt Prio 3 und 4 an eine Randspalte, ohne je
zu pruefen, ob sie noch vollendbar ist -- und ab Runde 3 nagelt
`v2_envelope_target` die Orientierung am Fuellstand fest, also womoeglich auf
eine tote Spalte.

**Was gebaut wird.** Eine Auflage auf `target_map`, die Zellen mit
`!cell_is_completable(...)` auf 0 setzt, und eine Orientierungswahl, die eine
nachweislich unvollendbare Randspalte nicht mehr festnagelt. Beides nutzt die
vorhandenen, gegen die Engine verifizierten Funktionen -- kein neuer
Erreichbarkeitsbegriff.

**Messung:** `V2Huelle` gegen `V2HuelleFilter`, Aufbau wie par.8.4 (je 80
gepaarte Partien, beide Sitze, 150 Sims, Seed 20260825, Bloecke zu 16).

**Entscheidungsmass:** volle Spalten je Partie, gepaart, Block-Ebene.
**Waechter:** Vollendungsquote >= 0,53.

**Vorab benanntes Risiko, damit es hinterher nicht als Erklaerung nachgereicht
wird:** der Filter kann in Runde 4-5 zu viel wegschneiden. Die Festnagelung
ab Runde 3 war der Bauschritt, der die Partien mit voller Spalte von 35 auf 50
Prozent hob; ein Filter, der die Zielspalte spaet noch wechseln laesst, kann
genau diesen Gewinn zurueckdrehen. Faellt der Arm negativ aus, ist die erste
Gegenprobe deshalb ein Filter, der NUR in Runde 1-3 greift -- und die ist dann
ein EIGENER Arm, keine Nachbesserung an diesem.

**Keine Vorhersage.** Zwei Vorhersagen in diesem Strang waren im Vorzeichen
falsch (par.9.1, par.9.2). Ich registriere hier keine dritte.

### par.10.1 ERGEBNIS: die Huelle schlaegt v1 UND v2 als Lehrer (2026-08-25)

`evaluations/v2_teacher_arena_v2huelle.json`, 407 Kampagnen-Seeds je Arm,
Champion `v21_2d_brierbest`@400 gegen die Heuristik@150, v1 auf denselben
Seeds als Bezug. Laufzeit 2.610 s bei 11 Threads (814 Partien, 3,207 s je
Partie).

| | Siege | Punkte | Marge | volle Spalten | Vollendungsquote | Strafpunkte | volle Zeilen |
| --- | --- | --- | --- | --- | --- | --- | --- |
| v1 (Bezug) | 0,256 | 37,6 | -12,2 | 0,086 | 0,564 | 19,3 | 0,432 |
| v2 (par.5.3) | 0,128 | 34,8 | -19,4 | 0,302 | 0,686 | -- | 0,403 |
| **Huelle** | **0,373** | **47,1** | **-5,5** | **0,798** | **0,717** | **13,6** | 0,216 |

Gepaart gegen das Netz (16 Bloecke): volle Spalten **+0,700 (t=+13,73)**,
Punkte -5,468 (t=-5,46), Siege -0,245 (t=-5,67), Strafpunkte -0,700
(t=-1,90). Das Netz selbst kommt auf 0,106 volle Spalten.

**Der Tausch, den v2 machen musste, ist aufgehoben.** par.5.3 hat Faehigkeit
mit Niveau bezahlt: volle Spalten 0,086 auf 0,302, dafuer Siegquote 0,256 auf
0,128 und Marge -12,2 auf -19,4. Die Huelle liefert BEIDES -- **2,6-mal so
viele volle Spalten wie v2 und gleichzeitig fast die dreifache Siegquote**,
plus 9,5 Punkte mehr als v1 und 5,7 Strafpunkte weniger.

Damit ist die Frage aus par.5.4 nicht mehr "uebernimmt das Netz die
Faehigkeit, ohne das Niveau mitzuuebernehmen?" -- der Lehrer hat kein
schlechteres Niveau mehr, das er weitergeben koennte.

**Der eine Posten, der faellt: volle Zeilen 0,432 auf 0,216.** Das ist
KEIN Artefakt des Aufbaus wie bei v2 (dort waren die 0,200 aus dem
v1-gegen-v2-Duell ein Konkurrenzeffekt um dieselben Zellen, gegen ein Netz
blieben 0,403). Hier misst derselbe Netz-Aufbau 0,216 -- die Leiter tauscht
Zeilen tatsaechlich gegen Spalten. Bei 7 Punkten je Spalte gegen 3 je Zeile
ist der Tausch rechnerisch guenstig, aber er ist eine ECHTE Verschiebung und
gehoert bei jedem Nachfolgearm mitgemessen.

**Was das freischaltet:** par.3b hatte als Voraussetzung ein Korpus, in dem
die Dreiecksform ueberhaupt vorkommt. Ein Lehrer mit 0,798 vollen Spalten je
Partie -- gegen 0,106 des Netzes -- erzeugt es. Die Voraussetzung ist damit
erstmals erfuellbar, und zwar von einem Lehrer, der nicht schwaecher ist als
der bisherige Anker.

**Offen bleibt der Vorbehalt aus par.8.5:** ein Teil des Punktevorsprungs
koennte aus der Blindziehungs-Regel stammen (`resolve_and_apply_stack_draw`,
Einheitenbruch). Die k6-Aufspaltung ist in der Sonde gebaut, aber fuer DIESEN
Lauf nicht ausgewertet -- `v2_teacher_arena.py` hat sie nicht, nur
`v2_envelope_arena.py`. Die Struktur-Kennzahlen sind davon nicht beruehrt.

### par.11.1 ERGEBNIS: H0, die externe Form uebertraegt sich nicht (2026-08-25)

`evaluations/v2_envelope_arena_phase.json`, n=160 gegen `V2Huelle`, sonst
Aufbau wie par.8.4.

| Kennzahl | Huelle | Phase | Delta | t (Block) |
| --- | --- | --- | --- | --- |
| volle Spalten | 0,787 | 0,812 | +0,025 | 0,39 |
| max Spaltenhoehe | 5,550 | 5,581 | +0,031 | 0,52 |
| Spezialfeld-Freischaltungen | 1,000 | 0,950 | -0,050 | -0,38 |
| Strafpunkte | -13,43 | -13,49 | -0,056 | -0,06 |
| eigene Punkte | 44,05 | 43,86 | -0,188 | -0,17 |

Siegquote 0,500. Vollendungsquote 0,714 gegen 0,712.

**Kein Effekt in irgendeiner Richtung.** Das Entscheidungsmass bewegt sich
nicht (t=0,39), und keine der uebrigen Kennzahlen kommt in die Naehe von
Signifikanz. `SPALTEN_PHASE` bleibt im Code, aber `V2HuellePhase` ist als Arm
negativ entschieden.

**Einordnung, weil die Quelle extern war:** Rzepecki 2025 beschreibt
phasenabhaengige Koeffizienten fuer ein anderes Spiel (Azul-Grundspiel),
andere Suchtiefe, andere Termmenge. Uebernommen war ausdruecklich die FORM,
nicht der Wert. Das Ergebnis sagt also nicht "Tapered Eval funktioniert
nicht", sondern "diese Form, auf diese Karte, mit diesen Werten, bewegt hier
nichts". Ein Sweep ueber die Werte waere die Dosis-Antwort, die in diesem
Projekt schon dreimal negativ entschieden wurde -- er findet NICHT statt.

**Nebenbefund aus der neu gebauten k6-Aufspaltung, erster Einsatz:** das
Punkteniveau liegt bei aktiver Wertungsplatte 6 bei 34,0 gegen 48,9 ohne --
knapp 15 Punkte Unterschied. Das ist mit dem Blindziehungs-Befund der
Parallelsitzung vertraeglich (`PREREG_stack_draw_reservation_rule.md`). Fuer
DIESEN Arm-Vergleich ist der Posten neutral: beide Seiten sind in beiden
Gruppen flach (+0,200 bzw. -0,257), der Vorbehalt aus par.8.5 greift hier
also nicht.
