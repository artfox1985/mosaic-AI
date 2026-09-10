<!-- STATUS: OFFEN | Frage: Was lernt ein Beobachter, der selbst gegen das Champion-Netz spielt, ueber dessen Schwaechen, das die Arenen nicht zeigen -- und stimmt die Spielstaerke des Netzes aus Spielersicht mit der Leiter ueberein? | Beleg: g01 gespielt 2026-09-06: Claude 72:42 gegen Champion v24-b06 @400, sechs Beobachtungen als Sondenkandidaten (par.7). AUSGESETZT (Nutzer 2026-09-10) bis zum Entscheid ueber die Sichtbarkeit der Rueckgabe-Reihenfolge (par.9 Punkt 5, dome_stack par.14). Audit par.9: Spezialfeld-Anzeige behoben, Pass- und Mondzug-Blocker abgeraeumt, KI-Zeile ungeklaert; Gegner bei Wiederaufnahme = models/champion.txt. -->

# Vorregistrierung: Temporaeres Spiel-Interface Claude gegen Netz (Nutzer-Auftrag 2026-09-06)

**Angelegt 2026-09-06, 12:30.** Nutzer, woertlich: *"schreib mir ein prereg fuer ein
temporaeres interface, dass du gegen das netz spielen kannst. bei bedarf bin ich das
durchfuehrende organ in den server games."*

## par.1 Anlass und Zweck

Die Kampagne misst das Netz mit Arenen (Tor 1/2), Sonden und dem Elo-Register.
Alle diese Instrumente sind Netz-gegen-Netz oder Netz-gegen-Heuristik; der
einzige menschliche Massstab sind die 20 Server-Partien in `static/log/`
(`PREREG_geometric_envelope.md` par.8.12a: Mensch gegen KI). Ein Beobachter, der
selbst spielt, sieht anderes als eine Kennzahl: welche Zuege das Netz in einer
konkreten Stellung uebersieht, ob es eine begonnene lange Reihe liegen laesst
(par.8.13), ob es Kuppelplatten passend waehlt, wie es auf Denial reagiert. Das
Interface ist TEMPORAER: es dient dieser Beobachtung und einer Gegenprobe der
Spielstaerke aus Spielersicht, nicht dem Dauerbetrieb und nicht der Leiter.

Zwei Wege, beide registriert, damit der Rueckfall nicht improvisiert wird:

- **Weg 1 (bevorzugt): Werkzeug-Schleife.** Claude spielt ueber ein Kommandozeilen-
  Werkzeug, das den Zustand als Text liefert, den Zug entgegennimmt, ihn an die
  Engine gibt und den Netz-Zug ausfuehrt. Jeder Zug ist ein Werkzeugaufruf der
  Sitzung.
- **Weg 2 (Rueckfall): der Nutzer als ausfuehrendes Organ.** Claude liest den
  Zustand aus dem laufenden Server (`/api/state`, oder ein Bildschirmfoto, das
  der Nutzer schickt), nennt den Zug in der Notation von par.3.3, der Nutzer
  fuehrt ihn im Browser aus. Weg 2 kostet Nutzerzeit je Zug und wird nur
  gebraucht, wenn Weg 1 ausfaellt (Server haelt das Wheel, Install-Konflikt,
  API-Luecke).

## par.2 Was heute ist (Code geprueft 2026-09-06)

- **Engine-API in Python:** `PyGame` (`engine/src/py.rs:79-102`): `new(names,
  first_player, seed, scoring_ids)`, `state_json()` (py.rs:143; dasselbe JSON wie
  der Server, `serialize.rs`, mit `valid_moves` nur in der Draft-Phase,
  `serialize.rs:479`), `apply_stone` (:197), `apply_dome` (:232),
  `apply_dome_stack_peek` / `_choose` (:255/:270), `apply_bonus_chip` (:303),
  `apply_pass` (:310), `apply_start_tile` (:321), `apply_tiling(player,
  pattern_row, slot_row, slot_col, space_index)` (:327), `apply_tiling_chips`
  (:343), `move_row_to_floor` (:419), `end_tiling` (:437), `select_scoring` (:461),
  `end_scoring_json` (:475), Netz-Zug `ai_step_net_json(simulations, c_puct, log)`
  (:526), Netz-Tiling `ai_tiling_step` (:931), Loeser-Kandidaten
  `tiling_candidates_json(state_json, player, k)` (Modulfunktion; von
  `tools/probes/tiling_geometry_probe.py` genutzt), Log `log_since` (:182).
