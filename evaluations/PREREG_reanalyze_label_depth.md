<!-- STATUS: ENTSCHIEDEN | Frage: Reagieren SPIELEN und LABELN unterschiedlich auf Suchtiefe -- und heilt tieferes Nachlabeln die Betrags-Daempfung? | Beleg: NEIN (par.A5, 2026-09-03): Arm `v23-b07` (200 Policy-Dateien mit b01 @400 nachgelabelt, sonst b01-Rezept) gegen b01: Arena 75:85 (p = 0,55), argmax-Spalten 0,445 gegen 0,515, Arena-Spalten -0,08/-0,14, Orakel 4/4 knapp vorn, Value-Kopf unbewegt. Tiefes Nachlabeln traegt die Spaltenaermut der Tiefe ins Ziel (par.4a, mild); b01 bleibt Generator. Lehrer-Relabel b05: par.A3 Nullbefund. Teil B ohne Verbraucher. -->

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

## par.A2 VORREGISTRIERT: Arena b05 gegen b01 auf Champion-Strenge verlaengern (2026-09-01, VOR dem Start)

**Anlass (Nutzer):** *"ich wuerd mehr arena spiele von b05 und b01 eintakten.
dann laesst sich das besser abschaetzen."* Die 80 Paare aus par.A1 loesen
+-10 Siege nicht auf; `docs/generation_loop.md` verlangt fuer einen ENTSCHEID
n >= 150 Paare oder Replikation mit eigenem Seed.

**Aufbau, identisch zu par.A1 bis auf den Seed:** `tools/paired_arena_env_ab.py`,
Netz gegen Netz @400/@400, `--env-name MOSAIC_STACK_DRAW_RESEARCH --arms 1
--control 1`, `--log-games`, threads 10, je Richtung 80 Partien (Brett-Tausch
per zweitem Lauf mit vertauschten `--model/--model-b`). **Zwei neue Basis-Seeds
20260996 und 20260997**, jeweils beide Richtungen: +160 Paare, zusammen mit
par.A1 (Seed 20260995) **240 Paare = 480 Partien**. Artefakte
`paired_arena_env_relabel2_{b05,b01}_first_s{96,97}.json`.

**Entscheidungsmetrik, vorab:**
1. **Siege:** gepoolt ueber alle drei Seeds (240 Paare), Vorzeichentest auf
   den informativen Paaren (ein Paar = derselbe Spielindex in beiden
   Richtungen: 2:0 informativ, 1:1 geteilt) und gepaarte Siegdifferenz mit
   95%-KI auf Block-Ebene. **Blockgroesse 5** (16 gleiche Bloecke je Lauf;
   Projektstandard seit 2026-08-29, `paired_gating`). Berichtigt 2026-09-01
   um 23:55 auf Nutzer-Hinweis, BEVOR ein Artefakt geschrieben war: die erste
   Kette lief mit dem Werkzeug-Default 25 (80 Partien = Bloecke 25/25/25/5),
   wurde gestoppt, als der erste Lauf gerade fertig war, und komplett neu
   gestartet. Sein Artefakt liegt als
   `paired_arena_env_relabel2_b05_first_s96_blk25_verworfen.json` beiseite
   und fliesst NICHT ein (andere Seed-Ableitung je Block, nur eine Richtung). Die par.A1-Laeufe (Seed
   20260995) tragen keine Blockgroesse im Artefakt und werden fuer die
   Block-KI in 5er-Gruppen nach Spielindex gefasst. Dazu je Seed einzeln als
   Replikationspruefung: zeigen alle drei Seeds dasselbe Vorzeichen?
2. **Spalten:** `tools/probes/arena_column_probe.py` auf jedem Artefakt,
   gepoolt je Netz ueber 480 Partien; Bezug ist der Punktschaetzer wie bei
   Tor 2 (par.A1: b05 0,679 gegen b01 0,635).
3. **Standard-Kennzahlen** wie in par.A1 (Reihen, Strafleiste, Punkte, Margin).

**Was das Ergebnis ausloest -- als Vorlage, nicht als Automatik:** der
Generator fuer v24 ist Nutzer-Entscheid (`PREREG_v24_window.md` par.4).
- b05 signifikant vorn bei den Siegen (p < 0,05 auf 240 Paaren) UND nicht
  unter b01 bei den Spalten: Vorlage "Generator-Wechsel auf b05" mit beiden
  Zahlen.
- b05 nicht signifikant vorn, oder vorn bei Siegen und hinten bei Spalten:
  b01 bleibt Generator, der Befund wird als Marge mit KI festgehalten.
