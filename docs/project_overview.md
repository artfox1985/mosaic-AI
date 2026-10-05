# Mosaic-AI: Was wir hier machen – eine Zusammenfassung in normalem Deutsch

Dieses Dokument erklärt das Projekt für Menschen ohne KI- oder
Statistik-Hintergrund. Es beantwortet drei Fragen: Was machen wir?
Wie machen wir es? Und warum ausgerechnet so?

Stand: 2026-10-05. Der tagesaktuelle Detailstand steht immer in
`evaluations/STATUS.md` (Fachdokument, deutsch); die technische
Kurzfassung in der `README.md` (englisch).

---

## 1. Was machen wir?

Wir haben ein Brettspiel digital nachgebaut (eine private, nicht
kommerzielle Nachbildung des Regelwerks von *Azul Duel*, einem
Legespiel für zwei Personen) und bringen einem Computerprogramm bei,
es richtig gut zu spielen – ohne ihm auch nur eine einzige Strategie
vorzusagen.

Das Spiel in einem Satz: Zwei Spieler nehmen abwechselnd bunte
Fliesen von gemeinsamen Auslagen, bauen damit an einer kleinen
6x6-Kuppel und bekommen am Ende Punkte – unter anderem über drei
zufällig ausliegende **Wertungsplatten**, die je Partie andere
Baumuster belohnen (z. B. "7 Punkte je vollständiger Spalte" oder
"minus 3 je leerem Spezialfeld"). Es gibt fünf Runden, dann wird
abgerechnet.

Das Ziel des Projekts ist bewusst einfach formuliert: **ein stärkerer
Spieler, gemessen im direkten Duell.** Nicht "schönere Statistiken",
nicht "besseres Bauchgefühl" – gewinnt die neue Programmversion gegen
die alte, ist sie besser. Gewinnt sie nicht, ist sie es nicht, egal
wie gut ihre Zwischenwerte aussehen.

## 2. Wie lernt das Programm? (Das AlphaZero-Prinzip, ohne Formeln)

Unser Ansatz folgt der AlphaZero-Idee, die durch Schach- und
Go-Programme bekannt wurde. Sie besteht aus zwei Teilen, die sich
gegenseitig hochschaukeln:

1. **Ein neuronales Netz als "Bauchgefühl".** Das Netz schaut auf
   eine Spielstellung und liefert zwei Einschätzungen: Welche Züge
   sehen vielversprechend aus? Und wie gut steht die Partie gerade
   (Gewinnwahrscheinlichkeit)? Am Anfang ist dieses Bauchgefühl
   zufällig und wertlos.
2. **Eine Suche als "Nachdenken".** Vor jedem Zug spielt das
   Programm im Kopf einige hundert Varianten durch. Das Bauchgefühl
   sagt ihr, welche Varianten sich überhaupt lohnen; das Nachdenken
   korrigiert das Bauchgefühl, wo es daneben liegt. Und genau diese
   Korrektur ist das Lernsignal: Das Netz wird darauf trainiert, beim
   nächsten Mal von vornherein das zu bevorzugen, was die Suche nach
   dem Nachdenken gewählt hat. Wo Suche und Bauchgefühl auseinander
   liegen, lernt das Netz am meisten.

Der Lernkreislauf, den wir "Generationszyklus" nennen:

- Der amtierende **Champion** (die beste bisherige Version) spielt
  tausende Partien **gegen sich selbst**. Jede Partie wird
  aufgezeichnet: alle Stellungen, was die Suche jeweils dachte, wer
  am Ende gewann.
- Aus diesen Aufzeichnungen wird ein **neues Netz trainiert**. Es
  lernt, die Ergebnisse des Nachdenkens direkt als Bauchgefühl zu
  haben – das nächste Nachdenken startet dadurch auf höherem Niveau.
- Der Kandidat muss den Champion dann **im Duell schlagen**
  (wir nennen das "Gating"): mehrere hundert Partien unter fairen,
  exakt gleichen Bedingungen. Nur wer statistisch klar gewinnt, wird
  neuer Champion. Ein Unentschieden reicht nicht.
- Die Stärke aller Versionen halten wir auf einer **Elo-Leiter**
  fest (dasselbe Zahlensystem wie im Schach). Als Fixpunkt dient ein
  regelbasierter Vergleichsspieler, den wir auf Elo 1000 setzen und
  eingefroren haben (mit eigenem Programmstand, damit ihn keine
  spätere Änderung verschiebt). Der aktuelle Champion (Generation 34)
  steht bei **1595**. Weil jedes Netz seit Generation 21 gegen den
  Fixpunkt rund neun von zehn Partien gewinnt, trägt die Leiter
  dazwischen auf eingefrorenen Zwischenstufen (ältere Champions),
  gegen die die Duelle noch etwas aussagen.

Eine Besonderheit unseres Spiels: In der letzten Runde ist fast
alles bekannt und berechenbar. Lange spielte dort ein Endspiel-Rechner
statt des Netzes. Seit Generation 34 spielt das Netz auch die letzte
Runde, weil es den Rechner im direkten Vergleich schlug (480:320,
`evaluations/PREREG_r5_net_vs_solver.md`). Der Rechner bleibt im
Programm für den Fixpunkt der Leiter und für ein Trainingsziel.

## 3. Wo wir stehen (Stand Generation 35)

