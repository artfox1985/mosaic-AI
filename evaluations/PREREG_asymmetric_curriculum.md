<!-- STATUS: ENTSCHIEDEN | Frage: Lernt der Value-Kopf den Wert des k1-Baus, wenn er ihn in asymmetrischen Partien (EIN Spieler baut, der andere nicht) erstmals als siegentscheidendes Merkmal sieht? | Beleg: Gesamtverdikt par.14-16 (2026-08-22): kein Signal (k1-Rate 12,2 % = Grundrate), aber kein Siegverlust (199 gegen 205 von 407); Behavior-Cloning drueckte sich nicht aus (par.16). Nachmessung par.17 (2026-08-29): v22-b05 ordnet dieselben Geschwister mit Tau +0,338 -- die Ordnung kam ueber die Lehrer-Linie, nicht das Curriculum. -->

# PREREG: Asymmetrisches Self-Play — den Plattenbau erstmals als Vorteil zeigen

> **FOKUS-REGEL (Nutzer 2026-08-18):** ausschliesslich **k1**. Registrierte
> "k1 oder k2"-Klauseln werden auf k1 gelesen. Begruendung: `STATUS.md`,
> Abschnitt "FOKUS-REGEL".

Stand **2026-08-18**. **ENTWURF, nichts gebaut.** Durchgehend Plan-Zeitform.

**Anlass.** `DOSSIER_ownership_head.md` 7(1): die Bauer-Knoepfe sind ein
Prozess-Schalter ohne Spielerparameter (`bauer_drafting_vorzug(state)`,
`self_play.rs:1170`) — in den Bauer-Armen bauen **beide** Spieler. Damit ist das
Value-Ziel (Sieg/Niederlage) beziiglich des Plattenbaus **wegsymmetrisiert**.
Der Value-Kopf hat ueber den *Wert* des Plattenbaus nicht das Falsche gelernt,
sondern **nichts**. Das erklaert die Stelle, an der alle vier geschlossenen Wege
haengenbleiben: der Prior bietet den Bauzug dominant an (4,91x
Gleichverteilungsmasse, 129 von 130 Held-out-Partien vorn,
`PREREG_corpus_distillation.md`), ueberstimmt wird er vom Wert-Backup — und der
Wert kennt keinen Grund, den Bau zu bevorzugen.

Eine externe Spezifikation (2026-08-18) hat daraus ein Drei-Phasen-Curriculum
gemacht. Diese Vorregistrierung uebernimmt den **flachen** asymmetrischen Arm und
**verwirft das dynamische Curriculum** (Begruendung: par.8).

---

## par.1 DIE FRAGE

> Sieht der Value-Kopf den k1-Bau als Vorteil, wenn er in einem Teil der
> Trainingspartien **nur auf einer Seite** vorkommt — und behaelt er ihn,
> nachdem der Bauer wieder weg ist?

Zwei getrennte Teilfragen, beide vorab benannt, weil die zweite die erste
entwerten kann:

- **B (Zuordnung):** entsteht ueberhaupt ein Signal — trennt der Value-Kopf
  Stellungen mit und ohne Spaltenfortschritt?
- **C (Transfer):** ueberlebt es den Wegfall des Bauers, oder war es
  "Bauer erkannt", nicht "Spalte bewertet"?

---

## par.2 GEPRUEFTER IST-STAND — die Seitigkeit ist schon gebaut

| Sache | Befund | Pruefstelle |
|---|---|---|
| Seitigkeits-Flag je Agent | `NetSelfPlayAgent { .., vorzug: bool }` | `self_play.rs:1332` |
| Absicht des Flags | *"die EXPLIZITE Seitigkeits-Konfiguration des Bauer-Vorzugs"* | `self_play.rs:1279` |
| heutiger Self-Play | EINE Konfiguration an beide Seiten: `players: [player, player]`, `vorzug: true` | `self_play.rs:2992`, `:2977` |
| Vorzug ist kein Zwang | `.or_else`-Kette: der Bauer greift nur, wo er etwas vorschlaegt, sonst das Netz | `self_play.rs:1170-1174` |
| Bauer je Kriterium | `bauer_fuer(1)` = `SPALTENBAUER_GENERISCH`, Knopf `MOSAIC_PLATTENBAU` | `plate_builder.rs:220-228`, `:231-243` |
| Knopf ist prozessglobal | `OnceCell::get_or_init` ueber `std::env::var` | `column_build.rs:78` |
| Tiling bleibt Solver | `plate_builder::tiling_vorzug` hat GENAU EINEN Aufrufer, und der ist Log-Ausgabe hinter `if pcfg.column_build_trace` | `self_play.rs:1691`; Entscheidungspfad `resolve_tiling_step`, `:1093`; kein `plate_builder`-Aufruf in `tiling_solver.rs` |
| **`dome_vorzug` faehrt mit** | haengt in derselben Draft-Kette wie `drafting_vorzug` | `self_play.rs:1173` |
| Partie-Seed je Partie setzbar | `plate_builder::set_partie_seed(Some(game_seed))` | `self_play.rs:2286` |

