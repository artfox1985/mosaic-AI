<!-- STATUS: OFFEN | Frage: Wie wird der Code vor dem Projektende sauber hinterlassen -- welche der beim Review 2026-09-11 gefundenen Defekte, Fussangeln und Altlasten werden behoben, in welcher Reihenfolge, mit welchen Toren? | Beleg: STUFE 1 GEBAUT (par.8: acht Punkte, 585 Tests gruen, Paritaets-Fixture wegen A2 bewusst neu, Kontrakt-Hash 39648b95bbba1acf). ANKER-DRIFT ROT durch A2 (Phantom-Abzug bewegt den lebenden hv1 ab Schritt 99) mit Entscheid (a) ERLEDIGT: Neuverankerung auf hv4_anchor, Leitersegment 2 (par.7a). Stufen 2/3 nach der letzten Generation. -->

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

**LEITER SEGMENT 2, ENDSTAND 23:25 (26 Kanten, alle am Anker; Block-Bootstrap) -- UEBERHOLT durch den Nachtrag "TREPPE GEFESTIGT" unten (2026-09-13, 01:00, 36 Kanten):**

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

## par.8a A13 ERLEDIGT: die vier widersprechenden Kommentare (2026-09-19, 09:40)

**Nutzer-Auftrag 2026-09-19:** *"ja zieh die kommentare gerade"*, waehrend Arena und Training laufen --
deshalb VORGEZOGEN aus Stufe 3 (par.5). Begruendung fuers Vorziehen: ein falscher Kommentar fuehrt aktiv in
die Irre, und genau das hat im Projekt schon einmal Zeit gekostet (`evaluations/STATUS.md`: ein
Code-Kommentar statt der Primaerquelle). Reine Kommentararbeit, kein Verhalten beruehrt, keine Rechenlast.

**Jede Stelle am Code nachgeprueft** (nicht aus dem Bericht uebernommen), sechs statt vier Fundstellen:

| # | Stelle | Kommentar behauptete | Code tut (Pruefstelle) |
| --- | --- | --- | --- |
| 1 | `tiling_solver.rs:100-102` | "Standard AUS bis gemessen ist" | `ROUND5_ENDSCORING_ENABLED = true` (`:103`) |
| 1b | `round5.rs:1602-1605` | "`=false` (Ist-Zustand)" | dieselbe Konstante ist `true`; der Testkoerper liest generisch |
| 2 | `tiling_solver.rs:1018-1019` | "STAND: AUS bis per Arena bestaetigt" | `NET_TILING_TIEBREAK_DEFAULT = 1` (`:1046`), seit 2026-09-17 Knopf statt Konstante |
| 3 | `provocation.rs:459-464` | "1. minimaler Ueberlauf auf die Strafleiste" | Sortiertupel beginnt mit der Konstante `0usize` (`:540`), Primaerkriterium ist die knappste Farbe |
| 3b | `provocation.rs:466-468` | "fordert GENAU `m.take.color` (`required_color_for`)" | `get_space` mit Fallunterscheidung `Wild`/`Normal`/`Special` (`:510-523`); `required_color_for` wird dort nicht gerufen |
| 4 | `envelope.rs:917-925`, `:932-934`, `:1007-1010` | Praedikat sei `get_space(..).is_some()`, "kein Filter auf Jokerplatten" | zusaetzlich `space_type == SpaceType::Wild` (`:1031-1032`), also NUR Jokerfelder |

**Die Zahl in der neuen Fassung von 1 ist belegt**, nicht uebernommen: 5 von 100 Runde-5-Drafting-Stellungen
(5,0 Prozent) waehlen einen anderen Zug, Laufzeit ON/OFF x1,08 (`archive/history.md`, Commit 3132b8c,
nachgelesen 2026-09-19).

**OFFEN: der Build.** Geaendert sind ausschliesslich Kommentarzeilen, ein `cargo`-Lauf zaehlt aber als Last
und die Maschine traegt Arena und Training. **Vor dem naechsten Wheel-Bau faellig:**
`cargo test --release --no-run` (auch `examples/` und `benches/`). Bis dahin gilt die Aenderung als
ungetestet -- Risiko gering (nur `//`- und `///`-Zeilen), aber nicht null: in 2 steht jetzt ein
Intra-Doc-Link auf `NET_TILING_TIEBREAK_DEFAULT`.

## par.8b KANDIDATENLISTE STUFE 2, am Code vom 2026-09-19 nachgeprueft (HEAD 7bbf54fc)

**Nutzer-Richtung 2026-09-19:** *"ich denk wir koennen dann auch viel vereinfachen. alte legacy sachen weg,
tote knoepfe weg usw"*. Das ist der Umfangs-Entscheid aus par.6 Punkt 3, aber noch keine pfadgenaue Freigabe --
**entfernt wird nichts vor ihr**, und jeder Rust-Schnitt braucht danach Wheel, Paritaets-Fixture und
Anker-Drift, also eine freie Maschine.

