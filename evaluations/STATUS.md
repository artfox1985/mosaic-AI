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

## 1. WAS GERADE LAEUFT (Stand 2026-08-31, 03:07)

**Erzeugung des v23-Fensterkorpus, Generator `v22-b05`, seit 2026-08-30
19:25.** Eine Hintergrund-Shell faehrt alle drei Klassen mit `&&`
hintereinander (`MOSAIC_STACK_DRAW_RESEARCH=1` exportiert, Abschluss-Echo
"ERZEUGUNG KOMPLETT"):

| Klasse | Ziel | Stand | Konfiguration |
| --- | --- | --- | --- |
| `v22-b05-value-argmax` | 6.000 | **fertig (6.000)** | 100 Sims, `--value-only --no-root-noise --deterministic`, Seed 20260902 |
| `v22-b05-value-sampled` | 2.000 | **1.540** | 100 Sims, `--value-only`, Seed 20260903 |
| `v22-b05-policy` | 4.000 | 0 | 100 Sims, voll gesampelt, Seed 20260901 |

Gemessenes Tempo: 3,45 s je Partie ohne Cache-Co-Bau, 3,6 s mit.

**Cache-Co-Bau laeuft mit** (`build_cache_incremental.py --encoder 2d
--value-target-variant nortv --workers 2 --watch --wartezeit 60
--leerlauf-abbruch 60`): 2.776 Bloecke liegen. Einstellungen decken sich mit
`manifest_train_v22-b05` (2d, nortv, conjunction_head false), die Bloecke
treffen also das geplante Training.

**Wenn der Lauf abgebrochen ist** -- fehlende Partien am g-Suffix ZAEHLEN,
nicht hochrechnen:

```
export MOSAIC_STACK_DRAW_RESEARCH=1
python -u self_play.py --mode network --model models/alphazero_v22-b05.onnx --games 6000 --sims 100 --value-only --version v22-b05-value-argmax --threads 11 --chunk 10 --seed 20260902 --per-file 20 --no-root-noise --deterministic
python -u self_play.py --mode network --model models/alphazero_v22-b05.onnx --games 2000 --sims 100 --value-only --version v22-b05-value-sampled --threads 11 --chunk 10 --seed 20260903 --per-file 20
python -u self_play.py --mode network --model models/alphazero_v22-b05.onnx --games 4000 --sims 100 --version v22-b05-policy --threads 11 --chunk 10 --seed 20260901 --per-file 20
```

`data/` enthaelt sonst nur noch `selfplay_hv2_*` (2.400 Dateien, Fenster);
die Messkorpora sind geloescht (Nutzer-Freigaben 2026-08-30, zuletzt die 60
`selfplay_v21depth*`).

---

## 2. WAS ALS NAECHSTES ZU TUN IST

### 2.1 Sofort nach dem Lauf: Tor 0 (bindend, exklusiv)

```
python -u tools/probes/corpus_column_outcome_symmetry_probe.py --pattern "selfplay_v22-b05-value-*.pkl" --out evaluations/artifacts/corpus_symmetry_v22b05_value.json
python -X utf8 -u tools/corpus_sanity_check.py data --pattern "selfplay_v22-b05-value-*.pkl" --out evaluations/artifacts/corpus_sanity_v22b05_value.json
python -X utf8 -u tools/corpus_sanity_check.py data --pattern "selfplay_v22-b05-policy_*.pkl" --out evaluations/artifacts/corpus_sanity_v22b05_policy.json
```

Lesart vorab (`PREREG_heuristic_v2_long_rows.md` par.3b.12): **primaer**
Symmetrie-Trennung auf der VALUE-Klasse signifikant > 0; **sekundaer**
>= 1.500 Seiten mit voller Spalte (`sides_with_full_column`); Spaltenrate
beider Klassen nur Bericht (Referenz: argmax 0,3375, gesampelt 0,07-0,11,
Champion 0,102). Reisst Tor 0: kein Training, Vorlage.

