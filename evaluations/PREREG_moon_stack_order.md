<!-- STATUS: OFFEN | Frage: Die Reihenfolge der Mondsteine nach einem Sonnenzug ist im Netzpfad ein Suchentscheid -- traegt das, und ist das Trainingsziel des Kopfs das richtige? | Beleg: Stufe 1 (par.7) und Stufe 3 (par.9h) BEIDE Nullbefund. **par.12.0: das Trainingsziel des moon-Kopfs ist ein No-Op** (das Label ist immer kanonisch). **par.12.5: b05 (Kopf ablatiert) ist BESSER als b03** -- 427:373 aus 800 Partien, gepoolt z=1,98, beide Seeds gleichgerichtet, einzeln nicht signifikant. **par.12.3a: die Folgerung "Zugriffs-Hebel klein" ist ZURUECKGENOMMEN** -- ein Mondzug nimmt ALLE Oberseiten einer Farbe, 43,8 Prozent raeumen mehrere Steine ab; die Hebelgroesse ist offen. Offen auch b04 (Korpus-Tor 44,1 Prozent) und ein dritter Seed fuer b05. -->

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

  **KORREKTUR 2026-09-15 (par.12.0, am Code geprueft):** die Aufzaehlung ist erschoepfend, der
  Bewerter ist blind. `solve_round_final_score` liest nur `players[pi]`
  (`tiling_solver.rs:396-404`, Modulkopf `:249`), die Mondreihenfolge lebt in
  `state.factories`; alle Permutationen scoren gleich, und weil `permutations()` mit der
  Identitaet beginnt, ist das Label IMMER die kanonische Reihenfolge. Der Kopf trainiert seit
  jeher auf die Sonnenseiten-Folge, nicht auf ein Rundenziel.
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

### Reihenfolge: erst messen, dann optimieren (Nutzer 2026-09-14)

Nutzer: *"ich denk mal das ist keine optimierte variante. und es wurde auch noch nicht gemessen
was es bringt."* Das ist die Leitlinie fuer Stufe 3 und trennt zwei Kostenfragen, die der
Koordinator zunaechst vermengt hatte:

* **Fuer das A/B sind die Kosten nachrangig.** 200 Paare dauern mit voller Nachsuche statt rund
  90 vielleicht 180 Minuten -- einmalig. Gemessen wird damit, was die saubere Modellierung
  HERGIBT, nicht was eine sparsame Variante davon uebriglaesst. Das Budget bleibt deshalb bei
  256 je Variante (Begruendung: `gumbel_top_m_for_budget(256) = 16`, dieselbe Wurzelbreite wie
  die erste Suche im Betrieb bei @400).
* **Optimiert wird erst, wenn der Nutzen belegt ist.** Dann geht es um die ERZEUGUNG, wo eine
  Verdopplung der Laufzeit die relevante Zahl waere. Moegliche Hebel, bewusst NICHT jetzt gebaut:
  Varianten nach Prior abschneiden statt alle zu bewerten, Budget je Variante senken, die
  Nachsuche auf Stellen mit unsicherem Prior beschraenken.

**Das Kostentor bleibt damit eine Messung** (par.9 oben) und ist kein Grund, den Bau vorher
schlank zu machen.

### Tore

Default 1 bitidentisch (Tests, Netz-Paritaets-Fixture, Anker-Drift), Kostentor vor dem A/B
(die Nachsuche kostet Varianten x Sims je Sonnenzug mit Rest >= 2; wie oft das vorkommt, sagt
die noch offene par.4-Diagnostik aus den Logs von Nr. 28), dann A/B 2 gegen 0 am Champion,
200 Paare, Blockgroesse 5, ohne Frueh-Stopp.

## par.9a BAUSTAND Stufe 3 (2026-09-14, gebaut, kompiliert, im Wheel)

`MOSAIC_MOON_ORDER_VARIANTS=2` plus Budget-Knopf `MOSAIC_MOON_ORDER_SEARCH_SIMS` (Default **256**).

**Wirkung.** Bei Wert 2 faechert die Zugauswahl NICHT auf: die Fan-out-Bedingung heisst jetzt
`== MOON_ORDER_VARIANTS_DEFAULT` statt `!= 0` (`net_mcts.rs:2362`), Wert 2 faellt damit in
denselben 1:1-Pfad wie Wert 0. Nach der Zugwahl laeuft `moon_order_post_search`
(`net_mcts.rs:5650`) mit dem reinen Kern `choose_moon_order_with` (:5533) und dem Tor
`moon_order_post_search_applies` (:5609). Vier Einhaengungen, alle NACH der Zugwahl und nie im
Baum: `net_search_drafting_action` (Einzelbaum und ISMCTS-Wald), `..._hybrid`,
`net_search_with_tree_inner` (GUI/Debug) und `self_play.rs::net_drafting_policy`.

**Das Tor ist eine eigene reine Funktion**, damit die Bitidentitaets-Zusage ohne Netz pruefbar
ist: `true` nur bei Wert 2 UND Budget > 0 UND `SmallFactorySun` mit Rest >= 2 UND mindestens
zwei eindeutigen Reihenfolgen. Sonst kommt die Aktion unveraendert zurueck -- kein Netzaufruf,
keine Zustandskopie, **keine Zufallszahl** (die Ziehung steht hinter dem Tor).

**Bewertung.** Wiederverwendet wird `build_net_tree` (`net_mcts.rs:5279`), kein zweiter
Suchtreiber. Folgezustand je Variante: Kopie plus `apply_drafting`, danach ist laut
`game.rs:786-788` der GEGNER am Zug -- genau der Halbzug, um den es geht. Kennzahl ist
`v_mix` an der Wurzel (:3632), gewaehlt wird das Minimum. Dieses Mischen ist der Unterschied zur
reinen Blattbewertung, an der `dome_return_order` Modus 1 scheitert.

**Sim-Default 256, am Zweck begruendet:** `gumbel_top_m_for_budget(256)` = 16, also genau die
Wurzelbreite, die die erste Suche bei @400 bekommt (`clamp(round(400/16), 4, 16)` = 16). 256 ist
der kleinste Wert mit dieser Eigenschaft; 128 gaebe m=8, 64 gaebe m=4 -- die Antwort des Gegners
waere dann auf einem engeren Kandidatenfeld bewertet als die Stellung, aus der sie kommt.

