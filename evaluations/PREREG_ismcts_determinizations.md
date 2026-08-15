<!-- STATUS: ENTSCHIEDEN | Frage: Verbessert Mehrfach-Determinisierung (k=1/2/4) die Spielstaerke gegen die PIMC-Strategy-Fusion? | Beleg: **GESCHLOSSEN 2026-08-10 unter ZWEI Anordnungen**: Sims-Split (Budget fix) 76,0/77,3/70,0%; gleiche Tiefe je Welt (Budget waechst mit k) 81,75/77,0/73,0% -- k=4 faellt in beiden ab, im zweiten Fall mit VIERFACHEM Budget und in beiden Pflichtinstrumenten signifikant (Block-t -3,73, McNemar p=0,00262, Bonferroni inklusive). Nicht ein Tiefenverlust, sondern: das Mitteln ueber gezogene Welten schadet aktiv. `evaluations/paired_arena_env_ismcts_k.json`, `..._tiefe_k{1,2,4}.json` -->

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
`PREREG_gpu_inference_batcher.md` haengt. Und existierte der Batcher,
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
`evaluations/paired_arena_env_ismcts_depth_k1.json` /
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

---
## ZWEITE WIEDEREROEFFNUNG 2026-08-09: k=2 ist keine faire Vertretung der Hypothese

Nutzer: *"k=2 ist für mich keine valide überprüfung. zwei welten sind
kein mittelwert bei unserem seed rauschen."* -- **trifft zu, und mein
"endgueltig geschlossen" war voreilig.**

Rechnung dazu: eine Mittelung ueber k Welten senkt die
Determinisierungs-Varianz auf 1/k. k=2 entfernt also die Haelfte, k=4
drei Viertel. Gleichzeitig loest unser Instrument nur grob auf: aus der
Trenn-Messung ergibt sich eine Block-SE von 0,55 Siegen je 25 Partien,
also **~2,2pp Standardfehler auf der Quote** und damit eine
Nachweisgrenze von etwa 4,4pp bei 2 SE. Ein Mechanismus, der die halbe
Determinisierungs-Varianz wegnimmt, muss diese Schwelle nicht
ueberschreiten -- die Messung war also nicht falsch, aber sie hat die
Hypothese in ihrer schwaechsten Form getestet.

### Letzte Eskalation: k=4 bei VOLLER Tiefe je Welt

`split_sims_across_worlds(2400, 4)` = [600,600,600,600] ⇒ jede Welt hat
600 Sims und m=16, exakt wie die Kontrolle. Vierfache Rechenzeit, das
ist der Preis fuer die dreiviertel Varianzreduktion.

- Arm A (bereits gemessen, wird wiederverwendet): k=1, 600 Sims,
  Basis-Seed 20260828 ⇒ **327/400**.
- Arm C (neu): k=4, `--net-sims 2400`, IDENTISCHER Basis-Seed 20260828,
  400 Partien. Auswertung gepaart ueber den Spielindex + Block-Ebene.

**Entscheidungsregeln (vorab, VOR dem Lauf):**
1. **Arm C schlaegt Arm A** (gepaarter McNemar p<0,05 UND Block-t < -2)
   ⇒ die Mittelung traegt, sobald sie ueberhaupt eine Mittelung ist.
   Dann ist der gemeinsame Informationsmengen-Baum gerechtfertigt (er
   liefert das zu ~1x Kosten) und bekommt eine eigene Vorregistrierung.
2. **H0 oder schlechter** ⇒ der Punkt ist **endgueltig** zu, und diesmal
   traegt das Wort: bei drei Vierteln entfernter Varianz und voller
   Tiefe je Welt gibt es kein k mehr, das wir bezahlen koennten und das
   mehr Mittelung liefert. k=8 waere 8x Kosten und koennte selbst bei
   Erfolg nie Preset werden.
3. **Arm C wird in KEINEM Fall Preset** (4x Rechenzeit ist im Self-Play
   nicht bezahlbar). Die Messung ist rein diagnostisch: sie entscheidet
   nur, ob der Umbau auf einen gemeinsamen Baum durch Messung gedeckt
   ist.
