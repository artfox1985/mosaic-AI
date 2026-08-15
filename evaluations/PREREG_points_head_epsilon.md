<!-- STATUS: ENTSCHIEDEN | Frage: Warum trug das Punkte-Ziel einen 0,1-Gegner-Anteil, und braucht es neben dem Punkte-Kopf ueberhaupt einen eigenen Gegner-Kopf? | Beleg: **ENTSCHIEDEN 2026-08-10** (Nutzer-Auftrag): Anteil ENTFERNT, Schema 19->20, Epsilon auf 0. Zum Gegner-Kopf: kein Faehigkeits-Argument (die Eingabe ist perspektiv-normalisiert, ein Flip genuegt), sondern nur ein KOSTEN-Argument (zweiter Forward-Pass = 1,6-1,8x) -- und dessen Bedingung ist falsch, weil `blended_leaf_win_prob_with` bei w=0 zurueckkehrt, bevor er gelesen wird. Verdikt: reines Hilfsziel, Nutzen UNBELEGT, Messung vorgeschlagen; Praezedenz `ownership_head`. -->

# Entscheidung: Gegner-Anteil aus dem Punkte-Ziel entfernt (Schema 20)

**2026-08-10, Nutzer-Auftrag** — *"nimm aus dem point head den kleinen anteil
von den gegner punkten raus. und dann erklärst mir wirklich stichhaltig warum
wir einen eigenen opp head brauchen wenn wir schon einen point head haben der
eigentlich genau das selbe machen sollte (nur halt beim anderen spieler)"*

## Was geändert wurde

Das Ziel des `points_head` war

    points_val = tanh(own_total/VALUE_SCALE) − 0,1 · tanh(opp_total/VALUE_SCALE)

und ist jetzt

    points_val = tanh(own_total/VALUE_SCALE)

An allen drei Stellen, an denen es gebildet wird: Basisformel, `rtv`-Override
und TD-Bootstrap-Blend (`neural_net.py`). `VALUE_SCHEMA_VERSION` 19 → **20**,
weil sich die Zielformel ändert — das ist der Fall, für den der Bump gedacht
ist.

`VALUE_OPP_EPSILON` steht auf beiden Seiten auf **0.0** statt entfernt zu
werden. Grund: dann degeneriert die Rückgewinnung in
`opp_aware_points_utility` automatisch korrekt zu `own_pts = pts_raw`, und
`engine_config_json` zeigt die Änderung an. Dieselbe Praxis wie
`POINTS_UTILITY_WEIGHT = 0.0` direkt darüber. Die Geschichte bleibt im
Kommentar stehen, weil für **vor** Schema 20 trainierte Modelle 0,1 der
richtige Wert wäre.

Drei Tests fielen dabei — die Handrechnungen des Blends. Sie sind neu
gerechnet (u_pts 0,66 → 0,65; Außenblend 0,58 → 0,575) und tragen die alten
Werte als Kommentar, damit die Differenz sichtbar bleibt statt stillschweigend
nachgezogen zu werden. 321 Tests grün.

## Die eigentliche Frage: braucht es den `opp_points_head`?

### 1. Fähigkeit — nein, der Punkte-Kopf kann es schon

Die Netz-Eingabe ist **perspektiv-normalisiert** (`state_to_tensor`:
`me = players[curr_pi]`, dann Gegner). Ein `points_head`, ausgewertet auf
Merkmalen mit dem GEGNER als "ich", liefert exakt dessen Punkteprognose. Der
Code sagt das selbst, `net_mcts.rs:1373`:

> Das Netz liefert einen EGO-perspektivischen Wert ... für den jeweils
> ANDEREN Spieler braucht es deshalb einen zweiten Forward-Pass mit
> geflipptem `current_player`, nicht einfach `1-wert`.

Ein Fähigkeits-Argument für einen eigenen Kopf existiert also nicht.

### 2. Kosten — hier liegt die einzige stichhaltige Begründung