- b01 signifikant vorn: b01 bleibt, Relabel-Arm als negativ registriert.

**Kosten, aus par.A1 abgelesen:** 806 s je 80 Partien bei threads 10
(10,1 s je Partie), also rund **54 min** fuer die vier Laeufe. Laeuft
EXKLUSIV, nichts parallel.

## par.A3 GEMESSEN: 240 Paare, b05 NICHT belegt besser -- b01 bleibt Generator (2026-09-02, 01:00)

Vier neue Laeufe nach par.A2 (Seeds 20260996/97, beide Richtungen, je 80
Partien, **Blockgroesse 5**, `--log-games`; Artefakte
`paired_arena_env_relabel2_{b05,b01}_first_s{96,97}.json`, Spalten in
`columns_relabel2_*.json`), gepoolt mit par.A1 (Seed 20260995):

| Seed | b05 : b01 | informative Paare (b05 beide / b01 beide) | p Vorzeichen |
| --- | --- | --- | --- |
| 20260995 (par.A1) | 85 : 75 | 41 (23 / 18) | 0,53 |
| 20260996 | 86 : 74 | 44 (25 / 19) | 0,45 |
| 20260997 | **75 : 85** | 37 (16 / 21) | 0,51 |
| **gepoolt** | **246 : 234** | 122 (64 / 58) | **0,65** |

Gepaarte Siegdifferenz je Partie +0,025, Block-SE 0,044 (48 Bloecke a 5),
95%-KI [-0,064, +0,114], t 0,57. **Der dritte Seed dreht das Vorzeichen um**
-- genau die Seed-Streuung, die `docs/generation_loop.md` als Grund fuer die
150-Paare-Regel nennt.

**Standard-Kennzahlen, gepoolt ueber 480 Partien** (Spalten aus 478 Logs,
eine Partie nicht nachspielbar):

| Kennzahl | b05 | b01 |
| --- | --- | --- |
| volle Spalten je Seite | 0,6757 | 0,6423 |
| Spaltendifferenz je Partie, Block-KI (95 Bloecke) | +0,034 [-0,063, +0,131], t 0,68 | |
| Punkte / Margin | 46,97 / -0,34 | 47,31 |
| Strafleiste (`total_floor`) | 9,40 | 9,83 |
| lange Reihen begonnen / vollendet | 4,39 / 2,97 | 4,38 / 2,94 |

Punkte je Kriterium wie in par.A1 nicht berechnet (Werkzeug-Format).

**Verdikt nach der vorab registrierten Regel (par.A2, Fall 2):** b05 ist
weder bei den Siegen noch bei den Spalten signifikant vorn; der
Punktschaetzer liegt bei beiden knapp ueber Null, das KI schliesst Null ein.
**b01 bleibt Generator fuer v24**, der Befund steht als Marge mit KI. Der
Relabel-Arm ist damit weder Gewinn noch Schaden: 200 lehrer-relabelte
Policy-Dateien im Fenster bewegen den Nachfolger nicht messbar. Laufzeit der
vier Laeufe zusammen 3.649 s (10 Threads, rund 11,4 s je Partie, im Artefakt).

Damit ist die Vorlage fuer die Gleichstandsregel der Generatorwahl
(`docs/generation_loop.md`) gegenstandslos geworden, soweit sie an b05 hing:
bei 240 Paaren gibt es keinen Gleichstand mehr zu entscheiden, sondern einen
Nullbefund. Die Regel selbst bleibt fuer kuenftige Generationen offen.

## par.A4 EINGETAKTET (Nutzer 2026-09-02): Teil A als Arm `v23-b07`, Teil B ohne Verbraucher

**Teil A (Zeile-1-Frage) wird jetzt so gefahren, wie par.3 es registriert
hat:** EIN Spielkorpus, ZWEI Label-Varianten.

- **A1 = `v23-b01`** (Labels wie gespielt, Sockel flach @100). Liegt vor.
- **A2 = `v23-b07`:** dieselben 2.345 Fensterdateien, nur die 200 Policy-Dateien
  ersetzt durch Kopien, deren Draft-Policy-Ziele mit dem AKTUELLEN Generator
  `v23-b01_brierbest` bei **400 Sims** nachgerechnet sind (Besuchsverteilung
  der Suche, `add_root_noise=false`, Seed je Zustand hash-abgeleitet). Kopie
  mit eigenem Praefix wie par.4b: `selfplay_v22-b05deep-policy_*` in
  `data/relabeled_v23_deep/`. Training exakt das b01-Rezept
  (`--load v22-b05`, 12 Epochen, lr 5e-5, Cosine, Val-Pool `^selfplay_v22-b05`
  wie beim Relabel-Arm b05); Manifest-Diff gegen b01 muss GENAU `name`,
  `file_list`, `extra_data_dir` und den Val-Pool-Regex zeigen.
