# Externe Recherche: mehrrundige Bau-Absicht (Spalten/Wertungsplatten) im Netz verankern

**Datum:** 2026-08-22
**Auftrag:** Web-/Literaturrecherche zum intern vorregistriert gemessenen Problemstand
(Policy-Prior bietet den Bauzug dominant an, Value-Backup vetot ihn; Ownership-Kopf,
Value-Ziel-Umbauten, asymmetrisches Zwangs-Curriculum und implizites Behavior-Cloning
jeweils gemessen negativ/null). Keine Code-Änderungen.
**Bearbeiter:** Recherche-Agent (nur Web-Quellen, kein Repo-Zugriff verwendet)

---

## Belegkonvention (REGEL 0)

Diese Datei trennt drei Stufen, jede Aussage trägt eine davon:

- **[Q]** – wörtlich oder inhaltlich **aus der genannten Quelle gelesen** (Volltext-Abruf
  oder Abstract/Doku direkt abgerufen).
- **[Q-sek]** – aus **Suchergebnis-Snippets** entnommen, Primärtext nicht selbst geöffnet.
  Vor jeder tragenden Verwendung nachprüfen.
- **[E]** – **meine Einschätzung / Herleitung**, kein Beleg.

Ausdrücklicher Negativbefund vorweg: Ich habe **keine** Publikation gefunden, die
unseren Fall (seltene, mehrrundige, plattenbedingte Bau-Absicht in einem
Draft-Brettspiel) direkt behandelt. Alles Folgende ist Übertragung aus benachbarten
Regimen. Wo die Übertragung dünn ist, steht es dabei.

---

## F1. Seltene, aber wertvolle Langfrist-Strategien im Selbstspiel etablieren

### F1.1 Der belegteste Hebel in Brettspiel-Engines ist nicht das Curriculum, sondern die *Startzustandsverteilung*

Das ist der eine Punkt, an dem sich Papers **und** Produktions-Engines treffen.

**Go-Exploit** (Trudeau & Bowling, AAMAS 2023) [Q, Quelle 7]. Abstract wörtlich:

> "AlphaZero trains upon self-play matches beginning from the initial state of a game and
> only samples actions over the first few moves, limiting its exploration of states deeper
> in the game tree. We introduce Go-Exploit, a novel search control strategy for AlphaZero.
> Go-Exploit samples the start state of its self-play trajectories from an archive of states
> of interest."

Begründung im Abstract, die für uns die eigentlich interessante ist: das Verfahren
"enables Go-Exploit ... to learn a value function that generalizes better", und
"Producing shorter self-play trajectories allows Go-Exploit to train upon more
independent value targets, improving value training." Gemessen in Connect Four und
9x9 Go: höhere Sample-Effizienz als AlphaZero, und laut Abstract eine wirksamere
Search-Control als KataGo.

**RGSC / Regret-Guided Search Control** (2026) [Q, Quelle 8] ist die Fortschreibung:
ein Regret-Netz identifiziert Zustände, "where the agent's evaluation diverges most from
the actual outcome", legt sie in einen priorisierten Puffer und startet daraus.
Gemessen: 9x9 Go, 10x10 Othello, 11x11 Hex; +77 Elo gegen AlphaZero und +89 Elo gegen
Go-Exploit im Mittel; auf einem austrainierten 9x9-Go-Modell Siegquote gegen KataGo
von 69,3 % auf 78,2 %, während die Baselines sich gar nicht verbesserten.

**KataGo macht dasselbe seit Jahren in Produktion** [Q, Quelle 3, `selfplay1.cfg`].
Die Trainingskonfiguration enthält genau die Maschinerie:

- `startPosesProb` / `startPosesFromSgfDir` / `startPosesLoadProb` /
  `startPosesTurnWeightLambda` – Anteil der Partien, die aus eingespeisten SGF-Stellungen
  starten, mit Gewichtung nach Zugnummer.
- `hintPosesProb` / `hintPosesDir` – Stellungen aus dem `dataminesgfs`-Werkzeug, also
  gezielt gesammelte Stellungen, an denen das Netz etwas lernen soll.
- `sidePositionProb = 0.020` – laut Kommentar Training "on refuting bad alternative moves",
  also **zusätzliche Wert-Stichproben abseits der gespielten Linie**.
- `initGamesWithPolicy = true`, `policyInitAreaProp = 0.04` – Eröffnungszüge mit hoher
  Temperatur aus der Policy, um die Startverteilung zu streuen.

Das ist für uns die direkteste Analogie: `sidePositionProb` erzeugt Value-Ziele für
Stellungen, die die On-Policy-Verteilung nie erreicht – ohne irgendeine Seite zu einem
Verhalten zu zwingen.

**[E]** Der Unterschied zu unserem gemessen negativen Zwangs-Curriculum (c) ist
strukturell und nicht graduell: dort wurde die **Policy** einer Seite über die ganze
Partie fremdbestimmt, wodurch alle Value-Ziele die Rendite einer *fremden* Politik
messen. Bei Startpositions-Injektion ist ab dem Startpunkt **alles wieder On-Policy**;
das Netz erfährt "wie gut steht es, wenn die Spalte halb steht" unter seiner eigenen
Fortsetzung. Genau die Größe, die laut Diagnose fehlt.

### F1.2 Curricula im engeren Sinn: dünne Beleglage

Ich habe keine Brettspiel-Engine gefunden, in der ein *Regel-Zwangs-Curriculum*
(scripted opponent erzwingt Verhalten) nachweislich Verhalten im freien Spiel erzeugt
hat. Die einzige belegte Umsetzung eines "gezwungenen" Regimes in einer Top-Engine ist
KataGos Handicap-Training mit **unbalancierten Playouts** [Q, Quelle 4]: das Netz spielt
gegen schwächere Versionen seiner selbst, "so that KataGo learns how to fight weaker
versions of itself (while the weaker versions simultaneously learn how to play safely
and resist)". Das ist Zwang über das *Suchbudget*, nicht über die Zugauswahl – die
Politik bleibt eigenverantwortlich.

### F1.3 Diversität / League-Training: der stärkste Präzedenzfall ist AZ_db, nicht AlphaStar

**AZ_db, "Diversifying AI: Towards Creative Chess with AlphaZero"** [Q, Quelle 10] ist
für uns die relevanteste Arbeit überhaupt, weil Architektur *und* Suchbudget passen:

- Mechanik: "a single latent-conditioned architecture", die Latente l^i sind
  **One-Hot-Vektoren, an den Input konkateniert**. Netz hat "a shared torso and three
  heads: policy, value, and intrinsic value".
- Diversität entsteht über einen **intrinsischen Reward** auf Verhaltensunterschiede
  (unterschiedliche Figuren-Belegungen, Hausdorff-Distanz zwischen erwarteten
  Feature-Vektoren) – nicht über erzwungene Züge.
- Spielzeit: "sub-additive planning", also Auswahl des Sub-Agenten pro Stellung nach
  Visit / Value / LCB / Gap.
