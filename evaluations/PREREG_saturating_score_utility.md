<!-- STATUS: OFFEN | Frage: Verwandelt eine KataGo-treue Score-Utility (Saettigung um den RE-ZENTRIERTEN Wurzel-Score, integriert ueber die Score-Verteilung) die gemessene, aber wertlose Punktemarge in Siege -- dort, wo die vorhandene lineare Mischung gescheitert ist? | Beleg: nichts gebaut, Entwurf angelegt 2026-08-23; Ausarbeitung liegt in research_value_head_alternatives_DRAFT.md Idee 1.1, war aber nie vorregistriert. Empirischer Anker: Task #12 Block 2, Marge +2,25 bei 151:149 -->

# Vorregistrierung: Gesaettigte, re-zentrierte Score-Utility

**Angelegt 2026-08-23, VOR jedem Bau.**

## par.1 Anlass

Task #12 hinterliess einen Befund, der bis heute unerklaert und unbehandelt
ist. Im belastbaren Arena-Block (n=150; Block 1 hatte n=75 mit SPRT-Stopp,
und die Projektlehre dazu lautet "n<=75 ist Kontext, keine Referenz") stand:

| Groesse | Wert |
|---|---|
| Durchschnittsmarge dist gegen v18 | **+2,25** (39,27 gegen 37,02) |
| Partieergebnis | **151:149** |

Positive Durchschnittsmarge bei exaktem Gleichstand heisst: der Arm gewinnt
groesser, wenn er gewinnt. Die Zusatzpunkte fallen in ohnehin entschiedenen
Partien an, und dort sind sie wertlos.

Das ist eine **gemessene Faehigkeit, die vollstaendig an der Siegschwelle
verpufft**. Das Netz kann etwas, das die Suche nicht in Siege uebersetzt.

`research_value_head_alternatives_DRAFT.md` Idee 1.1 benennt den Grund und
den Ausweg, mit Primaerquelle (Wu, KataGo, arXiv:1902.10565, Appendix F),
Aufwandsschaetzung und Erfolgskriterium. Sie wurde nie vorregistriert und
nie gebaut. Diese Prereg holt das nach.

## par.2 Was heute im Code steht

In dieser Sitzung selbst gelesen, `engine/src/net_mcts.rs`:

```rust
fn value_to_win_prob(value: &[f32]) -> f64 {        // :2227-2230
    let v = value.first().copied().unwrap_or(0.0) as f64;
    (v + 1.0) / 2.0
}

let wr  = calibrate_win_prob_with(value_to_win_prob(value), cal_a, cal_b);  // :2287
let pts = value_to_win_prob(points);                                        // :2291
let legacy_blended = (1.0 - W) * wr + W * pts;                              // :2297, W = 0.0
```

Vier Abweichungen von der KataGo-Form, alle vier im Code sichtbar:

1. **Der Punkte-Wert wird durch dieselbe lineare Abbildung geschickt wie der
   Sieg-Wert** (`value_to_win_prob(points)`, :2291). Eine tanh-gestauchte
   Punktzahl wird damit als Wahrscheinlichkeit behandelt.
2. **Additiv-lineare Mischung** statt eines eigenen Utility-Terms (:2297).
3. **Keine Integration ueber eine Score-Verteilung** -- der Kopf liefert nur
   einen Erwartungswert, eine Streuung existiert nirgends.
4. **Keine Re-Zentrierung** auf den Wurzel-Score.

Der Praezedenzfall gehoert dazu: `POINTS_UTILITY_WEIGHT` wurde am
2026-07-19 mit 0,5 (1:14) und 1,0 (0:12) getestet, spaeter w=0,1 gegen w=0
mit 300/400 zu 321/400 (Block-t −2,68). Die naive Form ist damit **klar
widerlegt**. Diese Prereg reaktiviert diesen Knopf ausdruecklich nicht,
sondern baut einen anderen Term daneben.

