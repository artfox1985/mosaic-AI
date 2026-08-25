<!-- STATUS: ENTSCHIEDEN | Frage: Warum meidet der Champion die AKTION "Ziel Strafleiste" massiv, die KONSEQUENZ "Steine auf der Strafleiste" aber nicht -- sitzt das im Policy-Prior oder in der Suche? | Beleg: H1 (Prior schon asymmetrisch, Suche verschiebt kaum), belegt in ZWEI Laeufen mit v21_2d_brierbest, sims=200. par.6 (2026-08-24, 280 Stellungen, floor_action_aversion_gate.json): Prior und Suchanteil auf dem Strafleisten-Ziel exakt 0. par.14 (2026-08-25, Nachmessung, 240 Stellungen aus Runde 2-4, floor_action_aversion_gate_r234_s20260825.json): der Nullwert war eine Eigenschaft der RUNDE 1 -- die par.6-Stichprobe lag zu 268/280 dort, weil die Sonde die ersten N Datensaetze je Datei nahm und die in Zugreihenfolge stehen (Sammel-Artefakt, Sonde repariert, Bestandsauswahl byte-identisch erhalten). In Runde 2-4: Prior 0,00065 gegen Ueberlauf 0,03951, Suchanteil 0,00221 gegen 0,03198; 62 von 240 Stellungen haben Prior > 0, in 10 besucht die Suche die Aktion, groesster Einzelwert Prior 0,0587 mit Suchanteil 0,15. GEFALLEN sind damit "exakt 0", "in schaerfster Form" und die Logit-Abstand-Herleitung; STEHEN bleibt die Asymmetrie (Faktor ~60) und das Verdikt H1. Arme R/A0/A1 entfallen weiterhin nach der vorab festgelegten Regel. -->

# Vorregistrierung: Aktions-Ebenen-Aversion gegen die Strafleiste

**Angelegt 2026-08-23, VOR jeder Messung.**

## par.1 Der Befund, der den Anlass gibt

Gepaart ueber **407 identische Partien** (`paired_arena_env_imm_a02.json`,
Champion und Heuristik auf denselben Seeds, Block-Ebene je Partie,
`tools/probes/penalty_track_probe.py`, Arm alpha=0):

| je Partie | Champion | Heuristik | Diff | t |
|---|---|---|---|---|
| abgeladene Steine (Ziel = Strafleiste) | 2,88 | 6,38 | **−3,50** | **−12,62** |
| Ueberlauf-Steine | 2,21 | 1,78 | **+0,43** | **+4,16** |
| Runden mit Strafe | 4,25 | 3,81 | **+0,44** | **+6,02** |
| Strafpunkte | 16,91 | 19,59 | −2,68 | −4,06 |

Der Champion meidet die **Aktion** massiv und die **Konsequenz** gar nicht.
Das ist die groesste Einzelbewegung, die in dieser Sondenfamilie je gemessen
wurde.

### Nachtrag 2026-08-24: Gegnerspezifitaets-Caveat geschlossen

Der obige Vergleich lief ausschliesslich gegen die HEURISTIK. Seit dem
Paritaets-Befund (`PREREG_completion_bottleneck_locus.md` par.1a) steht
jede Heuristik-Messung unter Gegnerspezifitaets-Verdacht -- nachgezogen mit
`penalty_track_probe.py` auf `imm_netvnet.json` + `..._swap.json` (dasselbe
Netz beidseitig, alpha=0,2 gegen den eingefrorenen Champion, 814 Partien
gepoolt je Arm):

| Quelle | abgeladene Steine je Partie |
|---|---|
| Champion gegen Heuristik (par.1, oben) | **2,88** |
| Champion (alpha=0,2) netz-gegen-netz | 4,27 |
| Champion (frozen) netz-gegen-netz | 4,05 |
| Heuristik gegen Champion (par.1, oben) | **6,38** |

