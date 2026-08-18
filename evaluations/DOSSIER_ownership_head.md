# Dossier: der Ownership-Kopf — Stand, Messungen, offene Fragen

**Zweck.** Eigenständige Vorlage für eine externe Durchsicht: Wir versuchen seit
mehreren Generationen, ein AlphaZero-artiges Netz dazu zu bringen, die
Wertungsplatten eines Brettspiels anzuspielen, und es tut es nicht. Vier Wege
sind durchgemessen und geschlossen. Dieses Dokument enthält alles Nötige; die
Belegstellen sind angegeben, damit nichts nachgeschlagen werden *muss*.

Stand **2026-08-18**. Sprachregel des Projekts: dieses Dokument deutsch,
`README.md` englisch.

**Lesekonvention.** Jede Zahl ist entweder mit Prüfstelle belegt (`datei:zeile`,
Vorregistrierung, Messdatei) oder ausdrücklich als **Herleitung** markiert. Diese
Trennung ist Projektregel, eingeführt nachdem ungeprüfte Zahlen mehrfach in
Rechnungen eingegangen waren.

---

## 1. Das Spiel und das Ziel

Zwei Spieler, fünf Runden. Fliesen werden aus Fabriken gedraftet, in Musterreihen
gesammelt und von dort auf eine **Kuppel** gelegt: 3×3 Kuppelplatten mit je 4
Feldern, was ein **6×6-Raster** ergibt (`scoring.rs:787`, `build_grid`). Punkte
kommen aus zwei Quellen, die leicht verwechselt werden:

1. **Platzierungspunkte**, sofort: eine Fliese ohne orthogonalen Nachbarn bringt
   1 Punkt, sonst die volle Länge der zusammenhängenden Linie — horizontal und
   vertikal getrennt bezahlt (`docs/engine_manual.md:143-148`).
2. **Wertungsplatten**, am Spielende: drei von acht Kriterien liegen je Partie
   aus (seedabhängig) und werten Geometrien auf dem Endbrett.

**Das Ziel des Projekts** (Nutzer-Formulierung): ein **stärkerer Spieler**,
gemessen am **direkten Duell** gegen den Champion. Der Hebel ist der
**Plattenblick** — die Grundmechanik spielt das Netz kompetent und läßt je Partie
10+ Punkte an Wertungsplatten liegen. **Ein Plattenzuwachs, der Siege kostet,
gilt nicht als Erfolg.**

Champion ist `v21_2d_brierbest`, Elo 1358 (Anker: Heuristik@150 = 1000).

---

## 2. Die acht Kriterien — und warum die Kettenlänge alles entscheidet

| ID | Name | Wertung | Felder je Treffer | Struktur |
|---|---|---|---|---|
| k0 | Horizontale Reihen | 3 Pkt je volle Reihe | 6 | Kette |
| **k1** | **Vertikale Reihen (Spalten)** | **7 Pkt je volle Spalte** | **6** | **Kette** |
| **k2** | **Diagonale Reihen** | **10 Pkt je Diagonale (max. 2)** | **6** | **Kette** |
| k3 | Mehrfarbige Felder | 2 Pkt je Jokerfeld, nur wenn ALLE belegt | wenige | kurz |
| k4 | Äußere Felder | 1 Pkt je Randfliese | **1** | **additiv** |
| k5 | Eckplatten | 3/8 Pkt je Eckplatte (oben/unten) | 4 | kurz |
| k6 | Spezialfelder | **−3 Pkt je LEEREM Spezialfeld** | 1 | **additiv** |
| k7 | Farbenreiche Reihen | 4 Pkt je Reihe mit ≥5 Farben | — | Farbe, nicht Ownership |

Quelle: `scoring.rs:41-49` (`ALL_SCORING_TILES`).

**k1 und k2 sind die Zielkriterien** dieser Kampagne: hoher Wert, und das Netz
erreicht sie praktisch nie. Sie sind zugleich die längsten Ketten — sechs Felder
müssen zusammenkommen. Diese Kettenlänge ist, wie Abschnitt 5 zeigt, der rote
Faden durch alle Messungen.

---

## 3. Aufbau des Ownership-Kopfes

140 Ausgänge, Sigmoid, ego-perspektivisch (`config.py:78/118`,
`neural_net.py:1825-1840`):

