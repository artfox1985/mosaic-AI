<!-- STATUS: OFFEN | Frage: Wird der Ownership-Kopf brauchbar, wenn sein Ziel von REALISIERUNG auf VOLLENDBARKEIT wechselt -- gelabelt mit dem vorhandenen Vorrats-Praedikat statt mit dem Endbrett der gespielten Partie? | Beleg: offen, nichts gebaut. Anlass: vier geschlossene Wege am Verbraucher, externe Durchsicht 2026-08-18. -->

# PREREG: Zielwechsel des Ownership-Kopfes — Vollendbarkeit statt Realisierung

Stand **2026-08-18**, **ENTWURF, nichts gebaut.** Durchgehend Plan-Zeitform.

**Anlass.** Vier Wege sind am Verbraucher gescheitert
(`DOSSIER_ownership_head.md` Abschnitt 5). Die Diagnose zeigt auf das **Ziel**,
nicht auf die Kopplung: der Kopf ist auf realisierte Ownership am Endbrett der
*gespielten* Partie trainiert. In einem Zustand aus normalem Spiel ist *"diese
Spalte wird nicht fertig"* die **richtige** Vorhersage — 20 fertige Spalten in
156 Partien. Als Wert benutzt ist das selbsterfüllend: die Suche wird dorthin
gefuehrt, wo die alte Politik schon war.

Externe Durchsicht 2026-08-18 nennt denselben Punkt als vielversprechendsten
Paradigmenwechsel. Ihr vorgeschlagenes Instrument (`round5.rs`-Minimax) traegt
allerdings nicht: das ist ein **Runde-5**-Orakel und kann Erreichbarkeit in
Runde 2 nicht labeln, wo die Entscheidungen fallen.

---

## par.1 DIE FRAGE

> Lernt der Kopf etwas Nuetzlicheres, wenn sein Ziel lautet *"kann Feld f / Kette
> G von hier aus noch gefuellt werden"* statt *"wurde es gefuellt"*?

---

## par.2 GEPRUEFTER IST-STAND — das Praedikat existiert bereits

| Sache | Befund | Pruefstelle |
|---|---|---|
| Vollendbarkeit je Spalte | `ist_spalte_vollendbar(player, spalte, verbleibend)` | `column_build.rs:506` |
| Vollendbarkeit je ZELLE (verallgemeinerbar) | `ist_zelle_vollendbar(player, r, c, verbleibend)` | `column_build.rs:563` |
| Semantik | prueft gegen den **verbleibenden Fliesenvorrat**: braucht eine offene Zeile mehr Kopien einer Farbe als noch erreichbar sind, ist die Zelle unvollendbar | ebd. |
| Wild-Zellen | zaehlen als vollendbar (farbfrei) | `:513` |
| Special-Zellen | per Default **unberuecksichtigt**, mit Knopf: vollendbar wenn ihre 3 Slot-Nachbarn es sind | `:514-527` |
| Kopfbreite heute | 140 (36+36 Felder, 34+34 Atome) | `config.py:78/118` |
| Feldindizierung | `idx(r,c) = (r/2)*12 + (c/2)*4 + (r%2)*2 + (c%2)` | `scoring.rs:422/432` |

**Das Praedikat ist in JEDER Runde berechenbar und braucht kein Minimax.** Damit
ist der Zielwechsel ein **Relabeling-Durchlauf** ueber den vorhandenen Korpus,
keine Orakel-Generierung.

**Verallgemeinerung auf die uebrigen Geometrien** ist billig und benutzt dieselbe
Zellfunktion: eine Reihe/Diagonale/Eckplatte ist vollendbar, wenn alle ihre
offenen Zellen es sind. Kein neuer Mechanismus, nur eine Schleife ueber die
jeweilige Zellmenge.

---

## par.3 WAS GEAENDERT WIRD — nur der Label-Bauer

**Variante R (Ersetzen), primaerer Arm.** Die 34 Konjunktions-Atome je Spieler
behalten ihre **Bedeutungsplaetze und ihre Anzahl**; nur das Label wechselt von
"Kette G war am Endbrett vollstaendig" auf "Kette G war im Zustand s noch
vollendbar". Die 36 Feldlabels wechseln analog von "Feld f war gefuellt" auf
"Feld f war noch fuellbar".