**Die Aversion ist real und ueberlebt netz-gegen-netz, ist aber teilweise
gegnerspezifisch in ihrer GROESSE.** Netz-gegen-netz liegt der Wert bei
4,05-4,27 -- deutlich naeher an den 2,88 gegen die Heuristik als an deren
6,38, aber klar darueber. Ein Teil der -3,50-Differenz aus par.1 ist also
Aversion, ein anderer Teil ist Kontext (gegen einen schwaecheren Gegner
laesst sich mehr "sparen"). Das AKTION-KONSEQUENZ-Missverhaeltnis, das
diese Prereg begruendet, bleibt davon unberuehrt -- es ist eine Eigenschaft
der Aktionskodierung (par.2), keine Eigenschaft des Gegners, und Tor par.6
(gefahren auf netz-generierten Korpus-Stellungen, nicht gegen die
Heuristik) zeigt dieselbe Extremitaet (Prior exakt 0 in 280/280 Stellungen)
unabhaengig von dieser Frage.

## par.2 Warum das ueberhaupt eine Frage ist

Beide Wege sind regelseitig **dieselbe Sache**. `docs/engine_manual.md`
Z.110-113: Steine, die nicht mehr in die gewaehlte Musterreihe passen,
fallen auf die Strafleiste; sie dort freiwillig abzulegen ist ebenfalls
erlaubt. Z.161: die Leiste zahlt −1, −2, −3, −4 je belegtem Slot. Es gibt
keine Regel, die zwischen "abgeladen" und "uebergelaufen" unterscheidet.

Oekonomisch sind die Kanaele also identisch. Verhaltensseitig behandelt der
Champion sie um Faktor 2 verschieden. **Ein Agent, der ueber ZUSTAENDE
optimiert, kann diese Asymmetrie nicht haben. Ein Agent, der ueber BENANNTE
AKTIONEN optimiert, muss sie haben.**

Der Aktionsraum liefert dazu den passenden Bauplan: das Strafleisten-Ziel
ist ein eigener, benennbarer Slot in der Kodierung (`neural_net.py:411-413`,
`row: -1..6 -> 0..7`, `-1` ist die Leiste). Der Policy-Kopf hat also einen
Ausgang, den er kleinrechnen kann. Fuer den Ueberlauf gibt es keinen -- er
ist Folge einer ganz normalen Reihen-Aktion, deren Entnahme die
Restkapazitaet uebersteigt.

## par.3 Die Nutzer-Hypothese, am Code geprueft

Nutzer-Vermutung 2026-08-23: "hat vielleicht mit dem Floor-Shaping-Term zu
tun". Am Code nachgesehen, und das Ergebnis dreht die Vermutung um.

`floor_shaping_delta` (`net_mcts.rs:958`) ist

```
(mine - theirs) / FLOOR_SHAPING_SCALE          // SCALE = 50.0
```

mit `floor_penalties` (`:966`) aus zwei Quellen: `broken_penalty()` --
laut Kommentar (`:948-950`) ausdruecklich die **materialisierten**
Strafleisten-Fliesen inklusive **Drafting-Ueberlauf**
(`execution.rs::add_to_penalty`) -- plus
`round_end::projected_unplaceable_penalty`.

**Das ist eine reine ZUSTANDS-Funktion.** Sie liest, wie viele Steine auf
der Leiste liegen, nicht wie sie dorthin kamen. Beide Kanaele gehen
identisch ein.

Zwei Folgerungen:

1. **Der Term kann die Asymmetrie nicht ERZEUGEN.** Die naheliegende Form
   der Hypothese ist damit erledigt, bevor eine Messung laeuft.
2. **Er sollte sie KORRIGIEREN -- und tut es offenbar nicht.** Er ist aktiv
   (Gewicht 0,3, `docs/knobs.md:18` "aktiv", angewandt auf den Blattwert in
   `net_mcts.rs:2770` und `:4000`). Ein symmetrischer Zustandsterm auf dem
   Blattwert muesste Ueberlauf genauso bestrafen wie Abladen. Dass die
   Asymmetrie trotzdem besteht, ist der eigentliche Befund -- und die
   Hypothese wird dadurch nicht schwaecher, sondern schaerfer.

