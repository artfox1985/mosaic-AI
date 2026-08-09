# Vorregistrierung: Prior-Blindfleck & Wurzelbreite (externes Review R2)

**Angelegt 2026-08-09, VOR allen Laeufen.** Anlass: zweite Runde
externes Feedback, Gumbel-spezifisch (drei behauptete Engpaesse).
Zwei der drei Punkte sind bereits entschieden bzw. architektonisch
entschaerft (siehe "Nicht-Tasks" unten); dieser Prereg deckt den einen
Punkt, der eine echte, nie gemessene Luecke trifft.

> **NICHT EINGETAKTET.** Reines Design-Dokument, solange die
> v21-Queue (A, D, E3b, ISMCTS-k) laeuft und der Nutzer bewertete
> Server-Partien spielt. Reihenfolge: erst E (offline, billig, Gate),
> F nur wenn E feuert.

## Befundlage, die den Task rechtfertigt

Die Wurzel-Kandidatenmenge wird EINMAL vor der ersten Simulation
fixiert (Gumbel-Top-m auf logit+Noise); Sequential Halving kann sie
nur verkleinern, nie erweitern. Gemessene Abdeckung
(`evaluations/dome_split_diagnose.json`, n=50 Stellungen, 400 Sims):

| Groesse | Median | Min | Max |
|---|---|---|---|
| legale Wurzel-Aktionen | 50 | 9 | 158 |
| davon von Gumbel betrachtet | 16 | — | 16 |
| **Abdeckungsquote** | **32%** | **10,1%** | 100% |

Bereits gemessen und H0: m INNERHALB 8-16 (m=9-Formel vs m=16 fest
@150 Sims, McNemar p=0,54, Messung 2; 16-vs-8 @400 Sims ein Wash).
**Nie gemessen: m deutlich GROESSER als 16.** Der Regler existiert
schon und umgeht die Klemme (`gumbel_top_m_override` liefert m direkt
zurueck, `gumbel_top_m_for_budget` klemmt nur den Formel-Zweig auf
16) -- die Messung braucht keine Code-Aenderung.

Verschaerfung gegenueber der externen Formulierung: der Blindfleck ist
nicht nur pro Stellung wirksam, sondern **selbstverstaerkend**. Die
Policy-Ziele sind Besuchszahlen genau dieser 16er-Menge; eine
systematisch nie betrachtete Zugfamilie bekommt nie Prior-Masse und
wird darum auch in der naechsten Generation nicht betrachtet. Das ist
das Risiko, das eine Arena-Einzelmessung NICHT sieht.

## Task E -- Prior-Blindfleck-Rate (offline, Gate)

Instrument: frozen_v2 + die 1.148 Orakel-Labels (bereits gebaut,
0 Fehler). Fuer jeden Zustand mit Orakel-Label: Prior des Champions
(`v21_2d_brierbest`) berechnen, absteigend sortieren, pruefen ob der
Orakel-Top-1 innerhalb der ersten m=16 liegt.

**AMENDMENT 2026-08-09, VOR dem Lauf auf dem Champion.** Bei der
Werkzeug-Sichtung zeigte sich, dass `tools/oracle_metrics.py` die
rauschfreie Variante bereits als `prior_recall_at_16` berechnet
(Zeile 233/280) -- Task E ist damit ueberwiegend Auswertung, kein
Neubau. Dabei waren die Werte der v14/v15-Aera auf frozen_v1 sichtbar
(recall@16 ~0,97-0,98, also Miss-Rate 2-3%). Das ist offengelegt,
weil danach amendiert wird; die 5%-Schwelle bleibt UNVERAENDERT, es
wird nur eine STRENGERE, engine-treue Metrik ergaenzt:

Die Engine waehlt nicht die Prior-Top-m, sondern **Gumbel-Top-m auf
logit+Gumbel(0,1)** -- mathematisch eine Ziehung ohne
Zuruecklegen aus der Prior-Verteilung. Selbst ein Zug auf Prior-Rang 1
hat damit KEINE garantierte Aufnahme, und ein Zug auf Rang 20 hat eine
echte Chance. Die rauschfreie Recall-Zahl ist deshalb weder obere noch
untere Schranke, sondern eine andere Groesse. Entscheidungsmetrik ist
ab hier die rausch-treue Variante.

