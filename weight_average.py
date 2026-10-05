# -*- coding: utf-8 -*-
"""weight_average.py -- Gewichtsmittelung der Epochen-Staende fuer train.py (`--weight-average`).

Herkunft: PREREG_v35_window.md par.16 (Arm v35-b08), Research E5
(RESEARCH_evaluator_architecture_external_2026-09-25.md Z. 469-490): statt des
Brier-besten Einzelstands ein gemitteltes Netz ueber die Epochen-Schnappschuesse
(KataGo: EMA mit decay 0,75; SWA nach Izmailov 2018). Ausgelagert aus train.py
nach dem Muster von freeze_trunk.py / head_warmstart.py (Modularitaetsregel,
Groessen-Ratsche tools/check_conventions.py Regel 1).

Bei `--weight-average none` (Default) ruft train.py aus diesem Modul nur
`validate_weight_average_args` auf; alles andere bleibt unbenutzt, der Bestand
laeuft byte-gleich.

Bausteine:

1. `validate_weight_average_args` -- harte Vorab-Validierung VOR dem teuren
   Datenaufbau (Muster `validate_freeze_args`).
2. `WeightAverager` -- fuehrt das gemittelte Parameterset als eigenes
   Modellobjekt (Kopie des Trainingsmodells). Gemittelt werden alle
   Gleitkomma-Eintraege des `state_dict`, also Parameter UND Buffer
   (BN-`running_mean`/`running_var`); `num_batches_tracked` und andere
   Ganzzahl-Buffer werden vom aktuellen Stand uebernommen, nicht gemittelt.
3. `recompute_bn_stats` -- BN-Neuschaetzung am Ende auf dem gemittelten Netz,
   inhaltlich dasselbe Verfahren wie `torch.optim.swa_utils.update_bn`
   (Ruecksetzen, momentum=None = kumulatives Mittel, Vorwaertslauf im
   train-Modus ohne Gradienten). Eigener Nachbau statt `update_bn`, weil
   `update_bn` aus einem Tupel-Batch nur das ERSTE Element als Eingabe nimmt;
   das 2D-Netz braucht zwei Eingaben (Ebenen plus Zustandsvektor), und der
   Cache liefert sie bitgepackt.
4. `copy_bn_stats` -- Rueckfall, falls die Neuschaetzung scheitert: die
   BN-Statistik des letzten Epochenstands wird uebernommen (Manifest
   `bn_stats: "last_epoch"`).
5. `preserved_rng` -- Kontextmanager um die ZUSAETZLICHE Validierung des
   gemittelten Stands. Jeder Durchlauf eines DataLoaders zieht beim Anlegen
   des Iterators einen Basis-Seed aus dem globalen torch-RNG
   (torch/utils/data/dataloader.py, `_BaseDataLoaderIter.__init__`,
   `_base_seed = ... .random_(generator=loader.generator)`), auch mit
   SequentialSampler. Ohne Sicherung verschoebe die zweite Validierung je
   Epoche die Shuffle-Folge aller folgenden Trainingsepochen, und der
   Einzelstand-Verlauf eines EMA-Laufs wiche vom selben Rezept ohne Knopf ab;
   die Prereg-Zuordnung "ein Unterschied zu b02 gehoert der Mittelung"
   verlangt aber denselben Trainingspfad.

Kosten (HERLEITUNG, nicht gemessen): je gemittelter Epoche eine zusaetzliche
Validierung (Vorwaertslauf ueber den Val-Split, rund ein Zehntel der Zuege
einer Trainingsepoche ohne Rueckwaertslauf), dazu am Ende EIN Vorwaertslauf
ueber den Trainingsanteil fuer die BN-Neuschaetzung und eine Schluss-
Validierung. Groessenordnung: rund +10 Prozent Trainingszeit.
"""
from __future__ import annotations

import contextlib
import copy
import random
import sys

import torch

WEIGHT_AVERAGE_MODES = ("none", "ema", "swa")
DEFAULT_WEIGHT_AVERAGE_DECAY = 0.75
DEFAULT_WEIGHT_AVERAGE_FROM_EPOCH = 2


def validate_weight_average_args(mode: str, decay: float, from_epoch: int,
                                 epochs: int | None, freeze_trunk: bool) -> None:
    """Harte Vorab-Validierung; kein stiller Rueckfall auf einen anderen Modus."""
    if mode not in WEIGHT_AVERAGE_MODES:
        sys.exit(f"❌ --weight-average {mode!r} unbekannt -- erlaubt: {WEIGHT_AVERAGE_MODES}.")
    if mode == "none":
        return
    if mode == "ema" and not (0.0 <= decay < 1.0):
        sys.exit(f"❌ --weight-average-decay {decay!r} ausserhalb [0, 1) -- Abbruch "
                 f"(1,0 hiesse: der erste gemittelte Stand bleibt fuer immer stehen).")
    if from_epoch < 1:
        sys.exit(f"❌ --weight-average-from-epoch {from_epoch!r} < 1 -- Epochen zaehlen ab 1.")
    if epochs is not None and from_epoch > epochs:
        sys.exit(f"❌ --weight-average-from-epoch {from_epoch} > --epochs {epochs}: es entstuende "
                 f"kein gemittelter Stand -- Abbruch.")
    if freeze_trunk:
        # Der BN-Riegel von freeze_trunk.py ueberschreibt `model.train` auf der
        # INSTANZ; eine Kopie davon und die BN-Neuschaetzung am Ende wuerden
        # genau die eingefrorene Trunk-Statistik verschieben, die der Riegel
        # schuetzt. Bis jemand das braucht: nicht kombinierbar.
        sys.exit("❌ --weight-average und --freeze-trunk sind nicht kombinierbar.")


