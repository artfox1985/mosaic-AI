<!-- STATUS: OFFEN | Frage: Was zeigt eigenes Spiel gegen das Champion-Netz, das die Arenen nicht zeigen? | Beleg: 6 Partien (par.7): g02-g05 gegen v27-b01 3:1, g06/g07 gegen v28-b02 1:1. Das Netz punktet aus Platzierungen, nicht aus den Wertungsplatten (Endwertung 0:10 und 2:8), und nutzt die Null-Klammer als Werkzeug (Arm A live belegt). SICHTGLEICHHEIT GILT IN KEINE RICHTUNG (par.10): vier Stellen sehe ich mehr (Beutel/Turm getrennt, Chipanzahl, Vorderseiten gezogener Platten, Historie), zwei sieht das Netz mehr (Stapelmaske, Rueckgabebloecke). Werkzeug par.9 P.11-14. -->

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
**g06 (2026-09-11; Seed 20260915, Claude Spieler 1, NETZ Erstspieler, Gegner
`v28-b02_brierbest` @400, Spec `models/frozen_champions/v27-b01/spec.json` aus dem Manifest):
Claude 70 : 64 Netz, CLAUDE GEWINNT** -- erste Partie gegen die v28-Generation. 79
Claude-Zuege. Wertungsplatten: Mehrfarbige Felder (2 Pkt je Wildfeld, nur wenn ALLE belegt),
Diagonale Reihen (10 Pkt je vollstaendige Diagonale), Farbenreiche Reihen.

**Endwertung je Kriterium** (Manifest `result.end_scoring`): Claude Mehrfarbige Felder +6
(alle drei Wildfelder belegt), Diagonale 0, Farbenreiche Reihen +4 (Summe +10); Netz in
ALLEN DREI Kriterien 0 (Summe 0). Das Netz holte seine 64 Punkte vollstaendig aus dem
laufenden Spiel.

**Standard-Kennzahlen** (Endraster):

- *Reihenauslastung Kuppel*: Claude 21 Steine (z0 5, z1 6, z2 5, z3 4, z4 1, z5 0);
  Netz 18 (z0 4, z1 4, z2 3, z3 3, z4 2, z5 2).
- *Spaltenauslastung*: **das Netz hatte ZWEI volle Spalten** (Spalte 0 und 1, je 6 von 6),
  obwohl keine Spaltenplatte im Spiel war; Claude keine volle Spalte, hoechste Spalte 5
  (Spalte 3), vier Spalten mit >= 4.
- *Strafleistenauslastung*: Claude -15 (R1 Marker -2, R2 -6 aus drei Zwangssteinen, R3 -1,
  R4 -3 = Marker plus ein Stein, R5 -3 aus zwei Steinen); Netz -8 (Marker in R2 und R3,
  je -2; R4 -1; R5 -3). Differenz 7 Strafpunkte bei 6 Punkten Endabstand.
- *Punkte und Marge*: 70 : 64, Marge +6.

**Stapelziehungen**: Netz VIER, alle einzeln und alle bei Punktestand > 0 (5->4, 7->6,
12->11, 28->27); Claude keine. Das Netz fiel in dieser Partie nie auf 0.

**Beobachtungen**:

1. **Plattenblind, aber stark**: 0 von 10 moeglichen Endwertungspunkten ueber drei
   Kriterien, und trotzdem 64 Punkte. Zwei seiner drei Wildfelder blieben leer, keine
   Reihe erreichte fuenf Farben, keine Diagonale wurde geschlossen. Vierter Beleg derselben
   Linie (g02, g04, g05, g06).
2. **Spaltenbau laeuft unabhaengig von der Wertungsplatte**: zwei volle Spalten ohne
   Spaltenkriterium. Das passt zum Strukturbefund "Champion vollendet keine Spalten" nur
   dem Anschein nach: er vollendet sie hier sehr wohl -- nur zahlt es in dieser Auslage
   nichts. Kandidat fuer eine eigene Sonde (Spaltenquote bedingt auf die ausliegende Platte).
3. **Die Chip-Aufdeckung entscheidet, wer den Restmuell frisst.** Bonuschips liegen unter
   den letzten Steinen einer Fabrik. Wer den letzten Stein raeumt, deckt den Chip fuer den
   Gegner auf. In R2 und R5 hat mich genau das getroffen: die KI nahm den einzigen
   aufgedeckten Chip, danach war der Steinblock meine einzige legale Aktion.
4. Das Netz nahm den Startmarker zweimal freiwillig (R2, R3), um zwei Tuerkis bzw. vier
   Gelb in einem Zug zu holen -- es bewertet den Zugriff hoeher als die -2.

**Eigene Fehler:**

a. **R2 -6**: mit dem Schwarz-Zug Fabrik 3 geleert, damit den Chip fuer die KI aufgedeckt,
   und danach blieb als einzige legale Aktion der Dreierblock Rot -> volle Strafleiste.
   Lehre: bei der Restzugrechnung zaehlen die AUFGEDECKTEN Chips, nicht die vorhandenen.
b. **R5, 4 Punkte verschenkt**: R2 mit Gelb gefuellt, um das Wildfeld (2,5) zu belegen --
   Gelb lag aber schon auf (2,2), war also keine fuenfte Farbe. Blau waere richtig gewesen.

**g07 (2026-09-11; Seed 20260916, Claude Spieler 1, NETZ Erstspieler, Gegner
`v28-b02_brierbest` @400, Spec wie oben): Claude 45 : 58 Netz, NETZ GEWINNT.** 77
Claude-Zuege. Wertungsplatten: Aeussere Felder, **Spezialfelder (-3 je LEEREM
Spezialfeld)**, Farbenreiche Reihen.

**Endwertung je Kriterium** (Manifest): Claude Aeussere Felder +10, Spezialfelder -6 (zwei
leer), Farbenreiche Reihen +4 (Summe +8); Netz Aeussere Felder +11, Spezialfelder -9 (drei
leer), Farbenreiche 0 (Summe +2). Claude gewann die Endwertung 8:2 und verlor die Partie um
13 -- dasselbe Muster wie g05.

**Standard-Kennzahlen** (Endraster):

- *Reihenauslastung Kuppel*: Claude 18 Steine (z0 5, z1 6, z2 3, z3 3, z4 1, z5 0);
  Netz 20 (z0 5, z1 5, z2 3, z3 3, z4 2, z5 2).
- *Spaltenauslastung*: Netz eine volle Spalte (Spalte 1), daneben eine mit 5; Claude keine
  volle, hoechste 5 (Spalte 1), zwei Spalten mit >= 4.
- *Strafleistenauslastung*: **Claude -25** (R2 -12 = volle Leiste plus Marker, R4 -10 =
  volle Leiste, R5 -3), Netz -11 (R1 -3, R2 -3, R3 -2, R4 -2, R5 -1). 14 Strafpunkte
  Unterschied bei 13 Punkten Endabstand -- die Partie in einer Zahl.
