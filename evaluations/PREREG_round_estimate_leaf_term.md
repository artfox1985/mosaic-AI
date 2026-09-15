<!-- STATUS: ENTSCHIEDEN | Frage: Traegt ein additiver Rundenschaetzer-Term am Netz-Blattwert Spielstaerke und Spalten? | Beleg: NEIN, er SCHADET in beiden vorregistrierten Dosen (par.7c/7d, 2026-09-15): 20:60 bei C_est 1,0 und 45:85 bei 0,5, McNemar p 0,0002 und 0,0005, -14,3 bzw. -8,3 Punkte und rund -0,9 volle Spalten. MECHANISMUS sichtbar: die Strafleiste sinkt (-1,57) und volle Zeilen steigen, waehrend Spalten und Spezialfelder einbrechen -- der Term macht die Suche rundenscore-gierig. Der Spaltenschaden saettigt frueh (bei halber Dosis 88 Prozent davon). Kostentor bestanden (par.7b, +4,3 Prozent). Offen als VORSCHLAG: Rundenprofil wie K3 statt kleinerer Dosis -- Nutzer-Entscheid. -->

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


## par.7a KONTAMINATION OFFENGELEGT (2026-09-15): Nebenlast waehrend `k4_kosten_mit`

**Was passiert ist.** Der Lauf `k4_kosten_mit_s20261092` lief von 00:49:19 bis 00:57:51. In
diesem Fenster hat die Sitzung DREI `git commit` gefahren (00:52:08, 00:53:06, 00:54:44),
deren pre-commit-Hook jeweils 98 Tests plus den Konventions-Check ausfuehrt. Das ist
CPU-Nebenlast waehrend eines Laufs, dessen EINZIGE Messgroesse die Wanduhr ist -- der
denkbar schlechteste Zeitpunkt. CLAUDE.md nennt `git commit` einen Grenzfall und sagt "im
Zweifel bis nach dem Lauf aufheben"; bei einem Kostentor ist es keiner.

**Groessenordnung, beziffert statt behauptet:**

| Groesse | Wert |
| --- | --- |
| Fenster | 512,5 s Wanduhr x 10 Threads = 5.125 Kern-Sekunden |
| tatsaechliche Auslastung | 2.240,2 s CPU = 43,7 Prozent (die Maschine war NICHT gesaettigt) |
| drei Commits, 3 bis 10 s Kern-Zeit je Commit | 9 bis 30 Kern-s = **0,18 bis 0,59 Prozent** |
| Torschwelle par.5 Punkt 3 | 25 Prozent |

Die Stoerung liegt damit rund zwei Groessenordnungen unter der Schwelle, und bei 43,7 Prozent
Auslastung konkurrierten die Testprozesse nicht einmal um belegte Kerne.

**Trotzdem ist der Verdacht nicht ausraeumbar, sondern nur wiederholbar.** Das ist die
ausdrueckliche Lehre in CLAUDE.md: ein Testlauf aus dem Cache erzeugt CPU-Last OHNE Spur im
Dateisystem, die Rechnung oben stuetzt sich also auf eine ANNAHME ueber die Kern-Zeit, nicht
auf eine Messung. Byte-gleiche Wiederholung belegt dagegen beides auf einmal.

**Vorschlag (Nutzer-Entscheid):** Schritt 2 wiederholen, sobald die Kette durch ist -- Kosten
8,5 min, gleicher Seed, keine Sitzungstaetigkeit waehrenddessen. Die Gegenseite
`k4_kosten_ohne_s20261093` ist nach jetzigem Stand SAUBER (ab 00:58 wurde nicht mehr
committet); ein Vergleich zwischen einem gestoerten und einem sauberen Lauf ist asymmetrisch
verfaelscht, und zwar in die Richtung, die das Tor reissen laesst.

**Konsequenz ab sofort, ohne Nachfrage:** solange eine Messkette laeuft, wird in dieser Sitzung
nicht committet. Dateien schreiben, Preregs pflegen, Artefakte lesen -- alles erlaubt; der
Commit wartet, bis die Maschine frei ist. Das gilt besonders fuer die Kostentore, weil dort
die Wanduhr nicht Nebenbedingung, sondern Messziel ist.


