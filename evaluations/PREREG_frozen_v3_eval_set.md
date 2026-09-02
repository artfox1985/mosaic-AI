<!-- STATUS: ENTSCHIEDEN | Frage: Das Eval-Set stammt aus der plattenBLINDEN Aera -- wie sieht die Abloesung aus? | Beleg: GEBAUT (par.7): 1.800 Zustaende aus frischen b01-Sockel-Partien, Ordnung auf allen drei Saetzen stabil, Niveaus stark verschoben. **par.9: die Zirkularitaet ist BELEGT** -- mit einem Orakel aus b01 saettigt b01s recall@16 bei 1,0000, mit dem v21-Gegen-Orakel faellt es auf 0,7825 und die Rangfolge dreht auf 2 von 3 Metriken. **Default fuer frozen_v3 ist ab sofort das v21-Orakel**; ein Orakel wird nie aus einem Netz gebaut, das daran gemessen wird. -->

# Vorregistrierung: `frozen_v3` -- Eval-Set der plattenbewussten Aera

**Angelegt 2026-08-31** auf Nutzer-Auftrag, waehrend `v23-b03` trainierte und
die Warm-gegen-Kalt-Arena lief. Nichts davon ist gebaut.

## par.1 Warum abloesen -- der Bestand, an der Datei geprueft

| Satz | Datei | Zustaende | Korpora | Datum |
| --- | --- | --- | --- | --- |
| `frozen_v1` | `evaluations/frozen_eval_set.pkl` | 1.800 (360 je Runde) | v10b 900, v12 900 | 2026-07-24 |
| `frozen_v2` | `evaluations/frozen_eval_set_v2.pkl` | 1.800 (360 je Runde) | v18 450, v19wdl 450, v19wdlsw 450, v19wdlann 450 | 2026-08-08 |

**Beide stammen aus der Zeit VOR dem plattenbewussten Spiel.** Der Bruch liegt
beim v22/v23-Korpus: `v23-b01` schliesst in der Anker-Arena 0,953 volle
Spalten je Partie, der Anker 0,027, der alte Champion v21 rund 0,10. Ein
Eval-Set aus v10b/v12- oder v18/v19-Partien enthaelt also im Wesentlichen
KEINE Zustaende, in denen eine Spalte kurz vor der Vollendung steht -- genau
die Zustaende, um die die laufende Kampagne sich dreht.

**Das ist keine neue Erkenntnis, nur eine unerledigte:** die
Promotions-Checkliste traegt seit dem 2026-08-28 den Verteilungs-Caveat
(Platt-Fit auf `frozen_v1` = Zustaende der v12-Aera, Anzeige-Kalibrierung
gehoert auf zeitgemaesse Zustaende), und die Kampagne kennt den Grundsatz
"nie auf plattenblindes Spiel eichen". Bisher stand dem nur kein Satz
gegenueber.

## par.2 Was ersetzt wird -- und was ausdruecklich NICHT

**Ersetzt wird die REFERENZ, nicht die Historie.** `build_frozen_eval_set.py`
schreibt es in seinen eigenen Kopf: *"Ab Version frozen_v1 wird dieses Set NIE
wieder ueberschrieben -- ein neuer Bedarf bekommt eine neue Versionsnummer und
einen neuen Dateinamen."* Die Regel gilt weiter. `frozen_v1` und `frozen_v2`
bleiben unangetastet und bleiben als TRENDMETRIK laufbar.

Zwei Bestandteile gehoeren zur Abloesung:

1. **Der Zustandssatz** `evaluations/frozen_eval_set_v3.pkl`
   (`build_frozen_eval_set.py --frozen-version frozen_v3`).
2. **Die Orakel-Labels** `artifacts/frozen_v3_oracle_labels.json`
   (`build_frozen_oracle_labels.py --set ... --model v23-b01_brierbest`).
   Die bestehenden Labels wurden mit einer tiefen `v16_best`-Suche gebaut --
   ein Netz von vor drei Generationen.

**Die Umstellung der VERBRAUCHER ist ein eigener Schritt** und wird je
Verbraucher registriert, nicht still nachgezogen: `oracle_metrics.py`,
`offline_diagnosis.py`, der Platt-Fit fuer die Anzeige-Kalibrierung
(`server.py` `_DISPLAY_CAL_A/_B`, Punkt 5b der Promotions-Checkliste).