- *Punkte und Marge*: 45 : 58, Marge -13.

**Stapelziehungen -- der schaerfste Beleg der Serie**: Netz 33 Ziehungen, Claude 3.
Aufgeschluesselt nach Punktestand beim Zug:

| Zug | Stand vorher | Ziehungen in DIESEM Zug |
| --- | --- | --- |
| Netz R1 | 5 | **13** (fuenf bezahlt, ab Stand 0 acht gratis) |
| Netz R2 | 0 | **8** |
| Netz R2 | 0 | **7** |
| Netz R3 | 0 | **4** |
| Netz R4 | 12 | **1** |
| Claude R2 | 7 | 2 |
| Claude R3 | 0 | 1 |

Bei Stand > 0 zieht das Netz genau einmal, bei Stand 0 vier- bis dreizehnmal. Zusammen mit
g06 (nie auf 0, vier Einzelziehungen) und g05 (dieselbe Gegenprobe) ist damit **Arm A der
`PREREG_corpus_behaviour_audit.md` an lebenden Partien bestaetigt**, bevor der Korpuslauf
ueberhaupt gefahren ist.

**Beobachtungen**:

1. Das Netz meidet Spezialplatten NICHT, obwohl sie in dieser Auslage -3 je leerem Feld
   kosten: es endete mit drei leeren Spezialfeldern (-9). Die ausliegende Platte aendert
   sein Plattenwahlverhalten nicht -- dritter unabhaengiger Beleg der Plattenblindheit
   (nach g04 und g06).
2. Es gewinnt trotzdem, weil es beim Platzieren dominiert: +29 in einem einzigen Tiling
   (R4) und +19 in einem zweiten (R5), gebaut aus langen waagerechten und senkrechten
   Linien.
3. Der Null-Klammer-Zug ist bei ihm kein Unfall, sondern ein Werkzeug: es faellt in R1
   bewusst von 5 auf 0 und durchsucht danach den halben Stapel gratis.

**Eigene Fehler:**

a. **R4, rund -5**: Platte #10 auf Slot (2,1) mit Rotation 0 gelegt; dadurch landete ihre
   Schwarz-Zelle in z5 statt in z4, und meine zwei geparkten Schwarz in R4 hatten keine
   Zielzelle mehr -> Zwangsraeumung. Mit Rotation 180 waere (4,3) schwarz gewesen. Die
   Warnzeile des Werkzeugs ("ZWANGSRAEUMUNG beim Tiling") erscheint erst NACH dem Legen.
b. **R2 -12**: dieselbe Senken-Falle wie in g02/g04/g05. Alle sechs Reihen farblich
   festgelegt, danach fegte Aktion C fuenf Gelb und zwei Schwarz als Block herein.
c. `chips 2` verbrauchte ausgerechnet den blau-tragenden Chip fuer eine Zelle, die drei
   beliebige gebraucht haette; damit fehlte R3 die zweite passende Farbe (-1). Die Auswahl
   trifft die Engine, nicht der Spieler (par.9 P.13).


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

8. **Restprogramm g06-g10: gegen `v28`, sobald es steht (Nutzer 2026-09-11, woertlich:
   "du wirst sobald v28 verfuegbar ist die restlichen spiele gegen v28 machen").** Damit ist
   par.8.2 endgueltig ueberholt (dort stand noch `v23-b01_k3p10`): die zehn Partien der
   Reihe laufen NICHT gegen einen festen Gegner, sondern je gegen den amtierenden Champion
   ihrer Zeit -- g01 gegen v24-b06, g02-g05 gegen v27-b01, g06-g10 gegen v28. Eine
   Siegquote ueber alle zehn ist damit KEINE Groesse: die Partien sind gegen verschiedene
   Gegner gespielt und werden je Block ausgewiesen. Vergleichbar bleibt das Qualitative
   (par.4.4) und, je Gegner getrennt, die sechs Standard-Kennzahlen.

   Seitenwahl wie vorgesehen: `--claude-side 1 --first-player 0`, also Claude als
   ZWEITSPIELER, damit die Reihe am Ende fuenf Partien je Seite hat (g01-g05 waren
   `--claude-side 0`). Gegner ohne `--opponent`, das Werkzeug liest dann `models/champion.txt`
   und loest die Spec ueber das eingefrorene Artefakt auf (par.9 P.6); vor dem Start ist zu
   pruefen, dass im Manifest auch wirklich v28 und dessen Spec stehen.

   **Vor g06: der ausstehende Rauchtest** (par.9 P.10) -- das Werkzeug ist seit den
   Aenderungen vom 2026-09-11 nicht mehr gegen einen lebenden Gegner gelaufen.

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

8. **Die `KI:`-Zeile ist GEFIXT, die Ursache bleibt offen (2026-09-11).** Punkt 2 oben ist
   damit fuer den Spielbetrieb erledigt. Befund aus g02-g05: das ENGINE-Log daneben ist
   korrekt -- dieselbe Aktion steht dort als `2 (2)×`, waehrend die Tool-Zeile
   `0× Stein tuerkis von F1 → Reihe 2 [0/2]` meldete, obwohl die Reihe danach auf 1/2 stand
   (g02 Runde 1), und `[4/4] (+1 Strafleiste)` bei LEERER Strafleiste (g02 Runde 2). Quelle
   ist `action.description` aus `ai_step_net_json`, gebaut in
   `engine/src/mcts.rs::label_search_move` (:624) ueber `tiles_taken` (:599); der Zaehler
   wird dort VOR dem Anwenden aus dem Zustand gelesen, warum er 0 bzw. zu klein herauskommt,
   ist weiter ungeklaert. **Fix im Werkzeug:** `drive_ai` druckt jetzt die sichtbaren
   Logzeilen, die die Engine gerade geschrieben hat (neue Funktion `ai_lines`), statt der
   Beschreibung. Damit sieht der Spieler exakt das, was auch in `game.log` landet. Der
   Engine-Fehler bleibt fuer die Suche selbst folgenlos (die Beschreibung ist reiner
   Anzeigetext), sollte aber bei naechster Gelegenheit nachgesehen werden.

9. **Engine-Luecke: der Validator laesst einen Zug durch, den es nicht gibt (2026-09-11).**
   `validation.rs::validate_small_moon` (:66-85) akzeptiert `SmallFactoryMoon` MIT
   `factory_id`, nimmt also den obersten Stein EINER Fabrik. Aktion C ist laut
   `docs/engine_manual.md` (Phase 1 C) immer global ueber alle Mondbereiche, und
   `generate_valid_moves` erzeugt folgerichtig nur die globale Form (:214). Der Zug ist also
   nur ueber die direkte API erreichbar -- Suche und Self-Play sind nicht betroffen. Der
   Kopf-Docstring dieses Werkzeugs hat ihn als `m1`-`m4` sogar angeboten; das war eine
   Einladung zu einem illegalen Zug. **Fix im Werkzeug:** `m1`-`m4` wird jetzt mit
   Verweis auf das Regelbuch abgewiesen, der Docstring korrigiert. Ob der Validator selbst
   nachgezogen wird, ist ein Nutzer-Entscheid (Engine-Aenderung, Anker-Invarianz faellig).