## par.7b KOSTENTOR GEMESSEN (2026-09-15): das Tor HAELT mit grossem Abstand

par.5 Punkt 3 verlangt Wanduhr je Partie MIT gegen OHNE Rundenschaetzer, Schwelle 25 Prozent.
Zwei Laeufe mit je identischen Specs auf beiden Seiten, 20 Paare / 40 Partien, 10 Threads.

| Lauf | Spec | s je Partie | Wanduhr | CPU s |
| --- | --- | --- | --- | --- |
| `k4_kosten_mit_s20261092` | `round_est_c10` beidseitig | **12,812** | 512,5 | 2.240,2 |
| `k4_kosten_ohne_s20261093` | `round_est_off` beidseitig | **12,286** | 491,4 | 2.166,5 |

**Ergebnis: +4,3 Prozent Wanduhr, +3,4 Prozent CPU** gegen eine Schwelle von 25 Prozent. Das
Tor haelt mit rund einem Sechstel des erlaubten Aufschlags. **Nr. 30 ist gruen, die Schritte 31
und 32 duerfen laufen.**

**Die Kontamination aus par.7a wirkt hier KONSERVATIV** und entwertet das Verdikt nicht: die
Nebenlast lag auf der `mit`-Seite, hat sie also kuenstlich verteuert. +4,3 Prozent ist damit
eine OBERGRENZE, der wahre Wert liegt darunter. Die Wiederholung bleibt fuer die Sauberkeit der
ZAHL sinnvoll, fuer das VERDIKT ist sie nicht noetig -- ein Tor, das in der pessimistischen
Richtung um Faktor 6 haelt, kippt nicht durch 0,2 bis 0,6 Prozent Stoerung.

**Kontrollprobe des Aufbaus: bestanden.** Beide Seiten je Lauf sind identisch (20:20, Punkte
46,33/46,33 und 51,27/51,27, Boden 10,75/10,75 und 8,80/8,80, volle Spalten gleich, McNemar
p = 1,000) -- wie es sein muss, wenn dieselbe Spec gegen sich selbst bei gleichem Seed spielt.

### Nebenbefund, ausdruecklich NICHT gedeutet

Zwischen den beiden LAEUFEN unterscheiden sich die Kennzahlen deutlich: Punkte 46,33 gegen
51,27, Boden 10,75 gegen 8,80, volle Spalten 0,5526 (n = 38) gegen 0,9250 (n = 40). Das sieht
nach einem Effekt von K4 aus, **ist aber nicht als solcher lesbar**: die Laeufe haben
VERSCHIEDENE Seeds (20261092 gegen 20261093) bei n = 40 Partien, und in dieser Kampagne bewegt
der Seed die Metrik 4- bis 6-mal staerker als jeder Knopf
(`project_training_seed_variance`, 5,75 Prozentpunkte Streuung bei n = 400 fuer identische
Konfiguration). Die gepaarten Arena-Laeufe der Schritte 3 und 4 (`k4_c10_vs_off`,
`k4_c05_vs_off`, je 80 Paare) messen genau das und entscheiden es. **Bis dahin ist dies eine
Beobachtung, kein Befund** -- aber eine, die man beim Lesen jener Artefakte im Kopf haben
sollte, weil sie eine Richtung vorhersagt.

### Wiedervorlage aus `PREREG_moon_stack_order.md` par.9h beantwortet

Dort stand offen, ob die Mondstapel-Nachsuche ueberhaupt RECHNET und nicht nur ausloest.
`k4_kosten_ohne` ist der fehlende Basiswert (reine Champion-Spec, keine Nachsuche, kein K4):

| Lauf | s je Partie | gegen Basis 12,286 |
| --- | --- | --- |
| `moon_order_post_vs_off_s20261091` (a-Seite mit Nachsuche) | 14,833 | **+20,7 Prozent** |

