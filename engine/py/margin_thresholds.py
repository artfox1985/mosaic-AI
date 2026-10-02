# -*- coding: utf-8 -*-
"""E2-Arm: Margen-Schwellen am WDL-Logit (Proportional-Odds-Zusatzverlust).

Registriert in `evaluations/PREREG_evaluator_pretests.md` par.4 (Leser (b)) und
par.8a (Vortest bestanden, Brier(a) - Brier(b) = +0,00213), Arm in
`evaluations/PREREG_v34_window.md` par.3. KEIN neuer Kopf (Nutzer 2026-09-14,
par.1 der Vortest-Prereg: "E2 sind Verlustterme am bestehenden WDL-Logit").

DER GEMEINSAME LOGIT z ist die Differenz der beiden WDL-Logits,
`z = logits[:, 1] - logits[:, 0]`: das Netz liest P(Sieg) als
`softmax(logits)[:, 1] = sigmoid(z)` (neural_net.py, `Mosaic2DNet.forward`,
`p_win = torch.softmax(value_wdl_logits, dim=-1)[:, 1:2]`), und train.py
trainiert den Wertverlust schon heute als BCE auf genau diesem z
(`_train_one_epoch`, `logit_diff`). Ein Softmax ueber zwei Logits haengt nur
von ihrer Differenz ab; z ist also DER Logit des Kopfs, kein Hilfskonstrukt.

DAS MODELL (wie der Vortest-Leser, tools/probes/evaluator_pretests.py
`fit_prop_odds`):
    P(Marge > t) = sigmoid(z - t / s_r),  t in {-10, -5, +5, +10} Punkte,
    s_r > 0 je Runde r = 1..5 (Skala in Punkten je Logit-Einheit).
Ziel je Schwelle `1[Marge > t]` (strikt, wie im Leser). OHNE die Schwelle 0
(Nutzer 2026-10-02: *"ohne die 0, wie im urspruenglichen Vorschlag"*,
RESEARCH_evaluator_architecture_external_2026-09-25.md E2): ein t = 0-Term waere
sigmoid(z) gegen den harten Ausgang und legte zusaetzliches Gewicht auf das
Sieg/Niederlage-Ziel, das der Wertverlust ohnehin traegt; E2 waere damit mit einem
Hard-Outcome-Effekt vermengt.

LERNBARE SKALARE: nur `log_scale` (5 Werte, einer je Runde; Startwert ln 10 wie
im Leser). Sie gehoeren NICHT zum Modell: der Export, die Suche und jeder
Checkpoint bleiben unveraendert; train.py fuehrt sie als eigene Parametergruppe
im Optimizer und schreibt ihren Stand ins Manifest.
"""
from __future__ import annotations

import math

import torch
import torch.nn.functional as F

# par.4: fest registriert, Punkte auf die Endmarge. Eine Aenderung geht zuerst
# in die Prereg.
MARGIN_THRESHOLDS = (-10.0, -5.0, 5.0, 10.0)
NUM_ROUNDS = 5
# Startwert der Skala wie im Vortest-Leser (`log_s = log(10)`).
INITIAL_SCALE_POINTS = 10.0


def initial_log_scale(device=None) -> torch.Tensor:
    """Startwerte der fuenf Rundenskalen als lernbarer Parameter (Blatt-Tensor)."""
    return torch.nn.Parameter(
        torch.full((NUM_ROUNDS,), math.log(INITIAL_SCALE_POINTS), dtype=torch.float32,
                   device=device))


def margin_threshold_targets(wdl_outcome: torch.Tensor, final_margin: torch.Tensor):
    """Ziele (B, 4) und Gueltigkeitsmaske (B,) bool.

    `wdl_outcome`: 1 = Sieg des Ziehers, 0 = Niederlage, -1 = unbekannt.
    `final_margin`: rohe Endmarge in Punkten aus Sicht des Ziehers, NaN = unbekannt.
    Gueltig ist ein Zustand nur mit bekanntem Ausgang UND endlicher Marge.
    """
    y = wdl_outcome.reshape(-1).float()
    m = final_margin.reshape(-1).float()
    valid = (y >= 0.0) & torch.isfinite(m)
    t = torch.tensor(MARGIN_THRESHOLDS, dtype=m.dtype, device=m.device)
    # NaN > t ist False; solche Zeilen sind ohnehin maskiert.
    targets = (m.unsqueeze(1) > t.unsqueeze(0)).to(m.dtype)
    return targets, valid


def margin_threshold_loss(logit_diff: torch.Tensor, wdl_outcome: torch.Tensor,
                          final_margin: torch.Tensor, rounds: torch.Tensor,
                          log_scale: torch.Tensor, sample_weight: torch.Tensor | None = None):
    """Mittlere Proportional-Odds-BCE ueber die vier Schwellen.

    Rueckgabe `(loss, weight_sum)`: `loss` ist ein Skalar-Tensor (0 bei keinem
    gueltigen Zustand, endlich und differenzierbar), `weight_sum` die Summe der
    Gewichte gueltiger Zustaende als Python-Zahl (fuer Epochenmittel).

    `rounds`: Rundennummer je Zustand (Cache-Feld `rounds`), auf 1..5 geklemmt
    wie im Leser (Start-Records ohne Runde zaehlen zu Runde 1).
    `sample_weight`: optional (B,), z. B. die `--exclude-round5`-Maske.
    """
    targets, valid = margin_threshold_targets(wdl_outcome, final_margin)
    z = logit_diff.reshape(-1)
    t = torch.tensor(MARGIN_THRESHOLDS, dtype=z.dtype, device=z.device)
    r = rounds.reshape(-1).long().clamp(1, NUM_ROUNDS) - 1
    scale = torch.exp(log_scale)[r]                                   # (B,)
    logits = z.unsqueeze(1) - t.unsqueeze(0) / scale.unsqueeze(1)     # (B, 4)
    per_sample = F.binary_cross_entropy_with_logits(
        logits, targets.to(z.dtype), reduction="none").mean(dim=1)    # (B,)
    w = valid.to(z.dtype)
    if sample_weight is not None:
        w = w * sample_weight.reshape(-1).to(z.dtype)
    w_sum = w.sum()
    loss = (per_sample * w).sum() / w_sum.clamp(min=1e-6)
    return loss, float(w_sum.item())
