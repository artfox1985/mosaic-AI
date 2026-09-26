# Externe Recherche: Architektur des Bewerters (Trunk, Koepfe, Ziele, Konsum)

**Weiterverarbeitung:** E1-E4 sind am 2026-09-25 in `PREREG_evaluator_pretests.md` eingetaktet
(Vortests vor jedem Arm; E1 bekommt seinen Arm auf Nutzer-Entscheid sicher).
**Stufe 1 gefahren 2026-09-26** (dort par.8a): E1 gleich gut, E2 besteht, E3 tot; und der
Kopf schlaegt im Mittelspiel den linearen Leser seiner Eingabe, die Auslese-Luecke aus 2.1 ist
endspiel- und zielspezifisch.

**Datum:** 2026-09-25. **Auftrag (Koordinator, auf Nutzer-Feedback):** Literatur plus Code-Lesen
zur Frage, wie die ARCHITEKTUR des Bewerters optimiert werden kann. Vier Teilfragen: (A)
Auslese-Luecke Trunk gegen Koepfe, (B) relationale Struktur Drafting x Tiling, (C)
Rundenuebergang netzseitig, (D) Punkte gegen Sieg. Ergebnis ist ein Bericht; nichts gebaut,
nichts gelaufen (auf der Maschine laeuft die v33-Erzeugung exklusiv).

**Randbedingungen:** "keine neuen Koepfe" (Nutzer 2026-09-14); nichts vorschlagen, was schon
gefahren ist (Nutzer 2026-09-25); Mehrkosten gegen Self-Play-Partien abwaegen.

**Belegkonvention (REGEL 0).** Jede Sachaussage traegt eine Pruefstelle oder eine Marke:

* `[GEPRUEFT]` in dieser Sitzung an der genannten Stelle gelesen (Code `datei:zeile`, Prereg-Absatz, URL).
* `[UEBERNOMMEN]` Zahl aus einem Prereg-Kopf, Kommentar oder Recherche-Dokument, NICHT an der
  Primaerquelle (Artefakt) nachgeprueft. Liste am Ende.
* `[HERLEITUNG]` eigene Rechnung oder Schluss, nicht gemessen. `[UNGEPRUEFT]` Annahme.
* Belegstufen externer Quellen: PAPER (begutachtet oder arXiv), ENGINE (Produktionscode/Doku
  einer Engine), BLOG, HERLEITUNG.

**Umrechnung der Kosten (fuer alle Vorschlaege):** eine Maschinenstunde entspricht rund
**1.000 Self-Play-Partien** @100 Sims, 11 Threads (v28: 3,183 s bzw. 2,908 s je Partie,
`docs/measured_runtimes.md`, Abschnitt Generation v28; v25: 3,607 s) `[GEPRUEFT]`, gerundet.
Ein Warmstart-Training kostete bei `v32-b01` 63 min (`PREREG_INDEX.md`, Zeile v32_window)
`[UEBERNOMMEN]`, auf dem 884-Wheel 72 min (`measured_runtimes.md`, v29-b09) `[GEPRUEFT]`. Ein
Tor-1-Seed mit 200 Paaren kostet 4.794-5.090 s (`measured_runtimes.md`, v29-b07/b09)
`[GEPRUEFT]`, zwei Seeds also rund 2,7 h. Ein Kostentor mit 2 x 20 Paaren rund 16 min
(11,3-12,0 s je Partie, ebenda) `[GEPRUEFT]`.

---

## 0. Kurzfassung

Die Literatur hat fuer unseren Fall (kleines CPU-Netz, 400 Sims, Zufall zwischen Runden,
Auslage-Mechanik) **keine direkte Vorlage**. Belastbar uebertragbar sind vier Muster: (1) ein
Zweispieler-Nullsummen-Bewerter bewertet in AlphaZero EINMAL aus Sicht des Ziehenden und
spiegelt, statt eine zweite, im Training nie gesehene Sicht zu rechnen; (2) Ordinal-/
Schwellenmodelle (Backgammon-Ausgaenge, CORAL) koppeln einen Siegwert an die Marge, ohne das
Ziel zu wechseln; (3) phasenabhaengige Ausgabeschichten (Stockfish-Layer-Stacks, Rzepecki)
sind in Brettspiel-Engines Standard; (4) abgeleitete Eingabemerkmale schlagen Architekturwechsel
bei gleicher Rechenklasse (Schach: +97 Elo Merkmale gegen +30 Elo Transformer). Die
Empfehlungsliste (Abschnitt 7) folgt daraus; drei von fuenf Punkten lassen sich vor jeder
Self-Play-Stunde offline auf dem eingefrorenen Champion toeten.

Ein Befund aus dem Code-Lesen steht vorn, weil er billig ist: **die Wurzelentscheidung wird
zu einem grossen Teil von einem Vorwaertspass getragen, dessen Eingabe es im Training nicht
gibt** (Abschnitt 2.4). Der Test, der ihn 2026-07-20 verwarf, konnte ihn nach Aufloesung und
Aera nicht treffen.

---

## 1. Ist-Architektur (mit Pruefstellen)

**Eingang.** Flachvektor `INPUT_SIZE = 888` (`config.py:49`) `[GEPRUEFT]`, Champion-Manifest
`input_size: 888` (`models/manifest_train_v32-b01_20260923_075819.json`) `[GEPRUEFT]`; dazu
Planes `NUM_PLANES_CHANNELS = 79` auf 6x6 (`engine/src/features.rs:1673`) `[GEPRUEFT]`.
Runde und Phase stehen als je EIN Skalar im Vektor: `round_number / 6`, `phase_id / 3`
(`features.rs:1289-1290`) `[GEPRUEFT]`. Die kleinen Fabriken sind je Fabrik als Farbzaehlung
der Sonnenseite /5 plus Chip-Bits kodiert, die grosse als Farbzaehlung /10
(`features.rs:804-853`); Musterreihen als Fuellgrad plus Farb-One-hot (`features.rs:869-879`)
`[GEPRUEFT]`. Die Beziehung "welche Quelle fuellt welche Reihe" steht NICHT als Merkmal im
Vektor; das Netz muss sie aus den Zaehlungen lernen (Grep nach Angebot/takeable/verfueg/
supply in `features.rs`: nur Beutel-/Turm-Zaehlung, `features.rs:1295-1303`) `[GEPRUEFT]`.
Die Tiling-Projektion der jetzt vollen Reihen (Variante C, 90 Werte) ist Eingabe
(`PREREG_round_transition_search_sampling.md` par.18.1) `[GEPRUEFT]`.

**Trunk (`Mosaic2DNet`, `engine/py/neural_net.py:2096-2391`)** `[GEPRUEFT]`:

* Conv-Zweig: `conv_layers` x (Conv 3x3, `conv_channels`, BN, ReLU), Konstruktor-Default 2 x 48
  (`neural_net.py:2120, 2146-2156`). Ob der Champion die Defaults nutzt, steht nicht im
  Trainings-Manifest `[UNGEPRUEFT]`.
* Flach-Zweig: Linear(888 -> 512), BN, ReLU (`:2162-2166`); `hidden: null` im Manifest heisst
  `HIDDEN_SIZE = 512` (`config.py:93`).
* Fusion: Linear(48*36 + 512 -> 512), BN, ReLU, Linear(512 -> 512), ReLU (`:2168-2174`).
* Rechenaufwand je Vorwaertspass `[HERLEITUNG]`, Multiplikationen ohne Ownership-Kopf: Flach
  0,45 Mio, Conv 1,98 Mio, Fusion 1,41 Mio, Policy 0,24 Mio, uebrige Koepfe unter 0,15 Mio,
  zusammen **rund 4,2 Mio MAC**.

