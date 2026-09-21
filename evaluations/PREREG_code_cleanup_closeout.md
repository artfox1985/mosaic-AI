<!-- STATUS: OFFEN | Frage: Wie wird der Code vor dem Projektende sauber hinterlassen -- welche Defekte, Fussangeln und Altlasten werden behoben, in welcher Reihenfolge, mit welchen Toren? | Beleg: Stufe 1, Gruppe A, Bonuschips (par.8, 8d, 8e). par.8i: die zehn Posten aus par.8g als EIN Buendel, 9 Beispiele und 3 tote E2E-Skripte raus, 3 Punkte abgelehnt. par.8j: Warteschleife sah cargo nicht (gemessen 3 gegen 0), Spec-Abbildung 5 echte Suchknoepfe kurz (keine registrierte Zahl betroffen), tote Modell-Defaults raus. par.8k: 62 rohe Korpus-Leser in 61 Werkzeugen auf corpus_io, davon 43 LIVE defekt (gzip). Alle Tore gruen. Offen: par.8h Punkte 2, 4, 9, 10 und par.8g Punkt 10. -->

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

### NACHTRAG 2026-09-20: Punkt 2 ist kleiner als hier beschrieben, Punkt 3 war ueberfaellig

**Die Behauptung "die Log-Auswertung haengt heute an `KI`" stimmt nicht** (am Code geprueft):

* `tools/analyze_game_log.py` nennt "KI" ausschliesslich in Kommentaren; eine Suche nach dem
  Literal als WERT (`== "KI"`) liefert im ganzen Baum keinen Treffer.
* Wer die KI-Seite braucht, nimmt das STRUKTURIERTE Feld `ai_player` aus dem JSON-Kopf des Logs
  (`tools/claude_play.py:239`, `tools/game_log_report.py:68`) -- der Kopf traegt zusaetzlich
  `ai_enabled` und `ai_model`.
* Die Treffer auf `st.get("players", ...)` in `claude_play.py`, `corpus_sanity_check.py` und
  `diagnosis.py` sind die SPIELERBRETTER im Zustand, nicht die Namensliste des Log-Kopfs. Zwei
  verschiedene Dinge unter demselben Wort.

**Der Name wird allein im Frontend gesetzt**, `static/js/app.js:227` und `:238`
(`aiOn ? 'KI' : p2name`), und landet von dort ueber `names` in den Log-Kopf.

**Damit ist die Umbenennung mechanisch und dreiteilig**, ohne Parser-Arbeit:

| Schritt | Stelle | Zeitpunkt |
| --- | --- | --- |
| 1 | `display_name: "Tessa"` im Manifest des Schluss-Artefakts | nach der LETZTEN Promotion |
| 2 | zwei Literale in `static/js/app.js:227` und `:238` | mit Schritt 1 |
| 3 | README "Current Status" | mit Schritt 1 |

**Ein Caveat bleibt:** Alt-Logs tragen `"KI"` im Kopf, neue `"Tessa"`. Kein heutiges Werkzeug
wertet ueber den Namen aus, aber wer kuenftig eines baut, nimmt `ai_player` und nicht den Namen.

### ALLE DREI SCHRITTE AUSGEFUEHRT (2026-09-20, nach der Promotion)

Anlass fuer die Eile bei 2 und 3 war ein Nutzer-Befund: *"die umbenennung auf tessa hats nicht ins
portable bundle geschafft. ich seh im gui noch ueberall KI stehen."* Schritt 1 war mit dem Artefakt
erledigt, die beiden anderen lagen als Nutzer-Entscheid -- aber das Bundle war da schon gebaut.

| Schritt | Umsetzung |
| --- | --- |
| 1 Manifestfeld | `display_name: "Tessa"` in `models/frozen_champions/v31-b01/manifest.json` |
| 2 Frontend | **EINE Konstante statt zweier Literale**: `AI_DISPLAY_NAME` in `static/js/app.js`, benutzt an den zwei Stellen, die den Spielernamen setzen; dazu vier sichtbare Texte in `static/index.html` ("Gegen Tessa spielen", die Sims-Erklaerung, "Tessa / Spieler 2", "Tessa denkt") |
| 3 README | Champion-Zeile nennt `v31-b01` und Tessa nebeneinander |

**Die Konstante ist bewusst mehr als par.5a verlangte.** Am selben Tag haben zwei fest verdrahtete
Werte gezeigt, was mit von Hand nachzuziehenden Angaben passiert: das README stand zwei
Generationen zurueck, `dist/mosaic_release.spec` drei. Ein Name an EINER Stelle wandert nicht
auseinander.