- Messung: bei **400 MCTS-Simulationen** (identisches Budget zu unserem) erreicht
  AZ_db-Spieler 0 **+29,6 Elo** gegen AZ, mit sub-additivem Planen **+50,3 Elo**.
  Auf Puzzle-Sets: AZ 11,76 % (Challenge) / 3,64 % (Penrose) gegen AZ_db
  max-over-latents 20,69 % / 13,5 %.
- Kernsatz zur Frage "finden diverse Agenten, was ein einzelner nicht findet":
  "some of the players in the AZdb team were able to solve the Penrose positions without
  training on them, while other players, including AZ, were not."

**AlphaStar** [Q-sek, Quelle 9] liefert die zweite Hälfte: die Politik ist "conditioned
on a statistic z that summarises a strategy sampled from human data (for example, a
build order)". Agenten werden **entweder** auf z konditioniert – "in which case agents
receive a reward for following the strategy corresponding to z" – **oder**
unkonditioniert trainiert, "in which case the agent is free to choose its own strategy".
Die Pseudo-Rewards messen Edit-Distanz der Bauordnung und Hamming-Distanz kumulativer
Statistiken. Dazu ein KL-Strafterm gegen die Supervised-Policy, "ensuring that a wide
variety of relevant modes of play continue to be explored throughout training".

**[E]** Das ist die belegte Bauform, die unserem geplanten UVFA-Zuschnitt am nächsten
kommt, und sie enthält **zwei** Zutaten, die unser Zuschnitt bisher nicht hat:
(i) der Regime-Flag kommt mit einem **Pseudo-Reward auf Regime-Treue**, nicht nur mit
erzwungenen Zügen, und (ii) es gibt **beide Modi im selben Training**
(konditioniert/unkonditioniert), was den Flag erst diskriminativ macht.

### F1.4 Hindsight / Goal-Relabeling und Options: in Brettspielen unbelegt

UVFA [Q-sek, Quelle 16] und HER [Q-sek, Quelle 17] sind die Standardreferenzen
(Relabeling-Schemata `final`, `future`, `episode`, `random`). Ich habe **keinen**
Beleg für erfolgreiche HER-Anwendung in einer Zwei-Spieler-Brettspiel-Engine gefunden.

**[E]** Der Grund ist strukturell: HER braucht ein Ziel, dessen Erreichen die
Belohnung *definiert*. Bei uns ist das Ziel (Spalte fertig) nur ein Zwischenprodukt,
der Reward bleibt Sieg/Niederlage. Ein hindsight-relabeltes "Ziel = die Spalten, die
tatsächlich fertig wurden" wäre kein Belohnungssignal, sondern genau die
politikabhängige Grundraten-Falle, die im Projekt schon einmal zugeschlagen hat
(Kopf sagt Eintreten vorher, nicht Erreichbarkeit).

### F1.5 Ein aktueller Negativ-/Positivbefund zur Grundfrage

"AlphaZero in Sparsely Rewarded Games: Limits and Auxiliary Supervision" [Q, Quelle 25]
zeigt an Connect Four und Chomp, dass "superhuman play does not necessarily imply
perfect play": Vanilla-AlphaZero hält optimale Linien nicht durch (Chomp 9x10: 60,9 %
Zug-Trefferquote, **0 % perfekte Partien**). Ihr Gegenmittel AZAL ist ein
**zusätzlicher Policy-Loss aus einem Orakel**, "without modifying search or value
targets" – Chomp 9x10 auf 94,8 % / 56,7 % perfekte Partien, Chomp 10x11 auf 100 %.
Diagnose der Autoren: "standard AlphaZero self-play creates a moving-target problem:
the network is asked to fit targets generated by its own evolving approximation".

**[E] Wichtige Einschränkung für uns:** AZAL hilft dort, wo ein **exaktes Orakel** die
korrekte Policy kennt. Unser Fall (d) ist genau der Gegentest dazu: wir hatten
Orakel-artige One-Hot-Policy-Ziele aus dem Bauer und haben keine Verhaltenswirkung
gemessen. Der Unterschied: in Chomp *ist* der Orakelzug der objektiv beste Zug, bei uns
ist der Bauerzug ein Verhaltenswunsch. Das trennt F1 von F4 sauber und stützt die
interne Diagnose (Engpass sitzt nicht in der Policy).

---

## F2. Prior-gegen-Value-Konflikt in der Suche

### F2.1 Die Theorie sagt: der Prior ist nur ein Regularisierer, dessen Gewicht mit den Visits fällt

Grill et al., "Monte-Carlo Tree Search as Regularized Policy Optimization" (ICML 2020)
[Q-sek, Quelle 13]: die empirische Besuchsverteilung von AlphaZero approximiert die
Lösung eines KL-regularisierten Politikoptimierungsproblems, mit dem Prior als
Referenzverteilung. Ihr Befund für unseren Betriebspunkt: die exakte Lösung "is superior
to normalized visit counts when the number of simulations is small", und ihre Variante
zeigt Gewinne "especially in cases where AlphaZero has been observed to fail, e.g., when
per-search simulation budgets are low".

### F2.2 Bei Gumbel ist das Gewichtsverhältnis eine *explizite Konstante*, und sie ist einstellbar

Das ist der konkreteste Fund dieser Recherche. Aus `mctx/_src/qtransforms.py`
(DeepMind-Referenzimplementierung von Gumbel MuZero) [Q, Quelle 12]:

- `qtransform_completed_by_mix_value` mit Defaults
  `value_scale = 0.1`, `maxvisit_init = 50.0`, `rescale_values = True`,
  `use_mixed_value = True`.
- Rückgabe: `visit_scale * value_scale * completed_qvalues`, wobei
  `visit_scale = maxvisit_init + max(visit_counts)` über die Geschwister des Knotens.
- Unbesuchte Aktionen werden über `_compute_mixed_value` gefüllt: gewichtete
  Interpolation aus roher Zustandsbewertung und besuchten Q-Werten, gewichtet mit den
  **Priors** und normiert über die Gesamtvisits.

Die verbesserte Politik ist `softmax(prior_logits + sigma(completedQ))` [Q-sek, Quelle 11].

**[E] Herleitung für unseren Betriebspunkt (ungeprüft an unserem Code, bitte gegen die
eigenen Konstanten halten):** bei 400 Sims und ~16 betrachteten Wurzelaktionen erhält
der Sieger der Sequential-Halving-Leiter grob 6 + 12 + 25 + 50 ≈ 93 Visits. Damit ist
`visit_scale ≈ 50 + 93 = 143`, mal `value_scale = 0.1` ergibt einen Faktor **~14** auf
die (durch `rescale_values` auf [0,1] normierten) Q-Differenzen. Ein Prior-Vorsprung
von Faktor 4,9 sind dagegen `ln(4,9) ≈ 1,6` Logits.

