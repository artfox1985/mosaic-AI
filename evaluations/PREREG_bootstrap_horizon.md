<!-- STATUS: ENTSCHIEDEN | Frage: Verbessert ein tieferer Bootstrap-Horizont (3 statt 2) das Value-Ziel -- und ist der zweite Rollout je Uebergang bezahlbar? | Beleg: BEIDE ARME NEGATIV, Prereg geschlossen 2026-08-25. ANKER-ARM (par.8): Kostengate gerissen, Aufschlag 60,7 Prozent gegen Schwelle 25. TIEFEN-ARM 2 gegen 3 (par.9f): gepaart auf 200 Zustaenden trifft Horizont 3 den echten Partieausgang SCHLECHTER (Brier gepaart +0,0567 +- 0,0254, Null klar ausgeschlossen) und kostet Faktor 1,63 je Label. Der Waechter aus par.9c greift NICHT: 51 Prozent der Zustaende weichen um mehr als 0,01 ab, im Mittel 0,089 -- die Frage war echt, nur die Antwort negativ. Damit erzeugt v22 mit HORIZONT 2; der Wert steht bei der ERZEUGUNG im Korpus (self_play.rs:1941) und ist spaeter nur durch Neu-Labeln aenderbar. BERICHTIGUNG par.9g: der Messkorpus war trotz --heuristik-variante v2huelle ein V1-Korpus (die Variante erreichte den aufzeichnenden Pfad nicht, Commit 224cc42; die Draft-Seite ist weiter blind). Am Verdikt aendert das nichts -- gepaart auf denselben Zustaenden -- wohl aber an der Reichweite: gemessen wurde im ALTEN Regime. WIEDERAUFNAHME beider Arme nur mit einem Korpus, in dem tatsaechlich Spalten gebaut werden; diese Bedingung ist unveraendert offen. Sonde: tools/probes/bootstrap_horizon_paired_probe.py. -->

# Vorregistrierung: Bootstrap-Horizont (2 vs 3) -- Option fuer den v22-Zuschnitt

**Angelegt 2026-08-09, VOR jeder Messung und VOR dem v22-Self-Play.**
Nutzer-Auftrag: *"takte es ein"*, nach der Feststellung, dass der
Horizont nur beim Erzeugen neuer Partien ueberhaupt aenderbar ist.

## Warum der Horizont nur JETZT aenderbar ist

`BOOTSTRAP_HORIZON_ROUNDS = 2` liegt in
`engine/src/round_transition_deep.rs:168` (Stand 2026-08-21; bei
Registrierung Zeile 153), ist also **engine-seitig** und
wird beim Self-Play in die Records geschrieben. Er steckt **nicht** im
Cache-Schluessel (`str(files)+INPUT_SIZE+NUM_ACTIONS+VALUE_SCHEMA_VERSION+
POLICY_TARGET_SHARPEN_EXPONENT+TD_LAMBDA+...`) -- zwei Konsequenzen:

1. Auf einem bestehenden Fenster ist er **nicht sweepbar**. Eine Aenderung
   verlangt NEUES Self-Play.
2. **Fussangel**: wer die Konstante aendert, ohne neu zu generieren,
   bekommt stillschweigend den alten Cache und merkt nichts. Gehoert in
   die geltenden Regeln.

Damit ist der v22-Generierungsstart der einzige Zeitpunkt dieser
Generation, an dem die Frage ohne zusaetzliche Generierungskosten
beantwortbar ist -- danach ist das Fenster geschrieben.

## Warum die Frage heute mehr Gewicht hat als beim Parken

