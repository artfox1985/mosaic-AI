<!-- STATUS: OFFEN | Frage: Erzeugt asymmetrisches Self-Play (Wuerfel, Stoerer, Exploiter, fremder Stil) Stellungen, die das Spiel gegen sich selbst nicht erreicht, und traegt ein Fenster daraus? | Beleg: NEIN in allen fuenf Formen (W Vollform par.5a, W Eroeffnung par.5d1 und zustandsbasiert par.5d2a, Stoerer par.5c3, Exploiter 46 % par.7a, v32 par.7b1). TRAEGT stattdessen: Q-Stichentscheid Modus 2 75 % gegen Bestand (par.5e3), und @400 mit Modus 2 verdoppelt die KL bei gleichen Punkten und Spalten (par.8b1). Offen: v35-Sockel-Entscheid (Nutzer). -->

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

## par.3b ENTSCHIEDEN 2026-10-03: der Suchbaum kennt die Wuerfel-Regel (Zufallsknoten)

Nutzer, nachdem der Koordinator gemeldet hatte, dass der kleinere Aktionsraum nur in der Platzsuche @600
wirkt (die keinen Record schreibt), waehrend alle anderen Suchen kuenftige W-Platten frei waehlen
(Bauplan 4.5): *"Der suchbaum sollte aber wissen dass die zukuenftigen w Platten auch gewuerfelt sind.
Sonst ist die gesamte Idee mit der suchtiefe nur schwach umgesetzt."* Grundidee der Klasse W laut
Nutzer: *"durch die Vorauswahl der kuppelplatten den aktionsraum klein zu machen und dann tiefer in
den suchbaum einzutauchen."* Auf die Vorlage gewaehlt (je Empfehlung):

* **Im Baum** fallen an jedem Knoten, an dem die W-Seite zieht (Runde 1-4, kein Teilzug offen, kein
  Pin), alle Plattenaktionen (`ChooseDomeSlot` jeder Auslage-Platte und Platz, `DrawStackPeek`) zu EINER
  Aktion "Platte legen" zusammen (Prior = Summe der Einzelpriors). Darunter ein **Zufallsknoten, der je
  Besuch neu wuerfelt** (dieselben Regeln wie der echte Wuerfel, `roll_dome_dice`, auf der
  determinisierten Welt der Suche); gleiche Ausgaenge teilen sich einen Kind-Knoten, der Wert ist der
  Mittelwert ueber die Besuche. Unter dem Ausgang setzt der Pin den Zustand fest, der Baum waehlt nur
  noch den Platz.
* **Beide Seiten** kennen die Regel: auch die Suchen von G modellieren die Platten von W als Zufall.
* **Policy-Ziel der W-Seite:** die Besuche auf "Platte legen" werden auf die einzelnen Plattenaktionen
  nach dem Prior des Netzes verteilt (keine Vorliebe fuer eine bestimmte Platte, nur die Haeufigkeit).
* Die echte Partie bleibt wie gebaut: waehlt die Suche "Platte legen", wuerfelt der echte Wuerfel aus
  seinem eigenen Strom (den der Baum nicht kennt), Platzsuche @600 deterministisch.
* Knopf AUS (und Partien ohne W) byte-gleich. Aufwand HERLEITUNG rund 1,5 Tage Code.

### par.3b1 BEFUND nach dem Bau: der Zufallsknoten macht den Baum zunaechst FLACHER (2026-10-03)

`#[ignore]`-Test `dice_tree_depth_report` (self_play.rs, Agent-Bau, vom Koordinator nachgefahren, Zahlen
identisch). **Grundmenge** n = 8 Plattenentscheide der W-Seite EINER Testpartie (Champion, Seed 4711),
je Entscheid eine W-Suche ohne und mit Zufallsknoten, gleiche Sims, Such-Seed 7. **Einheiten**
Wurzelkanten je Entscheid; Knotentiefe ueber alle Baumknoten; Halbzugtiefe = Spielerwechsel auf dem Pfad.

| Mittel ueber 8 Entscheide | 100 Sims | 400 Sims |
| --- | --- | --- |
| Wurzelkanten | 30,4 -> 21,0 | 30,4 -> 21,0 |
| mittlere Knotentiefe | 3,78 -> 3,68 | 4,50 -> 4,66 |
| mittlere Halbzugtiefe | 1,98 -> 1,19 | 2,51 -> 1,55 |
| max. Halbzugtiefe | 4,62 -> 3,12 | 6,88 -> 4,25 |

HERLEITUNG: je Besuch neu gewuerfelt erzeugt fast jeder Besuch einen neuen Ausgang (R1 bis 13 Tiefen x 4
Rotationen plus Auslage; bei 400 Sims in R1 24-28 Ausgaenge), jeder mit Netzaufruf; dazu belegt ein
W-Plattenzug drei Baumebenen (Zufall, Platz, Rotation) fuer einen Halbzug. In R4 (wenige Ausgaenge)
waechst die mittlere Knotentiefe dagegen (4,23 -> 7,07 bei 400 Sims). **Nutzer-Entscheid 2026-10-03:**
Progressive Widening am Zufallsknoten (hoechstens ceil(sqrt(Besuche)) verschiedene Ausgaenge, sonst
Wiederbesuch eines vorhandenen nach Besuchen) UND erzwungene Ein-Aktions-Schritte unter dem Pin ohne
eigenen Knoten/Netzaufruf anwenden; danach dieselbe Messung, erst dann Wheel und Sonden.

### par.3d ENTSCHIEDEN 2026-10-03: im Baum EINE zugewiesene Platte je Plattenentscheid (statt Widening)

Nutzer, nachdem par.3b1 mit Widening ceil(sqrt(N)) gebaut war: *"mir kommt vor du machst es zu
aufwendig/komplex. statt den ueblichen moeglichen kuppelplattenentscheidungen hab ich dann nur noch die
positionswahl. eigentlich so als wuerd ich als spieler ein platte zugewiesen bekommen deren rotation fix
ist. ich kann dann nur noch die position waehlen. im maximalfall (runde 1) hab ich 8
aktionsmoeglichkeiten."* Umgesetzt als Widening-Exponent 0 (`DICE_OUTCOME_WIDENING_EXPONENT`,
net_mcts.rs): der Zufallsknoten hat genau EINEN Ausgang (beim ersten Betreten gewuerfelt, danach immer
derselbe), darunter nur noch die Positionen der zugewiesenen Platte; die erzwungenen Ein-Aktions-Schritte
(Rotation, gewuerfelter Rueckgabekopf) laufen ohne Knoten. Manifest `dome_dice_tree_rule` =
`chance_node_single_assigned_plate_forced_pin_steps_policy_split_by_prior`.

**Messung** (`dice_tree_depth_report`, Koordinator, 2026-10-03). **Grundmenge** n = 16 Plattenentscheide der
W-Seite aus zwei Testpartien (Champion, Seeds 4711 und 4712, je 8), je Entscheid eine W-Suche, Such-Seed 7,
gleiche Sims. **Einheit** Halbzugtiefe = Spielerwechsel auf dem Pfad, gemittelt ueber alle Baumknoten bzw.
Maximum, Mittel ueber die 16 Entscheide.

| Variante | mittl. Halbzugtiefe 100 / 400 Sims | max. Halbzugtiefe 100 / 400 Sims | max. Knotentiefe 400 Sims |
| --- | --- | --- | --- |
| A ohne Wuerfel-Modell im Baum | 2,16 / 2,77 | 5,25 / 7,12 | 10,44 |
| B Zufallsknoten je Besuch (par.3b) | 1,25 / 1,73 | 3,31 / 4,31 | 9,50 |
| C Widening ceil(sqrt(N)) + Ein-Aktions-Schritte (par.3b1) | 2,05 / 2,60 | 4,75 / 6,12 | 10,94 |
| **D eine zugewiesene Platte + Ein-Aktions-Schritte (par.3d)** | **2,58 / 3,36** | **5,75 / 6,94** | **12,00** |

D ist die einzige Variante, die TIEFER als A sucht (mittlere Halbzugtiefe +0,42 bzw. +0,59), und die
einfachste. Preis, benannt (HERLEITUNG): der Wert von "Platte legen" haengt in EINER Suche an EINEM Wurf
(verrauscht); ueber viele Suchen mittelt er sich. Keine Signifikanz gerechnet (n = 16 aus zwei Partien);
die Wirkung im Spiel zeigen die Sonden. Lib-Tests 827 gruen, `--no-run` gruen.

## par.3c ENTSCHIEDEN 2026-10-03: die Platzwahl der gewuerfelten Platte schreibt einen Record

Nutzer auf die Frage, ob die Platzsuche @600 einen bedingten Policy-Record schreiben soll: *"Kannst sie
mitschreiben. Ist ja eine vorgegebene Platte und das Netz entscheidet wohin."* Das aendert par.2
("der erzwungene Plattenzug schreibt KEINEN Record") fuer genau EINEN Teilschritt: die Platzwahl.
Quelle, Platte bzw. Tiefe, Rotation und Rueckgabe bleiben ohne Record.

* **Record:** Zustand unmittelbar vor der Platzwahl (Ziehungen schon ausgefuehrt, Pin gesetzt), Policy-Ziel
  = Ergebnis der Platzsuche @600 (Besuche bzw. das Ziel, das die Erzeugung sonst schreibt) ueber die
  Plaetze der Wuerfel-Platte, Wertziel wie jeder andere Record. Markiert mit `dice_place: true`.
* **Pflicht-Maske:** der Pin steht NICHT in `state_to_json`; ohne Zusatz saehe das Training alle legalen
  Plattenaktionen als Alternativen und lernte, die gewuerfelte Platte zu bevorzugen. Der Record traegt
  darum die erlaubten Aktions-IDs (`dice_place_ids`), und der Policy-Verlust laeuft im Training NUR ueber
  diese IDs (Maske in `engine/py/corpus_dataset.py`, im Cache-Schluessel, wenn sie das Ergebnis aendert).
* Record-Feld-Regel: gebaut VOR der Erzeugung; Knopf AUS byte-gleich. Bau direkt nach dem Zufallsknoten
  (par.3b), beides beruehrt `self_play.rs`.

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

### par.5a ERGEBNISSE S1-S4 (2026-10-03 18:24-18:54 Laeufe, exklusiv; Auswertung `tools/probes/asym_probe_report.py`)

Wheel `59f32a16...` (Anker-Invarianz gruen), Rezept `models/v35_probes.recipe.json`, je Klasse 100 Partien,
Generator `v34-b01`, Artefakt `evaluations/artifacts/asym_probes_s1_s4.json`. Rezept-Waechter in allen sechs
Klassen gruen, alle Exit 0.

**S1 Kosten** (Grundmenge 100 Partien je Klasse, Einheit s Wanduhr je Partie, 11 Threads): `policy` 2,898,
`policy-dice` 3,108 -> **+7,2 %**, Leseregel: Plan haelt (<= +25 %). Je W-Partie 8,0 erzwungene Platten und
7,0 Platzwahl-Records.

