<!-- STATUS: ENTSCHIEDEN | Frage: Verwandelt eine KataGo-treue Score-Utility (Saettigung um den RE-ZENTRIERTEN Wurzel-Score) die gemessene, aber wertlose Punktemarge in Siege -- dort, wo die lineare Mischung gescheitert ist? | Beleg: NEIN (par.15-17, 2026-09-03/04, gebaut, Anker und Paritaet GRUEN): c = 0,2 am b01 einmal 104:56, Replikation 83:77, gepoolt 187:133 (p = 0,03); Margin +2 bis +5, aber Spalten darunter (argmax 0,36 gegen 0,52) und gegen den Champion v21 77:83 statt 88:72 auf denselben Seeds. Kein Rezept, keine Champion-Kante, Skalenwechsel par.4b entfaellt. -->

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

### par.3a ERGEBNIS (2026-08-24): DAZWISCHEN -- weder rein konstant noch rein kollinear

Gefahren mit `tools/probes/saturating_score_utility_gate.py`, Artefakt
`saturating_score_utility_gate.json`. Messset `frozen_eval_set.pkl`
(1.800 Stellungen, dasselbe Set wie `tools/oracle_metrics.py`), Champion
`v21_2d_brierbest`, Forward-Pass-Batch, `wr` mit der Default-Kalibrierung
(`cal_a=0, cal_b=1`, per Selbsttest vorab als Identitaet bestaetigt).

| Groesse | Wert |
|---|---|
| Spannweite von `pts` gesamt | **0,7685** (gegen die Entwurfsannahme 0,111 -- Differenz +0,6575) |
| Pearson r(pts, wr) | **0,7421**, Block-Bootstrap-95-KI [0,708; 0,775] (500 Resamples ueber 40 Korpusdateien) |

**Verdikt nach der vorab festgelegten Lesart: DAZWISCHEN.** Die
Spannweiten-Bedingung fuer "fast konstant" (< 0,2) ist klar verfehlt --
`pts` variiert ueber weite Teile des [0,1]-Bereichs, nicht in einem
schmalen Streifen. Die Korrelations-Bedingung fuer "fast kollinear"
(|r| > 0,8) ist knapp NICHT erreicht: 0,7421 liegt unter der Schwelle, und
das 95-%-Konfidenzintervall [0,708; 0,775] kommt der 0,8-Marke nicht nahe
-- das ist keine Randentscheidung, die vom Stichprobenrauschen kippen
koennte.

**Einordnung, ohne die Lesart zu ueberschreiben:** ein r von 0,74 ist eine
starke, aber keine austauschende Korrelation. Das passt zur bereits
registrierten Struktur des Ziels (`PREREG_points_dist_bin_scale.md` par.2a,
`STATUS.md` "Das Punkte-Ziel ist NICHT tanh(own/50)"): in ~83 % der
Trainingszeilen ist `points_val` ein TD-Blend mit derselben Value-Kopf-
Ausgabe, die auch `wr` speist -- ein STRUKTURELLER Grund fuer *einen* Teil
der Korrelation, aber eben nur einen Teil, kein Determinismus.

Je Runde (gleiches Muster: Spannweite waechst von Runde 1 nach 4, faellt in
Runde 5 wieder leicht):

| Runde | Spannweite | Mittel |
|---|---|---|
| 1 | 0,333 | 0,577 |
| 2 | 0,543 | 0,558 |
| 3 | 0,627 | 0,556 |
| 4 | **0,769** | 0,548 |
| 5 | 0,577 | 0,578 |

**Folge fuer par.4: NUTZER-ENTSCHEID, kein Automatismus.** Das Tor sieht
fuer diesen Fall explizit "beide Anteile relevant, zu berichten und dem
Nutzer vorzulegen" vor -- weder "Zuschnitt laeuft wie geplant weiter" noch
"sigma-Kopf braucht ein TD-unberuehrtes Ziel" ist durch die Messung allein
entschieden. Der Skalenwechsel (par.4a/par.4b) und der Margen-Kopf
(par.6a) bleiben davon unberuehrt bau-bereit (eigene Vorbedingungen, siehe
dort); offen ist nur, ob der `sigma`-Kopf (par.5, Weg S) auf `points_val`
selbst oder auf ein vom TD-Blend UNBERUEHRTES Ziel trainiert werden soll.

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
| `round5.rs:674` | R5-NETZ-Loeser -- entwickelbar (BERICHTIGT 2026-08-27, gleicher Fehler wie in par.10: der eingefrorene Anker ist `round5_anchor.rs`) |
| `round5_anchor.rs:671` | Anker-Loeser -- **eingefroren** |

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

