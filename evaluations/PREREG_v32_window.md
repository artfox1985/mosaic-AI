<!-- STATUS: ENTSCHIEDEN | Frage: Wie wird das v32-Fenster zugeschnitten, und traegt der erste Arm? | Beleg: Fenster 2.947 Dateien, Training `v32-b01` warm in 63 min (par.10). TOR 1 TRAEGT nach Vorregistrierung: 434:366 = 54,25 Prozent, Block-z +2,37 -- aber nur ein Seed einzeln (+3,26 gegen +0,10). PROMOVIERT 2026-09-25 (par.11): Elo 1480 [1431; 1529] gegen 1450 des Vorgaengers, Champion-2 94:56 trifft die transitive Erwartung, alle Pflicht-Diagnostiken gepaart gegen v31 und unauffaellig; Spec unveraendert, Startkuppel-Suche erst ab v33. -->

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
`envelope_search_c 1,0`, `heuristik_variante hv1`, alles uebrige 0.

**Berichtigt 2026-09-23:** `envelope_search_c` fehlte in dieser Aufzaehlung, die mit "alles
uebrige 0" schliesst -- die Datei `models/v31_generation.spec.json` traegt dort aber **1,0**.
Die Aufzaehlung sagte an dieser Stelle das Gegenteil der Datei. Der Huellenknopf war und ist in
allen drei Klassen der Erzeugung aktiv; das ist der Bestand, auf dem
`PREREG_geometric_envelope.md` par.14b aufsetzt.

**Naheliegende Ursache, NICHT nachgewiesen:** STATUS.md Abschnitt 6 Punkt 7 haelt fest, dass
`engine_config` im Lauf-Manifest fuer genau dieses Feld (neben `envelope_projection_mode`,
`envelope_hull_form`, `special_row6_w`, `return_order_mode`) den Env-Default statt des
wirksamen Spec-Werts meldet. Wer die Aufzaehlung aus dem Manifest statt aus der Spec-Datei
zieht, liest dort 0. Die Lehre ist die alte: **fuer Spec-Inhalte die Spec-Datei lesen**, nicht
das Manifest.

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

### k6 Spezialfelder: meine Feststellung von gestern war leer, nachgerechnet 2026-09-23

Ich hatte registriert, `k6` stehe bei -9,39 Punkten mit "Ertrag > 0 in 0,0 Prozent von 1.499
Partien", und das neben den Claude-Partien-Befund der leeren Spezialfelder gestellt.
**Nutzer-Einwand: *"das ist praktisch auch schwer moeglich. brauchst es nur mal statistisch
durchrechnen."*** Er hat recht, gleich zweifach.

**1. Die Platte kann gar nichts Positives zahlen.** `docs/engine_manual.md` Zeile 192, Platte 7:
**"-3 pts per Spezialfeld left empty"** -- eine reine Strafplatte ohne positiven Term. Das
Maximum ist **0**. "Ertrag > 0 in 0,0 Prozent" ist damit keine Beobachtung, sondern die
Definition. Ich habe eine leere Feststellung als auffaelligen Posten registriert.

**2. Die Zahl der gefuellten Spezialfelder ist exakt das erwartete Nebenprodukt.** Ein
Spezialfeld schaltet laut Handbuch (Abschnitt 5) NUR frei, wenn die anderen drei Zellen
DERSELBEN Platte gefuellt sind; die Spezialfliese wird dann automatisch gelegt, ohne Wahl.

Gemessen am v32-Korpus (200 abgeschlossene Partien, 400 Seiten, letzter Record je Partie):

| | je Seite |
| --- | --- |
| Spezialfelder auf dem eigenen Brett | **4,50** (9 im Spiel, auf zwei Seiten verteilt) |
| davon gefuellt | **1,29** |
| leer | 3,21 -> **-9,62 Pkt** (abgerechnet -9,39) |
| belegte Zellen von 36 | **17,54** |
| vollstaendig gefuellte Platten von 9 | **2,53** |

**Die Vorhersage aus der Regel:** 2,53 fertige Platten mal dem Anteil, der ein Spezialfeld traegt
(4,5 von 9 = 0,5), ergibt **1,27**. **Gemessen: 1,29.** Das Netz laesst die Spezialfelder nicht
liegen -- es fuellt sie genau so oft, wie es Platten fertigstellt.

