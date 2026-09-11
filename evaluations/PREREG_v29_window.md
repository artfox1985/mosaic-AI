<!-- STATUS: OFFEN | Frage: Wie wird das v29-Trainingsfenster zugeschnitten -- der zweite Zyklus nach dem Einfrieren, Generator = Sieger der v28-Promotion, Pflichtarm b01 mit unveraendertem Rezept? | Beleg: nichts gefahren. Zuschnitt rotiert aus v28 (580 Traeger + rund 2.367 Schwarm, Seed 20260941, par.1). v29-b02 ENTSCHIEDEN: Ablation der Spezialfeld-Kanaele 77/78 (par.6; die Kanaele sind seit e91cd34 gebaut, ihre Wirkung nie isoliert); Begleitprogramm par.7 (Leiter, Ziehsucht, Stapel-Stopp-Regel, Peek-Bewertung, Startkuppel, Sims-Kurve). Offen: G-2-Haelfte (par.2), letzte Generation?, Freigabe. -->

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

## par.2 WELCHE G-2-HAELFTE (Vorschlag, Nutzer-Entscheid)

`v26-b01` rutscht auf G-2; der Posten von 145 Dateien traegt EINE Haelfte (v26-Prereg par.6:
kein Split). v27 nahm die temperierte Haelfte (Rolle "Abdeckung"), v28 die Ausflug-Haelfte
(auf den Zahlen: spaltenreichste Klasse, doppelte Recordzahl je Datei). **Vorschlag: wieder
die Ausflug-Haelfte** (`selfplay_v26-b01-value-excursion_*`, 401 Dateien, 145 seed-gezogen
mit 20260941), aus denselben Gruenden wie in v28 und damit die beiden Fenster nach dem
Einfrieren dieselbe Regel tragen. Die temperierte v26-Haelfte rotiert dann ersatzlos hinaus.
Offen bis zum Nutzer-Entscheid; die Kette bekommt `G2_SWARM_PATTERN` erst danach.

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
8. **Namen reserviert** in `docs/generation_naming.md` (v29-b01; weitere nur mit eigener
   Registrierung), Ketten-Skripte `tools/night_v29_generate.sh` und `tools/night_v29_chain.sh`
   nach dem v28-Muster INKLUSIVE der Abbruch-Waechter aus `night_v28_chain_resume.sh` und
   `night_v28_b02.sh`.

## par.5 DIE ERZEUGUNGSBEFEHLE FUER v29 (Vorlage, Start nur auf Anweisung)

Seeds 20260920 / 20260921 / 20260922 (v28 nahm 17-19). `<GEN>` = Name des Generators
(par.3), `<SPEC>` = `models/frozen_champions/<GEN>/spec.json`, Modell aus dem Artefakt.

```
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
3. **Reste aus v28**, falls dort nicht mehr gefahren: Startkuppel-Sonde Stufe 0 (am v28- ODER
   v29-Korpus, gleiches Instrument), Ueberraschungs-Kante v24-b05 gegen v24-b04,
   `round_estimate_leaf_term` als Such-Knopf am Champion-Stand. Jeder davon ist ein
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
     faellig, weil INPUT_SIZE 744 -> 755 ein Aera-Wechsel ist): drei Punkte 100/250/400 wie in
     par.8b, dazu 150/200; rund eine Stunde; Betriebspunkt der Erzeugung bleibt 100, solange das
     Plateau steht.
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
3. Ist v29 die letzte Generation? Dann gilt: Leiter-Endfassung mit dem v29-Champion
   (`PREREG_difficulty_levels.md` Stufe 5), Generationswechsel ohne v30-Vorlage, und
   STATUS-Neufassung als Abschlussbericht. Sonst v30 nach demselben Muster.
4. Freigabe der Erzeugung (Regel seit 2026-09-03: die Fenstererzeugung startet nur auf
   Anweisung).

## par.9 ERGEBNISSE (leer bis zum Start)

Nichts gefahren (Stand 2026-09-11, 17:35).