| Bereich | Inhalt |
|---|---|
| `[0:36]` | P(Feld gefüllt) für die 36 Rasterfelder, **ich** |
| `[36:72]` | dasselbe für den **Gegner** |
| `[72:106]` | 34 Konjunktions-Atome, ich |
| `[106:140]` | 34 Konjunktions-Atome, Gegner |

Die 34 Atome je Spieler: 6 Reihen, 6 Spalten, 2 Diagonalen, 4 Ecken, 1
Alle-Joker, 6 farbenreich, 9 Layout (`P(Slot trägt Jokerplatte)`).
Feldindizierung: `idx(r,c) = (r/2)*12 + (c/2)*4 + (r%2)*2 + (c%2)`
(`scoring.rs:422/432`).

**Trainingsziel:** realisierte Ownership am Endbrett der *gespielten* Partie. Der
Kopf sagt also vorher, **was passieren wird** — nicht, was erreichbar wäre. Diese
Unterscheidung ist eine der offenen Fragen in Abschnitt 7.

**Gütemaße** (gemessen, `PREREG_ownership_selector.md` par.9.2): Konjunktions-AUC
**0,83–0,91**, Brier nur **8–14 %** unter der Grundrate. **Der Kopf ordnet gut und
beziffert schlecht.**

---

## 4. Wo der Kopf in Entscheidungen eingeht — zwei getrennte Maschinen

| Entscheidung | Wer entscheidet | Modul |
|---|---|---|
| **Draft** (welche Fliese / Kuppelplatte) | Gumbel-Suche über Netz-Priors | `net_mcts.rs` |
| **Tiling** (WO die Farbe landet) | ein **Solver**, nicht die Suche | `tiling_solver.rs` |

Der Plattenbau ist eine **Tiling**-Handlung. Beide Verbraucher stehen per Default
auf 0.

**Draft-Pfad** (`net_mcts.rs:1642`, Wrapper `:1711`) formt den **Blattwert**:

    shift += gew[k] * tanh(e[k] / 50)          # WERTUNG_SHAPING_SCALE, :1059
    out = clamp(value + w_own * shift, 0, 1)   # w_own = MOSAIC_OWNERSHIP_W

`e[k]` ist ein **Niveau** (`expected_plate_points`), kein Zuwachs. Der Nenner 50
gilt für **alle acht Kriterien gleich**.

**Die Suche ist Gumbel AlphaZero**, nicht PUCT (`USE_GUMBEL_SEARCH = true`,
`:2869`; der PUCT-Pfad ist Legacy). Wurzelentscheid `logit + gumbel + σ(q)` mit
`σ(q) = (c_visit + max_N)·c_scale·q`, c_visit = 50, c_scale = 1,0 (`:2697`,
`:2727`). In der Arena ist `add_root_noise = false`, die Gumbel-Samples sind also
**abgeschaltet** (`:3842`) — dort konkurriert der Shift gegen die
Log-Prior-Spreizung, nicht gegen Rauschen.

**Tiling-Pfad** ist bereits in der besseren Form: `ownership_marginals`
(`tiling_solver.rs:1054`) liefert **marginale** Feldwerte, der Kandidatenwert ist
`punkte(Abschluss) + w * end_scoring(...)` — **additiv**, damit der Plattenwert
Platzierungspunkte überstimmen *kann* (`:1079`). Ein Gewicht je Kriterium
existiert dort (`:1113`), ausdrücklich weil der Spezialfeld-Posten von −11,70
*„jede Geometrie überdeckt"* (`:1108`, gemessen 2026-08-12).

---

## 5. Die vier versuchten Wege — je mit vorab festgelegter Regel

Alle Arenen: `b18_best` @400 gegen Champion @400, **407 feste Seeds**, gepaart,
Auswertung auf **Block-Ebene** (Blöcke à 25, nB=6, Schwelle |t| > 2,571). Die
Block-Ebene ist Pflicht, weil Paar-SEs auf Partie-Ebene die Streuung massiv
unterschätzen.

**(a) Laufzeit-Regler in Produktform** — `PREREG_gate_c_consumer_sweep.md`
par.15, Replikation `PREREG_gate_c_d1_replication.md`. **Negativ.** Kein Arm hebt
k1/k2; Siege fallen monoton mit der Dosis. Der einzige Treffer (k5, Block-t 2,79)
**replizierte nicht** (frische Seeds: t 1,10).

