# Externe Recherche: Suchalgorithmus-Alternativen

**Datum:** 2026-08-22
**Auftrag:** Tiefe externe Web-/Literatur-Recherche ausschliesslich zu SUCH-Alternativen
fuer unsere Spielklasse. Kein Code geaendert. Ein Schwester-Agent deckt Training/Curriculum ab.
**Bearbeiter:** Recherche-Agent (Sonnet/Opus-Klasse), nur Web + lesende Repo-Pruefung.

## Belegstufen (durchgehend verwendet)

Jede Aussage traegt eine der drei Marken:

- **[ENGINE]** – in einer real spielenden, gemessenen Engine belegt (Turnier, Ratingliste,
  Release-Notes mit Elo-Zahl).
- **[PAPER]** – Paper-Demo: kontrolliertes Experiment, oft Kleinspiele oder Benchmarks,
  keine Turnier-Engine.
- **[EINSCHAETZUNG]** – meine Ableitung auf unsere Lage. Ungeprueft, keine Messung.

Zusaetzlich **[REPO/geprueft]** fuer Stellen, die ich in dieser Sitzung im Baum nachgelesen
habe, mit `datei:zeile`.

---

## Ausgangslage (als gegeben uebernommen, plus zwei Repo-Pruefungen)

Uebernommen aus dem Auftrag: 2 Spieler, 5 Runden, ~160 Entscheidungen, 406 Aktions-IDs,
Verzweigung ~10-70, fast vollstaendige Information (4 verdeckte Bonuschips je Runde,
Kuppelstapel-Reihenfolge), Zufallsknoten an Rundenuebergaengen, Gumbel-AlphaZero mit
150-600 Sims, CPU-only via tract, Determinismus-Pflicht, additive Umbauten bevorzugt.

Zwei Punkte habe ich im Baum nachgelesen, weil sie fuer S2/S3/S5 tragend sind:

1. **[REPO/geprueft]** `engine/src/round5.rs:1-52` beschreibt die R5-Suche selbst als
   Expectiminimax mit Alpha-Beta an Entscheidungsknoten und Zufallsknoten dort, wo
   verdeckte Information oeffentlich wird, mit exakter Blattwertung. Der Modulkopf ordnet
   sie ausdruecklich der Ballardschen *-Minimax-Familie zu und notiert, dass INNERHALB
   eines Zufallsknotens NICHT beschnitten wird ("Star1/Star2 waere der Standardweg,
   braucht aber Wertgrenzen je Ausgang und lohnt bei <=4 Ausgaengen nicht").
   `NODE_BUDGET = 200` steht in `round5.rs:88`. Der Kopf nennt zwei gemessene Zahlen, die
   fuer die Empfehlungsmatrix wichtig sind: gegen ein 20.000-Knoten-Orakel trifft Budget
   200 in 81,4 % dieselbe Wahl, das Zwanzigfache 84,8 % – "was den Wert dieser Suche
   traegt, ist die exakte Blattrechnung, nicht das Alpha-Beta darum herum". Und: das
   Netz@400 trifft die Orakel-Wahl in R5 nur zu 51,7 %.
2. **[REPO/geprueft]** `engine/src/column_build.rs:21-30`: eine FRUEHERE Fassung des
   Spaltenbau-Spielers hielt die Ziel-Spalte "ueber mehrere Entscheidungen persistent
   fest" und wurde nach vier vollen 20-Seed-Messungen verworfen – 0,70-2,45 statt 5,95
   vertikale Punkte. Das ist ein hausinterner Negativbefund GEGEN naive Absichts-Bindung
   und faellt in S3 ins Gewicht.

---

## S1. Taxonomie: was ist real im Einsatz, und wie schlaegt es sich bei 150-600 Evals?

### S1.1 Die zwei realen Grossfamilien

**PUCT-MCTS mit Policy+Value-Netz.** AlphaZero/Leela/KataGo/CrazyAra. **[ENGINE]** Leela
Chess Zero baut den Baum ueber die PUCT-Formel und wertet mit einem grossen Netz; die
Engine ist real und in Turnieren gemessen [1]. Charakteristische Staerke/Schwaeche wird in
der Crazyhouse-Arbeit von Czech et al. explizit benannt: Alpha-Beta-Engines sind in
offenen taktischen Stellungen am staerksten, MCTS zeigt das umgekehrte Bild – deutlich
weniger Knotenauswertungen, schwaecher beim schnellen Loesen von Taktik, die nicht schon
der Mustererkennung entspricht, aber "oft besser beim Ausfuehren langfristiger Strategien
und Opfer, weil die Suche von einer nichtlinearen Policy gefuehrt wird" [2] **[ENGINE]**.

**Alpha-Beta mit Netz-Eval (NNUE-Linie).** **[ENGINE]** Stockfish uebernahm NNUE 2020 und
meldete ~100 Elo Gewinn [3]; die Bauform wird ausdruecklich als Hybrid beschrieben, der
ein Netz in eine klassische Engine injiziert und den effizienten Suchalgorithmus behaelt
[4]. Im Shogi gewann YaneuraOu mit NNUE die WCSC29 [5] **[ENGINE]**. Der entscheidende
Punkt ist NICHT "Alpha-Beta schlaegt MCTS", sondern das Kostenprofil: Stockfish
evaluiert nach der in [1] zitierten Zahl rund 1500x mehr Stellungen pro Sekunde als Leela.
NNUE ist inkrementell aktualisierbar; ohne diese Eigenschaft kollabiert der Vorteil.

### S1.2 Weitere Paradigmen, die real Medaillen holen

**Unbounded Best-First Minimax / Descent (Athenan, Cohen-Solal & Cazenave).**
**[PAPER]/[ENGINE-nah]** Descent exploriert Aktionsfolgen bis zu Endzustaenden und lernt
auf dem gesamten Suchbaum statt nur auf der gespielten Zugfolge; im Spiel laeuft Unbounded
Best-First Minimax mit "safe decision". Gegen Polygames (AlphaZero-Reimplementierung)
berichtet die Arbeit +35,8 % Gewinnrate ohne Heuristiken bzw. 60,75 % mit
Verstaerkungsheuristiken, und dass Athenan die 15-Tage-Leistung von Polygames in ~2 Tagen
erreicht [6]. Descent gewann fuenf Goldmedaillen bei der Computer-Olympiade 2020 [7] –
das ist echte Turnierevidenz, aber gegen Olympiade-Feld, nicht gegen Stockfish-Klasse.
Die Folgearbeit "On some improvements to Unbounded Minimax" (2025) misst ueber 22 Spiele
mit 10 s/Zug: Wegnahme von "completion" kostet 5,03 Punkte, Wegnahme der
Transpositionstabellen 4,15, Ersatz der exakten Terminalwertung 13,13 [8] **[PAPER]**.
Die exakte Blattwertung ist also mit weitem Abstand der groesste Einzelposten – dieselbe
Aussage, die unser R5-Modulkopf empirisch macht **[REPO/geprueft, round5.rs:36-45]**.

**Best-First Minimax (Korf & Chickering) / MTD(f).** **[PAPER]** Korf & Chickering
expandieren stets den Randknoten am Ende der Hauptvariante und schlagen auf
Zufallsspielbaeumen sowie in Othello (mit Bills Evaluierungsfunktion) eine effiziente
Alpha-Beta-Implementierung bei gleichem Rechenaufwand [9]. MTD(f) schlaegt NegaScout in
Blattknoten, Gesamtknoten und Laufzeit [10]. Wichtige Relativierung aus derselben
Literatur: Best-First und Depth-First liegen in der Praxis nahe beieinander, und "mehr
Gewinn kommt aus den Alpha-Beta-Erweiterungen als aus dem darunterliegenden Algorithmus"
[10] **[PAPER]**.

**Proof-Number-Varianten.** **[PAPER]** Generalized Proof-Number MCTS (Kowalski, Soemers,
Kosakowski, Winands 2025) baut (Dis-)Proof-Numbers in die UCB1-Selektion ein, fuehrt
Proof-Numbers pro Spieler und verschmilzt das mit Score-Bounded MCTS, sodass obere und
untere SCHRANKEN AUF PUNKTWERTE bewiesen und genutzt werden koennen; die Arbeit meldet
Gewinnraten "im Bereich von 80 %" fuer 8 von 11 getesteten Brettspielen [11]. Die
Punktwert-Schranken sind der fuer uns interessante Teil, weil unser Spiel
punktdifferenzbasiert ist – Grundlage ist Score Bounded MCTS von Cazenave & Saffidine, das
Alpha-Beta-artige Cutoffs in MCTS bringt (angewandt auf Seki in Go und Connect Four) [12]
**[PAPER]**.

**Expectiminimax / *-Minimax.** Siehe S5.

### S1.3 Was ist ueber Staerke pro Rechenbudget belegt – speziell bei wenigen Evals?

Das ist der Kern der Frage, und die Evidenzlage ist duenner als man moechte. Die drei
belastbarsten Datenpunkte:

1. **Rapfi (Gomoku, ICLR-Einreichung 2025).** **[ENGINE]** Das ist der direkteste Beleg
   fuer unsere Lage: CPU-only, kein Beschleuniger, kompaktes Netz mit inkrementellem
   Update, sorgfaeltig getuntes Alpha-Beta. Rapfi wurde Erster unter 520 Gomoku-Agenten
   auf Botzone und gewann GomoCup 2024 gegen 54 Gegner; die Arbeit sagt explizit, dass
   Rapfi "Katagomo, die staerkste quelloffene Gomoku-KI auf AlphaZero-Basis, unter
   begrenzten Rechenressourcen ohne GPU uebertrifft" [13]. Ebenso wichtig ist die
   Ablation, die die Suchwahl an die NETZGROESSE koppelt: "MCTS haengt weniger von der
   Wertgenauigkeit ab, wenn eine starke Policy vorliegt, weshalb das GROESSERE Netz dort
   am besten abschneidet; fuer Alpha-Beta wird ein MITTELGROSSES Modell bevorzugt, bei dem
   die Wertgenauigkeit wesentlich ist" [13] **[ENGINE]**. Und die Begruendung fuer den
   Alpha-Beta-Vorteil ist ausdruecklich die Tiefensuche, die das inkrementelle
   Update-Schema ausnutzt – also die NNUE-Eigenschaft, nicht die Suchform an sich.
2. **Gumbel AlphaZero.** **[PAPER]** Danihelka et al. begruenden den Ansatz genau mit
   unserem Regime: "Bei wenigen Simulationen garantiert PUCT keine Policy-Verbesserung",
   und die Gumbel-Algorithmen "verbessern die bisherige Leistung beim Planen mit wenigen
   Simulationen deutlich" [14]. Das ist die Rechtfertigung des heutigen Pfads.
3. **MiniZero (Wu et al., IEEE ToG).** **[PAPER]** Systematischer Vergleich von AlphaZero,
   MuZero, Gumbel AlphaZero, Gumbel MuZero auf 9x9 Go und 8x8 Othello. Zwei Befunde, die
   der naiven Erwartung widersprechen: bei n=200 schlagen klassisches AlphaZero/MuZero
   ALLE vier Gumbel-Einstellungen; und in Othello ist n=2 fuer die Gumbel-Varianten gleich
   gut oder leicht besser als n=16 [15]. **[EINSCHAETZUNG]** Das heisst nicht, dass Gumbel
   schlecht ist – MiniZero variiert die SELF-PLAY-Simulationszahl, nicht die Spielstaerke
   bei fester Suche. Aber es widerlegt die Vorstellung, mehr Sims seien monoton besser,
   und passt zu unserem Regime, in dem 150-600 die realistische Bandbreite ist.

**Gegenbefund zur Faustregel "MCTS ist bei kleinem Budget besser".** Fuer VANILLA-MCTS mit
Zufalls-Rollouts ist das Gegenteil dokumentiert: in Connect-4 erreicht ein UCT-Agent mit
10.000 Zufallssimulationen nur 19,8 % gegen einen Tiefe-8-Alpha-Beta-Gegner [16]
**[PAPER]**. Das gilt fuer Rollout-MCTS, nicht fuer netzgestuetztes MCTS, ist aber der
Grund, warum die Literatur "MCTS gewinnt bei hoher Verzweigung UND fehlender guter
Evaluierungsfunktion" formuliert – und wir HABEN eine (das Netz plus die exakte
R5-Blattwertung).