- **Champion ist Generation 34, im Spiel "Tessa"** (seit 2026-10-03),
  Elo 1595. Sie schlug den Vorgänger 285:115 und den Fixpunkt 45:5.
- **Die Wertungsplatten-Baustelle ist gelöst.** Ein regelbasierter
  Lehr-Datensatz hat den Spaltenbau in die Trainingsdaten gebracht;
  seither baut der Champion rund eine volle Spalte je Partie (vorher
  praktisch null) und gewinnt trotzdem die Duelle.
- **Generation 35 ist die letzte.** Der Kreislauf stagniert: Der
  bewertende Teil des Netzes lernt aus Partien, die mit 100
  Durchrechnungen je Zug erzeugt wurden, nichts Messbares mehr. Die
  abschließende Reihe erzeugt das Material mit 400 Durchrechnungen
  neu, probiert dann vier Varianten des Bewertungsziels und zuletzt
  drei Änderungen an der Suche aus der Literatur. Trägt davon etwas,
  wird es Champion; sonst endet das Projekt mit Generation 34 als
  Tessa.

## 4. Warum so umständlich? (Unsere Arbeitsregeln, und woher sie kommen)

Vieles an diesem Projekt sieht nach Bürokratie aus: schriftliche
Versuchspläne, Messlatten vor der Messung, penible Protokolle. Das
hat einen einfachen Grund: **Wir haben uns selbst beim Schummeln
erwischt** – nicht aus Absicht, sondern weil Menschen (und
KI-Assistenten) Ergebnisse gern so deuten, wie es gerade passt.
Daraus sind Regeln geworden:

- **Vorregistrierung:** Vor jedem Experiment wird schriftlich
  festgelegt, was gemessen wird und ab welchem Wert es als Erfolg
  gilt (Dateien namens `PREREG_*` im Ordner `evaluations/`).
  Hinterher darf das Ergebnis nicht umgedeutet werden. Ein
  vorregistriertes "hat nicht funktioniert" ist ein vollwertiges,
  dokumentiertes Ergebnis und verhindert, dass dieselbe Idee ein
  halbes Jahr später nochmal Zeit kostet.
- **Faire Duelle:** Vergleichspartien laufen immer paarweise mit
  identischen Startbedingungen (gleiche "Würfel" für beide Seiten,
  Seitentausch), und der Rechner darf währenddessen nichts anderes
  tun – wir haben gemessen, dass schon parallele Rechenlast
  Partien verfälscht.
- **"Geprüft oder markiert":** Jede Zahl und jede Behauptung in
  unseren Dokumenten ist entweder frisch am Original nachgeprüft
  oder ausdrücklich als ungeprüft gekennzeichnet. Die Regel entstand,
  nachdem an einem einzigen Tag sieben kleine Flüchtigkeitsfehler
  auflaufen konnten, die jeweils ein simpler Blick in die Quelle
  verhindert hätte.
- **Ein einziges Übergabedokument:** Der aktuelle Stand lebt genau
  an einer Stelle (`evaluations/STATUS.md`). Kopien und veraltete
  Statusnotizen haben uns mehrfach Arbeitszeit gekostet, weil sie
  plausibel klangen, aber überholt waren.

Der rote Faden: Bei einem Lernsystem, das sich über Wochen selbst
verbessert, ist die größte Gefahr nicht ein Programmierfehler –
den findet man. Die größte Gefahr ist eine **plausible, aber falsche
Schlussfolgerung**, die unbemerkt zur Grundlage der nächsten zehn
Entscheidungen wird.

## 5. Womit ist das gebaut?

- **Spielregeln und Suche: Rust** (eine sehr schnelle
  Programmiersprache) – damit zehntausende Selbstspiel-Partien und
  Duelle in Stunden statt Wochen laufen.
- **Netz und Training: Python/PyTorch** – der Standardwerkzeugkasten
  für neuronale Netze.
- **Eine Web-Oberfläche zum Selberspielen** (`python server.py`,
  dann im Browser `http://localhost:5000`): Mensch gegen Programm,
  inklusive eines Debug-Fensters, das zeigt, was das Programm bei
  seinem Zug "dachte". Die Schwierigkeitsstufen werden zum Abschluss
  neu vermessen (vom eingefrorenen Regelspieler bis zum Champion).
- **Ordnung im Projektordner:** Der Wurzelordner führt aus,
  `engine/` rechnet, `tools/` misst, `evaluations/` protokolliert,
  `docs/` erklärt (dieses Dokument, das Regelheft, die
  Prozessdiagramme), `static/` ist die Spieloberfläche.

Wer tiefer einsteigen will, in dieser Reihenfolge: die fünf
Prozessdiagramme in `docs/` (gerendert aus `docs/diagrams.txt`),
dann die `README.md`, dann `evaluations/STATUS.md`.

## 6. Ehrlichkeitsklausel

Dieses Dokument ist eine Vereinfachung. Wo es mit den Fachdokumenten
kollidiert, gelten die Fachdokumente. Die Zahlen hier (Elo 1595 für
Generation 34, rund eine volle Spalte je Partie, neun von zehn
Partien gegen den Fixpunkt) stammen aus den am 2026-10-03/04
protokollierten Messungen (`evaluations/PREREG_v34_window.md` par.10e,
`PREREG_v35_window.md` par.11c); sie veralten mit dem Projekt, die
Aussagen zur Methode nicht.