Da in jeder Partie nur EINE der beiden Seiten die Nachsuche traegt, entspricht das
hochgerechnet rund +41 Prozent fuer beidseitigen Betrieb (**Herleitung, nicht gemessen** --
die Gelegenheiten sind nicht exakt gleich auf beide Seiten verteilt). par.9b erwartete +57
Prozent an Zusatz-SIMS; Sims und Wanduhr sind nicht dasselbe (thread-lokale Memoisierung des
Loesers, Batch-Effekte), die Groessenordnung passt aber. **Die Nachsuche hat gerechnet** --
damit ist par.9d Punkt 5 doppelt belegt: die Torbedingung oeffnet, und der Aufwand faellt an.


## par.7c ARENA DOSIS 1,0 GEMESSEN (2026-09-15): der Term SCHADET massiv -- und die Ursache ist die Dosis, nicht die Idee

**Lauf** `k4_c10_vs_off_s20261094`, beide Seiten `alphazero_v28-b02_brierbest` @400,
Unterschied genau ein Spec-Feld (`round_est_c` 1,0 gegen 0,0), Blockgroesse 5, --log-games.
Laufzeit 1.023,4 s, 12,793 s je Partie, 10 Threads. **a = K4 an, b = aus.**

**FRUEH GESTOPPT, und zwar zugunsten der Basislinie:** angelegt war der Lauf auf 80 Paare
(Skript-Deckel), gefahren wurden **40**; der SPRT hat bei LLR -7,511 die untere Schranke
-6,907 gerissen und H0 gemeldet. Die bekannte Verzerrung von Frueh-Stopps -- Siegquoten des
KANDIDATEN nach oben -- greift hier also nicht, sie wirkt wenn ueberhaupt gegen den Befund.
Die Effektstaerke (-14,3 Punkte) liegt ohnehin weit jenseits dessen, was ein Stopp-Zeitpunkt
bewegen koennte. Fuer die Kennzahlen bedeutet es n = 78 statt 158 Bretter je Seite, die
angegebenen SE beziehen sich darauf.

| Groesse | a (C_est 1,0) | b (aus) | Differenz |
| --- | --- | --- | --- |
| Siege (40 Paare) | **20** | **60** | McNemar **p = 0,00018** |
| gepaarte Differenz | \-- | \-- | **-1,00** [-1,42, -0,58] |
| Sweeps a / b / Splits | 4 | 24 | 12 |
| eigene Punkte | **45,76** | **60,05** | **-14,29** |
| **volle Spalten** (n = 78 je Seite) | **0,3205** | **1,2692** | **-0,9487** |
| Spalten >= 4 | 2,013 | 2,487 | -0,474 |
| Spezialfelder belegt | 0,949 | 1,385 | -0,436 |
| Huelle H | 0,484 | 0,585 | -0,101 |
| Zeilen voll | 0,244 | 0,103 | +0,141 |
| Strafleiste | 9,410 | 9,423 | -0,013 |

Das ist kein Nullbefund, sondern ein **Einbruch**: minus 14,3 Punkte je Partie und fast eine
ganze volle Spalte. Der Term lenkt das Spiel messbar um -- Zeilen steigen, Spalten und
Spezialfelder fallen --, und zwar in die falsche Richtung.

**Damit ist der Nebenbefund aus par.7b bestaetigt und war KEIN Seed-Effekt.** Dort standen die
Kostentor-Laeufe bei 46,33 gegen 51,27 Punkten und 0,55 gegen 0,93 vollen Spalten, was wegen
verschiedener Seeds bei n = 40 ausdruecklich nicht gedeutet wurde. Die gepaarte Messung zeigt
dieselbe Richtung, staerker. Die Vorsicht war methodisch richtig, die Beobachtung auch.

### Die Ursache, am Code belegt: C_est 1,0 ueberschreibt den Value-Kopf

`today_value` ist eine SIEGWAHRSCHEINLICHKEIT in [0,1] -- belegt durch die Klammerung
`today_value[0] = (today_value[0] + shift).clamp(0.0, 1.0)` (net_mcts.rs:3205-3206). Der K4-Term
ist `C_est * tanh((E0 - E1) / B)`, bei C_est = 1,0 also im Bereich [-1, +1]: er kann den
gesamten Wertebereich ueberschreiben.

