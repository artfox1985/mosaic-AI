<!-- STATUS: OFFEN | Frage: Zeigt die Diskrepanz zwischen Value-Kopf und Wurzel-Q (bzw. zwischen Prior und Suche) auf die Stellungen, an denen der Kopf gegen den Ausgang falsch liegt -- und lohnt es deshalb, den Schwarm dort statt zufaellig abzweigen zu lassen? | Beleg: angelegt 2026-09-26, nichts gebaut, nichts gefahren. Stufe 1 ist ein Offline-Vortest (par.3), Stufe 2 der Bau nur, wenn er besteht (par.4). -->

# Vorregistrierung: gezielt abzweigen statt zufaellig

**Angelegt 2026-09-26.** Anlass: Tor 1 von v33 trug nur auf der Kante (420:380 = 52,50 %,
Block-z +1,41, `PREREG_v33_window.md` par.10), der Sprung schrumpft gegen v32 (54,25 %, z +2,37).
Nutzer: *"Ich denk wir sind mit unserer aktuellen Architektur in der Saettigung ... Ist die frage
was der naechste Hebel ist. Mehr spiele oder diverseres material"*, auf die Vorlage: *"Gezielt
Abzweigen hoert sich vernuenftig an. Zufall kommt eh hinein durch die temperature"* und *"Und die
policy lernt aus den Daten bei der sie mit der Suche auseinanderliegt"*.

## par.1 WARUM

**Self-Play steuert in Stellungen, die das Netz gut bewertet.** Der Value-Kopf braucht aber
Material dort, wo er FALSCH liegt. "Vielfalt" gemessen als verschiedene Brettmasken ist gesaettigt:
der huellenfreie Schwarm brachte +1,1 Prozent (`PREREG_geometric_envelope.md` par.14e).

**Heute weichen beide Wege an ZUFAELLIGEN Stellen ab:** Weg C an einer aus der gemessenen
Verteilung (Runde, Index) gezogenen Stelle, Weg B (Ausflug) am ersten Halbzug nach dem Abzweig
(`engine/src/self_play.rs`, `deviate_stream`, am Code gelesen 2026-09-26). Die Abweichung selbst
waehlt das Netz ohne Suche aus den besten Kandidaten ausser dem Suchzug (`deviation_best_action`).

**Die Idee:** die Abzweigstelle dorthin legen, wo das Netz sich selbst widerspricht. Zwei Signale
stehen in jedem Record mit Suche:
* **Value-Diskrepanz** `|v_kopf - root_q|`: Kopf und Suche bewerten dieselbe Stellung verschieden.
* **Policy-Diskrepanz** `KL(Besuchsverteilung || Prior)`: die Suche widerspricht der Intuition.
  Genau dort lernt die Policy (ihr Ziel ist die Besuchsverteilung).

**Abgrenzung zum Bestand:**
* `PREREG_policy_surprise_weighting.md` (zweimal NEGATIV): gewichtete DIESELBEN Stichproben nach
  KL. Hier entstehen NEUE Stellungen in der Naehe solcher Stellen -- anderer Mechanismus.
* `PREREG_uncertainty_guided_selfplay.md` (UEBERHOLT, gefaltet in
  `PREREG_start_position_seeding.md` par.8): dieselbe Grundidee als Startstellungs-Warteschlange,
  nie gefahren, weil sie am b03-Befund des Seeding-Schwarms hing. Diese Prereg nimmt den Gedanken
  auf, aber am bestehenden Abzweig-Mechanismus (Weg B/C) statt an einer Warteschlange.
* Der Schwarm ist policy-maskiert: Abzweige dort liefern nur Value-Ziele. Primaer ist darum die
  VALUE-Diskrepanz; die Policy-Diskrepanz wird mitgemessen (par.3, Frage C).

## par.2 SUBSTRAT (Stufe 1)

* **Modell:** der GENERATOR des Materials, `v32-b01_brierbest` -- nur dann sind `root_q` und
  `v_kopf` Urteile desselben Netzes.
