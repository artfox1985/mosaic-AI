<!-- STATUS: OFFEN | Frage: Zeigt die Diskrepanz zwischen Value-Kopf und Wurzel-Q (bzw. zwischen Prior und Suche) auf die Stellungen, an denen der Kopf gegen den Ausgang falsch liegt -- und lohnt es deshalb, den Schwarm dort statt zufaellig abzweigen zu lassen? | Beleg: Stufe 1 (par.6a): roh TOT (misst die Huelle), Policy-KL A +0,029. Stufe 2 NEU registriert (par.7, Nutzer): der Ausflug zweigt nach Rundenprofil x Policy-Diskrepanz ab (Aktionszahl faellt weg), Knopf MOSAIC_EXCURSION_KL_WEIGHT, faehrt in v34 im Paket. Wirkung auf den Kopf: Offline-Pruefung nach dem v34-Training registriert (par.7a, Doppel-Differenz gegen den v33-Schritt). -->

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

**PRAEZISIERUNG 2026-09-27, VOR dem Lauf (am Code gelesen):**
* `root_q` ist `nodes[0].value / nodes[0].visits` der Wurzel (`net_mcts.rs`, `net_root_child_stats_and_policy`),
  also ein SUCHwert -- er enthaelt die suchseitigen Additive (Huelle, `envelope_search_c` 1 im
  Generator-Spec). Der Kopfwert `v_kopf` ist roh. Die rohe Diskrepanz misst darum auch die Huelle.
  **Primaer bleibt die rohe Diskrepanz** (registriert); **zusaetzlich berichtet** wird eine
  bereinigte Diskrepanz: Residuum von `root_q` nach linearer Anpassung auf `v_kopf` je Runde
  (Anpassung auf den Trainingsfaltungen, Auswertung auf der ausgehaltenen, 5-fach ueber Dateien
  wie `PREREG_evaluator_pretests.md` par.4). Bestehen A und B nur auf einer der beiden Fassungen,
  wird das ausdruecklich so berichtet; entschieden wird auf der rohen.
* **Sichtpruefung vor jeder Zahl:** aus wessen Sicht `root_q` steht, prueft das Werkzeug am Ausgang
  (Brier von `root_q` gegen den Sieg des Ziehers gegen Brier von `1 - root_q`); die bessere Lesart
  gilt, beide werden berichtet.
* **Runde 5 ausgenommen:** dort kommt `root_q` aus dem R5-Loeser (`round5::choose_action_with_analysis`),
  nicht aus der Netzsuche, und das Abzweig-Profil gibt Runde 5 ohnehin Gewicht 0. Grundmenge also
  Runde 1-4.
* **Policy-Diskrepanz:** `KL(Ziel || Prior)` ueber die Aktions-IDs der Policy-Eintraege des Records
  (Ziel = completed-Q-Politik des Records, nach ID zusammengefasst; Prior = Softmax der Netz-Logits
  auf denselben IDs).

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

### par.6a Stufe 1, gefahren 2026-09-27 (122,5 s, exklusiv)

`tools/probes/targeted_branching_pretest.py`, Artefakt
`evaluations/artifacts/targeted_branching_stage1_v32-b01.json`. **67.302 Drafting-Zustaende Runde 1-4**
aus 60 Val-Dateien von v33 (je 20 policy / value-excursion / value-tempc-nohull), Generator und
Modell `v32-b01`; Block = Datei. Sichtpruefung: `root_q` steht aus Sicht des Ziehers (Brier 0,2010
wie gespeichert gegen 0,4123 gespiegelt). Gesamt-Brier Kopf 0,2064, `root_q` 0,2010.

| Diskrepanz | A: Brier Kopf oberstes Dezil - untere Haelfte | B: Brier(root_q) - Brier(Kopf) im Dezil |
| --- | --- | --- |
| **roh** `|root_q - v_kopf|` (primaer) | **+0,0001** [-0,0134; +0,0154] -- nicht | -0,0276 [-0,0441; -0,0098] -- besteht |
| bereinigt (Residuum je Runde, 5-fach) | **+0,0168** [+0,0066; +0,0276] -- besteht | -0,0286 [-0,0430; -0,0132] -- besteht |
| Policy `KL(Ziel || Prior)` | **+0,0292** [+0,0221; +0,0364] -- besteht | -0,0097 [-0,0131; -0,0063] -- besteht |

