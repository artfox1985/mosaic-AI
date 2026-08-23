<!-- STATUS: OFFEN | Frage: Blieb der Verteilungs-Punkte-Kopf (Task #12) unterhalb der Aufloesung, weil seine Bins aequidistant im tanh-Raum liegen und damit im Punkteraum an den Raendern um Faktor 5-25 groeber werden -- und aendert eine punktlineare Bin-Skala das? | Beleg: nichts gebaut, Entwurf angelegt 2026-08-23; Bin-Kanten `torch.linspace(-1,1,bins+1)` in `engine/py/neural_net.py:2411` in dieser Sitzung gelesen, Vorpruefung par.6 ist Tor -->

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
`VALUE_SCALE = 50,0` (Agenten-Kartierung, in dieser Sitzung nicht
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

**Der Punkt, der die Wiederaufnahme rechtfertigt:** Seit Schema 20
(`PREREG_points_head_epsilon.md`, entschieden 2026-08-10) ist das
Punkte-Ziel **rein eigenseitig**, `tanh(own_total / 50)`, nicht mehr die
Differenz. Eigene Endstaende liegen typischerweise dort, wo z zwischen 0,7
und 0,9 liegt, also mitten in der Kompressionszone (Bin-Breite 4 bis 10
Punkte). Differenzen dagegen sind um null zentriert, also im feinen
Bereich (Bin-Breite rund 2 Punkte).

Daraus folgt eine unbequeme Konsequenz: **eine schlichte Wiederholung von
#12 mit dem heutigen Ziel waere schlechter als die Originalmessung**, nicht
besser. Die Kompression trifft das eigenseitige Ziel haerter als das
Differenzziel, unter dem #12 urspruenglich gemessen wurde.

## par.3 Begriffsklaerung: das ist NICHT die Platt-Entstauchung

Im Projekt ist "entstauchen" bereits belegt: `_destretch_prob`
(`engine/py/neural_net.py:675`, A = 0,0051, B = 1,9269) streckt eine
**Wahrscheinlichkeit** und wird auf das WDL-Bootstrap-Ziel angewandt
(`--wdl-bootstrap-destretch`, Arm B in `PREREG_task34_erosion_arms.md`).

Hier geht es um etwas anderes: um die **Lage der Bin-Kanten** auf der
Punkteskala. Um die Begriffe nicht zu vermischen, heisst die hier gemeinte
Variante durchgehend **punktlineare Bin-Skala**, nie "entstaucht".

## par.4 Hypothese -- und was sie ausdruecklich NICHT erklaert

> Am **heutigen, eigenseitigen** Ziel bricht die Aufloesung des
> Verteilungskopfes genau dort zusammen, wo die Datenmasse liegt. Eine
> punktlineare Bin-Skala behebt das.

**Diese Hypothese erklaert die beiden #12-Messungen nicht, und das ist
wichtig.** #12 lief am Differenzziel. Punktedifferenzen sind um null
zentriert; die gemessenen Durchschnittsmargen lagen bei 3,76 und 2,25
Punkten, das entspricht z-Werten um 0,05 bis 0,08 und damit dem feinsten
Bereich der Skala (Bin-Breite rund 2 Punkte). Die Randvergroeberung war dort
also **kein** Faktor.

Der stehende #12-Befund hat eine andere und bereits identifizierte Ursache:
im belastbaren Block (n=150) stand eine Marge von +2,25 gegen ein
Partieergebnis von 151:149, also exakter Gleichstand. Positive Marge ohne
Siegvorsprung heisst, dass die Zusatzpunkte in ohnehin entschiedenen Partien
anfielen. Das ist die Signatur einer fehlenden **Saettigung** in der
Konsumption, nicht einer zu groben Bin-Skala, und der zustaendige Zuschnitt
dafuer ist `research_value_head_alternatives_DRAFT.md` Idee 1.1.

Diese Prereg ist damit **vorwaerts gerichtet**: sie behauptet nicht, die
Vergangenheit zu erklaeren, sondern verhindert, dass eine Wiederaufnahme des
Kopfes am heutigen Ziel an einem Fehler scheitert, den #12 noch gar nicht
hatte.

Gegenhypothese, die die Vorpruefung ausdruecklich zulassen muss: die
Datenmasse liegt auch am eigenseitigen Ziel so weit innen, dass die
Randvergroeberung folgenlos ist.

## par.5 Arme

Genau ein Faktor gegen den Referenzarm. Alles andere bleibt am
Bestandsrezept.

| Arm | Aenderung |
|---|---|
| **R** Referenz | Bestandsrezept ohne Verteilungskopf |
| **T** tanh-Bins | `points-dist-bins 51`, Kanten wie heute (`linspace(-1,1)`) -- Replikation des bekannten Stands am HEUTIGEN, eigenseitigen Ziel |
| **P** punktlineare Bins | `points-dist-bins 51`, Kanten aequidistant in PUNKTEN ueber den empirisch belegten Bereich, danach durch tanh auf die Zielkoordinate abgebildet |

Arm T ist nicht verzichtbar. Ohne ihn waere ein Unterschied zwischen R und P
nicht von der Zielumstellung (Differenz zu eigenseitig) trennbar, die seit
#12 stattgefunden hat.

HL-Gauss-Sigma ist heute in **Bin-Breiten** definiert
(`train.py:196`: `sigma = POINTS_DIST_SIGMA * (edges[1] - edges[0])`). Bei
ungleichen Bin-Breiten muss festgelegt werden, ob Sigma je Bin mitwandert
oder global bleibt; siehe par.9.

## par.6 Vorpruefung als Tor (billig, offline, kein Training)

**Vor jedem Training.** Auf dem vorhandenen Korpus:

1. Histogramm der Zielwerte `tanh(own_total/50)` ueber die 51 heutigen Bins.
2. Je Bin die Breite in Punkten und die Belegung.
3. Die Kennzahl: **Anteil der Datenmasse in Bins, die breiter als 5 Punkte
   sind.**

Entscheidungsregeln, vorab festgelegt:

- **Anteil < 10 %**: Die Vergroeberung trifft die Daten kaum. Die Hypothese
  aus par.4 ist damit **widerlegt**, der Zuschnitt endet hier, und #12
  bleibt aus anderen Gruenden unterhalb der Aufloesung. Kein Training.
- **Anteil 10 bis 30 %**: Grenzfall. Entscheidung ueber die Trainingsarme
  liegt beim Nutzer.
- **Anteil > 30 %**: Die Hypothese ist plausibel und beziffert. Arme T und P
  werden gefahren.

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
- **T weicht unerwartet stark von der #12-Historie ab**: dann ist die
  Zielumstellung (Differenz zu eigenseitig) der dominierende Faktor und
  nicht die Bin-Skala. Eigener Befund, unabhaengig vom Ausgang von P zu
  berichten.

## par.9 Offen, vor dem Bau zu entscheiden

- Der Punktebereich, ueber den die punktlinearen Kanten gelegt werden. Aus
  der Vorpruefung abzuleiten, nicht zu raten.
- HL-Gauss-Sigma bei ungleichen Bin-Breiten: mitwandernd je Bin oder global.
- Ob dieselbe Frage auch fuer den `opp_points`-Kopf gilt, falls er je
  verteilungsfoermig wird.
- Ob die Bin-Kanten als Puffer im Checkpoint liegen bleiben (heute
  `register_buffer`), damit Alt-Checkpoints ihre eigene Skala mitbringen und
  ladbar bleiben.

## par.10 Verhaeltnis zu den Nachbar-Zuschnitten

- **Task #12 / `PREREG_post34_package.md` Arm 1**: derselbe Kopf, neuer
  Faktor. Diese Prereg eroeffnet ihn nicht generell wieder, sondern prueft
  genau eine bisher ungemessene Bedingung.
- **`research_value_head_alternatives_DRAFT.md` Idee 1.1**: die dortige
  These ist, dass nicht die Kopf-Architektur, sondern die **Konsumption**
  der offene Hebel ist. Beide Thesen schliessen einander nicht aus: eine
  vergroeberte Verteilung waere auch fuer eine gesaettigte, integrierte
  Utility ein schlechter Eingang. Faellt die Vorpruefung positiv aus, ist
  diese Prereg die guenstigere Vorstufe zu Idee 1.1.
- **`PREREG_score_correlation.md`**: unabhaengig. Dort geht es um die
  Notwendigkeit eines Differenzkopfes, hier um die Aufloesung eines
  vorhandenen.