- **Unterschied zu b05:** dort labelte der hv2-LEHRER (anderer Spieler), hier
  labelt dasselbe Netz mit TIEFERER Suche -- das ist Reanalyze im engeren
  Sinn und beantwortet die Zeile-1-Frage; par.4a nannte es "die Falle",
  weil die tiefere Suche spaltenaermer waehlt (par.7 des Suchtiefen-Strangs:
  sie verwirft flaechendeckend, Spalten fallen mit). Genau deshalb ist der
  Arm informativ: liefert tiefes Nachlabeln trotzdem einen staerkeren oder
  gleich spaltenfaehigen Nachfolger?

**Werkzeug:** `tools/relabel_drafts_with_net.py` ueber
`mosaic_rust.net_drafting_policy_states_json_batch` (neu; ruft je Zustand
GENAU `self_play::net_drafting_policy`, also die Funktion, die im Self-Play
das `policy`-Feld schreibt: Gumbel-verbesserte Policy ueber ALLE legalen
Drafting-Aktionen, hier bei 400 Sims, ohne Wurzelrauschen; Netz einmal je
Prozess geladen). **Zielform-Entscheid nach dem Smoke (2026-09-02):** der
erste Entwurf nahm die Besuchsanteile der 16 Wurzelkandidaten -- das ist
eine ANDERE Zielform als im Self-Play (dessen Records tragen die verbesserte
Policy ueber bis zu 300 Aktionen); die Zeile-1-Frage verlangt aber "wie
gespielt, nur tiefer gelabelt", also dieselbe Zielform. Relabelt werden nur
Records mit Stein-Zug als Original-Ziel; Kuppel-, Stapel-, Chip- und
Pass-Records (Smoke: rund 14 Prozent der "drafting"-Records) bleiben
unveraendert. Engine-Aenderungen sind rein additiv (zwei Stapel-Einstiege),
trotzdem Wheel-Neubau und Anker-Invarianz (erster Einstieg: GRUEN,
`anchor_drift_20260902_batchentry.json`; zweiter: siehe Chronik).

**Kosten, gemessen im Smoke** (`relabel_net_smoke.json`, Besuchsanteil-
Variante): 0,21 s je Zustand einkernig bei 400 Sims, 2.209 Kandidaten je
Datei (20 Partien). Hochgerechnet 200 Dateien rund 440.000 Zustaende, mit 8
Workern rund 3 h -- dreimal die Herleitung oben, weil die Kandidatenzahl je
Partie (110) hoeher liegt als die 51 Lehrer-Relabels der b05-Kopie.

**Entscheidungsmass, vorab (par.3):** die arena-validierten Orakelmetriken
(`prior_mass_on_oracle_top3`, `kendall_tau`) auf `frozen_v1` mit v18-Orakel
und auf `frozen_v3` mit v21-Orakel (das b01-Orakel ist per par.9 als Richter
ueber b01-Nachfolger verbrannt); bei Gleichstand die Arena gegen b01, 2 x 80,
Blockgroesse 5, `--log-games`, dazu das Spaltenprofil am argmax-Instrument
(Generatorwahl-Regel, `generation_loop.md`). Lesart: liegt b07 bei
Orakel/Arena vorn UND nicht unter b01 bei den Spalten, ist tiefes Nachlabeln
ein Gewinn und wandert ins v24-Rezept als Option; liegt er bei den Spalten
klar darunter (Richtung b02/b06), ist par.4a bestaetigt: Reanalyze traegt
die Spaltenblindheit der Tiefe ins Ziel. Beides ist ein Befund.

**Kosten (Herleitung):** rund 204.000 Draft-Zustaende @400 Sims; im Spiel
kostet ein 400-Sims-Zug rund 0,1-0,15 s (Arena 11,4 s je Partie a ~80
Zuege), mit 8 Worker-Prozessen also grob 1 h; Smoke mit einer Datei vorab,
Zahl ins Artefakt. Training rund 2,5 h GPU mit Monolith (Trainingsanteil
per `tools/window_train_split.py`, Umgebung wie das Training). Arena und
Instrument rund 1 h CPU.