## par.6a Der Margen-Kopf (Nutzer-Entscheid 2026-08-23) -- UEBERHOLT durch par.6b (2026-09-03)

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

**Sekundaer, deskriptiv:** R5-Kalibrierungssteigung, Brier/ECE, die beiden
Orakel-Metriken.

**Die R5-Steigung ist GETRENNT auszuweisen (praezisiert 2026-08-27,
`PREREG_r5_solver_split.md` par.3e verlangt die Trennung ausdruecklich):**

| Skala | Steigung des Value-Kopfs heute |
|---|---|
| Gesamtwert (Solver-Wurzelmarge) | **0,87-0,89** -- fast richtig geeicht |
| Platten-/Spaltenanteil | **0,06-0,09** -- der Kopf sieht ihn praktisch nicht |

Die frueher hier stehende Kurzform "0,06-0,09 fuer den Value-Kopf" liest sich
als allgemeine Fehleichung und ist in dieser Form falsch: der Kopf ordnet die
R5-Marge sehr gut (Tau 0,762 k1-aktiv). Der Zusatz "0,26 fuer den Punkte-Kopf"
war eine FEHLZUORDNUNG (an der Primaerstelle geprueft
2026-08-27, par.3e-Tabelle der r5-Prereg): die 0,263 ist die Steigung des
Kopfs `endgame_margin`; `points - opp_points` steht bei 1,131.

**Seed-Disziplin:** gepaarte Seeds, mindestens sechs bei Trainingsarmen.

**Auswertung auf Block-Ebene**, nicht auf Paar-Ebene.

## par.10 Waechter

1. **Der R5-ANKER wird nicht angefasst** (Datei BERICHTIGT 2026-08-27). Der
   eingefrorene Anker ist `round5_anchor.rs`, nicht `round5.rs`;
   `round5.rs` ist der NETZ-Loeser und darf sich entwickeln
   (`PREREG_r5_solver_split.md` par.2/par.2c, STATUS-Abschnitt
   "Architektur"). Der Waechter bleibt bestehen, schuetzt aber die richtige
   Datei: `round5_anchor.rs` bleibt unberuehrt, weil an ihm der Elo-Anker
   haengt. Ein Eingriff in `round5.rs` waere KEIN Ankereingriff -- er ist
   trotzdem gating-pflichtig, weil er die Zugwahl in Runde 5 aendert. Die
   Utility selbst wirkt ohnehin nur auf netzbewertete Blaetter.
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
- ~~**[Riegel par.6a]** Woher `x` kommt~~ (Verweis BERICHTIGT 2026-08-27:
  stand als "par.6.1" da, einen solchen Abschnitt gibt es nicht; gemeint ist
  par.6a, der Margen-Kopf) -- **entschieden 2026-08-23:**
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

## par.6b BERICHTIGUNG: KEIN neuer Kopf -- die Marge liegt schon in zwei vorhandenen Koepfen (Nutzer 2026-09-03)

Nutzer: *"Noch ein Kopf? Wir haben own points und opp points. Somit hast die
Marge doch schon."* Richtig, und die Begruendung von par.6a fuer einen
eigenen Kopf traegt im heutigen Rezept nicht mehr:

1. **"Ohne rtv-Zweig und ohne TD-Blend"** war das Argument fuer einen
   eigenen Kopf. Die b-Serie faehrt `value_target_variant nortv` und
   `value_target_lambda 1.0` (b01-Manifest `cli_args`; Trainingslog: "kein
   Mix, Bestandsverhalten"). Punkte- und Gegnerpunkte-Ziel sind damit der
   reine Endstand, genau das, was par.6a fuer den Margen-Kopf verlangte.
2. **Aufloesung:** der Punkte-Kopf trifft die Plattenpunkte mit Steigung
   0,97 bis 0,99 (`PREREG_r5_value_calibration.md` par.11), also die
   Groesse, an der der Value-Kopf mit 0,09 scheitert. Die Marge
   `50 * atanh(p_own) - 50 * atanh(p_opp)` (Ruecktransformation wie
   `tools/r5_value_calibration.py` `points_to_pts`) hat damit die Skala des
   Spiels; die MARGIN_SCALE-Ueberlegung aus par.6a betraf nur die
   tanh-Kompression eines EIGENEN Kopfes und entfaellt.
3. **Der Verbraucher existiert:** `blended_leaf_win_prob_with` liest beide
   Koepfe heute schon (net_mcts.rs:1381, Parameter `points`, `opp_points`).
   Die lineare Mischung dort ist gemessen wertlos (w = 0,1: 300:321 bei
   p = 0,053, Spalten unbewegt, Phase 3). Was diese Prereg vorschlaegt, ist
   die FORM der Verwendung -- Saettigung um den re-zentrierten Wurzelwert
   statt linearer Beimischung -- an derselben Stelle, mit denselben Koepfen.

**Was damit aus dem Zuschnitt faellt:** der Kopf-Bau, der Cache-Neubau und
der Trainingslauf aus par.6a. **Was bleibt:** ein Engine-Bau in
`blended_leaf_win_prob_with` (Knopf, Default aus, Paritaets-Gate, Wheel,
Anker-Invarianz), der Skalenwechsel par.4a, und die offene Frage par.12 zum
sigma-Ziel. Ein Arm braucht damit keine Trainingszeit, nur Arena.

**Einordnung (Nutzer-These 2026-09-02):** der Value-Kopf sieht die Platten,
sein Massstab ist falsch; der Punkte-Kopf hat den richtigen Massstab. Diese
Prereg ist der Weg, den richtigen Massstab in die Suche zu bringen, ohne den
Value-Kopf umzuerziehen. Registrierung des Baus als eigener Absatz VOR dem
ersten Handgriff.

## par.14 BAU-ABSATZ K1 fuer v24: saettigende, re-zentrierte Margen-Utility im Blattwert (registriert 2026-09-03, VOR dem Bau)

Kontext: `PREREG_v24_window.md` par.8, Such-Knopf K1; Nutzer-Auftrag
"schreib den Bau-Absatz gleich mit". Dieser Absatz ersetzt fuer den Bau die
Teile von par.4 bis par.6a, die durch par.6b (kein neuer Kopf) und die
heutige Codelage ueberholt sind. Er registriert Formel, Herkunft jeder
Groesse, Knoepfe, Paritaets-Gate, Messung und Verdikt. Zwei Punkte bleiben
ausdruecklich Nutzer-Entscheid (unten, "Offen vor dem ersten Handgriff").

### 14.1 Formel und Herkunft jeder Groesse

```
x    = 50 * atanh(clamp(p_own, -m_max, m_max)) - 50 * atanh(clamp(p_opp, -m_max, m_max))   # Marge in Punkten
x0   = dieselbe Rechnung am WURZEL-Knoten, einmal je Suche
u    = c * (2/pi) * atan((x - x0) / b)                                                     # in [-c, +c]
U    = wr + u                                                                               # Blattwert
```

| Groesse | Herkunft | Beleg |
| --- | --- | --- |
| `p_own`, `p_opp` | Punkte- und Gegnerpunkte-Kopf des Blatts, tanh-Skala (`points`, `opp_points` in `blended_leaf_win_prob_with`, net_mcts.rs:1398) | par.6b; Ruecktransformation wie `tools/r5_value_calibration.py` `points_to_pts` |
| `wr` | Siegwahrscheinlichkeit wie heute: `calibrate_win_prob_with(value_to_win_prob(value), cal_a, cal_b)` (net_mcts.rs:1409) | unveraendert |
| `x0` | Marge aus denselben Koepfen am Wurzelknoten der laufenden Suche (`Node::points_forecast` / `opp_points_forecast` der Wurzel, net_mcts.rs:1217-1223), einmal je Suche gesetzt | par.3 (Re-Zentrierung) |
| `b` | Breite der Saettigung in Punkten, Referenzsetzung **b = 20** (RMS-Marge der Mensch-Referenz, par.6a-Tabelle: ~21; Self-Play-Gegenprobe std 19,98 ist NICHT die Quelle) | par.6a, par.12 |
| `c` | Gewicht, Arme 0,1 / 0,2 / 0,3 (KataGo-Bereich, par.4) | par.4 |
| `m_max` | Klammerung vor `atanh`: 0,995 (entspricht |Marge| 150 Punkte, jenseits jedes Endstands); Anteil geklammerter Blaetter wird gezaehlt und berichtet | par.12 |

`u` ist antisymmetrisch um `x0`: ein Blatt, das genau die Wurzelerwartung
haelt, bekommt `u = 0`, der Blattwert ist dann exakt der heutige. Nur
ABWEICHUNGEN von der Wurzelmarge zaehlen, gesaettigt: +7 Punkte (eine
Spalte) ergeben bei b = 20 und c = 0,2 einen Zuschlag von 0,043 auf `wr`;
+30 Punkte 0,127, nie mehr als 0,2.

**Kein Verteilungskopf (Nutzer-Frage 2026-09-03):** die Integration ueber
eine Score-Verteilung (par.5, Weg S/V) glaettet `u` nahe `x0` und macht `b`
stellungsabhaengig. Den Haupteffekt, die Re-Zentrierung, braucht sie nicht;
mit festem `b` glaettet der arctan bereits. Ein sigma-Kopf ist damit ein
FOLGEARM fuer den Fall, dass K1 traegt und die Wirkung stark an `b` haengt
(Sensitivitaet: die drei `c`-Arme bei b = 20, dazu EIN Arm c = 0,2 bei
b = 10 als Breitenprobe). Vorher wird er nicht gebaut.

### 14.2 Skala: was par.4a entschieden hat, und die Frage davor

par.4a hat am 2026-08-23 den **Skalenwechsel** der ganzen Blattbewertung auf
[-1, 1] entschieden ("die sauberste Form, der Preis wird bezahlt"). par.4b
hat den Preis kartiert: fuenf Erzeuger der [0,1]-Skala, die
Platt-Kalibrierung, und VIER Korpusfelder (`root_q`, `root_child_q`,
`round_transition_value`, `bootstrap_value`), an denen Trainingsziele
haengen. Das ist ein Umbau ueber Engine, Korpusformat und Trainer, kein
Knopf -- und fuer die MESSFRAGE "traegt die re-zentrierte Marge?" nicht
noetig: `U = wr + u` verlaesst [0,1] nur, wenn `wr > 1 - c` bzw. `wr < c`,
also in schon entschiedenen Stellungen.

**Vorschlag fuer K1 (Nutzer-Entscheid, siehe unten):** Messvariante
**K1-A, Klammerung** `U = clamp(wr + u, 0, 1)` mit gezaehltem und
berichtetem Klammer-Anteil. Traegt K1-A, wird der Skalenwechsel nach par.4b
als eigener Bau nachgezogen, BEVOR der Knopf ins Rezept geht; traegt K1-A
nicht, ist der Skalenwechsel gespart. Damit wird par.4a nicht aufgehoben,
sondern hinter die Messung gestellt.

### 14.3 Bau, Knoepfe, Paritaets-Gate

- Ort: `blended_leaf_win_prob_with` (net_mcts.rs:1398) bekommt den Term
  ADDITIV hinter dem heutigen Rueckgabewert; `POINTS_UTILITY_WEIGHT` und der
  Task-#28-Pfad `w` bleiben unberuehrt (Waechter 2, par.10). `x0` wird beim
  Wurzelaufbau in `net_search_with_tree` aus dem Wurzel-Forecast gesetzt und
  ueber den Suchkontext an das Blatt gereicht (nicht ueber einen
  prozessweiten Cache, Regel "prozessweite Knoepfe: kein Spiegelmatch").
- Knoepfe: `MOSAIC_SCORE_UTILITY_C` (Default **0.0 = aus**, byte-identisch),
  `MOSAIC_SCORE_UTILITY_B` (Default 20), beide in `SearchConfig::from_env`
  und in die Knopf-Registratur (`knob_registry.rs`, `docs/knobs.md`), beide
  im Lauf-Manifest (`engine_config`) sichtbar. Fehlt ein Kopf
  (`points`/`opp_points` leer): `u = 0`, einmalige Warnung wie
  `warn_missing_opp_head_once`.
- Paritaets-Gate: mit `C = 0` muss die Golden-Selbstpruefung bitgleich
  bleiben (bestehende Tests `blended_leaf_win_prob_with_*`, Anker-Invarianz
  nach dem Wheel-Neubau, `/mosaic-anchor-invariance`); ein neuer Test prueft
  `u(x0) = 0` und die Antisymmetrie.
- Waechter 1 (par.10) unveraendert: `round5_anchor.rs` bleibt unberuehrt;
  der Term wirkt nur auf netzbewertete Blaetter.

### 14.4 Messung und Verdikt (vorab)

Instrument: `tools/paired_arena_env_ab.py --env-name MOSAIC_SCORE_UTILITY_C
--arms 0 0.1 0.2 0.3 --control 0`, Netz gegen dasselbe Netz ohne Knopf
(`--model-b`), zuerst am `v23-b01_brierbest` (verfuegbar, Bau kann vor v24
gemessen werden), dann am besten v24-Netz; @400 gegen @400, **Blockgroesse
5**, `--log-games`, **n >= 150 Paare je Arm oder Replikation mit eigenem
Seed** (Champion-Strenge, `generation_loop.md`). Dazu je Arm das
argmax-Spaltenprofil (200 Partien, Seed 20260931) und die sechs
Standard-Kennzahlen aus den Logs (`arena_column_probe`).

| Befund | Verdikt |
| --- | --- |
| ein `c`-Arm signifikant vorn bei den Siegen UND nicht unter der Kontrolle bei den Spalten | K1 traegt; Skalenwechsel par.4b nachziehen, dann Rezept-Kandidat; Breitenprobe b = 10 entscheidet, ob ein sigma-Folgearm lohnt |
| Spalten steigen, Siege fallen | Tausch wie bei der Suchtiefe; registrieren, kein Rezept |
| alle Arme H0 auf 150 Paaren | kein Beleg, Zuschnitt ruht (par.11) |
| Staerke faellt monoton mit `c` | die Familie "Score-Utility im Blattwert" ist geschlossen, nicht nur die naive Form (par.11, wichtigster moeglicher Befund) |

Kosten: Bau rund 2 h (Engine, Tests, Wheel, Anker), Arena 3 Arme x 2 x 80
Partien rund 1,5 h CPU plus Replikation, Spaltenprofil 3 x 23 min.

### 14.5 Offen vor dem ersten Handgriff (Nutzer-Entscheid)

1. ~~**K1-A (Klammerung) als Messvariante vor dem Skalenwechsel**, oder direkt
   der Skalenwechsel nach par.4a/4b~~ **ENTSCHIEDEN (Nutzer 2026-09-03):
   Klammerung als Messvariante.** `U = clamp(wr + u, 0, 1)`, Klammer-Anteil
   wird gezaehlt und berichtet. Der Skalenwechsel aus par.4a bleibt der
   registrierte Weg fuer den Fall, dass K1 traegt, und wird dann VOR der
   Rezeptaufnahme als eigener Bau nachgezogen (par.4b). Damit sind alle
   Punkte dieses Absatzes entschieden; K1 ist baureif.
2. ~~**Referenz b = 20** bestaetigen oder eine andere Referenz nennen~~
   **ENTSCHIEDEN (Nutzer 2026-09-03): b = 20.** Begruendung des Nutzers:
   *"20 punkte marge kommt schon gut hin bei einem gleichwertigen basisspiel
   und ein spieler schaut mehr auf die wertungsplatten"* -- also die Marge,
   die der Plattenblick allein zwischen sonst gleich starken Spielern
   erzeugt; genau die Groesse, die der Term sichtbar machen soll. Damit ist
   `b` eine Referenzsetzung aus dem Spielverstaendnis, wie `VALUE_SCALE` und
   `MARGIN_SCALE`, nicht aus einer Netzverteilung. Offen bleibt allein Punkt 1.

## par.15 ERSTMESSUNG K1 am `v23-b01_brierbest` (2026-09-03): c = 0,2 gewinnt Partien und Punkte, baut aber weniger Spalten -- Replikation offen

**Bau (Commit 8ffb2e4, Wheel Kontrakt-Hash `efd564d87bac2722` unveraendert):**
wie par.14, mit EINER registrierten Abweichung: der Term sitzt nicht in der
reinen Funktion `blended_leaf_win_prob_with`, sondern an deren Aufrufstelle in
`node_from_net_outputs` (`apply_score_utility`), weil `x0` absolut (Spieler 0
minus Spieler 1) gefuehrt wird und die Perspektivdrehung den Zustand braucht;
Bauform ist das Nullsummen-Additiv der Floor-/Langreihen-Terme, danach
Klammerung auf [0, 1] (K1-A). `x0` wird je Suche in
`build_gumbel_tree`/`build_net_tree` gesetzt (`with_root_margin`), bei `c = 0`
ist die Config eine unveraenderte Kopie. Paritaets-Gate: 506 Tests gruen
(`u(x0) = 0`, Antisymmetrie, Saettigung, Ruecktransformation, Nullsummen-
Anwendung mit Klammerzaehlung; das Zahlenbeispiel "+30 Punkte = 0,127" in
par.14.1 ist gerundet, exakt 0,1251), Anker-Drift GRUEN
(`anchor_drift_20260903_k1.json`, 1.763 Schritte), **Netz-Pfad bei `c = 0`
Record fuer Record identisch** mit dem b06-Instrument (Chunk 0 neu erzeugt,
1.733 Schritte, `k1_net_path_parity_repro.json`) -- der Heuristik-Anker allein
durchlaeuft den Netz-Blattpfad nicht. Spec-Pflichtfelder `score_utility_c`/
`score_utility_b` (vier lebende Specs nachgezogen, Artefakt-Specs unberuehrt).
Hinweis: die Messung lief auf dem Wheel des K3-Baus (e69aec3, Paritaet dort
ebenfalls GRUEN, `k3_net_path_parity_repro.json`), weil die erste Arena an
einer waehrend des Laufs geaenderten Spec-Datei abbrach (Chronik
`night_run_20260902.md`, 10:18).

**Aufbau:** `tools/paired_arena_env_ab.py`, Netz gegen dasselbe Netz @400/@400,
Env-Arm auf einem Brett, `models/k1_off.spec.json` (alle Knoepfe 0) auf dem
anderen, Brett-Tausch per zweitem Lauf (`--spec-a` statt `--spec-b`), Seed
20261001, 4 Arme x 2 Richtungen x 80 Partien, Blockgroesse 5, `--log-games`,
`MOSAIC_STACK_DRAW_RESEARCH=1` in allen Armen (Konvention der b05/b06-Arenen;
Kontrolle an den b06-Instrumentdaten: 111 von 3.468 Records mit
Stapelzug-Option). Gepoolt per `tools/probes/env_ab_swap_eval.py`
(Knopf-Seite gegen Kontrolle desselben Spielindex, McNemar exakt, Bloecke je
Richtung). Artefakte `paired_arena_env_k1_b01_{first,second}_s01.json`,
`k1_b01_swap_eval_s01.json`, `columns_k1_b01_{first,second}_s01.json`,
`tor2a_k1c02_v23b01.json`. Laufzeit UNTER NEBENLAST (b07-Training auf der
GPU): 4.207 + 4.334 s fuer 640 Partien (13,3 s je Partie, threads 10);
argmax-Instrument 1.702,8 s (8,51 s je Partie, threads 11) -- keine
Planungsgroessen.

| Arm | Knopf-Seite : Basislinie (160 Paare) | diskordant Knopf/Kontrolle, McNemar p | Block-Diff Siege (SE, t) | Punkte Knopf | Margin (Block-SE) | Klammer Einheit |
| --- | --- | --- | --- | --- | --- | --- |
| Kontrolle (0) | 80 : 80 (Spiegelmatch, per Konstruktion) | -- | -- | 48,58 | 0 | -- |
| c = 0,1 | 83 : 77 | 40 / 37, p = 0,82 | +0,019 (0,057; 0,33) | 48,36 | +3,12 (2,12) | 4,4 % |
| **c = 0,2** | **104 : 56** | **48 / 24, p = 0,0063** | **+0,150 (0,058; 2,61)** | 47,53 | **+4,94 (1,73)** | 5,6 % |
| c = 0,3 | 90 : 70 | 48 / 38, p = 0,33 | +0,062 (0,065; 0,96) | 49,46 | +3,19 (2,04) | 10,3 % |

Margen-Klammerung (`m_max`): 0 Blaetter in allen Armen. Die Einheits-
Klammerung (`wr + u` ausserhalb [0, 1]) trifft 4 bis 10 Prozent der
netzbewerteten Blaetter und waechst mit `c` -- der Preis der Messvariante
K1-A, den par.4b (Skalenwechsel) abschaffen wuerde.

**Spalten (Arena-Logs, 315 von 320 Partien replaybar, gepaart je Spielindex
und Brett, 32 Bloecke):** volle Spalten der Knopf-Seite minus Kontrolle
c = 0,1 +0,025 (SE 0,092), **c = 0,2 -0,130 (SE 0,070, t -1,85)**, c = 0,3
-0,094 (SE 0,076); Huellen-Deckung H (par.8.1 der Einhuellenden-Prereg)
c = 0,2 -0,042 (SE 0,019). Kontrolle 0,600 / 0,550 volle Spalten je Brett.
**argmax-Instrument @400, 200 Partien, Seed 20260931, c = 0,2
(`tor2a_k1c02_v23b01.json`): 0,3575 +- 0,059 volle Spalten gegen b01
0,5150 +- 0,065** (`tor2a_v23b01.json`; ungepaart, die b01-Dateien liegen im
Archiv), Seiten mit voller Spalte 116 gegen 168 von 400; volle Reihen 0,2025
gegen 0,1475; Punkte 46,15 gegen 46,80; Strafleiste 5,85 gegen 5,74.

**Lesart (vorlaeufig, gegen die Tabelle in par.14.4):** kein Arm erfuellt
Zeile 1 (signifikant vorn UND Spalten nicht unter der Kontrolle): c = 0,2 ist
bei Siegen und Margin signifikant vorn, liegt bei den Spalten aber in beiden
Instrumenten darunter (Arena t -1,85, argmax -0,16 bei getrennten KIs, die
sich nicht ueberlappen). Das ist der SPIEGEL des Suchtiefen-Tauschs
(`search_depth_column_optimum`: mehr Tiefe = staerker, weniger Spalten):
der Term macht den Blattwert margensensitiver, und die Suche kauft Punkte
dort, wo sie schneller liegen als in einer Spalte. Zeile 4 (Staerke faellt
monoton) ist widerlegt: 0,1 und 0,3 sind Nullbefunde, 0,2 ist vorn -- die
Familie ist NICHT geschlossen, aber die Nicht-Monotonie mahnt zur
Replikation. **Verdikt steht aus, bis c = 0,2 mit eigenem Seed repliziert
ist** (`generation_loop.md`: 160 Paare erfuellen die Zahl, die
Nicht-Monotonie ueber c verlangt trotzdem die zweite Stichprobe). Fuer die
Generatorwahl (`generation_loop.md`, Spaltenprofil entscheidet) ist c = 0,2
nach diesem Stand KEIN Kandidat; fuer den SPIELBETRIEB (Champion-Kante) ist er
nach der Replikation zu pruefen -- zwei getrennte Entscheide, wie in
par.8.4 der Einhuellenden-Prereg vorgesehen.

## par.16 REPLIKATION c = 0,2 und VERDIKT (2026-09-03, 15:20): der Staerkegewinn repliziert nicht, die Spalten bleiben darunter -- K1 ist kein Rezept-Kandidat

**Replikation** (Seed 20261003, Kontrolle plus c = 0,2, 2 x 80 mit Brett-
Tausch, sonst wie par.15; `paired_arena_env_k1_b01_{first,second}_s03.json`,
`k1_b01_swap_eval_s03.json`, `columns_k1_b01_{first,second}_s03.json`,
Laufzeit 2 x rund 17 min exklusiv): Knopf-Seite **83 : 77** gegen die
Basislinie 80 : 80, diskordant 39 / 36, McNemar p = 0,82, Block-Differenz
+0,019 (SE 0,045); Punkte 46,77, **Margin +2,03** (Block-SE 2,52);
Einheits-Klammerung 7,2 Prozent der Blaetter. Spalten der Knopf-Seite
0,494 gegen 0,532 (gepaart -0,036, Block-SE 0,079, t -0,46); H -0,009.

**Gepoolt ueber beide Seeds (320 Paare):** 187 : 133, diskordant 87 / 60,
McNemar p = 0,032, Block-Differenz +0,084 (SE 0,037, t 2,31, 64 Bloecke);
Margin +3,48 (SE 1,53). Die beiden Seeds unterscheiden sich in der
Siegdifferenz um z = 1,79 (+0,150 gegen +0,019) -- die erste Stichprobe
traegt den gepoolten Befund allein. Spalten gepoolt rund -0,08 je Partie
(-0,130 und -0,036); argmax-Instrument 0,3575 gegen 0,515 (par.15,
ungepaart, KIs ohne Ueberlappung).

**Verdikt (Tabelle par.14.4):** Zeile 1 faellt (Spalten unter der Kontrolle
in beiden Instrumenten). Zeile 4 faellt (keine monotone Verschlechterung:
alle Arme bei Siegen >= Basislinie, Margin in fuenf von fuenf Arm-Laeufen
positiv). Was bleibt, ist der Spiegel von Zeile 2: **die re-zentrierte
Margen-Utility macht die Suche margensensitiver (Margin +2 bis +5 in jedem
Lauf) und kauft das mit weniger Spalten; in Siegen ist der Gewinn klein und
nicht stabil** (einmal p = 0,006, einmal p = 0,82). Der Zuschnitt beantwortet
die Zeile-1-Frage damit so: die Punktemarge wird zu Punkten, nicht
verlaesslich zu Siegen. **K1 geht NICHT ins v24-Rezept** (Generatorwahl-
Regel: Spaltenprofil entscheidet, und das faellt), der Skalenwechsel par.4b
wird NICHT nachgezogen, der sigma-Folgearm und die Breitenprobe b = 10
entfallen (par.14.1: nur, wenn K1 traegt). Der Knopf bleibt gebaut
(Default 0, byte-identisch) und dokumentiert; eine Champion-Kante fuer den
SPIELBETRIEB mit c = 0,2 ist ein eigener, optionaler Nutzer-Entscheid, kein
Teil dieser Prereg. Einordnung zu par.11: die Familie "Score-Utility im
Blattwert" ist nicht geschlossen, aber die beiden gemessenen Formen (linear
par.8-10, saettigend-rezentriert hier) haben beide keinen verlaesslichen
Siegzuwachs gebracht -- weitere Formen brauchen eine neue Idee, nicht ein
neues Gewicht.

