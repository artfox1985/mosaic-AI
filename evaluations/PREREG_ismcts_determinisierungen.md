# Vorregistrierung: Mehrfach-Determinisierung (ISMCTS-k, Task #65-Reaktivierung)

**Angelegt 2026-08-08, VOR Knopf und Messung.** Nutzer-Go am selben Tag,
Einplanung NACH v21-Training + Gating + Auswertungs-Paket.

## Ausgangslage (Code verifiziert 2026-08-08)

Die Suche zieht heute EINE Stichwelt pro Zug (`NUM_DETERMINIZATIONS = 1`,
net_mcts.rs:704) -- klassisches PIMC mit der bekannten
Strategy-Fusion-Pathologie: die Suche optimiert gegen genau diese eine
moegliche Welt. Die Mehrfach-Variante ist **vollstaendig implementiert**
(Task #65: `build_determinized_forest` + `average_completed_q_policy`,
Standard-ISMCTS-Aggregation) und bei k=1 byte-identisch zum
Bestandspfad; sie ist nur nicht laufzeit-schaltbar.

**Wichtig (rechen-neutral)**: das Sims-Budget wird ueber die Welten
GESPLITTET (`split_sims_across_worlds`, Rest an Welt 1) -- k=4 bei
400 Sims sind 4 Baeume a 100 Sims, nicht 4x Rechenzeit. Der Test ist
damit ein reiner Tausch: Stichprobenvielfalt gegen Tiefe pro Welt.

**Zu erwartender Nebeneffekt (Confound, vorab benannt)**: die
Gumbel-Wurzelbreite haengt am Budget (`m = clamp(round(Sims/16), 4, 16)`)
und wird PRO WELT berechnet -- k=2 -> 200 Sims/Welt -> m=12, k=4 ->
100 Sims/Welt -> m=6. Ein etwaiger Verlust bei k=4 ist daher nicht
zwingend der Determinisierung zuzuschreiben, sondern moeglicherweise der
schmaleren Wurzel (Messung 2 fand die m-Formel allerdings staerke-neutral
bei 150 Sims/m=9 -- H0, p=0,54). Deshalb wird k=2 mitgemessen.

## Knopf

`MOSAIC_NUM_DETERMINIZATIONS` (Default 1 = byte-identisch, OnceLock/
read_f64_env-Muster wie MOSAIC_FLOOR_SHAPING_W). Wirkt an allen drei
Sucheinstiegen ueber die bestehende `NUM_DETERMINIZATIONS`-Semantik;
Paritaets-Hash vor Einsatz.

## Design

Instrument = `tools/paired_arena_env_ab.py` (Amendment-Muster: der Knopf
ist prozessweit, daher Netz-vs-Heuristik -- die Heuristik liest ihn
nicht). DREI Arme a 400 Spiele, identische Seeds, Basis-Seed 20260820:
k=1 (Kontrolle), k=2, k=4.

**AENDERUNG vor dem Lauf (Nutzer-Hinweis 2026-08-08): gemessen wird bei
600 Netz-Sims, nicht 400** -- "wir gehen bei den sockel spielen eh mit
600 sims ins rennen". Das entschaerft den oben benannten Confound
weitgehend, weil die Wurzelbreite pro Welt vom gesplitteten Budget
abhaengt (verifiziert: `split_sims_across_worlds` -> `build_net_tree` ->
`gumbel_top_m_for_budget(sims)`):

| Budget | k=1 | k=2 | k=4 |
|---|---|---|---|
| 400 Sims | 400/Welt, m=16 | 200/Welt, **m=13** | 100/Welt, **m=6** |
| 600 Sims | 600/Welt, m=16 | 300/Welt, **m=16** | 150/Welt, **m=9** |

