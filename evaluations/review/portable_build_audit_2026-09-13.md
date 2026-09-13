# Audit: Zustand des portablen Windows-Bundles (2026-09-13)

Auftrag (Nutzer 2026-09-13, 02:30): "ueberpruefen wie funktional unser portable
build ist. seit unserem letzten build hat sich viel getan".

Nur-Lese-Audit, KEIN Bau, KEIN Lauf (exklusive Messung auf der Maschine).
Regel 0: jede Aussage traegt eine Pruefstelle `datei:zeile` oder ist als
Annahme markiert.

**Kurzfassung:** das Bundle waere heute gebaut lauffaehig, spielte aber NICHT
den Champion. Die Spec buendelt noch das v21-Netz, `models/champion.txt` nennt
`v28-b02_brierbest`, und dessen ONNX und Spec-JSON packt niemand ein -- der
Server faellt auf die Heuristik zurueck (`server.py:700-714`), und eine Partie
gegen die Heuristik ist im neuen Elo-Register ungewertet.

---

## Ausgangslage (geprueft)

| Groesse | Wert | Pruefstelle |
|---|---|---|
| Letztes Bundle | `dist/Mosaic-AI_v21_2d_brierbest_20260815.zip`, 40,5 MB gepackt / 88 MB entpackt | `ls dist/`, `du -sm dist/Mosaic-AI` |
| Amtierender Champion | `v28-b02_brierbest` | `models/champion.txt` (Inhalt gelesen) |
| ONNX des Champions | `models/alphazero_v28-b02_brierbest.onnx` vorhanden | `ls models/` |
| Spec des Champions | `models/frozen_champions/v28-b02/spec.json` (432 B, 13 Felder) | Datei gelesen |
| `models/v28-b02_brierbest.spec.json` | existiert NICHT | `ls models/*.spec.json` (20 Treffer, keiner davon) |
| Vertragshash Quellbaum | `39648b95bbba1acf` | `engine/src/lib.rs:2275` |
| Vertragshash Champion-Wheel | `39648b95bbba1acf` | `evaluations/elo_history.csv` Spalte `contract` (v28-b02-Zeilen) |
| `INPUT_SIZE` | 755 (Python) / 755 (Rust) | `config.py:38`, `engine/src/features.rs:18` |
| Champion-Wheel-Artefakt | `mosaic_rust_knobs_20260912.whl`, sha256 `ea980d9f3c0c9556...` | `models/frozen_champions/v28-b02/wheel.sha256` |
| Elo-Anker | `Heuristik_hv4_anchor@150`, Aliase LEER | `tools/elo_tracker.py:147,150,173` |
| Schwierigkeitsstufen | NICHT gebaut, eingetaktet fuer v29 | `evaluations/PREREG_difficulty_levels.md:1` |

---

## (A) Luecken

Schwere: **B** = blockiert Start/Kernfunktion, **F** = Funktion fehlt oder
degradiert still, **K** = kosmetisch.

