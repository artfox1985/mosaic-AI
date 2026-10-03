<!-- STATUS: OFFEN | Frage: Erzeugt asymmetrisches Self-Play (Wuerfel-Kuppelplatten auf einer Seite, spaeter ein stoerender Gegner) Stellungen, die das Spiel gegen sich selbst nicht erreicht, und traegt ein Fenster daraus? | Beleg: Bau-Fragen entschieden (par.3a). Klasse W gebaut 2026-10-03 (Lib-Tests gruen, noch kein Wheel), Klasse S im Bau; Leseregeln der Sonden S1-S4 registriert (par.5). Ziel-Zusammensetzung par.4. -->

# Vorregistrierung: asymmetrisches Self-Play (Wuerfel-Kuppelplatten, Stoerer)

**Angelegt 2026-10-01 als ENTWURF**, vor jedem Bau. Zeitpunkt: nach dem v34-Training
(`PREREG_v34_window.md`), als einer der alternativen Ansaetze nach der letzten Generation dieser
Architektur (Nutzer 2026-09-27).

## par.1 WARUM

**Nutzer 2026-10-01:** *"Ich will das self play um zwei neue klassen erweitern/ergaenzen ...
prinzipiell wuensch ich mir mehr asymetrisches self play um bewusst stellungen zu provozieren die
nicht entstehen wenn du gegen dich selber spielst."*

Zu (1): *"Ausflug bei der eine zufaellige Kuppelplatte gelegt wird, damit sich die sims auch bereits
in den fruehen runden tiefer in den baum graben. Die rotation und ID wird zufaellig gewaehlt, die
position dieser wahl dann ueber suche und netz gelegt. die zufaellige auswahl muss also schon kommen
bevor die blattbewertung kommt."* Praezisiert am selben Tag: *"bei dieser klasse werden alle
kuppelplatten zufaellig ausgewaehlt. der erzwungene plattenzug brauch keine records, alle zuegen
danach jedoch schon."*

Zu (2): *"assymetrisches Spiel gegen aggressiven/stoerenden gegner. diesen sind seine punkte nicht
ganz so wichtig, sein augenmerk liegt darauf unseren aufbau und spiel zu stoeren."*

**Vorlaeufer, alle gemessen und in anderer Form** (Kopfzeilen gelesen 2026-10-01):
`PREREG_asymmetric_curriculum.md` (ein Spieler baut k1, der andere nicht: kein Signal, kein
Siegverlust), `PREREG_opponent_disruption.md` (heuristischer Stoerer ueber die Farbzaehlung:
ABGELEHNT, zwei Konstruktionsfehler par.7.5) samt `_v2` (UEBERHOLT), `PREREG_denial_tiebreak.md`
(Denial-Tie-Break an der Wurzel gescheitert), `PREREG_task28_aggression.md` (lambda_aggr als
SPIEL-Knopf: Gegnerpunkte -6,16, p = 0,078, ohne Siegverlust). **Neu ist hier:** zufaellige Platten
auf EINER Seite fuer die ganze Partie, und der lambda-Blend als GEGNER in der Erzeugung, nicht als
Spielknopf.

## par.2 KLASSE W: Wuerfel-Kuppelplatten (FESTGELEGT 2026-10-01, Nutzer)

**Regeln, auf die sich die Klasse stuetzt** (`docs/engine_manual.md` Abschnitte 2, 3, 4A, gelesen
2026-10-01): 18 Platten, 3 offen in der Auslage, Rest verdeckter Stapel; Auslage waehrend der Runde
nicht nachgefuellt; Stapelzug kostet je Platte 1 Punkt, beliebig oft, man behaelt EINE der gezogenen,
der Rest geht unter den Stapel; Position und Rotation frei; Runden 1-4 je Spieler 2 Platten, Runde 5
keine; Punktestand faellt nie unter 0. In der Engine ist ein Plattenzug mehrstufig
(`engine/src/moves.rs:156-191`): `ChooseDomeSlot` (Auslage: Platte plus Platz) bzw.
`DrawStackPeek` x d, dann `ChooseDrawStackSlot` (Platte plus Platz), ggf. `ChooseReturnFirst`, dann
`ChooseDomeRotation`.

