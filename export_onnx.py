"""
Exportiert ein trainiertes MosaicNet/Mosaic2DNet (.pth) nach ONNX für die
Rust-Inferenz (Phase B).

  python export_onnx.py --version s100

Erzeugt models/alphazero_<version>.onnx mit 5 Outputs (policy, value, moon,
points, ownership[, points_dist[, opp_points]]) und dynamischer Batch-Achse.
Die Rust-Engine (tract-onnx) lädt diese Datei für den Network-Modus
(Self-Play / Arena). `value`/`points`/`ownership` sind reine Trainings-
Zusatzsignale -- die Suche (Stage 1/3) liest nur `policy`/`moon`. (Baustein B:
die frueheren dome_slot/dome_rotation-Outputs sind entfallen -- Kuppelplatten-
Slot/Rotation haben jetzt eigene Policy-IDs statt einer separaten Kopf-
Faktorisierung, siehe net_mcts.rs::build_untried_actions.)

Task #28 (PREREG_task28_aggression.md): optionaler 6. (bzw. 7., falls
`points_dist` aktiv) Output `opp_points` -- reine GEGNER-Punkteprognose,
NUR wenn der Checkpoint den additiven `opp_points_head` traegt
(`neural_net.py::opp_points_head_present`). Alt-Modelle ohne diesen Kopf
exportieren byte-identisch wie zuvor. Die Engine erkennt den Output per
NAME, nicht Position.

Task #11 Phase 2 (M2.1): zusätzlicher 2D-Zweig für `Mosaic2DNet`-Checkpoints
(`--encoder 2d` beim Training, siehe `train.py`) -- ZWEI ONNX-Graph-Inputs
(`planes` [batch,76,6,6], `state` [batch,708]), erkannt am `conv.0.weight`-Key
im Checkpoint (`neural_net.py::encoder_from_state_dict`, rückwirkend
funktionsfähig, kein Manifest-Feld nötig). Der bestehende Flach-Zweig bleibt
UNVERÄNDERT (byte-identisches Verhalten für alle `MosaicNet`-Checkpoints).
"""
import sys
import argparse
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent / "engine" / "py"))
from neural_net import (MosaicNet, Mosaic2DNet, points_dist_bins_from_state,  # noqa: E402
                        encoder_from_state_dict, opp_points_head_present)
from config import INPUT_SIZE, NUM_ACTIONS, MODELS_DIR  # noqa: E402