Metriken (alle deskriptiv ausser der Entscheidungsmetrik):
- **Entscheidungsmetrik: `miss_rate_gumbel_m16`** = 1 - erwartete
  Aufnahme-Rate des Orakel-Top-1 unter dem ECHTEN Verfahren
  (logit + Gumbel(0,1), Top-16), Monte-Carlo mit >=200 Ziehungen je
  Zustand, fester Seed, ueber die volle legale Aktionsmenge.
- Deskriptiv daneben: `miss_rate_top16` (rauschfrei) = Anteil der
  Zustaende, in denen der Orakel-Top-1 NICHT in den Prior-Top-16
  liegt -- Vergleichbarkeit zur v14/v15-Reihe.
- Zusatz deskriptiv: dieselbe Rate fuer Top-8/Top-32/Top-64;
  Rangverteilung des Orakel-Top-1 im Prior; Aufschluesselung nach
  Runde und nach Anzahl legaler Aktionen (der 10%-Abdeckungs-Fall ist
  vermutlich der interessante).
- Kein Noise-Kanal, weil rein deterministisch (kein Gumbel-Noise, kein
  Seed) -- die Rate ist eine Eigenschaft von Netz+Orakel-Set.

**Entscheidungsregeln (vorab):**
1. `miss_rate_gumbel_m16 < 5%` **und** m=32 bringt keine relevante
   Verbesserung ⇒ Punkt GESCHLOSSEN, **kein Arena-Budget**. Externe
   Kritik dokumentiert als "gemessen, Effektgroesse zu klein".
2. `miss_rate_gumbel_m16 >= 5%` ⇒ Task F wird eingetaktet, mit der
   gemessenen Rate als Erwartungsgroesse.
2b. Klafft rauschfrei und rausch-treu weit auseinander (rauschfrei
   <5%, rausch-treu >=5%), ist der Befund NICHT "Breite zu klein",
   sondern "**Gumbel-Rauschen wirft gute Zuege raus**". Dann ist der
   erste Arm nicht m=32, sondern die Rausch-Temperatur an der Wurzel
   -- eigener Prereg, kein stiller Wechsel der Task-F-Arme.
3. Faellt die Rate stark mit m (z.B. 12% @16 → 2% @32), ist m=32 der
   primaere F-Arm; bleibt sie flach, ist der Prior selbst das Problem
   und nicht die Breite -- dann KEIN Breiten-Task, sondern
   Prior-Qualitaet (existierende Orakel-Metriken) als Weg.
4. Das Orakel ist ein tiefer-Such-Referenz, KEINE Wahrheit. Ein
   Orakel-Top-1 ausserhalb der Prior-Top-16 ist ein Kandidat fuer
   einen Blindfleck, kein Beweis eines verpassten Gewinnzugs.

Kosten: ~15 min, nur Inferenz auf 1.148 Zustaenden, keine Arena, kein
Self-Play.

## Task F -- Wurzelbreite gross (Arena, nur nach E-Gate)

Instrument `tools/paired_arena_env_ab.py` (Mehr-Arm, identische
Basis-Seeds), Regler `MOSAIC_GUMBEL_TOP_M`.

Arme a 400 Partien **@600 Sims** (Sockel-Budget, wo m=16 greift),
Basis-Seed 20260830:
- **m=16** (Default) = Kontrolle
- **m=32**
- **m=64**

**Explizite Budget-Arithmetik (vorab festgehalten, damit spaeter
niemand "Breite wurde bei gleicher Tiefe getestet" behauptet):** bei
festen 600 Sims verteilt Sequential Halving ueber ceil(log2(m))
Phasen. m=16 → 4 Phasen, ~150 Sims/Phase, ~9 je Kandidat in Phase 1;
m=32 → 5 Phasen, ~120/Phase, ~3,8 je Kandidat; m=64 → 6 Phasen,
~100/Phase, ~1,6 je Kandidat. Breite wird also mit Tiefe BEZAHLT.
Ein H0 bei m=64 ist deshalb NICHT als "Breite hilft nicht"
interpretierbar, sondern nur als "Breite hilft nicht bei diesem
Budget". Ein Gewinn bei m=32 waere der aussagekraeftige Fall.

**Entscheidungsregeln (vorab):**
1. Gewinner = signifikant gegen die Kontrolle (exakter zweiseitiger
   McNemar auf diskordanten Paaren, p<0,05) **und** Frisch-Seed-
   Replikation (Statistik-Regel 3). Alles andere = H0.
