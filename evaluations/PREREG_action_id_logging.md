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
   *RUECKNAHME 2026-08-18:* daraus wurde zunaechst geschlossen, die Engine
   protokolliere inkonsistent. **Das ist widerlegt** — `factory.rs::take_from_sun`
   der grossen Fabrik vergibt den Marker ausschliesslich bei
   `monochrome_fallback && has_first_player_marker` und zitiert die Regelstelle
   im Kommentar. Ebenso widerlegt: ein veralteter Server-Prozess (Server startete
   19:31:44, installiertes Wheel 19:16:28 — derselbe Stand, mit dem replayed
   wird). **Die Ursache der Divergenz in dieser Partie ist UNGEKLAERT** und liegt
   vermutlich in einem frueheren, textlich unsichtbaren Auseinanderlaufen
   (`moon_order`-Wahl oder eine RNG-verbrauchende Aktion).
   **Und genau das ist das Argument fuer diese Registrierung:** mit IDs wuerde der
   Replay die aufgezeichnete Aktion ANWENDEN statt zu raten, und eine echte
   Divergenz waere als "ID hier nicht legal" sofort benannt — statt still eine
   andere Aktion zu waehlen und erst drei Zeilen spaeter am Text zu scheitern.
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
- **Die Verhaltensdifferenz in `game_20260818_200516_seed585858` wird nicht
  geheilt.** Dort bot die heutige Engine keinen `LARGE_FACTORY_SUN`-Zug an, wo
  das Original einen machte. Mit IDs wuerde der Replay das SAUBER melden statt
  eine falsche Aktion zu waehlen — das ist der Gewinn, nicht die Heilung.
- **Es ist keine Aenderung an Suche, Wertung oder Self-Play.** Nur Logging plus
  ein Feld in `valid_moves`.

## par.7 ERGEBNIS (leer bei Registrierung)
