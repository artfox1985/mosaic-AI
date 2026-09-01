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
| Gepaarte Arena b05@400 gegen Heuristik@150 | 2 x 100 Partien | 10 | **3,33 s je Partie** (666 s), rund 34 s je Block von 10 |

**Parallelisierung ist ergebnisneutral, gemessen statt angenommen** (20 Seeds
beidseitig): Siegquote 0,450, volle Spalten 1,200 und Punkte 55,0 in BEIDEN
Faellen identisch, bei 4,8-fachem Tempo. Grund:
`PREREG_search_rng_split.md` -- jede Partie haengt an ihrem eigenen,
abgeleiteten Suchstrom.