Bei 600 Sims ist k=2 damit ein Effekt OHNE Breiten-Aenderung (m bleibt
16, weil 300/16 ueber dem Deckel liegt) -- der reine
Determinisierungs-Effekt. Und k=4 landet auf m=9, also exakt der
Konfiguration, die Messung 2 als staerke-neutral gegen m=16 gemessen hat
(H0, p=0,54). Der Confound ist damit fuer k=2 strukturell ausgeschlossen
und fuer k=4 empirisch gedeckt. Zusaetzlicher Vorteil: 600 Sims sind das
Regime, in dem die Sockel-Self-Plays tatsaechlich laufen -- ein positives
Ergebnis waere direkt auf die Korpus-Erzeugung uebertragbar.
Kosten: ~1,5x Wandzeit pro Arm (~30 min statt ~21 min), ~90 min gesamt.

## Entscheidungsregeln

1. **Default-Wechsel** (k>1 wird Standard) nur bei signifikantem
   Siegquoten-Vorteil (McNemar p<0,05) UND Frisch-Seed-Replikation --
   es ist eine Aenderung am Such-Default, dafuer gilt der volle Beleg
   (Statistik-Regel 3), nicht die gelockerte "schadet-nicht"-Logik.
2. H0 -> die Einzel-Determinisierung gilt als AUSREICHEND belegt, der
   Punkt (und damit die Imperfect-Information-Frage auf Suchebene) ist
   geschlossen; die ISMCTS-Maschinerie bleibt als inerter Pfad.
3. Deskriptiv: Scores/Floors auf Block-Ebene; zusaetzlich die
   Zeit/Spiel je Arm (Beleg der Rechen-Neutralitaet).
4. **Nicht Teil dieses Tests**: die Frage, ob k>1 die
   POLICY-ZIEL-Qualitaet im Self-Play verbessert (die Wurzelpolitik
   waere dann ein Welten-Mittel). Das waere ein eigener Korpus-Arm mit
   eigenem Prereg -- erst sinnvoll, wenn die Spielstaerke-Frage
   positiv beantwortet ist.

---
**STATUS (Stand 2026-08-08): OFFEN** -- der Knopf
(`MOSAIC_NUM_DETERMINIZATIONS`) ist vorbereitet, die Messung selbst
steht laut STATUS.md ausdruecklich in der "NACH-v21-QUEUE" (Nutzer-Go
2026-08-08) und ist noch nicht gelaufen. Die einzige verwandte Messung
in archive/history.md ("Task #65", 2026-07-22) ist eine AELTERE, ANDERE
Messung aus dem Vor-WDL-/Vor-Gumbel-Regime, die damals verworfen wurde
-- keine Antwort auf die hier reaktivierte 600-Sims-Messung. Belegstelle:
evaluations/STATUS.md, Abschnitt "NACH-v21-QUEUE (Nutzer-Go 2026-08-08)",
Punkt 2 ("ISMCTS-k"); kein Ergebnis in archive/history.md.

---
## ERGEBNIS (2026-08-09): H0 nach Regel 2 -- k=1 BLEIBT, Punkt GESCHLOSSEN

`tools/paired_arena_env_ab.py`, `MOSAIC_NUM_DETERMINIZATIONS` 1/2/4,
Champion@**600** Sims vs Heuristik@150dyn, 3x400 Partien, identische
Basis-Seeds (20260820). Belegstelle
`evaluations/paired_arena_env_ismcts_k.json`.

| Arm | Netz-Siege | Quote | vs k=1 | McNemar | Block-Ebene |
|---|---|---|---|---|---|
| **k=1 (Kontrolle)** | **304/400** | **76,0%** | — | — | — |
| k=2 | 309/400 | 77,25% | +1,25pp | p=0,7228 | t=-0,41 (5:8 Bloecke) |
| k=4 | 280/400 | 70,0% | **-6,00pp** | p=0,0465 | t=+1,63 (11:4 Bloecke) |

**Entscheid: Regel 2 greift -- kein Arm zeigt einen Vorteil, k=1 bleibt
Standard.** Die Einzel-Determinisierung gilt damit als ausreichend
belegt; die Imperfect-Information-Frage auf SUCHEBENE ist geschlossen,
die ISMCTS-Maschinerie bleibt als inerter Pfad erhalten. Regel 1
(Default-Wechsel) kam nie in Reichweite: sie haette einen signifikanten
VORTEIL plus Frisch-Seed-Replikation verlangt.

