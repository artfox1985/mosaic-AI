# Mosaic-AI – Status & Fahrplan

**Dieses Dokument traegt NUR Aktuelles und Offenes.** Neufassung vom
2026-08-31 (Nutzer-Auftrag); der vollstaendige Stand davor liegt in
`../archive/history.md`, Kapitel **"Vollstaendiger STATUS-Stand vom
2026-08-31 (vor der Neufassung)"** -- dort steht jede Herleitung, die hier
nur noch als Verweis vorkommt, inklusive der kompletten v22-Chronologie
(Faecher-Durchgang, Schlachtplan v22->v23, Nachtprogramme, abgeloeste
Tor-Fassungen).

**Pflegeregel:** wer einen Befund erzeugt, traegt ihn im selben Zug hier nach
und prueft, ob ein anderer Abschnitt dadurch falsch wird. Wer einen Strang
abschliesst, schiebt die Herleitung ins Archiv und laesst hier eine Zeile mit
Verweis stehen.

**Zahlen ohne Datum stammen aus dem Stand vom 2026-08-30 und sind in dieser
Neufassung nicht neu nachgemessen worden.**

**Dauerhaftes Prozesswissen steht NICHT hier**, sondern kanonisch in
`../docs/`: `generation_loop.md` (die Schleife und ihre Tore),
`promotion_checklist.md`, `generation_naming.md`, `working_rules.md`,
`pitfalls.md`, `measured_runtimes.md`, `architecture_reference.md`. Wer an
diesen Inhalten etwas aendert, aendert es DORT.

---

## 1. UEBERGABE an die naechste Sitzung (2026-09-09, 20:30)

**MASCHINE FREI, nichts laeuft.** Champion laut `models/champion.txt`:
**`v26-b01_brierbest`, Elo 1389** [1349, 1432] aus 1.240 Partien. Vorgaenger `v25-b01`
steht bei 1355, `v24-b07` bei 1296, der Anker fix bei 1000.

**Die Promotion v26-b01 ist VOLLSTAENDIG durch**, alle sieben Schritte der
`docs/promotion_checklist.md` inklusive eingefrorenem Artefakt. Der Generationsbericht
steht am Ende von `../archive/history.md`.

### Warum diese Generation zaehlt

Sie ist die erste, in der **nur das Material** geaendert wurde -- Architektur, Rezept und
Spec waren eingefroren. Damit heisst "v26 schlaegt v25" zum ersten Mal wirklich, dass das
Material traegt.

| Kante | Ergebnis | Bemerkung |
| --- | --- | --- |
| Tor 1, Seed 20261030 | 210:190 | voller Lauf, p 0,368 |
| Tor 1, Seed 20261031 | 85:55 | SPRT nach 70 Paaren, p 0,0135 |
| Tor 1, Seed 20261032 | 226:174 | voller Lauf ohne Fruehstopp, p 0,0080 |
| **verzerrungsfrei (die zwei vollen)** | **436:364 = 54,5 %** | der Fruehstopp-Lauf stoppte, WEIL er vorne lag |
| Anker | 127:23 | v25-b01 und v24-b07 hatten beide 126:24 |
| Champion-2 gegen `v24-b07` | 98:52 | erste Kante gegen das ARTEFAKT statt die lebende Datei |

**Struktur:** der neue Sockel liegt bei 0,737 vollen Spalten je Seite (Vorgeneration
0,637); gegen den Anker baut der Champion 1,267 je Partie gegen dessen 0,060.

### ERSTE AUFGABE DER NEUEN SITZUNG

1. **v27-Erzeugung starten** -- `bash tools/night_v27_generate.sh` (drei Klassen, Generator
   `v26-b01`, Seeds 20260914/15/16, rund 8,4 h nach den v26-Manifesten). Das Skript wartet selbst auf eine freie
   Maschine. **Daneben gehoert der Cache-Waechter**, zwingend mit
   `MOSAIC_IGNORE_POLICY_TARGET_VALID=1` -- der Aufruf steht im Kopf des Skripts.
