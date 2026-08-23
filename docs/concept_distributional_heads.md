# Konzept: Verteilungsköpfe, Risiko in der Suche, gerichtetes Self-Play

Stand 2026-08-23. Entstanden aus einem Entwurf ("Value-Kopf raus, ersetzt
durch Punkte-Kopf und Gegner-Kopf, dazu Wahrscheinlichkeiten und ein
Aggressivitäts-Knopf"), drei externen Durchsichten und einem Abgleich mit
der Projekthistorie.

Der Abgleich hat den Entwurf zum größeren Teil erledigt: fast jeder
Baustein war bereits gebaut und gemessen. Dieses Dokument hält fest, **was
gemessen ist**, **was davon offen bleibt** und **welche vier
Vorregistrierungen daraus entstanden sind**. Es ist kein Bauplan.

---

## 1. Die Value-Hälfte ist gemessen, nicht offen

| Vorschlag | Stand im Projekt |
|---|---|
| Verteilungskopf auf die Punktedifferenz | **Task #12**, 2026-07-29: 51-Bin C51/HL-Gauss über die tanh-gestauchte Punktedifferenz. Offline schlechter (R² 0,0906 gegen 0,1160), Arena gepoolt p=0,1046. `POINTS_DIST_BINS` bleibt 0, Code inert erhalten |
| Derselbe Kopf **neben** einem Sieg-Kopf | **Nach-#34-Paket Arm 1** (`t12_dist`), vorregistriert mit genau dieser Begründung. Erst SPRT-H1 mit 54:26, in der vorregistrierten Frisch-Seed-Replikation als Seed-Rauschen entlarvt (206:194 und 181:179). Geschlossen |
| Punkte-/Gegner-Nutzen in der Suche | `POINTS_UTILITY_WEIGHT` 0,5 → 1:14, 1,0 → 0:12 (2026-07-19). Später w=0,1 gegen w=0: 300/400 gegen 321/400, Block-t −2,68 |
| Aggressions-Knopf über Gegner-Gewicht | Drei Preregs, alle H0: `task28_aggression` (bester −6,16 Gegnerpunkte, p=0,078), `aggression_remapping` (alle drei Arme), `aggression_style_measurement` (Blend inert) |
| Mehrfach-Determinisierung, Mittelung über Welten | **Geschlossen negativ 2026-08-10**: k=1/2/4 ergibt 76,0/77,3/70,0 % bei festem Budget und 81,75/77,0/73,0 % bei mit k wachsendem Budget. Wortlaut: das Mitteln über gezogene Welten **schadet aktiv** |
| Quantil-Darstellung im Baum | Als Idee 1.4 im Recherche-Dokument bewertet und ausdrücklich **nicht empfohlen** mangels Präzedenz |
| Ziel "Erreichbarkeit" statt "Eintreten" | `PREREG_reachability_target.md` par.16: NICHT-ERFOLG. Wortlaut: das Ziel ist nicht der Engpass, **es bleibt die Policy-Seite** |
| Eigener Plattenkopf | 2026-08-10 gebaut und wieder entfernt |

Zwei Einschränkungen, damit daraus nicht mehr gelesen wird als drinsteht.
Die Auflösungsregel des Nach-#34-Pakets hält ausdrücklich fest, dass ein H0
"kein Beleg" bedeutet und **nicht "widerlegt"**. Und die 51 Bins liefen über
die tanh-gestauchte Differenz; eine andere Bin-Skala ist nicht gemessen.

---

## 2. Der Befund, der alles trägt

Ein Ergebnis aus Task #12 hat überlebt und ist der interessanteste Punkt der
ganzen Akte. Im belastbaren Arena-Block (n=150; Block 1 hatte n=75 mit
SPRT-Stopp, und die Projektlehre dazu lautet "n≤75 ist Kontext, keine
Referenz"):

| Größe | Wert |
|---|---|
| Durchschnittsmarge dist gegen v18 | **+2,25** (39,27 gegen 37,02) |
| Partieergebnis | **151:149** |

Das sind **keine Zusatzpunkte obendrauf**, sondern die Marge gegen denselben
Gegner in denselben Partien. Positive Durchschnittsmarge bei exaktem
Gleichstand heißt: der Arm gewinnt größer, wenn er gewinnt. Die Zusatzpunkte
fallen in ohnehin entschiedenen Partien an, und dort sind sie wertlos.

Damit ist es keine ungehobene Frucht, sondern die **Signatur einer fehlenden
Schwelle**: ein Kopf, der auf die Punktedifferenz trainiert und als
Erwartungswert konsumiert wird, maximiert Marge und kennt keine
Entscheidungsschwelle. In beiden Läufen, am alten wie am WDL-Ziel, wurde die
Verteilung ausschließlich als Erwartungswert konsumiert; im Nach-#34-Paket
sogar per ausdrücklichem Entscheid ("Blend bleibt überall AUS, w=0"). Die
Verteilung war zweimal im Netz und **nie** in der Suche.

### Und die schärfere Diagnose

Der naheliegende Schluss lautet, dem heutigen Blend fehle die Sättigung. Das
stimmt so nicht. `tanh(Punkte/50)` **ist** eine Sättigungsfunktion – sie
sättigt nur um **null Punkte**. Seit Schema 20 ist das Punkte-Ziel
eigenseitig, und reale eigene Endstände liegen damit im flachen Bereich:

| Eigener Punktestand | Empfindlichkeit je Punkt |
|---|---|
| 0 | 0,0200 |
| 55 | 0,0072 |
| 70 | 0,0043 |

Über die realistische Spanne von 40 bis 70 Punkten bewegt sich der Term auf
der [0,1]-Skala nur von 0,832 auf 0,943. Bei w=0,1 sind das höchstens 0,011
Variation, während der Sieg-Term den vollen Bereich abdeckt. Der gescheiterte
Blend ist damit zwanglos erklärt, ohne jede Sättigungstheorie: der
Punkte-Term war fast konstant, hat kaum unterschieden und dafür einen
gegner-blinden Versatz eingetragen.

**Es fehlt also nicht die Sättigung, sondern die Re-Zentrierung.** KataGos
arctan-Utility sättigt um den bei jeder Suche neu gesetzten vorhergesagten
Wurzel-Score; der steile Bereich liegt dort immer da, wo die Partie gerade
steht.

---

## 3. Was daraus vorregistriert wurde

| Prereg | Frage | Kosten bis zum ersten Verdikt |
|---|---|---|
| `PREREG_score_correlation.md` | Wie stark sind eigener und gegnerischer Endstand tatsächlich korreliert, und wie groß ist der Fehler der Unabhängigkeitsannahme in P(Sieg)? | Auswertung vorhandener Pickles, kein Training, keine Arena |
| `PREREG_points_dist_bin_scale.md` | Bricht die Auflösung des Verteilungskopfes am heutigen, eigenseitigen Ziel dort zusammen, wo die Datenmasse liegt? | Offline-Tor, Minuten; Trainingsarme nur bei positivem Tor |
| `PREREG_saturating_score_utility.md` | Verwandelt eine re-zentrierte, gesättigte, über die Verteilung integrierte Score-Utility die gemessene Marge in Siege? | Engine-Umbau plus Arena; der teuerste Value-seitige Zuschnitt |
| `PREREG_uncertainty_guided_selfplay.md` | Bringt es Stärke, Self-Play-Startstellungen dort zu wählen, wo das Netz unsicher ist **und** die Unsicherheit die Zugwahl kippen kann? | Tor G (nur messend) vor jedem Eingriff; danach Zyklus-Kosten |

Die ersten drei betreffen die Value-Seite, der vierte die Policy-Seite.
`score_correlation` und `points_dist_bin_scale` können jeweils für sehr
wenig Aufwand ihre eigene These erledigen und stehen deshalb vorn.

### Zusammenhänge zwischen ihnen

- `saturating_score_utility` braucht eine **Streuung**, die es im Netz
  nirgends gibt. Weg S ist ein `sigma`-Kopf per
  Selbst-Vorhersage-Regularisierer, Weg V eine wiederbelebte
  Bin-Verteilung. Weg V hängt am Tor von `points_dist_bin_scale`: eine
  Verteilung mit 5 bis 20 Punkte breiten Bins wäre auch für eine gesättigte
  Utility ein schlechter Eingang.
- `score_correlation` prüft die Voraussetzung eines eigenen Differenzkopfes
  und ist von den anderen unabhängig.
- `uncertainty_guided_selfplay` ist die einzige Hälfte ohne Vorläufer im
  Projekt. Sie dockt an `PREREG_start_position_seeding.md` par.4d an (erstes
  positives Zustandssignal, Tau +0,14 gegen −0,19, p=0,017) und an die
  wiederholte Feststellung, dass der Engpass auf der Policy-Seite liegt.

---

## 4. Zwei Unterscheidungen, die im Entwurf gefehlt haben

Sie stehen hier, weil sie in jedem Nachfolgedokument wieder gebraucht werden.

**Vorhersageverteilung, nicht Konfidenzintervall.** Was ein Verteilungskopf
ausgibt, ist die Streuung eines zukünftigen Ergebnisses, nicht die
Unsicherheit einer Schätzung. Der Begriff "Konfidenzintervall" ist dafür
falsch und reißt die folgende Trennung sprachlich wieder ein.

**Aleatorisch gegen epistemisch.** Die Breite der Vorhersage kommt aus dem
Spiel (Fabriken, Chips, Kuppelplatten, Gegnerzug) und schrumpft mit jeder
Runde. Sie beantwortet **nicht** die Frage, ob das Netz eine Stellung kennt.
Ein Verfahren, das für die Datenauswahl auf die Vorhersagebreite schaut,
sucht gezielt die zufälligsten Stellungen der Partie auf, also die mit dem
geringsten Lernwert – und sieht dabei wie gerichtete Exploration aus. Für
"kennt das Netz das schon" braucht es eine zweite Quelle (Modell-Uneinigkeit).

Ergänzend, aus derselben Familie: **Unsicherheit allein ist kein
Informationsgewinn.** Relevant ist Unsicherheit dort, wo sie eine
Entscheidung ändern kann. Bester Zug +40 gegen zweitbesten +5 bei Streuung 2
ist unsicher und vollkommen folgenlos.

---

## 5. Was gestrichen wurde, und warum

Aus dem ursprünglichen Entwurf sind gefallen: die drei Verteilungsköpfe als
Neubau (Task #12, zweimal gemessen), der Risiko-Knopf in Quantil-Form (drei
Aggressions-Preregs H0, Quantil-Form im Recherche-Dokument nicht empfohlen),
Zufallsknoten über gezogene Welten (geschlossen negativ, schadet aktiv), die
Plattenkanäle (Kopf gebaut und entfernt, Ziel gemessen und nicht der
Engpass) sowie die Debatte Quantilvektor gegen Momente im Suchbaum – die
entsteht nur bei der Quantil-Form und entfällt bei der Utility-Form, weil
eine gesättigte Utility gegen eine Normalverteilung integriert wird und
genau zwei Momente braucht.

---

## Anmerkung zur Belegbarkeit

Die Zahlen in Abschnitt 1 und 2 stammen aus `archive/history.md`,
`evaluations/PREREG_INDEX.md`, `evaluations/PREREG_post34_package.md` und
`evaluations/research_value_head_alternatives_DRAFT.md`. Die Codestellen in
Abschnitt 2 (`value_to_win_prob`, `blended_leaf_win_prob_with`) sind direkt
gelesen; `VALUE_SCALE = 50` stammt aus einer Agenten-Kartierung und ist
nicht zeilenweise nachgeprüft.

Ausdrücklich offen geblieben: ob es zu den Bootstrap- und
Unsicherheits-Ideen einen älteren, anders benannten Vorläufer im Projekt
gibt. Die Suche danach war negativ, aber nicht erschöpfend.
