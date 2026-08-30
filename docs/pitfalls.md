# Fallen (aus echten Vorfaellen)

**Kanonischer Ort seit 2026-08-28** (aus STATUS.md entflochten, Nutzer-Hinweis:
STATUS ist kein Langzeitgedaechtnis); Herkunft der Inhalte: STATUS-Stand
2026-08-28. Wer aendert, aendert HIER -- STATUS.md verweist nur noch.

Jeder Eintrag ist ein VORFALL, keine Vermutung: er ist einmal passiert und hat
Zeit oder eine Messung gekostet. Wo daraus eine stehende Regel geworden ist,
steht sie in `../CLAUDE.md`; hier steht die Herkunft, die sie glaubwuerdig
macht. Wer eine Falle ergaenzt, nennt Datum und Schaden.

- **paired_gating-Default BLOCK_SIZE=25 widerspricht der etablierten
  Blockgroesse 5** (2026-08-29, vom Nutzer im laufenden b05-Gating
  abgefangen; Schaden: ein angerechneter Erstblock, neu gestartet).
  Der Seed faellt JE BLOCK (`paired_gating.py`: `base_seed + block_idx *
  1_000_000`), alle Paare eines Blocks teilen also die Spiel-Population
  (Block-Korrelations-Lehre 2026-08-04). Mit dem Default gaebe es bei
  200 Paaren nur 8 unabhaengige Bloecke; die Praezedenz-Gatings liefen
  mit `--block-size 5` (Champion-Gating 2026-08-07: 37 Bloecke a 5).
  Behoben am selben Tag (Nutzer-Entscheid): der Default ist seit
  2026-08-29 `BLOCK_SIZE = 5`.
- **CPU-Nebenlast verstuemmelt Arena-Partien** (2026-08-20). Derselbe
  8-Partien-Smoke lieferte unter Last zwei verschiedene Ergebnisse (eine
  Partie endete 3:1), ohne Last dreimal byte-identisch. **Arena-Messungen
  laufen EXKLUSIV** -- keine zweite Arena, keine Sonde mit Suchlauf, kein
  Training, auch kein `cargo`-Lauf. Determinismus-Checks zaehlen nur unter
  denselben Lastbedingungen wie die Messung.
  Regel dazu: `CLAUDE.md`, Abschnitt "Messungen laufen EXKLUSIV -- und ein
  Build ist Nebenlast".
- **"Erste N je Datei" ist ein stiller Rundenfilter** (2026-08-25). Sonden,
  die je Datei die ersten N qualifizierenden Datensaetze nehmen, ziehen
  Fruehspiel-Stellungen -- Datensaetze stehen in Zugreihenfolge.
  `floor_action_aversion_gate.py` hatte dadurch 268 von 280 Stellungen in
  Runde 1 und ein daraus abgeleitetes Verdikt, das nur fuer Runde 1 galt;
  repariert (`rounds=`/`seed=`, Bestandsauswahl byte-identisch erhalten).
  **Gleiches Muster, gleiche Wirkung, NICHT repariert:
  `long_row_init_knob_effect.py` misst ausschliesslich Runde 1** (alle 240
  Stellungen). Gegenprobe: `long_row_prior_gate.py` hat dasselbe Muster, aber
  einen groesseren Deckel und ist unauffaellig (12/105/82/61) -- die Falle
  haengt am Verhaeltnis Deckel zu Trefferdichte.
