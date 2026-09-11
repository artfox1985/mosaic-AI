# Code-Review Python-Seite (Netz, Daten, Training, Serving)

- **Datum:** 2026-09-11
- **Bereich:** `engine/py/neural_net.py`, `engine/py/corpus_dataset.py`,
  `engine/py/file_cache_key.py`, `engine/py/reach_target.py`, `train.py`,
  `self_play.py`, `export_onnx.py`, `config.py`,
  `tools/build_cache_incremental.py`, `tools/build_cache_parallel.py`,
  `tools/paired_gating.py`, `server.py`
- **Gelesene Zeilen:** 11.868 (alle zwoelf Dateien vollstaendig; `train.py` und
  `server.py` ueber Subagenten kartiert, die tragenden Befunde danach selbst an
  der Quelle nachgeprueft -- was NICHT nachgeprueft ist, steht unten so da)
- **Art:** rein lesend, keine Ausfuehrung (Messkette lief), keine Quelldatei
  angefasst.

---

## 1. Bugs und Korrektheitsrisiken

### 1.1 `--val-frac 0` verwirft das gewaehlte Fenster (schwerster Fund)

`train.py:1397` setzt `train_files = None`, der Split-Block `:1398` laeuft nur
bei `val_frac > 0 and len(all_files) >= 10`. Bleibt `train_files` auf `None`,
globt `MosaicDataset` in `corpus_dataset.py:356` selbst den GANZEN
`data/`-Ordner (nur `MOSAIC_DATA_EXCLUDE` greift dort noch). Damit sind bei
`--val-frac 0` still wirkungslos: `--file-list` (`:1255-1271`, samt seinem
harten Abbruch bei fehlenden Eintraegen), `--extra-data-dir` (`:1237-1240`,
dessen Dateien gar nicht in `DATA_DIR` liegen) und `--train-file-limit`
(`:1446` prueft `train_files is not None`).

Zwei Verschaerfungen: das Lauf-Manifest schreibt `_manifest_files`
(`:1390-1394`), also das GEWOLLTE Fenster -- Manifest und trainierte Menge
koennen auseinanderlaufen, ohne dass es jemand sieht. Und der
`--cache-file`-Hilfetext empfiehlt genau diese Kombination (`:1464`). Der
Cache-Waechter faellt nicht auf: er rechnet den Fenster-Schluessel aus
derselben `files=None`-Glob-Liste und bestaetigt sich selbst.

Billigster Fix: `train_files = all_files` statt `None` in `train.py:1397`.

### 1.2 Warmstart-Verbreiterung nur fuer den Flach-Zweig, ohne Lage-Beweis

`train.py:1675-1682` fuellt fehlende EINGANGSSPALTEN von
`flat_branch.0.weight`/`body.0.weight` mit Nullen auf. Zwei Luecken:

- **Keine Pruefung, dass neue Merkmale HINTEN haengen.** Der Code kennt nur
  "alt schmaler als neu"; wo die neuen Spalten liegen, steht ausschliesslich im
  Kommentar (`train.py:1673-1674`). Wuerde ein Merkmal in der Mitte eingefuegt,
  wanderten alle Alt-Gewichte still auf falsche Eingaenge. Die Konvention wird
  in `neural_net.state_to_tensor_python` zwar durchgehalten (Abschnitte 12/13/
  14/15 haengen ausdruecklich ans Ende, `neural_net.py:357`, `380`, `408`),
  aber nichts erzwingt sie. Vorschlag: `INPUT_SIZE` in den Checkpoint schreiben
  und beim Warmstart gegen einen Marker "additiv erweitert" pruefen.
