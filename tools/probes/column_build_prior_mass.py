# -*- coding: utf-8 -*-
"""Gate C / par.16.1 Sonde: Policy-Priormasse auf Spaltenbau-Aktionen.

Siehe evaluations/PREREG_gate_c_consumer_sweep.md par.16.1 fuer den Auftrag.
Ergebnis-Ablage: evaluations/probe_column_build_prior_mass.json.

NUR CPU, <=3 Faeden (harte Vorgabe des Koordinators) -- Env-Variablen MUESSEN
VOR dem torch/onnxruntime-Import gesetzt werden.
"""
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["OMP_NUM_THREADS"] = "2"
os.environ["MKL_NUM_THREADS"] = "2"

import glob
import json
import pickle
import sys
import time
from pathlib import Path

import numpy as np
import torch

torch.set_num_threads(1)
import onnxruntime as ort  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "engine" / "py"))

from neural_net import state_to_tensor, state_to_planes, action_to_id  # noqa: E402

CORPUS_GLOB = str(REPO / "data" / "ownership_corpus" / "selfplay_v21_own_k1_*.pkl")
# Nachzug 2026-08-29 (Fahrplan Phase 0.3): Modelle per CLI uebersteuerbar
# (name=pfad), Default = urspruengliche Messung (par.16.1). Die Alt-Modelle
# stammen aus der 77-Kanal-Aera und laufen am heutigen state_to_planes
# (79 Kanaele) NICHT mehr -- fuer Nachmessungen aktueller Netze --model
# setzen und gegen die protokollierten Alt-Werte vergleichen.
import sys as _sys  # noqa: E402

MODELS = {
    "b18_best": REPO / "models" / "alphazero_v21-b18_best.onnx",
    "champion": REPO / "models" / "alphazero_v21_2d_brierbest.onnx",
}
_cli_models = [a.split("=", 1) for a in _sys.argv[1:]
               if a.startswith("--model") is False and "=" in a]
if _cli_models:
    MODELS = {name: Path(p) for name, p in _cli_models}
OUT_JSON = REPO / "evaluations" / (
    "probe_column_build_prior_mass_heldout.json" if "--heldout" in _sys.argv
    else "probe_column_build_prior_mass.json")
if "--out" in _sys.argv:
    OUT_JSON = Path(_sys.argv[_sys.argv.index("--out") + 1])

SESS_OPTS = ort.SessionOptions()
SESS_OPTS.intra_op_num_threads = 2
SESS_OPTS.inter_op_num_threads = 1
SESS_OPTS.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL


def is_qualifying(rec):
    """Definition (siehe Bericht par.1): eine Drafting-Entscheidung 'dient
    einer offenen Spalte', wenn ihr aufgezeichnetes Policy-Ziel ein reines
    Demonstrations-One-Hot ist (self_play.rs::NetSelfPlayAgent::decide,
    Zweig `vorzug_kandidat` -- fuer den own_k1-Korpus loest die Vorzugskette
    `builder_drafting_preference` auf `column_build::preference_move`/`preference_dome_choice`
    auf, den Spaltenbauer) UND mehr als eine legale Aktion vorlag (schliesst
    den trivialen Ein-Aktion-Kurzschluss aus, der ebenfalls prob=1.0 liefert,
    aber keine Bauer-Entscheidung ist) UND es sich nicht um die Start-
    Kuppelplatzierung handelt (eigene Heuristik, `choose_start_placement`,
    NICHT Teil der Bauer-Kette) UND KEINE echte Suche gelaufen ist.

    Der letzte Punkt ist die Korrektur eines echten Fehlers, der in dieser
    Sitzung per Stichprobe gefunden wurde: bei kleinen Aktionsraeumen
    (`choose_dome_rotation` <=4, `bonus_chip`) kann `net_drafting_policy`s
    completed-Q-Softmax NUMERISCH auf exakt 1.0 saettigen, OHNE dass die
    Bauer-Kette beteiligt war -- 1512 von 10508 One-Hot-Saetzen in einer
    10-Datei-Stichprobe hatten trotzdem ein `root_q`-Feld (= echte Suche
    lief). `root_q`/`root_child_q` werden NUR bei echter Suche geschrieben
    (self_play.rs:1657-1664, `if let Some(rq) = d.root_q`) -- ihre
    Abwesenheit ist der einzige verlaessliche Beleg fuer eine Uebersteuerung
    (self_play.rs:1352-1358: Ein-Aktion-Kurzschluss UND Vorzug-Zweig liefern
    BEIDE `root_q=None`, `root_child_q=[]`; nur der Vorzug-Zweig zusaetzlich
    `len(valid_actions)>1`)."""
    pol = rec.get("policy") or []
    if len(pol) != 1:
        return False
    if abs(pol[0].get("prob", 0.0) - 1.0) > 1e-9:
        return False
    act = pol[0]["action"]
    if act.get("is_start"):
        return False
    if rec["state"].get("phase") != "drafting":
        return False
    if len(rec.get("valid_actions") or []) <= 1:
        return False
    if "root_q" in rec:
        return False  # echte Suche lief -> kein Bauer-Override, egal wie die Policy aussieht
    return True


