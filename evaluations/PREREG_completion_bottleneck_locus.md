<!-- STATUS: OFFEN | Frage: Warum ist der k1-Gewinn des Suchhebels GEGNERSPEZIFISCH (gegen die Heuristik +7,0 pp, netz-gegen-netz exakt null) -- und wirkt der Hebel upstream auf die Reihenwahl oder nur auf die Endplatzierung? | Beleg: nichts gemessen, angelegt 2026-08-23, am 2026-08-24 per par.1a AMENDMENT umgestellt. Anlass war die Legalitaets-Stufe 0/160 (Vollendung nie legal moeglich, 54 Prozent Blockade = Musterreihe nicht voll) plus der Implicit-Minimax-Sprung k1 9,0 auf 16,0 Prozent. Dann kam die Netz-gegen-Netz-Fassung: Paritaet 400/814 und k1 30/312 auf beiden Seiten, identische Zaehler -- der Effekt uebertraegt sich NICHT. Damit ist die urspruengliche Locus-Frage vorab geschwaecht und die Gegnerspezifitaet die neue Primaerfrage (par.3a: Schlupf gegen Konkurrenz, unterschieden ueber die Blockade-Zusammensetzung je Gegnerklasse). Der Zuschnitt erzeugt KEINE Partien: alle drei Artefakte liegen vollstaendig geloggt vor -->

# Vorregistrierung: Wo sitzt der Vollendungs-Engpass, in der Suche oder im Ziel?

**Angelegt 2026-08-23, VOR jeder Messung.**

## par.1 Anlass

Drei Ebenen sind durchgemessen, und alle drei zeigen upstream. Was fehlt,
ist die Trennung der letzten Gabelung.

1. **Die Vollendungen waren nie moeglich.** Legalitaets-Stufe (2026-08-23,
   `tools/probes/column_completion_legality_probe.py`): in **0 von 160**
   stehengelassenen Hoehe-5-Faellen existierte im Restfenster eine legale
   Platzierung, die die Spalte vollendet haette. Der Champion verpasst
   nichts am Ende. **Wichtig fuer par.1a: 128 dieser 160 Faelle stammen aus
   NETZ-GEGEN-NETZ-Partien** (nur 18 bzw. 14 aus dem Heuristik-Lauf), und
   die Quote ist in jeder Gruppe 0 -- der Befund steht also bereits unter
   der strengen Gegnerbedingung.
2. **Die Reihenpraeferenz ist flach.** Der Champion zieht 55,5-56,1 % seiner
   Draft-Ziele auf die kurzen Musterreihen 1-3 und meidet 5/6 (12-13 %),
   **ohne jede Spaetrunden-Anpassung**. Der Heuristik-Lehrer macht das
   Gegenteil: Kurz-Anteil 46,0 % (R1-2) auf 33,4 % (R4-5), Reihe 6 spaet am
   haeufigsten (19,1 %). Der Bias ist nicht geerbt.
3. **Eine reine SUCHAENDERUNG hat k1 bewegt -- aber nur gegen die
   HEURISTIK.** Implicit-Minimax-Backup gegen Heuristik: k1 von 9,0 % auf
   16,0 % (+7,0 pp, p=0,090), bei unveraendertem Netz, Ziel und Korpus.
   k1 ist das Spalten-Kriterium (`docs/knobs.md:61`, `MOSAIC_SPALTENBAU` =
   "Spaltenbauer-Vorzugsschicht (Kriterium 1)").

## par.1a AMENDMENT 2026-08-24: der k1-Effekt ist gegnerspezifisch

**Vor jeder Messung dieses Zuschnitts nachgetragen**, Meldung der
Parallelsitzung, registriert in `PREREG_agent_encapsulation.md` par.6b mit
Querverweis `PREREG_implicit_minimax_backup.md` par.2c.

Die Netz-gegen-Netz-Fassung derselben Messung ist gefahren
(`paired_arena_env_imm_netvnet.json` und `..._swap.json`, 407 Seeds je
Datei, 400/400 Sims, per-Seite-Specs `champion_imm_a02` gegen
`champion_frozen`, beide Dateien vollstaendig geloggt -- 407/407, am
2026-08-24 nachgezaehlt):