Konsequenz der Rechnung: **eine Q-Differenz von nur ~11 % der lokalen Q-Spannweite
löscht unseren gesamten gemessenen Prior-Vorsprung aus.** Das ist keine Anomalie
unseres Netzes, das ist die designte Arbeitsteilung von Gumbel-AZ. Wenn der Value-Kopf
den Bauzug auch nur leicht schlechter sieht, ist der Prior chancenlos – exakt der
intern gemessene Befund.

Daraus folgen drei Stellschrauben, alle ohne Netzänderung:

1. `value_scale` / `maxvisit_init` (unser Äquivalent) senken – verschiebt das Gewicht
   zurück zum Prior. Direkter Test der Diagnose.
2. **Root Policy Softmax Temperature**: KataGo wendet am Wurzelknoten eine Temperatur
   an (1,25 früh, abklingend auf 1,1), bevor Rauschen addiert wird, und begründet das
   ausdrücklich damit, dass sie "ensures that moves will not decay in policy prior if
   the MCTS search finds them to have a utility comparable to the best alternative
   moves" [Q, Quelle 2].
3. **Policy Surprise Weighting**: KataGo überschreibt Trainingsstichproben nach der
   "KL-divergence from the policy prior to the policy training target" häufiger, damit
   "certain good moves" nicht "neglected during training despite having low initial
   policy estimates" werden [Q, Quelle 2].

### F2.3 KL-regularisierte Suche macht geklonte Ziele *ausdrucksfähig* – belegt

Das ist die direkte Antwort auf die Frage nach Gegenmitteln, die die Ausdrucksfähigkeit
geklonter Policy-Ziele erhöhen.

**piKL** (Jacob, Wu, Farina, Lerer, Hu, Bakhtin, Andreas, Brown; ICML 2022)
[Q-sek, Quelle 14]: Suche mit einem Kostenterm proportional zur KL-Divergenz zwischen
Suchpolitik und einer imitationsgelernten **Anker-Politik**. Belegt in **Schach und Go**,
dass das gleichzeitig menschenähnlicher *und* stärker ist als reine Imitation.
Kernproblem, das sie adressieren, ist wörtlich unseres in gespiegelter Form:
Suche erzeugt starke, aber vom Anker weglaufende Politiken.

**RL-DiL-piKL** (Bakhtin et al. 2022) [Q-sek, Quelle 15] hebt das ins Selbstspiel:
"a planning algorithm that regularizes a reward-maximizing policy toward a human
imitation-learned policy", erweitert zu einem Selbstspiel-RL-Algorithmus. Eingesetzt in
Cicero (Science 2022, Quelle 15/Cicero).

**[E]** Für uns die interessanteste Umdeutung: piKL ist genau der Mechanismus, mit dem
ein geklonter Prior die Suche *nicht mehr nur über die Logits*, sondern über den
**Nutzen** beeinflusst. Unser Fall (d) ist gescheitert, weil das Klonen ausschließlich
in die Logits ging – und die werden laut F2.2 rechnerisch überstimmt. Ein
KL-Strafterm gegen einen Bau-Anker greift dagegen dort an, wo das Veto sitzt.
Achtung: Anker ist bei piKL immer eine *Imitations*-Politik; unser Bauer wäre ein
regelbasierter Anker, das ist eine Übertragung, kein Beleg.

### F2.4 Weitere belegte Eingriffe an derselben Stelle

- **Subtree Value Bias Correction** (KataGo, Produktion) [Q, Quelle 2]: Knoten werden
  nach lokalen Mustern gebucketet, der beobachtete Bias je Bucket wird gemittelt und
  im Suchnutzen abgezogen:
  `NodeUtility(n) = NNUtility(n) − λ × MostRecentRetrievedObsBias(n)` mit λ ≈ 0,35.
  Also ein **direkter, laufzeitgelernter Korrekturterm auf den Leaf-Value** – genau die
  Klasse Eingriff, die bei uns als Ownership-Leaf-Shift negativ gemessen wurde, hier
  aber ohne Hilfskopf und mit Statistik statt Netz.
- **Optimistic Policy** (KataGo, Produktion) [Q, Quelle 2]: ein zweiter Policy-Kopf,
  trainiert auf demselben Ziel, aber **überproportional gewichtet auf Stichproben, in
  denen der Spieler überraschend besseren Kurzfrist-Wert/Score erzielt hat** (Sigmoid
  über z-Scores der Überraschung). Zur Testzeit lenkt diese optimistische Policy die
  Zugauswahl **für beide Spieler**, "aiming to guide exploration toward tactics that
  might outperform initial expectations".

**[E]** Die Optimistic Policy ist ein sehr guter Passform-Kandidat: sie ist genau ein
Mechanismus, um seltene, überdurchschnittlich gute Ausgänge in der Suche
überzugewichten, ohne das Value-Ziel anzufassen (das bei uns 3× negativ gemessen wurde).
Und sie ist in einer Produktions-Engine belegt, nicht nur im Paper.

---

## F3. Konditionierte Spielstil-Netze

### F3.1 Belegte Präzedenzfälle

| Fall | Konditionierung | Wie eingespeist | Spielzeit-Regler | Beleg |
|---|---|---|---|---|
| AZ_db (Schach) | One-Hot-Latente je Sub-Agent | **konkateniert an den Input** | Sub-Agent-Auswahl (Visit/Value/LCB/Gap) | [Q, Q10] |
| AlphaStar | Strategie-Statistik z (Bauordnung) | Policy-Input + Pseudo-Reward auf z-Treue | z zur Testzeit setzbar | [Q-sek, Q9] |
| KataGo | Komi, Ko-Regel, Suizid, Scoring, Tax, Encore | **globale Input-Kanäle** des Netzes | frei setzbar | [Q, Q6] |
| KataGo HumanSL (v1.15, 2024) | `humanSLProfile`, Rang 20k–9d bzw. Jahrgang ab 1800 | Modell-Input | GTP-/Analyse-Parameter | [Q-sek, Q5] |
| Maia-2 | Rating-Vektor `(rating_norm, classical, aggression)` | separater Konditionierungs-Tensor + skill-aware Attention | Rating zur Testzeit | [Q-sek, Q18] |

Die KataGo-Regel-/Komi-Kanäle habe ich am Primärcode geprüft [Q, Quelle 6]:
`fillRowV7` belegt u. a. `rowGlobal[5]` = Komi (Skalierung 1/20), `[6-7]` Ko-Regel,
`[8]` Suizid, `[9]` Scoring-Regel, `[10-11]` Tax, `[12-13]` Encore, `[14]`
Pass-beendet-Phase, `[15]` Komi-Paritätswelle. Das ist der sauberste belegte Beweis,
dass **additive globale Konditionierungskanäle in einer CPU-/GPU-Produktionsengine
funktionieren und zur Spielzeit frei gesetzt werden**.