2. **Danach `bash tools/night_v27_chain.sh`** -- wartet auf den `laufzeit`-Block der
   Ausflug-Klasse und faehrt dann Kennzahl, Traegermanifest (580), G-2-Auswahl aus der
   TEMPERIERTEN Haelfte, Fenster (~2.946), Bloecke, Monolith und das Training `v27-b01`.
3. **`/mosaic-generation-turnover`: Schritte 2, 3 und 4 gefahren (21:38-21:45, Snapshot
   `1dba15e8`, Chronik):** 9 Ketten-Skripte per `git rm`, 1.602 Korpusdateien und 6
   Manifeste, danach 2.802 Waisen-Bloecke (1.211 MiB) geloescht, `--orphans` = 0, `data/`
   8,6 GiB. **Offen:** Schritt 5 (Modelle) nicht vorgelegt.
   `selfplay_v23-b01-seedvalue_*` (600, 25 MiB) steht noch im Baum, weil
   `PREREG_start_position_seeding.md` OFFEN ist -- Nutzer-Rueckfrage 21:45, ob das noetig ist.
4. Die Ketten-Skripte der Generationen v25 und v26 sind Loeschkandidaten nach Schritt 3
   des Ablaufs; `night_v26_chain.sh` bleibt als Muster, bis die v27-Kette gelaufen ist.

### FREIGABEN UND VERBOTE (woertlich vom Nutzer)

- **Kein Push ohne Anweisung.** Ahead-Stand im Chat melden.
- **Loeschung nur auf pfadgenaue Freigabe.**
- **Messungen laufen exklusiv**; GPU und CPU duerfen parallel, zwei CPU-Messungen nicht.
- **Erzeugung startet nur auf Anweisung** -- der Nutzer faehrt sie in der neuen Sitzung
  selbst.

### BEFUNDE, die eine Entscheidung oder Nachschau brauchen

- **sigma/Prior Runde 4 springt auf 8,537** (v25-b01: 3,408), waehrend die Gesamt-Kennzahl
  auf 2,270 faellt. Die Regel haengt an der Gesamtzahl, die Familie bleibt also zu -- aber
  bei der naechsten Promotion nachsehen. n_used 233, eine Runde ist duenn.
- **Der Modell-Snapshot aus `train.py` scheitert reproduzierbar** (0xC0000142, dritter
  Fall). Seit 2026-09-09 raeumt die Funktion vorher auf, wiederholt einmal und legt bei
  Fehlschlag `models/.snapshot_pending_<name>.txt` ab. Ob das reicht, zeigt das
  v27-Training.
- **Die Anker-Kante ist gesaettigt** (127:23 gegen 126:24 zweimal). Als Fortschrittsmass
  taugt sie nicht mehr; als Fixpunkt bleibt sie richtig.

**Prereg-Audit 2026-09-09 abends (alle 13 offenen Preregs, drei Opus-Agenten, tragende
Stellen vom Koordinator am Code nachgeprueft).** Koepfe und Laufzeiten sind berichtigt;
die Befunde stehen je in der Prereg. Was eine ENTSCHEIDUNG braucht, in Reihenfolge:

- ~~Tor 2 fuer v26-b01 nachmessen~~ ENTSCHIEDEN 2026-09-09 (Nutzer: "nicht nachmessen").
  Praezedenz in `docs/generation_loop.md` (Abschnitt Tor 2) festgeschrieben: Tor 2a wird
  ex post am erzeugten Korpus gemessen, die v27-Kette liefert die Zahl fuer v26-b01 als
  Generator (Schritt 1, Bezug 0,737). Tor 2b (Arena gegen Vorgaenger) ist seit v25 nicht
  gemessen; die Anker-Arena zeigt 1,267 gegen 1,307 (kein Tor-Instrument, n = 150).
