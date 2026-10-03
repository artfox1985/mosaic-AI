"""Auswertung der Sonden S1-S4 des asymmetrischen Self-Plays (evaluations/PREREG_asymmetric_selfplay.md par.5).

Liest die Laeufe aus `tools/asym_probes.sh` (Rezept `models/v35_probes.recipe.json`, Ordner data/probe_asym)
und rechnet je Sonde die registrierten Groessen:

* S1 Kosten: Wanduhr je Partie aus dem Lauf-Manifest (`laufzeit.s_je_partie`) je Klasse, dazu erzwungene
  Platten je Partie (Zahl der `dome_dice_cost`-Felder) und Platzwahl-Records je Partie.
* S2 Andere Stellungen: Policy-KL(Ziel || Prior des Generators) an Drafting-Entscheiden NACH der ersten
  erzwungenen Platte, getrennt nach Seite (W / G), gegen alle Drafting-Entscheide derselben Runden im
  Sockel (`policy`); Median-Differenz mit Block-Bootstrap ueber Dateien.
* S3 Wert-Verzerrung: Siegquote, Punkte, Marge je Seite; Brier des Generator-Kopfs je Seite gegen den
  Sockel; Kalibrierungsversatz = mittlere Vorhersage P(Sieg der Seite am Zug) minus tatsaechliche
  Siegrate, je Seite und nach `forced_domes_before`; gezahlte Wuerfel-Punkte je Partie.
* S4 Stoerer-Pilot: je lambda Punkte und Siegquote beider Seiten, Versatz je Seite, Verteilung von
  `own_q_gap` der Stoerer-Zuege; Leseregel par.5 angewandt.

Grundmengen und Einheiten stehen im Artefakt je Groesse. Fortschritt mit flush=True.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "tools"))
sys.path.insert(0, str(BASE_DIR / "tools" / "probes"))
sys.path.insert(0, str(BASE_DIR / "engine" / "py"))
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

from runtime_block import laufzeit_block  # noqa: E402
from targeted_branching_pretest import policy_kl  # noqa: E402

ROUNDS = (1, 2, 3, 4)
AGGR_CLASSES = (("policy-aggr-l0", 0.0), ("policy-aggr-l05", 0.5), ("policy-aggr-l1", 1.0), ("policy-aggr-l2", 2.0))
N_BOOT = 2000


def class_files(data: Path, cls: str) -> list[str]:
    return sorted(glob.glob(str(data / f"selfplay_probe-v35-{cls}_*.pkl")))


def manifest_runtime(data: Path, cls: str):
    mans = sorted(glob.glob(str(data / f"manifest_probe-v35-{cls}_*.json")))
    if not mans:
        return None
    return json.load(open(mans[-1], encoding="utf-8")).get("laufzeit")


def boot_ci(values_by_file: list[np.ndarray], stat, rng, n_boot=N_BOOT):
    """Block-Bootstrap ueber Dateien: 95-%-Intervall von stat(konkatenierte Werte)."""
    k = len(values_by_file)
    out = []
    for _ in range(n_boot):
        pick = rng.integers(0, k, k)
        v = np.concatenate([values_by_file[i] for i in pick]) if k else np.array([])
        if v.size:
            out.append(stat(v))
    if not out:
        return None
    return [float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))]


def boot_diff_ci(a_by_file, b_by_file, stat, rng, n_boot=N_BOOT):
    """Intervall von stat(A) - stat(B), A und B je fuer sich ueber ihre Dateien gezogen."""
    out = []
    ka, kb = len(a_by_file), len(b_by_file)
    for _ in range(n_boot):
        va = np.concatenate([a_by_file[i] for i in rng.integers(0, ka, ka)])
        vb = np.concatenate([b_by_file[i] for i in rng.integers(0, kb, kb)])
        if va.size and vb.size:
            out.append(stat(va) - stat(vb))
    if not out:
        return None
    return [float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", default="data/probe_asym")
    ap.add_argument("--model", default="models/alphazero_v34-b01_brierbest.pth", help="Generator (.pth)")
    ap.add_argument("--batch", type=int, default=256)
    ap.add_argument("--seed", type=int, default=20261003)
    ap.add_argument("--out", default="evaluations/artifacts/asym_probes_s1_s4.json")
    args = ap.parse_args()
    t_start, c_start = time.monotonic(), time.process_time()
    rng = np.random.default_rng(args.seed)

    import torch
    import neural_net
    from neural_net import action_to_id, build_model_from_checkpoint, state_to_planes, state_to_tensor
    from corpus_io import load_records
    assert neural_net._FEATURES_FROM_RUST, "Rust-Bauer nicht aktiv"
    torch.set_num_threads(max(1, (os.cpu_count() or 2) - 1))
    blob = torch.load(BASE_DIR / args.model, map_location="cpu", weights_only=False)
    model, encoder = build_model_from_checkpoint(blob)[:2]
    model.eval()
    data = BASE_DIR / args.data_dir

    def net_eval(states):
        with torch.no_grad():
            flat = torch.stack([state_to_tensor(d) for d in states])
            o = model(torch.stack([state_to_planes(d) for d in states]), flat) if encoder == "2d" else model(flat)
        return o[0].numpy(), ((o[1][:, 0] + 1.0) / 2.0).numpy()

    def read_class(cls: str, side_field: str | None):
        """Je Drafting-Record (R1-4, completed, Ziel >= 2 IDs): Datei, Seite (0 = Sonderseite W/S, 1 = G,
        -1 ohne Sonderseite), Runde, forced_domes_before, Sieg der Seite am Zug, KL, p_head; dazu je
        Partie Endstand, Sieger, Sonderseite und gezahlte Wuerfel-Punkte; own_q_gap der Sonderseite."""
        files = class_files(data, cls)
        rec, games, ogap = defaultdict(list), [], []
        buf = []

        def flush():
            if not buf:
                return
            logits, ph = net_eval([b[0] for b in buf])
            for i, (_st, fi, side, rnd, fdb, win, targ) in enumerate(buf):
                rec["file"].append(fi); rec["side"].append(side); rec["round"].append(rnd)
                rec["fdb"].append(fdb); rec["win"].append(win)
                rec["kl"].append(policy_kl(logits[i], targ)); rec["p"].append(float(ph[i]))
            buf.clear()

        for fi, f in enumerate(files):
            by_game: dict[str, list] = defaultdict(list)
            for r in load_records(f):
                by_game[str(r.get("game_id", "")).split("_x")[0]].append(r)
            for gid, rs in by_game.items():
                special = None
                if side_field is not None:
                    vals = {r.get(side_field) for r in rs if r.get(side_field) is not None}
                    special = int(next(iter(vals))) if len(vals) == 1 else None
                fin = next((r for r in reversed(rs) if r.get("winner") is not None), None)
                if fin is not None:
                    sc = fin.get("scores") or [p["score"] for p in fin["state"]["players"]]
                    paid = sum(int(r["dome_dice_cost"][1]) for r in rs if r.get("dome_dice_cost"))
                    forced = sum(1 for r in rs if r.get("dome_dice_cost") is not None)
                    places = sum(1 for r in rs if r.get("dice_place"))
                    games.append({"file": fi, "special": special, "winner": int(fin["winner"]),
                                  "scores": [float(x) for x in sc], "paid": paid, "forced": forced,
                                  "places": places, "completed": fin.get("completed", True) is not False})
                for r in rs:
                    st = r.get("state") or {}
                    if not isinstance(st, dict) or st.get("phase") != "drafting" or r.get("completed", True) is False:
                        continue
                    if r.get("dice_place"):
                        continue  # Platzwahl-Records: kein Halbzug, Ziel nur ueber die Plaetze
                    rnd = int(st.get("round", 0))
                    if rnd not in ROUNDS or "winner" not in r:
                        continue
                    targ: dict[int, float] = {}
                    try:
                        for pe in r.get("policy") or []:
                            aid = action_to_id(pe["action"])
                            targ[aid] = targ.get(aid, 0.0) + float(pe["prob"])
                    except Exception:  # noqa: BLE001
                        continue
                    if len(targ) < 2 or sum(targ.values()) <= 0:
                        continue
                    p = int(r["player"])
                    side = -1 if special is None else (0 if p == special else 1)
                    if special is not None and p == special and r.get("own_q_gap") is not None:
                        ogap.append(float(r["own_q_gap"]))
                    buf.append((st, fi, side, rnd, int(r.get("forced_domes_before", 0) or 0),
                                1.0 if int(r["winner"]) == p else 0.0, targ))
                    if len(buf) >= args.batch:
                        flush()
            flush()
            print(f"[asym] {cls} {fi + 1}/{len(files)} Dateien, {len(rec['file'])} Zustaende, "
                  f"{time.monotonic() - t_start:.0f} s", flush=True)
        arr = {k: np.array(v) for k, v in rec.items()}
        return files, arr, games, np.array(ogap)

    def by_file(arr, mask, field, nfiles):
        return [arr[field][mask & (arr["file"] == i)] for i in range(nfiles)]

    def side_game_stats(games, nfiles):
        """Je Sonderseite (W bzw. S) und G: Siegquote, Punkte, Marge (je Partie, Grundmenge Partien)."""
        out = {}
        for name, pick in (("sonderseite", lambda g: g["special"]), ("G", lambda g: 1 - g["special"])):
            gs = [g for g in games if g["special"] is not None]
            win = np.array([1.0 if g["winner"] == pick(g) else 0.0 for g in gs])
            pts = np.array([g["scores"][pick(g)] for g in gs])
            mar = np.array([g["scores"][pick(g)] - g["scores"][1 - pick(g)] for g in gs])
            fidx = np.array([g["file"] for g in gs])
            out[name] = {"n_partien": len(gs), "siegquote": float(win.mean()) if gs else None,
                         "siegquote_ci95": boot_ci([win[fidx == i] for i in range(nfiles)], np.mean, rng),
                         "punkte": float(pts.mean()) if gs else None, "marge": float(mar.mean()) if gs else None}
        return out

    def calibration(arr, nfiles, side):
        m = arr["side"] == side
        if not m.any():
            return None
        off = arr["p"] - arr["win"]
        res = {"n": int(m.sum()), "versatz": float(off[m].mean()),
               "versatz_ci95": boot_ci(by_file({"x": off, "file": arr["file"]}, m, "x", nfiles), np.mean, rng),
               "brier": float(((arr["p"] - arr["win"]) ** 2)[m].mean())}
        res["je_forced_domes_before"] = {}
        for k in sorted(set(arr["fdb"][m].tolist())):
            mk = m & (arr["fdb"] == k)
            res["je_forced_domes_before"][str(k)] = {"n": int(mk.sum()), "versatz": float(off[mk].mean())}
        return res

    out = {"prereg": "evaluations/PREREG_asymmetric_selfplay.md par.5", "data_dir": args.data_dir, "model": args.model}

    # --- Sockel (Bezug) und W ------------------------------------------------------------------
    pf, pa, pg, _ = read_class("policy", None)
    wf, wa, wg, _ = read_class("policy-dice", "dome_dice_side")
    lz_p, lz_w = manifest_runtime(data, "policy"), manifest_runtime(data, "policy-dice")
    s1 = {"grundmenge": "Partien je Klasse (100), Einheit Sekunden Wanduhr je Partie aus dem Lauf-Manifest",
          "policy": lz_p, "policy_dice": lz_w}
    if lz_p and lz_w and lz_p.get("s_je_partie") and lz_w.get("s_je_partie"):
        s1["mehrkosten_w"] = lz_w["s_je_partie"] / lz_p["s_je_partie"] - 1.0
        s1["leseregel"] = "haelt (<= +25 %)" if s1["mehrkosten_w"] <= 0.25 else "Nutzer-Entscheid (> +25 %)"
    s1["erzwungene_platten_je_partie"] = float(np.mean([g["forced"] for g in wg])) if wg else None
    s1["platzwahl_records_je_partie"] = float(np.mean([g["places"] for g in wg])) if wg else None
    out["S1"] = s1

    s2 = {"grundmenge": ("Drafting-Records R1-4 (Ziel >= 2 IDs, ohne Platzwahl-Records); W-Klasse nur NACH der ersten "
                         "erzwungenen Platte (forced_domes_before >= 1); Bezug alle Sockel-Records derselben Runden"),
          "einheit": "KL(Ziel || Prior des Generators) je Record, Median; CI Block-Bootstrap ueber Dateien"}
    base_bf = by_file(pa, np.ones(len(pa["kl"]), bool), "kl", len(pf))
    s2["sockel"] = {"n": int(len(pa["kl"])), "median": float(np.median(pa["kl"]))}
    for sname, side in (("W", 0), ("G", 1)):
        m = (wa["side"] == side) & (wa["fdb"] >= 1)
        bf = by_file(wa, m, "kl", len(wf))
        ci = boot_diff_ci(bf, base_bf, np.median, rng)
        s2[sname] = {"n": int(m.sum()), "median": float(np.median(wa["kl"][m])) if m.any() else None,
                     "median_diff_gegen_sockel": (float(np.median(wa["kl"][m]) - np.median(pa["kl"])) if m.any() else None),
                     "ci95": ci, "lesart": ("andere Stellungen (hoeher)" if ci and ci[0] > 0
                                else "niedriger" if ci and ci[1] < 0 else "nicht nachweisbar anders")}
        s2[sname]["je_runde"] = {str(r): float(np.median(wa["kl"][m & (wa["round"] == r)]))
                                 for r in ROUNDS if (m & (wa["round"] == r)).any()}
    out["S2"] = s2

    s3 = {"grundmenge": "Partien (Siegquote/Punkte/Marge) bzw. Drafting-Records (Brier, Versatz) der Klasse policy-dice",
          "partien": side_game_stats(wg, len(wf)),
          "W": calibration(wa, len(wf), 0), "G": calibration(wa, len(wf), 1),
          "sockel_brier": float(((pa["p"] - pa["win"]) ** 2).mean()),
          "gezahlte_wuerfelpunkte_je_partie": float(np.mean([g["paid"] for g in wg])) if wg else None}
    flags = []
    for sname in ("W", "G"):
        c = s3[sname]
        if c is None:
            continue
        if c["brier"] - s3["sockel_brier"] > 0.01:
            flags.append(f"{sname}: Brier {c['brier']:.4f} > Sockel + 0,01")
        ci = c["versatz_ci95"]
        if ci and (ci[0] > 0 or ci[1] < 0) and abs(c["versatz"]) > 0.03:
            flags.append(f"{sname}: Versatz {c['versatz']:+.4f} (CI ohne 0, |x| > 0,03)")
    s3["leseregel"] = flags or ["keine Verzerrung nach den Leseregeln, alle Wertziele bleiben"]
    out["S3"] = s3

    # --- S4 ------------------------------------------------------------------------------------
    s4 = {"grundmenge": "je lambda 100 Partien policy-aggr (w = 0,1); own_q_gap ueber Drafting-Records der S-Seite",
          "stufen": {}}
    for cls, lam in AGGR_CLASSES:
        af, aa, agm, og = read_class(cls, "aggr_side")
        st = side_game_stats(agm, len(af))
        s4["stufen"][str(lam)] = {
            "partien": st, "S": calibration(aa, len(af), 0), "G": calibration(aa, len(af), 1),
            "own_q_gap": ({"n": int(og.size), "q25": float(np.percentile(og, 25)), "median": float(np.median(og)),
                           "q75": float(np.percentile(og, 75)), "anteil_le_0": float((og <= 0).mean())}
                          if og.size else None),
            "laufzeit": manifest_runtime(data, cls)}
    base = s4["stufen"].get("0.0")
    chosen = None
    if base:
        for _cls, lam in AGGR_CLASSES:
            stg = s4["stufen"][str(lam)]["partien"]
            ok_win = stg["sonderseite"]["siegquote"] >= base["partien"]["sonderseite"]["siegquote"] - 0.05
            g_down = stg["G"]["punkte"] < base["partien"]["G"]["punkte"]
            if lam > 0 and ok_win and g_down:
                chosen = lam
    s4["gewaehltes_lambda"] = chosen
    if chosen is not None and s4["stufen"][str(chosen)]["own_q_gap"]:
        s4["eps_median_own_q_gap"] = s4["stufen"][str(chosen)]["own_q_gap"]["median"]
    s4["leseregel"] = ("groesstes lambda mit Stoerer-Siegquote >= lambda-0-Wert - 5 Prozentpunkte UND weniger G-Punkten; "
                       "eps = Median own_q_gap bei diesem lambda" + ("" if chosen is not None else
                       " -- KEINE Stufe senkt die G-Punkte: Stoerer in dieser Form wirkungslos, Nutzer-Entscheid"))
    out["S4"] = s4
    out["laufzeit"] = laufzeit_block(t_start, cpu_start=c_start, threads=torch.get_num_threads(),
                                     n_units=len(pa["kl"]) + len(wa["kl"]), unit="zustand")
    Path(BASE_DIR / args.out).parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(BASE_DIR / args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: out[k] for k in ("S1",)}, ensure_ascii=False, indent=1), flush=True)
    print(f"Ergebnis: {args.out} ({time.monotonic() - t_start:.1f} s)", flush=True)


if __name__ == "__main__":
    main()
