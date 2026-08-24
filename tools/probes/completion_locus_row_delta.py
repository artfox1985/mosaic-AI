#!/usr/bin/env python
"""PREREG_completion_bottleneck_locus.md par.5: die sekundaere Locus-Frage.

Primaermetrik: Delta = Kurzanteil(R1-2) - Kurzanteil(R4-5) je Arm, aus
`paired_arena_env_imm_netvnet.json` + `..._swap.json` (dasselbe Netz auf
beiden Seiten, verschiedene per-Seite-Specs: `champion_imm_a02` = Arm M,
`champion_frozen` = Arm R -- der Gegner ist in BEIDEN Armen derselbe
eingefrorene Champion, siehe par.4).

Eigenstaendiges Skript statt Aenderung an `row_preference_probe.py`: jene
Datei hatte densselben Seiten-Labelling-Fehler wie `penalty_track_probe.py`
(model==model_b bestaetigt "Champion beidseitig", labelt aber BEIDE Seiten
gleich, obwohl spec_a/spec_b zwei verhaltensverschiedene Agenten sind) und
war von einer anderen, inzwischen beendeten Sitzung als Fix-Ziel reserviert
-- reine Lesefunktionen (`row_choices_from_log`, `PATTERNS`,
`plate_points_from_arena.partien`) werden importiert, nicht veraendert.

Auswertung auf BLOCK-Ebene (je Partie, dann ueber Partien gebootstrapt),
wie in par.5 vorgeschrieben.
"""
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "probes"))

from row_preference_probe import row_choices_from_log  # noqa: E402
from plate_points_from_arena import partien  # noqa: E402

EVAL = ROOT / "evaluations"
OUT_JSON = EVAL / "completion_locus_row_delta.json"

RNG = np.random.default_rng(20260824)
N_BOOT = 1000


def label_for_spec(spec_path):
    s = str(spec_path)
    if "imm_a02" in s:
        return "M_alpha0.2"
    if "frozen" in s:
        return "R_frozen"
    return f"unbekannt:{s}"


def collect_per_game_shares(paths):
    """{label: [(seed, kurz_r12, n_r12, kurz_r45, n_r45), ...]}"""
    out = defaultdict(list)
    for p in paths:
        d = json.load(open(p, encoding="utf-8"))
        assert d.get("model") == d.get("model_b"), f"{p.name}: model != model_b"
        lab_a = label_for_spec(d["spec_a"])
        lab_b = label_for_spec(d["spec_b"])
        for sp in partien(p, None):
            seed = sp.get("game_seed")
            log = sp.get("log") or []
            choices = row_choices_from_log(log)
            by_name = defaultdict(list)
            for rnd, name, row in choices:
                by_name[name].append((rnd, row))
            for name, lab in (("NetzA", lab_a), ("NetzB", lab_b)):
                rows = by_name.get(name, [])
                r12 = [row for rnd, row in rows if rnd in (1, 2)]
                r45 = [row for rnd, row in rows if rnd in (4, 5)]
                kurz12 = sum(1 for r in r12 if r in (1, 2, 3))
                kurz45 = sum(1 for r in r45 if r in (1, 2, 3))
                out[lab].append((seed, kurz12, len(r12), kurz45, len(r45), p.name))
    return out


def share(kurz, n):
    return kurz / n if n else None


def delta_point_estimate(rows):
    tot_kurz12 = sum(r[1] for r in rows)
    tot_n12 = sum(r[2] for r in rows)
    tot_kurz45 = sum(r[3] for r in rows)
    tot_n45 = sum(r[4] for r in rows)
    s12 = share(tot_kurz12, tot_n12)
    s45 = share(tot_kurz45, tot_n45)
    delta = (s12 - s45) if (s12 is not None and s45 is not None) else None
    return s12, s45, delta, tot_n12, tot_n45


def block_bootstrap_delta(rows, n_boot=N_BOOT):
    n = len(rows)
    deltas = []
    idx_all = np.arange(n)
    for _ in range(n_boot):
        pick = RNG.choice(idx_all, size=n, replace=True)
        sub = [rows[i] for i in pick]
        _, _, d, n12, n45 = delta_point_estimate(sub)
        if d is not None and n12 >= 5 and n45 >= 5:
            deltas.append(d)
    if not deltas:
        return None
    arr = np.array(deltas)
    return dict(mean=float(arr.mean()), p2_5=float(np.percentile(arr, 2.5)),
                p97_5=float(np.percentile(arr, 97.5)), n_boot=len(arr))


def main():
    paths = [EVAL / "paired_arena_env_imm_netvnet.json",
             EVAL / "paired_arena_env_imm_netvnet_swap.json"]
    for p in paths:
        assert p.exists(), f"fehlt: {p}"

    per_label = collect_per_game_shares(paths)
    result = {}
    for lab, rows in sorted(per_label.items()):
        s12, s45, delta, n12, n45 = delta_point_estimate(rows)
        boot = block_bootstrap_delta(rows)
        result[lab] = dict(
            n_partien=len(rows),
            kurzanteil_R1_2=round(s12, 4) if s12 is not None else None,
            kurzanteil_R4_5=round(s45, 4) if s45 is not None else None,
            delta=round(delta, 4) if delta is not None else None,
            delta_block_bootstrap_95ci=boot,
            n_zuege_R1_2=n12, n_zuege_R4_5=n45,
        )

    dm = result.get("M_alpha0.2", {}).get("delta")
    dr = result.get("R_frozen", {}).get("delta")
    if dm is None or dr is None:
        lesart = "KEIN_VERDIKT -- ein Arm fehlt"
    else:
        diff = dm - dr
        if diff >= 0.05:
            lesart = f"SUCH-LESART (Delta_M - Delta_R = {diff:+.4f} >= +0,05)"
        elif diff < 0.02:
            lesart = f"ZIEL-LESART, SCHWACHE BESTAETIGUNG nach par.1a-Amendment (Delta_M - Delta_R = {diff:+.4f} < +0,02)"
        else:
            lesart = f"GRENZFALL (Delta_M - Delta_R = {diff:+.4f}, zwischen 0,02 und 0,05) -- Nutzer-Entscheid"

    out = dict(je_arm=result, delta_m_minus_delta_r=round(dm - dr, 4) if (dm is not None and dr is not None) else None,
              lesart=lesart,
              meta=dict(quelle=[p.name for p in paths],
                       hinweis="Delta = Kurzanteil(R1-2) - Kurzanteil(R4-5), "
                              "Kurzanteil = Anteil Draft-Ziele auf Musterreihe 1-3. "
                              "Bestandswerte: Champion ~0 pp, Heuristik-Lehrer +12,6 pp."))
    OUT_JSON.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"\n-> {OUT_JSON}")


if __name__ == "__main__":
    main()
