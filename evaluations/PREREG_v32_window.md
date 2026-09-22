<!-- STATUS: OFFEN | Frage: Wie wird das v32-Fenster zugeschnitten, und traegt der erste Arm? | Beleg: par.1 Zuschnitt steht (neu v31-b01, G-1 v30-b02, G-2 v29-b11, Seed 20260953, Val-Pool ^selfplay_v31-). par.6 REZEPT ENTSCHIEDEN (Nutzer 2026-09-22 "Einstellungen wie v31"): Erzeugung unveraendert bis auf Generator, Seeds 20260938/39/40 und den Spec-Namen; Dosis 0,81 bleibt, obwohl die Gelegenheitsrate von 17,75 auf 28,0 Prozent gestiegen ist -- bewusst. Training ein Arm v32-b01, Warmstart. Erzeugung laeuft seit 2026-09-22. -->

# Vorregistrierung: das v32-Fenster

**Angelegt 2026-09-22** im Generationswechsel v31 -> v32 (Nutzer: *"du faehrst v32"*), nach dem
Ablauf `/mosaic-generation-turnover`. Die Generation v31 ist abgeschlossen: `v31-b01` hat Tor 1
getragen (461:339 aus 800, Block-z +4,24) und ist seit dem 2026-09-20 Champion.

**Diese Datei ist beim Anlegen UNVOLLSTAENDIG und soll es sein.** par.1 ist mechanisch aus der
Rotationsregel herleitbar und steht darum schon; par.6 traegt Entscheide, die dem Nutzer gehoeren.
Der Ablauf verlangt beide VOR dem Start der Erzeugung.

## par.1 ZUSCHNITT (Rotationsregel, Bestand am 2026-09-22 gezaehlt)

G = v32-Erzeugung durch **`v31-b01_brierbest`**; G-1 = `v30-b02` (die v31-Erzeugung);
G-2 = `v29-b11` (die v30-Erzeugung). **`v28-b02` ist aus der Rotation gefallen** und am
2026-09-22 mit pfadgenauer Freigabe geloescht (1.201 Dateien, 1,34 GB; restic-Beleg im Snapshot
`bb2d8bad`, 1.201 Treffer).

**Die Generatorwahl ist hier ohne Konkurrenz:** v31 hatte EINEN Arm. Die Stufenregel aus
`docs/generation_loop.md` ("Generatorwahl unter Armen") greift erst ab zwei Kandidaten; es gilt
die Grundregel "Generator = bester Stand von N-1", und der ist zugleich Champion.

| Generation | Klasse | Dateien | Partien | Policy-Ziel |
| --- | --- | --- | --- | --- |
| `v31-b01` (neu) | policy | noch zu erzeugen | | **ja** |
| `v31-b01` (neu) | value-tempc | noch zu erzeugen | | nein |
| `v31-b01` (neu) | value-excursion | noch zu erzeugen | | nein |
| `v30-b02` (G-1) | policy | 400 | 4.000 | Anteil offen |
| `v30-b02` | value-tempc | 400 | 4.000 | nein |
| `v30-b02` | value-excursion | 401 | 4.010 | nein |
| `v29-b11` (G-2) | policy | 400 | 4.000 | Anteil offen |
| `v29-b11` | value-tempc | 400 | 4.000 | nein |
| `v29-b11` | value-excursion | 401 | 4.010 | nein |

**Im Baum liegen damit heute 2.404 Altdateien** (gezaehlt 2026-09-22), dazu kommen die neuen
Klassen. Die Seed-Ziehung fuer die Traeger-Anteile der Alt-Klassen (bei v31: 135 von 400 bzw. 45
von 400) folgt dem Muster aus `PREREG_v31_window.md` par.1 und wird beim Fensterbau festgelegt.

**SEED: 20260953** (Vierer-Schritt aus `docs/generation_loop.md`: v29 20260941, v30 20260945,
v31 20260949).
**Val-Pool `^selfplay_v31-`** -- das Muster trifft ausschliesslich die neuen Klassen.

