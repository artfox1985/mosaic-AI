<!-- STATUS: ENTSCHIEDEN | Frage: Wird der Ownership-Kopf brauchbar, wenn sein Ziel von REALISIERUNG auf VOLLENDBARKEIT wechselt -- gelabelt mit dem vorhandenen Vorrats-Praedikat statt mit dem Endbrett der gespielten Partie? | Beleg: par.16 (2026-08-20), Wiederholung mit kopfspezifisch rekalibrierten Nennern (Saettigungs-Wache bestanden): NICHT-ERFOLG -- k1 T+S-neu gegen S-neu +0,23 (Block-t 1,11, Schwelle 2,571), gegen den eigenen Nullarm -0,05. KEIN Siegverlust: T+S-neu 233/407, nominell bester Arm der Kampagne (n.s.). Das Ziel ist nicht der Engpass; es bleibt die Policy-Seite (par.7-Klausel). -->

# PREREG: Zielwechsel des Ownership-Kopfes — Vollendbarkeit statt Realisierung

> **FOKUS-REGEL (Nutzer 2026-08-18):** ab hier wird ausschliesslich **k1**
> bearbeitet. Registrierte "k1 oder k2"-Klauseln bleiben gueltig, werden aber auf
> k1 gelesen (strengere Lesart). Begruendung und Umfang: `evaluations/STATUS.md`,
> Abschnitt "FOKUS-REGEL".


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

### KONKRETISIERUNG VOR DEM START (2026-08-19, vor der ersten Partie)

Die Tabelle oben laesst die DOSIS offen; sie wird hier festgelegt, nicht beim
Bauen:

- **`MOSAIC_OWNERSHIP_W = 1.0`** in S und T+S. Herleitung aus par.6.4 der
  Kopplungs-Prereg, keine freie Wahl: die Nenner (k1 ~1) sind exakt so
  bemessen, dass der Shift bei Gewicht 1 die q-Eigenspreizung der Suche
  erreicht (`tanh(0,082/1) = 0,082` gegen 0,078). Jede andere Dosis wuerde
  die Nenner-Herleitung wieder aufheben.
- **`MOSAIC_OWNERSHIP_GEW = "0,1,0,0,0,0,0,0"`** (nur k1) — Fokus-Regel;
  damit sind die k0/k2-Nenner inert, sie werden trotzdem wie gemessen
  gesetzt: **`MOSAIC_OWNERSHIP_SCALE = "17,1,0.3,50,50,50,50,50"`**.
- **`MOSAIC_OWNERSHIP_TILING_W = 0`** — der Tiling-Verbraucher ist nicht
  Teil dieser Anordnung.
- Modelle: **S = `v21-b18_best`**, **T+S = `v21-b24_best`** (bestes
  val_combined, Epoche 4 — gleiche Auswahlregel wie bei b18). Gegner
  Champion @400, die 407 Gate-C-Seeds, Blockgroesse 25, `--log-games`.
- Umsetzung: GEW/SCALE (kommahaltig) ueber die Eltern-Umgebung an BEIDE
  Arme, der Arm-Schalter ist `MOSAIC_OWNERSHIP_W` (0 = Nullarm; bei W=0
  kehrt der Verbraucher vor jeder Rechnung um, GEW/SCALE sind dann tot).
  Je Modell ein Lauf mit Armen {0, 1.0}; der S-gegen-T+S-Vergleich wird
  wie bei b18/b20 nachtraeglich auf Block-Ebene ueber die identischen
  Seeds gerechnet.
- Protokolliert ohne Entscheidungsregel: der b24-Nullarm (neues Ziel ohne
  Regler) gegen den Champion — misst, ob der Zielwechsel allein Staerke
  kostet.

Vorflug-Kontrollen vor dem Start (beide bestanden, 2026-08-19 ~23:45,
Belege `paired_arena_env_reach_smoke1/2.json`): Determinismus — derselbe
Arm zweimal auf 8 Seeds, der komplette `games`-Block beider Laeufe
identisch; Reglerwirkung — 3 von 8 Partien kippen zwischen W=0 und W=1.
Wheel frisch gebaut und installiert (Paritaets-Hash unveraendert,
`cargo test` 460/0). Start der Arena-Kette 2026-08-19 ~23:50, Arme
S (b18) und T+S (b24) sequenziell.

