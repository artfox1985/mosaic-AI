<!-- STATUS: ENTSCHIEDEN | Frage: Laesst sich die Inferenz von der CPU auf die GPU verlagern -- erreicht Verschraenkung vieler gleichzeitiger Partien den Batch, an dem die GPU gewinnt? | Beleg: **OFFEN, vorregistriert 2026-08-10** (Nutzer-Richtung "weg von der cpu und hin zur gpu"). Teil 1 GEMESSEN: Speicher ist kein Engpass (1,5 MiB je Suche, Batch 512 = 0,76 GiB) ⇒ Regel 1, Weg V (Verschraenkung, suchneutral) statt Weg B (Virtual Loss, gating-pflichtig). Teil 2 GESCHLOSSEN (Commit `e1bce64`, ohne neue Messung): die Blatt-Erzeugungsrate wurde ANALYTISCH aus der vorhandenen Task-#32-Messung (`selfplay_time_profile.json`, Netz 62 % / Tiling 27 %) plus Little's Law hergeleitet -- ein eigener Null-Evaluator haette die Baumform degeneriert. Erreichbarer Batch **~140 bis ~590**, Startwert **N=256**, damit in der Gewinnzone der GPU-Kennlinie. Deckel Amdahl 2,6-5,3x. **ENTSCHIEDEN, nachgetragen 2026-08-21 (Verdikt 2026-08-14):** Weg V wurde umgesetzt (`PREREG_async_search.md` Stufe 1-3, Archiv-Branches `async_search_stage{1,3}_archive`) und in `PREREG_gpu_inference_path.md` §20-§23 vermessen -- Batch-Erwartung ERFUELLT (Fuellung 99,7 % bei N=128), Regel 3 trotzdem VERFEHLT (beste Zelle 1,255x gegen den ehrlichen Sync-Nenner 528,5 Partien/h): GPU-Verlagerung GESCHLOSSEN bis zum groesseren Netz. STALE-FALLE 2026-08-12: diese Zeile trug bis hierher noch "offen ist die Blatt-Erzeugungsrate" und hat genau dadurch einen Agenten-Auftrag ausgeloest, der die Zahl neu messen sollte -- sie lag seit `e1bce64` vor. Ein veralteter Index kostet Arbeit, nicht nur Klarheit. `evaluations/interleave_batch_probe.json` (nur Teil-1-Daten) -->

# Vorregistrierung: Verlagerung der Inferenz von der CPU auf die GPU

**Angelegt 2026-08-10, VOR jeder Messung.** Nutzer-Vorgabe: *"was können wir
machen das wir die gpu mehr nutzen. derzeit ist sie nur im training aktiv.
und das ist eher ein kleines zeitfenster"* und, zugespitzt: *"ich will weg
von der cpu und hin zur gpu"*.

Das ist keine Auslastungs-Kosmetik, sondern eine Verlagerung des
Arbeitsschwerpunkts. Diese Vorregistrierung legt fest, woran sie hängt und
welche Messung darüber entscheidet -- **bevor** gebaut wird.

## Ausgangslage

Je Generation (STATUS, Kostenprofil):

| Phase | Dauer | Rechenwerk |
|-------|-------|------------|
| Self-Play | ~18 h | **CPU**, 11 Threads |
| Cache-Bau | ~3 h | CPU |
| Training | ~3,5 h | **GPU** |
| Gatings/Arenen | ~1-1,5 h je Lauf | **CPU** |

