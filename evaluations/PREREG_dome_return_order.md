<!-- STATUS: OFFEN | Frage: Die Reihenfolge, in der nicht gewaehlte Kuppelplatten unter den Stapel zurueckgehen, ist ein legaler Zug, der steuert, wann welche Platte wiederkommt -- das Netz legt heute immer in Ziehreihenfolge zurueck. Wird die Wahl gebaut, in welcher Form, und traegt sie? | Beleg: nichts gebaut. Bestand par.2 (self_play.rs:675-684, game.rs:413-423: kanonische Ziehreihenfolge, keine Policy-Dimension). Vorschlag par.4: netzbewertete Rueckgabe als Such-Knopf (Default 0 bitidentisch), A/B ueber den Referee (par.5). Nutzer 2026-09-12: Vollstaendigkeitsfrage, nicht Geschmacksfrage. -->

# Vorregistrierung: Rueckgabe-Reihenfolge der Kuppelplatten als Zug des Netzes

**Angelegt 2026-09-12, 02:00** auf Nutzer-Hinweis. Anlass war die Frage "kann das netz wenn es
mehrere kuppelplatten vom stapel zieht die reihenfolge waehlen und macht es das auch?"; Antwort
am Code: nein (par.2). Nutzer dazu: *"geht weniger darum ob ich es will. das ist ein gueltiger
[Zug] und dadurch laesst sich beeinflussen wann welche kuppelplatte kommt."* Das stellt die
Frage in dieselbe Klasse wie die Kuppelstapel-Informationsmengen
(`PREREG_dome_stack_information_sets.md`): ein Freiheitsgrad, den der Spieler rechtmaessig hat
und den das Modell nicht nutzt. Massstab ist Vollstaendigkeit, nicht Elo (CLAUDE.md
"Symmetrische Defekte sieht keine Arena"; Praezedenz "Korrektheit vor gemessenem Nutzen").

## par.1 Die Regel und was sie hergibt

Beim verdeckten Ziehen vom Kuppelstapel (Aktion A) zieht der Spieler eine oder mehrere Platten,
behaelt eine und legt die uebrigen UNTER den Stapel zurueck; die Reihenfolge waehlt er. Die
Engine prueft `return_order` als Permutation der nicht gewaehlten gezogenen Platten
(`game.rs:244-256`), der Mensch waehlt sie in der GUI (`static/js/app.js:2820-2900`), und der
Rueckleger kennt seinen Block seither in Reihenfolge (Variante A, `state.rs::determinize_dome_pool`;
Nutzer-Entscheid 2026-09-10: die Reihenfolge ist nur dem Rueckleger bekannt). Damit kann ein
Spieler steuern, welche seiner zurueckgelegten Platten als naechste oben liegt, sobald der
unbekannte Praefix aufgebraucht ist; der Gegner sieht nur die Menge.

## par.2 Bestand (Code geprueft 2026-09-12)

- **Netz-Spielpfad:** `self_play.rs:675-684` legt kanonisch in Ziehreihenfolge zurueck, mit dem
  Kommentar, die Reihenfolge sei "fuer die KI keine gelernte Policy-Dimension (wie
  moon_order/num_drawn)". Der Suchbaum (`game.rs:413-423`, `generate_draw_stack_moves`) faechert
  `return_order` ebenfalls nicht auf: ein Kandidat je (Platte, Slot), Rest in Ziehreihenfolge.
- **GUI-Pfad:** `py.rs:289` nimmt denselben Default, wenn der Aufrufer keine Reihenfolge
  mitgibt; die GUI gibt fuer den Menschen eine mit, fuer das Netz nicht.
- **Aktionsraum:** `choose_draw_stack_slot` (355-390) und `choose_dome_rotation` (391-394)
  kodieren Platte, Slot und Rotation; eine Reihenfolge-Aktion gibt es nicht
  (`features.rs:1444-1470`).
- **Records:** die `#a`-Zeile traegt `return_order` (`game.rs:285-290`), Replayer und Logs sind
  darauf eingerichtet; ein Netz, das waehlt, braucht kein neues Record-Feld.
