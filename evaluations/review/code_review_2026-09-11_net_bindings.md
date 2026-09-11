# Code-Review: Netz-Inferenz, Bindings, Referee, Registratur

**Datum:** 2026-09-11
**Bereich, alles gelesen:** `net.rs` (1437), `net_ort.rs` (419), `net_batcher.rs`
(428), `lib.rs` (2183), `py.rs` (1292), `referee.rs` (829), `profiling.rs` (817),
`knob_registry.rs` (368) = 7.773 Zeilen. Querverweise: `docs/architecture_reference.md`,
`docs/knobs.md`, `CLAUDE.md`.
**Art:** rein lesend. Kein Bau, kein Lauf. Alle Laufzeitzahlen unten sind ZITATE aus
Kommentaren im Baum, in dieser Sitzung nicht nachgemessen -- so markiert.

---

## 1. Bugs und Korrektheitsrisiken

**1.1 `split_planes_flat_batch_src` kuerzt nur in eine Richtung (net.rs:982-983).**
`planes_len`/`flat_len` kommen aus dem MODELL, `src_planes_len` aus dem Bauer
(net.rs:445). Der Fall "Bauer breiter als Modell" ist sauber. Umgekehrt ungeprueft:
Modell mit mehr Planes-Kanaelen -> `&s[..planes_len]` liest still in den Flat-Block
(Formen gueltig, Werte falsch); Modell mit mehr Flat-Werten -> Panik statt
`TractError`, in einem rayon-Worker also Laufabbruch. Dass die Panik real ist, steht
im Baum: lib.rs:1210-1211 protokolliert sie ("range end index 2736 out of range for
slice of length 708", 2026-08-23). Heute nicht erreichbar (`INPUT_SIZE = 755`,
features.rs:18, gegen Champion 744 = gedeckte Richtung). **Latent, Cross-Aera.**

**1.2 ORT-Pfad kuerzt beim Flat-Layout gar nicht (net_ort.rs:221-227).** tract kuerzt
an derselben Stelle auf die Modellbreite (net.rs:426). Bei `n != s.len()` scheitert
`Tensor::from_array` -> `Err` -> `warn_ort_cuda_fallback_once` (net.rs:54) -> stiller
Rueckfall auf tract fuer die ganze Prozesslaufzeit. Kein falsches Ergebnis, aber der
GPU-Kanal schaltet sich lautlos ab. Nicht produktionsrelevant, siehe 2.1.

**1.3 Die Pflicht-Vier werden ungeprueft positionell indiziert.** `out[0]`..`out[3]`
in net.rs:468/498/559/614/653/719 und net_ort.rs:307-310: weniger als vier Ausgaenge
= Panik. Die OPTIONALEN Koepfe sind dagegen namens- UND laengengesichert
(`Some(idx) if out.len() > idx`, net.rs:617-626). Die Asymmetrie ist unbeabsichtigt;
erreichbar ist sie heute nicht.

**1.4 Was der Vertragshash nicht deckt (lib.rs:639-648).** Gestempelt werden
`INPUT_SIZE`, `NUM_PLANES_CHANNELS`, `NUM_ACTIONS` und eine hart geschriebene
Kopf-Liste. Nicht gedeckt:
- **`PLANES_H`/`PLANES_W`.** `NUM_PLANES_VALUES = C*H*W` (features.rs:1169) -- eine
  Aenderung an H oder W verschiebt die Planes/Flat-Grenze in net.rs:982, ohne den
  Hash zu bewegen. `state_planes_from_json` verdrahtet die 6/6 sogar ein zweites Mal
  von Hand (lib.rs:1619), statt die Konstanten zu lesen.
- **Der `ownership`-Kopf.** net.rs:884-895 sucht ihn NAMENTLICH, genau wie
  `opp_points`; die Hash-Liste nennt nur `opp_points`. Bei einer Umbenennung im
  Export liefert `eval_*_ex` still eine leere Ownership-Spalte, der Verbraucher
  schoebe nichts, der Hash bliebe stehen.
