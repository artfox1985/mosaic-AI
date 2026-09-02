<!-- STATUS: ENTSCHIEDEN | Frage: Untersagt der spaltenkompetente Ownership-Kopf (v23) Zellen, die laut Vorrats-Praedikat noch vollendbar waeren? | Beleg: NEIN (par.5, 2026-09-01): 14,64 Prozent tot-kartiert bei tau=0,10 (Block-SE 0,005), Vorgaenger b05 bei 13,89 -- beide Bedingungen der vorab registrierten Abbruchregel erfuellt (<20 Prozent, <5 Punkte Abstand). Von den totkartierten Zellen wurden nur 7 Prozent doch noch gefuellt: der Kopf ist strenger als das Praedikat und hat recht. Stufe 1 wird NICHT eroeffnet. -->

# PREREG: Erreichbarkeits-Nachpruefung am v23-Kopf (Wiedervorlage aus PREREG_reachability_target.md par.17)

Stand **2026-08-28**, **ENTWURF, nichts gebaut.** Durchgehend Plan-Zeitform.

## par.1 ANLASS UND AUSLOESER

`PREREG_reachability_target.md` par.16 hat den Zielwechsel des
Ownership-Kopfs (Vollendbarkeit statt Eintreten) als NICHT-ERFOLG
geschlossen -- gemessen in einer Aera, in der alle Koepfe auf spaltenarmem
Spiel trainiert waren. Die dortige Diagnose bleibt aber strukturell wahr:
ein Eintretens-Ziel auf EIGENPARTIEN ist selbsterfuellend (der Kopf spiegelt
die eigene Politik). b01 ist davon nicht betroffen (Lehrerkorpus); der erste
betroffene Kopf wird **v23** sein, sobald er auf dem v22-Self-Play-Korpus
trainiert wird.

**Ausloeser dieser Prereg: das abgeschlossene v23-Training** (der erste
Ownership-Kopf auf einem spaltenkompetenten SELF-PLAY-Korpus). Nicht
frueher -- die Stufe-0-Diagnose befragt die KARTE des trainierten Kopfs;
vor dem Training gibt es nichts zu messen. Wecker-Anker:
`PREREG_v23_window.md` par.4b.

## par.2 STUFE 0 (trainingsfrei): Karten-Diagnose

Frage: unterschaetzt v23s Eintretens-Karte die Vollendbarkeit? Messgroesse:
Anteil der Spaltenzellen, die das Vorrats-Praedikat
(`ist_zelle_vollendbar`, column_build.rs:563, Pruefstelle bei Ausfuehrung
neu verifizieren) noch erlaubt, deren Karten-Wahrscheinlichkeit aber unter
einer vorab festzulegenden Schwelle liegt ("vom Kopf als tot kartiert").
Bezugsgroessen: dieselbe Diagnose auf b01s Kopf (Lehrerkorpus-Kopf, gleiche
Zustaende) als Vergleichsarm. Block-SE auf Dateiebene. Schwellen und
Zustandsstichprobe werden VOR dem Lauf in dieser Datei nachregistriert
(sie haengen von v23s tatsaechlicher Kartenverteilung ab -- eine heute
gewaehlte Schwelle wuerde gegen eine unbekannte Verteilung raten).

Faellt die Unterschaetzung klein aus: Wiedervorlage schliesst OHNE Training,
das Eintretens-Ziel bleibt bestaetigt nicht der Engpass.

## par.3 STUFE 1 (nur nach positiver Stufe 0): Zielwechsel am Konsument-Instrument

Zielwechsel-Arm wie in `PREREG_reachability_target.md` par.14/16, aber:

* auf dem spaltenkompetenten v22-Self-Play-Korpus statt der Alt-Aera,
* gemessen am inzwischen validierten KONSUMENT-Instrument
  (`PREREG_heuristic_v2_long_rows.md` par.3b.6: Tiling-Pol, argmax,
  Block-t ueber Dateibloecke) statt der damaligen Shaping-Arme.

Dritter Arm, in der Alt-Aera nie getestet: **Rollenteilung statt
Zielwechsel** -- Eintretens-Karte als WERT (graduierte Absicht), hartes
Vorrats-Praedikat als MASKE (nachweislich tote Zellen exakt auf 0).

Abgrenzung: der Vollendbarkeits-FILTER im Aktionsraum
(`PREREG_v23_window.md` par.4, Wecker-Liste) filtert ZUEGE in der Suche;
hier geht es um FELDWERTE im Tiling-Konsumenten.

## par.4 WAS DIESE PREREG NICHT IST