**Beweislage bei Knoepfen, wichtig fuer die Lesart:** seit A9 erzwingt der Waechter
`registered_non_dead_knobs_exist_in_code` (`knob_registry.rs:398`) fuer jeden nicht-`Tot`-Eintrag eine
Lesestelle; `tools/` wird nicht gescannt (`:320-330`). Ob ein Knopf LEBT, entscheidet daher der SETZER, nicht
die Lesestelle.

### A. Sicherer Schnitt (nichts liest es, kein Artefakt, kein Test haelt es)

| # | Kandidat | Pruefstelle |
| --- | --- | --- |
| 1 | vier Funktionen `is_row_complete`, `is_col_complete`, `completed_rows`, `completed_cols` | `board.rs:208-222`; **selbst nachgezaehlt 2026-09-19: 0 Treffer ausserhalb `board.rs`** |
| 2 | `envelope::tiling_cost_delta` samt eigenem Test | `envelope.rs:1387`, Test `:1688-1693`; die Rechnung steht lebend in `tiling_solver.rs:1636-1645` |
| 3 | Registratur-Zeilen ohne Lesestelle: `MOSAIC_ENDAWARE_W`, `MOSAIC_MUSTERREIHEN_W`, `MOSAIC_TORCH_IPC_PORT`, `_SHM_DIR`, `MOSAIC_GAME_TIMEOUT_SCALE` | `knob_registry.rs:203/204/206/207/196`; **selbst geprueft: `MOSAIC_ENDAWARE_W` hat nur zwei Kommentar-Treffer (`shaping.rs:543/546`), keine Lesestelle** |
| ~~4~~ | **GESTRICHEN 2026-09-19 vor der Ausfuehrung: der Wrapper ist NICHT tot.** `self_play.rs:7998` ruft ihn in einem Test auf (`resolve_and_apply_stack_draw(&mut game)`), und fuenf Kommentare plus der Knopf-Eintrag `knob_registry.rs:164` nennen ihn namentlich; sein eigener Kopfkommentar (`self_play.rs:1086-1091`) sagt ausdruecklich, Loeschen sei "ein eigener Entscheid, keine Aufraeumarbeit im Vorbeigehen". **Verschoben nach Gruppe B.** | – |
| 5 | `PyGame::net_eval_raw`, `clear_net`, `first_player` | `py.rs:204`, `:216`, `:260` -- kein Python-Aufrufer |
| 6 | `tools/probes/phase_sweep.py` (ihr Kopf erklaert sie selbst fuer wirkungslos); damit fallen `MOSAIC_PHASE_STAGE/_AMP/_PEAK` | `phase_sweep.py:1-15`, `knob_registry.rs:123-125` |
| 7 | drei Spec-Felder aus `KNOWN_FIELDS`, die KEINE Spec-Datei traegt: `special_unlock_beta`, `round_est_b_profile`, `moon_order_search_sims` | `net_mcts.rs:1260/1262/1266` |
| 8 | `--encoder`-Default `flat` -> `2d` an sechs Stellen | `train.py:3141`, `:1084`; `tools/build_cache_{incremental:235,parallel:247,serial:35}.py`; `tools/window_train_split.py:52` (dessen eigene Doku schreibt `2d` vor) |
| 9 | drei `server.py`-Endpunkte ohne Aufrufer | `/api/ai/suggest` `:1782` (abgeloest von `/api/ai/hint`), `/api/tiling/unplaceable` `:1173`, `POST /api/ai/config` `:1531` |

**Zu Punkt 8 selbst nachgeprueft (der Bericht liess es offen):** KEIN Skript verlaesst sich auf den Default.
Alle zehn `--encoder`-Vorkommen in `tools/*.sh` lauten `2d`; die zwei Skripte ohne Flag
(`night_v30_acceptance_b11.sh`, `night_v30_wheel_acceptance.sh`) nennen `train.py` nur in einer
`echo`-Zeile und rufen es nicht. Der Default-Wechsel ist damit fuer die Ketten folgenlos.

### B. Braucht eine Entscheidung (ein Test, eine Doku oder eine offene Prereg haelt es)

**Neu hier seit 2026-09-19:** der Wrapper `resolve_and_apply_stack_draw` (ex-Gruppe A Punkt 4; Test `self_play.rs:7998`, fuenf namentliche Kommentarverweise, ein Registratur-Eintrag). **Lehre:** die Kandidatenliste eines Agenten ist eine Behauptung -- dieser Eintrag stand dort als "keiner" bei den Aufrufern, obwohl der Test zwei Bildschirme unter der Definition steht. Jeder Punkt wurde vor der Ausfuehrung einzeln nachgeprueft; die uebrigen acht haben gehalten.