**(b) Policy-Destillation** — `PREREG_corpus_distillation.md`. Ein Lehrkorpus aus
8.000 regelgeführten Bauer-Partien. **Befund 2026-08-17: der Korpus war in SIEBEN
Trainingsläufen policy-maskiert** (`neural_net.py:679`, `:667`, `:1804`) — die
Frage war nie gestellt worden. Korrekt getragen dann: `b18` erreicht **Parität**
(211/407, p = 0,49) und baut **keine Platten** (k2 = 0,00 in 150 Partien). Der
Prior bietet den Bauzug dabei **dominant an**: 4,91-fache Gleichverteilungsmasse,
in **129 von 130** Held-out-Partien vorn. **Cold Start** (`b20`, ohne jeden Prior)
ebenfalls negativ: 158/407 Siege, k1 t 0,27, k2 t 1,00. **Der Prior war nicht die
Blockade.**

**(c) Konjunktionsform** — `PREREG_conjunction_terms.md`. Die konjunktiven
Kriterien aus **gelernten Atomen** statt aus dem Produkt von sechs
Feldwahrscheinlichkeiten. **Negativ:** k1 +0,14 (Block-t 0,54), k2 +0,07 (1,00).

Der Nachtrag par.9.1 ist der aufschlußreichste Teil — dieselbe Messung gegen den
**Nullarm**:

| Kriterium | Δ | Block-t | Struktur |
|---|---:|---:|---|
| **Plattenpunkte gesamt** | +0,94 | **4,53** | — |
| **k4 Äußere Felder** | +0,33 | **4,01** | **additiv** |
| k3 Mehrfarbige Felder | +1,24 | 1,94 | kurz |
| k5 Eckplatten | +0,27 | 1,89 | kurz |
| k6 Spezialfelder | +0,30 | 1,67 | additiv |
| k2 Diagonalen | +0,13 | 1,58 | Kette 6 |
| **k1 Spalten** | +0,05 | **0,11** | **Kette 6** |

**Die Rangfolge ist exakt die Kettenlänge.** Und k4/k6 sind genau die beiden
Kriterien, die die Konjunktionsform *nicht* anfaßt — sie laufen additiv weiter.
Die additiven bewegen sich, die konjunktiven nicht, gleichgültig ob als Produkt
oder als Atome gerechnet. Damit ist die **Form** als Ursache ausgeschieden.

**(d) Frozen Trunk** (`PREREG_lr_schedule.md`) — nur der Kopf lernt, Policy
bitgenau erhalten. **Negativ:** Ownership-Verlust 0,3466 → 0,3407 und dann flach,
während gemeinsames Training 0,3191 und ein stärker gewichteter Lauf 0,2994
erreicht. Der eingefrorene Rumpf liefert den **schlechteren** Kopf.

---

## 6. Diagnose: Größenordnung und Ordnung

**(i) Der Regler wirkt, unterscheidet aber kaum.** Gepaart je Kandidat über 60
Stellungen (`tools/probes/ownership_shift_magnitude.py`; die Zahlen kommen aus
dem Gumbel-Trace der Engine, nicht aus einem Nachbau): mittlere Verschiebung
0,0026, aber die **Spannweite über die Geschwister** nur **0,0024** gegen eine
**q-Eigenspreizung der Suche von 0,078** — also ~3 %. Nebenbei gemessen:
`max_N` = **19,6**.

**(ii) Er kippt dennoch Entscheidungen — die falschen.** An den Arena-Logs in
situ: **400 von 407 Partien** haben eine abweichende Draft-Folge, erste
Abweichung im Median bei Entscheidung 4, hergeleitete Kipp-Rate **~17 %** je
Draft-Entscheidung. Die Stärke reicht also; die **Richtung** stimmt nicht (siehe
Kettenlängen-Tabelle).

**(iii) `E` ist rundenkonstant, der Nenner ~50× zu groß.** 600 Zustände aus 600
Partien des Held-out-Satzes, 120 je Runde
(`tools/probes/shaping_scale_e_distribution.py`):

| Runde | Median E(k0) | Median E(k1) | Median E(k2) |
|---|---:|---:|---:|
| 1 | 1,362 | 0,082 | 0,038 |
| 3 | 1,403 | 0,082 | 0,025 |
| 5 | 1,174 | 0,116 | 0,023 |

