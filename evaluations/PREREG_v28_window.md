<!-- STATUS: OFFEN | Frage: Wie wird das v28-Trainingsfenster zugeschnitten -- die erste Generation NACH dem Einfrieren, mit Record-Feld fuer den Kuppelstapel-Wissensstand und zwei Armen (b01 Rezept fest, b02 Variante B)? | Beleg: nichts gebaut. Zuschnitt aus PREREG_v25_window.md par.17 auf v28 fortgeschrieben (580 Traeger + 2.366 Schwarm, Seed 20260937, Val-Pool ^selfplay_v27-), Generator v27-b01 (Champion, Tor 1 und 2 gehalten). Voraussetzung: Record-Feld dome_pool_view (par.4) im Wheel, Anker-Drift gruen. Offen: G-2-Haelfte (par.2), Freigabe der Erzeugung (Nutzer, v28 ausgesetzt seit 2026-09-10). -->

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

## par.2 WELCHE G-2-HAELFTE (offen, Nutzer)

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