`envelope.rs`-Wrapper `X` gegen `X_in` (Test `:1545-1602` erst auf `_in` umstellen, dann schneiden);
die `#[allow(dead_code)]`-Gruppe in `plate_builder.rs:171/610/751/1167`, `column_build.rs:789`,
`provocation.rs:124/134`, `net.rs:990`; der Inversionspfad Runde 5 (`round_transition_resample.rs`,
`lib.rs:2145-2171`, laut eigener Moduldoku fuer 87,6 Prozent der Faelle unbrauchbar und abgeloest);
die drei PyO3-Diagnosen (`sibling_ranking`, `draw_stack_peek_impact`, `value_noise_floor` -- zwei davon
stehen in lebender Doku, `docs/architecture_reference.md:114`); `MOSAIC_TILING_PUNKTE_W` (Status `Aktiv`,
Text sagt selbst "gemessen wirkungslos", `knob_registry.rs:141`); `/api/stack/peek` (haengt an zwei
Server-Tests); vier weitere Debug-Endpunkte; `tools/diagnosis.py` (reines Flach-Werkzeug); 29 verwaiste
`models/*.spec.json` (Belegwert gegen Aufraeumen).

### C. Sollte bleiben

Die Knopf-Zweige im LEBENDEN Heuristik- und Merkmalspfad (`MOSAIC_SPALTENBAU_*`, `MOSAIC_PROVOKATION_SPALTE`,
`MOSAIC_VORZUG_SPALTE`, `MOSAIC_ASYM_VORZUG`): `plate_builder::drafting_preference` haengt in der
hv1-Zugkette, `achievable_column_fill` speist `col_f_max` (`features.rs:1553`), `cell_is_completable` speist
K3-R/K3-D (`envelope.rs:438/1004/1159`) -- und **der Elo-Anker `hv4_anchor` IST hv1-Code**. Hoechstens
Statuspflege. Ebenso bleiben die Stufen-Spec-Felder und `DIFFICULTY_PRESETS` (offene
`PREREG_difficulty_levels.md`), `MosaicNet` selbst (Altmodelle ladbar) und die Fixture-Bauknoepfe.

**Korrekturen am Review-Stand von par.2/par.4, die dabei herauskamen:** `run_net_vs_net_arena_hybrid` und
`onnx_eval` sind NICHT tot (`tools/hybrid_paired_arena.py:89` bzw. vier Aufrufer); A7 ist erledigt (der
stille Rueckfall `_ => 405` existiert nicht mehr, `features.rs:2172`); A6 steht noch (`game.rs:852-854`,
sieben Aufrufer).

## par.8c FREIGABE UND ABARBEITUNGSPLAN GRUPPE A (Nutzer 2026-09-19: "gruppe a komplett, sobald die maschine frei ist")

**Freigabe erteilt fuer alle neun Punkte aus par.8b Gruppe A**, Ausfuehrung erst bei freier Maschine. Stand
bei der Freigabe: vier Python-Prozesse aktiv (b01-Arena Seed 2 plus b02-Kette), Ende erwartet gegen 13:30-14:00
(b02 faehrt nach seinem Training noch zwei eigene Arenen a rund 95 min).

**Warum nichts vorgezogen wird, auch nicht der Python-Teil:** `train.py` wird von der laufenden b02-Kette
benutzt, und die Chunk-Prozesse importieren frisch (`feedback_dont_touch_files_read_by_running_runs`,
STATUS Abschnitt 7). Punkt 8 beruehrt genau diese Datei.

**Reihenfolge, mit dem Tor nach jedem Block:**

1. **Rust-Schnitte** (Punkte 1, 2, 3, 4, 5, 7): `board.rs:208-222`; `envelope::tiling_cost_delta` samt Test;
   fuenf Registratur-Zeilen; Wrapper `self_play.rs:1092-1095`; drei `PyGame`-Methoden; drei Felder aus
   `KNOWN_FIELDS`. **Tor:** `cargo test --release --no-run` (faengt `examples/` und `benches/`, siehe
   CLAUDE.md), dann Wheel-Bau, Netz-Paritaets-Fixture, **Anker-Drift**.
   **Der Anker-Drift ist hier mehr als Pflicht, er ist die Probe aufs Exempel:** alle sechs Schnitte
   betreffen angeblich toten Code. Bleibt die Drift GRUEN, ist das der Beleg; wird sie ROT, war der Code
   nicht tot, und der betroffene Schnitt geht zurueck (kein Anker-Neusetzen, CLAUDE.md).
2. **Python-Schnitte** (Punkte 8 und 9): `--encoder`-Default auf `2d` an sechs Stellen; drei `server.py`-
   Endpunkte. **Tor:** die 44 Werkzeug-Tests und ein Rauchtest der Ketten-Skripte mit `--limit`.
   Vorab geprueft (2026-09-19): kein `tools/*.sh` verlaesst sich auf den Encoder-Default.
3. **Dateiloeschung** (Punkt 6): `tools/probes/phase_sweep.py`. **Beleg:** die Datei ist git-getrackt
   (`git ls-files --error-unmatch` geprueft 2026-09-19), Wiederherstellung also aus der Historie -- kein
   restic-Beleg noetig, anders als bei Korpora und Modellen. Danach fallen `MOSAIC_PHASE_STAGE/_AMP/_PEAK`
   aus der Registratur.