**S2 Andere Stellungen?** (Grundmenge Drafting-Records R1-4 mit Ziel >= 2 IDs, ohne Platzwahl-Records; W-Klasse
nach der ersten erzwungenen Platte; Einheit KL(Ziel || Prior), Median, CI Block-Bootstrap ueber Dateien):
Sockel 0,316 (n 11.999); **W-Seite 0,234 (n 4.383), Differenz -0,082 [-0,148; -0,033]**; G-Seite 0,313 (n 5.156),
Differenz -0,002 [-0,078; +0,061]. Lesart: G sieht keine nachweisbar anderen Stellungen. Die W-Seite liegt
NIEDRIGER, das ist aber zum Teil KONSTRUIERT (HERLEITUNG): ihr Policy-Ziel verteilt die Masse der
Plattenkante nach dem Prior (`push_dice_split`, net_mcts.rs:6391), INNERHALB der Kante ist das Ziel also
proportional zum Prior und traegt null KL bei; nur die Kantenmasse selbst kann abweichen.
Die Registrierung fragte nur nach "hoeher"; "niedriger" ist kein Befund fuer "andere Stellungen". Die
Auswertung beschriftete den Fall zunaechst als "nicht nachweisbar anders"; korrigiert, Lesart heisst jetzt "niedriger".

**S3 Wert-Verzerrung** (Grundmenge 100 Partien bzw. Drafting-Records der Klasse `policy-dice`): W gewinnt **25 %
[16; 35]**, Punkte 35,4 gegen 51,5, Marge -16,1; gezahlte Wuerfel-Punkte **8,15 je Partie**. Brier W 0,171,
G 0,182, Sockel 0,223 (nicht ueber dem Sockel, Regel a greift nicht). **Kalibrierungsversatz** (Vorhersage
P(Sieg) minus Siegrate): **W +0,109 [+0,030; +0,184]**, **G -0,136 [-0,208; -0,053]** -> **Regel b greift fuer
beide Seiten.** Nach `forced_domes_before` faellt der Versatz der W-Seite von +0,237 (0 Platten, n 654) ueber
+0,145 (2) und +0,070 (4) auf +0,025 (6) und -0,031 (7); G spiegelbildlich von -0,291 (0) auf -0,041 (6). Das
liest sich als verborgene Behinderung (HERLEITUNG, nicht getestet): frueh in der Partie sieht der Zustand
normal aus, der Ausgang ist es nicht; mit jeder gezahlten Platte wird sie sichtbarer und der Versatz schrumpft. **Folge nach Leseregel: Maske als Vorlage an den Nutzer.**

**S4 Stoerer-Pilot** (Grundmenge je lambda 100 Partien, w = 0,1; Einheit je Partie bzw. Record):

| lambda | Siegquote S [CI] | Punkte S / G | Versatz S / G | own_q_gap Median (Anteil <= 0) | s je Partie |
| --- | --- | --- | --- | --- | --- |
| 0 | 0,57 [0,48; 0,67] | 48,27 / 47,42 | -0,059 / +0,051 | 0,0 (63,6 %) | 2,865 |
| 0,5 | 0,52 [0,44; 0,62] | 47,39 / 46,73 | -0,012 / +0,005 | 0,0 (63,7 %) | 2,925 |
| 1 | 0,48 [0,39; 0,59] | 46,50 / 46,79 | +0,021 / -0,032 | 0,0 (63,5 %) | 2,897 |
| 2 | 0,50 [0,43; 0,58] | 44,16 / 45,81 | -0,002 / -0,021 | 0,0 (63,3 %) | 3,003 |

Leseregel (groesstes lambda mit S-Siegquote >= lambda-0-Wert - 5 Prozentpunkte UND weniger G-Punkten): **lambda =
0,5**, eps = Median own_q_gap = **0,0** (63,7 % der S-Zuege liefern dann ein Policy-Ziel). **Einschraenkung:** die
G-Punkte fallen bei lambda 0,5 nur um 0,69 gegen lambda 0, ohne CI; bei einer Streuung von rund 15 Punkten je
Partie (HERLEITUNG) ist das Rauschen. Der Stoerer kostet sich selbst mehr als G (lambda 2: S -4,1, G -1,6).
In dieser Form ist er schwach.
Laufzeit der Auswertung 125,9 s.

### par.5b NUTZER-ENTSCHEID 2026-10-03 nach den Sonden: neue Quellenregel fuer W (REGISTRIERT vor dem Lauf)

Nutzer zu W (25 % Siege, par.5a): *"die kuppelplatten vom stapel werden eigentlich bereits ueber einen
anderen knopf gestreut und bedient. mach die muenze fuer die platten wahl von [0-3] mit auslage 1, 2, 3 und
stapel."* Umgesetzt (`self_play.rs` `roll_dome_dice`, `DOME_DICE_SOURCE_RULE`): die Quelle ist
gleichverteilt ueber die belegten Auslageplaetze und die OBERSTE Stapelplatte (Tiefe 1, 1 Punkt). Ein leerer
Auslageplatz (die Auslage wird erst zur naechsten Runde aufgefuellt, game.rs:1469) faellt weg, als wuerde
der Vierer-Wuerfel dort neu geworfen (Koordinator-Lesart, dem Nutzer gemeldet). Die Tiefen-Obergrenzen
R2 7 / R3 3 aus par.2 und die Muenze entfallen; die Rueckgabe-Muenze (F4) faellt mit Tiefe 1 nie. Der Baum
nutzt dieselbe Funktion (par.3d), er kennt die neue Regel also ohne eigene Aenderung.

**Sonde (vor dem Lauf registriert):** Klasse `policy-dice-src4` in `models/v35_probes.recipe.json`, 100
Partien, gleicher Seed 20261720 wie `policy-dice` (par.5a), Auswertung
`tools/probes/asym_probe_report.py --dice-class policy-dice-src4 --skip-s4`. Berichtet werden S1 (Kosten,
gegen denselben `policy`-Lauf), S2 und S3 (Siegquote, Punkte, Marge, gezahlte Wuerfelpunkte, Versatz je
Seite und je `forced_domes_before`) im Vergleich zu par.5a. Es gibt KEINE Schwelle: der Lauf beschreibt, der
Nutzer entscheidet ueber Maske und Zusammensetzung. Vorher Anker-Invarianz auf dem neuen Wheel.

#### par.5b1 ERGEBNIS W mit neuer Quellenregel (2026-10-03 22:43-22:51, Artefakt `evaluations/artifacts/asym_probe_w_src4.json`)

Vorher Lib-Suite 827 gruen, Wheel neu, Anker-Drift und -Konservierung GRUEN (`anchor_v2_*_20261003_src4.json`).
Je 100 Partien, gleicher Seed wie par.5a, Vergleich gegen `policy-dice` (par.5a):

| Groesse (Grundmenge 100 Partien bzw. Drafting-Records) | alte Regel (par.5a) | neue Regel |
| --- | --- | --- |
| W-Siegquote [CI] | 0,25 [0,16; 0,35] | **0,23 [0,17; 0,28]** |
| Punkte W / G | 35,38 / 51,50 | 38,85 / 52,92 |
| gezahlte Wuerfelpunkte je Partie | 8,15 | **3,51** |
| Versatz W / G | +0,109 / -0,136 | **+0,165 / -0,184** (beide CI ohne 0) |
| Versatz W bei 0 erzwungenen Platten | +0,237 | +0,264 |
| KL W gegen Sockel (Median-Differenz) | -0,082 | -0,114 [-0,151; -0,080] |
| s je Partie (Zuege gleich: 19.207 / 19.151) | 3,108 | 4,134 (+42,7 % gegen `policy`) |

Lesart: die neue Regel senkt die gezahlten Punkte um 4,6, W gewinnt aber NICHT haeufiger. Der Nachteil
sitzt also in der Zufallswahl der Platte (und des Zeitpunkts der Plattenzuege), nicht in den Stapelkosten
(HERLEITUNG). Die Wertverzerrung wird groesser; sie ist schon VOR der ersten erzwungenen Platte da
(+0,264), also eine verborgene Behinderung, die das Netz an der Stellung nicht sehen kann.
**Die Laufzeit ist UNGESICHERT:** waehrend des Laufs bearbeitete ein Agent Quelltexte (Engine-Bau Stoerer
B). In `engine/target` gibt es keine Compile-Spur im Laufzeitfenster, Python-Last ist aber nicht
ausschliessbar. Gleiche Zugzahl bei +33 % Wanduhr gegen die alte Regel; Wiederholung unter sauberen
Bedingungen in der S4b-Kette.

### par.5c NUTZER-ENTSCHEID 2026-10-03: Stoerer neu als lexikografische Wahl an der Wurzel ("B"), REGISTRIERT vor Bau und Lauf

**Befund, der dazu fuehrte (Koordinator, am Code und an der Prereg-Historie gelesen):** S benutzte den Blend
aus Task #28 (`opp_aware_points_utility`, net_mcts.rs:2104) mit w = 0,1 und lambda in {0; 0,5; 1; 2} -- exakt
dem Raster, fuer das `PREREG_task28_aggression.md` (Statuszeile, Z. 112-117) schon "kein nutzbarer
Denial-Effekt bei w=0,1" registriert hat; groessere w waren dort laut Z. 62f "toedlich" (v9b). S4 konnte
also nur wirkungslos oder ruinoes ausgehen; das haette vor dem Bau gegen die Historie geprueft werden
muessen. Mechanik (HERLEITUNG aus dem Code, nicht gemessen): der Gegnerterm sitzt auf der tanh-Skala der
Endpunkte (Ziel `tanh(opp/50)`, corpus_dataset.py:1546) und wird halbiert (net_mcts.rs:2107); bei rund 48
Punkten ist ein Gegnerpunkt im Blattwert etwa 0,00045 * lambda wert, gegen q75 des `own_q_gap` von 0,007
(par.5a).

**Konstruktion B** (Nutzer: *"ja bau B"*): S sucht normal, ohne Blend. An der Wurzel gilt unter den
Halving-Ueberlebenden (Regel `AGGR_OWN_Q_GAP_N_MIN_RULE`) mit eigenem Q >= Q_best - eps derjenige Zug, dessen
Teilbaum dem Gegner im Mittel die wenigsten Endpunkte prognostiziert (Gegnerpunkte-Akkumulator je Knoten,
Perspektive fest der Stoerer). eps ist das ausdrueckliche Budget an Siegwahrscheinlichkeit, das S fuers
Stoeren opfern darf; kein lambda, kein w. Knopf `MOSAIC_AGGR_SIDE_EPS` (Kombination mit
`MOSAIC_AGGR_SIDE_LAMBDA` verboten). Record-Felder `aggr_opp_drop_pts` (prognostizierte Gegnerpunkte des
eigenen Bestzugs minus des gewaehlten, >= 0) und `aggr_switched`. Die Policy-Maske `own_q_gap <= eps` ist per
Konstruktion erfuellt; das Policy-Ziel bleibt die Suche.

**Sonde S4b (vor dem Lauf registriert):** Klassen `policy-aggr-e01/e02/e04` (eps 0,01 / 0,02 / 0,04), je 100
Partien, Seeds 20261730-32, sonst wie die S4-Klassen. Bezug: dieselben Partien-Kennzahlen der Klasse
`policy` (par.5a, G gegen G) und die lambda-Arme aus par.5a. Berichtet je eps: Siegquote S [CI], Punkte S
und G, Marge, Anteil `aggr_switched`, mittleres `aggr_opp_drop_pts`, Versatz je Seite, s je Partie.
**Leseregel:** gewaehlt wird das groesste eps mit S-Siegquote >= 0,45 UND G-Punkten unter dem Mittel je
Seite in `policy`; erfuellt das kein eps, oder liegt die G-Senkung unter 2 Punkten, geht die Frage an den
Nutzer (B dann ebenfalls zu schwach). Mehrkosten > +10 % gegen `policy` je Partie: Nutzer-Entscheid.

