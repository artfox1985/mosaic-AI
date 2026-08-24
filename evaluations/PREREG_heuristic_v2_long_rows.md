<!-- STATUS: OFFEN | Frage: Kann ein ZWEITER Heuristik-Lehrer, dessen Bewertung die Musterreihen sieht, langes-Reihen-Spiel ueberhaupt erst erzeugen -- und laesst er sich neben den eingefrorenen Elo-Anker stellen, ohne ihn anzufassen? | Beleg: MESSKETTE KOMPLETT 2026-08-24, v2 GEBAUT und variantengebunden (HeuristikVariante::V1/V2, Paritaets-Hash 8c6684ff haelt, Suite 512/0). Vorfragen: der Lehrer v1 kann es auch nicht (volle Spalten 0,098 gegen 0,101), such-seitig ist der Weg zu (scoring_plate_injection und long_row_payoff B1 beide negativ). Der Durchbruch kam vom PLATZIERUNGS-Routing, nicht von einem Bewertungsterm: best_first_step_inner waehlt nach reinen Sofortpunkten und warf jede Draft-Absicht weg. Schritt 2 (v1 gegen v2, 80 gepaarte Partien): volle Spalten 0,163 auf 0,562, Partien mit mindestens einer von 35 auf 50 Prozent, 5/6-Mauer durchbrochen. SCHRITT 3 (v2 gegen Champion, 407 Seeds je Arm, v1-Bezug auf denselben Seeds): Faehigkeit BELEGT, Preis HOCH -- volle Spalten 0,302 gegen v1 0,086 (gepaart +0,175, t=+7,79), Vollendungsquote 0,686 gegen 0,564 (B1-Vorgabe erfuellt), aber Siegquote gegen den Champion 0,128 gegen 0,256 und Marge -19,4 gegen -12,2. URTEIL STEHT AUS: par.5.3 hat bewusst keinen Schwellenwert, die Frage ist, ob das Netz die FAEHIGKEIT uebernimmt ohne das NIVEAU. Nebenbefund: volle Zeilen brechen gegen ein NETZ nicht ein (0,403 gegen 0,432) -- die Regression auf 0,200 war ein Artefakt des v1-gegen-v2-Aufbaus. OFFEN: par.5.4 Korpus und Training, Self-Play-Einstieg (Nutzer-Freigabe erteilt, nicht gebaut), Shaping-Kopf par.3b mit Abkling-Kurve und zwei Kanaelen, Einhuellende im 2D-Encoder. -->

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
