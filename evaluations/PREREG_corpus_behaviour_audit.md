<!-- STATUS: OFFEN | Frage: Zeigen die drei Verhaltensmuster, die beim Spielen gegen den Champion auffielen, sich auch im Korpus, und in welcher Groessenordnung? | Beleg: Quellenfrage GEKLAERT (par.3), alle drei Arme aus den vorhandenen Records messbar. Korpuslauf ERST MIT v29 (Nutzer 2026-09-11). Arm A1 ist an lebenden Partien schon belegt (par.7, g06/g07 gegen v28-b02): bei Punktestand 0 zog das Netz 13/8/7/4 Platten je Zug, bei Stand >0 genau eine, und in g06 fiel niemand auf 0 -- kein einziger Mehrfachzug. Am Korpus nichts gemessen. -->

# Vorregistrierung: Verhaltens-Audit am Korpus (drei Arme aus den Claude-Partien)

**Angelegt 2026-09-11.** Anlass sind die vier selbst gespielten Partien g02 bis g05 gegen
`v27-b01_brierbest` @400 (`PREREG_claude_play_interface.md` par.7). Sie haben drei Muster
gezeigt, die eine Arena aus Bauart nicht zeigen kann, weil sie auf beide Seiten gleich
wirken oder gar nicht in der Siegquote landen. Diese Prereg macht aus den vier
Einzelbeobachtungen drei Messungen mit grossem n.

**Diese Prereg TRAEGT Kanal 4** aus `PREREG_dome_stack_information_sets.md` par.11
("Anomalie-Report ... 13 Stapelziehungen in einer Runde waeren dort oben gestanden").
Arm A ist seine Spezifikation; die Beobachtung aus den Partien liefert sie mit.

## par.1 Was heute da ist (am Code geprueft 2026-09-11)

- **Die Zwangsraeumung steht schon im Log.** `engine/src/game.rs:869` und `:966` schreiben
  `"⚠️ {name}: Musterreihe {} ({}) nicht platzierbar → {n}× Strafleiste"`. Jedes Log mit
  `--log-games` traegt sie; es braucht keinen Engine-Eingriff.
- **Ausgewertet wird sie nirgends.** `tools/analyze_game_log.py` kennt den Ausdruck nicht
  (grep leer, 2026-09-11).
- **Die Wertungsplatten SIND kodiert.** `engine/src/features.rs:804` one-hot ueber die acht
  Platten, `:1306` schaltet im 2D-Encoder plattenabhaengige Ebenen (Zeilen, Spalten,
  Diagonalen, Rand). Arm C ist damit eine Frage an den gelernten Prior, nicht an die
  Merkmale.
- **Die Ziehungen sind als Regel entschieden**, nicht als Verhalten:
  `PREREG_score_clamp_incentive.md` par.11 (Nutzer 2026-09-10). par.10 derselben Prereg
  misst 3,1 Gratis-Ziehungen je Partie und Seite bei 39 % Partien mit Stand 0 -- eine
  Mittelung ueber alle Partien, nicht bedingt auf den Zustand.
- **Die Vollendungsfrage ist offen.** `PREREG_long_row_payoff.md`: Vollendungsquote
  beidseits rund 0,53, "B2 muss die VOLLENDUNG heben (Trainingsfrage)". Arm B ist der
  schaerfste Teilfall davon: die Reihe wird nicht nur nicht vollendet, sie ist gar nicht
  mehr platzierbar.

## par.2 Die drei Arme

### Arm A -- Anomalie-Report (Kanal 4), zwei Zaehler

**A1 Ziehungen je Plattenplatzierung, BEDINGT auf den Punktestand.**
n = alle Plattenplatzierungen mit mindestens einer Ziehung, Grundmenge = Plattenplatzierungen
je Seite und Runde, Einheit = Ziehungen je Platzierung. Aufgeteilt in Stand 0 und Stand > 0
VOR der ersten Ziehung dieser Platzierung.
*Vorab-Erwartung (aus g02-g05, also n = 4, ausdruecklich Hypothese):* bei Stand > 0 nahe 1,
bei Stand 0 zweistellig.

**A2 Zwangsraeumungen.** n = alle Partien des Korpus, Grundmenge = Partien je Seite,
Einheit = Vorfaelle je Partie und Steine je Vorfall, aufgeschluesselt nach Musterreihe (0-5)
und Runde.
*Vorab-Erwartung:* die Vorfaelle haeufen sich in den Reihen 4 und 5 und in den Runden 4-5.

### Arm B -- kostet der Sturz auf 0 die Partie?

Das Netz fuhr sich in g02, g03 und g04 in Runde 1 selbst auf 0 und verlor alle drei; in g05
fiel es nie auf 0 und gewann. **Das ist bei n = 4 reines Rauschen und hier nur die
Hypothese**, nicht der Befund.

