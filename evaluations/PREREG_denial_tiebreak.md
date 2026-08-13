# Vorregistrierung: Denial-Tie-Break an der Wurzel (E3, eigenstaendig)

**Angelegt 2026-08-07, VOR Implementierung und Messung.** Nutzer-Go am
selben Tag ("takten den test ein"), UNABHAENGIG vom Ausgang der
w/λ-Stilmessung (E3 war urspruenglich Stufe 3 der Eskalationsleiter in
PREREG_aggression_style_measurement.md).

## Mechanismus

Unter allen WURZEL-Kandidaten, deren completed-Q innerhalb eines
ε-Fensters um den besten Wurzelzug liegt (quasi-gleichwertige Zuege),
spielt die Suche den Zug mit der NIEDRIGSTEN prognostizierten
Gegner-Punktzahl (opp_points-Kopf, Task #28 / F1-gefixte Extraktion).
Die Nutzer-Nebenbedingung "dem Gegner Punkte rauben, wenn es uns
nicht schadet" ist damit BAUART: getauscht wird nur innerhalb des
Aequivalenzfensters.

## Implementierung (Env-Knopf-Muster, Commit 2cd364e)

- `MOSAIC_DENIAL_TIEBREAK_EPS` (f64, Default 0,0 = AUS =
  byte-identisches Bestandsverhalten; OnceLock/read_f64_env).
- Wirkt bei der FINALEN Wurzelzug-Wahl der Netz-Suche (Gumbel-Pfad);
  ε auf der completed-Q-Skala ([0,1]-Gewinnwahrscheinlichkeit).
- Gegner-Punkte-Prognose je Wurzelkind aus dessen ohnehin berechneter
  Netz-Evaluation (kein zusaetzlicher Forward-Pass; falls das im
  Baum nicht ohne Zusatzkosten verfuegbar ist, ist EIN zusaetzlicher
  Batch-Forward ueber die <=m Fenster-Kandidaten erlaubt -- Kosten
  dokumentieren).
- Modelle OHNE opp-Kopf: Knopf inert + einmalige Warnung (Muster
  `warn_missing_opp_head_once`).
- R5 bleibt Alpha-Beta-exakt (round5.rs unangetastet); Default-
  Paritaets-Nachweis (Hash-Probe) + Engine-Tests vor Einsatz.

## Messung (Instrument der Stilmessung, eigene Seeds)

DREI Arme a 400 Spiele (Champion@400 vs Heuristik@150dyn, Basis-Seed
20260811): Kontrolle (ε=0), ε=0,01, ε=0,03. Auswertung identisch zur
Stilmessung: Siegquoten-Wache (McNemar; Punkt-Schaetzung darf nicht
unter die Kontrolle fallen), Raub-Metriken auf Block-Ebene (16 Bloecke:
Gegner-Punkte ↓ / Gegner-Floor ↑, p<0,05). Zusaetzlich deskriptiv:
wie oft feuert der Tie-Break (Anteil getauschter Zuege, aus einem
Debug-Zaehler oder Stichproben-Traces).

**Erwartung/Lesart**: Siegquote ~unveraendert (Bauart). ε=0,03
aggressiver, aber naeher an der Grenze, wo "quasi-gleichwertig" nicht
mehr stimmt -- faellt die Siegquote dort, gilt nur ε=0,01.

**REGEL-AENDERUNG (Nutzer 2026-08-07, VOR Sichtung der Ergebnisse,
Lauf noch in der Arena): "e3 kommt so oder so rein wenn sie die
gewinnchance nicht verringert."** Uebernahme-Gate ist damit ALLEIN
die Siegquoten-Wache (Arm faellt nur, wenn Punktschaetzung unter der
Kontrolle ODER signifikant schlechter); die Raub-Signifikanz ist
Dokumentation, kein Gate mehr. Bestehen mehrere ε-Arme die Wache,
gewinnt das GROESSERE ε (mehr Denial-Wirkung), bei praktisch gleicher
Siegquote; sonst das ε mit der besseren Siegquoten-Differenz.
Risiko-Einordnung: bauartbedingt tauscht E3 nur Zuege im
Aequivalenzfenster, und der Feuerraten-Zaehler belegt die Aktivitaet
mechanisch -- eine Uebernahme auf schwacher Raub-Evidenz kostet daher
strukturell nichts.

## Einordnung / Kombination

- Queue: CPU nach der w/λ-Stilmessung (deren Verdikt zuerst).
- Kombination mit einem etwaigen w/λ-Preset wird ERST gemessen, wenn
  BEIDE einzeln bestanden haben (eigenes Mini-Prereg; keine
  ungemessenen Kombi-Presets).
- Uebernahme-Ziel bei Bestehen: Live-/Stil-Preset UND Self-Play
  (Diversitaets-Entscheid des Nutzers gilt sinngemaess; Anker-Kante
  vor bewertetem Einsatz).

## ERGEBNIS (2026-08-07, 3x400, Seed 20260811): E3 GESCHEITERT

Kontrolle 296/400 (74,0%); ε=0,01: 273/400 (-5,75pp, McNemar p=0,085);
ε=0,03: 241/400 (**-13,75pp, p<0,0001**). Beide Arme fallen an der
Siegquoten-Wache -> KEINE Uebernahme (auch nach der gelockerten Regel).

**Ursachen-Lesart (wichtig fuers Archiv)**: die "bauartbedingt
siegquoten-schonend"-Annahme war FALSCH. Das ε-Fenster liegt auf
GESCHAETZTEN completed-Q-Werten: der Suchsieger traegt positiven
Schaetzfehler (Auswahl-Bias), die Fenster-Nachbarn haben weniger
Besuche und sind real oft deutlich mehr als ε schlechter -- der
Tie-Break tauscht damit systematisch GEGEN das Urteil der Suche, und
der Schaden waechst mit ε (Dosis-Wirkung -5,75 -> -13,75pp).
Q-Schaetzwerte sind keine Aequivalenzklassen.

Moeglicher spaeterer E3b-Ansatz (NUR mit neuem Prereg + Nutzer-Go):
Fenster auf besuchs-gewichteten Konfidenzintervallen statt roher
Q-Differenz, oder Beschraenkung auf Kandidaten mit >=X% der Besuche
des Siegers. NICHT eingeplant.

# ==================================================================
# E3b: Denial-Tie-Break mit UNSICHERHEITS-Fenster (Nutzer-Go 2026-08-08)
# ==================================================================

**Angelegt VOR Implementierung und Messung.** Einplanung: NACH
v21-Training + Gating + Auswertungs-Paket (Nutzer-Zuschnitt
"eintakten nach dem v21 training, gating usw.").

## Warum ein zweiter Versuch ueberhaupt zulaessig ist

E3 ist nicht daran gescheitert, dass Denial schaedlich waere, sondern
daran, dass das Fenster auf ROHEN Q-Differenzen lag: der Suchsieger
traegt Auswahl-Bias und die meisten Besuche, die Fenster-Nachbarn
wurden im Sequential Halving frueh eliminiert und sind real oft mehr
als ε schlechter. Der Tausch ging damit systematisch gegen das Urteil
der Suche (Dosis-Wirkung -5,75pp -> -13,75pp). E3b ersetzt die
Aequivalenz-DEFINITION, nicht das Ziel.

## Aequivalenz-Kriterium (statt roher ε-Differenz)

Kandidat `a` gilt nur dann als gleichwertig zum Sieger `b`, wenn BEIDE
Bedingungen halten:
1. **Besuchs-Gate**: `N(a) >= f * N(b)` (Default f=0,5) -- vergleichbare
   Schaetzerqualitaet; eliminiert die frueh weggehalbierten Kandidaten.
2. **Unsicherheits-Fenster**: `Q(b) - Q(a) <= z * SE`, mit
   `SE = sqrt(Q_pool*(1-Q_pool)*(1/N(a) + 1/N(b)))` (Zwei-Anteils-
   Standardfehler; completed-Q ist eine Gewinnwahrscheinlichkeit, die
   Bernoulli-Approximation ist damit sachlich begruendet). Default z=1,0.
Unter den qualifizierten Kandidaten wird wie in E3 der mit der
NIEDRIGSTEN Gegner-Punkte-Prognose gespielt (opp-Kopf, kein
Zusatz-Forward). `v(s)` und alle Trainings-Ziele bleiben unberuehrt.

## Stufe 1 (BILLIG, entscheidet ueber Stufe 2): Feuerrate messen

Erwartung: im Sequential Halving haben am Ende typischerweise nur 1-2
Kandidaten hohe Besuchszahlen -- das Besuchs-Gate kann E3b also stark
ausbremsen. Deshalb ZUERST der bestehende Debug-Zaehler
(`denial_tiebreak_stats`, fired/total) in einem einzigen Lauf
(200 Partien @400 Sims, z=1,0, f=0,5).
**Abbruchregel**: Feuerrate < 5% der Entscheidungen -> E3b gilt als
IRRELEVANT (die Arena koennte einen Effekt dieser Groesse ohnehin nicht
aufloesen), Punkt ohne Arena geschlossen, Ergebnis dokumentiert.
Feuerrate >= 5% -> Stufe 2.

### ERGEBNIS Stufe 1 (2026-08-09): 36,52% -- STUFE 2 GERECHTFERTIGT

`tools/e3b_firing_rate.py` (eigener Treiber, s.u.), Champion@400 vs
Heuristik@150dyn, 200 Partien, Seed 20260826, z=1,0, f=0,5:
**fired 3.260 / total 8.926 = 36,52%**, ueber alle 8 Bloecke stabil
(36,58 / 36,50 / 36,40 / 36,52 / 36,55 / 36,52 -- keine Drift).
Belegstelle `evaluations/e3b_firing_rate.json`.

**Die Erwartung der Vorregistrierung war falsch.** Erwartet war eine
starke Ausbremsung durch das Besuchs-Gate ("am Ende typischerweise nur
1-2 Kandidaten mit hohen Besuchszahlen"); tatsaechlich qualifizieren
sich in ueber einem Drittel aller Wurzelentscheidungen Alternativen und
werden getauscht. Das Gate greift also viel seltener als gedacht --
lesbar als Hinweis, dass das Sequential Halving am Ende mehrere
Kandidaten mit vergleichbarer Besuchszahl hinterlaesst.

**WERKZEUG-HINWEIS (wichtig fuer jede Wiederholung)**: Die Messung
BRAUCHT `tools/e3b_firing_rate.py`. `DENIAL_TIEBREAK_FIRED/TOTAL` sind
prozessglobale Atomics; `self_play.py` (frischer `mp.Process` je
10er-Chunk) und `paired_arena_env_ab.py` (Worker je Arm) wuerden sie im
KIND fuehren, der Elternprozess liest `(0, 0)` -- das saehe wie
"Feuerrate 0%" aus und haette die Abbruchregel FALSCH-POSITIV
ausgeloest. Der Treiber prueft darum zusaetzlich `total > 0` und meldet
sonst "INSTRUMENT KAPUTT" statt einer Rate.

**Deskriptiver Vorab-Hinweis, NICHT entscheidend**: In diesem Lauf (mit
E3b AKTIV) gewann das Netz 143/200 = 71,5%. Task A hat am selben Tag,
gleiche Sims, gleicher Gegner, aber anderem Seed und OHNE E3b 322/400 =
80,5% gemessen. Die ~9pp Abstand liegen bei einer Block-SE von ~2,9pp
in der Groessenordnung von 3 SE -- das ist ein ernstzunehmender Hinweis,
dass E3b wie E3 SCHADET. Entschieden wird das trotzdem erst durch die
GEPAARTE Stufe 2 (identische Seeds), weil hier zwei ungepaarte Laeufe
mit verschiedenen Seeds verglichen werden.

### ERGEBNIS Stufe 2 (2026-08-09): WACHE NICHT BESTANDEN -- E3b BLEIBT AUS

`tools/paired_arena_env_ab.py`, ein Faktor (`MOSAIC_DENIAL_UNCERT_Z`
0 vs 1,0, `_MIN_VISIT_FRAC=0,5` in BEIDEN Armen), Champion@400 vs
Heuristik@150dyn, 2x400 Partien, Basis-Seed 20260827. Belegstelle
`evaluations/paired_arena_env_e3b_stufe2.json`.

| Arm | Netz-Siege | Quote |
|---|---|---|
| **z=0 (aus, Kontrolle)** | **308/400** | **77,0%** |
| z=1,0 (E3b an) | 289/400 | 72,2% |

Differenz **-4,75pp** gegen E3b. Gepaarter exakter McNemar
**p=0,1042** (b=52 / c=71). Block-Ebene (Pflichtregel): 9 von 16
Bloecken fuer AUS, 4 fuer AN, 3 gleich; mittlere Block-Differenz +1,19
Siege je 25 Partien fuer AUS, Block-SE 0,67, **t=+1,78** (p~0,10).

**Entscheid nach Prereg: die Siegquoten-Wache ist das Gate, und sie ist
NICHT bestanden.** Die Nutzer-Philosophie lautet "rein, wenn es nicht
schadet" -- die Beweislast liegt also auf Schadensfreiheit, und die ist
mit einem Punktschaetzer von -4,75pp nicht erbracht. `z` bleibt auf 0,
E3b wird NICHT Preset und NICHT ins Self-Play uebernommen; der
Sekundaerpunkt z=2,0 entfaellt (er war "bei Bestehen" vorgesehen).

**Sauber formuliert**: p=0,10 ist KEIN Schadensnachweis. Der Befund ist
"Wirksamkeit nicht gezeigt, Richtung negativ", nicht "signifikant
schaedlich". Fuer den Entscheid genuegt das, weil die Wache Bestehen
verlangt und nicht Widerlegung.

**Damit ist die Denial-Tie-Break-Familie zweimal gemessen und
geschlossen**: E3 (rohes ε-Fenster) -13,75pp, E3b
(Besuchs-Gate + Zwei-Anteils-SE) -4,75pp. Die Neufassung der
Aequivalenz-Definition hat den Schaden verkleinert, aber keinen Gewinn
erzeugt. Die Aussagekraft ist hoch, nicht grenzwertig: bei einer
Feuerrate von 36,52% (Stufe 1) veraendert der Mechanismus mehr als ein
Drittel aller Wurzelentscheidungen -- ein Nullergebnis bei dieser
Eingriffstiefe ist gut gemessen, nicht untermotorisiert.
Wiedereroeffnung nur mit einem NEUEN Mechanismus, nicht mit einer
weiteren Dosis-Variante.

## Stufe 2 (nur bei ausreichender Feuerrate)

Zwei Arme a 400 Spiele, Champion@400 vs Heuristik@150dyn, identische
Seeds (tools/paired_arena_env_ab.py): Kontrolle (z=0 = aus) vs z=1,0.
Auswertung wie in der Stilmessung: **Siegquoten-Wache = Gate**
(Nutzer-Philosophie "rein, wenn es nicht schadet"), Raub-Metriken auf
Block-Ebene deskriptiv. Bei bestandener Wache: Uebernahme als
Live-Preset UND Self-Play (Diversitaets-Entscheid gilt sinngemaess),
Anker-Kante vor bewertetem Einsatz. Sekundaer bei Bestehen: z=2,0 als
Dosis-Punkt.

## Implementierung (klein, Env-Knopf-Muster)

`MOSAIC_DENIAL_UNCERT_Z` (Default 0,0 = AUS = byte-identisch) und
`MOSAIC_DENIAL_MIN_VISIT_FRAC` (Default 0,5); wirkt an derselben
Stelle wie E3 (`select_final_root_child`/Gumbel-Zweig), nutzt die
bereits vorhandenen Besuchszahlen und `opp_points_forecast`-Felder.
Das alte `MOSAIC_DENIAL_TIEBREAK_EPS` bleibt bestehen (refutiert,
Default 0) -- beide gleichzeitig gesetzt = Abbruch mit Fehlermeldung.
