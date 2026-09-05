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
| `v24-b02` (lambda 0,7) | 08:58-12:21, 12.166 s (Datenaufbau 71 s), `_brierbest` Epoche 2 (val_brier 0,1923), `_best` Epoche 1; Val-R2 Value 0,47 (anderes Ziel, nicht mit b01 vergleichbar), Plateau-Muster wie b01 | -- | -- | -- | Abnahme wartet auf CPU (Reihenfolge: Gating b01 ohne Knopf, cargo/Wheel, b04-Bloecke) |
| `v24-b03` (Seeding-Schwarm) | Kuratierung 1.500 (0 Abweichungen), Schwarm 6.000 in 8.908 s (1,485 s je Partie), Monolith gebaut | -- | -- | -- | wartet auf b02 |

Beobachtung ohne Verdikt: das Material ist spaltenreich (0,61 @100 im
Self-Play), das daraus warm gestartete Netz spielt am Instrument @400 mit
Knopf spaltenaermer (0,44) als sein Lehrer ohne Knopf (0,515); `_brierbest`
fiel auf Epoche 2, die Val-Kennzahlen liegen auf einem neuen Val-Pool.
Ursachenanalyse nach b02/b03 (Generatorwahl-Regel), nicht je Arm.

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
