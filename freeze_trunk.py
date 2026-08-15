# -*- coding: utf-8 -*-
"""freeze_trunk.py -- Trunk-Einfrier-Modus fuer train.py (`--freeze-trunk`).

Herkunft: PREREG_ownership_corpus.md §10.3/§10.4 -- bei allen vier Sweep-Armen
faellt der `_best`-Checkpoint auf Epoche 1, weil das Auswahlkriterium
`val_combined` (train.py, `current_metric`-Stelle) den Ownership-Verlust GAR
NICHT enthaelt; der `final`-Checkpoint (Ep. 15) hat den weit besseren Kopf, aber
eine ueberangepasste Policy. Die Ueberanpassung ist NACHWEISLICH kein
Ownership-Effekt (Kontrollarm w0, Gewicht 0,0, zeigt denselben
policy-val-loss 0,3002). Dieses Modul loest den Zielkonflikt strukturell:
wenn Trunk und alle uebrigen Koepfe eingefroren sind, KANN die Policy nicht
mehr ueberanpassen -- der Ownership-Kopf bekommt seine Epochen allein.

Ausgelagert aus train.py (statt dort eingebaut) aus zwei Gruenden: die
Modularitaetsregel aus CLAUDE.md und die Groessen-Ratsche in
tools/check_conventions.py (Regel 1, Ausweg (a) "Funktionsblock in ein neues
Modul auslagern"). Vorbild fuer ein train.py-Hilfsmodul im Repo-Root:
head_warmstart.py.

DREI Bausteine, alle bei `active=False` (Default) wirkungslos:

1. `validate_freeze_args` -- harte Vorab-Validierung (Muster
   `--value-target-lambda`/`--extra-data-dir` in train.py): laeuft VOR jedem
   teuren Daten-Laden, kein stiller Fallback.
2. `TrunkFreeze` -- die eigentliche Einfrier-Mechanik (requires_grad + der
   BatchNorm-Riegel, siehe unten) und die Auswahl der Optimizer-Parameter.
3. `OwnershipValLoss` -- der maskierte BCE-Val-Verlust des Ownership-Kopfs,
   d.h. das ownership-BEWUSSTE Auswahlkriterium, das §10.3 gefehlt hat.

BatchNorm-Riegel -- der Punkt, an dem ein naives `requires_grad=False`
STILL falsch waere: `Mosaic2DNet` hat BatchNorm in `conv` (BatchNorm2d),
`flat_branch` und `fusion` (BatchNorm1d), `MosaicNet` in `body`
(neural_net.py, Konstruktoren beider Klassen). BatchNorm aktualisiert im
TRAIN-Modus seine `running_mean`/`running_var`-BUFFER -- und Buffer haben kein
`requires_grad`. Ohne zusaetzliche Massnahme wuerde der eingefrorene Trunk
seine Statistiken also weiter verschieben, und policy/value-Ausgaben waeren
nach einer Epoche NICHT mehr identisch zum Start-Checkpoint. Deshalb setzt
dieses Modul jeden nicht-trainierten Teilbaum dauerhaft in den eval-Modus und
haelt ihn dort, indem es `model.train` auf der INSTANZ ueberschreibt (nicht auf
der Klasse) -- damit greift der Riegel auch bei `model.train()`-Aufrufen, die
train.py an anderer Stelle macht (nach der Validierung und in der
Auslastungsanalyse), ohne dass dort etwas geaendert werden muesste. Genau
diese Zusicherung prueft `tools/freeze_trunk_selfcheck.py`.
"""
from __future__ import annotations

import sys

import torch.nn.functional as F

# Der EINZIGE Teilbaum, der im Freeze-Modus trainiert wird. Name laut
# neural_net.py (`self.ownership_head = nn.Sequential(...)` in BEIDEN
# Modellklassen, MosaicNet und Mosaic2DNet) -- die Konjunktions-Ausgaenge
# sind KEIN eigener Kopf, sondern die hinten angehaengten
# CONJUNCTION_TARGETS derselben Ausgabeschicht (neural_net.py, Kommentar
# "Konjunktions-Erweiterung ... +CONJUNCTION_TARGETS hinten angehaengt"),
# werden von diesem Namen also automatisch mit erfasst.
TRAINED_MODULE = "ownership_head"