**Koepfe** `[GEPRUEFT]`: Policy 512 -> 256 -> 414 (`:2179-2184`, `NUM_ACTIONS = 414`,
`config.py:57`); Value WDL 512 -> 64 -> 2, `p_win = softmax[1]`, ausgegeben als `2 p_win - 1`
(`:2197-2202, 2362-2367`); Punkte 512 -> 64 -> 1, tanh (`:2222-2227`); Gegnerpunkte gleiche
Bauform (`:2249-2256`, im Champion aktiv: Manifest `opp_points_head: true`); Mond und Ownership
mit Gewicht 0 (Kette `--moon-loss-weight 0.0 --ownership-weight 0.0`,
`tools/night_v33_chain.sh:183-184`).

**Ziele und Verlust** `[GEPRUEFT]`: Verlust `p + 0,2 v + 0,5 points + 0,5 opp`
(`train.py:724-729`, `config.py:106-107`; Manifest `value_weight`/`points_weight` null =
Defaults). Value-Ziel `values_wdl` mit `--value-target-lambda 0.7` (Mischung mit dem
Wurzel-Q, `neural_net.py:1349-1368`; Kette `night_v33_chain.sh:183`). Punkte-Ziel
`tanh(eigener Endstand / 50)` (`neural_net.py:1104, 1342`). Das Value-Ziel ist margenblind
(`docs/architecture_reference.md:88-90`).

**Konsum in der Suche** `[GEPRUEFT]`:

* Blattwert = `P(Sieg)` des Value-Kopfs; die Punkte-Koepfe gehen bei `w = 0` nicht ein
  (`engine/src/net_mcts.rs:2897-2898`, Default `MOSAIC_POINTS_UTILITY_W = 0`, `:195`).
* Danach zustandsbasierte Nullsummen-Additive: Floor-Shaping (`:3619-3635`), Huelle
  `C_HULL = 1,0` in der Gating-Spec (`models/v33_gating.spec.json:6`, Code `:3659-3685`).
* **Zwei Vorwaertspaesse je Blatt:** Zieher-Sicht und eine Kopie mit geflipptem
  `current_player` (`:3388, 3401-3405`, `MIRROR_OTHER_VAL = false` `:1958`). Der Knoten
  speichert `[wert_spieler0, wert_spieler1]` (`:3592-3593`); der Wert des Spielers, der gerade
  GEZOGEN hat, kommt am Kind also aus dem geflippten Pass, sobald danach der Gegner am Zug ist.
* Der Baum endet an der Rundengrenze; das Blatt ist der Zustand VOR dem Tiling
  (`PREREG_round_transition_search_sampling.md` par.17.1). Das Tiling legt der exakte Loeser mit
  Netz-Stichentscheid (`PREREG_v22_window.md:371-375`; par.16.12 der Rundenuebergangs-Prereg).
* Tiling-Zustaende stehen mit Value-Ziel im Korpus (Policy maskiert, `PREREG_v22_window.md:376`;
  `PREREG_heuristic_v2_long_rows.md:2013`), das Vor-Tiling-Blatt ist also keine
  Trainingsluecke.

**Messbild am Champion** (`PREREG_v32_window.md` par.11, Tabelle Z. 409-420) `[GEPRUEFT]`:
Value-Kopf gegen die exakte R4-Wahrheit Steigung 0,456, R2 0,408; Punkte-Kopf Steigung 1,250,
R2 0,327; lineare Trunk-Probe LOO-R2 0,940 (Marge) bzw. 0,910 (Siegwahrscheinlichkeit), Koepfe
realisiert -2,28 auf der Margenskala, Decke 0,983; R5-Daempfung 0,177; Platt auf `frozen_v3`
B = 0,5989. Grundmenge: n = 72 Zustaende am Ende von Runde 4 (R4/R4b), 139 Paare aus 24
Zustaenden (R5), Substrat `selfplay_v30-b02-policy_*` (Z. 429-431).

---

## 2. Frage A: Auslese-Luecke

### 2.1 Was die R4b-Zahl traegt und was nicht

**Die -2,28 ist ein Skalenfehler, kein Ordnungsfehler.** `PREREG_r4_value_calibration.md`
par.20 rechnet es vor: der Punkte-Kopf korreliert mit r = 0,556 mit der wahren Marge, streut aber
um den Faktor 2,1 zu weit (sd 40,17 gegen 18,80); R2 NACH linearer Anpassung 0,312, OHNE
Anpassung -2,18 `[GEPRUEFT]`. Der faire Vergleich zur Trunk-Probe (0,940) ist also 0,31 bis
0,41, nicht -2,28. Die Luecke bleibt gross, aber sie ist kleiner, als die Schlagzeile sagt.

**Die Probe und der Kopf loesen verschiedene Aufgaben** `[HERLEITUNG]`. Die Probe wird auf
dem EXAKTEN Erwartungswert (16 Neubefuellungen, Alpha-Beta) derselben 72 Zustaende angepasst,
der Kopf auf verrauschten Einzelausgaengen der ganzen Verteilung. Ein Kopf, der gegen
verrauschte Ziele kalibriert ist, schrumpft zur Mitte; das allein erzeugt Steigungen unter 1.
Dazu passt, dass derselbe Kopf gegen realisierte Ausgaenge eher UEBERzeichnet (Platt-B 0,60 auf
`frozen_v3`), gegen die exakte Wahrheit aber gedaempft ist (0,456): das ist die Signatur eines
Kopfes, dessen Fehler vor allem Rangrauschen ist, nicht eine falsche Skala allein
`[HERLEITUNG, verschiedene Substrate]`.

**Fehlende Kontrolle.** In der Probing-Literatur ist eine hohe Probe-Guete erst gegen eine
Kontrollaufgabe aussagekraeftig (Hewitt & Liang 2019, PAPER [Q13]). Bei p = 512 Merkmalen und
n = 72 mit dem Ridge-Optimum am Gitterrand (par.21, Vorbehalt 2) fehlt die Gegenprobe "Trunk
eines zufaellig initialisierten oder fruehen Netzes". Sie kostet Sekunden und gehoert vor jeden
Bau, der sich auf "der Trunk weiss es" stuetzt (Vorab-Test fuer Empfehlungen 2 und 3).

### 2.2 Was die Literatur fuer die Auslese anbietet

