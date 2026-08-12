# Vorregistrierung: Punkte-Optimierung mit λ UNTER dem Kipppunkt

**Angelegt 2026-08-11, Nutzer-Auftrag** — *"dann kannst auch die punkte
optimierung eintakten (inkludiert die punkteminimierung der gegner)"*.

Geht zurück auf die ältere Nutzer-Frage: *"können wir gleichzeitig unsere punkte
maximieren und die gegnerpunkte minimieren (ohne differenzrechnung der beiden,
weil sonst ist 55 vs. 50 schlechter als 30 vs 15)"*.

## 1. Warum ein geschlossener Punkt wieder aufgeht

`PREREG_punkte_blend_w.md` schloss `w>0` mit **Regel 2**: Kontrolle 321/400
(80,25 %) gegen Arm 300/400 (75,00 %), Block-Delta −5,25pp, t = −2,68.

**Beide Arme liefen bei λ = 2,0** (dort dokumentiert: Kontrolle
`w=0, lambda=2.0`, Arm `w=0.1, lambda=2.0`). Die Formel ist
(`opp_aware_points_utility`, `net_mcts.rs`):

    own_pts  = pts_raw + VALUE_OPP_EPSILON * opp_raw     // ε=0 seit Schema 20
    combined = (own_pts − lambda_aggr * opp_raw).clamp(-1, 1)

Bei λ = 1 ist das eine reine Differenz, bei λ = 2 dominiert der Gegnerterm.
**Der Kipppunkt für den Nutzer-Fall lässt sich ausrechnen** *(meine Rechnung,
nicht gemessen; `pts_raw = tanh(punkte/VALUE_SCALE)`, `VALUE_SCALE = 50`)*:

    55:50  ->  tanh(1,10) = 0,8005   gegen   tanh(1,00) = 0,7616
    30:15  ->  tanh(0,60) = 0,5370   gegen   tanh(0,30) = 0,2913
    0,8005 − 0,7616·λ  >  0,5370 − 0,2913·λ   <=>   0,2635 > 0,4703·λ
    =>  λ < 0,56

**Gemessen wurde bei λ = 2,0 also nicht "helfen Punkte", sondern "hilft es,
30:15 gegenüber 55:50 zu bevorzugen".** Dass das schadet, bestätigt die Formel,
nicht die Nutzlosigkeit des Kanals. Der Bereich λ < 0,56 — der einzige, in dem
die Formel das tut, was der Nutzer verlangt hat — ist **nie gemessen worden**.

Das ist ausdrücklich KEINE Aufhebung von Regel 2 für λ ≥ 1, sondern die
Feststellung, dass ihr Gültigkeitsbereich schmaler ist als die Zeile suggeriert.

## 2. Vorbedingung: GEPRÜFT, der Champion trägt den opp-Kopf

`combined` braucht `opp_points`; ohne den Kopf greift der Kurzschluss
`if opp_points.is_empty()`. Geprüft an den ONNX-Ausgängen:

    v21_2d_brierbest      -> policy, value, moon, points, ownership,
                             value_wdl_logits, opp_points, endgame_margin
    v20_2d_opp_brierbest  -> ... opp_points

Der Champion trägt ihn. **Kein Training nötig**, der Sweep läuft am Bestand.

## 3. Arme — EIN Faktor, und ein Arm ist schon gemessen

Instrument `tools/paired_arena_env_ab.py` im **Mehr-Var-Modus**
(`--env-name MOSAIC_POINTS_UTILITY_W,MOSAIC_AGGR_LAMBDA`), Champion
`v21_2d_brierbest`@400 vs Heuristik@150(dyn), **Basis-Seed 20260902, n=400,
16 Blöcke à 25** — identisch zum historischen Lauf, damit dessen Arm gepaart
mitzählt statt nur erinnert zu werden.