Der Horizont wurde in der v12-Aera geparkt ("teuer, Noise-Floor stuetzt
2"). Damals lief `rtv` parallel und teilte die Arbeit. Seit `nortv`
(v13-Champion) ist der TD-Bootstrap das **einzige** Mittel, das die
Fabrik-Neubefuellung mittelt -- der Zufallsknoten, den der Nutzer als die
stark zufaellige Komponente benannt hat. Die Parkbegruendung ist also
schwaecher geworden, ohne dass es nachgezogen wurde.

## Das Problem des rotierenden Fensters

v22 hat 12.000 neue von 29.450 Partien, in der Value-Klasse 8.000 von
23.650. Uebernommene Partien tragen ihre Labels mit dem ALTEN Horizont
fuer immer. Ein "v22 mit Horizont 3" haette also nur ~34% behandelte
Value-Labels -- konfundiert, und ein Nullergebnis waere nicht von "Dosis
zu klein" zu unterscheiden. Genau die Falle, die heute schon bei λ ueber
die Aussagekraft entschied.

## Zuschnitt: BEIDE Labels mitschreiben, dann zwei Arme auf identischen Partien

Waehrend der v22-Generierung wird je Rundenuebergang der Bootstrap-Wert
fuer Horizont 2 **und** Horizont 3 in denselben Record geschrieben. Dann:

- ein Cache (Schema-Bump, neues Feld), **zwei Trainings-Arme**, die sich
  ausschliesslich darin unterscheiden, welches Feld sie als Value-Ziel
  lesen;
- die uebernommenen Alt-Partien sind in BEIDEN Armen identisch (Horizont
  2, unveraenderbar) -- die Differenz zwischen den Armen ist damit
  **exakt** der Horizont auf dem neuen Drittel.

Das behebt die Konfundierung, nicht die Verduennung: der Effekt bleibt
auf ein Drittel der Value-Labels beschraenkt. **Vorab festgehalten**: ein
H0 ist deshalb ein SCHWACHER Beleg gegen den Horizont, kein starker. Wer
ihn spaeter als "Horizont 3 widerlegt" zitiert, zitiert falsch.

## Stufe 1 (GATE, vor allem anderen): Kosten des zweiten Rollouts

Der Bootstrap ist ein Netz-Rollout ueber N Runden, ~4x je Partie. Der
rtv-Praezedenzfall zeigt, dass Rollouts teuer werden koennen: 24 Samples
kosteten **81% der Self-Play-Zeit**. Ein zweiter Rollout je Uebergang ist
also nicht selbstverstaendlich billig -- das wird GEMESSEN, nicht
geschaetzt: Self-Play-Zeit je Partie mit einem Rollout gegen zwei
(kleine Stichprobe, ~50 Partien, gleicher Seed).

**Entscheidungsregeln (vorab):**
1. Aufschlag **<= +25%** Self-Play-Zeit ⇒ Stufe 2 wird gefahren.
2. Aufschlag **> +25%** ⇒ **verworfen**, ohne Rueckfrage. Begruendung: bei
   12.000 Partien und ~10h Generierung ist mehr als ein Viertel
   Aufschlag fuer eine Frage, deren Effekt ohnehin auf ein Drittel der
   Labels verduennt ist, nicht vertretbar. Der Nutzer hat diese
   Verwerfungs-Option ausdruecklich verlangt.
3. Der Horizont-3-Rollout darf die Horizont-2-Werte **nicht** veraendern
   (Paritaets-Nachweis am Label: dieselben Partien, Horizont-2-Feld
   bit-identisch zum Einzel-Rollout-Lauf). Sonst ist der Vergleich
   wertlos.

### Stufe 1 ERGEBNIS + VERDIKT (2026-08-24): GATE GERISSEN, Arm verworfen

`tools/probes/bootstrap_horizon_cost_gate.py`, Artefakt
`evaluations/artifacts/bootstrap_horizon_cost_gate.json`.

| Groesse | Wert |
| --- | --- |
| Kosten je Label, Horizont 2 | 223,8 ms (Median 246,0) |
| Kosten je Label, Horizont 3 | 410,2 ms (Median 436,5) |
| Verhaeltnis h3/h2 | **1,83** |
| Anteil Bootstrap an der Self-Play-Zeit | **33,1 Prozent** |
| **Aufschlag fuer BEIDE Labels** | **60,7 Prozent** |
| Schwelle | 25 Prozent |

**Vorregistrierte Folge: verworfen, ohne Rueckfrage.** Der 2-gegen-3-Arm ist
damit fuer den v22-Zuschnitt geschlossen; Horizont 2 bleibt.

**Robustheitspruefung, weil das Verdikt an einer Einstellung haengt:** der
Bootstrap-Anteil faellt, wenn die Self-Play-Suche teurer wird. Gemessen wurde
mit 300 Sims, der CLI-Default ist 100 (`self_play.py:688`). Weniger Sims
heissen weniger Suchzeit und damit einen HOEHEREN Bootstrap-Anteil -- bei der
Produktionseinstellung faellt der Aufschlag also groesser aus, nicht kleiner.
Das Verdikt kippt in dieser Richtung nicht.

**Die billigere Variante reisst das Gate ebenfalls, aber knapp:** wuerde man
statt beider Labels nur auf Horizont 3 UMSTELLEN, betruege der Aufschlag
33,1 Prozent mal 0,83 = **27,5 Prozent**. Immer noch ueber der Schwelle, aber
nah dran. Registriert, damit niemand die 60,7 Prozent als "Faktor 2,4 zu
teuer" liest: der Zuschnitt "beide schreiben" kostet das Doppelte des
Umstellens, und er ist es, den die Prereg vorsieht (er traegt den gepaarten
Vergleich).

**Zwei Bestaetigungen nebenbei:** die 223,8 ms decken sich mit den 235 ms aus
Stufe 0 -- unabhaengige Messung, gleiche Groesse. Und die strukturelle
Vorhersage ("derselbe Ein-Stichproben-Pfad mit einer Iteration mehr, also
Richtung Verdopplung") trifft mit 1,83, waehrend dieselbe Art Vorhersage beim
Anker-Arm um Faktor 13 danebenlag. Der Unterschied ist genau
`N_SAMPLES_TRAIN = 24` gegen 1 Stichprobe je Uebergang.

**Was NICHT geschlossen ist:** die Frage, ob ein tieferer Horizont das ZIEL
besser macht. Sie ist nicht beantwortet, sondern unbezahlbar -- und beide
Faktoren des Preises (Anteil und Verhaeltnis) sind an plattenblindem Spiel
gemessen. Es gilt dieselbe Wiederaufnahme-Bedingung wie fuer den Anker-Arm
(s. Nachtrag 2026-08-24 oben): ein Korpus mit echtem Spaltenbau ist ein neues
Regime, in dem sowohl der Nutzen als auch der Anteil anders liegen koennen.

## Stufe 2 (nur nach Stufe 1): zwei Arme

Training beider Arme mit identischem Rezept, Fenster und Seed; Gating
jedes Arms gegen den dann amtierenden Champion (Standard-SPRT, 400 Sims,
Block-Ebene, Fruehstopp-Replikationsregel).

- **Ein Arm gewinnt** ⇒ dieser Horizont wird Standard fuer kuenftige
  Generationen. Hinweis fuer die Umsetzung: die Umstellung wirkt nur auf
  NEUE Partien, das Fenster laeuft also ueber ~3 Generationen hinweg
  gemischt -- das ist dokumentiert und kein Fehler.
- **Beide H0** ⇒ Horizont 2 bleibt, Frage fuer die Aera geschlossen, mit
  dem Verduennungs-Vorbehalt oben.

## Nicht Teil davon

- Kein Sweep weiterer Horizonte (4+). Jeder zusaetzliche Wert kostet
  einen weiteren Rollout je Uebergang.
- Keine Aenderung an `TD_LAMBDA` (entschieden: Sweep empfahl 0,7, die
  Arena verwarf es 30:70, λ=0,5 bleibt).
- Keine Aenderung am v22-Fenster-Zuschnitt selbst (`PREREG_v22_window.md`
  bleibt gueltig; dieses Dokument ergaenzt nur eine Label-Option).

## Nachtrag 2026-08-21: zwei Umstaende haben sich veraendert, die Prereg bleibt scharf

1. **Regel 3 der Stufe 1 ist erstmals realistisch fuehrbar.** Der
   Paritaets-Nachweis (Horizont-2-Feld bit-identisch zum Einzel-Rollout)
   waere an den Task-#71-Wall-Clock-Not-Deckeln in
   `round_transition_deep.rs` gescheitert -- genau die Divergenzquelle,
   die das Async-Gate-B aufgedeckt hat. Seit
   `PREREG_deterministic_labels.md` (ENTSCHIEDEN 2026-08-14: Not-Deckel
   degradieren deterministisch, 1956/1956 Records byte-identisch unter
   kuenstlichem CPU-Stress) ist dieser Blocker weg.
2. **Die Verduennungsrechnung haengt an EINER offenen Zuschnitts-Frage
   (praezisiert nach Nutzer-Rueckfrage 2026-08-21).** Bleibt das
   v22-Fenster exakt der registrierte Zuschnitt (nur wdl-Rotations-
   klassen), gilt ~34 % unveraendert -- die seit dem 08.08. entstandenen
   Lehr-Korpora (Ownership 8.000, Asym 16.000) tauchen darin nicht auf.
   NUR falls das heutige Asym-Arm-Rezept (par.9 dort: v21-Fenster PLUS
   Lehr-Korpus) bis zum v22-Training uebertragen wird, waechst der
   Value-Nenner und der behandelte Anteil faellt Richtung ~20 % -- dann
   wird der Vorbehalt "H0 ist ein schwacher Beleg" entsprechend
   staerker. Die round5-Fix-Grenze konfundiert den A/B dagegen NICHT
   (Altpartien liegen in beiden Armen identisch); sie macht die
   Alt-Labels nur heterogener, als gemeinsames Rauschen beider Arme.

Der Ausfuehrungszeitpunkt ist unveraendert der v22-Generierungsstart --
und der liegt laut Fahrplan NACH dem plattenbewussten Modell (erst
Lehr-Korpora/Asym-Curriculum, dann Self-Plays). Ein Wecker dafuer steht
jetzt direkt im Halde-Kasten von `PREREG_v22_window.md`.

## Nachtrag 2026-08-23: neuer Anlass (Vollendungs-Strukturbefund) + Nutzer-Vorschlag rundenabhaengiger Horizont

**Neuer Anlass, der dieser Prereg deutlich mehr Gewicht gibt** (Kette in
evaluations/STATUS.md, STAND 2026-08-23, mit Artefakten): der Champion
vollendet keine Brett-Spalten (0,10/Partie, plattenunabhaengig; 0,55
Hoehe-5-Spalten je Partie bleiben stehen), meidet die langen
Musterreihen 5/6 FLACH ueber alle Runden -- waehrend das
Heuristik-Selfplay (der Abstammungs-Lehrer) spaet auf lange Reihen
umschwenkt. Der Bias ist also NICHT geerbt, sondern im Training
verloren gegangen. Verdachtspunkt (Herleitung, ungemessen): die
verzoegerte Auszahlung frueher Langreihen-Investitionen faellt aus dem
Kredit-Horizont der Value-Ziele.

**Code-Praezisierung dazu (2026-08-23 verifiziert):** der Horizont
schneidet zum NETZ-Leaf-Eval ab (Modulkommentar zu
BOOTSTRAP_HORIZON_ROUNDS: "bevor per net_leaf_eval direkt bewertet
wird, statt bis zum echten Spielende zu rekursieren"); der Uebergang
R4->R5 laeuft bereits ueber den EXAKTEN Freebie
(self_play.rs:2898, exact_round5_outcome), Runde 5 wird nicht
gelabelt. Folge: SPAETE Ziele reichen faktisch schon ans echte Ende;
die Beschneidung beisst FRUEH -- R1/R2-Ziele enden nach zwei Runden im
Netz-Eval von R3/R4, und genau dort muesste die Auszahlung frueher
Reihe-5/6-Fuetterung durch einen Value-Kopf, der Spaltenwert nie
gelernt hat (Sibling-/Kalibrierungs-Befunde).

**Nutzer-Vorschlag (2026-08-23, "der bootstrap horizon kann ja mit
jeder runde kleiner werden"):** rundenabhaengiger Horizont als
dritter Arm-Kandidat -- praktisch gelesen als "Ziele reichen immer
bis zu einem festen ANKER-Zeitpunkt (z. B. Runde-5-Start mit exaktem
Freebie) statt fester Tiefe": R1 saehe dann 4 Runden weit, R3 zwei --
der Horizont schrumpft je Runde, und KEIN Ziel endet mehr in einem
Netz-Eval mitten im Spiel. Passt in den bestehenden Zuschnitt (beide
-- bzw. dann drei -- Labels beim v22-Self-Play mitschreiben, Stufe-1-
Kostengate gilt je zusaetzlichem Rollout; die tiefen fruehen Rollouts
sind der Kostentreiber und genau das, was Stufe 1 beziffern muss).
Arm-Auswahl (2v3 vs. rundenabhaengig vs. beides) = Nutzer-Entscheid
beim v22-Start; diese Prereg bleibt der registrierte Ort dafuer.

## Nachtrag 2026-08-24: der Anker-Arm ist bereits GEMESSEN -- rtv-Waechter und Wiederaufnahme-Bedingung

Der Nutzer hat den rundenabhaengigen Horizont am 2026-08-24 erneut
aufgebracht ("ich brauch dann aber keinen konstanten horizon oder? denn kann
ich ja abnehmen lassen mit hoeherer rundenanzahl"). **Die Frage ist bereits
beantwortet:** Stufe 0 (unten, ENTSCHIEDEN 2026-08-23) hat die Anker-Variante
gemessen und geschlossen. Dieser Nachtrag traegt nichts Neues zur Idee bei,
sondern haelt drei Dinge fest, die dabei zur Sprache kamen.

### 1. Selbstkorrektur: eine Kostenrechnung, die um Groessenordnungen danebenlag

Beim Aufgreifen habe ich die Kosten aus der Struktur GESCHAETZT statt die
vorhandene Messung zu lesen: `h` simuliert `h-1` Runden, gelabelt werden die
Rundenenden 1 bis 4, also konstant 2 = 4 simulierte Runden je Partie,
konstant 3 = 7, Anker am R5-Start = 6. Daraus las ich "der Anker kostet das
1,5-fache".

**Gemessen sind 4.734 ms gegen 235 ms je Label, Faktor 20,1** (Stufe 0). Die
Schaetzung lag um mehr als eine Groessenordnung daneben, weil sie eine
simulierte Runde als konstanten Posten behandelt -- der Anker-Rollout ist
aber strukturell die vorhandene rtv-Kette
(`sample_round_transition_for_round`) mit rekursiven
`continue_through_round{2,3,4}`-Ketten, nicht ein flacher Durchlauf. Die
Lehre ist die alte: **eine Aufwandsstruktur, zu der eine Messung existiert,
wird nicht aus dem Code hergeleitet.**

### 2. WAECHTER GEGEN DIE rtv-FALLE (Nutzer-Auflage 2026-08-24)

Nutzer-Wortlaut: "pass auf das wir dann nicht wieder in die rtv falle tippen."
Die Auflage trifft und ist durch Stufe 0 bereits eingeloest: der Anker-Arm
HAT dieselbe Bauform wie rtv (mehr Rollout je Label fuer ein vermeintlich
besseres Ziel), ist strukturell sogar dieselbe Kette, und faellt mit
Faktor 20,1 aus jedem Kostenrahmen.

Fuer den weiterhin offenen 2-gegen-3-Arm gilt vorab festgelegt:

1. **Das Stufe-1-Kostengate (<= +25 Prozent Self-Play-Zeit) bindet** und wird
   gemessen, nicht geschaetzt (siehe Punkt 1 -- genau dieser Fehler ist am
   2026-08-24 einmal passiert).
2. **"Das Ziel sieht sauberer aus" ist kein Argument.** rtv sah auch sauberer
   aus und machte das Netz schlechter; entschieden wird an Staerke.

### 3. WIEDERAUFNAHME-BEDINGUNG (Nutzer-Einwand 2026-08-24)

Nutzer im selben Zug: "aber auch das relativiert sich, weil wir keine Ahnung
haben was das Netz macht wenn es wirklich Spalten baut."

Der Einwand ist berechtigt und praezisiert, was der Stufe-0-Verdikt-Satz
"nicht neu vorschlagen ohne neues Regime" bedeutet. **Beide Stufe-0-Zahlen
sind an Zustaenden aus plattenblindem Spiel erhoben** -- kritische Zellen wie
Kosten. Sie fallen damit unter dieselbe Kontaminationsregel wie jede andere
Aera-Messung: sie schliessen den Arm FUER DAS HEUTIGE REGIME, nicht
grundsaetzlich.

**Der Ausloeser fuer eine Wiederaufnahme ist damit benannt und pruefbar:** ein
Korpus, in dem tatsaechlich Spalten gebaut werden (etwa aus
`PREREG_heuristic_v2_long_rows.md`). Dort waeren die kritischen Zellen andere
Zustaende, und die Frage, ob tiefere Ziele die Auszahlung tragen, waere neu
zu stellen. Vorher nicht.

Dasselbe gilt fuer den Satz "Kredit-Horizont-Verdacht ist GESCHWAECHT" im
Verdikt unten: er ist an Labels von Netzen gemessen, die keine Spalten bauen.
Er darf nicht als "der Horizont ist als Erklaerung erledigt" weiterzitiert
werden.

### Anlass-Stand 2026-08-24 (fuer den offenen 2-gegen-3-Arm)

Der Vollendungs-Strukturbefund, der diese Prereg am 2026-08-23 aufgewertet
hat, ist inzwischen deutlich besser belegt -- und er zeigt inzwischen
woanders hin als auf den Horizont:

- **Erste unkontaminierte Referenz:** zehn Mensch-gegen-Netz-Partien
  (`static/log/`, Nutzer gewinnt 8 von 9) ergeben 1,80 volle Spalten je
  Partie gegen 0,10 des Netzes
  (`tools/probes/human_row_profile_probe.py`).
- **Der Lehrer kann es auch nicht** (407 Partien: volle Spalten 0,098 gegen
  0,101). Der Bias ist also weder geerbt noch im Training verloren gegangen,
  er war nie da -- das schwaecht die Formulierung "im Training verloren
  gegangen" im Nachtrag vom 2026-08-23.
- **Der Engpass ist Verteilung, nicht Versorgung:** eine volle Spalte kostet
  21 Zellen; das Netz verbraucht 42,7 Zellen und truege damit gleichverteilt
  2,03 Spalten statt 0,10 (`tools/probes/row_supply_ceiling_probe.py`).

Zusammen mit dem Stufe-0-Verdikt heisst das: der Horizont ist nicht mehr der
Hauptverdaechtige fuer die Vollendungsschwaeche. Der 2-gegen-3-Arm bleibt als
eigenstaendige Ziel-Qualitaetsfrage offen, aber er sollte nicht mehr als
deren Loesung verkauft werden.

## Stufe 0 (NEU, Nutzer-Freigabe 2026-08-23 "im kleinen testen/debuggen"): Label-Diagnose OHNE Training

Vor jedem v22-Commitment eine reine Diagnose-Sonde, kein Korpus, kein
Training:

1. **Bau (additiv):** eine Probe-Funktion, die fuer einen uebergebenen
   Zustand BEIDE Label-Varianten berechnet -- (a) Bestand: Horizont 2,
   Abschluss per net_leaf_eval; (b) Anker-Variante: Rollout bis zum
   Runde-5-Start, Abschluss per exact_round5_outcome-Freebie. KEINE
   Aenderung an Records/Cache/Selbstspiel-Pfad; eigenes Werkzeug nach
   Sonden-Muster.
2. **Messung:** 200-300 Zustaende aus VORHANDENEN fertigen Partien
   (Arena-/Korpus-Records; echter Endausgang bekannt), stratifiziert
   nach Runde (Schwerpunkt R1-R2) und Spalten-/Langreihen-Fortschritt.
   Ausgewiesen: (i) Label-Divergenz nach Runde x Fortschritt, (ii)
   Korrelation beider Varianten mit dem ECHTEN Endresultat, gesamt und
   auf den kritischen Zellen (frueh + hoher Fortschritt), (iii)
   Rechenzeit je Anker-Label (Kostengate-Vorschau: der tiefe fruehe
   Rollout ist der Treiber).
3. **Lesart VORAB:** die Anker-Variante qualifiziert sich fuer einen
   v22-Arm, wenn sie auf den kritischen fruehen Zustaenden besser mit
   dem Endresultat korreliert UND die Kosten je Label ein
   Stufe-1-Bestehen plausibel machen; andernfalls ist der
   Kredit-Horizont-Verdacht geschwaecht und der klassische 2v3-Arm
   bleibt allein. Start nach Abschluss des laufenden
   Welle-3-Engine-Bauslots (Cargo-/Lastkonflikt vermeiden).

### Stufe 0 ERGEBNIS + VERDIKT (2026-08-23; Agent, alle tragenden Zahlen vom Koordinator am Artefakt nachgemessen)

**VERDIKT nach der vorregistrierten Lesart: die Anker-Variante
QUALIFIZIERT SICH NICHT. Beide Bedingungen verfehlt.**

- **Kritische Zellen (Hauptmetrik, R1-2 x hoher Fortschritt, n=130):**
  Anker **0,282** gegen Bestand **0,363** (Pearson; Spearman
  gleichlaufend) -- der Anker ist dort SCHLECHTER, nicht besser.
- **Kosten:** 4.734 ms gegen 235 ms je Label = **Faktor 20,1** (Median
  4.476/208). Die Stufe-1-Schwelle (<= +25 % Self-Play-Zeit) ist damit
  ausser Reichweite.
- Gegenlaeufig und ehrlich ausgewiesen: GESAMT ist der Anker besser
  (0,419 gegen 0,386, n=480), ebenso auf der sekundaeren
  Punktemargen-Skala. Deutung (HERLEITUNG, ungemessen): der
  Anker-Rollout ist eine STICHPROBE des Rundenuebergangs, keine
  Bewertung -- ueber vier Runden akkumuliert Sampling-Varianz, was
  gerade die langen fruehen Rollouts (die kritischen Zellen) trifft,
  waehrend der Bias-Vorteil im Mittel sichtbar bleibt.
- **Struktur-Befund des Scouts (am Code, wichtig):** die Anker-Variante
  ist KEIN Neubau, sondern strukturell die vorhandene rtv-Kette
  (sample_round_transition_for_round, self_play.rs:2975ff; R4->R5 per
  exact_round5_outcome). bootstrap_value_after_rounds endet dagegen
  IMMER in net_leaf_eval (round_transition_deep.rs:852) -- ein
  groesserer Horizont allein waere nie in den Freebie gelaufen.
- **Historische Konsistenz (nachgeprueft, archive/history.md Task #80,
  Z.2255ff):** dort schon registriert, dass rtv schwaecher mit dem
  echten Ausgang korreliert als das billigere bootstrap und ~83 % der
  Suchkosten trug; v13_nortv wurde Champion, nachdem rtv aus dem
  Value-Ziel fiel. Stufe 0 reproduziert das auf den kritischen Zellen
  und beziffert den Preis erstmals je Label. (Nuance: gesamt faellt
  Stufe 0 anders aus als der Task-#80-Satz -- andere Metrik/Aera,
  nicht als glatte Bestaetigung lesen.)
- **Folge fuer die Prereg:** der Anker-/rundenabhaengige Arm ist damit
  fuer den v22-Zuschnitt GESCHLOSSEN (nicht neu vorschlagen ohne neues
  Regime). Der klassische 2-gegen-3-Arm bleibt unberuehrt offen. Der
  Kredit-Horizont-Verdacht als Erklaerung der Vollendungsschwaeche ist
  GESCHWAECHT: tiefere Ziele allein machen die Labels auf genau den
  Zustaenden nicht besser, an denen der Spaltenbau entschieden wird.
- Restpunkt: die Fortschritts-Definition der Stichprobe (max col_fill
  ueber beide Spieler, am ersten Tiling-Record der FOLGERUNDE
  gemessen) ist eine markierte Annahme des Agenten, nicht
  vorregistriert.

---

## par.9 EINGETAKTET 2026-08-25: gepaarter Klein-Ausschnitt auf v2-Partien

**Nutzer-Entscheid.** Anlass ist die eigene Wiederaufnahme-Bedingung dieser
Prereg -- "beide Zahlen sind an plattenblindem Spiel erhoben, ein Korpus mit
echtem Spaltenbau waere ein neues Regime" -- und die anstehende v22-Kampagne
mit der Heuristik v2 als Erzeuger (volle Spalten 0,798 je Partie gegen 0,086).

### par.9a Warum das VOR der Kampagne entschieden werden muss

Der Bootstrap-Wert wird **bei der Erzeugung** in den Korpus geschrieben
(`self_play.rs:1941-1954`, `bootstrap_value_after_rounds(&pre, lbl.net,
BOOTSTRAP_HORIZON_ROUNDS, rng)`). Einen anderen Horizont spaeter zu pruefen
heisst also neu labeln oder neu erzeugen -- es ist kein Trainingsschalter.
Wer die Frage offen laesst, entscheidet sie faktisch zugunsten des Bestands.

**Am Code geprueft, weil es leicht falsch erinnert wird:** der Bootstrap-Wert
wird IMMER vom Netz gerechnet, unabhaengig davon, wer spielt. Der Pfad haengt
nur daran, ob ein Netz FUER DIE LABELS uebergeben wurde
(`labels: net.map(...)`, `self_play.rs:2209`) -- genau dafuer gibt es
`run_self_play_with_net_labels`: die Heuristik spielt, ein Netz labelt. Ohne
Label-Netz gibt es gar keine Bootstrap-Labels, und das Value-Ziel faellt auf
den harten Ausgang zurueck.

### par.9b Zuschnitt

Ein KLEINER Ausschnitt v2-erzeugter Partien, **zweimal gelabelt** -- Horizont
2 (Bestand) gegen Horizont 3 --, dieselben Partien und dieselben Seeds in
beiden Durchlaufen. Damit ist der Vergleich gepaart und braucht keine Arena.

**Vorbedingung, ohne die es nicht laeuft:** der Self-Play-Einstieg ist auf die
V1-Heuristik festgenagelt (`heuristik_variante: HeuristikVariante::V1`,
`self_play.rs:2201`); nur die Arena nimmt die Variante als Parameter. Die
Variante muss bis `run_self_play`/`run_self_play_with_net_labels`
durchgereicht werden, bevor ueberhaupt v2-Partien erzeugt werden koennen.

### par.9c Drei Kennzahlen, vorab festgelegt

1. **Unterscheiden sich die Labels ueberhaupt?** Mittlere absolute Differenz
   der beiden Bootstrap-Werte je Datensatz. **Waechter:** ist sie klein, kauft
   der tiefere Horizont nichts -- unabhaengig von allem anderen, und der Arm
   ist ohne weitere Messung erledigt.
2. **Welcher Horizont trifft den tatsaechlichen Ausgang besser?** Beide
   Bootstrap-Werte gegen den ECHTEN Partieausgang (Brier und MSE). Das ist die
   Aufgabe des Ziels, und sie ist auf ausgespielten Partien offline messbar.
   **Einschraenkung, ausdruecklich:** eine bessere Ausgangs-Uebereinstimmung
   ist nicht automatisch ein besseres TD-Ziel -- ein Bootstrap, der den
   Ausgang nur kopiert, traegt nichts ueber den harten Ausgang hinaus bei.
   Deshalb wird (1) MITBERICHTET und nicht durch (2) ersetzt.
3. **Kostenfaktor**, gemessen statt geschaetzt: Wanduhr je Label in beiden
   Durchlaufen. Der Bestandswert, an dem der Arm 2026-08 gescheitert ist,
   waren +60,7 Prozent gegen eine Schwelle von 25 -- gemessen an
   plattenblindem Spiel. Auf v2-Partien kann er anders liegen: dort laufen
   Partien mit mehr vollen Spalten, und der Horizont sieht mehr Struktur.

### par.9d Lesarten, vorab

- **Labels praktisch gleich** (Kennzahl 1 klein): Arm erledigt, Korpus mit
  Horizont 2 erzeugen. Das ist ein vollwertiges Ergebnis.
- **Labels verschieden UND Horizont 3 trifft den Ausgang besser UND der
  Kostenfaktor bleibt unter der Schwelle**: Nutzer-Entscheid, ob die Kampagne
  mit Horizont 3 faehrt.
- **Labels verschieden, aber Horizont 3 trifft nicht besser**: Bestand, und
  der Befund gehoert hierher -- der tiefere Horizont sieht dann zwar mehr,
  aber nichts Nuetzliches.

**Nicht Gegenstand:** Spielstaerke. Ein Klein-Ausschnitt entscheidet die
Ziel-Qualitaet und die Kosten, nicht Elo.


### par.9e VORLAEUFIGES ERGEBNIS (2026-08-25, n=60): Horizont 3 ist SCHLECHTER

Erster Durchlauf auf v2huelle-Partien, gepaart auf denselben Zustaenden.
Korpus `data/probe_v2huelle_horizon.pkl` (20 Partien, 3444 Datensaetze, 837
Tiling-Zustaende, erzeugt in 17 s mit `heuristik_variante="v2huelle"` --
moeglich erst seit dem Durchreichen der Variante). Zustaende ORDNUNGSFREI
gezogen (Seed 20260825), nicht "die ersten N" -- die Falle vom selben Tag.

| Kennzahl | Ergebnis |
| --- | --- |
| 1) Label-Differenz h3 gegen h2 | **0,0876 ± 0,0420**; 41,7 % der Zustaende weichen um mehr als 0,01 ab |
| 2) Brier gegen echten Ausgang | h2 **0,1615**, h3 **0,2215**; gepaart **+0,0600 ± 0,0569** |
| 3) Kosten je Label | 164,4 ms gegen 245,9 ms -- **Faktor 1,50** |

**Der Waechter aus par.9c schliesst den Arm NICHT** -- die Labels
unterscheiden sich deutlich, die Frage war also berechtigt. Aber der tiefere
Horizont trifft den tatsaechlichen Ausgang **schlechter**, bei 50 Prozent
Mehrkosten. Das Konfidenzintervall schliesst die Null knapp aus
(0,0600 − 0,0569 = 0,0031).

**Power, aus der gemessenen Streuung statt aus einer Annahme:** aus dem KI
folgt σ_d = 0,0569·√60/1,96 ≈ 0,225. Mit `n = 7,85·σ_d²/Δ²` braucht ein
Effekt von 0,06 rund 110 Zustaende, 0,02 rund 990, 0,01 rund 3970. Eine
Bestaetigungsrunde mit 200 Zustaenden ist damit ausreichend dimensioniert;
feiner zu messen waere sinnlos, weil ein Unterschied unter 0,015 ohnehin
unter der Aufloesungsgrenze liegt, ab der Offline-Masse in diesem Projekt die
Arena vorhersagen.

**Kostenhinweis fuer die Wiederholung:** die Sonde rechnet je Zustand
zusaetzlich den ANKER (rtv-Kette, ~4,9 s), der fuer diesen Vergleich nicht
gebraucht wird -- der reine Bootstrap-Aufruf kostet 0,16-0,25 s. Ein
`with_anchor=false` am pyo3-Einstieg wuerde die Messung rund zwanzigfach
verbilligen. Nicht gebaut, weil es produktiven Sondencode beruehrt.

### par.9f VERDIKT (2026-08-25, n=200): Horizont 3 VERWORFEN

Bestaetigungsrunde, gleicher Aufbau, gleicher Seed, 200 statt 60 Zustaende.

| Kennzahl | n=60 (Pilot) | **n=200 (Verdikt)** |
| --- | --- | --- |
| 1) Label-Differenz | 0,0876 ± 0,0420 | **0,0892 ± 0,0191**; 51,0 % ueber 0,01 |
| 2) Brier h2 | 0,1615 | **0,1875 ± 0,0377** |
| 2) Brier h3 | 0,2215 | **0,2441 ± 0,0489** |
| 2) gepaart h3−h2 | +0,0600 ± 0,0569 | **+0,0567 ± 0,0254** |
| 3) Kostenfaktor | 1,50x | **1,63x** (185,0 gegen 302,2 ms) |