| Ansatz | Beleg | Neuer Kopf? | Bestand |
| --- | --- | --- | --- |
| Verlustgewichte automatisch (GradNorm, PCGrad, Unsicherheitsgewichtung) | PAPER [Q9-Q11]; Gegenbefund: ueber viele Aufgaben keine Verbesserung gegenueber einer abgestimmten gewichteten Summe (Xin et al. NeurIPS 2022, PAPER [Q12]) | nein | Gewichte von Hand gesweept: `PREREG_task_d_weights.md` H0 (vw 0,4 208:192, vw 0,8 92:108, pw 0,25 68:82) `[UEBERNOMMEN]` -> verworfen |
| Score und Sieg aus einer gemeinsamen Kopf-Einbettung (KataGo: `V_pooled`, getrennte FC je Ziel) | PAPER [Q1], App. A.5; Gewichte App. B: Wert 1,5, Score-pdf/cdf je 0,02 | nein (bei uns teilt der 512er-Trunk bereits) | kein Unterschied zu uns, der sich lohnt |
| Ordinal-/Schwellenmodell (Backgammon: Sieg, Gammon als geschachtelte Ereignisse; CORAL: gemeinsame Gewichte, nur Biases je Schwelle) | ENGINE [Q5, Q6], PAPER [Q7] | **nein**, siehe Empfehlung 2 | neu, Abschnitt 7 |
| Phasenabhaengige Ausgabeschicht (Stockfish 14: acht Ausgabe-Teilnetze nach `(piece_count - 1) div 4`; Rzepecki: Koeffizienten je Runde) | ENGINE [Q3], Thesis [Q4] | nein (Umbau der letzten Value-Schicht) | im Netz neu, in der Heuristik negativ (siehe 2.3) |
| Kopfkapazitaet / Kopftiefe | eigene Messung | nein | gefahren, verworfen (Abschnitt 8) |
| Gewichtsmittelung der Checkpoints (SWA/EMA) | ENGINE/PAPER [Q1] Abschnitt 2: EMA ueber vier Schnappschuesse, decay 0,75 | nein | neu (Grep SWA/EMA/Polyak/Gewichtsmittel: 0 Treffer) |
| Kopf allein auf eingefrorenem Trunk nachtrainieren | PAPER [Q14] (LP-FT) | nein | teilweise: Value-Kopf 64 -> 256 auf eingefrorenem Trunk 2026-07-15, Val-R2 0,273 gegen 0,272 (`archive/history.md:8109-8125`) `[GEPRUEFT]`; `PREREG_frozen_trunk_head.md` trainierte den OWNERSHIP-Kopf (Zeile 1) `[GEPRUEFT]` |

### 2.3 Abgleich der Phasen-Idee mit dem Bestand

Suchbegriffe `tapered|Phase|je Runde|gamePhase` in `evaluations/` und `archive/history.md`.
Treffer: der Tapered-Eval-Arm lief in der HEURISTIK (`V2HuellePhase`), Ergebnis "kein Effekt in
irgendeiner Richtung", t = 0,39, Siegquote 0,500 (`PREREG_heuristic_v2_long_rows.md:3245-3262`)
`[GEPRUEFT]`. Dort steht ausdruecklich, dass das Ergebnis nicht "Tapered Eval funktioniert nicht"
sagt, sondern "diese Form, auf diese Karte, mit diesen Werten". Im Netz gibt es keinen Arm: die
Runde geht als Skalar ein (`features.rs:1289`), eine rundenabhaengige Auslese muss das MLP selbst
bilden. Status: **(c) neu fuer das Netz**, (a) fuer die Heuristik.

### 2.4 Der zweite Vorwaertspass: Konsum statt Kopf

**Befund am Code** `[GEPRUEFT]`: je Blatt laufen zwei Paesse, der zweite auf einer Kopie mit
geflipptem `current_player` (`net_mcts.rs:3401-3405`). Der Code-Kommentar selbst sagt, dass
Trainingsdaten nur die Perspektive des tatsaechlichen Zugspielers kennen (`:1935-1941`). Der
Wert des gerade ziehenden Spielers wird am Kind aus diesem Pass gelesen (`:3592-3593`).

**Folge** `[HERLEITUNG]`: an der Wurzel beruht die Q-Schaetzung jedes Kindes, nach dem der Gegner
am Zug ist, auf "ich waere am Zug" statt auf der realen Stellung. Kinder, nach denen derselbe
Spieler weiterentscheidet (die zweistufigen Kuppel-Knoten Platz/Drehung), werden dagegen aus dem
echten Zieher-Pass bewertet. Ein Tempo-Versatz der Sicht wirkt dann NICHT gleich auf alle
Geschwister und hebt sich unter der Softmax nicht weg.

**Dass der Versatz existiert, ist im Bestand angedeutet:** die beiden gespeicherten
Bootstrap-Siegwahrscheinlichkeiten eines Zustands summieren sich zu rund 1,13-1,14 statt 1,
"rund +0,05 je Seite" (`PREREG_heuristic_v2_long_rows.md:1235-1240`, `docs/knobs.md:238`)
`[UEBERNOMMEN]`. Ob diese Paare aus demselben Doppelpass stammen, ist hier nicht nachgelesen
`[UNGEPRUEFT]`.

**Literatur:** AlphaGo Zero/AlphaZero bewerten einmal aus Sicht des Ziehenden und negieren im
Backup (PAPER [Q15]); das ist im Nullsummenspiel ohne Remis exakt, und unser Spiel hat kein Remis
(Gleichstand entscheidet eine Zusatzregel, `docs/engine_manual.md:203`) `[GEPRUEFT]`.

**Abgleich** (Suchbegriffe `MIRROR_OTHER_VAL|perspective_divergence|other_pass`): **(a)
gefahren, aber ohne Aufloesung.** 2026-07-20, `v9b_domeonly`, 150 Sims, n = 100 gegen die
Heuristik: 3:97, "eher schlechter als der 0.0-Baseline-Bereich", Floor-Shaping-Arm 11 Prozent
(`net_mcts.rs:1951-1957`) `[GEPRUEFT]` (Zahlen dort als Kommentar, Artefakt nicht gelesen). Ein
Netz, das in beiden Armen rund 90 Prozent verliert, kann bei n = 100 einen Effekt in der
Groessenordnung heutiger Generationsspruenge (54 gegen 50 Prozent) nicht aufloesen
`[HERLEITUNG]`. Der Retest wurde spaeter "bewusst nicht priorisiert (alter klarer
Negativ-Befund)" (`archive/history.md:1366-1368`) `[GEPRUEFT]`. Arm K
(`MOSAIC_BOOTSTRAP_COHERENCE=sum1`) normiert nur die gespeicherten Labels, nicht den Konsum in
der Suche; gebaut, Default aus (`docs/knobs.md:124, 238`) `[GEPRUEFT]`; ob je ein Arm damit
lief, ist hier nicht nachgesucht `[UNGEPRUEFT]`.

---

## 3. Frage B: Relationale Struktur Drafting x Tiling

### 3.1 Literatur

* **Relationale Encoder** (Self-Attention ueber Entitaeten): bessere Sample-Effizienz und
  Generalisierung in Box-World und StarCraft-II-Minispielen (Zambaldi et al., ICLR 2019, PAPER
  [Q16]); AlphaStar: Transformer mit 3 Schichten, 2 Koepfen, Breite 128 ueber bis zu 512
  Einheiten (ENGINE/PAPER, Zusammenfassung ueber [Q17]); OpenAI Five: Max-Pooling ueber
  Einheiten (ebenda). Alles bei GPU-Budgets um Groessenordnungen ueber unserem.
* **Brettspiele:** ResTNet (Residual plus Transformer verschraenkt) hebt Siegquoten von 54,6
  auf 60,8 Prozent (9x9 Go) und von 50,4 auf 58,0 Prozent (19x19 Hex) (IJCAI 2025, PAPER [Q18],
  Zahlen aus dem Abstract). Catan: ein "cross-dimensional" Netz fuer gemischte Brett- und
  Vektorinformation liess erstmals einen RL-Agenten den besten Heuristik-Agenten schlagen
  (Gendre & Kaneko 2020, PAPER [Q19]). 7 Wonders Duel (Kartenauslage, keine Brettgeometrie):
  MCTS plus Transformer-Encoder auf Expertenniveau, ohne Architekturvergleich (PAPER [Q20]).
  Splendor, Azul: nur Projekte ohne Ablation gefunden.
