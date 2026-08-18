<!-- STATUS: ENTSCHIEDEN | Frage: Kann der Partie-Replay exakt statt heuristisch werden, indem jede Aktion mit ihrer ID aus dem ACTION SPACE geloggt wird -- derselben, gegen die der Policy-Kopf trainiert? | Beleg: par.7, ENTSCHIEDEN 2026-08-18 -- gebaut und gemessen. Neue Partie: 52/52 Stein-Zuege ueber die ID, 245/245 Zeilen exakt. Beide offenen Alt-Partien laufen jetzt ebenfalls durch (321/321 bzw. 327/327). -->

# PREREG: Aktions-IDs im Partie-Log, synchron zum Action Space

Stand **2026-08-18**, **GEBAUT UND GEMESSEN** (par.7). Die Abschnitte par.1-par.6
stehen unveraendert in der Plan-Zeitform der Registrierung; wo die Wirklichkeit
davon abweicht, steht es in par.7.

**Anlass (Nutzer 2026-08-18):** *"willst du das nicht sauber encoden mit ids
ähnlich zum action space"* — und praeziser: *"kannst du die ids nicht gleich mit
dem action space syncen"*.

---

## par.1 DAS PROBLEM IST GEMESSEN, NICHT VERMUTET

`tools/analyze_game_log.py` rekonstruiert Aktionen aus **Prosa**: Farbnamen,
Emoji, `F2`/`GF`-Etiketten, ein eigenes `sun_used`-Tracking und ein
Permutations-Raten fuer die `moon_order` ueber die jeweils folgende
Mond-Stapel-Zeile. Am 2026-08-18 sind drei dieser Ebenen gekippt:

1. **Der Aktionstyp ist aus der Zeile nicht sicher ableitbar.**
   `game_20260818_200516_seed585858` zeigt in Runde 1 (Zeilen 15/20/21) eine
   Vergabe des Startspielersteins direkt vor einer Zeile im SONNEN-Format
   (`4× türkis von GF`), in Runde 2 (Zeilen 78/79/80) dieselbe Abfolge im
   MOND-Format (`2 (2)× türkis von GF`).
   **URSACHE GEKLAERT 2026-08-18 (zwei eigene Fehlschluesse davor, beide
   zurueckgenommen).** Nicht die Engine protokollierte inkonsistent im Sinne
   eines Regelfehlers, und es lag auch nicht an einem veralteten Server-Prozess
   (Server 19:31:44, installiertes Wheel 19:16:28 — derselbe Stand). Die
   tatsaechliche Kette:

   * `execute_move` schrieb das Emoji HART auf Sonne, obwohl `execute_take` auch
     Mond-Quellen behandelt. **Behoben** (Commits `9c92c66`, `86c1144`): das
     Emoji folgt jetzt der Quelle.
   * Der Zug in Runde 1 war `LargeFactoryMoon` — eine TEIL-Entnahme, die
     `validation.rs:214` **nie generiert**, `validate_large_moon` aber
     **akzeptiert**. Erreichbar also nur ueber die API, das heisst im
     Menschenspiel.
   * Der Parser leitete den Typ aus dem Emoji ab, suchte in der
     GENERATOR-Kandidatenliste, fand `LargeFactoryMoon` dort nicht — und der
     quellen-tolerante Rueckfall griff zur globalen Mond-Entnahme, also zu einer
     ANDEREN Aktion. Erst drei Zeilen spaeter scheiterte die Textpruefung.

   **Und genau das ist das Argument fuer diese Registrierung:** mit IDs wuerde der
   Replay die aufgezeichnete Aktion ANWENDEN. Eine nicht generierte, aber gueltige
   Aktion waere kein Problem mehr, und eine echte Divergenz waere sofort als "ID
   hier nicht legal" benannt statt durch eine stille Ersatzwahl verdeckt.
2. **`von GF` bestimmt die Quelle nicht.** Aktion C (Mond ueber alle Fabriken
   plus GF-Mondpool) traegt intern `SMALL_FACTORY_MOON` mit `factory_id = None`
   und passt damit nicht zu den `LARGE_*`-Quellen, die `GF` erwarten laesst.
