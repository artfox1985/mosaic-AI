<!-- STATUS: OFFEN | Frage: Wie wird das v28-Trainingsfenster zugeschnitten -- die erste Generation NACH dem Einfrieren, mit Record-Feld fuer den Kuppelstapel-Wissensstand und zwei Armen (b01 Rezept fest, b02 Variante B)? | Beleg: Erzeugung GEFAHREN 2026-09-10/11 (par.10: 3 x 4.000 Partien @100, 35.726 s = 9,9 h, Generator v27-b01). TOR 2a HAELT: 0,816 gegen 0,777 volle Spalten je Seite (n = 8.000 Seiten, +-0,017). Fenster 2.947 Dateien (580 Traeger + 145 G-2 Ausflug), Schluessel 2db448af20fe; Training v28-b01 laeuft in der Kette. Offen: Tor 1 b01, dann b02 (Variante B, par.9), Ablationen, Sonde, Kante, round_estimate (par.8). -->

# PREREG v28: Fensterzuschnitt und der erste Plan nach dem Einfrieren

**Vorlage ist `PREREG_v27_window.md`** (Zuschnitt par.1, Entscheide par.2/par.3, Befehle par.5)
und der stationaere Zustand aus `PREREG_v25_window.md` par.17. **v28 ist die erste Generation
nach dem Einfrieren** (`PREREG_v25_window.md` par.18: v25-b01 bis v27-b01 mit festem Rezept;
Ende mit der Promotion von v27-b01 am 2026-09-10). Sie hat deshalb zwei Arme: einen mit dem
unveraenderten Rezept als Fortsetzung der Materialkette, und einen mit der ersten Aenderung
am Netz seit v24.

**Nutzer-Stand:** v28-Self-Play ist ausgesetzt (2026-09-10, 13:25); dieser Zuschnitt ist die
Vorlage, die Erzeugung startet nur auf Anweisung.

## par.1 ZUSCHNITT (hergeleitet, Bestandszahlen geprueft am 2026-09-10)

G = v28-Erzeugung durch `v27-b01`, G-1 = `v26-b01` (400 / 400 / 401 Dateien), G-2 = `v25-b01`
(400 / 400 / 401). `v24-b07` faellt aus der Rotation.

**Sockel (Policy-Klasse, Traeger)**

| Posten | Quelle | Dateien | Partien |
| --- | --- | --- | --- |
| Sockel NEU | v28-Erzeugung, policy-aktiv | 400 | 4.000 |
| aus G-1 | 135 der 400 `selfplay_v26-b01-policy_*` (seed-bestimmt) | 135 | 1.350 |
| aus G-2 | 45 der 400 `selfplay_v25-b01-policy_*` (seed-bestimmt) | 45 | 450 |
| **Summe** | | **580** | **5.800** |

**Schwarm (Value-Klasse, policy-maskiert)**

| Posten | Quelle | Dateien | Partien |
| --- | --- | --- | --- |
| Schwarm NEU | v28, temperiert plus Ausfluege | rund 801 | rund 8.000 |
| Schwarm G-1, Haelfte a | alle 400 `selfplay_v26-b01-value-tempc_*` | 400 | 4.000 |
| Schwarm G-1, Haelfte b | alle 401 `selfplay_v26-b01-value-excursion_*` | 401 | 4.010 |
| Sockel-Rest G-1 | die 265 uebrigen `selfplay_v26-b01-policy_*` | 265 | 2.650 |
| Sockel-Rest G-2 | 355 der `selfplay_v25-b01-policy_*` | 355 | 3.550 |
| Schwarm G-2 | 145 der 400 `selfplay_v25-b01-value-<Haelfte>_*` (par.2) | 145 | 1.450 |
| **Summe** | | **rund 2.367** | **rund 23.660** |

**Fenster gesamt rund 2.947 Dateien** (v27: 2.947). Die Ausflug-Klassen liefern 400 oder 401
Dateien; nicht ausgeglichen.

**SEED der seedbestimmten Auswahlen UND des Trainings: 20260937** (Regel seit 2026-09-10,
`docs/generation_loop.md`: je Generation neu im Vierer-Schritt, alle Arme einer Generation
gleich; v27 hatte 20260933). **Val-Pool `^selfplay_v27-`.**

