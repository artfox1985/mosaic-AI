<!-- STATUS: OFFEN | Frage: Blieb der Verteilungs-Punkte-Kopf (Task #12) unterhalb der Aufloesung, weil seine Bins aequidistant im tanh-Raum liegen und damit im Punkteraum an den Raendern um Faktor 5-25 groeber werden -- und aendert eine punktlineare Bin-Skala das? | Beleg: nichts gebaut, Entwurf angelegt 2026-08-23, am selben Tag nach Durchsicht KORRIGIERT (par.2a). Bin-Kanten `torch.linspace(-1,1,bins+1)` in `engine/py/neural_net.py:2411` gelesen. Zwei Entwurfsfehler behoben: (1) #12 lief NICHT am Differenzziel, sondern seit 2026-07-06 eigenseitig -- der behauptete Defekt lag also bereits vor und die Messung kam flach heraus, #12 ist damit ein Prior GEGEN die Hypothese; (2) das Ziel ist nicht `tanh(own/50)`, sondern in ~83 % der Zeilen der TD-Blend mit einer remappten Gewinnwahrscheinlichkeit (gemessen 2026-08-23, je eine Datei pro Generation), der die Ziele in den FEINEN Bereich zieht. Vorpruefung par.6 ist Tor und rechnet jetzt auf dem tatsaechlichen `points_val`, nicht auf der Formel -->

# Vorregistrierung: Bin-Skala des Verteilungs-Punkte-Kopfes

**Angelegt 2026-08-23, VOR jeder Messung.** Wiederaufnahme von Task #12
unter EINER neuen, bisher nicht gemessenen Bedingung.

## par.1 Anlass

Task #12 (Verteilungs-Punkte-Kopf, 51 Bins, C51/HL-Gauss) ist zweimal ohne
Arena-Beleg geblieben: 2026-07-29 am alten Value-Ziel (offline R² 0,0906
gegen 0,1160, Arena gepoolt p=0,1046) und im Nach-#34-Paket als Arm 1
`t12_dist` am WDL-Ziel (erst SPRT-H1 mit 54:26, in der vorregistrierten
Frisch-Seed-Replikation als Seed-Rauschen entlarvt, 206:194 und 181:179).

Zwei Dinge daran sind bisher nicht ausgeschoepft.

**Erstens: die Aufloesungsregel des Nach-#34-Pakets** haelt ausdruecklich
fest, dass ein H0 "kein Beleg" bedeutet und **nicht "widerlegt"**. Der Kopf
liegt unterhalb der Aufloesung, er ist nicht erledigt. Eine
Wiederaufnahme braucht deshalb keine Ausnahme von einer Schliessungsregel,
sondern nur einen Grund, warum es diesmal anders ausgehen sollte.

**Zweitens: es gibt einen konkreten solchen Grund**, und er stand bisher in
keiner der beiden Messungen. Die Bin-Kanten sind

```
edges = torch.linspace(-1.0, 1.0, bins + 1)      # engine/py/neural_net.py:2411
```

also **aequidistant im tanh-Raum**. Das Ziel ist aber
`tanh(Punkte / VALUE_SCALE)`. Aequidistante Bins in tanh-Koordinaten sind im
Punkteraum stark ungleich: fein in der Mitte, grob an den Raendern.

## par.2 Die Kompression, hergeleitet

Herleitung, nicht gemessen. Sie folgt aus der Bin-Kanten-Zeile oben und aus
`VALUE_SCALE = 50.0` (`engine/py/neural_net.py:712`, am 2026-08-23
zeilenweise nachgeprueft). Bei 51 Bins ist die Bin-Breite im tanh-Raum
`2/51 = 0,0392`. Die entsprechende Breite in Punkten ist
`0,0392 · VALUE_SCALE / (1 − z²)`:

| Zielwert z = tanh(P/50) | Punktestand P | Bin-Breite in Punkten |
|---|---|---|
| 0,00 | 0 | 1,96 |
| 0,50 | 27,5 | 2,61 |
| 0,76 | 50,0 | 4,64 |
| 0,80 | 54,9 | 5,45 |
| 0,885 | 70,0 | 9,03 |
| 0,90 | 73,6 | 10,3 |
| 0,95 | 91,6 | 20,1 |
| 0,98 | 114,9 | 49,5 |

Ein Bin von 10 bis 20 Punkten Breite ist fuer eine Groesse, deren
Gesamtspanne in dieser Groessenordnung liegt, keine Verteilung mehr,
sondern eine Vergroeberung.

## par.2a Was das Ziel WIRKLICH ist (Korrektur 2026-08-23)

Der urspruengliche Entwurf dieser Prereg rechnete mit
`Ziel = tanh(own_total / 50)`. Das ist zweimal falsch, beide Male am Code
nachgeprueft.

**Erstens: `points_val` ist nicht nur der eigene Endstand.** Nach der
Formelzeile (`neural_net.py:1647`) greifen zwei Ueberschreibungen:

| Stelle | Wirkung |
|---|---|
| `neural_net.py:1704` | `points_val = own_rtv` -- ersetzt komplett, `own_rtv = 2·rtv[p] − 1`, also eine remappte GEWINNWAHRSCHEINLICHKEIT |
| `neural_net.py:1717` | `points_val = TD_LAMBDA·(2·bv[p] − 1) + (1 − TD_LAMBDA)·points_val`, `TD_LAMBDA = 0.5` (`neural_net.py:717`) |

Kein Schalter unterdrueckt den TD-Blend; `value_target_variant` greift nur
am rtv-Zweig. `bootstrap_value` wird je Runde mit echtem Uebergang
geschrieben (`self_play.rs:1881`), fehlt also nur in Runde 5.

**Gemessen am 2026-08-23** (je eine Datei pro Generation, kein Vollscan):

| Korpus | Datensaetze | `round_transition_value` | `bootstrap_value` |
|---|---|---|---|
| v18 | 1628 | 0 | 1362 (83,7 %) |
| v19wdl | 1654 | 0 | 1381 (83,5 %) |
| v19wdlsw | 1610 | 0 | 1352 (84,0 %) |
| v20wdl | 1644 | 0 | 1361 (82,8 %) |
| v20wdlsw | 1612 | 0 | 1344 (83,4 %) |

Der rtv-Zweig ist tot. Fuer rund 83 % aller Zeilen ist das Ziel der
TD-Blend, fuer die restlichen ~17 % (Runde 5) das reine `tanh(own/50)`.
Bei ausgeglichener Stellung liegt `2·bv−1` nahe null, der Blend also nahe
`0,5·tanh(own/50)` -- z um 0,42 statt 0,85, und damit im FEINEN Bereich der
Skala (Bin-Breite rund 2,4 Punkte statt 4 bis 10).

**Zweitens: #12 lief nicht am Differenzziel.** Der Verteilungskopf trainiert
auf `targets_points` (`train.py:1073`), und `points_val` war seit db73122
(2026-07-06, "Differenzbildung durch getrennt gesaettigte Terme ersetzt")
bis Schema 20 (08c565d, 2026-08-10)
`tanh(own/50) − 0,1·tanh(opp/50)` (`git show 78f3cf5:engine/py/neural_net.py`
Z. 571-572, `VALUE_OPP_EPSILON = 0.1`). Beide #12-Messungen lagen also
bereits eigenseitig. Der Irrtum stammt aus
`research_value_head_alternatives_DRAFT.md` Z. 7 und ist dort korrigiert.

**Konsequenz fuer diese Prereg** -- sie faellt haerter aus als der Entwurf
sie geplant hatte:

1. Die Behauptung "eine schlichte Wiederholung von #12 mit dem heutigen Ziel
   waere schlechter als die Originalmessung" ist **gestrichen**. Beide
   Messungen liefen am eigenseitigen Ziel, die Zielumstellung Schema 20 hat
   nur den 0,1-Gegner-Term entfernt.
2. Die Kompression war in #12 damit **bereits wirksam** -- soweit sie
   ueberhaupt wirksam ist. #12 ist kein neutraler Vorlauf, sondern ein
   **Prior gegen** die Hypothese: der behauptete Defekt lag vor, und die
   Messung kam flach heraus.
3. Ob die Kompression ueberhaupt beisst, haengt vollstaendig am TD-Blend und
   damit an einer Datei-Eigenschaft. Genau das entscheidet die Vorpruefung
   par.6, die deshalb auf den TATSAECHLICH gebauten `points_val` zu rechnen
   ist und nicht auf die Formel.

## par.3 Begriffsklaerung: das ist NICHT die Platt-Entstauchung

Im Projekt ist "entstauchen" bereits belegt: `_destretch_prob`
(`engine/py/neural_net.py:675`, A = 0,0051, B = 1,9269) streckt eine
**Wahrscheinlichkeit** und wird auf das WDL-Bootstrap-Ziel angewandt
(`--wdl-bootstrap-destretch`, Arm B in `PREREG_task34_erosion_arms.md`).

Hier geht es um etwas anderes: um die **Lage der Bin-Kanten** auf der
Punkteskala. Um die Begriffe nicht zu vermischen, heisst die hier gemeinte
Variante durchgehend **punktlineare Bin-Skala**, nie "entstaucht".

## par.4 Hypothese -- und die Beweislast, die auf ihr liegt

> Am heutigen Ziel bricht die Aufloesung des Verteilungskopfes dort
> zusammen, wo die Datenmasse liegt. Eine punktlineare Bin-Skala behebt das.

**Diese Hypothese steht schlechter da als im Entwurf angenommen** (par.2a).
Der Entwurf hielt sie fuer vorwaerts gerichtet, weil #12 angeblich am
Differenzziel lief und die Randvergroeberung dort kein Faktor gewesen waere.
Das war falsch: beide #12-Messungen liefen am eigenseitigen Ziel, unter
demselben `linspace(-1,1)` und, soweit die Korpora `bootstrap_value` trugen,
unter demselben TD-Blend. Der behauptete Defekt lag also bereits vor, und
die Messung kam flach heraus.

Damit traegt diese Prereg die Beweislast und nicht die Gegenhypothese. Sie
darf nur weiterlaufen, wenn die Vorpruefung par.6 beziffert, dass die
Datenmasse tatsaechlich in groben Bins liegt -- was die 83-%-Messung in
par.2a eher unwahrscheinlich macht, weil der TD-Blend die Ziele Richtung
null zieht, also in den feinen Bereich.

**Der stehende #12-Befund gehoert weiterhin nicht hierher.** Im belastbaren
Block (n=150) stand eine Marge von +2,25 gegen ein Partieergebnis von
151:149, also exakter Gleichstand. Positive Marge ohne Siegvorsprung heisst,
dass die Zusatzpunkte in ohnehin entschiedenen Partien anfielen. Das ist die
Signatur einer fehlenden **Schwelle in der Konsumption**, nicht einer zu
groben Bin-Skala; zustaendig ist `PREREG_saturating_score_utility.md`.

Gestrichen ist dabei die Ableitung des Entwurfs, die Durchschnittsmargen
3,76 und 2,25 entspraechen "z-Werten um 0,05 bis 0,08". Das war eine
Kategorie-Verwechslung: 3,76 und 2,25 sind **Arena-Margen zwischen zwei
Armen**, keine Zielwerte einzelner Partien. Der Zielwert je Partie hat die
volle Streuung des Endstands, nicht die eines Armmittelwerts.

Gegenhypothese, die die Vorpruefung ausdruecklich zulassen muss und die nach
par.2a die wahrscheinlichere ist: die Datenmasse liegt so weit innen, dass
die Randvergroeberung folgenlos ist.

## par.5 Arme

Genau ein Faktor gegen den Referenzarm. Alles andere bleibt am
Bestandsrezept.

| Arm | Aenderung |
|---|---|
| **R** Referenz | Bestandsrezept ohne Verteilungskopf |
| **T** tanh-Bins | `points-dist-bins 51`, Kanten wie heute (`linspace(-1,1)`) -- Replikation des bekannten Stands am HEUTIGEN, eigenseitigen Ziel |
| **P** punktlineare Bins | `points-dist-bins 51`, Kanten aequidistant in PUNKTEN ueber den empirisch belegten Bereich, danach durch tanh auf die Zielkoordinate abgebildet |

Arm T ist nicht verzichtbar, seine Begruendung aendert sich aber durch
par.2a. Nicht mehr: "trennt die Zielumstellung Differenz zu eigenseitig ab"
-- die hat es nie gegeben. Sondern: er repliziert den bekannten Stand unter
dem HEUTIGEN Korpus, heutigem Fenster, heutigem Rezept und ohne den
0,1-Gegner-Term. Ohne ihn waere ein Unterschied zwischen R und P nicht von
diesen Aera-Effekten trennbar, die im Projekt wiederholt groesser waren als
der jeweilige Knopf.

HL-Gauss-Sigma ist heute in **Bin-Breiten** definiert
(`train.py:196`: `sigma = POINTS_DIST_SIGMA * (edges[1] - edges[0])`). Bei
ungleichen Bin-Breiten muss festgelegt werden, ob Sigma je Bin mitwandert
oder global bleibt; siehe par.9.

## par.6 Vorpruefung als Tor (billig, offline, kein Training)

**Vor jedem Training.** Auf dem vorhandenen Korpus:

1. **Nicht** die Formel `tanh(own_total/50)` histogrammieren. Zu
   histogrammieren ist der Zielwert, den der Cache-Bau TATSAECHLICH
   erzeugt, also `points_val` nach allen Zweigen aus par.2a (rtv-Override,
   TD-Blend). Der Entwurf hatte hier die Formel stehen; das haette den
   Masseanteil in breiten Bins systematisch UEBERSCHAETZT, weil der TD-Blend
   die Ziele Richtung null zieht, und haette das 30-%-Tor faelschlich
   oeffnen koennen.
   Bezugsquelle ist dieselbe Codestelle, die trainiert
   (`neural_net.py:1640-1720`), nicht eine nachgebaute Formel -- sonst misst
   das Tor eine Groesse, die kein Training je gesehen hat.
2. Vorschaltung, eine Zeile: welche der Felder `round_transition_value` und
   `bootstrap_value` traegt der Korpus? Die Antwort entscheidet, welcher
   Zweig dominiert. Fuer den Bestand ist sie in par.2a gemessen (rtv nirgends,
   bootstrap ~83 %); fuer ein neues Korpus ist sie erneut zu erheben.
3. Je Bin die Breite in Punkten und die Belegung.
4. Die Kennzahl: **Anteil der Datenmasse in Bins, die breiter als 5 Punkte
   sind.**
5. Dieselbe Kennzahl zusaetzlich **getrennt nach Runde**. Runde 5 traegt
   das reine `tanh(own/50)`, alle anderen den Blend; ein gepoolter Wert
   verwischt genau den Unterschied, um den es geht.

Entscheidungsregeln, vorab festgelegt (unveraendert gegenueber dem Entwurf,
nur auf die richtige Groesse bezogen -- die Schwellen sind a priori gesetzt
und werden nicht nachtraeglich an das Ergebnis angepasst):

- **Anteil < 10 %**: Die Vergroeberung trifft die Daten kaum. Die Hypothese
  aus par.4 ist damit **widerlegt**, der Zuschnitt endet hier, und #12
  bleibt aus anderen Gruenden unterhalb der Aufloesung. Kein Training.
- **Anteil 10 bis 30 %**: Grenzfall. Entscheidung ueber die Trainingsarme
  liegt beim Nutzer.
- **Anteil > 30 %**: Die Hypothese ist plausibel und beziffert. Arme T und P
  werden gefahren.

Der gepoolte Wert entscheidet. Die Aufschluesselung nach Runde ist
mitzuberichten, aber kein zweiter Riegel -- sonst gaebe es zwei Tore und
damit Auswahlfreiheit im Nachhinein.

Diese Vorpruefung kostet eine Auswertung vorhandener Pickles. Sie kann die
ganze Wiederaufnahme fuer wenige Minuten Aufwand beenden, und genau dafuer
steht sie hier vorn.

## par.7 Entscheidungsmetrik der Trainingsarme

**Primaer: gepaarte Arena**, feste Paarzahl, **kein SPRT-Fruehstopp**.
Begruendung ist der Praezedenzfall dieses Kopfes selbst: `t12_dist` zeigte
SPRT-H1 mit 54:26 und war in der Replikation Seed-Rauschen. Ein
SPRT-Fruehstopp waere hier nicht nur unsauber, sondern nachweislich der
Fehler, der schon einmal passiert ist.

**Vorregistrierte Replikation:** Ein positiver Ausgang von Arm P zaehlt erst
nach einer Wiederholung mit frischem Seed-Satz. Ohne sie wird kein Verdikt
geschrieben. Diese Regel ist nicht neu, sie hat #12 beim letzten Mal vor
einem Fehlschluss bewahrt.

**Sekundaer, nur deskriptiv:** Brier auf dem Messset, Platt-B, und die
beiden Orakel-Metriken.

**Seed-Disziplin:** gepaarte Seeds, mindestens sechs. Der Seed bewegt die
Metrik um ein Vielfaches dessen, was ein einzelner Knopf bewegt.

## par.8 Was als Nicht-Erfolg gilt

- **Vorpruefung unter 10 %**: Hypothese widerlegt, Zuschnitt geschlossen.
- **P gegen T H0**: kein Beleg, dass die Bin-Skala der Engpass war. Der
  Zuschnitt ruht; #12 bleibt unterhalb der Aufloesung wie bisher.
- **P gegen T positiv, Replikation negativ**: derselbe Ausgang wie beim
  letzten Mal. Zu berichten als das, was es ist, und nicht zu
  reinterpretieren.
- **T weicht unerwartet stark von der #12-Historie ab**: dann dominiert ein
  Aera-Effekt (Korpus, Fenster, Rezept, Wegfall des 0,1-Gegner-Terms) und
  nicht die Bin-Skala. Eigener Befund, unabhaengig vom Ausgang von P zu
  berichten.
- **Der TD-Blend-Anteil im Korpus liegt deutlich unter den ~83 % aus
  par.2a**: dann gilt die Vorpruefung nicht mehr und ist zu wiederholen,
  bevor irgendein Arm gefahren wird.

## par.9 Offen, vor dem Bau zu entscheiden

- Der Punktebereich, ueber den die punktlinearen Kanten gelegt werden. Aus
  der Vorpruefung abzuleiten, nicht zu raten.
- HL-Gauss-Sigma bei ungleichen Bin-Breiten: mitwandernd je Bin oder global.
- Ob dieselbe Frage auch fuer den `opp_points`-Kopf gilt, falls er je
  verteilungsfoermig wird.
- Ob eine punktlineare Skala am TD-Blend ueberhaupt die richtige Antwort
  waere. Der Blend mischt zwei Groessen verschiedener Natur (Punkte-tanh und
  remappte Gewinnwahrscheinlichkeit) in EINE Koordinate; "aequidistant in
  Punkten" ist fuer den Wahrscheinlichkeits-Anteil ohne Bedeutung. Faellt
  das Tor positiv aus, ist diese Frage vor Arm P zu klaeren.

Bereits beantwortet, hier nur zur Sicherung: die Bin-Kanten liegen heute
schon als `register_buffer` im `state_dict` (`neural_net.py:2412-2413`),
Alt-Checkpoints bringen ihre eigene Skala also mit und bleiben ladbar. Das
war im Entwurf als offene Frage gefuehrt.

## par.10 Verhaeltnis zu den Nachbar-Zuschnitten

- **Task #12 / `PREREG_post34_package.md` Arm 1**: derselbe Kopf, neuer
  Faktor. Diese Prereg eroeffnet ihn nicht generell wieder, sondern prueft
  genau eine bisher ungemessene Bedingung.
- **`PREREG_saturating_score_utility.md`** (Ausarbeitung: Idee 1.1 in
  `research_value_head_alternatives_DRAFT.md`): die dortige These ist, dass
  nicht die Kopf-Architektur, sondern die **Konsumption** der offene Hebel
  ist. Beide Thesen schliessen einander nicht aus: eine vergroeberte
  Verteilung waere auch fuer eine gesaettigte, integrierte Utility ein
  schlechter Eingang. Faellt die Vorpruefung positiv aus, ist diese Prereg
  die guenstigere Vorstufe. Der TD-Blend-Befund aus par.2a betrifft beide
  Zuschnitte und ist dort als par.3a-Tor registriert.
- **`PREREG_score_correlation.md`**: unabhaengig. Dort geht es um die
  Notwendigkeit eines Differenzkopfes, hier um die Aufloesung eines
  vorhandenen.
