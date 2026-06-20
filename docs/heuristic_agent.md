# Der MCTS-Heuristik-Agent — Funktionsweise & Mechaniken

Diese Doku beschreibt den `HeuristicMCTSAgent` und sein Zusammenspiel mit dem
Reward-Shaping (`agents/shaping.py`) sowie den MCTS-Mechaniken
(`agents/mcts.py`). Er ist der **Bootstrap-Agent**: Er erzeugt ohne neuronales
Netz Trainingsdaten, indem er das Brett heuristisch bewertet statt zufällig bis
zum Spielende auszuspielen.

> Stand: Bootstrap-Phase (Generation 0). Der Agent liefert die Daten, aus denen
> das erste Netz (`AlphaZeroAgent`) trainiert wird. Sobald ein Netz existiert,
> übernimmt dieses die Bewertung; der Heuristik-Agent bleibt als Referenz und
> für neue Bootstraps erhalten.

---

## 1. Überblick: Was macht der Agent?

Klassisches MCTS spielt von einem Knoten aus zufällig bis zum Spielende
(Rollout) und nutzt das Ergebnis als Bewertung. Das ist bei Azul Duel teuer und
verrauscht. Der `HeuristicMCTSAgent` ersetzt das durch zwei Eingriffe:

1. **Heuristische Blattbewertung** statt Zufalls-Rollout: Eine Potential-Funktion
   (`get_player_potential`) schätzt sofort, wie gut ein Brett für einen Spieler
   steht.
2. **Geführte Aktionsauswahl**: Vor der Suche werden Aktionen heuristisch
   gerankt (`score_dome_action` + Step-Reward), damit das begrenzte Suchbudget
   auf die aussichtsreichen Züge fällt.

Das Ergebnis ist ein Agent, der mit wenig Suchbudget (100 Sims/Zug) brauchbar
spielt und scharfe Policy-Targets für das Netz-Training liefert.

---

## 2. Die Bewertungsfunktion: `get_player_potential`

Kern des Agents. Bewertet ein Spieler-Board als einzelne Zahl. Sechs Terme
(A–F), alle Gewichte als Konstanten oben in `shaping.py`.

### A — Musterreihen (Fortschritt + fertige Reihen)
Pro angefangener Reihe ein Fortschrittsbonus `(k/capacity) * 0.5` je Stein.
Fertige Reihen bekommen ihren geschätzten Reihenwert (`_estimate_row_values`).

### A2 — Sättigungs-Penalty (der Anti-Flutung-Term)
Bestraft **zu viele gleichzeitig offene** (angefangene, aber nicht fertige)
Musterreihen. Aktuell **quadratisch ab Schwelle 2**:

```
over = open_rows - 2
penalty = over * over          # 3 Reihen → -1, 4 → -4, 5 → -9, 6 → -16
```

Hintergrund: Öffnet die KI in Runde 1 zu viele Reihen, hat ab Runde 2 jede Reihe
eine Farbe — eingehende Steine passen nirgends und landen zwangsläufig auf der
Strafleiste. Der quadratische Term soll das Überöffnen verteuern.

> **Hinweis:** Die Code-Kommentare bei `_OPEN_ROW_THRESHOLD`/`_OPEN_ROW_PEN`
> sind veraltet (sie sprechen noch von "bis 3 offene Reihen" und linearem
> Penalty "pro Reihe"). Die tatsächlichen Werte sind Schwelle **2** und
> **quadratische** Skalierung. Messungen zeigen: Dieser Term verändert die
> Floor-Last empirisch kaum — die Strafleisten-Flutung ist überwiegend
> **strukturell** (zu wenige Reihen für zu viele gleichfarbige Steine am
> Rundenende), nicht durch eine korrigierbare Fehlentscheidung verursacht.

### B — Strafleiste (eskalierend)
Summiert `k * 1.8` für k = 1…Anzahl gebrochener Steine. Eskaliert: Der 3. Floor-
Stein kostet mehr als der 1. (`1.8 + 3.6 + 5.4 = 10.8` für 3 Steine). Wird ganz
am Ende vom Potential abgezogen.