**Folge:** der Arm ist ein zweiter Agent mit `vorzug: false` und `[p0, p1]` statt
`[player, player]`. Kein neuer Bauer, keine neue Heuristik, kein Eingriff in den
Tiling-Solver. Der prozessglobale Knopf bleibt unangetastet — er sagt nur, WELCHER
Bauer aktiv waere; WER ihn benutzt, entscheidet das Agenten-Flag.

**Der Kommentar `self_play.rs:1688`** (*"`resolve_tiling_step` prueft ihn intern
schon"*) ist insoweit irrefuehrend und wird beim Bauen berichtigt.

---

## par.3 WAS GEBAUT WIRD

**Arm S (asymmetrisch), primaer.** Self-Play-Korpus, in dem je Partie **genau
ein** Spieler den k1-Bauer-Vorzug hat:

- Seitenwahl aus dem Partie-Seed, Ziel-Aufteilung 50/50 ueber den Korpus.
- `MOSAIC_PLATTENBAU=1` (Spaltenbauer), Rest wie im Produktions-Self-Play.
- **`dome_vorzug` bleibt AN** (Begruendung und Gegenmessung: par.4).
- Tiling unveraendert (Solver), siehe par.2.

**Arm N (Kontrolle).** Derselbe Umfang, identische Seeds, **beide** Seiten ohne
Bauer-Vorzug — der heutige Zustand. Notwendig, weil sonst Korpusgroesse und
Erzeuger-Checkpoint mit der Asymmetrie konfundiert sind.

**Kein Arm mit beidseitigem Bauer.** Der existiert bereits (Destillations-Korpus,
`PREREG_ownership_corpus.md`) und ist genau der wegsymmetrisierte Fall.

**Training:** Warm Start vom Champion, Standardrezept (`lr 5e-5` + Cosine,
`--epochs` = tatsaechliches Budget, siehe Fussnote par.9). Fenster und
Traeger-Manifest wie im v21-Fenster; der neue Korpus ist **policy-tragend**
einzutragen — sonst wiederholt sich der Befund vom 2026-08-17 (sieben Laeufe mit
maskiertem Korpus, `neural_net.py:679/:667/:1804`).

---

## par.4 DIE ZWEI VORBEHALTE, DIE INS ERGEBNIS GEHOEREN

**(1) `dome_vorzug` faehrt mit.** Die Bauer-Kette entscheidet nicht nur den
Draft, sondern auch die **Kuppelplatten-Slot-Wahl** (`self_play.rs:1173`). Genau
dort hat das Netz eine gemessen falsche Gewohnheit (`DOSSIER` 7(5): 62,8 %
Spezialkuppeln nach unten, `domain_knowledge.md` §8 Hebel 2 verlangt oben).

Er bleibt AN, weil §8 Hebel 2 zum Ziel gehoert und ein halbierter Bauer die
Wirkung verduennt. **Gegenmessung, verbindlich:** die Slot-Verteilung (oben/unten
bei ausliegender k6-Platte) wird am Ende von Arm S **getrennt ausgewiesen**. Ohne
diese Zahl ist "der Kopf hat den Spaltenwert behalten" nicht von "der Kopf hat
eine Slot-Gewohnheit uebernommen" zu unterscheiden.

**Die Gegenmessung besteht aus ZWEI Zahlen** (Erweiterung nach externer
Durchsicht 2026-08-18, und sie ist noetig): neben der Slot-Verteilung die
**Platzierungspunkte in Partien OHNE k1-Treffer**, getrennt nach Zwangs- und
freier Seite. Holt die Zwangsseite dort mehr Punkte, ohne mehr Spalten zu bauen,
laeuft der Vorteil ueber die Slot-Wahl und die k1-Zurechnung faellt.

**(2) Ego-Perspektive vs. Regime.** Der Value-Kopf sieht nicht, ob ER der
gezwungene Spieler ist. Er lernt also "Brett mit Spaltenfortschritt gewinnt
oefter", nicht "ich sollte bauen". Das ist der beabsichtigte Mechanismus (die
Suche macht daraus die Praeferenz), aber es heisst: **ein Ausbleiben des Effekts
in Arm S widerlegt 7(1) nicht** — es koennte auch heissen, dass die Brettmerkmale
den Fortschritt nicht ausreichend tragen. Das ist in par.7 als
Nicht-Entscheidung protokolliert.

---

## par.5 SPERRE VOR DEM TRAINING — traegt der Korpus das Signal ueberhaupt?

**Vor** dem ersten Trainingslauf, auf dem fertigen Korpus S, drei Zahlen:

| Groesse | Warum | Vorabregel |
|---|---|---|
| **Siegquote der Zwangsseite** (Partien mit aktiver k1-Platte) | das ist das Signal, aus dem der Value-Kopf lernen soll | **nicht getunt** — siehe unten |
| **k1-Rate der Zwangsseite** | greift der Bauer ueberhaupt durch? | Erwartung ~42 % (`DOSSIER` 6a(C)); unter 30 % ist der Arm gegenstandslos |
| **k1-Rate der freien Seite** | Grundrate im selben Korpus | Erwartung ~13 % |

