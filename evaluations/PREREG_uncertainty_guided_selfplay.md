<!-- STATUS: OFFEN | Frage: Bringt es Staerke, Self-Play-Startstellungen dort zu waehlen, wo das Netz nachweislich unsicher ist UND diese Unsicherheit die Zugwahl kippen kann, statt kuratiert oder zufaellig? | Beleg: nichts gebaut, Entwurf angelegt 2026-08-23. Anschluss an PREREG_start_position_seeding par.4d (Tau +0,14 gegen -0,19, p=0,017); Tor G entscheidet vor jedem Eingriff, ob das Unsicherheitsmass ueberhaupt taugt (par.3). Stufe 1 braucht keine Engine-Aenderung: Entscheidungsnaehe aus root_q/root_child_q, in 65,2 % der Datensaetze (par.4). Abdeckungsmass und Waechter: par.6. -->

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

**Praezisierung 2026-08-23:** "billig" gilt fuer den Rechenaufwand, nicht
fuer die Verdrahtung. Sobald die Koepfe INNERHALB der Erzeugung gelesen
werden sollen, muessen sie durch den ONNX-Export und den Rust-Ausgabevertrag
-- und der ist bereits eng: `_unpack_optional_outputs` (`train.py:205 ff.`)
loest bis zu drei optionale Ausgaenge ueber das MODELL auf, ausdruecklich
nicht ueber die Tupel-Laenge, weil Laenge 6 sonst mehrdeutig waere; auf der
Rust-Seite haengen `net.rs::eval_ex` und `has_opp_head` daran. K zusaetzliche
Ausgaenge landen genau dort. Stufe 1 (par.4) vermeidet das vollstaendig,
Stufe 2 (par.5) nicht.

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
Verrechnung ist offen, siehe par.9 (im Entwurf stand hier faelschlich par.8,
das ist die Nicht-Erfolgs-Liste).

## par.3 Tor G: taugt das Mass ueberhaupt?

**Vor jedem Eingriff in die Erzeugung.** Die Bootstrap-Koepfe werden gebaut
und rein messend gefahren, ohne Einfluss auf Self-Play oder Suche.

**Vorbedingung, vor Tor G zu entscheiden** (nachgetragen 2026-08-23): an
welchem Ziel die K Koepfe haengen, Sieg oder Punkte. Der Entwurf fuehrte das
unter par.9 als offenen Punkt fuer "vor dem Bau". Das ist zu spaet: der
Gueltigkeitsnachweis unten misst Uneinigkeit gegen den "tatsaechlichen
Vorhersagefehler", und dieser Fehler ist ohne die Zielwahl nicht definiert.
Ohne die Festlegung ist Tor G nicht spezifiziert.

Zwei Nachweise:

- **Gueltigkeit.** Auf einem Holdout-Satz muss die Uneinigkeit mit dem
  tatsaechlichen Vorhersagefehler zusammenhaengen -- gemessen am oben
  festgelegten Ziel. Vorregistriert:
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

Kein asynchroner Umbau der Erzeugung, und -- Praezisierung 2026-08-23 --
**kein Eingriff in die Engine ueberhaupt**. Der Entwurf schrieb hier "waehrend
eines regulaeren Self-Play-Zyklus wird je Stellung die Akquisition
mitgeschrieben". Das haette die K Koepfe in den ONNX-Export und den
Rust-Ausgabevertrag gezwungen (par.2) und war der groesste Einzelposten der
Stufe. Er ist nicht noetig: die Stellungen liegen nach dem Zyklus ohnehin im
Korpus, und die Akquisition ist auf ihnen **nachtraeglich in Python**
berechenbar. Die Warteschlange laeuft damit ueber Zyklen hinweg:

1. Ein regulaerer Self-Play-Zyklus laeuft **unveraendert**. Keine Engine-
   Aenderung, kein neuer Ausgang, kein neues Feld.