class WeightAverager:
    """Gemittelter Stand ueber die Epochen-Schnappschuesse ab `from_epoch`.

    ema: avg = decay * avg + (1 - decay) * aktuell
    swa: gleichgewichtetes Mittel, avg += (aktuell - avg) / (n + 1)
    Der ERSTE gemittelte Schnappschuss (Epoche `from_epoch`) wird in beiden
    Modi unveraendert uebernommen (Startwert des Mittels).
    """

    def __init__(self, mode: str, decay: float, from_epoch: int):
        self.mode = mode
        self.decay = float(decay)
        self.from_epoch = int(from_epoch)
        self.n_averaged = 0
        self.averaged_epochs: list[int] = []
        self.model = None  # angelegt beim ersten Mitteln (spart Speicher davor)

    def _ensure_model(self, model) -> None:
        if self.model is None:
            self.model = copy.deepcopy(model)
            for p in self.model.parameters():
                p.requires_grad_(False)

    def update(self, model, epoch: int) -> bool:
        """Nimmt den Stand nach Epoche `epoch` (1-basiert) ins Mittel; False vor `from_epoch`."""
        if epoch < self.from_epoch:
            return False
        self._ensure_model(model)
        src = model.state_dict()
        with torch.no_grad():
            # `state_dict()` liefert abgetrennte Tensoren auf DENSELBEN Speicher
            # wie die Parameter/Buffer -- In-place-Operationen wirken also direkt
            # auf das gemittelte Modell.
            for key, dst in self.model.state_dict().items():
                cur = src[key].detach()
                if (self.n_averaged == 0 or key.endswith("num_batches_tracked")
                        or not dst.is_floating_point()):
                    dst.copy_(cur)
                elif self.mode == "ema":
                    dst.mul_(self.decay).add_(cur, alpha=1.0 - self.decay)
                else:  # swa
                    dst.add_(cur - dst, alpha=1.0 / (self.n_averaged + 1))
        self.n_averaged += 1
        self.averaged_epochs.append(int(epoch))
        return True

    def state(self) -> dict:
        """Fuer den Zwischenstand (`--resume`): Mittel plus Zaehler, auf der CPU."""
        return {
            "mode": self.mode, "decay": self.decay, "from_epoch": self.from_epoch,
            "n_averaged": self.n_averaged, "averaged_epochs": list(self.averaged_epochs),
            "model_state": (None if self.model is None else
                            {k: v.detach().cpu().clone() for k, v in self.model.state_dict().items()}),
        }

    def load_state(self, state: dict | None, model, device) -> None:
        """Gegenstueck zu `state()`; harter Abbruch, wenn der Zwischenstand kein Mittel traegt."""
        if state is None:
            sys.exit("❌ --resume: der Zwischenstand traegt keinen gemittelten Stand "
                     "(--weight-average), der Fingerabdruck verlangt aber einen -- Abbruch.")
        for key in ("mode", "decay", "from_epoch"):
            if state[key] != getattr(self, key):
                sys.exit(f"❌ --resume: weight_average {key}: Zwischenstand={state[key]!r} "
                         f"jetzt={getattr(self, key)!r} -- Abbruch.")
        self.n_averaged = int(state["n_averaged"])
        self.averaged_epochs = list(state["averaged_epochs"])
        if state["model_state"] is not None:
            self._ensure_model(model)
            self.model.load_state_dict({k: v.to(device) for k, v in state["model_state"].items()})

    def cpu_state_dict(self) -> dict:
        return {k: v.detach().cpu().clone() for k, v in self.model.state_dict().items()}


def _bn_modules(model) -> list:
    return [m for m in model.modules() if isinstance(m, torch.nn.modules.batchnorm._BatchNorm)]


def recompute_bn_stats(model, loader, inputs_from_batch) -> int:
    """BN-Statistik von `model` ueber `loader` neu schaetzen (Verfahren von
    `torch.optim.swa_utils.update_bn`). `inputs_from_batch(batch)` liefert das
    Tupel der Netz-Eingaben. Gibt die Zahl der gelaufenen Batches zurueck."""
    bns = _bn_modules(model)
    if not bns:
        return 0
    momenta = {}
    for m in bns:
        m.reset_running_stats()
        momenta[m] = m.momentum
        m.momentum = None
    was_training = model.training
    model.train()
    n = 0
    try:
        with torch.no_grad():
            for batch in loader:
                model(*inputs_from_batch(batch))
                n += 1
    finally:
        for m in bns:
            m.momentum = momenta[m]
        model.train(was_training)
    return n


def copy_bn_stats(src_model, dst_model) -> None:
    """Rueckfall: BN-Buffer (running_mean/var, num_batches_tracked) von `src_model` uebernehmen."""
    with torch.no_grad():
        for s, d in zip(_bn_modules(src_model), _bn_modules(dst_model)):
            if s.running_mean is not None:
                d.running_mean.copy_(s.running_mean)
                d.running_var.copy_(s.running_var)
            if s.num_batches_tracked is not None:
                d.num_batches_tracked.copy_(s.num_batches_tracked)


@contextlib.contextmanager
def preserved_rng():
    """Globalen torch-, CUDA- und Python-RNG um einen Block herum sichern und zuruecksetzen."""
    cpu_state = torch.get_rng_state()
    cuda_state = torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None
    py_state = random.getstate()
    try:
        yield
    finally:
        torch.set_rng_state(cpu_state)
        if cuda_state is not None:
            torch.cuda.set_rng_state_all(cuda_state)
        random.setstate(py_state)
