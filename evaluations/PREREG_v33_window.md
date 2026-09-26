<!-- STATUS: OFFEN | Frage: Wie wird das v33-Fenster zugeschnitten, und traegt der erste Arm? | Beleg: angelegt 2026-09-25 im Generationswechsel v32 -> v33. par.1 steht (Rotation, gezaehlt). par.6 ENTSCHIEDEN: Rezept wie v32, Schwarm a ohne Huellenknopf als `value-tempc-nohull`, Tor 1 beidseits mit start_by_search (v33_gating.spec.json). Erzeugung laeuft seit 2026-09-25 (par.9). Tor 1 mit Stufenregel (par.2a). Zweiter Arm b02: nur der Schwarm des Generators, A/B gegen b01 im Anschluss (par.6a). -->

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