| Arm | `w,λ` | Status |
|---|---|---|
| Kontrolle | `0,0.1` | w=0 kurzschliesst vor λ ⇒ blanker Champion |
| **A** | `0.1,0.1` | NEU — gleiche Dosis wie der schädliche Arm, nur λ geändert |
| **B** | `0.1,0.4` | NEU — knapp unter dem Kipppunkt 0,56 |
| (C) | `0.1,2.0` | **bereits gemessen**: 300/400, weit jenseits des Kipppunkts |

Der Zuschnitt ist bewusst **einfaktoriell**: `w` bleibt auf 0,1 wie im
gemessenen Arm, nur λ wandert. Damit ist der Kontrast genau die
Kipppunkt-Hypothese und nicht zusätzlich eine Dosisfrage. Zwei neue Arme, nicht
mehr — Task-D-Präzedenz (vier Arme, alle H0) und Seed-Skala 5,75pp bei n=400.

## 4. Pflicht-Nebenmessung: die PUNKTESTÄNDE, nicht nur die Siegquote

Die Hypothese handelt von **Niveaus** (55:50 gegen 30:15). Eine Siegquote kann
nicht unterscheiden, ob ein Arm gewinnt, weil er mehr Punkte macht, oder weil er
den Gegner drückt. Deshalb je Arm zusätzlich:

- **mittlerer eigener Endstand** und **mittlerer Gegner-Endstand**
- deren **Differenz** und deren **Summe** (die Summe trennt "beide hoch" von
  "beide niedrig" — genau der Unterschied, um den es dem Nutzer geht)

`scores` liegt im Arena-Ergebnis je Partie schon vor
(`tools/paired_arena_arm_worker.py`, Modulkopf), das kostet nichts.

### Lesart

| Siegquote | Summe der Endstände | Verdikt |
|---|---|---|
| steigt | steigt oder gleich | Kanal wirkt wie gewollt ⇒ Dosis übernehmen |
| steigt | **fällt** | gewonnen durch Drücken statt Punkten — λ trotz Rechnung zu hoch, kleiner testen |
| flach | steigt | mehr Punkte, kein Siegvorteil — Kanal ist neutral, Regel 2 gilt weiter |
| flach/fällt | fällt | Regel 2 gilt auch unter dem Kipppunkt ⇒ endgültig geschlossen |

## 5. Statistik

1. Gepaart über den Spielindex, **identischer Basis-Seed 20260902** in allen
   Armen (und im historischen Arm C).
2. **Block-Ebene als Pflichtinstrument** (16 Blöcke à 25,
   `feedback_arena_block_correlation`) — Block-Delta mit SE und t berichten.
3. Exakter zweiseitiger McNemar auf den diskordanten Paaren.
4. **Bonferroni über die zwei NEUEN Arme**: α = 0,025 je Arm. Arm C zählt als
   bereits erhoben, nicht als dritter Test.
5. Frühstopp unter 150 Paaren nur mit Frisch-Seed-Replikation.

## 6. Verhältnis zu den Injektions-Sweeps

Drei getrennte Kanäle, drei getrennte Vorregistrierungen, **keine gemeinsamen
Läufe**:

- `MOSAIC_UNLOCK_SHAPING_W` — Spezialfelder (`PREREG_injektion_dosis.md`)
- `MOSAIC_WERTUNG_SHAPING_W` — Wertungsplatten-Kriterien (eigene Prereg offen)
- `MOSAIC_POINTS_UTILITY_W`/`AGGR_LAMBDA` — Basis/Platzierung, **diese Datei**

Der Punkte-Kanal ist der einzige, der auf die **93 %** des Ergebnisses wirkt
(Platzierungspunkte); die anderen zwei bedienen die Wertungsplatten. Alle drei
gleichzeitig zu drehen wäre nicht interpretierbar.

## 7. Was dieser Sweep NICHT entscheidet

- Keinen Champion-Wechsel (kein neuer Checkpoint).
- Nicht die Frage, ob der `opp_points`-Kopf als **Hilfsziel** den Rumpf
  verbessert (`PREREG_punktekopf_epsilon.md`, nie gemessen) — hier wird nur
  seine Laufzeit-Verwendung geprüft.
- Nicht `VALUE_OPP_EPSILON`: bleibt 0 (Schema 20).