#### par.5c1 ERGEBNIS S4b (2026-10-03 23:18-23:35, Artefakt `evaluations/artifacts/asym_probe_s4b.json`) und Laufzeit-Wiederholung W

Vorher Lib-Suite 836 gruen, Wheel neu, Anker-Drift und -Konservierung GRUEN (`anchor_v2_*_20261003_s4b.json`).
Je eps 100 Partien; Bezug `policy` (par.5a): 46,85 Punkte je Seite.

| eps | Siegquote S [CI] | Punkte S / G | Marge S | Anteil `aggr_switched` | mittl. `aggr_opp_drop_pts` | Versatz S / G | s je Partie |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0,01 | 0,81 [0,74; 0,88] | 56,51 / 39,07 | +17,44 | 0,113 | 0,07 | -0,227 / +0,227 | 3,345 |
| 0,02 | 0,77 [0,66; 0,88] | 56,94 / 39,03 | +17,91 | 0,158 | 0,10 | -0,187 / +0,177 | 3,022 |
| 0,04 | 0,78 [0,69; 0,87] | 54,50 / 41,11 | +13,39 | 0,177 | 0,12 | -0,200 / +0,182 | 3,488 |

(Grundmenge `aggr_switched`/`aggr_opp_drop_pts`: rund 5.900 Drafting-Records der S-Seite je eps; Einheit
Anteil bzw. prognostizierte Gegnerpunkte je Zug.) Die Leseregel waehlt formal eps = 0,04. **Das Ergebnis ist
aber KEIN Stoerer-Effekt, die Konstruktion ist konfundiert:** S stoert kaum (11-18 % der Zuege, im Mittel
0,07-0,12 prognostizierte Gegnerpunkte je Zug), gewinnt aber 77-81 % und holt rund 10 Punkte MEHR als der
Sockel; der Abstand haengt nicht am eps. `disruptor_pick` misst gegen den Zug mit dem hoechsten EIGENEN Q
unter den Halving-Ueberlebenden (net_mcts.rs:7896), nicht gegen den Zug, den die Erzeugung sonst spielt
(Index aus `argmax_index` der Besuche, self_play.rs:7562, Gleichstand = ERSTER Eintrag, self_play.rs:559;
`tau_argmax_from_move` 1 im v35-Rezept, models/v35.recipe.json:15). S spielt dadurch "Q-gierig unter den
Ueberlebenden", G die normale Wahl (HERLEITUNG; wie oft die Ueberlebenden bei den Besuchen gleichauf liegen,
ist NICHT gemessen). Folgerung: B muss gegen den normal gespielten Zug messen (siehe Vorschlag an den Nutzer);
Nebenbefund zur Zugwahl der Erzeugung geht als eigene Frage an den Nutzer.

**Laufzeit-Wiederholung W (par.5b1), saubere Bedingungen** (`evaluations/artifacts/asym_probe_w_src4_rep.json`,
data/probe_asym_rep): `policy` 2,965 s je Partie, `policy-dice-src4` 3,918 s -> **+32,1 %**. Partien
identisch zum ersten Lauf (Siegquote, Punkte, Versatz gleich, also deterministisch); der erste Lauf
(+42,7 %) lag durch Nebenlast rund 10 Prozentpunkte zu hoch. Die Mehrkosten gegen die alte Regel (3,108 s)
sind damit echt; Ursache nicht untersucht.

#### par.5c2 NUTZER-ENTSCHEID 2026-10-03: B repariert (Bezugszug = Bestands-Wahl), S4b neu (REGISTRIERT vor dem Lauf)

Nutzer: *"ja, repariere B und registrier den Nebenbefund"*. `RootOwnStats::disruptor_pick(eps, base)`
(net_mcts.rs): Bezugszug `base` ist der Zug, den die Bestands-Zugwahl gezogen hat (self_play.rs,
`net_drafting_policy_with_own_gap`, `stats[idx]`). Kandidaten: Halving-Ueberlebende mit
`Q_own(base) - eps <= Q_own <= Q_own(base)`; der Stoerer weicht nur NACH UNTEN ab, nie zu einem
eigen-besseren Zug. Gleichstand der Gegnerpunkte -> der Bezugszug. `aggr_switched` und `aggr_opp_drop_pts`
messen jetzt gegen den Bezugszug. Damit ist eps = 0 bis auf exakte Q-Gleichstaende die Bestands-Wahl, also
die eingebaute Kontrolle. Nebenfolge: das Policy-Ziel des Stoerers ist in Modus B die unvermischte Suche
(w = 0), die `own_q_gap`-Maske (`MOSAIC_AGGR_OWN_Q_EPS`) ist fuer Modus B nicht noetig (HERLEITUNG: das
Ziel ist dieselbe Groesse wie bei G).

**S4b-Wiederholung:** dieselben drei Klassen `policy-aggr-e01/e02/e04` mit NEUEN Versionsnamen (die alten
Dateien bleiben als Beleg der Konfundierung), gleiche Seeds, Leseregel par.5c unveraendert. Zusaetzlich
berichtet: Siegquote S gegen 0,50 (muss jetzt UNTER oder bei 0,50 liegen; liegt sie bei eps 0,01 deutlich
darueber, ist B weiter konfundiert).

#### par.5e NEBENBEFUND (OFFEN, Nutzer: registrieren): Stichentscheid der argmax-Zugwahl in der Erzeugung

Aus par.5c1: "Q-gierig unter den Halving-Ueberlebenden" gewann in Erzeugungsbedingungen 77-81 % gegen die
Bestands-Wahl (300 Partien, drei eps-Stufen; die Stoerer-Wirkung war dabei vernachlaessigbar, 0,07-0,12
prognostizierte Gegnerpunkte je Zug). Bestands-Wahl der Erzeugung ab `tau_argmax_from_move` (v35-Rezept: 1,
models/v35.recipe.json:15): `argmax_index` der Besuche, Gleichstand = ERSTER Eintrag in Kinderreihenfolge
(self_play.rs:559/7562), ohne Q. Der `deterministic`-Zweig (Arena) bricht Gleichstaende dagegen nach Q
(self_play.rs, "Fund 2 (B2)"). Offene Fragen, NICHTS davon gemessen:
1. Wie oft liegen die Ueberlebenden der letzten Halving-Stufe bei den Besuchen gleichauf (Grundmenge
   Drafting-Entscheide der Erzeugung mit > 1 Aktion)?
2. Ist der erste Eintrag gewollte Exploration (die Kinderreihenfolge traegt das Gumbel-Rauschen), oder
   fehlt der Q-Stichentscheid (Gumbel-MuZero waehlt argmax g + logit + sigma(q) unter den Ueberlebenden)?
3. Wirkung: ein Arm "Q-Stichentscheid im tau-Zweig" gegen den Bestand, gleiche Seeds, als Sonde (Siegquote,
   Punkte, Spaltenbau) und, falls gross, als Erzeugungsfrage fuer das naechste Fenster.
Vorschlag, keine Entscheidung: Frage 1 zuerst (billig, aus einem Instrumentierungs-Test), dann 3.

##### par.5e1 MESSPLAN par.5e (REGISTRIERT 2026-10-04 vor Bau und Messung; Nutzer: *"par.5e zuerst messen"*)

**Frage 1 (Gleichstand):** `#[ignore]`-Test `tie_frequency_report` (self_play.rs, Muster `dice_tree_depth_report`):
Zustaende = alle Drafting-Records mit `root_q` und mehr als einer legalen Aktion aus 20 Partien des Champions
`v34-b01` (Erzeugungsbedingungen: 100 Sims, Root-Noise, Gumbel, `SearchConfig::from_env()`; Partie-Seeds
4711 ff.). Je Zustand EINE Suche @100, Such-Seed 7; aus `stats` (Aktion, Besuche, Q) werden gezaehlt:
(a) Anteil der Entscheide, bei denen mindestens zwei Wurzelkinder die MAXIMALE Besuchszahl teilen;
(b) Anteil, bei dem die Bestands-Wahl (`argmax_index`, erster Eintrag) von der Wahl "Besuche, dann Q"
(`deterministic`-Zweig) abweicht; (c) Anteil, bei dem sie von "hoechstes Q unter den Halving-Ueberlebenden"
(`visits >= n_min`) abweicht, dazu Mittel und Median der Q-Differenz (Gewinnwahrscheinlichkeit) in den Faellen
von (c); (d) alles getrennt nach Runde. **Grundmenge** Drafting-Entscheide mit > 1 Aktion, **Einheit** Anteil
je Entscheid bzw. Q-Differenz in Gewinnwahrscheinlichkeit. Keine Schwelle: Frage 1 beschreibt.

**Frage 3 (Wirkung), GEAENDERT 00:30 vor dem Lauf:** Spec-Feld je Seite `tau_tiebreak_q` (0 = Bestand,
byte-gleich; 1 = im tau-Zweig Gleichstand der Besuche nach Q brechen, wie der `deterministic`-Zweig; 2 =
unter den Halving-Ueberlebenden das hoechste Q, Gumbel-MuZero-Form). Die urspruenglich geplante gepaarte
Arena ist UNTAUGLICH: der Arena-Pfad (`net_arena_choose_action`, self_play.rs:4975 ->
`net_search_drafting_action`, :4994) laeuft nie durch den tau-Zweig der Erzeugung, beide Arme waeren
zuggleich (Agent-Befund, vom Koordinator an den Zeilen geprueft). Stattdessen dieselbe Anordnung, in der der
Befund par.5c1 entstand: **asymmetrisches Self-Play**, eine Seite je Partie (50:50 aus einem Hash des Partie-Seeds wie
`dome_dice_side`, ohne Ziehung aus dem Partie-RNG; Knopf `MOSAIC_TAU_TIEBREAK_SIDE=1`, Record-Feld `tiebreak_side`) spielt mit `tau_tiebreak_q` = Modus, die andere
mit 0; Klassen `policy-tb1` und `policy-tb2` in `models/v35_probes2.recipe.json`, je **200 Partien**,
Erzeugungs-Rezept (100 Sims, R5 @400, Weg C, Spiegelknopf), Seeds 20261740/41. Berichtet: Siegquote der
Knopf-Seite gegen 0,50 mit Block-Bootstrap-CI (Block Datei), Punkte und Marge beider Seiten, sechs
Standard-Kennzahlen, Kosten je Partie. **Leseregel:** CI der Siegquote ganz ueber 0,50 UND Punktmarge > 0 ->
der Modus geht als Vorschlag in das v35-Sockel-Rezept (Nutzer-Entscheid am Morgen, weil es die Zugwahl des
Generators aendert; bei zwei bestandenen Modi der mit der hoeheren Siegquote); CI mit 0,50 -> Bestand bleibt,
berichtet; CI ganz unter 0,50 -> Bestand bleibt, par.5c1 war dann etwas anderes (zu klaeren). Eingebaute
Kontrolle: Modus 0 auf beiden Seiten ist byte-gleich der Klasse `policy` (Anker-Invarianz prueft den Bestand).