- **Kein Gegenstueck fuer die Planes-Kanaele.** `train.py:1630` baut
  `Mosaic2DNet` OHNE `planes_channels`, also mit `NUM_PLANES_CHANNELS` (79,
  `neural_net.py:517`). Ein 77-Kanal-Checkpoint faellt damit in `skipped`
  (`train.py:1683-1686`) und die erste Conv-Schicht startet ZUFAELLIG, mit einer
  Warnzeile. Der Flach-Zweig wird geschont, der Conv-Zweig nicht -- dieselbe
  Erweiterungsart, zwei verschiedene Behandlungen.

### 1.3 Datei-Block-Schluessel wird im ELTERNPROZESS gebildet, der Inhalt im Worker

`build_cache_incremental.py:200` ruft `_block_path(...)` im Elternprozess;
`per_file_cache_key` liest `INPUT_SIZE` erst beim Aufruf
(`file_cache_key.py:207`, dort ausdruecklich so gewollt). Gebaut wird der Block
aber im Worker (`_build_one_file`, `:127-147`), der `config.py` FRISCH
importiert. Aendert sich `INPUT_SIZE` waehrend des Laufs, traegt der Block
Inhalt A unter Schluessel B -- genau der Vorfall, der am 2026-09-11 den
Formen-Waechter in `build_cache_parallel.py:116-133` erzwungen hat (24 Bloecke
mit 755 Spalten unter einem 744er-Schluessel). Der Waechter faengt es beim
Merge, die Ursache steht noch. Fix: den Schluessel IM Worker bilden (oder
`INPUT_SIZE` mitgeben und dort gegen den frischen Import pruefen). Dieselbe
Bauform in `build_cache_parallel.py:231`: der Elternprozess stempelt seinen
Fenster-Schluessel auf Teilbloecke, die die Worker mit ihrem eigenen
`config.py`-Stand gebaut haben.

### 1.4 `load_state_dict(..., strict=False)` deckt fehlende Schluessel still zu

`neural_net.py:2082`, `export_onnx.py:113`, `export_onnx.py:213`,
`train.py:1687`. Form-Abweichungen fliegen (bzw. werden vorher gefiltert),
FEHLENDE Schluessel nicht: der betroffene Kopf bleibt zufallsinitialisiert.
Konkret nicht aus dem Checkpoint abgeleitet wird `conv_layers` in
`build_model_from_checkpoint` (`neural_net.py:2067-2073`, Default 2 aus
`neural_net.py:1756`) -- ein Checkpoint mit drei Conv-Lagen laedt dort
STILL falsch (die Ueberzaehligen sind "unexpected keys"). `export_onnx.py:191`
leitet `conv_layers` korrekt ab; die beiden Wege sind also uneinheitlich.

### 1.5 Kleinere, belegte Punkte im Netz-/Export-Pfad

- **ONNX-Referenz deckt nur vier von bis zu neun Ausgaengen.**
  `export_onnx.py:163-171` und `:250-262` schreiben `policy`/`value`/`moon`/
  `points`; `ownership`, `points_dist`, `value_wdl_logits`, `opp_points`,
  `endgame_margin` sind in der Rust-Paritaetsprobe nicht abgedeckt. Folgenlos,
  solange Rust nur `out[0..3]` liest -- der Modulkopf (`:7-8`) verspricht mehr.
- **Stale Kopfzahlen.** `export_onnx.py:25` nennt `planes [batch,76,6,6]` und
  `state [batch,708]`; heute sind es 79 (`neural_net.py:517`) und 755
  (`config.py:38`). Ebenso zeigen `neural_net.py:1193` und
  `corpus_dataset.py:1395` auf "config.py:117", waehrend
  `CONJUNCTIONS_PER_PLAYER` in `config.py:120` steht.
- **`COLOR_ID_MAP` nur im Zwei-Spieler-Zweig.** Definiert in
  `neural_net.py:235` innerhalb von `if len(players) == 2:`, benutzt in
  `:394` ausserhalb -- `NameError` statt gepolstertem Vektor.
  `state_to_planes_python:589` faengt denselben Fall sauber ab.
