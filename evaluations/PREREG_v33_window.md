<!-- STATUS: OFFEN | Frage: Wie wird das v33-Fenster zugeschnitten, und traegt der erste Arm? | Beleg: angelegt 2026-09-25 im Generationswechsel v32 -> v33. par.1 steht (Rotation, gezaehlt). par.6 ENTSCHIEDEN: Rezept wie v32, Schwarm a ohne Huellenknopf als `value-tempc-nohull`, Tor 1 beidseits mit start_by_search (v33_gating.spec.json). Erzeugung abgenommen (par.9). Tor 1 GENAU AUF DER KANTE: 420:380 = 52,50 %, Block-z +1,41, formal getragen (par.10). Fenster-Arme b02/b03/b04 alle ohne messbaren Unterschied (par.6a, par.6d): weder Menge noch Alter des Value-Materials ist ein Hebel. -->

# Vorregistrierung: das v33-Fenster

**Angelegt 2026-09-25** im Generationswechsel v32 -> v33, nach dem Ablauf
`/mosaic-generation-turnover`. Die Generation v32 ist abgeschlossen: `v32-b01` hat Tor 1 getragen
(434:366 aus 800, Block-z +2,37, aber nur auf einem von zwei Seeds) und ist seit dem 2026-09-25
Champion (`PREREG_v32_window.md` par.11).

## par.1 ZUSCHNITT (Rotationsregel, Bestand am 2026-09-25 gezaehlt)

G = v33-Erzeugung durch **`v32-b01_brierbest`**; G-1 = `v31-b01` (die v32-Erzeugung);
G-2 = `v30-b02` (die v31-Erzeugung). **`v29-b11` ist aus der Rotation gefallen** und am 2026-09-25
mit pfadgenauer Freigabe geloescht (1.203 Korpusdateien plus 4 Manifeste, 946 MB; Beleg
restic-Snapshot `373b8404`, 1.203 von 1.203 und 4 von 4; danach 1.203 verwaiste Bloecke, 597 MB).

**Die Generatorwahl ist ohne Konkurrenz:** v32 hatte EINEN Arm, es gilt "Generator = bester Stand
von N-1", und der ist zugleich Champion.

| Generation | Klasse | Dateien (gezaehlt) | ins Fenster | Policy-Ziel |
| --- | --- | --- | --- | --- |
| `v32-b01` (neu) | policy | noch zu erzeugen | 400 | **ja** (alle 400 Traeger) |
| `v32-b01` (neu) | **value-tempc-nohull** (par.6) | noch zu erzeugen | 400 | nein |
| `v32-b01` (neu) | value-excursion | noch zu erzeugen | rund 401 | nein |
| `v31-b01` (G-1) | policy | 400 | 400 | 135 davon |
| `v31-b01` | value-tempc | 400 | 400 | nein |
| `v31-b01` | value-excursion | 401 | 401 | nein |
| `v30-b02` (G-2) | policy | 400 | 400 | 45 davon |
| `v30-b02` | value-excursion | 401 | 145 (Seed-Auswahl) | nein |

**Soll: 2.947 Fensterdateien** (dieselbe Form wie v32), **580 Policy-Traeger** = 400 neu + 135
G-1 + 45 G-2. Die G-2-`value-tempc` (400) geht wie bei v32 NICHT ins Fenster.

**SEED: 20260957** (Vierer-Schritt aus `docs/generation_loop.md`: v30 20260945, v31 20260949,
v32 20260953). **Val-Pool `^selfplay_v32-`** -- trifft ausschliesslich die neuen Klassen, auch
die neue Endung.

## par.2 TORE

Wie `PREREG_v32_window.md` par.2, geerbt aus `PREREG_v30_window.md` par.3 Punkt 5:
**Tor 1** gegen den besten Stand der eigenen Linie (`v32-b01`), zwei Seeds (20261600/20261601) a
200 Paaren, Blockgroesse 5; *"Traegt b01 (z >= +1,96 oder gepoolt >= 52,5 Prozent ohne
Gegenbefund)"*, Block-z auf DIFFERENZIERTEN Blockwerten. **Tor 2a** `sp_voll` des neuen Sockels
gegen den des Vorgaengers (Nicht-Unterlegenheit). **Tor 2b** volle Spalten im Tor-1-Lauf.

**Tor 2a bleibt vergleichbar**, obwohl sich ein Schwarm aendert: es misst den SOCKEL, und der
laeuft wie bisher mit Huellenknopf (`PREREG_geometric_envelope.md` par.14d).

### par.2a STUFENREGEL FUER TOR 1: ein dritter Seed, wenn die beiden ersten sich widersprechen

