<!-- STATUS: OFFEN | Frage: Traegt das v35-Fenster (fuenf v34-b01-Klassen, Modus-2-Sockel, W-v2, Wertmaske) ein Netz, das v34-b01 schlaegt? | Beleg: Fenster und Training v35-b01 GRUEN (par.11a), gegatet Epoche 2. Tor 1 Seed 1: 208:192 = 52,0 %, Block-z +0,92, Spalten 1,078 gegen 1,128 (par.11c); Seed 2 auf Nutzer-Entscheid abgebrochen, Tor NICHT entschieden. par.11b: Wertkopf lernt aus keiner Klasse messbar (dBrier +0,0006, CI mit 0), nur der Policy-Kopf bewegt sich (+0,068, am meisten @400). Offen: Nutzer-Entscheid Hebel. -->

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