**Der bindende Engpass ist ein anderer:** nur 17,54 von 36 Zellen werden ueberhaupt belegt. Um
`k6` auf 0 zu bringen, muessten alle 4,5 Spezialfeld-Platten fertig werden, also allein 13,5
regulaere Zellen von 17,5 verfuegbaren -- praktisch das ganze Budget, und damit keine Spalten
mehr, waehrend Platte 2 sieben Punkte je Spalte zahlt.

**Was damit faellt:** die Deutung "Formtreue auf Kosten der Punktequellen", die ich zum
Dreiecks-Muster und zum Claude-Partien-Befund gezogen hatte. Die Spezialfelder folgen der
PLATTENVOLLENDUNG, nicht der Form. Der Claude-Befund (drei leere Spezialfelder je Partie) bleibt
richtig -- er ist nur kein Hinweis auf eine Schwaeche, sondern die Normallage.

**Was NICHT faellt:** `project_column_completion_structural_weakness` (der Champion vollendet
wenige Spalten) und der Befund aus `PREREG_special_tile_yield.md`, dass beim Plattenlohn etwas
liegen bleibt. Beide reden ueber die VOLLENDUNG, und 2,53 von 9 Platten ist genau die Groesse,
an der sie haengen. Hier ist nur die Brucke zwischen Spezialfeldern und Huelle gekappt.

## par.8 KOSTEN (aus `docs/measured_runtimes.md`, damit der Start planbar ist)

Die v31-Erzeugung lief **14,66 h** ueber alle drei Klassen. Das Training des ersten Arms lief
warm in **58 min**. Der Fensterbau und der Monolith kommen dazu; der Monolith des v31-Fensters
liegt bei 1,48 GB und wird fuer v32 neu gebaut (die beiden v31-Monolithen sind darum erst NACH
dem Fensterbau Loeschkandidaten, `PREREG_code_cleanup_closeout.md` ist dafuer nicht zustaendig).

## par.10 ERGEBNISSE DER KETTE (2026-09-23, `tools/night_v32_chain.sh`)

Kette 07:27:56 bis 13:02:02 = **5 h 34 min**, exklusiv, Exit 0.

### Fenster und Monolith

| | v32 | v31 |
| --- | --- | --- |
| Fensterdateien | **2.947** | 2.947 |
| Train / Val | 2.800 / 147 | 2.800 / 147 |
| Policy-Traeger (Manifest) | **580** = 400 neu + 135 G-1 + 45 G-2 | 580 = 400 + 135 + 45 |
| davon im Trainingsanteil | 529 (51 fielen in den Val-Pool) | -- |
| Fenster-Schluessel | `1587a92e5739` | `ec851c536ffd` |
| Monolith | **1.520.948.006 B = 1,42 GB**, Stempel geprueft | 1,48 GB |
| Zustaende | **5.330.401** | 5.211.996 |
| Blockbau | 1.201 neu, **662,6 s** | 4 s (Waechter hatte vorgebaut) |
| Monolith-Merge | **611 s** | 611 s |

Die Dateizahl trifft par.1 exakt. `MOSAIC_DATA_EXCLUDE` war gesetzt und meldete "0 von 2800
ausgeschlossen" -- richtig, weil die Kette durchgehend mit expliziten Dateilisten arbeitet und
die beiden Streudateien `selfplay_v29-b11-probe_*` gar nicht erst in der Liste stehen.

### Training `v32-b01`

**63 min** (07:58:16 bis 09:01:20, gegen v31 warm 58 min; KEIN sauberer Vergleich, andere
Nebenlastlage), Exit 0. **Manifest-Diff gegen `manifest_train_v31-b01_20260920_124555.json`:
0 unerwartete Abweichungen**, gemeldet genau `cache_file`, `file_list`, `load`, `name`, `seed`,
`val_pool`. Ein `_brierbest` wurde geschrieben, die beste Epoche war also nicht die letzte
(bester Value-Brier 0,1835 in Epoche 4, letzte Epoche 0,1840).