## par.3 OFFEN VOR DEM BAU: woher die Zustaende kommen

`v23-b01` hat bereits Self-Play im Baum: `data/selfplay_tor2a-v23b01_*.pkl`,
200 Partien, 35.147 Zuege (Manifest `manifest_tor2a-v23b01_20260831_170305`).
**Aber es ist das argmax-Instrument** -- `--deterministic`, ohne
Wurzelrauschen, gebaut fuer die Spalten-Messung von Tor 2a. Seine Verteilung
ist ENGER als die des Spiels, fuer das geeicht wird: keine Explorationszuege,
kein Rauschen an der Wurzel.

Zwei Wege, der Entscheid gehoert dem Nutzer:

| Weg | Kosten | Was man bekommt |
| --- | --- | --- |
| **(a) Bestand nehmen** (`selfplay_tor2a-v23b01_*`) | 0 | sofort baubar; Verteilung ist argmax-eng, also NICHT die Spielverteilung |
| **(b) frische Sockel-Partien** mit Wurzelrauschen, wie die Korpus-Erzeugung | rund **1 h** fuer 400 Partien (gemessen: 8,3-8,7 s je Partie bei threads 11) | dieselbe Verteilung, aus der auch trainiert wird |

**Empfehlung: (b).** Ein Eichgrund, der die Explorationszuege weglaesst, misst
eine andere Verteilung als die, auf die es ankommt -- und der Zweck der
Abloesung ist gerade, die Verteilungsluecke zu SCHLIESSEN, nicht sie durch
eine neue zu ersetzen.

**Form bleibt wie im Bestand:** 1.800 Zustaende, stratifiziert 360 je Runde
1-5 (so sind v1 und v2 gebaut, so bleiben die Saetze untereinander
vergleichbar).

## par.4 Was der neue Satz leisten muss, VORAB festgelegt

Ein Referenzsatz ist kein Experiment -- er hat kein Verdikt "besser". Die
Abnahme ist deshalb eine Pruefliste, nicht eine Metrik:

1. **Stratifizierung** wie v1/v2: 360 Zustaende je Runde, ein Manifest mit
   Quelle je Zustand.
2. **Reproduzierbarkeit**: Seed im Manifest, Bau aus denselben Dateien
   ergibt denselben Satz.
3. **Ueberbrueckungs-Messung (Pflicht):** dieselben zwei Netze (`v23-b01`,
   `v21_2d_brierbest`) auf ALLEN DREI Saetzen rechnen. Ohne diese Zahl ist
   jede alte Diagnose-Zahl nach der Umstellung unlesbar -- man wuesste nicht,
   ob sich das Netz oder der Massstab bewegt hat. **Das ist der eigentliche
   Ertrag dieser Prereg**, nicht der neue Satz selbst.
4. **Einfrieren**: sobald der Satz einmal als Referenz benutzt wurde, gilt er
   als eingefroren (Projektregel "Einfrieren, sobald etwas Referenz WIRD").

## par.5 Registriertes Risiko: Zirkularitaet beim Orakel

Die Orakel-Labels sollen per tiefer Suche mit `v23-b01` entstehen -- und
`v23-b01` ist zugleich das Netz, dessen Nachfolger spaeter an diesen Labels
gemessen werden. Ein Nachfolger, der b01s Vorlieben teilt, sieht damit
tendenziell besser aus.

**Warum es trotzdem vertretbar ist:** das Orakel ist nicht das ROHE Netz,
sondern eine tiefe Suche darueber -- dieselbe Konstruktion, mit der die beiden
validierten Metriken 7/7 die Arena vorhergesagt haben, und dort war das Orakel
ebenfalls ein Netz der eigenen Linie (`v16_best`).

**Was den Verdacht ausraeumen wuerde, falls er auftritt:** ein zweites
Label-Set mit einem Netz ausserhalb der b01-Linie (Kandidat: der hv2-Lehrer
oder `v21_2d_brierbest`) und der Vergleich der Rangfolgen. Nicht Teil dieses
Auftrags, aber benannt.

## par.6 Was NICHT passieren darf