## par.4 Was am Gewicht 0,3 schon gemessen ist

**KORREKTUR 2026-08-23, noch am selben Tag.** Ein erster Entwurf dieses
Abschnitts behauptete, der Term sei seit der v9b-Aera "nie nachkalibriert".
Das ist falsch, Nutzer-Hinweis, am Bestand nachgeprueft. Der Code-Kommentar
an `FLOOR_SHAPING_WEIGHT` (`net_mcts.rs:470`) traegt zwar noch den alten
Stand ("erster Test, mit echten Arena-Ergebnissen kalibrieren", GETESTET
2026-07-19/20 an `v9b_domeonly` bei 11:89) -- die Akte ist aber weiter.

`PREREG_search_path_remeasurements.md` ist **ENTSCHIEDEN**, Messung 1 war
genau dieser Sweep in der WDL-Aera:

| Vergleich | Ergebnis |
|---|---|
| W=0,3 gegen W=0,15 | 153/200 gegen 144/200, **p=0,31**, H0 |
| W=0,3 gegen W=0,6 | **p=0,36**, H0 |
| **W=0,3 gegen W=0,0** (Task A, 2026-08-09, Champion `v21_2d_brierbest`) | **322/400 gegen 277/400**, 80,5 % gegen 69,3 %, **−11,25 pp**, exakter gepaarter McNemar **p=0,0001** (b=43/c=88), Block-Ebene **13 von 16 Bloecken**, Block-SE 0,71, **t=3,94** |

Daraus der registrierte Strukturbefund: **Floor-Shaping ist ein SCHALTER,
kein Regler.** Ob es an ist, macht rund 11 pp; welchen Wert es zwischen 0,15
und 0,6 traegt, macht nichts. Artefakt:
`evaluations/artifacts/paired_arena_env_paired_arena_env_floorw_taskA.json`.

**Was daran fuer diese Prereg wichtig ist -- und was trotzdem offen bleibt:**

1. Der Term ist auf **STAERKE** dreifach re-validiert. Die Frage "ist 0,3
   richtig" ist beantwortet und wird hier **nicht** neu gestellt.
2. Gemessen wurde ausschliesslich die Siegquote. **Ob der Term das tut,
   wofuer er gebaut ist, hat nie jemand nachgesehen** -- die
   Abladen-gegen-Ueberlauf-Aufteilung aus par.1 ist von allen drei Messungen
   unberuehrt.
3. Das Task-A-Artefakt traegt **beide Arme mit je 400 Partien, aber KEINE
   Logs** (`--log-games` war aus; nachgesehen 2026-08-23: 0 von 400 in
   beiden Armen). Die Verhaltensfrage laesst sich daran also nicht
   nachtraeglich beantworten, obwohl die Partien existieren.

Das macht diesen Zuschnitt **staerker**, nicht schwaecher: die
Staerke-Wirkung jedes Arms ist vorab bekannt, ein Verhaltenseffekt kann
also nicht mit einem Staerkeeffekt verwechselt werden.

## par.5 Hypothesen

- **H1 Prior.** Die Asymmetrie sitzt im rohen Policy-Prior. Abladen ist im
  Trainingskorpus selten, der Ausgang verkuemmert, und das verstaerkt sich
  selbst ueber Generationen. Die Suche erbt sie und korrigiert sie nicht.
- **H2 Suche.** Der Prior ist annaehernd symmetrisch, erst die Suche
  erzeugt die Asymmetrie -- dann liegt es an PUCT, am Gumbel-Zuschnitt oder
  am Zusammenspiel mit dem Shaping-Term.
- **H3 Reichweite des Shaping-Terms.** Der Term wirkt am Blattwert, aber die
  Drafting-Entscheidung wird nicht von ihm erreicht (zu klein bei
  Gewicht 0,3 gegen `tanh`, oder von der Prior-Masse ueberstimmt, bevor die
  Suche ihn sieht).

H1 und H3 schliessen einander nicht aus.

