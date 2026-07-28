# Vorregistrierung: Abschluss Ownership-Head und Gumbel-Parameter

**Angelegt 2026-07-28, VOR Erhebung der zusaetzlichen Daten.** Zweck: beide
offenen Punkte mit einer im Voraus festgelegten Regel schliessen, statt sie als
"Tendenz, nicht signifikant" liegen zu lassen. Die Regeln unten duerfen nach
Sichtung der Ergebnisse NICHT mehr geaendert werden.

Hintergrund zur Notwendigkeit: am selben Tag hat der `lr1e5`-Arm gezeigt, dass
ein nachtraeglicher Metrikwechsel (`val_combined` statt der vorregistrierten
Metrik) zur falschen Entscheidung gefuehrt haette. Siehe STATUS.md, Abschnitt
"Seed-Sweep".

---

## A) Ownership-Head

### Ausgangslage (6 Seeds, gemessen 2026-07-28)

| | |
|---|---|
| gepaarte Differenz Ø | +0,0017 |
| Streuung der Differenzen | 0,0016 (Population), 0,00175 (Stichprobe) |
| Richtung | 5 besser / 1 schlechter |
| Vorzeichentest | p = 0,2188 |
| **gepaarter t-Test (nachgerechnet)** | **t = 2,38, df = 5, p ≈ 0,063** |
| Effektstaerke | d ≈ 0,97 |

Die Paarung entfernt die Seed-Varianz (Spannweite des `base`-Arms allein:
0,1091..0,1160 = 0,0069), deshalb ist d gross, obwohl die absolute Differenz
klein ist.

### Erhebung

Vier zusaetzliche Seeds (7, 8, 9, 10) in BEIDEN Armen (`base`, `own` mit
`--ownership-weight 0.3`), identisches Rezept wie der Sweep:
`--load v17_best --epochs 100 --lr 5e-5 --lr-schedule cosine`.
Korpus MUSS stabil bleiben (900 Dateien, kein Self-Play parallel).
Kosten: 8 Laeufe a ~27 min ≈ 3,6 h.

### Auswertung -- ab hier unveraenderlich

* **Primaertest**: gepaarter t-Test ueber ALLE 10 Seeds,
  zweiseitig, alpha = 0,05.
* **Metrik**: `value_r2_rounds_1_4` auf dem frozen set (unveraendert).
* Der exakte Vorzeichentest wird zusaetzlich berichtet, ist aber NICHT
  entscheidend. Begruendung fuer den Wechsel des Primaertests, festgehalten
  VOR der Erhebung: der Vorzeichentest verwirft die Betragsinformation und
  war urspruenglich nur gewaehlt, weil kein scipy im Projekt ist -- eine
  praktische, keine methodische Begruendung. Der t-Test ist bei gepaarten
  Differenzen durchweg trennschaerfer. Die t-Verteilung wird per
  Reihenentwicklung berechnet, kein neues Paket.

### Entscheidungsregel

* **p < 0,05 UND Ø-Differenz > 0** → `OWNERSHIP_WEIGHT = 0.3` wird Standard.
* **sonst** → Punkt ist GESCHLOSSEN, `OWNERSHIP_WEIGHT` bleibt 0,0, kein
  weiterer Seed. Begruendung fuer das harte Ende: bei n=10 und dem aus n=6
  geschaetzten d ≈ 0,97 betraegt die Teststaerke ~85 %. Faellt der Test aus,
  ist der wahre Effekt also mit hoher Wahrscheinlichkeit KLEINER als
  geschaetzt -- und damit zu klein, um in der Arena (Aufloesung ~53 %
  Siegquote bei 400 Paaren) je sichtbar zu werden. Das ist dann die saubere
  Aussage, kein offener Rest.

Der Kopf bleibt in beiden Faellen im Code (bei Gewicht 0 inert, zuletzt in
`__init__`/`forward` deklariert, damit ONNX `out[0..3]` stabil bleibt).

### AENDERUNG A) am 2026-07-28, VOR der Erhebung -- Erhebung ENTFAELLT

Die vier Zusatz-Seeds werden NICHT gefahren. Der Punkt wird ohne sie
geschlossen: `OWNERSHIP_WEIGHT` bleibt **0,0**.

**Grund -- und ausdruecklich NICHT der erhoffte Ausgang**, sondern die
Gueltigkeit des Messinstruments. `tools/offline_vs_arena.py` (neu, am selben
Tag) hat die Entscheidungsmetrik erstmals gegen die Arena geprueft: neun
gepaarte Gating-Laeufe ueber v14..v18, davon sechs entschieden. Ergebnis:

| Δ `value_r2_rounds_1_4` | Paare | Richtung richtig |
|---|---|---|
| gross (+0,016..+0,053) | 3 | **3/3** |
| klein (-0,001..-0,009)  | 3 | **0/3** |

