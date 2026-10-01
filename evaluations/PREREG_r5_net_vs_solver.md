<!-- STATUS: OFFEN | Frage: Spielt das Netz Runde 5 besser als der Expectiminimax-Loeser (200 Knoten, statischer Endwert am Blatt) -- und traegt danach ein besserer Loeser? | Beleg: Stufe 1 ENTSCHIEDEN (par.6a): das Netz spielt Runde 5 besser, 495:305 = 61,9 %, gepoolt z +10,17. Der heutige Loeser ist eine Tiefensuche ohne Vertiefung (round5.rs:590-624); Stufe 2a (par.5a): iterativer Loeser gegen das Netz, gebaut; Sonde (par.6b): beim heutigen Loeser frisst das erste Kind in 86 von 117 Entscheidungen das Budget, iterativ @2000 kostet 129 ms Median je Entscheidung. Offen: A/B Stufe 2. -->

# Vorregistrierung: Runde 5 -- Netz gegen Loeser

**Angelegt 2026-09-26.** Nutzer: *"Ist Runde 5 mit unserem solver wirklich das Optimum? Was
haeltst davon das Netz spielen zu lassen, evtl. mit dem point head als helfer"*, auf die Vorlage:
*"Ja leg Stufe 1 als prereg an. Dann haben wir ein schoenes Paket fuer diese generation"*.

## par.1 WARUM: der Loeser in Runde 5 wurde nie gegen das Netz gegatet

**Am Code gelesen 2026-09-26** (`engine/src/round5.rs`, Modulkopf und `net_solver_enabled`,
Z.170-187): dass der Loeser das Netz in Runde 5 ersetzt, *"wurde NIE gegatet"* -- er kam in
98dffa3 gebuendelt herein, begruendet mit "die Runde ist exakt loesbar". Beides stimmt nicht:
* **Keine Loesung:** 200 Knoten bei Wurzelverzweigung ~20 reichen fuer ~3 Halbzuege. Exakt ist nur
  der BLATTWERT: der Endwert des erreichten Bretts (optimales Tiling plus Endwertung,
  `solve_round_final_score_endaware`), als ende die Runde am Blatt. Was danach in der Runde noch
  gedraftet wird, sieht der Blattwert nicht -- Lesart des Kommentars, im Code nicht tiefer geprueft.
* **Keine volle Information:** die Zuordnung der 4 frischen Bonuschips ist verdeckt (Zufallsknoten).

**Was die vorhandenen Zahlen belegen und was nicht** (`PREREG_chance_nodes.md` Teil E): der Loeser
@200 trifft zu 81,4 % (118/145) dieselbe Wahl wie ein Orakel mit 20.000 Knoten, das Netz@400 zu
51,7 %. **Das Orakel ist derselbe Loeser mit DEMSELBEN Blattwert** -- die Zahlen messen
Selbst-Uebereinstimmung, nicht Spielstaerke. Eine Arena Netz gegen Loeser in Runde 5 ist in
`PREREG_chance_nodes.md` Teil E und `PREREG_r5_solver_split.md` nicht registriert; die dort
eingetakteten Netz-Loeser-Arme (par.4: Knotenbudget, Policy-Sortierung, Korrekturterm) sind nie
gelaufen (`PREREG_v29_window.md` par.7 Punkt 4, "nach Maschinenlage").

**Fuer und gegen das Netz** (`PREREG_r5_solver_split.md` par.3e, 200 R5-Startzustaende): der
Value-Kopf ordnet die Loeser-Marge gut (Tau 0,76, Steigung Gesamtwert 0,87), sieht aber den
PLATTEN-Anteil kaum (Steigung 0,06-0,09) -- genau den Teil, den der Loeser exakt rechnet und der in
Runde 5 realisiert wird. Umgekehrt kennt das Netz die Drafting-Dynamik jenseits von 3 Halbzuegen.
Welche Seite ueberwiegt, ist die Frage dieser Prereg. Vorab-Vermutung aus Teil E (dort notiert):
"ein Sieg des Netzes waere ein Hinweis, dass die Drafting-Interaktion mehr wiegt als die exakte
Endabrechnung".

## par.2 BAU (in der naechsten Wheel-Runde, zusammen mit E1, Review-Fixes, Spiegelknopf)

`MOSAIC_R5_NET_SOLVER` ist heute ein prozessweiter OnceLock (`round5.rs:180-187`) und wirkt damit
in einer Arena auf BEIDE Seiten. Fuer ein A/B braucht es denselben Schalter **je Seite**, als
Spec-Feld der Seite (`r5_net_solver`, Default an = Bestand, byte-identisch). Dazu:
* Paritaet und Anker-Drift wie bei jedem Engine-Eingriff; der Anker nutzt den eingefrorenen
  `round5_anchor.rs` und ist per Konstruktion unberuehrt.