- `frozen_v1` / `frozen_v2` ueberschreiben (Werkzeug-Regel, par.2).
- Verbraucher still umstellen: jede Umstellung braucht ihre eigene Zeile, sonst
  vergleicht die naechste Sitzung Zahlen ueber einen Massstabswechsel hinweg.
- Den Satz aus einem Korpus ziehen, der im TRAINING desselben Netzes lag --
  der Praezedenzfall dazu ist die Sonden-Skala, die zu 88 Prozent im
  Trainingssatz lag. Die b01-Self-Play-Partien sind davon frei (sie sind nach
  dem Training entstanden), das gilt aber nur, solange der Satz nicht aus dem
  Fenster gezogen wird.

## par.7 GEBAUT UND UEBERBRUECKT (2026-09-01)

**Gebaut** (Nutzer-Entscheid: frische Partien, Weg (b) aus par.3):

| Schritt | Ergebnis |
| --- | --- |
| Zustandsquelle | 400 frische `v23-b01`-Partien, Sockel-Konfiguration (100 Sims, Wurzelrauschen, Seed 20260902), 24,2 min (`data/manifest_frozenv3-b01_20260901_100837.json`, `laufzeit.wanduhr_s` 1450,4; berichtigt 2026-09-01, vorher "22 min"). **Die Quelldateien `selfplay_frozenv3-b01_*.pkl` liegen seit dem 2026-09-01 NICHT mehr im Baum**, sondern als Klartext unter `<Sicherungswurzel>/archive_pre_v24/` (seit 2026-09-02; aus dem restic-Snapshot `e77c2d7c` zurueckgeholt, dann auf Nutzer-Wunsch aus `data/` herausverschoben) und im restic-Repository selbst; die Auflage par.4 Punkt 2 (Neubau aus denselben Dateien) ist damit einloesbar, indem der Ordner nach `data/archive_pre_v24/` zurueckkopiert wird |
| Satz | `evaluations/frozen_eval_set_v3.pkl`, **1.800 Zustaende, exakt 360 je Runde**, Manifest daneben |
| Orakel-Labels | `evaluations/artifacts/frozen_v3_oracle_labels.json`, **1.144 Labels** mit `v23-b01_brierbest` @5000 Sims, 88,8 min, 0 Mismatches, 0 Fehler |

**Reparatur unterwegs:** `build_frozen_eval_set.py` (vom 2026-07-24) las die
Korpusdateien mit rohem `pickle` und starb an frischen Dateien mit
`UnpicklingError: invalid load key, '\x1f'` -- die Korpora werden inzwischen
komprimiert geschrieben. Jetzt nutzt es `corpus_io.load_records_fh`, den
kanonischen Leser fuer BEIDE Formate; `frozen_v1` bleibt unveraendert
reproduzierbar.

### Die Ueberbrueckungs-Messung (par.4 Punkt 3, Pflicht)

Dieselben zwei Netze auf allen drei Saetzen. Als Paar dienen `v23-b01_brierbest`
und `v22-b05` -- ~~die Checkpoints von v19/v20/v21 liegen nicht mehr in
`models/`~~ (Begruendung berichtigt 2026-09-01: der Champion liegt seit dem
2026-08-23 in `models/frozen_champions/v21_2d_brierbest/model.onnx`, par.8
benutzt ihn selbst; die Bruecke haette von Anfang an gegen ihn gefahren
werden koennen), und dieses Paar ist das bestvermessene (Elo 1263 gegen
1136, b01 baut 66 Prozent mehr Spalten).

**Geltungsbereich der Bruecke, nachgetragen 2026-09-01:** die Metriken unten
decken NUR Runden 1-4 ab. `tools/oracle_metrics.py:288-298` schliesst Runde 5
aus, weil die Suche dort auf den exakten Loeser faellt und Prior-Metriken
keinen Sinn haben; `bridge_frozen_v3.json` fuehrt je Netz `overall.n = 915`
und `by_round["5"].n = 0`, obwohl der Satz 360 R5-Zustaende und die
Orakel-Labels 229 R5-Eintraege tragen. Die Bruecken-, Zirkularitaets- und
Relabel-Aussagen (par.7-9) sind damit R1-R4-Aussagen; die Kampagnenfrage der
Betrags-Daempfung sitzt in Runde 5 und ist ueber diese Bruecke nicht
adressiert. Die Bruecken- und Relabel-Artefakte tragen ausserdem keinen
`laufzeit`-Block (Pflichtfeld), die Orakel-Dateien nur `total_elapsed_seconds`.

