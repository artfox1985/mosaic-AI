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

## 1. UEBERGABE an die naechste Sitzung (2026-09-08, 23:50)

**MASCHINE FREI, nichts laeuft.** Baum sauber, **6 Commits vor origin, NICHT gepusht**
(Push nur auf Nutzer-Anweisung). Champion laut `models/champion.txt`: `v25-b01_brierbest`.

**Die Promotion v25-b01 ist VOLLSTAENDIG durch** -- alle sechs Schritte der Checkliste plus
das eingefrorene Artefakt. Was bleibt, steht unter "Erste Aufgabe".

### v25-b01 schlaegt den Champion -- die Beleglage

| Kante | Ergebnis | Bemerkung |
| --- | --- | --- |
| Gating gegen v24-b07, Seed 20261020 | 53:27 | SPRT nach 40 Paaren, p 0,0049 |
| Gating, Replikation Seed 20261021 | 129:91 | SPRT nach 110 Paaren, p 0,0145 |
| **gepoolt** | **182:118 = 0,607** | **p 0,0003**, KI [0,551; 0,662], n = 300 |
| Anker (festes n=150) | 126:24 | identisch zu v24-b07 |
| Champion-2 gegen v24-b06 | 48:22 | SPRT nach 35 Paaren |

Alle vier Zeilen stehen in `evaluations/elo_history.csv`. **Beide Gating-Seeds sind
einzeln signifikant** -- bessere Lage als bei K3-P, wo der Fruehstopp in der Replikation
zusammenfiel.

### ERSTE AUFGABE DER NEUEN SITZUNG (in dieser Reihenfolge)

1. **Champion-2-Kanten ueber das ARTEFAKT nachmessen** (der Methodenfehler unten).
   Betrifft `v25-b01` gegen `frozen_champions/v24-b06/` und `v24-b07` gegen
   `frozen_champions/v23-b01_k3p10/`. Weg: `tools/frozen_referee_match.py` bzw. das
   Artefakt-venv, NICHT die lebenden `models/alphazero_*`-Dateien. Abnahme: neue Zeile in
   `elo_history.csv` mit Vermerk, dass sie die alte ersetzt. Kosten je Kante rund 30 min.
   **ACHTUNG:** der Nutzer loescht `frozen_champions/v24-b06/` -- vorher fragen oder aus
   restic-Stand `b6842b4e` zurueckholen (`restic restore b6842b4e --target . --include
   "*/frozen_champions/v24-b06/*"`, alle sieben Teile geprueft vorhanden).
2. **Generationsbericht v25 nach `archive/history.md`** (Muster: der v24-Bericht am Ende
   der Datei). Elo-Zahl von v25-b01 vorher aus `tools/elo_tracker.py report` holen und ins
   Artefakt-Manifest nachtragen (Feld `elo.value` steht auf `null`).
3. **restic-Stand fuer v25-b01 nachholen** -- der Modell-Snapshot des Trainings ist mit
   Exitcode 0xC0000142 gescheitert.
4. **`/mosaic-generation-turnover`** vor der v26-Erzeugung, NICHT von Hand. Schritt 4
   (tote Korpora, Bloecke, Monolithe) wurde vor v25 uebersprungen und ist jetzt faellig.
5. **v26 erzeugen**: drei Befehle in `PREREG_v26_window.md` par.7, Generator `v25-b01`.
   **NUR auf ausdrueckliche Nutzer-Freigabe starten.**

### FREIGABEN UND VERBOTE (woertlich vom Nutzer)

- **Kein Push ohne Anweisung.** Ahead-Stand im Chat melden.
- **Loeschung nur auf pfadgenaue Freigabe**, auch bei "offensichtlichem" Muell.
- **Messungen laufen exklusiv**; GPU und CPU duerfen parallel, zwei CPU-Messungen nicht.
- **Erzeugung startet nur auf Anweisung.**
- Offene Loeschfreigaben: `evaluations/cleanup_proposal_turnover_v25.md` (6 Skripte),
  `models/attic_20260906_k3p10_copies/`, `venv_measure_hullform/`.