C: Spearman Value- gegen Policy-Diskrepanz **+0,095**; in beiden obersten Dezilen zugleich 1,2 Prozent
(1,0 bei Unabhaengigkeit) -- zwei weitgehend unabhaengige Zeiger. Anteil im obersten Dezil (roh) je
Runde 8,4 / 11,9 / 9,2 / 10,3 Prozent; je Klasse **policy 12,9 / excursion 14,3 / tempc-nohull 3,6**.

**VERDIKT nach der registrierten Regel (roh entscheidet): TOT.**

**Lesart, ausdruecklich als Nebenbefund:** die rohe Diskrepanz misst ueberwiegend die HUELLE (`root_q`
ist ein Suchwert mit Huellenterm, der Kopf roh): in der huellenfreien Klasse `tempc-nohull` liegen nur
3,6 Prozent der Zustaende im obersten Dezil, in den beiden Klassen mit Knopf 13-14 Prozent. Nach
Herausrechnen (bereinigt) zeigt die Value-Diskrepanz auf Kopf-Fehler (A +0,0168), und die
**Policy-Diskrepanz zeigt am staerksten darauf** (A +0,0292): wo Prior und Suche auseinanderliegen,
liegt auch der VALUE-Kopf deutlich schlechter. Beide Zeiger bestehen A und B. Ob Stufe 2 auf einem
dieser Zeiger gebaut wird, ist eine NEUE Entscheidung (Nutzer), keine Umdeutung dieses Verdikts:
dafuer braeuchte es eine neue Registrierung mit dem gewaehlten Zeiger, VOR dem Bau.

## par.7 STUFE 2, NEU REGISTRIERT 2026-09-27: der Ausflug zweigt nach der POLICY-Diskrepanz ab

**Nutzer 2026-09-27:** *"Mach die policy Diskrepanz."* -- nach par.6a (rohe Value-Diskrepanz nach
Regel TOT, weil sie die Huelle misst; Policy-Diskrepanz A +0,0292 [+0,0221; +0,0364], B besteht).
Das ist eine NEUE Registrierung auf einem anderen Zeiger, keine Umdeutung des Verdikts in par.6a.

**Bau (vor der v34-Erzeugung, eine Wheel-Runde):**
* Heute zieht der Ausflug seine Abzweigstelle per gewichtetem Reservoir-Sampling mit Gewicht
  Rundenprofil x Aktionszahl (`PREREG_start_position_seeding.md` par.9g). **Neu: Gewicht = Rundenprofil x
  Policy-Diskrepanz** `KL(completed-Q-Ziel || Prior)` an der Wurzel (beides liegt in der Suche ohnehin
  vor, keine Zusatzkosten). **Die Aktionszahl FAELLT WEG** (Nutzer 2026-09-27 auf die Frage, ob das
  Profil wegfaellt: *"Ja aendere das"*): sie war eine Setzung als Stellvertreter fuer "hier gibt es
  etwas zu lernen", das misst KL jetzt direkt; beides zu multiplizieren bevorzugte Stellen mit vielen
  Zuegen doppelt. Ob KL mit der Aktionszahl korreliert, ist UNGEMESSEN. Das Rundenprofil bleibt
  (gemessene Verlaesslichkeit des Value-Kopfs je Runde, Runde 5 Gewicht 0).
* Knopf `MOSAIC_EXCURSION_KL_WEIGHT` (Default 0 = heutiges Gewicht Profil x Aktionszahl,
  byte-identisch; 1 = Profil x KL),
  im Rezept der Erzeugung (`docs/working_rules.md`, Rezeptdatei). Weg C bleibt ZUFAELLIG (Vergleichsbasis).
* Record-Feld `branch_kl` am Abzweig-Record des Ausflugs, VOR der Erzeugung (Record-Feld-Regel).