4. Deskriptiv: Blockzeiten als Beleg, dass Arm C wirklich ~4x kostet und
   die Tiefe nicht heimlich anders liegt.

**Das vorige H0 bleibt gueltig fuer seine Frage** (k=2, gleiche Tiefe:
-4,75pp) und ebenso das rechen-neutrale H0 (k=1 bleibt Default). Neu ist
nur, dass die Hypothese in ihrer STARKEN Form noch offen war.

---
## FESTGELEGTER NACHFOLGER, falls k=4 nicht wirkt (Nutzer 2026-08-09)

Nutzer: *"und wenn k=4 nicht wirkt, müssen wir uns was anderes überlegen
wie wir die welten simulieren. k=1 find ich einfach nicht sauber und geht
am ziel vorbei."* Das deckt sich mit der stehenden Nutzer-Regel
"Korrektheit vor gemessenem Nutzen" -- ein H0 macht k=1 nicht sauber,
es macht nur k>1 zu keinem Hebel.

Die Code-Sichtung zeigt: es gibt **drei** Unsicherheits-Mechanismen, und
der k-Regler betrifft den unwichtigsten.

| Mechanismus | Stand | Bewertung |
|---|---|---|
| `DETERMINIZE_ROOT_HIDDEN_INFO=true` -- EINE Stichwelt je Zugsuche fuer Kuppelstapel + verdeckte Bonuschips, danach laeuft die ganze Suche darauf | an | der klassische Determinisierungsfehler; hier setzt k>1 an |
| `SHUFFLE_STACK_PEEK_IN_SEARCH=false` -- Neumischung bei jedem simulierten Peek | aus, **gemessen schaedlich** | mehr Suchvarianz als Bias-Korrektur; "ueberall neu ziehen" ist nachweislich nicht die Antwort |
| **`ROUND_TRANSITION_SAMPLING=false`** -- die Fabrik-Neubefuellung am Rundenuebergang | **aus, toter Code** | die eigentliche Luecke, s.u. |

**Der Nachfolger ist damit bestimmt: Chance-Node-Sampling am
Rundenuebergang im SUCHPFAD.** Begruendung:

1. Die Fabrik-Neubefuellung entscheidet, was BEIDE Spieler die ganze
   naechste Runde draften koennen -- laut Code-Kommentar ist sie
   "nirgends als echter Zufallsknoten repraesentiert". Das ist ein
   groesseres Loch als die Stichwelt fuer Stapel und Chips.
2. **Die Maschinerie existiert vollstaendig**:
   `round_transition::sample_round_transition_value` mit
   `N_SAMPLES_SEARCH=8` und eigenem `TIME_BUDGET`, angebunden in
   `net_mcts.rs:1732`. Es ist ein Schalter, kein Neubau.