**Zwischenfazit S1 [EINSCHAETZUNG].** Fuer unsere Zahlen (Verzweigung 10-70, Eval in
Millisekunden, 150-600 Evals) gilt: Alpha-Beta-Formen holen ihren Vorteil aus BILLIGEN
Evals (NNUE-artig, inkrementell). Bei ~1 ms je Eval sind 600 Evals ~0,6 s; das reicht fuer
ein volles Alpha-Beta bei Verzweigung 30 auf etwa 2-3 Halbzuege plus Zugsortierungsgewinn.
Genau in dieses Fenster faellt unsere R5-Suche mit Budget 200 – und deren gemessene
Orakel-Uebereinstimmung (81,4 % bei 200 vs. 84,8 % bei 4000) sagt, dass zusaetzliche Tiefe
dort wenig traegt **[REPO/geprueft, round5.rs:36-45]**. Ein globaler Alpha-Beta-Ersatz des
Gumbel-Pfads ist daher schlecht motiviert, ein LOKALER Einsatz gut.

---

## S2. Alpha-Beta + Netz fuer unsere Spielklasse

### S2.1 Machbarkeit bei Verzweigung 10-70

**[PAPER]** Die Standardrechnung fuer Alpha-Beta mit perfekter Zugsortierung ist
b^(d/2). Bei b=30 heisst das: Tiefe 4 kostet ~900 Blaetter, Tiefe 6 ~27.000. Bei b=70
kostet Tiefe 4 schon ~4.900. Mit 600 Netz-Evals kommt man ohne inkrementelle Eval also
verlaesslich auf Tiefe 3-4 bei mittlerer Verzweigung, und das auch nur mit guter
Sortierung. **[EINSCHAETZUNG]** Fuer 5 Runden a ~32 Entscheidungen bedeutet Tiefe 4 rund
zwei eigene Zuege Vorausschau – genug fuer lokale Taktik, zu wenig fuer eine
rundenuebergreifende Spaltenabsicht. Alpha-Beta loest unser motivierendes Problem also
NICHT durch Tiefe.

### S2.2 Policy-Prior als Zugsortierung