- **Ausflug-Klasse: 11 % der Ausfluege weichen nicht ab** (`PREREG_start_position_seeding.md`
  par.9k, n = 200 Paare). Fix ist ein Engine-Eingriff; Empfehlung: NACH v27-b01, weil v25-
  und v26-Klassen denselben Defekt tragen und der letzte eingefrorene Arm stationaer bleibt.
  Der Abzweig zur Haelfte in Runde 1 ist KEIN Widerspruch: die Begruendung "Engpass
  Vollendung spaet" in par.9b ist die am 2026-08-23 widerlegte Lesart (Legalitaetsstufe
  0/160, Engpass ist die Zufuehrung), par.9b gehoert berichtigt, nicht par.9g.
- **STATUS Abschnitt 8, erster Punkt ("Der Champion vollendet keine Spalten") ist
  ueberholt** (v26-Generationsbericht Punkt 4: 1,267 volle Spalten je Partie gegen den
  Anker). Beim naechsten Neuschnitt streichen oder auf v26 datieren.
- **Einfrieren ist am Trainings-Seed undicht:** `cli_args.seed` 20260925 / 20260929 /
  20260933 bei sonst identischen Flags (Manifeste v25-b01, v26-b01, Kette v27). Fixieren
  hebt die Konfundierung nicht auf (anderes Material, andere Batches), aber par.18 sagt
  "ausschliesslich Material". Entscheid: so lassen und in par.18 benennen, oder v27 mit
  20260929 fahren.
- **Null-Klammer, Kaufseite ohne Eigentuemer** und Stufe 0 auf der falschen Grundmenge
  (`PREREG_score_clamp_incentive.md` par.9, `PREREG_dome_stack_information_sets.md`
  par.14). Vor Stufe 0 zu klaeren, sonst schliesst die Schwelle den Strang auf Self-Play,
  wo der Effekt strukturell selten ist.
- **Die Oberflaeche zeigt dem Menschen die Rueckgabe-Reihenfolge des Stapels**
  (`game.rs:282-286`, Log im Frontend), die `dome_stack` par.4 als unbekannt modelliert.
  Vor der naechsten Referenzpartie entscheiden: Log kuerzen oder Reihenfolge als bekannt
  modellieren.
- Kleinere Widersprueche, je in der Prereg registriert: `round_transition_search_sampling`
  par.8 (Determinisierung lebt, Paritaetssonde nicht), `round_estimate_leaf_term` (eine
  Skala gegen gemessenes Rundenprofil), `stack_top_feature` par.12 (par.7 ohne
  Verwerf-Ausgang), `start_dome_choice` (Anker-Sperre ueberholt), `policy_surprise_weighting`
  par.11 (Kante b05 gegen b04 nie registriert).

## 2. WAS ALS NAECHSTES LAEUFT: die v26-Erzeugung

**Die drei Befehle stehen fertig in `PREREG_v26_window.md` par.7.** Generator ist `v25-b01`.

| Klasse | `--games` | Identitaeten | Zugwahl | Abweichung | Wurzelrauschen |
| --- | --- | --- | --- | --- | --- |
| Sockel (policy-aktiv) | 4.000 | 4.000 | greedy ab Zug 1 | Weg C im Hauptstrang | an |
| Schwarm a (value-only) | 4.000 | 4.000 | glatte Temperatur, Modus 2 | Weg C im Hauptstrang | an |
| Schwarm b (value-only) | 4.000 | rund 4.000 | greedy ab Zug 1 | Weg B, nur im Ausflug | aus |

**`--games 4000` auch in der dritten Zeile**, anders als in v25: der Ausflug hat eine
eigene `game_id` und zaehlt gegen `--games` (`PREREG_v25_window.md` par.19a). Der
v25-Lauf lieferte mit `--games 2000` nur 2.002 statt 4.000 Identitaeten und musste
aufgefuellt werden. Kosten nach den gemessenen v25-Werten rund 11,1 h
(`docs/measured_runtimes.md`, Abschnitt v25).

