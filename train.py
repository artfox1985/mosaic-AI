# train.py
import sys
import os
import argparse
from dataclasses import dataclass

# Windows-Konsolen (cp1252) können die Emoji-Ausgaben sonst nicht kodieren.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import torch
import math
import glob
import time
import json
import re
import subprocess
import random
import itertools
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from pathlib import Path
from datetime import datetime
from torch.utils.data import DataLoader

from freeze_trunk import (OwnershipValLoss, TrunkFreeze, plateau_series_for,
                          validate_freeze_args)


# ── Diagnose-Instrumentierung (2026-07-31, Task #11 Phase 2, fs_2d_s1-
# Absturzuntersuchung) ────────────────────────────────────────────────────
# Kein psutil installiert (Sicherheitsregel: kein pip ins System-Python) --
# direkt ueber die Windows-API (`GetProcessMemoryInfo`, psapi.dll), analog zu
# dem, was `psutil.Process().memory_info()` intern ebenfalls tut. Best-effort:
# auf Nicht-Windows oder bei jedem API-Fehler liefert die Funktion `None`,
# der Aufrufer ueberspringt die Zeile dann einfach -- die Instrumentierung
# darf das eigentliche Training nie gefaehrden.
def _mem_info_gb():
    """(WorkingSetSize, PrivateUsage) in GB, oder None bei Fehler/Nicht-Windows.
    WorkingSetSize ~= RSS (physisch resident), PrivateUsage ~= Commit Charge
    (inkl. reserviertem, noch nicht physisch belegtem virtuellem Speicher --
    die Kennzahl, die bei einem `MemoryError`/Allokationsfehler zuerst an
    ein Limit stoesst)."""
    try:
        import ctypes
        from ctypes import wintypes

        class _PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
                ("PrivateUsage", ctypes.c_size_t),
            ]

        # WICHTIG: `ctypes.windll.kernel32.GetCurrentProcess()` OHNE explizites
        # `restype` truncated das (Pseudo-)Handle stillschweigend auf `c_int`
        # -- `GetProcessMemoryInfo` scheitert dann leise (Rueckgabe 0, keine
        # Python-Exception). Explizite `WinDLL`+`restype`/`argtypes` beheben das.
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        kernel32.GetCurrentProcess.argtypes = []
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        psapi.GetProcessMemoryInfo.argtypes = [
            wintypes.HANDLE, ctypes.POINTER(_PROCESS_MEMORY_COUNTERS_EX), wintypes.DWORD,
        ]

        counters = _PROCESS_MEMORY_COUNTERS_EX()
        counters.cb = ctypes.sizeof(_PROCESS_MEMORY_COUNTERS_EX)
        handle = kernel32.GetCurrentProcess()
        ok = psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb)
        if not ok:
            return None
        return (counters.WorkingSetSize / 1e9, counters.PrivateUsage / 1e9)
    except Exception:
        return None


def _system_mem_info_gb():
    """(TotalPhys, AvailPhys, TotalPageFile/Commit-Limit, AvailPageFile) in GB,
    oder None -- einmalig beim Start geloggt (2026-07-31 Diagnose-Auftrag,
    Arm B/A), damit die Bewertung von Arm A ("laeuft RSS gegen die Commit-
    Grenze?") einen konkreten Nenner hat statt eines geschaetzten Werts."""
    try:
        import ctypes

        class _MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_uint64),
                ("ullAvailPhys", ctypes.c_uint64),
                ("ullTotalPageFile", ctypes.c_uint64),
                ("ullAvailPageFile", ctypes.c_uint64),
                ("ullTotalVirtual", ctypes.c_uint64),
                ("ullAvailVirtual", ctypes.c_uint64),
                ("ullAvailExtendedVirtual", ctypes.c_uint64),
            ]

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.GlobalMemoryStatusEx.restype = ctypes.c_int
        kernel32.GlobalMemoryStatusEx.argtypes = [ctypes.POINTER(_MEMORYSTATUSEX)]
        stat = _MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(_MEMORYSTATUSEX)
        ok = kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        if not ok:
            return None
        return (stat.ullTotalPhys / 1e9, stat.ullAvailPhys / 1e9,
                stat.ullTotalPageFile / 1e9, stat.ullAvailPageFile / 1e9)
    except Exception:
        return None


def plackett_luce_moon_loss(pred_moon, moon_targets):
    """Negative Log-Likelihood der DFS-Referenz-Reihenfolge unter einem
    Plackett-Luce-Modell über die 5 rohen Moon-Head-Scores (sequenzieller
    Softmax über die jeweils noch nicht platzierten, ursprünglich vorhandenen
    Farben — Rust-Pendant: net_mcts.rs::plackett_luce_prob, hier differenzierbar
    fürs Training). `moon_targets`: je Farbe der Rang (0=zuerst…4=zuletzt) oder
    -1 (Farbe nicht in der Restmenge dieses Samples). Gibt (B,) NLL zurück —
    Zeilen ohne jede gültige Farbe (kein Sonnenzug) liefern 0.
    Nutzt -1e9 statt -inf als Masken-Wert: nach der Max-Subtraktion in
    log_softmax bleibt eine vollständig maskierte Zeile ein wohldefiniertes
    Gleichverteilungs-Softmax (kein NaN), unabhängig davon ob ihr Beitrag
    später über `has_rank_t` verworfen wird."""
    present = moon_targets >= 0                      # (B,5) bool
    placed = torch.zeros_like(present)
    total_nll = torch.zeros(moon_targets.shape[0], device=moon_targets.device)
    for t in range(5):
        is_rank_t = present & (moon_targets == t)     # (B,5): genau 1 True je Zeile, falls Rang t existiert
        has_rank_t = is_rank_t.any(dim=1)
        avail = present & (~placed)
        masked_logits = pred_moon.masked_fill(~avail, -1e9)
        log_probs = F.log_softmax(masked_logits, dim=1)
        step_nll = -(log_probs * is_rank_t.float()).sum(dim=1)
        total_nll = total_nll + torch.where(has_rank_t, step_nll, torch.zeros_like(step_nll))
        placed = placed | is_rank_t
    return total_nll


# Unsere dynamischen Pfade aus der Config laden
from config import (MODELS_DIR, DATA_DIR, NUM_ACTIONS, BATCH_SIZE, LEARNING_RATE, VALUE_WEIGHT,
                    POINTS_WEIGHT, OWNERSHIP_WEIGHT, CONJUNCTION_TARGETS,
                    POINTS_DIST_BINS, POINTS_DIST_SIGMA)
from head_warmstart import apply_head_warmstart

# Netz/Dataset (PyTorch) liegen jetzt neben der Rust-Engine in engine/py/.
sys.path.insert(0, str(Path(__file__).resolve().parent / "engine" / "py"))
from train_manifest import (policy_carrier_report, corpus_composition,
                            write_train_manifest, _SELFPLAY_FILENAME_RE)
from corpus_dataset import MosaicDataset
from neural_net import (
    MosaicNet, Mosaic2DNet, TD_LAMBDA, POLICY_TARGET_SHARPEN_EXPONENT,
    VALUE_SCHEMA_VERSION, encoder_from_state_dict, VALUE_HEAD_VARIANTS,
    value_head_variant_from_state, unpack_planes_batch, unpack_masks_batch, RANKING_TOPK,
)


# ── Lauf-Manifest + Korpus-Log (#64 Teil 2, Phase 2b, 2026-07-22) ───────────
# Additiv neben dem bestehenden `--train-file-limit`-Flag (Daten-Skalierungs-
# Ablation, Task #69, unveraendert -- siehe dessen Kommentar unten). Ein
# Trainingslauf soll rueckwirkend rekonstruierbar sein: welche CLI-Args,
# welcher Rust/Python-Konstanten-Stand, welche Korpus-Zusammensetzung gingen
# ein. Nutzer-Wunsch: die Korpus-Zusammensetzung wird NUR geloggt (Konsole +
# Manifest) -- das Replay-Fenster selbst stellt der Nutzer weiterhin manuell
# zusammen (kein automatisches Filtern hier). Alles best-effort (git/
# engine_config_json koennen fehlen) -- ein Manifest-Fehler darf das
# eigentliche Training nie verhindern.



def points_dist_loss(logits, targets, model, rw2, denom):
    """Task #12: Kreuzentropie des Verteilungs-Punktekopfs gegen ein
    HL-Gauss-geglaettetes Ziel.

    `targets` ist der skalare tanh-gestauchte Punktedifferenz-Wert in [-1, 1].
    Statt ihn hart auf ein Bin zu legen (Two-Hot), wird eine Normalverteilung
    um ihn gelegt und ueber die Bin-KANTEN integriert (Differenz der Gauss-CDF)
    -- laut Farebrother et al. 2024 ("Stop Regressing") durchweg besser als
    Two-Hot, weil benachbarte Bins Gradient bekommen und das Ziel damit
    glatt in der Zielgroesse ist.

    Ziele ausserhalb von [-1, 1] koennen nicht auftreten (tanh), die
    Renormierung faengt aber die an den Raendern abgeschnittene
    Wahrscheinlichkeitsmasse ab.
    """
    edges = model.points_bin_edges.to(logits.device)          # (B+1,)
    sigma = POINTS_DIST_SIGMA * (edges[1] - edges[0])
    y = targets.view(-1, 1)                                    # (N, 1)
    # Gauss-CDF an jeder Bin-Kante: Phi(z) = 0.5*(1+erf(z/sqrt(2)))
    cdf = 0.5 * (1.0 + torch.erf((edges.view(1, -1) - y) / (sigma * math.sqrt(2.0))))
    probs = cdf[:, 1:] - cdf[:, :-1]                            # (N, B)
    probs = probs / probs.sum(dim=1, keepdim=True).clamp(min=1e-8)
    ce = -(probs * F.log_softmax(logits, dim=-1)).sum(dim=-1, keepdim=True)
    if rw2 is None:
        return ce.mean()
    return (ce * rw2).sum() / denom


def _unpack_optional_outputs(model, out_tuple):
    """Task #28 (PREREG_task28_aggression.md) / Task #34: `model(...)` haengt
    bis zu drei OPTIONALE Ausgaben hinter den festen 5 (policy/value/moon/
    points/ownership) an, IN DIESER REIHENFOLGE -- `points_dist`-Logits
    (Task #12, `points_dist_bins>0`), `value_wdl_logits` (Task #34,
    `value_head_variant=='wdl'`), und/oder `opp_points` (additiver Kopf,
    ZULETZT, Task #28). Deren Reihenfolge/Anwesenheit haengt vom MODELL ab,
    nicht von der Tupel-LAENGE allein (mehrdeutig sonst, z.B. Laenge 6) --
    daher Introspektion ueber die Modell-Attribute statt reinem Index-Raten.
    Gibt `(pred_points_logits, pred_value_wdl_logits, pred_opp_points)`
    zurueck, je `None` wenn nicht vorhanden."""
    idx = 5
    pred_points_logits = None
    if getattr(model, "points_dist_bins", 0) > 0:
        pred_points_logits = out_tuple[idx]
        idx += 1
    pred_value_wdl_logits = None
    if getattr(model, "value_head_variant", "tanh") == "wdl":
        pred_value_wdl_logits = out_tuple[idx]
        idx += 1
    pred_opp_points = None
    if getattr(model, "has_opp_points_head", False):
        pred_opp_points = out_tuple[idx]
        idx += 1
    # Schema 18: endgame_head haengt ZULETZT (hinter opp_points).
    pred_endgame = None
    if getattr(model, "has_endgame_head", False):
        pred_endgame = out_tuple[idx]
        idx += 1
    return pred_points_logits, pred_value_wdl_logits, pred_opp_points, pred_endgame


# ── Task #35b, "Ranking-Loss auf Geschwister-Q" (Research-Report Idee 7.1)
# ──────────────────────────────────────────────────────────────────────────
# Paarweiser RankNet-Stil-Loss auf den Policy-LOGITS: fuer je zwei
# Geschwister-Kandidaten (RANKING_CACHE_FIELDS, siehe neural_net.py) mit
# klar unterschiedlichem Suchwert Q soll der Kandidat mit dem GROESSEREN Q
# auch den GROESSEREN Policy-Logit bekommen -- ein zusaetzliches Signal
# neben der bestehenden Kreuzentropie auf der Besuchs-Softmax (die nur die
# GESAMTVERTEILUNG trifft, nicht explizit die paarweise REIHENFOLGE der
# Kandidaten trainiert). Additiv, `--ranking-loss-weight` (Default 0.0 =
# AUS) multipliziert das Gewicht in den Gesamt-Loss -- bei 0.0 wird der
# Term unten in `train()` komplett uebersprungen (kein Gradient, keine
# zusaetzliche Rechenzeit, byte-identisches Bestandsverhalten).
#
# MARGIN: nur Paare mit |q_i - q_j| > RANKING_MARGIN fliessen ein (Rauschen
# zwischen nahezu gleichwertigen Kandidaten soll kein hartes Rang-Signal
# erzeugen, siehe Task-Vorgabe "klare Q-Differenz"). Bewusst eine
# Code-Konstante statt ein weiteres CLI-Flag -- Loss-Design soll einfach
# bleiben (STATUS.md-Vorgabe); kann bei Bedarf spaeter zum Flag werden.
RANKING_MARGIN = 0.02

# Alle ungeordneten Paare aus den RANKING_TOPK Cache-Slots, EINMAL
# vorberechnet (K=8 -> 28 Paare) -- vektorisiert per Gather/Index statt
# einer Python-Schleife ueber Paare je Sample.
_RANKING_PAIR_IDX = list(itertools.combinations(range(RANKING_TOPK), 2))
_RANKING_PAIR_I = [i for i, _ in _RANKING_PAIR_IDX]
_RANKING_PAIR_J = [j for _, j in _RANKING_PAIR_IDX]

# Ab welchem --epochs die Cosine-Warnung greift (siehe Scheduler-Block in
# `train()`). Herleitung, nachgerechnet: CosineAnnealingLR mit eta_min=0 hat
# den Faktor (1 + cos(pi * t / T_max)) / 2.
#   T_max = 25, Stopp bei t = 15  ->  0,345  (34,5 % der Start-LR)
#   T_max = 100, Stopp bei t = 15 ->  0,946  (94,6 % der Start-LR)
# Bei T_max = 25 ist ein frueher Stopp also unkritisch (die LR ist bereits auf
# rund ein Drittel gefallen, der Sinn des Annealings ist erfuellt); bei einem
# grossen --epochs regelt der Scheduler faktisch nicht ab. 25 ist damit die
# Grenze, ab der die Kombination "cosine + Early Stopping + kein --lr-t-max"
# eine Meldung verdient. Die Zahl ist eine Auslegungsschwelle fuer eine
# WARNUNG, kein gemessener Optimalwert -- sie aendert kein Verhalten.
COSINE_TMAX_WARN_EPOCHS = 25


def _pairwise_ranking_loss(policy_logits, ranking_action_ids, ranking_child_q, ranking_mask):
    """Task #35b: paarweiser Ranking-Loss + deskriptive Ranking-Accuracy.

    `policy_logits`: (B, NUM_ACTIONS) rohe Policy-Logits (VOR Masking/
    Softmax -- die gespeicherten Geschwister-Aktionen sind per Konstruktion
    immer legale, tatsaechlich im Root-Suchbaum gesehene Kandidaten, ein
    zusaetzliches illegal-Masking ist hier nicht noetig).
    `ranking_action_ids`: (B, RANKING_TOPK) int, -1 = nicht belegter Slot.
    `ranking_child_q`: (B, RANKING_TOPK) float, [0,1]-Skala (root_child_q roh,
    siehe RANKING_CACHE_FIELDS-Kommentar in neural_net.py -- kein Remap
    noetig, nur Differenzen/Vorzeichen gehen ein).
    `ranking_mask`: (B,) float, 1.0 = Sample nutzbar (deckt bereits
    <2-Geschwister UND pol_w==0 ab, siehe Cache-Bau).

    Fuer jedes Paar (i,j) aus den RANKING_TOPK Slots mit BEIDEN Slots belegt,
    Sample-Maske=1 UND |q_i-q_j|>RANKING_MARGIN: RankNet-Logistik-Loss
    `softplus(-sign(q_i-q_j) * (logit_i-logit_j))` -- 0 (im Limit), wenn der
    Logit mit dem groesseren Q auch tatsaechlich groesser ist, waechst sonst.

    Rueckgabe `(loss, accuracy_or_None, n_pairs)`: `loss` ist ein
    Skalar-Tensor (0.0 bei keinem einzigen gueltigen Paar im Batch, sicher
    endlich/differenzierbar). `accuracy` ist der Anteil der gueltigen Paare,
    bei denen das Logit-Vorzeichen zum Q-Vorzeichen passt (rein deskriptiv,
    STATUS.md-Vorgabe "Val-Metrik: paarweise Ranking-Accuracy") -- `None`
    bei keinem gueltigen Paar im Batch. `n_pairs` = Anzahl gueltiger Paare
    (fuer Batch-uebergreifende Mittelung im Aufrufer)."""
    device = policy_logits.device
    ids = ranking_action_ids.long()
    valid_slot = ids >= 0                                   # (B,K) bool
    ids_clamped = ids.clamp(min=0)
    logits_k = policy_logits.gather(1, ids_clamped)          # (B,K)
    q_k = ranking_child_q.float()                            # (B,K)

    idx_i = torch.tensor(_RANKING_PAIR_I, device=device, dtype=torch.long)
    idx_j = torch.tensor(_RANKING_PAIR_J, device=device, dtype=torch.long)
    logit_i = logits_k[:, idx_i]                              # (B,P) P=28
    logit_j = logits_k[:, idx_j]
    q_i = q_k[:, idx_i]
    q_j = q_k[:, idx_j]
    valid_pair = (valid_slot[:, idx_i] & valid_slot[:, idx_j]).float()

    dq = q_i - q_j
    margin_ok = (dq.abs() > RANKING_MARGIN).float()
    sample_ok = ranking_mask.view(-1, 1).float()
    w = valid_pair * margin_ok * sample_ok                   # (B,P)

    sign = torch.sign(dq)
    logit_diff = logit_i - logit_j
    per_pair_loss = F.softplus(-sign * logit_diff)
    n_pairs = w.sum().item()
    loss = (per_pair_loss * w).sum() / w.sum().clamp(min=1e-6)

    accuracy = None
    if n_pairs > 0:
        correct = ((sign * logit_diff) > 0).float()
        accuracy = (correct * w).sum().item() / n_pairs
    return loss, accuracy, n_pairs


def _destretch_wdl_target(targets_v_wdl, wdl_outcome, a, b):
    """Erosions-Arm B (`--wdl-bootstrap-destretch`): entstaucht den
    Bootstrap-Anteil des `values_wdl`-Ziels OHNE Cache-Neubau.

    Hintergrund (Audit Befund 1): `bootstrap_value` stammt aus Suchen der
    Generator-Netze (tanh-Kopf) -- eine per `(v+1)/2` als Wahrscheinlichkeit
    etikettierte, gestauchte Punkte-Marge (gemessener Platt-Fit des
    Champions: B~1,93). Der Cache speichert nur das fertige Blend
    `t = TD_LAMBDA*bv + (1-TD_LAMBDA)*y`, aber `y` (`wdl_outcome`) liegt roh
    daneben -- `bv` ist daher algebraisch exakt rekonstruierbar
    (`bv = (t - (1-TD_LAMBDA)*y) / TD_LAMBDA`; der [0,1]-Clamp beim Cache-Bau
    kann nie gebunden haben, ein Konvex-Blend zweier [0,1]-Werte bleibt in
    [0,1]). Dann Platt-Streckung `sigmoid(a + b*logit(bv))` und Neu-Blend.
    Wo `y == -1` (kein echter Ausgang) bleibt das Ziel unveraendert.
    Grenzfall bv==y (Record ohne bootstrap_value): logit sattigt, sigmoid
    reproduziert ~y, Ziel bleibt effektiv unveraendert -- korrekt."""
    valid = wdl_outcome >= 0.0
    y = wdl_outcome.clamp(min=0.0)
    bv = ((targets_v_wdl - (1.0 - TD_LAMBDA) * y) / TD_LAMBDA).clamp(1e-6, 1.0 - 1e-6)
    logit_bv = torch.log(bv / (1.0 - bv))
    bv_corr = torch.sigmoid(a + b * logit_bv)
    t_corr = TD_LAMBDA * bv_corr + (1.0 - TD_LAMBDA) * y
    return torch.where(valid, t_corr, targets_v_wdl)