---

## VERDIKT 2026-08-11: H0, der Kanal bleibt zu

n=400 je Arm, gepaart je Spielindex, Kontrolle `MOSAIC_POINTS_UTILITY_W=0,
MOSAIC_AGGR_LAMBDA=0.1`.

| Arm | Netz | McNemar | Δ Endstand (Block) | SE | t | p~ | Δ Siegquote |
| --- | ---: | ------: | -----------------: | -: | -: | -: | ----------: |
| `0 / 0,1` (Kontrolle) | 321/400 | -- | -- | -- | -- | -- | -- |
| `0,1 / 0,1` | 323/400 | p=0,922 | **+0,85** | 1,08 | 0,79 | 0,43 | +0,5 pp |
| `0,1 / 0,4` | 319/400 | p=0,923 | **-0,40** | 0,97 | -0,41 | 0,68 | -0,5 pp |

Block-Ebene ueber 16 Bloecke a 25 Partien, wie es die stehende Regel verlangt
(Paar-SEs unterschaetzen die Streuung; vgl. `feedback_arena_block_correlation`).
Beide Tests sagen dasselbe, und diesmal in dieselbe Richtung wie McNemar -- kein
Fall wie bei der ISMCTS-Trennmessung, wo die beiden Ebenen auseinanderliefen.

**Entscheidung: `POINTS_UTILITY_WEIGHT` bleibt 0.** Die Vorregistrierung fragte,
ob der Punkte-Kanal UNTER dem Kipppunkt etwas beitraegt, wo er oberhalb schadete.
Antwort: nein, er ist dort einfach wirkungslos. Der Kanal ist damit nicht "falsch
dosiert", sondern als Hebel erledigt -- drittes negatives Ergebnis derselben
Familie nach dem Punkte-Blend (`403a516`) und dem PCR-A/B.

**Nicht verwechseln** mit dem Lambda-Ergebnis vom 09.08.: dort war
`MOSAIC_AGGR_LAMBDA=0,7` auf dem v18only-Mix arena-signifikant (227:173). Das war
die AGGRESSIONS-Groesse allein; hier geht es um das Oeffnen des Punkte-Kanals
(`POINTS_UTILITY_W`) bei kleinem Lambda. Zwei verschiedene Fragen, und nur die
erste hat je ein positives Ergebnis geliefert.

### KORREKTUR desselben Tages: "wirkungslos" war falsch -- er ist WIRKSAM und NEUTRAL

Nutzer-Einwand: *"dann gibt es einen fehler in der implementierung oder an einer
anderen stelle im code. kann nicht sein dass es keinen unterschied macht ob ich
den point/opp head beruecksichtige oder nicht."*

Der Einwand war berechtigt, und er hat einen Formulierungsfehler von mir
aufgedeckt. Geprueft wurde in dieser Reihenfolge:

1. **Ist der Knopf verdrahtet?** Ja -- `MOSAIC_POINTS_UTILITY_W` ->
   `points_utility_w()` (`net_mcts.rs:157`), und `blended_leaf_win_prob` wird von
   allen Blattpfaden aufgerufen, auch dem Haupt-Suchpfad (11 Aufrufstellen).
2. **Hat der Champion den `opp_points`-Kopf?** Ja -- sonst waere der Pfad
   `opp_points.is_empty()` -> `legacy_blended` gelaufen, und das ist numerisch
   `wr`, also exakt die Kontrolle. Das WAERE der Fehler gewesen, den der Nutzer
   vermutet hat. `alphazero_v21_2d_brierbest.onnx` traegt den Ausgang.
3. **Spielen die Arme ueberhaupt verschieden?** Der entscheidende Test, und er
   braucht keine neue Rechnung -- beide Arme liefen auf denselben Seeds:

| Arm | identische Partien | verschiedene | Ø abs. Δ Endstand |
| --- | -----------------: | -----------: | ----------------: |
| `0,1 / 0,1` | 28 | **372 von 400** | **12,10** |
| `0,1 / 0,4` | 34 | 366 von 400 | 10,79 |