* **Zustaende:** `data/window_v33_val.txt` (147 Dateien, von `v32-b01` erzeugt, gezaehlt:
  51 policy, 41 excursion, 55 tempc-nohull). Weder `v32-b01` noch `v33-b01` hat sie trainiert.
  Auswahl wie `PREREG_evaluator_pretests.md` par.2: 60 Dateien, je Klasse 20, Seed 20260926.
* **Grundmenge:** Drafting-Records MIT `root_q` (Records ohne Suche tragen keins,
  `self_play.rs:6061-6092`), `completed is not False`. **Einheit** Zustand, **Block** Datei.
* **Zu pruefen beim Bau, UNGEPRUEFT:** aus wessen Sicht `root_q` steht (Zieher erwartet) und ob es
  roh oder huellen-korrigiert ist; `v_kopf` wird in derselben Form gerechnet, sonst misst die
  Diskrepanz die Huelle statt den Kopf.
* **Werkzeug:** Erweiterung von `tools/probes/evaluator_pretests.py` (dieselbe Extraktion);
  laufzeit-Block, Fortschrittszaehler.

## par.3 STUFE 1: Vortest, Leseregel VORAB

**A (traegt der Zeiger?):** Zustaende nach Value-Diskrepanz in Dezile teilen. Brier des Kopfs gegen
den Ausgang im OBERSTEN Dezil gegen die UNTERE Haelfte, Differenz mit Block-CI.
**B (ist die Suche dort besser?):** im obersten Dezil Brier(`root_q`) gegen Brier(`v_kopf`).
**C (zeigen beide Signale auf dieselben Stellen?):** Spearman zwischen Value- und
Policy-Diskrepanz; Anteil der Zustaende, die in beiden obersten Dezilen liegen. Dazu A fuer die
Policy-Diskrepanz.
**Berichtet:** Verteilung der Diskrepanz je Runde und je Klasse (wo lagen die Stellen?).

**Besteht, wenn:** A zeigt im obersten Dezil einen um **>= 0,01 Brier** schlechteren Kopf, CI > 0,
UND B zeigt dort `root_q` besser als den Kopf (CI > 0). Die 0,01 ist eine SETZUNG: der Abstand
Kopf gegen linearen Leser in `PREREG_evaluator_pretests.md` par.8a lag bei 0,008-0,016, also die
Groessenordnung, in der sich an diesem Substrat ueberhaupt etwas bewegt hat.
**Tot, wenn** A nicht besteht: dann liegt der Kopf dort nicht haeufiger falsch, und gezieltes
Abzweigen erzeugt nur andere, nicht lehrreichere Stellungen.

**Kosten:** Extraktion wie bei den Bewerter-Vortests (495 s fuer 86.190 Zustaende), keine Suche.

## par.4 STUFE 2 (nur wenn Stufe 1 besteht)

**Festgelegt 2026-09-26 (Nutzer): gezielt abzweigen wird der AUSFLUG (Weg B)**, *"wir wollen die
Ausflug klasse ja umbauen vom abzweigort"*. Weg C bleibt zufaellig und ist damit die
Vergleichsbasis (die Klasse `value-wegc` aus `PREREG_v33_window.md` par.6b ist genau diese Basis).
Im selben Umbau: die verdeckte Welt am Abzweig neu mischen (Review-Befund #14, STATUS Fahrplan 3c).

Bau: die Abzweigstelle von Weg B und/oder Weg C nach der Diskrepanz waehlen -- in der laufenden
Partie ist sie ohne Zusatzkosten bekannt (Wurzelwert der Suche und Netzwert an der Wurzel).
Zuschnitt (Wahrscheinlichkeit proportional zur Diskrepanz oder Schwelle; welcher Weg), Arm und
Leseregel werden VOR dem Bau hier nachgetragen, auf Grundlage der Verteilung aus par.3. Record-Feld
fuer die Abzweig-Diskrepanz VOR der Erzeugung (`feedback_record_field_must_precede_generation`).

## par.5 ZEITPLAN

Stufe 1 nach dem b02-A/B (Maschine frei), zusammen mit oder vor den Bewerter-Vortests Stufe 2.
Ergebnis entscheidet, ob die v34-Erzeugung schon gezielt abzweigt.

## par.6 ERGEBNISSE

(noch leer)