## par.3 Der eigentliche Befund: es fehlt nicht die Saettigung, es fehlt die Re-Zentrierung

Dies ist der Punkt, an dem diese Prereg ueber Idee 1.1 hinausgeht.

Es liegt nahe zu sagen, dem heutigen Blend fehle die Saettigung. Das stimmt
so nicht: `tanh(Punkte / 50)` **ist** eine Saettigungsfunktion. Sie saettigt
nur um den falschen Punkt, naemlich um **null Punkte**.

Herleitung (aus der obigen Codestelle und `VALUE_SCALE = 50`; die Konstante
stammt aus einer Agenten-Kartierung und ist nicht zeilenweise nachgeprueft).
Die Empfindlichkeit des Terms ist `d/dx tanh(x/50) = (1/50)·sech²(x/50)`:

| Eigener Punktestand | Empfindlichkeit je Punkt |
|---|---|
| 0 | 0,0200 |
| 55 | 0,0072 |
| 70 | 0,0043 |

Seit Schema 20 ist das Punkte-Ziel eigenseitig, `tanh(own_total/50)`. Reale
eigene Endstaende liegen also dort, wo der Term **vier- bis fuenfmal
unempfindlicher** ist als an seinem Wendepunkt. Konkret: ein eigener
Punktestand zwischen 40 und 70 bewegt `pts` auf der [0,1]-Skala nur von
0,832 auf 0,943, also um 0,111 ueber die gesamte realistische Spanne. Bei
w=0,1 traegt der Term folglich hoechstens 0,011 Variation bei, waehrend `wr`
den vollen Bereich abdeckt.

**Damit ist der gescheiterte Blend zwanglos erklaert, ohne jede
Saettigungstheorie**: der Punkte-Term war fast konstant. Er hat kaum
unterschieden und dafuer einen Versatz eingetragen, der den Gegner
ignoriert. Ein solcher Term kann nur schaden.

KataGos arctan saettigt dagegen um `x0`, den **bei jeder Suche neu gesetzten
vorhergesagten Wurzel-Score**. Der steile Bereich liegt dort immer da, wo
die Partie gerade steht. Genau diese Verschiebung ist der Mechanismus, nicht
die Kruemmung an sich.

## par.4 Bauplan

Additiver, gesaettigter, re-zentrierter Utility-Term neben `wr`, nicht in
`legacy_blended` hinein:

```
u_score(x) = c_score · (2/pi) · arctan( (x − x0) / b )
U          = wr + E[ u_score ]
```

- `x` ist die Punkte-**Marge** (eigen minus Gegner), nicht der eigene Stand.
- `x0` wird zu Beginn **jeder** Suche auf die vom Netz vorhergesagte Marge
  an der Wurzel gesetzt.
- `E[u_score]` wird ueber die Score-Verteilung integriert, nicht am
  Erwartungswert ausgewertet. Ohne Integration ist die Streuung wirkungslos
  und der Term degeneriert wieder zu einer Punktschaetzung.
- `c_score` klein halten. KataGo faehrt 0,1 bis 0,3 und daempft im Self-Play
  anders als im Live-Spiel.

## par.5 Das fehlende Stueck: eine Streuung

Wir haben den Erwartungswert. Eine Streuung existiert im Netz **nirgends**
(kein Varianzkopf, kein Ensemble, kein Dropout). Zwei Wege:

- **Weg S (KataGo-treu):** ein `sigma`-Kopf, trainiert per
  Selbst-Vorhersage-Regularisierer auf Mittelwert und Standardabweichung der
  eigenen Vorhersage (KataGo: Huber, delta=10). Danach wird gegen eine
  Normalverteilung integriert, was nur zwei Zahlen je Knoten braucht --
  KataGo fuehrt es aus genau diesem Grund so, wegen Tree-Reuse.
- **Weg V (Verteilung):** `POINTS_DIST_BINS > 0` wiederbeleben und direkt
  ueber die Bins integrieren, ohne Normalverteilungsannahme.