- **Jede .py-Aenderung im Baum startet den Spielserver neu -- auch eine, die
  er nie importiert** (2026-08-29, 23:21:45; Schaden: die laufende
  Mensch-gegen-Netz-Partie des Nutzers wurde mitten im Spiel unterbrochen,
  eine Doku-Berichtigung an einer SONDE hat gereicht). `server.py:1656` ruft
  `app.run(debug=True, port=5000)`, damit laeuft der Werkzeug-Reloader.
  Belegkette, gemessen: PID 22944 ist der Reloader-Waechter (seit 23:11:36),
  sein Arbeits-Kind wurde um 23:21:45 durch PID 29076 ersetzt; die mtime von
  `tools/probes/column_completion_legality_probe.py` ist auf die Sekunde
  dieselbe, und ab 23:23:30 laeuft ein neues Spiellog. Die Datei wird von
  `server.py` NICHT importiert (gegengeprueft, kein Treffer), `watchdog` ist
  NICHT installiert.
  **Gegenprobe im selben Zeitfenster:** eine Aenderung an dieser Datei hier
  (`docs/pitfalls.md`, 23:19:28) hat KEINEN Reload ausgeloest -- das Kind von
  23:11:36 lief unveraendert weiter. `.md`/`.json` sind unbedenklich, `.py`
  ist es nicht.
  Mechanismus HERGELEITET, nicht geprueft (die Werkzeug-Quellen liegen
  ausserhalb des Projektordners, dort wird nicht nachgelesen -- Nutzer-Regel
  2026-08-28): der Stat-Reloader beobachtet ueber `sys.path` offenbar den
  ganzen Baum, und `sys.path[0]` ist das Projektverzeichnis.
  Regel daraus, zwischen parallelen Sitzungen abgestimmt: **solange eine
  Server-Partie laeuft, keine `.py`-Aenderung irgendwo im Projektbaum** --
  auch keine reine Kommentar- oder Docstring-Korrektur. Wer eine plant,
  fragt vorher, ob gespielt wird.
  Entschaerft am selben Abend (Nutzer-Auftrag, Commit a4e1fb0): der Reloader
  ist per Default aus, Opt-in ueber `MOSAIC_SERVER_RELOAD=1`, `debug=True`
  bleibt fuer Tracebacks. **Die Entschaerfung hat sich beim Einbau selbst
  vorgefuehrt**: der Edit an `server.py` loeste um 23:38:15 den naechsten
  Reload aus (Kind 29076 durch 32316 ersetzt, Waechter 22944 unveraendert).
  Sie wirkt erst nach einem MANUELLEN Serverneustart -- ob der noch laufende
  Waechter von 23:11 bis dahin weiter watcht, ist NICHT geprueft (waere nur
  durch eine absichtliche `.py`-Aenderung pruefbar, und die verbietet sich
  bei laufender Partie).
  **Sperre aufgehoben am 2026-08-30, am Code geprueft:** `use_reloader`
  haengt an `MOSAIC_SERVER_RELOAD == "1"` und geht so an `app.run`
  (server.py:1775/1778) -- ohne die Variable ist der Reloader AUS. Der
  manuelle Neustart ist am 2026-08-30 erfolgt (STATUS). `.py`-Aenderungen
  bei laufender Partie sind damit wieder unkritisch, solange der Server
  ohne diese Variable laeuft. Die oben genannte Fundstelle `server.py:1656`
  ist der Stand des Vorfalls und beschreibt nicht mehr den heutigen Code.
