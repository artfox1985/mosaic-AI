<!-- STATUS: OFFEN | Frage: Wird die Min-Knoten-Zugsortierung in round5.rs und round_transition_deep.rs hart gefixt, und wie wird die dadurch entwertete Elo-Leiter neu verankert (v21/v20/v19 + Anker)? | Beleg: Nutzer-Entscheid 2026-08-20 ("du kannst ihn jetzt schon fixen und dann faehrst du die arena games mit v21, v20 und v19. die alte elo leiter kannst ins archiv werfen"). Fix-Grundlage: PREREG_implementation_review_unprimed par.7 Befund 1. -->

# PREREG: round5-Min-Knoten-Fix + Neuverankerung der Elo-Leiter

Stand **2026-08-20**. Nutzer-Entscheid liegt vor; dies registriert den
Zuschnitt VOR dem Bau.

**Anlass.** `PREREG_implementation_review_unprimed.md` par.7 Befund 1
(bestaetigt): `ordered_children` sortiert an Min-Knoten mit wurzelfester
Perspektive absteigend — unter dem Knotenbudget (200 = p75) werden die
Gegner-Widerlegungen bevorzugt abgeschnitten, Min-Werte liegen systematisch
zu hoch. Zweite Fundstelle `round_transition_deep.rs` (Budget 40). Der
Heuristik-ANKER spielt Runde 5 durch denselben Loeser (`mcts.rs:746ff`) —
ein Fix veraendert daher JEDE Seite jeder Partie mit Runde-5-Anteil, und
die bestehende Elo-Leiter verliert ihre Vergleichbarkeit. Der
Nutzer-Entscheid ist der harte Fix mit komplettem Leiter-Neuaufbau statt
eines Knopfs.

## par.1 DER FIX (beide Fundstellen, hauseigenes korrektes Muster)

Sortierschluessel wird die Sicht des am KNOTEN ziehenden Spielers
(`state.current_player`), absteigend — an Max-Knoten identisch zu heute,
an Min-Knoten "beste Widerlegung zuerst" (Vorbild `self_play.rs:3398-3411`):

1. `round5.rs::ordered_children` — `leaf_value(s, state.current_player)`
   statt `leaf_value(s, perspective)` als Sortierwert (die RUECKGABE von
   `negamax` bleibt in `perspective`-Sicht; nur die Ordnung wechselt).
2. `round_transition_deep.rs::ordered_children_pruned` — analog (die
   perspektiv-relative Fortschritts-Differenz fuer die Sortierung aus der
   Sicht des Ziehenden, Vorzeichen beachten).

**Abnahme vor dem Wheel:** je Fundstelle ein Unit-Test, der an einem
konstruierten Min-Knoten belegt, dass die fuer den ZIEHENDEN beste
Widerlegung vorn steht; `cargo test --release` vollstaendig gruen.
**Erwartung an die Paritaetsprobe: der Hash AENDERT sich absichtlich** —
der neue Hash wird hier nachgetragen und ist die neue Basislinie.
Determinismus-Smoke (2x8 identisch) nach Wheel-Installation bleibt Pflicht.

## par.2 KONSEQUENZEN, vorab benannt

- **Alle Alt-Messungen mit Runde-5-Anteil verlieren die Vergleichbarkeit
  ueber die Fix-Grenze hinweg.** Innerhalb der Alt-Welt bleiben sie gueltig
  (beide Arme spielten denselben Fehler). Kuenftige Arenen laufen auf der
  Fix-Engine.
- **Elo-Leiter:** `evaluations/elo_history.csv` wird nach
  `archive/elo_history_pre_r5fix.csv` verschoben (Nutzer-Freigabe im
  Beleg-Kopf); eine frische `elo_history.csv` beginnt mit den
  Neuverankerungs-Kanten.
- **Der Asym-Korpus wird ERST NACH dem Fix generiert** (seine
  Runde-4/5-Labels laufen durch die betroffenen Loeser).

## par.3 NEUVERANKERUNGS-KANTEN (Nutzer: "v21, v20 und v19")

Kader nach stehender Praxis (Promotions-Checkliste Punkte 2-4):

| Kante | n | Anmerkung |
|---|---|---|
| v21_2d_brierbest gegen Heuristik@150(dyn) | 150, kein Fruehstopp | Anker-Kante |
| v20_2d_opp_brierbest gegen Heuristik@150(dyn) | 150, kein Fruehstopp | Anker-Kante |
| v19_2d_best gegen Heuristik@150(dyn) | 150, kein Fruehstopp | Anker-Kante |
| v21 gegen v20 (@400) | 200 Paare | Nachbar-Kante |
| v20 gegen v19 (@400) | 200 Paare | Nachbar-Kante |

Auswertung wie bisher (Elo-Fit ueber die Kanten, Anker definiert den
Nullpunkt). KEINE Erfolgsregel im Sinne einer Hypothese — das ist eine
NEUVERMESSUNG, kein A/B; die Reihung v19 < v20 < v21 ist Erwartung, ihr
Ausbleiben waere ein eigener Befund und wuerde hier protokolliert.
Exklusiv-Regel gilt (keine Nebenlast).