* **Gegenbefund, fuer uns der wichtigste:** in Schach brachte ein Wechsel auf Transformer-
  Bausteine rund +30 Elo, eine erweiterte EINGABE-Darstellung (Materialdifferenz, Figurenmasken,
  Schachgeber u.a.) rund +97 Elo, zusammen mit einem WDL-Wertkopf rund +180 Elo
  (Czech et al. 2023, "Representation Matters", PAPER [Q21], Tab. 4/5 laut HTML-Fassung).
* **Azul direkt:** Rzepecki 2025 (uebermenschlich auf Board Game Arena) nutzt Minimax mit
  NNUE-Bewertung und laut `RESEARCH_heuristic_methodology_external_2026-08-25.md` Abschnitt 6a
  phasenabhaengige Koeffizienten `[UEBERNOMMEN]`; das PDF war in dieser Sitzung nicht lesbar
  (kein Seiten-Renderer), die NNUE-Details sind daher nicht nachgeprueft.

**Einordnung** `[HERLEITUNG]`: die Literatur belegt relationale Encoder bei grossen, variablen
Entitaetsmengen. Unsere Auslage ist klein und fest (4 kleine Fabriken, 1 grosse, 6 Musterreihen
je Spieler, 9 Kuppelslots), und die belegte Alternative "abgeleitete Merkmale" ist in derselben
Rechenklasse staerker. Das deckt sich mit dem Hausmuster "netzseitige Sichten tragen"
(Variante C, 432:368, Block-z +2,40, Kopf von `PREREG_round_transition_search_sampling.md`)
`[UEBERNOMMEN]`.

### 3.2 Kosten eines Attention-Trunks

`[HERLEITUNG]` Zwei Attention-Schichten, Breite 64, 24 Tokens (5 Fabriken, 12 Musterreihen,
Kuppel- und Plattentokens) kosten je Schicht rund 0,39 Mio MAC (Projektionen) + 0,79 Mio (FFN) +
0,07 Mio (Attention), zusammen rund **2,5 Mio MAC, +60 Prozent** auf die 4,2 Mio des heutigen
Netzes. Bei einem Inferenzanteil von 62 Prozent der Self-Play-Zeit (v19_2d, 600 Sims,
`archive/history.md:7420-7430`) `[GEPRUEFT fuer damals]`, heute ungemessen `[UNGEPRUEFT]`, waeren
das rund +37 Prozent Erzeugungszeit, also rund 1.500 Partien je 4.000er-Klasse. Das ist ohne
Vorab-Beleg nicht zu vertreten.

### 3.3 Abgleich

Suchbegriffe `attention|transformer|deep ?sets|GNN|entity|cross-attention` in `evaluations/`:
nur die ungebaute faktorierte Policy-/Action-Attention aus dem Review 2026-08-08
(`EXTERNAL_REVIEW_2026-08-08.md:361`, "bleibt UNGEBAUT") `[GEPRUEFT]`. Der 2D-Encoder ist der
einzige gefahrene Trunk-Umbau: Arena-Gating 416:384 als Wash (`PREREG_2d_encoder.md` Zeile 1)
`[UEBERNOMMEN]`, heute Champion-Encoder. Farb-Permutation als Augmentierung wurde verworfen, weil
die Kuppelplatten feste Farbmuster tragen (`archive/history.md:5444-5450`) `[GEPRUEFT]`;
**Fabrik-Permutation** ist nirgends behandelt (Grep `augment|Permutation|Symmetri`) `[GEPRUEFT]`,
und das Regelwerk kennt keine Positionsregel zwischen den kleinen Fabriken
(`docs/engine_manual.md:35-36, 97-110`) `[GEPRUEFT]`.

---

## 4. Frage C: Rundenuebergang netzseitig

**Literatur:** Afterstate-Bewertung (TD-Gammon-Tradition, 2048: Szubert & Jaskowski 2014;
Stochastic MuZero, ICLR 2022, PAPER [Q22]) trennt den Wert der eigenen Entscheidung vom Zufall
der Neubefuellung. Netzseitig ohne Suchumbau bleiben davon zwei Hebel: das Ziel ueber den Zufall
mitteln und dem Netz den Zustand vor dem Zufall zeigen.

**Beides ist im Bestand weitgehend belegt oder gefahren:**

* Mittelung ueber Neubefuellungen als Ziel (`rtv`): gebaut, wegen der Kosten gestrichen: 149,7 von
  184,6 CPU-s je Partie, also rund 81 Prozent (v12-Aera, `archive/history.md:2344-2347`)
  `[GEPRUEFT]`.
* Bootstrap-Horizont 3 statt 2: trifft den Ausgang schlechter (`PREREG_bootstrap_horizon.md`
  Zeile 1) `[UEBERNOMMEN]`.
* Der Vor-Tiling-Zustand (das Afterstate-Aequivalent des Drafting-Blatts) steht als
  Tiling-Record mit Value-Ziel im Korpus (Abschnitt 1) `[GEPRUEFT]`, und die Tiling-Projektion
  ist seit v30 Eingabe (Variante C) `[GEPRUEFT]`.
* Zufallsknoten in der Suche, Blatt nach dem Uebergang (Variante B), Top-K-Tiling: negativ oder
  schaedlich (Kopf der Rundenuebergangs-Prereg, par.16.9, 17.9) `[UEBERNOMMEN]`.

**Was offen bleibt** `[HERLEITUNG]`: der Nutzer-Eindruck "Taktik nicht an die neu ausgelegten
Fliesen angepasst" betrifft den ERSTEN Drafting-Zug der neuen Runde, nicht den Uebergang selbst.
Dort muss das Netz die neue Auslage gegen die eigenen Reihen und Kuppelzellen halten, und genau
diese Beziehung steht nicht im Eingang (Abschnitt 1). Das ist Frage B in anderem Gewand;
Empfehlung 4 bedient beide. Ehrlich: fuer den Uebergang selbst gibt die Literatur netzseitig
nichts her, was nicht schon gefahren ist.

---

## 5. Frage D: Punkte gegen Sieg

**Was starke Agenten tun:**

* **KataGo:** Siegwert traegt die Suche; Score geht nur als kleiner, saettigender Zusatz ein
  (Score-pdf/cdf-Verlustgewichte je 0,02 gegen 1,5 fuer den Wert, [Q1] App. B). Die
  Hilfsziele Ownership und Score beschleunigen das LERNEN (ohne sie 1,65-fach langsamer,
  [Q1] Abschnitt 5.2) `[GEPRUEFT an der HTML-Fassung]`.
* **Backgammon (TD-Gammon, GNU Backgammon):** das Netz sagt geschachtelte
  Ausgangswahrscheinlichkeiten voraus (Sieg, Sieg mit Gammon, ...); gespielt wird auf die
  Equity, weil Gammons im Geldspiel tatsaechlich zaehlen ([Q5] 4 Ausgaenge; [Q6] 5 Ausgaenge,
  Suchtreffer-Zusammenfassung). Punkte sind dort die Auszahlung, nicht ein Stellvertreter.
* **Scrabble (Maven):** Zugwahl ueber "Equity" = Punkte des Zuges plus Wert des Restbanks, dazu
  Simulation; Endspiel mit B* (PAPER [Q23]). Ob Maven vor dem Endspiel auf Gewinnprozent
  umschaltet, ist hier nicht nachgelesen `[UNGEPRUEFT]`.
* **Poker:** EV ist die Auszahlung.

