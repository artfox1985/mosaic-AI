<!-- STATUS: ENTSCHIEDEN | Frage: Kann ein ZWEITER Heuristik-Lehrer, dessen Bewertung die Musterreihen sieht, langes-Reihen-Spiel ueberhaupt erst erzeugen -- und laesst er sich neben den eingefrorenen Elo-Anker stellen, ohne ihn anzufassen? | Beleg: JA (par.10.1), v2-Zweig entfernt (par.19). Bester Stand v22-b05 (par.3b.9/3b.10), DAgger-Runde 2 H0 (par.3b.11). Tor-Revision par.3b.12 loest das alte KEIN-Self-Play ab: Erzeugung ABGESCHLOSSEN 2026-08-31 (12.000 Partien), Waechter bestanden (Symmetrie +0,4041, 5.629 Seiten mit voller Spalte), v23 daraus trainiert; Arm K gebaut, Default aus (par.3b.3). -->

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

Aus `evaluations/artifacts/long_row_init_arena_eval.json` (814 gepaarte Partien,
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

**NACHTRAG 2026-08-25, zwei Pruefungen auf Nutzer-Auftrag -- beide aendern
den Zuschnitt dieses Arms.**

**(1) Die Grundrate der Hilfskoepfe in diesem Projekt ist 0 von 4.**

| Kopf | Ergebnis |
| --- | --- |
| `endgame_head` | Offline echte Gewinne (R5 0,457, Brier -0,0016), **Arena H0: Gating 97:103, p=0,76** -- wurde Standard-Rezept, Champion unveraendert (`PREREG_plate_intervention.md`) |
| `ownership_head` | Gewicht 0, kein belegter Staerkeeffekt (n=6, p=0,22) |
| `plate_head` | 2026-08-10 gebaut und wieder ENTFERNT |
| `conjunction_head` | Ziel politikabhaengig, vier Kalibrierungsvarianten gescheitert |

Der Endgame-Kopf ist der einschlaegige Praezedenzfall: exakte Labels, gratis,
genau auf die gemessene Schwachstelle gezielt -- also dieselben drei
Argumente, die fuer den Shaping-Kopf sprechen. Ergebnis 97:103. Wer diesen
Arm faehrt, sollte das vorher wissen und nicht hinterher erklaeren.

**(2) Ein Kopf, der die Abweichung JE ZELLE vorhersagt, waere ein
Informationsverlust -- nicht neutral, sondern schlechter als der Bestand.**

Die Abweichung einer Zelle ist `erlaubt_o(r,c) XOR belegt(r,c)`. `erlaubt_o`
ist eine FESTE Maske, die Abweichung also eine deterministische Umkodierung
von "belegt am Spielende". Beide Orientierungen kodieren dieselbe
`belegt`-Matrix um -- der zweite Kanal traegt damit genau dieselbe Information
wie der erste. Unterm Strich 36 Bit, zweimal verschieden vorzeichenbehaftet.

Der bestehende Ownership-Kopf traegt dagegen 72 (`neural_net.py:2422`:
"2 Spieler x 3x3 Slots x 4 Felder") -- also die 36 eigenen UND die 36 des
Gegners. Das Umlabeln wuerde die Gegnerhaelfte ersatzlos streichen und dafuer
nichts Neues liefern.

**Was stattdessen substanziell waere** (beide ungebaut, beide brauchen einen
eigenen Entscheid):

* **(a) Huellen-Gewichtung des bestehenden Ziels.** Ziel und Breite bleiben,
  aber die Loss-Maske gewichtet die 21 Huellen-Zellen hoeher als die uebrigen
  15. Das aendert nicht WAS gelernt wird, sondern WO die Kapazitaet hingeht --
  eine echte Aenderung, kein Relabeln. Die Stelle ist klein: `train.py`
  rechnet bereits `own_loss = (own_bce * own_m).sum() / own_m.sum()`, es gibt
  also schon eine Maske.
* **(b) Die Abweichung als AGGREGAT** (ein oder zwei Skalare) zusaetzlich zum
  bestehenden Kopf. Auch das bringt keine neue Information, aber eine andere
  Loss-Geometrie: der Gradient belohnt die Gesamtform statt der Einzelzelle.

**NUTZER-ENTSCHEID 2026-08-25 zum weiteren Vorgehen:** *"mag sein. aber ich
wuerd den kopf trotzdem mittrainieren ... dann laesst sich sauber abschaetzen
ob es einen effekt gibt oder nicht."*

Umgesetzt wird das als EINSCHALTEN, nicht als Umbau -- Punkt (2) oben zeigt,
dass ein Umlabeln auf die Zellabweichung die Gegnerhaelfte streichen wuerde,
ohne etwas Neues zu liefern. Das bestehende Ziel bleibt, `OWNERSHIP_WEIGHT`
geht ueber 0 (stehende Freigabe seit 2026-08-16).

**Bedingung, damit "sauber abschaetzen" auch traegt:** v22 wechselt mit dem
v2-Korpus ohnehin die groessere Variable. Ohne `w0`-Kontrollarm AUF DEMSELBEN
KORPUS sind Kopf und Korpuswechsel konfundiert und der Effekt nicht
zuordenbar. Der Kontrollarm ist im Projekt etabliert (`w0`-Waechter, siehe
`PREREG_ownership_corpus.md`) und kostet einen zweiten Trainingslauf, keine
zusaetzlichen Partien.

Die Huellen-Gewichtung (a) und das Aggregat (b) bleiben als spaetere Arme
liegen -- sie sind Verfeinerungen an einem Kopf, dessen Grundwirkung erst
gemessen sein sollte.

**NACHTRAG 2026-08-25 (3): der geometrische Abgleich ist etwas ANDERES als
das bereits negativ Gemessene -- aber aus ZWEI Gruenden zugleich.**

Nutzer-Praezisierung: *"nur verwenden wir ihn diesmal nicht als
bewertungsterm fuer wertungsplatten oder spezialfliesen usw. sondern rein als
geometrischen abgleich."* Die Unterscheidung traegt, aber nur zur Haelfte --
und beide Haelften gehoeren benannt, damit ein Ergebnis hinterher nicht auf
eine verkuerzt wird.

**(a) Plattenunabhaengige statt plattenabhaengiger Ablesung.** Der gemessene
Verbraucher (`PREREG_ownership_consumer.md`, UEBERHOLT) rechnete die
Kopfausgaben in ERWARTETE PLATTENPUNKTE um und hing damit an den aktiven
Kriterien. Ein geometrischer Abgleich haengt nur an der festen Huellenmaske:

```
E[Abweichung_o] = SUM (1 - p(r,c)) ueber die 21 Huellen-Zellen
                + SUM  p(r,c)      ueber die 15 uebrigen
```

Das ist eine feste Maskenrechnung auf den 36 Ego-Feldern -- kein neuer Kopf,
keine Formaenderung. Und die Plattenunabhaengigkeit hat hier einen POSITIVEN
Praezedenzfall: `heuristic_v2::plate_independent_l_value` war einer der vier
Bauschritte, die die vollen Spalten von 0,362 auf 0,438 gehoben haben, und
wurde genau deshalb gebaut, weil die Suche in rund 60 Prozent der Partien
ohne k1 GEGEN das Routing arbeitete.

**(b) Plattenbewusster statt plattenblinder Korpus.** Der Einwand aus dem
Dossier (Punkt 3, "Beschreibungsmodell als Zielgroesse") haengt NICHT an der
Ablesung, sondern an der Quelle: der Kopf beschreibt das heutige Spiel. Sagt
er "diese Zellen bleiben leer", ist die vorhergesagte Abweichung gross, und
ein Term, der sie bestraft, zieht die Suche zu Zustaenden, die das heutige
Spiel ohnehin erreicht -- selbsterfuellend, egal ob man in Punkte oder in
Geometrie umrechnet.

Was das aufloest, ist der KORPUS. Auf plattenblindem Spiel WAR "wird nicht
fertig" die korrekte Vorhersage. Auf einem v22-Korpus aus dem v2-Lehrer
(0,798 volle Spalten gegen 0,106 des Champions, par.10.1) ist sie es nicht
mehr. Das ist die Wiedervorlage, die
[[feedback_dont_calibrate_to_plate_blind_play]] ausdruecklich fuer den ersten
plattenbewussten Champion vorsieht.

**Keiner der beiden Gruende allein haette gereicht.** (a) behebt die Kopplung
an aktive Platten, (b) das Selbsterfuellende. Faellt der Arm negativ aus, ist
das deshalb NICHT wieder "Hilfskoepfe bringen nichts" -- dann waeren erstmals
beide Bedingungen gemeinsam geprueft, und DAS waere der Befund.

**NACHTRAG 2026-08-25 (4): die Einsatzform ist ERSETZEN, nicht nur stuetzen.**

Nutzer-Vorgabe: *"denk dran das wir den kopf in den ersten runden statt dem
value head im live spiel verwenden wollen. dann decay."* Das ist schaerfer als
die urspruengliche Formulierung oben ("stuetzen") und aendert drei Dinge:

1. **Es ist ein SUCH-Eingriff, kein blosser Trainings-Hilfsverlust.** Der
   Blattwert der fruehen Runden kaeme aus dem Formsignal statt aus der
   Ausgangsschaetzung. Gut begruendet ist das durch die gemessene Schwaeche
   genau dort -- Runden-R2 des Value-Kopfes rund 0,03 in Runde 1 gegen rund
   0,62 in Runde 5.
2. **Einheiten-Problem, und es ist das erste, was gebaut werden muss.** Eine
   Abweichung zaehlt FALSCHE ZELLEN, der Value-Kopf liefert eine
   Gewinnwahrscheinlichkeit. Ohne Abbildung auf die Wertskala ist "statt"
   nicht definiert. Kalibrierung ist in diesem Projekt schon einmal die
   Ursache gewesen ([[project_r5_calibration_result]]: gemessene Steigung
   0,06-0,09 statt ~1) -- die Abbildung wird vorab festgelegt und NICHT an
   der Entscheidungsmetrik getunt.
3. **Der Waechter aus Punkt 2 unten reicht dafuer NICHT.** Er wurde fuer eine
   stuetzende Rolle geschrieben ("Value-Qualitaet OHNE Shaping-Beitrag
   messen"). Beim ERSETZEN ist die Gefahr eine andere und heute Nacht vierfach
   gemessen: par.9.1, par.9.2, par.12 und par.15 haben alle dieselbe Signatur
   gezeigt -- ein Formziel optimiert, Punkte verloren, Teilspalten hoch, volle
   Spalten runter. Der Waechter beim Ersetzen muss deshalb das PUNKTENIVEAU
   und die Strafleiste der fruehen Runden mitmessen, nicht nur die
   Value-Guete.

Dass jene vier Arme das ROUTING veraendert haben und dieser die BEWERTUNG,
ist ein Unterschied -- aber kein Freibrief. par.16 (Deckel in der Bewertung)
war der einzige zustandsabhaengige Eingriff, der nicht geschadet hat, und
auch er hat nichts gebracht.

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

**NACHTRAG 2026-08-25 (5): STUFENPLAN (Nutzer). Erst der eingeschaltete
Kopf, dann -- bedingt -- ein 2D-KOPF.**

Nutzer-Vorgabe: *"wir schauen uns im ersten schritt den umgebauten ownership
head an. wenn das traegt bzw. nicht schaedlich ist bauen wir einen 2d kopf
statt/zusaetzlich zu dem umgebauten ownership head."*

Der 2D-Kopf stand bis hierher NICHT in dieser Prereg -- er wird mit diesem
Nachtrag registriert.

**Stufe 1 (wie oben registriert):** `OWNERSHIP_WEIGHT` > 0 auf dem v22-Korpus,
mit `w0`-Kontrollarm auf DEMSELBEN Korpus. Frage: traegt der Kopf, oder
schadet er wenigstens nicht?

**Stufe 2 (bedingt): ein 2D-Kopf statt oder zusaetzlich zum bestehenden.**

**Der Befund, der die Stufe rechtfertigt, am Code geprueft 2026-08-25:** auch
`Mosaic2DNet` -- die Champion-Architektur -- liest den Ownership-Kopf FLACH
aus, `nn.Linear(hidden_size, 128) -> ReLU -> nn.Linear(128, 72)`
(neural_net.py:2735-2739), byte-identisch zum flachen `MosaicNet`
(neural_net.py:2462-2466). Der Rumpf traegt seit v19 raeumliche Struktur, der
Kopf wirft sie am Ausgang wieder weg. Fuer ein Ziel, das die 6x6-Geometrie IST
-- Huelle, Spalten, Zeilen -- ist das die naheliegendste ungenutzte Stelle:
der flache Ausgang weiss nicht, dass Zelle (r,c) neben (r,c+1) liegt.

**Warum das NICHT unter den Einwand aus Punkt (2) faellt.** Dort ging es um ein
UMLABELN des ZIELS -- 36 Zellabweichungen statt der 72 Ownership-Felder, was
die Gegnerhaelfte ersatzlos gestrichen haette. Ein 2D-Kopf aendert die
ARCHITEKTUR DER ABLESUNG und laesst das Ziel unangetastet: weiterhin 72
Ausgaben, nur raeumlich gerechnet statt flach. Das ist ein anderer Eingriff,
und der alte Einwand trifft ihn nicht.

**Vorbehalt, der vor den Lauf gehoert und nicht danach:** "2D hilft" ist in
diesem Projekt fuer STAERKE nicht belegt. `PREREG_2d_encoder.md` ist
ENTSCHIEDEN mit Orakel 6/6 fuer 2D, aber Arena-Gating 416:384 (p=0,30, Wash).
Belegt ist der 2D-Vorteil auf Offline-Policy-Massen, nicht im Duell. Wer
Stufe 2 faehrt, sollte das vorher wissen.

**Uebergangsregel Stufe 1 -> Stufe 2, vorab festgelegt:** Stufe 2 wird gebaut,
wenn der `w0`-Vergleich KEINEN signifikanten Schaden zeigt (gepaarte Arena,
Block-Ebene). "Traegt" ist ausdruecklich NICHT Bedingung -- der Nutzer hat
"traegt bzw. nicht schaedlich" gesagt, und die Grundrate der Hilfskoepfe
(0 von 4, Nachtrag 1) macht einen Nullbefund zum wahrscheinlichsten Ausgang.
Ein Nullbefund STOPPT die Kette also nicht; ein Schaden schon.

**Was bei Stufe 2 vorab zu entscheiden ist** (nicht jetzt, aber vor dem Bau):
"statt" oder "zusaetzlich". Beides ist vertretbar -- "statt" haelt die
Parameterzahl, "zusaetzlich" erlaubt einen sauberen Ablationsvergleich gegen
denselben flachen Kopf. Der Nutzer hat beides offengelassen.

**NACHTRAG 2026-08-25 (6): der Kopf SOLL zusaetzlich auf die Dreiecksform
getrimmt werden -- das ist Option (a), nicht ein neuer Kopf.**

Nutzer: *"dennoch halte ich es fuer sinnvoll den shaping head zusaetzlich auf
die dreiecksform zu trimmen, damit der value head in runde 1/2 entlastet
wird"*.

**Der Einwand aus Nachtrag (2) richtete sich nicht gegen das Anliegen**, er
richtete sich gegen die BAUFORM: ein eigener Kopf auf die Zellabweichung
saehe 36 Bit, wo der Ownership-Kopf 72 traegt (eigene UND gegnerische Haelfte),
und die Abweichung ist eine feste Umkodierung der Endbelegung -- also sein
schwaecheres Duplikat.

**Das Anliegen ist ohne neuen Kopf erreichbar, in zwei Stuecken, die beide
schon registriert sind:**

* **Die Ablesung** ist die Maskenrechnung aus Nachtrag (3)(a) --
  `E[Abweichung] = SUM (1-p) ueber die 21 Huellen-Zellen + SUM p ueber die
  uebrigen 15`, gerechnet auf den vorhandenen Kopfausgaben. Kein neues Ziel,
  keine Formaenderung. **Sie liefert das fruehe Signal, das nicht auf den
  Ausgang wartet** -- der Grund, aus dem der Nutzer den Kopf will.
* **Das "Trimmen" ist Option (a)**, die Huellen-Gewichtung der Loss-Maske: die
  21 Huellen-Zellen im Verlust hoeher gewichten als die uebrigen 15. Ziel und
  Breite bleiben, die Gegnerhaelfte bleibt erhalten; es aendert nicht WAS
  gelernt wird, sondern WO die Kapazitaet hingeht. `train.py` rechnet bereits
  `own_loss = (own_bce * own_m).sum() / own_m.sum()`, die Maske existiert also.

**Damit ist der Nutzer-Wunsch vollstaendig abgedeckt, ohne die
Hilfskopf-Grundrate von 0 aus 4 erneut zu bemuehen.**

**Was davon unberuehrt bleibt und weiter vorab zu klaeren ist** (Nachtrag 4):
das Einheitenproblem beim ERSETZEN -- eine Abweichung zaehlt Zellen, der
Value-Kopf liefert eine Gewinnwahrscheinlichkeit; die Abbildung wird VORAB
festgelegt und nicht an der Entscheidungsmetrik getunt. Und der Waechter muss
beim Ersetzen das PUNKTENIVEAU und die Strafleiste der fruehen Runden
mitmessen, nicht nur die Value-Guete.

**Verhaeltnis zum Slot-Ausloesungs-Ziel** (`PREREG_special_tile_yield.md`
par.4c): das sind ZWEI Aenderungen am selben Kopf. Sie duerfen nicht in einem
Arm laufen -- die Huellen-Gewichtung veraendert die Kapazitaetsverteilung auf
einem BESTEHENDEN Ziel, das Slot-Ziel fuegt ein NEUES hinzu. Reihenfolge:
Grundwirkung des eingeschalteten Kopfes (Stufe 1), dann (a), dann das
Slot-Ziel.

**NACHTRAG 2026-08-25 (7): die Abklingkurve EXISTIERT schon -- als Treppe.**

Nutzer-Kette 2026-08-25: der Solver ist exakt, aber myopisch; die
v2-Routing-Huelle hat *"ebenfalls keinen weitblick"* (sie routet auf eine FESTE
Zielkarte, unabhaengig von der konkreten Partie); *"dann waere wieder unser
decaying ownership head an der reihe"*.

**Beim Nachsehen ist die Zustaendigkeit im Code bereits so verteilt**, wie die
Abklingkurve sie haben will:

| Runde | Value-Tiebreak | Ownership-Pol | warum |
| --- | --- | --- | --- |
| 1 | aus (nur 2-4) | **wirkt** | Value-R2 ~0,03, taugt hier nicht |
| 2-4 | wirkt, nur Gleichstaende | **wirkt** | beide |
| 5 | aus | aus | Sofortpunkte SIND hier das richtige Ziel, das Spiel endet |

Belege: `exact_or_valued_ignores_evaluator_outside_rounds_2_to_4`
(tiling_solver.rs:2157), `ownership_tiling_overrides_points_rounds_1_to_4`
(:2619), `ownership_tiling_round5_unaffected` (:2735).

**Der Value-Kopf ist frueh schwach und spaet stark, der Ownership-Pol ist
frueh scharf und spaet ueberfluessig -- sie sind Spiegelbilder.** Und die
Achse, ueber die Nachtrag (4) die Abklingkurve laufen laesst (Nutzer-Entscheid:
RUNDENNUMMER), ist genau die, die im Code schon die Zustaendigkeit regelt.

**Daraus die Neubewertung dieses ganzen Arms:** die Architektur ist im Umriss
fertig und nur abgeschaltet. Was fehlt, ist nicht der Mechanismus, sondern

1. ein Korpus, in dem Spalten fertig werden -- sonst sagt der Ownership-Kopf
   voraus, was plattenblindes Spiel erreicht, und routet in die eigene
   Schwaeche ([[feedback_dont_calibrate_to_plate_blind_play]]);
2. `OWNERSHIP_WEIGHT > 0`;
3. die HUELLEN-GEWICHTUNG (Option a) -- nach der Berichtigung unten kein
   Beiwerk, sondern die Stelle, an der Randbedingung und Vorhersage
   zusammenkommen;
4. die KURVE statt der Treppe -- eine Verfeinerung, nicht die Hauptsache.

**BERICHTIGUNG am selben Tag (Nutzer: *"die routing huelle im tiling ist schon
gut"*).** Der Absatz oben warf Huelle und Dreiecksabweichung in einen Topf --
"feste Karte, kein Weitblick". Das ist falsch, und der Unterschied ist die
ROLLE, nicht die Festigkeit:

| Rolle derselben Geometrie | Wert |
| --- | --- |
| Huelle als ROUTING-ZIEL (wohin zielen) | **strukturelle Identitaet**: eine volle Spalte kostet 1+2+3+4+5+6 = 21 Zellen, *unabhaengig davon, wie geschickt platziert wird* (par.1 dieser Prereg, `row_supply_ceiling_probe.py`). Gilt in JEDER Stellung; gemessen 0,798 gegen 0,086 |
| Dreiecksabweichung als VORHERSAGE-ZIEL (was wird belegt) | Umkodierung von "belegt", traegt nichts bei (Nachtrag 2) |

**Die Huelle sagt nichts voraus -- sie kodiert eine Randbedingung.** Deshalb
braucht sie keinen Weitblick: sie behauptet nichts ueber die Zukunft, sondern
beschreibt, was ueberhaupt moeglich ist. Ein Netz muesste die 21-Zellen-
Identitaet aus Daten rekonstruieren; sie hinzuschreiben ist billiger und
sicherer.

**Huelle und Ownership-Kopf sind damit KOMPLEMENTAER, nicht alternativ:**

* die **Huelle** sagt, WO zu zielen ist -- strukturell, immer gueltig;
* der **Ownership-Kopf** sagt, WAS DAVON in dieser Partie fertig wird --
  gelernt, stellungsspezifisch, genau der Weitblick, den die Huelle nicht hat.

**Das ist exakt Option (a), die Huellen-Gewichtung** (Nachtrag 6): die
Loss-Maske auf die 21 Huellen-Zellen konzentrieren. Die Huelle lenkt die
Kapazitaet, der Kopf sagt darin voraus. Sie ist damit **nicht** die
nachrangige Verfeinerung, als die der Absatz oben sie einordnet, sondern der
Kern der Kombination.

**Und der Vorschlag, dem NETZ-Pfad die Routing-Huelle zu geben** (heute
verworfen mit "kein Weitblick"), steht damit wieder: das ist kein Tausch einer
Handregel gegen eine andere, sondern das Mitgeben einer Randbedingung, die
immer stimmt. Er bleibt ein eigener Arm mit Default AUS, weil er den Elo-Anker
beruehrt.

**Was das fuer die Reihenfolge heisst:** die Huellen-Gewichtung (Option a)
bleibt sinnvoll als KAPAZITAETS-Lenkung -- sie schaerft den Kopf dort, wo es
zaehlt, ohne sein Ziel zu ersetzen. Sie ist aber nachrangig gegenueber
"Gewicht ueber null auf plattenbewusstem Korpus", weil ohne das gar nichts
wirkt.

**NACHTRAG 2026-08-25 (8): die Orientierungswahl -- Nutzer-Regel plus Messung**

Offene Frage aus Nachtrag (7): die Huelle hat zwei brauchbare Orientierungen
(oben-links, oben-rechts), und WELCHE gilt, ist stellungsabhaengig -- damit
haengt die Randbedingung scheinbar wieder am Weitblick, den sie ersetzen soll.

**Nutzer-Regel 2026-08-25:** *"es gilt jene, in der bereits mehr steine
liegen."* Sie liest die AKTUELLE Stellung, sagt also nichts voraus -- die
Eigenschaft, die die Huelle wertvoll macht, bleibt erhalten.

**Gemessen (540 Seiten aus 270 hv2-Partien, 2026-08-25):**

| Kennzahl | Wert |
| --- | --- |
| Orientierungs-Wechsel je Seite und Partie | **0,21** im Mittel, max 2 |
| Seiten ganz ohne Wechsel | **82,2 %** |
| Endgueltige Seite | 77 % links / 23 % rechts |
| Zustaende ohne Fuehrung (Gleichstand) | 26.523 |

**Der Kippel-Verdacht aus Nachtrag (5) bestaetigt sich NICHT** -- dort stand,
ein Min-Ziel sei nicht glatt, "welche Orientierung fuehrt, kann von Zug zu Zug
kippen". Einmal in Fuehrung, bleibt es dabei.

**Die Gleichstaende sind kein Mangel, sondern Geometrie.** Die beiden Huellen
UEBERLAPPEN sich in 12 von 21 Zellen; nur 9 je Seite unterscheiden, und die
liegen UNTEN:

```
BBBBBB     B = beide Orientierungen
LBBBBR     L = nur links
LLBBRR     R = nur rechts
LLLRRR
LL..RR
L....R
```

Zeile 0 ist vollstaendig geteilt. Solange oben gebaut wird, GIBT es keine
Fuehrung -- und dann ist die Orientierung auch nicht zu entscheiden.

**Daraus die Regel in ihrer vollstaendigen Form, ohne Notbehelf:**

* **Gleichstand ⇒ nicht entscheiden.** Beide Huellen zeigen auf dieselben 12
  Zellen; dorthin routen. Die Entscheidung wird genau bis zu dem Punkt
  aufgeschoben, an dem die Daten fuer sie existieren.
* **Fuehrung ⇒ dieser Orientierung folgen.** Keine Hysterese noetig, keine
  Verpflichtungsregel -- 82 Prozent wechseln ohnehin nie.

**Offen und unerklaert:** die endgueltige Seite ist 77 Prozent links gegen 23
Prozent rechts. Eine Symmetrie waere zu erwarten gewesen. Verdacht ist der
Eckbonus der Startkuppel-Heuristik (`start_placement_kandidaten`,
self_play.rs:756ff) -- **ungeprueft**. Wer die Orientierungsregel baut, sollte
das vorher klaeren: eine Schlagseite von 3:1 kann eine echte
Brett-Eigenschaft sein oder ein Artefakt einer Handregel, und im zweiten Fall
wuerde die Huelle sie fortschreiben.

**NACHTRAG 2026-08-25 (9): die Huelle ist die Machbarkeitshuelle der AKTIVEN
WERTUNG -- und sie muss ein Gewicht bleiben, kein Filter.**

Nutzer 2026-08-25: *"es kann natuerlich manchmal sinnvoll sein aus der huelle
auszubrechen wenn die joker wertungsplatte aktiv ist um alle jokerplatten zu
schliessen"* -- gefolgt von zwei weiteren Ausbruchsgruenden, siehe unten.

**Kriterium 3 ist "Mehrfarbige Felder": 2 Punkte je Wildcard-Feld, aber NUR
wenn ALLE belegt sind** (scoring.rs:45). Alles-oder-nichts. Liegt auch nur ein
Wild-Feld ausserhalb der Huelle, muss man ausbrechen oder die Platte
abschreiben.

**Gemessen (270 hv2-Partien, 2026-08-25):**

| Kennzahl | Wert |
| --- | --- |
| Partien mit aktivem k3 | **101 von 270 (37 %)** |
| Wild-Felder je Brett | 4,5 im Mittel (2-7) |
| davon AUSSERHALB der Huelle | **1,7** im Mittel |
| Bretter mit mindestens einem ausserhalb | **88-92 %** |

**Aus "manchmal sinnvoll" wird damit "fast immer noetig".** Eine harte Huelle
wuerde die k3-Platte in gut einem Drittel aller Partien verschenken.

**Der tiefere Haken:** bei einem Alles-oder-nichts-Kriterium ist die MARGINALE
eines nicht-letzten Feldes ungefaehr null. Der Ownership-Kopf allein wuerde die
Wild-Investition also nie ANFANGEN -- dieselbe Struktur, aus der die
Spalten-Schwaeche kommt. Auf die Marginalen zu vertrauen reicht nicht.

**Daraus die verallgemeinerte Fassung:**

```
Zielset = Huelle (21 Zellen)                    <- Spalten-Identitaet
        + alle Wild-Felder, wenn k3 aktiv       <- Alles-oder-nichts-Identitaet
```

Das bleibt STRUKTURELL und ohne Weitblick: welche Platten aktiv sind, steht ab
Zug 1 fest, die Wild-Positionen stehen auf dem Brett. Dieselbe Sorte Aussage
wie die 21 Zellen ("das kostet diese Wertung"), nur fuer ein anderes
Kriterium. Bezahlbar ist es auch: 21 + ~1,7 gegen die 60,9 Zellen, die ein
Mensch insgesamt verbraucht.

Damit ist die Huelle nicht mehr die "Spalten-Huelle", sondern die
**Machbarkeitshuelle der AKTIVEN WERTUNG**.

### par.3b.1 Das Gewicht braucht ein Fenster -- und ob es existiert, ist messbar

**BAU-HINWEIS (2026-08-28, aus dem B-Strang):** die Huellen-Geometrie
(`v2_envelope_target` samt Umfeld) ist mit dem B4a-Commit aus dem Quellstand
gefallen (`plate_builder.rs` 2.835 -> 1.422 Zeilen). Wer dieses Fenster baut,
holt die Geometrie aus der Historie VOR B4a; Herleitung in
`archive/history.md` (Kapitel 2026-08-25 bis 2026-08-28, Abschnitt
"B-Block: Planungs-Rueckschau").

Nutzer, zwei weitere Ausbruchsgruende: *"es wird immer wieder situationen
geben wo eine einzelne fliese ausserhalb der huelle platziert wird um keine
strafpunkte zu bekommen oder die reihe abzuschliessen damit sie frei ist fuer
die naechste runde"*. Beides sind Ressourcen- und Tempo-Fragen, keine
Wertungsgeometrie -- und sie begrenzen das Gewicht nach oben.

**`w` braucht zwei Schranken:**

* **Untergrenze:** es muss kleine Sofortpunkte-Unterschiede ueberstimmen
  koennen, sonst wird nie eine Spalte gebaut -- der Solver naehme immer den
  punktereicheren Zug. Das ist der ganze Zweck.
* **Obergrenze:** es darf NIE Strafpunkte in Kauf nehmen oder eine Reihe
  blockiert lassen. Beides kostet mehr als jede Struktur.

**Ob dieses Fenster nicht leer ist, ist eine MESSUNG, keine Designfrage** und
gehoert vor den Bau: wie gross ist der typische Punktunterschied zwischen dem
huellen-optimalen und dem punkt-optimalen Tiling-Zug, und wie teuer ist eine
blockierte Reihe? Liegt das erste ueber dem zweiten, gibt es kein gueltiges
`w` und die Konstruktion faellt -- ein vollwertiges Ergebnis.

**Konsequenz fuer die Bauform, endgueltig:** die Huelle ist ein GEWICHT auf den
Marginalen, kein Filter. Ein hartes Zielset haette alle drei genannten Faelle
ausgeschlossen -- k3-Vervollstaendigung, Strafvermeidung, Reihen-Freimachen.

### par.3b.2 Spalten-Abnahme-Tor (registriert 2026-08-27, VOR dem v22-Training)

**Zweck: das Arena-Gating misst Siege, nicht ob der Mechanismus angekommen
ist.** Der Sanity-Lauf (`PREREG_v22_window.md` par.4a/4b) hat genau diese
Luecke vorgefuehrt: Arm B kam auf 0,113 volle Spalten je Partie, also
Champion-Niveau (0,106) statt Lehrer-Niveau (0,741). Ein Gating haette daraus
"Netz B ist ungefaehr so stark wie der Champion" gemacht und die Frage, ob der
Spaltenbau ueberhaupt uebertragen wurde, offen gelassen. Dieses Tor
entscheidet, ob das v22-Self-Play gestartet wird -- der Lauf, der das
v23-Fenster besetzt (12.000 Partien, `PREREG_v23_window.md` par.2).

**Zeitpunkt:** nach dem v22-Training (beide Arme), VOR dem Start des
v22-Self-Play. Nicht danach, weil ein verfehltes Tor den Lauf gegenstandslos
macht und nicht nachtraeglich billiger wird.

**Stufe-1-Konfiguration, hiermit festgelegt.** Der Messarm ist Arm B
(`MOSAIC_IGNORE_POLICY_TARGET_VALID=1`) mit `--ownership-weight 1.0`, der
Kontrollarm derselbe Aufbau mit `--ownership-weight 0`, auf DEMSELBEN Korpus.
Praezedenz fuer die 1,0: die b-Serie fuhr w=1,0 und w=2,0; die stehende
Freigabe fuer w>1,0 ([[feedback_ownership_weight_may_rise]]) bleibt davon
unberuehrt und gilt fuer spaetere Arme weiter.

**NOTATIONS-KLARSTELLUNG, weil der Platzhalter `<w0>` in aelteren
Befehlsbloecken doppeldeutig war:** "w0-Kontrollarm" bezeichnet das Gewicht
NULL. Der Messarm heisst ab jetzt "w1-Arm" (Gewicht 1,0). Wo `<w0>` als
einzusetzender Wert fuer den Messarm stand, war das ein Schreibfehler, keine
zweite Bedeutung.

**Instrument -- dasselbe wie in par.4a/4b der v22-Fenster-Prereg**, damit die
dort gemessenen Baselines 0,062 (Arm A) und 0,113 (Arm B) vergleichbar
bleiben: argmax-Trajektorien mit `--deterministic --no-root-noise`, 400 Sims,
je Arm 200 Partien in 10 Bloecken zu 20. Gesampeltes Self-Play ist als
Messgrundlage AUSGESCHLOSSEN -- es hat in par.4a die vollen Spalten mehr als
halbiert und misst die Exploration statt des Spiels.

Drei Messreihen: w1-Arm, w0-Arm, und Champion v21 als mit DEMSELBEN Instrument
NEU gemessene Referenz. Die 0,106 aus par.4a stammt aus einem anderen Aufbau
und wird nicht als Vergleichswert eingesetzt; Provenienzen werden nicht
gemischt. Die sechs Standard-Kennzahlen sind Pflicht (CLAUDE.md-Regel:
Reihenauslastung, Spaltenauslastung, Strafleistenauslastung, Punkte je
Wertungsplatte, eigene Punkte, Marge). Laufzeit-Anhaltspunkt: rund 2,6 s je
Partie bei 11 Threads.

**TOR 1 (MECHANISMUS, hart).** Volle Spalten je Partie im w1-Arm signifikant
ueber (a) dem w0-Arm UND (b) der neu gemessenen Champion-Referenz, jeweils
Block-t ueber 2,262 (df=9, zweiseitig 5 Prozent). Verfehlt => KEIN
Self-Play-Start.

Damit ein verfehltes Tor nicht in Neu-Raten muendet, sind die Folgewege hier
BENANNT: Stufe 2 (2D-Ablesung des Ownership-Kopfs, Stufenplan in par.3b), die
Tiling-Kanal-Frage (die +0,199 Wechselwirkung aus `PREREG_v22_window.md`
par.4f), und ein Datenmengen-Check (voller Korpus statt Viertelkorpus -- der
offene Punkt aus par.4b).

**TOR 2 (VOLLENDUNG, B1-Vorgabe).** Vollendungsquote signifikant ueber 0,53
UND Punktschaetzung mindestens 0,60 (Lehrer: 0,717). Die 0,53 ist die Schwelle
aus B1: dort lagen BEIDE Arme bei rund 0,53, der Lauf verglich also zwei
inkompetente Regime ([[project_long_row_avoidance_is_correct]]).

Tor 1 bestanden und Tor 2 verfehlt => Befund dokumentieren, der Start ist dann
Nutzer-Entscheid. Das benannte Risiko ist die B1-Wiederholung: Initiierung
erzwingbar, Vollendungsfaehigkeit nicht -- ein Korpus aus angefangenen und
nicht vollendeten Spalten waere teurer als keiner.

**Berichtsgroessen ohne Torfunktion** (werden erhoben und berichtet, aber
entscheiden nichts): Abstand zum Lehrer (0,741), k1-Anteil, k6-Spezialfelder,
und ein Mechanik-Blick auf die Ownership-Marginalen -- zeigen sie auf
Spaltenzellen? Das trennt "Kopf gelernt, Konsument setzt es nicht um" von
"Kopf nicht gelernt", und nur der erste Fall macht Stufe 2 zum richtigen
Folgeweg.

**TOR GEFAHREN 2026-08-28 (spalten_tor_v22.json, drei argmax-Reihen zu
je 200 Partien, 10 Bloecke, Seeds identisch ueber die Arme):**

| Arm | volle Spalten | Quote vollendet/>=4 | init>=4 je Seite |
| --- | --- | --- | --- |
| Champion (neu, gleiches Instrument) | 0,102 +- 0,015 | 0,049 | 2,08 |
| v22-b01 (w1) | 0,297 +- 0,029 | 0,154 | 1,93 |
| v22-b02 (w0) | 0,260 +- 0,021 | 0,133 | 1,96 |
| Lehrer (Referenz, 100 hv2-Dateien, gleiches Instrument) | 0,742 +- 0,017 | 0,347 | 2,14 |

**TOR 1(b) BESTANDEN:** w1 gegen Champion +0,195, Block-t +5,55 (Schwelle
2,262) -- fast Verdreifachung, hochsignifikant. **TOR 1(a) VERFEHLT:** w1
gegen w0 +0,037, Block-t +1,53. Der Ownership-Kopf traegt den Gewinn NICHT;
der Sprung kommt vom Lehrerkorpus samt neuen Eingaben. **Nach der
vorregistrierten Regel: KEIN v22-Self-Play-Start**, die benannten Folgewege
uebernehmen (par.3b.5-Diagnose entscheidet die Weg-Wahl).

**TOR 2, mit Instrument-Berichtigung:** die registrierten Schwellen
0,53/0,60 stammten aus einer ANDEREN Quoten-Definition (B1-Kontext); mit dem
hiesigen Instrument (vollendet/initiiert>=4 am Endbrett) misst der LEHRER
0,347 -- die Schwellen waren also falsch skaliert und werden nicht
mechanisch angewendet. Substanziell: b01 erreicht 44 Prozent der
Lehrer-Quote. **Strukturbefund des Tors: die INITIIERUNG ist fast geerbt
(1,93 gegen 2,14), die VOLLENDUNG nicht** -- derselbe Engpass wie beim
Champion, eine Etage hoeher.

**Beifang:** die alte Champion-Zahl 0,106 (anderes Instrument) reproduziert
sich hier als 0,102 -- die Provenienz-Trennung war berechtigt, aber die
Groessen decken sich.

**Nachtrag (Nutzer-Entscheide 2026-08-27, am Tag der Registrierung):**

1. **KALTSTART statt Warmstart** ("wir werden einen kaltstart machen und bei
   bedarf afterburnen"). Beide Arme trainieren from-scratch auf dem vollen
   Korpus. Grund: die Sanity-Modelle weichen in der Kopfbestueckung vom
   Champion-Rezept ab (`opp_points_head`/`endgame_head` beide false, am
   Trainings-Manifest geprueft) -- ein Warmstart haette Kopfbestueckung,
   Traegerarm, Ownership-Gewicht und Korpuswechsel in einen Vergleich
   gemengt. Der vorbereitete Warmstart-Aufruf in `PREREG_v22_window.md`
   par.6 ist damit ueberholt (er lud zudem `hv2sanity_best`, also Arm A).
   `MOSAIC_VAL_POOL` entfaellt fuer den Kaltstart und greift erst wieder,
   falls der Afterburner als Warmstart auf demselben Korpus laeuft.
2. **Rolle des Gatings:** v22 tritt im normalen Gating gegen den Elo-Anker
   und gegen v21 an. Die Promotion ist ausdruecklich NICHT Voraussetzung
   fuer den Self-Play-Start ("ich geh nicht davon aus dass v22 besser ist
   als v21. wichtiger ... ist jedoch ob der spaltenbau uebernommen wurde").
   Ueber den Start entscheiden allein Tor 1 und Tor 2 dieses Absatzes; das
   Gating liefert die Elo-Einordnung.

### par.3b.3 Alternativplan Label-Qualitaet (Nutzer-Auftrag 2026-08-27: "dann brauchen wir einen alternativplan falls uns v21 die labels im rundenuebergang zerschiesst")

**Das Risiko, als Herleitung markiert:** das Value-Ziel ist der TD-Blend
`TD_LAMBDA * bootstrap + (1 - TD_LAMBDA) * Ausgang` mit `TD_LAMBDA = 0,5`
(Blend bei der Zielkonstruktion, corpus_dataset.py:919 fuer WDL;
`bootstrap_value` ist ein gespeichertes Record-Feld). Die Bootstrap-Haelfte
ist die Meinung des v21-Label-Netzes -- und dessen Value-Kopf traegt die
gemessene PLATTEN-Daempfung (R5-Plattensteigung 0,06-0,09 statt ~1,
`PREREG_r5_solver_split.md` par.3e). Die Bootstrap-Haelfte koennte
Spaltenfortschritt also genau dort unterbewerten, wo der Korpus ihn lehren
soll. Plattenwahr sind dagegen die Ausgangs-Haelfte und die Ownership-Ziele
(echte Endbretter) -- zwei eingebaute Hedges, der w1-Arm aktiviert den
zweiten.

**Stufe 0 -- VORAB-SONDE (vor dem Training fahrbar, reine Datenpassage ohne
Engine):** auf dem fertigen Korpus je Rundenuebergangs-Record den
gespeicherten Bootstrap gegen den realisierten Ausgang stellen, gebinnt nach
Spaltenfortschritt der Stellung (`col_f_max`-Maximum der eigenen Seite; das
Feld steht seit dem Erzeugungs-Wheel in jedem Zustand). Vorab festgelegte
Lesart: **Daempfung bestaetigt**, wenn das mittlere Residuum
(Ausgang minus Bootstrap, auf der Gewinnskala) ueber die Fortschritts-Bins
monoton waechst UND im obersten Bin ueber +0,05 liegt (Block-SE auf
Dateiebene). Dann wird Arm L PFLICHTARM des v22-Trainings statt Reserve.
Werkzeug-Praezedenz: `tools/probes/bootstrap_horizon_paired_probe.py` liest
dieselben Felder.

**Arm L -- TD_LAMBDA-Leiter (kein Neu-Labeln, kein Neu-Erzeugen):**
identisches Training, `TD_LAMBDA` 0,5 -> 0,25 -> 0,0 als Leiter auf
DEMSELBEN Korpus. `TD_LAMBDA` steht im Cache-Schluessel
(corpus_dataset.py:388, nach dem Retrain-Sweep-Audit nachgeruestet) -- die
Arme koennen sich also keinen falschen Cache teilen. Preis, aus v11
gemessen: der TD-Bootstrap hob damals erstmals das R1/R2-R2 -- reiner
Ausgang ist verrauschter. Deshalb Leiter statt Sprung, und Arm L nur bei
Sondenbefund (Stufe 0) oder verfehltem Spalten-Tor mit Value-Diagnose.

**Arm R -- Neu-Labeln der Bootstrap-Haelfte (erst NACH v22):** das
`bootstrap_value`-Feld der Records mit einem besseren Bewerter (dem
v22-Netz) neu schreiben; alle uebrigen Felder unangetastet, kein Neu-Spielen
-- reine Vorwaertspaesse an den Uebergaengen. Ergebnis waere ein
v22b-Training im Afterburner-Muster. Arm R setzt voraus, dass v22 die
Plattendaempfung nachweislich reduziert hat (R5-Plattensteigungs-Messung am
v22-Kopf), sonst tauscht man einen gedaempften Bewerter gegen den naechsten.

**BERICHTIGUNG der Arm-R-Vorbedingung (2026-08-27, nach dem Stufe-0-Lauf):**
die eben genannte Bedingung ist STRUKTURELL UNERFUELLBAR. Stufe 0 hat gezeigt,
dass es die Plattendaempfung im Bootstrap gar nicht gibt (Residuum ueberall
negativ, oberster Bin -0,0150 gegen eine Schwelle von +0,05) -- eine Messung,
die ihre "Reduktion" nachweist, kann es also nicht geben. **NEUE Bedingung:**
Arm R setzt voraus, dass v22 den GLOBALEN Versatz gegen DENSELBEN Korpus
senkt, gemessen mit DERSELBEN Sonde
(`tools/probes/bootstrap_plate_damping_probe.py`, voller Lauf 727 s). Damit
haengt der Arm an einer Groesse, die die Sonde tatsaechlich ausweist, und der
Vergleich bleibt gepaart auf denselben Zustaenden.

**Reihenfolge:** Stufe 0 vor dem Training; L und R sind BENANNTE Folgewege
des Spalten-Tors (par.3b.2), keine Parallelarme des Erstlaufs.

**Nachtrag Stufe 0 (2026-08-27, VOR dem vollen Sondenlauf; der Smoke war
Instrumententest):** Der Sondenbau fand ZWEI Fehler in dieser Registrierung
und EINEN im Zielbau selbst.

1. **Binning-Feld berichtigt:** `col_f_max` ist die ERREICHBARE Fuellung
   (serialize.rs:232-234, startet bei 6 und faellt) -- als Fortschritts-Bin
   fast ohne Aufloesung (Smoke: 4373 von 4386 Records in Bin 6). Gemeint war
   der GEBAUTE Fuellstand. Das Tor laeuft auf
   `max(score_geo.col_fill)` (serialize.rs:200), Bins unveraendert
   0-2/3/4/5/6; die `col_f_max`-Tabelle laeuft als Zusatz ohne Torfunktion
   mit.
2. **Skala berichtigt:** getort wird auf der ZIEL-AEQUIVALENTEN Skala --
   dem Wert, der tatsaechlich in `value_wdl` geblendet wird -- nicht auf dem
   rohen Speicherfeld. Beide Tabellen stehen im Artefakt.
3. **FUND im Zielbau (Nutzer-Entscheid 2026-08-27, VOR dem v22-Training zu
   beheben):** `WDL_GENERATOR_PREFIXES` (neural_net.py:759) kennt
   `selfplay_hv2` nicht; der NATIVE WDL-Bootstrap des v21-Label-Netzes wird
   dadurch faelschlich Platt-entstaucht (corpus_dataset.py:917-919,
   B=1,9269). Nutzer: *"das muessen wir sowieso anders loesen. wir haben
   keine gestauchten netze mehr. das war nur ein fix."* Beschlossene Form:
   **native ist der DEFAULT**; die Entstauchung wird zur Alt-Mechanik, die
   nur noch fuer eine explizite Blockliste alter tanh-Aera-Praefixe greift
   (heutiger data/-Bestand: ausschliesslich hv2). Der Umbau aendert die
   Zieldefinition und braucht deshalb eine eigene Cache-Key-Komponente und
   einen Test, der den hv2-Fall (nativ, unveraendert) und den Alt-Fall
   (entstaucht) fixiert. Nach dem Fix ist Punkt 2 gegenstandslos vereinfacht:
   Zielskala = Rohwert.

   **GEBAUT UND ABGENOMMEN 2026-08-27, noch am selben Tag.** Konstante
   heisst jetzt `LEGACY_STRETCHED_PREFIXES` (fuenf tanh-Aera-Praefixe:
   v10b/v12/v16/v17/v18, Inventur ueber data/, holdout/ und das
   v20-Traeger-Manifest); der v20-Traeger-Kurzschluss bekam eine EIGENE
   eingefrorene Konstante (`V20_CARRIER_SHORTCUT_PREFIXES`), weil die alte
   Liste ZWEI Aufgaben hatte und die Umkehr ihn sonst still mitgedreht
   haette. Beide Cache-Schluessel tragen den Status. Abnahme:
   `tools/probes/bootstrap_native_default_probe.py` GRUEN (Blend unabhaengig
   nachgerechnet, nativ=roh und alt=entstaucht auf 1733 Records, Delta der
   beiden Welten bis 0,0715, per-Datei-Schluessel trennt); vom Koordinator
   selbst nachgefahren. Die Sonde dieser Stufe laeuft seither auf
   `col_fill`-Tor und Rohskala (Punkte 1 und 2 umgesetzt); dabei zwei
   latente Fehler der Erstfassung behoben (Signatur-Absturz am Laufende,
   nie initialisierter Zaehler).

**STUFE 0 GEFAHREN 2026-08-27, voller Korpus (2.400 Dateien, 727 s):
DAEMPFUNG NICHT BESTAETIGT.** Das Residuum (Ausgang minus Bootstrap, roh,
eigene Seite, col_fill-Bins) ist ueberall NEGATIV und steigt monoton gegen
null: -0,0685 / -0,0504 / -0,0408 / -0,0286 / **-0,0150** (Block-SE im
obersten Bin 0,0050 auf 2.399 Bloecken; Schwelle war +0,05). Der
Smoke-Wert +0,113 war ein n=3-Artefakt. Lesart: das v21-Label-Netz ist
GLOBAL um ~5-7 Prozentpunkte zu optimistisch (seitensymmetrisch, Sanity
bestanden), und spaltenreiche Stellungen sind die am BESTEN kalibrierten
-- die Bootstrap-Haelfte unterbewertet Spaltenfortschritt im geblendeten
Ziel also NICHT. Nach der vorab registrierten Regel: **Arm L bleibt
RESERVE**, der Kaltstart faehrt mit Standard-TD_LAMBDA 0,5. Formaler
Grenzfall-Ausweis (Monotonie haelt, Schwelle klar verfehlt) steht im
Artefakt `evaluations/artifacts/bootstrap_plate_damping.json`. Beifang
ohne Torfunktion: die Optimismus-Konstante (~+0,05 auf beiden Seiten,
Summe der Gewinnwahrscheinlichkeiten ueber 1) ist ein KALIBRIER-Befund
am v21-Value-Kopf, kein Platten-Befund; Runde 4 ist fast kalibriert
(-0,018), Runde 1-3 tragen den Versatz.

**Arm K -- Bootstrap-Kohaerenz (ENTWURF 2026-08-27, Nutzer-Entscheid offen)**

**Befund-Basis:** Stufe 0 fand statt der vermuteten Plattendaempfung einen
GLOBALEN Optimismus-Versatz -- rund +0,05 je Seite, beidseitig, die Summe der
beiden Bootstrap-Gewinnwahrscheinlichkeiten liegt bei ~1,13-1,14 statt bei 1.
Ein Spiegelungs-Artefakt ist das nicht: `MIRROR_OTHER_VAL` steht auf `false`
(net_mcts.rs:670), `net_leaf_eval` rechnet also fuer Zieher und Gegner ZWEI
UNABHAENGIGE Vorwaertspaesse (Agent-geprueft, net_mcts.rs:1503-1534). Beide
Werte kommen aus demselben Kopf, aber aus verschiedenen Eingaben -- nichts
zwingt sie auf Summe 1.

**Idee:** die beiden Bootstrap-Werte je Zustand VOR dem TD-Blend auf Summe 1
normieren ODER den auf hv2 gefitteten affinen Versatz herausrechnen. Beides
ist eine reine LABEL-Transformation im WDL-Zweig von `corpus_dataset`, kein
Neu-Spielen und kein Engine-Eingriff. Eine eigene Cache-Key-Komponente ist
PFLICHT -- dieselbe Auflage wie beim Nativ-Default (Punkt 3 oben); ohne sie
teilen sich beide Welten still denselben Cache.

**Herleitung, als solche markiert (nicht gemessen):** ein fuer alle
Geschwister gleicher additiver Versatz hebt sich unter Softmax weg, ist also
SUCH-neutral -- aber nicht LABEL-neutral. Mit `TD_LAMBDA = 0,5` gehen rund
+0,03 je Seite systematisch ins v22-Value-Ziel, und ueber das v22-Self-Play
wandern sie weiter ins v23-Fenster.

**Praezedenz, die der Leser sehen muss:** eine Kohaerenz-Erzwingung zur
SUCHZEIT gab es bereits -- `MIRROR_OTHER_VAL` setzt `other_val = 1 - mover_val`
aus EINEM Vorwaertspass. Sie wurde arena-getestet (3:97) und auf `false`
zurueckgesetzt (net_mcts.rs:663-670). Arm K sitzt an einem ANDEREN
Eingriffsort: nicht am Blattwert der laufenden Suche, sondern am gespeicherten
Label des Trainingsziels. Das entwertet den Praezedenzfall nicht, es grenzt
ihn ab.

**Quer-Beleg, der die Reichweite begrenzt:** `tools/platt_fit.py` und
`evaluations/artifacts/platt_fit_v21.json` finden auf dem FROZEN-Set
A = -0,0033 und B = 0,906, also praktisch KEINEN Versatz. Der Versatz existiert
nur auf der LEHRER-Verteilung. Das ist genau das Muster "nie auf der falschen
Verteilung eichen" ([[feedback_dont_calibrate_to_plate_blind_play]]), diesmal
in Gegenrichtung: eine Eichung, die auf der einen Verteilung stimmt, sagt
ueber die andere nichts.

**Leitstern-Ehrlichkeit:** der Staerkebeitrag ist UNBELEGT. Ein globaler
Versatz laesst die Ordnung unveraendert, und die Suche entscheidet nach
Ordnung. Das Argument sind IRRTUMSKOSTEN fuer alles, was Absolutwerte liest:
die risikosensitive Blatt-Utility Stufe A
(`PREREG_risk_sensitive_leaf_utility.md`), die saettigende Score-Utility und
die WDL-Klassen. Die Infrastruktur-Regel verlangt einen BENANNTEN
Nutzniesser -- diese drei sind es.

**Entscheid faellt der Nutzer.** Bei JA ist der Arm nach dem laufenden
Kaltstart als v22b-Retrain nachholbar: zwei Arme auf DEMSELBEN Korpus,
Entscheid an Brier PLUS Arena.

**ARM K GEBAUT 2026-08-30 -- Form: SUMMEN-NORMIERUNG, Default AUS.**
Einaktung: `PREREG_v23_window.md` par.4a2 (Nutzer-Entscheid 2026-08-29
"takte es dort ein"), faellig VOR dem v23-Training. Gebaut wurde der
Knopf, NICHT eine Default-Aenderung -- der Bestandspfad bleibt
bit-identisch.

* **Gewaehlte Form (Entscheid des Koordinators, hier registriert):** von
  den beiden registrierten Formen die **Summen-Normierung**
  (`MOSAIC_BOOTSTRAP_COHERENCE=sum1`), nicht die affine
  Versatz-Korrektur. Grund ist der Quer-Beleg dieses Absatzes selbst: der
  Versatz existiert nur auf der LEHRER-Verteilung
  (`platt_fit_v21.json`: A -0,0033, B 0,906 auf dem Frozen-Set). Eine auf
  hv2 gefittete Konstante auf den v22-b05-Korpus anzuwenden waere genau
  die Falle "nie auf der falschen Verteilung eichen". Die Normierung
  braucht keine gefittete Konstante; sie erzwingt die Kohaerenz je
  Zustand aus den beiden Werten DIESES Zustands. Die affine Form bleibt
  registriert und ungebaut.
* **Eingriffsort** (corpus_dataset.py, WDL-Zweig, vor dem TD-Blend):
  `bvp <- bvp / (bvp + bvo)`. Der Gegner-Wert durchlaeuft dieselbe
  Entstauchungs-Fallunterscheidung wie der eigene -- sonst normierte man
  zwei Werte verschiedener Skalen gegeneinander. Summe 0 laesst den
  Rohwert stehen.
* **UMFANG, ausdruecklich:** nur der WDL-Zweig (`values_wdl`), wie
  registriert. Der [-1,1]-Zweig (`val`/`points_val`/`opp_points_val`)
  bleibt unangetastet.
* **Cache-Key-Komponente** (in der Registrierung PFLICHT) in BEIDEN
  Namensraeumen: `+bscoh_sum1_v1` im Fenster-Schluessel
  (corpus_dataset.window_cache_key) und `|bscoh_sum1_v1` im
  Datei-Schluessel (file_cache_key.per_file_cache_key). NUR bei aktivem
  Knopf angehaengt -- kein Bestands-Cache verfaellt, und der Co-Bau darf
  weiterlaufen.
* **Manifest:** `bootstrap_coherence` in `cli_args` (train.py), nach der
  Regel der Zeile darueber (`ignore_policy_target_valid`): ein Knopf, der
  die Zieldefinition aendert, gehoert ins Manifest und nicht nur in den
  Cache-Key.
* **Tippfehler = Abbruch**, nicht stilles "off"
  (`_bootstrap_coherence_mode` wirft bei unbekanntem Wert), plus
  Log-Ansage bei aktivem Arm.
* **Abnahme gebaut, LAUF STEHT AUS:**
  `tools/probes/bootstrap_coherence_probe.py` nach dem Muster von
  `bootstrap_native_default_probe.py` -- (A) off = Bestands-Blend,
  (A') ungesetzt = off, (B) sum1 = unabhaengig nachgerechneter
  normierter Blend, (C) Gegenprobe off != sum1, (D) beide Schluessel
  trennen und off trifft den ungesetzten Schluessel, (E) Berichtsgroessen
  (Paarsumme, Ziel-Verschiebung). Nicht gefahren, weil die v22-b05-
  Erzeugung exklusiv laeuft (Regel "Messungen laufen exklusiv"); der Lauf
  gehoert in dieselbe Stunde wie die Nach-Erzeugungs-Waechter.
* **Was damit NICHT entschieden ist:** ob das v23-Training mit `sum1`
  faehrt. Das bleibt die registrierte Arm-Frage (zwei Arme auf DEMSELBEN
  Korpus, Entscheid an Brier PLUS Arena). Der Bau macht sie
  entscheidbar; der Default bleibt bis dahin "off".

**EINTAKTUNG ENTSCHIEDEN 2026-08-31 (Nutzer): VERSCHOBEN, nicht verworfen --
"der hat mich noch nicht ueberzeugt".** Der Arm bleibt gebaut und
ausloeserbasiert in Reserve; die vorhandenen Caches werden zuerst
ausgenutzt. Das inhaltliche Argument fuer die Zurueckstufung steht in
par.3b.3a. Nutzer: *"den wuerd ich relativ spaet
eintakten und die vorhandenen caches erstmal ausnutzen."* Konkret:

* `v23-b01` (Warmstart), `v23-b02` (Kaltstart, Bestandsbreite), `v23-b03`
  (Ueberraschungs-Gewichtung) und `v23-b04` (Breite) fahren **ohne** Arm K --
  `MOSAIC_BOOTSTRAP_COHERENCE` bleibt ungesetzt, der Datei-Schluessel
  unveraendert, die 2.400 hv2- und alle b05-Bloecke bleiben gueltig.
* Arm K wird ein **eigener, spaeter Arm auf DEMSELBEN Korpus** -- genau die
  Bauform, die dieser Absatz von Anfang an vorgesehen hat ("zwei Arme auf
  demselben Korpus, Entscheid an Brier PLUS Arena"). Der Name folgt der
  Ausfuehrungsreihenfolge (heute geplant: nach b04).
* Der Preis ist benannt und akzeptiert: sein Lauf zahlt den Block-Neubau
  allein (alle Bloecke bekommen `+bscoh_sum1_v1`). Das ist der Grund fuer die
  spaete Eintaktung, nicht ein Zweifel am Arm.

**Was sonst noch Bloecke entwertet, damit es niemand versehentlich
mitfaehrt** (aus dem Schluesselmaterial, file_cache_key.py:80-106): ein
Traeger-Manifest (`carrier`), `MOSAIC_IGNORE_POLICY_TARGET_VALID`, eine
geaenderte `TD_LAMBDA` (Arm L), ein anderer `value_target_variant`,
`MOSAIC_CACHE_F32`, `MOSAIC_CACHE_NOPACK`. Wer Cache-Ausnutzung will, laesst
diese sechs in b01-b04 unangetastet.

### par.3b.3a Warum Arm K NICHT oben auf der Value-Liste steht (2026-08-31)

Nutzer: *"arm K hoert sich von der prioritaet nicht hoch an wenn ich unsere
anderen preregs in bezug auf die value head thematik ansehe"* -- und das
laesst sich schaerfer sagen als nach Gefuehl:

1. **Arm K korrigiert einen VERSATZ, das gemessene Problem ist eine
   STEIGUNG.** Die R5-Kalibrierung misst 0,0886 statt ~1. Ein fuer beide
   Seiten gleicher additiver Optimismus verschiebt den Achsenabschnitt, nicht
   die Steigung; Arm K kann die Betrags-Daempfung per Konstruktion nicht
   heilen.
2. **Seine benannten Nutzniesser existieren nicht.** Die Registrierung nennt
   risikosensitive Blatt-Utility, saettigende Score-Utility und die
   WDL-Klassen -- alle drei ungebaut. Ein Hygiene-Fix fuer Leser, die es noch
   nicht gibt.
3. **Er ist der einzige Arm, der ALLE Cache-Bloecke entwertet** (eigene
   Key-Komponente in beiden Namensraeumen). Der Preis faellt also voll auf
   seinen Lauf.

**Nuance, als Herleitung markiert, damit die Zurueckstufung nicht mehr
behauptet als sie darf:** ganz steigungsneutral ist die Summen-Normierung
nicht. Stufe 0 fand das Residuum nach Spaltenfuellstand gebinnt MONOTON
(-0,0685 bis -0,0150) -- spaltenreiche Stellungen sind am besten kalibriert.
Der Versatz ist also nicht exakt konstant; ihn herauszurechnen traefe
spaltenarme Zustaende staerker, der Rest-Effekt auf die Steigung waere klein,
aber nicht null. Die Abnahmesonde weist das in Kennzahl E aus, sobald sie
laeuft.

**Vorrang stattdessen** (nach dem, was gemessen ist): (1) Phase 3,
Betrags-Schiene (`PREREG_r5_value_calibration.md`, Erfolgstest "kippt die
Sims-Kurve?"); (2) Value tief nachlabeln
(`PREREG_reanalyze_label_depth.md` Teil B -- fuer die VALUE-Seite gilt der
Spaltenblindheits-Einwand ausdruecklich nicht); (3) die On-Policy-Exposition,
die der laufende Korpus liefert (die Wette von Zuschnitt D). Arm K steht
hinter allen dreien.

**WAECHTER GEFAHREN 2026-08-31 NACH DER ERZEUGUNG -- BEIDE BESTANDEN, GO
FUER DAS v23-TRAINING.** Korpus: 12.000 Partien des Generators v22-b05
(6.000 value-argmax + 2.000 value-sampled + 4.000 policy), erzeugt
2026-08-30 19:25 bis 2026-08-31 07:20.

**(a) PRIMAER, Symmetrie-Trennung auf der VALUE-Klasse: TRENNT.**
Punkt-biseriale Korrelation der vollen Spalten mit dem Ausgang, Block-Ebene
ueber 398 Dateien: **+0,4041 +- 0,0192 (SE 0,0098, t 41,26)**; Sieger minus
Verlierer +0,3940 (t 33,11). Nebengroesse Fuellstands-Summe +0,5361 (t 71,47).
8.000 von 8.000 Partien gewertet, 1.399.446 Records, kein Ausfall
(corpus_symmetry_v22b05_value.json, 346 s). **Einordnung, ehrlich:** der
hv2-Lehrerkorpus lag bei +0,573 (t 93) -- die Trennung ist SCHWAECHER als
beim Lehrer, was zur niedrigeren Vollendungsrate passt (b05 baut weniger
Spalten, also entscheidet die Groesse seltener die Partie). Das Tor fragt
nach "signifikant > 0", und das ist mit t 41 nicht knapp.

**(b) SEKUNDAER, Ereigniszahl: 5.629 von 16.000 Partien-Seiten der
Value-Klasse tragen mindestens eine volle Spalte** -- Schwelle 1.500, also
das **3,75-fache**. Kein Degenerations-Fall.

**(c) BERICHTSGROESSEN, und eine davon ist ein eigener Befund.** Volle
Spalten je Partie und Seite: Value-Klasse **0,481**, Policy-Klasse 0,129
(Referenzen: argmax@400 0,3375, gesampelt@400 0,07-0,11, Champion 0,102).

Die 0,481 der Value-Klasse liegt UEBER dem argmax-Instrumentwert, und das
ist keine Anomalie, sondern die Vorhersage der Sims-Kurve: sie besagt
~0,6 volle Spalten bei 25-100 Sims gegen 0,34 ab 250. Nachgerechnet aus den
beiden registrierten Vorbefunden -- 6.000 argmax bei ~0,6 plus 2.000
gesampelt bei ~0,10 -- ergibt (6000*0,6 + 2000*0,10)/8000 = **0,475**
erwartet gegen **0,481** gemessen. Sims-Kurve und Sampling-Leiter, beide auf
200-Partien-Stichproben registriert, treffen damit auf 8.000 Partien
unabhaengig zu.

Weitere Kennzahlen (Value / Policy): eigene Punkte 39,42 / 22,37,
Strafleiste 7,14 / 10,42 Steine, volle Reihen 0,141 / 0,094, k1-Punkte
3,55 / 0,86, k6 Spezialfelder -10,51 / -11,42. **Der Preis des Samplings ist
in der Policy-Klasse deutlich sichtbar** -- 17 Punkte weniger und drei
Strafsteine mehr je Seite. Das ist der bewusste Zuschnitt-D-Handel
(Zustandsabdeckung gegen Spielqualitaet), aber der Abstand ist groesser als
die Leiter mit 200 Partien vermuten liess.

**Traeger-Manifest gebaut** (`data/policy_carrier_manifest_v23.json`):
180 hv2-Dateien (Seed 20260921, aus den 1.745 Fensterdateien von Seed
20260920) = 1.800 policy-aktive Lehrerpartien, plus die Policy-Klasse
VOLLSTAENDIG (200 Dateien = 4.000 Partien) ueber `--include-glob`. Die
Value-Klasse ist bewusst NICHT gelistet. Geprueft: 380 Eintraege, Policy-
Klasse vollzaehlig, alle hv2-Traeger im Fenster, kein `carrier_prefixes`.

### par.3b.4 Symmetrie-Pruefung des Lehrerkorpus (registriert 2026-08-27, VOR der Tor-Auswertung von par.3b.2)

**Der Mechanismus ist in diesem Projekt schon einmal aufgetreten.**
`DOSSIER_ownership_head.md` Abschnitt 7, Punkt 1 haelt fest: die Bauer-Knoepfe
waren ein Prozess-Schalter ohne Spielerparameter, in den Bauer-Armen bauten
BEIDE Spieler, damit war das Value-Ziel bezueglich des Plattenbaus
wegsymmetrisiert -- und der Value-Kopf hat ueber den WERT des Plattenbaus
nichts gelernt, "nicht das Falsche, sondern nichts".

**Der hv2-Korpus hat dieselbe Bauform.** Er laeuft mit `v2huelle` auf BEIDEN
Seiten (`PREREG_v22_window.md` par.2, Aufruf
`--mode mcts --heuristik-variante v2huelle --sims 600 --threads 11 --version hv2
--per-file 10`). Bauen beide, trennt Spaltenbau Sieg nicht von Niederlage --
und der Value-Kopf koennte ueber den Wert des Spaltenbaus wieder nichts
lernen, obwohl der Korpus ihn im Uebermass zeigt (0,732 +- 0,007 volle Spalten
je Seite, `STATUS.md`). **Das ist eine HERLEITUNG aus der CLI-Zeile, nicht
gemessen** -- genau darum diese Pruefung.

**Stufe 0 (baufrei am Korpus, kein Netz, keine Engine):** je Partie die
SPALTEN-DIFFERENZ der beiden Seiten bilden -- volle Spalten des Siegers minus
die des Verlierers, dazu dieselbe Differenz auf `col_fill` -- und gegen den
Ausgang stellen. Ausgewertet wird auf BLOCK-Ebene je Datei (stehende Regel;
Paar-SEs unterschaetzen massiv).

**Vorab festgelegte Lesart:**

* **Trennt die Differenz den Ausgang NICHT** (punkt-biseriale Korrelation,
  Block-KI schliesst die 0 ein), dann misst par.3b.2 nur Policy-VERHALTEN,
  waehrend der Value-Kopf blind bleibt. Das Tor-Ergebnis ist dann entsprechend
  zu ETIKETTIEREN, und der w1-gegen-w0-Vergleich beantwortet die WERT-Frage
  NICHT -- er beantwortet nur, ob der Ownership-Kopf das Verhalten bewegt.
* **Trennt sie den Ausgang**, ist die Sorge vom Tisch und par.3b.2 laeuft
  unveraendert.

**Werkzeug:** `tools/probes/corpus_column_outcome_symmetry_probe.py`, NEU
geschrieben nach dem Lade-Muster von `bootstrap_plate_damping_probe.py`
(dieselbe `corpus_io`-Passage, Fortschrittszeilen mit `flush`,
`laufzeit`-Block im Artefakt, `--limit` fuer den Smoke). Geschrieben und als
3-Dateien-Smoke abgenommen am 2026-08-27; der VOLLE Lauf steht aus, weil ein
Cache-Bau die Maschine belegte (Regel "Messungen laufen exklusiv").

**Konsequenz-Kette, damit die Reihenfolge nicht verrutscht:**

1. Das Ergebnis gehoert VOR die Interpretation des Spalten-Tors (par.3b.2).
2. Die Wiederaufnahme des Bootstrap-Horizonts
   (`PREREG_bootstrap_horizon.md`; im Recherche-Abgleich vom 2026-08-27 als
   "P5" gefuehrt) kommt erst DANACH. Sieht der Value-Kopf Spalten gar nicht,
   misst ein Horizont-Vergleich wieder das falsche Regime -- derselbe Fehler
   wie in par.9g dort, nur an anderer Stelle.

**par.3b.4 GEFAHREN 2026-08-28, voller Korpus (24.000 Partien): TRENNT.**
Volle Spalten, Sieger minus Verlierer: +0,573 +- 0,012 (Block-SE 0,0061,
t +93,4 auf 2.400 Bloecken); punkt-biserial +0,597 gepoolt. Nebengroesse
col_fill_sum ebenso (+1,43, t +97). Die Block-KI schliesst die 0 weit aus --
die Symmetrie-Sorge aus DOSSIER Abschnitt 7 Punkt 1 uebertraegt sich NICHT
auf hv2: beide Seiten spielen zwar dieselbe Huelle, aber der Spaltenbau
trennt den Ausgang trotzdem. Das Spalten-Tor par.3b.2 misst also nicht nur
Policy-Verhalten -- der Value-Kopf hatte die Chance, den Spaltenwert zu
lernen. Artefakt: corpus_column_outcome_symmetry.json (711 s).

### par.3b.5 Orakel-Treue-Diagnose mit TIEFEN-Aufschluesselung (registriert 2026-08-28, VOR der Messung)

**Anlass, am Artefakt verifiziert:** beide Heuristik-Artefakte tragen
DASSELBE Wheel (md5 3aebff8b356387686da71032a707ac17 in hv1_anchor und
hv2_generator) -- der Tiling-Loeser-Kern ist identisch, der Variantenname im
Spec schaltet nur die v2-Routing-Huelle dazu. Der hv2-Korpus wurde also
GEKOPPELT erzeugt (Draft-Huelle + Tiling-Routing), waehrend das Netz zur
Spielzeit greedy kachelt. HERLEITUNG daraus (nicht gemessen): b01s
Draft-Erbe wurde auf Zwischenzustaenden gelernt, die das v2-Tiling geformt
hat; das eigene Greedy-Tiling schiebt das Netz von dieser Verteilung weg,
und eine imitierte Policy verliert ihre Treue zuerst dort. Der Split-Arm
par.4f (Huelle nur im Drafting, Tiling greedy: 0,756 volle Spalten) belegt
die DECKE des Greedy-Tilings, nicht die Korpus-Konfiguration.

**Messung:** die zwei validierten Orakelmetriken (prior_mass_on_oracle_top3,
kendall_tau; 7/7 Arena-Praediktoren) auf b01s Policy, Referenz = die
Lehrer-Zuege des hv2-Korpus, ZUSAETZLICH AUFGESCHLUESSELT NACH SPIELTIEFE
(Bins: Runde 1 / 2 / 3 / 4; innerhalb der Runde frueh/spaet nach Zugindex,
wenn n es traegt). Block-SE auf Dateiebene.

**Vorab festgelegte Lesarten (Nutzer-Auftrag 2026-08-28):**

1. Treue frueh HOCH, faellt mit der Tiefe => ZUSTANDS-DRIFT-These: das
   Draft-Erbe ist da, die Tiling-Differenz entzieht ihm den Boden. Hebel:
   Tiling-ABSICHT zur Spielzeit (MOSAIC_OWNERSHIP_TILING_W mit b01-Kopf)
   und/oder On-Policy-Nachschaerfung.
2. Treue schon FRUEH niedrig => DESTILLATIONS-These: das Erbe kommt gar
   nicht erst an. Hebel: Surprise-Weighting (PREREG_policy_surprise_weighting,
   waere v22-b03).
3. Treue ueberall hoch UND Spalten trotzdem bei ~0,3 => die Tiling-These in
   ihrer starken Form (Platzierung verschenkt korrekt gedraftete Steine);
   dann traegt der Ownership-Pol-Arm die Beweislast.

Schwellen bewusst qualitativ (hoch/niedrig relativ zwischen den Tiefen-Bins,
Block-KI getrennt); es ist eine DIAGNOSE zur Weg-Wahl, kein Staerke-Tor.
Reihenfolge: nach b02 und dem Spalten-Tor par.3b.2, vor der Wahl von
v22-b03.

**par.3b.5 GEFAHREN 2026-08-28 (300 Dateien, b01+b02, 859 s;
policy_teacher_fidelity.json): LESART 3 -- die STARKE TILING-THESE.**
Vorzugs-Haelfte (one-hot, exakt der gespielte Lehrerzug): Masse 0,806 (R1)
-> 0,600 (R4), Lift 28x ueber Zufall, spaet/frueh innerhalb der Runden
1,02-1,06 -- das Draft-Erbe IST angekommen, bei b01 und b02 identisch (das
Ownership-Gewicht beruehrt die Policy-Loss nicht). Zusammen mit par.3b.2
(Initiierung fast geerbt, Quote 0,154 gegen 0,347) verschenkt die
PLATZIERUNG korrekt gedraftete Steine. Die Such-Haelfte etikettiert
"Destillation" (Lift 1,36), misst aber gegen den MODALEN Zug unter
Temperatur -- weiche Referenz, im Artefakt ausgewiesen; die
Vorzugs-Haelfte traegt.

**WEG-WAHL (Empfehlung des Koordinators, registriert 2026-08-28):**

1. **Vor jedem weiteren Training: der Ownership-Pol-KONSUMENT zur
   Spielzeit** -- MOSAIC_OWNERSHIP_TILING_W-Sweep mit b01s erstmals
   spaltenbewusst trainiertem Kopf, argmax-Instrument des Tors, Mass =
   Vollendungsquote + volle Spalten gegen den w=0-Konsum desselben
   Modells. Lesart 3 legt die Beweislast exakt dorthin (die
   Gate-C-Nullmessungen liefen mit plattenblinden Koepfen, par.4e der
   Fenster-Prereg); kostet Arenen, kein Training. Traegt er -> Knopf in
   die Self-Play-Spec, v22-Self-Play-Start zurueck auf den Tisch.
2. **b03-Training nur falls (1) leer:** dann Stufe 2 (2D-Ablesung, par.3b
   Stufenplan -- schaerfere Karten fuer denselben Konsumenten) VOR
   Surprise-Weighting, dessen Ziel (Draft-Treue) auf der tragenden
   Haelfte bereits weitgehend erreicht ist.
3. Der Vollendungs-Filter (v23-Weckerliste) bleibt der komplementaere
   Such-Hebel fuer dieselbe Engpass-Stelle.

### par.3b.6 Ownership-Pol-Konsument-Arena mit b01-Kopf (registriert 2026-08-28, VOR dem Lauf)

**Zweck: Weg-Wahl Punkt 1 aus par.3b.5.** Lesart 3 legt die Beweislast auf
die PLATZIERUNG: das Draft-Erbe ist da (Masse 0,81->0,60, Lift 28x), die
Vollendungsquote verschenkt es (0,154 gegen Lehrer 0,347). Der Tiling-Pol
`MOSAIC_OWNERSHIP_TILING_W` wird hier ERSTMALS mit einem spaltenbewusst
trainierten Ownership-Kopf gefahren -- die Gate-C-Nullmessungen
(PREREG_gate_c_consumer_sweep.md) liefen mit plattenblinden Koepfen (par.4e
der Fenster-Prereg). b01s Kopf hat Own-Val 0,394 (Trainingslauf 2026-08-28,
STATUS A0 Schritt 3).

**Modell (beide Seiten): `models/alphazero_v22-b01_best.onnx`.**

**Instrument identisch zu par.3b.2**, damit die dortigen Werte vergleichbar
bleiben: `self_play.py --mode network --deterministic --no-root-noise
--sims 400 --games 200 --per-file 20 --seed 20260828 --threads 11`
(argmax-Trajektorien; gesampeltes Self-Play bleibt ausgeschlossen).

**Arme: w in {0 (Kontrolle); 0,5; 1,0; 2,0}**, gesetzt als Env je Prozess.
Wirkstelle: `tiling_solver.rs` `ownership_tiling_weight()` (Default 0,0 =
Fruehausstieg ohne Netz-Pass, `self_play.rs` `ownership_tiling_marginals`,
Fenster R1-4 via `plate_branch_applies`). `MOSAIC_OWNERSHIP_W` (Blatt-Pol)
bleibt 0 -- gemessen wird NUR der Tiling-Pol. Leiter um die natuerliche
Einheit 1,0 (Herleitung PREREG_gate_c_consumer_sweep.md par.3.3); die
Gate-C-Dosen D1-D3 fuhren 0,3/1,0/3,0, hier 0,5/1,0/2,0 als engere Leiter
um die Einheit.

**Masse (je Partie und Seite, am Endbrett aus `score_geo.col_fill`):
volle Spalten (Fuellstand >= 6) und Vollendungsquote (Anzahl ==6 je Anzahl
>= 4)**, dieselben Definitionen wie im Tor-Artefakt `spalten_tor_v22.json`
(`quota_definition` dort). Statistik: gepaarter Block-t ueber die 10
Dateibloecke (Paarung ueber den Blockindex, Seeds identisch ueber die Arme),
Schwelle |t| > 2,262 (df=9, zweiseitig 5 Prozent).

**TOR ("der Konsument traegt"):** mindestens ein w-Arm hebt die vollen
Spalten signifikant ueber den w0-Arm (Block-t > 2,262) UND senkt im selben
Arm die eigenen Punkte nicht signifikant (Block-t > -2,262; Schutz gegen
Spalten um jeden Preis). Die Vollendungsquote wird mit derselben Statistik
als ko-primaere Groesse berichtet, entscheidet aber nicht allein.
Konsequenzen wie in par.3b.5 registriert: traegt er, kommen Knopf-Aufnahme
in die Self-Play-Spec und der v22-Self-Play-Start zurueck auf den Tisch
(Nutzer-Entscheid); traegt er nicht, ist Stufe 2 (2D-Ablesung des
Ownership-Kopfs) VOR Surprise-Weighting der naechste Weg.

**Zwei Instrument-Waechter, vorab benannt:**

1. Das Lauf-Manifest erfasst Env-Knoepfe NICHT (selfplay_manifest.py haelt
   nur cli_args + engine_config; `ownership_tiling_weight` fehlt in
   `engine_config_json`). Der Arm steckt darum im Versionsnamen
   (`otw22b01w00/w05/w10/w20`), und das Auswertungs-Artefakt notiert das
   gesetzte Env je Arm. Ein w>0-Arm, der ZAHLENGLEICH mit w0 endet, heisst
   "Knopf kam nicht an" (ALARM, kein H0-Befund) -- stehende Lehre
   [[feedback_wheel_neu_bauen_nach_engine_aenderung]].
2. Der w0-Arm MUSS die b01-Werte aus par.3b.2 reproduzieren (0,2975 volle
   Spalten; gleiche Seeds, deterministisch, gleiches Wheel). Abweichung =
   Instrumentenbruch, zu klaeren VOR jeder Deutung der w-Arme.

Die sechs Standard-Kennzahlen kommen aus den pkl-Endzustaenden
(`score_geo`, `scoring_tile_points`, `scores`; Muster
tools/corpus_sanity_check.py). Marge zum Gegner entfaellt strukturell
(Self-Play desselben Modells, der Knopf wirkt auf BEIDE Seiten); berichtet
wird stattdessen das Punkte-Niveau je Seite und seine Verschiebung gegen w0.
Punkte je Wertungsplatte aus `scoring_tile_points` je aktivem Kriterium.

**Artefakt: `evaluations/artifacts/ownership_tiling_consumer_v22.json`**
(Muster spalten_tor_v22.json) inkl. `laufzeit`-Block je Arm. Die
Messdateien `selfplay_otw22b01w*_*.pkl` landen in `data/` im Trainings-Glob
-- Loeschung nach der Auswertung NUR mit pfadgenauer Nutzer-Freigabe.
Laufzeit-Anhaltspunkt: 6,7 s je Partie bei 11 Threads
(manifest_tor22b01_20260828_202529.json), also ~22 min je Arm, ~90 min
gesamt; die w>0-Arme zahlen einen Vorwaertspass je Tiling-Zug extra.

**par.3b.6 GEFAHREN 2026-08-29 (ownership_tiling_consumer_v22.json): TOR
VERFEHLT, die Leiter zeigt dosisabhaengig NEGATIV.**

| Arm | volle Spalten | Block-t vs w0 | Quote (==6/>=4) | Punkte |
| --- | --- | --- | --- | --- |
| w0 | 0,2975 +- 0,030 | -- | 0,154 | 34,78 |
| w0,5 | 0,2800 +- 0,033 | -1,17 | 0,147 | 34,82 |
| w1,0 | 0,2800 +- 0,035 | -0,98 | 0,143 | 35,21 |
| w2,0 | 0,2425 +- 0,029 | **-2,85** | 0,124 (t -2,60) | 34,31 |

Kein w-Arm hebt die vollen Spalten; w2,0 liegt SIGNIFIKANT UNTER w0
(|t| ueber der 2,262-Schwelle), die Vollendungsquote faellt mit.
Punkte-Waechter ohne signifikanten Befund in allen Armen.

**Waechter beide gruen:** w0 reproduziert die 0,2975 aus par.3b.2 EXAKT
(unabhaengige Nachzaehlung deckungsgleich), und kein w-Arm ist
zahlengleich mit w0 (der Knopf kam an; die Warnung "Kopf unbrauchbar"
erschien nicht). Sauberkeit: Neustart auf stiller Maschine (Blockdauern
107-145 s); der lastgebremste Erstlauf erwies sich im Inhaltsvergleich als
PARTIEGLEICH bis auf den game_id-Zeitstempel -- Determinismus belegt, die
Fremdlast hatte nur gebremst, nicht verfaelscht (Positivbefund im
Artefakt; die EXKLUSIV-Regel bleibt davon unberuehrt).

**Deutung (markiert als Deutung):** die flache Karte des b01-Kopfs gibt
dem Tiling-Pol keine Richtung, die die Vollendung hebt -- bei w=2 zieht
sie die Platzierung messbar vom Spaltenbau WEG. Zusammen mit par.3b.2
(Trainingsgewicht traegt nicht) ist der Ownership-Kopf in seiner heutigen
flachen Form auf BEIDEN Wirkwegen leer. **Konsequenz nach registrierter
Weg-Wahl (par.3b.5 Punkt 2): Stufe 2 -- 2D-Ablesung des Ownership-Kopfs,
schaerfere Karten fuer denselben Konsumenten -- VOR Surprise-Weighting.
Der v22-Self-Play-Start bleibt gestoppt.**

### par.3b.7 Stufe 2: 2D-Ablesung des Ownership-Kopfs, Arm v22-b04 (registriert 2026-08-29, VOR dem Training)

**Ausloeser:** par.3b.2 Tor 1(a) (Trainingsgewicht traegt nicht) plus
par.3b.6 (Konsument mit flacher Karte traegt nicht, dosisabhaengig negativ)
-- der flache Kopf ist auf beiden Wirkwegen leer. Die im par.3b-Stufenplan
registrierte Uebergangsregel ("kein Schaden" genuegt) ist erfuellt; der
registrierte Vorbehalt bleibt bestehen: "2D hilft" ist fuer STAERKE nicht
belegt (PREREG_2d_encoder.md, Arena-Wash).

**Entscheid der offenen Frage "statt oder zusaetzlich": STATT.**
Begruendung: b01 IST die flache Ablation (derselbe Korpus, derselbe Seed,
dasselbe Rezept) -- ein Doppelkopf wuerde nur die Konsumentenfrage
vernebeln, welche Karte der Tiling-Pol liest, und Parameter doppeln, ohne
einen Vergleich zu ermoeglichen, den b01 nicht schon liefert.

**Bauform (implementiert, Commit dieses Zugs):** `OwnershipHead2D` in
neural_net.py -- Fusionsvektor per Linear auf 32x6x6 projiziert, Conv3x3 +
ReLU + Conv1x1 auf 2 Kanaele (Zieher/Gegner), dann feste Permutation in
die Ziel-Ordnung (sr*12+sc*4+si, Primaerquelle
scoring.rs::ownership_index_for_grid; als Buffer im Modell, an 20 echten
Endbrettern gegen `_ownership_from_dome` verifiziert). Ziel, Breite (72)
und Ausgabe-Ordnung UNVERAENDERT: kein Cache-Key-Effekt, ONNX-Vertrag
unberuehrt, Alt-Checkpoints laden unveraendert (Praesenz-Erkennung aus dem
state_dict, Muster opp_points_head_present; Roundtrip-Test gruen, b01
laedt weiter flach). Der Huellen-Trimm (Nachtrag 6, Option a) ist BEWUSST
NICHT in diesem Arm -- eine Variable je Arm; er ist der benannte Folgearm.

**Arm v22-b04: KALTSTART, Rezept identisch b01** (Arm B
MOSAIC_IGNORE_POLICY_TARGET_VALID=1, --ownership-weight 1.0, --encoder 2d,
--value-head wdl, nortv, --opp-points-head, --endgame-head, --lr-schedule
plateau, --epochs 40, Seed 20260828, volles hv2-Fenster: 2400 Dateien,
verifiziert identisch zum b01-Stand). EINZIGER Unterschied:
--ownership-head-2d. Cache-Treffer auf dem b01-Schluessel erwartet
(Ablesung ist datenseitig unsichtbar).

**Messung und Entscheid:**

1. Own-Val gegen b01 (0,394) -- informative Kopfguete-Anzeige, KEIN Tor.
2. Das Tor ist verhaltensbasiert und zweistufig: erst argmax-Lauf
   (Instrument par.3b.2, 200 Partien) b04 ohne Konsument-Knopf gegen die
   b01-Referenz 0,2975 (der Umbau darf Policy/Spiel nicht verschlechtern;
   der Trunk wird durch den anderen Ownership-Gradienten mitgeformt).
   Dann WIEDERHOLUNG des Konsument-Sweeps par.3b.6 mit b04-Kopf, kleine
   Leiter w 0 / 0,5 / 1,0, gleiche Tore (volle Spalten signifikant ueber
   w0, Block-t 2,262, ohne signifikanten Punkteverlust).
3. Traegt der Konsument mit 2D-Karte -> Knopf-Aufnahme und
   Self-Play-Start zurueck auf den Tisch (Nutzer-Entscheid, wie
   registriert). Traegt er wieder nicht -> Surprise-Weighting (b03) ist
   der naechste registrierte Weg; die Konsumenten-Schiene ist dann mit
   flacher UND raeumlicher Karte leer gemessen.

Trainings-Freigabe: Nutzer 2026-08-29 ("du darfst bei bedarf weitere
trainings fuer v22 durchfuehren solang es unserem ziel naeher bringt").

**TRAINING GEFAHREN 2026-08-29 (manifest_train_v22-b04_20260829_012026,
2,5 h auf CUDA, Cache-Treffer 30,9 s, E17 mit Early Stop, best E7):**

| | b01 (flach) | b04 (2D-Ablesung) |
| --- | --- | --- |
| Ownership-Val bester Wert | 0,3901 (E17) | **0,3751 (E11)** |
| Ownership-Val Epoche 1 | 0,4229 | 0,3975 |
| Policy-Val bester Wert | 0,9071 (E7) | 0,9140 (E7) |
| Value-Brier bester Wert | 0,1920 (E1) | 0,1931 (E1) |

**Messgroesse 1 (informativ) ist damit positiv: die 2D-Ablesung senkt den
Ownership-Val-Loss in JEDER Epoche konsistent** (-0,015, rund -3,8 Prozent;
b04 erreicht in Epoche 1 fast b01s Endniveau). Policy marginal schlechter
(+0,005-0,007), Brier praktisch gleich. Ob die schaerfere Karte am
KONSUMENTEN ankommt, entscheidet Messgroesse 2 -- der Sweep
(w 0/0,5/1,0 mit `alphazero_v22-b04_best`, Checkpoint-Wahl analog b01)
laeuft. Der w00-Arm ist zugleich die argmax-Gegenprobe gegen b01s 0,2975.

**NACHTRAG (registriert 2026-08-29, VOR dem Erweiterungslauf): Leiter um
w=2,0 verlaengert.** Anlass: die kleine Leiter (Ergebnis unten) zeigt eine
POSITIVE, dosis-monotone Richtung (w05 +0,010, w10 +0,030 volle Spalten,
Quote t 1,71), aber unterhalb der Schwelle -- und b01s flache Karte hatte
bei w=2,0 ihr signifikantes NEGATIV. Der w20-Arm prueft, ob der positive
Trend traegt oder kippt; Instrument identisch, Tor unveraendert
(signifikant ueber w0 ohne signifikanten Punkteverlust, Schwelle 2,262).

**SWEEP GEFAHREN 2026-08-29 (ownership_tiling_consumer_v22_b04.json, vier
Arme a 200 Partien, Bloecke sauber 143-154 s): TOR VERFEHLT -- aber die
Dosis-Richtung DREHT gegenueber der flachen Karte.**

| Arm | volle Spalten | Block-t vs w0 | Quote | Punkte |
| --- | --- | --- | --- | --- |
| w0 | 0,2975 +- 0,023 | -- | 0,154 | 33,30 |
| w0,5 | 0,3075 +- 0,026 | +0,69 | 0,163 | 33,25 |
| w1,0 | 0,3275 +- 0,032 | +1,38 (Quote +1,71) | 0,174 | 33,26 |
| w2,0 | 0,3125 +- 0,029 | +0,67 | 0,163 | 33,26 |

Kein Arm ueberschreitet die 2,262-Schwelle; der Gipfel liegt bei w=1,0,
w=2,0 faellt zurueck. Punkte in allen Armen unversehrt. Kontrast zur
flachen Karte (par.3b.6): dort war JEDER Arm negativ und w2,0 signifikant
SCHLECHTER -- mit der 2D-Karte ist jeder Arm positiv. Die schaerfere Karte
schadet also nicht mehr, traegt aber (bei n=10 Bloecken) nicht belegbar.

Beifaenge: b04-w00 trifft mit 0,2975 zufaellig exakt b01s Wert (die
Partien sind verschieden -- Punkte 33,30 gegen 34,78); die argmax-
Gegenprobe zeigt ein um ~1,5 NIEDRIGERES Punkteniveau von b04 gegenueber
b01 (Signifikanz nicht mehr rechenbar, die b01-Blockrohdaten sind mit
Nutzer-Freigabe geloescht; der Auswerter schreibt Blockwerte seit diesem
Lauf mit ins Artefakt).

**Konsequenz nach par.3b.7 Punkt 3: die Konsumenten-Schiene ist mit
flacher UND raeumlicher Karte ohne Torerfolg gemessen.** Optionen fuer den
naechsten Schritt (Nutzer-Entscheid, Empfehlungen in der Morgenlage):
(a) Replikations-Arm w=1,0 mit zweitem Seed fuer mehr Power (der einzige
positive Kandidat, +1,38/+1,71 knapp unter der Schwelle), (b) der
registrierte Folgeweg Surprise-Weighting b03 (Vorbehalt aus par.3b.5:
Draft-Treue ist auf der tragenden Haelfte schon hoch), (c) der
Vollendungs-Filter in der Suche (v23-Weckerliste) als komplementaerer
Hebel derselben Engpass-Stelle.

**NACHTRAG REPLIKATION (registriert 2026-08-29, VOR dem Lauf;
Nutzer-Entscheid "mach den replikations arm w=1"):** w=1,0 gegen w=0 mit
ZWEITEM Seed 20260829 (sonst identisches Instrument, je 200 Partien, 10
Bloecke, Paarung je Block). Vorab festgelegte Auswertung, in dieser
Reihenfolge:

1. **Primaeres Tor: gepoolte Analyse ueber alle 20 Blockpaare** (Seed
   20260828 + 20260829), gepaarter t, Schwelle 2,093 (df=19, zweiseitig
   5 Prozent) -- plus unveraendert kein signifikanter Punkteverlust.
   Transparenz-Vermerk: die erste Haelfte war beim Registrieren dieses
   Nachtrags bereits beobachtet (t +1,38); das Pooling ist ein vorab
   festgelegtes Anfuegen einer zweiten Charge, kein nachtraegliches
   Datenwaehlen -- die Charge 2 laeuft blind gegen dieselbe Regel.
2. Berichtet, entscheidet aber nicht allein: das Replikat fuer sich
   (10 Bloecke, Schwelle 2,262) und die Vollendungsquote (gepoolt).
3. Tor bestanden => der Konsument traegt mit 2D-Karte bei w=1,0;
   Knopf-Aufnahme in die Self-Play-Spec und Start kommen zurueck auf den
   Tisch (Nutzer-Entscheid). Tor verfehlt => Konsumenten-Schiene zu, die
   Optionen (b)/(c) aus dem Ergebnisabsatz oben bleiben die Wege.

Die Messdaten des Erstlaufs sind mit Nutzer-Freigabe vom 2026-08-29
geloescht; die Blockwerte liegen vollstaendig im Artefakt
`ownership_tiling_consumer_v22_b04.json` (der Auswerter schreibt sie seit
diesem Lauf mit), die gepoolte Analyse ist damit rechenbar.

**REPLIKATION GEFAHREN 2026-08-29
(ownership_tiling_consumer_v22_b04_r2.json, Seed 20260829, Bloecke
sauber): TOR VERFEHLT.** Replikat allein: w10 0,3250 gegen w00 0,3075
(+0,0175, t +0,83). GEPOOLT ueber alle 20 Blockpaare beider Seeds:
volle Spalten +0,0237 (t +1,61, Schwelle 2,093), Quote +0,0177
(t +2,06, KNAPP unter der Schwelle), Punkte -0,16 (t -0,44, kein
Schaden). Der Effekt ist ueber beide Seeds richtungsstabil, aber das
vorregistrierte Tor ist nicht genommen; weiteres n-Nachschieben ist
NICHT registriert und unterbleibt (sequenzielles Testen). Verdikt:
die Konsumenten-Schiene bleibt OHNE Torerfolg -- ein kleiner, echter,
fuer sich nicht tragfaehiger Effekt bei w=1,0 mit 2D-Karte. Die
par.3b.8-Diagnose uebernimmt die WARUM-Frage.

### par.3b.8 Mechanik-Diagnose des Tiling-Pols (registriert 2026-08-29, VOR der Messung)

**Anlass:** par.3b.6/3b.7 messen das WAS (Endbrett-Aggregate), nicht das
WARUM. Nutzer-Einwand 2026-08-29: registrierte Form ist nicht automatisch
richtige Form. Form-Kritik (Herleitung, in dieser Registrierung
festgehalten): die eingebaute SUMMEN-Marginale `Σ wert(f)` unterschaetzt
den Wert einer ZELLMENGE fuer konjunktive Kriterien systematisch --
je Spalte mit zwei neuen Zellen ist der echte Mengenwert
`7·Π_rest·(1-p1·p2)` gegen die Summe `7·Π_rest·(p1+p2-2·p1·p2)`; bei
p=0,2 je Zelle gibt die Form nur ein Drittel des wahren Werts. Der Fehler
ist maximal, wenn die Karte den Schwesterzellen misstraut -- ein
Selbstverstaerker der Pessimismus-Falle, und Tiling-Kandidaten sind
komplette Rundenabschluesse (viele Zellen je Kandidat).

**Nutzer-Hypothese (2026-08-29, vorab festgelegte Stratifizierung):** der
Engpass haengt an den Rasterzeilen 5/6 -- dort ist der Preis hoch, solange
keine vollstaendige Spalte liegt (lange Musterreihen als Vorleistung), und
menschliches Spiel nimmt den momentanen Punktnachteil fuer das
SPALTENPOTENTIAL bewusst in Kauf. Erwartung: die fehlenden Zellen
angefangener Spalten sitzen ueberwiegend in Zeile 5/6, und genau dort ist
die Eintretens-Karte pessimistisch.

**Stufe A (Datenpassage + ONNX-Vorwaertspaesse, keine Engine):** an
Vollendungs-Stellen (Spalten >= 4/6 am Zwischenzustand, hv2-Korpus):

1. Zeilenverteilung der fehlenden Spaltenzellen (Soll-Pruefung der
   Hypothese: Anteil Zeile 5/6).
2. p_own der fehlenden Zellen und ihrer Schwesterzellen, b01- gegen
   b04-Karte, stratifiziert nach Zeile -- ist die Karte dort pessimistisch
   (unter der korpusweiten Fuellrate solcher Zellen)?
3. Summen- gegen Mengenwert der fehlenden Zellen je Spalte (Formel oben,
   auf den Kartenwerten) -- quantifiziert die Form-Luecke dort, wo sie
   zaehlt.

**Stufe B (Engine-Zugvergleich, Choice-Schnittstelle der Golden-Probe-
Infrastruktur):** an denselben Stellen Lehrerzug gegen Netz-Zug ohne und
mit Knopf (w=1,0): kippt der Knopf Entscheidungen Richtung Vollendung, und
falls nein -- fehlt der Vollendungszug schon in der Kandidatenmenge
(B1-Klasse: Faehigkeit, nicht Wille)?

**Nachtrag (Nutzer-Freigabe 2026-08-29, VOR Stufe B): Draft-Check an
denselben Stellen.** Anlass: die "Drafting ist intakt"-Evidenz ist
Prior-Masse auf LEHRER-Zustaenden (off-policy) plus geerbte Initiierung --
Zug-fuer-Zug-Masse sieht kein TIMING. Deshalb zusaetzlich: steht eine
Spalte bei 4-5/6 und haengt die fehlende Zelle an Musterreihe 5/6, wird
verglichen, ob der Lehrer auf diesem Zustand die VERSORGENDE Farbe draftet
(lange Reihe bedienen trotz momentanem Punktnachteil -- die
Nutzer-Strategie "Potential der Spalte") und ob das Netz auf demselben
Zustand dasselbe tut. Berichtet je Zeile der fehlenden Zelle und je Runde.

**Stufe C (Sims-Ablation, registriert auf Nutzer-Freigabe 2026-08-29,
VOR dem Lauf): testet das Such-Veto isoliert.** Hypothese 3 der
Diagnose-Diskussion: die 400-Sims-Suche kann den geerbten Lehrerzug per
Value-Head ueberstimmen (Vorleistung langer Reihen kostet sofortiges
Strafleisten-Risiko, der Spaltenlohn liegt Runden entfernt). Messung:
dasselbe argmax-Instrument, b04_best, w=0, aber MINIMALES Sims-Budget
(--sims 1; degeneriert die Gumbel-Suche daran, die kleinste lauffaehige
Zahl -- sie wird im Artefakt dokumentiert), 200 Partien, Seed 20260828,
gegen den vorhandenen 400-Sims-w00-Lauf (0,2975). Lesart: vollendet die
rohe Policy DEUTLICH mehr Spalten als die gesuchte, ist das Such-Veto
belegt (Hebel: Such-/Value-Seite, z.B. Vollendungs-Filter); sonst ist es
nicht der Haupttaeter. Benannter Confound, kein Tor: bei Sims 1 sinkt die
Spielstaerke insgesamt (beide Seiten); gelesen werden volle Spalten UND
Quote, als DIAGNOSE.

**Stufe D (Hüllen-Deckung, registriert auf Nutzer-Vorschlag 2026-08-29,
VOR der Messung): der geometrische Richtwert.** Frage: legt der Lehrer
seine Steine tatsaechlich IN der Dreiecks-Einhuellenden (erlaubter Bereich
r+c <= 5, 21 Zellen; Spiegelung je Start-Ecke, gemessen wird die
besser passende Orientierung; Definition aus heuristic_v2.rs im Stand
65b48af^, dreiecks_abweichung) -- und wie weit folgen ihm die Netze?
Reine Datenpassage, je Partie/Seite/RUNDE: Anteil der in der Runde NEU
belegten Zellen innerhalb der Huelle, Fuellstand Huelle (x/21) gegen
Aussenbereich (x/15) am Rundenende, Dreiecks-Abweichung. Quellen: (a)
Lehrer aus dem hv2-Korpus (Erzeugungs-Self-Plays, 300 Dateien wie
par.3b.5), (b) b04 aus den Replikations-Messdateien (otw22b04r2*).
Ergebnis ist ein RICHTWERT-Profil je Runde ("wie spielt der Lehrer
geometrisch"), kein Tor -- es eicht kuenftige Huellen-Hebel (Trimm der
Loss-Maske, ggf. Huelle als Netz-Einhuellende) an gemessener Geometrie
statt an Vermutung.

**Stufe-D-Ergaenzung GEFAHREN 2026-08-29 (Nutzer-Auftrag: Abgleich mit den
Server-Spiellogs; hull_coverage_server_logs.json, 9 fertige
Mensch-gegen-v21-Partien, Rekonstruktion ueber die korrektheitsbewiesene
column_build_structural_probe-Maschinerie):**

| Quelle | Huelle/21 | Abweichung | volle Spalten | Quote |
| --- | --- | --- | --- | --- |
| MENSCH (Server-Logs) | **17,44** | **6,00** | **1,78** | **0,727** |
| v21 (dieselben Partien) | 14,11 | 10,67 | 0,11 | 0,050 |
| Lehrer hv2 (Self-Play) | 13,55 | 11,42 | 0,74 | 0,347 |
| b04 (Self-Play) | 13,49 | 10,67 | ~0,30 | ~0,15 |

Der geometrische Richtwert menschlichen Spiels liegt WEIT ueber der
bisherigen Lehrer-Decke: die Huelle wird zu 17,4/21 gefuellt (Abweichung
6,0), fast zwei volle Spalten je Partie, Vollendungsquote 0,73. Der
Abstand Lehrer->Mensch ist damit GROESSER als der Abstand Netz->Lehrer.
Vorbehalte, wie im Memory registriert: n=9, einseitig (Mensch gewinnt fast
immer, Gegner ist der plattenblinde v21, andere Farbkonkurrenz als im
Self-Play) -- als Groessenordnungs-Beleg belastbar, als Verteilung nicht.
Folgerung fuer die Hebel-Diskussion: selbst eine perfekte
Lehrer-Imitation traefe nur die halbe Huelle; der Einhuellenden-Ansatz
des Nutzers hat oberhalb des hv2-Lehrers messbaren Raum.

Nachtrag 2026-08-29: zehnte fertige Partie
(game_20260829_183516_seed114421, 109:29) als benanntes
REFERENZBEISPIEL der Einhuellenden -- Mensch fuellt die Huelle 20/21,
KOSTEN-GEWICHTET 0,946 (ueber dem n=9-Richtwert 0,838), Abweichung 4,
zwei volle Spalten, zwei Chip-Vollendungen der Reihen 4/5 in R5
(Stufe-E-Muster). Das n=9-Artefakt bleibt unveraendert; ein kuenftiger
Sonden-Rerun mittelt ueber 10 Partien und faellt entsprechend hoeher aus.

**Stufe D2 (registriert 2026-08-29 auf Nutzer-Entscheid, VOR der Messung):
vier weitere Huellen-Kennzahlen, ueber alle drei Quellen (Lehrer-Korpus,
b04-Self-Play, Server-Logs) -- damit ist die Sonde ABGESCHLOSSEN.**

1. LEBENDE HUELLE: Anteil toter Zellen (kind=normal, Vorrats-Puffer < 0
   via mosaic_rust.plate_completability_json) unter den noch leeren
   Huellen-Zellen, am Ende von Runde 3 und 4. Nur pkl-Quellen (Server-Logs
   tragen keine Zustaende; Grenze wird ausgewiesen).
2. FRONTIER-TREUE: Kendall-tau zwischen Lege-RUNDE einer Zelle und ihrer
   Tiefe d=r+c (finale Orientierung) -- waechst die Huelle von der Ecke
   her, oder springt der Bau?
3. HALBZEIT-HUELLE: Fuellstand und Abweichung am Ende von Runde 3
   (Fruehindikator statt Endbrett-Ergebnis).
4. ORIENTIERUNGS-STABILITAET: frueheste Runde, ab der die bestpassende
   Orientierung des Teilbretts final bleibt, plus Anzahl vorher
   fehlorientiert gelegter Zellen (ausserhalb der finalen Huelle).

Alles Richtwerte, keine Tore. Danach (Nutzer-Entscheid 2026-08-29) folgt
die STAPELUNG: On-Policy-Nachschaerfung mit Lehrer-Relabeling PLUS die
Einhuellende als direktes Gelaender -- Zuschnitt wird nach der
D2-Befundlage als eigene Absaetze registriert.

**STUFE D2 GEFAHREN 2026-08-29 (triangle_hull_coverage_{lehrer,b04r2}.json,
hull_coverage_server_logs.json; inkl. KOSTEN-GEWICHTUNG r+1 je Zeile auf
Nutzer-Auftrag, Nenner 56 je Huelle). Die Sonde ist damit ABGESCHLOSSEN.**

| Quelle | Huelle gew. (Ende) | ungew. | Halbzeit gew. | Frontier-tau | tote Huelle R4 |
| --- | --- | --- | --- | --- | --- |
| MENSCH | **0,838** | 0,831 | **0,533** | 0,381 | n/a (keine Zustaende) |
| Lehrer hv2 | 0,600 | 0,645 | 0,340 | 0,325 | 0,006 (gew. 0,010) |
| b04 | 0,573 | 0,642 | 0,334 | 0,404 | 0,008 (gew. 0,014) |
| v21 | 0,538 | 0,672 | 0,323 | 0,413 | n/a |

Befunde: (1) Der MENSCH fuellt kosten-NEUTRAL (gewichtet = ungewichtet);
ALLE Maschinen kaufen ihre Fuellung in den billigen Zeilen (v21 -13,4 pp
unter Gewichtung, b04 -6,9, auch der Lehrer -4,5). Der wahre
Mensch-Maschine-Abstand ist gewichtet ~0,24-0,30, nicht ~0,17. (2) In der
gewichteten Geometrie liegt b04 FAST AUF Lehrer-Niveau (0,573 gegen 0,600;
Halbzeit 0,334 gegen 0,340) -- die Vollendungsluecke (0,30 gegen 0,74
Spalten) ist damit KEIN Fuellungs-, sondern ein KONZENTRATIONS-Problem:
gleicher gewichteter Einsatz, halber Spalten-Ertrag (Konversion
Spalten je gewichteter Fuellung: Lehrer ~1,23, b04 ~0,52) -- konsistent
mit der Ketten-Diagnose (Fuellung verstreut sich statt eine Spalte zu
schliessen). (3) Tote Huelle ueberall unter 1,5 Prozent: der Vorrat
stirbt NICHT, die teuren Zellen werden nicht bedient (Oekonomie, nicht
Erreichbarkeit). (4) Frontier-Ordnung und Orientierungs-Stabilitaet
differenzieren nicht (alle ~0,3-0,4 bzw. stabil ab ~R1).
LEITKENNZAHL der Einhuellenden ab jetzt: der kosten-gewichtete
Huellen-Fuellanteil (Mensch-Richtwert 0,84; Halbzeit 0,53).

**Stufe E (Chip-Nutzung, registriert 2026-08-29 auf Nutzer-Einwand "das
ist eine essentielle Mechanik", VOR der Korpus-Messung):** Chip-Abschluesse
je Partie und Musterreihe, drei Quellen. Server-Logs BEREITS GEZAEHLT
(explizite Log-Zeile, 10 Partien): MENSCH 3,0 je Partie (Reihe 5: 6,
Reihe 6: 8 -- fast einmal je Partie die teuerste Reihe), v21 2,2 je
Partie, aber Reihe 6 nur EINMAL in zehn Partien. Der par.3c-Rahmen
("feuert fast nie") beschrieb die v2-Heuristik und war als
Mechanik-Aussage irrefuehrend. Korpus-Seite (hv2-Lehrer, b04): gezaehlt
ueber den BESTANDSABFALL der gehaltenen bonus_chips zwischen
aufeinanderfolgenden Zustaenden derselben Partie/Seite (Chips werden nur
fuer Reihen-Abschluesse verbraucht; die Reihe ergibt sich aus der im
selben Schritt komplettierten pattern_line). Lesart vorab: liegt der
Lehrer nahe am Menschen und das Netz darunter, ist die Chip-Bewertung ein
konkreter Vollendungs-Hebel; liegt auch der Lehrer niedrig, fehlt die
Faehigkeit schon der Referenz und der Hebel gehoert in die
Gelaender-Schiene.

**Stufe E GEFAHREN 2026-08-29 (chip_usage_sources.json; Korpus-Methode
einmal korrigiert -- Ausgaben passieren INNERHALB der Tiling-Phase, die
Records enthalten Tiling-Zustaende, erste Zaehlung an Rundengrenzen war
blind):** Chips je Partie+Seite ausgegeben: Lehrer 7,74 (2,68
Ereignisse), b04 7,89 (2,56) -- dieselbe Groessenordnung wie die 3,0
Abschluesse des Menschen. **Am VOLUMEN liegt es nicht; der Unterschied
ist die ALLOKATION:** der Mensch schliesst Reihe 6 fast einmal je Partie
per Chips (0,8), v21 einmal in zehn Partien (Server-Logs; Reihen-
Attribution in den Korpora nicht moeglich, Grenze registriert). Der
par.3c-Null-Befund betraf nur den v2-ZUSATZ-Vorzug; der Basis-Solver
gibt reichlich aus. Hebel-Konsequenz: nicht "Chips nutzen lehren",
sondern die CHIP-ALLOKATION auf die teuren Reihen lenken -- das ist
dieselbe Kosten-Scheu wie in Stufe D2 (gewichtete Huelle) und gehoert
in die Gelaender-Schiene (par.3b.10-Klasse), nicht in einen neuen
Mechanik-Bau.

**par.3b.8 GEFAHREN 2026-08-29, alle Stufen. GESAMTVERDIKT: die Ketten-
und Drift-These traegt; Karte, Geometrie, Form und Such-Veto scheiden als
Haupttaeter aus.**

* **Stufe A** (ownership_map_completion_sites*.json; 15.903 Stellen
  Lehrer-Korpus, 1.397 on-policy): Zeilen-Hypothese BESTAETIGT (fehlende
  Zellen dominant tief, Zeile 6 allein ~35-40 Prozent). Die Karte ist auf
  Lehrer-Zustaenden KALIBRIERT (p 0,63 gegen real 0,598) und nicht
  pessimistisch; on-policy faellt die reale Vollendungsrate auf 0,446, die
  Karte folgt der Richtung, ist aber +9 pp zu optimistisch. Form-Luecke
  Summe/Menge: 0,82 (Lehrer-Zustaende) bzw. 0,73-0,75 (on-policy) --
  real, aber zweitrangig.
* **Stufe C** (Sims-Ablation, 200 Partien sims=1): SUCH-VETO TOT, Vorzeichen
  umgekehrt -- die rohe Policy kollabiert komplett (0,0075 volle Spalten,
  11,1 Punkte, init>=4 0,79); die Suche HEBT die Policy auf 0,30, sie
  unterdrueckt sie nicht.
* **Stufe D** (triangle_hull_coverage_*.json): Geometrie SAUBER GEERBT --
  b04 ist huellen-treuer als der Lehrer (neu-in-Huelle R1-3 0,98/0,88/0,80
  gegen 0,95/0,75/0,77; End-Abweichung 10,67 gegen 11,42). Verbotene Zone
  strukturgleich bei beiden (Band d=1 dominiert ~47 Prozent, Cluster ~1,
  SymKorr ~0): flaches Rand-Ueberschwappen, kein Systematik-Unterschied.
* **Draft-Check on-policy** (onpolicy_teacher_draft_fidelity.json, 618
  Entscheidungen, 12 Live-Partien, gefrorener Lehrer als Referenz auf
  b04-Brettern): Zug-Uebereinstimmung je Runde 0,69/0,54/0,55-0,63/
  0,57-0,58; das Reihenwahl-Profil des Netzes deckt sich mit dem des
  Lehrers. ENTSCHEIDEND: an Vollendungs-Stellen bedient DER LEHRER SELBST
  auf den Netz-Brettern die fehlende Zeile nur zu 0,21-0,32 -- statistisch
  wie das Netz (0,26-0,28). Die spaete Einzelentscheidung ist NICHT der
  Engpass; die Bretter sind zu diesem Zeitpunkt bereits kompromittiert.

**Lesart (Synthese):** 30-45 Prozent Nicht-Lehrer-Zuege je Entscheidung
multiplizieren sich ueber die Kette einer Spalte (0,6^k); das Netz landet
auf Brettern, auf denen auch der Lehrer nicht mehr vollenden wuerde
(Versorgung verspielt), und genau dort faellt die reale Vollendungsrate
auf 0,446. Kein einzelner spaeter Fehler, sondern akkumulierte fruehe
Divergenz -- Hypothesen 1+2 der Diagnose-Diskussion; Hypothese 3 (Suche)
widerlegt, Hypothese 4 an den Stellen selbst nicht bestaetigt.

**Hebel-Folgerung (Empfehlung, Nutzer-Entscheid):** (1) On-Policy-
Nachschaerfung mit LEHRER-RELABELING -- der gefrorene Worker kann
Netz-Zustaende in Masse labeln (DAgger-Muster; das Instrument existiert
und lief hier fehlerfrei ueber 618 Anfragen); adressiert die Drift direkt.
(2) Der Konsumenten-Knopf w=1,0 bleibt ein kleiner echter Zusatz, traegt
aber allein nicht. (3) Vollendungs-Filter (Suche) und b03 bleiben
nachrangige Alternativen. Mengen-Form-Arm und Blatt-Pol-Arm werden nach
dieser Befundlage ZURUECKGESTELLT (Formfehler zweitrangig, Konsument nicht
Haupttaeter) -- Wiedervorlage nur, falls (1) die Vollendung hebt und der
Konsument dann erneut messbar wird.

**Vorab benannte Lesarten (Registrierungsstand vor den Laeufen):** (i) Karte pessimistisch an 5/6-Zellen =>
Mengen-Form-Arm (Folge-Registrierung par.3b.9) und ggf. die Zielfrage
(PREREG_v23_reachability_recheck-Klasse); (ii) Karte ok, Zug kippt
trotzdem nicht => Skalen-/Formfrage, ebenfalls Mengen-Form-Arm; (iii)
Vollendungszug fehlt in den Kandidaten => Such-/Vorratshebel
(Vollendungs-Filter, v23-Weckerliste), der Knopf ist dann nicht der
Engpass. Reihenfolge nach Nutzer-Freigabe 2026-08-29: Diagnose ->
Mengen-Form-Arm -> Blatt-Pol-Arm.

### par.3b.9 Schiene 1 der Stapelung: On-Policy-Nachschaerfung v22-b05 (registriert 2026-08-29, VOR Erzeugung/Training; Namens-Korrektur auf Nutzer-Hinweis: b-Serie zaehlt fortlaufend, kein Buchstaben-Suffix)

**Ziel:** die Ketten-/Drift-Luecke schliessen (par.3b.8): der Lehrer
relabelt die Draft-Entscheidungen auf den EIGENEN Brettern des Netzes
(DAgger-Muster). Nutzer-Freigabe 2026-08-29 ("stapelung", "maschine
gehoert dir").

**Erzeugung:** 600 b04-Partien mit dem argmax-Instrument
(--deterministic --no-root-noise, 400 Sims, Seed 20260830, per-file 20,
Tag `dagger-b04`) -- exakt die Spielverteilung, in der die Vollendung
scheitert; Partien-Diversitaet kommt aus den Partie-Seeds. Die Dateien
werden nach der Erzeugung in ein UNTERVERZEICHNIS data/onpolicy_v22-b05/
verschoben (ausserhalb des Trainings-Globs; Einbindung nur explizit via
--extra-data-dir).

**Relabeling:** alle Draft-Entscheidungen der Runden 1-4 (~45-50k) werden
dem gefrorenen hv2_generator-Worker vorgelegt; die Policy des Records wird
durch den One-Hot-Lehrerzug ersetzt (policy_target_valid=true), Value-
Felder bleiben unveraendert (Ausgang der gespielten Partie).
**Registrierter Vorbehalt:** die Trainings-Records tragen die verdeckten
exact-Felder nicht; ein Shim ergaenzt sie SEEDED und konsistent zu den
sichtbaren Zaehlern (Beutel-/Stapelordnung). Das Label ist damit der
Lehrerzug unter EINER Determinisierung der verdeckten Information --
dieselbe Klasse wie determinize_root_hidden_info=true der Suche; kein
Orakelwissen. Parallelisierung: 8 Worker-Prozesse.

**Training v22-b05 (Afterburner):** Warm-Start von b04_best, NUR der
Relabel-Korpus via --extra-data-dir (das 40:1-Uebergewicht des
hv2-Korpus wuerde das Korrektursignal ertraenken), wenige Epochen,
lr 5e-5 + cosine (Standard-Warmstart-Rezept), Arm-B-Env,
--ownership-weight 1.0, --ownership-head-2d, Seed 20260828. Ein
gemischter Arm (hv2 + Relabel) ist als Eskalation benannt und wuerde
als v22-b06 laufen, falls b05 die Policy destabilisiert
(Punkte-Einbruch im Instrument).

**Messung/Tor:** argmax-Instrument 200 Partien gegen b04-Referenz 0,2975
(gleiche Seeds 20260828): volle Spalten Block-t > 2,262 ohne
signifikanten Punkteverlust; dazu die D2-Leitkennzahlen (kosten-
gewichtete Huelle, Konversion) als Berichtsgroessen.

**par.3b.9 ERZEUGUNG/RELABELING/TRAINING GEFAHREN 2026-08-29:**
600 dagger-b04-Partien (Instrument-Modus, Seed 20260830) erzeugt und nach
data/onpolicy_v22-b05/ verschoben; Relabeling **31.190/32.440**
Draft-Entscheidungen (0 Fehler, 0 unabbildbar; 1.250 mal antwortete der
Lehrer keinen Stein-Zug -- Original-Ziel behalten, gezaehlt). Zwei
Werkzeug-Befunde dabei: der frozen-Worker antwortet im ALT-Schema
(factory_id+source; Uebersetzung 1:1 aus self_play.rs::factory_index),
und gematcht werden muss gegen valid_actions statt der Gumbel-besuchten
Policy-Liste. Durchsatz ~5 ms je Label (8 Worker, 66 s gesamt).
v22-b05-Afterburner: Warm-Start b04_best, 6 Epochen cosine lr 5e-5,
176.366 Samples, 10,5 min; Policy-Val faellt monoton 1,482 -> 1,405
(kein Plateau, festgeschriebene 6 Epochen), Brier 0,198, Own-Val 0,386.
VAL-VORBEHALT registriert: der Val-Split stammt aus dem Relabel-Korpus
selbst (Warm-Start ohne MOSAIC_VAL_POOL, train.py-Warnung) -- die
Val-Metriken sind indikativ, das Urteil faellt die ARENA-Messung
(laeuft, otw22b05w00 gegen b04-Referenz 0,2975).

**par.3b.9 MESSUNG GEFAHREN 2026-08-29 (otw22b05w00, 200 Partien argmax,
Seeds identisch zur b04-Referenz, Blockpaarung):**

| | b04 (w0) | v22-b05 |
| --- | --- | --- |
| volle Spalten | 0,2975 | **0,3375** (+0,040, t +1,18) |
| Quote (==6/>=4) | 0,154 | 0,170 |
| init>=4 | 1,94 | 1,99 |
| Punkte | 33,30 | **37,16 (+3,86, t +2,61 SIGNIFIKANT)** |

**Das registrierte Spalten-Tor ist VERFEHLT** (t 1,18 unter 2,262) --
aber der Punkte-Waechter schlaegt in die GEGENRICHTUNG aus: b05 ist
signifikant STAERKER (hoechstes Punkteniveau der v22-Familie an diesem
Instrument, ueber b01s 34,78) bei zugleich bestem Spaltenwert ohne
Konsumenten-Knopf. Das On-Policy-Lehrer-Relabeling wirkt also primaer
als allgemeine Staerkung (Drift-Reparatur), nicht spezifisch auf die
Spaltenzahl. b05 ist damit der BESTE STAND aus Schiene 1 und traegt die
Gelaender-Leiter (par.3b.10); die Eskalation v22-b06 (Misch-Arm)
entfaellt (keine Destabilisierung -- das Gegenteil).

**NACHTRAG 2026-08-29 (Manifest-Diff der Folgesitzung, Regel
"Lauf-Manifest gegen Referenz"): das b05-Training lief NICHT nur auf dem
Relabel-Korpus.** manifest_train_v22-b05_20260829_131243.json,
`corpus_composition`: neben dagger-b04 (600 Partien) lagen otw22b04r2w00,
otw22b04r2w10 und otw22b04s1 (je 200 Partien, zusammen 600 UNRELABELTE
On-Policy-Messpartien, darunter die degenerierten sims=1-Partien der
Stufe C) als Policy-Traeger im Fenster -- MOSAIC_DATA_EXCLUDE traf nur
`^selfplay_hv2_`, die Messdateien im data-Glob liefen still mit
(176.366 Samples passen zu 1.200, nicht 600 Partien). Der b05-Effekt ist
damit KONFUNDIERT: Relabeling PLUS rohe On-Policy-Partien, nachtraeglich
nicht trennbar. Die Staerke-Messung gegen b04 bleibt davon unberuehrt
(sie misst das Artefakt, nicht den Mechanismus). Runde 2 (par.3b.11)
faehrt das registrierte REINE Design auf geraeumtem data-Verzeichnis.

### par.3b.10 Schiene 2 der Stapelung: Gelaender-Leiter (registriert 2026-08-29, VOR der Messung)

**Ziel:** Konzentrations-Fuehrung zur Suchzeit Richtung Mensch-Richtwert
(gewichtete Huelle 0,84 / Konversion ~2). Instrument OHNE Neubau: das
Netz-Blatt-Shaping `MOSAIC_WERTUNG_SHAPING_W` (Default 0, stetiger
quadratischer Fortschritt je Kriterium = konzentrations-sensitiv) wurde
NIE mit einer spaltenfaehigen Policy gefahren -- dieselbe Klasse "Knopf
existiert, hatte nie das richtige Netz" wie der Tiling-Pol. Leiter
w in {0; 0,15; 0,3} (0,3 = validiertes Floor-Shaping-Gewicht als
Groessenordnungs-Anker), k1-fokussierte Kriteriengewichte, am
argmax-Instrument, 200 Partien je Arm, auf dem BESTEN Stand aus Schiene 1
(v22-b05 falls es traegt, sonst b04). Tor wie par.3b.9. Die
Trainings-Haelfte des Gelaenders (Huellen-Trimm der Ownership-Maske mit
r+1-Kostengewichten, Nachtrag 6) bleibt benannter Folgearm NACH der
Leiter.

**par.3b.10 GEFAHREN 2026-08-29 (gelaender_ladder_b05.json, Basis v22-b05,
je 200 Partien, Blockpaarung gegen b05-w0): H0.**

| Arm | volle Spalten | Block-t vs w0 | Punkte |
| --- | --- | --- | --- |
| w0 (b05 pur) | 0,3375 | -- | 37,16 |
| k1-Shaping 0,15 | 0,3325 | -0,61 | 37,09 |
| k1-Shaping 0,30 | 0,3475 | +1,50 | 37,21 |

Kein Arm erreicht die Schwelle; 0,30 zeigt eine kleine positive Richtung
ohne Punkte-Kosten. Das Blatt-Shaping in dieser Dosis ist damit weder
Hebel noch Schaden. Die Trainings-Haelfte des Gelaenders (Huellen-Trimm
der Ownership-Maske mit r+1-Kostengewichten) und die Chip-ALLOKATIONS-
Fuehrung (Stufe-E-Befund) bleiben die benannten offenen Gelaender-Arme --
Nutzer-Entscheid der naechsten Sitzung.

### par.3b.11 DAgger-Runde 2: On-Policy-Nachschaerfung auf v22-b05 (registriert 2026-08-29, VOR Erzeugung/Training; Nutzer-Go 2026-08-29)

**Ziel:** die Stapelung fortsetzen -- b05 zeigte bei E6 KEIN Plateau
(Policy-Val fiel monoton 1,482 -> 1,405) und ist signifikant staerker;
Runde 2 relabelt die EIGENEN b05-Bretter und gibt dem Afterburner mehr
Epochen. Ergebnisname: **v22-b06** (b-Serie fortlaufend; der in par.3b.9
als Eskalation reservierte Misch-Arm b06 ist entfallen, der Name ist
frei; b03 bleibt fuer Surprise-Weighting reserviert).

**Design-Klarstellung nach dem par.3b.9-Nachtrag:** Runde 2 faehrt das
REGISTRIERTE reine Design -- Trainingsfenster = NUR der neue
Relabel-Korpus. Das data-Verzeichnis traegt nach den Loeschfreigaben
2026-08-29 top-level ausschliesslich `selfplay_hv2_*` (geprueft vor dem
Start); der Exclude greift damit vollstaendig. Benannter Unterschied zum
b05-IST-Rezept (das 600 rohe Messpartien enthielt): faellt b06 hinter
b05 zurueck, ist der Roh-Anteil ein benannter Verdaechtiger.

**Erzeugung (Referenz: manifest_dagger-b04_20260829_113736.json, nur
Modell/Seed/Version geaendert):** `python -u self_play.py --mode network
--model models/alphazero_v22-b05.onnx --games 600 --sims 400
--version dagger-b05 --threads 11 --chunk 10 --seed 20260831
--per-file 20 --no-root-noise --deterministic` (~83 min laut
Runde-1-Laufzeit). Danach werden die 30 Dateien samt Manifest nach
`data/onpolicy_v22-b06/` verschoben (ausserhalb des Trainings-Globs).

**Relabeling:** `python -u tools/relabel_drafts_with_teacher.py
--in-dir data/onpolicy_v22-b06 --workers 8` -- unveraendertes Werkzeug
aus Runde 1 (Alt-Schema-Uebersetzung und valid_actions-Match geloest,
749046c); Erwartung ~30k Labels, ~66 s.

**Training v22-b06 (Afterburner):** Warm-Start v22-b05, **12 Epochen**
(doppeltes Budget, da E6 kein Plateau zeigte), cosine lr 5e-5 mit
`--lr-t-max 12` (T_max-Falle), Early Stop aktiv wie in Runde 1;
Env `MOSAIC_IGNORE_POLICY_TARGET_VALID=1`,
`MOSAIC_DATA_EXCLUDE=^selfplay_hv2_`; Flags wie das b05-Manifest:
`--extra-data-dir data/onpolicy_v22-b06 --ownership-weight 1.0
--ownership-head-2d --encoder 2d --value-head wdl
--value-target-variant nortv --opp-points-head --endgame-head
--seed 20260828 --lr 5e-5 --lr-schedule cosine`. Val-Vorbehalt wie
par.3b.9: der Val-Split stammt aus dem Relabel-Korpus, Metriken
indikativ, das Urteil faellt die Arena-Messung.

**Messung/Tor:** argmax-Instrument, 200 Partien, Tag `otw22b06w00`,
Seed 20260828 (identisch zur b05-Referenz), 10 Bloecke a 20 Partien,
Blockpaarung gegen die gespeicherten b05-w0-Bloecke
(gelaender_ladder_b05.json: volle Spalten 0,3375, Punkte 37,16).
Tor wie par.3b.9: volle Spalten Block-t > 2,262 OHNE signifikanten
Punkteverlust; der Punkte-t wird beidseitig berichtet (in Runde 1 war
er der eigentliche Befund). Berichtsgroessen dazu: Vollendungsquote,
init>=4, die sechs Standard-Kennzahlen, und die D2-Leitkennzahl
(kosten-gewichtete Huelle via triangle_hull-Sonde auf den
Messdateien). Die Messdateien sind nach der Auswertung
Loeschkandidaten (naechste Freigabe-Runde).

**par.3b.11 KOMPLETT GEFAHREN 2026-08-29 (Erzeugung 5.066,6 s / 8,44 s je
Partie; Relabeling 31.133/31.996 Labels, 0 Fehler, 119 s, Artefakt
relabel_v22_b06.json -- der hart verdrahtete Artefaktname des Werkzeugs
hat dabei das Runde-1-Artefakt ueberschrieben, Werkzeug seitdem auf
in-dir-abgeleitete Namen gefixt; Training 472 s, 12 Epochen, Fenster
geprueft REIN: 2.400 hv2 ausgeschlossen, exakt 30 dagger-b05-Traeger;
Messung otw22b06w00 1.753,7 s; Artefakte dagger_round2_b06.json,
triangle_hull_coverage_b06.json):**

| | v22-b05 (Referenz) | v22-b06 |
| --- | --- | --- |
| volle Spalten | 0,3375 | 0,3500 (+0,0125, t +0,29) |
| Quote (==6/>=4) | 0,170 | 0,168 |
| init>=4 | 1,99 | 2,08 |
| Punkte | 37,16 | 36,24 (-0,91, t -0,72) |

**TOR VERFEHLT, beidseitig H0: Runde 2 traegt NICHT weiter.** Kein
Spalten-Schub (t +0,29) und kein Punkte-Schub mehr -- der Runde-1-Effekt
(+3,86 Punkte) wiederholt sich nicht; b06 ist statistisch gleichauf,
**v22-b05 bleibt bester Stand**. Passend dazu das Trainingsbild:
Policy-Val flacht schon ab E4-E7 aus (Runde 1: bei E6 noch fallend).
Lesart: die Drift-Reparatur ist nach EINER Runde weitgehend gesaettigt.
Benannter Verdaechtiger aus der Design-Klarstellung (nicht trennbar):
Runde 2 lief REIN (ohne die 600 Roh-Messpartien, die in b05s IST-Korpus
still mitliefen, par.3b.9-Nachtrag). Nebenbefund Geometrie: b06s
kosten-gewichtete Huelle 0,620 liegt erstmals UEBER dem Lehrer (0,600;
b04 0,573; Mensch 0,84) bei Konversion ~0,56 gegen Lehrer ~1,23 -- die
DAgger-Schiene verbessert die Huellen-Geometrie, nicht die
Spalten-Konzentration; das stuetzt die Gelaender-/Allokations-Hebel
(Chip-Allokation, Huellen-Trimm) als naechste Kandidaten.
Sechs-Kennzahlen im Artefakt (u.a. Strafleiste 6,92 Steine,
k1 2,45, k6 -11,26). Loeschkandidaten nach Registrierung:
data/selfplay_otw22b06w00_* (10 Dateien) und -- falls keine Runde 3
kommt -- data/onpolicy_v22-b06/ (31 Dateien); Nutzer-Freigabe noetig.

### par.3b.12 TOR-REVISION fuer den Generationen-Start (registriert 2026-08-30, VOR dem v22-Self-Play; Nutzer-Strategie 2026-08-29 "er soll nur jetzt mal spalten bauen, dann schlaegt er irgendwann hv2 und dann v21", Ausfuehrungs-Go "mach weiter im fahrplan / in der nacht gehoert die maschine dir")

**Was revidiert wird:** das par.3b.2-Tor band den Self-Play-Start an den
OWNERSHIP-KONSUMENTEN (w1 signifikant ueber w0 plus Vollendungsquote
ueber 0,53). Diese Frage ist seit par.3b.6/3b.7 NEGATIV beantwortet --
der Konsument traegt nicht -- und damit prueft das Tor einen Mechanismus,
der nicht mehr der Weg ist, statt der Generator-Eignung. Eine stille
Umgehung verbietet die stehende Regel (umgangenes Tor); darum diese
ausdrueckliche Revision.

**Neue Startbedingung (alle drei am 2026-08-29/30 gemessen erfuellt):**

1. Volle Spalten des Generators am argmax-Instrument >= 3x der
   Champion-Referenz: b05 0,3375 gegen 0,102 = 3,3x -- ERFUELLT.
2. Spaltenbau trennt Sieger von Verlierern (Symmetrie-Sonde am
   Erzeuger-Korpus): +0,573, t 93 -- ERFUELLT (hv2-Korpus; fuer den
   NEUEN Korpus siehe Waechter unten).
3. Relative Bewerter-Heilung belegt (Fahrplan Phase 0: Geschwister-Tau
   +0,338, Mensch-Orakel-Differenz ~0, Prior-Ratio 1,23) -- ERFUELLT.

**Anti-Drift-Anker der Generation:** 1.800 policy-aktive hv2-Partien im
v23-Fenster (PREREG_v23_window par.1) plus DAgger-Afterburner als
benannte Reserve, falls die Drift-Waechter anschlagen.

**Waechter NACH der Erzeugung, VOR dem v23-Training (bindend):** auf dem
neuen Self-Play-Korpus (a) volle Spalten je Partie+Seite >= 0,17 (die
Haelfte des argmax-Instrumentwerts; Herleitung als Annahme markiert --
Root-Noise und Temperatur druecken argmax-Werte, ein Einbruch UNTER die
Haelfte hiesse aber, dass der Generator im Explorationsmodus das
Spaltenspiel verliert => STOPP und Bericht), (b) Symmetrie-Trennung
signifikant > 0 (corpus_column_outcome_symmetry_probe). Werkzeuge
existieren beide.

**NACHTRAG 2026-08-30 (VOR dem Sockel-Start, registriert vor der
Leiter): Vorab-Evidenz gegen die geplante Konfiguration.** Der
N1-Kontrollarm des Nachtprogramms IST die geplante Sockel-Konfiguration
(b05@400, Root-Noise, Besuchs-Sampling) und baut nur 0,0825 +- 0,028
volle Spalten je Partie+Seite (200 Partien,
implicit_minimax_gating_b05.json; obere KI-Grenze 0,11) -- der
Waechter (a) verlangt >= 0,17, der Verlust kommt aus
Exploration/Sampling (argmax-Instrument: 0,65-0,67 gegen Heuristik).
Ein Blindstart liefe in einen fast sicheren Waechter-Riss. Deshalb,
als Revision der par.4c-Zeile "--tau-argmax-from-move nicht gesetzt"
(deren Praemisse damit gefallen ist): **tau-Leiter VOR dem Sockel** --
je 200 Partien mit --tau-argmax-from-move 24 bzw. 60 (Sampling nur in
den ersten N Halbzuegen, argmax danach; die Policy-ZIELE bleiben
unveraendert die Besuchsverteilungen, nur die Zustandsverteilung
verschiebt sich zur Spaetspiel-Exploitation), Root-Noise an,
MOSAIC_STACK_DRAW_RESEARCH=1 (N2-Entscheid), Seeds 20260913/20260914,
Tags tlb05t24/tlb05t60. **Entscheidungsregel (vorab): der KLEINSTE
tau-Arm mit vollen Spalten je Partie+Seite >= 0,17 wird
Sockel-Konfiguration; erreicht keiner die Schwelle, STOPP und
Nutzer-Vorlage am Morgen.** Punkteniveau wird berichtet
(Beobachtung, kein Tor).

**tau-LEITER GEFAHREN 2026-08-30 03:45 -- BEIDE ARME VERFEHLEN, Regel
gefeuert: KEIN Sockel-Start, Nutzer-Vorlage am Morgen.** t24: 0,0775
+- 0,018; t60: 0,0725 +- 0,015 (je 200 Partien; Punkte 23,1/21,2) --
praktisch gleichauf mit dem Voll-Sampling-Kontrollarm (0,0825). Das
Spaetspiel-Sampling ist damit NICHT der Taeter; der gemeinsame Faktor
aller drei Arme ist der ROOT-NOISE (Deutung: eine verrauschte
Entscheidung in der Vollendungs-Kette bricht sie, 0,6^k-Mechanik der
par.3b.8-Diagnose). Der 2x2 (Noise x Sampling) fehlt eine Zelle --
Noise aus, Sampling an: als DIAGNOSE-ARM registriert (200 Partien,
--no-root-noise OHNE --deterministic und ohne tau-Override, Seed
20260915, Tag tlb05nn, Stack-Draw EIN). Er entscheidet nichts, er
vervollstaendigt die Ursachen-Trennung fuer die Morgen-Vorlage;
Referenzzellen: Noise+Sampling 0,0825, Noise+argmax-spaet ~0,075,
ohne-Noise+argmax 0,3375 (otw22b05w00).

**DIAGNOSE-ARM GEFAHREN 03:48-04:14: ohne Noise, mit Sampling =
0,1075 +- 0,017 (Punkte 22,4).** Der 2x2 ist damit komplett und die
Deutung verschoben: der Root-Noise kostet ~0,03, das SAMPLING selbst
kostet den Grossteil (0,34 -> 0,11) -- die Vollendungs-Ketten brechen
an der fruehen Zug-Stochastik (Versorgungs-Entscheide der Runden 1-2),
nicht am Spaetspiel. Letzte Kandidaten-Zelle, registriert als zweiter
Diagnose-Arm (Seed 20260916, Tag tlb05nn24, Stack-Draw EIN): ohne
Noise, Sampling NUR Halbzuege 0-23 (--no-root-noise
--tau-argmax-from-move 24) -- minimale Exploration frueh, argmax
danach. Haelt sie >= 0,17, wird sie die EMPFOHLENE Sockel-Konfiguration
der Morgen-Vorlage; sonst lautet die Vorlage auf den Zielkonflikt
Exploration gegen Spaltenlehre (Optionen: deterministischer Sockel wie
die DAgger-Korpora, Misch-Sockel, oder Waechter-Frage an den Nutzer).

**ZWEITER DIAGNOSE-ARM GEFAHREN 04:17-04:43: 0,1025 +- 0,014 (Punkte
25,98, init>=4 1,62) -- VERFEHLT. Endstand der Nacht-Leiter (volle
Spalten je Partie+Seite, je 200 Partien, Waechter-Schwelle 0,17):**

| Konfiguration | volle Spalten |
| --- | --- |
| Noise + Voll-Sampling (geplanter Sockel) | 0,0825 |
| Noise + argmax ab 24 / ab 60 | 0,0775 / 0,0725 |
| ohne Noise + Voll-Sampling | 0,1075 |
| ohne Noise + Sampling nur 0-23 | 0,1025 |
| ohne Noise + argmax (Instrument-Referenz) | **0,3375** |

**ZUSCHNITT-ENTSCHEID 2026-08-30 (Nutzer: "mach D") -- ROLLEN-GETRENNTE
MISCHUNG, registriert VOR dem Start.** Anlass war der Nutzer-Einwand,
dass das v23-Fenster ohnehin viel hv2 traegt (par.1 der Fenster-Prereg:
1.800 policy-aktive und 15.650 policy-maskierte hv2-Partien). Daraus
die Rollenteilung:

* **Sockel = Policy-Klasse (4.000, voll gesampelt, Root-Noise an).**
  Begruendung (HERLEITUNG, als solche markiert): das Policy-ZIEL ist
  die Besuchsverteilung der Suche, nicht der gespielte Zug -- die
  Zug-Stochastik aendert also, WELCHE Zustaende besucht werden, nicht
  die Qualitaet der Ziele an ihnen. Die Spalten-Lehre der Policy deckt
  ohnehin der hv2-Anker (1.800 Partien a 0,73 volle Spalten). Der
  einzigartige Beitrag des Sockels ist Zustandsabdeckung.
* **Schwarm = Value-Klasse (8.000, davon 6.000 argmax + 2.000
  gesampelt).** Hier liegt der Engpass aus Fahrplan Phase 0: die
  Betrags-Daempfung (R5-Steigung 0,0886) hat auf hv2-Fenstern NICHT
  geheilt, obwohl die voller Vollendungen sind -- weil sie off-policy
  sind. Die Wette der Generation ist ON-POLICY-Exposition: eigene
  Partien, in denen Vollendungen vorkommen und sich im Ausgang
  auszahlen. Ein Value-Korpus mit 0,08 Spalten macht genau diese Wette
  kaputt; die 2.000 gesampelten halten Zustands-Streuung in der Klasse.
* **Benannter Preis:** die argmax-Partien beziehen ihre Vielfalt
  ausschliesslich aus den 6.000 Partie-Seeds (Plattenwahl, Beutel,
  Startspieler) -- Praezedenz sind die DAgger-Korpora (600 argmax-
  Partien, alle verschieden). Zustands-Diversitaet ist dort geringer als
  bei Sampling; das ist der bewusste Tausch gegen Vollendungs-Labels.

**WAECHTER NEU GEFASST 2026-08-30 (Nutzer-Freigabe "bau das so";
ersetzt die 0,17-Schwelle als Tor).** Anlass ist die Nutzer-Frage
"woher kommt eigentlich der wert 0.17" und die ehrliche Antwort: die
Zahl war der halbierte Instrumentwert, von mir gesetzt und als Annahme
markiert -- eine Faustzahl, die eine 20-Stunden-Entscheidung gesteuert
haette. Neue Fassung:

1. **PRIMAER (inhaltlich begruendet): Symmetrie-Trennung auf der
   VALUE-Klasse signifikant > 0** (corpus_column_outcome_symmetry_probe;
   Referenz hv2-Korpus +0,573, t 93). Begruendung: der Value-Kopf kann
   per Konstruktion nur lernen, was den AUSGANG trennt -- trennt
   Spaltenbau im neuen Korpus Sieg nicht von Niederlage, ist das
   Material fuer die Betrags-Heilung wertlos, unabhaengig von jeder
   Rate.
2. **SEKUNDAER: mindestens 1.500 Partien-Seiten mit >= 1 voller Spalte
   im Value-Korpus** (Zaehlung am Endbrett je Partie und Seite).
   Herkunft der Zahl: GESETZT, aber an der Lernmaterial-Logik statt an
   einer Rate orientiert -- eine Rate ignoriert die Korpusgroesse, die
   Ereigniszahl nicht. Der Posten ist ein STOPP gegen Degeneration
   (ein Korpus praktisch ohne Vollendungen), KEINE Lernbarkeits-
   Garantie: der hv2-Korpus enthaelt weit mehr solcher Seiten, und die
   Daempfung heilte dort trotzdem nicht (off-policy).
3. **BERICHTSGROESSE, kein Tor:** volle Spalten je Partie+Seite in
   beiden Klassen (Referenzwerte fuer die Einordnung: argmax 0,3375,
   gesampelt 0,07-0,11, Champion 0,102). Fuer die Policy-Klasse gilt
   ohnehin keine Schwelle -- ihr Auftrag ist Zustandsabdeckung, ihr
   Spaltensignal kommt aus dem hv2-Anker.

**Offene Frage dahinter, jetzt benannt:** wieviel Vollendungsdichte der
Value-Kopf ueberhaupt braucht, ist im Projekt NIE gemessen worden.
Erster billiger Test (Nutzer-Vorschlag 2026-08-30, sauberer als mein
v18/v19-Entwurf): **v21_2d_brierbest gegen v22-b05** -- gleiche Aera,
gleiche Architektur (2D/WDL), Korpus-Dichte ~0,10 gegen 0,73, also
Faktor 7 bei sonst gleichen Bedingungen. Bleibt die R5-Platten-Steigung
gleich (b05: 0,0886), ist die Dichte NICHT der Hebel und die
Betrags-Daempfung strukturell -- das faellt dann direkt auf Phase 3
zurueck.

**SIMS-PROBE GEFAHREN 2026-08-30 (VOR dem Schwarm-Start, weil
`--value-only` das Cheap-Budget an `--sims` koppelt, self_play.py:777 --
"kleine Sims" gibt es nur ueber ein kleines --sims):** 200 Partien
argmax value-only mit **150 Sims: 0,4425 +- 0,042 volle Spalten**
(Quote 0,211, init>=4 2,09, Punkte 41,0) gegen 5,3 s je Partie
(400 Sims: 12,5 s). Erst-Entscheid war "Schwarm 150 Sims, Sockel 400".

**BEIDES UEBERHOLT (2026-08-30, nach der vollstaendigen Kurve und der
Arena, PREREG_search_depth_column_optimum par.2i-2k).** Der neue Stand:
**BEIDE Klassen fahren 100 Sims** (Nutzer-Entscheid). Begruendung in
Kuerze: das Plateau liegt bei 25-100 (~0,6 volle Spalten gegen 0,34 ab
250, frisch-seed-repliziert), der Preis ist ein nicht signifikanter
Staerkeverlust (@100 gegen @400: 33:47, p=0,144, KI streift die Null;
@25 dagegen klar unterlegen, 11:29). Die 400 fuer den Sockel war
zudem willkuerlich gesetzt -- der Bestand fuhr 600
(PREREG_v21_window.md:15) -- und die Annahme "tiefe Suche labelt
besser" ist ungeprueft; die Policy-Ziele kommen ohnehin per
Lehrer-Relabeling, nicht aus der Spiel-Suche.

**BEOBACHTUNG mit Caveat, kein Befund:** 0,4425 liegt UEBER dem
400-Sims-Referenzwert 0,3375 -- aber die beiden stammen aus
VERSCHIEDENEN Modi (value-only gegen normalen Self-Play), sind also
nicht sauber vergleichbar; die Kontrollzelle (value-only @400) fehlt.
Falls sich der Effekt bestaetigt, waere er inhaltlich anschlussfaehig
an die Phase-0-Diagnose (Policy traegt das Spaltenwissen, der
gedaempfte Value-Kopf ueberstimmt es mit wachsender Suchtiefe; bei
sims=1 kollabiert dagegen alles, par.3b.8 Stufe C 0,0075) -- das waere
ein Optimum mittlerer Tiefe fuer den Spaltenbau und ein eigener
Messstrang, NICHT hier mitentschieden.

**Dateipraefixe (Generator-Konvention plus Klassen-Suffix):**
`v22-b05-policy` (Seed 20260901), `v22-b05-value-argmax` (Seed
20260902), `v22-b05-value-sampled` (Seed 20260903); Stack-Draw-Knopf
EIN in allen dreien (N2-Entscheid), implicit-Minimax 0,0 (N1).

**Verdikt: JEDE gemessene fruehe Zug-Stochastik drueckt die Vollendung
auf ~0,07-0,11; nur reines argmax haelt 0,34.** Die Initiierung bleibt
dabei intakt (init>=4 1,4-1,6) -- es bricht die KETTE, nicht der
Anfang; die Versorgungs-Entscheide der ersten Runden vertragen bei
diesem Netz keine Abweichung von der argmax-Linie (konsistent mit
par.3b.8). KEIN Sockel-Start per Regel; die Optionen (deterministischer
Sockel / Misch-Sockel / Design-Neufassung) liegen als Nutzer-Vorlage
in STATUS.

**Erzeugungs-Zuschnitt (Wecker-Abarbeitung in PREREG_v23_window par.4c
registriert):** 4.000 Sockel @400 Sims mit Root-Noise (Policy-Klasse) +
8.000 Schwarm --value-only (v20-Konvention, cheap-sims 150); Dateiname
nach Generator `v22-b05` (docs/generation_naming.md); Seeds 20260901
(Sockel) / 20260902 (Schwarm); Manifest-Pflichten wie immer.

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

**BERICHTIGUNG 2026-08-29 (Nutzer-Einwand "deshalb gibt es die 3er-Regel",
am Code geprueft):** der Erklaerteil oben ist falsch begruendet.
`greedy_chip_indices` (round_end.rs:487) faellt je fehlender Zelle
AUTOMATISCH auf 3 beliebige Chips zurueck, wenn keine 2 farbgleichen da
sind -- die 3er-Regel war im gemessenen Pfad AKTIV, nicht erst
"zuzulassen". Die Null-Feuerung in 80 Partien erklaert sich damit nicht
ueber den Farbzufall, sondern (Herleitung, ungemessen) ueber den BESTAND
zum Entscheidungszeitpunkt: maximal 2 Chips je Runde nehmbar, und der
Rundenende-Solver verbraucht gehaltene Chips selbst (TilingStep::Chips) --
drei UNGENUTZTE Chips plus blockierende Reihe im richtigen Zustand plus
sofortige Platzierbarkeit fallen selten zusammen. Messbarer
Anschlusspunkt, falls je relevant: Chip-Bestandsverlauf je Runde
auszaehlen.

**Zweite Berichtigung im selben Zug (Nutzer-Nachfrage "mehr als eine
Fliese je Reihe", an der Historie geprueft):** auch die Aussage "die
Reihe muss auf genau eine fehlende Zelle heruntergefuellt sein" war
falsch. Der gemessene Vorzug (v2_chip_preference, Stand 65b48af^,
plate_builder.rs:2570) rief das MEHRZELLFAEHIGE greedy_chip_alloc ohne
Ein-Zellen-Einschraenkung auf; die Engine-Regel (2 gleiche ODER 3
beliebige JE fehlender Zelle, 2*missing <= s <= 3*missing) und das
Netz-Feature chippable_tiling_rows decken Mehrfeld-Fuellung ebenfalls ab.
Der Ein-Zellen-Fall ist nur der WAHRSCHEINLICHSTE (2 fehlende Zellen
braeuchten 4-6 gehaltene Chips), keine Voraussetzung. Die gemessenen
Fakten des Absatzes (0 Feuerungen in 80 Partien, Test der Funktion
gruen) bleiben unberuehrt -- falsch war zweimal die ERKLAERUNG.

**Kein Ruecknahme-Fall wie par.3a:** der Term kostet nichts (er greift nur,
wenn er zuschlaegt) und bleibt im Code -- er wird wirksam, sobald ein Korpus
mehr Chip-Reserven zulaesst oder die Bedingung gelockert wird (z.B. 3
beliebige statt 2 farbgleiche zulassen, was `greedy_chip_alloc` bereits als
Fallback kennt). Fuer diese Kampagne ist er eine korrekte, aber seltene
Randbedingung -- nicht der Hebel, der die 7,5 Prozent Null-R6-Partien
schliesst.

### par.5.3 ERGEBNIS (2026-08-24): Faehigkeit belegt, Preis hoch -- URTEIL STEHT AUS

`tools/run_v2_teacher_arena.sh` -> `tools/probes/v2_teacher_arena.py`,
Artefakt `evaluations/artifacts/v2_teacher_arena.json`. 407 Kampagnen-Seeds je Arm,
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
keinen Schwellenwert vorregistriert (s. Klarstellung unter **par.5 Punkt 4**
"Korpus und Training"; Verweis BERICHTIGT 2026-08-27 -- er stand als "par.5.4"
da, und eine Ueberschrift dieses Namens gibt es nicht. Gemeint ist und war der
vierte Punkt der Messkette in par.5, der die Klarstellung woertlich traegt;
dieselbe Schreibweise steht noch an drei weiteren Stellen dieser Datei und
meint jedes Mal denselben Listenpunkt). Die
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
`evaluations/artifacts/v2_envelope_arena.json`. Aufbau genau wie in par.8.4 vorab
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

`evaluations/artifacts/v2_envelope_arena_heatmap.json`. Differenzen Heatmap minus Huelle.

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

`evaluations/artifacts/v2_teacher_arena_v2huelle.json`, 407 Kampagnen-Seeds je Arm,
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

`evaluations/artifacts/v2_envelope_arena_phase.json`, n=160 gegen `V2Huelle`, sonst
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
nichts". Ein Sweep ueber die Werte findet NICHT statt, und die Begruendung
steht in den Daten: der Arm zeigt KEINEN Effekt in irgendeine Richtung
(t=0,39 auf dem Entscheidungsmass, Siegquote 0,500). Werte eines Faktors zu
variieren, der bei der gesetzten Staerke nichts bewegt, braucht erst ein
Argument, warum eine andere Staerke etwas anderes tun sollte -- und das gibt
es hier nicht.

**KORREKTUR 2026-08-25 (Nutzer-Einwand), doppelt.** Die erste Fassung dieses
Absatzes begruendete den Verzicht mit einer "Dosis-Antwort, die in diesem
Projekt schon dreimal negativ entschieden wurde". Daran war beides falsch:

1. **Die Zahl.** Nachgesehen gibt es EINEN echten Dosis-Sweep, der negativ
   entschieden ist (`PREREG_scoring_plate_injection.md`, w = 0,03/0,1/0,3/1,0).
   `PREREG_long_row_payoff.md` B1 ist ebenfalls negativ, war aber
   ausdruecklich KEIN Sweep ("ein Wert genuegt zum Testen"). Kein dritter Fall.
2. **Der Bezug, und das wiegt schwerer.** Beide Praezedenzfaelle sitzen in der
   NETZ-BLATTBEWERTUNG -- B1 ist `net_mcts.rs::long_row_init_shaping_w`, ein
   additiver Term am Blattwert, und die Injektion fragt wortwoertlich nach der
   "Blattbewertung". par.11 dreht dagegen an einem Rundenfaktor auf die
   ZIELZELLEN-KARTE einer handgeschriebenen Heuristik im ROUTING. Anderer
   Layer, anderer Mechanismus, andere Fehlermoeglichkeit. Die Praezedenzfaelle
   gehoeren dorthin, wo an derselben Stelle gedreht wird
   (`PREREG_risk_sensitive_leaf_utility.md` par.2), nicht hierher.

Fuer kuenftige Arme heisst das: ein Praezedenzfall traegt nur, wenn er
DENSELBEN Eingriffspunkt betrifft. "Schon mal negativ entschieden" ohne
Layer-Abgleich ist ein Scheinargument.

**Nebenbefund aus der neu gebauten k6-Aufspaltung, erster Einsatz:** das
Punkteniveau liegt bei aktiver Wertungsplatte 6 bei 34,0 gegen 48,9 ohne --
knapp 15 Punkte Unterschied. Das ist mit dem Blindziehungs-Befund der
Parallelsitzung vertraeglich (`PREREG_stack_draw_reservation_rule.md`). Fuer
DIESEN Arm-Vergleich ist der Posten neutral: beide Seiten sind in beiden
Gruppen flach (+0,200 bzw. -0,257), der Vorbehalt aus par.8.5 greift hier
also nicht.

## par.13 Phasenfaktor: Sweep ueber STAERKE und POSITION (VORREGISTRIERT 2026-08-25)

**Anlass, und die Abgrenzung gegen par.11.** Nutzer-Auftrag 2026-08-25:
"variiere staerke und position des faktors ... latin hypercube". par.11 hat
GENAU EINE Form gemessen (Gipfel 1,4 auf den Runden 2-3) und H0 geliefert.
Daraus folgt nicht, dass keine Form etwas bewegt -- nur, dass diese es nicht
tut. Wo der Gipfel liegen soll, war nie gemessen; die Lage kam aus einer
externen Quelle fuer ein anderes Spiel.

Das ist ausdruecklich NICHT der Werte-Sweep, den par.11.1 abgelehnt hat:
dort ging es um dieselbe Form mit anderen Zahlen, hier um eine andere FORM.

**Parametrisierung** (`plate_builder::spalten_phase`, zwei Diagnose-Knoepfe,
Default aus, in `knob_registry.rs` eingetragen):

```
f(r) = 1 + (amp - 1) * exp(-(r - peak)^2 / (2 * sigma^2)),   sigma = 1,0 fest
```

`sigma` bleibt fest, damit der Entwurf zwei Dimensionen hat und nicht drei.
Ohne gesetzte Knoepfe liefert die Funktion die feste par.11-Tabelle -- der
Bestand ist unberuehrt.

### par.13.1 Stufe 1: SCREENING (entscheidet NICHTS)

Latin-Hypercube, 16 Punkte, `amp` in [1,0; 2,5], `peak` in [1,0; 5,0],
Entwurfs-Seed 20260825. Je Punkt 160 gepaarte Partien gegen `V2Huelle`, sonst
Aufbau wie par.8.4. Werkzeug: `tools/probes/phase_sweep.py`.

**`amp = 1,0` ist ein eingebauter NULLPUNKT** -- die Kurve ist dann konstant 1
und der Arm identisch zur Huelle. Punkte nahe 1,0 liefern den Rauschboden, an
dem die uebrigen zu messen sind. Das ersetzt keine Signifikanzrechnung, macht
aber sofort sichtbar, wie gross Ausschlaege ohne jede Ursache werden.

**Diese Stufe darf nichts entscheiden.** Bei 16 Punkten ist das Maximum einer
t-Statistik auch unter reiner Nullhypothese deutlich von Null entfernt. Den
besten Punkt abzulesen und als Befund zu melden waere Rosinenpickerei mit
16 Versuchen -- genau der Fehler, gegen den
[[feedback_preregister_decision_metric]] steht. Das Screening liefert einen
KANDIDATEN.

### par.13.2 Stufe 2: BESTAETIGUNG (entscheidet)

Der beste Punkt aus Stufe 1 laeuft erneut, auf einem ANDEREN Seed-Satz
(Seed 20260826 statt 20260825), gleiche Partienzahl.

**Entscheidungsmass: volle Spalten je Partie, gepaart, auf Block-Ebene** --
dasselbe wie in par.8.4, damit die Zahlen vergleichbar bleiben.
**Waechter:** Vollendungsquote >= 0,53.

**Falsifikator:** reproduziert die Bestaetigung den Effekt nicht, war der
Screening-Ausschlag Rauschen, und der Phasenfaktor ist ueber beide Arme
(par.11 und par.13) als Bauform negativ entschieden -- ohne dritten Versuch.

**Zusaetzlich vorab festgelegt, damit hinterher nichts umgedeutet wird:** ein
Kandidat, dessen Screening-Ausschlag den Rauschboden der Nullpunkte nicht
klar uebersteigt, geht gar nicht erst in Stufe 2. In dem Fall ist par.13
ohne Bestaetigungslauf negativ.

### par.13.1 ERGEBNIS Screening (2026-08-25): Position irrelevant, Arm negativ

`evaluations/artifacts/phase_sweep.json`, 16 LHS-Punkte, je 160 gepaarte Partien gegen
`V2Huelle`, Entwurfs-Seed 20260825, Laufzeit 236 s.

| Groesse | Wert |
| --- | --- |
| Korrelation Delta ~ **peak** | **+0,110** |
| Korrelation Delta ~ **amp** | **+0,674** |
| groesstes \|t\| ueber alle Punkte | **1,48** |
| Delta min / median / max | -0,006 / +0,053 / +0,113 |
| positive Deltas | 15 von 16 |
| bester Punkt | amp 2,12, peak 3,09: +0,113 (t=1,48) |

**Die POSITION ist es nicht.** Wo der Gipfel liegt, erklaert praktisch nichts
(r=0,110). Die Vermutung, par.11 habe nur den Gipfel an der falschen Stelle
gehabt, ist damit widerlegt -- das war der eigentliche Zweck dieses Arms.

**VERDIKT nach der vorab festgelegten Abbruchbedingung: par.13 ist NEGATIV,
Stufe 2 laeuft NICHT.** Kein Punkt kommt in die Naehe von Signifikanz
(max t=1,48, und das als Maximum aus 16 Versuchen). Der Kandidat uebersteigt
den Rauschboden nicht klar, und par.13.2 war genau daran geknuepft.

**Was die Flaeche darueber hinaus zeigt, ausdruecklich UNREGISTRIERT.** Es gibt
einen Dosis-Trend in der Amplitude (r=0,674; amp >= 1,8 im Mittel +0,072 gegen
+0,034 darunter). Das ist eine Beobachtung an der Antwortflaeche, kein
Befund, und sie geht in keine Entscheidung ein. Drei Gruende, sie nicht
weiterzuverfolgen, ohne dass jemand ausdruecklich einen neuen Arm dafuer
aufmacht:

1. **Alle 16 Punkte teilen denselben Seed-Satz.** Ein gemeinsamer Zug hebt
   alle Deltas zugleich -- das erklaert die 15 von 16 positiven Werten besser
   als ein echter Effekt. Auf den amp-Trend wirkt dieser Konfundierer zwar
   nicht (er ist eine additive Verschiebung, keine Steigung), aber die
   Fehlerbalken der einzelnen Punkte sind nicht unabhaengig.
2. **Die Groessenordnung traegt nicht.** Der staerkste Ausschlag ist +0,113
   gegen +0,525, die die Huelle selbst liefert -- ein Fuenftel, und das als
   Maximum aus 16 Zuegen.
3. **Ein struktureller Grund sagt Saettigung voraus.** Im Drafting entscheidet
   die Karte einen RANG, und Prio 3 schlaegt Prio 5 schon bei amp=1,0; mehr
   Amplitude aendert die Ordnung nicht. Wirksam wird Hoehe nur dort, wo
   Gewichte SUMMIERT werden (Tiling-Vorzug, Produkt der Plattenwahl). Das ist
   ein Verdacht aus dem Code, keine Messung -- aber er sagt vorher, was die
   Flaeche zeigt.

**Der Bereich war meine Setzung, nicht die des Nutzers** (amp in [1,0; 2,5],
peak in [1,0; 5,0]). Nach oben aufzumachen, WEIL das Ergebnis flach aussieht,
waere die Bewegung, die eine Vorregistrierung verhindern soll. Wer hoehere
Amplituden testen will, macht dafuer einen eigenen Arm mit eigener
Vorab-Festlegung auf.

**Gemeinsames Fazit par.11 + par.13:** der Phasenfaktor auf die Spalten-Stufen
ist als Bauform negativ entschieden -- eine feste Form (par.11, t=0,39) und
16 Formen ueber Staerke und Position (par.13, max t=1,48). `SPALTEN_PHASE`
und die beiden Diagnose-Knoepfe bleiben im Code, Default aus.

### par.12.1 ERGEBNIS (2026-08-25): NEGATIV, und das vorab benannte Risiko ist eingetreten

`evaluations/artifacts/v2_envelope_arena_filter.json`, n=160 gegen `V2Huelle`.

| Kennzahl | Huelle | Filter | Delta | t (Block) |
| --- | --- | --- | --- | --- |
| volle Spalten | 0,794 | **0,431** | **-0,362** | -5,03 |
| max Spaltenhoehe | 5,537 | 5,175 | -0,362 | -6,90 |
| Teilspalten >= 3 | 3,000 | **3,125** | **+0,125** | +2,80 |
| Spezialfeld-Freischaltungen | 1,069 | 0,919 | -0,150 | -2,32 |
| Strafpunkte | -14,87 | -13,87 | +1,000 | +1,06 |
| eigene Punkte | 44,34 | 39,49 | -4,850 | -4,49 |

Siegquote 0,431. Vollendungsquote 0,664 (Waechter haelt). Reihenauslastung
wandert nach OBEN: Rasterzeile 4 und 5 fallen (1,91 auf 1,69 und 1,38 auf
1,20), Zeile 0 und 1 steigen.

**Das in par.12 vorab benannte Risiko ist genau so eingetreten.** Dort stand:
"der Filter kann in Runde 4-5 zu viel wegschneiden ... ein Filter, der die
Zielspalte spaet noch wechseln laesst, kann genau diesen Gewinn
zurueckdrehen." Die Zahlen zeigen das Muster: weniger Tiefe, mehr Breite,
weniger Zuege in die unteren Rasterzeilen.

**Die Ursache ist eine Fehlpassung zwischen Filter und Zielfunktion, nicht
eine falsche Schwelle.** `cell_is_completable` ist ein BINAeRES Kriterium
(reicht die Restversorgung fuer die ganze Zelle?), aber die Spaltenwertung
zahlt STETIG und konvex: `(fuellung/6)^2 * 7` belohnt auch den Schritt von 4
auf 5, obwohl die Spalte nie voll wird. Der Filter wirft genau diesen
Teilfortschritt weg -- und mit ihm die Festnagelung, die den Bauschritt
"Zielspalte ab Runde 3" ueberhaupt erst wirksam gemacht hat.

Die k1-Aufspaltung stuetzt das: der Verlust ist groesser, wo die
Spalten-Wertungsplatte AKTIV ist (-0,500 gegen -0,324) -- also genau dort, wo
Teilfortschritt Punkte bringt und das Wegschneiden am meisten kostet.

**Folgerung fuer den Bericht der Parallelsitzung** (§4.5, dort Kandidat 1):
die Vollendbarkeits-Relaxation taugt als FEATURE und als Kostenterm -- sie
steckt seit dem Spaltenbauer in `cell_cost` und in beiden Punktekarten. Als
harter AKTIONSFILTER auf ein stetig kreditiertes Ziel taugt sie NICHT. Die
Literatur-Empfehlung "Filter statt Bewertungsterm" (§4.4) gilt also nicht
unbesehen, sondern haengt daran, ob das Ziel binaer oder stetig ausgezahlt
wird.

**Die Gegenprobe bleibt ein EIGENER Arm, keine Nachbesserung.** par.12 hat sie
vorab so festgelegt: ein Filter, der nur in Runde 1-3 greift. Sie ist nicht
gebaut, und sie waere nach diesem Ergebnis auch nicht die naheliegendste
Fortsetzung -- die Diagnose zeigt auf die Binaeritaet, nicht auf den
Zeitpunkt.

## par.14 Phasenfaktor, sauberer Entwurf: Stufe x Staerke x Position (VORREGISTRIERT 2026-08-25)

**Anlass: Nutzer-Auftrag 2026-08-25** nach dem Ergebnis von par.13 -- "mehr
sweeps, nur runde 1-4 damit es unterscheidbar ist, und bei bedarf ziehst auch
den tiling mit; drafting ist nur die halbe miete". Drei benannte Schwaechen
des ersten Entwurfs werden behoben:

1. **`peak` nur noch bis 4,0.** Das Routing endet nach Runde 4
   (`preference_move_for_cells` und `tiling_preference_for_cells` liefern ab
   Runde 5 nichts). In par.13 lag `peak` bis 5,0, vier von sechzehn Punkten
   setzten die Spitze also teilweise dorthin, wo sie niemand liest -- die
   Position war dadurch schwaecher geprueft als die Staerke.
2. **Dreimal so viele Punkte.** 48 statt 16, damit die Position ueberhaupt
   aufloesbar wird; in par.13 lagen nur vier Punkte je Runden-Gruppe.
3. **Die STUFE als dritte Dimension** (`MOSAIC_PHASE_STAGE`, Diagnose,
   Vorgabe `both`). Das ist der inhaltlich wichtigste Punkt.

### par.14.1 Warum die Stufe eine eigene Dimension ist

Die Zielkarte wird an drei Stellen gelesen, und sie wirkt dort VERSCHIEDEN:

| Stelle | Wie die Karte benutzt wird | Was Amplitude tut |
| --- | --- | --- |
| Drafting (`envelope_drafting_preference`) | bestes Zielgewicht der Reihe als RANG | nichts -- die Ordnung steht schon bei amp=1,0 |
| Plattenwahl (`slot_score_generic`) | Produkt aus Kartengewicht und Zellenwert | wirkt |
| Tiling (`tiling_preference_for_cells_weighted`) | SUMME der Kartengewichte | wirkt |

Das war in par.13 mein Erklaerungsversuch fuer die flache Antwortflaeche --
als Verdacht aus dem Code formuliert, nicht gemessen. Hier wird er zur
Messgroesse: `draft` / `tiling` / `both` als drei Arme mit je demselben
LHS-Entwurf. Ist der Verdacht richtig, muss `tiling` staerker ausschlagen als
`draft`.

Die Plattenwahl haengt an der Drafting-Stufe, weil sie dort als
`.or_else`-Zweig laeuft -- eine vierte Trennung waere ein eigener Umbau.

**Entwurf:** LHS ueber `amp` in [1,0; 2,5] und `peak` in [1,0; 4,0], 16 Punkte,
je Stufe derselbe Entwurf (Seed 20260826, ANDERER als par.13 -- das hier ist
kein Nachziehen desselben Laufs). 48 Laeufe zu je 160 gepaarten Partien.

**Diese Stufe entscheidet wieder NICHTS.** Dieselbe Regel wie par.13.1: bei 48
Punkten ist das Maximum einer t-Statistik erst recht vom Zufall bewegt. Was
sie liefert, ist der Stufen-Vergleich als AGGREGAT (Mittel je Stufe ueber 16
Punkte) -- und ein Kandidat.

**Bestaetigung (par.14.2), falls eine Stufe deutlich herausfaellt:** bester
Punkt dieser Stufe auf frischen Seeds, Entscheidungsmass volle Spalten je
Partie auf Block-Ebene, Waechter Vollendungsquote >= 0,53.

**Abbruchbedingung, vorab:** liegt kein Stufen-Mittel klar ueber dem
Rauschboden der Quasi-Nullpunkte (amp < 1,1), ist par.14 ohne
Bestaetigungslauf negativ -- und damit der Phasenfaktor endgueltig, ueber drei
Arme und 65 gemessene Formen.

### par.14.2 ERGEBNIS (2026-08-25): NEGATIV -- und meine Erklaerung war falsch

`evaluations/artifacts/phase_sweep.json`, 48 Laeufe (3 Stufen x 16 LHS-Punkte), je 160
gepaarte Partien, Entwurfs-Seed 20260826, Laufzeit 732 s.

| Stufe | n | Mittel Delta Spalten | max \|t\| | Mittel Delta Punkte | Mittel Siegquote |
| --- | --- | --- | --- | --- | --- |
| **draft** | 16 | **+0,048** | 1,33 | +0,17 | 0,510 |
| **tiling** | 16 | **+0,002** | 0,10 | -0,17 | 0,487 |
| both | 16 | +0,051 | 1,38 | +0,04 | 0,498 |

Rauschboden aus 3 Quasi-Nullpunkten (amp < 1,1): |delta| bis 0,025.
Nach Gipfel-Runde: [1;2) +0,016 (n=18), [2;3) +0,043 (n=12), [3;4) +0,045
(n=18).

**VERDIKT: negativ.** Kein Stufen-Mittel uebersteigt den Rauschboden klar
(0,051 gegen 0,025), kein einzelnes t kommt ueber 1,38. Die vorab festgelegte
Abbruchbedingung greift, par.14.3 laeuft nicht.

**MEINE ERKLAERUNG AUS par.14.1 IST WIDERLEGT, und zwar im Vorzeichen.** Dort
stand als Vorhersage: im Drafting entscheidet die Karte einen RANG, dort kann
Amplitude nichts bewirken; im Tiling und in der Plattenwahl werden Gewichte
SUMMIERT bzw. multipliziert, dort muss sie greifen. Gemessen ist es umgekehrt
-- `tiling` liefert exakt nichts (+0,002, max t 0,10), waehrend `draft` den
kleinen Rest traegt, den es ueberhaupt gibt.

Das war das dritte Mal in diesem Strang, dass eine von mir vorab formulierte
MECHANISMUS-Vermutung im Vorzeichen falsch lag (par.9.1 k1-Abhaengigkeit,
par.9.2 Fokus durch Superadditivitaet, jetzt Rang gegen Summe). Alle drei
waren aus dem Code hergeleitet und klangen zwingend. Die Lehre ist nicht "besser
herleiten", sondern: **eine Herleitung aus dem Code ist eine Hypothese, kein
Befund** -- sie gehoert vorregistriert und gemessen, nicht als Begruendung in
eine Zusammenfassung.

Warum das Tiling nichts tut, ist damit OFFEN und ausdruecklich nicht erklaert.
Eine naheliegende Vermutung waere, dass `tiling_preference_for_cells_weighted`
ohnehin nur zwischen wenigen Kandidaten des DFS-Budgets waehlt und die
Gewichtung dort selten den Ausschlag gibt -- aber das ist wieder eine
Herleitung, und die ungepruefte Sorte davon hat hier dreimal danebengelegen.

**ENDGUELTIG fuer den Phasenfaktor:** ueber drei Arme und 65 gemessene Formen
(par.11 eine feste, par.13 sechzehn, par.14 achtundvierzig) bewegt sich
nichts. `SPALTEN_PHASE` und die drei Diagnose-Knoepfe bleiben im Code, Default
aus. Ein weiterer Formvorschlag braucht ein neues Argument, keinen neuen
Entwurf.

## par.15 Erreichbarkeit als MASS statt als TOR (VORREGISTRIERT 2026-08-25)

**Anlass: Nutzer-Einwand 2026-08-25** zum negativen Ergebnis von par.12 --
"dann hast vielleicht den filter nicht sauber modelliert, ueberleg dir hier
ein alternatives konzept". Der Einwand trifft: par.12 war kein
Kalibrierungsfehler, sondern ein Modellierungsfehler.

**Der Fehler, benannt.** `cell_is_completable` beantwortet eine BINAERE Frage
(reicht die Restversorgung fuer diese Zelle?), aber die Spaltenwertung zahlt
STETIG und konvex: `(fuellung/6)^2 * 7` (`scoring.rs`, Zweig 1) belohnt auch
den Schritt von 4 auf 5, obwohl die Spalte nie voll wird. Der Filter hat genau
diesen Teilfortschritt auf 0 gesetzt -- gemessen volle Spalten 0,794 auf
0,431 (t=-5,03), und der Verlust war groesser, wo die Spalten-Platte AKTIV
ist (-0,500 gegen -0,324), also dort, wo Teilfortschritt Punkte bringt.

**Das Ersatzkonzept.** Dieselbe Relaxation, aber GEZAEHLT statt gelesen:

```
f_max(c) = Fuellstand(c) + noch bedienbare leere Zellen(c),  gedeckelt bei 6
Gewicht der Spalten-Stufen von c  *=  (f_max(c) / 6)^2
```

Drei Eigenschaften, die der Filter nicht hatte:

1. **Nichts faellt auf 0**, solange die Spalte irgendeinen Ertrag tragen kann.
   Eine Spalte, die hoechstens auf 4 kommt, behaelt 44 Prozent statt null.
2. **Die Gewichtung folgt derselben Kurve wie die Endwertung**, statt eine
   eigene Schwelle zu erfinden. Der Faktor IST der Anteil des
   Spalten-Ertrags, der noch erreichbar ist.
3. **Die Orientierungswahl bleibt unangetastet.** Der zweite Schaden in par.12
   war das spaete Umschwenken, das die Festnagelung ab Runde 3 aufhob -- den
   Bauschritt, der die Partien mit voller Spalte von 35 auf 50 Prozent
   gehoben hat. Hier wird ausschliesslich gewichtet, nie umgeschaltet. Der Arm
   misst damit genau EINEN Unterschied.

**Messung:** `V2Huelle` gegen `V2HuelleReach`, Aufbau wie par.8.4 (je 80
gepaarte Partien, beide Sitze, 150 Sims, Seed 20260825, Bloecke zu 16).

**Entscheidungsmass:** volle Spalten je Partie, gepaart, Block-Ebene.
**Waechter:** Vollendungsquote >= 0,53.

**KEINE VORHERSAGE.** In diesem Strang lagen drei von mir vorab formulierte
Mechanismus-Vermutungen im Vorzeichen falsch (par.9.1, par.9.2, par.14.2),
alle drei aus dem Code hergeleitet und alle drei zwingend klingend. Eine
vierte waere Rauschen. Die Begruendung oben erklaert, warum par.12 GESCHEITERT
ist -- sie sagt nicht voraus, dass dieser Arm gewinnt.

**Was ein negatives Ergebnis dann hiesse:** dass die Vollendbarkeits-Relaxation
im Routing ueberhaupt nichts beitraegt -- weder als Tor noch als Mass. Das
waere der sauberere Schluss als par.12 allein, weil dann die Bauform und nicht
die Modellierung widerlegt ist.

### par.15.1 ERGEBNIS (2026-08-25): auch als MASS negativ -- die Bauform ist widerlegt

`evaluations/artifacts/v2_envelope_arena_reach.json`, n=160 gegen `V2Huelle`, 16,4 s.

| Kennzahl | Huelle | Reach | Delta | t (Block) |
| --- | --- | --- | --- | --- |
| volle Spalten | 0,794 | **0,569** | **-0,225** | -3,52 |
| max Spaltenhoehe | 5,569 | 5,381 | -0,188 | -3,56 |
| Teilspalten >= 3 | 2,975 | **3,119** | **+0,144** | +2,16 |
| Teilspalten >= 4 | 2,038 | 1,913 | -0,125 | -3,25 |
| Spezialfeld-Freischaltungen | 0,988 | 1,012 | +0,025 | 0,33 |
| eigene Punkte | 44,01 | 40,34 | -3,663 | -2,25 |

Siegquote 0,431. Vollendungsquote 0,692 (Waechter haelt).

**Die bessere Modellierung hat geholfen, aber das Vorzeichen nicht gedreht:**
-0,225 gegen -0,362 beim harten Filter. Der Nutzer-Einwand war also richtig
(par.12 WAR schlecht modelliert), und er reicht trotzdem nicht.

**Damit gilt der vorab festgeschriebene Schluss:** die
Vollendbarkeits-Relaxation traegt im ROUTING nichts bei -- weder als Tor
(par.12) noch als Mass (par.15). Widerlegt ist jetzt die Bauform, nicht meine
Modellierung.

**Das Muster ueber vier Arme, und es ist staerker als jede meiner
Herleitungen:** par.9.1 (Plattenpunkte), par.9.2 (erwartete Punkte), par.12
(Filter), par.15 (Skalierung) zeigen ALLE dieselbe Signatur -- Teilspalten >= 3
steigen, volle Spalten und maximale Hoehe fallen. Jeder Versuch, die Zielkarte
auf den Zustand REAGIEREN zu lassen, hat sie verbreitert und verschlechtert.
Die Staerke der Prio-Leiter kommt offenbar aus dem UNBEDINGTEN Fokus: eine
Vorgabe, die dem lokalen Gradienten widerspricht und sich nicht davon
abbringen laesst.

Das ist ein Muster aus vier unabhaengigen Messungen, keine Code-Herleitung --
und damit belastbarer als die drei Mechanismus-Vermutungen, die in diesem
Strang im Vorzeichen falsch lagen.

**Fuer die Relaxation heisst das NICHT "unbrauchbar", sondern "nicht im
Routing".** Als Kostenterm steckt sie laengst in `column_build::cell_cost`,
und die Verwendungen ausserhalb des Routings sind ungeprueft (Netz-Eingabe,
Deckel in der v2-Bewertung, Beschneidung des Tiling-DFS).

## par.16 Deckel auf den vorausschauenden Reihen-Kredit (VORREGISTRIERT + GEMESSEN 2026-08-25)

**Prämissen-Korrektur vorweg.** Die erste Fassung dieser Idee lautete "die
Plattenbewertung kreditiert Spaltenfuellung, als waere Vollendung moeglich".
Das ist FALSCH und wurde vor dem Bau geprueft: `scoring.rs:166` rechnet
`col_fill`, also den REALISIERTEN Fuellstand. Es gibt dort keine Projektion
und nichts zu deckeln.

Vorausschauend ist genau ein Posten: `heuristic_v2::REIHEN_KREDIT` -- ein
handgesetzter Kredit dafuer, dass eine begonnene lange Reihe sich noch
auszahlt. Zahlt sie in eine Spalte ein, die hoechstens auf 4 kommt, ist er zu
hoch. `V2HuelleCap` skaliert ihn mit `(f_max/6)^2`, derselben Kurve, mit der
die Endwertung die Spalte bezahlt. **Das ROUTING ist unveraendert das der
Huelle** -- der Arm misst genau den Bewertungs-Unterschied.

**ERGEBNIS (n=160):** H0.

| Kennzahl | Huelle | Cap | Delta | t |
| --- | --- | --- | --- | --- |
| volle Spalten | 0,819 | 0,856 | +0,037 | 0,59 |
| max Spaltenhoehe | 5,562 | 5,594 | +0,031 | 0,47 |
| Spezialfeld-Freischaltungen | 0,994 | 1,012 | +0,019 | 0,17 |
| Strafpunkte | -13,59 | -13,48 | +0,119 | 0,13 |
| eigene Punkte | 44,15 | 44,99 | +0,844 | 0,58 |

Siegquote 0,519, Vollendungsquote 0,705.

**Kein Effekt -- aber der erste zustandsabhaengige Mechanismus in diesem
Strang, der nicht SCHADET.** par.9.1, par.9.2, par.12 und par.15 haben alle
die Breiten-Signatur gezeigt (Teilspalten >= 3 hoch, volle Spalten runter);
hier steigen beide leicht (+0,025 und +0,037). Der Unterschied zu jenen vier:
sie haben die ZIELKARTE zustandsabhaengig gemacht, dieser Arm die BEWERTUNG.

**Nicht ueberlesen:** alle sieben Kennzahlen zeigen nach oben, aber alle Arme
teilen denselben Seed-Satz -- eine gemeinsame Verschiebung erklaert das
genauso gut wie ein Effekt. "7 von 7 positiv" ist hier KEIN unabhaengiger
Beleg, und kein einzelnes t kommt ueber 0,59. Der Befund ist H0.

**Der Deckel bleibt im Code** (Variante, Default aus). Er kostet nichts und
ist begrifflich richtig; ihn wieder auszubauen waere Aufwand ohne Gewinn.

## par.17 Bindet das Tiling-Knotenbudget? (GEMESSEN 2026-08-25) -- NEIN, deutlich nicht

**Anlass.** Als dritte moegliche Verwendung der Vollendbarkeits-Relaxation
stand die Beschneidung des Tiling-DFS im Raum: tote Spalten nicht mehr
durchsuchen, damit Budget frei wird. Die Vermutung stuetzte sich auf einen
Kommentar im Bestand (`plate_builder::v2_chip_preference`), der die fehlenden
Chip-Vollendungen dem Knotenbudget zuschrieb.

**Nutzer-Vorgabe 2026-08-25:** erst zaehlen, dann bauen. Gebaut wurde deshalb
NUR ein Zaehler (`tiling_solver::TILING_BUDGET_STATS`, rein additiv, ueber
`mosaic_rust.tiling_budget_stats_json()` lesbar).

**Ergebnis** (40 Partien Huelle gegen Huelle, 150 Sims):

| Groesse | Wert |
| --- | --- |
| Aufrufe von `top_k_tilings` | 1671 |
| Budget erschoepft | **0** (0,00 %) |
| Knoten je Aufruf | **5,4** von 2000 |

Das Budget wird zu **0,27 Prozent** ausgenutzt und bindet an keiner Stelle.
**Die Beschneidung wuerde nichts freimachen, weil nichts eingeschraenkt ist.**
Der Arm ist damit erledigt, bevor eine Zeile dafuer gebaut wurde -- Kosten:
ein Zaehler und vier Minuten statt eines vollen Arms.

**Ein Bestands-Kommentar wird dadurch messbar falsch, und ist korrigiert.**
`v2_chip_preference` erklaerte die fehlenden Chip-Vollendungen damit, die
Suche finde sie "im DFS-Budget (2000 Knoten) offenbar nicht zuverlaessig --
die Verzweigung ueber Chip-Allokationen ist teuer". Bei 5,4 genutzten Knoten
und null Erschoepfungen kann das nicht stimmen.

**Was daraus FOLGT und was nicht.** Die Suche laeuft vollstaendig durch und
findet die Chip-Schritte trotzdem nicht -- die Ursache liegt also in der
Kandidaten-Erzeugung oder in der Bewertung, nicht in der Tiefe. WELCHE von
beiden, ist offen. Eine weitere Herleitung aus dem Code waere die vierte in
dieser Sitzung, und drei davon lagen im Vorzeichen falsch; wer das klaeren
will, misst es.

**Methodischer Ertrag, ueber diesen Arm hinaus:** eine Erklaerung, die als
Kommentar im Code steht, ist keine Messung. Diese hier hat monatelang
unwidersprochen dagestanden und eine Bau-Idee getragen, die nichts gebracht
haette.

## par.18 Repariert die Huelle die Blindzieh-Pathologie nebenbei? (GEMESSEN 2026-08-25) -- NEIN

**Anlass.** Die Parallelsitzung vermutete, der Spaltenbau koennte die tiefen
Blindziehungen bei aktiver Wertungsplatte 6 von selbst abstellen: freigeschaltete
Spezialfelder senken `special_empty` und heben damit das Brettniveau, an dem
`resolve_and_apply_stack_draw` seine Stopp-Entscheidung faellt. Die Huelle
schaltet 1,512 Felder je Partie frei gegen 0,713 bei v2 (par.8.5) -- die
Groesse bewegt sich also stark in die richtige Richtung.

**Zwei Messungen, zwei Seiten derselben Frage.** Die Parallelsitzung hat den
MECHANISMUS auf konstruierten Brettern geprueft (`PREREG_stack_draw_reservation_rule.md`
par.6d): die Ziehtiefe bleibt ueber den ganzen Spalten-Fuellbereich bei 9,
weil Kriterium 1 quadratisch zahlt (`7*(f/6)^2`) waehrend das
Spezialfeld-Defizit linear und sofort kostet (`-3` je Feld). Hier steht die
WIRKUNG im echten Spiel.

**Aufbau:** derselbe Lauf wie par.8.5 (v2 gegen Huelle, n=160), zusaetzlich
gezaehlte Blindziehungen. **GEZAEHLT, nicht aus dem Punktestand abgeleitet** --
bei Punktestand 0 ist eine Ziehung gratis und im Punktestand unsichtbar
(`game.rs:182`), und zwar UNGLEICHMAESSIG: der tiefer ziehende Arm wird
staerker abgeschnitten, ein Armvergleich ueber Punktdifferenzen
unterschaetzte den Unterschied also systematisch. Hinweis der
Parallelsitzung, vor dem Lauf eingebaut.

| Groesse | v2 | Huelle | Delta | t (Block) |
| --- | --- | --- | --- | --- |
| Ziehungen je Partie | 1,869 | **2,925** | **+1,056** | 4,94 |
| davon k6 AKTIV (n=52) | 2,596 | 3,308 | +0,760 | 1,71 |
| davon k6 INAKTIV (n=108) | 1,519 | 2,741 | **+1,276** | **6,80** |

**Die Vermutung ist doppelt widerlegt.** Die Huelle zieht MEHR statt weniger,
und der Zuwachs ist GROESSER, wo Kriterium 6 gar nicht liegt -- also
ausserhalb der Pathologie. Waere der vermutete Mechanismus am Werk, muesste es
genau umgekehrt sein.

**Was stattdessen passiert, und es ist ein eigener Befund:** die Huelle hat ein
Zielbild und KAUFT gezielt Platten dafuer. Jede Ziehung kostet 1 Punkt, sie
zahlt also rund 1,06 Punkte je Partie mehr an den Stapel -- und gewinnt dabei
8,07 (par.8.5). Das ist ein Handel, kein Symptom. Die Plattenwahl ist seit dem
Bauschritt "Kuppelplatten-Wahl verdrahtet" Teil des Routings (volle Spalten
0,450 auf 0,588), und dass sie sich auch das Ziehen etwas kosten laesst, ist
die konsequente Fortsetzung.

**Vorbehalt zur Vergleichbarkeit:** hier sind ZIEHUNGEN JE PARTIE gezaehlt,
bei der Parallelsitzung war es die TIEFE EINER SERIE auf einem konstruierten
Brett. Die Zahlen stehen nebeneinander, nicht uebereinander.

**Fuer die Blindzieh-Spur heisst das:** der billige Ausweg ist zu. Die
Pathologie muss dort behoben werden, wo sie sitzt -- im Einheitenbruch der
Stopp-Regel -- und nicht durch besseres Spiel an anderer Stelle.

## par.19 v2 verlaesst den Quellstand (ENTSCHIEDEN + AUSGEFUEHRT 2026-08-27)

**Nutzer-Entscheid**, in zwei Schritten und mit ausdruecklicher Begruendung:
"V2 ist durch. Keine Entwicklung mehr. Sonst wuerde ich es nicht einfrieren."
(2026-08-26) und, auf die Frage nach den letzten beiden Messwerkzeugen,
"Split-Test als Ergebnis stehen lassen, die beiden anderen migrieren. ich will
nicht mehr allzu viel zeit mit der heuristik verschwenden" (2026-08-26),
schliesslich "mach das. ist eh alles im git versioniert" (2026-08-27).

### Was entfernt wurde

`HeuristikVariante` (9 Varianten), `heuristic_v2.rs` (554 Zeilen), die
v2-Routing-Haelfte von `plate_builder.rs` (39 Items, vom Compiler
als tot benannt -- nicht nach eigenem Urteil ausgewaehlt), die beiden
Arena-Einstiege `run_heuristic_v1_vs_v2_arena` und
`run_net_vs_heuristic_v2_arena` samt pyo3-Bindungen, sowie die Faedelung durch
`self_play.rs`, `mcts.rs`, `net_mcts.rs`, `referee.rs` und `lib.rs`.

**Bilanz, gemessen statt geschaetzt** (`git diff HEAD --numstat` ueber
`engine/` und `self_play.py`): +130 / -3.063, netto **2.933 Zeilen**. Davon
1.429 in `plate_builder.rs`, 705 in `self_play.rs`, 554 als ganze Datei
`heuristic_v2.rs`, 184 in `mcts.rs`.

Zu jeder Funktion `X` gab es einen Zwilling `X_variante`; die Zwillinge sind
mit ihren Wrappern verschmolzen. Der V1-Zweig war in jedem Fall der
Bestandsrumpf -- die Verschmelzung ist deshalb keine Umschreibung des Ankers,
sondern das Entfernen einer Weiche, die nur noch einen Ausgang hatte.

### Was ausdruecklich BLEIBT

- **Das Spec-Feld `heuristik_variante`** ist weiter PFLICHT. Die Specs der
  eingefrorenen Artefakte tragen es; ein weggelassenes Pflichtfeld waere ein
  stiller Vertragsbruch. Eine Spec mit `v2*` wird jetzt HART ABGEWIESEN
  (`net_mcts.rs::from_spec_file`, Test
  `search_config_from_spec_file_rejects_v2_variante`).
- **Das CLI-Flag `--heuristik-variante`** bleibt, mit `choices=["v1"]`. Ein
  alter Kampagnen-Aufruf soll LAUT scheitern statt still einen anderen Korpus
  zu erzeugen -- genau der Fehler vom 2026-08-26 (Flag vergessen, Default v1,
  Korpus bitgleich, falscher Befund committet).
- **Beide Artefakte bleiben lauffaehig**, auf ihrem MITGELIEFERTEN Wheel:
  `models/frozen_heuristics/v1_anchor/` (Elo-Anker) und
  `models/frozen_heuristics/v2huelle_generator/` (Erzeuger des v22-Korpus).
  Genau dafuer ist die Kapselung gebaut. Die mit v2huelle erzeugten Korpora
  in `data/` sind unberuehrt.

### Die drei Messwerkzeuge, und warum sie verschieden behandelt wurden

| Werkzeug | Los | Grund |
|---|---|---|
| `frozen_agent_referee_probe.py` | MIGRIERT | beide Arme SIND Artefakte |
| `v2_envelope_arena.py` | stillgelegt | Arm `v2`-plain ist kein Artefakt |
| `v2_teacher_arena.py` | stillgelegt | dito, Netz gegen `v2`-plain |

Die Trennlinie ist nicht Bequemlichkeit, sondern die Kapselungsregel: eine
Messung laeuft ueber Artefakte. `v2`-plain war nie Champion und nie Erzeuger,
sondern ein Vergleichsarm -- dafuer ein Artefakt zu bauen, waere Aufwand ohne
benannten Nutznieser. Beide Dateien bleiben mit einem Stillegungs-Kopf
STEHEN, als Beleg dafuer, wie das registrierte Ergebnis zustande kam.

Dieselbe Linie hat schon der Split-Test bekommen (par.8.5): ein Ergebnis, kein
laufendes Werkzeug.

### Kollateral, ausdruecklich benannt statt still weggeraeumt

Die SOLL-Seite von `PREREG_stack_draw_reservation_rule.md` par.5
(`stack_draw_soll_seite`, `plate_value_anschluss_check` in `self_play.rs`) hat
`plate_builder::expected_points_map` als Plattenwert-Schaetzer benutzt --
"Platte probeweise legen, DANACH bewerten". Diese Karte war Teil des
v2-Routings und ist mitgefallen; die beiden Testmodule sind entfernt.

**Das registrierte Ergebnis bleibt gueltig**, nachrechnen laesst es sich auf
dem heutigen Build nicht mehr. Wer es je wieder braucht, holt
`expected_points_map` samt `points_map` und `most_available_color` aus der
Historie unmittelbar vor diesem Commit.

**Ebenfalls mitgefallen sind par.12 (Vollendbarkeit als FILTER) und par.15
(Erreichbarkeit als MASS)** -- beide sassen auf der v2-Zielkarte. Beide waren
zum Zeitpunkt der Entfernung bereits NEGATIV entschieden (par.12.1, par.15.1),
es geht also kein offener Arm verloren; sie sind mit dem Zweig ERLEDIGT, nicht
offen. (Vermerk 2026-08-28, aus dem Statuskopf hierher verschoben.)

### Belege

- Suite gruen, `cargo check --all-targets` ohne neue Warnung (die einzige,
  `net.rs::split_planes_flat_batch`, ist Altbestand -- gegen `git stash`
  geprueft).
- `frozen_agent_referee_probe.py` liefert seine festgenagelten Werte
  UNVERAENDERT: `v1_anchor [27,15]/159`, `v2huelle_generator [63,27]/163`.
  Das ist der eigentliche Beleg der Kapselung: v2 ist aus dem Quellstand
  verschwunden, und das v2-Artefakt spielt trotzdem Zug fuer Zug dieselbe
  Partie -- weil es sein eigenes Wheel mitbringt.