**Ablauf je Partie:**
* **Wuerfel-Seite:** eine Seite je Partie. VORSCHLAG: Spieler 0 oder 1 je Partie 50:50 aus dem
  Partie-RNG (sonst konfundiert die Seite mit dem Startspieler). Die andere Seite spielt normal.
* **Jeder Plattenzug der Wuerfel-Seite in Runde 1-4** wird gewuerfelt, VOR der Suche:
  1. Quelle Auslage/Stapel: Muenze 50:50 (VORSCHLAG). Ist die Auslage leer, Stapel; ist der Stapel
     leer, Auslage.
  2. Auslage: Platte gleichverteilt unter den offenen. Stapel: **Tiefe d gleichverteilt in
     1..max**, max = min(Obergrenze der Runde, Platten im Stapel); es werden d Platten gezogen
     (kostet d Punkte, Untergrenze 0), **behalten wird die d-te**, der Rest geht zurueck
     (Rueckgabe-Reihenfolge wie im Sockel, `return_order_random_p`).
     **Obergrenzen je Runde** (Nutzer 2026-10-01: *"Setz mir das maximum in runde 2 auf 7 und runde
     3 auf 3. Runde 4 hat sowieso nur noch 1 im stapel"*; zuvor *"wuerfel waehlt d in 1..max"*):
     Runde 1 keine (ganzer Stapel), Runde 2 **7**, Runde 3 **3**, Runde 4 ergibt sich aus dem
     Stapel. Begruendung des Nutzers fuer die Tiefe: *"Dafuer kennt sie aber auch den Stapel"* --
     die gezogenen Vorderseiten sind danach der Wuerfel-Seite bekannt (Rueckgabe-Reihenfolge nur ihr,
     `engine_manual.md` 4A).
  3. Rotation gleichverteilt in 0-3.
  4. **Den Platz waehlt die Suche mit 600 Sims**, unter festgehaltener Platte UND Rotation: an der
     Wurzel nur Plaetze fuer die gewuerfelte Platte, im Baum ist die Rotationsstufe auf den
     Wuerfelwert festgenagelt. So bewertet jede Simulation den Platz unter der Rotation, die
     tatsaechlich kommt. **Deterministisch: ohne Root-Noise, argmax** (par.3a F6). Alle anderen Zuege
     beider Seiten mit den Sockel-Sims (100).
* **Startplatte:** normal wie im Sockel (Nutzer: *"Nein, Start normal"*).
* **Records:** der erzwungene Plattenzug (alle seine Teilschritte) schreibt KEINEN Record. Alle
  anderen Zuege beider Seiten schreiben Records wie im Sockel, mit Policy- UND Wertziel. **Alle
  Wertziele bleiben** (Nutzer, auf die Frage nach Maskierung bis zur letzten erzwungenen Platte);
  die Verzerrung durch den schwaecheren Spieler wird gemessen (par.5 S3), nicht weggefiltert.
* **Record-Felder, VOR der Erzeugung** (Record-Feld-Regel): `dome_dice_side` (Spielerindex der
  Wuerfel-Seite) auf jedem Record einer W-Partie, `forced_domes_before` (Zahl der bisher erzwungenen
  Platten der Wuerfel-Seite) auf jedem Record. Damit bleibt eine spaetere Maskierung oder Gewichtung
  moeglich, ohne neu zu erzeugen. Additiv, Bestand byte-gleich.
* **Uebrige Sockel-Einstellung** wie die `policy`-Klasse des v34-Rezepts (`deviate_prob` 1,0,
  Root-Noise, `tie_mirror_p` 0,5, `start_slot_random_p` 0,15, E1, Runde 5 per Netz, seit v35 mit
  400 R5-Sims). ENTSCHIEDEN: die Weg-C-Abweichung bleibt in W (par.3a F5).

**Folgen, als HERLEITUNG vorab benannt (ungemessen):**
* Stapel zu Rundenbeginn (aus `engine_manual.md` 2/3/4A: 18 Platten, 2 Startplatten, Auslage zu
  jeder Runde auf 3 aufgefuellt, je Runde 1-4 vier Platten gelegt): Runde 1 **13**, Runde 2 **9**,
  Runde 3 **5**, Runde 4 **1**; innerhalb der Runde sinkt er um jede vom Stapel GELEGTE Platte
  (zurueckgelegte gehen wieder darunter). Erwartete Kosten eines Stapelzugs bei vollem Rundenstapel
  und d gleichverteilt, OHNE Deckel: Runde 1 7 Punkte (1..13), Runde 2 4 (1..7), Runde 3 2 (1..3),
  Runde 4 1. **KORREKTUR 2026-10-01 (Bauplan, am Code geprueft):** der Startstand ist 5
  (`engine/src/board.rs:286`, `engine_manual.md` Abschnitt 2), im Drafting gibt es keine Punkte, und
  die Zahlung ist auf den Stand gedeckelt (`board.rs:345-349`); der erste R1-Stapelzug kostet darum
  E[min(d, 5)] = 55/13, rund **4,2** Punkte, danach ist die Wuerfel-Seite in 9 von 13 Faellen auf 0.
  **Das gilt NUR fuer den ersten Stapelzug in Runde 1** (Nutzer 2026-10-01: *"ziehen kann mehr kosten
  als deine 5 punkte zu beginn. wenn du zb schon 12 punkte hast nach runde 2 kannst sehr schnell wieder
  runterkommen von den punkten wenn du zweimal tief ziehst"*). Allgemein kostet ein Zug
  min(d, Punktestand); nach den Wertungen ist der Stand hoeher, also greift der Deckel spaeter kaum.
  Beispiel (HERLEITUNG): 12 Punkte zu Beginn von Runde 2, Obergrenze 7: ein Zug kostet im Mittel 4,
  hoechstens 7, zwei tiefe Zuege koennen den Stand auf 0 bringen. S3 misst den tatsaechlichen
  Punkteverlauf der Wuerfel-Seite je Runde.
  Und es sind **hoechstens 7** Platzsuchen @600 je Partie, nicht 8: die letzte Platte hat nur noch
  einen freien Platz (HERLEITUNG aus 9 Plaetzen = Startplatte plus 8).
  **Bauplan:** `evaluations/asymmetric_selfplay_build_plan.md` (2026-10-01, 26 Edge Cases mit
  Pruefstellen, Fragen F1-F9, FS1-FS4, entschieden in par.3a). Bei 0 Punkten sind weitere Stapelzuege frei (`PREREG_score_clamp_incentive.md`
  par.11); die Verschiebung der Siegquote misst S3.
* Kosten je Partie: rund 8 Platzsuchen @600 auf einer Seite gegen rund 200 Entscheidungen je Partie
  (3.953 Zuege auf 20 Partien im Smoke, `PREREG_v34_window.md` par.7a): rund +20 % je Partie,
  ungemessen (S1).

## par.3 KLASSE S: stoerender Gegner (SKIZZE, nicht festgelegt)

* Baustein: `MOSAIC_AGGR_LAMBDA` (`engine/src/knob_registry.rs:69`), Blend aus eigenem Wert und
  vorhergesagten Gegnerpunkten; der `opp_points`-Kopf ist ein Ausgang von `v33-b01` (ONNX geprueft
  2026-10-01). Heute prozessweit (`net_mcts.rs:199-201`) -> fuer eine asymmetrische Partie braucht
  er ein **Spec-Feld je Seite** (Bau). Review #11 (`net_mcts.rs:3357-3359`, `opp_points` im
  gebuendelten Paar-Pfad verworfen) betrifft genau diesen Kopf und kommt in derselben Wheel-Runde.
* Den heuristischen Stoerer aus `PREREG_opponent_disruption.md` NICHT wiederbeleben (par.7.5 dort).
* **Records BEIDER Seiten** (Nutzer 2026-10-01: *"einerseits soll das netz lernen auf einen
  aggressiven gegner zu reagieren und andererseits selbst ein paar moves abschauen wo es sinn
  macht"*):
  * normale Seite: volle Records (Policy und Wert), das ist das "Reagieren".
  * Stoerer-Seite: Policy-Ziel NUR, wo sein Zug auch nach dem EIGENEN Wert (ohne lambda) fast
    gleichwertig ist: `own_q_gap = Q_own(bester Zug) - Q_own(gewaehlter Zug) <= eps`, sonst
    Policy-Gewicht 0. Das ist das "Abschauen, wo es Sinn macht", und genau die
    "bei ~gleichwertigen eigenen Zuegen"-Bedingung, die dem heuristischen Stoerer fehlte
    (`PREREG_opponent_disruption.md` par.7.5 Punkt 2). eps und die Wertziele der Stoerer-Seite:
    VORSCHLAG eps aus dem Pilot S4 (Anteil der Zuege, die durchkommen), Wertziele behalten und in
    S3/S4 messen, analog zur Klasse W.
  * **Bau-Voraussetzung, am Code gelesen 2026-10-01:** jeder Knoten speichert Rohwert und
    `opp_points_forecast` schon (`net_mcts.rs:2815-2835`), der lambda-Blend passiert aber am Blatt
    (`blended_leaf_win_prob`, `net_mcts.rs:3021-3023`) und hochgereicht wird EIN gemischtes Q. Fuer
    `own_q_gap` braucht jede Wurzelkante einen zweiten Akkumulator fuer den ungemischten Wert;
    kein zusaetzlicher Netzaufruf (HERLEITUNG, Aufwand beim Bau pruefen).
  * Record-Felder VOR der Erzeugung: `aggr_side` (Spielerindex des Stoerers) auf jedem Record,
    `own_q_gap` auf jedem Record der Stoerer-Seite. Die eps-Schwelle wirkt dann im Training
    (`corpus_dataset.py`), nicht in der Erzeugung: eps bleibt ohne Neuerzeugung verschiebbar.
* Offen: lambda (Pilot S4), eps, Anteil im Fenster.

## par.3a ENTSCHIEDEN 2026-10-03: die offenen Fragen F1-F9 und FS1-FS4 (Nutzer, einzeln abgefragt)

Fragen und Varianten: `evaluations/asymmetric_selfplay_build_plan.md` Abschnitt 12. Vorgelegt mit je einer
Empfehlung; gewaehlt:

| Frage | Entscheid |
| --- | --- |
| F1 Zeitpunkt des Plattenzugs | die normale Suche (100 Sims) entscheidet WANN; waehlt sie eine Plattenaktion, uebernimmt der Wuerfel WELCHE (Empfehlung) |
| F2 Ausloeser-Record | behalten mit Policy- und Wertziel, markiert als `dice_trigger` (wie Weg C) (Empfehlung) |
| F3 Stapeltiefe | ueber den ganzen Stapel, d in 1..max mit Deckel 7 (R2) / 3 (R3); Zuege in eigene bekannte Bloecke zulassen und in S3 zaehlen (Empfehlung) |
| F4 Rueckgabe-Reihenfolge im Wuerfelzug | Streumuenze p = 0,81 wie im Sockel VOR der Platzsuche werfen und festnageln, sonst Suche (Empfehlung) |
| F5 Weg C in den W-Klassen | behalten (`deviate_prob` 1,0), damit `policy` und `policy-dice` sich nur in der Behinderung unterscheiden (Empfehlung) |
| **F6 Platzsuche @600** | **deterministisch: ohne Root-Noise, argmax (staerkster Platz)** -- ABWEICHEND von der Empfehlung (Noise wie im Sockel) |
| F7 Quelle Wuerfel gegen Suche | jeder Plattenzug der Suche (Auslage oder Stapel) loest aus und gilt als `dice_trigger` (Empfehlung) |
| F8 Ausflug plus Wuerfel | Kombination verbieten; Ausfluege bleiben in der G-G-Klasse `value-excursion` (Empfehlung) |
| F9 Kosten der Wuerfelzuege | Record-Feld `dome_dice_cost` = [verlangte Tiefe, bezahlte Punkte] am ersten Record nach jedem erzwungenen Zug, VOR der Erzeugung gebaut (Empfehlung) |
| FS1 Gegnermodell des Stoerers | G spielt normal: nur der Stoerer bewertet gemischt, G-Knoten bleiben beim reinen Siegwert, kein Nullsummen-Baum (Empfehlung) |
| FS2 w fuer die lambda-Reihe | fest w = 0,1; Pilot S4 variiert nur lambda (z. B. 0 / 0,5 / 1 / 2) (Empfehlung) |
| FS3 bester eigener Zug fuer `own_q_gap` | nur Wurzelkinder mit mindestens so vielen Besuchen wie die letzte Halving-Stufe; Schwelle beim Bau festlegen und mitschreiben (Empfehlung) |
| FS4 Wirkort des Stoerers | nur Drafting; Startsetzung und Tiling unvermischt (Startsetzung braucht beim Bau eine Ausnahme) (Empfehlung) |

Damit ist der Bau der Klassen W und S vollstaendig spezifiziert; offen bleiben nur die Werte aus den
Sonden (lambda und eps aus S4, Zusammensetzung nach S1-S4).

## par.4 ZUSAMMENSETZUNG DES FENSTERS (Nutzer-Plan, endgueltig nach den Sonden)

**Nutzer 2026-10-01:** *"ich denk da an 4000 spiele im sockel sowie 2000 'normale' spiele im sockel.
dann haben wir insgesamt 6000 spiele und die g-1 und g-2 fallen raus, da diese sowieso zu aehnlich
spielen."* Auf die Frage nach Stoerer, Weg C und Ausflug: *"die exakte komposition koennen wir uns
noch ueberlegen, je nachdem was uns die sonden sagen"*.

| Klasse | Partien | Policy-Ziel | Stand |
| --- | --- | --- | --- |
| W (Wuerfel, Sockel-Einstellung) | 4.000 | ja (ausser erzwungene Plattenzuege, die keinen Record schreiben) | geplant |
| Sockel normal | 2.000 | ja | geplant |
| G-1 / G-2 (Traeger aelterer Generationen) | 0 | -- | faellt weg (Nutzer) |
| S, Weg C, Ausflug | offen | -- | nach den Sonden |

**ABGELOEST durch den Nutzer-Vorschlag vom selben Tag** (*"vorschlag fuer asymetric play ab v34+:
sockel: 2000 g vs g, 2000 g vs kuppelklasse, 2000 kuppelklasse vs. stoerklasse, 2000 g vs.
stoerklasse; schwarm wie gehabt mit 4000 wegc und 4000 ausflug"*). Zielzusammensetzung, endgueltig
nach den Sonden S1-S4 (par.5):

| Klasse (Arbeitsname) | Paarung | Partien | Policy-Ziel | Wertziel |
| --- | --- | --- | --- | --- |
| `policy` | G gegen G | 2.000 | beide Seiten | alle |
| `policy-dice` | G gegen W | 2.000 | G voll; W ausser den erzwungenen Plattenzuegen (kein Record) | alle |
| ~~`policy-dice-aggr`~~ | ~~W gegen S~~ | **0, GESTRICHEN 2026-10-03** (par.4a) | -- | -- |
| `policy-aggr` | G gegen S | 2.000 | G voll; S nur bei `own_q_gap <= eps` | alle |
| `value-deviate` (bis v34 `value-wegc`) | G gegen G, Weg C | 4.000 | nein | alle |
| `value-excursion` | G gegen G, Ausflug | 4.000 | nein | alle |
| G-1 / G-2 | -- | 0 | -- | faellt weg (Nutzer, oben) |

Annahmen, als VORSCHLAG markiert: die behinderte Seite (W bzw. S) sitzt je Partie 50:50 auf
Spieler 0 oder 1; in `policy-dice-aggr` traegt jede Seite ihre eigene Regel (Wuerfel bzw.
lambda_aggr), beide Record-Regeln gelten nebeneinander; Seeds und Klassennamen beim Bau.
**Kosten (HERLEITUNG, ungemessen; ueberholt durch par.4a: 14.000 Partien, davon der Schwarm schon erzeugt):** 16.000 statt 12.000 Partien; mit dem v34-Satz (rund 8,8 h fuer
12.000, `PREREG_v34_window.md` par.8a) rund 11,7 h, dazu die Platzsuchen @600 der Wuerfel-Seite in
4.000 Partien (rund +20 % je solcher Partie, par.2) und der zweite Akkumulator des Stoerers (kein
zusaetzlicher Netzaufruf): grob 12 h. S1 liefert die gemessene Zahl. **Kosten vom Nutzer
akzeptiert** (2026-10-01: *"damit kann ich leben, dann sind wir wieder auf dem stand vor der
einsparung"*; v33-Erzeugung ohne E1: 12,99 h, `PREREG_v34_window.md` par.8).
**Gewicht im Fenster (HERLEITUNG):** in 6.000 der 16.000 Partien spielt mindestens eine behinderte
Seite; das Policy-Material der normalen Suche stammt aus `policy` (beide Seiten) und den G-Seiten
von `policy-dice` / `policy-aggr`. Die Wertziele dieser 6.000 Partien bleiben alle (Nutzer, par.2);
ihre Verzerrung misst S3, getrennt je Paarung.

### par.4a NUTZER-ENTSCHEID 2026-10-03: W gegen S gestrichen, G-G-Sockel bleibt bei 2.000

Auf die Einschaetzung des Koordinators (W gegen S: keine Seite spielt normal, Policy- und Wertziele
beider Seiten verzerrt; Vorschlag streichen; zweiter Vorschlag G-G-Sockel auf 4.000 fuer einen
Kontrollarm): *"W gegen s koennen wir streichen. Den g-g sockel will ich nicht wirklich vergroessern.
Der ist als Basis ok, aber wirklich viel neues sieht das Netz hier nicht."* **Damit:** Sockel 3 x 2.000
(G-G, G-W, G-S), Schwarm 2 x 4.000 (schon erzeugt, `PREREG_v35_window.md` par.9), zusammen 14.000
Partien; behinderte Seite in 4.000 der 14.000. **Folge, benannt:** ohne Kontrollarm (Fenster ohne
Asym-Klassen bei gleichem Schwarm) ist ein v35-Ergebnis dem Paket zuzuschreiben (Generator, R5 @400,
Asym-Klassen), nicht den Asym-Klassen allein. Die Seitenwahl fuer W gegen S bleibt im Code (schadet
nicht), wird aber in keinem Rezept benutzt.

Stuetze fuer den Wegfall von G-1/G-2 (am Bestand): die Fensterarme b02-b04 waren ununterscheidbar,
Menge und Alter des Value-Materials kein Hebel (`PREREG_v33_window.md` par.6d, STATUS RICHTUNG).

## par.5 SONDEN vor der Festlegung (Leseregeln REGISTRIERT 2026-10-03 vor dem Bau-Ende, Koordinator)

Nutzer 2026-10-03: *"die sonden werden uns dann zeigen ob es in die richtige richtung geht"*. Gemeinsamer
Aufbau: Generator `v34-b01`, Rezept der v35-Erzeugung (100 Sims, R5 per Netz @400, Spiegelknopf, E1,
Weg C), je Klasse 100 Partien (S4: je lambda-Stufe), exklusiv, Seeds 20261720 ff. (20261700 ist in
`PREREG_minimal_strength_core.md` als Anker-Seed-Basis belegt). Sechs Standard-Kennzahlen je Seite in
jedem Bericht. Die Werte der Leseregeln sind Setzungen des Koordinators; der Nutzer kann sie vor dem
Lauf aendern.

* **S1 Kosten:** `policy` gegen `policy-dice`, gleiche Seeds (20261720), Wanduhr je Partie aus dem
  Manifest, dazu je Partie die Zahl der 600er-Platzsuchen und der Rueckgabesuchen. **Leseregel:**
  Mehrkosten je W-Partie <= +25 % -> Plan haelt; darueber -> Nutzer-Entscheid ueber die Sims der
  Platzsuche (HERLEITUNG-Erwartung +15 bis +20 %, Bauplan Abschnitt 10).
* **S2 Andere Stellungen?** Policy-KL `KL(Ziel || Prior)` (`tools/probes/targeted_branching_pretest.py`,
  Prior aus dem Generator) an allen Drafting-Entscheiden beider Seiten NACH der ersten erzwungenen
  Platte gegen dieselben Runden im Sockel, getrennt nach Seite (W / G) und Runde; dazu aus der
  `[dome_dice]`-Zeile Quellenanteile, Tiefenverteilung je Runde, Anteil Ziehungen aus eigenem bzw.
  fremdem Block. **Leseregel:** Median-KL der W-Partien ueber dem des Sockels mit Block-Bootstrap-CI
  (Block Datei) ueber 0 -> "andere Stellungen" fuer diese Seite; ueberdeckt das CI 0 -> nicht
  nachweisbar anders, berichtet, die Zusammensetzung entscheidet der Nutzer.
* **S3 Wert-Verzerrung:** Siegquote, Punkte, Marge der W-Seite (gegen 50 %); Brier des Generator-Kopfs
  auf W-Partie-Records gegen Sockel-Records, getrennt nach Seite und nach `forced_domes_before`;
  gezahlte Wuerfel-Punkte je Partie (aus `dome_dice_cost`, bei Stand > 0 und bei 0). **ERWEITERT
  2026-10-03 (Nutzer: *"S3 kannst erweitern"*): Kalibrierungsversatz je Seite** = mittlere Vorhersage
  des Generator-Kopfs P(Sieg der Seite am Zug) minus tatsaechliche Siegrate dieser Seite, getrennt fuer
  W- und G-Seite und nach `forced_domes_before`. Grund (HERLEITUNG): der Zustand verraet nicht, dass eine
  Seite kuenftig gewuerfelte Platten legt; ein Wertziel aus diesem Regime ist dann systematisch
  verschoben (W zu pessimistisch, G zu optimistisch), was der Brier allein nicht von "schwierigeren
  Stellungen" trennt. Dasselbe fuer `policy-aggr` (S- und G-Seite). **Leseregeln:** (a) Brier der
  W-Partien mehr als 0,01 ueber dem Sockel ODER (b) Versatz einer Seite mit Block-Bootstrap-CI ohne 0
  und |Versatz| > 0,03 -> Wertziele dieser Seite als verzerrt markiert, Maske (nach Seite bzw.
  `forced_domes_before`) als Vorlage an den Nutzer; sonst bleiben alle Wertziele (Nutzer-Entscheid par.2).
* **S4 Stoerer-Pilot:** `policy-aggr` mit w = 0,1 fest (FS2), lambda in {0; 0,5; 1; 2}, je Stufe 100
  Partien, Seeds 20261724-27. Berichtet je lambda: Punkte und Siegquote beider Seiten, Verteilung von
  `own_q_gap`. **Leseregel:** gewaehlt wird das GROESSTE lambda, bei dem die Siegquote des Stoerers
  nicht mehr als 5 Prozentpunkte unter der bei lambda = 0 liegt UND die Punkte von G sinken; eps =
  das 50-%-Quantil von `own_q_gap` der Stoerer-Zuege bei diesem lambda (die Haelfte der Stoerer-Zuege
  liefert ein Policy-Ziel). Senkt keine Stufe die Punkte von G, ist der Stoerer in dieser Form
  wirkungslos: berichtet, Nutzer-Entscheid.

## par.6 BAU (nach der v34-Erzeugung, in der Wheel-Runde mit E4 und dem Review-Rest)

Engine: Wuerfel-Seite und Wuerfel in der Self-Play-Schleife (Partie-RNG bzw. eigener Strom nach
`PREREG_search_rng_split.md`), Wurzel-Beschraenkung auf die Plaetze der gewuerfelten Platte,
festgenagelte Rotation im Baum, Platzsuche mit eigener Sim-Zahl, Record-Unterdrueckung fuer den
erzwungenen Zug, die zwei Record-Felder, Knopf mit Default aus (byte-identisch), Rezept-Schluessel.
Danach Anker-Invarianz, Netz-Paritaets-Fixture, Smoke. Fuer S: Spec-Feld je Seite fuer lambda_aggr.
Neue Mischstellen: keine (die Wuerfel nehmen dem Spieler nichts, was er rechtmaessig hat; sie
ERSETZEN seine Wahl), Eintrag in `docs/architecture_reference.md` darum nicht noetig, beim Bau
pruefen.
