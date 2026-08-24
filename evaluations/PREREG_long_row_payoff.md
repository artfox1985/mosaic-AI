<!-- STATUS: ENTSCHIEDEN | Frage: Verschwinden lange Musterreihen (5/6) schon im rohen Policy-Prior, oder erst in der Suche -- und laesst sich ihre verzoegerte Auszahlung als zusaetzliches Signal sichtbar machen, ohne den Kredit-Horizont-Weg zu wiederholen? | Beleg: KOMPLETT GEFAHREN 2026-08-24, B1 ist ENTSCHIEDEN UND NEGATIV -- aber als falscher HEBEL, nicht als falsches ZIEL (Nutzer-Korrektur, erste Lesart war falsch). Diagnose: par.2 Prior-Verhaeltnis lang/kurz 0,221 bei FORTSETZUNG; par.2a Stufe 3 Initiierung Netz 11,5 Prozent gegen Heuristik 25,2 Prozent, Faktor ~3, flach ueber R1-4. B1 darauf umgeschnitten (Stufenfunktion 0 auf 1 in Musterreihe 5/6, additiv am Blattwert, SCALE 10, w=0,3). Schritt 1 (240 Korpus-Stellungen): Besuchsanteil 0,00317 auf 0,00581, BCI [0,00083; 0,00525] -- Tor bestanden, aber nur Runde 1 abgedeckt. SCHRITT 2 (gepaarte Arena netz-gegen-netz, 407 Seeds, BEIDE Sitzpositionen, 814 Partien, 32 Bloecke): Mechanismus greift -- begonnene lange Reihen +0,310 (t=+7,57), vollendete +0,231 (t=+4,98), Vollendungsquote 0,534 gegen 0,514 also NICHT gefallen, Zugziele wandern aus Reihe 3/4 in Reihe 5/6. FALSIFIKATOR NICHT AUSGELOEST. Trotzdem verliert der Arm klar: Siegquote 42,9 Prozent (gepaart -0,145, t=-4,11), Punkte -3,428 (t=-5,37), Strafpunkte +3,640 (t=+6,75), Plattenpunkte in Summe leicht POSITIV (+0,33), volle Spalten +0,033 (n.s.), k1-Rate identisch 43/312. ENTSCHEIDENDER VORBEHALT: die Vollendungsquote liegt in BEIDEN Armen bei nur ~0,53 -- der Lauf vergleicht zwei inkompetente Regime und sagt NICHTS ueber die Staerke kompetenten Langreihen-Spiels. Ein Blattwert-Additiv kann bewirken DASS eine Reihe angefangen wird, nicht die Faehigkeit sie zu FUEHREN. Die Engstelle bleibt die VOLLENDUNG (Strukturbefund: Bau bis ~4,6 von 6), und die ist eine Trainings-, keine Suchfrage. Vorab-Lesart WIDERLEGT (nicht der Falsifikator: strikt trennen). B2-Zielrichtung praezisiert: nicht lange Reihen sichtbarer machen, sondern ihre Vollendung koennen; ein Arm ohne Vollendungsquote deutlich ueber 0,53 wiederholt B1 -->

# PREREG-SKELETT: Auszahlung langer Musterreihen -- Prior-Sichtbarkeit und Signal-Shaping

Stand **2026-08-24. ENTWURF, nichts gebaut, Plan-Zeitform.** Zwei
Zweige, die zusammen die Reihenwahl-Frage abschliessen sollen: erst
eine billige Diagnose (par.2), dann -- abhaengig vom Diagnose-Ergebnis
-- ein passender Eingriff (par.3). Reihenfolge und Umfang sind
Nutzer-Entscheid (par.7).

## par.1 Anlass, mit den tragenden Fakten (alle in dieser Sitzung geprueft)

1. **Die Praeferenz ist real, flach und nicht geerbt.**
   `tools/probes/row_preference_probe.py`: der Champion zieht in vier
   unabhaengigen Kontexten konsistent 55,5-56,1 % seiner Draft-Ziele auf
   die kurzen Musterreihen 1-3 und meidet Reihe 5/6 (12-13 %) -- FLACH
   ueber alle Runden. Das Heuristik-Selfplay (der Abstammungs-Lehrer,
   `data/holdout` heur-Arm) spielt spaet umgekehrt: Kurz-Anteil faellt
   von 46,0 % (R1-2) auf 33,4 % (R4-5), Reihe 6 wird dort ab R4 am
   HAEUFIGSTEN gezogen. Der Bias ist also im Training verlorengegangen,
   nicht ererbt (Artefakt `row_preference_probe.json`).
2. **Die Vollendungen waren nie legal moeglich -- der Engpass liegt
   VOR der Endplatzierung.** `tools/probes/column_completion_legality_
   probe.py`: 0 von 160 stehengelassenen Hoehe-5-Spalten hatten im
   Restfenster eine legale Vollendung. Blockadegruende: **Musterreihe
   noch nicht voll 87/160 (54 %)**, Spezialfeld nur ueber Sibling-Slot
   41, keine passende Farbe 32 (Artefakt gleichnamig).
3. **Regelkopplung** (`docs/engine_manual.md`, Phase 2 Tiling,
   Z. 125-131, in dieser Sitzung erneut gelesen): Musterreihen werden
   am Rundenende streng von oben (Reihe 1) nach unten (Reihe 6)
   abgearbeitet; eine vollendete Reihe schickt genau EINE Kachel in die
   Kuppel-Zeile, der Rest in den Turm. Reihe 6 ist damit die einzige
   Quelle fuer die unterste Kuppel-Zeile -- ohne sie vollendet
   niemand die letzte Zeile einer Spalte.
4. **Der Kredit-Horizont ist als Erklaerung GESCHWAECHT, nicht der
   Mechanismus selbst geprueft.** `PREREG_bootstrap_horizon.md`
   Stufe 0: ein Value-Ziel, das WEITER vorausschaut (Anker-Variante bis
   zum R5-Freebie statt Horizont 2), korreliert auf den kritischen
   fruehen Zustaenden SCHLECHTER mit dem echten Ausgang (Tau 0,282
   gegen 0,363) und kostet Faktor 20,1 je Label. **Das schliesst
   "tiefer schauen" als Loesung aus, aber nicht "das bestehende Signal
   deutlicher machen"** -- ein additiver Shaping-Term am bestehenden
   Horizont ist ein anderer Hebel als ein laengerer Horizont.
5. **Der Vierer-Vergleich zeigt: der Value-Kopf ist in Runde 5 NICHT
   allgemein schwach.** `PREREG_r5_solver_split.md` par.3e: Tau 0,762
   gegen die exakte Solver-Marge auf k1-aktiven R5-Zustaenden,
   Kennlinien-Steigung 0,87 auf der Gesamtwert-Skala. Gedaempft ist NUR
   der Platten-Anteil. Diese Prereg zielt eine Ebene FRUEHER: nicht auf
   die R5-Bewertung eines fertigen Zustands, sondern auf die
   Draft-ENTSCHEIDUNG in R1-4, die ueberhaupt erst festlegt, ob eine
   lange Reihe gefuettert wird.