* Mit Schalter aus sucht das Netz in Runde 5 wie in Runde 1-4 (Gumbel@400, Netz-Blattwert).
  Beim Bau pruefen und hier nachtragen, ob dann noch irgendein anderer Pfad den Loeser in Runde 5
  zieht (Tiling-Zug Runde 5, Label-Rollouts).

## par.3 STUFE 1: A/B, Leseregel VORAB

* **Arme:** Champion (nach der v33-Promotionsentscheidung) mit Loeser in Runde 5 (Bestand) gegen
  DENSELBEN Champion mit Netzsuche in Runde 5. Einziger Unterschied `r5_net_solver`.
* **Instrument:** `tools/paired_gating.py`, Spec `models/v33_gating.spec.json` bis auf das Feld,
  zwei Seeds (20261670, 20261671) a 200 Paare, Blockgroesse 5, fester Umfang (SPRT-Schranken
  alpha = beta = 1e-12), `--log-games`, Block-z ueber `tools/gating_block_z.py`.
* **Leseregel (Seite A = Netz in Runde 5):**
  * gepoolt z >= +1,96: **das Netz spielt Runde 5 besser** -> Rezeptfrage fuer v34 (Nutzer), dazu
    die Folge fuer die R5-Policy-Ziele: heute werden sie aus den Loeser-Zuegen destilliert
    (One-Hot, `net_mcts::net_root_child_stats_and_policy`), mit Netzsuche waeren es
    Besuchsverteilungen.
  * gepoolt z <= -1,96: **der Loeser ist besser** -> er bleibt; Stufe 2 prueft, ob ein Hybrid ihn
    noch verbessert.
  * dazwischen: gleich stark in dieser Aufloesung -> Stufe 2 entscheidet; bei weiter gleich bleibt
    der Loeser (billiger, deterministisch).
* **Berichtet** (CLAUDE.md, sechs Kennzahlen) und dazu: Punkte je Wertungsplatte in Runde 5 und
  die Strafleiste in Runde 5 getrennt -- dort sollte sich der Unterschied zeigen, falls er aus dem
  Plattenanteil oder aus dem Drafting kommt.
* **Kosten:** A/B rund 3,4 h (v33 Tor 1: rund 150 s je Block, 40 Bloecke je Seed); Bau in der
  Wheel-Runde ohne eigenen Maschinenlauf. Laufzeit-Block im Artefakt.

## par.4 WANN

Nach b03 (`PREREG_v33_window.md` par.6b) und der Wheel-Runde, im Paket der v33-Generation
(E1-Arm `PREREG_evaluator_pretests.md` par.5, Spiegelknopf `PREREG_tie_mirror.md`, gezieltes
Abzweigen `PREREG_targeted_branching.md` Stufe 1).

## par.5 STUFE 2 (nur nach Stufe 1, Zuschnitt dann hier nachtragen)

Hybrid: Loeser-Blatt plus ein Korrekturterm fuer das, was jenseits des Horizonts in der Runde noch
gedraftet wird -- der Punkte-Kopf ist der natuerliche Kandidat, weil er "noch kommende Punkte"
schaetzt (Arm c aus `PREREG_r5_solver_split.md` par.4). Abgrenzung: der Punkte-Kopf ALS Blattwert
war im Vierervergleich signifikant schlechter als der Value-Kopf (22:48, par.3e dort); hier ist er
Ergaenzung zum exakten Blatt, nicht Ersatz.

## par.5a STUFE 2a, REGISTRIERT 2026-09-27 VOR jedem Bau: Loeser mit iterativer Vertiefung gegen das Netz

**Nutzer 2026-09-27:** *"bau ihn mal, dann sehen wir wieviel wir von der spielstaerke gewinnen im
austausch fuer die zeit die er braucht. als referenz haben wir nun das netz."* Anlass: Stufe 1
Seed 20261670 243:157 fuer das Netz (Verdikt folgt in par.6), und ein Bauform-Befund am Loeser.