**Warum Ersetzen und nicht Verbreitern:** die Kopfbreite bleibt bei 140. Damit
bleiben Verbraucher (`apply_ownership_shaping_full`), alle Sonden, die
Arena-Werkzeuge und die Paritaetsprobe **unveraendert** — es aendert sich
ausschliesslich, was der Kopf bedeutet. Ein breiterer Kopf waere die Alternative,
wenn beide Ziele gleichzeitig gebraucht werden; das ist hier NICHT der Fall und
wuerde die Zurechnung nur verteuern.

**Attribution bleibt erhalten**, weil altes und neues Modell getrennt trainiert
und in derselben Arena gegeneinander gefahren werden.

---

## par.4 DER VORBEHALT, der ins Ergebnis gehoert

`ist_spalte_vollendbar` ist eine **notwendige** Bedingung, nicht "erreichbar bei
optimalem Spiel":

- Der **Gegner** kommt nicht vor. Er kann die benoetigten Fliesen wegdraften.
- Die **Draft-Konkurrenz** kommt nicht vor: dass der Vorrat reicht, heisst nicht,
  dass ich ihn bekomme.
- Die **eigene Musterreihen-Logistik** ist nur indirekt drin (ueber die offenen
  Zellen), nicht als Ablaufplan.

Das Label ist damit eine **obere Schranke** der Erreichbarkeit. Es ist trotzdem
grundlegend besser als Realisierung, weil es die selbsterfuellende Prophezeiung
bricht: es sagt, was moeglich WAERE, nicht was die alte Politik getan HAT.

**Diese Schranke ist beim Ergebnis mitzulesen.** Ein Kopf, der Vollendbarkeit
perfekt vorhersagt, sagt NICHT, dass ein Zug gut ist — nur dass er eine
Moeglichkeit offen laesst.

---

## par.5 SPERRE VOR DEM TRAINING — traegt das Label ueberhaupt Information?

Der Zielwechsel hat ein Spiegelbild-Risiko: wenn in Runde 1-2 **fast jede**
Spalte noch vollendbar ist, ist das Label nahezu konstant und traegt so wenig
Information wie die Realisierung am anderen Ende. Das ist billig vorab
messbar — Praedikat ueber den vorhandenen Korpus laufen lassen, kein Training.

**Zu messen VOR jeder Trainingsminute**, je Kriterium und je Runde: die
Positivrate des neuen Labels.

> **VORAB-REGEL:** die Positivrate muss fuer k1 und k2 in mindestens **drei der
> fuenf Runden** im Bereich **5 % bis 95 %** liegen. Liegt sie ausserhalb, ist
> das Label in dieser Runde uninformativ, und der Zielwechsel wird in dieser
> Form NICHT gebaut — stattdessen ist eine strengere Schranke noetig (z. B.
> Vollendbarkeit UND Restzuege ausreichend).

Zusaetzlich zu protokollieren, ohne Entscheidungsregel: die Positivrate der
Realisierungs-Labels derselben Zustaende als Bezug (heute ~13 % bei k1).

---

## par.6 MESSANORDNUNG

Der Zielwechsel allein kann in der Arena **nicht** sichtbar werden: der
Verbraucher ist gemessen ~50x zu leise (`PREREG_ownership_coupling.md` par.6.4,
`tanh(0,082/50)` = 0,0016 gegen eine q-Eigenspreizung von 0,078). Ein Arm "neues
Ziel, alte Skala" waere ein garantierter Nullbefund und deshalb Verschwendung.

Die Arena faehrt daher **drei** Arme, damit die Zurechnung erhalten bleibt:

| Arm | Kopf | Nenner | Was er isoliert |
|---|---|---|---|
| **N** | b18 (Realisierung) | Regler aus | Nullpunkt, liegt vor |
| **S** | b18 (Realisierung) | je Kriterium, gemessene Werte (k0 ~17, k1 ~1, k2 ~0,3) | "hoerbar, aber altes Ziel" |
| **T+S** | neu (Vollendbarkeit) | dieselben Nenner | Beitrag des ZIELS bei gleicher Hoerbarkeit |