@dataclass(frozen=True)
class LossSetup:
    """Wie der Verlust gerechnet wird -- die Knoepfe, die BEIDE Epochen-
    Durchgaenge brauchen.

    Ein Buendel, kein Sammelbeutel: jedes Feld beantwortet dieselbe Frage
    ("wie wird aus Netzausgabe und Ziel eine Zahl?"). Ohne dieses Buendel
    haette `_train_one_epoch` 21 und `_validate_one_epoch` 20 Parameter --
    eine Naht, die so breit ist, ist keine.

    `frozen`, weil sich innerhalb eines Laufs keiner dieser Werte aendert;
    ein versehentliches Zuweisen im Durchgang faellt damit sofort auf.
    """
    destretch_a: float
    destretch_b: float
    wdl_bootstrap_destretch: bool
    wdl_hard_only: bool
    wdl_label_smooth: float
    ranking_loss_weight: float
    exclude_round5: bool
    value_weight: float
    points_weight: float
    ownership_weight: float
    mse_loss: object


def _train_one_epoch(model, dataloader, dataset, optimizer, device, encoder, n_batches, epoch, mem_log_every, ftz, loss_setup) -> dict:
    """EINE Trainingsepoche. Herausgeloest aus `train()` (2026-08-27).

    Reine Extraktion: der Rumpf ist Zeile fuer Zeile der bisherige, nur
    ausgerueckt und mit `loss.` vor den Verlust-Knoepfen. Keine
    Verhaltensaenderung -- belegt gegen den Referenzlauf
    (`--train-file-limit 6 --epochs 2 --seed 4242`), dessen `epoch_history`
    im Manifest bitgleich bleiben muss.
    """
    t_loss, t_ploss, t_vloss, t_pointsloss = 0, 0, 0, 0
    t_opp_pointsloss = 0  # Task #28: nur != 0 relevant, wenn opp_points_head aktiv
    t_endgameloss = 0  # Schema 18: nur != 0 relevant, wenn endgame_head aktiv
    t_rankingloss = 0  # Task #35b: nur != 0 relevant, wenn ranking_loss_weight>0

    for _batch_idx, _batch in enumerate(dataloader):
        if mem_log_every and _batch_idx % mem_log_every == 0:
            _mi = _mem_info_gb()
            if _mi is not None:
                print(f"  [mem] epoch={epoch+1} batch={_batch_idx}/{n_batches} "
                      f"rss={_mi[0]:.2f}GB commit={_mi[1]:.2f}GB", flush=True)
        # Task #11 Phase 2 / Task #28 / Task #34: MosaicDataset liefert bei
        # encoder="2d" ein 14-Tupel (planes VORAN), bei encoder="flat"
        # (Standard) das 13-Tupel -- die letzten 4 Elemente
        # (opp_points_forecast, opp_points_mask, values_wdl, wdl_outcome)
        # sind additiv ANS ENDE angehaengt (siehe
        # `corpus_dataset.py::MosaicDataset.__getitem__`), unabhaengig davon,
        # ob `--opp-points-head`/`--value-head wdl` aktiv sind (die Cache-
        # Felder existieren immer, werden nur ggf. nicht im Loss genutzt).
        if encoder == "2d":
            (planes, states, targets_p, targets_v, masks, moon_targets, pol_w, targets_points,
             s_rounds, s_own, targets_opp_points, s_opp_mask,
             targets_v_wdl, s_wdl_outcome, targets_endgame, s_endgame_mask,
             s_rank_ids, s_rank_q, s_rank_mask) = _batch
            # RAM-Optimierung v21 (Bitpacking): liegt der Cache gepackt
            # vor (`dataset.bitpacked`, Standard seit diesem Feature),
            # kommt `planes` als [B,342]-Bytes statt [B,76,6,6] aus dem
            # DataLoader -- EINMAL pro Batch entpackt, NOCH VOR dem
            # Device-Move (Micro-Benchmark in neural_net.py zeigt diese
            # Reihenfolge als schnellsten Pfad, siehe
            # `unpack_planes_batch`-Kommentar). Alt-Cache/
            # MOSAIC_CACHE_NOPACK=1 -> `bitpacked=False`, `planes` ist
            # bereits [B,76,6,6] wie bisher, Aufruf entfaellt.
            if dataset.bitpacked:
                planes = unpack_planes_batch(planes)
            # RAM-Optimierung v20: Cache liefert kompakte Typen (planes
            # uint8, states/policies fp16, masks uint8) -- Cast auf
            # float32 erst NACH dem Device-Move (billig, spart Transfer).
            # `.float()` ist fuer Alt-Caches in float32 ein No-op.
            planes = planes.to(device).float()
        else:
            (states, targets_p, targets_v, masks, moon_targets, pol_w, targets_points,
             s_rounds, s_own, targets_opp_points, s_opp_mask,
             targets_v_wdl, s_wdl_outcome, targets_endgame, s_endgame_mask,
             s_rank_ids, s_rank_q, s_rank_mask) = _batch
        # RAM-Optimierung v21 (Bitpacking): masks-Entpacken analog zu
        # planes oben, UNABHAENGIG vom Encoder (masks gehoeren zum
        # Basis-Tupel, siehe MosaicDataset.__getitem__).
        if dataset.bitpacked:
            masks = unpack_masks_batch(masks)
        states    = states.to(device).float()
        targets_p = targets_p.to(device).float()
        targets_v = targets_v.to(device)
        targets_points = targets_points.to(device)
        targets_opp_points = targets_opp_points.to(device)
        s_opp_mask = s_opp_mask.to(device)
        targets_v_wdl = targets_v_wdl.to(device)
        s_wdl_outcome = s_wdl_outcome.to(device)
        targets_endgame = targets_endgame.to(device)
        s_endgame_mask = s_endgame_mask.to(device)
        masks     = masks.to(device).float()
        pol_w     = pol_w.to(device)
        # Task #35b: NUR bei aktivem Gewicht auf Device verschoben --
        # bei ranking_loss_weight==0.0 (Default) bleibt der Batch-Pfad
        # sonst byte-identisch zum Bestand (kein zusaetzlicher Transfer).
        if loss_setup.ranking_loss_weight > 0.0:
            s_rank_ids  = s_rank_ids.to(device)
            s_rank_q    = s_rank_q.to(device)
            s_rank_mask = s_rank_mask.to(device)

        optimizer.zero_grad()
        _out = model(planes, states) if encoder == "2d" else model(states)
        pred_p, pred_v, pred_moon, pred_points, pred_own = _out[:5]
        (pred_points_logits, pred_value_wdl_logits, pred_opp_points,
         pred_endgame) = _unpack_optional_outputs(model, _out)

        # Policy Loss mit Masking:
        # Illegale Aktionen aus pred_p rausrechnen, dann renormalisieren
        masked_logits = pred_p + (masks - 1) * 1e9   # illegale Aktionen auf -inf
        log_probs = F.log_softmax(masked_logits, dim=1)

        per_sample_ce = -torch.sum(targets_p * log_probs, dim=1)   # (B,)
        # Policy-Loss NUR auf echten Drafting-Schritten (pol_w=1); Tiling/Start-
        # One-Hot-Steps (pol_w=0) macht der DFS-Solver — sie würden sonst den
        # Policy-Head mit Tiling-Aktionen fluten und die Drafting-Priors ruinieren.
        # Task #15 B (2026-07-28): Runde-5-Samples optional komplett aus
        # dem Loss nehmen. Das Netz wird in Runde 5 NIE konsultiert
        # (net_mcts.rs:2265 bypassed den Suchpfad zu round5::choose_action,
        # der R4-Bootstrap nutzt round5::exact_round5_outcome) -- ~17% der
        # Value- und ~15% der Policy-Samples gehen dort in Entscheidungen,
        # die ein exakter Alpha-Beta-Solver trifft. Praezedenzfall: pol_w=0
        # fuer Tiling-Schritte, weil das der DFS-Solver macht.
        rw = (s_rounds.to(device) != 5).float() if loss_setup.exclude_round5 else None

        w = pol_w if rw is None else pol_w * rw
        p_loss = (per_sample_ce * w).sum() / w.sum().clamp(min=1e-6)

        # Moon-Order Loss direkt zu Policy-Loss — kein extra Hyperparameter.
        # Plackett-Luce-NLL statt MSE-auf-Rängen: der moon_order_head liefert
        # jetzt echte Präferenz-SCORES, die net_mcts.rs zur Suchzeit direkt als
        # P(Order)-Verteilung nutzt (statt einer bloßen Rang-Regression).
        moon_targets = moon_targets.to(device)
        # BUGFIX: sun_mask prüfte zuvor nur Spalte 0 (blau) auf >=0 — das
        # schloss gültige Sonnenzug-Samples aus, deren Restfarben blau nicht
        # enthielten (z.B. remaining=[gelb,rot]), und verzerrte den Loss
        # systematisch zugunsten blau-haltiger Samples. Jetzt: irgendeine Spalte.
        sun_mask = (moon_targets >= 0).any(dim=1)
        if sun_mask.any():
            moon_nll = plackett_luce_moon_loss(pred_moon, moon_targets)
            p_loss = p_loss + moon_nll[sun_mask].mean()

        # Value-/Punkte-Aux-Losses: reines Trainings-Zusatzsignal fuer den
        # Trunk (Suche/Self-Play nutzt weiterhin nur die Policy, siehe
        # evaluations/stage2_investigation.md) -- klein gewichtet, damit
        # sie den Policy-Loss nicht dominieren.
        rw2 = rw.view(-1, 1) if rw is not None else None
        denom = rw2.sum().clamp(min=1e-6) if rw2 is not None else None
        # Task #34: bei aktivem WDL-Kopf ist der Value-Verlust eine
        # Kreuzentropie mit WEICHEN Labels statt MSE (siehe
        # VALUE_SCHEMA_VERSION=16-Kommentar in neural_net.py). Ein
        # 2-Logit-Softmax reduziert algebraisch auf BCEWithLogits der
        # Logit-DIFFERENZ gegen die Ziel-Wahrscheinlichkeit `targets_v_wdl`
        # -- numerisch identisch zur kategorialen Kreuzentropie
        # -log(softmax)[y], aber stabiler (kein manuelles log(softmax)).
        # ACHTUNG (STATUS.md "val_combined"-Falle): diese Loss-GROESSE hat
        # eine ANDERE Einheit als die MSE des tanh-Arms -- `val_combined`
        # (current_metric weiter unten) ist damit NUR arm-INTERN fuer die
        # Checkpoint-Auswahl vergleichbar, NICHT zwischen tanh- und
        # wdl-Laeufen (siehe Kommentar an der current_metric-Stelle).
        if pred_value_wdl_logits is not None:
            logit_diff = pred_value_wdl_logits[:, 1] - pred_value_wdl_logits[:, 0]
            # Task #34 Audit 2026-08-05 (`--wdl-hard-only`): `values_wdl`
            # ist TD-geblendet mit `bootstrap_value` -- und der stammt aus
            # Self-Play-Suchen der GENERATOR-Netze (v16-v18, tanh-Kopf,
            # Platt-B~1,9): eine gestauchte Punkte-Marge, als
            # Wahrscheinlichkeit gelesen. Die Haelfte (TD_LAMBDA=0,5) des
            # "kohaerenten" WDL-Ziels traegt also die ALTE Semantik weiter.
            # Dieser Schalter trainiert stattdessen auf dem ROHEN Ausgang
            # `wdl_outcome` (-1 = unbekannt -> maskiert) -- das einzige auf
            # Bestandskorpora saubere Wahrscheinlichkeits-Ziel, bis eine
            # Kampagne mit WDL-Generator neue Bootstrap-Werte liefert.
            if loss_setup.wdl_hard_only:
                v_wdl_target = s_wdl_outcome.view(-1)
                wdl_mask = (v_wdl_target >= 0.0).float()
                # Erosions-Arm A (`--wdl-label-smooth`): weiche Labels
                # 1-eps/2 bzw. eps/2 statt 1/0 -- testet die
                # Memorisierungs-Hypothese (Trainings-Loss 0,60->0,39 bei
                # steigendem Val-Brier). Brier unten bleibt gegen den
                # ROHEN Ausgang gerechnet, unveraendert vergleichbar.
                hard_t = v_wdl_target.clamp(min=0.0)
                if loss_setup.wdl_label_smooth > 0.0:
                    hard_t = hard_t * (1.0 - loss_setup.wdl_label_smooth) + 0.5 * loss_setup.wdl_label_smooth
                v_bce = F.binary_cross_entropy_with_logits(
                    logit_diff, hard_t, reduction="none") * wdl_mask
                if rw is None:
                    v_loss = v_bce.sum() / wdl_mask.sum().clamp(min=1.0)
                else:
                    # Audit-F3: Nenner muss die MASKIERTE Gewichtssumme
                    # sein -- `denom` (=rw2.sum()) zaehlt auch
                    # wdl_mask==0-Samples und verduennte den Loss.
                    v_loss = ((v_bce.view(-1, 1) * rw2).sum()
                              / (wdl_mask.view(-1, 1) * rw2).sum().clamp(min=1e-6))
            else:
                v_wdl_target = targets_v_wdl.view(-1)
                if loss_setup.wdl_bootstrap_destretch:
                    v_wdl_target = _destretch_wdl_target(
                        v_wdl_target, s_wdl_outcome.view(-1),
                        loss_setup.destretch_a, loss_setup.destretch_b)
                if rw is None:
                    v_loss = F.binary_cross_entropy_with_logits(logit_diff, v_wdl_target)
                else:
                    v_bce = F.binary_cross_entropy_with_logits(logit_diff, v_wdl_target, reduction="none")
                    v_loss = (v_bce.view(-1, 1) * rw2).sum() / denom
        elif rw is None:
            v_loss = loss_setup.mse_loss(pred_v, targets_v)
        else:
            v_loss = (((pred_v - targets_v) ** 2) * rw2).sum() / denom

        # Task #12: bei aktivem Verteilungs-Kopf ist der Punkte-Verlust eine
        # KREUZENTROPIE gegen ein HL-Gauss-geglaettetes Ziel statt MSE auf
        # dem Erwartungswert -- reicheres Gradientensignal, robuster gegen
        # Ausreisser (Farebrother et al. 2024). Der ausgegebene Skalar
        # bleibt der Erwartungswert, die Schnittstelle also unveraendert.
        if pred_points_logits is not None:
            points_loss = points_dist_loss(
                pred_points_logits, targets_points, model, rw2, denom)
        elif rw is None:
            points_loss = loss_setup.mse_loss(pred_points, targets_points)
        else:
            points_loss = (((pred_points - targets_points) ** 2) * rw2).sum() / denom

        # Ownership-Loss (Task #9): dichtes Hilfsziel, 72 Binaerlabels je
        # Position statt eines Skalars. -1 = unbekannt (unvollstaendiges
        # Spiel) und wird maskiert. Bei Gewicht 0.0 wird der Term komplett
        # uebersprungen -- kein Gradient, Bestandsverhalten unveraendert.
        own_loss = torch.zeros((), device=device)
        if loss_setup.ownership_weight > 0.0:
            own_t = s_own.to(device).float()
            own_m = (own_t >= 0).float()
            if own_m.sum() > 0:
                own_bce = F.binary_cross_entropy_with_logits(
                    pred_own, own_t.clamp(min=0.0), reduction="none")
                own_loss = (own_bce * own_m).sum() / own_m.sum()

        # Task #28 (PREREG_task28_aggression.md "Minimal-invasiver
        # Zuschnitt" Punkt 2): Opp-Punkte-Aux-Loss, NUR wenn der additive
        # Kopf aktiv ist. MSE, Gewicht = POINTS_WEIGHT (symmetrisch zum
        # eigenen Punkte-Kopf, kein neues Tuning), maskiert mit
        # `s_opp_mask` (0 bei unvollstaendigen Partien ODER einem Alt-
        # Cache ohne das Feld -- kein erfundener Zielwert geht in den
        # Loss ein) UND zusaetzlich mit `rw` (--exclude-round5), falls
        # aktiv -- gleiches Kombinationsmuster wie beim Punkte-Loss oben.
        # Geht NICHT in `val_combined`/die Checkpoint-Auswahl ein (siehe
        # Kommentar an der Auswahlstelle unten) -- Bestandsmetrik bleibt
        # unveraendert vergleichbar mit Alt-Laeufen.
        opp_loss = torch.zeros((), device=device)
        if pred_opp_points is not None:
            opp_w = s_opp_mask.view(-1, 1) if rw2 is None else s_opp_mask.view(-1, 1) * rw2
            opp_denom = opp_w.sum().clamp(min=1e-6)
            opp_loss = (((pred_opp_points - targets_opp_points) ** 2) * opp_w).sum() / opp_denom

        # Schema 18 (PREREG_plate_intervention.md): Endgame-Aux-Loss,
        # NUR bei aktivem Kopf. MSE gegen den exakten R5-Wurzelwert
        # (Cache [0,1] -> Remap auf die Tanh-Skala [-1,1]), maskiert mit
        # `s_endgame_mask` (nur R5-Drafting mit root_q). Gewicht =
        # POINTS_WEIGHT (symmetrisch, kein neues Tuning, Muster opp_loss).
        # KEIN rw2: --exclude-round5 wuerde die Zone komplett leeren --
        # der Kopf ist ausdruecklich ein R5-Zonen-Signal. Geht NICHT in
        # val_combined/Brier-Checkpoint-Auswahl ein.
        endgame_loss = torch.zeros((), device=device)
        if pred_endgame is not None:
            eg_w = s_endgame_mask.view(-1, 1)
            eg_denom = eg_w.sum().clamp(min=1e-6)
            eg_target = targets_endgame * 2.0 - 1.0
            endgame_loss = (((pred_endgame - eg_target) ** 2) * eg_w).sum() / eg_denom

        # Task #35b ("Ranking-Loss auf Geschwister-Q"): NUR berechnet,
        # wenn `ranking_loss_weight>0` -- bei 0.0 (Default) komplett
        # uebersprungen, kein zusaetzlicher Gradient/keine zusaetzliche
        # Rechenzeit, byte-identisches Bestandsverhalten. Kein eigener
        # Modell-Kopf (nutzt die bestehenden Policy-Logits `pred_p`
        # VOR dem Illegal-Masking, siehe `_pairwise_ranking_loss`-
        # Docstring). Geht NICHT in val_combined/Brier-Checkpoint-
        # Auswahl ein (Muster opp_loss/endgame_loss oben).
        ranking_loss = torch.zeros((), device=device)
        if loss_setup.ranking_loss_weight > 0.0:
            ranking_loss, _rk_acc, _rk_n = _pairwise_ranking_loss(
                pred_p, s_rank_ids, s_rank_q, s_rank_mask)

        loss = (p_loss + loss_setup.value_weight * v_loss
                + loss_setup.points_weight * points_loss
                + loss_setup.ownership_weight * own_loss
                + loss_setup.points_weight * opp_loss
                + loss_setup.points_weight * endgame_loss
                + loss_setup.ranking_loss_weight * ranking_loss)
        if ftz.backward_ok(loss):   # nur im Freeze-Modus je restriktiv, s. Docstring
            loss.backward()
            optimizer.step()

        t_loss       += loss.item()
        t_ploss      += p_loss.item()
        t_vloss      += v_loss.item()
        t_pointsloss += points_loss.item()
        if pred_opp_points is not None:
            t_opp_pointsloss += opp_loss.item()
        if pred_endgame is not None:
            t_endgameloss += endgame_loss.item()
        if loss_setup.ranking_loss_weight > 0.0:
            t_rankingloss += ranking_loss.item()

    return {"t_loss": t_loss, "t_ploss": t_ploss, "t_vloss": t_vloss, "t_pointsloss": t_pointsloss, "t_opp_pointsloss": t_opp_pointsloss, "t_endgameloss": t_endgameloss, "t_rankingloss": t_rankingloss}