### WAS NOCH ZU TUN IST (mechanisch, keine Entscheidung noetig)

1. ~~Anzeige-Kalibrierung~~ **ERLEDIGT 22:45**: `server.py:1611/1612` traegt jetzt
   A **-0,0814** / B **0,6386** aus `platt_fit_v25-b01_v3.json` (Brier 0,2268 auf
   frozen_v3, b06 hatte 0,23221). Der Fit auf `frozen_eval_set.pkl` (A 0,3433 / B 0,6538 /
   Brier 0,24634) ist die TRENDmetrik und gehoert NICHT in die Anzeige -- er steht in
   `platt_fit_v25-b01.json` und im Artefakt-Manifest.
2. **Eingefrorenes Artefakt** `models/frozen_champions/v25-b01/` nach dem Muster von
   `v24-b07/`: model.onnx, model.pth, spec.json (= `v24-b07_brierbest.spec.json`, die Spec
   ist bis v27 eingefroren), das aktuelle Wheel plus `wheel.sha256`, `manifest.json`,
   Golden Probe (`tools/build_frozen_golden_probe.py --artifact-dir ... --seed-base 916001`,
   rund 16 min), venv aus dem Wheel, dann `tools/frozen_referee_match.py ... --n-games 2`.
3. **STATUS-Champion-Zeile und `archive/history.md`** nachziehen (Generationsbericht v25).
4. **Elo-Bericht lesen** und auf `NICHT mit Anker verbunden` pruefen.

### BEFUNDE, die eine Entscheidung brauchen

- **METHODENFEHLER bei der Champion-2-Kante, zweimal** (Nutzer 2026-09-08): sie wurde gegen
  die LEBENDEN Modelldateien gemessen statt gegen das eingefrorene Artefakt -- bei v25-b01
  gegen `models/alphazero_v24-b06_brierbest.onnx` (48:22) und bei v24-b07 gegen
  `models/alphazero_v23-b01_brierbest.onnx` (92:58). Damit lief der heutige Motor auf beiden
  Seiten. **Genau dafuer wird der Alt-Champion mit eigenem Wheel eingefroren:** damit er
  spielt wie zu der Zeit, aus der seine Elo-Zahl stammt. Beide Kanten sind nachzumessen,
  ueber den Artefakt-Pfad (`tools/frozen_referee_match.py` bzw. das Artefakt-venv). Bis
  dahin tragen sie weniger, als ihre Zahl suggeriert. **Die uebrigen Kanten sind nicht
  betroffen** -- Gating misst zwei aktuelle Netze gegeneinander, die Anker-Kante laeuft
  ohnehin ueber das Anker-Artefakt.
- **Lebende Modelldateien werden regelmaessig archiviert** (Nutzer): `alphazero_v24-b06*`
  wird nicht mehr gebraucht, das Artefakt `frozen_champions/v24-b06/` loescht der Nutzer.
  Was bleibt, ist die Artefakt-Kopie im restic-Stand b6842b4e (alle sieben Teile geprueft).

- **sigma/Prior-Balance steigt: 2,792** (b06: 2,603). Unter der Schwelle 3, die Regler-
  Familie bleibt also zu -- **aber Runde 4 liegt einzeln bei 3,408**. Artefakt
  `gumbel_scale_calibration_v25-b01.json`. Beim naechsten Champion wieder pruefen; bei
  Ueberschreiten oeffnet sich `c_visit`/`c_scale` per Regel, ohne Ermessen.
- **v25-b01 hat KEINEN eigenen restic-Stand**: der Modell-Snapshot des Trainings ist mit
  Exitcode 0xC0000142 (DLL-Init) fehlgeschlagen. Nachholen.
- **Loeschfreigaben stehen aus**: `evaluations/cleanup_proposal_turnover_v25.md`
  (6 Einmal-Skripte), `models/attic_20260906_k3p10_copies/`, `venv_measure_hullform/`.
