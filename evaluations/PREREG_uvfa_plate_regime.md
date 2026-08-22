<!-- STATUS: OFFEN | Frage: Lernt das Netz SELEKTIVEN Plattenbau, wenn das Bau-Regime als NETZ-EINGABE konditioniert wird (UVFA-Muster: Zwangsseite=1/frei=0 auf dem vorhandenen Asym-Korpus), statt als unsichtbarer Kontext -- und wird das Flag zur Spielzeit ein tragfaehiger Stil-Regler? | Beleg: ENTWURF 2026-08-22, nichts gebaut. Anlass: Asym-Kampagne durchgemessen (par.14/15: kein Signal, kein Schaden) PLUS Klon-Befund par.16 (One-Hot-Klonen war implizit im S-Training, druckte sich nicht aus). Primaerarm UVFA; Alternative Orakel-Action-Labels (gedaempft); Begleitoption Ownership-Gewicht (zweifach vorbelastet). Baustein-Abhaengigkeit: additiver Input-Mechanismus aus PREREG_stack_top_feature.md par.6 Punkt 2. -->

# PREREG-SKELETT: Platten-Regime als Netz-Eingabe (UVFA) -- der Policy-Seiten-Zuschnitt

Stand **2026-08-22. ENTWURF, nichts gebaut, alles in Plan-Zeitform.**
Umfang, Arm-Auswahl und Startzeitpunkt sind Nutzer-Entscheid (par.7).

## par.1 Anlass: die gemessene Sackgasse, praezise

Vier Befunde, alle registriert, zusammen ergeben sie die Diagnose:

1. **Der Prior will laengst bauen** (4,91x Gleichverteilungsmasse auf dem
   Bauzug, 129/130 vorn; PREREG_corpus_distillation) -- ueberstimmt wird
   er vom **Wert-Backup**.
2. **Die Wertseite ist durchgemessen negativ**: Ownership-Verbraucher
   (alle Formen), Zielwechsel/Kalibrierungen, und zuletzt das
   asymmetrische Value-Curriculum (kein Signal, par.14/15 dort).
3. **Naives Policy-Klonen ist zweifach leer gelaufen**: implizit im
   S-Training (~144k One-Hot-Bauer-Ziele, par.16 dort) und in der
   Block-H-Destillation.
4. **Strukturgrund**: die Trainingsdaten tragen widerspruechliche Ziele
   auf denselben Brettmerkmalen -- das Netz sieht NICHT, welche Seite im
   Bau-Regime war (par.4(2) der Asym-Prereg). Ein Mittelwert aus "bau"
   und "bau nicht" ist "bau nicht", weil die freie Seite plus das
   restliche Fenster die Mehrheit stellt.

**Warum weiter k1 und nicht der Spezialfelder-Posten (Nutzer-
Priorisierung 2026-08-22):** die -11,7 Punkte der Spezialfelder gelten
NUR bei aktiver Platte 6 (3/8-Chance); der Spaltenwert liegt dagegen
BEDINGUNGSLOS im Spielfluss (21 Platzierungspunkte je voller Spalte in
jeder Partie), plus 7 bei aktiver k1-Platte, plus die registrierte
k5-Verstaerkung (Eckplatten = aeussere Spaltenpaare, k5 und k1 nicht
wechselseitig ausgeschlossen, staerkste Bauer-Uebernahme +4,86;
PREREG_provocation par.20). k1 bleibt damit der fundamentale Hebel
dieser Prereg; das geparkte stack_top/B1-Paket bleibt nachrangig.