2. Score-Analyse auf **Block-Ebene** (stehende Regel: Paar-SEs
   unterschaetzen massiv).
3. Ein replizierter Gewinner wird nicht direkt Preset, sondern
   braucht eine eigene Anker-Kante (Gating Champion+Konfig vs
   Champion m=16), damit bewertete Partien Elo-regelkonform bleiben.
4. Alle H0 ⇒ Wurzelbreite gilt fuer die WDL-/2D-Aera als geschlossen
   (dritter H0-Befund der Wurzel-Regler-Familie nach m-Formel und
   c_scale); Wiedereroeffnung nur nach Aera-Wechsel oder wenn Task E
   in einer spaeteren Generation eine deutlich hoehere Miss-Rate
   zeigt.

Kosten: 3x400 @600 Sims, CPU-Bahn, ~4-5h.

## Task G -- c_scale-Nachmessung in der WDL-Aera (deskriptiv)

`tools/gumbel_scale_calibration.py` lief auf `v18_best` (Vor-WDL):
delta_q Median 0,0073, delta_ln(prior) Median 1,11, Verhaeltnis
sigma/Prior 1,23, max_N Median 96, c_scale fuer Gleichgewicht 0,81 --
also "q und Prior wiegen praktisch gleich schwer", keine Dominanz.
Der WDL-Kopf hat die Q-SKALA geaendert (P(Sieg) statt gestauchter
Marge), und "Aera-Grenzen entwerten alte Befunde" ist unsere eigene
Regel. Darum: dasselbe Tool einmal auf `v21_2d_brierbest`,
**rein deskriptiv, keine Entscheidungsmetrik, kein Regler-Wechsel**
(die c_visit/c_scale-Familie ist per PREREG_ownership_gumbel §B1
geschlossen; Wiedereroeffnung nur bei Verhaeltnis > ~3 oder < ~0,3,
d.h. echter Dominanz einer Seite). Kosten ~10 min.

## Nicht-Tasks (externe Punkte, die bereits entschieden sind)

- **"Q-Wert-Skalierung instabil / Floor-Shaping blaest die Q-Varianz
  auf"**: gemessen (Task #18, Zahlen oben) -- kein Dominanz-Befund.
  Zusaetzlich ist der behauptete Varianz-Treiber AUS: der
  Aggressions-Blend steht nach der Neukartierung ueberall auf w=0
  (alle 3 Arme H0), Floor-Shaping ist w-gewichtet und beschraenkt.
  Task G schliesst nur die Aera-Luecke.
- **"Sequential Halving verschwendet Budget in taktisch scharfen
  Stellungen, die eine tiefe Linie brauchen"**: Runde 5 -- die einzige
  Phase mit echten Zwangsfolgen und vollstaendiger Information --
  laeuft NICHT ueber Gumbel, sondern ueber den exakten
  Alpha-Beta-Loeser (`round5.rs`, in allen Sucheinstiegen, exakte
  endaware-Bewertung). Die taktisch schaerfste Spielphase ist geloest,
  nicht gesucht. In R1-4 ist die Struktur Draft + Zufall am
  Rundenuebergang, nicht "eine tiefe erzwungene Linie".
- **Adaptives Halving-Budget**: nicht gebaut, nicht eingetaktet. Die
  Wurzel-Regler-Familie hat wiederholt H0 geliefert (m-Formel p=0,54,
  c_scale folgenlos) und einmal SCHADEN (Denial-Tie-Break -13,75pp).
  Ein Adaptivitaets-Mechanismus wird nicht gebaut, bevor Task E zeigt,
  dass die Kandidatenmenge ueberhaupt falsch ist.
- **Der extern vorgeschlagene Diagnose-Weg "Prior-Miss-Rate gegen den
  R5-Alpha-Beta-Loeser"** funktioniert so nicht: in R5 laeuft keine
  Gumbel-Wurzelauswahl, es gibt dort also keine Top-m-Menge zum
  Vergleichen. Task E ersetzt ihn durch das Orakel-Set, das genau
  diese Referenzrolle hat und schon gebaut ist.

---
## ERGEBNIS Task E (2026-08-09): REGEL 1 -- PUNKT GESCHLOSSEN