**Tor, das leicht vergessen wird (Nachtrag 2026-09-19):** JEDE Aenderung an `knob_registry.rs` -- also die
Punkte 3 und 6 -- verlangt `python tools/generate_knob_docs.py` und das Mitcommitten von `docs/knobs.md`,
sonst faellt Regel 6 des Konventions-Checks. Am 2026-09-19 ist genau das einmal passiert, ausgeloest nicht
von einem Schnitt, sondern davon, dass `PREREG_dome_return_order.md` wieder auf OFFEN gesetzt wurde: die
generierte Uebersicht zaehlt Knoepfe nach dem Status IHRER Prereg (95 -> 93 beantwortet, 59 -> 57 mit
Default aus). Die Knopf-Doku haengt also nicht nur an der Registratur, sondern auch an den Prereg-Koepfen.

**Gegenprobe zu den Endpunkten (Nachtrag 2026-09-19), selbst nachgezaehlt:** zwei Treffer fuer
`/api/ai/debug` waren Teilstring-Effekte von `/api/ai/debug_history` (`static/debug.html:416`,
`engine/server_ai_test.py:124`). Eine exakte Suche mit Wortgrenze liefert NULL Aufrufer -- die Einstufung in
Gruppe A Punkt 9 steht. Umgekehrt lebt `/api/log_info`, obwohl eine Pfadsuche ihn nur in `server.py` findet:
`app.js` ruft ohne Praefix (`api('/log_info')`, aufgeloest in `static/js/app.js:88` zu `fetch('/api'+path)`).
**Wer Endpunkte auf Aufrufer prueft, muss die `api('…')`-Form nehmen, nicht den vollen Pfad.**

**Randbeobachtung, kein Kandidat:** unter `dist/Mosaic-AI/_internal/static/` liegt eine Kopie von `app.js`
(Stand 2026-08-15) aus einem aelteren Bundle-Bau. Build-Ausgabe, kein Quellstand -- relevant nur, falls zum
Projektabschluss ein frisches Bundle gebaut wird (dort haengt auch der Befund zu `/api/debug/replay_log`,
`portable_build_audit_2026-09-13.md:49`).

**Beleg-Korrektur zur Kandidatenliste (Nachtrag 2026-09-19):** Treffer von Knopfnamen unter `models/` sind
RAUSCHEN und kein Halter -- es sind die sechs eingefrorenen Artefakt-Binaries
(`frozen_champions/*/venv/.../mosaic_rust.*.pyd`, `frozen_heuristics/*/...`), die je eine einkompilierte
Kopie der Registratur-Stringtabelle tragen. Sie sind eingefroren und von jeder Quelltextaenderung unberuehrt.
Die echten Spec-Halter sind die Felder in den `spec.json`. Gruppe A bleibt davon unveraendert.

**Nicht in dieser Freigabe:** Gruppe B (braucht je einen eigenen Entscheid) und Gruppe C (bleibt; der
Elo-Anker ist hv1-Code).

**Nachtrag zur Beleglage von Punkt 2 (2026-09-19):** ein zweiter Grep ueber `engine/` inklusive Build-Baum,
`tools/` und die Root-`*.py` findet fuer `tiling_cost_delta` KEINEN Treffer ausserhalb von `envelope.rs`.
Einziger Nutzer bleibt der eigene Test.

## par.8d GRUPPE A AUSGEFUEHRT (2026-09-19, 12:30-13:10): 7 von 9 Punkten, alle Tore gruen

**Ausgefuehrt** nach dem Plan aus par.8c, sobald die Maschine frei war (b02-Kette durch um 12:10).

| Punkt | Ergebnis |
| --- | --- |
| 1 vier Funktionen `board.rs:208-222` | entfernt |
| 2 `envelope::tiling_cost_delta` | entfernt; **Test UMGEBAUT statt geloescht** (siehe unten) |
| 3 fuenf Registratur-Zeilen | entfernt |
| ~~4 Wrapper~~ | **VOR der Ausfuehrung gestrichen** (Test-Aufrufer, par.8b) |
| 5 `PyGame::net_eval_raw`/`clear_net`/`first_player` | entfernt, **plus Folgeschnitt** (siehe unten) |
| 6 `tools/probes/phase_sweep.py` + `MOSAIC_PHASE_*` | Datei per `git rm`, drei Registratur-Zeilen entfernt |
| ~~7 drei Spec-Felder~~ | **ZURUECKGENOMMEN nach rotem Test** (siehe unten) |
| 8 `--encoder`-Default auf `2d` | sechs Stellen umgestellt |
| 9 drei `server.py`-Endpunkte | entfernt (44 Zeilen), Kommentarverweis nachgezogen |

**Die Tore, in der Reihenfolge des Plans:**

| Tor | Ergebnis |
| --- | --- |
| `cargo test --release --no-run` (inkl. `examples/`, `benches/`) | gruen, 55,9 s |
| Lib-Tests | **702 passed, 0 failed** |
| Wheel-Bau plus Installation | gruen, Vertragshash **unveraendert** `6ef829e564c58bd5` |
| Netz-Paritaets-Fixture | gruen |
| **Anker-Drift** | **GRUEN, 1.763 Schritte Feld fuer Feld identisch** |
| Werkzeug-Tests `tools/tests` | **141 passed** |
| Knopf-Doku neu erzeugt, Konventions-Check | gruen (130 -> **122 Knoepfe**) |

