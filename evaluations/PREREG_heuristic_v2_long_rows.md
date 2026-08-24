<!-- STATUS: OFFEN | Frage: Kann ein ZWEITER Heuristik-Lehrer, dessen Bewertung die Musterreihen sieht, langes-Reihen-Spiel ueberhaupt erst erzeugen -- und laesst er sich neben den eingefrorenen Elo-Anker stellen, ohne ihn anzufassen? | Beleg: ENTWURF-Stand 2026-08-24, nichts gebaut, Nutzer-Vorgabe "v2 als ZUSAETZLICHER Anker". VORFRAGE ENTSCHIEDEN: der Lehrer kann es auch nicht (407 Partien Netz@400 gegen Heuristik@150, Vollendungsquote 0,538 gegen 0,563, volle Spalten 0,101 gegen 0,098) -- Destillation scheidet aus, es gibt nichts zu uebertragen. Gegenreferenz aus zehn Mensch-gegen-Netz-Partien in static/log (Nutzer gewinnt 8 von 9): Abschlussprofil 4,00/4,10/3,40/3,20/2,50/2,20 gegen 4,90/4,90/3,30/2,40/1,10/0,50, volle Spalten 1,80 gegen 0,10. Strukturbefund im Code: wertung_progress liest NUR das Kuppelraster (scoring.rs:876-882), ist innerhalb einer Runde fuer jeden Drafting-Zug gleich und kann die Reihenwahl nicht lenken; das einzige Stueck des Shapings, das pattern_lines liest, ist projected_unplaceable_penalty -- eine STRAFE. ZIEL-KENNZAHL folgt aus einer Identitaet: eine volle Spalte kostet 21 Zellen, das Netz verbraucht 42,7 und truege damit gleichverteilt 2,03 Spalten statt 0,10 -- ein VERTEILUNGS-, kein Versorgungsproblem; die Kennzahl ist das MINIMUM der Abschluesse ueber die sechs Reihen, das Zielprofil ist FLACHER statt laenger. Dritter Versorgungskanal (Nutzer-Hinweis): 9 Spezialfliesen, vierte Plattenzelle zum Preis von dreien, lokale Freischaltbedingung, rund 4 Felder je Partie leer gelassen (groesster Einzelposten der Plattenwertung). Offen und VOR dem Bau zu entscheiden: wie v2 ueberhaupt als eigener Agent existiert, ohne den spec-freien Heuristik-Anker anzufassen -->

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