**Diese Brier-Zahl ist NICHT generationsuebergreifend lesbar**: sie steht auf dem Val-Anteil des
v32-Fensters (147 Dateien aus `^selfplay_v31-`), waehrend v31 gegen `^selfplay_v30-` validierte.
Die vergleichbare Groesse ist der Alt-Set-Brier auf `frozen_v3` (`platt_fit.py`,
`docs/promotion_checklist.md` Punkt 5) -- das ist die Zahl, an der die gestreifte Brier-Regel
haengt, und sie faellt erst bei einer Promotion an.

### TOR 1: `v32-b01` gegen den Champion `v31-b01` -- TRAEGT, aber schwaecher als v31

Beide Seiten Champion-Spec (`frozen_champions/v31-b01/spec.json`, `envelope_search_c 1.0`),
400 Sims, c_puct 1,5, Blockgroesse 5, Deckel 200 Paare, alpha = beta = 0,001, 10 Threads,
`--log-games`. Beide Seeds liefen in den Deckel, **kein SPRT-Entscheid** -- die vierte
Nachbar-Generation in Folge (par.6 der v31-Prereg zaehlte drei).

| Seed | Stand | Anteil | Mittel | sd | **Block-z** | McNemar | LLR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 20261500 | 201:199 | 50,25 % | 0,5025 | 0,1527 | **+0,10** | p = 1,0000 | -3,604 |
| 20261501 | 233:167 | 58,25 % | 0,5825 | 0,1599 | **+3,26** | p = 0,0012 | +5,546 |
| **gepoolt** | **434:366** aus 800 | **54,25 %** | 0,5425 | 0,1605 | **+2,37** | | |

**Der Block-z ist auf DIFFERENZIERTEN Blockwerten gerechnet** (die Felder in `blocks[]` sind
kumulativ, `docs/pitfalls.md`), mit Summenprobe gegen `a_wins_total`/`b_wins_total` je Lauf.
**Die Methode ist geeicht:** dasselbe Skript reproduziert die registrierten v31-Zahlen exakt
(+3,54 / +2,42, gepoolt Mittel 0,5763, sd 0,1609, z +4,24).

**Das vorregistrierte Kriterium ist erfuellt.** Wortlaut aus `PREREG_v30_window.md` par.3
Punkt 5, ueber par.2 der v31- und dieser Prereg geerbt: *"Traegt b01 (z >= +1,96 oder gepoolt
>= 52,5 Prozent ohne Gegenbefund)"*. Beide Zweige halten: z = +2,37 und 54,25 Prozent.

**Und die Einschraenkung, die dazugehoert:** bei v31 lagen BEIDE Seeds einzeln ueber 1,96
(+3,54 und +2,42), und das war ausdruecklich Teil des Verdikts. Hier traegt einer (+3,26) und
der andere ist exakt H0 (+0,10). Ein gepoolter Wert ueber zwei so verschiedene Seeds ist
schwaecher als derselbe Wert ueber zwei gleichgerichtete. Das Kriterium wird deswegen NICHT
nachtraeglich verschaerft -- es stand vorher fest --, aber der Befund wird auch nicht staerker
berichtet, als er ist. Praezedenz fuer die Streuung: 5,75 Prozentpunkte bei n = 400 fuer
IDENTISCHE Konfiguration.

### TOR 2b (Nicht-Fallen) -- HAELT

| volle Spalten je Seite | `v32-b01` | `v31-b01` | Differenz |
| --- | --- | --- | --- |
| Seed 20261500 | **1,030** (+-0,073) | 1,025 (+-0,076) | +0,005 |
| Seed 20261501 | **1,093** (+-0,075) | 0,960 (+-0,075) | +0,133 |

### Die sechs Standard-Kennzahlen (CLAUDE.md), je Seite und als Differenz