def validate_freeze_args(freeze_trunk: bool, ownership_weight, load_version,
                         val_frac: float) -> None:
    """Harte Vorab-Validierung des Freeze-Modus (kein stiller Fallback).

    Bei `freeze_trunk=False` (Default) ein no-op.
    """
    if not freeze_trunk:
        return
    if ownership_weight is None or ownership_weight <= 0.0:
        sys.exit(
            f"❌ --freeze-trunk verlangt --ownership-weight > 0 (ist: {ownership_weight!r}).\n"
            f"   Sonst waere der EINZIGE trainierbare Teil des Netzes ohne Verlustterm -- "
            f"der Lauf wuerde Rechenzeit verbrauchen und nichts aendern."
        )
    if not load_version:
        sys.exit(
            "❌ --freeze-trunk verlangt --load: ein eingefrorener ZUFALLS-Trunk ist kein "
            "Experiment, sondern ein Zufallsmerkmals-Extraktor. Abbruch statt stillem Unsinn."
        )
    if not (val_frac and val_frac > 0.0):
        sys.exit(
            f"❌ --freeze-trunk verlangt --val-frac > 0 (ist: {val_frac!r}).\n"
            f"   Das Auswahlkriterium dieses Modus IST der Ownership-Val-Verlust "
            f"(PREREG_ownership_corpus.md §10.3) -- ohne Val-Split gibt es keins."
        )


class TrunkFreeze:
    """Zustandsobjekt des Freeze-Modus. `active=False` = Bestandsverhalten."""

    def __init__(self, active: bool = False):
        self.active = bool(active)
        self.n_frozen_params = 0
        self.n_trained_params = 0
        self.n_frozen_tensors = 0
        self.n_trained_tensors = 0

    # -- Aufbau ----------------------------------------------------------
    @classmethod
    def setup(cls, model, freeze_trunk: bool) -> "TrunkFreeze":
        """Friert alles ausser `ownership_head` ein. Ohne Flag: no-op.

        Aufzurufen NACH dem Warm-Start-Load und NACH `model.to(device)`.
        """
        self = cls(freeze_trunk)
        if not self.active:
            return self
        if not hasattr(model, TRAINED_MODULE):
            sys.exit(f"❌ --freeze-trunk: Modell hat kein `{TRAINED_MODULE}` -- Abbruch.")
        prefix = TRAINED_MODULE + "."
        for name, p in model.named_parameters():
            trained = name.startswith(prefix)
            p.requires_grad = trained
            if trained:
                self.n_trained_tensors += 1
                self.n_trained_params += p.numel()
            else:
                self.n_frozen_tensors += 1
                self.n_frozen_params += p.numel()
        if self.n_trained_tensors == 0:
            sys.exit(f"❌ --freeze-trunk: kein einziger `{prefix}*`-Parameter gefunden -- Abbruch.")
        _install_eval_lock(model)
        print(
            f"🧊 Freeze-Modus AKTIV (PREREG_frozen_trunk_head.md): trainiert wird NUR "
            f"`{TRAINED_MODULE}` ({self.n_trained_tensors} Tensoren, "
            f"{self.n_trained_params:,} Parameter); eingefroren sind "
            f"{self.n_frozen_tensors} Tensoren / {self.n_frozen_params:,} Parameter "
            f"(Trunk + policy/value/moon/points/opp_points/endgame).\n"
            f"   BatchNorm-Riegel gesetzt: alle eingefrorenen Teilbaeume bleiben dauerhaft "
            f"im eval-Modus, ihre running_mean/running_var werden NICHT mehr fortgeschrieben "
            f"-- policy/value-Ausgaben bleiben damit bit-identisch zum Start-Checkpoint."
        )
        return self

    # -- Verwendung im Trainingslauf --------------------------------------
    def trainable_params(self, model):
        """Parameterliste fuer den Optimizer. Inaktiv: `model.parameters()`."""
        if not self.active:
            return model.parameters()
        return [p for p in model.parameters() if p.requires_grad]

    def backward_ok(self, loss) -> bool:
        """Darf fuer diesen Batch `loss.backward()` laufen?

        Inaktiv immer True (Bestandsverhalten unveraendert). Aktiv kann der
        Gesamt-Loss ein reiner Konstanten-Tensor sein -- naemlich dann, wenn in
        einem Batch KEIN einziges Ownership-Label bekannt ist (alle -1, siehe
        Maskierung in train.py) und der einzige gradientenfuehrende Term damit
        wegfaellt. `backward()` wuerde dann mit "element 0 of tensors does not
        require grad" abbrechen; im Bestandsmodus kann das nicht passieren,
        weil der Policy-Term immer traegt.
        """
        if not self.active:
            return True
        return bool(getattr(loss, "requires_grad", False))

    def selected_by(self) -> str:
        return "ownership_val_loss(freeze-trunk, PREREG_frozen_trunk_head.md)"