Lauf am Champion `v21_2d_brierbest` gegen `frozen_v2_oracle_labels.json`,
n=930 (Runden 1-4; Runde 5 per Altcode ausgeschlossen, dort exakter
Loeser). Belegstelle `evaluations/t_e_prior_blindfleck.json`.

| m | rauschfrei `prior_recall_at_m` | rausch-treu `gumbel_recall_at_m` |
|---|---|---|
| 8 | 0,9215 | 0,8922 |
| **16** | 0,9978 | **0,9879** |
| 32 | 1,0000 | 0,99993 |
| 64 | 1,0000 | 1,0000 |

**Entscheidungsmetrik `miss_rate_gumbel_m16` = 1,21%** -- deutlich unter
der 5%-Schwelle, damit greift Regel 1: **Task F wird NICHT eingetaktet,
kein Arena-Budget.** Regel 2b greift ebenfalls nicht (rauschfrei 0,22%,
rausch-treu 1,21% -- die Kluft ist da, aber beide unter der Schwelle).

Zum zweiten, im Prereg nicht numerisch definierten Kriterium von Regel 1
("m=32 bringt keine relevante Verbesserung"): m=32 senkt die Miss-Rate um
**1,2 Prozentpunkte** (1,21% -> 0,007%). Diese Groesse ist einordbar,
weil die Arena die Staerke-Empfindlichkeit der Miss-Rate schon einmal
abgesteckt hat: **m=8 gegen m=16 bei 400 Sims war ein Wash** (Task #10,
2026-07-28, `v17_best` vs `v16_best`, 100 Paare, exakter McNemar
**p=1,0000** -- bei einer Diskordanz von 49 von 100 Paaren, d.h. m=8
aendert das Spiel massiv und ist trotzdem exakt gleich stark), und
zwischen diesen beiden liegen laut Tabelle **9,6 Prozentpunkte**
Miss-Rate (10,78% vs 1,21%). Ein bereits als folgenlos gemessener
Unterschied ist also ~8x groesser als der maximal noch erreichbare.

Zwei Einschraenkungen, damit der Anker nicht ueberdehnt wird:
1. Bei festen Sims kauft m=8 zugleich mehr Tiefe je Kandidat, der Wash
   ist ein NETTO-Effekt und isoliert den Abdeckungs-Term nicht.
2. **Task #10 stammt aus der v16/v17-Aera** (vor WDL, vor 2D) -- nach
   unserer eigenen Aera-Regel ist er damit nur noch ein Indiz, kein
   Beleg fuer heute. Das ist keine Kleinigkeit: Task G hat am selben Tag
   gezeigt, dass der Aera-Wechsel die sigma/Prior-Balance um 86%
   verschoben hat. Der aera-korrekte Anker ist die schwaechere Messung
   2 (m=9 vs m=16 **@150 Sims**, v20-Champion, p=0,54).
   **Die Schliessung haengt aber nicht am Anker**: die
   Entscheidungsmetrik selbst ist am AKTUELLEN Champion gemessen und
   liegt mit 1,21% vierfach unter der Schwelle. Der Anker ordnet nur
   die Restgroesse ein.

Abgrenzung zu Task G (wichtig, weil beide externen Punkte auf
verschiedene Stufen zielen): die Wurzel-Kandidatenmenge entsteht
ausschliesslich aus `logit + Gumbel(0,1)` -- **sigma(q) geht dort nicht
ein**. sigma wirkt erst beim Halbieren/Cullen und in der
Tiefe->=1-Auswahlregel. Task G kann die Task-E-Zahl daher nicht
entwerten, und umgekehrt.

**Die Aufschluesselung ist NICHT auswertbar** und wird bewusst nicht
interpretiert: der hoechste Bucket-Wert (33-64 Aktionen, 4,15% bei
n=149) entspricht ~6 Zustaenden gegen ~3,5 im Bucket >64 (2,86%,
n=122), und der "monoton steigende" Rundenverlauf (R1 0,77% -> R4
1,64%) sind ~2 gegen ~4 Zustaende. Alles Einzelzustands-Rauschen; die
Substruktur ist bei n=930 nicht aufgeloest. Festzuhalten ist nur:
**in allen Buckets niedrig**, inklusive des Falls mit >64 legalen
Aktionen, wo die Abdeckung nominell nur ~10-25% betraegt. Genau die
dort erwartete Haeufung tritt nicht auf.