6. **Ein strukturell verwandter, aber ausdruecklich ANDERER
   Mechanismus existiert bereits -- und ist tabu.** `wertung_progress`
   (`engine/src/scoring.rs:160`) ist ein Fortschritts-Formungsterm fuer
   die Wertungsplatten-Kriterien (u. a. k1/Spalten), aber er haengt am
   HEURISTIK-Pfad (`mcts.rs::player_total`) und ist der Elo-Anker --
   **NICHT ANFASSEN, das Netz hat ihn nie bekommen und soll ihn auch
   hier nicht bekommen.** Diese Prereg baut, falls ueberhaupt, einen
   EIGENEN, NETZ-seitigen Term nach dem Vorbild von `floor_shaping_
   weight` (net_mcts.rs, additiv am Blattwert, Default aus) -- ein
   anderer Codepfad, andere Ebene (Draft-Fortschritt statt
   Platten-Kriterium), keine Beruehrung des Anker-Terms.
7. **Genau dieses Vorbild ist dreifach validiert.**
   `FLOOR_SHAPING_WEIGHT` (net_mcts.rs, Kommentar in dieser Sitzung
   korrigiert): eine kleine additive Blattwert-Korrektur bewegt die
   Siegquote um ~11 pp (Task A, McNemar p=0,0001) und ist ein SCHALTER
   (an/aus zaehlt, der genaue Wert zwischen 0,15 und 0,6 nicht). Das
   ist der Praezedenzfall dafuer, dass ein kleiner additiver Netz-Term
   reale Staerke bewegen kann, wenn die Suche das zugrundeliegende
   Verhalten sonst nicht sieht.

## par.2 Zweig A: Prior-Sichtbarkeit (Diagnose, billig, zuerst)

**Frage:** schlaegt der ROHE Policy-Prior (vor jeder Suche) eine lange
Reihe ueberhaupt als plausible Fortsetzung vor, wenn sie objektiv
sinnvoll ist -- oder ist die Unterdrueckung schon im gelernten Prior,
bevor die Suche/der Value-Kopf ueberhaupt eingreift?

- **Zustandsauswahl:** Draft-Entscheidungspunkte aus vorhandenen
  Korpora/Arena-Logs (kein neuer Self-Play noetig), an denen (a) eine
  Reihe 5 oder 6 bereits mind. 2 Steine traegt (Fortsetzung ist
  "billig" im Sinne von: noch erreichbar) UND (b) unter den
  angebotenen Fabrik-/Mondbereich-Optionen mindestens eine legale
  Aktion existiert, die diese Reihe weiter fuellt. Stratifiziert nach
  Runde (Schwerpunkt R1-3, wo die Reihe ueberhaupt noch offen ist) und
  Fuellstand.
- **Instrument:** direkter PyTorch-Forward-Pass ohne Suche
  (`state_to_tensor`/`state_to_planes` -> Modell -> rohe Policy-Logits),
  exakt das Verfahren aus `tools/oracle_metrics.py`
  (`prior_mass_on_oracle_top3`-Muster, arena-validiert 7/7 als
  Instrument-Klasse -- wird hier NICHT als Oracle-Metrik verwendet,
  sondern als bewaehrter Lesepfad fuer rohe Priorwerte). Kein
  Engine-Build noetig.
- **Zwei Messungen je Zustand:**
  1. **Prior-Masse** auf der langen-Reihe-Aktion relativ zur Masse auf
     allen legalen kurzen-Reihe-Alternativen (Verhaeltnis, nicht nur
     Rang).
  2. **Nach-Suche-Masse** an derselben Wurzel (`root_completed_q`/
     Besuchsverteilung bei Standard-Sims) -- trennt "der Prior schlaegt
     es vor, die Suche verwirft es" von "der Prior schlaegt es nie
     vor".
- **Referenzpunkt:** dieselbe Messung auf dem Heuristik-Self-Play-Korpus
  (`data/holdout`), das die Spaetrunden-Umkehr bereits zeigt (par.1
  Punkt 1) -- als Kontrast, kein Erfolgskriterium fuer sich.
- **Lesart (vorab):**
  - Prior-Masse hoch, Nach-Suche-Masse niedrig -> die Suche/der
    Value-Kopf unterdrueckt ein vorhandenes Signal -> **Zweig B1**
    (Such-seitiges Shaping) ist der richtige Hebel.
  - Prior-Masse selbst schon niedrig (aehnlich Nach-Suche-Masse) -> das
    Signal fehlt bereits im gelernten Prior -> Such-seitiges Shaping
    wuerde nur kaschieren, nicht die Ursache treffen -> **Zweig B2**
    (Label-/Trainingsseite) ruecken vor, B1 waere trotzdem einen
    billigen Versuch wert (siehe par.4), aber mit gedaempfter Erwartung.
- Kosten: Minuten bis niedrige einstellige Stunden (kein Self-Play, kein
  Training, kein Engine-Build).

### par.2 ERGEBNIS (2026-08-24): Signal fehlt bereits im Prior -- B2 rueckt vor, B1 mit gedaempfter Erwartung

Gefahren mit `tools/probes/long_row_prior_gate.py`, Artefakt
`long_row_prior_gate.json`. **260 qualifizierende Netz-Stellungen** (Reihe
5/6 traegt bereits >= 2 Steine UND mindestens eine legale Fortsetzung
existiert), plus 260 aus dem Heuristik-Korpus als Kontrast, Champion
`v21_2d_brierbest`, `sims=200`. Runde 5 ausgeschlossen (par.2-Fokus R1-4;
`net_search_state_json` faellt dort auf einen Alpha-Beta-Loeser-Pfad mit
anderem Rueckgabe-Schema zurueck -- beim Bauen entdeckt, dokumentiert im
Werkzeug-Kopf). Zwei Selbsttests vorab bestanden (lokale `action_to_id`
gegen die Referenzfunktion; jeder Suchkandidat legal), dasselbe validierte
Instrument wie beim Floor-Aversions-Tor.

| Groesse | Netz | Heuristik |
|---|---|---|
| Roher Prior, lange Reihe (Mittel) | 0,110 | 0,068 |
| Roher Prior, kurze Reihe (Mittel) | 0,499 | 0,325 |
| Verhaeltnis lang/kurz, Prior | **0,221** | **0,210** |
| Suchanteil, lange Reihe (Mittel) | 0,116 | 0,089 |
| Suchanteil, kurze Reihe (Mittel) | 0,505 | 0,353 |
| Verhaeltnis lang/kurz, nach Suche | 0,230 | 0,254 |
| Delta Prior->Suche (lang / kurz) | +0,006 / +0,006 | +0,021 / +0,027 |

**Verdikt nach der vorab festgelegten Lesart: Prior-Masse ist bereits
niedrig (Verhaeltnis ~0,22, nicht ~1) und die Suche bewegt sie kaum (Delta
<= 0,006 bei Netz).** Das ist die zweite Lesart aus par.2: *"das Signal
fehlt bereits im gelernten Prior -> Zweig B2 (Label-/Trainingsseite)
rueckt vor, B1 waere trotzdem einen billigen Versuch wert, aber mit
gedaempfter Erwartung."*