3. **Die Text-Kreuzvalidierung bricht auch dann ab**, wenn der Zug korrekt
   aufgeloest ist, weil die Engine heute eine andere Zeile erzeugt als im
   Original steht.

Ergebnis: von zwei frischen Partien laeuft **eine** durch (109
Entscheidungspunkte), die andere nicht. Alte Elo-Logs laufen ohnehin nicht (der
Seed reproduziert dort den Fabrik-Aufbau nicht mehr — geprueft an
`game_20260802_181207_seed738365`: Fabrik 2 hat mit ihrem Seed kein tuerkis,
obwohl das Log es entnimmt).

---

## par.2 GEPRUEFTER IST-STAND

| Sache | Befund | Pruefstelle |
|---|---|---|
| kanonische Abbildung Aktion → Index | `action_to_id(a: &Value) -> usize` | `features.rs:982` |
| Kollisionsfreiheit + Grenze | Test `action_to_id_ranges_stay_within_num_actions_and_dont_collide` | `features.rs:1102` |
| Groesse des Raums | `NUM_ACTIONS = 406` | `net_mcts.rs:43`, `config.py:43` |
| `valid_moves` traegt eine ID | **NEIN** — Schluessel sind `color, factory_id, moon_order, row, source, type` | gemessen 2026-08-18 |
| `action_to_id` nach Python exportiert | **NEIN** | gemessen 2026-08-18 |

**Der entscheidende Punkt:** `action_to_id` ist **derselbe** Index, gegen den der
Policy-Kopf trainiert wird. Eine Log-ID in diesem Raum ist damit nicht nur ein
Replay-Schluessel, sondern unmittelbar mit den Policy-Logits vergleichbar.

---

## par.3 WAS GEBAUT WIRD — drei additive Stuecke

**S1 — `valid_moves` traegt die ID.** Jeder Eintrag bekommt ein Feld `id` =
`action_to_id(mv)`. Rein additiv; bestehende Leser ignorieren ein zusaetzliches
Feld. Damit braucht der Replay keinen eigenen Export und keinen zweiten Aufruf.

**S2 — die Engine loggt die ID der angewandten Aktion, NUR in der GESPEICHERTEN
Fassung.** Nutzer-Vorgabe 2026-08-18: *"am log der in index.html angezeigt wird
brauchst nichts ändern. nur in der gespeicherten variante"*. Die Zeile geht also
in die Datei unter `static/log/`, nicht in den UI-Strom — damit bleibt die
Anzeige unberuehrt und es entsteht kein Rauschen fuer den Spieler.

Eine EIGENE, maschinenlesbare Zeile je Aktion, nicht eine Aenderung der
bestehenden:

    #a {"id": 137, "p": 0}

**Warum eine neue Zeile und keine Erweiterung der bestehenden:** `tools/hooks/pre-push`
warnt bei Aenderungen am Logtext, und `tools/plate_points_from_arena.py`
importiert die Muster aus `tools/analyze_game_log.py` (dortiger Kommentar:
"aendert jemand den Logtext, brechen beide Seiten gemeinsam"). Eine zusaetzliche
Zeile mit eigenem Praefix laesst alle bestehenden Ausdruecke unberuehrt.

**S3 — der Replay matcht auf die ID.** Aus

    kandidaten = [mv for mv in valid_moves if <Farbe/Reihe/Quelle/Emoji-Heuristik>]

wird

    kandidaten = [mv for mv in valid_moves if mv["id"] == geloggte_id]

Eine Umkehrfunktion `id_to_action` ist NICHT noetig: aufgezaehlt wird ueber die
legalen Zuege, und der Kollisionsfreiheits-Test garantiert genau einen Treffer.
Damit entfallen `sun_used`, die Emoji-Deutung, die `F2`/`GF`-Zuordnung, das
Permutations-Raten — und die Text-Kreuzvalidierung, weil nichts mehr zu raten
ist.

