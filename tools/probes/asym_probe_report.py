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
    ap.add_argument("--out", default=None,
                    help="Artefakt; Default evaluations/artifacts/asym_probes_s1_s4.json, mit --kl-class "
                         "evaluations/artifacts/probe_<klasse>_kl.json")
    ap.add_argument("--kl-class", default=None,
                    help="NUR den S2-KL-Vergleich einer beliebigen Klasse ohne Wuerfel-Felder gegen `policy` rechnen "
                         "(Median KL(Ziel||Prior), Block-Bootstrap ueber Dateien), dazu Kosten je Partie aus den "
                         "Manifesten und die Standard-Kennzahlen (tools/corpus_sanity_check.py); S1-S4 entfallen")
    ap.add_argument("--side-class", default=None,
                    help="par.5e1 Frage 3: NUR die Seitenauswertung einer asymmetrischen Klasse (z. B. "
                         "policy-tb1): Siegquote der markierten Seite gegen 0,50 (Block-Bootstrap ueber "
                         "Dateien), Punkte und Marge beider Seiten, Standard-Kennzahlen je Seite, Kosten je "
                         "Partie; S1-S4 entfallen")
    ap.add_argument("--side-field", default="tiebreak_side",
                    help="Record-Feld mit dem Spielerindex der markierten Seite (Default tiebreak_side; "
                         "fuer ein Zweitnetz opponent_side, dann ist die 'sonderseite' das Zweitnetz)")
    ap.add_argument("--side-names", default=None,
                    help="Beschriftung 'sonderseite,G' im JSON, z. B. 'v32-b01 (Zweitnetz),v34-b01 (G)'")
    ap.add_argument("--kl-baseline", default="policy",
                    help="Bezugsklasse des KL-Vergleichs (Default policy; par.7b/par.8b: policy-m2)")
    ap.add_argument("--kl-side-field", default=None,
                    help="mit --kl-side-value: nur Records der KL-Klasse mit diesem Feldwert (z. B. net_label)")
    ap.add_argument("--kl-side-value", default=None,
                    help="Feldwert zu --kl-side-field (z. B. primary = Seite des Generators)")
    ap.add_argument("--kl-extra-class", default=None,
                    help="dritte Spalte: KL, Kosten und Standard-Kennzahlen einer weiteren Klasse (ohne Filter)")
    ap.add_argument("--dice-class", default="policy-dice",
                    help="W-Klasse fuer S1-S3 (par.5b: policy-dice-src4 nach der neuen Quellenregel)")
    ap.add_argument("--skip-s4", action="store_true", help="S4 (Stoerer-Stufen) auslassen")
    ap.add_argument("--aggr-classes", default=None,
                    help="S4-Klassen als 'klasse:stufe,...' (par.5c: policy-aggr-e01:0.01,...); Default die lambda-Arme")
    ap.add_argument("--skip-s2", action="store_true", help="W-Klasse und S1-S3 auslassen (nur S4)")
    ap.add_argument("--post-dice-phase", action="store_true",
                    help="par.5d (S5): S2/S3 der W-Klasse nur ueber Records NACH der Wuerfelphase (dice_phase false)")
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

    def read_class(cls: str, side_field: str | None, record_filter=None):
        """Je Drafting-Record (R1-4, completed, Ziel >= 2 IDs): Datei, Seite (0 = Sonderseite W/S, 1 = G,
        -1 ohne Sonderseite), Runde, forced_domes_before, Sieg der Seite am Zug, KL, p_head; dazu je
        Partie Endstand, Sieger, Sonderseite und gezahlte Wuerfel-Punkte; own_q_gap der Sonderseite."""
        files = class_files(data, cls)
        rec, games, ogap = defaultdict(list), [], []
        disrupt = {"switched": [], "drop": []}
        buf = []

        def flush():
            if not buf:
                return
            logits, ph = net_eval([b[0] for b in buf])
            for i, (_st, fi, side, rnd, fdb, win, targ, dph) in enumerate(buf):
                rec["file"].append(fi); rec["side"].append(side); rec["round"].append(rnd); rec["dphase"].append(dph)
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
                    if record_filter is not None and not record_filter(r):
                        continue  # --kl-side-field/--kl-side-value: nur Records dieser Seite
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
                    if special is not None and p == special and r.get("aggr_switched") is not None:
                        disrupt["switched"].append(1.0 if r["aggr_switched"] else 0.0)
                        disrupt["drop"].append(float(r.get("aggr_opp_drop_pts") or 0.0))
                    buf.append((st, fi, side, rnd, int(r.get("forced_domes_before", 0) or 0),
                                1.0 if int(r["winner"]) == p else 0.0, targ, 1 if r.get("dice_phase") is True else 0))
                    if len(buf) >= args.batch:
                        flush()
            flush()
            print(f"[asym] {cls} {fi + 1}/{len(files)} Dateien, {len(rec['file'])} Zustaende, "
                  f"{time.monotonic() - t_start:.0f} s", flush=True)
        arr = {k: np.array(v) for k, v in rec.items()}
        read_class.disrupt = disrupt
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

    def calibration(arr, nfiles, side, extra=None):
        m = arr["side"] == side
        if extra is not None:
            m = m & extra
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
    if args.out is None:
        args.out = (f"evaluations/artifacts/probe_{args.kl_class}_kl.json" if args.kl_class
                    else f"evaluations/artifacts/probe_{args.side_class}_side.json" if args.side_class
                    else "evaluations/artifacts/asym_probes_s1_s4.json")

    # --- Nur Seitenauswertung einer asymmetrischen Klasse (--side-class, par.5e1 Frage 3) --------
    if args.side_class:
        import corpus_sanity_check
        sf = args.side_field
        sfiles, sarr, sgames, _ = read_class(args.side_class, sf)
        nf = len(sfiles)
        sgs = side_game_stats(sgames, nf)
        mark = sgs["sonderseite"]
        ci = mark["siegquote_ci95"]
        mar = mark["marge"]
        if sf != "tiebreak_side":
            # Leseregel par.5e1 gilt nur fuer den Stichentscheid; fuer ein Zweitnetz (par.7b) entscheidet
            # die KL der G-Seite zusammen mit dem Versatz unten.
            lesart = None
        elif ci and ci[0] > 0.5 and mar is not None and mar > 0:
            lesart = "CI ganz ueber 0,50 UND Marge > 0: Modus als Vorschlag ins v35-Sockel-Rezept (Nutzer-Entscheid)"
        elif ci and ci[1] < 0.5:
            lesart = "CI ganz unter 0,50: Bestand bleibt, par.5c1 war dann etwas anderes (zu klaeren)"
        else:
            lesart = "CI mit 0,50 (oder Marge <= 0): Bestand bleibt, berichtet"
        n_marked = sum(1 for g in sgames if g["special"] is not None)
        names = (args.side_names.split(",", 1) if args.side_names
                 else (["Seite mit Knopf", "Gegenseite (Modus 0)"] if sf == "tiebreak_side"
                       else [f"Seite aus `{sf}`", "Gegenseite"]))
        out["side_class"] = args.side_class
        out["side_field"] = sf
        out["beschriftung"] = {"sonderseite": names[0].strip(), "G": names[-1].strip()}
        out["seiten"] = {
            "grundmenge": (f"Partien der Klasse {args.side_class} mit eindeutigem `{sf}` ({n_marked} von "
                           f"{len(sgames)}); 'sonderseite' = {names[0].strip()}, 'G' = {names[-1].strip()}"),
            "einheit": "Siegquote je Partie (CI Block-Bootstrap ueber Dateien), Punkte und Marge je Partie",
            "partien": sgs,
            "siegquote_gegen_050": {"siegquote": mark["siegquote"], "ci95": ci,
                                    "ci_ganz_ueber_050": bool(ci and ci[0] > 0.5),
                                    "ci_ganz_unter_050": bool(ci and ci[1] < 0.5)},
            "lesart": lesart,
            "nicht_beendet": sum(1 for g in sgames if not g["completed"]),
            # Wertkopf-Versatz je Seite (vorhandene Groesse aus S3/S4, ohne Leseregel hier).
            "kalibrierung": {"sonderseite": calibration(sarr, nf, 0), "G": calibration(sarr, nf, 1)},
            "kalibrierung_einheit": ("Wertkopf des Generators (--model) je Drafting-Record R1-4 der Seite am Zug: "
                                     "mittlere Vorhersage P(Sieg) minus tatsaechliche Siegrate"),
        }
        cal_g = out["seiten"]["kalibrierung"]["G"]
        if cal_g:
            cig = cal_g.get("versatz_ci95")
            # par.7b-Regel fuer die G-Seite: |Versatz| <= 0,05 oder CI mit 0.
            out["seiten"]["versatz_G_unverzerrt"] = bool(abs(cal_g["versatz"]) <= 0.05
                                                         or (cig and cig[0] <= 0.0 <= cig[1]))
        out["kosten"] = {"grundmenge": "Partien, Einheit Sekunden Wanduhr je Partie aus dem Lauf-Manifest",
                         args.side_class: manifest_runtime(data, args.side_class),
                         "policy": manifest_runtime(data, "policy"),
                         "policy-m2": manifest_runtime(data, "policy-m2")}

        def side_of(rec):
            v = rec.get(sf)
            return None if v is None else int(v)

        out["standard_kennzahlen"] = {
            "quelle": "tools/corpus_sanity_check.py auswerten (Endzustand je Partie), je Seite gefiltert",
            "sonderseite": corpus_sanity_check.auswerten(
                str(data), files=sfiles, side_filter=lambda r, pi: side_of(r) == pi),
            "G": corpus_sanity_check.auswerten(
                str(data), files=sfiles, side_filter=lambda r, pi: side_of(r) is not None and side_of(r) != pi),
        }
        out["laufzeit"] = laufzeit_block(t_start, cpu_start=c_start, threads=torch.get_num_threads(),
                                         n_units=len(sgames), unit="partie")
        Path(BASE_DIR / args.out).parent.mkdir(parents=True, exist_ok=True)
        json.dump(out, open(BASE_DIR / args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(json.dumps({k: out[k] for k in ("seiten", "kosten")}, ensure_ascii=False, indent=1)[:4000], flush=True)
        print(f"Ergebnis: {args.out} ({time.monotonic() - t_start:.1f} s)", flush=True)
        return

    # --- Nur KL-Vergleich einer Klasse gegen eine Bezugsklasse (--kl-class) --------------------
    if args.kl_class:
        import corpus_sanity_check
        base_name, cls_name, extra_name = args.kl_baseline, args.kl_class, args.kl_extra_class
        if (args.kl_side_field is None) != (args.kl_side_value is None):
            raise SystemExit("--kl-side-field und --kl-side-value gehoeren zusammen")
        side_filter = None
        if args.kl_side_field is not None:
            side_filter = (lambda r, f=args.kl_side_field, v=args.kl_side_value:
                           r.get(f) is not None and str(r.get(f)) == str(v))
        pf, pa, _pg, _ = read_class(base_name, None)
        kf, ka, _kg, _ = read_class(cls_name, None, record_filter=side_filter)
        base_bf = by_file(pa, np.ones(len(pa["kl"]), bool), "kl", len(pf))

        def kl_against_base(arr, nfiles):
            """Median-KL einer Klasse, Differenz zur Bezugsklasse mit Block-Bootstrap-CI ueber Dateien."""
            if not len(arr.get("kl", [])) or not len(pa["kl"]):
                return {"n": int(len(arr.get("kl", []))), "dateien": nfiles, "median": None,
                        f"median_diff_gegen_{base_name}": None, "ci95": None, "lesart": "keine Records"}
            ci_ = boot_diff_ci(by_file(arr, np.ones(len(arr["kl"]), bool), "kl", nfiles), base_bf, np.median, rng)
            return {"n": int(len(arr["kl"])), "dateien": nfiles, "median": float(np.median(arr["kl"])),
                    f"median_diff_gegen_{base_name}": float(np.median(arr["kl"]) - np.median(pa["kl"])),
                    "ci95": ci_,
                    "lesart": (f"hoeher als {base_name}" if ci_ and ci_[0] > 0
                               else f"niedriger als {base_name}" if ci_ and ci_[1] < 0
                               else "nicht nachweisbar anders")}

        def per_round(arr):
            return {str(r): (float(np.median(arr["kl"][arr["round"] == r]))
                             if len(arr.get("kl", [])) and (arr["round"] == r).any() else None) for r in ROUNDS}

        cls_kl = kl_against_base(ka, len(kf))
        sel = (f"nur Records mit {args.kl_side_field} == {args.kl_side_value!r}" if side_filter
               else "alle Seiten")
        kl = {"grundmenge": ("Drafting-Records R1-4 (Ziel >= 2 IDs, ohne Platzwahl-Records); "
                             f"Klasse {cls_name} ({sel}) gegen alle Records der Klasse {base_name}"),
              "einheit": "KL(Ziel || Prior des Generators --model) je Record, Median; CI Block-Bootstrap ueber Dateien",
              base_name: {"n": int(len(pa["kl"])), "dateien": len(pf),
                          "median": float(np.median(pa["kl"])) if len(pa["kl"]) else None},
              cls_name: cls_kl,
              # Bestandsschluessel (Artefakt probe_policy_s400_kl.json): Differenz, CI und Lesart der Klasse.
              f"median_diff_gegen_{base_name}": cls_kl[f"median_diff_gegen_{base_name}"],
              "ci95": cls_kl["ci95"], "lesart": cls_kl["lesart"],
              "record_filter": ({"feld": args.kl_side_field, "wert": args.kl_side_value} if side_filter else None)}
        kl["je_runde"] = {base_name: per_round(pa), cls_name: per_round(ka)}
        files_by_class = {base_name: pf, cls_name: kf}
        if extra_name:
            xf, xa, _xg, _ = read_class(extra_name, None)
            kl[extra_name] = kl_against_base(xa, len(xf))
            kl["je_runde"][extra_name] = per_round(xa)
            files_by_class[extra_name] = xf
        out["kl_class"] = cls_name
        out["kl_baseline"] = base_name
        out["KL"] = kl
        cost = {"grundmenge": "Partien je Klasse, Einheit Sekunden Wanduhr je Partie aus dem Lauf-Manifest"}
        for name in files_by_class:
            cost[name] = manifest_runtime(data, name)
        lz_b = cost[base_name]
        for name in files_by_class:
            lz = cost[name]
            if name != base_name and lz and lz_b and lz.get("s_je_partie") and lz_b.get("s_je_partie"):
                cost[f"kostenfaktor_{name}_gegen_{base_name}"] = lz["s_je_partie"] / lz_b["s_je_partie"]
        out["kosten"] = cost
        # Standard-Kennzahlen (CLAUDE.md 2026-08-23) aus dem Endzustand je Partie, je Partie-Seite gemittelt
        # ueber ALLE Seiten (auch bei --kl-side-field; je Seite getrennt: --side-class).
        std = {"quelle": "tools/corpus_sanity_check.py auswerten (score_geo / scoring_tile_points des Endzustands), "
                         "alle Seiten"}
        for name, files in files_by_class.items():
            std[name] = corpus_sanity_check.auswerten(str(data), files=files)
        diff_keys = ("zeilen_voll", "zeilen_fuell", "sp_voll", "sp_ge4", "sp_ge3", "sp_max", "floor", "punkte")
        for name in files_by_class:
            if name != base_name:
                std[f"differenz_{name}_minus_{base_name}"] = {k: std[name][k] - std[base_name][k] for k in diff_keys}
        if base_name == "policy":
            std["differenz_klasse_minus_policy"] = std[f"differenz_{cls_name}_minus_policy"]
        out["standard_kennzahlen"] = std
        n_states = len(pa["kl"]) + len(ka.get("kl", []))
        out["laufzeit"] = laufzeit_block(t_start, cpu_start=c_start, threads=torch.get_num_threads(),
                                         n_units=n_states, unit="zustand")
        Path(BASE_DIR / args.out).parent.mkdir(parents=True, exist_ok=True)
        json.dump(out, open(BASE_DIR / args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(json.dumps({k: out[k] for k in ("KL", "kosten")}, ensure_ascii=False, indent=1)[:4000], flush=True)
        print(f"Ergebnis: {args.out} ({time.monotonic() - t_start:.1f} s)", flush=True)
        return

    # --- Sockel (Bezug) und W ------------------------------------------------------------------
    pf, pa, pg, _ = read_class("policy", None)
    wa = {"kl": np.array([])}
    if not args.skip_s2:
        wf, wa, wg, _ = read_class(args.dice_class, "dome_dice_side")
        lz_p, lz_w = manifest_runtime(data, "policy"), manifest_runtime(data, args.dice_class)
        out["dice_class"] = args.dice_class
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
            m = (wa["side"] == side) & ((wa["dphase"] == 0) if args.post_dice_phase else (wa["fdb"] >= 1))
            bf = by_file(wa, m, "kl", len(wf))
            ci = boot_diff_ci(bf, base_bf, np.median, rng)
            s2[sname] = {"n": int(m.sum()), "median": float(np.median(wa["kl"][m])) if m.any() else None,
                         "median_diff_gegen_sockel": (float(np.median(wa["kl"][m]) - np.median(pa["kl"])) if m.any() else None),
                         "ci95": ci, "lesart": ("andere Stellungen (hoeher)" if ci and ci[0] > 0
                                    else "niedriger" if ci and ci[1] < 0 else "nicht nachweisbar anders")}
            s2[sname]["je_runde"] = {str(r): float(np.median(wa["kl"][m & (wa["round"] == r)]))
                                     for r in ROUNDS if (m & (wa["round"] == r)).any()}
        out["S2"] = s2

        post = (wa["dphase"] == 0) if args.post_dice_phase else None
        s3 = {"grundmenge": "Partien (Siegquote/Punkte/Marge) bzw. Drafting-Records (Brier, Versatz) der Klasse policy-dice",
              "partien": side_game_stats(wg, len(wf)),
              "W": calibration(wa, len(wf), 0, post), "G": calibration(wa, len(wf), 1, post),
              "nur_nach_wuerfelphase": bool(args.post_dice_phase),
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
    for cls, lam in (() if args.skip_s4 else AGGR_CLASSES):
        af, aa, agm, og = read_class(cls, "aggr_side")
        st = side_game_stats(agm, len(af))
        s4["stufen"][str(lam)] = {
            "partien": st, "S": calibration(aa, len(af), 0), "G": calibration(aa, len(af), 1),
            "own_q_gap": ({"n": int(og.size), "q25": float(np.percentile(og, 25)), "median": float(np.median(og)),
                           "q75": float(np.percentile(og, 75)), "anteil_le_0": float((og <= 0).mean())}
                          if og.size else None),
            "laufzeit": manifest_runtime(data, cls)}
    base = s4["stufen"].get("0.0") if not args.skip_s4 else None
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
    if not args.skip_s4:
        out["S4"] = s4
    # --- S4b (par.5c): lexikografischer Stoerer, eps-Stufen ----------------------------------------
    if args.aggr_classes:
        sock_pts = float(np.mean([x for g in pg for x in g["scores"]])) if pg else None
        s4b = {"grundmenge": "je eps 100 Partien policy-aggr-eXX; aggr_switched/aggr_opp_drop_pts ueber Drafting-Records "
                             "der S-Seite mit echter Suche; Bezug Punkte je Seite in `policy` (G gegen G)",
               "policy_punkte_je_seite": sock_pts, "policy_laufzeit": manifest_runtime(data, "policy"), "stufen": {}}
        levels = []
        for item in args.aggr_classes.split(","):
            cls, lvl = item.split(":")
            af, aa, agm, og = read_class(cls, "aggr_side")
            dis = read_class.disrupt
            st = side_game_stats(agm, len(af))
            s4b["stufen"][lvl] = {
                "klasse": cls, "partien": st, "S": calibration(aa, len(af), 0), "G": calibration(aa, len(af), 1),
                "anteil_switched": float(np.mean(dis["switched"])) if dis["switched"] else None,
                "opp_drop_pts_mittel": float(np.mean(dis["drop"])) if dis["drop"] else None,
                "n_s_records": len(dis["switched"]),
                "own_q_gap": ({"n": int(og.size), "median": float(np.median(og)), "q75": float(np.percentile(og, 75)),
                               "max": float(og.max())} if og.size else None),
                "laufzeit": manifest_runtime(data, cls)}
            levels.append(lvl)
        chosen_eps = None
        for lvl in sorted(levels, key=float):
            stg = s4b["stufen"][lvl]["partien"]
            if (sock_pts is not None and stg["sonderseite"]["siegquote"] >= 0.45
                    and stg["G"]["punkte"] < sock_pts - 2.0):
                chosen_eps = lvl
        s4b["gewaehltes_eps"] = chosen_eps
        s4b["leseregel"] = ("groesstes eps mit S-Siegquote >= 0,45 UND G-Punkten mindestens 2 unter dem Mittel je Seite in "
                            "`policy`" + ("" if chosen_eps else " -- KEINE Stufe erfuellt das: Nutzer-Entscheid"))
        out["S4b"] = s4b
    out["laufzeit"] = laufzeit_block(t_start, cpu_start=c_start, threads=torch.get_num_threads(),
                                     n_units=len(pa["kl"]) + len(wa["kl"]), unit="zustand")
    Path(BASE_DIR / args.out).parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(BASE_DIR / args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: out[k] for k in ("S1", "S4b") if k in out}, ensure_ascii=False, indent=1)[:4000], flush=True)
    print(f"Ergebnis: {args.out} ({time.monotonic() - t_start:.1f} s)", flush=True)


if __name__ == "__main__":
    main()
