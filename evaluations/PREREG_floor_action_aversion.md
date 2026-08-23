<!-- STATUS: OFFEN | Frage: Warum meidet der Champion die AKTION "Ziel Strafleiste" massiv, die KONSEQUENZ "Steine auf der Strafleiste" aber nicht -- sitzt das im Policy-Prior oder in der Suche, und warum korrigiert der aktive Floor-Shaping-Term es nicht? | Beleg: nichts gebaut, angelegt 2026-08-23. Anlass ist die gepaarte Strafleisten-Sonde ueber 407 identische Partien: abgeladene Steine 2,88 gegen 6,38 (t=-12,6), Ueberlauf-Steine 2,21 gegen 1,78 (t=+4,2), Strafrunden 4,25 gegen 3,81 (t=+6,0). Nutzer-Hypothese Floor-Shaping am Code geprueft: der Term ist eine reine ZUSTANDS-Funktion und damit symmetrisch, kann die Asymmetrie also nicht erzeugen -- er sollte sie korrigieren und tut es offenbar nicht. Zweiter Fund: sein Gewicht 0,3 wurde in der v9b-Aera bei 11:89 abgenommen und nie nachkalibriert, obwohl der Code-Kommentar es verlangt -->

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

## par.4 Der lose Faden, der dabei auffiel

`FLOOR_SHAPING_WEIGHT = 0.3` (`net_mcts.rs:470`) traegt im Code zwei
Kommentare, die zusammen nicht mehr stimmen koennen:

- "Bewusst klein gewaehlt (Nudge, kein Ersatz fuer den Value-Head) --
  **erster Test, mit echten Arena-Ergebnissen kalibrieren**."
- "GETESTET (2026-07-19/20, **v9b_domeonly**, 150 Sims, n=100): **11:89**
  (11 % Siege) ... die bisher beste Netz-Performance der gesamten Session.
  **Bleibt vorerst aktiv.**"

Der Term wurde also in einer Aera abgenommen, in der das Netz 11 % der
Partien gewann, und seither ueber rund ein Dutzend Champion-Generationen
nie nachkalibriert -- obwohl der eigene Kommentar genau das verlangt. Das
ist unabhaengig von dieser Prereg ein offener Punkt und wird hier
mitgemessen, weil die Arme ihn ohnehin abdecken.

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

## par.7 Arme

Nur wenn das Tor auf H2 oder H3 zeigt. Ein Faktor, vorhandener Knopf,
**kein Bau**: `MOSAIC_FLOOR_SHAPING_W` ist registriert und aktiv
(`docs/knobs.md:18`).

| Arm | `MOSAIC_FLOOR_SHAPING_W` |
|---|---|
| **R** | 0,3 (Bestand) |
| **A0** | 0,0 -- Term aus |
| **A1** | 0,6 -- doppeltes Gewicht |

`A0` ist der aussagekraeftigste Arm: **wenn der Term aus ist und die
Asymmetrie bleibt, hat er sie nie getragen.** `A1` prueft, ob mehr Gewicht
die Konsequenz-Seite ueberhaupt erreicht.

`MOSAIC_FLOOR_SHAPING_OPP_BIAS` bleibt bei 1,0 und wird NICHT mitvariiert --
das waere ein anderer Zuschnitt (Denial), und zwei Knoepfe gleichzeitig
machen jeden Ausgang mehrdeutig.

## par.8 Metriken

**Primaer, je Arm und Seite:** die vier Kennzahlen aus par.1, mit derselben
Sonde und derselben gepaarten Auswertung. Die Frage ist, ob sich der
Abstand zwischen abgeladenen und uebergelaufenen Steinen bewegt.

**Als Waechter gleichrangig:** Siegquote und Punkte-Niveau. Der Term ist
seit v9b aktiv; ihn zu drehen darf keine Staerke kosten, ohne dass es
auffaellt.

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
  erreicht bei hoeherem Gewicht beide Kanaele. Dann ist die Nachkalibrierung
  aus par.4 faellig und dieser Zuschnitt hat einen konkreten Vorschlag.
- **Staerke faellt in irgendeinem Arm ausserhalb der Aufloesung:** Befund
  unabhaengig vom Rest zu berichten; der Bestandswert 0,3 bleibt.

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
- Ob A1 mit 0,6 oder einem anderen Faktor faehrt.
- Ob der Zuschnitt vor oder nach `PREREG_completion_bottleneck_locus.md`
  laeuft. Beide sind billig; die Reihenfolge ist Nutzer-Entscheid.

## par.13 Verhaeltnis zu den Nachbar-Zuschnitten

- **`PREREG_completion_bottleneck_locus.md`**: dieselbe Frage in anderer
  Auspraegung -- dort Suche gegen Ziel bei der REIHENWAHL, hier Prior gegen
  Suche bei der STRAFLEISTE. Faellt beides auf dieselbe Seite, ist das ein
  gemeinsamer Befund ueber den Agenten und kein Zufall.
- **`PREREG_search_path_remeasurements.md` M1**: dort ist
  `MOSAIC_FLOOR_SHAPING_W` als Sweep-Knopf registriert. Dieser Zuschnitt
  nutzt denselben Knopf, misst aber eine VERHALTENS-Groesse statt Staerke.
- **`PREREG_aggression_style_measurement.md` E2**: dort haengt
  `OPP_BIAS`. Bewusst nicht Gegenstand (par.7).
- Die Reihen-Sonde und die Straf-Sonde (STATUS 2026-08-23): liefern die
  Bestandswerte. Straf-Aversion als Erklaerung der Kurzreihen-Praeferenz ist
  dort bereits geschwaecht -- dieser Zuschnitt greift den ZWEITEN Befund
  jener Messung auf, nicht den ersten.