**Reihenfolge zu v24:** Relabel und Instrument sind CPU und laufen VOR dem
v24-Self-Play; das Training darf parallel zum Self-Play auf die GPU.

**Teil B (Value-Reanalyze) wird NICHT eingetaktet, und zwar aus einem Grund,
der erst jetzt sauber benannt ist:** das Trainingsrezept faehrt
`value_target_lambda 1.0` (b01-Manifest; Trainingslog: "kein Mix,
Bestandsverhalten, 23,5 % der Samples HAETTEN root_q"). Das Value-Ziel ist
der reine Partieausgang, der Bootstrap-Anteil `root_q` geht NICHT ein.
Tieferes Nachrechnen von `root_q` haette damit keinen Verbraucher. Teil B
wird erst wieder aktuell, wenn ein Zuschnitt lambda < 1 faehrt
(`PREREG_lambda_v18only.md`: lambda 0,7 war einmal arena-signifikant, die
b-Serie faehrt 1,0). Registriert als Bedingung, nicht als Verzicht.

**Smoke mit der Self-Play-Zielform (2026-09-02, `relabel_net_smoke2.json`):**
Anker-Invarianz nach dem zweiten Wheel-Neubau GRUEN
(`anchor_drift_20260902_policybatch.json`, 1.763 Schritte). Eine Datei (20
Partien): 2.209 Draft-Records des Spielers am Zug, davon **1.173 kein
Steinzug** (Kuppel, Stapel, Chip, Pass -- bleiben unveraendert), 1.036
Kandidaten, **1.012 relabelt**, 24 ohne Kandidaten (0 oder 1 legale Aktion),
0 nicht abbildbar, 0 Aktionen ausserhalb der Legal-Liste. Zielform identisch
zum Original (z.B. 305 Eintraege, Summe 1,0); der Top-1 bleibt in 494 von
1.012 relabelten Records derselbe. **0,267 s je Zustand einkernig**;
hochgerechnet rund 207.000 Zustaende, mit 8 Workern rund 2 h. Voller Lauf
gestartet, Ausgabe `data/relabeled_v23_deep/selfplay_v22-b05deep-policy_*`.

**Voller Relabel DURCH (2026-09-03, 09:36; `relabel_net_relabeled_v23_deep.json`,
8 Worker, Quelle `<Sicherungswurzel>/archive_pre_v24/v23_window_b05`):**

| Kennzahl | Wert |
| --- | --- |
| Dateien / Records gesamt | 200 / 685.865 |
| kein Steinzug (Kuppel, Stapel, Chip, Pass; unveraendert) | 231.442 |
| Kandidaten (Steinzug-Records des Spielers am Zug) | 210.529 |
| **relabelt** | **205.854** (97,8 % der Kandidaten) |
| keine Kandidaten (0 oder 1 legale Aktion) | 4.675 |
| nicht abbildbar / keine Besuche / Aktionen ausserhalb der Legal-Liste | 0 / 0 / 0 |
| Laufzeit (`laufzeit`-Block) | Wanduhr **39.569,5 s = 11,0 h**, threads 8, `s_je_zustand` 1,50 |

Die Wanduhr je Kandidat liegt bei 0,188 s (39.569,5 / 210.529, Herleitung),
also rund das 1,4-fache der einkernigen Smoke-Zahl (0,267 s) statt des
Achtfachen: die 8 Worker haben sich die 6 Kerne mit der rayon-Suche geteilt
(Chronik `night_run_20260902.md`, 00:33). Die Kette b07 (`tools/night_b07_chain.sh`:
Kopie nach `data/`, Traeger-Manifest 380, Bloecke, Trainingsanteil, Monolith,
Training) ist um 09:37 gestartet; Abweichung zum Text oben: die Deep-Dateien
liegen als Kopie in `data/` statt ueber `--extra-data-dir`, der Manifest-Diff
gegen b01 zeigt dann `name`, `file_list`, `val_pool`, `surprise_alpha` (kein
`extra_data_dir`). Abnahme folgt als par.A5.

## par.A5 ABGENOMMEN (2026-09-03): tiefes Nachlabeln macht b07 nicht staerker und kostet Spalten -- par.4a bestaetigt, mild; b01 bleibt Generator

**Training** (`manifest_train_v23-b07_20260903_095253.json`): b01-Rezept,
Warmstart `v22-b05`, 12 Epochen, 12.494 s Wanduhr (3,47 h, GPU; Datenaufbau
31,7 s ueber den Monolithen des Trainingsanteils, 4.721.817 Zustaende).
Manifest-Diff gegen b01 in `cli_args` GENAU `name`, `file_list`, `val_pool`,
`surprise_alpha` (die Deep-Dateien lagen als Kopie in `data/`, kein
`extra_data_dir`; uebrige Unterschiede sind Formatfelder des neueren
Trainers, Chronik 09:52). `v23-b07_brierbest` = Epoche 7, val_brier 0,1939
(b01: Epoche 5, 0,1934); Val-R2 Value 0,379-0,383 flach ueber alle Epochen.

**Ergebnis gegen die Lesart aus par.A4** (Bezug `v23-b01_brierbest`):

| Mass | b07 | b01 | Quelle |
| --- | --- | --- | --- |
| Orakel frozen_v1 / v18: top3mass, tau | **0,5332, 0,2454** | 0,5308, 0,2296 | `reanalyze_b07_vs_b01_frozenv1.json` (n 952) |
| Orakel frozen_v3 / v21: top3mass, tau | **0,4690, 0,1558** | 0,4644, 0,1363 | `..._frozenv3_v21orakel.json` (n 915) |
| Value-Spearman (v1 / v3) | 0,628 / 0,680 | 0,634 / 0,681 | dieselben |
| Arena 2 x 80, Seed 20260999, Blockgroesse 5 | **75 : 85**; Paare b07 beide 20 / geteilt 35 / b01 beide 25, Vorzeichentest p = 0,55; Siegdifferenz je Partie -0,062, Block-SE 0,071 (32 Bloecke); Margin -1,40 (Block-SE 1,63) | | `paired_arena_env_b07_b01_{first,second}_s99.json` |
| volle Spalten, argmax @400, 200 Partien, Seed 20260931 | **0,445 +- 0,065** (Seiten mit voller Spalte 139 von 400; >= 4: 2,17; hoechste 5,19) | 0,515 +- 0,065 (168) | `tor2a_v23b07.json`, 1.507 s (7,54 s je Partie, threads 11) |
| volle Spalten in der Arena (gepaart je Partie) | b07 minus b01 **-0,075** (Block-SE 0,133) und **-0,138** (0,150); Seiten 0,5375 / 0,475 | 0,6125 / 0,6125 | `columns_b07_b01_{first,second}_s99.json`, 160 von 160 replaybar |
| Huellen-Deckung H (Arena) | 0,454 / 0,454 | 0,462 / 0,459 | dieselben |
| Punkte / Strafleiste / lange Reihen vollendet (Arena, Mittel beider Richtungen) | 47,58 / 9,68 / 2,85 | 49,0 / 9,20 / 2,89 | dieselben |
| Reihen (argmax): volle Reihen, Fuellstand | 0,158, 2,91/6 | 0,148, 2,92/6 | `tor2a_*.json` |
| Strafleiste (argmax) | 5,75 | 5,74 | |
| eigene Punkte (argmax) | 45,49 | 46,80 | |

Laufzeiten: Arena 931 + 920 s (11,6 s je Partie, threads 10, CPU exklusiv,
GPU frei), argmax 1.507 s, Orakel-Laeufe unter einer Minute.

**Verdikt (Lesart par.A4):** b07 liegt bei den beiden arena-validierten
Policy-Metriken auf beiden Orakeln vorn (4 von 4, Abstaende 0,002-0,020),
in der Arena aber NICHT (75:85, p = 0,55, Margin -1,4), und bei den Spalten
in beiden Instrumenten darunter (argmax 0,445 gegen 0,515; Arena -0,075 und
-0,138, jeweils innerhalb einer Block-SE). Das ist die milde Form von par.4a:
tiefes Nachlabeln mit demselben Netz traegt die Spaltenaermut der Tiefe
(`search_depth_column_optimum` par.7) ins Ziel, ohne Staerke zu bringen --
weit weniger drastisch als der Kaltstart b06 (0,18), aber in dieselbe
Richtung. **Zeile-1-Frage beantwortet: Spielen und Labeln reagieren NICHT
unterschiedlich auf Suchtiefe -- beides wird spaltenaermer, und die
Betrags-Daempfung heilt das Nachlabeln nicht** (Value-Spearman und Val-R2
unbewegt). Nach der Generatorwahl-Regel (`generation_loop.md`: Staerke
schliesst nicht aus, Spaltenprofil entscheidet) **bleibt b01 Generator fuer
v24**; Reanalyze wandert NICHT ins v24-Rezept. Teil B (Value) bleibt ohne
Verbraucher (lambda 1,0).