## par.2 WELCHE G-2-HAELFTE (entschieden 2026-09-10)

`v25-b01` rutscht auf G-2; der Posten von 145 Dateien traegt EINE Haelfte (v26-Prereg par.6:
kein Split). Fuer v27 fiel der Entscheid auf die temperierte Haelfte, auf der Rolle
"Abdeckung", weil das gemessene Vielfaltskriterium nicht trennte (`PREREG_v27_window.md`
par.2). Seitdem liegt ein weiterer Datenpunkt vor: im v27-Fenster ist die Ausflug-Klasse
die spaltenreichste (0,858 volle Spalten je Seite), die temperierte die aermste (0,463;
par.7 dort). Beide Lesarten stehen: Abdeckung (temperiert) gegen Wertziele aus
spaltenreichem, unverzerrtem Material (Ausflug). **Empfehlung des Koordinators: diesmal die
Ausflug-Haelfte** -- G-1 liefert beide Haelften ohnehin vollstaendig, der G-2-Posten ist mit
1.450 Partien klein, und die Ausflug-Haelfte bringt bei gleicher Dateizahl die doppelte Zahl
an Records (`PREREG_v27_window.md` par.2). Kandidatenmuster dann
`selfplay_v25-b01-value-excursion_*.pkl` (401), sonst `-value-tempc_*` (400).

**ENTSCHIEDEN 2026-09-10, 23:40 (Nutzer): die AUSFLUG-Haelfte.** *"dann machen wir das so."*
Der G-2-Schwarm besteht aus 145 der 401 `selfplay_v25-b01-value-excursion_*`, seed-gezogen
mit 20260937; `tools/night_v28_chain.sh` steht bereits so (`G2_SWARM_PATTERN`). Die
temperierte v25-b01-Haelfte rotiert ersatzlos hinaus. Damit hat jede Generation ihre eigene
G-2-Wahl (v27: temperiert auf der Rolle; v28: Ausflug auf den Zahlen), und der Vergleich
der beiden Fenster ist ein Nebenbefund, keine Messung.

## par.3 WER ERZEUGT (hergeleitet, keine Wahl)

`v27-b01` ist Champion mit Tor 1 (59:31 SPRT, 222:178) und Tor 2 auf beiden Flaechen
(`PREREG_v27_window.md` par.9/par.10); nach `docs/generation_loop.md` erzeugt der beste Stand
der Vorgeneration. Klassen: `selfplay_v27-b01-policy_*`, `-value-tempc_*`,
`-value-excursion_*`. Spec bleibt `models/v24-b07_brierbest.spec.json` (kein Spec-Entscheid
nach dem Einfrieren registriert; die Datei ist identisch mit der Spec im Artefakt v27-b01).

**Die Engine ist NICHT mehr die von v27** (bewusst, das Einfrieren ist beendet): die
Wurzel-Determinisierung kennt die eigenen Rueckgabe-Bloecke (Variante A,
`PREREG_dome_stack_information_sets.md` par.15), die erzwungene Abweichung schliesst den
Suchzug aus (`PREREG_start_position_seeding.md` par.9l), und das Record traegt
`dome_pool_view` (par.4). Anker-Drift war nach jedem der Schritte gruen. Die v28-Klassen sind
damit nicht bitgleich mit einer Erzeugung des alten Wheels; das ist registriert und
gewollt.

## par.4 RECORD-FELD `dome_pool_view` (Voraussetzung fuer Variante B)

Merkmale koennen nur lernen, was im Record steht. Die Records von v25 bis v27 tragen das
Frontend-JSON ohne Wissensstand ueber den Stapel; ein Merkmal fuer den eigenen Block waere
dort ueberall null. Deshalb VOR der Erzeugung: `serialize::state_to_json` bekommt
`dome_pool_view`, aus Sicht des Spielers am Zug, sichtkonform nach
`PREREG_dome_stack_information_sets.md` par.4 und dem Entscheid par.14 Punkt 3:

```
"dome_pool_view": {"unknown_prefix": k,
                   "blocks": [{"own": true,  "len": 8, "special": 3, "wild": 5, "types": ["wild", ...]},
                              {"own": false, "len": 2, "special": 1, "wild": 1, "types": null}]}
```