**Zur k=4-Zahl, sauber eingeordnet -- sie ist NICHT signifikant**,
obwohl der rohe McNemar mit p=0,0465 knapp darunter liegt:
1. **Block-Ebene** (Pflichtregel, weil Paar-SEs massiv unterschaetzen):
   mittlere Block-Differenz +1,50 Siege je 25 Partien fuer k=1, Block-SE
   0,92, **t=+1,63** ⇒ p~0,12. Der Befund haelt der konservativen
   Rechnung nicht stand.
2. **Mehrfachtestung**: zwei Vergleiche gegen dieselbe Kontrolle. Die
   Bonferroni-Schwelle liegt bei 0,05/2 = 0,025, p=0,0465 liegt
   darueber. (Diese Korrektur war im Prereg nicht vorgesehen -- ein
   Mangel des Designs, der hier festgehalten wird; bei einem
   Mehr-Arm-Test gegen eine gemeinsame Kontrolle gehoert sie vorab
   festgelegt.)
Korrekte Formulierung also: **k=4 zeigt keinen Vorteil und tendiert zum
Schaden (-6pp, 11 von 16 Bloecken), ist aber kein Schadensnachweis.**
Fuer den Entscheid ist das gleichgueltig -- Regel 2 haengt am fehlenden
Vorteil, nicht am Schaden.

**Mechanistische Lesart** (deskriptiv): bei festen 600 Sims teilt k=4 das
Budget auf 4 Welten a 150 Sims. Die Wurzelbreite ist dabei laut
Prereg-Tabelle nicht der Treiber (k=4 landet auf m=9, und m=9 vs m=16
war bei 150 Sims neutral gemessen) -- es bleibt die Budget-Zersplitterung
je Welt. k=2 haelt m=16 und kostet nichts, bringt aber auch nichts:
zwei Welten mitteln die verdeckte Information offenbar nicht besser als
eine, jedenfalls nicht messbar bei n=400.

**Zweite Widerlegung derselben Idee**: die Alt-Messung (`#65`,
2026-07-22) verwarf Mehrfach-Determinisierung im Vor-WDL-/Vor-Gumbel-
Regime. Die Reaktivierung war regelkonform (neues Regime, 600 Sims,
Confound entschaerft) und kommt zum selben Ergebnis. Wiedereroeffnung
daher nur mit einem NEUEN Mechanismus, nicht mit einer weiteren
k-Stufe -- und Regel 4 (Policy-Ziel-Qualitaet im Self-Play) entfaellt
per Prereg, weil sie eine positiv beantwortete Staerke-Frage
voraussetzte.

---
## WIEDEREROEFFNUNG 2026-08-09 (Nutzer-Einwand) -- NEUE Frage, nicht dieselbe Messung

Nutzer: *"bin ich noch nicht überzeugt. 'Zwei Welten mitteln die
verdeckte Information nicht besser als eine' hört sich für mich eher nach
einem design fehler an. mehr info sollte eigentlich immer besser sein."*

**Der Einwand trifft, und der Code belegt ihn.** Unsere Implementierung
ist **nicht** ISMCTS, sondern PIMC mit Wurzel-Mittelung:
`build_determinized_forest` (`net_mcts.rs:751`) baut *n unabhaengige*
Suchbaeume (`Vec<Vec<Node>>`), zusammengefuehrt wird erst an der Wurzel
(`aggregate_root_child_stats:794`, `average_completed_q_policy:822`).
Echtes ISMCTS haelt EINEN Baum, dessen Knoten Informationsmengen sind;
jede Simulation zieht eine frische Determinisierung und alle
Simulationen sammeln Statistik in DENSELBEN Knoten -- die Vielfalt kommt
ohne Teilung der Statistik.

Folge: das H0-Ergebnis oben vermischt zwei Aenderungen. k=2 halbiert die
Sims je Welt UND liefert den Vielfalts-Gewinn nur an der Wurzel; die
Tiefenstruktur profitiert nicht. Gemessen wurde also "gleiches Budget,
anders aufgeteilt", nicht "mehr Information". **Das H0-Verdikt bleibt
gueltig fuer die rechen-neutrale Frage** (und damit fuer die
Praxis-Entscheidung k=1) -- aber es beantwortet die Frage des Nutzers
nicht.

