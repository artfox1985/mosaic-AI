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

## 1. STAND DER ERZEUGUNG: FERTIG, TOR 0 BESTANDEN (2026-08-31)

**Der v23-Fensterkorpus ist erzeugt** (Generator `v22-b05`, 2026-08-30 19:25
bis 2026-08-31 07:20, rund 12 h): 6.000 value-argmax + 2.000 value-sampled +
4.000 policy, alle drei Klassen vollzaehlig. Der Cache-Co-Bau hat mitgehalten
-- **3.000 Bloecke liegen, 0 offen**; dank des Traeger-Umbaus
(`PREREG_cache_build_time.md` par.10) ueberleben sie das Manifest.

**Tor 0 GEFAHREN 2026-08-31, beide Wächter bestanden** (Registrierung und
Einordnung: Lehrer-Prereg par.3b.12):

| Waechter | Ergebnis |
| --- | --- |
| primaer: Symmetrie-Trennung Value-Klasse | **+0,4041 +- 0,0192, t 41,26** (398 Bloecke) -- TRENNT |
| sekundaer: Seiten mit voller Spalte | **5.629 von 16.000**, Schwelle 1.500 -- 3,75-fach |
| Bericht: volle Spalten je Partie+Seite | Value **0,481**, Policy 0,129 |

**Der Berichtswert ist ein eigener Befund:** 0,481 liegt UEBER dem
argmax-Instrumentwert 0,3375 -- genau wie die Sims-Kurve es vorhersagt.
Nachgerechnet aus den registrierten Vorbefunden (6.000 argmax bei ~0,6 plus
2.000 gesampelt bei ~0,10) erwartet man 0,475, gemessen sind es 0,481. Zwei
auf 200-Partien-Stichproben registrierte Befunde treffen damit auf 8.000
Partien.

**Traeger-Manifest gebaut:** `data/policy_carrier_manifest_v23.json`, 380
Eintraege -- 180 hv2-Dateien (1.800 Partien, Seed 20260921 aus dem Fenster
von Seed 20260920) plus die Policy-Klasse vollstaendig (200 Dateien). Die
Value-Klasse ist bewusst nicht gelistet.

**Damit ist der Weg frei fuer den Fensterbau und das v23-Training.**

**OFFEN AUS DIESER ERZEUGUNG (Nutzer-Anweisung 2026-08-31):** die
b05-Dateien tragen **20 Partien statt der geregelten 10**. Der Wert kam aus
dem Nachtrezept (`night_run_20260830.md`, Vorsitzung) und wanderte ueber die
Uebergabe in die gefahrenen Befehle; `self_play.py` steht per Default auf 10.
Regel ab jetzt: nicht ueberschreiben (`docs/working_rules.md`, Abschnitt
"Korpusdateien tragen 10 Partien"). **Fuer den laufenden Korpus bleibt es bei
20** -- ein Umpacken (`tools/repack_corpus.py`) waere moeglich, wuerde aber
alle 600 Basenames und damit ihre Cache-Bloecke aendern, und b01 traint
bereits darauf. Wiedervorlage nach b01, falls die groebere Granularitaet
beim naechsten Fensterschnitt stoert.

## 1b. v23-b01 STEHT, TOR 2a BESTANDEN (2026-08-31)

`v23-b01` ist trainiert (Warmstart von b05, 5,97 h, Kandidat
`v23-b01_brierbest`, Epoche 5, val_brier 0,1934). **Tor 2a ist bestanden, und
zwar mit Abstand** -- Herleitung und Tabelle in `PREREG_v23_window.md`
par.2b:

| je Partie und Seite | v23-b01 | v22-b05 |
| --- | --- | --- |
| **volle Spalten** | **0,5150** | 0,3100 |
| Punkte | 46,80 | 42,10 |
| Strafleiste | 5,74 | 6,61 |

Gepaart (gleicher Seed, 200 Paare): **+0,2050 +- 0,0898, t +4,47** -- plus
66 Prozent. Der Spaltenbau kostet hier NICHTS: mehr Punkte bei weniger
Strafsteinen.

**Laufend:** Tor 1 (gepaartes Gating b01 gegen b05, Champion-Strenge,
`--no-promote-winner`) auf der CPU, `v23-b02` (Kaltstart) auf der GPU.
**Danach:** Tor 2b (Arena mit `--log-games` +
`tools/probes/arena_column_probe.py`) und die drei Elo-Kanten.

**Beim Aufsetzen von Tor 1 abgefangen:** `paired_gating.py --promote-winner`
steht per Default auf AN und haette `models/champion.txt` auf b01 gesetzt,
sobald der SPRT signifikant ausfaellt. Das waere eine stille Promotion gegen
die eigene Regel gewesen (Champion ist v21; b01-gegen-b05 ist das
Ratschen-Tor). Mit `--no-promote-winner` gefahren.

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
* **Traeger-Manifest: JA (Nutzer-Entscheid 2026-08-31), und es kostet keine
  Bloecke mehr.** Der Traegerstatus ist seit dem Umbau vom 2026-08-31 KEIN
  Bestandteil des Datei-Schluessels mehr (`PREREG_cache_build_time.md`
  par.10): der Block ist traegeragnostisch, die Maske kommt beim
  Zusammenfuegen. Die ~2.600 befuerchteten Neubauten entfallen ersatzlos;
  Bestand nachweislich stabil (99 von 100 Schluesseln treffen, der eine
  Fehlschlag war eine 52 Sekunden alte Datei), Abnahme 4/4 gruen
  (`carrier_mask_at_merge_probe.json`). **Gezogen ist beides:** Fenster 1.745
  Dateien (Seed 20260920, `data/window_v23_hv2.txt`), Traeger 180 davon
  (Seed 20260921, `data/carriers_v23_hv2.txt`, = 1.800 Partien).
  **Zusammengebaut wird das Manifest, sobald die policy-Klasse fertig ist** --
  denn: **die Policy-Klasse MUSS ausdruecklich mitgelistet werden** (180 hv2 +
  200 b05-policy = 380 Eintraege) oder das Manifest traegt
  `carrier_prefixes: ["selfplay_v22-b05-policy_"]`; der Generator hat dafuer
  seit 2026-08-31 `--include-glob` (leerer Glob = harter Abbruch). Sonst setzt
  es `pol_w=0`
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

