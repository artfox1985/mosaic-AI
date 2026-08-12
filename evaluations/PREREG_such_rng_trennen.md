# Vorregistrierung: Such-RNG von der Partie trennen

**Angelegt 2026-08-11, Nutzer-Auftrag** — *"[Instrumentenschulden] takte das als
nächstes ein."*

## 1. Der Befund (GEPRÜFT am Code)

Suche und Spielzustand ziehen aus **derselben** Zufallsquelle:

- `self_play.rs:1523/1527` gibt dasselbe `rng: &mut R` an
  `net_search_drafting_action` / `search_drafting_action` **und** an die
  Zustands-Mutation weiter.
- `net_mcts.rs:620` `determinize_hidden_information` verbraucht es
  (`state.dome_tile_pool.shuffle(rng)`) — einmal je Suche.
- `supply.rs:43` `Bag::refill_from_tower` verbraucht es ebenfalls, proportional
  zur Turmgröße — typisch beim Befüllen von Runde 4.

**Folge**: wie viel gesucht wird, verschiebt den Zufallsstrom und damit die
**Fliesenversorgung**. Unabhängig belegt (Agent-Befund, am Code nachgeprüft):
das Replay in `tools/analyze_game_log.py` bricht in Runde 4 ab, in 5 von 5
Arena-Partien **und in allen 10 Watchlist-Logs** — und zwar auch bei
`net_sims=1`, es ist also nicht die Menge, sondern jede Suche überhaupt.

## 2. Was der Fix ist

Suchaufrufe bekommen einen **eigenen, deterministisch abgeleiteten** RNG
(z. B. aus Partie-Seed + Zugindex), statt den Partie-RNG weiterzudrehen. Der
Spielzustand zieht danach aus einem Strom, den die Suche nicht anfasst.

Präzedenz im Projekt: `tools/analyze_game_log.py` macht es für sein Orakel schon
so (`deterministic_seed()`).

## 3. Drei Nutzen, und der zweite ist der grössere

1. **Replay funktioniert.** Damit läuft die Kreuzvalidierung durch, und die
   **endbrettbasierten** Grössen werden verfügbar — heute fehlen sie
   (`row_fill` je Rasterreihe), und genau die sind der dichte Detektor für die
   Injektions-Versuche (~6.300 Beobachtungen bei 200 Paaren gegen ~120
   Abschlussereignisse).
2. **Gepaarte Arenen werden echt gepaart.** Heute gilt "gleicher Spielindex,
   gleiche Startbedingungen" nur bis zur ersten Suche; danach spielen die Arme
   unterschiedliches Material. Nach dem Fix ist die Versorgung identisch und nur
   die Entscheidungen unterscheiden sich — **gemeinsame Zufallszahlen statt
   Varianzreduktions-Versuch**. Das verbessert JEDEN künftigen A/B, nicht nur
   einen. (Nutzer-Präzisierung: das ist ein Power-, kein Gültigkeitsproblem —
   die Ausgangsbasis war immer identisch.)
3. Determinismus allgemein: seed-exakte Reproduktion einer Partie wird möglich.

## 4. Die Kosten — und sie brauchen NUTZER-ENTSCHEIDUNGEN

### (a) Die Paritätsprobe MUSS brechen

`tools/paritaets_probe.py` prüft, dass Defaults byte-identisch zum Bestand sind
(Hash `8c6684ffba06cf3e16e898b83325f3154c04efac555c8e862c079b71155bd423`). Eine
Änderung der Such-Zufallsquelle ändert die Determinisierungen und damit die
Suchergebnisse — **byte-identisch ist unmöglich**.

Das ist kein Fehlschlag, sondern die erwartete Wirkung. Es heisst aber, dass der
Golden-Wächter diese Änderung **nicht** validieren kann und ein dokumentiertes
Neu-Setzen der Basislinie braucht. **ENTSCHEIDUNG NÖTIG.**

### (b) Die Elo-Leiter überspannt einen Sprung