**KORREKTUR 2026-08-20, vor der ersten gewerteten Partie — `MOSAIC_OWNERSHIP_CONJ=1`
ist PFLICHT in S und T+S.** Die ersten beiden Starts (23:50, vom
Sitzungs-Ende gekillt; Neustart ~10:00, bei Block 15 des Nullarms
gestoppt) liefen in der Default-Produktform. Die liest im Verbraucher
NUR die 72 Feldlabels (`net_mcts.rs:1784-1790`, else-Zweig
`expected_plate_points` ueber `p_own`) — der Zielwechsel sitzt aber
ausschliesslich in den k1-ATOMEN (`reach_target.py::REACH_ATOMS`,
`neural_net.py:1877/1892`), und die Feldlabels sind unveraendert
Realisierung. In Produktform haette Arm T+S das neue Ziel also GAR NICHT
konsumiert; T+S gegen S waere reines Retraining-Rauschen gewesen.
Aufgefallen ueber die Praedikat-Ordnungs-Sonde (Tau +0,083 n.s. gegen
das Puffer-Praedikat — gemessen war die Produktform-Ordnung, siehe
`probe_sibling_vs_predicate_k1.json`). Auch die beiden Offline-Sonden
werden mit `MOSAIC_OWNERSHIP_CONJ=1` wiederholt; die Produktform-Werte
(Tau +0,972 Seed-Stabilitaet / +0,083 gegen Praedikat) bleiben als
Protokoll der FELD-Seite stehen. Verlorene Rechenzeit: ~50 min.
Der Nullarm N ist von CONJ unberuehrt (w_own=0, Verbraucher kehrt vor
jeder Rechnung um).

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

**Die Einschraenkung, praezisiert nach Nutzer-Rueckfrage und MESSUNG
(2026-08-18):** hier stand zunaechst, das neue Ziel sei stumm dort, wo "die
tragenden Entscheidungen fallen — Runde 1-2, die Kuppelplatten-Wahl". Das war
eine ungepruefte Behauptung und ist nur zur Haelfte richtig. Gemessen an den
407er-Arena-Logs (b18-Seite):

| Runde | Kuppelplatten GELEGT (je Partie) | Stapel-ZIEHUNGEN (beide Spieler) |
|---|---:|---:|
| 1 | 2,00 | 9,5 |
| 2 | 2,00 | 6,3 |
| 3 | 2,00 | 2,7 |
| 4 | 2,00 | 1,0 |
| 5 | 0,00 | 0,0 |

