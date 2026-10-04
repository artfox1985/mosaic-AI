# -*- coding: utf-8 -*-
"""tools/checkpoint_val_eval.py -- Trainings-Checkpoints auf einer Val-Dateiliste
GENAU SO auswerten, wie train.py seine Validierung rechnet, gesamt und je Klasse.

Zweck (PREREG_v35_window.md par.11b): (1) "Epoche 0" -- Val-Brier und Policy-Val des
ungetrainierten Warmstarts gegen die trainierten Checkpoints derselben Val-Menge;
(2) dieselben Groessen je Klasse des Fensters (Zuordnung ueber den Basename-Praefix
`<class-prefix><klasse>_`, mit Unterstrich: "policy_" trifft nicht "policy-s100_").

WAS WIEDERVERWENDET WIRD (nichts davon ist hier nachgebaut):
  * Val-Datensatz: `corpus_dataset.MosaicDataset(str(DATA_DIR), files=val_files, ...)`
    mit denselben Argumenten wie train.py (Val-Zweig) und danach
    `apply_value_target_lambda(lambda, wdl=...)` wie dort. Der Cache wird ueber den
    errechneten Fenster-Schluessel gefunden (`window_cache_key`); fehlt er, bricht das
    Werkzeug ab, statt still seriell neu zu bauen (`--allow-build` erlaubt es).
  * Metriken: `train._validate_one_epoch` mit `train.LossSetup`, ueber einen
    DataLoader in der Bauform von train.py --fast-loader (BatchSampler ueber
    SequentialSampler, Batchgroesse `config.BATCH_SIZE`, drop_last=False). Fuer eine
    Klasse laeuft derselbe Aufruf auf der Zeilen-Teilmenge ihrer Dateien in
    Dateireihenfolge -- das ist der Datensatz, den train.py fuer eine reine
    Klassen-Val-Liste baute (Herleitung, nicht gemessen: jede Zeile haengt nur an
    ihrer Datei, die sortierte Teilliste ist eine Teilfolge der sortierten
    Gesamtliste).
  * Modell: `neural_net.build_model_from_checkpoint` (Architektur aus dem Checkpoint).

WAS HIER ZUSAETZLICH GERECHNET WIRD: ein zweiter Durchgang Datei fuer Datei mit
Summen je Datei (Brier-Quadratfehler/Anzahl, Policy-CE*pol_w/pol_w, Wert-BCE*w/w).
Daraus kommen die POOLED-Werte (Summe/Summe, batchunabhaengig) und der
Block-Bootstrap mit der DATEI als Block. Der Brier ist in train.py ohnehin ein
gepoolter Mittelwert (train.py:1046-1052, 1113), deshalb ist der pooled Brier
zahlengleich zum train.py-Brier (das Werkzeug prueft das je Liste). Policy- und
Wert-Verlust sind in train.py dagegen MITTEL DER BATCH-MITTEL (train.py:931, 1011-1014,
1078-1079) und haengen damit an Batchgroesse und Reihenfolge; deshalb stehen beide
Lesarten im Artefakt: `policy_val_loss` (train.py-gleich) und `policy_val_loss_pooled`.

DATEI-ZUORDNUNG JE ZEILE: der Val-Monolith traegt keine Dateigrenzen
(`stamp_cache_key_attrs`, corpus_dataset.py:812-836, nur Schluessel, Dateizahl,
erste/letzte Datei). Er ist aber die Verkettung der sortierten Dateien
(`window_cache_key` sortiert, corpus_dataset.py:490; Bauschleife je Datei je Record,
corpus_dataset.py:1443-1481). Die Zeilenzahl je Datei kommt aus dem Datei-Block
(`.filecache_<key>.h5`, Pfad ueber `build_cache_incremental._block_path`), ersatzweise
aus der Recordzahl der .pkl; abgenommen wird die Zuordnung ueber (a) Summe ==
Monolith-Zeilen und (b) bitgleiche Felder `rounds`, `wdl_outcome`, `values` je Datei
zwischen Block und Monolith-Ausschnitt.

SELBSTPRUEFUNG: mit `--train-manifest` vergleicht das Werkzeug jeden Checkpoint, dessen
`version` zum Manifest passt, gegen `epoch_history[epochs]` (value_val_brier,
policy_val_loss, value_val_loss, points_val_loss; Toleranz `--selfcheck-tol`).

Aufruf (Selbstpruefung plus Epoche 0 plus Klassen, PREREG_v35_window.md par.11b):
    python -X utf8 -u tools/checkpoint_val_eval.py \\
        --checkpoints models/alphazero_v34-b01_brierbest.pth \\
                      models/alphazero_v35-b01_best.pth models/alphazero_v35-b01.pth \\
        --val-list data/window_v35_val.txt \\
        --classes value-deviate value-excursion policy policy-s100 policy-dice-v2-r1 \\
        --class-prefix selfplay_v34-b01- \\
        --train-manifest models/manifest_train_v35-b01_20261004_200022.json \\
        --out evaluations/artifacts/checkpoint_val_eval_v35.json

Rechenlast: ein Modell je Checkpoint auf GPU/CPU, drei Vorwaertsdurchgaenge ueber die
Val-Menge je Checkpoint. Laeuft EXKLUSIV wie jede netzgestuetzte Sonde (CLAUDE.md).
"""
import argparse
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "engine" / "py"))
sys.path.insert(0, str(_ROOT / "tools"))

PREREG = "PREREG_v35_window.md par.11b"
BOOTSTRAP_SEED_DEFAULT = 20261004
BOOTSTRAP_DRAWS_DEFAULT = 1000

# Umgebung des Trainingslaufs v35-b01, wenn kein --train-manifest angegeben ist.
# Pruefstellen: tools/night_v35_chain.sh:41-54 und `mosaic_env` in
# models/manifest_train_v35-b01_20261004_200022.json (dort zusaetzlich
# MOSAIC_MOON_TARGET_SOURCE=label, das train.py selbst aus dem Flag setzt, train.py:3527).
BUILTIN_ENV_V35 = {
    "MOSAIC_CARRIER_MANIFEST": "policy_carrier_manifest_v35.json",
    "MOSAIC_DATA_EXCLUDE": ("selfplay_v29-b11-probe_|selfplay_depth|selfplay_s4states|"
                            "selfplay_tor2a|selfplay_probe-|selfplay_x35|selfplay_x35e2"),
    "MOSAIC_FEATURES_FROM_RUST": "1",
    "MOSAIC_IGNORE_POLICY_TARGET_VALID": "1",
    "MOSAIC_MASK_DICE_PHASE_VALUE": "1",
    "MOSAIC_MOON_TARGET_SOURCE": "label",
    "MOSAIC_VAL_POOL": "^selfplay_v34-b01-",
}