Eigene Bloecke mit Reihenfolge der Typen (der Rueckgeber hat sie gewaehlt), fremde nur als
Zaehler (Fronten lagen offen, Reihenfolge nicht), Praefix nur als Laenge. Kein Merkmal, kein
Cache-Schluessel, kein Kontrakt-Hash aendert sich dadurch; Variante B liest das Feld spaeter
im Training (`neural_net.py`, additiv, INPUT_SIZE 744 -> 744 + k). Bau: Agentenauftrag
2026-09-10 (Rust plus Toleranz der Python-Leser), danach Wheel, Anker-Drift, Rauchtest mit
`self_play.py --games 2`.

## par.5 DIE ERZEUGUNGSBEFEHLE FUER v28 (Vorlage, Start nur auf Anweisung)

Seeds 20260917 / 20260918 / 20260919 (v27 nahm 14-16). Skripte `tools/night_v28_generate.sh`
und `tools/night_v28_chain.sh` nach dem v27-Muster; Cache-Waechter zwingend unter
`MOSAIC_IGNORE_POLICY_TARGET_VALID=1`.

```
# 1) Traeger, 4.000 Partien -- policy-aktiv
python -u self_play.py --mode network --model models/alphazero_v27-b01_brierbest.onnx   --spec models/v24-b07_brierbest.spec.json --games 4000 --sims 100   --version v27-b01-policy --threads 11 --chunk 10 --per-file 10 --seed 20260917   --tau-argmax-from-move 1 --deviate-prob 1.0

# 2) Schwarm Haelfte a, 4.000 Partien -- value-only, breite Abdeckung
python -u self_play.py --mode network --model models/alphazero_v27-b01_brierbest.onnx   --spec models/v24-b07_brierbest.spec.json --games 4000 --sims 100 --value-only   --version v27-b01-value-tempc --threads 11 --chunk 10 --per-file 10 --seed 20260918   --action-temp 2 --deviate-prob 1.0

# 3) Schwarm Haelfte b, 4.000 Identitaeten -- value-only, unverzerrte Ziele
python -u self_play.py --mode network --model models/alphazero_v27-b01_brierbest.onnx   --spec models/v24-b07_brierbest.spec.json --games 4000 --sims 100 --value-only   --version v27-b01-value-excursion --threads 11 --chunk 10 --per-file 10 --seed 20260919   --excursion-prob 1.0 --tau-argmax-from-move 1 --no-root-noise
```

**Kosten, gemessen an v27** (`docs/measured_runtimes.md`): Erzeugung 36.912 s = 10,25 h
(v26: 8,35 h; Ursache des Unterschieds nicht gemessen, mit der langsameren Zahl planen),
Kette 31 min, Training rund 1,4 h je Arm, Gating 86 min je vollem Lauf mit Logs.
Neu zu erwarten in der Ausflug-Klasse: die `[excursion] VERWORFEN`-Rate steigt leicht
(par.9l: leerer Kandidatenpool nach Ausschluss des Suchzugs); Rate im Manifest nachsehen und
hier eintragen (par.9k-Messung wiederholen: Anteil Ausfluege ohne Abweichung, Soll nahe 0).

## par.6 ARME UND TORE (der erste Plan nach dem Einfrieren)

| Arm | Was | Faktor gegen | Seed |
| --- | --- | --- | --- |
| **v28-b01** | Rezept UNVERAENDERT (Warmstart v27-b01, 12 Epochen, lr 5e-05 cosine, lambda 0,7, Koepfe wie gehabt) | v27-b01: nur das Material (4. Punkt der Materialkette) | 20260937 |
| **v28-b02** | Variante B: Merkmale aus `dome_pool_view` (eigener Block: Laenge, Zaehler, Typenfolge der obersten m; fremde Bloecke: Laenge und Zaehler; Praefix), additiv nach der 2D-Encoder-Regel | b01: EIN Faktor, das Merkmal | 20260937 |

Reihenfolge: b01 zuerst (Kette), dann b02 auf demselben Fenster und Monolith (Cache-Schluessel
aendert sich mit dem Merkmal, Bloecke werden fuer b02 neu gebaut, rund 30 min mit 6 Workern).

