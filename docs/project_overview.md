# Mosaic-AI: Was wir hier machen – eine Zusammenfassung in normalem Deutsch

Dieses Dokument erklärt das Projekt für Menschen ohne KI- oder
Statistik-Hintergrund. Es beantwortet drei Fragen: Was machen wir?
Wie machen wir es? Und warum ausgerechnet so?

Stand: 2026-09-12. Der tagesaktuelle Detailstand steht immer in
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
  spätere Änderung verschiebt). Der aktuelle Champion (Generation 28)
  steht bei **1344**. Weil jedes Netz seit Generation 21 gegen den
  Fixpunkt rund neun von zehn Partien gewinnt, trägt die Leiter
  dazwischen auf eingefrorenen Zwischenstufen (ältere Champions),
  gegen die die Duelle noch etwas aussagen.

Eine Besonderheit unseres Spiels: In der letzten Runde ist fast
alles bekannt und berechenbar. Dort rechnet das Programm nicht mehr
mit Bauchgefühl, sondern mit einem exakten Endspiel-Rechner
(inklusive der Wahrscheinlichkeiten für die wenigen noch verdeckten
Plättchen). Auch dessen Wissen fließt zurück ins Training.

## 3. Woran arbeiten wir gerade? (Die Wertungsplatten-Baustelle, Stand nach Generation 28)

Der Champion spielt das Grundspiel stark – aber lange ließ er
messbar Punkte liegen, die über die Wertungsplatten zu holen wären.
Ein menschlicher Spieler, der gezielt "auf die Platten spielt", holt
dort zweistellige Punktbeträge.

Warum ist ausgerechnet das schwer? Weil eine Wertungsplatte eine
**langfristige Absicht** verlangt: Wer eine 7-Punkte-Spalte bauen
will, muss sich über mehrere Runden hinweg auf bestimmte Farben und
Felder festlegen. In den Selbstspiel-Daten kam so ein konsequenter
Spaltenbau anfangs fast nie vor – und was in den Trainingsdaten nicht
vorkommt, kann das Netz nicht lernen.

Was seit August dazu belegt ist:

- Ein regelbasierter "Bauhelfer", der eine Seite zum Spaltenbau
  drängt, hat als Lehr-Datensatz den Knoten gelöst: Der Champion baut
  seither in jeder Generation mehr volle Spalten (heute rund eine je
  Partie, vorher praktisch null) und gewinnt trotzdem die Duelle
  gegen seinen Vorgänger. Das war das eigentliche Ziel dieser
  Baustelle.
- Ein "geometrisches Geländer" in der Suche (die Einhüllende: eine
  Dreiecksform, in der Spalten überhaupt fertig werden können) bleibt
  Teil des Rezepts, weil vier Champions in Folge damit ihre Duelle
  bestanden haben. Der Versuch, seinen Nutzen auch am Bauchgefühl des
  Netzes nachzuweisen, ist an einem ungeeigneten Maßstab gescheitert
  und wurde bewusst geschlossen.
- Drei Generationen lang wurde **nur das Material** getauscht (die
  Aufzeichnungen, aus denen trainiert wird), sonst nichts – und jede
  davon war stärker als die vorige. Das sagt, dass der Kreislauf
  selbst trägt.
- Zwei Fehler, die keine Messung zeigen konnte, weil sie beide
  Seiten eines Duells gleich betrafen, wurden durch Spielen und Lesen
  gefunden: die Suche vergaß eine Reihenfolge, die sie selbst gewählt
  hatte, und die Startsetzung der Kuppel landete im Netz auf einer
  falschen Kennung. Beide sind behoben, und aus beiden sind Wächter
  im Code geworden.

Was jetzt läuft: Generation 29 und 30. In 29 wird gemessen, ob die
Suche am Rundenende schon das Legen der Fliesen sehen soll, ob die
Startsetzung der Kuppel ein Suchentscheid wird, und woran genau die
Züge eines stärkeren Gegners (Partien gegen ein großes Sprachmodell)
vom Netz abweichen. Was davon trägt, kommt in Generation 30. Mit
ihr endet das Projekt: Das Schlussmodell heißt Tessa, und die
Web-Oberfläche bekommt eine gemessene Leiter von Schwierigkeitsstufen.

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
kollidiert, gelten die Fachdokumente. Die Zahlen hier (Elo 1344 für
Generation 28, rund eine volle Spalte je Partie, neun von zehn
Partien gegen den Fixpunkt) stammen aus den am 2026-09-12
protokollierten Messungen; sie veralten mit dem Projekt, die
Aussagen zur Methode nicht.