Bemerkenswert und der eigentliche Grund fuer den Befund: die
Prior-Verteilung ist offenbar scharf genug, dass eine Ziehung ohne
Zuruecklegen aus ihr den Orakel-Top-1 fast immer mitnimmt, obwohl nur
32% der legalen Aktionen betrachtet werden. Die geringe ABDECKUNG ist
also kein Blindfleck, solange die Prior-Masse konzentriert ist -- die
Wurzelbreite ist die falsche Stelle zum Ansetzen, die Prior-QUALITAET
bleibt der Hebel (dafuer existieren die validierten Orakel-Metriken).

Selbsttest bestanden (m = Anzahl legaler Aktionen ⇒ Aufnahme-Rate exakt
1,0 in allen 930 Zustaenden). Additivitaets-Nachweis: die historische
v14-Zahl war nicht reproduzierbar, weil die 7 in
`task89_oracle_metrics.json` gescorten Checkpoints nicht mehr auf der
Platte liegen (Vorzustand, siehe NUM_ACTIONS-Orphaning). Ersatzweise --
und starker -- Pre-Edit- gegen Post-Edit-Modul auf `v18_2d`:
**bitgleich** ueber alle 952 Zeilen, `prior_recall_at_16` 0,9863445...
in beiden.

---
## ERGEBNIS Task G (2026-08-09): AERA-EFFEKT BESTAETIGT, KEINE WIEDEREROEFFNUNG

`tools/gumbel_scale_calibration.py --model v21_2d_brierbest --sims 400
--n-states 300`; Belegstelle `evaluations/t_g_gumbel_scale_v21.json`.
Identische Zustandsmenge wie Task #18 (n_used 233, n_skipped 67,
max_N-Median 96 in beiden -- die Halbierungs-Verteilung haengt am Budget,
nicht am Netz).