---

## par.4 SPERRE VOR DEM BAU — bricht die neue Zeile bestehende Leser?

Drei Leser haengen am Logtext: `tools/analyze_game_log.py` (Parser),
`tools/plate_points_from_arena.py` (importiert dessen Muster) und
`tools/hooks/pre-push` (Warnung).

> **VORAB-REGEL:** vor dem Einbau wird an EINEM vorhandenen Arena-JSON mit
> `--log-games` geprueft, dass alle drei mit einer unbekannten `#a {...}`-Zeile
> im Strom unveraendert arbeiten. Bricht einer, wird die Zeile nicht eingebaut,
> sondern ein getrennter Kanal gewaehlt (Sidecar-Datei je Partie).

Zusaetzlich zu pruefen und zu protokollieren: dass `NUM_ACTIONS` unveraendert
bleibt und der Kollisionstest gruen ist.

---

## par.5 STABILITAET DER IDs — der Vorbehalt, der ins Log gehoert

Eine gespeicherte ID ist nur so stabil wie der Action Space. Eine Aenderung von
`NUM_ACTIONS` hat in diesem Projekt schon einmal alte Checkpoints entwertet
(Merkzettel `feedback_num_actions_change_breaks_old_checkpoints`); dasselbe wuerde
fuer gespeicherte IDs gelten.

**Deshalb traegt die Zeile beides:** die ID als schnellen Weg UND die kanonischen
Felder als Rueckfallebene.

    #a {"id": 137, "p": 0, "a": {"type": "stone", "source": "SMALL_FACTORY_MOON",
        "color": "türkis", "row": 3, "factory_id": null, "moon_order": []}}

Verschiebt sich der Raum spaeter, bleibt das Log lesbar. Die Felder sind genau
die, die `action_to_id` konsumiert — also keine zweite Wahrheit, sondern deren
Eingabe.

---

## par.6 WAS DER UMBAU NICHT LEISTET

- **Alte Logs bekommen nichts.** Sie bleiben unreplaybar; das sind sie ohnehin
  (par.1). Der Gewinn liegt bei allen kuenftigen Partien.
