# Mosaic-AI: Was wir hier machen – eine Zusammenfassung in normalem Deutsch

Dieses Dokument erklärt das Projekt für Menschen ohne KI- oder
Statistik-Hintergrund. Es beantwortet drei Fragen: Was machen wir?
Wie machen wir es? Und warum ausgerechnet so?

Stand: 2026-08-21. Der tagesaktuelle Detailstand steht immer in
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
   korrigiert das Bauchgefühl, wo es daneben liegt.

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
  regelbasierter Vergleichsspieler, den wir auf Elo 1000 setzen. Der
  aktuelle Champion (Generation 21) steht auf dieser Leiter bei
  etwa **1215** – grob gesagt: er gewinnt gegen den Fixpunkt rund
  drei von vier Partien.

Eine Besonderheit unseres Spiels: In der letzten Runde ist fast
alles bekannt und berechenbar. Dort rechnet das Programm nicht mehr
mit Bauchgefühl, sondern mit einem exakten Endspiel-Rechner
(inklusive der Wahrscheinlichkeiten für die wenigen noch verdeckten
Plättchen). Auch dessen Wissen fließt zurück ins Training.

## 3. Woran arbeiten wir gerade? (Die Wertungsplatten-Baustelle)

Der Champion spielt das Grundspiel inzwischen stark – aber er lässt
messbar Punkte liegen, die über die Wertungsplatten zu holen wären.
Ein menschlicher Spieler, der gezielt "auf die Platten spielt", holt
dort zweistellige Punktbeträge, die dem Programm entgehen.

Warum ist ausgerechnet das schwer? Weil eine Wertungsplatte eine
**langfristige Absicht** verlangt: Wer eine 7-Punkte-Spalte bauen
will, muss sich über mehrere Runden hinweg auf bestimmte Farben und
Felder festlegen. In den Selbstspiel-Daten kommt so ein konsequenter
Spaltenbau aber fast nie vor – und was in den Trainingsdaten nicht
vorkommt, kann das Netz nicht lernen. Ein Henne-Ei-Problem: Das Netz
baut keine Spalten, also sieht es nie, dass Spalten Siege bringen,
also baut es keine Spalten.

Wir haben dafür in den letzten Wochen systematisch Lösungswege
durchprobiert und die meisten **sauber gemessen und verworfen** (das
ist kein Scheitern, sondern der Sinn der Messung – siehe Abschnitt 4).
Der aktuell laufende Versuch ist ein **asymmetrisches Curriculum**,
und die Idee ist anschaulich:

- Wir erzeugen einen Lehr-Datensatz von 16.000 Partien, in dem **je
  Partie genau eine Seite** einen regelbasierten "Bauhelfer"
  bekommt, der sie zum Spaltenbau drängt. Die andere Seite spielt
  normal.
- Dadurch entsteht zum ersten Mal ein Datensatz, in dem "Brett mit
  Spaltenfortschritt" und "Partie gewonnen/verloren" nicht mehr
  symmetrisch verrauscht sind – das Netz bekommt erstmals die Chance,
  den **Wert** des Plattenbaus zu sehen, nicht nur seine Existenz.
- Die Abnahme des Datensatzes hat die Voraussetzung bestätigt: Die
  gedrängte Seite schließt in 34,6 % der Partien mindestens eine
  Spalte ab, die freie Seite nur in 3,3 % – ein deutlicher
  Unterschied, aus dem sich lernen lässt.
- Jetzt trainieren zwei ansonsten identische Netze: eines mit dem
  Lehr-Datensatz, eines mit einem gleich großen normalen Datensatz
  (die "Kontrollgruppe", wie in einer Studie). Danach wird gemessen,
  ob das Lehr-Netz von sich aus mehr Spalten baut – und ob es dabei
  nicht schwächer wird. Beides ist vorher schriftlich als Messlatte
  festgelegt.

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
  dann im Browser `http://localhost:5000`): Mensch gegen Programm in
  mehreren Schwierigkeitsstufen, inklusive eines Debug-Fensters, das
  zeigt, was das Programm bei seinem Zug "dachte".
- **Ordnung im Projektordner:** Der Wurzelordner führt aus,
  `engine/` rechnet, `tools/` misst, `evaluations/` protokolliert,
  `docs/` erklärt (dieses Dokument, das Regelheft, die
  Prozessdiagramme), `static/` ist die Spieloberfläche.

Wer tiefer einsteigen will, in dieser Reihenfolge: die fünf
Prozessdiagramme in `docs/` (gerendert aus `docs/diagrams.txt`),
dann die `README.md`, dann `evaluations/STATUS.md`.

## 6. Ehrlichkeitsklausel

Dieses Dokument ist eine Vereinfachung. Wo es mit den Fachdokumenten
kollidiert, gelten die Fachdokumente. Die Zahlen hier (Elo 1215,
16.000 Lehr-Partien, 34,6 % gegen 3,3 %) stammen aus den am
2026-08-21 protokollierten Messungen; sie veralten mit dem Projekt,
die Aussagen zur Methode nicht.