**Bau-Stand 2026-09-27 (Quelltext, noch NICHT kompiliert):** `excursion_branch_weight`
(`engine/src/self_play.rs:3380`) rechnet bei Knopf 0 woertlich den Bestandsausdruck
`profile_weight * n_actions`, die KL wird dann gar nicht berechnet (Guard `self_play.rs:6460`);
bei Knopf 1 Gewicht `profile_weight * kl`, ohne echte Suche (eine Aktion, Rueckfall, R5-Loeser)
Gewicht 0. KL = `KL(completed-Q-Ziel || Wurzel-Prior)` nach Aktions-ID, Epsilon 1e-12 wie das
Vortest-Werkzeug. Manifest-Schluessel `engine_config.excursion_kl_weight`. Wheel-Runde, Tests,
Paritaets-Fixture und Anker-Invarianz stehen aus.

**PRAEZISIERUNG der Abnahme, VOR der Erzeugung (Definitionsabstand):** die Engine liest den Prior
aus dem Suchbaum, dessen Wurzel determinisiert ist (`DETERMINIZE_ROOT_HIDDEN_INFO`,
`net_mcts.rs:2161`), in f32; das Vortest-Werkzeug rechnet die Logits auf dem gespeicherten Zustand
in f64. `branch_kl` und eine offline gerechnete KL sind darum nicht bitgleich definiert. Die
Quantil-Abnahme unten vergleicht deshalb BEIDE Seiten in der OFFLINE-Definition (Werkzeug-KL am
ersten Record jedes Ausflugs gegen die Werkzeug-KL aller Drafting-Records der Erzeugung);
`branch_kl` wird daneben als Engine-Wert berichtet, samt Rangkorrelation zur Werkzeug-KL
derselben Records. Einschraenkung: das Policy-Ziel des ersten Ausflug-Records stammt aus der
eigenen Suche des Ausflugs (anderer Seed), nicht aus der Suche der Hauptpartie, die gewichtet hat.

**Abnahme (Diagnose, kein eigenes Tor):**
* Verteilung von `branch_kl` im v34-Ausflug gegen die KL-Verteilung aller Drafting-Stellen derselben
  Erzeugung: der Median am Abzweig muss ueber dem 75-Prozent-Quantil aller Stellen liegen, sonst hat
  der Knopf nicht gegriffen (dann Bau pruefen, nicht deuten).
* Brier des Kopfs an den Abzweigstellen des v34-Ausflugs gegen Zufallsstellen aus Weg C: berichtet.
* **Staerke:** kein isolierter Arm. Der Knopf faehrt in der v34-Erzeugung zusammen mit anderen
  Paket-Aenderungen; ein Tor-1-Gewinn von v34 ist dem Paket, nicht diesem Knopf zuzuschreiben. Das
  ist bewusst so (Nutzer: v34 noch fahren, danach alternative Ansaetze pruefen).

### par.7a OFFLINE-PRUEFUNG NACH DEM v34-TRAINING: lernt der Kopf gezielt dort, wo abgezweigt wurde?

**Nutzer 2026-09-27:** *"Registriere die offline Pruefung"* (auf die Frage, ob das Abzweigen nach der
Policy-Diskrepanz ueberhaupt auf den Value-Kopf wirkt). Registriert VOR der v34-Erzeugung.

**Warum ueberhaupt:** der Knopf hat kein eigenes Tor (par.7), und die Abnahme in par.7 prueft nur,
ob er GREIFT (Abzweig an Stellen hoher KL), nicht, ob der Kopf daraus lernt. Der Mechanismus (am
Code gelesen 2026-09-27): die Abzweigstelle waehlt die Policy-Diskrepanz, die Abweichung selbst der
Value-Kopf (`deviation_best_action`, `engine/src/self_play.rs:3015`: unter zufaelligen Kandidaten
ohne den Suchzug der mit dem besten Kopfwert der Folgestellung), danach laeuft der Ausflug greedy
bis zum Ende und liefert nur Wertziele. Gemessen ist bisher nur, dass der Kopf AN solchen Stellen
schlechter liegt (par.6a, A +0,0292), nicht, dass Wertziele von dort ihn dort verbessern.

**Messung (Doppel-Differenz, Werkzeug-Definitionen wie par.6a):**
* **Grundmenge:** Drafting-Records Runde 1-4 MIT `root_q`, `completed is not False`, aus der
  v34-Val-Menge; Auswahl wie par.2 (60 Dateien, je Klasse gleich viele, Seed 20260926). **Einheit**
  Zustand, **Block** Datei. Weder der Generator noch der v34-Arm hat diese Dateien trainiert.
