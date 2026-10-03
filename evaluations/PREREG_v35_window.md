<!-- STATUS: OFFEN | Frage: Wie wird das v35-Fenster erzeugt und zugeschnitten (Schwarm sofort, Sockel nach dem asymmetrischen Bau), und traegt ein Arm? | Beleg: Generator v34-b01, Runde 5 per Netz @400, Spiegelknopf an (par.5). Schwarm erzeugt 2026-10-03 (value-deviate, value-excursion je 4.000), alle Abnahmen GRUEN (par.9). Offen: Sockel nach PREREG_asymmetric_selfplay.md, Fenster, Arme, Tore. -->

# Vorregistrierung: v35-Fenster

**Angelegt 2026-10-02 spaetabends**, waehrend die Promotionskette von `v34-b01` lief
(`tools/v34_promotion_chain.sh`, `PREREG_v34_window.md` par.10d). Nutzer: *"kannst schon alles
vorbereiten dass das self play nach der promotion von selbst startet? zumindest die schwarm daten
solltest ohne weiteres machen koennen"*. Das ist die Freigabe der Erzeugung fuer die zwei
Schwarm-Klassen; die Sockel-Klassen haengen am asymmetrischen Bau und sind NICHT freigegeben.

## par.1 ZUSCHNITT (aus `PREREG_asymmetric_selfplay.md` par.4, Nutzer 2026-10-01)

| Klasse | Paarung | Partien | Stand |
| --- | --- | --- | --- |
| `policy` | G gegen G | 2.000 | nach dem Bau, Seed 20260950 reserviert |
| `policy-dice`, `policy-dice-aggr`, `policy-aggr` | G/W/S | je 2.000 | nach dem Bau und den Sonden S1-S4 |
| `value-deviate` (bis v34 `value-wegc`) | G gegen G, Weg C | 4.000 | **hier, Seed 20260951** |
| `value-excursion` | G gegen G, Ausflug | 4.000 | **hier, Seed 20260952** |
| G-1 / G-2 | -- | 0 | faellt weg (Nutzer 2026-10-01) |

Endgueltige Zusammensetzung nach den Sonden S1-S4. **Seeds:** Vierer-Block 20260950-53 nach v34
(46-49). Zufaellige Namensgleichheit, ohne Wirkung: `PREREG_difficulty_levels.md` plant Arena-Seeds
20260950-54 fuer die GUI-Stufen (anderer Lauf, andere Spieler).

## par.5 ENTSCHIEDEN (Nutzer, mit Beleg)

1. **Generator `v34-b01`** (Champion seit 2026-10-02, `PREREG_v34_window.md` par.10d), eingefroren
   unter `models/frozen_champions/v34-b01`.
2. **Runde 5 per Netz mit 400 R5-Sims, sonst 100** (`PREREG_r5_net_vs_solver.md` par.6f/par.6h,
   Nutzer 2026-10-01: Sim-Frage nur fuer das Self-Play). Kosten +19,2 % je Partie gegen @100 (par.6g dort).
3. **Spiegelknopf an** (`tie_mirror_p` 0,5; Nutzer 2026-10-02: *"wollen ja ein wenig diversitaet"*,
   `PREREG_tie_mirror.md` par.4b).
4. **E1 an, KL-Abzweig im Ausflug an, getrennte Label-RNG, Ausflug-Neumischung** wie v34.
5. Klassenname `value-deviate` statt `value-wegc` (Nutzer 2026-10-01), Flags identisch.
6. **KL-Abzweig im Ausflug bleibt an** (Nutzer 2026-10-03: *"lass ihn an"*), obwohl die Offline-Pruefung
   keinen zuordenbaren Lerneffekt fand (`PREREG_targeted_branching.md` par.7d): er erzeugt andere
   Abzweigstellen ohne Zusatzkosten; gilt fuer alle v35-Klassen mit Ausflug.

## par.6 REZEPT (Schwarm)

`models/v35.recipe.json`: Modell `models/alphazero_v34-b01_brierbest.onnx`, Spec
`models/v35_generation.spec.json` (byte-gleich `v34_gen_r5net_sims400.spec.json`, sha256
`475530fd...`: v33-Erzeugungs-Spec plus `r5_net_solver` 0 und `r5_net_sims` 400), Env wie v34
(`MOSAIC_STACK_DRAW_RESEARCH=1`, `MOSAIC_SINGLE_PASS_OTHER_VAL=1`, `MOSAIC_R5_NET_SOLVER=0`), 100 Sims,
11 Threads, Chunk 10, 10 Partien je Datei, sonst die v34-Flags. Waechter je Klasse
(`excursion_kl_weight` 0 bzw. 1) plus rezeptweit wie v34.

## par.7 START (`tools/night_v35_swarm.sh`)

Wartet, bis die Promotionskette nicht mehr laeuft UND `referee_selftest_v34-b01.json` liegt (sonst
STOPP). Dann: Netz-Paritaets-Fixture (Checkliste 5d, nicht fatal), Tages-Snapshot (nicht fatal),
**Smoke je Klasse** (20 Partien in `data/probe_v35smoke`, Muster `PREREG_v34_window.md` par.7a;
rot = STOPP vor der Erzeugung), dann die Erzeugung. Neu gegenueber dem v34-Smoke ist nur das Feld
`r5_net_sims` in der Erzeugungs-Spec; es lief schon in der Sim-Leiter und im Kostentor ueber
denselben `self_play.py`-Pfad (`PREREG_r5_net_vs_solver.md` par.6e/par.6g), hier erstmals ueber
`--recipe`.