**NICHT umbenannt, bewusst:** die drei GUI-Stellen im System-Sinn (Button "KI-Debugger", Abschnitt
"KI-Einstellungen", das zugehoerige Label) und die Fehlertexte in `server.py` ("Nicht der Zug der
KI", "KI-Fehler: ..."). Die beschreiben das System, nicht den Spieler. Offener Nutzer-Entscheid.

**Am laufenden Bild geprueft**, nicht an der Datei: Server gestartet, `/api/champion` meldet
`v31-b01_brierbest`, die Konsolenzeile "Champion-Spec ..." erscheint, die Oberflaeche zeigt an
vier Stellen Tessa und an keiner mehr "KI" als Spielernamen. Das portable Bundle ist danach neu
gebaut; die erste Fassung vom selben Tag trug die Umbenennung noch nicht.

**Punkt 3 war unabhaengig vom Abschluss faellig und ist am 2026-09-20 ausgefuehrt:** das README
stand zwei Generationen zurueck (Champion `v28-b02`, Elo 1394), waehrend `v30-b02` mit 1436
amtiert. Das Repo ist oeffentlich; eine veraltete Champion-Zeile ist dort keine Kosmetik.
Nachgezogen sind die Champion-Zeile, die drei tragenden Kanten, der Kaltstart-Befund und die
Sprossenliste der Leiter (deren Zahlen sich mit dem Nachtrag der beiden `v30-b01`-Kanten
verschoben hatten).

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

## par.8e GRUPPE B, Punkt 3: die Bonusplaettchen kanonisch fuehren (2026-09-19)

**Nutzer-Befund 2026-09-19, 23:10:** *"ist dir bewusst dass es bei den bonusplaettchen dubletten
gibt? sprich die anzahl ist korrekt, aber schwarz/blau ist zb gleich wie blau/schwarz."* Dazu die
Einordnung des Nutzers: *"wird keinen grossen einfluss haben, sondern eher der vereinfachung
dienen."* -- damit ist der Punkt als VEREINFACHUNG registriert, nicht als Defektbehebung.

**Der Bestand, am Pool nachgezaehlt** (`engine/src/dome.rs:250-273`): 20 Chips, davon 10
einfarbige (je zwei pro Farbe) und 10 zweifarbige aus fuenf Kombinationen zu je zwei Stueck. Bei
drei Kombinationen stehen beide Eintraege zeichengleich, bei zweien ist die Reihenfolge
vertauscht: `[Schwarz, Blau]` (idx 6) gegen `[Blau, Schwarz]` (idx 15) und `[Gelb, Schwarz]`
(idx 7) gegen `[Schwarz, Gelb]` (idx 12). Die Vertauschung kommt aus der Quelle
`docs/bonus_chips_colors.csv` (Zeilen 7 und 16 bzw. 8 und 13), einer Abschrift der echten
Plaettchen; im Spiel traegt die Reihenfolge keine Bedeutung.

**Wo sie folgenlos ist, geprueft 2026-09-19:**

* Wertung: `round_end.rs:504` (`chip_sig`) faltet den Chip zu einer Farb-Bitmaske; der
  Kopfkommentar dort nennt Chips gleicher Signatur ausdruecklich austauschbar.
* Verbrauch: `round_end.rs:516`, `:596`, `:658` fragen `colors.contains(&color)`.
* Netz-Eingabe: `features.rs:1349` setzt eine Fabrik-Maske je Farbe, `features.rs:1402` zaehlt die
  Hand je Farbe. **Das Netz sieht die Reihenfolge nicht**, eine Umstellung aendert keine Eingabe.

**Wo sie durchschlaegt, beide Male als Arbeit und nicht als Ergebnis:**

1. `round5.rs:281` gruppiert die verdeckten Chips ueber Vec-Gleichheit (`*c == colors`). Liegen
   die beiden vertauschten Zwillinge gleichzeitig verdeckt, entstehen zwei Zufallsaeste mit je
   1/n statt einem mit 2/n. Die Kinder sind wertgleich (nur `chip_id` unterscheidet sie, und der
   fliesst laut dem Audit in `tiling_solver.rs:266` nie in eine Wertung), die Erwartung bleibt
   unverzerrt -- es ist ein Ast zu viel. Der Kopfkommentar `round5.rs:251-254` verspricht genau
   das Gegenteil ("farbgleiche Chips ... fallen zusammen") und loest es in zwei von fuenf
   Kombinationen nicht ein.
2. `tiling_solver.rs:331` legt `bonus_chip_colors` UNSORTIERT in den `TilingKey`. Zwei identische
   Bretter bekommen dadurch verschiedene Schluessel, also einen Fehlgriff statt eines Treffers.
   Dieselbe Klasse trifft ohnehin die Reihenfolge der Chips in der Hand; die Farbvertauschung ist
   ein weiterer Fall davon. Die Signaturfunktion `tiling_solver.rs:842` sortiert dagegen beides
   sauber -- die Kanonisierung existiert also schon einmal im selben Modul.

**Vorschlag (ein Entscheid, zwei Fassungen):** entweder die Farben beim Poolbau sortieren
(`dome.rs:250`, kleinster Eingriff), oder den Chip gleich als Bitmaske statt als
`Vec<TileColor>` fuehren; dann faellt die Vec-Gleichheit in `round5.rs` als Sonderfall weg und
der Tiling-Schluessel wird stabiler. Im zweiten Fall waere `bonus_chip_colors` im `TilingKey`
zusaetzlich zu sortieren, sonst bleibt der Handreihenfolge-Fall bestehen.

**Zwei Zwaenge, die den Zeitpunkt bestimmen:**

* `serialize.rs:219` schreibt die Farben in SPEICHERREIHENFOLGE ins Record. Eine Umstellung
  aendert damit die Records und zieht die Netz-Paritaets-Fixture nach
  (`feedback_record_field_must_precede_generation`: die Fixture hasht Records, nicht Eingaben).
  Der richtige Zeitpunkt ist deshalb ein Generationswechsel, nicht mitten in einem Fenster.
* Ein Wheel-Bau zaehlt als Last und geht nicht neben einer laufenden Erzeugung.

**Tore wie in Gruppe A:** `cargo test --release --no-run`, Lib-Tests, Wheel mit unveraendertem
Vertragshash, Netz-Paritaets-Fixture neu, **Anker-Drift gegen `hv4_anchor`** als Probe aufs
Exempel. Die Drift ist hier der eigentliche Beleg: aendert sich ein einziger Zug, war die
Reihenfolge eben doch irgendwo tragend.

### GEBAUT 2026-09-19: die Anzeige-Haelfte (Nutzer: "fuers gui am server waer es aufjedenfall gut das richtig zu stellen")

**Nur `static/js/app.js`, kein Engine-Code, kein Wheel, keine Records** -- deshalb neben der
laufenden v31-Erzeugung zulaessig. Neuer Helfer `chipColors(chip)` (Z.813-822) gibt die Farben
eines Plaettchens in der Enum-Reihenfolge der Engine zurueck (`engine/src/tile.rs:5-13`: Blau,
Gelb, Rot, Schwarz, Tuerkis), damit Anzeige und Farb-Bitmaske dieselbe Konvention haben.
Umgestellt sind die vier Stellen, an denen die Farbreihenfolge sichtbar wurde:

| Stelle | Was vorher passierte |
| --- | --- |
| Handchips, Z.1317-1323 | die beiden Haelften wurden in Speicherreihenfolge gefaerbt: zwei gleiche Chips sahen GESPIEGELT aus |
| Tooltip der Handchips und der Geister-Chips | las sich als "schwarz+blau" beim einen und "blau+schwarz" beim anderen |
| Chip auf der Manufaktur, Z.1729-1731 | dieselbe Spiegelung |
| Auswahl-Dialog beim Chip-Einsatz, Z.2493 | dieselbe Spiegelung in der Kostenvorschau |

**NICHT geprueft am laufenden Bild:** ein Bonuschip wird erst sichtbar, wenn seine Manufaktur
leer ist, die Gegenprobe braucht also eine gespielte Partie mit Netzzuegen -- das ist Last und
wartet auf eine freie Maschine. Geprueft ist die Ersetzung an allen vier Stellen (Zaehlung je
Muster genau 1) und die Farbfolge gegen das Enum; ein JS-Syntaxlauf war mangels `node` nicht
moeglich. **Offen bleibt die Engine-Haelfte oben** (Poolbau oder Bitmaske, plus der
Tiling-Schluessel); erst sie spart die Arbeit in `round5.rs` und im Cache.

### GEBAUT 2026-09-20: die Engine-Haelfte (Nutzer: "dann mach die engine haelfte gleich mit. es gibt kein v32")

Ausgefuehrt, nachdem die v31-Erzeugung fertig war und der Cache-Waechter beendet: Maschine frei,
also durfte gebaut werden. **Zeitpunkt bewusst hier**, weil eine Record-Aenderung an einen
Generationswechsel gehoert und v31 laut Nutzer die letzte Generation ist.

**Zwei Aenderungen, beide klein:**

1. `dome::build_bonus_chip_pool` sortiert die Farben jedes Plaettchens beim Bau des Vorrats
   (`colors.sort_by_key(|c| *c as u8)`, dieselbe Enum-Ordnung wie die Farb-Bitmaske in
   `round_end::chip_sig`). Damit fallen `[Schwarz, Blau]` und `[Blau, Schwarz]` zusammen.
   **Die beiden Vergleichsstellen sind dadurch OHNE eigene Aenderung geheilt:** die Gruppierung
   der verdeckten Chips in `round5::action_outcomes` macht aus zwei Zufallsaesten wieder einen mit
   Gewicht 2, und `tiling_solver::tiling_key` vergibt fuer identische Bretter denselben Schluessel.
2. `tiling_solver::tiling_key` sortiert zusaetzlich UEBER die Chips, nicht nur in ihnen. Das war
   der groessere Anteil derselben Fehlerklasse: zwei Bretter mit denselben Plaettchen in anderer
   AUFNAHMEREIHENFOLGE bekamen bisher verschiedene Schluessel. Zulaessig, weil Chips gleicher
   Farbmenge austauschbar sind (`round_end::chip_sig`-Kopfkommentar).

**Die Tore, in der Reihenfolge des Laufs:**

| Tor | Ergebnis |
| --- | --- |
| `cargo test --release --no-run` inkl. `examples/` und `benches/` | gruen, 1 min 19 s |
| Lib-Tests | **700 gruen**, 19 uebersprungen, 93 s; einziger Fehlschlag die Netz-Paritaets-Fixture |
| Anker-Fixtures `mcts.rs:1622` und `:1714` | gruen, die zweite deckt den R5-Pfad ab |
| Wheel gebaut und installiert | 30 s |
| **Vertragshash** | **`6ef829e564c58bd5` unveraendert**, 888/414 |
| Kanonisierung am Wheel | 86 zweifarbige Chips ueber 40 Partien: **5 Farbmengen in 5 Schreibweisen** (vorher waeren es 7 gewesen) |
| Netz-Paritaets-Fixture neu | `16208f49af911525` -> `bc1733c0f303f743`, Abnahme im FRISCHEN Prozess gruen |
| **Anker-Drift** | **ROT, vollstaendig aufgeklaert -- siehe unten** |

**Dass der Vertragshash steht, ist der tragende Nebenbefund:** er deckt `INPUT_SIZE`,
`NUM_ACTIONS` und die Merkmalsformel ab. Die Farbordnung erreicht die Netz-Eingabe also nicht, und
der bereits geschriebene v31-Korpus bleibt gueltig. Haette er sich bewegt, waere hier Schluss
gewesen.

### Die ROTE Anker-Drift, aufgeklaert (2026-09-20)

`tools/verify_frozen_heuristic.py --artifact-dir models/frozen_heuristics/hv4_anchor` meldet
**ROT: 0/1 Dateien Feld fuer Feld gleich**, erste Abweichung
`/state/factories[1]/bonus_chip/colors[0]`. Das Werkzeug haelt beim ersten Unterschied an und kann
darum nicht sagen, ob der Anker ANDERS SPIELT oder nur anders schreibt. Diagnose mit einer
Wegwerf-Sonde (Wiederholungslauf desselben Rezepts, 10 Partien, 16 s, dreifacher Vergleich):

| Vergleich | Ergebnis ueber alle 1.763 Schritte |
| --- | --- |
| roh, Feld fuer Feld | erste Abweichung `factories[1]/bonus_chip/colors[0]`: `'schwarz'` gegen `'gelb'` (reproduziert das ROT) |
| Chip-Farblisten beidseits sortiert, aufwaerts-tolerant | **IDENTISCH** |
| alle Record-Felder ausser `state` und `game_id` | **alle gleich**: `policy`, `valid_actions`, `winner`, `scores`, `scores_unclamped`, `completed`, `moon_order_target`, `player` |

**Der Anker zieht Zug fuer Zug dasselbe.** Das ROT hat genau zwei Ursachen, beide ohne
Verhaltensbezug: die kanonisierte Schreibweise der Chip-Farben (unter `colors` UND unter
`unused_chip_colors`) und das Zustandsfeld `tiled_max_row`, das nach dem Einfrieren am 2026-09-12
dazugekommen ist und vom aufwaerts-toleranten Vergleich abgedeckt wird. Die Elo-Leiter ist
unberuehrt.

**Zwei Lehren aus der Diagnose selbst**, beides eigene Fehler im ersten Anlauf: ein Normalisierer,
der nur Felder namens `colors` sortiert, uebersieht `unused_chip_colors` -- Farblisten haengen
unter mehreren Schluesseln. Und eine Verhaltenspruefung, die ihre Felder aus einer Kandidatenliste
zieht, prueft, was sie zufaellig trifft: erst der Wechsel auf "alle Felder ausser `state`" hat
`valid_actions` und `winner` ueberhaupt in den Vergleich genommen.

### OFFENER NUTZER-ENTSCHEID: die Golden Probe des Ankers meldet ab jetzt dauerhaft ROT

Sie enthaelt Records der alten Schreibweise. Jede kuenftige Drift-Pruefung wird daran scheitern,
obwohl nichts driftet. Drei Wege:

* **(a) Der Pruefer normalisiert die Farblisten** auf beiden Seiten, wie die Diagnose-Sonde. Das
  Artefakt bleibt unangetastet, das Tor bleibt fuer alles andere scharf. **Empfehlung des
  Koordinators** -- mit dem Vorbehalt, dass jede Normalisierung in einem Waechter kuenftig echte
  Unterschiede schlucken kann; sie muesste eng auf Farblisten begrenzt sein und im Code begruendet
  stehen.
* **(b) Die Golden Probe neu erzeugen.** Sauber im Ergebnis, aber sie ist der eingefrorene
  Bezugspunkt: neu erzeugt kann sie Drift, die VOR heute entstanden ist, nicht mehr melden. Das
  widerspricht dem Zweck des Einfrierens.
* **(c) Nichts tun, ROT dokumentieren.** Abgeraten: das ist der Fall "ein umgangenes Tor erzieht
  zum Umgehen".

Bis zum Entscheid gilt: die Drift-Pruefung vom 2026-09-20 ist inhaltlich BESTANDEN, belegt durch
die Diagnose oben, nicht durch das Werkzeugverdikt.

## par.8f PRUEFUNG DER TESTS UND HAKEN (2026-09-19, Nutzer-Auftrag)

**Anlass:** Nutzer 2026-09-19, *"lass mal einen agent laufen ob alle tests und hooks so noch
notwendig sind. ich denk da faellt einiges raus."* Zwei Agenten, rein lesend (Erzeugung und
Cache-Waechter liefen, also kein `cargo`, kein Testlauf, keine Messung). **Nichts ausgefuehrt,
nichts geloescht** -- das hier ist eine Vorlage.

**Was davon der Koordinator SELBST nachgeprueft hat, ist unten je Zeile markiert.** Der Rest sind
Agenten-Befunde, also Behauptungen (Regel 0).

### Die vier Posten mit Verdikt RAUS oder nahe daran

| Posten | Pruefstelle | Befund | geprueft |
| --- | --- | --- | --- |
| `net_leaf_eval_matches_legacy_value_to_win_prob_when_w_is_zero` | `engine/src/net_mcts.rs:12253` | **laeuft leer gruen.** Z.12254 ist `let Some(net) = load_v18_legacy_test_net() else { return };`, und `models/alphazero_v18_best.onnx` gibt es nicht mehr. Dieselbe Zusicherung steht netzfrei in `blended_leaf_win_prob_with_w_zero_ignores_points_and_opp_entirely` (`:12291`) | **JA**, Code und fehlende Datei |
| Hilfsfunktion `load_v18_legacy_test_net` | `engine/src/net_mcts.rs:12237` | genau zwei Vorkommen im Baum: Definition und der Aufruf darueber | **JA** |
| `tools/hooks/python_dll_path.sh` | ganze Datei | **null Aufrufer.** `grep -c python_dll_path tools/hooks/pre-push` = 0, der Haken traegt die Herleitung inline (`pre-push:150-174`). Die vier Skripte, fuer die sie am 2026-09-06 extrahiert wurde, sind geloescht. Die Falle (`STATUS_DLL_NOT_FOUND`) bleibt durch die Inline-Kopie bewacht. `docs/tools_index.md:57` waere mitzuziehen | **JA** |
| `tools/tests/train_resume_pause_test.sh` | `:15-17` | **Fixtures tot:** `--load v23-b01_brierbest` -- `models/` traegt nur noch v29- und v30-Gewichte; die aus `data/window_v24.txt` gezogenen `selfplay_v23-b01-*.pkl` fehlen. Der Lauf braechte sofort ab. **NICHT einfach loeschen:** `train.py:2302` und `:2894` sowie `docs/working_rules.md:136` berufen sich auf seine Faelle D und E. Also neu verankern (v31-Fenster) oder ausdruecklich stilllegen | **JA**, beide Fixture-Klassen |