| # | Schwere | Luecke | Pruefstelle | Fix |
|---|---|---|---|---|
| G1 | **B** | Spec packt `models/alphazero_v21_2d_brierbest.onnx`; `champion.txt` sagt `v28-b02_brierbest`. `_champion_onnx_path` findet nichts, `_load_champion_model` warnt, `new_game` setzt `model_warning` und spielt HEURISTIK. Das Bundle enthaelt dann ein Netz, das niemand laedt. | `dist/mosaic_release.spec:46`; `models/champion.txt`; `server.py:160-164`, `server.py:186-191`, `server.py:700-714` | `dist/mosaic_release.spec:46` auf `alphazero_v28-b02_brierbest.onnx` aendern (11,4 MB). v21-Zeile ersatzlos streichen. |
| G2 | **B** | Die Spec-JSON des Champions wird nicht eingepackt. `_resolve_champion_spec` findet weder `models/v28-b02_brierbest.spec.json` (gibt es nirgends) noch `models/frozen_champions/v28-b02/spec.json` (nicht im Bundle) und meldet "Env-Defaults gelten, das ist NICHT der Champion". Verloren gehen u.a. `envelope_search_c=1.0`, `envelope_projection_mode=1`, `envelope_hull_form=2`, `special_row6_w=1.0`, `score_utility_b=20.0`, `envelope_profile`. | `server.py:237-259`, `server.py:262-267`; `models/frozen_champions/v28-b02/spec.json` | In `dist/mosaic_release.spec` nach Zeile 47 ergaenzen: `datas.append((os.path.join(PROJECT_ROOT,'models','frozen_champions','v28-b02','spec.json'), os.path.join('models','frozen_champions','v28-b02')))` |
| G3 | **F** | Das neue Elo-Register kennt keinen Knoten `Heuristik`. Nur `Heuristik_hv2_generator`, `Heuristik_hv3_generator`, `Heuristik_hv4_anchor` stehen drin, und `ANCHOR_ALIASES` ist seit der Neuverankerung leer. Spielt der Nutzer gegen "heuristic" (bzw. faellt das Bundle wegen G1 dorthin), liefert `estimate_ai_anchor` `(None, True, None)` -- die Partie bleibt ungewertet. Das gilt schon im Repo, nicht erst im Bundle. | `evaluations/elo_history.csv` (Spalten `player_a`/`player_b`, 33 Kanten, kein `Heuristik`); `tools/elo_tracker.py:170-173`; `server.py:768-774`; `player_profiles.py:232-236` | NUTZER-ENTSCHEID noetig. Sauber: den GUI-Heuristik-Pfad als eigenen Knoten vermessen (eine Kante `Heuristik_live@<sims>` gegen `Heuristik_hv4_anchor@150`). Ein blosses Umbiegen von `server.py:768` auf `ANCHOR_NAME` waere eine ungeprueft gleichgesetzte Identitaet (live-hv1 gegen Artefakt hv4) und damit ein Regel-0-Bruch. Solange nichts vermessen ist, ist "ungewertet" das ehrliche Verhalten. |
| G4 | **F** | Asymmetrie im Namens-Rueckfall: `_resolve_champion_spec` schneidet `_brierbest`/`_best` ab, bevor es in `frozen_champions/` sucht; `_champion_onnx_path` tut das NICHT. Die Artefakt-Verzeichnisse heissen seit v24 ohne Suffix (`v24-b07`, `v26-b01`, `v27-b01`, `v28-b02`), nur `v21_2d_brierbest` trug es noch. Folge fuers Bundle: die ONNX MUSS als `models/alphazero_<name>.onnx` mitkommen, ein Einpacken als `frozen_champions/v28-b02/model.onnx` wuerde NICHT gefunden. | `server.py:160-163` gegen `server.py:249-258`; `ls models/frozen_champions/` | In `server.py:160-163` dieselbe Suffix-Abschneidung wie in `server.py:252-256` ergaenzen (und dann beide Fundorte dokumentieren). Nicht Voraussetzung fuer den Build, aber die Falle bleibt sonst stehen. |
| G5 | **F** | Das Bundle uebernimmt das AMBIENT installierte `mosaic_rust` (`binaries=[]`, `hiddenimports=['mosaic_rust', ...]`) -- nicht das eingefrorene Champion-Wheel. Der Champion wurde mit `mosaic_rust_knobs_20260912.whl` (Stand 2026-09-12 06:19) gemessen; danach sind `09bc9c4` (drei Such-Knoepfe), `5fef98d` und `0536aba` in den Baum gegangen, die zwei letzten laut Commit-Titel "(unkompiliert)". Welches Wheel installiert ist, war hier NICHT pruefbar (kein `pip`, kein `python`). Der Vertragshash beantwortet die Frage nicht: er deckt nur `INPUT_SIZE`, `NUM_PLANES_CHANNELS`, `PLANES_H/W`, `NUM_ACTIONS`, `HEADS` ab, keine Knopf-Semantik. | `dist/mosaic_release.spec:52-57`; `git log` (s. Abschnitt B); `engine/src/lib.rs:690-700` | STOPP-PUNKT vor dem Bau: entweder das Artefakt-Wheel in die Bau-Umgebung installieren (sha256 gegen `wheel.sha256` pruefen) oder bewusst mit dem Live-Wheel bauen und das im Zip-Namen/Changelog vermerken. Die neuen Knoepfe stehen nicht in der Champion-Spec, greifen also mit ihren Defaults -- dass diese Defaults bitidentisch sind, ist eine ANNAHME aus den Commit-Titeln, hier nicht nachgemessen. |
| G6 | **K** | `evaluations/elo_history.csv` im Alt-Bundle ist das Register VOR der Neuverankerung vom 2026-09-12 (Segment 2). Ein Rebuild zieht die aktuelle Datei automatisch nach. | `dist/mosaic_release.spec:50`; `tools/elo_tracker.py:140-147` | Kein Eingriff; nur nicht das Alt-Register `archive/elo_history_pre_phantomfix.csv` mit ausliefern. |
| G7 | **K** | `/api/debug/replay_log` importiert `analyze_game_log` dynamisch aus `APP_DIR/tools`; ein `tools/`-Verzeichnis gibt es im Bundle nicht (geprueft am Alt-Bundle). Der Aufruf faellt in `except` und liefert Fehler-JSON, kein Absturz. Debug-Werkzeug, keine Spielfunktion. | `server.py:812-822`; `ls dist/Mosaic-AI/_internal/` (kein `tools`) | Optional: `tools/analyze_game_log.py` als `datas` nach `tools/` plus `hiddenimports`. Oder so lassen und im README nicht erwaehnen. |
| G8 | **K** | `dist/README_GAME.txt:77` spricht von einer KI-Einstellung "Easy"; die GUI hat nur die Felder `ng-model` und `ng-sims`, keine Stufenwahl. Der Rest des Abschnitts (Zeilen 45-61: "no preset difficulty levels yet") stimmt weiterhin, denn die Stufen sind nicht gebaut. | `dist/README_GAME.txt:45-61,77`; `static/index.html:273,279`; `evaluations/PREREG_difficulty_levels.md:1` | Zeile 77 auf die tatsaechliche Bedienung umschreiben ("if you type `heuristic` into the model field"). |
| G9 | **K** | `static/js/app.js:239` faellt auf `'v16_best'` zurueck, wenn `/api/champion` nicht antwortet -- ein Netz, das kein Bundle enthaelt. Reiner Fehlerpfad. | `static/js/app.js:239`; `server.py:872-880` | Fallback auf Leerstring aendern, dann greift serverseitig `_CHAMPION_MODEL`. |
| G10 | **K** | Das Alt-Bundle traegt `numpy` (6 MB) + `numpy.libs` (21 MB) + `cryptography` (10 MB) = 37 von 81 MB `_internal`, obwohl `server.py`, `config.py`, `player_profiles.py`, `run_mosaic.py` und `tools/elo_tracker.py` keines davon importieren (Import-Greps ueber alle fuenf Dateien). Woher PyInstaller sie zieht, ist UNGEPRUEFT. | `du -sm dist/Mosaic-AI/_internal/*`; `tools/elo_tracker.py:79-87`; `player_profiles.py:30-44` | Optional NACH einem gruenen Rauchtest: `'numpy', 'cryptography'` in `dist/mosaic_release.spec:61-68` aufnehmen, erneut bauen, Rauchtest wiederholen. Bei Fehler zuruecknehmen -- Groesse ist kein Grund, ein Risiko einzugehen. |
| G11 | **K** | `LOG_DIR` (`_internal/static/log`) und `ELO_LOG_DIR` werden beim Import angelegt; `player_profiles.json` entsteht zur Laufzeit neben der EXE-Nutzlast. Entpackt der Empfaenger nach `C:\Program Files\...`, schlaegt schon der Import fehl. `README_GAME.txt:10` sagt "unpack anywhere you like". | `server.py:97-103`; `player_profiles.py:51-57`; `dist/README_GAME.txt:10` | README-Satz um "not into Program Files" ergaenzen. Alt-Verhalten, unveraendert seit dem letzten Bundle. |
| G12 | -- | KEINE Luecke, bewusst geprueft: `player_profiles.json` steht unter git-crypt und ist in `datas` NICHT enthalten. Es entsteht erst zur Laufzeit im Bundle-Verzeichnis. Kein Klartext-Leck. Nebeneffekt: mit jedem neuen Bundle sind die lokalen Spielerprofile/Ratings des Empfaengers weg. | `.gitattributes`; `dist/mosaic_release.spec:35-50`; `player_profiles.py:52` | Nichts zu tun. Ggf. im README erwaehnen, dass `player_profiles.json` vor einem Update gesichert werden kann. |