**Ausdrücklicher Negativbefund / ungeprüft:** Ich konnte **nicht** verifizieren, dass
`playoutDoublingAdvantage` ein Netz-Eingangskanal ist. Im abgerufenen `nninputs.cpp`
taucht PDA nur im `getHash()` für den NN-Cache auf, nicht in `fillRowV*`; die
Global-Feature-Zahl ist `NUM_FEATURES_GLOBAL_V7 = 19`, die Kanäle 16–18 konnte ich
nicht auflösen (Datei im Abruf vermutlich gekürzt). Belegt ist nur:
PDA ist ein Such-/Bewertungsparameter (2^PDA-fache Playouts unterstellt, Bereich −3..3)
und die Netze wurden mit **unbalancierten Playouts** speziell trainiert [Q, Quelle 4].
Wer diesen Präzedenzfall tragend verwenden will, muss das selbst nachschlagen.

### F3.2 Belegte Fallstricke

1. **Konditionierung ≠ Steuerung, wenn das Ziel politikabhängig ist.** Paster et al.,
   "You Can't Count on Luck" [Q-sek, Quelle 19]: Return-Conditioning versagt in
   stochastischen Umgebungen, weil "trajectories that result in a return may have only
   achieved that return due to luck". Ihr Gegenmittel ESPER clustert Trajektorien und
   konditioniert auf **Cluster-Mittelwerte**, die von der Umgebungsstochastik
   unabhängig sind. **[E]** Für uns: nicht auf "hat gebaut" konditionieren (das ist
   teilweise Glück in der Fliesenverfügbarkeit), sondern auf **"war im Bau-Regime"** –
   was der geplante Zuschnitt ohnehin tut. Gut so.
2. **Sequenzmodelle interpolieren, sie extrapolieren nicht** [Q-sek, Quelle 19]: Modelle
   "may struggle to reason about achieving returns that differ substantially to those
   seen in the training data", und Decision Transformer "fails to stitch trajectories
   even when the MDP is deterministic". **[E]** Direkte Warnung an unseren Zuschnitt:
   Flag=1 zur Spielzeit reproduziert die **Trainingsverteilung der Zwangsseite**, also
   ein 34,6-%-Bauverhalten *mit 45,7 % Siegquote*. Ein Regler, der brav genau das
   nachbildet, hat unser Problem nicht gelöst, sondern nur den Bauer nachgebaut.
3. **Flag-Leakage.** **[E], unbelegt:** wenn der Flag im Korpus nur bei genau einer
   Seite pro Partie auf 1 steht, korreliert er mit "diese Seite spielt gleich
   suboptimal" und damit mit dem Ausgang. Ein Value-Kopf lernt dann schlicht
   "Flag=1 → −4 Elo", und der Stil-Regler wird zum Selbstsabotage-Regler. Der interne
   Befund "Zwangsseite gewinnt 45,7 %" macht das quantitativ konkret: der Flag hat ein
   **eingebautes Handicap von ~4,3 Prozentpunkten**. Ohne Gegenmaßnahme ist das das
   wahrscheinlichste Scheitern des Zuschnitts.
4. **Kalibrierung des Reglers.** KataGo HumanSL wurde so trainiert, dass "using only one
   visit and full temperature ... will give the closest match to how players of the
   given rank might play" [Q-sek, Quelle 5]. Der Regler ist also nur bei einer
   *bestimmten* Suchkonfiguration kalibriert; unter 400 Sims verhält er sich anders.

### F3.3 Der belegte Verstärker: Conditioning-Dropout plus Guidance-Skala

Gegen Fallstrick 2 gibt es ein direkt passendes Rezept aus der Diffusions-/CFG-Ecke,
inzwischen in RL übertragen. "Policy Gradient Guidance" [Q-sek, Quelle 20] ist
"the first extension of classifier-free guidance to classical on-policy reinforcement
learning": PPO wird um einen **unkonditionierten Zweig** ergänzt, und zur Testzeit
werden konditionierte und unkonditionierte Logits interpoliert. Allgemein gilt:
Trainingszeit-**Dropout der Konditionierung** erzeugt ein Modell, das beides kann;
zur Testzeit steuert eine Skala w, wie stark die Bedingung wirkt, "where larger w
increases adherence to the condition at the cost of reduced diversity".

**[E]** Auf uns übertragen: Flag beim Training in z. B. 20 % der Zwangs-Stichproben auf
0 setzen (Dropout), zur Spielzeit
`logits = logits(flag=0) + w · (logits(flag=1) − logits(flag=0))` mit w > 1.
Damit lässt sich das Bauverhalten **über** die 34,6 % der Trainingsverteilung hinaus
extrapolieren, statt sie nur zu reproduzieren – genau der Punkt, an dem naive
Konditionierung laut Quelle 19 scheitert. Kosten: zwei Netz-Auswertungen je Knoten,
oder eine Auswertung mit Batch 2. Das ist bei CPU-Inferenz spürbar.
Bemerkenswert: AlphaStar tut faktisch dasselbe, indem es konditionierte **und**
unkonditionierte Agenten in derselben Liga trainiert [Q-sek, Quelle 9].

---

## F4. Warum Behavior-Cloning wirkungslos bleiben kann, obwohl der Prior dominant ist

### F4.1 Es gibt eine saubere theoretische Antwort, und sie deckt sich mit unserer Messung

Zwei belegte Bausteine ergeben zusammen die Erklärung:

- Der Prior ist in AZ-artiger Suche **nur** die Referenzverteilung eines
  KL-regularisierten Problems, dessen Regularisierungsgewicht mit wachsender Suche
  fällt [Q-sek, Quelle 13].
- Bei Gumbel ist dieses Gewicht eine explizite, mit `max_visits` **wachsende**
  Konstante vor den Q-Werten [Q, Quelle 12].

**[E] Schlussfolgerung:** Ein Behavior-Cloning-Signal, das ausschließlich die
Prior-Logits verschiebt, kann per Konstruktion nicht mehr als O(1) Logits Einfluss
kaufen, während der Value-Term O(`max_visits` · `value_scale`) skaliert. Bei 400 Sims
ist das ein Verhältnis von grob 1,6 zu 14. Der Befund "Prior 4,9× vorne, Verhalten
unverändert" ist damit kein Rätsel, sondern die Vorhersage. **Das ist die Antwort auf
F4 in einem Satz: Klonen in den Prior ist bei hohem Suchbudget das schwächste
verfügbare Interventionsniveau.**

### F4.2 Der Engpass in der Literatur: Value-Ziele aus fremd erzeugten Trajektorien

Das ist ein bekanntes Problem mit Namen.

- **Off-Policy-Value-Ziele in MuZero-Reanalyze** [Q-sek, Quelle 26/27]: "the value target
  computed from sampled trajectories suffers from off-policy issues since trajectories
  are rolled out using an older policy", und das verschärft sich, je fremder die
  erzeugende Politik ist. EfficientZero korrigiert das über einen **dynamischen Horizont
  l** (kürzer für ältere Trajektorien) und rechnet ab Schritt l eine **frische Suche mit
  der aktuellen Politik** als Value-Ziel.
- **Offline-RL-Standardbefund** [Q-sek, aus Quellensammlung F4]: OOD-Aktionen erzeugen
  überschätzte Q-Werte, die über Bootstrapping weiterpropagieren; deshalb arbeiten
  Offline-Verfahren mit Politik-Beschränkung oder pessimistischer Wertregularisierung.