**Wichtige Einordnung, damit das nicht mit dem Floor-Aversions-Befund
verwechselt wird:** dies ist eine MODERATE, keine EXTREME Unterdrueckung.
Lange Reihen bekommen rund ein Fuenftel der Prior-Masse kurzer Reihen --
das ist deutlich unter dem "fairen" Anteil (bei 3 langen und 3 kurzen
Zeilen waere 1,0 die Parity-Marke), aber himmelweit von der buchstaeblichen
Null des Floor-Ziels aus `PREREG_floor_action_aversion.md` entfernt. Zwei
verschiedene Grade derselben Asymmetrie-Familie, nicht derselbe Befund
zweimal gemessen.

**Zweiter Befund -- KORRIGIERT 2026-08-24, meine erste Deutung war falsch.**

Erste, FALSCHE Fassung dieses Absatzes: *"das Lang/Kurz-Verhaeltnis ist bei
Netz (0,221) und Heuristik (0,210) fast identisch ... dort unterscheiden
sich Netz und Lehrer kaum."* Das steht so nicht in den Daten. Am Werkzeug
nachgesehen (`long_row_prior_gate.py:314-315`): **BEIDE Spalten rufen
`evaluate(..., model, ...)` mit demselben `model` auf, dem CHAMPION.** Die
Spalte "heuristik" ist also der Prior DES CHAMPIONS, ausgewertet auf
heuristik-generierten Stellungen -- nicht das Verhalten der Heuristik. Ein
Vergleich zweier Agenten ist das nicht und war es nie.

Was die Zahl tatsaechlich sagt: **der Prior des Champions liefert auf zwei
sehr verschiedenen Zustandsverteilungen praktisch dasselbe Verhaeltnis
(0,221 gegen 0,210).** Die Unterdrueckung haengt also NICHT an der
Zustandsverteilung -- sie ist eine Eigenschaft des Netzes, die es in
fremde Stellungen mitnimmt. Das ist ein brauchbarer Befund, nur ein
anderer als der behauptete: er staerkt die Prior-Diagnose (die
Unterdrueckung ist robust), sagt aber NICHTS ueber den Lehrer.

**Was daraus offen bleibt und diesen Zuschnitt erst scharf macht:** die
Reihen-Sonde vergleicht GESPIELTE Zuege beider Agenten und findet dort
einen klaren Unterschied (Netz flach, Lehrer adaptiert spaet). Dieser
Zuschnitt misst PRIOR-MASSE nur des Netzes auf einer engeren
Entscheidungsklasse (Fortsetzung einer bereits begonnenen langen Reihe).
Beides ist vereinbar, wenn der Agentenunterschied im BEGINNEN langer
Reihen liegt statt im Fortsetzen -- eine Ableitung, keine Messung. Sie ist
Gegenstand von par.2a.

**Je Runde** (n=12/105/82/61 fuer R1-4 -- R1 duenn besetzt, Vorsicht bei
Einzelaussagen): das Verhaeltnis schwankt zwischen 0,13 (R3) und 0,53
(R1), ohne klaren monotonen Trend. Keine Rundenabhaengigkeit, die die
Kredit-Horizont-Hypothese stuetzen wuerde.

**Folge fuer par.4/par.7 (Nutzer-Entscheid, kein Automatismus):** B2
(Label-/Trainingsseite) ist nach diesem Tor die naheliegendere Richtung.
B1 (Such-seitiges Shaping) ist damit nicht ausgeschlossen -- das Tor sagt
ausdruecklich "billiger Versuch wert" -- aber mit gedaempfter Erwartung,
weil die Suche das vorhandene, wenn auch geringe, Prior-Signal in den
gemessenen 260 Stellungen kaum verstaerkt hat.

## par.2a Initiierung gegen Fortsetzung (2026-08-24, Nutzer-Auftrag)

**Frage:** liegt der Agenten-Unterschied im BEGINNEN langer Reihen statt im
FORTSETZEN? par.2 misst nur Fortsetzungen; die Reihen-Sonde vergleicht
gespielte Zuege beider Agenten und findet dort einen Unterschied. Beides ist
vereinbar, wenn die Luecke bei der Initiierung sitzt.

### Stufe 1 (Arena-Logs): auffaellig, aber KONFUNDIERT -- nicht verwertbar

`tools/probes/row_initiation_probe.py`, Anteil "Initiierung geht in eine
lange Reihe", gespielte Zuege, gepaart in denselben Partien:

| | R1 | R2 | R3 | R4 | R5 |
|---|---|---|---|---|---|
| Champion | 21,8 % | 27,7 % | **2,1 %** | 13,7 % | 20,5 % |
| Heuristik | 33,4 % | 5,3 % | 12,8 % | 17,1 % | 17,5 % |

Alle gepaarten t-Werte gross (|t| = 3 bis 22). Der R3-Einbruch des
Champions sah nach einem scharfen Strukturbefund aus.

**Er ist keiner.** Der Anteil ist konfundiert: eine lange Reihe laesst sich
nur initiieren, wenn sie gerade LEER ist. Wer in R2 viele lange Reihen
anfaengt, kann sie in R3 nicht mehr initiieren -- der Zickzack kann reine
Belegungsdynamik sein. **Diese Tabelle wird nicht als Befund gefuehrt.**

### Stufe 2 (Log-Rekonstruktion): am eigenen Selbsttest GESCHEITERT

`tools/probes/row_opportunity_probe.py` sollte die Belegung aus dem Log
rekonstruieren und darauf normieren. Eingebauter Selbsttest: die
Rekonstruktion muss den `[f/c]`-Fuellstand jedes Zuges unabhaengig
reproduzieren. **Er schlug in 233 von 407 Partien an** (netvnet 299/407).

Ursache am Code gefunden, nicht geraten: **`round_end.rs:87
process_unplaceable_rows` leert Musterreihen am Rundenende und schreibt
dafuer KEINE Logzeile.** Eine belegungsgenaue Rekonstruktion aus
Arena-Logs ist damit prinzipiell unmoeglich, ohne `find_unplaceable_rows`
samt Kuppel-Zustand nachzubauen -- also Spielregeln in einer Sonde zu
reimplementieren. Der Zuschnitt wurde deshalb umgestellt statt geflickt.

**Diese Stufe ist hier festgehalten, weil ihr Scheitern ein verwertbarer
Befund ist:** wer kuenftig Musterreihen-Belegung aus Arena-Logs ableiten
will, kann das nicht, und der Selbsttest ist das Werkzeug, das es zeigt.

### Stufe 3 ERGEBNIS (Korpus statt Logs): Faktor ~3, FLACH ueber R1-4

`tools/probes/row_initiation_opportunity_probe.py`. Der Self-Play-Korpus
traegt den Zustand exakt (`state.players[p].pattern_lines`) und die legalen
Zuege direkt -- keine Rekonstruktion, kein Regel-Nachbau. Gemessen wird die
`policy`-Masse (Besuchsverteilung der jeweiligen Suche) auf Aktionen, die
eine LEERE lange Reihe beginnen, **bedingt darauf, dass so eine Aktion
ueberhaupt legal ist**.

Netz: 248 Dateien stratifiziert, 293.250 Drafting-Entscheidungen, davon
100.864 mit Gelegenheit, 2.480 Partien. Heuristik: kompletter
Holdout-Korpus, 65.226 Entscheidungen, 14.377 mit Gelegenheit, 500 Partien.