def _validate_one_epoch(model, val_dataloader, val_dataset, device, encoder, loss_setup) -> dict:
    """EINE Validierungsepoche. Herausgeloest aus `train()` (2026-08-27).

    Gibt die elf Kennzahlen zurueck, die `train()` danach in die Historien
    schreibt. `own_meter` bleibt innen -- es wird ausserhalb nicht gelesen.
    """
    epoch_val_ploss = None
    epoch_val_vloss = None
    epoch_val_pointsloss = None
    epoch_val_value_r2 = None
    epoch_val_points_r2 = None
    epoch_val_opp_pointsloss = None
    epoch_val_opp_points_r2 = None
    epoch_val_endgame_mse = None
    epoch_val_ranking_acc = None  # Task #35b: rein deskriptiv, siehe val_ranking_acc_history
    epoch_val_brier = None  # Task #34: arm-uebergreifend vergleichbare Kalibrierungskennzahl
    epoch_val_ownloss = None  # PREREG_frozen_trunk_head.md, s. val_ownloss_history
    own_meter = OwnershipValLoss(loss_setup.ownership_weight > 0.0)
    if val_dataloader is not None:
        model.eval()
        val_ploss_sum, val_vloss_sum, val_pointsloss_sum, val_batches = 0.0, 0.0, 0.0, 0
        val_opp_pointsloss_sum, val_opp_batches = 0.0, 0  # Task #28, nur relevant wenn opp_points_head aktiv
        val_endgame_sqerr_sum, val_endgame_n = 0.0, 0.0  # Schema 18, nur relevant wenn endgame_head aktiv
        val_rank_correct_sum, val_rank_n = 0.0, 0.0  # Task #35b, nur relevant wenn ranking_loss_weight>0
        v_sum, v_sumsq, v_sqerr_sum, n_v = 0.0, 0.0, 0.0, 0
        pts_sum, pts_sumsq, pts_sqerr_sum, n_pts = 0.0, 0.0, 0.0, 0
        opp_sum, opp_sumsq, opp_sqerr_sum, n_opp = 0.0, 0.0, 0.0, 0
        brier_sqerr_sum, n_brier = 0.0, 0  # Task #34
        with torch.no_grad():
            for _v_batch in val_dataloader:
                if encoder == "2d":
                    (v_planes, v_states, v_targets_p, v_targets_v, v_masks, _vmoon, v_pol_w,
                     v_targets_points, v_rounds, v_own, v_targets_opp_points, v_opp_mask,
                     v_targets_v_wdl, v_wdl_outcome, v_targets_endgame, v_endgame_mask,
                     v_rank_ids, v_rank_q, v_rank_mask) = _v_batch
                    # RAM-Optimierung v21 (Bitpacking): Entpacken wie im
                    # Trainingszweig, siehe dortigen Kommentar.
                    if val_dataset.bitpacked:
                        v_planes = unpack_planes_batch(v_planes)
                    # RAM-Optimierung v20: Cast wie im Trainingszweig.
                    v_planes = v_planes.to(device).float()
                else:
                    (v_states, v_targets_p, v_targets_v, v_masks, _vmoon, v_pol_w,
                     v_targets_points, v_rounds, v_own, v_targets_opp_points, v_opp_mask,
                     v_targets_v_wdl, v_wdl_outcome, v_targets_endgame, v_endgame_mask,
                     v_rank_ids, v_rank_q, v_rank_mask) = _v_batch
                if val_dataset.bitpacked:
                    v_masks = unpack_masks_batch(v_masks)
                v_states = v_states.to(device).float()
                v_targets_p = v_targets_p.to(device).float()
                v_targets_v = v_targets_v.to(device)
                v_targets_points = v_targets_points.to(device)
                v_targets_opp_points = v_targets_opp_points.to(device)
                v_opp_mask = v_opp_mask.to(device)
                v_targets_v_wdl = v_targets_v_wdl.to(device)
                v_wdl_outcome = v_wdl_outcome.to(device)
                v_targets_endgame = v_targets_endgame.to(device)
                v_endgame_mask = v_endgame_mask.to(device)
                v_masks = v_masks.to(device).float()
                v_pol_w = v_pol_w.to(device)
                if loss_setup.ranking_loss_weight > 0.0:
                    v_rank_ids  = v_rank_ids.to(device)
                    v_rank_q    = v_rank_q.to(device)
                    v_rank_mask = v_rank_mask.to(device)
                _vout = model(v_planes, v_states) if encoder == "2d" else model(v_states)
                v_pred_p, v_pred_v, _v_pred_moon, v_pred_points, v_pred_own = _vout[:5]
                (_v_pred_points_logits, v_pred_value_wdl_logits,
                 v_pred_opp_points, v_pred_endgame) = _unpack_optional_outputs(model, _vout)
                own_meter.add(v_pred_own, v_own)
                if v_pred_endgame is not None:
                    _eg_w = v_endgame_mask.view(-1, 1)
                    val_endgame_sqerr_sum += (((v_pred_endgame - (v_targets_endgame * 2.0 - 1.0)) ** 2) * _eg_w).sum().item()
                    val_endgame_n += _eg_w.sum().item()
                # Task #35b: rein DESKRIPTIVE Val-Metrik (paarweise
                # Ranking-Accuracy, STATUS.md-Vorgabe) -- NICHT Teil von
                # val_combined/der Checkpoint-Auswahl. Gewichtete Summe
                # ueber alle Val-Batches (Anzahl gueltiger Paare variiert
                # je Batch, ein einfaches Batch-Mittel wuerde kleine
                # Batches ueberbewerten).
                if loss_setup.ranking_loss_weight > 0.0:
                    _, _v_rk_acc, _v_rk_n = _pairwise_ranking_loss(
                        v_pred_p, v_rank_ids, v_rank_q, v_rank_mask)
                    if _v_rk_acc is not None:
                        val_rank_correct_sum += _v_rk_acc * _v_rk_n
                        val_rank_n += _v_rk_n
                v_masked_logits = v_pred_p + (v_masks - 1) * 1e9
                v_log_probs = F.log_softmax(v_masked_logits, dim=1)
                v_per_sample_ce = -torch.sum(v_targets_p * v_log_probs, dim=1)
                v_rw = (v_rounds.to(device) != 5).float() if loss_setup.exclude_round5 else None
                v_w = v_pol_w if v_rw is None else v_pol_w * v_rw
                v_p_loss = (v_per_sample_ce * v_w).sum() / v_w.sum().clamp(min=1e-6)
                # Task #12, WICHTIG: der VALIDIERUNGS-Punkteverlust bleibt
                # auch bei aktivem Verteilungs-Kopf MSE auf dem
                # ERWARTUNGSWERT -- absichtlich NICHT die Kreuzentropie des
                # Trainings. Grund: `val_combined` ist zugleich die
                # Auswahlmetrik fuer den besten Checkpoint. Waere sie in den
                # beiden A/B-Armen eine andere GROESSE, waeren die Arme nicht
                # vergleichbar -- genau der Fehler, der am 2026-07-28 beim
                # lr1e5-Arm beinahe zur falschen Entscheidung gefuehrt haette
                # (siehe STATUS.md "Seed-Sweep", Abschnitt val_combined).
                # Task #34: der VALIDIERUNGS-Value-Verlust folgt (anders
                # als der Punkte-Verlust oben) bewusst DEMSELBEN Loss wie
                # das Training des jeweiligen Arms (MSE fuer 'tanh', BCE
                # fuer 'wdl') -- die STATUS.md-Vorgabe akzeptiert
                # ausdruecklich, dass `val_combined` dadurch zwischen den
                # Armen NICHT vergleichbar ist (nur armintern zur
                # Checkpoint-Auswahl, siehe Kommentar an der v_loss-Stelle
                # oben im Trainingsblock). Der arm-uebergreifend
                # vergleichbare Wert ist der Brier-Score weiter unten.
                if v_pred_value_wdl_logits is not None:
                    v_logit_diff = v_pred_value_wdl_logits[:, 1] - v_pred_value_wdl_logits[:, 0]
                    v_wdl_target = v_targets_v_wdl.view(-1)
                    # `--wdl-hard-only`: Val-Loss konsistent zum Trainings-
                    # Ziel auf dem rohen Ausgang (Maskierung wie im
                    # Trainingsblock; der Brier unten bleibt unveraendert,
                    # er nutzt ohnehin schon `wdl_outcome`).
                    if loss_setup.wdl_bootstrap_destretch:
                        # Erosions-Arm B: Val-Ziel identisch zum
                        # Trainingsziel transformieren (sonst misst der
                        # Val-Loss ein anderes Ziel als trainiert wird).
                        v_wdl_target = _destretch_wdl_target(
                            v_wdl_target, v_wdl_outcome.view(-1),
                            loss_setup.destretch_a, loss_setup.destretch_b)
                    if loss_setup.wdl_hard_only:
                        v_raw = v_wdl_outcome.view(-1)
                        v_mask = (v_raw >= 0.0).float()
                        # Audit-F3: Val-Zweig muss `v_rw` genauso
                        # respektieren wie der Trainingszweig -- sonst
                        # enthaelt val_combined (Auswahlmetrik!) bei
                        # `--exclude-round5` andere Samples als der Loss.
                        if v_rw is not None:
                            v_mask = v_mask * v_rw.view(-1)
                        v_hard_t = v_raw.clamp(min=0.0)
                        if loss_setup.wdl_label_smooth > 0.0:
                            v_hard_t = v_hard_t * (1.0 - loss_setup.wdl_label_smooth) + 0.5 * loss_setup.wdl_label_smooth
                        v_bce_h = F.binary_cross_entropy_with_logits(
                            v_logit_diff, v_hard_t, reduction="none") * v_mask
                        v_v_loss = v_bce_h.sum() / v_mask.sum().clamp(min=1e-6)
                    elif v_rw is None:
                        v_v_loss = F.binary_cross_entropy_with_logits(v_logit_diff, v_wdl_target)
                    else:
                        v_rw2 = v_rw.view(-1, 1)
                        v_den = v_rw2.sum().clamp(min=1e-6)
                        v_bce = F.binary_cross_entropy_with_logits(v_logit_diff, v_wdl_target, reduction="none")
                        v_v_loss = (v_bce.view(-1, 1) * v_rw2).sum() / v_den
                elif v_rw is None:
                    v_v_loss = loss_setup.mse_loss(v_pred_v, v_targets_v)
                else:
                    v_rw2 = v_rw.view(-1, 1)
                    v_den = v_rw2.sum().clamp(min=1e-6)
                    v_v_loss = (((v_pred_v - v_targets_v) ** 2) * v_rw2).sum() / v_den
                if v_rw is None:
                    v_points_loss = loss_setup.mse_loss(v_pred_points, v_targets_points)
                else:
                    v_rw2 = v_rw.view(-1, 1)
                    v_den = v_rw2.sum().clamp(min=1e-6)
                    v_points_loss = (((v_pred_points - v_targets_points) ** 2) * v_rw2).sum() / v_den
                val_ploss_sum += v_p_loss.item()
                val_vloss_sum += v_v_loss.item()
                val_pointsloss_sum += v_points_loss.item()
                val_batches += 1

                # Task #34: R² auf der ARM-EIGENEN Groesse -- 'tanh'
                # bleibt byte-identisch (targets_v/pred_v, [-1,1]-Marge),
                # 'wdl' vergleicht auf der [0,1]-Wahrscheinlichkeitsskala
                # (P(Sieg) = (v_pred_v+1)/2 gegen targets_v_wdl) -- dieselben
                # Groessen wie der Loss oben, daher intern konsistent, aber
                # NICHT direkt mit dem 'tanh'-R² vergleichbar (andere
                # Zielgroesse).
                if v_pred_value_wdl_logits is not None:
                    v_p_win = (v_pred_v + 1.0) * 0.5
                    v_sum += v_targets_v_wdl.sum().item()
                    v_sumsq += (v_targets_v_wdl ** 2).sum().item()
                    v_sqerr_sum += ((v_targets_v_wdl - v_p_win) ** 2).sum().item()
                    n_v += v_targets_v_wdl.numel()
                else:
                    v_sum += v_targets_v.sum().item()
                    v_sumsq += (v_targets_v ** 2).sum().item()
                    v_sqerr_sum += ((v_targets_v - v_pred_v) ** 2).sum().item()
                    n_v += v_targets_v.numel()

                # Task #34 (STATUS.md "gib pro Epoche eine Value-
                # KALIBRIERUNGSKENNZAHL aus, die zwischen Armen
                # vergleichbar ist"): Brier-Score von P(Sieg)=(pred_v+1)/2
                # gegen den ROHEN, UNGEBLENDETEN tatsaechlichen Ausgang
                # (`wdl_outcome`, -1 = unbekannt/maskiert) -- UNABHAENGIG
                # vom Arm, weil `pred_v` in BEIDEN Armen auf derselben
                # [-1,1]-Position/Skala liegt (siehe forward()-Kommentar in
                # neural_net.py). Anders als `targets_v`/`targets_v_wdl`
                # (beide TD-geblendet) ist `wdl_outcome` NICHT geblendet --
                # genau deshalb ist dieser Wert arm-uebergreifend
                # vergleichbar, waehrend val_vloss/value_r2 es nicht sind.
                brier_p_win = (v_pred_v + 1.0) * 0.5
                brier_mask = (v_wdl_outcome >= 0.0).float()
                brier_n_batch = brier_mask.sum().item()
                if brier_n_batch > 0:
                    brier_sqerr_sum += (((brier_p_win - v_wdl_outcome.clamp(min=0.0)) ** 2)
                                        * brier_mask).sum().item()
                    n_brier += brier_n_batch

                pts_sum += v_targets_points.sum().item()
                pts_sumsq += (v_targets_points ** 2).sum().item()
                pts_sqerr_sum += ((v_targets_points - v_pred_points) ** 2).sum().item()
                n_pts += v_targets_points.numel()

                # Task #28: Val-MSE + R² NUR ueber die tatsaechlich
                # gemaskten (opp_mask==1) Samples -- analog zum
                # Ownership-Loss-Muster, NICHT die volle Val-Menge (sonst
                # verwaesserte ein Alt-Cache-Anteil ohne das Feld die
                # Kennzahl mit erfundenen Nullen).
                if v_pred_opp_points is not None:
                    opp_m = v_opp_mask.view(-1, 1)
                    opp_n_batch = opp_m.sum().item()
                    if opp_n_batch > 0:
                        opp_batch_loss = (((v_targets_opp_points - v_pred_opp_points) ** 2)
                                          * opp_m).sum() / opp_m.sum().clamp(min=1e-6)
                        val_opp_pointsloss_sum += opp_batch_loss.item()
                        val_opp_batches += 1
                        opp_sum += (v_targets_opp_points * opp_m).sum().item()
                        opp_sumsq += ((v_targets_opp_points ** 2) * opp_m).sum().item()
                        opp_sqerr_sum += (((v_targets_opp_points - v_pred_opp_points) ** 2)
                                          * opp_m).sum().item()
                        n_opp += opp_n_batch
        model.train()
        epoch_val_ploss = val_ploss_sum / max(val_batches, 1)
        epoch_val_vloss = val_vloss_sum / max(val_batches, 1)
        epoch_val_pointsloss = val_pointsloss_sum / max(val_batches, 1)
        epoch_val_opp_pointsloss = (val_opp_pointsloss_sum / val_opp_batches
                                    if val_opp_batches > 0 else None)
        # Schema 18: maskiertes Val-MSE des endgame_head -- None (statt
        # einer erfundenen 0.0), wenn kein einziges maskiertes Sample im
        # Val-Split lag (Alt-Cache/Kopf inaktiv). Geht NICHT in
        # val_combined/die Brier-Checkpoint-Auswahl ein (Muster opp_loss,
        # siehe Kommentar am Trainings-Loss-Block oben).
        epoch_val_endgame_mse = (val_endgame_sqerr_sum / val_endgame_n
                                 if val_endgame_n > 0 else None)
        # Task #35b: gewichtetes Mittel ueber alle Val-Batches -- None
        # (statt einer erfundenen 0.0), wenn kein einziges gueltiges Paar
        # im Val-Split lag (Gewicht 0.0/Alt-Cache-Split ohne Geschwister-
        # Set). Rein deskriptiv, geht NICHT in val_combined ein.
        epoch_val_ranking_acc = (val_rank_correct_sum / val_rank_n
                                 if val_rank_n > 0 else None)
        epoch_val_ownloss = own_meter.value()  # PREREG_frozen_trunk_head.md

        def _r2(sum_y, sumsq_y, sqerr, n):
            if n == 0:
                return None
            ss_tot = sumsq_y - (sum_y ** 2) / n
            if ss_tot <= 1e-9:  # entartet: Val-Targets praktisch konstant
                return None
            return 1.0 - sqerr / ss_tot

        epoch_val_value_r2 = _r2(v_sum, v_sumsq, v_sqerr_sum, n_v)
        epoch_val_points_r2 = _r2(pts_sum, pts_sumsq, pts_sqerr_sum, n_pts)
        epoch_val_opp_points_r2 = _r2(opp_sum, opp_sumsq, opp_sqerr_sum, n_opp)
        epoch_val_brier = brier_sqerr_sum / n_brier if n_brier > 0 else None

    return {"epoch_val_ploss": epoch_val_ploss, "epoch_val_vloss": epoch_val_vloss, "epoch_val_pointsloss": epoch_val_pointsloss, "epoch_val_value_r2": epoch_val_value_r2, "epoch_val_points_r2": epoch_val_points_r2, "epoch_val_opp_pointsloss": epoch_val_opp_pointsloss, "epoch_val_opp_points_r2": epoch_val_opp_points_r2, "epoch_val_endgame_mse": epoch_val_endgame_mse, "epoch_val_ranking_acc": epoch_val_ranking_acc, "epoch_val_brier": epoch_val_brier, "epoch_val_ownloss": epoch_val_ownloss}


