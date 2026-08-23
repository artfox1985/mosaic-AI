<!-- STATUS: OFFEN | Frage: Verbessert ein tieferer Bootstrap-Horizont (3 statt 2) das Value-Ziel -- und ist der zweite Rollout je Uebergang bezahlbar? | Beleg: **OFFEN, vorregistriert 2026-08-09** (Nutzer-Auftrag). Nur beim v22-Generierungsstart aenderbar (Horizont steckt in den Records, nicht im Cache-Key); Stufe 1 = Kostengate <= +25% Self-Play-Zeit, Stufe 2 = Arme auf identischen Partien via mehrfach geschriebener Labels. Nachtrag 2026-08-23: NEUER ANLASS (Vollendungs-Strukturbefund; Bias nicht geerbt, Verdacht Kredit-Horizont) + Nutzer-Vorschlag rundenabhaengiger Horizont (Ziele bis zum R5-Anker statt fester Tiefe) als dritter Arm-Kandidat; Stufe 0 (Label-Diagnose ohne Training, Nutzer-Freigabe) registriert und beauftragt -->

# Vorregistrierung: Bootstrap-Horizont (2 vs 3) -- Option fuer den v22-Zuschnitt

**Angelegt 2026-08-09, VOR jeder Messung und VOR dem v22-Self-Play.**
Nutzer-Auftrag: *"takte es ein"*, nach der Feststellung, dass der
Horizont nur beim Erzeugen neuer Partien ueberhaupt aenderbar ist.

## Warum der Horizont nur JETZT aenderbar ist

`BOOTSTRAP_HORIZON_ROUNDS = 2` liegt in
`engine/src/round_transition_deep.rs:168` (Stand 2026-08-21; bei
Registrierung Zeile 153), ist also **engine-seitig** und
wird beim Self-Play in die Records geschrieben. Er steckt **nicht** im
Cache-Schluessel (`str(files)+INPUT_SIZE+NUM_ACTIONS+VALUE_SCHEMA_VERSION+
POLICY_TARGET_SHARPEN_EXPONENT+TD_LAMBDA+...`) -- zwei Konsequenzen:

1. Auf einem bestehenden Fenster ist er **nicht sweepbar**. Eine Aenderung
   verlangt NEUES Self-Play.
2. **Fussangel**: wer die Konstante aendert, ohne neu zu generieren,
   bekommt stillschweigend den alten Cache und merkt nichts. Gehoert in
   die geltenden Regeln.

Damit ist der v22-Generierungsstart der einzige Zeitpunkt dieser
Generation, an dem die Frage ohne zusaetzliche Generierungskosten
beantwortbar ist -- danach ist das Fenster geschrieben.

## Warum die Frage heute mehr Gewicht hat als beim Parken