10. **Drei Bedien-Verbesserungen aus 307 gespielten Zuegen (2026-09-11).**
    (a) `show` nennt jetzt die Pflichten der Runde: `Kuppelplatten x/2, Bonuschips y/2`.
    `dome_tiles_placed_this_round` ist nicht serialisiert (serialize.rs:759), laesst sich
    aber exakt ausrechnen (Startplatte plus zwei je abgeschlossener Runde); in g04 waere die
    Plattenpflicht beinahe verfallen.
    (b) `show` zeigt die **Reihen-Ziele**: je Musterreihe, welche Zellen ihrer Kuppelzeile
    sie noch aufnehmen kann, mit Warnung `ZWANGSRAEUMUNG beim Tiling`, wenn keine Zelle mehr
    passt und alle drei Slots der Zeile belegt sind. Das steht vollstaendig auf dem Brett,
    verletzt die Sichtgleichheit also nicht; es ist die Handrechnung, die jede Runde anfiel
    und die dreimal (g02, g04, g05) zweistellig danebenging.
    (c) Die Zugliste fasst die Zielreihen je Quelle und Farbe zusammen (`s 1 gelb 0-5|floor`)
    statt einer Zeile je Kombination. In Runde 1 waren das mehrere hundert Zeilen; das war
    der groesste Einzelposten am Token-Verbrauch und der Grund, warum `show` meist nur
    gefiltert gelesen wurde.
    **Keine Aenderung** gab es an der Ablehnungs-Ausgabe: `cmd_move` druckt bereits
    `ZUG ABGEWIESEN (...)` und gibt 1 zurueck. Dass drei abgewiesene Zuege in g03/g04
    unbemerkt blieben, lag an der eigenen `grep`-Filterung der Ausgabe, nicht am Werkzeug.
    Lehre fuer den naechsten Auftrag: die Ausgabe von `move` nicht filtern.

    Geprueft: `py_compile` gruen, `compact_rows`, `duty_line`, `row_targets` und `ai_lines`
    an der rekonstruierten Endstellung von g05 gegengerechnet, `s m2 ...` wird abgewiesen.
    **Ein Rauchtest mit lebendem Gegner steht aus** (Maschine belegt durch die v28-Erzeugung)
    und gehoert vor die naechste Partie.

11. **Rauchtest nachgeholt, GRUEN (2026-09-11, g06 Zug 1-3).** Der in Punkt 10 offene Test
    mit lebendem Gegner lief zu Beginn von g06 gegen `v28-b02_brierbest`: die Pflichtzeile
    ("Kuppelplatten 0/2, Bonuschips 0/2"), der Reihen-Ziele-Block und die gruppierte
    Zugliste (`s 1 gelb 0-5|floor mond:blau`) erschienen wie gebaut, die KI-Zeilen kamen aus
    dem Engine-Log statt aus `action.description`. Zwei Partien (156 Claude-Zuege) ohne
    Fehlanzeige.

12. **Werkzeugfehler in g06: `PermissionError` auf `manifest.json` -- und der Gegenzug ging
    verloren (2026-09-11, Runde 2).** OneDrive hatte die Datei waehrend der Synchronisierung
    fuer Sekundenbruchteile gesperrt. Die Stelle ist gefaehrlicher als sie aussieht:
    `drive_ai` ruft `save_manifest` NACH `ai_step_net_json`, aber VOR `append_log` -- der
    schon berechnete Netzzug war damit nur im Speicher und verschwand mit dem Prozess. Die
    Partie selbst blieb konsistent (der Zustand wird bei jedem Aufruf aus `.engine.log`
    rekonstruiert), aber sie stand mit der KI am Zug, und `move` haette nicht durchgekonnt.
    Zwei Gegenmassnahmen gebaut:
    (a) `save_manifest` wiederholt bis zu sechsmal mit 0,5 s Abstand, bevor es aufgibt;
    (b) neues Unterkommando **`step`**, das NUR die KI ziehen laesst, ohne eigenen Zug --
    der Notausgang genau fuer diesen Zustand. In g06 hat er die Partie ohne Verlust
    fortgesetzt.
    Offen (kein Fix, bewusst): die Reihenfolge in `drive_ai` liesse sich umdrehen
    (`append_log` vor `save_manifest`), dann waere der Zug auch ohne Wiederholversuche
    sicher. Das beruehrt die Log-Semantik und gehoert in einen eigenen Zug.

13. **Zwei Bedien-Luecken aus g06/g07, beide haben Punkte gekostet.**
    (a) **Die Zwangsraeumungs-Warnung kommt zu spaet.** `show` warnt erst, wenn die Platte
    schon liegt. In g07 R4 hat genau das -5 gekostet: Platte #10 mit Rotation 0 statt 180
    gelegt, Schwarz landete in z5 statt z4, die zwei geparkten Schwarz in R4 verloren ihre
    Zielzelle. Was fehlt, ist eine **Vorschau je Platzierungskandidat**: welche der eigenen
    belegten Musterreihen nach `d <platte> <slot> <rot>` keine Zielzelle mehr haette. Das
    steht vollstaendig auf dem Brett und verletzt die Sichtgleichheit nicht.
    (b) **`chips <reihe>` hat keine Chipwahl.** Die Engine sucht die Plaettchen selbst aus.
    In g07 R5 verbrauchte sie den einzigen blau-tragenden Chip fuer eine Zelle, die drei
    beliebige gebraucht haette; die danach geplante Vollendung von R3 fiel aus (-1). Ein
    optionales Argument (`chips <reihe> [ids]`) wuerde reichen.

