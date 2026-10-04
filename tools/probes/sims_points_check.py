"""Nachmessung Punkte und Spalten @400 gegen @100 (evaluations/PREREG_asymmetric_selfplay.md par.8c).

Vergleicht zwei GEPOOLTE Klassengruppen aus data/probe_asym, Grundmenge Partie-Seiten:

* je Gruppe die Standard-Kennzahlen ueber `tools/corpus_sanity_check.py` `auswerten` (je DATEI aufgerufen,
  damit der Block-Bootstrap ueber Dateien laufen kann): Punkte, volle Spalten, Spalten >= 4, Zeilen voll,
  Strafleiste, Plattenpunkte je Kriterium;
* Differenz A minus B je Groesse mit Block-Bootstrap-CI ueber Dateien (gepoolter Mittelwert je Ziehung =
  Summe aus Dateimittel mal Seitenzahl durch Seitenzahl);
* Kosten je Partie aus den Lauf-Manifesten;
* die Leseregel par.8c maschinell (`lesart`);
* Median-KL je Gruppe NICHT hier, sondern in `tools/probes/asym_probe_report.py --group-a ... --group-b ...`,
  das dieses Modul fuer die Kennzahlen benutzt und die KL mit seinem `read_class` dazurechnet (Netz noetig).

Ohne Netz direkt aufrufbar (nur Kennzahlen):

    python -X utf8 -u tools/probes/sims_points_check.py --group-a policy-s400-m2,policy-s400-m2-b \
        --group-b policy-m2,policy-m2-400g --out evaluations/artifacts/x.json
"""
from __future__ import annotations

import argparse
import contextlib
import glob
import io
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "tools"))

import corpus_sanity_check  # noqa: E402
from runtime_block import laufzeit_block  # noqa: E402

N_BOOT = 2000
BOOT_SEED = 20261730
# Groessen je Seite aus `auswerten`: Schluessel -> Beschriftung.
SIDE_KEYS = {
    "punkte": "Punkte je Seite",
    "sp_voll": "volle Spalten je Seite",
    "sp_ge4": "Spalten >= 4 je Seite",
    "zeilen_voll": "volle Zeilen je Seite",
    "floor": "Strafleiste (Steine) je Seite",
}
# Leseregel par.8c: Schwellen der Schaetzer (A minus B).
POINTS_THRESHOLD = -1.0
COLUMNS_THRESHOLD = -0.03


def class_files(data: Path, cls: str) -> list[str]:
    return sorted(glob.glob(str(data / f"selfplay_probe-v35-{cls}_*.pkl")))


def manifest_runtime(data: Path, cls: str):
    mans = sorted(glob.glob(str(data / f"manifest_probe-v35-{cls}_*.json")))
    if not mans:
        return None
    return json.load(open(mans[-1], encoding="utf-8")).get("laufzeit")


def per_file_metrics(data: Path, files: list[str]) -> list[dict]:
    """`auswerten` je Datei, Ausgabe unterdrueckt. Je Datei: Seitenzahl, Mittel je Groesse aus SIDE_KEYS und
    je Kriterium (Plattenpunkte-Mittel, Zahl der Seiten mit aktivem Kriterium = 2 x Partien)."""
    out = []
    for f in files:
        with contextlib.redirect_stdout(io.StringIO()):
            r = corpus_sanity_check.auswerten(str(data), files=[f])
        row = {"datei": os.path.basename(f), "seiten": int(r["seiten"])}
        for k in SIDE_KEYS:
            row[k] = float(r[k]) if r["seiten"] else float("nan")
        row["platten"] = {name: (float(v["punkte"]), 2 * int(v["aktiv_in_partien"]))
                          for name, v in (r.get("platten") or {}).items()}
        out.append(row)
    return out


def pooled_mean(rows: list[dict], key: str) -> float:
    """Mittel ueber alle Seiten der Dateien (Dateimittel mit Seitenzahl gewichtet)."""
    n = sum(r["seiten"] for r in rows if r["seiten"])
    if not n:
        return float("nan")
    return sum(r[key] * r["seiten"] for r in rows if r["seiten"]) / n


def pooled_plate(rows: list[dict], name: str) -> float:
    pairs = [r["platten"][name] for r in rows if name in r["platten"] and r["platten"][name][1]]
    n = sum(w for _, w in pairs)
    return sum(m * w for m, w in pairs) / n if n else float("nan")


def boot_diff(rows_a: list[dict], rows_b: list[dict], stat, rng, n_boot: int = N_BOOT):
    """95-%-Perzentil-CI von stat(A) - stat(B), A und B je fuer sich ueber ihre Dateien gezogen."""
    if not rows_a or not rows_b:
        return None
    ka, kb = len(rows_a), len(rows_b)
    draws = []
    for _ in range(n_boot):
        a = [rows_a[i] for i in rng.integers(0, ka, ka)]
        b = [rows_b[i] for i in rng.integers(0, kb, kb)]
        d = stat(a) - stat(b)
        if np.isfinite(d):
            draws.append(d)
    if not draws:
        return None
    return [float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))]


