<!-- STATUS: OFFEN | Frage: Was lernt ein Beobachter, der selbst gegen das Champion-Netz spielt, ueber dessen Schwaechen, das die Arenen nicht zeigen? | Beleg: g02-g05 gegen v27-b01 @400 gespielt (par.7), Claude 3:1 (55:43, 66:48, 36:28, 50:55). Zwei Muster in allen vier Partien: die Ziehzahl folgt dem Punktestand (bei 0 durchsucht das Netz den Stapel, 21 Ziehungen in g04 R1; in g05 nie auf 0, darum nur 7), und es fuellt lange Musterreihen mit Farben, die seine Kuppelzeile nicht aufnehmen kann (fuenfmal, in g04 zehn Steine auf einmal). g06-g10 offen. -->

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

**WIEDERAUFNAHME 2026-09-10/11 (Nutzer-Auftrag: g02-g05 gegen den amtierenden Champion).
g02 (Seed 20260911, Claude Spieler 0 UND Erstspieler, Gegner `v27-b01_brierbest` @400, Spec
`models/frozen_champions/v27-b01/spec.json`; Gegner und Spec-Pfad aus `manifest.json` der
Partie): Claude 55 : 43 Netz, Claude gewinnt.** 77 Claude-Zuege, Log
`evaluations/artifacts/claude_play/g02/game.log` (351 Zeilen), Notizen `notes.md`.
Wertungsplatten dieser Partie: Spezialfelder (-3 je leerem Feld), Aeussere Felder (+1 je
Randfliese), Farbenreiche Reihen (+4 je Reihe mit >= 5 Farben) -- KEINE Spalten-, Diagonal-
oder Eckplatte.

**Endwertung je Kriterium** (game.log Z. 344-351): Claude Spezialfelder -3, Aeussere Felder
+12, Farbenreiche Reihen +4 (Summe +13); Netz Spezialfelder -9, Aeussere Felder +11,
Farbenreiche Reihen 0 (Summe +2).

**Standard-Kennzahlen** (aus dem Endraster der `show`-Ausgabe, n = 1 Partie, Grundmenge
Endstellung, Einheit Zellen bzw. Punkte):

- *Reihenauslastung Kuppel*: Claude 21 Steine (z0 5/6, z1 6/6, z2 5/6, z3 4/6, z4 1/6,
  z5 0/6); Netz 16 (z0 4, z1 4, z2 2, z3 2, z4 2, z5 2).
- *Spaltenauslastung*: Claude 0 volle Spalten, hoechste Spalte 5 (Spalte 5), drei Spalten
  mit >= 4; Netz 2 VOLLE Spalten (0 und 1), dort liegen 12 seiner 16 Steine.
- *Strafleistenauslastung*: Claude 8 Fliesen (R3 vier = -10, R5 vier = -10, eine weitere
  lief in den Turm) plus Startmarker in R3 und R4 (-4), zusammen -24; Netz 5 Fliesen
  (R2 vier = -10, R3 eine = -1) plus Startmarker in R1, R2, R5 (-6), zusammen -17 nominal,
  davon -12 in R2 durch die Null-Klammer wirkungslos (Z. 148).
- *Punkte und Marge*: 55 : 43, Marge +12 fuer Claude.

**Beobachtungen** (Zeilen in `game.log`):

1. **Stapel-Ziehungen 28, davon 23 bei Punktestand 0** (Z. 26-38, 94-102, 172-193, 263).
   Runde 1: das Netz zog den KOMPLETTEN Reststapel, 13 von 13 Platten, fuer EINE Platte und
   legte 12 zurueck (Z. 39); die ersten fuenf Ziehungen verbrauchten seinen gesamten
   Startvorrat (5 -> 0, Z. 26-30), die restlichen acht waren gratis. Runde 2: 9 Ziehungen,
   alle bei 0. Runde 3: 5, alle bei 0. Runde 4, bei Stand 12: genau EINE. Das g01-Muster ist
   damit bestaetigt und geschaerft: bei Stand 0 wird die verdeckte Ziehung zur vollstaendigen
   Durchsicht des Stapels, bei positivem Stand zieht das Netz sparsam.
2. **Die Null-Klammer deckte eine ganze Runde**: das Netz stand ab Runde 1 auf 0 und nahm in
   Runde 2 vier Strafleisten-Fliesen plus Startmarker (-12, Z. 148) ohne jede Wirkung.
