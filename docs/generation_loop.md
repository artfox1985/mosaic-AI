# Die Generationen-Schleife

**Kanonischer Ort seit 2026-08-31** (Nutzer-Auftrag: *"erstmal generationen
schleife erstellen die idealerweise spaltenverstaerkend ist und immer besser
wird von den siegen als die vorgaenger generation"*). Schwesterdatei zu
`promotion_checklist.md`: dort steht, was beim Champion-WECHSEL zu tun ist,
hier, wie eine Generation zustande kommt und woran sie gemessen wird.

**Diese Datei beschreibt das VERFAHREN fuer eine beliebige Generation N, nicht
einen konkreten Durchlauf.** Wo eine Generation eigene Zahlen, Zuschnitte oder
Arme hat, stehen die in ihrer eigenen Fenster-Prereg (`PREREG_vN_window.md`)
und der aktuelle Stand in `evaluations/STATUS.md`. Wer hier eine konkrete
Generation einsetzt, hat die Datei falsch benutzt.

Die Mechanik war laengst gebaut -- `self_play.py`, die Korpus-Sonden,
`train.py`, `tools/paired_gating.py`, `tools/elo_tracker.py`,
`tools/set_champion.py`. Was gefehlt hat, sind die vorab festgelegten TORE:
bis v22 wurde jeder Schritt einzeln entschieden.

## Begriffe (die Verwechslungen kosten sonst eine Generation)

* **Generation N** -- der Trainings-Durchlauf und seine Arme (`vN-b01`,
  `vN-b02`, ... nach `generation_naming.md`).
* **Vor-Generation N-1** -- die Generation davor. **Ihr BESTER STAND** (nicht
  ihr erster Arm) ist der Bezug beider Tore.
* **Generator** -- das Netz, das die Partien fuer das Fenster N spielt: der
  beste Stand von N-1. Nicht der Kandidat, der daraus entsteht.
* **Amtierender Champion** -- das Netz mit der hoechsten Elo-Kante. Kann aus
  einer ANDEREN Linie stammen als die laufende Schleife; siehe Falle (1).
* **Linie** -- eine Kette von Generationen, die auseinander hervorgehen. Eine
  neue Linie beginnt, wenn ein Zyklus bewusst mit anderem Material oder
  anderer Zielsetzung startet.

## Ein Durchlauf

| Schritt | Werkzeug | Tor |
| --- | --- | --- |
| 1. Erzeugen (Generator = bester Stand von N-1) | `self_play.py`, Zuschnitt nach `PREREG_vN_window.md` | -- |
| 2. Korpus pruefen | `tools/probes/corpus_column_outcome_symmetry_probe.py`, `tools/corpus_sanity_check.py` | **Tor 0** |
| 3. Fenster bauen | Datei-Liste + Cache-Bloecke (`tools/build_cache_incremental.py`) | -- |
| 4. Trainieren (Arme nach `generation_naming.md`) | `train.py` | -- |
| 5. Bester Kandidat gegen den besten Stand von N-1 | `tools/paired_gating.py` | **Tor 1** |
| 6. Spaltenprofil des Kandidaten | argmax-Instrument | **Tor 2** |
| 7. Kante gegen den amtierenden Champion messen und berichten | `tools/paired_gating.py` / `tools/elo_tracker.py` | -- |
| 8. Promotion, falls die Champion-Kante faellt | `promotion_checklist.md` | -- |
| 9. Der beste Stand von N erzeugt Generation N+1 | zurueck zu 1 | -- |

Schritt 7 faellt IMMER an, auch wenn Schritt 8 ausbleibt: ohne ihn weiss die
naechste Generation nicht, wie weit ihre Linie vom Champion entfernt ist.

## Tor 0 -- traegt der Korpus das Signal?

Wortlaut und Herleitung: `PREREG_heuristic_v2_long_rows.md` par.3b.12
(dort fuer die Spalten-Kampagne formuliert; die Form ist uebertragbar).

* **primaer, inhaltlich:** trennt die Zielgroesse der Kampagne den AUSGANG?
  (Symmetrie-Sonde auf der Value-Klasse, signifikant > 0.) Der Value-Kopf
  kann per Konstruktion nur lernen, was Sieg von Niederlage trennt; trennt es
  nicht, ist das Material wertlos -- unabhaengig von jeder Rate.
* **sekundaer, gegen Degeneration:** eine Mindest-EREIGNISZAHL im Korpus
  (nicht eine Rate -- eine Rate ignoriert die Korpusgroesse). Die Schwelle
  gehoert in die Fenster-Prereg der Generation, mit Herleitung.
* Raten sind Berichtsgroessen.

## Tor 1 -- Siege gegen den Vorgaenger (das Ratschen-Tor)

**Der beste Kandidat aus N schlaegt den besten Stand von N-1 in einer
gepaarten Arena, signifikant.** Instrument `tools/paired_gating.py` (SPRT,
Blockgroesse 5 seit 2026-08-29).

**Auflage, Praezedenz 2026-08-29:** ein SPRT-Fruehstopp unter 150 Paaren ist
eine INFORMATIVE Messung, kein Promotionsentscheid. Fuer eine Promotion gilt
n >= 150 Paare oder eine Replikation mit eigenem Seed. Grund: der Seed bewegt
die Metrik in diesem Projekt 4- bis 6-mal staerker als jeder Knopf, und bei
n=400 wurden 5,75 Prozentpunkte Streuung fuer IDENTISCHE Konfiguration
gemessen.

## Tor 2 -- die Kampagnen-Groesse darf nicht fallen (das Richtungs-Tor)

**Die Groesse, um die es der Kampagne geht, gemessen am gleichen Instrument
wie bei der Vor-Generation, darf nicht unter deren Wert fallen.** Aktuell ist
das der Spaltenbau (volle Spalten je Partie und Seite, argmax-Instrument);
wechselt die Kampagne ihr Ziel, wechselt die Groesse mit -- das Tor bleibt.

**Den Bezugswert holt man sich, indem man die Vor-Generation am selben
Instrument misst**, nicht aus dem Gedaechtnis und nicht aus einem Bericht mit
anderem Betriebspunkt. Fuer die erste Generation einer neuen Linie gibt es
keinen Vorgaenger: dann ist der Bezug der Gruendungswert, und er wird beim
Start der Linie festgehalten.

**Warum das ein eigenes Tor braucht und sich nicht aus den Siegen ergibt:**
weil Staerke und Kampagnen-Groesse gegeneinander stehen koennen. Gemessener
Praezedenzfall (2026-08-30, Suchtiefen-Strang): flach gesucht baut dasselbe
Netz rund 0,6 volle Spalten und VERLIERT Partien (25 gegen 400 Sims: 11:29),
tief gesucht 0,34 und gewinnt sie. Ein reines Sieg-Tor zoege die Schleife
also in die Richtung, die die Kampagne gerade abschaffen will.

**Als NICHT-FALLEN formuliert, nicht als Steigerung:** eine Steigerung je
Generation ist das Ziel, aber es gibt keinen Beleg, dass sie in jeder
Generation erreichbar ist -- die zweite DAgger-Runde war bereits gesaettigt.
Ein Tor, das Unmoegliches verlangt, wird umgangen; ein Tor gegen Rueckschritt
haelt.

## Wenn ein Tor reisst

Vorab festgelegt, damit es nicht im Einzelfall verhandelt wird.

* **Tor 0 reisst:** kein Training. Der Korpus ist das Material; ein
  degeneriertes Material trainiert man nicht "trotzdem mal". Bericht und
  Nutzer-Vorlage.
* **Tor 1 reisst, Tor 2 haelt:** keine Promotion, aber der Korpus bleibt im
  Fenster und der bisherige beste Stand erzeugt weiter. Die Schleife verliert
  eine Runde, nicht ihre Richtung.
* **Tor 2 reisst, Tor 1 haelt:** **keine stille Promotion.** Das ist der
  Fall, in dem die Schleife ihre Richtung verliert, ohne dass es weh tut --
  also der gefaehrlichste. Vorlage an den Nutzer mit beiden Zahlen; eine
  Promotion ist dann eine bewusste Entscheidung gegen das Richtungs-Tor,
  keine Nebenwirkung.
* **Beide reissen:** Generation verworfen, Ursachenanalyse vor dem naechsten
  Erzeugungslauf.

## Zwei Fallen, die die Schleife von selbst stellt

**(1) "Vorgaenger" ist NICHT "amtierender Champion".** Sobald eine Linie
neben einer aelteren Elo-Leiter laeuft, gibt es zwei Bezugspunkte. Tor 1 misst
gegen den besten Stand der EIGENEN Linie -- sonst reisst es in jeder
Generation, solange die Linie den Champion noch nicht eingeholt hat, und die
Schleife kaeme nie in Gang. Die Kante gegen den Champion wird trotzdem in
JEDER Generation gemessen und BERICHTET (Schritt 7); sie ist das Ziel der
Kampagne, aber nicht das Ratschen-Tor. Erst wenn sie faellt, wechselt der
Champion.

**(2) "Generator" ist NICHT "Kandidat".** Die Partien einer Generation
erzeugt der beste Stand der Vor-Generation (`generation_naming.md`: Fenster
vN traegt die Partien von v(N-1)), und das Profil des GENERATORS bestimmt,
was im Korpus ueberhaupt vorkommt. Tor 2 misst den Kandidaten deshalb am
gleichen Instrument wie den Generator -- gleiche Zugwahl, gleiche Sims --
sonst vergleicht man zwei Betriebspunkte. Der Betriebspunkt der ERZEUGUNG
wird davon unabhaengig in der Fenster-Prereg entschieden und kann bewusst ein
anderer sein.

## Was hier NICHT steht

* Der Fenster-Zuschnitt und die Schwellen einer konkreten Generation --
  `PREREG_vN_window.md`.
* Die Trainings-Arme einer Generation -- `generation_naming.md`.
* Der aktuelle Stand, die laufenden Zahlen und welche Generation gerade dran
  ist -- `evaluations/STATUS.md`.
* Ob die Schleife automatisiert wird. Heute ist sie eine Abfolge von
  Handgriffen mit Toren; ein Treiberskript waere Bequemlichkeit, und die
  Erfahrung dieser Kampagne spricht dafuer, die Tore erst von Hand zu fahren,
  bis sie sich zweimal bewaehrt haben.
