# Code-Review 2026-09-11: Zusammenfassung und Plan fuer den Abschluss

**Anlass (Nutzer 2026-09-11):** "lass opus agenten den engine code wie auch den netz code
reviewen (bugs, optimierungspotential, aufraeumen, file size, nachvollziehbarkeit, usw.).
wenn wir das projekt abschliessen in den naechsten generationen will ich es sauber
hinterlassen."

**Verfahren:** sechs Opus-Agenten, je ein Bereich, nur lesend (keine Builds, keine Laeufe;
die Ablations-Kette lief daneben). Berichte in diesem Verzeichnis:

| Bereich | Bericht | Umfang |
| --- | --- | --- |
| Suche | `code_review_2026-09-11_search.md` | `net_mcts.rs` (10.795 Zeilen; Testmodul nur stichprobenweise) |
| Self-Play und Records | `code_review_2026-09-11_selfplay.md` | `self_play.rs`, `serialize.rs` |
| Engine-Kern und Runden | `code_review_2026-09-11_engine_core.md` | Regelmodule, `round5.rs`, Rundenwechsel, `mcts.rs` |
| Bewertung und Merkmale | `code_review_2026-09-11_evaluation_features.md` | `features.rs`, `envelope.rs`, Plattenbauer, `tiling_solver.rs` |
| Netzschicht und Bindings | `code_review_2026-09-11_net_bindings.md` | `net.rs`, `net_ort.rs`, `lib.rs`, `py.rs`, `referee.rs`, Registratur |
| Python Netz und Training | `code_review_2026-09-11_python_training.md` | `neural_net.py`, `corpus_dataset.py`, `train.py`, `server.py`, Cache-Bauer |

**Regel 0:** Agenten-Befunde sind Behauptungen. Die tragenden Funde unten hat der Koordinator
am Code nachgelesen (Spalte "geprueft"); alles andere steht in den Einzelberichten mit
Datei:Zeile und ist dort als Behauptung zu lesen.

## 1. Geprueftes Bild: keine Regelabweichung, aber vier stille Defekte

Die Regelkonformitaet ist in der Breite sauber (Engine-Kern-Bericht: alle acht Wertungsplatten,
Spezialfliesen, Strafleiste, Startspielerstein, Punktgleichstand Zeile fuer Zeile gegen
`docs/engine_manual.md`). Was das Review findet, sind stille Defekte der Sorte, die keine Arena
sieht (CLAUDE.md "Symmetrische Defekte"), Fussangeln in Werkzeugen und Altlast.