3. **Spaltenbau ohne Spaltenplatte**: es baute Spalte 0 und Spalte 1 voll, obwohl "Vertikale
   Reihen" nicht auslag, und liess dafuer 3 Spezialfelder leer (-9) und jede farbenreiche
   Reihe aus. Kandidat fuer eine Sonde: Spaltenpraeferenz gegen die tatsaechlich ausliegenden
   Wertungsplatten.
4. **Senken-Disziplin**: das Netz hielt lange Musterreihen (R3 mit 4, R5 mit 6 Plaetzen) bis
   zum Rundenende leer und konnte die Reststeine strafarm aufnehmen.
5. **Gezieltes Wegnehmen**: dreimal nahm es genau den Stein, den Claude als naechstes
   brauchte (R3 die zwei Blau der grossen Fabrik, R4 das letzte Tuerkis, R5 das letzte Rot).
6. **Werkzeug, par.9 Punkt 2 erneut belegt**: die `KI:`-Zeile meldete "Reihe 4 [4/4]
   (+1 Strafleiste)", waehrend der Zustand danach R3:S3/4 und eine LEERE Strafleiste zeigte.

**Eigene Fehler:**

a. Runde 3 und Runde 5 waren alle sechs Musterreihen belegt oder farblich festgelegt; am
   Rundenende war jeweils nur noch der Zug auf die Strafleiste legal (zweimal -10). Das Netz
   machte es umgekehrt (Beobachtung 4). Teuerster Fehler der Partie: 20 Punkte.
b. In Runde 5 hatte z1 keine freie Normalzelle mehr, R1 war damit eine Zwangsraeumungs-Falle
   und schied als Senke aus.
c. Startmarker zweimal genommen (-4); der Tempo-Gewinn in Runde 4 wurde durch Beobachtung 5
   wieder eingesammelt.

**g03 (2026-09-11; Seed 20260912, Claude Spieler 0, NETZ Erstspieler, Gegner
`v27-b01_brierbest` @400, Spec `models/frozen_champions/v27-b01/spec.json` aus dem Manifest):
Claude 66 : 48 Netz, Claude gewinnt.** 77 Claude-Zuege, Log 354 Zeilen. Wertungsplatten:
Eckplatten (3 Pkt je vollstaendige obere, 8 je untere Eckplatte), Farbenreiche Reihen,
Spezialfelder.

**Endwertung je Kriterium** (game.log Z. 344-354): Claude Eckplatten +6, Farbenreiche Reihen
+4, Spezialfelder 0 (Summe +10); Netz Eckplatten +11, Farbenreiche Reihen 0, Spezialfelder -9
(Summe +2).

**Standard-Kennzahlen** (Endraster, n = 1 Partie, Grundmenge Endstellung, Einheit Zellen bzw.
Punkte):

- *Reihenauslastung Kuppel*: Claude 21 Steine (z0 6/6, z1 6/6, z2 4, z3 3, z4 1, z5 1);
  Netz 19 (z0 6/6, z1 5, z2 2, z3 2, z4 2, z5 2).
- *Spaltenauslastung*: je 1 volle Spalte (Claude Spalte 5, Netz Spalte 0); Claude zusaetzlich
  zwei Spalten mit 4, das Netz eine mit 5.
- *Strafleistenauslastung*: Claude 6 Fliesen (R2 1, R3 1, R4 4) plus Startmarker in R2 und R5,
  Rundenstrafen -3/-1/-10/-2 = -16, dazu 1 Punkt fuer die einzige eigene Stapelziehung;
  Netz 6 Fliesen plus Startmarker in R1, R3, R4, Rundenstrafen -2/-3/-5/-6 = -16.
- *Punkte und Marge*: 66 : 48, Marge +18 fuer Claude.

**Beobachtungen** (Zeilen in `game.log`):

1. **Die Ziehzahl haengt am Punktestand, nicht an der Stellung** (Z. 26-38, 94-102, 172, 263).
   Netz-Ziehungen gesamt 24: Runde 1 dreizehn (die ersten fuenf verbrauchten den gesamten
   Startvorrat 5 -> 0, die uebrigen acht gratis), Runde 2 neun (eine kostete den letzten
   Punkt, acht gratis), Runde 3 GENAU EINE bei Stand 11 -> 10, Runde 4 GENAU EINE bei
   28 -> 27. Zusammen mit g02 (28 Ziehungen, 23 bei Stand 0) ist das Muster dreimal belegt:
   bei Stand 0 wird die verdeckte Ziehung zur vollstaendigen Stapel-Durchsicht, bei
   positivem Stand zieht das Netz genau einmal.