14. **Vier Nachbesserungen aus g06/g07 GEBAUT (2026-09-12), drei davon gegen Fehler, die in
    diesen Partien Punkte gekostet haben.** Alle vier sind reine Brett-Arithmetik und
    verletzen die Sichtgleichheit nicht (dieselbe Begruendung wie bei den Reihen-Zielen,
    P.10b): sie rechnen nur nach, was auf dem Tisch liegt.

    (a) **Platzierungs-Vorschau `placement_warnings`** -- die in P.13a benannte Luecke. Vor
    dem Legen wird fuer JEDE legale Kombination aus Platte, Slot und Drehung geprueft, ob
    danach eine eigene belegte Musterreihe ohne Zielzelle dastuende; ausgegeben werden nur
    die gefaehrlichen, mit zusammengefassten Drehungen:
    `d 7 0 2 rot 90|180  -> R0 B1/1 ohne Zielzelle`. Eine Platte nimmt nie eine Zelle weg --
    gefaehrlich ist nur die LETZTE Platte einer Kuppelzeile, und genau die hat in g07 Runde 4
    rund -5 gekostet.

    (b) **Spezialfeld-Zeilen `special_lines`** -- je leerem Spezialfeld, was seiner Platte
    noch fehlt und was es zahlt: `(4,3) +5, es fehlt: (4,2) G, (5,2) S, (5,3) R`. Das war die
    teuerste Handrechnung der beiden Partien (in g06 drei geplante Freischaltungen mit +4,
    +2 und +6; in g07 zwei leere Felder mit -6).

    (c) **Wertungsplatten-Stand `criteria_lines`** -- je AUSLIEGENDER Platte eine Zeile mit
    dem Stand beider Seiten. Anlass ist ein 4-Punkte-Fehler in g06: R2 wurde mit Gelb
    vollendet, um ein Wildfeld zu belegen, obwohl Gelb in derselben Kuppelzeile schon lag,
    also keine fuenfte Farbe war. Die Zuordnung laeuft ueber den NAMEN der Platte, nicht ueber
    ihre Id -- ein Id-Wechsel in der Engine soll hier nicht still falsch rechnen.

    (d) **Mond-Reihenfolge optional, aber nur wenn eindeutig** (`resolve_moon_order`). Dabei
    ist ein Nebenbefund aufgefallen, der die erste Fassung falsch gemacht haette: **der
    Zuggenerator fuehrt je (Quelle, Farbe, Reihe) nur EINE, kanonische Reihenfolge** --
    abweichende sind trotzdem legal, weil `apply_stone` nur die MENGE der Reststeine prueft.
    Wer die Zahl der Zugeintraege als Mass fuer Wahlfreiheit nimmt, setzt also still den
    Generator-Vorschlag ein; entschieden wird jetzt an der LAENGE der Restliste. Bei echter
    Wahl weist das Werkzeug ab und nennt die Reste samt Vorschlag.

    **Geprueft:** `criteria_lines` und `special_lines` an den rekonstruierten Endstellungen
    von g06 und g07 gegen `result.end_scoring` aus den Manifesten -- die Engine ist hier eine
    unabhaengige Referenz, und alle acht Zahlen stimmen (g06 Wildfelder 6 gegen 0,
    Farbenreiche 4 gegen 0; g07 Aeussere 10 gegen 11, Spezialfelder -6 gegen -9,
    Farbenreiche 4 gegen 0). Dazu **14 neue Unit-Tests** in
    `tools/tests/test_claude_play_board_hints.py`, darunter die g07-Stellung mit Rotation 0
    (Zwangsraeumung) gegen Rotation 180 (kein Verlust) und die Rotationstabelle gegen
    `engine/src/dome.rs:89-97`. Suite 58 Tests gruen. Live-Rauchtest in der Wegwerf-Partie
    `gsmoke2` (nicht Teil der Reihe): Warnung, Kriterien-Zeilen und die Mond-Abweisung
    erschienen wie gebaut; ein dabei gefundener Anzeigefehler (jede Drehung stand vierfach,
    weil `valid_moves` denselben Slot mehrfach fuehrt) ist behoben.

    **Nicht gebaut:** die Chipwahl aus P.13b. `apply_tiling_chips(spieler, reihe)` nimmt
    keine Plaettchenliste; das waere eine Engine-Aenderung und bleibt als solche offen.

## par.10 ZUGKLASSEN-DIFFERENTIAL AUS DEN CLAUDE-PARTIEN (Nutzer 2026-09-12, 17:58: "dann schreib das so ins prereg")

**Befund, der den Absatz traegt:** die Claude-Partien sind die einzige Stelle im Projekt, an der ein
staerkerer Gegner tatsaechlich vorliegt (g02-g05 gegen v27-b01 3:1 fuer Claude, g06/g07 gegen
v28-b02 1:1; `archive/history.md` 2026-09-11). Alle anderen Messungen vergleichen Netze
untereinander oder gegen Heuristiken, die jedes Netz seit v21 zu 82-90 % schlaegt.

**Frage:** an welchen Entscheiden weicht Claude vom Netz ab, und gewinnt danach? Nicht "wie viel
zieht Claude" (das ist die Ziehsucht-Sonde par.9, Stufe 1), sondern WELCHE ZUGKLASSE dem Netz fehlt;
das sagt, welcher Knopf oder welcher Zieltyp ueberhaupt zu bauen waere, bevor man einen baut.

**Instrument (netzfrei fuer Claude, Netz nur als Vergleich, kein Training):**
1. Jede Claude-Partie (`evaluations/artifacts/claude_play/g*/game.log`, Server-Format) wird per
   `analyze_game_log.run` Zug fuer Zug in Zustaende zerlegt (dasselbe Replay wie die Spaltensonde).
2. An jedem Claude-Entscheid (Drafting, Kuppelplatzierung, Startsetzung, Tiling-Schritte, Chips)
   rechnet der Champion mit seinem Arena-Instrument (@400, argmax, ohne Wurzelrauschen, Champion-Spec)
   seinen Zug und den Wurzelwert VOR und NACH Claudes Zug (Sicht Claude).
3. Abweichung = Claudes Zug ungleich Netzzug. Je Abweichung: Aktionsklasse (Quelle x Farbe x Reihe
   bzw. Kuppel-Slot/Rotation, Start, Chips), Runde, Wurzelwert-Differenz (Netzurteil ueber Claudes
   Zug gegen den eigenen) und der Partieausgang aus Claudes Sicht.
4. Aggregation: Abweichungsrate je Klasse und Runde; mittlere Wurzelwert-Differenz je Klasse (wo das
   Netz Claudes Zug fuer schlechter haelt, aber Claude gewinnt, sitzt die Luecke); Rangliste
   Haeufigkeit x Ausgang. Grundmenge: alle Claude-Entscheide der vorhandenen Partien (g01-g07,
   rund 80-90 je Partie), Einheit Entscheide; n ist klein (rund 600), die Sonde ist ein
   Richtungsgeber, kein Verdikt.
5. Ausgabe: JSON mit n/Grundmenge/Einheit, `laufzeit`-Block, Tabelle der zehn haeufigsten
   Abweichungsklassen mit Wurzelwert-Differenz und Ausgang; dazu die Gegenprobe mit einer
   NETZ-gegen-NETZ-Partie gleicher Laenge (Abweichungsrate des Netzes gegen sich selbst unter
   Wurzelrauschen als Rauschboden der Klassen).

