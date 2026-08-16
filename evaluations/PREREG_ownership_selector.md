<!-- STATUS: OFFEN | Frage: Traegt der Ownership-Kopf, wenn er als SELEKTOR ueber eine Vorzugsroute im Tiling wirkt statt als Gewicht in der Blatt- und Nachsortier-Bewertung? | Beleg: **STUFE 0 GEMESSEN 2026-08-16** (par.9), Umbau noch nicht gebaut. Keine der beiden Abbruchregeln greift: Spalten-Konjunktion AUC 0,830 auf 36.611 Tiling-Zustaenden (Grundrate 0,0243), F2 faellt gegen F1 nur 3-5 % relativ ab. ABER der Entwurf aus par.3.1 ist WIDERLEGT: eine absolute Schwelle feuert bei 0,7 fuer Spalten in 0,22 % der Zuege und fuer Ecken in 72,4 % -- gleichzeitig zu selten und zu haeufig. Ursache: hervorragende Rangordnung (AUC 0,83-0,91) bei schlechter Kalibrierung (Brier nur 8-14 % besser als Grundrate). Ersetzt durch eine kalibrierungsfreie RANGREGEL mit Abstandsbedingung (par.9.3). Hauptrisiko gemessen: Spalten-AUC 0,698 in Runde 1 gegen 0,886 in Runde 5 -- der Kopf ist genau dort am schwaechsten, wo die Hilfe gebraucht wird. Anlass: Tor C negativ (Regler) UND Destillation ohne Zielkriterien-Wirkung (par.10.2 dort) -- beide Wege des Verbrauchers gescheitert, Diagnose heute am Code gefuehrt (par.1). Nutzer-Auftrag: "der ownership head muss rein". -->

# PREREG: Der Ownership-Kopf als SELEKTOR — Vorzugsroute statt Blattgewicht

Stand 2026-08-16, **ENTWURF — nichts hiervon ist gebaut.** Durchgehend
Plan-Zeitform. Nutzer-Auftrag nach dem doppelten Negativbefund: *"dann überleg
dir woran es liegt. der ownership head muss rein."*

---

## par.1 DIE DIAGNOSE — WARUM BEIDE BISHERIGEN WEGE SCHEITERN MUSSTEN

Alles in diesem Abschnitt ist **heute am Code geprueft**, mit Fundstelle.

### par.1.1 Die Platzierung ist nicht die Entscheidung des Netzes

`resolve_tiling_step` (`engine/src/self_play.rs:1093`) bestimmt, **WO** eine
gedraftete Farbe landet — nicht die Suche, nicht die Policy. Der Kommentar in
`engine/src/tiling_solver.rs:968-975` benennt die Folge selbst:

> "WO die gedraftete Farbe landet, entscheidet der Solver, nicht die Suche --
> in Runde 1 vollstaendig plattenblind, in den Runden 2-4 wirkt der Netzwert
> nur als Faktor auf den nach Platzierungspunkten gebildeten Kandidatenwert.
> Ein Ownership-Verbraucher, der nur am Blatt haengt, erbt genau diese
> Blockade."

Dort steht auch die zugehoerige Messung (`PREREG_placement_side.md`): die
Draftingseite allein saettigte bei **0,70 → 1,75** vertikalen Plattenpunkten
gegen ein Ziel von 14.

**Das erklaert zugleich das Destillations-Versagen** (`PREREG_corpus_distillation.md`
par.10.2): die Policy waehlt den DRAFT, die Platzierung macht ein Loeser.
Spaltenbau lebt in der Platzierung. Kein Korpus kann einer Policy ein Verhalten
beibringen, fuer das sie keinen Ausgang hat.

### par.1.2 Die Hilfe erscheint genau dann, wenn sie nicht mehr noetig ist

Platzierungsregel, **abgelesen** aus `docs/engine_manual.md:143-148`: eine
Fliese ohne orthogonalen Nachbarn zahlt **1**; eine, die eine zusammenhaengende
Linie fortsetzt, zahlt die **volle Linienlaenge** (Farbe irrelevant); wer
horizontal und vertikal zugleich schliesst, bekommt **beides** bezahlt.

