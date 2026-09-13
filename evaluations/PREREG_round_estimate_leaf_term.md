<!-- STATUS: OFFEN | Frage: Traegt ein additiver Rundenschaetzer-Term am Netz-Blattwert (Solver-Rundenscore plus Strafleisten-Busse, Differenz beider Seiten, tanh mit gemessener Skala, Runde 5 null) Spielstaerke und Spalten? | Beleg: GEBAUT und im Wheel seit 2026-09-12 (par.7 Baustand; Default 0 bitidentisch: 601 Tests, Paritaets-Fixture unveraendert, Anker-Drift gruen), A/B UNGEMESSEN. Skala GEMESSEN 2026-09-05 (par.4: P90 3 / 8 / 10 / 12 je Runde, gepoolt 9,25). EINGETAKTET 2026-09-11 als Schritt 7 des v28-Programms (PREREG_v28_window.md par.8): Bau nach par.3, Skala (a) je Runde als Koordinator-Vorschlag (Nutzer kann auf (b) wechseln), A/B gleiches Netz Live gegen Artefakt nach dem Muster der Kuppelstapel-Kante, zwei Seed-Basen. -->

# Vorregistrierung: Rundenschaetzer als additiver Term am Netz-Blattwert (Such-Knopf K4)

**Angelegt 2026-09-05, 18:20, auf Nutzer-Auftrag ("leg die prereg an. die
strafleisten busse kannst als schaetzer mitaufnehmen"). Nichts gebaut.**

## par.1 Anlass und Leitsatz

Nutzer 2026-09-05, woertlich: *"drafting und tiling gehen hand in hand. das
drafting muss zum teil schon wissen wie das tiling agieren wird um die
fliesen zu legen und punkte zu generieren."* Und: *"wobei wir haben schon
einen point estimator implementiert. die heuristik verwendet ihn. vielleicht
kann/sollte das netz ihn auch verwenden."* Nutzer-Entscheid: *"additiver term
ist denk ich gut."*

## par.2 Was heute ist (Code geprueft 2026-09-05)

- Die Netz-Suche bewertet ein Blatt mit dem Netz auf dem Zustand VOR dem
  Tiling; am Rundenende wird kein Stein gelegt
  (`ROUND_TRANSITION_SAMPLING = false`, net_mcts.rs:95). Kontext:
  `PREREG_round_transition_search_sampling.md` par.7,
  `docs/architecture_reference.md` (Leitsatz).
- Der Punktschaetzer der Heuristik ist `mcts.rs::player_total`
  (mcts.rs:81-85): `solve_round_final_score(state, pi)` (exakter DFS-Loeser
  der Tiling-Phase, GREEDY-Chip-Politik) plus `scoring_progress`
  (Wertungsplatten-Fortschritt) plus `projected_unplaceable_penalty` (die
  Strafleisten-Busse, die bereits unplatzierbare Musterreihen am Rundenende
  verursachen). Normalisiert per `tanh(score / 50)` (mcts.rs:88-105,
  `VALUE_SCALE = 50` -- Skala des ABSOLUTEN Gesamtscores).
- Das Netz bekommt den Solver-Rundenscore bereits als EINGABE:
  `solve_round_final_score(state, pi) - score` je Spieler (features.rs:690),
  OHNE die Strafleisten-Busse. Ob das Netz dieses Merkmal ausreichend
  gewichtet, ist unbekannt.
- Im Netz-Blattwert taucht der Schaetzer nirgends direkt auf (net_mcts.rs
  nutzt `player_total` nur im ausgeschlossenen Dfs-Zweig, Zeile 2275).
  Additive Terme derselben Bauform existieren fuer K1 (`apply_score_utility`,
  aus den Punkte-KOEPFEN, nicht aus dem Solver) und K3 (Huelle).

## par.3 Bauform (registriert, VOR dem Bau)

Schaetzer je Spieler `pi`, in Punkten:

```
E(pi) = solve_round_final_score(state, pi) - score(pi)
        + projected_unplaceable_penalty(player pi)        (Vorzeichen wie in player_total)
```

Der Rundenscore-Anteil und die Busse werden getrennt mitgeloggt (par.5,
Kennzahl), aber als EIN Schaetzer verrechnet. `scoring_progress` geht NICHT
hinein (Wertungsplatten-Fortschritt ist Geometrie, nicht Rundenpunkte, und
ist ueber K3 / die Plattenkoepfe anders adressiert).

Term am Netz-Blattwert, aus Sicht von Spieler 0, Nullsumme, geklammert
(gleiche Bauform wie K1/K3, dieselbe Stelle im Blatt-Pfad hinter dem
K3-Term):

```
shift = C_est * tanh( (E(0) - E(1)) / B_est )      fuer Runde 1..4
shift = 0                                         in Runde 5
today_value[0] += shift;  today_value[1] -= shift;  beide auf [0, 1] geklammert
```

**Kein Runden-Profil** (Nutzer-Rueckfrage 2026-09-05, Antwort registriert):
der Schaetzer ist in jeder Runde gleich exakt, sein Betrag skaliert von
selbst mit den Rundenpunkten; ein Profil wuerde eine Eichung vorwegnehmen,
die es erst nach dem ersten Lauf gibt. Nur Runde 5 ist zwingend null, weil
dort der exakte Loeser samt Endwertung rechnet (dieselbe Auflage wie K3,
`geometric_envelope` par.4.1). Ein Profil wird erst dann eine Variante, wenn
der Basisarm frueh und spaet auseinanderlaeuft.

**Knoepfe:** `MOSAIC_ROUND_EST_C` (C_est, Default 0,0 = aus, byte-identisch)
und `MOSAIC_ROUND_EST_B` (B_est, Default = gemessener Wert aus par.4, VOR dem
Bau eingetragen). Beide als Spec-Pflichtfelder je Seite
(`round_est_c`, `round_est_b`), wie `envelope_search_c`; Registry-Eintrag,
`engine_config`, Manifest.

**Kosten:** der Solver laeuft fuer die Merkmale ohnehin je Netzaufruf fuer
beide Spieler (features.rs:690). Ob der Blatt-Pfad diesen Wert wiederverwenden
kann oder zwei weitere Solver-Aufrufe braucht, ist UNGEPRUEFT und wird beim
Bau geklaert; im zweiten Fall gilt das Kostentor aus par.5.

## par.4 Skala B_est: gemessen, nicht gesetzt

Die 50 der Heuristik passen nicht (Nutzer: "keiner macht 50 punkte in einer
runde" -- sie normalisiert den Gesamtscore einer Partie). Die Differenz zweier
Rundenschaetzer lebt auf der Skala weniger Punkte (Arena-Logs 2026-09-05:
rund 50 Tiling-Punkte je Partie und Seite, also etwa 10 je Runde).

**Messung (VOR dem Bau, billig, CPU-Kern, Minuten):** ueber die Draft-
Zustaende echter Partien (Replay der Arena-Logs
`paired_arena_env_v24b01_vs_b01_*_s14.json` per `analyze_game_log.Replayer`,
2 x 80 Partien) die Verteilung von `E(0) - E(1)` je Runde 1..4 aufnehmen:
Median, 90. Perzentil, Maximum des Betrags; Rundenscore-Anteil und Busse
getrennt. **Regel fuer B_est:** das 90. Perzentil des Betrags soll bei
`tanh = 0,75` landen, also `B_est = P90 / atanh(0,75) = P90 / 0,973`. Ein
Wert wird erst NACH dieser Messung hier eingetragen; Erwartung (Schaetzung,
keine Zahl fuer den Bau): zwischen 5 und 10.

**GEMESSEN 2026-09-05, 21:38 (`round_estimate_scale_probe.json`, 159 von 160 Partien
replayt, 1 Divergenz; 38.073 Draft-Zustaende R1-R4):**

| Runde | n | Median D | P90 von abs(D) | Max | Potenzial-Mittel je Seite | Busse ungleich 0 | B_est = P90/0,973 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 10.698 | 0 | 3 | 7 | 1,4 | 0,0 % | 3,1 |
| 2 | 9.441 | 0 | 8 | 22 | 3,2 | 1,8 % | 8,2 |
| 3 | 9.184 | 0 | 10 | 25 | 6,0 | 2,2 % | 10,3 |
| 4 | 8.750 | 0 | 12 | 33 | 7,5 | 9,7 % | 12,3 |
| 5 (nur zur Kenntnis, Term dort 0) | 5.007 | 1 | 14 | 31 | 12,7 | 3,6 % | 14,4 |
| **R1-R4 gepoolt** | 38.073 | | **9** | | | | **9,25** |

**Befund:** die Differenz waechst mit der Runde um den Faktor 4 (P90 3 in Runde 1, 12 in
Runde 4), die Strafleisten-Busse ist selten (unter 10 % der Seiten, Runde 4 am haeufigsten)
und klein. Mit EINER Skala B_est 9,25 ist der Term in Runde 1 praktisch aus (tanh(3/9,25) =
0,31 am P90) und in Runde 4 nahe der Saettigung. Das ist genau die Frage aus par.3 (kein
Profil) von der anderen Seite: nicht das Gewicht, die SKALA ist rundenabhaengig. Vorschlag,
Nutzer-Entscheid: (a) B_est je Runde aus dieser Tabelle (3 / 8 / 10 / 12), damit der Term in
jeder Runde dieselbe Aufloesung hat, oder (b) eine Skala 9,25 und in Kauf nehmen, dass der
Term frueh kaum wirkt. Die Zahlen stammen aus b01-gegen-v24-b01-Partien mit K3-P C 1,0
beidseitig; am v24-Siegernetz vor dem Bau erneut messen (Minuten).

## par.5 Messkette (Reihenfolge bindend)

1. **Skala** (par.4), Artefakt `round_estimate_scale_probe.json`.
2. **Bau** mit Paritaetsgate: `C_est = 0` ist byte-identisch zum Bestand
   (gleicher Nachweis wie bei K1/K3: gleiche Seeds, gleiche Zuege).
3. **Kostentor:** Wanduhr je Partie mit gegen ohne Knopf, Schwelle 25
   Prozent (uebernommen aus `round_transition_search_sampling` par.4.1 /
   `bootstrap_horizon`). Nur relevant, falls der Blatt-Pfad den Solver
   zusaetzlich aufrufen muss.
4. **argmax-Instrument** @400, 200 Partien, Seed 20260931, am
   v24-Siegernetz (Generatorwahl-Regel), C_est in zwei Dosen (Vorschlag 0,5
   und 1,0 -- Betrag wie K3, weil tanh-Skala gleich), jeweils auf dem
   Champion-Knopfsatz (K3-P C 1,0) obendrauf UND einmal ohne K3: trennt
   Term-Wirkung von Knopf-Wechselwirkung (Lehre v24 par.9b).
5. **Gepaarte Arena** 2 x 80 in beiden Richtungen, Blockgroesse 5, dasselbe
   Netz mit gegen ohne Knopf (Spec je Seite), Seed 20261014, `--log-games`.
   **Entscheidungsmass: Siegquote und Punktemarge auf Block-Ebene**, dazu die
   sechs Standard-Kennzahlen je Seite und als Differenz (Reihen-, Spalten-,
   Strafleistenauslastung, Punkte je Wertungsplatte, eigene Punkte, Marge;
   `arena_column_probe.py`, `arena_points_probe.py` mit Kuppel-Bonus und
   Strafe je Partie).
6. **Verdikt:** in den Spielbetrieb nur, wenn die Arena haelt UND die
   Spalten nicht fallen (Tor-2-Logik, Nicht-Fallen). Vorlage an den Nutzer,
   keine stille Aufnahme ins Rezept.

**Falsifikator:** keine signifikante Staerke auf Block-Ebene bei beiden
Dosen -> der Term traegt nicht; dann gilt: das Netz nutzt das Merkmal aus
features.rs:690 bereits ausreichend, und die Sicht auf das Tiling muss ueber
die Geometrie kommen (`round_transition_search_sampling` par.7 Variante B/C),
nicht ueber Punkte.

## par.6 Was dieser Term NICHT ist

- Keine Wiederbelebung des DFS-Blatts: das Netz bleibt der Blattwert, der
  Term ist ein Regler daneben ([[feedback_dfs_leaf_ruled_out]]).
- Keine Sicht auf die Tiling-GEOMETRIE: der Schaetzer misst Rundenpunkte.
  Spaltenvollendung als Endwertung, Huellen-Form, Kuppelplatten-Lage sieht
  er nur, soweit sie schon Rundenpunkte sind (Kuppel-Bonus ja, Spalten-
  Endwertung nein). Dafuer stehen K3-P/K3-P2 und
  `round_transition_search_sampling` par.7.
- Kein Ersatz fuer die Rundenweitsicht: der Solver ist rundenblind und
  greedy bei den Chips; als alleiniger Wert war das der Grund fuer Stufe 2,
  als Zusatz neben dem Netz ist es unproblematisch.

## par.7 Einordnung und Reihenfolge

Such-Knopf K4 in der Zaehlung von `PREREG_v24_window.md` par.8 (K1 Marge, K2
gestrichen, K3 Huelle, K3-P2 Platzhalter). Gemessen wird am v24-Siegernetz,
nach den v24-Abnahmen; vorher laeuft nur die Skalen-Messung (par.4), sobald
die CPU frei ist. Bei Erfolg Kandidat fuer den v25-Knopfsatz zusammen mit
K3-P2; Kreuzprodukte nur mit Anlass (ein Knopf, ein Netz, eine Messung).

## par.6a EINGETAKTET (2026-09-11): Schritt 7 des v28-Programms

*(Dieser Abschnitt trug bis zur Audit-Querlesung am 2026-09-11 ebenfalls die Nummer par.6 -- doppelt vergeben neben "par.6 Was dieser Term NICHT ist". Umbenannt in par.6a; externe Verweise auf par.6 dieser Datei gab es keine.)*

Nutzer 2026-09-11: *"takte den round_estimate_leaf_term noch an einer passenden stelle ein."*
Passende Stelle: nach `v28-b02`, am dann amtierenden Champion-Stand, als Such-Knopf ohne
Training (`PREREG_v28_window.md` par.8, Schritt 7). Messform wie bei Variante A des
Kuppelstapels: gleiches Netz, Live-Engine MIT Term gegen das eingefrorene Artefakt OHNE,
`frozen_referee_match`, zwei Seed-Basen a 150 Partien, plus Spaltensonde auf den Logs
(Standard-Kennzahlen). **Skala: Koordinator-Vorschlag (a) je Runde 3 / 8 / 10 / 12** (par.4
zeigt den Faktor 4 ueber die Runden; eine Skala 9,25 liesse den Term in Runde 1 praktisch
aus). Der Nutzer kann vor dem Bau auf (b) wechseln; der Knopf-Default traegt dann den
gewaehlten Wert, Vorab-Auflage aus par.3 erfuellt. Kostentor 25 % und Falsifikator aus par.5
unveraendert.

## par.7 BAUSTAND 2026-09-12 (gebaut, im Wheel seit 03:47)

Gebaut nach par.3 mit Skala (a) aus par.4/par.6a: `net_mcts.rs` K4-Block (`round_estimate_points`,
`round_estimate_shift_from`, `round_estimate_shift_state`, Blatt-Pfad hinter dem K3-Term),
Spec-Felder `round_est_c` (Default 0,0) und `round_est_b_profile` (vier Zahlen, Default 3 / 8 /
10 / 12 = P90 von |E(0) - E(1)| je Runde 1..4 aus `round_estimate_scale_probe.json`, n = 10.698 /
9.441 / 9.184 / 8.750 Draft-Zustaende, Einheit Punkte), Env `MOSAIC_ROUND_EST_C` /
`MOSAIC_ROUND_EST_B_PROFILE`, Registratur, `engine_config`, Spec-Abbildung in server.py und
claude_play.py, drei Tests. **Abweichung von par.3, hiermit registriert:** statt EINER Skala
`round_est_b` als Pflichtfeld ein RUNDENPROFIL `round_est_b_profile`, und beide Felder OPTIONAL
(Grund: die eingefrorenen Artefakt-Specs und `models/*.spec.json` tragen sie nicht und muessen
weiter laden; Muster `dead_cell_w`). Solver-Wiederverwendung (par.3 "UNGEPRUEFT"): der Blatt-Pfad
ruft `solve_round_final_score` je Spieler selbst, trifft aber die thread-lokale Memoisierung, die
der Merkmalsbau desselben Zustands unmittelbar davor fuellt (`tiling_solver.rs:404-427`,
`features.rs:859`); bei `MOSAIC_TILING_CACHE=0` waeren es zwei echte Solverlaeufe je Blatt. Der
Merkmalswert selbst ist als Quelle unbrauchbar (f32/100, ohne Strafleisten-Busse). Vorzeichen der
Busse wie `mcts.rs::player_total`. Kompilierung, Paritaets-Fixture, Anker-Drift und die Messkette
par.5 folgen im v28-Programm Schritt 7; A/B ueber den Referee am Champion, C_est aus par.5.

**Kompiliert und im Wheel (Nachtrag 03:50):** Bau-Tor 2026-09-12, 03:44-03:48 (`tools/night_v28_knob_build.sh`, Artefakte `anchor_drift_live_wheel_20260912_knobs.json` / `anchor_conservation_artifact_wheel_20260912_knobs.json`): `cargo test --release --lib` 601 gruen (84 s; darunter Kontrakt-Hash-Literal 39648b95bbba1acf und die Netz-Paritaets-Fixture des Champions UNVERAENDERT), Beispiele/Benches kompilieren, Wheel gebaut und installiert (Kontrakt 39648b95bbba1acf, INPUT_SIZE 755), Anker-Drift gegen hv4_anchor GRUEN und Konservierung GRUEN, Konventions-Check gruen. Zwei Nachbesserungen beim Bau: `#![recursion_limit = "256"]` in lib.rs (das `json!`-Literal von `engine_config_json` riss das Makro-Limit) und die Lesestelle der Startslot-Knoepfe als zwei Literal-Aufrufe (Registratur-Scanner). Alle neuen Knoepfe stehen damit auf Default im Wheel, das die Promotion v28-b02 einfriert.

## AGENTEN-AUFTRAG (Stand 2026-09-13, fuer eine autonome Abarbeitung durch einen Opus-Agenten)

### 1. Ziel und Verdikt-Regel

Zu beantworten ist, ob der additive Rundenschaetzer-Term am Netz-Blattwert (K4) Spielstaerke und
Spalten traegt. Die Verdikt-Regel steht in **par.5 Punkt 6**: in den Spielbetrieb nur, wenn die
Arena HAELT **und** die Spalten nicht fallen (Tor-2-Logik "Nicht-Fallen"); Vorlage an den
Nutzer, **keine stille Aufnahme ins Rezept**. Entscheidungsmass ist Siegquote und Punktemarge
auf **Block-Ebene** (par.5 Punkt 5), ausdruecklich nicht val-R2, nicht Brier, keine
Offline-Metrik. **Falsifikator (par.5):** keine signifikante Staerke auf Block-Ebene bei BEIDEN
Dosen -> der Term traegt nicht; dann gilt, dass das Netz das Merkmal aus `features.rs:690`
bereits ausreichend nutzt, und die Sicht auf das Tiling muss ueber die Geometrie kommen
(`PREREG_round_transition_search_sampling.md` par.7 Variante B/C), nicht ueber Punkte.
Zusaetzlich bindend: **Kostentor 25 Prozent** Aufschlag auf die Wanduhr je Partie (par.5 Punkt 3,
uebernommen aus `round_transition_search_sampling` par.4.1 und `bootstrap_horizon`).

### 2. Voraussetzungen

- **Der Knopf ist GEBAUT und im Wheel seit 2026-09-12, 03:47** (par.7 Baustand und Nachtrag):
  `net_mcts.rs` K4-Block (`round_estimate_points`, `round_estimate_shift_from`,
  `round_estimate_shift_state`, Blatt-Pfad hinter dem K3-Term), Spec-Felder `round_est_c`
  (Default 0,0 = aus, bitidentisch) und `round_est_b_profile` (vier Zahlen, Default **3 / 8 /
  10 / 12** = P90 von |E(0) - E(1)| je Runde 1..4, n = 10.698 / 9.441 / 9.184 / 8.750
  Draft-Zustaende, Einheit Punkte, aus `round_estimate_scale_probe.json`), Env
  `MOSAIC_ROUND_EST_C` und `MOSAIC_ROUND_EST_B_PROFILE`, Registratur, `engine_config`,
  Spec-Abbildung in `server.py` und `tools/claude_play.py`, drei Tests. Bau-Tor
  `tools/night_v28_knob_build.sh` gruen: 601 Lib-Tests, Kontrakt-Hash `39648b95bbba1acf` und
  Netz-Paritaets-Fixture des Champions unveraendert, Anker-Drift und Konservierung gruen.
  **Es ist also nichts mehr zu bauen; offen sind Kostentor, Instrument und A/B.**
- **Skala ist gemessen, nicht gesetzt** (par.4, 2026-09-05): Variante (a) je Runde ist gebaut
  (par.6a, Koordinator-Vorschlag). Der Nutzer kann auf (b) eine Skala 9,25 wechseln -- solange er
  das nicht tut, gilt (a).
- **Maschine frei laut Prozessliste**; exklusiv.
- **Spieler:** amtierender Champion-Stand mit seiner Spec (par.6a: "nach `v28-b02`, am dann
  amtierenden Champion-Stand, als Such-Knopf ohne Training").
- **Eintaktung:** Schritt 7 des v28-Programms, uebernommen ins v29-Begleitprogramm
  (`PREREG_v29_window.md` par.7 Punkt 3 und Punkt 4, letzter Spiegelstrich "nach Maschinenlage").

### 3. Schritte

**P1 -- Kostentor (par.5 Punkt 3)**

1. Wanduhr je Partie mit gegen ohne Knopf bei sonst identischer Konfiguration; Schwelle **25
   Prozent**. Messform: argmax-Instrument, 200 Partien @400, `--deterministic --no-root-noise`,
   threads 11, exklusiv, zweimal (C_est 0,0 gegen C_est 1,0):

   ```
   python -X utf8 -u self_play.py --mode network --model models/alphazero_<champion>.onnx \
     --spec models/round_est_c10.spec.json --games 200 --sims 400 --version rest-c10 \
     --threads 11 --chunk 10 --per-file 10 --seed 20260931 --no-root-noise --deterministic
   ```

   **Dauer (gemessen):** argmax-Instrument 200 Partien @400, threads 11, rund 24 min je Lauf
   (`docs/measured_runtimes.md`, Abschnitt Generation v24; als "C2 argmax-Instrument" auch mit
   rund 2.050 s je Lauf gefuehrt). Zwei Laeufe, also rund 50 min.
   **Hintergrund zur Erwartung (par.7 Baustand):** der Blatt-Pfad ruft
   `solve_round_final_score` je Spieler selbst, trifft aber die thread-lokale Memoisierung, die
   der Merkmalsbau desselben Zustands unmittelbar davor fuellt (`tiling_solver.rs:404-427`,
   `features.rs:859`); bei `MOSAIC_TILING_CACHE=0` waeren es zwei echte Solverlaeufe je Blatt.
   Das Kostentor misst den realen Fall.
   **Reisst das Tor: Arm nicht weiterverfolgen**, unabhaengig von jeder Staerkevermutung.

**P2 -- argmax-Instrument, zwei Dosen und die Knopf-Wechselwirkung (par.5 Punkt 4)**

2. @400, 200 Partien, Seed 20260931, am amtierenden Champion, C_est in zwei Dosen
   (**0,5 und 1,0**, Betrag wie K3, weil die tanh-Skala dieselbe Bauform hat), jeweils auf dem
   Champion-Knopfsatz (K3-P C 1,0) obendrauf **UND** einmal ohne K3 -- das trennt Term-Wirkung
   von Knopf-Wechselwirkung (Lehre v24 par.9b). Auswertung mit
   `python -X utf8 tools/corpus_sanity_check.py data --pattern "selfplay_rest-*_*.pkl" --out evaluations/artifacts/round_est_instrument_<dosis>.json`.
   **Die erzeugten Self-Play-Dateien sind Messmaterial** und gehoeren vor einem Fensterbau auf
   die Ausschlussliste (`MOSAIC_DATA_EXCLUDE`), nicht in den Korpus.

**P3 -- A/B (par.5 Punkt 5 und par.6a)**

3. **Messform nach par.6a** (Muster der Kuppelstapel-Kante): gleiches Netz, Live-Engine MIT Term
   gegen das eingefrorene Artefakt OHNE, `frozen_referee_match`, **zwei Seed-Basen a 150
   Partien**, plus Spaltensonde auf den Logs:

   ```
   python -X utf8 -u tools/frozen_referee_match.py \
     --artifact-dir models/frozen_champions/<champion> \
     --model-a models/alphazero_<champion>.onnx --spec-a models/round_est_c10.spec.json \
     --sims-a 400 --c-puct-a 1.5 --sims-worker 400 --c-puct-worker 1.5 \
     --n-games 150 --seed-base <SEEDBASIS> --workers 6 \
     --out evaluations/artifacts/round_est_ab_c10_<SEEDBASIS>.json
   ```

   **Dauer (gemessen):** A/B-Kante ueber den Referee, gleiches Netz, n=150, 6 Prozesse,
   2.515-2.621 s = rund 43 min je Lauf (`docs/measured_runtimes.md`).
   par.5 Punkt 5 nennt alternativ die gepaarte Arena (2 x 80 in beiden Richtungen, Blockgroesse
   5, Seed 20261014, `--log-games`); par.6a hat die Referee-Form nachregistriert -- **wer die
   Arena-Form nimmt, registriert das hier im selben Zug.**
   **Bei Abbruch:** Seed-Basis beibehalten und wiederholen; Teil-Laeufe nicht mit vollen poolen.
4. Sechs Standard-Kennzahlen je Seite und als Differenz (par.5 Punkt 5 nennt sie ausdruecklich):
   `python -X utf8 -u tools/probes/arena_column_probe.py --artifact <ART>`,
   `python -X utf8 -u tools/probes/arena_points_probe.py <ART>` (Kuppel-Bonus und Strafe je
   Partie) und `python -X utf8 -u tools/plate_points_from_arena.py <ART> --block 5`.
   Zusaetzlich getrennt mitloggen: **Rundenscore-Anteil und Strafleisten-Busse** (par.3 verlangt
   das ausdruecklich, obwohl beide als EIN Schaetzer verrechnet werden).

### 4. Auswertung und Registrierung

- **Zahlen mit n, Grundmenge, Einheit**: Kostentor "n = 200 Partien je Arm, Grundmenge
  argmax-Self-Play-Partien, Einheit Sekunden je Partie"; A/B "n = 150 Partien je Seed-Basis,
  Grundmenge Referee-Partien gleiches Netz mit gegen ohne Term, Einheit Siege"; Spalten "n =
  replaybare Partien, Grundmenge Arena-Partien, Einheit volle Spalten je Seite". Block-Ebene
  (Blockgroesse 5).
- **Registrierung in einem Ergebnis-Absatz dieser Datei** (par.5 Punkt 6 verlangt ein Verdikt),
  **Zeile-1-Kopf im selben Zug** nachziehen, danach sofort
  `python tools/generate_prereg_index.py`.
- **STATUS.md Abschnitt 1 und Abschnitt 5** sowie `archive/history.md` fortschreiben.
- **Rueckwaerts-Pruefung**:
  `grep -rn "round_est\|ROUND_EST\|round_estimate" evaluations/ docs/ tools/ engine/ server.py`
  -- betroffen sind mindestens `PREREG_v29_window.md` par.7 Punkt 3 und 4,
  `PREREG_round_transition_search_sampling.md` par.7/Nachtrag 2026-09-11 (dort steht die
  Reihenfolge-Berichtigung), `PREREG_v28_window.md` par.8 Schritt 7, `docs/knobs.md`.
  **Besonders zu pruefen:** wer sich auf die Skala 3/8/10/12 beruft -- die Zahlen stammen aus
  b01-gegen-v24-b01-Partien mit K3-P C 1,0 beidseitig (par.4 Schlusssatz: "am v24-Siegernetz vor
  dem Bau erneut messen, Minuten"); ist das nie geschehen, gehoert der Vorbehalt in die
  Ergebniszeile.
- **Laufzeit-Zeilen** in `docs/measured_runtimes.md` (Kostentor-Laeufe, A/B je Seed-Basis).
- **Elo-Register: NICHTS.** Gleiches Netz mit gegen ohne Knopf ist keine Kante am Champion; wird
  der Term Rezeptbestandteil, ist der Champion eine neue gemessene Identitaet
  (Feedback `measured_identity_gets_own_bxx`).

### 5. Stopp-Punkte fuer den Nutzer

- **Skala (a) je Runde 3/8/10/12 gegen (b) eine Skala 9,25** (par.4/par.6a): der Nutzer kann vor
  der Messung auf (b) wechseln. Gebaut ist (a).
- **Aufnahme ins Rezept** ist ausdruecklich Nutzer-Sache (par.5 Punkt 6: "Vorlage an den Nutzer,
  keine stille Aufnahme ins Rezept").
- **Ein Runden-Profil fuer C_est** (nicht fuer B_est) waere eine neue Variante und wird erst dann
  ueberhaupt zum Thema, wenn der Basisarm frueh und spaet auseinanderlaeuft (par.3). Kein Bau
  ohne Registrierung.
- **Reisst das Kostentor: anhalten** und melden, nicht "trotzdem messen".
- **Kein Push, keine Loeschung** ohne pfadgenaue Freigabe (auch nicht der Messdateien
  `selfplay_rest-*`; Ausschlussliste ja, `rm` nein).

### 6. Abhaengigkeiten und Reihenfolge

**Vorher:** der Bau ist erledigt (par.7 Nachtrag); die Messung braucht ein freies CPU-Fenster am
amtierenden Champion. Innerhalb des Begleitprogramms steht sie unter "nach Maschinenlage"
(`PREREG_v29_window.md` par.7 Punkt 4, letzter Spiegelstrich) und ist damit nachrangig gegenueber
Ziehsucht-Sonde, Mondstapel Stufe 1 und Rueckgabe-Reihenfolge.
**Danach:** faellt der Term negativ aus, ist das laut par.5 der Verweis auf die Geometrie-Seite
-- also auf `PREREG_round_transition_search_sampling.md` par.7 Variante B (dort par.9
eingetaktet) und Variante C (Encoder-Seite). Faellt er positiv aus, ist er ein Kandidat fuer das
v30-Rezept (`PREREG_v29_window.md` par.8 Punkt 3: v30 bekommt nur noch Rezept-Knoepfe).