> **VORABREGEL par.5:** die Sperre ist bestanden, wenn die **Differenz der
> k1-Raten zwischen Zwangsseite und freier Seite >= 20 Prozentpunkte** betraegt.
> Darunter existiert die Asymmetrie nur auf dem Papier und es wird **nicht
> trainiert**.

**Die Siegquote ist ERGEBNIS, nicht Zielgroesse.** Die externe Spezifikation will
den Bauer nachziehen (epsilon), bis die Zwangsseite 55–70 % gewinnt. Das ist hier
**ausdruecklich verboten**: damit stellte man genau die Korrelation her, die der
Value-Kopf anschliessend "entdecken" soll — das Experiment waere
selbstbestaetigend. Die Quote wird gemessen und berichtet, in jeder Hoehe. Sie
ist zugleich die erste **unkonfundierte** Messung zu 6a(B) (ist Spaltenbau
gratis?), weil dort bisher nur ein Vergleich *innerhalb* eines Arms vorlag.

Ein Nachziehen der Bauer-Staerke ist genau **einmal** erlaubt, mit frischem
Korpus und hier nachgetragener Begruendung — nicht als laufende Anpassung.

**Kein epsilon-Rauschen.** Die Spezifikation will Varianz per epsilon-greedy
zumischen; die `.or_else`-Kette liefert sie strukturell schon (der Bauer greift
nur, wo er etwas vorschlaegt). Wie oft er greift, ist **ungemessen** und wird in
der Sperre mit ausgewiesen.

---

## par.6 MESSANORDNUNG

**Teilfrage B (Zuordnung), nach dem Training auf Korpus S.**

Der naheliegende Test — mittlerer Value bei Stellungen *mit* gegen *ohne*
Spaltenfortschritt — ist **konfundiert** und wird NICHT verwendet: Stellungen mit
fortgeschrittener Spalte sind auch die, in denen die Partie gut laeuft. Das ist
dieselbe Fehlerklasse, die in diesem Projekt bereits dreimal aufgetreten ist
(Endzustands-Ziel auf den bereits entschiedenen Teil gemessen).

Verwendet wird stattdessen ein **gepaarter Geschwister-Vergleich**: dieselbe
Stellung, Nachfolgezustaende, die sich im Spaltenfortschritt unterscheiden;
Referenz je Stellung, nicht ueber den Satz gemittelt. Die Maschinerie liegt im
Baum (`sibling_ranking_diagnostic`, `DOSSIER` 7(2)). Ausgewiesen wird die
**Differenz zum Nullarm-Modell auf denselben Stellungen**.

**Teilfrage C (Transfer).** Arena **Nullarm** (alle Regler 0, `MOSAIC_OWNERSHIP_W`
= `MOSAIC_OWNERSHIP_TILING_W` = 0) gegen den Champion, **407 feste Seeds**,
gepaart, Auswertung auf **Block-Ebene** (Bloecke a 25, nB=6, Schwelle |t| >
2,571). Partie-Level-p-Werte gelten nicht.

Nullarm ist Pflicht: gemessen werden soll, was das **Netz** gelernt hat, nicht
was ein Regler erzwingt.

**Brettwechsel:** derselbe Arm zusaetzlich mit vertauschten `--model`/`--model-b`
und eigenem `--out-prefix`. Grund: der Vorbehalt aus `STATUS.md` (alle bisherigen
drei Arme liefen auf Brett 0, der Seiteneffekt ist unkontrolliert).

---

## par.7 VORAB-ERFOLGSREGEL (woertlich, vor der ersten Partie)

**ERFOLG** heisst **beides**:

1. **k1-Rate im Nullarm** (Partien mit ausliegender k1-Platte, eigene Seite):
   - **>= 30 %** = Ziel erreicht.
   - **>= 22 %** = Signal, Fortsetzung gerechtfertigt, aber kein Erfolg.
   - **< 22 %** = kein Signal.
   Bezugswerte: heute **13 %** (20/156, `DOSSIER` 6(C)), Bauer **42 %**
   (419/1000). Die Zweistufigkeit ist bewusst: eine einzelne Schwelle bei 30 %
   haette einen echten Teileffekt bei 25 % verworfen, ohne etwas zu entscheiden.
2. **Siege**: im Nullarm gegen den Champion **nicht signifikant schlechter** als
   der Kontroll-Arm N auf denselben Seeds (Block-Ebene). Ein Plattenzuwachs, der
   Siege kostet, ist **kein** Erfolg (Leitstern-Klausel, `STATUS.md`).

**MISSERFOLG** heisst: k1-Rate < 22 % **oder** signifikanter Siegverlust.