2. **Zwangsraeumung der langen Musterreihe, zweimal** (Z. 262, 330): "Musterreihe 6 (gelb)
   nicht platzierbar -> 2x Strafleiste" in Runde 4 und dasselbe mit tuerkis in Runde 5. In
   der Kuppelzeile z5 des Netzes waren nur blau- und rot-Zellen frei; es legte trotzdem
   zweimal eine nicht platzierbare Farbe in die 6er-Reihe und zahlte je zwei Strafleisten-
   Fliesen. Das ist derselbe Fehler, den Claude in g02 gemacht hat, hier vom Netz.
3. **Strafleiste genommen, obwohl eine leere 6er-Reihe frei war** (Z. 301-302): "KI: 1x rot
   von F4 -> Strafleiste (-1)", waehrend die eigene Musterreihe 6 leer war und den Stein
   strafffrei aufgenommen haette. Spaeter fuellte es dieselbe Reihe mit tuerkis, das dann
   zwangsgeraeumt wurde (Beobachtung 2).
4. **Eckstrategie erkannt**: das Netz besetzte beide unteren Ecken frueh mit SPEZIAL-Platten
   (Spezialfeld = die vierte Zelle gratis) und holte 11 Eckpunkte gegen Claudes 6. Es
   bezahlte das mit -9 Spezialfeldern an anderer Stelle; unter dem Strich blieben ihm 2
   Endwertungspunkte gegen 10.
5. **Gezieltes Wegnehmen** wie in g02: in Runde 4 nahm es unmittelbar nach Claudes
   Plattenzug die zwei letzten Tuerkis, die Claudes Reihe 3 fehlten.

**Eigene Fehler:**

a. Runde 4: Claude zahlte -10 Strafleiste, um EIN Blau aus einem Mondstapel freizugraben
   (zwei Schwarz Ueberlauf, zwei Rot obendrauf). Der Zug war den Preis wert (er schloss die
   obere Zeile, eine Ecke und ein Spezialfeld, zusammen 13 Punkte), aber der Engpass entstand
   vorher: das freie Blau der grossen Fabrik wanderte in den Mondpool, wo das Netz es nahm.
b. Runde 2: Startmarker genommen (-2), weil nach dem eigenen Zug auf die Sonnenseite der
   grossen Fabrik JEDER Mondzug den Pool beruehrte. Wer die grosse Fabrik anzapft, macht
   damit alle folgenden globalen Mondzuege markerpflichtig.
c. Runde 2: Reihe 2 auf z2c0 statt auf die Wildzelle z2c2 gelegt (1 statt 3 Punkte), um die
   Wildzelle aufzusparen; die Flexibilitaet wurde spaeter nicht gebraucht.

**g04 (2026-09-11; Seed 20260913, Claude Spieler 0 UND Erstspieler, Gegner
`v27-b01_brierbest` @400, Spec `models/frozen_champions/v27-b01/spec.json` aus dem Manifest):
Claude 36 : 28 Netz, Claude gewinnt.** 76 Claude-Zuege, Log 346 Zeilen. Wertungsplatten:
Spezialfelder, Eckplatten (3/8), Vertikale Reihen (7 Pkt je volle Spalte). Die niedrigste
Punktzahl der Serie auf beiden Seiten: die Auslage warf ab Runde 3 nur noch Spezialplatten
aus, und beide Seiten endeten mit je VIER leeren Spezialfeldern (-12).

**Endwertung je Kriterium** (game.log Z. 339-346): Claude Spezialfelder -12, Eckplatten +3,
Vertikale Reihen +7 (Summe -2); Netz Spezialfelder -12, Eckplatten +3, Vertikale Reihen 0
(Summe -9).

**Standard-Kennzahlen** (Endraster, n = 1 Partie, Grundmenge Endstellung):

- *Reihenauslastung Kuppel*: Claude 17 Steine (z0 5, z1 5, z2 2, z3 2, z4 1, z5 2);
  Netz 16 (z0 4, z1 5, z2 4, z3 1, z4 1, z5 1).
- *Spaltenauslastung*: Claude 1 VOLLE Spalte (Spalte 0, von oben nach unten aufgebaut,
  Platzierungspunkte 3+4+5+6 plus 7 fuer die Wertungsplatte); Netz 0 volle Spalten,
  hoechste Spalte 5 von 6.
