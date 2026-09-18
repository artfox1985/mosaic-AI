# Laufzeiten (gemessen, nicht geschaetzt)

**Kanonischer Ort seit 2026-08-28** (aus STATUS.md entflochten, Nutzer-Hinweis:
STATUS ist kein Langzeitgedaechtnis); Herkunft der Inhalte: STATUS-Stand
2026-08-28. Wer aendert, aendert HIER -- STATUS.md verweist nur noch.

**Pflegeregel: wer eine Zeile ergaenzt, traegt GEMESSENES ein.** Geschaetzte
Restzeiten sind wertlos (drei Schaetzungen in der Nacht des 2026-08-25 lagen
daneben). Die belastbaren Zahlen stehen je Lauf im Artefakt (`laufzeit`-Block,
Pflichtfeld seit 2026-08-25, siehe `../CLAUDE.md`, Abschnitt "Laufzeiten
messen, nicht schaetzen"); diese Tabelle ist nur die Planungsgroesse, damit
eine Sitzung einen Lauf einplanen kann, ohne ihn erst zu starten.

**`threads` gehoert zu jeder Zeile**, weil dieselbe Zahl in zwei Arena-
Einstiegen Verschiedenes bedeutete. Seit dem Geradezug 2026-08-25 gilt EINE
Konvention (`self_play::thread_plan`): `0` = alle Kerne, `1` = sequenziell,
`n` = n Threads. Zeilen mit aelteren Bedeutungen sind unten ausdruecklich
markiert.

**Zwei Zeilen nennen stillgelegte Werkzeuge** (`v2_envelope_arena.py`,
`v2_teacher_arena.py`, seit B4a nicht mehr lauffaehig). Die Zahlen bleiben als
Planungsgroessen gueltig -- sie beschreiben die FORM des Laufs (Heuristik gegen
Heuristik bzw. Netz gegen Heuristik, gleiche Sims), nicht das Werkzeug.

| Aufbau | Umfang | Threads | Wanduhr |
| --- | --- | --- | --- |
| Heuristik gegen Heuristik, 150 Sims (`v2_envelope_arena.py`) | 160 Partien | 0 = alle 12 Kerne | **21,9 s** |
| dito, Rauchtest | 20 Partien | alle Kerne | **4,1 s** |
| Netz@400 gegen Heuristik@150 (`v2_teacher_arena.py`), je Partie | – | 0 = **sequenziell** (alte Bedeutung) | **12,357 s** |
| dito | – | 11 | **2,575 s** |
| dito, voller Lauf | 814 Partien | 0 = sequenziell (alte Bedeutung) | ~2 h 48 min |
| Anker-Tor (`anchor_referee_parity_probe --games 20`) | 20 Partien, doppelt (in-process + extern) | 1 | **368,8 s** = 9,22 s je Partie |
| dito | 814 Partien | 11 | ~35 min |
| Strafleisten-Tor (`floor_action_aversion_gate.py`), 240 Stellungen, sims=200 | – | – | **~7 min** |
| Heuristik-Self-Play `hv2`, 600 Basis-Sims, Netz-Labels | 200 Partien | 11 | **239 s** = 50 Partien/min |
| dito, `hv1` (Vorzug feuert nicht, Suche laeuft voll) | 200 Partien | 11 | **331 s** = 36 Partien/min |
| v22-Korpus-Erzeugung (`hv2`, Netz-Labels) | 24.000 Partien | nicht protokolliert | **8,43 h** = 47,5 Partien/min -- REKONSTRUIERT aus Manifest-Start und mtime der letzten Datei (der Lauf begann vor dem `laufzeit`-Einbau) |
| `cargo test --release --lib` (volle Suite) | 527 Tests | – | **~65 s** |
| `cargo test --release` (alle Ziele, exklusiv, 2026-08-26) | 553 Tests | – | **97,1 s** |
| Datei-Cache erstbauen (`build_cache_incremental.py`) | 120 Dateien | 6 Worker | **112,6 s** = 0,96 s je Datei |
| Split-Arm Heuristik (`v2_envelope_arena.py --tiling`) | 160 Partien | 0 = alle Kerne | **~22 s** |
| dito, Bloecke liegen schon (anderes Fenster) | 120 Dateien | 6 | **7,9 s** |
| Cache-Bau voller Korpus, parallel | 4.186.112 Zustaende | – | **36,1 min** (seriell 2,58 h, Faktor ~4,3) |
| Training auf NEUER Fenster-Zusammensetzung (v23-b05 Relabel), Datenaufbau EINKERNIG | 2.345 Dateien, 4,72 Mio Samples | 6 = `torch.get_num_threads()`, tatsaechlich **ein** Kern im Aufbau | **7,42 h gesamt, davon 4,98 h Datenaufbau** -- zum Vergleich: b02 auf STEHENDEM Fenster-Cache 32 s, b01 (baut Bloecke selbst) 3,45 h. **Vermeidbar:** Fenster-Cache mit `build_cache_incremental.py --merge-out` parallel vorbauen, dann `train.py --cache-file` (seit dc40551) |
| Orakel-Labels bauen (`build_frozen_oracle_labels.py`, 5000 Sims, 2D-Netz) | 1.144 Labels | 1 | **88,8 min** = 0,21 Labels/s |
| Frozen-Set erzeugen (400 Partien Sockel-Konfiguration, sims 100, Rauschen) | 400 Partien | 10 | **~22 min** |
| Wheel-Bau (`maturin build --release`) plus Installation | – | – | **~30 s** |
| Netz-Self-Play argmax @400 (par.3b.2/3b.6-Instrument, `self_play.py --deterministic --no-root-noise`) | 200 Partien | 11 | **~20 min** = 0,15-0,17 Partien/s (Neustart 2026-08-29: Bloecke 107-145 s je 20 Partien; Tiling-Pol-Knopf kostet dabei praktisch nichts) |
| v22-Kaltstart-Training (b01, CUDA, inkl. In-Train-Cache-Bau 2,55 h) | 17 Epochen, 3,77 Mio Samples | 6 = `torch.get_num_threads()`, KAPAZITAET; gemessene Last rund **1 Kern** (`cpu_s/wanduhr_s` 0,92-0,98 ueber b01/b02/b04/b05). Der DataLoader laeuft ohne `num_workers` im Hauptprozess (train.py:1323) -- die fruehere Angabe "6 (DataLoader)" war falsch, berichtigt 2026-08-31 | **5,43 h** gesamt = ~10 min je Epoche nach dem Datenaufbau (manifest_train_v22-b01) |
| Lehrer-Relabeling via frozen-Worker (relabel_drafts_with_teacher) | 31.190 Labels / 600 Partien | 8 Worker | **66 s** = ~5 ms je Label (Huellen-Vorzug antwortet quasi instant) |
| Lehrer-Relabeling via frozen-Worker (v23-Sockel, 200 Dateien) | 204.008 Labels / 4.000 Partien | 4 Worker | **744 s** = 3,6 ms je Label. **UNTER NEBENLAST gemessen** (lief neben dem b01-Datenaufbau) -- als Planungsgroesse nach oben abgerundet, nicht nach unten |
| DAgger-Afterburner (v22-b05: Warm-Start, 6 Epochen, 176k Samples) | 600 Partien extra-dir | CUDA | **10,6 min** (davon Datenaufbau 6,6 min) |
| DAgger-Afterburner (v22-b06: Warm-Start, 12 Epochen, 89k Samples, reines Fenster) | 600 Partien extra-dir | CUDA | **7,9 min** (davon Datenaufbau 3,7 min) |
| Netz-Self-Play b05@400 MIT Root-Noise (Sockel-Konfiguration) | 4 x 100 Partien | 11 | **8,27-8,73 s je Partie** = 4.000 Sockel-Partien rund 9,3 h. **ACHTUNG: die v23-Erzeugung fuhr @100, nicht @400** -- diese Zeile hat am 2026-09-01 eine falsche v24-Kostenschaetzung (23 h) ausgeloest, die richtigen Zeilen stehen darunter |
| v23-Erzeugung Sockel, b05@100 gesampelt mit Rauschen (`manifest_v22-b05-policy_20260831_033448.json`) | 4.000 Partien | 11 | **3,365 s je Partie** = 13.459,5 s (3,74 h) |
| v23-Erzeugung Schwarm argmax, b05@100 `--value-only --deterministic --no-root-noise` (`manifest_v22-b05-value-argmax_20260830_192533.json`) | 6.000 Partien | 11 | **3,674 s je Partie** = 22.041,4 s (6,12 h) |
| v23-Erzeugung Schwarm gesampelt, b05@100 `--value-only` (`manifest_v22-b05-value-sampled_20260831_013258.json`) | 2.000 Partien | 11 | **3,653 s je Partie** = 7.306,5 s (2,03 h); alle drei zusammen **11,9 h** |
| Netz-Self-Play b01@400 argmax (`manifest_s4states-v23b01_20260901_222208.json`, Zustandssatz Stufe 4) | 80 Partien | 11 | **14,5 s je Partie** (1.161 s), mit leichter Nebenlast (Log-Replays) gemessen |
| Netz-Self-Play b06@400 argmax, exklusiv (`manifest_tor2a-v23b06_*.json`) | 200 Partien | 11 | **6,98 s je Partie** (1.396 s) -- die 14,5 s oben waren Nebenlast |
| Gepaarte Arena Netz@400 gegen Netz@400 (`paired_arena_env_ab`, Blockgroesse 5, `--log-games`) | 80 Partien | 10 | **rund 11,4 s je Partie** (900-920 s je Lauf, 2026-09-02) |
| Cache-Bloecke neu bauen (`build_cache_incremental`, 2D/nortv) | 2.156 Dateien | 6 Worker | **2.280 s** inkl. Zusammenfuegen; **Zusammenfuegen allein 344 s** fuer 2.228 Dateien (Hebel 3, gegen 17.934 s einkernig in train.py) |
| Training Kaltstart 12 Epochen, b01-Rezept, Monolith-Treffer (`manifest_train_v23-b06_20260902_021224.json`) | 4,72 Mio Samples | CUDA | **8.164 s** (2,27 h), Datenaufbau 31 s |
| Training Warm-Start 12 Epochen, b03-Rezept OHNE Hilfs-Losses (v29-b06: moon 0, ownership 0, ohne opp_points/endgame), `--fast-loader`, Monolith per `--cache-file` (`manifest_train_v29-b06_20260917_013522.json`) | 4.538.842 Samples, 794 | CUDA, daneben Arena mit 10 Threads | **rund 57 min** (01:35-02:32) gegen 1,38-1,48 h bei b03/b04 mit allen Koepfen -- die Hilfskoepfe kosten ein Drittel der Trainingszeit |
| Training Warm-Start 12 Epochen, b01-Rezept, `--fast-loader`, Monolith-Treffer (v24-b03, 2026-09-06, aus den Zwischenstaenden `alphazero_v24-b03_resume.pth`) | Fenster `window_v24_b03` (Samples im End-Manifest) | CUDA, daneben Arena mit 10 Threads | **5.344 s gesamt** (1,48 h; `manifest_train_v24-b03_20260906_002718.json`: 12 Epochen, 5.331.923 Samples, Datenaufbau 67,7 s, cpu_s 28.628) = **rund 440 s je Epoche** (Zwischenstaende 438-460 s) gegen 16 min (b04, Standard-Lader neben Arena, 13.305 s gesamt) und 13,9 min (b01, Standard-Lader ohne Nachbar); Faktor rund 2,2 bei gleicher Nebenlast |
| Gepaarte Arena b05@400 gegen Heuristik@150 | 2 x 100 Partien | 10 | **3,33 s je Partie** (666 s), rund 34 s je Block von 10 |

**Parallelisierung ist ergebnisneutral, gemessen statt angenommen** (20 Seeds
beidseitig): Siegquote 0,450, volle Spalten 1,200 und Punkte 55,0 in BEIDEN
Faellen identisch, bei 4,8-fachem Tempo. Grund:
`PREREG_search_rng_split.md` -- jede Partie haengt an ihrem eigenen,
abgeleiteten Suchstrom.

## Generation v24, gemessen am 2026-09-07

Alle Werte aus den Artefakten der Laeufe, nicht geschaetzt. Threads wie angegeben, exklusiv.

| Aufbau | Dauer | Bemerkung |
| --- | --- | --- |
| Gepaarte Arena, 80 Partien @400, threads 10 | **rund 1.060 s** | je Richtung; ein Arm braucht zwei |
| argmax-Instrument, 200 Partien @400, threads 11 | **rund 24 min** | Tor 2a |
| Vollstaendiger Knopf-Arm (Arena beide Richtungen + zwei Instrumente) | **91 min** | K5-Kette |
| Gepaartes Gating, 170 Paare @400, threads 10 | **70 min** | rund 125 s je Block zu 5 Paaren |
| Gepaartes Gating, 200 Paare @400 (Deckel) | **67 min** | |
| Anker-Kante, festes n=150, 6 Worker | **1.282 s** | rund 21 min |
| Champion-2-Kante, SPRT-Stopp nach 75 Paaren | **1.889 s** | rund 31 min |
| Golden Probe fuers Artefakt (10 Sonden @400, einkernig) | **16 min** | |
| Voller Build: cargo test --lib + --no-run + Wheel + Install + Anker beide Modi | **rund 6 min** | 554 Tests |
| Netz-Self-Play, 10 Partien @100 Sims, threads 11 | **37,6 s** | 3,77 s je Partie -- Basis der v25-Hochrechnung |
| restic rewrite + prune + check auf 14,5 GiB | **14 s** | lokale Pack-Dateien |
| Tagesschnappschuss + check | **9 s** | |
| Aktionsprofil-Sonde, 3 Gruppen a 400 Dateien | **rund 4 min** | 1,5 Mio Entscheide |
| **v25-Sockel: 4.000 Partien @100 Sims, threads 11** | **14.426 s = 4h 00m** | 3,61 s je Partie, 659.083 Zuege, 400 Dateien |
| **Cache-Bloecke je Datei, 400 Dateien, 3 Arbeiter** | **1.126 s = 18,8 min** | NEBEN der laufenden Erzeugung, ohne Durchsatzverlust |

**Hochrechnung fuer die v25-Erzeugung** (hergeleitet aus 3,77 s je Partie, NICHT auf dieser
Groesse gemessen): rund 4,2 h je 4.000-Partien-Block, rund 3,0 h fuer die Ausflug-Haelfte
(2.000 Hauptpartien plus 2.000 kuerzere Ausfluege), zusammen etwa 11,4 h.

## Generation v25, gemessen am 2026-09-09

Alle Werte aus den Artefakten der Laeufe. Die Erzeugung lief mit Generator `v24-b07`,
threads 11; Training auf der GPU, Arenen mit threads 10 exklusiv.

| Aufbau | Dauer | Bemerkung |
| --- | --- | --- |
| **Erzeugung Traeger**, 4.000 Partien @100, threads 11 | **14.426,1 s = 4h 00m** | 3,607 s je Partie (`manifest_v24-b07-policy_20260907_194058.json`) |
| **Erzeugung Schwarm temperiert**, 4.000 Partien @100 | **12.755,9 s = 3h 33m** | 3,189 s je Partie, zweite Maschine |
| **Erzeugung Schwarm Ausflug**, 2 x 2.000 Identitaeten | **6.291,1 s + 6.665,7 s = 3h 36m** | 3,142 bzw. 3,329 s je Identitaet; zwei Laeufe, weil `--games` die Ausfluege mitzaehlt (par.19a) |
| **Training v25-b01**, 12 Epochen, 4.704.642 Samples, cuda | **5.779,6 s = 1h 36m** | 27.399,9 s CPU auf 6 Threads, davon 69 s Datenaufbau; rund 8 min je Epoche |
| Gepaartes Gating, SPRT-Stopp nach 40 Paaren, threads 10 | **1.096,2 s = 18 min** | Seed 20261020 |
| Gepaartes Gating, SPRT-Stopp nach 110 Paaren, threads 10 | **3.122,2 s = 52 min** | Seed 20261021 |
| Champion-2-Kante, SPRT-Stopp nach 35 Paaren | **736,7 s = 12 min** | |
| Anker-Kante, festes n=150, 6 Worker | **1.138,4 s = 19 min** | v24-b07 hatte 1.282 s |
| Modell-Snapshot ins restic-Repo (`snapshot_models.ps1`) | **5 s** | 147 Dateien / 581,6 MiB, davon 41 neu |
| Tagesschnappschuss plus `check` | **7 s** | 7.725 Dateien / 9,279 GiB |

**Was daraus fuer v26 folgt** (hergeleitet, nicht gemessen): die drei Erzeugungsbefehle aus
`PREREG_v26_window.md` par.7 kosten zusammen rund 11,1 h, wenn `v25-b01` so schnell zieht
wie `v24-b07`: 4,0 h fuer Nr. 1, 3,5 h fuer Nr. 2 und rund 3,5 h fuer Nr. 3 (4.000
Identitaeten zu 3,142 s). Nr. 3 laeuft diesmal in EINEM Aufruf mit `--games 4000`; in v25
waren es zwei Laeufe zu je 2.000, weil der erste nur 2.002 Identitaeten lieferte.

## Generation v26, gemessen am 2026-09-09

| Aufbau | Dauer | Bemerkung |
| --- | --- | --- |
| **Erzeugung Traeger**, 4.000 Partien @100, threads 11 | **11.077,9 s = 3h 05m** | 2,769 s je Partie (`manifest_v25-b01-policy_20260909_003156.json`), schneller als v25 (3,607), weil der Cache-Waechter seinen Rueckstand abgearbeitet hatte; berichtigt 2026-09-09, vorher standen hier 'rund 3,0 h' und '2,62 s' ohne Artefakt |
| **Erzeugung Schwarm temperiert**, 4.000 Partien | **10.161,0 s = 2h 49m** | 2,540 s je Partie (`manifest_v25-b01-value-tempc_20260909_034044.json`); berichtigt 2026-09-09, vorher stand hier der v25-Schaetzwert 'rund 3,5 h' |
| **Erzeugung Schwarm Ausflug**, 4.000 Identitaeten | **8.837,9 s = 2h 27m** | 2,21 s je Identitaet, EIN Lauf mit `--games 4000` |
| **Training v26-b01**, 12 Epochen, 4.512.977 Samples | **7.441,0 s = 2h 04m** | 34.539,8 s CPU auf 6 Threads, 30,1 s Datenaufbau; langsamer als v25 (5.780 s), weil die G-2-Sonden daneben liefen |
| Gepaartes Gating, 200 Paare @400, threads 10 | **4.281 s / 4.269 s** | rund 21,4 s je Paar |
| Gepaartes Gating, SPRT-Stopp nach 70 Paaren | **1.453 s** | |
| Anker-Kante, festes n=150, 6 Worker | **1.106 s** | |
| Champion-2-Kante gegen das ARTEFAKT, n=150, 6 Prozesse | **rund 36 min** | frozen_referee_match, inkl. Handshake und Golden-Selbsttest |
| Golden Probe fuers Artefakt (10 Sonden @400) | **rund 17 min** | |
| Korpus-Vielfaltssonde, 400 Partien einkernig | **4.234 s** | 10,6 s je Partie -- die Prereg hatte "Minuten" geschaetzt |
| Korpus-Divergenzsonde, 1.002 gepaarte Partien | **6.444 s** | |
| Modell-Snapshot ins restic-Repo | **4 s** | |
| Netz-Paritaets-Fixture (cargo test, warmes target) | **rund 10 s** | plus Gegenprobe |

**Fuer v27 folgt daraus** (hergeleitet aus den drei v26-Manifesten, 30.076,8 s): die drei
Erzeugungsbefehle kosten zusammen rund 8,4 h, die Kette danach rund 2,5 h bis zum fertigen
Training.

## Generation v27, gemessen am 2026-09-10 (Erzeugung)

Generator `v26-b01`, je 4.000 Partien @100, threads 11, Cache-Waechter mit 3 Workern daneben
(`laufzeit`-Bloecke in `data/manifest_v26-b01-*.json`):

| Aufbau | Dauer | Bemerkung |
| --- | --- | --- |
| **Erzeugung Traeger** (policy, Weg C) | **13.769,2 s = 3h 49m** | 3,442 s je Partie (v26: 2,769) |
| **Erzeugung Schwarm temperiert** | **12.574,6 s = 3h 30m** | 3,144 s je Partie (v26: 2,540) |
| **Erzeugung Schwarm Ausflug**, `--games 4000` | **10.567,7 s = 2h 56m** | 2,640 s je Identitaet, 4.003 Identitaeten, 401 Dateien (v26: 2,207) |
| **zusammen** | **36.911,5 s = 10,25 h** | 23 % langsamer als v26 (30.076,8 s) bei gleicher Konfiguration; Ursache NICHT gemessen (Kandidaten: Waechter-Last beim Blockbau der neuen Dateien, OneDrive-Sync). Fuer die Planung der naechsten Erzeugung gilt die langsamere Zahl |

## Generation v28, gemessen am 2026-09-11 (Erzeugung)

Generator `v27-b01`, je 4.000 Partien @100, threads 11, Cache-Waechter daneben, dazu die
Claude-Partien der Parallelsitzung (Nebenlast klein, aber vorhanden; `laufzeit`-Bloecke in
`data/manifest_v27-b01-*.json`):

| Aufbau | Dauer | Bemerkung |
| --- | --- | --- |
| **Erzeugung Traeger** (policy, Weg C) | **12.732,4 s = 3h 32m** | 3,183 s je Partie (v27: 3,442) |
| **Erzeugung Schwarm temperiert** | **11.632,4 s = 3h 14m** | 2,908 s je Partie (v27: 3,144) |
| **Erzeugung Schwarm Ausflug**, `--games 4000` | **11.361,3 s = 3h 09m** | 2,837 s je Identitaet, 4.005 Identitaeten, 401 Dateien (v27: 2,640) |
| **zusammen** | **35.726,1 s = 9,92 h** | 3 % schneller als v27 (36.911,5 s). Die v26-Zahl (30.076,8 s) ist KEINE Referenz derselben Maschine: Teile der v26-Erzeugung liefen ausgelagert (Nutzer 2026-09-11); die "Verlangsamung" seit v27 ist damit kein Befund. Planungsgroesse fuer diese Maschine: rund 10 h |
| Tor 2a ex post (`corpus_sanity_check.py`, 4.000 Partien) | 270,7 s | 1 Thread |
| Kette Schritte 2-6 (Manifest, G-2, Fenster, Monolith-Schluessel) | 5 s | Bloecke lagen bereits (Waechter); der erste Merge starb an 24 Bloecken mit 755 Spalten (PREREG_v28_window.md par.10), Neubau der 24 Bloecke 112 s |
| Monolith-Merge 2.800 Bloecke, 1,10 GB | 531 s = 9 min | Wiederaufnahme 10:20:16-10:29:07, mit Formen-Waechter |
| **Training v28-b01**, 12 Epochen, Fenster 2.947 Dateien, 4,43 M Zustaende | **5.156,6 s = 1,43 h** | Datenaufbau 33,5 s, fast-loader, cuda; v27: 5.116,7 s |
| **Tor 1** gepaartes Gating @400, 10 Threads, `--log-games`, Seed 20261036 (SPRT-Stopp nach 145 Paaren) | **3.979,6 s = 66 min** | 290 Partien, 13,7 s je Partie |
| **Tor 1** Replikation Seed 20261037 bis zum Deckel 200 Paare | **5.446,0 s = 91 min** | 400 Partien, 13,6 s je Partie (v27: 5.182 s) |
| Tor 2b `arena_column_probe.py` auf 290 / 400 Partie-Logs | 83 s / 108 s | 1 Thread, Replayer |
| Plattenpunkte je Kriterium (`plate_points_from_arena.py`, 400 Partien) | unter 10 s | – |
| Blockbau 2.947 Dateien unter neuem Schluessel, 6 Worker, Rust-Merkmalsbauer (`MOSAIC_FEATURES_FROM_RUST=1`) | 1.582 s = 26 min | 1,86 Bloecke je s; Python-Pfad nicht unter gleichen Bedingungen gemessen |
| Monolith-Merge 2.800 Bloecke, 1,11 GB (b02) | 551 s = 9 min | mit Formen-Waechter |
| Blockbau 2.800 Dateien unter NEUEM Schluessel `421448d12eb8` (Formel-Version, `MOSAIC_FEATURES_FROM_RUST=1`), 6 Worker, PLUS Merge (Kette `night_v29_b08_head_pair.sh`, 2026-09-17 09:34-10:07) | **1.964 s = 32,7 min** gesamt, Bloecke rund 1.100 s (2.235 nach 1.096 s) | exklusiv; erste Kette auf dem Schluessel mit Formel-Version |
| Kompilat Variante C + Stichentscheid-Knopf 2026-09-17: `cargo test --release --lib` (Build 45 s, 703 Tests 100 s) / `--no-run` / Fixture-Neubau / `maturin build --release` | 146 s / rund 60 s / 2 x 0,1 s / 72 s inkl. Fixture-Test | neben GPU-Training v29-b08 (Val-Cache-Bau einkernig) |
| Training Warm-Start 12 Epochen, b03-Rezept mit ownership-Loss 0 und ohne endgame-Kopf (v29-b08, `manifest_train_v29-b08_20260917_100659.json`), `--fast-loader`, Monolith per `--cache-file`, Val-Cache neu (147 Dateien, einkernig, rund 8 min) | 4.538.842 Samples, 794 | CUDA, GEBREMST (Kompilat 10:12-10:14 daneben) | **4.456 s = 74 min** (b06 ohne Nebenlast 57 min) |
| Tor 1 b08 gegen b03, Seeds 20261160 / 20261161, je 200 Paare mit Logs, kein Frueh-Stopp | 4.606,9 s / 4.605,4 s | 11,5 s je Partie, 10 Threads, exklusiv (Referenz fuer die 884-Kette) |
| Kostentor Variante C (884-Wheel mit Tiling-Projektion im Encoder): Champion gegen sich selbst, 2 x 20 Paare, 10 Threads, Logs | 11,84 s / 11,34 s je Partie | exklusiv; gegen 11,5 s (Tor 1 b08, altes Wheel, exklusiv) +0,6 Prozent; gegen die registrierte Referenz 13,33 s (neben GPU-Training) -13 Prozent |
| Blockbau 2.800 Dateien unter 884 (Tiling-Projektion je Record, Schluessel `790ac07353a6`), 6 Worker, plus Merge | **2.144 s = 35,7 min** | exklusiv; gegen 1.964 s unter 794 am selben Tag +9,2 Prozent |
| A/B Stichentscheid an gegen aus, Champion @400, 200 Paare mit Logs, 10 Threads | 6.183 s = 103 min | 15,5 s je Partie NEBEN GPU-Training v29-b07 (exklusiv waeren rund 11,5 s) |
| Training Warm-Start 12 Epochen, b03-Rezept 1:1 auf 884 Eingaengen (v29-b07, `manifest_train_v29-b07_20260917_145251.json`), `--fast-loader`, Monolith per `--cache-file`, Val-Cache neu | 4.538.842 Samples, 884 | CUDA, GEBREMST (A/B mit 10 Threads daneben, Commit-Hook) | **6.757 s = 113 min** |
| Tor 1 b07 (884) gegen b03 (794) auf dem 884-Wheel, Seeds 20261190 / 20261191, je 200 Paare mit Logs | 4.971,5 s / 4.794,2 s | 12,4 / 12,0 s je Partie, 10 Threads, exklusiv; gegen 11,5 s auf dem 794-Wheel +4 bis +8 Prozent (Encoder-Projektion) |
| Training Warm-Start 12 Epochen, v30-Rezept auf 884 (v29-b09: moon 0, ownership 0, ohne endgame; `manifest_train_v29-b09_20260917_200920.json`), Monolith per `--cache-file`, Val-Cache-Treffer | 4.538.842 Samples, 884 | CUDA, GEBREMST (K6-A/B 10 Threads daneben) | **4.330 s = 72 min**; Split plus Merge liegender Bloecke vorher 827 s |
| K6: Kostentor 2 x 20 Paare exklusiv / A/B Dosis 0,5 (195 Paare, SPRT-Stopp) neben GPU-Training | 11,82 / 11,98 s je Partie / 5.879 s = 98 min, 15,1 s je Partie | Kostentor auf dem 884-Wheel mit K6 gegen 11,5 s Referenz +3,5 Prozent; A/B gebremst durch das Training |
| Tor 1 b09 (884) gegen b03 (794), Seeds 20261220 / 20261221, je 200 Paare mit Logs | 4.912,1 s / 5.090,3 s | 12,3 / 12,7 s je Partie, 10 Threads, exklusiv bis auf den Commit-Hook um 21:40 |
| K6 A/B Dosis 0,25 gegen aus, Champion @400, 200 Paare mit Logs, 10 Threads | 4.925,6 s = 82 min | 12,3 s je Partie, exklusiv, 884-Wheel |
| Champion-Kanten je Kandidat (884-Wheel, exklusiv): Gating 2 x 200 Paare / Anker 150 Partien hv4@150 / Champion-2 150 Partien @400 | 4.898 + 4.896 s bzw. 4.778 + 4.855 s / 1.246 bzw. 1.281 s / 2.388 bzw. 2.340 s | Summe je Kandidat rund 3,7 h; b07 01:48-05:36, b09 05:36-09:21 |
| 414/888-Wheel: Kostentor b10 gegen sich selbst 2 x 20 Paare / A/B b11 gegen b09 (175 Paare, SPRT H1) / Self-Play-Probe 20 Partien @100 mit neuen Knoten | 17,1 und 15,3 s je Partie / 5.040 s = 14,4 s je Partie / 79,6 s = 3,98 s je Partie | exklusiv; gegen 12,0 s (884-Wheel) +35 Prozent; Probe gegen v28-Erzeugung 3,18 s je Partie +25 Prozent |
| **Training v28-b02** (Variante B, 755), 12 Epochen | **5.262,3 s = 1,46 h** | GEBREMST (cargo test des Pre-push-Hakens um Epoche 6/7); b01 5.156,6 s |
| Tor 1 b02 gegen b01, Seeds 20261038 / 20261039, je 200 Paare mit Logs | 5.562,5 s / 4.773,3 s | 13,9 bzw. 11,9 s je Partie, 10 Threads; der zweite Lauf ohne Nebenlast |
| Block-Ziehungs-Diagnostik (`dome_stack_known_block_draw_probe.py`, 400 Partien) | 105 s / 129 s | 1 Thread, Replayer |
| K3-D-Bau: `cargo test --release --lib` (576 Tests) / Wheel / Anker-Drift | 80 s Tests, 26 s Wheel-Bau, rund 25 s Drift | Vollast nur beim Bauen |
| Ablation b03: Monolith 2.546 Bloecke / Training 3,88 M Zustaende / Tor 1 (80 + 35 Paare) | 7 min / 4.322 s / 1.994 s + 868 s | Nebenlast: Claude-Partien der Parallelsitzung |
| Ablation b04: Monolith 2.403 Bloecke / Training 3,60 M Zustaende / Tor 1 (60 + 115 Paare) | 6 min / 4.511 s / 1.581 s + 2.922 s | dito |
| Code-Abschluss Stufe 1: Tests (585) / Paritaets-Fixture / Wheel / Drift | 80 s / 14 s / 26 s / 17 s | – |
| Anker-Kante Segment 2 (hv4_anchor, `frozen_referee_match.py`, n=150, 6 Worker), 3 Kanten | **1.441 / 1.491 / 1.489 s** | 9,6-9,9 s je Partie; Artefakte `anchor_v2_arena_<name>.json` |
| Nachbar-Kante Segment 2 v28-b02 gegen v27-b01 (paired_gating, 10 Threads, Logs), SPRT nach 115 Paaren | **3.243 s** | 14,1 s je Partie |
| Knopf-Bau 2026-09-12: Lib-Tests (601) / no-run / Wheel+pip / Drift / Konservierung / Sonden-Rauchtest | 84 s / 33 s / 34 s / 19 s / 12 s / 18,7 s | `tools/night_v28_knob_build.sh` |
| Replikation Nachbar-Kante Seed 20261046, 200 Paare bis zum Deckel, 10 Threads, Logs | **5.449 s** | 13,6 s je Partie |
| Spaltensonde / Plattenpunkte je Kante (230 bzw. 400 Partien, Replay) | 49 s + 1 s / 108 s + 1 s | einkernig |
| Champion-2-Kante gegen Artefakt v26-b01 (Cross-Aera, 150 Partien, 6 Prozesse) | **2.516 s** | 16,8 s je Partie |
| sigma/Prior-Balance (300 Zustaende @400) / Platt v3 / Platt v1 | 787 s / 12 s / 9 s | |
| Paritaets-Fixture schreiben + Gegenprobe (je cargo test, warm) | 2 x ~14 s + Bau ~32 s | ein Schreiblauf scheiterte an einer OneDrive-Dateisperre (os error 32), Wiederholung gruen |
| Abnahme Variante B 2026-09-17 (`MOSAIC_ROUND_TRANSITION_LEAF`): `--no-run` / `maturin build --release` / `pip install` / Lib-Suite 673 Tests / Anker-Drift / Anker-Konservierung | 56 s / 28 s / 3 s / 108,4 s (78,1 s Testzeit) / 22,4 s / 16,6 s | warmes `target`; zweites Wheel mit dem Diagnose-Export 26 s + 1 s, Drift 22,8 s, Konservierung 16,4 s |
| Sichttor Variante B (`round_transition_leaf_sight_gate.py`), 300 Blatt-Zustaende Runde 3/4 | **41,1 s** (CPU 40,4 s) | 1 Thread, 0,137 s je Zustand; Loeser plus EINE Neubefuellung je Zustand |
| Paritaetssonde Rust gegen Python (`feature_parity_rust_python.py`, 4 Partien + 3 Korpusdateien) | 14,0 s | 1 Thread; Stand 2026-09-17 ROT in der Korpus-Population (Kanal 76), Befund aelter als der Variante-B-Bau |
| Einfrieren v28-b02: venv 24 s / Golden Probe (10 Sonden @400, einkernig) **1.450 s** / Referee-Selbsttest 2 Partien 78 s | | `tools/night_v28_freeze.sh` |
| Ueberraschungs-Kante v24-b05 gegen v24-b04 (paired_gating, SPRT H0 nach 100 Paaren, 10 Threads, Logs) | **2.731 s** | 13,7 s je Partie |
| C2 argmax-Instrument (self_play.py 200 Partien @400 deterministisch, 11 Threads) plus corpus_sanity_check | **~2.050 s + 12 s je Lauf** (4 Laeufe 07:31-09:49) | 10,3 s je Partie |
| Orakel-Bruecke Such-Variante (oracle_metrics --search-sims 400, frozen_v3, 1.144 Zustaende, einkernig) | **343-371 s je Einstellung** | 0,33 s je Zustand |
| Dritter Seed Nachbar-Kante, 200 Paare bis zum Deckel, Fruehstopp aus, 10 Threads, Logs | **5.405 s** | 13,5 s je Partie |
| Startkuppel Stufe 0 (arena_match Heuristik, 9 Slots x 60 Partien x 2 Sims-Stufen, threads 0) | **430 s** fuer 1.080 Partien | 0,40 s je Partie |
| argmax-Instrument je Knopf (Jokerfeld / K3-D, 200 Partien @400) | 41 min (gebremst, neben Push-Build) / 36 min | |
| Such-Start A/B (paired_gating, SPRT H0 nach 95 Paaren, 10 Threads, Logs) | **2.977 s** | 15,7 s je Partie (Such-Start kostet je Partie eine Suche mehr) |
| Such-Start A/B Wiederholung (SPRT H0 nach 85 Paaren) / Spaltensonde Replay 170 Partien / Plattenpunkte | **2.545 s** / 48 s / < 5 s | 15,0 s je Partie |
| Sprosse Netz@100 gegen Heuristik-Artefakt (Referee, 50 Partien, 6 Prozesse) / Netz@100 gegen Netz@400 live (paired_gating, 30 Paare, 10 Threads, Logs) | 155-167 s / 497 s | 3,2 s / 8,3 s je Partie |
| Champion v28-b02@100 gegen @400 (paired_gating, 15 Paare, Logs) / Spaltensonde Replay 30 Partien | 256 s / 6 s | 8,5 s je Partie |
| Netz@25 gegen Heuristik-Artefakt @150 (Referee, 50 Partien) / Netz@25 gegen Netz@100 live (paired_gating, 50 Paare) | 73-92 s / 294 s | 1,6 s / 2,9 s je Partie |
| Heuristik-Artefakt @600 gegen @150 (Referee, 150 Partien, 6 Prozesse) / Netz@25 gegen Heuristik @600 (150 Partien) | 111 s / 254 s | 0,7 s / 1,7 s je Partie |
| Sprossen-Kanten (frozen_referee_match, 50 Partien, 6 Prozesse) | Netz gegen Netz-Artefakt 917-963 s; Heuristik gegen Heuristik 53 s; Netz gegen Heuristik 365-464 s | je Block |
| Treppe 2026-09-13: Netz@100 gegen Heuristik-Artefakt @600 (Referee, 3 x 50 Partien, 6 Prozesse) | 166 / 164 / 151 s | 3,2 s je Partie; `rung_v22b05s100_vs_hv4s600_b*.json` |
| Treppe 2026-09-13: Netz@400 gegen Heuristik-Artefakt @600 (Referee, 3 x 50 Partien, 6 Prozesse) | 389 / 421 / 413 s | 8,2 s je Partie; `rung_v22b05s400_vs_hv4s600_b*.json` |
| Treppe 2026-09-13: Netz@25 gegen Netz@100 live (paired_gating, 75 Paare bis zum Deckel, 10 Threads, Logs) | **423 s** | 2,8 s je Partie; `paired_gating_v22-b05_s25_vs_s100_seed53_full.json` |
| Treppe 2026-09-13: Netz@100 gegen Netz@400 live (paired_gating, 75 Paare bis zum Deckel, 10 Threads, Logs) | **1.062 s** | 7,1 s je Partie; `paired_gating_v22-b05_s100_vs_s400_seed54_full.json` |
| hv2-Gegenprobe Startkuppel (9 Slots x 20 Referee-Partien, 6 Prozesse) | **219 s** | 1,2 s je Partie |
| hv3: Bau-Tore (629 Tests 85 s, Wheel, Drift, Konservierung) / Einfrieren mit Golden Probe / venv+Konservierung / 2 Heuristik-Kanten a 150 | 4 min / 30 s / 30 s / je ~2 min | `tools/night_hv3_freeze_edges.sh` |
| Such-Start Huellen-Diagnose (2 x 100 Partien @400 argmax) | 37 min / 30 min | |
| Platte/Rotation-Sonde Startkuppel (netzfrei, hv1, 200 Seeds x 2 Arme x Paarungen @25 und @400 = 800 Partien, alle Kerne) | **322 s** | 0,40 s je Partie |

## Generation v27, gemessen am 2026-09-10 (Abnahmen und Promotion)

| Aufbau | Dauer | Bemerkung |
| --- | --- | --- |
| **Training v27-b01**, 12 Epochen, Fenster 2.947 Dateien | **5.116,7 s = 1h 25m** | 25.933 s CPU, Datenaufbau 35,4 s; Maschine sonst frei |
| Kette Schritte 1-6 (4 Trägerkennzahlen, Manifeste, Fenster, Monolith) | **rund 31 min** | Bloecke lagen vom Waechter vollstaendig vor |
| Gepaartes Gating 200 Paare @400, threads 10, MIT `--log-games` | **5.181,5 s / 5.189,7 s** | 13,0 s je Partie; ohne Logs 10,7 s (v26). Artefakt 9,8 MB |
| Gepaartes Gating, SPRT-Stopp nach 45 Paaren, mit Logs | **1.139,5 s** | |
| Spaltensonde auf 400 Partie-Logs | **83 s** einkernig | |
| Anker-Kante, festes n=150, 6 Worker | **1.333,3 s** | 8,9 s je Partie |
| Champion-2-Kante gegen das Artefakt v25-b01, n=150, 6 Prozesse | **2.578 s = 43 min** | inkl. Handshake und Golden-Selbsttest |
| sigma/Prior-Kalibrierung, 300 Zustaende @400 | **rund 13 min** | |
| Platt-Fit, 1.440 Zustaende | **rund 10 s** je Set | |
| Golden Probe fuers Artefakt (10 Sonden @400) | **rund 23 min** | 14:53-15:16 |
| Referee-Selbsttest, 2 Echtpartien | **67 s** | |
| Paritaets-Fixture (cargo test, warmes target) | **rund 12 s** je Lauf | plus 43 s Kompilat |
| Anker-Drift-Pruefung nach Wheel-Bau | **rund 25 s** | 1.763 Schritte |
| A/B-Kante ueber den Referee, gleiches Netz, Live gegen Artefakt, n=150, 6 Prozesse | **2.515 s / 2.621 s** | rund 17 s je Partie |
| Orakel-Replay einer Partie, 98 Entscheidungen @400 (exakter Zustand) | **rund 290 s** | je Lauf |
| Null-Klammer-Sonde Stufe 0, 4.000 Partien plus 30 Logs, einkernig | **283 s** (360 s unter Fremdlast) | |
| Wheel-Bau plus Install | **rund 30 s** (warmes target) | |

## Sims-Kurve am Champion v28-b02, gemessen am 2026-09-13 (`PREREG_search_depth_column_optimum.md` par.8e)

| Aufbau | Dauer | Anmerkung |
| --- | --- | --- |
| Teil A, gepaarte Arena v28-b02@100 gegen @400, 75 Paare, threads 10, mit `--log-games` | **1.121,1 s** | 7,474 s je Partie, 150 Partien, Seed 20261055 |
| Teil A, dasselbe mit @200 gegen @400 | **1.385,9 s** | 9,239 s je Partie, Seed 20261056 |
| Teil A, dasselbe mit @600 gegen @400 | **2.363,8 s** | 15,758 s je Partie, Seed 20261057 |
| Teil B, argmax-Self-Play @100, 200 Partien, threads 11 | **791,2 s** | **3,956 s je Partie**, 35.348 Zuege |
| Teil B, argmax-Self-Play @200 | **1.047,3 s** | **5,237 s je Partie**, 35.296 Zuege |
| Teil B, argmax-Self-Play @400 | **1.492,9 s** | **7,464 s je Partie**, 35.537 Zuege |
| Teil B, argmax-Self-Play @600 | **2.112,5 s** | **10,563 s je Partie**, 35.403 Zuege |

Die Teil-B-Zeilen sind die Kostenbasis fuer den Zuschnitt eines Sockels von 4.000 Partien:
@100 4,40 h, @200 5,82 h, @400 8,29 h, @600 11,74 h (Multiplikation der gemessenen Sekunden je
Partie, auf dieser Groesse selbst nicht gemessen). **Falle:** der `laufzeit`-Block IM Artefakt
`depth_curve_<S>_v28b02.json` misst den Auswertungslauf von `corpus_sanity_check.py` (10-11 s,
threads 1, `s_je_partie` null), NICHT die Erzeugung; die Erzeugungsdauer steht in
`data/manifest_depth<S>-v28b02_*.json`.


## Encoder-Abschnitt 16 und die Nacht-Werkzeuge, gemessen am 2026-09-13/14

**ACHTUNG, alle Zahlen dieses Abschnitts sind GEBREMST:** sie wurden waehrend der laufenden
v29-Erzeugung genommen (Offenlegung in `evaluations/STATUS.md` Abschnitt 1). Als Planungsgroesse
taugen sie deshalb nur als Obergrenze.

| Lauf | Dauer | Bemerkung |
| --- | --- | --- |
| `cargo test --release --lib` (641 Tests, Abschnitt 16 gebaut) | **149,6 s** bis **194,2 s** | dreimal gefahren NEBEN DER ERZEUGUNG; die Streuung ist die Nebenlast |
| dieselbe Suite neben einem GPU-Training statt neben der Erzeugung | **100,3 s** | der Vergleich zeigt, was die Erzeugung gekostet hat: rund die Haelfte |
| Kompilieren allein (warmes target, nach Encoder-Aenderung) | **76 s** bis **83 s** | – |
| Feature-Golden-Fixture neu schreiben (`MOSAIC_UPDATE_FEATURE_FIXTURE=1`) | **0,05 s** Test plus 83 s Bau | 130 Zeilen |
| Netz-Paritaets-Fixture neu schreiben (3 Partien, 8 Sims) | **29,8 s** Test, 33,2 s gesamt | Champion v28-b02 |
| `cargo test --release --no-run` (alle Ziele) | rund **80 s** | Beispiele und Benchmarks |
| `dead_unit_probe.py`, 3 Modelle x 24 Zustaende | **1,5 s** | voller Satz (1.800) ungemessen |
| `corpus_behaviour_audit.py`, 10 Partien aus einer Datei | **0,5 s** bis **1,1 s** | rund 0,05 s je Partie |
| `corpus_behaviour_audit.py`, 2.500 Partien aus 228 Dateien | rund **2 min** | single-threaded, nur Lesen |

**Zwei Stolperfallen, beide mit Wiederholung geloest** (Muster `pitfalls.md`): zweimal brach
`cargo test` mit `LNK1104: cannot open file ... .exe` ab, weil der Testlaeufer des VORIGEN Laufs
die Datei noch hielt. Kein Testfehler, kein Schaden -- aber wer die Laeufe hintereinander
startet, muss das Ende des vorigen abwarten, nicht nur seinen Exit-Code.

## Counterfactual-Ranking-Sonde (Stufe 0), gemessen am 2026-09-17, exklusiv

`tools/probes/counterfactual_tiling_ranking.py`, registrierte Einstellungen
**sims 400 / M 6 / max-cands 4**, 1 Thread, ONNX-Sitzung einmal gebaut. Die beiden Runden
kosten VERSCHIEDEN viel, und zwar um den Faktor 3,7: in R4 antwortet nach der Neubefuellung
der Runde-5-Alpha-Beta-Loeser, der die Sim-Zahl nicht liest, in R1-R3 laeuft die Baumsuche
wirklich. Eine Zahl auf die andere Runde hochzurechnen geht deshalb schief.

| Lauf | Umfang | Wanduhr | s je Stellung | Artefakt |
| --- | --- | --- | --- | --- |
| Kostenmessung R4 | 3 Stellungen, 8 Paare | 9,4 s | **3,132** | `counterfactual_ranking_cost_probe.json` |
| Kostenmessung R3 | 3 Stellungen, 18 Paare | 35,1 s | **11,708** | `counterfactual_ranking_cost_probe_r3.json` |
| Volllauf R4 (400 Fensterdateien, Deckel 2 je Datei) | 800 Stellungen, 3.744 Paare | **2.644,5 s** (44 min), CPU 2.596,6 s | **3,306** | `counterfactual_ranking_r4.json` |
| Volllauf R3 (150 von 400 Dateien gebraucht) | 300 Stellungen, 1.461 Paare | **3.283,3 s** (55 min), CPU 3.229,7 s | **10,944** | `counterfactual_ranking_r3.json` |

**Planungsgroesse:** rund 3,3 s je R4-Stellung und rund 11,7 s je R3-Stellung; das Angebot des
v29-Fensters ist bei `--max-per-file 2` ueber 400 Dateien auf rund 800 Stellungen je Runde
begrenzt (in R4 gemessen: 800 aus 1.106 gescannten, der Rest ist eindeutig).