- **`own_dtype` haengt an der LETZTEN Datei.** Gesetzt je Datei in
  `corpus_dataset.py:1051`, benutzt fuer den ganzen Block in `:1461`. Heute
  harmlos, bei leerer Dateiliste ein `NameError`. Gehoert vor die Schleife.
- **`threads` im Laufzeit-Block ist die Blockzahl.**
  `build_cache_parallel.py:260` schreibt `len(bloecke)`, gemessen wurde mit
  `n_w` Prozessen (`:197`). `build_cache_incremental.py:347` macht es richtig.

### 1.6 server.py: globaler Zustand, ungenutzte Sperre, Rennen

`server.py:94` haelt EINEN globalen Spielzustand fuer alle Sitzungen;
`server.py:111` definiert `_ai_lock = threading.Lock()`, das im ganzen Modul
sonst nicht vorkommt (selbst geprueft: einziger Treffer). `server.py:1888`
startet Flask mit `debug=True` und damit threaded -- `/api/move/*` und
`/api/ai/move` (`server.py:1571`) koennen gleichzeitig in dieselbe `PyGame`
schreiben. Dazu `server.py:324-336`: `_rust_flush_log` liest
`log_since(_rust_logged)` und setzt danach `_rust_logged = log_len()`;
dazwischen angefallene Zeilen fehlen im Log, das zugleich die Replay-Grundlage
ist.

### 1.7 server.py: `_resolve_difficulty` ignoriert `sims` ohne `model`

`server.py:291-298` nimmt explizite Werte NUR, wenn `model` UND `sims` gesetzt
sind (selbst nachgelesen). `server.py:1497` ruft es mit
`d.get('difficulty','medium')`: ein POST `{"sims": 900}` ohne `model` landet
damit beim Preset `medium` = 60 Sims (`server.py:285`), nicht bei 900. Gleiche
Bauform in `server.py:675`.

### 1.8 server.py: Log-Kopf und Lehrer-Cache

Die Spec-Umgebung wird EINMAL beim Import fuer `_CHAMPION_MODEL` gesetzt
(`server.py:277`), der Log-Kopf zeigt aber
`_resolve_champion_spec(_ai_model)` (`:717-718`): waehlt der Nutzer im Modal
ein anderes Modell, steht dessen Spec-Pfad im Kopf, waehrend die Knoepfe die
des Startup-Champions sind. `/api/ai/config` POST (`:1492-1510`) wechselt das
Modell zur Laufzeit, ohne die Spec neu anzuwenden (Agentenbefund,
stichprobenhaft bestaetigt). Der Lehrer-Cache schluesselt auf
`(log_len, current_player)` OHNE `sims` (`:536`, selbst nachgelesen): eine mit
`_teacher_coach_sims` gerechnete Analyse wird fuer einen spaeteren
`/api/ai/hint` mit `_teacher_sims` wiederverwendet, und ein Modellwechsel
entwertet sie nicht.

### 1.9 Weitere belegte Punkte

- **Train/Val-Split**: deterministisch am festen Seed `20260707`
  (`train.py:1428`, `:1436`), NICHT am `--seed` -- aber er haengt an Inhalt und
  Laenge von `all_files` (`train.py:1212`). Waechst `data/`, ist es eine ANDERE
  Partition, und ehemalige Val-Dateien landen im Training. Schutz nur per
  `MOSAIC_DATA_EXCLUDE`/`--file-list`, und letzteres greift bei `val_frac = 0`
  nicht (siehe 1.1).
- **Resume-Fingerabdruck** (`train.py:1926-1939`) fuehrt u.a.
  `exclude_round5`, `ranking_loss_weight`, `wdl_*`, `points_dist_bins`,
  `conjunction_head`, `cache_file` NICHT -- ein `--resume` mit geaendertem Knopf
  laeuft still weiter (Agentenbefund, Feldliste nicht einzeln nachgeprueft).
