<!-- STATUS: OFFEN | Frage: Wie wird das v24-Trainingsfenster zugeschnitten? | Beleg: Zuschnitt vom Nutzer (2026-09-01), Rezept par.6b' mit K3-P C 1,0 (Vorbehalt gefallen, Champion-Kante par.10a der Einhuellenden-Prereg). ERZEUGUNG LAEUFT seit 2026-09-04 21:10 (Sockel extern, 1,48 s je Partie) und 21:31 (Value hier); par.6c Punkte 1 und 2 fuer alle drei Laeufe GRUEN (par.6c'), Tor 0 nach den Value-Laeufen. Nachtkette `tools/night_v24_chain.sh` traegt Manifest, Fenster, Monolith und die Trainings-Arme b01/b02 (par.8), b03 ueber `night_v24_b03_chain.sh`. Offen: Tor 0, Tor 1/2 je Arm, Generatorwahl. -->

# Vorregistrierung: v24-Fenster

**Angelegt 2026-09-01**, Zuschnitt vom Nutzer festgelegt, waehrend der
Relabel-Arm trainierte und die b03-Entscheidungsarena lief.

## par.1 Der Zuschnitt

**Sockel (Policy-Klasse, 5.800 Partien)**

| Posten | Quelle | Partien |
| --- | --- | --- |
| Sockel NEU | `v23-b01` Self-Play, policy-aktiv | 4.000 |
| Sockel Lehrer | `hv2`, policy-aktiv | 1.800 |

**Schwarm (Value-Klasse, 23.650 Partien)**

| Posten | Quelle | Partien |
| --- | --- | --- |
| Schwarm NEU | `v23-b01` Self-Play | 8.000 |
| Schwarm Lehrer | `hv2`, policy-maskiert | 15.650 |

**Summe 29.450** -- dieselbe Form wie v22 und v23, neu besetzt.

## par.2 Was daran NEU ist -- und wie wenig davon erzeugt werden muss

**Der hv2-Anteil ist identisch mit dem von v23:** 1.800 + 15.650 = 17.450
Partien, und genau so viele stehen im v23-Fenster (1.745 Dateien a 10 Spiele,
im Trainingslog von `v23-b05` nachgezaehlt). Im Baum liegen 2.400
hv2-Dateien, das Fenster zieht davon 1.745. **Es muss also kein einziges
Lehrerspiel neu erzeugt werden**; die Traeger-Auswahl (180 Dateien =
1.800 Partien) kann aus `data/carriers_v23_hv2.txt` uebernommen werden.

**Neu zu erzeugen sind 12.000 Partien mit `v23-b01`**: 4.000 fuer den Sockel
(gesampelt, mit Wurzelrauschen) und 8.000 fuer den Schwarm (6.000 argmax plus
2.000 gesampelt, beide `--value-only`). Das vollstaendige Rezept mit allen
Knoepfen steht in **par.6**; der fruehere Verweis "wie die Sockel-Erzeugung
von v23" zeigte auf `PREREG_v23_window.md` par.4c, und die dortige Zeile
"Sockel @400" ist FALSCH (gefahren wurden 100 Sims, dort seit 2026-09-01
berichtigt). **Mit `--per-file 10`** (`docs/working_rules.md`).

**Kosten, aus den drei v23-Erzeugungs-Manifesten abgelesen** (`data/manifest_v22-b05-*.json`,
Feld `laufzeit`, threads 11, 100 Sims; die fruehere Schaetzung "rund 23 h"
stammte aus einem 400-Sims-Richtwert und ist am 2026-09-01 ersetzt worden):

| Posten | gemessen v23 | s je Partie | Dauer |
| --- | --- | --- | --- |
| 4.000 Sockel-Partien (gesampelt, Rauschen) | 13.459,5 s | 3,365 | 3,74 h |
| 6.000 Schwarm argmax | 22.041,4 s | 3,674 | 6,12 h |
| 2.000 Schwarm gesampelt | 7.306,5 s | 3,653 | 2,03 h |
| Summe | 42.807 s | | **11,9 h** bei threads 11 |

`--per-file` aendert an der Dauer nichts, nur an der Dateizahl (1.200 statt
600). Als HERLEITUNG markiert: derselbe Generator-Typ, gleiche Sims, anderes
Netz; die Zahl gilt, bis das erste v24-Manifest sie ersetzt.

Der Lehreranteil kostet nichts, weil er liegt -- das ist der praktische
Hauptvorteil dieses Zuschnitts.

## par.3 Die Begruendung des Nutzers, woertlich

*"hv2 baut noch immer am meisten spalten und es ist noch nicht geklaert ab
wann sich die rotation selbst verstaerkt"*

Beides ist am Bestand belegbar, aber NUR am gleichen Instrument (berichtigt
2026-09-01; die erste Fassung dieses Absatzes setzte drei Betriebspunkte in
einen Satz, was `docs/generation_loop.md` ausdruecklich verbietet): der volle
hv2 erreicht in der gekoppelten Arena gegen hv1 bei 150 Sims 0,975 volle
Spalten je Partie, der Arm "nur Drafting" 0,756 (`PREREG_v22_window.md`
par.5, Split-Test). Der beste Netzstand b01 liegt am argmax-Instrument bei
0,5150 (@400) und 0,7200 (@100, `PREREG_r5_value_calibration.md` par.12),
in der Arena gegen b05 @400 bei 0,6456. Ein direkter Vergleich Lehrer gegen
b01 am SELBEN Instrument (gleiche Sims, gleicher Gegner) liegt NICHT vor;
die Aussage "hv2 baut am meisten Spalten" ist damit plausibel, aber
ungemessen. Und die Selbstverstaerkung
ist tatsaechlich offen: die Nacht auf den 2026-09-01 hat gezeigt, dass die
Policy-Dosis dieses Fensters einen bereits spaltenbewussten Spieler um 66
Prozent anhebt, einen Kaltstart aber nicht einmal auf den Stand des
Vorgaengers bringt (`PREREG_capacity_sim_frontier.md` par.12/13). Den Lehrer
im Fenster zu lassen, ist damit keine Vorsichtsmassnahme aus Prinzip, sondern
die Antwort auf einen gemessenen Befund.

## par.4 VORBEHALT: wer der Generator ist, steht noch nicht fest

Der Zuschnitt nennt `v23-b01`, weil er der beste Stand ist -- unter dem
ausdruecklichen Vorbehalt eines besseren v23-Kandidaten:

| Kandidat | Stand 2026-09-01 |
| --- | --- |
| `v23-b02` (Kaltstart) | gleich stark, aber ein Drittel der Spalten -- kein Generator |
| `v23-b03` (Ueberraschungs-Gewichtung) | Orakelmetriken Gleichstand (par.5 dort), erste Arena-Richtung 37:43 zurueck; zweite laeuft |
| `v23-b05` (relabelter Sockel) | gemessen: Arena 85:75 fuer b05, p = 0,53 -- nicht belegt besser (`reanalyze_label_depth` par.A1) |

**VORBEHALT AUFGELOEST (2026-09-01): `v23-b01` bleibt Generator.** Kein Arm der
Generation ist belegt besser -- b02 und b03 liegen mit 75:85 zurueck, b05 fuehrt
mit 85:75 bei p = 0,53. Bei n=160 gepaarten Partien ist +-10 Siege die
Rauschgrenze dieses Instruments; dass alle drei Arme dort landen, ist der Beleg
dafuer und nicht drei knappe Entscheidungen. Am Zuschnitt aendert sich nichts.

**Nachtrag 2026-09-01 (Pruefung der Preregs): diese Regel stand nicht vorab.**
`docs/generation_loop.md` definiert den Generator nur als "bester Stand von
N-1" und kennt keine Gleichstandsregel; "nicht belegt besser, also bleibt der
Amtsinhaber" ist am Messtag formuliert worden. Dazu wurde fuer b03 und b05 die
Kampagnen-Groesse (volle Spalten) NICHT gemessen, nur fuer b02
(`PREREG_capacity_sim_frontier.md` par.12/13); b03 und b05 sind allein ueber
Siege bei 80 Paaren beurteilt. Nach dem Punktschaetzer-Massstab des
Richtungs-Tors fuehrte b05 (85:75). Der Entscheid fuer b01 bleibt (dem Nutzer
am 2026-09-01 im Pruefbericht vorgelegt). **Die Regel steht seit 2026-09-02**
(`docs/generation_loop.md`, "Generatorwahl unter Armen": Staerke schliesst
aus, Spaltenprofil entscheidet, sonst Amtsinhaber); rueckwirkend auf v23
angewandt ergibt sie dieselbe Wahl (b05 +0,034 Spalten bei Block-SE 0,05,
Stufe 3, Amtsinhaber). Jeder Arm bekommt sein Spaltenprofil am
argmax-Instrument, bevor er als Generator ausscheidet.

## par.5 Was dieser Zuschnitt NICHT beantwortet

- **Die Dosisfrage.** Ob 1.800 Lehrer-Policy-Partien das Optimum sind, ist
  ungemessen; der Wert ist aus v23 uebernommen. Eine Dosis-Reihe ist
  registriert-aber-nicht-eingetaktet (Nutzer 2026-09-01: der Kaltstart
  interessiert weniger).
- **Die Generationen-Frage.** G-1 und G-2 kommen weiterhin aus DEMSELBEN
  hv2-Korpus (par.3 des v23-Fensters benennt das bereits als offenen Punkt);
  echte Generationsvielfalt entstuende erst, wenn ein frueherer NETZ-Stand
  einen eigenen Schwarm beisteuerte.
- **Ob das Fenster ueberhaupt der Hebel ist.** Die Phase-3-Schiene
  (Betrags-Daempfung des Value-Kopfs) ist am 2026-09-01 OHNE Bau geschlossen
  worden (`PREREG_r5_value_calibration.md` par.12); die Ursachenfrage der
  Tiefen-Delle liegt bei `PREREG_search_depth_column_optimum.md` Stufe 4 und
  ist vom Fenster unabhaengig.