**Tore** (`docs/generation_loop.md`): Tor 0 Traegerkennzahl (Kette Schritt 1; Tor 2a ex post
gegen 0,777), Tor 1 gepaartes Gating mit `--log-games` (Tor 2b kommt aus denselben Partien,
`arena_column_probe.py`), Blockgroesse 5, zwei Seeds, Replikation bei Fruehstopp unter 150
Paaren. Kanten: b01 gegen v27-b01; b02 gegen b01; der bessere gegen den Champion, falls das
nicht schon dieselbe Kante ist. Promotion nach `docs/promotion_checklist.md`, Champion-2 gegen
das Artefakt v26-b01.

**Diagnostik, vorregistriert:** auf den Tor-1-Logs von b02 gegen b01 die Sonde
`dome_stack_known_block_draw_probe.py`: Ziehungen in den eigenen bekannten Block bei
POSITIVEM Stand je Partie (`dome_stack` par.15f). Erwartung: b02 zieht dort SELTENER als b01
(der Value-Kopf sieht, was er kennt), bei gleicher oder besserer Staerke. Bleibt die Zahl
gleich, traegt das Merkmal nicht; steigt sie mit besserer Staerke, ist Ziehen richtig und
par.8 der Kuppelstapel-Prereg endgueltig UEBERHOLT. Standard-Kennzahlen aus
`plate_points_from_arena.py` (je Modell, seit 2026-09-10).

## par.7 WAS DANACH ANSTEHT (Zeiger, nicht vorregistriert)

1. **Sicht-Reststufen** (`PREREG_stack_top_feature.md` par.10 P.3/P.7, par.11): laufende
   Ziehserie (Typen in `pending_stack_draw` sind bereits im JSON) und Phasenaufloesung als
   Merkmal-Arm v28-b03, falls b02 traegt; sonst bleibt die Frage, ob Merkmale der zweiten
   Achse ueberhaupt ankommen.
2. **Offene Preregs schliessen, ohne neue Erzeugung:** `policy_surprise_weighting` (Kante
   v24-b05 gegen v24-b04, beide Modelle im restic-Repo, ein Gating-Lauf), `round_estimate_leaf_term`
   (Skalenentscheid a/b, Nutzer), `start_dome_choice` (Stufe 0 als Sonde am v28-Korpus),
   `round_transition_search_sampling` (in `dome_stack` aufgehen lassen oder UEBERHOLT).
3. **Denial-Hebel** (`docs/generation_loop.md`, Abschnitt Richtung je Generation): erst, wenn
   Spalten oder Punkte saettigen; v27 liegt bei 1,0 Spalten je Seite in der Arena und 53
   Punkten, die Saettigung (1-2 Spalten, 100 Punkte) ist nicht erreicht.
4. **Claude-Partien g02-g10** laufen parallel als Beobachtungsquelle; ihre Befunde werden zu
   Sondenkandidaten, nicht zu Armen.

## par.8 DAS v28-PROGRAMM, VERBINDLICH (Nutzer 2026-09-11, 00:10)

Nutzer-Wortlaut: *"bau das alles so ein mit den bauschritt aus der prereg rust_data_layer.
ansonsten weiter mit deinem vorschlag fuer die reihenfolge -> b01, b02 Variante B, dann die
zwei Ablationen, parallel dazu die Sonde Startkuppel und die Ueberraschungs-Kante. dann takte
den round_estimate_leaf_term noch an einer passenden stelle ein."*