# Rezept-Teil, der Val-Datensatz und Val-Verlust bestimmt (cli_args des v35-b01-Manifests).
BUILTIN_RECIPE_V35 = {
    "value_target_variant": "nortv", "encoder": "2d", "conjunction_head": False,
    "moon_target_source": "label", "value_target_lambda": 0.7, "value_head": "wdl",
    "wdl_hard_only": False, "wdl_label_smooth": 0.0, "wdl_bootstrap_destretch": False,
    "destretch_a": 0.0051, "destretch_b": 1.9269, "exclude_round5": False,
    "ranking_loss_weight": 0.0, "margin_thresholds": False, "ownership_weight": 0.0,
    "moon_loss_weight": 0.0, "surprise_alpha": 0.0, "surprise_confidence_min": 0.0,
    "value_weight": None, "points_weight": None,
}

# Felder je Datei im zweiten Durchgang (Reihenfolge = Spalten in `per_file`).
PER_FILE_FIELDS = ["n_samples", "n_policy_samples", "brier_sqerr_sum", "brier_n",
                   "policy_ce_w_sum", "policy_w_sum", "value_loss_w_sum", "value_w_sum",
                   "brier_vw_sqerr_sum", "brier_vw_n"]

# Vergleichsfelder der Selbstpruefung: Manifest-Feld -> Schluessel von _validate_one_epoch.
SELFCHECK_FIELDS = {"value_val_brier": "epoch_val_brier", "policy_val_loss": "epoch_val_ploss",
                    "value_val_loss": "epoch_val_vloss", "points_val_loss": "epoch_val_pointsloss"}


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


