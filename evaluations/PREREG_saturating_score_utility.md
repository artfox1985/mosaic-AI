<!-- STATUS: OFFEN | Frage: Verwandelt eine KataGo-treue Score-Utility (Saettigung um den RE-ZENTRIERTEN Wurzel-Score, integriert ueber die Score-Verteilung) die gemessene, aber wertlose Punktemarge in Siege -- dort, wo die vorhandene lineare Mischung gescheitert ist? | Beleg: nichts gebaut, Entwurf angelegt 2026-08-23, am selben Tag nach Durchsicht ERGAENZT. Ausarbeitung liegt in research_value_head_alternatives_DRAFT.md Idee 1.1, war aber nie vorregistriert. Empirischer Anker: Task #12 Block 2, Marge +2,25 bei 151:149. Neu: Tor par.3a (entscheidet offline zwischen "Punkte-Term fast konstant" und "fast kollinear zu wr" -- die Entwurfs-Diagnose setzte voraus, dass die Kopf-Ausgabe tanh(own/50) schaetzt, was fuer ~83 % der Trainingszeilen wegen des TD-Blends nicht gilt) sowie zwei Bau-Blocker, beide am 2026-08-23 per Nutzer-Entscheid geschlossen: par.4a -> SKALENWECHSEL der ganzen Blattbewertung auf [-1,1] (Bau-Umfang in par.4b kartiert; geschriebene Korpus-Felder bleiben auf [0,1], sonst still gemischtskaliges Fenster ueber 2945 Bestandsdateien), und par.6.1 -> eigener ADDITIVER Margen-Kopf ohne rtv/TD-Zweig, mit eigener Skala MARGIN_SCALE = 20 (par.6a; damit entfaellt die Zwei-Kopf-Subtraktion und opp_points bleibt Hilfsziel). Die 20 ist eine REFERENZSETZUNG wie VALUE_SCALE = 50, nicht aus Self-Play abgeleitet -- Beleg: neun Mensch-gegen-v21-Partien in static/log, RMS-Marge ~21, Median der Betragsmarge 17. Reihenfolge: Tor par.3a, dann Bau -->

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

Der Praezedenzfall gehoert dazu, und er besteht aus **zwei verschiedenen
Knoepfen**. Der Entwurf hatte sie in einem Satz zusammengezogen; das ist am
2026-08-23 korrigiert, weil par.3 sonst das Falsche erklaert.