**Variante B, Merkmalsdefinition (v28-b02), elf Werte additiv ans Ende des Flachvektors,
Sicht des Spielers am Zug, Quelle `dome_pool_view`:** unbekanntes Praefix (Laenge, 1);
eigener Block gesamt (Laenge, Spezial-, Wild-Zaehler, 3); Typen der obersten vier Positionen
des obersten eigenen Blocks (+1 Spezial, -1 Wild, 0 leer, 4); fremde Bloecke gesamt (Laenge,
Spezial, Wild, 3). INPUT_SIZE 744 -> 755. Alt-Records ohne Feld liefern Nullen; Alt-ONNX
bleiben spielbar (`net.rs::build_inputs` kuerzt). **Bauschritt aus `PREREG_rust_data_layer.md`
par.2 (Teil A):** das Merkmal wird EINMAL in `features.rs` gebaut, per pyo3 exportiert
(`state_features_from_json`, `state_planes_from_json`), der Python-Zwilling in `neural_net.py`
wird nachgezogen und dient als Test-Orakel; Tor: Bit-Identitaet beider Bauer
(`tools/probes/feature_parity_rust_python.py`, `np.array_equal`, keine Toleranz) VOR der
Umstellung des Blockbaus auf Rust (Schalter `MOSAIC_FEATURES_FROM_RUST`, nicht im
Cache-Schluessel). Netz-Paritaets-Fixture des Champions muss unveraendert gruen bleiben
(744-Modell, gekuerzt). Bau: Agentenauftrag 2026-09-11, 00:15; danach Wheel, Anker-Drift,
Paritaetswerkzeug, dann Bloecke fuer das v28-Fenster unter dem neuen Schluessel (INPUT_SIZE ist
Teil des Cache-Materials), dann Training b02 (Warmstart `v27-b01_brierbest`, Seed 20260937,
sonst wie b01).

**Reihenfolge und Kosten (Planung nach `docs/measured_runtimes.md`):**

| Schritt | Was | Kosten |
| --- | --- | --- |
| 1 | `v28-b01`, Rezept fest (Kette, laeuft seit 2026-09-10 23:49) | 10,3 h Erzeugung + 2 h |
| 2 | Tor 1 b01 gegen v27-b01, zwei Seeds mit Logs (Tor 2b inklusive) | 2 x 86 min |
| 3 | `v28-b02`, Variante B (Bloecke neu, Training, Tor 1 gegen b01 zwei Seeds; Diagnostik `dome_stack_known_block_draw_probe` auf den Logs, par.6) | 30 min + 1,4 h + 2 x 86 min |
| 4 | Ablationen: `v28-b03` = Fenster OHNE die neue Ausflug-Klasse (rund 401 Dateien weniger), `v28-b04` = Fenster OHNE den G-2-Posten (45 + 355 + 145 = 545 Dateien weniger); Rezept wie b01, Seed 20260937, Weglassen ohne Ersatz (Fenstergroesse ist damit Teil des Effekts, registriert); je Tor 1 gegen b01, ein Seed, zweiter nur bei Fruehstopp | je 1,3 h + 86 min |
| 5 | parallel zu 3/4, wenn die Maschine zwischen zwei Laeufen frei ist: Sonde Startkuppel Stufe 0 am v28-Korpus (`PREREG_start_dome_choice.md` par.4, Spannweite ueber die neun Slots; nur der Slot-Teil, Verdikt eingegrenzt nach dem Nachtrag dort) | Minuten |
| 6 | Ueberraschungs-Kante: `v24-b05` gegen `v24-b04`, beide aus dem restic-Repo (`run:v24-b05`, `run:v24-b04`) in einen Sammelordner zurueckgeholt, gepaartes Gating mit `models/k3v_off.spec.json` auf beiden Seiten (die Fassung OHNE Knopf, in der b05 seinen SPRT-Befund hatte, `PREREG_v24_window.md` par.9 Zeile v24-b05), 200 Paare, Blockgroesse 5 | 86 min |
| 7 | `round_estimate_leaf_term`: Such-Knopf am Champion-Stand nach b02 (Bau nach par.3 dort, Skala (a) je Runde 3/8/10/12 aus par.4; Koordinator-Vorschlag, Nutzer kann auf (b) 9,25 wechseln), A/B gleiches Netz Live gegen Artefakt wie bei Variante A, zwei Seed-Basen | Bau + 2 x 43 min |

Nach Schritt 7 sind von den acht offenen Preregs `round_estimate_leaf_term`,
`start_dome_choice`, `policy_surprise_weighting` und `rust_data_layer` (Teil A) mit Verdikt
versehen; `round_transition_search_sampling` geht in `dome_stack` auf (UEBERHOLT), `stack_top`
haengt am Ausgang von b02. Ziel "rund 7 OFFEN" ist damit erreichbar.

## par.9 BAUSTAND VARIANTE B (2026-09-11, 00:15-00:50) und die Zurueckstellung der Python-Seite

