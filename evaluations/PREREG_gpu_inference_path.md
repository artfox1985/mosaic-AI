<!-- STATUS: ENTSCHIEDEN | Frage: Ueber WELCHEN Pfad erreicht die Rust-Engine die GPU -- Cross-Language-Queue zu Python/torch oder ein CUDA-faehiger Rust-Pfad? | Beleg: ENTSCHIEDEN 2026-08-14 (Datei §23 Regel-3-Endverdikt): keine Zelle erreicht 2,0x gegen den frisch gemessenen staerksten Sync-Arm (528,5 Partien/h bei 11 Faeden); beste Konfiguration = Doppel-Prozess-Aggregat 663,0/h = 1,255x. Weg B (GPU-Inferenzpfad) wird NICHT Standard fuer v22+ -- geschlossen, bis ein groesseres Netz die Kennlinie verschiebt. -->

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


---

## 9. VERDIKT: Weg A ist NICHT gedeckt -- und meine Regel 1 mass die falsche Groesse

### Die Zahlen (Torch-Arm auf CUDA, RTX 3060 geprueft ansprechbar)

| N Faeden | synchron (Evals/s) | verschraenkt + Torch/CUDA | Faktor |
| -------: | -----------------: | ------------------------: | -----: |
| 11 | 4.424,7 | 1.343,5 | **0,30x** |
| 128 | 5.261,3 | 2.874,7 | **0,55x** |

Beide unter 1,0 -- langsamer als synchron. **Regel 3 (§4) verlangt >= 2,0x. Weg A
ist damit nicht gedeckt.**

Der Mechanismus selbst ist einwandfrei: Entscheidungsgleichheit **0 von 1148** in
Argmax und Gumbel-Top-16 (synchron gegen verschraenkt), Paritaets-Hash haelt bei
ausgeschaltetem Knopf, mittlerer Batch 125,90 bei N=128. Er ist nur nichts wert.

### MEIN MESSPLAN-FEHLER, und er ist der eigentliche Befund

Die "sonstige" Zeit je Sammelrunde betraegt bei N=128 **42,39 ms** -- das
**148-fache** des gemessenen IPC-Rundlaufs von 0,287 ms.

**Der Shared-Memory-Kanal ist also nicht der Engpass.** Was dominiert, ist der
Python-seitige Aufwand JE ANFRAGE: Tensor-Bau aus dem mmap-Puffer,
`.to(device)`-Transfer, `torch.cuda.synchronize()`, Socket-Marshalling.

**Regel 1 (§4) fragte, ob der BYTE-Rundlauf unter einem Drittel der GPU-Zeit
liegt.** Genau das wurde gemessen (0,287 ms gegen Schwelle 1,0816 ms, Faktor 3,8),
und daraus habe ich "Weg A ist gedeckt" geschlossen. Die relevante Groesse waere
der GESAMTE Aufwand je Batch gewesen -- Bytes plus Tensor-Bau plus Transfer plus
Synchronisation. Die 3,8x Luft lagen auf der falschen Groesse, und die richtige
liegt bei 148x DANEBEN.

Das ist derselbe Fehlertyp wie die vier Formfehler im Wertungsplatten-Strang: die
Messung war korrekt ausgefuehrt und beantwortete die falsche Frage. Zahlengleichheit
war dort der Alarm; hier waere es die Frage gewesen, ob die gemessene Groesse die
ENTSCHEIDUNGSrelevante ist.

### Was daraus folgt -- der Befund staerkt Weg B

Die drei Kostenposten, die Weg A erledigt haben, existieren bei **Weg B**
(`ort`-Crate mit CUDA-Provider, §3) **nicht**: kein IPC, kein Python, kein
Tensor-Bau aus einem Puffer, keine Prozessgrenze. Der Transfer zur GPU bleibt,
alles andere entfaellt.

Nach §6 Schritt 2 ist Weg B jetzt an der Reihe, und seine Vorbedingung steht dort
schon: **die Kennlinie gilt nicht** -- sie wurde an PyTorch gemessen, nicht an
ORT-CUDA, und muss neu gemessen werden, bevor ein Batch-Startwert begruendet ist.

**Die Verschraenkung bleibt brauchbar und muss nicht neu gebaut werden.** Sie ist
entscheidungsneutral nachgewiesen und liefert den Batch; nur der Verbraucher am
anderen Ende taugt nicht. Ein ORT-CUDA-Pfad wuerde an derselben Stelle
(`Net::eval_batch`) angeschlossen.

### Was NICHT geprueft ist

- Die GPU-Auslastung wurde nur VOR dem Lauf geschnappt (34 %, Desktop-Compositing),
  nicht fortlaufend. Der Agent hat das als Luecke benannt statt sie zu verschweigen.
- Die 148x-Zerlegung ist HERGELEITET (Rundenzeit minus synthetischer Baumarbeit),
  nicht instrumentiert. Welcher der vier Python-Posten wieviel beitraegt, ist offen.
- Der mittlere Batch 125,90 gilt unter GLEICHFOERMIGER synthetischer Last
  (Gleichschritt-Saettigung), nicht fuer heterogenes echtes Self-Play.


---

## 10. WEG B: NICHT MESSBAR -- fehlende CUDA-13-Laufzeit, Nutzer-Entscheidung nötig

### Befund

`ort` v2.0.0-rc.13 (ONNX Runtime 1.28) wurde als OPTIONALE Abhängigkeit
hinzugefügt (`engine/Cargo.toml`, Feature `ort_cuda_probe`, `required-features` am
neuen Beispiel `engine/examples/ort_cuda_batch_probe.rs`). `cargo test --lib` ohne
das Feature: **378 bestanden / 18 ignoriert**, keine Regression.

Der CUDA-Execution-Provider liess sich **nicht registrieren**:
`onnxruntime_providers_cuda.dll` verlangt `cublasLt64_13.dll`, also die
**CUDA-13-Laufzeit**. Auf dem Rechner ist kein CUDA-Toolkit installiert (kein
`CUDA_PATH`, kein `nvcc`, kein Toolkit-Ordner -- geprüft in `System32`, allen
`PATH`-Ordnern und `Program Files`). Das mitgelieferte `torch 2.12.0+cu126` bringt
CUDA-**12**-Bibliotheken, deren Namensschema nicht passt; das Python-`onnxruntime`
(1.27.0) hat nur den CPU-Provider.

**Kein Ersatzlauf auf dem CPU-Provider** -- `error_on_failure()` wurde explizit
gesetzt, damit der stille ORT-Fallback nicht greift, und das Programm bricht ab.
Es gibt keine Zahl und keine JSON. Das ist genau richtig: eine ORT-CPU-Kennlinie
wäre so wertlos wie der Torch-CPU-Lauf, an dem Weg A zuerst scheinbar scheiterte
(§9).

### Regel 2 und Regel 3 sind nicht anwendbar

Kein Zähler vorhanden. Der Vergleich ORT-CUDA gegen torch bei Batch 140-590
(41.959 / 78.896 Evals/s laut `gpu_batch_throughput.json`) kann nicht gezogen
werden.

### NUTZER-ENTSCHEIDUNG

Was fehlt, ist eine **Systeminstallation**, keine Repo-Änderung: CUDA-13-Toolkit-
Laufzeit (`cudart64_13.dll`, `cublas64_13.dll`, `cublasLt64_13.dll`) plus passendes
cuDNN. Alternativ ein `ort`-Build gegen CUDA 12, falls es einen gibt -- nicht
geprüft.

Ohne diese Installation ist Weg B nicht messbar und damit auch nicht
entscheidbar. **Beide Wege zur GPU sind damit blockiert**: Weg A gemessen
ungedeckt (§9), Weg B nicht messbar (hier).

### DOKUMENTATIONSLÜCKE in §9 -- vom Agenten aufgedeckt

Die dort genannten Durchsatzzahlen (synchron 4.424,7 bzw. 5.261,3 Evals/s;
Faktoren 0,30x und 0,55x) stammen aus der **stdout-Ausgabe** des Tests
`interleaved_throughput_vs_synchronous` und sind **in keiner Datei persistiert** --
`grep` über `evaluations/*.json` findet sie nicht. Sie sind damit nicht
nachprüfbar, ohne den Test erneut zu fahren.

Zuordnung geklärt: der "synchrone" Arm läuft bei ausgeschaltetem Knopf über
`net.eval` und damit über **tract-CPU** -- das Etikett in §9 ist korrekt, der
Zweifel des Agenten daran ist ausgeräumt. Aber die Zahl gehört in eine JSON, und
der Test schreibt keine. **Nachzuziehen, wenn der Test das nächste Mal läuft.**

Dieselbe Lehre wie beim veralteten Index (`STATUS.md`, Übergabe-Block): eine
tragende Zahl, die nur in einem Bericht steht, ist für den Nachfolger nicht
vorhanden.

---

## 11. WEG B: MESSBAR MIT VERSIONS-PIN -- Kennlinie liegt vor

### Der Versions-Pin, mit Quelle

`ort` v2.0.0-rc.13 bündelt ONNX Runtime 1.28.0 und bietet für
`x86_64-pc-windows-msvc` nur noch einen `cuda13`-Build (CUDA-13-Laufzeit) --
GEPRÜFT: `ort-sys`s eingebettete `build/download/dist.tsv`, aus dem
crates.io-Tarball extrahiert. **`ort` v2.0.0-rc.12** bündelt ONNX Runtime
1.24.2 und bietet dort noch einen **`cu12`**-Build (Quelle:
`ort-sys-2.0.0-rc.12/build/download/dist.txt`, Zeile 2:
`cu12	x86_64-pc-windows-msvc	https://cdn.pyke.io/0/pyke:ort-rs/ms@1.24.2/...+cu12.tar.lzma2`).
rc.12 ist die NEUESTE `ort`-Version mit einem Windows-cu12-Build -- rc.11
(ONNX Runtime 1.23.2) hat ihn auch noch, rc.13 nicht mehr. Auf `=2.0.0-rc.12`
gepinnt, zusätzlich `ORT_CUDA_VERSION=12` gesetzt (statt der
Auto-Erkennung zu vertrauen, die laut `resolve.rs` ohnehin auf `cu12`
zurückfällt, wenn kein `CUDA_HOME`/`nvcc` gefunden wird).

Torch-DLLs aus
`<USER>\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\torch\lib`
(cudart64_12, cublas64_12, cublasLt64_12, cudnn64_9 + 5 weitere cudnn-Teile,
cufft64_11, curand64_10, nvJitLink_120_0, nvrtc64_120_0 -- 19 Dateien) neben
die Beispiel-`.exe` kopiert, dieselbe Technik wie schon für die
Provider-DLLs (`copy-dylibs` erreicht `target/.../examples/` ohne
Windows-Entwicklermodus nicht, siehe §10). **Kein Systemeingriff, keine
Repo-Änderung** -- reine Dateikopie in den Scratch-Zielordner.

Ergebnis: **CUDA-Execution-Provider registriert sich, Modell lädt, volle
Kennlinie gemessen.** `error_on_failure()` blieb gesetzt; es gab diesmal
keinen Fehler, auf den er hätte reagieren müssen.

### Die Kennlinie -- VOLLE Zeit je Batch (Merkmalspuffer -> Tensor -> `run` -> `Vec<f32>`)

Zwei Läufe (derselbe Build, dieselben DLLs) zur Streubreiten-Einordnung:
Lauf 2 ist der in `evaluations/ort_cuda_batch_throughput.json` persistierte
(korrekte Versions-Metadaten; Lauf 1 hatte einen Anzeige-Fehler -- Quelltext
sagte fälschlich "rc.13"/"1.28", behoben vor Lauf 2).

| Batch | Lauf 1 (Evals/s) | Lauf 2 (Evals/s, persistiert) | Torch/CUDA (`gpu_batch_throughput.json`) |
| ----: | ---------------: | -----------------------------: | ----------------------------------------: |
|     1 |             760,4 |                          901,7 |                                     125,7 |
|     2 |             735,2 |                        1.358,1 |                                     275,7 |
|     4 |           2.564,2 |                        2.701,2 |                                     672,1 |
|     8 |           5.327,1 |                        5.029,6 |                                   1.585,4 |
|    11 |           8.580,0 |                        6.851,5 |                                   2.581,2 |
|    16 |           9.228,9 |                       12.851,0 |                                   4.538,6 |
|    22 |          14.183,6 |                       13.283,8 |                                   6.196,9 |
|    32 |          21.184,9 |                       19.069,3 |                                   8.407,4 |
|    44 |          29.432,1 |                       16.008,6 |                                  14.059,7 |
|    64 |          41.926,2 |                       36.625,7 |                                  20.863,3 |
|   128 |          51.292,8 |                       61.396,8 |                                  41.959,3 |
|   256 |          74.565,5 |                       77.770,4 |                                  78.896,5 |
|   512 |          79.336,0 |                       82.030,9 |                                 162.635,3 |

Streubreite zwischen Lauf 1/2 bei kleinen/mittleren Batches teils groß (z.B.
Batch 44: 29.432 vs. 16.008, -46 %) -- ungeklärt, ob GPU-Zustand
(Desktop-Compositing, Thermik) oder ORT-interne Heuristik-Neubewertung
(`ConvAlgorithmSearch::Exhaustive` ist Default). NICHT weiter zerlegt in
dieser Sitzung. Bei Batch 128/256/512 ist die Differenz deutlich kleiner
(±20 % bzw. ±4 % bzw. ±3 %).

### Regel 2 (§4) -- ORT-CUDA gegen Torch bei Batch 140-590

Kein gemessener Punkt liegt exakt in [140, 590]; 256 liegt darin, 128 und 512
grenzen das Fenster ein (dieselbe Wahl wie in `gpu_batch_throughput.json`
selbst dokumentiert):

| Batch | ORT-CUDA (Lauf 2) | Torch/CUDA | Verhältnis ORT/Torch |
| ----: | -----------------: | ---------: | --------------------: |
|   128 |            61.396,8 |   41.959,3 |                 1,464 |
|   256 |            77.770,4 |   78.896,5 |                 0,986 |
|   512 |            82.030,9 |  162.635,3 |                 0,504 |

Am einzigen Punkt INNERHALB des Fensters (256) liegt ORT-CUDA knapp unter
Torch (-1,4 %, in Lauf 1 -5,5 %) -- in beiden Läufen unter, nicht über
Torch, also kein Rauschartefakt in eine zufällige Richtung. Am unteren
Rand (128) liegt ORT-CUDA klar vorn; am oberen Rand (512, knapp außerhalb)
fällt ORT-CUDA auf gut die Hälfte von Torch zurück -- die ORT-CUDA-Kurve
flacht zwischen 256 und 512 fast ab, während Torch zwischen denselben
Punkten noch einmal mehr als verdoppelt. Kein Urteil hier: die Zahlen liegen
vor, Regel 2 wendet der Nutzer an.

### Regel 3 (§4) -- Faktor gegen den tract-CPU-Bezug

Bezug: §9/§10 "synchron" (4.424,7 Evals/s bei N=11, 5.261,3 bei N=128) --
Etikett vom Nutzer als tract-CPU (`net.eval`) bestätigt (§10). Diese Zahl ist
laut §10 in KEINER JSON persistiert und wurde in dieser Sitzung nicht durch
eine eigene Dateiquelle nachgeprüft, sondern als geprüfte Aussage des Nutzers
übernommen -- markiert, nicht selbst verifiziert.

| ORT-CUDA-Punkt | Faktor gg. N=11 (4.424,7) | Faktor gg. N=128 (5.261,3) |
| -------------: | -------------------------: | ---------------------------: |
|      128 (61.396,8) |                      13,9x |                        11,7x |
|      256 (77.770,4) |                      17,6x |                        14,8x |
|      512 (82.030,9) |                      18,5x |                        15,6x |

Alle sechs Kombinationen liegen weit über der 2,0x-Schwelle -- robust gegen
die Wahl des Bezugs (N=11 vs. N=128) UND gegen die Streubreite zwischen
Lauf 1/2. Regel 3 ist unter jeder vertretbaren Bezugswahl klar erfüllt.

### GPU-Belegung