Messgroesse: Siegquote der Seite, gruppiert danach, ob sie in RUNDE 1 auf 0 faellt.
n = alle Korpuspartien, Grundmenge = Seiten (zwei je Partie), Einheit = Siege je Seite.
**Der Rueckwaerts-Konfounder ist benannt und behandelt:** wer spaeter auf 0 faellt, tut das
womoeglich, WEIL er verliert. Runde 1 schliesst das weitgehend aus -- dort startet jede Seite
bei 5 Punkten, und der einzige Weg nach unten sind die eigenen Ziehungen. Spaetere Runden
werden getrennt ausgewiesen, aber nicht als Beleg verwendet.
*Falsifikator:* liegt die Differenz der Siegquoten im Rauschen (Blockgroesse 5, gepaarte
Auswertung auf Blockebene), ist das Muster aus den vier Partien erledigt und wird nicht
weiterverfolgt.

### Arm C -- konditioniert das Netz auf die ausliegenden Wertungsplatten?

In g02 baute es ZWEI volle Spalten, obwohl die Spaltenplatte nicht auslag, und liess dafuer
drei Spezialfelder leer (-9). Die Information liegt an (par.1).

Messgroesse, je Zielstruktur und je Seite: volle Spalten mit und ohne Platte 1 (Vertikale
Reihen), vollstaendige Eckplatten mit und ohne Platte 5 (Eckplatten), leere Spezialfelder mit
und ohne Platte 6 (Spezialfelder), farbenreiche Zeilen mit und ohne Platte 7.
n = alle Korpuspartien, Grundmenge = Partien je Plattenkombination, Einheit = Strukturen je
Partie.
*Falsifikator:* unterscheiden sich die Raten nicht ueber das Rauschen hinaus, konditioniert
der Prior nicht auf die Platten. Das waere ein Befund mit Folgen fuer den Leitstern-Hebel
Plattenblick -- und es waere KEIN Beweis, dass ein plattenbedingter Kopf hilft, sondern nur,
dass der heutige es nicht tut.

## par.3 Bauform

EIN Werkzeug, `tools/probes/corpus_behaviour_audit.py`, das vorhandene Partielogs liest und
ein JSON je Lauf schreibt (mit `laufzeit`-Block nach CLAUDE.md). Keine Engine-Aenderung, kein
neues Self-Play, keine Arena. A1 und B brauchen dieselben Logzeilen (die Zieh- und
Punktzeilen), A2 die Raeumungszeile, C das Endraster plus `scoring_tile_ids` aus der
Kopfzeile. Auswertung auf BLOCK-Ebene (Blockgroesse 5), wie fuer jede Score-Analyse in
diesem Projekt vorgeschrieben.

**GEPRUEFT 2026-09-11 -- die Quelle sind die RECORDS, nicht Partielogs.** Der Punkt war
falsch gestellt und ist damit erledigt:

- `--log-games` ist ein ARENA-Flag (`tools/paired_arena_arm_worker.py:101`, durchgereicht an
  `net_arena_match`), kein Self-Play-Flag. `self_play.py` schreibt ueberhaupt keine
  Partielogs (grep ueber die Datei, 2026-09-11), und `tools/night_v28_generate.sh` ruft es
  ohne so ein Flag auf. Es gibt also keine Self-Play-Partielogs, in keiner Generation.
- **Der Record traegt den Log aber selbst mit.** Jeder Datensatz hat `state.log`, ein
  mitlaufendes FENSTER der letzten Zeilen (im letzten Record einer Partie rund 30 von rund
  300). Da es je Zug einen Record gibt, ueberlappen die Fenster; wer sie ueber die Records
  einer Partie ueberlappend zusammensetzt, bekommt den vollstaendigen Log zurueck.
- **Die Zusammensetzung muss ueber die UEBERLAPPUNG laufen, nicht ueber eine Menge.**
  Gemessen an `data/selfplay_v27-b01-policy_20260910_2350_g10.pkl`: 301 gegen 299, 348 gegen
  340, 313 gegen 309, 339 gegen 333 Zeilen. Gleiche Zeilen kommen in einer Partie mehrfach
  vor; ein `set` verliert sie.
- **Alle drei Arme sind damit aus dem vorhandenen Korpus messbar**, ohne neue Erzeugung: die
  Ziehzeile traegt den Punktestand mit (`📦 Netz: 1. Kachel vom Stapel gezogen (Rueckseite:
  Special) −1 Pkt → 4 Gesamt`), die Raeumungszeile steht drin, und `state` enthaelt
  `scoring_tile_ids`, `round`, `players` samt Punkten und das Raster.

**Erste Zahlen aus der Stichprobe** (n = 4 Partien aus einer Datei, Grundmenge Partien,
Einheit Vorfaelle je Partie -- eine Vorschau, kein Ergebnis): Stapelziehungen 4, 24, 5, 36;
Zwangsraeumungen 0, 1, 2, 2. Die Spreizung bei den Ziehungen ist genau das Muster aus den
Claude-Partien und der Grund, warum A1 auf den Punktestand bedingt werden muss statt zu
mitteln (`PREREG_score_clamp_incentive.md` par.10 mittelt und kommt auf 3,1).