**Der Anker-Drift ist der eigentliche Beleg:** alle sechs Rust-Schnitte betrafen angeblich toten Code, und
der lebende Anker spielt danach Zug fuer Zug wie das eingefrorene Artefakt. Waere ein Schnitt in lebenden
Code gegangen, haette genau dieser Lauf es gezeigt.

**ZWEI Punkte haben die Pruefung NICHT ueberstanden, und beide wurden von einem Tor gefangen:**

1. **Punkt 4 (Wrapper `resolve_and_apply_stack_draw`)** -- vor der Ausfuehrung gestrichen: `self_play.rs:7998`
   ruft ihn in einem Test auf, fuenf Kommentare und ein Knopf-Eintrag nennen ihn namentlich, und sein eigener
   Kopfkommentar sagt, Loeschen sei "ein eigener Entscheid". Die Kandidatenliste hatte "keiner" bei den
   Aufrufern stehen.
2. **Punkt 7 (drei Spec-Felder aus `KNOWN_FIELDS`)** -- ausgefuehrt, dann von drei roten Tests zurueckgeholt:
   `search_config_from_spec_file_takes_moon_order_search_sims_as_optional_field` und zwei Geschwister pruefen,
   dass Specs diese Felder tragen DUERFEN. Entfernen hiesse, Alt-Specs hart abzulehnen -- ein eigener
   Entscheid, kein Aufraeumen. Nach der Ruecknahme wieder 702 gruen.

**Zwei Folgefunde bei der Ausfuehrung, beide nur durch Hinsehen gefangen:**

* **Punkt 2:** der Test des Kandidaten pruefte in seiner letzten Zeile zusaetzlich `adjusted_tiling_score` --
  eine LEBENDE Funktion. Ein Loeschen des ganzen Tests haette ihre Abdeckung still mitgenommen. Der Test ist
  jetzt auf sie zugeschnitten und heisst `adjusted_tiling_score_is_points_plus_weighted_cost_delta`.
* **Punkt 5:** nach dem Entfernen der Methode `first_player` wurde das gleichnamige FELD nur noch gesetzt und
  nie gelesen (Compiler-Warnung in Sicht). Feld und Struct-Initialisierung mit entfernt; der
  Konstruktor-Parameter bleibt, er geht an `Game::start`.

**Erhalten geblieben ist das Messwissen der entfernten Knoepfe:** der Kommentarblock in `shaping.rs:543-548`
nennt weiterhin die gemessenen Werte (-0,07 und -0,84 Punkte bei w = 0,1), jetzt mit dem Vermerk, dass die
beiden Knoepfe am 2026-09-19 aus der Registratur entfernt wurden.

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


**TREPPE GEFESTIGT (2026-09-13, 00:03-00:59, `tools/night_ladder_gap_fill.sh`, exklusiv; vier Kanten
bis zum Deckel OHNE Frueh-Stopp, alle im Register):**

| Kante | Ergebnis | Bloecke | p | Wanduhr |
| --- | --- | --- | --- | --- |
| v22-b05@100 gegen hv4_anchor@600 (Referee, 3 x 50) | 108:42 (72 %) | 31:19, 39:11, 38:12 | Binomial 7e-8 | 166+164+151 = 481 s |
| v22-b05@400 gegen hv4_anchor@600 (Referee, 3 x 50) | 110:40 (73 %) | 34:16, 38:12, 38:12 | Binomial 1e-8 | 389+421+413 = 1.223 s |
| v22-b05@25 gegen @100 (paired_gating Seed 20261053, 75 Paare) | 61:89 (41 %) | 15 x 5 Paare | McNemar 0,013; Diff -0,37 [-0,64; -0,11] | 423 s |
| v22-b05@100 gegen @400 (paired_gating Seed 20261054, 75 Paare) | 61:89 (41 %) | 15 x 5 Paare | McNemar 0,034; Diff -0,37 [-0,69; -0,06] | 1.062 s |

Nebenbefunde: Punkte 42,8 gegen 48,5 und Strafleiste 11,8 gegen 9,6 (@25 gegen @100: die flache
Suche verliert an der Strafleiste); Punkte 36,6 gegen 42,3 bei gleicher Strafleiste 12,4 gegen 12,3
(@100 gegen @400). hv4@600 ist mit 72-73 Prozent gegen v22@100 und @400 die Sprosse, die zwischen
Anker und Netzblock fehlte (gegen hv4@150 lagen die Netze bei 76-90 Prozent).

**Die Treppe traegt:** Anker (fix) -> hv4@600 (4 Kanten, alle am Deckel) -> v22@25 (5 Kanten, 2 am
Deckel: hv4@600, @100 Seed 53) -> v22@100 (7 Kanten, 3 am Deckel: hv4@600, @25, @400) -> v22@400
(6 Kanten, 3 am Deckel: v21, hv4@600, @100). Jeder Treppenknoten hat mindestens zwei Kanten ohne
Frueh-Stopp; kein Knoten haengt nur an frueh gestoppten Kanten. Nicht-Transitivitaet bleibt am
Boden sichtbar (v22@25 gegen hv4@600 50 Prozent, gegen hv4@150 76 Prozent), Bradley-Terry mittelt.