**Val-Pool-Regex:** in v25 `^selfplay_v24-b07-`; fuer v26 ist er der einzige offene
Zuschnitt-Punkt (`PREREG_v26_window.md` par.4).

## 3. WAS DIE SPEC JETZT TRAEGT -- und bis wann sie zu ist

`envelope_projection_mode 1`, `envelope_search_c 1,0`, `envelope_flush_w 0,0`,
**`envelope_hull_form 2`**, **`special_row6_w 1,0`**, Profil 1/0,92/0,67/0,33/0.

**Nutzer-Entscheid 2026-09-07: v25 bis v27 wird NICHT am Netz gedreht** -- Architektur,
Trainingsrezept, Value-Ziel-Mischung und Koepfe bleiben fest, nur das Material aendert
sich. Eine flache Arena ist dabei ausdruecklich akzeptiert, Ruecklauf nicht. **Damit ist
auch die Spec geschlossen**, denn ein Fenster ist nur stationaer, wenn die
Erzeugungsregeln stehen (`PREREG_v25_window.md` par.18).

## 3b. DAS PROGRAMM FUER v27 (Nutzer 2026-09-09: "ausreichendes Programm")

**Der v27-Zuschnitt steht seit 2026-09-09 in `PREREG_v27_window.md`** (Nutzer-Auftrag:
"unabhaengig davon kannst schon den v27 zuschnitt machen"). 2.946 Dateien, Seed 20260933,
Val-Pool `^selfplay_v26-`; es ist das erste VOLLSTAENDIG stationaere Fenster und zugleich
das letzte unter dem Einfrieren. **Beide Zuschnitt-Entscheide sind am 2026-09-09 gefallen:**
Generator ist `v26-b01` (par.3, ausdruecklich unabhaengig von Tor 1 -- Generatorwahl und
Promotion sind zwei Entscheidungen), und den G-2-Posten traegt die **temperierte** Haelfte
(par.2; das gemessene Kriterium trennte nicht, entschieden wurde auf der Rolle von G-2).
Offen ist damit nur noch die Erzeugung selbst, rund 8,4 h (30.077 s in den drei v26-Manifesten).

Vier Straenge liegen vor, alle vorregistriert. **Der Kern ist neu und kam aus einer
Partie**, nicht aus der Kampagnenplanung.

| Strang | Prereg | Stand |
| --- | --- | --- |
| **Informationsmengen am Kuppelstapel** -- die Wurzeldeterminisierung unterscheidet unbekannt / Rueckseite bekannt / Platte bekannt, statt den ganzen Stapel zu mischen | `PREREG_dome_stack_information_sets.md` | OFFEN, 2026-09-09 vorregistriert; Variante A (nur Suche) oder B (plus Merkmale) noch offen |
| **Sichtgleichheit, Reststufen** -- laufende Ziehserie, Phasenaufloesung, und ein Netz, das die in v24-b04 gelegten Werte auch NUTZT | `PREREG_stack_top_feature.md` par.7/par.10 | OFFEN, fuer v27 eingeplant (Nutzer 2026-09-08) |
| **Schwarm G-2 ohne Split** -- welche der beiden v24-b07-Haelften den G-2-Posten traegt | `PREREG_v26_window.md` par.6, `PREREG_v27_window.md` par.2 | **GEMESSEN 2026-09-09, Kriterium trennt NICHT** (bedingte Vielfalt saettigt bei beiden). Nutzer-Entscheid noetig; drei Lesarten stehen in par.2 |
| **Null-Klammer** -- bleibt die Anreizstruktur unter null erhalten | `PREREG_score_clamp_incentive.md` | OFFEN, 2026-09-09 aufgemacht; Stufe 0 ist eine Messung und darf frueher laufen |