- **Derselbe Bauplan bei den Mondsteinen:** `moon_order` (Reihenfolge der auf die Mondseite
  gelegten Steine nach einem Sonnenzug) ist ebenfalls kanonisch und keine Wahl des Netzes
  (`self_play.rs:234`, `game.rs:413` Kommentar). Gleiche Klasse, hier nur als Merkposten (par.7).

## par.3 Hypothesen (VOR jeder Messung)

- **H1 (Vollstaendigkeit).** Ein Netz, das die Rueckgabe waehlt, spielt regelkonform
  vollstaendiger; das ist unabhaengig vom Messergebnis der Grund, es zu bauen (Nutzer).
- **H2 (Wirkung, klein und spaet).** Die Wahl wirkt nur, wenn (a) mehr als eine Platte gezogen
  wurde (Ziehserien; Median der Ziehungen je Partie 3, `dome_stack_known_block_draws_*.json`),
  (b) der eigene Block spaeter erreicht wird (Praefix aufgebraucht; Anteil "eigener Block" bei
  Ziehungen 22-28 Prozent, dieselben Artefakte) und (c) die Platten im Wert verschieden sind.
  Erwartung: Arena-Effekt unter der Aufloesung von 150 Partien, sichtbar nur in der
  Diagnostik (par.5).
- **H3 (Form).** Eine Erweiterung des Aktionsraums um Permutationen (bis 3! = 6 fuer drei
  Restplatten) lohnt bei ein bis zwei Restgenerationen nicht (neuer Kontrakt, Policy ohne
  Trainingsziel). Eine SUCHSEITIGE Wahl ohne neues Trainingsziel reicht: die Rueckgabe wird wie
  der Tiling-Stichentscheid vom Netz BEWERTET, nicht vorhergesagt.

## par.4 Bauform (registriert VOR dem Bau)

**Knopf `MOSAIC_RETURN_ORDER_MODE`** (Spec-Feld `return_order_mode`, optional, Default 0):

| Wert | Verhalten |
| --- | --- |
| 0 | Bestand: Ziehreihenfolge (bitidentisch, Default) |
| 1 | **netzbewertet**: fuer jede Permutation der nicht gewaehlten Platten (hoechstens 6) den Folgezustand bilden und aus Sicht des Rueckleger mit dem Value-Kopf bewerten (ein Vorwaertspass je Kandidat, Muster `deviation_best_action`/`net_tiling_tiebreak_value` in `self_play.rs`); die beste gewinnt, Gleichstand -> Ziehreihenfolge |
| 2 | Heuristik "beste Platte nach oben": Rangfolge nach der Handregel aus `choose_start_placement`/Plattenwert (Farbtreffer fuer offene Musterreihen, Spezialfelder), Rest in Ziehreihenfolge; ohne Netz, auch fuer die Heuristik-Spieler nutzbar (NICHT fuer den Anker: hv1 bleibt bei 0) |

Wirkort: `self_play.rs` Netzpfad (Ziehserie, Rueckgabe) und `py.rs` GUI-Default; der Suchbaum
(`game.rs:413`) bleibt bei einem Kandidaten je (Platte, Slot), die Wahl faellt am Ende der
Ziehserie, nicht in jeder Simulation (Kosten). Seit Variante A kennt die Suche des Ruecklegers
den Block in der gewaehlten Reihenfolge, die Wahl kommt also spaeter in seinen eigenen
Ziehungen an. Bau: Registratur, `docs/knobs.md`, Test (Modus 1 waehlt bei zwei Platten mit
klar verschiedenem Wert die bessere nach oben; Modus 0 bitidentisch), Netz-Paritaets-Fixture
unveraendert bei 0, Anker-Drift gruen (hv1 liest den Knopf nicht).

## par.5 Messung (VORAB)

1. **A/B ueber den Referee, gleiches Netz** (`v28-b02`, Champion-Spec), Modus 1 gegen Modus 0,
   150 Partien, zwei Seed-Basen (Blockgroesse 5). Verdikt "traegt" bei Vorzeichentest p < 0,05,
   sonst "kein messbarer Effekt", und der Knopf bleibt trotzdem (H1, Nutzer-Praezedenz).
