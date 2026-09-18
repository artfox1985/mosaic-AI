# -*- coding: utf-8 -*-
"""tools/pad_policy_head_export.py -- Policy-Kopf eines fertigen Checkpoints
von 406 auf `config.NUM_ACTIONS` polstern und als neue gemessene Identitaet
exportieren, OHNE zu trainieren.

ANLASS (Nutzer-Entscheid 2026-09-18, "ja nimm es so in die kette auf"):
Generator der v30-Erzeugung wird der Champion-Kandidat `v29-b07` (884
Eingaenge, 406er-Policy) mit auf 414 GEPOLSTERTEM Policy-Kopf. Weil das
Artefakt damit ein anderes ist als `v29-b07_brierbest`, bekommt es nach
`feedback_measured_identity_gets_own_bxx` einen eigenen Namen: `v29-b10`.

WAS GEPOLSTERT WIRD, und WARUM genau so:

1. AUSGANG (Policy-Kopf, 406 -> 414): acht Nullzeilen im Gewicht und acht
   Nullen im Bias. Dieselbe Bauform wie der Warmstart-Zweig in
   `train.py:1699-1729` ("Additive AUSGABE-Erweiterung des Policy-Kopfs",
   Weg A / R3): `policy_head.2.weight` (zweilagiger Kopf,
   `neural_net.py:2175-2178`) bzw. `policy_head.0.weight` (einlagiger Kopf,
   `neural_net.py:2181`) wird an dim=0 verlaengert, der zugehoerige Bias an
   dim=0 mit. Nach dem maskierten log_softmax sind die acht neuen Aktionen
   damit gleichverteilt und nicht bevorzugt; fuer die 406 alten Aktionen ist
   das Netz exakt das alte.
2. EINGANG (Flachvektor 884 -> 888): Nullspalten hinten an
   `flat_branch.0.weight` bzw. `body.0.weight`, uebernommen aus
   `train.py:1691-1702` ("Additive Eingabe-Erweiterung"). Die vier neuen
   Werte (R2 / P.16 `designs_ordered`, `serialize.rs:119/167`) wirken erst,
   wenn ein Training sie ankoppelt -- hier wird NICHT trainiert, die
   Spaltennorm bleibt also 0.

Beide Richtungen sind ADDITIV: nur Verbreiterung. Ein SCHMALERES Zielformat
waere ein Fehler und wird gemeldet, nicht gepolstert.

EXPORT: `export_onnx.export(name, opset)` -- exakt die Routine, die
`train.py:2704-2707` fuer `_brierbest.onnx` aufruft. Damit stimmen opset,
Eingabenamen (`planes`, `state`) und Ausgabenreihenfolge (`policy`, `value`,
`moon`, `points`, `ownership`, ...) mit allen anderen Netzen ueberein; die
Engine liest die ersten vier Ausgaben positional (`net.rs:472-473`). Die
`.ref.txt` fuer die Rust-Paritaetspruefung schreibt dieselbe Routine mit
(`export_onnx.py:255-263`), es braucht dafuer keinen eigenen Schritt.

NICHT GEMESSEN: dass ein gepolsterter Kopf so stark spielt wie der
ungepolsterte, ist die Frage des A/B in
`PREREG_minimal_strength_core.md` par.10.12 -- dieses Werkzeug stellt das
Artefakt nur her.

Aufruf:

    python -X utf8 tools/pad_policy_head_export.py \
        --src models/alphazero_v29-b07_brierbest.pth --dst-name v29-b10

    python -X utf8 tools/pad_policy_head_export.py --dry-run     # nur Formen
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "engine" / "py"))
sys.path.insert(0, str(REPO / "tools"))

import torch  # noqa: E402

import config  # noqa: E402
import neural_net  # noqa: E402
from neural_net import build_model_from_checkpoint, encoder_from_state_dict  # noqa: E402
from runtime_block import laufzeit_block  # noqa: E402  (CLAUDE.md-Pflichtblock)

# Die beiden Kandidaten-Keys und ihre Reihenfolge stammen 1:1 aus
# train.py:1713 -- bei einem ZWEILAGIGEN Kopf ist `policy_head.2` die
# Ausgabeschicht und `policy_head.0` die verdeckte (deren Zeilenzahl ist
# `policy_hidden` und aendert sich nicht, die dim-0-Bedingung unten greift dort
# also nicht); bei einem EINLAGIGEN Kopf ist `policy_head.0` die Ausgabeschicht.
POLICY_OUT_KEYS = ("policy_head.2.weight", "policy_head.0.weight")
# Erste Linear-Schicht des Flach-Zweigs, 2D- und Flach-Architektur
# (train.py:1691).
FLAT_IN_KEYS = ("flat_branch.0.weight", "body.0.weight")


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def policy_out_key(state: dict) -> str | None:
    """Der Key der Policy-AUSGABESCHICHT dieses Checkpoints.

    Reihenfolge von POLICY_OUT_KEYS: bei einem zweilagigen Kopf gewinnt
    `policy_head.2`, bei einem einlagigen bleibt `policy_head.0`."""
    for k in POLICY_OUT_KEYS:
        if k in state:
            return k
    return None


def flat_in_key(state: dict) -> str | None:
    for k in FLAT_IN_KEYS:
        if k in state:
            return k
    return None


def pad_policy_rows(state: dict, target_actions: int) -> tuple[int, int]:
    """Polstert die Policy-Ausgabeschicht (Gewicht UND Bias) auf
    `target_actions`. Gibt (alt, neu) zurueck. Bauform train.py:1699-1729."""
    key = policy_out_key(state)
    if key is None:
        raise SystemExit("ABBRUCH: Checkpoint traegt keinen policy_head.* -- kein Policy-Kopf zu polstern.")
    old = state[key]
    old_rows = int(old.shape[0])
    if old_rows == target_actions:
        return old_rows, old_rows
    if old_rows > target_actions:
        raise SystemExit(
            f"ABBRUCH: {key} hat {old_rows} Zeilen, Ziel ist {target_actions} -- "
            "Verengung wird NICHT gepolstert (die Regel ist additiv, neue IDs haengen hinten)."
        )
    pad = torch.zeros(target_actions - old_rows, old.shape[1], dtype=old.dtype)
    state[key] = torch.cat([old, pad], dim=0)
    bias_key = key.replace(".weight", ".bias")
    if bias_key in state:
        ob = state[bias_key]
        if int(ob.shape[0]) < target_actions:
            state[bias_key] = torch.cat(
                [ob, torch.zeros(target_actions - int(ob.shape[0]), dtype=ob.dtype)], dim=0)
    return old_rows, target_actions


def pad_flat_input(state: dict, target_input: int) -> tuple[int, int]:
    """Polstert die erste Linear-Schicht des Flach-Zweigs auf `target_input`
    Eingangsspalten (Nullspalten hinten). Bauform train.py:1691-1702."""
    key = flat_in_key(state)
    if key is None:
        raise SystemExit("ABBRUCH: Checkpoint traegt weder flat_branch.0.weight noch body.0.weight.")
    old = state[key]
    old_cols = int(old.shape[1])
    if old_cols == target_input:
        return old_cols, old_cols
    if old_cols > target_input:
        raise SystemExit(
            f"ABBRUCH: {key} hat {old_cols} Eingangsspalten, config.INPUT_SIZE ist {target_input} -- "
            "Verengung wird NICHT gepolstert (neue Merkmale haengen hinten an)."
        )
    pad = torch.zeros(old.shape[0], target_input - old_cols, dtype=old.dtype)
    state[key] = torch.cat([old, pad], dim=1)
    return old_cols, target_input


def verify_strict(model, state: dict) -> list[str]:
    """Strenge Gegenprobe NACH der Polsterung: jeder Key des Checkpoints muss
    im gebauten Modell mit IDENTISCHER Form existieren, und umgekehrt.

    `build_model_from_checkpoint` laedt mit `strict=False`
    (neural_net.py:2441) -- das ist fuer Alt-Checkpoints richtig, wuerde hier
    aber eine vergessene Polsterung STILL als zufaellig initialisierten Kopf
    durchlassen. Genau der Fall, den `export_onnx.py:76-79` als Vorfall bei v6
    beschreibt."""
    have = model.state_dict()
    problems = []
    for k, v in state.items():
        if k not in have:
            problems.append(f"{k}: im Checkpoint, nicht im Modell")
        elif tuple(v.shape) != tuple(have[k].shape):
            problems.append(f"{k}: Checkpoint {tuple(v.shape)} gegen Modell {tuple(have[k].shape)}")
    for k in have:
        if k not in state:
            problems.append(f"{k}: im Modell, nicht im Checkpoint (startet zufaellig)")
    return problems


def main() -> int:
    t0, c0 = time.monotonic(), time.process_time()
    ap = argparse.ArgumentParser(description="Policy-Kopf polstern und als neue Identitaet exportieren")
    ap.add_argument("--src", default="models/alphazero_v29-b07_brierbest.pth",
                    help="Quell-Checkpoint (.pth mit ['model_state'], Format train.py:2520)")
    ap.add_argument("--dst-name", default="v29-b10",
                    help="Name der neuen Identitaet; erzeugt models/alphazero_<name>.pth/.onnx/.onnx.ref.txt")
    ap.add_argument("--opset", type=int, default=13,
                    help="ONNX-opset; Default 13 = der Default von export_onnx.export (export_onnx.py:267)")
    ap.add_argument("--dry-run", action="store_true",
                    help="nur die Formen drucken, nichts schreiben")
    args = ap.parse_args()

    src = (REPO / args.src) if not Path(args.src).is_absolute() else Path(args.src)
    if not src.exists():
        print(f"ABBRUCH: Quelle {args.src} fehlt.", flush=True)
        return 1

    target_actions = int(config.NUM_ACTIONS)
    target_input = int(config.INPUT_SIZE)
    print(f"== Quelle      : {args.src}", flush=True)
    print(f"== Ziel-Name   : {args.dst_name}", flush=True)
    print(f"== config      : INPUT_SIZE {target_input}, NUM_ACTIONS {target_actions} "
          f"(config.py:49/57)", flush=True)

    ckpt = torch.load(str(src), map_location="cpu")
    if "model_state" not in ckpt:
        print("ABBRUCH: Checkpoint hat kein Feld 'model_state'.", flush=True)
        return 2
    state = {k: v for k, v in ckpt["model_state"].items()}
    encoder = encoder_from_state_dict(state)

    pol_key = policy_out_key(state)
    fin_key = flat_in_key(state)
    old_policy = int(state[pol_key].shape[0]) if pol_key else -1
    old_input = int(state[fin_key].shape[1]) if fin_key else -1
    conv_channels = int(state["conv.0.weight"].shape[1]) if "conv.0.weight" in state else None
    print(f"== Encoder     : {encoder}", flush=True)
    print(f"== Policy-Kopf : {pol_key}  {tuple(state[pol_key].shape)} "
          f"(Ausgabebreite {old_policy})", flush=True)
    print(f"== Flach-Eingang: {fin_key}  Breite {old_input}", flush=True)
    if conv_channels is not None:
        print(f"== Planes-Kanaele: {conv_channels} "
              f"(neural_net.NUM_PLANES_CHANNELS = {neural_net.NUM_PLANES_CHANNELS})", flush=True)
        if conv_channels != neural_net.NUM_PLANES_CHANNELS:
            print("   WARNUNG: Kanalzahl weicht ab. Dieses Werkzeug polstert NUR Flach-Eingang und "
                  "Policy-Ausgang (train.py kennt keine Conv-Polsterung); ein Kanal-Zuwachs braucht "
                  "einen eigenen Entscheid.", flush=True)
    print(f"== geplant     : Policy {old_policy} -> {target_actions} "
          f"({max(0, target_actions - old_policy)} Nullzeilen), "
          f"Eingang {old_input} -> {target_input} "
          f"({max(0, target_input - old_input)} Nullspalten)", flush=True)

    if args.dry_run:
        print("== dry-run: nichts geschrieben.", flush=True)
        print(json.dumps({"laufzeit": laufzeit_block(t0, cpu_start=c0, threads=1)},
                         ensure_ascii=False), flush=True)
        return 0

    pol_old, pol_new = pad_policy_rows(state, target_actions)
    in_old, in_new = pad_flat_input(state, target_input)
    print(f"   policy_head: Breite {pol_old} -> {pol_new}", flush=True)
    print(f"   {fin_key}: Eingangsbreite {in_old} -> {in_new}", flush=True)

    # Modell mit der HEUTIGEN Architektur bauen und die gepolsterte State-Dict
    # hineinladen. `build_model_from_checkpoint` (neural_net.py:2382) ist die
    # gemeinsame Bauform von export_onnx/offline_diagnosis/oracle_metrics -- sie
    # leitet Kopf-Bestand, Breiten und Value-Variante aus der State-Dict ab.
    padded_ckpt = dict(ckpt)
    padded_ckpt["model_state"] = state
    model, encoder2 = build_model_from_checkpoint(padded_ckpt, input_size=target_input,
                                                 num_actions=target_actions)
    problems = verify_strict(model, state)
    if problems:
        print("ABBRUCH: State-Dict passt nach der Polsterung NICHT strikt auf das Modell:", flush=True)
        for p in problems:
            print(f"   {p}", flush=True)
        return 3
    # Jetzt, wo Keys und Formen geprueft sind, noch einmal STRIKT laden -- damit
    # steht das strict=True schwarz auf weiss im Pfad und nicht nur als
    # Gegenprobe daneben.
    model.load_state_dict(state, strict=True)
    model.eval()
    print(f"   strikte Gegenprobe gruen: {len(state)} Tensoren, Encoder {encoder2}", flush=True)

    # Herkunft mitschreiben: ohne diese Felder ist am Artefakt nicht ablesbar,
    # dass der Kopf gepolstert und NICHT trainiert wurde.
    padded_ckpt["version"] = args.dst_name
    padded_ckpt["num_actions"] = target_actions
    padded_ckpt["input_size"] = target_input
    padded_ckpt["padded_from"] = str(args.src)
    padded_ckpt["padded_policy_rows"] = [pol_old, pol_new]
    padded_ckpt["padded_input_cols"] = [in_old, in_new]
    padded_ckpt["padded_without_training"] = True
    padded_ckpt["padded_note"] = ("Policy-Ausgang und Flach-Eingang mit Nullen erweitert "
                                  "(Bauform train.py:1691-1729), kein Trainingsschritt.")

    dst_pth = Path(config.MODELS_DIR) / f"alphazero_{args.dst_name}.pth"
    torch.save(padded_ckpt, str(dst_pth))
    print(f"== .pth geschrieben: {dst_pth}", flush=True)

    # GENAU die Export-Routine von train.py:2704-2707 (`from export_onnx import
    # export`). Sie liest models/alphazero_<name>.pth wieder ein, exportiert
    # das ONNX und schreibt die .ref.txt daneben.
    from export_onnx import export  # noqa: E402  (spaet, wie in train.py)
    dst_onnx = export(args.dst_name, args.opset)
    dst_ref = Path(str(dst_onnx) + ".ref.txt")

    result = {
        "werkzeug": "tools/pad_policy_head_export.py",
        "src": str(args.src),
        "dst_name": args.dst_name,
        "encoder": encoder2,
        "opset": args.opset,
        "policy_out_key": pol_key,
        "policy_width_alt": pol_old,
        "policy_width_neu": pol_new,
        "flat_in_key": fin_key,
        "input_width_alt": in_old,
        "input_width_neu": in_new,
        "planes_channels": conv_channels,
        "padded_without_training": True,
        "dateien": {},
    }
    for label, p in (("pth", dst_pth), ("onnx", Path(dst_onnx)), ("ref", dst_ref)):
        if Path(p).exists():
            result["dateien"][label] = {"pfad": str(p), "bytes": Path(p).stat().st_size,
                                       "sha256": sha256_of(Path(p))}
            print(f"== {label:4s} {p}  {Path(p).stat().st_size} B  "
                  f"sha256 {result['dateien'][label]['sha256']}", flush=True)
        else:
            result["dateien"][label] = None
            print(f"   WARNUNG: {label} fehlt ({p})", flush=True)

    result["laufzeit"] = laufzeit_block(t0, cpu_start=c0, threads=1)
    art = REPO / "evaluations" / "artifacts" / f"pad_policy_head_{args.dst_name}.json"
    art.parent.mkdir(parents=True, exist_ok=True)
    with open(art, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"== Artefakt: {art}", flush=True)
    print(f"== laufzeit: {json.dumps(result['laufzeit'], ensure_ascii=False)}", flush=True)
    if result["dateien"]["onnx"] is None or result["dateien"]["ref"] is None:
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