**[PAPER]** Netze als Move-Ordering-Heuristik sind alt und belegt: die Arbeit "Move
Ordering Using Neural Networks" berichtet 20-50 % Effizienzgewinn, indem Zuege nach der
geschaetzten Wahrscheinlichkeit sortiert werden, der beste zu sein [17]. Die klassische
Reihenfolge in Engines ist Transpositionstabellen-Zug, dann Killer-Zuege, dann History
[18] **[ENGINE]**. **[EINSCHAETZUNG]** Unser Policy-Kopf ist genau das Objekt, das man
dort einsetzt, und wir haben ihn schon; der Prior bietet den Bauzug laut Auftrag mit 4,9x
Masse an – als SORTIERSCHLUESSEL ist eine so klare Praeferenz ideal, denn Alpha-Beta
bestraft eine falsche Sortierung nur mit Zeit, nicht mit einer falschen Antwort. Das ist
der wichtigste strukturelle Unterschied zur MCTS-Nutzung des Priors: dort steuert der
Prior, WELCHE Zuege ueberhaupt gesehen werden, im Alpha-Beta nur, in welcher REIHENFOLGE.

### S2.3 Value-Kopf als Eval

**[ENGINE]** Rapfi zeigt, dass bei Alpha-Beta die WERTGENAUIGKEIT das kritische
Netzattribut ist, waehrend MCTS staerker von der Policy lebt [13]. **[EINSCHAETZUNG]** Das
ist fuer uns eine Warnung: die Projekthistorie (Memory: Round-5-Kopf-Uneinigkeit,
R5-Kalibrierung mit Steigung 0,06-0,09 statt ~1) deutet auf einen in Runde 5 stark
gedaempften Value-Kopf. Ein Alpha-Beta, das genau diesen Kopf als Blattwert nimmt, erbt
die Daempfung ohne Mittelung, die sie kaschiert. Ausserhalb von R5, wo es keine exakte
Blattwertung gibt, ist das ein echtes Risiko.

### S2.4 Belegte Beispiele ausserhalb Schach/Shogi

- **[ENGINE]** Gomoku: Rapfi (siehe oben) [13].
- **[ENGINE]** Backgammon: *-Minimax/Star2 erlaubt "starken Backgammon-Programmen
  volle Tiefe-5-Suchen (statt 3) unter Turnierbedingungen auf normaler Hardware ohne
  riskante Forward-Pruning-Techniken" [19]. Dieselbe Arbeit relativiert aber: "mit
  heutigen ausgefeilten Evaluierungsfunktionen braucht gutes Steinspiel im Backgammon
  keine tiefen Suchen" [19] – ein Satz, der fast woertlich auf unseren R5-Befund passt.
- **[PAPER]** Othello: Best-First Minimax schlaegt Alpha-Beta bei gleichem Aufwand [9].
- **[PAPER]** Breakthrough/Othello/Catch the Lion: MCTS-Minimax-Hybride, siehe S4.

### S2.5 Wann behebt AB die "strategische" Schwaeche von MCTS – und wann versagt es?

**[PAPER]** Die Literatur formuliert das genau ANDERSHERUM als die Frage: Alpha-Beta ist
der TAKTISCHE Reparaturmechanismus, MCTS der strategische. Baier & Winands: "MCTS zeigt in
manchen taktischen Domaenen schwaecheres Spiel als minimax-basierte Suche, teils wegen
ihrer stark selektiven Suche und der MITTELNDEN Wertrueckgabe, die sie anfaellig fuer
Fallen macht" [20]. Die dortige Motivation fuer Hybride ist "die strategische Staerke von
MCTS mit der taktischen Staerke von Minimax zu verbinden" [20]. Und Czech et al. sagen aus
Engine-Sicht dasselbe: MCTS ist "oft besser beim Ausfuehren langfristiger Strategien" [2]
**[ENGINE]**.

**[EINSCHAETZUNG] – und das ist der wichtigste Satz dieses Kapitels:** Unser motivierendes
Problem (mehrrundige Absicht wird weggemittelt) ist in der Literatur NICHT das Problem,
gegen das Alpha-Beta hilft. Alpha-Beta hilft gegen flache Fallen und Zugzwang-Taktik.
Unser Problem ist eine Mischung aus (a) Value-Backup-Mittelung ueber lange, seltene Linien
und (b) Zustandslosigkeit zwischen Zuegen. (a) adressieren S4-Massnahmen direkt, (b) S3.
Ein Alpha-Beta-Umbau wuerde (a) teilweise mitheilen (Minimax mittelt nicht), (b) gar
nicht.

---

## S3. Absichts-/Plan-Persistenz UEBER Zuege hinweg

### S3.1 Tree Reuse – der billigste real belegte Hebel

**[ENGINE]** Tree Reuse ist Standard: Leela macht den gewaehlten Zug zur neuen Wurzel und
loescht den alten Wurzelknoten samt Geschwistern; NPS zaehlt uebernommene Knoten
ausdruecklich NICHT mit [21]. **[PAPER/ENGINE]** Die Crazyhouse-MCGS-Arbeit bringt die
naechste Stufe: Monte-Carlo GRAPH Search statt Baum, "etwa +110 Elo in Crazyhouse", und
sie bezeichnet Subtree-Solving als "obligatorisch ... leicht zu implementieren,
vernachlaessigbare Rechenkosten und erhoeht in Nullsummenspielen meist die Spielstaerke"
[22]. **[PAPER]** Aus dem Video-Game-Testing-Umfeld gibt es eine konkrete Zahl fuer
Standard-Pondering mit Wiederverwendung des Gegnerzug-Teilbaums: Sprung von 54,8 % auf
67,4 % [23]. **[ENGINE]** Transpositionen erhoehen in Schach die ausgewerteten Knoten pro
Sekunde "um Faktor zwei oder mehr" in manchen Stellungen [22].

**Wichtige Einschraenkung fuer UNS [EINSCHAETZUNG]:** Tree Reuse gibt Rechenzeit zurueck,
nicht Absicht. Es macht die Suche nicht "nicht-zustandslos" im gewuenschten Sinn – die
Statistiken des uebernommenen Teilbaums sind dieselben gemittelten Q-Werte, die die
Absicht schon einmal weggemittelt haben. Der Gewinn ist real, aber er greift am falschen
Hebel fuer das motivierende Problem. Zweite Einschraenkung: Gumbel-AlphaZero waehlt an der
Wurzel m Kandidaten per Gumbel-Top-m und verteilt das Budget per Sequential Halving
[14,24]; ein uebernommener Teilbaum bringt ungleiche Vorbesuche mit, was die
Sequential-Halving-Bilanz stoert. Ich habe KEINE Quelle gefunden, die Gumbel-Root-Auswahl
mit Tree Reuse sauber kombiniert – das ist eine echte Luecke in der Literatur, kein
Uebersehen. **[EINSCHAETZUNG]** Praktikabler Ausweg: Teilbaum-Statistiken nur unterhalb
der Wurzel wiederverwenden, die Wurzelphase (Gumbel-Ziehung + Sequential Halving) frisch
rechnen.

### S3.2 Optionen / Makro-Aktionen IN der Baumsuche