### Kandidaten, die einen Entscheid brauchen

| Posten | Pruefstelle | Warum Kandidat |
| --- | --- | --- |
| `engine/examples/`, sieben Sonden als BLOCK: `net_determinism`, `latency_2d_vs_flat`, `probe_input_shape`, `net_load_time_probe`, `profile_clones`, `eval_batch_size_numeric_probe`, `interleave_concurrency_probe` | Verzeichnis | **Der groesste Posten, und zwar wegen der Kosten:** der pre-push kompiliert `examples/` und `benches/` mit (CLAUDE.md, Abschnitt "Push scheitert am pre-push-Hook"). Keiner der sieben wird von einem Werkzeug oder einer OFFENEN Prereg gerufen. Mehrere sind auf eine tote Aera genagelt: `interleave_concurrency_probe.rs:25` und `net_2d_probe_two_input.rs:33` tragen `INPUT_SIZE = 708`, `net_load_time_probe.rs:15` und `profile_clones.rs:31` zeigen auf geloeschte Modelle. Ihre letzten Beruehrungen waren mechanische "Push-Blocker: examples nachgezogen"-Commits |
| `engine/examples/net_load_auto_backcompat.rs` | `:89-90` | beide geladenen Modelle (v17, v18) existieren nicht mehr, das Beispiel endet dann mit `exit(2)`. **Gegenlaeufig:** es ist der Nachweis der additiven Encoder-Regel, und die ist Architektur-Fixpunkt. Deshalb Entscheid, nicht RAUS |
| `engine/examples/net_2d_probe.rs`, `net_2d_probe_two_input.rs` | dort | Default-Modelle sind Wegwerf-Exporte aus Task #11 und liegen nicht im Baum |
| `tiling_cache_hit_rate_measurement` | `engine/src/tiling_solver.rs:3246` | laut eigenem Kopfkommentar (`:3243`) **kein Assert auf das Verhalten**, nur `plain_total >= 100` / `end_total >= 20`; trotzdem ohne `#[ignore]`, laeuft also in JEDEM pre-push mit 100 Rundenuebergaengen und 13 Suchen. Die Frage, die er beantworten sollte, ist entschieden. Er ist zugleich der einzige Aufrufer von `mcts::search_action`: loescht man ihn, wird produktiv toter Code sichtbar |
| sieben Tests des Inversions-Pfads | `engine/src/round_transition_resample.rs:354` ff. | der Code-Review nennt den Pfad Altlast, der Modulkopf (`:39-41`) sagt ausdruecklich "BLEIBEN". **Das ist ein Entscheid ueber den CODE, nicht ueber die Tests** -- sie fallen mit ihm oder gar nicht |
| `test_window_cache_key_planes_ablation.py::test_switch_off_keeps_the_legacy_key` | `tools/tests/test_window_cache_key_planes_ablation.py:88`, Literal in `:59` | der eingefrorene Schluessel wurde laut eigenem Kommentarblock in zwei Tagen DREIMAL absichtlich nachgezogen. Ein Stolperdraht, den man routinemaessig neu setzt, ist der Fall "Ein umgangenes Tor erzieht zum Umgehen" |
| `test_tiling_geometry_probe.py` | dort | neun Methoden auf eine Sonde zu einer ENTSCHIEDENEN Frage. **Einschraenkung:** `test_catalog_has_18_designs_with_4_cells` (`:126`) sichert eine SPIELREGEL und gehoert bei einem Schnitt erhalten -- Praezedenz ist par.8d Punkt 2, wo ein Komplettloeschen die Abdeckung einer lebenden Funktion mitgenommen haette |
| `engine/server_ai_test.py`, `engine/server_rust_test.py`, `engine/smoketest.py` | dort | **kein Laeufer**: der pre-commit sammelt nur `-s tools/tests -p "test_*.py"` ein. Seit 2026-06-26 nicht angefasst, dazwischen INPUT_SIZE 744 -> 888 und NUM_ACTIONS 406 -> 414. Entlastend: alle 15 von ihnen gerufenen Routen existieren noch in `server.py`. Ob sie gruen laufen, ist UNGEPRUEFT (Ausfuehrung war verboten) |
| Konventions-Regel 4, Teile `missing_from_index` und Abschnitts-Zaehler | `check_conventions.py:419-437` und `:487-502` | von der Byte-Gleichheits-Pruefung darueber logisch subsumiert: ist der Index byte-gleich mit dem Generat, koennen beide nicht mehr anschlagen. Ihr Nutzen ist heute nur die bessere Fehlermeldung. **Nicht** subsumiert ist `stale_in_index` (`:434`) |

### Was BLEIBT, und warum die Liste kurz ist

Die Gegenprobe war Auflage an beide Agenten: **ein Test, der eine in `docs/pitfalls.md`
beschriebene Falle bewacht, ist kein Loeschkandidat**, auch wenn er trivial aussieht. Das hat die
Liste stark gekuerzt. Namentlich in `pitfalls.md` gefunden und damit gesetzt:
`test_cache_key_feature_formula_version`, `test_cache_key_knobs_are_env_coupled`,
`test_cache_key_path_form`, `test_cache_overwrite_guard`, `test_name_path_cache_key_guard`,
`test_replayer_skips_diagnostic_lines`, `test_analyze_game_log_pass`, `test_train_manifest_flags`.
Dazu auf der Rust-Seite die beiden Anker-Fixture-Tests (`mcts.rs:1622`, `:1714`), der Vertragshash
(`lib.rs:2548`), die Netz-Paritaets-Fixture (`self_play.rs:8945`), die sechs Registratur-Waechter
(`knob_registry.rs:364` ff.) und die Additivitaets-Tests mit den Alt-Breiten 714/744/755/794/884
(`features.rs:2191`) -- letztere sind genau die Abwaertskompatibilitaet, die am 2026-09-19 drei
Spec-Feld-Loeschungen gestoppt hat (par.8d Punkt 7).

**Die Python-Seite ist sauber, was Gruppe A angeht.** 141 Testmethoden in 22 Dateien, gezaehlt mit
`grep -h "def test_" tools/tests/test_*.py | wc -l` -- dieselbe Zahl, die par.8d als gruen
registriert. Ein Test auf Entferntes waere rot gewesen oder beim Import gescheitert.
**Koordinator-Gegenprobe: JA**, Zahl selbst nachgezaehlt.

### Zwei Beifaenge, die nicht im Auftrag standen

**1. Der Waechter gegen leer-gruene Tests sieht die haeufigste Form nicht.** Regel 5
(`check_conventions.py:504-527`, Lauf `:579-613`) verlangt als Ausloeser `exists()`, `.is_err()`,
`let Ok(` oder "uebersprungen" und als Rueckgabe ein `return;` ALLEIN auf der Zeile (`:528`). Die
Form `let Some(x) = ... else { return };` faellt durch beide Raster -- und genau sie ist der
Posten oben. Der Anlassfall der Regel (17 leer-gruene Tests im Inventar 2026-08-15) ist damit
nicht geschlossen, sondern nur teilweise. **Koordinator-Gegenprobe: JA**, beide Muster gelesen.
Das ist kein Loeschgrund, sondern ein Nachbesserungsgrund.

**2. Eine Aussage in CLAUDE.md ist ueberholt.** Dort steht zum Prereg-Index: "waechst Zeile 1
darueber hinaus, faellt die Datei STILL aus dem Index". Das stimmt heute nicht mehr:
`tools/generate_prereg_index.py:162` gibt bei unparsebarem Kopf Exit 1 zurueck, und zwar BEVOR
`INDEX_PATH.write_text` (`:174`) erreicht wird -- der Generator schreibt dann gar nichts. Die
Falle ist also lauter geworden, als die Regel sie beschreibt. **Koordinator-Gegenprobe: JA**,
Quelltext gelesen. Aenderung an CLAUDE.md ist Nutzer-Entscheid.

### Eine Korrektur am Agenten-Befund

Der Python-Agent meldet fuer die Groessen-Ratsche (Regel 1) "**7 von 7** Dateien ueber der
Basislinie" und leitet daraus ab, sie habe ihren Anlass ueberlebt. **Der beobachtete Lauf zeigt
etwas anderes:** `python tools/check_conventions.py` am 2026-09-19 druckte genau ZWEI Warnungen,
fuer `engine/py/neural_net.py` und `tools/analyze_game_log.py`. Der Agent hat die Rohdifferenz
gegen `tools/size_baseline.json` gerechnet, aber die Reduktions-Ausnahme (`:186-190`, Vergleich
gegen `git cat-file -s HEAD:<datei>`) nicht nachgefahren und das selbst als ANNAHME markiert.
**NACHTRAG 2026-09-20, meine eigene Korrektur war zu kurz.** Der Commit-Haken derselben Nacht
druckte Regel-1-Warnungen fuer `train.py` und `engine/py/corpus_dataset.py` -- also fuer ZWEI
ANDERE Dateien als der volle Lauf. Direkt danach wiederholt: der volle Lauf
(`python tools/check_conventions.py`) meldet weiterhin genau `engine/py/neural_net.py` und
`tools/analyze_game_log.py`. Der Haken faehrt `--staged` und vergleicht die vorgemerkten Inhalte,
der volle Lauf vergleicht gegen die Blobgroesse in HEAD; **welche Dateien drucken, haengt also am
Modus**, und ueber beide Modi sind es mindestens vier verschiedene. Die Aussage "die tragende Zahl
ist 2" galt damit nur fuer einen der beiden Wege; naeher an der Sache ist der Agent mit seiner
Rohzaehlung von 7 ueber der Basislinie. **Der Mechanismus ist nicht aufgeloest** -- dazu muesste
man `:186-190` gegen beide Modi durchrechnen.

Der Kern des Arguments steht davon unberuehrt und ist am Regel-Kopf (`:15-26`) belegt: zehn
Ausloesungen, null Zerlegungen -- eine Warnung, die nie zu einer Handlung fuehrt, ist eine
Kandidatin. Sie ist kein Blocker und kostet 3,6 s im teuersten Modus. Dass sie je nach Modus
verschiedene Dateien nennt, ist ein Argument mehr: ein Waechter, dessen Ausgabe davon abhaengt,
wie man ihn ruft, erzieht niemanden.

### Was NICHT beurteilt ist

* **Die 707 `#[test]`-Attribute einzeln.** Gesucht wurde gezielt nach Bezuegen auf in Gruppe A
  Entferntes, nach Alt-Kontrakt-Zahlen (884/794/755/744/406/708), geloeschten Modell- und
  Ankerpfaden, `#[ignore]` und stillen Skips. **Inhaltliche Doppelabdeckung zwischen zwei
  verschieden benannten Tests ist damit NICHT systematisch erfasst** -- der eine gefundene Fall
  war ein Nebenprodukt. Zwei Namenskollisionen (`default_aus_liefert_ueberall_none` in
  `column_build.rs:1284` und `plate_builder.rs:1365`; `env_knoepfe_defaults_sind_bestandsverhalten`
  in `net_mcts.rs:7824` und `tiling_solver.rs:2634`) sind nicht Zeile fuer Zeile verglichen.