| | gesamt | R1 | R2 | R3 | R4 | R5 |
|---|---|---|---|---|---|---|
| **Netz** | **11,5 %** | 7,9 % | 10,6 % | 8,8 % | 11,2 % | **20,2 %** |
| **Heuristik** | **25,2 %** | 27,0 % | 28,6 % | 27,9 % | 27,0 % | **19,2 %** |

Block-Bootstrap-95-%-KIs (ueber Partien) sind eng und ueberlappen nirgends,
etwa gesamt Netz [0,113; 0,116] gegen Heuristik [0,249; 0,256].

**Befund: das Netz legt auf das Beginnen einer langen Reihe rund EIN
DRITTEL der Masse des Lehrers -- konstant ueber die Runden 1 bis 4.** Der
R3-Einbruch aus Stufe 1 war vollstaendig der Belegungs-Konfundierer; er
verschwindet unter Normierung restlos.

**Der Konfundierer, jetzt beziffert:** die Gelegenheits-Quote betraegt beim
Netz 34,4 %, beim Lehrer 22,0 % -- das Netz hat deutlich HAEUFIGER eine
leere lange Reihe, genau weil es sie seltener beginnt. Stufe 1 hat also
teilweise die Folge der Ursache gemessen.

**Zweiter Befund: die Konvergenz in Runde 5** (20,2 % gegen 19,2 %, KIs
ueberlappen). Nur dort verhaelt sich das Netz wie der Lehrer.
Caveat, ausdruecklich: Runde 5 laeuft ueber einen anderen Suchpfad (exakter
R5-Loeser), die `policy` dort ist nicht dasselbe Objekt wie in R1-4 -- die
Konvergenz ist berichtenswert, aber nicht ohne Weiteres als
"Verhaltensangleichung" zu lesen.

### Folge fuer par.2 und par.3

Die Ableitung aus par.2 ist **bestaetigt**: die Luecke sitzt in der
INITIIERUNG, nicht in der Fortsetzung. Das praezisiert den Zuschnitt
erheblich:

- Ein Shaping-Term (B1), der Fortschritt in bereits begonnenen langen
  Reihen aufwertet, trifft die falsche Entscheidung -- dort ist das Netz
  nicht auffaellig schlechter als der Lehrer (par.2: Verhaeltnis 0,22, und
  dieselbe Groesse auf beiden Zustandsverteilungen).
- Was fehlt, ist der ERSTE Stein in eine lange Reihe. Ein Eingriff muesste
  genau diese Aktionsklasse treffen, nicht den Fortschritt allgemein.

Das ist eine schaerfere Vorgabe fuer B1 und B2, als par.3 sie bisher hat --
und sie war ohne die Entkonfundierung nicht sichtbar.

## par.3 Zweig B: Auszahlung sichtbar machen (Eingriff, nach par.2 zuzuschneiden)

### B1 -- Such-seitiger Shaping-Term auf die INITIIERUNG (Nutzer-Entscheid 2026-08-24)

**Umgeschnitten nach par.2a.** Der urspruengliche Entwurf wertete
*Fortschritt* in Reihe 5/6 auf (belegte Slots relativ zur Kapazitaet).
par.2a Stufe 3 zeigt, dass das die falsche Aktionsklasse getroffen haette:
beim FORTSETZEN ist das Netz nicht auffaellig schlechter (par.2:
Verhaeltnis 0,22, auf beiden Zustandsverteilungen gleich), beim BEGINNEN
dagegen um Faktor ~3 (11,5 % gegen 25,2 %, flach ueber R1-4). Der Term
zielt deshalb auf den ERSTEN Stein.

**Warum B1 ueberhaupt noch aussichtsreich ist -- und warum der
Floor-Befund es nicht erledigt.** `PREREG_floor_action_aversion.md` par.6
hat gezeigt, dass ein Blattwert-Term wirkungslos bleibt, wenn die
Wurzelauswahl die Aktion vorher verwirft: dort war die Prior-Masse exakt 0
in 280/280 Stellungen, ein Logit-Abstand, den Gumbel-Rauschen nie
ueberbrueckt. **Hier ist die Lage anders und das ist der entscheidende
Unterschied:** die Masse auf Initiierungs-Aktionen betraegt 11,5 %, liegt
also weit im Bereich der Top-m-Wurzelauswahl. Ein Blattwert-Term kann diese
Aktionen erreichen. Der Floor-Befund schliesst B1 also nicht aus, er
erklaert nur, wo ein solcher Term NICHT wirkt.

**Form des Terms.** Analog `floor_shaping_delta` (`net_mcts.rs:958`) als
reine Zustandsfunktion, ego-perspektivisch und differenzbildend:

```
init_delta(state, ego) = (gestartete_lange_Reihen(ego)
                          - gestartete_lange_Reihen(gegner)) / SCALE
```

wobei `gestartete_lange_Reihen` = Anzahl der Reihen 5/6 mit mindestens
einem Stein (Wertebereich 0-2). **STUFENFUNKTION am Uebergang 0 -> 1, kein
Rampenterm** -- genau die Entscheidung, an der die gemessene Luecke sitzt.
Die Differenzform ist vom Floor-Vorbild uebernommen, damit kein
systematischer Versatz auf der Blattwertskala entsteht; die reine
Eigenseiten-Form waere die Alternative und ist in par.7 als offener Punkt
gefuehrt.

- **Codepfad:** neu, im Netz-Suchpfad (`net_mcts.rs`), NICHT
  `wertung_progress`/`mcts.rs` (par.1 Punkt 6). Default-Gewicht 0 =
  byte-identisches Bestandsverhalten (Paritaets-Gate wie ueblich).
- **Kapselungs-Anschluss:** direkt als `SearchConfig`-Feld bauen (zweiter
  Knopf nach `MOSAIC_IMPLICIT_MINIMAX_A`), nicht erst als Env-Knopf.

#### GEBAUT UND ABGENOMMEN (2026-08-24)

Nutzer-Entscheid: `SCALE = 10`. Gebaut, nichts gemessen -- die Messkette
unten steht noch komplett aus.

**Was gebaut ist:**

| Baustein | Stelle |
|---|---|
| `LONG_ROW_INIT_SHAPING_SCALE = 10.0` | `net_mcts.rs`, mit ausgerechneter Begruendung im Doc-Kommentar |
| `long_rows_started` (Stufenfunktion, 0..=2) | zaehlt Musterreihe 5/6 mit >= 1 Fliese, KEIN Fuellstands-Anteil |
| `long_row_init_delta(state, ego)` | `(eigen − gegner) / SCALE`, nullsummen wie `floor_shaping_delta` |
| `SearchConfig.long_row_init_shaping_w` | Default 0,0; Env `MOSAIC_LONG_ROW_INIT_W`; Spec-PFLICHTFELD |
| Anwendung | direkt nach dem Floor-Additiv, `w == 0.0` ueberspringt den Block komplett |

**Abnahme, alle vier Punkte bestanden:**

1. **Suite 506/0** (26 ignoriert).
2. **Paritaets-Hash `8c6684ff…` haelt** (`tools/parity_probe.py`, nach
   Wheel-Neubau und -Installation) -- Defaults byte-identisch zum Bestand.
