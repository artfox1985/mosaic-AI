# Vorregistrierung: der Inferenz-PFAD zur GPU

**Angelegt 2026-08-12, Nutzer-Entscheid** — auf die Frage, wie nach dem Befund
weiterzugehen ist: *"Erst Architektur entscheiden"*.

Diese Datei füllt eine Lücke, die `PREREG_gpu_inferenz_batcher.md` (Regel 2)
selbst verlangt hat und die `PREREG_gpu_verlagerung.md` übersprungen hat.

## 1. Der Befund, der sie nötig macht (GEPRÜFT)

- `engine/Cargo.toml`: einzige Inferenz-Abhängigkeit ist **`tract-onnx = "0.21"`**,
  mit dem Kommentar *"kein libtorch/onnxruntime nötig"*.
- `net.rs:14`: *"Reines Rust — keine libtorch/onnxruntime-Abhängigkeit."*
- tract läuft **CPU-only**.
- Die GPU-Kennlinie, auf der `PREREG_gpu_verlagerung.md` den Ziel-Batch 140–590
  und den Startwert N=256 aufbaut, stammt aus `tools/gpu_batch_throughput.py` —
  einem **Python/PyTorch-Benchmark** auf dem `.pth`-Checkpoint.

**Die Rust-Engine hat also keinen Weg zu der GPU, deren Zahlen die Begründung
tragen.** Eine Verschränkung innerhalb der Engine würde ihre Blätter an tract
übergeben, also an die CPU: sauber suchneutral, aber ohne GPU-Gewinn.

## 2. Der Widerspruch in der bestehenden Fassung — und er ist grundsätzlich

`PREREG_gpu_verlagerung.md` begründet Weg V damit, er sei **suchneutral**, im
Unterschied zu Weg B (Virtual Loss), der gating-pflichtig wäre. Diese Neutralität
bezieht sich aber ausschließlich auf das **Nebenläufigkeitsmodell** — auf die
Frage, ob die Auswahlreihenfolge im Baum verändert wird.

**Sie kann sich nicht auf die Inferenz beziehen.** Jeder Weg auf die GPU wechselt
die Inferenz-Maschinerie: tract gegen PyTorch (Weg A) oder tract gegen
ONNX-Runtime-CUDA (Weg B). Zwei verschiedene Implementierungen derselben
Netzarchitektur liefern **nicht bitgleiche** Zahlen. Damit gilt:

- Der Paritäts-Hash `8c6684ff…` **kann einen GPU-Umbau nicht überleben.** Das ist
  keine Nachlässigkeit, sondern eine Eigenschaft des Vorhabens.
- Passend dazu hält `net.rs:840` schon für den bestehenden Batch-Pfad fest, dass
  tract für verschiedene Batch-Pläne **keine Bit-Gleichheit** garantiert — der
  vorhandene Präzedenzfall arbeitet mit **Toleranz 1e-5**, nicht mit Identität.

**Folge, vorab festgehalten**: "suchneutral" heisst hier *Baumverhalten unverändert
bei toleranzgleicher Inferenz*, nicht *byte-identisch*. Der Abnahmenachweis ist
deshalb ein **Toleranz**- und ein **Stärke**-Nachweis, nicht der Golden-Hash. Wer
das anders erwartet, plant ein unmögliches Kriterium — ich habe im ersten
Umsetzungsauftrag genau das verlangt ("identische Ausgaben") und lag damit falsch.

## 3. Die zwei Wege

### Weg A: Cross-Language-Queue zu Python/torch

Rust sammelt N Blätter, schickt die Merkmalsvektoren an einen Python-Prozess mit
torch/CUDA, bekommt die Ergebnisse zurück.

- **Dafür**: nutzt die BEREITS GEMESSENE Kennlinie (Batch 128 → 41.959 Evals/s,
  Batch 512 → 162.635 Evals/s) — kein neuer Benchmark nötig. Kein neuer
  Rust-Abhängigkeitsbaum.