| Kennzahl | Seed 1500: v32 / v31 / Diff | Seed 1501: v32 / v31 / Diff |
| --- | --- | --- |
| Reihen (voll) | 0,142 / 0,110 / +0,032 | 0,107 / 0,110 / -0,003 |
| Reihen (Fuellsumme) | 18,140 / 18,052 / +0,088 | 18,195 / 17,955 / +0,240 |
| lange Reihen vollendet | 3,125 / 3,085 / +0,040 | 3,090 / 3,040 / +0,050 |
| Spalten voll | 1,030 / 1,025 / +0,005 | 1,093 / 0,960 / **+0,133** |
| Spalten >= 4 | 2,308 / 2,360 / -0,052 | 2,350 / 2,295 / +0,055 |
| Spalten >= 3 | 3,308 / 3,285 / +0,022 | 3,305 / 3,272 / +0,033 |
| hoechste Spalte | 5,695 / 5,673 / +0,022 | 5,718 / 5,635 / +0,083 |
| Strafleiste | 6,990 / 7,348 / **-0,357** | 7,050 / 7,527 / **-0,478** |
| eigene Punkte | 58,178 / 58,047 / +0,130 | 59,453 / 56,790 / **+2,663** |
| Margin | +0,130 / -0,130 / +0,260 | +2,663 / -2,663 / **+5,325** |

Plattenpunkte je Kriterium (Seed 1501, Mittel ueber Bretter mit aktivem Kriterium): der
Kandidat gewinnt bei **Vertikale Reihen** (8,20 gegen 7,21), **Eckplatten** (9,30 gegen 8,88)
und **Spezialfelder** (-9,05 gegen -9,96, also weniger Strafe); er verliert leicht bei
Diagonale (0,49 gegen 0,56) und Mehrfarbige Felder (4,17 gegen 4,43).

**Die Strafleiste faellt auf beiden Seeds** (-0,36 und -0,48) -- die einzige Kennzahl, die in
beiden Laeufen dasselbe Vorzeichen traegt und nicht am Seed haengt.

### Nebenbefund: ein stiller Nullwert in der Spaltensonde

`arena_column_probe.py:160` bildet `spezialfelder_belegt` als
`(geo.get("special_total") or 0) - (geo.get("special_empty") or 0)`. Das `score_geo` eines
Gating-Artefakts traegt aber **nur** `col_fill` und `row_fill` (am Artefakt geprueft), also
kommt 0 - 0 = **0** heraus -- in jedem aus einer Arena gespeisten Lauf. Am Korpus sind es
1,29 gefuellte Spezialfelder je Seite (par.9). **Der Wert ist ein Default, keine Messung.**

Rueckwaerts-Pruefung: ausser `arena_column_probe.py` rechnet nur
`tools/probes/move_class_differential.py:399` dieselbe Zeile; **keine Prereg und kein Dokument
stuetzt sich auf die Zahl**, es ist also nichts falsch geworden. Entweder `special_total` und
`special_empty` wandern additiv ins `score_geo` der Arena, oder das Feld wird dort auf `None`
gesetzt, damit es nicht als Null gelesen werden kann.

## par.11 PROMOTION: `v32-b01_brierbest` ist Champion (2026-09-25)

**Nutzer-Entscheid:** Aufruf `/mosaic-champion-promotion`; auf die Vorlage, die Startkuppel dabei
einzuschalten: *"Erst promoten wie gemessen, Knopf ab v33"* (`PREREG_start_dome_choice.md`
par.12). Die Champion-Spec ist damit **byte-gleich** mit der, auf der Tor 1 beidseits lief
(`frozen_champions/v31-b01/spec.json`, sha256 `4f5e5969...`), und liegt als
`models/v32-b01_brierbest.spec.json` fuer den Server auffindbar.

### Die drei Elo-Kanten (`docs/promotion_checklist.md` Punkte 2-4), keine frueh gestoppt

| Kante | Stand | Instrument | Bemerkung |
| --- | --- | --- | --- |
| Gating gegen `v31-b01` | 201:199 und 233:167 = **434:366** | paired_gating, 2 Seeds | par.10; zwei Registerzeilen mit Seed-Bloecken |
| Anker `hv4_anchor` @150 | **43:7** (n = 50 fest) | frozen_referee_match, 6 Worker | Worker **150 Sims, c_puct 0,3 ausdruecklich gesetzt** -- der Werkzeug-Default waere 400/1,5; Handshake ROT (Cross-Aera, vorgesehen), Golden-Selbsttest GRUEN; 418,6 s |
| Champion-2 gegen `v30-b02` | **94:56** (n = 150) | frozen_referee_match, 6 Worker | Handshake GRUEN, binomial p = 0,0024; 2.377,5 s |