Regelkonformitaet: der Prereg erlaubt Wiedereroeffnung "nur mit einem
NEUEN Mechanismus, nicht mit einer weiteren k-Stufe". Ein gemeinsamer
Informationsmengen-Baum IST ein neuer Mechanismus. Die Wiedereroeffnung
biegt die Regel also nicht.

### Trenn-Messung (kein Code noetig): gleiche TIEFE, eine Welt vs zwei

`split_sims_across_worlds` teilt das UEBERGEBENE Budget. Mit
`--net-sims 1200` bei k=2 bekommt jede Welt 600 Sims -- **gleiche Tiefe
wie die Kontrolle k=1@600, gleiche Wurzelbreite m=16 in beiden**
(`gumbel_top_m_for_budget(600)`=16). Einziger Unterschied: eine Welt
gegen zwei gemittelte. Ausdruecklich NICHT rechen-neutral (2x Kosten) --
das ist der Zweck.

Umsetzung: zwei Laeufe von `tools/paired_arena_env_ab.py` mit
IDENTISCHEM Basis-Seed 20260828 (die Spiel-Seeds sind je Spielindex
deterministisch abgeleitet, die Laeufe sind damit gepaart), je 400
Partien: (A) k=1, `--net-sims 600`; (B) k=2, `--net-sims 1200`.
Auswertung per exaktem McNemar auf den diskordanten Paaren ueber den
Spielindex, PLUS Block-Ebene (Pflichtregel).

**Entscheidungsregeln (vorab):**
1. **k=2@600/Welt schlaegt k=1@600 signifikant** (McNemar p<0,05 UND
   Block-SE-t>2) ⇒ die Vielfalt traegt, und die rechen-neutrale
   Niederlage lag an der Tiefen-Teilung. Dann ist der gemeinsame
   Informationsmengen-Baum GERECHTFERTIGT (er liefert Vielfalt ohne
   Teilung) und bekommt eine eigene Vorregistrierung mit
   Aufwandsschaetzung. **Dieser Arm selbst wird NICHT Preset** -- er
   kostet 2x Rechenzeit, das ist im Self-Play nicht bezahlbar.
2. **H0** ⇒ die Vielfalts-Hypothese selbst ist schwach, unabhaengig von
   der Implementierung. Dann ist der Punkt endgueltig zu, und ein
   Umbau auf gemeinsamen Baum waere nicht durch Messung gedeckt.
3. **k=2@600/Welt ist schlechter** ⇒ ebenfalls zu; die Mittelung
   schadet dann sogar bei gleicher Tiefe (moegliche Lesart:
   Strategy-Fusion-Mittelung verwaessert eine in der gezogenen Welt
   korrekte Linie).
4. Deskriptiv: Zeit je Partie beider Arme (Beleg, dass B wirklich ~2x
   kostet und die Tiefe nicht heimlich anders liegt).

### Kopplung an den GPU-Inferenz-Batcher (2026-08-09)

Die Trenn-Messung hat einen zweiten Adressaten. Waeren die k Welten
VERSCHRAENKT statt sequenziell gesucht (`build_determinized_forest` tut
heute letzteres), lieferten sie ~11·k gleichzeitig offene
Blattauswertungen statt ~11 -- genau den Batch, an dessen Erreichbarkeit
`PREREG_gpu_inferenz_batcher.md` haengt. Und existierte der Batcher,
kostete k>1 kaum Wandzeit, weil die k Welten in EINEM Batch liefen; das
Sim-Budget muesste dann nicht mehr geteilt werden -- also genau das
Regime, das diese Trenn-Messung vorwegnimmt.

Faellt sie positiv aus, ist das zugleich das Staerke-Motiv fuer den
Batcher (bisher hat er nur ein Durchsatz-Motiv). Faellt sie H0 aus,
bleibt der Batcher eine reine Durchsatzfrage und die
Verschraenkung nur ein Mittel zum Batch-Fuellen, kein Staerke-Hebel.