**LEITER SEGMENT 2, ENDSTAND 2026-09-13 01:00 (36 Kanten, alle am Anker; Block-Bootstrap,
`python tools/elo_tracker.py report`):**

| Knoten | Elo | KI95 | Partien | Frueh-Stopp-Kanten |
| --- | --- | --- | --- | --- |
| v28-b02@400 (Champion) | **1353** | [1306, 1402] | 1.410 | 3/7 |
| v28-b01@400 | 1326 | [1277, 1381] | 400 | 1/3 |
| v27-b01@400 | 1310 | [1264, 1359] | 1.280 | 2/5 |
| v26-b01@400 | 1255 | [1203, 1308] | 400 | 2/4 |
| v22-b05_live@400 | 1213 | [1178, 1254] | 610 | 3/6 |
| v24-b07@400 | 1207 | [1163, 1256] | 400 | 4/5 |
| v21_2d_brierbest@400 | 1204 | [1164, 1249] | 500 | 3/5 |
| v22-b05_live@100 | 1173 | [1136, 1212] | 710 | 4/7 |
| v28-b02@100 | 1146 | degeneriert | 30 | 1/1 |
| v22-b05_live@25 | 1103 | [1062, 1144] | 500 | 3/5 |
| Heuristik_hv4_anchor@600 | 1046 | [1009, 1083] | 600 | 0/4 |
| Heuristik_hv4_anchor@150 | 1000 | fix | 1.100 | 4/10 |
| Heuristik_hv2_generator@150 | 983 | [944, 1018] | 500 | 4/6 |
| Heuristik_hv3_generator@150 | 978 | [938, 1016] | 400 | 2/4 |

Bewegung gegen 00:02 (32 Kanten): Champion 1348 -> 1353, Intervalle der Netzknoten um 3-8 Punkte
schmaler (v22@400 [1145, 1241] -> [1178, 1254]); die vier Kanten haben die Leiter unten gestrafft,
nicht verschoben. Artefakte `rung_v22b05s{100,400}_vs_hv4s600_b1..b3.json`,
`paired_gating_v22-b05_s25_vs_s100_seed53_full.json`, `..._s100_vs_s400_seed54_full.json`.

## AGENTEN-AUFTRAG (Stand 2026-09-13, fuer eine autonome Abarbeitung durch einen Opus-Agenten)

### 1. Ziel und Verdikt-Regel

Zu beantworten ist, wie der Code vor dem Projektende sauber hinterlassen wird. Die Verdikt-Regel
ist NICHT Elo, sondern die aus **par.1** und **par.7**: jeder Schnitt braucht einen von vier
Gruenden -- Defekt, Fussangel, toter Code oder Widerspruch -- und jedes gebaute Stueck ist an
seinem Tor gemessen (par.3 je Punkt). Erfolgsmass sind Irrtumskosten und Nachvollziehbarkeit
(CLAUDE.md "Infrastruktur bewerten"). **Stufe 1 ist gebaut und registriert** (par.8: acht
Punkte, 585 Lib-Tests gruen, Kontrakt-Hash `c65768636c0560a7` -> `39648b95bbba1acf`,
Paritaets-Fixture wegen A2 bewusst neu); der Anker-Drift-ROT ist mit Entscheid (a) erledigt
(par.7a, Segment 2 mit `hv4_anchor`). **Offen sind Stufe 2 (Altlast) und Stufe 3 (Doku), beide
NACH der letzten Generation**, sowie der Umfang von Stufe 2 (par.6 Punkt 3, Nutzer-Entscheid).

### 2. Voraussetzungen

- **Maschine frei laut Prozessliste** fuer jedes `cargo`, jedes Wheel und jeden Werkzeug-Test;
  Code SCHREIBEN darf neben einem Lauf, BAUEN nicht (par.3, Randbedingungen; CLAUDE.md
  "ein Build ist Nebenlast").
- **Zeitpunkt:** Stufen 2 und 3 laufen erst nach der LETZTEN Generation, also nach der
  v30-Promotion (par.5a, Nutzer-Entscheid 2026-09-12: v30 wird released und ist der
  Projektabschluss). Vorher wird an ihnen nichts gebaut.
- **Quellen, die vorliegen muessen:** die sechs Bereichsberichte und die Zusammenfassung unter
  `evaluations/review/code_review_2026-09-11_*.md` (dort stehen die Funde mit Datei:Zeile),
  dazu par.2 dieser Datei (Tabelle A1-A13 und die Altlast-Liste).
- **Anker und Fixture:** Anker `models/frozen_heuristics/hv4_anchor`, Champion-Fixture
  `engine/tests/fixtures/net_parity_champion.txt` (Stand nach der v28-b02-Promotion
  `e1f94c44f0c7959b`); beide sind nach JEDEM Rust-Schnitt zu pruefen.
- **Keine andere Prereg muss vorher durch sein**; sachlich haengt Stufe 3 an
  `PREREG_difficulty_levels.md` (die toten `DIFFICULTY_PRESETS` gehen dort auf) und an der
  Namensumsetzung "Tessa" (par.5a).