**[PAPER]** OptionZero (ICLR 2025) ist der derzeit sauberste Vertreter: ein Options-Netz
sagt kumulative Aktionswahrscheinlichkeiten voraus, die "dominante Option" ist die
laengste Folge mit Produkt > 0,5; der Suchbaum enthaelt Kanten fuer Primitivaktionen UND
Optionen, und die Statistik bleibt konsistent, indem Primitivknoten die Optionsbeitraege
mitfuehren [25]. Ergebnis: 1054,30 % human-normalisierter Mittelwert (Optionslaenge 3)
gegen 922,72 % MuZero-Basis, also +131,58 % [25]. **Die fuer uns entscheidende
Einschraenkung steht in derselben Arbeit:** getestet wurde GridWorld und 26 Atari-Spiele,
Brettspiele nur theoretisch erwaehnt, KEINE empirischen Brettspiel-Ergebnisse; ~75 % der
gelernten Optionen sind blosse Aktionswiederholungen; in 4 von 26 Spielen wurde es
schlechter; und "Spiele mit komplexen Aktionsraeumen oder verwickelten strategischen
Moeglichkeiten zeigen Leistungsabfall, wenn die Optionskombinationen sich vermehren" [25].
**[EINSCHAETZUNG]** Unser Aktionsraum (406 IDs) und unsere Absichten (zwei 6er-Spalten
ueber Runden hinweg) liegen genau in der Zone, vor der die Arbeit warnt. Aktionswiederholung
gibt es bei uns nicht; unsere "Option" waere eine semantische Absicht, keine Zugfolge.

**[PAPER]** Aeltere Linie: O-MCTS waehlt Optionen statt Aktionen und expandiert erst,
wenn das Teilziel erreicht ist; Subgoal-MCTS teilt in Low-Level-Makrosuche und High-Level-
MCTS ueber Makro-Aktionen [26,27]. Alles General-Video-Game-Playing bzw. Navigation, keine
Brettspielbelege.

### S3.3 Was in Engines wirklich Absicht ueber Zuege traegt

**[ENGINE]** In Alpha-Beta-Engines ist Persistenz eingebaut und billig: Transpositionstabelle,
Killer-Zuege, History-Heuristik ueberdauern Iterationen und Zuege und lenken die Sortierung
[18]. **[EINSCHAETZUNG]** Das ist die realste Form von "sticky prior", die ich in der
Literatur finden konnte – eine Sortier-, keine Bewertungs-Persistenz. Ein MCTS-Analogon
waere ein ueber Zuege fortgeschriebener Prior-Bonus fuer Zuege, die zur zuletzt
verfolgten Linie gehoeren.

**[PAPER]** KataGo geht bei der Wurzel-Policy sogar in die GEGENRICHTUNG: Softmax-Temperatur
leicht ueber 1 (1,25 fruehes Spiel, abklingend auf 1,1) als "rueckstellende Kraft Richtung
uniform unter aehnlich bewerteten Zuegen", weil die Policy im Selbstspiel sonst zu scharf
wird [28]. Wer einen Sticky-Prior baut, arbeitet also gegen eine Massnahme, die in einer
starken Engine Elo gebracht hat.

### S3.4 Der hausinterne Negativbefund

**[REPO/geprueft, `engine/src/column_build.rs:21-30`]** Eine feste Bindung der Ziel-Spalte
ueber mehrere Entscheidungen wurde nach vier vollen 20-Seed-Messungen verworfen: 0,70-2,45
statt 5,95 vertikale Punkte, weil "die Bindung der Kosten-Formel genau die
Reaktionsfaehigkeit nahm". **[EINSCHAETZUNG]** Jede S3-Empfehlung muss diesen Befund
respektieren: Absichts-Persistenz darf nicht als HARTE Bindung gebaut werden, sondern nur
als Bewertungs- oder Sortierverschiebung, die ein starker Gegenbefund ueberstimmen kann.

---

## S4. Backup-/Selektionsvarianten gegen das Wegmitteln seltener langer Linien

Dies ist – meine Einschaetzung – das Kapitel mit dem besten Verhaeltnis von Evidenz zu
Umbaukosten fuer unser konkretes Problem.

### S4.1 Implicit Minimax Backups (Lanctot, Winands, Pepels, Sturtevant 2014)

**[PAPER]** Mechanismus, direkt aus dem Paper: neben dem MC-Mittelwert wird pro Knoten ein
zweiter Wert gefuehrt, der per MINIMAX aus den heuristischen Blattbewertungen
zurueckgegeben wird; die Selektion nutzt

`Q_IM(s,a) = (1 - alpha) * (r_{s,a} / n_{s,a}) + alpha * v_{s,a}`

wobei `v` der implizite Minimax-Wert ist [29]. Ergebnisse: Kalah Vorteil fuer
alpha in [0,1; 0,5]; Breakthrough mit einfacher Eval bestes alpha in [0,1; 0,6], dort
82,3 % gegen den Basis-Agenten; Breakthrough mit ausgefeilter Eval optimal bei
alpha in [0,5; 0,6]; Lines of Action Vorteil bei alpha in [0,1; 0,5], und "bei alpha=0,2
gibt es keinen statistisch signifikanten Fall, in dem implizite Minimax-Backups schaden"
[29]. Negativbefund derselben Arbeit: kein signifikanter Gewinn in Chinese Checkers und
Hearts; die Autoren erklaeren den Wirkmechanismus mit "kurzfristiger taktischer
Information, die lange Playouts nicht einfangen" [29].

**[EINSCHAETZUNG] Passung zu uns:** Der Umbau ist additiv (zweiter Wert je Knoten, ein
Mischparameter), das Netz bleibt unveraendert, und die Wirkung ist genau
"weniger Mittelung, mehr Minimax" – also gegen das Wegmitteln gerichtet. Der
Wirkmechanismus laut Autoren ist aber KURZFRISTIG-taktisch, nicht langfristig-strategisch.
Ich halte es fuer wahrscheinlicher, dass es unsere R5-Zone und Endphasen verbessert als
unsere Runden-1-3-Spaltenabsicht.

### S4.2 MCTS-Minimax-Hybride mit Zustandsbewertungen (Baier & Winands, JAIR 2018)

**[PAPER]** Drei Bauformen: Minimax in der Rollout-Phase, Minimax ALS ERSATZ der
Rollout-Phase, und Minimax als KNOTEN-PRIOR zur Verschiebung der Zugwahl; alle mit
Zugsortierung und k-best-Pruning fuer das Minimax [30]. Ergebnis: "Minimax zur Berechnung
von Knoten-Priors ergibt den staerksten untersuchten MCTS-Minimax-Hybrid in allen drei
Testdomaenen (Othello, Breakthrough, Catch the Lion)", und MCTS-IP-M-k schlaegt in
Breakthrough auch das reine verbesserte Minimax – der Hybrid ist dort staerker als beide
Eltern [30]. Konkrete Zahlen aus der Arbeit: Catch the Lion, MCTS-IC-M mit d=1 nur 2,9 %
von 1000 Partien, mit d=2 dann 34,3 %; MCTS-IP-M-IR-E gewinnt 61,1 % von 2000 Partien
gegen MCTS-IC-E [30]. **[EINSCHAETZUNG]** Die Variante "Minimax als Knoten-Prior" ist fuer
uns die attraktivste, weil sie den Suchkern (Gumbel-Wurzel, completed-Q) unberuehrt laesst
und nur die Prior-Berechnung eines Knotens ergaenzt. Der d=1/d=2-Sprung in Catch the Lion
warnt aber: eine 1-Halbzug-Minimax-Verlaengerung reicht nicht, man braucht mindestens 2.