## par.6 Tor: Prior gegen Suche, offline (kein Training, keine Arena)

**Vor jedem Arm.** Auf Stellungen aus dem vorhandenen Korpus, in denen
BEIDES legal ist: ein explizites Strafleisten-Ziel und mindestens ein
Reihen-Ziel, dessen Entnahme die Restkapazitaet uebersteigt (also Ueberlauf
erzeugt).

Erhoben wird je Stellung:

1. **Roher Policy-Prior** auf dem Strafleisten-Ausgang gegen die Summe der
   ueberlauferzeugenden Reihen-Ausgaenge, normiert auf die legale Maske.
2. **Besuchsverteilung nach der Suche** auf denselben beiden Mengen.
3. Beides zusaetzlich getrennt nach Runde.

Vorab festgelegte Lesart:

- **Prior schon asymmetrisch, Suche verschiebt kaum:** H1. Der Hebel liegt
  im Ziel/Korpus, nicht in der Suche.
- **Prior annaehernd symmetrisch, Suche erzeugt die Asymmetrie:** H2.
- **Beide asymmetrisch, aber die Suche verstaerkt sie:** H1 plus H3.

Dieses Tor kostet Vorwaertslaeufe ueber ein Stellungsset. Es entscheidet,
welche Arme ueberhaupt sinnvoll sind, und steht deshalb vorn.

### par.6 ERGEBNIS (2026-08-24): H1, eindeutig -- die Arme entfallen

Gefahren mit `tools/probes/floor_action_aversion_gate.py`, Artefakt
`floor_action_aversion_gate.json`. **280 qualifizierende Stellungen**
(Farbkonflikt- oder GF-Sonne-Kapazitaets-Kriterium, siehe Werkzeug-Kopf fuer
die exakte, konservative Definition), Champion `v21_2d_brierbest`,
`sims=200`, `c_puct=1,5`.

**Zwei Selbsttests VOR jeder Kennzahl bestanden** (REGEL 0): die lokal
portierte `action_to_id` gegen die importierte Referenzfunktion aus
`neural_net.py`, und "jeder von der Suche zurueckgegebene Kandidat ist
legal" gegen die Engine selbst. Ein erster Versuch, `mv["action_id"]` aus
`net_search_state_json` direkt mit der globalen `action_to_id`-Achse zu
vergleichen, ist dabei PROMPT gescheitert (die Engine gibt dort einen
LOKALEN Index in die Kandidatenliste zurueck, keine globale ID) --
korrigiert auf Matching ueber den Aktionsinhalt, bevor irgendetwas gezaehlt
wurde.

| Groesse | Floor-Ziel | Ueberlauf-Reihen-Ziel |
|---|---|---|
| Roher Prior (Mittel ueber 280 Stellungen) | **0,0 -- exakt, in ALLEN 280 Stellungen** (Float32-Softmax-Unterlauf, nicht Rundung) | 0,00055 (72/280 Stellungen > 0) |
| Suchanteil nach 200 Sims (Mittel) | **0,0 -- in ALLEN 280 Stellungen** | 0,00102 (10/280 Stellungen > 0) |

**Verdikt nach der vorab festgelegten Lesart: H1, und zwar in seiner
schaerfsten Form.** Der Prior ist nicht nur "schon asymmetrisch" -- er
schliesst das Strafleisten-Ziel in JEDER gepruefter Stellung numerisch
vollstaendig aus, und die Suche bewegt daran nichts (kann es auch nicht,
siehe Mechanismus unten). **Der Hebel liegt im Ziel/Korpus, nicht in der
Suche -- nach par.7 des Tors entfallen die Arme R/A0/A1 (H2/H3 waeren
Voraussetzung).**