**Der Befund (am Code gelesen 2026-09-27, `engine/src/round5.rs:590-624`):** `choose_action_deadlined`
durchsucht die Wurzelkinder der Reihe nach mit Tiefe `MAX_DEPTH - 1` und EINEM Knotenzaehler fuer
alle; ist das Budget erschoepft, bricht die Schleife ab und gibt das beste bisher bewertete Kind
zurueck. Ohne iterative Vertiefung kann schon das erste Kind das Budget von 200 Knoten
verbrauchen; dann ist der Loeser faktisch die Vorsortierung (`ordered_children`, statischer
Wert "als ende die Runde jetzt"). HERLEITUNG, wie oft das greift ist UNGEMESSEN (Pruefung unten,
Punkt 1). Die Lesart "~3 Halbzuege" im Modulkopf (`round5.rs:22-28`) und die 81,4 % Orakel-
Uebereinstimmung (derselbe Suchaufbau mit 20.000 Knoten) sind damit nicht mehr tragfaehig.

**Bau (Rust, per Seite, Default aus = byte-identisch):**
* Neue Spec-Felder je Seite `r5_solver_iterative` (0/1, Default 0) und `r5_solver_node_budget`
  (Default = heutiges Budget). Mit `r5_solver_iterative` 1: iterative Vertiefung d = 1, 2, 3 ...
  mit Alpha-Beta bis Tiefe d, statischer Blattwert an der Tiefengrenze wie heute, Wurzelkinder je
  Iteration nach den Werten der vorigen sortiert; Rueckgabe = bester Zug der letzten VOLLSTAENDIGEN
  Iteration (bei Budgetende mitten in einer Iteration). Zufallsknoten wie heute.
* Not-Deckel pro Entscheidung mit dem Budget skaliert (Muster `TIME_BUDGET`: Worst-Case 4,4 ms je
  Knoten x 5, `round5.rs:90-96`), bleibt Ausfallschutz; bindend ist das Knotenbudget.
* Kalibriersonde (`#[ignore]`-Test nach dem Muster `round5_node_calibration_probe`): auf
  realistischen Runde-5-Stellungen je Entscheidung erreichte volle Tiefe, Knoten, Millisekunden;
  fuer den heutigen Loeser zusaetzlich, wie oft er `ordered_children[0]` zurueckgibt, weil das
  Budget im ersten Kind endete (Befund oben).

**Bau-Stand 2026-10-01 (Quelltext, Agent, NICHT kompiliert):** Spec-Felder je Seite
`r5_solver_iterative` (Env-Default `MOSAIC_R5_SOLVER_ITERATIVE`) und `r5_solver_node_budget` (nur
Spec-Feld, `spec_env.py` begruendet ausgenommen, weil `MOSAIC_R5_NODE_BUDGET` prozessweit wirkt);
`round5.rs` `choose_action_iterative` (Tiefe 1 = Vorsortierung, dann d = 2, 3 ...), Default-Pfad ruft
denselben Kern wie `choose_action`; Kalibriersonde `r5_iterative_deepening_calibration_probe`
(`#[ignore]`). Build, Tests und Anker-Invarianz in der Wheel-Runde mit dem KL-Knopf.

**Messung, Stufenleiter von oben:**
1. **Sonde** (Kosten und Tiefe, deterministisch, Minuten): heutiger Loeser @200, iterativ @400,
   @2000, dazu die Netzsuche @400 und @100 in Millisekunden je Runde-5-Entscheidung, auf denselben
   Stellungen. Berichtet: Median und p90 der Zeit, Verteilung der erreichten vollen Tiefe, und die
   Quote "erstes Kind verbraucht das Budget" beim heutigen Loeser.
2. **A/B oben:** Champion `v32-b01`, Seite A iterativer Loeser **@2000**, Seite B Netz in Runde 5
   (`r5_net_solver` 0, die Referenz aus Stufe 1), sonst `models/v33_gating.spec.json`; Seeds
   **20261672 / 20261673** a 200 Paare, Blockgroesse 5, fester Umfang (SPRT 1e-12), `--log-games`,
   Block-z. Laufzeit-Block im Artefakt.
3. **A/B unten, nur wenn Stufe 2 z >= +1,96:** dasselbe mit **@400**, Seeds 20261674 / 20261675.

**Leseregel, VORAB (A = iterativer Loeser):**
* Stufe 2 z <= -1,96: das Netz schlaegt auch den tieferen Loeser -> **Loeser-Linie geschlossen**,
  das Netz spielt Runde 5; Stufe 3 entfaellt (Annahme: mehr Budget spielt nicht schlechter,
  ausdruecklich eine ANNAHME).
* Stufe 2 dazwischen: gleich stark -> das Netz bleibt, falls es je Entscheidung nicht teurer ist
  (Sonde); sonst Nutzer-Entscheid nach der Zeittabelle.
* Stufe 2 z >= +1,96: der Loeser traegt -> Stufe 3. Danach **Nutzer-Entscheid Staerke gegen Zeit**
  auf der Tabelle (Siegquote je Budget, ms je Entscheidung, s je Partie), getrennt fuer Champion/GUI
  (400 Sims, Zeit zweitrangig) und Erzeugung (100 Sims, Zeit zaehlt).