`tanh(0,082/50)` = **0,0016** gegen 0,078 Eigenspreizung. **Herleitung:** damit
der Shift die Größenordnung der Suche erreicht, wären Nenner von etwa **k0 ~17,
k1 ~1, k2 ~0,3** nötig statt einheitlich 50. Der Grund für die Rundenkonstanz ist
strukturell: der Heuristik-Pfad mißt **Fortschritt** und wächst, der
Ownership-Kopf prognostiziert den **Endzustand** und wird schärfer, nicht größer.

**(iv) Die Geschwister-Ordnung ist stabil.** Dieselbe Stellung, zwei
Determinisierungs-Seeds, 40 Stellungen aus 40 verschiedenen Partien ab Runde 2
(`tools/probes/sibling_order_stability.py`): Kendall-Tau **+0,942** (k1) und
**+0,943** (k2). Bemerkenswert: k2 ordnet **genauso stabil bei einem Drittel der
numerischen Größe** (3,7e-04 gegen 1,1e-03). **Betrag und Information laufen
auseinander** — das ist das Problem in einer Zahl.

---

---

## 6a. DER ENTSCHEIDENDE BEFUND (2026-08-18): eine Spalte kostet NICHTS

Die Frage, die dieser Kampagne die ganze Zeit zugrunde lag und nie gestellt
wurde: **kostet der Plattenbau mehr, als er bringt?** Plattenpunkte zaehlen voll
zum Gesamtstand (Nutzer-Klarstellung), es ist also eine reine
Opportunitaetsfrage.

**(A) Fuer die kurzen Ketten: ja, Nullsummentausch.** Gepaart ueber 407 Seeds,
`b18_best` gegen Champion:

| Arm | Siege | eigene Punkte | Marge | Plattenpunkte |
|---|---|---:|---:|---:|
| Nullarm | 211/407 | **44,76** | 0,99 | 2,96 |
| Produktform D1 | 236/407 | **45,03** | 2,69 | 3,86 |
| Konjunktionsform D1 | 229/407 | **44,79** | 2,55 | 3,85 |

Plattenpunkte +0,9 **signifikant** (Block-t 4,16 / 4,53), eigener Gesamtstand
praktisch unveraendert. Die gewonnenen Plattenpunkte sind aus Platzierungspunkten
bezahlt. Die Marge steigt (+1,5 bis +1,7), aber weil der GEGNER verliert, und
nicht signifikant (Block-t 1,32).

**(B) Fuer eine fertige Spalte: nein — sie ist gratis.** Innerhalb des
k1-Bauer-Arms, 1000 Partien, gleiche Einstellungen, Spieler 0:

| | n | Gesamtpunkte | davon k1 |
|---|---:|---:|---:|
| **mit** fertiger Spalte | 419 | **31,23** | 7,02 |
| **ohne** fertige Spalte | 581 | **23,37** | 0,00 |
| Differenz | | **+7,86** | +7,02 |

**Rest: +0,84.** Die Spalte bringt 7,02 Plattenpunkte und kostet nichts an
Platzierungspunkten — sie korreliert sogar mit leicht besserem Restspiel.

*Vorbehalt:* Korrelation innerhalb des Arms, keine Kostenmessung. Partien mit
fertiger Spalte koennten die mit guenstiger Fliesenversorgung sein. Was der
Vorbehalt NICHT erklaert: waere Spaltenbau teuer, muesste der Rest FALLEN.

**Der Mechanismus (Spielregel, `round_end.rs:366`, `engine_manual.md:143-148`):**
die Platzierung zahlt den VERTIKALEN Lauf getrennt vom horizontalen. Wer eine
Spalte aufbaut, kassiert unterwegs schon Platzierungspunkte — Spaltenbau liegt
**auf derselben Achse** wie das normale Spiel, nicht quer dazu. Nutzer-Praxis
dazu: *"wenn ich vertikale oder eck wertungsplatten hab, ist das eine wunderbare
synergie zum normalen spiel"*. Dasselbe gilt fuer k5, das einzige Kriterium, das
der Regler je signifikant gehoben hat (+0,34, Block-t 2,79) — auch dort schliesst
eine Ecke mit Spezialkuppel schneller (`domain_knowledge.md` §6).