## par.2 TORE

Wie `PREREG_v31_window.md` par.2, solange par.6 nichts anderes festlegt. **Tor 1** gegen den
besten Stand der eigenen Linie (`v31-b01`), **Tor 2a** `sp_voll` der neuen Klassen gegen die des
Vorgaengers, **Tor 2b** Replay-Kontrolle.

## par.3 EIN UNTERSCHIED ZU ALLEN FRUEHEREN FENSTERN, der benannt gehoert

Die Alt-Klassen `v30-b02` und `v29-b11` sind unter dem Wheel **1.0.0 oder frueher** erzeugt
worden, die neuen Klassen laufen unter **1.1.0**. Dazwischen liegt die Berichtigung des
Tiling-Cache-Schluessels (`PREREG_code_cleanup_closeout.md` par.8h): bis 1.0.0 warf der Schluessel
zwei Haende mit derselben Chip-Multimenge in anderer Reihenfolge zusammen, sobald mehr als
`CHIP_ALLOC_CAP` (14) Chips gehalten wurden.

**Was das ist und was nicht:** ein Fehler in der MEMOISIERUNG, nicht in der Spielregel -- betroffen
ist, welches Tiling-Ergebnis aus dem Cache kommt, nicht welche Zuege legal sind. Der Kontrakt
(`6ef829e564c58bd5`) ist unveraendert, der Anker reproduziert seinen Referenzlauf Zug fuer Zug.
Die Haeufigkeit des Regimes ist UNGEMESSEN.

**Folge fuer dieses Fenster:** die drei Generationen im Fenster sind nicht unter bitgleichen
Engines entstanden. Das ist kein Aera-Bruch im Sinne der Elo-Leiter (der Anker haelt), aber es
gehoert in den Bericht, statt still hingenommen zu werden. Wer aus diesem Fenster eine Aussage
ueber Merkmals-Wirkungen zieht, hat diesen Unterschied als Nebenfaktor.

## par.6 REZEPT: UNVERAENDERT WIE v31 (Nutzer-Entscheid 2026-09-22)

**Nutzer: *"Das brauchst nicht von mir. Du faehrst die Einstellungen wie v31."*** Damit sind die
fuenf offenen Punkte in einem Zug entschieden: es wird nichts variiert.

### Erzeugung

`tools/night_v32_generate.sh`, Fortschreibung der am selben Tag geloeschten
`night_v31_generate.sh` (Git-Historie). **Genau drei Dinge sind geaendert:**

| | v31-Erzeugung | **v32-Erzeugung** |
| --- | --- | --- |
| Generator | `alphazero_v30-b02_brierbest.onnx` | **`alphazero_v31-b01_brierbest.onnx`** |
| Seeds (Sockel / tempc / Ausflug) | 20260934 / 35 / 36 | **20260938 / 39 / 40** |
| Spec-Datei | `models/v30_generation.spec.json` | **`models/v31_generation.spec.json`** |

Die Spec ist **byte-identisch** (sha256 `4a3f9db3...`), nur nach dem GENERATOR benannt, damit das
Lauf-Manifest selbsterklaerend ist. Inhalt unveraendert: `envelope_hull_form 2`,
`envelope_projection_mode 1`, `envelope_profile [1,0; 0,92; 0,67; 0,33; 0,0]`,
`score_utility_b 20`, `special_row6_w 1`, `start_by_search 1`, `return_order_mode 1`,
`heuristik_variante hv1`, alles uebrige 0.

Alles andere steht wie in v31: 3 x 4.000 Partien, 100 Sims, 11 Threads, `--chunk 10`,
`--per-file 10`, `--start-slot-random-p 0.15`; Sockel `--tau-argmax-from-move 1 --deviate-prob 1.0`,
Schwarm a `--action-temp 2 --deviate-prob 1.0`, Schwarm b
`--excursion-prob 1.0 --tau-argmax-from-move 1 --no-root-noise`. Der Seed-Schritt von 4 je
Generation ist derselbe wie beim Fenster-Seed (v30 fuhr 20260930/31/32).

