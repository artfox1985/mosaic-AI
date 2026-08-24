<!-- STATUS: OFFEN | Frage: Verschwinden lange Musterreihen (5/6) schon im rohen Policy-Prior, oder erst in der Suche -- und laesst sich ihre verzoegerte Auszahlung als zusaetzliches Signal sichtbar machen, ohne den Kredit-Horizont-Weg zu wiederholen? | Beleg: par.2 (Prior-Sichtbarkeit) und par.2a (Initiierung gegen Fortsetzung) GEFAHREN 2026-08-24. par.2: Prior lang/kurz 0,221, Suche bewegt es kaum -> Signal fehlt bereits im Prior, B2 rueckt vor. KORREKTUR an par.2: die zweite Spalte war NICHT die Heuristik, sondern derselbe Champion auf heuristik-Stellungen -- die Zahl zeigt Robustheit ueber Zustandsverteilungen, keinen Agentenvergleich. par.2a in drei Stufen: Arena-Log-Anteil zeigte einen R3-Einbruch, der sich als BELEGUNGS-KONFUNDIERER erwies; die Log-Rekonstruktion dagegen scheiterte am eigenen Selbsttest (233/407 Partien), Ursache round_end.rs:87 process_unplaceable_rows leert Reihen ohne Logzeile; die Korpus-Fassung entkonfundiert: Policy-Masse auf "beginne eine leere lange Reihe", bedingt auf Gelegenheit, Netz 11,5 % gegen Heuristik 25,2 % -- Faktor ~3, FLACH ueber R1-4, Konvergenz nur in R5. Damit ist die Luecke in der INITIIERUNG lokalisiert, nicht in der Fortsetzung -- ein Fortschritts-Shaping (B1) traefe die falsche Aktionsklasse. par.3 bleibt Nutzer-Entscheid, nichts gebaut. Anlass: Reihen-Sonde (STATUS 2026-08-23/24) plus Legalitaets-Stufe (54 % der verpassten Vollendungen scheitern an "Musterreihe noch nicht voll") -->

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

### B1 -- Such-seitiger Shaping-Term (additiv, Netz-Pfad, SearchConfig-Kandidat)

Analog `floor_shaping_weight` (par.1 Punkt 7): ein kleiner additiver
Blattwert-Korrekturterm, der Fortschritt in Reihe 5/6 (Anzahl belegter
Slots relativ zur Kapazitaet) fuer den ZIEHENDEN Spieler leicht
aufwertet. Eckpunkte fuer den Bau (bei Freigabe):

- **Codepfad:** neu, im Netz-Suchpfad (`net_mcts.rs`), NICHT
  `wertung_progress`/`mcts.rs` (par.1 Punkt 6). Default-Gewicht 0 =
  byte-identisches Bestandsverhalten (Paritaets-Gate wie ueblich).
- **Kapselungs-Anschluss:** dies waere der ZWEITE Knopf, der ins
  `SearchConfig`-Geruest wandert (nach `MOSAIC_IMPLICIT_MINIMAX_A`,
  `PREREG_agent_encapsulation.md` par.4) -- direkt als SearchConfig-Feld
  bauen statt zuerst als Env-Knopf und spaeter migrieren, spart eine
  Runde.
- **Messkette, exakt das Muster von heute (Minimax-Knopf,
  `PREREG_implicit_minimax_backup.md`):**
  1. Vorzeichen-Sonde auf einer kleinen Partienzahl (Wirkung
     ja/nein, grobe Richtung).
  2. Paired Arena **NETZ-GEGEN-NETZ** (nicht zuerst gegen die
     Heuristik -- die Gegnerspezifitaets-Lehre vom 2026-08-23/24 gilt
     hier von Anfang an), 407 Kampagnen-Seeds, `--log-games`.
  3. Ausgewiesen: Siege (Block-Ebene), k1-Rate, UND die
     Reihenwahl-Verteilung selbst (mit dem `row_preference_probe.py`-
     Fix aus Punkt 2, siehe par.5) -- der direkte Wirkungsnachweis auf
     das Zielverhalten, nicht nur auf die Siegquote.
- **Vorab-Lesart:** primaer kein Staerkeverlust; eine Verschiebung der
  Reihenwahl-Verteilung Richtung Reihe 5/6 ist der Bonus-Befund, der
  die Kausalkette schliesst. Ein Sweep-Kandidat wie bei Floor-Shaping
  wird NICHT vorab erwartet (Praezedenz: Schalter, kein Regler) --
  sollte sich das wiederholen, ist EIN Wert ausreichend zu testen.

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

1. **par.2 zuerst, immer** -- billig, liefert die Weichenstellung
   zwischen B1 und B2, blockt nichts anderes.
2. **B1 nur nach par.2**, es sei denn der Nutzer gibt es unabhaengig
   vom Diagnose-Ausgang frei (es ist billig genug, um auch "auf
   Verdacht" gebaut zu werden -- das ist ein Abwaegungs-Punkt fuer
   par.7, keine Vorfestlegung).
3. **B2 fruehestens nach B1**, eigener Zuschnitt, eigene
   Nutzer-Freigabe.

## par.5 Beruehrungspunkte mit offenen Nebenpunkten

- Der Fix von `tools/probes/row_preference_probe.py:190-198`
  (Seiten-Labelling in `imm_netvnet`, aus der Parallelsitzung
  gemeldet, noch nicht erledigt) sollte VOR der B1-Arena stehen, weil
  die Reihenwahl-Verteilung dort mit ausgewiesen wird -- sonst mischt
  das Instrument wieder zwei Agenten.
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

1. Par.2 (Diagnose) sofort freigeben, oder als naechster Schritt einer
   kommenden Sitzung parken?
2. Soll B1 unabhaengig vom Diagnose-Ausgang gebaut werden (billig genug,
   klarer Praezedenzfall), oder strikt gated durch par.2s Ergebnis?
3. Stichprobengroesse/-quellen fuer par.2 (Vorschlag: 150-250 Zustaende,
   analog zur Groessenordnung des Vierer-Vergleichs) -- zu bestaetigen.
4. Reihenfolge gegenueber den anderen offenen Straengen (R5-Teil-B,
   Seeding-Dosis, UVFA, restliche Kapselungs-Wellen) -- alle weiterhin
   Nutzer-Entscheid, keine Prioritaet impliziert.