##### par.5e2 ERGEBNIS Frage 1 (2026-10-04 00:38-00:40, `tie_frequency_report`, Kette `tools/night_v35_prep_chain1.sh`; Anker-Drift und -Konservierung auf dem neuen Wheel GRUEN)

20 Partien `v34-b01` in Erzeugungsbedingungen (100 Sims, Root-Noise, `MOSAIC_TAU_ARGMAX_FROM_MOVE=1`, Weg C;
ABWEICHUNG: Runde 5 hier @100 statt @400, weil `r5_net_sims` keinen Env-Knopf hat), je Entscheid eine Nachsuche
@100 mit Such-Seed 7. **Grundmenge** n = 2.833 Drafting-Entscheide mit `root_q` und > 1 Aktion, **Einheit** Anteil
je Entscheid bzw. Q-Differenz in Gewinnwahrscheinlichkeit:

| Runde | n | (a) Gleichstand auf max. Besuchen | (b) Bestand != Besuche-dann-Q | (c) Bestand != bestes Q der Ueberlebenden | Q-Diff. (c) Mittel / Median |
| --- | --- | --- | --- | --- | --- |
| 1 | 601 | 0,117 | 0,087 | 0,276 | 0,014 / 0,008 |
| 2 | 605 | 0,091 | 0,061 | 0,222 | 0,023 / 0,011 |
| 3 | 634 | 0,148 | 0,099 | 0,259 | 0,019 / 0,011 |
| 4 | 581 | 0,172 | 0,121 | 0,219 | 0,025 / 0,008 |
| 5 (@100) | 412 | 0,240 | 0,153 | 0,286 | 0,033 / 0,005 |
| **Summe** | **2.833** | **0,148** | **0,101** | **0,250** | **0,022 / 0,009** |

Lesart: in rund jedem siebten Entscheid liegen Wurzelkinder bei den Besuchen gleichauf, und in jedem zehnten
spielt die Erzeugung dadurch einen anderen Zug als "Besuche, dann Q". Jeder vierte Zug weicht vom besten Q der
Halving-Ueberlebenden ab, im Median um 0,9 Prozentpunkte Gewinnwahrscheinlichkeit (Mittel 2,2). Ob das Staerke
kostet, misst Frage 3 (Klassen `policy-tb1`/`-tb2`, laufen in derselben Kette).

##### par.5e3 ERGEBNIS Frage 3 (2026-10-04 00:51-01:13, Klassen `policy-tb1`/`policy-tb2`, Artefakte `evaluations/artifacts/tiebreak_side_tb1.json`, `_tb2.json`)

Je Modus 200 Partien, eine Seite je Partie mit dem Modus, die Gegenseite Bestand (Modus 0), sonst Erzeugungs-
Rezept @100. **Grundmenge** 200 Partien je Klasse (alle mit eindeutigem `tiebreak_side`), **Einheit** Siegquote je
Partie (CI Block-Bootstrap ueber Dateien), Punkte und Marge je Partie, Kennzahlen je Seite ueber 200 Seiten:

| Groesse | Modus 1 (Besuche, dann Q) | Modus 2 (bestes Q der Ueberlebenden) |
| --- | --- | --- |
| Siegquote Knopf-Seite [CI] | **0,745 [0,690; 0,800]** | **0,755 [0,715; 0,795]** |
| Punkte Knopf-Seite / Bestand-Seite, Marge | 58,6 / 43,1, +15,5 | 59,7 / 41,9, +17,8 |
| volle Spalten je Seite Knopf / Bestand | 1,04 / 0,79 | 1,09 / 0,85 |
| Strafleiste je Seite Knopf / Bestand | 4,3 / 6,5 | 4,1 / 7,3 |
| Versatz Wertkopf Knopf / Bestand | -0,184 / +0,170 (CI ohne 0) | -0,161 / +0,149 (CI ohne 0) |
| s je Partie (11 Threads) | 2,974 | 2,813 |

**Leseregel: BEIDE Modi bestehen** (CI ganz ueber 0,50, Marge > 0); nach Regel geht der Modus mit der hoeheren
Siegquote als Vorschlag ins v35-Sockel-Rezept: **Modus 2** (die Intervalle ueberlappen fast vollstaendig; Modus 2
ist zugleich die Gumbel-MuZero-Form der Endauswahl). Lesart: der Bestand der Erzeugung (argmax Besuche, Gleichstand
= erster Eintrag, par.5e) verschenkt gegen dieselbe Suche mit Q-Stichentscheid drei von vier Partien und 15 bis 18
Punkte; die Verengung von Tor 1 (par.7 Anlass) hat damit einen benannten Mitverursacher: der Generator spielte seit
`tau_argmax_from_move` 1 unter seiner eigenen Suche. Das Policy-ZIEL war davon nie betroffen (completed-Q), nur die
Trajektorie und damit die Wertziele. Der Versatz des Wertkopfs (Knopf-Seite -0,16: der Kopf unterschaetzt den
Spieler mit korrektem Stichentscheid) passt dazu: der Kopf ist auf Trajektorien des Bestands geeicht.
**Nutzer-Entscheid am Morgen:** Modus 2 (oder 1) in das v35-Sockel-Rezept und in die Schwarm-Klassen (die
`value-*`-Klassen laufen ebenfalls mit `tau_argmax_from_move` 1 und sind betroffen; der schon erzeugte v35-Schwarm
traegt den Bestand). **Annahme fuer die Nacht (Koordinator):** die Exploiter-Zyklen (par.7) laufen mit Modus 2 auf
BEIDEN Seiten, weil ein Exploiter gegen den Bestand eine Schwaeche ausnutzen wuerde, die der v35-Sockel voraus-
sichtlich nicht mehr hat; faellt der Entscheid anders, sind die Zyklen zu wiederholen (rund 3,5 h).
**Rueckwaerts-Pruefung (Konsumenten von `tau_argmax_from_move` 1, Grep 01:30):** `models/v34.recipe.json` und
`models/v35.recipe.json` (der schon erzeugte v35-Schwarm traegt den Bestand; v34 ebenso, erklaert nichts
rueckwirkend falsch, weil Policy-Ziele unberuehrt sind); `PREREG_difficulty_levels.md` Z. 1029 (eine Stufen-Spec
mit `tau_argmax_from_move` wuerde den Bestands-Stichentscheid erben; der GUI-Pfad selbst ist nicht betroffen, er
spielt ueber `select_final_root_child` mit Q); `PREREG_search_path_remeasurements.md` M3/3-V (Sampling gegen argmax,
nicht widerlegt: beide Arme dort hatten denselben Stichentscheid).

### par.5d NUTZER-ENTSCHEID 2026-10-03: W als Eroeffnungs-Wuerfel (REGISTRIERT vor Bau und Lauf)

Anlass (par.5a/par.5b1): W verliert 75-77 %, die Wertziele beider Seiten sind verzerrt, und G sieht keine
nachweisbar anderen Stellungen (KL-Differenz -0,013, CI mit 0). Der Versatz der W-Seite faellt mit
`forced_domes_before` von +0,264 auf etwa 0 nach der letzten Wuerfelplatte: verzerrt ist der Wert, solange
KUENFTIGE Wuerfelplatten ausstehen, die die Stellung nicht zeigt (HERLEITUNG aus der Reihe).

**Konstruktion:** nur EINE Seite wuerfelt (Nutzer: beide Seiten waere *"wieder symmetrisches spiel"*), und
nur bis einschliesslich Runde R_dice; danach spielen beide normal. Die gewuerfelten Platten liegen danach
sichtbar auf dem Brett, der Ausgang ist ab dort aus der Stellung erklaerbar. Alles andere aus par.3d/par.3c/
par.5b bleibt (zugewiesene Platte, Positionswahl, Baum kennt die Regel nur bis R_dice). Records:
Wertziele BEIDER Seiten aus der Wuerfelphase (Runde <= R_dice) maskiert; Policy-Ziele und
Positionswahl-Records bleiben.

**Sonde S5 (vor dem Lauf registriert):** zwei Arme `policy-dice-r1` (R_dice = 1) und `policy-dice-r2`
(R_dice = 2), je 100 Partien, Seed wie `policy-dice`. Leseregel je Arm:
1. Versatz je Seite ueber Drafting-Records NACH der Wuerfelphase: |Versatz| <= 0,03 (oder CI mit 0). Sonst
   ist die Maske nicht ausreichend, Nutzer-Entscheid.
2. KL der G-Seite nach der Wuerfelphase gegen den Sockel (Median-Differenz, Block-Bootstrap): CI ganz ueber 0
   heisst "andere Stellungen". Sonst traegt W keine neuen Stellungen, Nutzer-Entscheid ueber W.
3. Siegquote, Punkte, gezahlte Wuerfelpunkte, Kosten je Partie werden berichtet, ohne Schwelle.

#### par.5d1 ERGEBNIS S5 (2026-10-04 00:04-00:25, Kette `tools/asym_s5_s4b2_chain.sh`, Artefakte `evaluations/artifacts/asym_probe_s5_r1.json`, `_r2.json`)

Vorher Lib-Suite gruen, Wheel neu, Anker-Drift und -Konservierung GRUEN (`anchor_v2_*_20261003_s5.json`). Je Arm
100 Partien, Seed 20261720, Bezug `policy` (par.5a; Grundmengen und Einheiten wie par.5a; Versatz und KL NUR
ueber Drafting-Records NACH der Wuerfelphase, `--post-dice-phase`):

| Groesse | `policy-dice-r1` (R_dice 1) | `policy-dice-r2` (R_dice 1-2) |
| --- | --- | --- |
| Siegquote W [CI] | **0,51 [0,40; 0,62]** | 0,34 [0,29; 0,40] |
| Punkte W / G, Marge | 45,08 / 45,07, +0,01 | 40,28 / 48,96, -8,68 |
| gezahlte Wuerfelpunkte je Partie | 0,93 | 1,97 |
| Mehrkosten je Partie gegen `policy` | +9,2 % | +10,7 % |
| Versatz W / G [CI] | -0,035 [-0,121; +0,053] / +0,017 [-0,066; +0,107] | +0,017 [-0,043; +0,076] / -0,022 [-0,082; +0,042] |
| KL-Differenz G gegen Sockel [CI] (n) | +0,030 [-0,012; +0,071] (4.497) | +0,021 [-0,032; +0,077] (2.906) |
| KL-Differenz W gegen Sockel [CI] (n) | +0,029 [-0,007; +0,070] (4.392) | +0,019 [-0,041; +0,075] (2.952) |

**Leseregel 1 (Versatz) HAELT in beiden Armen** (alle vier CI enthalten 0): die Wertmaske der Wuerfelphase
reicht, nach der Phase ist der Wert unverzerrt. **Leseregel 2 (G sieht andere Stellungen) HAELT NICHT:** beide
CI enthalten 0. Die Punktschaetzer liegen in beiden Armen und auf beiden Seiten ueber dem Sockel (+0,02 bis
+0,03 auf 0,316, also rund 6-10 % hoehere KL), bei n = 100 Partien aber nicht aufloesbar. R1 ist ausgeglichen
(51 %) und kostet 9 %; R2 benachteiligt W (34 %). **Nach Leseregel: Nutzer-Entscheid ueber W** (Vorschlag des
Koordinators: wenn W, dann R1; der Nachweis "andere Stellungen" braeuchte rund 400 Partien, HERLEITUNG aus der
CI-Breite 0,08 bei 100).