def _install_eval_lock(model) -> None:
    """Ueberschreibt `model.train` auf der INSTANZ (BatchNorm-Riegel, s. Moduldoku)."""
    base_train = type(model).train

    def _train(mode: bool = True):
        base_train(model, mode)
        if mode:
            for name, child in model.named_children():
                child.train(name == TRAINED_MODULE)
        return model

    model.train = _train          # type: ignore[method-assign]
    model.train(model.training)   # Riegel sofort auf den Ist-Modus anwenden


class OwnershipValLoss:
    """Maskierter BCE-Val-Verlust des Ownership-Kopfs (Ziel-Wert: klein = gut).

    Formel identisch zum Trainings-Term in train.py (`own_loss`:
    `binary_cross_entropy_with_logits` gegen `own_t.clamp(min=0)`, maskiert mit
    `own_t >= 0`). Unterschied bewusst und dokumentiert: hier wird ueber den
    GESAMTEN Val-Split label-gewichtet gemittelt (Summe/Summe), nicht als
    Mittel der Batch-Mittel -- kleine Rest-Batches wuerden sonst
    ueberproportional zaehlen, und dieser Wert IST im Freeze-Modus das
    Auswahlkriterium.

    `enabled=False` -> `value()` gibt None, `add()` ist ein no-op.
    """

    def __init__(self, enabled: bool):
        self.enabled = bool(enabled)
        self._sum = 0.0
        self._n = 0.0

    def add(self, pred_own, own_targets) -> None:
        if not self.enabled:
            return
        t = own_targets.to(pred_own.device).float()
        m = (t >= 0).float()
        if float(m.sum()) <= 0.0:
            return
        bce = F.binary_cross_entropy_with_logits(
            pred_own, t.clamp(min=0.0), reduction="none")
        self._sum += float((bce * m).sum().item())
        self._n += float(m.sum().item())

    def value(self):
        if not self.enabled or self._n <= 0.0:
            return None
        return self._sum / self._n


def plateau_series_for(freeze_active: bool, val_ownloss_history, default_series):
    """Welche Reihe die Plateau-Erkennung im Freeze-Modus beobachtet.

    Ohne Flag: unveraendert `default_series` (Val-Policy-Loss bzw.
    Trainings-Policy-Loss). MIT Flag WAERE die Policy-Reihe konstant -- die
    bestehende Plateau-Formel `(previous-recent)/previous` ergaebe sofort 0 und
    wuerde nach 2*plateau_window Epochen ein Early Stopping ausloesen, das mit
    dem Lernfortschritt des Kopfs nichts zu tun hat. Im Freeze-Modus zaehlt
    darum die Ownership-Reihe.
    """
    if not freeze_active:
        return default_series
    return [v for v in val_ownloss_history if v is not None]