Befund 4 ist der einzige, der einen unversuchten, gezielten Hebel hat:
**mach das Regime zur Eingabe.** Genau das ist die UVFA-Idee aus
DOSSIER_ownership_head Abschnitt 8; par.8 der Asym-Prereg hat das
dynamische Curriculum seinerzeit NUR deshalb verworfen, weil der
Armparameter nicht Eingabe war ("tragfaehig waere es erst, wenn der
Armparameter EINGABE ist") -- diese Bedingung wird hier erfuellt.

## par.2 Primaerarm UVFA: Zuschnitt

- **Eingabe**: EIN zusaetzliches Flat-Merkmal `plate_regime` am Ende des
  Vektors (INPUT_SIZE 708 -> 709), Wert 1.0 = "dieser Zustand gehoert
  der Bau-Regime-Seite", sonst 0.0. Kodierung ego-perspektivisch: 1.0
  genau dann, wenn `state.current_player` die Zwangsseite der Partie
  ist (Quelle: `data/asym_corpus/zwangsseiten_map.txt`); ALLE Zustaende
  anderer Korpora tragen 0.0.
- **Baustein-Abhaengigkeit (geteilt, nicht doppelt bauen)**: der
  additive Input-Mechanismus ist bereits in `PREREG_stack_top_feature.md`
  par.6 Punkt 2 registriert (features_for_layout kuerzt auf die vom
  MODELL deklarierte Laenge; nur kuerzen, nie auffuellen) -- er wird
  HIER zuerst gebraucht und dient danach beiden Preregs. 708er-Bestand
  bleibt byte-identisch ladbar (Nutzer-Anforderung Additivitaet).
- **Training**: Standardrezept, Warm Start Champion, dasselbe Fenster
  wie die Asym-Arme (b18-Regex, Asym-Korpus policy-tragend); Warmstart
  der neuen Eingabespalte null-initialisiert (head_warmstart-Muster:
  das Netz ist im ersten Schritt exakt das alte). Der ASYM-KORPUS IST
  DER TRAININGSINPUT -- er bleibt bis zur Entscheidung dieses Zuschnitts
  lokal (Nutzer-Frage 2026-08-22).
- **Spielzeit**: Laufzeit-Knopf (Name beim Bau, Registry-Pflicht), der
  das Flag fuer die EIGENE Seite setzt -- der erhoffte Stil-Regler
  "plattenbewusst". Default aus = 0.0 = Bestandsverhalten.

## par.3 Messanordnung und VORAB-ERFOLGSREGEL (Entwurf, vor Baubeginn zu fixieren)

1. **Regressions-Tor (Flag aus)**: Arena gegen den Champion auf den 407
   Kampagnen-Seeds, Flag=0 -- darf nicht signifikant verlieren
   (Block-Ebene). Erwartung: nahe Paritaet (null-initialisierte Spalte).
2. **Wirkungs-Messung (Flag an, eigene Seite)**: dieselben 407 Seeds.
   Erfolgsregel WOERTLICH wie par.7 der Asym-Prereg: k1-Rate auf
   k1-aktiven Partien **>= 30 % Ziel / >= 22 % Signal / < 22 % kein
   Signal** (Grundrate 12,8 % = 20/156, par.14 dort), UND kein
   signifikanter Siegverlust gegen den Flag=0-Lauf auf denselben Seeds.
   Ein Plattenzuwachs, der Siege kostet, ist KEIN Erfolg
   (Leitstern-Klausel).
3. **Mechanik-Sonde**: `tools/probes/asym_value_sibling_check.py` auf
   demselben Stellungs-Dump, UVFA-Netz mit Flag 1 gegen Flag 0 --
   erstmals eine WITHIN-Modell-Differenz statt S gegen N.

## par.4 Alternative B: Orakel-Action-Labels (AZAL-Strang, registriert, gedaempft)

Tiefensuche-/Solver-abgeleitete Policy-Ziele auf plattenrelevanten
Zustaenden statt Heuristik-Klonen. VORAB festgehalten, warum die
Erwartung gedaempft ist: par.16-Befund -- Klon-Ziele druckten sich nicht
aus, und das Wert-Veto in der Suche bleibt unbehandelt. Sinnvoll erst,
falls UVFA zeigt, dass das Regime-Signal ankommt, aber die Zugauswahl
zu grob bleibt. Kein eigener Zuschnitt in diesem Skelett.

## par.5 Begleitoption: Ownership-Gewicht > 0 (dritter Anlauf, ausgewiesen vorbelastet)

Der vorhandene Ownership-Kopf als Repraesentations-Former (Feld-Labels
waeren auf dem Asym-Korpus erstmals asymmetrisch). ZWEIFACH leer
gelaufen (b18-b24-Kampagne mit Gewicht 1,0; Block H ohne Beitrag) --
wird NUR als optionaler zweiter Faktor eines UVFA-Arms gefuehrt, nie
als eigener Arm, und nur wenn der Nutzer es beim Start ausdruecklich
freigibt (ein Faktor pro Messung bleibt die Regel; ein kombinierter
Arm braucht den passenden 2x2-Zuschnitt).

## par.6 Kosten (Schaetzung, beim Start nachzurechnen)

Kein neuer Korpus. Engine-Bausteine: Kuerzungs-Mechanismus (dient auch
stack_top), Flag-Durchleitung Self-Play-Records -> Cache (Schema-Bump)
-> Encoder, Laufzeit-Knopf. Training ~6 h je Arm (gemessen 2026-08-21/22
an den Asym-Armen), Arena 2 Laeufe a ~50 min plus Regressions-Tor.

## par.7 OFFENE NUTZER-ENTSCHEIDE (vor Baubeginn)

1. Arm-Auswahl: nur UVFA, oder UVFA + Begleitoption par.5?
2. Reihenfolge gegenueber dem geparkten stack_top/B1-Paket (teilt den
   Kuerzungs-Baustein; gemeinsamer Bau spart den Mechanismus-Aufwand).
3. Bestaetigung der Erfolgsregel par.3 (uebernommen aus Asym-par.7)
   oder Anpassung VOR dem ersten Bau-Commit.