* **`engine/examples/planes_parity.rs`** taucht in keiner der beiden Listen auf, weder als
  Kandidat noch als BLEIBT. Luecke.
* **Jede Laufzeitangabe.** Keine ist in dieser Pruefung gemessen worden; alle stammen aus
  `tools/hooks/README.md` oder aus par.8d und sind dort datiert (die 97 s fuer `cargo test
  --release` vom 2026-08-26, also vor rund 140 zusaetzlichen Tests). **Welcher Test die Laufzeit
  dominiert, ist damit offen** -- und das ist die Zahl, die den Nutzen eines Schnitts an
  `examples/` und am Messtest erst beziffern wuerde. Sie kostet einen exklusiven `cargo`-Lauf.
* **Die Differenz 702 gegen 707** zwischen par.8d und der Attribut-Zaehlung: nicht aufgeloest
  (vier davon sind `ort_cuda_probe`-feature-gated).
* **Ob die drei Skripte unter `engine/` heute gruen laufen.** Nur ihre Routen sind gegengeprueft.

## par.8g DIE VIER RAUS-POSTEN AUSGEFUEHRT (2026-09-20)

**Nutzer-Auftrag:** *"loesch die vier raus-posten und halte alles in der aufraeum prereg fest,
damit wir hier nach abschluss gleich sauber machen koennen."* Ausgefuehrt waehrend der laufenden
v31-Erzeugung -- alle vier sind reine Loeschungen ohne Bau, es wurde keine Rechenlast erzeugt.

### Was entfernt wurde

| Posten | Art | Belegt in |
| --- | --- | --- |
| `net_leaf_eval_matches_legacy_value_to_win_prob_when_w_is_zero` samt Doc-Kommentar | Testfunktion, `net_mcts.rs` | par.8f: lief leer gruen, weil `alphazero_v18_best.onnx` nicht mehr im Baum liegt |
| `load_v18_legacy_test_net` samt Doc-Kommentar | Hilfsfunktion, `net_mcts.rs` | ihr einziger Aufrufer war die Zeile darueber |
| `tools/hooks/python_dll_path.sh` | Datei, `git rm` | null Aufrufer; `pre-push` traegt die Herleitung inline (Z.150-174) |
| `tools/tests/train_resume_pause_test.sh` | Datei, `git rm` | Fixtures tot: `v23-b01_brierbest` und der v23-Korpus sind geloescht |

**Kein Folgeschnitt:** `net::test_model_path_opt` behaelt seinen zweiten Aufrufer
(`net.rs:1096` in `test_model_path`), wird also nicht mit tot. Geprueft.

### Sieben Verweise nachgezogen, und das war der eigentliche Aufwand

Ein Loeschen ohne diesen Schritt haette sieben Stellen ins Leere zeigen lassen. Drei davon sind
Belegverweise, also kein Formalkram: sie waren die Begruendung dafuer, dass ein Default so steht,
wie er steht.

| Stelle | was sie sagte | was jetzt dort steht |
| --- | --- | --- |
| `net_mcts.rs:11670` | nennt den geloeschten Test als Muster-Vorbild | Verweis auf den Alt-Pfad-Nachweis aus Task #28 ohne Testnamen |
| `net_mcts.rs:12399` | zaehlt ihn unter den parallel laufenden Tests auf | Aufzaehlung gekuerzt |
| `train.py:2302` | "Testhaken (train_resume_pause_test.sh, Fall D)" | Testhaken ohne Treibernamen, Ergebnis-Verweis auf `working_rules.md` |
| `train.py:2894` (`--fast-loader`) | "Beleg: train_resume_pause_test.sh Fall E" | "Beleg: Fall E des Resume-Tests vom 2026-09-06, docs/working_rules.md" |
| `engine/py/corpus_dataset.py:2087` | dieselbe Bitidentitaets-Begruendung, Fall E | dito |
| `docs/working_rules.md:136` | Aufruf des Treibers als Anleitung | Treiber als entfallen markiert, das gruene Ergebnis A-E bleibt der Beleg, Hinweis auf Neuverankerung aus der Historie |
| `tools/hooks/README.md` | ganzer Abschnitt zur Bibliothek plus eine Nennung des Shell-Tests | beide durch Entfallen-Notizen ersetzt |
| `tools/restic_env.sh:6` | nennt die Bibliothek als Vorbild | Vorbild als entfallen markiert |

**Methodischer Nebenbefund, der wiederverwendbar ist:** drei dieser Stellen
(`corpus_dataset.py:2087`, `README.md:199`, `restic_env.sh:6`) standen in KEINER der beiden
Agentenlisten. Sichtbar geworden sind sie erst, als `tools/generate_tools_index.py` nach der
Loeschung neu lief. Der Index ist damit das bessere Instrument fuer die Frage "wer nennt diese
Datei" als ein Grep von Hand -- er trennt Aufruf von Erwaehnung und zaehlt beides. **Wer kuenftig
eine Datei loescht, laesst ihn danach laufen**, nicht nur davor.

### Was NICHT geprueft ist, und das ist wichtig

**Der Rust-Schnitt ist nicht uebersetzt.** `cargo test --release --no-run` waere Volllast neben
der laufenden Erzeugung und ist deshalb unterblieben. Der Schnitt sitzt an Klammergrenzen und die
verbliebene Datei ist gegengelesen, aber **belegt ist das erst durch einen Bau**. Vor dem
naechsten Push gehoert `cargo test --release --no-run` gefahren -- sonst faellt es im pre-push
auf, und zwar zusammen mit allem anderen, was dann ansteht.

Ebenfalls offen: `tools/hooks/README.md` nennt fuer die Python-Tests des pre-commit weiterhin
"rund 0,3 s" und drei Dateien; es sind heute 22 Dateien mit 141 Methoden (par.8f). Die
Laufzeitangabe ist damit unbelegt, aber ihre Berichtigung braucht eine Messung.

### NACH PROJEKTABSCHLUSS SOFORT ABARBEITEN

Die Reihenfolge ist nach steigendem Entscheidungsbedarf sortiert; die Belege stehen je in par.8f.
Jeder Block endet mit denselben Toren wie Gruppe A: `cargo test --release --no-run`, Lib-Tests,
Wheel mit unveraendertem Vertragshash, Netz-Paritaets-Fixture, **Anker-Drift gegen `hv4_anchor`**.

1. **`engine/examples/`, sieben Sonden als Block** (`net_determinism`, `latency_2d_vs_flat`,
   `probe_input_shape`, `net_load_time_probe`, `profile_clones`, `eval_batch_size_numeric_probe`,
   `interleave_concurrency_probe`). Groesster Posten, weil der pre-push sie bei JEDEM Push
   mitkompiliert. Kein Aufrufer, mehrere auf `INPUT_SIZE = 708` oder geloeschte Modelle genagelt.
   **Vorher klaeren:** `planes_parity.rs` ist in par.8f durch keine Liste abgedeckt, also
   mitbeurteilen statt stillschweigend stehen lassen.
2. **`net_2d_probe.rs` und `net_2d_probe_two_input.rs`** -- Default-Modelle sind Wegwerf-Exporte
   aus Task #11 und liegen nicht im Baum.
3. **`net_load_auto_backcompat.rs`** -- beide Modelle fehlen, das Beispiel endet mit `exit(2)`.
   Gegenlaeufig: es ist der Nachweis der additiven Encoder-Regel, und die ist Architektur-Fixpunkt.
   Entweder auf zwei LEBENDE Modelle umhaengen oder ausdruecklich aufgeben.
4. **`tiling_cache_hit_rate_measurement`** (`tiling_solver.rs`). Zwei Wege: `#[ignore]` setzen
   (billig, erhaelt die Messfaehigkeit) oder loeschen. **Beim Loeschen wird `mcts::search_action`
   als produktiv tot sichtbar** -- das ist dann ein eigener Punkt, kein Nebeneffekt.
5. **`test_window_cache_key_planes_ablation.py::test_switch_off_keeps_the_legacy_key`** -- der
   eingefrorene Schluessel wurde in zwei Tagen dreimal nachgezogen. Entweder der Stolperdraht
   wird ein echtes Tor (Aenderung nur mit Registrierung) oder er faellt.
6. **`test_tiling_geometry_probe.py`** -- neun Methoden auf eine ENTSCHIEDENE Frage. **Nicht
   komplett loeschen:** `test_catalog_has_18_designs_with_4_cells` (`:126`) sichert eine
   SPIELREGEL. Praezedenz par.8d Punkt 2.
7. **`engine/server_ai_test.py`, `server_rust_test.py`, `smoketest.py`** -- kein Laeufer, seit
   2026-06-26 unberuehrt, dazwischen zwei Kontraktwechsel. **Vorher einmal laufen lassen**: sind
   sie gruen, sind sie ein geschenkter E2E-Test und gehoeren in den pre-commit statt in den
   Papierkorb; sind sie rot, ist die Entscheidung leicht.
8. **Konventions-Regel 4**, Teile `missing_from_index` und Abschnitts-Zaehler -- von der
   Byte-Gleichheit logisch subsumiert, Nutzen nur noch die bessere Fehlermeldung. `stale_in_index`
   bleibt.
9. **Konventions-Regel 1 (Groessen-Ratsche)** -- zehn Ausloesungen, null Zerlegungen laut eigenem
   Kopf. Kein Blocker, 3,6 s. Entweder Schwelle hochsetzen oder abschaffen.
10. **`round_transition_resample`** (Code plus seine sieben Tests) -- der Code-Review nennt den
    Pfad Altlast, der Modulkopf sagt "BLEIBEN". **Entscheid ueber den CODE**, die Tests fallen mit
    ihm oder gar nicht.

### Zwei Punkte, die NICHT in diese Liste gehoeren, aber offen sind

* **Regel 5 sieht die haeufigste Form leer-gruener Tests nicht** (par.8f, Beifang 1). Das ist
  Nachbesserung, nicht Aufraeumen: der Ausloeser (`check_conventions.py:525-527`) und das
  Rueckgabemuster (`:528`) muessten die `let ... else { return }`-Form kennen. Vorher lohnt ein
  Inventar, wie viele solcher Stellen es heute gibt.
* **CLAUDE.md beschreibt den Prereg-Index-Generator ueberholt** (par.8f, Beifang 2): "faellt die
  Datei STILL aus dem Index" gilt nicht mehr, `generate_prereg_index.py:162` gibt Exit 1 vor dem
  Schreiben. Aenderung an CLAUDE.md ist Nutzer-Entscheid.

## par.8h QUALITAETS-DURCHSICHT (2026-09-21, `/simplify`, vier Winkel repo-weit)

**Nutzer-Auftrag:** `/simplify` auf die Aenderungen der v31-Promotion, dann auf Zuruf
(*"du kannst dem agent sagen dass er das ganze repo anschauen soll"*) auf den ganzen Baum.
Vier Agenten, je ein Winkel: Wiederverwendung, Vereinfachung, Effizienz, Flughoehe. Rein lesend,
keine Rechenlast. **Ein erster Anlauf am 2026-09-20 ist am Monatslimit gescheitert, nicht an der
Aufgabe.**