## par.6 ERZEUGUNGSREZEPT, VOLLSTAENDIG (registriert 2026-09-01, VOR dem Start)

Anlass: die Pruefung vom 2026-09-01 fand, dass diese Prereg nur Anzahlen,
Wurzelrauschen und `--per-file` festlegte. Alles Weitere waere beim Start
still auf einen Default gefallen. Quelle jeder Zeile hier ist das
Manifest des entsprechenden v23-Laufs (`data/manifest_v22-b05-policy_20260831_033448.json`,
`..._value-argmax_20260830_192533.json`, `..._value-sampled_20260831_013258.json`),
nicht der Text von `PREREG_v23_window.md` par.4c, der in der Sims-Zeile falsch war.

### par.6a Generator und Knoepfe

| Was | Wert | Quelle / Grund |
| --- | --- | --- |
| Generator | `models/alphazero_v23-b01_brierbest.onnx` | Kandidat, der Tor 1 und Tor 2 bestanden hat (v23 par.2b-2e); Datei vom 2026-08-31 16:59 |
| Sims | **100** in allen drei Laeufen | gefahrener v23-Betriebspunkt (Manifeste); Suchtiefen-Strang: 100 baut 0,7200 gegen 0,5150 @400 |
| Zuschnitt D | Policy-Klasse gesampelt mit Rauschen; Value-Klasse 6.000 argmax ohne Rauschen plus 2.000 gesampelt | Lehrer-Prereg par.3b.12, v23 par.4c |
| `--value-only` | beide Schwarm-Laeufe | setzt `pcr_full_prob 0.0` und `pcr_cheap_sims = sims` (self_play.py:777-783); im Manifest NUR daran erkennbar, das Flag selbst wird nicht geschrieben |
| `--per-file` | **10** | `docs/working_rules.md` (v23 fuhr noch 20) |
| `--threads` / `--chunk` | 11 / 10 | wie v23; Thread-Budget bei GPU-Parallelbetrieb: `docs/working_rules.md` |
| Seeds | 20260904 (policy), 20260905 (argmax), 20260906 (sampled) | neu gewaehlt, Datumsform wie v23 (20260901/02/03); je Lauf ein eigener Seed, keiner aus v23 wiederverwendet |
| `MOSAIC_STACK_DRAW_RESEARCH=1` | in der Umgebung ALLER DREI Laeufe | chance_nodes par.15; hat keine Spec-Entsprechung und steht NICHT im Manifest, Kontrolle an den Daten (par.6c) |
| `MOSAIC_IMPLICIT_MINIMAX_A` | nicht setzen (0,0) | gemessener Entscheid v23 par.4c |
| `--seed-positions`, `--rtv`, `--pcr-full-prob`, `--spec` | nicht setzen | v23 par.4c; `spec: null` in allen drei v23-Manifesten |
| Bootstrap-Horizont, Startkuppel, `ROUND_TRANSITION_SAMPLING`, Reservation-Regel | Default (2, Handheuristik, false, aus) | unveraendert seit v23, `engine_config` der Manifeste |
| Wheel | 79-Kanal-Build, Vertragshash `efd564d87bac2722` | `engine_config.contract_hash` der v23-Manifeste; muss im v24-Manifest gleich sein, sonst Anker-Invarianz pruefen |

### par.6b Die drei Befehle

```
export MOSAIC_STACK_DRAW_RESEARCH=1
python -u self_play.py --mode network --model models/alphazero_v23-b01_brierbest.onnx --games 4000 --sims 100 --version v23-b01-policy --threads 11 --chunk 10 --seed 20260904 --per-file 10
python -u self_play.py --mode network --model models/alphazero_v23-b01_brierbest.onnx --games 6000 --sims 100 --value-only --version v23-b01-value-argmax --threads 11 --chunk 10 --seed 20260905 --per-file 10 --no-root-noise --deterministic
python -u self_play.py --mode network --model models/alphazero_v23-b01_brierbest.onnx --games 2000 --sims 100 --value-only --version v23-b01-value-sampled --threads 11 --chunk 10 --seed 20260906 --per-file 10
```

Die Dateien heissen nach dem GENERATOR (`selfplay_v23-b01-*`), nicht nach dem
Fenster (`docs/generation_naming.md`). Start ohne Pipe und ohne Umleitung,
Fortschritt am g-Suffix zaehlen.

### par.6b' REZEPT-VARIANTE MIT KNOPF K3-P (registriert 2026-09-04, 14:35 -- VORBEHALT: Nutzer "die Freigabe haengt an der Arena, aber ich tendiere zu ja")

Alle drei Befehle aus par.6b UNVERAENDERT, zusaetzlich in der Umgebung ALLER
DREI Laeufe (Sockel und beide Value-Laeufe, einheitliches Fenster):

```
export MOSAIC_ENVELOPE_PROJECTED=1 MOSAIC_ENVELOPE_SEARCH_C=1.0
```

Herleitung: `PREREG_geometric_envelope.md` par.8.7 (Bau), 8.7a-c (Instrument
und Arena, gepoolt 191:129 auf 320 Paaren, p = 0,014), 8.7d (Betriebspunkt
@100 mit dem Pilot-Rezept: 0,775 gegen 0,726 Spalten, 55 gegen 50 Prozent
Seiten mit voller Spalte, Huelle 0,718 gegen 0,685, Trennung +0,46), par.10
(Champion-Kante, Replikation laeuft). Profil = b01-Kurve (Default), Modus 1
(Musterreihen projiziert), `C_HULL` 1,0 -- C 2,0 ist am Instrument
spaltenreicher (0,635), in der Arena aber schwaecher; v24 faehrt 1,0.

**Manifest-Diff (par.6c Punkt 1) erwartet dann ZUSAETZLICH:**
`engine_config.envelope_projection_mode` 0 -> 1 und
`engine_config.envelope_search_c` 0.0 -> 1.0 (seit Commit a6789ed im
Manifest). Sonst nichts. Die Dateinamen bleiben `selfplay_v23-b01-*`
(Generator-Regel, `generation_naming.md`); dass der Knopf an war, steht im
Manifest, nicht im Namen.

**Freigabe:** faellt der Vorbehalt (Replikation par.10 haelt den Vorsprung,
Nutzer sagt ja), gilt 6b' als DAS Rezept; sonst 6b. Der Sockel darf auf
einer anderen Maschine laufen (Nutzer 2026-09-04; Befehle im Chat), die
Dateien und das Manifest kommen danach nach `data/`.

### par.6c Pflichtpruefungen direkt nach dem Start und nach dem Lauf

1. **Manifest-Diff gegen die v23-Referenz** (stehende Regel): erwartete
   Unterschiede sind GENAU `model`, `version`, `seed`, `per_file` (20 -> 10)
   und bei der Policy-Klasse `pcr_cheap_sims` (150 Default gegen 100; ohne
   PCR wirkungslos). Jeder weitere Unterschied stoppt den Lauf.
2. **Stack-Draw-Kontrolle an den Daten**, weil der Knopf nicht im Manifest
   steht: Records mit `choose_draw_stack_slot` in `valid_actions` muessen
   vorkommen (v23-Messung: 5,16 Prozent; ohne Knopf exakt 0).
3. **Tor 0 auf der Value-Klasse** (`docs/generation_loop.md`; die Schwelle
   gehoert laut Schleife HIERHER):
   - primaer: Symmetrie-Trennung signifikant > 0
     (`tools/probes/corpus_column_outcome_symmetry_probe.py --pattern "selfplay_v23-b01-value-*.pkl"`);
     v23-Wert 0,4041 bei t 41,26 ist die Berichtsgroesse, kein Mindestwert.
   - sekundaer: **mindestens 1.500 Partien-Seiten mit voller Spalte** in den
     16.000 Seiten der Value-Klasse (`tools/corpus_sanity_check.py data --pattern "selfplay_v23-b01-value-*.pkl"`,
     Feld `sides_with_full_column`). Herleitung der Schwelle: Lehrer-Prereg
     par.3b.12 (Stopp gegen Degeneration, keine Rate); v23 lag bei 5.629.
   - Reisst Tor 0: kein Training, Vorlage.

### par.6c' GEFAHREN fuer den argmax-Lauf (2026-09-04, 21:34; Chronik `night_run_20260902.md`)

Start 21:31 nach par.6b' (Nutzer-Freigabe; Sockel laeuft seit ~21:10 auf dem
anderen Rechner des Nutzers, Kontrakt dort `efd564d87bac2722`). Punkt 1:
`cli_args`-Diff GENAU model / version / seed / per_file; `engine_config`
Modus 1 und C 1,0 wie 6b', dazu sieben seit dem 30.08. neu exportierte
Knopf-Felder auf Default (kein Rezeptunterschied; `envelope_reach_w` 0,25
wirkt nur im Modus 2, `envelope.rs:330`); `contract_hash` gleich. Punkt 2:
101 von 3.526 Records der ersten zwei Dateien mit `choose_draw_stack_slot`
(2,86 %) -- Knopf an. Punkt 3 (Tor 0) nach dem Lauf. Cache-Bloecke entstehen
mitlaufend (`build_cache_incremental.py --watch`, Cache-Prereg par.6), die
Laufzeit des Laufs ist darum unter Nebenlast gemessen.

**Nachtrag 21:40: Sitzungsneustart, argmax-Lauf nach Chunk 4 gestorben.** Die
5 fertigen Dateien (Chunks 0-4) bleiben; der Rest laeuft als eigener Lauf mit
`--games 5950 --seed 20260910` (= base_seed + 5, self_play.py:515), der die
Chunks 5-599 deterministisch identisch erzeugt. Fuer par.6c Punkt 1 gilt darum
fuer die Value-argmax-Klasse ZUSAETZLICH erwartet: `cli_args.games` 5950 und
`cli_args.seed` 20260910 im zweiten Manifest; die Klasse hat zwei Manifeste.