- **Der Teil-Entnahme-Fehler wird nicht geheilt, sondern nur sichtbar gemacht.**
  Der Mondbereich ist EIN Pool (oberste Fliesen aller kleinen Stapel plus alles
  der Mondseite der grossen Fabrik, `engine_manual.md:100-102`). `LargeFactoryMoon`
  nimmt nur den GF-Anteil.

  **BESTAETIGT 2026-08-18** (Nutzer: *"ja lässt sich reproduzieren. das gehört
  nicht so."*), Beleg `static/log/game_20260818_205751_seed642598`: nach dem
  GF-Sonnenzug (rel. Zeile 1) liegt auf F4 rot obenauf (rel. Zeile 4, keine
  weitere F4-Entnahme dazwischen), und rel. Zeile 21 nimmt **1×** rot von GF
  statt der Vereinigung. Betroffen ist nur der MENSCH — der Generator erzeugt
  ausschliesslich die Vereinigungsform, das Netz spielt regelkonform.

  **Nutzer-Entscheid zur Reparatur:** der UI-Klick auf den GF-Mondbereich
  entfaellt; geklickt wird nur noch in den GETEILTEN Mondbereich, die Stapel
  bleiben ebenfalls nicht klickbar. Das ist eine EIGENE Aenderung und nicht Teil
  dieses Umbaus — hier steht sie nur, weil sie erklaert, warum alte Logs (auch
  die Elo-Logs) nicht reproduzieren: der Replay nimmt die Vereinigung, das
  Original nahm weniger, und ab da laufen die Zustaende auseinander.
- **Es ist keine Aenderung an Suche, Wertung oder Self-Play.** Nur Logging plus
  ein Feld in `valid_moves`.

## par.7 ERGEBNIS (2026-08-18)

**Alle drei Stuecke gebaut, die Sperre gezogen, gemessen.** `cargo test --release`:
447 bestanden, 0 gescheitert (dieselbe Zahl wie vor dem Umbau). `NUM_ACTIONS`
unveraendert 406 (`net_mcts.rs:43`), der Kollisionstest laeuft in diesen 447 mit.

### par.7.1 Die Sperre aus par.4 hat ZUGESCHLAGEN -- einer der drei Leser bricht

Gemessen per Injektion einer unbekannten `#a`-Zeile vor JEDE Textzeile von
`game_20260818_195111_seed558549`:

| Leser | Befund |
|---|---|
| `tools/analyze_game_log.py` | **unveraendert** -- `load_log` verwirft `#`-Zeilen ohnehin; Report byte-gleich |
| `tools/plate_points_from_arena.py` | **GEBROCHEN** -- `je_kriterium` fiel von `{Vertikale Reihen: 0, Eckplatten: 3, Spezialfelder: -12}` auf `{}` |
| `tools/hooks/pre-push` | **unveraendert** -- kein Log-LESER, sondern eine Diff-Heuristik; echte Rust-Aenderungen fallen konservativ auf den vollen `cargo test`, wie gewuenscht |

**Ursache des Bruchs** (`plate_points_from_arena.py`, Schleife in `auswerten`):
sie liest jede Zeile OHNE `[Rn] `-Praefix als Klartext weiter
(`text = m.group(2) if m else roh`). Landet dabei etwas anderes als eine
Kriteriumszeile im Endwertungs-Block, setzt der Sammler `aktiv = False` und der
Block bricht ab -- still, ohne Fehlermeldung.

**Entscheid, abweichend vom Wortlaut der Sperre:** die Sperre sah bei einem
Bruch den Sidecar-Kanal vor. Stattdessen wurde der Leser gehaertet -- ein
`if roh.startswith("#"): continue`, also exakt die Konvention, die
`analyze_game_log.load_log` seit jeher hat. Begruendung: die Injektion war
haerter als die Wirklichkeit (die Engine schreibt `#a` nur vor DRAFTING-
Aktionen, nie im Endwertungs-Block), und die Haertung schuetzt gegen JEDE
kuenftige `#`-Zeile an JEDER Stelle, ein Sidecar nur gegen diese eine.
Nach der Haertung ist der Leser injektionsfest (nachgemessen, Ergebnis identisch).

### par.7.2 S1 -- `valid_moves` traegt die ID

Gemessen an einer frischen Stellung (Seed 12345, nach beiden Startkacheln):
**209 Eintraege, 0 ohne `id`**, ID-Bereich 10-405.

**Eine Annahme der Registrierung ist FALSCH und wurde ersetzt.** par.3 schrieb:
*"der Kollisionsfreiheits-Test garantiert genau einen Treffer"*. Er tut es
nicht -- er sichert nur, dass verschiedene Aktions-TYP-FAMILIEN nicht
kollidieren. Innerhalb einer Familie ist die ID absichtlich groeber als der Zug:

- `moon_order` fliesst nicht in die ID ein (`net_mcts.rs:1824`, bewusst: sonst
  waeren alle Checkpoints entwertet).
- Kuppel-Zuege zerfallen intern in Slot-Wahl und Rotation
  (`game.rs::apply_drafting`); die vier Rotationsvarianten teilen sich die ID.

Gemessen in derselben Stellung: **24 IDs mit mehr als einem Eintrag, alle davon
Rotationsgruppen.** Deshalb traegt ein rotationsbehafteter Eintrag zusaetzlich
`id_rotation`; das PAAR identifiziert den atomaren UI-Zug, und `moon_order`
steht wie in par.5 vorgesehen in den kanonischen Feldern.

### par.7.3 S2 -- die Zeile, und wo sie NICHT steht

Format wie registriert, mit den Feldern, die der Replay zum AUFRUF braucht.
(par.5 nannte "die Felder, die `action_to_id` konsumiert" -- das waere
`factory_index` statt `source`/`factory_id`. Letztere sind die brauchbareren
und stehen deshalb dort.)

    #a {"a":{"color":"gelb","factory_id":null,"moon_order":[],"row":3,
        "source":"LARGE_FACTORY_SUN","type":"stone"},"id":86,"p":0}