**Gebaut (Opus-Agent, gegengelesen):** elf Werte an den Indizes 744..754 (Praefix /18; eigener
Block Laenge /18, Spezial /9, Wild /9; Typen der obersten vier Positionen des obersten eigenen
Blocks +1/-1/0; fremde Bloecke Laenge /18, Spezial /9, Wild /9; Konstanten
`dome::NUM_DOME_TILE_DESIGNS` 18 und neu `dome::NUM_SPECIAL_DOME_TILES` 9, gegen den Katalog
getestet). Beide Rust-Pfade (`features.rs`, Abschnitt 15) und der Python-Zwilling
(`neural_net.py`, Alt-Records elf Nullen); pyo3-Export `state_features_from_json` und
`state_planes_from_json` (`lib.rs`); Schalter `MOSAIC_FEATURES_FROM_RUST` (Default aus, nicht
im Cache-Schluessel); Paritaetswerkzeug `tools/probes/feature_parity_rust_python.py`
(ungelaufen, braucht das Wheel). INPUT_SIZE 744 -> 755 (`features.rs`, `config.py`),
Merkmals-Fixture neu, **Kontrakt-Hash 20b442a8164f748d -> c65768636c0560a7**: kuenftige
Anker- und Champion-2-Kanten gegen die Artefakte v25-v27 laufen Cross-Aera (`--force-cross-era`,
Regel vom 2026-08-29). Tests gezielt gruen (features 22, dome_pool_knowledge 11, contract 3,
examples/benches gebaut).

**Zwei Dinge, die der Bau aufgedeckt hat.** (1) Die Netz-Paritaets-Fixture war seit Commit
`56fd9f2` (Record-Feld `dome_pool_view`) rot: der Hash liest den Record-Zustand mit, das neue
Feld aendert ihn (b5188b25e073a1c0 statt 5e3b1362ddc65fa6); Gegenprobe des Agenten ohne das Feld
liefert exakt den alten Hash, kein Zugwechsel. Fixture am 2026-09-11 bewusst neu erzeugt (unten).
(2) **Die Python-Seite darf erst NACH dem Training von `v28-b01` in den Baum**: die laufende
Kette importiert `config.py`/`neural_net.py` beim Blockbau (Schritt 5) und beim Training
(Schritt 7); mit INPUT_SIZE 755 wuerde b01 ein 755-Modell mit den v28-Blockmerkmalen, also
kein "Rezept unveraendert" mehr. Deshalb liegen `config.py` und `engine/py/neural_net.py` in
`git stash` (stash@{0}, "Variante B Python-Seite"), der Baum steht auf 744; die Rust-Seite bleibt
im Baum, wird aber erst nach der Kette zum Wheel gebaut. Reihenfolge: Kette durch -> Tor 1 b01
-> `git stash pop` -> Wheel -> Anker-Drift -> Paritaetswerkzeug -> Bloecke unter neuem Schluessel
-> Training b02.

## par.10 ERGEBNISSE DER GENERATION (fortlaufend)

**Erzeugung (2026-09-10, 23:49:56 bis 2026-09-11, 09:45:31; Laufzeit-Bloecke in
`data/manifest_v27-b01-*.json`, threads 11, Cache-Waechter daneben, Claude-Partien der
Parallelsitzung daneben):**

| Klasse | Partien | Dateien | Wanduhr | s je Partie |
| --- | --- | --- | --- | --- |
| Traeger `v27-b01-policy` (Weg C, argmax ab Halbzug 1) | 4.000 | 400 | 12.732,4 s = 3h 32m | 3,183 |
| Schwarm `v27-b01-value-tempc` (Temperatur 2, Weg C) | 4.000 | 400 | 11.632,4 s = 3h 14m | 2,908 |
| Schwarm `v27-b01-value-excursion` (Ausflug, 4.005 Identitaeten) | 4.005 | 401 | 11.361,3 s = 3h 09m | 2,837 |
| zusammen | 12.005 | 1.201 | **35.726,1 s = 9,92 h** | (v27: 36.911,5 s; 3 % schneller, Ursache nicht gemessen) |