**Nachtrag 23:19, Sockel (Policy-Klasse) GRUEN:** 400 Dateien vom anderen
Rechner des Nutzers in `data/`, Manifest `manifest_v23-b01-policy_20260904_212036.json`,
1,481 s je Partie bei threads 11 (Core Ultra 7 255H). Diff gegen die
v23-Policy-Referenz: `cli_args` genau model / version / seed / per_file
(`pcr_cheap_sims` in beiden 150, kein Unterschied), `engine_config` wie beim
Value-Lauf, Kontrakt gleich. Stack-Draw an 30 Dateien 2,87 %. Damit sind
Punkte 1 und 2 fuer alle drei Laeufe belegt; Punkt 3 (Tor 0) nach den
Value-Laeufen.

**Nachtrag 2026-09-05, 04:02:** argmax-Klasse komplett (600 Dateien; Tail
5.950 Partien in 21.937,9 s, 3,687 s je Partie unter Nebenlast). Gesampelter
Lauf seit 03:46, Punkte 1 und 2 GRUEN (Diff genau model / version / seed /
per_file, Modus 1 und C 1,0, Kontrakt gleich; Stack-Draw 3,11 %). Damit sind
Punkte 1 und 2 fuer alle vier Manifeste der Erzeugung belegt.

**Nachtrag 2026-09-05, 05:16: ERZEUGUNG KOMPLETT.** 1.200 Dateien (400 policy,
600 argmax, 200 sampled). Laufzeiten: Sockel 1,481 s je Partie (andere
Maschine), argmax 3,687 s (unter Nebenlast), sampled 2,684 s (nur Watcher),
alle threads 11. Tor 0 folgt in der Nachtkette.

### par.6d Fenster, Traeger und Cache

- **Dateiliste `data/window_v24.txt`** = die 1.745 hv2-Dateien aus
  `data/window_v23_hv2.txt` UNVERAENDERT plus alle 1.200 `selfplay_v23-b01-*`-Dateien
  (400 policy, 600 value-argmax, 200 value-sampled). Summe 2.945 Dateien,
  29.450 Partien. `train.py --file-list` bricht bei fehlenden Eintraegen hart ab.
- **Traeger-Manifest `data/policy_carrier_manifest_v24.json`: 180 hv2 + 400
  policy = 580 Eintraege.** `data/carriers_v23_hv2.txt` allein reicht NICHT:
  sie listet nur die 180 hv2-Dateien, und ein Manifest ohne die neue
  Policy-Klasse setzt deren `pol_w` still auf 0 (Traeger-Falle,
  `PREREG_v23_window.md` par.4a3, am Code geprueft). Aufruf wie v23, mit
  demselben Seed, damit dieselben 180 hv2-Traeger herauskommen:

```
python tools/generate_carrier_manifest.py --from-list data/window_v23_hv2.txt --n-files 180 --seed 20260921 --include-glob "selfplay_v23-b01-policy_*.pkl" --out policy_carrier_manifest_v24.json
```

  Pruefung: die 180 hv2-Eintraege muessen mit `data/carriers_v23_hv2.txt`
  uebereinstimmen (Diff leer), `policy_carrier_files` hat 580 Eintraege, und
  im Trainingsmanifest zeigt `policy_carriers.traeger_dateien_je_praefix`
  180 + 400.
- **Cache**: nur die 1.200 neuen Dateien brauchen Bloecke
  (`tools/build_cache_incremental.py --data-dir data --encoder 2d --value-target-variant nortv --workers 6 --file-list data/window_v24.txt`),
  die 1.745 hv2-Bloecke liegen. **Vor dem Training den Fenster-Monolithen
  parallel bauen** (`--merge-out` plus `train.py --cache-file`), sonst kostet
  das Zusammenfuegen 4,98 h einkernig (`PREREG_cache_build_time.md` par.11).
  Achtung Hebel 4: der Monolith traegt den Fenster-Schluessel; `--val-frac`
  muss beim Bau und beim Training gleich sein.

### par.6e Trainingsrezept `v24-b01` und die Tore

Standardrezept wie `v23-b01` (Manifest `models/manifest_train_v23-b01_20260831_110246.json`),
geaendert sind nur Startgewicht, Fensterliste, Manifest und Val-Pool:

```
export MOSAIC_CARRIER_MANIFEST=policy_carrier_manifest_v24.json MOSAIC_IGNORE_POLICY_TARGET_VALID=1 MOSAIC_VAL_POOL='^selfplay_v23-b01-'
python -u train.py --name v24-b01 --load v23-b01_brierbest --file-list data/window_v24.txt --encoder 2d --value-target-variant nortv --value-head wdl --ownership-head-2d --ownership-weight 1.0 --endgame-head --opp-points-head --moon-loss-weight 0 --select-by-brier --val-frac 0.05 --epochs 12 --lr 5e-5 --lr-schedule cosine --lr-t-max 12 --seed 20260828
```

`--load v23-b01_brierbest` ist ein ENTSCHEID, kein Erbe: v23 lud `v22-b05`
(den Generator-Stand, nicht dessen `_brierbest`); hier ist der Generator der
`_brierbest`-Checkpoint, also wird der geladen. Wer davon abweicht,
registriert es.

| Tor | Instrument | Bezugswert (Vor-Generation am SELBEN Instrument) |
| --- | --- | --- |
| 1 | `tools/paired_gating.py` gegen `v23-b01_brierbest` @400, Champion-Strenge (n >= 150 Paare oder Replikation mit eigenem Seed); beide Seiten dieselbe Spec (Vorschlag: Champion-Spec mit Knopf, Nutzer-Entscheid vor dem Tor) | -- |
| 2a | argmax-Instrument @400, 200 Partien (`self_play.py --deterministic --no-root-noise`) | b01 **0,5150** (`evaluations/artifacts/tor2a_v23b01.json`) |
| 2b | gepaarte Arena gegen b01 mit `--log-games`, `tools/probes/arena_column_probe.py` (Anzahl voller Spalten aus der Brettgeometrie) | b01-Seite DERSELBEN Arena; zum Vergleich b01 gegen b05: 0,6456 |
| Champion-Kante | gegen den AMTIERENDEN Champion `v23-b01_k3p10` (b01 + K3-P C 1,0, seit 2026-09-04 19:33; die urspruengliche Zeile nannte v21) @400, **beide Seiten mit derselben Spec** (Knopf an), sonst misst die Kante den Knopf statt das Netz; berichten, Promotion nur nach `promotion_checklist.md` | b01 + K3-P gegen v21 259:191 gepoolt (`geometric_envelope` par.10a); b01 ohne Knopf gegen v21 214:186 |

Jeder weitere Arm dieser Generation bekommt VOR seinem Ausscheiden als
Generator sein Spaltenprofil am argmax-Instrument (Lehre aus par.4).

## par.7 MATERIAL-PILOT (Nachtprogramm N2, gefahren 2026-09-04, 05:30-06:55): das v24-Material ist spaltenreicher und signaltragender als das v23-Material

Rezept exakt par.6b, nur klein und mit eigenen Seeds und Tag `pilot24`
(gehoert in KEIN Fenster): Value-Klasse 400 Partien argmax @100
(`--value-only --no-root-noise --deterministic`, Seed 20260910,
`MOSAIC_STACK_DRAW_RESEARCH=1`, 1.342 s = 3,36 s je Partie, threads 11) und
Sockel-Klasse 200 Partien gesampelt @100 (Seed 20260911, 659 s). Artefakte
`pilot24_symmetry_value_argmax.json`, `pilot24_sanity_value_argmax.json`,
`pilot24_sanity_policy.json`.

| Groesse (Value-Klasse) | Pilot v24 (b01 @100) | Bezug v23-Material (b05 @100) | Lesart N2 |
| --- | --- | --- | --- |
| Seiten mit voller Spalte | **403 von 800 = 50,4 %** | 5.629 von 16.000 = 35,2 % | ueber 35 % -> mindestens so spaltenreich |
| volle Spalten je Seite | **0,726 +- 0,056** | 0,72 (par.2i der v23-Prereg, b01 @100) | wie erwartet |
| Symmetrie-Trennung (Sieger minus Verlierer, volle Spalten, Block-Mittel) | **+0,513** (Block-SE 0,047, t 11,0, 40 Bloecke) | +0,404 (t 41,26) | nicht unter 0,40 -> signaltragend |
| Korrelation volle Spalten mit Ausgang (Block-Mittel) | 0,505 (t 13,9) | -- | |
| Punkte / Strafleiste je Seite | 49,7 / 5,40 | -- | |

Sockel-Klasse (gesampelt, Rauschen): 0,188 volle Spalten, 27,2 Punkte,
Strafleiste 9,46 -- das ist die erwartete Rauschklasse (v23-Sockel lag in
derselben Groessenordnung; sie traegt die Policy, nicht die Spalten).

**Verdikt nach der vorab benannten Lesart (N2):** beide Schwellen erfuellt
(50 Prozent Seiten mit voller Spalte gegen 35, Trennung 0,51 gegen 0,40).
Das v24-Material waere mindestens so spaltenreich und so signaltragend wie
das v23-Material -- Tor 0 ist fuer den Generator `v23-b01_brierbest` @100
VORAB belegt.