### S4.3 Power-Mean-Backups (Power-UCT, Dam et al., IJCAI 2020)

**[PAPER]** Der Backup nutzt das Potenzmittel und liegt damit zwischen Mittelwert und
Maximum; Begruendung: "Mittelwert-Backup unterschaetzt den Optimalwert und verlangsamt das
Lernen, Maximum-Backup ueberschaetzt und verursacht Lernprobleme, besonders in
stochastischen Umgebungen"; Konvergenz zum Optimum ist bewiesen, und eine adaptive
Heuristik dreht die Gier ueber die Besuchszahl [31]. Nachfolgearbeit erweitert es auf
stochastische MCTS [32]. **Evidenzlage:** validiert gegen UCT auf MDP- und
POMDP-Benchmarks [31] – NICHT in Turnier-Brettspielen. **[EINSCHAETZUNG]** Genau der
Vorbehalt, den der Auftrag benennt. Als Env-Knopf ist es ein billiges A/B (ein Exponent
p), aber die Uebertragbarkeit auf ein Zwei-Spieler-Punktespiel mit Zufallsknoten ist
unbelegt, und "Maximum ueberschaetzt in stochastischen Umgebungen" ist bei unseren
Zufallsknoten ein konkretes Risiko.

### S4.4 Uncertainty- und Varianz-gewichtete Selektion (KataGo)

**[ENGINE]** KataGo gewichtet Playouts nach der vom Netz vorhergesagten Unsicherheit
(Downweighting unsicherer, Upweighting sicherer Playouts) und skaliert cPUCT dynamisch mit
der empirischen Utility-Varianz eines Knotens; beides zusammen: "etwa 75 Elo staerker als
das Vorgaengerrelease" [28]. Ebenfalls dort: Subtree Value Bias Correction (Buckets nach
lokalen Mustern, Online-Korrektur des beobachteten Fehlers zwischen Netz-Erstbewertung und
tieferer Suche), "30 bis 60 Elo" [28]. **[EINSCHAETZUNG]** Subtree Value Bias ist
interessant, weil er systematische Netz-Fehler korrigiert – und unser R5-Befund
(Value-Kopf-Plattendaempfung, Steigung 0,06-0,09) IST ein systematischer Fehler. Der
KataGo-Mechanismus braucht aber eine Bucket-Definition ueber lokale Muster; unser Analogon
waere ein Bucket pro Wertungsplatten-Konfiguration.

### S4.5 Simple-Regret-Wurzel und Anytime-Sequential-Halving

**[PAPER]** H-MCTS nutzt SHOT (rekursives Sequential Halving) nahe der Wurzel und UCT
weiter unten, demonstriert in sechs Zwei-Spieler-Spielen (Amazons, AtariGo, Ataxx,
Breakthrough, NoGo, Pentalath) [33]. Bekannte Schwaeche: Sequential Halving braucht ein
vorab festgelegtes Budget. **[PAPER]** Anytime Sequential Halving (Soemers et al. 2024)
behebt genau das und wird in synthetischen MAB-Problemen und zehn Brettspielen
konkurrenzfaehig zu Sequential Halving und UCB1 gemessen [34]. **[EINSCHAETZUNG]** Fuer
uns nur relevant, falls wir Zeitsteuerung statt festem Sim-Budget wollen – bei festem
Budget und Determinismus-Pflicht ist unser heutiger Weg der richtige.

### S4.6 Optimismus-Boni und Fallen-Erkennung

