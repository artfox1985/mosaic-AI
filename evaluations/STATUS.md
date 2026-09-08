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

## 1. STAND (2026-09-09, Generationswechsel v25 -> v26)

**MASCHINE FREI, nichts laeuft.** Baum sauber, **Commits vor origin nicht gepusht**
(Push nur auf Nutzer-Anweisung; Zahl im Chat gemeldet). Champion laut
`models/champion.txt`: `v25-b01_brierbest`, **Elo 1376** [1333, 1425] aus 520 Partien.

**Die Generation v25 ist abgeschlossen und berichtet.** Der vollstaendige
Generationsbericht (Beleglage, Fenster, Trainingszahlen, die zwei Koordinator-Fehler)
steht am Ende von `../archive/history.md`; die Uebergabe vom 2026-09-08, die hier stand,
ist damit abgeloest. Alle vier Punkte, die sie offen liess, sind erledigt: Bericht und
Elo-Zahl (auch im Artefakt-Manifest), restic-Stand `028989fb` (`run:v25-b01`),
Anzeige-Kalibrierung, eingefrorenes Artefakt.

**Nutzer-Entscheid 2026-09-08:** die zwei Champion-2-Kanten, die gegen die LEBENDEN
Modelldateien statt gegen die eingefrorenen Artefakte gemessen wurden (`v25-b01` 48:22
gegen `v24-b06`, `v24-b07` 92:58 gegen `v23-b01_k3p10`), werden NICHT nachgemessen --
"extra Fleissarbeit mit geringem Nutzen". Sie bleiben mit dieser Einschraenkung in
`elo_history.csv`; wer sich auf sie beruft, nennt sie mit. Nicht neu vorschlagen.

### Was der Generationswechsel gebracht hat (Ablauf `/mosaic-generation-turnover`)

- **Schritt 0-2 erledigt:** Maschine frei (Prozessliste, nicht Task-Meldungen),
  Tages-Snapshot **6dd4d988** (7.725 Dateien / 9,279 GiB, `check` ohne Fehler),
  Modell-Snapshot **028989fb**.
- **Schritt 1 war schon getan:** der Generator fuer v26 ist `v25-b01`, und der liegt
  eingefroren unter `models/frozen_champions/v25-b01/` (Wheel, Spec, Golden Probe).
- **Schritt 3-5 AUSGEFUEHRT** (Nutzer-Freigabe 2026-09-09 fuer alle Gruppen des
  Vorschlags `cleanup_proposal_turnover_v26.md`): **11.154 MiB frei**, `data/` von 19,69
  auf 9,12 GiB. Weg sind die Messkorpora der v24-Arme, der hv2-Korpus, die zwoelf
  Monolithe, die Modell-Arme `v24-b01` bis `b05` und 7.553 Waisen-Bloecke.
  Gegenprobe: **0 Waisen** bei 6.402 Bloecken.
- **Folge fuers naechste Mal:** `tools/probes/bootstrap_coherence_probe.py` und
  `action_count_profile_probe.py` finden ihre hv2-Vorgabedateien nicht mehr und brauchen
  `--file` bzw. eine andere Gruppe. Der Korpus liegt im Snapshot `6dd4d988`.
- **Der Monolith des v25-Fensters ist mit weg** (Schluessel 976b1ef66843 u.a.). Ein
  erneutes Training auf `window_v25.txt` muesste ihn neu bauen; die Korpusdateien des
  v25-Fensters sind alle noch da.

### ERSTE AUFGABE DER NEUEN SITZUNG

1. **Loeschfreigaben einholen** zu `evaluations/cleanup_proposal_turnover_v26.md`
   (Gruppen A bis E), dann loeschen und `cache_inventory.py --orphans` nachziehen.
2. **v26-Kette schreiben** nach dem Muster `tools/night_v25_chain.sh`, mit gehaerteter
   Wartebedingung und `--resume`-Hinweis; Chronik `night_run_<Datum>.md` anlegen.
3. **v26 erzeugen**: drei Befehle in `PREREG_v26_window.md` par.7, Generator `v25-b01`,
   rund 11,1 h. **NUR auf ausdrueckliche Nutzer-Freigabe starten.**
4. Vor dem Start: `MOSAIC_DATA_EXCLUDE` pinnen (Fenster-Pinning), Val-Pool-Regex in
   par.4 der v26-Prereg entscheiden -- das ist der einzige offene Zuschnitt-Punkt.

### FREIGABEN UND VERBOTE (woertlich vom Nutzer)

- **Kein Push ohne Anweisung.** Ahead-Stand im Chat melden.
- **Loeschung nur auf pfadgenaue Freigabe**, auch bei "offensichtlichem" Muell.
- **Messungen laufen exklusiv**; GPU und CPU duerfen parallel, zwei CPU-Messungen nicht.
- **Erzeugung startet nur auf Anweisung.**

### BEFUNDE, die weiter gelten

- **sigma/Prior-Balance 2,792** (v24-b06: 2,603), Schwelle 3 nicht gerissen, die
  Regler-Familie bleibt zu -- **aber Runde 4 liegt einzeln bei 3,408**
  (`artifacts/gumbel_scale_calibration_v25-b01.json`). Beim naechsten Champion wieder
  pruefen; bei Ueberschreiten oeffnet sich `c_visit`/`c_scale` per Regel, ohne Ermessen.
- **Die Anker-Kante steht still:** v25-b01 126:24, exakt wie v24-b07. Als Fixpunkt bleibt
  der Anker richtig, als Fortschrittsmass ist er gesaettigt.
- **Lebende Modelldateien werden regelmaessig archiviert** (Nutzer): `alphazero_v24-b06*`
  wird nicht mehr gebraucht; das Artefakt `frozen_champions/v24-b06/` loescht der Nutzer.
  Was bleibt, ist die Artefakt-Kopie im restic-Stand `b6842b4e`.

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