**Umgekehrte Richtung (eingepackt, aber nicht mehr gebraucht):**
`dist/mosaic_release.spec:46` -- `alphazero_v21_2d_brierbest.onnx` (9,2 MB) wird
vom Server nicht mehr angesprochen, sobald `champion.txt` auf v28-b02 zeigt.
Die Datei bleibt zwar ladbar (Alt-ONNX werden auf die Modellbreite gekuerzt,
`engine/src/net.rs:418-426` und `:438-444`), aber niemand fragt sie nach.
Streichen.

**Keine Luecke bei static/:** `collect_static_datas()` laeuft ueber den ganzen
Baum ausser `static/log` (`dist/mosaic_release.spec:19-32`); der Baum enthaelt
heute genau `css/style.css`, `js/app.js`, `index.html`, `debug.html`. Alle
GUI-Commits seit dem 2026-08-15 landen dadurch automatisch im Bundle. Der
Server nutzt keine Jinja-Templates -- beide Seiten kommen ueber
`send_from_directory` (`server.py:615-622`), ein `templates/`-Verzeichnis wird
nirgends gebraucht.

**Launcher passt weiterhin:** `dist/run_mosaic.py:50` importiert `server`,
`:65` startet `server.app.run(host=127.0.0.1, port=<frei>, use_reloader=False)`.
Der Server-Block in `server.py:1914-1923` ist `__main__`-only und wird dabei
nicht durchlaufen, der Reloader-Knopf `MOSAIC_SERVER_RELOAD` (Commit a4e1fb0)
ist fuer das Bundle also folgenlos. Pfadableitung: `server.py:55-58` und
`config.py:9-12` nehmen beide `sys._MEIPASS` -- konsistent, unveraendert.