| Nr | Fund | Datei:Zeile | geprueft | Einordnung |
| --- | --- | --- | --- | --- |
| A1 | Netz-Auswertungsfehler wird still zu einem 0,5-Blatt: `net.eval_ex(..).unwrap_or_else` liefert leere Vektoren, `value_to_win_prob` macht daraus 0,5; kein Zaehler, keine Spur im Artefakt | `net_mcts.rs:1922-1926`, `:1612-1614` (eine von elf Stellen) | JA | Korrektheit/Beobachtbarkeit: ein aussetzender ONNX-Lauf degradiert die Suche zu Zufall. Fix: Zaehler plus Warnung, in Arena/Self-Play als Fehler |
| A2 | Phantom-Fliesen (per Bonuschip virtuell ergaenzt) stehen als echte Eintraege in `pattern_lines[].tiles`; `provocation::remaining_colors` zieht `phantom_count` nicht ab, `self_play.rs` an seiner Zaehlstelle schon | `round_end.rs:635-638`, `provocation.rs:609-617`, `self_play.rs:6111-6117` | JA | Symmetrischer Defekt, klein: Restvorrat zu niedrig fuer Erreichbarkeits-Kanal 76, `col_f_max`, K3-R/K3-D, nur solange die Reihe noch nicht getilt ist (Rundenende). Fix: eine Zeile, danach Anker-Drift |
| A3 | Spec-Prüfung laesst `score_utility_b = 0` durch; der Term wird zur Vorzeichenfunktion, bei x == x0 NaN | `net_mcts.rs:577`, `:1751`, `:1777` | JA (strukturell; Default 20, Champion-Spec 20) | Robustheit, kein Betriebsfall. Fix: Bereichspruefung wie bei den vier juengsten Feldern |
| A4 | Bonuschip-Sperre (gesperrte Reihen, Manual Z.161) sitzt nur in den Aufrufern, nicht in `apply_bonus_chips_with` | `round_end.rs:460-468` gegen `:613` | JA | Korrektheits-Haertung; alle Aufrufer filtern heute. Fix nur mit Anker-Invarianz |
| A5 | Zwei HTTP-Routen reichen `slot_row`/`slot_col` ungeprueft in Rust-Indexzugriffe; ein Panic im PyO3-Aufruf faengt `except Exception` nicht | `game.rs:232`, `server.py:1000`, Engine-Kern-Bericht | JA | Robustheit des Servers; nur mit fehlerhaften Anfragen erreichbar. Fix: Bereichspruefung in `validate_*` |
| A6 | `Game::is_over()` ist ab Rundenbeginn 5 wahr (`round_number >= NUM_ROUNDS`); nach aussen als `done` | `game.rs:700` | JA | Semantik; intern harmlos (Endwertung haengt an anderem Pfad), Tests trivial erfuellt. Fix: Phase pruefen |
| A7 | Eroeffnungs-Records tragen als Policy-Ziel die tote ID 405 (`action_to_id` faengt Typ "dome" mit `_ => 405`), aber `corpus_dataset.py` gibt Start-Records Policy-Gewicht 0 | `features.rs:1477`, `self_play.rs:976-1005`, `corpus_dataset.py:1331` | JA | KEIN Trainingsfehler (maskiert); Inkonsistenz. Fix: eigener Typ oder Record ohne Policy |
| A8 | `--val-frac 0` verwirft still die Fensterliste: `train_files` bleibt `None`, der Datensatz globt den ganzen Ordner, das Manifest schreibt trotzdem das gewollte Fenster | `train.py:1394-1398`, `corpus_dataset.py:356` | JA | Fussangel; alle Ketten fahren 0,05. Fix: Fehler bei `--file-list` mit `val_frac 0`, oder Liste immer ehren |
| A9 | `MOSAIC_PHASE_AMP/_PEAK/_STAGE` liest die Engine nicht mehr; `tools/probes/phase_sweep.py` faehrt einen wirkungslosen Sweep; der Registratur-Waechter prueft Textvorkommen statt Lesestellen | `knob_registry.rs:112-114`, `phase_sweep.py:77-79` | JA (Grep: null Lesestellen) | Altlast. Fix: Eintraege auf UEBERHOLT, Sonde entfernen oder markieren; Waechter auf `read_*_env("NAME")` schaerfen |
| A10 | Kontrakt-Hash deckt den `ownership`-Kopf nicht (net.rs sucht ihn namentlich) und nicht die Planes-Geometrie | `lib.rs:639-648`, `net.rs:885` | JA | Messsicherheit. Fix bewegt den Hash (Cross-Aera-Folgen): NUTZER-ENTSCHEID |
| A11 | Prozessglobaler Mutex je expandiertem Knoten bei ausgeschaltetem Sammel-Faden; GameState-Klon je Knoten in `make_node` | `net_mcts.rs:1874-1890`, `net_batcher.rs:272-301`, `net_mcts.rs:2044` | Behauptung (nicht nachgelesen) | Leistung; Messung noetig, bevor gebaut wird |
| A12 | "Das Netz sieht nur den ersten Mondstapel je Fabrik" | Bewertungs-Bericht Fund 2 | WIDERLEGT durch die Klaerung 2026-09-05 (`PREREG_stack_top_feature.md` par.10 P.8: kleine Fabriken haben genau einen Stapel, `take_from_sun` leert die Sonnenseite) | kein Fund |
| A13 | Doku-Drift: `ROUND5_ENDSCORING_ENABLED`/`NET_TILING_TIEBREAK_ENABLED` als "AUS bis gemessen" dokumentiert, stehen auf `true`; `provocation.rs:459-464` nennt ein nie berechnetes Kriterium; Zeilenverweise in Registratur und `architecture_reference.md` verschoben; Jokerfeld-Kommentar in envelope.rs an zwei Stellen noch "jede gelegte Platte" | Berichte Bewertung, Suche, Netzschicht | Behauptung (Stichprobe envelope.rs:1043 vom Koordinator selbst korrigiert, Rest offen) | Nachvollziehbarkeit |

## 2. Altlast und Struktur (aus den Berichten, gepruefte Zahlen sind so markiert)

- **Tote Funktionen:** `board.rs:208-222` (`is_row_complete` u.a., kein Aufrufer), vier
  Diagnose-Einstiege in `self_play.rs` (rund 900 Zeilen) ohne Python-Konsument, Inversions-Pfad
  `invert_round5_fill`/`resample_round5_start` samt PyO3-Huelle, `envelope::tiling_cost_delta`
  (dupliziert `tiling_solver.rs:1636-1645`), 37 von 64 oeffentlichen Funktionen in
  `envelope.rs` ohne Aufrufer ausserhalb der Datei (das `X`/`X_in`-Paarmuster).