**Die Trennschaerfe der k1-Rate ist VOR dem ersten Lauf auszurechnen** (bei 407
Seeds sind ~150 Partien k1-aktiv; ob 13 % gegen 22 % auf Block-Ebene mit nB=6
aufloest, ist **offen** und keine Annahme).

**AUSGERECHNET (2026-08-19, Monte-Carlo, 20.000 Wiederholungen, 6 Bloecke a
25, Block-Korrelation als Beta-Mischung bis ICC 0,1):** die Schwellen loesen
auf. P(Rate >= 22 % | wahre Rate 13 %) = 0,2-5,4 % je nach ICC — ein
Fehlsignal aus der heutigen Grundrate ist also selten. P(Rate >= 22 % |
wahre Rate 30 %) = 89-99 %. Erwartbar und kein Mangel: liegt die wahre Rate
GENAU auf einer Schwelle, ist deren Ueberschreiten ein Muenzwurf (~51 % fuer
beide Stufen) — genau dafuer ist die Zweistufigkeit da. Lesart: "kein
Signal" (< 22 %) ist bei echter Grundrate fast sicher korrekt, ein echter
30-%-Effekt wird fast sicher mindestens als "Signal" erkannt.

**WAS DIESER VERSUCH NICHT ENTSCHEIDET** (vorab, damit es hinterher nicht
umgedeutet wird):

- Ein Nullresultat widerlegt 7(1) **nicht** — siehe par.4(2).
- Er sagt nichts darueber, ob die *Ordnung* des Ownership-Kopfes richtig ist
  (7(2)). Das ist eine eigene Messung.
- Er sagt nichts ueber k2. Fokus-Regel.

---

## par.8 WAS VERWORFEN WIRD, UND WARUM

**Das dynamische Curriculum** (externe Spezifikation, Phase B/C: Bonus an den
Verlierer, dann an die Plattenpunkt-Differenz gekoppelt) wird **nicht gebaut**.

Begruendung: es koppelt das Value-Ziel an ein Regime, **das nicht in der
Beobachtung steht**. Der Value-Kopf saehe wieder nicht, warum der Wert schwankt —
dieselbe Fehlerklasse wie 7(1), nur mit Nicht-Stationaritaet statt Symmetrie.
Tragfaehig waere es erst, wenn der Armparameter **Eingabe** ist; das ist der
UVFA-Punkt aus `DOSSIER` Abschnitt 8 und eine eigene Entscheidungseinheit.

**Der Warmup ("Phase A")** entfaellt: der Champion IST die konvergierte
Grundlinie. Ein Aufwaermen auf symmetrischem Self-Play waere ein zusaetzlicher
Korpus ohne Frage dahinter.

---

## par.9 REIHENFOLGE UND FREIGABEN

1. **Kostenrechnung** — Korpusgroesse mal Partiekosten, ausgerechnet und hier
   nachgetragen (der Destillations-Korpus waren 8.000 Partien; die Uebertragung
   ist **ungerechnet**).
   **AUSGERECHNET (2026-08-19, aus den Datei-Zeitstempeln des
   Ownership-Korpus vom 14.08.):** der Netz-Arm `v21_own_a` (Champion beide
   Seiten, 200 Sims, 8 Threads) lief mit **10,3 Partien/min** — die beste
   Naeherung fuer den asymmetrischen Arm (der Bauer-Vorzug selbst ist
   billig). Damit: **Arm S 8.000 Partien ~ 13 h, Arm N nochmal ~ 13 h,
   zusammen ~ 26 h** sequenziell. Halber Umfang (2 x 4.000) waere ~ 13 h;
   ob das reicht, haengt an der Sperre par.5 (Raten-Differenz), nicht an
   der Arena — die par.7-Messung laeuft ohnehin auf den 407 Seeds.
   Umfang ist Nutzer-Entscheid beim Freigeben.
2. Umbau `self_play.rs` (zweiter Agent, `[p0, p1]`), Wheel neu bauen. **Ein
   gruener `cargo test` heisst nicht, dass die Arena den Code sieht** —
   Zahlengleichheit bei gleichen Seeds waere Alarm, kein Befund.
3. Korpus S und Korpus N erzeugen.
4. **Sperre par.5.** Bestanden → weiter, sonst Ende.
5. Training beide Arme, Traeger-Manifest gesetzt, Fenster mit
   `MOSAIC_DATA_EXCLUDE` gepinnt.
6. Messungen par.6, Auswertung nach par.7.

> **FREIGABE-VORBEHALT.** Dieser Arm erzeugt einen **neuen Self-Play-Korpus**.
> Der Fahrplan (`STATUS.md`) sperrt Korpus-Erzeugung bis Schritt 1 und 2 stehen.
> Praezedenz fuer einen *Lehr*-Korpus ausserhalb der Reihe ist
> `PREREG_ownership_corpus.md`. **Die Einordnung — Lehrkorpus (jetzt) oder
> Schritt 3 (spaeter) — ist eine Nutzer-Entscheidung und hier offen.**