def reading(points: dict, columns: dict) -> dict:
    """Leseregel par.8c. `points`/`columns`: {"differenz": Schaetzer A-B, "ci95": [lo, hi]}."""
    def no_loss(d, threshold):
        ci = d.get("ci95")
        est = d.get("differenz")
        return bool((ci and ci[0] <= 0.0 <= ci[1]) or (est is not None and est > threshold))

    def loss(d, threshold):
        ci = d.get("ci95")
        est = d.get("differenz")
        return bool(ci and ci[1] < 0.0 and est is not None and est <= threshold)

    points_ok, columns_ok = no_loss(points, POINTS_THRESHOLD), no_loss(columns, COLUMNS_THRESHOLD)
    points_loss, columns_loss = loss(points, POINTS_THRESHOLD), loss(columns, COLUMNS_THRESHOLD)
    if points_loss or columns_loss:
        verdict = ("Verlust nachweisbar: Mischsockel 1.000 @100 plus 1.000 @400 (beide Modus 2) als Vorschlag, "
                   "Nutzer-Entscheid")
    elif points_ok and columns_ok:
        verdict = "kein Verlust nachweisbar: Hauptklasse bleibt rein @400"
    else:
        verdict = "keine der beiden Regeln greift eindeutig: berichtet, Nutzer-Entscheid"
    return {"punkte_kein_verlust": points_ok, "spalten_kein_verlust": columns_ok,
            "punkte_verlust": points_loss, "spalten_verlust": columns_loss, "verdikt": verdict,
            "regel": ("Punktdifferenz-CI enthaelt 0 ODER Schaetzer > -1,0, UND Spaltendifferenz-CI enthaelt 0 ODER "
                      "Schaetzer > -0,03 -> kein Verlust; Punktdifferenz-CI ganz unter 0 mit Schaetzer <= -1,0 ODER "
                      "Spaltendifferenz-CI ganz unter 0 mit Schaetzer <= -0,03 -> Mischsockel (par.8c)")}


def compare_groups(data: Path, group_a: list[str], group_b: list[str], n_boot: int = N_BOOT,
                   seed: int = BOOT_SEED) -> dict:
    """Kennzahlen, Differenzen mit CI, Kosten und Lesart fuer zwei gepoolte Gruppen (ohne KL)."""
    rng = np.random.default_rng(seed)
    files = {cls: class_files(data, cls) for cls in group_a + group_b}
    missing = [c for c, fs in files.items() if not fs]
    if missing:
        raise SystemExit(f"Klassen ohne Dateien in {data}: {missing}")
    rows = {}
    for name, group in (("A", group_a), ("B", group_b)):
        rows[name] = []
        for cls in group:
            rows[name] += per_file_metrics(data, files[cls])
            print(f"[points] Gruppe {name}: {cls} gelesen ({len(files[cls])} Dateien)", flush=True)
    ra, rb = rows["A"], rows["B"]
    groups = {}
    for name, group, rr in (("A", group_a, ra), ("B", group_b, rb)):
        groups[name] = {"klassen": group, "dateien": len(rr), "seiten": sum(r["seiten"] for r in rr),
                        "kennzahlen": {k: pooled_mean(rr, k) for k in SIDE_KEYS}}
    diffs = {}
    for k, label in SIDE_KEYS.items():
        stat = (lambda key: (lambda rs: pooled_mean(rs, key)))(k)
        diffs[k] = {"beschriftung": label, "differenz": stat(ra) - stat(rb), "ci95": boot_diff(ra, rb, stat, rng, n_boot)}
    plates = sorted({n for r in ra + rb for n in r["platten"]})
    plate_diffs = {}
    for name in plates:
        stat = (lambda nm: (lambda rs: pooled_plate(rs, nm)))(name)
        plate_diffs[name] = {"A": stat(ra), "B": stat(rb), "differenz": stat(ra) - stat(rb),
                             "ci95": boot_diff(ra, rb, stat, rng, n_boot)}
    costs = {cls: manifest_runtime(data, cls) for cls in group_a + group_b}
    return {
        "prereg": "evaluations/PREREG_asymmetric_selfplay.md par.8c",
        "grundmenge": "Partie-Seiten der gepoolten Klassen (Endzustand je Partie, corpus_sanity_check.auswerten)",
        "einheit": "Mittel je Seite; Differenz A minus B, CI Block-Bootstrap ueber Dateien",
        "n_boot": n_boot, "boot_seed": seed,
        "gruppen": groups, "differenz_a_minus_b": diffs,
        "plattenpunkte_je_kriterium": plate_diffs,
        "kosten_je_klasse": costs,
        "lesart": reading(diffs["punkte"], diffs["sp_voll"]),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", default="data/probe_asym")
    ap.add_argument("--group-a", required=True, help="Klassen der Gruppe A, kommagetrennt (z. B. die @400-Klassen)")
    ap.add_argument("--group-b", required=True, help="Klassen der Gruppe B, kommagetrennt (Bezug)")
    ap.add_argument("--n-boot", type=int, default=N_BOOT)
    ap.add_argument("--out", default="evaluations/artifacts/probe_s400_points_check.json")
    args = ap.parse_args()
    t_start, c_start = time.monotonic(), time.process_time()
    data = BASE_DIR / args.data_dir
    out = compare_groups(data, args.group_a.split(","), args.group_b.split(","), args.n_boot)
    out["laufzeit"] = laufzeit_block(t_start, cpu_start=c_start, threads=1,
                                     n_units=out["gruppen"]["A"]["seiten"] + out["gruppen"]["B"]["seiten"],
                                     unit="seite")
    Path(BASE_DIR / args.out).parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(BASE_DIR / args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"lesart": out["lesart"], "differenz": out["differenz_a_minus_b"]}, ensure_ascii=False, indent=1),
          flush=True)
    print(f"Ergebnis: {args.out} ({time.monotonic() - t_start:.1f} s)", flush=True)


if __name__ == "__main__":
    main()