* Berichtet wie Stufe 1 (sechs Kennzahlen, Runde 5 getrennt: Strafleiste, Plattenpunkte).

**Zeitplan:** Bau jetzt (Quelltext), Build in der Wheel-Runde vor der v34-Erzeugung (Default aus,
Anker-Invarianz). Die v34-Erzeugung faehrt Runde 5 nach dem Verdikt von Stufe 1; die A/B hier laufen
parallel zum v34-Training (GPU und EIN CPU-Auftrag, `docs/working_rules.md`). Die Frage, wer in der
ERZEUGUNG Runde 5 spielt, bleibt fuer v34 damit beim Ergebnis aus Stufe 1 (Nutzer-Abwaegung
2026-09-27, Kosten eines halben Tags Verzug gegen sauberere Ausgaenge).

**Kosten (Herleitung, durch die Sonde UEBERHOLT, par.6b: @2000 gemessen 129 ms Median je
Entscheidung):** Knotenkosten 0,3-4,4 ms (`round5.rs:81-83`); @2000 also rund 0,6-9 s je
Entscheidung. Ein A/B-Seed dauerte in Stufe 1 6.504,5 s (16,26 s je Partie); mit @2000 auf einer
Seite laenger, UNGEMESSEN, die Sonde liefert die Planungszahl vor dem Start.

## par.6 ERGEBNISSE

### par.6a Stufe 1 (Nachtkette `tools/night_v33_package.sh`, 2026-09-27 15:33-19:23)

Champion `v32-b01`, A = Netzsuche in Runde 5 (`models/v33_gating_r5net.spec.json`, `r5_net_solver`
0), B = Loeser (`v33_gating.spec.json`), je 200 Paare, fester Umfang, Blockgroesse 5, `--log-games`.

| Seed | A : B | Block-z | Sweeps A / B | Punkte | Marge (je Brett) | Strafleiste | volle Spalten je Seite |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 20261670 | **243:157** | **+6,49** | 47 / 4 | 60,77 / 56,51 | +4,27 | 6,63 / 7,94 | 1,108 / 0,953 |
| 20261671 | **252:148** | **+7,89** | 59 / 7 | 61,18 / 56,29 | +4,89 | 6,74 / 8,51 | 1,158 / 0,963 |
| **gepoolt** | **495:305 = 61,9 %** | **+10,17** | | | | | |

Gepaart je Partie (Seed 1 / Seed 2): Punkte +4,27 [+3,43; +5,10] / +4,89 [+4,06; +5,72].
Plattenpunkte je Kriterium: `evaluations/artifacts/ab_r5net_v32-b01_s2026167{0,1}_plate_points.json`.
Die Aufschluesselung nach Runde 5 (Strafleiste, Plattenpunkte, par.3 "berichtet") steht AUS; sie
kommt aus den `--log-games`-Logs zusammen mit der Loeser-Diagnose aus par.5a Punkt 1.

**Laufzeit:** 6.504,5 s (16,26 s je Partie) und 7.280,9 s (18,20 s je Partie), 10 Threads. **Auf Seed
20261671 wurden die Bloecke ab Nr. 15 (ab rund 18:00) von rund 155 s auf 195-242 s langsamer**; das
faellt mit zwei Lese-Agenten des Koordinators zusammen (Sicht-Audit, Loeser-Bau; einer fuehrte
regelwidrig einmal `python -c "print('skip')"` aus). Seed 20261671 steht damit unter
Nebenlast-Verdacht, gemeldet an den Nutzer. **Das Verdikt haengt daran nicht:** Seed 20261670 allein
(Bloecke 147-176 s, gleichmaessig) hat z +6,49.

**Sicht-Audit vor dem Verdikt** (Agent, Kernstelle vom Koordinator am Code nachgelesen,
`round5.rs:590-624`): kein Informationsleck der Netzseite (Wurzel-Determinisierung mischt verdeckte
Chips, Encoder liest Chipfarben nur aufgedeckt), Schalter wirkt nur je Seite, Tiling und Vorzug in
Runde 5 fuer beide Seiten gleich. Aber: der Loeser ist eine Tiefensuche ohne iterative Vertiefung
mit EINEM Knotenzaehler -- er misst sich hier vermutlich als gieriger Vorsortierer (par.5a).