**Fussnote zu `--epochs`:** `T_max` des Cosine haengt am `--epochs`-Flag; bei
`--epochs 100` und Early Stop nach 15 ist die LR faktisch konstant. Das Budget
ist vor dem Lauf realistisch zu setzen, sonst laeuft das Standardrezept ohne
Annealing.

---

## par.10 BEZUG ZU OFFENEN FRAGEN

- **7(1)** — direkter Test, das ist der Zweck dieser Datei.
- **6a(B)** — die Siegquote der Zwangsseite in par.5 ist die erste
  unkonfundierte Messung der Frage "kostet Spaltenbau etwas?".
- **7(5)** — die Slot-Gegenmessung in par.4(1) beruehrt die falsche Gewohnheit,
  entscheidet sie aber nicht.
- **7(2), 7(3), 7(4)** — unberuehrt. 7(3) laeuft eigenstaendig in
  `PREREG_reachability_target.md`.


## par.11 FREIGABE UND START-KONKRETISIERUNG (Nutzer, 2026-08-20)

**Freigegeben: voller Umfang (2 x 8.000 Partien), als Lehrkorpus ausserhalb
der Fahrplan-Reihe** (Praezedenz PREREG_ownership_corpus). Kein
Zusatz-Backup noetig — das automatische Tages-Backup (12:00) deckt
`data/` ab. **Start ERST NACH dem round5-Min-Knoten-Fix**
(`PREREG_round5_minfix_elo_reset.md`): die Runde-4/5-Labels des Korpus
laufen durch die betroffenen Loeser, der Korpus soll die reparierte
Engine sehen.

Festlegungen vor dem Start (Preflight 2026-08-20 bestanden: Seitenwahl
~50/50, Greifrate 15-22 je Partie nur auf der Zwangsseite):

- **Vier Bloecke a 4.000 Partien** (S1, S2, N1, N2), Basis-Seeds
  **20260830 / 20260831 / 20260832 / 20260833** (disjunkt von Korpus
  20260814 und Holdout 20260818-22). Datei-Granularitaet 10 Partien =
  natuerlicher Minuten-Checkpoint; bei Abbruch nur den fehlenden Rest
  mit Folge-Seed nachgenerieren.
- **Arm S:** `MOSAIC_ASYM_VORZUG=1`, `MOSAIC_PLATTENBAU=1`
  (k1-Spaltenbauer), Champion-Modell, 200 Sims, Streuung AUS
  (`MOSAIC_WERTUNG_STREUUNG_MAX` ungesetzt — die Seitigkeit ist die
  gewollte Varianz, par.5 verbietet Zusatz-Rauschen), rtv aus, 8 Threads,
  10 Partien/Datei, Ablage `data/asym_corpus/` via `MOSAIC_DATA_DIR`
  (nicht-rekursiver Fenster-Glob = Sperre, wie Holdout).
- **Arm N:** identisch, aber `MOSAIC_ASYM_VORZUG` und `MOSAIC_PLATTENBAU`
  UNGESETZT — der heutige Produktionszustand.
- **Zwischenkontrollen je Block** (protokolliert, nur Abbruch-Option):
  Vollstaendigkeit (Dateizahl x 10, 0 unvollstaendige), Greif-Statistik
  aus dem Log; nach S1 die par.5-FRUEHWARNUNG (k1-Raten-Differenz
  Zwangs- gegen freie Seite auf 4.000 Partien — liegt sie fern der
  20 pp, Abbruch statt Weiterlauf; die verbindliche par.5-Sperre laeuft
  unveraendert auf dem fertigen Korpus).
- Lauf in der Nutzer-Shell mit tee-Log (`logs/asym_corpus_<datum>.log`),
  Ueberwachung ueber Log + Dateizahl + Prozessliste.

## par.12 ERGEBNIS DER ABNAHME UND par.5-SPERRE (2026-08-21, Korpus fertig 18:43)

Log faktisch `logs/nacht_20260820.log` (gemeinsames Nachtlauf-Log statt
des in par.11 genannten Namens). Alle Zahlen an den Artefakten geprueft:

- **Vollstaendigkeit BESTANDEN**: 1.600 pkl-Dateien (800 S / 800 N), jede
  mit exakt 10 game_ids, 16.000 Partien, 0 unvollstaendige. Seitenwahl
  4032/3968 (50,4/49,6). Greif-Statistik Zwangsseite: min 8, Median 18,
  max 35, KEINE Partie ohne Greifer.
- **Fruehwarn-Gate nach S1** (04:16): +31,4 pp (34,6 % gegen 3,2 %),
  Kette lief weiter.
- **par.5-SPERRE BESTANDEN** (verbindlich, GESAMT-Korpus S, 8.000
  Partien, 0 ohne Log-Zuordnung): k1-Rate Zwangsseite **34,6 %**, freie
  Seite **3,3 %**, Differenz **+31,3 pp** >= 20 pp
  (`tools/probes/asym_early_rate_check.py --abbruch-pp 20`, Exit 0).
  Zur Erwartungstabelle in par.5: beide Raten liegen UNTER den
  Alt-Welt-Bezugswerten (~42 %/~13 % aus DOSSIER 6a(C)); die Bezugswerte
  stammen aus anderem Regime und Vor-Fix-Engine, fuer die Sperre traegt
  allein die Differenz. Die 30-%-Gegenstandslosigkeits-Schwelle
  (Zwangsseite < 30 %) ist NICHT gerissen (34,6 %).