**Das Werkzeug dahinter steht in `../docs/architecture_reference.md`**, Abschnitt "Wo der
Code Information ABSICHTLICH vernichtet" (Naht-Audit vom 2026-09-09, 24 Mischstellen mit
Urteil, plus die Regel fuer neue Stellen). CLAUDE.md verweist darauf; die drei uebrigen
Suchkanaele stehen in `PREREG_dome_stack_information_sets.md` par.11.

**Der Zeitpunkt ist entschieden (Nutzer 2026-09-09):** *"nach v27 ist das Einfrieren
beendet"*, und praezisiert: *"v27-b01 ist der letzte eingefrorene Arm. dann gehts weiter."*
**Der Ausloeser ist ein ARM, keine Generation.** Sobald `v27-b01` trainiert ist, steht die
Vergleichskette `v25-b01` / `v26-b01` / `v27-b01` -- drei Arme, gleiches Rezept, nur
rotierendes Material -- und der Umbau darf starten, notfalls als `v27-b02` innerhalb
derselben Generation. **In v27-b01 selbst faellt von der Tabelle oben nur die
G-2-Schwarm-Frage**, sie ist eine Material-Entscheidung.

**Vierter Strang, am 2026-09-09 aufgemacht und ebenfalls fuer v27 nach b01 eingetaktet:**
die Null-Klammer, `PREREG_score_clamp_incentive.md`. Bei Punktestand 0 sind Strafen wie
Kaeufe wirkungslos; der Schattenzaehler `score_unclamped` faengt nur das TRAININGSZIEL ab,
waehrend das Netz im Spiel den geklammerten Wert sieht (`features.rs:689`). **Stufe 0 ist
eine reine Messung** (wie oft steht ein Spieler auf 0, wie lange, wie viel Strafe schluckt
die Klammer) und darf frueher laufen, sobald die Maschine frei ist -- mit einer VOR der
Messung festgelegten Schwelle, unter der der Strang als UEBERHOLT geschlossen wird.

## 4. OFFENE NUTZER-ENTSCHEIDE (Stand 2026-09-07, 19:40)

1. **Loeschfreigaben**, pfadgenau: `evaluations/cleanup_proposal_turnover_v25.md`
   (6 Einmal-Skripte), dazu die seit gestern offenen
   `models/attic_20260906_k3p10_copies/` und `venv_measure_hullform/`.
2. **Schritt 4 des Generationswechsels** (Korpora, Bloecke, Monolithe toter Fenster) ist
   NICHT gefahren -- er braucht die v25-Fensterliste und je Gruppe einen
   `restic find`-Beleg. Vorlage folgt, sobald die Erzeugung laeuft.
3. **Eroeffnungsplatzierung und Kuppelstapel**: darf die Eroeffnung blind ziehen? Vom
   Nutzer als eigenes Prereg vertagt; Belege beider Lesarten in
   `docs/domain_knowledge.md`. Bis zur Klaerung ist die Eroeffnung aus allen
   Abzweig-Verteilungen ausgenommen.
4. **Paritaets-Fixture bei reinem Spec-Wechsel**: die Checkliste kennt nur den
   Champion-Wechsel. Fuer b07 wurde sie neu geschrieben und ist gruen -- ob das noetig
   war, ist ungeklaert.
5. **Prereg-Bestand: 11 mit OFFEN im Kopf** (2026-09-09 abends; v25 und v26 auf ENTSCHIEDEN gesetzt), Ziel rund 7.

## 5. OFFENE ENTSCHEIDUNGEN (Nutzer)