**Abweichung vom Generationswechsel-Ablauf, benannt:** Loeschungen (Schritte 3-5) brauchen
pfadgenaue Freigaben und laufen NICHT automatisch; die STATUS-Neufassung (Schritt 6) folgt waehrend
der Erzeugung (sie beruehrt keine Datei, die der Lauf liest). Fenster-Pinning gilt fuer das
Training, nicht fuer die Erzeugung.

## par.8 ABNAHMEN (nach der Erzeugung, wie `PREREG_v34_window.md` par.4)

Manifest-Diff je Klasse gegen v34, Waechter-Protokoll, Tor 0 je Klasse, `tie_mirrored`-Anteil
(Fenster 47-53 %), KL-Abnahme am Ausflug, `[Watchdog]`-Zeilen je Klasse.

## par.9 ERZEUGUNG UND ABNAHMEN DES SCHWARMS (2026-10-03)

**Erzeugung** (`tools/night_v35_swarm.sh`, startete von selbst nach der Promotionskette): `value-deviate`
05:19-08:06 (10.027,9 s, 2,507 s je Partie), `value-excursion` 08:06-10:01 (6.887,9 s, 1,722 s je Partie,
Ausfluege mitgezaehlt), je 400 Dateien / 4.000 Hauptpartien, beide Exit 0, 11 Threads. **0
Watchdog-, Deadline- oder Haenger-Zeilen.** Gegen v34 (Generator v33-b01, R5 @100): +5,8 % bzw. -6,1 % je
Partie; das Kostentor @400 (+19,2 %, `PREREG_r5_net_vs_solver.md` par.6g) lag bei gleichem Generator,
hier wechselt auch der Generator, die Zahlen sind nicht zerlegt. Nebenlast: drei Elo-Register-Eintraege
liefen 05:12-05:21 mit (gemeldet, ohne Spur in der Ausgabe).

| Abnahme (par.8) | Ergebnis |
| --- | --- |
| Smoke vor dem Start | **GRUEN**, Waechter 6 Knoepfe je Klasse, Manifest traegt `r5_net_sims` 400 |
| Manifest-Diff gegen v34 (`manifest_v33-b01-value-{wegc,excursion}`) | **GRUEN**: nur `cli_args.model/seed/spec/version`, `version`, Rezept-Block, `spec_file` (Inhalt: genau `r5_net_sims` 400 und `r5_net_solver` 0 neu); `engine_config` und `mosaic_env` gleich |
| Tor 0 je Klasse (`corpus_sanity_check.py`) | Exit 0 in beiden Klassen |
| Spiegelknopf | **GRUEN**: 49,18 % (value-deviate, SE 0,79) und 48,75 % (value-excursion, Hauptpartien, SE 1,12) gespiegelt, im Fenster 47-53 %; keine uneinheitliche Partie, keine ohne Feld |
| KL-Abzweig (`PREREG_targeted_branching.md` par.7) | **GREIFT**: Median 1,076 gegen q75 0,800 der Referenz (Quantil 0,829), Spearman `branch_kl`/Werkzeug +0,890; `excursion_kl_acceptance_v35.json` |

Die Werkzeuge `tie_mirror_acceptance.py` und `excursion_kl_acceptance.py` hatten die Klassenliste fest
(`value-wegc`); beide haben seit 2026-10-03 `--classes` (Default unveraendert).

**Sechs Standard-Kennzahlen** (`corpus_sanity_v34-b01-<klasse>.json`, je 8.000 Seiten; Margin per
Konstruktion 0), v34 zum Vergleich (`PREREG_v34_window.md` par.9):

| Kennzahl | value-wegc v34 | **value-deviate v35** | value-excursion v34 | **value-excursion v35** |
| --- | --- | --- | --- | --- |
| volle Reihen / Fuellstand | 0,071 / 2,90 | 0,066 / 2,90 | 0,079 / 2,94 | 0,066 / 2,94 |
| volle Spalten / >= 4 / >= 3 | 0,942 / 2,22 / 3,13 | 0,942 / 2,23 / 3,13 | 1,032 / 2,27 / 3,16 | **1,056** / 2,29 / 3,17 |
| Strafleiste (Steine je Partie und Seite) | 5,71 | 5,64 | 4,97 | 4,88 |
| eigene Punkte | 50,10 | 50,28 | 53,51 | 53,94 |
| Plattenpunkte k1 / k3 / k4 / k5 / k6 | 6,91 / 3,15 / 10,11 / 8,94 / -9,53 | 6,88 / 3,36 / 10,10 / 9,11 / -9,56 | 7,57 / 3,14 / 10,27 / 9,21 / -9,45 | 7,69 / 3,28 / 10,21 / 9,54 / -9,45 |

**Lesart, knapp:** der Schwarm liegt in allen Groessen auf v34-Niveau oder leicht darueber (Ausflug:
mehr volle Spalten, weniger Strafleiste, mehr Punkte). Volle Spalten weiter fast nur links (c0/c1),
gespiegelt wie ungespiegelt. Kein Befund, der die Erzeugung in Frage stellt. Offen: Sockel-Klassen nach
dem asymmetrischen Bau, dann Fenster, Training, Tore.
