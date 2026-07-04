"""
Exportiert ein trainiertes MosaicNet (.pth) nach ONNX für die Rust-Inferenz (Phase B).

  python export_onnx.py --version s100

Erzeugt models/alphazero_<version>.onnx mit 3 Outputs (policy, value, moon) und
dynamischer Batch-Achse. Die Rust-Engine (tract-onnx) lädt diese Datei für den
Network-Modus (Self-Play / Arena).
"""
import sys
import argparse
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent / "engine" / "py"))
from neural_net import MosaicNet  # noqa: E402
from config import INPUT_SIZE, NUM_ACTIONS, MODELS_DIR  # noqa: E402


def export(version: str, opset: int = 13) -> Path:
    pth = MODELS_DIR / f"alphazero_{version}.pth"
    if not pth.exists():
        raise SystemExit(f"❌ Modell nicht gefunden: {pth}")

    ckpt = torch.load(str(pth), map_location="cpu")
    state = ckpt["model_state"]
    hs = state["body.0.weight"].shape[0]
    vh = state["value_head.0.bias"].shape[0]
    in_size = state["body.0.weight"].shape[1]
    if in_size != INPUT_SIZE:
        print(f"⚠️  Modell-Input {in_size} ≠ config.INPUT_SIZE {INPUT_SIZE} — nutze Modellwert.")

    # policy_head.2 existiert nur bei der neuen 2-lagigen Head-Struktur (ab
    # v7). Bei älteren Checkpoints (v1-v6, 1-lagiger Head) policy_hidden=0
    # setzen — das lässt MosaicNet die ALTE, einlagige Architektur exakt
    # nachbauen, damit die echten trainierten Policy-Gewichte passen und
    # geladen werden (NICHT den neuen Head mit Zufallsgewichten auffüllen —
    # das hätte den Policy-Head beim Re-Export stillschweigend kaputt gemacht,
    # siehe Vorfall bei v6).
    ph = state["policy_head.0.bias"].shape[0] if "policy_head.2.weight" in state else 0

    model = MosaicNet(input_size=in_size, num_actions=NUM_ACTIONS, hidden_size=hs, value_hidden=vh,
                       policy_hidden=ph)
    new_state = model.state_dict()
    skipped = [k for k in state if k in new_state and state[k].shape != new_state[k].shape]
    if skipped:
        print(f"⚠️  Shape-Mismatch (alte Head-Architektur?), startet zufällig: {', '.join(skipped)}")
        state = {k: v for k, v in state.items() if k not in skipped}
    model.load_state_dict(state, strict=False)
    model.eval()

    dummy = torch.zeros(1, in_size, dtype=torch.float32)
    out = MODELS_DIR / f"alphazero_{version}.onnx"
    torch.onnx.export(
        model, dummy, str(out),
        input_names=["state"],
        output_names=["policy", "value", "moon"],
        dynamic_axes={
            "state":  {0: "batch"},
            "policy": {0: "batch"},
            "value":  {0: "batch"},
            "moon":   {0: "batch"},
        },
        opset_version=opset,
        dynamo=False,
    )
    print(f"✅ Exportiert: {out}  (input={in_size}, hidden={hs}, value_hidden={vh}, opset={opset})")

    # Referenz-Ein/Ausgabe für die Rust-Paritätsprüfung schreiben (deterministisch).
    torch.manual_seed(0)
    x = torch.rand(1, in_size, dtype=torch.float32)
    with torch.no_grad():
        p, v, m = model(x)
    ref = MODELS_DIR / f"alphazero_{version}.onnx.ref.txt"
    with open(ref, "w") as f:
        f.write("# input\n" + " ".join(f"{z:.6f}" for z in x[0].tolist()) + "\n")
        f.write("# policy\n" + " ".join(f"{z:.6f}" for z in p[0].tolist()) + "\n")
        f.write("# value\n" + f"{float(v[0,0]):.6f}" + "\n")
        f.write("# moon\n" + " ".join(f"{z:.6f}" for z in m[0].tolist()) + "\n")
    print(f"📎 Referenz für Rust-Parität: {ref}")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="MosaicNet .pth → ONNX")
    ap.add_argument("--version", required=True, help="z.B. s100")
    ap.add_argument("--opset", type=int, default=13)
    args = ap.parse_args()
    export(args.version, args.opset)