| Groesse | v18_best (#18) | v21 (G) |
|---|---|---|
| delta_q Median | 0,00734 | **0,01425** |
| delta_ln(prior) Median | 1,11036 | 1,11375 |
| **Verhaeltnis sigma/Prior** | **1,232** | **2,287** |
| c_scale fuer Gleichgewicht | 0,811 | 0,437 |

| Verhaeltnis je Runde | R1 | R2 | R3 | R4 |
|---|---|---|---|---|
| v18_best | 1,011 | 1,075 | 1,557 | 1,436 |
| **v21** | **1,908** | **2,818** | **2,972** | **2,527** |

**Der Mechanismus ist eindeutig**: `delta_ln(prior)` ist praktisch
unveraendert (1,110 -> 1,114), `delta_q` hat sich **verdoppelt**. Der
WDL-Kopf gibt P(Sieg) ueber den fast vollen [0,1]-Bereich aus, wo der
alte Kopf eine gestauchte tanh-Marge lieferte -- die
Geschwister-Q-Spreizung waechst entsprechend, und ueber
sigma(q) = (c_visit + max_N)·c_scale·q schlaegt das voll durch.

**Entscheid nach Prereg: KEINE Wiedereroeffnung.** Die vorab
festgelegte Schwelle war Verhaeltnis >~3 oder <~0,3 auf der
Gesamt-Kennzahl; 2,287 liegt darunter, c_visit/c_scale bleiben
unangetastet. Das wird ausdruecklich NICHT umgedeutet -- eine
nachtraegliche Schwellenverschiebung waere genau der Fehler, wegen dem
Task C zurueckgezogen wurde.

**Aber der Befund ist knapp und die Richtung eindeutig**, und das wird
hier festgehalten statt beschoenigt: R2 (2,818) und R3 (**2,972**)
liegen praktisch AUF der Schwelle, und ein weiterer Aera-Schritt von der
Groesse dieses einen (+86%) reisst auch die Gesamt-Kennzahl darueber.
Damit ist die externe Kritik an der Q-Skalierung **teilweise
bestaetigt**: in der v18-Aera wogen Q und Prior gleich schwer, heute
wiegt Q gut das Doppelte. Der Reviewer hatte die RICHTUNG richtig, die
Dominanz-Schwelle ist noch nicht erreicht.

**Folge (rein regelbasiert, kein neuer Task)**: Diese Messung wird
Pflicht-Diagnostik je Champion (Promotions-Checkliste 5c, ~10 min).
Ueberschreitet die Gesamt-Kennzahl 3, oeffnet sich die sigma-Familie
per Regel wieder -- ohne Ermessensentscheid. Zweitens ist damit
dokumentiert, dass die H0-Befunde der Wurzel-Regler-Familie
(m-Formel, c_scale) in einem ANDEREN Balance-Regime gemessen wurden als
dem heutigen; sie sind nicht falsch, aber ihre Uebertragbarkeit hat ein
Ablaufdatum.

---
### NACHTRAG 2026-08-09: behauptete "zweite Abschneide-Stufe" -- ZURUECKGEZOGEN

**Erst behauptet, dann auf Nutzer-Einwand im Code geprueft und widerlegt.
Die Task-E-Zahl 1,21% steht OHNE Einschraenkung.**

Der Verdacht lautete: `POLICY_MASS_CUTOFF = 0.95` (`net_mcts.rs:54`)
beschneide in `build_untried_actions` die Kandidatenmenge auf 95%
kumulierte Prior-Masse, BEVOR Gumbel-Top-m zieht -- dann waere meine
Messung ueber die volle legale Aktionsmenge zu grosszuegig gewesen. Der
Nutzer hielt dagegen ("eigentlich sollte es keinen beschnitt mehr
geben"). Nachpruefung im Aufrufpfad, nicht nur an der Konstante:

1. **`net_mcts.rs:1651`: `let skip_cutoff = parent.is_none() || USE_GUMBEL_SEARCH;`**
   -- der Cutoff wird also nicht bloss an der Wurzel ausgesetzt, sondern
   bei aktiver Gumbel-Suche an JEDEM Knoten. `USE_GUMBEL_SEARCH` ist
   `true` (Engine-Konfig). `build_untried_actions` kehrt in Zeile 1268
   vor der Truncation zurueck.
2. **Der Progressive-Widening-Cap (`MAX_ACTIONS + WIDEN_FACTOR·√N`)
   liegt im TOTEN Zweig**: `build_net_tree` springt in Zeile 3387 bei
   `USE_GUMBEL_SEARCH` per `return build_gumbel_tree(...)` heraus; der
   Widening-Code steht erst in Zeile 3447, also dahinter und
   unerreichbar. (In `crate::mcts` sind die beiden Konstanten weiter
   live -- das ist die HEURISTIK-Suche, unser Arena-Gegner, nicht der
   Netzpfad.)

**Der `#68`-Merkposten hatte also sachlich recht** ("ENTFERNT statt
getunt"): die Konstanten existieren noch, sind im Netzpfad aber inert --
dasselbe Muster wie `MOSAIC_VALUE_CAL_A/B`. Meine gegenteilige
Behauptung beruhte auf zwei Fundstellen (Konstante + `if cum >= ...`)
ohne Pruefung, ob der Zweig ueberhaupt erreicht wird.

**Lehre, die den Aufwand wert war**: Regler-Existenz ist nicht
Regler-Wirksamkeit. Bei einer Konstante immer den AUFRUFPFAD pruefen
(wer setzt das Flag, welcher Zweig kehrt vorher zurueck), nicht nur
`grep` auf den Namen. Dieselbe Klasse Fehler wie die Wheel-Blockade von
heute morgen -- dort war der Regler im Quelltext, aber nicht im
installierten Modul.

## Telemetrie-Antwort (externe Frage)

- **Varianz der Q-Skalierung: JA**, `tools/gumbel_scale_calibration.py`
  (Task #18), Zahlen oben; Aera-Nachmessung = Task G.
- **Ueberlebensrate von Zuegen im Sequential Halving: NEIN.**
  Protokolliert sind `root_child_q`, `root_num_actions`,
  `root_num_actions_considered` (daraus die 32%-Abdeckung oben) und
  `max_depth` (pro Kind und an der Wurzel, `ai_debug_net_json`), aber
  NICHT, welcher Kandidat welche Halbierungsphase ueberlebt. Bewusst
  nicht nachgeruestet: die Ueberlebensrate beschreibt, was die Suche
  INNERHALB einer gegebenen Menge getan hat; entscheidungsrelevant ist
  zuerst, ob die MENGE stimmt (Task E). Wird Task F eingetaktet, ist
  die Phasen-Telemetrie eine sinnvolle Beigabe zur Interpretation.
