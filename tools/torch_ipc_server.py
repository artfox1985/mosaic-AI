# -*- coding: utf-8 -*-
"""Weg A (`evaluations/PREREG_gpu_inferenzpfad.md` Abschnitt 3): Server-Seite
des optionalen Torch/CUDA-IPC-Kanals. Gegenstueck zu `engine/src/net_ipc.rs`
(Rust-Client) -- dort auch die vollstaendige Architektur-Begruendung
(Nutzlast in einer speicherabgebildeten Datei, Signalisierung ueber einen
TCP-Loopback-Socket).

Nutzlast-Vertrag (siehe `evaluations/gpu_inferenzpfad_ipc_roundtrip.json`,
Feld "feature_size" -- Quellen dort aufgelistet):
    Anfrage  = Planes[76,6,6] (2736 Elemente) + Flat[708]     = 3444 Elemente/Pos.
    Antwort  = Policy[406] + Value[1] + Moon[5] + Points[1]   =  413 Elemente/Pos.
Beide float32, LE (native Byteordnung auf x86_64 -- Rust und dieser Server
laufen auf derselben Maschine).

Torch-Modell-Aufruf spiegelt `tools/gpu_batch_throughput.py::measure` (SELBE
`model(planes, flat)`-Signatur, siehe `neural_net.py::Mosaic2DNet.forward`)
-- NICHT neu erfunden, die Weg-A-Begruendung in der Vorregistrierung stuetzt
sich genau auf jene Messung, also muss der Inferenzaufruf hier identisch
sein, sonst gilt die Kennlinie nicht mehr fuer diesen Server.

Protokoll je Anfrage (EIN TCP-Client, sequenziell -- keine Parallelitaet
noetig, siehe PREREG §5: die Verschraenkungs-Mechanik ist NICHT Teil dieses
Auftrags):
    Client -> Server (8 Bytes):  batch_n:u32 LE, input_len:u32 LE
    Server -> Client (12 Bytes): status:u32 LE, batch_n_echo:u32 LE, err_len:u32 LE
                                 (+ err_len Bytes UTF-8-Fehlertext, NUR wenn status!=0)
    Bei status==0 liegen die Ergebnisse im Response-Puffer (siehe unten).

Aufruf:
    python tools/torch_ipc_server.py --model models/alphazero_v20_2d_opp_brierbest.pth
"""
from __future__ import annotations

import argparse
import mmap
import os
import socket
import struct
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "engine" / "py"))

PLANES_C, PLANES_H, PLANES_W = 76, 6, 6          # features.rs:767; neural_net.py:322/392
FLAT_SIZE = 708                                   # config.py:38; features.rs:18
PLANES_LEN = PLANES_C * PLANES_H * PLANES_W       # 2736
INPUT_LEN = PLANES_LEN + FLAT_SIZE                # 3444 -- MUSS zu net_ipc.rs::MAX_INPUT_LEN passen

POLICY_WIDTH = 406                                # config.py:43; net_mcts.rs:42
VALUE_WIDTH = 1
MOON_WIDTH = 5
POINTS_WIDTH = 1
RESP_WIDTH = POLICY_WIDTH + VALUE_WIDTH + MOON_WIDTH + POINTS_WIDTH  # 413 -- MUSS zu net_ipc.rs::RESP_WIDTH passen

MAX_BATCH = 16                                    # MUSS zu net_ipc.rs::MAX_BATCH passen
REQUEST_BUF_BYTES = MAX_BATCH * INPUT_LEN * 4
RESPONSE_BUF_BYTES = MAX_BATCH * RESP_WIDTH * 4

DEFAULT_PORT = 8848
DEFAULT_SHM_DIR = Path(tempfile.gettempdir()) / "mosaic_torch_ipc"


