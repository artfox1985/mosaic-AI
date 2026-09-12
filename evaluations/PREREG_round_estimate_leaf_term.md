<!-- STATUS: OFFEN | Frage: Traegt ein additiver Rundenschaetzer-Term am Netz-Blattwert (Solver-Rundenscore plus Strafleisten-Busse, Differenz beider Seiten, tanh mit gemessener Skala, Runde 5 null) Spielstaerke und Spalten? | Beleg: Nichts gebaut. Skala GEMESSEN 2026-09-05 (par.4: P90 3 / 8 / 10 / 12 je Runde, gepoolt 9,25). EINGETAKTET 2026-09-11 als Schritt 7 des v28-Programms (PREREG_v28_window.md par.8): Bau nach par.3, Skala (a) je Runde als Koordinator-Vorschlag (Nutzer kann auf (b) wechseln), A/B gleiches Netz Live gegen Artefakt nach dem Muster der Kuppelstapel-Kante, zwei Seed-Basen. -->

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

## par.7 BAUSTAND 2026-09-12 (Code geschrieben, noch nicht kompiliert)

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