- **Adversarial Policies Beat Superhuman Go AIs** [Q-sek, Quelle 31] ist die
  Brettspiel-Illustration: KataGos Value-Kopf ist auf Verteilungen, die im Selbstspiel
  nie vorkommen, katastrophal falsch – trotz übermenschlicher On-Distribution-Stärke.

**[E] Übertragung auf unseren Fall (c):** Die Zwangsseite spielt eine Politik, die das
Netz nie spielen wird. Der Value-Kopf lernt daraus V unter der *Bauer-Politik*, nicht
unter seiner eigenen. Beim freien Spiel ist dieser Wert schlicht die falsche Größe, und
die Suche merkt das korrekt. Der gemessene Kendall-Tau von ≈ −0,08 (Kontrolle −0,19,
n.s.) ist konsistent damit, dass **überhaupt kein** brauchbares Ranking gelernt wurde.

### F4.3 Belegte Rezepte, Value-Ziele aus erzwungenen Trajektorien glaubwürdig zu machen

1. **Frische Suche ab einem Abbruchpunkt statt Rollout-Return** (EfficientZero-Rezept)
   [Q-sek, Quelle 27]. Übertragen: Zwangs-Trajektorie nur bis Zug k, ab dort **freies
   Selbstspiel beider Seiten**; das Value-Ziel kommt aus dem freien Teil. Das ist
   funktional identisch zu Go-Exploit-Startpositionen (F1.1), nur von der anderen Seite
   konstruiert – und es beseitigt das Off-Policy-Problem an der Wurzel statt es zu
   gewichten.
2. **Getrennte Value-Köpfe je Regime.** **[E], kein direkter Beleg gefunden.** Der
   nächste belegte Verwandte ist KataGos zweiter, anders gewichteter Policy-Kopf
   (Optimistic Policy, Quelle 2) und AZ_dbs dritter Kopf für den intrinsischen Wert
   (Quelle 10). Beide zeigen, dass ein zusätzlicher Kopf mit **anderem
   Stichprobengewicht** in Produktion trägt; für Value-Köpfe je Regime habe ich keinen
   Präzedenzfall.
3. **Importance Weighting: eher Warnung als Rezept.** [Q-sek, aus Quellensammlung F4]:
   "when importance ratios become heavy-tailed due to lag, hard clipping mechanisms
   become overly aggressive and zero out gradient contributions from many stale samples,
   leading to utilization collapse". **[E]** Bei einer deterministisch erzwungenen Seite
   ist das Importance-Ratio zum Netz-Prior in vielen Zuständen nahe Null oder sehr groß –
   also genau der Heavy-Tail-Fall. Ich würde IS hier **nicht** empfehlen.

---

## F5. Priorisierte Empfehlungsliste (max. 5)

Reihenfolge = Erwartungswert pro Aufwand. Aufwand: klein / mittel / groß.

### 1. Q-Skalierung der Suche messen und temperieren (plus Wurzel-Policy-Temperatur)

- **Mechanismus gegen Diagnose 4:** greift direkt am Veto an. Wenn der Value-Term
  rechnerisch mit Faktor ~14 auf die Prior-Logits wirkt (F2.2, [E]-Herleitung aus
  [Q, Quelle 12]), ist jede prior-seitige Maßnahme wirkungslos, solange dieser Faktor
  steht. Zusätzlich Wurzel-Temperatur nach KataGo [Q, Quelle 2].
- **Aufwand:** klein. Zwei Konstanten und eine Temperatur, keine Netzänderung, kein
  neues Training. Direkt in der bestehenden gepaarten Arena messbar; die Bau-Grundrate
  ist die Zielgröße, Elo der Wächter.
- **Größtes Risiko:** ein schwächerer Value-Einfluss kostet Spielstärke. Es kann sein,
  dass die Bau-Grundrate erst bei einem Setting steigt, das messbar Elo verliert. Dann
  ist das aber ein **Befund**, kein Fehlschlag: er quantifiziert den Preis des Vetos.
- **Verhältnis zu UVFA:** **Vorbedingung.** Ohne diese Messung ist nicht entscheidbar,
  ob der UVFA-Flag überhaupt eine Chance hat, in der Suche anzukommen.

### 2. Startpositions-Archiv statt Zwangs-Trajektorien

- **Mechanismus gegen Diagnose 4:** löst beide Hälften. (i) Der Value-Kopf bekommt
  Stichproben aus Stellungen mit halbfertigen Spalten, die er sonst nie sieht –
  aber **ab dem Startpunkt On-Policy**, also mit glaubwürdigem Ziel (F4.2/F4.3).
  (ii) Die Kontexte sind unterscheidbar, weil der Spaltenfortschritt auf dem Brett
  sichtbar ist; das behebt genau den Punkt "widersprüchliche Ziele auf ununterscheidbaren
  Kontexten".
- **Belege:** Go-Exploit [Q, Q7], RGSC +77/+89 Elo [Q, Q8], KataGo-Produktionskonfig
  `startPosesFromSgfDir` / `hintPosesDir` / `sidePositionProb` [Q, Q3].
- **Umsetzung:** aus dem **schon vorhandenen** 16.000-Partien-Zwangskorpus die
  Stellungen mit 3–5 gefüllten Spaltenfeldern extrahieren und als Startpositionen
  einspeisen. Der teure Teil ist bereits bezahlt.
- **Aufwand:** mittel (Selfplay-Einstiegspunkt, Positionsarchiv, Gewichtung).
- **Größtes Risiko:** Verteilungsverschiebung des Trainingskorpus insgesamt; wenn der
  Startpositionsanteil zu hoch ist, verlernt das Netz die Eröffnung. KataGos Defaults
  liegen bei sehr kleinen Anteilen (`sidePositionProb = 0.020`), das ist die
  Größenordnung, an der man sich orientieren sollte.
- **Verhältnis zu UVFA:** **ergänzt**, und ist mein Favorit als *Ersatz erster Wahl*,
  falls Maßnahme 3 wieder null liefert. Es ist die einzige Maßnahme in dieser Liste,
  die den Henne-Ei-Kreis mechanisch durchschneidet, ohne dass irgendeine Seite eine
  fremde Politik spielen muss.

### 3. UVFA-Regimeflag, aber mit Dropout, Guidance-Skala und Leakage-Wächter

- **Mechanismus:** wie geplant, plus drei belegte Zutaten:
  (i) **Conditioning-Dropout + Guidance-Skala w > 1** zur Spielzeit [Q-sek, Q20], damit
  der Regler über die 34,6-%-Trainingsverteilung hinaus extrapoliert statt sie zu
  kopieren (Fallstrick aus [Q-sek, Q19]);
  (ii) **beide Modi im selben Training** wie bei AlphaStar [Q-sek, Q9] und AZ_db
  [Q, Q10] – One-Hot am Input ist dort die belegte Bauform, additiv und
  bestandskompatibel;
  (iii) Pseudo-Reward bzw. Stichprobengewicht auf Regime-Treue statt reiner
  Zug-Imitation [Q-sek, Q9].