Anordnung wie bisher: `@400` gegen Champion `@400`, der 407er-Seed-Satz aus
`distillation_seeds_main.txt`, Blockgroesse 25 (nB=6), `--log-games` ist
**Pflicht** (ohne das Feld `log` sind k1/k2 nicht berechenbar).

**Offline vor der Arena**, weil billig und aussagekraeftig: Geschwister-Ordnungs-
Stabilitaet des neuen Kopfes (`tools/probes/sibling_order_stability.py`, Bezug
k1 Tau +0,942 / k2 +0,943) und die Ordnung gegen das Praedikat selbst.

---

## par.7 VORAB-ERFOLGSREGEL (woertlich, vor der ersten Partie)

> **ERFOLG** heisst: Arm **T+S** hebt **k1 oder k2** signifikant auf Block-Ebene
> gegen Arm **S** (gepaart ueber den Seed, nB=6, zweiseitig p < 0,05, also
> |t| > 2,571) — **und** verliert dabei keine Siege signifikant gegen den
> Nullarm N (exakter zweiseitiger McNemar, p >= 0,05).

**Der Bezug ist S, nicht N.** Das ist der Kern der Anordnung: gegen N gemessen
wuerde ein Zuwachs die Skala und das Ziel vermischen, und die Skala allein
erklaert ihn moeglicherweise vollstaendig.

**k1/k2 und sonst nichts.** k3/k4/k5/k6 bewegen sich schon unter der alten
Konstruktion (`PREREG_conjunction_terms.md` par.9.1: k4 Block-t 4,01, k3 1,94,
k5 1,89) und sind daher kein Nachweis.

**NICHT-ERFOLG** heisst: k1 und k2 bleiben flach, obwohl par.5 ein informatives
Label und die Offline-Pruefung eine stabile Ordnung belegt haben. Dann ist auch
das Ziel nicht der Engpass, und es bleibt die Policy-Seite
(orakel-abgeleitete Supervision, AZAL-Muster) als letzter unversuchter Strang.

**Zusaetzlich zu protokollieren, ohne Entscheidungsregel:** Arm S gegen N. Faellt
dort etwas signifikant aus, ist die Skalenkorrektur allein schon ein Ergebnis und
gehoert getrennt berichtet.

---

## par.8 WAS DIESER VERSUCH NICHT ENTSCHEIDET

- **Ob die Praeferenz des Kopfes RICHTIG ist.** Vollendbarkeit ist eine obere
  Schranke (par.4); ein perfekter Vollendbarkeits-Kopf kann eine Kette
  offenhalten, die kein guter Spieler anstreben wuerde. Die Orakel-Validierung
  der Ordnung (`PREREG_ownership_coupling.md` par.6.3 Stufe 2) bleibt offen und
  wird durch diesen Versuch NICHT beantwortet.
- **Die Symmetrie-Falle im Lehrkorpus.** Der Value-Kopf hat den Plattenvorteil
  nie als Vorteil gesehen, weil in den Bauer-Armen beide Spieler bauten
  (`DOSSIER_ownership_head.md` Abschnitt 7 Punkt 1). Dieser Versuch aendert das
  Ownership-Ziel, nicht das Value-Ziel.
- **Ob der Zielwechsel dem VALUE-Kopf hilft.** Er betrifft nur den
  Ownership-Kopf.
- **Runde 1.** Dort ist der Regler gemessen bitgleich wirkungslos, Ursache
  ungeklaert. Ein besseres Ziel aendert daran nichts, solange die Ursache offen
  ist.

---

## par.9 REIHENFOLGE

1. par.5-Sperre: Positivrate des Praedikat-Labels je Kriterium und Runde.
2. Label-Bauer umstellen (nur `neural_net.py`-Seite; Kopfbreite unveraendert).
3. Training, Warm Start vom Champion, Standardrezept.
4. Offline: Geschwister-Ordnungs-Stabilitaet und Ordnung gegen das Praedikat.
5. Arm S bauen (Nenner je Kriterium als Knopf, Default = heutige 50).
6. Arena N / S / T+S.