3. **Determinismus-Gegenprobe** 20/20 identisch (aus gegen aus, gleicher
   Seed).
4. **Wirkungsnachweis** auf 60 qualifizierenden Korpus-Stellungen (leere
   lange Reihe UND legale Aktion dorthin): bei `w = 0,3` aendert sich die
   Zugwahl in **10 von 60** Faellen. Der Knopf erreicht die Entscheidung
   also tatsaechlich -- das war nach dem Floor-Befund
   (`PREREG_floor_action_aversion.md` par.6: Prior exakt 0, Blattwert-Term
   unerreichbar) die offene Frage, und sie ist positiv beantwortet.

**Drei Bau-Entscheidungen, die begruendet gehoeren:**

- **Die Blattwert-Stelle liegt nicht in `make_node`**, sondern in
  `node_from_net_outputs` -- einer Extraktion, die AUCH der gebuendelte
  Wurzelpfad (`batched_expand_root_candidates`) benutzt. Beide bekamen den
  Parameter; nur `make_node` zu verdrahten haette den Term im Batch-Pfad
  still fehlen lassen.
- **Das neue Spec-Feld ist PFLICHT, nicht optional.** Damit lehnt dieses
  Wheel eine Welle-1-Spec (nur `implicit_minimax_alpha`) hart ab. Das ist
  gewollt: ein eingefrorenes Artefakt gehoert auf sein EIGENES
  mitgeliefertes Wheel; ein stiller Default wuerde genau diesen Fehler
  maskieren und die "beweisbar identisch"-Zusage aushebeln. Geprueft, dass
  der Freeze davon unberuehrt ist -- `frozen_referee_match.py:218` startet
  den Worker mit dem Interpreter AUS dem Artefakt.
  **Vorsicht fuer die naechste Sitzung:** die Spec-Dateien liegen unter
  `/models/*` und sind GITIGNORED. Die beiden aktiven
  (`champion_frozen`, `champion_imm_a02`) sind lokal nachgezogen; jede
  andere Alt-Spec faellt mit einer benannten Fehlermeldung auf, nicht
  still.
- **`cargo build` war gruen, `cargo test` nicht.** Die Suite kompiliert
  `engine/examples/` mit, und `kernbeweis_910002_probe.rs` konstruiert
  `SearchConfig` als Struct-Literal. Nachgezogen mit `0.0` -- jene Sonde
  ist ein Byte-Identitaets-Nachweis, ihr Suchverhalten MUSS unveraendert
  bleiben. (Genau die in CLAUDE.md dokumentierte Push-Blocker-Falle.)

#### Registriertes RISIKO: Initiieren ohne Vollenden

Ein Term, der das blosse Beginnen belohnt, kann eine bekannte Schwaeche
verschaerfen statt sie zu heilen. Der Strukturbefund zum Spaltenbau haelt
fest, dass der Champion lange Reihen bis etwa 4,6 von 6 fuellt und die
letzten Zellen nie -- **es gibt also bereits ein Vollendungs-Defizit, und
eine Initiierungs-Praemie zahlt genau darauf ein.** Das ist keine
Nebenbemerkung, sondern der wahrscheinlichste Weg, wie dieser Arm
"funktioniert" und trotzdem schadet.

**Pflicht-Kennzahl und Falsifikator, vorab festgelegt:** die
**Vollendungsquote begonnener langer Reihen** (Anteil der in Reihe 5/6
begonnenen Reihen, die ihre Kapazitaet erreichen) ist gleichrangig mit der
Initiierungsrate zu berichten.

- Initiierung steigt **und** Vollendungsquote bleibt gleich oder steigt:
  der behauptete Mechanismus.
- Initiierung steigt **und** Vollendungsquote faellt: **NICHT-ERFOLG, auch
  bei guenstiger Arena.** Der Term hat dann mehr angefangene Ruinen
  erzeugt, nicht mehr fertige Reihen. Ausdruecklich als solcher zu
  berichten und nicht als Teilerfolg zu buchen. (Dieselbe Bauart wie der
  Marge-in-Siege-Falsifikator in `PREREG_saturating_score_utility.md`
  par.8 -- eine Richtungsvorhersage, die auch bei guenstigem Ausgang
  scheitern kann.)

#### Messkette

1. **Direktwirkung auf die Entscheidung, OHNE neue Partien.** Der Knopf
   an/aus auf DEMSELBEN festen Satz Korpus-Stellungen, gemessen mit
   `tools/probes/row_initiation_opportunity_probe.py` (Suchseite statt
   `policy`-Feld). Das isoliert die Wirkung des Knopfes auf die
   Zugwahl exakt und kostet keine Arena. **Zuerst, weil ein Term, der die
   Entscheidung nicht bewegt, gar nicht erst in eine Arena muss.**
2. **Staerke: gepaarte Arena NETZ-GEGEN-NETZ**, 407 Kampagnen-Seeds,
   `--log-games`. Nicht gegen die Heuristik -- die
   Gegnerspezifitaets-Lehre vom 2026-08-23/24 gilt hier von Anfang an
   (der Implicit-Minimax-k1-Sprung von +7,0 pp gegen die Heuristik war
   netz-gegen-netz exakt null).
3. **Ausgewiesen:** Siege (Block-Ebene), k1-Rate, Initiierungsrate,
   **Vollendungsquote** (Falsifikator oben), sowie die sechs
   Standard-Kennzahlen je Seite (CLAUDE.md).

**Instrument-Hinweis, aus par.2a Stufe 2 gelernt:** die Initiierungs- und
Vollendungs-Kennzahlen sind **aus dem Korpus** zu ziehen, nicht aus
Arena-Logs. `round_end.rs:87` leert Musterreihen ohne Logzeile; eine
belegungsgenaue Auswertung aus Logs ist prinzipiell unmoeglich. Wer diese
Kennzahlen aus einem Arena-Lauf braucht, muss den Zustand mitschreiben
lassen -- das ist ein eigener Aufwandsposten und keine Selbstverstaendlichkeit.

**ERLEDIGT (2026-08-24, Nutzer-Auftrag "erweitere den arena mitschrieb"):**
dieser Aufwandsposten ist gebaut. Das Arena-Artefakt traegt jetzt je Partie
und Seite drei Zaehler, aus denen die Vollendungsquote direkt folgt:

| Feld | Bedeutung | Zaehlstelle |
| --- | --- | --- |
| `long_rows_started` | Uebergang LEER -> belegt in Musterreihe 5/6 | `execution.rs::execute_place`, vor `add_tiles` gelesen |
| `long_rows_completed` | Reihe voll ins Tiling gegangen | `round_end.rs::execute_tiling_action`; `validate_tiling_action` lehnt `!is_complete()` ab, die Stelle IST das Vollendungsereignis |
| `long_rows_cleared_unplaceable` | unvollendeter Abbruch, Steine auf die Strafleiste | `round_end.rs::process_unplaceable_rows` |

Vollendungsquote = `completed / started`; `cleared_unplaceable` ist der
teure Abbruch, der Rest steht am Partie-Ende noch belegt.

