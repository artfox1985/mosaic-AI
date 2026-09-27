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

Task #34: bei einem 'wdl'-Value-Kopf (`--value-head wdl` beim Training,
erkannt an `value_head.2.weight` mit Breite 2, siehe
`neural_net.py::value_head_variant_from_state`) haengt zusaetzlich ein
optionaler Output `value_wdl_logits` (rohe 2-Logit-Ausgabe) NACH `points_dist`
(falls aktiv), aber VOR `opp_points`. Der bestehende `value`-Output bleibt an
SEINER Position UND auf der GLEICHEN [-1,1]-Skala (`2*P(Sieg)-1`) -- die
Engine-Seite (`net_mcts.rs::value_to_win_prob`) liest ihn unveraendert,
`value_wdl_logits` ist reine Trainings-/Diagnose-Zusatzinformation, von der
Rust-Suche nicht konsumiert. Alt-Modelle (Tanh-Kopf) exportieren
byte-identisch wie zuvor.

Schema 18 (evaluations/PREREG_plate_intervention.md): optionaler LETZTER
Output `endgame_margin` -- exakter R5-Wurzelwert-Aux-Kopf, NUR wenn der
Checkpoint den additiven `endgame_head` traegt
(`neural_net.py::endgame_head_present`), haengt HINTER `opp_points` (falls
beide aktiv). Alt-Modelle ohne diesen Kopf exportieren byte-identisch wie
zuvor. Die Engine erkennt den Output per NAME, nicht Position (net.rs).
"""
import sys
import argparse
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent / "engine" / "py"))
from neural_net import (MosaicNet, Mosaic2DNet, points_dist_bins_from_state,  # noqa: E402
                        encoder_from_state_dict, opp_points_head_present,
                        endgame_head_present, conjunction_head_present,
                        ownership_head_2d_present,
                        value_head_variant_from_state)
from config import INPUT_SIZE, NUM_ACTIONS, MODELS_DIR  # noqa: E402


class PartialLoadError(RuntimeError):
    """Der Checkpoint passt nicht vollstaendig auf das gebaute Modell.

    Bewusst eine `Exception` (kein SystemExit): der Auto-Export am Ende von
    `train.py` (Abschnitt 7) faengt `Exception` und meldet "ONNX-Export
    uebersprungen", der Trainingslauf endet dann regulaer (Snapshot, Laufzeit,
    Zwischenstand-Loeschung laufen weiter) -- es entsteht nur KEIN .onnx. Ein
    SystemExit wuerde dort vorbeifliegen und den Rest des Laufs abschneiden."""


def load_state_checked(model, state: dict, allow_partial: bool, label: str) -> None:
    """Checkpoint-Gewichte laden und das Ergebnis AUSWERTEN (Code-Review
    2026-09-26 #18).

    Bis dahin wurden Shape-Abweichungen herausgefiltert, `load_state_dict(
    strict=False)` lief, und das Ergebnis (fehlende und unerwartete Schluessel)
    wurde nicht angesehen: ein Kopf, der im Checkpoint anders aussah, startete
    ZUFAELLIG und wurde exportiert -- die Rust-Paritaetsreferenz (.ref.txt)
    entsteht aus demselben Modell und faengt das nicht. Jetzt drei Klassen:

    * Shape-Abweichung (Schluessel in beiden, Form verschieden) -> startet zufaellig,
    * im Modell, nicht im Checkpoint -> startet zufaellig,
    * im Checkpoint, nicht im Modell -> Gewichte fallen weg (ein Kopf fehlt im Export).

    Jede davon ist ein ABBRUCH (`PartialLoadError`), ausser mit
    `allow_partial=True` (CLI `--allow-partial-load`); dann das alte Verhalten
    mit vollstaendiger Liste auf der Konsole. Der gewollte Anwendungsfall dafuer
    sind Alt-Checkpoints aus der value-head-losen Zwischenphase (v1-v6), deren
    fehlende Koepfe zufaellig starten DUERFEN, weil die Suche sie nicht liest.
    Herleitung, ungemessen: aktuelle Checkpoints laden verlustfrei, weil
    `train.py` (Modellbau vor dem Warm-Start) und die Kopf-Erkennung hier
    dieselben Konstruktor-Argumente benutzen.
    """
    new_state = model.state_dict()
    skipped = [k for k in state if k in new_state and tuple(state[k].shape) != tuple(new_state[k].shape)]
    loadable = {k: v for k, v in state.items() if k not in skipped}
    missing = sorted(k for k in new_state if k not in state)
    unexpected = sorted(k for k in state if k not in new_state)
    problems = []
    if skipped:
        problems.append("Shape-Mismatch, startet zufaellig: "
                        + ", ".join(f"{k} (Checkpoint {tuple(state[k].shape)}, Modell "
                                    f"{tuple(new_state[k].shape)})" for k in skipped))
    if missing:
        problems.append("im Modell, nicht im Checkpoint, startet zufaellig: " + ", ".join(missing))
    if unexpected:
        problems.append("im Checkpoint, nicht im Modell, faellt weg: " + ", ".join(unexpected))
    if problems and not allow_partial:
        raise PartialLoadError(
            f"Export {label}: Checkpoint passt nicht vollstaendig auf das Modell -- ABBRUCH "
            f"(nur mit --allow-partial-load wird trotzdem exportiert):\n  - "
            + "\n  - ".join(problems))
    for p in problems:
        print(f"⚠️  --allow-partial-load ({label}): {p}")
    model.load_state_dict(loadable, strict=False)


def _export_flat(version: str, ckpt: dict, opset: int, allow_partial_load: bool = False) -> Path:
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
    # Task #34: 'tanh' oder 'wdl' AUS DEM CHECKPOINT -- Alt-Modelle (kein
    # `value_head.2.weight` mit Breite 2) exportieren byte-identisch.
    value_head_variant = value_head_variant_from_state(state)
    # Schema 18 (PREREG_plate_intervention.md): siehe Modul-Kommentar --
    # additiv, nur wenn im Checkpoint vorhanden (Muster opp_head).
    eg_head = endgame_head_present(state)

    # Konjunktions-Erweiterung des Ownership-Kopfs: MUSS mitgezogen werden --
    # sonst baut der Export einen 72-breiten Kopf, der Checkpoint traegt 122,
    # und der Shape-Mismatch-Zweig unten haette den Kopf bis zu Code-Review #18
    # STILL zufaellig initialisiert exportiert (heute: Abbruch, load_state_checked).
    cj_head = conjunction_head_present(state)

    model = MosaicNet(input_size=in_size, num_actions=NUM_ACTIONS, hidden_size=hs, policy_hidden=ph,
                      points_dist_bins=points_dist_bins_from_state(state), opp_points_head=opp_head,
                      endgame_head=eg_head, conjunction_head=cj_head,
                      value_head_variant=value_head_variant)
    # Checkpoints aus der value-head-losen Zwischenphase haben KEINE
    # value_head.*/points_head.*-Keys, und Shape-Mismatches bei gemeinsamen
    # Keys (z.B. body.0.weight bei geaendertem INPUT_SIZE) liessen die
    # betroffenen Teile zufaellig starten. Seit Code-Review #18 ist beides ein
    # Abbruch, ausser mit --allow-partial-load (siehe load_state_checked).
    load_state_checked(model, state, allow_partial_load, f"{version} (flat)")
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
    # Task #34: "value_wdl_logits" haengt NACH "points_dist", aber VOR
    # "opp_points" -- muss exakt der Anhaenge-Reihenfolge in
    # `MosaicNet.forward` entsprechen (sonst Output-Name/Tensor-Mismatch).
    if getattr(model, "value_head_variant", "tanh") == "wdl":
        out_names.append("value_wdl_logits")
    # Task #28: "opp_points" MUSS der ZULETZT angehaengte Output sein (ONNX-
    # Vertrag mit der Engine-Seite, siehe PREREG_task28_aggression.md) --
    # deshalb nach "points_dist"/"value_wdl_logits", nicht davor. Die Engine
    # erkennt ihn per Output-NAME, nicht per Position.
    if getattr(model, "has_opp_points_head", False):
        out_names.append("opp_points")
    # Schema 18: "endgame_margin" MUSS der ALLERLETZTE Output sein (haengt
    # HINTER "opp_points", siehe Modul-Kommentar) -- Engine erkennt ihn per
    # Output-NAME, nicht per Position.
    if getattr(model, "has_endgame_head", False):
        out_names.append("endgame_margin")
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


def _export_2d(version: str, ckpt: dict, opset: int, allow_partial_load: bool = False) -> Path:
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
    # Task #34: siehe _export_flat-Kommentar.
    value_head_variant = value_head_variant_from_state(state)
    # Schema 18: siehe _export_flat-Kommentar.
    eg_head = endgame_head_present(state)

    model = Mosaic2DNet(input_size=in_size, num_actions=NUM_ACTIONS, hidden_size=hs, policy_hidden=ph,
                        points_dist_bins=points_dist_bins_from_state(state),
                        planes_channels=planes_channels, conv_channels=conv_channels,
                        conv_layers=max(conv_layers, 1), opp_points_head=opp_head,
                        endgame_head=eg_head, conjunction_head=conjunction_head_present(state),
                        ownership_head_2d=ownership_head_2d_present(state),
                        value_head_variant=value_head_variant)
    # Code-Review #18: siehe load_state_checked -- Abbruch statt stillem Zufallskopf.
    load_state_checked(model, state, allow_partial_load, f"{version} (2d)")
    model.eval()

    out_names = ["policy", "value", "moon", "points", "ownership"]
    if getattr(model, "points_dist_bins", 0) > 0:
        out_names.append("points_dist")
    # Task #34: "value_wdl_logits" NACH "points_dist", VOR "opp_points" (siehe
    # _export_flat-Kommentar).
    if getattr(model, "value_head_variant", "tanh") == "wdl":
        out_names.append("value_wdl_logits")
    # Task #28: "opp_points" ZULETZT (siehe _export_flat-Kommentar).
    if getattr(model, "has_opp_points_head", False):
        out_names.append("opp_points")
    # Schema 18: "endgame_margin" ALLERLETZT (siehe _export_flat-Kommentar).
    if getattr(model, "has_endgame_head", False):
        out_names.append("endgame_margin")
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


def export(version: str, opset: int = 13, allow_partial_load: bool = False) -> Path:
    """`allow_partial_load` (Code-Review #18): Default False = ein Checkpoint,
    der nicht vollstaendig auf das Modell passt, wirft `PartialLoadError`
    statt mit Zufallskopf zu exportieren (siehe `load_state_checked`)."""
    pth = MODELS_DIR / f"alphazero_{version}.pth"
    if not pth.exists():
        raise SystemExit(f"❌ Modell nicht gefunden: {pth}")

    ckpt = torch.load(str(pth), map_location="cpu")
    encoder = encoder_from_state_dict(ckpt["model_state"])
    if encoder == "2d":
        return _export_2d(version, ckpt, opset, allow_partial_load)
    return _export_flat(version, ckpt, opset, allow_partial_load)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="MosaicNet/Mosaic2DNet .pth → ONNX")
    ap.add_argument("--version", required=True, help="z.B. s100")
    ap.add_argument("--opset", type=int, default=13)
    ap.add_argument("--allow-partial-load", action="store_true",
                    help="Code-Review #18: auch exportieren, wenn der Checkpoint nicht "
                         "vollstaendig auf das Modell passt (Shape-Abweichung, fehlende oder "
                         "ueberzaehlige Schluessel) -- betroffene Teile starten dann ZUFAELLIG. "
                         "Nur fuer Alt-Checkpoints mit bekannt fehlenden Koepfen. Ohne das Flag: "
                         "Abbruch mit vollstaendiger Liste.")
    args = ap.parse_args()
    try:
        export(args.version, args.opset, allow_partial_load=args.allow_partial_load)
    except PartialLoadError as e:
        raise SystemExit(f"❌ {e}")