- **Dagegen**: IPC je Batch. Die Merkmalsgrösse ist zu RECHNEN und die Rundlaufzeit
  zu MESSEN, nicht zu schätzen — Ausgangspunkt: 76 Ebenen à 6×6 plus 708 flache
  Merkmale je Position. Die IPC-Zeit muss deutlich unter der GPU-Zeit liegen
  (3,05 ms bei Batch 128, 3,15 ms bei Batch 512), sonst frisst sie den Gewinn.
- **Zu messen ZUERST**: Rundlaufzeit für einen Batch von 256 über den gewählten
  Kanal (shared memory / Pipe / Socket), leer und mit echter Nutzlast.

### Weg B: CUDA-fähiger Rust-Pfad (`ort`-Crate mit CUDA-Provider)

tract wird für den GPU-Fall durch ONNX Runtime mit CUDA-Provider ersetzt.

- **Dafür**: kein IPC, ein Prozess, ein Speicherbild. Batching bleibt vollständig
  in Rust.
- **Dagegen**: neue Abhängigkeit samt CUDA-Laufzeit, und **die Kennlinie gilt
  nicht** — sie wurde an PyTorch gemessen, nicht an ORT-CUDA. Sie müsste neu
  gemessen werden, bevor irgendein Batch-Startwert begründet ist.
- **Zu messen ZUERST**: dieselbe Kennlinie wie `gpu_batch_throughput.py`, aber
  über ORT-CUDA auf dem ONNX-Modell statt über torch auf dem `.pth`.

## 4. Entscheidungsregeln, vorab

1. **Weg A ist gedeckt, wenn** die gemessene Rundlaufzeit für Batch 256 unter
   einem Drittel der GPU-Zeit desselben Batches liegt. Darüber ist der Gewinn
   nicht mehr die 2,6–5,3x, mit denen das Vorhaben begründet wurde.
2. **Weg B ist gedeckt, wenn** die neu gemessene ORT-CUDA-Kennlinie bei Batch
   140–590 mindestens den Durchsatz erreicht, den die torch-Messung dort zeigt.
   Erreicht sie ihn nicht, ist Weg A trotz IPC der bessere.
3. **Beide sind NICHT gedeckt, wenn** der Amdahl-Deckel nach Abzug der jeweiligen
   Zusatzkosten unter **2,0x** fällt. Dann ist der Umbau kein Durchsatzprojekt
   mehr, sondern eine Wette.

## 5. Was NICHT Teil dieser Entscheidung ist

Die **Verschränkungs-Mechanik** selbst (Interleaving über N Suchen, der Knopf, der
Toleranz-Paritätstest) ist von der Pfadfrage unabhängig und in beiden Wegen
identisch. Sie kann gebaut werden, sobald der Pfad entschieden ist — aber nicht
vorher, weil erst der Pfad den Batch-Startwert begründet.

## 6. Reihenfolge

1. Merkmalsgrösse je Position AUSRECHNEN und die Rundlaufzeit für Batch 256
   MESSEN (Weg A) — die billigere der beiden Messungen.
2. Nur wenn Weg A an Regel 1 scheitert: ORT-CUDA-Kennlinie messen (Weg B).
3. Entscheiden, dann die Verschränkung bauen.

Begründung: Weg A braucht **keine neue Abhängigkeit** und seine Messung ist ein
IPC-Rundlauf, also billig. Weg B verlangt einen neuen Abhängigkeitsbaum, bevor
überhaupt eine Zahl vorliegt.


---

## 7. WEG A GEBAUT (2026-08-12) — Kanal steht, Abnahme NICHT bestanden

`MOSAIC_TORCH_IPC_ENABLED=1` (Default aus): Rust schickt die Blatt-Merkmale über
eine dateigestützte `mmap` an `tools/torch_ipc_server.py` (torch), Signalisierung
über TCP-Loopback. Neu: `engine/src/net_ipc.rs`, eingehängt in
`net.rs:357-375` (`Net::eval_batch`), `memmap2` als Abhängigkeit.

`cargo test --lib` **375 bestanden / 15 ignoriert** (Baseline 366/14, also +9 neue
Unit-Tests und +1 ignorierter Toleranztest, keine Regression).

### Paritätsprobe: hält — SELBST GEPRÜFT nach Wheel-Neubau