| Satz | Netz | top3mass | tau | recall@16 | value_pearson |
| --- | --- | ---: | ---: | ---: | ---: |
| frozen_v1 | b01 | 0,5308 | 0,2296 | 0,8750 | 0,6913 |
| frozen_v1 | b05 | 0,5031 | 0,1709 | 0,8739 | 0,5706 |
| frozen_v2 | b01 | 0,5183 | 0,1931 | 0,8591 | 0,7650 |
| frozen_v2 | b05 | 0,4934 | 0,1354 | 0,8484 | 0,6747 |
| frozen_v3 | b01 | **0,6455** | 0,2219 | **1,0000** | **0,9266** |
| frozen_v3 | b05 | 0,6093 | 0,1743 | 0,9760 | 0,8553 |

**Befund 1 -- die Ordnung haelt auf allen drei Saetzen.** b01 steht in jeder
Zeile ueber b05, auf jeder Metrik. Der neue Satz kehrt nichts um.

**Befund 2 -- die NIVEAUS verschieben sich stark, und genau dafuer war die
Bruecke da.** Wer eine alte Diagnosezahl mit einer neuen vergleicht, ohne
diese Tabelle danebenzulegen, misst den Massstabswechsel und nennt ihn
Fortschritt.

**Befund 3 -- die in par.5 registrierte Zirkularitaet ist SICHTBAR, nicht nur
theoretisch.** Auf `frozen_v3` erreicht b01 **recall@16 = 1,0000** -- die
Metrik ist dort gesaettigt und kann nicht mehr unterscheiden. Auch die
Value-Korrelation springt auf 0,93 (gegen 0,69 auf v1). Beides passt dazu,
dass das Orakel mit b01 selbst gebaut wurde: die tiefe Suche waehlt Aktionen,
die b01s Prior ohnehin hoch fuehrt.

**Folgen, verbindlich fuer die Benutzung:**

1. **Auf `frozen_v3` gilt `prior_recall_at_16` als TOT** (gesaettigt). Wer sie
   dort berichtet, berichtet eine Konstante.
2. **Entscheidungsmasse bleiben `prior_mass_on_oracle_top3` und
   `kendall_tau`** -- sie unterscheiden weiter (b01 gegen b05: +0,0362 und
   +0,0476 auf v3, gegen +0,0277 und +0,0587 auf v1).
3. **Value-Korrelationen auf v3 sind NICHT mit denen auf v1/v2
   vergleichbar** und taugen nur als Vergleich ZWISCHEN Netzen auf demselben
   Satz.
4. Der Gegentest aus par.5 (zweites Label-Set mit einem Netz ausserhalb der
   b01-Linie) ist damit **keine Option mehr, sondern faellig, sobald ein
   b01-Nachfolger an diesen Labels gemessen werden soll.**

## par.8 DIE ZIRKULARITAET IST AKUT GEWORDEN -- Gegen-Orakel aus v21 (2026-09-01)

Der erste echte Anwendungsfall des neuen Satzes war der Relabel-Arm
`v23-b05_brierbest` gegen die Kontrolle `v23-b01_brierbest`. Die beiden Saetze
antworten mit VERSCHIEDENEM VORZEICHEN:

| Satz (Orakel) | b05 (relabelt) | b01 (Kontrolle) | Vorsprung |
| --- | --- | --- | --- |
| `frozen_v1` (Orakel aus **v18**) | top3mass **0,5538**, tau 0,2320 | 0,5308, 0,2296 | **b05 +0,0230** |
| `frozen_v3` (Orakel aus **b01**) | top3mass 0,6423, tau 0,2115 | **0,6455**, 0,2219 | b01 +0,0032 |

**Die Richtung des Widerspruchs ist genau die, die par.5 vorhergesagt hat:**
auf dem Orakel, das aus b01 gebaut wurde, gewinnt b01. Auf dem neutralen
Orakel gewinnt der Herausforderer, und zwar um +0,023 -- eine Groesse, die
sonst zwei nachweislich verschiedene Netze trennt (b01 gegen b05: +0,028).