- **Server:** `/api/new_game`, `/api/state`, `/api/move/{stone,dome,dome_stack_peek,
  dome_stack_choose,bonus_chip,start_tile,pass}`, `/api/tiling`,
  `/api/tiling/bonus_chips`, `/api/tiling/move_to_floor`, `/api/end_tiling`,
  `/api/scoring_tiles/select`, `/api/end_scoring` (`server.py:570-1336`).
  Schwierigkeit "expert" = Champion @400 (`server.py:253`); Champion aus
  `models/champion.txt` (`_load_champion_model`, `server.py:167`); Spec-Felder
  werden beim Start in Env-Knoepfe uebersetzt (`_SPEC_TO_ENV`, `server.py:205`).
  `/api/ai/hint` mit 800 Sims (`_teacher_sims`, `server.py:139`).
- **Log-Format:** `static/log/game_*.log`, Kopfzeile mit `seed`, `players`,
  `first_player`, `ai_model`, `ai_sims`; Replayer `tools/analyze_game_log.py`
  (`Replayer`) spielt diese Logs nach, die Sonden (`tiling_geometry_probe.py`,
  Reihen-Alter) laufen darauf. Eine Partie, die in DIESEM Format geloggt wird,
  ist mit den vorhandenen Werkzeugen auswertbar.
- **Regeln:** `docs/engine_manual.md` (bei Regelfragen dort nachschlagen, nicht
  ableiten; CLAUDE.md Regel 0 Punkt 3).
- **Auslastung:** ein Netz-Zug @400 ist ein CPU-Auftrag. Spielen darf NICHT
  neben einer laufenden CPU-Messung (Arena, Sonde), aber neben einem
  GPU-Training (`docs/working_rules.md`, Praezisierung 2026-08-31).

## par.3 Bauform (registriert VOR dem Bau)

### par.3.1 Werkzeug `tools/claude_play.py` (Weg 1)

Ein Kommandozeilen-Werkzeug mit persistenter Partie, weil jeder Zug ein eigener
Prozess ist:

- `--new --seed S --first-player P [--model NAME --sims N --spec PFAD]`: legt
  `evaluations/artifacts/claude_play/<id>/` an (Manifest: Seed, Erstspieler,
  Wertungsplatten-Ids, Modell, Sims, Spec, Kontrakt-Hash aus `engine_config_json`,
  Wheel), startet die Partie, spielt ggf. den ersten Netz-Zug, schreibt das Log
  im Server-Format (`game.log`) und den Zustand (`state.json`).
- `--show`: rendert den Zustand als Text (par.3.2) mit der Liste der legalen
  Zuege samt Kurzbezeichnern.
- `--move <Zug>`: spielt Claudes Zug (Notation par.3.3), dann alle Netz-Zuege bis
  Claude wieder dran ist (Draft-Zuege des Netzes ueber `ai_step_net_json`,
  Netz-Tiling ueber `ai_tiling_step`, Wertung ueber `end_scoring_json`), schreibt
  Log und Zustand, rendert den neuen Zustand.
- **Zustandsfuehrung:** der Zustand wird bei jedem Aufruf aus dem Log per
  `Replayer` (`analyze_game_log.py`) rekonstruiert, nicht aus einem Pickle. Grund:
  derselbe Weg wie fuer Server-Logs, jede Partie bleibt replaybar, kein zweites
  Format. Kosten unter 1 s je Aufruf (Sonde: 0,44-0,49 s je Partie, par.8.12a).
- **Gegner:** Champion aus `models/champion.txt` mit Champion-Spec, @400, c_puct
  1,5, Env wie `server.py:_SPEC_TO_ENV`; Seeds der Partie aus dem Manifest, damit
  eine Partie bei gleicher Zugfolge reproduzierbar ist. Abweichungen (anderes
  Netz, andere Sims) nur ueber Flags, die im Manifest landen.
- **Tiling durch Claude:** `--show` liefert in der Tiling-Phase die Top-K
  Abschluesse des exakten Loesers (`tiling_candidates_json`, K 8) mit Punkten,
  G4/Gline (par.8.12a) und den neuen Zellen; Claude waehlt einen Kandidaten
  (`--move t3`) oder legt frei (`--move tile r=4 to=(3,1)` je Stein). Der
  Kandidatenweg ist der Normalfall; freies Legen bleibt fuer Faelle, in denen
  Claude bewusst Punkte liegen lassen will (die Frage aus par.8.12).

