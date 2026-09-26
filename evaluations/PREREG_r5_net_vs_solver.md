<!-- STATUS: OFFEN | Frage: Spielt das Netz Runde 5 besser als der Expectiminimax-Loeser (200 Knoten, statischer Endwert am Blatt) -- und traegt danach ein Hybrid aus Loeser-Blatt und Punkte-Kopf? | Beleg: angelegt 2026-09-26, nichts gebaut, nichts gefahren. Stufe 1 ist ein gepaartes A/B desselben Champions, Loeser gegen Netzsuche in Runde 5 (par.3); braucht einen je Seite setzbaren Schalter (par.2). Stufe 2 (Hybrid) nur nach Stufe 1 (par.5). -->

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

## par.6 ERGEBNISSE

(noch leer)