| Punkt | Worum es geht |
| --- | --- |
| **b04: welcher Zweig wird breiter** | Flach-Zweig `hidden_size` 512 ist ohne Bau fahrbar; Conv-Zweig `conv_channels` 48 / `conv_layers` 2 braucht zwei Flags, ein Checkpoint-Feld und eine Ableitung beim Laden -- sonst ist der Checkpoint nicht ladbar (`PREREG_capacity_sim_frontier.md` par.10) |
| ~~frozen_v3: woher die Zustaende~~ ERLEDIGT 2026-09-01 | Weg (b) gefahren: 400 frische Sockel-Partien (24,2 min), Satz und zwei Orakel-Label-Saetze gebaut (`PREREG_frozen_v3_eval_set.md` par.7-9). Quelldateien liegen im restic-Backup (`archive_pre_v24/`) |
| ~~Generatorwahl bei Gleichstand der Arme~~ | ENTSCHIEDEN 2026-09-02: dreistufig, Staerke schliesst aus, Spaltenprofil entscheidet, sonst Amtsinhaber (`docs/generation_loop.md`) |
| ~~Loeschfreigaben~~ ERLEDIGT 2026-09-01 | `data/onpolicy_v22-b05/` und `-b06/` auf Nutzer-Freigabe geloescht (je 31 Dateien, 32 + 34 MB). Vorher geprueft: KEINE Fenster- oder Traegerdatei verweist darauf. Die Preregs `heuristic_v2_long_rows` (DAgger-Runden) und `v23_window` zitieren sie im TEXT -- die Herleitungen bleiben lesbar, die Rohpartien sind weg |
| **Messartefakte tracked?** | `evaluations/artifacts/` ist ungetrackt; Preregs zitieren die JSONs als Beleg, ein frischer Klon hat sie nicht. Zurueckdrehen: `.gitignore`-Zeile raus, `git add -f` |
| **Push** | NIE ohne ausdrueckliche Anweisung; der Ahead-Stand wird im CHAT gemeldet, nicht hier gefuehrt |

---

## 6. OFFENE STRAENGE -- abgeglichen mit dem Prereg-Index (2026-08-31, nachgefuehrt 2026-09-01)

Der Index zaehlt (Stand 2026-09-01 abends, aus dem Generator) **20 OFFEN, 77 ENTSCHIEDEN, 8 UEBERHOLT** (`search_depth_column_optimum` ist wieder OFFEN, `frozen_v3_eval_set` und `v23_reachability_recheck` sind ENTSCHIEDEN)****.
Koepfe, die gegen ihren eigenen Koerper standen, sind an drei Tagen berichtigt
worden: am 2026-08-31 `cache_build_time` und `v23_reachability_recheck`, am
2026-09-01 frueh `policy_surprise_weighting`, `cache_build_time` (Hebel 3
hat einen Nutzniesser) und `r5_solver_split`, am 2026-09-01 abends bei der
Pruefung aller geaenderten Preregs `prior_blind_spot` (Kopf behauptete die
widerlegte Erklaerung), `heuristic_v2_long_rows` (Erzeugung "laeuft"),
`v23_window` (Arm-Frage offen), `search_depth_column_optimum` (jetzt OFFEN,
Stufe 4), `capacity_sim_frontier`, `reanalyze_label_depth`,
`policy_surprise_weighting` (Kennzahlen).

**Am laufenden Strang, mit Platz im Fahrplan:**