Abgedeckte Aktionstypen in der Messpartie (Auszaehlung der `#a`-Zeilen):
`stone` 56, `dome_display` 8, `choose_dome_slot` 4, `choose_dome_rotation` 8,
`bonus_chip` 16, `dome_stack_peek` 4, `choose_draw_stack_slot` 4 -- also beide
Kuppel-Wege, der Stapel-Zug des Menschen und der Bonuschip.

Nachgemessen an einer frisch erzeugten Partie: **UI-Log 0 `#a`-Eintraege,
gespeicherter Strom 1** -- die Nutzer-Vorgabe ist eingehalten. Gefiltert wird in
`serialize.rs::state_to_json` VOR dem `take(30)`, sonst haette jede
Maschinenzeile einen echten Eintrag aus dem Anzeigefenster gedraengt.

**Der Haken sitzt an der API-Grenze (`py.rs`), nicht in `apply_drafting`.** Das
war eine Abwaegung: `apply_drafting` ist der Heisspfad der Suche (`net_mcts.rs`
ruft ihn pro Simulation), und ein Schalter am `Game`-Struct haette 47
Konstruktions-Stellen in `round5.rs`/`round_transition.rs`/`self_play.rs`
angefasst -- par.6 schliesst genau das aus.

**Zwei bewusste Luecken, beide markiert und beide vom Rueckfall gedeckt:**

1. **`Pass` schreibt nichts** -- weder im Mensch- noch im KI-Pfad. Es ist der
   einzige Drafting-Zug ohne Logzeile, und `Replayer.ensure_drafting_actor`
   bricht ab, wenn `apply_pass` die Log-Laenge veraendert. Passes rekonstruiert
   der Replay ohnehin aus dem Spielerwechsel. (Der Heuristik-KI-Pfad hat das im
   ersten Wurf verletzt -- gefunden ueber die Typ-Auszaehlung der `#a`-Zeilen
   der Messpartie, nicht durch Nachdenken.)
2. **Startet die NETZ-KI einen Stapel-Zug**, loest `apply_chosen_action` intern
   eine ganze Folge auf (`self_play.rs::resolve_and_apply_stack_draw`, im
   Self-Play-Heisspfad). Dieser eine Fall bleibt beim Textweg, den der Replay
   beherrscht.

### par.7.4 S3 -- Replay ueber die ID, mit Rueckfall

| Partie | vorher | jetzt | Aufloesung der Stein-Zuege |
|---|---|---|---|
| frisch erzeugt (Seed 424242, 97 `#a`-Zeilen) | -- | **245/245 Zeilen, keine Divergenz** | **52 ueber die ID, 0 ueber den Text** |
| frisch erzeugt (Seed 777001, 100 `#a`-Zeilen, Gegenprobe nach dem Pass-Fix) | -- | **259/259 Zeilen, keine Divergenz** | **56 ueber die ID, 0 ueber den Text** |
| `game_20260818_195111_seed558549` | 327/327 | **327/327**, Report inhaltsgleich | 64 ueber den Text (keine IDs im Log) |
| `game_20260818_200516_seed585858` | **Abbruch Zeile 16** | **321/321, keine Divergenz** | 66 ueber den Text |
| `game_20260802_181207_seed738365` (Elo) | Abbruch Zeile 4 | Abbruch Zeile 4 (unveraendert) | -- |

