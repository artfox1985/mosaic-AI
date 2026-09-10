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

## 1. UEBERGABE an die naechste Sitzung (2026-09-10, 15:30)

**MASCHINE FREI, nichts laeuft.** Champion laut `models/champion.txt`: **`v27-b01_brierbest`,
Elo 1405** [1361, 1453] aus 790 Partien. Leiter: `v26-b01` 1364, `v25-b01` 1336, `v24-b07`
1283, Anker fix 1000. **Die Promotion v27-b01 ist VOLLSTAENDIG durch** (alle Schritte der
`docs/promotion_checklist.md`, Artefakt `models/frozen_champions/v27-b01/`, restic
`run:v27-b01` 2a12d266). Generationsbericht v27 am Ende von `../archive/history.md`; Belege
`PREREG_v27_window.md` par.7 bis par.10.

**Das Einfrieren ist beendet.** v25-b01 / v26-b01 / v27-b01 sind die Vergleichskette mit
gleichem Rezept und rotierendem Material; dreimal Tor 1, dreimal steigende Spalten (Tabelle im
Generationsbericht). Ab jetzt duerfen Netz, Rezept und Spec wieder angefasst werden.

### NAECHSTE SCHRITTE, nur auf Anweisung (Nutzer 2026-09-10, 13:25: v28-Self-Play ausgesetzt)

1. **Nach-v27-Programm LAEUFT seit 15:35 (Nutzer):** Dubletten-Fix GEBAUT (Seeding-Prereg
   ENTSCHIEDEN), Null-Klammer Stufe 0 GEMESSEN (Schwelle nicht unterschritten, Kaufseite traegt,
   `score_clamp` par.10), Kuppelstapel Variante A GEBAUT und GEMESSEN (`dome_stack`
   par.15-15c: A/B 165:135 ohne Ruecklauf, Fix bleibt; PRE/POST exakt: Wissen allein bewegt
   die Ziehungen kaum, Erwartung aus par.8 an der Referenzpartie nicht eingetreten). Live-Wheel
   seit 18:00 mit Variante A, Dubletten-Fix, exaktem Orakel-Pfad und Knopf
   `MOSAIC_DOME_POOL_KNOWLEDGE`. **Naechste Schritte des Programms:** Diagnostik "Ziehung in
   eigenen bekannten Block" ueber Mensch-Logs und Self-Play (Werkzeug fehlt), dann Variante B
   (Merkmale), Stufe 1 der Null-Klammer an der Ziehung, Sicht-Reststufen (`stack_top`).
2. **Claude-Partien** (`PREREG_claude_play_interface.md` par.9): Engine, Replayer und
   `claude_play.py` sind umgebaut und gebaut, Alt-Logs replayen; offen ist nur ein Rauchtest
   von `claude_play.py new/move/show` mit `.engine.log`. Gegner ist `models/champion.txt`.
   Der Partien-Agent liest NUR `show` und `game.log`.
3. ~~Werkzeug `plate_points_from_arena.py`~~ ERLEDIGT 16:20: wertet mit `side_names` je
   Modell aus, gepaarte Differenzen je Kriterium; Befund fuer v27-b01: Zuwachs bei vertikalen
   Reihen (+1,34) und Eckplatten (+0,97), nicht bei Spezialfeldern (`PREREG_v27_window.md`
   par.10). Offen im Werkzeug: KI auf Paar- statt Block-Ebene.
4. **Generationswechsel-Rest:** Schritt 5 (Modell-Liste zur Ruecksprache), `night_v26_chain.sh`
   und die v27-Skripte werden Loeschkandidaten, sobald v28 ansteht.
5. **Entscheid Trainings-Seed** fuer die Zeit nach dem Einfrieren (wanderte 20260925/29/33).

### FREIGABEN UND VERBOTE (woertlich vom Nutzer)

- **Kein Push ohne Anweisung.** Ahead-Stand im Chat melden.
- **Loeschung nur auf pfadgenaue Freigabe.**
- **Messungen laufen exklusiv**; GPU und CPU duerfen parallel, zwei CPU-Messungen nicht.
- **v28-Self-Play ausgesetzt** (2026-09-10, 13:25).

### BEFUNDE, die eine Entscheidung oder Nachschau brauchen

- **`player_profiles.json` ist im Arbeitsbaum veraendert** (plus `player_profiles.json.bak`),
  nicht durch diese Sitzung; nicht committet. Nutzer fragen, woher.
- **Erzeugung 23 % langsamer als v26** bei gleicher Konfiguration (10,25 h gegen 8,35 h;
  `measured_runtimes.md` v27). Ursache nicht gemessen (Waechter-Last, OneDrive).
- **Einfrieren am Trainings-Seed undicht** (20260925/29/33); fuer die Kette folgenlos, aber
  par.18 sagt "ausschliesslich Material".
- **Null-Klammer, Kaufseite ohne Eigentuemer**; Stufe 0 auf der falschen Grundmenge
  (`score_clamp` par.9, `dome_stack` par.14).
- Kleinere Widersprueche, je in der Prereg registriert (Audit 2026-09-09):
  `round_transition_search_sampling` par.8, `round_estimate_leaf_term`, `stack_top_feature`
  par.12, `start_dome_choice` Nachtrag, `policy_surprise_weighting` par.11.

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