Die Metrik hat Aufloesung, aber erst ab einem Abstand von grob 0,015. Das
Pearson r = +0,717 (Permutations-p = 0,031) wird vollstaendig von den drei
grossen Punkten getragen -- Spannweiten-Artefakt, kein Beleg fuer Trennschaerfe
im Feinbereich.

Der Ownership-Effekt betraegt **+0,0017**, also rund ein Zehntel der kleinsten
Differenz, bei der die Metrik je richtig lag, und liegt mitten im Bereich mit
0/3 Trefferquote. Vier weitere Seeds koennten bestenfalls belegen, dass ein
Effekt STATISTISCH existiert, von dem gemessen ist, dass er nichts ueber
Spielstaerke aussagt. Das waere ein praeziser Wert ohne Bedeutung.

Konsistent dazu der aeltere Befund: v11 erreichte als erstes Modell ueberhaupt
positives R² in Runde 1/2 -- und keinerlei Staerkegewinn.

**Falls der Punkt je wieder aufgemacht wird**, ist das richtige Instrument ein
ARENA-Test, kein weiterer Seed. Erwartung dafuer aber gering: bei einem
Offline-Abstand dieser Groesse ist ein Arena-Effekt oberhalb der 400-Paare-
Aufloesung (~53 % Siegquote) unwahrscheinlich.

---

## B) Gumbel-Parameter

`net_mcts.rs:1290`: `sigma(q) = (GUMBEL_C_VISIT + max_N) * GUMBEL_C_SCALE * q`
mit c_visit = 50,0 und c_scale = 1,0.

### B1) c_visit braucht KEINEN eigenen Arena-Test -- Begruendung

Beide Konstanten gehen MULTIPLIKATIV in denselben Term ein. Fuer die Zugwahl
zaehlt nur die Differenz zwischen Aktionen:

    delta_sigma = (c_visit + max_N) * c_scale * delta_q

An der Wurzel zum Entscheidungszeitpunkt ist max_N ~ 93 (Sequential Halving,
16 Kandidaten, 400 Sims: 6+12+25+50). Damit ist `c_visit: 50 -> 0` numerisch
IDENTISCH zu `c_scale: 1,0 -> 0,65`. Eine c_scale-Variation deckt die
c_visit-Achse an der Wurzel also bereits ab.

Unterscheiden tun sich die beiden nur dort, wo max_N KLEIN ist -- an inneren
Knoten und frueh in der Suche (`improved_policy`, net_mcts.rs:1372, wird laut
Doc-Kommentar an beliebigem `nid` aufgerufen, max_N = groesste Besuchszahl
unter dessen Kindern JETZT). Dort setzt c_visit=50 einen Boden: sigma ~ 50*q,
also spuerbarer Q-Einfluss schon bei ein bis zwei Besuchen.

**Regel**: c_visit bekommt nur dann einen eigenen Test, wenn sich c_scale als
sensibel erweist. Erweist sich c_scale als folgenlos, ist die gesamte
Gumbel-sigma-Familie geschlossen.

### B2) c_scale -- erst messen, dann EIN gezielter A/B

Der Code begruendet c_scale = 1,0 (statt mctx-Default 0,1) damit, dass unsere
Q bereits [0,1]-Gewinnwahrscheinlichkeiten sind und keine Min-Max-Reskalierung
brauchen. Diese Begruendung hat eine Luecke: mctx' Min-Max-Normalisierung
spannt die Q der Kinder eines Knotens auf den VOLLEN [0,1]-Bereich. Unsere
rohen Gewinnwahrscheinlichkeiten spannen nur so weit, wie sich die Stellungen
tatsaechlich unterscheiden.

    mctx:   delta_sigma = (50+max_N) * 0,1 * delta_q_norm,  delta_q_norm ~ 1,0
    unser:  delta_sigma = (50+max_N) * 1,0 * delta_q_roh,   delta_q_roh = ?

Bei delta_q_roh ~ 0,05 liegen beide in derselben Groessenordnung, die
Kalibrierung waere vertretbar. Bei ~0,01 ist unser sigma deutlich zu schwach,
bei ~0,3 deutlich zu stark. Die Frage haengt also an EINER nie gemessenen
Groesse: **der tatsaechlichen Spannweite der completed-Q unter den
Wurzelkandidaten.**

**Schritt 1 (Messung, billig)**: ueber `gumbel_trace` (`py.rs:421`,
`collect_trace=true`) an mehreren hundert echten Stellungen erheben:
Spannweite und Interquartilsabstand der completed-Q unter den Kandidaten,
Spannweite von `ln(prior)`, sowie max_N zum Entscheidungszeitpunkt (prueft
zugleich die 93er-Schaetzung oben). Kein neuer Rust-Code noetig.