**Tor 2a ex post (Kette Schritt 1, `evaluations/artifacts/corpus_sanity_v27-b01-policy.json`,
Instrument `tools/corpus_sanity_check.py`, Grundmenge Policy-Klasse, n = 8.000 Seiten aus
4.000 Partien, Einheit volle Spalten je Seite): v27-b01 als Generator 0,816 (+-0,017) gegen
v26-b01 als Generator 0,777 (+-0,017, `corpus_sanity_v26-b01-policy.json`). HAELT.**
Nebenzahlen derselben Datei: volle Zeilen 0,112 (v26: 0,122), Punkte 46,34 je Seite,
Strafleiste 6,07. Die Reihe der Generatoren am selben Instrument: v24-b07 0,637, v25-b01
0,737, v26-b01 0,777, v27-b01 0,816.

**Kette (Schritte 2-6, 10:04:18 bis 10:04:23):** Traeger-Manifest 580 = 400 neu + 135 G-1 +
45 G-2 (`data/policy_carrier_manifest_v28.json`); Schwarm G-2 145 aus
`selfplay_v25-b01-value-excursion_*.pkl` (par.2); `data/window_v28.txt` 2.947 Dateien
(Soll rund 2.946); Bloecke lagen alle (Waechter: 3.203 von 3.203, INPUT_SIZE 744);
Fenster-Schluessel `2db448af20fe`.

**Zwischenfall Monolith (10:13):** der Merge starb mit `Can't broadcast (1661, 755) -> (1661, 744)`.
24 Bloecke (`selfplay_v27-b01-policy_20260911_0014_g410.pkl` bis `_0028_g640.pkl`, Blockdateien
00:15-00:29) trugen `states` mit 755 Spalten unter 744er-Schluesseln: der Schluessel liest
`config.INPUT_SIZE` im Elternprozess des Waechters (seit 23:49 auf 744), die Worker importieren
`config.py` je Start frisch, und die Datei stand 00:15-00:50 fuer den Variante-B-Bau (par.9) auf
755, bevor sie in den Stash ging. Die Kette startete Schritt 7 trotz Merge-Fehler; das Training
starb nach 26 s (KeyError `values` im halben Monolithen). Behebung: 24 Bloecke in eine
Nachbardatei neu gebaut, je auf 744 Spalten und gleiche Zeilenzahl geprueft, per `os.replace`
eingesetzt (112 s); Gesamtscan danach 3.203 Bloecke x 744, keine Abweichung. Dauerhaft:
Formen-Waechter in `build_cache_parallel.merge` (bricht VOR dem Schreiben ab), Kette stoppt bei
Merge-Fehler (`tools/night_v28_chain_resume.sh`). Rezept unveraendert, Seed 20260937, Fenster
und Schluessel identisch. Monolith 1.102.756.306 Byte, Merge 10:20-10:29 mit Formen-Waechter.

**Training v28-b01 DURCH (10:29:07-11:55:09, Exit 0):** Rezept fest (Warmstart
`v27-b01_brierbest`, 12 Epochen, lr 5e-05 cosine, lambda 0,7, Seed 20260937), Manifest
`models/manifest_train_v28-b01_20260911_102910.json`: Laufzeit 5.156,6 s (Datenaufbau 33,5 s,
4.431.025 Zustaende, 17.308 Batches je Epoche), restic-Marke `run:v28-b01`. `_brierbest` ist
**Epoche 3** (val_brier 0,1802, Val-Pool `^selfplay_v27-`), `_best` nach val_combined Epoche 1,
Plateau ab Epoche 10, Policy-Val 0,39 am Ende. ONNX `models/alphazero_v28-b01_brierbest.onnx`
(flat_input 744). Wie bei v27 (Epoche 3) liegt der Bestpunkt frueh; die Brier-Werte sind
ueber die Arme nicht vergleichbar (anderer Val-Pool), die Entscheidung faellt in Tor 1.

**Tor 1 (gestartet 2026-09-11, 12:05; `tools/night_v28_tor1.sh`):** v28-b01 gegen v27-b01 aus
dem eingefrorenen Artefakt, beide Seiten Champion-Spec `frozen_champions/v27-b01/spec.json`,
@400, Blockgroesse 5, 10 Threads, `--log-games`, Deckel 200 Paare, Seeds 20261036 und
20261037 nacheinander. Regel wie v27 (par.9 dort): kein dritter Seed, wenn beide Seeds fuer
b01 liegen und kein Nullentscheid faellt. Ergebnis folgt hier.
