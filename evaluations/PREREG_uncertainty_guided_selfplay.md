<!-- STATUS: OFFEN | Frage: Bringt es Staerke, Self-Play-Startstellungen dort zu waehlen, wo das Netz nachweislich unsicher ist UND diese Unsicherheit die Zugwahl kippen kann, statt kuratiert oder zufaellig? | Beleg: nichts gebaut, Entwurf angelegt 2026-08-23; Anschluss an PREREG_start_position_seeding par.4d (erstes positives Zustandssignal, Tau +0,14 vs -0,19, p=0,017), Tor G (Gueltigkeit des Unsicherheitsmasses) vor jedem Eingriff -->

# Vorregistrierung: Unsicherheitsgesteuertes Self-Play

**Angelegt 2026-08-23, VOR jedem Bau.**

## par.1 Anlass

Drei Befunde treffen zusammen.

1. **Die Startzustandsverteilung bewegt die Mechanik.**
   `PREREG_start_position_seeding.md` par.4d hat mit veraenderten
   Startstellungen das erste positive Zustandssignal der Kampagne erzeugt
   (Tau +0,14 gegen −0,19 im Kontrollarm, p=0,017), bei unveraendertem
   Verhalten und ohne Siegverlust. Die Stellungen waren dabei **kuratiert
   und statisch**.
2. **Der Engpass liegt auf der Policy-Seite.** Die Ownership-Straenge sind
   in allen Formen negativ geschlossen (`PREREG_ownership_coupling.md`,
   `PREREG_conjunction_terms.md`), und der Zielwechsel auf Vollendbarkeit
   war ebenfalls ein Nicht-Erfolg mit der ausdruecklichen Feststellung, dass
   das Ziel nicht der Engpass ist (`PREREG_reachability_target.md` par.16).
   Die Startzustandsverteilung ist der Hebel, der auf der Policy-Seite
   ansetzt.
3. **Es gibt Diversitaet, aber keine Richtung.** Vorhanden sind
   Gumbel-/Dirichlet-Rauschen an der Wurzel, Tau-Annealing,
   Playout-Cap-Randomisierung, kuratierte Startstellungen und ein
   asymmetrisches Curriculum. Nirgends wird gemessen, **wo das Netz etwas
   nicht weiss**. Der Unterschied zu dieser Prereg ist Richtung, nicht
   Menge.

## par.2 Mechanismus

### Zwei Unsicherheiten, strikt getrennt

**Aleatorisch** ist die Streuung, die aus dem Spiel selbst kommt (Fabriken,
Chips, Kuppelplatten, Gegnerzug). Sie ist in Runde 1 gross und schrumpft
mit jeder Runde. Sie ist **kein** Lernsignal: eine Stellung kann maximal
zufaellig und trotzdem vollstaendig verstanden sein.

**Epistemisch** ist, was das Netz nicht weiss. Nur diese Groesse steuert.

Die Verwechslung der beiden ist die teuerste Fehlermoeglichkeit dieses
Zuschnitts: ein Verfahren, das auf aleatorische Breite auswaehlt, sucht
gezielt die zufaelligsten Stellungen der Partie auf, also die mit dem
geringsten Lernwert, und sieht dabei wie gerichtete Exploration aus.

### Die epistemische Groesse

K schmale Bootstrap-Koepfe (K = 5 bis 8) auf dem vorhandenen Rumpf, jeder
mit eigenem Initialisierungs-Seed und eigener Bootstrap-Ziehung des Korpus.
Kosten: ein Forward-Pass wie bisher, die Koepfe sind gegen den Rumpf billig;
der Aufpreis liegt im Training.

Mass ist die Streuung der **Entscheidungsgroesse** ueber die K Koepfe, nicht
die Divergenz ihrer Verteilungsformen. Begruendung: zwei Koepfe koennen
verschieden aussehen und dieselbe Zugwahl treffen. Das ist folgenlose
Uneinigkeit, und sie in das Kriterium zu nehmen verschwendet Budget.

### Die Akquisition

Uneinigkeit allein reicht nicht. Leitprinzip:

> Unsicherheit ist kein Informationsgewinn. Relevant ist Unsicherheit dort,
> wo sie eine Entscheidung aendern kann.

Zwei Beispiele, die den Unterschied tragen:

