<!-- STATUS: OFFEN | Frage: Verschwinden lange Musterreihen (5/6) schon im rohen Policy-Prior, oder erst in der Suche -- und laesst sich ihre verzoegerte Auszahlung als zusaetzliches Signal sichtbar machen, ohne den Kredit-Horizont-Weg zu wiederholen? | Beleg: par.2 (Zweig-A-Diagnose) GEFAHREN 2026-08-24 (long_row_prior_gate.json, 260 qualifizierende Netz-Stellungen + 260 Heuristik-Kontrast, sims=200): roher Prior lang/kurz-Verhaeltnis 0,221 (Netz) bzw. 0,210 (Heuristik) -- FAST IDENTISCH --, Suche bewegt es kaum (Delta <=0,006 Netz). Verdikt: Signal fehlt BEREITS im Prior (moderat, nicht extrem wie beim Floor-Ziel) -> Zweig B2 (Label/Training) rueckt vor, B1 (Suchseitig) bleibt ein billiger Versuch mit gedaempfter Erwartung. par.3 (B1/B2-Bau) bleibt Nutzer-Entscheid nach par.7, nichts gebaut. Anlass: Reihen-Sonde (STATUS 2026-08-23/24) zeigt eine flache ~55,5-%-Kurzreihen-Praeferenz, die NICHT vom Heuristik-Lehrer geerbt ist; Legalitaets-Stufe zeigt, dass 54 % der verpassten Spalten-Vollendungen an "Musterreihe noch nicht voll" scheitern -- der Engpass liegt upstream in der Draft-Wahl, nicht am Spaltenende. -->

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

**Zweiter Befund, nicht vorregistriert, aber auffaellig:** das
Lang/Kurz-Verhaeltnis ist bei Netz (0,221) und Heuristik (0,210) FAST
IDENTISCH. Das ist eine andere Grundgesamtheit als die flache
55,5-56,1-%-Kurzreihen-Praeferenz aus `row_preference_probe.py` (die ALLE
Draft-Entscheidungen zaehlt, nicht nur Fortsetzungen einer bereits
begonnenen langen Reihe) -- dieser Zuschnitt misst eine ENGERE, spezifischere
Entscheidung ("die Reihe steht schon, mache ich weiter oder nicht"), und
dort unterscheiden sich Netz und Lehrer kaum. Das relativiert nicht den
Reihen-Sonden-Befund (andere Entscheidungsklasse), zeigt aber: nicht jede
Auspraegung der Kurzreihen-Neigung ist netz-spezifisch -- diese hier koennte
strukturell im Spiel selbst liegen (kurze Reihen sind schneller/sicherer
zu vollenden, unabhaengig vom Agenten) statt gelernt/verlernt zu sein.

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