**Vorab festgelegte Lesarten:** (a) haeufen sich die Abweichungen mit positivem Ausgang in EINER
Klasse (z. B. Kuppelplatzierung Richtung Spalten, oder Verzicht auf Ziehen), ist das der naechste
Knopf oder das naechste Trainingsziel (Prereg dafuer, kein Bau aus dieser Sonde heraus); (b) sind
sie ueber alle Klassen verteilt, fehlt dem Netz keine Zugklasse, sondern Tiefe (Suchgeschwindigkeit
ist per Nutzer-Entscheid 2026-09-12 kein Hebel mehr, GPU-Pfad und asynchrone Suche sind endgueltig
geschlossen; dann bleibt nur mehr Sims je Zug fuer Tessa gegen Menschen, ohne Motorumbau); (c) haelt das Netz
Claudes Zuege fast ueberall fuer schlechter und Claude gewinnt trotzdem, ist der Value-Kopf die
Luecke (Orakel-Differential wie `PREREG_human_game_oracle_gap.md`).

**Eingetaktet als v29-Begleitprogramm** (nach der Ziehsucht-Sonde, gleiche Logs, gleiches Replay;
Kosten: rund 600 Entscheide x eine Suche @400 = unter 30 min, exklusiv). Mehr Claude-Partien
erhoehen n; die Sitzung dafuer entscheidet der Nutzer.


## AGENTEN-AUFTRAG (Stand 2026-09-13, fuer eine autonome Abarbeitung durch einen Opus-Agenten)

### 1. Ziel und Verdikt-Regel

Zu beantworten ist, was eigenes Spiel gegen das Champion-Netz zeigt, das die Arenen nicht zeigen.
Die Messgroessen sind in **par.4** VOR dem Spielen festgelegt: (1) Ergebnis, Punkte, Marge --
mit der ausdruecklichen Vorab-Hypothese, dass die Frage NICHT ist, ob Claude gewinnt; (2) die
sechs Standard-Kennzahlen je Seite; (3) Uebereinstimmung mit dem Netz ist **ENTFALLEN**
(par.8 Punkt 4, Nutzer: "uebereinstimmungsmessung nein"); (4) **Pflicht: das qualitative
Protokoll** je Partie -- hoechstens drei Stellen mit Logzeile, an denen das Netz aus
Spielersicht falsch spielte, je Stelle die Regel oder das Muster, und ob eine registrierte Sonde
oder ein Knopf das Muster trifft. **Das ist der eigentliche Ertrag: Kandidaten fuer Sonden,
keine Verdikte.** Aus den Zahlen folgt ausdruecklich KEIN Elo-Knoten (Claudes Zuege sind nicht
reproduzierbar im Sinn der Leiter), keine Champion- oder Generatorentscheidung und KEIN
Trainingsmaterial (die Logs gehen NICHT ins Fenster). Fuer den zweiten Programmpunkt, das
Zugklassen-Differential, stehen die Lesarten in **par.10**: (a) haeufen sich Abweichungen mit
positivem Ausgang in EINER Klasse, ist das der naechste Knopf oder das naechste Trainingsziel
(mit eigener Prereg, kein Bau aus der Sonde heraus); (b) sind sie ueber alle Klassen verteilt,
fehlt dem Netz keine Zugklasse, sondern Tiefe; (c) haelt das Netz Claudes Zuege fast ueberall
fuer schlechter und Claude gewinnt trotzdem, ist der Value-Kopf die Luecke.

### 2. Voraussetzungen