### BEHOBEN: ein Korrektheitsfehler, den ich selbst eingebaut hatte

**Der Cache-Schluessel des Tiling-Solvers durfte nicht ueber die Chips sortiert werden.** Am
2026-09-20 hatte ich `tiling_key` so erweitert, mit der Begruendung, Chips gleicher Farbmenge
seien austauschbar (`round_end::chip_sig`). Das gilt fuer den exakten Aufzaehlungsweg, aber NICHT
fuer den Deckel-Rueckfall: ab mehr als `CHIP_ALLOC_CAP` (14) Chips faellt `chip_allocations` auf
`greedy_chip_indices` zurueck (`round_end.rs:574`), und das waehlt `same[0]`, `same[1]` bzw.
`pool.iter().take(3)` in HANDINDEX-Reihenfolge. Zwei Haende mit derselben Chip-Multimenge in
anderer Reihenfolge verbrauchen dort verschiedene Chips und lassen einen verschiedenen Rest --
seit der Sortierung teilten sie sich einen Schluessel.

**Das Regime ist nicht theoretisch:** `referee.rs:791-795` haelt fest, dass der Rueckfall am
2026-08-26 in einem 24-Partien-Lauf auftrat und dort einen legalen Zug abwies. Der Fehler steckte
im Bundle, das am 2026-09-20 ausgeliefert wurde.

**Eine zweite Annahme fiel dabei mit.** Ich hatte angenommen, nach der Kanonisierung des Vorrats
koenne der Schluessel keine verdrehten Farblisten mehr sehen. `serialize::bonus_chip_from_json`
(`serialize.rs:999-1003`) uebernimmt die Farbliste aber WOERTLICH aus dem Record -- auf dem
JSON-Weg (`features.rs:654`, `lib.rs:1828`) kommen weiterhin unsortierte Chips an, aus Records von
vor dem 2026-09-20. Die Kanonisierung in `dome::build_bonus_chip_pool` deckt nur engine-gebaute
Zustaende ab, nicht rekonstruierte.

**Die Form, die beides loest, stand schon im Baum.** `TilingKey` fuehrt jetzt je Chip die
Farb-MENGE als Bitmaske ueber `round_end::chip_sig` (dafuer von `fn` auf `pub(crate)` gehoben,
kein Neubau), in HANDREIHENFOLGE:

* gegen die Reihenfolge INNERHALB eines Chips immun -- auch auf dem JSON-Weg,
* die Reihenfolge UEBER die Chips bleibt erhalten, der Greedy-Rueckfall ist wieder sauber,
* und es faellt je Chip eine Allokation WEG statt einer dazuzukommen (vorher
  `sort_by_cached_key` mit einem `Vec<u8>` je Chip).

**Tore:** `cargo test --release --no-run` gruen ohne Warnung, **701 Lib-Tests gruen** samt
Netz-Paritaets-Fixture (die Records aendern sich also nicht), Wheel neu gebaut,
**Anker-Drift GRUEN** ueber 1.763 Schritte, 147 Werkzeug-Tests gruen.

### BEHOBEN: vier weitere Stellen aus dem Diff

| Stelle | Was war | Was jetzt |
| --- | --- | --- |
| `README.md` zweimal | "today `v30-b02` and `v29-b09`" und `alphazero_v30-b02_brierbest.onnx` -- eine Generation zurueck, EINEN Tag nach dem Nachziehen der Champion-Zeile | auf `v31-b01` gezogen |
| `static/js/app.js::chipColors` | verglich gegen `String(a).toLowerCase()`, waehrend `CHIP_COLOR_ORDER` die Drahtform `'türkis'` fuehrte -- eine bereits ueber `normColor` normalisierte Farbe waere auf Position 99 sortiert worden | Schluessel sind die normalisierten Namen, Vergleich ueber `normColor` |
| `dist/mosaic_release.spec` | eigene Aufloesung Champion -> Verzeichnis: `.replace()` statt `endswith` (trifft das Muster ueberall im Namen), und `models/<name>.spec.json` war unbekannt -- der Bau waere abgebrochen, wo der Server laeuft | dieselbe Reihenfolge und dieselbe Suffix-Regel wie `server.py::_resolve_champion_spec` |
| `docs/architecture_reference.md` | kein Eintrag zu den zwei neuen Stellen, obwohl CLAUDE.md ihn ausdruecklich verlangt | zwei Zeilen mit beiden Pflichtfragen beantwortet |

Dazu in `tools/probes/generator_repro_probe.py`: `CHIP_COLOR_FIELDS` traegt jetzt sein
Verfallsdatum. Es ist **dauerhaft** noetig, nicht uebergangsweise -- am 2026-09-21 nachgezaehlt
sind `hv4_anchor/golden_probe/` (vorkanonisch, eingefroren solange Leitersegment 2 laeuft) und
`frozen_champions/v30-b02/` (traegt beide Schreibweisen) im Baum; `v31-b01` ist nachkanonisch.

### NICHT BEHOBEN, mit Grund

* **`greedy_chip_indices` ordnungsfrei machen** (`round_end.rs:509`) waere die tiefere Loesung --
  dann waere die Austauschbarkeits-Behauptung wahr statt ueberwiegend wahr. Es ist aber eine
  VERHALTENSAENDERUNG im Spielpfad und zieht Fixture, Golden Probes und Anker-Drift nach, fuer ein
  Regime, dessen Haeufigkeit ungemessen ist. Nach dem Schluss-Champion nicht mehr angemessen.
* **Farb-Bitmaske als Datentyp von `BonusChip`** statt `Vec<TileColor>`: waere die tiefste Form,
  aendert aber den Record- und GUI-Vertrag (`serialize.rs:219` zeigt `colors` als Namensliste) und
  damit wieder Fixture und Probes. Kein messbarer Gewinn, kein v32.
* **Die toten Testhaken in `train.py`** (`:2308`, `:2367`, Env `MOSAIC_PAUSE_TEST_STOP_AT_EPOCH`
  und `MOSAIC_RESUME_TEST_ABORT_AFTER_EPOCH`): ihr Treiber ist am 2026-09-20 geloescht. Sie zu
  entfernen wuerde die in par.8g registrierte Alternative "neu verankern" zunichtemachen -- das
  ist ein offener Entscheid, kein Aufraeumen.
* **Zwei der sechs neuen Tests** in `test_upward_tolerant_divergence.py` laufen laut Agent in
  denselben Zweig, und `test_canonicalisation_is_limited_to_two_fields` prueft kein Verhalten.
  Das stimmt -- und ist Absicht: der Test existiert, damit ein Erweitern der Zweierliste ein
  BEWUSSTER Akt wird und den Kopfkommentar zu lesen zwingt. Behalten.

### REPO-WEITE FUNDE -- Vorlage, nicht ausgefuehrt

Alle ausserhalb des Diffs, alle mit Pruefstelle belegt, sortiert nach Kosten. **Nichts davon ist
angefasst**; das waere weit ausserhalb dessen, was `/simplify` abdeckt.

1. **16 Sonden laden Korpusdateien mit rohem `pickle.load`** statt ueber `corpus_io.load_records`
   (`corpus_io.py:47`), obwohl Korpora seit `dump_records(..., compress=True)` gzip sind. Zwei
   davon schlucken die Ausnahme und melden STILL ein leeres Ergebnis
   (`tools/probes/bootstrap_horizon_cost_gate.py:91`, `conjunction_base_rates.py:72`). Drei
   Fehlerpolitiken nebeneinander. **Der teuerste Fund.**
2. **72 Werkzeuge schreiben den `laufzeit`-Pflichtblock von Hand**, 6 nehmen den Helfer
   `tools/runtime_block.py:43`. Schon auseinandergelaufen: 25 Stellen rechnen auf `time.time()`,
   14 auf `time.monotonic()`; drei lassen `cpu_s`/`threads`/`s_je_partie` ganz weg.
3. **Blockmittel viermal mit drei verschiedenen Rest-Regeln** (`plate_points_from_arena.py:198`
   zaehlt den angebrochenen Block ab halber Groesse mit, `env_ab_swap_eval.py:60` immer,
   `arena_block_sd_probe.py:27` nie). Daran haengt laut CLAUDE.md die Entscheidungsmetrik JEDER
   Arena-Auswertung.
4. **Der exakte zweiseitige Binomialtest 15-mal gebaut**, unter zwei Namen (`mcnemar_exact_p`,
   `sign_test_p`). Es gibt kein Statistik-Modul in `tools/`.
5. **Die CPU-Warteschleife fuenfmal**, eine Kopie defekt: `tools/night_v31_generate.sh:55`
   verundet `[c]argo|[m]aturin` mit `Name -match 'python'` -- ein `cargo.exe` wird damit NIE
   gesehen, obwohl ein Build laut CLAUDE.md Messlast ist. `night_v31_chain.sh:68` hat genau
   dafuer den Zusatz `-or Name -match '^(cargo|rustc)'`; die Erzeugungskette hat ihn nicht.
6. **`_SPEC_TO_ENV` zweimal byte-gleich** (`server.py:205`, `tools/claude_play.py:80`) und beide
   12 Felder hinter `net_mcts.rs::KNOWN_FIELDS`. Die aktuelle Champion-Spec traegt davon
   `heuristik_variante` -- das Feld wird beim GUI-Laden still uebergangen.
7. **Der `_TEST_`-Ausnahme des Knopf-Waechters** (`knob_registry.rs:294`) ist ein Substring-Test,
   gemeint war das Praefix `MOSAIC_TEST_`. Dadurch rutschen zwei echte Laufzeit-Knoepfe an beiden
   Waechtern vorbei (`MOSAIC_PAUSE_TEST_STOP_AT_EPOCH`, `MOSAIC_RESUME_TEST_ABORT_AFTER_EPOCH`).
8. **Werkzeug-Defaults auf geloeschte Modelle**: `r4b_zone_probe.py:44`, `r5_value_calibration.py:338`,
   `plate_rank_invariance.py:176`, `play_rule_cost.py:122`, `chance_node_pretest.py:119`,
   `gpu_batch_throughput.py:99` und zwei `engine/examples`. Alle scheitern laut; es ist der
   registrierte Grund, warum Punkt 5 der Promotionsliste seit v24-b06 nicht mehr laeuft.
9. **`tiling_solver::apply_step` klont je Schritt den ganzen `GameState`**, obwohl der Solver nur
   `players[pi]` liest -- rund 110 Heap-Allokationen je Klon, davon rund 75 Prozent tot
   (HERLEITUNG des Agenten, nicht gemessen). Der Modul-Kommentar `:248-255` belegt die
   Feld-Abhaengigkeit selbst.
10. **`features.rs:1383` gegen `:1635`**: Abschnitt 5 und Abschnitt 17 fahren je Blatt und Spieler
    DIESELBE Tiling-Rekursion zweimal; `tiling_solver.rs:563` sagt selbst, die Punkte seien
    identisch. Vier Rekursionen je Blatt, zwei davon ableitbar.

### EIN OFFENER BEFUND HAT EINE HYPOTHESE MIT PRUEFWEG BEKOMMEN