- **Aufwand:** mittel (Training) bis groß, wenn Guidance zur Spielzeit zwei
  Netzauswertungen je Knoten kostet – auf CPU bei 400 Sims relevant.
- **Größtes Risiko:** **Flag-Leakage** (F3.2, Punkt 3). Der Flag korreliert im
  vorhandenen Korpus mit einer Seite, die 45,7 % gewinnt. Pflicht-Wächter vor jeder
  Stärkemessung: **Value-Kopf-Ausgabe bei Flag=0 gegen Flag=1 auf identischen
  Stellungen**. Ist der mittlere Versatz systematisch negativ, misst der Flag das
  Handicap und nicht den Stil, und der Zuschnitt ist erledigt, bevor Arena-Zeit
  verbrannt wird.
- **Verhältnis zu UVFA:** **das ist der Zuschnitt**, geschärft.

### 4. Suchnutzen-Term auf Spaltenfortschritt (KataGo-`staticScoreUtility`-Analogon), abklingend

- **Mechanismus gegen Diagnose 4 und gegen F6:** verankert die mehrrundige Absicht
  dort, wo sie jeden Zug neu gewinnen muss – im **Leaf-Nutzen der Suche**, nicht im
  Value-Ziel. Ein kleiner Bonus proportional zum Spaltenfortschritt, der über die
  Runden gegen 0 abklingt, macht Teilfortschritt in der Suche sichtbar, ohne dass
  irgendein Kopf neu trainiert werden muss.
- **Belege:** KataGo trennt in Produktion Gewinnwahrscheinlichkeit und einen
  **separaten Score-Nutzenterm** (`staticScoreUtilityFactor`, `dynamicScoreUtilityFactor`)
  [Q-sek, Q-KataGo-Konfig] und korrigiert Leaf-Nutzen laufzeitgelernt über Subtree Value
  Bias mit λ ≈ 0,35 [Q, Q2]. Die Klasse "additiver Leaf-Nutzenterm neben dem
  Value-Kopf" ist damit produktionsbelegt.
- **Aufwand:** klein bis mittel.
- **Größtes Risiko:** Es ist ein Heuristik-Knopf mit Verzerrungspotenzial, und im
  Projekt gibt es bereits einen Formungsterm auf Wertungsplatten in der Heuristik, der
  als Elo-Anker gilt. **Deshalb ausdrücklich: nur im Netz-Spieler, nicht am Anker.**
  Zweites Risiko: ein nicht abklingender Term kostet in Runde 5 Punkte.
- **Verhältnis zu UVFA:** **ergänzt**, und ist der billigste Weg, die Hypothese
  "das Verhalten fehlt nur, weil Teilfortschritt keinen Nutzen hat" überhaupt zu testen.
  Ein positives Ergebnis hier würde den UVFA-Zuschnitt teilweise überflüssig machen.

### 5. Optimistic-Policy-Kopf plus Policy-Surprise-Weighting

- **Mechanismus:** überwichtet im Training genau die Stichproben, in denen unerwartet
  gute Kurzfrist-Ergebnisse eintraten, und lenkt zur Testzeit die Zugauswahl [Q, Q2].
  Für uns: die seltenen Partien, in denen eine Spalte *doch* fertig wurde und der
  Ausgang überraschend gut war, bekommen Gewicht – ohne Zwang, ohne fremde Politik,
  ohne Value-Ziel-Umbau (der 3× negativ war).
- **Aufwand:** klein bis mittel (zusätzlicher Kopf + Stichprobengewichtung).
- **Größtes Risiko:** Optimismus in einem Spiel mit verdeckter Information kann
  systematisch überziehen; und der Effekt ist bei KataGo nicht isoliert quantifiziert,
  den ich gefunden hätte.
- **Verhältnis zu UVFA:** **ergänzt**, orthogonal.

**Nicht empfohlen, obwohl naheliegend:** Hindsight-Relabeling auf "welche Spalten wurden
fertig" (F1.4, politikabhängiges Ziel – im Projekt schon einmal in genau diese Falle
gelaufen); Importance Weighting auf dem Zwangskorpus (F4.3, Heavy-Tail); Max-Backup als
Ersatz für Mean-Backup (F6.3).

---

## F6. Alternativen und Ergänzungen zur Suche selbst

Vorbemerkung im Sinne des Auftrags: der bestehende Gumbel-Pfad ist stark und
golden-getestet. Die Beleglage unten stützt **keinen** Komplettumbau. Was sie stützt,
sind zwei additive Eingriffe (F6.1 Punkt 3, F6.3 Punkt 1) und einen Prior-Eingriff
(F6.2 Punkt 1).

### F6.1 Plan-/Absichts-Persistenz über Züge

**Belegt, Paper-Ebene:** **OptionZero** [Q-sek, Quelle 21], ICLR 2025 Oral. Ein
Options-Netz in MuZero entdeckt Optionen autonom im Selbstspiel; das Dynamik-Netz
liefert Übergänge für ganze Optionen, wodurch "searching deeper under the same
simulation constraints" möglich wird. Gemessen auf **26 Atari-Spielen**, +131,58 %
mittlerer human-normalisierter Score gegenüber MuZero. **Brettspiel-Evidenz habe ich
nicht verifiziert.** Voraussetzung ist ein **gelerntes Dynamikmodell** – wir haben ein
exaktes; die Übertragung ist nicht trivial.

**Belegt, ältere Linie:** Subgoal-basierte temporale Abstraktion in MCTS
[Q-sek, Quelle 29, IJCAI 2019] und Makro-Aktionen allgemein: "Macro-actions allow for
temporal extension over multiple time steps and increase the effective search depth
requiring fewer iterations to plan over longer horizons", mit dem bekannten Preis
"a loss of optimality due to the fixed internal structure of the options" (Sutton et al.).

**[E] Die für uns wichtigste Einordnung dieses ganzen Abschnitts:** unsere
Absichts-Persistenz ist **nicht** primär ein Gedächtnisproblem. Eine halbfertige Spalte
steht sichtbar auf dem Brett; der Suchbaum kann sie in jedem Knoten lesen. Was fehlt,
ist nicht die *Erinnerung* an den Plan, sondern der **Preis für Teilfortschritt**.
Deshalb rangiert bei mir Maßnahme F5-4 (Nutzenterm) deutlich vor Optionen/HRL: sie
adressiert dieselbe Beobachtung mit einem Bruchteil des Umbaus. Eine
Options-/Makro-Aktions-Maschinerie würde ich erst ansehen, wenn F5-4 zeigt, dass
Teilfortschritt bepreist ist und trotzdem nicht gebaut wird.

### F6.2 Andere Suchparadigmen