- `paired_gating.py:589`: `--promote-winner` steht per CLI auf `True` -- ein
  Ablations-Vergleich setzt bei signifikantem Ausgang ungefragt
  `models/champion.txt`. Bewusst so dokumentiert, bleibt eine Fussangel. Von
  den sechs Pflicht-Kennzahlen liefert das Artefakt direkt nur Punkte
  (`:478-479`) und Strafleiste (`:480-481`); Reihen, Spalten und
  Plattenkriterien gibt es erst ueber `--log-games` (`:584`) plus Fremdsonde.
- `self_play.py:568`: `_chunk_timeout_secs(..., has_model and mode == "mcts")`
  -- im `--mode network` faellt der 207-s-Zuschlag aus
  `_internal_game_timeout_secs` (`:148-149`) weg. Ob gewollt, ist **unklar**;
  praktisch deckelt `MAX_CHUNK_TIMEOUT_SECS = 450` (`:89`) die meisten Faelle.
- `torch.load` uneinheitlich: `weights_only=False` in `train.py:1057` und
  `corpus_dataset.py:906`, ohne das Argument in `train.py:1181`, `:1644` und
  `export_onnx.py:272`.

---

## 2. Tote und ueberholte Pfade

- **Tote Importe in `neural_net.py`** (Rest des Auszugs vom 2026-08-27, selbst
  geprueft): `glob` (:2), `_load_records_fh` (:3), `re` (:10), `math` (:12),
  `pickle` (:13), `statistics` (:14), `Dataset` (:18) sowie
  `REACH_ATOMS`/`reach_columns`/`reach_buffer_columns` (:24-26) und
  `CONJUNCTIONS_PER_PLAYER` (:28, nur noch im Docstring :1194).
- **Tote Importe in `train.py`** (selbst geprueft): `re` (:18, benutzt wird der
  lokale `_re` aus :1222), `subprocess` (:19, wird in :2779 lokal neu
  importiert), `POLICY_TARGET_SHARPEN_EXPONENT` (:165, sonst nirgends).
- **Ungenutzte Parameter**: `_pass(..., carrier_set, carrier_prefixes, ...)`
  in `build_cache_incremental.py:194` (Aufruf :277) benutzt beide nicht mehr,
  seit der Block traegeragnostisch ist.
- **Kein einziges argparse-Flag in `train.py` ist ungelesen** (45 Stueck,
  alle in `:3144-3170` durchgereicht -- Agentenbefund). Per DEFAULT inert sind:
  `--ranking-loss-weight` (0.0, samt `_pairwise_ranking_loss` `:285`),
  `--ownership-weight` (`OWNERSHIP_WEIGHT = 0.0`, `config.py:82`) und alles,
  was daran haengt (`--conjunction-head`, `--ownership-head-2d`,
  `--freeze-trunk`), `--points-dist-bins` (`POINTS_DIST_BINS = 0`,
  `config.py:137`) samt `points_dist_loss` (`:184`) und
  `--reinit-points-head`, `--opp-points-head`, `--endgame-head` sowie die vier
  `--wdl-*`-Knoepfe. Die Cache-Felder dazu werden trotzdem IMMER gebaut
  (`corpus_dataset.py:1515-1525`).
- **rtv**: in `train.py` nur noch Flag-Wert und Kommentar; die Rechnung liegt in
  `corpus_dataset.py:1184-1201`. `VALUE_TARGET_VARIANTS`
  (`neural_net.py:1128`) haelt "default"/"nortv_r1" als reine
  Alt-Reproduktion.
- **`MosaicNet` (flaches Legacy-Netz)**: konstruiert nur noch in
  `neural_net.py:2077` und `export_onnx.py:98`. Der eigentliche Altlast-Punkt
  ist der DEFAULT `--encoder flat` (`train.py:3083`,
  `build_cache_parallel.py:169`, `build_cache_incremental.py:235`,
  `tools/build_cache_serial.py:35`, `tools/window_train_split.py:52`), waehrend
  jeder Champion seit v19 2D ist. Ein vergessenes Flag baut still den falschen
  Korpus.