Weg V haengt an `PREREG_points_dist_bin_scale.md`: eine Verteilung, deren
Bins im relevanten Bereich 5 bis 20 Punkte breit sind, waere auch fuer eine
gesaettigte Utility ein schlechter Eingang. **Reihenfolge:** faellt dessen
Vorpruefung positiv aus, ist Weg V der guenstigere; sonst Weg S.

Weg S ist der Primaerarm dieser Prereg, weil er unabhaengig ist.

## par.6 Die Marge, die es heute nicht gibt

KataGos Utility laeuft ueber den **Vorsprung**. Seit Schema 20 sagt der
Punkte-Kopf aber den **eigenen** Stand vorher (`PREREG_points_head_epsilon.md`,
Epsilon auf 0). Eine Marge muss also aus zwei Koepfen gebildet werden:
`points` und `opp_points`.

Zwei Fallen dabei:

1. Beide Koepfe liefern tanh-Werte. Die Ruecktransformation
   `50·(atanh(p) − atanh(q))` explodiert nahe ±1. Es braucht eine
   Klammerung, und deren Wirkung ist zu berichten, nicht stillschweigend zu
   setzen.
2. `opp_points` ist laut `PREREG_points_head_epsilon.md` ein **Hilfsziel
   mit unbelegtem Nutzen**. Dieser Zuschnitt macht ihn erstmals tragend.
   Faellt er durch, ist offenzuhalten, ob die Utility oder der Kopf schuld
   war.

## par.7 Arme

| Arm | Inhalt |
|---|---|
| **R** | Bestandsrezept, Champion-Konfiguration, `w = 0` |
| **S0** | Weg S gebaut, `c_score = 0` -- muss **bitgleich** zu R spielen |
| **S1/S2/S3** | `c_score` in aufsteigender Leiter, Groessenordnung 0,1 / 0,2 / 0,3 |

**S0 ist ein Pflicht-Arm.** Er trennt "die Utility wirkt" von "der Umbau hat
etwas anderes veraendert". Ohne ihn ist jeder Ausgang mehrdeutig. Bitgleiches
Spiel gegen R bei identischen Seeds ist die Abnahmebedingung; Zahlengleichheit
bei gleichen Seeds ist hier ausnahmsweise das ERWARTETE Ergebnis und nicht,
wie sonst im Projekt, ein Alarmzeichen fuer ein nicht neu gebautes Wheel.

## par.8 Vorregistrierte Richtungsvorhersage

Das ist der eigentliche Falsifikator dieses Zuschnitts, und er ist schaerfer
als "Siegquote steigt".

Wenn der Mechanismus das tut, was er tun soll, dann verschiebt sich die
Marge **in** Siege:

- Siegquote steigt, **und**
- die Durchschnittsmarge bleibt gleich oder faellt.

Steigen Siegquote **und** Marge gemeinsam weiter, ist das **nicht** der
behauptete Mechanismus, sondern ein anderer Effekt, und der Zuschnitt hat
seine These nicht belegt, auch wenn die Arena guenstig ausgeht. Dieser Fall
ist ausdruecklich als solcher zu berichten und nicht als Erfolg zu buchen.

Bezugspunkt ist der #12-Befund: +2,25 Marge bei 151:149.

## par.9 Entscheidungsmetrik

**Primaer: gepaarte Arena** gegen den Champion, feste Paarzahl, **kein
SPRT-Fruehstopp**, plus vorregistrierte Replikation mit frischem Seed-Satz
vor jedem Verdikt. Begruendung ist die Aktenlage dieses Kopfes: `t12_dist`
zeigte SPRT-H1 mit 54:26 und war in der Replikation Seed-Rauschen.

**Mitzuberichten, gleichrangig:** Durchschnittsmarge je Block, wegen par.8.