## par.4 ERGEBNIS FIX-ABNAHME (2026-08-20, vor den Leiter-Laeufen)

- Fix umgesetzt (beide Fundstellen, Sortierschluessel = Knoten-Zieher;
  `perspective`-Parameter der Sortierfunktionen entfaellt), 4 neue
  Ordnungstests, **Suite 464/0**. Keine Alt-Erwartung musste angepasst
  werden. Kosmetik-Fixes (Feature-Kommentare, inkl. der Zwillingsstelle
  `features.rs:575`) mitgenommen.
- Wheel neu gebaut und installiert. **Abdeckungsbefund an der
  Paritaetsprobe: ihr Hash blieb UNVERAENDERT (8c6684ff...)** — die Probe
  erreicht die R5-/Deep-Pfade nicht. Die Verhaltensaenderung ist
  stattdessen direkt belegt: 8-Partien-Probe gegen die Alt-Engine, **2 von
  8 Partien verlaufen anders** (gleiche Seeds), Sieger in dieser
  Stichprobe zufaellig identisch. Determinismus der Fix-Engine: 2x8
  byte-identisch. Die Paritaets-Basislinie bleibt formal 8c6684ff; die
  Abdeckungsluecke der Probe ist als eigener niedriger Befund
  protokolliert. **Nachtrag 2026-08-22 (Nutzer-Frage): dieselbe
  Abdeckungsluecke gilt fuer den A4-Anker-Verhaltenstest** -- sein
  Korpus besteht aus Drafting-Zustaenden (mcts.rs::a4_anchor_corpus)
  und erreicht die R5-Pfade ebenfalls nicht; deshalb blieb die Fixture
  beim Fix unveraendert gruen. Das Anker-Verhalten in Runde 5 ist
  stattdessen durch die neu gefochtenen Anker-Kanten dieser Prereg
  abgedeckt. Beauftragt: Fixture v2 mit einem Runde-5-Zustand, der das
  NACH-Fix-Verhalten einfriert (Umsetzung nach Abschluss der laufenden
  Arena-Messungen, wegen Compile-Lastspike).


## par.5 ERGEBNIS DER NEUVERANKERUNG (registriert 2026-08-21)

Alle 5 Kanten im Nachtlauf 2026-08-20/21 gefahren (Nutzer-Shell, Log
`logs/nacht_20260820.log`), exklusiv, ohne Fruehstopp; Zahlen an den
Artefakt-JSONs verifiziert (`paired_arena_env_elo_r5fix_*.json`). Ein
Fehlstart der ersten Kante (exit 2, fehlende Argumente, 22:53) wurde vor
Spielbeginn neu abgesetzt — keine Partie doppelt.

| Kante | Ergebnis | Seed |
|---|---|---|
| v21_2d_brierbest@400 gegen Heuristik@150(dyn) | **116:34** (n=150) | 20260834 |
| v20_2d_opp_brierbest@400 gegen Heuristik@150(dyn) | **103:47** (n=150) | 20260834 |
| v19_2d_best@400 gegen Heuristik@150(dyn) | **112:38** (n=150) | 20260834 |
| v21 gegen v20 (@400) | **217:183** (n=400) | 20260835 |
| v20 gegen v19 (@400) | **238:162** (n=400) | 20260836 |

Bradley-Terry-Fit (`tools/elo_tracker.py report`, Anker Heuristik@150 = 1000,
Bootstrap-CI 95 %), eingetragen in die frische `evaluations/elo_history.csv`
(Contract-Stempel a169ebf0a4451e08, Knobs leer = Default):

| Knoten | Elo | 95%-CI |
|---|---:|---|
| v21_2d_brierbest@400 | **1215** | [1170, 1259] |
| v20_2d_opp_brierbest@400 | **1186** | [1144, 1227] |
| v19_2d_best@400 | **1136** | [1097, 1178] |

**Die Reihung v19 < v20 < v21 haelt im Fit** (Punktschaetzer; die
Nachbar-CIs ueberlappen). Ein Nebenbefund gehoert protokolliert: auf den
Anker-Kanten allein laege v19 (112) numerisch UEBER v20 (103) — die
Differenz von 9 Siegen bei n=150 traegt aber keine Ordnungsaussage, und
beide Direktkanten (217:183, 238:162) zeigen in die erwartete Richtung;
der Fit gewichtet sie mit n=400 entsprechend staerker.

Einordnung, nicht Verrechnung: im Alt-Register (`archive/
elo_history_pre_r5fix.csv`) stand v21 bei 1349 auf einer LAENGEREN Leiter
(mehr Kanten, mehr Zwischenstufen) und der Alt-Engine. Der Niveau-
Unterschied zur neuen 1215 ist damit doppelt konfundiert (Leiterlaenge +
Fix-Grenze) und KEINE Staerkeaussage — die Regel "Kanten ueber die
Fix-Grenze nie mischen" gilt unveraendert.