## par.10 ERGEBNIS DER SPERRE par.5 (2026-08-18): BESTANDEN, an der Grenze

`tools/probes/reachability_label_base_rate.py`, Held-out-Satz `data/holdout`,
Tiling-Stellungen, je (Partie, Runde) eine, 150 je Runde. Label-Quelle ist der
neue Export `mosaic_rust.plate_completability_json` (Wrapper um
`column_build::ist_spalte_vollendbar`; Vorrat aus
`provocation::noch_erreichbare_farben` — zaehlt ueber die Bretter beider Spieler
und die Strafleisten, also **nur beobachtbare Information**, kein verdecktes
Beutelwissen). Paritaetsprobe nach dem Wheel-Bau gruen, Hash unveraendert.

Granularitaet ist das **Atom** (6 Spalten, 2 Diagonalen), weil der Kopf je
Geometrie lernt:

| Runde | n | k1 Spalten-Atome | k2 Diagonalen-Atome | irgendeine Spalte | irgendeine Diagonale |
|---|---:|---:|---:|---:|---:|
| 1 | 150 | 100,0 % | 100,0 % | 100,0 % | 100,0 % |
| 2 | 150 | 98,8 % | 98,0 % | 100,0 % | 100,0 % |
| **3** | 150 | **85,1 %** | **86,0 %** | 100,0 % | 97,3 % |
| **4** | 150 | **55,4 %** | **52,3 %** | 96,0 % | 77,3 % |
| **5** | 150 | **47,2 %** | **47,7 %** | 96,0 % | 68,7 % |

> **VORABREGEL par.5: BESTANDEN.** k1 3/5 und k2 3/5 Runden im Band 5-95 % —
> gefordert waren je drei. **Bestanden mit null Reserve.**

**Drei Ablesungen:**

1. **Das Label traegt in Runde 3-5, nicht in 1-2.** Dort ist praktisch alles noch
   vollendbar (100 % / 98,8 %), das Label ist konstant und wertlos. In Runde 4-5
   ist es nahezu ausbalanciert (55 % / 47 %) — informationstheoretisch das
   Optimum.
2. **Gegen die Realisierung ist es ein klarer Gewinn**, aber in einem
   VERSCHOBENEN Fenster: Realisierung liegt bei ~13 % ueber die ganze Partie,
   Vollendbarkeit bei 47-85 % in der zweiten Haelfte.
3. **Das Signal sitzt JE SPALTE, nicht in der Aggregation.** "Irgendeine Spalte
   vollendbar" bleibt selbst in Runde 5 bei 96 %, waehrend einzelne Spalten bei
   47 % liegen. Ein Kopf, der nur "kriege ich irgendeine Spalte" lernt, lernt
   nichts. Die 6 Atome muessen einzeln gelernt werden.

**Die Einschraenkung, die ins Ergebnis gehoert:** das neue Ziel ist stumm genau
dort, wo laut `docs/domain_knowledge.md` §8 die tragenden Entscheidungen fallen —
Runde 1-2, die Kuppelplatten-Wahl. Es traegt in Runde 3-5. Das ist eine
Praezisierung des Vorhabens, nicht seine Erfuellung.

**Bezug zum Prototyp-Befund** (`PREREG_plate_policy_supervision.md` par.8): dort
zeigte sich, dass die Tiling-Ebene fuer k1 kein Aktionssignal traegt, weil die
Farbforderung des letzten Feldes im DRAFT entschieden wird. Die Sperre hier passt
dazu: die Vollendbarkeit — also ob der Vorrat noch reicht — ist genau die Groesse,
die sich zwischen Runde 3 und 5 entscheidet und die im Draft beeinflussbar ist.

**Naechster Schritt nach par.9:** Label-Bauer umstellen (Kopfbreite unveraendert),
Warm Start vom Champion, dann die Offline-Pruefungen und die Arena N / S / T+S.

