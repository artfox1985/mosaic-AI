<!-- STATUS: OFFEN | Frage: Wie wird das v24-Trainingsfenster zugeschnitten? | Beleg: ZUSCHNITT VOM NUTZER FESTGELEGT (2026-09-01), nichts erzeugt. Form wie v23 (29.450 Partien), hv2-Anteil UNVERAENDERT, neu nur 12.000 Partien von `v23-b01` (par.2). Generator b01 STEHT (par.4; Gleichstandsregel war nicht vorab registriert). **Erzeugungsrezept seit 2026-09-01 VOLLSTAENDIG (par.6):** 100 Sims, Zuschnitt D, `--per-file 10`, Stack-Draw-Env, Seeds, Traeger-Manifest 580 Eintraege, Tor-0-Schwelle 1.500 Seiten, Tore mit Bezugswerten. Gemessene Kosten 11,9 h. -->

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
| 1 | `tools/paired_gating.py` gegen `v23-b01_brierbest` @400, Champion-Strenge (n >= 150 Paare oder Replikation mit eigenem Seed) | -- |
| 2a | argmax-Instrument @400, 200 Partien (`self_play.py --deterministic --no-root-noise`) | b01 **0,5150** (`evaluations/artifacts/tor2a_v23b01.json`) |
| 2b | gepaarte Arena gegen b01 mit `--log-games`, `tools/probes/arena_column_probe.py` (Anzahl voller Spalten aus der Brettgeometrie) | b01-Seite DERSELBEN Arena; zum Vergleich b01 gegen b05: 0,6456 |
| Champion-Kante | gegen `v21_2d_brierbest` @400, berichten, Promotion nur nach `promotion_checklist.md` | 219:181 war die v23-Kante |

Jeder weitere Arm dieser Generation bekommt VOR seinem Ausscheiden als
Generator sein Spaltenprofil am argmax-Instrument (Lehre aus par.4).

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