| Prereg | Wo es haengt |
| --- | --- |
| ~~`v23_window`~~ | ENTSCHIEDEN: Fenster gebaut, alle Tore und alle Arme gemessen |
| `capacity_sim_frontier` | Warm gegen Kalt einfaktoriell belegt (b06, par.14b: 0,18 Spalten, 65:95); b04 wartet auf den Zweig-Entscheid (Abschnitt 5) |
| `policy_surprise_weighting` | wieder OFFEN seit 2026-09-05; Arm v24-b05 gefahren, Belege in `PREREG_v24_window.md` par.9, Kante b05 gegen b04 nie registriert (par.11, Audit 2026-09-09) |
| `reanalyze_label_depth` | ENTSCHIEDEN 2026-09-03 (par.A5): Lehrer-Relabel b05 Nullbefund (par.A3), Reanalyze b07 keine Staerke und weniger Spalten -- b01 bleibt Generator; Teil B ohne Verbraucher bei lambda 1,0 |
| ~~`r5_solver_split`~~ | Teil B war Phase 3 -- GESCHLOSSEN ohne Bau (2026-09-01) |
| ~~`v23_reachability_recheck`~~ | ENTSCHIEDEN 2026-09-01: 14,64 Prozent tot-kartiert gegen 13,89 beim Vorgaenger, Stufe 1 wird NICHT eroeffnet; Quelldateien im restic-Backup |
| ~~`search_depth_column_optimum`~~ | ENTSCHIEDEN 2026-09-02: Stufe 4 komplett (par.6b, par.7); Tiefen-Delle beschrieben, nicht behoben |
| `special_tile_yield` | Kanaele 77/78 gebaut, ihre Wirkung nie isoliert |
| `cache_build_time` | Hebel (3) hat seit 2026-09-01 einen Nutzniesser: **4,98 h** einkerniges Zusammenfuegen bei neuer Fenster-Zusammensetzung (par.11). Die vermisste serielle Vollreferenz liegt damit auch vor |
| `frozen_v3_eval_set` | ENTSCHIEDEN und GEBAUT 2026-09-01 (Satz 1.800 Zustaende, Orakel aus b01 und v21, Zirkularitaet belegt, par.7-9). Nachgetragen: die Bruecke gilt nur fuer Runden 1-4; Quelldateien im restic-Backup; Artefakte ohne `laufzeit`-Block |
| `geometric_envelope` | K3 GEBAUT 2026-09-03 (par.8.2/8.3, Anker und Paritaet GRUEN), Messung nach par.8.4 offen; par.8.6 (Value-Anteil im Tiling, Vorpruefung bestanden) wartet auf den Nutzer |

**Registriert, nicht eingetaktet** (jeder Bau braucht vorher eine
Registrierung): `plate_policy_supervision`, `saturating_score_utility`,
`risk_sensitive_leaf_utility`, `uvfa_plate_regime`,
`uncertainty_guided_selfplay`, `start_position_seeding` (Dosis-Folgearm),
`start_dome_choice` (Stufe 0, Wiedervorlage Generation 2),
`round_transition_search_sampling` (Kostentor zuerst),
`stack_draw_reservation_rule` (Default AUS steht),
`stack_top_feature`, `chance_nodes` (Teil B1/A1 geparkt),
`floor_shaping_scale`, `rust_data_layer` (Registrierung, kein Auftrag).

**OHNE PREREG, nur Merkposten -- und darum beim Index-Abgleich durchgefallen
(berichtigt 2026-08-31):** die Neufassung hat Abschnitt 5 aus dem
Prereg-Index gebaut, und damit faellt per Konstruktion alles heraus, was
offen ist, aber keine Prereg hat. Wieder aufgenommen:

* **Einhuellende / geometrisches Gelaender: seit 2026-08-31 REGISTRIERT**
  als `PREREG_geometric_envelope.md` (Nutzer-Auftrag) -- damit ist der
  Merkposten von 2026-08-24 abgeloest. Steht in Abschnitt 5 oben bei den
  Straengen am laufenden Fahrplan.
* **#31 / #38 / #39**: geparkt, Arbeitskreis "Spaeter", Beschreibungen im
  Archiv.

Wer Abschnitt 5 kuenftig aus dem Index erzeugt, traegt diese Liste HIER
nach -- der Index kennt nur, was eine Datei hat.

**Verschoben, nicht verworfen:** Arm K (Bootstrap-Kohaerenz,
`PREREG_heuristic_v2_long_rows.md` par.3b.3/3b.3a) -- gebaut, Default aus,
ausloeserbasiert. Er korrigiert einen VERSATZ, das gemessene Problem ist eine
STEIGUNG; seine drei benannten Nutzniesser sind ungebaut; und er ist der
einzige Arm, der alle Cache-Bloecke entwertet.