**Schluss** `[HERLEITUNG]`: wo Punkte die Auszahlung sind, ist das Punkte-Ziel richtig; in
Azul Duel zaehlt nur der Sieg, also ist `P(Sieg)` das richtige OBJEKT der Suche, und Punkte sind
ein dichteres LERNsignal. Die Nutzer-These "der Punkte-Kopf waere der eigentliche Treiber" trifft
nach dieser Lesart die Lernseite, nicht die Suchseite.

**Was davon bei uns schon gefahren ist (Suchbegriffe `PREREG_points_*`, `saturating`,
`risk_sensitive`, `lambda`, `t37`, `t12`):**

| Form | Ergebnis | Pruefstelle |
| --- | --- | --- |
| linearer Punkte-Blend im Blatt, 0,5 / 1,0 | 1:14 / 0:12 | `research_value_head_alternatives_DRAFT.md:8` `[UEBERNOMMEN]` |
| Punkte-Blend w = 0,1 | 300 gegen 321 von 400, Block-t -2,68 | `PREREG_points_blend_w.md` Zeile 1 `[UEBERNOMMEN]` |
| KataGo-treue, saettigende, re-zentrierte Margen-Utility (K1) | Erstlauf 104:56, Replikation 83:77, gegen Champion 77:83; weniger Spalten | `PREREG_saturating_score_utility.md` Zeile 1, par.15-17 `[UEBERNOMMEN]` |
| risikosensitive Blatt-Utility | gegenstandslos (zwei Logits, kein Remis) | `PREREG_risk_sensitive_leaf_utility.md` Zeile 1 |
| Punkte-Kanal unter dem Kipppunkt, Aggressions-Blends | H0 | `PREREG_points_lambda_below_tipping_point.md`, `PREREG_aggression_remapping.md` |
| Tiling-Kriterium Punkte x P(Sieg) gegen P(Sieg) | H0 | `PREREG_t37_tiling_criterion.md` |
| Verteilungs-Punkte-Kopf (C51/HL-Gauss) auf EIGENE Punkte | Replikation = Seed-Rauschen | `PREREG_post34_package.md`, Korrektur in `research_value_head_alternatives_DRAFT.md:7` (lief eigenseitig, nicht auf der Differenz) `[GEPRUEFT]` |
| Punkte-Gewicht 0,25 | H0 | `PREREG_task_d_weights.md` |
| Value-Ziel als Margen-tanh (Aera v13-v19), dann WDL | WDL-Kandidat gewann 208:162, mehrfaktoriell (Korpus-Aera wechselte mit) | `PREREG_v20_campaign.md` Zeile 1 `[UEBERNOMMEN]`, `neural_net.py:1173-1240` |

**Nicht gefahren** ist die Form, die das Objekt beibehaelt und die Marge nur an den Siegwert
KOPPELT: ein Schwellenmodell, in dem der vorhandene WDL-Logit auch die Ereignisse
"Marge > t" erklaeren muss (Empfehlung 2). Grep `kumulativ|ordinal|CORAL|Schwellen|gammon`
in `evaluations/`, `docs/`, `archive/`: nur Wortzufaelle (McNemar-Kumulation,
Ownership-Verbraucher "ordinal statt Betrag") `[GEPRUEFT]`. Die thematisch naechste Prereg,
`PREREG_score_correlation.md`, fragte, ob sich `P(Sieg)` aus zwei unabhaengigen
Punkte-Randverteilungen falten laesst (Fehler 0,039 in Runde 4, "Kennzahl, kein Bau-Argument")
`[GEPRUEFT]`, also eine Faltung ausserhalb des Netzes, nicht eine Kopplung im Verlust.

---

## 6. Was die Literatur fuer unseren Fall NICHT hergibt

* Keinen Beleg fuer Attention- oder Set-Encoder in Auslage-Spielen bei CPU-Budgets um 4 Mio MAC.
* Keinen Beleg, dass automatische Verlustgewichtung eine gesweepte Summe schlaegt [Q12].
* Keine Studie, die eine Auslese-Luecke "lineare Probe gegen Kopf" in AlphaZero-Systemen misst
  und schliesst. Die R4b-Beobachtung ist ein Hausbefund, fuer den die Literatur nur die
  Methodenwarnung (Kontrollaufgabe [Q13]) liefert.
* Fuer den Rundenuebergang netzseitig nichts Neues gegenueber dem Bestand.

---

## 7. Empfehlungen (hoechstens fuenf, nach erwartetem Nutzen je Kosten)

Allen fuenf gemeinsam: **erst nach der v33-Kette**, einfaktoriell gegen den Referenzarm auf
demselben Fenster und Monolithen, Tor 1 mit zwei Seeds und Blockgroesse 5. Zwei davon (2, 3)
teilen EIN Offline-Werkzeug: Trunk-Einbettung des Champions auf dem Val-Fenster extrahieren
(Muster `tools/r4b_zone_probe.py`), dann Logit-Auslesen anpassen und auf ausgehaltenen Dateien
per Brier vergleichen. Kosten des Werkzeugs: ANNAHME unter 1 h Bau, Laufzeit Minuten (R4b
brauchte fuer 72 Zustaende samt Ridge 42,5 s, `PREREG_v32_window.md:433`) `[GEPRUEFT fuer R4b]`.

### E1. Einpass-Konsum: Wert des Nicht-Ziehers als `1 - P(Sieg)` des Ziehers

* **Mechanismus:** statt eines zweiten Vorwaertspasses auf einer Stellung, die es im Training
  nicht gibt, bekommt der andere Spieler `1 - p`. Das ist exakt nullsummen-konsistent und
  entfernt einen moeglichen Tempo-Versatz zwischen Geschwistern (Abschnitt 2.4).
* **Beleg:** PAPER [Q15] (AlphaZero-Standard); Hausbefund Paarsumme 1,13-1,14 `[UEBERNOMMEN]`.
* **Abgleich:** (a) gefahren 2026-07-20, 3:97, aber ohne Aufloesung (Abschnitt 2.4). Das Argument,
  warum der Test die Idee nicht traf: Effektgroesse heutiger Spruenge gegen ein Netz, das in
  beiden Armen rund 90 Prozent verlor, bei n = 100 `[HERLEITUNG]`.
* **Kosten:** Laufzeit-Knopf statt Kompilierzeit-Konstante (Spec-Feld), Wheel, Paritaet,
  Anker-Drift (Pflicht nach CLAUDE.md; 22 s) rund 5 min Maschine; Kostentor 16 min; Tor 1 2,7 h.
  **Rund 3 h = 3.000 Partien, kein Training.** Moeglicher Gegenwert: die Erzeugung spart je
  Blatt einen Merkmalsbau und die Haelfte des Batch-2-Aufrufs. Wie viel das ist, haengt am
  Verhaeltnis Batch 2 zu Batch 1 auf tract und am heutigen Inferenzanteil, beides ungemessen
  `[UNGEPRUEFT]`; bei kleinen Netzen auf CPU kann Batch 2 fast so billig sein wie Batch 1, die
  Ersparnis liegt also irgendwo zwischen wenigen Prozent und rund 40 Prozent `[HERLEITUNG]`.
  Das Kostentor beantwortet es.
* **Risiko:** der geflippte Pass traegt womoeglich nuetzliche Zusatzinformation (zweite
  Schaetzung, Ensemble-Effekt); dann verliert E1. Geaendertes Such-Verhalten aendert auch die
  Labels der naechsten Erzeugung (`root_q`, Bootstrap).
