<!-- STATUS: OFFEN | Frage: Erzeugt asymmetrisches Self-Play (Wuerfel-Kuppelplatten auf einer Seite, spaeter ein stoerender Gegner) Stellungen, die das Spiel gegen sich selbst nicht erreicht, und traegt ein Fenster daraus? | Beleg: ENTWURF 2026-10-01, nichts gebaut. Wuerfel-Klasse W festgelegt (par.2), Stoerer-Klasse S skizziert, Records beider Seiten, Stoerer-Policy nur bei fast gleichwertigem eigenem Wert (par.3); Zusammensetzung des Fensters nach den Sonden (par.5), Nutzer-Plan 4.000 W plus 2.000 Sockel ohne G-1/G-2 (par.4). Zeitpunkt: nach dem v34-Training. -->

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
     tatsaechlich kommt. Alle anderen Zuege beider Seiten mit den Sockel-Sims (100).
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
  Root-Noise, `tie_mirror_p` 0,5, `start_slot_random_p` 0,15, E1, Runde 5 per Netz). VORSCHLAG,
  insbesondere ob die Weg-C-Abweichung (`deviate_prob` 1,0) in W bleibt.

**Folgen, als HERLEITUNG vorab benannt (ungemessen):**
* Stapel zu Rundenbeginn (aus `engine_manual.md` 2/3/4A: 18 Platten, 2 Startplatten, Auslage zu
  jeder Runde auf 3 aufgefuellt, je Runde 1-4 vier Platten gelegt): Runde 1 **13**, Runde 2 **9**,
  Runde 3 **5**, Runde 4 **1**; innerhalb der Runde sinkt er um jede vom Stapel GELEGTE Platte
  (zurueckgelegte gehen wieder darunter). Erwartete Kosten eines Stapelzugs bei vollem Rundenstapel
  und d gleichverteilt: Runde 1 **7** Punkte (1..13), Runde 2 **4** (1..7), Runde 3 **2** (1..3),
  Runde 4 **1**. Bei 0 Punkten sind weitere Stapelzuege frei (`PREREG_score_clamp_incentive.md`
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

Stuetze fuer den Wegfall von G-1/G-2 (am Bestand): die Fensterarme b02-b04 waren ununterscheidbar,
Menge und Alter des Value-Materials kein Hebel (`PREREG_v33_window.md` par.6d, STATUS RICHTUNG).

## par.5 SONDEN vor der Festlegung (VORSCHLAG, Leseregeln vor dem Lauf hier eintragen)

* **S1 Kosten:** je 100 Partien Sockel gegen W, gleiche Seeds, Muster `tools/v34_cost_gate.sh`.
* **S2 Andere Stellungen?** Policy-KL `KL(Ziel || Prior)` an den Zuegen nach erzwungenen Platten
  gegen dieselbe Groesse im Sockel (Werkzeug `tools/probes/targeted_branching_pretest.py`),
  dazu die sechs Standard-Kennzahlen je Seite.
* **S3 Wert-Verzerrung:** Siegquote und Punkte der Wuerfel-Seite; Brier des Generator-Kopfs auf
  W-Records gegen Sockel-Records, getrennt nach Seite.
* **S4 Stoerer-Pilot** (nur nach dem Bau par.3): lambda-Reihe, Punkte der normalen Seite und des
  Stoerers je lambda.

## par.6 BAU (nach der v34-Erzeugung, in der Wheel-Runde mit E4 und dem Review-Rest)

Engine: Wuerfel-Seite und Wuerfel in der Self-Play-Schleife (Partie-RNG bzw. eigener Strom nach
`PREREG_search_rng_split.md`), Wurzel-Beschraenkung auf die Plaetze der gewuerfelten Platte,
festgenagelte Rotation im Baum, Platzsuche mit eigener Sim-Zahl, Record-Unterdrueckung fuer den
erzwungenen Zug, die zwei Record-Felder, Knopf mit Default aus (byte-identisch), Rezept-Schluessel.
Danach Anker-Invarianz, Netz-Paritaets-Fixture, Smoke. Fuer S: Spec-Feld je Seite fuer lambda_aggr.
Neue Mischstellen: keine (die Wuerfel nehmen dem Spieler nichts, was er rechtmaessig hat; sie
ERSETZEN seine Wahl), Eintrag in `docs/architecture_reference.md` darum nicht noetig, beim Bau
pruefen.
