# Fallen (aus echten Vorfaellen)

**Kanonischer Ort seit 2026-08-28** (aus STATUS.md entflochten, Nutzer-Hinweis:
STATUS ist kein Langzeitgedaechtnis); Herkunft der Inhalte: STATUS-Stand
2026-08-28. Wer aendert, aendert HIER -- STATUS.md verweist nur noch.

Jeder Eintrag ist ein VORFALL, keine Vermutung: er ist einmal passiert und hat
Zeit oder eine Messung gekostet. Wo daraus eine stehende Regel geworden ist,
steht sie in `../CLAUDE.md`; hier steht die Herkunft, die sie glaubwuerdig
macht. Wer eine Falle ergaenzt, nennt Datum und Schaden.

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