- **Der Replayer raet die Chip-Auswahl -- und raet sich Partien kaputt**
  (2026-08-29, an `static/log/game_20260823_085652_seed546483.log`; Schaden:
  eine Mensch-Referenzpartie galt als unreplaybar, die Orakel-Messung lief
  auf 11 statt 12 Partien). Symptom: `ValueError: Reihe 6 nicht mit Chips
  komplettierbar` (`engine/src/py.rs:343`) mitten in einer Partie, deren Zug
  real gespielt und geloggt wurde.
  Ursache ist eine Pfad-Asymmetrie, KEINE Engine-Aenderung: die KI waehlt
  ihre Chip-Allokation exakt (`py.rs:911` -> `apply_bonus_chips_with`,
  `round_end.rs:590`, beliebige gueltige Teilmenge), der Replayer spielt
  JEDE geloggte Vollendung -- auch die der KI -- ueber den Menschen-Einstieg
  `apply_tiling_chips` (`analyze_game_log.py:926`), und der ist GREEDY
  (`round_end.rs:458` -> `:525` -> `:487`: ohne zwei farbgleiche nimmt er
  `pool.iter().take(3)`, die ersten drei der Hand). Die 🎫-Logzeile
  (`py.rs:925`) nennt nur die Reihe, nie die verbrauchten Chips -- die
  Divergenz ist damit UNSICHTBAR und schlaegt erst Runden spaeter zu.
  Nachgerechnet an der Partie: greedy verbrennt in R2 den Chip
  türkis+gelb, dem in R4 der zweite gelb-Traeger fehlt (3 statt 2 Chips
  bezahlt), und in R5 fehlt der KI genau ein Chip fuer Reihe 6 (Hand
  4 Chips, davon 1 rot-tragend, 2 fehlende Zellen -> unter
  `chips_complete`, `round_end.rs:514`, unmoeglich). Mit freier
  Allokationswahl ist dieselbe Partie unter der HEUTIGEN Regel vollstaendig
  konsistent (erschoepfende Suche ueber alle drei KI-Vollendungen).
  Mehrzellige Vollendungen sind normal, nicht der Ausloeser: ueber die 13
  Server-Logs 36x eine fehlende Zelle, 10x zwei, 1x drei.
  **Wer diese Abbrueche zaehlt, darf sie in DIESER Partie nicht
  `maybe_silent_chip_complete` zuschreiben** -- der stille Pfad hat hier
  nachweislich NICHT ausgeloest, der Abbruch kommt aus dem regulaeren
  `apply`-Pfad.
  **Diese Zuschreibung gilt aber NUR fuer Logs mit 🎫-Zeilen** (Mensch- und
  Server-Partien). Nachgemessen am 2026-08-30 an 20 Arena-Partien aus
  `paired_arena_env_imm_netvnet.json`: dort laufen **alle** Chip-Vollendungen
  still (in den drei abbrechenden Partien 14 stille, 0 geloggte), denn der
  KI-Pfad loggt nicht -- die Abbrueche kommen dort also sehr wohl aus
  `maybe_silent_chip_complete`. Die Korrektur vom 2026-08-29 war fuer die
  eine untersuchte Partie richtig und als PAUSCHALE Aussage falsch; die
  gemeinsame Ursache ist nicht der Einstieg, sondern das Raten
  (`greedy_chip_indices`) hinter BEIDEN.
  Repariert am 2026-08-30 (Commit cf53aab): `apply_tiling_chips_with` wendet
  eine explizite Auswahl an, `chip_allocations_json` zaehlt die zulaessigen
  auf -- die Regel bleibt in der Engine, der Replayer waehlt nur aus und
  faehrt ohne Plan weiter greedy (Bestandsverhalten). Bei einem Fehlschlag
  sucht er rueckwaerts, orakelfrei, und laeuft dann einmal in voller
  Bestueckung. Abnahme: 14 von 14 Server-Logs, vorher 13.
  **Zwei Dinge bleiben stehen.** Erstens ist die rekonstruierte
  Chip-Historie eine PLAUSIBLE, nicht die tatsaechliche -- sie erfuellt
  dieselbe Regel und dasselbe Log, aber welche Chips real lagen, gibt das
  Log nicht her; relevant, weil das Netz Chips als Merkmal sieht
  (`features.rs`). Zweitens erbte das nur, wer ueber `run()` geht.
  **Beide offenen Enden am 2026-08-30 nachgezogen** (zweiter Punkt erledigt,
  erster bleibt eine Eigenschaft der Rekonstruktion und kein Fehler):
  `tools/probes/column_completion_legality_probe.py::replay_arena_game` baut
  `Replayer`/`_run_loop` nicht mehr selbst, sondern faehrt
  `_replay_once`/`_search_chip_plan` -- DIESELBEN Funktionen wie `run()`,
  nur mit `header`/`lines` aus dem Arena-Adapter statt aus `load_log` (`run()`
  selbst ist datei-basiert und fuer Arena-JSON nicht nutzbar).
  Das allein reichte NICHT: die Plan-Suche hing nur an `apply_chip_completion`,
  also am geloggten Pfad, und Arena-Partien haben davon keinen einzigen
  (siehe Messung oben). Darum haengt jetzt auch `maybe_silent_chip_complete`
  am selben `chip_plan` -- ohne Plan-Eintrag weiter greedy, Bestandsverhalten
  byte-gleich, nur der Fehlerfall bekommt eine zweite Chance. Der Logtext
  beider Engine-Einstiege ist zeichengleich (`py.rs:353` vs `:398`), die
  Zeilen-Gegenprobe sieht den Unterschied also nicht.
  Abnahme: dieselben 20 Arena-Partien 17 -> **20 von 20** (gerettet: seeds
  1000, 1006, 1015); `static/log/*.log` ueber `run()` weiterhin 12 von 12,
  und `game_20260823_085652_seed546483` findet unveraendert den Plan
  `{0: [0, 2, 3]}` -- die Abnahme aus cf53aab bleibt bitgleich.
- **Python schreibt auf Windows still CRLF** (2026-08-25). Ein Skript mit
  `write_text` wandelte in 137 Dateien LF in CRLF; in einer Datei waren das
  971 Byte Zuwachs bei zwei geaenderten Zeilen. `git diff` zeigte wegen der
  Normalisierung weiter zwei Zeilen -- aufgefallen ist es nur an der
  Datei-Groessen-Ratsche. Wer so ein Skript schreibt: `newline` auf LF setzen.
- **Totes Wheel: Zahlengleichheit bei gleichen Seeds ist ALARM** (2026-08-25).
  Eine gepaarte 200-Partien-Arena lieferte NULL diskordante Paare, Block fuer
  Block identisch. Das war kein "kein Effekt", sondern ein Wheel ohne den
  gemessenen Knopf: Wheel 13:14, Knopf-Einbau 13:28. Neun Minuten Messzeit auf
  totem Code. Wer einen Knopf misst, prueft VORHER, ob das installierte Modul
  ihn kennt -- und zwar mit `knob_registry_json()`, nicht mit
  `engine_config_json()`: letzteres listet nur ausgewaehlte Werte und meldete
  auch nach korrektem Neubau "nicht bekannt". **Ein negatives Ergebnis aus
  einem ungeprueften Instrument ist kein Befund.**
