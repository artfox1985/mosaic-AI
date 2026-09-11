<!-- STATUS: OFFEN | Frage: Wie wird der Code vor dem Projektende sauber hinterlassen -- welche der beim Review 2026-09-11 gefundenen Defekte, Fussangeln und Altlasten werden behoben, in welcher Reihenfolge, mit welchen Toren? | Beleg: nichts gebaut. Review mit sechs Bereichsberichten liegt vor (evaluations/review/), zehn tragende Funde am Code geprueft (par.2). STUFE 1 (Korrektheit und Beobachtbarkeit, acht Punkte inkl. A4 und A10, par.3) vom Nutzer FREIGEGEBEN 2026-09-11, A8 gebaut; Stufe 2 (Altlast, par.4) und Stufe 3 (Doku, par.5) folgen nach der letzten Generation; offen bleibt der Umfang von Stufe 2 (par.6). -->

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

## par.8 Ergebnisse (leer bis zum Bau)

Nichts gebaut (Stand 2026-09-11, 23:10).