Der Rueckfall ist Absicht, kein Rest: ein Log ohne `#a`-Zeilen (alles vor heute,
Arena-Logs, der KI-Stapelzug) laeuft unveraendert ueber den Textweg. Ein Hinweis
mit dem FALSCHEN Typ wird verworfen statt erzwungen -- das waere genau die stille
Ersatzwahl, gegen die diese Registrierung angetreten ist. Ist die geloggte ID
hier nicht legal, sagt der Replay das jetzt woertlich ("Aktions-ID N aus dem Log
ist hier nicht legal") statt eine andere Aktion zu nehmen -- die Wirkung, die
par.1 sich versprochen hat.

Der Report weist ab sofort aus, WORAUF der Replay gelaufen ist ("52 ueber die
Aktions-ID, 0 ueber den Textweg"). Ohne diese Zeile sehen ID-Weg und Prosa-Raten
im Report identisch aus.

### par.7.5 Partie 2 laeuft -- die Ursache war NICHT nur der fehlende Kandidat

par.8 Punkt 1 nahm an, der Parser muesse lediglich `LargeFactoryMoon` als
Kandidaten kennen. Das ist die halbe Wahrheit. Nachgebaut und Zeile fuer Zeile
verglichen:

| | |
|---|---|
| Original (vor der Emoji-Korrektur geschrieben) | `[R1] ☀️  Spieler 1: 4× türkis von GF → Reihe 4 [4/4]` |
| Replay mit `SMALL_FACTORY_MOON` (global -- was der Textweg nahm) | `[R1] 🌙 Spieler 1: 4 (4)× türkis von GF → Reihe 4 [4/4]` |
| Replay mit `LARGE_FACTORY_MOON` (Teil-Entnahme, neuer Kandidat) | `[R1] 🌙 Spieler 1: 4× türkis von GF → Reihe 4 [4/4]` |

Der neue Kandidat trifft die Aktion **zeichengleich bis auf das Emoji**. Es
fehlte also beides: der Kandidat UND eine Antwort auf die Textaenderung, die die
Emoji-Korrektur von heute selbst erzeugt hat (par.8 Punkt 2).

Beides gebaut:

- **Rettungs-Kandidat**, hinten angehaengt. Gefahrlos, weil `apply_ambiguous`
  jeden Kandidaten auf einer frischen Kopie probiert und exakte Textgleichheit
  verlangt -- ein zusaetzlicher Kandidat kann nur retten, nie verfaelschen.
- **Eine benannte, datierte Emoji-Toleranz** im Textvergleich: nur ☀️
  gegen 🌙 direkt hinter dem `[Rn] `-Praefix, und
  nur wenn der Rest zeichengleich ist. Die globale Mond-Entnahme bleibt
  unterscheidbar, weil sie zusaetzlich die `(detail)`-Klammer traegt -- die
  Toleranz kann also keine Quellen-Verwechslung durchlassen. Jeder Treffer wird
  gezaehlt und im Report ausgewiesen (Partie 2: **2 Zeilen**), nicht verschwiegen.

### par.7.6 Nebenbefund: ein Altbestands-Fehler im Replay-Werkzeug

`_run_loop` endete mit `return rep, lines` (schon in `HEAD:785`, also nicht neu).
`run()` legt das auf `li` ab und reicht es als `li_reached` weiter -- die "wie
weit kam der Replay"-Zahl im Report war auf dem ERFOLGSPFAD also ein Tupel, kein
Zeilenindex. Auf dem Divergenzpfad war sie korrekt, deshalb ist es nie
aufgefallen. Korrigiert zu `return li`.

### par.7.7 Was NICHT geprueft ist

- **Kein Lauf durch den echten Server** (`server.py` im Browser). Die Messpartie
  lief ueber dieselben `apply_*`-Methoden, die die Server-Routen aufrufen, aber
  die Route selbst ist ungeprueft.
- **Keine Arena-Messung.** Arena-Logs entstehen nicht ueber `PyGame` und tragen
  daher keine `#a`-Zeilen; der Rueckfall greift dort per Konstruktion.
- **Keine Laufzeit-Aussage** zum Replay vorher/nachher (nicht gemessen; beide
  Alt-Partien liegen unter einer Sekunde).

---


### par.7.8 Nachtrag: die Groessen-Ratsche hat den Umbau gestoppt

`tools/analyze_game_log.py` wuchs von 57,5 KB auf 68,8 KB und riss damit die
Konventions-Schwelle (59,8 KB); der pre-commit-Haken hat den Commit abgelehnt.
**Nutzer-Entscheid: auslagern statt Basislinie neu legen.**

Herausgeschnitten wurde die REPORT-Schicht (`_git_commit_short`,
`extract_full_score_timeline`, `build_report`) nach `tools/game_log_report.py`
-- eine echte Naht: dort steht reine Darstellung, kein Parser, kein Replay,
kein Engine-Aufruf. Ergebnis 51,9 KB, also unter der Schwelle UND unter der
alten Basislinie.

Der Import steht bewusst asymmetrisch: `game_log_report` zieht
`ROOT`/`LogLine`/`classify` am Modulkopf, `analyze_game_log` zieht
`build_report` erst in `main()`. An beiden Koepfen waere es ein Zyklus.

Gegenprobe nach dem Schnitt: alle drei Partien liefern unveraenderte Reports
(259/259, 321/321, 327/327). `tools/plate_points_from_arena.py` importiert
weiterhin `PATTERNS`/`ROUND_PREFIX` aus `analyze_game_log` -- die sind
geblieben, der Import laeuft.

---

## par.8 UEBERGABE -- was ein anderer Agent wissen muss

**Der Umbau ist ERLEDIGT (par.7). Dieser Abschnitt beschreibt jetzt den Stand
danach, nicht mehr den Fahrplan davor.**

| Was | Stand |
|---|---|
| S1 `id`/`id_rotation` in `valid_moves` | gebaut (`serialize.rs::move_action_id`) |
| S2 `#a`-Zeile, nur gespeicherte Fassung | gebaut (`py.rs::push_action_id_line` / `log_and_apply`), UI-Filter in `serialize.rs::state_to_json` |
| S3 Replay ueber die ID | gebaut (`analyze_game_log.py::hint_for` / `resolve_stone`) |
| Report-Schicht | ausgelagert nach `tools/game_log_report.py` (par.7.8) |
| par.4-Sperre | gezogen; `plate_points_from_arena.py` gehaertet (par.7.1) |
| `cargo test --release` | 447 bestanden, 0 gescheitert |
| Wheel | neu gebaut und installiert -- OHNE das sieht Python den neuen Code nicht |

**Drei Dinge, die beim WEITERBAUEN zu beachten sind:**

1. **Die ID ist nicht eindeutig** (par.7.2). Wer auf ihr matcht, braucht die
   kanonischen Felder als Disambiguierung -- `moon_order` fuer Stein-Zuege,
   `id_rotation` fuer Kuppel-Zuege. Das ist kein Mangel, sondern die Folge der
   Entscheidung, `NUM_ACTIONS` nicht aufzublaehen.
2. **Der Haken sitzt in `py.rs`, nicht in `apply_drafting`.** Wer eine neue
   `apply_*`-Methode ergaenzt, muss `log_and_apply` statt `apply_drafting`
   aufrufen, sonst fehlt die Zeile fuer diesen Zugtyp. Umgekehrt gilt: in
   `apply_drafting` gehoert der Haken NICHT hin (Heisspfad der Suche, par.7.3).
3. **Die Emoji-Toleranz ist eng gehalten und datiert** (par.7.5). Sie deckt
   GENAU die Korrektur vom 2026-08-18 ab. Wer den Logtext erneut aendert, baut
   keine zweite Toleranz dazu, sondern zieht den Parser mit -- sonst wird aus
   einer benannten Ausnahme eine aufgeweichte Pruefung.

**Nicht wieder aufrollen:** die Ursache in par.1 (dreimal falsch geraten, jetzt
belegt), die Rolle des Server-Prozesses (geprueft, unschuldig), die Frage, ob
die Engine gegen das Regelwerk protokolliert (tut sie nicht -- `take_from_sun`
zitiert die Regel und haelt sie ein), und die Idee, `apply_drafting` selbst
loggen zu lassen (abgewogen und verworfen, par.7.3).