### Die Dosis bleibt 0,81 -- als Entscheidung, nicht als Versehen

`--return-order-random-p 0.81` steht unveraendert in allen drei Klassen. **Der Vorbehalt dazu ist
registriert und wird hier nicht weggelassen:** die 0,81 sind an der v30-Erzeugung geeicht (17,75
Prozent der Partien mit Gelegenheit, Ziel "15 Prozent mindestens einmal"). An der v31-Erzeugung
gemessen sind es **28,0 Prozent** (`PREREG_dome_return_order.md` par.13, Nachtrag 2026-09-22).
Bei gleicher Dosis streut v32 also in deutlich mehr Partien als die 15 Prozent, fuer die 0,81
gerechnet wurde; hergeleitet laegen rund **0,54** an.

**Der Nutzer hat "Einstellungen wie v31" entschieden, nachdem dieser Punkt vorgelegt war.** Die
hoehere Streurate ist damit gewollt. Fuer die Auswertung heisst das: der Anteil gestreuter
Rueckgaben in v32 ist NICHT mit dem in v31 vergleichbar, obwohl die Dosis gleich ist -- die
Gelegenheitsrate hat sich bewegt, nicht der Knopf.

### Training

Ein Arm, **`v32-b01`**, **WARMSTART von `v31-b01_brierbest`**, sonst rezeptgleich zu v31-b01. Der
Kaltstart ist in v30 einfaktoriell widerlegt (404:396 kalt gegen 443:297 warm bei sonst gleichem
Fenster, Monolith, Seed und Rezept, `PREREG_v30_window.md` par.9). Ein zweiter Arm braeuchte einen
benannten Faktor und eine eigene Registrierung (`docs/generation_naming.md`).

## par.7 PFLICHTPRUEFUNGEN VOR DEM START

Aus dem Ablauf, unveraendert:

* **Manifest-Diff gegen die Referenz** -- das erzeugte `cli_args` gegen das der v31-Erzeugung
  halten. Ein fehlendes Flag meldet sich nicht, es ist ein Default
  (`feedback_run_manifest_gegen_referenz`).
* **Erster Record der neuen Erzeugung aufmachen** und nachweisen, dass die Knoten und Felder
  darin stehen, die getragen werden sollen -- dieselbe Wiedervorlage wie bei P.12/P.16
  (`feedback_record_field_must_precede_generation`).
* **Stack-Draw-Kontrolle** und **Tor 0**.
* **Fenster-Pinning** (`MOSAIC_DATA_EXCLUDE`) setzen, damit Streudateien, die waehrend des Laufs
  entstehen, nicht still ins Fenster laufen (`feedback_window_pinning_during_generation`).
* **Wheel installiert, Kontrakt-Hash im Manifest.** Stand 2026-09-22: Wheel **1.1.0**,
  Hash `6ef829e564c58bd5`, Anker-Drift gruen ueber 1.763 Schritte.
* **Plattenplatz.** Nach der Loeschung am 2026-09-22 liegt `data/` bei 4,6 GB; die neuen Klassen
  brauchen rund 1,3 GB plus Bloecke.

## par.8 KOSTEN (aus `docs/measured_runtimes.md`, damit der Start planbar ist)

Die v31-Erzeugung lief **14,66 h** ueber alle drei Klassen. Das Training des ersten Arms lief
warm in **58 min**. Der Fensterbau und der Monolith kommen dazu; der Monolith des v31-Fensters
liegt bei 1,48 GB und wird fuer v32 neu gebaut (die beiden v31-Monolithen sind darum erst NACH
dem Fensterbau Loeschkandidaten, `PREREG_code_cleanup_closeout.md` ist dafuer nicht zustaendig).