### par.3.2 Zustandsdarstellung (Text)

Je Spieler: Wertungsplatten (Ids, Kriterien-Kurztext), Punkte, Musterreihen
(Index, Farbe, k/Kapazitaet, Phantome), Strafleiste (Fliesen), Kuppelraster 6x6
als Zeichen (belegt = Farbbuchstabe gross, frei = Farbbuchstabe klein, Wild `*`,
Spezial `#`, ohne Platte `.`), Kuppelplatten-Auslage (Id, vier Zellen, Bonus),
Stapel-Rueckseite oben, Fabriken (Sonnenseite und Mondstapel), grosse Fabrik,
Bonuschips, Beutel/Turm-Farbzaehler, Runde, wer am Zug ist. Das ist die
Menge, die `serialize.rs` liefert und die `neural_net.py` kodiert: Claude sieht
GENAU so viel wie das Netz (Sichtgleichheit, `PREREG_stack_top_feature.md`
par.10), nicht mehr.

### par.3.3 Zugnotation

Dieselben Koerper wie die Server-Routen, als Kurzform: `s <fabrik> <farbe>
<reihe|floor>` (Stein, `/api/move/stone`), `d <platte> <slot_r> <slot_c>
<rotation>` (Kuppelplatte, `/api/move/dome`), `peek` / `choose <platte> ...`
(Stapel), `chip <fabrik>` (Bonuschip), `start <platte> <slot_r> <slot_c>`
(Startplatte), `pass`, in der Tiling-Phase `t<k>` (Loeser-Kandidat) oder
`tile ...`, `floor <reihe>` (Reihe unplatzierbar), `done` (Tiling beenden),
`score <ids>` (Wertungsplatten). `--show` nennt zu jedem legalen Zug seine
Kurzform; ein Zug, der nicht in der Liste steht, wird abgewiesen (die Engine
validiert ohnehin, `validation.rs`).

### par.3.4 Weg 2 (Nutzer als ausfuehrendes Organ)

Claude ruft `GET /api/state` am laufenden Server ab (oder liest ein
Bildschirmfoto), nennt den Zug in der Notation par.3.3, der Nutzer fuehrt ihn
im Browser aus und bestaetigt. Das Server-Log entsteht wie bei jeder
Server-Partie; die Kopfzeile bekommt `"players": ["Claude", "KI"]`, damit die
Auswertung die Seite erkennt. Kein eigener Bau, nur Absprache.

### par.3.5 Was NICHT gebaut wird

Keine Web-Oberflaeche, kein Dauerprozess, keine Aenderung an `server.py` oder
der Engine. Das Werkzeug nutzt nur die vorhandene `PyGame`-API und den
Replayer. Nach Abschluss von par.7 wird es entfernt oder, auf Nutzer-Entscheid,
als `tools/probes/`-Werkzeug behalten.

## par.4 Messgroessen (VOR dem Spielen festgelegt)

Je Partie entsteht ein Log im Server-Format; ausgewertet wird mit den
vorhandenen Werkzeugen, nichts wird nachtraeglich definiert.

1. **Ergebnis:** Sieg/Niederlage, Punkte beider Seiten, Marge (CLAUDE.md
   Standard-Kennzahlen 5 und 6). Erwartung (Hypothese, vorab): Claude verliert
   die Mehrheit gegen den Champion @400; die Frage ist NICHT, ob Claude
   gewinnt, sondern was die Partien zeigen.
2. **Die sechs Standard-Kennzahlen** aus `tools/analyze_game_log.py` und
   `tools/probes/tiling_geometry_probe.py` (Reihen-, Spalten-,
   Strafleisten-Auslastung, Punkte je Wertungsplatte, eigene Punkte, Marge) je
   Seite, Claude gegen Netz, gegen die Mensch-Logs und die Netz-Arenen aus
   par.8.12a/8.14 der Einhuellenden (Reihen-Alter, blockierte 6er, Aussen-Legen).