### C — Kuppelplatten-Fundament
Pro gelegter Platte `0.6` Basis plus `0.5 * 0.3` pro orthogonalem Plattennachbarn
(Cluster-Bonus). Bewusst niedrig gehalten, damit C nicht A und D überwächst.

### D — Erzielte Punkte
`score * 0.85` (normal) bzw. `* 1.00` in Runde 5 (Cashout — am Ende zählen echte
Punkte am meisten).

### E — Spezialfeld Expected Value
Für jede Platte mit Spezialfeld (`is_locked`): Erfolgswahrscheinlichkeit =
Produkt der Reihen-Wahrscheinlichkeiten der 3 normalen Felder. Erwartungswert =
`p_success * (special_row+1) - (1-p_success) * special_penalty`. Die
`special_penalty` (3.0) greift nur, wenn Wertungsplatte ID 6 (Minuspunkte für
leere Spezialfelder) aktiv ist. Gewichtet mit `0.8`.

### F — Endgame-Wertungsplatten-Nähe
Greift ab Runde 3, mit steigendem Multiplikator (R3: 1.0, R4: 2.5, R5: 5.0).
Bewertet pro aktiver Wertungsplatte, wie nah das Board am Wertungsziel ist
(horizontale/vertikale Reihen, Diagonalen, äußere Felder, Ecken, farbenreiche
Reihen). IDs 0,1,2,4,5,7 sind implementiert; ID 3 (WildFields) noch nicht.

### Rückgabe
`potential - broken_penalty` (Terme A,C,D,E,F minus B).

### Reihen-Wahrscheinlichkeiten
Zwei Tabellen modellieren, wie wahrscheinlich eine Reihe noch gefüllt wird:
- Früh (R1–3): `[0.95, 0.85, 0.60, 0.35, 0.15, 0.05]`
- Spät (R4–5): `[0.80, 0.40, 0.10, 0, 0, 0]`

---

## 3. Aktionsbewertung: `score_dome_action`

Vor der MCTS-Suche wird jede Kuppelzug-Aktion grob gerankt (kein Clone/Step
nötig — billig). Berücksichtigt:

- **Reihen-EV**: pro Feld `prob * row_points`; Spezialfelder mit Verbund-
  wahrscheinlichkeit und Straf-Penalty (falls ID 6 aktiv).
- **Cluster-Bonus**: Nachbarschaft zu vorhandenen Fliesen (`* 0.5`).
- **Positions-Bonus**: `0.3` pro orthogonalem Plattennachbarn.
- **Capacity Matching**: häufige Farben ("Bulk", Dichte > 0.25) ins Auffang-
  becken (untere Reihen 4–6, `+0.4`); seltene Farben ("Snipe", Dichte ≤ 0.10)
  in kurze obere Reihen (`+0.3`).
- **Lategame-Boost**: obere Slots (slot_row 0) im Endgame dringend (`+1.5`).

---

## 4. MCTS-Mechaniken

### 4.1 Dynamisches Sim-Budget (`_compute_dynamic_sims`, Modus "play")
Die Anzahl gültiger Aktionen fällt im Rundenverlauf stark (z.B. 184 → 8). Statt
fix gleich viele Sims pro Zug zu nehmen, wird das Budget umverteilt:

```
target = base + sqrt(num_actions) * 25      # base = 100
budget = clamp(target, base, base*5)        # Unter-/Obergrenze
```

Frühe Züge (viele Optionen) bekommen mehr Suche (bis 500), späte weniger (Floor
100). Sublinear (sqrt), monoton steigend, Cap greift praktisch nie (~289 Aktionen
nötig). Effekt: durchgehend ≥5–9 Sims pro Kind statt der ~3, die ein fixes Budget
im Frühspiel liefern würde.

Der Modus **"selfplay"** existiert auch (`clamp(actions*0.35, 15, base)` —
Effizienz statt Stärke), wird aber im aktuellen Bootstrap nicht genutzt.

### 4.2 Progressive Widening
Die Zahl der expandierten Kinder wächst sublinear mit den Knoten-Visits:

```
allowed = max_actions + int(sqrt(node.visits) * 2.5)   # max_actions = 10
```

Bei 469 Visits sind das ~64 erlaubte Kinder. So konzentriert sich die Suche
zuerst auf die `max_actions` besten Aktionen, öffnet aber bei mehr Visits
schrittweise weitere — auch "unintuitive Rettungszüge" bekommen eine Chance.