| | Ergebnis |
|---|---|
| Partien | 201/407 und 199/407 = **400/814 (49,1 %)**, n.s. -- **Paritaet** |
| k1 | alpha **30/312 = 9,6 %** gegen frozen **30/312 = 9,6 %** -- identische Zaehler |

**Der +7,0-pp-Befund uebertraegt sich NICHT auf einen gleich starken
Gegner.** Damit faellt die Praemisse, auf der dieser Zuschnitt gebaut war:
es gibt netz-gegen-netz keinen Sucheffekt, dessen Ort noch zu bestimmen
waere.

**Was das fuer die Lesarten heisst -- ehrlich, vor der Messung:**

- Die **Such-Lesart** ist damit vorab geschwaecht. Wenn k1 sich um exakt
  null bewegt, ist auch von der Reihenwahl kaum Bewegung zu erwarten. Ein
  `Delta_M − Delta_R` nahe null waere nach par.7 die Ziel-Lesart -- aber es
  waere eine **schwache Bestaetigung**, weil der Arm ueberhaupt nichts
  bewegt hat, nicht weil er die Zufuehrung nicht erreicht.
- Die Entscheidungsregeln in par.7 bleiben unveraendert stehen. Sie sind
  vorregistriert und werden nicht nachtraeglich an die neue Lage angepasst.
  Aber ihr **Aussagewert** ist mit diesem Amendment kleiner geworden, und
  das ist beim Berichten dazuzusagen.

**Die interessantere Frage, die dadurch aufgeht** (siehe par.3a): warum ist
der k1-Gewinn gegnerspezifisch?

## par.2 Die Gabelung

Befund 3 sagt: die Suche kann etwas, das sie vorher nicht konnte, und es
schlaegt auf das Spaltenkriterium durch. Befund 1 und 2 sagen: der Engpass
liegt in der Zufuehrung, Runden vorher.

**Ungeklaert ist, ob das dasselbe ist.** Zwei Lesarten, beide mit den
vorliegenden Daten vereinbar:

- **Such-Lesart.** Die lange Linie war im Baum nicht ausdrueckbar. Mit dem
  Minimax-Backup wird sie es, und das wirkt bis in die Reihenwahl zurueck:
  der Arm faengt an, spaet lange Reihen zu fuettern. Dann ist der
  Kredit-Horizont-Verdacht in seiner POLICY-Form bestaetigt (nicht in der
  Label-Form, die Stufe 0 widerlegt hat).
- **Ziel-Lesart.** Der Minimax-Effekt sitzt nur in der Endplatzierung: aus
  dem, was ohnehin auf dem Brett liegt, wird mehr herausgeholt. Die
  Reihenwahl bleibt flach. Dann ist der Engpass die gelernte
  Randverteilung, und Hebel muessen ans ZIEL, nicht an die Suche.

Beide Ausgaenge aendern, was als Naechstes gebaut wuerde. Das ist der Grund
fuer diesen Zuschnitt.

## par.3 Warum das nichts kostet

Beide Sonden sind gebaut (`row_preference_probe.py`,
`column_completion_legality_probe.py`), der Knopf ist gebaut und abgenommen
(Welle 1, per-Seite-Spec).

**Und die Partien EXISTIEREN bereits** (Stand 2026-08-24, korrigiert
gegenueber dem Entwurf, der sie noch erwartete): die par.6a-Messung ist
gefahren, mit `--log-games`, drei Artefakte mit vollstaendigen Logs --
`paired_arena_env_imm_netvnet.json`, `..._swap.json` (je 407/407) und
`paired_arena_env_imm_a02.json` (gegen die Heuristik, Arme 0 und 0,2).

**Dieser Zuschnitt erzeugt damit keine einzige Partie.** Er ist reine
Auswertung vorhandener Artefakte und kostet Minuten.

## par.3a Die neue Primaerfrage: warum ist der Effekt gegnerspezifisch?

Nachgetragen mit par.1a. Zwei Mechanismen, beide mit den vorliegenden Daten
vereinbar, beide aus den VORHANDENEN Logs trennbar:

- **Schlupf-Hypothese.** Gegen die Heuristik gewinnt der Champion 74-80 %;
  viele Partien sind entschieden. Spaltenbau ist dann ein Luxus, den man
  sich leisten kann. Gegen einen gleich starken Gegner gibt es diesen
  Schlupf nicht.
