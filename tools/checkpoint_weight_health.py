# -*- coding: utf-8 -*-
"""tools/checkpoint_weight_health.py -- Netz-Gesundheit von Checkpoints gegen einen Warmstart,
NUR aus den Gewichten (kein Datensatz, kein Modellbau, keine Vorwaertsrechnung).

Zweck: die "Netz-Gesundheit gegen den Warmstart" aus PREREG_v34_window.md par.10 als
reproduzierbares Werkzeug (dort von Hand gerechnet). Gemessen wird:
  * NaN/Inf je Tensor des state_dict, in ALLEN Staenden (Referenz eingeschlossen);
  * je Schicht (Praefix vor dem letzten Punkt des Schluessels): Frobenius-Norm, Norm der
    Differenz zur Referenz, relative Aenderung in Prozent;
  * je BatchNorm-Schicht: Einheiten mit |gamma| < 1e-3 (Ersatzgroesse fuer tote Einheiten;
    Aktivierungen werden NICHT gemessen, wie in par.10);
  * Schluessel, die nur in der Referenz oder nur im Checkpoint vorkommen, und
    Formabweichungen gleicher Schluessel.
Die "Ankopplung neuer Spalten" aus par.10 (E4-Arm) entfaellt hier: sie setzt eine
Eingabe-Erweiterung voraus, die es in v35 nicht gibt.

Checkpoint-Format (train.py:2782-2858, geschrieben ueber `save_checkpoint_atomic`,
train.py:1161-1171): ein dict mit dem state_dict unter "model_state", Name unter
"version" (NICHT "version_name"), Epochenstand unter "epochs"; `_best`/`_brierbest`
sind Kopien mit eigenem "model_state"/"epochs" plus "is_best_checkpoint"/"selected_by"
(train.py:2875-2881, 2937-2941). `neural_net.build_model_from_checkpoint` liest
ebenfalls `ckpt["model_state"]` (engine/py/neural_net.py:2421). Hier wird NUR dieses
state_dict mit `torch.load(..., map_location="cpu")` geladen.

Verdikt-Regel (par.10 hat keine Schwelle, dort nur berichtet): "gesund", wenn
nan_inf_total == 0 und bn_dead_total == 0; sonst "ROT" mit Grund. Schluessel- und
Formabweichungen gehen als Hinweis in den Bericht, nicht ins Verdikt.

Aufruf:
    python -X utf8 -u tools/checkpoint_weight_health.py \\
        --reference models/alphazero_v34-b01_brierbest.pth \\
        --checkpoints models/alphazero_v35-b01_best.pth models/alphazero_v35-b01.pth \\
        --out evaluations/artifacts/checkpoint_weight_health_v35-b01.json

Rechenlast: klein (zwei bis drei state_dicts zu je ~11 MB auf der CPU, Default ein
Thread). Laedt aber Modelldateien -- waehrend eines Messlaufs trotzdem nicht starten.
"""
import argparse
import hashlib
import json
import math
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent

PREREG = "PREREG_v34_window.md par.10 (Definition); Anwendung v35-b01"
BN_DEAD_THRESHOLD = 1e-3
# Buffer einer BatchNorm-Schicht: Statistik, keine gelernten Gewichte. Sie gehen in die
# NaN/Inf-Zaehlung ein, aber NICHT in Norm und relative Aenderung der Schicht.
BUFFER_SUFFIXES = ("running_mean", "running_var", "num_batches_tracked")


def rel(p) -> str:
    """Pfad relativ zur Projektwurzel (oeffentliches Repo: keine absoluten Pfade)."""
    try:
        return Path(p).resolve().relative_to(_ROOT).as_posix()
    except ValueError:
        return Path(p).name