Der ungeklaerte Kostenbefund der v31-Erzeugung (Sockel je Zug 10,7 Prozent BILLIGER, beide
Schwarm-Klassen 13,7 und 18,4 Prozent TEURER, bei identischer Partielaenge -- `docs/measured_runtimes.md`,
Abschnitt "Generation v31") hat jetzt einen benannten Kanal:

**Die drei Tiling-Caches sind fadenlokal, ihr Schluessel ist ALLEIN das Spielerbrett
(`tiling_solver.rs:294-303`), und bei Ueberlauf von `CACHE_CAP = 20_000` werden sie GANZ geleert
(`:437-443`).** Die Kosten eines Zuges haengen damit nicht an der Zugzahl, sondern an der
VIELFALT der Brettzustaende, die eine Klasse erzeugt. Der Sockel faehrt `--tau-argmax-from-move 1`
(engste Verteilung, hoechste Trefferquote), die temperierte Klasse sampelt, die Ausflug-Klasse
erzwingt eine Abweichung. Das passt in der RICHTUNG auf das beobachtete Vorzeichen. Dazu kommt,
dass `--return-order-random-p 0.81` in v30 wirkungslos war und erst am 2026-09-19 in den
Knoten-Weg gezogen wurde -- eine zufaellige Rueckgabereihenfolge streut genau die Groesse, ueber
die der Schluessel laeuft.

**Beantwortbar OHNE eine einzige Partie:** `MOSAIC_TILING_CACHE_STATS=1` (`tiling_solver.rs:389-393`)
zaehlt Schluessel-Wiederkehr; ein kurzer Lauf je Klasse liefert Trefferquote und Zahl der
Voll-Leerungen. Das ist billiger als die bisher vorgeschlagene Knotenzahl-Sonde und trifft eine
ANDERE Vermutung -- beide bleiben offen. **HYPOTHESE, nicht Befund.**

### NACHTRAG 2026-09-21: die fehlerhafte Fassung ist AUSGELIEFERT

Nutzer: *"die zip mit dem fehlerhaften cache schluessel ist schon draussen. da koennen wir nur
eine neue version machen."* `Mosaic-AI_v1.0-alpha31.zip` war weitergegeben, bevor der Fehler im
Tiling-Cache-Schluessel auffiel. Zurueckholen geht nicht; der Weg ist eine neue Version.

**Was der Empfaenger konkret hat:** einen Cache-Schluessel, der zwei Haende mit derselben
Chip-Multimenge in anderer Reihenfolge zusammenwirft. Wirksam wird das erst ab mehr als
`CHIP_ALLOC_CAP` (14) gehaltenen Chips, wo `chip_allocations` auf `greedy_chip_indices`
zurueckfaellt; darunter ist die Aufzaehlung exakt und ordnungsfrei, der Schluessel also korrekt.
Die Haeufigkeit dieses Regimes ist UNGEMESSEN -- belegt ist nur, dass es vorkommt
(`referee.rs:791-795`, 24-Partien-Lauf am 2026-08-26). Es ist ein Fehler in der Memoisierung,
nicht in der Spielregel: betroffen ist, welches Tiling-Ergebnis aus dem Cache kommt, nicht
welche Zuege legal sind.

**Folge fuer die Benennung, und sie hat meine eigene Entscheidung von vorhin umgedreht.** Beim
Einbau des Schemas hatte ich das Ueberschreiben-in-place als Vorzug begruendet: gleiche Version
plus gleiche Generation soll dieselbe Datei sein. Sobald eine Fassung DRAUSSEN ist, ist das
falsch herum -- dann zirkulieren zwei Binaerstaende unter einem Namen. Dazu kam ein Schnitzer:
die Version wurde hart auf zwei Stellen gekuerzt, `1.0.0` und `1.0.1` haetten denselben
Dateinamen ergeben. Berichtigt (`tools/build_release.py::release_name`): ein abschliessendes
`.0` faellt weg, jede andere Stelle bleibt stehen. `1.0.1` ergibt jetzt
`Mosaic-AI_v1.0.1-alpha31.zip`.

**Die naechste Auslieferung kommt nach dem Aufraeumen** (Nutzer: *"aber da warten wir noch bis
du aufgeraeumt hast"*) und braucht einen Versionssprung in `engine/pyproject.toml` UND
`engine/Cargo.toml` -- beide, das ist die Falle vom 2026-09-20 (maturin liest pyproject, der
Rust-Code `CARGO_PKG_VERSION`).

### AUFRAEUMEN, ERSTER DURCHGANG (2026-09-21)

**Anlass fuer die Reihenfolge:** Nutzer *"vielleicht wird das projekt weitergehen. nur nicht
jetzt."* Das dreht die Bewertung aus par.8h um. Ich hatte die Konsolidierungs-Posten (76
Laufzeit-Bloecke, 15 Binomialtests) als Hygiene fuer eine Codebasis abgetan, die nicht
weiterentwickelt wird -- bei einer moeglichen Wiederaufnahme ist das falsch. Sortiert wird jetzt
danach, **was eine wiederaufnehmende Sitzung STILL in die Irre fuehrt**, nicht nach Doppelung.

| Rang | Punkt | Ergebnis |
| --- | --- | --- |
| 1 | Blockmittel, drei Rest-Regeln | **vereinheitlicht** in `tools/block_stats.py`, drei Aufrufer umgehaengt, 12 Waechter-Tests |
| 2 | zwei Sonden melden bei gzip still ein leeres Ergebnis | **behoben**: `corpus_io.load_records` statt rohem `pickle.load`, dazu ein Riegel gegen den Nullfall |
| 3 | `knob_registry` `_TEST_`-Substring | **behoben**: Praefix statt Substring; vier Knopfnamen nachgezogen |
| 4 | Regel 5 sieht `let ... else { return }` nicht | **behoben**: beide Haelften erweitert, Scan auf den Testteil begrenzt, 14 Waechter-Tests |

**Zu Rang 1, und es korrigiert meine eigene Rangfolge:** ich hatte den Punkt an die Spitze
gesetzt, weil ich ihn fuer wirksam hielt. Er ist es nicht. **Gemessen, bevor angefasst wurde:**
von allen Gating-Artefakten hat genau EINES einen Rest bei Blockgroesse 5, ein Rauchtest mit
n = 2. Der Grund ist strukturell -- `paired_gating` wertet je Block aus und stoppt darum immer auf
einer Blockgrenze. Keine registrierte Zahl haengt daran, die Vereinheitlichung aendert keine. Das
machte sie zugleich KOSTENLOS. Die kanonische Regel ist die von `plate_points_from_arena`, weil sie
als einzige begruendet war (ein 1-Partie-Rest waere ein Datenpunkt mit der Streuung einer
Einzelpartie). Praezisierung zum Agentenbefund: `corpus_behaviour_audit.blocks` ist KEINE vierte
Kopie, sondern ein reiner Zerteiler (`-> list[list]`) -- es waren drei, nicht vier.

**Zu Rang 2:** die beiden Sonden schwiegen nicht ganz, sie druckten je Datei eine
Ueberspringen-Zeile. Der Schaden war ein anderer: der Lauf lief DURCH und berichtete ueber nichts.
Beide haben jetzt zusaetzlich einen harten Riegel -- ein Bericht ueber eine leere Grundmenge ist
schlechter als kein Bericht.

**Zu Rang 3:** der Kommentar der Regel sagte "Praefix `MOSAIC_TEST_`", der Code pruefte
`contains("_TEST_")`. Zwei echte Laufzeit-Knoepfe in `train.py` rutschten dadurch an BEIDEN
Waechtern vorbei. Statt sie nachzuregistrieren tragen sie jetzt das Praefix, das ihre Natur
benennt: `MOSAIC_TEST_PAUSE_STOP_AT_EPOCH`, `MOSAIC_TEST_RESUME_ABORT_AFTER_EPOCH`. **Der
geschaerfte Waechter hat daraufhin sofort zwei weitere gefunden** -- die synthetischen
`MOSAIC_*_TEST_UNSET_XYZ` in `net_batcher.rs` und `net_ort.rs` trugen `_TEST_` ebenfalls als
Infix; auch sie sind umbenannt. Genau dafuer ist ein Waechter da.

**Zu Rang 4, mit einem eigenen Fehler auf dem Weg:** meine erste Reparatur hat nur das
RUECKGABEMUSTER erweitert. Der Anlassfall waere trotzdem durchgerutscht, weil der AUSLOESER
`let Some(` gar nicht kannte -- aufgefallen ist das nur, weil ich die Regel gegen den konkreten
Fall geprueft habe statt gegen ihre Abwesenheit von Warnungen. Dazu ein zweiter Schnitzer: ein
`\b` in einem nicht-rohen Generierstring wurde als literales BACKSPACE-Zeichen in die Datei
geschrieben, im Rohtext unsichtbar und im Regex wirkungslos (`cat -A` zeigte `mod tests^H`).
Beides behoben; der Scan laeuft jetzt nur noch im Testteil, damit die Regel nicht laenger bittet,
ihre eigenen Treffer zu ignorieren.

**Tore des Durchgangs:** 171 Werkzeug-Tests gruen (147 + 12 + 14, minus zwei zusammengelegte),
**701 Lib-Tests gruen**, Wheel neu, Vertragshash `6ef829e564c58bd5` unveraendert,
**Anker-Drift GRUEN** ueber 1.763 Schritte, Konventions-Check gruen ohne Fehlalarm.

**Offen bleiben** die Posten 1 (die uebrigen 21 rohen Korpus-Leser), 2, 4, 5, 6, 8, 9, 10 aus
par.8h sowie die zehn Punkte aus par.8g. Aufwandsschaetzung dafuer, mit heute gemessenen
Torkosten (rund 10 min je Rust-Buendel): **rund 15 h**, davon der groesste Einzelposten die 76
handgeschriebenen Laufzeit-Bloecke.

## par.8i DIE ZEHN PUNKTE AUS par.8g, ALS EIN BUENDEL (2026-09-21)

**Nutzer-Auftrag:** *"mach weiter mit par.8g als buendel"* -- als EIN Rust-Buendel, damit der
Torlauf (rund 10 min, heute gemessen) einmal statt zehnmal anfaellt.

**Drei der zehn Punkte haben die Pruefung nicht ueberstanden**, und das ist das wichtigere
Ergebnis des Durchgangs: eine Vorlage aus einer Durchsicht ist eine Behauptung, kein Auftrag.

| Punkt | Ergebnis |
| --- | --- |
| 1-3 `engine/examples/` | **9 von 11 entfernt** (15 Dateien -> 6), aber nicht die vorgeschlagene Auswahl |
| 4 `tiling_cache_hit_rate_measurement` | **`#[ignore]` mit Grund**, nicht geloescht |
| 5 Stolperdraht Fenster-Schluessel | **BLEIBT**, nur die Chronik im Kommentar gekuerzt |
| 6 `test_tiling_geometry_probe.py` | **ABGELEHNT** -- die Sonde lebt |
| 7 `engine/*.py` E2E-Skripte | drei gefahren, **alle rot** -> entfernt |
| 8 Konventions-Regel 4, zwei Teile | **ABGELEHNT** -- der Nutzen IST die bessere Fehlermeldung |
| 9 Konventions-Regel 1 | Basislinie nachgezogen, die Ratsche meldet wieder nur NEUES Wachstum |
| 10 `round_transition_resample` | Nutzer-Entscheid ueber den CODE -- offen, unberuehrt |