### 3. Schritte

**P1 -- Umfang von Stufe 2 festlegen (Nutzer-Entscheid par.6 Punkt 3)**

1. **Schritt "Zuschnitt registrieren und Nutzer fragen".** par.4 nennt Kandidaten, nicht einen
   beschlossenen Umfang: tote Funktionen und Diagnose-Einstiege, Inversions-Pfad Runde 5 samt
   PyO3-Huelle, `envelope::tiling_cost_delta`, die `X`/`X_in`-Wrapper in `envelope.rs`,
   `--encoder flat` als Default in `train.py` und drei Cache-Werkzeugen, acht `server.py`-
   Endpunkte ohne Frontend-Aufrufer, Auslagerung des Testmoduls von `net_mcts.rs` per `#[path]`,
   Abspaltung von `self_play_diagnostics.rs`, deutsche Bezeichner (Kern 13,
   `plate_builder.rs` 25 Typ-/Konstantennamen; `TileColor`-Varianten NICHT), entschiedene
   Knoepfe und die rund 4.800 Zeilen Plattenbauer-Code. Der Agent legt je Kandidat Nutzen,
   Nahtbreite und Risiko vor (Feedback `measure_seam_width_not_lines`: vor jedem Schnitt die
   Namen ueber der Naht ZAEHLEN) und wartet auf die Freigabe je Pfad. **Nicht raten.**

**P2 -- A6, A7, A11 abarbeiten (Stufe 2, par.2 und par.4)**

2. **A11 zuerst MESSEN, dann entscheiden** (par.2: "2, erst messen"): Mutex je Knoten bei
   ausgeschaltetem Sammel-Faden und GameState-Klon je Knoten (`net_mcts.rs:1874-1890`, `:2044`).
   Messform: Wanduhr je Partie mit gegen ohne Aenderung am argmax-Instrument, 200 Partien @400,
   `--deterministic --no-root-noise`, threads 11, exklusiv (gemessen rund 2.050 s je Lauf,
   `docs/measured_runtimes.md`). Ohne Messung kein Umbau.
3. **A6** (`Game::is_over()` ab Rundenbeginn 5 wahr, `game.rs:700`) und **A7** (Eroeffnungs-
   Records: Policy-Ziel auf toter ID 405 bei Gewicht 0, `features.rs:1477`,
   `corpus_dataset.py:1331`) nach der Freigabe aus P1; A7 beruehrt den Trainings-Cache und
   braucht deshalb einen Cache-Schluessel-Blick, bevor etwas gebaut wird.

**P3 -- Tore je Schnitt (bindend, par.4 Schlusszeile)**

4. Nach JEDEM Rust-Schnitt, exklusiv und in dieser Reihenfolge:

   ```
   $env:PATH = "$(python -c 'import sys,os;print(os.path.dirname(sys.executable))');" + $env:PATH
   cd engine; cargo test --release --lib        # gemessen 80-85 s
   cargo test --release --no-run                # examples/benches, gemessen 33 s
   python -m maturin build --release            # gemessen 26-34 s
   python -m pip install --force-reinstall --no-deps engine/target/wheels/mosaic_rust-0.1.0-cp314-cp314-win_amd64.whl
   python -X utf8 -u tools/verify_frozen_heuristic.py --artifact-dir models/frozen_heuristics/hv4_anchor --out evaluations/artifacts/anchor_drift_live_wheel_<datum>_stufe2.json
   python -X utf8 -u tools/verify_frozen_heuristic.py --artifact-dir models/frozen_heuristics/hv4_anchor --venv --out evaluations/artifacts/anchor_conservation_artifact_wheel_<datum>_stufe2.json
   python -X utf8 tools/check_conventions.py
   ```

   Netz-Paritaets-Fixture des Champions muss UNVERAENDERT bleiben (ein Aufraeum-Schnitt darf das
   Spiel nicht bewegen); tut sie es doch, ist das ein Befund und ein Stopp-Punkt.
   Nach Python-Schnitten: die Werkzeug-Tests (`python -X utf8 -m pytest tools/tests -q`) und ein
   Rauchtest der Ketten-Skripte mit `--limit`.
   **Bei Abbruch:** `os error 32` unter OneDrive ist eine Dateisperre, Wiederholung ist regulaer
   gruen; `STATUS_DLL_NOT_FOUND` heisst, die Python-DLL fehlt im PATH (erste Zeile).

**P4 -- Stufe 3, Doku (par.5, rund 3 h, keine Rechenlast)**

5. Zeilenverweise in `engine/src/knob_registry.rs` und `docs/architecture_reference.md`
   nachziehen; die vier widersprechenden Kommentare aus A13 beheben
   (`ROUND5_ENDSCORING_ENABLED`, `NET_TILING_TIEBREAK_ENABLED`, `provocation.rs:459-464`,
   Jokerfeld-Kommentare in `envelope.rs`); `python -X utf8 tools/generate_knob_docs.py`;
   Abschlusskapitel "Stand beim Projektende" in `docs/architecture_reference.md`.
