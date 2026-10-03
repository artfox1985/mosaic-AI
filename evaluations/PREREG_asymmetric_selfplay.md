<!-- STATUS: OFFEN | Frage: Erzeugt asymmetrisches Self-Play (Wuerfel-Kuppelplatten auf einer Seite, ein stoerender Gegner) Stellungen, die das Spiel gegen sich selbst nicht erreicht, und traegt ein Fenster daraus? | Beleg: W in Vollform verliert 75-77 % mit verzerrten Wertzielen (par.5a/5b1); jetzt Eroeffnungs-Wuerfel R1/R1-2 mit Wertmaske gebaut, Sonde S5 offen (par.5d). Stoerer B war konfundiert (S Q-gierig, 77-81 %, par.5c1), repariert, S4b neu offen (par.5c2). Nebenbefund Zugwahl der Erzeugung offen (par.5e). -->

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

## par.6 BAU (nach der v34-Erzeugung, in der Wheel-Runde mit E4 und dem Review-Rest)

Engine: Wuerfel-Seite und Wuerfel in der Self-Play-Schleife (Partie-RNG bzw. eigener Strom nach
`PREREG_search_rng_split.md`), Wurzel-Beschraenkung auf die Plaetze der gewuerfelten Platte,
festgenagelte Rotation im Baum, Platzsuche mit eigener Sim-Zahl, Record-Unterdrueckung fuer den
erzwungenen Zug, die zwei Record-Felder, Knopf mit Default aus (byte-identisch), Rezept-Schluessel.
Danach Anker-Invarianz, Netz-Paritaets-Fixture, Smoke. Fuer S: Spec-Feld je Seite fuer lambda_aggr.
Neue Mischstellen: keine (die Wuerfel nehmen dem Spieler nichts, was er rechtmaessig hat; sie
ERSETZEN seine Wahl), Eintrag in `docs/architecture_reference.md` darum nicht noetig, beim Bau
pruefen.