**Beide Zahlen halten, und das Intervall schliesst die Null jetzt klar aus**
(+0,0313 bis +0,0821). Der tiefere Horizont trifft den echten Partieausgang
schlechter, bei 63 Prozent Mehrkosten je Label.

**Der Waechter aus par.9c greift weiterhin nicht** -- die Labels sind nicht
etwa gleich: gut die Haelfte der Zustaende weicht um mehr als 0,01 ab, im
Mittel um 0,089. Der Arm war also eine echte Frage; die Antwort ist nur
negativ. Das unterscheidet dieses Ergebnis von einem Null-Befund aus einem
wirkungslosen Knopf.

**Nachgerechnete Power:** aus dem Intervall folgt σ_d = 0,0254·√200/1,96 ≈
0,183. Damit braucht Δ=0,06 rund 73 Zustaende, Δ=0,02 rund 660, Δ=0,01 rund
2640. Die 200 waren reichlich dimensioniert; der Pilot mit 60 lag knapp unter
der noetigen Zahl, was das gerade eben ausgeschlossene Intervall dort erklaert.

**Konsequenz fuer v22: Horizont 2.** Damit ist der letzte offene Punkt der
Korpus-Vorbereitung entschieden.

**Beide Arme dieser Prereg sind jetzt geschlossen** -- der Anker-Arm ueber das
Kostengate (par.8), der Tiefen-Arm hier ueber die Zielguete. Die
Wiederaufnahme-Bedingung bleibt in beiden Faellen dieselbe: ein Korpus, in dem
tatsaechlich Spalten gebaut werden. Der hier verwendete v2huelle-Korpus ist
ein Schritt in diese Richtung, aber 20 Partien sind kein Regimewechsel.