**Belegt und brettspielrelevant:** Baier & Winands, "MCTS-Minimax Hybrids with State
Evaluations", JAIR 62 (2018) [Q-sek, Quelle 22]. Ausgangsbefund wörtlich sinngemäß:
MCTS spielt in taktischen Domänen schwächer als Minimax, "partly due to its highly
selective search and **averaging value backups**, which make it susceptible to traps".
Drei Hybride getestet; **der stärkste ist der, bei dem Minimax die Knoten-Priors
berechnet** (MCTS-IP-M-k), getestet in Othello, Breakthrough und Catch the Lion; in
Breakthrough schlägt der Hybrid beide Bestandteile einzeln.

**[E]** Das ist die einzige Familie in F6.2, die zu unseren Constraints passt und
belegt trägt – und sie ist **additiv**: Minimax-berechnete Priors ändern die
Zugauswahl-Verteilung, nicht das Suchgerüst. Interessanterweise haben wir dafür schon
das Material (Round-5-Alpha-Beta ist laut Projektgedächtnis live und exakt endaware).
Die Übertragung wäre: einen flachen, exakten Suchwert als **Prior-Modifikator** für die
Bauzüge nutzen, statt ihn nur als Blattbewertung zu verwenden. Das ist eine Hypothese,
kein Beleg für unser Spiel.

**Nicht empfohlen:** Beam-/Plan-Suche über Zugsequenzen und MPC-artige Ansätze. Ich habe
für Zwei-Spieler-Brettspiele mit Gegnerzügen dazwischen keine belegte Engine-Anwendung
gefunden; die Literatur dazu ist Einzelagenten-/Regelungstechnik. **[E]** Bei
gegnerischem Zug zwischen unseren Zügen ist eine Sequenz-Festlegung ohnehin nur unter
Annahmen über den Gegner haltbar.

### F6.3 Backup-Varianten

**Belegt:** Power-Mean-Backup [Q-sek, Quelle 23, IJCAI 2020] interpoliert über einen
Koeffizienten zwischen Mittelwert und Maximum und "balanc[es] between a safe but slow
update and a greedy but misleading one". Khandelwal et al. [Q-sek, Quelle 24, ICML 2016]
analysieren komplexe Backup-Strategien systematisch.

**[E] Nüchterne Einordnung:** Diese Arbeiten sind auf RL-Benchmarks belegt, nicht in
Top-Brettspiel-Engines. Weder KataGo, Leela noch Lc0 haben Mean-Backup durch Max-Backup
ersetzt – aus dem gut bekannten Grund, dass Max-Backup unter Funktionsapproximation
Bewertungsrauschen einsammelt. Bei uns wäre das besonders gefährlich: ein
Max-Backup würde genau die seltenen, optimistisch fehlbewerteten Bauzüge hochziehen,
also wie eine Verhaltensänderung aussehen und dabei Spielstärke kosten.
**Nicht empfohlen als Umbau.**

**Was stattdessen belegt trägt:** KataGos zwei produktive Eingriffe an derselben Stelle,
beide ohne Backup-Umbau: Subtree Value Bias Correction (λ ≈ 0,35 auf dem Knoten-Nutzen)
und Optimistic Policy (optimistische Gewichtung im *Trainings*-Ziel eines zweiten
Policy-Kopfs) [Q, Quelle 2]. Das ist der pragmatische Ersatz für "Risk-seeking-Backup":
Optimismus im Ziel und in der Zugauswahl statt im Backup-Operator.

### F6.4 Constraint-Prüfung (CPU, kleines Netz, 400 Sims, Determinismus)

| Mechanismus | CPU/400 Sims | Determinismus | Engine-belegt |
|---|---|---|---|
| Q-Skalierung / Wurzeltemperatur | kostenlos | unverändert | ja (KataGo) |
| Startpositions-Archiv | nur Trainingszeit | unverändert | ja (KataGo, Go-Exploit, RGSC) |
| UVFA-Flag (One-Hot am Input) | ~kostenlos | unverändert | ja (AZ_db, AlphaStar, KataGo-Regelkanäle) |
| Guidance-Skala w > 1 | **2 Auswertungen/Knoten** | unverändert | nein, nur RL-Paper |
| Leaf-Nutzenterm Spaltenfortschritt | kostenlos | unverändert | ja (KataGo Score-Utility) |
| Optimistic-Policy-Kopf | +1 Kopf | unverändert | ja (KataGo) |
| Subtree Value Bias | billig | **bricht Reproduzierbarkeit** – Zustand lebt über Züge hinweg | ja (KataGo) |
| Optionen / OptionZero | Dynamiknetz nötig | unverändert | nein (Atari) |
| Max-/Power-Mean-Backup | kostenlos | unverändert | nein |

**[E]** Die Determinismus-Warnung bei Subtree Value Bias ist wichtig, weil im Projekt
deterministische Reproduzierbarkeit Hausanforderung ist: die Bias-Tabelle ist
**globaler, über Suchen hinweg mutierender Zustand**. Eine Stellung liefert dann nicht
mehr denselben Zug unabhängig von der Vorgeschichte. Falls dieser Mechanismus je
angefasst wird, muss die Tabelle je Partie zurückgesetzt und in den Determinismus-Check
einbezogen werden.

---

## Quellenliste

1. David J. Wu: *Accelerating Self-Play Learning in Go* (KataGo, AAAI-20 RLG Workshop) –
   https://arxiv.org/abs/1902.10565 · Volltext: https://arxiv.org/pdf/1902.10565
2. KataGo, `docs/KataGoMethods.md` (Optimistic Policy, Policy Surprise Weighting,
   Subtree Value Bias Correction, Root Policy Softmax Temperature) –
   https://github.com/lightvector/KataGo/blob/master/docs/KataGoMethods.md
3. KataGo, `cpp/configs/training/selfplay1.cfg` (startPoses, hintPoses, sidePositionProb) –
   https://github.com/lightvector/KataGo/blob/master/cpp/configs/training/selfplay1.cfg
4. KataGo Release v1.3 (Handicap play, playoutDoublingAdvantage, unbalanced playouts) –
   https://github.com/lightvector/KataGo/releases/tag/v1.3
5. KataGo Release v1.15.0 (Human-like play, `humanSLProfile`, Rang-/Jahrgangs-Regler) –
   https://github.com/lightvector/KataGo/releases/tag/v1.15.0
6. KataGo, `cpp/neuralnet/nninputs.cpp` (globale Input-Kanäle: Komi, Regeln, Encore) –
   https://github.com/lightvector/KataGo/blob/master/cpp/neuralnet/nninputs.cpp
7. Trudeau & Bowling: *Targeted Search Control in AlphaZero for Effective Policy
   Improvement* (Go-Exploit, AAMAS 2023) – https://arxiv.org/abs/2302.12359
8. *Regret-Guided Search Control for Efficient Learning in AlphaZero* (2026) –
   https://arxiv.org/abs/2602.20809
9. Vinyals et al.: *Grandmaster level in StarCraft II using multi-agent reinforcement
   learning* (Nature 2019) – https://www.nature.com/articles/s41586-019-1724-z ·
   Volltext-PDF: https://storage.googleapis.com/deepmind-media/research/alphastar/AlphaStar_unformatted.pdf