**Damit ist der in par.5 als "nicht Teil dieses Auftrags, aber benannt"
gefuehrte Gegentest faellig.** Nutzer-Entscheid 2026-09-01: *"dann nimm v21
fuer v3"*.

**Warum v21 der richtige Gegenpol ist:** `v21_2d_brierbest` ist der amtierende
Champion, stammt aus der Zeit VOR der Spalten-Linie (0,10 volle Spalten je
Partie gegen b01s 0,6) und teilt mit dem Herausforderer keine
Trainingsvorgeschichte in der relabelten Policy. Ein Orakel aus ihm kann
weder b01 noch b05 systematisch schmeicheln.

**Umsetzung:** `build_frozen_oracle_labels.py` nimmt seit heute auch einen
PFAD als `--model`. Noetig, weil `models/alphazero_v21_2d_brierbest.onnx`
nicht mehr existiert -- der Champion liegt nur noch im getrackten Artefakt
`models/frozen_champions/v21_2d_brierbest/model.onnx`. Die Alternative waere
eine 9-MB-Kopie mit zweifelhafter Herkunft in `models/` gewesen.

Ziel: `evaluations/artifacts/frozen_v3_oracle_labels_v21.json` (eigener Dateiname, die
b01-Labels bleiben unveraendert -- Orakel-Labels sind nach Fertigstellung
unveraenderlich). Kosten nach der heutigen Messung: rund 90 min fuer 1.144
Labels.

**Was der Gegentest entscheidet:** stimmt das v21-Orakel dem v18-Orakel zu
(b05 vorn), ist der Relabel-Vorsprung offline bestaetigt und die b01-Labels
sind als Richter ueber b01-Nachfolger verbrannt. Stimmt es dem b01-Orakel zu,
ist der v18-Befund der Ausreisser -- dann liegt es an der Aera des Satzes,
nicht an der Zirkularitaet.

## par.9 GEGEN-ORAKEL GEFAHREN: die Zirkularitaet ist BELEGT (2026-09-01)

`evaluations/artifacts/frozen_v3_oracle_labels_v21.json`, 1.144 Labels mit dem
eingefrorenen Champion `v21_2d_brierbest` @5000 Sims -- plattenblind, ohne
gemeinsame Vorgeschichte mit b01 oder b05.

| Metrik auf `frozen_v3` | Orakel aus **b01** | Orakel aus **v21** |
| --- | --- | --- |
| recall@16, b01 | **1,0000** (gesaettigt) | **0,7825** |
| recall@16, b05 | 0,9760 | 0,7945 |
| top3mass, b05 / b01 | 0,6423 / 0,6455 | 0,4580 / 0,4644 |
| tau, b05 / b01 | 0,2115 / 0,2219 | 0,1460 / 0,1363 |

**Befund: die Saettigung war ein Artefakt des Orakels, nicht des Satzes.** Mit
einem Orakel von ausserhalb der Linie faellt b01s recall@16 von 1,0000 auf
0,7825, und die Rangfolge dreht sich auf zwei von drei Metriken. Ein Orakel,
das aus dem gepruefeten Netz selbst gebaut ist, schmeichelt ihm messbar.

**Verbindliche Nutzungsregel, ersetzt par.7 Punkt 1-3:**

1. **Das v21-Orakel ist ab sofort der DEFAULT fuer `frozen_v3`.** Die
   b01-Labels bleiben liegen (unveraenderlich), sind aber nur noch fuer
   Vergleiche zulaessig, an denen b01 selbst NICHT beteiligt ist.
2. `recall@16` ist auf `frozen_v3` mit dem v21-Orakel wieder gueltig (0,78,
   nicht gesaettigt).
3. Die Regel gilt allgemein: **ein Orakel wird nie aus einem Netz gebaut, das
   an denselben Labels gemessen werden soll.** Fuer den naechsten Satz heisst
   das, den Orakel-Bauer von vornherein auf ein Netz ausserhalb der zu
   pruefenden Linie zu setzen.

**Was es fuer die Armfrage NICHT leistet:** die Unterschiede zwischen b05 und
b01 bleiben unter jeder Aufloesung (top3mass +0,006 fuer b01, tau +0,010 und
recall +0,012 fuer b05). Drei Orakel, drei Bilder, alle winzig -- offline ist
zwischen den beiden nicht zu entscheiden.