- **Konkurrenz-Hypothese.** Ein gleich starker Gegner konkurriert um
  DIESELBEN Kacheln. Lange Musterreihen lassen sich dann nicht mehr fuellen
  -- und genau das ist der groesste Blockadeposten der Legalitaets-Stufe
  (Musterreihe nicht voll, 87 von 160). Dann waere die Vollendungsschwaeche
  zum Teil **kompetitiv** und nicht rein intern.

**Der unterscheidende Test kostet nichts Neues:** die Legalitaets-Sonde
liefert die Blockade-Zusammensetzung bereits. Sie ist auf BEIDE
Gegnerklassen zu fahren -- gegen die Heuristik (`imm_a02`) und
netz-gegen-netz (`imm_netvnet` plus `_swap`) -- und die Zusammensetzung zu
vergleichen.

Vorab festgelegte Lesart:

- **Anteil "Musterreihe nicht voll" netz-gegen-netz deutlich hoeher als
  gegen die Heuristik:** Konkurrenz-Hypothese gestuetzt. Die
  Vollendungsschwaeche ist zum Teil eine Eigenschaft des GEGNERS, nicht nur
  des Agenten, und jede kuenftige Messung gegen die Heuristik ueberschaetzt
  systematisch, was ein Hebel bringt.
- **Zusammensetzung praktisch gleich:** Konkurrenz-Hypothese aus. Dann ist
  die Gegnerspezifitaet des k1-Effekts anderswo begruendet, und die
  Schlupf-Hypothese bleibt.

### par.3b ERGEBNIS (2026-08-24): Konkurrenz-Hypothese NICHT gestuetzt, Test unterversorgt

Der Test war billiger als registriert -- die Zusammensetzung liegt je
Gruppe fertig im Artefakt (`column_completion_legality_probe.json`, Feld
`blockadegruende` je Tabellenzeile). Kein neuer Lauf, keine neue Sonde,
reine Arithmetik auf vorhandenen Daten. Gerechnet 2026-08-24:

| Gruppe | n | Musterreihe nicht voll | Spezialfeld | keine Farbe |
|---|---|---|---|---|
| `champion_netvnet` / Champion | 128 | **51,6 %** (66) | 26,6 % (34) | 21,9 % (28) |
| `imm_a02` / Champion | 18 | **72,2 %** (13) | 16,7 % (3) | 11,1 % (2) |
| `imm_a02` / Heuristik | 14 | 57,1 % (8) | 28,6 % (4) | 14,3 % (2) |

**Verdikt: keiner der beiden vorregistrierten Zweige trifft zu, und das ist
so zu berichten.** Der Anteil ist netz-gegen-netz nicht hoeher, sondern
**20,7 pp NIEDRIGER** -- also gegen die Richtung der Konkurrenz-Hypothese.
Signifikant ist er aber nicht (z=+1,81, zweiseitig p~0,07), und das
95-%-Band der kleinen Gruppe allein ist ±20,7 pp, also so breit wie der
Effekt selbst.

**Konkurrenz-Hypothese damit nicht gestuetzt.** Sie ist nicht widerlegt --
dafuer traegt n=18 nicht --, aber sie hat kein Argument mehr. Die
Schlupf-Hypothese bleibt als einzige stehen und ist ungetestet.

**Konstruktionsfehler, offen benannt:** der Diskriminator haengt an den
Heuristik-Gruppen, und die haben n=18 und n=14. Das haette ich vor dem
Registrieren am Artefakt nachsehen koennen und muessen; der Hinweis kam von
der Parallelsitzung. Wer die Frage ernsthaft entscheiden will, braucht mehr
Gap-Ereignisse auf der Heuristik-Seite (mehr Partien gegen die Heuristik,
geloggt) oder einen anderen Diskriminator -- nicht dieselbe Rechnung noch
einmal.

Diese Frage war ab par.1a die **primaere** dieses Zuschnitts und ist damit
so weit beantwortet, wie die Daten es zulassen. Die urspruengliche
Locus-Frage laeuft als sekundaere mit -- sie kostet auf denselben
Artefakten nichts extra.

## par.4 Arme

Genau ein Faktor, geerbt aus der Alpha-Messung.

| Arm | Inhalt |
|---|---|
| **R** | Champion, `alpha = 0` (Bestandsverhalten) |
| **M** | Champion, `alpha = 0,2`, per-Seite-Spec |