- **Beschaffung** (welche Platten-TYPEN man ueberhaupt sieht, §8 Hebel 1 "Joker
  horten"): **81 % der Ziehungen in Runde 1-2.** Dort ist das Label stumm.
- **Platzierung** (welcher Slot, §8 Hebel 2 "erzwungene Spezialkuppeln nach
  oben"): **exakt 2 Platten je Runde in Runde 1-4**, in Runde 5 keine. Die
  **Haelfte der Platzierungen fallt in Runde 3-4** — genau dort, wo das Label
  traegt.

Das neue Ziel deckt also die Platzierungs-Haelfte von §8 ab und die
Beschaffungs-Haelfte nicht. Das ist eine Praezisierung des Vorhabens, nicht seine
Erfuellung — aber eine deutlich guenstigere als zuerst notiert.

**Bezug zum Prototyp-Befund** (`PREREG_plate_policy_supervision.md` par.8): dort
zeigte sich, dass die Tiling-Ebene fuer k1 kein Aktionssignal traegt, weil die
Farbforderung des letzten Feldes im DRAFT entschieden wird. Die Sperre hier passt
dazu: die Vollendbarkeit — also ob der Vorrat noch reicht — ist genau die Groesse,
die sich zwischen Runde 3 und 5 entscheidet und die im Draft beeinflussbar ist.

**Naechster Schritt nach par.9:** Label-Bauer umstellen (Kopfbreite unveraendert),
Warm Start vom Champion, dann die Offline-Pruefungen und die Arena N / S / T+S.

## par.11 UMSETZUNGS-BEFUND (2026-08-18): das Label ist JE ZUSTAND, nicht je Partie

Beim Vorbereiten von par.9 Schritt 2 zeigt sich ein struktureller Unterschied, der
in par.3 noch nicht stand.

**Heute** werden die Ownership-Labels **EINMAL je Partie** aus dem Endbrett
gebildet (`_conjunctions_from_dome`, `neural_net.py:932`) und auf alle Zustaende
derselben Partie angewandt. Das ist billig: eine Rechnung je Partie.

**Vollendbarkeit ist dagegen eine Eigenschaft des ZUSTANDS** — sie haengt am
Brett und am verbleibenden Vorrat und aendert sich mit jedem Zug. Das Label muss
also **je Trainings-Sample** berechnet werden, ueber den neuen Export und mit
einer JSON-Serialisierung des Zustands je Aufruf.

**Kostenschaetzung (Herleitung, nicht gemessen):** das Fenster hat ~4,3 Mio.
Samples; bei ~1 ms je Aufruf sind das ~70 Minuten EINMALIG beim Cache-Bau. Danach
ist der Cache wiederverwendbar.

**Cache-Sicherheit ist geklaert:** der Schluessel wird aus Material mit
`+`-Suffixen gebildet (`neural_net.py:1254-1292`, Muster `+enc2d_v1`,
`+conj_v2`). Ein `+reach_v1` erzwingt einen eigenen Cache, alte Labels koennen
also nicht still weiterverwendet werden.

**Verbilligung, die aus der Sperre folgt:** par.10 zeigt, dass das Label in Runde
1-2 konstant ist (100 % / 98,8 %) und erst ab Runde 3 traegt. Es genuegt daher,
**nur Runde 3-5 umzulabeln** und in Runde 1-2 beim Realisierungs-Label zu bleiben
oder den Gradienten dort zu maskieren. Das halbiert die Kosten und wirft keine
Information weg, die es nicht ohnehin nicht gibt.

**Das ist eine Aenderung an par.3** und wird hier registriert, statt sie beim
Bauen stillschweigend zu treffen: die Variante heisst weiter "Ersetzen", aber
**rundenweise ersetzen** — Runde 3-5 Vollendbarkeit, Runde 1-2 unveraendert. Die
Kopfbreite bleibt bei 140.

## par.12 NACHTRAG-ARM: VORRATSPUFFER STATT BOOLEAN (2026-08-18)

**ENTWURF, nichts gebaut.** Plan-Zeitform.

**Anlass.** Eine externe Spezifikation (`EXP-2026-MICRO-MILESTONE`, 2026-08-18)
schlaegt einen zusaetzlichen Hilfskopf mit abgestuftem Kurzfrist-Label vor. Der
Vorschlag wird in dieser Form **nicht uebernommen** (Begruendung: par.13). Ein
Punkt daraus traegt aber, und er faellt in genau den Durchlauf, der hier ohnehin
ansteht.

**Der Punkt.** par.10 zeigt, dass das Praedikat in Runde 1-2 bei 100 % / 98,8 %
saettigt und deshalb genau dort stumm ist, wo die Beschaffung faellt (81 % der
Stapel-Ziehungen in Runde 1-2, par.10). Die Saettigung ist eine Folge der
**Booleschen Form**, nicht der Groesse selbst: `ist_spalte_vollendbar` prueft, ob
der Vorrat reicht, und wirft den **Abstand** weg.

**Arm P (Puffer).** Dieselbe Rechnung, stetiger Ausgang: je offener Zelle die
Zahl der noch erreichbaren Kopien der geforderten Farbe **minus** dem Bedarf,
ueber die Kette zum Minimum zusammengefasst (die bindende Zelle bestimmt die
Spalte). Quelle unveraendert `provocation::noch_erreichbare_farben` — also
weiterhin **nur beobachtbare Information**, kein Beutelwissen.

- **Kopfbreite unveraendert** (140). Der Ausgang bleibt Sigmoid; das Ziel wird
  auf [0,1] gestaucht (Stauchung vor dem ersten Lauf festzulegen und hier
  nachzutragen — sie ist ein Freiheitsgrad und darf nicht beim Bauen fallen).
- **Kein neuer Kopf, kein Hilfsverlust, kein Annealing.** Arm P ist eine zweite
  Label-Variante im selben Relabeling-Durchlauf, nicht eine zweite Architektur.
- **Eigener Cache-Schluessel** (`+reachbuf_v1` neben `+reach_v1`, Muster
  `neural_net.py:1254-1292`), damit die Varianten sich nicht still mischen.

**Rundenaufteilung, verbindlich:** Puffer in **Runde 1-2**, boolesche
Vollendbarkeit in **Runde 3-5**. Nicht 1-3/4-5: in Runde 3 traegt das boolesche
Label bereits (85,1 %, par.10), dort gibt es nichts zu ersetzen. Arm P schliesst
die Luecke, er verschiebt sie nicht.

**Warum ueberhaupt ein zweiter Arm.** Variante R (boolesch) und Arm P
unterscheiden sich damit nur in Runde 1-2; in Runde 3-5 sind sie identisch.

**Was Arm P NICHT ist: gratis.** Die Label-Rechnung ist es fast (dieselbe
Vorratsabfrage, ein zusaetzlicher Schreibzugriff je Sample) — der **Trainingslauf
ist es nicht**. Zwei Label-Varianten sind zwei Laeufe, und damit ein A/B mit der
bekannten Seed-Empfindlichkeit. Die externe Durchsicht 2026-08-18 nennt Arm P
"kein A/B-Trainingsrisiko"; das ist falsch, und die Kostenzeile in par.9 ist
entsprechend zu fuehren.

**Und er kann sehr wohl schlechter sein als das boolesche Label.** Die externe
Durchsicht argumentiert, schlimmstenfalls lerne der Kopf denselben Wert. Das
gilt nur, wenn die Stauchung informationserhaltend ist — eine zu enge Kappung
(z. B. "3 Fliesen ueber Bedarf = 1,0") macht aus dem Puffer in Runde 1-2 wieder
eine Konstante, nur mit anderem Wert. Die Kappung ist ein **Hyperparameter**,
kein Detail; sie wird vor dem Lauf festgelegt und hier nachgetragen, und genau
darauf zielt die Sperre unten.

### VORAB-SPERRE fuer Arm P (vor jeder Trainingsminute)

Dieselbe Anordnung wie par.5/par.10 (Held-out, je (Partie, Runde) eine Stellung,
150 je Runde), aber fuer eine stetige Groesse:

> **VORAB-REGEL par.12:** der Puffer muss in **Runde 1 und 2** eine
> Standardabweichung ueber die 6 Spalten-Atome von **> 0** in mindestens 80 % der
> Stellungen aufweisen, und der Median darf nicht am Rand der Stauchung liegen
> (nicht in den obersten oder untersten 5 % des Wertebereichs). Andernfalls ist
> der Puffer nur eine umskalierte Konstante, und Arm P wird NICHT gebaut.

Der Sinn ist eng: Arm P existiert **ausschliesslich**, um die Runde-1-2-Luecke zu
schliessen. Zeigt er dort keine Spreizung, hat er keinen Zweck — dann bleibt es
bei Variante R.

**Vor der Sperre, als Handprobe** (uebernommen aus der externen Durchsicht): 20
bis 30 Stellungen aus Runde 1-2 ansehen und pruefen, ob die stetige Skala mit der
Naehe zur Fertigstellung zusammengeht. Das ist keine Entscheidungsregel, sondern
der billige Schutz gegen einen Vorzeichen- oder Normierungsfehler, den die
Sperre selbst nicht faende — eine invertierte Skala haette Spreizung.

**Erfolgsregel:** unveraendert par.7, mit Arm P an der Stelle von T+S. Ein
zusaetzlicher Vergleich P gegen T+S wird protokolliert, entscheidet aber nichts
(die Anordnung ist dafuer nicht gebaut; zwei Trainingslaeufe unterscheiden sich
gemessen staerker im Seed als im Knopf).

### ERGEBNIS DER VORAB-SPERRE par.12 (2026-08-19): BESTANDEN, Stauchung festgelegt

`tools/probes/reachability_buffer_spread.py`, Anordnung wie par.10 (`data/
holdout`, Tiling-Stellungen, je (Partie, Runde) eine, 150 je Runde). Puffer aus
dem erweiterten Export `plate_completability_json` (neues Feld
`col_open_cells`: je offener Normal-Zelle `buffer = erreichbar - Bedarf`,
bindende Zelle = Minimum ueber die Spalte). Rohzahlen:
`evaluations/artifacts/probe_reachability_buffer_spread.json`.

| Runde | bindende Spalten je Stellung | Roh-Puffer p10 / Median / p90 |
|---|---:|---|
| 1 | 5,64 | 6 / 9 / 11 |
| 2 | 5,89 | 2 / 5 / 8 |
| 3 | 5,95 | −1 / 2 / 6 |
| 4 | 5,99 | −3 / 0 / 3 |
| 5 | 5,96 | −4 / −1 / 2 |

**Drei Absicherungen, alle gruen:** Paritaets-Selbsttest Puffer↔Boolean 0
Brueche in 4.500 Spalten-Pruefungen (Spalte unvollendbar ⇔ eine bindende Zelle
mit Puffer < 0); Handprobe 25 Stellungen ohne Vorzeichen-/Normierungsbefund;
der Puffer faellt monoton mit dem Vorrat ueber die Runden.

> **Sperre je Kappungs-Kandidat** (`squash(b) = clip(b, 0, CAP)/CAP`,
> `b < 0 → 0`, Spalte ohne bindende Zelle → 1,0):
>
> | CAP | R1 std>0 | R1 Median | R2 std>0 | R2 Median | Sperre |
> |---:|---:|---:|---:|---:|---|
> | 4 | 2,7 % | 1,000 (Rand) | 80,7 % | 1,000 (Rand) | nicht bestanden |
> | 8 | 70,0 % | 1,000 (Rand) | 100 % | 0,625 | nicht bestanden |
> | **12** | **100 %** | **0,750** | **100 %** | **0,417** | **BESTANDEN** |
> | 16 | 100 % | 0,562 | 100 % | 0,312 | BESTANDEN |
>
> **Festgelegte Stauchung: CAP = 12** — der kleinste bestehende Kandidat; er
> laesst die Mediane beider Runden am weitesten von den Raendern und kappt bei
> p90(Runde 1) = 11 fast nichts. Arm P ist damit baubar.

**Einordnung, unveraendert:** die Sperre belegt SPREIZUNG des Labels in Runde
1-2, nicht seinen Nutzwert. Ob der Puffer die Beschaffungs-Haelfte wirklich
traegt, entscheidet erst par.7.

### ENTSCHEID 2026-08-19 (Nutzer): der Neustart faehrt ARM P, als EIN Lauf

Der abgebrochene `v21-b23` (Variante R) wird als **`v21-b24` mit Arm P**
neu gestartet — Runde 1-2 Puffer (CAP 12), Runde 3-5 boolesch. Begruendung:
das Realisierungs-Label ist in Runde 1-2 zu ~99,5 % konstant (kein Gradient,
und es ist das selbsterfuellende Ziel in genau den Runden mit 81 % der
Stapel-Ziehungen); die einzige Vorbedingung von Arm P (Sperre oben) ist
bestanden. Es faehrt EIN Arm, kein R-gegen-P-Trainings-A/B (par.12:
Seed-Empfindlichkeit schlaegt den Knopf).

Umsetzungs-Festlegungen, vor dem Lauf registriert:

- Knopf: `MOSAIC_REACH_TARGET_K1=p` (Wert `1` = Variante R bleibt moeglich,
  Default aus). Der Knopf wird ab jetzt im Trainingsmanifest protokolliert
  (`train_manifest.py`) — beim b23-Fehlstart waechterte nur der Cache-Key.
- Cache-Key: zusaetzlich `+reachbuf_cap12_v1` neben `+reachk1_r3_v1`.
- Speicherung: die Ownership-Ziele wechseln im Puffer-Modus von int8 auf
  **float16** (stetige Ziele; BCE-with-logits nimmt weiche Ziele nativ, die
  `-1`-Maskierung und der `>= 0`-Loss-Filter bleiben unveraendert).
- Trainingsrezept wie b23 (Warm Start Champion, ownership 1,0, Korpus
  additiv, Traeger `policy_carrier_manifest_own.json`), aber `--epochs 20`
  statt 100 — sonst annealt der Cosine faktisch nicht (T_max-Footgun,
  Optimum lag zweimal bei Epoche 4).

## par.13 WAS AUS `EXP-2026-MICRO-MILESTONE` NICHT UEBERNOMMEN WIRD

Vollstaendig, damit es nicht in einem halben Jahr erneut vorgeschlagen wird.

1. **Die Begruendung des Vorschlags haelt nicht.** Er stuetzt sich darauf, das
   Realisierungs-Label habe in der Aufbauphase "~50 % Varianz" und ersticke
   deshalb den Gradienten. Gemessen ist das Gegenteil: Realisierung liegt bei
   **~13 %** (`DOSSIER_ownership_head.md` 6(C), 20 Spalten in 156 Partien) — das
   Label ist entartet **duenn**. Die 47-55 % sind die **Vollendbarkeit** in
   Runde 4-5 (par.10 oben), wo sie ausdruecklich als informationstheoretisches
   Optimum bewertet ist. Der Vorschlag schreibt die Zahl des Heilmittels der
   Krankheit zu.
2. **Die vorgeschlagene Label-Quelle liegt auf der falschen Ebene.** "Garantiert
   belegbar" soll aus dem Tiling-Solver kommen. Der entscheidet, WO eine Farbe
   landet (`DOSSIER` Abschnitt 4); die Vorratsgarantie ist
   `column_build.rs:506/563`. Und auf der Tiling-Ebene ist fuer k1 **kein
   Aktionssignal** vorhanden: 265 von 265 Kandidaten mit k1 = 0
   (`PREREG_plate_policy_supervision.md` par.8).
3. **Die Definition widerspricht sich.** "Unter Annahme optimaler
   Gegner-Verteidigung, aber ohne Beruecksichtigung von Draft-Unsicherheit" —
   die bindende Beschraenkung IST der Draft (ebd.).
4. **Der Bezug auf 7(4) ist ein Kategorienfehler.** 7(4) beschreibt einen
   **Laufzeit**-Befund (der Regler ist in Runde 1 bitgleich wirkungslos,
   40/40 Stellungen). Ein Trainings-Hilfsziel, das laut eigener Spezifikation
   NICHT in den Draft-Shift eingeht, beruehrt das nicht.
5. **Die dazu behauptete Spielregel stimmt nicht.** "In Runde 1 ist kein Feld in
   <= 2 Zuegen garantiert belegbar, da noch keine Musterreihe gewaehlt ist" —
   abgeschlossene Musterreihen werden am **Rundenende** aufgeloest und schicken
   je eine Fliese auf die Kuppel (`docs/engine_manual.md:125-131`); die Reihe
   mit Kapazitaet 1 ist in Runde 1 abschliessbar.
6. **Zwei der fuenf Erfolgsmetriken sind nicht auswertbar.**
   - `loss_micro < 0,1` ohne Grundraten-Waechter: bei einer Grundrate um 90 %
     erreicht man das durch Vorhersage der Grundrate.
   - `Kendall-Tau >= 0,9 gegen den Vor-Zustand` misst mit
     `sibling_order_stability.py` die Stabilitaet ueber
     **Determinisierungs-Seeds** (`DOSSIER` 6(iv)), nicht ueber Checkpoints — und
     bestraft davon abgesehen genau die Aenderung, die der Versuch herbeifuehren
     soll. Stabilitaet einer moeglicherweise falschen Ordnung (7(2)) ist kein
     Guetemass.
7. **Der Kostenblock ist falsch veranschlagt.** Die Spezifikation sorgt sich um
   Solver-Laufzeit. Teurer ist, dass es ein **Trainings**-A/B ist: der Seed
   bewegt die Metrik staerker als der Knopf, Einzellaeufe sind uninterpretierbar
   (Projektbefund; hier nicht neu geprueft). "Parallel zum asymmetrischen Arm"
   ist damit kein billiger Zusatz.

## par.14 ERGEBNIS (2026-08-20): NICHT-ERFOLG, mit umgekehrtem Vorzeichen

**Anordnung wie registriert** (par.6 + Konkretisierung + CONJ-Korrektur):
407 Gate-C-Seeds, Champion @400 als Gegner, `MOSAIC_OWNERSHIP_CONJ=1`,
`W=1,0`, GEW nur k1, Nenner `17,1,0.3,...`, Blockgroesse 25, exklusiv
(keine CPU-Nebenlast), Vorflug-Gate bestanden (Determinismus identisch,
Reglerwirkung ja). Rohdaten `paired_arena_env_reach_s_b18.json` /
`_reach_ts_b24.json`.

| Arm | Kopf | Regler | Siege | k1-Punkte (aktive Partien) |
|---|---|---|---:|---:|
| N | b18 (Realisierung) | aus | 211/407 | 0,90 |
| S | b18 (Realisierung) | an | 214/407 | 0,85 |
| b24-Null | b24 (Vollendbarkeit) | aus | **221/407** | — (protokolliert) |
| T+S | b24 (Vollendbarkeit) | an | **194/407** | **0,18** |

- **Erfolgsregel-Teil 1 (k1 hoch gegen S): VERFEHLT, invertiert.** T+S gegen
  S auf Block-Ebene: **k1 -0,67 Punkte, t = -3,73** (Schwelle war +2,571).
  Der Kopf mit dem Vollendbarkeits-Ziel steuert die Suche VON den Spalten
  WEG (0,85 -> 0,18).
- **Erfolgsregel-Teil 2 (keine Siegkosten): VERFEHLT.** T+S verliert gegen
  den eigenen Nullarm signifikant (diskordant 29/56, McNemar p = 0,0045);
  zusaetzlich Strafleiste +1,83 Punkte (Block-t 2,87) und Marge -1,56.
- **Arm S gegen N (protokolliert): flach.** k1 -0,05 (Block-t -0,18),
  Siege 214:211 (p = 0,84) — die hoerbare Skala allein bewegt beim alten
  Ziel weiterhin nichts. Nebenbefund Spezialfelder -0,28 (Block-t -2,65).
- **Der Zielwechsel allein kostet keine Staerke:** b24-Null 221/407 —
  numerisch sogar ueber b18-Null (gleiche Seeds).
- Nebenbefund T+S: Spezialfelder +0,56 (Block-t 7,00) — wieder bewegt sich
  das kurze Kriterium, nicht die Kette (dasselbe Muster wie bei allen
  bisherigen Reglern).

**Die Offline-Prufung hatte es angekuendigt** (par.6, exklusiv wiederholt):
die Kopf-Ordnung ist ueber Determinisierungs-Seeds stabil (Tau +0,970),
aber sie folgt dem eigenen Trainings-Praedikat NICHT (Puffer-Summe der
Nachfolgezustaende: Tau -0,03, n.s., 33 Runde-2-Stellungen;
`probe_sibling_vs_predicate_k1.json`). Der Kopf hat das Ziel auf
ZUSTANDS-Ebene gelernt (own_val fiel monoton), unterscheidet aber die
GESCHWISTER eines Knotens nicht danach — dieselbe Fehlerklasse wie beim
Realisierungs-Kopf ("sieht die Absicht kaum", Feld-Kopf-Befund 2026-08-18).

**Folge (par.7, woertlich registriert):** "Dann ist auch das Ziel nicht der
Engpass, und es bleibt die Policy-Seite (orakel-abgeleitete Supervision,
AZAL-Muster) als letzter unversuchter Strang." Dazu unveraendert offen:
das asymmetrische Curriculum (`PREREG_asymmetric_curriculum.md`, greift den
VALUE-Kopf an, nicht den Ownership-Kopf — von diesem Ergebnis unberuehrt).
Der Ownership-Verbraucher-Strang ist damit in ALLEN gemessenen Formen
(Produktform, Konjunktionsform, hoerbare Skala, neues Ziel) negativ.


## par.15 KORREKTUR NACH IMPLEMENTIERUNGS-REVIEW (2026-08-20): par.14 IST EIN DOSIS-ARTEFAKT-VERDACHT, WIEDERHOLUNG REGISTRIERT

**Befund** (`PREREG_implementation_review_targeted.md`, Linse C; vom
Koordinator unabhaengig quantifiziert, 200 k1-aktive Holdout-Zustaende):

| Kopf | e_k1 Median (Konjunktionsform, Ego-Atome 6..12) | p10/p90 | tanh(e/1) > 0,95 |
|---|---:|---|---|
| b18 (Realisierung) | 0,26 | 0,15 / 0,55 | 0 % |
| **b24 (Vollendbarkeit)** | **36,1** | 22,4 / 41,0 | **100 %** |

Mit `W=1, SCALE_k1=1` war der Shift im T+S-Arm konstant 1,0 und
`out = clamp(value + 1,0)` in praktisch jedem Blatt **1,0 — der Arm war
wertblind**, die Suche spielte Prior + Gumbel-Rauschen. Siegverlust und
k1-Einbruch aus par.14 sind damit nicht als Aussage ueber das ZIEL
interpretierbar. Auch die Offline-Sonden (Tau +0,970 Stabilitaet, −0,03
gegen Praedikat) sind entwertet: ihre q(w=1)-Seite lag in 80/80 Faellen
auf der Clamp-Grenze (`probe_sibling_k1_w1.0.json`).

**Die Fehlannahme, benannt:** par.6 setzte "T+S: dieselben Nenner" fuer
gleiche Hoerbarkeit. Der Zielwechsel aendert aber die AUSGABESKALA des
Kopfes (Atome ~0,5-1,0 statt ~0,005) um Faktor ~140 — ein Nenner ist
kopfspezifisch, nicht kriteriumsspezifisch.

**Unberuehrt bleiben:** die b24-Null-Zeile (221/407 — der Zielwechsel
selbst kostet keine Staerke; W=0), Arm S gegen N (flach; b18-e liegt mit
0,26 im linearen Bereich), und saemtliche Label-/Verbraucher-/Messweg-
Freisprueche der Linsen A/B/C.

### WIEDERHOLUNGS-ANORDNUNG (vorab, vor der ersten Partie)

Wie par.6/Konkretisierung, mit EINER Aenderung — Nenner je KOPF nach der
par.6.4-Methode (Shift-Median = q-Eigenspreizung 0,078, tanh-linear):

- **Arm S': b18_best, `MOSAIC_OWNERSHIP_SCALE` k1 = 0,26/0,078 ~ 3,3**
  (die bisherige 1 machte S ~3x lauter als registriert beabsichtigt).
- **Arm T+S': b24_best, k1 = 36,1/0,078 ~ 463.**
- Alles andere unveraendert: `W=1`, GEW nur k1, `CONJ=1`, 407 Seeds,
  Blockgroesse 25, `--log-games`, exklusiv, Vorflug (Determinismus +
  Reglerwirkung + NEU: Saettigungs-Wache — in einer 8-Partien-Probe muss
  q(w=1) im Trace STREUEN, nicht clampen).
- Erfolgsregel unveraendert par.7 (T+S' hebt k1 gegen S' auf Block-Ebene,
  ohne Siegverlust gegen N). Der N-Arm liegt vor und bleibt gueltig.


## par.16 ERGEBNIS DER WIEDERHOLUNG (2026-08-20): NICHT-ERFOLG, diesmal ohne Artefakt

Anordnung nach par.15 (Nenner S' 3,3 / T+S' 463, sonst unveraendert; nur die
aktiven Arme neu gefahren, Nullarme byte-reproduzierbar aus dem Erstlauf).
Vorflug komplett bestanden: Saettigungs-Wache b24@463 Clamp 0,0 % (q-Median
0,557), b18@3,3 Clamp 0,1 %; Determinismus identisch; Reglerwirkung ja.
Rohdaten `paired_arena_env_reach2_s_b18.json` / `_reach2_ts_b24.json`.

| Arm | Siege | k1 vs S' (Block-t) | k1 vs eigener Null (Block-t) |
|---|---:|---|---|
| S' (b18@3,3) | 194/407 | — | — |
| **T+S' (b24@463)** | **233/407** | **+0,23 (t 1,11)** | **−0,05 (t −0,25)** |

- **Erfolgsregel-Teil 1 (k1 signifikant hoch gegen S'): VERFEHLT** — flach,
  weit unter der Schwelle 2,571. Gegen den eigenen Nullarm traegt das
  Shaping exakt nichts bei (−0,05). Einziger Beweger ist erneut das kurze
  Kriterium (Spezialfelder +0,66, t 1,89, n.s.).
- **Erfolgsregel-Teil 2 (keine Siegkosten): ERFUELLT** — T+S' verliert
  nirgends signifikant (gegen b24-Null p=0,169, gegen N p=0,137) und ist
  nominell der staerkste Arm der gesamten Kampagne. Der Schaden aus par.14
  war vollstaendig das Saettigungs-Artefakt.
- Protokolliert: S' gegen N 194:211 (p=0,075, n.s. leicht negativ) — die
  auf Hoerbarkeit kalibrierte Skala nutzt dem alten Kopf nichts;
  T+S' gegen S' Siege p=0,0072, aber modellkonfundiert (b24-Null war schon
  +10 gegen N), keine Zurechnung.

> **ENDVERDIKT (par.7-Klausel, woertlich registriert):** k1 bleibt flach,
> obwohl Label informativ (par.10), Ordnung stabil (Tau 0,970) und die
> Skala nachweislich hoerbar und unsaettigt war. *"Dann ist auch das Ziel
> nicht der Engpass, und es bleibt die Policy-Seite (orakel-abgeleitete
> Supervision, AZAL-Muster) als letzter unversuchter Strang."* Der
> Ownership-VERBRAUCHER-Strang ist damit endgueltig durchgemessen —
> Beifang dieser Wiederholung: das Vollendbarkeits-Shaping ist bei
> korrekter Dosis KOSTENLOS (kein Siegverlust), nur wirkungslos fuer k1.