Keine Wiedereroeffnung von `PREREG_reachability_target.md` -- deren par.16
bleibt ENTSCHIEDEN (die dortige Frage war die Alt-Aera-Frage). Diese Datei
traegt die NEUE Frage der neuen Aera und wird nach dem v23-Training
konkretisiert (Schwellen, Stichprobe), dann gefahren.

## par.4a STUFE 0: Schwelle und Stichprobe, VOR dem Lauf registriert (2026-09-01)

*(Nummer am 2026-09-01 von par.4 auf par.4a berichtigt, weil die Datei zwei
Absaetze par.4 hatte; Verweise auf die Abbruchregel meinen diesen Absatz.)*

**Der Ausloeser ist eingetreten:** `v23-b01_brierbest` ist der erste auf
Self-Play-Eigenpartien trainierte spaltenkompetente Stand (0,5150 volle
Spalten am argmax-Instrument gegen 0,3100 des Vorgaengers).

**Machbarkeit geprueft, kein Bau noetig.** Die Praedikat-Seite ist bereits
nach Python exponiert: `plate_completability_json(state_json, player)`
(lib.rs:1176) ruft `column_build::cell_is_completable` (column_build.rs:563 --
der Prereg-Text nennt noch den alten deutschen Namen `ist_zelle_vollendbar`,
umbenannt mit der Bezeichner-Konvention). Die Kartenseite liefert der
Bestandspfad aus `tools/probes/ownership_map_completion_sites_probe.py`.

**Stichprobe:** 300 Zustaende aus `data/selfplay_frozenv3-b01_*.pkl` -- frische
b01-Sockel-Partien (100 Sims, Wurzelrauschen), also die Verteilung, in der das
Netz tatsaechlich spielt, und NICHT das argmax-Instrument. Je Zustand beide
Spielerseiten. Block-SE ueber Dateien.

**Arme:** `v23-b01_brierbest` (der neue Kopf) gegen `v22-b05` (der Kopf der
Vor-Generation), gleiche Zustaende.

**Messgroesse:** Anteil der Spaltenzellen, die das Praedikat noch als
vollendbar fuehrt, deren Kartenwert `p_own` aber unter der Schwelle liegt --
"vom Kopf als tot kartiert".

**Schwelle, vorab und schlicht:** **tau = 0,10** als PRIMAERES Mass. Dazu wird
die ganze Kurve berichtet (Anteile unter 0,05 / 0,10 / 0,20), damit das
Verdikt nicht an einem Schnitt haengt. Die Prereg warnt zu Recht davor, eine
Schwelle gegen eine unbekannte Verteilung zu raten; die Antwort darauf ist
nicht, sie nach den Daten zu waehlen, sondern einen schlichten,
interpretierbaren Schnitt zu nehmen (der Kopf gibt der Zelle unter zehn
Prozent) und die Empfindlichkeit mitzuliefern.

**Entscheidungsregel, vorab:**

* **"klein" -- Wiedervorlage schliesst OHNE Training**, wenn der Anteil
  totkartierter, aber vollendbarer Zellen bei b01 **unter 20 Prozent** liegt
  UND sich von b05 um **weniger als 5 Prozentpunkte** unterscheidet.
* Andernfalls ist Stufe 1 (Zielwechsel am Konsument-Instrument, par.3)
  eroeffnet.

**Zusatz, weil er nichts kostet:** dieselbe Kalibrierung, die das
Bestandswerkzeug schon rechnet -- wurde die als tot kartierte Zelle im
weiteren Partieverlauf TATSAECHLICH noch gefuellt? Das trennt "der Kopf irrt"
von "der Kopf hat recht, das Praedikat ist zu grosszuegig", und ohne diese
Trennung waere ein hoher Anteil nicht interpretierbar.

## par.5 STUFE 0 GEMESSEN -- WIEDERVORLAGE SCHLIESST OHNE TRAINING (2026-09-01)

Werkzeug: `tools/probes/reachability_stage0_probe.py` (neu, im Repo).
300 Zustaende aus `selfplay_frozenv3-b01_*` (Runden 2-4, je 8 Zustaende aus 38
Dateien), beide Spielerseiten, 40.718 offene Zellen vollendbarer Spalten.

| Arm | tot-kartiert (tau=0,10) | Block-SE | Kurve 0,05 / 0,10 / 0,20 | davon spaeter doch gefuellt |
| --- | --- | --- | --- | --- |
| `v23-b01_brierbest` | **0,1464** | 0,0051 | 0,0376 / 0,1460 / 0,2775 | 0,0696 |
| `v22-b05` | 0,1389 | 0,0047 | 0,0278 / 0,1382 / 0,2773 | 0,0707 |