Sucht das Netz aus einem anderen Strom, ändert sich sein Spiel statistisch
äquivalent, aber nicht identisch — und der **Heuristik-Anker ändert sich
mit** (er sucht ebenfalls). Messungen vor und nach dem Schnitt sind damit nur
eingeschränkt vergleichbar, wie schon einmal bei der Engine-Ära-Aktivierung
(`elo_history.csv` Zeile 24 vermerkt genau so einen Fall).

Optionen: neu verankern (Kosten: Anker-Kanten neu fahren, je n=150 ohne
Frühstopp) oder den Sprung nur vermerken. **ENTSCHEIDUNG NÖTIG.**

### (c) Alt-Korpora bleiben gültig, Alt-Partien nicht reproduzierbar

Die vorhandenen 29.450 Self-Play-Partien sind Stichproben und bleiben als
Trainingsmaterial brauchbar. Was **nicht** geht: eine alte Partie aus ihrem Seed
exakt nachspielen. Für die 64 Nutzer-Logs heisst das: sie werden durch diesen
Fix **nicht** replaybar — sie wurden vor dem Schnitt erzeugt.

Das ist der wichtigste Vorbehalt gegen die Erwartung, der Fix mache die
Watchlist-Partien nachrechenbar. **Er macht nur KÜNFTIGE Partien replaybar.**

## 5. Verifikation — der eine entscheidende Test

**Suchvolumen darf den Versorgungsstrom nicht mehr berühren.** Dieselbe Partie
mit `net_sims=1` und `net_sims=400` spielen und prüfen, dass die
**Fliesenfolge** (Fabrikinhalte je Runde) identisch ist. Heute ist sie das
nachweislich nicht — das ist die Ursache des Runde-4-Abbruchs.

Dazu:
- `cargo test --lib` grün (Stand 346 / 14 ignoriert).
- Replay-Kreuzvalidierung auf **neu erzeugten** Arena-Logs läuft durch
  (Exit 0), inklusive der Punkte-Invariante gegen `scores`, die heute schon
  10/10 hält.
- Neue Paritäts-Basislinie dokumentiert, mit Begründung im Commit.

## 6. Zuschnitt und Reihenfolge

Betroffen sind laut Agent-Befund `self_play.rs`, `py.rs`, `mcts.rs`,
`net_mcts.rs`. Der Umbau ist **nicht** nebenbei zu machen und sollte **nicht**
parallel zu einem laufenden Messvorhaben stattfinden, weil er die
Vergleichsgrundlage verschiebt.

Empfohlene Reihenfolge: **erst** die vorregistrierten Injektions-Versuche mit
dem heutigen Stand fahren (sie brauchen nur die ereignisbasierten Grössen, die
ohne Replay verfügbar sind), **dann** den Schnitt machen — sonst überspannen die
Versuche selbst den Sprung.

## 7. Der zweite, kleine Punkt: Parser-Lücke `move_row_to_floor`

`py.rs:316` erzeugt `"{name}: {n} unplatzierbare Fliesen → Strafleiste"` ohne
PATTERNS-Eintrag in `analyze_game_log.py`. Erreichbar **nur** über den manuellen
Server-Endpunkt `/api/tiling/move_to_floor` (`server.py:902-912`); kein
KI-/Arena-Pfad ruft es, und in allen 64 Logs 0 Treffer.

**Niedrige Priorität, und bewusst nicht "auf Verdacht" gefixt**: es gibt keine
echte Zeile, an der die Replay-Behandlung zu verifizieren wäre. Sinnvoll erst,
wenn eine Partie über diesen Endpunkt gespielt und aufgezeichnet wurde.

---

## 8. NUTZER-ENTSCHEIDUNGEN 2026-08-11 -- beide Blocker sind weg

### (b) Elo-Leiter: **Sprung wird nur vermerkt**

Nutzer-Wortlaut: *"sprung wird nur vermerkt."* Also KEIN Neuverankern, keine
neuen Anker-Kanten. Stattdessen eine Zeile in `elo_history.csv`, die den Schnitt
markiert -- dieselbe Behandlung wie bei der Engine-Aera-Aktivierung (dort Zeile
24). Messungen ueber den Schnitt hinweg bleiben damit ausdruecklich nur
eingeschraenkt vergleichbar, und das steht dann dort, wo es gelesen wird.