### ERGEBNIS der Trenn-Messung (2026-08-09): Regel 3 -- Vielfalt hilft AUCH bei gleicher Tiefe nicht

Zwei gepaarte Laeufe, identischer Basis-Seed 20260828, je 400 Partien,
Champion vs Heuristik@150dyn. Belegstellen
`evaluations/paired_arena_env_ismcts_tiefe_k1.json` /
`..._tiefe_k2.json`.

| Arm | Budget | Netz-Siege | Quote |
|---|---|---|---|
| **A: k=1** | 600 Sims, 1 Welt | **327/400** | **81,75%** |
| B: k=2 | 1200 Sims = 600 **je Welt** | 308/400 | 77,00% |

**Differenz -4,75pp gegen k=2**, und zwar bei DOPPELTEM Rechenaufwand.
Gepaart: diskordant 46 (nur B) / 65 (nur A), exakter McNemar
**p=0,0871**. Block-Ebene: **10 von 16 Bloecken** fuer k=1, mittlere
Block-Differenz -1,19 Siege je 25 Partien, Block-SE 0,55, **t=-2,16**
(p~0,047).

**Bemerkenswert: hier ist die BLOCK-Ebene signifikanter als der gepaarte
McNemar** -- umgekehrt zur ueblichen Richtung. Grund: McNemar zaehlt nur
diskordante Paare, der Block-Test nutzt die HOEHE der Differenzen. Bei
einem konsistent gerichteten, pro Paar aber moderaten Effekt ist der
Block-Test staerker. Es wird ausdruecklich NICHT der guenstigere der
beiden Tests herausgegriffen: die faire Zusammenfassung ist "Richtung
klar negativ, ein Test knapp signifikant, einer nicht".

**Entscheid**: Regel 1 (Vorteil) ist definitiv verfehlt -- sie haette
p<0,05 UND Block-t>+2 in die ANDERE Richtung verlangt. Es greift Regel 3
(bzw. mindestens Regel 2): **der Punkt ist zu.** Die
Vielfalts-Hypothese traegt in diesem Spiel nicht, und zwar unabhaengig
von der Budget-Teilung -- genau der Confound, den der Nutzer-Einwand
zurecht benannt hatte, ist hier ENTFERNT, und das Ergebnis bleibt
negativ. Ein Umbau auf einen gemeinsamen Informationsmengen-Baum ist
damit NICHT durch Messung gedeckt.

**Was das ueber den Mechanismus sagt -- als Lesart, nicht als Nachweis**:
zwei unabhaengige 600-Sim-Suchen zu mitteln muesste die Varianz SENKEN.
Dass es die Staerke drueckt, deutet darauf, dass die Mittelung der
completed-Q-Politiken eine in der gezogenen Welt scharfe Praeferenz
verwischt (Strategy-Fusion-Mittelung), statt Fehlurteile auszubuegeln.
Passend dazu die strukturelle Beobachtung: die verdeckte Information
(Beutel/Turm/Stapel) steckt in der Netz-Eingabe nur als AGGREGIERTE
Zaehler, nicht als geordnete Liste -- deshalb war auch der
Seed-Rauschboden der Forward-Pass-Groessen strukturell exakt Null. Wo
das Netz die Reihenfolge nicht sieht, fuegt eine zweite Ziehung
derselben Zaehler kaum Signal hinzu, aber Mittelungs-Unschaerfe schon.

**Seed-Skala als Nebenbefund (wichtig fuer alle kuenftigen Vergleiche)**:
dieselbe Konfiguration k=1@600 ergab 304/400 (76,0%) mit Seed 20260820
und 327/400 (81,75%) mit Seed 20260828 -- **5,75pp allein durch den
Seed** bei n=400. Groesser als die meisten Effekte, die wir diskutieren.
Ungepaarte Vergleiche zwischen Laeufen sind damit wertlos; A und B lagen
deshalb auf demselben Basis-Seed.
