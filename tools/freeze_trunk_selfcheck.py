# -*- coding: utf-8 -*-
"""tools/freeze_trunk_selfcheck.py -- Selbsttest des Trunk-Einfrier-Modus
(`train.py --freeze-trunk`, Modul `freeze_trunk.py`).

Prueft die HARTE ZUSICHERUNG des Modus, statt sie zu behaupten:

  FREEZE   Nach mehreren echten Optimizer-Schritten auf einem reinen
           Ownership-Verlust sind policy/value/moon/points/opp_points/endgame
           bei identischer Eingabe BIT-IDENTISCH zum Start (torch.equal, keine
           Toleranz), und die BatchNorm-Buffer (running_mean/running_var/
           num_batches_tracked) ebenfalls. Beides in BEIDEN Modellklassen
           (MosaicNet flach + Mosaic2DNet). Gegenprobe im selben Lauf: der
           Ownership-Ausgang MUSS sich geaendert haben -- sonst waere die
           Gleichheit trivial erfuellt, weil gar nichts trainiert wurde.

  CONTROL  Derselbe Ablauf OHNE Freeze veraendert policy UND die
           BatchNorm-Buffer. Beweist, dass die FREEZE-Suite ueberhaupt etwas
           pruefen kann (nicht vacuous) -- die Lehre aus dem
           Streuungs-Leck-Test in PREREG_ownership_corpus.md §3.7.

  NAIV     Der naive Modus von Hand nachgebaut (nur requires_grad, KEIN
           eval-Riegel) driftet nachweislich -- damit ist belegt, dass der
           Riegel tragend ist und nicht bloss Dekoration.

  GUARD    `validate_freeze_args` bricht bei jeder der drei unsinnigen
           Kombinationen hart ab (Gewicht 0, kein --load, kein Val-Split) und
           laesst die gueltige Kombination durch; ohne Flag ist sie ein no-op.

  METER    `OwnershipValLoss` rechnet dieselbe Formel wie der Trainings-Term
           in train.py (maskierte BCE-Summe / Maskensumme), gegen eine von
           Hand aufgestellte Referenz mit -1-Labels.

Ohne Korpus, ohne GPU, ohne Modelldateien lauffaehig (Sekunden).
Aufruf:  python tools/freeze_trunk_selfcheck.py
Exit 0 = alle Suiten gruen, Exit 1 = mindestens eine rot.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Windows-Konsolen (cp1252) koennen die Emoji-Ausgaben von freeze_trunk.py
# sonst nicht kodieren -- gleiches Muster wie am Kopf von train.py.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import torch
import torch.nn.functional as F

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "engine" / "py"))

from config import NUM_ACTIONS, OWNERSHIP_TARGETS  # noqa: E402
from freeze_trunk import (OwnershipValLoss, TrunkFreeze,  # noqa: E402
                          plateau_series_for, validate_freeze_args)
from neural_net import NUM_PLANES_CHANNELS, Mosaic2DNet, MosaicNet  # noqa: E402

INPUT_SIZE = 64      # klein gehalten -- die Zusicherung haengt nicht an der Breite
HIDDEN = 32
BATCH = 8
STEPS = 4
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'[ok]  ' if ok else '[FAIL]'} {name}" + (f" -- {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def build(kind: str):
    torch.manual_seed(4711)
    common = dict(input_size=INPUT_SIZE, num_actions=NUM_ACTIONS, hidden_size=HIDDEN,
                  opp_points_head=True, endgame_head=True, conjunction_head=True,
                  value_head_variant="wdl")
    if kind == "2d":
        return Mosaic2DNet(planes_channels=NUM_PLANES_CHANNELS, **common)
    return MosaicNet(**common)


def forward(model, kind: str, planes, flat):
    return model(planes, flat) if kind == "2d" else model(flat)


def buffers_snapshot(model) -> dict:
    return {n: b.detach().clone() for n, b in model.named_buffers()}


def run_training(model, kind, planes, flat, own_target, frozen: bool):
    """Echte Optimizer-Schritte auf einem reinen Ownership-BCE."""
    ftz = TrunkFreeze.setup(model, frozen)
    opt = torch.optim.Adam(ftz.trainable_params(model), lr=1e-2)
    model.train()          # Bestandsaufruf von train.py -- der Riegel muss ihn ueberleben
    for _ in range(STEPS):
        opt.zero_grad()
        out = forward(model, kind, planes, flat)
        loss = F.binary_cross_entropy_with_logits(out[4], own_target)
        if ftz.backward_ok(loss):
            loss.backward()
            opt.step()
        model.train()      # train.py ruft das nach jedem Val-Durchlauf erneut
    return ftz


def suite_freeze(kind: str) -> None:
    print(f"\n=== FREEZE / {kind} ===")
    torch.manual_seed(20260816)
    planes = torch.randn(BATCH, NUM_PLANES_CHANNELS, 6, 6)
    flat = torch.randn(BATCH, INPUT_SIZE)
    model = build(kind)
    own_width = model.ownership_head[-1].out_features
    own_target = (torch.rand(BATCH, own_width) > 0.5).float()

    model.eval()
    with torch.no_grad():
        before = [t.detach().clone() for t in forward(model, kind, planes, flat)]
    buf_before = buffers_snapshot(model)

    ftz = run_training(model, kind, planes, flat, own_target, frozen=True)
    check(f"{kind}: setup meldet aktiv + genau die ownership_head-Tensoren trainierbar",
          ftz.active and ftz.n_trained_tensors == 4 and ftz.n_frozen_tensors > 0,
          f"trainiert {ftz.n_trained_tensors} Tensoren / {ftz.n_trained_params} Parameter, "
          f"eingefroren {ftz.n_frozen_tensors} / {ftz.n_frozen_params}")

    model.eval()
    with torch.no_grad():
        after = [t.detach().clone() for t in forward(model, kind, planes, flat)]

    # Ausgangs-Reihenfolge laut neural_net.py::forward: 0 policy, 1 value,
    # 2 moon, 3 points, 4 ownership, danach die OPTIONALEN in genau dieser
    # Reihenfolge -- dynamisch aus dem Modell abgeleitet statt geraten, damit
    # der Test nicht still an der falschen Stelle vergleicht.
    names = {0: "policy", 1: "value", 2: "moon", 3: "points"}
    optional = ([] + (["points_logits"] if model.points_dist_bins > 0 else [])
                + (["value_wdl_logits"] if model.value_head_variant == "wdl" else [])
                + (["opp_points"] if model.has_opp_points_head else [])
                + (["endgame"] if model.has_endgame_head else []))
    for j, nm in enumerate(optional):
        names[5 + j] = nm
    check(f"{kind}: Ausgangsbreite wie erwartet ({5 + len(optional)} Tensoren)",
          len(before) == 5 + len(optional), f"ist {len(before)}, optional: {optional}")
    for idx, nm in names.items():
        check(f"{kind}: {nm} bit-identisch nach {STEPS} Freeze-Schritten",
              torch.equal(before[idx], after[idx]),
              "" if torch.equal(before[idx], after[idx])
              else f"max |delta| = {(before[idx] - after[idx]).abs().max().item():.3e}")

    # Gegenprobe: ohne Aenderung am Kopf waere alles oben trivial gruen.
    check(f"{kind}: ownership HAT sich geaendert (Test nicht vacuous)",
          not torch.equal(before[4], after[4]),
          f"max |delta| = {(before[4] - after[4]).abs().max().item():.3e}")

    buf_after = buffers_snapshot(model)
    bn_names = [n for n in buf_before if "running_" in n or "num_batches_tracked" in n]
    check(f"{kind}: {len(bn_names)} BatchNorm-Buffer unveraendert (BatchNorm-Riegel)",
          bool(bn_names) and all(torch.equal(buf_before[n], buf_after[n]) for n in bn_names),
          f"geprueft: {len(bn_names)} Buffer")


def suite_control(kind: str) -> None:
    """Ohne Freeze MUSS sich policy aendern -- sonst prueft die Suite oben nichts."""
    print(f"\n=== CONTROL (ohne Freeze) / {kind} ===")
    torch.manual_seed(20260816)
    planes = torch.randn(BATCH, NUM_PLANES_CHANNELS, 6, 6)
    flat = torch.randn(BATCH, INPUT_SIZE)
    model = build(kind)
    own_target = (torch.rand(BATCH, model.ownership_head[-1].out_features) > 0.5).float()

    model.eval()
    with torch.no_grad():
        before = [t.detach().clone() for t in forward(model, kind, planes, flat)]
    buf_before = buffers_snapshot(model)

    run_training(model, kind, planes, flat, own_target, frozen=False)

    model.eval()
    with torch.no_grad():
        after = [t.detach().clone() for t in forward(model, kind, planes, flat)]
    buf_after = buffers_snapshot(model)
    bn_names = [n for n in buf_before if "running_mean" in n]

    check(f"{kind}: policy AENDERT sich ohne Freeze", not torch.equal(before[0], after[0]),
          f"max |delta| = {(before[0] - after[0]).abs().max().item():.3e}")
    check(f"{kind}: BatchNorm-Statistiken wandern ohne Freeze",
          any(not torch.equal(buf_before[n], buf_after[n]) for n in bn_names))


def suite_naive(kind: str) -> None:
    """Warum der BatchNorm-Riegel existiert: `requires_grad=False` ALLEIN reicht nicht.

    Baut den naiven Modus von Hand nach (nur requires_grad, kein eval-Riegel)
    und zeigt, dass policy/value dann DOCH wandern -- ueber die
    running_mean/running_var-Buffer, die kein requires_grad haben. Faellt diese
    Suite eines Tages "gruen im naiven Sinn" aus (nichts wandert), ist der
    Riegel entweder ueberfluessig geworden oder die FREEZE-Suite prueft nichts
    mehr -- beides gehoert dann angesehen.
    """
    print(f"\n=== NAIV (nur requires_grad, ohne Riegel) / {kind} ===")
    torch.manual_seed(20260816)
    planes = torch.randn(BATCH, NUM_PLANES_CHANNELS, 6, 6)
    flat = torch.randn(BATCH, INPUT_SIZE)
    model = build(kind)
    own_target = (torch.rand(BATCH, model.ownership_head[-1].out_features) > 0.5).float()

    model.eval()
    with torch.no_grad():
        before = [t.detach().clone() for t in forward(model, kind, planes, flat)]

    for n, p in model.named_parameters():
        p.requires_grad = n.startswith("ownership_head.")
    opt = torch.optim.Adam([p for p in model.parameters() if p.requires_grad], lr=1e-2)
    model.train()
    for _ in range(STEPS):
        opt.zero_grad()
        F.binary_cross_entropy_with_logits(
            forward(model, kind, planes, flat)[4], own_target).backward()
        opt.step()

    model.eval()
    with torch.no_grad():
        after = [t.detach().clone() for t in forward(model, kind, planes, flat)]
    check(f"{kind}: policy DRIFTET ohne Riegel (Riegel ist tragend, keine Deko)",
          not torch.equal(before[0], after[0]),
          f"max |delta| = {(before[0] - after[0]).abs().max().item():.3e}")


def suite_guard() -> None:
    print("\n=== GUARD ===")
    cases = [
        ("Gewicht 0 bricht ab", dict(freeze_trunk=True, ownership_weight=0.0,
                                     load_version="x", val_frac=0.1)),
        ("Gewicht None bricht ab", dict(freeze_trunk=True, ownership_weight=None,
                                        load_version="x", val_frac=0.1)),
        ("kein --load bricht ab", dict(freeze_trunk=True, ownership_weight=0.5,
                                       load_version=None, val_frac=0.1)),
        ("val_frac 0 bricht ab", dict(freeze_trunk=True, ownership_weight=0.5,
                                      load_version="x", val_frac=0.0)),
    ]
    for name, kwargs in cases:
        try:
            validate_freeze_args(**kwargs)
            check(name, False, "kein SystemExit")
        except SystemExit:
            check(name, True)
    for name, kwargs in (
        ("gueltige Kombination laeuft durch",
         dict(freeze_trunk=True, ownership_weight=0.5, load_version="x", val_frac=0.1)),
        ("ohne Flag no-op (auch bei Unsinn-Argumenten)",
         dict(freeze_trunk=False, ownership_weight=0.0, load_version=None, val_frac=0.0)),
    ):
        try:
            validate_freeze_args(**kwargs)
            check(name, True)
        except SystemExit as exc:
            check(name, False, str(exc))

    inactive = TrunkFreeze(False)
    model = build("flat")
    check("inaktiv: trainable_params == model.parameters()",
          len(list(inactive.trainable_params(model))) == len(list(model.parameters())))
    check("inaktiv: backward_ok immer True",
          inactive.backward_ok(torch.zeros(())) is True)
    check("inaktiv: Plateau-Reihe unveraendert",
          plateau_series_for(False, [0.1, 0.2], [9.0, 8.0]) == [9.0, 8.0])
    check("aktiv: Plateau-Reihe ist die Ownership-Reihe (None gefiltert)",
          plateau_series_for(True, [None, 0.2, 0.15], [9.0, 8.0]) == [0.2, 0.15])


def suite_meter() -> None:
    print("\n=== METER ===")
    m = OwnershipValLoss(False)
    m.add(torch.zeros(2, OWNERSHIP_TARGETS), torch.zeros(2, OWNERSHIP_TARGETS))
    check("deaktiviert liefert None", m.value() is None)

    torch.manual_seed(7)
    logits = torch.randn(3, 5)
    targets = torch.tensor([[1., 0., -1., 1., 0.],
                            [-1., -1., -1., -1., -1.],
                            [0., 1., 1., -1., 0.]])
    mask = (targets >= 0).float()
    bce = F.binary_cross_entropy_with_logits(logits, targets.clamp(min=0.0), reduction="none")
    reference = float((bce * mask).sum() / mask.sum())   # exakt die train.py-Formel

    m = OwnershipValLoss(True)
    for i in range(3):                                   # batchweise wie im Val-Loop
        m.add(logits[i:i + 1], targets[i:i + 1])
    got = m.value()
    check("maskierter BCE == train.py-Formel (auch ueber Batches hinweg)",
          got is not None and abs(got - reference) < 1e-9, f"{got!r} vs {reference!r}")

    m2 = OwnershipValLoss(True)
    m2.add(torch.randn(2, 5), torch.full((2, 5), -1.0))
    check("nur -1-Labels -> None statt erfundener 0.0", m2.value() is None)


if __name__ == "__main__":
    for kind in ("flat", "2d"):
        suite_freeze(kind)
        suite_control(kind)
        suite_naive(kind)
    suite_guard()
    suite_meter()
    print("\n" + "=" * 60)
    if FAILURES:
        print(f"ROT: {len(FAILURES)} Pruefung(en) fehlgeschlagen:")
        for f in FAILURES:
            print(f"  - {f}")
        sys.exit(1)
    print("GRUEN: alle Pruefungen bestanden.")