**Beide Bedingungen der Abbruchregel aus par.4 sind erfuellt:** der Anteil
liegt mit 14,64 Prozent unter 20, und der Abstand zum Vorgaenger betraegt 0,75
Punkte statt der kritischen 5. **Die Wiedervorlage schliesst damit OHNE
Training; Stufe 1 wird NICHT eroeffnet.**

**Die Kalibrierung stuetzt das Verdikt zusaetzlich:** von den als tot
kartierten Zellen wurden nur **7 Prozent** im weiteren Partieverlauf doch noch
gefuellt. Der Kopf irrt also in der grossen Mehrheit NICHT -- er ist strenger
als das Vorrats-Praedikat, und die Wirklichkeit gibt ihm recht. Genau diese
Trennung war der Zweck des Kalibrierungs-Zusatzes; ohne sie waeren 14,6
Prozent nicht interpretierbar gewesen.

**Der neue Kopf ist nicht strenger als der alte.** b01 und b05 liegen
innerhalb einer halben Standardabweichung beieinander (0,1464 gegen 0,1389
bei SE 0,005). Die Sorge, ausgerechnet der spaltenkompetente Kopf koennte
Vollendbarkeit unterschaetzen, ist damit gegenstandslos.

**Methodischer Fehler im Erstlauf, korrigiert und benannt:** der erste Lauf
zog alle 300 Zustaende aus der ERSTEN Datei (`n_dateien = 1`) und lieferte
deshalb keine Block-SE -- und mit 22,3 Prozent eine deutlich andere Zahl,
weil eine einzelne Partienserie keine repraesentative Stichprobe ist. Die
Sonde streut die Zustaende jetzt ueber die Dateien (`--per-file`, Default 8);
die Zahlen oben stammen aus dem korrigierten Lauf. Der fehlerhafte Erstlauf
ist nicht in die Bewertung eingegangen.

## par.6 Fundort der Zustandsquelle (nachgetragen 2026-09-01)

Das Artefakt `evaluations/artifacts/reachability_stage0.json` und der Default
der Sonde (`tools/probes/reachability_stage0_probe.py:69`) nennen als Muster
`archive_pre_v24/selfplay_frozenv3-b01_*.pkl`. Dieses Verzeichnis liegt NICHT
im Baum: die Dateien sind am 2026-09-01 mit dem uebrigen Vorgenerations-
Material in das restic-Backup gewandert (`MOSAIC_BACKUP_DIR`, Snapshot-Pfad
`archive_pre_v24/`; Wiederherstellung nach `docs/backup_restore.md`). Wer die
Messung wiederholen will, stellt sie zuerst wieder her; par.5 bleibt als
Ergebnis gueltig, ist aber ohne diesen Schritt nicht reproduzierbar.

## par.7 REPRODUZIERT aus dem Backup (2026-09-02, 02:20, Nachtprogramm N5)

Die Quelldateien (`selfplay_frozenv3-b01_*.pkl`, 40 Dateien) sind aus dem
restic-Snapshot vom 2026-09-01 12:00 nach `data/archive_pre_v24/`
zurueckgeholt und die Sonde mit Default-Muster neu gefahren
(`evaluations/artifacts/reachability_stage0_repro.json`, 23,3 s). **Alle 26
Kennwerte sind zifferngleich** mit `reachability_stage0.json` (0,14641302 /
0,13895 / Block-SE 0,0051246 / 38 Dateien / 300 Zustaende / 40.718 Zellen);
verschieden sind nur zwei Schluesselnamen, die seit dem Erstlauf ins Englische
umbenannt wurden (`n_zustaende` -> `n_states_done`, `n_zellen` -> `n_cells`,
`kurve` -> `curve`). Die Auflage aus par.6 ist damit eingeloest, par.5 ist
reproduzierbar. **Seit 2026-09-02, 03:05 liegen die Quelldateien unter
`<Sicherungswurzel>/archive_pre_v24/`** (Sicherungswurzel = `MOSAIC_BACKUP_DIR`,
sonst `Backups/mosaic-AI` im OneDrive; neben dem restic-Repository, ausserhalb
der Backup-Quelle; Nutzer-Wunsch: keine Unterordner in `data/` vor dem
Tageslauf). Fuer eine Wiederholung den Ordner nach `data/archive_pre_v24/`
zurueckkopieren oder der Sonde ein `--pattern` mit absolutem Pfad geben.