---

## (B) Relevante Commits seit dem letzten Bundle (2026-08-15)

Vollstaendige Liste: `git --no-pager log --since=2026-08-15 --date=short
--format=%h_%ad_%s -- server.py static/ templates/ dist/ tools/build_release.py
engine/py/ config.py` (73 Commits). Hier die, die Bundle-Inhalt oder Start
betreffen.

**Champion, Modell und Spec (der Kern des Audits)**

| Commit | Datum | Wirkung auf das Bundle |
|---|---|---|
| `7d72f46` | 09-12 | Promotion v28-b02: `champion.txt` und die Platt-Anzeigekurve `server.py:1701-1702` (A=-0,0539, B=0,6684) -- damit ist G1/G2 entstanden. |
| `3d22e54` | 09-10 | Promotion v27-b01 (Zwischenstand derselben Kette). |
| `d37e093` | 09-09 | Promotion v26-b01. |
| `ae2f9f0`, `0e87ddd` | 09-04 | Promotion v23-b01: Projektions-Modus wird Spec-PFLICHTFELD, der Server uebernimmt die Champion-Spec in die Umgebung (`server.py:196-289`). Ab hier ist die Spec-Datei Bundle-relevant. |
| `97343c9` | 09-10 | Spec-Rueckfall auf das eingefrorene Artefakt (`server.py:237-259`) -- der Grund, warum heute `frozen_champions/v28-b02/spec.json` die zu buendelnde Datei ist. |
| `e05d74a` | 08-29 | Champion-Aufloesung mit Frozen-Artefakt-Fallback (`server.py:144-164`) -- traegt die Suffix-Asymmetrie G4. |
| `27debeb` | 09-07 | `envelope_hull_form` auf seinen Env-Knopf. |
| `09bc9c4` | 09-12 | Drei Such-Knoepfe im Wheel (Rundenschaetzer K4, Rueckgabe-Reihenfolge, Startslot) -- `_SPEC_TO_ENV` waechst auf 18 Felder. |
| `5fef98d` | 09-12 | Startkuppel-Streuung und Such-Start, laut Titel **unkompiliert**. |
| `0536aba` | 09-12 | hv3-Lehrer portiert, laut Titel **unkompiliert**. |
| `4133ae7` | 09-11 | `INPUT_SIZE` 744 -> 755, Rust-Merkmalsexport. Alt-ONNX bleiben spielbar (Kuerzung auf Modellbreite, `engine/src/net.rs:418-426`). |
| `8ab2ecb` | 09-08 | Anzeigekurve auf v25-b01 -- durch `7d72f46` ueberholt. |

**Elo/Wertung**

| Commit | Datum | Wirkung |
|---|---|---|
| `8b141ea` | 09-09 | Blockname als Rueckfall im KI-Anker (`player_profiles.py:161-174`) -- der Grund, warum `v28-b02_brierbest` heute den Leiterknoten `v28-b02@400` trifft. |
| `1ca379f` | 09-09 | Ungewertete Partien nennen ihren Grund -- macht G3 im Bundle wenigstens sichtbar. |