| Knopf | Was er mischt | Ergebnis |
|---|---|---|
| `POINTS_UTILITY_WEIGHT` (`net_mcts.rs:108`, konstant 0,0) | `pts = value_to_win_prob(points)` linear zu `wr` (:2297). Der Gegner kommt darin **nicht** vor | 2026-07-19: 0,5 -> 1:14, 1,0 -> 0:12 |
| `w = points_utility_w()` (Task #28, :2309) | `opp_aware_points_utility(pts_raw, opp_raw, lambda_aggr)` (`net_mcts.rs:450-454`): `(pts + eps·opp) − lambda·opp`. Dieser Arm traegt den Gegner **ausdruecklich** | w=0,1 gegen w=0: 300/400 zu 321/400, Block-t −2,68 |

Die naive Form ist in beiden Auspraegungen **klar widerlegt**. Diese Prereg
reaktiviert weder den einen noch den anderen Knopf, sondern baut einen
anderen Term daneben. Wichtig fuer par.3: "gegner-blind" gilt nur fuer die
obere Zeile.

## par.3 Der eigentliche Befund: es fehlt nicht die Saettigung, es fehlt die Re-Zentrierung

Dies ist der Punkt, an dem diese Prereg ueber Idee 1.1 hinausgeht.

Es liegt nahe zu sagen, dem heutigen Blend fehle die Saettigung. Das stimmt
so nicht: `tanh(Punkte / 50)` **ist** eine Saettigungsfunktion. Sie saettigt
nur um den falschen Punkt, naemlich um **null Punkte**.

Herleitung (aus der obigen Codestelle und `VALUE_SCALE = 50.0`,
`engine/py/neural_net.py:712`, am 2026-08-23 zeilenweise nachgeprueft).
Die Empfindlichkeit des Terms ist `d/dx tanh(x/50) = (1/50)·sech²(x/50)`.
**Einheiten beachten:** die Tabelle steht in tanh-Einheiten, `pts` liegt auf
der [0,1]-Skala und ist damit halb so empfindlich.

| Eigener Punktestand | Empfindlichkeit je Punkt (tanh-Skala) | dasselbe auf der [0,1]-Skala von `pts` |
|---|---|---|
| 0 | 0,0200 | 0,0100 |
| 55 | 0,0072 | 0,0036 |
| 70 | 0,0043 | 0,0022 |

Waere das Punkte-Ziel der reine eigene Endstand, laegen reale Endstaende
dort, wo der Term **vier- bis fuenfmal unempfindlicher** ist als an seinem
Wendepunkt. Konkret: ein eigener Punktestand zwischen 40 und 70 bewegte
`pts` auf der [0,1]-Skala nur von 0,832 auf 0,943, also um 0,111 ueber die
gesamte realistische Spanne. Bei w=0,1 truege der Term hoechstens 0,011
Variation bei, waehrend `wr` den vollen Bereich abdeckt.

**Zwei Einschraenkungen, beide am 2026-08-23 nachgetragen.**

**(a) Datierung.** Der Entwurf haengte das Argument an "seit Schema 20 ist
das Punkte-Ziel eigenseitig" (2026-08-10) und erklaerte damit eine Messung
vom 2026-07-19. Der own-Term dominiert aber schon seit db73122
(2026-07-06, "Differenzbildung durch getrennt gesaettigte Terme ersetzt");
Schema 20 hat nur den 0,1-Gegner-Term entfernt. Das Argument traegt also
ueber den ganzen Zeitraum -- aber aus diesem Grund, nicht aus dem im
Entwurf genannten.

**(b) Die Praemisse "die Kopf-Ausgabe schaetzt `tanh(own/50)`" ist fuer den
groessten Teil des Trainingssignals falsch.** `points_val` wird nach der
Formelzeile (`neural_net.py:1647`) ueberschrieben: `neural_net.py:1704`
setzt bei vorhandenem `rtv` komplett auf `own_rtv = 2·rtv[p] − 1`, und
`neural_net.py:1717` blendet `TD_LAMBDA·(2·bv[p] − 1) + (1 − TD_LAMBDA)·
points_val` mit `TD_LAMBDA = 0.5` (`neural_net.py:717`). Beide eingemischten
Groessen stammen aus dem **Value**-Kopf des Generators, nicht aus dem
Punkte-Kopf: `bootstrap_value` ist `net_leaf_eval` nach einem Rollout
(`round_transition_deep.rs:852` -> `net_mcts.rs:2411`
`blended_leaf_win_prob(&value, ...)`, bei `w=0` also
`calibrate_win_prob_with(value_to_win_prob(value))`). Bei WDL-Kopf ist das
`2·p_win − 1` (`neural_net.py:2503`, eine Gewinnwahrscheinlichkeit), beim
tanh-Kopf davor `tanh((own−opp)/50)` (eine Punkte-Marge). `tanh(own/50)`
dagegen ist der Punkte-Kopf. Beide eingemischten Formen sind um null
zentriert und keine von beiden ist der eigene Endstand.
Gemessen am 2026-08-23
(je eine Datei pro Generation, kein Vollscan): `round_transition_value` in
v18/v19wdl/v19wdlsw/v20wdl/v20wdlsw **nirgends** vorhanden, `bootstrap_value`
in 82,8 bis 84,0 % der Datensaetze. Nur die restlichen ~17 % (Runde 5, kein
Uebergang) tragen das reine `tanh(own/50)`.

Damit ist die Erklaerung eine **Hypothese, keine Herleitung**. Die
Kopf-Ausgabe wird vermutlich vom Bootstrap-Anteil dominiert, dessen Spanne
die des Punkte-Anteils weit uebersteigt. Der Term war dann
nicht "fast konstant", sondern **fast kollinear zu `wr`** -- was in der
WDL-Aera besonders scharf gilt, weil `wr` und der Bootstrap-Anteil dann
denselben Kopf lesen. Beide Lesarten
erklaeren denselben Nullbefund, sind aber verschiedene Mechanismen und
fuehren zu verschiedenen Auswegen. Welche zutrifft, entscheidet par.3a.

Was in beiden Lesarten fehlt, ist die Re-Zentrierung. KataGos arctan
saettigt um `x0`, den **bei jeder Suche neu gesetzten vorhergesagten
Wurzel-Score**. Der steile Bereich liegt dort immer da, wo die Partie gerade
steht. Genau diese Verschiebung ist der Mechanismus, nicht die Kruemmung an
sich.

Der "gegner-blinde Versatz" aus dem Entwurf gilt nur fuer
`POINTS_UTILITY_WEIGHT`, nicht fuer den Task-#28-Arm `w` (par.2).

## par.3a Tor: welche der beiden Lesarten stimmt? (billig, offline)

**Vor jedem Bau.** Auf dem vorhandenen Messset, mit dem Champion-Netz, ohne
Training und ohne Arena:

1. Histogramm der rohen Kopf-Ausgabe `points[0]` ueber die Stellungen des
   Messsets, aufgeschluesselt nach Runde.
2. Spannweite dieser Ausgabe, auf der [0,1]-Skala von `pts`
   (`value_to_win_prob`), gegen die im Entwurf angenommenen 0,111.
3. Korrelation von `pts` mit `wr` auf denselben Stellungen, auf Block-Ebene
   gerechnet.

Vorab festgelegte Lesart:

- **Spannweite deutlich unter 0,2 und Korrelation mit `wr` niedrig**:
  Lesart "fast konstant" bestaetigt. Re-Zentrierung ist der richtige Hebel,
  der Zuschnitt laeuft wie geplant weiter.
- **Spannweite gross und Korrelation mit `wr` hoch (|r| > 0,8)**: Lesart
  "fast kollinear" bestaetigt. Dann ist der Punkte-Kopf in seiner heutigen
  Trainingsform kein unabhaengiger Punkte-Kanal, sondern eine zweite,
  schlechtere Sieg-Schaetzung. Re-Zentrierung allein hilft dann nicht; vor
  dem Bau ist zu entscheiden, ob der `sigma`-Kopf (par.5, Weg S) auf ein
  vom TD-Blend UNBERUEHRTES Punkte-Ziel trainiert werden muss. Das ist ein
  Nutzer-Entscheid, kein Automatismus.
- **Dazwischen**: beide Anteile relevant, zu berichten und dem Nutzer
  vorzulegen.

Dieses Tor kostet einen Vorwaertslauf ueber das Messset. Es entscheidet, ob
der teuerste Value-seitige Zuschnitt des Projekts auf der richtigen Diagnose
aufsetzt, und steht deshalb vor par.4.

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

### par.4a Skalen-Riegel: `U` darf [0,1] nicht verlassen

**Bau-Blocker, kein offener Punkt.** Nachgetragen 2026-08-23.

`wr` liegt in [0,1], `E[u_score]` in [−c_score, +c_score]. Die Formel oben
liefert damit `U ∈ [−0,3; 1,3]` bei `c_score = 0,3`. Der Blattwert MUSS aber
auf der [0,1]-Skala von `crate::mcts::evaluate` liegen -- das steht so in der
Funktionsdoku ueber `value_to_win_prob` (`net_mcts.rs:2223-2226`: "muss zu
`crate::mcts::evaluate`s [0,1]-Skala passen, damit PUCTs Q-Mittelung
konsistent bleibt"). Betroffen waeren PUCTs Q-Mittelung und jede Stelle, die
Q als Wahrscheinlichkeit behandelt, unter anderem `round5.rs:674`.

Wirkt hier NICHT: Waechter 1 (par.10) haelt nur den R5-Loeser selbst frei;
die Unvertraeglichkeit entstuende an der Nahtstelle, nicht im Loeser.

Drei Formen standen zur Wahl:

| Form | Wirkung |
|---|---|
| **Klammerung** `U = clamp(wr + E[u_score], 0, 1)` | einfachste Form; die Utility verliert Wirkung genau in den Stellungen, in denen `wr` schon extrem ist. Anteil geklammerter Blaetter waere zu berichten |
| **Stauchung** `U = (1 − c_score)·wr + c_score·(0,5 + 0,5·E[u_score]/c_score)` | bleibt in [0,1] ohne Klammerung, aendert aber den Sieg-Term mit -- dann ist es kein rein additiver Term mehr |
| **Skalenwechsel** ganze Blattbewertung auf [−1,1] wie KataGo | sauberste Form, aber der groesste Eingriff: jede Q-lesende Stelle muss mit |

**NUTZER-ENTSCHEID 2026-08-23: der Skalenwechsel.** Gilt fuer alle Arme.
Begruendung des Nutzers: die sauberste Form, der Preis wird bezahlt.

### par.4b Bau-Umfang des Skalenwechsels (kartiert 2026-08-23, nichts gebaut)

Read-only-Kartierung, damit der Umfang vor dem ersten Eingriff bekannt ist.

**Erzeuger der [0,1]-Skala** (jede Stelle muss auf `2q − 1` mitwandern):

| Stelle | Was |
|---|---|
| `mcts.rs:101` | `normalize_score` -- Heuristik-Blattwert |
| `net_mcts.rs:2229` | `value_to_win_prob` -- Netz-Blattwert |
| `net_mcts.rs:453` | `opp_aware_points_utility` (Task-#28-Pfad, `w>0`) |
| `round5.rs:674` | R5-Loeser -- **eingefrorener Anker, siehe unten** |
| `round5_anchor.rs:671` | Anker-Loeser -- dito |

**Inverse und Kalibrierung:** `round_transition_deep.rs:304`
(`denormalize_score`, mit Paritaetstest
`denormalize_score_is_the_inverse_of_normalize_score`) und
`net_mcts.rs:418/431` (`calibrate_win_prob[_with]`, Platt auf der
WAHRSCHEINLICHKEITS-Skala; acht Tests pruefen dort ausdruecklich
Wahrscheinlichkeits-Semantik: Ordnungserhalt, Verhalten an 0/1, "stretches
above/below half"). Platt auf [−1,1] ist nicht dasselbe wie Platt auf [0,1];
die Kalibrierungskonstanten `cal_a`/`cal_b` sind kein blosser Umrechnungsfall.

**Der harte Teil: vier Felder gehen ins KORPUS.**

| Schreibstelle | Feld | Verbraucher |
|---|---|---|
| `self_play.rs:1772` | `root_q` | Python-Auswertung, `PREREG_uncertainty_guided_selfplay.md` par.4 |
| `self_play.rs:1777` | `root_child_q` | dito |
| `self_play.rs:1879` | `round_transition_value` | `neural_net.py:1702-1705` (`2·rtv−1`) |
| `self_play.rs:1882` | `bootstrap_value` | `neural_net.py:1713-1717` (`2·bv−1`), plus die WDL-Sonderbehandlung, die `bootstrap_value` ausdruecklich als "bereits eine [0,1]-Gewinnwahrscheinlichkeit" direkt blendet |

**Vorab festgelegt, weil hier eine stille Datenkorruption droht:** die
GESCHRIEBENEN Felder bleiben auf [0,1]. Der Skalenwechsel wirkt intern; an
der Schreibgrenze wird zurueckkonvertiert. Grund: die 2945 vorhandenen
Korpusdateien liegen auf [0,1], und ein Skalenwechsel im Schreibpfad wuerde
sie nicht kaputt machen, sondern still falsch etikettieren -- das Training
saehe ein gemischtskaliges Fenster ohne jede Fehlermeldung. Wer das doch
aendern will, zieht `VALUE_SCHEMA_VERSION` und baut den Cache neu.

**Waechter 1 gilt weiter, wird aber praeziser:** `round5.rs`/
`round5_anchor.rs` sind eingefrorene Anker. Der Skalenwechsel darf dort die
Skala mitziehen, aber **keine Entscheidung aendern**. Abnahmebedingung ist
der Paritaets-Hash: identische Zuege bei identischen Seeds vor und nach dem
Umbau. Faellt der Hash, ist der Umbau falsch, nicht der Anker.

**Abnahme insgesamt:** der Skalenwechsel ist ein bijektiver Refaktor und
muss **verhaltensgleich** sein. Paritaets-Hash + volle Suite + Wheel-Neubau
vor jeder Messung. Zahlengleichheit ist hier das ERWARTETE Ergebnis (wie bei
Arm S0, par.7).

**Reihenfolge:** der Skalenwechsel ist verhaltensneutral und damit
unabhaengig vom Tor par.3a. Er darf davor gebaut werden. Gebaut wird er aber
NICHT waehrend einer laufenden Arena (Nebenlast verstuemmelt Partien, und
ein Wheel-Neubau tauscht die Engine unter der Messung).

### par.4c Verhaeltnis zur Agenten-Kapselung (Nutzer-Hinweis 2026-08-23)

`PREREG_agent_encapsulation.md` baut `AgentSpec`: Modell plus Such- und
Blattwert-Konfiguration, pro Seite instanziiert. Das laeuft in einer anderen
Sitzung. Drei Konsequenzen fuer diesen Zuschnitt, damit sich die beiden
Arbeiten nicht in die Quere kommen.

1. **Gleicher Hotspot.** `net_mcts.rs` traegt laut jener Prereg par.2
   32 OnceLock-Statics und ist der Hauptschauplatz der Migration. Drei der
   fuenf Stellen aus par.4b liegen dort (`:2229`, `:453`, `:418/431`).
   Der Skalenwechsel wird deshalb **nicht parallel zu einer laufenden
   Migrationswelle** gebaut. Reihenfolge ist Nutzer-Entscheid, nicht meiner.
2. **Die neuen Knoepfe gehoeren in die Spec, nicht ins Global.** `c_score`,
   `b`, `m_max` und der Ein/Aus-Schalter der Utility sind
   Blattwert-Konfiguration und damit genau das, was `AgentSpec` buendeln
   soll. Wird dieser Zuschnitt NACH der Kapselung gebaut, entstehen sie
   direkt dort; davor als OnceLock nach dem `#30`-Muster, mit dem
   ausdruecklichen Vermerk, dass sie zu migrieren sind. Damit faellt auch
   Waechter 6 (par.10, verschiedene `c_score` in Self-Play und Live-Spiel)
   natuerlich in die Spec-Form.
3. **Die [−1,1]-Skala ist KEIN Knopf, sondern ein Vertrag.** Sie darf nicht
   in die `AgentSpec`. Beide Seiten einer Partie und jeder Knoten desselben
   Baumes muessen dieselbe Blattwertskala haben, sonst sind Q-Werte nicht
   mehr vergleichbar. Sie gehoert damit in dieselbe Klasse wie
   `NUM_ACTIONS`, `INPUT_SIZE` und `POLICY_MASS_CUTOFF`, die jene Prereg
   par.2 ausdruecklich global belaesst. Dasselbe gilt fuer `MARGIN_SCALE`
   aus par.6a: das ist eine Ziel-Definitionskonstante wie `VALUE_SCALE`,
   kein Verhaltensknopf.

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

Drei Fallen dabei.

1. **Die Ruecktransformation ist heute gar nicht definiert** (Bau-Blocker,
   nachgetragen 2026-08-23). `50·(atanh(p) − atanh(q))` setzt voraus, dass
   `p = tanh(own/50)` ist. Nach par.3(b) ist die Kopf-Ausgabe fuer ~83 % der
   Trainingszeilen ein Gemisch aus einem Punkte-tanh und einer
   Value-Kopf-Ausgabe. Die atanh-Inversion eines Gemischs liefert
   keinen Punktestand, sondern eine Zahl ohne Einheit. Damit waere `x` in
   par.4 nicht bestimmt, und `x0`, `b` und `c_score` haengen alle an `x`.

   **NUTZER-ENTSCHEID 2026-08-23: eigener, additiver Margen-Kopf.** Siehe
   par.6a. Damit entfaellt die Zwei-Kopf-Subtraktion vollstaendig, und mit
   ihr Falle 2 und Falle 3 unten, soweit sie den tragenden Pfad betreffen.
   Das Tor par.3a bleibt trotzdem stehen: es entscheidet nicht mehr ueber
   die Quelle von `x`, sondern darueber, ob die Diagnose in par.3
   ("Re-Zentrierung fehlt") ueberhaupt der richtige Mechanismus ist.
2. **Numerik.** Auch bei gueltiger Inversion explodiert `atanh` nahe ±1. Es
   braucht eine Klammerung, und deren Wirkung ist zu berichten, nicht
   stillschweigend zu setzen. Welche Notation gemeint ist, muss dabei
   dastehen: `p` ist die ROHE Kopf-Ausgabe in [−1,1], nicht das
   `value_to_win_prob`-Ergebnis in [0,1]. Der Entwurf liess das offen, und
   die beiden Lesarten ergeben verschiedene Formeln.
3. `opp_points` ist laut `PREREG_points_head_epsilon.md` ein **Hilfsziel
   mit unbelegtem Nutzen**. Der Entwurf haette ihn erstmals tragend
   gemacht. Mit dem Entscheid in par.6a ist das vom Tisch: `opp_points`
   bleibt Hilfsziel, der Margen-Kopf traegt. Das ist ein Nebengewinn des
   Entscheids -- ein Nullbefund waere sonst zwischen Utility und einem
   unbelegten Hilfskopf nicht auftrennbar gewesen.

## par.6a Der Margen-Kopf (Nutzer-Entscheid 2026-08-23)

Ein **additiver** Kopf `score_margin`, nach dem im Projekt etablierten
Muster fuer optionale Ausgaben (`opp_points`, `points_dist`,
`value_wdl_logits`). Alte Checkpoints ohne ihn bleiben ladbar und spielen
auf dem Bestandspfad weiter (Waechter 3, par.10).

Ziel: `tanh((own_total − opp_total) / MARGIN_SCALE)`, aus
`scores_unclamped` (im Korpus zu 100 % vorhanden, gemessen 2026-08-23).
**Ohne rtv-Zweig und ohne TD-Blend** -- das ist der ganze Zweck dieses
Kopfes. Damit ist die Ruecktransformation definiert:
`x = MARGIN_SCALE · atanh(clamp(m, −m_max, +m_max))`.

Kein neues Self-Play noetig: das Ziel ist aus dem Bestandskorpus rechenbar,
es kostet einen Cache-Neubau und einen Trainingslauf.

### Die Skala ist NICHT VALUE_SCALE

`VALUE_SCALE = 50.0` ist ausdruecklich am **absoluten Eigenstand**
kalibriert ("ab ~100 Punkten gilt ein Ergebnis als sehr gut",
`neural_net.py:502-509`). Fuer eine Marge ist das viel zu gross: bei einer
Marge von 10 Punkten stuende `tanh(10/50) = 0,197`, der Kopf laege in einem
schmalen, nahezu linearen Streifen um null und verschenkte den groessten
Teil des tanh-Bereichs. Das ist der Spiegelfall des Kompressionsproblems aus
`PREREG_points_dist_bin_scale.md`: dort zu grob an den Raendern, hier zu
fein in der Mitte.

**Harte Anforderung: eine EIGENE Konstante `MARGIN_SCALE`, nicht
`VALUE_SCALE`.** `VALUE_SCALE` haengt an `mcts::normalize_score`
(`mcts.rs:90/101`), an `round5.rs:674`/`round5_anchor.rs:671` und an
`denormalize_score`. Sie zu drehen wuerde den Elo-Anker mitverschieben. Das
ist kein Abwaegungspunkt.

### Woher die Zahl kommt: Referenz, NICHT Self-Play-Streuung

**`MARGIN_SCALE = 20`, festgelegt und eingefroren (Nutzer-Entscheid
2026-08-23).**

Ein erster Entwurf dieses Abschnitts hatte `MARGIN_SCALE = std(D)` ueber den
Self-Play-Korpus vorgeschlagen. **Das war der falsche Typ von Regel**, und
zwar aus einem Grund, den das Projekt an genau dieser Stelle schon einmal
entschieden hat. `neural_net.py:502-509` zu `VALUE_SCALE`, woertlich:

> NICHT aus aktuellen Spieldaten abgeleitet (Heuristik und Netz spielen
> beide noch schwach -- jede aus dieser Verteilung abgeleitete Skala wuerde
> nur die aktuelle Schwaeche festschreiben, nicht das echte Punktepotenzial
> des Spiels). Stattdessen an einem groben menschlichen Referenzwert
> kalibriert.

Dieselbe Falle steht als eigene Projektregel: eine Skala nie gegen die
Verteilung heutiger Netze eichen, wenn genau deren Verhalten das Ziel ist.
Self-Play-Margen stammen aus zwei plattenblinden Netzen; eine daraus
abgeleitete Skala schriebe die heutige Schwaeche fest.

**Referenzabgleich (gemessen 2026-08-23, `static/log`):** neun
abgeschlossene Mensch-gegen-Netz-Partien, alle gegen `v21_2d_brierbest` bei
400 Sims.

| Kennzahl | Wert |
|---|---|
| Margen | +38, +29, +24, +23, +17, +11, +6, +2, 0 |
| Mittel | +16,7 |
| Median \|Marge\| | 17,0 |
| Standardabweichung | 12,9 |
| RMS-Marge | ~21 |

Bei `MARGIN_SCALE = 20` spannt diese Verteilung `tanh` von 0,10 (Marge 2)
bis 0,96 (Marge 38); die RMS-Marge liegt bei `tanh(21/20) = 0,78`, also
genau im steilen Bereich. Bei 50 laege alles zwischen 0,04 und 0,64 -- die
obere Haelfte des Wertebereichs bliebe ungenutzt.

**Caveat, ausdruecklich:** dieser Referenzsatz ist EINSEITIG. Der Mensch
gewinnt acht der neun Partien, eine endet gleich; die Streuung 12,9 ist also
Streuung um +16,7 und nicht um null. Die tragende Kennzahl ist deshalb die
RMS-Marge, nicht die Standardabweichung. n=9 ist klein. Die Zahl 20 ist
damit **eine Referenzsetzung mit Groessenordnungs-Beleg**, keine geschaetzte
Verteilungskonstante -- genau wie die 50 bei `VALUE_SCALE`, und sie ist als
solche zu behandeln.

**Wiedervorlage, nicht Nachjustierung:** wenn ein plattenbewusster Champion
existiert, aendert sich die Margenverteilung. Dann ist `MARGIN_SCALE` neu zu
PRUEFEN -- aber wieder gegen eine Referenz guten Spiels, nicht gegen die
dann aktuelle Netzverteilung. Eine Nachjustierung waehrend eines laufenden
Zuschnitts ist ein neuer Arm, kein Detail.

**`Var(D)` aus `PREREG_score_correlation.md` par.3.2 bleibt eine
GEGENPROBE**, nicht die Quelle. Weicht die Self-Play-Streuung stark von der
Referenz ab, ist das ein eigener Befund ueber den Abstand zwischen
Netzspiel und gutem Spiel -- und kein Anlass, die Skala zu drehen.

**Gemessen 2026-08-24** (`score_correlation_probe.json`, netzgenerierte
Stichprobe, 2.480 Partien): `Var(D) = 399,32`, also `std(D) ≈ 19,98` --
bemerkenswert nah an `MARGIN_SCALE = 20`. Trotzdem **keine Handlungsfolge**,
aus zwei Gruenden, beide bereits oben festgelegt: erstens sind die beiden
Groessen verschiedene Objekte (dort RMS-Marge einer einseitigen
Mensch-Stichprobe, hier Standardabweichung der signierten, um null
zentrierten Self-Play-Marge zwischen zwei gleich starken Netzen); zweitens
ist die Netzstreuung explizit NICHT die Quelle, sondern nur die Gegenprobe
(par.6a oben, "Referenz, NICHT Self-Play-Streuung"). Die Naehe ist eine
Beobachtung, kein Beleg.

### Was noch offen bleibt

- `m_max`, die Klammerung vor dem `atanh` (Falle 2 oben). Aus der
  empirischen Margenverteilung abzuleiten, nicht zu raten; der Anteil
  geklammerter Blaetter ist zu berichten.
- Ob der Kopf auf die Marge am Partieende trainiert oder, wie `val`, einen
  Bootstrap-Anteil bekommen darf. **Vorab festgelegt: nein.** Ein
  TD-Anteil waere genau der Defekt, dessentwegen dieser Kopf existiert.

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

Reihenfolge: erst das Tor par.3a, dann die beiden Riegel, dann der Rest.
Die ersten beiden sind **keine offenen Punkte, sondern Bau-Blocker** und
stehen hier nur als Merkposten.

- **[Riegel par.4a]** Wie `U` in [0,1] gehalten wird: Klammerung, Stauchung
  oder Skalenwechsel. Aendert, was gemessen wird.
- ~~**[Riegel par.6.1]** Woher `x` kommt~~ -- **entschieden 2026-08-23:**
  eigener additiver Margen-Kopf, siehe par.6a.
- ~~`MARGIN_SCALE`~~ -- **entschieden 2026-08-23: 20**, als Referenzsetzung
  wie `VALUE_SCALE = 50`, mit Groessenordnungs-Beleg aus neun
  Mensch-gegen-v21-Partien. Siehe par.6a.
- `m_max`, die Klammerung vor dem `atanh`.
- `b`, die Breite der arctan-Saettigung, in Punkten. **Nicht dasselbe wie
  `MARGIN_SCALE`**: `MARGIN_SCALE` bestimmt, wie gut der Kopf die Marge
  aufloesen kann, `b` bestimmt die Form der Utility. Zwei Knoepfe, zwei
  Begruendungen.
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
- **`PREREG_score_correlation.md`**: unabhaengig, wie urspruenglich. Ihr
  `Var(D)` (par.3.2) ist fuer den Margen-Kopf eine **Gegenprobe** zur
  Referenzsetzung `MARGIN_SCALE = 20`, nicht deren Quelle -- ein
  Zwischenstand vom 2026-08-23 hatte sie kurzzeitig zur Bau-Voraussetzung
  gemacht, das ist mit dem Skalen-Entscheid hinfaellig. Reihenfolge also
  wieder: Tor par.3a, dann Bau; `score_correlation` laeuft parallel.
- **`research_value_head_alternatives_DRAFT.md` Idee 1.1**: die Quelle
  dieses Zuschnitts. Der Beitrag hier ist par.3 (Re-Zentrierung statt
  Saettigung als eigentlicher Mechanismus, mit der Empfindlichkeitsrechnung),
  par.3a (das Tor, das zwischen "fast konstant" und "fast kollinear"
  entscheidet) und par.8 (Marge-in-Siege als vorregistrierter Falsifikator).
  Die dortige Z. 7 ("tanh-gestauchte Punktedifferenz") ist am 2026-08-23
  als falsch korrigiert; #12 lief eigenseitig.