### 4.3 Quota-System in `_sample_actions`
Problem: `score_dome_action` liefert Werte ~1–8, die Step-Reward-basierte
Bewertung anderer Züge ~−2…+2. Ungefiltert würden Kuppelzüge die Steinzüge aus
den Top-`max_actions` verdrängen. Lösung: getrennte Kontingente.

```
dome_quota  = max_actions // 2          # halbe Plätze für Kuppelzüge
other_quota = max_actions - dome_quota  # halbe für Steine/Chips/...
```

Beide Listen getrennt nach Score sortiert, dann `top = dome[:quota] +
other[:quota]`, Rest hintenan (sortiert) für Progressive Widening. Ist nur ein
Typ vorhanden, bekommt er alle Plätze.

### 4.4 end_tiling-Schutz
`end_tiling` bekommt **−inf** (bzw. niedrigste Priorität), solange noch andere
Tiling-Züge offen sind. Verhindert den 500-Züge-Infinite-Loop, bei dem die Engine
ein verfrühtes `end_tiling` ablehnt und der State sich nicht ändert.

### 4.5 Bestzug-Auswahl mit Q-Tiebreaker
Statt nur nach Visits wird bei Gleichstand der Q-Wert herangezogen:

```
best = max(children, key=lambda n: (n.visits, n.value/n.visits))
```

Behebt Fälle, in denen zwei Züge gleich oft besucht wurden, aber einer klar den
besseren Mittelwert hat.

---

## 5. Blattbewertung im Baum: `evaluate_state`

Bindet alles zusammen. Pro Spieler:

```
eval = base_score + est_round_score + get_player_potential(...)
```

- `base_score`: echte Punkte
- `est_round_score`: Schätzung der Rundenpunkte (`include_rows=False`, damit
  Reihen nicht doppelt zählen — sie stecken schon im Potential)
- `potential`: die A–F-Bewertung oben

Bei Gleichstand: +0.1 für den Spieler mit dem Startspieler-Marker (Tie-Breaker).

---

## 6. Temperature im Self-Play

Steuert, wie stark die finale Zugauswahl der Visit-Verteilung folgt (τ=1
proportional/explorativ, τ→0 greedy). Aktionszahl-basiert, nicht zugzähler-
basiert — das bildet die schrumpfende Optionen-Matrix am Rundenende ab:

| Situation                | Aktionen | τ    | Zweck                                  |
|--------------------------|----------|------|----------------------------------------|
| Rundenbeginn             | > 50     | 0.7  | Fundament-Entscheidungen explorieren   |
| Rundenmitte              | > 15     | 0.4  | moderater Fokus                        |
| Rundenende (Floor-Phase) | ≤ 15     | 0.15 | scharf aufs Fundament zuspitzen        |
| Startkuppel-Platzierung  | —        | 0.3  | milde Variation für diverse Starts     |

Wichtig: Die kritische Floor-Phase läuft schon mit τ=0.15 (fast greedy). Floor-
Züge sind dort also **kein Explorationsrauschen**, sondern das, was die KI für am
wenigsten schlecht hält — ein weiterer Beleg, dass die Floor-Last strukturell ist.

---

## 7. Durchgerechnetes Beispiel: ein MCTS-Zug Schritt für Schritt

Ausgangslage: Die KI ist am Zug, `_compute_dynamic_sims` hat für diese Stellung
**150 Sims** vergeben, `max_actions = 10`. Es gibt 32 gültige Aktionen (gemischt:
Kuppelzüge, Steinzüge, Chips).

### Aufbau der Wurzel (erste Expansion)

Beim allerersten `_expand` auf die Wurzel wird `_sample_actions(actions, env)`
gerufen (mit env, weil Wurzel → echtes Ranking via Quota-System):

- Kuppelzüge per `score_dome_action` gerankt, andere per Clone+Step-Reward.
- Quota: `dome_quota = 5`, `other_quota = 5`.
- Ergebnis ist eine **vollständig sortierte Liste aller 32 Aktionen**.