## par.17 CHAMPION-KANTE mit c = 0,2 (Nutzer-Wunsch 2026-09-03; gefahren 2026-09-04, 02:33-04:12): K1 kostet gegen den Champion

`tools/paired_gating.py` (seit heute mit `--spec-a/--spec-b`), `v23-b01_brierbest`
mit `MOSAIC_SCORE_UTILITY_C=0.2` gegen `v21_2d_brierbest` mit Spec "alle Knoepfe
0" (`k3v_off.spec.json`), @400/@400, Blockgroesse 5, Seed 20261004, SPRT
H1 p = 0,65, Deckel 200 Paare; Bezugskante b01 OHNE Knopf gegen denselben
Champion, GLEICHER Seed. Artefakte `paired_gating_result_v23-b01_k1c02_vs_v21_2d_brierbest.json`,
`paired_gating_result_v23-b01_vs_v21_2d_brierbest_s04.json`.

| Kante | Ergebnis | Paare | SPRT | Vorzeichentest p | gepaarte Differenz, 95%-KI |
| --- | --- | --- | --- | --- | --- |
| b01 + K1 c = 0,2 gegen v21 | **77 : 83** | 80 (Fruehstopp H0, LLR -3,05) | kein Beleg | 0,77 | -0,075 [-0,405, +0,255] |
| b01 ohne Knopf gegen v21 | **214 : 186** | 200 (Deckel) | kein Entscheid | 0,20 | +0,140 [-0,059, +0,339] |
| dieselben ersten 80 Paare, b01 ohne Knopf | 88 : 72 | 80 | -- | -- | -- |

**Verdikt:** auf denselben 80 Seeds faellt b01 mit K1 von 88:72 auf 77:83
gegen den Champion; die Bezugskante bestaetigt die v23-Kante vom 2026-08-31
(219:181) mit 214:186. **Keine Champion-Kante mit K1**; der Knopf bleibt
Default 0. Kein Elo-Eintrag (K1-Konfiguration ist kein Spieler der Leiter;
die Bezugskante ist eine Replikation der bestehenden Kante, nicht neu
eingetragen -- Promotions-Checkliste greift nicht, kein Champion-Wechsel).