**Start/Betrieb**

| Commit | Datum | Wirkung |
|---|---|---|
| `a4e1fb0` | 08-29 | Auto-Reloader Default aus (nur Dev-Pfad, Bundle unberuehrt). |
| `b352b52` | 08-19 | `sys.path`-Fix im Server (`server.py:43-45`), GUI-Texte ohne lange Bindestriche. |

**Engine (wirkt ueber das Wheel, nicht ueber `datas`)**
`c83fb35` (08-20, round5-Zugsortierung knotenlokal), `1ae77a0` (09-07, K5),
`e91cd34`/`29fb1f1` (08-25/08-27, neue Netz-Eingaben), `7220923` (09-11,
K3-D + Jokerfeld-Knopf), `2a0cf4b` (09-12, Code-Abschluss Stufe 1).

**Reine GUI (automatisch im Bundle, kein Spec-Eingriff)**
`dbd7093`, `625937c`, `1466a1b`, `7f4d523`, `094480d`, `af9eb71`, `7277031`,
`f9225c8`, `bbdbcb0`, `6712aa4`, `76ec95e`, `449e9e2`, `45d67f5`, `4f51466`,
`6e157ac`, `ad9a4bb`, `94b9090`, `a1d9d9c`, `0f67b3e`, `4452c60`, `bf1ed0f`,
`1b2b5ef`, `47d36f7`, `266e29c` -- Tiling-Gesten, Chip-Reihen, Haptik,
Plattendarstellung, Stapel-Dialog.

**Doku**
`be27723` (09-10) aendert `docs/engine_manual.md` (Regelentscheid: Ziehen bei 0
bleibt gratis). Der Bundle-Kopie vom 2026-08-15 fehlt das; `copy_docs()` zieht
sie beim Rebuild automatisch nach (`tools/build_release.py:75-82`).

---

## (C) Bau- und Rauchtestplan fuer die freie Maschine

