<!-- STATUS: OFFEN | Frage: Traegt das v35-Fenster (fuenf v34-b01-Klassen, Modus-2-Sockel, W-v2, Wertmaske) ein Netz, das v34-b01 schlaegt? | Beleg: TRAGEN gegen v34-b01 (gepoolt): b02 56,8 % z +4,07 (par.12e), b03 58,6 %, b05 56,4 %, b06 56,9 % (par.13), b04 56,2 % (par.14c), **b10 (Schwarm als Policy-Traeger) 60,9 % z +6,22, staerkste Kante (par.18b)**, **b09 (Policy-Volumen) 59,1 % z +4,15 (par.17c)**; b07 NICHT (par.15b); b08 EMA ohne Gewinn (par.16a). Policy-Kopf stichprobenbegrenzt. Keine Promotion (Nutzer). Naechster Schritt b11-b15 (par.19). -->

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
| `policy-dice`, `policy-aggr` | G gegen W, G gegen S | je 2.000 | nach dem Bau und den Sonden S1-S4 (W gegen S gestrichen, `PREREG_asymmetric_selfplay.md` par.4a) |
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

## par.10 SOCKEL (REGISTRIERT 2026-10-04 13:25 vor dem Start; Nutzer: *"den mischsockel kannst schon starten"*)

Rezept `models/v35_sockel.recipe.json` (aus dem Entwurf der Nacht umbenannt), Generator `v34-b01_brierbest`, Spec
`models/v35_generation.spec.json`, Env wie der Schwarm, Weg C, **Stichentscheid `tau_tiebreak_q` 2 in allen
Sockel-Klassen** (`PREREG_asymmetric_selfplay.md` par.5e3; der Schwarm bleibt mit Bestand, Nutzer 11:35).

| Klasse | Partien | Sims | Seed | Grund |
| --- | --- | --- | --- | --- |
| `policy` | 1.000 | 400 | 20260950 | KL x2 gegen @100 bei gleichen Punkten (par.8b1/8c1) |
| `policy-s100` | 1.000 | 100 | 20260954 | haelt die Spaltenkultur: @400 verliert 0,07 volle Spalten je Seite (par.8c1) |
| `policy-dice-v2-r1` | 2.000 | 100 (Basis), Platzsuche 600 (Nutzer 13:30: *"ich meinte die platzsuche, basis 100 passt"*) | 20260953 | W-v2 Runde 1 traegt (par.5d3a/b); Start `tools/v35_sockel_w_generate.sh` nach dem Mischsockel |
| `policy-exploiter` | 2.000 | 100 | 20260955 | nur nach bestandenem Tor par.7c |

Start `tools/v35_sockel_generate.sh` (Smoke 10 Partien je Klasse nach `data/probe_v35sockel_smoke`, dann die zwei
Haelften nach `data/`). Kosten HERLEITUNG aus par.8c1: 1.000 x 6,0 s + 1.000 x 3,2 s = rund 2,6 h. Abnahmen wie par.8
nach der Erzeugung. Fenster: Schwarm (8.000) + Sockel (2.000 + W 2.000 + ggf. Exploiter); Traeger-Manifest nach der
Erzeugung.

### par.10a ERZEUGUNG DES SOCKELS (2026-10-04 13:17-17:43, Terminal-Tab-Ketten, Exit 0, Smokes gruen)

| Klasse | Partien | Dateien | Wanduhr | s je Partie (11 Threads) | Manifest |
| --- | --- | --- | --- | --- | --- |
| `policy` (@400, Modus 2) | 1.000 | 100 | 6.207,6 s | 6,21 | `manifest_v34-b01-policy_20261004_131853.json` |
| `policy-s100` (@100, Modus 2) | 1.000 | 100 | 3.177,6 s | 3,18 | `manifest_v34-b01-policy-s100_20261004_150226.json` |
| `policy-dice-v2-r1` (W-v2 R1, Basis 100, Platzsuche 600) | 2.000 | 200 | 6.415,0 s | 3,21 | `manifest_v34-b01-policy-dice-v2-r1_20261004_155639.json` |

Zusammen 4.000 Partien in 4,4 h. Keine Watchdog-, Deadline- oder Haenger-Zeile gesehen (Terminal-Ausgabe, nicht
vollstaendig gelesen; Abnahmen par.8 stehen aus). **Abnahmen, Traeger-Manifest, Fenster und Training folgen nach
Freigabe der Maschine durch den Nutzer** (Nutzer 15:20: Maschine bis auf Widerruf beim Nutzer). Exploiter-Klasse:
nicht erzeugt (par.7c der Asym-Prereg offen, Nutzer: *"lass den exploiter noch aussen vor"*).

### par.10b ABNAHMEN DES SOCKELS (2026-10-04 18:05-18:20, nach Freigabe der Maschine; Nutzer: *"mach die abnahmen und committe"*)

| Abnahme (par.8) | Ergebnis |
| --- | --- |
| Smoke vor dem Start | GRUEN (10 Partien je Klasse, Waechter 10 bzw. 14 Knoepfe je Klasse) |
| Manifest-Diff gegen v34 (`manifest_v33-b01-policy_20261001_100644`) | **GRUEN**: `mosaic_env` identisch; in `cli_args`/`engine_config` nur die neuen Knoepfe der Nacht (Wuerfel, Stoerer, Stichentscheid, Zweitnetz) mit ihren Defaults bzw. den registrierten Werten (par.10) sowie model/spec/seed/version/games/sims wie beabsichtigt |
| Tor 0 je Klasse (`corpus_sanity_check.py data --pattern`) | Exit 0 in allen drei Klassen; Artefakte `corpus_sanity_v34-b01-{policy,policy-s100,policy-dice-v2-r1}.json` |
| Vollstaendigkeit | 1.000 / 1.000 / 2.000 Partien, 0 unvollstaendige (Feld `completed`), 198.667 / 198.612 / 395.446 Records; W-Klasse: `dome_dice_side` auf allen 395.446 Records, 4.000 Platzwahl-Records (2 je Partie) |
| Spiegelknopf (`tie_mirror_acceptance.py --prefix v34-b01`) | **GRUEN**: 48,8 % (policy, SE 1,6), 49,2 % (policy-s100, SE 1,6), 48,55 % (policy-dice-v2-r1, SE 1,1); keine uneinheitliche Partie, keine ohne Feld |
| Watchdog-/Deadline-/Haenger-Zeilen | 0 im gelesenen Terminal-Rest (letzte 1.000 Zeilen der Sockelkette) und 0 unvollstaendige Partien in allen drei Klassen; die vollstaendige Kettenausgabe lag nur im Terminal |
| KL-Abnahme am Ausflug | entfaellt (keine Ausflug-Klasse im Sockel) |

**Sechs Standard-Kennzahlen** (Grundmenge Seiten: 2.000 / 2.000 / 4.000; Einheit je Seite; v34-Sockel `v33-b01-policy`
zum Vergleich aus `PREREG_v34_window.md` par.9 nicht hier wiederholt):

| Kennzahl | `policy` @400 M2 | `policy-s100` @100 M2 | `policy-dice-v2-r1` @100 M2 |
| --- | --- | --- | --- |
| volle Reihen / Fuellstand | 0,081 / 2,91 | 0,094 / 2,94 | 0,084 / 2,92 |
| volle Spalten / >= 4 / >= 3 | 0,826 / 2,29 / 3,24 | 0,907 / 2,31 / 3,21 | 0,835 / 2,29 / 3,24 |
| Strafleiste (Steine je Seite) | 5,47 | 5,08 | 5,25 |
| eigene Punkte | 50,94 | 53,05 | 51,48 |
| Plattenpunkte k1 / k3 / k4 / k5 / k6 | 6,06 / 3,76 / 9,83 / 8,38 / -9,70 | 6,59 / 3,69 / 10,10 / 9,04 / -9,47 | 6,26 / 3,74 / 9,95 / 8,55 / -9,63 |

Lesart: der @400-Teil liegt wie in par.8c1 der Asym-Prereg bei 0,08 weniger vollen Spalten und 2 Punkten weniger als
der @100-Teil (hier 1.000 gegen 1.000 Partien, Richtung und Groesse wie gemessen); die W-Klasse liegt dazwischen
(W-Seite und G-Seite gepoolt, W gewinnt rund 44 %, par.5d3a). Kein Befund, der die Erzeugung in Frage stellt.
**Naechste Schritte:** Traeger-Manifest, Fenster (Schwarm 8.000 + Sockel 4.000), Cache, Training `v35-b01`,
Tor 1 gegen `v34-b01`, Promotion falls die Kante faellt. Exploiter-Klasse offen (par.7c der Asym-Prereg).

## par.11 FENSTER, TRAINING v35-b01 UND TORE (REGISTRIERT 2026-10-04 abends VOR dem Lauf; Kette `tools/night_v35_chain.sh`)

Nutzer-Rahmen: v35 ist die LETZTE Generation (STATUS, Abschnitt RICHTUNG). Exploiter bleibt aussen vor
(Nutzer 15:20) und ist am 2026-10-04 abends GESTRICHEN (*"streich den exploiter, sockel-manifest passt so"*;
`PREREG_asymmetric_selfplay.md` par.7c1). Das Fenster wird OHNE Exploiter-Klasse gebaut; das Traeger-Manifest mit den
400 Sockel-Dateien ist vom Nutzer bestaetigt.

**Fenster (1.200 Dateien, 12.000 Partien, alles Generator `v34-b01`, alles in `data/`):** die fuenf Klassen aus
par.9/par.10a: `value-deviate` 400, `value-excursion` 400, `policy` 100, `policy-s100` 100, `policy-dice-v2-r1`
200. KEINE Alt-Generationen (G-1/G-2 fallen weg, `PREREG_asymmetric_selfplay.md` par.4a), KEINE Sonden- oder
Probe-Daten (die liegen in `data/probe_asym`, `data/probe_asym_rep`, `data/exploiter*`,
`data/probe_v35sockel_smoke`, nicht in `data/` direkt; geprueft 2026-10-04: `data/*.pkl` traegt nur
`selfplay_v31-b01-*` bis `selfplay_v34-b01-*`). `MOSAIC_DATA_EXCLUDE` wird trotzdem um `selfplay_probe-`,
`selfplay_x35`, `selfplay_x35e2` erweitert (Fenster-Pinning, zweite Sicherung neben der Dateiliste).

**Traeger-Manifest `data/policy_carrier_manifest_v35.json`, 400 Traeger = die drei Sockel-Klassen vollstaendig**
(`policy` 100 + `policy-s100` 100 + `policy-dice-v2-r1` 200; W-Klasse beide Seiten, par.5d der Asym-Prereg:
"Policy-Ziele bleiben"). Die 800 Schwarm-Dateien (Weg C, Ausflug) sind wie in v34 KEINE Policy-Traeger
(v34-Manifest: `v33-b01-value-*` 0 Traeger). **Abweichung von der Uebergabe, benannt:** die Uebergabe sagte "ohne
Traeger-Manifest"; ohne Manifest macht `corpus_dataset._is_policy_carrier` (`corpus_dataset.py:126-158`,
`carrier_set is None`) aber JEDE Datei zum Traeger, also auch den Schwarm. Gemeint war "ohne Alt-Generationen";
so wird es gebaut. Erzeugung mit `tools/generate_carrier_manifest.py` (`--pattern` policy, `--n-files 100`,
`--include-glob` fuer `policy-*`), Kette bricht ab, wenn das Manifest nicht 400 = 100 + 100 + 200 traegt.

**Val-Menge 120 Dateien (10 %, val_frac 120/1.200), Val-Pool `^selfplay_v34-b01-`** (alle fuenf Klassen).
v34 hatte 147/1.380 wegen `PREREG_targeted_branching.md` par.7a; die Prereg ist geschlossen, der Grund entfaellt.

**Wertmaske der Wuerfelphase `MOSAIC_MASK_DICE_PHASE_VALUE=1`** (par.5d der Asym-Prereg: Wertziele BEIDER Seiten
in Runde 1 der W-Partien maskiert, Zusatzfeld `value_weights`; Knopf in `file_cache_key.py:166-178` und `:336`
(Block-Schluessel) sowie `corpus_dataset.py:781-784` (Fenster-Schluessel), Verbrauch `train.py:461-464`, `:864`).
Stichprobe 2026-10-04: erste W-Datei 368 von 1.978 Records mit `dice_phase` true (n = 1 Datei). Die Maske
wirkt nur auf die W-Klasse; Bestandsrecords ohne Feld bekommen Gewicht 1. Abnahme: der Schluessel des Monolithen
traegt den Marker `maskdicephasevalue_v1` bzw. unterscheidet sich vom Schluessel ohne Knopf; das Trainings-Manifest
traegt die Variable in `mosaic_env`.

