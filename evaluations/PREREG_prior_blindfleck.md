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

Metriken (alle deskriptiv ausser der Entscheidungsmetrik):
- **Entscheidungsmetrik: `miss_rate_top16`** = Anteil der Zustaende,
  in denen der Orakel-Top-1 NICHT in den Prior-Top-16 liegt.
- Zusatz deskriptiv: dieselbe Rate fuer Top-8/Top-32/Top-64;
  Rangverteilung des Orakel-Top-1 im Prior; Aufschluesselung nach
  Runde und nach Anzahl legaler Aktionen (der 10%-Abdeckungs-Fall ist
  vermutlich der interessante).
- Kein Noise-Kanal, weil rein deterministisch (kein Gumbel-Noise, kein
  Seed) -- die Rate ist eine Eigenschaft von Netz+Orakel-Set.

**Entscheidungsregeln (vorab):**
1. `miss_rate_top16 < 5%` **und** Top-32 bringt keine relevante
   Verbesserung ⇒ Punkt GESCHLOSSEN, **kein Arena-Budget**. Externe
   Kritik dokumentiert als "gemessen, Effektgroesse zu klein".
2. `miss_rate_top16 >= 5%` ⇒ Task F wird eingetaktet, mit der
   gemessenen Rate als Erwartungsgroesse.
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