Ein PyInstaller-Lauf ist Volllast ueber viele Kerne und faellt unter die
Exklusivitaetsregel (CLAUDE.md, "Messungen laufen EXKLUSIV -- und ein Build ist
Nebenlast"). **Erst starten, wenn die Maschine frei ist und der Staffelstab
angesagt wurde.**

### Schritt 0 -- STOPP-PUNKT: welches Wheel soll ins Bundle? (G5)

```powershell
python -c "import mosaic_rust,json;print(json.loads(mosaic_rust.engine_config_json())['contract_hash'])"
```

Erwartung `39648b95bbba1acf`. Das belegt nur die Vertragsgroessen, NICHT die
Knopf-Semantik. Entscheidung des Nutzers:

- **(a) Artefakt-Wheel** aus `models/frozen_champions/v28-b02/` installieren
  (sha256 gegen `wheel.sha256` pruefen: `ea980d9f3c0c9556...`). Das ist der
  Stand, auf dem der Champion gemessen wurde.
- **(b) Live-Wheel** verwenden und im Changelog/Zip-Begleittext festhalten,
  dass das Bundle auf einem spaeteren Engine-Stand laeuft als die Elo-Zahl.

### Schritt 1 -- Spec anpassen (`dist/mosaic_release.spec`)

Zeile 46 ersetzen und eine Zeile ergaenzen:

```python
# Champion-Stand 2026-09-13: v28-b02_brierbest (Elo 1296, Leitersegment 2).
datas.append((os.path.join(PROJECT_ROOT, 'models', 'alphazero_v28-b02_brierbest.onnx'), 'models'))
datas.append((os.path.join(PROJECT_ROOT, 'models', 'champion.txt'), 'models'))
# Ein Champion ist Modell PLUS Spec (server.py::_resolve_champion_spec): ohne
# diese Datei gelten Env-Defaults, und das ist NICHT der Champion.
datas.append((os.path.join(PROJECT_ROOT, 'models', 'frozen_champions', 'v28-b02', 'spec.json'),
              os.path.join('models', 'frozen_champions', 'v28-b02')))
datas.append((os.path.join(PROJECT_ROOT, 'evaluations', 'elo_history.csv'), 'evaluations'))
```

Den ueberholten v16/v21-Kommentarblock (`dist/mosaic_release.spec:37-45`) im
selben Zug auf den neuen Stand bringen.

Optional im selben Zug: `dist/README_GAME.txt:77` (G8) und
`static/js/app.js:239` (G9).

### Schritt 2 -- Bauen

```powershell
python tools/build_release.py
```

Erwartete Ausgabe: `[1/4]` ... `[4/4]`, dann eine Kasten-Zusammenfassung mit
`dist/Mosaic-AI` und `dist/Mosaic-AI_v28-b02_brierbest_20260913.zip`
(Name entsteht aus `champion.txt` + Datum, `tools/build_release.py:86-96`).
Der Zip-Name ist damit der erste Stopp-Punkt: er muss den Champion nennen, den
das Bundle wirklich spielt.

Dauer: **ANNAHME** 3-8 Minuten (das Alt-Bundle hat 88 MB entpackt; gemessen ist
nichts, `tools/build_release.py` schreibt keine Laufzeit). Wer die Zahl fuer
die naechste Sitzung haben will, misst sie mit und traegt sie in STATUS.md
"Laufzeiten (gemessen)" nach. Keine Pipe, keine Umleitung.

### Schritt 3 -- Start des Bundles

```powershell
dist\Mosaic-AI\Mosaic-AI.exe
```

**Erfolg belegen anhand der Konsole (Reihenfolge wie beim Import):**

1. KEIN `⚠️  WARNUNG: Champion-ONNX zu 'v28-b02_brierbest' fehlt` (`server.py:187`).
2. KEIN `⚠️  KEINE Spec fuer Champion v28-b02_brierbest gefunden` (`server.py:265`).
3. Genau eine Zeile `Champion-Spec spec.json: MOSAIC_IMPLICIT_MINIMAX_A=0.0, ...,
   MOSAIC_ENVELOPE_SEARCH_C=1.0, MOSAIC_ENVELOPE_PROJECTED=1,
   MOSAIC_ENVELOPE_HULL_FORM=2, MOSAIC_SPECIAL_ROW6_W=1.0` (`server.py:284`).
   13 Felder, denn `spec.json` traegt 13 (die fuenf optionalen Knoepfe
   `dead_cell_w`, `out_wild_w`, `round_est_*`, `return_order_mode`,
   `start_by_search` fehlen dort und bleiben auf Engine-Default).
4. KEIN `WARNUNG: Elo-Anker-Tabelle konnte nicht geladen werden` (`server.py:133`).
5. `Spiel läuft unter: http://127.0.0.1:5000` (`dist/run_mosaic.py:57`).

### Schritt 4 -- Rauchtest im Browser

| # | Handgriff | Erfolgsbeleg | Pruefstelle |
|---|---|---|---|
| 1 | `http://127.0.0.1:5000/` oeffnet | Spielbrett laedt, keine 404 auf `css/style.css`, `js/app.js` | `server.py:615-617` |
| 2 | `GET /api/champion` | `{"ok":true,"model":"v28-b02_brierbest"}` | `server.py:872-880` |
| 3 | Neues-Spiel-Modal oeffnen | Feld "Modell-Version" ist automatisch auf `v28-b02_brierbest` gefuellt, Sims 400 | `static/js/app.js:165-168`, `static/index.html:273,279` |
| 4 | Profil anlegen, Spiel gegen KI starten (Sims 400) | Antwort OHNE `warning`, `ai_model` = `v28-b02_brierbest` | `server.py:750-751` |
| 5 | KI-Elo-Badge | `ai_rating.node` = `v28-b02@400`, `is_estimate` = **false** (exakte Kante, kein "~") | `player_profiles.py:182-184`; `evaluations/elo_history.csv` (v28-b02@400-Kanten) |
| 6 | Logkopf `_internal\static\log\game_*.log` lesen | `"champion_spec": "models\\frozen_champions\\v28-b02\\spec.json"` und `"knobs"` mit den Spec-Werten | `server.py:735-741` |
| 7 | Startkachel setzen, ein Menschen-Zug, ein KI-Zug | KI zieht ohne 500er, Zugdauer im Sekundenbereich | `server.py:1602` |
| 8 | Tiling-Phase und Rundenwechsel einmal ganz durchspielen | keine Exception in der Konsole | `server.py:1102-1201` |
| 9 | Partie zu Ende spielen, `/api/end_scoring` | Partie wird GEWERTET (Rating veraendert sich), nicht "ungewertet" | `server.py:1416` |
| 10 | "📄 Log"-Knopf | Datei laedt ueber `/static/log/...` | `server.py:901-910` |
| 11 | Lehrer-Modus Stufe 2, ein Tipp | Hint kommt, Partie wird als "ungewertet" markiert | `server.py:1829`, `server.py:677-678` |
| 12 | `http://127.0.0.1:5000/debug` | Debug-Seite laedt | `server.py:620-622` |
| 13 | Ordnerinhalt | `README_GAME.txt` und `engine_manual.md` liegen neben der EXE, Manual traegt den Regelentscheid aus `be27723` | `tools/build_release.py:75-82` |

**Gegenprobe fuer G3 (optional, aber aufschlussreich):** ein zweites Spiel mit
`heuristic` im Modellfeld starten. Erwartung nach heutigem Code: KEIN KI-Elo,
Partie ungewertet mit Begruendung. Wenn das so eintritt, ist G3 bestaetigt; wenn
nicht, ist meine Lesart von `evaluations/elo_history.csv` falsch und gehoert
korrigiert.

Dauer Rauchtest: **ANNAHME** 20-30 Minuten (eine ganze Partie).

### Schritt 5 -- STOPP-PUNKT vor der Weitergabe

Der Nutzer entscheidet:

- Zip-Name `Mosaic-AI_v28-b02_brierbest_20260913.zip` so behalten?
- Wheel-Variante (a) oder (b) aus Schritt 0 -- und steht das irgendwo, wo der
  Empfaenger es sieht?
- Weitergabe erst nach gruenem Punkt 5 und 9 der Tabelle: ein Bundle, das die
  Partie nicht wertet oder nicht den Champion spielt, ist kein Release.
- Das alte `dist/Mosaic-AI_v21_2d_brierbest_20260815.zip` (40,5 MB) loeschen
  oder behalten? Nur nach ausdruecklicher, pfadgenauer Freigabe.

---

## (D) Was nicht geprueft werden konnte

1. **Welches `mosaic_rust` installiert ist.** `pip`/`python` waren im Auftrag
   gesperrt, und site-packages liegt ausserhalb des Projektordners. Damit ist
   G5 offen: Version, Baudatum und Knopf-Semantik des Wheels, das der Build
   einsammeln wuerde, sind unbekannt. Schritt 0 des Plans schliesst das.
2. **Ob PyInstaller `tools.elo_tracker` heute noch einsammelt.** `tools/` hat
   kein `__init__.py` (Namensraum-Paket), `player_profiles.py:39` importiert
   aber `from tools.elo_tracker import ...`. Beim Build vom 2026-08-15 hat es
   funktioniert (Commit-Text `a8be83a`: "gewertetes KI-Spiel (Anker 1256
   estimate)"), und im Alt-Bundle gibt es folgerichtig kein `tools/`-Verzeichnis
   -- der Code steckt im PYZ. Das ist ein PRAEZEDENZFALL, kein Beweis fuer heute;
   Punkt 5 des Rauchtests prueft es.
3. **Ob der 755er Champion im GUI-Pfad wirklich laedt und zieht.** Kein Lauf
   moeglich. `Net::load_auto` bestimmt das Layout aus der ONNX-Datei
   (`engine/src/net.rs:104-130`), ein Breitenkonflikt wuerde sich erst beim
   ersten Forward-Pass zeigen.
4. **Groesse und Startzeit des neuen Bundles.** Alle Zahlen in diesem Bericht
   stammen vom Bundle des 2026-08-15.
5. **PyInstaller- und Python-Version der Bau-Umgebung.** Aus dem Alt-Bundle
   laesst sich nur `python314.dll` ablesen, also Python 3.14 zum Bauzeitpunkt.
   Ob das heute noch die aktive Umgebung ist: ungeprueft.
6. **GUI-Bedienung gegen README/Manual am Bildschirm.** Die GUI-Commits seit
   dem 2026-08-15 (Tiling-Gesten getauscht, Reihen-Klick uebergibt an die KI,
   Pass-Zeile) sind nur ueber ihre Commit-Titel beurteilt, nicht gespielt.
   `README_GAME.txt` beschreibt die Bedienung ohnehin nur grob (Start,
   Beenden, Log, Lehrer-Modus) und wird davon vermutlich nicht falsch --
   das ist eine ANNAHME.
7. **Woher `numpy` und `cryptography` im Bundle stammen** (G10). Kein
   Import-Pfad in den vier Einstiegsdateien gefunden; die Ursache bleibt offen.