- **`.pt`-Migrationspfad** `corpus_dataset.py:892-969`: laut eigenem Kommentar
  fuer 2D unerreichbar, fuer flach nur bei Caches aus der Vor-HDF5-Zeit.
- **server.py-Routen ohne Frontend-Aufrufer** (Agentenbefund, Tabelle nicht
  Zeile fuer Zeile nachgeprueft): `/api/debug/replay_log` (:757),
  `/api/tiling/unplaceable` (:1134), `/api/stack/peek` (:1463, legt zudem
  verdeckte Stapelinfo offen), `/api/ai/config` POST (:1492),
  `/api/aggression` (:1538/:1548), `/api/ai/debug` (:1697), `/api/ai/suggest`
  (:1739, abgeloest von `/api/ai/hint`), `/api/teacher/config` (:1763/:1773).
- **`DIFFICULTY_PRESETS`** (`server.py:280-289`): selbst geprueft -- `app.js`
  sendet in `/new_game` IMMER `model` und `sims` (static/js/app.js:272-274),
  also greift in `_resolve_difficulty` stets der Kurzschluss `:292-293`. Alle
  fuenf Presets sind aus der Oberflaeche unerreichbar, `easy` ("heuristic") hat
  gar keinen Weg mehr.

---

## 3. Optimierungspotenzial (nur an Code belegt)

- `train.py` faehrt **ohne AMP, ohne Gradientenakkumulation und mit
  `num_workers = 0`** (kein Treffer fuer `autocast`, `GradScaler`,
  `num_workers` in der Datei -- selbst geprueft; Loader `train.py:1549-1551`).
  `--fast-loader` (`train.py:1537-1546`) umgeht den Collate-Aufwand, ist aber
  Default AUS. Der batchweise Weg dafuer liegt fertig in
  `corpus_dataset.get_batch` (:1791).
- Sieben `.item()`-Aufrufe je Trainingsbatch (`train.py:734-743`) und rund
  fuenfzehn je Val-Batch (`train.py:919-970`) erzwingen je Batch eine
  GPU-Synchronisation; als Tensor akkumulieren und einmal je Epoche abrufen
  spart sie (Agentenbefund, Zeilen stichprobenhaft gesehen).
- `_pairwise_ranking_loss` baut die Paar-Indizes je Batch neu aus
  Python-Listen (`train.py:318-319`) -- gehoert als Buffer ans Modell. Betrifft
  nur den heute toten Ranking-Pfad.
- Doppeltes `torch.load` desselben Checkpoints: `train.py:1181` (nur
  Encoder-Erkennung) und `train.py:1644`.
- `server.py` serialisiert den Zustand je Drafting-Zug zweimal
  (`server.py:901` und `:339`), bei `/api/move/pass` dreimal (`:1063`).
- Der Merge liest jeden Block voll ins RAM (`build_cache_parallel.py:143`,
  `np.array(hf[k])`) statt in Scheiben; bei grossen Feldern ist das die Spitze,
  gegen die der Rest der Funktion ausdruecklich gebaut wurde.

---

## 4. Struktur und Nachvollziehbarkeit

**`train.py` (3.170 Zeilen).** `train()` laeuft von :1076 bis :2705, also
**1.630 Zeilen in einer Funktion**; daneben `_train_one_epoch` (:399-745, 347)
und `_validate_one_epoch` (:748-1005, 258). Brauchbare Naehte, mit der Zahl der
Namen, die darueber gehen (Agenten-Zaehlung, Bereiche selbst gesichtet):