**Mechanismus, warum die Suche strukturell nicht helfen kann (Herleitung,
nicht separat gemessen):** ein Float32-Softmax-Unterlauf auf exakt 0
bedeutet einen Logit-Abstand von grob > 87 natuerlichen Einheiten zum
Maximum. Gumbels Top-m-Wurzelauswahl addiert Rauschen aus `Gumbel(0,1)`
(praktisch fast nie ausserhalb von etwa ±10) auf die Logits, bevor die
`m` hoechsten genommen werden -- ein Abstand von >87 ist damit fuer JEDE
praktisch erreichbare Rauschziehung unueberwindbar. Der Floor-Shaping-Term
(`floor_shaping_delta`, additiv auf dem BLATTWERT) wirkt an einer Stelle,
die die Suche gar nicht mehr erreicht, wenn die Wurzelauswahl das
Strafleisten-Ziel schon vorher verworfen hat -- **das erklaert zwanglos,
warum ein aktiver, dreifach staerke-validierter Shaping-Term die
Aktions-Ebenen-Asymmetrie aus par.1 nicht korrigiert: er sitzt hinter dem
Nadeloehr, nicht davor.**

**Einschraenkung, offen ausgewiesen:** die Runden-Verteilung der 280
Stellungen ist stark ungleich (Runde 1: 268, Runde 2: 11, Runde 3: 1,
Runde 4/5: 0) -- eine Folge der konservativen Ueberlauf-Kriterien (kleine
Reihenkapazitaet macht Ueberlauf frueh im Spiel haeufiger nachweisbar).
Die je-Runde-Aufschluesselung im Artefakt ist fuer Runde 2/3 zu duenn fuer
eine eigene Aussage; das GESAMT-Verdikt (n=280) ist davon nicht beruehrt,
da Runde 1 ohnehin die grosse Mehrheit stellt und dort allein schon
eindeutig ist.

## par.7 Arme

**ENTFAELLT (2026-08-24).** Das Tor aus par.6 hat H1 ergeben; nach der dort
vorab festgelegten Regel werden die Arme R/A0/A1 nicht gefahren. Dieser
Abschnitt bleibt zur Dokumentation stehen.

Nur wenn das Tor auf H2 oder H3 zeigt. Ein Faktor, vorhandener Knopf,
**kein Bau**: `MOSAIC_FLOOR_SHAPING_W` ist registriert und aktiv
(`docs/knobs.md:18`). Die Konfiguration ist die von Task A, nur **mit
`--log-games`** -- das ist der einzige Unterschied und der einzige
Neu-Aufwand.

| Arm | `W` | Staerke laut par.4 | Rolle hier |
|---|---|---|---|
| **R** | 0,3 | Bestand | Referenz |
| **A0** | 0,0 | **−11,25 pp, p=0,0001** | **reiner Diagnose-Arm** |
| **A1** | 0,6 | H0, p=0,36 | reine Verhaltenssonde |

**A0 ist ausdruecklich KEIN Default-Kandidat.** Dass Abschalten Staerke
kostet, ist entschieden und wird hier nicht neu verhandelt; der Arm laeuft
allein, um zu sehen, ob der Term die Asymmetrie traegt. Faende er sich als
Traeger, waere die Konsequenz eine BESSERE Fassung des Terms, nie sein
Abschalten.

**Vorregistrierte Vorhersage aus dem Schalter-Befund.** Wenn "Schalter, kein
Regler" auch fuer das VERHALTEN gilt, dann bewegt `A0` die Aufteilung und
`A1` bewegt sie nicht. Bewegt umgekehrt `A1` etwas und `A0` nicht, ist der
Schalter-Befund auf der Verhaltensseite falsch -- ein eigener, berichtbarer
Befund ueber einen Term, der seit der v9b-Aera aktiv ist.

`MOSAIC_FLOOR_SHAPING_OPP_BIAS` bleibt bei 1,0 und wird NICHT mitvariiert --
das waere ein anderer Zuschnitt (Denial), und zwei Knoepfe gleichzeitig
machen jeden Ausgang mehrdeutig.

## par.8 Metriken

**Primaer, je Arm und Seite:** die vier Kennzahlen aus par.1, mit derselben
Sonde und derselben gepaarten Auswertung. Die Frage ist, ob sich der
Abstand zwischen abgeladenen und uebergelaufenen Steinen bewegt.