### Was ein Blockschnitt mitgenommen haette

**`planes_parity.rs` stand in KEINER der beiden Listen** und waere als Teil des Blocks gefallen --
par.8g Punkt 1 verlangte ausdruecklich, es mitzubeurteilen. Es hat zwei lebende Stellen, die es
als Referenzroute nennen (`engine/py/neural_net.py:167`, `tools/probes/feature_parity_rust_python.py:23`).
Bleibt.

**`profile_clones.rs` war IN dem Block und bleibt trotzdem.**
`evaluations/review/code_review_2026-09-11_search.md` fuehrt es als Instrument zu einer OFFENEN
Optimierungsfrage (`note_gamestate_clone()`), und genau die ist am 2026-09-21 als Fund 9 in par.8h
wieder aufgetaucht (`GameState`-Klone je Solver-Schritt). Ein Werkzeug loeschen, dessen Frage
offen ist, waere verkehrt herum.

**Entfernt sind damit neun:** `net_determinism`, `latency_2d_vs_flat`, `probe_input_shape`,
`net_load_time_probe`, `interleave_concurrency_probe`, `eval_batch_size_numeric_probe`,
`net_2d_probe`, `net_2d_probe_two_input`, `net_load_auto_backcompat`. Jeder Name ist vor dem
Schnitt ueber `*.py`, `*.sh`, `*.md`, `*.toml` gesucht worden: ausserhalb von `engine/examples/`
und dieser Prereg wird keiner genannt. Einen Cargo-Eintrag hat nur `ort_cuda_batch_probe`
(feature-gated), die uebrigen sind implizit -- die Datei zu loeschen genuegt.

**Zu `net_load_auto_backcompat` im Besonderen**, weil par.8g Punkt 3 es an einen
Architektur-Fixpunkt band: die additive Encoder-Regel wird NICHT von diesem Beispiel getragen,
sondern von den Tests in `features.rs:2191-2208` mit den Alt-Breiten `LEN_BEFORE_*`
(714/744/755/794/884). Das Beispiel konnte seine Aufgabe ohnehin nicht mehr erfuellen -- beide
Modelle, die es laedt (v17, v18), sind geloescht, es endete mit `exit(2)`. Die dritte Option
neben "umhaengen" und "aufgeben" war also, dass die Aufgabe laengst woanders erfuellt ist.

### Punkt 4: fast falsch herum gelaufen

`tiling_cache_hit_rate_measurement` traegt kein Assert auf Verhalten und lief in JEDEM
`cargo test` mit. Loeschen waere trotzdem doppelt verkehrt gewesen: er ist der einzige Aufrufer
von `mcts::search_action` (dessen Tod damit sichtbar wuerde -- ein eigener Entscheid, wie par.8g
Punkt 4 selbst festhaelt), UND er ist das Instrument fuer die Cache-Vielfalt-Hypothese aus par.8h.
`#[ignore]` mit Begruendung im Attribut nimmt die Kosten je Push, ohne beides zu verlieren; ein
ignorierter Test kompiliert weiter und verfaellt darum nicht still.

### Punkt 5: der Waechter hat gehalten, gewuchert ist die Chronik

Der Befund lautete, der eingefrorene Schluessel sei "in zwei Tagen dreimal nachgezogen" worden und
damit ein umgangenes Tor. **Am Bestand stimmt das nicht.** Der Kommentar verlangt ausdruecklich,
das duerfe nur absichtlich und mit Eintrag in der Prereg geschehen, und alle drei Bewegungen sind
genau so dokumentiert, mit Grund und Verweis (`PREREG_rust_data_layer` par.9a/9b,
`PREREG_round_transition_search_sampling` par.18, `PREREG_dome_return_order` par.12.6-12.10). Ein
Tor, das dreimal ausgeloest und dreimal bewusst passiert wurde, hat getan, wozu es da ist. Der
Test bleibt unveraendert. Gekuerzt ist allein der Kommentarblock, der auf 18 Zeilen Verlauf
angewachsen war -- dieselbe Bauform, die CLAUDE.md beim Prereg-Statuskopf abgeschafft hat.

### Punkt 6 und 8: abgelehnt, mit Grund

**Punkt 6:** `tools/probes/tiling_geometry_probe.py` lebt -- `docs/tools_index.md:103` fuehrt sie
mit zwei Aufrufern. Neun Tests, die lebenden Code decken und zusammen unter einer Sekunde laufen,
zu loeschen waere genau der Fehler aus par.8d Punkt 2, wo ein Komplettschnitt die Abdeckung einer
lebenden Funktion mitgenommen haette. Die Vorlage nannte diese Praezedenz selbst und zog dann den
halben Schluss daraus.

**Punkt 8:** die Teile `missing_from_index` und der Abschnitts-Zaehler sind von der
Byte-Gleichheit logisch gedeckt; ihr verbleibender Nutzen ist die PRAEZISERE Fehlermeldung. Sie
kosten nur Zeilen, nie Laufzeit an einem gruenen Lauf. Fuer eine moeglicherweise wiederaufnehmende
Sitzung (Nutzer: *"vielleicht wird das projekt weitergehen"*) ist eine Meldung, die sagt WAS
fehlt, mehr wert als ein Dutzend gesparte Zeilen.

### Punkt 7: rot -- und der Grund ist der eigentliche Befund

`engine/smoketest.py`, `server_rust_test.py`, `server_ai_test.py` einmal gefahren, wie die Vorlage
es verlangte (Flask-Testclient, kein laufender Server noetig). **Alle drei scheitern**, und zwar
aussagekraeftig: zwei brechen mit *"Passen nicht erlaubt - es gibt noch gueltige Aktionen"* ab,
der dritte mit *"Spiel noch nicht beendet"*. Ursache ist ihre eigene Zugwahl, die den seit v30
gewachsenen Aktionsraum nicht kennt (Mondstapel 406-410, Rueckgabe 411-413, Slot und Rotation als
eigene Knoten). **Kein Server-Defekt** -- dieselben Routen tragen die Mensch-Partien und sind am
2026-09-20 am laufenden Bild geprueft.

Entfernt nach der in par.8g registrierten Regel ("sind sie rot, ist die Entscheidung leicht").

**Was dadurch ungedeckt bleibt, und das gehoert benannt statt hingenommen:** die HTTP-Routen von
`server.py` haben jetzt KEINE automatische E2E-Abdeckung mehr. Der Ersatz ist unvollstaendig --
`tools/claude_play.py` treibt dieselbe Engine ueber die Kommandozeile, nicht ueber die Routen; die
Routen selbst belegen nur noch echte Mensch-Partien. Wer die Skripte wieder aufbaut, muss ihre
Zugwahl um die vier neuen Knotentypen erweitern; der Rest ihres Aufbaus (Flask-Testclient,
vollstaendige Partie ohne Server) war tragfaehig und ist in der Historie nachlesbar.

### Punkt 9

Die Groessen-Basislinie war 119 Dateien hinterher, darum loeste die Ratsche bei jedem Lauf aus,
ohne je eine Zerlegung ausgeloest zu haben. Nachgezogen statt abgeschafft: sie meldet damit wieder
nur NEUES Wachstum, und das ist die Eigenschaft, um derentwillen sie gebaut wurde.

### Tore des Buendels (alle gruen)

| Tor | Ergebnis |
| --- | --- |
| `cargo test --release --no-run` | gruen, **1:00 min** (vorher 1:26 -- der Gewinn aus den neun entfernten Beispielen) |
| Lib-Suite | **700 gruen, 0 rot, 20 ignoriert** (19 + der neue `#[ignore]`), 99,3 s |
| Netz-Paritaets-Fixture | gruen (in der Suite) |
| Wheel | neu gebaut, 32,4 s; Vertragshash `6ef829e564c58bd5`, `input_size` 888, `num_actions` 414, `engine_version` 1.0.0 -- unveraendert |
| **Anker-Drift gegen `hv4_anchor`** | **GRUEN**, 1.763 Schritte Feld fuer Feld gleich |
| Werkzeug-Tests | **171 gruen**, 1,2 s |
| Konventions-Check | gruen, ohne Fehlalarm |

Die Lib-Suite steht bei 700 statt 701, weil der Messtest aus Punkt 4 jetzt ignoriert wird; es ist
kein Test verloren gegangen.

### Was aus par.8g offen bleibt

Nur **Punkt 10** (`round_transition_resample`), und der ist unveraendert ein Entscheid ueber den
CODE: der Code-Review nennt den Pfad Altlast, der Modulkopf sagt "BLEIBEN". Die sieben Tests
fallen mit ihm oder gar nicht -- sie einzeln anzufassen waere die falsche Reihenfolge.

Die uebrigen offenen Posten stehen unveraendert in par.8h (Punkte 1, 2, 4, 5, 6, 8, 9, 10),
Aufwand dafuer weiterhin rund 15 h.

## par.8j RESTLISTE par.8h, BUENDEL 1: die drei stillen Posten (2026-09-21)

**Nutzer-Auftrag:** *"mach weiter mit den restlichen punkten aus par.8h"*. Zuerst die drei, die
nicht doppelt sind, sondern FALSCH: Punkte 5, 6 und 8. Rein auf der Python- und Shell-Seite, also
ohne Rust-Torlauf.

**Zwei der drei Befunde des Agenten waren im Detail unzutreffend**, und beide Male lag der
tatsaechliche Sachverhalt daneben, nicht nur die Zeilenangabe. Das ist der Grund, warum REGEL 0
auch fuer eine sorgfaeltige Durchsicht gilt.

### Punkt 5: die defekte Warteschleife, mit Gegenprobe statt Behauptung

Fuenf Kopien, vier Bauformen, eine davon defekt -- das stimmte. `tools/night_v31_generate.sh:55`
verundete `[c]argo|[m]aturin` in der Kommandozeile mit `Name -match 'python'`; ein `cargo.exe`
heisst nicht `python.exe`, die Kopie konnte einen laufenden Build also nie sehen. Genau an der
Stelle, an der CLAUDE.md sagt, dass ein Build Messlast ist.

**Gemessen, nicht behauptet:** bei laufendem `cargo test --release --no-run` zaehlt der
gehaertete Filter **3** Prozesse (cargo plus rustc), der alte **0**. Die Erzeugungskette haette in
diesem Moment eine Messung gestartet.

Alle fuenf haengen jetzt an `tools/lib/cpu_free.sh`. Die drei Haertungen dort stammen je aus
einem Vorfall: der Klammer-Trick gegen das Warten auf sich selbst, Cargo/rustc/maturin am
PROZESSNAMEN statt in der Kommandozeile, und eine unlesbare Antwort gilt als BELEGT. Die
Bezeichner sind bei der Gelegenheit englisch geworden (`cpu_busy_count`, `cpu_is_free`,
`wait_for_free_cpu`), wie es die Konvention seit 2026-08-24 verlangt.