---

## 7. MERKLISTE CODEPFLEGE (Audit 2026-08-27, bewusst verschoben)

**Naechstes Build-Fenster** (brauchen cargo, Paritaets-Gate): sechs Dialekte
fuer "ist dieser Bool-Knopf an?" (Befund 4); drei stille Env-Verschlucker
(13-15); Value-Spread-Pfad verkleinert den Pool still (16); toter Zweitpfad
`board.rs:184-220` mit irrefuehrenden Spaltennamen (19).

**Nach dem v23-Training:** ONNX-Paritaetspruefung nie fertiggebaut (18);
Kanalzahl als Hand-Literal im Fenster-Key (5, NICHT vor dem Training);
viermal dasselbe 95%-KI mit Entartungen (20); sieben Eigenaufloesungen von
`champion.txt`, sechs Tool-Stellen offen plus `dist/mosaic_release.spec:46`
packt eine geloeschte ONNX (21); `MosaicDataset.__init__` mit 998 Zeilen
(22); `offline_diagnosis.py` rechnet ein historisches Value-Ziel (6).

Fundstellen im Audit-Bericht; Details im Archiv-Kapitel.

---

## 8. STRUKTURBEFUNDE, die weitergelten

- **Der Champion vollendet keine Spalten**, und der Grund ist Verteilung,
  nicht Versorgung: eine volle Spalte kostet 21 Zellen, das Netz verbraucht
  42,7 und truege gleichverteilt 2,03 Spalten statt 0,10.
- **Die Dreiecksform ist die MACHBARKEITSHUELLE**, keine aesthetische Wahl:
  erlaubt ist `r + c <= 5`, also dieselben 21 Zellen.
- **Eine volle Rasterzeile ist ohne Spezialfliese unmoeglich** -- sie wird nur
  von ihrer Musterreihe gespeist, und die schliesst hoechstens einmal je Runde
  ab. Spalten haben das Problem nicht.
- **Der Durchbruch kam vom DRAFTING, nicht vom Routing** (Split-Test, je 160
  gepaarte Partien): Huelle nur im Drafting 0,756 gegen 0,044 (t 10,29),
  Huelle nur im Routing 0,113 gegen 0,113. Die Luecke zur Summe ist eine
  Wechselwirkung -- das Routing kann nur einsortieren, was das Drafting geholt
  hat.
- **Erste unkontaminierte Referenz:** Mensch-gegen-Netz in `static/log/` --
  der Mensch schliesst 1,80 volle Spalten je Partie gegen 0,10 des Netzes,
  bei GLEICHEN Platzierungspunkten. Der Vorsprung sitzt bei den
  Spezialfliesen; der Mensch tauscht kurze Reihen gegen lange.
- **Chip-Allokation, nicht Chip-Volumen:** Mensch 0,8 Reihe-6-Chip-
  Abschluesse je Partie, v21 0,1. Kosten-gewichtete Huelle Mensch 0,86,
  Lehrer 0,68 (berichtigt 2026-09-03: die zweite Huelle war falsch
  gespiegelt, `heuristic_v2_long_rows` par.3b.14); Netz-Werte 0,54-0,62
  stammen noch aus der falschen Rechnung und sind vermutlich zu niedrig.
- **Blindzieh-Regel:** bei Wertungsplatte 6 laeuft die gebaute Stopp-Regel das
  Punktekonto leer (58-66 Prozent der Serien enden bei 0). Spaltenbau behebt
  das NICHT -- k1 zahlt quadratisch, das Spezialfeld-Defizit kostet linear -3
  je Feld.
- **Eine Herleitung aus dem Code ist eine Hypothese, kein Befund.** Am
  2026-08-25 lagen vier davon im Vorzeichen falsch.