2. **Diagnostik aus den Logs** (Grundmenge Rueckgaben mit >= 2 Restplatten, Einheit Rueckgaben):
   Anteil der Rueckgaben, deren Reihenfolge von der Ziehreihenfolge abweicht; Anteil, bei dem
   der Rueckleger die oben gelegte Platte spaeter selbst zieht; Ziehungen in den eigenen Block
   bei positivem Stand (wie `dome_stack_known_block_draw_probe.py`). Erwartung nach H2: die
   Abweichungsrate ist hoch, die Wiederkehr-Rate niedrig.
3. Sechs Standard-Kennzahlen (CLAUDE.md) aus denselben Logs.

## par.6 Kosten und Eintaktung

Bau rund 3 h (Permutationen, Bewertung, Knopf, Tests), Wheel, Fixture, Drift; Messung rund
45 min (2 x 150 Partien) plus Diagnostik. Eintaktung: NACH der Neuverankerung und der
Promotion von v28-b02 (beide laufen auf dem heutigen Wheel; ein Engine-Knopf dazwischen
haette die Promotionskanten auf eine andere Engine gestellt), als Teil des
v29-Begleitprogramms (`PREREG_v29_window.md` par.7 Punkt 4, gleiche Gruppe wie Stopp-Regel und
Peek-Bewertung). Wird Modus 1 Default (Nutzer-Entscheid), gilt er fuer die v29-Erzeugung.

## par.7 Was NICHT gebaut wird

- Keine Aktionsraum-Erweiterung, kein neues Trainingsziel (H3).
- `moon_order` (Mondsteine) bleibt kanonisch; derselbe Bauplan waere moeglich (Merkposten,
  eigener Entscheid).
- Kein Eingriff in die Heuristik-Anker (hv1/hv2 bleiben bei Modus 0).

## par.8 Ergebnisse (leer bis zum Bau)

Nichts gebaut (Stand 2026-09-12, 02:00).

## par.8a BAUSTAND 2026-09-12 (Code geschrieben, noch nicht kompiliert)

Knopf `return_order_mode` (Spec optional, Env `MOSAIC_RETURN_ORDER_MODE`, 0/1/2) nach par.4 gebaut:
`self_play.rs` (`order_permutations`, `return_order_candidates`, `choose_return_order`,
`resolve_and_apply_stack_draw_with`, Diagnostik-Zeile `[return_order] mode=.. drawn=[..]
chosen=[..]`), `py.rs` GUI-Default und `ai_drafting_net_step`, `referee.rs` In-Process-Seite,
Registratur, `engine_config`, Spec-Abbildungen, sechs Tests. Zwei Bau-Entscheide ueber par.4
hinaus: (1) permutiert werden hoechstens die ersten drei Restplatten (`RETURN_ORDER_MAX_PERMUTED`),
der Schwanz bleibt in Ziehreihenfolge (`MAX_STACK_PEEKS` erlaubt laengere Serien; wie oft, ist
nicht gemessen); (2) Handregel Modus 2 mit gesetzten Gewichten Spezial 2, Joker 1, Farbtreffer
1. **Oben liegt `return_order[0]`** (geprueft: `game.rs:187` zieht per `remove(0)`, `game.rs:290-295`
legt per `push` in Reihenfolge zurueck, der Block liegt unten und `[0]` kommt zuerst wieder).

**Zwei Befunde, die par.5 vorab einordnen (am Code geprueft, nicht gemessen):**
1. Der Value-Kopf sieht die Reihenfolge nur als TYP-Folge: `features.rs:212` kodiert fuer die
   obersten vier Positionen des eigenen Blocks +1 Spezial / -1 Joker / 0. Permutationen
   gleichtypiger Platten sind fuer das Netz identisch, Modus 1 waehlt dann per Gleichstand die
   Ziehreihenfolge. Die Abweichungsrate ist damit strukturell gedeckelt; ein Kopf, der
   Plattentypen im Block unterscheidet, waere die naechste Stufe (nicht registriert).
2. Modus 1 braucht die Sicht des Ruecklegers im FOLGEZUSTAND, in dem der Gegner am Zug ist;
   `net_leaf_eval` liefert beide Bretter nur ueber den gespiegelten zweiten Vorwaertspass
   (`MIRROR_OTHER_VAL = false`, `net_mcts.rs:1117`). Kosten je Kandidat: ein `eval_pair`-Batch,
   nicht ein Pass.
Kompilierung, Fixture, Drift und die Messung par.5 folgen nach der Promotion von v28-b02.