| Bereich | Inhalt | Namen ueber der Naht |
|---|---|---|
| 1076-1201 | Vorab-Validierung, Warmstart-Pruefung | 1 (`load_path`) |
| 1203-1453 | Fensterbau, Manifest, Split, Limit | ~14 |
| 1455-1551 | Datensatz und Loader | ~6 -- **beste Naht** |
| 1553-1697 | Modellbau, Warmstart, Freeze, Optimizer | ~8 -- **gute Naht** |
| 1977-2332 | Epochenschleife | schmal nach innen, breit nach aussen |
| 2447-2705 | Speichern und Export | ~40 Historien-Namen -- **schlechte Naht** |

Empfehlung, falls ueberhaupt geschnitten wird: NUR die beiden guten Naehte
(Datenaufbau und Modellaufbau) in `train_setup.py` ziehen und die Historien in
ein Objekt nach dem Vorbild von `LossSetup` (`train.py:371`) buendeln. Der
Speicherblock lohnt ohne diese Buendelung nicht.

**`server.py` (1.888 Zeilen).** Keine Funktion ueber 150 Zeilen; `new_game`
(:605-754) liegt genau bei 150. Sauberste Schnitte: Anzeige-Kalibrierung
(:1635-1694, **1 Name** nach aussen), Champion/Spec/Difficulty (:144-315,
7 Namen, Zustand nur `os.environ`). Der Lehrer-Block (:357-590) braucht erst
ein Zustandsobjekt (acht Globals gehen hinein), und er hat einen
Schichtbruch: `_teacher_compute_analysis` (:519) ruft
`_calibrate_display_win_prob`, das erst :1671 definiert wird.

**Deutsche Bezeichner** (CLAUDE.md 2026-08-24; `tools/check_conventions.py`
Regel 7 prueft nur NEUE Namen, der Bestand bleibt stehen):
`build_cache_parallel.py` fast durchgehend (`_bau_teilmenge` :50, `dateien`
:55/:176ff, `felder` :98, `formen` :111, `bloecke`/`grenzen` :194-196,
`ergebnisse`/`teile`/`n_zustaende` :206-222, `wand`/`erg`/`ziel` :238-263);
`build_cache_incremental.py` (`n_verschwunden` :208, `--wartezeit` :242,
`--leerlauf-abbruch` :244, Artefaktfeld `dateien` :331);
`corpus_dataset.py` (`ego`/`geg` :1406-1407, :1421-1422),
`reach_target.py:360-361` (`zellen`/`werte`), `neural_net.py:352`
(`_spieler`); `server.py` (`gesetzt`/`ueberstimmt` :261-274, `typ` :372ff,
`rang` und `bester_zug_description` :583-589/:1451/:1863 -- die letzten beiden
sind **Frontend-Vertrag**, app.js:546ff, also nur gemeinsam umbenennbar).
Zu Recht deutsch bleiben `heuristik_variante` (`self_play.py:165`, Feldname der
eingefrorenen pyo3-Signatur) und `laufzeit`/`wanduhr_s` (von CLAUDE.md
vorgeschrieben).