- **Prereg-Koepfe veralten gegen ihren eigenen Koerper** (2026-08-25, zweimal
  an einem Tag). `PREREG_chance_nodes` behauptete ein Merkmal, das es nicht
  gibt; `PREREG_heuristic_v2_long_rows` fuehrte par.11 als "ungemessen",
  waehrend par.11.1 laengst das Ergebnis trug. Beide Male hat der Kopf einen
  Leser in die Irre gefuehrt. Die Pflegeregel ist nicht Kosmetik.
  Regel dazu: `CLAUDE.md`, Abschnitt "Prereg-Statuskopf und Index".
- **Wheel nach Engine-Aenderung neu bauen.** `cargo test` gruen heisst nicht,
  dass Python den neuen Code sieht. `maturin develop` scheitert hier (kein
  Virtualenv); der Weg ist `maturin build --release` plus
  `pip install --force-reinstall --no-deps`.
- **Backticks in doppelten Quotes** werden von der Shell ausgefuehrt --
  Markdown-Code-Spans verschwinden spurlos aus Text, der ueber `python -c`
  oder `git -m` geschrieben wird. Heredoc mit einfachen Quotes benutzen.
- **Ein fehlendes Flag meldet sich nicht -- es ist ein Default** (2026-08-26).
  In drei Reproduktionslaeufen fehlte `--heuristik-variante hv2`; der
  Default ist `hv1` (`self_play.py`). Gemessen wurde `hv1` gegen einen
  `hv2`-Korpus, der falsche Befund wurde committet (`b54b41d`) und an die
  Parallelsitzung gemeldet. Der Kontrollmechanismus war da: `self_play.py`
  schreibt `cli_args` ins Manifest neben die Daten. **Regel daraus: vor der
  Auswertung das erzeugte Manifest gegen das Referenz-Manifest halten.**
- **Die falsche Referenz ist so teuer wie die falsche Messung** (2026-08-26).
  Das Anker-Tor wurde zuerst gegen `play_arena_game` gemessen statt gegen
  `unified_game_loop` -- Ergebnis 0/6 und die Fehldeutung "die Umstellung
  verschiebt den Anker". Es gibt DREI In-Process-Pfade, und nur einer traegt
  den Anker (siehe `architecture_reference.md`).
- **Aus dem Vorhandensein eines Feldes folgt nicht seine Wirksamkeit**
  (2026-08-25/26, fuenfmal an einem Tag). `tiling_net: Some(net)` heisst nicht
  "das Netz steuert das Tiling"; `--heuristik-variante` in der Signatur heisst
  nicht, dass die Variante ankommt; "kein Schreiber im Baum" heisst nicht "von
  Hand erzeugt". Gegenmittel jedes Mal: Default, Reichweite und Aufrufer
  ansehen.
- **Eine reine Verschiebung laesst Altbestand als "neu" erscheinen**
  (2026-08-27). Der Bezeichner-Linter (Regel 7) schlug beim A-Commit an
  `PARTIE_GEWICHT`/`conj_breite` an, obwohl nichts Neues entstand. Das ist
  kein Fehlalarm: verschobener Altbestand kommt so ueberhaupt erst einmal
  unter die Regel.
- **Ein umgangenes Tor erzieht zum Umgehen** (Bilanz 2026-08-27). Die
  Datei-Groessen-Ratsche hat 10-mal die Basislinie neu gelegt und **null**
  Zerlegungen bewirkt; sie ist deshalb WARNUNG statt Blocker. Waechter an
  Ausloesungen-gegen-Wirkung messen, nicht am blossen Vorhandensein.
- **Eine Herleitung aus dem Code ist eine Hypothese, kein Befund**
  (2026-08-25; Schaden: vier Herleitungen lagen am selben Tag im VORZEICHEN
  falsch, drei in der Parallelsitzung und eine hier). Der Fall hier: Kriterium
  6 "startet bei -27" -- falsch, `special_empty` zaehlt nur Spezialfelder auf
  bereits GELEGTEN Platten, das Konto startet bei 0. Die Code-Seite steht in
  `architecture_reference.md`, Abschnitt "Konstanten mit Fallstrick"; hier
  steht der Vorfall. Regel daraus: wer aus dem Code ableitet, markiert es als
  Herleitung, bis eine Messung oder ein zweiter Leser sie bestaetigt.