### Punkt 6: schaerfer als registriert -- und trotzdem keine falsche Zahl

Registriert war: zwei byte-gleiche Kopien von `_SPEC_TO_ENV`, beide zwoelf Felder hinter
`net_mcts.rs::KNOWN_FIELDS`, und *"die aktuelle Champion-Spec traegt davon `heuristik_variante`
-- das Feld wird beim GUI-Laden still uebergangen"*.

**Der Beispielfall war der falsche.** `heuristik_variante` fehlt ABSICHTLICH: es waehlt die
Variante der netzlosen Gegenseite, ist kein Suchknopf des Netzes, und `oracle_metrics`
protokolliert es seit je als ignoriertes Feld. Die zwoelf Fehlenden zerfallen in acht solche
(sechs Erzeugungs-Stilmittel plus `heuristik_variante`) und **fuenf echte Suchknoepfe mit
eigenem Env-Namen**: `special_unlock_w`, `special_unlock_beta`, `moon_order_search_scale`,
`round_transition_leaf`, `net_tiling_tiebreak`.

**Die Rueckwaerts-Pruefung war hier Pflicht, und sie faellt gut aus.** Im Baum liegen neun
A/B-Specs, die genau diese Felder tragen (`tiebreak_off/on`, `rt_leaf_off/on`,
`moon_order_scale0/1`, `k6_off/w025/w050`). Alle neun sind ueber `paired_gating` gemessen worden,
also ueber den RUST-Leser, der alle 32 Felder kennt; und die vier registrierten
`oracle_metrics`-Laeufe nennen als ignoriertes Feld ausschliesslich `heuristik_variante`. **Keine
registrierte Zahl haengt daran.** Es war eine geladene, keine abgefeuerte Waffe.

**Wo sie geladen war, ist der Punkt:** `oracle_metrics` faehrt A/B als ZWEI Laeufe mit
verschiedenen `--spec`-Dateien. Waere eine der neun durch dieses Werkzeug gegangen, haette es
zwei IDENTISCHE Arme gemessen -- und an den Zahlen waere das nicht zu sehen gewesen.

Die Abbildung steht jetzt einmal in `spec_env.py` (Wurzelverzeichnis wie `corpus_io.py`, weil
`server.py` sie importiert und PyInstaller ueber `pathex=[PROJECT_ROOT]` laeuft: ein Modul unter
`tools/` waere im portablen Bundle nicht gelandet). Die fuenf Knoepfe sind nachgetragen, die acht
Ausnahmen tragen je einen GRUND im Code, und alle drei Aufrufer melden ein Feld ohne Knopf jetzt
laut -- `oracle_metrics` bricht sogar ab, weil dort ein stilles Ueberspringen die Messung
entwertet.

**Der eigentliche Schutz ist `tools/tests/test_spec_env.py`** (16 Tests): er liest `KNOWN_FIELDS`
aus dem Rust-Quelltext und verlangt fuer JEDES Feld eine Entscheidung -- abgebildet oder mit
Grund ausgenommen. Dazu die Gegenrichtung (kein erfundener Env-Name), ein Abgleich gegen
`knob_registry.rs` (ein Tippfehler setzt sonst eine Variable, die niemand liest) und die Probe
aufs Exempel ueber alle `models/*.spec.json`. Ein neues Spec-Feld in Rust zwingt damit zu einer
Entscheidung auf der Python-Seite, statt still zwoelf anwachsen zu lassen.

### Punkt 8: die Pfade stimmten nicht, und ein Posten war gar kein Default

Die sechs Werkzeuge liegen in `tools/`, nicht in `tools/probes/` wie registriert. Bestaetigt ist
der Kern: fuenf Modelle und ein Korpus-Glob zeigen ins Leere
(`alphazero_v16/v17/v18_best`, `v19_2d_best`, `v21_2d_brierbest`, `data/selfplay_v16_*.pkl`),
dazu die drei Checkpoints in `--models` von `r5_value_calibration`.

Behandelt wurde aber nicht alles gleich, weil sie nicht dasselbe sind:

* **Vier Werkzeuge** (`plate_rank_invariance`, `play_rule_cost`, `chance_node_pretest`,
  `gpu_batch_throughput`) und `--models` von `r5_value_calibration`: Default weg, Flag
  `required`. Das gewaehlte Netz IST die Substanz der Messung; ein Default, der nicht existiert,
  ist keine Bequemlichkeit, sondern eine Falschauskunft.
* **`r5_value_calibration --model-path-for-api`** ist der Gegenfall: die Moduldoku sagt selbst,
  der Inhalt werde fuer Runde-5-Zustaende nie benutzt (`round5.rs`-Kurzschluss), gebraucht werde
  nur ein LADBARER ONNX-Pfad. Dort ist ein mitwandernder Default richtig -- jetzt der amtierende
  Champion aus `models/champion.txt`.
* **`r4b_zone_probe` ist gar kein Default.** `MODEL_KEY` ist zugleich Schluessel in
  `r4b_value_calibration_v20_n72.json`, wo die Referenzwerte je Zustand fuer GENAU dieses Netz
  liegen. Ein anderes Modell einzutragen waere kein Ersatz, sondern ein Messfehler. Die Sonde
  bekommt darum einen frueh ausloesenden Riegel, der das benennt, statt einen Traceback aus
  `torch.load` zu liefern -- und verweist auf den offenen Nutzer-Entscheid, ob sie gezogen wird.

### Tore

187 Werkzeug-Tests gruen (171 + 16 neue), Konventions-Check gruen, `server.py` und
`tools/claude_play.py` laden sauber, die Champion-Spec setzt unveraendert ihre zwoelf Knoepfe.
Kein Rust beruehrt, also kein Wheel und keine Anker-Drift noetig.

**Offen aus par.8h:** Punkte 1, 2, 4, 9, 10.

## par.8k RESTLISTE par.8h, BUENDEL 2: die rohen Korpus-Leser (Punkt 1)

**Der als teuerster bezeichnete Fund, und er war groesser als registriert.** Die Vorlage nannte
"16 Sonden"; nachgezaehlt am Code sind es **62 Lesestellen in 61 Werkzeugen** unter `tools/`.
Die Zahl 16 kam aus einer engeren Suche -- deshalb steht hier die GRUNDMENGE: alle `*.py` unter
`tools/` ausser `tools/tests/`, gezaehlt ueber `ast` auf Aufrufe von `pickle.load`/`pickle.loads`,
nicht ueber Textsuche (die haette die Kommentare mitgezaehlt, in denen die Regel ERKLAERT wird).

### Was davon wirklich defekt war, und was nur zerbrechlich

**Gemessen, nicht angenommen:** die Dateien unter `data/` tragen das gzip-Magic, die eingefrorenen
Eval-Sets unter `evaluations/` nicht (`frozen_eval_set.pkl`, `_v2`, `_v3` alle roh). Damit zerfaellt
die Menge:

* **43 der 61 Werkzeuge** lesen ueber `data/`- oder `selfplay_`-Globs. Dort war es LIVE defekt.
  Beleg auf derselben Datei: `pickle.load` -> `UnpicklingError: invalid load key, '\x1f'`,
  `load_records` -> 10 abgeschlossene Spiele (`data/selfplay_v28-b02-policy_20260913_1208_g10.pkl`,
  ueber `scoring_tile_impact.load_final_game_records`).
* **18** lesen nur eingefrorene Eval-Sets. Dort lief es -- und haette beim ersten komprimierten
  Eval-Set aufgehoert. `load_records` entscheidet am Magic-Byte und ist in BEIDEN Faellen richtig.

**Der eigentliche Schaden war die Fehlerpolitik, nicht die Doppelung.** Vier Politiken standen
nebeneinander: laut sterben (die Mehrheit), die Ausnahme schlucken und STILL ueber eine leere
Grundmenge berichten (zwei Sonden, in par.8h Rang 2 behoben), ein eigener Lader in
`count_new_nodes_in_corpus`, der am AUSNAHMETYP statt am Magic-Byte entschied, und ein
`sys.path.insert(0, ".")`, das nur traegt, solange man aus der Projektwurzel startet.

### Wie umgestellt wurde

56 Stellen fielen in vier mechanische Bauformen (`with open(..., "rb")`, `pickle.load(open(...))`,
`pickle.loads(p.read_bytes())`, `with p.open("rb")`), sechs mussten von Hand
(`dome_split_diagnosis`, `interleave_batch_probe`, `plate_head_labels`,
`envelope_head_discrimination_probe`, `train_pcr_dose`, plus der eigene Lader in
`count_new_nodes_in_corpus`).

**Warum der mechanische Teil belegbar sicher ist:** das Muster verlangte, dass die
`pickle.load`-Zeile die EINZIGE Anweisung im `with`-Block ist. Waere ein Block mehrzeilig gewesen,
haette die Entfernung der `with`-Zeile die Einrueckung gebrochen -- `ast.parse` ueber alle
Werkzeuge meldet null Fehler, also war kein Block mehrzeilig. Zehn Einfuegungen des Imports
landeten zunaechst INNERHALB eines mehrzeiligen `import (...)`; sie sind ueber `ast.end_lineno`
neu gesetzt worden statt ueber eine Zeilenheuristik.

Jede Datei hat jetzt einen `__file__`-relativen Anker statt eines arbeitsverzeichnis-abhaengigen;
geprueft ist fuer jede, dass das errechnete `parents[N]` tatsaechlich `corpus_io.py` enthaelt.

### Der Waechter

`tools/tests/test_no_raw_corpus_readers.py` (5 Tests): keine rohe `pickle`-Lesestelle unter
`tools/` ausserhalb einer namentlich BEGRUENDETEN Ausnahmeliste (heute zwei: `repack_corpus`,
das beide Formen anfassen MUSS, und `corpus_io` selbst), kein `sys.path.insert(0, ".")`, und
jeder `corpus_io`-Import mit absolutem Anker. Gezaehlt wird ueber `ast`, nicht ueber Text --
sonst wuerden die Kommentare, die diese Regel erklaeren, ihre eigene Verletzung melden.

### Eigener Fehler auf dem Weg

Ein Kompilierlauf zur Zwischenpruefung schrieb seine `.pyc` in die PROJEKTWURZEL statt in den
Scratchpad (die Umgebungsvariable war in der Ersetzung leer, `Path("") / name` ist ein relativer
Pfad). 232 Dateien, alle ungetrackt -- aber eine davon hiess wie ein Testmodul und hat die
Testsuche uebernommen: `unittest discover` brach mit *"module incorrectly imported"* ab. Entfernt,
nachdem geprueft war, dass alle 232 denselben Zeitstempel meines Laufs tragen und keine getrackt
ist. **Lehre: ein Zwischenschritt, der Dateien schreibt, gehoert in den Scratchpad mit einem
Pfad, der nicht still relativ werden kann.**

### Tore

**192 Werkzeug-Tests gruen** (187 + 5 neue), Konventions-Check gruen, `ast.parse` ueber alle
Werkzeuge fehlerfrei, eine umgestellte Funktion auf einer echten gzip-Korpusdatei nachgefahren.
Kein Rust beruehrt.

**Offen aus par.8h:** Punkte 2, 4, 9, 10.
