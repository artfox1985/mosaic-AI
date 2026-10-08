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

6. Auswahl des gespeicherten Stands (`--weight-average-select`, PREREG_v35_window.md
   par.16b, Arm v35-b08b): `final` (Default, Bestand) speichert das Mittel nach
   der letzten Epoche; `brierbest` haelt nach jeder Epochen-Validierung des
   Mittels eine CPU-Kopie des gemittelten `state_dict` fest, sobald dessen
   Val-Brier STRENG unter dem bisher besten liegt (erstes Minimum, dieselbe
   Regel wie `_brierbest` in train.py), und setzt am Ende diesen Stand ein,
   BEVOR die BN-Neuschaetzung und die Schlussvalidierung laufen. Anlass
   par.16a: der Endstand mittelt die ueberangepassten spaeten Epochen mit hinein.
   Speicher: eine Modellkopie (b08-`_avg.pth` 11.532.710 Byte auf der Platte).

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
# par.16b: welcher gemittelte Stand als `_avg` gespeichert wird.
WEIGHT_AVERAGE_SELECTS = ("final", "brierbest")
DEFAULT_WEIGHT_AVERAGE_SELECT = "final"


def validate_weight_average_args(mode: str, decay: float, from_epoch: int,
                                 epochs: int | None, freeze_trunk: bool,
                                 select: str = "final") -> None:
    """Harte Vorab-Validierung; kein stiller Rueckfall auf einen anderen Modus."""
    if mode not in WEIGHT_AVERAGE_MODES:
        sys.exit(f"❌ --weight-average {mode!r} unbekannt -- erlaubt: {WEIGHT_AVERAGE_MODES}.")
    if select not in WEIGHT_AVERAGE_SELECTS:
        sys.exit(f"❌ --weight-average-select {select!r} unbekannt -- erlaubt: {WEIGHT_AVERAGE_SELECTS}.")
    if mode == "none":
        if select != DEFAULT_WEIGHT_AVERAGE_SELECT:
            # Ohne Mittel gibt es nichts auszuwaehlen; ein gesetzter Knopf ohne
            # Wirkung waere ein Bedienfehler, der im Manifest falsch aussaehe.
            sys.exit(f"❌ --weight-average-select {select!r} ohne --weight-average (none) -- Abbruch.")
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

    select (par.16b): `final` = das Mittel nach der letzten Epoche wird
    gespeichert (Bestand); `brierbest` = `observe_val_brier` haelt den
    gemittelten Stand mit dem kleinsten Val-Brier fest, `apply_selection`
    setzt ihn am Ende in `self.model` ein.
    """

    def __init__(self, mode: str, decay: float, from_epoch: int, select: str = "final"):
        self.mode = mode
        self.decay = float(decay)
        self.from_epoch = int(from_epoch)
        self.select = select
        self.n_averaged = 0
        self.averaged_epochs: list[int] = []
        self.model = None  # angelegt beim ersten Mitteln (spart Speicher davor)
        # Zuletzt gemessener Brier des Mittels (beide Modi, nur Mitschrift fuers Manifest).
        self.last_epoch: int | None = None
        self.last_brier: float | None = None
        # Nur select=brierbest: bester gemittelter Stand (CPU-Kopie), erstes Minimum.
        self.best_epoch: int | None = None
        self.best_brier: float | None = None
        self.best_state: dict | None = None

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

    def observe_val_brier(self, brier: float | None, epoch: int) -> bool:
        """Val-Brier des Mittels nach Epoche `epoch` mitschreiben; bei `brierbest`
        den Stand festhalten, wenn er STRENG besser ist als der bisher beste
        (erstes Minimum). True = neuer bester Stand festgehalten. Beruehrt
        keinen Zufallsgenerator und nicht `self.model` (nur Lesen)."""
        self.last_epoch = int(epoch)
        self.last_brier = brier
        if self.select != "brierbest" or brier is None or self.model is None:
            return False
        if self.best_brier is not None and not (brier < self.best_brier):
            return False
        self.best_brier = float(brier)
        self.best_epoch = int(epoch)
        self.best_state = {k: v.detach().cpu().clone() for k, v in self.model.state_dict().items()}
        return True

    def apply_selection(self, device) -> int | None:
        """Am Trainingsende: bei `brierbest` den festgehaltenen Stand in
        `self.model` einsetzen (danach BN-Neuschaetzung und Schlussvalidierung
        auf DIESEM Stand). Gibt die Epoche des eingesetzten Stands zurueck; bei
        `final` die letzte gemittelte Epoche (das Mittel bleibt unveraendert).
        None = `brierbest`, aber kein Brier gemessen -- dann bleibt der Endstand
        stehen, und der Aufrufer muss das laut melden."""
        if self.select != "brierbest":
            return self.averaged_epochs[-1] if self.averaged_epochs else None
        if self.best_state is None:
            return None
        self.model.load_state_dict({k: v.to(device) for k, v in self.best_state.items()})
        return self.best_epoch

    def selected_brier(self) -> float | None:
        """Val-Brier (gemittelte BN-Buffer, vor der Neuschaetzung) des gewaehlten Stands."""
        if self.select == "brierbest":
            return self.best_brier
        if self.averaged_epochs and self.last_epoch == self.averaged_epochs[-1]:
            return self.last_brier
        return None

    def state(self) -> dict:
        """Fuer den Zwischenstand (`--resume`): Mittel plus Zaehler, auf der CPU.
        Die Felder ab `select` (par.16b) kamen spaeter hinzu; `load_state` liest
        aeltere Zwischenstaende ohne sie als `final`."""
        return {
            "mode": self.mode, "decay": self.decay, "from_epoch": self.from_epoch,
            "n_averaged": self.n_averaged, "averaged_epochs": list(self.averaged_epochs),
            "model_state": (None if self.model is None else
                            {k: v.detach().cpu().clone() for k, v in self.model.state_dict().items()}),
            "select": self.select,
            "last_epoch": self.last_epoch, "last_brier": self.last_brier,
            "best_epoch": self.best_epoch, "best_brier": self.best_brier,
            "best_state": (None if self.best_state is None else
                           {k: v.clone() for k, v in self.best_state.items()}),
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
        saved_select = state.get("select", "final")
        if saved_select != self.select:
            sys.exit(f"❌ --resume: weight_average select: Zwischenstand={saved_select!r} "
                     f"jetzt={self.select!r} -- Abbruch.")
        self.n_averaged = int(state["n_averaged"])
        self.averaged_epochs = list(state["averaged_epochs"])
        if state["model_state"] is not None:
            self._ensure_model(model)
            self.model.load_state_dict({k: v.to(device) for k, v in state["model_state"].items()})
        self.last_epoch = state.get("last_epoch")
        self.last_brier = state.get("last_brier")
        self.best_epoch = state.get("best_epoch")
        self.best_brier = state.get("best_brier")
        best_state = state.get("best_state")
        self.best_state = None if best_state is None else {k: v.detach().cpu().clone()
                                                           for k, v in best_state.items()}
        if self.select == "brierbest" and self.best_epoch is not None and self.best_state is None:
            sys.exit("❌ --resume: Zwischenstand nennt einen besten gemittelten Stand "
                     f"(Epoche {self.best_epoch}), traegt ihn aber nicht -- Abbruch.")

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