Der Agent konnte das nicht zeigen (er durfte kein Wheel bauen, die installierte
`.pyd` war älter als seine Änderungen). Nach meinem Neubau und Install:

    PARITAETS-HASH: 8c6684ffba06cf3e16e898b83325f3154c04efac555c8e862c079b71155bd423
    OK -- Defaults sind byte-identisch zum Bestand.

Bei ausgeschaltetem Knopf ist der Bestand also unberührt, wie §2 es verlangt.

### Der TOLERANZ-Vergleich: drei von vier Köpfen bestehen, der POLICY-Kopf NICHT

Gemessen vom Agenten (Batches 1/2/5/16, CPU, `v20_2d_opp_brierbest`), Toleranz
1e-5 nach dem Präzedenzfall `net.rs:820/830/864/875`:

| Kopf | max. Abweichung tract gegen torch | gegen 1e-5 |
| ---- | --------------------------------: | ---------- |
| value | 0,00000048 | bestanden |
| moon | 0,00000131 | bestanden |
| points | 0,00000051 | bestanden |
| **policy** | **0,00003433** | **VERFEHLT, Faktor 3,4** |

**Der Agent hat die Testzusicherung NICHT aufgeweicht** -- der Test schlägt beim
`--ignored`-Aufruf ehrlich fehl. Das ist die richtige Entscheidung: eine
angepasste Toleranz hätte den Befund verschwinden lassen, statt ihn zu zeigen.

### Was der Policy-Befund bedeutet, und was NICHT

**Ungeprüfte Erklärung des Agenten**, hier als solche markiert: Policy sind 406
unbeschränkte rohe Logits ohne Tanh, während die drei bestehenden Köpfe
tanh-begrenzt sind -- größere absolute Werte häufen über ONNX/tract gegen
Eager-Torch mehr Gleitkomma-Drift an.

Das ist plausibel und es ist **nicht dasselbe wie harmlos**. Der Policy-Kopf setzt
die Priors der Gumbel-Wurzelauswahl. Ob eine Abweichung von 3,4e-5 auf Logits die
Auswahl je kippt, ist eine EIGENE Frage, und sie ist offen. Zwei Wege, sie zu
beantworten, keiner davon gefahren:

1. **Auf die Auswahl messen statt auf die Zahl**: dieselbe Wurzelstellung mit
   beiden Pfaden, und zählen, wie oft die Gumbel-Top-m-Menge und der gewählte Zug
   abweichen. Das ist die Größe, die zählt -- eine Logit-Differenz, die die
   Rangfolge nicht ändert, ist gleichgültig.
2. **Toleranz begründet neu setzen**: 1e-5 stammt aus dem tract-gegen-tract-
   Vergleich verschiedener Batch-Pläne. Für tract-gegen-torch ist sie
   möglicherweise die falsche Marke -- aber eine neue Marke braucht eine
   Begründung aus der Wirkung, nicht aus dem Wunsch, den Test grün zu sehen.

**Weg A ist damit gebaut und nicht abgenommen.** Der Kanal funktioniert, die
Parität bei Default hält, und die offene Frage ist präzise: kippt die
Policy-Abweichung die Zugwahl?

### Zuschnitt-Vorbehalte (Agenten-Entscheidungen, nachträglich bewertet)

- Batch-Deckel **16**, nicht 256: `eval_batch` deckelt heute bei
  `EVAL_BATCH_MAX_N`. Damit ist der gemessene Durchsatzvorteil (Batch 140-590)
  mit diesem Stand **noch nicht abrufbar** -- er kommt erst mit der Verschränkung,
  die §5 ausdrücklich ausschliesst. Der Kanal ist Vorarbeit, kein Gewinn.
- `eval_batch` hatte vor dem Umbau **keinen Produktions-Aufrufer** (nur Tests).
  Der Knopf berührt den heutigen Suchpfad also gar nicht -- das erklärt die
  gehaltene Parität und begrenzt gleichzeitig die Aussagekraft des Umbaus.
- Kein Retry nach einmal erkannter Nichterreichbarkeit: ein später gestarteter
  Server wird erst nach Rust-Neustart gesehen.


---

