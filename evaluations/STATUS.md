# Mosaic-AI – Status & Fahrplan

**Hier steht nur AKTUELLES und OFFENES.** Abgeschlossenes liegt in
**`../archive/history.md`**.

---

## DAS ZIEL (Leitstern – Nutzer-Auftrag 2026-08-17: bei jeder Priorisierung im Kopf behalten)

> *"das netz spielt die basis an sich schon gut, aber nimmt keine ruecksicht auf
> die wertungsplatten. das wollen wir via injektion -> selfplay -> ownership
> head in den griff bekommen. dann sind nochmal je partie 10 punkte und mehr
> drinnen"*

1. **Ziel: ein staerkerer Spieler**, gemessen am **direkten Duell** gegen den
   Champion. Zielgroesse: **"Sieg mit vielen Punkten"** – nicht Punkte allein.
2. **Hebel: der Plattenblick.** Die Grundmechanik spielt das Netz kompetent und
   laesst 10+ Punkte je Partie liegen.

**Klausel, die schon sechs Vorschlaege aussortiert hat:** ein Plattenzuwachs,
der Siege kostet, ist KEIN Erfolg. Ein Zuwachs bei den Zaehl-Kriterien (k3/k4)
zaehlt nicht – gefragt sind die konjunktiven k1/k2/k5.

**Vor jeder Arbeit fragen: was traegt das dazu bei?** Ownership-Kopf, Korpus,
Regler, Konjunktionsterme, LR-Schedules, Traeger-Manifeste sind WERKZEUG ohne
Eigenwert. Am 2026-08-17 wurde ein Legacy-Test gestrichen, weil die Antwort auf
diese Frage "nichts" war.

---

## FOKUS-REGEL: NUR k1 (Nutzer-Entscheid 2026-08-18)

> *"mir kommt vor du switcht wild zwischen den wertungsplatten analysen herum.
> wir sollten uns wirklich mal nur auf eine wertungsplatte fokussieren"*

**Bis auf Widerruf wird ausschliesslich k1 (Vertikale Reihen, 7 Pkt je volle
Spalte) bearbeitet.** Warum k1 und nicht eine andere – alles gemessen:

| | |
|---|---|
| Wert | 7 Punkte je Spalte, 6 Geometrien |
| Kosten | **keine** – innerhalb des k1-Bauer-Arms +7,86 Gesamtpunkte, davon 7,02 aus der Platte, Rest +0,84 |
| Synergie | Platzierung zahlt den vertikalen Lauf getrennt (`round_end.rs:366`), Spaltenbau liegt auf derselben Achse wie normales Spiel |
| Luecke | Netz 20/156 Partien (13 %), Bauer 419/1000 (42 %) |
| Label | Vollendbarkeits-Sperre bestanden, traegt in Runde 3-5 |

**Was das AUSSCHLIESST**, obwohl dazu Befunde vorliegen: k2 (Diagonalen), k4
(Aeussere Felder), k5 (Eckplatten), k6 (Spezialfelder). Ihre Messungen bleiben in
den Preregs erhalten und gelten weiter, werden aber **nicht weiterverfolgt**. Erst
wenn k1 traegt, kommt k2 – so war es in
`PREREG_plate_policy_supervision.md` registriert und so bleibt es.

**Konkret heisst k1-only:**

- Erfolgsregeln nennen nur k1. (Die registrierten "k1 oder k2"-Klauseln bleiben
  gueltig, werden aber auf k1 gelesen – die strengere Lesart.)
- Der Verbraucher wird nur mit `MOSAIC_OWNERSHIP_GEW` auf k1 gefahren.
- Nebenbefunde zu anderen Kriterien werden protokolliert und NICHT verfolgt.

**Der Anlass war Drift, nicht Erkenntnis:** am 2026-08-18 sind aus k1-Messungen
heraus Analysen zu k6 (Spezialkuppel-Platzierung, Stapel-Ziehungen), k5 und k4
entstanden. Alle drei lieferten echte Befunde – und keiner davon brachte k1 voran.

---


## STAND JETZT (2026-08-24)

**Champion unveraendert:** `v21_2d_brierbest`, Elo **1215** [1170, 1259]
(neue R5-Fix-Leiter). Kanten ueber die Fix-Grenze nie mischen.

### LAUFEND: Heuristik v2 als ZUSAETZLICHER Lehrer

`PREREG_heuristic_v2_long_rows.md` -- **der aktive Strang.** Anlass ist eine
geschlossene Ursachenkette: der Champion vollendet keine Spalten, und der
Grund ist NICHT fehlende Versorgung, sondern Verteilung. Eine volle Spalte
kostet 21 Zellen; das Netz verbraucht 42,7 Zellen und truege damit
gleichverteilt 2,03 Spalten statt 0,10.

Zwei Vorfragen sind beantwortet und schliessen die billigeren Wege aus:

- **Der Lehrer kann es auch nicht** (407 Partien, Netz@400 gegen
  Heuristik@150): volle Spalten 0,098 gegen 0,101, Vollendungsquote 0,563
  gegen 0,538. Destillation scheidet aus -- es gibt nichts zu uebertragen.
- **Such-seitig ist der Weg zu**: `PREREG_scoring_plate_injection` (Sweep
  ueber 30-fachen Dosisbereich) und `PREREG_long_row_payoff` B1 sind beide
  negativ entschieden.

**Gebaut und gemessen** (v1 gegen v2, je 80 gepaarte Partien, beide Sitze):

| Bauschritt | volle Spalten | volle Zeilen |
| --- | --- | --- |
| v1 (Anker) | 0,163 | 0,438 |
| Routing (Draft + Tiling) | 0,362 | 0,250 |
| + plattenunabhaengiger L-Wert | 0,438 | 0,400 |
| + gestreute Start-Ecke | 0,450 | 0,263 |
| + Kuppelplatten-Wahl | 0,588 | 0,200 |
| + Zielspalte ab Runde 3 festgenagelt | 0,562 | 0,200 |

Das Festnageln wirkt in der VERTEILUNG, nicht im Mittelwert: Partien mit
mindestens einer vollen Spalte **35 auf 50 Prozent** (Hoehe 4/6 von 14 auf 8,
6/6 von 28 auf 40). Die 5/6-Mauer ist durchbrochen (max Hoehe 4,65 auf 5,40).

