<!-- STATUS: OFFEN | Frage: Zeigen die drei Verhaltensmuster, die beim Spielen gegen den Champion auffielen, sich auch im Korpus, und in welcher Groessenordnung? | Beleg: Anlass sind g02-g05 (PREREG_claude_play_interface.md par.7): Ziehzahl folgt dem Punktestand (28/24/32 Ziehungen bei Stand 0, in g05 nur 7 ohne Stand 0), fuenf Zwangsraeumungen langer Musterreihen (einmal zehn Steine), Spaltenbau ohne Spaltenplatte. Drei Arme, alle aus vorhandenen Logs, kein Engine-Eingriff, keine neue Erzeugung. Nichts gemessen. -->

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

**UNGEPRUEFT und vor dem Bau zu klaeren:** ob die v27- und v28-Self-Plays mit `--log-games`
gelaufen sind. Ohne Partielogs braucht Arm A eine eigene, kleine Log-Erzeugung; Arm C kaeme
notfalls auch aus den Self-Play-Records, Arm A und B nicht.

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

Leer. Nichts gemessen.

## par.8 Offene Nutzer-Entscheide

1. **Reihenfolge gegen die v28-Kette:** sofort nach dem Lesen der Logs, oder erst nach Tor 1
   von `v28-b01`?
2. **Umfang von Arm C:** nur `v27-b01` (der heutige Champion) oder die Kette v25/v26/v27, um
   zu sehen, ob die Plattenblindheit ueber die Generationen zu- oder abnimmt?