**Die Champion-2-Kante trifft die transitive Erwartung**, anders als bei v31. Herleitung, nicht
gemessen: aus den gepoolten Tor-1-Kanten (+29,6 Elo v32/v31, +53,4 Elo v31/v30) folgen +83,0 Elo,
also **61,7 Prozent**; gemessen **62,7**.

**Nebenlast waehrend der Champion-2-Kante, gemeldet und aufgeklaert:** ein `grep -rn` des
Koordinators lief etwa 08:50 bis 08:54 ueber das Repo samt `data/` mit. Die Partien der
Listenindizes 44 bis 71 (alles, was im Fenster fertig wurde oder lief) wurden mit denselben Seeds
und derselben Paritaet wiederholt: **28 von 28 identisch** in Seite, Anzug, Punkten, Sieger und
Schrittzahl (`champion2_v32-b01_vs_v30-b02_rerun_44-71.json`). Die Kante ist nicht kontaminiert,
und der Referee ist unter dieser Last nachweislich deterministisch.

**Leiter** (Segment 2, Anker fix 1000, Block-Bootstrap):

| Knoten | Elo | KI95 | Partien |
| --- | --- | --- | --- |
| **`v32-b01@400`** | **1480** | [1431; 1529] | 1.000 |
| `v31-b01@400` | 1450 | [1406; 1496] | 1.800 |
| `v30-b02@400` | 1411 | [1371; 1453] | 1.890 |

+30 Elo gegen den Vorgaenger, die Intervalle ueberlappen -- passend zu einem Tor 1, das auf einem
von zwei Seeds ruhte.

**Standard-Kennzahlen:** fuer den Kandidaten vollstaendig an der Hauptkante in par.10 (800
gepaarte Partien, je Seed). Fuer die beiden Referee-Kanten hier Punkte und Marge aus den
Artefakten: Anker v32 **59,52** gegen 42,20, Marge **+17,32** (sd 15,2, n = 50); Champion-2 v32
**57,23** gegen 52,83, Marge **+4,41** (sd 18,9, n = 150). Reihen, Spalten, Strafleiste und
Plattenpunkte dieser zwei Kanten sind NICHT ausgewertet: die Werkzeuge
(`plate_points_from_arena.py`, `arena_column_probe.py`) lesen das Format der gepaarten Arena, nicht
das des Referees. Die vollen Partie-Logs liegen aber in beiden Artefakten (`games[].log`), die
Groessen sind also ohne Neulauf nachziehbar.

### Pflicht-Diagnostiken (Punkt 5), jede GEPAART gegen v31-b01

| | v31-b01 | **v32-b01** | Paarungs-Beleg |
| --- | --- | --- | --- |
| R4: Value-Kopf Steigung / R2 | 0,454 / 0,414 | 0,456 / 0,408 | 72 von 72 Zustaenden identisch in `game_id`, `true_margin`, `true_winprob` |
| R4: Punkte-Kopf Steigung / R2 | 1,193 / 0,312 | 1,250 / 0,327 | dieselben |
| R4: Vorzeichen-Anker | 50/70 | 50/70 | dieselben |
| R4b: Trunk -> Marge / Siegwahrscheinlichkeit (LOO-R2) | 0,940 / 0,927 | **0,940 / 0,910** | Eingabe-Sonde 0,087 / 0,034 auf beiden Seiten identisch |
| R4b: Koepfe realisiert (Margenskala) | -2,18 | -2,28 | Decke 0,983 beide |
| R5: Value-Daempfung (Steigung) / R2 | 0,146 / 0,309 | **0,177** / 0,328 | Kennlinie BITGLEICH (a = -0,78786, b = 0,39438), je 139 Paare |
| R5: Punkte-Kopf Steigung / R2 | 1,088 / 0,372 | 1,068 / 0,378 | dieselben |
| Platt `frozen_v3`: A / B / Brier | -0,0261 / 0,6006 / 0,22919 | **-0,0127 / 0,5989 / 0,22864** | v31 reproduziert seine eingetragenen Werte EXAKT |
| Platt `frozen_v1` (Trend): B / Brier | 0,5489 / 0,26266 | 0,5462 / 0,26181 | dieselben Laeufe |
| sigma/Prior, Median (Runden 1-4) | 1,899 (1,52/2,10/1,94/2,03) | **1,743** (1,17/1,98/2,62/2,13) | 233 verwertbare von 300 Zustaenden beide |