Vorher (Lauf 2): 28 %, 1.520 MiB, 21,6 W. Nachher: 40 %, 1.526 MiB, 22,0 W.
Fortlaufend mitgeschnitten (`nvidia-smi -l 1`): Spitzenwert während des Laufs
1.703 MiB Speicher (+~180 MiB ggü. Grundlast) und 56,1 W (ggü. ~22 W
Grundlast) -- echte GPU-Rechenlast, kein Leerlauf-Artefakt. Kein anderer
Compute-Prozess auf der GPU (`nvidia-smi --query-compute-apps` vorher/nachher
geprüft, nur Desktop-/Shell-Prozesse ohne Speicherbelegung).

### Eigene Entscheidungen (nicht vorgegeben)

- rc.12 statt rc.11 gewählt (beide bieten `cu12`): rc.12 ist neuer/näher an
  rc.13s API, kein Unterschied in den `Session`/`ep::CUDA`-Signaturen beim
  Umstieg nötig gewesen.
- `ORT_CUDA_VERSION=12` explizit gesetzt statt auf die Auto-Erkennung zu
  vertrauen (auch wenn diese hier ohnehin `cu12` geraten hätte).
- Torch-DLL-Liste um 8 Dateien über die vom Nutzer genannten hinaus erweitert
  (`cudnn_engines_runtime_compiled64_9.dll`, `cudnn_graph64_9.dll`,
  `cudnn_heuristic64_9.dll`, `cudnn_ops64_9.dll`, `nvJitLink_120_0.dll`,
  `nvToolsExt64_1.dll`, `nvrtc-builtins64_126.dll`, `nvrtc64_120_0(.alt).dll`)
  -- Vorsicht gegen eine zweite Kette fehlender Abhängigkeiten wie beim
  `cublasLt`-Fund in §10.
- Nach dem Fund des Anzeige-Fehlers (Quelltext nannte nach dem Versionswechsel
  weiter "rc.13"/"1.28") den Lauf wiederholt, statt die persistierte JSON mit
  falschen Metadaten stehen zu lassen.

---

## 12. VERDRAHTUNG (Schritt 1) UND ENTSCHEIDUNGSGLEICHHEIT DRITTES BACKEND (Schritt 2)

Nutzer-Auftrag "fang an" (2026-08-12): Regel 3 gilt als erfüllt (7,0x-18,5x,
vom Nutzer selbst nachgeprüft). Die ersten zwei Bauschritte, nicht mehr.

### Schritt 1: ORT-CUDA in `Net::eval_batch` eingehängt

Neues Modul `engine/src/net_ort.rs` (`#![cfg(feature = "ort_cuda_probe")]`,
`mod net_ort;` in `lib.rs` ebenso gated), eingehängt in `net.rs::eval_batch`
GENAU an der Stelle, an der schon der Torch/IPC-Knopf hängt. Rangfolge, im
Modulkommentar von `net_ort.rs` UND als Inline-Kommentar in `net.rs::eval_batch`
festgehalten:

1. **ORT-CUDA** (`MOSAIC_ORT_CUDA_ENABLED=1`, nur wirksam mit
   `--features ort_cuda_probe` gebaut) -- ZUERST geprüft.
2. **Torch/IPC** (`MOSAIC_TORCH_IPC_ENABLED=1`, `net_ipc.rs`) -- NUR falls (1)
   erfolglos. Bleibt stehen (nicht entfernt), verdeckt Weg B aber nicht, weil
   im Code NACH ihm geprüft.
3. **tract** -- immer letzter Fallback, nie abschaltbar.

Bei (1)/(2) aus (Default): byte-identisches Bestandsverhalten, `net_ort` wird
nicht einmal betreten.

**Session/Umgebung**: EINE `ort::session::Session` je `Net`-Instanz, in einer
nach Zeiger-Identität schlüsselnden Registry (`net_ort::SESSIONS`) -- exakt
dasselbe Muster wie `net_batcher::REGISTRY`/`ensure_batcher_for` (dortige
Begründung "sicher, weil dieselbe `Net`-Instanz für die gesamte Laufzeit lebt"
gilt hier unverändert). ONNX Runtime braucht (anders als tracts feste
Batch=N-Pläne) KEINE Pläne je Batchgröße -- eine Session bedient jede
Batchgröße symbolisch (schon in `ort_cuda_batch_probe.rs` so genutzt, Batch
1..512 mit EINER Session). Thread-Sicherheit: `Session::run` verlangt in der
`ort`-Rust-API `&mut self` (obwohl `Session` selbst `unsafe impl Send + Sync`
ist, GEPRÜFT in `ort-2.0.0-rc.12/src/session/mod.rs:675-676`) -- deshalb
`Mutex<Session>` je Slot. Der äußere Registry-Mutex wird nur für die
Kartensuche/den Erstaufbau gehalten, nicht während `run()` -- verschiedene
`Net`-Instanzen blockieren sich beim Inferieren nicht gegenseitig.

**Fallback**: jeder Fehler (Session-Aufbau, Tensor-Bau, `run`, Extraktion)
liefert `Err(String)`, NIE Panic -- Aufrufer fällt weiter auf Schritt 2/3
zurück, Warnung einmal je Prozess (`warn_ort_cuda_fallback_once`).
`error_on_failure()` beim CUDA-Provider bleibt ABSICHTLICH gesetzt: ohne sie
würde `ort` bei nicht registrierbarem CUDA-Provider intern still auf seinen
EIGENEN CPU-Provider zurückfallen -- ein zweiter, nutzloser CPU-Pfad, der sich
als "ORT-CUDA" ausgibt. Mit ihr entscheidet UNSER Code, dass tract der
richtige Fallback ist.

`Net` bekam ein additives Feld `onnx_path: String` (Weg B braucht den Pfad
außerhalb von tract, das ihn nirgends vorhält) -- `load`/`load_auto` reichen
ihn durch, kein bestehender Aufrufer betroffen. `split_batch_n`/
`split_planes_flat_batch` von `net.rs` auf `pub(crate)` angehoben (Weg B
nutzt dieselbe Zeilen-Split-Logik wie der tract-Pfad, keine zweite
Implementierung).

`cargo test --lib --release --features ort_cuda_probe`: **380 bestanden / 20
ignoriert** (378+2 neue Unit-Tests, 18+1 neuer `#[ignore]`-Test). Ohne das
Feature: unverändert **378 bestanden / 18 ignoriert**.

### Schritt 2: Entscheidungsgleichheit tract<->ORT-CUDA (DRITTES Backend)

Neuer Test `net_mcts::tests::ort_cuda_matches_tract_gumbel_root_selection`
(`#[cfg(feature = "ort_cuda_probe")]` + `#[ignore]`), dieselbe Messkette wie
`policy_head_deviation_effect_on_gumbel_root_selection` (tract<->torch) und
`interleaved_matches_synchronous_gumbel_root_selection` (synchron<->
verschränkt) -- dieselben 1148 Zustände, dasselbe Modell
`alphazero_v20_2d_opp_brierbest.onnx`, PLUS max. Rohwert-Abweichung je Kopf
(wie `net_ipc`s Toleranztest).

**GEMESSEN (`cargo test --release --lib --features ort_cuda_probe -- --ignored
--exact net_mcts::tests::ort_cuda_matches_tract_gumbel_root_selection
--nocapture`, `MOSAIC_FROZEN_STATES_JSON` aus
`tools/export_frozen_drafting_states.py --set evaluations/frozen_eval_set_v2.pkl`,
Gegenprobe 1148 bestanden):**

| Metrik | Abweichungen | Rate |
| ------ | -----------: | ---: |
| Argmax (rauschfrei) | 0 / 1148 | 0,00 % |
| **Gumbel-Top-16-Menge** | **16 / 1148** | **1,39 %** |

Zum Vergleich tract<->torch (§8): Argmax 0/1148, Top-16 0/1148 -- ORT-CUDA
weicht dort ab, wo torch es nicht tat. **NICHT toleranzangepasst, NICHT
weginterpretiert -- das ist der Befund.** Plausible, aber UNGEPRÜFTE
Erklärung: ORT-CUDA ist sowohl ein anderer Graph-Optimierer (ORT statt tract
ODER torch) ALS AUCH eine andere Hardware-Klasse (GPU statt CPU) ggü. BEIDEN
Vergleichspartnern -- zwei Abweichungsquellen statt einer.

Max. Rohwert-Abweichung je Kopf (tract vs. ORT-CUDA), zum Vergleich tract vs.
torch (§7) danebengestellt:

| Kopf | tract<->ORT-CUDA | tract<->torch (§7) |
| ---- | ---------------: | ------------------: |
| policy | 0,01745224 | 0,00003433 |
| value | 0,00153267 | 0,00000048 |
| moon | 0,00084567 | 0,00000131 |
| points | 0,00048220 | 0,00000051 |

ALLE vier Köpfe weichen bei ORT-CUDA um 2-3 Größenordnungen mehr ab als bei
torch -- konsistent mit der Zwei-Abweichungsquellen-Erklärung oben, aber das
ist eine HERLEITUNG, keine Messung der Ursache selbst.

GPU-Belegung waehrend des Tests: Spitzenwert 1.720 MiB (+~150-190 MiB ggü.
Grundlast), 43,7 W (ggü. ~21-22 W Grundlast) -- echte Rechenlast, kein
Leerlauf-Artefakt.

### Was das NICHT bedeutet -- und der nächste Schritt (Nutzer-Entscheidung)

Die 1,39 % Top-16-Abweichung ist eine WIRKUNGSMESSUNG auf der
Kandidatenmengen-Ebene, KEINE Aussage über die Suchstärke selbst -- ob eine
andere Top-16-Menge an der Wurzel die tatsächliche Zugwahl/Elo bewegt, ist
Schritt 3/4 (Selfplay-Durchsatz, Arena), ausdrücklich NICHT Teil dieses
Auftrags. Kein Urteil hier -- die Zahl liegt vor.

### Eigene Entscheidungen (nicht vorgegeben)

- `InputLayout::Planes` (reiner Rang-4-Einzel-Input) im ORT-Pfad NICHT
  unterstützt (klarer `Err` statt Vermutung über einen ungeprüften
  Eingabenamen) -- kein `export_onnx.py`-Zweig erzeugt dieses Layout,
  GEPRÜFT (nur zwei `input_names`-Stellen dort).
- Ausgaben per INDEX (`outputs[0..3]`) statt per Name gelesen -- gleiche
  Annahme wie der tract-Pfad, für identische Verträge zwischen den Backends.
- Registry-Erstaufbau haelt den äußeren Mutex ueber die GESAMTE
  Session-Konstruktion (kein Doppel-Check-Locking) -- einfacher, für den
  seltenen Fall (Aufbau einmal je `Net`-Instanz) ausreichend, exakt das
  Muster von `net_batcher::ensure_batcher_for`.
- Device-ID fest auf 0 (keine eigene Env-Var) -- einzige GPU auf der
  Zielumgebung, außerhalb des engen Auftrags-Zuschnitts.
- Für den Test-Lauf dieselbe Handkopie-Technik (Provider- + Torch-CUDA-12-
  DLLs neben das Testbinary, `target/.../release/deps/`) wie beim
  Kennlinien-Beispiel -- keine neue Lösung erfunden.

---

## 13. TF32-VERDACHT: BESTÄTIGT ALS HAUPTURSACHE, ABER NICHT VOLLSTÄNDIG -- Kennlinie fast unverändert

Nutzer-Auftrag 2026-08-12, vor dem Arena-Lauf geprüft: die 500-fache
Policy-Abweichung (§12: 0,01745 gg. 0,00003 bei torch) sei zu groß für
gewöhnliche Graph-Optimierer-Unterschiede und passe zu TF32 auf Ampere.

### (1) Die Option, mit Fundstelle

`ort::ep::CUDA::with_tf32(bool)`, Provider-Option `use_tf32` -- GEPRÜFT:
`ort-2.0.0-rc.12/src/ep/cuda.rs:276-297`. Dokumentierter Default: **"This
option is disabled by default."** (Zeile 281). Das ist die Behauptung der
`ort`-Rust-Bindung selbst (Doc-Kommentar im Quelltext dieser Version), NICHT
unabhängig gegen den ONNX-Runtime-C++-Quelltext (der hier nicht vorliegt)
geprüft -- diese Einschränkung ausdrücklich markiert, nicht verschwiegen.
Bis Schritt 1 (§12) hatte `net_ort.rs::build_session` `with_tf32` nie
aufgerufen, lief also auf diesem (laut Doku bereits ausgeschalteten) Default.

### (2) Entscheidungsgleichheit mit `with_tf32(false)` explizit gesetzt

`net_ort.rs::build_session`: `CUDA::default().with_device_id(0).with_tf32(false)...`
-- doppelte Absicherung statt sich auf den dokumentierten Default zu
verlassen. Derselbe Test wie in §12
(`net_mcts::tests::ort_cuda_matches_tract_gumbel_root_selection`, 1148
Zustände, `alphazero_v20_2d_opp_brierbest.onnx`), erneut gefahren:

| Metrik | vorher (§12, TF32 auf ORT-Default) | jetzt (`with_tf32(false)`) |
| ------ | ----------------------------------: | ---------------------------: |
| Argmax | 0 / 1148 (0,00 %) | 0 / 1148 (0,00 %) |
| **Gumbel-Top-16-Menge** | **16 / 1148 (1,39 %)** | **1 / 1148 (0,09 %)** |

Max. Rohwert-Abweichung je Kopf:

| Kopf | vorher (§12) | jetzt | Faktor | tract<->torch (§7, Referenz) |
| ---- | ------------: | ----: | -----: | -----------------------------: |
| policy | 0,01745224 | 0,00003815 | 457x kleiner | 0,00003433 |
| value | 0,00153267 | 0,00000232 | 660x kleiner | 0,00000048 |
| moon | 0,00084567 | 0,00000125 | 677x kleiner | 0,00000131 |
| points | 0,00048220 | 0,00000077 | 626x kleiner | 0,00000077 |

GPU-Belegung: Spitzenwert 1.721 MiB (+~150 MiB), 44,3 W (ggü. ~22 W
Grundlast) -- echte Rechenlast.

### DER BEFUND, UNGESCHÖNT: TF32 ist die Hauptursache, aber NICHT die
### vollständige Erklärung

Alle vier Köpfe fallen auf tract<->torch-Größenordnung zurück (moon/points
sogar auf dieselbe Zahl) -- das bestätigt den Verdacht klar UND deutlich.
**Aber die Gumbel-Top-16-Abweichung geht auf 1/1148 zurück, NICHT auf 0/1148.**
Weder auf 0 gerundet noch als "im Rauschen" verworfen -- eine einzelne
Zustands-Abweichung bleibt, mit ausgeschaltetem TF32, ungeklärt. NICHT weiter
untersucht (welcher der 1148 Zustände, wieso genau dieser) -- außerhalb des
Auftrags-Zuschnitts ("nicht weiter suchen" galt für den Fall "bleiben
unverändert"; dieser Fall hier -- 16→1 -- ist keiner der beiden vorab
entschiedenen Äste, deshalb hier so stehen gelassen statt in einen der beiden
gepresst).

### (3) Kennlinie neu gemessen mit `with_tf32(false)`

Gleiches Modell/gleiche Batch-Punkte wie §11, JSON
`evaluations/ort_cuda_batch_throughput_tf32off.json` (§11s Datei bleibt
unangetastet):

| Batch | TF32 aus (Evals/s) | TF32 auf ORT-Default (§11, Lauf 2) | Torch/CUDA |
| ----: | -------------------: | -----------------------------------: | -----------: |
|   128 |             54.926,2 |                             61.396,8 |     41.959,3 |
|   256 |             76.305,3 |                             77.770,4 |     78.896,5 |
|   512 |             92.892,6 |                             82.030,9 |    162.635,3 |

**Kaum verändert** -- die Differenzen liegen in derselben Größenordnung wie
die bereits in §11 dokumentierte Lauf-zu-Lauf-Streuung (dort z.B. Batch 44:
-46 % zwischen zwei Läufen desselben Zustands). Bei 512 ist der TF32-aus-Lauf
sogar SCHNELLER als der TF32-Default-Lauf -- kein Hinweis auf einen
systematischen Verlangsamungs-Trend durch das Abschalten, für DIESES kleine
Modell bei diesen Batchgrößen. GPU-Belegung: Spitzenwert 1.720 MiB, 62,0 W
(höher als beim TF32-Default-Lauf in §11 -- passt zur Erwartung "mehr
Rechenaufwand ohne TF32-Abkürzung", auch wenn sich das hier nicht in
niedrigerem Durchsatz niederschlägt).

