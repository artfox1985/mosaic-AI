# -*- coding: utf-8 -*-
"""
Mosaic-AI -- Runde-5-Value-Kalibrierung, KRITERIENWEISE aufgeschluesselt
(2026-08-30)
============================================================================

Warum diese Sonde ueberhaupt gebaut wurde
-----------------------------------------
`tools/r5_value_calibration.py` misst EINE Steigung je Kopf: wie stark
reagiert der Value-Kopf auf einen Wertungsplatten-Tausch, gemessen an der
exakten Alpha-Beta-Marge (`round5.rs`). Die Zahl (b05: 0,0886) ist ein
AGGREGAT ueber alle acht Kriterien. Daraus wurde gefolgert, der Kopf
unterbiete den Plattenlohn und baue deshalb keine Spalten -- aber eine
Gesamtsteigung kann nicht zwischen

  (a) "der Kopf ist speziell fuer Kriterium 1 (vertikale Reihen = Spalten)
      taub" -- spaltenblind, und
  (b) "der Kopf reagiert auf ALLE Wertungsplatten gleichmaessig schwach"
      -- plattensensitiv-schwach, was mit gutem Spaltenbau vereinbar ist
      (wer nach der Dreiecks-Einhuellenden baut, bekommt wertvolle Spalten
      ohnehin, und muss auf Plattenwechsel gar nicht stark reagieren)

unterscheiden. Genau das trennt diese Sonde.

Messanordnung (erbt Ground Truth und Modellpfad unveraendert)
-------------------------------------------------------------
Alle tragenden Bausteine werden aus `tools/r5_value_calibration.py`
IMPORTIERT, nicht kopiert (kein Logik-Fork):
`ab_value_for_combo` (exakte Marge via `round5.rs`), `fit_curve` /
`local_expected_delta_winprob` (empirische Punkte->Sieg-Kennlinie),
`load_torch_model` / `raw_value_points_torch` (Torch-Forward-Pass, kuerzt
Planes seit 2026-08-30 auf die Kanalzahl des Modells, Alt-Modelle also
messbar), `value_to_win_prob`, `points_to_pts`, `select_round5_states`.

Der Unterschied liegt allein in der KOMBINATIONSMENGE und der Auswertung:

1. Statt 6 repraesentativer Kombinationen laufen ALLE 32 gueltigen
   3er-Kombinationen je Zustand (`scoring_tile_sensitivity.all_valid_combos`).
   Der Grund ist nicht "mehr ist besser", sondern Balance: ueber alle 32
   kommt JEDES der acht Kriterien exakt 12-mal vor, und die
   Indikatormatrix hat vollen Spaltenrang 8 (in dieser Sitzung geprueft).
   Nur so haben alle acht Steigungen dieselbe Praezision -- Voraussetzung
   dafuer, Kriterium 1 ueberhaupt gegen die anderen stellen zu duerfen.
   Mit den 6 Kombinationen des Bestandswerkzeugs waere die Frage nicht
   beantwortbar (mehrere Kriterien kaemen 0- bis 2-mal vor).

2. AUSWERTUNG A -- additive Zerlegung je Zustand. Fuer einen festen
   Zustand s liegen 32 Werte vor (exakte Marge `ab`, Modell-Gewinnprozent,
   Modell-Punktekopf). Angepasst wird je Zustand und je Groesse

       V(c) = sum_k beta_k * 1[k in c]      (8 Parameter, KEIN Achsenabschnitt)

   Kein Achsenabschnitt ist noetig und auch nicht schaetzbar: jede gueltige
   Kombination hat genau 3 Kriterien, der Einsvektor liegt also exakt in der
   Spaltenhuelle (1 = X @ (1/3)). Eine additive Grundlast B des Zustands
   verteilt sich dadurch als B/3 gleichmaessig auf alle acht Koeffizienten
   und faellt beim ZENTRIEREN (beta_k - mean_j beta_j) exakt heraus. Genau
   dieses Zentrieren wird angewandt, auf BEIDEN Seiten identisch -- sonst
   erzeugte die stark streuende Grundlast (ab_value streut ueber die
   Zustaende um Dutzende Punkte) eine Scheinkorrelation.

   Die Zerlegung ist eine NAEHERUNG: `ab_value` ist ein Minimax-Wert, also
   ein Maximum ueber Strategien und damit in den Kriteriengewichten konvex,
   nicht exakt additiv. Wie gut die Naeherung traegt, wird als R2 der
   additiven Anpassung je Zustand und Groesse mitberichtet (Feld
   `additive_fit_r2`), damit die Zerlegung nicht ungeprueft geglaubt wird.

3. AUSWERTUNG B -- Tausch innerhalb eines Ausschluss-Paares
   (annahmefrei, ohne Zerlegung). Die vier Wertungsplatten sind physisch
   zweiseitig (`MUTUALLY_EXCLUSIVE_PAIRS = [(0,7),(6,3),(4,1),(2,5)]`).
   Fuer jedes Paar (A,B) gibt es je Zustand 12 Kombinationspaare, die sich
   NUR darin unterscheiden, dass A durch B ersetzt ist. Der Kontrast
   V(c mit B) - V(c mit A) isoliert damit die Differenz zweier Kriterien
   ohne jede Additivitaets-Annahme. Fuer die Leitfrage ist das Paar (4,1)
   der Schluesselkontrast: Kriterium 1 (vertikale Reihen, 7 Pkt je volle
   Spalte) gegen Kriterium 4 (aeussere Felder).

   Ein EINZELNES Kriterium ohne Partnerwechsel laesst sich mit gueltigen
   Kombinationen prinzipiell nicht isolieren: jede gueltige Kombination
   traegt genau 3 Kriterien aus 3 verschiedenen Paaren, die symmetrische
   Differenz zweier Kombinationen ist also immer mindestens 2. Deshalb
   diese zwei Auswertungen nebeneinander statt einer einzigen.

4. Standardfehler: Auswertung A regressiert ueber ZUSTAENDE (je Kriterium
   ein Punkt je Zustand, unabhaengig) -- gewoehnlicher OLS-Fehler.
   Auswertung B poolt 12 Kontraste je Zustand, die untereinander
   korreliert sind; dort wird ein zustands-geclusterter (CR1) Fehler
   berichtet, nicht der naive (Memory `feedback_arena_block_correlation`:
   Paar-Fehler werden sonst massiv unterschaetzt).

Kosten: die exakte Ground Truth (`ab_value`) ist MODELLUNABHAENGIG --
`round5.rs` kurzschliesst das Netz vollstaendig. Die 32 x n_states
Alpha-Beta-Aufrufe fallen daher EINMAL an und werden von allen gemessenen
Modellen geteilt; je Modell kommen nur die billigen Torch-Vorwaertspaesse
dazu.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import pickle
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "engine", "py"))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import torch  # noqa: E402

import scoring_tile_sensitivity as sts  # noqa: E402
import r5_value_calibration as r5  # noqa: E402
from neural_net import state_to_tensor, state_to_planes  # noqa: E402


def model_flat_features(model):
    """Erwartete Laenge des FLACHEN Eingabevektors, abgelesen an der ersten
    Linear-Schicht des flachen Zweigs ([out, in]). None, wenn keine gefunden
    wird."""
    branch = getattr(model, "flat_branch", None)
    modules = branch.modules() if branch is not None else model.modules()
    for mod in modules:
        if isinstance(mod, torch.nn.Linear):
            return mod.weight.shape[1]
    return None


def raw_value_points_truncated(model, encoder: str, state: dict, combo) -> tuple:
    """Wie `r5.raw_value_points_torch`, ZUSAETZLICH mit Kuerzung des FLACHEN
    Vektors auf die vom Modell erwartete Laenge.

    Das Bestandswerkzeug kuerzt seit 2026-08-30 nur die PLANES (79 heute,
    v21 kennt 76). v21 hat aber auch den flachen Vektor kleiner: 708 gegen
    heute 714 -- ohne diese zweite Kuerzung bricht der Vorwaertspass mit
    "mat1 and mat2 shapes cannot be multiplied (1x714 and 708x512)"
    (in dieser Sitzung reproduziert).

    Dieselbe Begruendung wie planes-seitig, in dieser Sitzung an der Quelle
    geprueft: die sechs neuen flachen Merkmale (`col_f_max`) wurden in
    Commit 29fb1f1 ("6 col_f_max ans Ende des flachen Blocks", INPUT_SIZE
    708 -> 714) HINTEN angehaengt, die vorderen 708 Werte sind also
    bedeutungsgleich. NUR kuerzen, nie auffuellen: erwartet das Modell MEHR
    als die Eingabe liefert, bleibt es beim harten Fehler."""
    s = dict(state)
    s["scoring_tile_ids"] = list(combo)
    x_flat = state_to_tensor(s).unsqueeze(0)
    want_flat = model_flat_features(model)
    if want_flat is not None and want_flat < x_flat.shape[1]:
        x_flat = x_flat[:, :want_flat]
    with torch.no_grad():
        if encoder == "2d":
            x_planes = state_to_planes(s).unsqueeze(0)
            want = r5._model_plane_channels(model)
            if want is not None and want < x_planes.shape[1]:
                x_planes = x_planes[:, :want, :, :]
            out = model(x_planes, x_flat)
        else:
            out = model(x_flat)
    return r5.value_to_win_prob(float(out[1].squeeze().item())), r5.points_to_pts(float(out[3].squeeze().item()))


CRITERION_NAMES = {
    0: "horizontal rows (3 pts per full row)",
    1: "vertical rows / COLUMNS (7 pts per full column)",
    2: "diagonals (10 pts, max 2x)",
    3: "wildcard cells (2 pts each when all filled)",
    4: "outer cells (1 pt per tile on the dome border)",
    5: "corner tiles (3/8 pts per corner dome tile)",
    6: "special cells (-3 pts per empty special cell)",
    7: "colorful rows (4 pts per row with >=5 colors)",
}


# -- Regressions-Bausteine mit Standardfehler ------------------------------

def ols_with_stderr(x, y, clusters=None):
    """OLS y = a + b*x mit Achsenabschnitt. Gibt Steigung, Standardfehler,
    t-Wert, R2 und n zurueck. Ist `clusters` gesetzt (eine Gruppenkennung je
    Beobachtung), wird ein zustands-geclusterter CR1-Fehler statt des naiven
    berechnet -- Beobachtungen desselben Zustands sind korreliert."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    n = int(len(x))
    if n < 3 or np.std(x) == 0:
        return {"slope": None, "intercept": None, "stderr": None, "t": None,
                "r2": None, "n": n, "note": "entartet (n<3 oder std(x)=0)"}
    X = np.column_stack([np.ones(n), x])
    xtx_inv = np.linalg.inv(X.T @ X)
    beta = xtx_inv @ (X.T @ y)
    resid = y - X @ beta
    ss_res = float(resid @ resid)
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")

    if clusters is None:
        var_beta = xtx_inv * (ss_res / (n - 2))
        n_clusters = None
    else:
        clusters = np.asarray(clusters)
        uniq = np.unique(clusters)
        n_clusters = int(len(uniq))
        meat = np.zeros((2, 2))
        for g in uniq:
            m = clusters == g
            xg = X[m]
            ug = resid[m]
            s = xg.T @ ug
            meat += np.outer(s, s)
        # CR1-Kleinstichprobenkorrektur (Cameron/Miller-Standard).
        corr = (n_clusters / max(1, n_clusters - 1)) * ((n - 1) / max(1, n - 2))
        var_beta = corr * (xtx_inv @ meat @ xtx_inv)

    stderr = float(math.sqrt(max(0.0, var_beta[1, 1])))
    slope = float(beta[1])
    return {
        "slope": slope, "intercept": float(beta[0]), "stderr": stderr,
        "t": (slope / stderr) if stderr > 0 else None,
        "ci95": [slope - 1.96 * stderr, slope + 1.96 * stderr] if stderr > 0 else None,
        "r2": float(r2), "n": n, "n_clusters": n_clusters,
    }


