#!/usr/bin/env python
"""Tor fuer PREREG_points_dist_bin_scale.md par.6.

Histogrammiert NICHT die Formel tanh(own_total/50), sondern den Zielwert,
den der Cache-Bau TATSAECHLICH erzeugt (neural_net.py:1640-1720): own-Zweig
inklusive rtv-Override und TD-Bootstrap-Blend, exakt nachgebaut. Bins sind
die 51 heutigen, aequidistant im tanh-Raum (linspace(-1,1,52), wie
neural_net.py:2411). Kennzahl: Anteil der Datenmasse in Bins, deren
punktebasierte Breite > 5 liegt (Formel aus par.2: bin_width(z) =
(2/BINS)*VALUE_SCALE/(1-z^2), an der jeweiligen Bin-Mitte ausgewertet).

Kein Training, keine Arena -- reine Pickle-Auswertung.
"""
import glob
import io
import json
import math
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVAL = ROOT / "evaluations"
OUT_JSON = EVAL / "points_dist_bin_scale_gate.json"

VALUE_SCALE = 50.0
TD_LAMBDA = 0.5
BINS = 51

EDGES = [-1.0 + i * (2.0 / BINS) for i in range(BINS + 1)]
CENTERS = [(EDGES[i] + EDGES[i + 1]) / 2.0 for i in range(BINS)]


def bin_width_points(z_center):
    denom = 1.0 - z_center * z_center
    if denom <= 1e-9:
        return float("inf")
    return (2.0 / BINS) * VALUE_SCALE / denom


WIDE_BIN = [bin_width_points(c) > 5.0 for c in CENTERS]


def bin_index(x):
    x = max(-1.0, min(1.0, x))
    idx = int((x - (-1.0)) / (2.0 / BINS))
    return min(BINS - 1, max(0, idx))


def points_val_for_step(step):
    """Repliziert neural_net.py:1640-1720, own-Zweig, value_target_variant
    effektiv irrelevant (rtv im Bestand ueberall abwesend, siehe unten)."""
    if "scores" not in step or "winner" not in step:
        return None, None
    p = step["player"]
    scores_src = step.get("scores_unclamped", step["scores"])
    own_total = float(scores_src[p])
    points_val = math.tanh(own_total / VALUE_SCALE)

    rtv = step.get("round_transition_value")
    if rtv is not None:
        own_rtv = float(rtv[p]) * 2.0 - 1.0
        points_val = own_rtv

    bv = step.get("bootstrap_value")
    if bv is not None:
        own_bootstrap = float(bv[p]) * 2.0 - 1.0
        points_val = TD_LAMBDA * own_bootstrap + (1.0 - TD_LAMBDA) * points_val

    rnd = step.get("state", {}).get("round")
    return points_val, rnd


def stratified_sample(files, stride):
    """Nimmt jede `stride`-te Datei je Generations-Praefix (selfplay_<gen>_...),
    damit die Stichprobe ueber alle Generationen gleichmaessig verteilt bleibt
    -- ein reines `files[::stride]` haette bei sortierter Namensliste einzelne
    Generationen ausduennen koennen, wenn ihre Dateizahl nicht durch `stride`
    teilbar ist."""
    import re
    from collections import defaultdict
    groups = defaultdict(list)
    for f in files:
        m = re.search(r"selfplay_([a-zA-Z0-9]+)_", Path(f).name)
        groups[m.group(1) if m else "?"].append(f)
    out = []
    for gen in sorted(groups):
        out.extend(sorted(groups[gen])[::stride])
    return sorted(out)


def main():
    all_files = sorted(glob.glob(str(ROOT / "data" / "selfplay_*.pkl")))
    if not all_files:
        print("Kein Korpus gefunden.", file=sys.stderr)
        sys.exit(1)
    stride = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    files = stratified_sample(all_files, stride)
    print(f"Korpus gesamt: {len(all_files)} Dateien -- Stichprobe (jede "
          f"{stride}. je Generation): {len(files)} Dateien", file=sys.stderr)

    per_round_mass = {}
    per_round_wide = {}
    total_mass = 0
    total_wide = 0
    n_files = 0
    n_records = 0
    n_scored = 0
    rtv_seen = 0
    bootstrap_seen = 0

    for f in files:
        n_files += 1
        with open(f, "rb") as fh:
            recs = pickle.load(fh)
        for r in recs:
            n_records += 1
            pv, rnd = points_val_for_step(r)
            if pv is None:
                continue
            n_scored += 1
            if r.get("round_transition_value") is not None:
                rtv_seen += 1
            if r.get("bootstrap_value") is not None:
                bootstrap_seen += 1
            idx = bin_index(pv)
            wide = WIDE_BIN[idx]
            total_mass += 1
            total_wide += 1 if wide else 0
            rk = rnd if rnd is not None else "unbekannt"
            per_round_mass[rk] = per_round_mass.get(rk, 0) + 1
            per_round_wide[rk] = per_round_wide.get(rk, 0) + (1 if wide else 0)

    gepoolt = total_wide / total_mass if total_mass else None
    je_runde = {
        str(rk): dict(
            n=per_round_mass[rk],
            anteil_breit=round(per_round_wide[rk] / per_round_mass[rk], 4),
        )
        for rk in sorted(per_round_mass, key=lambda x: (isinstance(x, str), x))
    }

    if gepoolt is None:
        verdikt = "KEIN_DATENSATZ"
    elif gepoolt < 0.10:
        verdikt = "WIDERLEGT (< 10 %) -- Zuschnitt endet, kein Training"
    elif gepoolt < 0.30:
        verdikt = "GRENZFALL (10-30 %) -- Nutzer-Entscheid"
    else:
        verdikt = "PLAUSIBEL (> 30 %) -- Arme T und P werden gefahren"

    result = dict(
        n_dateien_gesamt_korpus=len(all_files),
        n_dateien=n_files,
        n_datensaetze_gesamt=n_records,
        n_mit_score_winner=n_scored,
        n_mit_round_transition_value=rtv_seen,
        n_mit_bootstrap_value=bootstrap_seen,
        anteil_breite_bins_gepoolt=round(gepoolt, 4) if gepoolt is not None else None,
        verdikt=verdikt,
        je_runde=je_runde,
        meta=dict(
            frage="Anteil der Datenmasse in Bins > 5 Punkte breit, auf dem "
                  "TATSAECHLICH gebauten points_val (rtv-Override + "
                  "TD-Bootstrap-Blend), nicht auf der Formel tanh(own/50).",
            schwellen="< 10% widerlegt, 10-30% Grenzfall, > 30% plausibel "
                      "(a priori gesetzt, PREREG_points_dist_bin_scale.md par.6)",
            bins=BINS, value_scale=VALUE_SCALE, td_lambda=TD_LAMBDA,
        ),
    )
    OUT_JSON.write_text(json.dumps(result, indent=2, ensure_ascii=False),
                        encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\n-> {OUT_JSON}")


if __name__ == "__main__":
    main()