### 2.3b BELEGUNGSPLAN: GPU und CPU parallel (Nutzer-Entscheid 2026-08-31)

Nicht seriell fahren, was sich nicht dieselbe Ressource teilt. Regel und
Thread-Budget: `../docs/working_rules.md`, Abschnitt "Auslastung". Fuer diese
Kette heisst das konkret:

| GPU | CPU daneben (rund 10 Threads -- ein Training belegt gemessen nur EINEN Kern) |
| --- | --- |
| -- (Erzeugung laeuft) | Cache-Co-Bau -- laeuft bereits so |
| b01 trainiert | Relabel-Kopie anlegen und Policy-Relabeling fahren; danach die Bloecke der Kopie bauen |
| b02 trainiert (Kaltstart) | **b01s drei Elo-Kanten** (Abschnitt 2.4) |
| b03/b04 trainieren | tiefes Value-Nachlabeln (Tagesbudget, `PREREG_reanalyze_label_depth.md`) |

Zwei CPU-Auftraege gegeneinander bleiben verboten -- sie teilen dieselbe
Ressource, bremsen sich und machen beide Laufzeiten wertlos. Und jeder unter
Nebenlast gefahrene Lauf markiert das in seinem `laufzeit`-Block, sonst
wandern gebremste Zahlen als Planungsgroessen nach
`../docs/measured_runtimes.md`.

### 2.3c ABNAHME DER GENERATION v23 (Nutzer-Anweisung 2026-08-31)

Wortlaut: *"mindestens genauso viel Affinitaet zum Spaltenbau wie v22-b05.
Mehr nehm ich gern. Und muss v22-b05 besiegen. Gating Kriterien wie bei einem
Spiel gegen den Champ. Trifft das fuer ein Modell der v23 Generation zu,
koennen wir in die self plays fuer v24 gehen."*

| Tor | Bezug v22-b05 | Zuschnitt |
| --- | --- | --- |
| **1: Siege** | Elo 1084 | gepaarte Arena, **Champion-Strenge**: n >= 150 Paare oder Replikation mit eigenem Seed. Ein SPRT-Fruehstopp darunter ist informativ, KEIN Tor-Ergebnis |
| **2a: Spalten im SELF-PLAY** | **0,3375** volle Spalten je Partie+Seite | am REGISTRIERTEN argmax-Instrument (deterministisch, ohne Root-Noise, gleiche Sims wie die Referenz) -- nicht am Erzeugungs-Betriebspunkt |
| **2b: Spalten in der ARENA** | k1-Punkte von b05 aus demselben Lauf | gepaarte Arena gegen b05 mit `--log-games`, ausgewertet ueber `tools/plate_points_from_arena.py`. Beide Seiten stammen aus DENSELBEN Partien, eine getrennte Referenz braucht es nicht |

**Warum zwei Flaechen (Nutzer-Anweisung 2026-08-31):** im Self-Play
konkurriert niemand um die Farben. 2a sagt, was der Generator in den
v24-Korpus schreiben wuerde; 2b sagt, ob er Spalten auch gegen Widerstand
baut. Ein Netz kann das eine koennen und das andere nicht. Achtung bei 2b:
das Partie-Log traegt die Endwertung je Kriterium, NICHT das Endbrett -- die
ANZAHL voller Spalten ist daraus nicht rekonstruierbar, k1-Punkte sind der
monotone Ersatz und duerfen nicht als Anzahl gelesen werden.

**Punktschaetzer entscheidet Tor 2:** liegt der Kandidat darunter, ist es
gerissen, auch bei nicht signifikantem Abstand. Dann Vorlage mit beiden
Zahlen samt Signifikanz.

**Was das Bestehen freigibt:** das Self-Play fuer **v24**. Die Promotion zum
Champion ist eine ANDERE Frage und faellt erst mit der Kante gegen
v21_2d_brierbest (1215). Eine Linie darf mehrere Generationen ratschen, bevor
sie den Champion einholt -- Verfahren in `../docs/generation_loop.md`.

**Achtung beim Messen von Tor 2:** die Referenz 0,3375 stammt vom
argmax-Instrument bei 400 Sims. Die Erzeugung lief bei 100 Sims und der
Korpus zeigt dort 0,481 -- dieselbe Groesse liegt je nach Suchtiefe um mehr
als das Doppelte auseinander. Kandidat und Referenz muessen am GLEICHEN
Betriebspunkt gemessen werden, sonst misst das Tor die Sims-Zahl.

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
| `geometric_envelope` | Gelaender fuer die fruehen Runden -- Stufe 0 ist netzfrei und kann VOR dem v23-Training laufen |

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
