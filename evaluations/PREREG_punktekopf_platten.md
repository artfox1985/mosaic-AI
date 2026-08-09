# Vorregistrierung: Reagiert der PUNKTE-Kopf auf die Wertungsplatten?

**Angelegt 2026-08-09, VOR der Messung.** Anlass: Nutzer-Partie
`game_20260809_115404_seed704874` (Grundpunkte 51:51, Endwertung 18
gegen -2, also 69:49 -- Diagonalen 10:0, leere Spezialfelder -3 gegen
-12). Nutzer-Argument, das den Task ausloest: *"eigentlich sollte der
point head auch reagieren. durch die kombination aus wertungsplatten zum
schluss und strategischem aufbau der reihen/spalten während den runden
maximieren wir die punkteanzahl"* -- und das ist strukturell gedeckt:
das Trainingsziel des Punkte-Kopfes ist
`own_total = step["scores"][Spieler]`, laut Kommentar in
`engine/py/neural_net.py:474` **bereits inklusive Wertungsplatten**.
Der Kopf ist also darauf trainiert, die Platten einzupreisen. Gemessen
wurde das nie: alle bisherigen Platten-Instrumente lesen `root_value`.

## Die GEGNER-Richtung ist gleichrangig Teil des Tasks

Nutzer-Ergaenzung (2026-08-09): *"weil es geht dann auch anders herum.
ich kann schauen dass mein gegner seine wertungsplatten nicht erreicht
oder strafpunkte durch die -3 platte bekommt."* Das ist strukturell
genauso gedeckt wie die eigene Richtung -- und wir haben dafuer einen
eigenen Kopf: `opp_points_head` (Task #28) mit dem Ziel
`opp_points_val = tanh(opp_total / VALUE_SCALE)`, wobei `opp_total`
aus derselben `step["scores"]`-Quelle stammt wie `own_total` und damit
**ebenfalls die Wertungsplatten enthaelt** (inkl. der -3 je leerem
Spezialfeld, Platte 6). `opp_points_forecast` liegt in `value_debug`
bereits vor.

Die Gegner-Richtung wird deshalb in BEIDEN Stufen gleichrangig
mitgemessen (nicht als Beigabe), mit denselben Schwellen. Zwei
Anschluesse, die davon abhaengen:

- **Der Aggressions-Blend** (`MOSAIC_POINTS_UTILITY_W` w,
  `MOSAIC_AGGR_LAMBDA` λ) ist der EINZIGE gebaute Weg, ueber den der
  opp-Kopf die Suche beeinflusst -- er steht nach der Neukartierung
  ueberall auf w=0, weil alle drei Arme H0 ergaben. Diese Messung war
  aber auf die allgemeine PUNKTE-MARGE gerichtet, nicht auf
  plattenspezifisches Verhindern. Ergibt Stufe 2 fuer den opp-Kopf eine
  ZUG-DIFFERENZIERUNG nach Platten, ist das ein NEUES Argument fuer
  w>0 und kein Wiederaufguss -- dann aber mit eigener Vorregistrierung
  und Arena-Entscheid, nicht durch Analogieschluss.
- **E3b** (laeuft gerade als Stufe 2) waehlt unter gleichwertigen
  Kandidaten den mit der NIEDRIGSTEN Gegner-Punkteprognose. Das ist
  bereits Verhinderung -- aber ueber die GESAMT-Prognose, nicht
  plattenspezifisch. Ein plattenbewusster Zuschnitt waere die
  schaerfere Variante; ob er lohnt, entscheidet erst dieses Ergebnis
  zusammen mit dem E3b-Verdikt.

## Was schon bekannt ist (und die Fallgrube definiert)

| Befund | Quelle |
|---|---|
| `mcts_visits` aendert sich bei Plattenwechsel NIE (JS 0,0 in 124/124) | Teil 3 (v16), in v21 reproduziert |
| Die TATSAECHLICHE Zugwahl kippt aber in **29,0%** (36/124) der Faelle | `plate_rank_invariance_v21.json`; v16 29,8%, v17 23,4% -- aera-stabil |
| Mechanismus: Sequential Halving laesst die Top-2 mit GLEICHEN Besuchszahlen enden, `gumbel_final_root_action` entscheidet dann per `ln(prior) + sigma(Q)` | Task #5, 2026-07-27 |
| Value-Kopf reagiert auf Plattenkombinationen: Streuung 0,0694 vs Seed-Rauschboden 0,0147 = **4,7x** | `scoring_tile_sensitivity_v21.json` |
| Der gebaute `PLATE_SHAPING`-Hebel blieb folgenlos (+2,4pp, n.s.) -- Begruendung in der Historie: **globaler Root-Value-Shift, der sich im Ranking wegkuerzt** | Task #5 Teil 1c |

**Die Fallgrube ist damit benannt**: eine Groesse, die sich bei
Plattenwechsel bewegt, aber ALLE Kandidatenzuege gemeinsam bewegt
(NIVEAU-Verschiebung), ist fuer die Zugwahl wertlos -- sie kuerzt sich
im Ranking weg. Genau daran ist Plate-Shaping gescheitert, und genau
das kann die 4,7x-Zahl des Value-Kopfes ebenfalls sein (unentschieden,
weil bisher nur an der WURZEL gemessen). Eine Messung, die nur
"reagiert der Punkte-Kopf ueberhaupt?" beantwortet, wiederholte diesen
Fehler. Deshalb zwei Stufen, und die ENTSCHEIDUNG liegt in Stufe 2.

## Stufe 1 (jetzt, KEIN Code noetig): traegt der Kopf Platten-Information?

`value_debug` aus `net_search_state_json_trace` enthaelt bereits
`points_forecast` und `opp_points_forecast` (`RootValueDebug`,
`net_mcts.rs`). Erhebung additiv im BESTEHENDEN Lauf von
`tools/plate_rank_invariance.py` (16 Zustaende x 8 Kombinationen,
Champion @400 Sims, Seed 1000) -- derselbe Suchlauf, der die Kipprate
misst, kein zusaetzliches Rechenbudget.

- Groesse: Spannweite von `points_forecast` ueber die 8 Kombinationen je
  Zustand.
- Rauschboden: dieselbe Kombination mit zwei verschiedenen Seeds (der
  Seed mischt die ECHT verdeckte Information neu -- identisches
  Protokoll wie beim `root_value`-Rauschboden).
- **Kennzahl: Verhaeltnis Platten-Spannweite / Seed-Rauschboden**, plus
  dieselbe Zahl fuer `opp_points_forecast` und (als Referenz)
  `raw_value`.

**Regel 1a**: Verhaeltnis **>= 3** ⇒ der Punkte-Kopf traegt
Platten-Information, Stufe 2 wird gefahren.
**Regel 1b**: Verhaeltnis **< 3** ⇒ der Kopf hat die Platten trotz
plattenhaltigem Ziel NICHT gelernt. Das ist ein eigenstaendiger Befund
und verschiebt die Frage auf die TRAININGSSEITE (Credit-Assignment),
nicht auf die Suche. Stufe 2 entfaellt.
**Regel 1c (Vorab-Warnung, keine Entscheidung)**: Ein Bestehen von
Stufe 1 heisst NICHT, dass der Kopf ein Hebel ist -- siehe Fallgrube.
Ein positives Stufe-1-Ergebnis darf NICHT als "Punkte-Kopf
beruecksichtigt die Platten" berichtet werden, sondern nur als
"Punkte-Kopf traegt Platten-Information an der Wurzel".

## Stufe 2 (nur bei Regel 1a): NIVEAU oder ZUG-DIFFERENZIERUNG?

Braucht eine **additive** Rust-Ergaenzung: die je Kandidat vom Netz
berechneten Kopf-Ausgaben (`value` / `points` / `opp_points` am
KINDzustand) im `gumbel_trace` mitprotokollieren. Der Suchlauf
evaluiert diese Kinder ohnehin, es fehlt nur die Aufzeichnung.
Bedingungen: neue Felder additiv, Default-Verhalten byte-identisch,
**Paritaets-Hash muss
`8c6684ffba06cf3e16e898b83325f3154c04efac555c8e862c079b71155bd423`
bleiben**, Tests gruen.

Auswertung je Zustand und Kombination: Vektor der Kopf-Ausgaben ueber
die Kandidaten in **NIVEAU** (Mittelwert) und **ZENTRIERT**
(Vektor minus Mittelwert -- nur dieser Teil ist rangrelevant) zerlegen.

- **Entscheidungsmetrik: Kendall-Tau der Kandidaten-Reihenfolge nach
  `points_forecast` zwischen den Plattenkombinationen** (Median ueber
  Zustaende), plus Spannweite des ZENTRIERTEN Anteils gegen denselben
  Seed-Rauschboden.
- **Regel 2a**: Tau-Median **< 0,9** UND zentrierte Spannweite
  **>= 3x** Rauschboden ⇒ der Punkte-Kopf differenziert die ZUEGE nach
  Platten. Dann ist er ein echter Hebel-Kandidat, und der Folgeschritt
  ist eine eigene Vorregistrierung fuer sein Gewicht im Suchpfad
  (heute traegt der Value-Kopf den Backup) -- mit Arena-Entscheid, kein
  Offline-Verdikt.
- **Regel 2b**: Tau-Median **>= 0,9** ODER zentrierte Spannweite
  **< 3x** ⇒ der Kopf ist plattenbewusst, aber nur im NIVEAU. Dann ist
  er als Suchpfad-Hebel TOT (derselbe Grund wie bei Plate-Shaping),
  und der Punkt wird geschlossen mit der Konsequenz: die Plattenwirkung
  muss zug-differenzierend ins TRAINING gebracht werden.
- **Pflicht-Beigabe**: dieselbe Zerlegung fuer `raw_value`. Damit ist
  nachtraeglich geklaert, ob die heute gemessenen 4,7x des Value-Kopfes
  Niveau oder Differenzierung sind -- eine offene Frage, die diese
  Messung gratis mitbeantwortet.

## Was NICHT Teil dieses Tasks ist

- Kein Plate-Shaping-Wiederaufguss (2026-07-27 gemessen, folgenlos, und
  der Grund ist strukturell verstanden).
- Keine Encoder-Aenderung. Die Beobachtung "6 von 8 Platten haben eine
  gattierte 2D-Ebene, die Platten 3 (Mehrfarbige Felder) und 6
  (Spezialfelder) nicht" ist notiert, aber KEIN Befund: die Diagonalen
  (Platte 2) HABEN eine Ebene und gingen in der Nutzer-Partie trotzdem
  0:10 verloren -- das spricht gegen die Encoder-Erklaerung als
  Hauptursache.
- Keine Aenderung an Suchreglern. Die Wurzel-Regler-Familie hat in
  dieser Sitzung zweimal H0 und einmal Schaden geliefert.