* **Billigster Vorab-Test (Minuten, kein Self-Play):** auf den Val-Zustaenden je Zustand
  `p_zieher` und `p_flip` rechnen. Kennzahlen: mittlerer Tempo-Versatz
  `p_flip + p_zieher - 1` je Runde, Brier von `p_zieher` gegen `1 - p_flip` gegen den Ausgang,
  Anteil der Wurzeln mit gemischtem Folgezieher unter den Top-16-Kindern. Ist der Versatz rund
  null und `1 - p_flip` gleich gut, bleibt nur das Kostenmotiv (dann entscheidet das Kostentor
  allein).
* **Keine neuen Koepfe:** eingehalten (reiner Konsum).

### E2. Margen-Schwellen am vorhandenen WDL-Logit (Schwellen- bzw. CORAL-Verlust)

* **Mechanismus:** der Value-Kopf behaelt seinen Ausgang `P(Sieg) = sigma(z)`. Im VERLUST
  kommen Terme `BCE(sigma(z - t_k / s_r), 1[Marge > t_k])` fuer wenige Schwellen
  (z.B. t = -10, -5, +5, +10 Punkte) hinzu, mit einer Skala `s_r` je Runde (fuenf trainierbare
  Skalare, nur im Training). Damit muss der Siegwert-Logit selbst eine monotone Margen-
  Lage sein: die Punkteinformation formt den Siegwert, ohne das Objekt der Suche zu wechseln.
* **Beleg:** CORAL (gemeinsame Gewichte, Schwellen unterscheiden sich nur im Bias, PAPER [Q7]);
  geschachtelte Ausgaenge in Backgammon (ENGINE [Q5, Q6]); das Proportional-Odds-Modell ist
  die statistische Grundform `[HERLEITUNG]`.
* **Abgleich:** Suchbegriffe siehe Abschnitt 5; naechste Preregs gelesen:
  `PREREG_score_correlation.md` (Faltung ausserhalb des Netzes), `PREREG_saturating_score_utility.md`
  par.6/6b (Marge in der SUCHE aus den Punkte-Koepfen), `PREREG_points_dist_bin_scale.md`
  (Verteilung auf eigene Punkte). **(c) neu.** Abgrenzung zur Margen-Aera v13-v19: dort war die
  Marge das Objekt der Suche (`(v + 1) / 2` eines Margen-tanh), hier bleibt es `P(Sieg)`.
* **Kosten:** Verlust plus Manifest-Feld, rund ein halber Tag Bau; das Margen-Ziel braucht den
  ungeklemmten Endstand je Record (`scores_unclamped` im Korpus zu 100 Prozent vorhanden,
  `PREREG_score_correlation.md` par.7) `[GEPRUEFT]`, im Cache ggf. als neues Feld, dann Blockbau
  rund 36 min (`measured_runtimes.md`, 2.144 s fuer 2.800 Dateien unter 884) `[GEPRUEFT]`.
  Training 63-72 min, Tor 1 2,7 h. **Rund 4,5 h = 4.500 Partien.** Inferenz je Zug: null (der
  exportierte Graph aendert sich nicht).
* **Risiko:** falsch spezifizierte Streuung (die Marge streut je Stellung, nicht nur je Runde)
  kann den Siegwert verbiegen; deshalb Schwellen nah an null und ein kleines Gewicht. Der
  gemischte WDL-Zielwert (Lambda 0,7 mit Wurzel-Q) bleibt an der Schwelle 0 unveraendert; die
  anderen Schwellen lernen aus dem harten Endstand.
* **Billigster Vorab-Test (Offline-Werkzeug oben):** auf der eingefrorenen Trunk-Einbettung
  (a) logistischen Siegwert-Leser und (b) Schwellen-Leser mit gemeinsamem Logit anpassen,
  Brier auf ausgehaltenen Dateien je Runde vergleichen, dazu die Steigung gegen die 72 exakten
  R4-Zustaende. Kein Brier-Gewinn von (b) ueber (a) jenseits der Seed-Streuung: Idee tot, bevor
  ein Training faellt. Dazu die Kontroll-Probe aus 2.1.
* **Keine neuen Koepfe:** eingehalten; kein zusaetzlicher Ausgang, nur Verlustterme und fuenf
  Trainings-Skalare.

### E3. Rundenabhaengige letzte Value-Schicht (Layer-Stacks)

* **Mechanismus:** die letzte Schicht des Value-Kopfs (64 -> 2) wird je Runde eigen gewichtet
  (5 Saetze), gewaehlt ueber die Runde; alle fuenf werden gerechnet, einer gewaehlt. Das Netz
  muss die Phasenabhaengigkeit der Auslese dann nicht aus einem Skalar `round / 6` erzeugen.
* **Beleg:** Stockfish 14, acht Ausgabe-Teilnetze nach `(piece_count - 1) div 4` (ENGINE [Q3]);
  Rzepecki, Koeffizienten je Spielphase (Thesis [Q4], `[UEBERNOMMEN]` ueber die Vorrecherche).
* **Abgleich:** Abschnitt 2.3; (c) neu im Netz, in der Heuristik (a) negativ, aber mit dort
  selbst benannter enger Reichweite.
* **Kosten:** Kopf-Umbau plus ONNX-Nachweis auf tract (One-hot der Runde entweder im Graph aus
  dem Skalar oder als 5 zusaetzliche Eingaben, additiv nach Hausmuster), rund ein halber Tag;
  Training und Tor 1 wie E2: **rund 4,5 h = 4.500 Partien.** Inferenz: rund 0,6 Tsd. MAC mehr,
  vernachlaessigbar `[HERLEITUNG]`.
* **Risiko:** weniger Daten je Satz (Runde 5 ist ohnehin exakt gerechnet); Warmstart der fuenf
  Saetze aus dem vorhandenen, sonst verschiebt sich die Linie.
* **Billigster Vorab-Test:** im selben Offline-Werkzeug je Runde getrennte gegen globale
  lineare Auslese auf dem eingefrorenen Trunk; kein Brier-Gewinn in den Runden 1-4: tot.
  Kombinierbar mit E2 (die Skalen `s_r` sind der gleiche Gedanke), aber als eigener Faktor zu
  messen.
* **Keine neuen Koepfe:** eingehalten (Umbau der letzten Schicht, gleicher Ausgang).

### E4. Angebots-Bedarfs-Sicht als Encoder-Abschnitt

* **Mechanismus:** abgeleitete Beziehungsmerkmale je Spieler und Musterreihe, z.B. "groesste
  Menge der passenden Farbe aus EINER Sonnenseite", "aus dem Mondzug", "eine einzelne Nahme
  vollendet die Reihe ohne Ueberlauf", "Ueberlauf in Fliesen". Grob 4 x 6 x 2 = 48 Werte
  `[HERLEITUNG, Zuschnitt offen]`. Das ist die Relation Auslage x Reihe x Kuppel, die heute das
  MLP aus Zaehlungen bilden muss, und sie ist genau die Frage des ersten Zugs einer neuen Runde
  (Nutzer-Punkt 2).
* **Beleg:** Schach, Merkmale +97 Elo gegen Transformer +30 Elo ([Q21]); hausintern der Erfolg
  von Variante C mit einer ebenfalls ableitbaren Groesse `[UEBERNOMMEN]`; Catan [Q19] als
  Hinweis, dass gemischte Brett-/Vektor-Relationen explizit gemacht werden wollen.
* **Abgleich:** Grep `Angebot|takeable|verfueg|supply|vollendbar|in einem Zug` in `features.rs`
  und `PREREG_stack_top_feature.md` (die thematisch naechste Prereg, dort geht es um SICHT, nicht
  um Relationen): nichts `[GEPRUEFT]`. **(c) neu.**
