<!-- STATUS: OFFEN | Frage: Wie wird das v35-Fenster erzeugt und zugeschnitten, und traegt v35-b01 gegen den Generator v34-b01? | Beleg: Erzeugung komplett und abgenommen (par.9, par.10a/10b): Schwarm 2 x 4.000 + Sockel policy @400 1.000, policy-s100 1.000, W-v2 R1 2.000, alle GRUEN. Fenster, Training v35-b01 und Tor 1 registriert (par.11), Lauf steht aus. -->

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
(Nutzer 15:20); der Nutzer fragt 2026-10-04 abends selbst, ob sein Nutzen den Aufwand rechtfertigt (Vorlage des
Koordinators: streichen; Entscheid offen). Das Fenster wird OHNE Exploiter-Klasse gebaut.

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