Die Wurzel teilt diese Liste:
```
untried_actions   = ranked[:10]    # die 10 besten — erste Welle
remaining_actions = ranked[10:]    # die übrigen 22 — Reserve fürs Widening
```

### Die Sim-Schleife (150 Durchläufe)

Jeder Sim durchläuft vier Phasen: **Selection → Expansion → Evaluation →
Backpropagation**. Entscheidend sind die Verzweigungen in `_select`, die
festlegen, *wann* eine neue Aktion dazukommt und *wann* abgestiegen wird.

#### Sims 1–10: die erste Welle wird aufgebaut
Die Wurzel hat noch `untried_actions`. In `_select` greift sofort Check 2
("noch unversuchte freigeschaltete Züge?") → Rückgabe der Wurzel, `_expand`
zieht **eine zufällige** der 10 freigeschalteten Aktionen, spielt sie per
`env.step`, legt ein Kindknoten an. Dann `evaluate_state` auf das Kind →
Potential-Differenz → Backprop.

Nach 10 Sims: Wurzel hat 10 Kinder, `untried_actions` ist leer,
`remaining_actions` hat noch 22.

> Warum zufällig statt bestes zuerst? Die Reihenfolge ist durch das Ranking schon
> gut, aber zufälliges Ziehen aus der Top-10 verhindert, dass ein einzelner
> früh-expandierter Zug durch Reihenfolge-Artefakte bevorzugt wird. Die Qualität
> kommt über UCB1 in den folgenden Sims.

#### Sim 11: jetzt entscheidet Progressive Widening
Wurzel hat keine `untried_actions` mehr, aber `remaining_actions` (22). Check 1
greift:
```
allowed = max_actions + int(sqrt(visits) * 2.5)
        = 10 + int(sqrt(10) * 2.5) = 10 + 7 = 17
current = len(children) + len(untried) = 10 + 0 = 10
10 < 17  →  ja: eine remaining-Aktion freischalten
```
Die nächstbeste Reserve-Aktion (ranked[10], die 11.-beste) wandert aus
`remaining_actions` in `untried_actions`. `_expand` macht daraus ein 11. Kind.

**Das ist der Moment, in dem eine "weniger gute" Aktion dazukommt** — gesteuert
allein durch die Visit-Zahl der Wurzel.

#### Sims 12–17: Widening läuft weiter
Solange `current < allowed` (17), schaltet jeder Sim eine weitere Reserve-Aktion
frei. Bei Visit 17 ist `current = 17`, `allowed` ist inzwischen leicht gestiegen
(`10 + int(sqrt(17)*2.5) = 10 + 10 = 20`) — es kommen also weiter Aktionen dazu,
aber der Abstand schließt sich.

#### Sim ~25+: der erste Abstieg eine Ebene tiefer
Sobald `current >= allowed` (Widening pausiert) **und** keine `untried_actions`
übrig sind, greift Check 3: Abstieg.
```
node = node.best_child(c=0.3)   # UCB1 wählt das vielversprechendste Kind
env.step(node.action)           # Spielzustand eine Ebene tiefer
```
UCB1 wägt ab: `Q + 0.3 * sqrt(ln(parent.visits) / child.visits)`. Ein Kind mit
hohem Mittelwert (Exploitation) oder wenigen Besuchen (Exploration) gewinnt. Erst
**jetzt** geht die Suche eine Ebene tiefer — am gewählten Kind beginnt dieselbe
Logik von vorn (eigene Expansion, eigenes Widening).

> Kernidee: Das sublineare Widening (`sqrt`) sorgt dafür, dass die Breite einer
> Ebene mit zunehmenden Besuchen **abflacht**, während die Visit-Zahl linear
> weiterwächst. Dadurch wird ab einem gewissen Punkt `current >= allowed`
> dauerhaft erfüllt → die Suche investiert ihre Sims in **Tiefe** statt immer
> neue mittelmäßige Geschwister zu öffnen. Genau die Balance, die man will:
> früh breit (viele Optionen anschauen), dann tief (die besten verfolgen).

### Wann kommen also schwächere Aktionen dazu? — Zusammenfassung