**Und B ist per Konstruktion das P90** der Differenz je Runde (par.4, Variante (a): 3 / 8 / 10 /
12 aus 38.073 Draft-Zustaenden). In rund **10 Prozent** der Blaetter ist |E0 - E1| also groesser
als B, das tanh-Argument groesser als 1 und |tanh| groesser als 0,76 -- **in jeder Runde gleich
oft**, weil B je Runde neu geeicht ist. Bei C_est = 1,0 wird der Netzwert dort faktisch
ersetzt.

**Warum die Dosis-Begruendung das nicht sah.** par.5 Punkt 4 begruendet die Dosen mit *"Betrag
wie K3, weil tanh-Skala gleich"*. Die Analogie ist strukturell RICHTIG -- K3 (`envelope_search_c`)
wirkt an derselben Stelle, auf dasselbe `today_value`, mit derselben Bauform
(`+shift`/`-shift`, geklammert, net_mcts.rs:3183-3184), und faehrt im Champion-Rezept mit
c = 1,0 ohne zu schaden. Uebersehen wurde die ZWEITE Daempfung, die nur K3 hat: sein Shift
traegt das abfallende Rundenprofil `[1,0 0,92 0,67 0,33 0,0]` in sich
(`search_shift_state(&state, env_c, &search_config.envelope_profile, ..)`), faellt also ueber die
Partie auf null. **K4 hat kein Profil.** Die Skala B im NENNER des tanh reguliert die
Saettigungshaeufigkeit, nicht den Betrag -- und weil sie je Runde neu geeicht ist, haelt sie die
Wirkung ueber die Runden sogar KONSTANT, statt sie zu daempfen.