**(C) Die Groessenordnung des Ziels.** Der Bauer erreicht die Spalte in **419 von
1000** Partien (42 %), das Netz in **20 von 156** (13 %). *Herleitung:* die
Differenz von ~29 Prozentpunkten mal 7,86 sind **~2,3 Punkte je Partie** allein
bei k1, dazu die Diagonalen mit 10 Punkten je Treffer.

> **WAS DAS FUER DIE DIAGNOSE AENDERT.** Bisher wurde nach einem
> wirtschaftlichen Grund gesucht, warum das Netz die Platten meidet — Kosten,
> Tempo, Opportunitaet. Es gibt keinen. **Das Netz lehnt kostenlose Punkte auf
> seiner eigenen Achse ab.** Damit ist es kein Abwaegungsproblem, sondern ein
> Zuordnungs- und Entdeckungsproblem: das Verhalten wurde nie gelernt, obwohl es
> nichts kostet. Genau dorthin zeigen Abschnitt 7 Punkt (1) — der Value-Kopf hat
> den Vorteil nie als Vorteil gesehen — und der Aussenblick in Abschnitt 8.

### 6b. EINE MENSCHENPARTIE ALS SOLLBILD (2026-08-18)

`static/log/game_20260818_195111_seed558549.log` — Nutzer gegen Champion
`v21_2d_brierbest` @400, Wertungsplatten [1, 5, 6], also **k1 dabei**. n=1, also
kein Beleg, aber das schaerfste Sollbild, das vorliegt.

| | Grundpunkte | Plattenpunkte | Endstand |
|---|---:|---:|---:|
| **Mensch** | 34 | **+13** (k1 **14**, k5 11, k6 −12) | **47** |
| KI | **41** | −9 (k1 **0**, k5 3, k6 −12) | 32 |

**Die KI spielt die Basis besser (41:34) und verliert um 15.** Der gesamte
Unterschied sind die Platten, 25 gegen 3, und der groesste Posten sind die **zwei
fertigen Spalten**, die die KI mit null beantwortet — bei ausliegender Platte.

**Der Aufbau ist progressiv, und er beginnt in Runde 2.** Maximaler vertikaler
Lauf je Runde:

| Runde | Mensch | KI |
|---|---:|---:|
| 1 | 2 | 2 |
| 2 | **4** | 3 |
| 3 | 3 | 2 |
| 4 | **6** (fertig) | 3 |
| 5 | **6** (zweite) | 4 |

Die KI kommt **nie ueber 4** und erreicht ihr Maximum erst in Runde 5, wenn nichts
mehr geht.

**Und die Kostenfrage klaert sich anders als vermutet — es ist eine Frage des
ZEITPUNKTS.** Strafpunkte je Runde:

| Runde | Mensch | KI |
|---|---:|---:|
| 1 | 3 | 1 |
| 2 | **8** | 1 |
| 3 | **12** | 1 |
| 4 | 5 | 1 |
| **5** | **0** | **12** |
| Summe | 28 | 16 |

**In DIESER Partie zahlt der Mensch vorne, die KI hinten** (zur Verallgemeinerung siehe 6c — sie haelt NICHT). 25 von 28 Strafpunkten fallen in Runde
2-4 — der Preis dafuer, Fliesen nach FARBE statt nach Plazierbarkeit zu nehmen. In
Runde 5 zahlt er null, weil die Spalten stehen. Die KI zahlt vier Runden je einen
Punkt und dann **12 in Runde 5** — sie vermeidet die Kosten nicht, sie verschiebt
sie, und bekommt nichts dafuer.

**Die Frage ist also nicht "Strafpunkte oder nicht", sondern wann man sie zahlt
und ob es eine Rendite gibt.** Das ist ein besseres Argument fuer den Spaltenbau
als der Kostenvergleich in Abschnitt 6a — und es passt zu ihm: dort war der "Rest"
+0,84, also kein Preis; hier ist der Preis vorgezogen und in Runde 5
zurueckverdient.