**Der Durchbruch kam nicht von einem Bewertungsterm, sondern vom
Platzierungs-Routing.** `best_first_step_inner` waehlt nach reinen
Sofortpunkten (`tiling_solver.rs:49-56`) und warf jede Draft-seitige Absicht
wieder weg -- derselbe Kernbefund steht in `PREREG_provocation.md` ("der
Engpass ist die PLATZIERBARKEIT, nicht die Plattenbewertung"). Neu gebaut
wurde fast nichts: das vorhandene Plattenbauer-Sortiment hat die generische
Zellen-Mechanik mit genau den drei Entscheidungspunkten, alle ohne Netz. v2
liefert nur die Zellenliste.

**Alles variantengebunden** (`mcts::HeuristikVariante::{V1,V2}`), nicht ueber
`MOSAIC_SPALTENBAU`/`MOSAIC_PLATTENBAU` -- beide Knoepfe sind prozessweit und
damit fuer eine Partie v1 GEGEN v2 unbrauchbar. **Der Anker ist unberuehrt:**
alle Bestandssignaturen laufen ueber V1, Paritaets-Hash `8c6684ff...` haelt,
Suite 512/0.

**OFFEN an v2:**

**SCHRITT 3 IST DURCH (2026-08-24): Faehigkeit belegt, Preis hoch, URTEIL
STEHT AUS.** 407 Kampagnen-Seeds je Arm, Champion@400 gegen Heuristik@150,
mit v1-Bezug auf denselben Seeds:

| | Siege | Punkte | Marge | volle Spalten | Vollendungsquote | max Hoehe |
| --- | --- | --- | --- | --- | --- | --- |
| v1 (Bezug) | 0,256 | 37,6 | -12,2 | 0,086 | 0,564 | 4,58 |
| **v2** | **0,128** | 34,8 | **-19,4** | **0,302** | **0,686** | 5,08 |

Gepaart gegen das Netz (16 Bloecke): volle Spalten +0,175 (t=+7,79), Punkte
-19,610 (t=-18,94), Siege -0,755 (t=-20,09), Strafpunkte +7,567 (t=+11,83).

v2 baut **3,5-mal so viele volle Spalten** wie v1 und hebt die
Vollendungsquote von 0,564 auf 0,686 -- die B1-Vorgabe ("deutlich ueber
0,53") ist erfuellt. Erstmals gibt es damit einen Agenten im System, der
lange Reihen nicht nur anfaengt, sondern zu Ende bringt. Der Preis: die
Siegquote gegen den Champion halbiert sich (25,6 auf 12,8 Prozent).

**Die ZEILEN-Regression ist kleiner als angenommen.** Gegen ein NETZ brechen
die vollen Zeilen nicht ein (0,403 gegen 0,432). Der Absturz auf 0,200 war
ein Artefakt des v1-gegen-v2-Aufbaus, in dem beide Seiten um dieselbe
Zellenmenge konkurrieren. Im Selbstspiel-Aufbau bleibt der Posten offen, fuer
den Lehrer-Einsatz ist er entschaerft.

**OFFEN an v2:**

1. **URTEIL zu Schritt 3** -- Nutzer-Entscheid. par.5.3 hat bewusst KEINEN
   Schwellenwert vorregistriert. Die Abwaegung: ein Korpus mit 3,5-mal mehr
   Spaltenvollendungen (der Faehigkeit, die im System nirgends vorkommt und
   die weder Destillation noch vier Such-Eingriffe erzeugen konnten), erkauft
   mit einem Erzeuger auf 12,8 Prozent Siegquote. Ob das ein guter Tausch
   ist, haengt daran, ob das Netz die FAEHIGKEIT uebernimmt, ohne das NIVEAU
   mitzuuebernehmen -- das ist par.5.4 und mit dieser Messung nicht
   beantwortet, sondern erst gestellt.
2. **Self-Play-Einstieg** (Nutzer-Freigabe 2026-08-24, NICHT gebaut): v2
   existiert bisher nur in Arenen. Ohne Korpus-Erzeuger haben weder der
   Shaping-Kopf noch eine 2D-Erweiterung Trainingsmaterial. Braucht eine
   eigene Korpus-Kennung, sonst ist das Fenster still gemischt und keine
   spaetere Auswertung kann die Arme trennen. Die Verdrahtung ist vorbereitet:
   `PlayerLoopConfig` traegt bereits das Feld `heuristik_variante` (an allen
   acht Bestandsstellen auf `V1`).
3. **Abstand zum Ziel**: 0,562 volle Spalten im Heuristik-Duell gegen die vom
   Nutzer geforderte 1,0.
4. **NEUER ARM `V2Huelle` -- GEMESSEN 2026-08-25, ARM GEWINNT**
   (`PREREG_heuristic_v2_long_rows.md` par.8). Die Prio-Leiter des Nutzers
   als Routing-Huelle: eigene Variante, Bewertung byte-identisch zu `V2`,
   nur die Zielzellen-Karte unterscheidet sich. Prio 3 Randspalte, Prio 4
   zweite Spalte (Spezialfliese auf Rasterzeile 5), Prio 5 Spezialfeld
   freischalten und Joker halten, Prio 6 obere Zeilen, Prio 7 Nachbarn
   (aufgeweicht bei aktiver Diagonale). Drafting als LINEARER Score mit
   Strafleisten- und Stoerungsterm (`provocation::floor_line_growth` /
   `disruption_score`, beide Bestand) und Phasen-Eskalation `[1,2,4,8]`.
   Suite 520/0, Paritaets-Hash `8c6684ff` haelt.

   **Ergebnis (par.8.5, n=160, `v2_envelope_arena.json`):** volle Spalten
   0,425 auf **0,950** (t=9,12 auf 10 Bloecken), Spezialfeld-Freischaltungen
   0,713 auf **1,512** (t=9,32), Strafpunkte -15,0 auf -13,4, eigene Punkte
   40,1 auf **48,2** (t=4,80), Siegquote im direkten Duell **0,706**,
   Vollendungsquote 0,743 (B1-Waechter erfuellt). Die Reihenauslastung
   verschiebt sich genau in die Zielrichtung (Rasterzeile 3/4/5:
   +0,32/+0,68/+0,21). **Erster v2-Bauschritt ueberhaupt, der Spalten NICHT
   mit Punkten bezahlt** -- alle vier vorherigen taten es, Schritt 3 hat die
   Siegquote gegen den Champion halbiert.

   **Ablationen (par.8.6):** Struktur und Staerke haengen an verschiedenen
   Bausteinen. Die Spalten kommen aus der ZIELKARTE (bleiben bei 0,506-0,525
   ohne Stoer- und Strafterm); nur die Prio-5-Auflage bewegt sie (-0,10). Die
   Marge zerfaellt in `W_STRAF` 5,09, Prio-5 2,59, `W_STOER` 2,56. Ohne
   `W_STRAF` dreht die Strafleiste ins Negative (-1,44). Kontrolllauf nach
   dem Zurueckbauen reproduziert exakt.

   **Zwei Punktekarten als Alternative zur Leiter: BEIDE NEGATIV**
   (par.9.1/9.2, je n=160 gegen die Huelle). `V2Heatmap` (Plattenanteil aus
   `scoring_progress`): volle Spalten 0,650 auf 0,281, Siegquote 0,463.
   `V2PointMap` (dazu die Platzierungspunkte nach Linienlaenge): 0,762 auf
   0,219, Siegquote 0,400. Beide zeigen dieselbe Signatur -- Teilspalten >= 3
   STEIGEN (+0,375 / +0,325), volle Spalten und maximale Hoehe fallen, und die
   Strafpunkte werden besser (+2,4 / +2,7).

   **Der Befund dahinter ist allgemein und gilt fuer kuenftige Arme:** eine
   gerechnete Punktekarte ist ein BREITEN-Signal und erzeugt den besseren
   Greedy-Spieler bei schlechterem Bau. Volle Spalten verlangen eine Vorgabe,
   die dem lokalen Punktgradienten WIDERSPRICHT -- das leistet die
   handgesetzte Leiter, keine der beiden Karten. Zwei Hypothesen von mir sind
   dabei im Vorzeichen widerlegt worden (k1-Abhaengigkeit in par.9.1, Fokus
   durch Superadditivitaet in par.9.2). **Die Netz-Verwendung als
   Eingabeebene ist davon NICHT beruehrt** (Nutzer-Absicht 2026-08-25: die
   Karte war fuers Netz gedacht) -- ein Netz kann aus einem Breiten-Signal
   Fokus lernen, ein Greedy-Routing nicht.

   **LEHRER-TEST DURCH (par.10.1, 2026-08-25, 407 Kampagnen-Seeds je Arm,
   Champion@400 gegen Heuristik@150, 2.610 s bei 11 Threads): DIE HUELLE
   SCHLAEGT v1 UND v2.**

   | | Siege | Punkte | Marge | volle Spalten | Vollend. | Strafpkt | volle Zeilen |
   | --- | --- | --- | --- | --- | --- | --- | --- |
   | v1 | 0,256 | 37,6 | -12,2 | 0,086 | 0,564 | 19,3 | 0,432 |
   | v2 | 0,128 | 34,8 | -19,4 | 0,302 | 0,686 | -- | 0,403 |
   | **Huelle** | **0,373** | **47,1** | **-5,5** | **0,798** | **0,717** | **13,6** | 0,216 |

   Gepaart gegen das Netz (16 Bloecke): volle Spalten +0,700 (t=+13,73),
   Punkte -5,468 (t=-5,46), Siege -0,245 (t=-5,67). Das Netz selbst kommt auf
   0,106 volle Spalten.

   **Der Tausch ist aufgehoben.** v2 hat Faehigkeit mit Niveau bezahlt; die
   Huelle liefert 2,6-mal so viele volle Spalten wie v2 UND fast die
   dreifache Siegquote, dazu 9,5 Punkte mehr als v1 und 5,7 Strafpunkte
   weniger. **Damit ist die Voraussetzung von par.3b erstmals erfuellbar:**
   ein Lehrer, der die Dreiecksform erzeugt, ohne schwaecher zu sein als der
   bisherige Anker.

   **Der Preis, und er ist echt:** volle Zeilen 0,432 auf 0,216. Anders als
   bei v2 (dort war der Einbruch ein Artefakt des v1-gegen-v2-Duells, gegen
   ein Netz blieben 0,403) misst hier derselbe Netz-Aufbau die Haelfte. Bei
   7 Punkten je Spalte gegen 3 je Zeile ist der Tausch rechnerisch guenstig,
   gehoert aber bei jedem Nachfolgearm mitgemessen.

   **ELO EINGETRAGEN (2026-08-25):** `Heuristik_v2huelle@150` = **1125**
   [1069, 1186]. Die Kante kam aus dem Lehrer-Test selbst (407 Partien gegen
   `v21_2d_brierbest`@400, 255:152) -- keine zusaetzlichen Partien noetig,
   weil der Elo-Anker der Leiter genau diese Heuristik@150-Bedingung ist.
   Vertrags-Hash `a169ebf0a4451e08` identisch zur Leiter, also keine Kante
   ueber die Fix-Grenze.

   | Modell | Elo | 95%-KI |
   | --- | --- | --- |
   | v21_2d_brierbest@400 | 1215 | [1173, 1261] |
   | v20_2d_opp_brierbest@400 | 1186 | [1147, 1230] |
   | v19_2d_best@400 | 1136 | [1096, 1177] |
   | **Heuristik_v2huelle@150** | **1125** | [1069, 1186] |
   | Heuristik@150 | 1000 | Anker (fix) |

   **+125 Elo ueber dem Anker**, mit einer handgeschriebenen Heuristik bei 150
   Sims gegen Netze bei 400. **Nicht belegt** ist ein Vorsprung vor v19: das
   KI ueberlappt deutlich. Belegt ist der Abstand zum Anker und der Rueckstand
   von 90 Elo auf den Champion.

   Nicht eingetragen, aber verfuegbar: das ALTE v2 hat auf denselben
   Kampagnen-Seeds 0,128 Siegquote gegen den Champion (par.5.3). Eine Kante
   daraus wuerde v2 unter den Anker setzen und den Sprung sichtbar machen --
   die Laufbedingungen jener Messung sind aber nicht von mir verifiziert,
   deshalb nicht ungefragt nachgetragen.

   **par.11 GEMESSEN, H0** (par.11.1): rundenabhaengige Spalten-Gewichte
   bewegen nichts (volle Spalten +0,025, t=0,39; Siegquote 0,500). Der Arm ist
   negativ entschieden; ein Werte-Sweep findet NICHT statt (Dosis-Antwort,
   dreimal negativ entschieden). `SPALTEN_PHASE` bleibt im Code.

   **UEBERGABE-NOTIZ 2026-08-25:** Maschine und `self_play.rs` sind FREI
   (Commit `ae88cf3`, Suite 520/0, Paritaet haelt). Die Parallelsitzung
   `mosaic-ai-4f` wartete auf diese Freigabe fuer zwei Laeufe
   (Strafleisten-Tor Runde 2-4, dann ein netzfreier Gegentest zur
   Blindziehungs-Regel, Code bei ihr fertig) -- sie war beim Freigabezeitpunkt
   nicht mehr erreichbar (`ListAgents`: keine Agenten), die Nachricht kam
   nicht zu. Wer dort weitermacht, findet den Stand in
   `PREREG_stack_draw_reservation_rule.md`.

   **FRUEHERER STAND (par.10, jetzt erledigt):** Champion@400 gegen Huelle@150 auf den
   407 Kampagnen-Seeds, mit v1 als Bezug -- derselbe Aufbau wie par.5.3, damit
   die Zahlen nebeneinander stehen. `net_vs_heuristic_v2_arena` nimmt die
   Variante seit heute als Parameter. Das ist die Frage, an der der ganze
   Strang haengt: v2 hat Faehigkeit mit Niveau bezahlt (Siegquote 0,256 auf
   0,128), die Huelle tut das im Heuristik-Duell nicht.

   Nicht gebaut, weil schon vorhanden oder ohne Anknuepfungspunkt: Prio 0
   (Spiel endet nach genau 5 Runden, `game.rs:687`; Runde 5 laeuft ueber den
   eingefrorenen `round5_anchor` -- Expectiminimax mit Zufallsknoten und
   exaktem Blattwert, aber **kein geloestes Endspiel**: ~3 Halbzuege,
   Orakel-Uebereinstimmung 81,4 Prozent, `round5_anchor.rs:44-59`), Prio 1
   in der BEWERTUNG (`projected_unplaceable_penalty`, nur die Routing-Seite
   ist neu).

   **Offene Luecken aus dem Nutzer-Review 2026-08-25, alle geprueft:**
   `heuristic_v2.rs` koppelt seinen Saettigungsterm an KEINE Farbknappheit
   (0 Vorkommen, waehrend `column_build::cell_cost:287` die Knappheit ueber
   `scarcity_surcharge` einpreist); es gibt keinen Term, der FREIE
   Musterreihen als Puffer belohnt; und die **Mondstapel-Reihenfolge**
   (`Move::moon_order`) ist eine legale Wahl, die `generate_valid_moves`
   nie aufspannt (`validation.rs:183` emittiert genau eine kanonische
   Reihenfolge) -- der schaerfste variantenspezifische Stoerhebel liegt
   damit brach. Zum Moon-Order-Kopf siehe die Zeile in OFFENE
   ENTSCHEIDUNGEN.

**Vorregistriert, NICHT gebaut:** Shaping-Kopf statt Ownership-Kopf, der die
Dreiecks-Abweichung vorhersagt (par.3b) -- mit Abkling-Kurve zugunsten des
Value-Kopfes und ZWEI Kanaelen (volle Spalte links / rechts). Dazu die
Nutzer-Frage, die Einhuellende auch im 2D-Encoder als Eingabeebene sichtbar
zu machen. Beide brauchen erst das Korpus aus (2) -- sonst waeren sie auf
plattenblindes Spiel geeicht, derselbe Fehler wie viermal zuvor.

### Strukturbefunde, die weitergelten

- **Die Dreiecksform ist die MACHBARKEITSHUELLE, keine aesthetische Wahl.**
  Erlaubt ist `r + c <= 5`, also 6+5+4+3+2+1 = **21 Zellen** -- dieselbe 21,
  die eine volle Spalte kostet. Gemessen fuellt v2 4,88 / 4,70 / 2,88 / 2,23 /
  1,71 / 1,31 Zellen je Rasterzeile, also exakt dieselbe Neigung. Gespiegelt
  wird NUR um die Spalten-Achse; die unteren Orientierungen verlangten eine
  volle Rasterzeile 5, und die ist strukturell unerreichbar.
- **Eine volle Rasterzeile ist ohne Spezialfliese unmoeglich.** Sie wird nur
  von ihrer Musterreihe gespeist, und die schliesst hoechstens einmal je
  Runde ab: fuenf Steine fuer sechs Zellen. Spalten haben das Problem nicht
  (sechs Zellen aus sechs verschiedenen Musterreihen).
- **Erste unkontaminierte Referenz**: zehn Mensch-gegen-Netz-Partien in
  `static/log/` (Nutzer gewinnt 8 von 9) ergeben **1,80 volle Spalten** je
  Partie gegen 0,10 des Netzes; Abschlussprofil 4,00/4,10/3,40/3,20/2,50/2,20
  gegen 4,90/4,90/3,30/2,40/1,10/0,50. Die Platzierungspunkte sind dabei ein
  Gleichstand (54,9 gegen 55,8) -- der Vorsprung sitzt bei den Spezialfliesen
  (2,70 gegen 0,50 Freischaltungen je Partie, 8,50 gegen 0,90 Punkte).
- **B1-Vorgabe fuer jeden Nachfolge-Arm**: wer die Initiierung hebt, ohne die
  Vollendungsquote deutlich ueber 0,53 zu bringen, wiederholt B1.
- **Infrastruktur zahlt in Irrtumskosten, nicht in Elo** (Nutzer-Entscheid
  2026-08-25). `PREREG_search_rng_split.md` hat keinen Zug verbessert; vor ihr
  galt "gleicher Spielindex, gleiche Startbedingungen" aber nur bis zur ersten
  Suche, gepaarte Arenen waren also nur nominell gepaart. Genau davon lebt der
  laufende Lehrer-Test (par.10): Huellen-Arm und v1-Bezug sind GETRENNTE
  Partien auf denselben 407 Seeds. Wer kuenftig Messinfrastruktur vorschlaegt,
  begruendet sie an einer BENANNTEN Messung, die dadurch moeglich oder
  schaerfer wird -- sonst richtet man sich in Messgenauigkeit ein und
  vermeidet die haertere Frage, ob ueberhaupt Ideen da sind, die stark genug
  sind, um gemessen zu werden.
- **Methodische Lehre**: aus "Eingriff X in Richtung Y verliert" folgt NICHT
  "Y ist falsch" -- nur, dass X in diesem Zustand verliert. Es fehlt die
  Kontrollgruppe: ein Agent, der Y KANN.
- **Die Blindzieh-Stopp-Regel laeuft bei Wertungsplatte 6 das Konto leer**
  (2026-08-25, `PREREG_stack_draw_reservation_rule.md` par.4c; 600 Partien
  `selfplay_v20wdlsw_*`, Einheit Partie ueber beide Bretter, CI 95 %).
  `self_play.rs:500-545` `resolve_and_apply_stack_draw` entscheidet auf dem
  DEFAULT-Pfad, wie oft blind gezogen wird, und vergleicht dabei ein
  ABSOLUTES Brettniveau (`scoring_progress`, `scoring.rs:160` -- bei
  Kriterium 6 als einziges NEGATIV) gegen einen Typmittelwert in [1, 3]. Aus dem Code
  vorhergesagt und dann gemessen: **ohne Platte 6** haben 92 % der Ziehserien
  Tiefe 1, ab Runde 3 sind es 100 %; **mit Platte 6** enden **59,8 %** der
  Serien bei Punktestand 0, und es gehen **11,22 ± 0,42 Punkte je Partie** in
  Blindziehungen statt 3,93 ± 0,15 -- bei praktisch gleicher Serienzahl (3,60
  gegen 3,50), der Unterschied sitzt also allein in der TIEFE. Weil Ziehungen
  bei Punktestand 0 gratis und damit unsichtbar sind, sind die gemessenen
  Tiefen UNTERGRENZEN.
  **Nicht beantwortet:** ob der Kauf sich lohnt -- eine Wild-Platte kann mehr
  wert sein als 5 Punkte. Beantwortet ist nur, dass die Entscheidung auf einem
  Skalenbruch beruht und nicht auf einer Rechnung.
  **Konfundierungs-Verdacht** `[HERLEITUNG, ungeprueft]`: `PREREG_chance_nodes.md`
  Teil C liest die erhoehte Ziehquote bei Platte 6 als GELERNTE Interaktion.
  Dieselbe Korrelation entstuende auch rein mechanisch, weil der Resolver die
  Labels praegt. Nicht widerlegt, aber mit unausgeschlossenem Alternativerklaerer.
- **Strafleisten- und Ueberlauf-Zuege sind gemessen, nicht selten** (2026-08-25,
  `tools/diagnosis.py::run_penalty_bias` unveraendert + Aggregation je Partie;
  Korpus `selfplay_v20wdlsw_*`, 60 Dateien = 600 Partien, 97.970
  Entscheidungsschritte; Einheit Partie ueber beide Bretter, CI 95 %): die
  TOP-Aktion ist ein reiner Strafleisten-Zug (`row=-1`) in **4,40 ± 0,19**
  Schritten je Partie (2,70 % aller Schritte) -- davon **3,31 erzwungen** (keine
  legale Reihe) und **1,09 freiwillig**; eine Reihe MIT Ueberlauf ist TOP-Aktion
  in **5,51 ± 0,21** Schritten (6,17 uebergelaufene Steine je Partie). Bezogen
  auf die 89,08 Schritte je Partie, in denen ueberhaupt ein Stein-Zug angeboten
  wird, sind das 4,9 % bzw. 6,2 %.
  **Folge fuer die Aktionsfilter-Frage** (Anlass: externe Recherche,
  `evaluations/RESEARCH_heuristic_methodology_external_2026-08-25.md`): ein harter Filter nach dem Muster
  "Strafleisten-Ziel und Ueberlauf raus" waere NICHT wirkungslos, er traefe rund
  11 % der Stein-Entscheidungen. Drei Viertel der Strafleisten-Faelle sind
  allerdings erzwungen und muessten ohnehin stehen bleiben.
  **Spannung zu `PREREG_floor_action_aversion.md` par.6**: dort ist der rohe
  Prior auf dem Strafleisten-Ziel in ALLEN 280 qualifizierenden Stellungen exakt
  0 (nachgeprueft in `floor_action_aversion_gate.json`), hier stehen 1,09
  freiwillige Faelle je Partie. Die beiden Zahlen sind NICHT deckungsgleich und
  widerlegen einander auch nicht: das Tor sampelte 268 von 280 Stellungen in
  RUNDE 1, die freiwilligen Faelle liegen nach derselben Auswertung in Runde 2-4
  (R1=30, R2=255, R3=214, R4=154). **Die Schieflage ist ein Artefakt der
  Sammlung, nicht des Spiels** (geprueft an
  `tools/probes/floor_action_aversion_gate.py:221-242`): `collect_qualifying`
  laeuft die Datensaetze je Datei IN REIHENFOLGE durch und nimmt die ersten
  `cap_per_file = 3` qualifizierenden; Datensaetze stehen in Zugreihenfolge,
  also fuellt sich die Stichprobe mit Fruehspiel-Stellungen. Wer dasselbe Muster
  "erste N je Datei" anderswo benutzt, hat denselben stillen Rundenfilter drin.
  **Sonde repariert** (2026-08-25, Nutzer-Auftrag): `collect_qualifying` nimmt
  jetzt `rounds=` und `seed=`; mit Seed werden je Datei ALLE qualifizierenden
  Datensaetze gesammelt und daraus reproduzierbar gezogen. Ohne Seed ist die
  Auswahl unveraendert -- GEPRUEFT, nicht behauptet: auf einem 25-Dateien-
  Ausschnitt liefern alte und neue Fassung dieselben 60 Stellungen (alle in
  Runde 1), mit `rounds={2,3,4}` und Seed dagegen 17/19/24 aus Runde 2/3/4.
  Laeufe mit Filter oder Seed schreiben in eine ABGELEITETE Artefaktdatei, das
  registrierte `floor_action_aversion_gate.json` wird nie ueberschrieben.
  **Audit desselben Musters** (2026-08-25, Nutzer-Auftrag, an den Artefakten
  belegt statt vermutet):
  - `tools/probes/long_row_init_knob_effect.py:89-103` -- gleiche Form, und sie
    beisst: `long_row_init_knob_effect.json` hat `je_runde = {1: n=240}`, also
    **alle 240 Stellungen in Runde 1**. Wer aus dieser Sonde etwas ableitet,
    leitet es ueber Runde 1 ab. (Gehoert zum v2-/Langreihen-Strang, nicht
    angefasst.)
  - `tools/probes/long_row_prior_gate.py:193-221` -- gleiche Form, beisst hier
    NICHT: `je_runde` = 12/105/82/61 fuer Runde 1-4. Grund ist der groessere
    Deckel (`cap_per_file` Vorgabe 25 statt 3), der tief genug in jede Partie
    laeuft. Die Falle haengt also am VERHAELTNIS Deckel zu Trefferdichte, nicht
    am Muster allein.
  - `tools/tiling_value_reference_main.py:127` -- gleiche Form, aber mit
    explizitem Rundenfenster 2-4 und `--only_round`; Restbias innerhalb des
    Fensters Richtung Runde 2. Derzeit kein Artefakt in `evaluations/`, also
    haengt kein registriertes Ergebnis daran.
  - `tools/probes/column_completion_legality_probe.py:294` -- **kein Fall**:
    der Deckel greift auf PARTIEN, nicht auf Stellungen innerhalb einer Partie;
    Partien in einem Arena-Artefakt sind untereinander unabhaengig.
  Dazu zwei weitere Unterschiede, die einen
  direkten Vergleich verbieten: Generation (v21-Modell im Tor, v20-Korpus hier)
  und Groesse (roher Prior gegen Argmax einer wurzelverrauschten
  Self-Play-Policy). **Mit einem Lauf aufloesbar**:
  `tools/probes/floor_action_aversion_gate.py` auf Runde-2-4-Stellungen.

### Laufzeiten (gemessen, nicht geschaetzt)

Planungsgroessen. Die belastbaren Zahlen stehen je Lauf im Artefakt
(`laufzeit`-Block, Pflichtfeld seit 2026-08-25); hier steht nur, was man zum
Einplanen braucht. Wer eine Zeile ergaenzt, traegt GEMESSENES ein.

| Aufbau | Umfang | Threads | Wanduhr |
| --- | --- | --- | --- |
| Heuristik gegen Heuristik, 150 Sims (`v2_envelope_arena.py`) | 160 Partien | 0 = alle 12 Kerne | **21,9 s** |
| dito, Rauchtest | 20 Partien | alle Kerne | **4,1 s** |
| Netz@400 gegen Heuristik@150 (`v2_teacher_arena.py`), je Partie | -- | 0 = **sequenziell** | **12,357 s** |
| dito | -- | 11 | **2,575 s** |
| dito, voller Lauf 407 Seeds + v1-Bezug | 814 Partien | 0 = sequenziell | ~2 h 48 min (hochgerechnet aus 12,357 s je Partie; ein Lauf wurde nach 99 min abgebrochen) |
| dito | 814 Partien | 11 | ~35 min |

**Parallelisierung ist ergebnisneutral, gemessen statt angenommen**
(2026-08-25, 20 Seeds beidseitig, `neutral_seq.json` / `neutral_par.json`):
Siegquote 0,450, volle Spalten 1,200 und Punkte 55,0 in BEIDEN Faellen
identisch, bei 4,8-fachem Tempo. Grund ist `PREREG_search_rng_split.md`: jede
Partie haengt an ihrem eigenen, abgeleiteten Suchstrom.

**Die Falle in der dritten Zeile:** `threads = 0` heisst in
`run_heuristic_v1_vs_v2_arena` ALLE KERNE und in
`run_net_vs_heuristic_v2_arena` SEQUENZIELL. Dieselbe Sonde mit derselben
Zahl laeuft also einmal 12-fach und einmal einfach. Siehe die eingetaktete
Aufgabe "Arena-Threadzahl geradeziehen" in der Strang-Tabelle.

### Weitere entschiedene Straenge (Herleitungen im Archiv)

- **Agenten-Kapselung ENTSCHIEDEN**, Kernbeweis gruen (8/8 Partien
  byte-identisch). Quarantaene des Referee-/Worker-Pfads aufgehoben.
  Offen ist nur der planbare Ausbau: die restlichen ~31 Such-/Blattwert-
  Knoepfe wellenweise ins SearchConfig (par.4, je Knopf ein Commit mit
  Paritaets-Gate).
- **`PREREG_bootstrap_horizon.md`: BEIDE Arme geschlossen.** Anker-Variante
  an Stufe 0 (kritische Zellen 0,282 gegen 0,363, Kosten Faktor 20,1),
  klassisch 2-gegen-3 am Kostengate (+60,7 Prozent gegen Schwelle 25).
  Wiederaufnahme-Bedingung ist benannt: beide Zahlen sind an plattenblindem
  Spiel erhoben, ein Korpus mit echtem Spaltenbau waere ein neues Regime.
- **Plattenblick-Kette**: der Engpass liegt UPSTREAM in der Draft-/Reihenwahl,
  nicht am Spalten-Ende. Vier durchgemessene Ebenen ohne k1-Signal, dann der
  Strukturbefund (Bau bis ~4,6 von 6) und die Legalitaets-Stufe (0 von 160
  Faellen legal vollendbar). Details im Archiv.
- **Arena-Mitschrieb dauerhaft erweitert**: `long_rows_started` /
  `long_rows_completed` / `long_rows_cleared_unplaceable` je Partie und Seite
  (Zaehler auf `PlayerBoard`, NICHT im `state.log` -- das ist das
  Kernbeweis-Vergleichsobjekt). `tools/arena_compact.py` nimmt sie mit.

**Offener Sonden-Fix (bestaetigt, NICHT erledigt):**
`tools/probes/row_preference_probe.py:190-198` labelt in `imm_netvnet` beide
Seiten als "Champion", obwohl spec_a=alpha0.2 und spec_b=frozen zwei Agenten
sind. Fix-Muster: `tools/probes/penalty_track_probe.py` (liest spec_a/spec_b,
trennt NetzA/NetzB, rechnet die gepaarte Differenz). Der Kernbefund (~55,5 %
kurze Reihen) ruht auf drei weiteren, eindeutigen Kontexten.


## NAECHSTE SCHRITTE – ALLE OFFEN, ALLE NUTZER-ENTSCHEID

Der NAECHSTE Schritt je Strang ist Nutzer-Entscheid; einzelne Straenge tragen
bereits gebaute/gemessene Teilergebnisse (siehe jeweilige Zeile). Umfaenge und
Schwellen fuer noch nicht begonnene Teile stehen je Prereg und sind vor
Baubeginn freizugeben.

| Strang | Datei | Zuschnitt |
|---|---|---|
| **Arena-Threadzahl geradeziehen** | (kein Prereg, Werkzeugarbeit) | **EINGETAKTET 2026-08-25 (Nutzer-Entscheid), NICHT GEBAUT.** `threads = 0` heisst in `run_heuristic_v1_vs_v2_arena` ALLE KERNE und in `run_net_vs_heuristic_v2_arena` SEQUENZIELL (`self_play.rs:2866`, `if num_threads <= 1`). Gemessen am Lehrer-Test: 19,8 CPU-Minuten in 20,4 Wanduhr-Minuten bei 12 Kernen, Faktor 1,0. Betrifft `tools/probes/v2_teacher_arena.py` (`THREADS = 0`) und damit auch die urspruengliche Schritt-3-Messung. **Vorsicht beim Beheben:** die Bedeutung von `0` einfach umzudrehen aendert still das Verhalten JEDER Bestandsaufrufstelle. Sauber ist ein gemeinsamer Helfer mit EINER dokumentierten Konvention plus Nachweis der Ergebnisgleichheit auf einer Stichprobe (Partien sind je Seed unabhaengig, also sollte Parallelisierung nichts verschieben -- das ist zu ZEIGEN, nicht anzunehmen). |
| **Heuristik v2 als zusaetzlicher Lehrer** | `PREREG_heuristic_v2_long_rows.md` | **AKTIV, Messkette KOMPLETT.** Schritt 3: Faehigkeit belegt (volle Spalten 0,302 gegen v1 0,086, Vollendungsquote 0,686), Preis hoch (Siegquote 0,128 gegen 0,256). **URTEIL = NUTZER-ENTSCHEID**, kein Schwellenwert vorregistriert. Offen: par.5.4 Korpus und Training, Self-Play-Einstieg (freigegeben, nicht gebaut) |
| **Shaping-Kopf statt Ownership-Kopf** | `PREREG_heuristic_v2_long_rows.md` par.3b | Vorregistriert, NICHT gebaut. Sagt die Dreiecks-Abweichung voraus; zwei Kanaele (Spalte links/rechts), Abkling-Kurve zugunsten des Value-Kopfes. Braucht erst ein v2-Korpus, sonst auf plattenblindes Spiel geeicht |
| **Einhuellende im 2D-Encoder** | – | Nutzer-Frage 2026-08-24, nicht registriert. Zusaetzliche Eingabeebene "Dreiecks-Zugehoerigkeit je Zelle". Additiv moeglich (Eingabegroesse kommt vom Modell), aber eigener Bau nach par.3b |
| **R5-Netz-Loeser + R5-Value-Kalibrierung** | `PREREG_r5_solver_split.md` par.2 a/b/c, Teil B | Netz-Loeser-Arme (Budget, Policy-Sortierung, spaeter Value-Korrekturterm; je per-Agent verdrahtet, NIE per Env-Knopf) und der Vierer-Kopf-Vergleich. Zielmetrik: `r5_value_calibration`-Steigung, heute 0,06-0,09 statt ~1. **Arm 3 braucht ein b-Serie-Modell mit geprueftem Traeger-Status** -- der Ownership-Ausgang des Champions ist untrainiert (par.3a) |
| **Seeding-Folgearm: Dosis** | `PREREG_start_position_seeding.md` | k=6 war die erste Dosis; hoehere Dosis ist der naheliegende Folgeschritt, aber nicht registriert |
| **UVFA-Regime-Eingabe** | `PREREG_uvfa_plate_regime.md` | Folge-/Kombinationsarm; par.8: Conditioning-Dropout + Leakage-Waechter sind PFLICHT. par.7-Entscheid steht aus |
| **Saettigende Score-Utility** | `PREREG_saturating_score_utility.md` | Tor par.3a gefahren, Verdikt DAZWISCHEN -- **NUTZER-ENTSCHEID offen**: sigma-Kopf auf `points_val` selbst oder auf ein TD-unberuehrtes Ziel. Kein Automatismus, so im Tor vorgesehen |
| **Agenten-Kapselung: Ausbau** | `PREREG_agent_encapsulation.md` par.4 | ENTSCHIEDEN und gruen; offen ist nur der planbare Ausbau der restlichen ~31 Such-/Blattwert-Knoepfe ins SearchConfig, je Knopf ein Commit mit Paritaets-Gate |
| **Implicit-Minimax-Backup** | `PREREG_implicit_minimax_backup.md` | ENTSCHIEDEN: Effekt war GEGNERSPEZIFISCH (Heuristik-Arena +7,0 pp k1, netz-gegen-netz Paritaet). Knopf bleibt Self-Play-Kandidat mit gedaempfter Erwartung |
| **Lange-Reihen-Auszahlung** | `PREREG_long_row_payoff.md` | ENTSCHIEDEN und NEGATIV, aber als falscher HEBEL, nicht falsches ZIEL. B2 ist Nutzer-Entscheid und muss die Vollendungsquote deutlich ueber 0,53 bringen |
| **Bootstrap-Horizont** | `PREREG_bootstrap_horizon.md` | ENTSCHIEDEN: BEIDE Arme geschlossen (Anker an Stufe 0, klassisch am Kostengate). Wiederaufnahme nur mit einem Korpus, in dem tatsaechlich Spalten gebaut werden |
| **Reihenfolge Seeding-Kette gegen R5-Strang** | – | entscheidet der Nutzer beim Aufgreifen |

**Geschlossen ohne Messung (nicht neu vorschlagen):** die
Q-Skalierungs-Option (Aera-Nachmessung `gumbel_scale_calibration_v21.json`:
q:prior 1,47, kein mctx-Faktor-14; c_scale-Senkung hauseigen mit -13 % Score
vorbelastet) und jeder Suchparadigmen-Wechsel (beide externen Recherchen
`RESEARCH_plate_intent_external_2026-08-22.md` und
`RESEARCH_search_alternatives_external_2026-08-22.md`: additive Hebel zuerst,
kein Beleg-Fall fuer einen AB-Umbau).

---

## OFFENE ENTSCHEIDUNGEN (Nutzer)

| Punkt | Stand |
|---|---|
| **Gewichtsarm 4,0** | Vorabregel hat ihn freigegeben (`PREREG_ownership_weight_new_window.md` par.7); Nutzer-Entscheid 2026-08-17: **weiter hinten geparkt** |
| **Stoerungs-Baustein Stufe 2** | gehoert zum **Moon-Order-Kopf**, keine Einzelentscheidung mehr |
| **Korpus mit hoeheren Sims nachgenerieren** | **ABGELEHNT** (Nutzer 2026-08-17) – nicht neu vorschlagen |
| **Fester Bewertungssatz** | Bauer-Satz: 300 Dateien / 3000 Partien in `data/holdout/`, fertig 2026-08-18. Details (Zusammensetzung, Abnahme, Herkunft) siehe `../archive/history.md`, Kapitel "Ownership-/Zielwechsel-Kampagne v21-b18..b24 und Begleitbefunde (2026-08-16 bis 2026-08-20)". |
| **Push** | NIE ohne ausdrueckliche Nutzer-Anweisung (Nutzer-Regel 2026-08-20); Stand wird als "n Commits voraus" gemeldet |
| **`logs/nacht_20260820.log`** | darf weg (Nutzer 2026-08-22); die Zwangsseiten-Map ist extrahiert nach `data/asym_corpus/zwangsseiten_map.txt`. Loeschung ist Nutzersache |
| **Asym-Korpus** | bleibt LOKAL – Trainingsinput fuer Seeding und UVFA |
| **Ownership-Korpus** | entfernt der Nutzer selbst (5b-Abschluss registriert) |
| **`tools/night_run_20260820.ps1`** | vom Nutzer geloescht, die Loeschung ist noch nicht committet |


## FALLE vom 2026-08-20 – CPU-NEBENLAST VERSTUEMMELT ARENA-PARTIEN

Zwei parallel laufende Arena-Instanzen (je `--threads 10` plus Worker):
derselbe 8-Partien-Smoke lieferte unter Last ZWEI VERSCHIEDENE Ergebnisse
(eine Partie endete 3:1 – offensichtlich abgewuergt), ohne Last dreimal
byte-identisch (auch identisch zum Vortag; das frische Wheel war NICHT die
Ursache, per Dreifach-Vergleich ausgeschlossen). **Regel: Arena-Messungen
laufen EXKLUSIV – keine zweite Arena, keine Sonden mit Suchlaeufen, kein
Training parallel.** Vorflug-Determinismus-Checks zaehlen nur, wenn sie
unter denselben Lastbedingungen laufen wie die Messung selbst (praktisch:
beide exklusiv). Belege: `paired_arena_env_reach_conj_smoke1/2.json`
(unter Last, abweichend) gegen `reach_smoke1/3/4.json` (exklusiv,
identisch).


## TASK-INDEX (nur OFFEN/LAUFEND)

| Task | Status |
| --- | --- |
| **#29-Instrument (Offline-Value-Praediktor)** | **WARTET AUF POWER**: braucht >=6 arena-entschiedene Paare (Stand ~3); Kandidaten-Metriken werden je Gating mitgefuehrt. `PREREG_post34_package.md` |
| #31 / #38 / #39 | geparkt (Arbeitskreis "Spaeter"). Beschreibungen: ../archive/history.md, Kapitel "STATUS.md-Aufraeumung (2026-08-24)" |
| `stack_top_feature` | geparkt, Arbeitskreis "Spaeter", gleiche Stufe wie #38 (Nutzer-Entscheid 2026-08-20). Ziel ist SICHTGLEICHHEIT Netz/Spieler, kein Staerke-A/B. `PREREG_stack_top_feature.md`; Beschreibung im Archiv-Kapitel oben |

### v22-FENSTER -- DESIGN AUF HALDE, NICHT EINGEPLANT

**Nutzer-Entscheid 2026-08-08: keine v22-Self-Plays; erst die v21-Task-Queue.**
`PREREG_v22_window.md`: gleiche Form wie v21 (29.450 gesamt), juengster
Value-Posten 3.550 v19wdl-Rest + 1.450 v19wdlsw, Schwarm bleibt 74 %.
**Ab v22 ist die Rotationsregel stationaer.** Gating-H0-Vorbehalt: neuer
Batch desselben Generators braucht Suffix (`v20wdlb`).
**Hinweis 2026-08-14**: der Ownership-Korpus ist KEIN v22-Fenster -- er liegt
ausserhalb der Rotation (`data/ownership_corpus/`, additiv via
`--extra-data-dir`) und aendert diese Halde-Entscheidung nicht.

---


## GELTENDE REGELN (kompakt)

- **Das Punkte-Ziel ist NICHT `tanh(own/50)` (geprueft 2026-08-23).** Zwei
  Irrtuemer, die zusammen drei Dokumente falsch gemacht haben; beide am Code
  nachgesehen, beide korrigiert.
  1. **`points_val` ist ueberwiegend TD-geblendet.** Nach der Formelzeile
     (`neural_net.py:1647`) greifen zwei Ueberschreibungen: `:1704` setzt bei
     vorhandenem `rtv` komplett auf `own_rtv = 2·rtv[p] − 1`, `:1717`
     blendet `TD_LAMBDA·(2·bv[p] − 1) + (1 − TD_LAMBDA)·points_val` mit
     `TD_LAMBDA = 0.5` (`:717`). Kein Schalter unterdrueckt den TD-Blend
     (`value_target_variant` greift nur am rtv-Zweig).
     **Was da eingemischt wird, ist die Ausgabe des VALUE-Kopfes, nicht des
     Punkte-Kopfes:** `bootstrap_value` entsteht ueber
     `self_play.rs:1737` -> `round_transition_deep.rs:852` ->
     `net_mcts::net_leaf_eval` -> `net_mcts.rs:2411`
     `blended_leaf_win_prob(&value, ...)`, bei `w=0` also
     `calibrate_win_prob_with(value_to_win_prob(value))`. Seine Bedeutung
     haengt am Value-Kopf des GENERATORS: bei WDL-Kopf ist
     `value_out = 2·p_win − 1` (`neural_net.py:2503`), also eine
     Gewinnwahrscheinlichkeit; beim tanh-Kopf davor ist es
     `tanh((own−opp)/50)`, also eine Punkte-MARGE. Beides ist um null
     zentriert, beides ist NICHT der eigene Endstand `tanh(own/50)` -- die
     Etikettierung "Gewinnwahrscheinlichkeit" gilt aber nur fuer die
     WDL-Aera (v19wdl aufwaerts), nicht fuer v18.
     Gemessen (je eine Datei pro Generation): `round_transition_value` in
     v18/v19wdl/v19wdlsw/v20wdl/v20wdlsw **nirgends**, `bootstrap_value` in
     **82,8 bis 84,0 %** der Datensaetze. Nur Runde 5 (kein Uebergang)
     traegt das reine `tanh(own/50)`. **Folge: jede Aussage ueber die
     Verteilung des Punkte-Ziels oder ueber die Bedeutung der Kopf-Ausgabe
     muss diesen Blend mitrechnen.** Eine nachgebaute Formel misst eine
     Groesse, die kein Training je gesehen hat.
  2. **Task #12 lief NICHT am Differenzziel, sondern eigenseitig.** Der
     Verteilungskopf trainiert auf `targets_points` (`train.py:1073`), und
     `points_val` war seit db73122 (2026-07-06, "Differenzbildung durch
     getrennt gesaettigte Terme ersetzt") bis Schema 20 (08c565d,
     2026-08-10) `tanh(own/50) − 0,1·tanh(opp/50)`. Auf der Differenz liegt
     `val`, das Value-Ziel. **Folge fuer die Wiederaufnahme:** der in
     `PREREG_points_dist_bin_scale.md` behauptete Bin-Skalen-Defekt lag in
     #12 bereits vor, und die Messung kam flach heraus -- #12 ist damit ein
     Prior GEGEN die Hypothese, nicht ein neutraler Vorlauf.

  Der Irrtum stammt aus `research_value_head_alternatives_DRAFT.md` Z. 7 und
  war von dort nach `docs/concept_distributional_heads.md` und in zwei
  Preregs gewandert. Alle vier Stellen sind am 2026-08-23 korrigiert.

- **NEUER PUSH-BLOCKER seit 2026-08-21 (79de9fa): Rechnerstruktur im
  `pre-push`-Haken.** Wenn ein Push abbricht mit „RECHNERSTRUKTUR in
  gepushten Dateien", ist das kein Defekt, sondern der Waechter: eine
  hinzugefuegte/geaenderte Datei im Push-Bereich enthaelt einen absoluten
  Pfad in ein Nutzerverzeichnis (Windows- wie Git-Bash-Schreibweise), einen
  OneDrive-Pfad in den Dokumente- oder Backups-Ordner, oder den Nutzernamen
  aus der Umgebung. **Das genaue Muster steht ausschliesslich in
  `PRIVACY_PAT` (`tools/hooks/pre-push`)** -- dort als Regex mit
  Zeichenklassen notiert, was es davor bewahrt, sich selbst zu treffen. Wer
  es woanders WOERTLICH hinschreibt, macht diese Datei zum Dauerblocker;
  genau das ist beim ersten Eintragen hier passiert. Das setzt CLAUDE.md
  („Oeffentliches Repo: keine
  Rechnerstruktur", 2026-08-17) durch, das bisher nur ein Pruefbefehl zum
  Selbstausfuehren war. Geprueft wird der GEPUSHTE Stand (nicht der Working
  Tree) und nur A/C/M/R -- die Historie wird nicht umgeschrieben, Alt-Treffer
  blockieren nicht. `CLAUDE.md` ist ausgenommen. Richtige Antwort: Pfad aus
  der Umgebung beziehen (`MOSAIC_PYTHON_DIR`, `MOSAIC_BACKUP_DIR`,
  `MOSAIC_MODELS_DIR`). Nur bei echtem Fehlalarm `git push --no-verify`.
  Kosten < 1 s (gemessen 0,44 s ueber 10 Commits), laeuft VOR der
  `engine/src`-Weiche, also auch bei reinen Doku-Pushes. Details:
  `tools/hooks/README.md`.

  Gleicher Zug: `.git/hooks/pre-push` (tote Alt-Kopie ohne den
  `cygpath`-Fix) geloescht -- aktiv ist ausschliesslich `tools/hooks/` via
  `core.hooksPath`. Und die Golden-Waechter **A1-A4 sind gebaut** (geprueft
  2026-08-21: A2 `engine/src/lib.rs:583`, A3 `engine/src/features.rs:1375`,
  A4 `engine/src/mcts.rs:1271` ff.); die Hook-README behauptete bis dahin
  das Gegenteil.

- **Seed-Skala der Arena bei n=400 (gemessen 2026-08-09)**: dieselbe
  Konfiguration (k=1, Champion@600 vs Heuristik@150dyn) ergab **76,0%**
  mit Basis-Seed 20260820 und **81,75%** mit 20260828 -- **5,75
  Prozentpunkte allein durch den Seed**. Das ist groesser als die
  meisten Effekte, die wir messen (λ, k=2, Denial-Varianten liegen alle
  darunter). Folge: **ungepaarte Vergleiche zwischen zwei Laeufen sind
  wertlos**, auch wenn beide n=400 haben. Jeder A/B braucht identische
  Basis-Seeds im SELBEN Instrument; wo zwei getrennte Laeufe noetig sind
  (unterschiedliche Sim-Budgets), muss der Basis-Seed gleich gesetzt und
  die Paarung ueber den Spielindex selbst gerechnet werden.

- **Champion**: `v21_2d_brierbest` seit 2026-08-09. Gueltige Elo-Leiter:
  **1215** [1170, 1259] (`PREREG_round5_minfix_elo_reset.md` par.5);
  Alt-Leiter vor dem R5-Minfix-Reset 1358 -- **Kanten ueber die Fix-Grenze
  nie mischen**, Alt-Register in `../archive/elo_history_pre_r5fix.csv`.
  Gating-Chronologie und Herleitung des Niveaus: `../archive/history.md`.
  **Generator-Naming**: Dateien/Laeufe IMMER nach dem GENERATOR benennen;
  eine Ziel-Generation existiert erst mit trainiertem Modell.

- **Fenster-Pinning -- ZWEI Variablen, nicht eine (verschaerft
  2026-08-09 nach einem Beinahe-Fehler)**: Ein Trainingsstart im
  v21-Fenster braucht BEIDE:
  
  ```
  export MOSAIC_DATA_EXCLUDE="$(cat evaluations/v21_exclude_regex.txt)"
  export MOSAIC_CARRIER_MANIFEST="policy_carrier_manifest_v21.json"
  ```
  
  **DRITTER Beinahe-Fehler derselben Klasse (2026-08-19): die Regex-Datei
  veraltet.** Das b18-FENSTER (Korpus-Sockel-Linie: b18/b19/b23/b24) schliesst
  zusaetzlich `selfplay_v19wdlsw_` aus – `v21_exclude_regex.txt` enthaelt das
  NICHT. Ein b24-Start mit der txt-Datei lud 3371 statt 2945 Dateien (800
  v19wdlsw zu viel); aufgefallen an der Kompositions-Zeile VOR dem Cache-Bau,
  Lauf gestoppt und neu gestartet. **Regel: das Exclude fuer einen
  Wiederholungs-/Nachfolgelauf IMMER aus dem `data_exclude`-Feld des
  REFERENZ-Manifests ziehen** (materialisiert:
  `evaluations/b18_window_exclude_regex.txt` aus dem b23-Manifest), nie aus
  einer benannten txt-Datei, deren Stand niemand prueft. Fuer die
  b18-Linie gilt zudem `MOSAIC_CARRIER_MANIFEST="policy_carrier_manifest_own.json"`.
  
  `MOSAIC_CARRIER_MANIFEST` wurde beim `t_d_vw08`-Start VERGESSEN. Der
  Default ist `policy_carrier_manifest_v20.json`, also ein ANDERER
  Traeger-Satz: der Arm haette mit einer anderen Policy-Maske als
  `t_d_vw04` und als `v21_2d` trainiert und waere als Sweep-Arm wertlos
  gewesen -- ohne Fehlermeldung, nur mit plausiblen Zahlen. Der Lauf
  wurde gestoppt und korrekt neu gestartet; ein angefangener
  Falsch-Cache war noch nicht auf der Platte.
  **Verifikation ist Pflicht und zwar VOR dem Weggehen**: die
  Cache-Zeile muss `📦 Lade HDF5-Cache (2651 Dateien)` lauten.
  Steht dort `Lade Daten aus 2651 Dateien...`, ist der Cache-Schluessel
  anders -- Lauf sofort stoppen und die Ursache klaeren, NICHT einen
  Neubau durchlaufen lassen (er zementiert das falsche Fenster).
  Beweisweg fuer die Ursache (bei Bedarf wiederholbar): Cache-Key aus
  `str(files)+INPUT_SIZE+NUM_ACTIONS+VALUE_SCHEMA_VERSION+...+carriers`
  nachrechnen und mit den `data/.cache_*.h5`-Namen vergleichen -- die
  v21-Caches sind `26e304f5d2c7` (train, 2.651 Dateien) und
  `8a04a7143bbe` (val, 294). Merke: der **Cache-Key ist der einzige
  Waechter** ueber die Traeger-Wahl, das Lauf-Manifest protokolliert
  `MOSAIC_CARRIER_MANIFEST` NICHT (`engine_config`/`python_constants`
  waren zwischen richtigem und falschem Lauf identisch).
  Harmlos dagegen: die 55 archivierten v18-Dateien sind seit 10:16 aus
  `data/` heraus, `MOSAIC_DATA_EXCLUDE` schliesst nun 0 statt 55
  Dateien aus -- Split und Dateiliste sind trotzdem BEWEISBAR identisch
  (rekonstruiert und verglichen: 2.651/294 in beiden Faellen gleich).

- **NACHSCHUB BEI GATING-FEHLSCHLAG -- KORRIGIERTE FASSUNG
  (Nutzer 2026-08-09)**: Die Streichung des Nachschub-Ventils vom
  2026-08-07 war **generationsspezifisch** (v20-Zyklus, weil dort eine
  lange Nebentask-Liste offen war) und **KEINE stehende Anweisung** --
  ich hatte sie faelschlich verallgemeinert (auch in
  PREREG_v21_window.md, dort korrigiert).
  **ERSETZUNG (frischer Batch desselben Generators + Rausrotieren einer
  Alt-Generation) ist VERWORFEN** -- Nutzer-Argument, und es ist
  richtig: das ist indirekt mehr Volumen vom SELBEN Champion, waehrend
  die Diversitaet der alten Generationen aus dem Fenster fliegt. Genau
  die Generationen-Spreizung ist aber der Grund, ueberhaupt Alt-Material
  mitzufuehren.
  **Was bleibt: gezielte INJEKTION** (Sockel-Partien dazu, nichts
  verdraengt -- schont die Diversitaet). Bedingungen, damit daraus kein
  "solange nachlegen bis der Kandidat gewinnt" wird:
  
  1. Umfang und Entscheidungsregel VOR der Injektion schriftlich
     (Mini-Prereg), nicht nach dem verlorenen Gating improvisiert.
  2. Einmalig und begrenzt je Generation (Vorschlag: +2.000 Sockel),
     kein iteratives Nachlegen.
  3. Naming: derselbe Generator erzeugt ein Batch mit
     Unterscheidungs-Suffix (`v20wdlb`), sonst Datei-Kollision.
  4. Lesart des Ergebnisses: ein Sieg NACH Injektion belegt "die
     Generation brauchte mehr Policy-Material" -- NICHT, dass eine
     etwaige Rezept-Aenderung des Kandidaten gewirkt hat. Diese
     Unterscheidung muss im Verdikt stehen.
  5. Diagnostischer Rueckenwind erwuenscht (Policy-Wacht: fallen die
     Orakel-Metriken gegen die Vorgeneration, ist die Policy-Klasse der
     belegte Engpass), aber keine harte Vorbedingung -- Nutzer-Entscheid.

- **FENSTERGROESSE: FIXIERTE BASIS, Injektion ist die benannte Ausnahme
  (Nutzer-Entscheide 2026-08-09)**: 29.450 Partien / 2.945 Dateien / ~4,8 Mio.
  Zustaende bleiben die stehende Groesse. Die Rotation haelt sie
  konstant -- pro Windung 12.000 NEUE Partien (4.000 Sockel @600 +
  8.000 Schwarm @150), gleich viel altes Material rotiert raus. Folgen:
  (a) Kosten pro Generation KONSTANT (~18h Self-Play + ~3h Cache +
  ~3,5h Training), kein Anwachsen; (b) das Fenster wird mit jeder
  Windung FRISCHER statt groesser; (c) RAM/Cache-Budget stabil
  (~13 GB im Training, ~1 GB auf Platte).
  **Nicht neu aufrollen**: der Dosis-Befund ("Volumen half 6/6") ist
  eine stehende Versuchung, das Fenster generell zu vergroessern -- die
  Entscheidung dagegen ist bewusst gefallen (planbare Kosten,
  stationaeres Design ab v22). Eine DAUERHAFTE Vergroesserung braucht
  einen ausdruecklichen neuen Nutzer-Entscheid. Die einmalige,
  vorregistrierte Injektion bei Gating-Fehlschlag (s.o.) ist davon
  ausgenommen und veraendert die Basisgroesse nicht.

- **Backup-/Alt-Regel-Korpora**: kommen NIE wieder ins Training.

- **PROMOTIONS-CHECKLISTE (Nutzer-Hinweis 2026-08-09: die Kader-Praxis
  wurde bis dato nicht konsequent umgesetzt)** -- bei JEDEM
  Champion-Wechsel vollstaendig abarbeiten, nicht aus dem Gedaechtnis:
  
  1. `tools/set_champion.py <neu>` (Server-Default, wirkt nach Neustart).
  2. Elo-Kante **Gating** (Champion-1) -- inkl. Replikations-Zeile, falls
     Fruehstopp <150 Paare.
  3. Elo-Kante **Anker**: `Heuristik@150(dyn)`, **festes n=150 ohne
     Fruehstopp** (Praezedenz v18/v19/v20-Verankerung).
  4. Elo-Kante **Champion-2** (der Vorvorgaenger, @400) -- **das ist der
     Punkt, der bei v20 UND v21 zunaechst fehlte**; ohne ihn ruht die
     Elo-Schaetzung auf zu wenigen Kanten (v21 nach dem Gating:
     CI +-90 Punkte).
  5. Pflicht-Diagnostiken am Sieger (Platt, R5, Alt-Set-Brier, R4b) +
     Eintrag in die #29-Buchfuehrung.
     5b. **Anzeige-Kalibrierung nachziehen**: die Platt-Parameter A/B des
     NEUEN Champions in `server.py` (`_DISPLAY_CAL_A/_B`) eintragen --
     sie sind modellspezifisch. Quelle: `tools/platt_fit.py --models
     models/alphazero_<neu>.pth`. Ohne das zeigt die GUI die
     Gewinnwahrscheinlichkeit mit der Kurve des VORGAENGERS an.
     5c. **sigma/Prior-Balance messen** (neu 2026-08-09, aus Task G):
     `tools/gumbel_scale_calibration.py --model <neu> --sims 400
     --n-states 300`, ~10 min. Der Aera-Wechsel v18->v21 hat das
     Verhaeltnis von 1,232 auf **2,287** verschoben (delta_q verdoppelt,
     delta_ln(prior) unveraendert) -- R3 liegt mit 2,972 praktisch auf
     der Wiedereroeffnungs-Schwelle. **Ueberschreitet die
     Gesamt-Kennzahl 3, oeffnet sich die c_visit/c_scale-Familie per
     REGEL wieder** (kein Ermessen). Zugleich Verfallsdatum-Waechter
     fuer die H0-Befunde der Wurzel-Regler-Familie: die wurden in einem
     anderen Balance-Regime gemessen.
  6. STATUS-Champion-Zeile + history-Kapitel.
     **Nachtrag-Schuld ERLEDIGT** (Klarstellung 2026-08-10): die v20-Kante zu
     `v19_best` lief am 2026-08-09 -- 114:76 ueber 190 Partien, SPRT-H1 nach 95
     Paaren, p=0,0043 (`elo_history.csv` Zeile 53,
     `paired_gating_v20_vs_v19best_nachtrag.json`). Die alte "fehlt"-Zeile hier
     hat mich zweimal dazu verleitet, die Messung erneut vorzuschlagen.
     **Elo-Fragen am Primaerregister `elo_history.csv` pruefen, nicht an dieser
     Datei.**

- **LOESCHEN NUR MIT EXPLIZITER RUECKFRAGE (Nutzer-Regel 2026-08-08,
  dritter Vorfall dieser Klasse -- "inakzeptabel")**: Kein Loeschen,
  Verschieben oder Ueberschreiben von Dateien, Ordnern oder Worktrees
  ohne vorherige, den KONKRETEN Pfad benennende Nutzer-Freigabe.
  Ausnahme: das eigene Scratch-Verzeichnis.
  Im Einzelnen:
  
  1. **Eine FRAGE ist keine Anweisung.** "Ist X noch aktuell?", "kann
     man X weg?", "brauchen wir X?" verlangen eine ANTWORT. Handeln
     erst nach einem Imperativ, der das Ziel nennt.
  2. Als Loeschen gelten auch: `git worktree remove`, `git checkout --`,
     `git reset --hard`, `git clean -fd`, `mv` aus dem Projekt heraus,
     `rm` auf generierte Artefakte (Caches sind KEINE Ausnahme -- die
     Freigabe vom 2026-08-08 galt fuer sechs namentlich genannte Dateien).
  3. Vor jeder freigegebenen Loeschung: Ziel ANSEHEN (Inhalt, Groesse,
     Reparse-Points bei Worktrees -- Junction-Vorfall 2026-07-24), das
     Ergebnis der Pruefung BERICHTEN, und nur dann ausfuehren.
  4. Gilt fuer Sub-Agents identisch und steht in jedem Agent-Prompt.
  5. "Aufraeumen" ist niemals selbst-autorisiert -- auch dann nicht,
     wenn etwas offensichtlich veraltet ist.

- **Statistik**: (1) Score-Auswertungen IMMER auf Block-Ebene;
  (2) Netz-vs-Heuristik-Effekte <8pp = Seed-Rauschen; (3) SPRT-
  Fruehstopps <150 Paare zaehlen nur mit Frisch-Seed-Replikation.

- **Value-Aenderungen brauchen Arena-Gating** (kein validierter
  Offline-Praediktor, solange #29 offen/unvalidiert ist).

- **AUFLOESUNG SCHLAEGT SPARSAMKEIT (Nutzer-Regel 2026-08-08)**: Wenn
  eine Entscheidung an einer Differenz haengt, die UNTERHALB der
  Auflösung des Offline-Instruments liegt (Value-Seite: Brier-Gaps
  <0,015 sagten 0/4 die Arena voraus; gemessene Seed-Skala ~0,0006),
  dann darf das Offline-Mass die Entscheidung NICHT tragen -- auch nicht
  als Spar-Vorfilter ("nur gaten, wenn Brier X schlaegt"). Stattdessen
  die ARENA in die Abwaegung nehmen und die Kosten AUSRECHNEN, nicht
  schaetzen: ein Gating (~1-1,5h CPU, 200 Paare @400) ist regelmaessig
  BILLIGER als das Training, das man sich mit dem Vorfilter sparen
  wollte (~3,5h GPU) -- und es ist das einzige validierte Instrument.
  Wer auf einem blinden Mass spart, spart die billige Ressource und
  riskiert die teure Fehlentscheidung.
  **Ausnahme Policy-Seite**: die Orakel-Metriken (Prior-Masse Top-3,
  Kendall-Tau) sind arena-validiert (7/7) und DUERFEN als Vorfilter
  dienen -- so entschieden bei #35b (beide Metriken schlechter -> kein
  Gating). Der Unterschied ist der Validierungsstand, nicht die
  Bequemlichkeit.
  Zusatznutzen, den man mitnehmen soll: jedes gefahrene Gating liefert
  ein arena-ENTSCHIEDENES Paar -- die Waehrung, in der #29 (Validierung
  eines Offline-Value-Praediktors) bezahlt wird (Stand ~3, noetig >=6).

- **Aggressions-/Denial-Programm GESCHLOSSEN** (2026-08-07): alle
  Knoepfe auf Default (w=0, λ=0, ε=0, bias=1); "gate what you ship";
  Wiedervorlage nur mit messbar schaerferem opp-Kopf
  (PREREG_aggression_style_measurement/PREREG_denial_tiebreak).

- **Heuristik-Anker-Parameterpaket: NICHT ANFASSEN** (definiert den
  Elo-Anker@200; jede Aenderung entwertet die Leiter).

- **Elo-Betrugsschutz (GUI)**: gewertete Spiele nur gegen verankerte
  Konfigurationen (`is_estimate=False`); Abbruch-Verhalten bleibt
  (Nutzer-Entscheid). **Tiling-Cache** Default AN
  (`MOSAIC_TILING_CACHE=0` schaltet ab).

- **Checkpoint-Politik**: brierbest (arena-re-validiert 2026-08-07,
  E15-Alt-Set-Vorsprung uebersetzt nicht in Staerke).

- **Telemetrie-Stand Q-Skalierung/Sequential-Halving** (externes Review
  R2 2026-08-09, `PREREG_prior_blind_spot.md`, Tasks E/F/G dazu
  geschlossen -> history): Q-Skalierungs-Varianz ist JA protokolliert
  (`tools/gumbel_scale_calibration.py`), **Ueberlebensrate im
  Sequential Halving NEIN** -- vorhanden sind `root_child_q`,
  `root_num_actions(_considered)` und `max_depth`, aber nicht, welcher
  Kandidat welche Halbierungsphase uebersteht. Bewusst nicht
  nachgeruestet: Task E hatte zuerst zeigen muessen, ob die MENGE
  stimmt (Ergebnis: Miss-Rate 1,21%, weit unter der 5%-Schwelle).


## ARCHITEKTUR, Stand jetzt (Referenz; aktualisiert 2026-08-24)

**Such-/Engine-Seite** (`engine/src/net_mcts.rs`, `engine_config_json()`):

- `ACTIVE_LEAF = LeafEval::Net` -- das Netz liefert den Blattwert; Stufe 1
  (DFS-Blatt, `mcts.rs`) liegt dormant im Code. Rueckfall ist AUSGESCHLOSSEN
  (Rundenweitsicht ist harte Anforderung).
- Gumbel-Suche aktiv, `GUMBEL_TOP_M = 16`, `GUMBEL_C_SCALE = 1,0`,
  `DEFAULT_C_PUCT = 1,5`, `floor_shaping_weight = 0,3`.
- `VALUE_SHRINK_ENABLED = false`; `round_transition_sampling = false`;
  `bootstrap_horizon_rounds = 2` -- **beide Arme der Vertiefung sind
  geschlossen** (`PREREG_bootstrap_horizon.md`: Anker-Variante an Stufe 0,
  klassisch 2-gegen-3 am Kostengate mit +60,7 Prozent gegen eine Schwelle
  von 25).
- **Zwei R5-Loeser seit 2026-08-23** (`PREREG_r5_solver_split.md`): der
  EINGEFRORENE Anker-Loeser `round5_anchor.rs` haengt an den drei
  Sucheinstiegen der Heuristik (`mcts.rs:746`, `:777`, `:796`) und schuetzt
  die Elo-Leiter; `round5.rs` ist der Netz-Loeser und darf sich entwickeln.
- Runde 5 wird NICHT vom Netz gespielt: `round5.rs` uebernimmt ab
  `round_number>=5 && phase==Drafting`, Blattwert = exakter Endscore inkl.
  Wertungsplatten. **Seit 2026-08-10 EXPECTIMINIMAX, nicht mehr reines
  Alpha-Beta**: Zufallsknoten an den Aufdeck-Stellen der verdeckten
  Chip-Zuordnung (16 der 20 Chips sind aus R1-4 bekannt, unbekannt ist nur
  die Fabrik-Position der restlichen 4). Kein Pruning in Zufallsknoten
  (Star1/Star2 bewusst weggelassen). `NODE_BUDGET=200` ist eine
  Bezahlbarkeits-, keine Hinreichenszahl.
- Laufzeit-Knoepfe (alle Default = Bestandsverhalten):
  `MOSAIC_POINTS_UTILITY_W`/`MOSAIC_AGGR_LAMBDA` (Task #28, Default 0),
  `MOSAIC_VALUE_CAL_A`/`_B` (Task #30, Default 0/1),
  `MOSAIC_TILING_CACHE` (**Default AN** seit 2026-08-05),
  `MOSAIC_PROFILE_SELFPLAY` (Task #32, Default aus),
  `MOSAIC_R5_CHANCE_NODES` (**Default AN** seit 2026-08-10, `=0` stellt das
  Altverhalten her), `MOSAIC_R5_NODE_BUDGET`, `MOSAIC_R5_NET_SOLVER`
  (Default an).

**Netz-/Trainingsseite** (`config.py`, `engine/py/neural_net.py`):

- `INPUT_SIZE = 708`, `NUM_ACTIONS = 406`.
- Champion-Encoder ist **2D** (`Mosaic2DNet`: Conv-Zweig auf
  `state_to_planes` + Flach-Zweig auf `state_to_tensor`); der flache
  `MosaicNet` bleibt Parallel-/Messarm.
- Koepfe: `policy`, `value`, `moon_order`, `points`, `ownership`, seit
  Task #28 zusaetzlich `opp_points` (nur in Modellen, die damit trainiert
  wurden -- Engine erkennt ihn per Output-NAME und faellt sonst auf
  Bestandsverhalten zurueck). **`plate_head` wurde am 2026-08-10 gebaut und
  wieder ENTFERNT** -- der Ownership-Kopf ist der Randlayer.
  `ownership` ist seit 2026-08-10 **140 breit** (72 Feldlabels + 68
  Konjunktionen, Breite an config.py:117-118 + Label-Bauer verifiziert
  2026-08-14); `OWNERSHIP_WEIGHT` steht in `config.py` weiter auf 0 --
  der Champion-Kopf ist untrainiert. Naechster Lauf mit Gewicht 0,2 +
  `--conjunction` ist der Korpus-Trainingslauf (PREREG_ownership_corpus.md).
- `VALUE_WEIGHT = 0,2`, `POINTS_WEIGHT = 0,5`, `VALUE_SCALE = 50`,
  `TD_LAMBDA = 0,5`, **`VALUE_OPP_EPSILON = 0,0`** (war 0,1 bis Schema 19).
- **Punkte-ZIEL (Schema 20, 2026-08-10)**:
  `points_val = tanh(own_total/VALUE_SCALE)` -- der Gegner-Anteil ist
  ENTFERNT. Fuer VOR Schema 20 trainierte Modelle bedeutet ihr
  `points`-Ausgang weiter `own - 0,1*opp`; fuer die Spielstaerke belanglos,
  weil die Ausgabe im Suchpfad ohnehin verworfen wird
  (`POINTS_UTILITY_WEIGHT = 0` und `w = 0`).
- **Value-ZIEL (#34-Verdikt, Schema 17 unveraendert gueltig)**: `values_wdl`
  = TD-Blend aus Bootstrap-Gewinnwahrscheinlichkeit und hartem Ausgang;
  Alt-Datei-Bootstraps werden beim Cache-Bau Platt-entstaucht
  (A=0,0051/B=1,9269), `selfplay_v19wdl*`-Bootstraps (WDL-Generator) bleiben
  roh. Training: `--value-head wdl --select-by-brier` (KEIN destretch-Flag
  mehr noetig). **Das Ziel ist margen-BLIND** -- Herleitung in
  `../archive/history.md` (der Abschnitt "warum das Netz nicht punktoptimiert
  spielt" ist mit den Alt-STAND-Kapiteln dorthin gewandert).
  Policy-Traeger-Manifest **`data/policy_carrier_manifest_v21.json`**
  (Default in `neural_net.py` ist noch die v20-Datei -- ein Trainingsstart
  im v21-Fenster MUSS `MOSAIC_CARRIER_MANIFEST` setzen, s. Fenster-Pinning
  oben), maskiert Alt-Dateien ausser 135 v19wdl + 45 v18, plus
  `carrier_prefixes: ["selfplay_v20wdl_"]`; alles im Cache-Key.
  Checkpoints: `_best` (val_combined), `_brierbest` (Value-Peak).
- Champion: `models/champion.txt` -> **`v21_2d_brierbest`**.

---