**Warum Zaehler und keine Logzeile:** `state.log` ist das Vergleichsobjekt
des Kernbeweises (`referee.rs::full_log`, dort so dokumentiert). Eine neue
Logzeile haette ihn gegen das eingefrorene Artefakt gebrochen. Die Zaehler
liegen wie ihr Vorbild `total_floor_penalties` auf `PlayerBoard` und
erscheinen nur im Arena-JSON -- `state.log` ist unberuehrt.

Abnahme: Suite 506/0 gruen, **Paritaets-Hash `8c6684ff...` haelt nach
Wheel-Neubau und Neuinstallation** (die Erweiterung ist such-neutral).
Live-Gegenprobe netz-gegen-netz mit beiden Specs, 4 Partien a 60 Sims:
Start 14/12, vollendet 7/8, geraeumt 0/1 -- Quote 0,50 gegen 0,667. Bei
n=4 ist das Rauschen, belegt aber die Ableitbarkeit Ende zu Ende.

Ein Test in `self_play.rs::arena_match_produces_results` prueft die
Buchhaltung (`completed + cleared <= started` je Seite) und dass ueber
vier Partien ueberhaupt Starts gezaehlt werden -- sonst waere die
Ungleichung trivial erfuellt.

**Vorab-Lesart:** primaer kein Staerkeverlust; eine Verschiebung der
Initiierungsrate Richtung Lehrer-Niveau bei gehaltener Vollendungsquote ist
der Bonus-Befund, der die Kausalkette schliesst. Ein Sweep wird NICHT
vorab erwartet (Praezedenz Floor-Shaping: Schalter, kein Regler) -- ein
Wert genuegt zum Testen.

### Messkette Schritt 1 ERGEBNIS (2026-08-24): Tor BESTANDEN, aber knapp und schmal

Gemessen mit `tools/probes/long_row_init_knob_effect.py`, Artefakt
`evaluations/long_row_init_knob_effect.json`. 240 qualifizierende
Korpus-Stellungen (leere lange Reihe UND legale Steinaktion dorthin, sonst
kann der Term per Konstruktion nichts bewegen), 200 Sims,
w = 0,3, gepaart mit identischem Seed je Stellung in beiden Armen,
Block-Bootstrap ueber `game_id`.

| Groesse | aus | an | Delta | 95-Prozent-BCI |
| --- | --- | --- | --- | --- |
| Besuchsanteil Initiierung LANG | 0,00317 | 0,00581 | **+0,00264** | [0,00083; 0,00525] |
| Besuchsanteil Initiierung KURZ | 0,44977 | 0,44894 | -0,00083 | [-0,00183; -0,00017] |

Stellungsweise: **10 hoch, 0 runter, 230 unveraendert.**

**Verdikt: das Tor aus par.4 Punkt 2 ist bestanden.** Die Richtung stimmt,
das Intervall schliesst die Null aus, und keine einzige Stellung bewegt
sich gegen die Absicht. Die Masse kommt erkennbar aus der Kurzreihen-
Initiierung (-0,00083, ebenfalls null-ausschliessend).

**Drei Einschraenkungen, die zum Ergebnis gehoeren:**

1. **Der Effekt ist winzig.** Der Besuchsanteil auf Initiierung langer
   Reihen steigt von 0,32 auf 0,58 Prozent. Der Term verschiebt die
   Entscheidung, aber er stellt das Verhalten nicht um. Achtung beim
   Vergleich: das ist ein BESUCHSANTEIL EINER Suche und NICHT dieselbe
   Groesse wie die 11,5 gegen 25,2 Prozent aus par.2a Stufe 3 (dort:
   Anteil der Gelegenheiten, bei denen tatsaechlich initiiert wurde).
   Die beiden Zahlen duerfen nicht verrechnet werden.
2. **Nur Runde 1.** Alle 240 Stellungen liegen in Runde 1
   (`je_runde` im Artefakt). Das ist kein Zufall, sondern ein
   Auswahl-Artefakt: die Sonde nimmt je Datei die ersten bis zu zehn
   qualifizierenden Records, und die Korpus-Pickles stehen in Zugreihenfolge.
   **Die Runden 2-4 sind damit ungeprueft** -- ausgerechnet die, in denen
   par.2a den Faktor 3 als flach ueber R1-4 ausweist. Wenn Schritt 2
   keinen Effekt zeigt, ist das die erste Stelle, an der nachzusehen ist.
3. **Abweichung vom registrierten Instrument.** Die Messkette nannte
   `row_initiation_opportunity_probe.py`. Die tatsaechliche Sonde ist
   neu gebaut, weil jene Sonde den Knopf nicht schaltet und keine
   gepaarte An/Aus-Struktur hat; die Qualifikations- und
   Bootstrap-Logik ist uebernommen. Runde 5 ist ausgeschlossen (exakter
   R5-Loeser, andere Suche) -- dieselbe Einschraenkung wie in
   `long_row_prior_gate.py`.

**Folge:** Schritt 2 (gepaarte Arena netz-gegen-netz, 407 Seeds) ist
freigegeben. Vorab-Lesart bleibt "primaer kein Staerkeverlust"; nach
diesem Schritt-1-Bild ist ein Staerke-EFFEKT in beide Richtungen
unwahrscheinlich, und der eigentliche Ertrag des Laufs sind die
Initiierungs- und Vollendungszahlen aus dem erweiterten Mitschrieb.

### Messkette Schritt 2 ERGEBNIS (2026-08-24): Mechanismus BESTAETIGT, Staerke VERLOREN

Gepaarte Arena netz-gegen-netz, `alphazero_v21_2d_brierbest` beidseitig,
400/400 Sims, 407 Kampagnen-Seeds, **beide Sitzpositionen** (Pflicht-Brett-
wechsel) = 814 gepaarte Partien. Artefakte
`paired_arena_env_lrinit_netvnet.json` und `..._swap.json`, Auswertung
`tools/probes/long_row_init_arena_eval.py` ->
`evaluations/long_row_init_arena_eval.json`. Die 407 Seeds sind mengen- UND
reihenfolgengleich mit `paired_arena_env_imm_netvnet.json` (in dieser Sitzung
nachgeprueft), der Lauf ist also direkt mit dem Implicit-Minimax-Vergleich
vergleichbar. Statistik auf BLOCK-Ebene, Blockmittel je Datei gebildet
(32 Bloecke a 25 Partien).

#### Der Falsifikator ist NICHT ausgeloest

| Groesse | AN | AUS | gepaart AN-AUS | t |
| --- | --- | --- | --- | --- |
| begonnene lange Reihen je Partie | 3,639 | 3,324 | **+0,310** | **+7,57** |
| vollendete lange Reihen je Partie | - | - | **+0,231** | **+4,98** |
| **Vollendungsquote** | **0,534** | **0,514** | +0,019 | +1,42 |
| unplatzierbar geraeumt je Partie | - | - | +0,035 | +1,43 |

Der registrierte Nicht-Erfolgs-Fall war "Initiierung hoch **und**
Vollendungsquote runter". Die Initiierung steigt hoch signifikant, die
Vollendungsquote faellt **nicht** -- sie steigt leicht (nicht signifikant).
**Der behauptete Mechanismus ist damit belegt:** der Term erzeugt keine
angefangenen Ruinen, sondern mehr fertige lange Reihen.