* **Kosten:** Bau in Rust in beiden Pfaden plus Paritaetstests plus Python ueber das Wheel, 1-2
  Tage; Kostentor 16 min; Blockbau rund 36 min; Training 72 min; Tor 1 2,7 h: **rund 4,5 h =
  4.500 Partien.** Laufend: Variante C kostete +4 bis +8 Prozent je Partie (12,4 / 12,0 s gegen
  11,5 s, `measured_runtimes.md`) `[GEPRUEFT]`; diese Merkmale brauchen keinen Loeser, erwartet
  deutlich darunter `[HERLEITUNG]`, also unter rund 100 Partien je 4.000er-Klasse.
* **Risiko:** das Netz weiss es schon; dann ist der Abschnitt tote Last.
* **Billigster Vorab-Test:** lineare Probe der vorgeschlagenen Groessen auf der Trunk-Einbettung
  des Champions (dasselbe Werkzeug). Liegt die Probe-Guete fuer "vollendet in einer Nahme" schon
  nahe 1, entfaellt der Bau; liegt sie deutlich darunter, ist die Luecke belegt.
* **Keine neuen Koepfe:** eingehalten (Encoder).

### E5. Gewichtsmittelung (EMA/SWA) der Trainings-Checkpoints

* **Mechanismus:** statt des Brier-besten Einzel-Checkpoints ein exponentiell gemitteltes Netz
  ueber die letzten Schnappschuesse; glaettet Kopf-Rauschen, das gerade beim Value-Kopf (Rangrauschen,
  2.1) teuer ist.
* **Beleg:** KataGo, EMA ueber vier Schnappschuesse mit decay 0,75 fuer jeden Kandidaten ([Q1]
  Abschnitt 2) `[GEPRUEFT]`; SWA (Izmailov et al. 2018, PAPER [Q24]).
* **Abgleich:** Grep `SWA|EMA|Polyak|Gewichtsmittel` in `evaluations/`, `docs/`, `archive/`:
  0 Treffer `[GEPRUEFT]`; die naechste Prereg `PREREG_lr_schedule.md` betrifft den Plan der
  Lernrate, nicht die Mittelung. **(c) neu.** Es liegen je Lauf nur `_resume` und Bestmodell
  vor (`train.py:1009-1020`, `models/`), also ist kein Offline-Vorab-Test auf Altlaeufen moeglich.
* **Kosten:** rund 1-2 h Bau (torch `swa_utils` oder eigene EMA, BN-Statistik neu schaetzen),
  Training 63-72 min, Tor 1 2,7 h: **rund 3,8 h = 3.800 Partien.** Inferenz null.
* **Risiko:** gering; der Gewinn ist in der Literatur klein und stetig, nicht sprunghaft.
* **Billigster Vorab-Test:** Brier des gemittelten gegen den Brier-besten Checkpoint desselben
  Laufs auf dem Val-Fenster (faellt im Training ohnehin an). Kein Gewinn: kein Tor 1.
* **Keine neuen Koepfe:** eingehalten.

**Reihenfolge-Vorschlag:** das Offline-Werkzeug einmal bauen und E1-, E2-, E3- und E4-Vorab-
Tests in einer Sitzung fahren (zusammen deutlich unter 1 h Maschine `[HERLEITUNG]`); nur was dort
ueberlebt, bekommt einen Arm. So kostet eine tote Idee Minuten statt 4.500 Partien.

---

## 8. Bewusst verworfen, weil schon getestet (mit Pruefstellen)

| Idee | warum verworfen | Pruefstelle |
| --- | --- | --- |
| Value-Kopf breiter / tiefer | 64 -> 256 auf eingefrorenem Trunk, Val-R2 unveraendert | `archive/history.md:8109-8125` `[GEPRUEFT]` |
| Trunk nur fuer den Wert (ohne Policy-Signal) | schlechter (0,19 gegen 0,27-0,34) | `archive/history.md:8127-8144` `[GEPRUEFT]` |
| Groesserer Trunk / Kapazitaets-Frontier | geparkt, R4b zeigt keinen Trunk-Engpass am Endspiel | `PREREG_capacity_sim_frontier.md` Zeile 1; `PREREG_r4_value_calibration.md` par.21 `[GEPRUEFT]` |
| Verlustgewichte (und damit GradNorm/PCGrad/Unsicherheitsgewichtung) | Handsweep H0; Literatur: automatische Verfahren schlagen die Summe nicht [Q12] | `PREREG_task_d_weights.md` Zeile 1 `[UEBERNOMMEN]` |
| Punkte in die Suche (linear, saettigend, risikosensitiv, Lambda) | alle H0 oder schaedlich | Abschnitt 5, Tabelle |
| Verteilungskopf auf eigene Punkte | Replikation Seed-Rauschen | `PREREG_post34_package.md` Zeile 1 |
| Ranking-Verlust | Orakel-Vorpruefung negativ | `PREREG_t35b_ranking.md` Zeile 1 |
| Tieferes Nachlabeln / Reanalyze | Arena 75:85 | `PREREG_reanalyze_label_depth.md` Zeile 1 `[UEBERNOMMEN]` |
| Mehr Suche statt besserer Bewerter | saettigt bei 400 (@600 74:76) | `PREREG_search_depth_column_optimum.md` Zeile 1 `[UEBERNOMMEN]` |
| Rundenschaetzer als Blattterm (K4) | schadet, 20:60 und 45:85 | `PREREG_round_estimate_leaf_term.md` Zeile 1 `[UEBERNOMMEN]` |
| Tiling im Blatt (Variante B), Top-K-Tiling mit Ueberstimmung | negativ bzw. schaedlich | Rundenuebergangs-Prereg Zeile 1, par.16.9 |
| Zufallsknoten ISMCTS / Mehrfachdeterminisierung | k = 4 faellt ab | `PREREG_ismcts_determinizations.md` Zeile 1 |
| Farb-Permutation als Augmentierung | erzeugt Kuppelplatten, die es nicht gibt | `archive/history.md:5444-5450` `[GEPRUEFT]` |
| Eigener Margen-Kopf | Nutzer: Marge liegt in Punkte- und Gegnerpunkte-Kopf | `PREREG_saturating_score_utility.md` par.6b `[GEPRUEFT]` |
| Afterstate-Ziel ueber Neubefuellungen (`rtv`) | rund 81 Prozent der CPU-Zeit je Partie (149,7 von 184,6 CPU-s, v12-Aera) | `archive/history.md:2342-2347` `[GEPRUEFT fuer die Kosten]` |
| GPU-Inferenz / Async-Batcher | Faktor 1,255 statt 2 | `docs/external_relaunch_plan_2026-09-16.md:46` `[UEBERNOMMEN]` |

**Nachrangig, nicht in der Liste:** (i) Attention- oder Set-Trunk: rund +60 Prozent MAC
(3.2) ohne Beleg in unserer Klasse; erst wenn E4 zeigt, dass die Relation fehlt UND Merkmale sie
nicht schliessen. (ii) Fabrik-Permutation als Augmentierung (4! Anordnungen der kleinen Fabriken,
Aktions-IDs mitpermutiert): regelkonform `[HERLEITUNG aus engine_manual.md:35-36, 97-110]`, neu,
aber die Policy saettigt laut Koordinator-Brief bereits (`[UEBERNOMMEN]`, Primaerquelle nicht
gelesen; `PREREG_task36_value_saturation.md` Zeile 1 belegt nur die Value-Seite) und die
permutierten Zustaende tragen denselben Ausgang, also wenig neue Wertinformation `[HERLEITUNG]`.

