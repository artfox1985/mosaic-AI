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