**Registriert 2026-09-25, VOR jedem Tor-1-Lauf dieser Generation** (Nutzer: *"Registrieren das so
vor und takte es ein"*). Anlass ist die gemessene Aufloesung, nicht ein Wunschergebnis:

* Ein Tor 1 aus zwei Seeds hat 80 Bloecke; bei v32 lag die Block-sd bei 0,1605, der
  Standardfehler des gepoolten Anteils also bei **0,1605 / sqrt(80) = 1,8 Prozentpunkten**
  (Herleitung aus par.10 der v32-Prereg; sie reproduziert dort z = +2,37). Ein echter Sprung von
  3 Punkten landet damit im Mittel bei z = 1,7 -- unter der Schwelle.
* Die Seeds streuen stark: v32 +0,10 gegen +3,26, v31 +3,54 gegen +2,42.

**Die Regel:**

1. Tor 1 laeuft wie in par.2 auf den Seeds 20261600 und 20261601.
2. **Ausloeser:** GENAU EINER der beiden Seeds erreicht einzeln Block-z >= +1,96. (v32 haette
   ausgeloest, v31 nicht.)
3. Dann laeuft **Seed 20261602** mit identischen Einstellungen.
4. **Verdikt:** gepoolter Block-z ueber ALLE gelaufenen Seeds, mit dem unveraenderten Kriterium
   aus par.2 (z >= +1,96 oder gepoolt >= 52,5 Prozent, ohne Gegenbefund). Alle Einzel-z werden
   berichtet.
5. Rechnung: `tools/gating_block_z.py`, geeicht am 2026-09-25 gegen die sechs registrierten
   Werte von v31 und v32 (`--check-v31-v32`, 6 von 6 exakt).

**Was die Regel NICHT ist, ehrlich benannt:** ein fester Umfang. Sie fuegt Daten nur im
Widerspruchsfall hinzu; ihr Fehler erster Art ist damit nicht genau der eines Tests mit festem n.
Bewusst in Kauf genommen, weil der dritte Seed in BEIDE Richtungen wirken kann (ein Widerspruch
kann gepoolt auch unter die Schwelle fallen) und weil ein fester dritter Seed jede Generation
rund 2 h kostete (v32: 7.251 s je Seed). Ob die Regel Pflicht fuer spaetere Generationen wird,
entscheidet sich nach diesem Einsatz, nicht jetzt.

**Zur Entscheidung gestellt, noch am selben Tag** (Nutzer: *"Mehrkosten sind kritisch
abzuwaegen"*): ob die Regel fuer v33 ueberhaupt gilt, entscheidet der Nutzer VOR dem Start der
Kette (`STATUS.md` Abschnitt 6, Punkt 15). Faellt sie, wird der Block 8b aus `night_v33_chain.sh`
entfernt, bevor die Kette startet.

**ENTSCHIEDEN 2026-09-26: die Regel gilt fuer v33** (Nutzer auf die Vorlage mit Stufenregel und
Kettenstart: *"Setz es um wie vorgeschlagen"*). Block 8b bleibt in der Kette.

## par.3 DER EINE INHALTLICHE UNTERSCHIED ZU v32

**Schwarm a laeuft ohne Huellenknopf** (Nutzer-Entscheid 2026-09-25 auf Koordinator-Empfehlung,
`PREREG_geometric_envelope.md` par.14d). Der Ausflug bleibt huellen-an, weil er die einzige
Klasse mit unverzerrten Value-Zielen ist.

**Abnahme, vorab festgelegt:** die Vielfaltssonde (`tools/probes/corpus_state_diversity_probe.py`)
auf dem neuen `value-tempc-nohull` gegen `v31-b01-value-tempc` (G-1, huellen-an). **Vorbehalt:**
die beiden unterscheiden sich AUCH im Generator, der Vergleich ist nicht rein einfaktoriell.
**Zeigt die Sonde praktisch keinen Unterschied, war der temperierte Schwarm der falsche Ort**
(par.14d). **Noch zu klaeren:** das Werkzeug nimmt zwei Verzeichnisse, die Korpora liegen flach in
`data/`.

**Nebenfaktor, wie bei v32 benannt:** die Generationen im Fenster sind unter verschiedenen Wheels
entstanden (G-2 unter 1.0.0 oder frueher, G-1 unter 1.1.0 `e11ea6d5`, G unter 1.1.0 `46b5dfed` mit dem
GUI-Tor aus `PREREG_dome_return_order.md` par.14b). Das GUI-Tor aendert den Self-Play-Pfad NICHT
(die Spielschleife setzt das Tor seit R3 selbst); Anker-Drift und -Konservierung sind ueber den
Wechsel gruen.

## par.6 REZEPT -- VORLAGE, braucht Nutzer-Entscheide vor dem Start

### Erzeugung: `tools/night_v33_generate.sh`

Fortschreibung von `night_v32_generate.sh`. Geaendert sind genau vier Dinge:

| | v32-Erzeugung | **v33-Erzeugung** |
| --- | --- | --- |
| Generator | `alphazero_v31-b01_brierbest.onnx` | **`alphazero_v32-b01_brierbest.onnx`** |
| Seeds (Sockel / Schwarm a / Ausflug) | 20260938 / 39 / 40 | **20260942 / 43 / 44** |
| Spec (Sockel, Ausflug) | `v31_generation.spec.json` | **`v32_generation.spec.json`**, byte-gleich (sha256 `4a3f9db3...`) |
| Schwarm a | `value-tempc`, Spec wie oben | **`value-tempc-nohull`, `v32_generation_nohull.spec.json`** (einziger Unterschied `envelope_search_c: 0.0`, sha256 `ada4238c...`) |

Alles andere wie v32: 3 x 4.000 Partien, 100 Sims, 11 Threads, `--chunk 10`, `--per-file 10`,
`--start-slot-random-p 0.15`, `--return-order-random-p 0.81`, `MOSAIC_STACK_DRAW_RESEARCH=1`;
Klassen-Flags unveraendert. Das Skript prueft vor dem Start, dass sich die beiden Specs in GENAU
diesem einen Feld unterscheiden, und dass das Lauf-Manifest die Spec mitschreibt.

### Fenster, Training, Tor 1: `tools/night_v33_chain.sh`

Fortschreibung von `night_v32_chain.sh` mit den Namen und Seeds aus par.1/par.2. **Trainingsrezept
unveraendert** (Referenz `models/manifest_train_v32-b01_20260923_075819.json`): warm von
`v32-b01_brierbest`, 12 Epochen, lr 5e-5 cosine, WDL-Kopf, nortv, lambda 0,7, `--select-by-brier`.
Die Kette diffed das Trainings-Manifest gegen diese Referenz; erwartet sind genau `load`, `name`,
`file_list`, `cache_file`, `seed`, `val_pool`.

### ZWEI ENTSCHEIDE -- GEFALLEN 2026-09-25

**Nutzer: *"1 und 2 wie vorgeschlagen, starte die Erzeugung"*.** Damit gilt: Klassenname
`value-tempc-nohull`, Tor 1 auf `models/v33_gating.spec.json` beidseits, und die Erzeugung ist
freigegeben. Die Begruendungen, wie sie vorgelegt waren:

1. **Klassenname `value-tempc-nohull`** statt Weiterfuehrung von `value-tempc`. Fuer den neuen
   Namen spricht: ab v33 traegt jede spaetere Fensterliste den Unterschied im Dateinamen, und die
   G-1-Klasse gleichen Zwecks ist davon unterscheidbar. Dagegen: Werkzeuge, die nach
   `-value-tempc_` suchen, finden die neue Klasse nicht (die v33-Kette ist nachgezogen; andere
   Sonden ungeprueft).
2. **Tor 1 auf `models/v33_gating.spec.json` BEIDSEITS** -- die Champion-Spec von `v32-b01` plus
   `start_by_search: 1` (sha256 `aa5cf25f...`) -- **byte-gleich mit
   `models/start_by_search_on.spec.json`**, also genau der Spec, auf der der Such-Start am
   2026-09-12 gemessen wurde (`PREREG_start_dome_choice.md` par.9e: 91:99, gleichwertig). Grundlage: `PREREG_start_dome_choice.md` par.12,
   *"Knopf ab v33"*. Laeuft Tor 1 schon so, ist die gemessene Identitaet die, die bei einer
   Promotion spielt; sonst stuende bei der v33-Promotion dieselbe Frage wie bei v32. Dagegen: der
   Tor-1-Gegner `v32-b01` spielt dann mit einer Spec, auf der er nicht promoviert wurde -- fair,
   weil beidseits gleich, aber eine andere Konfiguration als die seiner eigenen Kanten.

**Die Freigabe der Erzeugung** ist mit demselben Satz erteilt.

## par.6a ZWEITER ARM `v33-b02`: nur der Schwarm des Generators (registriert 2026-09-25, VOR jedem Lauf)

**Nutzer:** *"Ich bin mir nicht sicher ob ein groesseres trainingsfenster hilft. Der value head ist
klein und schlussendlich ist es nur eine regression"*, dann *"Dann fahr Im Anschluss eine a/b
Partie mit weniger Schwarm Anteil (zb nur die 8000 vom aktuellen champ)"*.

**Die Frage:** traegt der AELTERE Schwarm (G-1 und G-2) im Fenster zur Staerke bei, oder ist er
Ballast? Belegt ist bisher nur, dass mehr Partien DERSELBEN Aera helfen (Task #36,
`PREREG_corpus_dose.md`, beide aus einer aelteren Encoder-Aera); ob mehr ALTE Partien helfen, ist
ungemessen, und "Aera >> Dosis" (`PREREG_v25_window.md`) spricht eher dagegen.

**Der eine Unterschied zu b01:** das Fenster verliert den Schwarm aus G-1 und G-2.

| Fenster | b01 (par.1) | **b02** |
| --- | --- | --- |
| neu `v32-b01`: policy / tempc-nohull / Ausflug | 400 / 400 / ~401 | 400 / 400 / ~401 (gleich) |
| G-1 `v31-b01`: policy | 400 | 400 (gleich) |
| G-1 `v31-b01`: tempc / Ausflug | 400 / 401 | **0 / 0** |
| G-2 `v30-b02`: policy | 400 | 400 (gleich) |
| G-2 `v30-b02`: Ausflug (Seed-Auswahl) | 145 | **0** |
| **Summe** | **2.947** | **2.001** |

Policy-Traeger unveraendert (580, dasselbe Manifest). Gleiches Rezept, gleicher Warmstart
(`v32-b01_brierbest`), gleicher Trainings-Seed. **Die Val-Menge ist IDENTISCH:** die Aufteilung
zieht n_val = round(N * val_frac) aus demselben Pool (`^selfplay_v32-`, 1.201 Dateien in beiden
Fenstern) mit festem Seed (`tools/window_train_split.py` Z.78-83, `train.py` Z.1430); das Skript
rechnet `--val-frac` fuer b02 aus der TATSAECHLICHEN b01-Val-Liste und der tatsaechlichen
b02-Fenstergroesse (bei 2.947/2.001 Dateien: 147 Val-Dateien), damit n_val gleich ist -- ein
fester Wert haette bei einer anderen Ausflug-Dateizahl eine andere Val-Menge ergeben. Das Skript bricht ab, wenn die Val-Liste nicht
byte-gleich zu `data/window_v33_val.txt` ist. **Unvermeidliche Nebenfolge, benannt:** mit weniger
Daten macht dieselbe Epochenzahl weniger Gradientenschritte -- das GEHOERT zur Frage "weniger
Material", es ist kein Stoerfaktor, der sich abstellen liesse.

**Messung:** gepaartes A/B `v33-b02` gegen `v33-b01`, beide mit `models/v33_gating.spec.json`, 400
Sims, zwei Seeds (20261650, 20261651) a 200 Paare, Blockgroesse 5, `--log-games`, Block-z ueber
`tools/gating_block_z.py` (A = b02).

**Leseregel, VORAB:**

* **z <= -1,96: der aeltere Schwarm TRAEGT.** Fenstertiefe hilft dem Value-Kopf; Volumen bleibt der
  Hebel, auch aelteres.
* **z >= +1,96: der aeltere Schwarm SCHADET.** Die v34-Fenster werden ohne ihn gebaut.
* **dazwischen: kein messbarer Beitrag.** Dann ist b02 bei gleicher Staerke das billigere Fenster
  (rund ein Drittel weniger Dateien, kuerzerer Merge und kuerzeres Training); ob es ab v34 Rezept
  wird, entscheidet der Nutzer.
* Zweitrangig, berichtet: Val-Brier beider Arme (identische Val-Menge) und die sechs
  Standard-Kennzahlen.

**Was das A/B NICHT entscheidet:** den v33-Champion. Eine Promotion laeuft nur ueber Tor 1 gegen
den amtierenden Champion; b02 braeuchte dafuer ein eigenes Tor 1.

**Wann und was es kostet:** im Anschluss an die v33-Kette, `bash tools/night_v33_b02.sh`.
Geschaetzt (HERLEITUNG aus v32, nicht gemessen): Merge rund 7 min, Training rund 45 min, A/B
2 x rund 2 h -- zusammen rund 5 h, also der Gegenwert von rund 4.400 Self-Play-Partien.

**NACHTRAG 2026-09-26, 17:55, VOR dem dritten Seed: Entscheidungsseed.** Die beiden Seeds
widersprechen sich: 20261650 **134:156, Block-z -1,61** (SPRT-Fruehstopp nach 145 von 200 Paaren,
29 Bloecke), 20261651 **229:171, Block-z +3,09** (40 Bloecke); gepoolt +1,45 (69 Bloecke).
In Seed 20261651 lief ab etwa Block 6 bis 17 Nebenlast des Koordinators (STATUS); eine exklusive
Wiederholung ergab **Block 1-17 IDENTISCH** zum Original (kumulative Siege und Paar-Aufteilung je
Block, 17 von 17) und wurde danach abgebrochen (Artefakt-Teillauf
`ab_v33-b02_vs_v33-b01_s20261651_rerun.json` unvollstaendig). Das Lastfenster ist damit
abgedeckt; **Seed 20261651 gilt unveraendert.** Nutzer: *"Ob der
rerun von b02 sinnvoll ist wage ich zu bezweifeln. Da waere ein entscheidungseed sinnvoller
gewesen"*. **Daher: dritter Seed 20261652, fester Umfang 200 Paare** (SPRT-Schranken bei
alpha = beta = 1e-12, praktisch unerreichbar). **Verdikt:** gepoolter Block-z ueber ALLE DREI Seeds
mit der Leseregel oben (<= -1,96 / >= +1,96 / dazwischen). Die Einzel-z werden berichtet.

### par.6a ERGEBNIS (2026-09-26, 14:17-19:53)

Training `v33-b02` 13:39-14:17 (brierbest Epoche 3, `val_brier` 0,1835 gegen b01 0,1837 auf
derselben Val-Menge). A/B `v33-b02` gegen `v33-b01`, Spec `v33_gating` beidseits, Blockgroesse 5:

| Seed | b02 : b01 | Bloecke | Block-z | volle Spalten b02 / b01 |
| --- | --- | --- | --- | --- |
| 20261650 | 134:156 | 29 (SPRT-Fruehstopp nach 145 Paaren) | -1,61 | 1,007 / 1,000 |
| 20261651 | 229:171 | 40 (Nebenlast Block 6-17; Wiederholung Block 1-17 identisch) | +3,09 | 1,078 / 0,948 |
| 20261652 (Entscheidungsseed, fester Umfang) | 211:189 | 40 | +1,00 | 1,083 / 1,048 |
| **gepoolt** | **574:516** | 109 | **+1,76** | |

**Verdikt nach der Leseregel: DAZWISCHEN -- kein messbarer Beitrag des alten Schwarms.** b02 ist
bei gleicher Staerke das billigere Fenster (Nutzer-Entscheid fuer v34). Richtung: b02 liegt in zwei
von drei Seeds vorn und baut leicht mehr volle Spalten; das ist keine Freigabe fuer "alter Schwarm
schadet". Einschraenkung par.6b: getestet ist alter SCHWARM, nicht altes Material. Elo-Register:
drei Zeilen 2026-09-26. **Folge fuer b03 (par.6b): Basis b02, Gegner b01.**

## par.6b DRITTER ARM `v33-b03`: 4.000 Schwarm-Partien MEHR aus der aktuellen Generation (registriert 2026-09-26, VOR dem b02-Ergebnis)

**Nutzer 2026-09-26:** *"Je nachdem was bei b02 rauskommt wuerd ich b03 registrieren mit 4000 mehr
schwarmdaten aus der aktuellen Generation"*. b02 misst, was WENIGER Schwarm kostet (ohne G-1/G-2),
b03 misst, was MEHR Schwarm vom aktuellen Generator bringt. Zusammen beantworten sie die Frage
"mehr Spiele?" in dieser Aera (die Volumenbelege `PREREG_corpus_dose.md` und task36 stammen aus
der v20-Aera).

**Material:** 4.000 zusaetzliche Partien vom Generator `v32-b01_brierbest` (derselbe wie die
v33-Erzeugung, also "aktuelle Generation"). **Klasse ENTSCHIEDEN 2026-09-26: `value-wegc`** --
die Sockel-Einstellung (`--tau-argmax-from-move 1 --deviate-prob 1.0 --start-slot-random-p 0.15
--return-order-random-p 0.81`, Spec `models/v32_generation.spec.json`, 100 Sims) mit
`--value-only`, eigener Seed 20260945. Nutzer: *"Die frage ist dann eigentlich nur, Ausflug oder.
Weg c"*, auf die Vorlage *"Ausserdem wollen wir die Ausflug klasse ja umbauen vom abzweigort"*.
Begruendung (am Korpus nachgezaehlt 2026-09-26): die Ausflug-Klasse speichert PAARE (je Datei
5 Hauptpartien ohne Abweichung plus 5 Ausfluege `_x1`), deren verdeckte Zukunft geteilt ist
(Review-Befund #14); aus 4.000 Ausflugs-Partien werden nur 2.000 Abzweige. Weg C liefert 4.000
unabhaengige, je einmal abgewichene Partien mit argmax-Fortsetzung (unverzerrtes Ziel), und der
Ausflug wird ohnehin beim Abzweigort umgebaut (`PREREG_targeted_branching.md`). Kosten gemessen am
Sockel: 16.577 s je 4.000 Partien.

**Zuschnitt, abhaengig vom b02-Ergebnis (par.6a):**
* b02 **z <= -1,96** (aelterer Schwarm traegt): **b03 = Fenster von b01 + die 4.000 neuen**.
* b02 **z >= +1,96** (aelterer Schwarm schadet): **b03 = Fenster von b02 + die 4.000 neuen**
  (nur frisches Material, dafuer mehr davon).
* **dazwischen:** b03 = Fenster von b02 + die 4.000 neuen (gleich stark und billiger als der alte
  Schwarm; b03 prueft, ob frisches Volumen traegt, wo altes es nicht tat). Nutzer kann vor dem Start
  anders entscheiden.

**Alles andere wie b01:** dieselbe Val-Menge (die neuen Dateien gehen ganz ins Training; das
Skript prueft die Val-Liste byte-gleich wie `night_v33_b02.sh`), dasselbe Rezept, Startgewicht,
Trainings-Seed 20260957, `--val-frac` dynamisch, Tor-1-Spec `models/v33_gating.spec.json`.

**Messung:** A/B **b03 gegen b01**, zwei Seeds (20261660, 20261661) a 200 Paare, Blockgroesse 5,
`--log-games`, Block-z ueber `tools/gating_block_z.py`. **Fester Umfang:** SPRT-Schranken bei
alpha = beta = 1e-12 (+-27,6), bei 200 Paaren praktisch unerreichbar -- das b02-A/B hatte mit
0,001 Seed 1 nach 145 von 200 Paaren gestoppt. Skript: `tools/night_v33_b03.sh b01|b02`.
**Leseregel, VORAB:** z >= +1,96: **mehr frischer Schwarm traegt** -> v34 bekommt die zusaetzliche
Klasse (Kosten rund +4 h Erzeugung je Generation). Dazwischen: Volumen ist in dieser Aera kein
Hebel mehr; der naechste Kandidat ist das gezielte Abzweigen (`PREREG_targeted_branching.md`).
z <= -1,96: mehr Material schadet -- dann Diagnose vor jeder weiteren Fensterentscheidung.

**NACHTRAG 2026-09-26, VOR dem b02-Verdikt: GEGNER von b03 bedingt** (Nutzer auf die Frage, was ein
b02-Sieg aussagt: *"Weniger Schwarm besser? Weniger Schwarm alter Champs besser?"*, auf die
Vorlage: *"Mach das"*). Ein b02-Sieg vermischt zwei Ursachen -- weniger Schwarm ueberhaupt (der
Sockel wiegt mehr) und alter Schwarm (Wertziele unter schwaecherem Spiel). Getrennt werden sie nur,
wenn b03 dann gegen b02 spielt:
* **b02 gepoolt z >= +1,96 (ueber alle drei Seeds, par.6a Nachtrag):** Basis b02, **Gegner b02**.
  b03 gewinnt -> frisches Volumen traegt, am alten Schwarm schadete das ALTER; gleich -> mehr
  Schwarm bringt nichts, der Anteil ist ausgereizt; b03 verliert -> WENIGER Schwarm ist an sich
  besser, der Sockel soll mehr Gewicht haben. Gleiche Schwellen (+-1,96).
* **sonst:** Basis nach der Regel oben, Gegner b01, Leseregel wie oben.
Aufruf: `bash tools/night_v33_b03.sh <basis b01|b02> <gegner b01|b02>`; der Manifest-Diff des
Trainings vergleicht unabhaengig vom Gegner gegen das b01-Rezept.

**EINSCHRAENKUNG (Nutzer 2026-09-26: *"Nur sind im Schwarm von b02 noch immer maskierte policy games
von g-1 und g-2 drinnen"*):** das b02-Fenster enthaelt weiter ALTES Value-Material ueber den
Sockel von G-1 und G-2 (je 400 Dateien; davon 620 policy-maskiert, also reine Wertziele, 265 G-1 und
355 G-2, plus 180 Policy-Traeger, 135 + 45; Traeger-Assert `night_v33_chain.sh` Schritt 2).
**b02 gegen b01 testet damit "alter SCHWARM", nicht "altes Material"**; ein Alters-Schluss aus
b02 oder b03 gilt nur fuer den Schwarm. Ein sauberer Alterstest waere ein eigener Arm
(Vorschlag `v33-b04`): b02-Fenster minus die 620 policy-maskierten alten Sockel-Dateien, die 180
alten Traeger bleiben (Policy wie v32). Registriert als par.6c.

## par.6c VIERTER ARM `v33-b04`: nur frische Wertziele (registriert 2026-09-26, VOR jedem b04-Lauf)

**Nutzer 2026-09-26:** *"Mal schauen was b03 bringt. Sauberer waere es"*, dann *"Bzw. Kannst b04
parallel trainieren"* und *"Das kann nebenbei laufen"*.

**Frage:** schadet ALTES Value-Material an sich (Wertziele unter dem Spiel schwaecherer
Generatoren)? b02 hat nur den alten SCHWARM entfernt (par.6b Einschraenkung).

**Fenster:** `data/window_v33_b02.txt` minus die **policy-maskierten** Sockel-Dateien von G-1
(`selfplay_v31-b01-policy_*`) und G-2 (`selfplay_v30-b02-policy_*`), also alle alten Sockel-Dateien,
die NICHT in `data/policy_carrier_manifest_v33.json` stehen. **Soll: 620 entfernt (265 G-1, 355
G-2), 180 alte Traeger bleiben (135 + 45)**; das Skript bricht bei Abweichung ab. Die Policy lernt
damit exakt wie in b01/b02 (dieselben 580 Traeger); das Value-Material stammt bis auf die 180
alten Traeger nur aus der aktuellen Generation.

**Alles andere wie b02:** dieselbe Val-Menge (alte Sockel-Dateien liegen nicht im Pool
`^selfplay_v32-`, `--val-frac` dynamisch, Abbruch bei nicht byte-gleicher Val-Liste), Rezept,
Warmstart `v32-b01_brierbest`, Trainings-Seed 20260957.

**Messung: b04 gegen b02** (einziger Unterschied die 620 Dateien), zwei Seeds (20261680, 20261681)
a 200 Paare, fester Umfang (SPRT alpha = beta = 1e-12), Blockgroesse 5, `--log-games`, Block-z ueber
`tools/gating_block_z.py`. **Leseregel, VORAB (A = b04):**
* z >= +1,96: **altes Value-Material schadet** -> v34-Fenster ohne alte Nicht-Traeger.
* z <= -1,96: **altes Value-Material traegt** (Fenstertiefe hilft) -> bleibt.
* dazwischen: kein messbarer Beitrag -> v34 kann es weglassen (billiger), Nutzer-Entscheid.

**Ablauf, parallel zu b03** (`tools/night_v33_b03_b04.sh`, working_rules "GPU und CPU duerfen
parallel"): b04-Fenster und Monolith vor der b03-Erzeugung; b04-Training (GPU) WAEHREND der
b03-Erzeugung (CPU, 10 statt 11 Threads); b04-A/B (CPU) WAEHREND des b03-Trainings (GPU); danach
b03-A/B. Laufzeiten dieser parallelen Schritte sind als *unter Nebenlast* markiert und keine
Planungsgroessen. **Kosten** (Herleitung aus b02): Fenster/Monolith rund 10 min, Training rund
45 min, A/B rund 3,4 h -- zusaetzlich zu b03 rund 10 min Maschinenzeit, der Rest faellt in
Parallelphasen.

**Kosten (Herleitung aus par.9 und der v33-Kette):** Erzeugung rund 4,6 h (Sockel-Einstellung
16.577 s je 4.000 Partien), Bloecke, Monolith und Training rund 1,5 h, A/B rund 3,4 h: **rund 9,5 h**. Laeuft mit
dem heutigen Wheel, also VOR der Wheel-Runde (E1, E4, Review-Fixes, Spiegelknopf); die verschiebt
sich entsprechend.

## par.6d ERGEBNISSE b03 und b04 (Kette `tools/night_v33_b03_b04.sh b02 b01`, 2026-09-26 19:59 bis 2026-09-27 08:09)

Ablauf ohne Stopp; Manifest-Diffs beider Trainings: 0 unerwartete Abweichungen; Val-Menge beider
Arme identisch mit b01 (147 Dateien). Laufzeiten der Parallelphasen UNTER NEBENLAST: b03-Erzeugung
`value-wegc` 20:02-00:44 (400 Dateien, 10 Threads, parallel zum b04-Training 4.507 s),
b03-Training 4.307 s parallel zum b04-A/B. Tor 0 `value-wegc`: 0,974 volle Spalten je Seite.

| Arm | Gegner | Seed | Ergebnis | Block-z | volle Spalten A / B |
| --- | --- | --- | --- | --- | --- |
| b04 | b02 | 20261680 | 197:203 | -0,29 | 1,003 / 1,028 |
| b04 | b02 | 20261681 | 202:198 | +0,21 | 1,078 / 1,055 |
| **b04 gepoolt** | | | **399:401** | **-0,07** | |
| b03 | b01 | 20261660 | 190:210 | -0,88 | 1,043 / 1,008 |
| b03 | b01 | 20261661 | 221:179 | +2,38 | 0,958 / 0,945 |
| **b03 gepoolt** | | | **411:389** | **+0,75** | |

Val-Brier (dieselbe Val-Menge): b01 0,1837, b02 0,1835, b03 0,1834 (Epoche 9), b04 0,1843
(Endmodell = bestes). Elo-Register: vier Zeilen 2026-09-27.

**Verdikte nach den Leseregeln:**
* **b04 (par.6c): DAZWISCHEN -- altes Value-Material hat keinen messbaren Beitrag.** v34 kann die
  620 policy-maskierten alten Sockel-Dateien weglassen (billiger), Nutzer-Entscheid.
* **b03 (par.6b, Gegner b01): DAZWISCHEN -- mehr frisches Volumen ist in dieser Aera kein Hebel.**
  Nach der Leseregel ist der naechste Kandidat das gezielte Abzweigen
  (`PREREG_targeted_branching.md`).

**Gesamtbild der vier Arme:** b01 (2.947 Dateien), b02 (ohne alten Schwarm, 2.001), b03 (b02 plus
4.000 frische Partien) und b04 (nur frische Wertziele, 1.381) sind in der Arena ununterscheidbar,
und ihr Val-Brier liegt innerhalb von 0,001. Die Fensterzusammensetzung ist in dieser Aufloesung
KEIN Hebel mehr -- weder Menge noch Alter des Value-Materials. Das widerspricht der
Volumen-Folgerung aus task36/corpus_dose (v20-Aera) fuer die heutige Aera und stuetzt die
Saettigungs-These des Nutzers ("mit unserer aktuellen Architektur in der Saettigung"). Bericht an
den Verbraucher: `PREREG_targeted_branching.md`, STATUS Abschnitt 6 Punkt 14.

## par.8 KOSTEN (aus `docs/measured_runtimes.md`)

Erzeugung: v31 **14,66 h** ohne Nebenlast, v32 **13 h 57** mit Nebenlast (keine saubere
Vergleichsgroesse). Kette: v32 **5 h 34** (Fenster, Monolith, Training 63 min, Tor 1 zwei Seeds).
Zusammen also rund **20 h** bis zum Tor-1-Verdikt.

## par.9 ERZEUGUNG (gefahren 2026-09-25/26)

Pflichtpruefungen direkt nach der Erzeugung, je Klasse:
* **Manifest-Diff** gegen `manifest_v32-b01...` bzw. die v32-Erzeugung: erwartet `model`, `seed`,
  `spec`, `version`, und bei Schwarm a zusaetzlich `spec_file.content.envelope_search_c` 1,0 ->
  0,0 (der Block `spec_file` ist neu, er fehlt in den v32-Manifesten ganz).
* **Wiedervorlage am ersten Record** (Mond- und Rueckgabeknoten mit Lernziel, wie v32 par.9).
* **Tor 0** je Klasse, **Tor 2a** am Sockel, **Vielfaltssonde** an Schwarm a (par.3).

**Erzeugung:** `tools/night_v33_generate.sh`, Exit 0 am 2026-09-26 04:23:55, Dateien gezaehlt:
`policy` 400, `value-tempc-nohull` 400, `value-excursion` 401. Laufzeiten aus den Manifesten
(je 4.000 Partien, threads 11): 16.577,0 s / 16.436,1 s / 13.753,9 s, zusammen **12,99 h**.
Der Ausflug lief mit 3,43 s je Partie deutlich schneller als bei v32 (4,36 s); Ursache
UNGEKLAERT, nichts lief daneben.

| Pruefung | Ergebnis |
| --- | --- |
| Manifest-Diff je Klasse gegen die v32-Erzeugung (`manifest_v31-b01-*`) | **GRUEN**: je 11 Felder, davon inhaltlich genau `cli_args.model`, `.seed`, `.spec`, `.version` und `version`; der Rest ist `git_commit`, `laufzeit.*`, `run_timestamp`. `spec_file` ist neu; `content.envelope_search_c` = **0,0** bei `value-tempc-nohull` (sha `ada4238c`), **1,0** bei Sockel und Ausflug (sha `4a3f9db3`). Kein stiller Default. |
| Wiedervorlage am Record (`tools/count_new_nodes_in_corpus.py`, je 10 Dateien, Seed 20260945) | **GRUEN** in allen drei Klassen: Mondknoten 406-410 mit Ziel in 11,63 / 11,95 / 11,39 % der Records, Rueckgabeknoten 411-413 in 40 / 17 / 18 Records, 0 Records mit leerem Policy-Ziel. Artefakte `new_nodes_v32-b01-*.json` |
| **Tor 2a** (`corpus_sanity_check.py`, Sockel, n = 8.000 Seiten) | `sp_voll` **0,966 (+-0,017)** gegen **0,977 (+-0,017)** bei `v31-b01` -- **HAELT** (Nicht-Unterlegenheit); erstmals seit v25 mit Richtung nach unten (-0,011, innerhalb der Streuung). Artefakt `corpus_sanity_v32-b01-policy.json`, 278,7 s |
| **Vielfaltssonde** Schwarm a (par.3) | verschiedene (Runde, Brettmaske)-Zustaende **100.894** ohne Knopf gegen **99.775** mit Knopf (G-1), je 4.000 Partien: **+1,1 %**; Endbretter 96,7 % gegen 95,9 % verschieden. **Praktisch kein Unterschied** -- nach der Leseregel in par.3 war der temperierte Schwarm der falsche Ort fuer den Knopf (der vorab benannte Gegenpunkt aus `PREREG_geometric_envelope.md` par.14d trifft zu). Eine Generator-Kontrolle (v30 -> v31) ist nicht gefahren: sie kann +1,1 % nicht mehr zu einem Befund machen. Artefakt `diversity_v32-b01-tempc-nohull_vs_v31-b01-tempc.json`, **4.482,8 s** |
| **Tor 0** der Schwarm-Klassen | laeuft als Schritt 1 der Kette (`night_v33_chain.sh`) |

## par.10 TOR 1 (gefahren 2026-09-26, 10:07-13:33, `tools/night_v33_chain.sh`)

`v33-b01_brierbest` gegen den Champion `v32-b01_brierbest`, Spec `models/v33_gating.spec.json`
beidseits (Startkuppel-Suche an), je Seed 200 Paare, Blockgroesse 5, SPRT ohne Entscheid (Deckel).
Block-z aus `tools/gating_block_z.py` (Kette Schritt 8b), Elo-Register 2026-09-26 (zwei Zeilen).

| Seed | v33-b01 : v32-b01 | Block-z | gepaarte Diff je Paar | volle Spalten je Seite (Tor 2b) | Punkte |
| --- | --- | --- | --- | --- | --- |
| 20261600 | **212:188** | +1,32 | +0,120 [-0,066; +0,306] | 1,045 gegen 0,988 | 59,14 gegen 57,52 |
| 20261601 | **208:192** | +0,73 | +0,080 [-0,108; +0,268] | 1,003 gegen 1,133 | 59,94 gegen 60,23 |
| gepoolt | **420:380 = 52,50 %** | **+1,41** | | 1,024 gegen 1,060 | |

Stufenregel (par.2a): kein Seed einzeln >= +1,96, also kein dritter Seed.

**Verdikt nach par.2: das Kriterium "gepoolt >= 52,5 Prozent ohne Gegenbefund" ist GENAU AUF DER
KANTE erfuellt** (420 von 800; eine Partie weniger haette es gerissen). Statistisch ist der
Vorsprung nicht gesichert (z +1,41). Tor 2b zeigt keinen einheitlichen Befund: Seed 1 mehr volle
Spalten, Seed 2 weniger (-0,13, einzeln nicht signifikant bei +-0,07 je Seite); gepoolt liegt v33
leicht darunter. Als Gegenbefund im Sinne von par.2 ist das nicht registriert, als Warnzeichen
schon. Der Sprung ist kleiner als bei v32 (54,25 %, z +2,37).

**Tor 0 der Schwarm-Klassen** (Kette Schritt 1, `corpus_sanity_check.py`, je 4.000 Partien):
`value-tempc-nohull` 0,598 volle Spalten je Seite, 42,41 Punkte; `value-excursion` 1,036 / 55,30.
Beide Exit 0.

**Promotion:** Nutzer-Entscheid. Vorschlag des Koordinators: erst nach dem b02-A/B (par.6a),
das heute Abend fertig ist -- traegt b02 gegen b01, ist b02 der Kandidat, und die Promotion kostet
nur einmal rund 2,3 h.