Die GPU arbeitet also ~3,5 h von ~25 h. Und 62-81 % der Self-Play-Zeit sind
**Inferenz** (Task #81, Amdahl-Split) -- genau die Arbeit, für die eine GPU
gebaut ist.

## Warum das die #82-Schließung nicht widerlegt, sondern ihre Bedingung einlöst

`PREREG_gpu_inference_batcher.md` ist am 2026-08-10 nach Regel 1 geschlossen
worden: an den erreichbaren Batches 11/22/44 liefert die RTX 3060
2.581/6.197/14.060 Evals/s und bleibt damit unter der unteren CPU-Schranke
von 17.600. Der Vermerk dazu lautet aber ausdrücklich **"nur zusammen mit
blatt-paralleler Auswertung sinnvoll"** -- und die gemessene Kurve zeigt, wo
der Gewinn liegt:

| Batch | Evals/s | vs. CPU-Aggregat |
|-------|---------|------------------|
| 44 | 14.060 | 0,40-0,80x |
| 64 | 20.863 | 0,59-1,19x |
| **128** | **41.959** | **1,19-2,38x** |
| 256 | 78.896 | 2,24-4,48x |
| 512 | 162.635 | 4,62-9,24x |

**Die GPU ist nicht langsam, sie ist ausgehungert.** Der Hebel ist der
erreichbare Batch, heute 11, weil 11 Threads je genau ein Blatt bewerten.

**Amdahl-Deckel**: bei 62-81 % Inferenzanteil ist selbst bei unendlicher
Beschleunigung nur **2,6x bis 5,3x** auf die Self-Play-Zeit zu holen. Eine
Generation ginge von ~25 h auf 10-18 h. Mehr ist nicht drin, und das gehört
vorher gesagt, damit später keine 10x-Erwartung enttäuscht wird.

## Zwei Wege, fundamental verschieden im Risiko

### Weg V -- Verschränkung vieler gleichzeitiger Partien (empfohlen)

Statt 11 Partien laufen N gleichzeitig; ihre Suchen wechseln sich ab, sodass
zu jedem Zeitpunkt bis zu N Blätter auf Bewertung warten. **Jede einzelne
Suche bleibt bitgleich** -- sie wartet nur länger auf ihre Antwort.

- Kein Gating nötig, keine Stärkefrage, Parität über `tools/parity_probe.py`
  beweisbar.
- Kosten: Speicher für N Spielzustände samt Suchbäumen; Umbau der
  Self-Play-Schleife von "Partie fertig spielen" auf eine Zustandsmaschine
  mit anstehender Bewertung.

### Weg B -- blatt-parallele Suche mit Virtual Loss (nicht empfohlen als Erstes)

Eine Suche holt 8-16 Blätter gleichzeitig; mit 11 Threads ergibt das 88-176.

- **Virtual Loss verändert die Suche** (die Auswahl sieht künstlich
  abgewertete Geschwister) ⇒ Gating zwingend.
- Die k=4-Erfahrung desselben Tages mahnt: Eingriffe in die Suchsemantik
  haben in diesem Projekt schon einmal geschadet
  (`PREREG_ismcts_determinizations.md`: Mitteln über Stichproben eines
  unbekannten Zustands, -8,75pp bei vierfachem Budget).

Weg V zuerst, Weg B nur, wenn V den nötigen Batch nicht erreicht.

## Die Probe (Teil 1): ist Batch >= 128 überhaupt erreichbar?

Zwei Größen entscheiden, und beide sind billig messbar:

1. **Speicher je gleichzeitiger Suche.** Der Suchbaum hält je Knoten einen
   vollen `GameState` (`net_mcts.rs::Node.state`) -- das ist der Treiber, nicht
   der Spielzustand selbst. Gemessen als Zuwachs des **Peak Working Set** über
   einen Suchlauf bei 400 Sims.
2. **Effektiver Batch = N x Auslastungsgrad.** Ein Blatt je Partie gilt nur,
   solange eine Suche wirklich auf eine Bewertung wartet. Zwischen
   Zug-Anwendung, Tiling und Rundenübergang steht kein Blatt an. Der
   Auslastungsgrad ist damit nach oben durch den **Inferenzanteil (62-81 %)**
   begrenzt -- er IST das Tastverhältnis.

Maschine (gemessen 2026-08-10): **31,9 GiB RAM** (20,6 frei), **12 logische
Kerne**, **12 GiB VRAM**.

`N_max = verfügbarer RAM / Speicher je Suche`, davon der Auslastungsgrad ⇒
erwarteter effektiver Batch ⇒ zugehörige Evals/s aus der Tabelle oben.

## Entscheidungsregeln (vorab)

1. **Effektiver Batch >= 128** ⇒ die GPU liefert >= 1,19-2,38x. Weg V wird
   gebaut, `#82` gilt unter seiner eigenen Bedingung als eingelöst.
2. **Effektiver Batch 64-128** ⇒ Bereich 0,59-2,38x, also möglicherweise
   ein Verlust. Dann muss **die CPU-Referenz nachgemessen** werden (das
   PREREG-Band 17.600-35.200 ist zu breit für ein Verdikt in dieser Zone),
   bevor irgendetwas gebaut wird.
3. **Effektiver Batch < 64** ⇒ Verschränkung allein erreicht die Gewinnzone
   nicht. Dann ist Weg B der einzige Weg -- und der braucht ein Gating.
   Alternative in dieser Lage: die Frage vertagen, statt Suchsemantik für
   einen unsicheren Durchsatzgewinn zu riskieren.
4. **Speicher-Ausschluss**: N, das mehr als **16 GiB** beansprucht, gilt als
   nicht erreichbar (32 GiB gesamt, Cache-Bau braucht ~13 GiB, und der
   Rechner soll benutzbar bleiben).

## Was diese Verlagerung NICHT bringt -- vorab, damit es keine Enttäuschung wird

**Self-Play und Training können weiterhin nicht gleichzeitig laufen.** Beide
brauchen dann die GPU, und die Erfahrung steht schon im Projekt-Gedächtnis:
GPU-Teilung mit einem laufenden Spiel kostete Faktor 9. Der Gewinn ist
Durchsatz INNERHALB einer Phase, nicht Überlappung der Phasen. Die Bahnen
bleiben sequenziell, sie werden nur kürzer.

Ebenso unberührt: der Tiling-Solver und die Runde-5-Suche sind
kombinatorisch, nicht tensoriell -- die bleiben auf der CPU, und sie sind
nach dem Kostenprofil auch nicht der Engpass (Runde 5: 4,3 %).

## ERGEBNIS Teil 1 (2026-08-10): REGEL 1 -- Speicher ist kein Engpass

Instrument: `tools/interleave_batch_probe.py`. Peak-Working-Set-Zuwachs ueber
einen 400-Sims-Suchlauf, 3 Wiederholungen, Maschine 31,9 GiB RAM (20,3 frei).

| Groesse | Messwert |
|---------|----------|
| Speicher je gleichzeitiger Suche | **~1,5 MiB** (400 Knoten x ~2,6 KB Zustand -- passt zum Bitpacking) |
| Batch 128 | 0,19 GiB |
| Batch 512 | 0,76 GiB |
| Batch 1024 | 1,52 GiB |
| CPU-Nachfrage nach Wegfall der Inferenz | 46.000-185.000 Evals/s |
| GPU-Angebot bei Batch 512 | 162.635 Evals/s |

**Verdikt: Regel 1.** Speicher ist kein Engpass; Nachfrage und Angebot
ueberlappen sich. **Weg V wird gebaut.** Der verbleibende Deckel ist Amdahl
(2,6-5,3x), NICHT der Batch.

### KORREKTUR meiner eigenen Ableitung (gleicher Tag, direkt nach dem ersten Lauf)

Der erste Lauf rechnete `N_max = nutzbarer RAM / Speicher je Suche` und
multiplizierte das mit dem Auslastungsgrad -- Ergebnis: effektiver Batch
6.600-12.300. **Das ist Unsinn**, und der Fehler liegt im Modell, nicht in der
Messung: die Rechnung unterstellt Speicher als BINDENDE Schranke. Bei 1,5 MiB
je Suche ist er das nicht, und 10.000 gleichzeitige Suchen sind keine
praktische Zahl.

Bindend ist die **CPU-seitige Baumarbeit** (Auswahl, Backup,
Zustands-Klonen). Sie verschwindet nicht, wenn die Inferenz auf die GPU
wandert -- sie ist genau der Amdahl-Rest. Der Speicher beantwortet deshalb
nur eine Ja/Nein-Frage: reicht er fuer die Gewinnzone? Er reicht.

Die Sonde ist entsprechend umgebaut und traegt die Korrektur im Code, damit
sie nicht wieder als "effektiver Batch" fehlgelesen wird.

### Teil 2: ERLEDIGT, ohne neue Messung -- die Zahl lag schon vor

Ich hatte hier eine "naechste Messung vor dem Bau" notiert (Blatt-Erzeugungsrate
via Null-Evaluator). **Die war ueberfluessig**, und der Weg dorthin ist zweimal
falsch abgebogen:

1. Erst habe ich die Zerlegung von Hand versucht (Gesamtzeit einer Suche minus
   Zahl der Evals x isoliert gemessener Eval-Preis). Ergebnis: Inferenz kaeme auf
   **120 %** der Gesamtzeit, Baumarbeit also negativ. Ungueltig, weil die Suche
   `eval_pair` nutzt (0,82 ms je Eval statt 0,97 einzeln) und von Cache-Effekten
   profitiert -- ein isoliert gemessener Preis ist nicht abziehbar.
2. Dann wollte ich einen Null-Evaluator bauen. Der hat einen ECHTEN
   methodischen Haken, der ueber meine erste Begruendung hinausgeht: mit
   konstantem Blattwert wird die Suche **degeneriert** (entartetes completed-Q,
   andere Baumform, andere Knotenzahl) -- gemessen wuerde die Baumarbeit eines
   ANDEREN Baums.
3. **Das Instrument existiert seit Task #32**: `profiling.rs` trennt
   `SelfplayCat::NetInference` von `TotalSelfplay`, dazu
   `GUMBEL_NET_EVAL_NANOS/_CALLS/_INSTANCES` (Instanzen unterscheiden `eval`
   von `eval_pair`). Hinter `MOSAIC_PROFILE_SELFPLAY`, Default aus. Und die
   Messung ist GELAUFEN: Commit 6af37ca, **Netz 62 %, Tiling 27 %, Runde 5
   4,3 %**.

Damit ist die Baumarbeit der Rest (38 %), die Erzeugungsrate bei kostenloser
Inferenz also `1/0,38 = 2,6x` der heutigen -- **derselbe Amdahl-Faktor, der
oben schon steht**. Es gab nichts Neues zu messen.

### Erreichbarer Batch, analytisch (Little)

    Batch = Erzeugungsrate x GPU-Latenz

| Groesse | Wert |
|---------|------|
| Nachfrage (2,6-5,3x heutiges Aggregat 17.600-35.200) | 46.000-186.000 Evals/s |
| GPU-Latenz bei Batch 128 / 512 | 3,05 / 3,15 ms |
| **Erreichbarer Batch** | **~140 bis ~590** |

Das liegt vollstaendig in der Gewinnzone (Batch 128 = 1,19-2,38x, Batch 512 =
4,62-9,24x). **Teil 2 ist damit geschlossen, Weg V ist rechnerisch gedeckt.**

Der Zielwert fuer die Implementierung ist entsprechend **N = 256 als
Startpunkt** (0,38 GiB Speicher, mittig im erreichbaren Band), nicht 512 --
bei 512 waere die Annahme, die CPU erreiche das obere Ende ihres
Nachfragebandes, und das ist die optimistischere der beiden Kanten.

### Lehre, die ins Gedaechtnis gehoert

Zweimal an einem vorhandenen Werkzeug vorbeigebaut (nach `arena.py` jetzt
`profiling.rs`). Die Regel steht in CLAUDE.md und im Projekt-Gedaechtnis. Vor
jeder neuen Sonde: erst `profiling.rs`, `tools/` und die Kategorien-Enums
lesen.