def _export_flat(version: str, ckpt: dict, opset: int) -> Path:
    """Bestehender Flach-Zweig (`MosaicNet`) -- UNVERÄNDERT ggü. vor Task #11
    Phase 2, nur aus `export()` herausgezogen (nimmt jetzt das bereits
    geladene `ckpt`-Dict entgegen statt selbst `torch.load` aufzurufen)."""
    state = ckpt["model_state"]
    hs = state["body.0.weight"].shape[0]
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
    # Task #28 (PREREG_task28_aggression.md): additiver opp_points_head NUR,
    # wenn der Checkpoint ihn traegt -- Alt-Modelle exportieren dadurch
    # byte-identisch (5 Outputs) wie vor dieser Aenderung.
    opp_head = opp_points_head_present(state)

    model = MosaicNet(input_size=in_size, num_actions=NUM_ACTIONS, hidden_size=hs, policy_hidden=ph,
                      points_dist_bins=points_dist_bins_from_state(state), opp_points_head=opp_head)
    new_state = model.state_dict()
    # Checkpoints aus der value-head-losen Zwischenphase haben KEINE
    # value_head.*/points_head.*-Keys -- strict=False laesst diese Heads
    # dann einfach zufallsinitialisiert (kein Ziel dafuer im alten Checkpoint).
    # Shape-Mismatches bei den verbleibenden, gemeinsamen Keys (z.B.
    # body.0.weight bei geaendertem INPUT_SIZE) werden weiterhin explizit
    # rausgefiltert, sonst wuerde load_state_dict crashen.
    skipped = [k for k in state if k in new_state and state[k].shape != new_state[k].shape]
    if skipped:
        print(f"⚠️  Shape-Mismatch (alte Head-Architektur?), startet zufällig: {', '.join(skipped)}")
        state = {k: v for k, v in state.items() if k not in skipped}
    model.load_state_dict(state, strict=False)
    model.eval()

    # Ausgabenamen/-achsen abhaengig vom Verteilungs-Kopf (Task #12): bei
    # aktiven Bins haengt "points_dist" NOCH hinter "ownership". net.rs liest
    # out[0..3] positionsbasiert, angehaengte Koepfe aendern daran nichts.
    # JEDE Ausgabe MUSS in dynamic_axes stehen -- fehlt ein Eintrag, backt der
    # Export eine FESTE Batch-Dimension ein, was den Batch=2-Pfad
    # (net.rs::eval_pair) auf Graph-Ebene brechen kann.
    out_names = ["policy", "value", "moon", "points", "ownership"]
    if getattr(model, "points_dist_bins", 0) > 0:
        out_names.append("points_dist")
    # Task #28: "opp_points" MUSS der ZULETZT angehaengte Output sein (ONNX-
    # Vertrag mit der Engine-Seite, siehe PREREG_task28_aggression.md) --
    # deshalb nach "points_dist", nicht davor. Die Engine erkennt ihn per
    # Output-NAME, nicht per Position.
    if getattr(model, "has_opp_points_head", False):
        out_names.append("opp_points")
    dyn_axes = {"state": {0: "batch"}}
    dyn_axes.update({n: {0: "batch"} for n in out_names})

    dummy = torch.zeros(1, in_size, dtype=torch.float32)
    out = MODELS_DIR / f"alphazero_{version}.onnx"
    torch.onnx.export(
        model, dummy, str(out),
        input_names=["state"],
        # "ownership" steht ZULETZT (Task #9): net.rs liest die Ausgaenge
        # positionsbasiert (out[0..3]), ein angehaengter Kopf laesst die
        # bestehenden Indizes unveraendert und wird von Rust ignoriert.
        output_names=out_names,
        dynamic_axes=dyn_axes,
        opset_version=opset,
        dynamo=False,
    )
    print(f"✅ Exportiert (flat): {out}  (input={in_size}, hidden={hs}, opset={opset})")

    # Referenz-Ein/Ausgabe für die Rust-Paritätsprüfung schreiben (deterministisch).
    torch.manual_seed(0)
    x = torch.rand(1, in_size, dtype=torch.float32)
    with torch.no_grad():
        p, v, m, pts, *_own = model(x)
    ref = MODELS_DIR / f"alphazero_{version}.onnx.ref.txt"
    with open(ref, "w") as f:
        f.write("# input\n" + " ".join(f"{z:.6f}" for z in x[0].tolist()) + "\n")
        f.write("# policy\n" + " ".join(f"{z:.6f}" for z in p[0].tolist()) + "\n")
        f.write("# value\n" + " ".join(f"{z:.6f}" for z in v[0].tolist()) + "\n")
        f.write("# moon\n" + " ".join(f"{z:.6f}" for z in m[0].tolist()) + "\n")
        f.write("# points\n" + " ".join(f"{z:.6f}" for z in pts[0].tolist()) + "\n")
    print(f"📎 Referenz für Rust-Parität: {ref}")
    return out