def train(version_name, load_version=None, input_epoch=None, hidden_size=None, early_stop=True,
          select_by_brier=False, wdl_hard_only=False,
          wdl_label_smooth=0.0, wdl_bootstrap_destretch=False,
          destretch_a=0.0051, destretch_b=1.9269,
          show_plot=True, val_frac=0.1, train_file_limit=None, lr=None, lr_schedule="none",
          lr_t_max=None,
          exclude_round5=False, ownership_weight=None, seed=None, snapshot=True,
          value_weight=None, points_weight=None, value_target_variant="default",
          points_dist_bins=None, reinit_points_head=False, encoder="flat",
          value_target_lambda=1.0, opp_points_head=False, endgame_head=False, value_head="tanh",
          ranking_loss_weight=0.0, conjunction_head=False, head_warmstart=True, extra_data_dir=None,
          freeze_trunk=False):
    # PREREG_frozen_trunk_head.md: harte Vorab-Validierung des Freeze-Modus,
    # VOR jedem teuren Daten-Laden (Muster --value-target-lambda unten).
    validate_freeze_args(freeze_trunk, ownership_weight, load_version, val_frac)
    # Task #34: harte Validierung wie bei --value-target-lambda -- kein
    # stiller Fallback auf einen unbekannten Wert.
    if value_head not in VALUE_HEAD_VARIANTS:
        sys.exit(f"❌ --value-head {value_head!r} unbekannt -- erlaubt: {VALUE_HEAD_VARIANTS}.")
    # λ-Misch-Value-Target-Experiment (Willemsen et al. 2021, "soft-Z"):
    # harte Validierung VOR jedem teuren Daten-Laden -- kein stiller Clamp
    # (siehe train.py --load-Footgun-Historie im Modulkommentar/Memory
    # feedback_num_actions_change_breaks_old_checkpoints: neue Flags muessen
    # hart abbrechen statt still auf unerwartetes Verhalten zurueckzufallen).
    if not (0.0 <= value_target_lambda <= 1.0):
        sys.exit(
            f"❌ --value-target-lambda {value_target_lambda!r} ausserhalb [0,1] -- Abbruch. "
            f"1.0 = Bestandsverhalten (kein Mix), 0.0 = ausschliesslich root_q."
        )
    # PREREG_ownership_corpus.md §3.4: additiver Datei-Zugang, hart validiert
    # WIE die anderen CLI-Args oben -- ein Tippfehler im Pfad soll sofort
    # abbrechen, nicht still 0 zusaetzliche Dateien finden.
    if extra_data_dir is not None and not Path(extra_data_dir).is_dir():
        sys.exit(f"❌ --extra-data-dir {extra_data_dir!r} ist kein vorhandenes Verzeichnis -- Abbruch.")
    # Warm-Start-Checkpoint sofort validieren (vor dem teuren Daten-Laden).
    # --load hängt selbst "alphazero_" an; wer versehentlich den vollen
    # Dateinamen übergibt, landet bei alphazero_alphazero_*.pth. Das doppelte
    # Präfix wird erkannt und mit Warnung korrigiert. Fehlt der aufgelöste
    # Checkpoint, bricht das Training hart ab: der frühere stille
    # From-Scratch-Fallback hat im v13-Zyklus 6 Epochen gekostet, weil er nur
    # am zu niedrigen Epoche-1-Val-R² erkennbar war.
    if encoder not in ("flat", "2d"):
        sys.exit(f"❌ Unbekannter --encoder '{encoder}' -- erlaubt: 'flat', '2d'.")
    # Diagnose-Instrumentierung (2026-07-31, Arm A/B): einmalig physisches
    # Gesamt-RAM + Commit-Limit der Maschine loggen -- Nenner fuer die
    # RSS/Commit-Log-Interpretation waehrend des Laufs (siehe _mem_info_gb).
    _sys_mem = _system_mem_info_gb()
    if _sys_mem is not None:
        total_phys, avail_phys, total_commit, avail_commit = _sys_mem
        print(f"🖥️  System-RAM: {total_phys:.1f} GB gesamt, {avail_phys:.1f} GB frei beim Start "
              f"| Commit-Limit: {total_commit:.1f} GB, {avail_commit:.1f} GB frei beim Start")
    load_path = None
    if load_version:
        if load_version.startswith("alphazero_"):
            corrected = load_version[len("alphazero_"):]
            if (MODELS_DIR / f"alphazero_{corrected}.pth").exists():
                print(f"⚠️  --load '{load_version}' enthält bereits das Präfix 'alphazero_' — "
                      f"verwende '{corrected}'.")
                load_version = corrected
        load_path = MODELS_DIR / f"alphazero_{load_version}.pth"
        if not load_path.exists():
            sys.exit(
                f"❌ Start-Modell nicht gefunden: {load_path}\n"
                f"   --load erwartet den Versionsnamen OHNE 'alphazero_'-Präfix "
                f"(z.B. --load v12b_lr_best für alphazero_v12b_lr_best.pth).\n"
                f"   Abbruch, um stilles Training von null zu verhindern."
            )
        # Task #11 Phase 2: im 2D-Modus darf NUR von einem 2D-Checkpoint warm
        # gestartet werden -- ein stiller Teil-Load (Flach-Checkpoint hat
        # z.B. kein `conv.*`, aber teils gleich benannte `policy_head.*`/
        # `value_head.*`-Keys, die load_state_dict(strict=False) klaglos
        # uebernehmen wuerde) wuerde den Conv-Zweig zufaellig lassen, OHNE
        # dass das auffiele -- harter Fehler statt stillem Teil-Load.
        _load_ckpt_state = torch.load(str(load_path), map_location="cpu")["model_state"]
        _load_ckpt_encoder = encoder_from_state_dict(_load_ckpt_state)
        if _load_ckpt_encoder != encoder:
            sys.exit(
                f"❌ --encoder {encoder!r}, aber --load '{load_version}' ist ein "
                f"{_load_ckpt_encoder!r}-Checkpoint. Warm-Start ueber Encoder-Grenzen "
                f"hinweg ist nicht sinnvoll (Architektur passt nicht) -- Abbruch statt "
                f"stillem Teil-Load."
            )
        # Task #34: KEIN harter Abbruch (anders als beim Encoder oben) -- ein
        # Wechsel der Value-Kopf-Variante beim Warm-Start ist bewusst erlaubt
        # (analog zu --reinit-points-head/--points-dist-bins): die bestehende
        # Shape-Mismatch-Skip-Logik weiter unten erkennt `value_head.*`
        # automatisch und laesst NUR diesen Kopf frisch starten, Trunk/Policy/
        # uebrige Koepfe bleiben warm. Nur ein informativer Hinweis vorab.
        _load_ckpt_value_head = value_head_variant_from_state(_load_ckpt_state)
        if _load_ckpt_value_head != value_head:
            print(f"ℹ️  --value-head {value_head!r}, aber --load '{load_version}' ist ein "
                  f"{_load_ckpt_value_head!r}-Checkpoint -- der Value-Kopf startet FRISCH "
                  f"(automatischer Shape-Mismatch-Skip weiter unten), Trunk/Policy/uebrige "
                  f"Koepfe starten warm.")

    # 1. Daten laden (Nutzt jetzt dynamisch den DATA_DIR Pfad)
    # Val-Split auf DATEI-Ebene (nicht Zug-Ebene!): Zuege derselben Partie sind
    # stark korreliert, ein Zug-Split wuerde nahezu identische Zustaende in
    # Training UND Validierung streuen und ein zu gutes Val-R² vortaeuschen.
    # Bewusst PRO TRAININGSLAUF neu gezogen (kein ueber Generationen fixer
    # Val-Satz) -- das Val-Ergebnis soll nur beantworten "ueberfittet DIESES
    # Modell auf sein eigenes aktuelles Fenster", nicht als generations-
    # uebergreifendes Benchmark dienen (das leistet schon die Arena vs.
    # Champion/Heuristik).
    all_files = sorted(glob.glob(str(DATA_DIR / "*.pkl")))
    # MOSAIC_DATA_EXCLUDE (Fenster-Pinning, 2026-08-07): MUSS VOR dem
    # Train/Val-Split greifen -- data/ waechst waehrend laufender
    # Generierungen, und schon die SPLIT-Partition haengt an der
    # Gesamtliste (Vorfall pi_ctrl_s3: frisch gelandete v19wdlann-Dateien
    # verschoben den Seed-Shuffle -> anderer Key, Voll-Neubau,
    # kontaminiertes Fenster). Gleicher Filter wie in neural_net.py.
    import os as _os
    # `re` unbedingt, nicht nur im _excl-Zweig: MOSAIC_VAL_POOL unten braucht es
    # auch ohne gesetztes MOSAIC_DATA_EXCLUDE.
    import re as _re
    _excl = _os.environ.get("MOSAIC_DATA_EXCLUDE")
    if _excl:
        _n0 = len(all_files)
        all_files = [f for f in all_files if not _re.search(_excl, _os.path.basename(f))]
        print(f"🔒 MOSAIC_DATA_EXCLUDE={_excl!r}: {_n0 - len(all_files)} von {_n0} Dateien ausgeschlossen (vor Split).")

    # PREREG_ownership_corpus.md §3.4: additiver Datei-Zugang -- NACH dem
    # MOSAIC_DATA_EXCLUDE-Filter (der ist fuer das waehrend laufender
    # Generierung wachsende Standard-Fenster gedacht, siehe Kommentar oben;
    # ein --extra-data-dir ist ein bewusst hinzugefuegtes, separates Korpus
    # und bleibt davon unberuehrt). Leer/None (Default) -> `all_files`
    # unveraendert, byte-identisch zum Bestand (Task-#28-Muster). NICHT
    # rekursiv, gleiche `*.pkl`-Konvention wie DATA_DIR (§1: Unterordner sind
    # strukturell getrennt, dieses Flag ist genau die vorgesehene Bruecke).
    if extra_data_dir:
        extra_files = sorted(glob.glob(str(Path(extra_data_dir) / "*.pkl")))
        print(f"➕ --extra-data-dir {extra_data_dir!r}: {len(extra_files)} zusaetzliche Datei(en) gefunden.")
        all_files = sorted(all_files + extra_files)

    # Lauf-Manifest + Korpus-Log (#64 Teil 2) -- siehe Funktionskommentare
    # oben. Additiv, rührt die train_file_limit-Logik unten nicht an.
    _run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    _t_start_train = time.time()
    _t_daten_fertig = None
    # Val-Pool-Waechter (2026-08-27): MOSAIC_VAL_POOL schuetzt den Val-Split
    # beim Warm-Start heute nur, wenn man daran DENKT -- ohne die Variable
    # zieht der Split still frei (Mechanismus und die ~21 Prozent
    # Kontamination stehen im Kommentar am Split-Block unten). Der Zustand
    # wird hier EINMAL bestimmt: als Feld im Manifest, damit spaeter ablesbar
    # ist, unter welcher Bedingung der Split entstand, und als Warnung im Log.
    # Kein Abbruch: beim normalen Warm-Start rotiert der Vorgaenger-Korpus
    # groesstenteils aus dem Fenster, die Kontamination ist dann klein.
    # Die Bedingung `val_frac > 0 and len(all_files) >= 10` ist DIESELBE wie am
    # Split-Block unten -- sonst meldete der Waechter eine Kontaminationsgefahr
    # fuer einen Split, den es gar nicht gibt.
    _val_split_happens = val_frac > 0 and len(all_files) >= 10
    _val_pool_env = _os.environ.get("MOSAIC_VAL_POOL")
    if _val_pool_env:
        _val_pool_guard = "pool_set"
    elif load_version and _val_split_happens:
        _val_pool_guard = "warned"
    else:
        _val_pool_guard = "not_applicable"
    if _val_pool_guard == "warned":
        print(f"⚠️  Warm-Start (--load {load_version}) OHNE MOSAIC_VAL_POOL: der Val-Split "
              f"wird frei aus dem gesamten Fenster gezogen und kann darum Dateien "
              f"enthalten, auf denen das Startmodell bereits trainiert wurde -- die "
              f"Val-Metrik (und mit --select-by-brier die Checkpoint-Auswahl) ist dann "
              f"zugunsten spaeter Epochen verzerrt. Ausweg: MOSAIC_VAL_POOL auf einen "
              f"Regex setzen, der nur unverbrauchte Dateien als Val-Kandidaten zulaesst.")
    _cli_args = {
        "name": version_name, "load": load_version, "epochs": input_epoch, "hidden": hidden_size,
        "early_stop": early_stop, "show_plot": show_plot, "val_frac": val_frac,
        "train_file_limit": train_file_limit, "lr": lr, "lr_schedule": lr_schedule,
        "lr_t_max": lr_t_max,
        "exclude_round5": exclude_round5, "ownership_weight": ownership_weight,
        "conjunction_head": conjunction_head,
        "seed": seed, "snapshot": snapshot,
        "value_weight": value_weight, "points_weight": points_weight,
        "value_target_variant": value_target_variant, "encoder": encoder,
        "value_target_lambda": value_target_lambda, "opp_points_head": opp_points_head,
        "endgame_head": endgame_head,
        "value_head": value_head,
        "ranking_loss_weight": ranking_loss_weight,
        "extra_data_dir": extra_data_dir, "freeze_trunk": freeze_trunk,
        "val_pool": _val_pool_env,
        "val_pool_guard": _val_pool_guard,
        # MOSAIC_IGNORE_POLICY_TARGET_VALID definiert einen Trainings-ARM
        # (PREREG_v22_window.md par.4: der Policy-Kopf sieht die
        # `policy_target_valid=false`-Zuege oder nicht -- im v22-Korpus 61,8
        # Prozent der Draftingzuege), stand aber in keinem Manifest-Feld:
        # geprueft am hv2sanity_ptv-Manifest, 0 Treffer. Der Cache-Key
        # waechterte den Schalter, das Manifest schwieg -- exakt die
        # Fehlerklasse des MOSAIC_CARRIER_MANIFEST-Vorfalls
        # (train_manifest.py:74). Abgelegt wird der AUFGELOESTE Wert mit
        # DERSELBEN Regel wie neural_net.py:9 (`== "1"`, nicht Truthiness) --
        # rein dokumentierend, kein Verhalten haengt daran.
        "ignore_policy_target_valid":
            _os.environ.get("MOSAIC_IGNORE_POLICY_TARGET_VALID") == "1",
    }
    # Manifest auf der GEFILTERTEN Liste (Fix 2026-08-21): neural_net.py:1217
    # wendet MOSAIC_DATA_EXCLUDE beim Laden auf die GESAMTE Liste an, auch auf
    # --extra-data-dir-Dateien -- das Manifest dokumentierte bis hierher die
    # ungefilterte Liste und damit ein Fenster, das nie trainiert wird
    # (Vorfall v21-asymS: asymN als Bestandteil gelistet, obwohl vom Loader
    # ausgeschlossen). Der Datenfluss (Split auf all_files) bleibt unberuehrt.
    _manifest_files = all_files
    if _excl:
        _manifest_files = [f for f in all_files if not _re.search(_excl, _os.path.basename(f))]
    write_train_manifest(version_name, _cli_args, corpus_composition(_manifest_files), _run_timestamp,
                          policy_carriers=policy_carrier_report(_manifest_files, _SELFPLAY_FILENAME_RE))

    val_files = []
    train_files = None  # None == MosaicDataset laedt wie bisher den ganzen Ordner
    if val_frac > 0 and len(all_files) >= 10:
        # MOSAIC_VAL_POOL (2026-08-25): Regex, der die KANDIDATEN fuer den
        # Val-Split einschraenkt -- alles, was NICHT matcht, geht garantiert in
        # den Trainings-Teil. Default (ungesetzt) = bestandsidentisch.
        #
        # ANLASS, und er ist spezifisch: beim Warm-Start von einem Modell, das
        # auf einer TEILMENGE desselben Korpus trainiert wurde, enthaelt ein
        # frei gezogener Val-Split Dateien, die das Startmodell bereits
        # trainiert hat. Beim hv2-Fall waeren das rund 21 Prozent des Val-Sets
        # (240 Val-Dateien von 2.400, davon ~51 aus den 513 hv2sanity-Dateien).
        # `--select-by-brier` waehlt den Checkpoint AUF diesem Mass aus -- die
        # Auswahl waere systematisch zugunsten spaeter Epochen verzerrt.
        # Sonst rotiert der Vorgaenger-Korpus beim naechsten Fenster
        # groesstenteils aus; hier bleibt er vollstaendig drin, deshalb ist die
        # Lage anders als bei den bisherigen Warm-Starts.
        # Derselbe Wert wie oben beim Waechter (`_val_pool_env`) -- EINMAL
        # gelesen, damit Manifest-Feld `val_pool_guard` und tatsaechlicher
        # Split nicht auseinanderlaufen koennen.
        _val_pool_rx = _val_pool_env
        if _val_pool_rx:
            _pool = [f for f in all_files if _re.search(_val_pool_rx, _os.path.basename(f))]
            _rest = [f for f in all_files if not _re.search(_val_pool_rx, _os.path.basename(f))]
            n_val = max(1, round(len(all_files) * val_frac))
            if len(_pool) < n_val:
                raise SystemExit(
                    f"MOSAIC_VAL_POOL trifft nur {len(_pool)} Dateien, gebraucht werden "
                    f"{n_val} fuer val_frac={val_frac}. Entweder den Regex weiten oder "
                    f"val_frac senken -- ein stillschweigend kleinerer Val-Split waere "
                    f"ein anderes Mass als das registrierte.")
            shuffled = _pool[:]
            random.Random(20260707).shuffle(shuffled)
            val_files = sorted(shuffled[:n_val])
            train_files = sorted(shuffled[n_val:] + _rest)
            print(f"🔒 MOSAIC_VAL_POOL: Val-Split aus {len(_pool)} von {len(all_files)} "
                  f"Kandidaten gezogen ({n_val} Val-Dateien); die uebrigen "
                  f"{len(_rest)} gehen garantiert ins Training.")
        else:
            shuffled = all_files[:]
            random.Random(20260707).shuffle(shuffled)
            n_val = max(1, round(len(shuffled) * val_frac))
            val_files = sorted(shuffled[:n_val])
            train_files = sorted(shuffled[n_val:])

    # Daten-Skalierungs-Ablation (Task #69): Trainings-Dateien NACH dem
    # Val-Split auf train_file_limit kappen -- der Val-Split oben ist davon
    # unberuehrt (bleibt identisch zu v11/vollem Korpus), nur die Trainings-
    # menge schrumpft. Eigener, vom Val-Split-Seed getrennter Seed (+1), damit
    # die Auswahl nicht zufaellig mit dem Val-Split-Shuffle korreliert.
    if train_file_limit is not None and train_files is not None and len(train_files) > train_file_limit:
        subsample_rng = random.Random(20260707 + 1)
        pool = train_files[:]
        subsample_rng.shuffle(pool)
        orig_n = len(train_files)
        train_files = sorted(pool[:train_file_limit])
        print(f"   Subsampling (Task #69): {len(train_files)} von {orig_n} Trainings-Dateien "
              f"(Seed 20260708, Val-Split unveraendert)")

    if value_target_variant != "default":
        print(f"🧪 Value-Target-Variante (Task #84, rtv-Ablation): '{value_target_variant}'")
    if encoder == "2d":
        print(f"🧩 Encoder: '2d' (Task #11 Phase 2, Mosaic2DNet -- Conv-Zweig auf state_to_planes "
              f"+ Flach-Zweig auf state_to_tensor)")
    dataset = MosaicDataset(str(DATA_DIR), files=train_files, value_target_variant=value_target_variant,
                            encoder=encoder, conjunction_head=conjunction_head)
    _t_daten_fertig = time.time()
    print(f"⏱️  Datenaufbau: {_t_daten_fertig - _t_start_train:.1f}s "
          f"({len(dataset)} Zustaende aus {len(train_files or [])} Dateien)")
    if len(dataset) == 0:
        print(f"❌ Fehler: Keine Daten im Ordner '{DATA_DIR}' gefunden!")
        return
    # λ-Misch-Value-Target-Experiment: mischt das TATSAECHLICH trainierte
    # Zielfeld IN-PLACE, direkt nach dem Laden, VOR dem DataLoader-Wrap
    # (siehe MosaicDataset.apply_value_target_lambda-Docstring). KORREKTHEITS-
    # FIX (Koordinator-Befund 2026-08-08): frueher wurde immer `self.values`
    # (tanh-Ziel) gemischt, auch wenn `--value-head wdl` gegen `self.values_wdl`
    # trainiert -- der Mix lief in dem Fall komplett ins Leere. `wdl=` waehlt
    # jetzt das zum aktiven Kopf passende Feld; das gemischte Feld heisst im
    # Log ausdruecklich beim Namen, damit ein solcher Irrtum kuenftig sofort
    # auffaellt. Wird auch bei value_target_lambda=1.0 aufgerufen -- die
    # Methode ruehrt das Zielfeld dann NICHT an (frueher Return), liefert
    # aber den Praesenz-Anteil fuers Log (PREREG_lambda_target.md verlangt
    # den Misch-Anteil dokumentiert, auch als Baseline-Referenz).
    _lambda_mix_wdl = (value_head == "wdl")
    _lambda_mix_field = "values_wdl" if _lambda_mix_wdl else "values"
    train_root_q_frac = dataset.apply_value_target_lambda(value_target_lambda, wdl=_lambda_mix_wdl)
    if value_target_lambda < 1.0:
        print(f"🧪 λ-Misch-Value-Target (Willemsen et al. 2021, soft-Z): λ={value_target_lambda} "
              f"auf Zielfeld '{_lambda_mix_field}' -- {train_root_q_frac*100:.1f}% der "
              f"Trainings-Samples haben root_q (gemischt), Rest bleibt beim bisherigen Ziel.")
    else:
        print(f"ℹ️  λ-Misch-Value-Target: λ=1.0 (kein Mix, Bestandsverhalten, Zielfeld waere "
              f"'{_lambda_mix_field}') -- {train_root_q_frac*100:.1f}% der Trainings-Samples "
              f"HAETTEN root_q (informativ).")

    val_dataset = None
    if val_files:
        val_dataset = MosaicDataset(str(DATA_DIR), files=val_files, value_target_variant=value_target_variant,
                                    encoder=encoder, conjunction_head=conjunction_head)
        val_root_q_frac = val_dataset.apply_value_target_lambda(value_target_lambda, wdl=_lambda_mix_wdl)
        print(f"   Val-Split: {len(train_files)} Trainings-Dateien / {len(val_files)} Val-Dateien "
              f"({len(dataset):,} / {len(val_dataset):,} Züge)")
        if value_target_lambda < 1.0:
            print(f"   Val-root_q-Anteil (gemischt auf '{_lambda_mix_field}'): {val_root_q_frac*100:.1f}%")

    # drop_last=True: ohne das kann die letzte Batch einer Epoche zufällig auf
    # Größe 1 fallen (Datensatzgröße mod BATCH_SIZE == 1) — BatchNorm im Netz
    # verlangt >1 Sample pro Kanal im Training und crasht sonst hart.
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True, drop_last=True)
    val_dataloader = (DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)
                      if val_dataset is not None else None)

    # 2. Hardware Setup
    # Reproduzierbarkeit (Task #9, 2026-07-28): bis dahin setzte train.py
    # KEINEN Seed -- zwei Laeufe mit identischen Flags unterschieden sich durch
    # Gewichts-Init UND Batch-Shuffling. Damit war jeder Trainings-A/B auf
    # Einzellaeufen (v12b_lr, v17_lrfix, r5base/r5excl) nur bis auf eine
    # UNBEKANNTE Lauf-zu-Lauf-Varianz interpretierbar. Mit --seed laufen zwei
    # Arme auf identischer Init und identischer Batch-Reihenfolge, der
    # Unterschied ist dann allein die getestete Aenderung.
    # Default None = altes Verhalten (unseeded), damit Alt-Rezepte unveraendert
    # bleiben. torch.manual_seed deckt Init UND DataLoader-Shuffle ab.
    if seed is not None:
        torch.manual_seed(seed)
        random.seed(seed)
        print(f"   Seed          : {seed} (reproduzierbar)")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n🚀 Starte PyTorch Training auf: {device.type.upper()}")

    # 3. Modell Setup
    from config import HIDDEN_SIZE as DEFAULT_HIDDEN
    hs = hidden_size if hidden_size is not None else DEFAULT_HIDDEN
    print(f"🧠 Netz-Architektur: {dataset.input_size}→{hs}→{hs}→{hs}")
    # --lr/--lr-schedule (Task #77, v12b): additiv zum bisherigen Verhalten --
    # ohne --lr bleibt LEARNING_RATE aus config.py unveraendert massgeblich,
    # ohne --lr-schedule bleibt Adam mit konstanter LR wie bisher (kein
    # Scheduler-Objekt, kein zusaetzlicher .step()-Aufruf).
    effective_lr = lr if lr is not None else LEARNING_RATE
    # --value-weight/--points-weight (Task #79, v12d): additiv analog zu
    # --lr -- ohne die Flags bleiben VALUE_WEIGHT/POINTS_WEIGHT aus config.py
    # unveraendert massgeblich (Bestandsverhalten). Beeinflussen NUR den
    # Trainings-Loss (loss = p_loss + value_weight*v_loss + points_weight*
    # points_loss) und die Checkpoint-Auswahl (dieselbe gewichtete Val-Metrik,
    # siehe unten) -- NICHT die Targets selbst, der HDF5/Pickle-Cache bleibt
    # deshalb fuer diesen Sweep unveraendert wiederverwendbar.
    effective_value_weight = value_weight if value_weight is not None else VALUE_WEIGHT
    effective_points_weight = points_weight if points_weight is not None else POINTS_WEIGHT
    effective_ownership_weight = ownership_weight if ownership_weight is not None else OWNERSHIP_WEIGHT
    # Task #12: 0 = Skalar-Regression (Bestandsverhalten), >0 = Verteilungs-Kopf.
    effective_points_dist_bins = (points_dist_bins if points_dist_bins is not None
                                  else POINTS_DIST_BINS)
    if effective_points_dist_bins > 0:
        print(f"   Punkte-Kopf   : VERTEILUNG ueber {effective_points_dist_bins} Bins "
              f"(HL-Gauss sigma={POINTS_DIST_SIGMA} Bin-Breiten, Task #12) -- "
              f"Ausgabe bleibt der Erwartungswert")
    print(f"⚙️  Hyperparameter (config.py, ggf. per CLI überschrieben):")
    print(f"   Learning Rate : {effective_lr}" + (f"  (Default {LEARNING_RATE})" if lr is not None else ""))
    print(f"   LR-Schedule   : {lr_schedule}")
    print(f"   Ownership-W   : {effective_ownership_weight}"          f"{'  (Kopf aus)' if effective_ownership_weight <= 0.0 else ''}")
    if conjunction_head:
        print(f"   Konjunktionen : AN -- Ownership-Kopf traegt zusaetzlich "
              f"{CONJUNCTION_TARGETS} Zusatzziele: 25 Konjunktionen + 9 Layout (Cache-Key '+conj_v2')"
              + ("  ⚠️  wirkungslos bei Ownership-W 0.0" if effective_ownership_weight <= 0.0 else ""))
    print(f"   Batch Size    : {BATCH_SIZE}")
    print(f"   Value Weight  : {effective_value_weight}  (Sieg/Niederlage, Aux-Signal fuer den Trunk)"
          + (f"  (Default {VALUE_WEIGHT})" if value_weight is not None else ""))
    print(f"   Points Weight : {effective_points_weight}  (Punktestand-Prognose, Aux-Signal)"
          + (f"  (Default {POINTS_WEIGHT})" if points_weight is not None else ""))
    if opp_points_head:
        print(f"   Opp-Punkte-Kopf: AN (Task #28, PREREG_task28_aggression.md) -- "
              f"Gewicht={effective_points_weight} (=POINTS_WEIGHT-Override), NICHT Teil von val_combined")
    if endgame_head:
        print(f"   Endgame-Kopf  : AN (Schema 18, PREREG_plate_intervention.md) -- "
              f"Gewicht={effective_points_weight} (=POINTS_WEIGHT-Override), NUR R5-Drafting-Zone "
              f"maskiert, NICHT Teil von val_combined")
    if ranking_loss_weight > 0.0:
        print(f"   Ranking-Loss  : AN (Task #35b, Geschwister-Q) -- Gewicht={ranking_loss_weight}, "
              f"Margin={RANKING_MARGIN}, Top-{RANKING_TOPK}-Geschwister/Zustand, "
              f"NICHT Teil von val_combined (rein additiv, kein neuer Modell-Kopf)")
    if value_head == "wdl":
        print(f"   Value-Kopf    : WDL (Task #34) -- 2-Logit-Softmax-Klassifikation, "
              f"Kreuzentropie auf Sieg/Niederlage-Ziel (`values_wdl`). ACHTUNG: val_combined "
              f"ist damit NICHT gegen einen 'tanh'-Lauf vergleichbar (andere Loss-EINHEIT, "
              f"siehe Kommentar an der current_metric-Stelle) -- Value-Brier-Score (unten) "
              f"ist die arm-uebergreifend vergleichbare Kennzahl.")
    else:
        print(f"   Value-Kopf    : tanh (Bestandsverhalten) -- Skalar-Regression, MSE auf "
              f"`values`.")
    if encoder == "2d":
        model = Mosaic2DNet(input_size=dataset.input_size, num_actions=NUM_ACTIONS, hidden_size=hs,
                            points_dist_bins=effective_points_dist_bins, opp_points_head=opp_points_head,
                            endgame_head=endgame_head, conjunction_head=conjunction_head,
                            value_head_variant=value_head)
    else:
        model = MosaicNet(input_size=dataset.input_size, num_actions=NUM_ACTIONS, hidden_size=hs,
                          points_dist_bins=effective_points_dist_bins, opp_points_head=opp_points_head,
                          endgame_head=endgame_head, conjunction_head=conjunction_head,
                          value_head_variant=value_head)

    # Warm Start? (Existenz von load_path wurde oben bereits hart validiert)
    if load_version:
        print(f"📥 Lade altes Model als Startpunkt: {load_path.name}")
        ckpt = torch.load(str(load_path), map_location=device)
        old_state = ckpt["model_state"]
        new_state = model.state_dict()
        # strict=False allein reicht NICHT bei INPUT_SIZE-Änderungen: es
        # toleriert fehlende/zusätzliche Keys, aber KEINE Shape-Mismatches
        # bei gleichnamigen Keys (z.B. body.0.weight bei geändertem
        # INPUT_SIZE) — das würde crashen. Shape-inkompatible Keys daher
        # vorher explizit rausfiltern; der Rest (tiefere Body-Schichten,
        # alle Heads) startet weiterhin warm. Alte Checkpoints mit einem
        # value_head.* haben automatisch keine Entsprechung mehr in
        # new_state (Head existiert nicht mehr) -- werden einfach ignoriert.
        if reinit_points_head:
            # Task #12, FAIRER KONTROLLARM: der Verteilungs-Kopf KANN nicht warm
            # starten (andere Ausgabebreite) -- er beginnt zwangslaeufig zufaellig.
            # Ein Kontrollarm, dessen Skalar-Kopf warm startet, waere deshalb im
            # Vorteil, und der A/B wuerde "Verteilung vs. Skalar" mit "frisch vs.
            # warm" vermischen. Mit dieser Option startet auch der Skalar-Kopf
            # frisch, der Unterschied ist dann allein die Kopf-ART.
            drop = [k for k in old_state if k.startswith("points_head.")]
            print(f"   ↻ points_head wird NEU initialisiert ({len(drop)} Tensoren) "
                  f"-- fairer Kontrollarm zu --points-dist-bins")
            old_state = {k: v for k, v in old_state.items() if k not in drop}

        old_state = apply_head_warmstart(old_state, new_state, head_warmstart)
        skipped = [k for k in old_state if k in new_state and old_state[k].shape != new_state[k].shape]
        if skipped:
            print(f"   ⚠️  Shape-Mismatch, startet frisch: {', '.join(skipped)}")
            old_state = {k: v for k, v in old_state.items() if k not in skipped}
        model.load_state_dict(old_state, strict=False)

    model.to(device)

    # PREREG_frozen_trunk_head.md: Trunk + alle uebrigen Koepfe einfrieren,
    # nur `ownership_head` weitertrainieren. Ohne --freeze-trunk ein no-op
    # (Task-#28-Muster). Siehe freeze_trunk.py fuer den BatchNorm-Riegel.
    ftz = TrunkFreeze.setup(model, freeze_trunk)

    # 4. Training Parameter
    optimizer = optim.Adam(ftz.trainable_params(model), lr=effective_lr)

    # Epochen-Anzahl ---
    epochs = input_epoch
    print(f"   Epochen       : {epochs}")

    # LR-Scheduler (Task #77, v12b_lr): Cosine-Annealing ueber `T_max` Epochen,
    # `eta_min=0` (Standard von CosineAnnealingLR) -- die LR faellt bis Epoche
    # `T_max` gegen 0. Kein Scheduler (None) reproduziert exakt das alte
    # Verhalten (konstante LR).
    #
    # BERICHTIGUNG 2026-08-27: hier stand, ein frueher Stopp breche die Kurve
    # "einfach vorzeitig ab, das ist unproblematisch". Das verharmlost. T_max
    # hing bis hierher fest an `--epochs`, und mit Early Stopping (Patience 5)
    # endet ein Lauf typischerweise weit vor `--epochs`. Nachgerechnet (Faktor
    # (1 + cos(pi * t / T_max)) / 2): bei T_max = 100 und Stopp bei t = 15
    # liegt die LR noch bei 94,6 Prozent der Start-LR -- es hat faktisch KEIN
    # Annealing stattgefunden, der Lauf ist ein Lauf mit konstanter LR unter
    # anderem Namen. Erst bei T_max = 25 waere sie bis t = 15 auf 34,5 Prozent
    # gefallen. Der Sweep-Horizont (`--epochs`) und der Anneal-Horizont sind
    # also zwei verschiedene Groessen; `--lr-t-max` entkoppelt sie.
    #
    # `--lr-t-max` ungesetzt (Default None) = T_max ist `epochs`, also
    # bestandsidentisch -- KEIN stiller Default-Wechsel, nur die Warnung unten.
    lr_scheduler = None
    if lr_schedule == "cosine":
        cosine_t_max = lr_t_max if lr_t_max is not None else epochs
        if lr_t_max is not None:
            print(f"   Cosine-T_max  : {cosine_t_max} (--lr-t-max, entkoppelt von --epochs={epochs})")
        elif early_stop and epochs is not None and epochs > COSINE_TMAX_WARN_EPOCHS:
            print(f"   ⚠️  --lr-schedule cosine mit T_max=--epochs={epochs} UND aktivem Early "
                  f"Stopping (Patience 5): stoppt der Lauf frueh, ist die LR kaum gefallen "
                  f"(Faktor (1+cos(pi*t/T_max))/2 -- bei T_max={epochs} und Stopp bei Epoche 15 "
                  f"noch {(1 + math.cos(math.pi * 15 / epochs)) / 2:.1%} der Start-LR; zum "
                  f"Vergleich T_max={COSINE_TMAX_WARN_EPOCHS}: 34,5%). Ausweg: --lr-t-max auf "
                  f"den erwarteten Stopp-Horizont setzen oder --lr-schedule plateau nehmen.")
        lr_scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=cosine_t_max)
    elif lr_schedule == "plateau":
        # Grob bis zum Plateau, dann feiner in der Zielregion (Nutzer-Anstoss
        # 2026-08-17). Adaptiv, braucht also den Horizont NICHT -- der Grund, warum
        # Cosine beim Cold Start ausfaellt: dessen T_max braucht einen geschaetzten
        # Anneal-Horizont (per --lr-t-max, sonst --epochs), und der
        # Saettigungspunkt eines Laufs von null ist unbekannt.
        # patience=2 ist bewusst KLEINER als die 5 Epochen des Early Stoppings --
        # sonst braeche der Lauf ab, bevor die LR je gesenkt wuerde. Greift die
        # Senkung, kommt wieder Fortschritt und der Early-Stop-Zaehler faellt zurueck.
        # factor/patience sind gaengige Startwerte, NICHT fuer dieses Projekt gemessen.
        lr_scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode="min", factor=0.5, patience=2)
    elif lr_schedule not in (None, "none"):
        print(f"   ⚠️  Unbekanntes --lr-schedule '{lr_schedule}' -- ignoriert (konstante LR).")
    if load_version:
        print(f"🔄 Warm-Start erkannt: Trainiere für {epochs} Epochen.")
    else:
        print(f"🆕 Neues Modell: Trainiere für {epochs} Epochen.")
    # --------------------------------------

    # 5. DIE SCHLEIFE
    mse_loss = nn.MSELoss()
    n_batches = len(dataloader)
    policy_history  = []
    epoch_history   = []   # je Epoche ein Datensatz -> Manifest (Nutzer 2026-08-17)
    value_history   = []
    points_history  = []
    # Task #28: nur befuellt, wenn --opp-points-head aktiv ist -- rein
    # informatives Logging/Checkpoint-Feld, NICHT Teil der Checkpoint-
    # Auswahl (siehe Kommentar an der `current_metric`-Stelle unten).
    opp_points_history = []
    # Schema 18 (PREREG_plate_intervention.md): nur befuellt, wenn
    # --endgame-head aktiv ist -- gleiches Muster wie opp_points_history.
    endgame_history = []
    # Task #35b: nur befuellt, wenn ranking_loss_weight>0 ist -- gleiches
    # Muster wie endgame_history/opp_points_history. NICHT Teil von
    # val_combined (siehe Kommentar an der current_metric-Stelle unten).
    ranking_loss_history = []
    val_ploss_history = []
    # Value/Points hatten bisher KEINEN Val-Split-Loss/R² -- nur der rohe
    # Trainings-Loss wurde reported (siehe TRAINING SUMMARY unten). Für den
    # Runden-Übergangs-Sampling-Vergleich (evaluations/STATUS.md, Phase-1-
    # Gate: points_forecast-Val-R² gegen die archivierte 0.2-0.3-Baseline)
    # braucht es einen echten Held-out-Wert -- Trainings-Loss allein sagt
    # nichts über Generalisierung aus.
    val_vloss_history = []
    val_pointsloss_history = []
    val_value_r2_history = []
    val_points_r2_history = []
    val_opp_pointsloss_history = []
    val_opp_points_r2_history = []
    # Schema 18: maskiertes Val-MSE des endgame_head, nur relevant wenn aktiv
    # (Muster val_opp_pointsloss_history, aber kein R² -- root_q-Ziel ist auf
    # der R5-Zone stark einseitig verteilt, R² waere hier keine sinnvolle
    # Zusatzkennzahl, siehe PREREG_plate_intervention.md).
    val_endgame_mse_history = []
    # Task #35b: deskriptive paarweise Ranking-Accuracy auf dem Val-Split
    # (STATUS.md-Vorgabe) -- nur befuellt, wenn ranking_loss_weight>0.
    # NICHT Teil von val_combined/der Checkpoint-Auswahl (rein informativ,
    # gleiches Muster wie val_endgame_mse_history).
    val_ranking_acc_history = []
    # Task #34: Brier-Score von P(Sieg) gegen den echten Spielausgang -- die
    # ARM-UEBERGREIFEND vergleichbare Value-Kalibrierungskennzahl (siehe
    # Kommentar an der Berechnungsstelle im Val-Loop). Anders als
    # val_vloss/value_r2 gilt sie fuer 'tanh'- UND 'wdl'-Laeufe gleichermassen.
    val_brier_history = []
    # PREREG_frozen_trunk_head.md (aus PREREG_ownership_corpus.md §10.3): der
    # Ownership-Val-Verlust fehlte bisher komplett -- deshalb konnte
    # `val_combined` den Kopf gar nicht sehen und waehlte durchgaengig Epoche 1.
    # Wird ab jetzt bei jedem Lauf mit Ownership-Gewicht > 0 mitgemessen (rein
    # additiv: geht NUR im Freeze-Modus in die Auswahl ein, sonst nur ins Log).
    val_ownloss_history = []
    plateau_window    = 5
    plateau_threshold = 0.01
    early_stop_patience = 5 if early_stop else 999999
    policy_plateau_since = None
    # Task #34 (2026-08-05, Nutzer-Vorschlag): DOPPELTES Early Stopping.
    # Bisher wurde NUR das Val-Policy-Plateau ueberwacht. Bei einem Lauf mit
    # FRISCH initialisiertem Value-Kopf (z.B. Wechsel tanh->wdl, Shape-
    # Mismatch beim Warm-Start) plateaut die warm gestartete Policy sofort,
    # waehrend der neue Value-Kopf noch lernt -- der Lauf stoppte damit
    # systematisch zu frueh (real beobachtet 2026-08-05: die v20_wdl-Arme
    # stoppten bei Epoche 15 mit einem 15 Epochen alten Kopf gegen eine ueber
    # 10 Generationen gereifte Kontrolle -- der Arena-Vergleich mass damit
    # nicht das ZIEL, sondern die Kopf-Reife).
    # Jetzt: Stop erst, wenn BEIDE Seiten plateauen. Value-Seite ueber den
    # BRIER-Score (arm-uebergreifend vergleichbar, existiert fuer tanh- UND
    # wdl-Arme; die rohen Value-Losses waeren es nicht).
    value_plateau_since = None
    stopped_early = False
    stop_reason = None
    total_history = []

    # Best-Checkpoint-Tracking: bisher wurde NUR der letzte Epochenstand
    # gespeichert, auch wenn Early Stopping (Patience-Fenster) erst einige
    # Epochen nach dem eigentlichen Optimum greift (siehe v8c: Minimum bei
    # Epoche 5, Stop typischerweise erst bei Epoche plateau_since+patience).
    # Bestes Modell nach GEWICHTETER Kombination aus Policy-/Value-/Points-
    # Val-Loss (Fallback Train-Loss ohne Val-Split), dieselbe Gewichtung wie
    # der Trainings-Loss selbst -- siehe Kommentar an der Vergleichsstelle
    # unten (Fund 8, Bugfixes.txt: reine Policy-Val-Loss-Auswahl ignorierte
    # den Value-Head, den erklärten Engpass dieser Session) -- zusätzlich als
    # *_best.pth/.onnx sichern.
    best_combined_metric = float("inf")
    best_epoch = None
    best_state_dict = None
    # Task #34 Audit: separater VALUE-optimaler Checkpoint (siehe Kommentar an
    # der Tracking-Stelle im Epoch-Loop).
    best_brier_metric = float("inf")
    best_brier_epoch = None
    best_brier_state_dict = None

    # ── Live-Plot (zusätzlich zur Textausgabe) ──────────────────────────────
    plot = None
    if show_plot:
        try:
            import matplotlib
            import matplotlib.pyplot as plt
            plt.ion()
            fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
            fig.suptitle(f"Training {version_name}")
            ax_top.set_ylabel("Policy Loss")
            ax_bot.set_ylabel("Value / Points Loss (Aux)")
            ax_bot.set_xlabel("Epoche")
            (line_policy,) = ax_top.plot([], [], label="Policy (Train)", color="tab:orange")
            (line_value,) = ax_bot.plot([], [], label="Value (Train)", color="tab:green")
            (line_points,) = ax_bot.plot([], [], label="Points (Train)", color="tab:purple")
            # Val-Kurven (gestrichelt, gleiche Farbe) -- der ganze Grund fuer
            # diese Ergaenzung: das v8-Overfitting (Value Train/Val-Verhaeltnis
            # 48.6x) war an der finalen Zahl allein erkennbar, aber NICHT, AB
            # WELCHER Epoche die Schere aufgeht -- nur sichtbar, wenn Train-
            # und Val-Kurve gemeinsam im Verlauf geplottet werden.
            (line_policy_val,) = ax_top.plot([], [], label="Policy (Val)", color="tab:orange", linestyle="--")
            (line_value_val,) = ax_bot.plot([], [], label="Value (Val)", color="tab:green", linestyle="--")
            (line_points_val,) = ax_bot.plot([], [], label="Points (Val)", color="tab:purple", linestyle="--")
            ax_top.legend(loc="upper right")
            ax_bot.legend(loc="upper right")
            plot = {
                "fig": fig, "ax": ax_top, "ax_bot": ax_bot,
                "line_policy": line_policy, "line_value": line_value, "line_points": line_points,
                "line_policy_val": line_policy_val, "line_value_val": line_value_val, "line_points_val": line_points_val,
                "plateau_line": None,
            }
        except Exception as e:
            print(f"⚠️  Live-Plot deaktiviert (kein Display?): {e}")
            plot = None

    # Diagnose-Instrumentierung (2026-07-31): alle 100 Batches eine RSS/Commit-
    # Zeile, MIT flush=True -- falls der Prozess stirbt, bevor der naechste
    # Puffer-Flush ohnehin faellig waere, steht die letzte Messung trotzdem
    # in der Log-Datei. Absichtlich unabhaengig vom Encoder (auch im Flach-
    # Pfad aktiv) fuer eine direkte Vergleichsbasis.
    # Alle 100 Batches waren 215 Zeilen je Epoche und ueber einen Lauf rund 3.000 --
    # der Epochen-Verlauf im Manifest deckt den Informationsbedarf jetzt ab
    # (Nutzer 2026-08-17). Ganz abschalten waere trotzdem falsch: RAM ist in diesem
    # Projekt Engpass 2, ein Lauf belegt 15-19 GB von 32. 0 = aus.
    _mem_log_every = int(os.environ.get("MOSAIC_MEM_LOG_EVERY", "2000"))

    epoch_count_done = 0
    # Die Verlust-Knoepfe einmal buendeln (siehe `LossSetup`): sie aendern
    # sich innerhalb eines Laufs nicht, und beide Durchgaenge brauchen sie.
    _loss_setup = LossSetup(
        destretch_a=destretch_a, destretch_b=destretch_b,
        wdl_bootstrap_destretch=wdl_bootstrap_destretch,
        wdl_hard_only=wdl_hard_only, wdl_label_smooth=wdl_label_smooth,
        ranking_loss_weight=ranking_loss_weight, exclude_round5=exclude_round5,
        value_weight=effective_value_weight, points_weight=effective_points_weight,
        ownership_weight=effective_ownership_weight, mse_loss=mse_loss,
    )
    for epoch in range(epochs):
        epoch_count_done = epoch + 1
        _t = _train_one_epoch(
            model, dataloader, dataset, optimizer, device, encoder,
            n_batches, epoch, _mem_log_every, ftz, _loss_setup,
        )
        t_loss = _t["t_loss"]
        t_ploss = _t["t_ploss"]
        t_vloss = _t["t_vloss"]
        t_pointsloss = _t["t_pointsloss"]
        t_opp_pointsloss = _t["t_opp_pointsloss"]
        t_endgameloss = _t["t_endgameloss"]
        t_rankingloss = _t["t_rankingloss"]

        epoch_ploss = t_ploss / n_batches
        epoch_vloss = t_vloss / n_batches
        epoch_pointsloss = t_pointsloss / n_batches
        epoch_opp_pointsloss = t_opp_pointsloss / n_batches
        epoch_endgameloss = t_endgameloss / n_batches
        epoch_rankingloss = t_rankingloss / n_batches
        epoch_tloss = t_loss / n_batches
        policy_history.append(epoch_ploss)
        value_history.append(epoch_vloss)
        points_history.append(epoch_pointsloss)
        opp_points_history.append(epoch_opp_pointsloss)
        endgame_history.append(epoch_endgameloss)
        ranking_loss_history.append(epoch_rankingloss)
        total_history.append(epoch_tloss)

        # ── Validierung (Policy + Value + Points) auf dem NIE trainierten
        # Datei-Split. R² (nicht bloß MSE) je Kopf: 1 - SS_res/SS_tot über
        # den GESAMTEN Val-Split (nicht Mittel über Batch-R²s -- R² ist eine
        # globale Kennzahl, die von der Gesamtvarianz des Val-Sets abhängt,
        # ein Batch-Mittel würde das verzerren). SS_tot/SS_res daher als
        # laufende Summen über alle Batches akkumuliert, R² erst danach
        # einmalig berechnet.
        _v = _validate_one_epoch(
            model, val_dataloader, val_dataset, device, encoder, _loss_setup,
        )
        epoch_val_ploss = _v["epoch_val_ploss"]
        epoch_val_vloss = _v["epoch_val_vloss"]
        epoch_val_pointsloss = _v["epoch_val_pointsloss"]
        epoch_val_value_r2 = _v["epoch_val_value_r2"]
        epoch_val_points_r2 = _v["epoch_val_points_r2"]
        epoch_val_opp_pointsloss = _v["epoch_val_opp_pointsloss"]
        epoch_val_opp_points_r2 = _v["epoch_val_opp_points_r2"]
        epoch_val_endgame_mse = _v["epoch_val_endgame_mse"]
        epoch_val_ranking_acc = _v["epoch_val_ranking_acc"]
        epoch_val_brier = _v["epoch_val_brier"]
        epoch_val_ownloss = _v["epoch_val_ownloss"]
        val_ploss_history.append(epoch_val_ploss)
        val_vloss_history.append(epoch_val_vloss)
        val_pointsloss_history.append(epoch_val_pointsloss)
        val_value_r2_history.append(epoch_val_value_r2)
        val_points_r2_history.append(epoch_val_points_r2)
        val_opp_pointsloss_history.append(epoch_val_opp_pointsloss)
        val_opp_points_r2_history.append(epoch_val_opp_points_r2)
        val_endgame_mse_history.append(epoch_val_endgame_mse)
        val_ranking_acc_history.append(epoch_val_ranking_acc)
        val_brier_history.append(epoch_val_brier)
        val_ownloss_history.append(epoch_val_ownloss)

        # Fund 8 (externer Hinweis, Bugfixes.txt Abschnitt C): "bestes Modell"
        # wurde bisher NUR nach Policy-Val-Loss gewählt -- der Value-Head
        # (dieser Session zentraler Engpass) lief dabei unbeachtet mit, ein
        # Checkpoint konnte also als "best" markiert werden, waehrend der
        # Value-Head an genau diesem Punkt bereits schlechter war als an
        # einem anderen Epochenstand. Fix: dieselbe gewichtete Kombination
        # wie der Trainings-Loss selbst (`p_loss + VALUE_WEIGHT*v_loss +
        # POINTS_WEIGHT*points_loss`), nur auf den Val-Metriken -- "best"
        # bedeutet jetzt "bestes GESAMTZIEL", nicht mehr "bestes Policy-Val
        # allein". Fallback (kein Val-Split) nutzt dieselbe Formel auf den
        # Trainings-Losses, konsistent mit dem bisherigen Fallback-Muster.
        #
        # Task #28 (PREREG_task28_aggression.md "Minimal-invasiver Zuschnitt"
        # Punkt 2): der opp-Punkte-Loss geht BEWUSST NICHT in `current_metric`
        # ein, obwohl er mit POINTS_WEIGHT in den Trainings-`loss` einfliesst
        # (siehe oben) -- `val_combined` bleibt dieselbe GROESSE wie vor
        # diesem Task, Checkpoints aus Laeufen MIT und OHNE --opp-points-head
        # bleiben damit anhand dieser Metrik vergleichbar (sonst waeren
        # --opp-points-head-Laeufe stillschweigend auf einer anderen Skala
        # ausgewaehlt worden als alle Alt-Laeufe).
        #
        # Task #34 (STATUS.md "Achtung val_combined"): bei `--value-head wdl`
        # ist `epoch_val_vloss` eine Kreuzentropie (~0.65-0.69 auf binaerem
        # Ausgang) statt der bisherigen MSE (~0.03 auf dem weichen Ziel) --
        # FAKTOR ~22 unterschiedliche EINHEIT. `current_metric`/`val_combined`
        # bleibt dadurch NUR ARM-INTERN sinnvoll (zur Checkpoint-Auswahl
        # INNERHALB eines Laufs) -- ein direkter Zahlenvergleich
        # `val_combined(tanh-Lauf)` vs. `val_combined(wdl-Lauf)` ist UNGUELTIG
        # (vergleicht nicht dieselbe Groesse, exakt dasselbe Muster wie beim
        # `--value-weight`-Sweep, [[feedback-preregister-decision-metric]]).
        # Die arm-uebergreifend vergleichbare Kennzahl ist `epoch_val_brier`
        # (siehe Berechnung im Val-Loop oben) -- NICHT Teil von
        # `current_metric`, nur separat geloggt/gespeichert.
        # Task #34 (2026-08-05): `--select-by-brier` ersetzt den VALUE-Term durch
        # den Brier-Score. Grund: bei WDL-Armen ist `epoch_val_vloss` eine BCE
        # (~0,6) statt einer MSE (~0,03) -- der Term ist damit entweder
        # vernachlaessigbar (kleines value_weight) oder dominiert (grosses), und
        # die Auswahl faellt real auf Epoche 1, also einen praktisch
        # untrainierten frischen Kopf (beobachtet 2026-08-05). Der Brier liegt
        # fuer BEIDE Kopfarten im selben Wertebereich (~0,2) und macht den Term
        # wieder sinnvoll gewichtet. Default AUS -> byte-identisches Verhalten.
        # PREREG_frozen_trunk_head.md: im Freeze-Modus IST der Ownership-Val-
        # Verlust das Auswahlkriterium. Alles andere waere die Wiederholung des
        # §10.3-Fehlers -- policy/value sind hier konstant (eingefroren), eine
        # val_combined-Auswahl waere reines Rauschen auf einer Nachkommastelle.
        value_term_val = epoch_val_brier if (select_by_brier and epoch_val_brier is not None) else epoch_val_vloss
        if ftz.active and epoch_val_ownloss is not None:
            current_metric = epoch_val_ownloss
        elif epoch_val_ploss is not None:
            current_metric = epoch_val_ploss + effective_value_weight * value_term_val + effective_points_weight * epoch_val_pointsloss
        else:
            current_metric = epoch_ploss + effective_value_weight * epoch_vloss + effective_points_weight * epoch_pointsloss
        if current_metric < best_combined_metric:
            best_combined_metric = current_metric
            best_epoch = epoch + 1
            best_state_dict = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}

        # Task #34 Audit 2026-08-05: der VALUE-optimale Checkpoint existierte
        # bisher nie als Datei. Beobachtet (t34-Laeufe): der WDL-Brier ist bei
        # Epoche ~3 minimal (0,1990) und steigt danach MONOTON (0,2030 bei
        # E15) -- fortgesetztes Policy-Training erodiert den Value-Fit. Die
        # val_combined-Auswahl kann das nie einfangen, weil der Policy-Term
        # (~1,16) den Brier-Term (~0,2*w) IMMER dominiert -- auch mit
        # --select-by-brier faellt die Wahl auf das Policy-Optimum (E1).
        # Daher zusaetzlich den brier-besten Zustand festhalten (nur Tracking,
        # aendert Auswahl/Verhalten nicht; gespeichert wird am Trainingsende
        # als `_brierbest`, nur falls von final/best verschieden).
        if epoch_val_brier is not None and epoch_val_brier < best_brier_metric:
            best_brier_metric = epoch_val_brier
            best_brier_epoch = epoch + 1
            best_brier_state_dict = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}

        # ── Plateau-Erkennung (auf Val-Policy-Loss wenn vorhanden, sonst
        # Fallback auf Train-Loss) ───────────────────────────────────────────
        # WARUM Val statt Train: v8b zeigte, dass die Train-Policy-Loss noch
        # bis Epoche 56 weiter sank, waehrend die Val-Policy-Loss bereits ab
        # ~Epoche 15-18 ihr Minimum hatte und danach durchgehend STIEG (2.2 ->
        # 2.67) -- Train-Loss-Plateau-Erkennung haette das nie bemerkt, weil
        # sie ja gar nicht plateaut, sondern normal weiter faellt. `rel < 0`
        # (Val-Loss steigt) unterschreitet plateau_threshold automatisch und
        # loest Early Stopping korrekt aus, auch wenn "PLATEAU" fuer einen
        # tatsaechlich divergierenden Verlauf untertrieben ist.
        has_val_ploss = val_dataloader is not None
        plateau_series = plateau_series_for(          # PREREG_frozen_trunk_head.md
            ftz.active, val_ownloss_history,
            val_ploss_history if has_val_ploss else policy_history)
        plateau_marker = ""
        policy_plateaued = False
        if len(plateau_series) >= plateau_window * 2:
            recent   = sum(plateau_series[-plateau_window:]) / plateau_window
            previous = sum(plateau_series[-plateau_window*2:-plateau_window]) / plateau_window
            rel = (previous - recent) / previous if previous > 0 else 0
            if rel < plateau_threshold:
                policy_plateaued = True

        plateau_label = ("OWNERSHIP-PLATEAU" if ftz.active else
                         "VAL-POLICY-PLATEAU" if has_val_ploss else "POLICY-PLATEAU")
        if policy_plateaued:
            if policy_plateau_since is None:
                policy_plateau_since = epoch + 1
            plateau_marker = f"  🟡 {plateau_label}"
        else:
            policy_plateau_since = None      # Plateau muss zusammenhaengen

        # ── Value-Plateau (Task #34): identische Fensterlogik auf dem Brier ──
        brier_series = [b for b in val_brier_history if b is not None]
        value_plateaued = False
        if len(brier_series) >= plateau_window * 2:
            b_recent   = sum(brier_series[-plateau_window:]) / plateau_window
            b_previous = sum(brier_series[-plateau_window*2:-plateau_window]) / plateau_window
            b_rel = (b_previous - b_recent) / b_previous if b_previous > 0 else 0
            if b_rel < plateau_threshold:
                value_plateaued = True
        elif not brier_series:
            value_plateaued = True           # kein Brier messbar -> Bestandsverhalten
        if value_plateaued:
            if value_plateau_since is None:
                value_plateau_since = epoch + 1
            plateau_marker += "  🟠 VALUE-PLATEAU"
        else:
            value_plateau_since = None

        # ── Live-Plot aktualisieren (zusätzlich zur Textzeile unten) ────────
        if plot is not None:
            try:
                xs = list(range(1, len(total_history) + 1))
                plot["line_policy"].set_data(xs, policy_history)
                plot["line_value"].set_data(xs, value_history)
                plot["line_points"].set_data(xs, points_history)
                nan = float("nan")
                plot["line_policy_val"].set_data(xs, [v if v is not None else nan for v in val_ploss_history])
                plot["line_value_val"].set_data(xs, [v if v is not None else nan for v in val_vloss_history])
                plot["line_points_val"].set_data(xs, [v if v is not None else nan for v in val_pointsloss_history])
                if policy_plateau_since is not None and plot["plateau_line"] is None:
                    plot["plateau_line"] = plot["ax"].axvline(
                        policy_plateau_since, color="red", linestyle="--", alpha=0.5, label="Plateau")
                    plot["ax"].legend(loc="upper right")
                plot["ax"].relim()
                plot["ax"].autoscale_view()
                plot["ax_bot"].relim()
                plot["ax_bot"].autoscale_view()
                plot["fig"].canvas.draw()
                plot["fig"].canvas.flush_events()
                import matplotlib.pyplot as _plt
                _plt.pause(0.001)
            except Exception:
                plot = None  # Fenster evtl. geschlossen o.ä. — Rest ohne Plot weiterlaufen

        val_p_str = f" | Policy-Val={epoch_val_ploss:5.2f}" if epoch_val_ploss is not None else ""
        val_r2_str = ""
        if epoch_val_value_r2 is not None or epoch_val_points_r2 is not None:
            v_r2_s = f"{epoch_val_value_r2:.3f}" if epoch_val_value_r2 is not None else "n/a"
            p_r2_s = f"{epoch_val_points_r2:.3f}" if epoch_val_points_r2 is not None else "n/a"
            val_r2_str = f" | Val-R² Value={v_r2_s} Points={p_r2_s}"
        # Task #34: Brier-Score separat ausgewiesen (arm-uebergreifend
        # vergleichbar, siehe Kommentar an der Berechnungsstelle).
        val_brier_str = f" | Value-Brier={epoch_val_brier:.4f}" if epoch_val_brier is not None else ""
        # Schema 18 (PREREG_plate_intervention.md): kompakte Zusatz-Zeile
        # NUR bei aktivem Kopf, sonst bleibt die Ausgabe unveraendert (Muster
        # der uebrigen optionalen Koepfe hier, z.B. val_brier_str).
        endgame_str = ""
        if getattr(model, "has_endgame_head", False):
            _eg_val_s = f"{epoch_val_endgame_mse:.4f}" if epoch_val_endgame_mse is not None else "n/a"
            endgame_str = f" | Endgame: {epoch_endgameloss:.4f} / Val-MSE {_eg_val_s}"
        # Task #35b: kompakte Zusatz-Zeile NUR bei aktivem Gewicht, sonst
        # bleibt die Ausgabe unveraendert (gleiches Muster wie endgame_str).
        ranking_str = ""
        if ranking_loss_weight > 0.0:
            _rk_acc_s = f"{epoch_val_ranking_acc:.3f}" if epoch_val_ranking_acc is not None else "n/a"
            ranking_str = f" | Ranking: {epoch_rankingloss:.4f} / Val-Acc {_rk_acc_s}"
        # PREREG_frozen_trunk_head.md: sichtbar machen, WELCHES Kriterium greift.
        own_str = ""
        if epoch_val_ownloss is not None:
            own_str = (f" | Own-Val={epoch_val_ownloss:.4f}"
                       + ("  ⬅ AUSWAHLKRITERIUM" if ftz.active else ""))
        lr_str = f" | LR={optimizer.param_groups[0]['lr']:.2e}" if lr_scheduler is not None else ""
        # Epochen-Verlauf fuers Manifest. Bisher blieb er nur in der Konsole stehen und
        # war mit zwei Nachkommastellen zu grob, um daraus z.B. Scheduler-Parameter
        # abzuschaetzen (Anlass: Plateau-Abschaetzung 2026-08-17).
        epoch_history.append({
            "epoch": epoch + 1,
            "lr": optimizer.param_groups[0]["lr"],
            "policy_loss": epoch_ploss,
            "policy_val_loss": epoch_val_ploss,
            "value_loss": epoch_vloss,
            "value_val_loss": epoch_val_vloss,
            "value_val_brier": epoch_val_brier,
            "points_loss": epoch_pointsloss,
            "points_val_loss": epoch_val_pointsloss,
            "ownership_val_loss": epoch_val_ownloss,
            "val_combined": current_metric,
        })
        print(f"Epoche {epoch+1:2d}/{epochs} | Policy Loss: {epoch_ploss:6.2f}{val_p_str} "
              f"| Value: {epoch_vloss:.3f} | Points: {epoch_pointsloss:.3f}{val_r2_str}{val_brier_str}{own_str}{endgame_str}{ranking_str}{plateau_marker}{lr_str}")

        # LR-Schedule-Schritt NACH der Epoche (Standard-PyTorch-Reihenfolge:
        # optimizer.step() viele Male innerhalb der Epoche, scheduler.step()
        # einmal danach) -- bleibt bei lr_scheduler=None ein no-op.
        if lr_scheduler is not None:
            # ReduceLROnPlateau ist der einzige Scheduler hier, der die Metrik
            # braucht -- dieselbe, nach der auch der beste Checkpoint gewaehlt wird.
            if isinstance(lr_scheduler, optim.lr_scheduler.ReduceLROnPlateau):
                lr_scheduler.step(current_metric)
            else:
                lr_scheduler.step()

        # ── Early Stopping: BEIDE Koepfe muessen plateauen (Task #34) ──
        if policy_plateau_since is not None and value_plateau_since is not None:
            since = (epoch + 1) - max(policy_plateau_since, value_plateau_since)
            if since >= early_stop_patience:
                print(f"\n⏹️  Early Stopping: {plateau_label} seit Epoche {policy_plateau_since} "
                      f"+ VALUE-PLATEAU (Brier) seit Epoche {value_plateau_since} "
                      f"({since} Epochen ohne Fortschritt auf BEIDEN Seiten).")
                stopped_early = True
                stop_reason = "plateau"
                break

    max_loss = math.log(NUM_ACTIONS)
    final_p = epoch_ploss
    pct = final_p / max_loss * 100

    if pct < 8:
        quality = "⚠️  Overfitting-Verdacht"
    elif pct < 25:
        quality = "🟢 Sehr gut"
    elif pct < 40:
        quality = "🟡 Gut"
    elif pct < 70:
        quality = "🟠 Schwaches Signal"
    else:
        quality = "🔴 Nichts gelernt"

    print(f"\n{'='*55}")
    print(f"  TRAINING SUMMARY")
    print(f"{'='*55}")
    print(f"  Epochen:       {epochs}")
    print(f"  Züge:          {len(dataset):,}"
          + (f"  (+{len(val_dataset):,} Val, nie trainiert)" if val_dataset is not None else ""))
    print(f"  Batches/Epoche:{n_batches}")
    print(f"{'─'*55}")
    def _last_valid(history):
        for v in reversed(history):
            if v is not None:
                return v
        return None

    print(f"  Policy Loss:   {final_p:.4f} / {max_loss:.2f} max  ({pct:.1f}%)  {quality}")
    print(f"  Value Loss:    {value_history[-1]:.4f}  (Aux, Sieg/Niederlage +1/-1, Training)")
    print(f"  Points Loss:   {points_history[-1]:.4f}  (Aux, Punktestand-Prognose, Training)")
    final_val_ploss = _last_valid(val_ploss_history)
    final_val_vloss = _last_valid(val_vloss_history)
    final_val_pointsloss = _last_valid(val_pointsloss_history)
    final_value_r2 = _last_valid(val_value_r2_history)
    final_points_r2 = _last_valid(val_points_r2_history)
    final_opp_points_val_loss = _last_valid(val_opp_pointsloss_history)
    final_opp_points_r2 = _last_valid(val_opp_points_r2_history)
    final_value_brier = _last_valid(val_brier_history)
    if final_val_ploss is not None:
        policy_val_gap = final_val_ploss - final_p
        print(f"  Policy Val-Loss: {final_val_ploss:.4f}  (Gap ggü. Train: {policy_val_gap:+.4f})")
    # Val-R² (nicht bloß Val-Loss) ist die Kennzahl, gegen die die archivierte
    # 0.2-0.3-Plateau-Baseline (evaluations/STATUS.md) vergleichbar ist --
    # Loss allein sagt ohne Referenz-Skala wenig aus.
    if final_val_vloss is not None:
        r2_s = f"{final_value_r2:.4f}" if final_value_r2 is not None else "n/a"
        _head_label = "wdl/BCE, [0,1]-Skala" if value_head == "wdl" else "tanh/MSE, [-1,1]-Skala"
        print(f"  Value Val-Loss:  {final_val_vloss:.4f}  (Val-R²: {r2_s}, {_head_label} -- "
              f"NUR armintern vergleichbar, Task #34)")
    if final_value_brier is not None:
        print(f"  Value Brier:     {final_value_brier:.4f}  (P(Sieg) vs. echter Ausgang -- "
              f"ARM-UEBERGREIFEND vergleichbar, Task #34)")
    if final_val_pointsloss is not None:
        r2_s = f"{final_points_r2:.4f}" if final_points_r2 is not None else "n/a"
        print(f"  Points Val-Loss: {final_val_pointsloss:.4f}  (Val-R²: {r2_s})")
    if final_opp_points_val_loss is not None:
        r2_s = f"{final_opp_points_r2:.4f}" if final_opp_points_r2 is not None else "n/a"
        print(f"  Opp-Punkte Val-Loss: {final_opp_points_val_loss:.4f}  (Val-R²: {r2_s})  "
              f"(Task #28, NICHT Teil von val_combined)")
    print(f"{'─'*55}")
    if stopped_early:
        print(f"  ⏹️  Early Stopping (Policy-Plateau) nach Epoche {len(policy_history)}/{epochs}")
    if policy_plateau_since:
        print(f"  🟡 Plateau ab Epoche {policy_plateau_since}.")
        print(f"     → Für nächste Generation: mehr Sims im Self-Play.")
    else:
        print(f"  🟢 Kein Plateau — Policy sinkt noch. Mehr Epochen möglich.")
    print(f"{'='*55}")

    # 5b. Netzauslastung (Dead Neurons + Effective Rank)
    try:
        sample_batch = next(iter(dataloader))[0][:512].to(device)
        if sample_batch.shape[0] >= 2:
            cap = model.analyze_capacity(sample_batch)
            print(f"\n{'='*55}")
            print(f"  NETZAUSLASTUNG (Hidden Size: {hs})")
            print(f"{'─'*55}")
            print(f"  {'Schicht':<9} {'Dead':>11} {'Aktiv-Rate':>12} {'Eff.Rank':>15}")
            print(f"  {'─'*51}")
            for ln, m in cap.items():
                dead_str = f"{m['dead']}/{m['n_neurons']} ({m['dead_ratio']*100:.0f}%)"
                rank_str = f"{m['eff_rank']:.0f}/{m['n_neurons']} ({m['rank_pct']*100:.0f}%)"
                print(f"  {ln:<9} {dead_str:>11} {m['active_rate']*100:>11.0f}% {rank_str:>15}")
            print(f"  {'─'*51}")
            avg_dead = sum(m['dead_ratio'] for m in cap.values()) / len(cap)
            avg_rank = sum(m['rank_pct'] for m in cap.values()) / len(cap)
            if avg_dead > 0.4:
                print(f"  🔴 Viele tote Neuronen ({avg_dead*100:.0f}%) — Netz unterausgelastet.")
            elif avg_rank > 0.7:
                print(f"  🟡 Hohe Auslastung (Eff.Rank {avg_rank*100:.0f}%) — bei Plateau mehr Neuronen erwägen.")
            else:
                print(f"  🟢 Gesunde Auslastung (Dead {avg_dead*100:.0f}%, Rank {avg_rank*100:.0f}%).")
            print(f"{'='*55}")
        model.train()
    except Exception as e:
        print(f"  ⚠️  Auslastungsanalyse übersprungen: {e}")

    # 6. Speichern
    model.cpu()
    # Epochen-Verlauf ins bereits geschriebene Manifest nachtragen (es entsteht VOR
    # dem Training, den Verlauf gibt es erst danach).
    _mpath = MODELS_DIR / f"manifest_train_{version_name}_{_run_timestamp}.json"
    try:
        _m = json.loads(_mpath.read_text(encoding="utf-8"))
        _m["epoch_history"] = epoch_history
        _mpath.write_text(json.dumps(_m, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"📝 Epochen-Verlauf ({len(epoch_history)} Epochen) ins Manifest nachgetragen.")
    except Exception as e:
        print(f"  ⚠️  Epochen-Verlauf nicht nachtragbar ({e!r}) -- Rest laeuft weiter.")

    save_path = MODELS_DIR / f"alphazero_{version_name}.pth"
    actual_epochs = len(policy_history)
    checkpoint = {
        "model_state":       model.state_dict(),
        "version":           version_name,
        "timestamp":         __import__("datetime").datetime.now().isoformat(),
        "epochs":            actual_epochs,
        "epochs_requested":  epochs,
        "early_stopped":     stopped_early,
        "stop_reason":       stop_reason,
        "early_stop_epoch":  policy_plateau_since if stopped_early else None,
        "num_games":         len(dataset),  # Züge
        "input_size":        dataset.input_size,
        "num_actions":       NUM_ACTIONS,
        "hidden_size":       hs,
        "batch_size":        BATCH_SIZE,
        "lr":                effective_lr,
        "lr_schedule":       lr_schedule,
        # Nur bei 'cosine' belegt: der TATSAECHLICH benutzte Anneal-Horizont
        # (--lr-t-max oder ersatzweise --epochs). Ohne ihn ist aus dem
        # Checkpoint nicht ablesbar, wie weit die LR ueberhaupt abregeln konnte.
        "lr_t_max":          (lr_t_max if lr_t_max is not None else epochs) if lr_schedule == "cosine" else None,
        "final_policy_loss": round(final_p, 4),
        "final_policy_val_loss": round(final_val_ploss, 4) if final_val_ploss is not None else None,
        "final_value_loss":  round(value_history[-1], 4),
        "final_points_loss": round(points_history[-1], 4),
        "final_value_val_loss": round(final_val_vloss, 4) if final_val_vloss is not None else None,
        "final_points_val_loss": round(final_val_pointsloss, 4) if final_val_pointsloss is not None else None,
        "final_value_val_r2": round(final_value_r2, 4) if final_value_r2 is not None else None,
        "final_points_val_r2": round(final_points_r2, 4) if final_points_r2 is not None else None,
        "value_weight":      effective_value_weight,
        "points_weight":     effective_points_weight,
        "val_frac":          val_frac,
        "num_val_games":     len(val_dataset) if val_dataset is not None else 0,
        "policy_pct":        round(pct, 1),
        "load_version":      load_version,
        "value_target_variant": value_target_variant,
        "value_target_lambda": value_target_lambda,
        # Task #11 Phase 2: nur ein Bequemlichkeits-/Dokumentationsfeld --
        # `neural_net.py::encoder_from_state_dict` bleibt die maßgebliche,
        # rückwirkend funktionierende Quelle (Erkennung aus `model_state`).
        "encoder":           encoder,
        # Task #28 (PREREG_task28_aggression.md): analoges Bequemlichkeits-
        # feld -- `neural_net.py::opp_points_head_present` bleibt die
        # massgebliche, rueckwirkend funktionierende Quelle. `final_opp_*`
        # sind rein informativ, NICHT Teil von val_combined/der Checkpoint-
        # Auswahl (siehe Kommentar an der `current_metric`-Stelle oben).
        "opp_points_head":   bool(opp_points_head),
        "final_opp_points_loss": round(opp_points_history[-1], 4) if opp_points_history else None,
        "final_opp_points_val_loss": (
            round(final_opp_points_val_loss, 4) if final_opp_points_val_loss is not None else None),
        "final_opp_points_val_r2": (
            round(final_opp_points_r2, 4) if final_opp_points_r2 is not None else None),
        # Task #34: `neural_net.py::value_head_variant_from_state` bleibt die
        # massgebliche, rueckwirkend funktionierende Quelle (analog zu
        # `encoder`/`opp_points_head` oben) -- dieses Feld ist nur ein
        # Bequemlichkeits-/Dokumentationswert. `final_value_val_brier` ist die
        # arm-uebergreifend vergleichbare Kalibrierungskennzahl (siehe
        # Kommentar an der current_metric-Stelle) -- NICHT Teil von
        # val_combined/der Checkpoint-Auswahl, nur informativ.
        "value_head":        value_head,
        "final_value_val_brier": (
            round(final_value_brier, 4) if final_value_brier is not None else None),
        # Task #35b: analoges Bequemlichkeitsfeld -- kein neuer Modell-Kopf
        # (nutzt die bestehenden Policy-Logits), daher keine "*_present"-
        # Rueckerkennungsfunktion in neural_net.py noetig/vorhanden. Rein
        # informativ, NICHT Teil von val_combined/der Checkpoint-Auswahl.
        # PREREG_frozen_trunk_head.md: Freeze-Modus + der Ownership-Val-Verlust,
        # der ihn steuert (bei inaktivem Modus rein informativ).
        "freeze_trunk":      bool(freeze_trunk),
        "final_ownership_val_loss": (
            round(_last_valid(val_ownloss_history), 4)
            if _last_valid(val_ownloss_history) is not None else None),
        "ranking_loss_weight": ranking_loss_weight,
        "final_ranking_loss": round(ranking_loss_history[-1], 4) if ranking_loss_history else None,
        "final_ranking_val_acc": (
            round(val_ranking_acc_history[-1], 4)
            if val_ranking_acc_history and val_ranking_acc_history[-1] is not None else None),
    }
    torch.save(checkpoint, str(save_path))
    print(f"\n✅ Training beendet! Neues Model gespeichert unter:\n📂 {save_path}")

    best_version_name = None
    if best_state_dict is not None and best_epoch != actual_epochs:
        best_idx = best_epoch - 1
        best_checkpoint = dict(checkpoint)
        best_checkpoint["model_state"]      = best_state_dict
        best_checkpoint["epochs"]           = best_epoch
        best_checkpoint["is_best_checkpoint"] = True
        best_checkpoint["selected_by"]      = (ftz.selected_by() if ftz.active
                                                else "val_combined(p+v*value_w+pts*points_w)" if val_dataloader is not None
                                                else "train_combined(p+v*value_w+pts*points_w)")
        best_checkpoint["final_ownership_val_loss"] = (
            round(val_ownloss_history[best_idx], 4)
            if best_idx < len(val_ownloss_history) and val_ownloss_history[best_idx] is not None
            else None)
        best_checkpoint["final_policy_loss"] = round(policy_history[best_idx], 4)
        best_checkpoint["final_policy_val_loss"] = (
            round(val_ploss_history[best_idx], 4) if val_ploss_history[best_idx] is not None else None)
        best_checkpoint["final_value_loss"]  = round(value_history[best_idx], 4)
        best_checkpoint["final_points_loss"] = round(points_history[best_idx], 4)
        best_checkpoint["final_value_val_loss"] = (
            round(val_vloss_history[best_idx], 4) if val_vloss_history[best_idx] is not None else None)
        best_checkpoint["final_points_val_loss"] = (
            round(val_pointsloss_history[best_idx], 4) if val_pointsloss_history[best_idx] is not None else None)
        best_checkpoint["final_value_val_r2"] = (
            round(val_value_r2_history[best_idx], 4) if val_value_r2_history[best_idx] is not None else None)
        best_checkpoint["final_points_val_r2"] = (
            round(val_points_r2_history[best_idx], 4) if val_points_r2_history[best_idx] is not None else None)
        # Task #28: rein informativ am selben best_idx, siehe Kommentar oben.
        best_checkpoint["final_opp_points_loss"] = (
            round(opp_points_history[best_idx], 4) if best_idx < len(opp_points_history) else None)
        best_checkpoint["final_opp_points_val_loss"] = (
            round(val_opp_pointsloss_history[best_idx], 4)
            if best_idx < len(val_opp_pointsloss_history) and val_opp_pointsloss_history[best_idx] is not None
            else None)
        best_checkpoint["final_opp_points_val_r2"] = (
            round(val_opp_points_r2_history[best_idx], 4)
            if best_idx < len(val_opp_points_r2_history) and val_opp_points_r2_history[best_idx] is not None
            else None)
        # Task #34: rein informativ am selben best_idx, siehe Kommentar oben.
        best_checkpoint["final_value_val_brier"] = (
            round(val_brier_history[best_idx], 4)
            if best_idx < len(val_brier_history) and val_brier_history[best_idx] is not None
            else None)
        # Task #35b: rein informativ am selben best_idx, siehe Kommentar oben.
        best_checkpoint["final_ranking_loss"] = (
            round(ranking_loss_history[best_idx], 4) if best_idx < len(ranking_loss_history) else None)
        best_checkpoint["final_ranking_val_acc"] = (
            round(val_ranking_acc_history[best_idx], 4)
            if best_idx < len(val_ranking_acc_history) and val_ranking_acc_history[best_idx] is not None
            else None)
        best_version_name = f"{version_name}_best"
        best_save_path = MODELS_DIR / f"alphazero_{best_version_name}.pth"
        torch.save(best_checkpoint, str(best_save_path))
        print(f"⭐ Bestes Modell (Epoche {best_epoch}, {best_checkpoint['selected_by']}="
              f"{best_combined_metric:.4f}) zusätzlich gespeichert unter:\n📂 {best_save_path}")
    elif best_state_dict is not None:
        print(f"ℹ️  Letzte Epoche ({actual_epochs}) war bereits die beste — kein separater Best-Checkpoint nötig.")

    # Task #34 Audit: VALUE-optimalen Checkpoint (`_brierbest`) speichern, nur
    # falls er weder mit dem finalen noch mit dem val_combined-besten Stand
    # zusammenfaellt (sonst waere er ein Duplikat).
    brierbest_version_name = None
    if (best_brier_state_dict is not None
            and best_brier_epoch not in (actual_epochs, best_epoch)):
        bb_idx = best_brier_epoch - 1
        bb_checkpoint = dict(checkpoint)
        bb_checkpoint["model_state"] = best_brier_state_dict
        bb_checkpoint["epochs"] = best_brier_epoch
        bb_checkpoint["is_best_checkpoint"] = True
        bb_checkpoint["selected_by"] = "val_brier(value-optimal, Task #34 Audit)"
        bb_checkpoint["final_policy_val_loss"] = (
            round(val_ploss_history[bb_idx], 4)
            if bb_idx < len(val_ploss_history) and val_ploss_history[bb_idx] is not None else None)
        bb_checkpoint["final_value_val_brier"] = round(best_brier_metric, 4)
        brierbest_version_name = f"{version_name}_brierbest"
        bb_save_path = MODELS_DIR / f"alphazero_{brierbest_version_name}.pth"
        torch.save(bb_checkpoint, str(bb_save_path))
        print(f"🎯 Value-optimales Modell (Epoche {best_brier_epoch}, val_brier={best_brier_metric:.4f}) "
              f"zusätzlich gespeichert unter:\n📂 {bb_save_path}")

    if plot is not None:
        try:
            plot_path = MODELS_DIR / f"alphazero_{version_name}_loss.png"
            plot["fig"].savefig(str(plot_path))
            print(f"📈 Loss-Verlauf gespeichert unter:\n📂 {plot_path}")
        except Exception as e:
            print(f"⚠️  Loss-Plot konnte nicht gespeichert werden: {e}")

    # 7. ONNX direkt mitexportieren (Rust-Inferenz für Self-Play/Arena), damit
    #    kein manueller export_onnx.py-Schritt nötig ist.
    try:
        from export_onnx import export
        export(version_name)
    except Exception as e:
        print(f"⚠️  ONNX-Export übersprungen (manuell nachholbar: python export_onnx.py --version {version_name}): {e}")
    if best_version_name is not None:
        try:
            from export_onnx import export
            export(best_version_name)
        except Exception as e:
            print(f"⚠️  ONNX-Export (Best) übersprungen "
                  f"(manuell nachholbar: python export_onnx.py --version {best_version_name}): {e}")
    if brierbest_version_name is not None:
        try:
            from export_onnx import export
            export(brierbest_version_name)
        except Exception as e:
            print(f"⚠️  ONNX-Export (Brierbest) übersprungen "
                  f"(manuell nachholbar: python export_onnx.py --version {brierbest_version_name}): {e}")

    # 8. Modell-Snapshot ins OneDrive-Backup (Nutzer-Entscheid 2026-07-24 nach
    #    dem models/-Datenverlust: ereignisgesteuert nach JEDEM Training statt
    #    nur zeitgesteuert). Scheitert leise mit Warnung — ein Backup-Problem
    #    darf nie ein fertiges Training entwerten.
    if snapshot:
        _snapshot_models_to_backup(version_name)
    else:
        print("💾 Modell-Snapshot uebersprungen (--no-snapshot): fuer Ablations-/Sweep-Laeufe, "
              "deren Checkpoints per --seed reproduzierbar und keine Champions sind. "
              "Ein Snapshot je Lauf zippt den GESAMTEN models/-Ordner (>140 MB).")

    # 9. Laufzeit ins Manifest (CLAUDE.md, Nutzer-Anweisung 2026-08-25). Bis
    #    dahin hielt es nur den START-Zeitstempel; die Dauer stand allein auf
    #    stdout. `datenaufbau_s` ist hier eigens getrennt, weil genau dieser
    #    Teil am 2026-08-25 ueber eine Stunde ohne Fortschrittsausgabe lief und
    #    niemand sagen konnte, ob er arbeitet oder haengt.
    from train_manifest import append_train_laufzeit
    append_train_laufzeit(version_name, _run_timestamp, {
        "wanduhr_s": round(time.time() - _t_start_train, 1),
        "cpu_s": round(time.process_time(), 1),
        "datenaufbau_s": round(_t_daten_fertig - _t_start_train, 1)
        if _t_daten_fertig is not None else None,
        "threads": torch.get_num_threads(),
        "device": str(device),
        "epochen": epoch_count_done,
        "samples": len(dataset) if dataset is not None else None,
    })


def _snapshot_models_to_backup(version_name: str) -> None:
    """Zippt den kompletten models/-Ordner als datierten, nach dem Training
    benannten Snapshot nach <OneDrive>\\Backups\\mosaic-AI\\models_snapshots\\."""
    try:
        import os
        import shutil
        from datetime import datetime
        onedrive = os.environ.get("OneDrive")
        if not onedrive:
            print("⚠️  Modell-Snapshot übersprungen: OneDrive-Umgebungsvariable nicht gesetzt.")
            return
        snap_dir = Path(onedrive) / "Backups" / "mosaic-AI" / "models_snapshots"
        snap_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
        target = snap_dir / f"models_{stamp}_{version_name}"
        archive = shutil.make_archive(str(target), "zip", str(MODELS_DIR))
        size_mb = os.path.getsize(archive) / 1e6
        print(f"💾 Modell-Snapshot gesichert: {archive} ({size_mb:.0f} MB)")
    except Exception as e:
        print(f"⚠️  Modell-Snapshot fehlgeschlagen (Training davon unberührt): {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trainiere das Mosaic-AI Neuronale Netz")
    parser.add_argument("--name", type=str, required=True, help="Name der neuen Version, z.B. v2")
    parser.add_argument("--load", type=str, default=None, help="Name der alten Version für Warm Start, z.B. v1")
    parser.add_argument("--epochs", type=int, default=15, help="Wieviele Epochen")
    parser.add_argument("--hidden", type=int, default=None, help="Hidden Layer Größe (Standard: aus config.py)")
    parser.add_argument("--no-early-stop", action="store_true", help="Early Stopping deaktivieren")
    parser.add_argument("--select-by-brier", action="store_true",
                        help="Checkpoint-Auswahl: Brier statt roher Value-Loss im kombinierten Mass (Task #34 -- noetig bei --value-head wdl, sonst waehlt die Auswahl einen praktisch untrainierten frischen Kopf). Default AUS = byte-identisch.")
    parser.add_argument("--wdl-label-smooth", type=float, default=0.0,
                        help="Erosions-Arm A: Label-Smoothing eps auf dem harten WDL-Ziel "
                             "(1 -> 1-eps/2, 0 -> eps/2) -- testet die Memorisierungs-Hypothese. "
                             "Nur zusammen mit --wdl-hard-only. Default 0 = byte-identisch.")
    parser.add_argument("--wdl-bootstrap-destretch", action="store_true",
                        help="Erosions-Arm B: entstaucht den Bootstrap-Anteil des values_wdl-Blends "
                             "per Platt-Streckung (Champion-Fit A/B, siehe --destretch-a/-b) -- "
                             "macht den Stabilisator sauber, ohne Cache-Neubau (bv wird aus "
                             "values_wdl + wdl_outcome rekonstruiert). Nicht mit --wdl-hard-only "
                             "kombinieren. Default AUS = byte-identisch.")
    parser.add_argument("--destretch-a", type=float, default=0.0051,
                        help="Platt-A fuer --wdl-bootstrap-destretch (Default: v19_2d_best-Fit, value_calibration_fit.json 'full').")
    parser.add_argument("--destretch-b", type=float, default=1.9269,
                        help="Platt-B fuer --wdl-bootstrap-destretch (Default: v19_2d_best-Fit).")
    parser.add_argument("--wdl-hard-only", action="store_true",
                        help="Task #34 Audit: WDL-Ziel = ROHER Ausgang (`wdl_outcome`) statt TD-geblendetes "
                             "`values_wdl` -- der Blend-Anteil (bootstrap_value) stammt aus Alt-Netz-Suchen "
                             "(tanh-Kopf, B~1,9) und traegt die gestauchte Alt-Semantik ins neue Ziel. "
                             "Nur zusammen mit --value-head wdl sinnvoll. Default AUS = byte-identisch.")
    parser.add_argument("--no-plot", action="store_true",
                        help="Live-Loss-Plot deaktivieren (z.B. ohne Display)")
    parser.add_argument("--val-frac", type=float, default=0.1,
                        help="Anteil der Spiele-DATEIEN (nicht Züge), der als Val-Split nie "
                             "trainiert wird (Standard: 0.1). 0 deaktiviert den Split.")
    parser.add_argument("--train-file-limit", type=int, default=None,
                        help="Begrenzt die TRAININGS-Dateien (nach Abzug des Val-Splits) auf N "
                             "(Daten-Skalierungs-Ablation, Task #69). Val-Split bleibt unveraendert "
                             "identisch zu einem Lauf ohne dieses Flag.")
    parser.add_argument("--extra-data-dir", type=str, default=None,
                        help="Zusaetzliches Datenverzeichnis, ADDITIV zu DATA_DIR (*.pkl, NICHT "
                             "rekursiv, gleiche Lade-Konvention wie das Standard-Fenster) -- fuer "
                             "Korpora ausserhalb von data/ (z.B. data/ownership_corpus/, siehe "
                             "PREREG_ownership_corpus.md §1: das Standard-Fenster laedt "
                             "Unterordner nicht). Default leer = byte-identisches Bestandsverhalten "
                             "(Task-#28-Muster).")
    parser.add_argument("--lr", type=float, default=None,
                        help="Start-Learning-Rate fuer Adam (Standard: LEARNING_RATE aus config.py, "
                             "aktuell 0.0004). Task #77 (v12b_lr): Warm-Start-Feintuning-Kontrolle "
                             "mit niedrigerer Start-LR.")
    parser.add_argument("--no-snapshot", action="store_true",
                        help="Den OneDrive-Modell-Snapshot nach dem Training auslassen. "
                             "Gedacht fuer Ablations-/Seed-Sweep-Laeufe: der Hook zippt den "
                             "GESAMTEN models/-Ordner (>140 MB) je Lauf, was bei einem Sweep "
                             "mehrere GB fast identischer Archive erzeugt. Fuer echte "
                             "Generationen NICHT setzen -- der Hook ist die Absicherung nach "
                             "dem models/-Datenverlust vom 2026-07-24.")
    parser.add_argument("--seed", type=int, default=None,
                        help="Seed fuer Gewichts-Init und Batch-Shuffling. Default None = "
                             "altes, unseeded Verhalten. Zwei Arme eines A/B mit DEMSELBEN "
                             "Seed unterscheiden sich allein durch die getestete Aenderung "
                             "-- ohne Seed vermischt sich der Effekt mit der Lauf-zu-Lauf-"
                             "Varianz (die in diesem Projekt bis 2026-07-28 nie gemessen wurde).")
    parser.add_argument("--freeze-trunk", action="store_true",
                        help="Trunk und ALLE Koepfe ausser ownership_head einfrieren "
                             "(requires_grad=False + BatchNorm-Riegel) und die Checkpoint-"
                             "Auswahl auf den Ownership-Val-Verlust umstellen. Loest den "
                             "Zielkonflikt aus PREREG_ownership_corpus.md §10.3 (best=Ep.1 mit "
                             "untrainiertem Kopf vs. final=Ep.15 mit ueberangepasster Policy). "
                             "Verlangt --load, --ownership-weight > 0 und --val-frac > 0. "
                             "Details/Zusicherung: freeze_trunk.py, PREREG_frozen_trunk_head.md.")
    parser.add_argument("--reinit-points-head", action="store_true",
                        help="Den points_head beim Warm-Start NEU initialisieren statt ihn zu "
                             "uebernehmen. Fairer Kontrollarm zu --points-dist-bins: der "
                             "Verteilungs-Kopf kann nicht warm starten (andere Ausgabebreite), "
                             "ein Vergleich gegen einen warm gestarteten Skalar-Kopf vermischt "
                             "sonst 'Verteilung vs Skalar' mit 'frisch vs warm'.")
    parser.add_argument("--points-dist-bins", type=int, default=None,
                        help="Task #12: Anzahl Bins fuer den DISTRIBUTIONALEN Punkte-Kopf. "
                             "0 = aus (Skalar-Regression, Standard). Typisch 51 (C51). Der Kopf "
                             "sagt dann eine Verteilung der tanh-gestauchten Punktedifferenz "
                             "vorher und wird per Kreuzentropie gegen ein HL-Gauss-geglaettetes "
                             "Ziel trainiert; nach aussen wird weiterhin der ERWARTUNGSWERT als "
                             "Skalar ausgegeben, die ONNX-Schnittstelle out[0..3] bleibt also "
                             "unveraendert. ACHTUNG: warm-gestartete points_head-Gewichte passen dann nicht mehr (Shape-Mismatch) und starten frisch -- die Warnung dazu ist erwuenscht.")
    parser.add_argument("--conjunction-head", action="store_true",
                        help="Erweitert den Ownership-Kopf um die KONJUNKTIVEN Wertungskriterien "
                             "(25 je Spieler, 50 gesamt): 6 Reihen + 6 Spalten + 2 Diagonalen + "
                             "4 Eckplatten + 1 Jokerfeld-Konjunktion + 6 farbenreiche Reihen. "
                             "Der Ownership-Randlayer deckt die ADDITIVEN Kriterien 4 und 6 "
                             "bereits exakt ab (Summe der Feldwahrscheinlichkeiten = Erwartungswert); "
                             "die konjunktiven lassen sich daraus NICHT ableiten und brauchen je "
                             "einen eigenen Ausgang. Labels sind gratis aus dem Endbrett. "
                             "Eigener Cache-Key-Suffix '+conj_v1' (kein VALUE_SCHEMA_VERSION-Bump). "
                             "Wirkt nur zusammen mit --ownership-weight > 0 -- die Konjunktionen "
                             "haengen am selben Verlustterm.")
    parser.add_argument("--ownership-weight", type=float, default=None,
                        help="Task #9: Gewicht des Ownership-Hilfsziels (72 Binaerlabels je "
                             "Position: wird dieses Kuppelfeld am SPIELENDE belegt sein?). "
                             "Standard OWNERSHIP_WEIGHT aus config.py (aktuell 0.0 = Kopf aus, "
                             "Bestandsverhalten byte-identisch). Motivation: der beste "
                             "Checkpoint lag bei v15/v16/v17 stets bei Epoche 1-3, dem Netz "
                             "fehlt lernbares Signal pro Sample, nicht Sample-Anzahl -- dieser "
                             "Kopf liefert 72 Gradienten statt eines Skalars. Zielbalance "
                             "gemessen 41/59.")
    parser.add_argument("--exclude-round5", action="store_true",
                        help="Task #15 B: Runde-5-Samples komplett aus Value-, Points- UND "
                             "Policy-Loss nehmen (Training UND Validierung, damit die "
                             "Checkpoint-Auswahl konsistent ist). Begruendung: das Netz wird "
                             "in Runde 5 nie konsultiert -- net_mcts.rs:2265 bypassed den "
                             "Suchpfad zu round5::choose_action (exakte Alpha-Beta-Suche), "
                             "und der Runde-4-Bootstrap nutzt round5::exact_round5_outcome. "
                             "~17%% der Value- und ~15%% der Policy-Samples liegen dort.")
    parser.add_argument("--lr-schedule", type=str, default="none", choices=["none", "cosine", "plateau"],
                        help="LR-Verlauf ueber die Epochen. 'none' (Standard): konstante LR wie bisher. "
                             "'cosine': CosineAnnealingLR mit T_max=--lr-t-max, ersatzweise --epochs "
                             "(ACHTUNG: bei zu grossem --epochs regelt er faktisch nicht ab -- dann "
                             "--lr-t-max setzen). 'plateau': ReduceLROnPlateau (factor 0.5, patience 2) "
                             "-- adaptiv, fuer Laeufe mit unbekanntem Saettigungspunkt.")
    parser.add_argument("--lr-t-max", type=int, default=None,
                        help="Anneal-Horizont fuer --lr-schedule cosine (T_max in Epochen). "
                             "Ungesetzt (Default): T_max = --epochs, bestandsidentisch. ANLASS: mit "
                             "Early Stopping (Patience 5) endet ein Lauf meist weit vor --epochs, und "
                             "T_max=--epochs heisst dann faktisch konstante LR -- bei --epochs 100 und "
                             "Stopp bei Epoche 15 steht die LR noch bei 94,6%% der Start-LR (Faktor "
                             "(1+cos(pi*t/T_max))/2). Mit diesem Flag wird der Anneal-Horizont auf den "
                             "ERWARTETEN Stopp-Horizont gesetzt, unabhaengig vom Epochen-Deckel. "
                             "Landet als Feld 'lr_t_max' im Trainings-Manifest.")
    parser.add_argument("--value-weight", type=float, default=None,
                        help="Gewicht des Value-Aux-Loss im Gesamt-Loss (Standard: VALUE_WEIGHT aus "
                             "config.py, aktuell 0.2). Task #79 (v12d): VALUE_WEIGHT/POINTS_WEIGHT-Sweep. "
                             "Wirkt nur im Loss/der Checkpoint-Auswahl, nicht im Cache/Targets.")
    parser.add_argument("--points-weight", type=float, default=None,
                        help="Gewicht des Punktestand-Aux-Loss im Gesamt-Loss (Standard: POINTS_WEIGHT "
                             "aus config.py, aktuell 0.5). Siehe --value-weight.")
    parser.add_argument("--value-target-variant", type=str, default="nortv",
                        choices=["default", "nortv", "nortv_r1"],
                        help="Task #84 (rtv-Ablation Phase 1). STANDARD SEIT 2026-07-28: 'nortv' "
                             "(vorher 'default'). Begruendung: v13_nortv_best schlug den Champion "
                             "v12b_lr_best 171:129 allein durch das Weglassen des rtv-Overrides im "
                             "Value-Target, bei zugleich ~3x guenstigerem Self-Play -- und JEDE "
                             "Generation seit v15 wurde ohnehin explizit mit 'nortv' trainiert, der "
                             "alte Default wurde faktisch nie genutzt. Ihn stehen zu lassen war nur "
                             "ein Footgun (Flag vergessen = stillschweigend schlechteres Netz). "
                             "'default' bleibt waehlbar, um Alt-Laeufe byte-identisch zu "
                             "reproduzieren (rtv-Override bevorzugt, wo vorhanden); 'nortv_r1' "
                             "ignoriert den Override nur fuer Runde-1-Zustaende. Aendert den "
                             "HDF5-Cache-Key (siehe corpus_dataset.py::MosaicDataset).")
    parser.add_argument("--value-target-lambda", type=float, default=1.0,
                        help="λ-Misch-Value-Target-Experiment (Willemsen et al. 2021, 'soft-Z' -- "
                             "Varianzreduktion des HAUPT-Value-Targets durch Mischen mit dem "
                             "Root-Suchwert). target = λ*z + (1-λ)*root_q_remapped fuer Samples mit "
                             "geloggtem root_q (Commit 2718b9a, aktuell nur selfplay_v18_*-Dateien), "
                             "sonst bleibt z unveraendert. STANDARD 1.0 = KEIN Mix, byte-identisches "
                             "Bestandsverhalten (values-Tensor bleibt unangetastet). Harte Validierung "
                             "0<=λ<=1 (kein stiller Clamp). Siehe "
                             "corpus_dataset.py::MosaicDataset.apply_value_target_lambda, "
                             "evaluations/PREREG_lambda_target.md. Aendert den HDF5-Cache-Key NICHT "
                             "(root_q ist additiv im Cache, der Mix passiert erst hier). "
                             "KORREKTHEITS-FIX 2026-08-08: bei --value-head wdl mischt dies "
                             "stattdessen 'values_wdl' (Skala [0,1], root_q wird dafuer von [-1,1] "
                             "zurueckgerechnet) -- vorher wirkte λ in dem Fall folgenlos auf "
                             "'values', das der WDL-Kopf gar nicht sieht.")
    parser.add_argument("--opp-points-head", action="store_true",
                        help="Task #28 (PREREG_task28_aggression.md): additiven opp_points_head "
                             "aktivieren (reine GEGNER-Punkteprognose, gleiche Architektur wie der "
                             "skalare points_head, Gewicht=POINTS_WEIGHT, MSE, maskiert wo das "
                             "Cache-Feld 'opp_points_forecast' fehlt/0 ist). STANDARD AUS -- ohne "
                             "dieses Flag byte-identisches Bestandsverhalten (Kopf existiert nicht "
                             "im Modell, kein ONNX-Output 'opp_points'). Der opp-Loss geht NICHT in "
                             "val_combined/die Checkpoint-Auswahl ein (Bestandsmetrik bleibt "
                             "unveraendert vergleichbar mit Alt-Laeufen), nur separat geloggt. "
                             "--load von einem Alt-Checkpoint OHNE diesen Kopf funktioniert "
                             "(fehlende Keys -> frisch initialisiert, Rest warm).")
    parser.add_argument("--endgame-head", action="store_true",
                        help="Schema 18 (evaluations/PREREG_plate_intervention.md): additiven "
                             "endgame_head aktivieren -- MLP auf `shared`, Ziel = exakter R5-"
                             "Wurzelwert (root_q der R5-Drafting-Records, [0,1]-Skala im Cache -> "
                             "Tanh-Remap [-1,1] im Loss), MSE, Gewicht=POINTS_WEIGHT, maskiert mit "
                             "'endgame_mask' (nur R5-Drafting-Zustaende mit geloggtem root_q; Alt-"
                             "Caches/Nicht-R5-Zustaende -> Maske 0). STANDARD AUS -- ohne dieses "
                             "Flag byte-identisches Bestandsverhalten (Kopf existiert nicht im "
                             "Modell, kein ONNX-Output 'endgame_margin'). Der Loss geht NICHT in "
                             "val_combined/die Checkpoint-Auswahl ein (Bestandsmetrik bleibt "
                             "unveraendert vergleichbar mit Alt-Laeufen), nur separat geloggt. "
                             "--load von einem Alt-Checkpoint OHNE diesen Kopf funktioniert "
                             "(fehlende Keys -> frisch initialisiert, Rest warm, gleiches Muster "
                             "wie --opp-points-head).")
    parser.add_argument("--no-head-warmstart", action="store_true",
                        help="Nutzer-Auftrag 2026-08-11: deaktiviert die gezielte Teiluebernahme "
                             "formabweichender Koepfe beim Warm-Start (Standard: AN, siehe "
                             "head_warmstart.py::apply_head_warmstart() fuer beide Faelle/Details). "
                             "Mit diesem Flag: Bestandsverhalten (formabweichende Tensoren werden "
                             "immer zufaellig neu gewuerfelt) -- fuer den A/B 'Warmstart gegen "
                             "Zufall'.")
    parser.add_argument("--encoder", type=str, default="flat", choices=["flat", "2d"],
                        help="Task #11 Phase 2. 'flat' (Standard, Bestandsverhalten byte-identisch): "
                             "MosaicNet auf state_to_tensor (708 Features). '2d': Mosaic2DNet -- "
                             "Conv-Zweig auf state_to_planes ([76,6,6]) + Flach-Zweig auf demselben "
                             "708er-Vektor, spaete Fusion (siehe docs/design_2d_encoder.md). "
                             "Aendert den HDF5-Cache-Key (Suffix '+enc2d_v1', der Flach-Cache derselben "
                             "Dateiliste bleibt unberuehrt). --load erwartet dann einen 2D-Checkpoint "
                             "(harter Fehler bei Encoder-Mismatch statt stillem Teil-Load).")
    parser.add_argument("--value-head", type=str, default="tanh", choices=list(VALUE_HEAD_VARIANTS),
                        help="Task #34 (STATUS.md 'Sieg/Niederlage-Ziel wiederherstellen'). 'tanh' "
                             "(Standard, Bestandsverhalten byte-identisch): Skalar-Regressionskopf, "
                             "MSE auf der weichen Punkte-Marge ('values'). 'wdl': 2-Logit-Softmax-"
                             "Klassifikationskopf, Kreuzentropie mit weichen Labels auf der harten "
                             "Sieg/Niederlage-Wahrscheinlichkeit ('values_wdl') -- `forward()` gibt an "
                             "der BESTEHENDEN Position weiterhin `2*P(Sieg)-1` aus (identische Skala/"
                             "Position, `net_mcts.rs::value_to_win_prob` unveraendert kompatibel, keine "
                             "Rust-Aenderung noetig). Schaltet ZIEL+LOSS+ARCHITEKTUR gemeinsam um. "
                             "ACHTUNG: val_combined ist zwischen 'tanh'- und 'wdl'-Laeufen NICHT "
                             "vergleichbar (andere Loss-Einheit) -- fuer den Arm-Vergleich den "
                             "geloggten/gespeicherten Value-Brier-Score nutzen (arm-uebergreifend "
                             "vergleichbar). Checkpoint speichert die Wahl; "
                             "`build_model_from_checkpoint`/`value_head_variant_from_state` erkennen "
                             "sie rueckwirkend aus dem state_dict, Alt-Checkpoints bleiben unveraendert "
                             "ladbar (gleiches Muster wie --points-dist-bins/--opp-points-head).")
    parser.add_argument("--ranking-loss-weight", type=float, default=0.0,
                        help="Task #35b (Research-Report Idee 7.1, 'Ranking-Loss auf Geschwister-Q'). "
                             "Zusaetzlicher paarweiser RankNet-Stil-Loss auf den Policy-LOGITS: fuer "
                             "Geschwister-Kandidaten (Top-8 Root-Q-Paare je Zustand, "
                             "RANKING_CACHE_FIELDS in neural_net.py) mit klarer Q-Differenz "
                             "(|dq|>0.02) soll der Kandidat mit dem groesseren Suchwert Q auch den "
                             "groesseren Policy-Logit bekommen -- ergaenzt die bestehende Kreuzentropie "
                             "auf der Besuchs-Softmax (die nur die Gesamtverteilung trifft, nicht "
                             "explizit die paarweise Reihenfolge). STANDARD 0.0 = AUS, dann komplett "
                             "uebersprungen (kein neuer Modell-Kopf, kein Gradient, byte-identisches "
                             "Bestandsverhalten). Gewicht multiplikativ ins Gesamt-Loss, geht NICHT in "
                             "val_combined/die Brier-Checkpoint-Auswahl ein -- separat geloggt "
                             "(Trainings-Loss + deskriptive paarweise Val-Ranking-Accuracy). Nur "
                             "nutzbar auf Zuegen mit `pol_w>0` UND geloggtem Geschwister-Set "
                             "(v19wdl/v19wdlann-Sockel-Partien; policy-maskierte Schwarm-Partien tragen "
                             "kein nutzbares Set, Maske dort 0).")

    args = parser.parse_args()

    train(points_dist_bins=args.points_dist_bins, reinit_points_head=args.reinit_points_head,
          version_name=args.name, load_version=args.load, input_epoch=args.epochs,
          hidden_size=args.hidden, early_stop=not args.no_early_stop,
          select_by_brier=args.select_by_brier, wdl_hard_only=args.wdl_hard_only,
          wdl_label_smooth=args.wdl_label_smooth,
          wdl_bootstrap_destretch=args.wdl_bootstrap_destretch,
          destretch_a=args.destretch_a, destretch_b=args.destretch_b,
          show_plot=not args.no_plot, val_frac=args.val_frac,
          train_file_limit=args.train_file_limit, lr=args.lr, lr_schedule=args.lr_schedule,
          lr_t_max=args.lr_t_max,
          exclude_round5=args.exclude_round5, ownership_weight=args.ownership_weight,
          conjunction_head=args.conjunction_head,
          seed=args.seed, snapshot=not args.no_snapshot,
          value_weight=args.value_weight, points_weight=args.points_weight,
          value_target_variant=args.value_target_variant, encoder=args.encoder,
          value_target_lambda=args.value_target_lambda, opp_points_head=args.opp_points_head,
          endgame_head=args.endgame_head,
          value_head=args.value_head,
          ranking_loss_weight=args.ranking_loss_weight,
          head_warmstart=not args.no_head_warmstart, extra_data_dir=args.extra_data_dir,
          freeze_trunk=args.freeze_trunk)