def open_or_create_mmap(path: Path, size: int) -> mmap.mmap:
    """Oeffnet (oder legt an) eine Datei fixer Groesse und bildet sie ab --
    Gegenstueck zu `net_ipc.rs::open_or_create_mmap`. Beide Seiten duerfen
    diese Datei zuerst anlegen (Reihenfolge egal, siehe dortiger Kommentar)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.stat().st_size != size:
        with path.open("wb") as fh:
            fh.truncate(size)
    fh = path.open("r+b")
    return mmap.mmap(fh.fileno(), size)


def recv_exact(conn: socket.socket, n: int) -> bytes:
    buf = bytearray(n)
    view = memoryview(buf)
    got = 0
    while got < n:
        chunk = conn.recv_into(view[got:], n - got)
        if chunk == 0:
            raise ConnectionError("Verbindung vor Nachrichtenende geschlossen")
        got += chunk
    return bytes(buf)


def send_error(conn: socket.socket, status: int, message: str) -> None:
    msg_bytes = message.encode("utf-8")
    conn.sendall(struct.pack("<III", status, 0, len(msg_bytes)))
    if msg_bytes:
        conn.sendall(msg_bytes)


def build_model(path: Path, device: str):
    import torch

    import neural_net as nn_mod

    ckpt = torch.load(path, map_location="cpu", weights_only=False)
    model, encoder = nn_mod.build_model_from_checkpoint(ckpt)
    if encoder != "2d":
        raise SystemExit(
            f"Checkpoint {path} ist kein 2D-Encoder-Modell (encoder={encoder!r}) -- "
            f"der Nutzlast-Vertrag dieses Servers (Planes+Flat) passt nur zu Mosaic2DNet."
        )
    model.eval().to(device)
    return model, encoder


def serve_one_connection(conn: socket.socket, model, device: str, request_mm: mmap.mmap, response_mm: mmap.mmap) -> None:
    import numpy as np
    import torch

    while True:
        try:
            header = recv_exact(conn, 8)
        except ConnectionError:
            return  # Client hat die Verbindung geschlossen -- zurueck zu accept().
        batch_n, input_len = struct.unpack("<II", header)

        if not (1 <= batch_n <= MAX_BATCH):
            send_error(conn, 1, f"batch_n={batch_n} ausserhalb 1..={MAX_BATCH}")
            continue
        if input_len != INPUT_LEN:
            send_error(conn, 2, f"input_len={input_len}, erwartet {INPUT_LEN} (Planes+Flat)")
            continue

        n_floats = batch_n * input_len
        request_mm.seek(0)
        raw = request_mm.read(n_floats * 4)
        arr = np.frombuffer(raw, dtype="<f4").reshape(batch_n, input_len)

        planes_np = arr[:, :PLANES_LEN].reshape(batch_n, PLANES_C, PLANES_H, PLANES_W).copy()
        flat_np = arr[:, PLANES_LEN:].copy()

        with torch.no_grad():
            planes = torch.from_numpy(planes_np).to(device)
            flat = torch.from_numpy(flat_np).to(device)
            out = model(planes, flat)
            if device == "cuda":
                torch.cuda.synchronize()
            # Reihenfolge = ONNX-Ausgabereihenfolge (neural_net.py::Mosaic2DNet.forward,
            # siehe net.rs::eval() fuer die exakt gleiche 0..3-Extraktion).
            policy = out[0].to("cpu").numpy().astype("<f4")
            value = out[1].to("cpu").numpy().astype("<f4")
            moon = out[2].to("cpu").numpy().astype("<f4")
            points = out[3].to("cpu").numpy().astype("<f4")

        if policy.shape != (batch_n, POLICY_WIDTH):
            send_error(conn, 3, f"policy-Kopfbreite {policy.shape[1]}, erwartet {POLICY_WIDTH}")
            continue

        row = np.concatenate([policy, value, moon, points], axis=1)  # (batch_n, RESP_WIDTH)
        response_mm.seek(0)
        response_mm.write(row.astype("<f4").tobytes())

        conn.sendall(struct.pack("<III", 0, batch_n, 0))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", required=True, help="Pfad zum .pth-Checkpoint (2D-Encoder)")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--shm-dir", default=str(DEFAULT_SHM_DIR))
    ap.add_argument("--device", default=None, help="cuda|cpu (Default: cuda falls verfuegbar)")
    args = ap.parse_args()

    import torch

    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    if device == "cuda" and not torch.cuda.is_available():
        print("WARNUNG: --device cuda angefordert, aber keine CUDA-GPU verfuegbar -- falle auf cpu zurueck.")
        device = "cpu"

    model_path = Path(args.model)
    if not model_path.is_absolute():
        model_path = REPO / model_path
    print(f"Lade {model_path} auf {device} ...")
    model, encoder = build_model(model_path, device)
    print(f"Modell geladen (encoder={encoder}, device={device}).")

    shm_dir = Path(args.shm_dir)
    request_mm = open_or_create_mmap(shm_dir / "request.bin", REQUEST_BUF_BYTES)
    response_mm = open_or_create_mmap(shm_dir / "response.bin", RESPONSE_BUF_BYTES)
    print(f"Shared-Memory-Puffer: {shm_dir} (Anfrage {REQUEST_BUF_BYTES:,} B, Antwort {RESPONSE_BUF_BYTES:,} B)")

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", args.port))
    srv.listen(1)
    print(f"Bereit auf 127.0.0.1:{args.port} (PID {os.getpid()}). Strg+C zum Beenden.")

    try:
        while True:
            conn, _addr = srv.accept()
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            try:
                serve_one_connection(conn, model, device, request_mm, response_mm)
            finally:
                conn.close()
    except KeyboardInterrupt:
        print("\nBeendet.")
        return 0
    finally:
        request_mm.close()
        response_mm.close()
        srv.close()


if __name__ == "__main__":
    raise SystemExit(main())
