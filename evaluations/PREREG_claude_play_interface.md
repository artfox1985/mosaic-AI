<!-- STATUS: OFFEN | Frage: Was lernt ein Beobachter, der selbst gegen das Champion-Netz spielt, ueber dessen Schwaechen, das die Arenen nicht zeigen -- und stimmt die Spielstaerke des Netzes aus Spielersicht mit der Leiter ueberein? | Beleg: Nichts gespielt; Bau von tools/claude_play.py laeuft seit 2026-09-06 12:40. Nutzer-Entscheide par.8: 10 Partien (5/5), Gegner Champion @400, keine Uebereinstimmungsmessung, Werkzeug bleibt in tools/. Bauform par.3, Messgroessen par.4, Ergebnisse par.7. -->

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

Noch nichts gespielt.

## par.8 Nutzer-Entscheide (2026-09-06, 12:40, woertlich: "partienanzahl 10 ist ok, gegner champ @400 ist ok, uebereinstimmungsmessung nein, werkzeug bleibt dann in tools.")

1. **Zahl der Partien: 10**, je fuenf als Erst- und Zweitspieler. ENTSCHIEDEN.
2. **Gegner: Champion `v23-b01_k3p10` @400** (wie "expert"). ENTSCHIEDEN.
3. **Tiling:** Loeser-Kandidaten als Normalfall, freies Legen als Ausnahme
   (Vorschlag; gilt, solange der Nutzer nichts anderes sagt).
4. **Uebereinstimmungs-Messung (par.4.3): NEIN.** ENTSCHIEDEN; par.4.3 entfaellt,
   die Netz-Vorschlaege werden nicht berechnet.
5. **Weg 2 nur als Rueckfall** (Vorschlag; gilt, solange der Nutzer nichts anderes
   sagt).
6. **Verbleib: das Werkzeug bleibt in `tools/`** (`tools/claude_play.py`).
   ENTSCHIEDEN; par.3.5 entsprechend: kein Abbau nach par.7.