(Vergleich ueber Endstaende UND Zuganzahl -- identisch in beiden heisst dieselbe
Partie.)

**Also: 93 % der Partien laufen anders, und einzelne Endstaende verschieben sich
im Mittel um 12,10 Punkte bei einem Niveau von ~52.** Der Knopf greift massiv in
die Zugwahl ein. Was unveraendert bleibt, ist allein die STAERKE (321 gegen 323
von 400).

Der Befund lautet damit nicht "wirkungslos" oder "toter Hebel", sondern: **der
Punkte-Kanal ist wirksam und staerkeneutral -- die Suche findet eine ANDERE, gleich
gute Politik.** Die Entscheidung (`POINTS_UTILITY_WEIGHT` bleibt 0) aendert sich
dadurch nicht, die Begruendung schon: nicht "er tut nichts", sondern "er tut viel,
ohne dass es besser wird". Wer ihn spaeter wieder aufgreift, sucht damit nicht
nach einem fehlenden Signal, sondern nach einer Richtung, in der die Umverteilung
etwas eintraegt.

**Methodische Lehre, dieselbe wie beim Wheel-Vorfall des Tages**: bei einem
H0-Befund IMMER erst pruefen, ob die Behandlung ueberhaupt angekommen ist --
Partie-Gleichheit ist der billigste und schaerfste Test dafuer. Beim Wheel war die
Antwort "nein" (bit-identisch), hier "ja" (372 von 400 verschieden). Ohne diesen
Test sehen beide Faelle im Ergebnis gleich aus.

### ZWEITE KORREKTUR: das Verdikt war gegen die FALSCHE Zielgroesse gemessen

Nutzer-Praezisierung 2026-08-12: *"die zielgroesse ist sieg mit vielen punkten und
den gegner so gut es geht stoeren."*

Ich hatte auf die SIEGQUOTE gemessen und daraus "H0, Knopf bleibt 0" geschlossen.
Das war eine Entscheidung gegen ein Kriterium, das der Nutzer nicht gesetzt hat.
Dieselben Daten, gegen die genannte Zielgroesse ausgewertet (Block-Ebene, 16
Bloecke a 25):

| Arm | Δ eigen | t | Δ Gegner | t | **Δ Marge** | t | Δ Siegquote |
| --- | ------: | -: | -------: | -: | ----------: | -: | ----------: |
| `w=0,1 / λ=0,1` | +0,85 | 0,79 | **-1,14** | -1,42 | **+1,99** | **1,42** | +0,5 pp |
| `w=0,1 / λ=0,4` | -0,40 | -0,41 | -0,76 | -0,82 | +0,36 | 0,26 | -0,5 pp |

Kontrolle `0 / 0,1`: eigen 51,88, Gegner 37,12, Marge +14,76.

**Bei λ=0,1 zeigen alle drei Komponenten der Zielgroesse in die richtige
Richtung.** Der Stoerungsanteil wirkt: der Gegner verliert 1,14 Punkte.

Vorbehalte, ohne Beschoenigung:

1. **Nicht signifikant.** t=1,42, zweiseitig ~p=0,16. Die Konsistenz ueber drei
   Groessen ist KEIN zusaetzlicher Beleg -- Marge ist eigen minus Gegner, es ist
   derselbe Effekt dreimal betrachtet.
2. **Power.** +1,99 bei SE 1,40 braucht etwa die doppelte Blockzahl fuer t=2,
   also n~800 oder eine Replikation auf frischen Seeds.
3. **Mehr Denial ist nicht besser.** λ=0,4 ist auf allen Groessen schlechter als
   λ=0,1 und drueckt die Gegnerpunkte sogar WENIGER (-0,76 gegen -1,14). Lesart
   (Herleitung, nicht gemessen): starke Denial-Gewichte kosten die eigene
   Entwicklung mehr, als sie dem Gegner nehmen.