**Lesart, knapp:** unveraendert der Befund, den R4b fuer v31 geliefert hat -- der Trunk traegt die
Endspiel-Information, das Auslesen verliert sie; die Engstelle ist weder Encoder noch Kapazitaet.
Die R5-Daempfung ist leicht kleiner, liegt aber weit unter dem unverzerrten 1,0; ein Intervall
traegt das Werkzeug nicht aus, und 139 Paare aus 24 Zustaenden sind geklumpt -- Richtung, kein
Befund. Die **Brier-Regel haelt** (0,22864 gegen 0,22919). Die sigma/Prior-Kennzahl bleibt unter
3; die c_visit/c_scale-Familie oeffnet sich NICHT.

**Substrat-Vorbehalt:** R4/R4b stehen fuer die Paarung auf `selfplay_v30-b02-policy_*`, also auf
Zustaenden zweier Generationen zurueck; R5 und Platt auf den eingefrorenen Sets. Das ist die
Bedingung der Vergleichbarkeit und wird so benannt, nicht verschwiegen.

**Laufzeiten** (in den Artefakten): R4 2.756,1 s, R4b 42,5 s, R5 877,7 s, sigma/Prior 707,5 s.

### 5b-5d und Punkt 7

* **5b Anzeige-Kalibrierung:** `server.py` `_DISPLAY_CAL_A/_B` auf -0,0127 / 0,5989.
* **5d Netz-Paritaets-Fixture:** neu erzeugt, `champion=v32-b01_brierbest hash=180b582713f6259c`;
  im frischen Prozess ohne Umgebungsvariable gruen (693 Lib-Tests bestanden).
* **Punkt 7, eingefrorenes Artefakt `models/frozen_champions/v32-b01/`:** Wheel **1.1.0**,
  sha256 `e11ea6d5...`, byte-gleich mit dem installierten zur Mess- und Trainingszeit
  (`direct_url.json`); Golden Probe 10 Sonden (3 mit offener Kuppelwahl), 1.109 s, 40 Partien;
  venv ohne Netz (`--no-index --no-deps`, nur `mosaic_rust`); Referee-Selbsttest GRUEN (Handshake,
  10/10, zwei Echtpartien). **`.onnx`, `.pth` und Wheel sind per `.gitignore` NICHT im Repo** --
  das erste Artefakt unter der Regel vom 2026-09-23.
* **Zwei-Champion-Regel:** `frozen_champions/v30-b02/` geloescht (Nutzer-Freigabe 2026-09-25),
  Beleg restic-Snapshot **`4137c235`**, alle 7 sicherungswuerdigen Dateien mit gleicher Groesse
  nachgewiesen; das `venv/` ist per `backup_excludes.txt` ausgenommen. Vorher geprueft: keine
  Junction und kein Symlink im Baum (die 3.455 ReparsePoint-Treffer sind OneDrive-Platzhalter).
* **Server-Neustart:** Konsolenzeile *"Champion-Spec v32-b01_brierbest.spec.json"* mit
  `MOSAIC_ENVELOPE_SEARCH_C=1.0` und Form 2, keine Ueberstimmung; `/api/champion` meldet
  `v32-b01_brierbest`.

### Werkzeug-Befunde dieser Promotion

* `tools/frozen_referee_match.py` schrieb den `laufzeit`-Pflichtblock nicht (nur `elapsed_s`);
  betroffen war JEDE Anker- und Champion-2-Kante. Nachgezogen; Falle dabei: der Referee misst mit
  `perf_counter()`, der Helfer rechnet gegen `monotonic()` -- zwei Epochen.
* `tools/gumbel_scale_calibration.py` schrieb ihn ebenfalls nicht, und sein fester Default-Pfad
  hat das v31-Ergebnis unter einem Namen ohne Modell abgelegt. Beides nachgezogen.