#### par.5c3 ERGEBNIS S4b neu, Stoerer B repariert (2026-10-04 00:09-00:26, Artefakt `evaluations/artifacts/asym_probe_s4b2.json`)

Je eps 100 Partien, Seeds 20261730-32, Bezug `policy` 46,855 Punkte je Seite (par.5a):

| eps | Siegquote S [CI] | Punkte S / G | Marge S | Anteil `aggr_switched` | mittl. `aggr_opp_drop_pts` | Versatz S / G | s je Partie |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0,01 | 0,47 [0,40; 0,55] | 44,26 / 44,82 | -0,56 | 0,057 | 0,05 | +0,016 / -0,044 | 2,973 |
| 0,02 | 0,47 [0,42; 0,50] | 44,86 / 46,39 | -1,53 | 0,084 | 0,07 | +0,027 / -0,038 | 2,842 |
| 0,04 | 0,49 [0,39; 0,59] | 45,28 / 45,29 | -0,01 | 0,106 | 0,08 | +0,015 / -0,040 | 2,930 |

(Grundmenge `aggr_switched`: rund 5.900 Drafting-Records der S-Seite je eps; Versatz-CI enthalten alle 0.)
**Die Konfundierung aus par.5c1 ist weg:** S liegt bei 47-49 %, nicht mehr bei 77-81 %. **B ist aber zu
schwach:** die Leseregel par.5c waehlt formal eps 0,04 (S >= 0,45, G 45,29 < 46,855), die G-Senkung betraegt
dort 1,57 Punkte (< 2) und bei eps 0,01 2,03 bei gleichzeitig -2,6 Punkten fuer S selbst; S weicht nur in 6-11 %
der Zuege ab, um 0,05-0,08 prognostizierte Gegnerpunkte je Zug (rund 0,3 Punkte je Partie, HERLEITUNG), und
beide Seiten liegen 1-2 Punkte unter dem `policy`-Bezug anderer Seeds (Streuung rund 15 Punkte je Partie, SE des
Mittels rund 1,5, also Rauschen). **Verdikt: Stoerer als Suchknopf (Blend UND lexikografisch) traegt nicht;
Linie geschlossen, Ersatz ist der trainierte Exploiter (par.7).** Nutzer-Entscheid 2026-10-04 00:00 (Exploiter
statt Stoerer) damit bestaetigt.

#### par.5d2 MESSPLAN "andere Stellungen" zustandsbasiert (REGISTRIERT 2026-10-04 vor der Auswertung; Nutzer: *"gib die auswertung an einen agenten"*)

Zweifel am Instrument von S2/S5: KL(Ziel || Prior) misst die Korrektur des Priors je Entscheid, nicht die Neuheit
der Stellung. Zustandsbasiertes Mass, OHNE neuen Lauf, aus den vorhandenen Dateien in `data/probe_asym`:
* **Grundmengen:** `policy` (100 Partien, Bezug), `policy-dice-r1` (100), `policy-dice-r2` (100), zur Einordnung
  `policy-dice-src4` (W Vollform) und `policy-s400`. Einheit je Mass unten.
* **M1 Platzierungen Runde 1:** Verteilung der in Runde 1 gelegten Kuppelplatten je Seite (Platten-ID, Rotation,
  Platz) aus den Record-Zustaenden am Ende von Runde 1; Jensen-Shannon-Distanz jeder Klasse und Seite gegen den
  Sockel (beide Seiten gepoolt), Bootstrap-CI ueber Partien; dazu Anzahl distinkter (Platte, Rotation, Platz)-
  Tripel und Entropie.
* **M2 Brettzustaende zu Beginn von Runde 2 und Runde 3:** Anteil der Zustaende (Belegung aller Kuppelfelder je
  Spieler, kanonisiert) einer Klasse, die im Sockel NICHT vorkommen, und umgekehrt; Zahl distinkter Zustaende je
  100 Partien.
* **M3 Entscheidungen der G-Seite nach der Wuerfelphase:** Anteil der G-Entscheide (R2-4), deren Zustand im
  Sockel nie auftritt; mittlere Prior-Entropie und mittleres `root_q` je Runde gegen den Sockel (ist G in den
  neuen Stellungen unsicherer?).
**Leseregel (PRAEZISIERT vor dem Lauf, Agent-Einwand: eine JS-Distanz endlicher Stichproben ist per
Konstruktion > 0, "CI ueber 0" greift immer):** M1 traegt, wenn die JS-Distanz der Klasse ueber dem 95-%-Quantil
der Permutations-Nullverteilung liegt (Partien zufaellig auf Klasse/Sockel verteilt, 1.000 Permutationen) UND ueber
dem Rauschbezug Sockel 1-5 gegen 6-10; M2 traegt, wenn der Anteil sockelfremder Bretter den Rauschbezug (Sockel-
Haelfte gegen Haelfte, gleich grosse Bezugsmenge) mit CI ohne Ueberlappung uebersteigt; Feinheit `plates`
(Platz, Platten-ID, Rotation) ist die massgebliche, `slots` und `full` Einordnung. M3 zeigt, ob G dort anders
ENTSCHEIDET. Tragen M1/M2, aber nicht KL, ist S2/S5 das falsche Instrument und die Leseregel 2 von par.5d wird fuer
kuenftige W-Varianten (par.5d3: Platzwahl mit eps-Spielraum, Platte aus dem Prior mit Temperatur, 400 Partien)
durch M1-M3 ersetzt. Werkzeug `tools/probes/state_novelty_probe.py`, Artefakt
`evaluations/artifacts/state_novelty_s5.json` mit `laufzeit`-Block.

##### par.5d2a ERGEBNIS zustandsbasiert (2026-10-04 10:40, `tools/probes/state_novelty_probe.py`, Artefakt `evaluations/artifacts/state_novelty_s5.json`, 50 Dateien, 107 s)

**M1, Platzierungen Runde 1** (Grundmenge 2 Platten je Partie und Seite, n = 200 je Klasse/Seite gegen 400 im Sockel;
Einheit JS-Distanz log2 der Tripel Platte/Rotation/Platz; Null: 1.000 Permutationen ueber Partie-Seiten):

| Zeile | distinkte Tripel | JS gegen Sockel | Permutations-Null Mittel / q95 / p | traegt? |
| --- | --- | --- | --- | --- |
| `policy-dice-r1`, W-Seite | 118 | **0,645** | 0,554 / 0,588 / 0,001 | ja, aber erzwungen (die Wuerfel setzen die R1-Platten) |
| `policy-dice-r1`, G-Seite | 100 | **0,479** | 0,510 / 0,545 / 0,916 | **nein**, G liegt sogar UNTER der Null |
| `policy-s400`, beide | 164 | 0,473 | 0,473 / 0,503 / 0,485 | nein |
| Rauschbezug Sockel 1-5 gegen 6-10 | 114 | 0,560 | 0,578 / 0,621 / 0,761 | |

r2 und src4 sind in Runde 1 mit r1 IDENTISCH (gleicher Seed 20261720, Runde 1 laeuft in allen drei Armen gleich),
also kein unabhaengiger Beleg. Alle 100 Partien jeder Klasse haben dieselbe Auslage wie die Sockel-Partie gleichen
Index: die Arme sind gepaart, die Permutations-Null ist fuer G darum eher zu weit, und G's R1-Platzierungen liegen
naeher am Sockel als zwei Sockel-Haelften aneinander (HERLEITUNG: gleiche Auslage zieht G zum Sockel hin).

**M2, Bretter zu Beginn von Runde 2 und 3:** in der massgeblichen Feinheit `plates` ist das Mass GESAETTIGT (100 von
100 Brettern je Klasse distinkt, Rauschbezug Haelfte gegen Haelfte schon 1,000; R3 ueberall 1,000); in `slots`
uebersteigt keine Zeile den Rauschbezug ohne CI-Ueberlappung (R2 r1/G 0,07 [0,04; 0,16] gegen Rauschbezug 0,05
[0,01; 0,15]). **M3, G-Entscheide R2-4 nach der Wuerfelphase** (r1 n = 4.817): Anteil sockelfremder Zustaende in
`slots` 0,122 gegen Rauschbezug 0,153 / 0,136; Prior-Entropie der G-Seite nicht verschieden (R2 -0,017 [-0,046;
+0,010] nat); `root_q` der G-Seite HOEHER (r1 R2 +0,061 [+0,025; +0,098]; r2 R3 +0,129, R4 +0,161): G ist nicht
unsicherer, sondern vorn (passt zum Punktrueckstand von W, nicht zu neuen Stellungen). Bootstrap-Perzentil-CI der
JS-Distanz sind nach oben verzerrt (Ziehen mit Zuruecklegen verkleinert den Traeger), deshalb zaehlt die
Permutations-q95.

**Verdikt:** auch zustandsbasiert sieht G in W-Partien keine nachweisbar anderen Stellungen; M1 traegt nur fuer W und
dort per Konstruktion. Das Instrument KL (S2/S5) ist damit nicht widerlegt, die Lesart par.5d1 bleibt. Fuer eine
kuenftige W-Variante (par.5d3, Platzwahl mit eps-Spielraum, Platte aus dem Prior) muesste die Messung gepaart
(Klasse gegen Sockel je gleichem Spielindex) und mit groeberer Feinheit (Platten-ID-Menge, Plaetze je Platte) gebaut
werden, sonst saettigt sie bei 100 Partien. **Nach vier Formen (W Vollform, W Eroeffnung, Stoerer, Exploiter, dazu
v32 als Gegner) hat kein asymmetrischer Gegner fuer G messbar andere Stellungen erzeugt; der Hebel der Nacht liegt
in der Zugwahl (par.5e3) und der Suchtiefe mit Modus 2 (par.8b1).**

#### par.5d3 W, naechste Form (NUTZER 2026-10-04 *"kein W und kein exploiter ist keine option ... optimieren bis die zwei ihre gewuenschte wirkung entfalten"*; REGISTRIERT vor Bau und Lauf)

**Diagnose aus par.5d1/5d2a:** die 600er-Platzsuche legt jede gewuerfelte Platte an den normalsten Platz und
"repariert" die Stellung; die Wuerfel aendern nur W's zwei R1-Platten, G's Runde 1 bleibt wie im Sockel; danach
laufen die Partien zusammen. Zwei Hebel, zusammen als EINE Variante `policy-dice-v2`:
1. **Platzwahl mit eps-Spielraum:** unter den Plaetzen der gewuerfelten Platte, deren Q hoechstens
   `MOSAIC_DOME_DICE_PLACE_EPS` (Default 0 = Bestand, byte-gleich; Sonde 0,02) unter dem besten liegt, wird
   gleichverteilt aus dem Wuerfelstrom gezogen. Das ist ein ausdrueckliches Budget an Siegwahrscheinlichkeit je
   Platzierung, per Konstruktion kein Handicap ueber eps, aber Streuung genau an der Stelle, die heute alles
   zusammenzieht. Record-Feld `dice_place_eps_pick` (Zahl der Kandidaten im Fenster) am Platzwahl-Record.