**Sekundaer, deskriptiv:** R5-Kalibrierungssteigung (heute 0,06-0,09 fuer
den Value-Kopf, 0,26 fuer den Punkte-Kopf), Brier/ECE, die beiden
Orakel-Metriken.

**Seed-Disziplin:** gepaarte Seeds, mindestens sechs bei Trainingsarmen.

**Auswertung auf Block-Ebene**, nicht auf Paar-Ebene.

## par.10 Waechter

1. **Der R5-Loeser wird nicht angefasst.** `round5.rs` ist eingefrorener
   Anker und rechnet exakt/endaware; die Utility wirkt nur auf
   netzbewertete Blaetter. Ein Eingriff dort waere ein anderer Zuschnitt.
2. **`POINTS_UTILITY_WEIGHT` bleibt 0.** Der neue Term steht daneben, nicht
   darin. Die alte Konstante wird nicht rekalibriert, sonst vermengen sich
   ein widerlegter und ein ungetesteter Mechanismus.
3. **Alt-Checkpoints bleiben ladbar.** Netze ohne `sigma`-Kopf muessen
   weiterhin spielen, mit sauberem Rueckfall auf den Bestandspfad.
4. **Wheel neu bauen** vor jeder Messung. Gruene `cargo test` heisst nicht,
   dass die Arena den neuen Code sieht.
5. **Arena exklusiv**, keine Nebenlast. CPU-Nebenlast verstuemmelt Partien
   nichtdeterministisch.
6. **Self-Play und Live-Spiel duerfen verschiedene `c_score` fahren**
   (KataGo tut das). Wenn davon Gebrauch gemacht wird, ist es vorab
   festzulegen und nicht nachtraeglich.

## par.11 Was als Nicht-Erfolg gilt

- **S0 nicht bitgleich zu R:** Bau fehlerhaft, Messung ungueltig, nichts
  wird berichtet ausser dem Fehler.
- **Alle `c_score` H0:** kein Beleg. Zuschnitt ruht.
- **Monoton fallende Staerke mit steigendem `c_score`**, wie bei der linearen
  Variante: dann ist die Richtung "Score-Utility in der Blattbewertung"
  insgesamt geschlossen, nicht nur ihre naive Form. Das ist der wichtigste
  moegliche Befund dieses Zuschnitts, weil er eine ganze Familie erledigt.
- **Siege und Marge steigen gemeinsam:** These nicht belegt, siehe par.8.

## par.12 Offen, vor dem Bau zu entscheiden

- `b`, die Breite der arctan-Saettigung, in Punkten.
- Klammerung der `atanh`-Ruecktransformation aus par.6.
- Ob `x0` aus dem Netz an der Wurzel kommt oder aus der Wurzel-Suchstatistik.
- Ob der `sigma`-Kopf auf die eigene Punktzahl oder auf die Marge trainiert.
- Ob die Utility im Backup oder erst in der Wurzelauswahl wirkt.

## par.13 Verhaeltnis zu den Nachbar-Zuschnitten

- **`PREREG_points_dist_bin_scale.md`**: liefert Weg V. Dessen Offline-Tor
  entscheidet, ob Weg V ueberhaupt in Frage kommt.
- **`PREREG_points_blend_w.md` / `PREREG_task28_aggression.md` /
  `PREREG_aggression_remapping.md`**: die widerlegte lineare Familie. Diese
  Prereg eroeffnet sie nicht wieder; sie baut einen strukturell anderen Term
  und benennt in par.3, warum der alte scheitern musste.
- **`PREREG_score_correlation.md`**: unabhaengig, betrifft die Notwendigkeit
  eines Differenzkopfes.
- **`research_value_head_alternatives_DRAFT.md` Idee 1.1**: die Quelle
  dieses Zuschnitts. Der Beitrag hier ist par.3 (Re-Zentrierung statt
  Saettigung als eigentlicher Mechanismus, mit der Empfindlichkeitsrechnung)
  und par.8 (Marge-in-Siege als vorregistrierter Falsifikator).
