# -*- coding: utf-8 -*-
"""Tote ReLU-Einheiten je Modell auf dem FESTEN Auswertungssatz frozen_v3.

Vorregistriert in `evaluations/PREREG_v29_window.md` par.6d Punkt 2
("Netz-Gesundheit unter wachsendem Eingang", Nutzer 2026-09-13: "nicht dass uns
der nun abstirbt mit der anzahl an features"). Gemessen wird der Anteil der
Einheiten der ersten Flachschicht und des Rumpfs, die ueber ALLE Zustaende des
Satzes nie feuern.

**Warum neben `net_capacity_probe.py`, das dieselbe Kennzahl rechnet:** jenes
Werkzeug zieht eine ZUFALLSSTICHPROBE aus einer Fensterliste (Seed, `--n-states`).
Fuer eine Reihe ueber Generationen -- 744 gegen 755 gegen 794 -- braucht es
denselben Satz fuer jedes Modell, sonst vermischt sich der Eingangs-Effekt mit der
Stichprobe. Deshalb frozen_v3 (1.800 Zustaende, 360 je Runde,
`PREREG_frozen_v3_eval_set.md`) und deshalb ein eigener Einstieg. Die Messung
selbst kommt aus `analyze_capacity` der beiden Modellklassen -- hier wird sie
NICHT nachgebaut, nur auf den festen Satz gestellt und gegen eine Referenz
gehalten.

**Verdikt-Regel, vorab registriert:** mehr als das DOPPELTE des Referenz-Anteils
ist ROT. Die Referenz ist per Vorgabe der Pflichtarm der Generation (v29-b01);
sie wird mit `--reference` benannt und muss unter den gemessenen Modellen sein.
Ohne Referenz werden die Zahlen nur berichtet, ohne Verdikt.

**Umfang:** par.6d fragt nach "der ersten Flachschicht (und des Rumpfs)". Das sind
im 2D-Encoder die Schichten `flat`, `fusion1` und `fusion2`, im flachen Encoder
`layer1` bis `layer3`. Die Conv-Schichten werden mitgemessen, aber getrennt
ausgewiesen und gehen nicht ins Verdikt ein: sie sehen den gewachsenen Eingang
gar nicht.

Aufruf:
    python -X utf8 -u tools/probes/dead_unit_probe.py \\
        --models v29-b03_brierbest v29-b01_brierbest v28-b02_brierbest \\
        --reference v29-b01_brierbest \\
        --out evaluations/artifacts/dead_units_v29.json

Rechenlast: ein Vorwaertslauf je Modell ueber 1.800 Zustaende, keine Suche,
Minuten je Modell -- aber NIE neben einer Arena oder Erzeugung (par.6d, CLAUDE.md).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "engine" / "py"))

import torch  # noqa: E402
import corpus_io  # noqa: E402
from neural_net import build_model_from_checkpoint, state_to_planes, state_to_tensor  # noqa: E402

FROZEN = REPO / "evaluations" / "frozen_eval_set_v3.pkl"

# Schichten, die den Flachvektor sehen -- nur sie gehen ins Verdikt (s. Modulkopf).
FLAT_FED_LAYERS_2D = ("flat", "fusion1", "fusion2")
FLAT_FED_LAYERS_1D = ("layer1", "layer2", "layer3")


def load_frozen_states(path: Path) -> list[dict]:
    """Zustaende des festen Auswertungssatzes. Format wie in
    `tools/probes/value_head_reliability_probe.py`: Dict mit `records`."""
    data = corpus_io.load_records(path)
    records = data["records"] if isinstance(data, dict) else data
    states = [r["state"] for r in records if isinstance(r, dict) and isinstance(r.get("state"), dict)]
    if not states:
        raise SystemExit(
            f"{path}: keine Zustaende gefunden -- der Lauf darf nicht leer gruen durchgehen."
        )
    return states


def encode(states: list[dict], input_size: int):
    """Planes und Flachteil. Der Flachteil wird auf die MODELLBREITE gekuerzt --
    das Layout ist append-only, Altmodelle sehen ihre ersten n Werte unveraendert
    (dieselbe Regel wie `net.rs::build_inputs` im Spielpfad)."""
    planes = torch.stack([state_to_planes(s).float() for s in states])
    flat = torch.stack([state_to_tensor(s)[:input_size] for s in states])
    return planes, flat


def flat_fed_ratio(cap: dict, encoder: str) -> tuple[float, list[str]]:
    """Anteil toter Einheiten ueber die Schichten, die den Flachvektor sehen.
    Gewichtet nach Einheitenzahl, nicht als Mittel der Anteile: eine breite
    Schicht mit wenigen toten Einheiten soll eine schmale mit vielen nicht
    ueberstimmen."""
    wanted = FLAT_FED_LAYERS_2D if encoder == "2d" else FLAT_FED_LAYERS_1D
    used = [n for n in wanted if n in cap]
    dead = sum(cap[n]["dead"] for n in used)
    total = sum(cap[n]["n_neurons"] for n in used)
    return (dead / total if total else 0.0), used


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--models",
        nargs="+",
        required=True,
        help="Checkpoint-Namen ohne 'alphazero_' und '.pth'",
    )
    ap.add_argument(
        "--reference",
        default=None,
        help="Modell, gegen das die Verdikt-Schwelle rechnet (par.6d: v29-b01). "
        "Muss unter --models stehen. Ohne Referenz: nur Bericht, kein Verdikt.",
    )
    ap.add_argument(
        "--frozen-set",
        default=str(FROZEN),
        help="Auswertungssatz (Default frozen_v3, 1.800 Zustaende)",
    )
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    if a.reference and a.reference not in a.models:
        raise SystemExit(
            f"--reference {a.reference} steht nicht unter --models: "
            "die Schwelle rechnet gegen ein Modell desselben Laufs, nicht gegen eine Zahl von aussen."
        )

    t0 = time.time()
    states = load_frozen_states(Path(a.frozen_set))
    print(f"{len(states)} Zustaende aus {a.frozen_set} ({time.time() - t0:.1f}s)", flush=True)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    out = {
        "frozen_set": a.frozen_set,
        "n_states": len(states),
        "device": device,
        "reference": a.reference,
        "modelle": {},
    }

    for i, name in enumerate(a.models, 1):
        t_model = time.time()
        print(f"[{i}/{len(a.models)}] {name} ...", flush=True)
        pth = REPO / "models" / f"alphazero_{name}.pth"
        if not pth.exists():
            raise SystemExit(f"{pth} fehlt -- kein stiller Skip (Nutzer-Regel: nie leer gruen).")
        ckpt = torch.load(pth, map_location="cpu", weights_only=False)
        model, encoder = build_model_from_checkpoint(ckpt)
        model.to(device).eval()
        in_size = model.input_size if hasattr(model, "input_size") else ckpt.get("input_size")
        planes, flat = encode(states, in_size)
        with torch.no_grad():
            if encoder == "2d":
                cap = model.analyze_capacity(planes.to(device), flat.to(device))
            else:
                cap = model.analyze_capacity(flat.to(device))
        ratio, used = flat_fed_ratio(cap, encoder)

        print(f"    Eingang {in_size}, Encoder {encoder}, Epochen {ckpt.get('epochs')}")
        print(f"    {'Schicht':<9} {'tot':>14} {'Aktiv-Rate':>12}")
        for ln, m in cap.items():
            mark = "*" if ln in used else " "
            print(
                f"   {mark}{ln:<9} {m['dead']:>5}/{m['n_neurons']:<5} "
                f"({m['dead_ratio'] * 100:>4.1f}%) {m['active_rate'] * 100:>10.1f}%"
            )
        print(
            f"    -> Flachvektor-Schichten (*): {ratio * 100:.2f} % tot "
            f"({time.time() - t_model:.1f}s)",
            flush=True,
        )
        out["modelle"][name] = {
            "encoder": encoder,
            "input_size": in_size,
            "hidden_size": ckpt.get("hidden_size"),
            "epochs": ckpt.get("epochs"),
            "schichten": cap,
            "flat_fed_layers": used,
            "flat_fed_dead_ratio": ratio,
        }

    # Verdikt gegen die Referenz (par.6d: mehr als das Doppelte ist ROT).
    if a.reference:
        ref = out["modelle"][a.reference]["flat_fed_dead_ratio"]
        out["reference_dead_ratio"] = ref
        out["schwelle"] = 2.0 * ref
        print(
            f"\nReferenz {a.reference}: {ref * 100:.2f} % tot, "
            f"Schwelle {2 * ref * 100:.2f} % (par.6d: mehr als das Doppelte ist ROT)"
        )
        for name, m in out["modelle"].items():
            r = m["flat_fed_dead_ratio"]
            if name == a.reference:
                verdict = "REFERENZ"
            elif ref == 0.0:
                # Ohne tote Einheiten in der Referenz gibt es kein Doppeltes;
                # dann ist jede tote Einheit im Arm der Befund.
                verdict = "ROT" if r > 0.0 else "GRUEN"
            else:
                verdict = "ROT" if r > 2.0 * ref else "GRUEN"
            m["verdikt"] = verdict
            print(f"  {name:<22} {r * 100:>6.2f} %  {verdict}")

    wall = time.time() - t0
    out["laufzeit"] = {
        "wanduhr_s": round(wall, 1),
        "cpu_s": round(time.process_time(), 1),
        "threads": torch.get_num_threads(),
        # Kein Partienlauf; das Pflichtfeld bleibt ausdruecklich leer statt zu fehlen
        # (Konvention wie tools/corpus_sanity_check.py).
        "s_je_partie": None,
    }
    if a.out:
        Path(a.out).write_text(
            json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
        )
        print(f"\nArtefakt: {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
