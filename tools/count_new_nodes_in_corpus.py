# -*- coding: utf-8 -*-
"""Wieviel LERNSTOFF tragen die neuen Suchknoten in einer Korpus-Klasse?

Vorregistrierte Nachzaehlung: `PREREG_v30_window.md` par.1b sagt ausdruecklich
"Nachzaehlung gehoert in par.9" -- zum Zeitpunkt der Vorregistrierung gab es die
Dateien noch nicht. Beantwortet wird genau eine Frage: an wievielen Records
haengt ueberhaupt ein Policy-ZIEL an den Knoten 406-413 (Mond, Rueckgabe) und an
den aelteren Hilfsknoten, und wie oft steht der Knoten nur in der Maske.

ZAEHLWEISE uebernommen aus `tools/night_v30_acceptance_b11.sh` Stufe 7 (dieselben
Bereiche, dieselbe ID-Ableitung ueber `neural_net.action_to_id`), mit EINEM
Unterschied: die Records werden mit `gzip.open` gelesen (Vorfall 2026-09-18,
`docs/pitfalls.md` -- `pickle.load` auf der Datei scheitert am Magic 0x1f).

GRUNDMENGE: die gezogene Stichprobe von Dateien EINER Klasse, Einheit Records
beziehungsweise Vorkommen je Record. Die Ziehung ist seed-fest.

Aufruf:
    python -X utf8 -u tools/count_new_nodes_in_corpus.py v29-b11-policy --sample 40 \
        --out evaluations/artifacts/new_nodes_v29-b11-policy.json
"""
import argparse, glob, gzip, io, json, os, pickle, random, sys, time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "engine" / "py"))
sys.path.insert(0, str(REPO))
from neural_net import action_to_id, UnknownActionTypeError  # noqa: E402
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # corpus_io liegt in der Wurzel
from corpus_io import load_records  # noqa: E402

RANGES = [("mond 406-410", 406, 410), ("rueckgabe 411-413", 411, 413),
            ("slot/rotation kuppel 328-354", 328, 354),
            ("slot/rotation stapel 355-390", 355, 390),
            ("rotation 391-394", 391, 394),
            ("stapel-blick 405", 405, 405)]




def ids_of(entries, unknown_types):
    out = []
    for e in entries or []:
        if not isinstance(e, dict):
            continue
        act = e["action"] if isinstance(e.get("action"), dict) else e
        try:
            out.append(action_to_id(act))
        except UnknownActionTypeError as exc:
            unknown_types.add(str(exc)[:60])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("corpus_class", help="Namensstamm, z.B. v29-b11-policy")
    ap.add_argument("--data-dir", default=str(REPO / "data"))
    ap.add_argument("--sample", type=int, default=40, help="0 = all_files Dateien")
    ap.add_argument("--seed", type=int, default=20260945)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    all_files = sorted(glob.glob(os.path.join(a.data_dir, f"selfplay_{a.corpus_class}_*.pkl")))
    if not all_files:
        raise SystemExit(f"keine Dateien fuer {a.corpus_class}")
    if a.sample and a.sample < len(all_files):
        random.Random(a.seed).shuffle(all_files)
        files = sorted(all_files[:a.sample])
    else:
        files = all_files
    print(f"Klasse {a.corpus_class}: {len(files)} von {len(all_files)} Dateien (Seed {a.seed})", flush=True)

    t0 = time.time()
    target_hits = {n: 0 for n, _, _ in RANGES}      # Vorkommen im Policy-ZIEL
    mask_hits = {n: 0 for n, _, _ in RANGES}     # Vorkommen in valid_actions
    records_with_target = {n: 0 for n, _, _ in RANGES}  # RECORDS mit mindestens einem Ziel
    records_with_mask = {n: 0 for n, _, _ in RANGES}
    total = designs = designs_ordered = 0
    new_node_records = new_node_empty_policy = 0
    unknown_types = set()

    for i, fp in enumerate(files, 1):
        for r in load_records(fp):
            total += 1
            if not isinstance(r, dict):
                continue
            blob = json.dumps(r.get("state"), default=str)
            if '"designs"' in blob:
                designs += 1
            if "designs_ordered" in blob:
                designs_ordered += 1
            pol = ids_of(r.get("policy"), unknown_types)
            val = ids_of(r.get("valid_actions"), unknown_types)
            pol_set, val_set = set(pol), set(val)
            for n, lo, hi in RANGES:
                z = sum(1 for x in pol if lo <= x <= hi)
                m = sum(1 for x in val if lo <= x <= hi)
                target_hits[n] += z
                mask_hits[n] += m
                records_with_target[n] += 1 if any(lo <= x <= hi for x in pol_set) else 0
                records_with_mask[n] += 1 if any(lo <= x <= hi for x in val_set) else 0
            if any(x >= 406 for x in val_set):
                new_node_records += 1
                if not r.get("policy"):
                    new_node_empty_policy += 1
        if i % 10 == 0 or i == len(files):
            print(f"   {i}/{len(files)} Dateien, {total} Records ({time.time()-t0:.0f} s)", flush=True)

    print(f"\nRecords insgesamt: {total}   (Grundmenge aller Anteile unten)")
    print(f"P.12 `designs` im Zustand      : {designs} Records ({designs/total*100:.1f} %)")
    print(f"P.16 `designs_ordered`          : {designs_ordered} Records ({designs_ordered/total*100:.1f} %)")
    print(f"\n{'Knotenbereich':32s} {'Records m. ZIEL':>16s} {'Anteil':>8s} {'Records i. Maske':>17s} "
          f"{'Ziel-Vorkommen':>15s}")
    for n, _, _ in RANGES:
        print(f"{n:32s} {records_with_target[n]:16d} {records_with_target[n]/total*100:7.2f}% {records_with_mask[n]:17d} {target_hits[n]:15d}")
    print(f"\nRecords mit einer ID >= 406 in der Maske: {new_node_records} "
          f"({new_node_records/total*100:.2f} %), davon mit LEEREM policy: {new_node_empty_policy}")
    if unknown_types:
        print(f"WARNUNG: unbekannte Aktionstypen: {sorted(unknown_types)}")
    duration = time.time() - t0
    print(f"\nLaufzeit {duration:.1f} s")

    if a.out:
        result = {"klasse": a.corpus_class, "dateien": len(files), "dateien_gesamt": len(all_files),
               "seed": a.seed, "records": total, "designs": designs,
               "designs_ordered": designs_ordered,
               "records_mit_ziel": records_with_target, "records_in_maske": records_with_mask,
               "ziel_vorkommen": target_hits, "maske_vorkommen": mask_hits,
               "records_maske_ab_406": new_node_records, "davon_policy_leer": new_node_empty_policy,
               "laufzeit": {"wanduhr_s": round(duration, 1), "cpu_s": None, "threads": 1,
                            "s_je_datei": round(duration / len(files), 3)}}
        os.makedirs(os.path.dirname(a.out), exist_ok=True)
        io.open(a.out, "w", encoding="utf-8").write(json.dumps(result, ensure_ascii=False, indent=2))
        print(f"Artefakt: {a.out}")


if __name__ == "__main__":
    main()
