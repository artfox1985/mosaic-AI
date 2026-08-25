# Externe Recherche: Spielstrategie und Heuristik-Methodik

**Stand 2026-08-25.** Auftrag: externe Internet-Recherche zu (a) Spielstrategien
fuer das Mosaic-/Azul-Duel-Regelwerk und (b) Methodik, wie man Heuristiken
systematisch baut. Ausloeser war die Nutzer-Beobachtung, der Zufall sitze
INNERHALB der Runde im Kuppelstapel und ZWISCHEN den Runden in Fabriken und
Bonuschips.

**Regel-0-Kennzeichnung.** Jeder Absatz sagt, woher er kommt:
`[EXTERN]` = fremde Quelle, in dieser Sitzung gelesen aber inhaltlich NICHT
nachgeprueft; `[GEPRUEFT]` = an genannter Stelle im Repo nachgesehen;
`[HERLEITUNG]` = folgt aus einer geprueften Stelle, ist selbst aber nicht
gemessen. Keine Zahl aus diesem Dokument geht ungeprueft in eine Rechnung.

---

## 0. Quellenlage vorweg

`[EXTERN]` Zu **Azul Duel** selbst existiert kein Strategiekorpus. Gefunden
wurden: die Regelhilfe von Board Game Arena, vier Rezensionen (Meeple Mountain,
Opinionated Gamers, What's Eric Playing, Tabletopping) und ein kurzer
BGG-Thread zu Bonuschips. Keine Turnierdaten, keine Eroeffnungstheorie, keine
Partiendatenbank, kein Fachartikel.

`[EXTERN]` Zu **Azul (Grundspiel)** gibt es Strategie-Blogs und drei
studentische KI-Projekte (u.a. eine Melbourner Kurs-Competition, COMP90054),
aber ebenfalls keinen begutachteten Fachartikel und keine
Komplexitaetsanalyse. Die Suche nach "Azul NP-hard" liefert nichts.

**Konsequenz.** Externe Quellen liefern fuer dieses Projekt keine Zahlen,
sondern nur Struktur- und Methodenwissen. Die quantitative Autoritaet bleibt
die eigene Messkette. Wo unten Zahlen aus Blogs stehen, sind sie als solche
markiert und ausdruecklich nicht belastbar.

---

## 1. Wo der Zufall wirklich sitzt

Die Ausgangsvermutung stimmt, laesst sich aber schaerfen.

`[GEPRUEFT]` **Rundenuebergang.** `engine/src/round_transition.rs`, Modulkopf:
die Fabrik-Neubefuellung ist "der EINE tatsaechlich zufaellige Schritt", und
der Suchbaum laeuft "bewusst NUR innerhalb einer Runde". Die Bonuschips werden
im selben Schritt gezogen: `round_transition_resample.rs:8-10` invertiert
`fill_factories` und legt dafuer "Sonnenplaettchen + Bonuschips zurueck in
Beutel/Pool".

`[HERLEITUNG]` Damit sind die Chips **kein eigener Zufall in der Runde**. Ihr
Wert steht beim Rundenaufbau fest; was in der Runde passiert, ist reine
**Informationsaufdeckung** (Chip wird sichtbar, sobald seine Fabrik leer ist,
`docs/engine_manual.md` §2). In der Fachsprache der Imperfect-Information-
Literatur ist das der *disambiguation factor*, nicht ein Chance-Node. Das ist
kein Wortspiel: Zufall braucht Erwartungswertbildung, Aufdeckung braucht
Glaubens-Zustaende oder eine Entscheidung ueber das Aufdeck-Timing. Der
Mond-Stapel ist genau der Hebel dafuer: wer eine Fabrik leerraeumt, deckt auf.

`[GEPRUEFT]` **Innerhalb der Runde** gibt es genau einen echten Zufall: die
Blindziehung vom Kuppelstapel, `Action::DrawStackPeek` in
`engine/src/moves.rs:117`, Regel in `docs/engine_manual.md` §4A.

`[HERLEITUNG]` Damit ist Mosaic **fast ein stochastisches Spiel mit vollstaendiger
Information** (Backgammon-Klasse), nicht ein Kartenspiel-artiges Spiel mit
privater Information. Beide Spieler wissen dasselbe ueber Beutel, Turm,
Fabriken und Bretter. Die einzige echte private Information, die das
Regelwerk kennt, ist die vom ziehenden Spieler frei gewaehlte **Rueckgabe-
Reihenfolge** der nicht behaltenen Platten unter den Stapel
(`docs/engine_manual.md` §4A; ob die Engine das so modelliert, ist hier NICHT
geprueft) sowie die Stapelordnung selbst.

**Warum das methodisch zaehlt:** CFR, ISMCTS und Belief-Modellierung – der
teure Werkzeugkasten fuer Poker-artige Spiele – sind hier ueberdimensioniert.
Zustaendig ist die Literatur zu **Chance-Nodes**: Expectimax, Sparse Sampling
und `*`-Minimax (Lanctot et al., *Monte Carlo `*`-Minimax Search*), sowie
Double Progressive Widening, wenn die Zahl der Ausgaenge an einem Chance-Node
zu gross wird. `[EXTERN]`

---

## 2. Der Stand der Engine gegen diese Literatur

`[GEPRUEFT]` Zwei Schalter stehen aktuell auf `false`:

* `net_mcts.rs:84` `ROUND_TRANSITION_SAMPLING = false` – der Rundenuebergang
  wird NICHT als Chance-Node gesampelt; der Blattwert muss die Verteilung
  implizit mitteln. Der Modulkopf von `round_transition.rs` nennt genau das
  als Verdacht fuer das Val-R2-Plateau.
* `net_mcts.rs:654` `SHUFFLE_STACK_PEEK_IN_SEARCH = false` – die Suche liest
  beim Peek die **echte, im realen Spiel verdeckte** oberste Platte. Der
  Kommentar dort dokumentiert den Messversuch vom 2026-07-20: mit Neumischung
  9:91 statt 17 % Siege, Begruendung "die Neumischung erhoeht eher die Varianz
  der Suche (jeder simulierte Ast sieht eine andere Ziehung)".

`[EXTERN]` Genau dieser Ausgang ist in der Literatur ein bekanntes Muster. Long,
Sturtevant, Buro und Furtak (*Understanding the Success of Perfect Information
Monte Carlo Sampling in Game Tree Search*, AAAI 2010) zeigen, dass
"schummelnde" Perfect-Information-Suche in vielen Spielen praktisch nah am
Optimum liegt, und identifizieren drei Spieleigenschaften, die das
vorhersagen: *leaf correlation* (aehnliche Auszahlung benachbarter Blaetter),
*bias* und *disambiguation factor* (wie schnell verdeckte Information
aufgedeckt wird). Hohe Blattkorrelation und schnelle Aufdeckung sprechen fuer
PIMC. `[HERLEITUNG]` Mosaic hat beides: eine Platte mehr oder weniger
verschiebt den Endstand selten kategorisch, und die Aufdeckung erfolgt sofort
beim Ziehen.

`[EXTERN]` Die Gegenrichtung ist ebenso dokumentiert: *strategy fusion* und
*non-locality* (Frank, Basin, Matsubara 1998) sind die theoretischen Kosten
der Determinisierung, und der Standardfehler beim Beheben ist eine
Varianzexplosion, wenn pro Simulation neu gewuerfelt wird statt eine feste
Stichprobe zu benutzen.

**Ehemaliger Uebernahme-Kandidat, am 2026-08-25 ZURUECKGEZOGEN.** Die erste
Fassung schlug hier vor, beim Peek nicht pro Simulation neu zu mischen,
sondern K feste Determinisierungen an der Wurzel zu benutzen (Common Random
Numbers). Der Vorschlag war ungeprueft gegen den Bestand -- die Frage ist im
Projekt bereits entschieden, und zwar negativ:

`[GEPRUEFT]` `evaluations/PREREG_ismcts_determinizations.md`, Status
ENTSCHIEDEN: Mehrfach-Determinisierung k=1/2/4 wurde unter ZWEI Anordnungen
gemessen -- Sims-Split bei festem Budget (76,0 / 77,3 / 70,0 %) und gleiche
Tiefe je Welt, also mit k wachsendem Budget (81,75 / 77,0 / 73,0 %). k=4
faellt in beiden Faellen ab, im zweiten mit VIERFACHEM Budget, und in beiden
Pflichtinstrumenten signifikant (Block-t −3,73, McNemar p=0,00262, Bonferroni
inklusive). Die dort registrierte Deutung ist nicht "zu wenig Tiefe", sondern:
**das Mitteln ueber gezogene Welten schadet aktiv**.

Damit ist die Varianzreduktions-Idee nicht nur unbelegt, sondern laeuft der
gemessenen Richtung entgegen. Sie wird hier nicht weiterverfolgt. Was offen
BLEIBT, ist etwas anderes und liegt in `PREREG_chance_nodes.md` Teil B1: dem
Peek-Knoten eine korrekte Ein-Schritt-Erwartung geben, statt ueber Welten zu
mitteln.

---

## 3. Ein exakt rechenbarer Fund: die Blindziehung ist ein Pandora's-Box-Problem

`[GEPRUEFT]` Regel (`docs/engine_manual.md` §4A): jede einzelne Blindziehung
kostet 1 Punkt, darf beliebig oft wiederholt werden, die Rueckseiten zeigen
nur den Typ (Wild/Special), am Ende behaelt man **eine** Platte, der Rest geht
zurueck.

`[HERLEITUNG]` Das ist buchstaeblich das oekonomische Standardmodell
**"sequenzielle Suche mit Rueckgriff und konstanten Suchkosten"** – der Kern
von Weitzmans Pandora's Box `[EXTERN]`. Fuer den Fall, dass alle Ziehungen aus
derselben Verteilung stammen und Rueckgriff erlaubt ist, ist die optimale
Politik keine Suche, sondern eine **Reservationswert-Regel**:

> Ziehe weiter, solange der Wert der besten Platte in der Hand unter R liegt.
> R ist der Wert, der `E[max(V − R, 0)] = c` loest, mit c = Ziehungskosten.

`[EXTERN]` Der Reservationswert haengt nur von Verteilung und Kosten ab, nicht
vom bisher Gesehenen – das ist die Eigenschaft, die die Regel ueberhaupt
brauchbar macht.

`[HERLEITUNG]` Fuer Mosaic ist das besonders guenstig, weil die Rueckseite den
Typ verraet: es gibt nur zwei Verteilungen (Wild/Special), und die Restmenge
des Stapels ist oeffentlich abzaehlbar. R ist also je Zustand ausrechenbar,
ohne Baum.

**Zwei Faelle, die eine Umsetzung pruefen muesste (beide NICHT geprueft):**

1. **c ist nicht konstant.** Bei Punktestand 0 ist eine Ziehung faktisch
   gratis (`docs/engine_manual.md` §4A: Score kann nie unter 0 fallen). Die
   Reservationsregel degeneriert dort zu "zieh weiter, bis der Stapel nichts
   Besseres mehr hergibt". Ob die Engine das so spielt, waere zu messen.
2. **V ist zustandsabhaengig.** Der Wert einer Platte haengt vom eigenen
   Brett ab (welche Farbzellen in welcher Rasterreihe noch fehlen). Die Regel
   bleibt gueltig, sie braucht nur eine brettabhaengige Bewertung V – exakt
   das, was der Plattenbau-Layer ohnehin schon berechnet.

### 3a. Die Voraussetzungen, am Code geprueft (2026-08-25)

Die Regel taugt nur, wenn das Spiel wirklich die Struktur hat, die sie
voraussetzt. Vier Punkte, alle `[GEPRUEFT]`:

1. **Konstante Kosten je Ziehung.** `game.rs:182` `apply_paid_cost(-1)`, im
   Kommentar ausdruecklich als KAUF bezeichnet, nicht als Strafe -- und "bei 0
   Punkten laut Regelbuch wirklich gratis".
2. **Rueckgriff besteht.** Gezogene Platten sammeln sich in
   `pending_stack_draw` (`game.rs:185`), und `validate_draw_from_stack`
   akzeptiert JEDE `chosen_id` aus dieser Menge (`game.rs:201`). Man behaelt
   also die beste aller bisher gezogenen, nicht die letzte. Das ist genau die
   Voraussetzung "search with recall".
3. **Endlicher, abzaehlbarer Vorrat.** Die Ziehung nimmt vorne aus
   `dome_tile_pool` (`game.rs:183`); `serialize.rs:265/282` legen
   `dome_stack_count` und `dome_wild_remaining_frac` offen. Kein Ziehen mit
   Zuruecklegen, sondern aus einem bekannten Rest.
4. **Der Typ der NAECHSTEN Platte ist gratis sichtbar.**
   `serialize.rs:270` `dome_stack_top_type` liest
   `dome_tile_pool.first()` und meldet Wild oder Special, BEVOR bezahlt wird.

Punkt 4 ist der wichtigste und war in der ersten Fassung dieses Abschnitts
nicht gesehen. Er macht die Aufgabe **leichter** als das Lehrbuchproblem: dort
zahlt man, um ueberhaupt etwas ueber die Kiste zu erfahren, hier bekommt man
das Typ-Signal umsonst. Damit gibt es nicht EINEN Reservationswert, sondern
zwei bedingte -- `[HERLEITUNG]`:

> Zieh weiter, wenn `E[max(V_next − V_hand, 0) | Typ des naechsten Rueckens]`
> groesser ist als 1 Punkt.
> `V_hand` ist dabei nicht nur die beste gezogene Platte, sondern das Maximum
> aus gezogenen Platten UND der besten Platte im offenen Display -- die ist
> gratis zu haben und damit die eigentliche Ausstiegsoption.

Die verbleibende Unsicherheit steckt allein in der Farbanordnung der Platte,
nicht mehr in ihrem Typ. `[HERLEITUNG]` Zwei Einschraenkungen, die eine
Umsetzung ausweisen muesste, statt sie zu verschweigen:

* Die Myopie-Regel ("eine Ziehung vorausschauen") ist im klassischen Fall
  unabhaengiger, gleichverteilter Ziehungen mit Rueckgriff **exakt** optimal.
  Hier wird ohne Zuruecklegen aus einem endlichen Vorrat gezogen; die Regel
  bleibt die naheliegende Naeherung, ihre Optimalitaet braucht aber den
  Monotonie-Nachweis (schliesst die Stopp-Menge?) und ist hier NICHT gefuehrt.
* `V` ist brettabhaengig (welche Farbzellen in welcher Rasterreihe noch
  fehlen). Das ist kein Hindernis, sondern eine Anschlussstelle: genau diese
  Groesse rechnet der Plattenbau-Layer bereits.

**Die Einheitenfrage, und warum sie die Regel entscheidet** (Hinweis der
Parallelsitzung 2026-08-25, von mir am Code nachgeprueft). Die Regel loest
`E[max(V − R, 0)] = c` mit `c = 1 PUNKT`. Ein `V` in anderer Einheit macht `R`
zu einer Zahl ohne Bedeutung -- dieselbe Fehlerklasse wie die
Floor-Shaping-Altlast.

`[GEPRUEFT]` Die naheliegende Anschlussstelle ist die falsche:
`column_build::cell_value` (Z.880-899) liefert Wild 3,0, Special 2,0, passende
Farbe 2,5 (bzw. `JACKPOT_WERT`), leere Reihe 1,5, falsche Farbe 0,0 -- reine
Praeferenz-Einheiten fuer Rangvergleiche, nie gegen Punkte geeicht.

`[GEPRUEFT]` Richtig ist `plate_builder::points_map` (Z.1039-1102, oeffentlich
als `expected_points_map`): je Zelle `scoring_progress(&probe, ids) − basis +
bonus`, mit Spezialfliesen-Sofortbonus und, bei `mit_platzierung`, den
Linienpunkten aus `round_end::score_placed_tile`. Durchgehend Punkte, und es
benutzt die Anker-Formel selbst statt eines Nachbaus. `slot_score_generic`
(Z.450-459) nimmt die Zellbewertung als Funktionszeiger, dieselbe Schleife
laeuft also mit der Punktekarte.

`[HERLEITUNG]` Zwei Skalen-Fallen bleiben auch dann offen, und eine Umsetzung
muss sie ausweisen:

1. **Additivitaet.** `V(Platte) = Summe der Kartenwerte ueber die bedienbaren
   Zellen` unterstellt Unabhaengigkeit. `scoring_progress` ist nicht additiv:
   zwei Zellen, die gemeinsam eine Spalte schliessen, sind zusammen mehr wert
   als einzeln, und der gemeinsame Anteil wird bei getrennter Zaehlung doppelt
   vergeben. Die Summe ist eine Naeherung mit bekannter Richtung -- eher zu
   hoch.
2. **Potenzial gegen Realisierung.** Eine Platte FUELLT keine Zelle, sie macht
   sie bedienbar; die Steine muessen noch gedraftet und gekachelt werden. Ein
   `V` aus reinen Potenzialpunkten laesst die Regel zu oft ziehen. Der
   Abschlag ist messbar statt zu raten: der gemessene Durchsatz je Rasterreihe
   (4,80 / 4,77 / 2,84 / 1,89 / 0,84 / 0,58 Abschluesse je Partie,
   `docs/domain_knowledge.md`) ist genau die Groesse, mit der eine Zelle in
   Rasterreihe r abzuwerten waere.

Solange beide Punkte nicht beziffert sind, ist die Regel als **Struktur**
richtig und als **Zahl** nicht einsatzbereit. Eine Reservationsregel mit falsch
skaliertem `V` waere schlechter als keine, weil sie eine Zahl mit Bedeutung
vortaeuscht.

**Stand der beiden Fallen, 2026-08-25 abends.**

Zu (1): die Parallelsitzung hat `plate_builder::best_plate_value(player, tile,
zellen, karte, wert) -> Option<f64>` gebaut (roher Maximalwert ueber Slot und
Rotation, Legalitaet nur geometrisch, `wert` als Funktionszeiger). Die
Additivitaets-Naeherung laesst sich exakt ersetzen, indem die Zellen einer
(Slot, Rotation)-Kombination auf einem Probe-Brett GEMEINSAM belegt werden und
EINE `scoring_progress`-Differenz genommen wird. Das ist hier der richtige Weg:
die Naeherung irrt nach oben, und nach oben ist die Richtung, in der die Regel
zu oft zieht.

Zu (2): Vorschlag fuer den Realisierungsabschlag, `[HERLEITUNG]`, aus
gemessenen Groessen statt aus einer Setzung. Eine Platte macht eine Zelle
bedienbar; belegt wird sie erst, wenn ihre Musterreihe noch abschliesst und die
Farbe passt. Aus `docs/domain_knowledge.md:39-46` steht der Abschluss je Reihe
und Runde bereits gemessen zur Verfuegung. Fuer eine Entscheidung in Runde k:

> `E[Restabschluesse der Reihe r] = Summe der Tabellenwerte ueber die Runden
> k..5`, und die Chance einer BESTIMMTEN freien Zelle in Rasterreihe r ist in
> erster Naeherung dieser Wert geteilt durch die Zahl der noch freien Zellen
> dieser Reihe -- die Zelle konkurriert mit ihnen um dieselben Abschluesse.

Beispiel fuer die Groessenordnung: Reihe 6 liefert ueber die Runden 3-5
zusammen 0,15 + 0,23 + 0,19 = 0,57 Abschluesse, Reihe 1 im selben Fenster
0,91 + 0,95 + 1,13 = 2,99. Eine Zelle ganz unten ist also, bei gleicher
Punktzahl auf der Karte, um ein Vielfaches weniger wert als eine oben. Genau
diese Verschiebung fehlt einer reinen Potenzialkarte.

**Vorbehalt gegen die eigene Zahl**: die Durchsatztabelle ist das IST eines
v20-Self-Play-Korpus MIT Wurzelrauschen, also das Verhalten eines Spielers, der
lange Reihen gerade nicht vollendet. Sie als Realisierungswahrscheinlichkeit zu
nehmen, schreibt diese Schwaeche in die Regel fort -- dieselbe Falle, die im
Memory als "nie auf plattenblindes Normalspiel eichen" steht. Fuer eine erste
Fassung ist sie die beste verfuegbare Groesse; sie gehoert erneut gemessen,
sobald ein Champion die Spalten tatsaechlich schliesst.

`[HERLEITUNG]` Warum das relevant ist: aus der Regel folgt, dass **in jeder
Runde 1-4 mindestens eine Blindziehung stattfinden MUSS** – vier Platzierungen
(zwei je Spieler, §4A) stehen drei offenen Display-Platten gegenueber, und das
Display wird waehrend der Runde nicht nachgefuellt (§2). Die vierte
Platzierung kommt zwangslaeufig aus dem Stapel. Das ist keine Randentscheidung,
sondern ein Pflichtereignis mindestens viermal je Partie.

---

## 4. Methodik: wie man Bewertungsheuristiken baut

Zusammengetragen aus der Schachprogrammier-Literatur, General Game Playing
(Ludii/Clune) und der 2048-/Go-Linie. Alles `[EXTERN]`.

### 4.1 Aufbau der Funktion

* Terme werden nach **Ordnung** getrennt: erste Ordnung (Material), zweite
  Ordnung (Position einzelner Steine, Piece-Square-Tabellen), hoehere Ordnung
  (Wechselwirkungen mehrerer Steine). Die uebliche Kombination ist linear.
* **Feature-Unabhaengigkeit ist die zentrale Hygieneregel.** Verdeckte
  Abhaengigkeiten zwischen Termen erzeugen beim Abstimmen nichtlineare
  Effekte, die niemand mehr auseinandernehmen kann.
* **Tapered Eval**: zwischen Eroeffnungs- und Endspielgewichten wird nach
  Spielphase interpoliert. Fuer Mosaic ist die Phase nicht zu schaetzen,
  sondern gegeben (Runde 1-5, Platten nur in Runde 1-4). Das ist der
  naheliegendste Strukturimport ueberhaupt.
* Ludii fuehrt eine **Bibliothek generischer Heuristik-Terme** (Material,
  Mobilitaet, Einfluss, Linienvollendung, Naehe) jeweils mit positivem UND
  negativem Gewicht und sagt per Regression aus der Spielbeschreibung vorher,
  welche taugen. Das ist die sauberste Vorlage fuer einen Termkatalog, den man
  nicht einzeln von Hand erfindet.

### 4.2 Gewichte nicht von Hand setzen

Drei Familien, mit Datenbedarf und dokumentierten Fallstricken:

| Familie | Daten | Fallstrick |
|---|---|---|
| Logistische Regression auf Partieausgang (Texel-Tuning, Logistello) | markierte Stellungen + Ergebnis | braucht grosse, saubere Saetze; wird schlecht, sobald Suchparameter mit im Topf sind |
| TD / TD-Leaf (Samuel, KnightCap) | Selbstspiel | langsame Konvergenz, empfindlich gegen Lambda, braucht stabile Referenzgegner |
| Black-Box auf Matchergebnisse (SPSA, CLOP, CMA-ES, GA) | nur Partieausgaenge | teuer; skaliert schlecht mit der Parameterzahl, beruecksichtigt dafuer die Wechselwirkung Suche/Bewertung |

Zwei Merksaetze aus derselben Quelle, die zum Projekt passen: die Kunst
besteht darin, die **kleine richtige** Parametermenge zu finden (Althoefer);
und je enger zwei Gegner beieinander liegen, desto mehr Partien braucht der
Nachweis – bis in die Zehntausende.

### 4.3 Validierung: SPRT -- IM PROJEKT BEREITS GEBAUT

`[EXTERN]` Der Standard im Schach ist der sequenzielle Test (SPRT/GSPRT) mit
Elo_0/Elo_1-Grenzen und normalisiertem Elo, wodurch die erwartete Testdauer
nur noch von den Grenzen abhaengt, nicht vom Remisanteil.

**KORREKTUR 2026-08-25 (Nutzer-Rueckfrage).** Die erste Fassung dieses
Abschnitts nannte das "die disziplinierte Version dessen, was hier heute als
Arena mit fester n laeuft" und schlug einen Einbau auf Blockebene als
Uebernahme-Kandidat vor. Das war eine ungepruefte Behauptung ueber den
Projektstand und ist falsch -- ein Regel-0-Bruch. Der Test ist gebaut, und zwar
genau in der vorgeschlagenen Form:

`[GEPRUEFT]` `tools/paired_gating.py` faehrt einen truncated Wald-SPRT auf
**informativen PAAREN**, nicht auf Einzelspielen (Modul-Docstring Z.60-100,
Implementierung `sprt_bounds`/`sprt_llr_delta` Z.189-208): H0 p0 = 0,5, H1
p1 = 0,65 (per `--h1` verstellbar), alpha = beta = 0,05, Schranken
±ln(19) = ±2,9444, **LLR-Update nach jedem Block**, harter Deckel 200 Paare.
Splits tragen weder zum LLR noch zur Paarzahl bei. Der exakte
Paar-Vorzeichentest (McNemar) und die gepaarte Differenz-KI bleiben erhalten,
sind aber nur noch die deskriptive Endstatistik, nicht die Stopp-Regel. Bei
jedem Skriptstart laeuft ein Rechen-Selbsttest gegen die von Hand
ausgerechneten Schranken.

`[GEPRUEFT]` `tools/arena.py` hat zusaetzlich einen DUALEN SPRT auf
**Einzelspielen** (Z.68-92, Z.296-310): zwei parallele Tests, je p1 = 0,64,
alpha = 0,05, beta = 0,10. Das ist dort statistisch sauber, weil die Partien
nicht seed-gepaart sind -- `run_net_vs_net` spielt mit `seed = base_seed +
chunk_idx`, Netz A immer auf Brett 0 (Z.400-402); es gibt also keine zwei
Partien desselben Seeds, deren Ausgaenge sich gegenseitig erklaeren.

Offen bleibt allenfalls die Feinheit, dass Fishtest den GENERALISIERTEN SPRT
mit normalisiertem Elo benutzt, waehrend hier der klassische Wald-Test mit
festem p1 laeuft. Die Groesse, die normalisiertes Elo adressiert (Abhaengigkeit
der Testdauer vom Remis-/Streuungsanteil), faengt die Paarbildung hier bereits
weitgehend ab -- kein Kandidat, nur der Vollstaendigkeit halber vermerkt.

### 4.4 Heuristik als Aktionsfilter, nicht als Bewertung

`[EXTERN]` Aus der MCTS-Literatur (Ueberblicksarbeiten zu Modifikationen) und
aus dem Azul-Kursprojekt: Wissen kann an drei Stellen eingespeist werden – in
die Zugreihenfolge, in die Playouts ("heavy playouts") und in die Bewertung.
Im Azul-Kursprojekt schlug **Minimax mit Aktionsfilterung** sowohl MCTS als
auch DQN; der explizite Befund war, dass der Aktionsraum fuer das lernende
Verfahren zu gross war. Progressive Unpruning/Widening ist die
zurueckhaltende Variante: fruehes Beschneiden, spaeteres Wiederzulassen.

`[GEPRUEFT-anderswo]` Das deckt sich mit dem eigenen v2-Befund (Memory
`project_heuristic_v2_teacher`): der Durchbruch kam vom **Platzierungs-Routing**,
nicht von neuen Bewertungstermen. Die Literatur sagt also: das war kein
Zufall, sondern die Regel.

### 4.5 Relaxationsheuristiken: die formale Fassung der "Machbarkeitshuelle"

`[EXTERN]` Die Planungsliteratur baut Heuristiken nicht durch Raten, sondern
durch **Vereinfachen des Problems und exaktes Loesen der Vereinfachung**:
Delete-Relaxation (h+, h_max, h_add, Relaxed Planning Graph) und
Pattern-Databases (Abstraktion auf Teilvariablen, disjunkt additiv
kombinierbar). Ergebnis ist eine Schaetzung mit bekannter Richtung
(zulaessig = nie zu teuer).

`[HERLEITUNG]` Genau diese Bauart passt auf den gemessenen Strukturbefund
"Champion vollendet keine Spalten" (Memory
`project_column_completion_structural_weakness`): die Frage "ist diese Spalte
ueberhaupt noch vollendbar?" ist ein Erreichbarkeitsproblem ueber
Restversorgung (Beutel/Turm/Fabriken), Restplatten (Farbzellen je Slot) und
Restrunden. Eine Relaxation, die Reihenfolge und Gegnerzugriff ignoriert und
nur Zaehlbarkeit prueft, ist exakt loesbar und liefert ein Feature mit klarer
Semantik – und, wichtiger, einen **Aktionsfilter** nach 4.4: Zuege, die in
eine nachweislich unvollendbare Spalte investieren, koennen ausgeschlossen
oder abgewertet werden. Die bestehende Dreiecks-Machbarkeitshuelle aus dem
v2-Strang ist die grobe Vorstufe davon.

**Praezisierung, gemeldet von der Parallelsitzung am 2026-08-25** (deren
Messung, hier NICHT nachgeprueft, Prereg `PREREG_heuristic_v2_long_rows.md`
par.8.4-9.2): die Relaxation traegt als **Filter** (`cell_is_completable`
schneidet unerreichbare Zielzellen), nicht als **Zielfunktion**. Zwei
gerechnete Punktekarten als Routing-Ziel fielen negativ aus, beide mit
derselben Signatur: Teilspalten >= 3 steigen, volle Spalten fallen. Deutung
der Sitzung: eine additive Punktekarte ist ein BREITEN-Signal, waehrend eine
volle Spalte eine Vorgabe braucht, die dem lokalen Punktgradienten
widerspricht. Das passt zur Merkmalsliste in Abschnitt 6a: der staerkste
bekannte Azul-Agent fuehrt "groesstes Potenzial, eine noch nicht vollendete
Spalte zu vollenden" als EIGENEN Term mit eigenem Phasengewicht, nicht als
Punktesumme.

### 4.6 Potentialbasiertes Shaping, wenn Belohnung spaet kommt

`[EXTERN]` Die einzige Form von Zusatzbelohnung, die die optimale Politik
nachweislich nicht verschiebt, ist die potentialbasierte:
`F(s, s') = gamma * Phi(s') − Phi(s)`. Alles andere kann die Rangfolge der
Politiken kippen.

`[HERLEITUNG]` Relevant, weil im Repo bereits ein Formungsterm haengt
(`scoring.rs`, Memory `project_wertung_progress_nur_heuristik`) und weil jeder
kuenftige "Spaltenfortschritt"-Bonus dieselbe Falle stellt. Wer so etwas
einbaut, sollte es in der Potentialform bauen; dann ist die Frage "verzerrt
das mein Optimum?" beantwortet, bevor sie gestellt wird.

### 4.7 Afterstates: den Zufall aus der Bewertung heraushalten

`[EXTERN]` Die 2048-Linie (Szubert/Jaskowski, danach Multi-Stage-TD und
Delayed Temporal Coherence) bewertet nicht den Zustand, sondern den
**Afterstate**: den Zustand nach der eigenen Aktion, aber vor dem Zufall. Die
Messung dort war eindeutig – die Afterstate-Variante schlug Zustands- und
Aktionswerte deutlich. Zweiter Baustein dort: **N-Tupel-Netze**, also viele
kleine Musterfenster statt eines globalen Modells; dritter: **Multi-Stage-TD**,
getrennte Gewichte je Spielabschnitt.

`[HERLEITUNG]` Uebertragung auf Mosaic: der Zug (Steine nehmen, Reihe waehlen)
ist deterministisch, die Neubefuellung ist der Zufall. Ein Bewerter, der
konsequent auf dem Afterstate arbeitet, muss die Refill-Verteilung nicht
mitmitteln – das ist dieselbe Diagnose, die `round_transition.rs` im eigenen
Modulkopf stellt, nur von der Zielseite her statt von der Suchseite.

**Rueckmeldung der Parallelsitzung, 2026-08-25** (deren Messung, hier NICHT
nachgeprueft, `PREREG_heuristic_v2_long_rows.md` par.9.1/9.2): ihre beiden
Punktekarten SIND Afterstate-Bewertungen – eine Zelle wird probeweise belegt
und der Zustand danach bewertet – und beide haben verloren, je n=160 gegen die
Prio-Leiter: volle Spalten 0,650 auf 0,281 (Plattenanteil) bzw. 0,762 auf
0,219 (zusaetzlich Platzierungspunkte).

**Die Reichweite dieses Befunds ist eng, und die Verwechslung waere teuer:**
er entscheidet ausschliesslich ueber die Verwendung einer Afterstate-Bewertung
als **Routing-ZIEL** – also als Karte, die sagt, welche Zelle als naechstes
angesteuert wird. Der 2048-Befund betrifft eine andere Groesse, naemlich das
**Lern-TARGET des Wertkopfes** (bewerte den Nach-Aktions-Zustand statt des
Zustands, um die Zufallsverteilung nicht mitmitteln zu muessen). Beides
Afterstates, aber an verschiedenen Stellen der Maschine; aus "Afterstate-Karte
taugt nicht zum Routen" folgt NICHTS ueber "Afterstate-Ziel taugt nicht zum
Lernen". Die 2048-Uebertragung oben bleibt davon unberuehrt.

### 4.8 Hilfsziele (KataGo)

`[EXTERN]` KataGo meldet, dass das Entfernen der Hilfsziele (Ownership,
Score) die Lerneffizienz sichtbar senkt, und dass Playout-Cap-Randomisierung
fixe Playout-Zahlen schlaegt, weil sie die Spannung zwischen Value- und
Policy-Ziel aufloest.

`[GEPRUEFT-anderswo]` Im eigenen Projekt ist beides bereits gemessen und
faellt anders aus: Ownership-Gewicht ohne belegten Staerkeeffekt (Memory
`project_ownership_head_closed`, n=6/p=0,22, also kein Beleg in beide
Richtungen) und PCR negativ (Memory `project_pcr_ab_result`, beide
Orakel-Metriken 0/6). Der Punkt hier ist nicht "nochmal probieren", sondern:
die externe Evidenz ist aera-abhaengig, und die eigene Messung sticht sie.

---

## 5. Spielstrategie: was extern ueberhaupt zu holen war

`[EXTERN]` Aus Rezensionen und Regelhilfen, alles qualitativ:

* **Mond-Stapel-Patt.** Mehrere Rezensenten beschreiben dieselbe Kernspannung:
  unter einer Schicht liegt ein grosser gleichfarbiger Vorrat, und beide
  Spieler vermeiden es, ihn freizulegen. Wer die Reihenfolge beim Abraeumen
  der Sonnenseite festlegt, baut diese Sperre. Das ist die Stelle, an der die
  Aufdeckungs-Steuerung aus Abschnitt 1 spielerisch sichtbar wird.
* **Plattenknappheit.** Drei offene Platten, vier Platzierungen je Runde – die
  Rezensionen nennen das als bewusste Verknappung. Deckt sich mit der
  Herleitung in Abschnitt 3.
* **Chips als Pivot.** Bonuschips gelten als Ausgleich fuer entgleiste
  Draftplaene, nicht als eigener Plan.
* **Startspielerstein als Sabotage.** Den Gegner in den Stein zu zwingen, gilt
  als legitimes Mittel; −2 ist der Preis.
* **Strafleiste ist kleiner als im Grundspiel** (4 Plaetze, maximal −10 statt
  7 Plaetze/−14). Das deckt sich mit `docs/engine_manual.md` §2/§4.

`[EXTERN]` Aus der Azul-Grundspiel-Strategieliteratur, uebertragbar dem Sinn
nach: kurze Reihen zuerst; **"faengt keine lange Reihe an, die ihr nicht in
zwei Runden fertig bekommt"**; Strafleiste als Waehrung, nicht als Unfall;
Spalten sind mehr wert als Zeilen (im Grundspiel Faktor 3,5, hier laut
Regelwerk 7 gegen 3 Punkte); im Zweipersonenspiel ist Verweigerung
("hate drafting") stark, weil eigener Punkt und verweigerter Gegnerpunkt
denselben Wert haben.

**Achtung bei einer Zahl.** Ein Strategie-Blog behauptet, Spieler mit im Mittel
unter 2 Strafsteinen je Runde haetten eine "65 % hoehere Siegquote". Diese Zahl
hat keine Quelle und keine Methode; sie ist hier nur festgehalten, um sie
ausdruecklich als **nicht verwendbar** zu markieren.

`[GEPRUEFT-anderswo]` Interessant ist die Beruehrung mit dem eigenen Befund
(Memory `project_long_row_avoidance_is_correct`): der externe Rat ist eine
BEDINGTE Regel ("nur anfangen, wenn vollendbar"), waehrend das B1-Experiment
die Initiierung erzwungen hat, ohne die Vollendungsfaehigkeit zu aendern. Die
externe Faustregel widerspricht dem Projektbefund also nicht, sie benennt
dieselbe Bedingung von der anderen Seite: der Engpass ist die Vollendung.

---

## 6. Uebernahme-Kandidaten, nach Beitrag zum Leitstern sortiert

Alles `[HERLEITUNG]`, nichts davon gemessen.

1. **Vollendbarkeits-Relaxation als Feature UND Filter** (4.5). Trifft den
   gemessenen Strukturengpass direkt, ist exakt rechenbar statt gelernt, und
   wirkt nach der Literatur an der Stelle mit dem besten Hebel-Kosten-
   Verhaeltnis (Aktionsraum statt Bewertung).
2. **Reservationswert-Regel fuer die Blindziehung** (Abschnitt 3). Kleiner,
   abgeschlossener Baustein mit exakter Loesung; betrifft ein Pflichtereignis
   mindestens viermal je Partie.
3. **Rundenabhaengige Parametrisierung nach Tapered-Eval-Vorbild** (4.1).
   Die Phasenstruktur ist gegeben und wird bisher nicht systematisch
   ausgenutzt.
4. **Robuste Aggregatoren am Rundenuebergang** (Median, gestutztes oder
   winsorisiertes Mittel statt des arithmetischen), falls
   `ROUND_TRANSITION_SAMPLING` je wieder eingeschaltet wird -- der billige
   Zusatz aus 6a. Beruehrt NICHT die Determinisierungs-Frage, siehe unten.
   **Zugehoerige Vorregistrierung existiert inzwischen**:
   `evaluations/PREREG_round_transition_search_sampling.md` (nicht von dieser
   Spur angelegt) fragt, ob das Bemustern ueberhaupt Staerke bringt. Der
   Aggregator-Punkt ist dort eine Variante innerhalb der Frage, kein eigener
   Kandidat -- wer ihn aufgreift, gehoert in jene Prereg und nicht hierher.

**Zwei Streichungen am 2026-08-25**, beide, weil der Kandidat gegen den
Bestand ungeprueft war:

* "SPRT auf Blockebene fuer das Gating" -- gegenstandslos,
  `tools/paired_gating.py` faehrt das seit laengerem auf informativen Paaren
  (Korrektur in 4.3).
* "Feste Determinisierungen statt Neumischung" -- die Frage ist in
  `PREREG_ismcts_determinizations.md` ENTSCHIEDEN und negativ; das Mitteln
  ueber gezogene Welten schadet gemessen (Korrektur in Abschnitt 2).

**Registriert am 2026-08-25**: Kandidat 2 (Reservationswert-Regel) hat eine
eigene Vorregistrierung bekommen,
`evaluations/PREREG_stack_draw_reservation_rule.md`, mit einer ausdruecklichen
Abgrenzung gegen `PREREG_chance_nodes.md` Teil B1 (Suche) und
`PREREG_stack_top_feature.md` (Merkmale). Stufe 1 dort ist reine
Korpus-Auswertung ohne Arena-Budget.

---

## 6a. Der einzige ernsthafte Vorgaenger: Rzepecki 2025 (NNUE fuer Azul)

Nachtrag 2026-08-25, nachdem der Nutzer das PDF unter
`docs/Rzepecki2025ImplementingSuperhuman.pdf` abgelegt hat. Alles hier ist
`[EXTERN]`, aber im Volltext gelesen, mit Seitenangabe.

**Ergebnis zuerst.** Der Agent erreichte auf Board Game Arena Platz 1 in beiden
Ranglisten (Allzeit-Elo 1173, Saison-Elo 2340, beides neue Rekorde), Siegquote
ueber 99 % gegen den Schnitt, und gegen einen Top-5-Spieler zwei Siege und ein
Remis (S. 106). Die Community hielt ihn fuer einen Bot und diskutierte das
oeffentlich. Der Anspruch "uebermenschlich" ist damit belegt, nicht behauptet.

**Minimax schlaegt MCTS deutlich** (S. 35): die MCTS-Agenten "performed very
poorly", ohne erkennbare Strategie. Begruendung der Autoren: eine
Zufallspartie ist eine sehr schlechte Wertschaetzung, weil typischerweise ein
oder zwei Zuege gut und alle anderen deutlich schlechter sind. **Wichtige
Einschraenkung fuer uns:** das ist MCTS mit ZUFALLS-Playouts, nicht
netzgefuehrtes MCTS mit Blattbewertung. Der Befund trifft Mosaics Aufbau also
nicht direkt – er sagt nur, dass die Blattbewertung in diesem Spiel alles ist.

**Die Heuristik-Bauart ist genau die aus Abschnitt 4.1** (S. 39): lineare
Kombination extrahierter Merkmale, und die **Koeffizienten haengen von der
Spielphase ab** (`gamePhase` = Rundenindex). Tapered Eval ist in diesem Spiel
also nicht nur uebertragbar, sondern beim staerksten bekannten Agenten gebaut.
Die Merkmale der besten Handheuristik (Nr. 11, S. 39-40) enthalten unter
anderem: mehrere Terme fuer die drei oberen Zeilen, "jedes Paar Steine in den
zwei unteren Zeilen in derselben Spalte", "jede nicht leere Zeile, die einmal
voll die unteren zwei Zellen einer Spalte schliesst", "**das groesste Potenzial,
eine noch nicht vollendete Spalte zu vollenden**", "keine Steine derselben Farbe
in verschiedenen Zeilen", Startspielerstein, genommene Steine, plus den
Endstands-Wert. Die Spalten-Terme tragen ihr hoechstes Gewicht in den mittleren
Runden (gamePhase 2 und 3). **Das ist die direkte externe Bestaetigung, dass
Spaltenvollendung ein eigenstaendiger, phasenabhaengiger Bewertungsterm sein
muss** – nicht ein Nebenprodukt der Endwertung.

**Gewichte automatisch abstimmen: probiert und aufgegeben** (S. 39). Ein
genetischer Algorithmus auf den Koeffizienten "required a lot of computational
power and did not seem to give a lot of improvement". Das daempft Abschnitt 4.2:
die Black-Box-Familie war hier konkret nicht der Hebel.

**Chance-Nodes: `branching` mit robusten Aggregatoren** (S. 37-38). Die neuen
Steine werden vor der Suche vorbereitet; zwei Parameter steuern das:
`branchingFactor` (Zahl der gezogenen Varianten) und `branchingMethod` mit den
Werten Median, arithmetisches Mittel, gestutztes Mittel und winsorisiertes
Mittel. **Mosaic mittelt in `round_transition.rs` arithmetisch** – die robusten
Varianten sind dort nicht vorgesehen und waeren ein billiger Zusatz, falls
`ROUND_TRANSITION_SAMPLING` je wieder eingeschaltet wird.

**Varianzreduktion an der Neubefuellung** (S. 38, S. 102). Drei Politiken:
`random`, `semirandom` (Farbmengen auf ihren Erwartungswert gesetzt, dann
zufaellig auf die Fabriken verteilt) und `evenly` (zusaetzlich gleichmaessige
Verteilung). Der finale Agent benutzt `semirandom`; die Autoren folgern, eine
gute Simulation der Ziehung solle die wichtigen Merkmale nahe am Erwartungswert
haben, aber die Verteilung auf die Fabriken zufaellig lassen.
**Vorsicht mit dieser Zahl:** das zugehoerige Duell steht auf 49,29 % mit CI
[48,35 %, 50,22 %] (Tabelle 8.4) – das Intervall enthaelt 50 %. Die
Schlussfolgerung der Arbeit ist an dieser Stelle **statistisch nicht gedeckt**,
auch wenn die Richtung plausibel ist.

**Suchtiefe zahlt sich massiv aus** (Tabelle 8.5, S. 104): 0,1 s gegen 1 s
ergibt 25,06 %, 1 s gegen 5 s 34,02 %, 5 s gegen 20 s 38,27 %. Auch mit einer
starken gelernten Bewertung bleibt die Suche der groesste Einzelhebel – die
Autoren schliessen daraus selbst, ihr Agent sei "far from the optimal one".

**Architektur-Detail mit Uebertragungswert** (S. 42): Clipped ReLU funktioniert
in Azul nicht, weil das Abschneiden die Groesseninformation zerstoert, und
Punkte sind in diesem Spiel die Sache selbst. Verwendet wurden ReLU zwischen
den Schichten und Tanh am Ausgang. Trainiert wurde auf dem Partieergebnis
(−1/0/1); die Autoren nennen als offene Idee, stattdessen die Punktedifferenz
zu nehmen (S. 117) – in Mosaic laengst gebaut.

**Spielstrategie, die der Agent selbst zeigt** (S. 112-116, 36.608
Selbstspiel-Partien): der Startspieler gewinnt 58,32 % der Partien, und ein
Ausgleich von **1,5 Punkten** fuer den Nachziehenden bringt das auf 50,02 % –
eine saubere Zahl fuer den Wert des Anzugs. Der Sieger ist in allen Statistiken
besser ausser einer: er verliert in Runde 1 MEHR Punkte an die Strafleiste
(1,39 gegen 1,12). Fruehes Opfern zahlt sich also aus. Eroeffnung: er entwickelt
Zeile 3 und 4 und baut damit auf eine der drei MITTLEREN Spalten hin. Den
Startspielerstein nimmt er bevorzugt in Runde 4, um Runde 5 zu eroeffnen, und
meidet ihn in Runde 5.

**Was die Arbeit als naechstes vorschlaegt und uns betrifft** (S. 118-119):
Zugsortier-Heuristiken ("Create heuristics that would assign values to moves, so
that we can sort them"), eine Heuristik, die die drei Teile eines Zuges getrennt
vorschlaegt, und – ausdruecklich als vermuteter Engpass – ein besseres
Verstaendnis davon, **wie neue Ziehungen in der Suche simuliert werden sollten**.
Ausserdem der Vorschlag, neue Strategien zu finden, indem man denselben Agenten
gegen sich selbst spielen laesst und einer Seite eine Zugpraeferenz aufzwingt –
also genau das Vorzugs-Verfahren, das hier in `plate_builder.rs` steht.

## 7. Quellen

Spiel und Strategie:
Board Game Arena, Gamehelpazulduel ·
Meeple Mountain, Azul Duel Review ·
Opinionated Gamers, Dale Yu Review ·
Tabletopping, Azul Duel vs Azul ·
azultiles.com, Azul Strategy Guide (Blog, unbelegt)

Methodik:
Chessprogramming Wiki: Evaluation, Automated Tuning, Texel's Tuning Method,
Sequential Probability Ratio Test ·
Long, Sturtevant, Buro, Furtak, *Understanding the Success of Perfect
Information Monte Carlo Sampling in Game Tree Search*, AAAI 2010 ·
Frank, Basin, Matsubara 1998 (strategy fusion, non-locality) ·
Lanctot et al., *Monte Carlo `*`-Minimax Search*, IJCAI 2013 ·
Swiechowski et al., *MCTS: a review of recent modifications and applications*,
Artif Intell Rev 2022 ·
Szubert, Jaskowski, *TD Learning of N-Tuple Networks for the Game 2048*,
CIG 2014; Jaskowski, *Mastering 2048 with Delayed Temporal Coherence Learning*
(arXiv 1604.05085) ·
Wu, *Accelerating Self-Play Learning in Go* (KataGo, arXiv 1902.10565) ·
Ng, Harada, Russell (potentialbasiertes Shaping), rezipiert in
*Potential-based Reward Shaping in Sokoban* (arXiv 2109.05022) ·
Helmert/Hoffmann-Linie zur Delete-Relaxation (Lehrmaterial Basel/Saarbruecken)
·
Piette et al., Ludii: *General Board Game Concepts* (CoG 2021),
*General Game Heuristic Prediction Based on Ludeme Descriptions*
(arXiv 2105.12846) ·
Clune, *Heuristic Evaluation Functions for General Game Playing*, AAAI 2007 ·
Weitzman 1979, Pandora's Box; Uebersicht *Recent Developments in Pandora's Box
Problem* (arXiv 2308.12242) ·
kaiyoo/AI-agent-Azul-Game-Competition (COMP90054-Kursprojekt)