def ols_design_cluster(X, y, clusters):
    """OLS mit beliebiger Designmatrix und zustands-geclustertem CR1-Fehler.
    Gibt Koeffizienten, Standardfehler und t-Werte zurueck. Wird fuer den
    Wechselwirkungstest gebraucht (dort ist die Designmatrix dreispaltig)."""
    X = np.asarray(X, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    n, p = X.shape
    xtx_inv = np.linalg.inv(X.T @ X)
    beta = xtx_inv @ (X.T @ y)
    resid = y - X @ beta
    clusters = np.asarray(clusters)
    uniq = np.unique(clusters)
    g = len(uniq)
    meat = np.zeros((p, p))
    for c in uniq:
        m = clusters == c
        s = X[m].T @ resid[m]
        meat += np.outer(s, s)
    corr = (g / max(1, g - 1)) * ((n - 1) / max(1, n - p))
    var_beta = corr * (xtx_inv @ meat @ xtx_inv)
    se = np.sqrt(np.maximum(0.0, np.diag(var_beta)))
    return beta, se, g, n


def interaction_tests(per_criterion_rows, curve):
    """DER Test zur Leitfrage: ist die Steigung von Kriterium k eine ANDERE als
    die der uebrigen sieben?

    Acht getrennte Regressionen nebeneinander zu stellen beantwortet das nicht
    -- ihre Punkte stammen aus DENSELBEN 24 Zustaenden und sind deshalb
    korreliert; ein Augenschein-Vergleich zweier Steigungen mit je eigenem
    Fehler hat keinen Test dahinter. Stattdessen EINE gepoolte Regression ueber
    alle 8 x n_states Beobachtungen

        y = a + b*x + c*(x * 1[Kriterium == k])

    mit zustands-geclustertem Fehler. `c` IST die gesuchte Groesse: um wieviel
    die Steigung von Kriterium k von der der anderen sieben abweicht, mit
    t-Wert. Ein spaltenblinder Kopf muesste bei k=1 ein deutlich NEGATIVES `c`
    zeigen; gleichmaessige Daempfung heisst `c` nahe 0 fuer alle acht."""
    out = {}
    for head in ("value_head", "points_head"):
        per_head = {}
        for k in range(8):
            xs, ys, dummies, clusters = [], [], [], []
            for r in per_criterion_rows:
                for j in range(8):
                    expected = r5.local_expected_delta_winprob(
                        curve["a"], curve["b"], r["ab_ref"], r["true_effect_pts"][j])
                    if head == "value_head":
                        y = r["model_value_effect_winprob"][j]
                    else:
                        y = r5.local_expected_delta_winprob(
                            curve["a"], curve["b"], r["ab_ref"], r["model_points_effect_pts"][j])
                    xs.append(expected)
                    ys.append(y)
                    dummies.append(1.0 if j == k else 0.0)
                    clusters.append(r["state_index_in_eval_set"])
            xs = np.asarray(xs)
            dummies = np.asarray(dummies)
            X = np.column_stack([np.ones(len(xs)), xs, xs * dummies])
            beta, se, g, n = ols_design_cluster(X, ys, clusters)
            per_head[str(k)] = {
                "criterion": k, "name": CRITERION_NAMES[k],
                "slope_others": float(beta[1]), "slope_others_se": float(se[1]),
                "slope_difference": float(beta[2]), "slope_difference_se": float(se[2]),
                "t": float(beta[2] / se[2]) if se[2] > 0 else None,
                "slope_criterion": float(beta[1] + beta[2]),
                "n_obs": int(n), "n_clusters": int(g),
            }
        out[head] = per_head
    return out


def criterion_design_matrix(combos):
    """[n_combos, 8] Indikatormatrix: Zeile c, Spalte k = 1, wenn Kriterium k
    in Kombination c aktiv ist."""
    X = np.zeros((len(combos), 8), dtype=np.float64)
    for i, combo in enumerate(combos):
        for k in combo:
            X[i, int(k)] = 1.0
    return X


def decompose_centered(values, X):
    """Additive Zerlegung EINES Zustands: kleinste Quadrate ohne
    Achsenabschnitt (siehe Moduldoku Punkt 2), anschliessend ueber die acht
    Kriterien zentriert. Gibt (zentrierte Koeffizienten [8], R2 der additiven
    Anpassung) zurueck."""
    v = np.asarray(values, dtype=np.float64)
    beta, *_ = np.linalg.lstsq(X, v, rcond=None)
    fitted = X @ beta
    ss_res = float(np.sum((v - fitted) ** 2))
    ss_tot = float(np.sum((v - v.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return beta - float(beta.mean()), r2


# -- Ground Truth einmal fuer alle Modelle ---------------------------------

def load_cache(path):
    """Zwischenspeicher der exakten Ground Truth. Ohne ihn kostet jeder Abbruch
    den GESAMTEN Lauf: am 2026-08-30 wurde ein Lauf nach 616 von 768
    Alpha-Beta-Aufrufen (43 Minuten) beendet, ohne dass ein einziger Wert
    ueberlebt haette. Die Werte sind deterministisch und modellunabhaengig,
    also gefahrlos wiederverwendbar -- der Schluessel traegt Zustandsindex,
    Kombination, Seed, sims und c_puct, damit kein Wert unter geaenderten
    Bedingungen recycelt wird."""
    if not path or not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_cache(path, cache):
    if not path:
        return
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cache, f)
    os.replace(tmp, path)


def collect_ground_truth(states, combos, model_path_for_api, sims, c_puct, seed,
                          cache_path=None):
    """32 (bzw. len(combos)) Alpha-Beta-Aufrufe je Zustand. MODELLUNABHAENGIG
    (`round5.rs` kurzschliesst das Netz), wird daher einmal erhoben und von
    allen Modellen geteilt. Schreibt nach jedem Zustand in den Zwischenspeicher
    (siehe `load_cache`)."""
    table = []
    n_calls = 0
    n_from_cache = 0
    cache = load_cache(cache_path)
    t_start = time.time()
    for si, (record_index, rec) in enumerate(states):
        state = rec["state"]
        ref_combo = tuple(sorted(state["scoring_tile_ids"]))
        ab_by_combo = {}
        for combo in combos:
            key = (f"{record_index}|{','.join(str(x) for x in sorted(combo))}"
                   f"|s{seed + si}|n{sims}|c{c_puct}")
            if key in cache:
                ab = cache[key]
                n_from_cache += 1
                fresh = False
            else:
                ab = r5.ab_value_for_combo(state, combo, model_path_for_api, sims, c_puct, seed + si)
                n_calls += 1
                cache[key] = ab
                fresh = True
            if ab is not None:
                ab_by_combo[tuple(sorted(combo))] = float(ab)
            if fresh and n_calls % 8 == 0:
                el = time.time() - t_start
                print(f"    [ground truth] {n_calls} neue Alpha-Beta-Aufrufe "
                      f"(+{n_from_cache} aus dem Zwischenspeicher), {el:.0f}s "
                      f"({el / max(1, n_calls):.2f}s/Aufruf)", flush=True)
        save_cache(cache_path, cache)
        if ref_combo not in ab_by_combo:
            print(f"  Zustand {si} (idx={record_index}): Referenz-Kombination {ref_combo} "
                  f"lieferte kein ab_value -- Zustand uebersprungen", flush=True)
            continue
        if len(ab_by_combo) < len(combos):
            print(f"  Zustand {si} (idx={record_index}): nur {len(ab_by_combo)}/{len(combos)} "
                  f"Kombinationen mit ab_value -- Zustand uebersprungen (Zerlegung braucht "
                  f"die volle balancierte Menge)", flush=True)
            continue
        table.append({
            "state_index_in_eval_set": record_index,
            "ref_combo": list(ref_combo),
            "ab_ref": ab_by_combo[ref_combo],
            "ab_by_combo": {",".join(str(x) for x in k): v for k, v in ab_by_combo.items()},
        })
        print(f"  Zustand {si} (eval_set idx={record_index}): ab_ref={ab_by_combo[ref_combo]:.1f}, "
              f"ab-Spanne ueber Kombinationen "
              f"{min(ab_by_combo.values()):.1f}..{max(ab_by_combo.values()):.1f}", flush=True)
    return table, n_calls


def model_response_table(pth_path, states, combos):
    """Torch-Vorwaertspass je (Zustand, Kombination): Gewinnprozent des
    Value-Kopfs und Punkte des Punkte-Kopfs. Billig gegenueber Alpha-Beta."""
    model, encoder = r5.load_torch_model(pth_path)
    out = {}
    for si, (record_index, rec) in enumerate(states):
        state = rec["state"]
        per_combo = {}
        for combo in combos:
            per_combo[tuple(sorted(combo))] = raw_value_points_truncated(model, encoder, state, combo)
        out[record_index] = per_combo
    return out, encoder, {"plane_channels": r5._model_plane_channels(model),
                          "flat_features": model_flat_features(model)}


# -- Auswertung A: additive Zerlegung je Kriterium --------------------------

def per_criterion_slopes(ground_truth, model_table, combos, curve):
    X = criterion_design_matrix(combos)
    keys = [tuple(sorted(c)) for c in combos]

    rows = []
    for entry in ground_truth:
        idx = entry["state_index_in_eval_set"]
        if idx not in model_table:
            continue
        ab_ref = entry["ab_ref"]
        ab_map = {tuple(int(x) for x in k.split(",")): v for k, v in entry["ab_by_combo"].items()}
        ab_vec = [ab_map[k] for k in keys]
        value_vec = [model_table[idx][k][0] for k in keys]
        points_vec = [model_table[idx][k][1] for k in keys]

        true_c, true_fit_r2 = decompose_centered(ab_vec, X)
        value_c, value_fit_r2 = decompose_centered(value_vec, X)
        points_c, points_fit_r2 = decompose_centered(points_vec, X)

        rows.append({
            "state_index_in_eval_set": idx, "ab_ref": ab_ref,
            "true_effect_pts": true_c.tolist(),
            "model_value_effect_winprob": value_c.tolist(),
            "model_points_effect_pts": points_c.tolist(),
            "additive_fit_r2": {"ab_value": true_fit_r2, "value_head": value_fit_r2,
                                 "points_head": points_fit_r2},
        })

    per_criterion = {}
    pooled_x, pooled_y, pooled_yp, pooled_cluster = [], [], [], []
    for k in range(8):
        xs, ys, yps, true_pts = [], [], [], []
        for r in rows:
            expected = r5.local_expected_delta_winprob(
                curve["a"], curve["b"], r["ab_ref"], r["true_effect_pts"][k])
            model_points_winprob = r5.local_expected_delta_winprob(
                curve["a"], curve["b"], r["ab_ref"], r["model_points_effect_pts"][k])
            xs.append(expected)
            ys.append(r["model_value_effect_winprob"][k])
            yps.append(model_points_winprob)
            true_pts.append(r["true_effect_pts"][k])
            pooled_x.append(expected)
            pooled_y.append(r["model_value_effect_winprob"][k])
            pooled_yp.append(model_points_winprob)
            pooled_cluster.append(r["state_index_in_eval_set"])
        per_criterion[k] = {
            "criterion": k, "name": CRITERION_NAMES[k],
            "value_head": ols_with_stderr(xs, ys),
            "points_head": ols_with_stderr(xs, yps),
            "true_effect_pts_mean": float(np.mean(true_pts)),
            "true_effect_pts_sd": float(np.std(true_pts, ddof=1)) if len(true_pts) > 1 else 0.0,
            "true_effect_pts_absmean": float(np.mean(np.abs(true_pts))),
            "expected_winprob_sd": float(np.std(xs, ddof=1)) if len(xs) > 1 else 0.0,
            "n_states": len(xs),
        }

    pooled = {
        "value_head": ols_with_stderr(pooled_x, pooled_y, clusters=pooled_cluster),
        "points_head": ols_with_stderr(pooled_x, pooled_yp, clusters=pooled_cluster),
    }
    fit_r2 = {
        key: float(np.mean([r["additive_fit_r2"][key] for r in rows]))
        for key in ("ab_value", "value_head", "points_head")
    } if rows else {}
    return per_criterion, pooled, rows, fit_r2


# -- Auswertung B: Tausch innerhalb eines Ausschluss-Paares -----------------

def pair_swap_slopes(ground_truth, model_table, combos, curve):
    valid = {tuple(sorted(c)) for c in combos}
    out = {}
    for (a, b) in sts.MUTUALLY_EXCLUSIVE_PAIRS:
        xs, ys, yps, clusters, true_pts = [], [], [], [], []
        for entry in ground_truth:
            idx = entry["state_index_in_eval_set"]
            if idx not in model_table:
                continue
            ab_map = {tuple(int(x) for x in k.split(",")): v for k, v in entry["ab_by_combo"].items()}
            for combo in sorted(valid):
                if a not in combo:
                    continue
                swapped = tuple(sorted([x for x in combo if x != a] + [b]))
                if swapped not in valid or swapped not in ab_map or combo not in ab_map:
                    continue
                true_delta = ab_map[swapped] - ab_map[combo]
                expected = r5.local_expected_delta_winprob(
                    curve["a"], curve["b"], entry["ab_ref"], true_delta)
                v_from, p_from = model_table[idx][combo]
                v_to, p_to = model_table[idx][swapped]
                model_points_winprob = r5.local_expected_delta_winprob(
                    curve["a"], curve["b"], entry["ab_ref"], p_to - p_from)
                xs.append(expected)
                ys.append(v_to - v_from)
                yps.append(model_points_winprob)
                clusters.append(idx)
                true_pts.append(true_delta)
        out[f"{a}->{b}"] = {
            "swap": [a, b],
            "meaning": f"{CRITERION_NAMES[a]}  ==>  {CRITERION_NAMES[b]}",
            "value_head": ols_with_stderr(xs, ys, clusters=clusters),
            "points_head": ols_with_stderr(xs, yps, clusters=clusters),
            "true_delta_pts_absmean": float(np.mean(np.abs(true_pts))) if true_pts else None,
            "true_delta_pts_sd": float(np.std(true_pts, ddof=1)) if len(true_pts) > 1 else 0.0,
            "n_contrasts": len(xs),
        }
    return out


# -- Aggregat-Gegenprobe gegen das Bestandswerkzeug -------------------------

def aggregate_replication(ground_truth, model_table, combos, curve):
    """Repliziert die Auswertung von `r5_value_calibration.py` (Referenz-
    Kombination gegen alle uebrigen, gepoolt) auf DIESER Kombinationsmenge --
    Gegenprobe, dass die Zerlegung nicht an einer anderen Grundgesamtheit
    haengt als die berichtete Gesamtsteigung 0,0886."""
    xs, ys, yps, clusters = [], [], [], []
    for entry in ground_truth:
        idx = entry["state_index_in_eval_set"]
        if idx not in model_table:
            continue
        ref = tuple(entry["ref_combo"])
        ab_map = {tuple(int(x) for x in k.split(",")): v for k, v in entry["ab_by_combo"].items()}
        v_ref, p_ref = model_table[idx][ref]
        for combo, ab in ab_map.items():
            if combo == ref:
                continue
            true_delta = ab - entry["ab_ref"]
            expected = r5.local_expected_delta_winprob(curve["a"], curve["b"], entry["ab_ref"], true_delta)
            v_t, p_t = model_table[idx][combo]
            xs.append(expected)
            ys.append(v_t - v_ref)
            yps.append(r5.local_expected_delta_winprob(curve["a"], curve["b"], entry["ab_ref"], p_t - p_ref))
            clusters.append(idx)
    return {
        "value_head": ols_with_stderr(xs, ys, clusters=clusters),
        "points_head": ols_with_stderr(xs, yps, clusters=clusters),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval-set", default="evaluations/frozen_eval_set.pkl")
    ap.add_argument("--models", nargs="+", default=["models/alphazero_v22-b05.pth"])
    ap.add_argument("--model-path-for-api", default="models/alphazero_v22-b05.onnx",
                    help="beliebiger gueltiger ONNX-Pfad (API-Zwang, fuer Runde-5-Zustaende "
                         "inhaltlich nie benutzt -- round5.rs-Kurzschluss)")
    ap.add_argument("--sims", type=int, default=400)
    ap.add_argument("--c-puct", type=float, default=1.5)
    ap.add_argument("--n-states", type=int, default=24)
    ap.add_argument("--n-combos", type=int, default=32,
                    help="32 = alle gueltigen Kombinationen (balanciert, Rang 8). Kleinere "
                         "Werte machen die kriterienweise Zerlegung unbalanciert oder singulaer.")
    ap.add_argument("--curve-n-states", type=int, default=233)
    ap.add_argument("--curve-json", default=None,
                    help="Statt die Kennlinie neu zu fitten (233 Alpha-Beta-Aufrufe, ~16 min) "
                         "eine bereits gemessene uebernehmen: Pfad auf ein Artefakt mit "
                         "'curve' oder 'summary.curve'. Nur a und b gehen in die Rechnung ein.")
    ap.add_argument("--cache", default=None,
                    help="Zwischenspeicher fuer die exakte Ground Truth (JSON). Ein "
                         "abgebrochener Lauf verliert damit nur den laufenden Zustand "
                         "statt aller bisherigen Aufrufe.")
    ap.add_argument("--seed", type=int, default=1000)
    ap.add_argument("--out", default="evaluations/artifacts/r5_calibration_per_criterion.json")
    args = ap.parse_args()

    wall_start = time.time()
    cpu_start = time.process_time()

    with open(args.eval_set, "rb") as f:
        data = pickle.load(f)
    records = data["records"]

    states = r5.select_round5_states(records, args.n_states)
    print(f"[per_criterion] {len(states)} Runde-5-Zustaende gewaehlt (gleicher Selektor/Seed "
          f"wie tools/r5_value_calibration.py).", flush=True)

    if args.n_combos >= 32:
        combos = sts.all_valid_combos()
    else:
        combos = sts.pick_representative_combos(args.n_combos)
    X = criterion_design_matrix(combos)
    rank = int(np.linalg.matrix_rank(X))
    counts = X.sum(axis=0).astype(int).tolist()
    print(f"[per_criterion] {len(combos)} Kombinationen, Indikator-Rang {rank}/8, "
          f"Vorkommen je Kriterium {counts}", flush=True)
    if rank < 8:
        raise SystemExit("Indikatormatrix hat nicht vollen Rang 8 -- kriterienweise Zerlegung "
                         "waere nicht identifiziert. Mehr Kombinationen waehlen.")

    if args.curve_json:
        with open(args.curve_json, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        curve = loaded.get("curve") or loaded.get("summary", {}).get("curve")
        if not curve or "a" not in curve or "b" not in curve:
            raise SystemExit(f"Keine verwertbare Kennlinie in {args.curve_json}")
        curve = dict(curve)
        curve["source"] = args.curve_json
        print(f"[per_criterion] Kennlinie UEBERNOMMEN aus {args.curve_json}: "
              f"a={curve['a']:.5f} b={curve['b']:.5f} "
              f"mcfadden_r2={curve.get('mcfadden_r2')} n={curve.get('n_points')}", flush=True)
        n_curve_calls = 0
    else:
        print("[per_criterion] Kennlinie wird gefittet (identischer Code/Substrat wie das "
              "Bestandswerkzeug) ...", flush=True)
        # `r5.fit_curve` selbst druckt nichts und braucht einen Alpha-Beta-Aufruf
        # je Record (233 Stueck, mehrere Minuten) -- ohne den folgenden Zaehler
        # waere der Lauf in dieser Phase stumm (CLAUDE.md "Lange Laeufe":
        # Fortschritt muss in den Hintergrundaufgaben SICHTBAR sein). Statt das
        # Bestandswerkzeug anzufassen, wird sein Modul-Global nur fuer die Dauer
        # des Fits durch einen zaehlenden Weiterreicher ersetzt.
        original_ab = r5.ab_value_for_combo
        curve_calls = {"n": 0}
        curve_start = time.time()

        def counting_ab(*call_args, **call_kwargs):
            curve_calls["n"] += 1
            if curve_calls["n"] % 16 == 0:
                el = time.time() - curve_start
                print(f"    [Kennlinie] {curve_calls['n']}/{args.curve_n_states} Aufrufe, "
                      f"{el:.0f}s ({el / curve_calls['n']:.2f}s/Aufruf)", flush=True)
            return original_ab(*call_args, **call_kwargs)

        r5.ab_value_for_combo = counting_ab
        try:
            curve = r5.fit_curve(records, args.model_path_for_api, args.sims, args.c_puct,
                                 args.curve_n_states, seed_base=args.seed + 500000)
        finally:
            r5.ab_value_for_combo = original_ab
        n_curve_calls = curve_calls["n"]
        print(f"[per_criterion] Kennlinie: a={curve['a']:.5f} b={curve['b']:.5f} "
              f"mcfadden_r2={curve['mcfadden_r2']:.3f} n={curve['n_points']}", flush=True)

    print(f"[per_criterion] Ground Truth: {len(states)} x {len(combos)} Alpha-Beta-Aufrufe "
          f"(modellunabhaengig, wird von allen Modellen geteilt) ...", flush=True)
    ground_truth, n_ab_calls = collect_ground_truth(
        states, combos, args.model_path_for_api, args.sims, args.c_puct, args.seed,
        cache_path=args.cache)
    print(f"[per_criterion] {len(ground_truth)} Zustaende mit vollstaendiger Ground Truth.", flush=True)

    per_model = {}
    for pth_path in args.models:
        print(f"\n=== Modell: {pth_path} ===", flush=True)
        model_table, encoder, shapes = model_response_table(pth_path, states, combos)
        per_criterion, pooled, rows, fit_r2 = per_criterion_slopes(
            ground_truth, model_table, combos, curve)
        swaps = pair_swap_slopes(ground_truth, model_table, combos, curve)
        agg = aggregate_replication(ground_truth, model_table, combos, curve)
        interactions = interaction_tests(rows, curve)

        print(f"  Encoder: {encoder} (Planes {shapes['plane_channels']}, flach "
              f"{shapes['flat_features']}); mittleres R2 der additiven Zerlegung: "
              f"ab_value={fit_r2.get('ab_value'):.3f} value={fit_r2.get('value_head'):.3f} "
              f"points={fit_r2.get('points_head'):.3f}", flush=True)
        print("  Kriterium | Steigung Value | SE     | t     | R2    | |wahre Wirkung| Pkt", flush=True)
        for k in range(8):
            e = per_criterion[k]["value_head"]
            s = "  n/a " if e["slope"] is None else f"{e['slope']: .4f}"
            se = "  n/a " if e["stderr"] is None else f"{e['stderr']:.4f}"
            tv = "  n/a " if e["t"] is None else f"{e['t']: .2f}"
            r2 = "  n/a " if e["r2"] is None else f"{e['r2']:.3f}"
            print(f"    k={k}     | {s}       | {se} | {tv} | {r2} | "
                  f"{per_criterion[k]['true_effect_pts_absmean']:.3f}", flush=True)
        print("  Wechselwirkungstest (Steigung von k MINUS Steigung der uebrigen sieben, "
              "geclustert je Zustand):", flush=True)
        for k in range(8):
            it = interactions["value_head"][str(k)]
            tv = "n/a" if it["t"] is None else f"{it['t']: .2f}"
            print(f"    k={k}: Differenz {it['slope_difference']: .4f} "
                  f"SE {it['slope_difference_se']:.4f} t {tv}", flush=True)
        for key, sw in swaps.items():
            e = sw["value_head"]
            print(f"  Tausch {key}: Steigung {e['slope']} SE(cluster) {e['stderr']} "
                  f"n={e['n']} Cluster={e['n_clusters']}", flush=True)
        print(f"  Aggregat-Gegenprobe (Referenz gegen alle): Value-Steigung "
              f"{agg['value_head']['slope']} SE(cluster) {agg['value_head']['stderr']}", flush=True)

        per_model[pth_path] = {
            "encoder": encoder,
            "input_shapes": shapes,
            "additive_fit_r2_mean": fit_r2,
            "per_criterion": {str(k): v for k, v in per_criterion.items()},
            "pooled_over_criteria": pooled,
            "interaction_tests": interactions,
            "pair_swaps": swaps,
            "aggregate_replication": agg,
            "per_state_effects": rows,
        }

    wall = time.time() - wall_start
    cpu = time.process_time() - cpu_start
    result = {
        "tool": "tools/probes/r5_calibration_per_criterion.py",
        "created": "2026-08-30",
        "config": {
            "eval_set": args.eval_set, "models": args.models,
            "model_path_for_api": args.model_path_for_api,
            "sims": args.sims, "c_puct": args.c_puct,
            "n_states_requested": args.n_states, "n_states_used": len(ground_truth),
            "n_combos": len(combos), "combos": [list(c) for c in combos],
            "design_rank": rank, "criterion_counts": counts,
            "curve_n_states": args.curve_n_states, "seed": args.seed,
            "curve_json": args.curve_json, "cache": args.cache,
        },
        "criterion_names": CRITERION_NAMES,
        "curve": curve,
        # Die exakte Ground Truth wird MITGESCHRIEBEN: sie ist modellunabhaengig
        # und der teure Teil (32 Alpha-Beta-Aufrufe je Zustand). Wer die
        # Auswertung spaeter anders schneiden will, braucht damit keinen neuen
        # Rechenlauf.
        "ground_truth": ground_truth,
        "per_model": per_model,
        "laufzeit": {
            "wanduhr_s": wall,
            "cpu_s": cpu,
            "threads": {
                "rayon_num_threads_env": os.environ.get("RAYON_NUM_THREADS"),
                "cpu_count": os.cpu_count(),
                "note": "Alpha-Beta (round5.rs) laeuft je Aufruf sequenziell; die Maschine "
                        "trug waehrend der Messung parallel eine 12.000-Partien-Erzeugung "
                        "(vom Nutzer freigegeben; Messung ist deterministisch, nur langsamer).",
            },
            "n_alpha_beta_calls_fresh": n_ab_calls + n_curve_calls,
            "n_alpha_beta_calls_ground_truth_fresh": n_ab_calls,
            "n_alpha_beta_calls_curve_fresh": n_curve_calls,
            "s_je_alpha_beta_aufruf": wall / max(1, n_ab_calls + n_curve_calls),
        },
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print(f"\nErgebnis geschrieben nach {args.out} "
          f"(Wanduhr {wall:.0f}s, CPU {cpu:.0f}s)", flush=True)


if __name__ == "__main__":
    main()