**Gegenprobe an den Arena-Daten** (b18-Seite, Nullarm, 20 Partien mit fertiger
Spalte gegen 136 ohne): Bodenreihe 14,10 gegen 13,69, Differenz **+0,41** — der
Strafleisten-Mechanismus zeigt sich dort NICHT als Aufschlag. Die −28 des Menschen
sind also seine Spielweise in dieser Partie (zwei Spalten UND zwei Eckplatten),
nicht der generelle Preis. *Nebenbefund zur Methode: die erste Messung dieser
Frage am Korpus schlug fehl, weil der letzte Record keinen Bodenwert traegt —
Strafsteine werden am Rundenende geraeumt. Ersetzt durch die Arena-Daten, statt
die 0,00 als Befund zu melden.*

**Der schaerfste Einwand gegen den laufenden Zielwechsel kommt aus dieser
Partie:** das Vollendbarkeits-Label traegt ab Runde 3
(`PREREG_reachability_target.md` par.10), der entscheidende Aufbau beginnt hier
aber in Runde **2**.

### 6c. ZWEITE MENSCHENPARTIE (2026-08-18) — ein Muster haelt, eines nicht

`static/log/game_20260818_200516_seed585858.log`, Platten **[1, 2, 3]** (Spalten,
Diagonalen, Mehrfarbige).

| | Grundpunkte | k1 | k2 | k3 | Endstand |
|---|---:|---:|---:|---:|---:|
| **Mensch** | 38 | **7** | **10** | 6 | **61** |
| KI | **40** | **0** | **0** | **12** | 52 |

**WAS SICH BESTAETIGT — und es ist das Wichtigere:**

1. **Die KI ist bei den Grundpunkten vorn und verliert trotzdem** (40:38, Endstand
   52:61). Wie in 6b (41:34 → 32:47). Zwei von zwei.
2. **Die KI holt die KURZE Kette und laesst die langen liegen.** Sie nimmt k3 mit
   **12 Punkten** — doppelt so viel wie der Mensch — und bleibt bei k1 und k2 auf
   **null**. Das ist die Kettenlaengen-Rangfolge aus
   `PREREG_conjunction_terms.md` par.9.1, hier unabhaengig in einer
   Menschenpartie. Ueber beide Partien: KI-Plattenpunkte kommen aus k5 (3) und k3
   (12), aus k1/k2 **nie** (0/0/0/0).

**WAS SICH NICHT BESTAETIGT — Ruecknahme:** das Strafprofil. Hier zahlt der Mensch
**7** und die KI **23**; in 6b war es 28 gegen 16. Die Aussage "der Mensch zahlt
vorne, die KI hinten" war eine Ein-Partie-Beobachtung und ist **keine Regel**. Sie
ist in 6b entsprechend eingeschraenkt.

| Runde | Mensch | KI |
|---|---:|---:|
| 1 | 2 | 0 |
| 2 | 2 | 6 |
| 3 | 1 | 2 |
| 4 | 0 | **12** |
| 5 | 2 | 3 |

**Was in beiden Partien vorkommt:** eine schwere Spaetstrafe der KI — 12 in Runde
5 (6b) bzw. 12 in Runde 4 (hier). Zwei Faelle, also ein Hinweis und kein Befund.

**Auch der Aufbauweg unterscheidet sich:** hier 2, 2, 3, 0, **6** — die Spalte
faellt in Runde 5 in einem Sprung; in 6b war es progressiv 2, 4, 5, 6. Zwei Wege
zum selben Ziel. Der Einwand aus 6b, das Vollendbarkeits-Label spreche erst ab
Runde 3 und der Aufbau beginne in Runde 2, wird dadurch **schwaecher**: in dieser
Partie liegt der entscheidende Zug in Runde 5, also mitten im tragenden Fenster.

## 7. Offene Fragen, die tragfähigste Ursache zuerst

**(1) Der Lehrkorpus konnte dem VALUE-Kopf nichts beibringen — per Konstruktion.**
Die Bauer-Knöpfe sind ein Prozess-Schalter ohne Spielerparameter
(`bauer_drafting_vorzug(state)`, `self_play.rs:1171`): in den Bauer-Armen bauen
**beide** Spieler. Damit ist das Value-Ziel (Sieg/Niederlage) bezüglich des
Plattenbaus **wegsymmetrisiert** — gemessene Siegquoten der Arme 44–52 %, wie es
die Symmetrie erzwingt. Der Value-Kopf hat über den *Wert* des Plattenbaus also
nichts gelernt; nicht das Falsche, sondern nichts.