3. **Uebereinstimmung mit dem Netz:** Anteil von Claudes Draft-Zuegen, die dem
   Netz-Vorschlag @800 entsprechen (Top-1 und Top-3; Weg 1: `ai_debug_net_json`,
   Weg 2: `/api/ai/hint`), je Runde. Nur, wenn der Nutzer den Zusatzaufwand
   freigibt (par.5). Lesart: niedrige Uebereinstimmung bei gutem Ergebnis =
   das Netz uebersieht etwas; niedrige bei schlechtem = Claude spielt schwach.
4. **Qualitatives Protokoll je Partie (Pflicht):** hoechstens drei Stellen mit
   Log-Zeile, an denen das Netz aus Spielersicht falsch spielte, je Stelle die
   Regel oder das Muster (z.B. "laesst blockierte 6er-Reihe liegen", "waehlt
   Platte ohne passende Zelle fuer Reihe 5"), und ob eine registrierte Sonde
   oder ein Knopf (K3-F par.8.14, K4 `round_estimate_leaf_term`) das Muster
   trifft. Das ist der eigentliche Ertrag: Kandidaten fuer Sonden, keine
   Verdikte.

**Was aus den Zahlen NICHT folgt:** kein Elo-Knoten (Claudes Zuege sind nicht
reproduzierbar im Sinn der Leiter), keine Champion- oder Generatorentscheidung,
kein Trainingsmaterial (die Logs gehen NICHT ins Fenster; ein Arm "Claude-Logs
als Traeger" waere eine eigene Prereg).

## par.5 Kosten (gemessen, wo vorhanden; sonst als Annahme markiert)

- Netz-Zug @400 im Server-Spiel: Nutzer-Erfahrung "expert"-Stufe, Sekunden je
  Zug; die Zahl aus `measured_runtimes.md` fuer Netz-Self-Play @400 argmax ist
  6,98 s je Partie bei 11 Threads (viele Partien parallel), also je Zug im
  Einzelspiel unter 1 s Rechenzeit (ANNAHME aus dieser Zahl, nicht einzeln
  gemessen). Der Werkzeugaufruf je Zug kostet die Sitzung rund 20-60 s
  (Lesen, Entscheiden, Aufruf): eine Partie mit rund 35-45 Claude-Zuegen
  dauert 30-60 min (ANNAHME).
- Bau von `tools/claude_play.py`: Renderer, Notation, Replayer-Anbindung,
  Netz-Zugschleife, Manifest; rund 2-3 h ohne Rechenlast. Rauchtest: eine
  Partie Claude gegen Heuristik @150 (billig), dann Champion.
- Uebereinstimmungs-Messung (par.4.3): +800 Sims je Claude-Zug, rund 2 s
  (ANNAHME), also plus 1-2 min je Partie.
- Exklusivitaet: Partien laufen NUR im CPU-freien Fenster (kein Spielen neben
  Arena oder Sonde); neben einem GPU-Training erlaubt.

## par.6 Reihenfolge

1. Nutzer-Entscheide par.8 einholen.
2. Werkzeug bauen (Weg 1), `python -m py_compile`, Rauchtest gegen Heuristik.
3. Erste Partie gegen den Champion @400, Log und Protokoll (par.4.4) hier in
   par.7 registrieren.
4. Weitere Partien bis zur registrierten Zahl (par.8), je Partie Protokoll;
   Auswertung par.4.1-4.3 gesammelt nach der letzten Partie.
5. Verdikt in par.7 und Statuskopf, Werkzeug entfernen oder behalten (par.3.5).

## par.7 Ergebnisse (leer bis zum ersten Spiel)

**Werkzeug gebaut 2026-09-06, 13:12: `tools/claude_play.py`** (Befehle `new`, `show`,
`move`, `note`; Zustand je Aufruf per `analyze_game_log.run` aus `game.log`,
Gegner-Spec als Env vor dem Engine-Import wie `server.py`, Netz-Zuege ueber
`ai_step_net_json` / `ai_start_tile_json`, Endwertung ueber `end_scoring_json`,
Manifest je Partie mit Seed, Erstspieler, Modell, Sims, Spec, Kontrakt-Hash;
Partien unter `evaluations/artifacts/claude_play/<id>/`). Nur `py_compile` und
Import geprueft; **Rauchtest steht aus**, weil die CPU belegt ist (Champion-Kante
A, danach b06-Abnahme). **g01 (2026-09-06, 18:46-19:5x, drei Agenten-Laeufe wegen zweier Werkzeug-Blocker; Seed
20260906, Claude Spieler 0 und Erstspieler, Gegner Champion `v24-b06` mit K3-P @400):
Claude 72 : 42 Netz, Claude gewinnt.** 78 Claude-Zuege; Endwertung Claude Diagonale +10,
Aussenfelder +9, Spezialfelder -9; Netz Diagonale 0, Aussenfelder +11, Spezialfelder -12.
Log `evaluations/artifacts/claude_play/g01/game.log` (433 Zeilen, Server-Format), Notizen
`notes.md` (13 Zeilen). Protokoll des Agenten (Behauptungen, vom Koordinator noch nicht
am Log nachgeprueft):
1. Runde 1 und 3: das Netz zog verdeckt vom Stapel, bis der Punktestand von 5 auf 0 bzw.
   6 auf 1 fiel (je 5 Punkte fuer eine Platte); bei Stand 0 sind weitere Zuege gratis.
2. Runde 1-3: Reihe 2 (rot 3/3) lag unplatzierbar, das Netz legte zwei Platten in die
   Kuppelzeile 2 ohne rot-Zelle (Rotation ohne Ruecksicht auf die wartende volle Reihe).
3. Runde 3: Kachel 7 auf Slot (1,1) rot 180 setzte das gesperrte Spezialfeld auf z2c2,
   eine Zelle der eigenen Hauptdiagonale bei ausliegender Diagonal-Wertungsplatte;
   Diagonale des Netzes damit strukturell tot (0 gegen 10 Punkte).
4. Runde 3: fast fertige Reihe 6 (tuerkis 5/6) nicht geschlossen, obwohl genau ein
   tuerkis auf dem Tisch lag (in die 1er-Reihe gelegt).
5. Runde 5: Chipwahl ohne Ruecksicht auf die kuerzeste Luecke (zwei ungenutzte Chips).
6. Partieende mit drei angefangenen langen Reihen (par.8.13-Muster).
Eigene Fehler des Agenten: Startplatte mit Spezialfeld auf dem unwahrscheinlichsten
Platz, Chips zu frueh ausgegeben, Slots (1,2)/(2,1) bis Runde 4 frei gelassen (-9
Spezialfelder). Werkzeug-Maengel notiert: `KI:`-Zeile zeigt Aktionsbeschreibung mit
falschen Zaehlern, gefuelltes Spezialfeld nicht vom leeren unterscheidbar.
Restprogramm: 9 Partien (4 als Erst-, 5 als Zweitspieler).
**PAUSIERT (Nutzer 2026-09-06, 23:45, woertlich: "die kannst pausieren, die machen wir
vermutlich mit v25 weiter"):** die neun Partien laufen nicht gegen v24-b06; Wiederaufnahme
voraussichtlich gegen den v25-Champion, Aufruf und Agenten-Auftrag wie in STATUS
Abschnitt 1 der Uebergabe vom 2026-09-06 21:46 beschrieben (g02-g05 `--claude-side 0`,
g06-g10 `--claude-side 1 --first-player 0`, Halter davor, Marke danach loeschen).

## par.8 Nutzer-Entscheide (2026-09-06, 12:40, woertlich: "partienanzahl 10 ist ok, gegner champ @400 ist ok, uebereinstimmungsmessung nein, werkzeug bleibt dann in tools.")

1. **Zahl der Partien: 10**, je fuenf als Erst- und Zweitspieler. ENTSCHIEDEN.
2. **Gegner: Champion `v23-b01_k3p10` @400** (wie "expert"). ENTSCHIEDEN.
3. **Tiling: Claude legt SELBST** (Nutzer 12:50: "tiling spielst selber"). ENTSCHIEDEN;
   par.3.1 entsprechend: freies Legen je Stein (`tile <reihe> <r> <c>`), Chips und
   Raeumen ausdruecklich, KEINE Loeser-Kandidaten in der Anzeige (sie wuerden die
   eigene Wahl anleiten).
4. **Uebereinstimmungs-Messung (par.4.3): NEIN.** ENTSCHIEDEN; par.4.3 entfaellt,
   die Netz-Vorschlaege werden nicht berechnet.
5. **Weg 2 nur als Rueckfall** (Nutzer 12:50: "weg 2 als rueckfall ist ok"). ENTSCHIEDEN.
6. **Verbleib: das Werkzeug bleibt in `tools/`** (`tools/claude_play.py`).
   ENTSCHIEDEN; par.3.5 entsprechend: kein Abbau nach par.7.
7. **Wer spielt: ein SUBAGENT** (Nutzer 16:46: "Wichtig ist nur dass das Spiel gegen dich
   via subagent gestartet wird. Dein Modell ist zu teuer fuer diese spielerein").
   ENTSCHIEDEN: die Partien fuehrt ein Subagent (Modell Opus, mittlerer Aufwand,
   CLAUDE.md-Vorgabe) ueber `tools/claude_play.py`; der Koordinator startet ihn im
   CPU-freien Fenster, prueft sein Protokoll (par.4.4) nach Regel 0 und registriert
   hier. "Claude" in dieser Prereg meint ab jetzt den Subagenten.

## par.9 AUDIT 2026-09-10 (Nutzer-Auftrag "ueberpruefe par.7"), vor der Wiederaufnahme

Geprueft am Code, je Punkt mit Pruefstelle:

1. **Gefuelltes Spezialfeld nicht vom leeren unterscheidbar: STIMMTE, behoben.**
   `cell_char` (`tools/claude_play.py:172-183`) gab fuer `filled == "special"` dasselbe
   `#` zurueck wie fuer ein leeres Spezialfeld. Jetzt: leeres Spezialfeld `#`, gefuelltes
   `@`; Legende in `render` nachgezogen. Reiner Anzeige-Fix, kein Engine-Eingriff.
2. **`KI:`-Zeile mit unzuverlaessigen Zaehlern (g01-Notizen 19:59): NICHT geklaert.**
   Die Zeile zeigt `action.description` aus `ai_step_net_json`; im Hauptpfad wird die
   Beschreibung VOR dem Anwenden gebaut (`engine/src/py.rs:781` gegen `:793`), was die
   beobachteten Nullzaehler ("0x Stein rot von F1") nicht erklaert. Reproduktion braucht
   eine Partie, also die Maschine; bis dahin gilt die Warnung aus par.7: verlaesslich sind
   Raster, Musterreihen-Zeile und die Klartextzeilen in `game.log`, nicht die `KI:`-Zeile.
3. **Die zwei Werkzeug-Blocker aus g01 sind abgeraeumt:** Pass schreibt seit 2026-09-07
   eine eigene Logzeile (`game.rs:816-824`, Kategorie PASS im Replayer); Mondzuege werden
   mit `mond:<farben>` gelistet und angenommen (`claude_play.py:261`, `:314`).
4. **`show` druckt keine Engine-Logzeilen**, nur Raster, Musterreihen, legale Zuege
   (`claude_play.py:408-419`); `drive_ai` druckt je Netz-Zug nur die `KI:`-Zeile
   (`:151`, `:165`). Die volle Engine-Logliste liegt aber in `game.log` auf der Platte
   (`append_log`, `:124-131`), inklusive der Rueckgabe-Reihenfolge der Kuppelplatten mit
   Kachel-ID. Ein Agent, der die Datei liest, sieht sie.
5. **Sichtbarkeit der Rueckgabe-Reihenfolge ist ein offener Nutzer-Entscheid**, kein
   Werkzeugfehler: `game.rs:262-269` registriert vom 2026-08-09, dass der Gegner sie SIEHT;
   `PREREG_dome_stack_information_sets.md` par.4 modelliert sie als unbekannt (dort par.14
   Punkt 3, Lesarten (a)/(b)). **ENTSCHIEDEN 2026-09-10 (Nutzer): nur der Ausfuehrende
   sieht seine Reihenfolge** (Lesart b). Vor der Wiederaufnahme: Engine-Logzeile ohne IDs,
   `claude_play.py` trennt `game.log` (Anzeige, ohne `#`-Zeilen) von `.engine.log` (voll,
   fuer den Replayer); Patch 2026-09-10 vorbereitet, Build und Rauchtest auf freier
   Maschine. Der Agent der Partien liest NUR `show` und `game.log`, nie `.engine.log`
   (in den Auftrag aufnehmen).
6. **Gegner bei Wiederaufnahme:** ohne `--opponent` liest das Werkzeug `models/champion.txt`
   (`claude_play.py:461`, `:470`), also den amtierenden Champion (heute `v26-b01_brierbest`);
   par.8.2 (`v23-b01_k3p10`) und der Kopf (`v25`) sind ueberholt. Der Gegner der Partie steht
   im Manifest je Partie und gehoert beim Registrieren in die Ergebniszeile.