def json_safe(v):
    """NaN/Inf -> None, Tensor/numpy-Skalare -> Python-Zahl, rekursiv."""
    import math
    if isinstance(v, dict):
        return {str(k): json_safe(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [json_safe(x) for x in v]
    if hasattr(v, "item") and not isinstance(v, (str, bytes)):
        try:
            v = v.item()
        except Exception:
            return str(v)
    if isinstance(v, float) and not math.isfinite(v):
        return None
    if isinstance(v, (int, float, str, bool)) or v is None:
        return v
    return str(v)


def read_list(path) -> list[str]:
    """Basenames einer Dateiliste, Kommentarzeilen (#) und Leerzeilen raus -- dieselbe
    Leseregel wie train.py --file-list (train.py:1423-1426)."""
    out = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#"):
            out.append(os.path.basename(line))
    return out


# ---------------------------------------------------------------------------
# Umgebung und Rezept -- MUSS vor jedem Projekt-Import stehen
# ---------------------------------------------------------------------------

def resolve_env_and_recipe(args) -> tuple[dict, dict, str, dict | None]:
    """Ziel-Umgebung und Rezept bestimmen und die Umgebung setzen.

    Quelle ist das Trainings-Manifest (`mosaic_env`, `cli_args`), sonst die
    eingebauten v35-Werte. Fehlende Variablen werden gesetzt (mit Ausgabe); eine
    GESETZTE Variable mit anderem Wert ist ein harter Abbruch, denn sie aendert den
    Cache-Schluessel oder die Daten (`neural_net._IGNORE_PTV` wird beim Import
    gelesen, engine/py/neural_net.py:9). Gibt (env, recipe, quelle, manifest) zurueck.
    """
    manifest = None
    if args.train_manifest:
        manifest = json.load(open(args.train_manifest, encoding="utf-8"))
        target_env = dict(manifest.get("mosaic_env") or {})
        cli = manifest.get("cli_args") or {}
        recipe = {k: cli.get(k, v) for k, v in BUILTIN_RECIPE_V35.items()}
        source = rel(args.train_manifest)
    else:
        target_env = dict(BUILTIN_ENV_V35)
        recipe = dict(BUILTIN_RECIPE_V35)
        source = "builtin_v35 (tools/night_v35_chain.sh:41-54, manifest_train_v35-b01)"
    applied, conflicts = [], []
    for k, v in sorted(target_env.items()):
        have = os.environ.get(k)
        if have is None:
            os.environ[k] = str(v)
            applied.append(k)
            print(f"   env gesetzt: {k}={v}", flush=True)
        elif have != str(v):
            conflicts.append(f"{k}: Umgebung={have!r}, Ziel={v!r}")
    if conflicts:
        raise SystemExit("ABBRUCH: MOSAIC_*-Umgebung weicht vom Trainingslauf ab "
                         "(anderer Cache-Schluessel oder andere Daten):\n   "
                         + "\n   ".join(conflicts)
                         + "\n   Variablen in der Shell angleichen oder entfernen.")
    extra = sorted(k for k in os.environ if k.startswith("MOSAIC_") and k not in target_env)
    if extra:
        print(f"WARNUNG: MOSAIC_*-Variablen ausserhalb der Trainings-Umgebung gesetzt: {extra} "
              f"-- sie stehen nicht im Manifest des Laufs; pruefen, ob sie Daten aendern.",
              flush=True)
    return {"target": target_env, "applied_by_tool": applied, "extra_in_shell": extra}, \
        recipe, source, manifest


# ---------------------------------------------------------------------------
# Datei-Zuordnung je Zeile
# ---------------------------------------------------------------------------

def file_row_ranges(val_files, ds, recipe, data_dir) -> tuple[list, dict]:
    """(basename, start, stop) je Datei in Monolith-Reihenfolge plus Abnahmeprotokoll.

    Zeilenzahl aus dem Datei-Block (`build_cache_incremental._block_path`), sonst aus
    der Recordzahl der .pkl (`corpus_io.load_records_fh`, gzip-faehig). Abnahme:
    Summe == len(ds) und bitgleiche Felder je Datei, wo ein Block liegt.
    """
    import h5py
    import numpy as np
    from build_cache_incremental import _block_path
    from corpus_io import load_records_fh

    kwargs = {"value_target_variant": recipe["value_target_variant"],
              "encoder": recipe["encoder"], "conjunction_head": bool(recipe["conjunction_head"])}
    fields = ("rounds", "wdl_outcome", "values")
    ranges, start = [], 0
    n_block, n_pkl, mismatches = 0, 0, []
    for f in val_files:
        b = os.path.basename(f)
        bp = _block_path(str(data_dir), b, kwargs)
        block_arrays = None
        if os.path.exists(bp):
            with h5py.File(bp, "r") as hf:
                n = int(hf["values"].shape[0])
                block_arrays = {k: hf[k][:] for k in fields if k in hf}
            n_block += 1
        else:
            with open(f, "rb") as fh:
                n = len(load_records_fh(fh))
            n_pkl += 1
        stop = start + n
        if block_arrays is not None and stop <= len(ds):
            for k, arr in block_arrays.items():
                mono = getattr(ds, k)[start:stop].numpy()
                is_float = mono.dtype.kind == "f"
                if mono.shape != arr.shape or not np.array_equal(mono, arr, equal_nan=is_float):
                    mismatches.append(f"{b}:{k}")
        ranges.append((b, start, stop))
        start = stop
    report = {"rows_from_block": n_block, "rows_from_pkl_count": n_pkl,
              "checked_fields": list(fields), "rows_sum": start, "rows_monolith": len(ds),
              "field_mismatches": mismatches[:50], "n_field_mismatches": len(mismatches)}
    if start != len(ds):
        raise SystemExit(f"ABBRUCH: Zeilensumme je Datei {start} != Monolith-Zeilen {len(ds)} "
                         f"-- Datei-Zuordnung nicht moeglich.")
    if mismatches:
        raise SystemExit(f"ABBRUCH: {len(mismatches)} Feld-Abweichungen zwischen Block und "
                         f"Monolith-Ausschnitt, z.B. {mismatches[:5]} -- Zuordnung unsicher.")
    return ranges, report


# ---------------------------------------------------------------------------
# Auswertung
# ---------------------------------------------------------------------------

def make_row_view_class():
    import torch

    class RowBatchView(torch.utils.data.Dataset):
        """Batchweises Holen wie train.py `_BatchView` (train.py:1735-1743), aber
        ueber eine Zeilen-Teilmenge: Index-Liste des Samplers -> Monolith-Zeilen."""

        def __init__(self, ds, rows):
            self.ds = ds
            self.rows = rows

        def __len__(self):
            return len(self.rows)

        def __getitem__(self, indices):
            return self.ds.get_batch(self.rows[torch.as_tensor(indices, dtype=torch.long)])

    return RowBatchView


def train_py_validation(train_mod, model, ds, rows, encoder, device, loss_setup, batch_size):
    """`train._validate_one_epoch` auf einer Zeilenmenge, Lader wie train.py
    --fast-loader im Val-Zweig (train.py:1750-1754)."""
    import torch
    from torch.utils.data import BatchSampler, DataLoader, SequentialSampler
    view = make_row_view_class()(ds, rows)
    loader = DataLoader(view, batch_size=None,
                        sampler=BatchSampler(SequentialSampler(range(len(rows))), batch_size,
                                             drop_last=False),
                        pin_memory=torch.cuda.is_available())
    return train_mod._validate_one_epoch(model, loader, ds, device, encoder, loss_setup)


def per_file_pass(train_mod, model, ds, ranges, encoder, device, recipe, batch_size, label):
    """Summen je Datei, Formeln wie `_validate_one_epoch`, aber je Zeile summiert:

    * Brier: Maske `wdl_outcome >= 0`, ((pred_v+1)/2 - outcome)^2 (train.py:1046-1052),
      OHNE Wertgewicht -- genau wie train.py.
    * Policy: CE gegen die maskierte log_softmax, Gewicht pol_w (mal Runde != 5 bei
      exclude_round5) (train.py:926-931).
    * Wert: WDL-BCE mit logit_diff gegen values_wdl, Gewicht rw = (Runde-Maske) *
      value_weights (train.py:929-936, 955-990); tanh-Kopf: MSE (train.py:999-1004).
    Batchgroesse egal (eval-Modus, BatchNorm mit Laufstatistik).
    """
    import torch
    import torch.nn.functional as F
    from neural_net import unpack_masks_batch, unpack_planes_batch

    model.eval()
    has_vw = getattr(ds, "value_weights", None) is not None
    out = {}
    t0 = time.time()
    with torch.no_grad():
        for j, (name, start, stop) in enumerate(ranges):
            acc = [0, 0, 0.0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0]
            for b0 in range(start, stop, batch_size):
                idx = torch.arange(b0, min(b0 + batch_size, stop), dtype=torch.long)
                batch = ds.get_batch(idx)
                vw = None
                if has_vw:
                    vw, batch = batch[-1], batch[:-1]
                if encoder == "2d":
                    planes, rest = batch[0], batch[1:]
                else:
                    planes, rest = None, batch
                (states, targets_p, targets_v, masks, _moon, pol_w, _t_points, rounds, _own,
                 _t_opp, _opp_mask, targets_v_wdl, wdl_outcome, _t_eg, _eg_mask,
                 _rk_ids, _rk_q, _rk_mask) = rest
                if ds.bitpacked:
                    masks = unpack_masks_batch(masks)
                    if planes is not None:
                        planes = unpack_planes_batch(planes)
                states = states.to(device).float()
                masks = masks.to(device).float()
                targets_p = targets_p.to(device).float()
                pol_w = pol_w.to(device).float().view(-1)
                rounds = rounds.to(device).view(-1)
                wdl_outcome = wdl_outcome.to(device).float().view(-1)
                if planes is not None:
                    outp = model(planes.to(device).float(), states)
                else:
                    outp = model(states)
                pred_p, pred_v = outp[0], outp[1]
                _, wdl_logits, _, _ = train_mod._unpack_optional_outputs(model, outp)
                n_b = int(idx.numel())
                # Policy
                log_probs = F.log_softmax(pred_p + (masks - 1) * 1e9, dim=1)
                ce = -torch.sum(targets_p * log_probs, dim=1)
                w = pol_w
                round_mask = (rounds != 5).float() if recipe["exclude_round5"] else None
                if round_mask is not None:
                    w = w * round_mask
                # Brier
                p_win = ((pred_v.view(-1) + 1.0) * 0.5).float()
                bmask = (wdl_outcome >= 0.0).float()
                bsq = ((p_win - wdl_outcome.clamp(min=0.0)) ** 2) * bmask
                # Zweite Brier-Groesse (PREREG_v35_window.md par.11b, Nachtrag): dieselbe
                # Maske UND value_weights > 0, also ohne die Wuerfelphasen-Records. Ohne
                # Feld ist sie per Konstruktion gleich dem ungewichteten Brier.
                bmask_vw = bmask if vw is None else bmask * (vw.to(device).float().view(-1) > 0).float()
                bsq_vw = ((p_win - wdl_outcome.clamp(min=0.0)) ** 2) * bmask_vw
                # Wert-Verlust mit Gewicht rw
                rw = torch.ones(n_b, device=device)
                if round_mask is not None:
                    rw = rw * round_mask
                if vw is not None:
                    rw = rw * vw.to(device).float().view(-1)
                if wdl_logits is not None:
                    logit_diff = wdl_logits[:, 1] - wdl_logits[:, 0]
                    target = targets_v_wdl.to(device).float().view(-1)
                    if recipe["wdl_bootstrap_destretch"]:
                        target = train_mod._destretch_wdl_target(
                            target, wdl_outcome, recipe["destretch_a"], recipe["destretch_b"])
                    if recipe["wdl_hard_only"]:
                        rw = rw * (wdl_outcome >= 0.0).float()
                        target = wdl_outcome.clamp(min=0.0)
                        s = float(recipe["wdl_label_smooth"] or 0.0)
                        if s > 0.0:
                            target = target * (1.0 - s) + 0.5 * s
                    vloss = F.binary_cross_entropy_with_logits(logit_diff, target, reduction="none")
                else:
                    tv = targets_v.to(device).float()
                    vloss = ((pred_v - tv) ** 2).view(n_b, -1).sum(dim=1)
                acc[0] += n_b
                acc[1] += int((pol_w > 0).sum().item())
                acc[2] += float(bsq.double().sum().item())
                acc[3] += int(bmask.sum().item())
                acc[4] += float((ce * w).double().sum().item())
                acc[5] += float(w.double().sum().item())
                acc[6] += float((vloss * rw).double().sum().item())
                acc[7] += float(rw.double().sum().item())
                acc[8] += float(bsq_vw.double().sum().item())
                acc[9] += int(bmask_vw.sum().item())
            out[name] = acc
            if (j + 1) % 10 == 0 or j + 1 == len(ranges):
                print(f"   [{label}] Datei {j + 1}/{len(ranges)}, {stop:,} Zeilen, "
                      f"{time.time() - t0:.1f} s", flush=True)
    return out


def pooled(per_file, names) -> dict:
    """Gepoolte Kennzahlen (Summe/Summe) einer Dateimenge."""
    tot = [0.0] * len(PER_FILE_FIELDS)
    for n in names:
        for i, v in enumerate(per_file[n]):
            tot[i] += v
    d = dict(zip(PER_FILE_FIELDS, tot))

    def ratio(a, b):
        return a / b if b > 0 else None
    return {"n_samples": int(d["n_samples"]), "n_policy_samples": int(d["n_policy_samples"]),
            "n_brier_samples": int(d["brier_n"]),
            "n_brier_vw": int(d["brier_vw_n"]),
            "value_val_brier_pooled": ratio(d["brier_sqerr_sum"], d["brier_n"]),
            "value_val_brier_vw": ratio(d["brier_vw_sqerr_sum"], d["brier_vw_n"]),
            "policy_val_loss_pooled": ratio(d["policy_ce_w_sum"], d["policy_w_sum"]),
            "value_val_loss_pooled": ratio(d["value_loss_w_sum"], d["value_w_sum"]),
            "policy_w_sum": d["policy_w_sum"], "value_w_sum": d["value_w_sum"]}


def bootstrap_draws(per_file, names, idx, num_field, den_field):
    """Verhaeltnis Summe/Summe je Ziehung; idx: [B, m] Dateiindizes."""
    import numpy as np
    i_num, i_den = PER_FILE_FIELDS.index(num_field), PER_FILE_FIELDS.index(den_field)
    num = np.array([per_file[n][i_num] for n in names], dtype=np.float64)
    den = np.array([per_file[n][i_den] for n in names], dtype=np.float64)
    s_num, s_den = num[idx].sum(axis=1), den[idx].sum(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(s_den > 0, s_num / s_den, np.nan)


def ci95(draws):
    import numpy as np
    d = draws[np.isfinite(draws)]
    if d.size == 0:
        return None
    return [float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))]


def model_arch(model, encoder, ckpt_state) -> dict:
    from neural_net import model_input_widths
    flat_in, planes_c = model_input_widths(model, encoder)
    mk, ck = set(model.state_dict().keys()), set(ckpt_state.keys())
    # Policy-Breite wie build_model_from_checkpoint sie ableitet (neural_net.py:2447-2449).
    pk = "policy_head.2.weight" if "policy_head.2.weight" in ckpt_state else "policy_head.0.weight"
    return {"encoder": encoder, "flat_input": flat_in, "planes_channels": planes_c,
            "num_actions": int(ckpt_state[pk].shape[0]) if pk in ckpt_state else None,
            "value_head_variant": getattr(model, "value_head_variant", None),
            "opp_points_head": bool(getattr(model, "has_opp_points_head", False)),
            "endgame_head": bool(getattr(model, "has_endgame_head", False)),
            "points_dist_bins": int(getattr(model, "points_dist_bins", 0) or 0),
            "missing_keys": sorted(mk - ck), "unexpected_keys": sorted(ck - mk)}


def self_check(meta, metrics, manifest, tol, n_val_rows, batch_size) -> dict:
    if manifest is None:
        return {"status": "not_applicable", "reason": "kein --train-manifest"}
    if meta.get("version") != manifest.get("version"):
        return {"status": "not_applicable",
                "reason": f"Checkpoint-Version {meta.get('version')!r} != Manifest-Version "
                          f"{manifest.get('version')!r}"}
    ep = meta.get("epochs")
    entry = next((e for e in manifest.get("epoch_history") or [] if e.get("epoch") == ep), None)
    if entry is None:
        return {"status": "FAIL", "reason": f"keine Epoche {ep} in epoch_history"}
    rows, ok = {}, True
    for mf, vk in SELFCHECK_FIELDS.items():
        expected, actual = entry.get(mf), metrics.get(vk)
        if expected is None or actual is None:
            rows[mf] = {"expected": expected, "actual": actual, "abs_diff": None,
                        "ok": expected is None and actual is None}
        else:
            d = abs(float(actual) - float(expected))
            rows[mf] = {"expected": expected, "actual": actual, "abs_diff": d, "ok": d <= tol}
        ok = ok and rows[mf]["ok"]
    info = {"num_val_games_ckpt": meta.get("num_val_games"), "num_val_rows_now": n_val_rows,
            "batch_size_ckpt": meta.get("batch_size"), "batch_size_now": batch_size}
    if meta.get("num_val_games") not in (None, n_val_rows):
        ok = False
    return {"status": "PASS" if ok else "FAIL", "epoch": ep, "tolerance": tol,
            "fields": rows, **info}


# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--checkpoints", nargs="+", required=True,
                    help=".pth-Dateien; der ERSTE ist die Referenz der Differenzen "
                         "(Warmstart minus Checkpoint), siehe --reference")
    ap.add_argument("--reference", default=None,
                    help="Referenz-Checkpoint der Differenzen (Default: erster in --checkpoints)")
    ap.add_argument("--val-list", required=True, help="Val-Dateiliste (Basenames)")
    ap.add_argument("--classes", nargs="*", default=[])
    ap.add_argument("--class-prefix", default="",
                    help="Basename-Praefix vor dem Klassennamen; Datei gehoert zur Klasse k, "
                         "wenn sie mit <prefix><k>_ beginnt")
    ap.add_argument("--train-manifest", default=None,
                    help="Trainings-Manifest: Quelle fuer MOSAIC_*-Umgebung und Rezept, und "
                         "Referenz der Selbstpruefung (epoch_history)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--batch-size", type=int, default=4096,
                    help="nur fuer den Datei-Durchgang; der train.py-gleiche Durchgang laeuft "
                         "immer mit config.BATCH_SIZE (Policy-/Wert-Verlust sind dort Batch-Mittel)")
    ap.add_argument("--device", default=None, choices=["cuda", "cpu"])
    ap.add_argument("--threads", type=int, default=None, help="torch.set_num_threads")
    ap.add_argument("--bootstrap-draws", type=int, default=BOOTSTRAP_DRAWS_DEFAULT)
    ap.add_argument("--bootstrap-seed", type=int, default=BOOTSTRAP_SEED_DEFAULT)
    ap.add_argument("--selfcheck-tol", type=float, default=1e-4)
    ap.add_argument("--allow-build", action="store_true",
                    help="fehlenden Val-Cache seriell bauen lassen (Default: Abbruch)")
    ap.add_argument("--no-sublists", action="store_true",
                    help="Klassen-Teillisten nicht nach <val-list>_<klasse>.txt schreiben")
    args = ap.parse_args()

    t_wall0, t_cpu0 = time.time(), time.process_time()
    print(f"== checkpoint_val_eval ({PREREG}) Start {datetime.now():%Y-%m-%d %H:%M:%S}", flush=True)

    # 1. Umgebung VOR jedem Projekt-Import
    env_report, recipe, recipe_source, manifest = resolve_env_and_recipe(args)
    if recipe.get("margin_thresholds"):
        raise SystemExit("ABBRUCH: --margin-thresholds-Rezept wird nicht unterstuetzt "
                         "(Val-Batch traegt final_margin, die Rundenskalen fehlen hier).")

    import numpy as np
    import torch
    import torch.nn as nn
    import train as train_mod  # Modulkopf: nur Importe und Konstanten (train.py:1-314)
    from config import BATCH_SIZE, DATA_DIR, POINTS_WEIGHT, VALUE_WEIGHT
    import corpus_dataset
    from neural_net import build_model_from_checkpoint

    if args.threads:
        torch.set_num_threads(args.threads)
    device = torch.device(args.device or ("cuda" if torch.cuda.is_available() else "cpu"))
    if device.type == "cuda" and not torch.cuda.is_available():
        raise SystemExit("ABBRUCH: --device cuda, aber keine CUDA-Karte verfuegbar.")
    print(f"   Geraet {device.type}, torch-Threads {torch.get_num_threads()}, "
          f"train.py-Batch {BATCH_SIZE}, Datei-Batch {args.batch_size}", flush=True)

    ckpt_paths = [Path(p) for p in args.checkpoints]
    for p in ckpt_paths:
        if not p.exists():
            raise SystemExit(f"ABBRUCH: Checkpoint fehlt: {p}")
    ref_path = Path(args.reference) if args.reference else ckpt_paths[0]
    if ref_path.resolve() not in [p.resolve() for p in ckpt_paths]:
        raise SystemExit(f"ABBRUCH: --reference {ref_path} steht nicht in --checkpoints")

    # 2. Val-Dateien in train.py-Pfadform (glob ueber DATA_DIR, train.py:1378, 1427-1435)
    wanted = read_list(args.val_list)
    have = {os.path.basename(f): f for f in glob.glob(str(DATA_DIR / "*.pkl"))}
    missing = [n for n in wanted if n not in have]
    if missing:
        raise SystemExit(f"ABBRUCH: {len(missing)} Val-Dateien fehlen in data/, z.B. {missing[:3]}")
    if len(set(wanted)) != len(wanted):
        raise SystemExit("ABBRUCH: doppelte Eintraege in der Val-Liste")
    val_files = sorted(have[n] for n in wanted)

    # 3. Klassen
    classes = {}
    for k in args.classes:
        pre = f"{args.class_prefix}{k}_"
        classes[k] = [os.path.basename(f) for f in val_files if os.path.basename(f).startswith(pre)]
    assigned = {}
    for k, names in classes.items():
        for n in names:
            if n in assigned:
                raise SystemExit(f"ABBRUCH: {n} faellt in zwei Klassen ({assigned[n]}, {k})")
            assigned[n] = k
    unassigned = [os.path.basename(f) for f in val_files if os.path.basename(f) not in assigned]
    print(f"   Val-Liste {rel(args.val_list)}: {len(val_files)} Dateien; je Klasse "
          f"{ {k: len(v) for k, v in classes.items()} }; ohne Klasse {len(unassigned)}", flush=True)
    for k, names in classes.items():
        if not names:
            print(f"WARNUNG: Klasse {k!r} trifft keine Val-Datei (Praefix "
                  f"{args.class_prefix}{k}_)", flush=True)
    sublists = {}
    if not args.no_sublists:
        vl = Path(args.val_list)
        for k, names in classes.items():
            sp = vl.with_name(f"{vl.stem}_{k}.txt")
            body = (f"# Klasse {k} der Val-Liste {vl.name} (Praefix {args.class_prefix}{k}_), "
                    f"{len(names)} Dateien, tools/checkpoint_val_eval.py\n"
                    + "".join(n + "\n" for n in names))
            if not sp.exists() or sp.read_text(encoding="utf-8") != body:
                sp.write_text(body, encoding="utf-8", newline="\n")
                print(f"   Teilliste geschrieben: {rel(sp)}", flush=True)
            sublists[k] = rel(sp)

    # 4. Val-Datensatz wie train.py (train.py:1709-1712), Cache ueber den Namen
    wk = corpus_dataset.window_cache_key(
        str(DATA_DIR), val_files, value_target_variant=recipe["value_target_variant"],
        encoder=recipe["encoder"], conjunction_head=bool(recipe["conjunction_head"]),
        moon_target_source=recipe["moon_target_source"])
    if len(wk.files) != len(val_files):
        raise SystemExit(f"ABBRUCH: MOSAIC_DATA_EXCLUDE nimmt {len(val_files) - len(wk.files)} "
                         f"Val-Dateien heraus -- die Liste passt nicht zur Umgebung.")
    cache_path = DATA_DIR / f".cache_{wk.key}.h5"
    if not cache_path.exists() and not args.allow_build:
        raise SystemExit(f"ABBRUCH: Val-Cache {rel(cache_path)} (Schluessel {wk.key}) fehlt. "
                         f"Entweder weicht Umgebung/Rezept vom Trainingslauf ab, oder der Cache "
                         f"wurde geloescht. Neubau nur bewusst mit --allow-build (seriell, "
                         f"schreibt einen Monolithen).")
    t_data0 = time.time()
    ds = corpus_dataset.MosaicDataset(str(DATA_DIR), files=val_files,
                                      value_target_variant=recipe["value_target_variant"],
                                      encoder=recipe["encoder"],
                                      conjunction_head=bool(recipe["conjunction_head"]),
                                      moon_target_source=recipe["moon_target_source"])
    if ds.final_margin is not None:
        raise SystemExit("ABBRUCH: Val-Datensatz traegt final_margin (MOSAIC_CACHE_FINAL_MARGIN) "
                         "ohne Margen-Rezept -- das Batch-Tupel passt dann nicht.")
    if ds.value_weights is None and os.environ.get("MOSAIC_MASK_DICE_PHASE_VALUE") == "1":
        raise SystemExit("ABBRUCH: MOSAIC_MASK_DICE_PHASE_VALUE=1, aber kein value_weights-Feld.")

    # 5. Datei-Zuordnung (vor der Lambda-Mischung: `values` wird bei tanh gemischt)
    ranges, align_report = file_row_ranges(val_files, ds, recipe, DATA_DIR)
    lam_wdl = recipe["value_head"] == "wdl"
    root_q_frac = ds.apply_value_target_lambda(float(recipe["value_target_lambda"]), wdl=lam_wdl)
    data_s = time.time() - t_data0
    print(f"   Val-Datensatz: {len(ds):,} Zeilen, Cache {rel(cache_path)}, root_q-Anteil "
          f"{root_q_frac:.3f}, Datenaufbau {data_s:.1f} s", flush=True)

    rows_of = {}
    by_name = {n: (a, b) for n, a, b in ranges}
    lists = {"all": [n for n, _, _ in ranges]}
    lists.update({k: v for k, v in classes.items() if v})
    for lname, names in lists.items():
        parts = [torch.arange(*by_name[n], dtype=torch.long) for n in names]
        rows_of[lname] = torch.cat(parts) if parts else torch.zeros(0, dtype=torch.long)

    def eff(v, default):
        return default if v is None else v
    loss_setup = train_mod.LossSetup(
        destretch_a=float(recipe["destretch_a"]), destretch_b=float(recipe["destretch_b"]),
        wdl_bootstrap_destretch=bool(recipe["wdl_bootstrap_destretch"]),
        wdl_hard_only=bool(recipe["wdl_hard_only"]),
        wdl_label_smooth=float(recipe["wdl_label_smooth"] or 0.0),
        ranking_loss_weight=float(recipe["ranking_loss_weight"] or 0.0),
        exclude_round5=bool(recipe["exclude_round5"]),
        value_weight=float(eff(recipe["value_weight"], VALUE_WEIGHT)),
        points_weight=float(eff(recipe["points_weight"], POINTS_WEIGHT)),
        ownership_weight=float(eff(recipe["ownership_weight"], 0.0)),
        moon_loss_weight=float(recipe["moon_loss_weight"] or 0.0),
        surprise_alpha=float(recipe["surprise_alpha"] or 0.0),
        surprise_confidence_min=float(recipe["surprise_confidence_min"] or 0.0),
        mse_loss=nn.MSELoss(), margin_log_scale=None, margin_threshold_weight=0.0)

    # 6. Bootstrap-Ziehungen je Liste EINMAL, fuer alle Checkpoints dieselben (gepaart)
    boot_idx = {}
    for lname, names in lists.items():
        rng = np.random.default_rng(args.bootstrap_seed)
        boot_idx[lname] = rng.integers(0, len(names), size=(args.bootstrap_draws, len(names)))

    # 7. Checkpoints
    results, per_file_all, any_fail = [], {}, False
    meta_keys = ("version", "epochs", "is_best_checkpoint", "selected_by", "timestamp",
                 "load_version", "num_val_games", "batch_size", "hidden_size", "input_size",
                 "num_actions", "final_value_val_brier", "final_policy_val_loss")
    for ci, cp in enumerate(ckpt_paths):
        label = f"{ci + 1}/{len(ckpt_paths)} {cp.name}"
        print(f"\n== Checkpoint {label}", flush=True)
        t_c0 = time.time()
        ckpt = torch.load(str(cp), map_location=device)  # wie train.py:1852
        model, enc = build_model_from_checkpoint(ckpt)
        if enc != recipe["encoder"]:
            raise SystemExit(f"ABBRUCH: {cp.name} ist encoder {enc!r}, Rezept {recipe['encoder']!r}")
        model.to(device)
        model.eval()
        arch = model_arch(model, enc, ckpt["model_state"])
        meta = {k: json_safe(ckpt.get(k)) for k in meta_keys if k in ckpt}
        if arch["missing_keys"] or arch["unexpected_keys"]:
            print(f"WARNUNG: {cp.name}: Schluessel-Abweichung Modell/Checkpoint -- fehlend "
                  f"{len(arch['missing_keys'])}, ueberzaehlig {len(arch['unexpected_keys'])}; "
                  f"fehlende Teile tragen Zufalls-Init (strict=False, neural_net.py:2477)",
                  flush=True)
        entry = {"path": rel(cp), "sha256": sha256_of(cp), "meta": meta, "arch": arch,
                 "lists": {}}
        # 7a. train.py-gleich, gesamt und je Klasse
        tp = {}
        for lname in lists:
            t_l = time.time()
            tp[lname] = train_py_validation(train_mod, model, ds, rows_of[lname], enc, device,
                                            loss_setup, BATCH_SIZE)
            print(f"   [{label}] train.py-Validierung {lname}: brier "
                  f"{tp[lname]['epoch_val_brier']}, ploss {tp[lname]['epoch_val_ploss']}, "
                  f"{time.time() - t_l:.1f} s", flush=True)
        # 7b. Datei-Durchgang
        pf = per_file_pass(train_mod, model, ds, ranges, enc, device, recipe, args.batch_size,
                           label)
        per_file_all[str(cp)] = pf
        for lname, names in lists.items():
            pl = pooled(pf, names)
            v = tp[lname]
            m = {"n_files": len(names), **{k: pl[k] for k in ("n_samples", "n_policy_samples",
                                                              "n_brier_samples")},
                 "value_val_brier": v["epoch_val_brier"],
                 "policy_val_loss": v["epoch_val_ploss"],
                 "value_val_loss": v["epoch_val_vloss"],
                 "value_val_brier_pooled": pl["value_val_brier_pooled"],
                 "policy_val_loss_pooled": pl["policy_val_loss_pooled"],
                 "value_val_loss_pooled": pl["value_val_loss_pooled"],
                 "value_val_brier_ci95": ci95(bootstrap_draws(pf, names, boot_idx[lname],
                                                              "brier_sqerr_sum", "brier_n")),
                 "value_val_brier_vw": pl["value_val_brier_vw"],
                 "n_brier_vw": pl["n_brier_vw"],
                 "value_val_brier_vw_ci95": ci95(bootstrap_draws(
                     pf, names, boot_idx[lname], "brier_vw_sqerr_sum", "brier_vw_n")),
                 "policy_val_loss_pooled_ci95": ci95(bootstrap_draws(
                     pf, names, boot_idx[lname], "policy_ce_w_sum", "policy_w_sum")),
                 "train_py_validation": v}
            b_tp, b_pl = v["epoch_val_brier"], pl["value_val_brier_pooled"]
            m["brier_consistency_abs_diff"] = (abs(b_tp - b_pl)
                                               if b_tp is not None and b_pl is not None else None)
            if m["brier_consistency_abs_diff"] is not None and m["brier_consistency_abs_diff"] > 1e-6:
                print(f"WARNUNG: {lname}: pooled Brier {b_pl} != train.py-Brier {b_tp} "
                      f"(Differenz {m['brier_consistency_abs_diff']:.2e}) -- Datei-Durchgang "
                      f"pruefen.", flush=True)
            entry["lists"][lname] = m
        entry["selfcheck"] = self_check(meta, tp["all"], manifest, args.selfcheck_tol, len(ds),
                                        BATCH_SIZE)
        if entry["selfcheck"]["status"] == "FAIL":
            any_fail = True
        print(f"   [{label}] Selbstpruefung: {entry['selfcheck']['status']}"
              f"{'' if entry['selfcheck']['status'] != 'not_applicable' else ' (' + entry['selfcheck']['reason'] + ')'}"
              f", {time.time() - t_c0:.1f} s", flush=True)
        entry["per_file"] = {n: pf[n] for n, _, _ in ranges}
        entry["wall_s"] = round(time.time() - t_c0, 1)
        results.append(entry)
        del model, ckpt
        if device.type == "cuda":
            torch.cuda.empty_cache()

    # 8. Differenzen Referenz minus Checkpoint, gepaart ueber dieselben Datei-Ziehungen
    ref_key = str(ckpt_paths[[p.resolve() for p in ckpt_paths].index(ref_path.resolve())])
    ref_entry = next(e for e in results if e["path"] == rel(ref_key))
    diffs = {}
    for cp, entry in zip(ckpt_paths, results):
        if str(cp) == ref_key:
            continue
        dl = {}
        for lname, names in lists.items():
            pr, pc = per_file_all[ref_key], per_file_all[str(cp)]
            rb, cb = ref_entry["lists"][lname], entry["lists"][lname]

            def sub(a, b):
                return a - b if a is not None and b is not None else None
            db = (bootstrap_draws(pr, names, boot_idx[lname], "brier_sqerr_sum", "brier_n")
                  - bootstrap_draws(pc, names, boot_idx[lname], "brier_sqerr_sum", "brier_n"))
            dbv = (bootstrap_draws(pr, names, boot_idx[lname], "brier_vw_sqerr_sum", "brier_vw_n")
                   - bootstrap_draws(pc, names, boot_idx[lname], "brier_vw_sqerr_sum", "brier_vw_n"))
            dp = (bootstrap_draws(pr, names, boot_idx[lname], "policy_ce_w_sum", "policy_w_sum")
                  - bootstrap_draws(pc, names, boot_idx[lname], "policy_ce_w_sum", "policy_w_sum"))
            dl[lname] = {
                "value_val_brier_diff": sub(rb["value_val_brier"], cb["value_val_brier"]),
                "value_val_brier_diff_ci95": ci95(db),
                "value_val_brier_vw_diff": sub(rb["value_val_brier_vw"], cb["value_val_brier_vw"]),
                "value_val_brier_vw_diff_ci95": ci95(dbv),
                "policy_val_loss_diff": sub(rb["policy_val_loss"], cb["policy_val_loss"]),
                "policy_val_loss_pooled_diff": sub(rb["policy_val_loss_pooled"],
                                                   cb["policy_val_loss_pooled"]),
                "policy_val_loss_pooled_diff_ci95": ci95(dp)}
        diffs[entry["path"]] = dl

    wall = time.time() - t_wall0
    n_file_evals = len(val_files) * len(ckpt_paths)
    result = {
        "tool": "tools/checkpoint_val_eval.py", "prereg": PREREG,
        "created": datetime.now().isoformat(timespec="seconds"),
        **git_state(),
        "args": {k: (rel(v) if k in ("val_list", "out", "train_manifest", "reference") and v
                     else v) for k, v in vars(args).items() if k != "checkpoints"},
        "mosaic_env": {k: v for k, v in sorted(os.environ.items()) if k.startswith("MOSAIC_")},
        "env_report": env_report,
        "recipe": recipe, "recipe_source": recipe_source,
        "val_list": {"path": rel(args.val_list), "sha256": sha256_of(args.val_list),
                     "n_files": len(val_files)},
        "val_cache": {"path": rel(cache_path), "window_key": wk.key, "rows": len(ds),
                      "root_q_frac": root_q_frac},
        "classes": {k: {"n_files": len(v), "prefix": f"{args.class_prefix}{k}_",
                        "list_path": sublists.get(k)} for k, v in classes.items()},
        "unassigned_files": unassigned,
        "file_alignment": align_report,
        "definitions": {
            "value_val_brier": "train._validate_one_epoch epoch_val_brier: Summe ueber Zeilen mit "
                               "wdl_outcome>=0 von ((pred_v+1)/2 - outcome)^2 / Anzahl; ohne "
                               "value_weights (train.py:1046-1052, 1113); Selbstpruefung gegen "
                               "das Manifest laeuft auf dieser Groesse",
            "value_val_brier_vw": "Datei-Durchgang, gepoolt: dieselbe Formel wie value_val_brier, "
                                  "aber nur ueber Zeilen mit wdl_outcome>=0 UND value_weights>0, "
                                  "also ohne Wuerfelphasen-Records (value_weights = 0 bei "
                                  "dice_phase, corpus_dataset.py:423-434); ohne value_weights-Feld "
                                  "gleich value_val_brier; n_brier_vw = Anzahl dieser Zeilen "
                                  "(PREREG_v35_window.md par.11b, Nachtrag)",
            "policy_val_loss": "epoch_val_ploss: Mittel der Batch-Mittel sum(CE*pol_w)/sum(pol_w), "
                               "Batch config.BATCH_SIZE (train.py:926-931, 1078)",
            "value_val_loss": "epoch_val_vloss: Mittel der Batch-Mittel der WDL-BCE gegen "
                              "values_wdl (lambda-gemischt), Gewicht value_weights "
                              "(train.py:934-936, 984-990, 1079)",
            "*_pooled": "Summe/Summe ueber alle Zeilen der Liste (batchunabhaengig)",
            "ci95": "Perzentil-Bootstrap 2.5/97.5, Block = Datei, Ziehung mit Zuruecklegen",
            "diff": "Referenz minus Checkpoint, gepaart ueber dieselben Datei-Ziehungen",
            "n_policy_samples": "Zeilen mit pol_w > 0"},
        "bootstrap": {"draws": args.bootstrap_draws, "seed": args.bootstrap_seed, "unit": "file",
                      "ci": 0.95, "method": "percentile",
                      "rng": "numpy.random.default_rng(seed) je Liste neu"},
        "batch_size_train_py": BATCH_SIZE, "batch_size_per_file_pass": args.batch_size,
        "per_file_fields": PER_FILE_FIELDS,
        "reference": rel(ref_key),
        "checkpoints": results,
        "differences_reference_minus_checkpoint": diffs,
        "selfcheck_overall": ("FAIL" if any_fail else
                              ("PASS" if any(e["selfcheck"]["status"] == "PASS" for e in results)
                               else "not_applicable")),
        "laufzeit": {"wanduhr_s": round(wall, 1),
                     "cpu_s": round(time.process_time() - t_cpu0, 1),
                     "threads": torch.get_num_threads(),
                     "s_je_datei": round(wall / n_file_evals, 3) if n_file_evals else None,
                     "s_je_datei_einheit": "Wanduhr je (Val-Datei x Checkpoint)",
                     "datenaufbau_s": round(data_s, 1), "device": device.type},
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(out.suffix + ".tmp")
    tmp.write_text(json.dumps(json_safe(result), indent=1, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    os.replace(tmp, out)

    print("\n== Ergebnis (value_val_brier [CI95] | policy_val_loss | policy_pooled)", flush=True)
    for e in results:
        print(f"   {e['path']}  Selbstpruefung {e['selfcheck']['status']}")
        for lname, m in e["lists"].items():
            print(f"      {lname:<20} n_files {m['n_files']:>4}  brier {m['value_val_brier']} "
                  f"{m['value_val_brier_ci95']}  ploss {m['policy_val_loss']}  "
                  f"ploss_pooled {m['policy_val_loss_pooled']}")
    print(f"   Artefakt: {rel(out)}  ({wall:.1f} s Wanduhr)", flush=True)
    return 3 if any_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