def _export_2d(version: str, ckpt: dict, opset: int) -> Path:
    """Task #11 Phase 2 (M2.1): 2D-Zweig (`Mosaic2DNet`) -- ZWEI ONNX-Graph-
    Inputs (`planes` [batch,76,6,6], `state` [batch,708]), Reihenfolge Planes
    ZUERST (muss zu `net.rs::InputLayout::PlanesPlusFlat`/`detect_layout`
    passen: Input 0 = Rang 4/Planes, Input 1 = Rang 2/Flat)."""
    state = ckpt["model_state"]
    in_size = state["flat_branch.0.weight"].shape[1]
    hs = state["flat_branch.0.weight"].shape[0]
    if in_size != INPUT_SIZE:
        print(f"⚠️  Modell-Input {in_size} ≠ config.INPUT_SIZE {INPUT_SIZE} — nutze Modellwert.")
    ph = state["policy_head.0.bias"].shape[0] if "policy_head.2.weight" in state else 0
    planes_channels = state["conv.0.weight"].shape[1]
    conv_channels = state["conv.0.weight"].shape[0]
    # Anzahl Conv-Lagen aus den vorhandenen "conv.<3k>.weight"-Keys ableiten
    # (jede Lage = Conv2d+BatchNorm2d+ReLU -- Conv2d-Gewichte liegen bei
    # Index 0,3,6,... im `nn.Sequential`).
    conv_layers = sum(1 for k in state if k.startswith("conv.") and k.endswith(".weight")
                      and "running" not in k and int(k.split(".")[1]) % 3 == 0)

    # Task #28: siehe _export_flat-Kommentar -- additiv, nur wenn im Checkpoint vorhanden.
    opp_head = opp_points_head_present(state)

    model = Mosaic2DNet(input_size=in_size, num_actions=NUM_ACTIONS, hidden_size=hs, policy_hidden=ph,
                        points_dist_bins=points_dist_bins_from_state(state),
                        planes_channels=planes_channels, conv_channels=conv_channels,
                        conv_layers=max(conv_layers, 1), opp_points_head=opp_head)
    new_state = model.state_dict()
    skipped = [k for k in state if k in new_state and state[k].shape != new_state[k].shape]
    if skipped:
        print(f"⚠️  Shape-Mismatch (2D-Architektur weicht ab?), startet zufällig: {', '.join(skipped)}")
        state = {k: v for k, v in state.items() if k not in skipped}
    model.load_state_dict(state, strict=False)
    model.eval()

    out_names = ["policy", "value", "moon", "points", "ownership"]
    if getattr(model, "points_dist_bins", 0) > 0:
        out_names.append("points_dist")
    # Task #28: "opp_points" ZULETZT (siehe _export_flat-Kommentar).
    if getattr(model, "has_opp_points_head", False):
        out_names.append("opp_points")
    # JEDE Ein-/Ausgabe muss in dynamic_axes stehen (siehe Flach-Zweig-Kommentar
    # oben) -- gilt hier für BEIDE Inputs.
    dyn_axes = {"planes": {0: "batch"}, "state": {0: "batch"}}
    dyn_axes.update({n: {0: "batch"} for n in out_names})

    dummy_planes = torch.zeros(1, planes_channels, 6, 6, dtype=torch.float32)
    dummy_flat = torch.zeros(1, in_size, dtype=torch.float32)
    out = MODELS_DIR / f"alphazero_{version}.onnx"
    torch.onnx.export(
        model, (dummy_planes, dummy_flat), str(out),
        input_names=["planes", "state"],
        output_names=out_names,
        dynamic_axes=dyn_axes,
        opset_version=opset,
        dynamo=False,
    )
    print(f"✅ Exportiert (2d): {out}  (planes_channels={planes_channels}, conv_channels={conv_channels}, "
          f"conv_layers={conv_layers}, flat_input={in_size}, hidden={hs}, opset={opset})")

    # Referenz-Ein/Ausgabe für die Rust-Paritätsprüfung (deterministisch,
    # analog zum Flach-Zweig -- ZWEI Input-Bloecke statt einem).
    torch.manual_seed(0)
    xp = torch.rand(1, planes_channels, 6, 6, dtype=torch.float32)
    xf = torch.rand(1, in_size, dtype=torch.float32)
    with torch.no_grad():
        p, v, m, pts, *_own = model(xp, xf)
    ref = MODELS_DIR / f"alphazero_{version}.onnx.ref.txt"
    with open(ref, "w") as f:
        f.write("# input_planes\n" + " ".join(f"{z:.6f}" for z in xp.flatten().tolist()) + "\n")
        f.write("# input_state\n" + " ".join(f"{z:.6f}" for z in xf[0].tolist()) + "\n")
        f.write("# policy\n" + " ".join(f"{z:.6f}" for z in p[0].tolist()) + "\n")
        f.write("# value\n" + " ".join(f"{z:.6f}" for z in v[0].tolist()) + "\n")
        f.write("# moon\n" + " ".join(f"{z:.6f}" for z in m[0].tolist()) + "\n")
        f.write("# points\n" + " ".join(f"{z:.6f}" for z in pts[0].tolist()) + "\n")
    print(f"📎 Referenz für Rust-Parität: {ref}")
    return out


def export(version: str, opset: int = 13) -> Path:
    pth = MODELS_DIR / f"alphazero_{version}.pth"
    if not pth.exists():
        raise SystemExit(f"❌ Modell nicht gefunden: {pth}")

    ckpt = torch.load(str(pth), map_location="cpu")
    encoder = encoder_from_state_dict(ckpt["model_state"])
    if encoder == "2d":
        return _export_2d(version, ckpt, opset)
    return _export_flat(version, ckpt, opset)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="MosaicNet/Mosaic2DNet .pth → ONNX")
    ap.add_argument("--version", required=True, help="z.B. s100")
    ap.add_argument("--opset", type=int, default=13)
    args = ap.parse_args()
    export(args.version, args.opset)