**Siegquote und Punkte-Niveau:** mitzuberichten, aber als KONTROLLE, nicht
als Waechter -- die Staerke-Wirkung jedes Arms steht bereits fest (par.4).
Weicht ein Arm stark von seinem bekannten Wert ab, ist zuerst das Instrument
zu pruefen, nicht der Befund umzudeuten.

Dazu die sechs Standard-Kennzahlen je Seite (CLAUDE.md): Reihenauslastung,
Spaltenauslastung, Strafleistenauslastung, Punkte je Wertungsplatte, eigene
Punkte, Marge zum Gegner.

**Auswertung auf Block-Ebene**, gepaarte Seeds, **kein SPRT-Fruehstopp**.

## par.9 Entscheidungsregeln, vorab festgelegt

Sei `Q = abgeladene Steine / (abgeladene + uebergelaufene Steine)` je Seite.
Bestand: Champion 0,57, Heuristik 0,78 (aus par.1 gerechnet).

- **`Q` bewegt sich in A0 um weniger als 0,05 gegen R:** der Shaping-Term
  traegt die Asymmetrie nicht. Sie sitzt im Prior beziehungsweise im Ziel,
  und dieser Zuschnitt endet mit diesem Befund -- Anschluss waere die
  Ziel-Seite.
- **`Q` steigt in A0 deutlich (>= 0,10):** der Term hat die benannte Aktion
  unterdrueckt. Dann ist zu klaeren, warum er die Konsequenz nicht
  gleichermassen unterdrueckt hat, obwohl er zustandsbasiert ist -- H3.
- **`Q` faellt in A1 und die Ueberlauf-Steine fallen mit:** der Term
  erreicht bei hoeherem Gewicht beide Kanaele. Das WIDERSPRAECHE dem
  Schalter-Befund aus par.4 auf der Verhaltensseite und waere der
  interessanteste Ausgang -- ein Regler, der nur in der Siegquote wie ein
  Schalter aussieht. Zu berichten als eigener Befund, nicht als
  Default-Vorschlag.
- **In jedem Fall bleibt `W = 0,3` der Default.** Dieser Zuschnitt aendert
  keinen Knopfwert; er lokalisiert eine Verhaltensasymmetrie. Ein
  Default-Wechsel waere ein eigener Zuschnitt mit eigener Staerke-Messung
  und Frisch-Seed-Replikation.

## par.10 Waechter

1. **Nur ein Knopf.** `OPP_BIAS` bleibt 1,0 (par.7).
2. **Gegner konstant** ueber alle Arme, gepaarte Seeds.
3. **Block-Ebene**, nie Zug-Ebene.
4. **Keine Nebenlast**, Arena exklusiv.
5. **Sonde unveraendert.** Wird `penalty_track_probe.py` fuer diesen Lauf
   angefasst, sind die Bestandswerte aus par.1 neu zu erheben.
6. **Kein Eingriff am Anker.** Die Heuristik-Seite bleibt unberuehrt; sie
   ist hier Referenz, nicht Messobjekt.

## par.11 Was als Nicht-Erfolg gilt

- **Tor zeigt H1 (Prior traegt alles):** dieser Zuschnitt endet ohne Arme.
  Zulaessiger Ausgang, und der billigste.
- **Alle Arme H0 auf `Q`:** die Asymmetrie ist gegen den vorhandenen Knopf
  robust. Zu berichten als das, was es ist.
- **`Q` bewegt sich, die Strafpunkte nicht:** dann wurde nur zwischen den
  Kanaelen umverteilt, ohne Gewinn. Wichtiger Befund, weil er die ganze
  Richtung relativiert.

## par.12 Offen, vor dem Lauf zu entscheiden

- Das Stellungsset fuer das Tor: aus welchem Korpus, wie viele Stellungen,
  und wie "ueberlauferzeugend" genau bestimmt wird (Restkapazitaet gegen
  Entnahmegroesse -- die Entnahmegroessen je Seite sind bisher NICHT
  erhoben, siehe die Einschraenkung im STATUS-Eintrag zur Straf-Sonde).
