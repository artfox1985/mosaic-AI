Ich würde nicht das Spiel oder die bisherigen Artefakte wegwerfen, sondern einen Relaunch als „zweite Forschungsarchitektur“ machen: dieselben Erkenntnisse, aber mit einem viel kleineren, strengeren Kern.

## Was ich von Anfang an anders bauen würde

| Schicht            | Relaunch-Entscheidung                                                                                     | Learning aus dem Projekt                                                                                                                                       |
| ------------------ | --------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Spielzustand       | Ein kanonischer Zustand, ein Transition-Dispatcher, ein exakter Replay-Pfad                               | Unterschiede zwischen Suche, Self-Play, Korpus und Replay sind die teuersten Fehlerquellen. Sie erzeugen falsche Labels oder verdecken Fehler vor jeder Arena. |
| Informationsmodell | Sicht jedes Spielers explizit modellieren; verdeckte Information nur über einen zentralen Determinisierer | Vollmischung des Kuppelstapels und verlorenes eigenes Wissen waren Korrektheitsprobleme, nicht Elo-Fragen.                                                     |
| Netz               | Start mit Policy + WDL-Value; jeder Hilfskopf ist optional und muss seinen Nutzen beweisen                | Zusätzliche Köpfe, Losses und Outputs wurden oft übernommen, bevor klar war, ob sie den gemeinsamen Rumpf wirklich stärken.                                    |
| Suche              | Eine einfache, deterministische MCTS-Variante mit wenigen Specs                                           | Komplexe Durchsatzarbeit konnte Batches verbessern, verfehlte aber ihr Kostenziel klar.                                                                        |
| Daten              | Versionierter Generator, festen Split, kompletter semantischer Cache-Key                                  | Cache-Kollisionen, maskierte Policy-Träger und falsche Validierungsdaten haben Ergebnisse beinahe fehlgedeutet.                                                |
| Auswertung         | Korrektheit, Verhalten und Spielstärke getrennt messen                                                    | Offline-Metriken und Arena haben mehrfach in verschiedene Richtungen gezeigt.                                                                                  |

## Das Kernprinzip

Nicht zuerst „Wie wird das Netz schlauer?“, sondern:

> Ist das, was die Suche bewertet, exakt das, was später ausgeführt, geloggt und trainiert wird?

Das ist die größte Lehre. Der Moon-Kopf lernte lange ein konstantes Ziel; eine Action-ID bündelte zuvor falsche Aktionen; verdecktes Wissen wurde symmetrisch zerstört; ein Val-Cache war kontaminiert. Solche Defekte kann eine Arena zwischen zwei gleich fehlerhaften Agenten nicht finden. [Architekturreferenz](architecture_reference.md) · [unprimed Review](../evaluations/PREREG_implementation_review_unprimed.md)

## Mein Relaunch-Fahrplan

1. **Referenzspiel zuerst.**  
   Rust ist alleinige Wahrheit für Legalität, Zustandsübergang, Sicht und Serialisierung. Jede Partie ist exakt replaybar. Fuzzing prüft: legaler Zug, Transition, Serialize/Deserialize und Replay führen immer zu demselben Zustand.

2. **Minimalagent als harte Baseline.**  
   Ein Netz mit Policy und WDL-Value, ein klarer Suchmodus, ein fester Spec. Keine Moon-, Ownership-, Gegnerpunkte- oder Endgame-Köpfe im Startrezept. Jeder spätere Kopf muss gegen diese Baseline in derselben Generation gewinnen oder eine klar definierte Nichtunterlegenheitsregel bestehen.

3. **Eine Lernschleife, drei getrennte Tore.**
   
   - Korrektheit: Golden Replays, Sicht-/Informationsaudit, Vertrags- und Cache-Tests.
   - Verhalten: baut das Netz die gewünschten Strukturen, wählt es sinnvolle Aktionen, nutzt es sichtbares Wissen?
   - Stärke: gepaarte Arena über mehrere Seeds.  
     Nichts aus einer Ebene darf eine Aussage der anderen ersetzen.

4. **Korpus und Labels als Produkt behandeln.**  
   Jeder Datensatz trägt Generator, Spec, Modellhash, Suchbudget, Sichtschema, Action-Schema, Policy-Maskierung und Cache-Schema. Der Val-Split wird vor Erzeugung fest fixiert. Kein Environment-Override darf semantisch unsichtbar bleiben.

