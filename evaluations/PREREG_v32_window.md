<!-- STATUS: OFFEN | Frage: Wie wird das v32-Fenster zugeschnitten, und traegt der erste Arm? | Beleg: par.1 Zuschnitt steht, par.6 Rezept entschieden (Nutzer "Einstellungen wie v31"). par.9 ERZEUGUNG GEFAHREN 2026-09-22/23: 13 h 57 min, 1.201 Dateien, alle Klassen Exit 0. Manifest-Diff genau 4 Abweichungen (Modell, Seed, Spec, Version), Wiedervorlage am ersten Record gruen (Knoten mit Lernziel), Streurate 14,0 Prozent gegen Ziel 15, TOR 2a HAELT (sp_voll 0,977 gegen 0,955). Profil stabil. Offen: Fensterbau, Monolith, Training v32-b01, Tore 1 und 2b. -->

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

### Die Dosis bleibt 0,81 -- und die Nachmessung gibt dem Entscheid recht

`--return-order-random-p 0.81` steht unveraendert in allen drei Klassen.

**Beim Vorlegen hatte ich einen Vorbehalt registriert, der sich als mein eigener Zaehlfehler
erwiesen hat** (`PREREG_dome_return_order.md` par.13, Berichtigung 2026-09-23): ich hatte die
Gelegenheitsrate mit 28,0 Prozent gegen registrierte 17,75 Prozent gehalten und daraus rund
`p = 0,54` hergeleitet. Die beiden Zahlen zaehlen verschiedene Dinge -- 17,75 Prozent meint
Gelegenheiten mit mindestens DREI Restplatten, meine 28,0 Prozent den Knoten in `valid_actions`,
also ab ZWEI. **Verglichen waren zwei Kriterien, nicht zwei Generationen.**

**Mit einer Zaehlweise an beiden Korpora nachgemessen** (je 20 Dateien, 200 Partien):

| Erzeugung | Gelegenheit | gestreut |
| --- | --- | --- |
| v31 (Generator `v30-b02`) | 22,5 % | 12,0 % |
| **v32 (Generator `v31-b01`)** | **23,5 %** | **14,0 %** |

Der Unterschied ist Rauschen (n = 200, sd rund 3 Punkte). **Die Streurate liegt mit 14,0 Prozent
am Ziel von 15 Prozent** -- die Dosis ist richtig eingestellt, und "Einstellungen wie v31" war die
richtige Wahl.

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

## par.9 ERZEUGUNG GEFAHREN (2026-09-22/23)

`tools/night_v32_generate.sh`, gestartet 09:44:39, fertig **23:41:37 = 13 h 57 min**. Alle drei
Klassen Exit 0, **1.201 Dateien / 12.010 Partien**.

| Klasse | Zeitraum | Dauer | Dateien |
| --- | --- | --- | --- |
| Sockel (`policy`) | 09:44:39 - 14:16:19 | 4 h 32 | 400 |
| Schwarm a (`value-tempc`) | 14:16:19 - 18:49:56 | 4 h 34 | 400 |
| Schwarm b (`value-excursion`) | 18:49:56 - 23:41:37 | 4 h 52 | 401 |

**Die Wanduhr ist NICHT sauber gegen v31 (14,66 h) zu halten.** Waehrend des Laufs lag Nebenlast
auf der Maschine: die Claude-Partien g09 (10:10) und g10 (18:55) trieben je eine Netzsuche, dazu
ein Commit um 18:59 mit 206 Tests im Haken. Der Effekt ist erkennbar klein -- die beiden ersten
Klassen liefen mit 4:32 und 4:34 praktisch gleich, obwohl g09 in die erste fiel --, aber die Zahl
ist keine saubere Vergleichsgroesse mehr und wird hier nicht als solche gefuehrt.

### Pflichtpruefungen

| Pruefung | Ergebnis |
| --- | --- |
| Manifest-Diff gegen `manifest_v30-b02-policy_20260919_202347.json` | **genau 4 Abweichungen**: `model`, `seed`, `spec`, `version` -- exakt die drei registrierten Aenderungen plus den daraus folgenden Versionsnamen. Kein stiller Default. |
| Wiedervorlage am ersten Record | **GRUEN**: 1.989 Records aus 10 Partien, `dome_pool_view` in allen; Mondknoten 406-410 **248 valid / 248 policy**, Rueckgabeknoten 411-413 **2/2** -- mit Lernziel, nichts faellt eine Generation zurueck |
| Stack-Draw-Kontrolle | `MOSAIC_STACK_DRAW_RESEARCH=1` gesetzt, vom Skript geprueft |
| Streuung am Korpus (20 Dateien, 200 Partien) | Gelegenheit **23,5 %**, gestreut **14,0 %** gegen das Ziel 15 % |
| **Tor 2a** | `sp_voll` **0,977 (+-0,017)** fuer `v31-b01` gegen **0,955 (+-0,017)** fuer `v30-b02` -- **HAELT** (Kriterium ist Nicht-Unterlegenheit, nicht Signifikanz) |

Artefakt: `evaluations/artifacts/corpus_sanity_v31-b01-policy.json`, Laufzeit 358,2 s.

### Die sechs Standard-Kennzahlen des Sockels (CLAUDE.md), gegen die Vorgeneration

| | `v30-b02` | **`v31-b01`** |
| --- | --- | --- |
| volle Spalten je Seite (`sp_voll`) | 0,955 | **0,977** |
| Spalten >= 4 / >= 3 | 2,224 / 3,168 | 2,246 / 3,177 |
| volle Reihen | 0,098 | 0,094 |
| Strafleiste je Seite | 5,105 | 5,046 |
| eigene Punkte | 52,34 | **52,87** |
| Margin | 0,00 (per Konstruktion) | 0,00 |

**Das Profil ist stabil** -- keine Kennzahl bewegt sich ueber ihr Intervall hinaus.

### Ein Posten, der seit zwei Generationen unveraendert liegt

Die Punkte je Wertungsplatte sind bis auf die zweite Stelle dieselben. Auffaellig bleibt **k6
Spezialfelder: -9,39 Punkte, Ertrag > 0 in 0,0 Prozent von 1.499 Partien** (v30-b02: -9,41 und
ebenfalls 0,0 Prozent). In ZWEI vollen Generationen hat keine Seite aus dieser Platte je einen
positiven Ertrag gezogen.

Das deckt sich mit dem Befund aus den Claude-Partien (`PREREG_claude_play_interface.md`,
2026-09-22: "das Netz bedient die aktiven Wertungsplatten unzuverlaessig, g09/g10 je drei leere
Spezialfelder") und mit `project_special_tile_yield_remeasure`. **Es ist hier nur festgehalten,
nicht gedeutet** -- ob -9,39 eine Strafe fuer unbelegte Felder ist oder ein Rechenartefakt der
Zuordnung, ist in dieser Prereg nicht geprueft.

## par.8 KOSTEN (aus `docs/measured_runtimes.md`, damit der Start planbar ist)

Die v31-Erzeugung lief **14,66 h** ueber alle drei Klassen. Das Training des ersten Arms lief
warm in **58 min**. Der Fensterbau und der Monolith kommen dazu; der Monolith des v31-Fensters
liegt bei 1,48 GB und wird fuer v32 neu gebaut (die beiden v31-Monolithen sind darum erst NACH
dem Fensterbau Loeschkandidaten, `PREREG_code_cleanup_closeout.md` ist dafuer nicht zustaendig).