- **Schritt 4 des Generationswechsels** (tote Korpora, Bloecke, Monolithe) wurde vor v25
  bewusst uebersprungen und ist vor v26 faellig.

### DER NAECHSTE GROSSE SCHRITT: v26

**Zuschnitt steht fertig in `PREREG_v26_window.md`**, Befehle in par.7 (Generator
`v25-b01`, drei Klassen, `--games 4000` auch fuer die Ausflug-Haelfte). **Vorher
`/mosaic-generation-turnover`**, nicht von Hand.

**Der Rahmen, der alles bindet** (`PREREG_v25_window.md` par.18): v25 bis v27 wird NICHT
am Netz gedreht, nur das Material aendert sich; die Spec ist zu. Eine flache Arena waere
akzeptiert, Ruecklauf nicht.

### WAS IN DIESER SITZUNG GEBAUT WURDE (Kurzfassung)

Huellenform 2 und K5 in die Spec (als eigene Entitaet `v24-b07`, nicht durch Mutation von
b06); Weg B mit erzwungener Einzelabweichung statt gesampelter Phase; Weg C auf die
gemessene Ziehungsregel; aktionsabhaengige Temperatur als Modus 0/1/2; Dubletten-Waechter
fuer Ausfluege; zwei unbegruendete Konstanten ersatzlos entfernt (109 Knoepfe -> 107).
Zwei neue Regeln in CLAUDE.md: Rueckwaerts-Pruefung beim Registrieren, und Regel 0
Zusatz 2 (n, Grundmenge, Einheit gegen die des Verbrauchers).

## 2. WAS ALS NAECHSTES LAEUFT: die v25-Erzeugung

**Die drei Befehle stehen fertig in `PREREG_v25_window.md` par.19.** Generator ist b07.

| Klasse | Partien | Identitaeten | Zugwahl | Abweichung | Wurzelrauschen |
| --- | --- | --- | --- | --- | --- |
| Sockel (policy-aktiv) | 4.000 | 4.000 | greedy ab Zug 1 | Weg C im Hauptstrang | an |
| Schwarm a (value-only) | 4.000 | 4.000 | glatte Temperatur, Modus 2 | Weg C im Hauptstrang | an |
| Schwarm b (value-only) | 2.000 | 4.000 | greedy ab Zug 1 | Weg B, nur im Ausflug | aus |

**`--games 2000` in der dritten Zeile ist kein Tippfehler:** ein Ausflug kommt ZUSAETZLICH
zur Hauptpartie. Hergeleitete Kosten rund 11,4 h, nacheinander auf einer Maschine.

**Val-Pool-Regex wandert** von `^selfplay_v24-b06-` auf `^selfplay_v24-b07-`.

## 3. WAS DIE SPEC JETZT TRAEGT -- und bis wann sie zu ist

`envelope_projection_mode 1`, `envelope_search_c 1,0`, `envelope_flush_w 0,0`,
**`envelope_hull_form 2`**, **`special_row6_w 1,0`**, Profil 1/0,92/0,67/0,33/0.

**Nutzer-Entscheid 2026-09-07: v25 bis v27 wird NICHT am Netz gedreht** -- Architektur,
Trainingsrezept, Value-Ziel-Mischung und Koepfe bleiben fest, nur das Material aendert
sich. Eine flache Arena ist dabei ausdruecklich akzeptiert, Ruecklauf nicht. **Damit ist
auch die Spec geschlossen**, denn ein Fenster ist nur stationaer, wenn die
Erzeugungsregeln stehen (`PREREG_v25_window.md` par.18).

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
5. **Prereg-Bestand: 13 mit OFFEN im Kopf**, Ziel rund 7.

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
| ~~`policy_surprise_weighting`~~ | ENTSCHIEDEN 2026-09-01: b03 traegt nicht (Orakel Gleichstand, Arena 75:85) |
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