- Bester Zug +40, zweitbester +5, Uneinigkeit 2. Unsicher und vollkommen
  folgenlos, die Rangfolge steht.
- Bester Zug +5, zweitbester +4, Uneinigkeit 8. Hier entscheidet die
  Unsicherheit, welcher Zug gespielt wird.

Die Akquisition kombiniert deshalb **Uneinigkeit** und
**Entscheidungsnaehe** (Abstand der besten Wurzelkandidaten). Die konkrete
Verrechnung ist offen, siehe par.8.

## par.3 Tor G: taugt das Mass ueberhaupt?

**Vor jedem Eingriff in die Erzeugung.** Die Bootstrap-Koepfe werden gebaut
und rein messend gefahren, ohne Einfluss auf Self-Play oder Suche.

Zwei Nachweise:

- **Gueltigkeit.** Auf einem Holdout-Satz muss die Uneinigkeit mit dem
  tatsaechlichen Vorhersagefehler zusammenhaengen. Vorregistriert:
  Rangkorrelation zwischen Uneinigkeit und absolutem Fehler, positiv und
  signifikant, mit Block-Bootstrap ueber Korpusdateien (nicht ueber
  Einzelstellungen, siehe Waechter 5).
- **Kein Kollaps.** Die K Koepfe muessen ueber die Trainingsdauer
  unterscheidbar bleiben. Berichtet wird die mittlere paarweise Uneinigkeit
  je Epoche. Sie darf nicht gegen null laufen.

**Faellt Tor G durch, endet der Zuschnitt hier.** Das ist ein zulaessiger
Ausgang. Ohne Tor G wuerde ein Indikator optimiert, dessen Bedeutung
unbewiesen ist, und ein spaeterer Nullbefund waere nicht interpretierbar.

## par.4 Stufe 1: Warteschlange offline

Kein asynchroner Umbau der Erzeugung. Die Warteschlange laeuft **ueber
Zyklen hinweg**:

1. Waehrend eines regulaeren Self-Play-Zyklus wird je Stellung die
   Akquisition mitgeschrieben.
2. Nach dem Zyklus werden die Stellungen mit der hoechsten Akquisition
   ausgeschrieben.
3. Im naechsten Zyklus werden sie als zusaetzliche Startstellungen
   eingespeist, ueber die vorhandene Startstellungs-Mechanik.

Das ist traeger als echtes Verzweigen, kostet aber keine neue Architektur
und nutzt genau den Pfad, der in `PREREG_start_position_seeding.md` bereits
abgenommen ist.

## par.5 Stufe 2: echtes Verzweigen (nur bei Beleg aus Stufe 1)

Gabelung mitten in der laufenden Partie: Stellung erkannt, zweite
Fortsetzung mit anderem Zug. Das bricht die heutige lineare
Erzeugungsschleife (unabhaengige Partien auf Kerne verteilt) und braucht
eine Warteschlange plus Arbeiter, die daraus neue Partien starten. Das ist
der groesste Engineering-Posten des Zuschnitts.

**Wird erst angefasst, wenn Stufe 1 einen Nutzen belegt.**

## par.6 Waechter

1. **Nur epistemisch auswaehlen.** Die aleatorische Breite darf nicht ins
   Kriterium. Siehe par.2.
2. **On-Policy-Anker.** Ein fester, vorab festgelegter Anteil der Partien
   laeuft unveraendert. Ohne ihn driftet die Trainingsverteilung von der
   weg, in der der Agent tatsaechlich spielt, und das Netz wird auf
   Stellungen gut, die nie vorkommen.
3. **Herkunftsvermerk je Stellung.** Ein Feld, das festhaelt, ob eine
   Stellung aus einer regulaeren Partie oder aus einer Akquisitions-Einspeisung
   stammt. Ohne ihn ist Waechter 2 nicht nachrechenbar und ein misslungener
   Zyklus nicht gezielt zurueckdrehbar. Gehoert auf dieselbe Ebene wie die
   bestehenden Masken und Datei-Manifeste.
4. **Abdeckungsmass.** Faellt die Uneinigkeit global, muss unabhaengig
   sichtbar sein, ob der besuchte Stellungsraum breiter oder enger geworden
   ist. Sonst ist Koennen nicht von Kopf-Angleichung zu unterscheiden.