- *Strafleistenauslastung*: Claude R3 drei Fliesen (-6), R5 vier Fliesen plus eine in den
  Turm (-10), Startmarker in R3 und R4 (-4), zusammen -20; Netz Startmarker in R1, R2, R5
  (-6), R4 zehn zwangsgeraeumte Fliesen (Strafleiste voll, -10), R5 eine (-1), zusammen -17.
- *Punkte und Marge*: 36 : 28, Marge +8.

**Beobachtungen** (Zeilen in `game.log`):

1. **Ziehzahl am Punktestand, drittes Mal**: 32 Netz-Ziehungen, 26 davon bei Stand 0.
   Runde 1: 21 Ziehungen (die ersten fuenf verbrauchten 5 -> 0, danach 16 gratis), Runde 2:
   9 (alle bei 0), Runde 3: GENAU EINE bei 9 -> 8, Runde 4: GENAU EINE bei 17 -> 16. Damit
   ist das Muster in g02, g03 und g04 identisch: Stand 0 = Stapel durchsuchen, Stand > 0 =
   genau eine Ziehung.
2. **Zwangsraeumung, gross** (Z. 262-263): "Musterreihe 5 (schwarz) nicht platzierbar ->
   5x Strafleiste" UND "Musterreihe 6 (blau) nicht platzierbar -> 5x Strafleiste" in
   derselben Runde. Das Netz hatte eine volle 5er- und eine volle 6er-Reihe gefuellt, ohne
   dass die zugehoerige Kuppelzeile eine passende freie Zelle hatte: ZEHN Steine auf einmal
   verloren, Strafleiste voll (-10). Zusammen mit g03 (zweimal je zwei Steine) ist das der
   vierte Beleg: das Netz prueft beim Fuellen der langen Musterreihen nicht, ob die Zielzeile
   die Farbe ueberhaupt aufnehmen kann.
3. **Der Vergleich der Endwertung**: identische Spezialfeld-Strafe (-12 zu -12), identische
   Eckpunkte (3 zu 3), Unterschied allein bei der Spalte (7 zu 0). Der Sieg kam aus dem
   Spaltenbau, nicht aus der Endwertung im Uebrigen.

**Eigene Fehler:**

a. Runde 5: einen Schwarz-Stein in die leere Reihe 4 geparkt, obwohl die Kuppelzeile z3 nur
   noch tuerkise Zellen frei hatte -> Zwangsraeumung, ein Stein auf die Leiste. Genau der
   Fehler aus Beobachtung 2, in klein.
b. Runde 5: am Rundenende waren alle sechs Musterreihen farblich festgelegt, sodass drei
   erzwungene Rot-Zuege -7 kosteten (dieselbe Senken-Falle wie in g02).
c. Ab Runde 3 gab es nur noch Spezialplatten; zwei davon landeten in der unteren Slotreihe,
   wo R4/R5 nie drei Zellen fuellen konnten (-6 davon). Frueher haette man mit Ziehungen
   (1 Punkt je Zug) Wildplatten sichern koennen, solange der Stapel noch welche hatte.

**g05 (2026-09-11; Seed 20260914, Claude Spieler 0, NETZ Erstspieler, Gegner
`v27-b01_brierbest` @400, Spec `models/frozen_champions/v27-b01/spec.json` aus dem Manifest):
Claude 50 : 55 Netz, NETZ GEWINNT** -- die erste Niederlage der Serie. 77 Claude-Zuege, Log
331 Zeilen. Wertungsplatten: Mehrfarbige Felder (2 Pkt je Wildfeld, aber nur wenn ALLE
belegt sind), Aeussere Felder, Farbenreiche Reihen.

**Endwertung je Kriterium** (game.log Z. 324-331): Claude Mehrfarbige Felder +8 (alle vier
Wildfelder belegt), Aeussere Felder +9, Farbenreiche Reihen +4 (Summe +21); Netz Mehrfarbige
Felder 0 (zwei Wildfelder leer), Aeussere Felder +9, Farbenreiche Reihen 0 (Summe +9).
Claude gewann die Endwertung mit 21:9 und verlor die Partie trotzdem.

**Standard-Kennzahlen** (Endraster):

- *Reihenauslastung Kuppel*: Claude 18 Steine (z0 5, z1 5, z2 3, z3 3, z4 2, z5 0);
  Netz 20 (z0 4, z1 4, z2 4, z3 2, z4 2, z5 4).