**Nachtrag 2026-09-04, 14:06 (K3-P im Betriebspunkt, `geometric_envelope` 8.7d):**
dasselbe Pilot-Rezept mit `MOSAIC_ENVELOPE_PROJECTED=1 MOSAIC_ENVELOPE_SEARCH_C=1.0`
(Tag `pilot24k3p`, gleicher Seed): 0,775 Spalten je Seite (gegen 0,726),
440 von 800 Seiten mit voller Spalte (55 gegen 50 Prozent), 51,0 Punkte,
Huelle 0,718 (gegen 0,685), Trennung +0,455 (gegen +0,512, innerhalb einer
SE). Der Knopf verbessert das Material in der Erzeugung selbst; als
Rezept-Knopf der Value-Laeufe (par.6a) Kandidat -- Nutzer-Entscheid vor dem
Start, dazu ob auch die Sockel-Klasse ihn traegt. Das beantwortet die Nutzer-Frage vom 2026-09-02 ("welche
Evidenz haben wir, dass v24 besser wird") fuer das MATERIAL; die Frage nach
dem Knopf im Rezept (K3-P, par.8) bleibt davon unberuehrt.

## par.8 ARME UND KNOEPFE DER GENERATION v24 (Nutzer 2026-09-03: "wir sollten uns alle Themen mit v24 ansehen")

Ausgangslage: der Generator steht (b01), das Material steht (par.6), die
Rezept-Knoepfe der Policy-Seite sind in v23 ausgemessen (b03, b05, b07:
Nullbefunde bzw. laufend). Die Arbeitshypothese seit 2026-09-02 ist der
MASSSTAB des Value-Kopfs (`capacity_sim_frontier` par.15,
`saturating_score_utility` par.6b). v24 prueft deshalb die fuenf offenen
Hebel, die daran oder an der Datenseite ansetzen -- getrennt nach dem, was
ein Training braucht, und dem, was ein Suchknopf am fertigen Netz ist.

### Trainings-Arme (GPU, je rund 2,5 h mit Monolith; Namen vorab, `generation_naming.md`)

| Arm | Was | Prereg | Einziger Faktor gegen b01 |
| --- | --- | --- | --- |
| `v24-b01` | Standardrezept, Warmstart aus `v23-b01_brierbest`, Fenster par.1/par.6 | diese Datei | Kontrolle |
| `v24-b02` | **lambda 0,7** im Value-Ziel (`--value-target-lambda 0.7`): Partieausgang mit Bootstrap-Anteil `root_q` gemischt | `lambda_v18only` (0,7 war 227:173 arena-signifikant, WDL-Aera-Grenze) | `value_target_lambda` |
| `v24-b03` | **Seeding-Schwarm**: 1.500 Stellungen aus der v24-Value-Klasse (Spieler am Zug, R2-4, Spaltenfortschritt 3-5), k = 4, 6.000 Partien `--value-only` @100 als Zusatz-Schwarm; Regel und Kosten (rund 3 h) in `start_position_seeding` par.7 | `start_position_seeding` par.7 | Fensterzusammensetzung (Zusatz-Schwarm), sonst b01 |
| `v24-b04` | **Sicht-Arm** (Nutzer 2026-09-05): 30 additive Flachwerte -- Plattentyp (Stapel-Rueckseite 2, Wild/Spezial der Auslage 6), Strafleisten-Farben (10), Phantom-Anteil je Musterreihe (12), `INPUT_SIZE` 714 -> 744, Warmstart mit null-initialisierten neuen Spalten; Kriterium Sichtgleichheit, Arena als Waechter | `stack_top_feature` par.10 | Eingabe (+8 Werte), sonst b01 |
| `v24-b05` | **Ueberraschung nur bei sicherer Suche** (Nutzer 2026-09-05): `--surprise-alpha 0.5 --surprise-confidence-min 0.5`, sonst b04-Rezept | `policy_surprise_weighting` par.10 | Policy-Gewichtung (gegatet), gegen b04 |

Reanalyze Teil B (Value tief nachrechnen) wird erst fuer b02 zum Werkzeug
mit Verbraucher (lambda < 1); ob er nachgezogen wird, entscheidet sich nach
b02, nicht vorher (`reanalyze_label_depth` par.A4, Kostenlage 15 h je
Sockel-Relabel).

### Such-Knoepfe (kein Training; Bau in der Engine, Default aus, Paritaets-Gate, dann Arena am besten v24-Netz)

| Knopf | Was | Prereg | Messung |
| --- | --- | --- | --- |
| K1 Margen-Saettigung | Blattwert aus Siegwahrscheinlichkeit UND saettigender, re-zentrierter Marge aus Punkte- minus Gegnerpunkte-Kopf | `saturating_score_utility` par.6b (kein neuer Kopf) | gepaarte Arena gegen dasselbe Netz ohne Knopf, Spalten aus Logs |
| ~~K2 Risiko-Utility~~ | GESTRICHEN 2026-09-03: der WDL-Kopf hat zwei Klassen, kein Remis; Stufe A waere eine affine Umskalierung des Siegwerts (`risk_sensitive_leaf_utility` par.6). Bleibt als bedingter TRAININGS-Folgearm (Streuungs- oder Verteilungskopf) hinter K1 | -- | -- |
| K3 Gelaender (c) | rundenabklingendes Dreiecks-Potential in Suche und Tiling, Form B oder C, Stufe 0 bestanden (Kopf kennt die Huelle) | `geometric_envelope` par.5c, par.3d | dito, zusaetzlich argmax-Spaltenprofil |
| K3-P2 Platzhalter (Nutzer 2026-09-05: "ja bau k3-p2") | K3-P plus Platzhalter-Regel: gebundene Reihe ohne annehmende Zielzelle zaehlt mit w_slot 0,5 auf den plattenlosen Huellenzellen ihrer Zeile (Modus 4) -- Lenkung der Plattenwahl R1-2 | `geometric_envelope` par.8.9b, par.8.11 (gebaut, cargo/Wheel ausstehend) | argmax @400 und gepaarte Arena am v24-Siegernetz gegen K3-P, plus Kuppel-Bonus je Partie (`arena_points_probe.py`) |
| K4 Rundenschaetzer (Nutzer 2026-09-05: "additiver term ist denk ich gut") | additiver Term am Netz-Blattwert: tanh((E0 - E1)/B_est) mit E = Solver-Rundenscore plus Strafleisten-Busse, Runde 5 null, kein Profil; Skala B_est wird vorab gemessen | `round_estimate_leaf_term` par.3-5 (registriert, nichts gebaut) | Skala-Sonde, Paritaetsgate, argmax @400 und gepaarte Arena am v24-Siegernetz, Kuppel-Bonus und Strafe je Partie |
| Tiling im Blatt, Variante B (Nutzer 2026-09-05: "ja registrier B") | Rundenende-Blatt spielt das Tiling beider Seiten mit dem Loeser durch, zieht EINE Fabrik-Neubefuellung mit stellungsgebundenem Seed und bewertet dann mit dem Netz (Leitsatz: Drafting muss das Tiling kennen) | `round_transition_search_sampling` par.4.2 (Bauvorgabe), par.7 | Kostentor 25 %, Anteil Rundenende-Blaetter, gepaarte Arena dasselbe Netz mit gegen ohne Schalter, Block-Streuung gegen 5,75 pp |

**Reihenfolge und Kosten:** Erzeugung (11,9 h CPU) -> b01 (GPU) -> parallel
zur GPU die drei Engine-Bauten mit Paritaets-Gate (CPU, je Bau plus Arena
rund 1,5-2 h) -> b02, b03 (GPU) -> Abnahme aller Arme mit Tor 1, Tor 2a/2b
und der Generatorwahl-Regel (`generation_loop.md`). Knoepfe, die am
v24-b01-Netz tragen, werden am Gewinner-Arm wiederholt, bevor sie ins
Rezept gehen (ein Knopf, ein Netz, eine Messung -- keine Kreuzprodukte ohne
Anlass).

**Registrierungsstand (2026-09-03):** K1 baureif (`saturating_score_utility`
par.14), K3 baureif (`geometric_envelope` par.8), K2 gegenstandslos
(`risk_sensitive_leaf_utility` par.6), b03-Kuratierungsregel registriert
(`start_position_seeding` par.7). Nichts wird vor seiner Registrierung
angefasst; alles Registrierte darf laufen, ausser der Erzeugung selbst
(Nutzer 2026-09-03).

## par.9 ERGEBNISSE DER ARME (ab 2026-09-05; Werkzeuge `tools/night_v24_chain.sh`, `night_v24_b03_chain.sh`, `night_v24_acceptance_chain.sh`)

**Tor 0 (Value-Klasse, 10:37 registriert): GRUEN.** Symmetrie-Sonde TRENNT
(`artifacts/v24_symmetry_value_class.json`), 6.945 von 16.000 Seiten mit
voller Spalte (Schwelle 1.500; v23 5.629), volle Spalten 0,6085 je Seite,
Punkte 44,0 (`v24_sanity_value_class.json`). Fenster-Kennzahl der
Policy-Klasse (Bericht, v25 par.7): 1.319 von 8.000 Seiten, 0,189, Punkte
26,0 (`v24_sanity_policy_class.json`).

| Arm | Training | Tor 2a (argmax @400, Knopf an; Bezug b01 + K3-P 0,555) | Tor 1 (gegen `v23-b01_brierbest`, beide Seiten Champion-Spec) | Tor 2b | Stand |
| --- | --- | --- | --- | --- | --- |
| `v24-b01` | 06:12-08:58, 9.973 s, `_brierbest` Epoche 2 (val_brier 0,1919, Val-Pool v24) | **0,4425** (KI +-0,063), Punkte 45,7 -> **GERISSEN** | 34:46 (40 Paare, SPRT H0) und 49:61 (55 Paare, H0), gepoolt 83:107, Elo informativ 1219 [1160, 1283] -> **GERISSEN** (kein Beleg besser; "schwaecher" ist damit NICHT belegt, siehe Tor 2b) | **93:67** ueber beide Richtungen (v24 auf Brett 0: 52:28, auf Brett 1: 41:39; Seed 20261014, je 80, Spec beide Seiten); Spalten v24 **0,696 / 0,600** gegen b01 0,494 / 0,575 (SE 0,07-0,09), Punkte 48,4 / 45,5 gegen 41,9 / 44,6, Huelle gleich (0,55) -> **NICHT GEFALLEN** | Tor 1 und 2a gerissen, 2b gehalten und den beiden anderen entgegengesetzt; scheidet als Generator aus (kein Beleg besser); Ursachenanalyse par.9a |
| `v24-b02` (lambda 0,7) | 08:58-12:21, 12.166 s (Datenaufbau 71 s), `_brierbest` Epoche 2 (val_brier 0,1923), `_best` Epoche 1; Val-R2 Value 0,47 (anderes Ziel, nicht mit b01 vergleichbar), Plateau-Muster wie b01 | -- | -- | -- | Abnahme laeuft seit 16:56 (zweiter Anlauf nach dem Neustart). **Tor 2a OHNE Knopf (17:25): 0,430 volle Spalten (KI +-0,066), Punkte 46,2, Zeilen 0,188** gegen b01 ohne Knopf 0,510 und v24-b01 ohne Knopf 0,518 -- spaltenaermer als beide (`tor2a_v24b02nk.json`). **Tor 1 OHNE Knopf (18:45, beide Seiten `k3v_off`, Seed 20261016, `paired_gating_result_v24-b02_vs_v23-b01_noknob_s16.json`): 209:161 nach 185 Paaren, SPRT-ENTSCHEID fuer v24-b02 (LLR +3,09), McNemar p 0,016, gepaarte Differenz +0,26, Punkte 45,9 gegen 43,8, Strafleiste 9,7 gegen 11,4; 4.457 s.** Erste Ratsche der Generation, die genommen wurde (v24-b01 ohne Knopf: 216:184, kein Entscheid); Champion-Strenge verlangt einen zweiten Seed (nicht in der Kette). **Tor 2a MIT Knopf (19:07, `tor2a_v24b02.json`): 0,525 volle Spalten (KI +-0,069), Punkte 49,1, Zeilen 0,195, Strafleiste 5,8** gegen Bezug b01 + K3-P 0,555 (Punktschaetzer darunter, KI schliesst ihn ein) und v24-b01 + Knopf 0,443. Anders als bei v24-b01 hebt der Knopf b02 (0,430 -> 0,525, +0,095), die Wechselwirkung hat hier das Vorzeichen von b01 (+0,045). **Tor 1 MIT Knopf (19:40, beide Seiten Champion-Spec, Seed 20261012, `paired_gating_result_v24-b02_vs_v23-b01_s12.json`): 101:69 nach 85 Paaren, SPRT-ENTSCHEID fuer v24-b02 (LLR +3,26), McNemar p 0,011, gepaarte Differenz +0,38, Punkte 49,0 gegen 45,1, Strafleiste 8,6 gegen 10,9; 2.033 s.** Fruehstopp unter 150 Paaren; **Replikation Seed 20261013 (20:35, `..._s13.json`): 91:59 nach 75 Paaren, erneut SPRT-ENTSCHEID fuer v24-b02, p 0,014, Diff +0,43, Punkte 47,9 gegen 44,6, Strafleiste 10,2 gegen 11,3; 2.114 s. Gepoolt 192:128 aus zwei unabhaengigen Seeds -- Champion-Strenge erfuellt (wie v23: zwei Seeds).** Elo-Knoten `v24-b02_k3p10` gegen `v23-b01_k3p10`. **Tor 2b (20:52, `paired_arena_env_v24b02_vs_b01_{first,second}_s14.json`, beide Seiten Champion-Spec, Seed 20261014): Siege 43:37 (b02 auf Brett 0) und 44:36 (b02 auf Brett 1), zusammen 87:73; volle Spalten b02 0,550 / 0,475 gegen b01 0,688 / 0,562 (SE 0,08), Punkte 45,9 / 44,5 gegen 47,1 / 42,0; Kuppel-Bonus 4,0 / 3,5 gegen 4,1 / 3,8 (`points_v24b02_vs_b01_s14.json`) -> Spalten in BEIDEN Richtungen unter dem Vorgaenger: GERISSEN.** |
| `v24-b04` (Sicht-Arm, INPUT_SIZE 744: Plattentyp, Strafleisten-Farben, Phantom-Anteile) | 17:21-20:51 mit Unterbrechung (Harness-Stopp 19:39 in Epoche 9, per `--resume` ab Epoche 9 fortgesetzt, Chronik), 13.305 s Wanduhr ueber beide Segmente (Datenaufbau 98 s im zweiten), `_brierbest` Epoche 4 (val_brier 0,1922), `_best` Epoche 1; Brier-Verlauf 0,1929 / 0,1924 / 0,1922 / 0,1922 / 0,1924 / 0,1928 ... 0,1929 -- Minimum frueh wie bei b01/b02, danach Erosion | **0,5325** (KI +-0,071), Punkte 49,0, Zeilen 0,185 -- Bezug b01 + K3-P 0,555, KI schliesst ein | OHNE Knopf (Seed 20261016, `paired_gating_result_v24-b04_vs_v23-b01_noknob_s16.json`): 218:182 nach 200 Paaren, kein SPRT-Entscheid, p 0,085, Diff +0,18 [-0,01, +0,37], Punkte 45,9 gegen 43,0, Strafleiste 10,3 gegen 10,4; 5.597 s. **MIT Knopf (Seed 20261012, `..._s12.json`, 01:17): 135:135 nach 135 Paaren, SPRT H0 (LLR -3,02), McNemar p 1,0, Diff 0,00 [-0,23, +0,23], Punkte 44,2 gegen 43,5, Strafleiste 10,7 gegen 11,1; 3.671 s** -- nach 40 Paaren stand es 49:31, der Vorsprung zerfiel vollstaendig; Fruehstopp < 150. **Replikation Seed 20261013 (`..._s13.json`, 02:38): 221:179 nach 200 Paaren, KEIN SPRT-Entscheid (LLR +1,74, Deckel), McNemar p 0,046, Diff +0,21 [+0,01, +0,41], Punkte 48,8 gegen 46,4, Strafleiste 10,8 gegen 10,7; 4.827 s.** Gepoolt 356:314 aus 335 Paaren -- in keinem der beiden Seeds ein SPRT-Entscheid fuer b04, die Ratsche ist nach dem Tor-1-Kriterium NICHT genommen (informativ: Punktschaetzer positiv, McNemar im zweiten Seed knapp unter 0,05; kein Verdikt "schwaecher"). Elo-Knoten `v24-b04_k3p10` gegen `v23-b01_k3p10` | **92:68** ueber beide Richtungen (03:04, `paired_arena_env_v24b04_vs_b01_{first,second}_s14.json`, beide Seiten Champion-Spec, Seed 20261014, je 80): b04 auf Brett 0 **42:38**, auf Brett 1 **50:30**; volle Spalten b04 **0,684 / 0,738** gegen b01 0,608 / 0,525 (SE 0,08-0,09; `columns_v24b04_vs_b01_*_s14.json`, 1 Partie nicht replaybar), Punkte 45,9 / 48,7 gegen 45,3 / 43,1, Strafleiste 9,9 / 10,6 gegen 10,6 / 11,0, Huelle 0,550 / 0,576 gegen 0,557 / 0,535; Kuppel-Bonus je Partie 3,9 / 4,3 gegen 3,6 / 3,9 (`points_v24b04_vs_b01_s14.json`); lange Reihen begonnen/vollendet 4,43/2,77 und 4,39/2,91 gegen 4,23/2,58 und 4,19/2,50 -> Spalten in BEIDEN Richtungen ueber dem Vorgaenger: **NICHT GEFALLEN** | **Abnahme komplett (03:04).** Tor 2a ohne Knopf gerissen (0,4125 gegen 0,510), mit Knopf 0,5325 (KI schliesst Bezug 0,555 ein); Tor 1 ohne Knopf 218:182 und mit Knopf 135:135 / 221:179: in keiner Fassung ein SPRT-Entscheid (kein Beleg besser, kein Beleg schwaecher); Tor 2b gehalten, mit 92:68 informativ vorn. Profil wie v24-b01 (2b gehalten), aber ohne dessen Tor-1-Niederlage mit Knopf; der Knopf hebt b04 um +0,12 wie b02. Abnahme lief in `venv_measure744` (744er-Wheel, Anker darunter GRUEN) |
| `v24-b05` (b04-Rezept plus Ueberraschungsgewichtung alpha 0,5 mit Sicherheits-Tor 0,5, `policy_surprise_weighting` par.10) | 20:51-00:20, 12.553 s (Datenaufbau 55 s, Val-Cache 744 lag), `_brierbest` Epoche 4 (val_brier 0,1925); Brier-Verlauf endet 0,1928 / 0,1932 / 0,1930 -- Policy-Loss hoeher als b04 (1,09 gegen 0,74 in Epoche 12, erwartbar durch die Gewichtung) | -- | -- | -- | Abnahme laeuft seit 2026-09-06 03:08 (`night_v24_b05_acceptance_wait.sh`, Basis-python, 744er-Wheel); Bezug b04 UND b01. **Tor 2a OHNE Knopf (03:35, `tor2a_v24b05nk.json`): 0,4825 volle Spalten (KI +-0,068), Punkte 46,8, Zeilen 0,185, Strafleiste 5,7** gegen b01 ohne Knopf 0,510 (Punktschaetzer darunter, KI schliesst ein), b04 ohne Knopf 0,4125, b02 0,430, v24-b01 0,518 -- spaltenreicher als b04 und b02, Punkte hoeher als b04 (44,4). **Tor 1 OHNE Knopf (03:53, beide Seiten `k3v_off`, Seed 20261016, `paired_gating_result_v24-b05_vs_v23-b01_noknob_s16.json`): 66:34 nach 50 Paaren, SPRT-ENTSCHEID fuer v24-b05 (LLR +3,63), McNemar p 0,004, Diff +0,64 [+0,26, +1,02], Punkte 47,3 gegen 41,5, Strafleiste 9,9 gegen 11,3; 1.038 s.** Staerkster Tor-1-Befund der Generation (b02: 209:161 nach 185 Paaren), Fruehstopp unter 150 Paaren. **Replikation Seed 20261013 (2026-09-06 09:23-09:58, exklusiv, `..._noknob_s13.json`): 112:78 nach 95 Paaren, erneut SPRT-ENTSCHEID fuer v24-b05, McNemar p 0,021, Diff +0,36 [+0,08, +0,64], Punkte 48,8 gegen 43,6, Strafleiste 10,4 gegen 10,6; 2.083 s. Gepoolt 178:112 aus 145 Paaren, zwei unabhaengige Seeds -- Champion-Strenge OHNE Knopf erfuellt.** Elo-Kanten `v24-b05` gegen `v23-b01_brierbest`. **Tor 2a MIT Knopf (04:18, `tor2a_v24b05.json`): 0,4975 volle Spalten (KI +-0,068), Punkte 48,6, Zeilen 0,170, Strafleiste 5,9** gegen Bezug b01 + K3-P 0,555 (Punktschaetzer darunter, KI schliesst ein); Knopf-Wirkung nur +0,015 (0,4825 -> 0,4975) gegen +0,12 bei b04, +0,095 bei b02, -0,075 bei v24-b01. **Tor 1 MIT Knopf (05:28, beide Seiten Champion-Spec, Seed 20261012, `..._s12.json`): 219:181 nach 200 Paaren, KEIN SPRT-Entscheid (LLR +1,31, Deckel), McNemar p 0,067, Diff +0,19 [-0,00, +0,38], Punkte 45,0 gegen 42,9, Strafleiste 10,8 gegen 11,2; 4.178 s** -- n >= 150, keine Replikation in der Kette. Mit Knopf also kein Beleg (wie b04 218:182 / 356:314), ohne Knopf 66:34 SPRT: die Knopf-Fassung schwaecht b05 wie b01 (dort 216:184 ohne, 83:107 mit). Elo-Knoten `v24-b05_k3p10` gegen `v23-b01_k3p10`. **Tor 2b (05:54, `paired_arena_env_v24b05_vs_b01_{first,second}_s14.json`, beide Seiten Champion-Spec, Seed 20261014, je 80): Siege 48:32 (b05 auf Brett 0) und 50:30 (b05 auf Brett 1), zusammen 98:62; volle Spalten b05 0,650 / 0,557 gegen b01 0,500 / 0,570 (SE 0,07-0,09; Brett 0 klar darueber, Brett 1 gleichauf innerhalb der SE; gepoolt 0,60 gegen 0,54), Punkte 46,1 / 47,0 gegen 42,9 / 41,3, Strafleiste 11,6 / 10,6 gegen 10,7 / 11,8, Kuppel-Bonus 3,8 / 3,7 gegen 3,5 / 4,1 (`points_v24b05_vs_b01_s14.json`), lange Reihen begonnen/vollendet 4,20/2,64 und 4,04/2,54 gegen 4,38/2,79 und 4,51/2,72 -> NICHT GEFALLEN (gepoolt darueber, keine Richtung signifikant darunter).** **Abnahme komplett (05:54).** Bilanz b05: Tor 2a ohne Knopf 0,4825 und mit Knopf 0,4975 (beide unter Bezug, KI schliesst ein); Tor 1 ohne Knopf 66:34 SPRT GENOMMEN (50 Paare, kein zweiter Seed), mit Knopf 219:181 ohne Entscheid; Tor 2b gehalten mit 98:62 -- der einzige Arm, der Tor 1 (ohne Knopf) nimmt UND Tor 2b haelt |
| `v24-b06` (b02-Rezept lambda 0,7 auf Sicht 744; Nutzer 2026-09-06 11:55 "starte A und B": Rueckfall-Kandidat fuer einen 744er-Champion) | 2026-09-06 11:47-13:07, 4.845 s (`--fast-loader`, Datenaufbau 82 s), 4,87 Mio Samples, `_brierbest` Epoche 4 (val_brier 0.1926); Brier-Verlauf 0,1932 / 0,1928 / 0,1926 / 0,1926 / 0,1926 / 0,1930 / 0,1928 / 0,1930 / 0,1930 / 0,1928 / 0,1931 / 0,1930 -- Minimum frueh, danach flach wie bei allen Armen; Manifest `manifest_train_v24-b06_20260906_114705.json` (traegt `fast_loader` und `laufzeit.lader`) | -- | -- | -- | Abnahme laeuft seit 13:22 (`night_v24_b06_chain.sh`, 744er-Basis-Wheel mit K3-F Default aus). **Tor 2a OHNE Knopf (13:50, `tor2a_v24b06nk.json`): 0,475 volle Spalten (KI +-0,067), Punkte 46,2, Zeilen 0,195, Strafleiste 5,9** gegen b01 ohne Knopf 0,510 (KI schliesst ein) -- gegen das 714er-b02 (0,430) spaltenreicher |
| `v24-b03` (Seeding-Schwarm, INPUT_SIZE 714, Nutzer: "lass b03 auf 714") | Kuratierung 1.500 (0 Abweichungen), Schwarm 6.000 in 8.908 s (1,485 s je Partie), Monolith gebaut. Erster Lauf 2026-09-05 12:22 durch Maschinen-Neustart in Epoche 12 verloren (Chronik 16:04). **Neu-Training 2026-09-06 00:27-01:56 mit `--fast-loader`: 5.344 s, 12 Epochen, 5,33 Mio Samples, Datenaufbau 68 s, `_brierbest` Epoche 4 (val_brier 0,1868 -- zifferngleich mit dem verlorenen Lauf), Brier-Verlauf 0,1876 / 0,1875 / 0,1874 / 0,1868 / 0,1871 / 0,1872 / 0,1876 / 0,1876 / 0,1874 / 0,1875 / 0,1873 / 0,1873; Manifest `..._20260906_002718.json` (Lader als Nachtrag von Hand, Chronik 00:46)** | -- | -- | -- | Abnahme unter dem 714er-Champion-Artefakt-Wheel (`night_v24_b03_acceptance_714.sh`, venv_measure714, byte-identisch zum Wheel der b01/b02-Abnahmen) laeuft seit 2026-09-06 05:55. **Tor 2a OHNE Knopf (06:21, `tor2a_v24b03nk.json`): 0,490 volle Spalten (KI +-0,068), Punkte 46,8, Zeilen 0,193, Strafleiste 5,5** gegen b01 ohne Knopf 0,510 (Punktschaetzer darunter, KI schliesst ein; b05 0,4825, b02 0,430, b04 0,4125, v24-b01 0,518). **Tor 1 OHNE Knopf (07:29, beide Seiten `k3v_off`, Seed 20261016, `paired_gating_result_v24-b03_vs_v23-b01_noknob_s16.json`): 215:185 nach 200 Paaren, KEIN SPRT-Entscheid (LLR +0,07, Deckel), McNemar p 0,155, Diff +0,15 [-0,04, +0,34], Punkte 46,8 gegen 44,2, Strafleiste 9,5 gegen 11,1; 4.095 s** -- wie v24-b01 (216:184) und b04 (218:182): kein Beleg. Elo-Kante `v24-b03` gegen `v23-b01_brierbest` (Kontrakt efd564d87bac2722, 714er Artefakt-Wheel). **Tor 2a MIT Knopf (07:53, `tor2a_v24b03.json`): 0,5025 volle Spalten (KI +-0,068), Punkte 48,9, Zeilen 0,218, Strafleiste 5,9** gegen Bezug 0,555 (KI schliesst ein); Knopf-Wirkung +0,0125 (wie b05 +0,015). **Tor 1 MIT Knopf (08:13, beide Seiten Champion-Spec, Seed 20261012, `..._s12.json`): 75:45 nach 60 Paaren, SPRT-ENTSCHEID fuer v24-b03 (LLR +3,28), McNemar p 0,008, Diff +0,50 [+0,17, +0,83], Punkte 47,9 gegen 42,0, Strafleiste 9,7 gegen 11,0; 1.215 s.** Das Gegenbild zu b05 (ohne Knopf 66:34, mit Knopf kein Beleg): b03 ohne Knopf 215:185 ohne Beleg, MIT Knopf genommen. Fruehstopp < 150; **Replikation Seed 20261013 (08:54, `..._s13.json`): 139:101 nach 120 Paaren, erneut SPRT-ENTSCHEID fuer v24-b03, McNemar p 0,016, Diff +0,32 [+0,08, +0,56], Punkte 49,5 gegen 44,5, Strafleiste 9,9 gegen 11,9; 2.464 s. Gepoolt 214:146 aus 180 Paaren, zwei unabhaengige Seeds -- Champion-Strenge mit Knopf erfuellt (wie b02 192:128).** Elo-Knoten `v24-b03_k3p10` gegen `v23-b01_k3p10`. **Tor 2b (09:20, `paired_arena_env_v24b03_vs_b01_{first,second}_s14.json`, beide Seiten Champion-Spec, Seed 20261014, je 80, 714er Artefakt-Wheel): Siege 46:34 (b03 auf Brett 0) und 37:43 (b03 auf Brett 1), zusammen 83:77; volle Spalten b03 0,675 / 0,628 gegen b01 0,575 / 0,692 (SE 0,08-0,09; eine Richtung darueber, eine darunter, gepoolt 0,65 gegen 0,63), Punkte 48,5 / 47,2 gegen 45,2 / 47,1, Strafleiste 9,3 / 10,3 gegen 11,0 / 10,0, Kuppel-Bonus 4,15 / 4,16 gegen 3,48 / 3,62 (hoechster Wert aller Arme; `points_v24b03_vs_b01_s14.json`), lange Reihen begonnen/vollendet 4,35/2,84 und 4,36/2,79 gegen 4,33/2,71 und 4,28/2,82 -> Spalten GLEICHAUF (nicht in beiden Richtungen darunter): NICHT GEFALLEN, aber auch kein Gewinn.** **Abnahme komplett (09:20).** Bilanz b03: Tor 2a ohne Knopf 0,490 und mit Knopf 0,5025 (KI schliesst Bezug ein); Tor 1 ohne Knopf 215:185 ohne Beleg, MIT Knopf 75:45 + 139:101 SPRT (zwei Seeds, Champion-Strenge); Tor 2b Spalten gleichauf, Siege 83:77, Kuppel-Bonus +0,6 |

Beobachtung ohne Verdikt: das Material ist spaltenreich (0,61 @100 im
Self-Play), das daraus warm gestartete Netz spielt am Instrument @400 mit
Knopf spaltenaermer (0,44) als sein Lehrer ohne Knopf (0,515); `_brierbest`
fiel auf Epoche 2, die Val-Kennzahlen liegen auf einem neuen Val-Pool.
Ursachenanalyse nach b02/b03 (Generatorwahl-Regel), nicht je Arm.

### par.9c VORLAGE GENERATORWAHL v24 (2026-09-06, 09:24; alle fuenf Arme abgenommen; ENTSCHEID OFFEN beim Nutzer)

Regel: `docs/generation_loop.md` "Generatorwahl unter Armen" (Staerke schliesst
aus, Spaltenprofil entscheidet, sonst Amtsinhaber) und "Richtung je Generation"
(spalten- UND siegverstaerkend). Amtsinhaber `v23-b01_brierbest` (Champion-Knopf
K3-P C 1,0 = `v23-b01_k3p10`, Elo 1292). Alle Zahlen aus der par.9-Tabelle.

| Arm | Tor 2a ohne Knopf (Bezug 0,510) | Tor 2a mit Knopf (Bezug 0,555) | Tor 1 ohne Knopf | Tor 1 mit Knopf | Tor 2b Siege | Tor 2b Spalten Arm gegen b01 (Brett 0 / Brett 1) | Kuppel-Bonus Arm gegen b01 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| v24-b01 | 0,518 | 0,4425 gerissen | 216:184 kein Beleg | 83:107 (2 Seeds, H0) | 93:67 | 0,696 / 0,600 gegen 0,494 / 0,575 GEHALTEN | 3,8 gegen 3,6 |
| v24-b02 (lambda 0,7) | 0,430 | 0,525 (KI ein) | **209:161 SPRT** (185 Paare) | **101:69 + 91:59 SPRT** (2 Seeds) | 87:73 | 0,550 / 0,475 gegen 0,688 / 0,562 GERISSEN | 4,0 / 3,5 gegen 4,1 / 3,8 |
| v24-b03 (Seeding, 714) | 0,490 (KI ein) | 0,5025 (KI ein) | 215:185 kein Beleg | **75:45 + 139:101 SPRT** (2 Seeds) | 83:77 | 0,675 / 0,628 gegen 0,575 / 0,692 GLEICHAUF | **4,2 / 4,2 gegen 3,5 / 3,6** |
| v24-b04 (Sicht 744) | 0,4125 gerissen | 0,5325 (KI ein) | 218:182 kein Beleg | 135:135 H0 + 221:179 kein Beleg | 92:68 | 0,684 / 0,738 gegen 0,608 / 0,525 GEHALTEN | 3,9 / 4,3 gegen 3,6 / 3,9 |
| v24-b05 (b04 + Ueberraschung) | 0,4825 (KI ein) | 0,4975 (KI ein) | **66:34 + 112:78 SPRT** (2 Seeds, gepoolt 178:112) | 219:181 kein Beleg | 98:62 | 0,650 / 0,557 gegen 0,500 / 0,570 GEHALTEN (Brett 1 gleichauf) | 3,8 / 3,7 gegen 3,5 / 4,1 |

**Regel Schritt 1 (Staerke schliesst aus):** kein Arm verliert signifikant gegen
den Amtsinhaber (b01 mit Knopf 83:107 ist H0, p 0,31 / 0,33, kein Verlust-Beleg).
Umgekehrt BELEGT staerker (Tor 1, SPRT): **b02** (beide Fassungen, je zwei Seeds),
**b03** (mit Knopf, zwei Seeds), **b05** (ohne Knopf, ein Seed; Champion-Strenge
verlangt den zweiten, er laeuft). b01 und b04 haben in keiner Fassung einen Beleg.

**Regel Schritt 2 (Spaltenprofil, Punktschaetzer Tor 2a):** mit Knopf b04 0,5325 >
b02 0,525 > b03 0,5025 > b05 0,4975 > b01 0,4425, alle unter dem Amtsinhaber
0,555, die ersten vier innerhalb einer Block-SE (rund 0,035); ohne Knopf b01 0,518 >
b03 0,490 > b05 0,4825 > b02 0,430 > b04 0,4125 (Bezug 0,510). Im Spielbetrieb
(Tor 2b, beide Seiten Champion-Spec): b01, b04, b05 halten, b03 gleichauf, b02
reisst in beiden Richtungen.

**Regel Schritt 3 (unter Block-SE: Amtsinhaber):** mechanisch angewandt bliebe
v23-b01 Generator, weil kein Arm ihn am Instrument uebertrifft. Das widerspricht
dem Zweck der Ratsche (drei Arme sind belegt staerker); die Regel wurde fuer die
Wahl UNTER Armen geschrieben, nicht gegen den Amtsinhaber. Vorlage deshalb als
Gabelung an der Knopf-Frage, die der Nutzer ohnehin entscheiden muss:

**Die Knopf-Wechselwirkung ist der Kern.** Mit K3-P auf beiden Seiten (so wurde
v24 erzeugt, par.6b') halten nur b02 und b03 ihren Vorsprung; b01 kippt, b04 und
b05 verlieren den Beleg. Ohne Knopf nehmen b02 und b05, b03 nicht. Fuer die
v25-Erzeugung heisst das:

- **Faehrt die Erzeugung MIT K3-P (wie v24): Vorschlag b03.** Belegt staerker
  mit Knopf (214:146, zwei Seeds), Spalten gleichauf mit dem Amtsinhaber (2b) und
  innerhalb der KI am Instrument (0,5025 gegen 0,555), hoechster Kuppel-Bonus der
  Generation (4,2 gegen 3,5-3,6: der Seeding-Schwarm hat Plattenwahl gesaet).
  Nicht spaltenverstaerkend, aber nicht spaltenaermer. Zu beachten: b03 ist ein
  714er-Netz, die Erzeugung liefe auf dem 714er-Artefakt-Wheel; das v25-Fenster
  laesst sich trotzdem 744 kodieren (die b04-Kette hat 744er-Bloecke aus denselben
  Records gebaut, Chronik 2026-09-05 16:04 (c)). Alternative in dieser Gabel:
  b02 (staerkster Beleg, 4 Seeds), aber spaltenaermer in 2a ohne Knopf UND 2b in
  beiden Richtungen -- gegen die Richtungsregel.
- **Faehrt die Erzeugung OHNE K3-P: Vorschlag b05.** Belegt staerker ohne Knopf
  (66:34 und 112:78, zwei Seeds, Champion-Strenge erfuellt), Tor 2b
  gehalten (98:62, gepoolt 0,60 gegen 0,54), Instrument innerhalb der KI. Der
  einzige Arm, der Tor 1 UND 2b nimmt -- aber nur in der Knopf-losen Fassung.
- **Nicht vorgeschlagen:** b04 (kein Tor-1-Beleg in beiden Fassungen, trotz
  bestem Instrumentwert mit Knopf), b01 (kippt mit Knopf), Amtsinhaber
  (Schritt-3-Mechanik gegen drei belegte Ratschen).

**Offene lange Reihen (par.8.13) in den 2b-Arenen:** je Seite 4,0-4,5 begonnen,
2,5-2,9 vollendet, bei allen Armen gleich; b03 und b04 vollenden am meisten
(2,8-2,9), b05 am wenigsten (2,5-2,6). Kein Arm loest den Engpass; K3-F ist
dafuer gebaut (par.8.14 der Einhuellenden), Messung am Siegernetz offen.

**Nutzer-Entscheid (09:40): "744er bleibt fix drinnen. ist die korrektere
variante."** Die Sicht 744 ist gesetzt; die Gabelung reduziert sich damit auf
die 744er-Arme b04 und b05 (b03 scheidet als 714er-Netz aus, b01/b02 ebenso).
Nachgeprueft auf Nutzer-Frage ("konnte das 744er netz ueberhaupt mit den
vorhandenen self plays bedient werden?"): die 30 Zusatzwerte rechnet der
Python-Encoder (`engine/py/neural_net.py:296-341`) aus dem State-Dict jedes
Records (`dome_stack_top_type`, `type` der Auslage-Platten, `floor`-Farben,
`phantom_count`); in vier Dateien aller Fensterklassen (policy, hv2 vom
2026-08-25, seedvalue, value-argmax; 1.269-1.784 Schritte je Datei) fehlt
KEIN Schluessel, und die Werte streuen (Stapel-Rueckseite wild/special/leer
rund 40/35/25 %, 46-170 Reihen mit Phantomen je Datei, 877-995 Auslage-
Platten mit Spezialfeld). Die 744er-Bloecke wurden aus denselben Records neu
gebaut (2.945 Bloecke, Chronik 2026-09-05 16:04) -- nichts fiel still auf 0.

**ENTSCHIEDEN (Nutzer 2026-09-06, 11:40): Generator v25 = b05, Erzeugung OHNE K3-P**
(registriert in `PREREG_v25_window.md` par.4). **Champion-Frage (Nutzer 11:45: "self plays
eigentlich nur mit champion"): Kante in SPIELKONFIGURATION, b05 `k3v_off` gegen
v23-b01 Champion-Spec, Seed 20261012 (12:17, `paired_gating_result_v24-b05nk_vs_v23-b01_k3p10_s12.json`):
58:72 nach 65 Paaren, SPRT H0 (LLR -3,82), McNemar p 0,31, Diff -0,22 [-0,57, +0,14],
Punkte 42,9 gegen 44,8; 1.804 s. **Seed 20261013 (13:20, `..._s13.json`): 144:146 nach 145 Paaren, H0 (LLR -3,00), McNemar p 1,0, Diff -0,01 [-0,22, +0,19], Punkte 48,7 gegen 48,6; 3.816 s. Gepoolt 202:218 aus 210 Paaren: b05 in Spielkonfiguration GLEICHAUF mit dem Champion, kein Champion-Beleg.** Rueckfall B: v24-b06 (b02-Rezept auf 744) trainiert 11:47-13:07, Abnahme laeuft seit 13:21; wird b06 Champion-Kandidat (Tor 1 mit Knopf, zwei Seeds), ist die Kante b06 gegen den Champion dieselbe Messung wie sein Tor 1 mit Knopf.**

**Was der Entscheid mitentscheidet:** (1) Knopf in der v25-Erzeugung ja/nein
(par.6b'); (2) Generator; (3) ob der v24-Sieger den Champion-Knoten herausfordert
(Kante gegen `v23-b01_k3p10` = Tor 1 mit Knopf: b02 192:128 und b03 214:146
liegen vor, `/mosaic-champion-promotion`); (4) Reihenfolge der Knopf-Messungen
K3-P2 / K3-F am Siegernetz (par.8.11/8.14).

### par.9a Widerspruch der Instrumente bei v24-b01 (11:05, offen)

Tor 1 (`paired_gating`, 190 Partien): 83:107, Punkte 44,9/45,8 gegen 46,0/48,2.
Tor 2b (`paired_arena_env_ab --log-games`, 160 Partien, dieselbe Spec beide
Seiten): 93:67, Punkte 48,4/45,5 gegen 41,9/44,6, Spalten +0,20 / +0,03.
Differenz der Siegquoten 14 Prozentpunkte (43,7 gegen 58,1 %), naiv 2,7 SE;
gegen die gemessene Seed-Streuung des Projekts (5,75 Prozentpunkte bei n = 400
fuer identische Konfiguration, `docs/working_rules.md`) bei n rund 175 je
Instrument aber innerhalb dessen, was zwei Seeds auseinanderbringen. Gepoolt
176:174. Spec-Weitergabe beider Werkzeuge am Code geprueft: beide reichen
`spec_a`/`spec_b` an `net_vs_net_arena_match` (paired_gating.py:249/254,
paired_arena_arm_worker.py:122-129); Unterschied: der Arena-Worker setzt
zusaetzlich `MOSAIC_ENVELOPE_SEARCH_C=1.0` prozessweit. Lesart: v24-b01 ist
gegen b01 NICHT belegt besser (Tor 1 gerissen als Ratsche) und NICHT belegt
schwaecher; das argmax-Instrument (0,44) und die Arena-Spalten (0,60-0,70)
gehen auseinander. Naechste Messungen (CPU frei, sobald die Ketten es
zulassen): argmax v24-b01 OHNE Knopf (trennt Netz von Knopf-Wechselwirkung),
Huellen-Sonde auf `tor2a-v24b01`, hv2-Fenster-Kennzahl, v23-Sockel als
Vergleich fuer die Policy-Klasse.

### par.9b Ursachenanalyse v24-b01 (11:55): das Netz hat nicht verlernt, der Knopf kippt

| Messung (argmax @400, 200 Partien, Seed 20260931) | volle Spalten (KI) | Punkte | volle Reihen |
| --- | --- | --- | --- |
| b01 ohne Knopf (Kontrolle K3 S 0,1) | 0,510 (+-0,065) | 46,5 | 0,150 |
| b01 + K3-P C 1,0 | **0,555** (+-0,067) | 47,7 | 0,193 |
| **v24-b01 ohne Knopf** (`tor2a_v24b01nk.json`) | **0,518** (+-0,072) | 46,8 | 0,200 |
| v24-b01 + K3-P C 1,0 (`tor2a_v24b01.json`) | **0,443** (+-0,063) | 45,7 | 0,175 |

Huellen-Sonde des v24-b01-Korpus mit Knopf (`triangle_hull_coverage_tor2a-v24b01.json`):
Huelle am Ende 0,693, Halbzeit 0,446, aussen 2,18 -- identisch mit b01 + Knopf
(0,703 / 0,444 / 2,15). Die Huelle wird also gleich gefuellt, nur die
VOLLENDUNG fehlt.

**Lesart:** v24-b01 spielt ohne Knopf spaltengleich zu b01 (+0,008, weit
innerhalb der KI). Der Knopf, der b01 um +0,045 hebt, senkt v24-b01 um
-0,075: die Wechselwirkung Knopf x Netz hat das Vorzeichen gewechselt. Passende
Erklaerung (Hypothese, nicht belegt): das v24-Material ist mit Knopf erzeugt,
das Netz hat die Huellen-Praeferenz in Policy und Value bereits aufgenommen;
der Knopf obendrauf verschiebt die Blaetter ein zweites Mal in dieselbe
Richtung, die Suche verteilt Steine in der Huelle statt Spalten zu vollenden
(dasselbe Muster wie K3-R in 8.9a: Huelle rauf, Vollendung runter).

**Folgen fuer die Messungen dieser Generation:** Tor 1 und Tor 2a wurden mit
Knopf auf beiden Seiten gefahren (par.6e-Berichtigung vom 2026-09-04) und
messen damit auch die Knopf-Wechselwirkung, nicht nur das Netz. Nachzuholen
(eingetaktet): **Tor 1 OHNE Knopf** (beide Seiten `k3v_off.spec.json`) und
das argmax-Instrument fuer v24-b01 bei C 0,5. Fuer b02/b03/b04 gilt: Tor 2a
und Tor 1 beidseitig OHNE Knopf zusaetzlich fahren, sonst ist "schwaecher"
nicht vom "anders geeicht" zu trennen.

**Gegenmassnahmen (Vorschlag, Nutzer-Entscheid):**
1. Knopf-Dosis je Generation neu eichen statt fest 1,0: fuer ein Netz, das
   auf Knopf-Material trainiert ist, C am argmax-Instrument ueber 0 / 0,5 /
   1,0 messen und den Betriebspunkt waehlen (billig: 3 x 27 min).
2. Material weiter MIT Knopf erzeugen (das ist die Spaltenquelle: 0,75 in der
   argmax-Klasse), den Knopf im SPIELBETRIEB des trainierten Netzes aber als
   abklingende Dosis fuehren (Generation n: C_n <= C_(n-1)), analog zum
   Rundenprofil.
3. v25-Zuschnitt unveraendert (hv2 sinkt auf 18 %); der Materialmix ist nach
   dieser Analyse NICHT die Ursache (Sockel v24 besser als v23, argmax-Klasse
   spaltenreich, ohne Knopf kein Rueckschritt).

**Nachtrag par.9b, 13:47 -- Tor 1 OHNE Knopf (beide Seiten `k3v_off.spec.json`,
Seed 20261015, `paired_gating_result_v24-b01_vs_v23-b01_noknob_s15.json`):
v24-b01 216:184 nach 200 Paaren (harter Deckel, kein SPRT-Entscheid, LLR
+0,90), McNemar p 0,105, gepaarte Differenz +0,16 [-0,02, +0,34], Punkte 45,9
gegen 43,1, Strafleiste 10,2 gegen 11,1; 6.422 s.** Zusammen mit den Knopf-
Kanten (83:107): ohne Knopf mindestens gleichauf, mit Knopf klar dahinter --
die Knopf-Wechselwirkung kostet v24-b01 rund 15 Prozentpunkte Siegquote gegen
denselben Gegner. Die Ratsche (signifikant besser) ist NICHT genommen; die
Groessenordnung entspricht der v23-Champion-Kante b01 gegen v21 (214:186).
Elo-Register: die beiden Knopf-Kanten von heute Morgen sind auf die Knoten
`v24-b01_k3p10` / `v23-b01_k3p10` umbenannt (Knopf = eigener Spieler,
Praezedenz Champion-Knoten), die knopflose Kante steht unter `v24-b01` /
`v23-b01_brierbest`.

**Nachtrag par.9b, 21:30 -- Knopf-Dosis v24-b01 bei C 0,5 (`tor2a_v24b01c05.json`, argmax @400,
200 Partien, Seed 20260931, Lauf 21:01-21:30): volle Spalten 0,450 (KI +-0,063), Punkte 46,4,
Zeilen 0,195, Strafleiste 5,9.** Damit die Dosisreihe fuer v24-b01: C 0 -> 0,518, C 0,5 -> 0,450,
C 1,0 -> 0,443. Die halbe Dosis kostet dieselben rund 0,07 Spalten wie die volle -- kein
Dosis-Effekt, sondern ein Schalter: sobald der Knopf an ist, verteilt die Suche bei diesem Netz
Steine in der Huelle statt Spalten zu vollenden. Gegenmassnahme 1 (Dosis je Generation neu
eichen) traegt fuer v24-b01 also NICHT; offen bleibt Gegenmassnahme 2 (Material mit Knopf,
Spielbetrieb ohne oder mit anderem Knopf) und die Frage, warum b02 anders reagiert (+0,095).