- **Wer spielt: ein SUBAGENT** (par.8 Punkt 7, Nutzer 16:46: "Dein Modell ist zu teuer fuer
  diese spielerein"), Modell Opus, mittlerer Aufwand (CLAUDE.md). Der Koordinator startet ihn im
  CPU-freien Fenster, prueft sein Protokoll nach Regel 0 und registriert in par.7.
- **Werkzeug:** `tools/claude_play.py` liegt im Baum und bleibt dort (par.8 Punkt 6). Der letzte
  Rauchtest mit lebendem Gegner ist gruen (par.9 Punkt 11, g06 Zug 1-3), die vier Nachbesserungen
  aus g06/g07 sind gebaut und geprueft (par.9 Punkt 14: Platzierungs-Vorschau, Spezialfeld-Zeilen,
  Wertungsplatten-Stand, Mond-Reihenfolge nur wenn eindeutig; 14 neue Unit-Tests, Suite 58 gruen).
- **Auftrag an den Partien-Agenten, woertlich zu uebernehmen** (par.9 Punkt 7 und Punkt 10):
  nur `show`, `move`, `note`, `step` und `game.log` benutzen, **`.engine.log` NIE lesen** (dort
  steht die Rueckgabe-Reihenfolge mit Kachel-IDs, die laut Nutzer-Entscheid 2026-09-10 nur der
  Ausfuehrende sieht); `--sims 400`; Gegner OHNE `--opponent`, das Werkzeug liest dann
  `models/champion.txt`; je Partie Gegner und Spec-Pfad aus dem Manifest in die Ergebniszeile;
  **die Ausgabe von `move` NICHT filtern** (drei abgewiesene Zuege blieben in g03/g04 durch
  eigene grep-Filterung unbemerkt).
- **Seitenwahl** (par.8 Punkt 8): `--claude-side 1 --first-player 0`, also Claude als
  ZWEITSPIELER, damit die Reihe am Ende fuenf Partien je Seite hat.
- **Gegner je Block, keine Gesamt-Siegquote** (par.8 Punkt 8): g01 gegen v24-b06, g02-g05 gegen
  v27-b01, g06-g10 gegen den v28-Champion. Eine Siegquote ueber alle zehn ist KEINE Groesse.
- **Auslastung:** Spielen ist ein CPU-Auftrag (@400 je Zug) und darf NICHT neben einer laufenden
  CPU-Messung laufen, aber neben einem GPU-Training (par.2, `docs/working_rules.md`).
- **Fuer die beiden Sonden (P2/P3):** die Logs `evaluations/artifacts/claude_play/g*/game.log`
  im Server-Format, der Replayer `tools/analyze_game_log.py` (`Replayer`/`run`) und das
  Arena-Instrument des Champions.

### 3. Schritte

**P1 -- g08 bis g10 spielen (par.6 Punkt 4, par.8 Punkt 1: zehn Partien)**

1. Je Partie: `python -X utf8 tools/claude_play.py new --seed <SEED> --claude-side 1 --first-player 0 --sims 400`,
   dann abwechselnd `show` und `move <Zug>` (Notation par.3.3), `step` als Notausgang, wenn die
   KI am Zug haengen bleibt (par.9 Punkt 12b), `note` fuer das Protokoll. Partie-Verzeichnis
   `evaluations/artifacts/claude_play/<id>/` mit Manifest (Seed, Erstspieler, Modell, Sims, Spec,
   Kontrakt-Hash, Wheel).
   **Dauer:** rund 35-45 Claude-Zuege je Partie, 30-60 min je Partie (ANNAHME, par.5); die
   Rechenzeit je Netz-Zug liegt unter 1 s (ANNAHME aus 6,98 s je Self-Play-Partie @400 bei
   11 Threads, `docs/measured_runtimes.md`) -- die Kosten sind Sitzungszeit, nicht CPU.
   **Bei Abbruch:** der Zustand wird bei jedem Aufruf aus `.engine.log` rekonstruiert, die Partie
   ist also fortsetzbar; bleibt die KI am Zug (PermissionError auf `manifest.json` durch
   OneDrive, par.9 Punkt 12), `step` benutzen.
2. Je Partie das **qualitative Protokoll** (par.4.4) in `notes.md` und die Ergebniszeile in
   par.7 registrieren, mit Gegner und Spec-Pfad aus dem Manifest. Der Koordinator prueft die
   Behauptungen des Agenten am Log nach (Regel 0: Agenten-Befunde sind Behauptungen).

**P2 -- Ziehsucht-Sonde (par.9 / `PREREG_v29_window.md` par.7 Punkt 2)**

3. Ein CPU-Lauf ohne neue Erzeugung, auf dem vorhandenen Korpus; die Spezifikation ist Arm A der
   `PREREG_corpus_behaviour_audit.md` (dort par.2: A1 Ziehungen je Plattenplatzierung, BEDINGT
   auf den Punktestand; A2 Zwangsraeumungen). Der Selbsttest des Werkzeugs laeuft gegen die
   Claude-Logs und muss dort **exakt die Zahlen aus par.7 dieser Datei** liefern -- unter anderem
   die A1-Tabelle aus g06/g07: bei Stand > 0 im Mittel 1,17 (7 Ziehungen in 6 Zuegen, Maximum 2),
   bei Stand 0 im Mittel 6,6 (33 in 5 Zuegen, Maximum 13); n = 12 Zuege mit Ziehung, Grundmenge
   die beiden Partien, Einheit Ziehungen je Plattenzug.
   Reihenfolge im Begleitprogramm: vor oder nach der Leiter-Kante, je nachdem, was die Maschine
   frei hat.

**P3 -- Zugklassen-Differential (par.10, `PREREG_v29_window.md` par.7 Punkt 2b)**

4. Instrument bauen (netzfrei fuer Claude, das Netz nur als Vergleich, kein Training), fuenf
   Punkte genau wie in par.10 registriert:
   (1) jede Claude-Partie `evaluations/artifacts/claude_play/g*/game.log` per
   `analyze_game_log.run` Zug fuer Zug in Zustaende zerlegen (dasselbe Replay wie die
   Spaltensonde);
   (2) an jedem Claude-Entscheid (Drafting, Kuppelplatzierung, Startsetzung, Tiling-Schritte,
   Chips) rechnet der Champion mit seinem Arena-Instrument (@400, argmax, ohne Wurzelrauschen,
   Champion-Spec) seinen Zug und den Wurzelwert VOR und NACH Claudes Zug (Sicht Claude);
   (3) Abweichung = Claudes Zug ungleich Netzzug; je Abweichung Aktionsklasse, Runde,
   Wurzelwert-Differenz und Partieausgang aus Claudes Sicht;
   (4) Aggregation: Abweichungsrate je Klasse und Runde, mittlere Wurzelwert-Differenz je Klasse,
   Rangliste Haeufigkeit x Ausgang;
   (5) Ausgabe als JSON mit n / Grundmenge / Einheit und `laufzeit`-Block, Tabelle der zehn
   haeufigsten Abweichungsklassen, **dazu die Gegenprobe mit einer NETZ-gegen-NETZ-Partie
   gleicher Laenge** (Abweichungsrate des Netzes gegen sich selbst unter Wurzelrauschen als
   Rauschboden der Klassen).
   **Dauer:** rund 600 Entscheide mal eine Suche @400 = unter 30 min, exklusiv (ANNAHME, par.10).
   Grundmenge: alle Claude-Entscheide der vorhandenen Partien (g01-g07, rund 80-90 je Partie),
   Einheit Entscheide; **n ist klein (rund 600), die Sonde ist ein Richtungsgeber, kein Verdikt.**
   Direkt nach der Ziehsucht-Sonde, gleiches Replay.

**P4 -- Offene Werkzeug- und Engine-Punkte aus par.9**

5. **Nicht gebaut, mit Begruendung:** die Chipwahl (par.9 Punkt 13b / Punkt 14 Schlusssatz) --
   `apply_tiling_chips(spieler, reihe)` nimmt keine Plaettchenliste; ein optionales Argument
   `chips <reihe> [ids]` waere eine ENGINE-Aenderung und bleibt als solche offen. In g07 R5 hat
   das einen Punkt gekostet.
6. **Engine-Luecke par.9 Punkt 9:** `validation.rs::validate_small_moon` (:66-85) akzeptiert
   `SmallFactoryMoon` MIT `factory_id`, obwohl Aktion C laut `docs/engine_manual.md` Phase 1 C
   immer global ueber alle Mondbereiche ist und `generate_valid_moves` nur die globale Form
   erzeugt (:214). Der Zug ist nur ueber die direkte API erreichbar, Suche und Self-Play sind
   nicht betroffen; das Werkzeug weist `m1`-`m4` inzwischen ab. **Ob der Validator nachgezogen
   wird, ist Nutzer-Entscheid** (Engine-Aenderung, Anker-Invarianz faellig).
7. **Offener Anzeigefehler par.9 Punkt 8:** die Ursache der falschen Zaehler in
   `action.description` (gebaut in `engine/src/mcts.rs::label_search_move` :624 ueber
   `tiles_taken` :599) ist weiter ungeklaert; das Werkzeug umgeht ihn, indem `drive_ai` die
   sichtbaren Engine-Logzeilen druckt (`ai_lines`). Fuer die Suche folgenlos (reiner
   Anzeigetext), aber bei naechster Gelegenheit nachzusehen.
8. **Reihenfolge in `drive_ai`** (par.9 Punkt 12, bewusst offen): `append_log` vor
   `save_manifest` waere sicherer; das beruehrt die Log-Semantik und gehoert in einen eigenen Zug.

### 4. Auswertung und Registrierung

- **Zahlen mit n, Grundmenge, Einheit**: Partien "n = Partien je Gegner-Block, Grundmenge
  Claude-Partien gegen den jeweils amtierenden Champion, Einheit Siege / Punkte / Marge" --
  **je Block getrennt ausgewiesen, nie ueber alle zehn gepoolt** (par.8 Punkt 8);
  Zugklassen-Differential "n = rund 600 Entscheide, Grundmenge alle Claude-Entscheide der
  Partien g01-g07, Einheit Entscheide"; Ziehsucht "n = Zuege mit Ziehung, Grundmenge
  Plattenzuege, Einheit Ziehungen je Zug", bedingt auf den Punktestand.
- **Die sechs Standard-Kennzahlen** je Seite (par.4.2) aus `tools/analyze_game_log.py` und
  `tools/probes/tiling_geometry_probe.py`, verglichen mit den Mensch-Logs und den Netz-Arenen.
  **Endstand aus den Endwertungszeilen, NICHT aus `# SPIELENDE`**
  (`PREREG_difficulty_levels.md` par.2.4: die Zeile weicht in allen 33 Server-Logs ab).
- **Registrierung in par.7** (Ergebnisse je Partie plus Protokoll) und, fuer das Differential, in
  einem eigenen Ergebnis-Absatz zu par.10; **Zeile-1-Kopf im selben Zug** nachziehen, danach
  sofort `python tools/generate_prereg_index.py`.
- **STATUS.md Abschnitt 1 und Abschnitt 4** sowie `archive/history.md` fortschreiben.
- **Rueckwaerts-Pruefung**:
  `grep -rn "claude_play\|Ziehsucht\|g06\|g07\|Zugklassen" evaluations/ docs/ tools/`
  -- betroffen sind mindestens `PREREG_corpus_behaviour_audit.md` par.7 (Arm A1 stuetzt sich auf
  die Zahlen aus par.7 hier), `PREREG_v29_window.md` par.7 Punkt 2/2b,
  `PREREG_difficulty_levels.md` par.5 Stufe 4 (die Ziehsucht zaehlt dort nicht als Aussetzer),
  `PREREG_score_clamp_incentive.md` par.10/par.11.
- **Laufzeit-Zeilen** in `docs/measured_runtimes.md` (Sondenlauf Zugklassen-Differential mit n
  Entscheiden; Antwortzeit je Zug liefert erst `PREREG_difficulty_levels.md` Stufe 1 -- bis dahin
  bleibt par.5 hier eine ANNAHME und ist so zu markieren).
- **Elo-Register: NICHTS.** par.4 schliesst einen Elo-Knoten ausdruecklich aus.

### 5. Stopp-Punkte fuer den Nutzer

- **Ob es mehr als zehn Partien gibt** (par.10 Schlusssatz: "Mehr Claude-Partien erhoehen n; die
  Sitzung dafuer entscheidet der Nutzer"). **Nutzer fragen.**
- **Chipwahl in der Engine** (`apply_tiling_chips` mit Plaettchenliste) und **Validator-Fix fuer
  `validate_small_moon`**: beides Engine-Aenderungen mit faelliger Anker-Invarianz --
  Nutzer-Entscheid, kein Agenten-Bau.
- **Jeder Knopf und jedes Trainingsziel, das aus dem Zugklassen-Differential folgt**, braucht eine
  eigene Prereg (par.10 Lesart (a): "kein Bau aus dieser Sonde heraus").
- **Die Logs gehen nicht ins Trainingsfenster** (par.4); ein Arm "Claude-Logs als Traeger" waere
  eine eigene Prereg.
- **Kein Push, keine Loeschung** ohne pfadgenaue Freigabe; das Werkzeug bleibt in `tools/`
  (par.8 Punkt 6).

### 6. Abhaengigkeiten und Reihenfolge

**Vorher:** ein CPU-freies Fenster (Spielen neben einem GPU-Training ist erlaubt, neben einer
Arena nicht). Die Nachbesserungen und der Rauchtest sind erledigt (par.9 Punkte 11 und 14).
**Reihenfolge im Begleitprogramm** (`PREREG_v29_window.md` par.7): Punkt 2 Ziehsucht-Sonde, dann
Punkt 2b Zugklassen-Differential auf demselben Replay (unter 30 min), beide vor dem teuren
Tiling-Umbau (Punkt 2c) und in derselben Gruppe wie der Korpus-Verhaltens-Audit
(`PREREG_corpus_behaviour_audit.md`), weil alle denselben Befund bearbeiten.
**Danach:** was das Differential in EINER Klasse zeigt, wird zu einer eigenen Prereg und
gegebenenfalls zu einem v30-Rezept-Knopf (`PREREG_v29_window.md` par.8 Punkt 3).

## par.10 SICHTGLEICHHEIT DES SPIELFENSTERS, BEIDE RICHTUNGEN (Audit 2026-09-13, Nutzer-Auftrag "pruefe ob sichtgleichheit herrscht in beide richtungen")

**Abgrenzung zuerst.** `PREREG_stack_top_feature.md` fuehrt die Inventur NETZ gegen MENSCH AM TISCH
(par.15/par.16, P.1-P.15). Dieser Absatz fragt etwas anderes, das dort nicht steht: gilt
Sichtgleichheit zwischen **dem Spielfenster `tools/claude_play.py`** und **dem Netz**, gegen das
in g02-g07 gespielt wurde? Das ist die Frage, an der der Wert dieser sechs Partien haengt. Wo sich
die Befunde mit P.9/P.11/P.14 decken, steht der Verweis dabei.

**Verdikt: Sichtgleichheit gilt in KEINE der beiden Richtungen.** Vier Stellen sehe ich mehr als
das Netz, zwei sieht das Netz mehr als ich. Alle Pruefstellen in dieser Sitzung selbst nachgelesen.

### par.10a Ich sehe MEHR als das Netz

1. **Mondstapel der kleinen Fabriken.** Der Encoder gibt je Fabrik 15 Werte = die obersten DREI
   Steine, und das **nur vom ERSTEN Stapel** (`stacks.first()`, `break` bei `pos >= 3`;
   `features.rs:498-517` JSON-Pfad, `features.rs:971-988` Direktpfad, beide bytegleich). Es gibt
   weder ein Laengen- noch ein Mengenmerkmal fuer den Rest. `moon_stacks` ist ein `Vec<Vec<..>>`
   (`factory.rs:11`), eine Fabrik kann also mehrere Stapel tragen (`place_on_moon` pusht je
   Sonnenzug einen weiteren, `factory.rs:62-66`), und jeder von ihnen ist mit Aktion C nehmbar
   (`factory.rs:73-83`, Regel `docs/engine_manual.md` Phase 1 C). Mein `show` zeigt jeden Stapel
   vollstaendig und in Reihenfolge (`claude_play.py:636-638`, unten zuerst, `factory.rs:60-61`).
   **Gemessen, wie stark das gegriffen hat:** 291 protokollierte Stapelzustaende in g02-g07
   (Grundmenge: alle Zeilen `Mond-Stapel: (...)` in den sechs `game.log`), davon **0 mit vier oder
   mehr Steinen**. Die Tiefengrenze hat in diesen Partien also nie zugeschlagen. Ob eine Fabrik je
   ZWEI Stapel trug (Rest aus der Vorrunde plus neuer Zug), laesst sich aus `game.log` allein
   nicht auszaehlen -- **ungemessen**. Und: genau diese Reihenfolge habe ich taktisch benutzt
   (Blau in g06 zweimal bewusst unten vergraben, par.7), also an einer Stelle, an der das Netz
   hoechstens die obersten drei sieht.
2. **Beutel und Turm getrennt.** Der Encoder addiert beide zu EINEM Farbzaehler
   (`(bag_colors[i] + tower_colors[i]) / 13`, `features.rs:265-269`); eine getrennte
   Turmverteilung gibt es nicht. Mein `show` druckt beide Zeilen einzeln
   (`claude_play.py:633`). Der Unterschied ist nicht kosmetisch: Steine im Beutel kommen in der
   naechsten Fuellung, Turmsteine erst, wenn der Beutel leer ist. Ich habe die Beutelzahlen in
   beiden v28-Partien zur Farbknappheit herangezogen. **Deckt sich mit P.9** der Sicht-Prereg
   (dort als "Turm je Farbe, 5" fuer v29-b03 eingetaktet, also noch nicht gebaut).
3. **Anzahl gehaltener Bonuschips.** Der Encoder zaehlt nur Farben ueber alle Chips
   (`features.rs:381-396`); mein `show` listet jeden Chip einzeln (`claude_play.py:648`), ich sehe
   also die Anzahl. Die Vollendungsregel haengt genau daran (2 farbgleiche ODER 3 beliebige je
   fehlender Fliese). In g06 habe ich damit R3 gerechnet und vollendet (+6 mit dem Spezialfeld),
   in g07 R2 und R3 geplant. **Identisch mit P.11.**
4. **Vorderseiten der gezogenen Stapelplatten -- und das ist die einzige Stelle, an der mein
   Fenster gegen die REGEL verstoesst, nicht nur gegen die Sichtgleichheit.** Nutzer-Regelauskunft
   (dort par.16): "die vorderseiten sind nur bekannt nach dem aufhoeren. beim weiterziehen sind
   nur die rueckseiten bekannt." `serialize.rs` serialisiert `pending_stack_draw` trotzdem mit
   voller Vorderseite (eigener Kommentar dort: "hier vereinfacht schon mit voller Vorderseite
   serialisiert"), und mein `show` druckt sie (`claude_play.py:634`, Feld `gezogen:`). Das Netz
   bekommt sie NICHT: `pending_stack_draw` kommt in `features.rs` nur in einem Kommentar vor
   (Z.1435), in keiner Kodierung. In g07 Runde 2 ist das live passiert: nach dem ersten `peek`
   stand `gezogen: #17[#g/br]+3` auf dem Schirm, und ich habe DANACH entschieden weiterzuziehen.
   Benutzt habe ich nur den Typ (Spezial), was regelkonform ist -- gesehen habe ich mehr.
   Nebenbefund in eigener Sache: die am 2026-09-12 gebaute Platzierungs-Vorschau (par.9 P.14a)
   liest denselben Datensatz (`claude_play.py:597`), rechnet also auf einer Information weiter,
   die zu diesem Zeitpunkt nicht offen sein duerfte.
5. **Historie.** Der Encoder hat KEINE (0 Treffer fuer `move_number|history|prev_state` in
   `features.rs`, selbst nachgezaehlt); er sieht eine Momentaufnahme. Ich lese `game.log`, also
   den ganzen Partieverlauf. Das ist kein Fehler des Fensters -- ein Mensch am Tisch erinnert sich
   auch --, aber es ist eine echte Asymmetrie zum Gegner dieser Partien und die einzige, die sich
   nicht am Fenster beheben laesst, sondern nur am Netz.

### par.10b Das NETZ sieht mehr als ich

1. **Kuppelstapel-Maske und Wild-Anteil.** Der Encoder bekommt 18 Bits "dieses Design liegt noch
   verdeckt im Stapel" (`features.rs:274-277`) plus den Wild-Anteil des Rests als Skalar
   (`features.rs:282-286`). Mein `show` zeigt vom Stapel nur Hoehe und den Typ der obersten Platte
   ("Stapel 12 (oben: wild)", `claude_play.py:633`). Beides ist aus oeffentlicher Information
   ableitbar (18 bekannte Designs minus alle offen gewordenen Fronten), aber ableitbar ist nicht
   gesehen: das Netz bekommt es fertig, ich haette es in jeder Runde von Hand fuehren muessen und
   habe es in sechs Partien kein einziges Mal getan.
2. **Das Rueckgabe-Wissen (elf Werte, seit v28-b02).** `dome_pool_view` traegt unbekanntes
   Praefix, eigene Bloecke mit Reihenfolge und fremde Bloecke als Menge (`serialize.rs:96-133`,
   Encoder `features.rs:744-754`). **`dome_pool_view` kommt in `tools/claude_play.py` null Mal
   vor** -- das sichtkonforme Stapelwissen erreicht mein Fenster ueberhaupt nicht. Genau dieses
   Merkmal ist gegen den v27-Champion frisch eingebaut worden; in g06/g07 spielte also ein Netz
   mit einer Stapelkenntnis, die mein Fenster nicht anzeigt.

### par.10c Was NICHT als Asymmetrie zaehlt

Der Encoder bekommt eine Reihe fertiger AGGREGATE (`score_geo`, `line_geo`, `col_f_max`,
`estimated_score`, `cell_reachable_mask`), die mein Fenster nicht druckt. Das ist keine
Information, sondern Rechenhilfe: alles davon steht auf dem Brett. Dieselbe Begruendung traegt
umgekehrt meine eigenen Hilfen (Reihen-Ziele, Spezialfelder, Wertungsplatten-Stand, par.9 P.10/P.14)
-- und `estimated_score` zeigt mein Fenster ohnehin als "Rundenschaetzer". Ebenfalls nicht gezaehlt:
die Aktionsliste. Beide Seiten bekommen von der Engine nur legale Aktionen; dass der Encoder die
Top-down-Sperre nicht kennt (P.14), betrifft seine Bewertung, nicht seine Zugauswahl.

### par.10d Folge fuer par.7

Die sechs Partien bleiben als **Beobachtung** gueltig -- die tragenden Befunde (Plattenblindheit,
Null-Klammer als Werkzeug, Strafleisten-Bilanz) haengen an keiner der sechs Stellen. Als
**Staerkevergleich** sind sie es nicht: der Vorteil aus par.10a.2/3 wirkt in jeder Runde, und
par.10b.2 wirkt gegen mich. Eine Siegquote aus dieser Reihe ist damit auch aus diesem Grund keine
Groesse (par.8.8 nennt schon den Champion-Wechsel). Offen und Nutzer-Entscheid: ob das Fenster
angeglichen wird (Punkt 4 der Liste ist am billigsten -- gezogene Platten bis zum Aufhoeren nur mit
Typ zeigen; Punkte 2 und 3 waeren ein bewusstes Verschlechtern der eigenen Anzeige, Punkt 1 und 5
gehen nur am Netz).