**Revidiertes Verdikt**: der Punkte-Kanal ist kein erledigter Hebel, sondern ein
UNENTSCHIEDENER mit positiver Richtung auf der tatsaechlichen Zielgroesse. Die
naheliegende Fortsetzung ist eine Replikation von `w=0,1 / λ=0,1` auf frischen
Seeds mit n~800, Metrik VORAB die Marge, nicht die Siegquote.

**Lehre fuer kuenftige Vorregistrierungen**: die Zielgroesse gehoert in die
Vorregistrierung, BEVOR gemessen wird -- nicht die Metrik, die am naechsten liegt.
Dieselbe Familie wie `feedback_preregister_decision_metric`, nur eine Ebene
hoeher: dort ging es um die richtige Metrik fuer eine gegebene Frage, hier um die
richtige FRAGE.

---

## FORTSETZUNG (Nutzer-Auftrag 2026-08-12): λ=0,2 und Replikation

*"ich wuerd noch einen lambda term 0.2 einfuehren. anschliessend dann mit dem
vielversprechendsten noch eine replikation auf frischen seeds fahren"*

### Stufe 1 -- λ=0,2 auf DENSELBEN Seeds

`--env-name MOSAIC_POINTS_UTILITY_W,MOSAIC_AGGR_LAMBDA --arms 0.1,0.2
--control 0,0.1 --seed 20260902 --n-games 400`. Gleicher Basis-Seed wie die drei
vorhandenen Arme, damit gepaart gegen dieselbe Kontrolle gerechnet werden kann.

**Eingebaute Kontrollprobe**: die neu mitgefahrene Kontrolle MUSS die vorhandene
reproduzieren. Tut sie es nicht, hat die zwischenzeitliche Shaping-Formel-Aenderung
den λ-Pfad beruehrt (sie sollte nicht -- alle Shaping-Gewichte stehen auf 0, die
Abkuerzung greift, und der Paritaets-Hash ist unveraendert). Das ist derselbe
Test, der heute den Wheel-Fehler und den Formelfehler gefunden hat.

Erwartung, vorab festgehalten: λ=0,2 liegt zwischen λ=0,1 (Marge +1,99) und λ=0,4
(+0,36). Faellt es AUSSERHALB dieser Spanne, ist die Dosis-Wirkung nicht monoton
und die Lesart "starke Denial-Gewichte kosten mehr als sie nehmen" traegt nicht.

### Stufe 2 -- Replikation auf FRISCHEN Seeds

- **Arm**: der beste der vier nach der unten benannten Metrik. Falls zwei
  gleichauf liegen, der mit dem kleineren λ (weniger Eingriff bei gleichem
  Ertrag).
- **Basis-Seed 20260812**, klar getrennt von 20260902. n=400.
- **METRIK, VORAB und allein entscheidend: die MARGE** (eigene minus Gegnerpunkte),
  auf Block-Ebene ueber 16 Bloecke a 25, gepaart gegen die im selben Lauf
  mitgefahrene Kontrolle `0 / 0,1`.
- Mitberichtet, aber NICHT entscheidend: eigene Punkte, Gegnerpunkte, Siegquote.
  Sie stehen dabei, damit sichtbar bleibt, WOHER die Marge kommt -- eine Marge,
  die nur aus gedrueckten Gegnerpunkten bei fallenden eigenen entsteht, ist etwas
  anderes als eine aus beidem.
- **Erfolgskriterium**: gleiche Richtung wie im ersten Lauf UND t >= 2 auf der
  Marge. Gleiche Richtung ohne Signifikanz heisst "weiter unentschieden, mehr
  Power noetig", nicht "bestaetigt". Gegenlaeufige Richtung heisst, der erste Lauf
  war Rauschen.

Warum nur n=400 und nicht die aus der Power-Rechnung folgenden ~800: die
Replikation soll zuerst die RICHTUNG auf unabhaengigen Seeds pruefen. Ein
Richtungswechsel bei n=400 erledigt die Frage billiger als ein n=800-Lauf, der
dieselbe Antwort teurer gibt. Haelt die Richtung, ist n=800 die naechste Stufe --
das steht dann als eigene Entscheidung an, nicht automatisch.

