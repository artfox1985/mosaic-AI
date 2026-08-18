<!-- STATUS: OFFEN | Frage: Kann der Partie-Replay exakt statt heuristisch werden, indem jede Aktion mit ihrer ID aus dem ACTION SPACE geloggt wird -- derselben, gegen die der Policy-Kopf trainiert? | Beleg: offen, nichts gebaut. Anlass: Nutzer-Vorschlag 2026-08-18 nach drei Fehlschluessen aus der Prosa-Rekonstruktion. -->

# PREREG: Aktions-IDs im Partie-Log, synchron zum Action Space

Stand **2026-08-18**, **ENTWURF, nichts gebaut.** Durchgehend Plan-Zeitform.

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

## par.7 ERGEBNIS (leer bei Registrierung)

---

## par.8 UEBERGABE — was ein anderer Agent wissen muss

**Ausgangslage, alles committet und gruen (447 Tests):**

| Was | Stand |
|---|---|
| `--dump-states` im Analyse-Werkzeug | gebaut (`21697ac`), liefert JSONL je Entscheidungspunkt |
| Emoji folgt der Quelle | gebaut (`9c92c66`, `86c1144`) |
| Replay `game_20260818_195111_seed558549` | laeuft VOLLSTAENDIG durch, 109 Zustaende |
| Replay `game_20260818_200516_seed585858` | scheitert, Ursache geklaert (par.1) |
| alte Elo-Logs | reproduzieren nicht; vermutlich dieselbe Ursache (Teil-Entnahmen ueber die API) |

**Die drei Bauteile stehen in par.3.** Reihenfolge: S1 (`id` in `valid_moves`) →
par.4-Sperre → S2 (Log-Zeile, NUR gespeicherte Fassung) → S3 (Replay auf ID).

**Zwei Dinge, die beim Bauen zu beachten sind und heute Zeit gekostet haben:**

1. **Der Parser muss `LargeFactoryMoon` als Kandidaten kennen**, sonst scheitert
   Partie 2 weiter — die Kandidatenliste kommt aus dem GENERATOR, der diese
   Aktion nie erzeugt. Mit S3 entfaellt das Problem, weil ueber die ID gematcht
   wird; bis dahin ist es die kleinste Reparatur fuer Partie 2.
2. **Die Emoji-Korrektur hat den Logtext GEAENDERT.** Kuenftige Logs tragen 🌙 im
   schlichten Format (ohne die `(detail)`-Klammer) fuer Teil-Entnahmen. Der
   Parser kennt bisher 🌙 nur MIT Klammer (`MOON_GLOBAL_TAKE`). Das ist beim
   Einbau mitzuziehen — alte Logs behalten ihr ☀️.

**Nicht wieder aufrollen:** die Ursache in par.1 (dreimal falsch geraten, jetzt
belegt), die Rolle des Server-Prozesses (geprueft, unschuldig), und die Frage, ob
die Engine gegen das Regelwerk protokolliert (tut sie nicht — `take_from_sun`
zitiert die Regel und haelt sie ein).
