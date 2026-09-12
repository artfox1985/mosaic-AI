<!-- STATUS: OFFEN | Frage: Wie wird der Code vor dem Projektende sauber hinterlassen -- welche der beim Review 2026-09-11 gefundenen Defekte, Fussangeln und Altlasten werden behoben, in welcher Reihenfolge, mit welchen Toren? | Beleg: STUFE 1 GEBAUT (par.8: acht Punkte, 585 Tests gruen, Paritaets-Fixture wegen A2 bewusst neu, Kontrakt-Hash 39648b95bbba1acf). ANKER-DRIFT ROT durch A2 (Phantom-Abzug bewegt den lebenden hv1 ab Schritt 99; Gegenprobe ohne A2 gruen): Nutzer-Entscheid (a) Anker neu setzen, (b) A2 zuruecknehmen, (c) Knopf. Stufen 2/3 nach der letzten Generation. -->

# Vorregistrierung: Code-Abschluss (Aufraeumen vor dem Projektende)

**Angelegt 2026-09-11, 23:10** auf Nutzer-Auftrag ("pack das ganze in ein prereg, stufe 1 ist
freigegeben"), nach dem Code-Review vom selben Tag (Nutzer: "wenn wir das projekt abschliessen
in den naechsten generationen will ich es sauber hinterlassen"). Quelle: die sechs
Bereichsberichte und die Zusammenfassung unter `evaluations/review/code_review_2026-09-11_*.md`.
Diese Prereg registriert, WAS gebaut wird und mit welchen Toren; die Herleitung der Funde
steht in den Berichten mit Datei:Zeile.

## par.1 Anlass und Zweck

Das Projekt endet nach ein bis zwei Generationen nach v28. Der Code soll so zurueckbleiben,
dass ein Leser ihn ohne die Sitzungen versteht: keine stillen Defekte, keine Fussangeln in
Werkzeugen, keine Zweige, die entschiedene Knoepfe offen halten, keine widersprechenden
Kommentare. Das Review fand KEINE Regelabweichung gegen `docs/engine_manual.md`; es fand
stille Defekte der Sorte, die keine Arena sieht (CLAUDE.md "Symmetrische Defekte"), Fussangeln
und Altlast. Aufraeumen ist Infrastruktur: das Erfolgsmass sind Irrtumskosten und
Nachvollziehbarkeit, nicht Elo (CLAUDE.md "Infrastruktur bewerten").

## par.2 Bestand (geprueft am Code, 2026-09-11)

| Nr | Fund | Prüfstelle | Stufe |
| --- | --- | --- | --- |
| A1 | Netz-Auswertungsfehler wird still zu einem 0,5-Blatt; kein Zaehler | `net_mcts.rs:1922-1926`, `:1612-1614`, elf Stellen laut Bericht | 1 |
| A2 | Phantom-Fliesen in `pattern_lines[].tiles` werden in `remaining_colors`/`still_reachable_colors` nicht abgezogen (self_play.rs tut es) | `round_end.rs:635-638`, `provocation.rs:609-617`, `self_play.rs:6111-6117` | 1 |
| A3 | Spec-Prüfung laesst `score_utility_b = 0` durch (Vorzeichenfunktion, NaN bei x == x0) | `net_mcts.rs:577`, `:1751` | 1 |
| A4 | Bonuschip-Sperre nur in den Aufrufern, nicht in `apply_bonus_chips_with` | `round_end.rs:460-468`, `:613` | Entscheid (par.6) |
| A5 | Slot-Indizes aus HTTP ungeprueft in Rust-Indexzugriffe; Panic faengt `except Exception` nicht | `game.rs:232`, `game.rs:570-573`, `server.py:1000/1046` | 1 |
| A6 | `Game::is_over()` ab Rundenbeginn 5 wahr | `game.rs:700` | 2 |
| A7 | Eroeffnungs-Records: Policy-Ziel auf toter ID 405, aber Gewicht 0 | `features.rs:1477`, `corpus_dataset.py:1331` | 2 |
| A8 | `--val-frac 0` verwirft still die Fensterliste; drei Doku-Stellen empfehlen den Weg | `train.py:1394-1398`, `corpus_dataset.py:356`; `docs/working_rules.md:162`, `PREREG_v23_window.md:532`, `PREREG_cache_build_time.md:533` | 1 |
| A9 | `MOSAIC_PHASE_AMP/_PEAK/_STAGE` ohne Lesestelle; `phase_sweep.py` misst nichts; Registratur-Waechter prueft Textvorkommen | `knob_registry.rs:112-114`, `:309-323`, `tools/probes/phase_sweep.py:77-79` | 1 |
| A10 | Kontrakt-Hash deckt `ownership`-Kopf und Planes-Geometrie nicht | `lib.rs:639-648`, `net.rs:885` | Entscheid (par.6) |
| A11 | Mutex je Knoten bei ausgeschaltetem Sammel-Faden; GameState-Klon je Knoten | `net_mcts.rs:1874-1890`, `:2044` | 2, erst messen |
| A12 | "nur der erste Mondstapel je Fabrik" | WIDERLEGT (Klaerung 2026-09-05, `PREREG_stack_top_feature.md` par.10 P.8) | kein Fund |
| A13 | Doku-Drift (vier Kommentare widersprechen dem Code, verschobene Zeilenverweise) | Berichte Bewertung/Suche/Netzschicht | 3 |

Altlast (Berichte, gepruefte Zahlen im Summary): tote Funktionen (`board.rs:208-222`, vier
Diagnose-Einstiege in `self_play.rs`, Inversions-Pfad Runde 5, `envelope::tiling_cost_delta`,
37 von 64 oeffentlichen Funktionen in `envelope.rs` ohne externen Aufrufer), rund 4.800 Zeilen
Plattenbauer-Code hinter entschiedenen Knoepfen, `--encoder flat` als Default in vier
Werkzeugen, acht Server-Endpunkte ohne Frontend, Testmodul = halbe `net_mcts.rs`, deutsche
Bezeichner (Kern 13, `plate_builder.rs` 25 von 28 Typnamen).

## par.3 STUFE 1: Korrektheit und Beobachtbarkeit (FREIGEGEBEN 2026-09-11)

**Was gebaut wird, je Punkt mit Tor:**

1. **A1 Zaehler und Warnung fuer Netz-Auswertungsfehler.** Ein prozessweiter Zaehler
   (`AtomicU64`) in `net_mcts.rs`, an allen elf `unwrap_or_else`-Stellen erhoeht; Warnung beim
   ersten Fall (einmalig, wie die vorhandenen `OnceLock`-Warnungen); der Zaehler geht in
   `engine_config`/Lauf-Manifest (`lib.rs`) und in das Arena-Artefakt (`paired_gating`). Regel
   fuer Arena und Self-Play: Zaehler > 0 wird im Artefakt als `net_eval_failures` gefuehrt und
   im Bericht laut gemeldet; kein Abbruch (die Suche hat ein definiertes Fallback), aber kein
   stilles Ergebnis mehr. Tor: Bit-Identitaet der Suche (kein Verhaltenswechsel), Netz-
   Paritaets-Fixture unveraendert.
2. **A2 Phantom-Abzug** in `provocation::remaining_colors` und `still_reachable_colors`, nach
   dem Muster von `self_play.rs:6111-6117` (`phantom_count.min(raw)` je Reihe und Farbe). Tor:
   Unit-Test mit einer Reihe mit Phantomen; Anker-Drift danach. Dieser Punkt KANN Zuege
   bewegen (Erreichbarkeits-Kanal 76, `col_f_max`, K3-R/K3-D lesen den Restvorrat): ROT in der
   Drift ist NUTZER-ENTSCHEID (Anker neu setzen oder Aenderung zuruecknehmen), keine Reparatur.
   Erwartung: GRUEN, weil hv1 keinen dieser Konsumenten liest (ANNAHME, die Drift prueft es).
3. **A3 Bereichspruefung** fuer `score_utility_b > 0` in `from_spec_file` und `from_env`,
   Fehlermeldung wie bei `special_row6_w`. Tor: Spec-Test, alle Spec-Dateien im Baum laden.
4. **A5 Bereichspruefung** der Slot-Indizes in `validate_draw_from_stack` und
   `apply_start_placement` (Fehler statt Panic), und in `server.py` vor dem Aufruf. Tor:
   Unit-Test mit Index 3, Rauchtest der Route nicht noetig (kein Verhaltenswechsel fuer gueltige
   Eingaben).
5. **A8** `train.py`: `--file-list` zusammen mit `--val-frac 0` ist ein Fehler mit klarer
   Meldung (oder die Liste wird immer geehrt; Entscheid beim Bau, Meldung ist der kleinere
   Eingriff); die drei Doku-Stellen nachziehen. Tor: keine Kette betroffen (alle fahren 0,05).
6. **A9** Registratur: die drei Phasen-Knoepfe auf UEBERHOLT mit Vermerk "keine Lesestelle";
   `tools/probes/phase_sweep.py` bekommt einen Kopfhinweis "wirkungslos seit ..." (Loeschung
   nur mit Freigabe); Registratur-Waechter (`knob_registry.rs:309-323`) prueft Lesestellen
   (`read_*_env("NAME")`, `env::var("NAME")`) statt Textvorkommen und scannt `tools/` nicht
   mehr. Tor: `cargo test --lib knob_registry` gruen, `docs/knobs.md` generiert.

7. **A4 Chip-Sperre in die Arbeitsfunktion** (ENTSCHIEDEN 2026-09-11, 23:30, Nutzer: "ja, nimm
   A4 und A10 mit rein"): die Pruefung `row_idx >= tiled_max_row` aus `round_end.rs:460-468`
   nach `apply_bonus_chips_with` (`:613`) ziehen, Aufrufer unveraendert (doppelte Pruefung
   ist harmlos). Tor: Unit-Test gesperrte Reihe -> false; Anker-Drift (kann Zuege bewegen,
   falls ein Aufrufer heute nicht filtert; ROT ist Nutzer-Entscheid).
8. **A10 Kontrakt-Hash erweitern** (ENTSCHIEDEN 2026-09-11, 23:30): `contract_canonical_string`
   (`lib.rs:639-648`) um `PLANES_H`/`PLANES_W` und den Kopf `ownership` (Reihenfolge wie
   `net.rs` sie sucht) erweitern. Der Hash wechselt (heute c65768636c0560a7); die Manifeste
   der eingefrorenen Artefakte behalten ihren alten Hash, Kanten dagegen laufen Cross-Aera
   (`--force-cross-era`, Regel 2026-08-29; seit Variante B ohnehin). Tor: `cargo test`
   (Kontrakt-Tests), neuer Hash in `PREREG_v29_window.md` par.3/par.4 nachziehen, Registrierung
   hier in par.8 mit altem und neuem Hash.

**Reihenfolge und Randbedingungen:** Code schreiben darf neben der laufenden Ablations-Kette
(kein Build); `cargo test`, Wheel, Paritaets-Fixture und Anker-Drift erst, wenn keine Messung
laeuft (nach der Kette, vor dem naechsten Messlauf des v28-Programms). Ein Wheel, ein
Drift-Lauf, ein Commit je Punkt oder gesammelt; `cargo test --release --no-run` vor dem Push
(examples/benches). Bezeichner englisch. Kosten: rund 4 h Bau plus 5 min Tore (ANNAHME).

**Verdikt Stufe 1:** alle sechs Tore gruen, Drift gruen (oder Nutzer-Entscheid bei ROT),
Registrierung in par.8.

## par.4 STUFE 2: Altlast (nach der letzten Generation, VOR dem Einfrieren des Schlussstands)

Nicht freigegeben; Umfang ist Nutzer-Entscheid (par.6). Kandidaten, je mit Freigabe je Pfad:

- Tote Funktionen und Diagnose-Einstiege (Listen je Bericht), Inversions-Pfad Runde 5 samt
  PyO3-Huelle, `envelope::tiling_cost_delta`, `X`/`X_in`-Wrapper in `envelope.rs`, die nur der
  Bit-Identitaets-Test haelt (Test auf `_in` umstellen, Wrapper entfernen).
- `--encoder flat` als Default in `train.py` und drei Cache-Werkzeugen auf `2d` (jeder
  Champion seit v19 ist 2D); Legacy-`MosaicNet`-Pfade bleiben ladbar (Altmodelle), aber nicht
  Default.
- Acht `server.py`-Endpunkte ohne Frontend-Aufrufer (Liste im Python-Bericht), darunter
  `/api/stack/peek`; `DIFFICULTY_PRESETS` gehen in der Schwierigkeitsleiter auf
  (`PREREG_difficulty_levels.md`).
- Testmodul von `net_mcts.rs` per `#[path]` auslagern (Nahtbreite null);
  `self_play_diagnostics.rs` abspalten (9 Namen ueber der Naht); kein weiterer Modulschnitt.
- Deutsche Bezeichner: Kern (13), `plate_builder.rs` (25 Typ-/Konstantennamen), Farb-Sonde in
  `net_mcts.rs`; `TileColor`-Varianten NICHT (Serialisierungs-Paritaet).
- Entschiedene Knoepfe: je Knopf entscheiden; Registratur-Status UEBERHOLT plus Kommentar
  reicht, wenn der Zweig bei Default bitidentisch ist; entfernen nur, wo er Wartungslast
  erzeugt. A6, A7, A11 (nach Messung) gehoeren hierher.
- Tore: nach jedem Rust-Schnitt Wheel, Paritaets-Fixture, Anker-Drift; nach Python-Schnitten
  die 44 Werkzeug-Tests und ein Rauchtest der Ketten-Skripte mit `--limit`.

## par.5 STUFE 3: Doku (rund 3 h)

Zeilenverweise in `knob_registry.rs` und `docs/architecture_reference.md` nachziehen; die vier
widersprechenden Kommentare (A13: `ROUND5_ENDSCORING_ENABLED`, `NET_TILING_TIEBREAK_ENABLED`,
`provocation.rs:459-464`, Jokerfeld-Kommentare in `envelope.rs`); `docs/knobs.md` generieren;
Abschlusskapitel in `docs/architecture_reference.md` "Stand beim Projektende".

## par.5a NAME DES SCHLUSSMODELLS: "Tessa" (Nutzer-Entscheid 2026-09-11, 23:45)

Nutzer 2026-09-12, 18:05: v30 wird released und ist der Projektabschluss; Tessa ist damit der v30-Champion, Stufe 2 und 3 folgen der v30-Promotion.

Der Champion am Projektende heisst nach aussen **Tessa** (Tessera: der einzelne Mosaikstein;
Nutzer: "tessa passt, so machen wir das"). Umsetzung mit Stufe 3, NACH der letzten Promotion:

1. Manifestfeld `display_name: "Tessa"` im eingefrorenen Artefakt des Schlusschampions
   (`models/frozen_champions/<name>/manifest.json`); der Generationsname (z.B. `v29-b01`) bleibt
   der technische Name in Register, Preregs und Dateinamen, damit Elo-Kanten eindeutig bleiben.
2. GUI: Anzeige "Tessa" statt "KI" als Spielername im Spielfeld und im Log-Kopf
   (`server.py` Spielernamen, `static/js/app.js`); die Log-Auswertung (`analyze_game_log.py`)
   muss den Namen als KI-Seite erkennen (heute haengt sie an "KI", Pruefstelle beim Bau).
3. README "Current Status": Name und Generationsname nebeneinander; Schwierigkeitsleiter
   (`PREREG_difficulty_levels.md`): Stufe "Meister" = Tessa.

## par.6 Nutzer-Entscheide

1. ~~A10 Kontrakt-Hash erweitern~~ ENTSCHIEDEN 2026-09-11 (Nutzer: "ja, nimm A4 und A10 mit
   rein"): in Stufe 1, par.3 Punkt 8.
2. ~~A4 Chip-Sperre in die Arbeitsfunktion~~ ENTSCHIEDEN 2026-09-11: in Stufe 1, par.3 Punkt 7.
3. **Umfang Stufe 2** (par.4): welche Kandidaten, insbesondere die Plattenbauer-Zweige. Offen.

## par.7 Was diese Prereg NICHT ist

Keine Staerkemessung, kein neuer Arm. Kein Refactoring "weil es schoener ist": jeder Schnitt
braucht einen der Gruende Defekt, Fussangel, toter Code oder Widerspruch. Die Elo-Leiter und
die eingefrorenen Artefakte werden nicht angefasst.

## par.7a NEUVERANKERUNG DER ELO-LEITER (Nutzer 2026-09-12: "setz den anker neu")

Anlass: die Anker-Drift ist durch A2 ROT (par.8). Entscheid (a): A2 bleibt, der Anker wird
bewusst neu gesetzt. Verfahren nach dem Praezedenzfall `PREREG_round5_minfix_elo_reset.md`
par.2/par.3/par.5 (Neuverankerung 2026-08-21): ein NEUES Leitersegment, Kanten ueber die
Grenze werden nie gemischt.

1. **Neues Anker-Artefakt `models/frozen_heuristics/hv4_anchor`**: hv1 mit dem Wheel, das
   A2 traegt (Stand `2a0cf4b` plus Wheel-Bau vom 2026-09-12), Golden-Probe wie beim ersten
   Artefakt (10 Partien, 600 Sims, Seed 20260826, 11 Threads; `tools/freeze_heuristic.py`).
   `hv1_anchor` bleibt als historisches Artefakt liegen (Bezug des Alt-Registers). Drift-Pruefung
   gegen das neue Artefakt muss GRUEN sein (gleiches Wheel; Konstruktionsbeleg).
2. **Register**: `evaluations/elo_history.csv` wird nach `archive/elo_history_pre_phantomfix.csv`
   verschoben (git mv, Teil des Nutzer-Entscheids "setz den anker neu"), eine frische
   `elo_history.csv` beginnt mit den Neuverankerungs-Kanten. `tools/elo_tracker.py`:
   `ANCHOR_NAME = "Heuristik_hv4_anchor"`, keine Aliase (der alte Anker ist ein anderer
   Spieler auf einer anderen Engine).
3. **Neuverankerungs-Kanten, alle auf der A2-Engine** (Kandidaten als ONNX plus Champion-Spec
   auf dem lebenden Wheel; `models/alphazero_v27-b01_brierbest.onnx` ist sha256-identisch mit
   dem Artefakt-Modell, geprueft 6f19f28dc6ee17eb):

   | Kante | n | Werkzeug |
   | --- | --- | --- |
   | v28-b02@400 gegen hv4_anchor@150 | 150 fest, kein Fruehstopp, Seed-Basis 900001 | `frozen_referee_match.py` (Anker aus dem Artefakt, 6 Worker) |
   | v28-b01@400 gegen hv4_anchor@150 | 150, dito | dito |
   | v27-b01@400 gegen hv4_anchor@150 | 150, dito | dito |
   | v28-b02@400 gegen v27-b01@400 | 200 Paare mit Logs, Seed 20261044, Blockgroesse 5 | `paired_gating.py` |

   Kosten: 3 x rund 22 min + 86 min (ANNAHME aus `docs/measured_runtimes.md`). Erwartung: die
   Reihung v27-b01 < v28-b01 <= v28-b02 haelt im Fit; die absoluten Zahlen sind nicht mit dem
   Alt-Register vergleichbar (kuerzere Leiter, andere Engine), Regel wie 2026-08-21.
4. **Konsumenten** (Rueckwaerts-Pruefung): `docs/promotion_checklist.md` (Anker-Name),
   `.claude/skills/mosaic-anchor-invariance/SKILL.md` (Artefaktpfad), `README.md` "Current
   Status" (Anker und Leiter), `PREREG_difficulty_levels.md` par.4.1 (Anfaenger-Stufe hv2 bleibt
   hv2_generator; der Elo-Knoten 1100 stammt aus dem Alt-Register und ist im neuen Segment
   ungemessen), `docs/generation_loop.md`. Alle mit dem Ergebnis nachziehen.

**Ergebnisse par.7a (2026-09-12, 01:31-02:46, `tools/night_reanchor.sh`, exklusiv):** die drei
Anker-Kanten sind gefahren und registriert (`evaluations/elo_history.csv`, Zeilen 2-4), alle mit
Handshake gruen OHNE Cross-Aera (39648b95bbba1acf beidseits) und Golden-Selbsttest ohne Abweichung,
n=150 fest, Seed-Basis 900001, 6 Worker:

| Kante | Ergebnis | Wanduhr | Elo im Segment 2 (nach 3 Kanten) |
| --- | --- | --- | --- |
| v28-b02@400 gegen hv4_anchor@150 | 126:24 | 1.441 s | 1288 [1220, 1382] |
| v28-b01@400 gegen hv4_anchor@150 | 132:18 | 1.491 s | 1346 [1271, 1458] |
| v27-b01@400 gegen hv4_anchor@150 | 124:26 | 1.489 s | 1271 [1207, 1357] |

Report ohne "NICHT mit Anker verbunden" (geprueft `tools/elo_tracker.py report`). Die Reihung
aus Punkt 3 (v27-b01 < v28-b01 <= v28-b02) haelt nur zur Haelfte: v28-b01 liegt in diesem
Fit ueber v28-b02, mit ueberlappenden Intervallen; auf drei Anker-Kanten allein traegt die
Leiter noch keine Reihung unter den Netzen (Bezug Alt-Register: 127:23 fuer v27-b01, dort
n=150 gegen hv1_anchor). Die Nachbar-Kante v28-b02 gegen v27-b01 (Seed 20261044, 02:46-03:40, 3.243 s,
10 Threads, Blockgroesse 5, Logs): **SPRT-Entscheid fuer v28-b02 nach 115 Paaren, 133:97**
(LLR +3,025), McNemar p=0,0198, gepaarte Differenz +0,313 [+0,068; +0,558], Punkte 53,7 gegen
50,2 (61 Splits, 36 A-Sweeps, 18 B-Sweeps; Artefakt
`paired_gating_v28-b02_vs_v27-b01_s44_segment2.json`). Register nach vier Kanten: v28-b02 1305
[1248, 1371], v28-b01 1346 [1271, 1458], v27-b01 1256 [1202, 1317]. Fruehstopp unter 150
Paaren: die Replikation (Seed 20261046, bis zum Deckel) laeuft als Schritt 2r der
Promotionskette `tools/night_v28_promotion.sh`.

**Replikation (Seed 20261046, 03:48-05:19, 5.449 s, 10 Threads, Logs): 212:188 am Deckel, KEIN
SPRT-Entscheid** (LLR -1,19), McNemar p=0,281, gepaarte Differenz +0,12 [-0,08; +0,32], Punkte
51,4 gegen 50,8 (96 Splits, 58 A-Sweeps, 46 B-Sweeps; Artefakt
`paired_gating_v28-b02_vs_v27-b01_s46_segment2.json`). Die Replikation traegt die Signifikanz
des ersten Seeds NICHT; die Richtung ist dieselbe (fuenfte positive Arena von v28-b01/b02 gegen
v27-b01 ueber beide Segmente, aber nur zwei davon signifikant). Ein Pool aus SPRT-Stopp und
Deckel-Lauf waere verzerrt (Regel seit v26); nach der v26-Praezedenz folgt ein dritter Seed als
unverzerrter Stichentscheid (200 Paare, Fruehstopp per alpha=beta=1e-12 aus), eingetaktet NACH
der Master-Kette. Register nach fuenf Kanten: v28-b02 1296 [1244, 1358], v27-b01 1264
[1210, 1323], v28-b01 1346 [1271, 1441] (eine Kante). Die Promotion von v28-b02 laeuft
unabhaengig davon weiter: der Nutzer-Entscheid zum besten Stand (Korrektheit des volleren
Merkmalsbilds) haengt nicht an dieser Kante, und der Vorgaenger v27-b01 hat im Segment 2 keine
Kante, die ihn ueber v28-b02 stellt.

**Dritter Seed (unverzerrter Stichentscheid, `tools/night_v28_third_seed.sh`, 10:13-11:43,
5.405 s): 226:174 am Deckel, McNemar p=0,0167, gepaarte Differenz +0,26 [+0,06; +0,46], Punkte
52,7 gegen 50,3** (90 Splits, 68 A-Sweeps, 42 B-Sweeps; Fruehstopp per Schranken 1e-12 aus,
LLR +2,86; Artefakt `paired_gating_v28-b02_vs_v27-b01_s47_segment2.json`). Damit traegt die
Nachbar-Kante: zwei von drei Seeds signifikant, der dritte als verzerrungsfreier Deckel-Lauf.
Verzerrungsfrei gepoolt (nur die beiden Deckel-Laeufe 46 und 47): 438:362 aus 800 = 0,548.
Replay-Sonden (Spalten, Plattenpunkte) auf s47 folgen im Schwanz der Kette.

**KORREKTUR 2026-09-12, 12:05 (Anker-Kanten falsch etikettiert):** die drei Anker-Kanten oben
liefen ueber `tools/night_reanchor.sh` OHNE `--sims-worker 150 --c-puct-worker 0.3`; der Anker
spielte @400 mit c_puct 1,5 (Artefakte `anchor_v2_arena_*.json`: `sims_worker 400`,
`c_puct_worker 1.5`), nicht die Leiterdefinition @150/0,3 (`tools/anchor_arena.py:118-119`, so
lief die Segment-1-Kante von v27-b01). Die Zeilen liegen in
`archive/elo_history_segment2_anchor_mislabelled.csv`; alle daraus abgeleiteten Segment-2-Zahlen
(1299/1262/1173/1346) sind bis zur Wiederholung VORLAEUFIG. Wiederholung mit korrekten
Parametern, festes n=150, in `tools/night_ladder_rungs2.sh` Teil A.

**ZWISCHENSTUFEN (Nutzer 2026-09-12: "die neuverankerung steht auf recht wackligen beinen ...
weil der abstand von hv1 bereits gesaettigt ist"):** die Anker-Kanten liegen bei 84-88 % Siegquote
(gegen den STAERKEREN Anker @400; Segment 1 zeigt Saettigung ab v23 mit 84-85 %, geprueft am
Alt-Register). Deshalb Sprossen in rund 100-Elo-Schritten aus eingefrorenen Artefakten:
hv2_generator (Segment 1: 1100), v21_2d_brierbest (1190, aus restic-Snapshot 55623af8, Worker-
Wheel wave3g aus f003e008), v24-b07 (1283, aus bfbe80b1), v26-b01 (1364). Neun Kanten
(`night_ladder_rungs2.sh` Teil B), jede in Bloecken zu 50 Partien mit eigener Seed-Basis und
Frueh-Stopp bei zweiseitigem Binomialtest p < 0,05 der gepoolten Bloecke, spaetestens 150
(Nutzer: "muss nicht fest 150 sein, kann auch vorher abbrechen, wir machen ja kein champion
gate"; und: "lass die sprossen, die werden wir brauchen wenn wir vorzeitig abbrechen lassen").
Heuristik-Seiten @150 mit c_puct 0,3, Netze @400 mit 1,5; Artefakt gegen Artefakt per
`--artifact-dir-a`, Cross-Aera per `--force-cross-era`. Lesart: mit Frueh-Stopp traegt jede
Kante weniger Praezision, dafuer haengt jeder Knoten an mehreren Nachbarn; Kanten mit Frueh-Stopp
werden im Register als solche gekennzeichnet (SPRT-artige Verzerrung der Siegquote nach oben).

**ANKER-KANTEN KORREKT WIEDERHOLT (2026-09-12, 15:02-16:15, `tools/night_ladder_missing_edges.sh`
Teil A; Anker @150, c_puct 0,3, festes n=150, Seed-Basis 900001, 6 Worker, Handshake gruen ohne
Cross-Aera, Golden-Selbsttests gruen):**

| Kante | korrekt (@150/0,3) | Morgenfassung (@400/1,5, archiviert) | Wanduhr |
| --- | --- | --- | --- |
| v28-b02@400 gegen hv4_anchor@150 | **126:24** | 126:24 | 1.472 s |
| v28-b01@400 gegen hv4_anchor@150 | **126:24** | 132:18 | 1.460 s |
| v27-b01@400 gegen hv4_anchor@150 | **122:28** | 124:26 | 1.444 s |

Kontrolle, dass die Parameter ankamen (Regel 0, weil v28-b02 dieselbe Summe wie morgens hat):
keine der 150 Partien ist identisch (Punkte und Schrittzahl je Seed verglichen), die Worker-
Wartezeit sinkt von 417 s auf 301 s (150 statt 400 Sims). Der schwaechere Anker @150 gewinnt
NICHT mehr Partien als der staerkere @400 (24/24/28 gegen 24/18/26): die Kanten sind in der
Saettigung, die Zahlen dort sind Rauschen um 84 %, genau der Grund fuer die Zwischenstufen.
Register nach den Anker-Kanten und fuenf Sprossen: v28-b02 1294 [1244, 1354], v28-b01 1288
[1220, 1369], v27-b01 1251 [1204, 1311], v26-b01 1178 [1100, 1257], v24-b07 1096 [1019, 1174],
hv2 818 (nur zwei Frueh-Stopp-Kanten, direkte Anker-Kante laeuft).

**hv2 GEGEN ANKER (16:15-16:18, `night_ladder_missing_edges.sh` Teil B):** hv2_generator@150 gegen
hv4_anchor@150, beide c_puct 0,3, drei Bloecke bis zum Deckel ohne Frueh-Stopp (27:23, 29:21,
21:29) = **77:73 aus 150, p 0,81**: hv2 und hv1 sind im Segment 2 gleich stark (hv2 972
[921, 1022]). Die Segment-1-Zahl 1100 fuer `Heuristik_v2huelle` (2026-08-25, ueber v21 gemessen)
haelt fuer das Artefakt hv2_generator nicht; ob beides derselbe Spieler ist, bleibt ungeprueft
(`PREREG_difficulty_levels.md` Stufe 0b). **Cross-Aera (Nutzer-Rueckfrage 17:20):** das hv2-Artefakt
ist vom 2026-08-26 (Wheel aus 40600ba, Kontrakt a3f61f24) und traegt den Phantom-Fix A2 vom
2026-09-12 NICHT, der Anker hv4_anchor schon; ein hv2-Wheel mit A2 ist nicht baubar, der
hv2-Zweig ist seit 2026-08-26 aus dem Quellstand entfernt. hv2 ist damit dauerhaft ein Knoten der
Aera vor A2 (wie die Netz-Artefakte v21-v27 mit ihren eigenen Wheels), und die Aussage lautet
genau: hv2 ohne A2 gegen hv1 mit A2 = 77:73. Folge: die Anfaenger-Stufe der Schwierigkeitsleiter
(hv2@150) ist so stark wie der Anker, nicht 100 Elo darueber. Register nach dieser Kante: v28-b02
1329 [1281, 1389], v28-b01 1288, v27-b01 1285, v26-b01 1232, v24-b07 1155, Anker 1000, hv2 972.

**v21-SPROSSEN (16:18-17:09, `tools/night_ladder_v21_edges.sh`):** v21 gegen hv2 34:16 (Frueh-Stopp
nach 50, p 0,015); v24-b07 gegen v21 **85:65 am Deckel** (drei Bloecke 30:20, 27:23, 28:22, p 0,12,
die Sprosse mit der besten Aufloesung); v21 gegen Anker 42:8 (Frueh-Stopp, p < 0,0001: auch v21 ist
gegen den Anker schon gesaettigt).

**LEITER SEGMENT 2, ENDSTAND 17:10 (16 Kanten, alle am Anker, `tools/elo_tracker.py report`):**

| Knoten | Elo | KI95 | Partien |
| --- | --- | --- | --- |
| v28-b02@400 (Champion) | **1344** | [1298, 1399] | 1.380 |
| v27-b01@400 | 1301 | [1256, 1352] | 1.280 |
| v28-b01@400 | 1288 | [1220, 1369] | 150 (nur Anker-Kante) |
| v26-b01@400 | 1251 | [1188, 1316] | 250 |
| v24-b07@400 | 1184 | [1134, 1236] | 400 |
| v21_2d_brierbest@400 | 1157 | [1100, 1215] | 250 |
| Heuristik_hv4_anchor@150 | 1000 | fix | 650 |
| Heuristik_hv2_generator@150 | 987 | [941, 1033] | 300 |

Lesart: die Leiter traegt jetzt auf Kanten im 57-77-%-Bereich (v24-b07 gegen v21, v26 gegen
v24, v27 gegen v24) statt nur auf gesaettigten Anker-Kanten; die Netze ab v21 gewinnen gegen beide
Heuristiken 82-90 %. Der Abstand v28-b02 zu v27-b01 (+43) ist der der drei Nachbar-Seeds; v28-b01
haengt nur an der Anker-Kante und ist damit die unschaerfste Zahl. Frueh-Stopp-Kanten sind im
Register als solche markiert. Alle Segment-2-Zahlen in STATUS, README und dem Artefakt-Manifest
sind auf diesen Stand gezogen; die Vorlaeufigkeits-Markierung entfaellt.

**UMBENENNUNG 17:40 (Nutzer: "das benennst mir um auf hv4"):** das Anker-Artefakt hv1_anchor_v2
heisst jetzt `models/frozen_heuristics/hv4_anchor`, der Elo-Knoten `Heuristik_hv4_anchor@150`
(Register-Zeilen und Archiv umgeschrieben, ANCHOR_NAME in `tools/elo_tracker.py`). Lesart der
Nummern: hv1 = Heuristik ohne Fix (Segment-1-Anker `hv1_anchor`), hv2 = Huellen-Lehrer ohne Fix,
hv3 = Huellen-Lehrer mit Phantom-Fix (im Bau), hv4 = hv1-Code mit Phantom-Fix (der heutige Motor).
Das Spec-Schluesselwort `heuristik_variante: hv1` bleibt, jede Champion-Spec traegt es.

**AUFLOESUNG DER LEITER, Nutzer-Entscheide 17:20-17:30:** (1) alle Kanten zum Anker sind
gesaettigt (81-90 %), die Luecke 1000-1157 (Heuristiken bis v21) hat keine Sprosse; (2) hv2 ist
ein Knoten der Aera vor A2 und nicht nachbaubar. Daraus: **hv3** = hv2-Verhalten auf dem heutigen
Motor mit Phantom-Fix (Nutzer: "mach mir eine hv3 (hv2 + phantom fix)"), Port aus Commit 65b48af^
(Agent, nur Code; Kompilat und Einfrieren nach dem Such-Start-A/B), dann als Knoten
`Heuristik_hv3_generator@150` gegen Anker, hv2 und v21; und **v22-b05** als Sprosse in der Luecke
(Segment 1: 1084, verlor 16:34 gegen v21), aus dem Backup nur als ONNX (Snapshot f567ad7d,
`models/restored_v22/`), spielt LIVE mit `k3v_off.spec.json` als Knoten `v22-b05_live`
(`tools/night_ladder_v22_edges.sh`: gegen v21, Anker, hv2). v23-b01_k3p10 liegt als Artefakt im
Backup (Segment 1: 1242, zwischen v21 und v24-b07, dort ist die Leiter dicht) und wird nicht
gezogen, solange die Luecke unten offen ist.

**hv3 GEBAUT, EINGEFROREN UND GEMESSEN (21:41-21:49, `tools/night_hv3_freeze_edges.sh`):** Port
des hv2-Rezepts auf den heutigen Motor (heuristic_v3.rs, plate_builder_v3.rs; der Phantom-Fix A2
wirkt ueber `remaining_colors` an zwei Routing-Stellen), Bau-Tore gruen (629 Lib-Tests,
Beispiele, Wheel, Fixture und Kontrakt unveraendert, Anker-Drift und Konservierung gruen,
Python-Spiegeltest der Aktions-IDs 8/8), Artefakt `models/frozen_heuristics/hv3_generator`
(Golden Probe 10 Partien, venv, Konservierung gruen). Kanten, beide @150 c_puct 0,3, drei
Bloecke bis zum Deckel: **hv3 gegen hv4-Anker 73:77** (p 0,81), **hv3 gegen hv2 78:72** (p 0,68).
Der Phantom-Fix aendert die Staerke des Huellen-Lehrers nicht messbar; hv3 992 [948, 1035].

**v22-b05 UND v28-b01 (18:04-20:20, `tools/night_v28_tail8.sh`):** v22-b05 live (k3v_off) gegen v21
64:86 (Deckel, p 0,086), gegen Anker 38:12 (Frueh-Stopp, 76 %), gegen hv2 41:9; v28-b01 gegen
v26-b01 92:58 (Deckel, p 0,007), gegen v21 69:31 (Frueh-Stopp nach 100). v22-b05 1158 liegt
knapp unter v21, die Luecke 1000-1158 bleibt ohne Netz-Sprosse.

**LEITER SEGMENT 2, ENDSTAND 21:50 (23 Kanten, alle am Anker; Korrektur 22:56: das Register zaehlt 23 Zeilen, nicht 24):**

| Knoten | Elo | KI95 | Partien |
| --- | --- | --- | --- |
| v28-b02@400 (Champion) | **1344** | [1301, 1395] | 1.380 |
| v28-b01@400 | 1313 | [1264, 1366] | 400 |
| v27-b01@400 | 1301 | [1256, 1351] | 1.280 |
| v26-b01@400 | 1244 | [1194, 1296] | 400 |
| v24-b07@400 | 1191 | [1146, 1244] | 400 |
| v21_2d_brierbest@400 | 1178 | [1135, 1224] | 500 |
| v22-b05_live@400 | 1158 | [1105, 1215] | 250 |
| Heuristik_hv4_anchor@150 | 1000 | fix | 850 |
| Heuristik_hv3_generator@150 | 992 | [948, 1035] | 300 |
| Heuristik_hv2_generator@150 | 978 | [937, 1018] | 500 |

**PRUEFUNG DES TRACKERS UND WERKZEUG (Nutzer 2026-09-12, gegen 22:45-22:56: "Pruefung wie der Tracker
rechnet" / "mach das Werkzeug"):** `tools/elo_tracker.py` fittet Bradley-Terry per MM (Zermelo/
Hunter, Anker-gamma fix, Zeilen desselben Paars summiert), das Intervall ist ein nichtparametrischer
Bootstrap (1.000 Wiederholungen), der bis dahin JEDE Zeile als Binomial(n, p) zog, also alle
Partien als unabhaengig. Befund: (1) gepaarte Bloecke (5 Paare je Seed) sind korreliert, das
Intervall war dort zu schmal; (2) elf der 23 Kanten sind frueh gestoppt (SPRT oder Binomial-
Block-Abbruch), ihre Siegquote ist nach oben verzerrt und der Fit weiss es nicht; (3) das Modell
setzt Transitivitaet voraus, der Widerspruch v21/hv2/hv4 (68 % / 84 % / 51 %) geht nicht ins
Intervall. Gebaut: zwei ADDITIVE Register-Spalten `units` ("k:w1,w2,..." Siege je Seed-Block, aus
dem paired_gating-Artefakt ableitbar: `elo_tracker.py units --paired-artifact`, `add
--units-from-paired-artifact`) und `early_stop` (`add --early-stop`); der Bootstrap zieht bei
gesetzten `units` Bloecke statt Partien, der Report traegt eine Spalte "Frueh" (gestoppte/alle
Kanten je Knoten), markiert Zeilen mit [FRUEH-STOPP] und nennt die Zaehlung. Kopf-Migration
automatisch beim naechsten `add` (DictReader verwirft Felder jenseits des Kopfes still:
Testfund). Tests `tools/tests/test_elo_tracker_units.py` 8/8; Rueckfuellung: die drei
paired_gating-Zeilen v28-b02 gegen v27-b01 mit Bloecken, elf Zeilen als frueh gestoppt.
**Wirkung auf die Zahlen: praktisch keine** (v28-b02 [1301, 1393] statt [1301, 1395], v28-b01
[1266, 1375] statt [1264, 1366]): die Block-Korrelation der drei gepaarten Kanten ist gering, und
der Anker-Schritt, nicht die Paarung, traegt die Breite. Der Frueh-Stopp bleibt eine Markierung,
keine Korrektur.

**SPROSSE v22-b05@100 (Nutzer 2026-09-12, gegen 22:50 und 22:53; 23:09-23:23,
`tools/night_ladder_v22_sims100.sh`):** Ziel war ein Knoten ZWISCHEN Anker (1000) und v22-b05@400
(1158), weil alle Netz-Kanten gegen die Heuristiken gesaettigt sind. Drei Kanten, alle frueh
gestoppt: **v22@100 gegen hv4-Anker 39:11** (Block 1, p 0,0001, 167 s), **gegen hv3 43:7** (Block 1,
p < 0,0001, 155 s), **gegen v22@400 21:39** (paired_gating Seed 20261050, SPRT H0 nach 30 Paaren,
McNemar p 0,049, gepaarte Differenz -0,60 [-1,10; -0,10], 497 s; Register-Zeile mit Bloecken).
**Befund: die Sprosse liegt NICHT in der Luecke.** Mit 100 statt 400 Sims verliert v22-b05 gegen
sich selbst 35 %, schlaegt die Heuristiken aber weiter zu 78-86 %: der Vorsprung der Netze ueber
die Heuristiken ist kein Suchtiefen-Vorsprung, sondern sitzt im Netz (Prior und Value-Kopf), und er
schrumpft mit weniger Sims kaum. Der Fit legt v22@100 auf 1175 und zieht damit den ganzen unteren
Netz-Block um 10-30 Punkte nach oben (v22@400 1191 statt 1158, v21 1194 statt 1178); der Champion
steigt auf 1349 [1302, 1402]. Das ist genau die Weichheit, die oben beschrieben ist: die absolute
Hoehe des Netz-Blocks ueber der 1000 haengt am gesaettigten Anker-Schritt, und jede neue Kante
dorthin verschiebt sie. Wer die Luecke wirklich fuellen will, braucht einen Knoten, der gegen die
Heuristiken bei 55-70 % liegt: ein Netz mit 25 Sims oder eine Heuristik mit 600 Sims (nicht
gefahren; Vorschlag fuers v29-Begleitprogramm, kein Auftrag).

**LEITER SEGMENT 2, ENDSTAND 23:25 (26 Kanten, alle am Anker; Block-Bootstrap):**

| Knoten | Elo | KI95 | Partien |
| --- | --- | --- | --- |
| v28-b02@400 (Champion) | **1349** | [1302, 1402] | 1.380 |
| v28-b01@400 | 1321 | [1272, 1375] | 400 |
| v27-b01@400 | 1306 | [1261, 1358] | 1.280 |
| v26-b01@400 | 1250 | [1198, 1305] | 400 |
| v24-b07@400 | 1200 | [1150, 1249] | 400 |
| v21_2d_brierbest@400 | 1194 | [1150, 1239] | 500 |
| v22-b05_live@400 | 1191 | [1145, 1241] | 310 |
| v22-b05_live@100 | 1175 | [1127, 1231] | 160 |
| Heuristik_hv4_anchor@150 | 1000 | fix | 900 |
| Heuristik_hv3_generator@150 | 980 | [940, 1021] | 350 |
| Heuristik_hv2_generator@150 | 980 | [939, 1018] | 500 |

 `tools/night_ladder_rungs2.sh` Teil B, nach
dem Worker-Patch 13:37; die drei Anker-Kanten und hv2 gegen Anker davor gescheitert, Nachlauf
`tools/night_ladder_missing_edges.sh`; v21-Sprossen im Nachlauf `night_ladder_v21_edges.sh`):**

| Kante | Ergebnis | Bloecke | Binomial p | Wanduhr |
| --- | --- | --- | --- | --- |
| v26-b01 (Art.) gegen v24-b07 (Art.) | 36:14 | 1 (Frueh-Stopp) | 0,0026 | 941 s |
| v27-b01 gegen v24-b07 (Art.) | 63:37 | 2 | 0,012 | 963 + 933 s |
| v28-b02 gegen v24-b07 (Art.) | 44:6 | 1 | < 0,0001 | 917 s |
| v24-b07 (Art.) gegen hv2@150 | 45:5 | 1 | < 0,0001 | 464 s |
| v26-b01 (Art.) gegen hv2@150 | 41:9 | 1 | < 0,0001 | 436 s |

Alle im Register (`elo_history.csv`, Kommentar nennt den Frueh-Stopp). Lesart: v24-b07 ist die
brauchbare Sprosse fuer v26/v27 (72 % / 63 %), fuer v28-b02 schon gesaettigt (88 %); hv2@150 ist
fuer alle Netze ab v24 gesaettigt (82-90 %) und taugt nur als Sprosse fuer v21. Zwischenstand des
Fits OHNE Anker (bis die Anker-Kanten aus dem Nachlauf da sind): v28-b02 > v27-b01 (+44) >
v26-b01 (+72) > v24-b07 (+82) > hv2 (+278). Die Segment-1-Zahl von hv2 (1100 gegen Anker 1000)
war damit vermutlich zu hoch; die Kante hv2 gegen Anker im Nachlauf entscheidet das.

**Champion-2-Kante (Promotion Schritt 4, 05:22-06:04, 2.516 s):** v28-b02 gegen das
EINGEFRORENE Artefakt v26-b01 mit dessen eigenem Wheel (`frozen_referee_match.py`, 150 Partien,
6 Prozesse, Seed-Basis 20261052) **101:49**, Punkte 52,9 gegen 50,5. Cross-Aera nach der
Aera-Regel (Handshake ROT 20b442a8164f748d gegen 39648b95bbba1acf, `--force-cross-era`;
Golden-Selbsttest des Artefakts 10/10 gruen: es spielt noch wie am Einfriertag). Artefakt
`champion2_v28-b02_vs_v26-b01.json`. Damit haengt v28-b02 im Segment 2 an drei Nachbarn
(Anker, v27-b01, v26-b01); v26-b01 selbst hat im Segment 2 nur diese eine Kante.

**Pflicht-Diagnostiken (Schritte 5b/5c, 06:04-06:17):** sigma/Prior-Balance
(`gumbel_scale_calibration.py`, 300 Zustaende, n_used 233) gesamt **2,222** (v27-b01 2,161,
v26-b01 2,270), je Runde 1,30 / 2,48 / 3,04 / 3,76; die c_visit/c_scale-Familie bleibt zu
(Regel: Gesamt-Kennzahl ueber 3). Nebenbefund: Runde 4 liegt mit 3,76 ueber der Schwelle
(v27-b01 2,88), Runde 3 knapp (3,04); kein Ausreisser wie bei v26-b01 (8,54). Anzeige-
Kalibrierung (`platt_fit.py`, je 1.440 Zustaende): frozen_v3 (Anzeige) **A -0,0539, B 0,6684,
Brier 0,22537** (v27-b01: -0,0476 / 0,6853 / 0,22379), frozen_v1 (Trend) A +0,3840, B 0,6074,
Brier 0,25217 (v27-b01: +0,4010 / 0,6335 / 0,25135). In `server.py` eingetragen (06:20).
Artefakte `gumbel_scale_calibration_v28-b02.json`, `platt_fit_v28-b02_v3.json`,
`platt_fit_v28-b02.json`. Schritt 1 `set_champion v28-b02_brierbest` 06:17; Schritte 5d und 7
(Fixture, Artefakt `frozen_champions/v28-b02`, Golden Probe, Selbsttest) liefen in
`tools/night_v28_freeze.sh` (06:19-06:45, zweiter Anlauf nach einer Dateisperre im ersten
Schreiblauf): Fixture **e1f94c44f0c7959b** (Schreiblauf + frische Gegenprobe gruen), Artefakt
mit Wheel `mosaic_rust_knobs_20260912.whl` (sha256 ea980d9f..., identisch mit dem live
installierten), Golden Probe 10 Sonden (3 mit pending_dome_choice, 1.450 s), Referee-Selbsttest
Handshake gruen (39648b95bbba1acf beidseits), Golden 10/10, 2 Echtpartien. **Promotion v28-b02
VOLLSTAENDIG (06:45); Manifest vervollstaendigt.** Offen bleibt der dritte Seed der Nachbar-Kante.

Nebenbefund zur Erwartung aus Punkt 3: im Alt-Register lag v28-b02 gegen v28-b01 im
Nullbefund (207:193, 209:191, `PREREG_v28_window.md` par.10); im Segment 2 tragen die beiden
b01-Zahlen nur EINE Kante (Anker), das Intervall 1271-1458 ist entsprechend breit.

## par.8 Ergebnisse (leer bis zum Bau)

**STUFE 1 GEBAUT (2026-09-11 abends bis 2026-09-12, 01:30), Tore gefahren im freien Fenster
nach der Ablations-Kette:**

| Punkt | Bau | Tor |
| --- | --- | --- |
| A1 | Zaehler `NET_EVAL_FAILURES` mit einmaliger Warnung an elf Stellen (`net_mcts.rs:184-229`, Aufrufstellen laut Agentenbericht), pyo3 `net_eval_failures()`/`reset_net_eval_failures()`, Feld `net_eval_failures` in `engine_config_json`; Grundmenge = fehlgeschlagener AUFRUF, nicht Batchzeile | Test `net_eval_failure_counter_counts_and_resets`; Bit-Identitaet: Paritaets-Fixture ohne A2 unveraendert (Gegenprobe) |
| A2 | `provocation.rs` `subtract_phantom_tiles` in `remaining_colors` und `still_reachable_colors`, deutsche Lokale mitmigriert | Tests `remaining_colors_ignores_phantom_tiles`, `still_reachable_colors_ignores_opponent_phantom_tiles`; Feature-Golden-Hash unveraendert; **Netz-Paritaets-Fixture ROT -> bewusst neu erzeugt** (b5188b25e073a1c0 -> f644cafc5e6506c6; Gegenprobe: ohne A2 haelt die alte, die Aenderung ist also der Grund); **ANKER-DRIFT ROT** (siehe unten) |
| A3 | `sanitized_score_utility_b`, `from_spec_file` harter Fehler bei b <= 0 | Tests `search_config_from_spec_file_validates_score_utility_b`, `sanitized_score_utility_b_falls_back_on_non_positive`; alle 15 Spec-Dateien tragen 20,0 |
| A4 | Sperre in `apply_bonus_chips_with` plus Reihenindex-Pruefung | Test `locked_row_is_refused_by_apply_bonus_chips_with` (ein fehlender Slot kostet zwei Chips, Test entsprechend); Drift ohne A2 GRUEN, A4 bewegt hv1 also nicht |
| A5 | Bereichspruefungen `validate_draw_from_stack`, `apply_start_placement`, `validate_tiling_action` (Zusatzfund `player_idx`), `py.rs::check_player_row` fuer die Chip-Routen, `server.py::_slot_out_of_range` an vier Routen | Tests `draw_from_stack_rejects_out_of_range_slot`, `start_placement_rejects_out_of_range_indices` |
| A8 | `train.py` ehrt die Fensterliste auch ohne Val-Split; drei Doku-Nachtraege | Commit f8db185 |
| A9 | drei Phasen-Knoepfe auf `Tot`, Waechter prueft Lesestellen (Rust- und Python-Marker, `tools/` nicht mehr gescannt), `phase_sweep.py` gesperrt; keine weiteren Eintraege betroffen (Grep-Simulation, dann `cargo test`) | Test `read_site_scanner_counts_reads_not_mentions`, `docs/knobs.md` generiert |
| A10 | Vertragsstring mit `PLANES_H`/`PLANES_W` und Kopf `ownership`; **Hash c65768636c0560a7 -> 39648b95bbba1acf** | Test `contract_hash_matches_pinned_literal` mit datiertem Vermerk |

Gesamt: `cargo test --release --lib` 585 gruen, `--no-run` fuer examples/benches gruen, Wheel
gebaut und installiert, Konventions-Check gruen.

**ANKER-DRIFT ROT durch A2 (NUTZER-ENTSCHEID, keine Reparatur):**
`anchor_drift_live_wheel_20260912_stage1.json`: erste Abweichung Schritt 99 von 1.763, Feld
`state`. Gegenprobe `..._ohneA2.json` (Wheel ohne den Phantom-Abzug): GRUEN. Der lebende
hv1-Pfad liest den Restvorrat ueber `column_build`/`plate_builder`, und die Phantom-Korrektur
aendert dort einen Zug. Das Anker-ARTEFAKT (eigenes Wheel) ist davon unberuehrt, die Leiter
haengt am Artefakt; ROT heisst: der lebende Code hat sich vom Artefakt entfernt. Optionen:
(a) A2 behalten und den Anker bewusst neu setzen (neues Leitersegment; Kanten ueber die Grenze
nie mischen), (b) A2 zuruecknehmen (der Phantom-Fehler bleibt, symmetrisch fuer alle Spieler),
(c) A2 nur im Netzpfad wirken lassen (Knopf, Default fuer die Heuristik aus) -- (c) haelt den
Anker und den Fix, ist aber eine zweite Wahrheit fuer denselben Restvorrat. Empfehlung des
Koordinators: (a), weil das Artefakt die Leiter traegt und der Fehler ein echter Sichtfehler
ist. Bis zum Entscheid: Code im Baum committet, Wheel MIT A2 installiert, KEINE Elo-Kante mit
dem lebenden hv1; die Referee-Kanten laufen ohnehin aus dem Artefakt-Wheel.