---

## VERDIKT DER FORTSETZUNG (2026-08-12): unentschieden, und der DENIAL-Anteil repliziert NICHT

### Stufe 1 -- λ=0,2, Erwartung vorab getroffen

Kontrollprobe: **400/400 Partien identisch** zur alten Kontrolle -- die
Shaping-Formel-Aenderungen des Abends beruehren den λ-Pfad nicht.

| Arm | Siege | Δ eigen | Δ Gegner | Δ MARGE | t |
| --- | ----: | ------: | -------: | ------: | -: |
| λ=0,1 | 323/400 | +0,85 | -1,14 | **+1,99** | 1,42 |
| λ=0,2 | 321/400 | -0,07 | **-1,44** | +1,37 | 1,19 |
| λ=0,4 | 319/400 | -0,40 | -0,76 | +0,36 | 0,26 |

λ=0,2 liegt zwischen den bekannten Werten -- die vorab notierte Erwartung ist
getroffen, die Dosis-Wirkung ist monoton fallend. Der Zielkonflikt ist sauber
sichtbar: von 0,1 auf 0,2 wird der Gegner STAERKER gedrueckt (-1,14 -> -1,44),
aber die eigenen Punkte gehen mit (+0,85 -> -0,07), sodass die Marge faellt. Bei
0,4 drueckt es den Gegner nicht einmal mehr gut.

Bester Arm nach der vorab benannten Metrik: **λ=0,1**.

### Stufe 2 -- Replikation auf frischen Seeds (20260812, n=400)

Seed-Probe: **0/400** Kontrollpartien gleich zum Erstlauf -- die Seeds sind
unabhaengig.

| Lauf | Δ eigen | Δ Gegner | Δ MARGE | SE | t |
| ---- | ------: | -------: | ------: | -: | -: |
| Erstlauf (20260902) | +0,85 | **-1,14** | +1,99 | 1,40 | 1,42 |
| Replikation (20260812) | +1,36 | **+0,81** | +0,55 | 1,04 | **0,53** |

**Erfolgskriterium war "gleiche Richtung UND t >= 2".** Die Richtung haelt, t=0,53
nicht. Damit gilt das vorab festgeschriebene Urteil: **weiter unentschieden, mehr
Power noetig -- NICHT bestaetigt.** Gepoolt liegt die Marge bei ~+1,27 mit t~1,45;
auch n=800 reicht nicht.

### Der wichtigere Befund steckt in der Zerlegung

- **Eigene Punkte: in beiden Laeufen positiv** (+0,85 / +1,36). Konsistent.
- **Gegnerpunkte: -1,14, dann +0,81.** VORZEICHENWECHSEL.

Der Margengewinn der Replikation kommt vollstaendig aus den eigenen Punkten, nicht
aus dem Druecken des Gegners. **Der Denial-Anteil, fuer den λ der Regler IST,
repliziert nicht.** Fuer die Nutzer-Zielgroesse ("sieg mit vielen punkten und den
gegner so gut es geht stoeren") heisst das: die erste Haelfte ist plausibel, die
zweite ist durch zwei Laeufe nicht belegt.

Das relativiert auch meine Lesart aus Stufe 1 ("starkes Denial kostet mehr als es
nimmt"). Sie beschrieb eine monotone Reihe, die im Erstlauf existierte; wenn das
Vorzeichen des Gegner-Effekts zwischen Laeufen kippt, war die Monotonie
womoeglich Rauschen mit Struktur. **Als Herleitung markiert, nicht als Befund.**

### Was daraus folgt

`POINTS_UTILITY_WEIGHT` bleibt 0. Nicht weil der Kanal nichts tut -- er aendert
372 von 400 Partien --, sondern weil zwei Laeufe mit n=400 die Richtung nicht
sichern und der Mechanismus, der ihn begruenden wuerde, nicht repliziert. Wer ihn
wieder aufgreift, braucht n>=800 auf frischen Seeds UND eine Erklaerung, warum der
Gegner-Effekt zwischen Laeufen das Vorzeichen wechselt.
