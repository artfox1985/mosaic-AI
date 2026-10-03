<!-- STATUS: OFFEN | Frage: Wie wird das v35-Fenster erzeugt und zugeschnitten (Schwarm sofort, Sockel nach dem asymmetrischen Bau), und traegt ein Arm? | Beleg: angelegt 2026-10-02 nach der Promotion von v34-b01. Generator v34-b01, Runde 5 per Netz mit 400 R5-Sims, Spiegelknopf an (par.5). Schwarm (value-deviate, value-excursion je 4.000) startet von selbst nach der Promotionskette (par.6/par.7, Nutzer-Freigabe 2026-10-02); Sockel offen bis PREREG_asymmetric_selfplay.md. -->

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