Der Gegner ist in BEIDEN Armen derselbe (der eingefrorene Champion mit
`alpha = 0`) und auf denselben Seeds. Gemessen wird ausschliesslich das
Verhalten der ARM-Seite. Ohne diese Festlegung waere eine
Verhaltensaenderung nicht von einer Gegneraenderung trennbar.

## par.5 Primaermetrik, vorab festgelegt

**Die Rundenabhaengigkeit des Kurzreihen-Anteils**, nicht sein Niveau:

```
Delta = Kurzanteil(R1-2) − Kurzanteil(R4-5)
```

Kurzanteil = Anteil der Draft-Ziele auf Musterreihen 1-3, wie ihn
`row_preference_probe.py` bereits bildet.

Bezugswerte aus dem Bestand:

| Spieler | Kurzanteil R1-2 | Kurzanteil R4-5 | Delta |
|---|---|---|---|
| Champion heute | flach 55,5-56,1 % ueber alle Runden | dito | **~0 pp** |
| Heuristik-Lehrer | 46,0 % | 33,4 % | **+12,6 pp** |

Begruendung der Wahl: das Niveau kann sich aus vielen Gruenden verschieben,
die Rundenabhaengigkeit nicht. Sie ist die Signatur einer BERECHNETEN
Reihenwahl gegenueber einem gelernten Prior, und genau das ist die Frage.

**Auswertung auf Block-Ebene** (je Partie, dann ueber Partien
gebootstrapt), nicht auf Entscheidungs-Ebene. Im Projekt sind Paar-SEs schon
einmal massiv unterschaetzt worden.

## par.6 Sekundaermetriken

Deskriptiv, kein Tor:

- **Blockade-Zusammensetzung** der Legalitaets-Sonde. Bestand: Musterreihe
  nicht voll 87/160 (54 %), Zielfeld Spezialfeld 41 (26 %), keine passende
  Farbe 32 (20 %). Faellt der erste Posten, ist das die Zufuehrungs-Wirkung;
  faellt nur der dritte, ist es Farbrouting.
- **Stehengelassene Hoehe-5-Spalten je Partie.** Bestand 0,55. Ausdruecklich
  ein SYMPTOM-Mass, kein Tor -- so ist es im Strukturbefund registriert.
- **k1-Baurate.** Zur Anbindung an die +7,0-pp-Messung.

Dazu die sechs Standard-Kennzahlen je Seite (CLAUDE.md): Reihenauslastung,
Spaltenauslastung, Strafleistenauslastung, Punkte je Wertungsplatte, eigene
Punkte, Marge zum Gegner. Sie fallen bei `--log-games` ohnehin an.

**Die Strafleistenauslastung ist hier nicht Beiwerk.** Lange Reihen tragen
Ueberlaufrisiko; liegt der Champion dort deutlich unter dem Lehrer, ist
Straf-Aversion ein eigenstaendiger Kandidat fuer die flache
Kurzreihen-Praeferenz. Diese Zahl ist aus vorhandenen Logs auch ohne diesen
Zuschnitt zu ziehen und darf vorgezogen werden.

## par.7 Entscheidungsregeln, vorab festgelegt

Sei `Delta_M` die Primaermetrik im Arm M, `Delta_R` im Arm R.

- **`Delta_M − Delta_R >= +5 pp`, Block-Bootstrap-KI schliesst 0 aus:**
  **Such-Lesart bestaetigt.** Der Suchhebel wirkt upstream. Folge: der
  Policy-seitige Kredit-Horizont ist der offene Hebel, und die naechsten
  Zuschnitte gehoeren in die Suche (Alpha-Sweep, Knopf im Self-Play).
- **`Delta_M − Delta_R < +2 pp`:** **Ziel-Lesart bestaetigt.** Der
  Suchhebel erreicht die Zufuehrung nicht; k1 steigt aus der Endplatzierung.
  Folge: Hebel gehoeren ans Ziel beziehungsweise an das Formungssignal, das
  dem Netz fehlt (siehe par.9).
- **dazwischen:** Grenzfall, Entscheidung liegt beim Nutzer. Kein
  nachtraegliches Verschieben der Schwellen.

Die Schwellen sind a priori gesetzt. Begruendung: der Lehrer trennt sich mit
+12,6 pp vom Champion; 5 pp sind rund 40 % dieses Abstands und damit eine
Bewegung, die man nicht wegdiskutieren kann, 2 pp liegen im Bereich dessen,
was Seed und Gegnerwahl ohnehin bewegen.