**ABER DAS GILT NUR FUER @400, NICHT FUER DIE ERZEUGUNG** (Nutzer-Hinweis 2026-09-14: *"fuer die
self plays haben wir sowieso ein anderes thema. hier sind die 100 sims die staerkste variante"*).
Die Erzeugung faehrt 100 Sims (`project_search_depth_column_tradeoff`: 25-100 bauen rund 0,6
volle Spalten gegen 0,34 ab 250). Dort ist die Wurzelbreite `clamp(round(100/16), 4, 16)` = **6**,
und ein Nachsuch-Budget von 256 gaebe der Nachsuche fast die dreifache Breite der Hauptsuche, die
sie bewerten soll. Die Kosten waeren entsprechend: bei rund 8.000 Sims je Partie im Betrieb
stuenden bis zu 30.600 Zusatz-Sims dagegen -- das VIERFACHE, nicht eine Verdopplung.

**Folge:** das Budget ist ein Spec-Feld und wird je Kontext gesetzt.

| Kontext | Hauptsuche | Wurzelbreite | passendes Nachsuch-Budget |
| --- | --- | --- | --- |
| Arena, Gating, das A/B von Stufe 3 | 400 | 16 | **256** (Default) |
| Erzeugung | 100 | 6 | **rund 96** |

Der Koordinator hatte 256 zunaechst pauschal begruendet; die Zahl stammt aus dem Arena-Kontext
und war fuer die Erzeugung nie geprueft. Das ist dieselbe Fehlerklasse wie in CLAUDE.md Regel 0
Zusatz 2: eine Zahl aus einer Grundmenge in einen Verbraucher mit anderer Grundmenge getragen.

**Determinismus:** genau EINE Zahl aus dem Suchstrom, daraus je Variante
`derive_search_seed(base ^ MOON_ORDER_SEARCH_SEED_DISTINGUISHER, rang)` (:5486). Der Hauptstrom
verschiebt sich um genau einen Zug, unabhaengig vom Verbrauch der Nachsuche.

**BAU-TOR GRUEN:** `cargo test --release --lib` **659 gruen** (0 rot; darunter fuenf neue Tests
und die **unveraenderte Netz-Paritaets-Fixture** -- sie faehrt mit `SearchConfig::from_env()`,
Default 1, das Tor bleibt zu), `--no-run` deckt examples und benches ab (keine E0063),
Wheel gebaut und installiert, **Kontrakt-Hash UNVERAENDERT 39994362fba145a6** (am laufenden Wheel
gegengeprueft, das `moon_order_search_sims: 256` fuehrt), `docs/knobs.md` neu (124 Knoepfe),
Konventions-Check gruen, **Anker-Drift und Konservierung GRUEN**.

**EIN BUG IM TESTHELFER, gefunden und behoben:** `state_with_multi_order_sun_move` setzte die
Startkuppeln stur von Spieler 0 aufwaerts und verschluckte den Fehler mit `let _ =`. Die
Startsetzung hat aber eine Reihenfolgeregel -- der Nicht-Startspieler legt zuerst
(`game.rs:586-589`). War Spieler 0 der Startspieler, blieb `start_tile_pending` stehen, der Seed
wurde verworfen, und nach 64 Versuchen meldete der Helfer "64 Startaufbauten ohne mehrdeutigen
Sonnenzug -- das waere ein Befund, kein Zufall". **Es war kein Befund ueber das Spiel, sondern
ein Bug im Helfer**; behoben mit zwei Durchlaeufen. Drei Tests waren dadurch rot.

### Offene Entscheide aus dem Bau (Nutzer)

1. **Aufzeichnendes Self-Play ist mitverdrahtet** (`net_drafting_policy`): ein Modus-2-Korpus
   traegt damit die nachgesuchte Reihenfolge, sonst haette er dieselbe Luecke wie die
   TD-Bootstrap-Rollouts. Aendert die gespielte Trajektorie eines solchen Korpus; ruecknehmbar an
   einer Aufrufstelle.
2. **Keine verschachtelte Nachsuche:** im Unterbaum spielt der Gegner seine eigenen Sonnenzuege
   kanonisch (sonst unbegrenzte Rekursion). Die Nachsuche bewertet den Gegnerzug also unter der
   Annahme, dass der Gegner selbst nicht nachsucht.
3. **TD-Bootstrap-Rollouts** bleiben wie in par.8 hart auf Fan-out -- bei Modus 2 ist der Knopf
   dort weiterhin unvollstaendig.
4. **Zwei Umgehungen in `net_arena_choose_action`** (genau eine legale Aktion, Bauer-Vorzug)
   ueberspringen die Suche und damit auch die Nachsuche.
5. **par.2s Haeufigkeitszahl passt nicht auf den Verbraucher:** dort stehen "19,9 Sonnenzuege mit
   Rest >= 2 je Partie", im Code entsteht das Ziel aber schon bei Rest >= 1
   (`self_play.rs:1296`). Die Zahl ist damit eine LOSE OBERE Schranke fuer das Tor der Nachsuche
   (Rest >= 2 UND >= 2 eindeutige Reihenfolgen) und darf so nicht ins Kostentor. Die scharfe Zahl
   liefert die offene par.4-Diagnostik aus den Logs von Nr. 28.

## par.9b DIAGNOSTIK GEMESSEN (par.4 Punkt 2) und: KEINE Nachsuche im Self-Play

**Gemessen 2026-09-14 aus ALLEN `--log-games`-Artefakten im Baum** (125 Dateien, **12.907
Partien**, 637.304 Mondstapel-Ereignisse), ohne neue Partien:

| Steine im Stapel | eindeutige Reihenfolgen | Faelle je Partie | Zusatz-Sims @256 |
| --- | --- | --- | --- |
| 2 | 1 (zwei gleiche) | 4,39 | 0 (Tor zu) |
| 2 | 2 | **14,02** | 512 |
| 3 | 1 (drei gleiche) | 0,76 | 0 (Tor zu) |
| 3 | 3 (zwei gleiche) | **6,09** | 768 |
| 3 | 6 (drei verschiedene) | **4,23** | 1.536 |

**Echte Wahl (mindestens zwei eindeutige Reihenfolgen): 24,34 je Partie.**
**Zusatz-Sims je Partie bei Budget 256: rund 18.350.**

> **UEBERHOLT 2026-09-15 (par.9i): beide Zahlen sind rund doppelt so hoch wie die Wirklichkeit.**
> Sie stammen aus den Spiel-Logs, und die Zeile `🌙 Fx Mond-Stapel: ...` ist eine
> ZUSTANDSANZEIGE aller Stapel einer Fabrik (`format_moon_stacks`), keine Ereignisliste --
> derselbe Stapel wird bei jedem weiteren Zug aus derselben Fabrik erneut gelistet. Der Zaehler
> IM CODE sagt **12,20 Entscheidungen je Partie** und rund **9.200** Zusatz-Sims. Die Tabelle
> unten bleibt als Beleg fuer die VERTEILUNG der Stapelgroessen gueltig; ihre absoluten Raten je
> Partie sind es nicht.

**KORREKTUR EINES ZAEHLFEHLERS (Nutzer 2026-09-14: "kann ich mir dennoch nicht vorstellen. dass
wir nie einen dreier stapel hatten").** Eine erste Auswertung meldete "in 400 Partien nie ein
Stapel groesser als zwei" und hielt das fuer einen Befund ueber das Spiel. **Es war ein
Parsing-Fehler.** Das Logformat trennt den Rest mit KOMMA und nur den obersten Stein mit Pfeil
(`execution.rs:116-118`: `format!("({}->{})", rest.join(", "), top.value())`); ein Dreierstapel
steht also als `(blau, rot->gelb)` im Log. Der Regex hat nur am Pfeil getrennt und daraus zwei
Steine gemacht. Korrekt gezaehlt sind es **142.945 Dreierstapel**, also 22,4 Prozent aller
Ereignisse. Die kleinen Fabriken tragen vier Steine (Nutzer-Auskunft), ein Dreierstapel entsteht
also immer dann, wenn nur EIN Stein der gewaehlten Farbe genommen wird -- haeufig, nicht selten.

**Lehre:** die erste Zahl kam aus EINEM Artefakt mit einer Seed-Basis und wurde nicht gegen das
Log-FORMAT geprueft, nur gegen die eigene Erwartung. Die Nutzer-Rueckfrage nach der Partienzahl
hat den Fehler aufgedeckt.

**Damit ist par.2s Zahl ersetzt.** Dort standen "19,9 Ziele je Partie", gemessen mit der
Grundmenge Rest >= 1 (`self_play.rs:1296`); der Verbraucher (das Tor der Nachsuche) verlangt
mindestens zwei eindeutige Reihenfolgen. Die damals ermittelte Zahl war **24,34 je Partie**
(seit par.9i als Ueberzaehlung erkannt, richtig sind 12,20), Grundmenge
Mondstapel-Ereignisse mit echter Wahlmoeglichkeit, Einheit Ereignisse, n = 12.907 Partien.

**Erwartete Mehrkosten:** rund **18.350 Zusatz-Sims je Partie** bei Budget 256. Gegen rund
32.000 bei @400 sind das **+57 Prozent**; gegen rund 8.000 bei @100 waeren es mehr als das
Doppelte -- was den Nutzer-Entscheid unten (keine Nachsuche im Self-Play) zusaetzlich stuetzt.

### Nutzer-Entscheid 2026-09-14: im Self-Play laeuft KEINE Nachsuche

Woertlich: *"vielleicht machen wir fuer das self play ueberhaupt keine nachsuche. dort kann es
ruhig divers spielen."*

Das loest die teure Haelfte -- und nicht nur aus Kostengruenden: die Erzeugung soll VIELFALT
liefern, nicht optimal spielen. Eine Nachsuche, die dort die beste Reihenfolge erzwingt, verengt
den Zustandsraum genau an der Stelle, an der die Rueckgabe-Streuung
(`PREREG_dome_return_order.md` par.11) gerade Varianz hinzufuegt.

**Kein Umbau noetig:** der Knopf ist ein Spec-Feld. Die Erzeugung faehrt ihre eigene Spec und
setzt `moon_order_variants` schlicht nicht auf 2. Die Verdrahtung in `net_drafting_policy`
(par.9a, offener Entscheid 1) bleibt bestehen, liegt aber brach, solange keine Erzeugungs-Spec
Modus 2 anfordert. Damit ist auch die Frage nach einem eigenen Erzeugungs-Budget (rund 96 statt
256) gegenstandslos, solange dieser Entscheid gilt.

**Stufe 3 ist damit ein reiner ARENA-Knopf**: Wirkung in Arena, Gating und Referee, nicht in der
Korpus-Erzeugung.

## par.9c LESERICHTUNG des A/B vom 2026-09-14 (Nachtkette)

`tools/night_v29_20260914.sh`, Schritt 1, Artefakt
`moon_order_post_vs_off_s20261091.json`. **Die Seitennamen im Artefakt sind
nichtssagend (`..._a` / `..._b`) -- hier die Zuordnung, damit sie beim Auswerten nicht aus dem
Skript rekonstruiert werden muss:**

| Seite | Spec | `moon_order_variants` | bedeutet |
| --- | --- | --- | --- |
| **a** | `models/moon_order_post2.spec.json` | **2** | Nachsuche nach der Zugwahl (Stufe 3) |
| **b** | `models/moon_order_off0.spec.json` | **0** | kanonische Reihenfolge, kein Fan-out |

**Gewinnt a, traegt die Nachsuche.** Beide Seiten fahren dasselbe Modell
(`alphazero_v28-b02_brierbest.onnx`) auf demselben Wheel; die Specs unterscheiden sich in genau
einem Feld (vor dem Start geprueft).

**Warum nicht gegen Wert 1 (den Fan-out) gemessen wird:** Stufe 1 hat bereits gezeigt, dass der
Fan-out gegen kanonisch nichts traegt (par.7). Die offene Frage ist, ob die REIHENFOLGE etwas
wert ist, wenn man sie ohne Kandidatenkonkurrenz entscheidet -- und die Referenz dafuer ist die
kanonische Reihenfolge, nicht der bereits verworfene Fan-out.

## par.9d LESART VORAB (Nutzer 2026-09-14, VOR dem Ergebnis von Schritt 1)

Nutzer woertlich: *"spannend wuerd ich es finden wenn a nicht besser ist als b beim moon order
post. dann haut irgendwas von der implementierung noch nicht hin. weil dadurch kann ich recht
gezielt steuern wann ich und wann mein gegner etwas bekommt. das sollte nicht nur durch eine
'einfache' permutation abgehandelt werden koennen."*

**Das dreht die Lesart des Nullbefunds um.** Bei Stufe 1 (par.7) war ein Nullbefund vorab als
wahrscheinlicher Ausgang und als vollwertiges Ergebnis registriert. Hier NICHT: der Nutzer
erwartet einen Effekt, weil die Reihenfolge eine ZUGRIFFSSTEUERUNG ist -- wer bestimmt, welche
Farbe obenauf liegt, bestimmt mit, was der Gegner im naechsten Halbzug ueberhaupt nehmen kann
(pro Stapel ist nur der oberste Stein ziehbar, `docs/engine_manual.md` Z.101-106,
`factory.rs:76/96-97`). Das ist Steuerung, nicht Kosmetik.

**Bleibt a gleichauf oder schlechter als b, ist das ein IMPLEMENTIERUNGS-Verdacht, kein
Verdikt.** Dann sind vor jeder inhaltlichen Deutung diese Stellen zu pruefen:

1. **Aus wessen Sicht bewertet die Nachsuche?** `v_mix(&nodes, 0)` ist der Wert des Spielers, der
   an der Wurzel des UNTERBAUMS am Zug ist -- und das ist der GEGNER (`game.rs:786-788` ruft nach
   `execute_move` ein `switch_player()`). Gewaehlt wird das Minimum, also der fuer den Gegner
   schlechteste Folgezustand. Das ist die beabsichtigte Richtung; falls dort ein Vorzeichen oder
   eine Perspektive kippt, misst der Lauf das Gegenteil.
2. **Wird die gewaehlte Reihenfolge ueberhaupt gespielt?** Der Rueckgabeweg laeuft ueber
   `m.take.moon_order`; die Nachsuche tauscht das Feld und gibt die Aktion zurueck. Zu pruefen
   ist, dass genau diese Aktion ausgefuehrt wird und nicht die urspruengliche.
3. **Kommen die Varianten vollstaendig an?** `unique_moon_orders` liefert die eindeutigen
   Permutationen; bei drei verschiedenen Farben sind es sechs. Wird davon eine Teilmenge
   bewertet, ist der beste Kandidat womoeglich nie dabei.
4. **Reicht das Budget?** 256 Sims je Variante geben Wurzelbreite 16; wenn der entscheidende
   Gegnerzug (den frisch oben liegenden Stein nehmen) nicht unter den 16 Kandidaten ist, sieht
   die Nachsuche den Unterschied nicht, den sie messen soll.
5. **Ist die Stelle ueberhaupt erreicht worden?** Die Diagnostik aus par.9b sagt 24,34
   (seit par.9i korrigiert auf 12,20)
   Gelegenheiten je Partie; wenn im Artefakt weniger Nachsuchen auftauchen, greift das Tor
   seltener als gedacht.

**Erst wenn diese fuenf sauber sind, ist ein Nullbefund ein Befund ueber das Spiel.**

## par.9e EINWAND GEGEN DEN PRIOR: Plackett-Luce ist kurzsichtig (Nutzer 2026-09-14)

Nutzer woertlich: *"ich denk mir Plackett-Luce-Modell ist halt kurzfristig. da brauchst schon ein
wenig weitsicht. zumindest rundensicht."*

**Das trifft die Vorordnung, nicht die Nachsuche.** Der Prior, der die Varianten sortiert, kommt
aus dem `moon`-Kopf ueber `plackett_luce_prob` (`net_mcts.rs:2097`) -- er rankt FARBEN nach
einem Sofortwert und kennt keine Folgen ueber die Runde hinweg. Das Trainingsziel dahinter
(`moon_order_target`) stammt aus dem Rundenloeser, ist also auf das Rundenende gerichtet und
nicht auf den Partieausgang; genau das ist H2 in par.3.

**Was Stufe 3 daran aendert und was nicht:** die Nachsuche ersetzt den Prior NICHT als
Entscheider -- sie bewertet die Varianten mit einer echten Suche ueber den Folgezustand und
laesst den Prior nur die Reihenfolge der Bewertung bestimmen. Damit liegt die Entscheidung
erstmals bei einer Suche statt bei einer Sofortwert-Rangfolge. **Wie WEIT diese Suche sieht, ist
aber eine Budgetfrage:** 256 Sims je Variante geben Wurzelbreite 16 und reichen fuer den
naechsten Halbzug -- ob sie bis zum Rundenende tragen, ist NICHT geprueft.

**Folge fuer die Auswertung (Ergaenzung zu par.9d):** faellt das A/B flach aus, ist "die Suche
sieht zu kurz" eine sechste Verdachtsstelle neben den fuenf dort genannten. Sie ist billig
pruefbar, indem `MOSAIC_MOON_ORDER_SEARCH_SIMS` erhoeht wird -- das ist ein Knopf, kein Umbau.
Traegt der Effekt erst bei deutlich groesserem Budget, ist das ein Befund ueber die noetige
Weitsicht und kein Widerspruch zur Bauform.

## par.9f VORAUSSETZUNG GEPRUEFT: der Value-Kopf SIEHT die Mondstapel-Reihenfolge

Nutzer-Einwand 2026-09-14: *"wenn wir keinen value oder policy im mondstapel haben wird es
schwierig."* Berechtigt -- und am Code geprueft mit positivem Ergebnis.

**Der Encoder kodiert die Mondseite der kleinen Fabriken als 4 x 15 Werte** (`features.rs:833-850`
JSON-Pfad, `:1313-1325` Direktpfad): je Fabrik DREI Positionen mal FUENF Farben als One-Hot, und
zwar `stack.iter().rev()` -- von OBEN nach unten, Position 0 ist der oberste Stein. Die Stapel
sind hoechstens drei hoch (gemessen in par.9b: 1, 2 oder 3), es faellt also nichts weg.

**Der Value-Kopf sieht die Reihenfolge damit vollstaendig und positionsgenau.** Jede Permutation
erzeugt einen anderen Eingabevektor.

**Das ist der entscheidende Unterschied zur Rueckgabe-Reihenfolge**
(`PREREG_dome_return_order.md` par.10), an der dieselbe Idee scheitert:

| | Kuppelstapel-Block (Rueckgabe) | Mondstapel |
| --- | --- | --- |
| Kodierung | Typ-Folge (+1 Spezial / -1 Joker / 0), `features.rs:212` | **Farbe je Position, One-Hot** |
| Aufloesung | vier Positionen, drei Typklassen | **drei Positionen, fuenf Farben** |
| Folge | gleichtypige Platten ununterscheidbar | **jede Permutation unterscheidbar** |

**Folge fuer par.9d:** Verdachtsstelle 1 ("sieht die Bewertung den Unterschied ueberhaupt?") ist
damit ENTSCHAERFT, was die Eingabe angeht. Bleibt ein Nullbefund, liegt es nicht daran, dass der
Value-Kopf blind waere -- die uebrigen fuenf Stellen und die Budgetfrage aus par.9e stehen weiter.

**Die Policy hat keine eigene Dimension fuer `moon_order`** (par.2). Stufe 3 braucht sie auch
nicht: entschieden wird ueber Blattwerte einer Suche, nicht ueber einen Prior auf Aktionen. Der
`moon`-Kopf ordnet nur die Bewertungsreihenfolge.

## par.9g DIAGNOSE-ZEILE NACHGETRAGEN (2026-09-15, Code gebaut, Wheel-Bau steht aus)

**Die Luecke.** Der Streu-Knopf der Rueckgabe schreibt seit seinem Bau eine
`[return_order]`-Zeile ins Spiel-Log (self_play.rs:1188/1207). Die Nachsuche aus Stufe 3
schreibt NICHTS. Damit ist aus den Logs des A/B vom 2026-09-14 nicht ablesbar, ob sie
ueberhaupt eine ANDERE Reihenfolge waehlt als der Bestand. Beim Bau von Stufe 3 wurde die
Zeile schlicht vergessen; aufgefallen ist es erst, als der A/B auf einen Gleichstand zulief
(Nutzer-Meldung 2026-09-14, 95:95 nach 190 Paaren).

**Warum die Zahl gebraucht wird, und zwar VOR Weg C.** Ein Nullbefund hat hier zwei Lesarten,
und sie fuehren zu entgegengesetzten Entscheidungen:

| Befund | Lesart | Folge fuer par.10 |
| --- | --- | --- |
| `changed` nahe 0 | die Nachsuche bestaetigt fast immer den Bestand | der Horizont ist NICHT der Engpass -- **Weg C faellt**, und mit ihm Fahrplan 32a |
| `changed` hoch, Ergebnis flach | sie waehlt oft anders, es aendert den Ausgang nicht | Weg C bleibt die naechste Frage (reicht die Weitsicht der Nachsuche nicht?) |

par.9b hat bereits gemessen, dass die GELEGENHEIT haeufig ist (dort 24,34 echte Wahlen je
Partie, seit par.9i auf 12,20 korrigiert,
n = 12.907 Partien). Offen ist die zweite Haelfte: was die Nachsuche aus der Gelegenheit macht.

**Bauform.** Zwei thread-lokale Zaehler in `net_mcts.rs` (`MOON_ORDER_DIAG`: Ausloesungen,
Abweichungen), erhoeht an der Wahlstelle in `moon_order_post_search`; ausgelesen und
zurueckgesetzt per `take_moon_order_diag()`. `unified_game_loop` verwirft den Stand am
Partieanfang und schreibt am Partieende EINE Zeile, wenn ueberhaupt etwas ausgeloest hat:

    [moon_order] applied=<n> changed=<m>

**Warum nicht an Ort und Stelle geloggt:** in `moon_order_post_search` ist `state` nur
unveraenderlich geliehen, `log_event` braucht `&mut`. Ein `println!` waere auf stdout gelandet
statt im Spiel-Log und haette bei rund 24 Ereignissen je Partie die Laufausgabe geflutet --
eine erste Fassung genau so wurde verworfen.

**Warum der Reset die tragende Eigenschaft ist:** ein Worker spielt viele Partien auf
demselben Thread. Ohne Zuruecksetzen zaehlte die Zeile einer Partie alle frueheren mit, und
"changed je Partie" waere um die Zahl der bereits gespielten Partien zu gross. Dagegen stehen
zwei Sicherungen (Verwerfen am Partieanfang, Reset beim Lesen) und der Test
`moon_order_diagnostics_reset_on_read`.

**Bitidentitaet:** bei `moon_order_variants != 2` loest nichts aus, `applied` bleibt 0, es
wird keine Zeile geschrieben. Der Zaehler sitzt hinter dem Early-Out von
`moon_order_post_search_applies`.

**STAND: Code im Baum, NICHT gebaut.** Das Wheel bleibt unangetastet, solange die Messkette
der Nacht laeuft -- sie und die Anschlusskette fahren auf dem Kontrakt 39994362fba145a6, und
ein Neubau mitten in der Kette haette die Arme auf zwei verschiedenen Wheels laufen lassen.
Faellig danach: `cargo test --release`, Wheel-Bau, dann eine kleine Serie mit
`moon_order_variants=2` und `--log-games`, aus der die beiden Zahlen fallen.

## par.9h ERGEBNIS STUFE 3 (2026-09-15): die Nachsuche traegt NICHT -- und par.9d haelt

**Lauf:** `moon_order_post_vs_off_s20261091.json`, 200 Paare / 400 Partien, beide Seiten
`alphazero_v28-b02_brierbest` @400 c_puct 1,5, Unterschied GENAU ein Spec-Feld
(`moon_order_variants` 2 gegen 0), Blockgroesse 5, SPRT weit gesetzt (alpha = beta = 0,001),
kein Frueh-Stopp. Laufzeit **5.933 s Wanduhr, 25.868 s CPU, 10 Threads, 14,833 s je Partie**.

**a = Nachsuche, b = kanonisch.**

| Groesse | a (Nachsuche) | b (kanonisch) | Differenz |
| --- | --- | --- | --- |
| Siege (n = 200 Paare) | **197** | **203** | -6 |
| SPRT | \-- | \-- | UNDECIDED_CAP_REACHED, LLR -5,786 (Schranke -6,907) |
| McNemar p | \-- | \-- | **0,844** |
| gepaarte Differenz | \-- | \-- | -0,030 [-0,229, +0,169] |
| Sweeps a / Sweeps b / Splits | 50 | 53 | 97 |

### Die sechs Standard-Kennzahlen

Spaltenblock: n = 396 je Seite (von 400; vier Partien nicht nachspielbar, Chip-Vollendung).
Plattenblock: n = 400 Bretter je Modell.

| # | Kennzahl | a | b | Diff a-b |
| --- | --- | --- | --- | --- |
| 1 | Reihen voll / Fuellsumme / lange Reihen vollendet | 0,1465 / 17,838 / 3,056 | 0,1540 / 17,879 / 2,990 | -0,008 / -0,040 / +0,066 |
| 2 | **volle Spalten** (SE 0,038 / 0,039) | **0,8838** | **0,9823** | **-0,0985** |
| 2b | Spalten >= 4 / >= 3 / max. Hoehe | 2,270 / 3,174 / 5,604 | 2,230 / 3,179 / 5,641 | +0,040 / -0,005 / -0,038 |
| 3 | Strafleiste gesamt / Rundenstrafen (Log) | 8,682 / -13,672 | 8,467 / -13,453 | +0,215 / -0,220 |
| 4 | Platten gesamt / Spezial-Bonus / Plazierung | 7,855 / 5,263 / 52,038 | 7,532 / 5,125 / 52,708 | +0,323 / +0,138 / -0,670 |
| 5 | eigene Punkte (SE 0,86 / 0,94) | 52,465 | 52,928 | -0,462 |
| 6 | Marge (SE 0,995) | -0,463 | +0,463 | -0,925 |

**Keine Groesse ist ueber der Aufloesung.** Die groesste Einzelabweichung sind die vollen
Spalten mit -0,0985; bei SE 0,038 und 0,039 je Seite sind das rund 1,8 SE der ungepaarten
Differenz, also unterhalb der Schwelle und auf einer Groesse, die ueber Seeds bekanntlich
stark streut. **Sie zeigt allerdings in dieselbe Richtung wie alles andere**: Siege, Punkte,
Marge, Plazierungspunkte und Strafleiste liegen saemtlich leicht gegen die Nachsuche. Nur die
Plattenpunkte (+0,32) und der Spezial-Bonus (+0,14) liegen dafuer.

### par.9d ist abgearbeitet: drei der fuenf Punkte sind sauber, zwei bleiben offen

par.9d hat vorab festgelegt, dass ein Nullbefund hier ein IMPLEMENTIERUNGS-VERDACHT ist und
kein Verdikt (Nutzer: *"dann haut irgendwas von der implementierung noch nicht hin"*). Die
fuenf Punkte, am Code geprueft 2026-09-15:

1. **Perspektive GRUEN.** `choose_moon_order_with` klont, ruft `apply_drafting`, und in
   `game.rs::apply_drafting` laeuft `switch_player()` -- im Folgezustand ist der GEGNER am Zug.
   Gewaehlt wird per `if best.is_none_or(|(_, b)| opp_value < b)`, also das MINIMUM des
   Gegnerwerts. Die Richtung ist die beabsichtigte.
2. **Die gewaehlte Reihenfolge wird gespielt: GRUEN.** `moon_order_post_search` setzt
   `mm.take.moon_order = seq` und gibt die Aktion zurueck; in `net_drafting_policy`
   (self_play.rs:5664-5675) ist ihr Ergebnis `chosen` und damit das erste Tupelglied, das der
   Agent spielt. Der Arena-Pfad ist derselbe: `paired_gating.py` ruft `net_vs_net_arena_match`
   (lib.rs:378) -> `run_net_vs_net_arena` -> `NetSelfPlayAgent::decide` (self_play.rs:3441)
   -> `net_drafting_policy`. **Die Nachsuche lief in diesem Lauf tatsaechlich.**
3. **Varianten vollstaendig: GRUEN.** `unique_moon_orders(&m.take.moon_order)` liefert alle
   eindeutigen Permutationen, ohne Deckel; `RETURN_ORDER_MAX_PERMUTED` gehoert zum anderen
   Knopf. Der Test `choose_moon_order_with_picks_the_order_the_evaluator_prefers` belegt, dass
   jede vorhandene Ziel-Oberflaeche erreichbar ist.
4. **Budget: OFFEN, nur messbar.** 256 Sims je Variante geben Wurzelbreite 16
   (`gumbel_top_m_for_budget`). Ob der entscheidende Gegnerzug -- den frisch oben liegenden
   Stein nehmen -- unter diesen 16 Kandidaten ist, steht nicht im Code, sondern im Lauf.
5. **Ausloesungsrate: GRUEN, per Deckungsgleichheit der Bedingung** (praezisiert 2026-09-15,
   nachdem der Punkt zuerst als offen notiert war). Das Tor prueft
   `TakeSource::SmallFactorySun && moon_order.len() >= 2 && unique_moon_orders(..).len() >= 2`
   (`moon_order_post_search_applies`), und `choose_moon_order_with` prueft dieselbe Bedingung
   noch einmal. par.9b hat GENAU diese Menge gezaehlt -- "mindestens zwei eindeutige
   Reihenfolgen", dort 24,34 je Partie (seit par.9i auf 12,20 korrigiert -- die Log-Methode
   zaehlte Zustaende mehrfach). Die Frage "wird die Stelle erreicht" ist damit beantwortet,
   ohne dass eine Logzeile noetig waere: das Tor kann nicht seltener oeffnen als die Bedingung
   zutrifft. **Uebertragen, nicht beobachtet:** par.9b zaehlte auf 12.907 Self-Play-Partien bei
   anderen Sims und anderer Spec; die Rate DIESES Laufs kann davon abweichen, die Bedingung
   nicht.

**Damit ist der Verdacht aus par.9d in vier von fuenf Punkten ausgeraeumt.** Offen bleibt allein
Punkt 4, das Budget. Das Verdikt lautet deshalb NICHT "die Reihenfolge ist egal" -- diese
Gegenhypothese ist seit par.7 widerlegt -- sondern: **die Nachsuche in DIESER Bauform und mit
DIESEM Budget traegt nicht.**

**Und die Frage, die par.9d gar nicht gestellt hat, ist die eigentlich offene:** nicht WIE OFT
die Nachsuche laeuft, sondern WIE OFT SIE ANDERS WAEHLT. Dafuer ist die Diagnose-Zeile gebaut
(par.9g, `changed`). Bleibt `changed` nahe 0, bestaetigt die Nachsuche fast immer den Bestand --
dann ist weder Horizont noch Budget der Engpass, sondern der Prior ordnet die Varianten
bereits so, wie die Suche sie ohnehin sortiert, und **Weg C faellt vor dem Bau**. Ist `changed`
hoch, bleibt Punkt 4 der Verdaechtige und Weg C die naechste Frage.

**KOSTENSEITE BELEGT (nachgetragen 2026-09-15, 01:20):** dass die Nachsuche auch wirklich
RECHNET und nicht nur ausloest, faellt aus derselben Nachtkette. `k4_kosten_ohne_s20261093`
ist der Basiswert ohne Nachsuche und ohne K4 (reine Champion-Spec, identische Specs beidseitig):
**12,286 s je Partie**. Dieser Lauf liegt mit **14,833 s** also **+20,7 Prozent** darueber --
und das, obwohl in jeder Partie nur EINE der beiden Seiten die Nachsuche traegt. Hochgerechnet
auf beidseitigen Betrieb rund +41 Prozent (**Herleitung, nicht gemessen**: die Gelegenheiten
sind nicht exakt gleich auf beide Seiten verteilt). par.9b erwartete +57 Prozent an Zusatz-SIMS;
Sims und Wanduhr sind nicht dasselbe (thread-lokale Memoisierung, Batch-Effekte), die
Groessenordnung passt. **Damit ist par.9d Punkt 5 doppelt belegt:** die Torbedingung oeffnet
(Deckungsgleichheit mit par.9b), und der Aufwand faellt tatsaechlich an. Der Nullbefund kommt
NICHT daher, dass die Nachsuche nie lief.

### Was das fuer par.10 heisst

Die Richtung der Randgroessen passt zu Weg C, ohne ihn zu belegen. Die Nachsuche optimiert
`v_mix` des Folgezustands, also den Wert EINEN Halbzug weiter -- und genau die langfristigste
Groesse im Block (volle Spalten) faellt am staerksten gegen sie aus, waehrend die kurzfristigen
Plattenpunkte leicht fuer sie sprechen. Das ist derselbe Einwand, den par.9e gegen den Prior
erhebt und den der Nutzer gegen die Bauform erhoben hat (*"da brauchst schon ein wenig
weitsicht. zumindest rundensicht."*). **Als Beleg taugt es nicht** (1,8 SE auf einer Groesse,
die ueber Seeds stark streut); als Reihenfolge-Argument fuer C vor B vor A taugt es.

## par.9i DIAGNOSE GEMESSEN (2026-09-15): 12,20 Entscheidungen je Partie, und par.9bs 24,34 ist eine UEBERZAEHLUNG

**Lauf** `moon_order_diagnostics_s20261110.json`: 10 Paare / 20 Partien, BEIDE Seiten
`v28-b02` @400 mit `moon_order_post2` (Nachsuche aktiv), `--log-games`, 298,6 s.

| Groesse (n = 20 Partien, beide Seiten, Zaehler aus par.9g) | Wert |
| --- | --- |
| **Ausloesungen der Nachsuche je Partie** | **12,20** |
| davon ANDERE als die kanonische Wahl (`changed`) | **0,623** |

**Die zweite Zahl beantwortet die Frage aus par.9g, und zwar im zweiten Zweig:** die Nachsuche
waehlt in fast zwei Dritteln der Faelle eine ANDERE Reihenfolge als der Bestand -- und aendert
am Ausgang trotzdem nichts (par.9h, 197:203). **Der Prior ist also nicht die Erklaerung.** Weg C
(Horizont) und Weg A (Entscheidungsform) bleiben lebend, Weg B verliert an Dringlichkeit.

### KORREKTUR an par.9b: die 24,34 zaehlen Zustaende, nicht Ereignisse

par.9b hat "24,34 echte Wahlen je Partie" aus den `--log-games`-Artefakten gezaehlt. **Diese
Zahl ist zu hoch, und der Grund sitzt im Logformat.** Die Zeile

    🌙 F2 Mond-Stapel: (gelb, tuerkis→gelb)

entsteht bei jedem Sonnenzug aus einer kleinen Fabrik mit Rest (`execution.rs:147-159`), und
ihr Inhalt kommt aus `format_moon_stacks(&state.factories[fidx])` -- das formatiert **ALLE
Mond-Stapel dieser Fabrik in ihrem AKTUELLEN Zustand**, nicht den einen gerade gelegten. Die
Zeile ist eine ZUSTANDSANZEIGE. Derselbe Stapel erscheint bei jedem weiteren Zug aus derselben
Fabrik erneut; im Log stehen direkt hintereinander `F4 ... (rot→tuerkis)`, spaeter `F4 ...
(rot)` und `F3 ... leer`.

**Wer diese Zeilen als Ereignisse zaehlt, zaehlt Stapel mehrfach.** Nachgerechnet an denselben
20 Partien: die Log-Methode liefert 23,20 "Wahl-Ereignisse" je Partie -- nahe an par.9bs 24,34,
weil BEIDE dieselbe fehlerhafte Methode benutzen -- waehrend der Zaehler IM CODE, der je
tatsaechlicher Entscheidung einmal hochzaehlt, 12,20 sagt. **Faktor 1,90.**

**Die richtige Zahl ist 12,20** (n = 20 Partien, Grundmenge Ausloesungen der Nachsuche je Partie
ueber BEIDE Seiten, Einheit Entscheidungen; gezaehlt an der Wahlstelle in
`moon_order_post_search`, nicht im Log).

**Folge fuer die Kostenrechnung:** par.9b schaetzte rund 18.350 Zusatz-Sims je Partie bei
Budget 256 aus 24,34 Gelegenheiten. Mit 12,20 sind es rund **9.200** -- etwa +29 Prozent
gegenueber @400 statt +57. Das passt zur gemessenen Wanduhr: der Diagnoselauf mit beidseitiger
Nachsuche kostet 14,93 s je Partie gegen 12,29 s ohne (`k4_kosten_ohne_s20261093`), also
**+21,5 Prozent**. Die alte Schaetzung lag um denselben Faktor daneben wie die Zaehlung.

### Eine verworfene Hypothese, offen dokumentiert

Aus der Differenz 23,20 gegen 12,20 hatte ich zunaechst geschlossen, die Nachsuche erreiche nur
52,6 Prozent der Gelegenheiten, weil sie in `net_drafting_policy` sitzt -- also an EINEM der
drei Zweige von `NetSelfPlayAgent::decide` (self_play.rs:3458-3464: Ein-Aktions-Kurzschluss,
Vorzugs-Handregel, Gumbel-Suche). Die Hypothese war aus dem Code HERGELEITET, nicht gemessen.

**Sie ist widerlegt.** Der Gegentest: die Nachsuche zusaetzlich in den beiden anderen Zweigen
aufrufen, dann dieselbe Serie mit demselben Seed. Ergebnis **bitgleich** -- Ausloesungen 12,20,
`changed` 0,6230, Deckung unveraendert. Der Umbau ist deshalb zurueckgenommen worden: eine
Aenderung im Suchpfad, die nachweislich nichts bewirkt, ist Ballast mit falscher Begruendung.
(Anker-Drift war waehrend des Versuchs gruen, der Kontrakt-Hash unveraendert; der Eingriff war
also harmlos, nur nutzlos.)

**Lehre, dieselbe wie bei der Dreierstapel-Korrektur in par.9b:** eine Log-Zeile sagt, WAS sie
formatiert, nicht was man in ihr zaehlen moechte. Vor jeder Zaehlung ueber Logs gehoert die
formatierende Codestelle gelesen -- hier haette `format_moon_stacks` die Frage in einer Minute
beantwortet.

## par.10 ARCHITEKTUR-HEBEL jenseits der Sim-Zahl (Nutzer-Auftrag 2026-09-14, VOR dem Bau)

Nutzer: *"ist mir dennoch noch zu schwach. ueberleg dir jenseits von der sim anzahl was wir von
der architektur optimieren koennen."* -- registriert werden drei Wege. Keiner ist gebaut.

**Der Ausgangsbefund, der sie alle traegt:** `moon_order` ist heute in die Take-Aktion
eingebacken. Die Engine kann mehrstufige Zuege aber laengst -- `ChooseDomeRotation` ist ein
EIGENER Zug im Baum, der den Spieler nicht wechselt (`moves.rs`: "ueber zwei
Spielerentscheidungen ... ohne switch_player()") und eine eigene Aktions-ID traegt
(`serialize.rs:614`, `move_action_id`). Die Mondreihenfolge ist die Ausnahme, nicht die Regel.

### Weg A: eigener Entscheidungsknoten (der grosse Wurf)

Nach dem Sonnenzug ein Folgeknoten "welcher Stein liegt oben", gebaut wie die Kuppelrotation.

* **Gewinn 1:** MCTS verteilt Visits und Backups darauf -- keine Nebensuche, kein Extra-Budget,
  die Tiefe kommt aus dem normalen Sim-Budget.
* **Gewinn 2:** die Varianten konkurrieren NICHT mehr mit anderen Zuegen um das Wurzelfenster --
  genau der Defekt, den Stufe 1 gemessen hat (par.7).
* **Gewinn 3, der eigentliche:** die POLICY bekommt eine Dimension. Das Netz kann die Wahl
  lernen, statt sie ueber einen Hilfskopf zu ranken. Damit faellt auch der Einwand aus par.9e
  (Plackett-Luce ist kurzsichtig) weg -- der Prior kaeme dann aus derselben Policy wie jeder
  andere Zug.
* **Preis:** `NUM_ACTIONS` waechst. Das macht **alle bestehenden Checkpoints unbrauchbar**
  (`feedback_num_actions_change_breaks_old_checkpoints`) -- Champion, Anker-Kader, die ganze
  Leiter muessten neu aufgebaut oder als Cross-Aera gefuehrt werden. par.6 schliesst die
  Erweiterung bisher aus; das war eine ENTSCHEIDUNG, keine Notwendigkeit, und sie ist hiermit
  wieder offen.
* **Empfehlung:** nicht fuer den Mondstapel allein. Wer `NUM_ACTIONS` anfasst, macht es EINMAL
  fuer alles, was eine Dimension braucht.

#### Was sonst noch fuer Weg A in Frage kommt (Nutzer-Frage 2026-09-14, erhoben am Code)

Der heutige Aktionsraum (`net_mcts.rs:51-53`): 328 Stone+Tiling + 27 dome_slot + 36
draw_stack_slot + 4 rotation + 6 use_chips + 4 bonus_chip + 1 peek = 406.

**Drei Teilentscheidungen loest die Engine INTERN, statt sie der Suche zu geben** -- dasselbe
Muster, dieselbe Fehlerklasse:

| Entscheidung | heute geloest durch | Schaden belegt? |
| --- | --- | --- |
| **Mondstapel-Reihenfolge** (`moon_order`) | in die Take-Aktion eingebacken; Fan-out oder Nachsuche, kein Policy-Ziel | Stufe 1 flach (par.7); Wirkung ungeklaert |
| **Rueckgabe-Reihenfolge** (`return_order`) | kanonisch oder Blattbewertung; **keine Policy-Dimension** (`dome_return_order` par.2) | A/B flach, aber Henne-Ei (dort par.10) |

**GESTRICHEN: die Chipwahl ist KEINE Luecke** -- zweimal korrigiert, beide Male vom Nutzer
ausgeloest.

Der Koordinator hatte sie erst als dritten Weg-A-Kandidaten gefuehrt ("Handregel"), dann als
billigen Korrektheitsfix ("greedy statt exakt"). **Beides war falsch.** Am Code nachgesehen:

* Die **Chip-Aufnahme beim Drafting** hat vier eigene Policy-Dimensionen (`bonus_chip`).
* Die **Reihenwahl beim Tiling** loest der Solver -- wie der Nutzer sagte.
* Die **Chip-Teilmenge** ebenfalls: `tiling_solver.rs:17` importiert `chip_allocations`, und der
  Modulkopf (`:36-38`) haelt fest, dass sie "in `legal_steps`, einmal PRO chippable Reihe PRO
  Knoten" gerufen wird und bis zu 2^14 Teilmengen prueft (`CHIP_ALLOC_CAP = 14`). **Der Solver
  verzweigt ueber ALLE Allokationen**; `greedy_chip_alloc` ist nur der Cap- und
  Budget-Fallback.

**Der in `docs/pitfalls.md` nachgerechnete Schaden betrifft den REPLAYER, nicht das Spiel:** dort
steht ausdruecklich, der Replayer spiele jede geloggte Vollendung "ueber den Menschen-Einstieg
`apply_tiling_chips`, und der ist GREEDY". Ein Werkzeugproblem beim Nachspielen.

**Wie der Fehler entstand, weil er sich wiederholen kann:** der Koordinator greppte die Aufrufer
von `chip_allocations` mit `head -6` und bekam nur `py.rs` und `referee.rs` zu sehen --
`tiling_solver.rs` fiel unter den Schnitt. Daraus wurde "nur die GUI nutzt es, die KI spielt
greedy". **Dieselbe `head`-Falle hat in dieser Kampagne schon einmal einen Wheel-Bau zerlegt**
(uebersehenes Beispiel, E0063). Aufrufer-Greps gehoeren vollstaendig, ohne Schnitt.

**Fuer Weg A bleiben damit ZWEI Kandidaten** (Mondstapel- und Rueckgabe-Reihenfolge), nicht drei.
Der staerkste Einzelgrund, den der Koordinator genannt hatte, existiert nicht.

**Nicht auf der Liste, weil bereits abgedeckt:** Kuppelplatte, Slot und Rotation (dome_slot 27
plus rotation 4, eigener Zug `ChooseDomeRotation`), die Peek-Entscheidung (1 Dimension, binaer
genuegt), Startsetzung (laeuft ueber dieselben dome_slot/rotation-Dimensionen).

**Folge:** ein `NUM_ACTIONS`-Wechsel waere mit diesen drei Posten zu buendeln. Die Groesse der
Erweiterung ist noch nicht bestimmt -- fuer den Mondstapel genuegt vermutlich "welcher Stein
liegt oben" (5 Farben), fuer die Rueckgabe dasselbe, fuer die Chipwahl ist die Kombinatorik zu
klaeren. **Das ist eine eigene Vorregistrierung wert, bevor irgendetwas gebaut wird.**

### Weg B: Ziel des `moon`-Kopfs wechseln

Das ist H2 aus par.3 und Stufe 2 aus par.5, jetzt ohne die Bindung an H1 (die auf der
widerlegten Gegenhypothese stand, siehe Nachtrag in par.3). Der Prior kommt heute aus dem
Rundenloeser, ist also auf das Rundenende gerichtet statt auf den Partieausgang.

* Kein neuer Kopf (`feedback_no_new_heads` erlaubt Zielwechsel), keine Aktionsraum-Erweiterung.
* **Preis:** ein Trainingsarm plus Gating, rund 1,5 h.
* **Lesart:** traegt der Zielwechsel, ist der Prior die Ursache; traegt er nicht, liegt es an der
  Entscheidungsform (Weg A) oder am Horizont (Weg C).

### Weg C: Terminierung statt Sim-Zahl

Die Nachsuche aus Stufe 3 laeuft heute auf ein festes Budget. Alternative: bis zum RUNDENENDE
rechnen -- Nutzer 2026-09-14: *"da brauchst schon ein wenig weitsicht. zumindest rundensicht."*

* Das ist ein Abbruchkriterium, kein Sim-Parameter; die Tiefe richtet sich nach der Stellung
  statt nach einer Zahl.
* **Preis:** unklar und stellungsabhaengig -- ein Kostentor ist hier Pflicht, nicht Kuer.
  Nahe am Rundenende billig, frueh in der Runde teuer.
* Unabhaengig von A und B, billiger als beide.

### Reihenfolge

**C vor B vor A.** C ist der kleinste Eingriff und adressiert denselben Einwand wie B (Weitsicht),
ohne Training. B kostet einen Arm und beantwortet die Prior-Frage sauber. A ist der grosse Wurf
und sollte nur gebaut werden, wenn C und B die Sache nicht erklaeren -- und dann gebuendelt mit
allem anderen, was eine Policy-Dimension braucht.

**Voraussetzung fuer alle drei:** das Ergebnis des laufenden A/B (Stufe 3, par.9c). Traegt die
Nachsuche bereits, ist die Frage nicht mehr "warum wirkt nichts", sondern "wie viel geht noch" --
und dann steht C vorn.

## par.10a EINGETAKTET (Nutzer-Auftrag 2026-09-15): C und B stehen VOR Fahrplan Nr. 33

Woertlich: *"b und c kannst ebenfalls eintakten vor fahrplan punkt 33"*, gesagt beim
Zwischenstand des Stufe-3-A/B (Nutzer-Meldung 2026-09-14, 95:95 nach 190 von 200 Paaren:
*"wird mit ziemlicher sicherheit ein tie"*). Damit sind sie als **Nr. 32a (Weg C)** und
**Nr. 32b (Weg B)** in `evaluations/v29_program_agent_plan.md` eingetragen, vor dem Bau von
Variante B des Rundenuebergangs.

**Die Voraussetzung oben ist damit aufgeloest, und zwar in den Zweig "warum wirkt nichts".**
Wichtig fuer die Diagnose ist, dass Seltenheit als Erklaerung AUSSCHEIDET: die Nachsuche greift
**12,20-mal je Partie** (par.9i, im Code gezaehlt; par.9bs 24,34 aus den Logs war eine
Ueberzaehlung, n = 12.907 Partien, Grundmenge Mondstapel-Ereignisse mit
mindestens zwei eindeutigen Reihenfolgen, Einheit Ereignisse). Sie laeuft oft und aendert am
Ausgang nichts. Das unterscheidet Stufe 3 von Stufe 1, wo Seltenheit noch eine offene
Erklaerung war, und es laesst genau drei Kandidaten uebrig: Horizont (C), Prior (B),
Entscheidungsform (A). Die Reihenfolge C vor B vor A bleibt damit unveraendert gueltig.

**Was beides NICHT ist: eine Kettenposition.** Der Nutzer-Auftrag lautete "eintakten", und
eingetaktet sind sie in den FAHRPLAN, nicht in eine Nachtkette. Beide beginnen mit einem Bau
(C in Rust, B als Trainingsarm), und ein Bau ist Volllast ueber viele Kerne, also Nebenlast im
Sinne von CLAUDE.md. Sie starten erst, wenn die Messkette der Nacht durch ist.

**Offen bei B, wenn es soweit ist:** ein Trainingsarm braucht eine eigene v29-bXX-Nummer
(`feedback_measured_identity_gets_own_bxx`); die Reservierung steht in
`docs/generation_naming.md`.

### 12.3a KORREKTUR (2026-09-16, Nutzer-Einwand): "der Hebel ist klein" traegt NICHT

**Der Einwand, woertlich:** *"das kannst so nicht rechnen meiner meinung nach. da musst alle
oben liegenden einer farbe beruecksichtigen nicht nur einen seperaten stapel."* Er trifft, und
zwar am Code belegt.

**Die Regel:** ein Mondzug ist **Aktion C** und damit GLOBAL. `validation.rs:214` erzeugt
Mond-Zuege ausschliesslich mit `factory_id: None` ueber `available_moon_colors(state)`; der
Kommentar in `execution.rs:48-50` sagt es ausdruecklich ("erzeugt Mond-Zuege NUR als Aktion C").
Ein Zug nimmt also ALLE Steine einer Farbe von ALLEN Stapel-Oberseiten auf einmal -- im Log
sichtbar als `2 (1+1)x tuerkis von F3, GF`.

**Was die Bilanz damit gemessen hat:** ob GENAU DIESER Stein im naechsten Halbzug vom Gegner
abgeholt wird (14,75 Prozent). Das ist eine gueltige, aber ENGE Frage. Sie beantwortet nicht,
wie gross der Hebel der Reihenfolge-Wahl ist -- denn wer eine Farbe oben legt, die anderswo
schon oben liegt, vergroessert das PAKET, das ein einziger Gegnerzug abraeumt.

**Die Buendel-Zahlen** (n = 20.842 Mondzuege aus denselben Artefakten):

| Groesse | Anteil |
| --- | --- |
| 1 Stein | 0,562 |
| 2 Steine | 0,276 |
| 3 Steine | 0,120 |
| 4 und mehr | 0,043 |
| **mittlere Buendelgroesse** | **1,653** |
| **mehr als ein Stein** | **0,438** |
| **mehr als eine Quellfabrik** | **0,407** |

**In zwei von fuenf Zuegen werden mehrere Stapel gleichzeitig abgeraeumt.** Der Mechanismus, den
die enge Frage uebersieht, ist also real und haeufig.

**Verdikt zurueckgenommen.** par.12.3 bleibt als Messung gueltig, aber die daraus gezogene
Folgerung "der Hebel ist klein, weder C1 noch A lohnen" ist NICHT gedeckt. Fahrplan 32c ist
damit nicht durch, sondern halb: die enge Zugriffsfrage ist beantwortet, die HEBELGROESSE nicht.

**Was dafuer noch fehlt (offen, nicht gebaut):** die kontrafaktische Messung -- um wie viel
aendert die Wahl der Oberseite die maximale Buendelgroesse, die dem Gegner im naechsten Halbzug
zur Verfuegung steht? Dafuer braucht es die Oberseiten ALLER Fabriken zum Zeitpunkt der Wahl;
aus dem Log sind sie nur als Zustandsanzeige je Fabrik rekonstruierbar (par.9i), sauberer waere
ein Zaehler im Code an derselben Stelle wie `MOON_ORDER_DIAG`.

**Lehre:** die Grundmenge einer Sonde muss der REGEL folgen, nicht der Datenstruktur. Die
Stapelzeile im Log legt "ein Stapel" als Einheit nahe; die Regel kennt aber nur "eine Farbe
ueber alle Oberseiten". Dieselbe Verwechslung wie in par.9i, wo die Zustandsanzeige als
Ereignisliste gelesen wurde.

## par.12.5 ARM v29-b05 GEMESSEN (2026-09-15): das No-Op-Ziel hat Staerke GEKOSTET

**Aufbau.** b05 = b03 plus `--moon-loss-weight 0`, sonst identisch -- Manifest-Diff gegen b03
zeigt GENAU zwei Felder (`moon_loss_weight` 1,0 -> 0,0 und den Namen), Policy-Traeger beidseits
580, derselbe Monolith, derselbe Seed 20260941. Training 3.031,7 s, 12 Epochen, bester
val_brier 0,1792 in Epoche 5 (b03: 0,17967 -- der Abstand liegt weit unter der Aufloesung
dieser Metrik, `project_offline_metric_resolution_limit`, und ist KEIN Befund).

**Tor 1 gegen b03**, zwei Seeds a 200 Paaren, Champion-Spec beidseits, **kein Frueh-Stopp**:

| Groesse | Seed 20261120 | Seed 20261121 |
| --- | --- | --- |
| Siege b05 : b03 | **215 : 185** | **212 : 188** |
| McNemar p | 0,159 | 0,235 |
| gepaarte Differenz | +0,150 [-0,044, +0,344] | +0,120 [-0,061, +0,301] |
| volle Spalten | +0,0125 | **+0,1033** |
| eigene Punkte | +0,15 | **+1,99** |
| Marge | +0,31 | **+3,98** |
| Spezialfelder belegt | +0,018 | +0,055 |
| Strafleiste | -0,20 | +0,04 |
| Reihen voll | -0,020 | 0,000 |
| Laufzeit | 4.563 s | 4.533 s |

**Gepoolt: 427 : 373 von 800 Partien, gepaarte Differenz +0,134 (SE 0,068), z = 1,98.**

### Verdikt

**Die vorab registrierte Lesart trifft zu, aber am unteren Rand.** par.12.1 sagt: *"traegt b05
(Gewicht 0), hat das Rauschziel Policy-Qualitaet gekostet und die Task-#38-Behauptung ist
erstmals gemessen"*. b05 traegt -- schwach, aber konsistent:

* **Beide Seeds zeigen dieselbe Richtung**, in der Siegquote wie in Punkten, Marge, Spalten und
  Spezialfeldern. Fuenf der sechs Standard-Kennzahlen liegen in beiden Seeds fuer b05.
* **Einzeln erreicht kein Seed die Schwelle** (p 0,159 und 0,235); gepoolt liegt z = 1,98 genau
  darauf. Nach `feedback_statistical_rigor` ist das KEIN Sieg, den man ohne Zusatz nennen darf.
* **Die Effektstaerke unterscheidet sich stark zwischen den Seeds** (+0,15 gegen +1,99 Punkte).
  Das ist die bekannte Seed-Streuung dieser Kampagne (`project_training_seed_variance`).

**Was damit gemessen ist:** das Entfernen eines Trainingsziels, das nachweislich eine Konstante
lernt (par.12.0), macht das Netz nicht schlechter -- eher besser. Der Kopf hat also Kapazitaet
und Gradienten verbraucht, ohne etwas beizutragen. Die Task-#38-Behauptung "der moon-Kopf hilft"
ist damit erstmals geprueft und in ihrer bisherigen Form widerlegt.

**Was NICHT gemessen ist:** ob ein Kopf mit RICHTIGEM Ziel hilft. Das ist b04
(`--moon-target-source played`), und dessen Voraussetzung ist erfuellt -- die Korpus-Sonde
findet **44,1 Prozent** nicht-kanonische gespielte Reihenfolgen (245 von 556, Tor war 10
Prozent). b04 bleibt also auf dem Plan.

**Vorschlag (Nutzer-Entscheid):** ein DRITTER Seed als Stichentscheid, Praezedenz v26/v28
(dort hat der dritte Seed die Nachbar-Kante entschieden). Kosten rund 75 min. Ohne ihn bleibt
der Befund "konsistente Richtung, gepoolt an der Schwelle" -- tragfaehig fuer die Entscheidung
"Kopf raus", nicht fuer eine Elo-Kante.

### Korrektur an der eigenen Auswertung (2026-09-15)

Die erste Fassung dieser Tabelle hatte ALLE Vorzeichen der Kennzahlen vertauscht: die Seiten
der Spaltensonde wurden nach ihrer Position im Dict zugeordnet (`list(seiten)[0]`) statt nach
ihrem NAMEN -- und dort steht `v29-b03` zuerst. Aufgefallen ist es nur, weil Gating und
Spaltensonde sich dann widersprachen (Gating: b05 mehr Punkte; Sonde scheinbar: b05 weniger).
Dieselbe Falle wie in `project_selfplay_log_parsing_traps`: **die Seite kommt aus dem Namen,
nie aus der Reihenfolge.**

## par.11 WEG C VORREGISTRIERT (2026-09-15, VOR dem Bau): Terminierung statt Sim-Zahl

**Fahrplan 32a.** Nutzer-Auftrag 2026-09-14: *"da brauchst schon ein wenig weitsicht.
zumindest rundensicht."* Ausloeser ist par.9i: die Nachsuche waehlt in **62 Prozent** der Faelle
ANDERS als kanonisch und aendert am Ausgang trotzdem nichts. Der Prior ordnet also nicht schon
richtig vor -- die Nachsuche trifft eine echte, andere Wahl, die sich nicht auszahlt. Zwei
Erklaerungen bleiben: ihr HORIZONT ist zu kurz (Weg C) oder ihre Entscheidungsform ist falsch
(Weg A).

**Bestand:** je Variante ein `build_net_tree` ueber den Folgezustand mit festem Budget
(`moon_order_search_sims`, Default 256), Kennzahl `v_mix` an dessen Wurzel, gewaehlt wird das
Minimum (net_mcts.rs `choose_moon_order_with`/`moon_order_post_search`). Der Baum sieht also
rund 256 Simulationen weit -- unabhaengig davon, ob die Runde noch 20 Zuege hat oder 2.

### Drei Bauformen, und eine davon ist eine Falle

**C1 -- echte Tiefe bis zum Rundenende.** Der Baum laeuft, bis seine Blaetter das Rundenende
erreichen, statt bis zu einer Sim-Zahl. Das ist die woertliche Umsetzung von "Rundensicht".
*Preis:* stellungsabhaengig und im schlimmsten Fall enorm -- frueh in der Runde steht eine
Verzweigung ueber viele Zuege, spaet ist es fast gratis. Ein Kostentor ist hier PFLICHT.

**C2 -- Rundenloeser als Bewerter.** Statt `v_mix` des Baums den exakten
`tiling_solver::solve_round_final_score` des Folgezustands nehmen. *Billig, rundensichtig --
und eine FALLE.* Genau diese Bauform ist in der Nacht zum 2026-09-15 an K4 gescheitert
(`PREREG_round_estimate_leaf_term.md` par.7c/7d): ein Term, der den RUNDENSCORE an die
Bewertung haengt, macht die Suche rundenscore-gierig. Gemessen: Strafleiste runter, volle Zeilen
hoch, Spalten (-0,84) und Spezialfelder (-0,59) eingebrochen, unter dem Strich 8 bis 14 Punkte
je Partie VERLOREN. **C2 wird nicht gebaut.** Wer Rundensicht will, darf sie nicht mit
Rundenscore-Optimierung verwechseln -- der Value-Kopf schaetzt den PARTIEausgang, und genau das
soll er behalten.

**C3 -- Budget an die Restlaenge koppeln.** `sims` je Variante proportional zur Zahl der noch
offenen Zuege der Runde. Das ist keine Terminierung, sondern adaptives Budget: es verschiebt
Rechenzeit dorthin, wo noch etwas passiert. Billiger als C1, ohne C2s Zielverschiebung.

> **NACHTRAG 2026-09-15, nach par.12.0 (Rueckwaerts-Pruefung): die Prioritaet von Weg C faellt.**
> Dieser Absatz ist geschrieben worden, als der Horizont die naechstliegende Erklaerung war.
> par.12.0 hat seither am Code belegt, dass das Trainingsziel des `moon`-Kopfs ein No-Op ist --
> das Label war IMMER die kanonische Reihenfolge, und der Kopf hat mit Gewicht 1,0 darauf
> trainiert. **Damit gibt es eine dritte Erklaerung fuer den Nullbefund aus par.9h, und sie ist
> billiger zu pruefen als C:** der Prior, der die Kandidaten der Nachsuche vorordnet, ist auf
> eine Konstante gelernt. Die Reihenfolge des Fahrplans ist entsprechend geaendert -- 32b
> (b05 ohne Bau, danach b04) und die Sonden aus 32c stehen VOR 32a. Der Knopf C3 bleibt gebaut
> und vorregistriert; seine Tore sind offen, nicht gescheitert.
>
> Was der Befund NICHT umstoesst: `changed` = 0,623 aus par.9i bleibt gueltig und bekommt sogar
> eine schaerfere Lesart -- wenn der Prior auf "kanonisch" gelernt ist, ist diese Zahl der
> Anteil, in dem der BAUM den Prior ueberstimmt.

**Empfehlung innerhalb von Weg C: C3 zuerst, C1 nur wenn C3 traegt.** Begruendung: C3 testet dieselbe These
("mehr Weitsicht hilft") mit einem Bruchteil des Aufwands und ohne Terminierungslogik im
Suchpfad. Traegt C3 nicht, ist auch C1 unwahrscheinlich -- traegt es, lohnt C1 als Ausbau.

### Tore (bindend, VOR dem A/B)

1. **Bitidentitaet bei aus:** `moon_order_variants != 2` unveraendert, kein Netzaufruf, keine
   Zahl aus dem Suchstrom. Beleg: Anker-Drift gruen plus Kontrakt-Hash unveraendert.
2. **Kostentor, Schwelle 25 Prozent** (Muster K4 par.5 Punkt 3): Wanduhr je Partie mit gegen
   ohne, zwei Laeufe mit identischen Specs je Seite. Ein gerissenes Tor beendet den Arm.
   Bezugswert ist die heutige Nachsuche (14,93 s je Partie beidseitig, par.9i), NICHT die
   Basislinie ohne Nachsuche.
3. **Diagnose:** `changed` und `applied` aus par.9g muessen weiterhin fallen; steigt `changed`
   deutlich ueber 0,62, waehlt die Nachsuche mit mehr Horizont ANDERS als vorher -- das ist die
   Voraussetzung dafuer, dass ueberhaupt ein Staerkeeffekt moeglich ist. Bleibt `changed`
   gleich, hat der Horizont die Wahl nicht veraendert und der Arm ist ohne A/B beendet.

### Lesart vorab

Traegt C3 gepaart ueber der Aufloesung (200 Paare, Blockgroesse 5, kein Frueh-Stopp), ist der
Horizont die Ursache und Weg A wird nicht gebraucht. Traegt es nicht UND `changed` hat sich
bewegt, bleibt allein Weg A (eigener Entscheidungsknoten) -- dann ist die Entscheidungsform das
Problem, nicht die Information. Traegt es nicht und `changed` bleibt gleich, ist der Knopf
wirkungslos gebaut und Tor 3 hat das schon vor dem A/B gesagt.

## par.12 ARCHITEKTUR KONKRETISIERT (Code-Audit 2026-09-15, Nutzer-Auftrag "konkretisiere moegliche architektur optimierungen")

Kein Bau, kein Entscheid. Dieser Absatz macht aus den drei Wegen von par.10 baubare Stuecke mit
Codestellen, Kosten, Toren und Reihenfolge -- und er beginnt mit einem Befund, der die Lesart
von par.2, par.7 und par.9e aendert.

### 12.0 BEFUND: das Trainingsziel des `moon`-Kopfs ist ein No-Op (am Code geprueft)

`moon_order_target` (`self_play.rs:1331-1386`) zaehlt alle Permutationen der Reststeine auf
(`permutations`, `:1389-1403`; das erste Element ist die IDENTITAET, also die Sonnenseiten-
Reihenfolge ohne die genommene Farbe -- dieselbe Folge, die `validation.rs:177-183` als
kanonische Reihenfolge erzeugt), wendet jede auf einer Spielkopie an und bewertet mit
`solve_round_final_score(&g.state, pi)` (`:1378`). Diese Funktion liest **nur das Brett des
Spielers**: `tiling_solver.rs:497` -> `cached_plain` (`:404`, Cache-Schluessel
`tiling_key(&state.players[pi])`, `:301-329`) -> `compute_plain` (`:396-401`: `p.score`,
Strafleiste, Startspielermarker, `solve_max_tiling_points`). Der Modulkopf sagt es selbst:
`tiling_solver.rs:249` fuehrt `state.factories` unter dem, was der Loeser ABSICHTLICH nicht
liest. Die Mondreihenfolge lebt aber in `state.factories[..].moon_stacks` (`factory.rs:11`,
`execution.rs:154`).

**Folge:** alle Permutationen scoren identisch, `score > best_score` greift nur beim ersten
Element, das Ziel ist IMMER die kanonische Reihenfolge. Der Kopf (5 Logits,
`neural_net.py:1702-1710`) trainiert mit Plackett-Luce-NLL (`train.py:125-149`) und Gewicht 1,0
(`moon_loss_weight` in den Manifesten v28-b02, v29-b01, v29-b02, v29-b03, alle 1,0) darauf, die
Sonnenseiten-Reihenfolge zu reproduzieren -- eine Groesse ohne jeden Bezug zum Wert der Stellung.

**Das war bekannt und ist nie entschieden worden:** `PREREG_implementation_review_unprimed.md`
Befund 2 (2026-08-20) und der Kommentar in `train.py` (Zeilen um 555) sagen genau das; die
"Behebung" war der Abschaltknopf `--moon-loss-weight`, der seither auf 1,0 steht. par.2 dieser
Datei beschreibt das Ziel dagegen als "beste Reihenfolge nach `solve_round_final_score` ...
ERSCHOEPFEND" -- die Aufzaehlung ist erschoepfend, der Bewerter ist blind. par.9e nennt den
Prior "kurzsichtig"; er ist nicht kurzsichtig, er ist blind.

**Was das fuer die drei Messungen heisst (Herleitung, nicht gemessen):**

- **Stufe 1 (par.7, Fan-out):** P(Reihenfolge) = Plackett-Luce ueber Kopf-Scores, die die
  kanonische Folge bevorzugen (`net_mcts.rs:2453-2467`). Die Prior-Masse liegt damit auf dem
  kanonischen Kind; an der Wurzel werden nur 16 Kandidaten gerankt. Ein Nullbefund gegen
  "Fan-out aus" ist unter diesem Prior die ERWARTUNG, nicht ein Befund ueber die Reihenfolge.
  Messbar in Minuten: Anteil der Prior-Masse auf der kanonischen Variante an Fan-out-Knoten
  (Diagnose-Zaehler, kein Umbau).
- **Stufe 3 (par.9h):** der Prior ordnet nur vor (`:5645-5652`), entscheidet tut das Minimum
  von `v_mix`; par.9i zeigt 62 Prozent Abweichung -- Stufe 3 haengt also NICHT am Kopf. Der
  Nullbefund dort bleibt ein Befund ueber Horizont oder Hebelwirkung (12.3).
- **Weg B (par.10) ist damit kein "Zielwechsel", sondern eine REPARATUR.** Die Frage "Rundenende
  gegen Partieausgang" stellt sich erst, wenn das Ziel ueberhaupt etwas misst.

**Konsumenten dieser Korrektur (Rueckwaerts-Pruefung, zu lesen vor jedem Nachzug):** par.2 und
par.9e hier; `PREREG_dome_return_order.md` par.2 (Notiz zum Mondkopf); der Registratur-Text von
`MOSAIC_MOON_ORDER_VARIANTS` in `engine/src/knob_registry.rs` und damit `docs/knobs.md`
("Trainingsziel ... beste Reihenfolge nach solve_round_final_score" -- sachlich falsch, Nachzug
braucht einen Build, weil `knobs.md` generiert wird); `archive/history.md` Task #38.

### 12.1 Weg B konkret: Reparatur des Ziels, Arm `v29-b04`

Drei Zielquellen, nach Kosten geordnet:

| Quelle | Was ist das Label | Braucht neue Erzeugung? | Guete |
| --- | --- | --- | --- |
| **B1 gespielte Reihenfolge** | `action.moon_order` steht in JEDEM Record (`self_play.rs:226-235`, als Debug-Feld geschrieben, von `action_to_id` nicht gelesen). Im v29-Korpus (Fan-out Variante 1, 100 Sims) ist sie die Besuchs-Argmax-Wahl unter bis zu 6 Kindern, also ein SUCH-Label | **nein** -- das v29-Fenster traegt es | begrenzt durch den blinden Prior: bei 100 Sims folgt die Suche oft dem kanonischen Kind |
| **B2 Nachsuche-Reihenfolge** | dasselbe Feld, aber aus einer Erzeugung mit `moon_order_variants=2` (par.9): die gespielte Folge ist dann die Wahl der 256-Sim-Nachsuche | **ja** (v30-Erzeugung, +21 Prozent Wanduhr je par.9i) | bestes verfuegbares Label; Kosten stellen sich erst mit C3/C1 (par.11) |
| B3 exakte 1-Zug-Zugriffsregel | Handregel "welche Farbe oben dem Gegner nutzt" | nein | NICHT empfohlen: eine Handregel als Ziel deckelt den Kopf auf Handregel-Niveau (Lehre aus `dome_return_order` Modus 2) |

**Vorschlag: B1 jetzt, B2 mit v30.** Schritte fuer B1:

1. **Korpus-Sonde zuerst (Minuten, kein Bau):** Anteil der Sonnenzuege aus kleinen Fabriken mit
   mindestens zwei eindeutigen Reihenfolgen, deren gespielte `moon_order` von der kanonischen
   abweicht (n = Records mit `moon_order_target != null`, Grundmenge v29-Fenster, Einheit
   Anteil). Liegt er unter rund 10 Prozent, ist B1 selbst ein Henne-Ei (das Label waere fast
   immer kanonisch) und es bleibt nur B2. Zwischen 10 und 50 Prozent: B1 fahren. Die Zahl
   gehoert VOR den Arm, nicht in seine Deutung.
2. **Datenpfad:** `corpus_dataset.py:1351-1358` baut den Rang-Vektor aus `moon_order_target`;
   Umstellung auf `action.moon_order` (Rang = Position im gespielten Vektor, `-1` fuer Farben,
   die nicht im Rest sind). Kein Aenderung am Kopf, an der Loss (`plackett_luce_moon_loss`) oder an
   `NUM_ACTIONS`. Der Knopf heisst z. B. `--moon-target-source {solver,played}`, Default `solver`
   = Bestand (bitidentischer Cache-Schluessel; `played` gehoert in den Fenster-Schluessel, Lehre
   `feedback_feature_knob_belongs_in_both_cache_keys`).
3. **Arm `v29-b04`** = Rezept von b03 (794, Warmstart `v28-b02_brierbest`, Seed 20260941,
   12 Epochen) plus `--moon-target-source played`. Name ab b04 ist reserviert
   (`docs/generation_naming.md` Z.165), eigene Registrierung hier.
4. **Tore:** (a) Offline: `moon_nll` auf dem sauberen Val-Cache muss unter dem b03-Wert liegen --
   sonst hat der Kopf das neue Ziel nicht gelernt und der Arm ist ohne Arena beendet; (b)
   Diagnose: Prior-Masse auf der kanonischen Variante an Fan-out-Knoten faellt gegenueber b03
   (Zaehler aus 12.0); (c) Tor 1 gepaart gegen b03, zwei Seeds, Blockgroesse 5, 200 Paare ohne
   Frueh-Stopp (Lehre par.10a von `special_tile_yield`: 30 Paare mit Stopp reichten nicht).
5. **Lesart vorab:** traegt b04 in (c), war der blinde Prior eine Ursache und Stufe 1 ist am
   reparierten Netz neu zu messen (par.7 wiederholen, Fan-out an gegen aus). Traegt b04 nicht,
   obwohl (a) und (b) gruen sind, ist der Prior NICHT der Hebel; dann ist `moon_loss_weight 0`
   der billigere Kandidat (die Behauptung aus Task #38, der Kopf ziehe rund ein Drittel des
   Policy-Gradienten, ist UNGEPRUEFT und waere vorher an einem Gradienten-Log zu belegen).

**Was B nicht anfasst:** kein neuer Kopf (`feedback_no_new_heads`), kein Kontrakt-Wechsel, alle
Checkpoints bleiben spielbar. Kosten: Datenpfad rund 1 h Bau (ANNAHME), Training 1,4 h
(gemessen), Tor 1 2 x 86-91 min (gemessen).

**ENTSCHIEDEN 2026-09-15 (Nutzer: "beides. trag es in den fahrplan ein."): B1 UND die
Ablation, als zwei Arme mit eigener Nummer** (`feedback_measured_identity_gets_own_bxx`):

| Arm | Rezept | Was er beantwortet | Voraussetzung |
| --- | --- | --- | --- |
| **`v29-b04`** | b03 plus `--moon-target-source played` (B1) | traegt ein Kopf mit ECHTEM Ziel? | Korpus-Sonde ueber 10 Prozent; Datenpfad gebaut; Monolith unter eigenem Fenster-Schluessel (die Zielquelle aendert die Daten) |
| **`v29-b05`** | b03 plus `--moon-loss-weight 0` | kostete das Rauschziel Policy-Qualitaet? (Task-#38-Behauptung, bisher ungemessen) | keine -- der Knopf existiert (`train.py:575`), das Gewicht ist kein Daten-Schluessel, b03s 794er-Monolith reicht |

Reihenfolge: **b05 zuerst** (kein Bau, kann sofort auf die GPU), b04 nach Korpus-Sonde und
Datenpfad. Tore je Arm wie oben Punkt 4, Bezugspunkt beide Male **b03** (gleicher Eingang 794,
gleiches Fenster). Registriert in `docs/generation_naming.md` (v29-Abschnitt) und im Fahrplan
als 32b. Lesart der vier Ausgaenge: b04 traegt -> Prior war eine Ursache, Stufe 1 am reparierten
Netz wiederholen; nur b05 traegt -> das Ziel war Ballast, der Kopf geht auf Gewicht 0 ins
Rezept; beide tragen -> b04 gegen b05 als Stichentscheid; keiner traegt -> der Kopf ist kein
Hebel, es bleiben Horizont (12.4) und Hebelwirkung (12.3).

### 12.2 Weg A konkret: eigener Entscheidungsknoten -- und warum er ausserhalb des v30-Rahmens liegt

**Bauform, aus dem Praezedenzfall `ChooseDomeRotation` abgeleitet** (`moves.rs:121-124`,
`state.rs:100` `pending_dome_choice`, `game.rs:790-842`: kein Phasenwechsel, kein
`switch_player()` bis zur letzten Stufe; `drafting_actions` liefert bei anhaengiger Wahl NUR die
Stufe-2-Kandidaten, `game.rs:642-667`):

1. **Zustand:** `pending_moon_order: Option<PendingMoonOrder { factory_id, remaining: Vec<TileColor> }>`
   analog `pending_dome_choice`. `Action::Stone` aus einer kleinen Fabrik legt die Reststeine
   zunaechst NICHT ab, sondern setzt den Marker, sobald `unique_moon_orders(remaining).len() >= 2`;
   sonst kanonisch wie heute (bitidentisch fuer den Ein-Varianten-Fall).
2. **Zug:** `Action::ChooseMoonTop(TileColor)` = "diese Farbe liegt als naechste OBEN". Bei drei
   verschiedenen Farben zwei Entscheide hintereinander (oben, dann Mitte; der Rest ist bestimmt),
   bei zwei verschiedenen einer. `switch_player()` erst nach dem letzten.
3. **Aktions-IDs:** 5 neue IDs 406..410 (Farbe), `NUM_ACTIONS` 406 -> 411 (`net_mcts.rs:54`,
   `features.rs:1920-1966`, `KNOWN_ACTION_TYPES` plus Python-Spiegel
   `tools/tests/test_action_id_mirror.py`). Dieselbe ID-Familie fuer beide Stufen, wie die vier
   Rotations-IDs fuer beide Kuppelpfade (`features.rs:1956`).
4. **Prior und Ziel:** aus der normalen Policy, Ziel = Besuchsverteilung am Knoten
   (`policy_target_valid`-Muster). Der `moon`-Kopf wird ueberfluessig (Gewicht 0, Ausgang bleibt
   fuer die ONNX-Form).
5. **Suche:** `player_who_acted` wird vor dem Apply gelesen (`net_mcts.rs:5476-5490`), Backups
   laufen fuer denselben Spieler ueber beide Kanten -- die Kuppelrotation zeigt, dass der Baum
   dafuer keine Sonderbehandlung braucht.

**Preis, und er ist der Grund gegen A in diesem Projekt:**

- `NUM_ACTIONS` aendert sich -> **jeder bestehende Checkpoint ist fuer Live-Inferenz verwaist**
  (`feedback_num_actions_change_breaks_old_checkpoints`: `net.rs::Net::eval` liest Ausgaben
  positional, alte Policy-Gewichte waeren 406 breit). Champion, Anker-Kader, Leiter: alles
  Cross-Aera mit Rueckfall.
- **Abmilderung "additiver Policy-Kopf"** (dieselbe Regel wie beim 2D-Encoder,
  `project_2d_encoder_must_be_additive`): die Engine liest die Policy-Breite aus dem ONNX; ein
  406er-Modell bekommt nie einen Mondknoten (Rueckfall kanonisch), ein 411er schon; der
  Warmstart polstert 5 Nullzeilen. Damit bleiben alte Netze SPIELBAR und vergleichbar -- aber
  nur mit kanonischer Reihenfolge, also genau ohne das, was gemessen werden soll.
- Der Korpus muss die Knoten TRAGEN, bevor ein Netz sie lernen kann
  (`feedback_record_field_must_precede_generation`): fruehestens die v30-Erzeugung liefert
  Records mit `ChooseMoonTop`, fruehestens ein v31-Training koennte sie nutzen. **v30 ist die
  letzte Generation und traegt nur Rezept-Knoepfe** (`project_v30_release_close`). Weg A
  passt damit nicht in den Rahmen; ihn zu oeffnen ist ein Nutzer-Entscheid, kein Fahrplanpunkt.
- Wenn ueberhaupt, dann GEBUENDELT mit der Rueckgabe-Reihenfolge (`dome_return_order` par.12
  R3, 3 weitere IDs -> 414); zwei Kontraktwechsel waeren zwei Verwaisungen.

### 12.3 Instrument VOR jedem weiteren Bau: die Zugriffs-Bilanz (Fahrplan 32c)

Die Nachsuche waehlt zu 62 Prozent anders und aendert nichts (par.9i). Neben Horizont (C) und
Prior (B) gibt es eine dritte, bisher ungemessene Erklaerung: **der Hebel ist klein, weil der
oben gelegte Stein selten den Besitzer wechselt.** Das ist mit vorhandenen Logs pruefbar, ohne
Engine-Aenderung:

- **Sonde** `tools/probes/moon_order_access_probe.py` ueber `--log-games`-Artefakte
  (`moon_order_post_vs_off_s20261091`, die K4-Laeufe): je Mondstapel-Entscheid (Grundmenge:
  Sonnenzuege aus kleinen Fabriken mit mindestens zwei eindeutigen Reihenfolgen, wie der
  Zaehler in `moon_order_post_search`) -- WER nimmt den oben gelegten Stein als naechstes
  (Waehler, Gegner, niemand vor Rundenende) und WIE VIELE Halbzuege spaeter; dazu, ob der
  darunter liegende Stein in derselben Runde noch erreicht wird. Parser-Falle par.9i beachten:
  die Zeile `Mond-Stapel:` ist ein ZUSTAND; Ereignis ist der Zug C (`take_from_moon`,
  `factory.rs:96-107`), also die Log-Zeile des Mondzugs.
- **Lesart vorab:** nimmt der Gegner den oben gelegten Stein in weniger als rund einem Viertel
  der Faelle im naechsten Halbzug, steuert die Reihenfolge den Zugriff nur selten -- dann ist
  ein kleiner Effekt die Wahrheit ueber das Spiel und weder C1 noch A lohnen. Nimmt er ihn in
  mehr als der Haelfte, ist der Hebel real und Horizont (C) die naechste Frage.
- Kosten: Bau rund 1 h (ANNAHME), Lauf Sekunden. Kein Nutzer-Entscheid noetig, weil nichts
  gebaut wird, das spielt.

### 12.4 Weg C: Stand und Rest

C3 (Budget skaliert mit der Restlaenge) ist gebaut (Commit a4f92a5, Knopf
`MOSAIC_MOON_ORDER_SEARCH_SCALE`, Tore par.11 offen). C1 (echte Terminierung am Rundenende) nur,
wenn C3 `changed` deutlich ueber 0,62 hebt UND das A/B traegt (par.11 Tor 3) -- sonst ist mehr
Horizont nicht die Antwort.

### 12.5 Reihenfolge, zusammengefasst

1. **12.3 Zugriffs-Bilanz** (Sekunden) und **12.1 Korpus-Sonde** (Minuten) -- beide ohne Bau am
   Spiel, beide entscheiden, ob 2 und 3 lohnen.
2. **C3-Tore und A/B** (par.11, laeuft im Fahrplan als 32a).
3. **`v29-b05`** (Gewicht 0, sofort) und **`v29-b04`** (B1, nach Korpus-Sonde ueber 10 Prozent) -- beide
   ENTSCHIEDEN 2026-09-15 (12.1).
4. **B2** mit der v30-Erzeugung (Variante 2 oder C3 in der Erzeugung, Nutzer-Entscheid ueber die
   Kosten).
5. **A** nur nach Nutzer-Entscheid ueber den Rahmen, gebuendelt mit `dome_return_order` R3.
