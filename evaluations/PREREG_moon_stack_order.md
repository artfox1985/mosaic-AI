<!-- STATUS: OFFEN | Frage: Die Reihenfolge der Mondsteine nach einem Sonnenzug ist im Netzpfad seit 2026-07-01 ein Suchentscheid (Varianten mit Prior aus dem Moon-Order-Kopf). Traegt das, und ist das Trainingsziel des Kopfs das richtige? | Beleg: nichts gemessen. Bestand par.2 (Code geprueft 2026-09-12). EINGETAKTET als v29/v30-Begleitprogramm (Nutzer 2026-09-12): A/B Fan-out an gegen aus am Champion (par.4), danach Zielfrage (par.5). -->

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
  (der erste Sonnenzug aus der Fabrik legt den Stapel), also hoechstens 4 je Runde und 20 je
  Partie, real weniger (Rest >= 2 noetig). Der Posten ist damit von vornherein klein. Im Korpus `selfplay_v27-b01-policy_..._g10.pkl`
  tragen 199 von 1.675 Records ein Ziel (Sonnenzuege aus kleinen Fabriken mit Rest >= 2).
- **Korrektur einer Notiz:** `PREREG_dome_return_order.md` par.2 nennt `moon_order` "kanonisch
  und keine Wahl des Netzes". Das gilt fuer `self_play.rs:234` (Aktionsraum/Record) und fuer den
  Heuristik-Pfad, NICHT fuer die Netzsuche. Dort korrigiert.

## par.3 Hypothesen (VOR jeder Messung)

- **H1:** der Fan-out traegt messbar: Champion mit Varianten gegen denselben Champion mit
  kanonischer Reihenfolge (Fan-out AUS) gewinnt gepaart. Gegenhypothese: die Reihenfolge ist im
  Duell fast immer irrelevant (Mondsteine werden ohnehin komplett gezogen), der Fan-out kostet nur
  Suchbudget (bis zu 6 Kinder statt 1 je Sonnenzug).
- **Erwartung:** klein, wegen der Haeufigkeit (par.2); ein Nullbefund bei 200 Paaren ist der
  wahrscheinliche Ausgang und dann ein vollwertiges Ergebnis (Fan-out bleibt aus Gruenden der
  Vollstaendigkeit).
- **H2:** das Rundenloeser-Ziel ist kurzsichtig (Rundenende statt Partieausgang); ein Ziel aus der SUCHE (die vom Baum gewaehlte
  Reihenfolge, wie beim Rueckgabe-Knopf Modus 1 gedacht) oder aus dem Ausgang traegt mehr.
  Nur pruefbar nach H1 und nur mit Training (ein Arm).

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

## par.7 Ergebnisse (leer bis zur Messung)

Nichts gemessen (Stand 2026-09-12, 13:20).