Daraus folgt (Nutzer-Korrektur 2026-08-16, die eine falsche Fassung dieser
Prereg-Begruendung ersetzt — sie lautete "auch wenn das jetzt null Punkte
bringt"):

- Spaltenbau ist **spaet punkt-konform**: die 6. Fliese einer Spalte zahlt 6
  Sofortpunkte plus 7 Plattenpunkte.
- Spaltenbau ist **frueh punkt-teuer**: die erste Fliese einer neuen Spalte im
  leeren Bereich zahlt 1, dieselbe Fliese am Cluster 3–4. Der Plan kostet also
  einen kleinen Kredit ueber ein bis zwei Zuege.

Der marginale Feldwert der Produktform (`scoring.rs:539`) verhaelt sich **genau
invers dazu**: er ist ~0, solange die Geometrie leer ist, und maximal, wenn sie
fast fertig ist — also dann, wenn die Sofortpunkte ohnehin dorthin zeigen.

> **Der Verbraucher hilft am Ende eines Plans, den er am Anfang nicht anstossen
> kann.** Das ist Tor Cs Diagnose "stupst an, plant nicht" in ihrer genauen,
> regelgestuetzten Form.

### par.1.3 Die Produktform unterdrueckt zusaetzlich genau die Zielkriterien

Marginalwerte, **hergeleitet aus den exakten Formeln** in
`engine/src/scoring.rs:461-533`, ausgewertet bei p = 0,5 (die Form ist
multilinear, `marginal = (1-p) * dE/dp`):

| Kriterium | Form | Marginalwert bei p=0,5 |
|---|---|---:|
| **k1** vertikale Reihe (6 Felder, +7) | Produkt | **0,109** |
| **k2** Diagonale (6 Felder, +10) | Produkt | **0,156** |
| k5 Eckplatte (4 Felder, +8) | Produkt | 0,500 |
| k4 Randfelder (+1 je Feld) | additiv | 0,500 |
| k6 Spezialfelder (−3 je leerem) | additiv | 1,500 |

Die beiden Zielkriterien haben die **kleinsten Marginalwerte von allen**,
Faktor 3 bis 14 gegen die additiven. Das ist keine Kalibrierfrage, sondern die
Bauform: ein Produkt ueber 6 Faktoren < 1 kollabiert. Es erklaert Tor Cs
Monotonie — mehr Gewicht heisst mehr Zug zu k3/k4 — und es erklaert, warum k5
(**kurze** Konjunktion, 4 statt 6 Felder) das einzige Zielkriterium mit
brauchbarem Absolutwert ist.

Diese Zahlen sind eine **Herleitung bei angenommenem p=0,5**, keine Messung an
echten Kopfausgaben. Stufe 0 misst die tatsaechliche Verteilung nach.

### par.1.4 Wir haben das Richtige trainiert und lesen es nicht

`_conjunctions_from_dome` (`engine/py/neural_net.py:932`) liefert **34 Atome je
Spieler**, und zwar auf GEOMETRIE-Ebene, nicht auf Kriteriums-Ebene:

| Index | Atom | Punktwert |
|---|---|---|
| 0..5 | Reihe r vollstaendig | +3 |
| **6..11** | **Spalte c vollstaendig** | **+7** |
| **12..13** | **Diagonale d vollstaendig** | **+10** |
| **14..17** | **Eckplatte voll** | +3/+3/+8/+8 |
| 18 | alle Jokerfelder belegt | 2 x wild_total |
| 19..24 | Reihe r hat >= 5 Farben | +4 |
| 25..33 | Slot traegt Jokerplatte (Layout) | — |

Der Kopf schaetzt also **je einzelner Spalte** die Vollendungswahrscheinlichkeit
— exakt die Groesse, die ein Selektor braucht ("welche Spalte lohnt sich?").
Der Verbraucher liest sie nicht: `apply_ownership_shaping_full`
(`engine/src/net_mcts.rs:1655`) nutzt nur `[0:72]` und rekonstruiert die
Konjunktion durch Multiplikation. Der Kommentar dort
(`net_mcts.rs:1620-1638`) sagt es selbst und zitiert den Python-Docstring
gegen sich: *"P(alle 6 Felder) ist nicht das Produkt der
Einzelwahrscheinlichkeiten"*, die Konjunktions-Ausgaenge seien "heute
UNGENUTZT".

### par.1.5 Der Mechanismus, der nachweislich Platten baut, sieht anders aus

Der Spaltenbauer wirkt ueber `column_build::vorzug_tiling_step`
(`engine/src/tiling_solver.rs:1467`) als **Vorzugsroute mit Frueh-Ausstieg**,
VOR der punktbasierten Kandidatenbildung. Ergebnis (Korpus par.8):
Spaltendeckung **3,2 % → 42 %**. Der Ownership-Kopf hat nichts Vergleichbares —
er ist ein Gewicht in einer Nachsortierung von `top_k_tilings`
(`MAX_TILING_LEAVES = 400`, `tiling_solver.rs:622`).

**Gegenbeleg, der die Grenze markiert** (`tiling_solver.rs:1473-1477`): ein
Plattenterm, der den Netz-Stichentscheid VERDRAENGTE statt ihn zu ergaenzen,
mass **0,70 gegen 2,10** — schlechter. Eine Vorzugsroute ist deshalb NICHT
"Plattenterm gewinnt immer", sondern eine eng bedingte Ausnahme (par.3.1).

### par.1.6 Die Ein-Satz-Diagnose

> Tor A hat gezeigt, dass der Kopf gut ERKENNT, welche Geometrie vollendbar ist
> (Feld-AUC 0,78–0,87), und nur maessig schaetzt, WIE VIEL sie bringt
> (E_k-Rangkorrelation 0,28–0,47). **Wir haben ihn als Wertfunktion benutzt.
> Er ist ein Selektor.**

---

## par.2 GEPRUEFTER IST-STAND

| Sache | Befund | Pruefstelle |
|---|---|---|
| Blatt-Verbraucher liest nur `[0:72]` | Produktform, Konjunktionen ungenutzt | `net_mcts.rs:1620-1655` |
| Tiling-Verbraucher | Term IN `best_first_step_platten_valued`, nach `top_k_tilings` | `tiling_solver.rs:1224` |
| `MOSAIC_OWNERSHIP_TILING_W` | Default **0,0** | `tiling_solver.rs:1006` |
| `MOSAIC_TILING_PLATTEN_W` | Default **0,0** | `tiling_solver.rs:964` |
| Vorzugsroute-Muster existiert | `column_build::vorzug_tiling_step`, Frueh-Ausstieg vor allem anderen | `tiling_solver.rs:1467` |
| Kandidatendeckel | `MAX_TILING_LEAVES = 400` | `tiling_solver.rs:622` |
| Konjunktions-Atome | 34 je Spieler, Geometrie-Ebene, Spalten `6..11` | `neural_net.py:932-958` |
| Platzierungspunkte | 1 ohne Nachbar, sonst Linienlaenge, beide Richtungen getrennt bezahlt | `docs/engine_manual.md:143-148` |
| k2 und k5 nie zusammen; k1 und k4 nie zusammen | Ausschlusspaare (0,7)(6,3)(4,1)(2,5) | `scoring.rs:59-65` |
| Staerkster Checkpoint | `w0_best`, 333/407 gegen Heuristik@150 | `PREREG_corpus_distillation.md` par.8.4 |
| `w0_best` hat **untrainierten** Kopf | `ownership_weight: 0.0` | `manifest_train_v21_2d_own_w0_20260815_015638.json` |
| F1-Policy == W1-Policy, bitgleich | 0 diskordante Paare auf 407 Seeds | `PREREG_corpus_distillation.md` par.8.4 |

**Ungeprueft / uebernommen:** die Tor-A-Guetezahlen (Feld-AUC, E_k-Rang) sind
aus `PREREG_ownership_corpus.md` par.10 und `PREREG_frozen_trunk_head.md` par.7
uebernommen, hier nicht nachgerechnet.

---

## par.3 DIE DREI UMBAUTEN (Plan, nichts gebaut)

Alle drei folgen dem Task-#28-Muster: **neuer Knopf, Default 0 = Frueh-Ausstieg
= byte-identisch.** Kein Bestandsverhalten aendert sich ohne gesetzten Knopf.

### par.3.1 Umbau A — die Selektor-Vorzugsroute (der Kern)

Neuer Knopf `MOSAIC_OWNERSHIP_ROUTE_P`, Default 0,0 = aus.

Einmal je Tiling-Zug (die Ownership-Karte liegt aus
`self_play.rs::ownership_tiling_marginals` ohnehin vor, ein Vorwaertspass):

1. **Zielwahl** — unter den Atomen der AKTIVEN Kriterien (`scoring_tile_ids`)
   das mit der hoechsten Konjunktionswahrscheinlichkeit `p_atom`; nur Atome der
   Zielkriterien k1/k2/k5 (Spalten `6..11`, Diagonalen `12..13`, Ecken
   `14..17`).
2. **Schwelle** — feuert nur, wenn `p_atom >= MOSAIC_OWNERSHIP_ROUTE_P`.
3. **Route** — gibt es unter den legalen Platzierungen eine, die ein noch
   fehlendes Feld GENAU DIESER Geometrie belegt, wird sie gewaehlt
   (Frueh-Ausstieg, Muster `column_build::vorzug_tiling_step`). Bei mehreren:
   die mit den hoechsten Sofortpunkten — die Route waehlt die Geometrie, nicht
   die Zelle.

**Warum eine Schwelle und keine Gewichtung:** eine Gewichtung ist genau das,
was in Tor C gescheitert ist, und par.1.5 zeigt, dass Verdraengung ohne
Bedingung schadet (0,70 gegen 2,10). Die Schwelle macht die Route zur eng
bedingten Ausnahme: sie feuert nur, wenn der Kopf sich sicher ist.

**Kostenbedingung bleibt:** kein Netz-Aufruf je Kandidat. Die Route liest die
bereits berechnete Karte.

### par.3.2 Umbau B — den Konjunktions-Ausgang tatsaechlich lesen

`E_k = punkte_k * p_k^conj` statt `punkte_k * PROD p_f`, sobald der Kopf 140
breit ist. Bei 72er-Koepfen (amtierender Champion) faellt es auf die
Produktform zurueck — die Kopfbreiten-Agnostik aus `net_mcts.rs:1630` bleibt
damit erhalten, sie wird nur nicht mehr um den Preis der Genauigkeit erkauft.

Fuer die vom Tiling gebrauchten FELD-Marginalwerte, die aus einer
Konjunktionsausgabe nicht direkt ableitbar sind (der dritte Grund in
`net_mcts.rs:1636`), wird der Kriteriumswert auf die noch fehlenden Felder
verteilt statt multipliziert:

```text
wert(f) = punkte_k * p_k^conj * (1 - p_f) / SUM_{g in Geometrie} (1 - p_g)
```

Wohldefiniert, kostet nichts, und kollabiert nicht.

### par.3.3 Umbau C — Normalisierung je Kriterium

Jeder Kriteriums-Marginalwert wird durch seinen eigenen Maximalwert geteilt,
damit eine 6-Feld-Konjunktion ueberhaupt gegen ein additives Kriterium antreten
kann (par.1.3). Eigener Knopf, damit A und C getrennt messbar bleiben.

---

## par.4 DAS VEHIKEL-PROBLEM (vor dem Bau zu loesen)

**Der staerkste Checkpoint hat keinen Kopf, und die Checkpoints mit Kopf sind
schwaecher.** `w0_best` (333/407) wurde mit `ownership_weight 0,0` trainiert,
sein Kopf ist untrainiert. `w1_best`/`f1` haben einen brauchbaren Kopf, aber
321/407.

Kandidat: **F3 = Frozen-Trunk-Kopftraining auf `w0_best`** — dasselbe Rezept
wie F1/F2, nur mit `w0_best` als Basis. Der Frozen-Trunk-Riegel ist heute live
belegt (F1 == W1 auf 407 Seeds, 0 diskordant), die Policy bliebe also exakt die
von `w0_best`. Das gaebe **staerkste Policy + trainierten Kopf**.

Offen und von Stufe 0 zu beantworten: ob ein Trunk, der nie einen
Ownership-Gradienten gesehen hat, einen brauchbaren Kopf traegt. Genau das
misst F2 (Frozen-Trunk auf dem Champion, fertig 2026-08-16, Ownership-Val
0,3673, Plateau ab Epoche 9) — dessen Tor-A-Auswertung steht noch aus und ist
Vorbedingung fuer F3.

---

## par.5 STUFENPLAN MIT ABBRUCHREGELN (vorab festgelegt)

### Stufe 0 — offline, kein Bau, keine Arena

1. **F2 Tor A** (`tools/probes/ownership_gate_a.py`): Feld-AUC und E_k-Rang
   gegen F1 (0,780 / 0,280 / 0,314 / 0,345). **Abbruch fuer F3**, wenn F2
   deutlich unter F1 liegt — dann traegt ein ownership-blinder Trunk keinen
   Kopf, und das Vehikel muss `f1` bleiben.
2. **Kalibrierung der Konjunktions-Atome fuer k1/k2/k5** auf dem Held-out:
   Brier und AUC je Atomgruppe gegen die Grundrate, plus Zuverlaessigkeitskurve.
   **ABBRUCHREGEL: Ist `p_atom` fuer die Spalten-Atome (6..11) nicht besser als
   die Grundrate, wird Umbau A nicht gebaut.** Eine Schwellenregel auf einem
   unkalibrierten Wert ist ein Muenzwurf mit Extraschritten.
3. **Verteilung von `p_atom` messen** — daraus wird das Schwellenraster
   abgeleitet, nicht geraten (Lehre aus Tor C, wo das Dosisraster aus der
   tanh-Skala kam und alle vier Stufen zu gross waren).

### Stufe 1 — gebaut, aber ohne Staerkeaussage

4. **Tor B**: `MOSAIC_OWNERSHIP_ROUTE_P = 0` byte-identisch, Paritaets-Hash
   `8c6684ff...` haelt.
5. **Feuerrate und Trefferlage**: wie oft feuert die Route je Partie, in welcher
   Runde, und wie oft fuehrt ein Feuern zu einer tatsaechlich vollendeten
   Geometrie? **ABBRUCHREGEL: feuert sie in weniger als 1 % der Tiling-Zuege
   oder fast nur in Runde 5, wird Stufe 2 nicht gefahren** — dann ist es wieder
   Hilfe am Ende des Plans (par.1.2).

### Stufe 2 — Arena, die einzige Staerkeaussage

6. Schwellenraster aus Stufe 0 Punkt 3, gepaart gegen den w_own=0-Arm desselben
   Checkpoints, 407-Seed-Satz aus `PREREG_corpus_distillation.md` (>= 150
   Partien je Kriterium, 6 tragende Bloecke — dieselbe Stichprobe, damit die
   Zahlen vergleichbar sind), Block-Ebene, Blockgroesse 25.

---

## par.6 VORAB-ERFOLGSREGEL (woertlich, vor der ersten Entscheidungspartie)

> **ERFOLG** heisst: die Route hebt **k1 oder k2** signifikant auf Block-Ebene
> — **und** verliert dabei keine Siege signifikant (exakter zweiseitiger
> McNemar, p >= 0,05 zugunsten des Kontrollarms).

**Ein Plattenzuwachs, der Siege kostet, ist KEIN Erfolg.** Das ist zum fuenften
Mal dieselbe Regel und zum fuenften Mal aus demselben Grund: k6-Kuppeldraft,
Stoerungs-v1, Tor C D2/D3 und der k3-Zuwachs der Destillation haben alle
Platten gehoben und entweder Siege gekostet oder am Ziel vorbeigezielt.

**k3/k4 zaehlen ausdruecklich NICHT als Erfolg.** Ein Zuwachs, der wieder aus
den Zaehl-Kriterien kommt, ist das dritte Auftreten desselben Musters und
belegt die Plattenagenda nicht.

**Kein Nachziehen der Stichprobe**, keine nachtraegliche Schwellenwahl: die
Schwelle, die in Stufe 2 als Sieger gilt, muss in Stufe 0 Punkt 3 im Raster
gestanden haben.

**Auswertungsebene BLOCK** (stehende Regel seit 2026-08-04), Partie-Ebene wird
zusaetzlich ausgewiesen.

---

## par.7 KOSTEN (geschaetzt, nicht gemessen)

| Stufe | Aufwand |
|---|---|
| Stufe 0 Punkt 1+2 | Sonden auf vorhandenen Daten, < 1 h |
| F3-Training (falls Stufe 0 gruen) | ~4 h GPU (F2-Rezept) |
| Umbau A | ein Zweig in `best_first_step_exact_or_valued_ex`, Muster liegt vor |
| Stufe 1 | Paritaetsprobe + Instrumentierung, ~1 h |
| Stufe 2 | je Arm 407 Partien x ~2,8 s = ~20 min |

---

## par.8 RISIKEN UND OFFENE PUNKTE

1. **Die Route koennte den Loeser schlechter machen**, weil sie die
   Sofortpunkt-Optimierung uebersteuert. Der Gegenbeleg aus par.1.5 (0,70 gegen
   2,10) betraf eine BEDINGUNGSLOSE Verdraengung; die Schwelle soll genau das
   verhindern. Ob sie es tut, entscheidet Stufe 2, nicht dieses Argument.
2. **Ausschlusspaare**: k1 und k4 kommen nie zusammen vor, k2 und k5 auch nicht
   (`scoring.rs:59-65`). Der in par.1.3 beschriebene Wettbewerb k1-gegen-k4
   kann in EINER Partie also gar nicht auftreten — der reale Konkurrent von k1
   ist k6 (Marginalwert 1,5, Faktor 14). Das aendert die Diagnose nicht, aber
   die Zahl, die man zitiert.
3. **Der Kopf sagt den ENDZUSTAND voraus**, nicht die Erreichbarkeit unter
   optimalem Spiel. Eine hohe `p_atom` heisst "wird wahrscheinlich voll",
   nicht "lohnt sich anzusteuern". Bei einem Selektor ist das weniger
   schaedlich als bei einer Wertfunktion (die Rangfolge genuegt), aber es ist
   dieselbe Konfundierung wie in
   `feedback_skill_confound_already_determined` — die Schwelle koennte
   schlicht Geometrien waehlen, die ohnehin vollgelaufen waeren. **Stufe 1
   Punkt 5 ist genau dagegen gebaut**: wenn die Route fast nur in Runde 5
   feuert, misst sie Vergangenheit statt Absicht.
4. **Kriterium 7** bleibt ausserhalb (`neural_net.py:958`: das Ziel dort ist
   belegt/leer ohne Farbe). k0/k7 sind ohnehin "verteidigen, nie anstreben".

---

## par.9 ERGEBNIS STUFE 0 (2026-08-16, abends)

Beide Sonden gelaufen, alle tragenden Zahlen vom Koordinator an den
Roh-JSONs nachgeprueft. **Keine der beiden Abbruchregeln greift — aber
Stufe 0 hat den Entwurf aus par.3.1 widerlegt** (par.9.3). Genau dafuer war
sie da.

### par.9.1 Kopfguete F2 gegen F1 (Stufe 0 Punkt 1)

`evaluations/ownership_gate_a_f1_f2.json`, Sonde
`tools/probes/ownership_gate_a.py`, beide Arme ueber den `final`-Tag
(Epoche 15). Held-out identisch: 820 Partien, 82 Val-Dateien.

| Metrik | F1 (Trunk sah Ownership-Gradient) | F2 (Trunk sah ihn nie) |
|---|---:|---:|
| Feld-AUC me / opp | 0,780 / 0,715 | 0,749 / 0,682 |
| Konjunktion Spalten AUC | **0,909** | 0,866 |
| Konjunktion Diagonalen AUC | 0,924 | 0,893 |
| Konjunktion Ecken AUC | 0,918 | 0,885 |
| E_k-Rang Spalten / Ecken | 0,280 / 0,345 | 0,265 / 0,275 |

**MANGEL DER VORREGISTRIERUNG, ausdruecklich benannt:** die Abbruchregel in
par.5 sagt "deutlich unter F1" und nennt **keine Zahl**. Sie ist damit
nachtraeglich auslegbar, und genau das musste hier geschehen — der
ausfuehrende Agent hat den Mangel selbst angezeigt statt ihn zu ueberspielen.
Auslegung des Koordinators: die Regel war gegen *"traegt keinen Kopf"*
formuliert; F2 faellt konsistent um 3–5 % relativ ab, kollabiert aber nirgends
zur Grundrate. **Die Regel greift nicht.** Kuenftige Abbruchregeln bekommen
eine Zahl.

**Folge:** F3 (Frozen-Trunk-Kopf auf `w0_best`) wird gebaut — gestartet
2026-08-16 16:04. Begruendung: `w0_best`s Trunk hat den Korpus gesehen, nur
nicht den Ownership-Gradienten, liegt also strikt zwischen F2 und F1. Ein
Rangverlust von wenigen Prozent gegen +12 Siege Policy-Staerke (333 statt
321 von 407) ist ein guter Tausch, wenn nur der RANG benutzt wird.

### par.9.2 Kalibrierung dort, wo die Route liest (Stufe 0 Punkte 2+3)

`evaluations/ownership_route_calibration_results.json`, neue Sonde
`tools/probes/ownership_route_calibration.py`. **Methodisch besser als
beauftragt:** gemessen wird nicht am Endzustand wie Tor A, sondern auf den
**36.611 Tiling-Zustaenden**, an denen die Route tatsaechlich lesen wuerde
(Runden r1..r5 = 4806/7284/8193/7875/8453).

| Gruppe (F1) | Grundrate | Brier (Basis) | AUC |
|---|---:|---:|---:|
| Spalten 6..11 | 0,0243 | 0,0200 (0,0217) | 0,830 |
| Diagonalen 12..13 | 0,0267 | 0,0237 (0,0264) | 0,911 |
| Ecken 14..17 | 0,2702 | 0,0939 (0,1255) | 0,844 |

Kein Einzelatom traegt das Makro-AUC allein (Spalten je Atom 0,759–0,890).

**Abbruchregel 2 ("p_atom fuer Spalten nicht besser als die Grundrate")
greift nicht**: AUC 0,830 gegen 0,5, konsistent ueber alle sechs Atome.

**Zuverlaessigkeit:** Ecken gut kalibriert; Spalten und Diagonalen ueber 0,5
deutlich **ueberschaetzt** (F1-Top-Bin Spalten: vorhergesagt 0,949,
tatsaechlich 0,733 — aber n=15, also eine schwach gestuetzte Punktschaetzung,
vom W1-Muster nur gestuetzt, nicht belegt).

**Konfundierung nach Runde** (par.8 Punkt 3), Spalten-AUC:

| r1 | r2 | r3 | r4 | r5 |
|---:|---:|---:|---:|---:|
| 0,698 | 0,795 | 0,823 | 0,867 | 0,886 |

Der Kopf weiss mehr, je weiter die Geometrie schon ist — die Konfundierung
ist **real und messbar**. Sie ist aber **nicht vollstaendig**: schon in Runde 1
liegt die AUC bei 0,698, klar ueber Zufall. Sauber trennen laesst sie sich mit
diesen Daten nicht (kein kontrafaktischer "gleicher Fuellgrad, andere
Runde"-Vergleich moeglich) — ausdruecklich als UNGETRENNT markiert.

### par.9.3 DER ENTWURF AUS par.3.1 IST WIDERLEGT — Feuerraten

Anteil der Tiling-Zustaende, in denen eine absolute Schwelle feuern wuerde
(Zustandsebene, MAX ueber die Atome der Gruppe):

| Schwelle | Spalten | Diagonalen | Ecken |
|---|---:|---:|---:|
| >= 0,3 | 2,0 % | 2,6 % | **98,9 %** |
| >= 0,5 | 0,7 % | 1,1 % | **91,4 %** |
| >= 0,7 | **0,22 %** | **0,47 %** | **72,4 %** |

Quantile Spalten (Zustands-Max): p50 0,020 · p75 0,041 · p90 0,091 ·
p95 0,156 · **p99 0,422**. Hoeher kommt der Kopf fuer Spalten praktisch nie.

> **Eine absolute Schwelle ist gleichzeitig zu selten und zu haeufig.** Fuer
> die Zielkriterien feuert sie bei 0,7 in 0,22 % der Zuege — mein eigener
> Entwurf haette damit die Stufe-1-Abbruchregel ("unter 1 %") gerissen. Fuer
> die Ecken feuert dieselbe Schwelle in 72,4 % der Zuege, waere also keine
> Ausnahme mehr, sondern der Normalfall — und damit exakt die
> bedingungslose Verdraengung, die laut par.1.5 gemessen geschadet hat
> (0,70 gegen 2,10).

Ursache ist der Befund aus par.9.1/par.9.2 zusammengenommen: **hervorragende
Rangordnung bei schlechter Kalibrierung.** Spalten-AUC 0,909 (Endzustand) bzw.
0,830 (Tiling-Zustaende), aber der Brier verbessert sich nur um 8–14 % gegen
die Grundrate. Der Kopf weiss sehr genau, WELCHE der sechs Spalten vollaeuft,
und kaum, mit welcher Wahrscheinlichkeit. Das ist die dritte unabhaengige
Bestaetigung der These aus par.1.6 — nun auch in der Kalibrierung.

**GEAENDERTER ENTWURF (par.3.1 wird ersetzt, nicht ergaenzt):**

1. **Rangregel statt absoluter Schwelle.** Gewaehlt wird das Atom mit der
   hoechsten `p_atom` unter den Atomen der AKTIVEN Zielkriterien. Ein Rang ist
   kalibrierungsfrei — genau die Eigenschaft, an der die Schwelle scheitert.
2. **Abstandsbedingung als Regler** statt eines Wahrscheinlichkeitsniveaus:
   die Route feuert nur, wenn das beste Atom das zweitbeste um den Faktor
   `MOSAIC_OWNERSHIP_ROUTE_MARGIN` uebertrifft (Default 0 = aus). Damit ist
   die Feuerrate stetig steuerbar, unabhaengig davon, wo die absoluten Werte
   einer Gruppe liegen.
3. **Ecken werden nach Punktwert getrennt.** Die Gruppe mischt zwei billige
   Ecken (Grundrate 0,68 / 0,30, je +3) mit zwei teuren (0,038 / 0,056, je
   +8). Ein gruppenweiter Wert verwischt genau den Unterschied, auf den es
   ankommt.
4. Das **Raster fuer Stufe 2** wird aus der Feuerraten-Messung von Stufe 1
   abgeleitet und VOR Stufe 2 festgeschrieben.

**Die Erfolgsregel in par.6 bleibt unveraendert.** Geaendert wird die Bauform,
nicht der Massstab.

### par.9.4 Das gemessene Hauptrisiko

Die Hilfe wird **frueh** gebraucht (par.1.2: der Plan kostet nur die ersten
ein bis zwei Zuege etwas), und dort ist der Kopf am schwaechsten
(Spalten-AUC 0,698 in Runde 1 gegen 0,886 in Runde 5). Das ist kein
Ausschlussgrund — 0,698 ist deutlich ueber Zufall —, aber es ist die Stelle,
an der dieser Umbau scheitern wird, wenn er scheitert. **Stufe 1 Punkt 5 ist
genau dagegen gebaut** und bleibt bindend.


## par.10 ERGEBNIS STUFE 1 (leer bei Registrierung)

## par.11 ERGEBNIS STUFE 2 (leer bei Registrierung)

## par.12 VERDIKT NACH DER VORAB-REGEL (leer bei Registrierung)