Ersparnis gegenueber dem Neuverankern: die Anker-Kanten haetten je n=150 ohne
Fruehstopp gebraucht.

### (a) Paritaets-Basislinie: folgt zwingend, nicht separat entschieden

Das war keine echte Wahl. Der Hash MUSS brechen (Abschnitt 4a), also gibt es nur
"Basislinie neu setzen und begruenden" oder "den Umbau gar nicht machen". Da die
Elo-Frage entschieden ist, ist der Umbau gewollt -- damit wird die Basislinie neu
gesetzt, mit Begruendung im Commit und dem alten Hash
`8c6684ffba06cf3e16e898b83325f3154c04efac555c8e862c079b71155bd423` daneben
festgehalten, damit der Uebergang nachvollziehbar bleibt. **Widerspruch des
Nutzers hierzu geht vor.**

### ZEITPUNKT: nach der Koeffizientensuche, nicht jetzt

Abschnitt 6 dieser Datei sagt es selbst: der Umbau *"sollte NICHT parallel zu
einem laufenden Messvorhaben stattfinden, weil er die Vergleichsgrundlage
verschiebt."* Die Koeffizientensuche fuer die vertikalen Wertungsplatten
(`PREREG_injektion_wertungsplatten.md` N7) ist genau so ein Vorhaben -- Zellen vor
und nach dem Schnitt waeren nicht mehr gegeneinander lesbar, und der Nullpunkt
(53,30 Endstand, 0,70 vertikale Punkte) muesste neu gemessen werden.

Reihenfolge also: Koeffizientensuche abschliessen, dann schneiden. Danach werden
die endbrettbasierten Groessen verfuegbar (`row_fill` je Rasterreihe, ~6.300
Beobachtungen bei 200 Paaren statt ~120 Abschlussereignissen) -- und genau die
sind der dichte Detektor fuer alles, was in dieser Injektions-Reihe noch kommt.


---

## 9. WARNUNG 2026-08-12: der GPU-Batcher arbeitet gegen den Zweck dieser Datei

`PREREG_gpu_inferenzpfad.md` §17: mit eingeschaltetem Verschraenkungs-Batcher haengt
die Rangfolge der Wurzelkandidaten an der **Batch-Zusammensetzung**, und die
entsteht aus dem Zeitverhalten der Faeden -- also von Lauf zu Lauf verschieden.
Belegt an `record_index=320`, der unter 128er-Bloecken eine Rangvertauschung zeigt
und unter einem 455er-Aufruf nicht.

**Damit ist Nutzen 3 dieser Vorregistrierung (seed-exakte Reproduktion) mit
eingeschaltetem Batcher NICHT erreichbar**, auch nach dem hier geplanten
RNG-Schnitt. Der Schnitt macht den Zufallsstrom deterministisch; der Batcher macht
die Inferenz-Reihenfolge nichtdeterministisch. Zwei verschiedene Quellen.

Wer diese Datei umsetzt, muss das wissen: die Reproduzierbarkeit gilt dann nur bei
AUSGESCHALTETEM Batcher. Die drei Optionen dazu stehen in §17 der anderen Datei;
Option 1 (Batcher fuer Self-Play, aus fuer Arena/Gating) haelt beide Nutzen
getrennt verfuegbar, ist aber eine Einschaetzung und nicht gemessen.

---

## 10. ENTSCHÄRFT durch Nutzer-Entscheid 2026-08-12

*"batcher für self play an, arena und gating aus"* (`PREREG_gpu_inferenzpfad.md` §18).

Der Widerspruch aus §9 ist damit aufgelöst, nicht weggeredet: die seed-exakte
Reproduktion, die diese Vorregistrierung herstellen soll, gilt für **Arena und
Gating** -- und dort ist der Batcher aus. Im Self-Play ist er an, dort sind die
Partien Stichproben und die Reproduktion einzelner Partien wird nicht gebraucht.

Der RNG-Schnitt bleibt damit sinnvoll und uneingeschränkt umsetzbar. Wer ihn
umsetzt, muss nur wissen, dass die Reproduzierbarkeit im Self-Play nicht gilt,
solange der Batcher dort läuft.