Sonde: `tools/probes/bootstrap_horizon_paired_probe.py` (aus dem Scratchpad in
den Baum uebernommen, damit die naechste Sitzung sie wiederholen kann);
Artefakt `evaluations/artifacts/bootstrap_horizon_paired_200.json` -- die Werte
darin sind aus der stdout-Ausgabe uebernommen, weil der Lauf noch die
Scratchpad-Fassung ohne Artefakt-Ausgabe nutzte; das Feld `herkunft` sagt das
auch im Artefakt selbst. Wanduhr **2151 s fuer 200 Zustaende** (10,8 s je
Zustand, aus den Zeitstempeln der Aufgabendatei), davon nur 0,49 s je Zustand
fuer die eigentlichen Bootstrap-Aufrufe -- der Rest ist der ungenutzte
Anker-Zweig.


### par.9g BERICHTIGUNG (2026-08-25, am selben Tag): der Korpus war V1, nicht v2huelle

`data/probe_v2huelle_horizon.pkl` wurde mit `--heuristik-variante v2huelle`
erzeugt, ist aber ein **V1-Korpus**. Grund: die Variante erreichte den
aufzeichnenden Tiling-Pfad nicht (`tiling_step` rief die varianten-blinde
Fassung; behoben in Commit `224cc42`), und die Draft-Entscheidung ist bis
heute variantenblind (`HeuristicSelfPlayAgent` hat kein Variantenfeld).
Nachgewiesen an einem 200-Partien-Paar: v2huelle und v1 waren bis auf die
letzte Nachkommastelle identisch (volle Spalten 0,004665140240412135 in
BEIDEN Armen).

