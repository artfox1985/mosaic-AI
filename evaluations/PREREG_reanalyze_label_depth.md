<!-- STATUS: OFFEN | Frage: Reagieren SPIELEN und LABELN unterschiedlich auf Suchtiefe -- und heilt tieferes Nachlabeln die Betrags-Daempfung? | Beleg: Zeile-1-Frage UNGEMESSEN (par.3 A1/A2 nie gefahren). Gefahren wurde stattdessen Lehrer-Relabeln (par.4a): `v23-b05`, Arena 85:75 fuer b05, p = 0,53, Spalten 0,679 gegen 0,635 (par.A1, Kennzahlen nachgetragen 2026-09-01) -- nicht belegt besser, b01 bleibt Generator fuer v24. Teil B (Value tief) UNGEBAUT. -->

# Vorregistrierung: Reanalyze -- Spielen und Labeln entkoppeln

**Angelegt 2026-08-30** auf Nutzer-Auftrag ("das muessen wir mal
aufschreiben und mit dem Phasenplan abgleichen"), VOR jeder Messung.

## par.1 Zwei unabhaengige Motive, die auf dasselbe Werkzeug zeigen

**(1) Anti-Drift (Literatur).** Die Research-Durchsicht 2026-08-29 hat
Reanalyze als den Standard-Mechanismus gegen die Moving-Target-Falle
iterierten Self-Plays benannt (RESEARCH_alphazero_improvements Fund 2,
Uebertragbarkeit "HOCH" wegen des perfekten Simulators). Im Projekt ist
er UNBESETZT -- geprueft per Grep ueber alle Preregs: ausser dieser
Datei erwaehnt ihn keine. Das gebaute
`tools/relabel_drafts_with_teacher.py` ist etwas anderes: es ersetzt
POLICY-Ziele durch LEHRER-Zuege und laesst die Value-Felder
ausdruecklich unberuehrt (Docstring).

**(2) Der gemessene Sims-Effekt (neu, 2026-08-30).** Flachere Suche
SPIELT bei b05 spaltenreicher und punktstaerker
(PREREG_search_depth_column_optimum: 100 Sims 0,6225 gegen 400 Sims
0,3375). Das NETZ-Self-Play koppelt aber Spielen und Labeln in einer
Suche, waehrend der hv2-Korpus sie trennt (Heuristik spielt, Netz
labelt mit 600). Wenn die beiden Rollen unterschiedlich auf Tiefe
reagieren, ist die Entkopplung die saubere Loesung -- flach spielen,
tiefer nachlabeln.

## par.2 Voraussetzungen, mit Pruefstand

| # | Voraussetzung | Stand |
| --- | --- | --- |
| 1 | flache Suche spielt wirklich besser | OFFEN -- Self-Play-Zahlen ja, Arena steht aus (Sims-Prereg Stufe 3) |
| 2 | tiefe Suche labelt wirklich besser | UNGEPRUEFT, und es gibt keine neutrale Referenz (ein tieferes Orakel ist derselbe Bewerter mit mehr Zeit) -- deshalb ist Teil A ein END-TO-END-Test, kein Metrik-Vergleich |
| 3 | die Engine kann nachlabeln | **ERFUELLT**: `net_search_state_json(state_json, model_path, sims, c_puct, seed)`, lib.rs:865 -- nimmt gespeicherte Zustaende und eine FREIE Sims-Zahl. Offen bleibt der Fuenf-Minuten-Check, ob die Rueckgabe die BESUCHSVERTEILUNG traegt (das Policy-Ziel) oder nur Zugbewertungen |

## par.3 TEIL A -- reagieren Spielen und Labeln unterschiedlich? (Policy-Seite)

**Anordnung (die einzige, die die Rollen trennt):** EIN Spielkorpus,
ZWEI Label-Varianten.

* Korpus: der **SOCKEL** (Policy-Klasse) des v22-Self-Play, flach
  gespielt. NICHT der Schwarm -- der laeuft `--value-only` und traegt
  per Konstruktion keine gueltigen Policy-Ziele, dort gaebe es nichts
  nachzulabeln (Nutzer-Praezisierung 2026-08-30).
* Arm A1: Labels wie gespielt (flache Tiefe).
* Arm A2: alle Draft-Zustaende mit tiefer Suche (400) nachgelabelt.
* Sonst identisch: gleiches Fenster, gleicher Seed, gleiches Rezept.

**Zielmetrik (vorab):** die arena-validierten Orakelmetriken
(`prior_mass_on_oracle_top3`, `kendall_tau`, 7/7 richtig), bei
Gleichstand die Arena. Ausdruecklich NICHT ein Vergleich der Labels
untereinander -- dafuer fehlt die neutrale Referenz (par.2 Nr. 2).

**Kosten (Annahme, aus 12,5 s je 400-Sims-Partie und ~80 Zuegen):**
~0,15 s je Zustand. Ein voller 12.000-Partien-Korpus haette ~600.000
Draft-Zustaende, also rund einen Tag -- fuer den A/B genuegt eine
Teilmenge (1.000 Partien, ~2 h). Dazu zwei Afterburner-Trainings.

**Bedingung, die den Test ueberhaupt erst moeglich macht:** der Sockel
muss FLACH gespielt worden sein. Faellt die Sims-Entscheidung auf eine
tiefe Sockel-Suche, sind die Labels schon tief und es gibt nichts
nachzulabeln -- dann braeuchte Teil A einen eigenen Korpus.

## par.4 TEIL B -- Value-Reanalyze gegen die Betrags-Daempfung

Die Value-Ziele tragen einen Bootstrap-Anteil aus der Suche (`root_q`).
Ihn mit dem AKTUELLEN Netz und tieferer Suche nachzurechnen ist die
Haelfte, die in der Literatur den Ausschlag gibt, und sie zielt direkt
auf den gemessenen Defekt (R5-Platten-Steigung 0,0886, Fahrplan
Phase 0). Betrifft den SCHWARM (Value-Klasse) und den Sockel
gleichermassen.

**Ehrlicher Vorbehalt, der Teil B von Teil A unterscheidet:** hier
labelt dasselbe Netz nach, dessen Bewertung verzerrt IST. Reanalyze
verbessert dann die Konsistenz (weniger Drift gegen ein veraltetes
Netz), aber nicht notwendig die Richtigkeit. Ein Gewinn ist zu
erwarten, wenn die Ziele von einem SCHWAECHEREN Vorgaenger stammen --
genau der Fall im Generationen-Loop, nicht im Erstlauf.

## par.4a DREI Arten von "Relabeln" -- nicht verwechseln (praezisiert 2026-08-30 nach der Sims-Kurve)

Die Kurve (PREREG_search_depth_column_optimum) zwingt zu einer
Unterscheidung, die par.1 noch nicht scharf hatte: sie gilt auch fuer
die BESUCHSVERTEILUNG. Eine tiefe Suche besucht denselben Spaltenzug
seltener als eine flache -- tiefes Nachlabeln holt die
Spaltenblindheit also ueber die Hintertuer zurueck.

| Variante | Ziele danach | Stand |
| --- | --- | --- |
| tief nachlabeln (Reanalyze i.e.S.) | taktisch schaerfer, aber SPALTENAERMER | die Falle; fuer die Policy-Seite kontraproduktiv, solange die Kurve gilt |
| Lehrer-Relabeln (DAgger) | spaltenreich | gebaut; Runde 2 GESAETTIGT (par.3b.11) |
| **flach spielen + Lehrer-Relabeln** | spaltenreiche Zustaende UND Ziele | NEU, Nutzer-Vorschlag 2026-08-30 |

**Die dritte Zeile ist die interessante, und sie liefert eine
Erklaerung fuer die Saettigung:** alle bisherigen DAgger-Runden liefen
auf Brettern aus 400-Sims-Spiel -- genau den spaltenaermsten, die b05
produziert. Auf ihnen bedient laut par.3b.8 selbst der LEHRER die
fehlende Reihe nur zu ~0,25. Mit einem flach gespielten Sockel waeren
die Bretter spaltenreicher, der Lehrer haette dort wieder etwas zu
holen. HYPOTHESE, nicht gemessen -- aber sie erklaert die Saettigung
ohne die Annahme, DAgger sei ausgereizt.

**Fuer die VALUE-Seite gilt der Einwand NICHT.** Dort geht es um
Bootstrap-Werte, nicht um Zugpraeferenzen; tieferes Nachrechnen ist
dort unverdaechtig. Daraus die Arbeitsteilung (Nutzer 2026-08-30):
flach spielen, POLICY per Lehrer relabeln, VALUE tief nachlabeln.

**Zwei Auflagen fuer den Value-Teil, die dabei nicht untergehen
duerfen:** (1) das Value-Ziel ist KEIN einzelner Suchwert, sondern
Ausgang plus Bootstrap (TD_LAMBDA 0,5, Horizont 2) -- nachlabeln heisst,
diese Kette konsistent neu zu rechnen, nicht nur root_q zu ersetzen.
(2) Kosten grob 0,15 s je Zustand bei 400 Sims; ein voller
12.000-Partien-Korpus ist damit ein Tagesbudget.

## par.4b Wo relabelt wird: KOPIE mit eigenem Praefix (Nutzer-Entscheid 2026-08-31)

Nutzer: *"da relabeling anscheinend die pkl daten aendert, mach einfach einen
subordner mit dem gesamten kopierten fenster. das wird dann gelabelt und
stoert keinen."* Richtig, mit einer Praezisierung, ohne die die Isolation
nicht haelt:

**Der Unterordner allein trennt den Cache NICHT.** Der Datei-Cache-Schluessel
wird aus dem BASENAME gebildet, nicht aus dem Pfad (file_cache_key.py:81,
`"filecache_v1|" + basename`). Gleiche Dateinamen in einem anderen Ordner
ergeben denselben Schluessel; die relabelte Kopie traefe also den Block des
Originals -- genau die stille Falle, gegen die die Kopie gebaut wird.
`tools/relabel_drafts_with_teacher.py` schreibt in place (Zeile 138), und
`build_cache_incremental.py` erkennt einen Block allein am Dateinamen (kein
mtime, kein Inhalt).

**Also: Kopie MIT eigenem Praefix.** Form (am Code geprueft 2026-08-31: das
Dateinamen-Regex in train.py liest die Klasse korrekt heraus, und der Praefix
faellt unter keine Blockliste -- weder `LEGACY_STRETCHED_PREFIXES` noch
`V20_CARRIER_SHORTCUT_PREFIXES`):

```
data/relabeled_v23/selfplay_v22-b05relab-<klasse>_<datum>_g<N>.pkl
```

**Kopiert wird nur der NEUE Korpus, nicht das ganze Fenster.** Die
hv2-Haelfte ist der Lehrerkorpus -- ihre Policy-Ziele SIND schon die des
Lehrers; sie mitzukopieren waere bestenfalls ein No-op und wuerde ihre 2.400
Cache-Bloecke entwerten. Umfang: rund 600 Dateien a 2,35 MB = 1,4 GB
(Platte ist kein Argument, 1,7 T frei).

**Was das an der Reihenfolge-Frage aendert:** sie loest sich auf. Roh und
relabelt liegen nebeneinander auf DENSELBEN Partien. Das v23-Training faehrt
zuerst das rohe Fenster (die reine On-Policy-Wette des Zuschnitts D), und das
relabelte Fenster wird ein gepaarter Arm darauf -- ein Faktor, identische
Spiele. Das ist die Bauform, die diese Kampagne sonst nachtraeglich
herzustellen versucht.

**GEFAHREN 2026-08-31, Policy-Seite:** die Kopie liegt als
`data/relabeled_v23/selfplay_v22-b05relab-policy_*` (200 Dateien, 4.000
Partien, 404 MB). Ergebnis: **204.008 von 210.529 Draft-Entscheidungen
relabelt, 0 Fehler, 0 nicht abbildbar**, 6.521 uebersprungen, weil der
Lehrerzug kein Steinzug war (`type != "stone"`, also Stapel-/Sonderzuege --
sie bleiben unveraendert stehen). 744 s mit 4 Workern, neben dem
b01-Datenaufbau, also unter Nebenlast.

**NUR die Policy-Klasse, nicht der Schwarm** -- eine Praezisierung gegenueber
par.4b ("nur der NEUE Korpus"): das Traeger-Manifest listet die Value-Klasse
nicht, ihre Policy-Ziele haben im Training Gewicht 0. Sie zu relabeln waere
dreimal so teuer und am Training wirkungslos. Fuer den Schwarm ist das
VALUE-Nachlabeln vorgesehen (Teil B), und das ist eine andere Operation.

Damit liegen roher und relabelter Sockel auf DENSELBEN 4.000 Partien
nebeneinander. Der Vergleich ist ein gepaarter Arm nach b01/b02, kein
Bestandteil von b01.

## par.5 Abgleich mit dem Phasenplan (STATUS)

* **Phase 2 (Generationen-Lauf) geht VOR** -- beide Teile brauchen den
  Korpus, den sie erst erzeugt.
* **Phase 3.1 des Fahrplans nannte "Reanalyze-light" bereits als
  Kandidaten**, aber ohne Prereg und ohne die Label-Tiefen-Frage. Diese
  Datei ersetzt den losen Eintrag; der Fahrplan verweist hierher.
* **Reihenfolge innerhalb Phase 3:** Teil A ist billiger und
  beantwortet eine Frage, die den naechsten Erzeugungslauf betrifft
  (Sockel-Tiefe). Teil B ist der eigentliche Angriff auf die
  Daempfung, aber er lohnt erst in Generation 2+ (siehe par.4).
* **Abhaengigkeit nach unten:** faellt die Arena der Sims-Prereg
  (Stufe 3) gegen die flache Suche aus, entfaellt Motiv (2) -- Teil A
  bleibt dann nur als Label-Frage bestehen, mit deutlich geringerer
  Dringlichkeit.

## par.A1 TEIL A GEBAUT UND GEMESSEN: `v23-b05` (2026-09-01)

**Vorab, nachgetragen 2026-09-01:** dieser Absatz misst NICHT den in par.3
registrierten Teil A (A1 flach gegen A2 tief nachgelabelt). Gefahren wurde die
Variante aus par.4a/par.4b, Lehrer-Relabeln der Policy-Klasse -- der Schwenk
ist dort vor der Messung begruendet, par.3 blieb aber unveraendert stehen.
Die Zeile-1-Frage "reagieren Spielen und Labeln unterschiedlich auf
Suchtiefe" ist damit weiterhin UNGEMESSEN.

**Was gebaut wurde.** Der Relabel-Arm der v23-Generation: dieselben 2.345
Fensterdateien wie die Kontrolle `v23-b01`, aber die 200 Policy-Dateien durch
ihre lehrer-relabelten Kopien ersetzt (204.008 hv2-Lehrerzuege, 0 Fehler).
**Ein Faktor, dieselben Partien** -- Manifest-Diff `cli_args` b01 gegen b05
(nachgetragen 2026-09-01): `file_list window_v23.txt -> window_v23_relab.txt`,
`extra_data_dir None -> data/relabeled_v23`, `name`, `surprise_alpha None ->
0.0` (Default, wirkungsgleich) und `val_pool '^selfplay_v22-b05-' ->
'^selfplay_v22-b05'` (Regex ohne Bindestrich, damit die relabelten Kopien
mit in den Val-Pool fallen; sachlich noetig, aber ein zweiter Unterschied im
Validierungssatz).

| | Wert |
| --- | --- |
| Laufzeit | 26.695 s (7,42 h), davon **17.934 s (4,98 h) einkerniger Datenaufbau** |
| Epochen / Samples | 12 / 4,72 Mio |
| val_brier (E12) | 0,1954 |
| Korpus-Pruefung im Log | 200 relabelte Traeger (nicht 200 rohe), Traeger gesamt 380, Manifest gefunden |

**Arena gegen die Kontrolle** (2 x 80 Partien, getauschte Rollen, gleicher
Seed 20260995, `paired_arena_env_ab --log-games`):

```
b05 85 : 75 b01
Paare: b05 beide 23, geteilt 39, b01 beide 18
gepaarte Differenz +0,125, 95%-KI [-0,190, +0,440]
Vorzeichentest auf 41 informativen Paaren: p = 0,53
Punkte 46,72 gegen 46,62, Margin +0,10
```

**Offline auf drei Orakeln** (dieselben zwei Netze):

| Orakel | top3mass b05 / b01 | tau b05 / b01 | Richtung |
| --- | --- | --- | --- |
| v18 auf `frozen_v1` | **0,5538** / 0,5308 | 0,2320 / 0,2296 | b05 |
| b01 auf `frozen_v3` | 0,6423 / **0,6455** | 0,2115 / **0,2219** | b01 (zirkulaer, siehe `PREREG_frozen_v3_eval_set` par.9) |
| v21 auf `frozen_v3` | 0,4580 / **0,4644** | **0,1460** / 0,1363 | gemischt |

**Standard-Kennzahlen, nachgetragen 2026-09-01** (aus den Arena-Artefakten
`paired_arena_env_relabel_b05_first.json` / `_b01_first.json` und
`tools/probes/arena_column_probe.py`, Artefakte `columns_relabel_*.json`;
159 von 160 Partien nachspielbar):

| Kennzahl | b05 | b01 |
| --- | --- | --- |
| volle Spalten je Seite, b05 zuerst (n=79) | **0,6962** | 0,6329 |
| volle Spalten je Seite, b01 zuerst (n=80) | **0,6625** | 0,6375 |
| volle Spalten gepoolt (n=159) | **0,679** | 0,635 |
| lange Reihen begonnen / vollendet je Seite | 4,52 / 2,97 | 4,40 / 2,96 |
| Strafleiste (`total_floor`) je Seite | 8,86 | 9,88 |
| Punkte / Margin | 46,72 / +0,10 | 46,62 |

Punkte je Kriterium fehlen: `tools/plate_points_from_arena.py` nimmt
Arena-Kuerzel, nicht dieses Artefakt-Format; Spalten sind ueber die
Brettgeometrie abgedeckt. **Lesart:** der Relabel-Arm liegt in BEIDEN
Richtungen auch bei den Spalten vorn (+0,044 gepoolt), ohne Signifikanzpruefung
auf Block-Ebene; fuer den Generator-Entscheid (par.4 der v24-Prereg) lag diese
Zahl am Entscheidungstag nicht vor.

**Verdikt: der Relabel-Arm ist NICHT belegt besser -- und auch nicht
schlechter.** Er ist der einzige Arm dieser Generation mit positivem
Vorzeichen in der Arena (85:75), aber die Marge ist dieselbe, die b02 und b03
in die Gegenrichtung erzeugt haben; bei n=160 ist das die Rauschgrenze des
Instruments. Offline widersprechen sich drei Orakel auf winzigen Differenzen.

**Folge fuer v24:** `v23-b01` bleibt Generator. Der Vorbehalt aus
`PREREG_v24_window.md` par.4 ist damit AUFGELOEST, ohne dass sich am Zuschnitt
etwas aendert.

**Was der Arm trotzdem gebracht hat, und es ist nicht wenig:** er hat den
`frozen_v3`-Zirkularitaetsbefund ausgeloest (par.9 dort) -- der erste echte
Anwendungsfall des neuen Satzes hat gezeigt, dass sein Orakel als Richter ueber
b01 untauglich war. Und die Laufzeit-Zeile oben hat die 5-Stunden-Falle des
einkernigen Fenster-Aufbaus sichtbar gemacht (`docs/measured_runtimes.md`,
Ausweg: `--merge-out` parallel plus `train.py --cache-file`).

**Teil B (Value tief nachlabeln) bleibt UNGEBAUT.**
