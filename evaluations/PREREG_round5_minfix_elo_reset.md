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

## par.4 ERGEBNIS (leer bei Registrierung)