**Was das am Verdikt aendert: nichts.** par.9f vergleicht Horizont 2 gegen 3
GEPAART auf denselben Zustaenden; welcher Erzeuger die Zustaende erzeugt hat,
geht in die Differenz nicht ein. Brier, Kostenfaktor und Power bleiben, wie
sie registriert sind.

**Was es aendert, ist die REICHWEITE.** Die Saetze in par.9e/par.9f, der Korpus
sei "ein Schritt Richtung Spaltenbau-Korpus" und die Messung liefe "auf
v2huelle-Partien", sind falsch: gemessen wurde im ALTEN Regime. Die
Wiederaufnahme-Bedingung beider Arme -- ein Korpus, in dem tatsaechlich
Spalten gebaut werden -- ist damit **unveraendert offen**, nicht
angenaehert. Sie ist es sogar staerker als gedacht, weil jetzt belegt ist,
dass der Lehrer im Self-Play noch gar nicht ankommt.

Lehre, und sie ist die teure: die Abnahme des Durchreich-Commits hat "gleicher
Seed, v1 gegen v2huelle -> die Partien unterscheiden sich" auf einem
ARENA-Pfad geprueft. Dort sitzt der Verbraucher. Der Pfad, fuer den der Umbau
gebaut war, war der einzige, den sie nicht angefasst hat.