**[PAPER]** "Optimistische Zuege" (Finnsson & Bjoernsson) sind scheinbar starke Zuege, die
sofort widerlegt werden koennen, deren Widerlegung MCTS aber prohibitiv viele Simulationen
kostet; flache Fallen sind das verwandte Phaenomen, und die dokumentierte Gegenmassnahme
sind eingebettete flache Minimax-Suchen [20]. **[EINSCHAETZUNG]** Bei uns ist das
Spiegelbild interessant: nicht die scheinbar starke Falle, sondern die scheinbar schwache,
aber langfristig starke Bau-Linie. Optimismus-Boni (im Sinne von "bewerte einen Knoten
nach oben, solange seine Streuung gross ist") sind dafuer eine plausible, aber in
Brettspielen kaum belegte Antwort.

---

## S5. Umgang mit unseren Zufallsknoten je Paradigma

### S5.1 Was es an Optionen gibt

| Ansatz | Belegstufe | Kern | Determinismus |
|---|---|---|---|
| Expectiminimax mit Vollaufzaehlung | **[REPO]** in `round5.rs`, **[PAPER]** allgemein | Erwartungswert ueber alle Ausgaenge | vollstaendig deterministisch |
| *-Minimax Star1/Star2 (Ballard) | **[PAPER/ENGINE]** Backgammon [19,35] | Cutoffs auch in Zufallsknoten ueber Wertgrenzen | deterministisch, wenn Grenzen fest |
| ChanceProbCut (Schadd, Winands, Uiterwijk) | **[PAPER]** Stratego, Dice [36] | Forward-Pruning IN Zufallsknoten ueber Tiefenkorrelation | deterministisch, aber verlustbehaftet |
| Stochastic (Gumbel) AlphaZero/MuZero, Afterstates | **[PAPER]** 2048, Backgammon, Go [37,38] | Baum alterniert Entscheidungs- und Zufallsknoten, Ausgang wird GESAMPELT | Sampling: nur mit fixem Seed reproduzierbar |
| Determinisierung / ISMCTS | **[PAPER]** [39] | mehrere Welten, je Welt perfekte Information | Sampling der Welten |

### S5.2 Bewertung fuer unsere zwei Zufallsquellen

**Chip-Aufdeckung (4 Chips je Runde, Restsatz oeffentlich).**
**[REPO/geprueft, round5.rs:28-35]** Der Modulkopf haelt fest: oeffentlich ist der
RESTSATZ, verdeckt ist die ZUORDNUNG zu den Manufakturen; dafuer stehen die Zufallsknoten.
**[EINSCHAETZUNG]** Das ist die saubere Loesung und sie ist schon gebaut: kleine, exakt
aufzaehlbare Ausgangsmenge, keine Sampling-Varianz, Determinismus geschenkt. Star1/Star2
waere die naechste Stufe, aber der Modulkopf begruendet nachvollziehbar, dass es bei <=4
Ausgaengen nicht lohnt **[REPO/geprueft, round5.rs:49-52]**. Ich sehe keinen Grund, das
anzufassen.

**Fabrik-Neubefuellung am Rundenuebergang.** Hier ist die Ausgangsmenge kombinatorisch
gross, Vollaufzaehlung faellt aus. Zwei belegte Bauformen:
- **[PAPER]** Afterstate-Trennung nach Stochastic MuZero: "der Afterstate entspricht dem
  Brettzustand, nachdem ein Spieler seine Aktion gespielt hat, aber bevor der andere
  wuerfeln konnte"; das trennt den Aktionseffekt von der Umweltzufaelligkeit [37]. Real
  gemessen: 2048 besser als vorheriger SOTA mit perfekten Simulatoren; Backgammon mit 1600
  Simulationen auf Niveau von AlphaZero; Go unveraendert [37]. Und die Kombination mit
  Gumbel existiert (Stochastic Gumbel AlphaZero/MuZero, angewandt auf 2048) [38]
  **[PAPER]** – das ist die naechstliegende Literatur zu unserem heutigen Pfad.
- **[REPO/geprueft]** Wir haben mit `round_transition_deep.rs` und
  `round_transition_resample.rs` bereits Bausteine, die den Uebergang zum Zufallsknoten
  aufloesen und n-fach sampeln (`round_transition_deep.rs:562` beschreibt
  `resolve_to_pre_chance` plus n-faches Sampling). **[EINSCHAETZUNG]** Damit ist das
  Geruest fuer eine Erwartungswert-Behandlung des Rundenuebergangs vorhanden; was fehlt,
  ist die Verdrahtung in die laufende Suche und eine Seed-Disziplin.

### S5.3 Determinismus-Vertraeglichkeit – ausdrueckliche Bewertung

**[EINSCHAETZUNG]**, aber mit klarer Struktur:

- **Vollaufzaehlung (heutige R5-Loesung): unproblematisch.** Keine Zufallsquelle in der
  Suche, Golden-Tests bleiben gueltig.
- **Star1/Star2, ChanceProbCut: unproblematisch fuer Determinismus**, aber ChanceProbCut
  ist FORWARD-Pruning, also wertaendernd – es braucht eine eigene Golden-Test-Runde, weil
  es Zugwahlen bewusst veraendert.
- **Sampling-basierte Zufallsknoten (Stochastic AlphaZero-Linie): bedingt vertraeglich.**
  Reproduzierbar nur mit einem aus dem Zustand abgeleiteten, nicht aus der Wanduhr oder
  Thread-Reihenfolge stammenden Seed. Der Memory-Eintrag zur Arena-Exklusivitaet
  ("CPU-Nebenlast verstuemmelt Partien nichtdeterministisch") zeigt, dass diese Klasse von
  Fehlern bei uns schon aufgetreten ist. Wer sampelt, MUSS den Seed aus
  (Partie-Seed, Zugnummer, Knotenpfad) ableiten.
- **Determinisierung/ISMCTS: am wenigsten vertraeglich** und laut Auftragslage auch am
  wenigsten noetig, weil wir fast vollstaendige Information haben. Es gibt im Repo bereits
  eine Vorregistrierung `PREREG_ismcts_determinizations.md` **[REPO, nur Dateiname
  geprueft]**; deren Inhalt habe ich nicht gelesen.

---

## S6. Empfehlungsmatrix

Fuenf Optionen, sortiert nach Verhaeltnis von erwartetem Nutzen gegen das MOTIVIERENDE
Problem zu Aufwand. Alle Nutzenaussagen sind **[EINSCHAETZUNG]**, die Belege dahinter
tragen die jeweils genannte Marke.

### O1. Implicit-Minimax-Backup als Env-Knopf (alpha-Mischung)

- **Wirkmechanismus:** zweiter, minimax-zurueckgegebener Wert je Knoten; Selektion nutzt
  `(1-alpha)*Q_MC + alpha*v_minimax` [29] **[PAPER]**. Das mittelt seltene starke Linien
  weniger weg, weil die Minimax-Schiene den besten Kindwert durchreicht statt ihn zu
  verduennen.
- **Constraint-Passung:** additiv (ein Feld je Knoten, ein Skalar), CPU-neutral, keine
  zusaetzliche Netz-Eval, deterministisch. Netz bleibt UNVERAENDERT weiterverwendbar.
- **Aufwand:** klein bis mittel.
- **Groesstes Risiko:** der publizierte Wirkmechanismus ist kurzfristig-taktisch [29]; es
  kann sein, dass es R5/Endphasen hilft und die Runden-1-3-Absicht gar nicht beruehrt.
  Zweitrisiko: unser Value-Kopf ist in R5 nachweislich gedaempft (Memory-Befund), und
  Minimax verstaerkt Einzelfehler, die Mittelung glaettet.
- **Vorschlag fuer die Vorregistrierung:** alpha in {0,2; 0,4}, Entscheidungsmass Arena
  (nicht offline), separat je Runde ausgewertet.

### O2. Minimax als Knoten-Prior in Runde 3-4 (MCTS-IP-Variante)

- **Wirkmechanismus:** bei Expansion eines Knotens eine flache Minimax-Suche (Tiefe 2, mit
  Policy-Sortierung und k-best-Pruning) und deren Ergebnis als Prior-Verschiebung; in
  Othello/Breakthrough/Catch the Lion der staerkste der untersuchten Hybride, in
  Breakthrough sogar staerker als beide Eltern [30] **[PAPER]**.
- **Constraint-Passung:** additiv und LOKALISIERBAR – man kann es auf Runde 3-4
  beschraenken, wo laut Auftragslage die Spaltenabsicht entsteht und R5 noch nicht greift.
  Deterministisch. Netz unveraendert.
- **Aufwand:** mittel. Die Zugsortierung liegt vor (Policy-Prior), das k-best-Pruning ist
  neu, und der Kostendeckel muss hart sein: bei ~1 ms/Eval kostet Tiefe-2-Minimax mit k=5
  rund 25 Evals JE EXPANSION, was bei 400 Sims das Budget sprengt. Realistisch nur mit
  k<=3 und nur an Knoten oberhalb einer Besuchsschwelle.
- **Groesstes Risiko:** Rechenkosten fressen den Nutzen; die Catch-the-Lion-Zahlen
  (2,9 % bei d=1 gegen 34,3 % bei d=2 [30]) zeigen, dass die billige Variante nichts
  taugt.
- **Netz weiterverwendbar:** ja.

### O3. Tree Reuse unterhalb der Wurzel (Gumbel-Wurzel bleibt frisch)

- **Wirkmechanismus:** der Teilbaum unter dem gespielten Zug wird uebernommen; die
  Gumbel-Ziehung und Sequential Halving an der Wurzel laufen neu. Real belegt als
  Standardpraxis [21] **[ENGINE]**, mit +110 Elo fuer die Graph-Variante in Crazyhouse
  [22] **[PAPER/ENGINE]** und einem 54,8 %-auf-67,4 %-Sprung fuer Pondering mit
  Teilbaum-Wiederverwendung [23] **[PAPER]**.
- **Constraint-Passung:** Determinismus bleibt erhalten, WENN die Wurzelphase frisch
  gerechnet wird und die uebernommenen Statistiken deterministisch entstanden sind. Netz
  unveraendert. Additiv im Sinne der Modelle, aber ein Eingriff in den Suchkern.
- **Aufwand:** mittel. Der Hauptaufwand ist nicht der Code, sondern die
  Determinismus-Absicherung und die Frage, wie vorbesuchte Kinder mit Sequential Halving
  zusammengehen (siehe S3.1: dazu FEHLT Literatur).
- **Groesstes Risiko:** genau diese Luecke. Ausserdem: es gibt mehr Rechenzeit, nicht mehr
  Absicht – es adressiert das motivierende Problem nur indirekt.
- **Netz weiterverwendbar:** ja.

### O4. Zufallsknoten am Rundenuebergang in die Suche ziehen (Afterstate-Bauform)

- **Wirkmechanismus:** die Suche endet heute faktisch an der Rundengrenze; mit
  Afterstate-Trennung (Aktion -> Afterstate -> gesampelter Nachfolgezustand [37]
  **[PAPER]**) kann sie darueber hinaussehen. Das ist der EINZIGE der fuenf Vorschlaege,
  der die mehrrundige Absicht direkt sichtbar macht, statt sie ueber Bewertung zu
  simulieren.
- **Constraint-Passung:** die Bausteine existieren (`round_transition_deep.rs:562`
  beschreibt `resolve_to_pre_chance` plus n-faches Sampling) **[REPO/geprueft]**.
  Determinismus NUR mit strikt abgeleitetem Seed (siehe S5.3). Netz unveraendert, weil die
  Eingabekodierung sich nicht aendert.
- **Aufwand:** gross.
- **Groesstes Risiko:** Sampling-Varianz plus Determinismus. Zweitrisiko: der Value-Kopf
  muss dann Zustaende direkt nach einem Rundenuebergang bewerten – eine Verteilung, die im
  Trainingskorpus vorkommt, aber nicht als SUCHBLATT.
- **Bemerkung:** Stochastic MuZero brauchte in Backgammon 1600 Simulationen, um AlphaZero
  zu erreichen [37]. Bei 150-600 Sims ist das ein Warnsignal.

### O5. Sticky Prior als weiche Sortier-/Prior-Verschiebung (KEINE harte Bindung)

- **Wirkmechanismus:** Zuege, die zur zuletzt gesuchten Hauptvariante gehoeren, bekommen
  im Prior einen kleinen additiven Bonus. Vorbild ist die History-/Killer-Heuristik in
  Alpha-Beta-Engines, die Sortierwissen ueber Zuege hinweg traegt [18] **[ENGINE]**.
- **Constraint-Passung:** streng additiv (ein Bonusterm), deterministisch, CPU-frei, Netz
  unveraendert. Der Bonus ist ueberstimmbar – das ist der Punkt, an dem der hausinterne
  Negativbefund respektiert wird **[REPO/geprueft, column_build.rs:21-30]**.
- **Aufwand:** klein.
- **Groesstes Risiko:** zwei. Erstens: es gibt fuer diese Bauform in Brettspiel-Engines
  KEINEN mir bekannten Staerkebeleg – ich habe gesucht und nur Alpha-Beta-Sortier-
  Heuristiken und Optionen-Literatur gefunden. Zweitens: KataGo verschiebt die
  Wurzel-Policy bewusst in die GEGENRICHTUNG (Softmax-Temperatur > 1 als rueckstellende
  Kraft [28] **[ENGINE]**), was nahelegt, dass zusaetzliche Schaerfe an der Wurzel eher
  schadet.

### Ausdrueckliches Gegenmodell: "der Gumbel-Pfad bleibt richtig"

**[EINSCHAETZUNG], gestuetzt auf S1:** Ein Ersatz des Gumbel-MCTS durch Alpha-Beta halte
ich fuer schlecht begruendet. Der Alpha-Beta-Vorteil in Rapfi haengt am inkrementell
aktualisierbaren Netz [13] **[ENGINE]**; unser tract-Netz ist nicht inkrementell, damit
faellt der Faktor weg, aus dem der Vorteil kommt. Der Gumbel-Ansatz ist genau fuer wenige
Simulationen entworfen [14] **[PAPER]**. Und die Literatur ordnet Alpha-Beta die TAKTISCHE
Reparatur zu, MCTS die strategische [2,20] – unser Problem ist strategisch.
Die konsequente Lesart lautet: Gumbel behalten, gezielt ergaenzen (O1, O2, O3), und O4 nur
mit voller Vorregistrierung angehen.

---

## Quellen

1. Leela Chess Zero / Stockfish Vergleich (Suchparadigmen, NPS-Verhaeltnis):
   https://www.raindropchess.com/stockfish-vs-leela-chess-zero-vs-komodo-dragon-how-the-top-3-engines-actually-differ/
   und https://en.wikipedia.org/wiki/Leela_Chess_Zero
2. Czech, Willig et al., "Learning to play the Chess Variant Crazyhouse above World
   Champion Level with Deep Neural Networks and Human Data":
   https://arxiv.org/pdf/1908.06660
3. "Stockfish Absorbs NNUE, Claims 100 Elo Point Improvement":
   https://www.chess.com/news/view/stockfish-absorbs-nnue-100-elo
4. NNUE-Uebersicht: https://beuke.org/nnue/ und
   https://en.wikipedia.org/wiki/Efficiently_updatable_neural_network
5. YaneuraOu (WCSC29, NNUE): https://en.wikipedia.org/wiki/YaneuraOu
6. Cohen-Solal, Cazenave, "Minimax Strikes Back": https://arxiv.org/html/2012.10700
7. "Descent wins five gold medals at the Computer Olympiad":
   https://journals.sagepub.com/doi/full/10.3233/ICG-210192
8. "On some improvements to Unbounded Minimax" (2025):
   https://arxiv.org/html/2505.04525v1
9. Korf, Chickering, "Best-First Minimax Search":
   https://www.semanticscholar.org/paper/Best-First-Minimax-Search-Korf-Chickering/3cd93c0f7af712d06bf96eee739a69b5a011ed21
   sowie "Best-First Minimax Search: Othello Results":
   https://www.semanticscholar.org/paper/Best-First-Minimax-Search:-Othello-Results-Korf-Chickering/6a3f4a421466d3f83ec02da847d57598acd25347
10. Plaat et al., "Best-First and Depth-First Minimax Search in Practice":
    https://arxiv.org/abs/1505.01603 ; Schaeffer, Plaat, "New Advances in Alpha-Beta
    Searching": https://liacs.leidenuniv.nl/~plaata1/papers/acm-final.pdf
11. Kowalski, Soemers, Kosakowski, Winands, "Generalized Proof-Number Monte-Carlo Tree
    Search" (2025): https://arxiv.org/abs/2506.13249
12. Cazenave, Saffidine, "Score Bounded Monte-Carlo Tree Search":
    https://www.lamsade.dauphine.fr/~cazenave/papers/mcsolver.pdf
13. "Rapfi: Distilling Efficient Neural Network for the Game of Gomoku":
    https://arxiv.org/abs/2503.13178 und
    https://openreview.net/pdf/1e9d3e9c5820892cc51138d092b1ce02d038e19e.pdf
14. Danihelka, Guez, Schrittwieser, Silver, "Policy Improvement by Planning with Gumbel":
    https://davidstarsilver.wordpress.com/wp-content/uploads/2025/04/gumbel-alphazero.pdf
15. Wu et al., "MiniZero: Comparative Analysis of AlphaZero and MuZero on Go, Othello, and
    Atari Games": https://arxiv.org/abs/2310.11305
16. AlphaViT / UCT-vs-Alpha-Beta-Zahl fuer Connect-4:
    https://arxiv.org/pdf/2408.13871
17. "Move Ordering Using Neural Networks":
    https://www.researchgate.net/publication/221047746_Move_Ordering_Using_Neural_Networks
18. Chess Programming Wiki, Iterative Deepening / Killer Heuristic / History Heuristic:
    https://chessprogramming.org/Iterative_Deepening ,
    https://chessprogramming.org/Killer_Heuristic ; Schaeffer, "The History Heuristic and
    Alpha-Beta Search Enhancements in Practice":
    https://webdocs.cs.ualberta.ca/~jonathan/publications/ai_publications/pami.pdf
19. Hauk, Buro, Schaeffer, "*-Minimax Performance in Backgammon":
    https://link.springer.com/chapter/10.1007/11674399_4
20. Baier, Winands, "Monte-Carlo Tree Search and Minimax Hybrids":
    https://dke.maastrichtuniversity.nl/m.winands/documents/paper%2049.pdf
21. "Technical Explanation of Leela Chess Zero":
    https://lczero.org/dev/wiki/technical-explanation-of-leela-chess-zero/
22. Czech, Korus, Kersting, "Monte-Carlo Graph Search for AlphaZero":
    https://arxiv.org/pdf/2012.11045 und
    https://ojs.aaai.org/index.php/ICAPS/article/download/15952/15763/19445
23. "Enhancing the Monte Carlo Tree Search Algorithm for Video Game Testing":
    https://arxiv.org/pdf/2003.07813
24. Danihelka, "Planning and Policy Improvement" (Dissertation):
    https://discovery.ucl.ac.uk/10167022/2/ivo_danihelka_thesis.pdf
25. "OptionZero: Planning with Learned Options" (ICLR 2025):
    https://arxiv.org/html/2502.16634 und
    https://proceedings.iclr.cc/paper_files/paper/2025/file/c7f812431607ac5a17973bbf79733013-Paper-Conference.pdf
26. de Waard et al., "Monte Carlo Tree Search with options for general video game playing":
    https://www.researchgate.net/publication/313963372
27. "Subgoal-Based Temporal Abstraction in Monte-Carlo Tree Search" (IJCAI 2019):
    https://www.ijcai.org/proceedings/2019/0772.pdf ; "Automatic Goal Discovery in Subgoal
    Monte Carlo Tree Search": https://ieee-cog.org/2021/assets/papers/paper_283.pdf
28. KataGo, `docs/KataGoMethods.md`:
    https://github.com/lightvector/KataGo/blob/master/docs/KataGoMethods.md ; Wu,
    "Accelerating Self-Play Learning in Go": https://arxiv.org/pdf/1902.10565
29. Lanctot, Winands, Pepels, Sturtevant, "Monte Carlo Tree Search with Heuristic
    Evaluations using Implicit Minimax Backups": https://arxiv.org/abs/1406.0486
    (gelesen ueber https://ar5iv.labs.arxiv.org/html/1406.0486 )
30. Baier, Winands, "MCTS-Minimax Hybrids with State Evaluations", JAIR:
    https://www.jair.org/index.php/jair/article/view/11208 ; Kurzfassung:
    https://www.ijcai.org/proceedings/2018/0782.pdf
31. Dam, Klink, D'Eramo, Peters, Pajarinen, "Generalized Mean Estimation in Monte-Carlo
    Tree Search" (Power-UCT), IJCAI 2020: https://www.ijcai.org/proceedings/2020/0332.pdf
32. "Power Mean Estimation in Stochastic Monte-Carlo Tree Search":
    https://arxiv.org/abs/2406.02235
33. Pepels, Cazenave, Winands, Lanctot, "Minimizing Simple and Cumulative Regret in
    Monte-Carlo Tree Search": https://dke.maastrichtuniversity.nl/m.winands/documents/h-mcts.pdf
34. "Anytime Sequential Halving in Monte-Carlo Tree Search":
    https://arxiv.org/pdf/2411.07171
35. Hauk, Buro, Schaeffer, "Rediscovering *-Minimax Search":
    https://link.springer.com/chapter/10.1007/11674399_3
36. Schadd, Winands, Uiterwijk, "CHANCEPROBCUT: Forward Pruning in Chance Nodes":
    https://dke.maastrichtuniversity.nl/m.winands/documents/CIG2009.pdf
37. Antonoglou, Schrittwieser, Ozair, Hubert, Silver, "Planning in Stochastic Environments
    with a Learned Model" (Stochastic MuZero, ICLR 2022):
    https://openreview.net/pdf?id=X6D9bAHhBQ1
38. Stochastic Gumbel AlphaZero / Gumbel MuZero auf 2048, referiert in:
    https://arxiv.org/html/2603.18994v1 ; verwandt: "An Empirical Analysis of Gumbel MuZero
    on Stochastic and Deterministic Einstein Wuerfelt Nicht!":
    https://link.springer.com/chapter/10.1007/978-981-97-1711-8_25
39. Cowling, Powley, Whitehouse, "Information capture and reuse strategies in Monte Carlo
    Tree Search, with applications to games of hidden information":
    https://www.sciencedirect.com/science/article/pii/S0004370214001052

---

## Fazit (10 Zeilen)

1. Kein Paradigmenwechsel noetig: Gumbel-MCTS ist genau fuer 150-600 Sims gebaut [14], und
   der einzige starke CPU-only-Gegenbeleg (Rapfi [13]) haengt an einem inkrementell
   aktualisierbaren Netz, das wir nicht haben.
2. Die Literatur ordnet Alpha-Beta die TAKTISCHE Reparatur zu und MCTS die strategische
   Staerke [2,20] – unser Problem ist strategisch, also loest ein AB-Umbau es nicht.
3. Unsere R5-Suche ist bereits die lehrbuchgemaesse Antwort fuer Zufallsknoten
   (Expectiminimax mit exakter Blattwertung); ihr Wert kommt gemessen aus dem Blatt, nicht
   aus der Tiefe (81,4 % bei 200 gegen 84,8 % bei 4000 Knoten).
4. Genau das bestaetigt die Unbounded-Minimax-Ablation extern: exakte Terminalwertung ist
   mit 13,13 Punkten der weitaus groesste Einzelposten [8].
5. Gegen das Wegmitteln gibt es eine belegte, additive Massnahme: Implicit Minimax Backups,
   mit publizierten Gewinnraten bis 82,3 % und einem sicheren Bereich alpha um 0,2 [29].
6. Die staerkste Hybrid-Bauform ist "Minimax als Knoten-Prior" (bester Hybrid in drei
   Domaenen, in Breakthrough staerker als beide Eltern) – aber erst ab Tiefe 2 [30].
7. Power-Mean-Backups sind theoretisch attraktiv, in Brettspielen aber unbelegt (nur MDP/
   POMDP-Benchmarks) und in stochastischen Umgebungen ausdruecklich risikobehaftet [31].
8. Tree Reuse ist Engine-Standard und lohnend [21,22,23], gibt uns aber Rechenzeit statt
   Absicht; ausserdem fehlt Literatur zur Kombination mit Gumbels Sequential Halving.
9. Optionen/Makro-Aktionen (OptionZero) sind die einzige echte Plan-Persistenz-Linie, aber
   ohne jeden Brettspielbeleg und mit dokumentiertem Abfall bei komplexen Aktionsraeumen
   [25]; dazu passt unser eigener Negativbefund zur festen Spaltenbindung.
10. Empfehlung in dieser Reihenfolge: O1 (Implicit-Minimax-Knopf, klein), O2 (Minimax-Prior
    in Runde 3-4, mittel), O3 (Tree Reuse unter der Wurzel, mittel), O5 (weicher Sticky
    Prior, klein, unbelegt), O4 (Zufallsknoten am Rundenuebergang, gross, hoechstes Risiko).
