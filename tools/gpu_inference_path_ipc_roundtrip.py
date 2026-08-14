# -*- coding: utf-8 -*-
"""Schritt 1 (Weg A) aus `evaluations/PREREG_gpu_inference_path.md` Abschnitt 6.

Anlass: Abschnitt 3 (Weg A, Cross-Language-Queue Rust -> Python/torch) und
Abschnitt 4 (Entscheidungsregel 1) verlangen VOR jeder Architekturentscheidung
zwei Zahlen: (a) die Merkmalsgroesse je Position -- Anfrage UND Antwort, aus
dem CODE, nicht aus dem README -- und (b) die IPC-Rundlaufzeit fuer Batch 256
ueber mindestens zwei Kanaele: eine naive Serialisierungs-Variante und eine
Shared-Memory-Variante, jeweils LEER (nur Signalisierung) und MIT Nutzlast in
der berechneten Groesse.

Vergleichsmarke (Abschnitt 4, Regel 1): die Rundlaufzeit fuer Batch 256 muss
unter einem DRITTEL der GPU-Zeit DESSELBEN Batches liegen. Die GPU-Zeit kommt
NICHT aus einer neuen Messung, sondern aus der schon vorhandenen
`evaluations/gpu_batch_throughput.json` (torch/CUDA, RTX 3060) -- die hat den
Batch-256-Punkt bereits: 78.896,47 Evals/s -> 256/78896,47 = 3,2454 ms.
(Die in der Vorregistrierung genannten 3,05 ms/3,15 ms sind die Nachbarpunkte
Batch 128/512 -- Kontext fuer die Kennlinie, aber nicht der fuer Regel 1
einschlaegige Wert; der ist batch-eigen.)

Merkmalsgroesse (float32, Quellen im JSON-Feld "feature_size.sources" und im
Bericht):
    Anfrage = Planes[76,6,6] (2736 Elemente) + Flat[708]  = 3444 Elemente/Pos.
    Antwort = Policy[406] + Value[1] + Moon[5] + Points[1] = 413 Elemente/Pos.

Methode: EIN Kindprozess (multiprocessing, spawn) simuliert den Python/torch-
Server, der Elternprozess den Rust-Client. Zwei Kanaele:

  - "socket": TCP-Loopback (127.0.0.1), feste Nachrichtengroesse je Modus.
    Die Nutzlast wird als `ndarray.tobytes()`/`np.frombuffer()` seriealisiert
    -- die minimal noetige Serialisierung. Ein echtes Cross-Prozess-Protokoll
    (Laengenpraefix, Feldformat wie protobuf) waere zusaetzlicher Overhead,
    hier NICHT gemessen -- diese Messung ist damit eher eine UNTERGRENZE fuer
    den naiven Kanal.
  - "shm": `multiprocessing.shared_memory.SharedMemory` fuer die Nutzlast,
    Signalisierung ("Doorbell") ueber ein `multiprocessing.Pipe`
    (send_bytes/recv_bytes, kein Pickle, keine Nutzlast im Pipe selbst).

"Leer" bedeutet NICHT ein Null-Byte-Nachrichtenpaar (das wuerde keinen
tatsaechlichen Rundlauf erzwingen -- der Server koennte ohne jede Wartezeit
vorauslaufen). Stattdessen: eine 8-Byte-Kontrollnachricht je Richtung beim
Socket-Kanal, bzw. ein Doorbell ohne Schreiben in den grossen Puffer beim
Shared-Memory-Kanal. So bleibt in jeder Iteration ein echter Prozess-
uebergreifender Rundlauf erzwungen, nur ohne die grosse Nutzlast-Kopie.

Kein Torch/keine GPU in dieser Messung -- es geht um Bytes/Latenz der
IPC-Mechanik, nicht um Inferenz (PREREG Abschnitt 3: "Nutzlast darf
synthetisch sein"). GPU-Verfuegbarkeit dieser Maschine ist fuer DIESE Messung
irrelevant, wird aber informativ mitgeschrieben (Feld "environment").

Nicht vom Auftrag vorgegeben (siehe Bericht "jede Entscheidung, die ich nicht
vorgegeben habe"): der Client-Prozess ist hier Python, nicht Rust (der Server
ist es ohnehin, da Weg A Python/torch verlangt). Das ist vermutlich eine
UNGUENSTIGE Annahme fuer den naiven Kanal -- Python-`socket`/`Connection`-
Aufrufe tragen Interpreter-/GIL-/Objektallokations-Overhead je Nachricht, den
ein Rust-Client nicht haette. UNGEPRUEFT (nicht in Rust nachgemessen): die
hier gemessene Zahl ist eher ein oberes Limit als eine Unterschaetzung.

Aufruf:
    python tools/gpu_inference_path_ipc_roundtrip.py
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import socket
import statistics
import time
from multiprocessing import shared_memory
from multiprocessing.connection import Connection
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent

# --- Merkmalsgroesse, aus dem CODE (Fundstellen siehe feature_size_report) ---
PLANES_C, PLANES_H, PLANES_W = 76, 6, 6   # engine/src/features.rs:767; neural_net.py:322/392
FLAT_SIZE = 708                            # config.py:38; engine/src/features.rs:18
POLICY_WIDTH = 406                         # config.py:43; engine/src/net_mcts.rs:42
VALUE_WIDTH = 1                            # neural_net.py:2418 Linear(...,1)+Tanh (out[1])
MOON_WIDTH = 5                             # neural_net.py:2309 moon_order_head Linear(32,5); net.rs:4 "moon_logits[5]"
POINTS_WIDTH = 1                           # neural_net.py:2363 (aktiv, da POINTS_DIST_BINS=0, config.py:134)
BYTES_PER_ELEM = 4                          # float32 -- torch-Default-Dtype, keine set_default_dtype-Ueberschreibung gefunden

CONTROL_BYTES = 8   # "leer"-Kontrollnachricht (Socket-Kanal) je Richtung


def feature_size_report(batch: int) -> dict:
    req_elems_per_pos = PLANES_C * PLANES_H * PLANES_W + FLAT_SIZE
    resp_elems_per_pos = POLICY_WIDTH + VALUE_WIDTH + MOON_WIDTH + POINTS_WIDTH
    return {
        "batch": batch,
        "dtype": "float32",
        "request": {
            "planes_elements": PLANES_C * PLANES_H * PLANES_W,
            "flat_elements": FLAT_SIZE,
            "elements_per_position": req_elems_per_pos,
            "bytes_per_position": req_elems_per_pos * BYTES_PER_ELEM,
            "bytes_batch": req_elems_per_pos * BYTES_PER_ELEM * batch,
        },
        "response": {
            "policy_elements": POLICY_WIDTH,
            "value_elements": VALUE_WIDTH,
            "moon_elements": MOON_WIDTH,
            "points_elements": POINTS_WIDTH,
            "elements_per_position": resp_elems_per_pos,
            "bytes_per_position": resp_elems_per_pos * BYTES_PER_ELEM,
            "bytes_batch": resp_elems_per_pos * BYTES_PER_ELEM * batch,
        },
        "sources": [
            "engine/src/features.rs:767 NUM_PLANES_CHANNELS=76",
            "engine/py/neural_net.py:322 NUM_PLANES_CHANNELS=2*16+19+25=76; :392 state_to_planes -> [76,6,6]",
            "engine/src/features.rs:18 INPUT_SIZE=708; config.py:38 INPUT_SIZE=708",
            "engine/src/features.rs:911-912 Kombi-Layout Planes(2736 Werte) + Flat(708 Werte) = 3444, Vec<f32>",
            "config.py:43 NUM_ACTIONS=406; engine/src/net_mcts.rs:42 NUM_ACTIONS=406",
            "engine/py/neural_net.py:2418 value_head letzter Linear(value_hidden,1)+Tanh",
            "engine/py/neural_net.py:2309 moon_order_head letzter Linear(32,5); engine/src/net.rs:4 'moon_logits[5]'",
            "engine/py/neural_net.py:2363 points_head letzter Linear(value_hidden,1)+Tanh (Skalar-Zweig, POINTS_DIST_BINS=0 in config.py:134)",
            "engine/src/net.rs:286-289 (eval()) out[0..3] = policy,value,moon,points -- exakt die 4, die Rust liest",
        ],
    }


def load_gpu_reference() -> dict:
    """Liest den vorhandenen Batch-256-Punkt aus
    `evaluations/gpu_batch_throughput.json` (torch/CUDA-Messung, RTX 3060,
    ungeaendert -- KEINE Neumessung). Entscheidungsregel 1 verlangt die
    GPU-Zeit DESSELBEN Batches (256), nicht die Nachbarpunkte 128/512."""
    path = REPO / "evaluations" / "gpu_batch_throughput.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    evals = data["evals_per_s"]
    gpu_name = data["gpu"]

    def ms_for(batch_key: str) -> float:
        return (int(batch_key) / evals[batch_key]) * 1000.0

    return {
        "source": str(path.relative_to(REPO)).replace("\\", "/"),
        "gpu": gpu_name,
        "evals_per_s_batch128": evals["128"],
        "evals_per_s_batch256": evals["256"],
        "evals_per_s_batch512": evals["512"],
        "gpu_time_ms_batch128": ms_for("128"),
        "gpu_time_ms_batch256": ms_for("256"),
        "gpu_time_ms_batch512": ms_for("512"),
        "decision_basis_ms": ms_for("256"),
        "decision_threshold_ms_one_third": ms_for("256") / 3.0,
    }


# ------------------------------------------------------------------ Socket --

def _recv_exact(conn: socket.socket, n: int) -> None:
    remaining = n
    while remaining > 0:
        chunk = conn.recv(min(remaining, 1 << 20))
        if not chunk:
            raise ConnectionError("Socket-Verbindung vor Nachrichtenende geschlossen")
        remaining -= len(chunk)


def _socket_server(port_q: "mp.Queue", req_bytes: int, resp_bytes: int, n_iters: int) -> None:
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    port_q.put(srv.getsockname()[1])
    conn, _addr = srv.accept()
    conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    resp_buf = bytes(resp_bytes)
    try:
        for _ in range(n_iters):
            _recv_exact(conn, req_bytes)
            conn.sendall(resp_buf)
    finally:
        conn.close()
        srv.close()


def measure_socket(req_bytes: int, resp_bytes: int, reps: int, warmup: int) -> list[float]:
    n_iters = reps + warmup
    port_q: "mp.Queue" = mp.Queue()
    proc = mp.Process(target=_socket_server, args=(port_q, req_bytes, resp_bytes, n_iters), daemon=True)
    proc.start()
    port = port_q.get(timeout=10)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    for _attempt in range(100):
        try:
            sock.connect(("127.0.0.1", port))
            break
        except (ConnectionRefusedError, OSError):
            time.sleep(0.02)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    req_payload = np.random.rand(max(req_bytes, 1) // 4 or 1).astype(np.float32).tobytes()[:req_bytes] \
        if req_bytes else b""
    if req_bytes and len(req_payload) < req_bytes:
        req_payload = req_payload + bytes(req_bytes - len(req_payload))

    times = []
    for i in range(n_iters):
        t0 = time.perf_counter()
        sock.sendall(req_payload)
        _recv_exact(sock, resp_bytes)
        dt = time.perf_counter() - t0
        if i >= warmup:
            times.append(dt)
    sock.close()
    proc.join(timeout=5)
    return times


# --------------------------------------------------------------- Shared Mem --

def _shm_server(req_name: str, resp_name: str, req_bytes: int, resp_bytes: int,
                 conn: Connection, n_iters: int, do_payload: bool) -> None:
    req_shm = shared_memory.SharedMemory(name=req_name) if req_bytes else None
    resp_shm = shared_memory.SharedMemory(name=resp_name) if resp_bytes else None
    resp_fill = None
    if do_payload and resp_shm is not None:
        resp_fill = np.zeros(resp_bytes // 4, dtype=np.float32)
    try:
        for _ in range(n_iters):
            conn.recv_bytes()  # Doorbell: Anfrage liegt (ggf.) bereits im Shared-Memory-Puffer
            if resp_fill is not None:
                view = np.ndarray(resp_fill.shape, dtype=np.float32, buffer=resp_shm.buf)
                view[:] = resp_fill
            conn.send_bytes(b"\x01")  # Doorbell zurueck
    finally:
        if req_shm is not None:
            req_shm.close()
        if resp_shm is not None:
            resp_shm.close()


def measure_shm(req_bytes: int, resp_bytes: int, reps: int, warmup: int, do_payload: bool) -> list[float]:
    n_iters = reps + warmup
    req_shm = shared_memory.SharedMemory(create=True, size=max(req_bytes, 1))
    resp_shm = shared_memory.SharedMemory(create=True, size=max(resp_bytes, 1))
    parent_conn, child_conn = mp.Pipe(duplex=True)
    proc = mp.Process(
        target=_shm_server,
        args=(req_shm.name, resp_shm.name, req_bytes, resp_bytes, child_conn, n_iters, do_payload),
        daemon=True,
    )
    proc.start()
    child_conn.close()  # Elternprozess braucht sein Ende nicht

    req_fill = None
    if do_payload and req_bytes:
        req_fill = np.random.rand(req_bytes // 4).astype(np.float32)

    times = []
    for i in range(n_iters):
        t0 = time.perf_counter()
        if req_fill is not None:
            view = np.ndarray(req_fill.shape, dtype=np.float32, buffer=req_shm.buf)
            view[:] = req_fill
        parent_conn.send_bytes(b"\x01")
        parent_conn.recv_bytes()
        dt = time.perf_counter() - t0
        if i >= warmup:
            times.append(dt)
    proc.join(timeout=5)
    req_shm.close()
    req_shm.unlink()
    resp_shm.close()
    resp_shm.unlink()
    return times


# ------------------------------------------------------------------- Report --

def summarize(times_s: list[float]) -> dict:
    ms = [t * 1000.0 for t in times_s]
    return {
        "n": len(ms),
        "median_ms": statistics.median(ms),
        "mean_ms": statistics.mean(ms),
        "stdev_ms": statistics.stdev(ms) if len(ms) > 1 else 0.0,
        "min_ms": min(ms),
        "max_ms": max(ms),
    }


def environment_info() -> dict:
    info = {"cpu_count": None, "cuda_available": None, "cuda_device": None, "note":
             "GPU-Status ist fuer DIESE Messung irrelevant (reine IPC-Latenz, keine Inferenz) -- nur informativ."}
    try:
        import os
        info["cpu_count"] = os.cpu_count()
    except Exception:
        pass
    try:
        import torch
        info["cuda_available"] = bool(torch.cuda.is_available())
        if info["cuda_available"]:
            info["cuda_device"] = torch.cuda.get_device_name(0)
    except Exception as exc:  # torch fehlt/Import schlaegt fehl
        info["cuda_available"] = f"unbekannt (torch-Import fehlgeschlagen: {exc})"
    return info


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--batch", type=int, default=256)
    ap.add_argument("--reps", type=int, default=200)
    ap.add_argument("--warmup", type=int, default=20)
    ap.add_argument("--out", default="evaluations/gpu_inference_path_ipc_roundtrip.json")
    args = ap.parse_args()

    fsize = feature_size_report(args.batch)
    req_bytes = fsize["request"]["bytes_batch"]
    resp_bytes = fsize["response"]["bytes_batch"]

    print(f"Merkmalsgroesse je Position: Anfrage {fsize['request']['elements_per_position']} Elemente "
          f"({fsize['request']['bytes_per_position']} B), Antwort {fsize['response']['elements_per_position']} "
          f"Elemente ({fsize['response']['bytes_per_position']} B)")
    print(f"Batch {args.batch}: Anfrage {req_bytes:,} B ({req_bytes/1024:.1f} KiB), "
          f"Antwort {resp_bytes:,} B ({resp_bytes/1024:.1f} KiB)")

    gpu_ref = load_gpu_reference()
    threshold_ms = gpu_ref["decision_threshold_ms_one_third"]
    print(f"\nGPU-Referenz (unveraendert aus {gpu_ref['source']}, {gpu_ref['gpu']}): "
          f"Batch {args.batch} = {gpu_ref['decision_basis_ms']:.4f} ms "
          f"(Batch128={gpu_ref['gpu_time_ms_batch128']:.4f} ms, Batch512={gpu_ref['gpu_time_ms_batch512']:.4f} ms)")
    print(f"Entscheidungsschwelle (1/3 der Batch-{args.batch}-GPU-Zeit): {threshold_ms:.4f} ms")

    channels: dict[str, dict] = {}

    print("\n-- Socket (TCP-Loopback, raw bytes) --")
    empty = summarize(measure_socket(CONTROL_BYTES, CONTROL_BYTES, args.reps, args.warmup))
    payload = summarize(measure_socket(req_bytes, resp_bytes, args.reps, args.warmup))
    channels["socket"] = {"empty": empty, "payload": payload}
    print(f"  leer     (({CONTROL_BYTES} B <-> {CONTROL_BYTES} B): median {empty['median_ms']:.4f} ms, "
          f"stdev {empty['stdev_ms']:.4f} ms, n={empty['n']}")
    print(f"  Nutzlast ({req_bytes/1024:.0f} KiB <-> {resp_bytes/1024:.0f} KiB): "
          f"median {payload['median_ms']:.4f} ms, stdev {payload['stdev_ms']:.4f} ms, n={payload['n']}")

    print("\n-- Shared Memory (multiprocessing.shared_memory + Pipe-Doorbell) --")
    empty_shm = summarize(measure_shm(req_bytes, resp_bytes, args.reps, args.warmup, do_payload=False))
    payload_shm = summarize(measure_shm(req_bytes, resp_bytes, args.reps, args.warmup, do_payload=True))
    channels["shm"] = {"empty": empty_shm, "payload": payload_shm}
    print(f"  leer     (nur Doorbell, kein Puffer-Schreiben): median {empty_shm['median_ms']:.4f} ms, "
          f"stdev {empty_shm['stdev_ms']:.4f} ms, n={empty_shm['n']}")
    print(f"  Nutzlast ({req_bytes/1024:.0f} KiB <-> {resp_bytes/1024:.0f} KiB memcpy + Doorbell): "
          f"median {payload_shm['median_ms']:.4f} ms, stdev {payload_shm['stdev_ms']:.4f} ms, n={payload_shm['n']}")

    verdicts = {}
    print(f"\nRegel 1 (Weg A gedeckt <=> Rundlauf < {threshold_ms:.4f} ms):")
    for name, res in channels.items():
        med = res["payload"]["median_ms"]
        covered = med < threshold_ms
        margin = threshold_ms / med if med > 0 else float("inf")
        verdicts[name] = {"covered": covered, "median_ms": med, "threshold_ms": threshold_ms, "margin_x": margin}
        status = "GEDECKT" if covered else "NICHT GEDECKT"
        print(f"  {name:10s}: median {med:.4f} ms vs Schwelle {threshold_ms:.4f} ms -> {status} "
              f"(Faktor {margin:.2f}x{'unter' if covered else 'ueber'} der Schwelle)")

    any_covered = any(v["covered"] for v in verdicts.values())
    overall = ("Weg A ist nach Regel 1 GEDECKT (mind. ein Kanal unter der Schwelle)."
               if any_covered else
               "Weg A ist nach Regel 1 NICHT GEDECKT (kein gemessener Kanal unter der Schwelle).")
    print(f"\nGESAMTURTEIL: {overall}")

    out = {
        "batch": args.batch,
        "reps": args.reps,
        "warmup": args.warmup,
        "feature_size": fsize,
        "gpu_reference": gpu_ref,
        "channels": channels,
        "verdicts": verdicts,
        "overall_covered": any_covered,
        "overall_verdict": overall,
        "environment": environment_info(),
    }
    out_path = REPO / args.out
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nErgebnis: {out_path}")
    return 0


if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
    raise SystemExit(main())