* **Zeiger:** `KL(Ziel || Prior)` wie par.3, Prior aus dem GENERATOR der Daten (nicht aus dem
  neuen Arm), damit beide Koepfe auf denselben Zustaenden verglichen werden. Oberstes Dezil
  (KL >= q90) und untere Haelfte (KL <= q50) wie in `analyse()` des Vortest-Werkzeugs.
* **Groesse:** `DiD = [Brier(neu) - Brier(Generator)]_oberstes Dezil - [Brier(neu) - Brier(Generator)]_untere Haelfte`,
  Brier des rohen Kopfs gegen den Sieg des Ziehers, Block-Bootstrap ueber Dateien (wie par.6a).
  Negativ heisst: der neue Kopf hat dort, wo abgezweigt wurde, MEHR dazugelernt als im Rest.
* **v34:** neu = der v34-Arm mit Knopf, Generator = der Generator der v34-Erzeugung.
* **Kontrolle v33** (derselbe Generationsschritt OHNE KL-Abzweigen, Ausflug nach Profil x
  Aktionszahl): neu = `v33-b01`, Generator = `v32-b01`, Val-Menge `data/window_v33_val.txt`, dieselbe
  Auswahl wie par.6a. Noetig, weil ein neuer Kopf ohnehin dort mehr aufholen kann, wo der alte
  schlecht lag (Regression zur Mitte, Auswahl nach einem fehler-korrelierten Zeiger). Die Kontrolle
  darf VOR der v34-Erzeugung laufen (alle Teile liegen vor), exklusiv wie jede Sonde.
* **Primaere Groesse:** `E = DiD(v34) - DiD(v33)`, CI aus unabhaengigen Bootstrap-Ziehungen beider
  Mengen (gleiche Zahl Ziehungen, paarweise differenziert).

**Leseregel, VORAB:**
* **E < 0 mit CI-Obergrenze < 0:** der Knopf wirkt auf den Kopf, gezielt an den Abzweigstellen.
* **CI von E ueberdeckt 0:** kein zuordenbarer Lerneffekt; das Abzweigen nach KL erzeugt andere,
  aber nicht nachweisbar lehrreichere Stellungen. Die Linie gilt damit fuer diese Architektur als
  abgeschlossen (kein eigener Arm mehr, Nutzer-Richtung: danach alternative Ansaetze).
* **E > 0 mit CI-Untergrenze > 0:** der Kopf lernt dort WENIGER als ohne Knopf; berichtet, v35
  (falls es eine gibt) faehrt ohne Knopf.
* Berichtet werden zusaetzlich DiD(v34) und DiD(v33) einzeln, n je Gruppe, die Brier-Werte beider
  Koepfe je Gruppe, und dieselbe Rechnung getrennt fuer die Ausflug-Dateien und fuer die uebrigen
  Klassen (der Knopf wirkt nur ueber die Ausflug-Klasse; wirkt er, sollte sich E dort zuerst zeigen).

**Grenzen, vorab benannt:** gemessen wird am Zeiger KL, nicht an den tatsaechlichen Abzweigstellen
des Trainingsmaterials (die liegen in Trainingsdateien, nicht in der Val-Menge). Und der v34-Arm
unterscheidet sich vom v33-Schritt nicht nur im Knopf (Paket, par.7); E ist darum ein Hinweis auf
die Wirkrichtung, kein isolierter Knopf-Effekt. Ein Arm ohne Knopf waere die saubere Kontrolle, ist
aber bewusst nicht vorgesehen (Kosten einer ganzen Erzeugung).

**Werkzeug:** Erweiterung von `tools/probes/targeted_branching_pretest.py` um einen zweiten Kopf
(`--model-new`; KL und Dezile bleiben beim `--model` = Generator), laufzeit-Block und
Fortschrittszaehler wie bisher. **Kosten, HERLEITUNG, ungemessen:** der Vortest brauchte 122,5 s fuer
ein Modell auf 60 Dateien; zwei Mengen mit je zwei Koepfen also rund 4 x 2 min, unter 10 min.

