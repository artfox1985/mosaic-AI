<!-- STATUS: OFFEN | Frage: Reagieren SPIELEN und LABELN unterschiedlich auf Suchtiefe -- und heilt ein tieferes Nachlabeln der gespeicherten Zustaende (Reanalyze) die Betrags-Daempfung des Value-Kopfs? | Beleg: ANGELEGT 2026-08-30, nichts gebaut. Zwei unabhaengige Motive (Literatur-Anti-Drift + der gemessene Sims-Effekt), Machbarkeit GEPRUEFT (net_search_state_json, lib.rs:865, freie Sims-Zahl auf gespeicherten Zustaenden). Teil A braucht einen flach gespielten SOCKEL, Teil B zielt auf den Value-Bootstrap. -->

# Vorregistrierung: Reanalyze -- Spielen und Labeln entkoppeln

**Angelegt 2026-08-30** auf Nutzer-Auftrag ("das muessen wir mal
aufschreiben und mit dem Phasenplan abgleichen"), VOR jeder Messung.

## par.1 Zwei unabhaengige Motive, die auf dasselbe Werkzeug zeigen

**(1) Anti-Drift (Literatur).** Die Research-Durchsicht 2026-08-29 hat
Reanalyze als den Standard-Mechanismus gegen die Moving-Target-Falle
iterierten Self-Plays benannt (RESEARCH_alphazero_improvements Fund 2,
Uebertragbarkeit "HOCH" wegen des perfekten Simulators). Im Projekt ist
er UNBESETZT -- geprueft per Grep ueber alle Preregs: ausser dieser
Datei erwaehnt ihn keine. Das gebaute
`tools/relabel_drafts_with_teacher.py` ist etwas anderes: es ersetzt
POLICY-Ziele durch LEHRER-Zuege und laesst die Value-Felder
ausdruecklich unberuehrt (Docstring).

**(2) Der gemessene Sims-Effekt (neu, 2026-08-30).** Flachere Suche
SPIELT bei b05 spaltenreicher und punktstaerker
(PREREG_search_depth_column_optimum: 100 Sims 0,6225 gegen 400 Sims
0,3375). Das NETZ-Self-Play koppelt aber Spielen und Labeln in einer
Suche, waehrend der hv2-Korpus sie trennt (Heuristik spielt, Netz
labelt mit 600). Wenn die beiden Rollen unterschiedlich auf Tiefe
reagieren, ist die Entkopplung die saubere Loesung -- flach spielen,
tiefer nachlabeln.

## par.2 Voraussetzungen, mit Pruefstand

| # | Voraussetzung | Stand |
| --- | --- | --- |
| 1 | flache Suche spielt wirklich besser | OFFEN -- Self-Play-Zahlen ja, Arena steht aus (Sims-Prereg Stufe 3) |
| 2 | tiefe Suche labelt wirklich besser | UNGEPRUEFT, und es gibt keine neutrale Referenz (ein tieferes Orakel ist derselbe Bewerter mit mehr Zeit) -- deshalb ist Teil A ein END-TO-END-Test, kein Metrik-Vergleich |
| 3 | die Engine kann nachlabeln | **ERFUELLT**: `net_search_state_json(state_json, model_path, sims, c_puct, seed)`, lib.rs:865 -- nimmt gespeicherte Zustaende und eine FREIE Sims-Zahl. Offen bleibt der Fuenf-Minuten-Check, ob die Rueckgabe die BESUCHSVERTEILUNG traegt (das Policy-Ziel) oder nur Zugbewertungen |

## par.3 TEIL A -- reagieren Spielen und Labeln unterschiedlich? (Policy-Seite)

**Anordnung (die einzige, die die Rollen trennt):** EIN Spielkorpus,
ZWEI Label-Varianten.

* Korpus: der **SOCKEL** (Policy-Klasse) des v22-Self-Play, flach
  gespielt. NICHT der Schwarm -- der laeuft `--value-only` und traegt
  per Konstruktion keine gueltigen Policy-Ziele, dort gaebe es nichts
  nachzulabeln (Nutzer-Praezisierung 2026-08-30).
* Arm A1: Labels wie gespielt (flache Tiefe).
* Arm A2: alle Draft-Zustaende mit tiefer Suche (400) nachgelabelt.
* Sonst identisch: gleiches Fenster, gleicher Seed, gleiches Rezept.

**Zielmetrik (vorab):** die arena-validierten Orakelmetriken
(`prior_mass_on_oracle_top3`, `kendall_tau`, 7/7 richtig), bei
Gleichstand die Arena. Ausdruecklich NICHT ein Vergleich der Labels
untereinander -- dafuer fehlt die neutrale Referenz (par.2 Nr. 2).

**Kosten (Annahme, aus 12,5 s je 400-Sims-Partie und ~80 Zuegen):**
~0,15 s je Zustand. Ein voller 12.000-Partien-Korpus haette ~600.000
Draft-Zustaende, also rund einen Tag -- fuer den A/B genuegt eine
Teilmenge (1.000 Partien, ~2 h). Dazu zwei Afterburner-Trainings.

**Bedingung, die den Test ueberhaupt erst moeglich macht:** der Sockel
muss FLACH gespielt worden sein. Faellt die Sims-Entscheidung auf eine
tiefe Sockel-Suche, sind die Labels schon tief und es gibt nichts
nachzulabeln -- dann braeuchte Teil A einen eigenen Korpus.

## par.4 TEIL B -- Value-Reanalyze gegen die Betrags-Daempfung

Die Value-Ziele tragen einen Bootstrap-Anteil aus der Suche (`root_q`).
Ihn mit dem AKTUELLEN Netz und tieferer Suche nachzurechnen ist die
Haelfte, die in der Literatur den Ausschlag gibt, und sie zielt direkt
auf den gemessenen Defekt (R5-Platten-Steigung 0,0886, Fahrplan
Phase 0). Betrifft den SCHWARM (Value-Klasse) und den Sockel
gleichermassen.

**Ehrlicher Vorbehalt, der Teil B von Teil A unterscheidet:** hier
labelt dasselbe Netz nach, dessen Bewertung verzerrt IST. Reanalyze
verbessert dann die Konsistenz (weniger Drift gegen ein veraltetes
Netz), aber nicht notwendig die Richtigkeit. Ein Gewinn ist zu
erwarten, wenn die Ziele von einem SCHWAECHEREN Vorgaenger stammen --
genau der Fall im Generationen-Loop, nicht im Erstlauf.

## par.5 Abgleich mit dem Phasenplan (STATUS)

* **Phase 2 (Generationen-Lauf) geht VOR** -- beide Teile brauchen den
  Korpus, den sie erst erzeugt.
* **Phase 3.1 des Fahrplans nannte "Reanalyze-light" bereits als
  Kandidaten**, aber ohne Prereg und ohne die Label-Tiefen-Frage. Diese
  Datei ersetzt den losen Eintrag; der Fahrplan verweist hierher.
* **Reihenfolge innerhalb Phase 3:** Teil A ist billiger und
  beantwortet eine Frage, die den naechsten Erzeugungslauf betrifft
  (Sockel-Tiefe). Teil B ist der eigentliche Angriff auf die
  Daempfung, aber er lohnt erst in Generation 2+ (siehe par.4).
* **Abhaengigkeit nach unten:** faellt die Arena der Sims-Prereg
  (Stufe 3) gegen die flache Suche aus, entfaellt Motiv (2) -- Teil A
  bleibt dann nur als Label-Frage bestehen, mit deutlich geringerer
  Dringlichkeit.