**Kommentar-Chronik, die nach `docs/` gehoert.** `neural_net.py:724-931` sind
rund 200 zusammenhaengende Kommentarzeilen Schema-Historie ("Ab Version 12 ...
Ab Version 16 ..."), die im Code nur noch `VALUE_SCHEMA_VERSION = 20`
begruenden; dasselbe noch einmal in `config.py:58-138` und
`corpus_dataset.py:202-227`. In `train.py` 859 reine Kommentarzeilen
(27 Prozent, Agentenzaehlung), am dichtesten :2039-2109 und :2828-3140
(argparse-Hilfetexte, ueberwiegend Begruendung statt Bedienhinweis); in
`server.py` :1635-1665 (Promotions-Chronik der Platt-Fits). Vorschlag: EIN
`docs/value_target_history.md` mit den Schema-Absaetzen 1-20, im Code je ein
Dreizeiler plus Zeiger.

**Widerspruechliche Docstrings**: `export_onnx.py:25` (76/708 statt 79/755),
`neural_net.py:1193` und `corpus_dataset.py:1395` (Zeiger auf `config.py:117`,
richtig ist :120), `corpus_dataset.py:1712` (Aussage ueber `num_workers` in
einer FREMDEN Datei -- stimmt heute, veraltet beim ersten Loader-Umbau).

---

## 5. Vor Projektende (priorisiert) -- und was bleiben kann

| # | Punkt | Stelle | Aufwand | Risiko |
|---|---|---|---|---|
| 1 | `train_files = all_files` statt `None`, damit `--file-list`/`--extra-data-dir`/`--train-file-limit` auch bei `--val-frac 0` greifen | train.py:1397 | 0,5 h + 1 Probelauf | mittel: aendert den Cache-Schluessel fuer `val_frac=0`-Laeufe (Voll-Neubau), deshalb NUR zwischen zwei Generationen |
| 2 | Datei-Block-Schluessel im Worker bilden (oder `INPUT_SIZE` mitgeben und dort pruefen) | build_cache_incremental.py:200, :127 | 1 h | gering, reine Absicherung |
| 3 | Planes-Kanal-Erweiterung beim Warmstart wie den Flach-Zweig behandeln, sonst laut scheitern statt zufaellig starten | train.py:1630, :1675-1686 | 1,5 h | gering |
| 4 | `_ai_lock` tatsaechlich um Zustandsaenderungen legen (oder loeschen und den Einzelsitzungs-Charakter dokumentieren) | server.py:111, :1571 | 2 h | mittel: beruehrt jeden Move-Endpunkt |
| 5 | `_resolve_difficulty`: `sims` und `model` einzeln respektieren | server.py:291-298 | 0,5 h | gering |
| 6 | Lehrer-Cache-Schluessel um `sims` und Modell erweitern | server.py:536 | 0,5 h | gering, kostet Latenz -- Nutzer-Entscheid |
| 7 | Tote Importe und Parameter entfernen (2.1/2.2, `_pass`-Parameter) | neural_net.py:2-28, train.py:18-165, build_cache_incremental.py:194 | 0,5 h | sehr gering |
| 8 | Stale Docstrings/Zeiger berichtigen (1.6, 4.) | export_onnx.py:25, neural_net.py:1193, corpus_dataset.py:1395 | 0,5 h | keins |
| 9 | `threads` im Laufzeit-Block auf die Workerzahl korrigieren | build_cache_parallel.py:260 | 0,2 h | keins |
| 10 | `conv_layers` in `build_model_from_checkpoint` aus dem Checkpoint ableiten (wie `export_onnx.py:191`) | neural_net.py:2067 | 0,5 h | gering |

**Kann bleiben** (bewusst nicht auf der Liste):

- Die per Default inerten Koepfe und ihre Cache-Felder (2.). Sie sind additiv,
  dokumentiert und ihr Ausbau wuerde jeden Bestands-Cache entwerten -- teurer
  als der Nutzen in ein bis zwei Generationen.
- `MosaicNet` und der `.pt`-Migrationspfad: tragen Alt-Checkpoints, kosten
  nichts im Betrieb.
- Deutsche Bezeichner im Bestand von `build_cache_parallel.py` und der
  `rang`/`bester_zug_description`-Vertrag zu `app.js`: eine Umbenennung ist
  reine Kosmetik mit echtem Bruchrisiko am Frontend.
- `train.py`/`server.py` aufteilen. Die Naehte sind benannt (4.), aber ein
  Schnitt kurz vor Projektende bringt keine Messung und riskiert genau die
  Verhaltensaenderung, die der `MosaicDataset`-Auszug am 2026-08-27 nur mit
  einem Bit-Identitaets-Beleg vermeiden konnte.
- Die Kommentar-Chronik: Auslagern ist richtig, aber nur, wenn jemand das
  Zieldokument wirklich pflegt. Sonst ist der Code die letzte Stelle, an der
  die Begruendungen ueberhaupt noch stehen.