**Schritt 2 (EIN A/B)**: gepaarter Arena-Test, c_scale = 1,0 (Kontrolle) gegen
den aus Schritt 1 abgeleiteten Wert. Compile-Zeit-Konstante -> zwei Wheels,
beide Arme sequenziell mit identischem Basis-Seed (Muster
`tools/paired_arena_plate_ab.py`). 400 Paare, ~3 h je Arm.

### Entscheidungsregel

* **exakter McNemar p < 0,05 UND Vorteil fuer den neuen Wert** → neuer Wert
  wird Standard, danach optional eine zweite Sprosse.
* **sonst** → c_scale bleibt 1,0, c_visit bleibt 50, **Gumbel-Familie
  GESCHLOSSEN**. Zusammen mit dem bereits gemessenen Nullergebnis fuer
  TOP_M (16 vs 8: perfekter Wash bei 49/100 diskordanten Paaren, p = 1,0000)
  ist das dann die abschliessende Aussage: die Gumbel-Parametrisierung ist
  nicht der Ort, an dem Spielstaerke liegt.

### Bekannte Einschraenkung, bewusst akzeptiert

Die Gumbel-Parameter formen auch das TRAININGSZIEL (die verbesserte Policy),
nicht nur die Spielstaerke bei festem Netz. Ein Effekt koennte sich erst in
der Folgegeneration zeigen. Das sauber zu messen kostet einen vollen Zyklus
statt einer Nacht. Der Arena-Test oben misst NUR die Spielstaerke bei festem
Netz -- ein Nullergebnis schliesst einen Trainingsziel-Effekt nicht aus. Diese
Einschraenkung wird im Abschlussbericht mitgenannt und NICHT als
"kein Effekt vorhanden" verkauft.

---

## AENDERUNG B) am 2026-07-29, NACH Schritt 1, VOR dem A/B

Schritt 1 ist gelaufen (`tools/gumbel_scale_calibration.py`, 216 auswertbare
Stellungen aus dem frozen set, v18_best @ 400 Sims, letzte
Sequential-Halving-Phase, delta_q und delta_ln(prior) ueber DIESELBE
Kandidatenmenge):

| Groesse | Median | IQR |
|---|---|---|
| delta_q | 0,0073 | 0,0029 .. 0,0140 |
| delta_ln(prior) | 1,11 | 0,41 .. 2,12 |
| max_N | 96 | (Schaetzung aus Sequential Halving war 93) |
| **delta_sigma / delta_lnprior** | **1,23** | 0,43 .. 2,77 |

Je Runde: 1,01 / 1,08 / 1,56 / 1,44 (n = 68/71/46/31) -- bemerkenswert stabil.

**Befund: c_scale = 1,0 ist bereits nahe am Gleichgewicht.** q wiegt das
1,23-Fache des Priors; fuer exakte Gleichheit waere c_scale = 0,81. Die
Begruendung im Quellcode ("unsere q sind schon [0,1]") traegt damit -- die
vermutete Fehlkalibrierung existiert nicht.

**Konsequenz fuer den A/B, VOR der Erhebung festgelegt:** Der urspruenglich
vorgesehene Vergleich "1,0 gegen den abgeleiteten Wert" waere 1,0 gegen 0,81 --
19 % Unterschied, das testet nichts. Stattdessen wird ein Wert getestet, der die
Balance DEUTLICH verschiebt: **c_scale = 0,3** (Prior wiegt dann rund das
2,5-Fache von q statt 0,8-Fache).

Damit ist der Test informativ, egal wie er ausgeht:
* Gewinnt 0,3 signifikant, war die Balance doch falsch und die Messung misst
  nicht das, worauf es ankommt.
* Ist es ein Wash, ist die Suche gegen eine 3,3-fache Aenderung dieses Knopfes
  unempfindlich -- zusammen mit dem TOP_M-Nullergebnis (16 vs 8, p=1,0000) ist
  die **Gumbel-Familie dann abschliessend geschlossen**.

Umfang: 400 Spiele je Arm, gepaart, identischer Basis-Seed, v18_best vs
v17_best (dasselbe Muster wie Task #16). Entscheidungsregel unveraendert:
exakter McNemar p < 0,05 UND Vorteil fuer den neuen Wert.

**Sample-Groesse VORAB festgelegt auf 400 je Arm; eine Verlaengerung wird
NICHT vorgenommen** -- bei Task #16 hat genau die Verlaengerung gezeigt, dass
ein knappes p bei n=400 eine Fluktuation sein kann. Bleibt es hier knapp, gilt
das als Wash und nicht als Anlass zum Weitermessen.