### Regel 2 (§4), neu mit `with_tf32(false)`

| Batch | ORT-CUDA (TF32 aus) | Torch/CUDA | Verhältnis |
| ----: | --------------------: | -----------: | ----------: |
|   128 |             54.926,2 |     41.959,3 |       1,309 |
|   256 |             76.305,3 |     78.896,5 |       0,967 |
|   512 |             92.892,6 |    162.635,3 |       0,571 |

Gleiches Muster wie in §11: am unteren Rand (128) vorn, am einzigen Punkt
INNERHALB des Fensters (256) knapp darunter, am oberen Rand (512) deutlich
darunter. Kein Urteil hier.

### Regel 3 (§4), neu mit `with_tf32(false)`

Bezug 5.261,3 Evals/s (N=128, §9/§10, Etikett vom Nutzer bestätigt) bzw.
4.424,7 (N=11):

| ORT-CUDA-Punkt (TF32 aus) | Faktor gg. N=128 (5.261,3) | Faktor gg. N=11 (4.424,7) |
| --------------------------: | ---------------------------: | ---------------------------: |
|          128 (54.926,2) |                       10,4x |                       12,4x |
|          256 (76.305,3) |                       14,5x |                       17,2x |
|          512 (92.892,6) |                       17,7x |                       21,0x |

Weiterhin weit über der 2,0x-Schwelle bei jeder Bezugswahl -- die
"Luft" (7,0x-15,6x in §12) bleibt praktisch erhalten (jetzt 10,4x-21,0x, eher
etwas GRÖSSER als kleiner).

### Eigene Entscheidungen (nicht vorgegeben)

- `with_tf32(false)` fest in `net_ort.rs::build_session` verdrahtet (kein
  eigener Knopf) -- Ergebnisgleichheit mit tract ist der Zweck dieses
  Backends, nicht der letzte Prozentpunkt Durchsatz.
- Dieselbe Änderung auch im Kennlinien-Beispiel (`ort_cuda_batch_probe.rs`)
  nachgezogen, damit Produktionscode und Messwerkzeug denselben Zustand
  messen -- sonst wäre die Kennlinie für den jetzt verdrahteten Code nicht
  mehr repräsentativ.
- Neue JSON-Datei statt Überschreiben der §11-Datei -- beide Messpunkte
  bleiben nachvollziehbar nebeneinander.
- Die verbleibende 1/1148-Abweichung NICHT in einen der beiden
  vorgegebenen Äste ("verschwinden" / "bleiben") gepresst, sondern als
  eigener, unvollständig geklärter Zwischenbefund stehen gelassen.

---

## 14. DER EINE ABWEICHENDE ZUSTAND -- vier Zahlen, keine Deutung

Nutzer-Auftrag 2026-08-12: nur der eine verbleibende Zustand aus §13
(1/1148 mit `with_tf32(false)`). Neuer Test
`net_mcts::tests::ort_cuda_single_deviation_gap_diagnostic`, GEMESSEN
(`cargo test --release --lib --features ort_cuda_probe -- --ignored --exact
net_mcts::tests::ort_cuda_single_deviation_gap_diagnostic --nocapture`,
dieselben 1148 Zustände, dasselbe Modell wie §12/§13).

**(1) Welcher Zustand**: `record_index=320`, Runde 4, 130 Kandidaten nach
Moon-Expansion (`n_root`).

**(2) An welcher Stelle**: exakt der 16. Platz (`m_prime=16`, der volle
Schnitt bei 400 Sims) -- nicht weiter vorne. Die Aktion, die bei ORT-CUDA
herausfällt: `Stone(Move { take: TakeAction { source: SmallFactoryMoon,
color: Gelb, ... }, place: PlaceAction { row_index: 1 } })` (Rang tract=16,
Rang ORT-CUDA=40). Die Aktion, die neu hereinkommt: `Stone(Move { take:
TakeAction { source: SmallFactorySun, color: Gelb, factory_id: Some(3),
moon_order: [Rot, Schwarz, Blau] }, place: PlaceAction { row_index: 1 } })`
(Rang tract=40, Rang ORT-CUDA=16).

**(3) Der Abstand, in beiden Backends** (Rang-16-Score minus Rang-17-Score,
jeweils in der eigenen Rangfolge des Backends):

| Backend | Rang-16-Score | Rang-17-Score | Abstand |
| ------- | -------------: | -------------: | -------: |
| tract | -3,473041 | -3,634069 | 0,161028 |
| ORT-CUDA | -3,473037 | -3,634073 | 0,161035 |

**(4) Verteilung dieses Abstands über die 1147 NICHT abweichenden Zustände**
(tracts eigener Rang-16/17-Abstand, `n=454` mit echtem Schnitt --
693 der 1148 hatten `m_prime>=n_root`, also keinen echten Schnitt, und sind
hier nicht Teil der Verteilung):

| | Wert |
| --- | ---: |
| Median | 0,150264 |
| 10 %-Quantil | 0,018741 |

Der abweichende Zustand (0,161028 bei tract) liegt oberhalb des Medians der
Nicht-Abweichenden und weit oberhalb des 10 %-Quantils. Keine weitere Deutung
hier -- der Nutzer entscheidet.

GPU-Belegung während des Diagnoselaufs: Spitzenwert 1.682 MiB, 44,4 W (ggü.
~22 W Grundlast).

### Eigene Entscheidungen (nicht vorgegeben)

- Zustände ohne echten Schnitt (`m_prime>=n_root`, alle Kandidaten passen
  ohnehin in die Top-m) aus der Verteilung in Punkt 4 ausgeschlossen -- für
  sie existiert keine "16./17. Stelle", ein Abstand wäre dort nicht definiert.
  693 von 1148 Zuständen betroffen (n_root oft klein an spät-Runden-Zuständen
  mit wenig verbleibenden Optionen).
- Der Populationsabstand in Punkt 4 nutzt **tracts** eigene Rangfolge als
  durchgehende Referenzgröße (nicht ORT-CUDAs), weil tract der Bezug in der
  gesamten übrigen PREREG-Untersuchung ist -- für den einen abweichenden
  Zustand werden trotzdem BEIDE Backend-Abstände berichtet (Punkt 3), wie
  verlangt.
- Neuer Hilfs-Helfer `gumbel_scored_sorted` (net_mcts.rs) statt
  `gumbel_topm_set` wiederzuverwenden -- Letzterer kürzt intern auf
  `m_prime` und gibt keine Ränge/Scores zurück, für die Rang-Diagnose wird
  die VOLLE sortierte Liste gebraucht. Gleiche RNG-Verbrauchsreihenfolge wie
  `gumbel_topm_set`, damit beide für denselben Seed identische erste
  `m_prime` Einträge liefern.

---

## 15. ZUORDNUNGS-HYPOTHESE BESTÄTIGT -- der 24-Rangsprung ist ein Zuordnungs-, kein Präzisionsartefakt

