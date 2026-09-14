<!-- STATUS: OFFEN | Frage: Wie wird das v29-Trainingsfenster zugeschnitten -- zweiter Zyklus nach dem Einfrieren, Generator v28-b02, Pflichtarm b01? | Beleg: par.9 -- Erzeugung durch (1.201 Dateien, 12,8 h), Tor 2a HAELT (0,843 gegen 0,816, Reihe ueber fuenf Generationen monoton), Fenster 2.947 Dateien, Training b01 1,55 h. **Tor 1 BEIDE SEEDS H0** (87:93 und 69:81, je SPRT-Abbruch): der Pflichtarm traegt nicht, kein Champion-Wechsel. ACHTUNG: b01 war KEIN reiner Materialschritt -- der v29-Korpus bringt drei Aenderungen mit (Startkuppel-Variation 0,15, Startkuppel per Suche, Stapelzug-Knopf, Eingang 744 -> 755), der Nullbefund kann auch Umstellungskosten sein. Offen: b02, b03, Sockel-Sims. -->

# PREREG v29: Fensterzuschnitt fuer den zweiten Zyklus nach dem Einfrieren

**Angelegt 2026-09-11, 17:35** auf Nutzer-Auftrag ("schreib schon mal das v29 fenster
prereg"), waehrend Tor 1 `v28-b02` gegen `v28-b01` noch laeuft. **Vorlage ist
`PREREG_v28_window.md`** (Zuschnitt par.1, G-2-Entscheid par.2, Generator par.3, Befehle
par.5, Arme par.6). Bestandszahlen sind am 2026-09-11 geprueft, alles Weitere ist als
Herleitung oder als offener Entscheid markiert.

**Nutzer-Stand (2026-09-11):** *"nach v28 haben wir die meisten preregs dann erledigt. ich
denk nun haben wir einen recht stabilen alphazero zyklus aus selfplay, training, arena und
wieder von vorne."* v29 ist deshalb als ZYKLUSDURCHLAUF geschnitten, nicht als
Experimentgeneration: ein Pflichtarm mit unveraendertem Rezept, kein zweiter Arm ohne
eigenen Nutzer-Entscheid, und das Begleitprogramm (par.7) laeuft in den CPU-freien Fenstern
mit. Ob v29 die letzte Generation ist oder v30 folgt, ist offen (par.8).

## par.1 ZUSCHNITT (hergeleitet aus der Rotationsregel, Bestandszahlen geprueft 2026-09-11)

G = v29-Erzeugung durch den v28-Generator (par.3), Dateien `selfplay_v28-bXX-*`; G-1 =
`v27-b01` (400 / 400 / 401 Dateien: `selfplay_v27-b01-policy_*`, `-value-tempc_*`,
`-value-excursion_*`); G-2 = `v26-b01` (400 / 400 / 401). **`v25-b01` faellt aus der
Rotation** (seine 400 Policy- und 145 Ausflug-Dateien des v28-Fensters werden nicht mehr
gelesen; Loeschung erst im Generationswechsel und nur mit Freigabe).

**Sockel (Policy-Klasse, Traeger)**

| Posten | Quelle | Dateien | Partien |
| --- | --- | --- | --- |
| Sockel NEU | v29-Erzeugung, policy-aktiv | 400 | 4.000 |
| aus G-1 | 135 der 400 `selfplay_v27-b01-policy_*` (seed-bestimmt) | 135 | 1.350 |
| aus G-2 | 45 der 400 `selfplay_v26-b01-policy_*` (seed-bestimmt) | 45 | 450 |
| **Summe** | | **580** | **5.800** |

**Schwarm (Value-Klasse, policy-maskiert)**

| Posten | Quelle | Dateien | Partien |
| --- | --- | --- | --- |
| Schwarm NEU | v29, temperiert plus Ausfluege | rund 801 | rund 8.000 |
| Schwarm G-1, Haelfte a | alle 400 `selfplay_v27-b01-value-tempc_*` | 400 | 4.000 |
| Schwarm G-1, Haelfte b | alle 401 `selfplay_v27-b01-value-excursion_*` | 401 | 4.010 |
| Sockel-Rest G-1 | die 265 uebrigen `selfplay_v27-b01-policy_*` | 265 | 2.650 |
| Sockel-Rest G-2 | 355 der `selfplay_v26-b01-policy_*` | 355 | 3.550 |
| Schwarm G-2 | 145 der `selfplay_v26-b01-value-<Haelfte>_*` (par.2) | 145 | 1.450 |
| **Summe** | | **rund 2.367** | **rund 23.660** |

**Fenster gesamt rund 2.947 Dateien** (v27 und v28: 2.947). Die Ausflug-Klassen liefern 400
oder 401 Dateien; nicht ausgeglichen.

**SEED der seedbestimmten Auswahlen UND des Trainings: 20260941** (Regel seit 2026-09-10,
`docs/generation_loop.md`: je Generation neu im Vierer-Schritt, alle Arme einer Generation
gleich; v27 hatte 20260933, v28 20260937). **Val-Pool `^selfplay_v28-`.**

**Was am Fenster NEU ist, ohne Zuschnitt-Entscheid:** wenn der Generator `v28-b02` ist
(par.3), tragen ALLE drei neuen Klassen das Stapelwissen im NETZ, nicht nur im Record. Die
elf Merkmale (Index 744..754) lernen dann auf G plus G-1 (beide mit `dome_pool_view`, 2.402
von 2.947 Dateien, 82 Prozent) statt auf 40 Prozent wie bei `v28-b02`; die v26-Dateien
liefern Nullen. Das ist der eigentliche Grund, warum ein reiner Materialschritt in v29 mehr
sein kann als in v28, und er ist NICHT von einem Rezeptwechsel zu trennen; registriert als
Erwartung, nicht als Arm.

## par.2 WELCHE G-2-HAELFTE -- ENTSCHIEDEN 2026-09-13 (Nutzer)

`v26-b01` rutscht auf G-2; der Posten von 145 Dateien traegt EINE Haelfte (v26-Prereg par.6:
kein Split). v27 nahm die temperierte Haelfte (Rolle "Abdeckung"), v28 die Ausflug-Haelfte
(auf den Zahlen: spaltenreichste Klasse, doppelte Recordzahl je Datei). **Vorschlag: wieder
die Ausflug-Haelfte** (`selfplay_v26-b01-value-excursion_*`, 401 Dateien, 145 seed-gezogen
mit 20260941), aus denselben Gruenden wie in v28 und damit die beiden Fenster nach dem
Einfrieren dieselbe Regel tragen. Die temperierte v26-Haelfte rotiert dann ersatzlos hinaus.
**ENTSCHIEDEN 2026-09-13, 13:20 (Nutzer): "Nimm fuer die g-2 das selbe was wir auch bei v28
hatten. Da brauchen wir nichts aendern."** Also die AUSFLUG-Haelfte, wie vorgeschlagen:
`G2_SWARM_PATTERN="selfplay_v26-b01-value-excursion_*.pkl"`, 145 Dateien seed-gezogen mit
20260941. Geprueft: v28 fuhr `selfplay_v25-b01-value-excursion_*.pkl`
(`tools/night_v28_chain.sh` Z.21), die Regel ist also woertlich dieselbe, nur eine Generation
weiter. Die 401 Quelldateien liegen vollstaendig im Baum (beim Aufraeumen am 2026-09-13
bewusst NICHT angetastet, anders als die v25-Klassen). Die temperierte v26-Haelfte rotiert
ersatzlos hinaus.

## par.3 WER ERZEUGT (Regel fest, Name offen bis zur v28-Promotion)

Nach `docs/generation_loop.md` erzeugt der beste Stand der Vorgeneration mit Tor 1 und Tor 2
auf beiden Flaechen. Stand 2026-09-11, 20:30: `v28-b01` hat Tor 1 gegen `v27-b01` (166:124,
221:179; Elo 1447) und Tor 2b (1,030 gegen 0,884); `v28-b02` ist gegen `v28-b01` ein
Nullbefund (207:193, 209:191) und per Nutzer-Entscheid als korrektere Fassung der beste Stand. **Generator ist der Sieger der v28-Promotion**
(`docs/promotion_checklist.md`, Champion-2-Kante gegen das Artefakt `v26-b01`):

| Fall | Generator | Klassen | Merkmalsbreite des Generators |
| --- | --- | --- | --- |
| b02 besteht Tor 1 gegen b01 | `v28-b02` | `selfplay_v28-b02-policy_*`, `-value-tempc_*`, `-value-excursion_*` | 755 (sieht den Stapel) |
| b02 gleichauf mit b01 (EINGETRETEN 2026-09-11: 207:193, 209:191, beide Deckel) | `v28-b02` (Nutzer-Entscheid 2026-09-11: bei Gleichstand ist die Fassung mit dem volleren Informationsstand die richtige, `PREREG_v28_window.md` par.10) | `selfplay_v28-b02-*` | 755 |
| b02 negativ gegen b01 | `v28-b01` | `selfplay_v28-b01-*` | 744, unter dem 755er-Wheel gekuerzt (`net.rs:421`) |
| eine Ablation b03/b04 schlaegt den Sieger | der Ablationsarm | entsprechend | wie sein Rezept |

Spec: die Champion-Spec aus dem Artefakt des Generators (`models/frozen_champions/<name>/spec.json`;
seit v25 inhaltlich die v24-b07-Spec, `PREREG_v28_window.md` par.3). Wheel: das Variante-B-Wheel
(INPUT_SIZE 755, Kontrakt-Hash seit 2026-09-12 39648b95bbba1acf nach A10 des Code-Abschlusses, vorher
c65768636c0560a7; Wheel `mosaic_rust-0.1.0-cp314-cp314-win_amd64.whl`), Anker-Drift gruen (`anchor_drift_live_wheel_20260911_varB.json`).
**Die Engine ist dieselbe wie bei der v28-Erzeugung** bis auf den Merkmalsbauer (Rust statt
Python, bit-identisch, `PREREG_rust_data_layer.md` par.7); Records tragen `dome_pool_view`
seit dem v27-Wheel. Aendert sich vor dem Start noch etwas an der Engine (par.7 Punkt 3):
Anker-Drift wiederholen, hier eintragen.

## par.4 PFLICHTPRUEFUNGEN VOR DEM START (aus dem Generationswechsel und den Vorfaellen von v28)

1. **Maschine frei, Prozessliste leer** (nicht die Task-Meldungen), App offen, keine
   parallele Messung; die Claude-Partien der Parallelsitzung sind zulaessige Nebenlast
   (Nutzer 2026-09-10), die Laufzeit wird dann als gebremst markiert.
2. **Wheel installiert und im Manifest**: `python -c "import mosaic_rust as m; m.state_features_from_json"`
   vorhanden, Kontrakt-Hash im Manifest der ersten Klasse = 39648b95bbba1acf (seit A10, 2026-09-12).
3. **Spec-Datei liegt** (Artefakt-Spec des Generators), Golden-Probe des Generator-Artefakts
   gruen (Promotion Schritt 5d), Anker-Drift auf dem Start-Wheel gruen.
4. **Manifest-Diff gegen die Referenz**: das Manifest der ersten Klasse gegen
   `data/manifest_v27-b01-policy_20260910_234958.json` diffen (cli_args, sims, Knoepfe, Spec);
   jede Abweichung ausser Modell, Version, Seed und Datum ist ein Stopp.
5. **Stack-Draw-Kontrolle und Tor 0** wie in v28 (Kette Schritt 1, Tor 2a ex post gegen den
   Wert des v28-Generators: `corpus_sanity_v27-b01-policy.json` 0,816).
6. **Kein Eingriff in importierte Dateien waehrend Waechter oder Kette** (`config.py`,
   `engine/py/neural_net.py`, `corpus_dataset.py`, `file_cache_key.py`): Vorfall 2026-09-11
   (24 Bloecke mit 755 Spalten unter 744er-Schluessel, `PREREG_v28_window.md` par.10). Der
   Merge traegt den Formen-Waechter, die Kette bricht bei Merge-Fehler ab; beides bleibt.
7. **Fenster-Pinning** `MOSAIC_DATA_EXCLUDE` fuer Streudateien, Cache-Waechter unter
   `MOSAIC_IGNORE_POLICY_TARGET_VALID=1` und `MOSAIC_FEATURES_FROM_RUST=1` (derselbe Bauer wie
   beim v28-b02-Training), Plattenplatz fuer rund 1.200 Dateien plus 1.200 Bloecke plus
   Monolith (rund 1,1 GB).
7b. **Record-Feld `tiled_max_row`** (P.14, `stack_top_feature` par.15) additiv in `state_to_json`
   VOR dem Start der Erzeugung, mit dem P.10-Fix im selben Wheel; sonst fehlt es im v29-Korpus.
8. **Namen reserviert** in `docs/generation_naming.md` (v29-b01; weitere nur mit eigener
   Registrierung), Ketten-Skripte `tools/night_v29_generate.sh` und `tools/night_v29_chain.sh`
   nach dem v28-Muster INKLUSIVE der Abbruch-Waechter aus `night_v28_chain_resume.sh` und
   `night_v28_b02.sh`.

## par.5 DIE ERZEUGUNGSBEFEHLE FUER v29 (Vorlage, Start nur auf Anweisung)

Seeds 20260920 / 20260921 / 20260922 (v28 nahm 17-19). `<GEN>` = Name des Generators
(par.3), `<SPEC>` = `models/frozen_champions/<GEN>/spec.json`, Modell aus dem Artefakt.

**PFLICHT in der Umgebung BEIDER Laeufe (Nutzer-Entscheid 2026-09-13, 11:15: "ja dann schalten
wir ihn ein"):** `export MOSAIC_STACK_DRAW_RESEARCH=1`. Ohne ihn traegt der Korpus NULL
Datensaetze fuer `choose_draw_stack_slot` -- an der v28-Erzeugung nachgezaehlt: 0 von 13.145
Records gegen 4,06 Prozent im Kontrollkorpus mit Knopf (`PREREG_chance_nodes.md`, Nachtrag
2026-09-13). Der Knopf hat KEINE Spec-Entsprechung und wird je Prozess einmal per OnceLock
gelesen; `self_play.py` startet jeden Chunk als frischen Prozess, der die Elternumgebung erbt,
ein Setzen vor dem Aufruf genuegt also. Ab Wheel 1 steht er im Lauf-Manifest
(`engine_config_json`), damit die Frage nicht wieder rekonstruiert werden muss.

```
export MOSAIC_STACK_DRAW_RESEARCH=1

# 1) Traeger, 4.000 Partien -- policy-aktiv
python -u self_play.py --mode network --model models/frozen_champions/<GEN>/model.onnx \
  --spec <SPEC> --games 4000 --sims 100 --version <GEN>-policy \
  --threads 11 --chunk 10 --per-file 10 --seed 20260920 \
  --tau-argmax-from-move 1 --deviate-prob 1.0

# 2) Schwarm Haelfte a, 4.000 Partien -- value-only, breite Abdeckung
python -u self_play.py --mode network --model models/frozen_champions/<GEN>/model.onnx \
  --spec <SPEC> --games 4000 --sims 100 --value-only --version <GEN>-value-tempc \
  --threads 11 --chunk 10 --per-file 10 --seed 20260921 \
  --action-temp 2 --deviate-prob 1.0

# 3) Schwarm Haelfte b, 4.000 Identitaeten -- value-only, unverzerrte Ziele
python -u self_play.py --mode network --model models/frozen_champions/<GEN>/model.onnx \
  --spec <SPEC> --games 4000 --sims 100 --value-only --version <GEN>-value-excursion \
  --threads 11 --chunk 10 --per-file 10 --seed 20260922 \
  --excursion-prob 1.0 --tau-argmax-from-move 1 --no-root-noise
```

Ob `self_play.py --model` einen Artefakt-Pfad annimmt, ist NICHT geprueft (v28 nahm
`models/alphazero_v27-b01_brierbest.onnx`); notfalls die Bestandsdatei `models/alphazero_<GEN>_brierbest.onnx`,
die per sha256 mit dem Artefakt uebereinstimmen muss (Manifest des Artefakts).

**Kosten, gemessen an v28** (`docs/measured_runtimes.md`): Erzeugung 35.726 s = 9,9 h auf
dieser Maschine (die v26-Zahl war keine Referenz derselben Maschine), Kette mit
Waechter-Bloecken rund 15 min (Tor 2a 271 s, Monolith 9 min), Training 1,4-1,5 h je Arm,
Gating 66-91 min je Seed mit Logs, Tor 2b und Plattenpunkte unter 5 min.

## par.6 ARME UND TORE

| Arm | Was | Faktor gegen | Seed |
| --- | --- | --- | --- |
| **v29-b01** (Pflicht) | Rezept UNVERAENDERT (Warmstart `<GEN>_brierbest`, 12 Epochen, lr 5e-05 cosine, lambda 0,7, Koepfe wie gehabt, INPUT_SIZE 755) | Champion (= Generator): nur das Material, 5. Punkt der Materialkette; bei Generator b02 zusaetzlich das Stapelwissen auf 82 statt 40 Prozent des Fensters (par.1, nicht trennbar) | 20260941 |
| **v29-b02** (ENTSCHIEDEN 2026-09-11, 19:00, par.8.2) | ABLATION der Spezialfeld-Eingabe: Rezept b01, Planes-Kanaele 77 (Spezialfeld-Ertrag) und 78 (Abstand zur Ausloesung) auf Null; Schalter im Merkmalsbauer (`features.rs`, beide Pfade, plus Python-Zwilling), Teil des Cache-Schluessels; Bloecke neu, gleiches Fenster, gleicher Seed | b01: EIN Faktor, die Spezialfeld-Eingabe | 20260941 |
| **v29-b03** (Sicht-Arm, EINGETAKTET 2026-09-13, Nutzer: "takte p3 und p7 fuer v29 ein"; par.6c) | Rezept b01 plus Encoder-Abschnitt 16 (`PREREG_stack_top_feature.md` par.13): P.3 laufende Ziehserie, P.7 Phasenaufloesung, P.9 Turm je Farbe, P.11 Chip-Anzahl, P.12 Designs im EIGENEN Block (korrigiert 2026-09-13, stack_top par.10: fremde Vorderseiten sieht niemand), P.13 Blocktiefe, P.14 Tiling-Sperre, P.15 Startspieler (ENTSCHIEDEN 2026-09-13, 02:35, stack_top par.15); INPUT_SIZE 755 -> 794. **P.12 ist in v29 eine TOTE SPALTE** (stack_top par.17, Nutzer 2026-09-13: erst ab v30) -- der v29-Korpus wurde vor dem Wheel von Abschnitt 16 erzeugt und traegt das Record-Feld `designs` nicht; der Arm misst 21 der 39 Werte; Warmstart mit null-initialisierten neuen Spalten (v24-b04-Muster); Bloecke neu, gleiches Fenster, gleicher Seed | b01: EIN Faktor, die Sichtwerte | 20260941 |

**BERICHTIGUNG 2026-09-11, 18:50 (Regel 0):** die Aussage, par.4a sei "registriert und nie
gebaut", war FALSCH. Die zwei Planes (Spezialfeld-Ertrag je Slot und Abstand zur Ausloesung)
sind seit Commit `e91cd34` (2026-08-28) gebaut: `features.rs:1149` `SPECIAL_YIELD_CHANNEL = 77`,
`:1160` `SPECIAL_UNLOCK_DISTANCE_CHANNEL = 78`, NUM_PLANES_CHANNELS 79; jedes Modell seit v22-b01
traegt sie (`PREREG_special_tile_yield.md`, Nachtrag 2026-08-29 im Kopfbereich). Was fehlt, ist
die ISOLIERTE Wirkungsmessung (kein 77-gegen-79-A/B, der Beitrag ist in der b-Serien-Baseline
konfundiert) und der par.4c-Kopf (ungebaut; Hilfskoepfe stehen 0 von 4). Der Koordinator hat
die eigene Memory-Notiz ("Kanaele 77/78 gebaut, Wirkung nie isoliert") uebersehen.

Folge fuer den Arm: ein Neubau derselben Eingabe ist gegenstandslos. Was die Frage "traegt die
Spezialfeld-Eingabe?" beantwortet, ist die Ablation: v29-b02 = Rezept b01 mit den Kanaelen
77/78 auf Null (Schalter im Merkmalsbauer, Teil des Cache-Schluessels; Bloecke neu, rund 26 min),
Tor 1 b02 gegen b01. **ENTSCHIEDEN 2026-09-11, 19:00 (Nutzer: "dann fahren wir die ablation als
v29-b02").** Leserichtung, VORAB: die Kante laeuft b02 (ohne Kanaele) gegen b01 (mit); verliert b02
signifikant, traegt die Eingabe (Verdikt fuer `special_tile_yield` par.4a: wirksam), und der
naechste Hebel fuer den Spezialfeld-Posten ist die Drafting-Seite oder par.4c; gleichauf oder
b02 vorn, dann traegt sie nicht, und die Kanaele bleiben nur aus Kompatibilitaet (Modellbreite)
im Vektor. Zusatzkennzahl je Modell aus den Logs: Plattenpunkte "Spezialfelder" und ausgeloeste
untere Spezialfelder je Seite (`plate_points_from_arena.py`, `special_tile_yield_measurement.py`).
Bau: Schalter `MOSAIC_SPECIAL_PLANES_OFF` (Name vorlaeufig, Registratur-Eintrag Pflicht) im
Rust-Bauer und im Python-Zwilling, Paritaetstor mit Schalter an, Anker-Drift (der Anker ist
netzlos, die Drift muss gruen bleiben), Netz-Paritaets-Fixture des Champions unveraendert (Schalter
aus = bitidentisch). Generator fuer v30 (falls es v30 gibt) bleibt der Sieger der Kanten.

**Warum die Spezialfelder (Nutzer 2026-09-11: "Kandidat 1 als einzigen Netz-Arm"; Zahlen bleiben gueltig):**
die Spezialfelder sind der groesste negative Posten der Plattenwertung (Tor 1 v28: -9,73 gegen
-10,61 Punkte je Partie bei 160 von 400 Brettern, `PREREG_v28_window.md` par.10), der Lehrer
liess 81 Prozent der unteren Spezialfelder liegen (`special_tile_yield` par.7), und der Knopf K5
(`MOSAIC_SPECIAL_ROW6_W`, in der Champion-Spec) hob zwar die Spalten, nicht aber das
Spezialfeld-Kriterium (par.9 dort). Der Tiling-Loeser holt den Bonus bereits exakt ab; die Luecke
sitzt im Drafting Runden vorher (par.4a). Die Eingabe dafuer existiert (Berichtigung oben); ob
sie wirkt, ist die offene Frage. Das Sicht-Reststufen-Paket (`stack_top_feature` par.10
P.3/P.7) ist NICHT bestellt.

**Diagnostik am Arm, vorregistriert:** auf den Tor-1-Logs b02 gegen b01 die Plattenpunkte je
Kriterium (`plate_points_from_arena.py --block 5`): Erwartung ist ein Zuwachs GENAU im Posten
Spezialfelder (gepaart, 200 Paare); ein Zuwachs anderswo bei unbewegtem Spezialfeld-Posten
hiesse, die Eingabe wirkt ueber einen anderen Weg (Praezedenz K5). Zusaetzlich der
Spezialfeld-Bonus je Partie aus den Logs (Sonde `tools/probes/special_tile_yield_measurement.py`,
Grundmenge Arena-Partien, Einheit ausgeloeste untere Spezialfelder je Seite).

Weitere Arme (Ablationen, Knoepfe) nur mit eigener Registrierung in dieser Datei; Namensregel
`docs/generation_naming.md`. Reihenfolge: b01 in der Kette, b02 danach auf demselben Fenster
(Bloecke neu unter dem Planes-Schluessel), Tor 1 b02 gegen b01, der bessere gegen den Champion,
falls das nicht dieselbe Kante ist.

**Tore** (`docs/generation_loop.md`): Tor 0 Traegerkennzahl (Kette Schritt 1; Tor 2a ex post
gegen den Wert des v28-Generators, par.4 Punkt 5), Tor 1 gepaartes Gating mit `--log-games`,
Blockgroesse 5, zwei Seeds (Regel v27: kein dritter Seed, wenn beide positiv und kein
Nullentscheid), Tor 2b aus denselben Logs (`arena_column_probe.py`), Plattenpunkte je Modell
(`plate_points_from_arena.py --block 5`), sechs Standard-Kennzahlen. Kante: b01 gegen den
Champion aus seinem Artefakt, beide Seiten Champion-Spec. Promotion nach
`docs/promotion_checklist.md`; Champion-2-Kante dann gegen das Artefakt `v27-b01`.

## par.6b STARTKUPPEL-STREUUNG IN DER ERZEUGUNG (Nutzer 2026-09-12, Dosis offen)

Nach Stufe 0 der Startkuppel-Frage (`PREREG_start_dome_choice.md` par.9/9a: die Handregel legt
immer (0,0), und das ist der beste Slot) will der Nutzer, dass das Netz abweichende Setzungen
KENNT (par.9b dort). Vorschlag fuer das v29-Rezept: Erzeugungsknopf `MOSAIC_START_SLOT_RANDOM_P`
(je Spieler, aus dem Partie-RNG), Start-Record der gestreuten Setzung mit
`policy_target_valid = false`, Value-Labels gueltig; Arena und Gating unveraendert. Dosis
Vorschlag 0,15 je Spieler, Nutzer-Entscheid. Bau vor dem Generationswechsel (Default 0
bitidentisch, Tore Tests/Fixture/Drift). Der Knopf ist KEIN Arm: v29-b01 bleibt das v28-Rezept
plus diese Streuung; ob die Streuung selbst etwas kostet, prueft Tor 2a (Punkteniveau und
Spalten der Erzeugung gegen v28) ex post.

## par.6c SICHT-ARM v29-b03 (Nutzer 2026-09-13, 01:00: "takte p3 und p7 fuer v29 ein")

Dritter Arm, Registrierung und Zuschnitt in `PREREG_stack_top_feature.md` par.13. Kurz: die
drei Record-Felder (`pending_stack_draw`, `phase`, `bag_colors`/`tower_colors`) liegen seit jeher
im Record, es braucht KEIN neues Record-Feld vor der Erzeugung (anders als `dome_pool_view` fuer
v28-b02), nur den additiven Encoder-Anbau (Rust beide Pfade, Python-Zwilling, `config.INPUT_SIZE`,
Sichtgleichheits-Test, Regressionstest 755er-Layout, Paritaets-Fixture des Champions unveraendert,
Anker-Drift gruen). P.9 (Turm je Farbe) ist im Arm ENTSCHIEDEN (Nutzer 2026-09-13, 01:45, nach Crosscheck `stack_top_feature` par.14). Nach der Sichtinventur (`stack_top_feature` par.15, Nutzer 02:20) kommen P.11 (Anzahl gehaltener Bonuschips, 2 Werte) und P.15 (Startspieler der naechsten Runde, 1 Wert) dazu; seit 02:35 (par.8 Punkt 6) auch P.12 (18 Bits), P.13 (2) und P.14 (2): 39 sichere Werte, INPUT_SIZE 794 (812 mit den Design-Bits von P.3). Fruehere Zwischenstaende 769/787 und 772/790 sind ueberholt. P.10 (Suche wuerfelt den Typ der obersten Stapelplatte neu) ist ein Suchfix, kein Merkmal; Zeitpunkt Nutzer-Entscheid (par.8 Punkt 7).

**Bau-Zeitpunkt:** Wheel-Wechsel, deshalb in einem Fenster ohne Erzeugung, Waechter oder Kette
(par.4 Punkt 6). Vorschlag: im Generationswechsel NACH der Sims-Neumessung
(`PREREG_search_depth_column_optimum.md` par.8e) und VOR dem Start der v29-Erzeugung; der
Generator deklariert 755 und sieht die neuen Werte nie. Danach die Pflichtpruefung par.4 Punkt 2/3
mit dem NEUEN Kontrakt-Hash (der Vertragsstring traegt die Vektorlaenge; A10 des Code-Abschlusses),
Manifest-Referenz entsprechend. Alternative: nach dem Ende der Erzeugung vor dem Training.

**Reihenfolge der Arme:** b01 in der Kette, b02 (Ablation) und b03 (Sicht) danach auf demselben
Fenster mit je eigenen Bloecken; Tor 1 je Arm gegen b01 (zwei Seeds, Blockgroesse 5, Logs), der
beste gegen den Champion. Lesart b03 nach `stack_top_feature` par.7 mit dem Verwerfungs-Ausgang
aus par.12: Gleichstand -> Sichtstand uebernehmen (Kriterium Sichtgleichheit), Regression ueber
zwei Seeds -> Merkmal aus, Ursache suchen. Kosten (ANNAHME): Bau und Tore rund 2 h, Bloecke rund
26 min, Training wie b01, Tor 1 zwei Seeds rund 3 h.

## par.6d NETZ-GESUNDHEIT unter wachsendem Eingang (Nutzer 2026-09-13, 01:55: "schreib fuer v29 hinzu dass wir uns die netz gesundheit anschauen sollten. nicht dass uns der nun abstirbt mit der anzahl an features")

Der Flachvektor ist von 714 (bis v23) ueber 744 (v24-b04) und 755 (v28-b02) auf 794 oder 812
(v29-b03, `stack_top_feature` par.15) gewachsen, jedes Mal per Warmstart mit null-initialisierten neuen Spalten in
`flat_branch.0.weight` (`train.py` Z.1685-1692). Praezedenz fuer einen sterbenden Kopf gibt es
(v14: Kaltstart-Destillation verlor den Value-Kopf; v8d). Deshalb, VORREGISTRIERT als Pflichtteil
der Abnahme von v29-b03 (und als Bezug an b01 mitgemessen):

1. **Neue Spalten leben?** Nach dem Training die Spaltennormen von `flat_branch.0.weight` fuer die
   neuen Indizes (755..) gegen die Altspalten: nahe 0 heisst, das Netz benutzt die Sichtwerte nicht
   (dann traegt der Arm per Konstruktion nichts); ein Vielfaches der Altnormen heisst, sie
   dominieren. Beides ist ein Befund, kein Tor. Einzeiler am Checkpoint, kein Werkzeug noetig.
2. **Tote Einheiten:** Anteil der ReLU-Einheiten der ersten Flachschicht (und des Rumpfs), die auf
   dem Frozen-Set nie feuern, b03 gegen b01 gegen den Champion; Schwelle vorab: mehr als das
   Doppelte des b01-Anteils ist ROT.

   **GEBAUT 2026-09-13 als `tools/probes/dead_unit_probe.py`** (Fahrplan Nr. 20). Die Aussage
   "Werkzeug gibt es nicht" war nur halb richtig: die MESSUNG stand bereits als
   `analyze_capacity` in beiden Modellklassen (`neural_net.py` Z.1866 flach, Z.2142 2D) und
   wird von `tools/probes/net_capacity_probe.py` aufgerufen -- was fehlte, war der FESTE
   Auswertungssatz. Jenes Werkzeug zieht eine Zufallsstichprobe aus einer Fensterliste; fuer
   eine Reihe ueber 744 / 755 / 794 braucht es denselben Satz je Modell, sonst vermischt sich
   der Eingangs-Effekt mit der Stichprobe. Die neue Sonde stellt `analyze_capacity` auf
   frozen_v3 (1.800 Zustaende) und haelt sie gegen eine benannte Referenz (`--reference`,
   Pflichtarm der Generation); sie baut die Messung NICHT nach.

   Ins Verdikt gehen nur die Schichten, die den Flachvektor sehen (2D: `flat`, `fusion1`,
   `fusion2`; flach: `layer1` bis `layer3`), gewichtet nach Einheitenzahl. Die Conv-Schichten
   werden mitgemessen und getrennt ausgewiesen -- sie sehen den gewachsenen Eingang nicht.

   Selbsttest am 2026-09-13 ueber drei Generationen (n = 24 Zustaende, Grundmenge ein
   Ausschnitt von frozen_v3, Einheit Anteil toter ReLU-Einheiten -- eine FUNKTIONSPROBE, kein
   Ergebnis): v28-b02 6,51 %, v28-b01 6,71 %, v27-b01 6,71 % bei Eingaengen 755 / 744 / 744.
   Der volle Lauf ueber 1.800 Zustaende gehoert zur b03-Abnahme und darf nicht neben einer
   Arena oder Erzeugung laufen.
3. **Koepfe einzeln:** `tools/offline_diagnosis.py` (Value-R2 gesamt und je Runde, Policy Top-1/3)
   und `tools/oracle_metrics.py` (prior_mass_on_oracle_top3, kendall_tau; sagen die Arena 7/7
   voraus) b03 gegen b01 auf demselben Val-Split. Aufloesungsgrenze value_r2 rund 0,015; eine
   Verschlechterung des Value-Kopfs jenseits davon ist der Verwerfungs-Ausgang aus
   `stack_top_feature` par.12, unabhaengig vom Tor-1-Ergebnis.
4. **Value-Kopf-Verlaesslichkeit:** `tools/probes/value_head_reliability_probe.py` (rho je Runde)
   und `tools/platt_fit.py` (A/B, Brier auf frozen_v3) b03 gegen b01; Brier darf nicht ueber den
   b01-Wert steigen (Praezedenz v14: der Kopf starb, die Arena sah es spaet).
5. **Trend ueber die Generationen:** dieselben Zahlen fuer v24-b04, v28-b02 und v29-b03 in EINER
   Tabelle (Eingang 744 / 755 / 787), damit ein schleichender Abbau sichtbar wird und nicht nur ein
   Sprung. Ergebnis in par.9 dieser Datei und in `stack_top_feature` par.13.

Lesart vorab: haelt b03 in 3 und 4 das b01-Niveau und leben die neuen Spalten (1), ist der Eingang
tragfaehig und die naechste Sichtstufe darf anbauen. Faellt 3 oder 4, ist die Sichtgleichheit nicht
der Fehler, sondern Warmstart oder Kapazitaet (Bezug `project_value_head_capacity`); dann Kaltstart
oder breiterer Rumpf als eigener Arm, nicht Merkmal raus. Rechenlast: alle fuenf Punkte ohne Suche,
Minuten je Modell, nie neben einer Arena.

## par.7 BEGLEITPROGRAMM IN DEN CPU-FREIEN FENSTERN VON v29 (eingetaktet, keine Arme)

1. **Schwierigkeitsleiter** (`PREREG_difficulty_levels.md` par.8.6, Nutzer 2026-09-11):
   Inventur und Bau (Stilmittel in die Spec, Server-Stufentabelle, Frontend-Auswahl, Wheel
   mit Paritaets-Fixture und Anker-Drift) WAEHREND der Erzeugung; die drei Kanten
   (Meister/Experte, Experte/Erfahren, Erfahren/Anfaenger, je 100 Paare) NACH Tor 1 v29
   mit dem dann amtierenden Champion als Meister; danach Nutzer-Partien je Stufe. Der
   Wheel-Bau fuer die Leiter ist eine Engine-Aenderung: Anker-Drift und Paritaets-Fixture
   vor jedem weiteren Messlauf, und NICHT waehrend Waechter oder Kette (par.4 Punkt 6).
2. **Ziehsucht-Sonde** der Claude-Partien-Sitzung (`PREREG_claude_play_interface.md` par.9,
   STATUS Abschnitt 1: drei Arme aus dem vorhandenen Korpus messbar, Lauf vom Nutzer auf
   v29 gelegt): ein CPU-Lauf ohne neue Erzeugung, Reihenfolge nach der Leiter-Kante oder
   davor, je nachdem, was die Maschine frei hat.
2b. **Zugklassen-Differential der Claude-Partien** (`PREREG_claude_play_interface.md` par.10,
   Nutzer 2026-09-12): an jedem Claude-Entscheid Champion-Zug und Wurzelwert, Abweichungen je
   Klasse mit Ausgang; unter 30 min, direkt nach der Ziehsucht-Sonde (gleiches Replay).
2c. **Drafting sieht das Tiling** (`PREREG_round_transition_search_sampling.md` par.9, Nutzer
   2026-09-12): Variante B als Such-Knopf mit Default aus, Mischregel = determinize_dome_pool;
   Kostentor am Instrument, dann A/B 200 Paare am Champion v29-b01. Rund ein Tag Bau, 3 h Messung;
   Aufnahme ins Rezept nur bei positivem A/B (Nutzer-Entscheid).
2d. **Mondstapel-Reihenfolge Stufe 1** (`PREREG_moon_stack_order.md` par.4): Knopf
   `MOSAIC_MOON_ORDER_VARIANTS` (Default = Bestand), A/B Fan-out an gegen aus, 200 Paare.
3. **Reste aus v28**, falls dort nicht mehr gefahren: Startkuppel-Sonde Stufe 0 (am v28- ODER
   v29-Korpus, gleiches Instrument), ~~Ueberraschungs-Kante v24-b05 gegen v24-b04~~ (in v28
   gefahren 2026-09-12: 97:103, SPRT H0, `policy_surprise_weighting` par.12 ENTSCHIEDEN),
   `round_estimate_leaf_term` als Such-Knopf am Champion-Stand (Knopf seit 2026-09-12 im Wheel). Jeder davon ist ein
   Engine-Knopf oder eine Sonde ohne Training; sie laufen NIE neben einer Arena.
4. **Aus der Audit-Querlesung 2026-09-11 (Nutzer: "2 bis 4 als Sonden und Knoepfe im
   Begleitprogramm, 5 und 6 nach Maschinenlage"), alle ohne Training, keine neben einer Arena:**
   - **Stapelziehen bei positivem Stand**, zwei Teile: (a) Neurechnung der Stopp-Regel der
     Blindziehung (`PREREG_stack_draw_reservation_rule.md` par.7: das Modell nahm ein
     gedaechtnisloses Ziehen an; seit Variante A behaelt die Suche das Wissen; par.5b: die Regel
     zieht bei negativem Brettniveau 9 bis 11 Mal, optimal ist Tiefe 1), Ergebnis als Sonde am
     v29-Korpus plus Knopf-A/B, wenn die Neurechnung eine andere Regel ergibt; (b) Bau der
     Ein-Schritt-Bewertung der Zieh-Aktion (`PREREG_chance_nodes.md` par.14 Teil B1, Knopf
     `MOSAIC_STACK_DRAW_CHANCE`, nie gebaut) als Such-Knopf mit A/B ueber den Referee. Beides
     laeuft zusammen mit der Ziehsucht-Sonde (Punkt 2), weil alle drei denselben Befund
     bearbeiten.
   - **Startkuppel**: Stufe 0 nach `PREREG_start_dome_choice.md` par.4 (Slot-Spannweite), dazu
     die Plattenwahl (Nachtrag 2026-09-09 dort) als zweiter Teil; Anlass par.6a:
     `choose_start_placement` bewertet `SpaceType::Special` mit 0,0 (`self_play.rs:922`).
   - **Sims-Kurve des Generators neu messen** (`PREREG_search_depth_column_optimum.md` par.8c:
     faellig, weil INPUT_SIZE 744 -> 755 ein Aera-Wechsel ist). NEU GEFASST 2026-09-13 (par.8e
     dort, Nutzer): vier Punkte 100/200/400/600 in ZWEI Formen (gepaart gegen @400 fuer die
     Staerke, argmax-Instrument fuer den Korpus), VOR dem v29-Self-Play, weil der erste Punkt
     am Champion das Plateau gekippt hat (@100 verliert 7:23, weniger Spalten). Faellt die Kurve
     fuer hoehere Sims aus, wird auch der SOCKEL (par.1/par.6) mit den hoeheren Sims neu erzeugt
     (Nutzer 2026-09-13, 00:12); Kosten und Zuschnitt dann hier vorregistrieren. Die
     argmax-Dateien `data/selfplay_depth<S>-v28b02_*.pkl` sind Messmaterial und gehoeren vor dem
     Fensterbau auf die Ausschlussliste (Punkt 7, Fenster-Pinning).
   - **Rueckgabe-Reihenfolge der Kuppelplatten** (`PREREG_dome_return_order.md`, Nutzer
     2026-09-12: legaler Zug, den das Netz nicht nutzt): Such-Knopf `return_order_mode` (netzbewertet),
     A/B ueber den Referee nach der Promotion; wird er Default, gilt er fuer die v29-Erzeugung.
   - **Nach Maschinenlage**: `round_estimate_leaf_term` (Skala (a) 3/8/10/12, Bau nach par.3
     dort; sitzt schon als v28-Schritt 7) und die Netz-Loeser-Arme aus `PREREG_r5_solver_split.md`
     par.4 (Knotenbudget netzseitig, Policy-Sortierung, Korrekturterm; 200 Knoten treffen das
     Orakel zu 81,4 Prozent, 4.000 zu 84,8; der Anker ist eingefroren und davon unberuehrt).
5. **Prereg-Bestand**: Ziel bleibt rund 7 OFFEN. Mit v28 schliessen `rust_data_layer` (Teil A
   Verdikt mit b02), `stack_top` (haengt an b02), `round_transition_search_sampling`
   (UEBERHOLT durch `dome_stack`), `start_dome_choice`, `policy_surprise_weighting`,
   `round_estimate_leaf_term`; offen bleiben `v29_window`, `difficulty_levels`,
   `claude_play_interface` bis zu ihren Laeufen.

## par.8 OFFENE NUTZER-ENTSCHEIDE

1. G-2-Haelfte (par.2; Vorschlag Ausflug).
2. ~~Kandidat v29-b02~~ ENTSCHIEDEN 2026-09-11, 19:00 (Nutzer: "dann fahren wir die ablation
   als v29-b02"), nach der Berichtigung in par.6: v29-b02 = Ablation der Spezialfeld-Kanaele
   77/78. Weiter entschieden: Stapel-Stopp-Regel, Peek-Bewertung,
   Startkuppel und Sims-Kurve als Sonden und Knoepfe im Begleitprogramm (par.7 Punkt 4);
   Rundenschaetzer und R5-Netzloeser nach Maschinenlage. Die Sicht-Reststufen sind nicht
   bestellt.
5. ~~P.9 (Turm je Farbe) im Sicht-Arm v29-b03 mitbauen?~~ ENTSCHIEDEN 2026-09-13, 01:45 (Nutzer:
   "also wieder eine sichtluecke. takte es ein"), Beleg `stack_top_feature` par.14 (Crosscheck
   106/106, Encoder sieht nur die Summe). b03 baut P.3, P.7 und P.9.
6. ~~P.12 in Abschnitt 16 aufnehmen?~~ ENTSCHIEDEN 02:35 (Nutzer: "p12 kommt mit rein"); dazu P.13
   (2 Werte) und P.14 (2 Werte, Record-Feld `tiled_max_row` VOR der Erzeugung) nach Pruefung.
7. ~~Zeitpunkt des Suchfixes P.10~~ ENTSCHIEDEN 02:35 (Nutzer: "p10 fix kommt jetzt"): Code steht in
   `state.rs`, Build/Tests/Wheel/Fixture/Anker-Drift nach dem Ende der laufenden Messungen.
8. **Schwarm-Erzeugung FREIGEGEBEN (Nutzer 2026-09-13, 02:10):** nach Abschluss der Sims-Messung
   selbststaendig ueber `/mosaic-generation-turnover`, Schwarm (tempc + excursion) mit 100 Sims.
   **Sockel zurueckgestellt**: Sims nach par.8e der Sims-Prereg, vermutlich auf der schnelleren
   Maschine (Nutzer); Zuschnitt par.1 bleibt, nur die Reihenfolge aendert sich (Schwarm zuerst).
   Folge fuer par.5: nur die zwei value-only-Befehle laufen jetzt; der Policy-Befehl wartet.
3. ~~Ist v29 die letzte Generation?~~ ENTSCHIEDEN (Nutzer 2026-09-12, 18:05): **v30 folgt, wird
   released und ist der Projektabschluss.** Folgen: v29 ist die Generation, in der das
   Begleitprogramm (par.7: Tiling im Blatt, Mondstapel Stufe 1, Claude-Differential, Sonden) seine
   Verdikte liefert; was traegt, geht ins v30-Rezept; v30 selbst bekommt nur noch Rezept-Knoepfe,
   keine neuen Bauvorhaben. Nach der v30-Promotion: Leiter-Endfassung mit dem v30-Champion
   (`PREREG_difficulty_levels.md` Stufe 5), Schlussmodell "Tessa" = v30-Champion
   (`PREREG_code_cleanup_closeout.md` par.5a), Code-Abschluss Stufen 2 und 3, STATUS-Neufassung
   als Abschlussbericht, letzter restic-Snapshot mit Beleg.
4. Freigabe der Erzeugung (Regel seit 2026-09-03: die Fenstererzeugung startet nur auf
   Anweisung).

## par.9 ERGEBNISSE

### Erzeugung und Tor 2a (2026-09-14, Kette Schritt 1)

**Erzeugung durch, vollstaendig** (2026-09-13 12:08 bis 2026-09-14 00:57, rund 12,8 h): 400
Dateien `v28-b02-policy`, 400 `v28-b02-value-tempc`, 401 `v28-b02-value-excursion`. Die Dauer
liegt ueber der Hochrechnung von 10,8 h; als Ursache kommt die Nebenlast in Frage, die in
Abschnitt 1 von `STATUS.md` offengelegt ist (nicht geprueft).

**Tor 2a ex post: HAELT.** `v28-b02` als Generator **0,843** (+-0,017) gegen `v27-b01` **0,816**
(+-0,017). n = 8.000 Seiten aus 4.000 Partien der Policy-Klasse, Grundmenge Seiten, Einheit
**volle Spalten je Seite** (`corpus_sanity_check.py`, Feld `sp_voll`; Instrument und Bezugsregel
in `docs/generation_loop.md`).

**Die Reihe ist ueber fuenf Generationen monoton:**

| Generator | volle Spalten je Seite |
| --- | --- |
| v24-b07 | 0,637 |
| v25-b01 | 0,737 |
| v26-b01 | 0,777 |
| v27-b01 | 0,816 |
| **v28-b02** | **0,843** |

Der Zuwachs wird kleiner (+0,100 / +0,040 / +0,039 / +0,027). Das passt zur erwarteten Saettigung
aus dem Leitstern, ist aber KEIN Beleg dafuer: die Zahl misst die Self-Play-Flaeche des
Generators, nicht die Spielstaerke, und vier Differenzen sind keine Kurve.

**Standard-Kennzahlen der Policy-Klasse** (CLAUDE.md; alle aus demselben Artefakt, n = 8000 Seiten
aus 4000 Partien):

| Groesse | Wert |
| --- | --- |
| volle Spalten je Seite | 0.843 (+-0.017) |
| Teilspalten >= 3 | 3.131 |
| Teilspalten >= 4 | 2.167 |
| hoechste Spalte | 5.537 |
| eigene Punkte | 48.66 |
| Strafleiste | 5.58 |
| Margin zum Gegner | 0.0 |

Der Margin ist per Konstruktion 0: im Self-Play spielt dasselbe Netz beide Seiten, die Klasse ist
also ihr eigener Gegner. Die Reihenauslastung traegt dieses Artefakt nicht; sie steht in den
Arena-Logs von Tor 1 und wird dort berichtet.

### Tor 1 v29-b01 gegen v28-b02: **BEIDE SEEDS H0 -- der Pflichtarm traegt nicht**

| Seed | Verdikt | Paare | Siege b01 : b02 | LLR | McNemar p | Punkte b01 / b02 | Laufzeit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 20261061 | H0 | 90 | 87 : 93 | -2,956 | 0,76 | 49,99 / 50,23 | 2.485 s |
| 20261062 | H0 | 75 | 69 : 81 | -3,838 | 0,44 | 48,31 / 51,23 | 1.989 s |

Beide Laeufe brachen an der unteren Wald-Schranke ab (H0 p = 0,5 gegen H1 p = 0,65, alpha =
beta = 0,05), zusammen 330 Partien. **Kein Champion-Wechsel**: `v28-b02_brierbest` bleibt.
Ein DRITTER Seed ist kein Automatismus und hier auch nicht angezeigt -- beide Seeds zeigen
dasselbe, und keiner war knapp.

**Tor 2b GRUEN in beiden Laeufen** (Replay-Pruefung: 180 von 180 und 150 von 150 nachgespielt,
je 0 divergiert).

**Die vollen Spalten drehen das Vorzeichen zwischen den Seeds** -- genau deshalb sind zwei
Pflicht:

| | Seed 1 | Seed 2 |
| --- | --- | --- |
| volle Spalten b01 | 0,928 (+-0,109) | 0,920 (+-0,127) |
| volle Spalten b02 | 0,883 (+-0,107) | 0,933 (+-0,117) |
| Differenz | +0,045 | -0,013 |

n = 180 bzw. 150 Bretter je Modell, Grundmenge Bretter, Einheit volle Spalten je Seite.

**Der Kriteriums-Befund aus Seed 1 haelt der Wiederholung NICHT stand.** In Seed 1 war
"Mehrfarbige Felder" mit -1,222 [-2,341, -0,104] das einzige Intervall ohne die Null; in Seed 2
liegt dasselbe Kriterium bei -0,680 [-2,027, +0,667], also klar ueber der Null. Dasselbe bei den
Vertikalen Reihen (+1,207 gegen +0,913, beide Intervalle enthalten die Null). **Die VORZEICHEN
wiederholen sich, die Signifikanz nicht** -- und bei acht geprueften Kriterien war genau das die
angekuendigte Erwartung. Als Befund geht das nicht durch; als Richtung bleibt es notiert.

**Was das fuer die Kampagne heisst -- und was NICHT.** Die erste Fassung dieses Absatzes hat
b01 einen "reinen Materialschritt auf demselben Rezept" genannt und daraus geschlossen, mehr
Material bewege den Champion nicht mehr. **Das ist falsch, und der Nutzer hat es am 2026-09-14
korrigiert: "das war kein reiner materialschnitt. wir haben den input erweitert" und "die
startkuppel variation hinzugefuegt".**

Am Manifest-Diff nachgepruefen (v29-Erzeugung gegen die des Champions, also
`manifest_v28-b02-value-excursion_20260913` gegen `manifest_v27-b01-value-excursion_20260911`;
Dateien heissen nach dem GENERATOR). **DREI Unterschiede, alle in der ERZEUGUNG:**

| Feld | Korpus des Champions | Korpus von b01 |
| --- | --- | --- |
| `start_slot_random_p` | nicht gesetzt | **0,15** |
| `spec` | `v24-b07_brierbest.spec.json` | **`start_by_search_on.spec.json`** |
| `stack_draw_research` | aus | **an** |

**Nicht in dieser Liste: `input_size` 744 -> 755.** Der Diff zeigt sie, sie ist aber KEINE
Neuerung der v29-Erzeugung, sondern die Breite des GENERATORS: Abschnitt 15 (Kuppelstapel-Wissen)
kam mit v28-b02, also erzeugt dieser Champion mit 755, waehrend sein Vorgaenger v27-b01 mit 744
erzeugte. Ein Generator, der breiter sieht als der davor, ist der Normalfall jedes Zyklus und
kein Arm-Unterschied. (Nutzer-Rueckfrage 2026-09-14; die erste Fassung dieser Tabelle hatte die
Zeile faelschlich als vierten Unterschied gefuehrt.)

Das TRAININGS-Rezept ist dagegen unveraendert (`cli_args`-Diff: nur Fensterliste, Warmstart-Name,
Lauf-Name, Seed und Val-Pool-Regex). "Rezept unveraendert" in par.6 meint genau das -- es meint
NICHT, dass der Korpus derselbe waere.

**Die Lesart des H0 aendert sich damit grundlegend.** b01 hat nicht mehr vom Gleichen bekommen,
sondern Material aus einer anderen Verteilung: variierte Startkuppeln statt fester, die
Startkuppel per Suche statt per Handregel, dazu den Stapelzug-Knopf. **Hypothese des Nutzers
(2026-09-14, ausdruecklich als solche notiert): "kann gut sein dass sich das netz erst daran
gewoehnen muss."** Ein Nullbefund nach EINEM Zyklus auf einer neuen Verteilung ist damit etwas
anderes als eine Saettigung -- er koennte auch der Preis der Umstellung sein.

**Und die Verduennung ist gross** (Nutzer 2026-09-14: "nicht alles vom material ist tragend fuer
die neuen input features"). Am Fenster nachgezaehlt (n = 2.947 Dateien, Grundmenge
`data/window_v29.txt`, Einheit Dateien):

| Generator | Anteil am Fenster | `dome_pool_view` (Abschnitt 15) | `tiled_max_row` (P.14) |
| --- | --- | --- | --- |
| v28-b02 (neu) | 1.201 = **40,8 %** | ja | ja |
| v27-b01 (G-1) | 1.201 = 40,8 % | ja | **nein** |
| v26-b01 (G-2) | 545 = 18,5 % | **nein** | **nein** |

**Nur 40,8 Prozent des Fensters sind ueberhaupt mit den drei neuen Erzeugungs-Knoepfen
entstanden.** Die Startkuppel-Variation, die Startkuppel-Suche und der Stapelzug-Knopf wirken auf
diesem Anteil; die restlichen 59,2 Prozent sind Material aus der Zeit davor. Ein Nullbefund nach
EINEM Zyklus misst also einen stark verduennten Effekt -- das ist kein Einwand gegen den Test,
aber es begrenzt, was er zeigen kann.

**Dasselbe trifft die Merkmale, und zwar unterschiedlich hart.** Die Felder, aus denen Abschnitt
15 und 16 rechnen, liegen nicht in allen Records:

- Abschnitt 15 (11 Werte, Kuppelstapel-Wissen): **81,6 %** des Fensters tragen `dome_pool_view`,
  der v26-Anteil nicht -- dort sind die elf Werte 0.
- P.14 (2 Werte, Sperrstand der Musterreihen): **nur 40,8 %** tragen `tiled_max_row`.
- P.12 (18 Werte, Designs im eigenen Block): **0 %** -- das Feld `designs` entstand erst mit dem
  Wheel von heute (par.17 der `stack_top_feature`-Prereg, Nutzer-Entscheid: erst ab v30).
- P.3, P.7, P.9, P.11, P.13, P.15 (19 Werte): aus Feldern, die alle drei Generationen tragen.

**Folge fuer die Lesart von b03:** von den 39 Werten des Sicht-Arms sind 19 ueber das ganze
Fenster belegt, 2 nur auf 40,8 Prozent und 18 gar nicht. Wer b03 gegen b01 misst, misst im
Wesentlichen diese 19 -- und muss das beim Verdikt sagen, statt von "dem Sicht-Arm" zu sprechen.

**Was daraus NICHT folgt:** dass die Umstellung sich lohnt. Der Arm ist einfaktoriell geplant
gewesen und ist es nicht; welcher der drei Unterschiede den H0 traegt, ist mit diesen Daten nicht
trennbar. Wer das wissen will, braucht einen Arm, der genau einen davon zuruecknimmt.

Die beiden anderen Arme sind davon unberuehrt: b02 (Spezialfeld-Ablation) und b03 (Sicht-Arm)
laufen auf DEMSELBEN Fenster wie b01 und aendern nur den Eingang -- gegen b01 gemessen sind sie
sauber einfaktoriell.

### Tor 1 v29-b01 gegen v28-b02, Seed 20261061 (erster von zwei): **H0**

**SPRT-Verdikt H0** nach 90 Paaren (180 Partien, Abbruch an der unteren Wald-Schranke,
LLR -2,956 gegen -2,944). Getestet wurde H0 p = 0,5 gegen H1 p = 0,65; H0 heisst **kein Beleg
fuer die vorregistrierte Ueberlegenheit**, nicht "b01 ist schlechter".

| Groesse | v29-b01 | v28-b02 |
| --- | --- | --- |
| Siege | 87 | 93 |
| volle Spalten je Seite | 0,928 (+-0,109) | 0,883 (+-0,107) |
| Teilspalten >= 4 | 2,200 | 2,306 |
| Teilspalten >= 3 | 3,139 | 3,167 |
| hoechste Spalte | 5,639 | 5,628 |
| volle Zeilen | 0,117 | 0,078 |
| Spezialfelder belegt | 1,283 | 1,172 |
| eigene Punkte | 49,99 | 50,23 |
| Strafleiste | 8,61 | 8,13 |
| Margin | -0,23 | +0,23 |

n = 180 Bretter je Modell, Grundmenge Bretter, Einheit je Partie. Gepaart ueber 90 Paare:
Siege -0,033 [-0,177, +0,110], Punkte -0,233 [-2,99, +2,52], McNemar p = 0,76. **Alles null.**

**Tor 2b GRUEN**, und zwar im Sinne der Replay-Pruefung: 180 von 180 Partien nachgespielt,
**0 divergiert**.

**Der einzige Befund mit einem Intervall, das die Null ausschliesst, sitzt bei den
Plattenkriterien** (gepaart, nur Partien mit beidseitig aktivem Kriterium):

| Kriterium | Differenz b01 minus b02 | 95-%-KI | n Paare |
| --- | --- | --- | --- |
| Mehrfarbige Felder | **-1,222** | [-2,341, **-0,104**] | 36 |
| Vertikale Reihen | +1,207 | [-0,363, +2,777] | 29 |
| Diagonale Reihen | +0,735 | [-0,106, +1,576] | 34 |
| Eckplatten | -0,586 | [-1,738, +0,566] | 35 |

**Lesart, mit Vorbehalt:** die Richtung passt zur Kampagne -- b01 baut mehr vertikale Reihen
(volle Spalten) und bezahlt bei den Mehrfarbigen Feldern. Aber **acht Kriterien wurden geprueft**,
und bei acht Intervallen auf 95 Prozent ist eines knapp ausserhalb der Null der Erwartungswert,
nicht der Befund. Die obere Grenze liegt bei -0,104, also hart an der Null. **Ohne den zweiten
Seed ist das keine Aussage**; wiederholt es sich dort mit demselben Vorzeichen, lohnt der
genauere Blick.

**Laufzeit:** 2.485,4 s (41 Minuten) statt der geplanten 86-91 min -- der SPRT hat nach 90 statt
200 Paaren abgebrochen, genau wozu er da ist. 13,8 s je Partie, 10 Threads.

**Der zweite Seed (20261062) laeuft.** Ein DRITTER Seed ist kein Automatismus (Regel v27, par.6).

### Training v29-b01 und eine Falle im Namensschema (2026-09-14)

**Training durch** (01:28 bis 03:00, `wanduhr_s` 5.568,8 = **1,55 h**, 12 Epochen, 4.538.842
Samples, cuda, 6 Threads). Warmstart auf `v28-b02_brierbest`, Rezept unveraendert.

**`alphazero_v29-b01_brierbest` EXISTIERT NICHT -- und das ist richtig so.** `train.py`
Z.2624-2626 schreibt den `_brierbest`-Checkpoint nur, wenn die Brier-beste Epoche weder die
letzte noch die `val_combined`-beste ist ("sonst waere er ein Duplikat"). Hier war die beste
Epoche die ZWOELFTE und damit die letzte (`value_val_brier` 0,17934, `epoch_history` im
Manifest). **Das finale Modell IST der value-optimale Stand.**

**Folge, und sie hat Zeit gekostet:** `tools/night_v29_tor1_b01.sh` wartete auf
`models/alphazero_v29-b01_brierbest.onnx` -- eine Datei, die nie entsteht. Das Skript haette
BELIEBIG LANGE gewartet, ohne Fehler, ohne Ausgabe; genau der Stillstand, der vermieden werden
sollte. Es ist am 2026-09-14 03:03 beendet und durch
`tools/night_v29_tor1_b01_final.sh` ersetzt worden (Kandidat `alphazero_v29-b01.onnx`, sonst
Wort fuer Wort derselbe Befehl, ohne Warteschleife weil die Maschine frei war).

**Der Befehl in par.6 Punkt 7 (Z.609) traegt denselben Fehler**: er nennt
`alphazero_v29-b01_brierbest.onnx`. Gemeint ist der value-optimale Stand; wie er heisst, haengt
davon ab, ob er mit dem finalen zusammenfaellt.

**REGEL fuer b02 und b03, und fuer jede kuenftige Kette:** vor einem Gating pruefen, WELCHE
Datei da ist, statt den Namen zu raten --
`ls models/alphazero_<arm>*.onnx`. Die Reihenfolge der Wahl ist
`_brierbest` (falls vorhanden) vor dem finalen Modell; `_best` ist der `val_combined`-beste und
NICHT der value-optimale. Ein Wartescript, das auf einen Namen wartet, braucht ausserdem einen
Deckel oder eine Abbruchbedingung: ein stilles Warten sieht von aussen aus wie Arbeit.

**Fenster gebaut:** Traeger-Manifest 580 (400 neu + 135 G-1 + 45 G-2), G-2-Haelfte 145 aus
`selfplay_v26-b01-value-excursion_*.pkl` (Soll 145, par.2), Fensterliste `data/window_v29.txt`
mit 2.947 Dateien, Cache-Schluessel `35c6bd2b9bd2`.

## AGENTEN-AUFTRAG (Stand 2026-09-13, fuer eine autonome Abarbeitung durch einen Opus-Agenten)

### 1. Ziel und Verdikt-Regel

Zu beantworten ist, ob ein weiterer Materialschritt (v29-b01, Rezept unveraendert) den Champion
`v28-b02` schlaegt, und welcher der drei Arme der beste Stand wird. Die Verdikt-Regel steht in
**par.6** (Tore) und `docs/generation_loop.md`: Tor 0 Traegerkennzahl aus der Kette Schritt 1
plus Tor 2a ex post gegen den Wert des v28-Generators (`corpus_sanity_v27-b01-policy.json`
0,816, par.4 Punkt 5); **Tor 1** gepaartes Gating mit `--log-games`, Blockgroesse 5, ZWEI Seeds
(Regel aus v27: kein dritter Seed, wenn beide positiv sind und kein Nullentscheid vorliegt);
**Tor 2b** aus denselben Logs (`arena_column_probe.py`), Plattenpunkte je Modell
(`plate_points_from_arena.py --block 5`), dazu die sechs Standard-Kennzahlen. Fuer **b02**
(Ablation der Spezialfeld-Kanaele) ist die Leserichtung in par.6 vorab festgelegt: verliert b02
signifikant gegen b01, TRAEGT die Eingabe; gleichauf oder b02 vorn, dann traegt sie nicht. Fuer
**b03** (Sicht-Arm) gilt par.6c mit dem Verwerfungs-Ausgang aus `PREREG_stack_top_feature.md`
par.12: Gleichstand -> Sichtstand uebernehmen (das Kriterium ist Sichtgleichheit, nicht Elo);
Regression ueber ZWEI Seeds bei Blockgroesse 5 -> Merkmal aus und Ursache suchen. Die
Netz-Gesundheit (par.6d) ist Pflichtteil der b03-Abnahme, mit eigener Lesart dort.

### 2. Voraussetzungen

- **Maschine frei laut Prozessliste** (PowerShell-Zaehler wie in `tools/night_v28_generate.sh`,
  Funktion `busy`); Ergebnis `0`. CLAUDE.md "Messungen laufen EXKLUSIV": ein Training auf der GPU
  und EIN CPU-Auftrag daneben sind erlaubt, zwei CPU-Messungen nie; jeder Build zaehlt als Last.
- **Pflichtpruefungen par.4 Punkte 1-8 abgearbeitet**, insbesondere: Wheel installiert und
  `python -X utf8 -c "import mosaic_rust as m; m.state_features_from_json"` vorhanden,
  Kontrakt-Hash im Manifest der ersten Klasse; Spec-Datei des Generators liegt
  (`models/frozen_champions/v28-b02/spec.json`); Golden-Probe des Generator-Artefakts gruen;
  Anker-Drift auf dem Start-Wheel gruen; **Manifest-Diff gegen die Referenz**
  `data/manifest_v27-b01-policy_20260910_234958.json` (jede Abweichung ausser Modell, Version,
  Seed und Datum ist ein Stopp, Feedback `lauf_manifest_gegen_referenz`).
- **Vorher durch sein muessen:** die Sims-Neumessung
  (`PREREG_search_depth_column_optimum.md` par.8e, Auswertung und Sockel-Vorschlag), die wartende
  Leiter-Kante v28-b02@100 gegen v22-b05@25, der Build des P.10-Fixes samt Record-Feld
  `tiled_max_row` (par.4 Punkt 7b) und `/mosaic-generation-turnover`.
- **Generator:** `v28-b02` (par.3, Nutzer-Entscheid 2026-09-11), Modell
  `models/alphazero_v28-b02_brierbest.onnx` (sha256-identisch mit dem Artefakt),
  Spec `models/frozen_champions/v28-b02/spec.json`.
- **Fenster-Pinning:** `MOSAIC_DATA_EXCLUDE` fuer Streudateien, darunter zwingend die
  Messdateien `data/selfplay_depth<S>-v28b02_*.pkl` (par.7 Punkt 4); Cache-Waechter unter
  `MOSAIC_IGNORE_POLICY_TARGET_VALID=1` und `MOSAIC_FEATURES_FROM_RUST=1`. Feedback
  `watcher_workers_reimport_config`: waehrend Waechter oder Kette laufen, wird
  `config.py`, `engine/py/neural_net.py`, `corpus_dataset.py` und `file_cache_key.py` NICHT
  angefasst (Vorfall 2026-09-11, 24 Bloecke unter falschem Schluessel).

### 3. Schritte

Jeder Programmpunkt hat eigene Schritte. Reihenfolge wie nummeriert.

**P1 -- Schwarm-Erzeugung v29 (FREIGEGEBEN, par.8 Punkt 8; Sockel spaeter)**

1. `/mosaic-generation-turnover` vollstaendig durchlaufen (Maschine frei, Einfrieren,
   daily-Snapshot mit restic-Beleg, Namen reservieren in `docs/generation_naming.md`,
   STATUS-Neufassung). **Loeschliste des Nutzers erst NACH dem Start des Self-Plays** (STATUS
   Abschnitt 1, Verbote), und nur mit pfadgenauer Freigabe.
2. Ketten-Skript `tools/night_v29_generate.sh` nach dem Muster von `tools/night_v28_generate.sh`
   anlegen (mit Warte-Schleife `busy`, Datei-Zaehler je Klasse, Abbruch-Waechter aus
   `night_v28_chain_resume.sh` und `night_v28_b02.sh`), aber NUR mit den beiden
   value-only-Befehlen (par.8 Punkt 8: der Policy-Befehl wartet):

   ```
   python -u self_play.py --mode network --model models/alphazero_v28-b02_brierbest.onnx \
     --spec models/frozen_champions/v28-b02/spec.json \
     --games 4000 --sims 100 --value-only --version v28-b02-value-tempc \
     --threads 11 --chunk 10 --per-file 10 --seed 20260921 \
     --action-temp 2 --deviate-prob 1.0

   python -u self_play.py --mode network --model models/alphazero_v28-b02_brierbest.onnx \
     --spec models/frozen_champions/v28-b02/spec.json \
     --games 4000 --sims 100 --value-only --version v28-b02-value-excursion \
     --threads 11 --chunk 10 --per-file 10 --seed 20260922 \
     --excursion-prob 1.0 --tau-argmax-from-move 1 --no-root-noise
   ```

   Dazu der Startkuppel-Streuknopf `MOSAIC_START_SLOT_RANDOM_P=0.15` je Spieler (par.6b,
   Koordinator-Wahl im Nutzer-Rahmen). Start als Hintergrundaufgabe, OHNE Pipe und OHNE
   Umleitung (CLAUDE.md "Lange Laeufe NIE in eine Pipe"); `python -u` ist im Befehl.
   **Dauer (gemessen an v28, `docs/measured_runtimes.md` Abschnitt Generation v28):** tempc
   11.632,4 s = 3h 14m, excursion 11.361,3 s = 3h 09m, zusammen rund 6,4 h.
   **Bei Abbruch:** nur den fehlenden Tail nachziehen (`--games <Rest>`, `--seed base + fertige
   Chunks`, Projekt-Erinnerung `selfplay_tail_resume_by_chunk_seed`), NICHT den ganzen Block neu;
   Ausnahme, wenn der Suchalgorithmus zwischendrin gewechselt hat.
3. Daneben (erlaubt, weil er zur Erzeugung gehoert) der Cache-Waechter:
   `MOSAIC_IGNORE_POLICY_TARGET_VALID=1 MOSAIC_FEATURES_FROM_RUST=1 python -X utf8 -u tools/build_cache_incremental.py --data-dir data --encoder 2d --value-target-variant nortv --workers 3 --watch --wartezeit 60 --leerlauf-abbruch 100000`
4. **Tor 0 / Tor 2a ex post** nach jeder Klasse:
   `python -X utf8 tools/corpus_sanity_check.py data --pattern "selfplay_v28-b02-value-tempc_*.pkl" --out evaluations/artifacts/corpus_sanity_v28-b02-value-tempc.json`
   (gemessen 270,7 s fuer 4.000 Partien, 1 Thread, `docs/measured_runtimes.md`).

**P2 -- Sockel (ZURUECKGESTELLT, Nutzer-Entscheid offen)**

5. **Schritt "Zuschnitt registrieren und Nutzer fragen":** die Sims des Sockels und die Maschine
   sind NICHT entschieden (par.8 Punkt 8: "vermutlich auf der schnelleren Maschine"). Der Agent
   legt den Kosten-Vorschlag aus `PREREG_search_depth_column_optimum.md` par.8e vor, registriert
   den gewaehlten Zuschnitt HIER in par.9 und startet nichts. Der Befehl liegt in par.5 Nr. 1
   (Seed 20260920, `--tau-argmax-from-move 1 --deviate-prob 1.0`); bei geaenderten Sims ist die
   Zeile hier mit der neuen Zahl zu registrieren, bevor sie laeuft.

**ENTSCHIEDEN (Nutzer 2026-09-13, 11:50): der Sockel faehrt 400 SIMS**, woertlich "Die 100 sims
fuer den sockel sind nicht entschieden. Ich nehm 400 und push die policy ein wenig." Der Befehl
in par.5 Nr. 1 ist damit mit `--sims 400` zu fahren (Seed 20260920 unveraendert), auf der
schnelleren Maschine des Nutzers; Kosten 8,29 h statt 4,40 h fuer 4.000 Partien. **Der Schwarm
bleibt bei 100 Sims** (Freigabe 02:10), das v29-Fenster mischt also bewusst zwei Betriebspunkte:
der policy-tragende Teil tiefer gesucht, der value-tragende Schwarm flacher und billiger.
Begruendung des Nutzers ist die Zielqualitaet, nicht die Zustandsverteilung -- das in par.8e
notierte Gegenargument gegen den Koordinator-Vorschlag.

**Ueberholter Vorschlag des Koordinators (04:15, zur Nachvollziehbarkeit): Sockel mit 100 Sims,
wie der Schwarm.** Die Sims-Kurve am Champion ist
durchgemessen (`PREREG_search_depth_column_optimum.md` par.8e). Fuer den KORPUS faellt sie
monoton: volle Spalten je Seite 1,0975 / 0,9575 / 0,8950 / 0,8200 bei 100 / 200 / 400 / 600 Sims
(n = 200 argmax-Self-Play-Partien je Punkt, Grundmenge 400 Seiten, @100 gegen @400 z = +3,74).
Der Staerke-Teil derselben Messung zeigt Saettigung bei 400, aber fuer die ERZEUGUNG ist nach der
vorab festgelegten Lesart Teil B zustaendig, fuer die BEWERTUNG Teil A. Kosten fuer 4.000
Partien aus den gemessenen Sekunden je Partie: @100 4,40 h, @200 5,82 h, @400 8,29 h,
@600 11,74 h. Der teurere Betriebspunkt liefert also den spaltenaermeren Korpus.

**Folge fuer Tor 0 und Tor 2a, jetzt der EINGETRETENE Fall (ABLEITUNG, nicht gemessen):** der
Sockel bei 400 zieht die Bezugswerte NACH UNTEN, nicht nach oben. Der
Bezugswert von par.6 ist 0,816 volle Spalten je Seite aus `corpus_sanity_v27-b01-policy.json`
(v28-Generator). Die Sims-Kurve misst dieselbe Groesse, aber in einer anderen BETRIEBSART
(argmax ohne Wurzelrauschen statt policy-aktiv mit Rauschen und Temperatur): die Betraege sind
deshalb nicht direkt vergleichbar, uebertragbar ist allein die RICHTUNG. **Ein niedrigerer Wert als 0,816 ist beim
Sockel also erwartbar und allein KEIN Torriss** -- wer das Tor liest, nennt die Sim-Zahl dazu.
Der Schwarm bei 100 Sims behaelt dagegen die Betriebsart des Bezugswerts.

**P3 -- Kette und Arm b01 (Pflichtarm)**

6. `tools/night_v29_chain.sh` nach dem v28-Muster: Manifest je Klasse, G-2-Kennzahlen, Fenster
   (Seed **20260941**, Val-Pool `^selfplay_v29-`), Bloecke, Monolith mit Formen-Waechter,
   Training. **G-2-Haelfte:** `G2_SWARM_PATTERN` erst nach dem Nutzer-Entscheid setzen (par.2,
   Vorschlag Ausflug-Haelfte `selfplay_v26-b01-value-excursion_*`) -- siehe Stopp-Punkte.
   Dauer gemessen: Kette Schritte 2-6 rund 5 min bei vorliegenden Bloecken, Monolith-Merge
   531-551 s, Training 12 Epochen 5.156,6 s = 1,43 h (`docs/measured_runtimes.md`).
7. **Tor 1 b01 gegen den Champion** (= Generator v28-b02, beide Seiten Champion-Spec), zwei
   Seeds, Blockgroesse 5, Logs:

   ```
   python -X utf8 -u tools/paired_gating.py \
     --model-a models/alphazero_v29-b01_brierbest.onnx --spec-a models/frozen_champions/v28-b02/spec.json \
     --model-b models/alphazero_v28-b02_brierbest.onnx --spec-b models/frozen_champions/v28-b02/spec.json \
     --name-a v29-b01 --name-b v28-b02 --sims-a 400 --sims-b 400 --c-puct 1.5 \
     --block-size 5 --max-pairs 200 --seed <SEED> --threads 10 --log-games \
     --no-promote-winner --out evaluations/artifacts/paired_gating_v29-b01_vs_v28-b02_s<SEED>.json
   ```

   Dauer gemessen: 200 Paare @400 mit Logs 5.182-5.446 s = 86-91 min je Seed
   (`docs/measured_runtimes.md`).
8. **Tor 2b und Plattenpunkte** auf denselben Logs:
   `python -X utf8 -u tools/probes/arena_column_probe.py --artifact <ARTEFAKT>` (83-108 s) und
   `python -X utf8 -u tools/plate_points_from_arena.py <ARTEFAKT> --block 5` (unter 10 s).

**P4 -- Arm b02 (Ablation der Spezialfeld-Kanaele 77/78, ENTSCHIEDEN par.6)**

9. **Bau:** Schalter `MOSAIC_SPECIAL_PLANES_OFF` (Name vorlaeufig, Registratur-Eintrag Pflicht)
   im Rust-Merkmalsbauer und im Python-Zwilling. Betroffene Stellen laut par.6:
   `engine/src/features.rs:1149` `SPECIAL_YIELD_CHANNEL = 77`, `:1160`
   `SPECIAL_UNLOCK_DISTANCE_CHANNEL = 78` (beide Pfade), Zwilling
   `engine/py/neural_net.py`; der Schalter ist Teil des Cache-Schluessels.
   **Reihenfolge Bau -> Tore -> Messung.** Tore, in dieser Folge (Muster
   `tools/night_v28_knob_build.sh`, gemessen 84 s / 33 s / 34 s / 19 s / 12 s):
   Python-DLL in den PATH (`$env:PATH = "$(python -c 'import sys,os;print(os.path.dirname(sys.executable))');" + $env:PATH`),
   `cargo test --release --lib`, `cargo test --release --no-run` (examples/benches),
   `python -m maturin build --release` plus `pip install --force-reinstall --no-deps`,
   **Paritaetstor mit Schalter AN**, Netz-Paritaets-Fixture des Champions UNVERAENDERT bei
   Schalter aus, `/mosaic-anchor-invariance` (Drift und Konservierung; der Anker ist netzlos und
   muss gruen bleiben), `python -X utf8 tools/generate_knob_docs.py` und
   `python -X utf8 tools/check_conventions.py`.
10. Bloecke fuer das ganze Fenster neu unter dem Planes-Schluessel (gemessen 1.582 s = 26 min bei
    6 Workern, Rust-Merkmalsbauer), Monolith neu (9 min), Training wie b01.
11. **Tor 1 b02 gegen b01**, zwei Seeds, Befehl wie Schritt 7 mit `--model-a` b02 und
    `--model-b` b01. Diagnostik vorregistriert (par.6): Plattenpunkte je Kriterium mit
    Erwartung "Zuwachs GENAU im Posten Spezialfelder", plus
    `python -X utf8 -u tools/probes/special_tile_yield_measurement.py` (Grundmenge Arena-Partien,
    Einheit ausgeloeste untere Spezialfelder je Seite).

**P5 -- Arm b03 (Sicht-Arm, Abschnitt 16)**

12. Bau und Tore stehen in `PREREG_stack_top_feature.md` par.15 / Abschnitt 16 und in deren
    AGENTEN-AUFTRAG; hier nur die Einordnung: der Encoder-Anbau ist ein **Wheel-Wechsel** und
    gehoert in ein Fenster OHNE Erzeugung, Waechter oder Kette (par.4 Punkt 6). Vorschlag par.6c:
    im Generationswechsel NACH der Sims-Neumessung und VOR dem Start der Erzeugung; Alternative
    nach dem Ende der Erzeugung vor dem Training. Danach Pflichtpruefung par.4 Punkte 2/3 mit dem
    NEUEN Kontrakt-Hash und einer neuen Manifest-Referenz.
13. Bloecke neu, Training wie b01, **Tor 1 b03 gegen b01** mit zwei Seeds (Befehl wie Schritt 7).
14. **Netz-Gesundheit (par.6d, PFLICHTTEIL der b03-Abnahme, auch an b01 als Bezug):**
    (1) Spaltennormen von `flat_branch.0.weight` fuer die neuen Indizes (755..) gegen die
    Altspalten -- Einzeiler am Checkpoint, kein Werkzeug noetig;
    (2) tote ReLU-Einheiten der ersten Flachschicht und des Rumpfs auf dem Frozen-Set, b03 gegen
    b01 gegen Champion; Werkzeug existiert NICHT (geprueft 2026-09-13: kein Treffer fuer
    dead/activation in `tools/`), Bau rund eine Stunde als `tools/probes/dead_unit_probe.py`;
    Schwelle vorab: mehr als das Doppelte des b01-Anteils ist ROT;
    (3) `python -X utf8 -u tools/offline_diagnosis.py` und `python -X utf8 -u tools/oracle_metrics.py`
    b03 gegen b01 auf demselben Val-Split (Aufloesungsgrenze value_r2 rund 0,015);
    (4) `python -X utf8 -u tools/probes/value_head_reliability_probe.py` und
    `python -X utf8 tools/platt_fit.py` (Brier auf frozen_v3) -- Brier darf nicht ueber den
    b01-Wert steigen;
    (5) Trendtabelle ueber v24-b04 (744), v28-b02 (755) und v29-b03 (794/812).
    Alle fuenf ohne Suche, Minuten je Modell, **nie neben einer Arena**.

**P6 -- Begleitprogramm (par.7)**

15. Die eingetakteten Punkte laufen in den CPU-freien Fenstern und haben je eine eigene Prereg
    mit eigenem AGENTEN-AUFTRAG: Schwierigkeitsleiter (`PREREG_difficulty_levels.md`),
    Ziehsucht-Sonde und Zugklassen-Differential (`PREREG_claude_play_interface.md` par.9/par.10),
    Korpus-Verhaltens-Audit (`PREREG_corpus_behaviour_audit.md`), Tiling im Blatt
    (`PREREG_round_transition_search_sampling.md` par.9), Mondstapel Stufe 1
    (`PREREG_moon_stack_order.md` par.4), Rueckgabe-Reihenfolge (`PREREG_dome_return_order.md`
    par.5), Rundenschaetzer (`PREREG_round_estimate_leaf_term.md` par.5), Stapelziehen bei
    positivem Stand (`PREREG_stack_draw_reservation_rule.md` par.7 und `PREREG_chance_nodes.md`
    par.14 Teil B1). Reihenfolge nach Maschinenlage, aber: **keine zwei CPU-Laeufe gleichzeitig**.

### 4. Auswertung und Registrierung

- **Zahlen mit n, Grundmenge, Einheit**: Tor 1 "n = 400 Partien (200 Paare) je Seed, Grundmenge
  gepaarte Arena-Partien, Einheit Siege"; Tor 2b "n = replaybare Partien, Grundmenge
  Arena-Partien, Einheit volle Spalten je Seite"; Tor 2a "n = 8.000 Seiten, Grundmenge
  Self-Play-Seiten, Einheit volle Spalten je Seite". Auswertung auf **Block-Ebene**
  (Blockgroesse 5).
- **Die sechs Standard-Kennzahlen** je Arm und als Differenz (CLAUDE.md), zusaetzlich fuer b02
  die Spezialfeld-Kennzahlen aus Schritt 11 und fuer b03 die fuenf Gesundheitspunkte.
- **Ergebnisse in par.9 dieser Datei** eintragen, den **Zeile-1-Kopf im selben Zug** nachziehen
  (Ueberholtes ersetzen, unter rund 600 Zeichen), danach sofort
  `python tools/generate_prereg_index.py`.
- **STATUS.md Abschnitt 1** und `archive/history.md` fortschreiben; pruefen, ob ein ANDERER
  STATUS-Abschnitt dadurch falsch wird (CLAUDE.md Pflegeregel).
- **Rueckwaerts-Pruefung**: `grep -rn "v29-b01\|v29-b02\|v29-b03\|v29_window" evaluations/ docs/ tools/`
  -- jede Fundstelle lesen.
- **Laufzeiten** je Lauf ins Artefakt (`laufzeit`-Block mit `wanduhr_s`, `cpu_s`, `threads`,
  `s_je_partie`), Planungsgroessen nach `docs/measured_runtimes.md` unter einem neuen Abschnitt
  "Generation v29".
- **Elo-Register**: nur Kanten AM CHAMPION eintragen (Gating-Kante, Anker-Kante, Champion-2-Kante
  nach `docs/promotion_checklist.md`), je mit `--units-from-paired-artifact` und `--early-stop`,
  falls frueh gestoppt wurde. Arm-gegen-Arm-Kanten ohne Champion-Bezug gehoeren nicht hinein.

### 5. Stopp-Punkte fuer den Nutzer

- **G-2-Haelfte (par.2, par.8 Punkt 1) ist NICHT entschieden.** Vorschlag ist die Ausflug-Haelfte;
  der Agent setzt `G2_SWARM_PATTERN` erst nach ausdruecklicher Antwort. **Nutzer fragen.**
- **Sockel: Sims und Maschine** (par.8 Punkt 8) -- Vorschlag vorlegen, nicht starten.
- **Start der Erzeugung** ist grundsaetzlich freigabepflichtig (par.8 Punkt 4); die Freigabe vom
  2026-09-13, 02:10 deckt AUSSCHLIESSLICH den Schwarm mit 100 Sims.
- **Champion-Wechsel** nur ueber `/mosaic-champion-promotion` und `docs/promotion_checklist.md`;
  kein `set_champion` aus eigenem Antrieb.
- **Anker-Drift ROT: anhalten.** ROT heisst Nutzer-Entscheid (Anker bewusst neu setzen oder
  Aenderung zuruecknehmen), nie Reparatur (CLAUDE.md).
- **Aufnahme eines Knopfs ins Rezept** (Rueckgabe-Reihenfolge, Rundenschaetzer, Tiling im Blatt,
  Mondstapel) ist Nutzer-Entscheid, auch bei positivem A/B.
- **Loeschungen** (Loeschliste aus STATUS Abschnitt 1, alte Manifeste, Messdateien) nur auf
  pfadgenaue Freigabe und erst nach dem Start des v29-Self-Plays.
- **Kein Push**; Ahead-Stand melden.

### 6. Abhaengigkeiten und Reihenfolge

**Vorher:** Sims-Auswertung (`PREREG_search_depth_column_optimum.md` par.8e), wartende
Leiter-Kante, Build P.10-Fix und `tiled_max_row`, `/mosaic-generation-turnover`.
**Reihenfolge der Arme** (par.6c): b01 in der Kette, b02 und b03 danach auf demselben Fenster mit
je eigenen Bloecken, Tor 1 je Arm gegen b01, der beste gegen den Champion.
**Danach:** Promotion nach `docs/promotion_checklist.md` (Champion-2-Kante gegen das Artefakt
`v27-b01`), dann die Kanten der Schwierigkeitsleiter (par.7 Punkt 1: NACH Tor 1 v29), dann v30
mit ausschliesslich Rezept-Knoepfen und der Projektabschluss (par.8 Punkt 3).
**Das Begleitprogramm par.7 laeuft parallel in den CPU-freien Fenstern**, nie neben einer Arena;
seine Verdikte gehen ins v30-Rezept.