6. **Name "Tessa" (par.5a), NACH der letzten Promotion:** Manifestfeld `display_name: "Tessa"` im
   Artefakt des Schlusschampions (`models/frozen_champions/<name>/manifest.json`); GUI-Anzeige
   in `server.py` und `static/js/app.js`; `tools/analyze_game_log.py` muss den Namen als KI-Seite
   erkennen (haengt heute an "KI" -- Pruefstelle beim Bau); README "Current Status" mit Name und
   Generationsname nebeneinander; Schwierigkeitsleiter Stufe "Meister" = Tessa.

**P5 -- Leiter-Pflege (par.7a, laufend)**

7. Der Anker ist `hv4_anchor`, Segment 2; Kanten ueber die Segmentgrenze werden NIE gemischt.
   Wird die Loeschliste aus STATUS Abschnitt 1 abgearbeitet (`hv1_anchor` ist obsolet), sind die
   Textverweise nachzuziehen: CLAUDE.md Abschnitt Anker-Invarianz, `docs/working_rules.md` Z.50,
   `docs/generation_naming.md` Z.68, `docs/architecture_reference.md` Z.39, Docstrings
   `tools/verify_frozen_heuristic.py` Z.31/33 und `tools/anchor_arena.py` Z.8, Skill
   `mosaic-anchor-invariance`. **Die Loeschung macht der Nutzer**; die Sitzung traegt danach
   Snapshot-ID und Loeschung in Chronik und STATUS ein.

### 4. Auswertung und Registrierung

- **Zahlen mit n, Grundmenge, Einheit**: Testlaeufe "n = Tests, Grundmenge cargo-Lib-Suite,
  Einheit gruene Tests"; A11-Messung "n = 200 Partien, Grundmenge argmax-Self-Play-Partien,
  Einheit Sekunden je Partie"; Nahtbreite "n = Namen ueber der Naht, Grundmenge oeffentliche
  Symbole des Moduls, Einheit Namen".
- Eine Arena laeuft in dieser Prereg nur, falls ein Schnitt das Spiel doch bewegt; dann gelten
  die sechs Standard-Kennzahlen (CLAUDE.md) aus den Logs.
- **Registrierung in par.8**, je Punkt eine Zeile Bau plus Tor; **Zeile-1-Kopf im selben Zug**
  nachziehen (Status bleibt OFFEN, bis Stufen 2 und 3 durch sind), danach sofort
  `python tools/generate_prereg_index.py`.
- **STATUS.md Abschnitt 1** und `archive/history.md` fortschreiben.
- **Rueckwaerts-Pruefung**:
  `grep -rn "code_cleanup_closeout\|39648b95bbba1acf\|hv4_anchor\|net_parity_champion" evaluations/ docs/ tools/ engine/`
  -- jede Fundstelle lesen.
- **Laufzeiten** ins Artefakt je Lauf; Planungsgroessen nach `docs/measured_runtimes.md`
  (bereits vorhanden: "Code-Abschluss Stufe 1: Tests (585) / Paritaets-Fixture / Wheel / Drift
  = 80 s / 14 s / 26 s / 17 s").
- **Elo-Register**: nur bei Kanten am Champion. Ein Aufraeum-Schnitt erzeugt keine Kante; wenn
  doch eine noetig wird (weil das Spiel sich bewegt hat), ist das der Stopp-Punkt unten, nicht
  eine stille Register-Zeile.

### 5. Stopp-Punkte fuer den Nutzer

- **Umfang von Stufe 2** (par.6 Punkt 3) -- insbesondere die Plattenbauer-Zweige. **Nutzer fragen.**
- **Jede Loeschung** von Code, Modellen, Artefakten oder Skripten: pfadgenaue Freigabe, und die
  Loeschungen der Loeschliste erst nach dem Start des v29-Self-Plays (restic-daily).
- **Paritaets-Fixture aendert sich durch einen Aufraeum-Schnitt**: anhalten und melden; ein
  Aufraeumen, das das Spiel bewegt, ist kein Aufraeumen.
- **Anker-Drift ROT: anhalten.** Nutzer-Entscheid (Anker neu setzen oder Aenderung
  zuruecknehmen); Praezedenz ist par.7a.
- **Kein Push** ohne Anweisung; Ahead-Stand melden (der pre-push-Hook baut und testet, zaehlt
  also als Last).
- **Champion-Wechsel und Anker-Neusetzung** sind nie Teil dieser Prereg.

### 6. Abhaengigkeiten und Reihenfolge

**Vorher:** die letzte Generation (v30) muss durch sein, samt Promotion; bis dahin ruht dieser
Strang bis auf P1 (Umfangs-Entscheid), der jederzeit vorgelegt werden kann.
**Nachher:** Leiter-Endfassung mit dem v30-Champion (`PREREG_difficulty_levels.md` Stufe 5),
Schlussmodell "Tessa" (par.5a), STATUS-Neufassung als Abschlussbericht, letzter
restic-Snapshot mit Beleg (`PREREG_v29_window.md` par.8 Punkt 3).
Zum Begleitprogramm von `PREREG_v29_window.md` par.7 gehoert dieser Strang NICHT -- er ist der
Abschluss danach.