Nutzer-Auftrag 2026-08-12 ("meine Erwartung widerlegt... genau deshalb ist
die Spannung jetzt sichtbar"): Codefrage plus gezielte Prüfung am einen
Zustand aus §14, keine Reparatur.

### (1) Wie die Gumbel-Zufallszahlen zugeordnet werden

`net_mcts.rs:3719-3728` (`build_gumbel_tree_inner`, Produktionscode):

```rust
let mut scored: Vec<(f64, f64, usize)> = nodes[0]
    .untried
    .iter()
    .enumerate()
    .map(|(i, &(_, p))| {
        let g = if add_root_noise { sample_gumbel(rng) } else { 0.0 };
        (g + (p as f64).max(1e-9).ln(), g, i)
    })
    .collect();
```

EINE Ziehung je Kandidat, **in Aufzählungsreihenfolge von `nodes[0].untried`**
(`.enumerate()`), NICHT deterministisch an einer Aktions-ID/-Identität
festgemacht. Welche Zufallszahl eine Aktion bekommt, hängt an ihrer
LISTENPOSITION zum Ziehzeitpunkt, nicht an der Aktion selbst.

### (2) Ist die Aufzählungsreihenfolge prior-abhängig? JA

`net_mcts.rs:1800` (`build_untried_actions`):

```rust
acts.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
```

`acts` (→ `nodes[0].untried` via `make_node`, GEPRÜFT: `net_mcts.rs:2291`
`build_untried_actions(&state, &logits, &moon_scores, skip_cutoff)` liefert
direkt die `untried`-Belegung) wird nach **Prior absteigend** sortiert --
`.1` ist der Prior-Float `p` aus der Netz-Policy. Damit bestimmt der
(backend-abhängige) Policy-Kopf direkt die Listenposition und damit die
Gumbel-Zuordnung.

### (3) Hypothese bestätigt -- belegt am Zustand `record_index=320`

| | Position in `acts_t` | Position in `acts_o` |
| --- | ---: | ---: |
| SmallFactoryMoon (Gelb, Reihe 1) | 35 | 36 |
| SmallFactorySun (Gelb, Fabrik 3, Rot/Schwarz/Blau, Reihe 1) | 36 | 35 |

Die Aufzählungsreihenfolge unterscheidet sich -- die beiden Aktionen tauschen
GENAU EINEN benachbarten Listenplatz (35↔36).

| | tract: Rang / Score / g / ln(prior) | ORT-CUDA: Rang / Score / g / ln(prior) |
| --- | --- | --- |
| SmallFactoryMoon | 16 / -3,473041 / **2,666478** / -6,139518 | 40 / -5,827941 / **0,311575** / -6,139516 |
| SmallFactorySun | 40 / -5,827945 / **0,311575** / -6,139520 | 16 / -3,473037 / **2,666478** / -6,139515 |

Die beiden Aktionen bekommen **exakt vertauschte** Gumbel-Zahlen
(2,666478 und 0,311575 tauschen komplett die Seiten) -- weil sie beim Ziehen
ihre Listenplätze getauscht haben. `ln(prior)` bewegt sich dabei nur um
~2e-6 zwischen den Backends (beide Aktionen liegen mit `ln(prior)≈-6,1395`
ohnehin fast exakt gleich) -- die ~2,35 Punkte Score-Differenz stammen fast
vollständig aus `g`, nicht aus `ln(prior)`.

**Damit ist die Hypothese bestätigt**: der 24-Rangsprung ist ein
Zuordnungsartefakt (welche Zufallszahl eine Aktion bekommt, hängt an ihrer
Listenposition, nicht an ihrer Identität), kein Präzisionsartefakt (die
zugrunde liegenden Prior-Werte selbst unterscheiden sich kaum). Keine
weitere Deutung, ob das für die Abnahme akzeptabel ist.

### (4) Betrifft dasselbe auch synchron-gegen-verschränkt?

Codelich: JA, dieselbe Zuordnung. `interleaved_matches_synchronous_gumbel_root_selection`
(`net_mcts.rs:8776`) ruft an den Zeilen 8898-8899/8907-8908 exakt dieselben
zwei Funktionen (`build_untried_actions` + `gumbel_topm_set`) auf wie der
hier untersuchte Vergleich -- derselbe Mechanismus, dieselbe
Listenpositions-Abhängigkeit. GEPRÜFT ist hier nur die Code-IDENTITÄT der
Zuordnungsfunktion, NICHT erneut gemessen, ob dieser Mechanismus im
synchron/verschränkt-Vergleich tatsächlich einen Rangsprung ausgelöst hat --
dessen 0/1148 (§8/§12-Kontext) bleibt unangetastet, aber es beruht auf
derselben Annahme (kein Rangkreuzungs-Ereignis in der Stichprobe), nicht auf
einer Eigenschaft, die einen Rangkreuzung ausschließt.

### Eigene Entscheidungen (nicht vorgegeben)

- `gumbel_scored_sorted` von `(f64, usize)` auf `(f64, f64, usize)`
  (Score, `g`, Index) erweitert -- exakt das Tupel-Layout des echten
  Produktionscodes (`net_mcts.rs:3719`), damit `g`/`ln(prior)` einzeln
  berichtbar sind. Einziger Aufrufer (`ort_cuda_single_deviation_gap_diagnostic`)
  entsprechend angepasst, kein anderer Code betroffen.
- Für Punkt (4) bewusst NUR die Code-Identität geprüft, keinen neuen Lauf
  gegen den synchron/verschränkt-Vergleich gefahren -- außerhalb des engen
  Auftrags-Zuschnitts ("eine gezielte Prüfung, nichts weiter").

---

## 16. VERTEILUNGSVERGLEICH MIT SELBSTKONTROLLE -- alle drei Masse identisch, UND eine batch-abhängige Überraschung

Nutzer-Auftrag 2026-08-12 ("verteilungsgleich statt punktgleich prüfen, und
den Batcher rückwirkend mit"): §15 zeigte, Punktgleichheit ist für keinen
Backend-Wechsel erreichbar. Gumbel-Top-m ist aber ohnehin stochastisch --
die Frage ist Verteilungsgleichheit, geprüft gegen eine aus der Messung
selbst gewonnene Rauschgrenze (Selbstkontrolle), nicht gegen eine vorab
gesetzte Schwelle.

### (1) Stichprobe und K

Struktureller Filter (nicht ergebnisabhängig): nur Zustände mit echtem
Schnitt (`m_prime < n_root`, wie §14) tragen stochastische Information --
**455/1148**. Ursprünglich geplant: eine Zufallsstichprobe `N=60` daraus
(fester Seed). Ein PILOTLAUF damit ergab bei ALLEN DREI Vergleichen exakt
dieselbe Zahl -- kein Fehler, sondern die Folge der in §14 gemessenen
Basisrate (1/455 ≈ 0,22%; Erwartungswert bei N=60 nur ~0,13 Treffer, die
seltene Vertauschung wird mit hoher Wahrscheinlichkeit komplett verfehlt).
**Deshalb (eigene Entscheidung) die VOLLE 455er-Menge verwendet, keine
Stichprobe** -- deterministisch, kein Stichproben-Glück, immer noch schnell
(~5s bei `N=455`). `K=200` (wie vorgeschlagen), aber ALLE DREI Vergleiche
mit `K/2=100` DISJUNKTEN Seeds je Seite (nicht `K` gegen `K`) -- Seite A ist
in allen drei Vergleichen dieselbe Berechnung (tract/synchron, Seeds 0-99),
Seite B unterscheidet sich: ORT-CUDA, verschränkt, bzw. tract/synchron mit
den ANDEREN 100 Seeds (Selbstkontrolle) -- fair, weil alle drei dieselbe
Auflösung (100 gegen 100) nutzen.

### (2) Die drei Maße

| Vergleich | max\|diff\| | mittel\|diff\| | n Paare |
| --- | ---: | ---: | ---: |
| tract vs. ORT-CUDA | 0,2800 | 0,0117 | 50.537 |
| synchron vs. verschränkt (tract) | 0,2800 | 0,0117 | 50.537 |
| SELBSTKONTROLLE (tract vs. tract) | 0,2800 | 0,0117 | 50.537 |

### (3) Innerhalb oder außerhalb der Selbstkontrolle

**Alle drei Zahlen sind identisch** (nicht nur "ähnlich" -- bis auf die
vierte Nachkommastelle gleich). tract-vs-ORT und synchron-vs-verschränkt
liegen damit **innerhalb** der Selbstkontrolle, mit Gleichheit als
Grenzfall. Direkt verifiziert, WARUM: die Kandidatenlisten-**Reihenfolge**
(die Ursache laut §15) unterscheidet sich in DIESER Messung nur bei
**1/455** Zuständen (tract vs. ORT) bzw. **0/455** (tract vs. verschränkt)
-- bei der übergroßen Mehrheit der Zustände ist die Reihenfolge über alle
Arme hinweg BITGLEICH, und selbst der eine Fall mit unterschiedlicher
Reihenfolge bewegt Max/Mittel im Aggregat aus 50.537 Paaren nicht sichtbar.

### (4) Der Batcher zeigt dasselbe Bild -- UND eine Überraschung

Synchron-vs-verschränkt zeigt exakt dasselbe Ergebnis wie tract-vs-ORT
(identische Zahlen, 0/455 Reihenfolge-Unterschiede -- sogar noch "sauberer"
als der ORT-Vergleich). Die Überraschung: **der aus §14/§15 bekannte
Zustand `record_index=320` selbst zeigt in DIESER Messung `order_diff=0`**
(GEPRÜFT: Priorwerte an Position 35/36 in diesem Lauf `0,002155971` vs.
`0,002155970` bei ORT -- ohne Vertauschung -- gegen `0,002155962` vs.
`0,002155958` bei tract, ebenfalls ohne Vertauschung, beide Seiten in
DERSELBEN Reihenfolge). Der in §15 gefundene Rangsprung trat dort unter
EINER ANDEREN Batch-Zusammensetzung auf (§14/§15: Chunks à 128 über alle
1148 Zustände) als hier (455 Zustände in EINEM ORT-Aufruf, ~28er-Batches
beim Sammel-Faden). Die EINE hier gefundene Reihenfolge-Abweichung
(1/455, tract-vs-ORT) betrifft einen ANDEREN, nicht identifizierten
Zustand. **Ob eine Rang-Vertauschung ueberhaupt auftritt, haengt also nicht
nur an "tract vs. ORT", sondern zusaetzlich an der Batch-Zusammensetzung
selbst** -- ein GEPRUEFTER Befund, keine Vermutung, aber NICHT weiter
verfolgt (aus dem Auftrag "nichts umbauen" heraus). Keine Deutung, ob das
fuer die Abnahme relevant ist.

GPU-Belegung: vorher 36 %/1.567 MiB/21,3 W, nachher 38 %/1.572 MiB/21,9 W;
Spitzenwert während des Laufs 1.752 MiB (+~180 MiB), 43,9 W (ggü. ~21-22 W
Grundlast) -- echte Rechenlast.

### Eigene Entscheidungen (nicht vorgegeben)

- Volle 455er-Menge statt Stichprobe (siehe Punkt 1) -- nachtraeglich
  entschieden, nach einem Pilotlauf, der die Notwendigkeit aufzeigte.
- Seite A identisch in allen drei Vergleichen (tract/synchron, Seeds 0-99)
  -- reduziert auf drei echte Freiheitsgrade (nur Seite B unterscheidet
  sich je Vergleich) statt sechs unabhaengige Stichproben.
- Aggregation ueber ALLE (Zustand, Kandidat)-Paare geflacht (nicht je
  Zustand gemittelt dann ueber Zustaende) -- gibt Zustaenden mit mehr
  Kandidaten proportional mehr Gewicht, naturtreu fuer "wie sieht ein
  zufaellig gezogener Kandidat aus".
- Zusaetzliche, nicht angeforderte Transparenz-Diagnose ergaenzt (Reihen-
  folge-Vergleich je Zustand, Einzelwerte fuer `record_index=320`) --
  ohne sie waere die batch-abhaengige Ueberraschung (Punkt 4) unsichtbar
  geblieben, und ein durchgehend identisches Aggregat ohne Erklaerung
  waere schwer einzuordnen gewesen.
- `Action` implementiert kein `Hash` (nur `PartialEq`/`Eq`) -- Haeufigkeits-
  Zaehlung ueber lineare `Vec`-Suche statt `HashMap` (bei `n_root<=130`,
  `K=200`, `N=455` performant genug, siehe Laufzeit ~5s).


---

## 17. VERTEILUNGSVERGLEICH und der PREIS, den ich nicht benannt hatte

### Ergebnis: nicht unterscheidbar -- aber der Test ist degeneriert

455 Zustaende (alle mit echtem Schnitt `m_prime < n_root`, kein Stichprobenglueck),
K=200, je Vergleich 100 gegen 100 disjunkte Seeds:

| Vergleich | max abs. Diff | mittel abs. Diff | n Paare |
| --------- | ------------: | ---------------: | ------: |
| tract gegen ORT-CUDA | 0,2800 | 0,0117 | 50.537 |
| synchron gegen verschraenkt | 0,2800 | 0,0117 | 50.537 |
| **SELBSTKONTROLLE** tract gegen tract | 0,2800 | 0,0117 | 50.537 |

**Alle drei identisch, nicht nur aehnlich** -- und das ist kein Messfehler, sondern
Degeneration: die Kandidatenreihenfolge unterscheidet sich nur in **1 von 455**
Zustaenden (tract gegen ORT) bzw. **0 von 455** (tract gegen verschraenkt). Bei
allen uebrigen ist sie bitgleich, dieselben Seeds erzeugen dieselben Mengen -- der
Backend-Vergleich IST dort die Selbstkontrolle.

**Was die Zahl trotzdem sagt**: der Umfang des Problems ist **0,22 % der
Zustaende**, und dort wird die Menge aus derselben Verteilung gezogen (Tausch zweier
benachbarter, praktisch gleichwertiger Kandidaten). Fuer den Batcher 0 von 455.

Was sie NICHT sagt: dass der Test eine Differenz erkennen KOENNTE, wenn es eine
gaebe. Bei einer Basisrate von 1/455 hat er dafuer keine Auflösung. Das ist eine
Grenze der Messung, nicht ein Beleg fuer Gleichheit.

### DER PREIS: mit Batcher ist die Suche NICHT MEHR REPRODUZIERBAR

`record_index=320` -- der Zustand mit dem 24-Rangsprung aus §14/§15 -- zeigt in
DIESER Messung `order_diff=0`. Priors an Position 35/36: 0,002155971 gegen
0,002155970, keine Vertauschung. Der Unterschied zur frueheren Messung: dort liefen
128er-Bloecke ueber alle 1148 Zustaende, hier 455 in einem Aufruf.

**Ob eine Rangvertauschung auftritt, haengt an der BATCH-ZUSAMMENSETZUNG.** Und mit
dem Batcher entsteht die Zusammensetzung aus dem Zeitverhalten der Faeden -- sie ist
von Lauf zu Lauf verschieden.

Folge, und sie hat nichts mit Staerke zu tun: **derselbe Seed kann mit
eingeschaltetem Batcher eine andere Partie ergeben.** Ich hatte diesen Preis in
keinem der Abschnitte §7-§16 benannt.

### DAS STEHT IM DIREKTEN WIDERSPRUCH ZU `PREREG_such_rng_trennen.md`

Jene Vorregistrierung hat als ganzen Zweck, Partien aus ihrem Seed reproduzierbar
zu machen -- Abschnitt 3 dort nennt es ausdruecklich als Nutzen 3
("Determinismus allgemein: seed-exakte Reproduktion einer Partie wird moeglich").
Der Nutzer hat sie freigegeben (Abschnitt 8 dort: Elo-Sprung wird vermerkt,
Paritaets-Basislinie wird neu gesetzt).

**Der Batcher arbeitet dagegen.** Beides gleichzeitig ist nicht zu haben: entweder
Durchsatz ueber eine zeitabhaengige Batch-Zusammensetzung, oder Reproduzierbarkeit.

Das ist eine ENTSCHEIDUNG, keine Messfrage, und sie gehoert dem Nutzer. Drei
Optionen, keine davon gemessen:

1. **Reproduzierbarkeit aufgeben** fuer Self-Play (dort zaehlt Durchsatz), sie aber
   fuer Arena/Gating behalten (dort zaehlt Nachvollziehbarkeit) -- der Knopf ist
   ohnehin je Prozess schaltbar.
2. **Batch-Zusammensetzung deterministisch machen** -- feste Gruppen statt "wer
   gerade wartet". Kostet Durchsatz, Betrag ungemessen.
3. **Reproduzierbarkeit vorziehen** und den Batcher nur fuer Messlaeufe nutzen, bei
   denen sie nicht gebraucht wird.

Option 1 ist die naheliegende und kostet nichts, aber sie ist meine Einschaetzung
und keine Messung -- **ausdruecklich als solche markiert.**

---

## 18. NUTZER-ENTSCHEID 2026-08-12: Option 1

*"batcher für self play an, arena und gating aus"*

Damit ist der Konflikt aus §17 entschieden, und beide Nutzen bleiben verfügbar:

| Kontext | Batcher | Begründung |
| ------- | ------- | ---------- |
| **Self-Play** | **AN** | dort zählt Durchsatz; Reproduzierbarkeit einzelner Partien wird nicht gebraucht, die Partien sind Stichproben |
| **Arena / Gating** | **AUS** | dort zählt Nachvollziehbarkeit; gepaarte Vergleiche und seed-exakte Reproduktion bleiben erhalten |

Umsetzung: der Knopf ist prozessweise schaltbar, also setzt der jeweilige
Einsprungpunkt ihn -- kein neuer Mechanismus nötig. **Zu beachten**: die
Self-Play-Treiber müssen ihn AKTIV setzen und die Arena/Gating-Treiber ihn
AKTIV NICHT setzen; ein Default-aus genügt, aber wer später einen gemeinsamen
Treiber baut, muss die Trennung mitnehmen.

Folge für die Paritätsprobe: sie prüft Defaults, läuft also weiter über den
tract-Pfad und bleibt gültig. Der Golden-Hash bleibt der Wächter für Arena und
Gating -- genau dort, wo er gebraucht wird.

---

## 19. ECHTE SELF-PLAY-MESSUNG (`self_play.py`): Weg B NICHT GEDECKT --
## Regel 3 verfehlt, gesättigter Batch übersetzt sich NICHT in Durchsatz

Nutzer-Auftrag 2026-08-13: die frühere e2e-Messung (`self_play_throughput_probe.rs`,
`evaluations/self_play_throughput_e2e*`) lief über ein eigens gebautes
Beispiel-Binary, NICHT über den Produktionspfad -- deshalb hier wiederholt über
`self_play.py` → `mosaic_rust.net_self_play_games` → `run_net_self_play`
(`self_play.rs:2822`), also exakt den Pfad, den ein echter Self-Play-Lauf nimmt.
Volle Zahlen: `evaluations/gpu_inference_path_selfplay_e2e_route_b.json`.

### Vorgefunden, nicht gebaut: die Verdrahtung aus §12 war bereits vollständig

Der Auftrag verlangte, den Batcher "NUR in `run_net_self_play`" einzuhängen und
zu prüfen, ob `try_batched_single_eval`/`try_batched_pair_ex` im Suchpfad hängen.
**Beide waren bereits verdrahtet, committet in `4de6f98` (2026-08-12), VOR
diesem Auftrag:**

- `self_play.rs:2843` (`run_net_self_play`) UND `self_play.rs:1742`
  (`run_net_arena_match`) rufen beide bereits `net_batcher::ensure_batcher_for`
  -- No-Op bei `MOSAIC_INTERLEAVE_ENABLED` aus, exakt das in §18 beschlossene
  Modell (der Knopf ist prozessweise geschaltet, nicht die Funktionsauswahl).
- `net_mcts.rs:1930-2089` (`net_leaf_eval`, `drafting_action_priors` -- die
  PRODUKTIONS-Blattauswertung, keine Testfunktion) versuchen bereits ZUERST
  `try_batched_pair_ex`/`try_batched_single_eval`, fallen erst bei `None` auf
  `net.eval_pair_ex`/`net.eval` zurück.
- `net.rs:451-477` (`eval_batch`) prüft bereits ORT-CUDA zuerst, dann Torch/IPC,
  dann tract -- exakt die in §12 festgelegte Rangfolge.

Die einzige eigene Code-Änderung: ein additives `batcher_diagnostics`-Objekt am
Ende von `run_net_self_play` (gleiches Muster wie
`perspective_divergence_diagnostics`), weil es vorher KEINEN Weg gab, den
tatsächlich erreichten mittleren Batch aus einem echten `self_play.py`-Lauf
auszulesen -- `self_play.py` filtert/druckt ihn und verwirft ihn vor dem
Pickling (kein Einfluss auf Trainingsdaten). Ausserdem der geforderte
DLL-Handgriff (`os.add_dll_directory` auf `torch/lib`, try/except, vor dem
`mosaic_rust`-Import).

### Baustein-Hürde: Wheel-Bau in einem isolierten Worktree

Der Arbeitsbaum hatte zum Zeitpunkt des Baus `tiling_solver.rs`/`provokation.rs`
unfertig (ein paralleler Agent, `spaltenbau`-Modul referenziert, aber nicht
deklariert) -- **`cargo check --lib` schlug dadurch AUCH ohne jedes Feature
fehl**, unabhängig von diesem Auftrag. Diese Dateien wurden nicht angefasst
(Auftragssperre). Stattdessen: `git worktree add --detach` auf HEAD, nur die
eigene `self_play.rs`-Änderung dorthin kopiert, dort mit
`--features ort_cuda_probe` und eigenem `CARGO_TARGET_DIR` gebaut. Wheel
installiert (`pip install --force-reinstall --no-deps`); die
ORT-CUDA-Provider-DLLs (`onnxruntime_providers_cuda/_shared/_tensorrt/
_nv_tensorrt_rtx.dll`, `DirectML.dll`) landen laut `ort`-Crate-Build-Skript
zwar automatisch neben dem `cdylib`-Rohbau im `target/release/`-Ordner, aber
NICHT im maturin-Wheel selbst (kein `[tool.maturin]`-Include dafür) -- von dort
per Handkopie neben die installierte `.pyd` in `site-packages/mosaic_rust/`
gelegt (gleiches Verfahren wie §11 für das Beispiel-Binary, nur diesmal für
den Python-Import-Pfad).

### Paritätsprobe: hält

`tools/parity_probe.py` nach dem Neubau: Hash
`8c6684ffba06cf3e16e898b83325f3154c04efac555c8e862c079b71155bd423` -- identisch
zum Bestand, Defaults byte-identisch.

### Die Messtabelle (`alphazero_v21_2d_brierbest.onnx`, base_sims=400, je 40
### angeforderte Partien, `data/gpu_measurement/` -- isoliert per `MOSAIC_DATA_DIR`,
### NICHT gelöscht)

| Arm | Threads | Partien fertig/angefordert | Wandzeit | Spiele/h (angefordert) | Spiele/h (fertig) | mittlerer Batch |
| --- | ------: | --------------------------: | -------: | ---------------------: | -----------------: | ---------------: |
| (a) Bestand | 8 | 40/40 | 638,4 s | 225,6 | 225,6 | -- (kein Sammel-Faden) |
| (a) Bestand | 64 | **3/40** | 498,1 s | 289,1 | 21,7 | -- |
| (b) Batcher+ORT-CUDA | 8 | 23/40 | 2190,3 s | 65,7 | 37,8 | **14,64** (Deckel 16) |
| (b) Batcher+ORT-CUDA | 64 | **0/40** | 454,2 s | 317,0 | **0,0** | -- (Prozess vom Wachhund getötet, bevor der Wert geschrieben wurde) |

**Beide 64er-Zellen sind degeneriert** -- 64 Fäden auf dieser Maschine (12
logische Kerne, 5,3x Überzeichnung) allein reichen, den
Chunk-Hänger-Notdeckel (450s) grossflächig auszulösen, UNABHÄNGIG von
Batcher/ORT-CUDA: schon der Bestand verliert dort 37 von 40 Partien an den
Wachhund. Der "requested-basis"-Faktor bei t64 (1,10x) ist ein Artefakt zweier
kaputter Nenner, kein Befund -- NICHT als Regel-3-Eingabe verwendet.

**Die einzige belastbare Zelle ist t8** (beidseitig überwiegend/vollständig
echte Partien, 40/40 gegen 23/40): dort ist Arm (b) **3,4x LANGSAMER** als
Arm (a) (2190,3s gegen 638,4s für dieselben 40 angeforderten Partien), UND
löste selbst 4 Chunk-Hänger aus (Bestand: 1x).

### Regel 3 (§4): NICHT GEDECKT

| | requested-basis | completed-basis |
| - | --------------: | ---------------: |
| Faktor (b)/(a), t8 | **0,29x** | **0,17x** |
| Faktor (b)/(a), t64 | nicht interpretierbar (siehe oben) | nicht interpretierbar |

Beide Zahlen der einzig belastbaren Zelle liegen NICHT nur unter der
2,0x-Schwelle, sondern unter 1,0x -- eine Regression, keine schwache
Verbesserung. **Weg B ist über den echten Self-Play-Pfad NICHT gedeckt.**

### Der Widerspruch zur eigenen Erwartung aus §9, ungeschönt

§9 schloss mit *"Der Befund stärkt Weg B [...] die drei Kostenposten [IPC,
Python, Tensor-Bau aus einem Puffer], die Weg A erledigt haben, existieren bei
Weg B nicht."* Das stimmt weiterhin als Code-Tatsache -- Weg B hat kein IPC,
kein Python, keinen Puffer-Tensor-Bau. **Trotzdem ist er hier langsamer, nicht
schneller, als der synchrone tract-Pfad.** Der erreichte Batch (14,64 von 16,
also nahe gesättigt) zeigt, dass die Verschränkung selbst tut, was sie soll --
die Bündelung funktioniert. Die Verlangsamung muss also woanders liegen:
im `Mutex<Session>` samt EINEM einzigen Sammel-Faden als serialisierendem
Nadelöhr, in `Session::run()`-Aufrufkosten pro Batch unter echter (nicht
synthetisch gleichförmiger) Ankunftsrate, oder im Zusammenspiel mit dem
Wachhund selbst. **Keine dieser Hypothesen ist hier geprüft** -- nur die
frühere (§9) Zerlegungstechnik ("sonstige Zeit je Sammelrunde" gegen den reinen
Rundlauf) würde eine Antwort liefern, und `BatcherStats` liefert dafür bisher
nur `batches`/`rows`/`max_batch_seen`, keine Latenzverteilung je Aufruf.

### Was NICHT geprüft ist

- Die Ursache der Verlangsamung selbst (siehe oben) -- keine Zeitzerlegung
  durchgeführt, nur die Endzahl gemessen.
- Threads=11 statt 8 als zweiter "Bestandskonvention"-Punkt -- nicht separat
  gefahren, 8 (self_play.py-Standard) stellvertretend gewählt.
- GPU-Auslastung ist ein Sekundenraster-Snapshot (`nvidia-smi -l 2`), keine
  kernelgenaue Messung -- die Bestands-Arme (kein GPU-Pfad aktiv) zeigen
  bereits 11-29% Mittelwert allein durch Desktop-Compositing-Rauschen, in
  derselben Grössenordnung wie die gemessenen Differenzen zwischen den Armen.
  Der GPU-Speicherstand (+~100-200 MiB bei Arm (b) gegenüber Arm (a)) ist der
  einzige robuste Beleg, dass tatsächlich ein Modell auf der GPU resident war.
- Ob eine kürzere/längere Chunk-Hänger-Notdeckel-Schwelle (450s,
  `self_play.py::MAX_CHUNK_TIMEOUT_SECS`) das Bild verändern würde --
  unverändert aus dem Bestand übernommen, nicht selbst variiert.

### Eigene Entscheidungen (nicht vorgegeben)

- `MOSAIC_DATA_DIR=data/gpu_measurement` (bereits existierender Override in
  `config.py`, gebaut für die Korpus-Dosis-Vorstudie) statt eines neuen
  CLI-Flags oder eines nachträglichen Verschiebens -- `self_play.py` hat kein
  eigenes Ausgabeverzeichnis-Argument, und ein Verschieben nach dem Schreiben
  hätte gegen das Löschverbot/Verschiebeverbot für `data/` verstossen
  (OneDrive-Sync, siehe `project_onedrive_file_disappearance`).
- Wheel-Bau in einem `git worktree --detach` auf HEAD statt im gemeinsamen
  Arbeitsbaum, weil letzterer durch einen parallelen Agenten aktuell nicht
  compiliert (`spaltenbau`) -- nur die eigene `self_play.rs`-Änderung
  hineinkopiert, `tiling_solver.rs`/`provokation.rs` nicht angefasst. Der
  Worktree (`scratchpad/wt_gpu2`) wurde NICHT entfernt (Löschverbot).
- ORT-Provider-DLLs per Handkopie neben die installierte `.pyd` gelegt (kein
  `[tool.maturin]`-Include ergänzt) -- kleinster Eingriff, kein
  Build-Konfigurationsschritt, der den Bestand für andere Feature-Kombinationen
  verändert hätte.
- `games_per_hour` in zwei Varianten berichtet (angefordert/fertig) statt einer
  einzigen Zahl -- bei stark unterschiedlicher Vollständigkeit zwischen den
  Armen wäre eine einzige Konvention irreführend gewesen (siehe t64, wo die
  angefordert-Basis fälschlich nach einer Verbesserung aussieht).
- t64-Zelle explizit als "nicht interpretierbar" markiert statt einen Faktor
  zu berichten, der aus zwei kaputten Nennern entsteht -- Regel 0/"trägt es
  nicht: sagen, nicht retten".

## 20. STUFE 3 (Async-Suche + Batcher + ORT-CUDA): Wiederholung von §19 mit
## dem entkoppelten Suchpfad -- Regel 3 NOCH DEUTLICHER verfehlt

Nutzer-Auftrag: §19s Ende-zu-Ende-Messung (Weg B, blockierende Fäden,
0,29x/0,17x bei Batch ~14,64) wiederholen, diesmal mit dem in
`evaluations/PREREG_async_suche.md` gebauten Baustein, der wartende Suchen
nicht mehr an einen OS-Faden bindet. Gebaut in Worktree `scratchpad/wt_async2`
(HEAD `7e5a243` + Stufe-1/2/3/4-Cherry-Picks, `cargo test --lib` 406/0/31),
neues Beispiel `engine/examples/async_selfplay_throughput_probe.rs`, drei
Arme: (a) Bestand synchron/tract (identischer Aufruf wie §19 Arm A), (b)
async verschränkt/tract-CPU, (c) wie (b) + `MOSAIC_ORT_CUDA_ENABLED=1`
(`--features ort_cuda_probe`, DLL-Handkopie wie §11/§19). Alle Läufe
`alphazero_v21_2d_brierbest.onnx`, 400 Sims, `data/gpu_measurement/` (dieses
Rust-Beispiel schreibt selbst keine `.pkl`-Dateien -- nur die JSONL-
Ergebniszeile).

### Die Messtabelle

Rohdaten: `evaluations/async_gpu_stage3_probe.jsonl` (8 Zeilen).

| Messpunkt | Träger-Fäden | N (Nebenläufigkeit) | fertig/angefordert | Wandzeit | mittlerer Batch | Batch-Deckel-Sättigung |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| (a) Bestand, 40 Partien | 8 | -- | 40/40 | 579,4 s | -- (kein Sammel-Faden) | -- |
| (b) async/tract | 8 | 64 | **0/64** | 449,0 s | 110,79 | 86,6 % |
| (b) async/tract | 8 | 128 | **0/128** | 481,5 s | 127,59 | 99,7 % |
| (b) async/tract | 8 | 256 | **0/256** | 550,5 s | 127,17 | 99,4 % |
| (b) async/tract | 8 | 8 | **0/8** | 441,3 s | 15,49 | 12,1 % |
| **Isolationsdiagnose (N=1, Seed 999, EINE Partie, kein Sammel-Faden-Wettbewerb):** |||||||
| (a) Bestand | 1 | -- | 1/1 | 21,70 s | -- | -- |
| (b) async/tract | 1 | 1 | **1/1** | 412,28 s | 1,96 | -- |
| (c) async/ORT-CUDA | 1 | 1 | **1/1** | 406,66 s | 1,96 | -- |

(Sättigung = mittlerer Batch / 128, dem harten `EVAL_BATCH_MAX_N`-Deckel aus
`net.rs`, GEPRÜFT.)

### Regel 3 (§4): NICHT NUR VERFEHLT -- die einzige gültige Zelle zeigt eine
### 19-fache Verlangsamung

Die N=64/128/256/8-Zeilen sind auf **completed-Basis nicht interpretierbar**
(0 von N Partien erreichten `Phase::End` -- dieselbe Konvention wie §19s
t64-Zelle: kein Faktor aus einem kaputten Zähler). Die EINZIGE Zelle mit
echter, geprüfter 1/1-Vollständigkeit auf beiden Seiten ist die
Isolationsdiagnose (N=1, kein Nebenläufigkeits-Wettbewerb):

| | Spiele/h | Faktor (b)/(a) | Faktor (c)/(a) |
| - | ---: | ---: | ---: |
| N=1, Seed 999 | (a) 165,87 / (b) 8,73 / (c) 8,85 | **0,053x** | **0,053x** |

**Weit unter der 2,0x-Schwelle, und weit unter §19s eigenem 0,29x/0,17x-Fund.**
Beide Backends (tract-CPU UND ORT-CUDA) liegen binnen 1,4 % beieinander --
der Engpass liegt NICHT im Inferenz-Backend, sondern in der
Async-Exec/Batcher-Rundlauf-Schicht selbst, die beiden Armen gemeinsam ist.

### Der Widerspruch, ungeschönt: der Sammel-Faden füllt hervorragend, aber
### das Spiel wird trotzdem nicht fertig

Zwei gegensätzliche Befunde in derselben Messung:

1. **Die Bündelung selbst funktioniert weit besser als in §19.** Bei N=128
   sättigt der mittlere Batch (127,59) den harten 128er-Deckel zu 99,7 % --
   gegenüber §19s 14,64 (Deckel 16, ~91 %) bei blockierenden Fäden ist das
   KEIN Zufall, sondern genau das, was Stufe 1/2 versprochen haben: wartende
   Suchen binden keinen OS-Faden mehr, also können weit mehr Partien
   gleichzeitig zum Sammel-Faden beitragen, ohne durch Thread-Überzeichnung
   ausgebremst zu werden (§19s eigene 64-Fäden-Zeile brach an genau diesem
   Punkt zusammen, 5,3x Überzeichnung löste den Chunk-Hänger-Notdeckel aus).
2. **Trotzdem erreichte KEINE der 64/128/256/8 Partien `Phase::End`** in
   441-579 s Wandzeit, während dieselbe Partie synchron 21,7 s braucht und
   isoliert-async (N=1, kein Wettbewerb) 412 s. Der `run_concurrent`-Aufruf
   selbst kehrte in allen vier Fällen zurück (die JSONL-Zeile enthält
   `batcher_batches`/`batcher_rows`, die erst NACH `run_async_wave` gelesen
   werden -- GEPRÜFT an `engine/examples/async_selfplay_throughput_probe.rs:
   254-264`, `run_concurrent` selbst hat laut `engine/src/async_exec.rs:81-98`
   KEINEN Timeout/Abbruchpfad, es kehrt nur zurück wenn ALLE Futures fertig
   sind). Das heisst: bei N≥8 endete JEDE beteiligte Partie über den
   `_ => break`-Zweig der Phasen-Schleife auf einer Phase, die NICHT
   `Phase::End` ist.

**Die genaue Ursache von Punkt 2 ist in dieser Sitzung NICHT isoliert --
ausdrücklich als ungeprüft markiert, nicht weginterpretiert.** Plausibel
(nicht bewiesen): unter echtem N-fachem Wettbewerb auf denselben Sammel-Faden
könnte die pro Runde/Entscheid vorhandene Wall-Clock-Notbremse
(`round_transition_deep::ROUND_SIM_TIME_BUDGET`/`POLICY_TIME_BUDGET_PER_DECISION`,
GEPRÜFT: 15s/200ms) unter der 19-fachen Verlangsamung anders greifen als
synchron und die Partie auf eine andere Phase lenken als im
Isolationsfall -- das ist eine Hypothese, KEIN Befund; eine Nachprüfung
bräuchte eine Instrumentierung, welche Phase die `_ => break`-Treffer bei
N≥8 tatsächlich verlassen, die aktuell nicht existiert.

### Zeitanteile: der Batch klemmt NICHT, das Ende-zu-Ende-Ergebnis klemmt an
### einer anderen Stelle

Der Auftrag verlangte eine Zerlegung "falls der Batch klemmt" (wie bei der
391s-Diagnose) -- hier klemmt der Batch gerade NICHT (99,7 % Sättigung bei
N=128). Die vorhandene Zerlegung ist die Isolationsdiagnose selbst: bei N=1
sind `batcher_batches=26323` (b) bzw. `26319` (c) für EINE Partie messbar
(GEPRÜFT: `async_gpu_stage3_probe.jsonl`), daraus folgt eine
Rundlaufzeit von **412,28s / 26323 ≈ 15,66 ms** (b) bzw. **406,66s / 26319 ≈
15,45 ms** (c) je Sammelrunde -- bei einem mittleren Batch von nur 1,96 legt
das nahe, dass die Rundlaufzeit selbst (nicht die Inferenz) den Löwenanteil
der 19-fachen Verlangsamung trägt. **Eine Zahlen-Koinzidenz, AUSDRÜCKLICH
NICHT instrumentell bestätigt (Regel 0):** 15,66 ms liegt nahe an Windows'
Standard-Systemtakt (1/64 s ≈ 15,625 ms) -- ob `mpsc::Receiver::recv_timeout`
(oder eine andere Wartestelle im Sammel-Faden/Executor) den konfigurierten
`fill_timeout` (200 µs, laut Stufe-1-Diagnose §9) tatsächlich in dieser
Granularität einhält, ist NICHT geprüft (`BatcherStats` liefert aktuell kein
`fill_wait_ns`/`eval_ns`-Feld, das dies direkt belegen würde). Diese Hypothese
wird hier ALS Hypothese berichtet, nicht als Befund.

### Regel 3 (§4): NICHT GEDECKT -- deutlicher verfehlt als §19

| | N=1 (einzig gültige Zelle) |
| - | ---: |
| Faktor (b: async/tract) / (a) | **0,053x** |
| Faktor (c: async/ORT-CUDA) / (a) | **0,053x** |

Beide weit unter der 2,0x-Schwelle UND unter §19s bereits negativem
0,29x/0,17x -- **der Async-Umbau macht den Ende-zu-Ende-Pfad langsamer, nicht
schneller**, trotz nachweislich exzellenter Batch-Füllung. Die
Amdahl-Obergrenze (2,6-5,3x) ist damit ebenfalls nicht erreichbar, solange
dieser Rundlauf-Kostenposten besteht.

### Was NICHT geprüft ist

- Die exakte Ursache, warum keine der N≥8-Partien `Phase::End` erreichte
  (siehe oben) -- keine Live-Instrumentierung der Phasenübergänge durchgeführt.
  - Die Windows-Systemtakt-Hypothese für die ~15,6 ms Rundlaufzeit --
    `fill_wait_ns`/`eval_ns` existieren nicht in `BatcherStats`, keine
    Nachmessung durchgeführt.
- Zweite Saat/Varianzprüfung (>=2 Seeds bei >20% Streuung) -- nur EIN Seed
  für den N=64/128/256/8-Sweep (20260814) und ein zweiter, separater Seed
  (999) für die Isolationsdiagnose; angesichts der Grössenordnung
  (19x, konsistent über zwei Backends) hätte eine zweite Saat das
  qualitative Ergebnis vermutlich nicht verändert, wurde aber nicht gefahren.
- Arm (c) nur bei N=1 gefahren, NICHT im vollen Sweep (siehe "Eigene
  Entscheidungen").
- `>=40` Partien je Messpunkt (Auftragsvorgabe) wurde für den
  N=64/128/256/8-Sweep durch die Nebenläufigkeit selbst erreicht (N Partien
  gleichzeitig), aber KEINE davon wurde fertig -- die Vorgabe "stabile Zahl"
  ist damit gegenstandslos, weil keine games/h-Zahl auf completed-Basis
  existiert.

### Eigene Entscheidungen (nicht vorgegeben)

- `carrier_threads=8` für alle (b)/(c)-Messpunkte (statt z.B. 4 oder 16) --
  identisch zu Arm (a)s Fadenzahl, damit ein Unterschied nicht durch eine
  andere Fadenzahl konfundiert wird.
- Isolationsdiagnose (N=1, EIN Träger-Faden, Seed 999) VOR dem vollen Sweep
  gefahren, obwohl nicht explizit angefordert -- ohne sie wäre der
  0/N-Befund bei N≥8 nicht von einem reinen "Batch reicht nicht"-Problem zu
  unterscheiden gewesen; sie zeigt, dass die Verlangsamung schon OHNE jede
  Nebenläufigkeit (also unabhängig von Sammel-Faden-Wettbewerb) 19x beträgt.
- Arm (c) NUR bei N=1 gefahren, nicht im vollen Sweep -- (b) zeigte bereits,
  dass der Engpass in der Async-Exec/Batcher-Schicht liegt, nicht im
  Inferenz-Backend (identische Rundlaufzeit tract vs. ORT-CUDA bei N=1);
  ein CUDA-Sweep bei N=64+ hätte nur dieselbe Schlussfolgerung mit
  zusätzlichem DLL-/GPU-Risiko wiederholt.
- Arm (a) frisch in `wt_async2` neu gemessen (statt §19s alte 225,6/h-Zahl
  zu übernehmen) -- andere Maschine/Zustand seit §19, "Geprüft oder
  markiert" verlangt eine eigene Prüfstelle für die Vergleichsbasis, nicht
  eine ältere Zahl aus einem anderen Lauf.
- N=64/128/256/8-Sweep NICHT künstlich abgebrochen (kein externer Timeout
  auf den Prozess) -- `run_concurrent` hat laut Code keinen Abbruchpfad,
  jede Zeile im Ergebnis-JSONL stammt von einem Lauf, der regulär
  zurückgekehrt ist (bestätigt durch die vorhandenen `batcher_*`-Felder,
  die erst nach `run_async_wave` gelesen werden).
- Kein Arena-Lauf, kein Gating -- wie im Auftrag verlangt, reine
  Kennlinien-/Durchsatzmessung.

### Fazit Stufe 3

**Weg B über den Async-Suchpfad ist über den echten Self-Play-Pfad NICHT
gedeckt -- schlechter als der bereits gescheiterte §19-Befund.** Die
Batch-Füllung selbst ist ein klarer, unabhängig geprüfter Erfolg der
Stufe-1/2-Bausteine (99,7 % Deckel-Sättigung bei N=128 gegen §19s ~91 % bei
Deckel 16, UND ohne den Thread-Überzeichnungs-Kollaps, den §19s 64-Fäden-
Zeile zeigte) -- aber dieser Erfolg übersetzt sich nicht in Durchsatz, weil
eine ~15,6ms-Rundlaufzeit je Sammelrunde (Ursache nicht instrumentell
bestätigt, Windows-Systemtakt nur eine plausible, ausdrücklich ungeprüfte
Hypothese) den gesamten Pfad 19x verlangsamt, unabhängig vom
Inferenz-Backend. Der aktuelle `async_exec::run_concurrent`/Waker-Pfad ist,
wie in seiner eigenen Dokumentation vermerkt, "NICHT produktionsreif" --
diese Messung bestätigt das jetzt mit Zahlen, nicht nur als Vorbehalt.

## 21. DER FIX: Condvar-basiertes Park/Wake -- von 0,053x auf 0,98x, Regel 3
## trotzdem NICHT gedeckt (Ursache jetzt eine ANDERE, code-belegte Grenze)

Nutzer-Auftrag nach §20: die 15,6ms-Koinzidenz beweisen statt vermuten, den
Sleep-/Poll-Fund reparieren (Condvar statt Takt-Hack), neu messen, und die
0/N-Anomalie aus §20 aufklären statt sie stehenzulassen.

### Punkt 1: Beleg statt Koinzidenz

**Fundstelle** (Commit `c540285`, `wt_async2`, GEPRÜFT per `git show`):
- `engine/src/net_batcher.rs:318`: `match req_rx.recv_timeout(fill_timeout)
  { ... }` in der Fuell-Schleife des Sammel-Fadens -- EIN solcher Aufruf pro
  Batch, IMMER dann, wenn keine weitere Zeile sofort verfuegbar ist (bei
  N=1 also praktisch jeder Batch). Das ist die EINZIGE Stelle in der
  Async-/Batcher-Kette mit einem Warte-Aufruf, der eine Zeitspanne
  entgegennimmt.
- `engine/src/async_exec.rs:81-97` (`run_concurrent`, alter Stand): KEIN
  Sleep/Timeout -- reines Busy-Poll (`for i in 0..futs.len() { ...
  futs[i].poll(...) }` in einer `while`-Schleife ohne jede Wartezeit).
  Verschwendet CPU, ist aber NICHT die Quelle der 15,6ms-Latenz (dafuer gibt
  es dort keinen Kandidaten-Aufruf).

**Test**: `timeBeginPeriod(1)` (WinMM, `winmm.lib`) vor der Isolationsmessung
gesetzt (`rc=0`, `TIMERR_NOERROR`, GEPRÜFT per Rueckgabewert), ALTER Code
(vor dem Fix unten), N=1/Seed 999:

| | ohne `timeBeginPeriod` (§20) | mit `timeBeginPeriod(1)` |
| - | ---: | ---: |
| Wandzeit | 412,28 s | **411,28 s** |
| Batches | 26323 | 26317 |

**Widerlegt**: 1,0 s Unterschied bei 412 s Gesamtlaufzeit ist Rauschen, keine
Verbesserung. Der Windows-Multimedia-Timer (`timeBeginPeriod`) ist NICHT der
wirksame Hebel -- die 15,6ms-Zahlenkoinzidenz mit dem Standard-Systemtakt
(1/64 s ≈ 15,625 ms) bleibt damit ungeklaert, aber die naheliegendste
Reparatur (Systemtakt global anheben) ist WIDERLEGT, nicht bestaetigt. Das
ist ein Befund fuer sich: `recv_timeout`s tatsaechliche Wartegranularitaet
auf Windows haengt laut dieser Probe NICHT (nur) am klassischen Multimedia-
Timer, den `timeBeginPeriod` bedient -- WARUM sie trotzdem bei ~15,6ms liegt,
ist nicht weiter untersucht (ausserhalb des Auftragsumfangs, siehe "Was
nicht geprüft ist").

### Punkt 2: Der Fix -- Condvar-Wecken statt Takt-Warten

Zwei Stellen geaendert (`wt_async2`, Commit-Historie siehe unten):

- **`net_batcher.rs`**: `collector_loop`s Fuell-Schleife ruft nicht mehr
  `recv_timeout` auf. Neue `Doorbell` (`Mutex<()>` + `Condvar`) wird von
  JEDEM Aufrufer nach dem Einreichen einer Zeile SOFORT geklingelt
  (`notify_all`). Die Fuell-Schleife selbst (`wait_for_more_row`) prueft per
  `try_recv` (kein Warte-Aufruf), und weicht fuer das verbleibende
  Zeitfenster unter `SPIN_WAIT_THRESHOLD` (2 ms, der konfigurierte
  `fill_timeout`-Default von 200 µs liegt komplett darunter) auf Spinnen
  (`std::hint::spin_loop()`, `Instant::now()`-Polling) aus -- KEIN
  OS-Wartepfad, also KEINE Systemtakt-Rundung moeglich, unabhaengig davon,
  wodurch diese in Punkt 1 entsteht. Fuer unueblich GROSSE konfigurierte
  Fenster (weit ueber einem Systemtakt) bleibt ein echtes
  `Condvar::wait_timeout` auf die Klingel als Fallback bestehen -- dort
  faellt die Rundung relativ zum Fenster nicht mehr ins Gewicht.
- **`async_exec.rs`**: `run_concurrent` pollt nicht mehr reihum ALLE
  offenen Futures. Jedes Future bekommt einen eigenen `ReadySetWake`-Waker
  (Index-spezifisch); der Treiberfaden parkt (`Condvar::wait`, UNBEFRISTET)
  bis irgendein Future per `wake()` als bereit markiert wurde, pollt dann
  NUR die tatsaechlich bereiten. Ein unbefristetes Warten ist auf Windows
  praezise/sofort aufgeweckt (das Systemtakt-Problem betrifft laut Punkt 1
  spezifisch KURZE `_timeout`-Aufrufe, nicht unbefristete Waits).

`cargo test --lib` nach beiden Aenderungen: **406/0/31**, unveraendert
gegenueber dem Stand vor dem Fix -- Gate A/B (Entscheidungsgleichheit,
Bit-Identitaet ohne Batcher) bleiben unberuehrt, die Umstellung aendert NUR
WANN gepollt/gesammelt wird, nicht WOHIN Ergebnisse geschrieben werden.

### Punkt 3: Nachmessen

Referenzen (§20, unveraendert): Sync-Flotte (a) 40 Partien/8 Faeden =
**248,5 Partien/h**; Sync-Isolation (a) 1 Partie = **165,87 Partien/h**
(21,70 s).

| Messpunkt | Traeger | N | fertig/angefordert | Wandzeit | Partien/h | mittl. Batch | Faktor ggue. Sync |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Isolation (b) tract | 1 | 1 | 1/1 | 22,94 s | 156,9 | 1,96 | **0,946x** |
| Isolation (c) ORT-CUDA | 1 | 1 | 1/1 | 42,30 s | 85,1 | 1,96 | **0,513x** |
| Flotte (b) tract | 8 | 8 | 8/8 | 130,47 s | 220,7 | 11,95 | 0,888x |
| Flotte (b) tract | 8 | 16 | 16/16 | 236,79 s | 243,3 | 18,82 | **0,979x** |
| Flotte (b) tract | 8 | 32 | **1/32** | 439,56 s | -- (nicht interpretierbar) | 31,59 | -- |
| Flotte (b) tract | 8 | 64 | **0/64** | 441,61 s | -- (nicht interpretierbar) | 56,64 | -- |
| Flotte (b) tract (Wdh.) | 8 | 64 | **0/64** | 442,23 s | -- (nicht interpretierbar) | 56,16 | -- |
| Flotte (c) ORT-CUDA | 8 | 16 | 16/16 | 260,68 s | 221,0 | 18,58 | 0,889x |

**Verbesserung ggue. §20 (N=1)**: tract 156,9 / 8,73 = **17,97x**; ORT-CUDA
85,1 / 8,85 = **9,62x** -- der Fix wirkt in BEIDEN Backends, mit sehr
unterschiedlicher Grössenordnung (siehe unten).

**Neuer Befund, vom Fix erst sichtbar gemacht**: tract schlaegt ORT-CUDA bei
N=1 UND bei N=16 (22,94s vs 42,30s; 243,3 vs 221,0 Partien/h) -- vor dem Fix
lagen beide Backends binnen 1,4% beieinander (§20), weil die 19-fache
Rundlauf-Verlangsamung beide gleichermassen ueberdeckte. Jetzt, wo dieser
Deckel weg ist, zeigt sich die BEKANNTE Kennlinie aus §9-§19: ORT-CUDAs
GPU-Dispatch-Overhead pro Aufruf lohnt sich erst ab einem grossen Batch
(dokumentierte Gewinnzone ab 128) -- bei den hier erreichten Batches (1,96
bis 18,82) ist tract-CPU durchgaengig schneller. Das ist KEIN neuer Fund an
sich (§9-§19 haben genau das schon fuer den blockierenden Pfad gezeigt),
sondern die Bestaetigung, dass er nach dem Fix wieder SICHTBAR ist, statt
von einem Async-Kostenposten ueberdeckt zu werden.

### Regel 3 (§4): IMMER NOCH NICHT GEDECKT, aber die Groessenordnung hat
### sich komplett verschoben

Die BESTE vollstaendige (completed-Basis) Zelle ist N=16/tract: **0,979x**
-- nahe an Sync-Paritaet, aber unter der 2,0x-Schwelle. N=8 liegt bei
0,888x, N=1 bei 0,946x. **Keine der gemessenen Zellen erreicht 2,0x.** Der
Fix hebt den Pfad von "19x langsamer" (§20) auf "nahezu gleich schnell"
(§21) -- das ist eine fundamentale Verbesserung der eigentlichen
Async/Batcher-Maschinerie, aber noch KEIN Konkurrenzvorteil gegenueber
synchron, weil bei diesen Batch-Groessen (unter 32) keine Backend-seitige
Effizienzsteigerung zu holen ist, die den (kleinen, aber realen)
Rest-Overhead der Verschraenkung selbst aufwiegen wuerde.

### Punkt 4: Die 0/N-Anomalie aus §20 -- AUFGEKLAERT, kein Deadlock, keine
### Restspur des alten Rundlauf-Problems

Mit `MOSAIC_DIAG_STUCK_PHASE=1` (protokolliert je Partie die letzte
erreichte Runde/Phase) instrumentiert, VOR der Neumessung:

- **N=8** (1 Partie/Traeger-Faden, keine echte Mehr-Futures-pro-Faden-Last):
  8/8 Partien enden korrekt bei `Runde 5, Phase Tiling, completed=true`.
  Kein Anomalie-Verhalten -- entspricht dem erwarteten Spielablauf.
- **N=64** (8 Partien/Traeger-Faden, zwei Wiederholungen): **64/64 Partien
  enden mit `completed=false`**, 40 bei Runde 2, 24 bei Runde 3 (von 5) --
  GEPRÜFT per Instrumentierungs-Log, reproduzierbar ueber beide Laeufe.

**Ursache** (GEPRÜFT, `engine/src/self_play.rs`, Commit `c540285`+Fix,
Zeilen unveraendert von dieser Aenderung):

```
self_play.rs:3176   let t_start = std::time::Instant::now();
self_play.rs:3177   let timeout_secs = net_game_timeout_secs(base_sims)
                         + crate::round_transition_deep::EXTRA_GAME_TIMEOUT_SECS;
self_play.rs:3183   if guard > 100_000 || t_start.elapsed().as_secs() >= timeout_secs {
                         break;
                     }
```

`net_game_timeout_secs(400) = (400*9)/20 = 180` (`self_play.rs:86-88`,
GEPRÜFT), `EXTRA_GAME_TIMEOUT_SECS = 60+75+75+45 = 255`
(`round_transition_deep.rs:180`, GEPRÜFT) -- macht **435 Sekunden** WAND-
ZEIT-Deckel PRO PARTIE (Task #71, existiert unveraendert seit vor diesem
Async-Umbau, gedacht als Haenger-Schutz fuer den SYNCHRONEN Pfad). Bei N=64
teilen sich 64 Partien EINEN Sammel-Faden -- jede einzelne Partie braucht
dadurch pro Entscheid laenger (die MCTS-Suche einer Partie ist inhaerent
SEQUENTIELL, sie kann nicht gegen sich selbst batchen; Batching entsteht nur
ueber VERSCHIEDENE gleichzeitige Partien). Bei 64-facher Teilung reicht die
Wandzeit fuer eine volle 5-Runden-Partie nicht mehr innerhalb von 435s --
der Notdeckel greift GENAU WIE VORGESEHEN (er schuetzt vor echten Haengern),
trifft hier aber eine Partie, die nur LANGSAM, nicht haengend, war.

**Das ist die vollstaendige Erklaerung der §20-0/N-Anomalie**: KEIN Deadlock,
KEINE Restspur des alten 19x-Rundlauf-Problems, KEIN Bug im Fix -- sondern
ein VORBESTEHENDER, fuer den synchronen Ein-Partie-Fall kalibrierter
Wandzeit-Notdeckel, der bei dieser Konkurrenzstufe (64 Partien / 1
Sammel-Faden) zu eng wird. Bestaetigt durch N=32 als Grenzfall (nur 1/32
schafft es knapp vor 439,56s) -- die Schwelle liegt zwischen N=16 (16/16
fertig) und N=32/N=64.

### Was NICHT geprüft ist

- WARUM `recv_timeout`/`Condvar::wait_timeout` auf dieser Maschine trotz
  widerlegtem `timeBeginPeriod`-Hebel bei ~15,6ms lag -- der Fix umgeht die
  Frage (kein `_timeout`-Aufruf mehr im gemessenen Bereich), beantwortet sie
  aber nicht. Wuerde weitere Windows-Kernel-Recherche brauchen (z.B.
  `NtSetTimerResolution`, `WaitOnAddress`-Interna), ausserhalb des
  Auftragsumfangs.
- Der 435s-Notdeckel selbst wurde NICHT angepasst/parametrisiert -- er ist
  Bestandteil des produktiven Haenger-Schutzes (Task #71) und war nicht
  Gegenstand dieses Auftrags. Eine hoehere N-Konkurrenzstufe (echte
  Produktionswerte) wuerde eine bewusste, separate Entscheidung ueber diesen
  Deckel brauchen (z.B. skaliert mit der Konkurrenzstufe) -- hier nur
  beschrieben, nicht gebaut.
- Batches ueber 32 wurden wegen des 435s-Deckels nicht vollstaendig
  (completed-Basis) gemessen -- ob die Regel-3-Schwelle bei hoeheren,
  produktionsnahen Batch-Groessen (>64, in Richtung der ORT-Gewinnzone 128)
  doch noch erreicht wird, ist NICHT geprueft.
- Nur EIN Seed je Zelle (Zeitbudget) -- bei der Groessenordnung der
  Verbesserung (17,97x/9,62x, weit ausserhalb jeder plausiblen Varianz)
  waere eine zweite Saat fuer die RICHTUNG des Befunds nicht entscheidend,
  fuer die exakten Faktoren aber nicht abgesichert.

### Eigene Entscheidungen (nicht vorgegeben)

- `SPIN_WAIT_THRESHOLD = 2ms` als Grenze zwischen Spinnen und echtem
  `wait_timeout` -- der gemessene/konfigurierte `fill_timeout`-Default (200
  µs) liegt komfortabel darunter, ohne den Fallback-Pfad fuer unuebliche
  Konfigurationen zu verlieren.
- N=32 als zusaetzlicher Messpunkt (nicht angefordert) eingefuegt, um die
  435s-Schwelle zwischen N=16 (vollstaendig) und N=64 (0 vollstaendig)
  einzugrenzen, statt nur die zwei angeforderten Punkte zu berichten.
- 0/N-Anomalie-Diagnose VOR der finalen N=64-Messung gefahren (wie im
  Auftrag verlangt) -- dieselbe Konfiguration zweimal gemessen (mit und ohne
  `MOSAIC_DIAG_STUCK_PHASE`), um den Befund (Runde 2-3, completed=false) als
  reproduzierbar statt als Einzelmessung zu belegen.
- ORT-CUDA-Sweep auf N=1 und N=16 begrenzt (nicht N=8/32/64) -- der
  Backend-Unterschied ist bei N=1 und N=16 bereits eindeutig und konsistent
  (tract schneller, siehe oben); weitere Zellen haetten dieselbe
  Schlussfolgerung nur wiederholt, bei zusaetzlichem Zeit-/GPU-Risiko.

### Fazit §21

Der Condvar-Fix behebt das in §20 gefundene 19x-Rundlauf-Problem
vollstaendig -- der Async-Pfad liegt jetzt bei 0,89x-0,98x gegenueber
synchron, nicht mehr bei 0,053x. **Regel 3 (>=2,0x) ist damit IMMER NOCH
NICHT gedeckt**, aber aus einem GRUNDSAETZLICH ANDEREN Grund als in §20:
nicht mehr eine kaputte Rundlauf-Mechanik, sondern schlicht, dass die
erreichten Batch-Groessen (bis 32, real gemessen) noch unter der
Groessenordnung liegen, ab der Batching selbst einen Effizienzgewinn
gegenueber synchronem Rechnen bringt. Die zusaetzlich aufgeklaerte
0/N-Anomalie ist ein vorbestehender, fuer den synchronen Fall kalibrierter
Wandzeit-Notdeckel (Task #71, `self_play.rs:3177/3183`), keine neue
Baustelle des Async-Umbaus. Ob hoehere, produktionsnahe Konkurrenzstufen
(die diesen Notdeckel bewusst mitdenken muessten) die 2,0x-Schwelle
erreichen, ist eine offene, nicht triviale Folgefrage.

## 22. DIE ORT-GEWINNZONE BEI BATCH>=128 -- GEMESSEN, UND DIE VORAB
## DOKUMENTIERTE ERWARTUNG NICHT BESTAETIGT

Nutzer-Auftrag nach §21: den 435s-Notdeckel messtauglich machen (Task-#28-
Muster, additiv, Default unveraendert) statt ihn produktiv umzubauen, dann
N=64/128 (und N=256 ORT nur falls 128 nicht saettigt) je tract UND ORT-CUDA
fahren -- das ist die Zelle, in der laut Kennlinie (§9-§19) die ORT-
Gewinnzone (ab Batch 128) endlich mitspielen sollte, statt wie in §21 durch
zu kleine Batches (<=32) unerreichbar zu bleiben.

### Der Deckel-Knopf (Punkt 1 des Auftrags)

`self_play.rs`: `net_self_play_game_timeout_secs(base_sims)` extrahiert die
bisherige `net_game_timeout_secs(base_sims) + EXTRA_GAME_TIMEOUT_SECS`-Summe
unveraendert und skaliert sie mit `game_timeout_scale()`
(`MOSAIC_GAME_TIMEOUT_SCALE`, Default **1,0** = byte-identisch zum
Bestand, Task-#28-Muster) an BEIDEN Aufrufstellen (sync + async). `cargo
test --lib` danach unveraendert **406/0/31**. Das Mess-Beispiel setzt den
Knopf fuer Arm b/c automatisch auf `concurrency` (~N-skaliert, siehe
`set_arm_env`) und ersetzt den damit funktionslos gemachten Pro-Partie-
Deckel durch eine GLOBALE Ende-zu-Ende-Deadline
(`--global-timeout-secs`, Default 1800s, in dieser Messreihe auf 3600-5400s
angehoben) -- die einzige noch aktive Haenger-Absicherung fuer diese
Messung.

### Die Messtabelle

Sync-Bezug (§20/§21, unveraendert): **248,5 Partien/h** (40 Partien, 8
Faeden).

| Messpunkt | N | fertig/angefordert | Wandzeit | Partien/h | mittl. Batch | Faktor ggue. Sync | Zeilen/s (Aggregat) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| tract | 64 | 64/64 | 1349,70 s | 170,7 | 50,27 | 0,687x | 2624,4 |
| ORT-CUDA | 64 | 64/64 | 600,30 s | **383,8** | 48,19 | **1,545x** | 5955,6 |
| tract | 128 | **nicht abgeschlossen** (siehe unten) | -- | -- | -- | -- | -- |
| ORT-CUDA | 128 | 128/128 | 1260,73 s | 365,5 | 81,70 (Deckel 128 erreicht) | 1,471x | 5648,9 |

### Regel 3 (§4): WEITERHIN NICHT GEDECKT -- und ORT-CUDA wird bei N=128
### NICHT besser, sondern leicht SCHLECHTER als bei N=64

Die beste gemessene Zelle ueberhaupt (ueber §20-§22 hinweg) ist **N=64
ORT-CUDA mit 1,545x** -- unter der 2,0x-Schwelle, aber der bisher
naechste Punkt daran. **Die vorab im Auftrag dokumentierte Erwartung
("ORT muss bei Batch>=128 laut Kennlinie deutlich abheben") trifft NICHT
ein**: obwohl der mittlere Batch von N=64 auf N=128 deutlich steigt (48,19
auf 81,70, `max_batch_seen` erreicht bei BEIDEN den harten 128er-Deckel),
FAELLT sowohl der Faktor (1,545x auf 1,471x) als auch der reine
Zeilen-Aggregatdurchsatz (5955,6 auf 5648,9 Zeilen/s, -5,2%). Mehr
Nebenlaeufigkeit bringt hier also NICHT mehr Durchsatz, sondern
tendenziell weniger -- das Gegenteil der Kennlinien-Erwartung, die aus
einer SYNTHETISCHEN, gleichfoermigen Batch-Fuellung stammt (`net.rs`-
Mikrobenchmark, siehe §9), waehrend die reale Ankunftsrate hier durch 128
unabhaengige, ungleichmaessig fortschreitende Partien UND einen einzigen
Sammel-Faden bestimmt wird, der selbst bei Batch 81,70 im Mittel weit
unter der synthetischen Kennlinien-Bedingung (durchgehend volle 128er-
Batches) bleibt. **Dieser Befund wird so berichtet, nicht wegerklaert.**

### tract N=128: DREI Versuche, KEIN abgeschlossenes Ergebnis --
### Ursachendiagnose (Punkt 4 des Auftrags: nicht still neu starten)

Drei Läufe (`--global-timeout-secs 5400`, harness-getrackt per
`run_in_background`, jeweils frisch gestartet nach Bestaetigung, dass kein
Restprozess mehr lief), ALLE mit demselben Muster: stetiges, NICHT
stockendes Wachstum (Fortschritts-Herzschlag alle 30s, `batches`/`rows`
steigen durchgehend, kein Plateau, kein Fehler/Panik im stderr-Log) bis
zum Abbruch bei **t≈3450-3570s (57,5-59,5 Minuten)**, dort jeweils
5,6-5,8 Mio. Zeilen erreicht (von geschaetzt ~7,08 Mio. gesamt, extrapoliert
aus dem 2-fachen von N=64s 3,54 Mio.) -- **80-82% des erwarteten Volumens,
keine Stagnation.** Alle drei Abbrueche erfolgten NICHT durch die
watchdog-Deadline (5400s, nie erreicht) und NICHT durch einen Absturz
(kein Panik-Log, kein OOM-Hinweis im stderr) -- sondern jeweils als "was
stopped"-Ereignis der Mess-Umgebung selbst (Sitzungslimit-Interrupt der
Agenten-Sitzung, die den Hintergrundprozess getrackt hat), reproduzierbar
am (fast) selben Wandzeit-Punkt ueber alle drei Versuche hinweg.

**Kausalitaet daher wie folgt eingeordnet**: die MESSUNG selbst zeigt
KEIN Anzeichen eines Haengers oder einer Regression -- lineare
Extrapolation der letzten gemessenen Rate (~770-860 Zeilen/s in den
letzten Intervallen vor jedem Abbruch) auf das geschaetzte Gesamtvolumen
ergibt eine erwartete Gesamtlaufzeit von **~85-90 Minuten**, ausdruecklich
als HERLEITUNG markiert, NICHT gemessen. Der Abbruch selbst ist ein
Befund ueber die MESSUMGEBUNG (Sitzungslimit liegt unter der fuer diese
Zelle benoetigten Wandzeit), NICHT ueber den Async-Pfad oder den
skalierten Notdeckel -- beide taten in allen drei Laeufen genau das, was
sie sollten (kein vorzeitiger Abbruch durch `net_self_play_game_timeout_secs`,
kein Hänger).

### Task-#71-Notdeckel: JETZT DREIFACH als Stoerer aktenkundig

1. Gate-B-Trainingsziel-Divergenz (`PREREG_async_suche.md` §12): sync/async
   unterschiedliche Wandzeit-Geschwindigkeit fuer aequivalente Arbeit lenkt
   den Notdeckel unterschiedlich, divergente `bootstrap_value`/
   `round_transition_value`-Felder trotz bit-identischer Zuege.
2. Flotten-Kappung (§20/§21): bei N=64 kappte der UNSKALIERTE Notdeckel
   ALLE 64 Partien vor Rundenende (0/64 completed), obwohl keine haengte --
   reine Kalibrierungslücke fuer Nebenlaeufigkeit.
3. (NEU, §22) Selbst nach der Skalierung bleibt die REALE Wandzeit pro
   Partie bei hoher Nebenlaeufigkeit so gross (~85-90 Min. bei N=128
   tract, extrapoliert), dass eine VOLLSTAENDIGE Messung an der
   Mess-INFRASTRUKTUR (Sitzungs-/Prozesslaufzeitgrenzen), nicht mehr am
   Notdeckel selbst, scheitern kann -- ein Symptom, dass der aktuelle
   Ein-Sammel-Faden-Entwurf bei sehr hoher Konkurrenz strukturell lange
   Einzelpartie-Laufzeiten erzeugt, unabhaengig vom Notdeckel.

**Umbau-Empfehlung (offener Punkt, NICHT jetzt umgesetzt)**: perspektivisch
waere ein deckelfreies Trainings-Label-Schema (Task-#71-Zeitbudgets NUR
als Haenger-Schutz, niemals einflussreich auf das aufgezeichnete Ergebnis)
oder eine concurrency-bewusste Kalibrierung (Notdeckel als Funktion der
AKTUELLEN Sammel-Faden-Auslastung statt eines statischen Faktors) die
sauberere Loesung fuer alle drei Symptome gleichzeitig. Ausserhalb des
Auftragsumfangs dieser Messreihe -- hier nur als wiederholt aktenkundiger,
offener Befund vermerkt.

### Was NICHT geprüft ist

- N=128 tract: kein abgeschlossenes Ergebnis (siehe oben) -- die
  berichteten ~85-90 Minuten sind eine Extrapolation aus drei
  uebereinstimmenden Teil-Laeufen, KEINE Messung.
- N=256 ORT-CUDA: NICHT gefahren -- der Auftrag sah dies nur vor, "falls
  128 nicht saettigt"; `max_batch_seen=128` bei N=128 (der harte
  `EVAL_BATCH_MAX_N`-Deckel) UND ein FALLENDER, nicht steigender
  Aggregatdurchsatz von N=64 auf N=128 sprechen gegen einen Gewinn bei
  noch mehr Konkurrenz -- als eigene Entscheidung nicht gefahren (siehe
  unten), nicht weil die Bedingung unklar war.
- Die genaue Ursache des GPU-seitigen Nicht-Abhebens (Mutex-serialisierter
  Sammel-Faden? `Session::run()`-Aufrufkosten bei ungleichmaessiger
  Ankunftsrate? Speicher-/Cache-Effekte bei 128 gleichzeitigen
  Baumzustaenden?) -- keine Zeitzerlegung des `eval_ns`/`fill_wait_ns`-Paars
  fuer diese Zellen durchgefuehrt (waere der naechste Schritt, analog zur
  391s- und 15,6ms-Diagnose).
- GPU-Auslastung nur als Vorher/Nachher-Schnappschuss (wie §20/§21) UND ein
  kurzer, vorzeitig abgebrochener kontinuierlicher Log-Ausschnitt (13-31%,
  8 Samples über ~16s, siehe "Eigene Entscheidungen") -- kein vollstaendiger
  kontinuierlicher Verlauf ueber eine ganze Zelle.
- Nur EIN Seed je Zelle.

### Eigene Entscheidungen (nicht vorgegeben)

- `SPIN_WAIT_THRESHOLD`/Doorbell-Architektur aus §21 unveraendert
  uebernommen -- kein erneuter Eingriff in den bereits gefixten Rundlauf
  noetig fuer diesen Auftrag.
- `MOSAIC_GAME_TIMEOUT_SCALE` als Multiplikator (nicht als absolute
  Sekundenzahl) gewaehlt UND im Beispiel automatisch auf `concurrency`
  gesetzt -- vermeidet einen weiteren manuellen Parameter je Messpunkt,
  ohne den Bestand (Default 1,0) zu beruehren.
- 30s-Fortschritts-Herzschlag (`batches`/`rows`/`mean_batch` aus dem
  Sammel-Faden) additiv ergaenzt, NACHDEM der erste N=128-tract-Versuch
  ohne jede Diagnosedaten starb (Auftrag Punkt 4: Ursache diagnostizieren
  statt still neu starten) -- ohne ihn waere die "kein Haenger, nur zu
  langsam"-Einordnung oben nicht moeglich gewesen.
- Kontinuierliches GPU-Logging (`nvidia-smi -l N`) nach einem ersten
  fehlgeschlagenen Versuch (verschachteltes `&` in einem Hintergrund-
  Aufruf, siehe `feedback_agent_background_process_discipline`-Lektion,
  Prozess starb nach ~16s mit) NICHT wiederholt -- angesichts der ohnehin
  wiederholten Sitzungsunterbrechungen bei den Hauptmessungen war das
  Risiko eines weiteren verlorenen Nebenprozesses gegenueber dem
  Diagnosewert (GPU-Auslastung ist bei tract ohnehin 0%, bei CUDA laut
  Schnappschuss 22-30%) nicht gerechtfertigt.
- N=128 tract nach dem DRITTEN uebereinstimmenden Abbruch NICHT ein
  viertes Mal versucht -- alle drei Versuche brachen am (fast) selben
  Wandzeit-Punkt (57,5-59,5 Min.) mit identischem, nicht-stockendem Muster
  ab; ein vierter Versuch haette voraussichtlich dasselbe wiederholt
  (Mess-Infrastruktur-Grenze, kein Zufallsartefakt) -- die Zeit floss
  stattdessen in die bereits abgeschlossene, ENTSCHEIDENDE Zellenreihe
  (ORT-CUDA N=64/128, die die Auftrags-Kernfrage beantwortet).
- N=128 ORT-CUDA VOR dem dritten tract-Versuch priorisiert, nachdem N=64
  ORT-CUDA in nur 600s (gegen tracts 1349,7s) fertig wurde -- die
  wahrscheinlichere schnell abschliessbare UND fachlich entscheidendere
  Zelle zuerst.

### Fazit §22

**Regel 3 (>=2,0x) bleibt ueber alle gemessenen Zellen unerreicht.** Die
beste Zelle ist N=64 ORT-CUDA (1,545x) -- UNTER, nicht ueber der Schwelle,
und die vorab dokumentierte Erwartung ("ORT hebt bei Batch>=128 deutlich
ab") ist durch die N=128-ORT-CUDA-Messung explizit WIDERLEGT, nicht nur
unbestaetigt: Faktor UND Aggregatdurchsatz fallen leicht von N=64 auf
N=128, trotz gestiegenem mittlerem Batch und trotz erreichtem
128er-Ceiling. tract N=128 bleibt unentschieden (Mess-Infrastruktur-
Grenze, keine Code-Ursache) -- die vorliegenden Zellen genuegen aber
bereits, um die Auftrags-Kernfrage ("erreicht Weg B/Async+Batcher+ORT-CUDA
Regel 3 bei produktionsnahem Batch") mit **Nein** zu beantworten, auf
Basis GEMESSENER, nicht extrapolierter Zahlen fuer die entscheidenden
ORT-Zellen.

## 23. TRAEGER-SKALIERUNG, DER FAIRE SYNC-VERGLEICH -- UND DAS ENDVERDIKT

Nutzer-Auftrag: die Maschine ist frei (Korpus-Generierung abgeschlossen,
keine parallelen Agenten-Lasten). Drei Zellen: (1) N=128 ORT-CUDA mit 11
statt 8 Traegern (6C/12T Ryzen 3600X, GEPRÜFT per
`Get-CimInstance Win32_Processor`: 6 Kerne/12 logische Prozessoren -- 11
Traeger + 1 Sammel-Faden = volle Breite), (2) Sync FRISCH mit 11 UND 12
Faeden (40 Partien, wie der bisherige Bezug), staerkerer Arm wird ab jetzt
der Regel-3-Nenner, (3) Bonus: zwei gleichzeitige Async+ORT-Prozesse
(je 5-6 Traeger, je N=64) gegen den besten Einzelprozess.

### Zelle 2 zuerst: der Sync-Nenner aendert sich DRASTISCH

| Faeden | fertig | Wandzeit | Partien/h |
| --- | ---: | ---: | ---: |
| 8 (§20-22, alter Bezug) | 40/40 | 579,36 s | 248,5 |
| **11** | 40/40 | 272,46 s | **528,5** |
| 12 | 40/40 | 388,28 s | 370,9 |

**11 Faeden schlaegt 12** (528,5 gegen 370,9/h) -- bei 6 physischen Kernen/12
logischen Prozessoren laesst 11 einen logischen Prozessor fuer OS/Rayon-
Koordination frei, waehrend 12 die Maschine voll saettigt und dadurch
LANGSAMER wird, nicht schneller. **11 Faeden mit 528,5 Partien/h ist ab
sofort der Regel-3-Nenner.** Der Sprung gegenueber dem alten 248,5er-Bezug
(2,126x) ist NICHT durch mehr Faeden allein erklaerbar (nur 8->11, +37,5%)
-- er zeigt, dass die §20-22-Messungen unter spuerbarer Maschinenlast
(parallele Agenten/Sitzungen zu dieser Zeit) liefen, waehrend diese Messung
auf einer freien Maschine lief. **Alle Regel-3-Faktoren aus §20-22 waren
dadurch zu GUENSTIG fuer Weg B** (der Nenner war kuenstlich niedrig) --
dieser Abschnitt korrigiert das.

### Zelle 1: Traeger-Skalierung bestaetigt sich, reicht aber nicht

| Traeger | Partien/h | mittl. Batch | Faktor ggue. NEUEM Nenner (528,5) | Faktor ggue. ALTEM Nenner (248,5) |
| --- | ---: | ---: | ---: | ---: |
| 8 (§22) | 365,5 | 81,70 | 0,692x | 1,471x |
| **11** | **475,2** | 87,29 | **0,899x** | 1,912x |

Traeger-Skalierung wirkt wie vorab erwartet: 11/8=1,375x mehr Traeger ->
475,2/365,5=1,300x mehr Durchsatz, ohne den Batch zu verschlechtern (87,29
gegen 81,70, beide erreichen den 128er-Deckel). **Gegen den ALTEN Bezug
waere das mit 1,912x knapp UNTER Regel 3 gelandet -- gegen den korrekten,
frischen Nenner sind es nur 0,899x, UNTER Paritaet.** Genau dieser
Unterschied ist der Grund, warum Zelle 2 zuerst gemessen werden musste.

### Zelle 3 (Bonus): zwei kleine CUDA-Kontexte schlagen einen grossen

Zwei gleichzeitige, VOLLSTAENDIG unabhaengige Prozesse (eigener `Net::
load_auto`, eigene ORT-CUDA-Session, eigener Sammel-Faden) -- Traeger und
Gesamt-Partienzahl exakt auf die Zelle-1-Bestwerte aufgeteilt (6+5=11
Traeger, 2x64=128 Partien):

| Prozess | Traeger | Partien/h | Wandzeit |
| --- | ---: | ---: | ---: |
| A | 6 | 373,1 | 617,54 s |
| B | 5 | 331,5 | 694,96 s |
| **Aggregat** (128 Partien / laengere Wandzeit) | 11 (gesamt) | **663,0** | 694,96 s |

**Aggregat schlaegt den besten Einzelprozess** (663,0 gegen 475,2/h,
**1,395x**) -- bei IDENTISCHER Gesamt-Traeger- und Gesamt-Partienzahl. Die
im Auftrag vorab formulierte Deutungsregel ("ein Gewinn muss aus der
GPU-Entlastung kommen; scheitert die Zelle an CUDA-Kontext-Kosten, ist das
der Befund") faellt damit auf die POSITIVE Seite: **kein Scheitern an
CUDA-Kontext-Kosten** -- im Gegenteil, zwei kleinere, unabhaengige
Sammel-Faeden/CUDA-Kontexte sind effizienter als einer, der 128
gleichzeitige Partien buendeln muss. Plausible (NICHT gepruefte, siehe
unten) Erklaerung: der EINE Sammel-Faden bei N=128 muss VIEL mehr
gleichzeitig eintreffende Anfragen sequenziell abarbeiten und serialisiert
dadurch staerker, als zwei Sammel-Faeden, die je nur 64 Anfragen-Quellen
bedienen -- die Aufteilung selbst reduziert Kontention, unabhaengig von der
GPU. Gegen den NEUEN Sync-Nenner: **663,0/528,5 = 1,255x** -- die beste
Zelle in §20-23, aber immer noch UNTER 2,0x.

### Regel-3-Endverdikt (Massstab: >=2,0x gegen den STAERKSTEN Sync-Arm,
### 528,5 Partien/h)

| Zelle | Partien/h | Faktor |
| --- | ---: | ---: |
| N=1 ORT-CUDA (§21) | 85,1 | 0,161x |
| N=16 ORT-CUDA (§21) | 221,0 | 0,418x |
| N=64 ORT-CUDA, 8 Traeger (§22) | 383,8 | 0,726x |
| N=128 ORT-CUDA, 8 Traeger (§22) | 365,5 | 0,692x |
| N=128 ORT-CUDA, 11 Traeger (§23) | 475,2 | 0,899x |
| **Doppel-Prozess-Aggregat, 6+5 Traeger (§23)** | **663,0** | **1,255x (bester Wert)** |

**Keine Zelle erreicht 2,0x.** Die beste bisher gemessene Konfiguration
(zwei unabhaengige Prozesse) liegt bei 1,255x gegen den korrekten,
frisch gemessenen Sync-Nenner -- deutlich besser als jede
Einzelprozess-Zelle, aber weniger als die Haelfte der Deckungsschwelle.

**Verdikt gemaess der vorab festgelegten Regel: Weg B (GPU-Inferenzpfad)
wird NICHT Standard fuer v22+ -- geschlossen bis zum groesseren Netz.**

### Was NICHT geprüft ist

- Die genaue Ursache, WARUM zwei kleinere Sammel-Faeden effizienter sind
  als einer grosser (Zelle 3) -- keine Zeitzerlegung (`fill_wait_ns`/
  `eval_ns`) fuer diesen spezifischen Vergleich durchgefuehrt, nur die
  Endzahlen. Plausible Hypothese (Kontention im geteilten Sammel-Faden
  bei N=128) NICHT instrumentell bestaetigt.
  - Ob mehr als zwei Prozesse (3, 4...) den Trend fortsetzen oder an
    einer anderen Grenze (GPU-Speicher, PCIe-Bandbreite, CUDA-Kontext-
    Limit) gaeben wuerden -- nicht gefahren.
- Ob ein groesseres Netz (wie im Verdikt referenziert) die Kennlinie
  verschieben wuerde -- ausserhalb des Auftragsumfangs dieser Messreihe,
  reine Forward-Reference auf die Verdikt-Regel selbst.
- N=128 tract mit 11 Traegern -- nicht gefahren, da tract bereits bei 8
  Traegern (§22) nicht innerhalb der Mess-Infrastruktur-Grenzen
  abschliessbar war; ein Versuch mit MEHR Traegern (potenziell noch
  laengere Wandzeit durch mehr Nebenlaeufigkeit auf demselben
  Sammel-Faden) haette dasselbe Problem wahrscheinlich verschaerft, nicht
  geloest.
- Nur EIN Seed je Zelle (Zeitbudget, wie in §20-22).

### Eigene Entscheidungen (nicht vorgegeben)

- Zelle 2 (Sync-Nenner) VOR Zelle 1 gefahren, obwohl im Auftrag als "1."
  und "2." nummeriert -- der neue Nenner war fuer die EINORDNUNG jeder
  weiteren Zelle noetig, nicht erst am Ende.
- Traeger-Aufteilung 6+5 (nicht 5+6 oder 5,5+5,5) fuer Zelle 3 -- addiert
  sich exakt auf die Zelle-1-Traegerzahl (11) fuer einen sauberen
  Gesamt-Ressourcen-Vergleich; Reihenfolge (welcher Prozess 6 bekommt)
  beliebig.
- Verschiedene `--seed`-Werte fuer die beiden Zelle-3-Prozesse (20260814
  bzw. 314159265) -- vermeidet identische Partie-Sequenzen zwischen den
  beiden Prozessen, ohne die Wandzeit-Messung zu beeinflussen.
- Aggregat-Partien/h in Zelle 3 als `(Partien A + Partien B) /
  max(Wandzeit A, Wandzeit B)` definiert, nicht als Summe der
  Einzel-Partien/h -- letzteres wuerde einen Prozess, der frueher fertig
  wird, faelschlich so behandeln, als liefe er in der "toten" Zeit nach
  seinem Ende weiter mit.
- N=256 (aus §22 bereits per Bedingung "nur falls 128 nicht saettigt"
  uebersprungen) hier NICHT erneut aufgegriffen -- die Traeger-Skalierung
  (Zelle 1) und die Doppel-Prozess-Zelle (Zelle 3) beantworten die
  Kernfrage bereits eindeutig, ohne weitere Batch-Eskalation.

### Fazit §23

Die Maschinenlast-Korrektur (Zelle 2) ist der wichtigste Einzelbefund
dieses Abschnitts: sie zeigt, dass JEDER Regel-3-Faktor aus §20-22 gegen
einen kuenstlich niedrigen Nenner gemessen wurde. Nach der Korrektur bleibt
Weg B trotz aller Verbesserungen (Condvar-Fix §21, Traeger-Skalierung UND
der ueberraschende Doppel-Prozess-Gewinn hier) bei **maximal 1,255x** --
weniger als zwei Drittel der 2,0x-Schwelle. Verdikt gemaess vorab
festgelegter Regel: **Weg B (GPU-Inferenzpfad) bleibt geschlossen, bis ein
groesseres Netz die Kennlinie veraendert.**

## §23 PLAN: Die letzten drei Hebel (vorregistriert 2026-08-14, Nutzer-Auftrag)

Befund-Basis §22: die GPU laeuft bei ~10 % (5.950 Evals/s gemessen gegen
~61.000 der Kennlinie bei Batch 128) -- der Deckel ist die CPU-seitige
Blatt-Erzeugung der 8 Traeger-Threads, nicht die Karte. Drei Zellen, LAUFEN
ERST NACH ABSCHLUSS der Korpus-Generierung (Kern-Konkurrenz wuerde beide
Messungen verderben):

1. **Traeger-Skalierung**: N=128 ORT mit 11-12 Traegern statt 8
   (Praezedenz Threads 8->11 = 1,39x, stabil). Erwartung vorab: Blatt-
   Erzeugung und damit Partien/h steigen etwa mit dem Traeger-Faktor,
   solange die GPU Luft hat (sie hat 10x).
2. **Fairer Endvergleich bei vollen Kernen**: Sync 11-12 Threads (frisch
   messen -- rechnerisch ~345/h) GEGEN Async+ORT 11-12 Traeger x N=128.
   DAS ist die eigentliche Entscheidungszelle: Regel 3 (>=2,0x) gilt ab
   jetzt gegen den STAERKSTEN Sync-Arm, nicht gegen den 8-Thread-Bezug --
   alles andere waere ein geschoenter Nenner.
3. **Bonus, zwei Flotten teilen die GPU** (Nutzer: "takte auch die bonus
   idee ein"): zwei unabhaengige Async+ORT-Prozesse (je halbe Traeger,
   je N=64-128) gleichzeitig; Messgroesse ist der AGGREGAT-Durchsatz
   beider gegen den besten Einzelprozess. Vorab-Risiko benannt: die
   9x-Verlangsamung aus der GPU-Teilung mit einem SPIEL (2D-Encoder-
   Phase-2-Befund) betraf Rendering-Konkurrenz -- ob zwei reine
   CUDA-Compute-Prozesse sich vertragen, ist UNGEMESSEN; genau das
   klaert die Zelle. Scheitert sie an Kontext-Switch-Kosten, ist das ein
   Befund, kein Fehlschlag der Messung.

Verdikt-Regel vorab: Gewinnt eine Konfiguration >=2,0x gegen den staerksten
Sync-Arm (Zelle 2 definiert ihn), wird der GPU-Pfad fuer KUENFTIGE
Generierungslaeufe (v22+) der Standard; sonst ist Weg B geschlossen, bis ein
groesseres Netz den Amdahl-Anteil der Inferenz verschiebt (der ORT-Vorsprung
je Batch, 10-21x, bleibt dann die stehende Vorleistung).

**Hardware-Nachtrag zu §23 (gemessen 2026-08-14, Nutzer-Nachfrage)**: CPU ist
ein AMD Ryzen 5 3600X — **6 physische Kerne / 12 logische Prozessoren**
(Win32_Processor, os.cpu_count()=12). Die 8-Thread-Konvention lief also schon
immer ueber der physischen Kernzahl (SMT); der 8->11-Praezedenzfall (1,39x)
ist damit als SMT-Gewinn eingeordnet, nicht als Kern-Skalierung. Fuer
Zelle 1/2 gilt: 11 Traeger + 1 Sammel-Faden = 12 = volle logische Breite,
mehr ist strukturell sinnlos; der staerkste Sync-Arm ist entsprechend
11-12 Threads. Fuer Zelle 3 (zwei Flotten) teilen sich die Prozesse dieselben
12 logischen Prozessoren -- der Aggregat-Gewinn muss also aus der GPU-
Entlastung kommen, nicht aus mehr CPU (vorab notiert, damit ein Nullergebnis
richtig gelesen wird).