Die Reihenwahl bestaetigt das direkt (Zugziele ueber alle 814 Partie-Seiten):

| Musterreihe | 1 | 2 | 3 | 4 | 5 | 6 |
| --- | --- | --- | --- | --- | --- | --- |
| Delta AN-AUS | +1 | -17 | -230 | -351 | **+453** | **+269** |

Die Verlagerung geht aus den Reihen 3 und 4 in die Reihen 5 und 6 -- genau
die Zielmenge des Knopfes (`LONG_ROW_INDICES = [4, 5]`, 0-indexiert).

#### Und der Arm verliert trotzdem, deutlich

| Groesse | gepaart AN-AUS | t |
| --- | --- | --- |
| **Siegquote** | **-0,145** (42,9 Prozent) | **-4,11** |
| eigene Punkte | **-3,428** | **-5,37** |
| Strafpunkte | **+3,640** | **+6,75** |
| Zuege mit Ziel Strafleiste | +0,753 | +6,32 |
| Steine auf die Strafleiste | +1,394 | +6,68 |
| Ueberlauf-Steine | +0,239 | +2,79 |
| Runden mit Strafe | +0,146 | +3,14 |
| volle Spalten | +0,033 | +1,83 |
| Teilspalten >= 4 | -0,058 | -1,38 |
| k1-Rate | 43/312 gegen 43/312, **identisch** | - |

**Die Punktebilanz geht auf, und sie zeigt auf die Strafleiste.** Die
Plattenpunkte je Kriterium sind in der Summe leicht POSITIV fuer den AN-Arm
(+0,33 ueber alle acht Kriterien; groesster Einzelposten "Mehrfarbige Felder"
-0,40, dagegen "Spezialfelder" +0,28 und "Eckplatten" +0,16). Die
Strafleiste kostet +3,55 Punkte je Partie (21,09 gegen 17,54). Beides
zusammen ergibt -3,22, gemessen sind -3,39 -- der Rest von etwa 0,17 liegt
in den uebrigen Score-Bestandteilen und ist nicht weiter aufgeschluesselt.

**Rechenhinweis, damit nichts doppelt gezaehlt wird:** die Marge ist in
diesem Aufbau algebraisch 2x die Punktedifferenz (beide Seiten spielen
DIESELBE Partie, marge_AN = -marge_AUS). Der Wert -6,855 bei identischem
t=-5,37 ist deshalb KEIN unabhaengiger Befund, sondern dieselbe Zahl
skaliert. In gepaarten Netz-gegen-Netz-Laeufen traegt die Marge nichts ueber
die Punkte hinaus bei.

#### Lesart (NUTZER-KORREKTUR 2026-08-24, erste Fassung war falsch)

**Die Vorab-Lesart "primaer kein Staerkeverlust" ist widerlegt.** Sie und
der Falsifikator sind strikt zu trennen: der Falsifikator hat NICHT
ausgeloest, die Vorab-Lesart schon. Das Ergebnis ist damit keiner der beiden
vorregistrierten Zweige, sondern ein dritter: **der Mechanismus greift und
der Arm verliert trotzdem.**

**Was daraus NICHT folgt -- und zuerst falsch registriert war:** die erste
Fassung dieses Abschnitts schloss, die Meidung langer Musterreihen sei
"kein blinder Fleck, sondern richtiges Spiel". Das ist ein unzulaessiger
Sprung, vom Nutzer zurueckgewiesen mit der Begruendung, dass so kein ernst
zu nehmender Gegner spielt. Der Einwand ist durch die eigenen Zahlen
gestuetzt:

**Die Vollendungsquote liegt in BEIDEN Armen bei rund 0,53.** Wer eine
Reihe mit Kapazitaet 5 oder 6 beginnt und sie in der Haelfte der Faelle
nicht fertigbekommt, spielt lange Reihen schlecht -- das gilt fuer den
AN- wie fuer den AUS-Arm. Der Lauf vergleicht also zwei inkompetente
Regime und stellt fest, dass "weniger davon" besser abschneidet. Ueber die
Staerke KOMPETENTEN Langreihen-Spiels sagt er nichts. Die Strafleisten-
Rechnung ist damit kein Beleg gegen lange Reihen, sondern der erwartbare
Preis dafuer, ein Netz in ein Regime zu schieben, das es nie gelernt hat.

**Was der Lauf wirklich zeigt: B1 war der falsche HEBEL, nicht das falsche
ZIEL.** Ein Additiv am Blattwert kann bewirken, DASS eine lange Reihe
angefangen wird -- es kann die Faehigkeit, sie zu FUEHREN (Steinwahl,
Timing, Ueberlaufschutz, Vollendungs-Sequenz), nicht mitliefern. Genau
diese Faehigkeit fehlt, und genau dort sitzt der Strukturbefund zum
Spaltenbau: Bau bis etwa 4,6 von 6, die letzten Zellen nie. Die
Engstelle ist die VOLLENDUNG, und die ist eine Trainings-, keine
Suchfrage.

**Folge fuer B2:** offen und eigener Nutzer-Entscheid, aber die
Zielrichtung praezisiert sich. Nicht "lange Reihen sichtbarer machen"
(das kann B1, und es reicht nicht), sondern **die Vollendung langer
Reihen ueberhaupt erst koennen**. Ein Arm, der die Initiierung erhoeht,
ohne die Vollendungsquote deutlich ueber 0,53 zu heben, wiederholt B1.

**Registrierter Vorbehalt zum w-Sweep:** ein kleineres w ist nicht durch
dieses Ergebnis motiviert -- w skaliert Nutzen und Preis gleichzeitig, und
die fehlende Faehigkeit bleibt bei jedem w dieselbe. Ein Sweep waere eine
NEUE Registrierung; die Prereg hat vorab "Schalter, kein Regler"
festgehalten (Praezedenz Floor-Shaping).

**Methodische Lehre, teuer bezahlt:** aus "Eingriff X in Richtung Y
verliert" folgt NICHT "Y ist falsch". Es folgt nur, dass X in diesem
Zustand verliert. Der Unterschied ist genau die Kontrollgruppe, die hier
fehlt: ein Agent, der lange Reihen KANN. Solange die Vollendungsquote in
beiden Armen gleich schlecht ist, ist die Faehigkeit konstant gehalten und
nicht mitgemessen.

### B2 -- Label-/Trainingsseite (Folgearm, NICHT jetzt gebaut, nur skizziert)

Falls par.2 auf einen bereits im Prior fehlenden Wert zeigt: die
verzoegerte Auszahlung muesste in den TRAININGS-Labels sichtbarer
werden, nicht nur in der Laufzeit-Suche. Zwei Kandidaten, keiner
zugeschnitten:

- Ein zusaetzliches, additives Trainingsziel-Signal (Analog zu B1, aber
  in die Self-Play-Labels geschrieben statt zur Laufzeit addiert) --
  teuer (neuer Korpus/Training), erst nach B1-Ergebnis sinnvoll.