**Training `v35-b01`:** warm von `v34-b01_brierbest`, Rezept byte-gleich `models/manifest_train_v34-b01_20261001_183258.json`
`cli_args` (12 Epochen, lr 5e-5 cosine, `--lr-t-max 12`, WDL, nortv, lambda 0,7, ownership-head-2d mit Gewicht 0,
opp-points-head, destretch 0,0051/1,9269, `--select-by-brier`, `--fast-loader`), **Seed 20260965** (Vierer-Schritt
nach `docs/generation_loop.md`; v34 20260961). Env wie v34 (`MOSAIC_IGNORE_POLICY_TARGET_VALID=1`,
`MOSAIC_FEATURES_FROM_RUST=1`) plus Maske und Manifest v35. Erwartete Manifest-Abweichungen gegen v34-b01: genau
`name, load, file_list, cache_file, seed, val_pool, val_frac` sowie Schluessel, die train.py seit dem v34-Manifest
neu mit Default fuehrt (z. B. `margin_thresholds`, `margin_threshold_weight`, Asym-Prereg par.7 Lauf-Chronik);
jede andere Abweichung STOPPT die Kette vor Tor 1. Gegatet wird das Brier-beste Netz, aus dem Manifest bestimmt
(`tools/brier_best_checkpoint.py`, Code-Review 2 #1), nicht aus dem Dateinamen.

**Tor 1 = Champion-Kante** (Generator `v34-b01` IST der amtierende Champion, `docs/generation_loop.md` Schritt 5
und 7 fallen zusammen): `tools/paired_gating.py`, Seeds 20261600/20261601 a 200 Paare, 400 Sims beide, Blockgroesse
5, SPRT 0,001, `--log-games`, Spec `models/v34-b01_brierbest.spec.json` BEIDSEITS (byte-gleich
`models/v33_gating_r5net.spec.json`, `cmp` 2026-10-04: Startkuppel-Suche an, Runde 5 per Netz). Kriterium wie
`PREREG_v34_window.md` par.2: z >= +1,96 oder gepoolt >= 52,5 % ohne Gegenbefund, Block-z ueber
`tools/gating_block_z.py`; Stufenregel: loest GENAU EINER der beiden Seeds Block-z >= +1,96 aus, laeuft Seed
20261602, Verdikt auf dem gepoolten Block-z. Zuordnung vorab: ein Gewinn gehoert dem v35-FENSTER (Mischsockel
Modus 2, W-v2, Maske, R5 @400 in der Erzeugung) bei unveraendertem Rezept und gleicher Spec beider Seiten.

**Tor 2a (Self-Play-Flaeche, ex post, schon gemessen par.10b):** `sp_voll` der Sockel-Klassen 0,826 (`policy`
@400 M2) / 0,907 (`policy-s100` @100 M2) je Seite gegen 0,921 des v34-Sockels (par.9a der v34-Prereg); NICHT
gleich bedingt (Stichentscheid Modus 2, Runde 5 @400 statt @100, par.9a Nachtrag dort), und der Nutzer hat den
Mischsockel in Kenntnis der -0,07 Spalten @400 entschieden (par.10). Kein neues Tor-2a-Verdikt; die Zahlen stehen.
**Tor 2b (Arena-Flaeche):** volle Spalten je Seite aus den Tor-1-Logs (`tools/probes/arena_column_probe.py`),
Punktschaetzer v35-b01 >= v34-b01 in derselben Arena (Nicht-Fallen, `docs/generation_loop.md`).

**Kosten (HERLEITUNG aus `docs/measured_runtimes.md`):** Bloecke 1.200 Dateien rund 20 min (0,96 s je Datei, 6
Worker), Merge wenige Minuten, Training rund 1 h (v34-b01: 12 Epochen auf 1.233 Dateien), Tor 1 rund 1,3-1,5 h
je Seed (200 Paare @400, 10 Threads); zusammen rund 4,5 h, darum im Terminal-Tab (2-h-Grenze der
Hintergrundaufgaben). Laufzeiten stehen in den Artefakten (`laufzeit`-Block) und werden hier nachgetragen.

**Nach dem Lauf, in dieser Reihenfolge:** Abnahme Fenster (1.200 Dateien, 0 Sonden-Namen, Schluessel traegt die
Maske), Manifest-Diff, Netz-Gesundheit gegen den Warmstart (wie par.10 der v34-Prereg: NaN/Inf, BN-Gamma,
relative Gewichtsaenderung), Tor-1-Verdikt mit Block-z, Tor 2b, sechs Standard-Kennzahlen je Seite, Elo-Register.
Promotion NUR nach Nutzer-Entscheid und `/mosaic-champion-promotion`; Netz-Paritaets-Fixture (Checkliste 5d) und
Diagnostiken (Platt, R4/R4b, sigma/Prior) gehoeren zur Promotion, nicht zur Trainings-Abnahme (die Fixture folgt
`models/champion.txt`).

### par.11a FENSTER UND TRAINING v35-b01: ERGEBNIS (2026-10-04 19:41-20:37, `tools/night_v35_chain.sh`, exklusiv)

**Fenster (Schritte 1-4, 19:41-20:00):** Traeger-Manifest 400 = 100 + 100 + 200 (Soll erfuellt); Fensterliste 1.200
Dateien, eindeutig, 0 Sonden-Namen; Split Val 120 / Train 1.080; Bloecke 1.200 neu in 953,5 s (0,79 s je Datei, 6
Worker); Monolith `data/.cache_ac852965e449.h5`, Zusammenfuegen 154 s, Stempel = Schluessel, 1.080 Dateien,
2.025.784 Zustaende. **Masken-Abnahme GRUEN:** Schluessel mit Maske `ac852965e449`, ohne Maske `8531f0889293`,
Marker `+maskdicephasevalue_v1` im Material, Fingerabdruck traegt `MOSAIC_MASK_DICE_PHASE_VALUE=1`; im Monolithen
`value_weights` mit 67.171 Nullen von 2.025.784 (3,3 %, Grundmenge Trainingszustaende; passt zu rund 180 W-Dateien
im Trainingsanteil mit je rund 370 Wuerfelphasen-Records, Stichprobe par.11). Traeger-Maske beim Zusammenfuegen:
725 von 1.080 Bloecken policy-maskiert (= 355 Traeger im Trainingsanteil + 45 im Val-Anteil = 400).

**Training (Schritt 5, 20:00-20:37):** Exit 0, `laufzeit` 2.198,0 s Wanduhr (cpu_s 9.871, 6 Threads, cuda,
fast-loader, Datenaufbau 17,2 s, 12 Epochen, 2.025.784 Samples); v34-b01 2.956,6 s bei 2.328.960 Samples.
Manifest `models/manifest_train_v35-b01_20261004_200022.json` (Commit `a193b409`, dirty = STATUS/Pitfalls-Edits).
**Manifest-Diff gegen v34-b01: 0 unerwartete Abweichungen**; abweichend genau `cache_file, file_list, load, name,
seed, val_frac, val_pool`; neu mit Default `margin_thresholds` False, `margin_threshold_weight` 1,0 (inaktiv).
`mosaic_env` traegt Maske und Manifest v35; `policy_carriers`: 400 Traeger, value-Klassen 0.

**Gegatetes Netz: `v35-b01_best`** (`tools/brier_best_checkpoint.py`: final 12, brier_best 2, best 2; kein
`_brierbest`, weil Brier-Minimum = `best_epoch`). Kurven (Grundmenge Val 120 Dateien; Policy-Val nur auf den rund
45 Traeger-Dateien im Val-Anteil; Einheit Verlust je Sample):

| Epoche | 1 | 2 | 4 | 6 | 8 | 10 | 12 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Value-Brier v35 | 0,19506 | **0,19460** | 0,19509 | 0,19491 | 0,19490 | 0,19503 | 0,19508 |
| Policy-Val v35 | 0,4292 | 0,4287 | 0,4331 | 0,4379 | 0,4425 | 0,4450 | 0,4464 |
| Policy-Train v35 | 1,075 | 1,021 | 0,953 | 0,906 | 0,873 | 0,852 | 0,844 |

Lesart: Brier flach (Spanne 0,0005, unter der Offline-Aufloesung `project_offline_metric_resolution_limit`);
Policy-Val steigt monoton +4,1 % waehrend Policy-Train faellt, dieselbe Form wie bei v34-b01 (0,358 -> 0,3715,
+3,8 %). Das Niveau ist nicht gegen v34 lesbar (anderer Val-Satz: Modus-2-, @400- und W-Ziele, par.8b1 der
Asym-Prereg: KL x2). Das gegatete Netz hat zwei Epochen vom Generator weg trainiert. **Netz-Gesundheit gegen den
Warmstart (NaN/Inf, BN-Gamma, relative Gewichtsaenderung) folgt NACH Tor 1** (Torch-Last waehrend der Arena
vermieden). Tor 1 gestartet 20:37:04, Seed 20261600.

### par.11b OFFLINE-NACHMESSUNG "WARUM LERNT ES NICHTS MEHR" (REGISTRIERT 2026-10-04 abends VOR dem Lauf; Nutzer: *"ja, fahr beide messungen nach tor 1"*)

Anlass: par.11a (Brier flach ab Epoche 1, Policy-Val steigt, gegatet wird Epoche 2) und die Nutzer-Frage, warum
das Netz aus nachweislich staerkerem Sockel-Material (Modus 2, par.5e3 der Asym-Prereg) nichts lernt. Beide
Messungen laufen NACH Tor 1 (Exklusivitaet), Werkzeug `tools/checkpoint_val_eval.py` (gebaut 2026-10-04 abends),
Grundmenge der Val-Satz `data/window_v35_val.txt` (120 Dateien: value-deviate 34, value-excursion 41, policy 12,
policy-s100 11, policy-dice-v2-r1 22; Einheit Verlust je Sample, Block = Datei), Checkpoints `v34-b01_brierbest`
(Warmstart = "Epoche 0"), `v35-b01_best` (Epoche 2, gegatet), `v35-b01` (Epoche 12). Metriken zahlengleich zu
train.py (Selbstpruefung des Werkzeugs: `v35-b01_best` auf der Val-Liste muss `value_val_brier` 0,1946 und
`policy_val_loss` 0,42868 der Epochenzeile 2 treffen, Toleranz 1e-4; sonst ist das Werkzeug falsch, nicht das Netz).

**M1 (Epoche 0):** gepaarte Differenz je Datei Brier(Warmstart) minus Brier(`v35-b01_best`) ueber 120 Dateien,
Block-Bootstrap-CI 95 % (1.000 Ziehungen, Seed 20261004). **Leseregel:** CI ganz ueber 0 heisst, die zwei Epochen
haben auf dem eigenen Material etwas gelernt (Groesse berichten); CI mit 0 heisst, das Fenster hat dem Wertkopf
nichts beigebracht. Dasselbe fuer Epoche 12 (Verlauf). Policy-Val analog, nur berichtet: der Policy-Val ist als
Staerke-Mass unbrauchbar (`project_offline_metric_resolution_limit`), und auch der Brier sagt hier nichts ueber
Arena-Staerke, sondern nur, ob das Netz sich auf seiner eigenen Verteilung bewegt hat.

**M2 (je Klasse):** Brier des Warmstarts je Klasse mit Block-Bootstrap-CI; Schwarm = deviate + excursion gepoolt.
**Leseregel:** liegt das CI einer Sockel-Klasse (Modus 2 bzw. W) ganz ueber dem Schwarm-CI, traegt diese Klasse
Material, das der Wertkopf schlechter vorhersagt (Kandidat fuer "Information, die das Netz nicht hat"; HERLEITUNG,
denn ein Klassen-Brier kann auch strukturell hoeher liegen, etwa durch die W-Asymmetrie oder die Maske, die die
Wuerfelphase aus dem Brier nimmt). Entscheidend ist darum **M2b:** die gepaarte Differenz Warmstart minus
`v35-b01_best` JE KLASSE: nur wo sie ganz ueber 0 liegt, hat das Training aus dieser Klasse gelernt. Vorab benannt:
n = 11 bis 22 Dateien je Sockel-Klasse, die CIs werden breit; ein CI mit 0 ist dann "nicht aufloesbar", nicht "kein
Effekt". Folgerung, falls M2b nur auf den Sockel-Klassen positiv ist und auf dem Schwarm nicht: ein Fenster nur aus
Modus-2-Material waere der Hebel; das ist ein Nutzer-Entscheid (v35 ist die letzte Generation).

Kosten HERLEITUNG: drei Checkpoints auf 120 Dateien (rund 230.000 Zustaende), GPU, wenige Minuten; Klassen-Caches
aus liegenden Bloecken. Laufzeit steht im Artefakt `evaluations/artifacts/checkpoint_val_eval_v35.json`.

**Nachtrag par.11b (2026-10-04 22:25, am Code geprueft, vor dem Lauf):** der Val-Brier von train.py ist NICHT mit
`value_weights` gewichtet; seine Maske ist allein `wdl_outcome >= 0` (`train.py:1046-1052`, Mittelwert `:1113`),
`value_weights` geht erst in `value_val_loss` und Punkte ein (`train.py:934-936`). Folgen: (a) die Wuerfelphasen-
Records der W-Klasse (rund 19 % ihrer Records, par.11) zaehlen im Brier voll, obwohl ihr Ausgang aus der Stellung
per Konstruktion nicht erklaerbar ist (par.5d der Asym-Prereg); der W-Klassen-Brier liegt darum STRUKTURELL hoeher,
M2 ist fuer W nicht als "fehlende Information" lesbar. (b) Dasselbe gilt fuer die Auswahlregel `--select-by-brier`
des Trainings: rund 3,5 % der Val-Zustaende (22 W-Dateien x rund 370 Records von rund 230.000) sind unlernbar und
gehen trotzdem in die Auswahl ein; fuer alle Epochen gleich, also ohne Wirkung auf die Rangfolge der Epochen
(HERLEITUNG). Das Werkzeug gibt deshalb zusaetzlich `value_val_brier_vw` aus (Zeilen mit `value_weights` 0
ausgeschlossen); fuer M2/M2b der W-Klasse gilt diese Groesse, fuer die Selbstpruefung gegen das Manifest die
ungewichtete.

### par.11c TOR 1, SEED 20261600 (2026-10-04 20:37-23:15, `gating_v35-b01_vs_v34-b01_s20261600.json`; GEBREMST, siehe unten)

| Groesse | v35-b01 (A) | v34-b01 (B) |
| --- | --- | --- |
| Siege (400 Partien, 200 Paare) | **208** | 192 |
| Siegquote A | 52,0 % | |
| gepaarte Differenz je Paar | +0,08 [-0,11; +0,27] | McNemar p 0,47 |
| Block-z (40 Bloecke a 5 Paare, Mittel 0,520, sd 0,138) | **+0,92** | |
| SPRT | UNDECIDED_CAP_REACHED, LLR -1,86 | |
| Paare: A-Sweep / B-Sweep / Split | 50 / 42 / 108 | |
| eigene Punkte je Partie | 58,56 | 57,40 |
| Marge je Partie (A minus B) | +2,33 [-1,03; +5,68] | |
| Strafleiste (Steine je Partie) | 7,71 | 8,28 |
| volle Spalten je Seite (`arena_column_probe`, n = 400) | **1,078 +- 0,074** | 1,128 +- 0,072 |
| Spalten >= 4 / lange Reihen | 2,40 / 3,22 | 2,29 / 3,23 |
| Plattenpunkte, Platzierung (gepaart, `plate_points_from_arena`) | +1,37 [+0,13; +2,60] | einziges Kriterium mit CI ohne 0 |

Vollstaendigkeit: 400 von 400 Partien `completed`, 0 unvollstaendig. **Laufzeit 9.509,9 s Wanduhr (cpu_s 39.213,5,
10 Threads, 23,8 s je Partie), GEBREMST:** neben der Arena lief ein Spiel des Nutzers (gemessen 20:50 ueber 10 s:
Gating 38,9 %, Spiel 16,9 %, Claude-Prozesse rund 7 % der 12 Kerne), Referenz exklusiv 13,6 s je Partie
(`docs/measured_runtimes.md` Z. 174). Nach `docs/working_rules.md` als gebremste Laufzeit markiert; Partien sind
seit der Wheel-Runde vom 2026-10-02 schrittbegrenzt, nicht wanduhrbegrenzt, alle 400 vollstaendig.

**Lesart Seed 1 (kein Verdikt, das faellt gepoolt ueber beide Seeds, par.11):** Block-z +0,92 liegt weit unter +1,96,
die Siegquote 52,0 % unter 52,5 %; der Verlauf stieg bis Block 24 auf 55,0 % (132:108) und fiel bis zum Deckel auf
52,0 % zurueck. Punkte und Marge zeigen in dieselbe Richtung, ohne Signifikanz. **Tor 2b** (volle Spalten je
Seite): Punktschaetzer 1,078 gegen 1,128, also UNTER dem Vorgaenger (Differenz -0,05 bei SE rund 0,07 je Seite):
nach `docs/generation_loop.md` ist das Tor am Punktschaetzer gerissen, nicht signifikant; Verdikt ebenfalls erst
gepoolt ueber beide Seeds. Seed 20261601 gestartet 23:15:37.

**NUTZER-ENTSCHEID 2026-10-04 23:4x: Seed 20261601 ABGEBROCHEN** (*"abbrechen, bei bedarf koennen wir immer noch den zweiten
seed fahren"*; Vorlage des Koordinators: eine knappe Kante ist nicht das Ziel "staerker als v34", und Seed 2 blockiert
gebremst 2,7 h lang par.11b und den naechsten Schritt). Stand beim Abbruch: Block 2, 8:12 (10 Paare), kein Artefakt,
keine Wertung; Kette im Terminal beendet, keine verwaisten Prozesse (Prozessliste geprueft). **Abweichung von par.11,
benannt:** Tor 1 fuer `v35-b01` liegt damit mit EINEM Seed vor (200 Paare, 52,0 %, Block-z +0,92) und ist NICHT
entschieden, nicht gerissen; nach `docs/generation_loop.md` reicht n >= 150 Paare fuer eine Tor-Messung, das
vorregistrierte Verdikt verlangte aber zwei Seeds gepoolt. Seed 20261601 kann mit identischen Einstellungen
nachgeholt werden (`tools/night_v35_chain.sh` Schritt 6, `gate`-Funktion). Weiter mit par.11b, Netz-Gesundheit, dann
Nutzer-Entscheid ueber einen Modus-2-Schwarm (STATUS, RICHTUNG).

### par.11b ERGEBNIS (2026-10-04 23:25-23:27, `evaluations/artifacts/checkpoint_val_eval_v35.json`, 83,5 s Wanduhr, cuda)

Selbstpruefung PASS: `v35-b01_best` auf der Val-Liste trifft die Manifest-Zeile Epoche 2 exakt (Brier 0,19460015,
Policy-Val 0,42868324). Datei-Zuordnung: 224.893 Zeilen aus 120 Bloecken, 0 Feldabweichungen gegen den Monolithen
`.cache_81bef1158189.h5`. Grundmenge Val-Satz (Dateien / Zustaende): all 120 / 224.893; deviate 34 / 67.030;
excursion 41 / 68.436; policy @400 M2 12 / 23.936; policy-s100 M2 11 / 22.040; W 22 / 43.451 (davon 8.259
Wuerfelphase, aus `brier_vw` ausgeschlossen). Einheit Verlust je Zustand; CI = Block-Bootstrap ueber Dateien, 95 %.

**M1 (Epoche 0 gegen Epoche 2 und 12), gepaarte Differenz Warmstart minus Checkpoint (positiv = gelernt):**

| Liste | Brier Warmstart | dBrier zu Epoche 2 [CI] | dBrier zu Epoche 12 [CI] | dPolicy-Val gepoolt zu Ep. 2 [CI] |
| --- | --- | --- | --- | --- |
| all | 0,19518 | +0,00058 [-0,00032; +0,00141] | +0,00010 [-0,00099; +0,00119] | **+0,068 [+0,055; +0,080]** |

**Leseregel M1: CI mit 0, das Fenster hat dem Wertkopf nichts Messbares beigebracht**, weder in zwei noch in zwoelf
Epochen (Epoche 12 liegt wieder auf dem Warmstart). Der Policy-Kopf hat sich dagegen messbar bewegt (CI ganz ueber
0), auf Epoche 12 noch +0,023 [+0,015; +0,030] gegen den Warmstart, aber schlechter als Epoche 2.

**M2 / M2b je Klasse** (Warmstart-Brier mit CI; gepaarte Differenz zu Epoche 2; Policy-Val gepoolt nur Traeger):

| Klasse | Brier Warmstart [CI] | brier_vw | dBrier zu Ep. 2 [CI] | Policy-Val Warmstart -> Ep. 2, dPloss [CI] |
| --- | --- | --- | --- | --- |
| value-deviate | 0,2028 [0,1900; 0,2147] | = | +0,0008 [-0,0010; +0,0028] | -- |
| value-excursion | 0,1873 [0,1764; 0,1984] | = | +0,0012 [-0,0001; +0,0025] | -- |
| policy @400 M2 | 0,1987 [0,1776; 0,2205] | = | +0,0004 [-0,0016; +0,0023] | 1,380 -> 1,250, **+0,131 [+0,118; +0,143]** |
| policy-s100 M2 | 0,1998 [0,1818; 0,2163] | = | +0,0002 [-0,0031; +0,0027] | 1,041 -> 1,003, +0,038 [+0,026; +0,051] |
| W (policy-dice-v2-r1) | 0,1916 [0,1771; 0,2056] | 0,1791 | -0,0004 [-0,0023; +0,0013] | 1,066 -> 1,018, +0,048 [+0,039; +0,056] |

**Leseregel M2: keine Sockel-Klasse liegt mit ihrem CI ueber dem Schwarm**; der hoechste Warmstart-Brier liegt auf
`value-deviate` (0,2028), die Modus-2-Klassen liegen dazwischen, W ohne Wuerfelphase am niedrigsten (0,1791). **M2b:
keine Klasse mit CI ueber 0**; die groessten Punktschaetzer liegen auf dem SCHWARM (excursion +0,0012, deviate +0,0008),
die Modus-2-Klassen bei +0,0002 bis +0,0004, W negativ. Die Hypothese "Modus-2-Material traegt Information, die der
Wertkopf noch nicht hat" wird NICHT gestuetzt; mit n = 11 bis 22 Dateien ist das "nicht aufloesbar", wie vorab benannt,
aber die Richtung der Punktschaetzer spricht gegen sie. **Was das Netz gelernt hat, ist Policy, und am meisten auf
der @400-Klasse** (Policy-Val 1,38 gegen 1,04 bei @100: die @400-Suchziele liegen am weitesten vom Prior, und dorthin
bewegt sich der Kopf, +0,131). Ob das Arena-Staerke traegt, sagt die Offline-Metrik nicht
(`project_offline_metric_resolution_limit`; bei 400 Sims traegt der Wertkopf, `project_hybrid_head_attribution`).

**Folgerung fuer den Hebel "Schwarm mit Modus 2 neu erzeugen":** nach M2b nicht belegt, der Wertkopf lernt aus keiner
Klasse messbar. Belegt ist nur ein Policy-Effekt aus tieferer Suche (@400). Nutzer-Entscheid offen.

**Netz-Gesundheit gegen den Warmstart (2026-10-04 23:35, `tools/checkpoint_weight_health.py`, Artefakt
`checkpoint_weight_health_v35-b01.json`, 2,9 s; nur Gewichte):** keine NaN/Inf in Warmstart, Epoche 2 und Epoche 12; BN-Gamma
|g| < 1e-3 in 0 von 1.120 Einheiten (4 BN-Schichten) in allen drei Staenden. Relative Gewichtsaenderung
(Frobenius, weight+bias je Schicht, gegen `v34-b01_brierbest`): Epoche 2 (gegatet) 0,8-5,2 % im Rumpf und Policy-Kopf,
9,1-9,8 % in Wert-, Punkte- und Gegnerpunkte-Kopf; Epoche 12 8,6-13,2 % Rumpf, 11,9 % Policy, **22,9 % `value_head.0`**,
22,0 % Punkte, 21,7 % Gegnerpunkte; moon- und ownership-Koepfe 0,0 % (Gewicht 0). Verdikt GESUND. Lesart: der Wertkopf
hat sich in zwoelf Epochen um fast ein Viertel bewegt, ohne dass der Val-Brier sich bewegt (par.11b: Epoche 12 auf
Warmstart-Niveau); das ist Anpassung an die Trainingsdateien, nicht an das Material (HERLEITUNG aus beiden Messungen).

### par.11d ROHES NETZ GEGEN SUCHWERT DER WURZEL, je Runde und Klasse (2026-10-04 23:39, nach der Nutzer-Frage *"warum lernt es nichts mehr"*; Artefakt `checkpoint_val_eval_v35_rootq.json`, 33 s)

Frage: ist die Suche der Erzeugung dem rohen Netz beim Wert noch voraus? Nur dann traegt der Kreislauf (die 30 %
`root_q` im Wertziel, `corpus_dataset.py:2168`, und die Trajektorien). Werkzeug `tools/checkpoint_val_eval.py`
(Block `root_q_compare`): auf IDENTISCHEN Zeilen (root_q_mask > 0, wdl_outcome >= 0, value_weights > 0) Brier des
rohen Netzes `v34-b01_brierbest` (= Generator, Sicht des Ziehers) gegen Brier von `(root_q+1)/2` (Suchwert der Wurzel
aus Sicht des Ziehers, `net_mcts.rs:7905-7923`, Skala `corpus_dataset.py:1492-1498`), gegen die Konstante m(1-m);
diff = Netz minus root_q, positiv = Suche besser; CI Block-Bootstrap ueber Dateien. Grundmenge Val-Satz, Einheit
Verlust je Zustand. Erzeugungs-Suche: Schwarm und policy-s100 @100 Sims, Klasse `policy` @400, Runde 5 ueberall per
Netz @400 (par.5).

| Liste (Sims) | Runde 1 | Runde 2 | Runde 3 | Runde 4 | Runde 5 |
| --- | --- | --- | --- | --- | --- |
| all (n 24.004 / 33.217 / 34.269 / 33.829 / 24.856) | Netz 0,2485, root_q 0,2553, **diff -0,0068 [-0,0125; -0,0009]** | +0,0022 [-0,0024; +0,0065] | +0,0063 [+0,0033; +0,0094] | +0,0127 [+0,0103; +0,0151] | +0,0212 [+0,0182; +0,0242] |
| policy-s100 (@100; n 3.270 / 3.428 / 3.339 / 3.140 / 2.288) | **-0,0103 [-0,0189; -0,0016]** | +0,0019 [-0,0087; +0,0120] | +0,0030 [-0,0061; +0,0116] | +0,0093 [-0,0002; +0,0186] | +0,0335 [+0,0253; +0,0447] |
| policy (@400; n 3.564 / 3.659 / 3.606 / 3.422 / 2.479) | -0,0002 [-0,0119; +0,0097] | **+0,0136 [+0,0045; +0,0224]** | **+0,0148 [+0,0047; +0,0255]** | **+0,0245 [+0,0126; +0,0353]** | +0,0228 [+0,0091; +0,0393] |
| value-deviate (@100) | -0,0096 [-0,0198; +0,0000] | -0,0015 [-0,0101; +0,0072] | +0,0035 [-0,0026; +0,0105] | +0,0135 [+0,0094; +0,0172] | +0,0187 [+0,0147; +0,0232] |
| value-excursion (@100) | -0,0045 [-0,0146; +0,0043] | +0,0003 [-0,0073; +0,0071] | +0,0071 [+0,0019; +0,0120] | +0,0099 [+0,0063; +0,0134] | +0,0190 [+0,0147; +0,0234] |
| W (@100, nach Wuerfelphase) | -- | +0,0044 [-0,0060; +0,0144] | +0,0065 [-0,0002; +0,0138] | +0,0122 [+0,0084; +0,0160] | +0,0222 [+0,0149; +0,0308] |

Konstante (Raten) ueberall 0,2500. Runde 5 ist ein anderes Schaetzproblem (Netz-Suche @400 mit Loeser-Resten,
`net_mcts.rs:7725-7739`), dort nur berichtet.

**Lesart (geprueft, n wie angegeben):** bei **100 Sims ist die Suche dem Netz beim Wert in Runde 1 UNTERLEGEN**
(Netz 0,2485, Suche 0,2553, schlechter als Raten) und in Runde 2 und 3 nicht nachweisbar ueberlegen; erst ab Runde 4
liegt sie vorn. Bei **400 Sims liegt die Suche ab Runde 2 klar vorn** (+0,014 / +0,015 / +0,025, CIs ohne 0; n = 12
Val-Dateien). Damit ist der Mechanismus des Stillstands benannt: das Wertziel traegt zu 30 % einen Suchwert, der in
der Eroeffnung schlechter ist als das Netz selbst, und zu 35 % die eigene Vorhersage; die Suche @100 hat dem Netz
beim Wert nichts mehr voraus, @400 schon. Dasselbe Muster wie bei der Policy (par.11b: gelernt wird nur aus den
@400-Zielen). Konsistent mit `project_lambda_sweep_result`: lambda 0,7 trug, als die Suche dem Netz voraus war.

**Folgerung (Vorlage an den Nutzer, kein Entscheid):** der eine Hebel mit Beleg ist die SUCHTIEFE DER ERZEUGUNG, nicht
Kopf, Ziel oder Kapazitaet (acht zielinvariante Gatings, `archive/history.md` Z. 9185-9229). Arm `v35-b02`: Fenster
komplett mit 400 Sims und Modus 2 neu erzeugen (Schwarm 2 x 4.000, policy 2.000 davon 1.000 vorhanden, W 2.000;
`policy-s100` entfaellt), Rezept und lambda 0,7 unveraendert, Tor 1 gegen v34-b01. Kosten HERLEITUNG aus 6,21 s je
@400-Partie (par.10a) und dem Verhaeltnis @400/@100 von 1,95: Schwarm rund 4,9 bzw. 3,4 s, W rund 6,3 s je Partie,
zusammen rund 14 h Erzeugung plus 20 min Bloecke, 37 min Training, 1,5 h Tor 1. Bekannter Preis: @400 kostet im
Self-Play 0,07 volle Spalten je Seite (`PREREG_asymmetric_selfplay.md` par.8c1).

## par.12 ARM v35-b02: FENSTER KOMPLETT MIT 400 SIMS UND MODUS 2 (NUTZER-ENTSCHEID 2026-10-04 spaet: *"b02 voll"*; REGISTRIERT VOR dem Lauf)

**Grund:** par.11d (die Erzeugungs-Suche @100 ist dem Netz beim Wert in Runde 1 unterlegen und bis Runde 3 nicht
ueberlegen; @400 ab Runde 2 klar voraus) und par.11b (der Policy-Kopf lernt nur aus @400-Zielen). Hypothese: mit
400 Sims in der GESAMTEN Erzeugung bekommt die Schleife ihren Vorsprung zurueck, Wert (30 % root_q im Ziel) wie
Policy. Alternativen zu "mehr Sims" (Nutzer-Frage) sind in STATUS/RICHTUNG festgehalten und NICHT Teil dieses Arms.

**Erzeugung (`models/v35_b02.recipe.json`, `tools/v35_b02_generate.sh`; Generator `v34-b01_brierbest`, Spec
`v35_generation.spec.json`, Env wie par.6, Runde 5 per Netz @400, Spiegelknopf an, E1 an):**

| Klasse (neu) | Partien | Sims | Stichentscheid | Seed | Flags |
| --- | --- | --- | --- | --- | --- |
| `policy-s400` | 1.000 | 400 | Modus 2 | 20263100 | wie `policy` (par.10); zusammen mit den vorhandenen 1.000 `policy`-Partien = 2.000 |
| `policy-dice-v2-r1-s400` | 2.000 | 400 (Basis), Platzsuche 600 | Modus 2 | 20263300 | W-v2 Runde 1 wie par.10 |
| `value-deviate-s400` | 4.000 | 400 | Modus 2 | 20262100 | Weg C, value-only, wie par.6 |
| `value-excursion-s400` | 4.000 | 400 | Modus 2 | 20262600 | Ausflug, KL-Abzweig an, value-only, wie par.6 |

Seeds: Chunk-Seed = Basis + Chunk-Index, Chunkzahl 100 / 200 / 400 / 400, Abstaende der Basen >= 200 (STATUS
Betriebsbefund 2026-10-04); keine der vier Basen ist je als Self-Play-Seed benutzt; 20262100 und 20262600 kommen als ARENA-Seeds in
`champion2_v31-b01_vs_v29-b09_s20262100.json` und `champion2_v34-b01_vs_v31-b01.json` vor (anderer Strom, Agent-Befund
2026-10-05, harmlos). Reihenfolge: policy-s400,
W-s400, deviate-s400, excursion-s400. Smoke je Klasse (10 Partien nach `data/probe_v35b02_smoke`) mit
Manifest-Abnahme: Sims 400, `tau_tiebreak_q` 2, `r5_net_sims` 400, Klassen-Knoepfe wie erwartet; rot = STOPP.
**Cache-Waechter laeuft daneben** (Nutzer: *"lass den cache waechter gleich mitlaufen"*; `build_cache_incremental.py
--watch`, 3 Worker, gemessen ohne Durchsatzverlust, `docs/measured_runtimes.md` Z. 93) mit derselben Umgebung
wie das Training (Wertmaske an), damit die Bloecke den Trainings-Schluessel treffen. Abnahmen nach par.8 je Klasse
(Tor 0, Spiegelknopf, KL-Abnahme am Ausflug, Vollstaendigkeit), berichtet, nicht fatal.

**Fenster `v35-b02` (1.200 Dateien, 12.000 Partien, alles @400 Modus 2):** `policy` 100 (vorhanden) + `policy-s400`
100 + `policy-dice-v2-r1-s400` 200 + `value-deviate-s400` 400 + `value-excursion-s400` 400. Traeger-Manifest
`policy_carrier_manifest_v35_b02.json` = 400 (policy 100, policy-s400 100, W-s400 200); Schwarm ohne Policy. Val
120, Val-Pool `^selfplay_v34-b01-`, Wertmaske an, Seed 20260965 (alle Arme einer Generation teilen den Seed),
Rezept byte-gleich v34-b01/v35-b01, Warmstart `v34-b01_brierbest`, gegatet das Brier-beste Netz
(`brier_best_checkpoint.py`). Die @100-Klassen (`policy-s100`, `value-deviate`, `value-excursion`,
`policy-dice-v2-r1`) bleiben in `data/` und sind NICHT im Fenster.

**Tore:** Tor 1 = Champion-Kante gegen `v34-b01` wie par.11 (Seeds 20261600/20261601, 200 Paare, Blockgroesse 5,
`--log-games`, Spec `v34-b01_brierbest.spec.json` beidseits, Kriterium z >= +1,96 oder gepoolt >= 52,5 % ohne
Gegenbefund, Stufenregel 20261602). Zuordnung vorab: ein Gewinn gehoert der Suchtiefe der Erzeugung (400 statt
100) plus Modus 2 im Schwarm, bei unveraendertem Rezept. **Tor 2a** ex post aus `corpus_sanity` der Policy-Klassen
gegen 0,826 (`policy` @400 M2, par.10b), gleich bedingt; bekannter Preis @400: -0,07 volle Spalten je Seite gegen
@100 (Asym-Prereg par.8c1), vom Nutzer in Kauf genommen. **Tor 2b** aus den Tor-1-Logs gegen v34-b01 wie par.11.
Vergleich mit b01 (par.11c) nur deskriptiv: gleiche Seeds, aber b01 hat einen Seed und lief gebremst.

**Kosten (HERLEITUNG):** policy-s400 1.000 x 6,21 s = 1,7 h (gemessen par.10a), W-s400 2.000 x rund 6,3 s = 3,5 h,
deviate-s400 4.000 x rund 4,9 s = 5,4 h, excursion-s400 4.000 x rund 3,4 s = 3,8 h (Schwarm: Faktor 1,95 aus
policy @400/@100 auf die @100-Zeiten aus par.9), zusammen rund 14,4 h Erzeugung; Bloecke durch den Waechter
nebenher; Merge, Training rund 40 min; Tor 1 rund 1,5 h je Seed exklusiv. Kette `tools/night_v35_b02_chain.sh`
im Terminal-Tab, Start 2026-10-05 nach Mitternacht; Laufzeiten aus den Artefakten werden nachgetragen.

### par.12a SCRATCH-MESSUNG (2026-10-05 00:05, NICHT vorregistriert, auf Nutzer-Frage *"35 % eigene Vorhersage, wie verbessern?"*): heutiger Bootstrap gegen den echten Suchwert zwei Runden spaeter

Grundmenge: Val-Satz `data/window_v35_val.txt`, Records mit `bootstrap_value` UND einem spaeteren Record derselben Seite
mindestens zwei Runden spaeter mit `root_q`, ohne Wuerfelphase, vollstaendige Partien; n = 91.490 (Runde 1-3 unten);
Einheit Brier gegen den Partieausgang. Der heutige Bootstrap ist ein SIMULIERTER Rollout des Netzes zwei Runden voraus
(`round_transition_deep.rs:802-840`: eine gezogene Rundenueberleitung plus `simulate_one_round` mit den Prioren des
Netzes, "Label-Rollout, keine Partie-Streuung"), nicht die echte Trajektorie.

| Liste (Sims) | Runde | n | Bootstrap heute (Netz-Rollout) | root_q des echten Records >= 2 Runden spaeter | root_q jetzt | Raten |
| --- | --- | --- | --- | --- | --- | --- |
| alle | 1 | 24.004 | 0,2547 | **0,2131** | 0,2553 | 0,2500 |
| alle | 2 | 33.217 | 0,2356 | **0,1875** | 0,2363 | 0,2500 |
| alle | 3 | 34.269 | 0,1976 | **0,1343** | 0,2048 | 0,2500 |
| policy @400 | 3 | 3.606 | 0,2266 | **0,1238** | 0,1968 | 0,2499 |
| policy-s100 @100 | 3 | 3.339 | 0,2319 | **0,1450** | 0,2089 | 0,2499 |

Lesart: der heutige Bootstrap ist in Runde 1 schlechter als Raten und liegt in Runde 1-3 praktisch auf dem rohen
Netzwert JETZT (0,2547 gegen 0,2553 usw.): der simulierte Rollout fuegt dem Wertziel keine Information hinzu, er
wiederholt die Vorhersage des Netzes. Der Suchwert des ECHTEN Records zwei Runden spaeter trifft den Ausgang um
0,04 bis 0,10 besser (echte Zuege, echte Kuppelplatten, Suche statt Prior). Ein TD-Ziel aus der echten Trajektorie
(n-Schritt-TD mit Such-Bootstrap, MuZero-Form) waere damit ein Wertziel, das ueber dem liegt, was das Netz schon
weiss. Reine Datenschicht (Bauschleife `corpus_dataset.py` um 1635-1690, Knopf in BEIDE Cache-Schluessel), keine
Erzeugungsaenderung: `bootstrap_value` und `root_q` liegen in jedem Record. Vorschlag: Arm `v35-b03` auf dem
b02-Fenster mit diesem Ziel, getrennt von b02 (Rezept unveraendert), damit Suchtiefe und Zielform einzeln
zuordenbar bleiben; Nutzer-Entscheid. Grenzen dieser Scratch-Messung: ungepaart, ohne CI, der spaetere Suchwert
kennt zwei Runden echten Spiels mehr (das ist der Sinn eines TD-Ziels, aber auch seine Varianzquelle), und die
Arena war bei Zielform-Aenderungen achtmal invariant (`archive/history.md` Z. 9185-9229); hier aendert sich die
INFORMATION des Ziels, nicht nur die Form.

### par.12b TRAINING v35-b02 (2026-10-05 19:53-20:21, Kette `tools/night_v35_b02_chain.sh`, GPU; Tor 1 laeuft danach)

**Erzeugung komplett 19:16:48** (vier Klassen @400 Modus 2, 11.000 Partien, 2.064.212 Zuege, 68.104,8 s = 18,9 h; je
Partie policy 6,92 s, dice 6,91 s, deviate 6,64 s, excursion 5,20 s, Threads 11 mit Cache-Waechter; Manifeste). Abnahmen
par.8 GRUEN 19:50: Tor 0 je Klasse Exit 0 (`corpus_sanity_v34-b01-*-s400.json`; policy-s400 volle Spalten je Seite 0,807
+- 0,032 bei n = 2.000 Seiten, dice 0,718 +- 0,022 bei 4.000), KL-Abnahme GREIFT (Median Abzweig 2,004 gegen q75 Referenz
1,448, Spearman +0,844, `excursion_kl_acceptance_v35_b02.json`), Vollstaendigkeit 0 unvollstaendige Partien in allen
Klassen, Cache-Waechter Exit 0. Fenster `data/window_v35_b02.txt` 1.200 Dateien (policy 100, policy-s400 100, dice 200,
deviate 400, excursion 400), Val 120 (`val_frac` 0,1, Pool `^selfplay_v34-b01-`), Train 1.080, Traeger-Manifest 400,
725 von 1.080 Bloecken maskiert, Fenster-Schluessel `8e8096768cf0`.

**Training `v35-b02`** (`manifest_train_v35-b02_20261005_195355.json`): Warmstart `v34-b01_brierbest`, Seed 20260965,
12 Epochen, 2.037.090 Samples, **1.676,8 s** Wanduhr (cpu 7.851 s, Datenaufbau 15,9 s, cuda, 6 Threads; b01: 2.198 s).
Manifest-Diff gegen das v34-b01-Rezept: 0 unerwartete Abweichungen (neu mit Default: `margin_threshold_weight`,
`margin_thresholds`, `weight_average`/`_decay`/`_from_epoch`). Auswahl: `brier_best_epoch` 5, `best_epoch` 2, gegatet wird
`alphazero_v35-b02_brierbest.onnx`.

| Epoche | policy_loss | policy_val_loss | value_loss | value_val_loss | value_val_brier |
| --- | --- | --- | --- | --- | --- |
| 1 | 1,234 | 0,4798 | 0,5454 | 0,5463 | 0,18973 |
| 2 | 1,173 | 0,4785 | 0,5418 | 0,5458 | 0,18943 |
| 5 | 1,074 | 0,4835 | 0,5363 | 0,5464 | **0,18942** |
| 8 | 1,014 | 0,4904 | 0,5333 | 0,5476 | 0,18988 |
| 12 | 0,983 | 0,4923 | 0,5322 | 0,5476 | 0,18980 |

**Lesung (vorlaeufig, Offline-Vergleich gegen den Warmstart steht aus):** dasselbe Muster wie v34-b01 und v35-b01 (par.17,
Tabelle): der Val-Brier bewegt sich ueber zwoelf Epochen um 0,0005 (Spanne 0,18942 bis 0,18990), waehrend der
Trainings-Wertverlust um 0,013 faellt; der Policy-Val-Verlust hat sein Minimum in Epoche 2 und steigt danach monoton
(0,4785 auf 0,4923). Das Brier-NIVEAU (0,189 gegen 0,195 bei b01) ist NICHT vergleichbar: anderer Val-Satz (b02-Val sind
@400-Partien, b01-Val @100-Partien). Ob das @400-Material den Wertkopf gegenueber dem Warmstart `v34-b01_brierbest`
bewegt (die Frage von par.12), misst erst `tools/checkpoint_val_eval.py` auf dem b02-Val-Satz (Warmstart gegen Epoche 2
und 5, Muster par.11b) nach dem Ende von Tor 1 (Last). Tor 1 gestartet 20:21:54.

### par.12c TOR 1 v35-b02 gegen v34-b01, SEED 20261600 (2026-10-05 20:22-22:20, exklusiv, `tools/paired_gating.py` @400 beidseits, Spec `v34-b01_brierbest`, Blockgroesse 5, 200 Paare, `--log-games`)

**Ergebnis Seed 1: v35-b02 218:182 = 54,5 %** (n = 400 Partien, 200 Paare, Grundmenge Partien je Modell), Block-z **+1,51**
(40 Bloecke, Mittel 0,545, sd 0,188; `tools/gating_block_z.py`), gepaarte Differenz +0,18 [-0,019; +0,379], Paare
A-Sweep 61 / B-Sweep 43 / Split 96, McNemar p = 0,095, SPRT `UNDECIDED_CAP_REACHED` (LLR +0,67). Verlauf: 61:39
nach 50 Paaren, 116:84 nach 100, 162:138 nach 150, 218:182 am Deckel (Bloecke 21-40 zusammen 102:98). Laufzeit
**7.061,2 s** (17,65 s je Partie, 10 Threads, cpu 31.157 s; b01 Seed 1 gebremst 23,8 s, exklusive Referenz 13,6 s; ob
Nebenlast anlag, ist UNGEPRUEFT). Artefakt `gating_v35-b02_vs_v34-b01_s20261600.json`.

**Kriterium (par.12, par.11):** Block-z >= +1,96 ODER gepoolt >= 52,5 % ohne Gegenbefund. Seed 1 allein: Block-z unter
der Linie, Siegquote darueber; die Kette faehrt Seed 20261601 (laeuft seit 22:20), Verdikt auf dem gepoolten Block-z
ueber beide Seeds, Stufenregel 20261602 falls genau ein Seed die Block-z-Linie nimmt.

**Sechs Standard-Kennzahlen Seed 1** (Grundmenge je Modell 400 Bretter; `arena_columns_gating_..._s20261600.json`,
Tor 2b GRUEN, 400 von 400 Partien aus dem Record; `plate_points_v35-b02_vs_v34-b01_s20261600.json`, Plausibilitaet
400/400):

| Kennzahl | v35-b02 | v34-b01 |
| --- | --- | --- |
| Volle Spalten je Brett | **1,085** (CI95 +-0,073) | 0,978 (+-0,073) |
| Spalten >= 4 / >= 3 / max. Hoehe | 2,41 / 3,35 / 5,73 | 2,30 / 3,20 / 5,67 |
| Volle Zeilen / Zeilenfuellung Summe | 0,11 / 18,32 | 0,08 / 17,55 |
| Strafleiste (Steine gesamt je Brett) | 8,12 | 7,35 |
| Eigene Punkte | 57,92 | 56,20 |
| Marge | +1,72 [-0,06; +3,50] | -1,72 |
| Plattenpunkte gesamt | 8,27 | 7,72 |
| je Kriterium (nur aktiv): Vertikale 7,25 / Aeussere 10,49 / Eckplatten 9,13 / Mehrfarbige 4,07 / Spezialfelder -9,57 / Diagonale 0,48 / Horizontale 0,35 / Farbenreiche 0,19 | | 7,21 / 10,01 / 8,95 / 4,04 / -10,05 / 0,24 / 0,35 / 0,16 |

Lesung (Seed 1, ohne Verdikt): b02 baut mehr volle Spalten (+0,11 je Brett, CIs ueberlappen knapp) und holt auf allen
Plattenkriterien mindestens gleich viel, am deutlichsten Aeussere Felder (+0,47) und Spezialfelder (+0,47 weniger
Abzug); dafuer mehr Strafsteine (+0,77 je Brett). Vergleich b01 Seed 1 (par.11c): 208:192, Block-z +0,92, Spalten
1,078 gegen 1,128; b02 liegt in Siegquote, Block-z und Spalten vor b01, bei gleichem Gegner und gleicher Spec.

### par.12d TOR 1 v35-b02 gegen v34-b01, SEED 20261601 und GEPOOLT (2026-10-05 22:20 bis 2026-10-06 00:19, exklusiv, Aufbau wie par.12c)

**Ergebnis Seed 2: v35-b02 219:181 = 54,75 %** (n = 400 Partien, 200 Paare), Block-z **+2,12** (40 Bloecke, Mittel
0,5475, sd 0,141), gepaarte Differenz +0,19 [-0,002; +0,382], Paare A-Sweep 58 / B-Sweep 39 / Split 103, McNemar
p = 0,067, SPRT `UNDECIDED_CAP_REACHED` (LLR +1,31). Laufzeit **7.185,2 s** (17,96 s je Partie, 10 Threads).
Artefakt `gating_v35-b02_vs_v34-b01_s20261601.json`.

**Gepoolt Seed 1 + Seed 2: 437:363 = 54,6 %** (n = 800 Partien), **Block-z +2,50** (80 Bloecke, Mittel 0,5463, sd
0,165; Kettenausgabe von `tools/gating_block_z.py`). Kriterium par.12: gepoolter Block-z >= +1,96 ERFUELLT und gepoolt
>= 52,5 % ERFUELLT. **Stufenregel greift trotzdem:** genau EIN Seed nimmt einzeln die Block-z-Linie (Seed 1 +1,51, Seed 2
+2,12), darum laeuft Seed 20261602 (Start 00:19:27, identische Einstellungen); das Verdikt faellt auf dem gepoolten
Block-z ueber alle drei Seeds (par.11, `PREREG_v34_window.md` par.2). Vorab, damit es nicht nachtraeglich gelesen wird:
ein dritter Seed mit Block-z um 0 wuerde den gepoolten z ueber 120 Bloecke auf rund +2,0 druecken (HERLEITUNG: Mittel
(80 x 0,5463 + 40 x 0,50)/120 = 0,531, sd rund 0,165, z = 0,031 / (0,165 / sqrt(120)) = +2,06); ein Seed unter 50 %
wuerde ihn unter die Linie bringen.

**Sechs Standard-Kennzahlen Seed 2** (400 Bretter je Modell; `arena_columns_gating_..._s20261601.json` Tor 2b GRUEN,
`plate_points_..._s20261601.json`):

| Kennzahl | v35-b02 | v34-b01 |
| --- | --- | --- |
| Volle Spalten je Brett | **1,097** (CI95 +-0,076) | 0,985 (+-0,070) |
| Spalten >= 4 / >= 3 / max. Hoehe | 2,41 / 3,37 / 5,72 | 2,23 / 3,13 / 5,72 |
| Volle Zeilen / Zeilenfuellung Summe | 0,10 / 18,33 | 0,06 / 17,39 |
| Strafleiste (Steine je Brett) | 8,37 | 7,67 |
| Eigene Punkte | 58,69 | 55,28 |
| Marge | +3,41 (Punkte, gepaart +0,19 Siege [-0,00; +0,38]) | -3,41 |
| Plattenpunkte gesamt | 9,04 | 7,67 |
| je Kriterium: Vertikale 8,42 / Aeussere 10,27 / Eckplatten 9,19 / Mehrfarbige 4,09 / Spezialfelder -9,55 / Diagonale 0,59 / Horizontale 0,35 / Farbenreiche 0,33 | | 6,92 / 10,11 / 8,70 / 3,97 / -10,10 / 0,29 / 0,16 / 0,10 |

Gepaart je Kriterium (b02 minus b01, Kettenausgabe): Vertikale Reihen **+1,50 [+0,45; +2,55]** (84 Paare), Farbenreiche
Reihen +0,24 [+0,03; +0,44], alle uebrigen mit CI ueber 0. Lesung Seed 2: wie Seed 1 mehr volle Spalten (+0,11 je
Brett), mehr Punkte (+3,4), mehr Plattenpunkte (+1,4, getragen von Vertikale Reihen), mehr Strafsteine (+0,7). Beide
Seeds zeigen dieselbe Richtung in allen sechs Kennzahlen.

### par.12e TOR 1 v35-b02 gegen v34-b01, SEED 20261602 (Stufenregel) und VERDIKT (2026-10-06 00:19-01:32, exklusiv; Kette fertig 01:32:32)

**Seed 3: v35-b02 159:91 = 63,6 %** nach 125 Paaren (n = 250 Partien), SPRT `ACCEPT_H1` fuer v35-b02 (LLR +7,22 ueber
der Schranke +6,91, Stopp vor dem Deckel), Block-z **+3,99** (25 Bloecke, Mittel 0,636, sd 0,171), gepaarte Differenz
+0,54 [+0,30; +0,79], Paare A-Sweep 52 / B-Sweep 18 / Split 55, McNemar p = 0,00006. Laufzeit 4.382,4 s (17,53 s je
Partie, 10 Threads). Artefakt `gating_v35-b02_vs_v34-b01_s20261602.json`. Der fruehe Stopp zaehlt hier, weil die
Seeds 1 und 2 bis zum Deckel liefen (Regel "frueher Stopp nur nach Replikation bis zum Deckel", `docs/generation_loop.md`).

**GEPOOLT ueber drei Seeds: 596:454 = 56,8 %** (n = 1.050 Partien, 525 Paare), **Block-z +4,07** (105 Bloecke, Mittel
0,5676, sd 0,170; Kettenausgabe `tools/gating_block_z.py`, gleiche Zahl von Hand reproduziert).

| Seed | Ergebnis | Block-z | Bloecke |
| --- | --- | --- | --- |
| 20261600 | 218:182 = 54,5 % | +1,51 | 40 |
| 20261601 | 219:181 = 54,75 % | +2,12 | 40 |
| 20261602 | 159:91 = 63,6 % (SPRT-Stopp) | +3,99 | 25 |
| gepoolt | 596:454 = 56,8 % | **+4,07** | 105 |

**VERDIKT TOR 1: v35-b02 TRAEGT.** Kriterium par.12 (Block-z >= +1,96 oder gepoolt >= 52,5 % ohne Gegenbefund):
beides erfuellt, kein Gegenbefund in den sechs Kennzahlen (unten). Zuordnung wie vorab festgelegt (par.12 "Tore"): der
Gewinn gehoert der Erzeugungs-Suchtiefe (400 statt 100 Sims) PLUS Modus 2 in allen Klassen, bei unveraendertem Rezept;
die beiden Anteile sind nicht getrennt. Deskriptiv gegen b01 (par.11c, ein Seed, gebremst): 52,0 % / z +0,92 gegen
54,5 % / z +1,51 auf demselben Seed 20261600.

**Tor 2a** (ex post, `corpus_sanity` der Policy-Klassen gegen 0,826 = `policy` @400 M2 aus par.10b): policy-s400
**0,807 +- 0,032** volle Spalten je Seite (n = 2.000 Seiten) = gleich bedingt (CI deckt 0,826); policy-dice-v2-r1-s400
0,718 +- 0,022 (n = 4.000) liegt darunter, ist aber die W-Klasse mit Wuerfel-Eroeffnung und hatte in par.10b keinen
eigenen Bezugswert (ungeprueft, ob die @100-W-Klasse hoeher lag; deskriptiv). **Tor 2b** (volle Spalten aus den
Tor-1-Logs): b02 in allen drei Seeds ueber v34-b01 (1,085 / 1,097 / 1,108 gegen 0,978 / 0,985 / 1,040 je Brett),
GRUEN.

**Sechs Standard-Kennzahlen Seed 3** (250 Bretter je Modell; Tor 2b GRUEN, Plausibilitaet 250/250):

| Kennzahl | v35-b02 | v34-b01 |
| --- | --- | --- |
| Volle Spalten je Brett | **1,108** (+-0,094) | 1,040 (+-0,091) |
| Spalten >= 4 / >= 3 / max. Hoehe | 2,44 / 3,43 / 5,73 | 2,28 / 3,08 / 5,73 |
| Volle Zeilen / Zeilenfuellung Summe | 0,12 / 18,56 | 0,09 / 17,51 |
| Strafleiste (Steine je Brett) | 7,56 | 7,65 |
| Eigene Punkte | 60,88 | 55,92 |
| Marge | +4,96 Punkte (gepaart +0,54 Siege [+0,30; +0,79]) | -4,96 |
| Plattenpunkte gesamt | 9,22 | 8,63 |
| je Kriterium: Vertikale 8,75 / Aeussere 10,54 / Eckplatten 9,64 / Mehrfarbige 3,90 / Spezialfelder -9,48 / Diagonale 0,47 / Horizontale 0,38 / Farbenreiche 0,27 | | 8,47 / 10,09 / 9,47 / 3,90 / -9,62 / 0,19 / 0,38 / 0,04 |

Gepaart je Kriterium Seed 3 (b02 minus b01, Kettenausgabe): Aeussere Felder +0,45 [+0,08; +0,82], Farbenreiche Reihen
+0,23 [+0,03; +0,44], uebrige CI ueber 0. Ueber die drei Seeds hinweg: b02 baut 0,07 bis 0,11 volle Spalten je Brett
mehr, holt 1,7 bis 5,0 Punkte mehr je Partie, mehr Plattenpunkte (Seed 2: Vertikale Reihen gepaart +1,50 [+0,45;
+2,55]); Strafsteine in Seed 1 und 2 rund 0,7 je Brett mehr, in Seed 3 gleich.

**Laufzeiten Tor 1 (gemessen):** 7.061 + 7.185 + 4.382 = 18.629 s = 5,2 h fuer 1.050 Partien, 17,5 bis 18,0 s je Partie
bei 10 Threads (exklusive Referenz b01-Aera 13,6 s; ob Nebenlast anlag, ist UNGEPRUEFT). Kette gesamt 00:21 bis 01:32:32
= 25,2 h (Erzeugung 18,9 h, Abnahmen 0,6 h, Fenster/Merge 0,1 h, Training 0,5 h, Tor 1 5,2 h).

**Faellig (par.12, Kettenausgabe):** Netz-Gesundheit und Offline-Vergleich gegen den Warmstart (par.12f), Elo-Register
(drei Kanten) NUR mit der Promotion, Promotion NUR nach Nutzer-Entscheid und `/mosaic-champion-promotion`
(Ein-Promotion-Regel je Generation; die Arme b03-b10 messen weiter gegen v34-b01, Baseline b02 bleibt vergleichbar).

### par.12f NETZ-GESUNDHEIT UND OFFLINE-VERGLEICH GEGEN DEN WARMSTART (2026-10-06 01:4x, exklusiv, nach der Kette)

**Netz-Gesundheit** (`tools/checkpoint_weight_health.py`, Referenz `v34-b01_brierbest`, `weight_health_v35-b02.json`):
`_best` und `_brierbest` GESUND, keine NaN/Inf, BN-tot 0/1.120 in 4 BN-Schichten; relative Aenderung 0,00 %
(moon_order_head, ownership_head: eingefroren bzw. Gewicht 0) bis 17,99 % (value_head.0); value_head.2 13,65 %,
points_head.0 17,41 %, opp_points_head.0 17,31 %.

**Offline-Vergleich auf dem b02-Val-Satz** (`tools/checkpoint_val_eval.py`, 120 Val-Dateien, 225.789 Zustaende, 3
Checkpoints, 32,6 s cuda; `checkpoint_val_eval_v35-b02_vs_warmstart.json`; Referenz minus Checkpoint, > 0 = Checkpoint
besser; Block-Bootstrap ueber Dateien):

| Checkpoint | Val-Brier | dBrier gegen Warmstart [CI95] | dPolicy-CE gepoolt [CI95] |
| --- | --- | --- | --- |
| `v34-b01_brierbest` (Warmstart) | 0,19050 | | |
| `v35-b02_best` (Epoche 2) | 0,18943 | **+0,00107 [+0,00041; +0,00169]** | +0,158 [+0,149; +0,166] |
| `v35-b02_brierbest` (Epoche 5) | 0,18942 | **+0,00108 [+0,00022; +0,00191]** | +0,145 [+0,136; +0,153] |

**Das ist die Antwort auf die par.12-Frage:** auf dem @400-Fenster lernt der Wertkopf messbar (CI ganz ueber 0), auf
dem @100-Fenster von b01 nicht (par.11b: +0,0006 [-0,0003; +0,0014], Val-Satz dort die @100-Partien). Die Groesse ist
klein (0,001 Brier, rund 0,6 %), aber sie ist da, und die Richtung passt zur Arena. Grundmenge beider Messungen
verschieden (je der eigene Val-Satz), die Aussage ist je Fenster "Warmstart gegen trainiert", nicht b01 gegen b02.

**Netz gegen Wurzel-Q (par.11d-Muster, derselbe Val-Satz, @400-Partien):** fuer den Warmstart liegt die Suche ab R2 vor
dem Netz (R2 +0,0049 [+0,0007; +0,0087], R3 +0,0104, R4 +0,0145, R5 +0,0264, R1 -0,0006 n.s.); fuer `v35-b02_brierbest`
ab R3 (R2 +0,0031 [-0,0010; +0,0070] n.s., R3 +0,0095 [+0,0062; +0,0129], R4 +0,0136, R5 +0,0243, R1-4 +0,0069
[+0,0042; +0,0096]). Die @400-Suche hat dem b02-Netz also weiter etwas voraus; die Vor-Erzeugungs-Regel
(`docs/generation_loop.md`, `root_q_compare`) waere fuer b02 als Generator @400 erfuellt, @100 nicht gemessen.

## par.13 ARME v35-b03 (k=1) / v35-b05 (k=2) / v35-b06 (k=3): WERTZIEL MIT TRAJEKTORIEN-BOOTSTRAP (NUTZER 2026-10-05 00:1x: *"mach mir auch b03 in verschiedenen tiefen"*; REGISTRIERT VOR Bau-Abnahme und Lauf)

**Grund:** par.12a. Der TD-Bootstrap im WDL-Wertziel ist heute ein simulierter Netz-Rollout und liegt auf dem rohen
Netzwert; der Suchwert des echten Records derselben Seite k Runden spaeter trifft den Ausgang um 0,04 bis 0,10
besser (Scratch, Val-Satz b01). Nutzer-Hinweis: nicht jeder Rundenuebergang braucht die volle Tiefe; k ist eine
OBERGRENZE, fehlt ein Record der Seite bei Runde >= rd + k (Partieende naeher), ist der Bootstrap der echte Ausgang.

**Knopf (gebaut 2026-10-05 00:10-00:20, Agent; Abnahme Standardweg bitgleich an einem Block, Koordinator 00:25):**
`MOSAIC_BOOTSTRAP_SOURCE=trajectory` plus `MOSAIC_BOOTSTRAP_HORIZON_ROUNDS=k` (k in 1..3; ungueltig = harter
Fehler). Wirkung nur im WDL-Zweig der Bauschleife (`corpus_dataset.py` um 1704-1725): `value_wdl = TD_LAMBDA * bvp +
(1 - TD_LAMBDA) * wdl_outcome` mit `bvp` = `root_q` ([0,1], Sicht des Ziehers) des ersten spaeteren Records derselben
Partie und Seite mit Runde >= rd + k, ohne Wuerfelphase; sonst `bvp` = Ausgang. Marker `bootstraptraj_h<k>_v1` in
BEIDEN Cache-Schluesseln (`file_cache_key.py:386-388`, `corpus_dataset.py:790-793`); reine Funktion
`engine/py/trajectory_bootstrap.py`, Test `tools/tests/test_trajectory_bootstrap.py` (15 Faelle, gruen, torch-frei);
`docs/knobs.md` und `knob_registry.rs` nachgezogen. Unveraendert: `apply_value_target_lambda` 0,7 mit `root_q` jetzt,
`wdl_outcome`, Masken, `value_weights`, tanh-Zweig. Val-Brier bleibt gegen `wdl_outcome` gerechnet
(`train.py:1046-1051`), also zwischen Armen vergleichbar. Ziel-Zusammensetzung im Arm (HERLEITUNG): 0,35 Ausgang +
0,35 Suchwert spaeter + 0,30 Suchwert jetzt; kein Anteil mehr aus dem rohen Netz.

**Arme (Namen vom Nutzer 2026-10-05 00:4x: *"benenn mir b03-h1 um auf b03, -h2 auf b05 und h3 auf b06"*):**
`v35-b03` (k = 1), `v35-b05` (k = 2), `v35-b06` (k = 3) auf dem b02-FENSTER (par.12; gleiche 1.200 Dateien, gleiches
Traeger-Manifest, Val 120, Seed 20260965, Warmstart `v34-b01_brierbest`, Rezept byte-gleich b02 bis auf die zwei
Knopf-Variablen); je Arm eigene Bloecke und eigener Monolith (Marker im Schluessel; HERLEITUNG rund 16 min Bloecke +
3 min Merge + 37 min Training je Arm). Reihenfolge nach Tor 1 von b02. Gegatet je Arm das Brier-beste Netz
(`brier_best_checkpoint.py`). Vorab benannt: der Val-Brier ist zwischen den Armen vergleichbar, sagt aber nichts
ueber Arena-Staerke (`project_offline_metric_resolution_limit`); er wird berichtet, entscheidet nicht.

**Tore (Stufenform, vorab):** jeder Arm bekommt Tor 1 gegen `v34-b01` mit Seed 20261600 (200 Paare, Einstellungen
wie par.11). Ein Arm mit Block-z >= +1,96 ODER >= 52,5 % auf Seed 1 bekommt Seed 20261601; Verdikt je Arm gepoolt
wie par.11 (Stufenregel 20261602). Arme ohne diese Schwelle auf Seed 1: ein Seed, nicht entschieden, berichtet.
Vergleich mit b02 deskriptiv auf denselben Seeds. Zuordnung vorab: ein Gewinn gegen b02 gehoert dem Wertziel
(Bootstrap-Quelle und Tiefe), nicht der Suchtiefe. Tor 2a entfaellt (gleiches Fenster wie b02), Tor 2b aus den Logs.
Kosten HERLEITUNG: 3 x 56 min Bau+Training, Seed 1 je Arm rund 1,5 h exklusiv (4,5 h), Seed 2 nach Schwelle.

**Nebenbefund zur Erosion (Vorwissen, `archive/history.md` Z. 9185-9229):** das reine Ausgangs-Ziel erodierte 2026-08-05
nach Epoche 2-3 (Memorisierung); ein tieferer Bootstrap liegt naeher am Ausgang und koennte dieselbe Erosion zeigen.
Die Brier-Auswahl faengt das ab; die Epochenkurve je Arm wird berichtet (Peak-Epoche, Erosion bis Epoche 12).

### par.13a ERGEBNIS v35-b03 (k = 1): TRAINING UND TOR 1 SEED 1 (2026-10-06 06:45-08:46, `tools/night_v35_arms_chain.sh`, exklusiv)

**Bau und Training:** Bloecke mit Marker `bootstraptraj_h1_v1` fuer alle 1.200 Dateien plus Merge in rund 20 min
(06:45-07:05), Split byte-gleich b02 (Kette diffte Train- und Val-Liste), Training `v35-b03` 1.688,6 s
(`manifest_train_v35-b03_20261006_070121.json`, `mosaic_env` MOSAIC_BOOTSTRAP_SOURCE=trajectory, HORIZON_ROUNDS=1,
Traeger v35_b02), Manifest-Diff gegen b02 ohne unerwartete Abweichung (Kette lief weiter). Val-Brier auf denselben 120
Val-Dateien wie b02: Epoche 1 0,19013, Minimum **0,18965 in Epoche 5**, Epoche 12 0,18994 (b02: 0,18942 in Epoche 5);
`policy_val_loss` Minimum Epoche 2 (0,4784, b02 0,4785), danach steigend wie in allen Armen. Der `value_val_loss`
(0,5442 gegen 0,5458) ist NICHT vergleichbar, weil b03 ein anderes Ziel mischt. Offline liegt b03 damit beim Brier
0,0002 UNTER b02 (schlechter), ohne gepaartes CI; die gepaarte Messung (`checkpoint_val_eval.py`, b02 gegen b03) folgt
nach der Arm-Kette.

**Tor 1 Seed 20261600: v35-b03 159:91 = 63,6 %** nach 125 Paaren (n = 250 Partien), SPRT `ACCEPT_H1` (LLR +7,32,
Stopp vor dem Deckel), Block-z **+5,28** (25 Bloecke, Mittel 0,636, sd 0,129), gepaarte Differenz +0,54 [+0,30; +0,79],
McNemar p = 0,00004. Laufzeit 4.436,7 s (17,75 s je Partie, 10 Threads). Tor 2b GRUEN: volle Spalten je Brett 1,080
gegen 1,016, Punkte 59,13 gegen 55,63, Strafsteine 8,13 gegen 7,65 (n = 250 Bretter je Modell). Artefakt
`gating_v35-b03_vs_v34-b01_s20261600.json`. Auf demselben Seed 20261600 lag b02 bei 218:182 ueber 200 Paare (par.12c);
die Zahl 159:91 ist zufaellig dieselbe wie b02 Seed 3 (anderer Seed). Stufe genommen, Seed 20261601 laeuft (seit 08:46).

**Lesung vorab (ohne Verdikt):** ein fruehes SPRT-Ende zaehlt erst nach Replikation; das Verdikt faellt wie bei b02 auf
dem gepoolten Block-z ueber alle Seeds. Offline (Brier) und Arena zeigen bei b03 nicht in dieselbe Richtung; welche
Groesse die Staerke traegt, ist genau die Frage von par.13 ("Korpus wirkt, Gewicht nicht" oder umgekehrt).

### par.13b VERDIKT v35-b03 (k = 1): TOR 1 SEED 2 UND GEPOOLT (2026-10-06 08:46-10:46, exklusiv)

**Seed 20261601: v35-b03 222:178 = 55,5 %** (n = 400, 200 Paare, Deckel), Block-z **+2,64** (40 Bloecke, Mittel 0,555,
sd 0,132), gepaarte Differenz +0,22 [+0,03; +0,41], SPRT `UNDECIDED_CAP_REACHED`, 17,86 s je Partie.

**Gepoolt: 381:269 = 58,6 %** (n = 650 Partien, 325 Paare), **Block-z +5,12** (65 Bloecke, Mittel 0,586, sd 0,136).
Beide Seeds einzeln ueber +1,96, die Stufenregel (dritter Seed nur bei genau einem) greift nicht; die Kette geht zu b05.

**VERDIKT TOR 1: v35-b03 TRAEGT** (Kriterium par.13 wie par.12: Block-z >= +1,96 oder gepoolt >= 52,5 % ohne
Gegenbefund; beides erfuellt). Die sechs Kennzahlen zeigen in beiden Seeds dieselbe Richtung wie bei b02:

| Kennzahl je Brett | b03 Seed 1 / v34-b01 (n = 250) | b03 Seed 2 / v34-b01 (n = 400) |
| --- | --- | --- |
| Volle Spalten | 1,080 / 1,016 | 1,097 / 1,010 |
| Spalten >= 4 / >= 3 | 2,45 / 3,38 gegen 2,29 / 3,12 | 2,45 / 3,39 gegen 2,28 / 3,12 |
| Volle Zeilen / Zeilenfuellung | 0,10 / 18,30 gegen 0,04 / 17,48 | 0,10 / 18,38 gegen 0,06 / 17,39 |
| Strafsteine | 8,13 / 7,65 | 7,90 / 7,04 |
| Eigene Punkte | 59,13 / 55,63 | 58,47 / 56,62 |
| Plattenpunkte gesamt | 8,68 / 7,76 | 8,81 / 7,86 |
| Vertikale Reihen (nur aktiv) | 8,05 / 7,42 | 8,00 / 7,29 |
| Mehrfarbige Felder | 4,87 / 4,15 | 4,35 / 3,86 |
| Spezialfelder | -9,55 / -9,73 | -9,24 / -9,86 |

**Einordnung gegen b02 (deskriptiv, gleicher Gegner, gleiche Seeds, gleiche Spec):** b02 kam auf denselben zwei Seeds
auf 437:363 = 54,6 % (z +2,50, 80 Bloecke), b03 auf 381:269 = 58,6 % (z +5,12, 65 Bloecke; Seed 1 frueh gestoppt).
Vier Punkte Unterschied bei n = 800 gegen 650 liegen in der Groessenordnung der Seed-Streuung (CLAUDE.md: 5,75 Punkte bei
n = 400 fuer identische Konfiguration); ob b03 staerker als b02 ist, sagt nur eine direkte Kante b03 gegen b02, die hier
nicht vorregistriert ist (Nutzer-Entscheid, s. par.13 Lesart). Offline lag b03 beim Brier 0,0002 unter b02 (par.13a), die
gepaarte Offline-Messung folgt nach der Arm-Kette. Einziger Unterschied zu b02 ist die Bootstrap-Quelle im Wertziel
(echter Suchwert eine Runde spaeter statt simulierter Rollout zwei Runden spaeter), bei bitgleichem Fenster, Val-Satz,
Seed und Rezept.

**Laufzeiten:** Bloecke und Merge rund 20 min, Training 1.688,6 s, Tor 1 4.437 + 7.142 s (gerundet; 17,7 bis 17,9 s je
Partie, 10 Threads); Arm gesamt rund 4,0 h.

### par.13c ERGEBNIS v35-b05 (k = 2): TRAINING UND TOR 1 SEED 1 (2026-10-06 10:46-13:27, Arm-Kette, exklusiv)

**Training** `v35-b05` 1.674,7 s (`manifest_train_v35-b05_20261006_105829.json`, `mosaic_env` BOOTSTRAP_SOURCE=trajectory,
HORIZON_ROUNDS=2), Val-Brier auf den 120 b02-Val-Dateien: Minimum **0,18970 in Epoche 2** (b02 0,18942, b03 0,18965),
Epoche 12 0,19030; Brier-Minimum faellt mit der kombinierten Auswahl zusammen, darum kein eigenes `_brierbest`, gegatet
wird `alphazero_v35-b05_best.onnx` (Epoche 2). `policy_val_loss` Minimum Epoche 2 (0,4784) wie in allen Armen.

**Tor 1 Seed 20261600: v35-b05 224:176 = 56,0 %** (n = 400, 200 Paare, Deckel), Block-z **+2,53** (40 Bloecke, Mittel
0,560, sd 0,150), gepaarte Differenz +0,24 [+0,05; +0,43], SPRT `UNDECIDED_CAP_REACHED`, 17,84 s je Partie. Tor 2b:
volle Spalten je Brett 1,050 gegen 1,005, Punkte 58,65 gegen 55,46, Strafsteine 7,93 gegen 7,99. Stufe genommen,
Seed 20261601 laeuft. Zum Vergleich auf demselben Seed: b02 218:182 (z +1,51), b03 159:91 nach 125 Paaren (z +5,28).

### par.13d VERDIKT v35-b05 (k = 2): TOR 1 SEED 2 UND GEPOOLT (2026-10-06 13:27-15:28, exklusiv)

**Seed 20261601: v35-b05 227:173 = 56,75 %** (n = 400, Deckel), Block-z **+2,93** (40 Bloecke, Mittel 0,5675, sd 0,146),
gepaarte Differenz +0,27 [+0,08; +0,46], SPRT `UNDECIDED_CAP_REACHED`, 7.275 s (18,19 s je Partie).

**Gepoolt: 451:349 = 56,4 %** (n = 800, 400 Paare), **Block-z +3,88** (80 Bloecke, Mittel 0,564, sd 0,147). Beide Seeds
einzeln ueber +1,96, kein dritter Seed. **VERDIKT TOR 1: v35-b05 TRAEGT** (Kriterium par.13 wie par.12).

| Kennzahl je Brett | Seed 1: b05 / v34-b01 (n = 400) | Seed 2: b05 / v34-b01 (n = 400) |
| --- | --- | --- |
| Volle Spalten | 1,050 / 1,005 | 1,048 / 1,010 |
| Spalten >= 4 / >= 3 | 2,43 / 3,32 gegen 2,32 / 3,20 | 2,41 / 3,38 gegen 2,25 / 3,14 |
| Volle Zeilen / Zeilenfuellung | 0,10 / 18,22 gegen 0,05 / 17,53 | 0,08 / 18,18 gegen 0,06 / 17,57 |
| Strafsteine | 7,93 / 7,99 | 7,92 / 7,72 |
| Eigene Punkte | 58,65 / 55,46 | 58,04 / 55,75 |
| Plattenpunkte gesamt | 9,10 / 7,73 | 8,91 / 7,91 |
| Vertikale / Mehrfarbige / Spezialfelder | 8,18 / 4,84 / -9,45 gegen 7,67 / 3,29 / -10,01 | 7,71 / 4,34 / -9,38 gegen 6,96 / 4,17 / -9,97 |

Gleiche Richtung wie b02 und b03 in allen Kennzahlen; der Spaltenvorsprung ist kleiner (+0,04 je Brett gegen +0,07 bis
+0,11 bei b03), die Strafsteine liegen gleichauf statt darueber. Reihe auf den Seeds 20261600/01 gegen v34-b01, gepoolt:
b02 54,6 % (z +2,50), b03 58,6 % (z +5,12, Seed 1 frueh gestoppt), b05 56,4 % (z +3,88); Unterschiede innerhalb der
Seed-Streuung, keine direkten Kanten zwischen den Armen (Nutzer-Entscheid). Arm gesamt rund 4,7 h.

### par.13e ERGEBNIS v35-b06 (k = 3): TRAINING (2026-10-06 15:28-16:10, Arm-Kette); Tor 1 laeuft

**Training** `v35-b06` 1.689,5 s (`manifest_train_v35-b06_20261006_154232.json`, `mosaic_env` BOOTSTRAP_SOURCE=trajectory,
HORIZON_ROUNDS=3), Val-Brier auf den 120 b02-Val-Dateien: Minimum **0,18965 in Epoche 2**, Epoche 12 0,19067; kein
eigenes `_brierbest` (Minimum = Auswahl), gegatet `alphazero_v35-b06_best.onnx`. Brier-Minima der Bootstrap-Reihe auf
demselben Val-Satz: b02 0,18942 (Epoche 5), b03 0,18965 (5), b05 0,18970 (2), b06 0,18965 (2); Spanne 0,0003, ohne
gepaartes CI nicht unterscheidbar. Tor 1 Seed 20261600 seit 16:10.

**Tor 1 Seed 20261600: v35-b06 231:169 = 57,75 %** (n = 400, Deckel), Block-z **+3,05** (40 Bloecke, Mittel 0,5775,
sd 0,161), gepaarte Differenz +0,31 [+0,11; +0,51], SPRT `UNDECIDED_CAP_REACHED`, 17,76 s je Partie. Tor 2b: volle
Spalten je Brett 1,062 gegen 0,990, Punkte 58,11 gegen 55,39, Strafsteine 7,97 gegen 8,32 (b06 WENIGER, erster Arm mit
weniger Strafsteinen als der Champion), Plattenpunkte 8,88 gegen 7,68 (Spezialfelder -9,04 gegen -10,36, Eckplatten
9,70 gegen 8,87). Stufe genommen, Seed 20261601 laeuft seit 18:11.

### par.13f VERDIKT v35-b06 (k = 3): TOR 1 SEED 2 UND GEPOOLT (2026-10-06 18:11-20:10, exklusiv)

**Seed 20261601: v35-b06 224:176 = 56,0 %** (n = 400, Deckel), Block-z **+2,35** (40 Bloecke, Mittel 0,560, sd 0,161),
gepaarte Differenz +0,24 [+0,04; +0,44], SPRT `UNDECIDED_CAP_REACHED`, 7.096 s (17,74 s je Partie).

**Gepoolt: 455:345 = 56,9 %** (n = 800, 400 Paare), **Block-z +3,83** (80 Bloecke, Mittel 0,569, sd 0,160). Beide Seeds
einzeln ueber +1,96, kein dritter Seed. **VERDIKT TOR 1: v35-b06 TRAEGT** (Kriterium par.13 wie par.12).

| Kennzahl je Brett | Seed 1: b06 / v34-b01 (n = 400) | Seed 2: b06 / v34-b01 (n = 400) |
| --- | --- | --- |
| Volle Spalten | 1,062 / 0,990 | 1,060 / 0,983 |
| Spalten >= 4 / >= 3 | 2,35 / 3,35 gegen 2,27 / 3,21 | 2,35 / 3,37 gegen 2,28 / 3,15 |
| Volle Zeilen / Zeilenfuellung | 0,12 / 18,20 gegen 0,08 / 17,67 | 0,12 / 18,22 gegen 0,08 / 17,55 |
| Strafsteine | 7,97 / 8,32 | 8,03 / 8,03 |
| Eigene Punkte | 58,11 / 55,39 | 58,78 / 55,98 |
| Plattenpunkte gesamt | 8,88 / 7,68 | 9,02 / 7,67 |
| Spezialfelder / Eckplatten / Mehrfarbige | -9,04 / 9,70 / 4,29 gegen -10,36 / 8,87 / 3,90 | -8,96 / 9,64 / 4,32 gegen -10,37 / 9,42 / 3,49 |

Eigenart von b06 gegenueber b02, b03 und b05: Strafsteine nicht ueber dem Champion (Seed 1 darunter, Seed 2 gleich) und
der kleinste Spezialfeld-Abzug der Reihe (-9,0 gegen -10,4); der Spaltenvorsprung (+0,07 je Brett) liegt zwischen b05 und
b03.

**Bootstrap-Reihe par.13 komplett, alle drei Tiefen tragen gegen v34-b01, gepoolt ueber die Seeds 20261600/01:**

| Arm | k | Gepoolt | Block-z | Val-Brier-Minimum |
| --- | --- | --- | --- | --- |
| b02 (Referenz, simulierter Rollout, Horizont 2) | - | 437:363 = 54,6 % | +2,50 | 0,18942 |
| b03 | 1 | 381:269 = 58,6 % (Seed 1 frueh gestoppt) | +5,12 | 0,18965 |
| b05 | 2 | 451:349 = 56,4 % | +3,88 | 0,18970 |
| b06 | 3 | 455:345 = 56,9 % | +3,83 | 0,18965 |

Lesung zur Frage von par.13 (traegt die Bootstrap-Quelle etwas ueber b02 hinaus?): alle drei liegen deskriptiv ueber
b02, mit 2 bis 4 Punkten Abstand bei n = 650 bis 800 je Arm, also innerhalb der Seed-Streuung (CLAUDE.md: 5,75 Punkte bei
n = 400); keine Monotonie in k (k = 1 am hoechsten, k = 2 und 3 gleich). Offline unterscheiden sich die Brier-Minima
um hoechstens 0,0003 (b02 am besten). Ein Verdikt "Bootstrap-Quelle traegt" ist damit NICHT belegt, nur "schadet
nicht"; belegbar waere es allein durch direkte Kanten Arm gegen b02 (Nutzer-Entscheid) oder durch die gepaarte
Offline-Messung nach der Kette (dort ist die Aufloesung hoch, aber der Brier zeigte bei b03 schon in die andere
Richtung als die Arena). Arm b06 gesamt rund 4,7 h.

## par.14 ARM v35-b04: WERTZIEL MIT MARGEN-BOOTSTRAP (NUTZER 2026-10-05 00:3x: *"takte das ebenfalls ein als b04"*; REGISTRIERT VOR Bau-Abnahme und Lauf)

**Anlass:** Nutzer-Vorschlag "Blend mit dem Point Head" (Diskussion 2026-10-04 spaet) und der Koordinator-Satz, ein Blend
des Ziels mit der Punkteprognose statt mit `root_q` sei nie gemessen worden. **Abweichung vom Zitat, benannt:** die
Records tragen KEINE Punkteprognose des Netzes (Felder geprueft 2026-10-05: `bootstrap_value`, `root_q`,
`root_child_q`, `scores`, `scores_unclamped`, `winner` ...); sie bräuchte Netz-Inferenz beim Cache-Bau. b04 nimmt
darum die REALISIERTE Endmarge: `bvp = sigmoid(final_margin / b)` mit `final_margin` = `scores_unclamped[p] -
scores_unclamped[1-p]` aus Sicht des Ziehers (`corpus_dataset.final_margin_of_step`, `:438`), b = 20 Punkte (die
Bezugsbreite des Projekts: Marge, die der Plattenblick allein zwischen sonst gleich starken Spielern erzeugt,
`PREREG_saturating_score_utility.md` par.14.5, Nutzer-Entscheid 2026-09-03). Ziel damit (HERLEITUNG): 0,35 Ausgang +
0,35 weiche Marge + 0,30 Suchwert jetzt; die weiche Marge traegt die HOEHE des Ergebnisses (knapp gegen klar), kein
Anteil aus dem rohen Netz, keine Trajektorie. Knopf `MOSAIC_BOOTSTRAP_SOURCE=margin` +
`MOSAIC_BOOTSTRAP_MARGIN_SCALE=20`, Marker `bootstrapmargin_b20_v1` in beiden Cache-Schluesseln (Bau beauftragt
00:3x, Abnahme wie par.13: Standardweg bitgleich, Mini-Test).

**Vorwissen, das dagegen spricht und vorab benannt ist:** die Marge als ALLEINIGES Wertziel (tanh-Aera bis 2026-08-05)
war ueberkonfident (Platt B 1,93) und die Arena zielinvariant (`archive/history.md` Z. 9185-9229); E2 (Margen-Schwellen
als Zusatzausgaenge) trug nicht (`PREREG_v34_window.md` par.10b, 395:405). Neu an b04 ist nur die Form (Blend mit dem
harten Ausgang und dem Suchwert statt Ersatz); Erwartungswert des Koordinators nahe null, Kosten 37 min Training.

**Arm:** `v35-b04` auf dem b02-Fenster wie par.13 (eigene Bloecke und Monolith, Seed 20260965, Warmstart
`v34-b01_brierbest`, Rezept byte-gleich b02 bis auf die zwei Knopf-Variablen), Reihenfolge nach b03, b05, b06 (par.13).
**Tore:** Stufenform wie par.13 (Seed 20261600, Seed 2 nur ueber der Schwelle). Zuordnung vorab: ein Gewinn gegen b02
gehoert der Zielform "weiche Marge im Bootstrap-Anteil". Berichtet: Val-Brier, Epochenkurve (Erosion), Platt-B des
gegateten Netzes gegen b02 (die tanh-Aera war hier der Vorfall).

### par.14a ERGEBNIS v35-b04 (Margen-Bootstrap, b = 20): TRAINING (2026-10-06 20:10-20:51, Arm-Kette); Tor 1 laeuft

**Training** `v35-b04` 1.691,1 s (`manifest_train_v35-b04_20261006_202256.json`, `mosaic_env` BOOTSTRAP_SOURCE=margin,
MARGIN_SCALE=20), Val-Brier auf den 120 b02-Val-Dateien: Epoche 1 0,19068, Minimum **0,19034 in Epoche 4**, Epoche 12
0,19052; `_brierbest` (Epoche 4) liegt getrennt vom `_best` (Epoche 2), gegatet wird `alphazero_v35-b04_brierbest.onnx`.
Das ist das SCHLECHTESTE Brier-Minimum der Reihe (b02 0,18942, b03/b06 0,18965, b05 0,18970; Abstand zu b02 0,0009,
groesser als die Spanne der Trajektorien-Arme) und der einzige Arm, dessen Brier in Epoche 1 ueber dem Warmstart-Niveau
der anderen Arme startet (0,19068 gegen 0,1897 bis 0,1901). Lesung vorab: die realisierte Endmarge als Bootstrap-Quelle
mischt ein Ziel ein, das vom Ausgang abhaengt und damit mehr Rauschen traegt als ein Suchwert; der Val-Brier rechnet
gegen den reinen Ausgang und sieht das. `policy_val_loss` wie in allen Armen (Minimum Epoche 2). Tor 1 Seed 20261600
seit 20:51.

**Tor 1 Seed 20261600: v35-b04 216:184 = 54,0 %** (n = 400, Deckel), Block-z **+1,65** (40 Bloecke, Mittel 0,540, sd
0,153), gepaarte Differenz +0,16 [-0,04; +0,36], SPRT `UNDECIDED_CAP_REACHED`, 17,55 s je Partie. Tor 2b: volle Spalten
je Brett 1,060 gegen 1,020, Punkte 58,48 gegen 55,51, Strafsteine 7,70 gegen 7,67, Plattenpunkte 8,48 gegen 7,67. Der
schwaechste erste Seed der Reihe (b02 +1,51 war aehnlich, b03 +5,28, b05 +2,53, b06 +3,05); Siegquote ueber 52,5 %,
darum laeuft Seed 20261601 (seit 22:52), Verdikt gepoolt.

### par.14b v35-b04: TOR 1 SEED 2, GEPOOLT, STUFENREGEL (2026-10-06 22:52 bis 2026-10-07 00:52)

**Seed 20261601: v35-b04 236:164 = 59,0 %** (n = 400, Deckel), Block-z **+3,08** (40 Bloecke, Mittel 0,590, sd 0,185),
gepaarte Differenz +0,36 [+0,17; +0,55], 7.197 s (17,99 s je Partie). Tor 2b: volle Spalten je Brett 1,115 gegen 0,988
(groesster Spaltenvorsprung der Reihe in einem Seed, +0,13), Punkte 58,80 gegen 54,91, Strafsteine 8,01 gegen 8,18,
Plattenpunkte 8,91 gegen 7,96 (Vertikale 8,46 gegen 7,25, Mehrfarbige 4,44 gegen 3,48).

**Gepoolt Seed 1 + 2: 452:348 = 56,5 %** (n = 800), **Block-z +3,41** (80 Bloecke, Mittel 0,565, sd 0,171). Genau EIN
Seed einzeln ueber +1,96 (Seed 1 +1,65, Seed 2 +3,08), darum Stufenregel: Seed 20261602 laeuft (seit 00:52), Verdikt
auf dem gepoolten z ueber drei Seeds. Die beiden Seeds liegen 5 Punkte auseinander (54,0 gegen 59,0 %), die groesste
Seed-Spreizung der Reihe; genau die Streuung, die CLAUDE.md fuer n = 400 nennt (5,75 Punkte).

Lesung vorab: faellt Seed 3 um 50 %, bleibt der gepoolte z bei rund +2,8 (HERLEITUNG wie par.12d) und b04 traegt gegen
v34-b01 trotz des schlechtesten Val-Briers der Reihe; die Zuordnung "Margen-Bootstrap traegt" ist damit NICHT belegt
(Fenster-Effekt, par.14a-Lesung, Nutzer 2026-10-06), und offline ist die Quelle messbar schlechter.

### par.14c VERDIKT v35-b04 (Margen-Bootstrap): SEED 3 UND GEPOOLT (2026-10-07 00:52-02:53)

**Seed 20261602: v35-b04 222:178 = 55,5 %** (n = 400, Deckel), Block-z **+2,05** (40 Bloecke, Mittel 0,555, sd 0,169),
gepaarte Differenz +0,22 [+0,03; +0,41], 7.107 s (17,77 s je Partie). Tor 2b: volle Spalten 1,093 gegen 0,995, Punkte
59,72 gegen 56,52, Strafsteine 7,63 gegen 7,58, Plattenpunkte 9,51 gegen 8,44.

**Gepoolt drei Seeds: 674:526 = 56,2 %** (n = 1.200, 600 Paare), **Block-z +3,98** (120 Bloecke, Mittel 0,562, sd
0,170). **VERDIKT TOR 1: v35-b04 TRAEGT** (Kriterium par.14 wie par.12; Stufenregel erfuellt, Seed 3 ueber der Linie).

| Seed | Ergebnis | Block-z | Spalten je Brett b04 / v34-b01 |
| --- | --- | --- | --- |
| 20261600 | 216:184 = 54,0 % | +1,65 | 1,060 / 1,020 |
| 20261601 | 236:164 = 59,0 % | +3,08 | 1,115 / 0,988 |
| 20261602 | 222:178 = 55,5 % | +2,05 | 1,093 / 0,995 |
| gepoolt | 674:526 = 56,2 % | **+3,98** | |

**Einordnung (par.14-Frage: traegt die Margen-Quelle etwas ueber b02 hinaus?):** NEIN, nicht belegbar. b04 liegt gepoolt
bei 56,2 % gegen b02 56,8 % ueber jeweils drei Seeds auf denselben Seeds (b02 par.12e), bei schlechterem Val-Brier
(0,19034 gegen 0,18942, par.14a) und derselben Kennzahlen-Richtung. Die Kante gegen v34-b01 ist der Fenster-Effekt
(Nutzer-Lesung 2026-10-06: "kann es sich auch nur um den 400 Sims effekt handeln"); die Margen-Quelle hat offline
messbar gekostet und in der Arena nichts Sichtbares gebracht. Lesart (c) von par.14: kein Hebel; b04 wird nicht weiter
verfolgt (keine direkte Kante gegen b02 noetig). Arm gesamt rund 6,7 h (drei Seeds).

## par.15 ARM v35-b07: LAMBDA 1,0 (KEIN root_q-ANTEIL IM WERTZIEL) AUF DEM b02-FENSTER (NUTZER 2026-10-05 00:5x: *"registrier das so"*; REGISTRIERT VOR dem Lauf)

**Anlass (an der Quelle verifiziert 2026-10-05):** `PREREG_lambda_wdl_arm.md` (ENTSCHEIDEN 2026-08-08) fand lambda 0,7
in der WDL-Aera als H0 (Ein-Faktor-Gating 63:77, p 0,21; Brier 0,18937 gegen 0,18749, schlechter) mit dem Satz
"lambda wird NICHT ins Rezept aufgenommen". Seit dem v24-b02-Rezept (`PREREG_v24_window.md` par.9: "b02-Rezept lambda
0,7") steht `--value-target-lambda 0.7` trotzdem im Rezept bis v35-b01; eine Neumessung in der WDL-Aera habe ich im
Index nicht gefunden (Muster "lambda" im PREREG_INDEX: nur die drei Lambda-Preregs von 2026-08). Dazu par.11d: der
`root_q`-Anteil ist in Runde 1 auch @400 nicht besser als das Netz.

**Arm:** `v35-b07` = b02-Fenster, b02-Rezept, einziger Unterschied `--value-target-lambda 1.0` (Ziel = 0,5 Bootstrap +
0,5 Ausgang, kein Suchwert jetzt). Kein neuer Cache-Schluessel (lambda mischt im Training, `apply_value_target_lambda`,
corpus_dataset.py:2164 ff.), also dieselben Bloecke und derselbe Monolith wie b02; Kosten 37 min Training. Seed
20260965, Warmstart `v34-b01_brierbest`, gegatet das Brier-beste Netz. **Tore:** Stufenform wie par.13 (Seed 20261600,
Seed 2 nur ueber der Schwelle). Zuordnung vorab: ein Unterschied zu b02 gehoert dem root_q-Anteil. Berichtet: Val-Brier
gegen b02, Epochenkurve, Platt-B. Reihenfolge: nach b03, b05, b06, b04.

### par.15a ERGEBNIS v35-b07 (lambda 1,0, kein root_q-Anteil): TRAINING (2026-10-07 02:46-03:09, Arm-Kette); Tor 1 laeuft

**Training** `v35-b07` 1.357,9 s (`manifest_train_v35-b07_20261007_024653.json`; derselbe Monolith wie b02
`.cache_8e8096768cf0.h5`, kein Blockbau, `value_target_lambda` 1.0, keine Bootstrap-Variablen). Val-Brier auf den 120
b02-Val-Dateien: Epoche 1 0,18966, Minimum **0,18946 in Epoche 2**, Epoche 12 0,19027; kein eigenes `_brierbest`,
gegatet `alphazero_v35-b07_best.onnx`. Gegen b02 (0,18942, Epoche 5) praktisch gleich (0,00004), also: der
root_q-Anteil von 30 % im Wertziel aendert den Val-Brier des Warmstart-Trainings nicht messbar; der `value_val_loss`
(0,5477 gegen 0,5458) ist wegen des anderen Ziels nicht vergleichbar. `policy_val_loss` wie ueberall (Minimum Epoche 2).
Tor 1 Seed 20261600 seit 03:09.

**Tor 1 Seed 20261600: v35-b07 216:184 = 54,0 %** (n = 400, Deckel), Block-z **+1,75** (40 Bloecke, Mittel 0,540, sd
0,145), gepaarte Differenz +0,16 [-0,03; +0,35], SPRT `UNDECIDED_CAP_REACHED`, 17,57 s je Partie. Tor 2b: volle
Spalten je Brett 1,095 gegen 1,058, Punkte 57,63 gegen 55,77, Strafsteine **8,70 gegen 7,77** (groesster
Strafstein-Aufschlag der Reihe, +0,93), Plattenpunkte 8,94 gegen 7,84 (Spezialfelder -8,86 gegen -10,56, Vertikale
7,93 gegen 8,01: einziger Arm ohne Vorsprung bei den Vertikalen). Siegquote ueber 52,5 %, Block-z unter 1,96: Seed
20261601 laeuft (seit 05:06), Verdikt gepoolt mit Stufenregel. Gleiche Zahl wie b04 Seed 1 (216:184) auf demselben Seed.

### par.15b VERDIKT v35-b07 (lambda 1,0): TOR 1 SEED 2 UND GEPOOLT (2026-10-07 05:06-07:07)

**Seed 20261601: v35-b07 202:198 = 50,5 %** (n = 400, Deckel), Block-z **+0,18** (40 Bloecke, Mittel 0,505, sd 0,174),
gepaarte Differenz +0,02 [-0,18; +0,22], 7.095 s (17,74 s je Partie); Verlauf: bis Paar 135 hinten (LLR -6,38 nahe der
unteren Schranke), danach aufgeholt. Tor 2b: volle Spalten 1,100 gegen 1,095 (gleich), Punkte 58,31 gegen 57,60,
Strafsteine 8,10 gegen 8,02, Plattenpunkte 8,57 gegen 8,74 (einziger Seed der Reihe mit WENIGER Plattenpunkten als der
Champion).

**Gepoolt: 418:382 = 52,25 %** (n = 800), **Block-z +1,26** (80 Bloecke, Mittel 0,5225, sd 0,160). Kein Seed einzeln
ueber +1,96, gepoolt unter 52,5 % und unter +1,96: **VERDIKT TOR 1: v35-b07 TRAEGT NICHT** (Kriterium par.15 wie par.12;
Stufenregel greift nicht). Erster Arm der Reihe ohne Kante gegen v34-b01.

**Lesung (par.15-Frage: braucht das Wertziel den root_q-Anteil?):** JA, nach dieser Messung. b07 unterscheidet sich von
b02 (56,8 %, drei Seeds; auf denselben zwei Seeds 54,6 %, z +2,50) NUR darin, dass der 30-%-Anteil des Suchwerts der
aktuellen Stellung aus dem Wertziel entfaellt (lambda 1,0 statt 0,7), bei identischem Monolithen, Val-Satz, Seed und
Rezept; offline war der Val-Brier gleich (0,18946 gegen 0,18942, par.15a). Ohne den Suchwert-Anteil faellt die Kante
gegen den Champion von z +2,50 auf +1,26 auf denselben Seeds. Das ist konsistent mit dem WDL-Aera-Befund (lambda 0,7 im
Rezept seit v24-b02, `PREREG_lambda_wdl_arm.md`) und sagt zugleich: der Brier auf dem Val-Satz sieht diesen Unterschied
nicht, die Arena schon. Vorsicht: 4 Punkte auf n = 800 liegen an der Grenze der Seed-Streuung; die Richtung passt aber
zu Rezept und Vorgeschichte, und b07 ist der einzige Arm mit einem Seed um 50 %. b07 wird nicht weiterverfolgt; lambda
0,7 bleibt. Arm gesamt rund 4,4 h.

## par.16 ARM v35-b08: GEWICHTSMITTELUNG DER CHECKPOINTS (EMA/SWA, Research E5) (NUTZER 2026-10-05 01:0x: *"die anderen 3 kandidaten kannst auch eintakten als eigene arme"*; REGISTRIERT VOR Bau und Lauf)

**Quelle:** `RESEARCH_evaluator_architecture_external_2026-09-25.md` E5 (Z. 469-490): statt des Brier-besten Einzel-
Checkpoints ein gemitteltes Netz ueber die Schnappschuesse (KataGo: EMA ueber vier Schnappschuesse, decay 0,75; SWA
Izmailov 2018); "der Gewinn ist in der Literatur klein und stetig". Stand im Baum (Agent 2026-10-05, Muster
EMA/SWA/Polyak/AveragedModel): ungebaut, in `PREREG_evaluator_pretests.md:7-8` ausdruecklich nicht aufgenommen.

**Bau (Trainingsseite, Datenschicht unberuehrt):** train.py-Knopf `--weight-average {ema,swa}` mit Parametern
(EMA-decay je Epoche, Default 0,75 nach KataGo; SWA ab Epoche k), `torch.optim.swa_utils` oder eigene EMA ueber die
Epochen-Schnappschuesse, BN-Statistik am Ende neu geschaetzt (`update_bn` auf dem Trainingsanteil); gespeichert als
eigener Stand `alphazero_<arm>_avg.pth/.onnx` NEBEN den Bestandsstaenden (Bestand byte-gleich ohne Knopf); Val-Brier
des gemittelten Stands wird je Epoche mitgeloggt (Manifest `epoch_history`), damit die Auswahlregel greift.

**Arm:** `v35-b08` = b02-Fenster, b02-Rezept plus `--weight-average ema` (decay 0,75 ueber die Epochen-Schnappschuesse
2-12), Seed 20260965. **Vorab-Test (vor Tor 1, kostenlos):** Brier des gemittelten Stands gegen den Brier-besten
Einzelstand desselben Laufs auf dem Val-Satz, gepaart ueber Dateien (`checkpoint_val_eval.py`): liegt das CI der
Differenz nicht ueber 0, KEIN Tor 1 (Research-Vorgabe "Kein Gewinn: kein Tor 1"). Sonst Tor 1 in Stufenform wie
par.13. Zuordnung vorab: ein Unterschied zu b02 gehoert der Mittelung. Kosten HERLEITUNG: Bau 1-2 h, Training 37 min
plus EMA-Overhead, Vorab-Test 1 min, Tor 1 Seed 1 rund 1,5 h.

**Rahmen (Nutzer 2026-10-05 01:1x: *"entweder ist dann was dabei, oder auch nicht. danach kann ich gut mit dem
projektabschluss leben."*):** b02 bis b08 und die drei Such-Preregs sind die abschliessende Reihe von v35; danach
Promotion, falls eine Kante faellt, sonst Abschluss mit v34-b01 als Tessa.

### par.16a ERGEBNIS v35-b08 (EMA decay 0,75 ab Epoche 2): TRAINING UND VORAB-TEST, KEIN TOR 1 (2026-10-07 07:05-07:38, Arm-Kette)

**Training** `v35-b08` 1.461,0 s (`manifest_train_v35-b08_20261007_070511.json`, `weight_average` ema / 0,75 / ab
Epoche 2, b02-Monolith, Seed 20260965). **Der Einzelstand-Pfad ist bitgleich b02:** die Val-Brier-Kurve der Epochen ist
Wert fuer Wert dieselbe wie bei b02 (0,18973 / 0,18943 / 0,18948 / 0,18943 / 0,18942 / ...; Minimum 0,18942 in Epoche 5),
also hat die Zusatz-Validierung unter `preserved_rng` den Trainingspfad nicht verschoben (Abnahme des Knopfs, par.16).

**Gemittelter Stand je Epoche** (`avg_value_val_brier`, BN-Statistik gemittelt, nicht neu geschaetzt):

| Epoche | Einzelstand Brier | EMA Brier | Einzelstand Policy-Val | EMA Policy-Val |
| --- | --- | --- | --- | --- |
| 2 | 0,18943 | 0,18943 | 0,4785 | 0,4785 |
| 3 | 0,18948 | 0,18940 | 0,4794 | 0,4778 |
| 4 | 0,18943 | 0,18934 | 0,4819 | 0,4778 |
| 5 | 0,18942 | **0,18930** | 0,4835 | 0,4781 |
| 8 | 0,18988 | 0,18945 | 0,4904 | 0,4820 |
| 12 | 0,18980 | 0,18966 | 0,4923 | 0,4880 |

Das Mittel liegt ab Epoche 3 in JEDER Epoche unter dem Einzelstand derselben Epoche, beim Brier um bis zu 0,0004
(Epoche 8) und beim Policy-Val um bis zu 0,0084; sein Minimum 0,18930 (Epoche 5) ist um 0,00012 besser als das beste
Einzel-Brier der ganzen Reihe. Gespeichert wurde aber per Bauform der ENDSTAND des Mittels nach Epoche 12 (11 Epochen
gemittelt, BN neu geschaetzt ueber 7.957 Batches): Brier 0,18967, Policy-Val 0,4882.

**Vorab-Test par.16** (`checkpoint_val_eval_v35-b08_avg_vs_brierbest.json`, Referenz `_brierbest` = Epoche 5, gepaart ueber
120 Val-Dateien): Brier Referenz minus `_avg` **-0,00025 [-0,00045; -0,00007]**, Policy-CE gepoolt -0,0119 [-0,0131;
-0,0107]; das CI liegt ganz UNTER 0, der gemittelte Endstand ist schlechter als der Brier-beste Einzelstand. Regel par.16:
**kein Tor 1**, Arm beendet (Kette: "Vorab-Test ohne Gewinn", 0,42 h).

**Lesung:** die Mittelung wirkt (sie glaettet die Erosion ab Epoche 5 sichtbar), aber die Bauform nimmt den falschen
Stand: der Endstand mittelt die ueberangepassten spaeten Epochen mit hinein. Der gemittelte Stand haette wie der
Einzelstand nach SEINEM eigenen Brier-Minimum ausgewaehlt werden muessen (Epoche 5, 0,18930). Folgearm, NICHT gebaut,
Nutzer-Entscheid: **b08b = EMA mit Auswahl des gemittelten Stands am eigenen Brier-Minimum** (speichern des Mittels je
Epoche oder Mitfuehren des besten Mittels; BN-Neuschaetzung dann fuer diesen Stand), Vorab-Test wie par.16 gegen
`_brierbest`; Erwartung aus der Tabelle: +0,00012 Brier, +0,005 Policy-Val, beides innerhalb der Val-Aufloesung
(CI-Breite rund 0,0004 bei gepaarter Messung) und damit ein Fall fuer den Schnellblick par.19.0 gegen b02, nicht fuer
eine volle Arena.

### par.13-16 ZUSAMMENFASSUNG DER NETZARME (Arm-Kette 2026-10-06 06:45 bis 2026-10-07 07:38, 24,9 h)

| Arm | Aenderung gegen b02 | Val-Brier-Minimum (Epoche) | Tor 1 gegen v34-b01, gepoolt | Block-z | Verdikt |
| --- | --- | --- | --- | --- | --- |
| b02 | Referenz: Fenster @400, Modus 2 | 0,18942 (5) | 596:454 = 56,8 % (3 Seeds) | +4,07 | traegt (par.12e) |
| b03 | Trajektorien-Bootstrap k = 1 | 0,18965 (5) | 381:269 = 58,6 % (Seed 1 SPRT-Stopp) | +5,12 | traegt (par.13b) |
| b05 | k = 2 | 0,18970 (2) | 451:349 = 56,4 % | +3,88 | traegt (par.13d) |
| b06 | k = 3 | 0,18965 (2) | 455:345 = 56,9 % | +3,83 | traegt (par.13f) |
| b04 | Margen-Bootstrap b = 20 | 0,19034 (4) | 674:526 = 56,2 % (3 Seeds) | +3,98 | traegt, kein Hebel (par.14c) |
| b07 | lambda 1,0 (kein root_q) | 0,18946 (2) | 418:382 = 52,25 % | +1,26 | traegt NICHT (par.15b) |
| b08 | EMA ueber Epochen | 0,18942 (5); EMA-Endstand 0,18967 | kein Tor 1 (Vorab-Test negativ) | - | kein Gewinn so gebaut (par.16a) |
| b10 | Schwarm als Policy-Traeger (1.200 statt 400), 0 h Erzeugung | 0,18877 (3) | 420:270 = 60,9 % (2 Seeds, beide SPRT-Stopp) | +6,22 | traegt, staerkste Kante (par.18b) |
| b09 | Policy-Volumen: +4.000 Partien @400 (rund 7 h Erzeugung) | 0,18880 (3) | 390:270 = 59,1 % (Seed 1 SPRT-Stopp) | +4,15 | traegt, Lesart (a) (par.17c) |

Laufzeiten je Arm (Kettenausgabe): b03 rund 4,0 h, b05 4,7 h, b06 4,7 h, b04 6,65 h (drei Seeds), b07 4,3 h, b08 0,42 h;
Bloecke plus Merge je Arm rund 20 min, Training 1.358 bis 1.691 s, Tor-1-Seed 7.100 bis 7.300 s (17,5 bis 18,2 s je
Partie, 10 Threads). Was die Reihe sagt: (1) der Fenster-Effekt @400 traegt in jedem Arm, der ihn hat; (2) die
Bootstrap-Quelle (Trajektorie, Marge) legt nichts Belegbares darauf, Trajektorie schadet nicht, Marge kostet Brier;
(3) der Suchwert-Anteil im Wertziel traegt (b07); (4) die Mittelung der Epochen ist offline sichtbar, aber in der
gebauten Form nicht nutzbar. Keine direkte Kante zwischen den tragenden Armen gefahren (Nutzer-Entscheid offen; Vorschlag
Schnellblick par.19.0 gegen b02 als Vorsortierung).

## par.17 ARM v35-b09: POLICY-VOLUMEN (4.000 POLICY-PARTIEN @400 MEHR AUF DEM b02-FENSTER) (NUTZER 2026-10-05 09:xx: *"registrier den policy-volumen-arm als b09"*; REGISTRIERT VOR Bau und Lauf)

**Anlass (Koordinator, am Trainingsverlauf abgelesen, Manifeste `manifest_train_v34-b01_*_183258.json` und
`manifest_train_v35-b01_*_200022.json`, Feld `epoch_history`):** der Policy-Kopf ist auf dem Fenster
stichprobenbegrenzt, der Wertkopf nicht.

| Kopf | v34-b01 (1.380 Dateien, 580 Traeger) | v35-b01 (1.200 Dateien, 400 Traeger) |
| --- | --- | --- |
| `policy_val_loss` Epoche 1 bis 12 | 0,358 auf 0,372, steigt ab Epoche 1 | 0,429 auf 0,446, steigt ab Epoche 2 |
| `policy_loss` (Training) | 0,950 auf 0,773 | 1,075 auf 0,844 |
| `value_val_brier` | 0,1853 bis 0,1855, flach | 0,1946 (Epoche 2) bis 0,1951, flach |
| `value_loss` (Training) | 0,549 auf 0,537 | 0,538 auf 0,525 |

Der Policy-Val-Verlust steigt in beiden Generationen monoton, waehrend der Trainingsverlust faellt: Ueberanpassung,
der Kopf hat mehr Kapazitaet, als die Traegerdateien fuellen. v35 traegt dabei 400 Policy-Traeger statt 580 in
v34 (`data/policy_carrier_manifest_v34.json`: 400 eigene + 135 G-1 + 45 G-2; die Alt-Traeger sind mit dem
Nutzer-Entscheid "ohne Alt-Generationen" weggefallen, par.11). Die einzige Messung, in der Volumen je getragen hat
(`PREREG_corpus_dose.md`: 900 gegen 450 Dateien, Orakel 6/6, Arena 479:321), war ein Policy-Effekt (beide
Orakel-Metriken sind Policy-Masse). Der Nullbefund "Volumen seit v33 kein Hebel" (`PREREG_v33_window.md` par.6b/6d)
betrifft SCHWARM-Partien, also die Wertseite; Policy-Volumen ist seit v20 nicht isoliert gemessen. Der Wertkopf
dagegen steht in jeder Epoche beider Generationen auf seinem Endwert (par.11b: dBrier Warmstart minus Epoche 2
+0,0006, CI mit 0); fuer ihn ist das Fenster gross genug, sein Problem ist der Inhalt des Ziels (par.11d, par.12).

**Frage:** Traegt ein Fenster mit doppelt so vielen Policy-Traegern (800 statt 400 Dateien @400) ein Netz, das
v34-b01 schlaegt, bei sonst unveraendertem b02-Rezept?

**Arm:** `v35-b09` = b02-Fenster (1.200 Dateien, par.12) plus 4.000 neue Partien der Sockel-Klasse @400, Modus 2,
als EIGENE Klasse `policy-s400-vol` (Dateien `selfplay_v34-b01-policy-s400-vol_*`, 400 Dateien a 10 Partien).
Einstellung byte-gleich Klasse `policy-s400` aus `models/v35_b02.recipe.json` (Weg C, `deviate_prob` 1,0,
`tau_tiebreak_q` 2, Spec `models/v35_generation.spec.json`, 400 Sims), nur Seed-Basis 20263500 (400 Chunks, also
20263500 bis 20263899; frei: b02 belegt 20262100+399, 20262600+399, 20263100+99, 20263300+199, v35-b01
20260950-20260955 je +199). Eigene Rezeptdatei `models/v35_b09.recipe.json` (die laufende b02-Kette liest
`v35_b02.recipe.json` je Klasse neu, die Datei wird NICHT angefasst). Fenster `data/window_v35_b09.txt` = 1.600
Dateien; Traeger-Manifest `data/policy_carrier_manifest_v35_b09.json` = die 400 Traeger von b02 plus alle 400
neuen = 800 (Kette bricht ab, wenn es nicht 800 = 100 + 100 + 200 + 400 sind). Training byte-gleich b02 (Warmstart
`v34-b01_brierbest`, Seed 20260965, 12 Epochen, lambda 0,7, Wertmaske, `--select-by-brier`), Manifest-Diff gegen
das b02-Manifest: erlaubt nur `name`, `cache_file`, `file_list`, `val_frac`, `val_pool`.

**Val-Satz = byte-gleich b02 (Vorbedingung fuer jede Offline-Zahl).** train.py zieht den Val-Split als feste
Mischung (`random.Random(20260707)`, train.py:1643) aus den Treffern des Pool-Regex und nimmt die ersten
`round(len(all_files) * val_frac)` (train.py:1634). b09 setzt darum `MOSAIC_VAL_POOL` auf die fuenf b02-Klassen
(`^selfplay_v34-b01-(policy|policy-s400|policy-dice-v2-r1-s400|value-deviate-s400|value-excursion-s400)_`, die
neue Klasse trifft nicht) und `val_frac` = 120/1.600 = 0,075: Pool und Reihenfolge sind die von b02, n_val = 120,
also dieselben 120 Dateien; die 400 neuen gehen garantiert ins Training. Die Kette prueft `_val.txt` gegen
`window_v35_b02_val.txt` ohne Kommentarzeilen (Abweichung = STOPP). `MOSAIC_DATA_EXCLUDE` der laufenden und der
folgenden Ketten bekommt `^selfplay_v34-b01-policy-s400-vol_` dazu, sobald die Klasse existiert (Fenster-Pinning;
die Dateiliste ist die erste Sicherung).

**Messung:** (1) Tor 1 wie die Reihe: gepaartes Gating `v35-b09` gegen `v34-b01` @400, Spec `v34-b01_brierbest`
beidseits, Seeds 20261600/20261601 a 200 Paare, Blockgroesse 5, `--log-games`, Kriterium Block-z >= +1,96 oder
gepoolt >= 52,5 % ohne Gegenbefund, Stufenregel 20261602 (par.11, `PREREG_v34_window.md` par.2). (2) Offline,
vorab, auf dem byte-gleichen Val-Satz: `tools/checkpoint_val_eval.py --checkpoints <b02_brierbest> <b09_brierbest>
--train-manifest <b09-Manifest>`, gepaart ueber Dateien mit Block-Bootstrap: Policy-CE-Differenz (b02 minus b09)
und Brier-Differenz; dazu aus den Manifesten die Epoche des Minimums von `policy_val_loss` und sein Wert.
Standard-Kennzahlen (CLAUDE.md) aus den Gating-Artefakten wie bei b02.

**Erwartung, vorab festgelegt:** ist der Policy-Kopf stichprobenbegrenzt, liegt das Minimum von `policy_val_loss`
bei b09 unter dem von b02 (CI der gepaarten CE-Differenz ganz ueber 0) und tritt spaeter ein; der Val-Brier bleibt
innerhalb 0,001 von b02 (der Wertkopf ist nicht stichprobenbegrenzt). Lesart: (a) CE-Gewinn UND Tor 1 faellt:
Volumen traegt, Zuordnung an die 400 Traegerdateien (einziger Unterschied zu b02 bei gleichem Val-Satz);
Promotion nach der Ein-Promotion-Regel je Generation. (b) CE-Gewinn, Tor 1 faellt nicht: "Korpus wirkt, Gewicht
nicht" (Muster v22); Policy-Volumen damit abgeschlossen. (c) kein CE-Gewinn: der Kopf ist nicht
stichprobenbegrenzt, das steigende `policy_val_loss` ist Rauschen-Anpassung ohne Signal; abgeschlossen. Konfundiert
bleibt die Batch-Mischung (50 statt 33 % Traeger je Epoche); das gehoert zum Arm "mehr Policy-Partien" und wird
nicht getrennt. Seed-Varianz (4- bis 6-mal so gross wie Knopfeffekte) bleibt die Grenze jeder Einzelarena; die Kante
b09 gegen b02 direkt laeuft nur, wenn beide Tor 1 nahe der Schwelle liegen (Nutzer-Entscheid dann).

**Nicht Teil von b09, offen:** die nicht erzwungenen Zuege des Schwarms als Policy-Traeger freizugeben (0 h
Erzeugung); ungeprueft, ob die Schwarm-Records dafuer Besuchsverteilungen tragen (par.9b: Startslot-Records ohne
Policy-Ziel).

**Kosten (HERLEITUNG aus `docs/measured_runtimes.md`):** Erzeugung 4.000 x 6,92 s = 27.680 s, rund 7,7 h
exklusiv (Threads 11; ohne Cache-Waechter 6,21 s, rund 6,9 h); Bloecke 400 x 0,79 s rund 5 min; Merge rund 3 min;
Training rund 2.930 s (b01 2.198 s bei 2,03 M Zustaenden, b09 rund 2,7 M); Tor 1 Seed 1 rund 1,5 h. Zusammen rund
10,5 h mit einem Seed. **Reihenfolge:** die Erzeugung ist CPU-Last und kann neben keiner Arena laufen; nach der Arm-Kette
b03 bis b08 in `tools/night_v35_b09_b10_chain.sh`, dort HINTER b10 (Nutzer 2026-10-06 06:5x: *"tausch b09 mit
b10"*; Grund par.18: b10 beantwortet Lesart (c) ohne Erzeugung, ein Nullbefund dort macht b09 entbehrlich).

### par.17a ERGEBNIS v35-b09 (Policy-Volumen): ERZEUGUNG, TRAINING UND OFFLINE (2026-10-07 11:25 bis 2026-10-08 00:46, `tools/night_v35_b09_b10_chain.sh`); Tor 1 laeuft

**Erzeugung** `v34-b01-policy-s400-vol`, 4.000 Partien @400 Modus 2, Seed 20263500, ohne Cache-Waechter: Hauptlauf 11:25 bis
17:32:41 vom Rechner-Neustart bei 389 von 400 Dateien gekillt (Manifest `..._112529.json` ohne `laufzeit`; nach Dateistempeln
21.968 s = 5,65 s je Partie, HERLEITUNG), Rest 110 Partien per Chunk-Seed `--games 110 --seed 20263889` (Basis + 389 fertige
Chunks, `self_play.py:1315`) 23:33 bis 23:50, 1.016,6 s = 9,24 s je Partie (Manifest `..._233354.json`). Genau 400 Dateien.
Kette danach im Wiederaufnahme-Modus `RESUME=1` (ab 23:54): Bloecke fuer die 400 neuen Dateien 294 s, Traeger-Manifest 800 =
100 policy + 100 policy-s400 + 200 dice-v2 + 400 vol, Split val_frac 0,075 ueber den Pool der fuenf b02-Klassen, **Val-Liste
byte-gleich b02** (120 Dateien), Trainingsanteil 1.480 = 1.080 b02 + 400 neue, Monolith `1e0bdfe0d133` (725 von 1.480 Bloecken
policy-maskiert), Merge rund 7 min.

**Training** `v35-b09` 2.355,4 s (`manifest_train_v35-b09_20261008_000652.json`, 2.832.807 Samples gegen 2.037.090 bei b02,
+39 %; ab 00:30 lief eine claude_play-Partie daneben, Nutzer-Entscheid), Manifest-Diff gegen b02 ohne unerwartete Abweichung
(erlaubt: cache_file, file_list, name, val_frac, val_pool, Traeger-Manifest). Epochenkurve auf denselben 120 Val-Dateien:

| Epoche | b09 Val-Brier | b02 Val-Brier | b09 Policy-Val | b02 Policy-Val |
| --- | --- | --- | --- | --- |
| 1 | 0,18913 | 0,18973 | 0,4758 | 0,4798 |
| 2 | 0,18928 | 0,18943 | 0,4739 | 0,4785 |
| 3 | **0,18880** | 0,18948 | **0,4737** | 0,4794 |
| 5 | 0,18909 | **0,18942** | 0,4751 | 0,4835 |
| 8 | 0,18941 | 0,18988 | 0,4782 | 0,4904 |
| 12 | 0,18958 | 0,18980 | 0,4800 | 0,4923 |

Auswahl `_best` = `_brierbest` = Epoche 3. Der Policy-Kopf ueberpasst spaeter und flacher als bei b02 (Minimum Epoche 3 statt 2,
Anstieg bis Epoche 12 +0,006 statt +0,014), der Wertkopf liegt in JEDER Epoche unter b02.

**Offline gegen b02 (par.17 Punkt 2)** (`checkpoint_val_eval_v35-b09_vs_b02.json`, Referenz `v35-b02_brierbest` minus
`v35-b09_best`, gepaart ueber 120 Val-Dateien, Selbstpruefung PASS, 27,4 s):

| Groesse | Referenz minus b09 [CI95] | Lesung | zum Vergleich b10 (par.18a) |
| --- | --- | --- | --- |
| Val-Brier | **+0,00063 [+0,00008; +0,00115]** | b09 besser, CI ueber 0 (knapp) | +0,00066 [+0,00030; +0,00104] |
| Policy-CE gepoolt | **+0,0249 [+0,0224; +0,0274]** | b09 besser, CI ganz ueber 0 | +0,0301 [+0,0278; +0,0326] |

**Lesung vorab (ohne Verdikt):** die These von par.17 (Policy-Kopf stichprobenbegrenzt) bestaetigt sich offline ein zweites
Mal, mit 4.000 neuen Partien etwa so stark wie bei b10 mit 800 zusaetzlichen Traegern aus dem Schwarm, bei rund 7 h
Erzeugung gegen 0 h. Der Wertkopf gewinnt mit, obwohl die neuen Partien reine Policy-Partien sind (mehr Zustaende, 2,83 M
statt 2,04 M Samples). Was die Staerke daraus macht, sagt Tor 1 (Seed 20261600 seit 00:46:41, Seed 20261601 danach; beide
Seeds laufen mit claude_play-Partien g11/g12 daneben, Nutzer-Entscheid 2026-10-08, Laufzeiten entsprechend markiert).

### par.17b ERGEBNIS v35-b09 (Policy-Volumen): TOR 1 SEED 1 (2026-10-08 00:46-02:15; Nebenlast: claude_play g11/g12 bis 02:00, Nutzer-Entscheid)

**Seed 20261600: v35-b09 164:96 = 63,1 %** nach 130 Paaren (n = 260 Partien), SPRT **ACCEPT_H1** (LLR +7,22 ueber +6,91,
Stopp vor dem Deckel), Block-z **+4,18** (26 Bloecke, Mittel 0,631, sd 0,159), gepaarte Differenz +0,52 [+0,29; +0,76],
McNemar p = 0,00006, informative Paare A-Sweep 52 / B-Sweep 18 / Split 60. Laufzeit 5.301,2 s = 20,39 s je Partie bei 10
Threads, GEBREMST (claude_play-Partien bis 02:00 daneben; Vorlaeufe 17,3 bis 18,0 s). Artefakt
`gating_v35-b09_vs_v34-b01_s20261600.json`; der Zwischenstand `.partial.json` wurde nach jedem Block geschrieben und nach dem
Artefakt geloescht (erster Echtbetrieb des Mechanismus, Fortsetzung nicht gebraucht). Stufe genommen, Seed 20261601 laeuft
seit 02:15:05.

Die sechs Kennzahlen (Grundmenge Bretter je Modell, n = 260 je Seite; `arena_column_probe`, `plate_points_from_arena`):

| Kennzahl je Brett | v35-b09 | v34-b01 | gepaart b09 minus b01 [KI95] |
| --- | --- | --- | --- |
| Volle Spalten | 1,069 +- 0,088 | 0,992 +- 0,091 | - |
| Spalten >= 4 / lange Reihen | 2,47 / 3,23 | 2,26 / 3,15 | - |
| Zeilenfuellung H | 0,606 | 0,594 | - |
| Strafsteine | 8,21 | 7,93 | Boden +0,28 [-0,68; +1,25] |
| Eigene Punkte | 59,39 | 55,40 | +3,99 [+1,93; +6,04] |
| Margin | +3,98 | -3,98 | +7,97 [+3,86; +12,08] |
| Plattenpunkte gesamt | 8,95 | 7,65 | +1,30 [+0,40; +2,21] |
| davon Vertikale Reihen (106 Bretter) | 8,65 | 7,33 | +1,32 [-0,02; +2,66] |
| davon Mehrfarbige Felder (112) | 4,82 | 3,52 | +1,30 [+0,21; +2,40] |
| davon Spezialfelder (98) | -9,89 | -9,80 | -0,09 [-1,15; +0,97] |

Platzierungspunkte gepaart +3,77 [+2,30; +5,23]: der Gewinn kommt wie bei b02/b03/b10 zuerst aus der Grundwertung und den
Spalten, die Spezialfelder bleiben bei beiden Netzen bei rund drei leeren je Brett (vgl. claude_play g11/g12 gegen b10,
`PREREG_claude_play_interface.md` par.14a).

**Einordnung auf demselben Seed (deskriptiv, gleicher Gegner, gleiche Spec):** b02 218:182 ueber 200 Paare (54,5 %), b03 159:91
nach 125 Paaren (63,6 %), b10 185:115 nach 150 Paaren (61,7 %), b09 164:96 nach 130 Paaren (63,1 %). Verdikt wie bei allen Armen
erst gepoolt ueber beide Seeds (par.17c), Kriterium par.12.

### par.17c VERDIKT v35-b09 (Policy-Volumen): TOR 1 SEED 2 UND GEPOOLT, LESART (a) (2026-10-08 02:15-04:15, exklusiv)

**Seed 20261601: v35-b09 226:174 = 56,5 %** (n = 400, 200 Paare, Deckel), Block-z **+2,21** (40 Bloecke, Mittel 0,565, sd 0,186),
gepaarte Differenz +0,26 [+0,06; +0,46], McNemar p = 0,015, A-Sweep 66 / B-Sweep 40 / Split 94, SPRT `UNDECIDED_CAP_REACHED`
(LLR +3,05). Laufzeit 7.238,3 s = 18,10 s je Partie, 10 Threads, exklusiv (claude_play war seit 02:00 fertig).

**Gepoolt: 390:270 = 59,1 %** (n = 660 Partien, 330 Paare), **Block-z +4,15** (66 Bloecke, Mittel 0,591, sd 0,178). Beide Seeds einzeln
ueber +1,96 (Kette: "Seeds einzeln >= +1,96: 2 von 2"), die Stufenregel greift nicht.

**VERDIKT TOR 1: v35-b09 TRAEGT.** Lesart nach par.17, vorab festgelegt: **(a) CE-Gewinn UND Tor 1 faellt**, also "Volumen traegt",
Zuordnung an die 400 neuen Traegerdateien (einziger Unterschied zu b02 bei gleichem Val-Satz, gleichem Rezept, gleichem Seed,
gleicher Spec). Die Erwartung zum Policy-Kopf trifft zu (CE gepoolt +0,0249 [+0,0224; +0,0274], Minimum spaeter: Epoche 3 statt 2).
Die Erwartung zum Wertkopf ("innerhalb 0,001 von b02, nicht stichprobenbegrenzt") trifft nur zur Haelfte: der Brier liegt zwar
innerhalb 0,001, aber mit CI ueber 0 BESSER (+0,00063 [+0,00008; +0,00115]); 4.000 reine Policy-Partien haben also auch dem
Wertkopf Zustaende gebracht, die ihm fehlten (2,83 M statt 2,04 M Samples). Dasselbe Muster wie bei b10 (par.18a).
Promotion NUR nach Nutzer-Entscheid (Ein-Promotion-Regel), hier nichts entschieden.

Die sechs Kennzahlen Seed 2 (Grundmenge Bretter je Modell, n = 400 je Seite):

| Kennzahl je Brett | v35-b09 | v34-b01 | gepaart b09 minus b01 [KI95] |
| --- | --- | --- | --- |
| Volle Spalten | 1,085 +- 0,071 | 1,070 +- 0,071 | - |
| Spalten >= 4 / lange Reihen | 2,44 / 3,27 | 2,31 / 3,15 | - |
| Zeilenfuellung H | 0,597 | 0,600 | - |
| Strafsteine | 7,38 | 7,61 | Boden -0,23 [-0,98; +0,53] |
| Eigene Punkte | 60,17 | 57,59 | +2,58 [+0,85; +4,31] |
| Margin | +2,58 | -2,58 | +5,16 [+1,70; +8,61] |
| Plattenpunkte gesamt | 9,23 | 8,24 | +1,00 [+0,28; +1,71] |
| davon Eckplatten (132 Bretter) | 10,18 | 9,11 | +1,07 [+0,40; +1,74] |
| davon Horizontale Reihen (130) | 0,37 | 0,07 | +0,30 [+0,12; +0,49] |
| davon Spezialfelder (136) | -9,31 | -9,73 | +0,42 [-0,30; +1,13] |

Auf Seed 2 ist der Spalteneffekt klein (1,085 gegen 1,070; auf Seed 1 1,069 gegen 0,992), der Gewinn kommt aus Grundwertung
(Platzierung +2,05 [+0,71; +3,38]) und Platten; welches Kriterium traegt, wechselt zwischen den Seeds (Seed 1 Mehrfarbige Felder
und Vertikale, Seed 2 Eckplatten und Horizontale), das ist Seed-Streuung bei 47 bis 85 Paaren je Kriterium, kein Befund.

**Einordnung in die Reihe (deskriptiv, gleiche Seeds, gleicher Gegner):** b09 59,1 % / z +4,15 liegt zwischen b02 (54,6 % auf
denselben zwei Seeds) und b10 (60,9 % / z +6,22); b10 erreicht das ohne Erzeugung (0 h) aus 800 zusaetzlichen Schwarm-Traegern,
b09 mit 4.000 neuen Partien (rund 7 h Erzeugung @400). Beide bestaetigen dieselbe These (Policy-Kopf stichprobenbegrenzt), b10 ist
der billigere Hebel; ob b09 und b10 sich addieren (b16 = b10 + b09-Partien, Nutzer: "warten wir mal bis wir durch sind mit allen
aesten"), ist offen. Direkte Kante b09 gegen b02 oder b10 nicht vorregistriert (Nutzer-Entscheid).

**Laufzeiten (Kettenausgabe und Artefakte):** Bloecke 400 neue 295 s, Merge 418 s, Training 2.360 s (GEBREMST, claude_play
daneben), Offline 29 s, Tor 1 5.301 s (Seed 1, GEBREMST, 20,4 s je Partie) + 7.238 s (Seed 2, exklusiv, 18,1 s je Partie);
Arm ohne Erzeugung 15.658 s = 4,35 h; mit Erzeugung (rund 6,4 h Haupt- plus Rest-Lauf) rund 10,8 h.

**Nachlauf, offen:** `MOSAIC_DATA_EXCLUDE` folgender Ketten um `^selfplay_v34-b01-policy-s400-vol_` ergaenzen, sobald eine Kette
wieder ueber den Pool statt ueber eine feste Fensterliste baut (die v35-Ketten lesen feste Listen `window_v35_*.txt`; dort ist
die Klasse nur drin, wo sie hingehoert). Eintrag in STATUS Abschnitt 1.

## par.18 ARM v35-b10: SCHWARM ALS POLICY-TRAEGER (1.200 STATT 400 TRAEGER, KEINE NEUE ERZEUGUNG) (NUTZER 2026-10-05 09:xx: *"koennen wir noch immer machen nach b09. dann sind wir flexibel. registrier das als b10"*; REGISTRIERT VOR Bau und Lauf)

**Was die Schwarm-Records tragen (geprueft 2026-10-05 an `selfplay_v34-b01-value-deviate-s400_*_g10.pkl`, 2.000 Records,
und einer `value-excursion`-Datei der v35-b01-Erzeugung, 1.780 Records):** jeder Record traegt `policy` (Liste, bei
Drafting-Zuegen die Besuchsverteilung der Suche), `root_q` auf Suchzuegen, `bootstrap_value`, `scores`, `winner`. Die
Marke `policy_target_valid` steht auf false bei 1.408 von 2.000 (deviate) bzw. 1.323 von 1.780 (excursion) Records,
true bei 112 bzw. 97 (gesuchte Startsetzungen, `start_by_search`), sonst fehlt sie (Ein-Aktion-Zuege, Tiling). Die
Quelle des false ist NICHT der Ausflug oder die Abweichung, sondern der Value-only-Modus: `--value-only` setzt
`pcr_full_prob` 0,0 und `pcr_cheap_sims` = `--sims` (self_play.py:1836-1839), damit laeuft jeder
Mehrfach-Aktions-Zug ueber den PCR-Billigpfad und bekommt die Marke (self_play.rs, PCR-Vertrag). Der Billigpfad
unterscheidet sich von der Vollsuche NUR in der Sims-Zahl (`self_play.rs:5591-5594`: `Some(false) =>
self.pcr_cheap_sims`), und die ist im Schwarm @400 gleich der Vollsuche (Rezept `value-deviate-s400` /
`value-excursion-s400`: `value_only` true, Sims 400 aus `common`). Die Policy-Ziele des Schwarms sind damit
Suchziele mit demselben Budget wie im Sockel; die Marke ist im @400-Schwarm ein Etikett ohne Qualitaetsunterschied.
Die Ausflug-Records tragen kein eigenes Feld (nur `branch_kl` bei KL-Abzweig, 5 von 1.780); ein Ausflug ist eine
eigene Partie (`[excursion] game_id=ex_...`), deren Zuege nach dem Abzweig die normale Suche spielt. Ausnahmen
bleiben maskiert ueber eigene Bedingungen, unabhaengig von der Marke: gestreute Startsetzungen (`start_slot_randomized`,
par.9b, Gewicht 0 als Start-Record), gestreute Rueckgabe-Reihenfolge (`return_order_randomized`), Tiling.

**Wie der Schwarm heute aus dem Policy-Ziel faellt:** die Trainingsketten fahren `MOSAIC_IGNORE_POLICY_TARGET_VALID=1`
(Manifest v35-b01: `ignore_policy_target_valid` true), die Marke ist also ohnehin wirkungslos; gesperrt ist der Schwarm
allein ueber das Traeger-Manifest (`_is_policy_carrier`, `corpus_dataset.py:128-159`; Maske beim Zusammenfuegen,
`build_cache_incremental.py:329`). Im Sockel (Klasse `policy-s400`, ebenfalls `deviate_prob` 1,0) zaehlt der
abgewichene Zug bereits als Policy-Ziel; b10 dehnt genau diese Behandlung auf die 800 Schwarm-Dateien aus.

**Praezedenz:** `PREREG_v22_window.md` par.4 (Traegerfrage, Flagge ignorieren: Arm B besser, keine Kennzahl einzeln
signifikant, n = 40 auf einem Viertelkorpus; der volle A/B ist nie gefahren) und `PREREG_pcr.md` (Billigsuche mit 150
Sims bei p = 0,25: negativ) -- beides nicht dieselbe Frage, denn hier ist die "Billigsuche" eine 400-Sim-Suche.
Das v20-Zwei-Klassen-Design (Schwarm = reines Wertmaterial) stammt aus der Zeit, in der der Schwarm wirklich billiger
suchte; mit @400 in allen Klassen (par.12) ist diese Grundlage weg.

**Frage:** Traegt das b02-Fenster mit allen 1.200 Dateien als Policy-Traeger (statt 400) ein Netz, das v34-b01
schlaegt, bei sonst unveraendertem b02-Rezept?

**Arm:** `v35-b10` = b02-Fenster (dieselben 1.200 Dateien, `data/window_v35_b02.txt`), Traeger-Manifest
`data/policy_carrier_manifest_v35_b10.json` = ALLE 1.200 Dateien des Fensters (`tools/generate_carrier_manifest.py
--from-list data/window_v35_b02.txt --n-files 1200`; Kette bricht ab, wenn das Manifest nicht genau die 1.200
Fenster-Dateien traegt). Keine neue Erzeugung, keine Code-Aenderung, keine neuen Bloecke (Bloecke sind
traegeragnostisch): nur ein neuer Merge, denn die Traegermenge steht im Fenster-Schluessel (`corpus_dataset.py:539`),
der Monolith heisst also anders als der von b02. Val-Satz: dieselbe Liste, derselbe Pool-Regex `^selfplay_v34-b01-`,
dasselbe `val_frac` wie b02, daher byte-gleich die 120 b02-Val-Dateien (Kette diffed `_val.txt` gegen b02; Abweichung
= STOPP). Training byte-gleich b02 (Warmstart `v34-b01_brierbest`, Seed 20260965, 12 Epochen, lambda 0,7, Wertmaske,
`--select-by-brier`); Manifest-Diff gegen b02: erlaubt nur `name`, `cache_file`, und in `mosaic_env`
`MOSAIC_CARRIER_MANIFEST` = v35_b10. Val-Policy-Verlust und Val-Brier bleiben vergleichbar: der Val-Brier rechnet
gegen `wdl_outcome` (train.py:1046-1051), der Policy-Val-Verlust ueber dieselben Val-Dateien, nun aber mit
Policy-Gewicht auf 120 statt 45 davon (b02: 400 Traeger, davon 45 im Val-Anteil, par.11a) -- diese Zahl ist also
NICHT direkt mit b02 vergleichbar; vergleichbar ist `checkpoint_val_eval.py` auf der b02-Traegermaske (Werkzeug mit
`--train-manifest` des b02-Laufs, beide Checkpoints auf denselben 45 Traeger-Val-Dateien).

**Messung:** (1) Tor 1 wie die Reihe (par.17 Punkt 1: gepaart gegen v34-b01 @400, Seeds 20261600/01, Block-z >= +1,96
oder gepoolt >= 52,5 % ohne Gegenbefund, Stufenregel). (2) Offline vorab: `tools/checkpoint_val_eval.py --checkpoints
<b02_brierbest> <b10_brierbest> --train-manifest <b02-Manifest>` (Traegermaske von b02, damit die Policy-CE auf
derselben Menge rechnet), gepaart ueber Dateien mit Block-Bootstrap: Policy-CE-Differenz und Brier-Differenz; dazu
die Epoche des Minimums von `policy_val_loss` aus dem b10-Manifest (nur Richtung, Niveau nicht vergleichbar).

**Erwartung, vorab festgelegt (wie par.17):** stichprobenbegrenzter Policy-Kopf -> Policy-CE-Gewinn gegen b02 auf der
b02-Maske mit CI ueber 0, Val-Brier innerhalb 0,001. Lesarten (a)/(b)/(c) wie par.17. Spezifisches Risiko von b10,
vorab benannt: Schwarm-Partien enthalten je Partie eine erzwungene Abweichung ODER einen Ausflug (Weg C,
Ausflug-Abzweig), ihre Stellungen liegen also weiter abseits der Championlinie als der Sockel; ein Policy-Ziel auf
solchen Stellungen ist ein Suchziel, aber auf einer Verteilung, die das Netz im Spiel seltener sieht. Zeigt b10 einen
CE-Gewinn ohne Tor-1-Kante und b09 (frische Sockel-Partien) beides, ist DAS der Unterschied; zeigen beide dasselbe, ist
die Herkunft der Traeger gleichgueltig und b10 der billigere Weg. Konfundiert gegenueber b02: Traeger-Anteil je Epoche
100 statt 33 %; gehoert zum Arm.

**Kosten (HERLEITUNG, `docs/measured_runtimes.md`):** Manifest Sekunden, Merge rund 3 min (165 s bei b01), Training
rund 37 min (2.198 s bei b01, gleiche Zustandszahl wie b02), Tor 1 Seed 1 rund 1,5 h; zusammen rund 2,2 h mit einem
Seed, 3,7 h mit zweitem. **Reihenfolge (Nutzer: "nach b09"):** b10 braucht keine Erzeugung und kann als Arm in die
Arm-Kette (Bauform wie b07: kein Blockbau, eigener Merge unter eigenem Schluessel); zunaechst hinter b09 registriert, am
2026-10-06 06:5x vom Nutzer VORGEZOGEN (*"tausch b09 mit b10"*), weil es die Antwort auf par.17 (c) ohne 7,7 h Erzeugung vorwegnimmt: faellt bei b10 kein
CE-Gewinn an, ist der Policy-Kopf nicht stichprobenbegrenzt und b09 entbehrlich.

### par.18a ERGEBNIS v35-b10 (Schwarm als Policy-Traeger): TRAINING UND OFFLINE (2026-10-07 07:38-08:11, `tools/night_v35_b09_b10_chain.sh`); Tor 1 laeuft

**Bau:** Traeger-Manifest `policy_carrier_manifest_v35_b10.json` mit allen 1.200 Fenster-Dateien, Split byte-gleich b02
(Kette diffte Val- UND Train-Liste), Merge unter neuem Schluessel `c577aaeafe38` (b02: `8e8096768cf0`; Traegermenge im
Schluessel), kein Blockbau. **Training** `v35-b10` 1.714,1 s (`manifest_train_v35-b10_20261007_073340.json`), Warmstart
`v34-b01_brierbest`, Seed 20260965, Rezept byte-gleich b02; Manifest-Diff ohne unerwartete Abweichung (Kette lief weiter).

**Val-Brier auf den 120 b02-Val-Dateien** (vergleichbar, der Brier haengt nicht an der Traegermaske): Epoche 1 0,18906,
Minimum **0,18877 in Epoche 3**, Epoche 12 0,18938; `_brierbest` (Epoche 3) getrennt vom `_best`, gegatet wird
`alphazero_v35-b10_brierbest.onnx`. Das ist das beste Brier-Minimum der Reihe (b02 0,18942, b03/b06 0,18965, b05 0,18970,
b07 0,18946, b04 0,19034, b08-EMA 0,18930), obwohl b10 am Wertziel nichts aendert. Der `policy_val_loss` des Manifests
(1,19) ist NICHT mit b02 vergleichbar (Policy-Gewicht auf 120 statt 45 Val-Dateien, par.18).

**Offline gegen b02 auf der b02-Traegermaske** (`checkpoint_val_eval_v35-b10_vs_b02.json`, Referenz `v35-b02_brierbest`,
`--train-manifest` b02, Policy-CE auf den 45 Traeger-Val-Dateien, Brier auf allen 120, gepaart, Block-Bootstrap):

| Groesse | b02 minus b10 [CI95] | Lesung |
| --- | --- | --- |
| Val-Brier | **+0,00066 [+0,00030; +0,00104]** | b10 besser, CI ganz ueber 0 |
| Policy-CE gepoolt | **+0,0301 [+0,0278; +0,0326]** | b10 besser, CI ganz ueber 0 |

Zum Massstab: b02 gegen den Warmstart war Brier +0,00107 und Policy-CE +0,158 (par.12f); b10 legt auf den ganzen
Fenster-Effekt beim Brier rund 60 % und bei der Policy-CE rund 20 % obendrauf. **Die Erwartung von par.18 ("stichproben-
begrenzter Policy-Kopf -> CE-Gewinn mit CI ueber 0") ist eingetreten; Lesart (c) von par.17 (nicht stichprobenbegrenzt)
entfaellt.** Dazu ein nicht vorhergesagter Nebenbefund: der Wertkopf wird besser, ohne dass sein Ziel sich aendert; die
naheliegende Erklaerung ist der gemeinsame Rumpf, der von den zusaetzlichen Policy-Zielen auf 800 Schwarm-Dateien
bessere Merkmale lernt (HERLEITUNG, nicht gemessen). Vorfilter par.19.0 waere bestanden.

**Tor 1 gegen v34-b01** laeuft seit 08:11 (Seed 20261600, dann 20261601, Stufenregel). Offen danach: Lesart (a)
(CE-Gewinn UND Kante: Volumen traegt, Zuordnung an die Traegermenge) oder (b) (CE-Gewinn ohne Kante: "Korpus wirkt,
Gewicht nicht"); b09 (frische Sockel-Partien) ist nach Nutzer-Entscheid 2026-10-07 ("Mal schauen ob sich bei B10 was
tut. Dann entscheidet sich die Erzeugung von b09") erst nach diesem Verdikt zu starten oder zu streichen.

**Tor 1 Seed 20261600: v35-b10 185:115 = 61,7 %** nach 150 Paaren (n = 300), SPRT `ACCEPT_H1` fuer b10 (LLR +7,20,
Stopp vor dem Deckel), Block-z **+4,30** (30 Bloecke, Mittel 0,617, sd 0,149), gepaarte Differenz +0,47 [+0,25; +0,68],
5.202 s (17,34 s je Partie). Tor 2b: volle Spalten je Brett 1,027 gegen 0,983, Punkte 58,74 gegen 54,46 (+4,3, groesster
Punktvorsprung der Reihe in einem Seed), Strafsteine 8,15 gegen 8,15 (gleich), Plattenpunkte 8,23 gegen 7,09
(Spezialfelder -9,41 gegen -10,32, Vertikale 7,83 gegen 6,94, Mehrfarbige 4,18 gegen 3,56). Zum Vergleich auf demselben
Seed: b02 218:182 (z +1,51), b03 159:91 nach 125 Paaren (z +5,28), b06 231:169 (z +3,05). Stufe genommen, Seed 20261601
laeuft seit 09:30; der fruehe Stopp zaehlt nach Replikation bis zum Deckel.

### par.18b VERDIKT v35-b10 (Schwarm als Policy-Traeger): TOR 1 SEED 2 UND GEPOOLT (2026-10-07 09:30-11:25)

**Seed 20261601: v35-b10 235:155 = 60,3 %** nach 195 Paaren (n = 390), SPRT `ACCEPT_H1` fuer b10 (LLR +7,85, Stopp
einen Block vor dem Deckel), Block-z **+4,44** (39 Bloecke, Mittel 0,603, sd 0,144), gepaarte Differenz +0,41 [+0,22;
+0,60], 6.878 s (17,64 s je Partie). Tor 2b: volle Spalten je Brett 1,036 gegen 1,010, Punkte 59,79 gegen 55,65
(+4,1), Strafsteine 7,99 gegen 7,76, Plattenpunkte 9,42 gegen 7,91 (Mehrfarbige Felder 5,49 gegen 4,04, Vertikale 8,17
gegen 7,22, Spezialfelder -9,11 gegen -10,23).

**Gepoolt: 420:270 = 60,9 %** (n = 690 Partien, 345 Paare), **Block-z +6,22** (69 Bloecke, Mittel 0,609, sd 0,145).
Beide Seeds einzeln ueber +1,96 mit SPRT-Annahme, kein dritter Seed. **VERDIKT TOR 1: v35-b10 TRAEGT**, mit der
staerksten Kante der Reihe (b02 56,8 % z +4,07 ueber drei Seeds; b03 58,6 % z +5,12; auf denselben zwei Seeds b02 54,6 %
z +2,50).

| Seed | Ergebnis | Block-z | Punkte b10 / v34-b01 |
| --- | --- | --- | --- |
| 20261600 | 185:115 = 61,7 % (SPRT-Stopp nach 150 Paaren) | +4,30 | 58,74 / 54,46 |
| 20261601 | 235:155 = 60,3 % (SPRT-Stopp nach 195 Paaren) | +4,44 | 59,79 / 55,65 |
| gepoolt | 420:270 = 60,9 % | **+6,22** | |

**Lesart (a) von par.17/par.18: Policy-Volumen TRAEGT.** Offline CE-Gewinn mit CI ueber 0 (par.18a) UND Kante; einziger
Unterschied zu b02 ist die Traegermenge (1.200 statt 400 Dateien desselben Fensters, gleicher Val-Satz, gleicher Seed,
gleiches Rezept). Zuordnung an die Traegermenge; dass die zusaetzlichen Traeger Schwarm-Partien (Abweichung, Ausflug)
sind, hat nicht geschadet. Nebenbefund: der Punktvorsprung (+4,3 / +4,1 je Partie) ist der groesste der Reihe und kommt
vor allem ueber die Plattenpunkte (Mehrfarbige Felder, Vertikale, Spezialfelder), der Spaltenvorsprung ist dagegen klein
(+0,03 bis +0,04 je Brett). Arm gesamt rund 3,9 h (Manifest, Merge, Training 1.714 s, zwei Seeds 5.202 + 6.878 s).

**Folgen:** (1) b09 (frische Sockel-Partien, 800 Traeger) laeuft seit 11:25 wie registriert (Nutzer-Frist ohne Gegenwort);
seine Frage ist jetzt "Herkunft der Traeger" und "noch mehr Traeger", nicht mehr "ist der Kopf stichprobenbegrenzt".
(2) Eine direkte Kante b10 gegen b02 waere die saubere Bestaetigung der Zuordnung (Schnellblick par.19.0 reicht als
Vorsortierung nicht, hier ist die volle Kante angezeigt: Nutzer-Entscheid). (3) Fuer die Varianten par.19 (b11-b15) ist
b10 die neue Referenz-Traegermenge, sofern der Nutzer das so festlegt; sonst bleibt b02 die Baseline.

## par.19 ARME v35-b11 bis v35-b15: VARIANTEN DES TRAJEKTORIEN-BOOTSTRAPS (NUTZER 2026-10-06 23:xx: *"Registrier mir die Punkte 1 bis 5 der trajektorien. Dann haben wir die rundenuebergaenge schoen abgebildet"*; REGISTRIERT VOR Bau und Lauf)

**Anlass und Diagnose (par.13a-13f):** die drei Trajektorien-Arme tragen gegen v34-b01 (58,6 / 56,4 / 56,9 %), liegen
aber nur 2 bis 4 Punkte ueber b02 (Seed-Streuung), und ihre Brier-Minima liegen binnen 0,0003 mit b02 vorn. Lesung:
die Trajektorie bringt Information (echte Fortsetzung, tiefe Suche an einer spaeteren Stellung), kostet aber Rauschen
(ein einzelner Pfad, eine einzelne Suche); der Rollout glaettete, informierte aber nicht (par.12a). Die Varianten unten
senken das Rauschen der Trajektorie, ohne ihre Information aufzugeben. Alle sind reine Datenschicht
(`engine/py/trajectory_bootstrap.py`, `corpus_dataset.py`), Marker in BEIDEN Cache-Schluesseln, Standardweg bitgleich
(Abnahme wie bei b03), Fenster, Val-Satz, Seed und Rezept byte-gleich b02.

**par.19.0 Mess-Protokoll "Schnellblick" (Nutzer 2026-10-06: *"Ich brauch nicht gleich die volle Arena. Ich wuerd eher
nur mal schnell reinschauen lassen (2x50 seeds) wenn was spannendes dabei ist laesst sich die volle Breite untersuchen"*):**

1. Gegner ist **b02** (`alphazero_v35-b02_brierbest.onnx`), nicht v34-b01: die Frage ist, ob die Variante etwas AUF das
   @400-Fenster legt; gegen den Champion steckt der Fenster-Effekt immer mit drin (par.14a-Lesung, Nutzer 2026-10-06).
2. **Vorfilter offline** (rund 30 s): `tools/checkpoint_val_eval.py --checkpoints <b02 brierbest> <Arm brierbest>
   --val-list data/window_v35_b02_val.txt --train-manifest <Arm-Manifest>`, gepaart ueber Dateien; liegt das CI der
   Brier-Differenz (b02 minus Arm) GANZ UNTER 0 (Arm schlechter), entfaellt der Schnellblick, der Arm ist abgeschlossen.
3. **Schnellblick:** `tools/paired_gating.py` @400 beidseits, Spec `v34-b01_brierbest`, Blockgroesse 5, feste Laenge
   **2 Seeds a 50 Paare** (Seeds 20261700 und 20261701; n = 200 Partien), `--log-games`, SPRT-Schranken nur
   mitgeschrieben. Aufloesung vorab: 95-%-Intervall einer Siegquote bei n = 200 rund +-7 Punkte; der Blick trennt
   "deutlich" von "nicht deutlich", nicht die 2 bis 4 Punkte der bisherigen Arme.
4. **Lesart vorab:** gepoolt >= 55 % ODER gepoolter Block-z >= +1,5 (20 Bloecke) = "spannend" -> volle Breite gegen b02
   (2 x 200 Paare, Seeds 20261600/01, Stufenregel, Kriterium wie par.12). Zwischen 45 und 55 % ohne Block-z >= +1,5 =
   abgeschlossen, kein Hebel. Unter 45 % = abgeschlossen mit Gegenbefund. Die sechs Standard-Kennzahlen werden auch im
   Schnellblick berichtet.
5. Kosten je Arm (HERLEITUNG aus den Arm-Messungen par.13): Bloecke 1.200 Dateien rund 20 min, Merge 3 min, Training
   rund 28 min, Vorfilter 30 s, Schnellblick 200 Partien x rund 17,7 s = rund 1,0 h; zusammen rund 1,9 h je Arm, fuenf
   Arme rund 9,5 h ohne Vollausbau.
6. Dasselbe Protokoll steht fuer die Vorsortierung der tragenden Arme b03/b05/b06 gegen b02 zur Verfuegung (Nutzer-
   Entscheid, par.13f).

**par.19.1 Arm v35-b11: TD(lambda) ueber den echten Pfad (Punkt 1).** Statt des Suchwerts GENAU k Runden spaeter das
gewichtete Mittel der Suchwerte ALLER spaeteren eigenen Drafting-Records derselben Partie, Gewicht lambda_traj^(j-1) fuer
den j-ten spaeteren Record (j = 1 die naechste eigene Suchstellung), normiert; ohne spaeteren Record der Ausgang
(Rueckfall wie b03). Knopf `MOSAIC_BOOTSTRAP_SOURCE=trajectory_lambda`, `MOSAIC_BOOTSTRAP_TRAJ_LAMBDA` (Default 0,5;
Marker `bootstraptrajlambda_l<lambda>_v1`). Erwartung: Brier-Minimum nicht schlechter als b03, Schnellblick gegen b02
positiv, wenn das Rauschen der Einzelsuche der begrenzende Faktor war.

**par.19.2 Arm v35-b12: zusaetzlich die Gegnerstellungen (Punkt 2).** Wie b11, aber als Stuetzstellen auch die
Drafting-Records des GEGNERS nach der Stellung, mit gespiegeltem Wert (1 - root_q aus Gegnersicht), Gewichte in
Halbzug-Schritten (lambda_traj^((h-1)/2) fuer den h-ten spaeteren Record beider Seiten). Verdoppelt die Dichte der
Stuetzstellen. Knopf `MOSAIC_BOOTSTRAP_TRAJ_OPPONENT=1` (nur mit `trajectory_lambda`; Marker `_opp1`). Voraussetzung,
vor dem Bau zu pruefen: `root_q` der Gegner-Records ist aus Sicht des jeweiligen Ziehers gespeichert (Record-Feld
`player`), die Spiegelung ist dann 1 - q.

**par.19.3 Arm v35-b13: Mittel aus Trajektorie und Rollout (Punkt 3).** bvp = 0,5 x Trajektorie (wie b03, k = 1) +
0,5 x Rollout (Bestand `bootstrap_value`). Beide Werte liegen im Record, keine neue Erzeugung. Knopf
`MOSAIC_BOOTSTRAP_TRAJ_MIX=0.5` (nur mit `trajectory`; Marker `_mix0.5`). Billigste Kontrolle der Diagnose "Information
gegen Glaettung": ist b13 besser als b03 UND b02, tragen beide Anteile.

**par.19.4 Arm v35-b14: Mischgewichte neu (Punkt 4).** Die Anteile Ausgang / Bootstrap / Suchwert jetzt (heute 0,35 /
0,35 / 0,30 ueber `TD_LAMBDA` 0,5 und `--value-target-lambda` 0,7) wurden mit dem Rollout als Quelle gemessen
(`PREREG_lambda_wdl_arm.md`, Bootstrap-Horizont). Mit der Trajektorie als Quelle (b03-Form, k = 1) zwei Punkte:
b14a `TD_LAMBDA` 0,7 (Bootstrap-Anteil hoch, Ausgang runter: 0,21 / 0,49 / 0,30), b14b `--value-target-lambda` 0,5
(Suchwert jetzt hoch: 0,25 / 0,25 / 0,50). Dafuer wird `TD_LAMBDA` (heute Konstante `neural_net.py:1361`) zum Knopf
`MOSAIC_TD_LAMBDA` mit Marker in beiden Schluesseln (Standardweg 0,5 bitgleich); lambda ist Trainingsflag (kein neuer
Schluessel, wie b07). Zwei Trainings, zwei Schnellblicke.

**par.19.5 Arm v35-b15: Gewichtung nach Verlaesslichkeit der spaeteren Suche (Punkt 5).** Der spaetere Suchwert zaehlt
voll, wenn die Suche dort "sicher" war, sonst wird zum Ausgang hin abgeschwaecht: w = Konfidenz aus `root_child_q`
(Abstand des besten zum zweitbesten Kind-Q, geclippt auf [0, 1] ueber eine Skala s), bvp = w x root_q_spaeter +
(1 - w) x Ausgang. Die Skala s wird VOR dem Bau aus der Verteilung des Q-Abstands im b02-Fenster geeicht (Median als
Startwert), die Eichung wird hier nachgetragen, bevor trainiert wird. Knopf `MOSAIC_BOOTSTRAP_TRAJ_CONF_SCALE=<s>`
(nur mit `trajectory`; Marker `_conf<s>`). Hoechste Bau-Unsicherheit der fuenf; darum zuletzt.

**Reihenfolge (Nutzer-Rang, par.13f-Diskussion):** b11 und b12 zusammen gebaut (gleiche Funktion), b13 als Kontrolle
daneben, dann b14a/b14b, zuletzt b15. **Bau erst nach dem Ende der laufenden Ketten** (Arm-Kette, dann b10/b09): die
Datenschicht (`corpus_dataset.py`, `trajectory_bootstrap.py`, `file_cache_key.py`) wird von den Cache-Workern und von
train.py bei jedem Start neu importiert; eine Aenderung waehrend einer Kette aendert deren Verhalten
(Memory "Waechter-Worker importieren frisch", "laufende Laeufe lesen ihre Dateien neu"). Abnahme vor dem ersten Lauf:
Standardweg bitgleich (Datensatz-Hashes wie bei b03), Unit-Tests in `tools/tests/test_trajectory_bootstrap.py` je
Variante (Gewichte, Normierung, Spiegelung, Rueckfall), Marker in beiden Schluesseln (`test_window_key_covers_data_knobs`).

**Vorab festgelegt, was ein Gesamtergebnis heisst:** ist KEINE der fuenf Varianten im Schnellblick "spannend", ist die
Bootstrap-Quelle als Hebel abgeschlossen; was von der Reihe bleibt, ist der Fenster-Effekt @400 (par.12) und die
tragenden Arme b03/b05/b06 als gleichwertige Kandidaten neben b02. Ist eine "spannend", faehrt sie die volle Breite
gegen b02, und erst eine dort gefallene Kante begruendet einen Vorzug vor b02.