## 8. POLICY-TOR: WIRKUNGSLOS -- Weg A auf der Inferenz-Achse abgenommen

Die Toleranzueberschreitung aus §7 (Policy 3,4e-5 gegen 1e-5) wurde auf ihre
WIRKUNG gemessen statt auf die Zahl. Grund: der Policy-Kopf setzt die Priors der
Gumbel-Wurzelauswahl, und eine Logit-Differenz, die die RANGFOLGE nicht aendert,
ist gleichgueltig.

Alle **1148** Drafting-Zustaende aus `frozen_eval_set_v2.pkl`, nur legale Aktionen:

| Metrik | Abweichungen | Rate |
| ------ | -----------: | ---: |
| **Argmax** (hoechster Logit unter den legalen Aktionen) | **0 / 1148** | **0,00 %** |
| **Gumbel-Top-16-Menge** (echte Wurzel-Kandidatenziehung, gleicher Seed je Backend) | **0 / 1148** | **0,00 %** |

Logit-Abstaende in Abweichungsfaellen: keine, weil es keine gab.

### Damit ist die vorab festgelegte Deutung eingetreten

Der 0-%-Fall war vorab so festgeschrieben: *"die Toleranzueberschreitung ist
wirkungslos, die 1e-5-Marke ist fuer tract-gegen-torch die falsche Marke, und das
ist dann mit der Wirkung begruendet statt mit dem Wunsch."*

**Die 1e-5-Marke stammt aus dem tract-gegen-tract-Vergleich verschiedener
Batch-Plaene** (`net.rs:820/830/864/875`). Fuer einen Vergleich zweier
verschiedener Inferenz-Maschinerien ist sie nicht die passende Groesse -- die
passende ist die Entscheidungsgleichheit, und die ist 1148 von 1148 gegeben.

**Weg A ist auf der Inferenz-Achse abgenommen.** Nicht abgenommen ist der
Durchsatz -- siehe unten.

### Was GEPRUEFT ist und was RELAYED

Selbst nachgeprueft: die 1148 stimmen mit einer UNABHAENGIGEN Quelle ueberein
(`oracle_v21_own02.json` nennt `n_labeled: 1148`); die m-Formel
(`net_mcts.rs:2456-2461`) gibt fuer 400 Sims tatsaechlich 16. Die 0/1148 selbst ist
die Messung des Agenten, von mir nicht wiederholt.

**Vorbehalt, vom Agenten selbst benannt**: EIN Gumbel-Seed je Zustand, nicht
mehrere. Ueber 1148 Zustaende sind das 1148 unabhaengige Ziehungen, also breite
Abdeckung -- ein Wiederholungslauf je Zustand waere strenger und ist der
naheliegende Nachschlag, falls jemand daran zweifelt.

### Der Durchsatz ist damit NICHT abgenommen -- und das ist der naechste Schritt

Der Kanal deckelt bei **Batch 16** (`EVAL_BATCH_MAX_N`), die gemessene Gewinnzone
beginnt bei **Batch 128**. Ein Test bei 16 wuerde eine garantierte Niederlage
liefern und nichts ueber Weg A aussagen, sondern nur ueber den Deckel: die CPU
macht 1.600-3.200 Evals/s je Faden bei elf Faeden, eine GPU bei Batch 16
amortisiert ihren Kernel-Aufwand ueber zu wenige Elemente.

**Reihenfolge fuer den naechsten Bauschritt**:

1. **Verschraenkung** (§5, bisher ausgeschlossen) -- sie ist das einzige Stueck,
   das Batch 256 erzeugt und damit den gemessenen Vorteil (2,6-5,3x) abruft.
2. **Dann** der Durchsatz-Nachweis: Evals/s ueber den Kanal gegen den tract-Pfad,
   bei dem Batch, den die Verschraenkung tatsaechlich erreicht.
3. **Dann** der Staerke-Nachweis in der Arena, gepaart -- weil der Golden-Hash bei
   eingeschaltetem Kanal strukturell nicht halten kann (§2). Das Kriterium lautet
   gleiche Staerke bei entscheidungsgleicher Inferenz, und die zweite Haelfte davon
   ist mit diesem Abschnitt belegt.