5. **Block-Ebene bei jeder Auswertung.** Score- und Fehleranalysen werden
   auf Block-Ebene gerechnet, nicht auf Stellungs- oder Paar-Ebene; im
   Projekt sind Paar-SEs schon einmal massiv unterschaetzt worden.
6. **Fenster-Pinning.** Trainings waehrend laufender Generierung werden
   gepinnt, sonst verschiebt sich das Datenfenster unter der Messung.

## par.7 Entscheidungsmetrik, vorab festgelegt

**Primaer: gepaarte Arena** gegen den Champion, feste Paarzahl, **kein
SPRT-Fruehstopp.**

Begruendung aus der Akte: `t12_dist` zeigte zunaechst SPRT-H1 mit 54:26 und
war in der vorregistrierten Frisch-Seed-Replikation Seed-Rauschen (206:194
und 181:179, beide n.s.). Offline-Kennzahlen haben unterhalb ihrer
Aufloesung mehrfach in die falsche Richtung gezeigt.

**Sekundaer, ausdruecklich nur deskriptiv:**

- die beiden Orakel-Metriken, die bisher 7/7 mit der Arena liefen;
- das Zustandssignal aus `PREREG_start_position_seeding.md` par.4d, damit
  der Vergleich zum Vorlaeufer-Arm moeglich ist;
- das Abdeckungsmass aus Waechter 4.

**Kontrollarm:** derselbe Zyklus mit derselben Zahl zusaetzlicher
Startstellungen, aber **zufaellig** statt nach Akquisition gewaehlt. Ohne
diesen Arm misst der Vergleich nur "mehr Startstellungen", nicht
"gerichtete Startstellungen". Das ist der eigentliche Ein-Faktor-Test
dieses Zuschnitts.

**Seed-Disziplin:** Trainings-A/Bs innerhalb des Zuschnitts brauchen
gepaarte Seeds. Der Seed bewegt die Metrik im Projekt um ein Vielfaches
dessen, was ein einzelner Knopf bewegt; Einzellauf-Vergleiche sind hier
wertlos.

## par.8 Was als Nicht-Erfolg gilt

- **Tor G nicht bestanden.** Zuschnitt endet, ohne dass Self-Play angefasst
  wird.
- **Arena-Gating H0 bei voller Paarzahl.** Kein Beleg, Zuschnitt ruht.
  Ausdruecklich nicht "widerlegt".
- **Kein Unterschied zum Zufalls-Kontrollarm.** Dann wirkt die Menge, nicht
  die Richtung, und die Akquisition traegt nichts bei. Das ist der
  wahrscheinlichste Nullbefund und der wichtigste zu berichtende.
- **Arena-Verlust ausserhalb der Aufloesung.** Zuschnitt wird geschlossen.
- **Abdeckung sinkt statt zu steigen.** Unabhaengig vom Arena-Ausgang zu
  berichten: die Steuerung wirkt dann gegen ihr eigenes Ziel.

## par.9 Offen, vor dem Bau zu entscheiden

- K, die Zahl der Bootstrap-Koepfe, und wie stark ihre Ziehungen
  ueberlappen duerfen.
- Verrechnung von Uneinigkeit und Entscheidungsnaehe. Ein Produkt ist die
  einfachste Annahme und vermutlich nicht die beste.
- Anteil des On-Policy-Ankers.
- Ob die Bootstrap-Koepfe am Sieg-Ziel oder am Punkte-Ziel haengen.
- Schwelle beziehungsweise Quantil, ab dem eine Stellung in die
  Warteschlange kommt, und wie viele Stellungen je Zyklus eingespeist
  werden.

## par.10 Verhaeltnis zu den Nachbar-Zuschnitten

- `PREREG_start_position_seeding.md`: der Vorlaeufer. Gleiche Mechanik
  (Start ab Stellung), andere **Auswahl** der Stellungen. Diese Prereg ist
  der gerichtete Nachfolger seines kuratierten Satzes.
- `PREREG_reachability_target.md` und die Ownership-Straenge: dort ist die
  Ziel-Seite negativ geschlossen mit dem Verweis auf die Policy-Seite. Hier
  wird die Policy-Seite angefasst.
- Verteilungskoepfe fuer die Blattbewertung (Task #12, Nach-#34-Paket Arm 1)
  sind **nicht** Gegenstand. Die Bootstrap-Koepfe hier dienen der
  Datenauswahl, nicht der Blattbewertung.