3. Die Abschaltbegruendung im Code ("erst nach einer Val-R²-Verbesserung
   im Trainingsziel-Pfad aktivieren") **vermischt zwei Fragen**:
   Sampling im SUCHPFAD (Blattbewertung am Uebergang) ist unabhaengig von
   Sampling im TRAININGSZIEL. Die Suchseite wartet damit seit Wochen auf
   eine Verbesserung an anderer Stelle und ist nie eigenstaendig
   getestet worden.
4. Es ist die richtige Lehre aus dem `SHUFFLE_STACK_PEEK`-Befund: nicht
   ueberall neu ziehen, sondern **genau am echten Zufallsknoten**.

**Vor dem Arena-Arm zuerst die Kosten messen** (eigene Vorregistrierung,
noch nicht angelegt): welcher Anteil der Blaetter sind
Rundenuebergangs-Blaetter, und was kostet 8-faches Sampling dort? Nur
Uebergangs-Blaetter sind betroffen, nicht alle -- der Aufschlag koennte
klein sein. Ein Arm, dessen Kosten unbekannt sind, ist nicht
rechen-neutral vergleichbar.

Reihenfolge: k=4-Ergebnis abwarten (laeuft), dann diese Kostenmessung,
dann der Arena-Arm. Bei einem k=4-SIEG gilt weiter Regel 1 oben (dann
zuerst der gemeinsame Informationsmengen-Baum).

### WORUEBER k eigentlich mittelt (Nutzer-Frage 2026-08-09, im Code geklaert)

`determinize_hidden_information` (`net_mcts.rs:614`) mischt **genau zwei**
Dinge: `dome_tile_pool` (Kuppelstapel) und die noch UNAUFGEDECKTEN
Bonuschip-Werte (Fabrik-Chips mit `!bonus_chip_revealed` +
`bonus_chip_pool`). Aufgedeckte Chips bleiben unangetastet -- oeffentliches
Wissen. **Der Beutel ist NICHT dabei.**

Damit ist das H0 erklaerbar, und zwar nicht als Aussage ueber Mittelung,
sondern ueber den Gegenstand:
- **Kuppelstapel: bewiesen irrelevant** fuer die Bewertung -- der
  Value-Kopf sieht `pending_stack_draw` architektonisch nie
  (Bindungs-Check, dokumentiert am
  `DETERMINIZE_ROOT_HIDDEN_INFO`-Kommentar).
- **Unaufgedeckte Chips**: als Merkmal existiert nur
  `bonus_chip_revealed`; ein unaufgedeckter Chip erreicht die Bewertung
  erst, wenn innerhalb der Suche eine Aufdeckung passiert -- ein
  schmaler Kanal entlang weniger Linien.

**k mittelt also ueber verdeckte Information, die die Bewertung
strukturell fast nicht erreicht.** Es war kaum etwas zu mitteln da. Das
ist die vollstaendige Erklaerung fuer alle drei k-Messungen (rechen-neutral,
gleiche Tiefe k=2, gleiche Tiefe k=4) -- und zugleich die Bestaetigung,
dass die Unsauberkeit woanders sitzt: beim Beutel, also am
Rundenuebergang.

### KORREKTUR am Nachfolger (Nutzer-Frage "ist das das rtv?" -- ja)

Es ist **dieselbe Maschinerie**: `sample_round_transition_value` wird
aus `self_play.rs:2121/2131` mit `N_SAMPLES_TRAIN=24` fuer die LABELS
gerufen (Phase 1) und aus `net_mcts.rs:1734` mit `N_SAMPLES_SEARCH=8`
fuer die SUCHE (Phase 2, "noch nicht aktiviert").

**Das senkt den Vorwissens-Wert des Vorschlags erheblich.** Phase 1 ist
gemessen und verworfen: rtv trug keine messbare Spielstaerke bei, kostete
~81% der Self-Play-Zeit, und die Labels korrelierten mit dem Ausgang nur
0,215 gegen 0,445 beim Bootstrap (`v13_nortv` wurde deshalb Champion).
Das ist eine Aussage ueber die QUALITAET DES SCHAETZERS, nicht nur ueber
Label-Oekonomie -- und derselbe Schaetzer soll in Phase 2 die
Blattbewertung tragen.

Was sachlich anders bleibt: als Label konkurrierte rtv gegen den besser
korrelierten Bootstrap und verlor. In der Suche gibt es am
Uebergangsblatt KEINEN konkurrierenden Schaetzer -- dort steht heute ein
einzelner deterministischer Wert, und 8 Stichproben senken dessen
Varianz. Aber ein praeziser schwacher Schaetzer bleibt schwach.

**Geaenderte Reihenfolge -- Offline-Verzerrungsmessung VOR jedem
Arena-Arm** (Minuten, kein Arena-Budget):

Auf einer Menge von Vor-Uebergangs-Zustaenden beides berechnen und
vergleichen: (a) den heutigen einzelnen deterministischen Blattwert,
(b) das 8-Stichproben-Mittel aus `sample_round_transition_value`.

- **Systematische Abweichung** (Median-Differenz deutlich ueber dem
  Seed-Rauschboden derselben Groesse) ⇒ echte Verzerrung, der Arena-Arm
  ist gerechtfertigt.
- **Uebereinstimmung** ⇒ das Netz mittelt bereits selbst ueber
  Neubefuellungen (der Beutel steckt als aggregierter Zaehler in den
  Merkmalen), das Sampling korrigiert nichts, und der Punkt ist ohne
  Arena-Kosten zu. Dann waere die Unsauberkeit zwar formal vorhanden,
  aber ohne Wirkung auf die Bewertung -- dieselbe Lage wie beim
  Kuppelstapel.

Damit ist auch die alte Freigabebedingung im Code aufgeloest: sie
verlangte eine "Val-R²-Verbesserung im Trainingsziel-Pfad", also an einem
Mechanismus, der inzwischen ABGESCHALTET ist (`nortv` in jedem aktuellen
Training). Die Bedingung ist damit unerfuellbar geworden, ohne dass es
jemand bemerkt hat -- sie wird durch die Verzerrungsmessung ersetzt.

### VERZERRUNGSMESSUNG: nicht ausfuehrbar -- und der TD-Bootstrap erklaert warum sie sich eruebrigt

Nutzer-Hinweis, der die Sache entscheidet: *"eigentlich haben wir eine
stark zufällige komponente im rundenübergang -> die befüllung der
fabriken. die machen wir über die td-bootstrap labels."*

**Das ist das Argument, das gefehlt hat.** Der TD-Bootstrap nimmt am
Rundenuebergang den Netzwert des TATSAECHLICH eingetretenen
Nachfolgezustands als Label. Ueber viele Partien folgen auf dieselbe
Vor-Uebergangs-Situation verschiedene Befuellungen -- der gelernte Wert
konvergiert also gegen den ERWARTUNGSWERT ueber Befuellungen. Sampling in
der Suche wuerde zur Laufzeit nachrechnen, was das Netz aus dem Korpus
schon gelernt hat. Das erklaert zugleich das rtv-Verdikt: explizites
Chance-Node-Averaging als LABEL trug nichts bei, weil der Bootstrap die
Mittelung ohnehin leistet -- bei 81% der Self-Play-Kosten.

**Versuchte Messung, Ergebnis: nicht ausfuehrbar** (Belege aus dem Lauf):
- Die Nachfolgezustaende aus `autoplay_to_round5_and_resample_json` sind
  Runde-5-Zustaende. Dort liefert `net_search_state_json_trace`
  `root_value = None` und KEIN `value_debug` -- Runde 5 umgeht das Netz
  vollstaendig (exakter Alpha-Beta-Loeser).
- Der Vor-Uebergangs-Zustand (`r4_end_state`, Runde 4, Phase Tiling) hat
  ebenfalls kein `value_debug` -- die Tiling-Phase laeuft ueber den
  Tiling-Loeser.
- **Keine der beiden Seiten des Vergleichs existiert als Netzwert.** Ein
  Resample-Einstieg fuer die Uebergaenge R1->R2 / R2->R3 / R3->R4, wo
  beide Seiten netzbewertet waeren, ist nicht exponiert.

**Entscheid: der Punkt wird geschlossen, ohne die Bindung zu bauen.**
Begruendung, nicht Resignation: wir wuerden ein Instrument bauen, um
einen Hebel zu rechtfertigen, dessen Praemisse durch das TD-Argument
bereits erklaert ist -- und dessen Schaetzer in Phase 1 als schwach
gemessen wurde (Ausgangskorrelation 0,215 gegen 0,445). Eine Messung,
deren erwartete Antwort "das Netz mittelt bereits" lautet, ist die
Bindung nicht wert.

**Damit ist die Imperfect-Information-Frage auf Suchebene vollstaendig
abgehandelt**, und zwar mechanismusweise statt pauschal:
| Quelle verdeckter Information | Behandlung | Status |
|---|---|---|
| Kuppelstapel | Wurzel-Determinisierung | bewiesen irrelevant (Value-Kopf sieht `pending_stack_draw` nie) |
| unaufgedeckte Bonuschips | Wurzel-Determinisierung, k-Regler | schmaler Kanal; k=1/2/4 dreimal H0 |
| Peek/Reveal in-tree | `SHUFFLE_STACK_PEEK_IN_SEARCH` | aus, gemessen SCHAEDLICH |
| **Fabrik-Neubefuellung** | **TD-Bootstrap-Label** | **behandelt -- ueber den Korpus gemittelt, nicht zur Laufzeit** |

### NACHTRAG: der Zieh-Zug ist in 45% der Entscheidungen verfuegbar -- Verduennung erklaert das H0 NICHT

Nutzer-Argument: die Wurzel-Determinisierung des Kuppelstapels kann nur
dort wirken, wo Ziehen ein legaler Zug ist; unsere Messung mittelte aber
ueber ALLE Stellungen. Dazu zwei Praezisierungen.

**Erstens traegt der alte "Kuppelstapel irrelevant"-Befund hier nicht.**
Er stuetzte sich darauf, dass der Value-Kopf `pending_stack_draw`
architektonisch nie sieht -- das gilt fuer den ANSTEHENDEN Zug. Ist
gezogen, liegt die Fliese im beobachtbaren Zustand und wirkt nach unten
weiter. Vier Welten heissen also vier verschiedene gezogene Kuppeln, und
die restlichen Sims schauen tiefer in genau diese Unterschiede. Der alte
Befund war fuer die IN-TREE-Neumischung formuliert, nicht fuer die
Wurzel-Determinisierung.

**Zweitens ist die Verfuegbarkeit gemessen, nicht geschaetzt** (frozen_v2,
`valid_actions` enthaelt den Aktionstyp `dome_stack_peek`):

| Netz-Entscheidungen (Drafting) | mit Zieh-Zug |
|---|---|
| Runde 1: 302 | 134 = **44,4%** |
| Runde 2: 270 | 116 = **43,0%** |
| Runde 3: 256 | 113 = **44,1%** |
| Runde 4: 241 | 122 = **50,6%** |
| **R1-R4 gesamt: 1.069** | **485 = 45,4%** |
| Runde 5: 218 | **0** (dort entscheidet der exakte Loeser) |

Die Nutzer-Regel ("Runde 1-4") ist damit exakt bestaetigt.

**Folge fuer die Lesart des H0**: bei 45% Verfuegbarkeit ist der
Verduennungsfaktor ~2, nicht ~10. Unsere Aufloesung liegt bei ~4,4pp
(2 x Block-SE 2,2pp), ein echter Effekt auf den berechtigten Stellungen
muesste also ueber ~10pp liegen, um gesamt sichtbar zu werden. Der
Vorbehalt hat damit **Zaehne fuer kleine Effekte** -- ein wahrer Effekt von
5pp auf berechtigten Stellungen waere unsichtbar geblieben. Er rettet die
Hypothese aber nicht: beobachtet wurde ein NEGATIVER Punktschaetzer
(-4,75pp bei k=2, gleiche Tiefe), nicht ein zu kleiner positiver.

**Verfuegbares Instrument fuer eine schaerfere Messung** (nicht gebaut,
aber ohne Neubau moeglich): dasselbe Muster wie
`tools/plate_rank_invariance.py` -- auf FESTEN Zustaenden die tatsaechlich
gewaehlte Aktion unter k=1 gegen k=4 vergleichen und nach
Peek-Verfuegbarkeit bedingen. Das misst die Kipprate auf
Entscheidungsebene statt Partie-Ergebnisse und braucht keine Arena. Wer
das k-Thema noch einmal aufnimmt, sollte dort anfangen und nicht bei
einem weiteren Arena-Arm.

## ERGEBNIS k=4 (2026-08-10) -- Familie geschlossen

Rechnerisch gleiche Gesamtsims (k Welten x 600 Sims), Basis-Seed 20260828,
n=400, gepaart je Spielindex, Champion `v21_2d_brierbest` vs
Heuristik@150dyn:

| Arm | Quote | Block-Delta vs k=1 | Block-t | exakter McNemar |
|-----|-------|--------------------|---------|-----------------|
| k=1 @600 | **327/400 = 81,75%** | -- | -- | -- |
| k=2 @1200 | 308/400 = 77,00% | -4,75pp | -2,16 | p=0,0871 |
| k=4 @2400 | 292/400 = 73,00% | **-8,75pp** | **-3,73** | **p=0,00262** |

k=4 vs k=2: -4,00pp, t=-1,35, p=0,195 (Trend, nicht signifikant).

**Monoton fallend.** k=4 ist in BEIDEN Pflichtinstrumenten signifikant und
uebersteht die Bonferroni-Korrektur fuer 3 Familienvergleiche
(alpha' = 0,0167). Damit ist der Einwand des Nutzers gegen k=2 ("zwei
Welten sind kein Mittelwert bei unserem Seed-Rauschen") beantwortet, ohne
dass die Schliessung auf dem schwachen Arm ruht.

### KORREKTUR meiner Lesart (noch am 2026-08-10, beim Index-Nachziehen)

Ich hatte oben geschrieben, die Messung sei "rechenneutral" und der Verlust
ein **Tiefenverlust**, weil dasselbe Gesamtbudget auf mehrere Baeume
verteilt werde. **Das ist falsch.** Die Laeufe heissen
`paired_arena_env_ismcts_depth_k*` (bis zur Umbenennung 2026-08-13:
`..._ismcts_tiefe_k*`) -- "depth"/"tiefe" = GLEICHE TIEFE JE WELT: die
Arena-Koepfe sagen `@600` (k=1), `@1200` (k=2), `@2400` (k=4). Jede Welt
bekam 600 Sims, das GESAMTBUDGET wuchs mit k.

k=4 hatte also das **Vierfache an Rechenzeit** und verlor trotzdem
signifikant (-8,75pp, Block-t -3,73, McNemar p=0,00262). Das ist der
STAERKERE Befund: kein Tiefenverlust, sondern **das Mitteln ueber gezogene
Welten schadet aktiv**. Plausibler Mechanismus: die gemittelte
completed-Q-Politik (`average_completed_q_policy`) mischt Plaene, die je
Welt kohaerent sind, zu einem der in keiner Welt gut ist -- genau die
Strategy Fusion, gegen die k antreten sollte.

Damit stuetzen sich beide Versuchsanordnungen gegenseitig:

| Anordnung | k=1 | k=2 | k=4 |
|-----------|-----|-----|-----|
| Sims-Split (Gesamtbudget FIX, `..._ismcts_k.json`) | 304/400 = 76,0% | 309/400 = 77,3% | 280/400 = 70,0% |
| Gleiche Tiefe je Welt (Budget WAECHST, `..._tiefe_k*.json`) | 327/400 = 81,75% | 308/400 = 77,0% | 292/400 = 73,0% |

Unter beiden Anordnungen faellt k=4 ab -- einmal mit gleichem, einmal mit
vierfachem Budget. Die Familie ist damit nicht nur "nicht besser", sondern
in der oberen Dosis nachweislich schlechter.

### Konsequenz fuer den Nachfolger

Die Warnung an `PREREG_chance_nodes.md` bleibt bestehen, wird aber
praeziser: gefaehrlich ist nicht die Baum-Vervielfachung als Kostenfaktor,
sondern das **Mitteln ueber Stichproben eines unbekannten Zustands**. Der
aufgezaehlte Zufallsknoten am AUFDECK-Punkt ist davon strukturell
verschieden -- er mittelt Ausgaenge, die danach oeffentlich sind, statt
Plaene aus nicht unterscheidbaren Welten. Genau dieser Unterschied ist der
Grund, warum der Knoten an die Aufdeck-Stelle gehoert und nicht an die
Wurzel.
