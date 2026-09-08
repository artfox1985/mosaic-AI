<!-- STATUS: OFFEN | Frage: Wie wird das v26-Trainingsfenster zugeschnitten, jetzt wo die Rotation zum ERSTEN MAL vollstaendig aus eigenem Material besteht? | Beleg: nichts gemessen, nichts gebaut. Zuschnitt hergeleitet aus PREREG_v25_window.md par.17 (stationaerer Zustand) mit den tatsaechlichen Dateizahlen der v24-b07-Erzeugung; hv2 faellt erstmals ganz heraus. Offen ist praktisch nur der Val-Pool-Regex; Sockelgroesse und Klassengewichte sind durch par.18 der v25-Prereg bis v27 eingefroren (Nutzer-Berichtigung 2026-09-08). Vor dem Zuschnitt faellig: Traeger-Kennzahl der drei v24-b07-Klassen messen. -->

# PREREG v26: Fensterzuschnitt

**Vorlage ist `PREREG_v25_window.md` par.17** ("Der stationaere Zustand, wenn alles
durchrotiert ist"). v26 ist die erste Generation, in der dieser Zustand ERREICHBAR wird,
weil G-1 zum ersten Mal die Zwei-Haelften-Struktur des Schwarms mitbringt. Vollstaendig
stationaer ist erst v27.

## par.1 ZUSCHNITT (hergeleitet, nicht entschieden)

G = v25, G-1 = v24-b07, G-2 = v23-b01.

**Sockel (Policy-Klasse, Traeger)**

| Posten | Quelle | Dateien | Partien |
| --- | --- | --- | --- |
| Sockel NEU | v25-Self-Play, policy-aktiv | 400 | 4.000 |
| aus G-1 | 135 der 400 `selfplay_v24-b07-policy_*` (seed-bestimmt) | 135 | 1.350 |
| aus G-2 | 45 der 400 `selfplay_v23-b01-policy_*` (seed-bestimmt) | 45 | 450 |
| **Summe** | | **580** | **5.800** |

**Schwarm (Value-Klasse, policy-maskiert)**

| Posten | Quelle | Dateien | Partien |
| --- | --- | --- | --- |
| Schwarm NEU | v25, temperiert plus Ausfluege | 800 | 8.000 |
| Schwarm G-1, Haelfte a | alle 400 `selfplay_v24-b07-value-tempc_*` | 400 | 4.000 |
| Schwarm G-1, Haelfte b | alle 402 `selfplay_v24-b07-value-excursion*_*` | 402 | 4.004 |
| Sockel-Rest G-1 | die 265 uebrigen `selfplay_v24-b07-policy_*` | 265 | 2.650 |
| Sockel-Rest G-2 | 355 der `selfplay_v23-b01-policy_*` | 355 | 3.550 |
| Schwarm G-2 | 145 der 800 `selfplay_v23-b01-value-*` | 145 | 1.450 |
| **Summe** | | **2.367** | **23.654** |

**Fenster gesamt 2.947 Dateien, 29.454 Partien** -- dieselben Groessen wie v25
(2.947 / 29.804), die Zusammensetzung ist eine andere.

## par.2 DER MEILENSTEIN: hv2 faellt heraus

**v26 ist das erste Fenster ohne den plattenblinden Lehrer.** hv2 war G-2 in v25 und
waere in v26 G-3 -- ausserhalb der Rotation. Damit besteht das Fenster erstmals
vollstaendig aus Netz-Self-Play, und zwar aus drei Generationen, die alle den
Huellen-Knopf kannten.

Das ist die Bedingung, unter der [[feedback_dont_calibrate_to_plate_blind_play]] ueberhaupt
erfuellbar wird: solange 545 hv2-Dateien im Fenster lagen, war ein Teil des Wertmaterials
per Konstruktion plattenblind.

## par.3 WAS SICH DADURCH AN DER TRAEGER-KENNZAHL AENDERT

Die Traeger-Kennzahl (volle Spalten je Seite, gemittelt ueber die Policy-Klasse) steigt,
weil die G-1-Traeger zum ersten Mal aus einer Erzeugung mit Umschaltpunkt 1 und Weg C
stammen statt aus voller Temperatur:

| Generation | 4.000 neu | 1.350 aus G-1 | 450 aus G-2 |
| --- | --- | --- | --- |
| v25 | v24-b07, greedy + Weg C | v23-b01-policy, **volle Temperatur** | hv2 |
| **v26** | v25, greedy + Weg C | **v24-b07-policy, greedy + Weg C** | v23-b01-policy, volle Temperatur |

**UNGEMESSEN.** Die Zahlen fuer die einzelnen Klassen liegen nicht vor; Messung 3-V hat
0,5325 fuer das Rezept gemessen, nicht fuer diesen Korpus. **Vor dem v26-Zuschnitt gehoert
die Traeger-Kennzahl der drei v24-b07-Klassen gemessen** (`tools/probes/`-Sonden auf den
fertigen Korpora, keine neue Erzeugung noetig).

## par.4 WAS ENTSCHIEDEN WERDEN MUSS -- fast nichts (Nutzer-Berichtigung 2026-09-08)

**Hier standen zuerst zwei Fragen, die es nicht gibt:** ob der Sockel bei 4.000 bleibt und
ob die Ausflug-Klasse als G-1 hoeher gewichtet gehoert. **Beide sind durch
`PREREG_v25_window.md` par.18 bereits entschieden** -- von v25 bis v27 aendert sich nur das
MATERIAL, nicht die Regel. Nutzer dazu: *"ich dacht wir wollen mal konsistent das fenster
ziehen bis v27."*

Der Widerspruch war nicht harmlos: waere die Zusammensetzung zwischen v25 und v26
verschoben worden, waeren die drei Generationen nicht mehr vergleichbar, und der einzige
Zweck des Einfrierens -- eine saubere Attribution, wenn nur noch das Netz sich aendert --
waere weg. Genau davor warnt par.18 im letzten Absatz.

**Es bleibt EIN Punkt, und der ist reine Buchfuehrung:**

1. **Der Val-Pool** wandert auf `^selfplay_v25-`. Kein Ermessen, aber eine stille
   Fehlerquelle: er gehoert in den Kopf der Kette, nicht in die Erinnerung. In v25 war der
   Wechsel von `^selfplay_v24-b06-` auf `^selfplay_v24-b07-` faellig und ist nur deshalb
   nicht vergessen worden, weil er in par.19 stand.

**Die Zuteilung der Rollen folgt mechanisch aus der Rotation** (par.1): 4.000 neue Traeger,
1.350 aus G-1, 450 aus G-2, alles Uebrige maskiert. Die seedbestimmten Teilauswahlen laufen
wie in v25 ueber `tools/generate_carrier_manifest.py --include-glob` fuer die neue Klasse
und `--pick` fuer die beiden aelteren.

## par.5 WAS NICHT NEU ENTSCHIEDEN WERDEN MUSS

Erzeugungsrezept (Umschaltpunkt 1 + Weg C fuer den Sockel; glatte Temperatur + Weg C und
Weg B fuer die beiden Schwarm-Haelften), Trainingsrezept, Ziehungsregel der Abweichung,
Blockgroesse 5 in jeder Arena, die beiden Tor-Flaechen. Alles registriert und unveraendert.

**Eine Korrektur aus v25 gilt fort:** `--games` zaehlt bei Weg B die Ausfluege MIT
(par.19a dort). Fuer 4.000 Identitaeten der Ausflug-Haelfte also `--games 4000`.

## par.6 WAS FUER v27 VORGEMERKT IST (Nutzer 2026-09-08)

Nicht Teil des v26-Zuschnitts, aber hier notiert, damit es beim naechsten
Generationswechsel nicht neu gefunden werden muss.

1. **Schwarm G-2: EINE Haelfte, kein Split.** Ab v27 rutscht `v24-b07` auf G-2, und dort
   stehen die temperierte Haelfte und die Ausflug-Haelfte nebeneinander fuer einen Posten
   von 1.450 Partien (145 Dateien). **Nutzer-Entscheid: kein Split** -- 145 Dateien auf
   zwei Klassen aufgeteilt machen aus zwei klaren Beitraegen zwei zu kleine. Welche der
   beiden, wird GEMESSEN, nicht geraten: `tools/probes/corpus_state_diversity_probe.py`
   (distinkte Belegungsmuster je Runde, distinkte Endbretter) und
   `paired_corpus_divergence_probe.py` auf den beiden fertigen Korpora. Aufruf mit der
   `pfad::glob`-Form, Minuten statt Stunden, keine neue Erzeugung.
   **Koordinator-Vorurteil, ausdruecklich als solches:** die temperierte Haelfte, weil
   Abdeckung die Rolle von G-2 ist und der Vorteil der Ausfluege -- unverzerrte Wertziele
   -- dort am staerksten wiegt, wo das Material die aktuelle Wertschaetzung traegt.
2. **Sichtgleichheit, Reststufen** (`PREREG_stack_top_feature.md`): laufende Ziehserie,
   Phasenaufloesung, und ein Netz, das die in b04 gelegten Werte auch nutzt. Der Anlass
   jener Prereg (Stapel-Rueckseite) ist mit b04 geschlossen; diese drei sind es nicht.

## par.7 DIE ERZEUGUNGSBEFEHLE FUER v26 (Generator v25-b01, Nutzer 2026-09-08)

**Generator ist `v25-b01`**, unabhaengig davon, ob er Champion wird -- Generatorwahl und
Promotion sind zwei Entscheidungen (`docs/generation_loop.md`). Belegt ist "nicht
schlechter" ueber 240 Partien mit p 0,0015 (gepoolt aus zwei Gating-Laeufen).

**Die Spec bleibt `models/v24-b07_brierbest.spec.json`** und bekommt bewusst KEINE Kopie
unter neuem Namen: sie ist nach par.18 der v25-Prereg bis v27 eingefroren, und eine zweite
Datei mit gleichem Inhalt waere die Einladung, sie auseinanderlaufen zu lassen.

```
# 1) Traeger, 4.000 Partien -- policy-aktiv
python -u self_play.py --mode network --model models/alphazero_v25-b01_brierbest.onnx   --spec models/v24-b07_brierbest.spec.json --games 4000 --sims 100   --version v25-b01-policy --threads 11 --chunk 10 --per-file 10 --seed 20260911   --tau-argmax-from-move 1 --deviate-prob 1.0

# 2) Schwarm Haelfte a, 4.000 Partien -- value-only, breite Abdeckung
python -u self_play.py --mode network --model models/alphazero_v25-b01_brierbest.onnx   --spec models/v24-b07_brierbest.spec.json --games 4000 --sims 100 --value-only   --version v25-b01-value-tempc --threads 11 --chunk 10 --per-file 10 --seed 20260912   --action-temp 2 --deviate-prob 1.0

# 3) Schwarm Haelfte b, 4.000 Identitaeten -- value-only, unverzerrte Ziele
python -u self_play.py --mode network --model models/alphazero_v25-b01_brierbest.onnx   --spec models/v24-b07_brierbest.spec.json --games 4000 --sims 100 --value-only   --version v25-b01-value-excursion --threads 11 --chunk 10 --per-file 10 --seed 20260913   --excursion-prob 1.0 --tau-argmax-from-move 1 --no-root-noise
```

**`--games 4000` in Nr. 3, nicht 2000** -- die Korrektur aus `PREREG_v25_window.md`
par.19a: der Ausflug hat eine eigene `game_id` und zaehlt gegen `--games`. In v25 hat der
erste Lauf deshalb nur 2.002 statt 4.000 Identitaeten geliefert und musste aufgefuellt
werden. Erwartete Dauer nach den gemessenen v25-Werten: rund 4,0 h fuer Nr. 1 (3,61 s je
Partie), 3,5 h fuer Nr. 2 (3,19 s auf der zweiten Maschine), 3,5 h fuer Nr. 3
(3,14 s je Identitaet).

**Cache-Waechter nur fuer Nr. 1** (`tools/cache_build_socket.sh` mit der Dateiliste der
Sockel-Klasse): die Traeger-Klasse ist policy-tragend, ihr Schluessel stimmt schon ohne
Traeger-Manifest. Fuer die value-only-Klassen entstehen die Bloecke erst mit dem
v26-Manifest.

**BERICHTIGUNG 2026-09-09 (an der Primaerquelle geprueft):** die Einschraenkung "nur
Nr. 1" ruht auf einer ueberholten Annahme. **Der Traegerstatus ist seit 2026-08-31 NICHT
mehr Teil des Datei-Schluessels** (`engine/py/file_cache_key.py:29-47`,
Nutzer-Auftrag): der Block ist traegeragnostisch, die Traeger-Maske wird erst beim
Zusammenfuegen des Fensters angewandt (`build_cache_parallel.merge(..., mask_parts=...)`).
Die einzige praefixabhaengige Groesse im Schluessel ist `bootstrap_native`, und
`selfplay_v25-b01-*` steht in keiner der `LEGACY_STRETCHED_PREFIXES`
(`engine/py/neural_net.py:837-839`) -- fuer alle drei Klassen ergibt sich derselbe
Schluessel. **Der Waechter darf also ueber alle drei Klassen laufen**, nicht nur ueber die
Sockel-Klasse; `--file-list` ist ohnehin nicht mit `--watch` kombinierbar
(`tools/build_cache_incremental.py:258`). Gefahren wird er als
`build_cache_incremental.py --watch --workers 3 --encoder 2d --value-target-variant nortv`
ohne `MOSAIC_CARRIER_MANIFEST` (Vorgabe leer, "jede Datei traegt").