- *Spaltenauslastung*: keine volle Spalte auf beiden Seiten; Claude hoechste Spalte 5
  (Spalte 3), zwei Spalten mit 4.
- *Strafleistenauslastung*: **Claude -32 in Strafen** (R1 Marker -2, R2 -12 = Leiste voll
  plus Marker, R3 -12 dito, R4 -3, R5 -3), davon zweimal die volle Leiste; Netz -8 (Marker
  in R4 und R5, dazu drei zwangsgeraeumte Fliesen in R5). Das ist die Partie in einer Zahl:
  24 Strafpunkte Unterschied bei 5 Punkten Endabstand.
- *Punkte und Marge*: 50 : 55, Marge -5.

**Beobachtungen** (Zeilen in `game.log`):

1. **Die Ziehzahl folgt dem Punktestand -- Gegenprobe**: in dieser Partie fiel das Netz NIE
   auf 0 und zog folglich nur SIEBEN Mal insgesamt (Runde 1 vier Ziehungen von 5 auf 1,
   danach je genau eine bei 4->3, 13->12, 28->27). In g02/g03/g04 dagegen 28/24/32
   Ziehungen, jeweils mit langen Serien bei Stand 0. Damit ist die Regel in beide
   Richtungen belegt: das Netz zieht sparsam, solange Punkte kosten, und durchsucht den
   Stapel, sobald sie es nicht mehr tun.
2. **Zwangsraeumung, fuenfter Beleg** (Z. 310): "Musterreihe 4 (gelb) nicht platzierbar ->
   3x Strafleiste".
3. **Das Netz gewinnt hier ohne Endwertung**: 9 Endwertungspunkte gegen 21, aber ein
   Vorsprung von 17 aus dem laufenden Spiel. Sein Spiel ist auf Platzierungspunkte und
   Strafvermeidung gebaut, nicht auf die ausliegenden Wertungsplatten -- dasselbe Bild wie
   in g02 (Spaltenbau ohne Spaltenplatte) und g04 (-12 Spezialfelder).

**Eigene Fehler (diese Partie hat Claude verloren, nicht das Netz gewonnen):**

a. **Runde 2 und Runde 3 je -12**: beide Male waren am Rundenende alle sechs Musterreihen
   farblich festgelegt, und die Reststeine (Tuerkis, Rot) hatten in keiner Kuppelzeile eine
   freie Zelle. Dieselbe Senken-Falle wie in g02 und g04, hier zweimal in Folge und
   spielentscheidend. Die Lehre steht damit dreimal im Protokoll: **eine lange Musterreihe
   muss bis zum Rundenende eine Farbe aufnehmen koennen, die noch auf dem Tisch liegt.**
b. Runde 1: den Startmarker fuer drei Blau genommen (-2), obwohl der Zug nicht nötig war;
   in Runde 2 und 3 kam er nochmals dazu, weil nach dem Anzapfen der grossen Fabrik jeder
   globale Mondzug den Pool beruehrte.
c. Reihe 5 (6 Plaetze) wurde in Runde 1 mit einem einzelnen Schwarz belegt und blieb damit
   die ganze Partie als Senke unbrauchbar; genau dieser Stein haette die spaeteren
   Zwangszuege aufgefangen.

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

7. **Rauchtest 2026-09-10, 18:15-18:30, GRUEN** (Partie `gsmoke`, Seed 20260910, Claude
   Spieler 0, Gegner `v27-b01_brierbest` @50, Spec ueber den neuen Rueckfall
   `models/frozen_champions/v27-b01/spec.json`): `new` legt `game.log` (nur Anzeige, 0
   Zeilen mit `#`) und `.engine.log` (Kopfzeilen plus voller Strom) an; `move "start 5 2 2 0"`
   wird angenommen, das Netz zieht, `show` rekonstruiert danach aus `.engine.log` ohne
   Divergenz. Der Rauchtest fand den Spec-Fehler des Servers (STATUS Abschnitt 1): ohne den
   Rueckfall brach `new` mit FileNotFoundError ab, waehrend `server.py` an derselben Stelle
   STILL auf Env-Defaults zurueckfiel. **Bereit fuer g02-g10**; Auftrag an den
   Partien-Agenten: nur `show`, `move`, `note` und `game.log` benutzen, `.engine.log` nie
   lesen; `--sims 400`; Gegner ohne `--opponent` (= `models/champion.txt`); je Partie den
   Gegner und den Spec-Pfad aus dem Manifest in die Ergebniszeile.