- Orakel-Action-Labels fuer plattenrelevante Zustaende (der in
  `PREREG_uvfa_plate_regime.md` par.4 bereits registrierte,
  ausdruecklich GEDAEMPFTE AZAL-Strang) -- keine neue Idee, sondern der
  bestehende Verweis; diese Prereg aendert nichts an seiner gedaempften
  Erwartung.

B2 ist bewusst nur benannt, nicht vorregistriert -- ein Zuschnitt lohnt
erst, wenn par.2 die Richtung vorgibt.

## par.4 Reihenfolge und Gate

**Stand 2026-08-24:** par.2 und par.2a sind GEFAHREN, die Weichenstellung
ist damit erfolgt, und B1 ist auf die Initiierung umgeschnitten
(Nutzer-Entscheid). Es gilt jetzt:

1. ~~par.2 zuerst~~ -- erledigt (par.2, par.2a Stufen 1-3).
2. **B1, Messkette Schritt 1 zuerst** (Knopf an/aus auf festen
   Korpus-Stellungen, keine Arena). Bewegt der Term die Entscheidung
   nicht, endet der Arm dort -- ein billiges Tor VOR dem teuren Teil.
3. **B1, Messkette Schritt 2** (gepaarte Arena netz-gegen-netz) nur nach
   Schritt 1.
4. **B2 fruehestens nach B1**, eigener Zuschnitt, eigene
   Nutzer-Freigabe. Die par.2-Lesart ("Signal fehlt bereits im Prior")
   spricht inhaltlich fuer B2 -- B1 ist trotzdem zuerst dran, weil er
   ungleich billiger ist und sein Schritt 1 gar keine Partien kostet.

## par.5 Beruehrungspunkte mit offenen Nebenpunkten

- Der Fix von `tools/probes/row_preference_probe.py:190-198`
  (Seiten-Labelling in `imm_netvnet`) ist fuer diesen Zuschnitt
  ENTSCHAERFT, aber nicht erledigt: die B1-Kennzahlen laufen nach dem
  Umschnitt ueber `row_initiation_opportunity_probe.py` (Korpus,
  eindeutige Seitenzuordnung), nicht ueber die Reihenwahl-Verteilung aus
  jener Datei. Wer sie dennoch heranzieht, braucht den Fix vorher --
  dieselbe Falle hat am 2026-08-24 schon `penalty_track_probe.py`
  getroffen (dort behoben).
- Die Legalitaets-Sonde (`column_completion_legality_probe.py`) bleibt
  die Referenz fuer "wie viele Faelle betrifft das" -- diese Prereg
  wiederholt sie nicht, sondern baut auf ihrem Befund auf.

## par.6 Abgrenzung -- was das NICHT ist

- **Nicht** eine Wiederholung von `PREREG_bootstrap_horizon.md` Stufe 0
  (Kredit-Horizont-Tiefe) -- die ist geschlossen (par.1 Punkt 4).
- **Nicht** ein Eingriff an `wertung_progress`/dem Heuristik-Anker
  (par.1 Punkt 6) -- der bleibt in jeder Form unangetastet.
- **Nicht** Teil B des R5-Solver-Split (`PREREG_r5_solver_split.md`,
  R5-Value-Kalibrierung) -- andere Ebene (Draft-Entscheidung vor
  Runde 5, nicht R5-Blattbewertung); beide Straenge koennen parallel
  laufen, keine gemeinsame Messung.
- **Kein** Suchparadigmen-Wechsel (bleibt geschlossen, RESEARCH_*-
  Recherchen 2026-08-22).

## par.7 OFFENE NUTZER-ENTSCHEIDE (vor Baubeginn)

~~1. Par.2 sofort freigeben oder parken?~~ -- erledigt, gefahren 2026-08-24.
~~2. B1 unabhaengig vom Diagnose-Ausgang bauen?~~ -- gegenstandslos, die
Diagnose liegt vor und hat B1 umgeschnitten (Nutzer-Entscheid 2026-08-24).
~~3. Stichprobengroesse fuer par.2?~~ -- erledigt (par.2: 260 Stellungen;
par.2a Stufe 3: 100.864 Gelegenheits-Entscheidungen).

**Weiterhin offen:**

1. **Form des Terms: Differenz oder reine Eigenseite.** par.3/B1 setzt die
   Differenzform `(eigen - gegner)` nach dem Floor-Vorbild an, damit kein
   systematischer Versatz auf der Blattwertskala entsteht. Die reine
   Eigenseiten-Form waere semantisch naeher am Ziel ("baue DEIN Brett"),
   erzeugt aber einen Offset. Vor dem Bau zu entscheiden, nicht im Bau.
2. **`SCALE` des Terms -- AUSGERECHNET 2026-08-24, nicht mehr offen in der
   Groessenordnung.** Die naheliegende Analogie zu `FLOOR_SHAPING_SCALE`
   (50,0) ist zu verwerfen, und zwar aus einem Grund, der beim Nachrechnen
   des Floor-Terms selbst aufgefallen ist (eigene Prereg:
   `PREREG_floor_shaping_scale.md`).

   Der Floor-Term nutzt Nenner 50 fuer einen Zaehler, der nur ueber
   [−10, +10] laeuft. Sein maximales `tanh`-Argument ist damit 0,2, die
   `tanh` weicht dort um **1,3 %** von der Geraden ab -- **sie ist
   dekorativ, der Term ist faktisch linear.** Maximaler Blattwert-Shift:
   **0,059** auf der [0,1]-Skala.

   Fuer B1 laeuft der Zaehler nur ueber **0 bis 2** (Anzahl gestarteter
   langer Reihen, Differenzform also [−2, +2]). Mit Nenner 50:

   | | max. Argument | max. Shift bei `W = 0,3` |
   |---|---|---|
   | Floor-Term (Bestand) | 0,200 | 0,059 |
   | **B1 mit `SCALE = 50`** | **0,040** | **0,012** |

   Also **fuenfmal schwaecher als der Floor-Term**, und noch tiefer im
   linearen Zipfel. Das ist mit hoher Wahrscheinlichkeit zu wenig, um eine
   Rangfolge zu kippen.

   **Was daraus folgt, ist aber KEINE fertige Zahl.** Der Floor-Praezedenzfall
   zeigt, dass ein Term dieser Groessenordnung reichen KANN, wenn er nur
   Vorzeichen setzt (11,25 pp aus einem Shift von maximal 0,059, und der
   W-Sweep war zweimal H0 -- die Groesse traegt dort nachweislich nicht).
   Ob B1 einen groesseren Shift braucht oder ebenfalls nur ein Vorzeichen,
   ist offen. Vorschlag zur Entscheidung: `SCALE` so waehlen, dass der
   maximale Shift dem Floor-Term entspricht (also `SCALE ≈ 10` bei
   `W = 0,3`, macht max. Argument 0,2 und Shift 0,059) -- gleiche
   Groessenordnung wie der einzige Term, der in diesem Projekt
   nachweislich wirkt. Zu bestaetigen, nicht gesetzt.
3. **Reihenfolge gegenueber den anderen offenen Straengen** (R5-Teil-B,
   Seeding-Dosis, UVFA, sigma-Kopf-Ziel aus
   `PREREG_saturating_score_utility.md` par.3a) -- alle weiterhin
   Nutzer-Entscheid, keine Prioritaet impliziert.