2. **Platte aus G's Prior mit Temperatur statt gleichverteilt:** `MOSAIC_DOME_DICE_SOURCE_RULE` bekommt die
   Variante `prior_tempered` (Knopf `MOSAIC_DOME_DICE_PRIOR_TEMP`, Default 0 = Bestand gleichverteilt; Sonde
   T = 2): die Wahl unter Auslageplaetzen und oberster Stapelplatte folgt softmax(log prior / T) ueber die
   Plattenaktionen des Netzes am Zustand (Prior der Plattenkante je Platte summiert). Plausible, aber andere
   Platten; damit kann die Wuerfelphase auf Runde 1-2 ausgedehnt werden, ohne den 34-%-Einbruch von R2 (par.5d1).
Alles andere wie par.5d (eine Seite, Wertmaske der Wuerfelphase, Baum kennt die Regel).

**Sonde (vor dem Lauf registriert, Rezept `models/v35_probes2.recipe.json`, je Klasse 400 Partien statt 100, weil
die KL-Differenz von 0,03 bei 100 Partien nicht aufloesbar war; Seeds 20261760 ff., Modus 2 beide Seiten):**
* `policy-m2-400g`: G gegen G, 400 Partien (Bezug; derselbe Seed wie die W-Klassen fuer die gepaarte Auswertung).
* `policy-dice-v2-r1`: eps 0,02, T 2, R_dice 1. `policy-dice-v2-r2`: dasselbe, R_dice 2.
**Berichtet und Leseregeln:** (a) Siegquote W [CI] und Marge (R2-Arm muss ueber 0,42 liegen, sonst ist die
Temperatur zu hoch); (b) Versatz je Seite nach der Wuerfelphase (|Versatz| <= 0,03 oder CI mit 0, wie par.5d);
(c) Median-KL der G-Seite nach der Wuerfelphase gegen den Bezug, Block-Bootstrap, bei 400 Partien CI-Breite rund
0,04; (d) NEU, gepaart: fuer jede W-Partie und ihre Bezugspartie gleichen Index der erste Halbzug, an dem G's
Zustand abweicht, und der Anteil der G-Entscheide in R2-4, deren (eigenes Brett, Gegnerbrett) in Feinheit
`slots` im Bezug fehlt, gegen den Rauschbezug Bezug-Haelften (`state_novelty_probe.py`, gepaart erweitert);
(e) sechs Standard-Kennzahlen je Seite, Kosten. **W traegt**, wenn (b) haelt UND mindestens eines von (c) (CI
ganz ueber 0) oder (d) (ueber dem Rauschbezug ohne Ueberlappung) greift; dann geht der bestandene Arm mit 2.000
Partien in den v35-Sockel-Vorschlag. Greift keines, berichtet der Koordinator die naechste Stellschraube (eps,
T, beide Seiten) als Vorlage; W wird nicht gestrichen (Nutzer).

## par.6 BAU (nach der v34-Erzeugung, in der Wheel-Runde mit E4 und dem Review-Rest)

Engine: Wuerfel-Seite und Wuerfel in der Self-Play-Schleife (Partie-RNG bzw. eigener Strom nach
`PREREG_search_rng_split.md`), Wurzel-Beschraenkung auf die Plaetze der gewuerfelten Platte,
festgenagelte Rotation im Baum, Platzsuche mit eigener Sim-Zahl, Record-Unterdrueckung fuer den
erzwungenen Zug, die zwei Record-Felder, Knopf mit Default aus (byte-identisch), Rezept-Schluessel.
Danach Anker-Invarianz, Netz-Paritaets-Fixture, Smoke. Fuer S: Spec-Feld je Seite fuer lambda_aggr.
Neue Mischstellen: keine (die Wuerfel nehmen dem Spieler nichts, was er rechtmaessig hat; sie
ERSETZEN seine Wahl), Eintrag in `docs/architecture_reference.md` darum nicht noetig, beim Bau
pruefen.


## par.7 EXPLOITER-GEGNER (NUTZER-ENTSCHEID 2026-10-04, REGISTRIERT vor Bau und Lauf)