**Das ist ein Befund ueber die DOSIS und die FEHLENDE DAEMPFUNG, kein Verdikt ueber die Idee.**
Der Falsifikator aus par.5 ("keine signifikante Staerke bei beiden Dosen -> der Term traegt
nicht") passt auf diesen Ausgang nicht: hier gibt es sehr wohl eine signifikante Wirkung, sie
zeigt nur nach unten. Ein Term, der bei voller Dosis das Spiel umlenkt, ist nicht wirkungslos --
er ist falsch dosiert.

### Vorschlag (Nutzer-Entscheid, NICHT selbst gefahren)

1. **Dosis 0,5 abwarten** (laeuft als `k4_c05_vs_off_s20261095`). Sie sagt, ob der Schaden
   linear mit C_est skaliert. Erwartung: ebenfalls negativ, etwa halb so stark.
2. Wenn ja, ist die sinnvolle Reihe **0,05 / 0,1 / 0,2** statt 0,5 / 1,0 -- Groessenordnung so
   gewaehlt, dass der Term in den 10 Prozent Saettigungsblaettern hoechstens rund ein Fuenftel
   des Wertebereichs bewegt statt ihn zu ersetzen.
3. **Oder** K4 bekommt dieselbe Daempfung wie K3, also ein Rundenprofil. Das ist ein Bau, kein
   Knopf, und waere der sachlich naeherliegende Weg: der Rundenschaetzer ist frueh in der Runde
   am unsichersten, genau dort wirkt er heute am staerksten.

**Nicht aufgeraeumt, aber benannt:** der Falsifikator in par.5 und par.10 unterstellt, ein
Nullbefund sei der einzige negative Ausgang. Ein SCHADEN ist ein dritter, und die Prereg hat
ihn nicht vorgesehen.


## par.7d ARENA DOSIS 0,5 (2026-09-15): bestaetigt -- und der MECHANISMUS wird sichtbar

**Lauf** `k4_c05_vs_off_s20261095`, angelegt auf 80 Paare, **nach 65 per SPRT gestoppt**
(LLR -7,699 unter der Schranke -6,907, Verdikt H0) -- wie bei Dosis 1,0 zugunsten der
Basislinie, die Frueh-Stopp-Verzerrung wirkt also gegen den Befund, nicht fuer ihn. Laufzeit
1.651,2 s, 12,701 s je Partie, 10 Threads. n = 129 Bretter je Seite im Spaltenblock.

| Groesse | C_est 1,0 (par.7c) | C_est 0,5 | Verhaeltnis 0,5 zu 1,0 |
| --- | --- | --- | --- |
| Siege | 20 : 60 | **45 : 85** | \-- |
| McNemar p | 0,00018 | **0,00054** | \-- |
| gepaarte Differenz | -1,00 | **-0,615** [-0,924, -0,306] | 0,62 |
| eigene Punkte | -14,29 | **-8,26** | 0,58 |
| **volle Spalten** | -0,949 | **-0,837** | **0,88** |
| Spalten >= 4 | -0,474 | -0,411 | 0,87 |
| Spezialfelder belegt | -0,436 | -0,589 | 1,35 |
| Zeilen voll | +0,141 | +0,109 | 0,77 |
| Strafleiste | -0,013 | **-1,566** | \-- |
| Huelle H | -0,101 | -0,076 | 0,75 |

**Beide Dosen schaden hochsignifikant.** Die halbe Dosis halbiert den PUNKTE-Schaden grob
(Faktor 0,58), aber **nicht den SPALTEN-Schaden: davon bleiben 88 Prozent** uebrig. Der
Spaltenbau ist also schon bei 0,5 nahezu voll gestoert -- die Wirkung saettigt lange vor der
vollen Dosis.

*(Vorbehalt: die beiden Laeufe haben verschiedene Seeds und verschiedene n. Jeder ist IN SICH
gepaart und gegen dieselbe Basislinie `round_est_off` gemessen, der Vergleich der Differenzen
ist damit zulaessig -- aber die Verhaeltnisse tragen die Seed-Streuung mit und sind
Groessenordnungen, keine Messwerte.)*

### Der Mechanismus: K4 macht das Netz RUNDENSCORE-GIERIG

Die Randgroessen bei Dosis 0,5 ergeben ein geschlossenes Bild, und es ist genau das, was der
Term verspricht:

* **Die Strafleiste sinkt deutlich** (8,81 gegen 10,37, also -1,57 Strafpunkte je Partie).
* **Volle Zeilen steigen** (+0,109).
* **Volle Spalten brechen ein** (-0,837), **Spezialfelder ebenso** (-0,589).
* **Unter dem Strich 8,3 Punkte weniger.**

`round_estimate_points` ist Solver-Rundenscore plus Strafleisten-Busse (par.3). Der Term liefert
also GENAU, worauf er zeigt: weniger Strafen, mehr sofort abrechenbare Zeilen. Bezahlt wird mit
allem, was ueber die Runde hinausreicht -- Spalten und Spezialfelder sind die langfristigen
Posten dieses Spiels (`project_column_completion_structural_weakness`,
`project_spezialpunkte_sind_reihenabhaengig`).

**Das ist die empirische Gegenprobe zur Nutzer-Frage vom 2026-09-14** (*"nein er optimiert nicht
nur runden score hoff ich mal. dafuer haben wir den einfluss von value head und einhuellender
eingebaut"*): sobald ein Term den Rundenscore mit genug Gewicht an den Blattwert haengt,
optimiert die Suche ihn -- und verliert das Langfristige. Value-Kopf und Einhuellende halten
dagegen, aber nur solange sie nicht ueberstimmt werden. Bei C_est 1,0 kann der Term den ganzen
Wertebereich [0,1] verschieben (par.7c), bei 0,5 die Haelfte.

### Folgerung fuer die Dosisreihe

Der Vorschlag aus par.7c (0,05 / 0,1 / 0,2) bleibt richtig, aber die Erwartung sinkt: wenn
der Spaltenschaden bei halber Dosis zu 88 Prozent erhalten bleibt, ist er bei einem Zehntel
nicht automatisch weg. **Die Sattigung liegt offenbar tief.** Der sachlich naeherliegende Weg
ist damit der zweite aus par.7c: **K4 ein abfallendes Rundenprofil geben wie K3.** Damit
wirkt der Schaetzer dort, wo er hingehoert (frueh, wenn die Runde noch offen ist), und
verschwindet, wenn die langfristigen Posten abgerechnet werden -- statt ueber die ganze Partie
konstant zu druecken.

**Nutzer-Entscheid, nicht selbst gefahren.** Beide Wege sind billig genug, um sie zu messen;
der Profil-Weg ist ein Bau (rund 1 h), die Dosisreihe drei Laeufe a rund 25 min.

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