- **Die Bedeutung der Merkmalsplaetze** -- eine Umsortierung innerhalb der 755 Werte
  laesst den Hash unveraendert. Dagegen steht der getrennte A3-Golden-Hash in
  `features.rs`; der Doc-Kommentar lib.rs:625-639 sagt diese Arbeitsteilung nicht.

Der Waechter selbst (lib.rs:2147-2155, Literal `c65768636c0560a7`) ist in Ordnung und
wird gepflegt -- fuenf dokumentierte Neusetzungen, die letzte heute.

**1.5 Die Tiling-Entscheidung ist zweimal gebaut.** `py.rs:962-983` (GUI) und
`self_play.rs:1282-1296` (`resolve_tiling_step_with`, Arena/Referee) sind Zeile fuer
Zeile dieselbe Logik: `ownership_tiling_marginals`, `net_tiling_tiebreak_value`,
`net_tiling_margin_value`, dann `best_first_step_exact_or_valued_envelope` mit
identischer Argumentliste; der netzlose Zweig ebenso. Der Kommentar direkt darueber
(py.rs:956-961) behauptet das Gegenteil ("ueber dieselbe Funktion -- eine zweite
Implementierung koennte auseinanderlaufen"). Geteilt ist nur der Blatt-Helfer.
`resolve_tiling_step_with` ist `pub(crate)` (self_play.rs:1276), py.rs koennte ihn
direkt rufen. **Kein heutiger Verhaltensunterschied** (beide Bloecke verglichen),
aber die Drift-Gelegenheit ist gebaut und der Kommentar deckt sie zu.

**1.6 Knopf-Quelle: GUI liest Env, Arena liest Spec.** `net_search_with_tree`
(net_mcts.rs:4983) und der GUI-Tiling-Pfad (py.rs:969) rufen
`SearchConfig::from_env()`; die Arena-/Referee-Einstiege nehmen eine Pro-Seite-Spec
(lib.rs:259-268; referee.rs:231, :697). `server.py:204-222` uebersetzt beim Start.
**Geprueft und heute vollstaendig:** `SearchConfig` hat 14 `pub`-Felder
(net_mcts.rs:383-475), 13 stehen in `_SPEC_TO_ENV`, das 14.
(`score_utility_root_margin`, net_mcts.rs:412) ist intern abgeleitet und kommt laut
Test net_mcts.rs:6680 "nie aus einer Spec". Zwei offene Kanten:
- `KNOWN_FIELDS` (net_mcts.rs:531-546) akzeptiert `heuristik_variante`, aber weder
  `SearchConfig` noch `_SPEC_TO_ENV` konsumieren es: eine Spec mit
  `"heuristik_variante": "hv2"` wird still angenommen und wirkt nicht.
- Kein Waechter haelt `_SPEC_TO_ENV` gegen `KNOWN_FIELDS`. Das naechste Spec-Feld
  faellt in der GUI still aus -- genau das ist schon passiert, protokolliert in
  server.py:230-234.

**1.7 Stille Defaults.** `configured_batch_max()` (net_batcher.rs:245-253):
`MOSAIC_INTERLEAVE_BATCH_MAX` ausserhalb `1..=128` faellt per `.filter(...)` still auf
128 -- ein Tippfehler im Messlauf ist unsichtbar, gegen die Hausregel "Lauf-Manifest
gegen Referenz". Ebenso `fill_timeout()` (net_batcher.rs:263-270, still 200 us).
`seed.unwrap_or(0)` an lib.rs:1321, :1358, :1465, :1711, :1730: der Einstieg sieht
geseedet aus, determinisiert ohne Argument aber alle Aufrufe identisch. Ob das die
jeweiligen Verbraucher stoert: **unklar**, nicht einzeln nachgelesen.

**1.8 Registry nach Zeiger-Identitaet** (net_batcher.rs:287, :299; net_ort.rs:201).
Die Begruendung (net_batcher.rs:40-49) traegt fuer Selfplay/Arena, wo ein `Arc<Net>`
den ganzen Lauf lebt. Fuer die GUI gilt sie nicht: `load_net`/`clear_net`
(py.rs:103, :135) legen und verwerfen `Net`-Instanzen im selben Prozess. **Heute
folgenlos**, weil py.rs `ensure_batcher_for` nie ruft. Wer den Batcher je in der GUI
verdrahtet, faellt hinein; ein Satz an der Registry-Doku wuerde das festhalten.

---

## 2. Tote und ueberholte Pfade

**2.1 `net_ort.rs` steckt in keinem gebauten Artefakt.** `#![cfg(feature =
"ort_cuda_probe")]` (net_ort.rs:107), Feature optional (Cargo.toml:44), von keinem
Wheel-Bau gesetzt (Grep ueber `*.toml`/`*.py`/`*.ps1`: nur Cargo.toml, ein Kommentar
in self_play.py:42, Prereg-Prosa). 419 Zeilen plus das Hook-Paar net.rs:31-97 und
vier `allow(dead_code)`-Marken (net.rs:62, :85, :89, :115).

**2.2 pyo3-Exporte ohne Python-Aufrufer.** Selbst nachgeprueft per Grep ueber ALLE
`*.py` im Repo (Grundmenge: Root, `tools/`, `engine/py/`, `engine/`):
`reset_tiling_budget_stats` (lib.rs:1672), `reset_score_utility_stats` (lib.rs:844),
`net_search_states_json_batch` (lib.rs:973), `onnx_eval` (lib.rs:608),
`resample_round_transition_json` (lib.rs:1819), `profiling_snapshot`/`profiling_reset`
(lib.rs:534/:523) -- null Treffer.

Bemerkenswert: `net_search_states_json_batch` wurde 2026-09-02 gebaut, WEIL der
Einzel-Einstieg das Netz je Aufruf neu laedt (lib.rs:961-962) -- und hat keinen
Aufrufer, waehrend der teure Einzel-Einstieg benutzt wird.

Nur-Prosa, kein Aufruf (Agentenbefund), zwei Klassen: `sibling_ranking_diagnostic`,
`value_noise_floor_diagnostic` und `tiling_budget_stats_json` stehen in LEBENDER Doku
(`DOSSIER_ownership_head.md`, `docs/architecture_reference.md:114`,
`PREREG_floor_action_aversion.md:441`) -- referenzierte Messinstrumente, nicht
vergessen. `profiling_reset`, `profiling_snapshot`, `draw_stack_peek_impact_diagnostic`
stehen dagegen nur noch in `archive/history.md`.

**2.3 `PyGame`-Methoden ohne Aufrufer** (selbst per Grep ueber alle `*.py`
bestaetigt): `net_eval_raw` (py.rs:123), `clear_net` (py.rs:135), `first_player`
(py.rs:179), `ai_debug_log` (py.rs:598). Bei `first_player` gegengeprueft: der Name
kommt in `*.py` nur als Konstruktor-Argument und JSON-Feld vor, nie als Methodenaufruf.

**Ein ganzer Pfad ist aufgegeben, aber stehen geblieben:** `onnx_eval` +
`net_eval_raw` + `clear_net` bilden den Einstieg "Netz direkt auf einen
Merkmalsvektor auswerten". Die einzige Erwaehnung ausserhalb des Archivs ist eine
Absage (`PREREG_r5_value_calibration.md:67`: "Erster Anlauf verworfen:
`PyGame.features()` + `mosaic_rust.onnx_eval()`"). Die drei gehoeren als Gruppe weg.

**2.4 Drei Registratur-Eintraege ohne Leser.** `MOSAIC_PHASE_STAGE`, `_AMP`, `_PEAK`
(knob_registry.rs:112-114, Status `Diagnose`). Selbst geprueft: Grep nach
`MOSAIC_PHASE_|phase_wirkt_auf|spalten_phase` ueber `engine/src/**/*.rs` liefert
ausserhalb `knob_registry.rs` null Treffer; die genannte Pruefstelle
`plate_builder.rs::phase_wirkt_auf` existiert nicht mehr.

**Die schwerere Haelfte:** `tools/probes/phase_sweep.py:77-79` SETZT die drei
weiterhin und faehrt damit einen Sweep, der per Konstruktion nichts veraendert. Ein
Messwerkzeug, das folgenlos schwenkt, produziert Nullbefunde, die wie Ergebnisse
aussehen.

**Warum das Tor nicht angeschlagen hat:** `registered_non_dead_knobs_exist_in_code`
(knob_registry.rs:309-323) prueft TEXTVORKOMMEN, nicht Lesestellen, und seine
Scan-Menge schliesst `tools/**/*.py` ein (knob_registry.rs:255) -- das `set_var` in
`phase_sweep.py` genuegt ihm. Dieselbe Luecke traegt jeder Knopf, dessen Name noch in
einem Kommentar steht. Bauform: "ein umgangenes Tor erzieht zum Umgehen".

Zur Fairness: die Gegenrichtung ist dicht (kein unregistrierter Knopf im Code --
selbst geprueft per Literal-Diff ueber `engine/src/*.rs` und `*.py`), und
`docs/knobs.md` ist mit 111 zu 111 aktuell (knob_registry.rs:68-188, 111 Eintraege:
65 aktiv, 38 diagnose, 7 tot, 1 geplant).

**2.5 Veraltete Pruefstellen und Defaults in der Registratur** (Agentenbefund,
teilweise nachgeprueft): knob_registry.rs:172-175 nennen Zeilen und Werte, die nicht
mehr stimmen -- `MOSAIC_DISPLAY_CAL_A` steht dort mit `-0.0033`/`server.py:1407`,
tatsaechlich `-0.0476` an server.py:1666 (selbst gesehen). Dass Pruefstellen driften,
sagt knob_registry.rs:63-64 selbst; die DEFAULTS sollten es nicht.

**2.6 Profiling: zwei Systeme, beide praktisch aus.** System 1 (`clone_profiling`,
profiling.rs:1-330) ist nur ueber einen Sonder-Bau erreichbar und wird ausschliesslich
aus `engine/examples/` ausgelesen -- `profiling_snapshot()` hat keinen
Python-Konsumenten (2.2). System 2 (`selfplay_profile`, profiling.rs:414ff) haengt an
`MOSAIC_PROFILE_SELFPLAY` (profiling.rs:493); selbst geprueft: kein `*.py`, `*.ps1`
oder `*.toml` im Baum setzt die Variable, der einzige Konsument bekaeme also einen
Snapshot aus Nullen.

Positiv: die Aus-Kosten sind sauber -- `timed_with_enabled` kehrt vor jedem
`Instant::now()` zurueck (profiling.rs:488-491). **Blinder Fleck im Aktiv-Fall:** in
`eval_batch`/`eval_batch_ex` liegt der ORT-Hook VOR dem `timed`-Wrapper
(net.rs:540-545, :735-737) -- laeuft der GPU-Kanal, wird seine Zeit nicht gebucht.

---

## 3. Optimierungspotenzial

**3.1 112 von 128 tract-Plaenen werden nie benutzt (net.rs:385-393).**
`build_from_layout` baut EAGER je einen optimierten Plan fuer `N in 1..=128`. Die
einzigen Nicht-Test-Aufrufer von `eval_batch*`:
- Gumbel-Wurzel-Buendelung, net_mcts.rs:3930 und :3948, mit `m_prime <= GUMBEL_TOP_M
  = 16` (net.rs:196-197 sagt diese Schranke selbst zu);
- Sammel-Faden, net_batcher.rs:189 -- laeuft nur bei `MOSAIC_INTERLEAVE_ENABLED`
  (net_batcher.rs:231-236, Default AUS).

Kosten laut Kommentar net.rs:174-179 (dort GEMESSEN, nicht von mir): 16 Plaene
0,293 s, 128 Plaene 1,927 s. Rund 1,6 s je `Net::load*`, die im Default-Betrieb
niemand abruft -- und das trifft jeden Ladevorgang: py.rs:111, referee.rs:279/:366,
lib.rs:608/:1202/:1272/:913. Vorschlag: `1..=GUMBEL_TOP_M` eager, den Rest nur bei
`net_batcher::interleave_enabled()`. Eine Bedingung, `Sync` bleibt unangetastet.

**3.2 Vermeidbare Kopien beim Batch-Rueckbau.** `eval_batch`/`eval_batch_ex`
(net.rs:563-570, :745-752) und `eval_batch_ex_via_ort_cuda` (net_ort.rs:328-339)
bauen ihre Zeilen mit `split_batch_n` und klonen danach JEDE nochmal
(`policy_rows[i].clone()`). Bei N=16 und 406 Policy-Werten sind das 16 unnoetige
Vektorkopien je Aufruf; ein `into_iter()`-Zip spart sie ohne Semantikaenderung.
`Batcher::eval_rows` kopiert zusaetzlich jede Zeile in den Kanal (`f.to_vec()`,
net_batcher.rs:137, ~3.500 f32) -- unvermeidbar bei `&[f32]`-Signatur, eine
`Vec<f32>`-Signatur wuerde den Move erlauben. Nur bei eingeschaltetem Batcher relevant.

**3.3 Modell-Neuladen je Einzelentscheidung.** `net_search_state_json` (lib.rs:913),
`net_arena_choice_state_json` (:1202), `tiling_choice_state_json` (:1272) und
`onnx_eval` (:612) rufen je Aufruf `Net::load_auto`. referee.rs:322-324 nennt dafuer
**2.023 ms je Entscheidung, rund 48 s je Partie** (dort gemessen, nicht von mir). Der
Ausweg ist gebaut und richtig (`FrozenWorkerEngine` haelt das Netz,
referee.rs:216-232), und die Kommentare sagen, dass die freien Einstiege fuer
Stapelaufrufe gedacht sind (lib.rs:1196-1201). Mit 3.1 zusammen faellt der Posten um
rund 1,6 s je Aufruf, ohne dass eine Cache-Lebensdauer geklaert werden muss.

**3.4 GIL.** Alle Massen-Einstiege geben sie frei (11x `py.detach` in lib.rs, u.a.
:87, :302). Die Einzel-Entscheidungs-Einstiege (lib.rs:906, :1188, :1242, :1265,
:1290) und saemtliche `PyGame`-Methoden halten sie ueber die ganze Suche. Fuer die
GUI folgenlos; es erklaert aber, warum `anchor_referee_parity_probe.py` und
`build_frozen_golden_probe.py` sequenziell bleiben muessen.

**3.5 Kleiner Posten im GUI-Tiling.** py.rs:943 rechnet `solve_round_final_score` --
einen vollen exakten DFS-Durchlauf -- ausschliesslich fuer zwei Debug-Felder
(py.rs:1032, :1045), je KI-Tiling-Schritt. Der Arena-Pfad zahlt das nicht.

---

## 4. Struktur und Nachvollziehbarkeit

**4.1 Deutsche Bezeichner: der Bereich ist fast sauber.** Vollstaendige Liste ueber
alle acht Dateien:

| Stelle | Bezeichner | Naht |
|---|---|---|
| referee.rs:217, :224, :232, :243 | `heuristik_drafting` | Feld + pyo3-Signatur, Aufrufer `tools/frozen_champion_worker.py` |
| lib.rs:108, :122, :137-147 | `heuristik_variante` | pyo3-Signatur, Aufrufer `self_play.py`, plus `KNOWN_FIELDS` net_mcts.rs:545 |
| referee.rs:490 | `externe` | lokal |
| lib.rs:1372 / :1475 | `spalten` / `wertung_e` | lokal |
| net.rs:1346, :1349 | `verschoben`, `unbenannt` | lokal, Testcode |

Fuenf davon sind Ein-Zeilen-Umbenennungen; die zwei `heuristik_*` queren die
Python-Kante und eine Spec-Schema-Liste (Naht drei bis vier Namen ueber Sprachgrenze).

**4.2 `lib.rs` als Sammelbecken** -- 2.183 Zeilen, 53 pyo3-Funktionen, fuenf Gruppen
(gezaehlt am `#[pymodule]`-Block lib.rs:2011-2069): Selfplay/Arena (lib.rs:75-520),
Vertrag/Konfiguration (:639-800), Laufzeit-Regler und Zaehler (:801-880),
Zustands-JSON fuer Sonden und Referee (:904-1600), Uebergangs-/Wertungssonden
(:1600-2010).

*Naht-Analyse.* Gruppe 2 ist die sauberste: `contract_hash`/`fnv1a_64` sind
`pub(crate)` mit genau zwei externen Nutzern (A3-Golden-Hash in `features.rs`, der
Testblock lib.rs:2073-2183), `engine_config_json` liest nur Konstanten. Ein
`engine_contract.rs` haette eine Naht von zwei Namen. Gruppe 4 waere der groessere
Gewinn (~700 Zeilen), aber die Naht ist breiter: gemeinsam sind
`resolve_search_config` (lib.rs:259), der `json_to_state`-Zweig und je eigene
JSON-Schemata.

*Empfehlung: nicht mehr schneiden.* Bei ein bis zwei verbleibenden Generationen
kostet ein Schnitt mehr an Wheel-Neubau, Anker-Invarianz-Pruefung und
Aufrufer-Nachzug, als er an Lesbarkeit bringt.

**4.3 Ueberholte oder widerspruechliche Doc-Kommentare.**

| Stelle | Behauptung | Ist |
|---|---|---|
| py.rs:956-961 | Tiling laeuft "ueber dieselbe Funktion" wie der Selfplay-Pfad | Zweitkopie, siehe 1.5 |
| lib.rs:1208 | `PyGame::features` "liefert IMMER das flache 708er-Legacy-Layout" | liefert `INPUT_SIZE` = 755 (features.rs:18); py.rs:158 sagt es richtig |
| net.rs:110-111, :143-145 | "alle Bestandsmodelle v1..v18, N=708" als Gegenwart | historisch; heutige Modelle 714/744 |
| net.rs:121-122 | `load`: `input_size` "muss zur Feature-Laenge passen" | seit net.rs:426 genuegt `<=`; beschreibt den Vor-2026-08-25-Vertrag |
| knob_registry.rs:112-114 | Pruefstelle `plate_builder.rs::phase_wirkt_auf` | existiert nicht mehr, siehe 2.4 |
| net_ort.rs:391 | Test synthetisiert mit `net.input_size()` | net.rs:1243-1250 erklaert, dass das der FALSCHE Vertrag ist (`builder_input_len()` waere richtig) |

**4.4 Tests, deren Name mehr verspricht als sie pruefen.**
- `net_ort.rs:377 eval_batch_via_ort_cuda_matches_tract_within_tolerance`: `#[ignore]`
  UND wuerde in dieser Form am falschen Eingabevertrag scheitern (4.3, letzte Zeile) --
  also selbst mit CUDA-DLLs kein abrufbarer Paritaetsbeleg.
- `net_batcher.rs:369 batcher_eval_rows_matches_direct_eval_batch`: vergleicht gegen
  `eval_batch_ex` (Zeile 390). Inhaltlich richtig, nur der Name hinkt.
- Gegenprobe, damit das Bild stimmt: `net.rs:1243-1250` (`builder_input_len`)
  dokumentiert die Vertragsfalle ausdruecklich, und die `load_test_net`-Kommentare
  (net.rs:1189-1195, net_batcher.rs:317-328) halten zwei echte Leer-Gruen-Vorfaelle
  fest. Diese Sorgfalt ist im Bereich die Regel.

**4.5 Kopf-Extraktion viermal ausgeschrieben.** Der Block "Ausgaben 0..3, dann
`opp_head_index`/`own_head_index` optional" steht identisch in net.rs:604-637,
:639-698, :700-767 und net_ort.rs:307-320 -- rund 60 Zeilen Duplikat. Ein privater
Helfer zoege drei davon zusammen; der ORT-Zweig bliebe getrennt (anderer Tensor-Typ).

---

## 5. Prioritaet vor Projektende

Aufwand geschaetzt, nicht gemessen.

| # | Punkt | Stelle | Aufwand | Risiko |
|---|---|---|---|---|
| 1 | `MOSAIC_PHASE_*` auf `Tot` setzen UND `phase_sweep.py` stilllegen oder warnen lassen | knob_registry.rs:112-114, phase_sweep.py:77-79 | 0,5 h | keins, kein Code-Pfad |
| 2 | Waechter auf LESESTELLEN statt Textvorkommen umstellen (`env::var`/`read_*_env*`/`probe_usize`) | knob_registry.rs:309-323 | 1,5 h | mittel: deckt vermutlich weitere Leichen auf, das ist der Zweck |
| 3 | Eager-Planbau auf `1..=GUMBEL_TOP_M` begrenzen, Rest nur bei aktivem Batcher | net.rs:385-393 | 1 h | niedrig, aber Engine-Aenderung -> Anker-Invarianz-Pruefung Pflicht |
| 4 | py.rs:962-983 durch `resolve_tiling_step_with(...)` ersetzen, Kommentar berichtigen | py.rs:956-983 | 0,5 h | niedrig; Bloecke als deckungsgleich verglichen, GUI-Zugfolge einmal gegenspielen |
| 5 | Laengenpruefung in `split_planes_flat_batch_src` (klarer Fehler statt Panik/Stilldatenfehler) | net.rs:978-985 | 1 h | niedrig; macht den Cross-Aera-Fall diagnostizierbar |
| 6 | `ownership` in die Kopf-Liste des Vertragshashs, `PLANES_H`/`PLANES_W` ergaenzen, Literal neu setzen, lib.rs:1619 mit umstellen | lib.rs:640-648, :2147, :1619 | 1 h | **mittel**: bewegt den Hash -> Nutzer-Entscheid noetig (Aera-Regel) |
| 7 | Waechter `_SPEC_TO_ENV` gegen `KNOWN_FIELDS`; `heuristik_variante` verdrahten oder streichen | server.py:204, net_mcts.rs:531-546 | 1,5 h | niedrig |
| 8 | Registratur-Defaults an server.py:1666-1668 und train.py angleichen | knob_registry.rs:172-175 | 0,5 h | keins |
| 9 | Tote Exporte und Methoden entfernen (2.2/2.3, zehn Stueck, `onnx_eval`-Gruppe zusammen) | lib.rs, py.rs | 1,5 h | niedrig, aber pyo3-Signaturwechsel -> vor dem Push `cargo test --release --no-run` mit examples/benches (CLAUDE.md) |
| 10 | Doc-Korrekturen aus 4.3, fuenf Stellen, reine Kommentararbeit | siehe Tabelle | 0,5 h | keins |

**Kann bleiben** (bewusst nicht auf der Liste):

- `net_ort.rs` samt Hook-Paar (2.1). Gemessen, dokumentiert, kostet im Default-Bau
  null Bytes; Entfernen naehme eine belegte Messung aus dem Baum. Nutzer-Entscheid,
  kein Aufraeumen.
- Die positionelle Indizierung `out[0..3]` (1.3): kein exportiertes Modell trifft den
  Fall, eine Pruefung waere Code fuer ein Szenario, das nie eintritt.
- Die Aufteilung von `lib.rs` (4.2) und die GIL-Haltung der Einzel-Einstiege (3.4).
- Die deutschen KNOPF-NAMEN (`MOSAIC_SPALTENBAU`, `MOSAIC_WERTUNG_*`, ...): das sind
  Env-Variablen, also externe Schnittstelle, festgeschrieben in Specs, Lauf-Manifesten
  und Messartefakten. Die Bezeichner-Konvention meint Code-Bezeichner, nicht
  Protokoll-Namen.
- `MOSAIC_PROFILE_SELFPLAY` ohne Setzer (2.6): der Schalter funktioniert, er wird von
  Hand gesetzt -- Bedienfrage, kein Defekt.
- 38 Diagnose-Knoepfe: je ein `OnceLock`-Read, vernachlaessigbar, und sie
  dokumentieren die Kampagne.