## par.8 Waechter

1. **Kein SPRT-Fruehstopp**, feste Seedzahl. Im Projekt hat ein
   SPRT-H1-Zwischenstand schon einmal Seed-Rauschen als Effekt ausgewiesen
   (`t12_dist`, 54:26, in der Replikation 206:194).
2. **Block-Ebene bei jeder Auswertung** (par.5).
3. **Gegner konstant** ueber beide Arme (par.4).
4. **Keine Nebenlast.** Solange Server-Partien des Nutzers laufen, keine
   Messung -- CPU-Nebenlast verstuemmelt Partien nichtdeterministisch.
5. **Instrument-Caveat ausweisen.** Die +7,0-pp-k1-Messung lief gegen die
   HEURISTIK. Dieser Zuschnitt laeuft netz-gegen-netz. Ein Unterschied im
   Niveau ist deshalb erwartbar und kein Befund.
6. **Sonden unveraendert.** Werden `row_preference_probe.py` oder
   `column_completion_legality_probe.py` fuer diesen Lauf angefasst, ist der
   Bestandswert damit neu zu erheben -- sonst wird ein Sondenwechsel als
   Verhaltensaenderung gelesen.

## par.9 Was als Nicht-Erfolg gilt

- **Ziel-Lesart bestaetigt** (`< +2 pp`): kein Misserfolg des Zuschnitts,
  sondern sein zweiter gueltiger Ausgang. Er schliesst den Suchweg als
  Erklaerung der ZUFUEHRUNG aus und richtet die Aufmerksamkeit auf das
  fehlende Formungssignal. Dazu gehoert der Befund, dass die Suchadditiv-Form
  dieses Signals bereits getestet wurde (`PLATE_SHAPING_ENABLED`, gepaarter
  A/B 2026-07-25, p=0,7111, gegen Merge) -- aber in der v15-Aera und
  gemessen an der SIEGQUOTE, nicht an k1 oder der Reihenwahl. Die
  Ziel-Form (Formungsterm als Trainingsziel statt als Suchadditiv) ist nie
  getestet worden und waere der Anschluss.
- **Beide Arme flach, k1 bewegt sich auch nicht:** dann repliziert der Lauf
  die +7,0 pp nicht. Zuerst das Instrument pruefen, nicht den Befund
  umdeuten.
- **Delta bewegt sich, aber die Blockade-Zusammensetzung nicht:** zu
  berichten. Reihenwahl geaendert, ohne dass es Vollendungen freischaltet,
  hiesse, dass ein weiterer Riegel dahinter liegt.

## par.10 Offen, vor dem Lauf zu entscheiden

- Ob `--log-games` in der Alpha-Messung schon gesetzt ist (par.3).
- Ob zusaetzlich `alpha = 0,1` und `0,4` mitlaufen (der Sweep ist ohnehin
  Nutzer-Entscheid; die Sonden kosten je Arm nichts extra).
- Die genaue Rundengruppierung R1-2 gegen R4-5. Sie ist aus der
  Bestandssonde uebernommen, damit die Bezugswerte gelten -- eine andere
  Gruppierung waere ein anderer Vergleich.

## par.11 Verhaeltnis zu den Nachbar-Zuschnitten

- **`PREREG_implicit_minimax_backup.md`**: liefert den Knopf und die
  +7,0-pp-Messung. Dieser Zuschnitt misst nicht seine Staerke nach, sondern
  den ORT seiner Wirkung.
- **`PREREG_agent_encapsulation.md` par.6a**: liefert die Partien. Ohne
  jenen Lauf hat dieser Zuschnitt keine Datenbasis; er erzeugt bewusst keine
  eigene.
- **`PREREG_bootstrap_horizon.md`**: dessen Stufe 0 hat den Kredit-Horizont
  in seiner LABEL-Form geschwaecht. Hier geht es um die POLICY-Form
  (erreicht die Suche die Auszahlung). Das sind zwei verschiedene
  Horizonte; ein Nullbefund dort ist kein Nullbefund hier.
- **`PREREG_plate_policy_supervision.md`**: naechster Nachbar auf der
  Ziel-Seite. Faellt hier die Ziel-Lesart, ist jener Zuschnitt der
  Anschluss.