---

## 9. Quellen

* [Q1] Wu, "Accelerating Self-Play Learning in Go" (KataGo), PAPER, https://arxiv.org/html/1902.10565v5 (App. A.5 `V_pooled`, App. B Verlustgewichte, Abschnitt 2 SWA/EMA, Abschnitt 5.2 Ablation Hilfsziele).
* [Q2] KataGo Methods, ENGINE, https://github.com/lightvector/KataGo/blob/master/docs/KataGoMethods.md
* [Q3] Stockfish NNUE (HalfKAv2, Stockfish 14: acht Ausgabe-Teilnetze nach `(piece_count - 1) div 4`), ENGINE, https://www.chessprogramming.org/Stockfish_NNUE
* [Q4] Rzepecki, "Implementing superhuman AI for Azul board game with a variation of NNUE", Masterarbeit Wroclaw 2025, https://jakubkowalski.tech/Supervising/Rzepecki2025ImplementingSuperhuman.pdf (Details hier ueber die Vorrecherche, nicht selbst gelesen).
* [Q5] TD-Gammon, vier Ausgaenge, https://en.wikipedia.org/wiki/TD-Gammon (Sekundaerquelle).
* [Q6] GNU Backgammon, fuenf Ausgaenge (Suchtreffer-Zusammenfassung, u.a. https://arxiv.org/abs/2608.15146 und https://gnubg.readthedocs.io/en/latest/), nicht im Volltext gelesen.
* [Q7] Cao, Mirjalili, Raschka, "Rank consistent ordinal regression for neural networks" (CORAL), PAPER, https://arxiv.org/abs/1901.07884
* [Q9] Chen et al., GradNorm, ICML 2018, PAPER, https://arxiv.org/abs/1711.02257
* [Q10] Yu et al., Gradient Surgery (PCGrad), NeurIPS 2020, PAPER, https://arxiv.org/abs/2001.06782
* [Q11] Kendall, Gal, Cipolla, Unsicherheitsgewichtung, CVPR 2018, PAPER, https://arxiv.org/abs/1705.07115
* [Q12] Xin et al., "Do Current Multi-Task Optimization Methods in Deep Learning Even Help?", NeurIPS 2022, PAPER, https://proceedings.neurips.cc/paper_files/paper/2022/hash/580c4ec4738ff61d5862a122cdf139b6-Abstract-Conference.html
* [Q13] Hewitt & Liang, "Designing and Interpreting Probes with Control Tasks", EMNLP 2019, PAPER, https://aclanthology.org/D19-1275/
* [Q14] Kumar et al., "Fine-Tuning can Distort Pretrained Features", ICLR 2022, PAPER, https://arxiv.org/abs/2202.10054
* [Q15] Silver et al., "Mastering the game of Go without human knowledge" (AlphaGo Zero), Nature 2017, PAPER, https://www.nature.com/articles/nature24270
* [Q16] Zambaldi et al., "Deep reinforcement learning with relational inductive biases", ICLR 2019, PAPER, https://openreview.net/pdf/b1ca2a9380e6534782a5ba79e91f2971a1b8ab8a.pdf
* [Q17] AlphaStar-Architektur (Zusammenfassung), https://arxiv.org/pdf/2104.06890 und https://www.alexirpan.com/2019/02/22/alphastar-part2.html, BLOG/Sekundaer.
* [Q18] Ju et al., "Bridging Local and Global Knowledge via Transformer in Board Games" (ResTNet), IJCAI 2025, PAPER, https://arxiv.org/abs/2410.05347
* [Q19] Gendre & Kaneko, "Playing Catan with Cross-dimensional Neural Network", ICONIP 2020, PAPER, https://arxiv.org/abs/2008.07079
* [Q20] "Learning to Play 7 Wonders Duel Without Human Supervision" (ZeusAI), PAPER, https://arxiv.org/abs/2406.00741
* [Q21] Czech et al., "Representation Matters for Mastering Chess: Improved Feature Representation in AlphaZero Outperforms Switching to Transformers", PAPER, https://arxiv.org/html/2304.14918
* [Q22] Antonoglou et al., Stochastic MuZero, ICLR 2022, PAPER, https://openreview.net/forum?id=X6D9bAHhBQ1 (bereits in der Vorrecherche).
* [Q23] Sheppard, "World-championship-caliber Scrabble", Artificial Intelligence 134 (2002), PAPER, https://www.sciencedirect.com/science/article/pii/S0004370201001667
* [Q24] Izmailov et al., "Averaging Weights Leads to Wider Optima and Better Generalization" (SWA), UAI 2018, PAPER, https://arxiv.org/abs/1803.05407

## 10. Zahlen aus Preregs/Kommentaren ohne Pruefung an der Primaerquelle

Alle als `[UEBERNOMMEN]` markierten Stellen, gesammelt: Arena-Ergebnisse aus den Zeile-1-Koepfen
(Variante C 432:368 / Block-z +2,40; `search_depth` 74:76; `task_d_weights` 208:192, 92:108,
68:82; `points_blend_w` 300 gegen 321; K1 104:56, 83:77, 77:83; `reanalyze` 75:85; K4 20:60,
45:85; `v20_campaign` 208:162; `2d_encoder` 416:384); die Punkte-Blend-Zahlen 1:14 / 0:12 aus
`research_value_head_alternatives_DRAFT.md`; die Bootstrap-Paarsumme 1,13-1,14 bzw. +0,05 je
Seite (Prereg-Absatz, Artefakt nicht gelesen); der Mirror-Test 3:97 (Code-Kommentar
`net_mcts.rs:1951-1957`, Artefakt nicht gelesen); der Inferenzanteil 81 Prozent der v20-Aera
(`PREREG_gpu_inference_batcher.md:23`, dort zitiert aus `PREREG_v20_campaign.md:71`); GPU-Faktor
1,255; das Trainingszeit-Mass 63 min fuer v32-b01; die Rzepecki-Details.

---

## 11. Fazit (10 Zeilen)

1. Die Literatur liefert fuer unseren Fall keine Blaupause; sie liefert vier uebertragbare Muster.
2. Das billigste ist ein Konsum-Befund: der Wert des Ziehenden kommt am Kind aus einem Pass, den es im Training nicht gibt.
3. Der Gegentest von 2026-07-20 (3:97) hatte keine Aufloesung; eine Minuten-Sonde entscheidet, ob E1 Staerke oder nur Rechenzeit bringt.
4. Die R4b-Luecke ist real, aber kleiner als -2,28 vs 0,940 suggeriert (fair: 0,31-0,41 gegen 0,94) und braucht eine Kontroll-Probe.
5. Punkte gehoeren als Lernsignal an den Siegwert, nicht als Objekt in die Suche; alle Suchformen sind bei uns gescheitert.
6. Ein Schwellen-/CORAL-Verlust am vorhandenen WDL-Logit koppelt beides ohne neuen Kopf und ist ungetestet (E2).
7. Rundenabhaengige Auslese ist Engine-Standard (Stockfish, Rzepecki) und im Netz ungetestet (E3).
8. Relationale Trunks sind in unserer Rechenklasse unbelegt und kosten rund +60 Prozent MAC; abgeleitete Merkmale sind der belegte Weg (E4).
9. Fuer den Rundenuebergang selbst gibt es netzseitig nichts, was nicht schon gefahren ist.
10. E2, E3 und E4 lassen sich mit einem Offline-Werkzeug auf dem eingefrorenen Champion in Minuten toeten, bevor eine Self-Play-Stunde faellt.