**Anlass:** Tor 1 verengt sich ueber die Generationen (v31 57,6 %, v32 54,3 %, v33 52,5 %; Koepfe der
Fenster-Preregs), der Stoerer als Suchknopf bewegt G nur um Rauschen (par.5a, par.5c1), und W verzerrt
die Wertziele (par.5a/5b1). Koordinator-Vorschlag, vom Nutzer angenommen (*"den stoerer als trainierten
exploiter find ich gut"*; Entscheide: *"3 x 1000, sims 100, tor 55 %"*).

**Konstruktion (AlphaStar-Form):** E_0 = Kopie des Generators G (`v34-b01`). Zyklus k = 1..3: 1.000
Partien E_{k-1} gegen G @100 Sims, E-Seite je Partie 50:50 Spieler 0 oder 1 (Partie-RNG), **Records NUR
von der E-Seite** (Policy aus der eigenen Suche, Wert = Partieausgang aus E-Sicht); dann Warm-Start-Training
E_k aus E_{k-1} auf genau diesen Records (Afterburner-Muster, `docs/measured_runtimes.md` Z. 52-53: 6 Epochen,
uebrige Flags wie das v34-Training). G bewegt sich nicht. **Die Wertverzerrung von W tritt hier nicht auf:**
E ist kein behinderter, sondern ein anderer Spieler; G-Records gegen E tragen den echten Ausgang gegen
diesen Gegner (HERLEITUNG).

**Tor (Nutzer):** E_3 schlaegt G in einer gepaarten Arena @100 Sims (200 Paare, Blockgroesse 5, Seed
20261745) mit **mindestens 55 %** der Partien. Haelt das Tor, kommt die Sockel-Klasse `policy-exploiter`
(G gegen E_3, sonst Sockel-Einstellung) in den v35-Sockel-Vorschlag; sonst wird berichtet, keine Klasse.
**NUTZER 2026-10-04 00:20: Records BEIDER Seiten mitschreiben** (*"ja, beide seiten mitschreiben. waere schon
gut wenn er sich ein paar aggressive moves abschaut"*), jeder Record mit Seitenmarkierung (`opponent_side`,
`net_label`). Standardvorschlag fuer das Fenster: G-Seite voll; E-Seite als ZWEITE Klasse mit eigener
Registrierung, Entscheid am Morgen, wie die E-Policy gefiltert wird (alles, oder nur Zuege, die auch G
plausibel findet, z. B. ueber G's Prior auf E's Zug; `own_q_gap` aus Klasse S ist dafuer NICHT die richtige
Groesse, weil es E's eigene Bewertung misst). Die Auswahl passiert im Training, nicht in der Erzeugung. Zusaetzlich berichtet je Zyklus: Siegquote E gegen G, Punkte und Marge beider Seiten,
sechs Standard-Kennzahlen, Laufzeit im Artefakt.

**Bau (Record-Feld-Regel: VOR der Erzeugung):** Self-Play mit zweitem Netz je Seite (`--opponent-model`,
Seitenwahl je Partie, Record-Feld `opponent_side` auf jedem Record einer solchen Partie, `net_label` je
Record), Schalter welche Seite Records schreibt (`--record-sides both|primary|opponent`); Rezept-Schluessel,
Manifest, Waechter. Knopf AUS byte-gleich (Lib-Tests, Anker-Invarianz, Netz-Paritaets-Fixture). Kosten
HERLEITUNG: je Zyklus rund 50 min Partien (3 s je Partie, par.5a) plus rund 10 min Training; drei Zyklen plus
Tor-Arena rund 3,5 h.

**Bauform, REGISTRIERT 2026-10-04 01:00 vor Kompilat und Lauf** (Bauplan `evaluations/exploiter_build_plan.md`,
Agent 2, Entscheide D1-D7; vom Koordinator angenommen): (D2) Seitenwahl des Gegner-Netzes je Partie aus einem
Hash des Partie-Seeds wie `dome_dice_side`, nicht aus dem Partie-RNG (der bleibt bei AN und AUS unberuehrt);
(D3) Zyklus-Partien mit `--record-sides both`, trainiert wird auf einer Kopie nur der E-Records
(`tools/split_records_by_net_label.py`), weil die Datenschicht nicht nach Feldern filtert und die Kennzahlen
den letzten Record je Partie brauchen; (D4) das Bootstrap-Label (`bootstrap_value`, TD-lambda 0,5 Anteil am
Wertziel) kommt je Seite aus dem Netz DIESER Seite, sonst waere die Haelfte von E's Wertziel G's Urteil; Grenze:
im Bootstrap spielt E gegen E weiter (HERLEITUNG); (D5) nicht kombinierbar mit Wuerfel, Stoerer, Stichentscheid-
Seite, Ausflug, `--rtv`; (D6) Dateinamen nach dem ERZEUGER: Zyklus k heisst `x35-e0{k-1}-cycle`, `e00` =
`v34-b01_brierbest`; (D7) der Gegner-Pfad kommt als Flag von der Kette (`_brierbest`, sonst finales Modell;
Manifest-Pruefung `engine_config.opponent_model`). Seeds: Partien 20261750/51/52, Training 20261753/54/55,
Smoke 20261756, Tor-Arena 20261745. Smoke-Schritt in der Kette: 10 Partien ohne und 10 mit Gegner E_0 bei
gleichem Seed muessen bis auf `opponent_side`, `net_label`, `game_id` identisch sein (Byte-Gleichheit der
Netzwahl bei gleichen Gewichten), sonst Stopp.

**Lauf-Chronik (Koordinator):** Kette gestartet 01:24; Lib 856 gruen, Anker-Drift und -Konservierung GRUEN
(`anchor_v2_*_20261004_exploiter.json`), Paritaets-Fixture GRUEN, Smoke identisch. Zyklus 1: 1.000 Partien in
6.126,6 s (**6,13 s je Partie**, 11 Threads; die HERLEITUNG oben mit 3 s war falsch, zwei Netze kosten das
Doppelte), Training `x35-e01` 183 s (6 Epochen, 347 Batches je Epoche; `_best` Epoche 2, `_brierbest` Epoche 1,
Policy-Val flach bei 1,02, "kein Plateau"). Stopp 03:19 am Manifest-Diff: `margin_threshold_weight`/`margin_thresholds`
sind train.py-Defaults vom 2026-10-02 (train.py:3453/3463), juenger als das v34-Manifest, inaktiv; Falsch-Positiv,
Diff-Liste korrigiert. **Koordinator-Entscheid 03:25 (vor Zyklus 2): E_k ist das FINALE Modell `alphazero_x35-e0k`,
nicht `_brierbest`** (das war Epoche 1, der am wenigsten vom Generator entfernte Stand; der Exploiter braucht die
am weitesten spezialisierte Policy). D7 ist damit ueberholt. Wiederaufnahme ab Zyklus 2 mit `EXPLOITER_FROM_CYCLE=2`.

**Zyklen 1 und 2, Kennzahlen** (`evaluations/artifacts/exploiter_cycle_1.json`, `_2.json`; Grundmenge je 1.000
Partien, Einheit Siegquote je Partie mit Block-Bootstrap-CI ueber 100 Dateien, Punkte je Partie; Kennzahlen je
Seite ueber 1.000 Seiten):

| Zyklus | Paarung | Siegquote E [CI] | Punkte E / G | volle Spalten E / G | Strafleiste E / G |
| --- | --- | --- | --- | --- | --- |
| 1 | G gegen E_0 (= G) | 0,520 [0,489; 0,552] | 53,3 / 52,6 | 0,91 / 0,91 | 5,0 / 5,2 |
| 2 | G gegen E_1 | **0,458 [0,430; 0,486]** | 52,4 / 54,3 | 0,93 / 0,90 | 5,0 / 4,9 |

Zyklus 1 ist die Nullkontrolle (gleiche Gewichte, 52 %, CI mit 0,50). **Zyklus 2: E_1 ist SCHWAECHER als G** (CI
ganz unter 0,50, -1,9 Punkte), nicht staerker. HERLEITUNG (vorlaeufig, vor Zyklus 3 und Tor): ein Afterburner
ueber 6 Epochen auf rund 99.000 E-Records aus einem 50:50-Regime erzeugt keine Gegenstrategie, sondern eine
verrauschte Kopie (Policy-Val flach 1,02-1,03; Value-R2 von 0,45 auf 0,53 ist Anpassung an den kleinen Satz). Die
AlphaStar-Form braucht vermutlich ein Vielfaches an Partien je Zyklus oder ein anderes Ziel (nur Verlustpartien
von G, hoeheres Gewicht auf E-Siege); das Tor 55 % wird nach diesem Stand voraussichtlich NICHT fallen. Zyklus 3 und
Tor laufen wie registriert weiter (Nutzer-Entscheid 3 x 1.000), Ergebnis unten. Nebenbefund: beide Seiten holen
mit Stichentscheid Modus 2 rund 53 Punkte je Partie gegen 46,9 im Bestand-Sockel `policy` (par.5a), konsistent
mit par.5e3.

**Zyklus 3, Lauf-Chronik:** Start 05:17 (E_2 = `alphazero_x35-e02` final); um 05:24 beendete der Harness die
Hintergrundaufgabe (Zeitlimit 2 h), danach scheiterten neue Chunk-Subprozesse mit Exit 0xC0000142, self_play.py
brach bei 70 Partien ab (Chunks 0-6 vollstaendig). **Teil-Wiederaufnahme 05:40 im Terminal-Tab** nach der
Tail-Konvention: `--games 930 --seed 20261759` (Basis 20261752 + 7 Chunks), Rezept-Overrides im Manifest; die
Kennzahlen laufen ueber alle 100 Dateien, `laufzeit_vollstaendig` = false (Abbruchlauf ohne Laufzeit).
**Befund (Agent 2, vom Koordinator an `make_chunk` nicht nachgeprueft, Lesart plausibel): die Chunk-Seeds sind
Basis + Chunk-Index, und die Basis-Seeds 20261750/51/52 liegen nur um 1 auseinander** -- Chunk i von Zyklus 2
startet mit demselben Seed wie Chunk i+1 von Zyklus 1 (gleiche Wertungsplatten, gleicher Startspieler), nur mit
anderem E. Je Zyklus sauber, ueber Zyklen korreliert; fuer eine Sockel-Klasse aus mehreren Zyklen und fuer
kuenftige Zyklus-Seeds mindestens 100 Abstand waehlen.

### par.7a ERGEBNIS EXPLOITER: Zyklus 3 und Tor (2026-10-04 05:29-07:39; Artefakte `exploiter_cycle_3.json`, `exploiter_gate.json`, `plate_points_exploiter_gate.json`, `arena_columns_exploiter_gate.json`)

| Zyklus | Paarung | Siegquote E [CI] | Punkte E / G | Marge E |
| --- | --- | --- | --- | --- |
| 1 | G gegen E_0 (= G) | 0,520 [0,489; 0,552] | 53,3 / 52,6 | +0,7 |
| 2 | G gegen E_1 | 0,458 [0,430; 0,486] | 52,4 / 54,3 | -1,9 |
| 3 | G gegen E_2 | 0,476 [0,443; 0,508] | 52,0 / 53,1 | -1,1 |

(Grundmenge je 1.000 Partien @100, Erzeugungsbedingungen, Stichentscheid Modus 2 beide Seiten; Zyklus 3 aus
zwei Laeufen, 70 plus 930 Partien, Laufzeit des Abbruchlaufs fehlt.)

**TOR (par.7): E_3 gegen G, gepaarte Arena @100, 200 Paare = 400 Partien, Blockgroesse 5, Seed 20261745,
Fruehstopp aus, 1.797 s bei 10 Threads: 185:215 = 46,25 %** (Siege je Brett 0,463 [0,414; 0,511]), gepaarte
Differenz -0,15, McNemar p 0,17; Punkte 57,8 gegen 58,7, Marge -0,9 [-2,8; +1,0], volle Spalten je Seite
1,0 gegen 1,1 (Spaltensonde), Strafleiste 7,5 gegen 7,2, Plattenpunkte 8,3 gegen 8,6. **Das Tor von 55 % faellt
NICHT; E_3 ist tendenziell schwaecher als G.** Keine Sockel-Klasse `policy-exploiter` im v35-Vorschlag.

**Lesart (HERLEITUNG):** drei Afterburner-Zyklen mit je rund 99.000 E-Records aus einem 50:50-Regime bewegen
E nicht zu einer Gegenstrategie, sondern zu einer verrauschten, leicht schwaecheren Kopie (Policy-Val flach
1,02-1,03, Siegquote 52 -> 46 -> 48 %). Die AlphaStar-Form braucht ein anderes Ziel oder ein Vielfaches an
Material: (a) Training nur auf den Partien, die E gewinnt, oder mit Gewicht auf E-Siege (Ziel "schlage G",
nicht "spiele wie G gegen G"); (b) deutlich mehr Partien je Zyklus (hier 1.000 bei 6,1 s je Partie, also
rund 100 min; ein Vielfaches ist eine Nacht je Zyklus); (c) kaltere Lernrate ist NICHT der Hebel (die Policy
bewegte sich kaum). Der Bau (zweites Netz je Seite, `--record-sides`, Record-Felder) bleibt im Baum,
Knopf AUS byte-gleich (Anker, Paritaet, Smoke gruen), und steht fuer eine spaetere Form bereit. Linie fuer
v35 GESCHLOSSEN; Wiederaufnahme nur mit neuer Registrierung (Ziel und Material).

**Kosten der Nacht fuer par.7 (gemessen):** Partien 3 x rund 6.200 s, Trainings 3 x rund 180 s, Tor 1.797 s;
zusammen rund 5,9 h Maschine.

### par.7b WEG 1: fremder Stil statt trainierter Exploiter (NUTZER 2026-10-04 *"fahr die weg-1 sonde gegen v32-b01"*, REGISTRIERT vor dem Lauf)

Anlass par.7a: ein Exploiter aus einer Kopie von G findet G's Loecher nicht. Billigste Form eines Gegners mit
anderem Stil, ohne Training: der vorige Champion `v32-b01` (Register: 1544 gegen 1595 bei gleicher Spec, G
gewinnt rund 57 %, HERLEITUNG aus den Elo-Werten). Der Zweitnetz-Knopf aus par.7 wird dafuer unveraendert
benutzt (`--opponent-model models/alphazero_v32-b01_brierbest.onnx`, Eingabeform [79,6,6] wie v34, geprueft).

**Sonde (Rezept `models/v35_probes2.recipe.json`, je Klasse Seed 20261720, Erzeugungs-Rezept @100, Stichentscheid
Modus 2 auf BEIDEN Seiten, weil das der vorgeschlagene v35-Sockel ist):**
* `policy-m2`: G gegen G, 200 Partien. Bezugsklasse fuer KL und Kennzahlen unter Modus 2.
* `policy-vs-v32`: G gegen v32-b01, 200 Partien, `--record-sides both`, Felder `opponent_side`/`net_label`.

**Berichtet** (Grundmenge Drafting-Records R1-4 mit Ziel >= 2 IDs bzw. Partien; Einheit wie par.5a): Median-KL(Ziel ||
Prior von G) der G-Seite (`net_label` primary) von `policy-vs-v32` gegen alle Records von `policy-m2`, Block-
Bootstrap-CI ueber Dateien, je Runde; Versatz des Wertkopfs je Seite (G und v32); Siegquote G gegen v32 mit CI;
Punkte und Marge; sechs Standard-Kennzahlen je Seite; Kosten je Partie. **Leseregel:** KL-CI der G-Seite ganz
ueber 0 UND |Versatz G| <= 0,05 (oder CI mit 0) -> Vorschlag Sockel-Klasse `policy-vs-v32` (2.000 Partien, rund
3,4 h bei 6 s je Partie) fuer den Nutzer-Entscheid; KL-CI mit 0 -> Weg 1 traegt nicht, berichtet; Versatz
groesser -> Wertziele der G-Seite als verzerrt markiert, Maske als Vorlage (wie par.5 Regel b).

#### par.7b1 ERGEBNIS WEG 1 (2026-10-04 09:44-10:32, Kette `tools/night_v35_prep_chain2.sh`, Artefakte `probe_vs_v32_kl.json`, `probe_vs_v32_sides.json`)

Je 200 Partien @100, Modus 2 beide Seiten, Seed 20261720. **Grundmenge** Drafting-Records R1-4 mit Ziel >= 2 IDs
(G-Seite von `policy-vs-v32`: 12.060; `policy-m2` beide Seiten: 24.018) bzw. 200 Partien; **Einheit** wie par.5a.

| Groesse | `policy-m2` (G gegen G) | `policy-vs-v32`, G-Seite | `policy-vs-v32`, v32-Seite |
| --- | --- | --- | --- |
| Median-KL (R1 / R2 / R3 / R4) | 0,338 (0,24 / 0,35 / 0,39 / 0,39) | 0,347 (0,25 / 0,35 / 0,40 / 0,41) | -- |
| Differenz gegen `policy-m2` [CI] | | **+0,010 [-0,009; +0,032]** | |
| Siegquote [CI] | 0,50 | **0,64 [0,565; 0,725]** | 0,36 [0,28; 0,44] |
| Punkte, Marge | 52,4 | 55,6, +7,0 | 48,5, -7,0 |
| Versatz Wertkopf [CI] | | **-0,101 [-0,179; -0,026]** | +0,083 [+0,011; +0,155] |
| volle Spalten / Strafleiste je Seite | 0,88 / 5,3 | 0,99 / 4,8 | 0,76 / 5,6 |
| s je Partie (11 Threads) | 3,206 | 6,300 | |

**Leseregel: Weg 1 traegt NICHT.** Die KL der G-Seite ist nicht nachweisbar anders (CI mit 0), und der Versatz der
G-Seite liegt mit -0,10 ausserhalb der 0,05-Grenze mit CI ohne 0: G gewinnt gegen den schwaecheren Vorgaenger 64 %,
der Wertkopf erwartet aber G-gegen-G, also sind die Wertziele der G-Seite systematisch zu optimistisch gegenueber
der Vorhersage (dieselbe Form von verborgener Behinderung wie bei W, nur umgekehrt). Keine Sockel-Klasse. Lesart
(HERLEITUNG): ein 50 Elo schwaecherer Vorgaenger aus derselben Linie spielt keinen anderen Stil, nur schwaecher.
Die zustandsbasierte Pruefung (par.5d2) laeuft noch; sie kann die KL-Lesart fuer W und v32 noch kippen.

### par.7c EXPLOITER, naechste Form (NUTZER 2026-10-04, siehe par.5d3; REGISTRIERT vor Bau und Lauf)

**Diagnose aus par.7a:** Imitation der eigenen Suche auf 99.000 Records erzeugt eine verrauschte Kopie, kein
Gegner im Ziel, E_0 = G teilt G's blinde Flecken. Drei Aenderungen GLEICHZEITIG:
1. **Ziel mit Gegner (REINFORCE-Filter):** E trainiert Policy NUR aus Partien, die E gewonnen hat; Records aus
   verlorenen Partien behalten das Wertziel, ihr Policy-Ziel wird stummgeschaltet ueber das vorhandene Record-Feld
   `policy_target_valid = false` (corpus_dataset.py:1798 setzt dann Policy-Gewicht 0; Training OHNE
   `--ignore-policy-target-valid`, anders als v34). Umsetzung in `tools/split_records_by_net_label.py`
   (`--policy-only-won`), kein Datenschicht-Umbau.
2. **E sucht tiefer als G in den Zyklus-Partien:** E @200, G @100 (Sims je Seite fuer das Zweitnetz, Knopf
   `--opponent-sims`, Default = `--sims`, byte-gleich). E's Policy-Ziele stammen damit aus einer staerkeren Suche
   als G's Spiel (Register: @400 gegen @100 rund 77 %; @200 ungemessen, HERLEITUNG dazwischen); ob das Wissen ins
   Netz uebergeht, prueft das Tor bei GLEICHEN Sims.
3. **Volumen mit Vortor:** 2 Zyklen a 2.000 Partien (statt 3 x 1.000), nach Zyklus 1 ein Vortor: E_1 gegen G in
   einer gepaarten Arena @100, 100 Paare, muss >= 0,52 erreichen, sonst Abbruch (spart Zyklus 2); Basis-Seeds
   mit Abstand >= Chunkzahl: Zyklus 1 20261800, Zyklus 2 **20262000** (KORRIGIERT vor dem Lauf: 200 Chunks je
   Zyklus, Chunk-Seed = Basis + Index, 100 Abstand haette wieder ueberlappt; Agent-Befund); Trainings-Seeds
   20261860 und 20262060, Vortor 20261850, Tor 20261950. Training wie par.7 (6 Epochen,
   finales Modell), E_0 = G.
**Tor unveraendert:** E_2 gegen G @100, 200 Paare, >= 55 %. Danach die Sockel-Klasse `policy-exploiter`
(G gegen E_2, Records beider Seiten) wie par.7. Kosten HERLEITUNG: Zyklus 2.000 Partien mit E @200 rund 2.000 x
9 s = 5 h (ungemessen, aus 6,1 s bei @100/@100 plus E-Haelfte doppelt), Training 5 min, Vortor 15 min, Tor 30
min; zwei Zyklen rund 11 h. Falls das Vortor faellt, wird vor Zyklus 2 berichtet. Scheitert auch diese Form,
ist die naechste Stellschraube ein anderer Startpunkt fuer E_0 (`v32-b01`) oder ein Gewicht statt Filter.

## par.8 SOCKEL @400 SIMS (NUTZER 2026-10-04: *"sockel mit 400 sims kann ich gut leben"*)

Vorschlag des Koordinators: die 2.000 G-G-Partien des v35-Sockels @400 statt @100 (der Schwarm bleibt @100).
Begruendung: der Policy-Zielwert ist eine Suche ueber den eigenen Prior; hat der Prior die 100er-Suche
eingeholt, traegt das Ziel nichts Neues (HERLEITUNG). Kosten aus `PREREG_search_depth_column_optimum.md`
par.8e: 8,29 h fuer 4.000 @400 -> rund 4,1 h fuer 2.000. Benannter Preis: die Spaltenvollendung faellt ueber
100-400 Sims monoton (par.8e; Nutzer-Entscheid 2026-09-13 "Betriebspunkt 100 BLEIBT" galt den Spalten).

**Vortest (REGISTRIERT vor dem Lauf):** Klasse `policy-s400` (wie `policy`, Sims 400, gleicher Seed 20261720,
100 Partien) in `models/v35_probes2.recipe.json`; Median-KL(Ziel || Prior) der Drafting-Records R1-4 gegen die
0,316 der Klasse `policy` @100 (par.5a, gleiche Grundmenge und Einheit), Block-Bootstrap-CI ueber Dateien;
dazu Kosten je Partie und die sechs Standard-Kennzahlen. Keine Schwelle: der Vortest beschreibt, der
Nutzer entscheidet ueber das Sockel-Rezept.

### par.8a ERGEBNIS Vortest Sockel @400 (2026-10-04 00:40-00:51, Artefakt `evaluations/artifacts/probe_policy_s400_kl.json`)

100 Partien `policy-s400` (Seed 20261720, sonst wie `policy`), Bezug `policy` @100 (par.5a). **Grundmenge** Drafting-
Records R1-4 mit Ziel >= 2 IDs (12.095 gegen 11.999), **Einheit** KL(Ziel || Prior) je Record, Median; Kennzahlen
je Seite ueber 200 Seiten aus 100 Partien (`corpus_sanity_check.auswerten`):

| Groesse | `policy` @100 | `policy-s400` @400 |
| --- | --- | --- |
| Median-KL (R1 / R2 / R3 / R4) | 0,316 (0,21 / 0,34 / 0,37 / 0,38) | **0,625** (0,52 / 0,61 / 0,69 / 0,72) |
| Differenz [CI Block-Bootstrap] | | **+0,310 [+0,263; +0,354]** |
| s je Partie (11 Threads) | 2,898 | 6,010 (**Faktor 2,07**) |
| Punkte je Seite | 46,9 | **31,4** |
| volle Spalten je Seite / Seiten mit voller Spalte | 0,90 / 128 | **0,445 / 73** |
| volle Zeilen je Seite | 0,05 | 0,11 |
| Strafleiste je Seite | 5,9 | **8,4** |
| k1-Punkte (aktiv in 38 Partien) | 7,4 | 3,1 |
| k5-Punkte (aktiv in 36) | 9,2 | 6,4 |

Lesart: die tiefere Suche korrigiert den Prior DOPPELT so stark (die Frage aus par.8 ist mit JA beantwortet, das
Ziel traegt bei 400 Sims deutlich mehr Information als bei 100). **Aber der Preis ist groesser als der aus par.8e
bekannte Spalten-Tausch:** beide Seiten holen 15 Punkte weniger, vollenden halb so viele Spalten und nehmen 2,5
Strafpunkte mehr. HERLEITUNG, nicht geprueft: die tiefere Nullsummen-Suche opfert eigene Punkte fuer Siegwahrschein-
lichkeit (Denial), und ein Teil der hoeheren KL ist dieser Stilwechsel, nicht nur "mehr Wissen". Fuer den Punkte-
und Spaltenlehrer (Kopf `opp_points`, Spaltenziele der Kampagne) waere ein solcher Sockel ein Schritt zurueck.
Kosten fuer 2.000 Partien: rund 3,3 h (HERLEITUNG aus 6,01 s). **Nutzer-Entscheid am Morgen**; Vorschlag des
Koordinators: NICHT der ganze Sockel @400, sondern ein Mischarm (z. B. 1.000 @100 plus 1.000 @400, oder @200 als
Zwischenpunkt mit eigener Sonde), damit der Punkte-Einbruch nicht das ganze Policy-Material praegt.

### par.8b NUTZER-FRAGE 2026-10-04 (*"gleicht sich das aus mit dem q-stichentscheid?"*), REGISTRIERT vor dem Lauf

Der Vortest par.8a lief mit Bestands-Stichentscheid (Modus 0). Ob der Punkte-Einbruch bei 400 Sims (46,9 -> 31,4)
mit Modus 2 verschwindet, ist nicht ableitbar: Modus 2 behebt die Wahl unter Gleichstaenden (@100: +6 Punkte je
Seite, par.7a Zyklus 1 gegen par.5a), der Einbruch @400 ist nach der HERLEITUNG in par.8a ein Stilwechsel der
tieferen Nullsummen-Suche; beides kann sich addieren oder nicht. **Klasse `policy-s400-m2`:** wie `policy-s400`
(100 Partien @400, Seed 20261720), aber Modus 2 beide Seiten. **Berichtet:** Punkte je Seite, volle Spalten,
Strafleiste, Plattenpunkte, Median-KL gegen `policy-m2`, Kosten, jeweils neben `policy-s400` (par.8a) und
`policy-m2`. **Leseregel:** Punkte je Seite von `policy-s400-m2` innerhalb von 3 Punkten von `policy-m2` -> der
Einbruch war ein Stichentscheid-Artefakt, Sockel @400 wieder offen; bleibt der Abstand groesser als 8 Punkte ->
Einbruch ist die Suchtiefe, par.8a-Lesart bestaetigt; dazwischen -> teilweise, berichtet. Keine Entscheidung
ueber den Sockel durch die Sonde, die liegt beim Nutzer.

#### par.8b1 ERGEBNIS: der Einbruch @400 war der Stichentscheid (2026-10-04 10:17-10:32, Artefakt `probe_s400_m2_kl.json`)

100 Partien @400 mit Modus 2 (`policy-s400-m2`, Seed 20261720) gegen `policy-m2` (200 @100, Modus 2) und
`policy-s400` (100 @400, Modus 0, par.8a). **Grundmenge** Drafting-Records R1-4 (12.047 / 24.018 / 12.095) bzw.
Seiten (200 / 400 / 200); **Einheit** wie par.8a.

| Groesse | `policy-m2` @100 | `policy-s400-m2` @400 | `policy-s400` @400, Modus 0 |
| --- | --- | --- | --- |
| Median-KL | 0,338 | **0,683** (+0,345 [+0,313; +0,382]) | 0,625 |
| Punkte je Seite | 52,4 | **50,3** (-2,1; CI je 1,7 / 2,6) | 31,4 (-21,0) |
| volle Spalten je Seite | 0,88 | **0,845** (-0,035; CI je 0,07 / 0,10) | 0,445 |
| Strafleiste je Seite | 5,3 | 5,3 | 8,4 |
| Spalten >= 4 je Seite | 2,33 | 2,23 | 1,88 |
| s je Partie (11 Threads) | 3,206 | 6,754 (**Faktor 2,1**) | 6,010 |

**Leseregel par.8b: Punkte innerhalb von 3 Punkten -> der Einbruch war ein Stichentscheid-Artefakt, der Sockel
@400 ist wieder offen.** Mit Modus 2 verdoppelt die 400er-Suche die KL (0,338 -> 0,683) bei gleichen Punkten,
gleichen vollen Spalten und gleicher Strafleiste; der Spalten-Tausch aus par.8e (Vollendung faellt mit den Sims)
ist in dieser Anordnung NICHT sichtbar (CI ueberlappen). HERLEITUNG, warum: bei 400 Sims liegen nach dem Halving
mehr Kinder gleichauf, und "erster Eintrag" verschenkt dann systematisch den Q-besseren Zug; der Effekt
waechst also mit den Sims. Das heisst auch: die Sims-Kurve vom 2026-09-13 (par.8e) wurde mit Modus 0 gemessen
und ist fuer die Vollendung neu zu bewerten (Rueckwaerts-Pruefung, Konsumenten: `PREREG_search_depth_column_optimum.md`,
STATUS Abschnitt 8 "Sims und Spaltenbau", Memory). **Fuer den v35-Sockel ist @400 mit Modus 2 damit die Form, die
beides liefert: doppelte Zielinformation ohne Punkte- oder Spaltenpreis; Kosten 2.000 Partien rund 3,75 h.**
Nutzer-Entscheid.