5. **Suche vor Heuristikstapeln.**  
   Der größte offene fachliche Hebel bleibt der Rundenübergang: Drafting soll das anschließende Tiling besser sehen. Aber ein verbesserter Blattübergang darf nur bleiben, wenn er einen bisherigen Proxy ersetzt. Sonst wächst Komplexität schneller als Erkenntnis. [Rundenübergang-Prereg](../evaluations/PREREG_round_transition_search_sampling.md)

## Was die History ziemlich klar sagt

- **Offline-Güte ist kein Stärke-Nachweis.** Lambda-Ziele waren offline vielfach positiv und verloren in der Arena. Gewichtssweeps, Value-Kalibrierungen und Punkte-Blends lieferten ähnliche Warnungen. Arena bleibt das Entscheidungsinstrument. [Prereg-Index](../evaluations/PREREG_INDEX.md)
- **Mehr oder raffiniertere Architektur ist selten der Engpass.** Async Search füllte den Batch fast vollständig, erreichte aber nur Faktor 1,255 statt des nötigen 2x. Große Umbauten brauchen ein starkes Kosten- und Nutzen-Tor.
- **Repräsentation und korrekte Information sind wertvoller als kosmetische Losses.** Sichtmerkmale und korrekt modelliertes Stapelwissen sind zumindest kausal plausibel; an manchen davon hängt echte Spielstärke oder korrekteres Verhalten. Aber auch hier gilt: Information hineinzugeben reicht nicht, wenn Suche und Ziel sie nicht konsumieren.
- **Materialqualität zählt.** Mehr Korpus und der bessere Heuristik-Lehrer haben deutlich mehr getragen als viele Hyperparameter-Ideen.
- **H0 heißt nicht „gleich gut“.** Die bisherige Dokumentation hat das zunehmend sauber gelernt. Für Vereinfachungen braucht ihr explizite Nichtunterlegenheitsmargen.

Mein Fazit: Der Relaunch wäre kein „größeres AlphaZero“, sondern ein kleineres, überprüfbares System mit weniger Köpfen, weniger Env-Knöpfen, exakt modellierter Information und einer harten Trennung zwischen Korrektheit und Elo. Die jetzige neue [Minimal-Core-Prereg](../evaluations/PREREG_minimal_strength_core.md) ist im Grunde schon der Übergang dorthin.



Der Unterschied ist: Variante B macht das Tiling im Blatt sichtbar, aber **nicht selbst zum Suchentscheid**. Anmerkung 1

Bei B läuft für jeden Drafting-Blattzustand genau der bestehende, rundenscore-orientierte Tiling-Solver. Erst dessen einzelnes Ergebnis wird nach einer Neubefüllung vom Netz bewertet:

```
Drafting-Aktion → ein Tiling-Ergebnis des Solvers → Neubefüllung → Netz-Value
```

Das Netz kann dadurch bessere Drafting-Aktionen bevorzugen, weil es deren tatsächliche Tiling-Folge sieht. Es kann aber nicht sagen: „Für dieselbe Drafting-Lage nehme ich ein etwas schlechteres Rundentiling, weil das Nachbrett langfristig besser ist.“

Mein Top-K-Vorschlag wäre eine spätere, separate Erweiterung:

```
Drafting-Aktion → K Tiling-Endbretter nahe am Rundenscoreoptimum
               → Neubefüllung je Endbrett → Netz-Value
               → wähle das Endbrett mit besserem Zukunftswert
```

Er verändert also die **Tiling-Wahl selbst**, während B nur die **Drafting-Bewertung mit bereits aufgelöstem Tiling** korrigiert.

Darum: zuerst B. Wenn B stärkt, aber die Mehrdeutigkeits-Sonde zeigt, dass es oft mehrere ähnlich gute Tiling-Pläne mit deutlich verschiedenen Nach-Runden-Values gibt, wäre Top-K der nächste sinnvolle Ausbau. Wenn der Solver fast immer einen klaren Plan hat, bringt Top-K nur Kosten und Komplexität.



Dann sollte das Netz in R1/R2 nicht plötzlich zum alleinigen Richter über Tiling werden. Die richtige Frage ist nicht „Wie machen wir den frühen Value größer?“, sondern:

> Wann ist sein Ranking zwischen zwei Tiling-Folgezuständen verlässlich genug, um eine exakte lokale Entscheidung zu überstimmen?

Dass der Value in Runde 1 am schwächsten ist, ist bereits dokumentiert. Ein tieferer Bootstrap war kein guter Ausweg: Horizont 3 war teurer und traf das Ziel schlechter. [Bootstrap-Horizont](../evaluations/PREREG_bootstrap_horizon.md)

Ich würde daher eine rundenabhängige Architektur bauen:

```
R1/R2: exakte lokale Struktur + Unsicherheits-/Robustheitsregel
R3/R4: Zukunfts-Value darf enge Tiling-Alternativen entscheiden
R5: exakter Endspielsolver
```

Konkret:

1. **B trotzdem in R1/R2 nutzen, aber bescheiden lesen**  
   Variante B löst das Tiling und geht wenigstens in den Zustand nach der Neubefüllung. Das Netz bewertet also nicht mehr „vor Tiling“, sondern eine Runde später. Das beseitigt einen Informationsfehler, auch wenn der resultierende Value noch unsicher ist.

2. **Value in frühen Runden nur als Tie-Breaker über strukturell plausible Tiling-Pläne**  
   Der Tiling-Solver erzeugt Top-K-Endbretter, aber nur aus einer engen, nicht-dominierten Menge:
   
   - kein schlechterer Rundenscore ohne strukturellen Gewinn;
   - keine vermeidbar zerstörten erreichbaren Zellen;
   - keine schlechtere Spalten-/Spezialfeld-Erreichbarkeit;
   - Chips und Reihenoptionen bleiben erhalten.
   
   Erst innerhalb dieser Pareto-Menge darf der Netz-Value entscheiden. Dadurch kann ein schlechter früher Value nicht beliebig einen sofort klar schlechteren Tiling-Plan kaufen.

3. **Nicht den Mittelwert, sondern Stabilität über Zufall bewerten**  
   Für jedes Top-K-Endbrett kann man wenige, gekoppelte Neubefüllungen aus demselben Beutel/Turm ziehen. Entscheidend wäre nicht nur:
   
   `mittlerer Netz-Value`
   
   sondern auch:
   
   `wie stabil bleibt die Rangfolge über die möglichen Füllungen?`
   
   Wenn Plan A in fast jeder Füllung vor Plan B liegt, ist das ein brauchbares Signal. Wenn die Rangfolge kippt, ist die richtige frühe Entscheidung nicht „Netz glaubt A“, sondern „beide sind noch nicht sauber unterscheidbar“ -- dann gewinnt die strukturell robustere Lösung.

4. **Eine Counterfactual-Ranking-Sonde vor jedem Bau**  
   Das wäre der eigentlich spannende Test: echte R1/R2-Rundenendzustände nehmen, mehrere gute Tiling-Pläne erzeugen und sie mit gemeinsamen Zufallsseeds mehrfach fortsetzen. Dann messen:
   
   - trifft der Value die Reihenfolge der Pläne?
   - ab welcher Runde?
   - nur bei welchen Fällen: Spezialfeld, Chip, Spalte, lange Reihe?
   - ist Mittelwert, Worst-Case oder Rang-Stabilität die bessere Kennzahl?
   
   Falls das Netz in R1 zwischen den Plänen praktisch zufällig rangiert, darf es dort nicht entscheiden. Falls es bei speziellen Zuständen schon zuverlässig ist, kann man genau dort den Netz-Tie-Break aktivieren.

Mein Favorit wäre also kein pauschales „früh mehr suchen“, sondern ein **unsicherheitsbewusster Tiling-Selector**:

```
exakter Solver → nicht-dominierte Top-K-Pläne
              → wenige gekoppelte Chance-Folgen
              → Netz nur bei stabiler Rangordnung
              → sonst strukturell robustester Plan
```

Das vermeidet auch die frühere Falle des Rundenscore-Terms: Der hat kurzfristige Punkte bevorzugt und dabei langfristige Spalten und Spezialfelder beschädigt. Hier wäre Rundenscore nur eine harte Schranke; Zukunftswert entscheidet nur nahe beieinanderliegende, tatsächlich offene Tiling-Optionen.