- **Siegquote der Zwangsseite, protokolliert und NICHT getunt** (erste
  unkonfundierte 6a(B)-Zahl): **45,7 %** gesamt (3658/8000), **47,5 %**
  bei aktiver k1-Platte (1398/2942, k1 = ID 1, scoring.rs:43).
  Erzwungener Spaltenbau kostet im Selbstspiel also ~4 pp Siegquote.
  Fuer den Lernmechanismus (Korrelation Brettmerkmal/Ausgang) ist das
  unschaedlich; ein Nachziehen der Bauer-Staerke findet NICHT statt.
  **Lesart (Nutzer, 2026-08-21):** die ~4 pp sind der Preis des BLINDEN
  Zwangs, kein Deckel fuer gelernten Bau -- der trainierte Arm muss aus
  den Daten SELEKTIVES Bauen lernen (wann die Platte es bezahlt, wann
  die Farben platzierbar bleiben), nicht den Zwang imitieren. Genau das
  prueft par.7: Nullarm-Baurate UND kein Siegverlust; ein Netz, das nur
  den Zwang nachahmt, faellt an der zweiten Bedingung. Der Split stuetzt
  die Richtung: bei aktiver k1-Platte kostet der Zwang weniger (47,5
  gegen 45,7 %).

**Warum der Bauer AUCH OHNE aktive k1-Platte greift (Nutzer-Frage
2026-08-21, nachgetragen; die Immer-an-Wahl war in par.3/par.11 nur
implizit):** k1 lag in 2.942 von 8.000 Zwangspartien aus (~37 %,
Ziehchance 3/8), der Bauer lief in ALLEN. Drei Gruende:

1. **Der Kontrast ist das Interaktions-Signal.** Das Netz soll nicht
   "Spalten sind gut" lernen, sondern "Spalten sind MEHR wert, wenn k1
   ausliegt" -- das verlangt Bauen mit UND ohne Platte im selben Regime.
   Gemessen traegt der Kontrast: Siegquote Zwangsseite 47,5 % mit
   aktiver k1-Platte gegen 44,7 % ohne (2260/5058, Arithmetik aus den
   Abnahme-Zaehlern). Ein Platten-Gate am Bauer haette "Zwangsseite"
   perfekt mit "k1 liegt aus" konfundiert.
2. **Selektives Bauen braucht Negativ-Beispiele.** Partien ohne Platte
   zeigen, wann Bauen NICHT lohnt; eine volle Spalte bringt auch ohne
   Platte die 21 Platzierungspunkte (PREREG_provocation.md par.2), ist
   also der Basiswert-Fall, nicht sinnloses Spiel.
3. **Die Auswertung bedingt auf die Platte, der Korpus nicht:** par.7
   misst die Nullarm-Baurate auf Partien MIT ausliegender k1-Platte,
   und die Bezugswerte 42 %/13 % stammen ebenfalls aus dem
   Immer-an-Regime. Ein Platten-Gate waere zudem neuer Mechanismus
   (die .or_else-Kette kennt keine Plattenbedingung) und haette die
   Zwangsstichprobe je Klasse verkleinert.

## par.13 TRAININGSERGEBNIS + MESSAUFBAU (2026-08-22 frueh, VOR den Arena-Ergebnissen festgehalten)

- **Beide Arme trainiert** (identisches Rezept, seed 2, Fenster an der
  Cache-Zeile verifiziert: je 2638 Dateien, Traeger 1380 mit 800/800
  des jeweiligen Korpus): Arm S Early Stop 19/20 (best Ep. 11,
  brierbest Ep. 6, Brier 0,1842), Arm N Early Stop 15/20 (best Ep. 5,
  brierbest Ep. 2, Brier 0,1852). ONNX-Exporte + Snapshots liegen.
- **Checkpoint-Wahl fuer die par.6/par.7-Messungen: `_best` beider
  Arme.** Begruendung VOR der ersten Partie: die Kampagnen-Praezedenz
  (N/S/T+S-Arena, z. B. `paired_arena_env_reach2_ts_b24.json`) lief mit
  `v21-b24_best`; gleiche Regel fuer beide Arme, keine nachtraegliche
  Checkpoint-Selektion nach Ergebnis.
- **Seeds: exakt die 407 Kampagnen-Seeds** (aus dem b24-Artefakt
  extrahiert nach `evaluations/seeds_asym_407.txt`) -- par.7 verlangt
  den S/N-Vergleich "auf denselben Seeds", und so bleiben die Zahlen
  zusaetzlich zur b18/b24-Reihe einordbar.
