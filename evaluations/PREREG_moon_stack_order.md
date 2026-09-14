<!-- STATUS: OFFEN | Frage: Die Reihenfolge der Mondsteine nach einem Sonnenzug ist im Netzpfad ein Suchentscheid -- traegt das, und ist das Trainingsziel des Kopfs das richtige? | Beleg: Knopf GEBAUT und im Wheel (par.8). **A/B GEMESSEN 2026-09-14 (par.7): H1 NICHT bestaetigt** -- 193:207, p=0,55, Punkte 53,0 gegen 54,8; Fan-out bleibt. **Gueltig, kein Henne-Ei** (Knopf war bei der Erzeugung an, moon-Kopf trainiert). Gegenhypothese von H1 WIDERLEGT (nur der oberste Stein je Stapel ist ziehbar, die Reihenfolge steuert den Zugriff) -- der Nullbefund ist gemessen, nicht erklaert. **H2 (Zielwechsel) bleibt lebend**, Nutzer-Entscheid. -->

# Vorregistrierung: Mondstapel-Reihenfolge (Moon-Order) als Optimierungsposten

**Angelegt 2026-09-12** (Nutzer: *"dann haben wir irgendwann vor uhrzeiten festgehalten dass wir
uns den mondstapel auch anschauen bzgl. optimierung. ich denk mit v29 oder v30 waere ein guter
zeitpunkt"*). Vorlaeufer-Notizen: `PREREG_stack_top_feature.md` par.10 P.8 (Klaerung des Stapels),
`archive/history.md` 2026-08-25 (Nutzer-Review: "Mondstapel-Reihenfolge ist eine legale Wahl, die
`generate_valid_moves` nie aufspannt"), `PREREG_dome_return_order.md` par.2/par.7 (Merkposten,
dort UNGENAU formuliert, siehe par.2 hier).

## par.1 Die Regel

Nach einem Sonnenzug aus einer kleinen Fabrik legt der Ziehende die restlichen Sonnensteine in
selbst gewaehlter Reihenfolge auf die Mondseite (`docs/engine_manual.md`; `factory.rs:61-66`
`place_on_moon`, EIN Stapel mit hoechstens 3 Steinen). Die Reihenfolge ist Teil des Zugs
(`TakeAction::moon_order`, `execution.rs:154`).

## par.2 Bestand (Code geprueft 2026-09-12)

- **Heuristik-Pfad:** `validation.rs:175-193` erzeugt je (Farbe, Reihe) GENAU EINEN Zug mit der
  kanonischen Restreihenfolge (Filter ueber `sun_tiles`). Die Heuristik waehlt nie.
- **Netz-Suchpfad:** `net_mcts.rs:1724-1920` (Commit c01c305, 2026-07-01, "Suche-getriebene
  Moon-Order-Wahl"): beim Expandieren eines SmallFactorySun-Knotens mit >= 2 Reststeinen werden
  ALLE eindeutigen Permutationen (`unique_moon_orders`) als Kinder angelegt, Prior = P(Basis) x
  P(Reihenfolge | Plackett-Luce ueber die 5 Farb-Scores des `moon_order_head`). Kein Knopf, immer
  aktiv. Die Aktions-ID kodiert die Reihenfolge nicht (406 Aktionen bleiben).
- **Kopf und Ziel:** `engine/py/neural_net.py:1458` (5 Logits, hoch = Farbe tief im Stapel),
  trainiert mit `moon_loss_weight 1.0` (Manifest v28-b02). Ziel `moon_order_target`
  (`self_play.rs:1052ff`): beste Reihenfolge der Reststeine nach `solve_round_final_score`
  ueber alle Permutationen (bei hoechstens 3 Steinen sind das hoechstens 6, also ERSCHOEPFEND;
  Nutzer 2026-09-12, Korrektur der ersten Fassung "Stichproben"), also ein RUNDEN-Label (was am
  Rundenende am meisten bringt), kein Such- oder Ausgangslabel.
- **Haeufigkeit (Nutzer):** der Entscheid faellt hoechstens EINMAL je kleiner Fabrik und Runde
  (der erste Sonnenzug aus der Fabrik legt den Stapel), also 4 je Runde und rund 20 je Partie;
  Nutzer: "ziemlich genau 20, die wahrscheinlichkeit dass 4 gleiche farben auf einer fabrik
  liegen ist gering". Korpus-Beleg: 199 Ziele in einer Datei mit 10 Partien = 19,9 je Partie.
  Ein Entscheid je Fabrik und Runde, mit hoechstens 6 Alternativen; der Posten ist damit klar
  umrissen und eher klein. Im Korpus `selfplay_v27-b01-policy_..._g10.pkl`
  tragen 199 von 1.675 Records ein Ziel (Sonnenzuege aus kleinen Fabriken mit Rest >= 2).
- **Korrektur einer Notiz:** `PREREG_dome_return_order.md` par.2 nennt `moon_order` "kanonisch
  und keine Wahl des Netzes". Das gilt fuer `self_play.rs:234` (Aktionsraum/Record) und fuer den
  Heuristik-Pfad, NICHT fuer die Netzsuche. Dort korrigiert.

## par.3 Hypothesen (VOR jeder Messung)

- **H1:** der Fan-out traegt messbar: Champion mit Varianten gegen denselben Champion mit
  kanonischer Reihenfolge (Fan-out AUS) gewinnt gepaart. Gegenhypothese: die Reihenfolge ist im
  Duell fast immer irrelevant (Mondsteine werden ohnehin komplett gezogen), der Fan-out kostet nur
  Suchbudget (bis zu 6 Kinder statt 1 je Sonnenzug).

  **KORREKTUR 2026-09-14 (Nutzer: "das alle 3 die selbe farbe haben beim ziehen ist eher ein
  ausnahmenfall"): die Klammer der Gegenhypothese ist FALSCH.** Mondsteine werden NICHT komplett
  gezogen. `docs/engine_manual.md` Zeile 101-106, Zug C: *"Collect every TOPMOST tile of one
  chosen colour across the moon areas of all factories at once -- ONE TILE PER STACK"*, und zu
  Zug B: *"the taking player decides the stack order of those leftovers, WHICH MATTERS: only the
  top tile of a moon stack can be taken later."* Am Code bestaetigt: `factory.rs:76` und `:96-97`
  pruefen und nehmen `stack.last()`, also nur den obersten.

  **Die Reihenfolge ist damit Zugriffssteuerung, nicht Kosmetik:** wer oben liegt, ist als
  naechstes verfuegbar, die beiden darunter sind blockiert, bis er weg ist. Irrelevant waere sie
  nur bei drei gleichfarbigen Resten -- der Ausnahmefall. **Ein Nullbefund ist damit nicht durch
  die Mechanik erklaerbar und braucht eine andere Erklaerung** (siehe par.7).
- **Erwartung:** klein, wegen der Haeufigkeit (par.2); ein Nullbefund bei 200 Paaren ist der
  wahrscheinliche Ausgang und dann ein vollwertiges Ergebnis (Fan-out bleibt aus Gruenden der
  Vollstaendigkeit).
- **H2:** das Rundenloeser-Ziel ist kurzsichtig (Rundenende statt Partieausgang); ein Ziel aus der SUCHE (die vom Baum gewaehlte
  Reihenfolge, wie beim Rueckgabe-Knopf Modus 1 gedacht) oder aus dem Ausgang traegt mehr.
  Nur pruefbar nach H1 und nur mit Training (ein Arm).

  **NACHTRAG 2026-09-14: die Bindung "nur pruefbar nach H1" stand auf der falschen
  Gegenhypothese.** Sie hiess sinngemaess: wenn die Reihenfolge ohnehin egal ist, lohnt kein
  besseres Ziel. Da sie NICHT egal ist (Korrektur oben), faellt H2 mit einem H1-Nullbefund nicht
  automatisch weg -- im Gegenteil, ein kurzsichtiges Ziel ist dann eine der wenigen verbliebenen
  Erklaerungen dafuer. **H2 bleibt eine lebende Option**; sie ist zudem KEIN neuer Kopf, sondern
  ein Zielwechsel am bestehenden -- und nur der Neubau ist gesperrt
  (`feedback_no_new_heads`).

## par.4 Stufe 1 (v29-Begleitprogramm, ein Referee- oder Gating-Lauf, kein Training)

Knopf `MOSAIC_MOON_ORDER_VARIANTS` (Default 1 = BESTAND, bitidentisch; 0 = nur die kanonische
Reihenfolge wie im Heuristik-Pfad), Spec-Feld `moon_order_variants` (optional, fehlt = 1, damit
alle eingefrorenen Specs weiter laden). A/B am amtierenden Champion, beide Seiten gleiche Spec
bis auf dieses Feld, 200 Paare, Blockgroesse 5, `--log-games`, Standard-Kennzahlen; zusaetzlich
je Seite: Anteil der Sonnenzuege mit Rest >= 2 und Anteil davon, in denen die gewaehlte
Reihenfolge NICHT die kanonische ist (aus den Logs, `#a`-Zeile traegt `moon_order`). Lesart: Sieg
und Punkte gepaart ueber der Aufloesung -> H1; sonst Fan-out bleibt (Vollstaendigkeit, Nutzer-
Praezedenz Rueckgabe-Reihenfolge), aber die Zielfrage par.5 wird nicht weiterverfolgt.

## par.5 Stufe 2 (nur bei H1 positiv, v30): Ziel des Kopfs

Ein Arm mit Suchziel statt Rundenloeser-Ziel (Record traegt die vom Baum gewaehlte Reihenfolge,
`policy_target_valid`-Muster), Tor 1 gegen den Vorgaenger, Orakel-Metriken ohne Aussage
(die Bruecke kennt die Reihenfolge nicht). Kosten: ein Trainingsarm (rund 1,5 h) plus Gating.

## par.6 Was NICHT gebaut wird

- Keine Erweiterung des Aktionsraums (406 bleibt), kein Fan-out im Heuristik-Pfad (Anker).
- Keine Aenderung an `moon_order_target` vor par.4.

## par.7 ERGEBNIS Stufe 1 (2026-09-14): Nullbefund -- und er ist NICHT durch die Mechanik erklaert

`tools/night_v29_moon_order_ab.sh`, Fahrplan Nr. 28. Beide Seiten der amtierende Champion
v28-b02 auf demselben Wheel, unterschieden durch GENAU ein Spec-Feld (geprueft: 14 Felder je
Datei, ein Unterschied `moon_order_variants` 1 gegen 0). 200 Paare bis zum Deckel,
`--sprt-alpha/beta 0.001` (Wald-Schranken +-6,907), also kein Frueh-Stopp.

| | Fan-out AN | Fan-out AUS |
| --- | --- | --- |
| Siege | 193 | 207 |
| Punkte je Partie | 53,01 | **54,84** |

McNemar p = 0,5507, gepaarte Differenz -0,070 [-0,267, +0,127], Splits 99 von 200 Paaren
(47 A-Sweeps, 54 B-Sweeps). **Verdikt nach par.4: H1 NICHT bestaetigt, der Fan-out bleibt**
(Vollstaendigkeit, Nutzer-Praezedenz).

**Das Ergebnis ist gueltig, kein Henne-Ei:** der Fan-out ist Default AN, war bei der Erzeugung
aktiv, und der `moon`-Kopf ist mit `moon_order_targets` als PFLICHTFELD im Korpus trainiert
(`corpus_dataset.py:609`). Das Netz kennt die Groesse und hat einen gelernten Prior dafuer --
anders als beim Rueckgabe-Knopf (`PREREG_dome_return_order.md` par.10) ist die Frage hier
wirklich beantwortet.

**Was der Nullbefund NICHT ist: durch die Regel erklaert.** Die Gegenhypothese in H1 ("Mondsteine
werden ohnehin komplett gezogen") ist am 2026-09-14 als falsch nachgewiesen worden -- pro Stapel
wird nur der OBERSTE Stein genommen, die Reihenfolge ist Zugriffssteuerung (Korrektur in par.3,
Beleg `docs/engine_manual.md` Z.101-106 und `factory.rs:76/96-97`). Die Reihenfolge HAT also
Bedeutung, und trotzdem bringt ihre Auffaecherung nichts.

**Zwei Erklaerungen bleiben, beide ungeprueft:**

1. **Der Fan-out kostet mehr, als er bringt.** Bis zu sechs Kinder statt einem je Sonnenzug
   verteilen dasselbe Sim-Budget auf mehr Kandidaten. Dazu passt das Punktebild: 1,83 Punkte je
   Partie WENIGER mit Fan-out. Nicht signifikant, aber in der Richtung, die H1 als Kostenargument
   genannt hatte.
2. **Der Prior ist kurzsichtig** -- genau H2: das `moon_order_target` kommt aus dem Rundenloeser
   (Rundenende statt Partieausgang). Die Suche faechert dann zwar auf, aber entlang einer
   Rangfolge, die den Partieausgang nicht kennt.

**H2 ist damit NICHT erledigt**, obwohl H1 negativ ist: die Bindung "nur pruefbar nach H1" stand
auf der widerlegten Gegenhypothese (Nachtrag in par.3). Sie ist ein ZIELWECHSEL am bestehenden
Kopf, kein Neubau, und faellt damit nicht unter die Kopf-Sperre (`feedback_no_new_heads`).
Kosten nach par.5: ein Trainingsarm (rund 1,5 h) plus Gating. **Nutzer-Entscheid, nicht
eingetaktet.**

**Offen aus par.4:** die Diagnostik je Seite (Anteil der Sonnenzuege mit Rest >= 2, davon Anteil
mit nicht-kanonischer Wahl). Sie geht aus den `--log-games`-Artefakten dieses Laufs, ohne neue
Partien, und wuerde Erklaerung 1 von 2 trennen helfen.

**Laufzeit** 7.751 s Wanduhr bei 10 Threads. **NICHT als Kostenmass verwendbar:** auf der
Maschine lief waehrenddessen Nutzer-Nebenlast (Blockzeiten zwischen 129 s und 276 s). Die
Siegquote ist davon unberuehrt -- feste 400 Sims, feste Seeds, kein Zeitbudget.

## par.7a Ergebnisse (leer bis zur Messung)

Nichts gemessen (Stand 2026-09-12, 13:20).

## AGENTEN-AUFTRAG (Stand 2026-09-13, fuer eine autonome Abarbeitung durch einen Opus-Agenten)

### 1. Ziel und Verdikt-Regel

Zu beantworten ist, ob der Moon-Order-Fan-out der Netzsuche (seit 2026-07-01 immer aktiv, ohne
Knopf) ueberhaupt traegt. Die Verdikt-Regel steht in **par.4** (Stufe 1): A/B am amtierenden
Champion, beide Seiten gleiche Spec bis auf `moon_order_variants`, 200 Paare, Blockgroesse 5,
`--log-games`; **Lesart: Sieg und Punkte gepaart ueber der Aufloesung -> H1 bestaetigt; sonst
bleibt der Fan-out (Vollstaendigkeit, Nutzer-Praezedenz Rueckgabe-Reihenfolge), aber die
Zielfrage par.5 wird nicht weiterverfolgt.** Die Vorab-Erwartung steht in par.3: klein, weil der
Entscheid nur rund 20 Mal je Partie faellt (gemessen: 199 Ziele in einer Datei mit 10 Partien =
19,9 je Partie, Korpus `selfplay_v27-b01-policy_..._g10.pkl`, 199 von 1.675 Records); ein
Nullbefund bei 200 Paaren ist der wahrscheinliche Ausgang und dann ein vollwertiges Ergebnis.

### 2. Voraussetzungen

- **Der Knopf ist NICHT gebaut.** par.2 (Code geprueft 2026-09-12): `net_mcts.rs:1724-1920`
  legt bei einem SmallFactorySun-Knoten mit mindestens 2 Reststeinen ALLE eindeutigen
  Permutationen als Kinder an (`unique_moon_orders`), Prior = P(Basis) x P(Reihenfolge |
  Plackett-Luce ueber die 5 Farb-Scores des `moon_order_head`); **kein Knopf, immer aktiv.**
  Zu bauen ist `MOSAIC_MOON_ORDER_VARIANTS` / Spec-Feld `moon_order_variants` nach par.4.
- **Maschine frei laut Prozessliste** fuer Bau (Volllast) und Messung; exklusiv.
- **Eintaktung:** v29/v30-Begleitprogramm (par.4 und `PREREG_v29_window.md` par.7 Punkt 2d);
  Stufe 2 nur bei H1 positiv und dann in v30.
- **Spieler:** amtierender Champion mit seiner Spec (heute `v28-b02`,
  `models/frozen_champions/v28-b02/spec.json`).

### 3. Schritte

**P1 -- Bau des Knopfs (par.4)**

1. `MOSAIC_MOON_ORDER_VARIANTS`, **Default 1 = BESTAND, bitidentisch**; `0` = nur die kanonische
   Restreihenfolge wie im Heuristik-Pfad (`validation.rs:175-193`). Spec-Feld
   `moon_order_variants` **optional** (fehlt = 1), damit alle eingefrorenen Specs weiter laden
   (Muster `round_est_c`, `dead_cell_w`). Wirkort ist die Expansion in
   `engine/src/net_mcts.rs:1724-1920`; der Aktionsraum bleibt bei 406 Aktionen (par.6), der
   Heuristik-Pfad bleibt unberuehrt (kein Fan-out fuer den Anker). Registratur-Eintrag in
   `engine/src/knob_registry.rs`, `engine_config`, Spec-Abbildung in `server.py` und
   `tools/claude_play.py`, mindestens ein Test (bei `variants=0` entsteht genau ein Kind je
   Sonnenzug; bei `variants=1` bitidentisch zum Bestand). Bezeichner englisch (CLAUDE.md).
2. **Tore, Reihenfolge Bau -> Tore -> Messung** (Muster `tools/night_v28_knob_build.sh`,
   gemessene Dauern 84 s / 33 s / 34 s / 19 s / 12 s):

   ```
   $env:PATH = "$(python -c 'import sys,os;print(os.path.dirname(sys.executable))');" + $env:PATH
   cd engine; cargo test --release --lib
   cargo test --release --no-run
   python -m maturin build --release
   python -m pip install --force-reinstall --no-deps engine/target/wheels/mosaic_rust-0.1.0-cp314-cp314-win_amd64.whl
   python -X utf8 -u tools/verify_frozen_heuristic.py --artifact-dir models/frozen_heuristics/hv4_anchor --out evaluations/artifacts/anchor_drift_live_wheel_<datum>_moon.json
   python -X utf8 -u tools/verify_frozen_heuristic.py --artifact-dir models/frozen_heuristics/hv4_anchor --venv --out evaluations/artifacts/anchor_conservation_artifact_wheel_<datum>_moon.json
   python -X utf8 tools/generate_knob_docs.py
   python -X utf8 tools/check_conventions.py
   ```

   **Netz-Paritaets-Fixture des Champions muss bei Default UNVERAENDERT bleiben**; Anker-Drift
   gruen (die Heuristik hat keinen Fan-out). Kosten: rund eine Stunde Bau plus 6 min Tore
   (ANNAHME; die Tore selbst sind gemessen).
   **Bei Abbruch:** `os error 32` = OneDrive-Dateisperre, wiederholen; `STATUS_DLL_NOT_FOUND` =
   Python-DLL fehlt im PATH.

**P2 -- Stufe 1: A/B Fan-out an gegen aus (par.4)**

3. Zwei Spec-Dateien, die sich NUR in `moon_order_variants` unterscheiden (1 gegen 0), sonst
   identisch mit der Champion-Spec. Dann:

   ```
   python -X utf8 -u tools/paired_gating.py \
     --model-a models/alphazero_v28-b02_brierbest.onnx --spec-a models/moon_variants_on.spec.json \
     --model-b models/alphazero_v28-b02_brierbest.onnx --spec-b models/moon_variants_off.spec.json \
     --name-a v28-b02_moon_on --name-b v28-b02_moon_off --sims-a 400 --sims-b 400 --c-puct 1.5 \
     --block-size 5 --max-pairs 200 --sprt-alpha 1e-12 --sprt-beta 1e-12 \
     --seed <SEED> --threads 10 --log-games --no-promote-winner \
     --out evaluations/artifacts/moon_order_ab_on_vs_off_s<SEED>.json
   ```

   Frueh-Stopp AUS, weil ein Nullbefund hier ein vollwertiges Ergebnis ist und ein frueh
   gestoppter Lauf die Quote verzerrt. **Dauer (gemessen):** 200 Paare @400 mit Logs
   5.182-5.446 s = 86-91 min (`docs/measured_runtimes.md`).
   **Bei Abbruch:** mit demselben Seed wiederholen; Teil-Laeufe nicht mit vollen poolen.
4. **Zusatzkennzahlen je Seite, aus den Logs** (par.4, `#a`-Zeile traegt `moon_order`): Anteil
   der Sonnenzuege mit Rest >= 2 und, davon, der Anteil, in dem die gewaehlte Reihenfolge NICHT
   die kanonische ist. Erwartungsgroesse aus par.2: rund 20 Entscheide je Partie.
5. Sechs Standard-Kennzahlen (CLAUDE.md) aus denselben Logs:
   `python -X utf8 -u tools/probes/arena_column_probe.py --artifact <ART>` und
   `python -X utf8 -u tools/plate_points_from_arena.py <ART> --block 5`.

**P3 -- Stufe 2 (nur bei H1 positiv, v30)**

6. Ein Trainingsarm mit SUCHZIEL statt Rundenloeser-Ziel: der Record traegt die vom Baum
   gewaehlte Reihenfolge (`policy_target_valid`-Muster), Tor 1 gegen den Vorgaenger;
   Orakel-Metriken sind hier ohne Aussage (die Bruecke kennt die Reihenfolge nicht). Kosten:
   ein Trainingsarm rund 1,5 h plus Gating (par.5). **Nur nach H1 und nur mit Nutzer-Freigabe.**
   Vorher ist `moon_order_target` (`self_play.rs:1052ff`, beste Reihenfolge nach
   `solve_round_final_score` ueber alle Permutationen, bei hoechstens 3 Steinen also
   erschoepfend) NICHT zu aendern (par.6).

### 4. Auswertung und Registrierung

- **Zahlen mit n, Grundmenge, Einheit**: A/B "n = 400 Partien (200 Paare), Grundmenge gepaarte
  Arena-Partien desselben Netzes mit gegen ohne Fan-out, Einheit Siege"; Haeufigkeit "n =
  Sonnenzuege mit Rest >= 2, Grundmenge Sonnenzuege aus kleinen Fabriken, Einheit Entscheide je
  Partie"; Abweichungsrate "Grundmenge Entscheide mit Rest >= 2, Einheit Anteil nicht-kanonisch".
  Auswertung auf Block-Ebene (Blockgroesse 5).
- **Die sechs Standard-Kennzahlen** je Seite und als Differenz (CLAUDE.md).
- **Registrierung in par.7** dieser Datei, **Zeile-1-Kopf im selben Zug** nachziehen, danach
  sofort `python tools/generate_prereg_index.py`.
- **STATUS.md Abschnitt 1 und Abschnitt 6 (Punkt 00c)** sowie `archive/history.md` fortschreiben.
- **Rueckwaerts-Pruefung**:
  `grep -rn "moon_order\|MOON_ORDER\|moon_loss_weight" evaluations/ docs/ tools/ engine/`
  -- betroffen sind mindestens `PREREG_dome_return_order.md` par.2/par.7 (dort steht die bereits
  eingetragene Korrektur), `PREREG_stack_top_feature.md` par.10 P.8,
  `PREREG_implementation_review_unprimed.md` (Befund `moon_order_target` als No-Op, behoben,
  Knopf `train.py --moon-loss-weight`), `docs/knobs.md`.
- **Laufzeit-Zeilen** in `docs/measured_runtimes.md` (Bau-Tore, A/B-Lauf mit Threads 10).
- **Elo-Register: NICHTS** fuer den A/B (gleiches Netz mit gegen ohne Knopf ist keine Kante am
  Champion). Wird `variants=0` Default, ist das eine neue gemessene Identitaet
  (Feedback `measured_identity_gets_own_bxx`) und braucht einen eigenen Knotennamen.

### 5. Stopp-Punkte fuer den Nutzer

- **Aufnahme ins Rezept** (Fan-out aus- oder anlassen) entscheidet der Nutzer; par.4 legt fest,
  dass der Fan-out bei Nullbefund BLEIBT.
- **Stufe 2 (Zielwechsel des Kopfs)** ist ein Trainingsarm und braucht eine ausdrueckliche
  Freigabe; sie kommt fruehestens mit v30 (`PREREG_v29_window.md` par.8 Punkt 3: v30 bekommt nur
  noch Rezept-Knoepfe, keine neuen Bauvorhaben -- ein Zielwechsel ist ein Bauvorhaben und
  braucht deshalb eine eigene Entscheidung). **Nutzer fragen.**
- **Anker-Drift ROT oder Paritaets-Fixture veraendert: anhalten**, Nutzer-Entscheid.
- **Keine Erweiterung des Aktionsraums** (par.6: 406 bleibt), kein Fan-out im Heuristik-Pfad.
- **Kein Push, keine Loeschung** ohne Freigabe.

### 6. Abhaengigkeiten und Reihenfolge

**Vorher:** ein freies CPU-Fenster in v29; der Bau ist ein Wheel-Wechsel und darf NICHT waehrend
Erzeugung, Waechter oder Kette laufen (`PREREG_v29_window.md` par.4 Punkt 6). Innerhalb des
Begleitprogramms steht dieser Punkt als par.7 Punkt 2d nach der Ziehsucht-Sonde und vor dem
Tiling-Umbau (`PREREG_round_transition_search_sampling.md` par.9 nennt die Reihenfolge
ausdruecklich: "nach Ziehsucht-Sonde und Mondstapel-Stufe 1, weil die beiden billiger sind").
**Danach:** bei H1 positiv Stufe 2 in v30; sonst ist der Strang mit dem Nullbefund abgeschlossen
und die Prereg kann auf ENTSCHIEDEN.

## par.8 BAUSTAND 2026-09-14 (gebaut, kompiliert, im Wheel)

Knopf `moon_order_variants` (Spec optional mit Default **1**, Env `MOSAIC_MOON_ORDER_VARIANTS`,
Werte 0/1) nach par.4 gebaut. **Wirkort** `net_mcts.rs::build_untried_actions` (neuer Parameter),
verdrahtet ueber `SearchConfig` in `node_from_net_outputs` -- damit in beiden Netz-Arenen,
Netz-Self-Play, Referee (in-process und Worker ueber `resolve_search_config`) und GUI. Beruehrt:
`net_mcts.rs` (Env-Leser, Spec-Feld, `KNOWN_FIELDS`, Fan-out-Zweig, Testhelfer, vier Tests),
`lib.rs` (`engine_config`), `knob_registry.rs`, `engine/examples/kernbeweis_910002_probe.rs`
(Struct-Literal), `server.py` und `tools/claude_play.py` (Spec-Abbildung). Aktionsraum bleibt
406, Heuristik-Pfad unberuehrt.

**Die Zeilennummern in par.2 waren veraltet.** Der Fan-out sitzt in `net_mcts.rs:2241-2255`
(Bedingung `source == SmallFactorySun && moon_order.len() >= 2`, dann `unique_moon_orders` x
`plackett_luce_prob`), nicht bei 1724-1920. Die kanonische Reihenfolge kommt aus
`game::drafting_actions` -> `validation.rs:170-193`; bei `variants=0` wird der Zweig nicht
betreten und die Aktion faellt in den 1:1-Pfad.

**ZWEI BAU-ENTSCHEIDE UEBER par.4 HINAUS, beide bewusst:**

1. **Der Knopf wirkt NICHT in den TD-Bootstrap-Rollouts.** `drafting_action_priors`
   (`net_mcts.rs:2713`) bleibt hart auf Fan-out, weil die Rollouts
   (`round_transition_deep::continue_through_round{2,3,4}`) keine `SearchConfig` mitfuehren
   (geprueft: kein `SearchConfig` in `round_transition_deep.rs`). Fuer das A/B am Champion ist
   das folgenlos -- dort entstehen keine Labels. **Wuerde je ein KORPUS mit Modus 0 erzeugt,
   waere der Knopf dort unvollstaendig**; das ist vor einer solchen Erzeugung zu klaeren.
2. **Umgekehrte Polung:** anders als bei allen Nachbar-Knoepfen ist der Bestand der
   EINgeschaltete Zustand. Im Testhelfer `search_config_off()` steht deshalb `1`, nicht `0` --
   das bricht die dortige Lesart "alles aus" und ist im Code kommentiert.

**Bau-Tor 2026-09-14 GRUEN** (zusammen mit der Phasen-Korrektur unten): `cargo test --release
--lib` **646 gruen** (0 rot, darunter die vier neuen Knopf-Tests und die Netz-Paritaets-Fixture
UNVERAENDERT), `cargo test --release --no-run` deckt examples/benches ab (keine E0063),
Wheel gebaut und installiert, **Kontrakt-Hash UNVERAENDERT 39994362fba145a6** (er bildet nur
INPUT_SIZE, Planes-Geometrie, NUM_ACTIONS und die Kopf-Liste ab, `lib.rs:684-700` --
`engine_config_json` geht nicht ein), `docs/knobs.md` neu generiert (122 Knoepfe),
Konventions-Check gruen, **Anker-Drift GRUEN und Konservierung GRUEN** gegen `hv4_anchor`
(Artefakte `anchor_drift_live_wheel_20260914_moon_phase.json` und
`anchor_conservation_artifact_wheel_20260914_moon_phase.json`).

**Offen: das A/B** (Fahrplan Nr. 28) -- Fan-out an gegen aus am Champion, 200 Paare,
Blockgroesse 5, `--log-games`, plus Abweichungsrate je Seite nach par.4.

## par.9 STUFE 3: eigene Nachsuche fuer die Reihenfolge (Nutzer-Auftrag 2026-09-14, VOR dem Bau)

Nutzer woertlich: *"dann modellier es korrekt: sobald von der sonnenseite gezogen wird brauchen
wir eine zusaetzliche suche fuer die mond reihenfolge. damit wir in den naechsten halbzug
hineinschauen koennen. sonst verschwendest simulationen fuer wenig wissen."*

### Warum der Bestand die falsche Form ist

`moon_order` ist heute Teil der Zugaktion (`TakeAction::moon_order`, `execution.rs:154`), und
der Fan-out macht daraus bis zu sechs VERSCHIEDENE ZUEGE an derselben Stelle. Die konkurrieren
im selben Kandidatenfeld wie inhaltlich andere Zuege; an der Wurzel rangt Gumbel daraus nur
`gumbel_top_m_for_budget(sims)` = 16 bei @400 (`net_mcts.rs:4852`), und der Prior wird auf die
Varianten VERTEILT (`base_p * p/pl_sum`, :2255), die Verteilung also flacher -- der
Masse-Cutoff `POLICY_MASS_CUTOFF = 0.95` (:2280-2289) behaelt danach mehr Kandidaten mit je
weniger Gewicht.

**Sachlich ist der Stapelaufbau aber ein FOLGESCHRITT, kein Alternativzug** (Nutzer-Einwand
2026-09-14: "wenn ich mich entscheide von der sonnenseite zu ziehen, ist der aufbau des
mondstapels ein davon unabhaengiger schritt"). Die Kopplung ist eine Folge der Modellierung.
Dazu passt das gemessene Bild aus par.7: der Fan-out wirkt oft (99 von 200 Paaren entschieden)
und traegt trotzdem nichts, bei 1,83 Punkten je Partie WENIGER.

### Bauform Stufe 3 (registriert VOR dem Bau)

**Dritter Wert des vorhandenen Knopfs**, `MOSAIC_MOON_ORDER_VARIANTS=2`: kein Fan-out im
Suchbaum (die Zugauswahl sieht genau EINEN Kandidaten je Zugidee, wie bei Wert 0), und NACH der
Zugwahl entscheidet eine eigene, kleine Suche ueber die Reihenfolge.

* **Wann:** nur bei einem `SmallFactorySun`-Zug mit mindestens zwei Reststeinen -- dieselbe
  Bedingung wie der Fan-out heute (`net_mcts.rs:2241-2255`).
* **Worueber:** die eindeutigen Permutationen aus `unique_moon_orders` (:2080), unveraendert.
* **Wie tief:** je Variante eine Suche ueber den FOLGEZUSTAND, in dem der GEGNER am Zug ist --
  genau der Halbzug, in dem sich die Reihenfolge auswirkt, weil pro Stapel nur der oberste Stein
  ziehbar ist (`docs/engine_manual.md` Z.101-106, `factory.rs:76/96-97`). Eine reine
  Blattbewertung reicht dafuer NICHT: sie sieht nicht, was der Gegner mit dem obersten Stein
  macht. Das unterscheidet Stufe 3 von `dome_return_order` Modus 1, der genau daran scheitert
  (dort par.10).
* **Budget:** eigener Knopf `MOSAIC_MOON_ORDER_SEARCH_SIMS`. Das Budget kommt NICHT aus dem
  Wurzelbudget -- das ist der Kern des Auftrags. **Nutzer-Praezisierung 2026-09-14:** *"dann
  kannst eine normale suche machen mit 400 sims im ersten schritt. dann eine nachgelagerte fuer
  die sonnenfelder."* Die erste Suche behaelt also ihr volles, unveraendertes Budget; die
  Nachsuche kommt OBENDRAUF, sie wird nicht davon abgezweigt.
* **Die Mehrkosten sind bekannt und akzeptiert.** Nutzer dazu: *"das dauert dann evtl. etwas
  laenger ist. aber sauberer meiner meinung nach."* Das Argument ist die KORREKTHEIT der
  Modellierung, nicht Elo (CLAUDE.md "Correctness over measured benefit", Praezedenz
  `feedback_correctness_over_measured_benefit`). **Folge fuer das Kostentor unten:** es ist eine
  MESSUNG, kein Veto -- ein gerissenes Tor beendet den Arm hier NICHT automatisch, sondern ist
  ein Nutzer-Entscheid. Entsprechend wird die Nachsuche nicht auf Sparsamkeit optimiert, wenn das
  ihren Zweck verfehlen wuerde (in den naechsten Halbzug hineinsehen).
* **Prior:** der vorhandene `moon`-Kopf ordnet die Varianten vor (Plackett-Luce wie heute), damit
  bei knappem Budget die aussichtsreichsten zuerst drankommen. **Kein neuer Kopf**
  (`feedback_no_new_heads`), kein neues Trainingsziel, keine Aktionsraum-Erweiterung (par.6).
* **Default bleibt 1** (Bestand, bitidentisch), bis ein A/B etwas anderes sagt.

### Was das misst, das die bisherigen Stufen nicht messen konnten

Stufe 1 hat Fan-out gegen kanonisch gemessen und dabei ZWEI Dinge vermischt: den Wert der
Reihenfolge und die Kosten der Kandidatenkonkurrenz. Stufe 3 trennt sie: die Zugauswahl ist
identisch zu Wert 0, der einzige Unterschied ist die Nachsuche. **Ein A/B 2 gegen 0 misst damit
den Wert der Reihenfolge allein**, ohne Verdraengung im Wurzelfenster.

### Tore

Default 1 bitidentisch (Tests, Netz-Paritaets-Fixture, Anker-Drift), Kostentor vor dem A/B
(die Nachsuche kostet Varianten x Sims je Sonnenzug mit Rest >= 2; wie oft das vorkommt, sagt
die noch offene par.4-Diagnostik aus den Logs von Nr. 28), dann A/B 2 gegen 0 am Champion,
200 Paare, Blockgroesse 5, ohne Frueh-Stopp.