def sha256_of(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_state() -> dict:
    def run(cmd):
        try:
            r = subprocess.run(cmd, cwd=_ROOT, capture_output=True, text=True,
                               encoding="utf-8", check=False)
            return r.stdout.strip() if r.returncode == 0 else None
        except Exception:
            return None
    status = run(["git", "status", "--porcelain", "--untracked-files=no"])
    return {"git_commit": run(["git", "rev-parse", "HEAD"]),
            "git_dirty": None if status is None else bool(status)}


def finite_or_none(x):
    return x if (x is not None and math.isfinite(x)) else None


def load_checkpoint(path: Path, torch):
    """Laedt den Checkpoint auf die CPU; gibt (state_dict, meta) zurueck.

    Regulaer liegt das state_dict unter "model_state" (train.py:2783). Fehlt der
    Schluessel und besteht das dict nur aus Tensoren, wird es als nacktes state_dict
    gelesen (Fallback fuer Fremd-Dateien), das steht dann in meta["format"]."""
    ckpt = torch.load(str(path), map_location="cpu")
    if isinstance(ckpt, dict) and "model_state" in ckpt:
        meta = {k: ckpt.get(k) for k in ("version", "epochs", "epochs_requested",
                                         "is_best_checkpoint", "selected_by",
                                         "load_version", "final_value_val_brier")}
        meta["format"] = "train.py dict (model_state)"
        return ckpt["model_state"], meta
    if isinstance(ckpt, dict) and ckpt and all(torch.is_tensor(v) for v in ckpt.values()):
        return ckpt, {"format": "nacktes state_dict"}
    sys.exit(f"FEHLER: {rel(path)} ist weder ein train.py-Checkpoint (model_state) "
             f"noch ein nacktes state_dict -- Abbruch.")


def layer_of(key: str) -> tuple[str, str]:
    """Schicht = Praefix vor dem letzten Punkt; Rest = Tensorname in der Schicht."""
    if "." in key:
        prefix, name = key.rsplit(".", 1)
        return prefix, name
    return "", key


def nan_inf_per_tensor(state, torch) -> dict:
    """NaN/Inf-Zahl je Tensor; Ganzzahl-Tensoren (num_batches_tracked) sind per Typ endlich."""
    out = {}
    for k, t in state.items():
        if torch.is_tensor(t) and t.is_floating_point():
            out[k] = int((~torch.isfinite(t)).sum().item())
        else:
            out[k] = 0
    return out


def bn_layers(state) -> list[str]:
    """BatchNorm-Schichten: Praefix mit `weight` UND `running_mean` im state_dict."""
    out = []
    for k in state:
        prefix, name = layer_of(k)
        if name == "running_mean" and f"{prefix}.weight" in state:
            out.append(prefix)
    return out


def analyse(state, ref_state, torch) -> dict:
    """Schicht-Tabelle, BN-Befund, Schluesselabgleich eines Checkpoints gegen die Referenz.

    Ist `ref_state` None, entfallen Differenz und relative Aenderung (Referenz selbst)."""
    layers: dict[str, dict] = {}
    shape_mismatch = []
    for k, t in state.items():
        prefix, name = layer_of(k)
        if name in BUFFER_SUFFIXES or not (torch.is_tensor(t) and t.is_floating_point()):
            continue
        d = layers.setdefault(prefix, {"tensors": [], "numel": 0, "sq": 0.0,
                                       "ref_sq": 0.0, "diff_sq": 0.0, "compared": True})
        x = t.detach().to(torch.float64)
        d["tensors"].append(name)
        d["numel"] += int(x.numel())
        d["sq"] += float((x * x).sum().item())
        if ref_state is None:
            continue
        r = ref_state.get(k)
        if r is None or not torch.is_tensor(r):
            d["compared"] = False
            continue
        if tuple(r.shape) != tuple(t.shape):
            shape_mismatch.append({"key": k, "shape": list(t.shape), "ref_shape": list(r.shape)})
            d["compared"] = False
            continue
        rr = r.detach().to(torch.float64)
        d["ref_sq"] += float((rr * rr).sum().item())
        d["diff_sq"] += float(((x - rr) ** 2).sum().item())

    bn = {}
    for p in bn_layers(state):
        g = state[f"{p}.weight"].detach().to(torch.float64).abs()
        bn[p] = {"dead_units": int((g < BN_DEAD_THRESHOLD).sum().item()),
                 "units": int(g.numel()),
                 "gamma_abs_min": finite_or_none(float(g.min().item())) if g.numel() else None}

    table = []
    for p, d in layers.items():
        row = {"layer": p, "tensors": d["tensors"], "numel": d["numel"],
               "norm": finite_or_none(math.sqrt(d["sq"])) if math.isfinite(d["sq"]) else None}
        if ref_state is not None:
            ref_norm = math.sqrt(d["ref_sq"]) if math.isfinite(d["ref_sq"]) else None
            diff_norm = math.sqrt(d["diff_sq"]) if math.isfinite(d["diff_sq"]) else None
            row["compared_all_tensors"] = d["compared"]
            row["ref_norm"] = finite_or_none(ref_norm)
            row["diff_norm"] = finite_or_none(diff_norm)
            row["rel_change_pct"] = (finite_or_none(100.0 * diff_norm / ref_norm)
                                     if (diff_norm is not None and ref_norm) else None)
        if p in bn:
            row["bn_dead_units"] = bn[p]["dead_units"]
            row["bn_units"] = bn[p]["units"]
        table.append(row)

    out = {"layers": table, "bn": bn, "shape_mismatch": shape_mismatch}
    if ref_state is not None:
        out["keys_only_in_reference"] = sorted(set(ref_state) - set(state))
        out["keys_only_in_checkpoint"] = sorted(set(state) - set(ref_state))
    return out


def summarize(nan_inf: dict, ana: dict, with_ref: bool) -> dict:
    nan_inf_total = sum(nan_inf.values())
    bn_dead = sum(b["dead_units"] for b in ana["bn"].values())
    bn_units = sum(b["units"] for b in ana["bn"].values())
    s = {"nan_inf_total": nan_inf_total,
         "nan_inf_tensors": sorted(k for k, v in nan_inf.items() if v),
         "bn_layers": len(ana["bn"]), "bn_dead_total": bn_dead, "bn_units_total": bn_units,
         "layers": len(ana["layers"])}
    reasons, notes = [], []
    if nan_inf_total:
        reasons.append(f"{nan_inf_total} NaN/Inf-Werte in {len(s['nan_inf_tensors'])} Tensoren")
    if bn_dead:
        reasons.append(f"{bn_dead} BN-Einheiten mit |gamma| < {BN_DEAD_THRESHOLD:g}")
    if with_ref:
        rated = [r for r in ana["layers"] if r.get("rel_change_pct") is not None
                 and r.get("compared_all_tensors")]
        if rated:
            lo = min(rated, key=lambda r: r["rel_change_pct"])
            hi = max(rated, key=lambda r: r["rel_change_pct"])
            s["rel_change_min_pct"] = {"layer": lo["layer"], "value": lo["rel_change_pct"]}
            s["rel_change_max_pct"] = {"layer": hi["layer"], "value": hi["rel_change_pct"]}
        s["layers_rated"] = len(rated)
        if ana["keys_only_in_reference"]:
            notes.append(f"{len(ana['keys_only_in_reference'])} Schluessel nur in der Referenz")
        if ana["keys_only_in_checkpoint"]:
            notes.append(f"{len(ana['keys_only_in_checkpoint'])} Schluessel nur im Checkpoint")
        if ana["shape_mismatch"]:
            notes.append(f"{len(ana['shape_mismatch'])} Formabweichungen")
    s["verdict"] = "gesund" if not reasons else "ROT"
    s["verdict_reasons"] = reasons
    s["notes"] = notes
    return s


def fmt(x, spec):
    return format(x, spec) if x is not None else "-"


def print_table(name: str, meta: dict, ana: dict, summary: dict, with_ref: bool) -> None:
    print(f"\n=== {name}  (version={meta.get('version')}, epochs={meta.get('epochs')}, "
          f"selected_by={meta.get('selected_by')})", flush=True)
    w = max([len(r["layer"]) for r in ana["layers"]] + [7])
    head = f"{'Schicht':<{w}}  {'Norm':>11}"
    if with_ref:
        head += f"  {'Diff-Norm':>11}  {'rel. %':>8}"
    head += f"  {'BN-tot':>9}"
    print(head, flush=True)
    for r in ana["layers"]:
        line = f"{r['layer']:<{w}}  {fmt(r['norm'], '11.4f')}"
        if with_ref:
            mark = "" if r.get("compared_all_tensors", True) else " *"
            line += f"  {fmt(r.get('diff_norm'), '11.4f')}  {fmt(r.get('rel_change_pct'), '8.2f')}{mark}"
        if "bn_units" in r:
            line += f"  {r['bn_dead_units']:>4}/{r['bn_units']:<4}"
        print(line, flush=True)
    lo, hi = summary.get("rel_change_min_pct"), summary.get("rel_change_max_pct")
    rng = (f"; rel. Aenderung {lo['value']:.2f} % ({lo['layer']}) bis {hi['value']:.2f} % "
           f"({hi['layer']})" if lo and hi else "")
    print(f"-> NaN/Inf {summary['nan_inf_total']}; BN-tot {summary['bn_dead_total']}/"
          f"{summary['bn_units_total']} in {summary['bn_layers']} BN-Schichten{rng}; "
          f"Verdikt {summary['verdict']}"
          + (f" ({'; '.join(summary['verdict_reasons'])})" if summary['verdict_reasons'] else "")
          + (f"; Hinweise: {'; '.join(summary['notes'])}" if summary['notes'] else ""), flush=True)
    if with_ref and any(not r.get("compared_all_tensors", True) for r in ana["layers"]):
        print("   * = Schicht nicht vollstaendig vergleichbar (Schluessel fehlt oder Form weicht ab)",
              flush=True)


DEFINITIONS = {
    "layer": "Praefix des state_dict-Schluessels vor dem letzten Punkt (z.B. 'value_head.2' "
             "fuer 'value_head.2.weight'/'value_head.2.bias').",
    "norm": "Frobenius-Norm ueber ALLE Gleitkomma-Tensoren der Schicht zusammen (weight und bias "
            "gemeinsam, float64), OHNE BN-Buffer running_mean/running_var/num_batches_tracked.",
    "diff_norm": "Frobenius-Norm von (Checkpoint - Referenz) ueber dieselben Tensoren; nur "
                 "Tensoren mit gleichem Schluessel und gleicher Form.",
    "rel_change_pct": "100 * diff_norm / ref_norm je Schicht (ref_norm = Norm der Referenz ueber "
                      "dieselben Tensoren). In min/max gehen nur Schichten ein, deren Tensoren "
                      "alle vergleichbar sind.",
    "nan_inf": "Anzahl nicht-endlicher Werte (NaN, +Inf, -Inf) je Tensor, ueber ALLE Tensoren "
               "des state_dict einschliesslich BN-Buffer; Ganzzahl-Tensoren zaehlen 0.",
    "bn_layer": "Schicht mit '<p>.weight' UND '<p>.running_mean' im state_dict.",
    "bn_dead": f"BN-Einheiten mit |gamma| < {BN_DEAD_THRESHOLD:g} (gamma = '<p>.weight'); "
               "Ersatzgroesse fuer tote Einheiten, Aktivierungen NICHT gemessen (wie par.10).",
    "verdict": "'gesund', wenn nan_inf_total == 0 und bn_dead_total == 0, sonst 'ROT' mit Grund "
               "(par.10 setzt keine Schwelle fuer die relative Aenderung; sie wird nur berichtet). "
               "Schluessel-/Formabweichungen sind Hinweise, kein Verdiktgrund.",
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--reference", required=True, type=Path, help="Warmstart-Checkpoint (.pth)")
    ap.add_argument("--checkpoints", required=True, nargs="+", type=Path)
    ap.add_argument("--out", required=True, type=Path, help="Artefakt-JSON")
    ap.add_argument("--threads", type=int, default=1, help="torch-Threads (Default 1)")
    args = ap.parse_args()

    for p in [args.reference, *args.checkpoints]:
        if not p.exists():
            sys.exit(f"FEHLER: {p} fehlt -- Abbruch.")

    t_wall, t_cpu = time.time(), time.process_time()
    import torch
    torch.set_num_threads(max(1, args.threads))
    started = datetime.now().isoformat(timespec="seconds")
    print(f"checkpoint_weight_health: Referenz {rel(args.reference)}, "
          f"{len(args.checkpoints)} Checkpoint(s), torch {torch.__version__}, "
          f"threads {torch.get_num_threads()}", flush=True)

    ref_state, ref_meta = load_checkpoint(args.reference, torch)
    ref_nan = nan_inf_per_tensor(ref_state, torch)
    ref_ana = analyse(ref_state, None, torch)
    ref_sum = summarize(ref_nan, ref_ana, with_ref=False)
    print_table(f"REFERENZ {rel(args.reference)}", ref_meta, ref_ana, ref_sum, with_ref=False)
    reference_entry = {"path": rel(args.reference), "sha256": sha256_of(args.reference),
                       "meta": ref_meta, "summary": ref_sum, "nan_inf_per_tensor": ref_nan,
                       "layers": ref_ana["layers"], "bn": ref_ana["bn"]}

    entries = []
    for i, cp in enumerate(args.checkpoints, 1):
        t0 = time.time()
        state, meta = load_checkpoint(cp, torch)
        nan = nan_inf_per_tensor(state, torch)
        ana = analyse(state, ref_state, torch)
        summ = summarize(nan, ana, with_ref=True)
        print_table(f"[{i}/{len(args.checkpoints)}] {rel(cp)}", meta, ana, summ, with_ref=True)
        entries.append({"path": rel(cp), "sha256": sha256_of(cp), "meta": meta,
                        "summary": summ, "nan_inf_per_tensor": nan, "layers": ana["layers"],
                        "bn": ana["bn"], "keys_only_in_reference": ana["keys_only_in_reference"],
                        "keys_only_in_checkpoint": ana["keys_only_in_checkpoint"],
                        "shape_mismatch": ana["shape_mismatch"],
                        "seconds": round(time.time() - t0, 3)})
        del state

    all_healthy = ref_sum["verdict"] == "gesund" and all(
        e["summary"]["verdict"] == "gesund" for e in entries)
    wall, cpu = time.time() - t_wall, time.process_time() - t_cpu
    n_files = 1 + len(entries)
    result = {
        "tool": "tools/checkpoint_weight_health.py",
        "prereg": PREREG,
        "started": started,
        **git_state(),
        "torch_version": torch.__version__,
        "definitions": DEFINITIONS,
        "reference": reference_entry,
        "checkpoints": entries,
        "verdict_overall": "gesund" if all_healthy else "ROT",
        "laufzeit": {"wanduhr_s": round(wall, 3), "cpu_s": round(cpu, 3),
                     "threads": torch.get_num_threads(),
                     # Grundmenge: alle geladenen Dateien (Referenz eingeschlossen).
                     "s_je_checkpoint": round(wall / n_files, 3),
                     "dateien": n_files},
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    tmp = args.out.with_suffix(args.out.suffix + ".tmp")
    tmp.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False),
                   encoding="utf-8")
    tmp.replace(args.out)
    print(f"\nGesamtverdikt {result['verdict_overall']}; Artefakt {rel(args.out)}; "
          f"Wanduhr {wall:.1f} s, CPU {cpu:.1f} s", flush=True)


if __name__ == "__main__":
    main()