| Auslöser                                   | Was passiert                          |
|--------------------------------------------|---------------------------------------|
| `untried_actions` nicht leer               | nächste der **Top-10** wird expandiert|
| `remaining` da **und** `current < allowed` | nächstschwächere Reserve freigeschaltet (Widening) |
| `current >= allowed`, `untried` leer       | **Abstieg** zum besten Kind (UCB1)    |
| Kind erreicht Spielende (`done`)           | direkt bewertet, kein weiterer Abstieg|

`allowed = 10 + sqrt(visits)*2.5` ist der Hebel: Bei 100 Wurzel-Visits sind ~35
Aktionen offen, bei 400 ~60. Es kommen also immer langsamer neue (schwächere)
Aktionen dazu, während der Großteil der späten Sims in die Tiefe der besten
Linien fließt.

### Abschluss des Zugs

Nach 150 Sims wählt `mcts_search` den finalen Zug — **nicht** über UCB1, sondern
über Visits mit Q-Tiebreaker:
```
best = max(children, key=lambda n: (n.visits, n.value / n.visits))
```
Im Self-Play wird dieser Zug zusätzlich durch die **Temperature** (Abschnitt 6)
verrauscht; die Visit-Verteilung über alle Wurzelkinder bildet das **Policy-
Target** fürs Netz-Training.

### Bezug zur Bewertung

Jedes Blatt, das ein Sim erreicht, wird über `evaluate_state` bewertet — also
über die A–F-Potentialfunktion aus Abschnitt 2. Ein Blatt, an dem die KI z.B. 2
Floor-Steine angesammelt hat (B-Penalty `−5.4`), bekommt ein entsprechend
niedrigeres Potential und wird über die Backpropagation für alle Knoten auf dem
Pfad "unattraktiver". So fließt die Heuristik in die Visit-Verteilung ein, ohne
dass je bis zum Spielende ausgespielt wird.

---

## 8. Wichtige Konstanten auf einen Blick

| Konstante         | Wert            | Term | Bedeutung                          |
|-------------------|-----------------|------|------------------------------------|
| `_C_BASIS`        | 0.6             | C    | Basis pro Kuppelplatte             |
| `_C_POS_WEIGHT`   | 0.3             | C    | Positions-Bonus pro Nachbar        |
| `_D_WEIGHT`       | 0.85            | D    | Punkte-Gewicht (normal)            |
| `_D_WEIGHT_CASH`  | 1.00            | D    | Punkte-Gewicht (R5)                |
| `_B_BASE_PEN`     | 1.8             | B    | Strafleisten-Eskalationsfaktor     |
| `_E_WEIGHT`       | 0.8             | E    | Spezialfeld-EV-Dämpfung            |
| `_F_START_ROUND`  | 3               | F    | F greift ab Runde 3                |
| `_F_MULTI`        | {3:1, 4:2.5, 5:5} | F  | Endgame-Multiplikatoren            |
| `_OPEN_ROW_THRESHOLD` | 2           | A2   | erlaubte offene Reihen ohne Penalty|
| `_OPEN_ROW_PEN`   | 1 (quadratisch) | A2   | Sättigungs-Penalty-Faktor          |

| MCTS-Parameter        | Wert  | Bedeutung                              |
|-----------------------|-------|----------------------------------------|
| Sim-Budget (base)     | 100   | Basis-Simulationen, ×5 max im Frühspiel|
| `max_actions`         | 10    | erste Welle expandierter Kinder        |
| Progressive-Widening  | `+sqrt(visits)*2.5` | sublineares Aufweiten     |
| UCB1-Konstante `c`    | 0.3   | Exploration/Exploitation-Balance       |

---

## 9. Bekannte Grenzen

- **Floor-Flutung ist strukturell.** Heuristik-Tuning (A2 linear→quadratisch)
  bewegt die Floor-Last empirisch kaum. Das Netz soll die verzögerten Floor-
  Kaskaden über das Value-Target lernen, nicht das Shaping.
- **Wertungsplatte ID 3 (WildFields)** ist im F-Term nicht implementiert.
- **`score_dome_action`** nutzt die Wertungsplatten nur über die Spezialfeld-
  Penalty (ID 6), nicht für die F-artige Zielnähe-Bewertung.
- **Veraltete Code-Kommentare** beim A2-Term (Schwelle/Linearität) — die Werte
  im Code sind maßgeblich, nicht die Kommentare.