- **Drei Laeufe, sequenziell und exklusiv** (Instrument
  `paired_arena_env_ab.py`, Null-Knopf-Muster, 400/400 Sims,
  `--log-games` fuer die k1-Raten aus DENSELBEN Partien):
  (1) S_best gegen Champion, (2) N_best gegen Champion,
  (3) Brettwechsel des S-Arms (vertauschte --model/--model-b).

## par.14 ARENA-ERGEBNIS TEILFRAGE C (2026-08-22): KEIN SIGNAL, kein Siegverlust

Artefakte `paired_arena_env_asym_nullarm_{s,n,s_swap}.json`; k1-Raten
aus den Endwertungs-Zeilen der Partie-Logs ("Vertikale Reihen: X Pkt",
Schwelle >= 7 = mindestens eine Spalte), je Lauf dieselben 156
k1-aktiven Partien -- exakt der DOSSIER-6(C)-Nenner, die Zahlen sind
direkt vergleichbar. (Zwischenfall protokolliert: Lauf 2 wurde einmal
neu gestartet, weil eine Pickle-Ladelast parallel lief; der
Kalibrierungs-Smoke ergab spaeter 4x byte-identisch unter genau dieser
Lastklasse -- der Neustart war ueberkonservativ, aber regelkonform.)

| Groesse | S (Lehr-Arm) | N (Kontrolle) |
|---|---|---|
| k1-Rate eigene Seite (k1-aktiv) | **19/156 = 12,2 %** (Brettwechsel: 20/156 = 12,8 %) | 15/156 = 9,6 % |
| Champion-Gegenseite | 12/156 = 7,7 % | 14/156 = 9,0 % |
| Siege gegen Champion | 199/407 (Swap 184/407) | 205/407 |

- **VERDIKT nach par.7 (woertlich): MISSERFOLG als "kein Signal"** --
  12,2 % liegt unter der 22-%-Signalschwelle und exakt auf der
  registrierten Grundrate (heute 13 % = 20/156). Der Brettwechsel
  bestaetigt (12,8 %).
- **Kriterium 2 waere erfuellt gewesen**: kein signifikanter
  Siegverlust gegen N auf denselben Seeds (McNemar diskordant 97:103,
  p=0,72; Block-Ebene nB=17 a 25, Block-t = -0,53).
- **Vorregistrierte Einordnung gilt**: das Nullresultat widerlegt 7(1)
  NICHT (par.4(2), Ego-Perspektive). Die Trennung "nichts gelernt"
  gegen "gelernt, aber nicht suchwirksam" leistet allein Teilfrage B
  (gepaarter Geschwister-Vergleich S- gegen N-Netz auf denselben
  Stellungen) -- sie steht als naechster Schritt aus.

## par.15 TEILFRAGE B GEMESSEN (2026-08-22) + GESAMTVERDIKT

Instrument NEU (`tools/probes/asym_value_sibling_check.py`, Artefakt
`evaluations/artifacts/asym_value_sibling_check.json`): identische Stellungsbasis
fuer beide Netze (der bestehende Nachfolger-Dump
`probe_sibling_succ_k1_w1.0.json`, 40 Runde-2-Stellungen aus
Champion-Suchlaeufen), je Kandidat rohes Value-Kopf-Urteil
(ONNX-Ausgang 'value', ego-kodiert, Zieher-Vorzeichen per
Nullsummen-Flip wie net_leaf_eval) gegen den k1-Puffer-Fortschritt des
Ziehenden (`reach_buffer_columns`, wie in der Praedikat-Sonde);
Kendall-Tau je Stellung, gepaarte Differenz.

| Groesse | Wert |
|---|---|
| auswertbare Stellungen | 33 |
| Tau S (Value ~ k1-Puffer) | **-0,077** |
| Tau N | **-0,185** |
| Differenz S-N | +0,107 (sd 0,72, t +0,86) |
| Vorzeichen S besser / N besser / gleich | 17 / 8 / 8, p(Vorzeichentest) 0,108 |

Keine vorregistrierte Schwelle (par.6 verlangt nur den Ausweis);
Kaveats: nur 33 Runde-2-Stellungen, Positionsauswahl aus
Champion-Laeufen, roher Value-Kopf statt Such-Blend.

**GESAMTVERDIKT des Curriculums (par.7-Regel plus Teilfrage B):**

1. **MISSERFOLG als "kein Signal"** -- Nullarm-k1-Rate 12,2 % (=
   Grundrate), und der Value-Kopf ordnet Geschwister auch mechanisch
   nicht nach Spaltenfortschritt (Tau S -0,08; nur ein schwacher,
   nicht signifikanter Richtungshinweis gegenueber N). Arena und
   Mechanik-Sonde konvergieren: es wurde nichts Suchwirksames gelernt,
   und auch kein starkes, nur verdecktes Zustandssignal.
2. **Kein Staerkepreis** (Kriterium 2 erfuellt; S 199/407 gg. N
   205/407, n.s.).