- **Entschiedene Knoepfe halten Code offen:** rund 4.800 Zeilen in `column_build.rs`,
  `plate_builder.rs`, `provocation.rs`, von denen im Default sechs Funktionen laufen; Legacy-PUCT
  in `net_mcts.rs`; rtv/PCR/Reservationsregel/Aggression in `self_play.rs`; `--encoder flat`
  als Default in `train.py` und drei Cache-Werkzeugen (jeder Champion seit v19 ist 2D);
  acht `server.py`-Endpunkte ohne Frontend-Aufrufer, darunter `/api/stack/peek`.
- **Deutsche Bezeichner:** Engine-Kern 13 (halbe Stunde), `plate_builder.rs` 25 von 28
  Typ-/Konstantennamen, Farb-Sonde in `net_mcts.rs` sechs; `TileColor`-Varianten NICHT
  umbenennen (Serialisierungs-Paritaet).
- **Dateigroessen:** `net_mcts.rs` ist zur Haelfte Testmodul (5.399-10.795): per `#[path]`
  auslagern = Nahtbreite null; ein echter Modulschnitt kostet 17 Namen ueber der Naht, davon
  raten die Berichte ab. `self_play.rs`: schmalster Schnitt `self_play_diagnostics.rs` mit 9
  Namen. `train.py`/`server.py`: Aufteilung vorgeschlagen, aber nicht vor Projektende.
- **112 von 128 tract-Plaenen** werden im Default nie benutzt (rund 1,6 s je `Net::load`);
  Referee/Sonden laden je Aufruf neu (Behauptung, Netzschicht-Bericht).

## 3. Vorschlag: Abschluss-Aufraeumen in drei Stufen

Regeln, die dabei gelten: nichts davon neben einer Messung; nach jeder Engine-Aenderung Wheel,
Netz-Paritaets-Fixture und Anker-Drift (`/mosaic-anchor-invariance`); Bit-Identitaet bei
Default-Knoepfen; Loeschungen nur mit pfadgenauer Freigabe; Bezeichner englisch.

**Stufe 1, Korrektheit und Beobachtbarkeit (rund 4 h, vor v29):** A1 Zaehler und Warnung;
A2 Phantom-Abzug in `remaining_colors`/`still_reachable_colors`; A3 Bereichspruefung; A5
Bereichspruefung der Routen; A8 Fehler bei `--file-list` mit `val_frac 0`; A9 Registratur auf
UEBERHOLT und Waechter schaerfen. Danach Anker-Drift (A2 kann Zuege bewegen: ROT waere
Nutzer-Entscheid, nicht Reparatur).

**Stufe 2, Altlast entfernen (rund 8 h, nach der letzten Generation, VOR dem Einfrieren des
Schlussstands):** tote Funktionen und Diagnose-Einstiege (Liste je Bericht, Freigabe je Pfad),
`--encoder flat`-Defaults, tote Server-Endpunkte, Testmodul von `net_mcts.rs` auslagern,
`self_play_diagnostics.rs` abspalten, deutsche Bezeichner im Kern und in `plate_builder.rs`.
Entschiedene Knoepfe: NICHT loeschen, sondern je Knopf entscheiden (Registratur-Status
UEBERHOLT plus Kommentar reicht, wenn der Code Bit-Identitaet bei Default hat; entfernen nur,
wo der Zweig Wartungslast erzeugt).

**Stufe 3, Doku (rund 3 h):** Zeilenverweise in `knob_registry.rs` und
`docs/architecture_reference.md` nachziehen, die vier widersprechenden Kommentare (A13),
Registratur-Waechter auf Lesestellen, `docs/knobs.md` generieren.

**Nutzer-Entscheide:** A10 (Hash erweitern, Cross-Aera-Folge), A4 (Sperre in die
Arbeitsfunktion, moegliche Anker-Bewegung), Umfang von Stufe 2 (welche Knopfzweige
verschwinden).

## 4. Was das Review NICHT geprueft hat

Keine Laeufe, keine Messungen: die Leistungsbefunde (A11, tract-Plaene) sind Lesebefunde; das
Testmodul von `net_mcts.rs` und Teile der Python-Werkzeuge wurden stichprobenweise gelesen;
Zeilenverweise gelten fuer den Stand vom 2026-09-11 abends (nach K3-D).