def masked_softmax_mass(logits, valid_ids, chosen_id):
    legal_logits = logits[valid_ids]
    m = legal_logits.max()
    ex = np.exp(legal_logits - m)
    probs = ex / ex.sum()
    idx = valid_ids.index(chosen_id)
    return float(probs[idx])


def main():
    files = sorted(glob.glob(CORPUS_GLOB))
    # Held-out-Filter (Koordinator 2026-08-17): 87 der 100 k1-Dateien liegen in
    # v21-b18s TRAININGSSATZ. Ohne Filter misst die Sonde zu 87 % Wiedererkennung
    # von Trainingsdaten gegen einen Champion, der keine davon gesehen hat -- die
    # Zahl waere dann kein Guetevergleich, sondern ein Gedaechtnisvergleich.
    # Aufruf mit --heldout beschraenkt auf den Val-Split (fixer Shuffle 20260707
    # ueber die sortierte Gesamtliste, exakt wie neural_net.py ihn bildet).
    if "--heldout" in sys.argv:
        import random as _rnd
        _fen = [Path(f).name for f in glob.glob(str(REPO / "data" / "*.pkl"))
                if "v19wdlsw" not in Path(f).name]
        _kor = [Path(f).name for f in glob.glob(str(REPO / "data" / "ownership_corpus" / "*.pkl"))]
        _alle = sorted(_fen + _kor)
        _sh = list(_alle); _rnd.Random(20260707).shuffle(_sh)
        _val = set(_sh[:int(len(_alle) * 0.1)])
        files = [f for f in files if Path(f).name in _val]
        print(f"[info] --heldout: auf {len(files)} Val-Dateien beschraenkt", flush=True)
    print(f"[info] {len(files)} Korpus-Dateien gefunden", flush=True)

    sessions = {
        name: ort.InferenceSession(str(path), sess_options=SESS_OPTS,
                                    providers=["CPUExecutionProvider"])
        for name, path in MODELS.items()
    }

    # Kopf-Breite je Modell protokollieren (Regel-0-Pruefstelle: bestaetigt,
    # dass wir tatsaechlich die genannten zwei Checkpoints ansprechen).
    for name, sess in sessions.items():
        shapes = {o.name: o.shape for o in sess.get_outputs()}
        print(f"[info] {name}: policy-shape={shapes.get('policy')}", flush=True)

    t0 = time.time()
    n_total_records = 0
    n_qualifying = 0
    n_games = set()
    decisions = []  # eine Zeile je qualifizierender Entscheidung

    for fi, fp in enumerate(files):
        with open(fp, "rb") as f:
            data = pickle.load(f)
        n_total_records += len(data)

        batch_flat = []
        batch_planes = []
        batch_meta = []
        for rec in data:
            if not is_qualifying(rec):
                continue
            chosen = rec["policy"][0]["action"]
            chosen_id = action_to_id(chosen)
            valid_ids = sorted(set(action_to_id(a) for a in rec["valid_actions"]))
            if chosen_id not in valid_ids:
                # Sollte nach Konstruktion nie vorkommen (Training verlaesst
                # sich auf dieselbe Garantie, neural_net.py:1770-1776) --
                # defensiv uebersprungen statt stillschweigend verzerrt.
                continue
            n_qualifying += 1
            n_games.add(rec["game_id"])
            flat = np.asarray(state_to_tensor(rec["state"]), dtype=np.float32)
            planes = state_to_planes(rec["state"]).numpy().astype(np.float32)
            batch_flat.append(flat)
            batch_planes.append(planes)
            batch_meta.append({
                "game_id": rec["game_id"],
                "action_type": chosen.get("type"),
                "chosen_id": chosen_id,
                "valid_ids": valid_ids,
                "n_legal": len(valid_ids),
            })

        if not batch_meta:
            continue

        flat_arr = np.stack(batch_flat)
        planes_arr = np.stack(batch_planes)

        model_logits = {}
        for name, sess in sessions.items():
            out = sess.run(["policy"], {"planes": planes_arr, "state": flat_arr})[0]
            model_logits[name] = out

        for j, meta in enumerate(batch_meta):
            row = dict(meta)
            row["file"] = os.path.basename(fp)
            for name in MODELS:
                mass = masked_softmax_mass(model_logits[name][j], meta["valid_ids"], meta["chosen_id"])
                row[f"mass_{name}"] = mass
                row[f"ratio_{name}"] = mass * meta["n_legal"]  # mass / (1/n_legal)
            decisions.append(row)

        if (fi + 1) % 20 == 0:
            print(f"[info] {fi+1}/{len(files)} Dateien, {n_qualifying} qualifizierende Entscheidungen bisher, "
                  f"{time.time()-t0:.1f}s", flush=True)

    print(f"[info] fertig: {n_total_records} Rohsaetze, {n_qualifying} qualifizierende Entscheidungen, "
          f"{len(n_games)} Partien, {time.time()-t0:.1f}s", flush=True)

    # ── Aggregation ──────────────────────────────────────────────────────────
    def describe(values):
        a = np.asarray(values, dtype=np.float64)
        n = len(a)
        if n == 0:
            return {"n": 0}
        mean = float(a.mean())
        sd = float(a.std(ddof=1)) if n > 1 else 0.0
        se = sd / (n ** 0.5) if n > 1 else 0.0
        sorted_a = np.sort(a)
        median = float(np.median(a))
        return {
            "n": n, "mean": mean, "sd": sd, "se": se, "median": median,
            "p10": float(np.percentile(a, 10)), "p90": float(np.percentile(a, 90)),
            "min": float(sorted_a[0]), "max": float(sorted_a[-1]),
        }

    result = {
        "definition": (
            "Eine Drafting-Entscheidung 'dient einer offenen Spalte' <=> ihr "
            "aufgezeichnetes Policy-Ziel im own_k1-Korpus ist ein reines "
            "Demonstrations-One-Hot (prob=1.0 auf genau einer Aktion), das "
            "aus der Bauer-Vorzugskette stammt (self_play.rs::builder_drafting_preference, "
            "die fuer own_k1 auf column_build::preference_move / "
            "column_build::preference_dome_choice -- den Spaltenbauer -- aufloest), "
            "UND mehr als eine legale Aktion vorlag (schliesst den trivialen "
            "Ein-Aktion-Kurzschluss aus) UND es keine Start-Kuppelplatzierung "
            "ist (eigene, bauer-unabhaengige Heuristik). Unter dieser Bedingung "
            "ist die tatsaechlich gespielte Aktion nach Konstruktion IDENTISCH "
            "mit der einen Policy-Eintragsaktion (self_play.rs:1352-1358)."
        ),
        "corpus_glob": CORPUS_GLOB,
        "n_files": len(files),
        "n_total_records": n_total_records,
        "n_qualifying_decisions": n_qualifying,
        "n_games": len(n_games),
        "models": {k: str(v) for k, v in MODELS.items()},
        "runtime_sec": time.time() - t0,
    }

    for name in MODELS:
        masses = [d[f"mass_{name}"] for d in decisions]
        ratios = [d[f"ratio_{name}"] for d in decisions]
        result[f"mass_{name}"] = describe(masses)
        result[f"ratio_{name}"] = describe(ratios)

        # je Aktionstyp
        by_type = {}
        types = sorted(set(d["action_type"] for d in decisions))
        for t in types:
            sub_mass = [d[f"mass_{name}"] for d in decisions if d["action_type"] == t]
            sub_ratio = [d[f"ratio_{name}"] for d in decisions if d["action_type"] == t]
            by_type[t] = {"mass": describe(sub_mass), "ratio": describe(sub_ratio)}
        result[f"by_action_type_{name}"] = by_type

    # Paar-Auswertung nur, wenn GENAU die beiden Original-Arme laufen
    # (Nachzug 2026-08-29: mit CLI-Modellen entfaellt sie; Vergleich dann
    # gegen die protokollierten Alt-Werte im Original-Artefakt).
    if set(MODELS) != {"b18_best", "champion"}:
        OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
        with open(OUT_JSON, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"[info] Ergebnis geschrieben (ohne Paar-Teil): {OUT_JSON}", flush=True)
        print("\n=== ZUSAMMENFASSUNG ===")
        for name in MODELS:
            m = result[f"mass_{name}"]
            r = result[f"ratio_{name}"]
            print(f"{name}: mass mean={m['mean']:.4f} median={m['median']:.4f} | "
                  f"ratio(mass/uniform) mean={r['mean']:.2f} median={r['median']:.2f}")
        return

    # gepaarte Differenz je Entscheidung (b18 - champion), auf RATIO (skaleninvariant
    # gegen den je nach Aktionstyp stark schwankenden Legalitaets-Nenner).
    diffs_ratio = [d["ratio_b18_best"] - d["ratio_champion"] for d in decisions]
    diffs_mass = [d["mass_b18_best"] - d["mass_champion"] for d in decisions]
    result["paired_diff_ratio_decision_level"] = describe(diffs_ratio)
    result["paired_diff_mass_decision_level"] = describe(diffs_mass)
    n_b18_higher = sum(1 for d in diffs_ratio if d > 0)
    n_champ_higher = sum(1 for d in diffs_ratio if d < 0)
    n_tied = len(diffs_ratio) - n_b18_higher - n_champ_higher
    result["sign_count_decision_level"] = {
        "b18_higher_ratio": n_b18_higher, "champion_higher_ratio": n_champ_higher, "tied": n_tied,
        "n": len(diffs_ratio),
    }

    # game-level Mittel (Block-Analogon -- Entscheidungen INNERHALB einer
    # Partie sind nicht unabhaengig, Stufe-Ebene wie in den Arena-Preregs).
    by_game = {}
    for d in decisions:
        by_game.setdefault(d["game_id"], []).append(d)
    game_rows = []
    for gid, rows in by_game.items():
        b18_mean = float(np.mean([r["ratio_b18_best"] for r in rows]))
        champ_mean = float(np.mean([r["ratio_champion"] for r in rows]))
        game_rows.append({"game_id": gid, "n_decisions": len(rows),
                           "ratio_b18_best": b18_mean, "ratio_champion": champ_mean,
                           "diff": b18_mean - champ_mean})
    result["n_games_used"] = len(game_rows)
    result["game_level_ratio_b18_best"] = describe([g["ratio_b18_best"] for g in game_rows])
    result["game_level_ratio_champion"] = describe([g["ratio_champion"] for g in game_rows])
    game_diffs = [g["diff"] for g in game_rows]
    result["game_level_paired_diff"] = describe(game_diffs)
    if len(game_diffs) > 1:
        mean_d = float(np.mean(game_diffs))
        sd_d = float(np.std(game_diffs, ddof=1))
        se_d = sd_d / (len(game_diffs) ** 0.5)
        t_stat = mean_d / se_d if se_d > 0 else float("nan")
        result["game_level_paired_t"] = t_stat
    n_games_b18_higher = sum(1 for d in game_diffs if d > 0)
    n_games_champ_higher = sum(1 for d in game_diffs if d < 0)
    result["sign_count_game_level"] = {
        "b18_higher_ratio": n_games_b18_higher, "champion_higher_ratio": n_games_champ_higher,
        "tied": len(game_diffs) - n_games_b18_higher - n_games_champ_higher,
        "n": len(game_diffs),
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"[info] Ergebnis geschrieben: {OUT_JSON}", flush=True)

    # Kurzbericht auf stdout.
    print("\n=== ZUSAMMENFASSUNG ===")
    print(f"n Dateien={len(files)}  n qualifizierende Entscheidungen={n_qualifying}  n Partien={len(n_games)}")
    for name in MODELS:
        m = result[f"mass_{name}"]
        r = result[f"ratio_{name}"]
        print(f"{name}: mass mean={m['mean']:.4f} sd={m['sd']:.4f} median={m['median']:.4f} | "
              f"ratio(mass/uniform) mean={r['mean']:.2f} sd={r['sd']:.2f} median={r['median']:.2f}")
    print(f"paired diff ratio (b18-champion), decision-level: mean={result['paired_diff_ratio_decision_level']['mean']:.3f} "
          f"sd={result['paired_diff_ratio_decision_level']['sd']:.3f}")
    print(f"sign count decision-level: {result['sign_count_decision_level']}")
    print(f"game-level n={result['n_games_used']} paired diff mean={result['game_level_paired_diff'].get('mean')} "
          f"t={result.get('game_level_paired_t')}")
    print(f"sign count game-level: {result['sign_count_game_level']}")


if __name__ == "__main__":
    main()