3. Vorregistrierte Grenzen: 7(1) ist damit NICHT widerlegt (par.4(2));
   moeglich bleibt, dass die Brettmerkmale den Fortschritt nicht
   tragend abbilden -- das waere aber ein anderes Projekt (Merkmals-/
   Zielseite), nicht dieses Curriculum in dieser Form.
4. **Die par.4-Gegenmessungen (Slot-Verteilung, Platzierungspunkte
   ohne k1-Treffer) entfallen begruendet**: sie dienen der
   ATTRIBUTION eines Effekts, und es gibt keinen Effekt zu
   attribuieren.
5. Damit ist der im par.7-Umfeld registrierte Wertekopf-Weg
   durchgemessen; offen bleibt laut STATUS die **Policy-Seite**
   (orakel-abgeleitete Supervision) als letzter Strang. Umfang und
   Reihenfolge sind Nutzer-Entscheid.

## par.16 NEBENFUND (2026-08-22, planungstragend): das S-Training WAR bereits Verhaltens-Klonen -- und es druckte sich nicht aus

Am Code verifiziert bei der Vorpruefung des Policy-Zuschnitts: greift
der Bauer, zeichnet das Self-Play SEINEN Zug als One-Hot-Policy-Ziel
auf (prob 1.0, keine Suche; self_play.rs:1396-1398), und diese Schritte
sind im Cache voll policy-gueltig (pol_w=1.0: Drafting-Phase, kein
Start-Schritt, asymS-Dateien 800/800 Traeger, kein
policy_target_valid-Feld ohne PCR; neural_net.py:1814-1834). Bei median
18 Greifern je Zwangspartie enthielt das S-Training damit geschaetzt
~144.000 Klon-Ziele "bau die Spalte" (Schaetzung aus der
Greif-Statistik par.12). Ergebnis trotzdem: Nullarm-Baurate =
Grundrate (par.14).

Das ist der ZWEITE Null-Befund dieser Mechanik (Block H: Destillation
der Bauer-Korpora liess die Zielkriterien ebenfalls unbewegt) und
passt zum registrierten Kernbefund des Anlasses: der Prior bietet den
Bauzug laengst dominant an (4,91x), ueberstimmt wird er vom
Wert-Backup. **Folgerung fuer den Policy-Zuschnitt: naives
Policy-Klonen ist zweifach vorbelastet; der gemessene Engpass ist die
Ununterscheidbarkeit des Regimes (widerspruechliche Ziele auf
denselben Brettmerkmalen) plus das Wert-Veto in der Suche.** Der
daraus geschnittene Nachfolger: `PREREG_uvfa_plate_regime.md` (Regime
als Netz-EINGABE).

**par.9 Schritt 5 gestartet** (beide Arme sequenziell, identisches
Rezept/Seed): Warm Start `v21_2d_brierbest`, lr 5e-5 + Cosine,
`--epochs 20` (echtes Annealing, T_max-Fussnote beachtet), 2d/wdl/
opp-points/endgame, nortv, `--seed 2`, `--extra-data-dir
data/asym_corpus`. Fenster gepinnt: b18-Regex plus Ausschluss des jeweils
ANDEREN Arms; Traeger-Manifeste `data/policy_carrier_manifest_asym{S,N}.
json` (v21-Traeger plus jeweiliger Korpus policy-tragend, 800/800;
Traeger gesamt 1380). An der Cache-Zeile verifiziert (Arm S): Root-Filter
800/2945, Lade-Filter 733/3371 (asymN raus), geladen 2638 Dateien.
**Doku-Falle**: das automatische Trainings-Manifest listet die
Zusammensetzung VOR dem Lade-Filter (asymN faelschlich enthalten, mit
falscher Spielzahl) -- fuer die Fenster-Wahrheit gilt die Cache-Zeile im
Log, nicht das Manifest.

## par.17 NACHMESSUNG des Geschwister-Instruments auf v22-b05 (2026-08-29, Fahrplan Phase 0.2)

Dieselbe Sonde (asym_value_sibling_check, seit heute mit
--model-s/--model-n/--out parametrisierbar; Ein-Modell-Modus ohne
Paarvergleich), derselbe Dump (probe_sibling_succ_k1_w1.0.json, 33
gewertete Stellungen): der rohe Value-Kopf von v22-b05 ordnet die
Geschwister-Nachfolger mit **Tau +0,338** nach k1-Spaltenfortschritt --
Vorzeichenwechsel gegenueber den plattenblinden Netzen der
Erstmessung (S -0,077 / N -0,185, par.15). Die Ordnungs-Faehigkeit,
die das Asym-Curriculum nicht erzeugen konnte, ist ueber die
DAgger-/Lehrerkorpus-Linie entstanden. Einschraenkung: die GROESSE der
Reaktion bleibt gedaempft (R5-Steigung 0,0886,
PREREG_r5_value_calibration Nachmessung) -- Ordnung ja, Betrag nein.
Artefakt: evaluations/artifacts/b05_value_sibling_check.json.