## par.4 Kosten

Reines Parsen, kein Rechenlauf; nach Erfahrung mit `analyze_game_log.py` unter 0,5 s je
Partie (par.8.12a der Einhuellenden). Bau des Werkzeugs geschaetzt zwei bis drei Stunden
(ANNAHME). Der Lauf darf neben der laufenden Erzeugung stattfinden, sobald das Lesen der
Logs die Erzeugung nicht stoert; im Zweifel danach.

## par.5 Was aus den Zahlen NICHT folgt

Kein Elo-Knoten, keine Champion-Entscheidung, kein Trainingsziel. Arm A und B sagen, WIE OFT
etwas passiert, nicht, ob es falsch ist: eine unplatzierbare Reihe zu fuellen kann richtig
sein, wenn sie dem Gegner Steine entzieht, und bei Stand 0 ist die Stapel-Durchsicht
regelkonform und gratis (Regelbuch S.4/S.9). Ein Suchfilter oder ein Trainingsterm waere ein
eigener Arm mit eigener Vorregistrierung -- erst die Rate, dann die Frage.

## par.6 Reihenfolge

1. Klaeren, ob Partielogs vorliegen (par.3).
2. Werkzeug bauen, an den vier Claude-Logs gegenpruefen: es muss dort A1, A2 und C exakt die
   Zahlen liefern, die in `PREREG_claude_play_interface.md` par.7 von Hand stehen. Das ist
   der Selbsttest.
3. Lauf ueber den Korpus, Ergebnis hier in par.7.
4. Verdikt je Arm, Statuskopf nachziehen, Index neu erzeugen.

## par.7 Ergebnisse

**Am Korpus: nichts gemessen** (der Lauf kommt mit v29, par.8 P.1).

**Aus LEBENDEN Partien liegt Arm A1 aber bereits belegt vor (2026-09-11, g06/g07 gegen
`v28-b02_brierbest`, `PREREG_claude_play_interface.md` par.7).** Das ist keine
Korpusmessung und ersetzt sie nicht -- es ist die Vorhersage des Arms an zwei Partien, und
sie trifft in beide Richtungen:

| Partie | Zug | Punktestand VOR dem Zug | Ziehungen in diesem Zug |
| --- | --- | --- | --- |
| g06 | Netz R1/R2/R3/R4 | 5 / 7 / 12 / 28 | 1 / 1 / 1 / 1 |
| g07 | Netz R1 | 5 | **13** (fuenf bezahlt, dann Stand 0) |
| g07 | Netz R2 | 0 | **8** |
| g07 | Netz R2 | 0 | **7** |
| g07 | Netz R3 | 0 | **4** |
| g07 | Netz R4 | 12 | 1 |
| g07 | Claude R2 | 7 | 2 |
| g07 | Claude R3 | 0 | 1 |

n = 12 Zuege mit Ziehung, Grundmenge die beiden Partien g06/g07, Einheit Ziehungen je
Plattenzug. Bei Stand > 0: 1,17 im Mittel (7 Ziehungen in 6 Zuegen, Maximum 2). Bei Stand 0:
6,6 (33 in 5 Zuegen, Maximum 13). In g06 fiel keine Seite je auf 0 -- und es gab keinen
einzigen Mehrfachzug. Die Gegenprobe steht damit dreimal (g05, g06 und der v28-Zug in g07
R4, nach Rueckkehr auf 12 Punkte).

**Was das fuer den Korpuslauf aendert: nichts am Aufbau, aber es schaerft die Erwartung.**
A1 misst dieselbe Groesse ueber Zehntausende Partien und liefert die Verteilung, nicht nur
das Vorzeichen; die Vorschau (par.3, Ziehungen 4/24/5/36 je Partie) passt zu dem hier
sichtbaren Mechanismus. Die Konfundierung bleibt dieselbe und wird dort behandelt: wer bei 0
steht, steht meist schlecht -- die Frage ist nicht, OB schlechte Lagen mehr ziehen, sondern
ob die Ziehzahl an der 0-Grenze SPRINGT. In g07 springt sie im selben Zug, in dem der Stand
die 0 erreicht (Ziehung 5 bezahlt, Ziehung 6 gratis, weitere acht folgen).


## par.8 Offene Nutzer-Entscheide

1. ~~Reihenfolge gegen die v28-Kette~~ **ENTSCHIEDEN (Nutzer 2026-09-11): der Lauf kommt
   erst mit v29.** Bis dahin bleibt diese Prereg vorregistriert und ungemessen; gebaut wird
   das Werkzeug, wenn v29 ansteht, gegen den dann vorliegenden Korpus.
2. **Umfang von Arm C:** nur `v27-b01` (der heutige Champion) oder die Kette v25/v26/v27, um
   zu sehen, ob die Plattenblindheit ueber die Generationen zu- oder abnimmt?
