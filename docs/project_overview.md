# Mosaic-AI: Was wir hier machen – eine Zusammenfassung in normalem Deutsch

Dieses Dokument erklärt das Projekt für Menschen ohne KI- oder
Statistik-Hintergrund. Es beantwortet drei Fragen: Was machen wir?
Wie machen wir es? Und warum ausgerechnet so?

Stand: 2026-10-09 (Projektabschluss). Eine bebilderte Erklärung, wie Netz und Suche einen Zug
finden und woher das Lernsignal kommt, steht (englisch) in
`docs/tessa_explained.html` (im Browser öffnen). Der tagesaktuelle Detailstand steht immer in
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
  spätere Änderung verschiebt). Der bisherige Champion (Generation 34)
  stand bei **1595** (nach dem neuen Fit 1575), der neue (Generation 35)
  steht bei **1660**. Weil jedes Netz seit Generation 21 gegen den
  Fixpunkt rund neun von zehn Partien gewinnt, trägt die Leiter
  dazwischen auf eingefrorenen Zwischenstufen (ältere Champions),
  gegen die die Duelle noch etwas aussagen.

Eine Besonderheit unseres Spiels: In der letzten Runde ist fast
alles bekannt und berechenbar. Lange spielte dort ein Endspiel-Rechner
statt des Netzes. Seit Generation 34 spielt das Netz auch die letzte
Runde, weil es den Rechner im direkten Vergleich schlug (480:320,
`evaluations/PREREG_r5_net_vs_solver.md`). Der Rechner bleibt im
Programm für den Fixpunkt der Leiter und für ein Trainingsziel.

## 3. Wo wir stehen (Abschluss, Generation 35)

- **Generation 35 ist die letzte, und sie stellt den neuen Champion.**
  Nutzer-Entscheid vom 2026-10-09: die Variante "b16" der Generation
  35 wird Champion und trägt damit im Spiel den Namen **"Tessa"**;
  die Promotion (die Pflichtmessungen beim Champion-Wechsel) läuft am
  selben Tag. Gegen den bisherigen Champion (Generation 34) gewann
  sie 289:161 Partien (64,2 %), in der Wiederholung mit neuen
  "Würfeln" 249:151 (62,3 %); gegen den Fixpunkt 46:4 und gegen den
  Champion der Generation 32 107:43. Ihre Elo-Zahl: 1660 (der
  Vorgänger stand bei 1595, nach dem neuen Fit 1575).
- **Die Wertungsplatten-Baustelle bleibt gelöst.** Ein regelbasierter
  Lehr-Datensatz hat den Spaltenbau in die Trainingsdaten gebracht;
  seither baut der Champion rund eine volle Spalte je Partie (vorher
  praktisch null) und gewinnt trotzdem die Duelle. Der neue Champion
  baut rund 1,1 volle Spalten je Partie gegen rund 1,0 beim alten
  und holt je Partie rund 5,7 Punkte mehr als sein Gegner.

Was die abschließende Reihe gelernt hat, in Alltagssprache:

1. **Gründlicheres Nachdenken beim Üben ergibt besseres
   Übungsmaterial.** Die Übungspartien der letzten Generation wurden
   mit 400 statt 100 Durchrechnungen je Zug neu gespielt. Schon das
   allein hob die Siegquote gegen den alten Champion von 50 auf rund
   57 Prozent.
2. **Der größte Hebel war, woraus das Netz seine Zugwahl lernt.** Das
   Netz lernt zwei Dinge: welche Züge gut aussehen (Zugwahl) und wie
   gut eine Stellung steht (Bewertung). Bisher diente nur ein Drittel
   der Übungspartien als Lehrer für die Zugwahl. Alle Partien als
   Lehrer zuzulassen brachte 60,9 Prozent gegen den alten Champion,
   4.000 frische Partien dazu 59,1 Prozent; beides zusammen ergab den
   neuen Champion mit 64,2 Prozent, die stärkste Kante der ganzen
   Reihe.
3. **Am Bewertungsziel war nichts mehr zu holen.** Alle Varianten
   davon, woraus das Netz lernt, wie gut eine Stellung steht, brachten
   gegen den jeweils besten Stand nichts Messbares; ebenso wenig das
   Mitteln mehrerer Trainingsstände zu einem Netz.
4. **Die Suche hat beim starken Netz kaum noch etwas zu korrigieren.**
   Von den Such-Ideen aus der Fachliteratur wurde "Tree Reuse" gebaut
   und gemessen: das Programm behält den Suchbaum vom vorigen Zug,
   statt jedes Mal neu anzufangen. Auf dem alten Netz brachte das
   einen knappen Gewinn (53,1 % über 1.200 Partien), auf dem neuen
   Champion war nichts mehr zu sehen (51,0 % in einer kurzen Probe);
   es bleibt darum draußen. Eine weitere Messung zeigte, dass das Netz
   den Ausgang einer Runde schon so gut vorhersieht, dass eine
   zusätzliche kleine Suche am Rundenende keinen Spielraum hätte.

**Damit endet das Projekt:** Generation 35 war die letzte, Tessa ist
der Schlussstand.

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
kollidiert, gelten die Fachdokumente. Die Zahlen hier stammen aus den
bis 2026-10-09 protokollierten Messungen: Elo 1595 für Generation 34
aus `evaluations/PREREG_v34_window.md` par.10e; die Duelle, Spalten und Punkte
der Generation 35 aus `evaluations/PREREG_v35_window.md` (par.12-21a,
Promotion par.22) und `evaluations/PREREG_tree_reuse.md` (par.3c,
par.3e); die Rundenend-Messung aus
`evaluations/PREREG_tiling_surprise_probe.md` (par.3b). Die Elo-Zahl 1660
des neuen Champions stammt aus dem Fit vom 2026-10-09 (par.22a). Die Zahlen veralten mit dem Projekt, die Aussagen zur Methode
nicht.