Der Perspektiv-Flip kostet einen **zweiten Forward-Pass** je Blatt. Inferenz
ist 62–81 % der Self-Play-Zeit (Task #81), ein zweiter Pass also ~1,6–1,8×
Gesamtkosten. Ein zusätzlicher Kopf kostet Bruchteile eines Prozents.

**Konditional gilt damit: wird die Gegner-Prognose am Blatt gebraucht, ist ein
eigener Kopf eindeutig richtig.** Ein Pass statt zwei.

### 3. Die Bedingung ist falsch — nichts braucht sie

`blended_leaf_win_prob_with` (`net_mcts.rs:1336`):

```rust
let legacy_blended = (1.0 - POINTS_UTILITY_WEIGHT) * wr + POINTS_UTILITY_WEIGHT * pts;
if w == 0.0 { return legacy_blended; }        // <- Kurzschluss
if opp_points.is_empty() { ... }              // <- wird nie erreicht
```

- `w == 0.0` ist der Default und kehrt zurück, **bevor** `opp_points` gelesen
  wird.
- `POINTS_UTILITY_WEIGHT = 0.0` macht `legacy_blended` numerisch identisch zu
  `wr`, also zum reinen Value-Kopf.

**Beide Punkte-Köpfe werden berechnet und verworfen.** `w = 0` ist zweifach
geschlossen: Aggressions-Neukartierung (alle Arme H0) und
`PREREG_points_blend_w.md` heute (Kontrolle 321/400 gegen Arm 300/400,
Block-Delta −5,25pp, t = −2,68).

### 4. Diese Änderung nimmt die letzte strukturelle Rolle

Die algebraische Rückgewinnung `own_pts = pts_raw + ε·opp_raw` existierte
ausschließlich, um die Epsilon-Verunreinigung des `points_head` zu entfernen.
Mit ε = 0 degeneriert sie zu `own_pts = pts_raw`. **Nach dieser Änderung hat
der `opp_points_head` in der Suche keine Funktion mehr.**

## Verdikt: nicht "löschen", sondern "unbelegt"

Was bleibt, ist eine einzige offene Begründung: als **Hilfsziel** kann er den
gemeinsamen Rumpf verbessern (Multi-Task-Lernen), auch bei Laufzeitgewicht
null. Das ist messbar — und **nie gemessen worden**.

Präzedenzfall im Projekt: `ownership_head` liegt inert mit Gewicht 0 und ist
seit 2026-07-28 geschlossen (Effekt ~1/10 der Auflösung). Ein unbelegter
Hilfskopf ist hier schon einmal so geendet.

**Vorgeschlagene Messung (billig, noch nicht angesetzt)**: ein Trainingsarm
mit und einer ohne `opp_points_head`, identisches Fenster und Rezept,
verglichen an `val_brier` und den arena-validierten Orakel-Metriken
(Prior-Masse Top-3, Kendall-Tau). Bei H0 folgt er `ownership`.

Nicht vergessen: der Kopf ist zugleich das **Instrument** aus
`PREREG_points_head_plates.md` Stufe 2 (Tau-Median 0,640, stärker
plattendifferenzierend als der eigene Punkte-Kopf mit 0,792). Als
Diagnose-Werkzeug hat er sich bezahlt — das ist aber kein Argument dafür, ihn
in jedem Champion mitzuschleppen.

## Kostenhinweis: Cache-Neubau bündeln

Der Schema-Bump 19 → 20 entwertet den vorhandenen Cache, Neubau ~3 h. Der
Plattenkopf braucht ebenfalls einen Neubau (`+plate_v1`). **Beides zusammen
fahren — einmal 3 h statt zweimal.** Ein Trainingsstart vor dem Neubau würde
sonst still auf dem alten Ziel rechnen.

## Was diese Änderung NICHT tut

Bestandsmodelle bleiben ladbar und spielbar — die Kopfform ist unverändert.
Ihr `points_head` bedeutet aber weiter `own − 0,1·opp`, ein nach Schema 20
trainierter bedeutet `own`. Für Vergleiche der `points`-Ausgabe ÜBER diesen
Schnitt hinweg ist das zu beachten; für die Spielstärke nicht, weil die
Ausgabe im Suchpfad ohnehin verworfen wird.

## Nachtrag: Moon-Order ist KEIN Denial-Blindfleck (Nutzer-Korrektur 2026-08-10)

Ich hatte behauptet, `moon_order` sei der eingebaute Denial-Hebel und werde auf
ein Ziel trainiert, das den Gegner nicht kennt -- "Denial kommt im
Trainingssignal ueberhaupt nicht vor". Der Nutzer hat widersprochen
(*"das glaub ich nicht. dafuer haben wir einen eigenen moon order head"*), und
die Pruefung AM CODE (nicht an STATUS, wo ich es hergeholt hatte) gibt ihm
recht.

**Was stimmt**: das LABEL ist selbstbezogen.
`self_play.rs::moon_order_target` waehlt die Permutation mit
`solve_round_final_score(&g.state, pi)`, `pi` = ziehender Spieler -- der Gegner
wird bei der Label-Bildung nie bewertet.

**Was ich uebersehen hatte**: `net_mcts.rs:1241` spannt die Reihenfolgen als
eigene KINDER auf (`unique_moon_orders`), jede Variante bekommt ihren Q-Wert
ueber den Value-Kopf, und der bewertet den Partieausgang -- also gegnerbewusst.
Das Label formt nur den PRIOR, die Entscheidung trifft completed-Q.

**Und es ist praktisch folgenlos**: bei <=3 Restfliesen liefert
`unique_moon_orders` <=6 Varianten (Test `unique_moon_orders_dedups_repeated_colors`),
`GUMBEL_TOP_M` ist 16. Alle Reihenfolgen werden also ohnehin gezogen; der
selbstbezogene Prior hat kaum Raum, eine gute Variante zu verhindern.

**Korrigierte Aussage**: die SORTIERREIHENFOLGE der Kandidaten ist
selbstbezogen gelernt, ihre BEWERTUNG nicht. Moon-Order faellt damit als Hebel
fuer die Nutzer-Frage ("eigene Punkte maximieren UND Gegnerpunkte minimieren,
ohne Differenz") aus. Uebrig bleibt der eine nie gemessene Arm: **lambda <= 0,5**
in `opp_aware_points_utility` -- alle je getesteten Arme lagen bei lambda >= 1,0
und damit jenseits des Kipppunkts, ab dem die Formel 30:15 gegenueber 55:50
bevorzugt.

**Methodische Lehre, zum wiederholten Mal**: ich habe eine Verhaltensaussage
aus STATUS zitiert statt aus dem Code. Die Regel dagegen steht im
Projekt-Gedaechtnis (`feedback_verify_code_not_history`), und sie hat hier
erneut gegriffen -- nur weil der Nutzer widersprochen hat.