Das trifft genau die Stelle, an der alle Messungen hängenbleiben: der Prior
bietet den Bauzug dominant an (4,91×), überstimmt wird er vom **Wert-Backup** —
und der Wert kennt keinen Grund, den Plattenbau zu bevorzugen. Es erklärt auch
den bislang unerklärten Befund aus Tor C par.15, daß ein **stärkerer**
Ownership-Kopf den Verbraucher **inert** machte (91:91, b=c=18).

*Richtungshinweis, konfundiert (Kreuzarm-Vergleich, verschiedene Arme):* Arm A
ohne Bauer-Knöpfe kommt auf 25,5 Punkte, die Bauer-Arme auf 26,7–30,3. Das
Verhalten bringt also absolut Punkte — es ist in keinem Trainingslabel je als
**Vorteil** aufgetreten.

**Naheliegender Test:** einige hundert **asymmetrische** Partien (Bauer gegen
Basisspiel) und prüfen, ob der Value-Kopf dann überhaupt trennen kann.

**(2) Ist die Präferenz des Kopfes RICHTIG?** Abschnitt 6 zeigt: er hat eine
stabile Meinung, die ~50× zu leise ist. Jeder naheliegende Umbau macht sie
lauter. **Niemand hat geprüft, ob sie stimmt** — eine stabil *falsche* Ordnung
hätte alle bisherigen Tests bestanden. Im Baum liegt passende Maschinerie:
`sibling_ranking_diagnostic` vergleicht Kendall-Tau gegen einen **exakten
DFS-Solver** über Geschwister-Nachfolgezustände, bisher nur für den Value-Kopf.

**(3) Beschreibungsmodell als Zielgröße.** Der Kopf ist auf realisierte Ownership
trainiert. In einem Zustand aus normalem Spiel ist *„diese Spalte wird nicht
fertig"* die **richtige** Vorhersage. Als Wert benutzt, ist das selbsterfüllend.
Kandidat für ein besseres Ziel: **Erreichbarkeit** statt Realisierung — *„könnte
ein Spieler, der es anstrebt, Feld f von hier noch füllen"*.

**(4) In Runde 1 ist der Regler exakt wirkungslos.** `q` ist mit und ohne Regler
**bitgleich**, 40 von 40 Stellungen. `E` ist dort *nicht* null (0,082 wie
überall), die Ursache **bleibt ungeklärt**. Keine Randnotiz: in Runde 1 stehen 195
Optionen offen, und dort fällt die Kuppelplatten-Wahl, die festlegt, welche
Spezialfelder man sich einhandelt.

**(5) Das Netz hat eine falsche Gewohnheit gelernt.** Gemessen am **Nullarm**
(Regler AUS, also aus dem trainierten Netz und nicht aus dem Verbraucher): liegt
die k6-Platte, legt `b18` Spezialkuppeln zu **62,8 %** in die unteren Slots (ohne
die Platte 42,3 %) und räumt die oberen von 29,6 % auf **8,5 %**. Die
Nutzer-Spielpraxis (`docs/domain_knowledge.md` §8) verlangt das Gegenteil:
erzwungene Spezialkuppeln nach **oben**, weil sie dort an den billigen
Musterreihen hängen und fast von selbst schließen. Bei k5 dagegen **keine
Reaktion** (50,2 gegen 50,1 %), obwohl §6 dort Spezialkuppeln in die unteren
Ecken will.

**(6) Absolute Seltenheit — Grundrate für jeden Vorschlag.** In den 156 Partien
mit aktiver Spaltenplatte entstehen **20** Spalten auf der `b18`-Seite und 19
beim Champion — und in **keiner** Partie zwei. Bei den Spezialfeldern bleiben
3,94 je Partie leer, und in **0 von 153** Partien kam eine Seite auf null. Es geht
nicht um Feinschliff, sondern um ein Verhalten, das praktisch nicht vorkommt.

---

## 8. Außenblick (2026-08-18 recherchiert)

[AlphaZero in Sparsely Rewarded Games](https://arxiv.org/abs/2607.08984) (Juli
2026) untersucht denselben Fall: AlphaZero spielt stark, hält aber die optimale
Linie nicht — in Chomp stellt es die tragende Invariante nicht zuverlässig wieder
her, **obwohl es die exakten Werte kennt**. Die Lösung dort ist nicht
Wert-Formung, sondern **orakel-abgeleitete POLICY-Supervision als Hilfsverlust**
(AZAL); Ergebnis: perfekte Orakel-Konsistenz auf 10×11. Mehr Eingabekontext
allein schließt die Lücke ausdrücklich nicht.

