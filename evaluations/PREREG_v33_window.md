<!-- STATUS: OFFEN | Frage: Wie wird das v33-Fenster zugeschnitten, und traegt der erste Arm? | Beleg: angelegt 2026-09-25 im Generationswechsel v32 -> v33. par.1 steht (Rotation, gezaehlt). par.6 ENTSCHIEDEN: Rezept wie v32, Schwarm a ohne Huellenknopf als `value-tempc-nohull`, Tor 1 beidseits mit start_by_search (v33_gating.spec.json). Erzeugung freigegeben und gestartet 2026-09-25 (par.9). -->

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

## par.8 KOSTEN (aus `docs/measured_runtimes.md`)

Erzeugung: v31 **14,66 h** ohne Nebenlast, v32 **13 h 57** mit Nebenlast (keine saubere
Vergleichsgroesse). Kette: v32 **5 h 34** (Fenster, Monolith, Training 63 min, Tor 1 zwei Seeds).
Zusammen also rund **20 h** bis zum Tor-1-Verdikt.

## par.9 ERZEUGUNG (noch leer)

Pflichtpruefungen direkt nach der Erzeugung, je Klasse:
* **Manifest-Diff** gegen `manifest_v32-b01...` bzw. die v32-Erzeugung: erwartet `model`, `seed`,
  `spec`, `version`, und bei Schwarm a zusaetzlich `spec_file.content.envelope_search_c` 1,0 ->
  0,0 (der Block `spec_file` ist neu, er fehlt in den v32-Manifesten ganz).
* **Wiedervorlage am ersten Record** (Mond- und Rueckgabeknoten mit Lernziel, wie v32 par.9).
* **Tor 0** je Klasse, **Tor 2a** am Sockel, **Vielfaltssonde** an Schwarm a (par.3).