**Beide Befehlszeilen sind am 2026-08-31 smoke-geprueft** (je zwei bis drei
Sekunden auf einem Kern, Ausgabe in den Scratchpad): die erweiterte
`corpus_sanity_check`-CLI filtert wie gewollt (`--pattern` auf eine Datei:
20 Partien, 40 Seiten), schreibt `pattern` und den `laufzeit`-Block ins
Artefakt, die Bestandsfelder bleiben, und `sides_with_full_column` zaehlt
(14 von 40). Die Symmetrie-Sonde nimmt `--pattern` und `--out` in der hier
notierten Form an. Ein Tippfehler kann den Waechter-Lauf also nicht mehr
aufhalten.

**Beifang aus dem Smoke, ausdruecklich KEIN Torbefund:** auf zwei Dateien
der argmax-Klasse (40 Partien) trennt der Spaltenbau den Ausgang bereits
deutlich (+0,50, t 3,48 auf zwei Bloecken). Das ist ein Hinweis, kein
Verdikt -- der Waechter laeuft auf der ganzen Value-Klasse, und zwei Bloecke
tragen keine Aussage.

### 2.2 Fensterbau

* **hv2-Auswahl GEZOGEN 2026-08-31** (Nutzer: "such dir per seed zufaellig
  welche aus"): 1.745 von 2.400 Dateien, Seed **20260920**, Liste in
  `data/window_v23_hv2.txt`. Regel des Werkzeugs ist seed-zufaellig mit
  zeitlicher Streuung; bei 1.745 aus 2.400 sind die Straten 1-2 Dateien
  breit, also praktisch gleichverteilt. Wiederholungslauf byte-gleich. Die
  Zahlen gehen glatt auf: 1.745 x 10 = 17.450 Partien, 655 Dateien
  = 6.550 rotieren aus.
* **Traeger-Manifest ja/nein** -- offener Nutzer-Entscheid, Abschnitt 4. Wenn
  JA: **die Policy-Klasse MUSS ausdruecklich mitgelistet werden** (180 hv2 +
  200 b05-policy = 380 Eintraege) oder das Manifest traegt
  `carrier_prefixes: ["selfplay_v22-b05-policy_"]`. Sonst setzt es `pol_w=0`
  fuer den GESAMTEN neuen Korpus: der v20-Kurzschluss deckt nur
  `selfplay_v19wdl`/`selfplay_v20wdl` (neural_net.py:796), und der Generator
  schreibt `carrier_prefixes` bewusst nicht. Gegenprobe vor dem Training:
  `policy_carriers.traeger_dateien_je_praefix` im Trainingsmanifest.
* **Relabeling laeuft auf einer KOPIE mit eigenem Praefix**
  (Nutzer-Entscheid 2026-08-31, `PREREG_reanalyze_label_depth.md` par.4b):
  `data/relabeled_v23/selfplay_v22-b05relab-<klasse>_*`. Der Unterordner
  allein reicht NICHT -- der Datei-Cache-Schluessel haengt am Basename, nicht
  am Pfad (file_cache_key.py:81), die Kopie traefe sonst den Block des
  Originals. Kopiert wird nur der neue Korpus (rund 600 Dateien, 1,4 GB),
  nicht hv2. Folge: roh und relabelt liegen auf denselben Partien nebeneinander
  -- das Relabeling wird ein gepaarter Arm statt einer Reihenfolge-Frage.
* Monolith gegen Val-Split: `train.py --cache-file` prueft den
  FENSTER-Schluessel; ein Lauf mit `--val-frac > 0` bildet einen anderen
  Schluessel, der Waechter lehnt korrekt ab.

### 2.3 Der v23-Zyklus (Arme vorab benannt, `docs/generation_naming.md`)

| Arm | Was | Stand |
| --- | --- | --- |
| `v23-b01` | Warmstart aus den Self-Plays | offen |
| `v23-b02` | **Kaltstart**, Bestands-Rumpfbreite -- oeffnet das Rumpfbreiten-Fenster, ein Faktor gegen b01 | offen |
| `v23-b03` | Ueberraschungs-Gewichtung (`PREREG_policy_surprise_weighting.md`) | ungebaut, baubar waehrend b01/b02 rechnen |
| `v23-b04` | Kaltstart mit anderer Rumpfbreite (`PREREG_capacity_sim_frontier.md` par.10) | vorregistriert; Zweig-Entscheid offen |

Fuer alle Arme gilt: **`--moon-loss-weight 0`** (Flag existiert,
train.py:2460), Encoder 2d, `nortv`, `wdl`, `ownership_head_2d`,
**Endgame-Kopf AN** (Nutzer-Entscheid 2026-08-31) -- und **ohne Arm K**,
damit die vorhandenen Bloecke gueltig bleiben.

**Zum Endgame-Kopf, mit berichtigter Zahl:** er ist seit 2026-08-08
Standard-Rezept, und mit diesem Korpus bekommt er zum ersten Mal ein Ziel
(root_q: 2.332 von 3.538 Records einer b05-Datei, davon 314 R5-Drafting; auf
hv2 war die Maske komplett 0). Sein damaliger Beitrag zur R5-Steigung war
**+0,108 gegenueber dem Champion** (0,349 -> 0,457, rund 2 Seed-Sigma), die
vorregistrierte 0,5-Schwelle wurde KNAPP VERFEHLT und die **Arena war H0
(97:103)**; der Verlauf 0,086 -> 0,457 geht ueber mehrere Generationen, nicht
auf sein Konto (PREREG_plate_intervention par.79-102). Er bleibt an, weil er
Standard ist und offline genau die Groesse bewegt, gegen die Phase 3 antritt
-- nicht, weil er Staerke belegt haette. Kaltstart
kostet mit vorgebautem Cache rund 2,5 h (v22-b02 2,56 h, b04 2,52 h).

**Was ausser Arm K sonst noch ALLE Bloecke entwertet** und darum in b01-b04
unangetastet bleibt: Traeger-Manifest, `MOSAIC_IGNORE_POLICY_TARGET_VALID`,
`TD_LAMBDA` (Arm L), `value_target_variant`, `MOSAIC_CACHE_F32`,
`MOSAIC_CACHE_NOPACK`.

### 2.4 Tore und Messkette danach

Verfahren: `../docs/generation_loop.md`. Fuer diesen Durchlauf ist der Bezug
beider Tore **v22-b05** (volle Spalten 0,3375 am argmax-Instrument, Punkte
37,16, Elo 1084); die Champion-Kante (Schritt 7 der Schleife) geht gegen
`v21_2d_brierbest` (1215) und wird gemessen und berichtet, auch wenn keine
Promotion folgt.

**ELO-EINSCHAETZUNG FUER b01: drei Kanten (Nutzer-Auftrag 2026-08-31).**
Nicht eine Messung, sondern der Kader aus der Promotions-Checkliste -- eine
einzelne Kante traegt keine Schaetzung (v21 lag nach dem Gating bei +-90
Punkten CI):

| Kante | Gegner | Zuschnitt |
| --- | --- | --- |
| **Anker** | `Heuristik_hv1_anchor`@150 | festes **n=150 ohne Fruehstopp**, exklusiv, Knoepfe aus dessen `spec.json` (`elo_tracker --knobs`) |
| **Champion** | `v21_2d_brierbest`@400 | n=400 ohne Fruehstopp (Muster der Nachbar-Kanten in elo_history.csv) |
| **Vorgaenger** | `v22-b05`@400 | `tools/paired_gating.py`, Blockgroesse 5 -- **das ist zugleich Tor 1 der Schleife**; Fruehstopp unter 150 Paaren bleibt informativ, fuer eine Promotion braucht es n >= 150 oder eine Replikation |

Alle drei mit b01 auf **400 Sims**: die Leiter ist auf diesen Betriebspunkt
geeicht. Dass die ERZEUGUNG mit 100 Sims laeuft, aendert daran nichts --
Messen und Erzeugen sind verschiedene Betriebspunkte, und Kanten ueber
verschiedene Punkte sind nicht vergleichbar. Kanten ueber die R5-Fix-Grenze
nie mischen.

Kostenschaetzung (HERLEITUNG aus 3,33 s je Partie gepaarter b05-Arena): Anker
rund 8 min, Champion rund 22 min, Vorgaenger je nach SPRT-Verlauf bis rund
17 min -- zusammen unter einer Stunde, exklusiv zu fahren.

Faellt die Wahl spaeter auf b02 statt b01 (Kaltstart gegen Warmstart), gelten
dieselben drei Kanten fuer den Arm, der weitergeht.

Danach: Phase 3 (Betrags-Schiene, `PREREG_r5_value_calibration.md`,
Erfolgstest "kippt die Sims-Kurve?"), Erreichbarkeits-Nachpruefung Stufe 0
(`PREREG_v23_reachability_recheck.md`), optional Stufe 4 des
Suchtiefen-Strangs. Bei einem Champion-Wechsel die vollstaendige
`docs/promotion_checklist.md` abarbeiten (Pflicht-Diagnostiken,
Anzeige-Kalibrierung in server.py, sigma-Prior-Waechter).

---

## 3. STAND JETZT

**Champion:** `v21_2d_brierbest`, Elo **1215** [1170, 1259] auf der
R5-Fix-Leiter. Kanten ueber die Fix-Grenze nie mischen.

**Bester Stand der Spalten-Linie:** `v22-b05` -- volle Spalten 0,3375 am
argmax-Instrument (3,3x Champion), Punkte 37,16 (+3,86, t 2,61), Elo
**1084** [961, 1198] aus einem SPRT-Fruehstopp unter 150 Paaren (informativ,
nicht promotionsfaehig). Der hv2-Lehrer liegt mit 1125 dazwischen.

**Wheel:** 79-Kanal-Build (`e91cd34`), Vertragshash `efd564d87bac2722`,
Paritaets-Hash `8c6684ff...` gemessen unveraendert.

**Was ueber den Value-Kopf gemessen ist:** relativ geheilt, im Betrag
gedaempft. Geschwister-Tau auf b05 **+0,338** (gegen -0,08/-0,19 der
plattenblinden Netze), Mensch-Orakel-Differenz praktisch null -- aber
R5-Platten-Steigung **0,0886** statt ~1. Kriterienweise aufgeloest ist die
Daempfung BREIT, nicht spaltenspezifisch (k1 mit 0,1747 am wenigsten
gedaempft). Daraus die Betrags-Schiene als Phase 3.

**Was ueber den Spaltenbau gemessen ist:** der Korpus wirkt (b01 baut 3x so
viele Spalten wie der Champion), das Ownership-TRAININGSGEWICHT nicht (w0
gleichauf, w2,0 signifikant darunter). Der Engpass ist die VOLLENDUNG spaet,
nicht der Plattenblick. Die Suchtiefe ist ein Regler zwischen Policy
(traegt das Spaltenwissen) und Value-Kopf: Plateau 25-100 Sims bei ~0,6
vollen Spalten gegen 0,34 ab 250 -- aber ein TAUSCH (@25 verliert 11:29,
@100 verliert 33:47 n.s.). Die Erklaerung dafuer ist OFFEN; die Deutung
"der Kopf sieht Spalten nicht" ist durch die kriterienweise Zerlegung
widerlegt.

**Erzeugungs-Knoepfe, gemessen entschieden:** implicit-Minimax alpha 0,0,
Stack-Draw-Kontrollfluss EIN, Bootstrap-Horizont 2, Seed-Positionen AUS
(Quelle plattenblind), Startkuppel Handheuristik, Vollendbarkeits-Filter AUS
(ungebaut). Vollstaendig in `PREREG_v23_window.md` par.4c.

---

## 4. OFFENE ENTSCHEIDUNGEN (Nutzer)

| Punkt | Worum es geht |
| --- | --- |
| **Traeger-Manifest fuer hv2** | `PREREG_v23_window.md` par.1 will hv2 ueberwiegend policy-maskiert (1.800 von 24.000 Partien aktiv). Das geht nur per Manifest, und das entwertet die 2.400 liegenden hv2-Bloecke. Ohne Manifest traegt jeder hv2-Record mit `policy_target_valid != false` Policy (gezaehlt: 534 von 1.733 in einer Datei) -- der Cache bleibt, aber das Fenster weicht bewusst von par.1 ab und das gehoert dann registriert |
| **b04: welcher Zweig wird breiter** | Flach-Zweig `hidden_size` 512 ist ohne Bau fahrbar; Conv-Zweig `conv_channels` 48 / `conv_layers` 2 braucht zwei Flags, ein Checkpoint-Feld und eine Ableitung beim Laden -- sonst ist der Checkpoint nicht ladbar (`PREREG_capacity_sim_frontier.md` par.10) |
| **Loeschfreigaben** | `data/onpolicy_v22-b06/` (31 Dateien) und -- falls keine DAgger-Runde 3 -- `data/onpolicy_v22-b05/` (30) |
| **Messartefakte tracked?** | `evaluations/artifacts/` ist ungetrackt; Preregs zitieren die JSONs als Beleg, ein frischer Klon hat sie nicht. Zurueckdrehen: `.gitignore`-Zeile raus, `git add -f` |
| **Push** | NIE ohne ausdrueckliche Anweisung; der Ahead-Stand wird im CHAT gemeldet, nicht hier gefuehrt |

---

## 5. OFFENE STRAENGE -- abgeglichen mit dem Prereg-Index (2026-08-31)

Der Index zaehlt **22 OFFEN, 71 ENTSCHIEDEN, 8 UEBERHOLT**. Beim Abgleich
sind zwei Koepfe berichtigt worden, die gegen ihren eigenen Stand standen:
`cache_build_time` sagte "nicht in train.py verdrahtet" (`--cache-file`
existiert seit `dc40551`, train.py:2554), und `v23_reachability_recheck`
sagte "v22-Self-Play per Tor-Regel gestoppt" (es laeuft seit dem 2026-08-30).

**Am laufenden Strang, mit Platz im Fahrplan:**

| Prereg | Wo es haengt |
| --- | --- |
| `v23_window` | Fensterbau -- Abschnitt 2.2 |
| `capacity_sim_frontier` | b02/b04 -- Abschnitt 2.3 |
| `policy_surprise_weighting` | b03 -- ungebaut |
| `reanalyze_label_depth` | Relabel-Etappe: Policy per hv2-Lehrer, Value tief -- Abschnitt 2.2 |
| `r5_solver_split` | Teil B = R5-Value-Kalibrierung, Phase 3 |
| `v23_reachability_recheck` | Stufe 0 NACH dem v23-Training |
| `search_depth_column_optimum` | weitgehend beantwortet; offen bleibt die ERKLAERUNG (optionale Stufe 4) |
| `special_tile_yield` | Kanaele 77/78 gebaut, ihre Wirkung nie isoliert |
| `cache_build_time` | Hebel (3) offen; serielle Vollreferenz fehlt |

**Registriert, nicht eingetaktet** (jeder Bau braucht vorher eine
Registrierung): `plate_policy_supervision`, `saturating_score_utility`,
`risk_sensitive_leaf_utility`, `uvfa_plate_regime`,
`uncertainty_guided_selfplay`, `start_position_seeding` (Dosis-Folgearm),
`start_dome_choice` (Stufe 0, Wiedervorlage Generation 2),
`round_transition_search_sampling` (Kostentor zuerst),
`stack_draw_reservation_rule` (Default AUS steht),
`stack_top_feature`, `chance_nodes` (Teil B1/A1 geparkt),
`floor_shaping_scale`, `rust_data_layer` (Registrierung, kein Auftrag).

**Verschoben, nicht verworfen:** Arm K (Bootstrap-Kohaerenz,
`PREREG_heuristic_v2_long_rows.md` par.3b.3/3b.3a) -- gebaut, Default aus,
ausloeserbasiert. Er korrigiert einen VERSATZ, das gemessene Problem ist eine
STEIGUNG; seine drei benannten Nutzniesser sind ungebaut; und er ist der
einzige Arm, der alle Cache-Bloecke entwertet.

---

## 6. MERKLISTE CODEPFLEGE (Audit 2026-08-27, bewusst verschoben)

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

## 7. STRUKTURBEFUNDE, die weitergelten

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
  Abschluesse je Partie, v21 0,1. Kosten-gewichtete Huelle Mensch 0,84,
  Maschinen 0,54-0,62.
- **Blindzieh-Regel:** bei Wertungsplatte 6 laeuft die gebaute Stopp-Regel das
  Punktekonto leer (58-66 Prozent der Serien enden bei 0). Spaltenbau behebt
  das NICHT -- k1 zahlt quadratisch, das Spezialfeld-Defizit kostet linear -3
  je Feld.
- **Eine Herleitung aus dem Code ist eine Hypothese, kein Befund.** Am
  2026-08-25 lagen vier davon im Vorzeichen falsch.