Bezug zu uns: alle vier geschlossenen Wege waren Wert- oder Laufzeitseite. Der
einzige, der die Policy berührte, hatte eine **regelgeführte Heuristik** als
Lehrer, kein Orakel. Das Projekt besitzt Orakel (exakte Runde-5-Minimax-Wertung
in `round5.rs`; exakter DFS-Solver über Geschwister in
`sibling_ranking_diagnostic`) und nutzt sie bisher nur zum Messen.

Zweiter Punkt: die Wertungsplatten sind ein **je Partie wechselndes Ziel** (drei
von acht). Die Standardantwort dafür sind zielbedingte Politiken
([UVFA](https://proceedings.mlr.press/v37/schaul15.pdf)). Das Netz bekommt
`scoring_tile_ids` **bereits** als Eingabe (`neural_net.py:65`, `:374`) — die
Architektur ist also zielbedingt, es fehlt **Trainingsdruck je Ziel**. Heute lernt
ein globaler Kopf über alle Plattenkombinationen gemittelt. Das paßt zu Punkt (5)
oben: das Netz *reagiert* auf die Platte, aber mit einer gemittelten Gewohnheit
statt einer zielbedingten Strategie.

---

## 9. Glossar

| Kürzel | Bedeutung |
|---|---|
| k0…k7 | die acht Wertungsplatten, Tabelle in Abschnitt 2 |
| Tor A/B/C | Prüfschritte der Kampagne: Kopfgüte / Parität bei Default / Verbrauchernutzen |
| D1, D2, D3 | Dosisstufen des Verbrauchers, `MOSAIC_OWNERSHIP_W,MOSAIC_OWNERSHIP_TILING_W` = 0,1/0,3 · 0,3/1,0 · 1,0/3,0 |
| Nullarm | derselbe Checkpoint mit allen Reglern auf 0 |
| Bauer-Arme | regelgeführte Heuristiken, die gezielt ein Kriterium bauen (Lehrkorpus) |
| Sockel / Schwarm | policy-tragender bzw. policy-maskierter Teil des Trainingsfensters |
| `b18`…`b22` | Trainingsläufe der v21-Serie |
| `par.N` | Abschnitt einer Vorregistrierung |
| Block-Ebene | Auswertung über Blöcke à 25 Partien statt je Partie |

## 10. Wo was liegt

| Was | Datei |
|---|---|
| aktueller Stand, alle Befunde | `evaluations/STATUS.md` |
| Kopplungs-Analyse, aktuelle Entwürfe | `evaluations/PREREG_ownership_coupling.md` |
| Verbraucher-Messreihe | `evaluations/PREREG_gate_c_consumer_sweep.md` |
| Destillation | `evaluations/PREREG_corpus_distillation.md` |
| Konjunktionsform | `evaluations/PREREG_conjunction_terms.md` |
| Aufbau des Lehrkorpus (Arme A–F) | `evaluations/PREREG_ownership_corpus.md` |
| Nutzer-Spielpraxis (Taktiken je Kriterium) | `docs/domain_knowledge.md` |
| Spielregeln | `docs/engine_manual.md` |
| Index aller Vorregistrierungen | `evaluations/PREREG_INDEX.md` |
| Archiv (11.600 Zeilen, kein Einstieg) | `archive/history.md` |

**Zur Auditierbarkeit:** jede Messreihe hat ihre Erfolgsregel **vor** der ersten
Partie schriftlich — einschließlich der Fälle, in denen sie danach gegen die
eigene Hoffnung entschied. Auch die Fehlgriffe sind protokolliert (eine
pseudoreplizierte Stichprobe, ein 25 h altes Wheel, eine falsch behauptete
Suchvariante, ein Hypothesentest den die Symmetrie void machte), damit ein Prüfer
die Kette nachvollziehen kann statt sie zu rekonstruieren.

**Wonach wir konkret fragen:** Punkt (1) und (2) in Abschnitt 7 halten wir für
die tragenden Fragen. Wer einen fünften Weg sieht — oder einen Grund, warum
Punkt (1) die Sache nicht erklärt —, trifft damit den Kern.