10. Zahavy et al.: *Diversifying AI: Towards Creative Chess with AlphaZero* (AZ_db) –
    https://arxiv.org/abs/2308.09175 · HTML: https://arxiv.org/html/2308.09175
11. Danihelka et al.: *Policy Improvement by Planning with Gumbel* (ICLR 2022) –
    https://openreview.net/forum?id=bERaNdoegnO
12. DeepMind mctx, `mctx/_src/qtransforms.py` (`qtransform_completed_by_mix_value`,
    `value_scale=0.1`, `maxvisit_init=50.0`) –
    https://github.com/google-deepmind/mctx/blob/main/mctx/_src/qtransforms.py
13. Grill et al.: *Monte-Carlo Tree Search as Regularized Policy Optimization* (ICML 2020) –
    https://arxiv.org/abs/2007.12509
14. Jacob, Wu, Farina, Lerer, Hu, Bakhtin, Andreas, Brown: *Modeling Strong and Human-Like
    Gameplay with KL-Regularized Search* (piKL, ICML 2022) – https://arxiv.org/abs/2112.07544
15. Bakhtin et al.: *Mastering the Game of No-Press Diplomacy via Human-Regularized
    Reinforcement Learning and Planning* (RL-DiL-piKL) – https://arxiv.org/abs/2210.05492 ·
    Cicero (Science 2022): https://www.science.org/doi/10.1126/science.ade9097
16. Schaul et al.: *Universal Value Function Approximators* (ICML 2015) –
    https://proceedings.mlr.press/v37/schaul15.html
17. Andrychowicz et al.: *Hindsight Experience Replay* (NeurIPS 2017) –
    https://arxiv.org/abs/1707.01495
18. Tang et al.: *Maia-2: A Unified Model for Human-AI Alignment in Chess* (NeurIPS 2024) –
    https://arxiv.org/abs/2409.20553
19. Paster, McIlraith, Ba: *You Can't Count on Luck: Why Decision Transformers and RvS
    Fail in Stochastic Environments* (ESPER) – https://arxiv.org/abs/2205.15967
20. *Policy Gradient Guidance Enables Test Time Control* (CFG in on-policy RL) –
    https://arxiv.org/abs/2510.02148
21. Huang, Peng, Guei, Wu: *OptionZero: Planning with Learned Options* (ICLR 2025 Oral) –
    https://arxiv.org/abs/2502.16634 · Code: https://github.com/rlglab/optionzero
22. Baier & Winands: *MCTS-Minimax Hybrids with State Evaluations* (JAIR 62, 2018) –
    https://www.jair.org/index.php/jair/article/view/11208
23. Dam et al.: *Generalized Mean Estimation in Monte-Carlo Tree Search* (IJCAI 2020) –
    https://www.ijcai.org/proceedings/2020/0332.pdf
24. Khandelwal et al.: *On the Analysis of Complex Backup Strategies in Monte Carlo Tree
    Search* (ICML 2016) – https://proceedings.mlr.press/v48/khandelwal16.pdf
25. *AlphaZero in Sparsely Rewarded Games: Limits and Auxiliary Supervision* (AZAL, 2026) –
    https://arxiv.org/abs/2607.08984
26. Schrittwieser et al.: *Online and Offline Reinforcement Learning by Planning with a
    Learned Model* (MuZero Reanalyse) – https://arxiv.org/abs/2104.06294
27. Ye et al.: *Mastering Atari Games with Limited Data* (EfficientZero, dynamischer
    Value-Ziel-Horizont) – https://arxiv.org/abs/2111.00210
28. *Subgoal-Based Temporal Abstraction in Monte-Carlo Tree Search* (IJCAI 2019) –
    https://www.ijcai.org/proceedings/2019/0772.pdf
29. Wang et al.: *Adversarial Policies Beat Superhuman Go AIs* –
    https://arxiv.org/abs/2211.00241
30. KataGo, `cpp/configs/gtp_example.cfg` (playoutDoublingAdvantage,
    dynamicPlayoutDoublingAdvantageCapPerOppLead, Score-Utility-Faktoren) –
    https://github.com/lightvector/KataGo/blob/master/cpp/configs/gtp_example.cfg

Direkt im Volltext/Primärtext abgerufen: 2, 3, 4, 6, 7, 8, 10, 12, 25, 30.
Nur über Suchergebnis-Snippets: 1, 5, 9, 11, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22,
23, 24, 26, 27, 28, 29.

---

## Fazit (10 Zeilen)

1. Kein Paper behandelt unseren Fall direkt; alles Folgende ist belegte Übertragung.
2. Der stärkste Einzelfund ist quantitativ: bei Gumbel skaliert der Value-Term mit
   `(maxvisit_init + max_visits) · value_scale` – bei 400 Sims grob Faktor 14 gegen
   1,6 Logits Prior-Vorsprung. Klonen in den Prior *kann* strukturell nicht gewinnen.
3. Damit ist Befund (d) erklärt und nicht mehr rätselhaft: die Interventionsebene war
   zu schwach, nicht das Signal.
4. Erste Maßnahme ist deshalb billig und ohne Training: Q-Skalierung und
   Wurzel-Policy-Temperatur messen und temperieren, Bau-Grundrate als Zielgröße.
5. Der belegteste Struktur-Hebel in echten Engines ist die Startzustandsverteilung, nicht
   das Curriculum: Go-Exploit, RGSC (+77/+89 Elo) und KataGos `startPoses`/`hintPoses`/
   `sidePositionProb` in Produktion.
6. Für uns heißt das: aus dem vorhandenen 16k-Zwangskorpus Stellungen mit halbfertigen
   Spalten als **Startpositionen** ziehen, ab dort frei spielen – das erzeugt die
   fehlenden Value-Daten On-Policy und ohne fremde Politik.
7. Genau daran scheiterte (c): erzwungene Trajektorien liefern V einer Politik, die das
   Netz nie spielt; das ist der bekannte Off-Policy-Value-Target-Fehler, und
   EfficientZeros Rezept dagegen ist strukturell dieselbe Abschneide-Idee.
8. Der UVFA-Zuschnitt hat belegte Präzedenzfälle (AZ_db: One-Hot am Input, +29,6 bis
   +50,3 Elo bei 400 Sims; AlphaStar-z; KataGo-Regelkanäle) – ihm fehlen aber
   Conditioning-Dropout mit Guidance-Skala und ein Leakage-Wächter auf dem Value-Kopf.
9. Der billigste ungetestete Mechanismus gegen die Plan-Persistenz ist kein Suchumbau,
   sondern ein abklingender Leaf-Nutzenterm auf Spaltenfortschritt (KataGo-Score-Utility-
   Analogon) – nur im Netzspieler, niemals am Heuristik-Elo-Anker.
10. Max-Backup, Hindsight-Relabeling und Importance Weighting auf dem Zwangskorpus rate
    ich ab; belegt tragfähiger sind KataGos Optimistic Policy und Policy-Surprise-Weighting.