Der Horizont wurde in der v12-Aera geparkt ("teuer, Noise-Floor stuetzt
2"). Damals lief `rtv` parallel und teilte die Arbeit. Seit `nortv`
(v13-Champion) ist der TD-Bootstrap das **einzige** Mittel, das die
Fabrik-Neubefuellung mittelt -- der Zufallsknoten, den der Nutzer als die
stark zufaellige Komponente benannt hat. Die Parkbegruendung ist also
schwaecher geworden, ohne dass es nachgezogen wurde.

## Das Problem des rotierenden Fensters

v22 hat 12.000 neue von 29.450 Partien, in der Value-Klasse 8.000 von
23.650. Uebernommene Partien tragen ihre Labels mit dem ALTEN Horizont
fuer immer. Ein "v22 mit Horizont 3" haette also nur ~34% behandelte
Value-Labels -- konfundiert, und ein Nullergebnis waere nicht von "Dosis
zu klein" zu unterscheiden. Genau die Falle, die heute schon bei λ ueber
die Aussagekraft entschied.

## Zuschnitt: BEIDE Labels mitschreiben, dann zwei Arme auf identischen Partien

Waehrend der v22-Generierung wird je Rundenuebergang der Bootstrap-Wert
fuer Horizont 2 **und** Horizont 3 in denselben Record geschrieben. Dann:

- ein Cache (Schema-Bump, neues Feld), **zwei Trainings-Arme**, die sich
  ausschliesslich darin unterscheiden, welches Feld sie als Value-Ziel
  lesen;
- die uebernommenen Alt-Partien sind in BEIDEN Armen identisch (Horizont
  2, unveraenderbar) -- die Differenz zwischen den Armen ist damit
  **exakt** der Horizont auf dem neuen Drittel.

Das behebt die Konfundierung, nicht die Verduennung: der Effekt bleibt
auf ein Drittel der Value-Labels beschraenkt. **Vorab festgehalten**: ein
H0 ist deshalb ein SCHWACHER Beleg gegen den Horizont, kein starker. Wer
ihn spaeter als "Horizont 3 widerlegt" zitiert, zitiert falsch.

## Stufe 1 (GATE, vor allem anderen): Kosten des zweiten Rollouts

Der Bootstrap ist ein Netz-Rollout ueber N Runden, ~4x je Partie. Der
rtv-Praezedenzfall zeigt, dass Rollouts teuer werden koennen: 24 Samples
kosteten **81% der Self-Play-Zeit**. Ein zweiter Rollout je Uebergang ist
also nicht selbstverstaendlich billig -- das wird GEMESSEN, nicht
geschaetzt: Self-Play-Zeit je Partie mit einem Rollout gegen zwei
(kleine Stichprobe, ~50 Partien, gleicher Seed).

**Entscheidungsregeln (vorab):**
1. Aufschlag **<= +25%** Self-Play-Zeit ⇒ Stufe 2 wird gefahren.
2. Aufschlag **> +25%** ⇒ **verworfen**, ohne Rueckfrage. Begruendung: bei
   12.000 Partien und ~10h Generierung ist mehr als ein Viertel
   Aufschlag fuer eine Frage, deren Effekt ohnehin auf ein Drittel der
   Labels verduennt ist, nicht vertretbar. Der Nutzer hat diese
   Verwerfungs-Option ausdruecklich verlangt.
3. Der Horizont-3-Rollout darf die Horizont-2-Werte **nicht** veraendern
   (Paritaets-Nachweis am Label: dieselben Partien, Horizont-2-Feld
   bit-identisch zum Einzel-Rollout-Lauf). Sonst ist der Vergleich
   wertlos.

## Stufe 2 (nur nach Stufe 1): zwei Arme

Training beider Arme mit identischem Rezept, Fenster und Seed; Gating
jedes Arms gegen den dann amtierenden Champion (Standard-SPRT, 400 Sims,
Block-Ebene, Fruehstopp-Replikationsregel).

- **Ein Arm gewinnt** ⇒ dieser Horizont wird Standard fuer kuenftige
  Generationen. Hinweis fuer die Umsetzung: die Umstellung wirkt nur auf
  NEUE Partien, das Fenster laeuft also ueber ~3 Generationen hinweg
  gemischt -- das ist dokumentiert und kein Fehler.
- **Beide H0** ⇒ Horizont 2 bleibt, Frage fuer die Aera geschlossen, mit
  dem Verduennungs-Vorbehalt oben.

## Nicht Teil davon

- Kein Sweep weiterer Horizonte (4+). Jeder zusaetzliche Wert kostet
  einen weiteren Rollout je Uebergang.
- Keine Aenderung an `TD_LAMBDA` (entschieden: Sweep empfahl 0,7, die
  Arena verwarf es 30:70, λ=0,5 bleibt).
- Keine Aenderung am v22-Fenster-Zuschnitt selbst (`PREREG_v22_window.md`
  bleibt gueltig; dieses Dokument ergaenzt nur eine Label-Option).

## Nachtrag 2026-08-21: zwei Umstaende haben sich veraendert, die Prereg bleibt scharf

1. **Regel 3 der Stufe 1 ist erstmals realistisch fuehrbar.** Der
   Paritaets-Nachweis (Horizont-2-Feld bit-identisch zum Einzel-Rollout)
   waere an den Task-#71-Wall-Clock-Not-Deckeln in
   `round_transition_deep.rs` gescheitert -- genau die Divergenzquelle,
   die das Async-Gate-B aufgedeckt hat. Seit
   `PREREG_deterministic_labels.md` (ENTSCHIEDEN 2026-08-14: Not-Deckel
   degradieren deterministisch, 1956/1956 Records byte-identisch unter
   kuenstlichem CPU-Stress) ist dieser Blocker weg.
2. **Die Verduennungsrechnung haengt an EINER offenen Zuschnitts-Frage
   (praezisiert nach Nutzer-Rueckfrage 2026-08-21).** Bleibt das
   v22-Fenster exakt der registrierte Zuschnitt (nur wdl-Rotations-
   klassen), gilt ~34 % unveraendert -- die seit dem 08.08. entstandenen
   Lehr-Korpora (Ownership 8.000, Asym 16.000) tauchen darin nicht auf.
   NUR falls das heutige Asym-Arm-Rezept (par.9 dort: v21-Fenster PLUS
   Lehr-Korpus) bis zum v22-Training uebertragen wird, waechst der
   Value-Nenner und der behandelte Anteil faellt Richtung ~20 % -- dann
   wird der Vorbehalt "H0 ist ein schwacher Beleg" entsprechend
   staerker. Die round5-Fix-Grenze konfundiert den A/B dagegen NICHT
   (Altpartien liegen in beiden Armen identisch); sie macht die
   Alt-Labels nur heterogener, als gemeinsames Rauschen beider Arme.

Der Ausfuehrungszeitpunkt ist unveraendert der v22-Generierungsstart --
und der liegt laut Fahrplan NACH dem plattenbewussten Modell (erst
Lehr-Korpora/Asym-Curriculum, dann Self-Plays). Ein Wecker dafuer steht
jetzt direkt im Halde-Kasten von `PREREG_v22_window.md`.

## Nachtrag 2026-08-23: neuer Anlass (Vollendungs-Strukturbefund) + Nutzer-Vorschlag rundenabhaengiger Horizont

**Neuer Anlass, der dieser Prereg deutlich mehr Gewicht gibt** (Kette in
evaluations/STATUS.md, STAND 2026-08-23, mit Artefakten): der Champion
vollendet keine Brett-Spalten (0,10/Partie, plattenunabhaengig; 0,55
Hoehe-5-Spalten je Partie bleiben stehen), meidet die langen
Musterreihen 5/6 FLACH ueber alle Runden -- waehrend das
Heuristik-Selfplay (der Abstammungs-Lehrer) spaet auf lange Reihen
umschwenkt. Der Bias ist also NICHT geerbt, sondern im Training
verloren gegangen. Verdachtspunkt (Herleitung, ungemessen): die
verzoegerte Auszahlung frueher Langreihen-Investitionen faellt aus dem
Kredit-Horizont der Value-Ziele.

**Code-Praezisierung dazu (2026-08-23 verifiziert):** der Horizont
schneidet zum NETZ-Leaf-Eval ab (Modulkommentar zu
BOOTSTRAP_HORIZON_ROUNDS: "bevor per net_leaf_eval direkt bewertet
wird, statt bis zum echten Spielende zu rekursieren"); der Uebergang
R4->R5 laeuft bereits ueber den EXAKTEN Freebie
(self_play.rs:2898, exact_round5_outcome), Runde 5 wird nicht
gelabelt. Folge: SPAETE Ziele reichen faktisch schon ans echte Ende;
die Beschneidung beisst FRUEH -- R1/R2-Ziele enden nach zwei Runden im
Netz-Eval von R3/R4, und genau dort muesste die Auszahlung frueher
Reihe-5/6-Fuetterung durch einen Value-Kopf, der Spaltenwert nie
gelernt hat (Sibling-/Kalibrierungs-Befunde).

**Nutzer-Vorschlag (2026-08-23, "der bootstrap horizon kann ja mit
jeder runde kleiner werden"):** rundenabhaengiger Horizont als
dritter Arm-Kandidat -- praktisch gelesen als "Ziele reichen immer
bis zu einem festen ANKER-Zeitpunkt (z. B. Runde-5-Start mit exaktem
Freebie) statt fester Tiefe": R1 saehe dann 4 Runden weit, R3 zwei --
der Horizont schrumpft je Runde, und KEIN Ziel endet mehr in einem
Netz-Eval mitten im Spiel. Passt in den bestehenden Zuschnitt (beide
-- bzw. dann drei -- Labels beim v22-Self-Play mitschreiben, Stufe-1-
Kostengate gilt je zusaetzlichem Rollout; die tiefen fruehen Rollouts
sind der Kostentreiber und genau das, was Stufe 1 beziffern muss).
Arm-Auswahl (2v3 vs. rundenabhaengig vs. beides) = Nutzer-Entscheid
beim v22-Start; diese Prereg bleibt der registrierte Ort dafuer.

## Stufe 0 (NEU, Nutzer-Freigabe 2026-08-23 "im kleinen testen/debuggen"): Label-Diagnose OHNE Training

Vor jedem v22-Commitment eine reine Diagnose-Sonde, kein Korpus, kein
Training:

1. **Bau (additiv):** eine Probe-Funktion, die fuer einen uebergebenen
   Zustand BEIDE Label-Varianten berechnet -- (a) Bestand: Horizont 2,
   Abschluss per net_leaf_eval; (b) Anker-Variante: Rollout bis zum
   Runde-5-Start, Abschluss per exact_round5_outcome-Freebie. KEINE
   Aenderung an Records/Cache/Selbstspiel-Pfad; eigenes Werkzeug nach
   Sonden-Muster.
2. **Messung:** 200-300 Zustaende aus VORHANDENEN fertigen Partien
   (Arena-/Korpus-Records; echter Endausgang bekannt), stratifiziert
   nach Runde (Schwerpunkt R1-R2) und Spalten-/Langreihen-Fortschritt.
   Ausgewiesen: (i) Label-Divergenz nach Runde x Fortschritt, (ii)
   Korrelation beider Varianten mit dem ECHTEN Endresultat, gesamt und
   auf den kritischen Zellen (frueh + hoher Fortschritt), (iii)
   Rechenzeit je Anker-Label (Kostengate-Vorschau: der tiefe fruehe
   Rollout ist der Treiber).
3. **Lesart VORAB:** die Anker-Variante qualifiziert sich fuer einen
   v22-Arm, wenn sie auf den kritischen fruehen Zustaenden besser mit
   dem Endresultat korreliert UND die Kosten je Label ein
   Stufe-1-Bestehen plausibel machen; andernfalls ist der
   Kredit-Horizont-Verdacht geschwaecht und der klassische 2v3-Arm
   bleibt allein. Start nach Abschluss des laufenden
   Welle-3-Engine-Bauslots (Cargo-/Lastkonflikt vermeiden).