**Verdikt nach par.3: gepoolt z +10,17 >= +1,96 -> das Netz spielt Runde 5 besser als der heutige
Loeser.** Folgen, Rezeptfrage an den Nutzer: (a) v34-Erzeugung mit Netzsuche in Runde 5, dann werden
die R5-Policy-Ziele Besuchsverteilungen statt Loeser-One-Hot (`net_mcts.rs:6796`, gegatet); (b) der
Champion spielt mit dieser Spec als eigene gemessene Identitaet (`feedback_measured_identity`);
(c) das Label am Uebergang Runde 4 -> 5 (`exact_round5_outcome`, `self_play.rs:6510-6515`) laeuft
weiter ueber dieselbe Tiefensuche und ist vom Schalter NICHT erfasst -- offener Punkt fuer par.2.
Stufe 2a (iterativer Loeser gegen das Netz) misst, ob der Abstand am Blattwert oder an der Suchform
liegt. Elo-Register zwei Zeilen 2026-09-27 (`v32-b01-r5net`).

**NUTZER-ENTSCHEID 2026-10-01:** *"Runde 5 mit Netz, Seed 2 nicht wiederholen"* -- die v34-Erzeugung
spielt Runde 5 per Netzsuche (Env im Rezept, `PREREG_v34_window.md` par.5 Punkt 3); Seed 20261671 bleibt
mit Nebenlast-Vermerk stehen. Champion-Spec und R5-Kalibrierung bleiben offen bis zur naechsten
Promotion bzw. Stufe 2a.

### par.6b Stufe 2a, Punkt 1: Kalibriersonde (2026-10-01, exklusiv, Wheel 1.1.0)

`cargo test --release --lib r5_iterative_deepening_calibration_probe -- --ignored --nocapture`
(Test-Binary aus dem Cache, kein Kompilieren), Wanduhr 24,3 s, 1 Thread, Zufallsknoten an
(`chance=true`). Rohzeilen: `evaluations/artifacts/r5_iterative_calibration_probe_20261001.txt`.
**Grundmenge:** Runde-5-Entscheidungen mit mindestens 2 Kandidaten auf 8 Stellungen
`drive_to_round_start(seed, 5)`, Seeds 101-808, die Runde gespielt mit dem heutigen Loeser @200;
**n = 117 Entscheidungen**, Einheit je Spalte unten. Alle drei Arme auf denselben 117 Stellungen.

| Arm | ms Median / p90 / max | Knoten Median | erreichte volle Tiefe (Anzahl Entscheidungen) | Rundenende erreicht | Zug aus angebrochener Iteration | gleicher Zug wie alt@200 |
| --- | --- | --- | --- | --- | --- | --- |
| alt@200 (heute) | 9 / 25 / 211 | 203 | -- | -- | -- | -- |
| iterativ @400 | 24 / 126 / 257 | 400 | 1:8, 2:60, 3:20, 4:14, 5:9, 6:4, 7:2 | 19/117 | 8/117 | 93/117 (79,5 %) |
| iterativ @2000 | 129 / 268 / 721 | 2000 | 2:33, 3:41, 4:18, 5:5, 6:5, 7:10, 8:4, 9:1 | 30/117 | 10/117 | 77/117 (65,8 %) |

**Befund aus par.5a beantwortet:** beim heutigen Loeser frisst das ERSTE Wurzelkind das Budget in
**86 von 117 Entscheidungen (73,5 %)**; in genau diesen 86 wurde nur ein Kind durchsucht. Dort
entscheidet die Vorsortierung (`ordered_children[0]`), nicht die Suche. Die Bauform-Lesart aus
par.5a ist damit gemessen, nicht mehr Herleitung.

**Kosten, gegen die Herleitung in par.5a:** dort standen "@2000 rund 0,6-9 s je Entscheidung"
(aus 0,3-4,4 ms je Knoten); gemessen sind 129 ms Median, p90 268 ms, max 721 ms je
Entscheidung, also rund 0,06 ms je Knoten im Median. Die Herleitung lag um mehr als eine
Groessenordnung zu hoch; die Planungszahl fuer Stufe 2 ist die gemessene. Einschraenkung:
1 Thread auf freier Maschine; im A/B laufen 10 Partien parallel (Cache-/Speicherdruck UNGEMESSEN).

**Nicht gemessen von der Sonde:** die Netzzeiten je Runde-5-Entscheidung @400 und @100 (die Sonde
misst nur Loeser-Arme, Doc-Kommentar `round5.rs:2299`). @100 ergibt sich als Differenz aus dem
Kostentor der v34-Erzeugung (`PREREG_v34_window.md` par.5 Punkt 3) je Partie, nicht je
Entscheidung; @400 steht AUS, bis eine Sonde dafuer gebaut ist (nicht vor Stufe 2 noetig, weil
Stufe 2 die Wanduhr je Partie im Artefakt traegt).