2. Danach wird der Korpus in Python durchlaufen: je Stellung ein
   Vorwaertslauf durch die K Bootstrap-Koepfe (Uneinigkeit) und die
   Entscheidungsnaehe aus den bereits mitgeschriebenen Wurzelstatistiken.
   **Nachgesehen 2026-08-23** an `selfplay_v20wdl_*_g4000.pkl`: die
   Datensaetze tragen `root_q` (Wurzelwert) und `root_child_q` (Liste der
   Kind-Q-Werte auf der [0,1]-Skala, im Stichprobendatensatz 347 Eintraege),
   beide in **65,2 %** der Zeilen. Der Abstand der beiden besten Eintraege
   in `root_child_q` IST die Entscheidungsnaehe; sie muss nicht neu erzeugt
   werden.
3. Die Stellungen mit der hoechsten Akquisition werden ausgeschrieben.
4. Im naechsten Zyklus werden sie als zusaetzliche Startstellungen
   eingespeist, ueber die vorhandene Startstellungs-Mechanik.

Das ist traeger als echtes Verzweigen, kostet aber **keine neue Architektur
und keine Engine-Aenderung** und nutzt genau den Pfad, der in
`PREREG_start_position_seeding.md` bereits abgenommen ist. Stufe 1 ist damit
ein Auswertungsskript plus ein Trainingslauf fuer die K Koepfe.

Was das kostet, ist Genauigkeit: die Uneinigkeit wird an der gespielten
Stellung gemessen und nicht an der, die die Suche gerade betrachtet. Fuer
die Auswahl von Startstellungen ist das dieselbe Groesse; fuer Stufe 2
(Verzweigen mitten in der Suche) waere es das nicht.

Zweiter Preis, vorab zu benennen: **fuer 34,8 % der Stellungen fehlen die
Wurzelstatistiken**, dort ist die Entscheidungsnaehe offline nicht
bestimmbar (Verteilung ueber die Runden in der Stichprobe: R1 232/321,
R2 235/345, R3 232/348, R4 225/358, R5 147/271). Vorab festgelegt, damit
daraus keine stille Auswahl wird: diese Stellungen kommen **nicht** in die
Warteschlange, und ihr Anteil ist je Zyklus zu berichten. Wuerden sie
stattdessen allein nach Uneinigkeit bewertet, waere das genau der Fehler,
den par.2 ausschliesst -- Auswahl ohne Entscheidungsnaehe.

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
   **Festgelegt 2026-08-23** (der Entwurf nannte hier keine Groesse, und
   ohne Groesse ist es kein Waechter): das Mass ist die
   Shannon-Entropie der Eroeffnungs-Ereignisse aus
   `tools/selfplay_diversity_report.py` (`shannon_entropy`, `:90`, gespeist
   aus `opening_events`, `:59`), gerechnet je Arm auf denselben
   Zyklus-Umfang. Bestandswerkzeug, keine Neuentwicklung. Berichtet wird die
   Differenz zum Kontrollarm, nicht der Absolutwert -- der haengt an der
   Partiezahl.
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
- Schwelle beziehungsweise Quantil, ab dem eine Stellung in die
  Warteschlange kommt, und wie viele Stellungen je Zyklus eingespeist
  werden.

Herausgenommen 2026-08-23: "ob die Bootstrap-Koepfe am Sieg-Ziel oder am
Punkte-Ziel haengen" stand hier und ist nach par.3 vorgezogen -- Tor G ist
ohne diese Wahl nicht spezifizierbar. Ebenfalls entschieden statt offen: das
Abdeckungsmass (Waechter 4) und der Verzicht auf jede Engine-Aenderung in
Stufe 1 (par.4).

Am Rande, aber vor dem Bau zu wissen: die Wurzelstatistik im Korpus liegt
auf der [0,1]-Blattwertskala (`root_q`/`root_child_q`), das Punkte-Ziel des
Netzes dagegen auf der tanh-Skala und ist zusaetzlich TD-geblendet (siehe
`PREREG_points_dist_bin_scale.md` par.2a). Uneinigkeit und
Entscheidungsnaehe liegen also NICHT in derselben Einheit; die Verrechnung
oben muss das ausweisen und nicht stillschweigend addieren.

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