- Ob A1 mit 0,6 oder einem anderen Faktor faehrt. 0,6 ist gewaehlt, weil
  genau dieser Wert in Messung 1 schon lief und dort H0 war -- die
  Staerke-Seite ist damit bekannt.
- Ob R und A0 als Neu-Lauf gefahren werden oder ob es billiger ist, Task A
  mit `--log-games` schlicht zu wiederholen (gleiche Seeds, gleiche
  Konfiguration). Letzteres liefert zusaetzlich eine Replikation der
  −11,25 pp gratis.
- Ob der Zuschnitt vor oder nach `PREREG_completion_bottleneck_locus.md`
  laeuft. Beide sind billig; die Reihenfolge ist Nutzer-Entscheid.

## par.13 Verhaeltnis zu den Nachbar-Zuschnitten

- **`PREREG_completion_bottleneck_locus.md`**: dieselbe Frage in anderer
  Auspraegung -- dort Suche gegen Ziel bei der REIHENWAHL, hier Prior gegen
  Suche bei der STRAFLEISTE. Faellt beides auf dieselbe Seite, ist das ein
  gemeinsamer Befund ueber den Agenten und kein Zufall.
- **`PREREG_search_path_remeasurements.md`** (ENTSCHIEDEN): dort ist der
  Knopf gebaut und die STAERKE-Frage dreifach beantwortet (par.4). Dieser
  Zuschnitt nutzt denselben Knopf und dieselbe Instrument-Konfiguration,
  misst aber eine VERHALTENS-Groesse. Er eroeffnet die Staerke-Frage
  ausdruecklich nicht wieder.
- **`PREREG_aggression_style_measurement.md` E2**: dort haengt
  `OPP_BIAS`. Bewusst nicht Gegenstand (par.7).
- Die Reihen-Sonde und die Straf-Sonde (STATUS 2026-08-23): liefern die
  Bestandswerte. Straf-Aversion als Erklaerung der Kurzreihen-Praeferenz ist
  dort bereits geschwaecht -- dieser Zuschnitt greift den ZWEITEN Befund
  jener Messung auf, nicht den ersten.

---

## par.14 NACHMESSUNG 2026-08-25: der Nullwert war eine Eigenschaft der RUNDE 1

**Anlass.** Der par.6-Lauf vom 2026-08-24 registrierte "roher Prior auf dem
Strafleisten-Ziel in ALLEN 280 Stellungen numerisch EXAKT 0, Suchanteil
ebenfalls in allen 280 exakt 0 -- H1, in schaerfster Form", mit der
Einschraenkung "Runden-Verteilung schief (268/11/1/0/0)". Diese Schieflage ist
kein Zufall, sondern ein **Artefakt der Stichprobe**:
`collect_qualifying` lief die Datensaetze je Datei IN REIHENFOLGE durch und
nahm die ersten `cap_per_file = 3` qualifizierenden. Datensaetze stehen in
Zugreihenfolge, die Stichprobe fuellte sich also mit Fruehspiel-Stellungen.

**Reparatur** (Nutzer-Auftrag 2026-08-25): `collect_qualifying` nimmt jetzt
`rounds=` und `seed=`; mit Seed werden je Datei ALLE qualifizierenden
Datensaetze gesammelt und daraus reproduzierbar gezogen. Ohne Seed ist die
Auswahl byte-identisch zum Bestand (geprueft: auf einem 25-Dateien-Ausschnitt
liefern alte und neue Fassung dieselben 60 Stellungen). Laeufe mit Filter oder
Seed schreiben in eine ABGELEITETE Artefaktdatei; `floor_action_aversion_gate.json`
ist unveraendert.

**Nachmessung**, gleiches Modell (`alphazero_v21_2d_brierbest`), gleiche
sims=200, jetzt 240 Stellungen aus den Runden 2-4 (96/68/76),
`floor_action_aversion_gate_r234_s20260825.json`:

| Groesse | Bestandslauf (268 von 280 in R1) | NEU, Runde 2-4 |
| --- | --- | --- |
| `prior_floor_mean` | **0,0** | **0,00065** |
| `prior_overflow_mean` | 0,00055 | 0,03951 |
| `search_floor_share_mean` | **0,0** | **0,00221** |
| `search_overflow_share_mean` | 0,00102 | 0,03198 |

Und die Verteilung dahinter, die der Mittelwert verdeckt: **62 der 240
Stellungen haben einen Prior groesser als 0** auf dem Strafleisten-Ziel, in
**10** besucht die Suche die Aktion tatsaechlich. Der groesste Einzelwert
liegt bei Prior 0,0587 (Runde 2) mit einem Suchanteil von 0,15 an derselben
Stelle.

### Was davon steht und was faellt

* **Es faellt**: "numerisch EXAKT 0", "in ALLEN Stellungen", "H1 in schaerfster
  Form", und die Mechanismus-Herleitung "ein Logit-Abstand > ~87 ist fuer
  Gumbel(0,1)-Rauschen an der Wurzel unueberwindbar". In den Runden 2-4 ist
  der Abstand ueberwindbar, und er wird ueberwunden.
* **Es steht**: die ASYMMETRIE und damit das Verdikt H1. Auch in den Runden
  2-4 bekommt das Strafleisten-Ziel nur etwa ein Sechzigstel der Masse der
  ueberlauferzeugenden Reihen-Ziele (0,00065 gegen 0,03951), und die Suche
  verschiebt daran wenig (0,00221 gegen 0,03198). Die vorab festgelegte
  Lesart bleibt "Prior schon asymmetrisch, Suche verschiebt kaum".
* **Neu sichtbar**: die Ueberlauf-Seite bekommt in den Runden 2-4 rund 70-mal
  so viel Prior-Masse wie in Runde 1 (0,03951 gegen 0,00055). Die Stellungen
  spaeterer Runden sind also nicht nur zahlreicher, sondern qualitativ andere
  -- ein Grund mehr, warum eine Runde-1-Stichprobe hier nicht verallgemeinert.

### Nebenlast-Verdacht geprueft und ausgeraeumt

Die Parallelsitzung meldete nach dem Lauf von sich aus, dass sie entgegen
ihrer Zusage zwischenzeitlich `cargo test --release` und mehrere
`cargo build --release` gefahren hatte -- also genau die CPU-Nebenlast, vor
der die Hausregel warnt ("Arena exklusiv, keine Nebenlast").

Zwei Pruefungen:

1. **Zeitfenster.** Der Lauf endete 10:32:32. Im Fenster 10:00-11:00 hat cargo
   nichts kompiliert (`find target/release/.fingerprint -newermt ... ` liefert
   0 Treffer, dieselbe Suche fuer 11:00-12:00 liefert 64 -- der Befehl trifft
   also). Das schliesst eine Kompilier-Ueberlappung aus, aber NICHT einen
   Suite-Lauf aus dem Cache, der CPU-Last ohne Dateispur erzeugt.
2. **Wiederholung.** Derselbe Lauf mit identischen Argumenten, auf
   nachweislich stiller Maschine: das Artefakt ist **byte-identisch**
   (md5 6e394b2dd54eeab8e4ac1492dd3bbb69). Damit ist die Kontamination
   ausgeschlossen und zugleich gezeigt, dass die Sonde deterministisch ist.

**Der Zustand des Werkzeugs zum Laufzeitpunkt** (Hausregel "Wheel nach
Engine-Aenderung neu bauen"): das installierte Wheel enthaelt
`tiling_budget_stats_json` (in dieser Sitzung geprueft), eine Funktion aus dem
letzten Engine-Commit -- das Wheel ist also nicht aelter als der
verhaltensrelevante Quellstand. Eine Quelldatei (`plate_builder.rs`) ist
juenger, ihr Diff besteht laut Parallelsitzung ausschliesslich aus
Kommentarzeilen, und `net_search_state_json` beruehrt den Plattenbau-Layer
nicht.
