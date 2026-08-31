# -*- coding: utf-8 -*-
"""Erzeuger fuer Policy-Traeger-Manifeste (Rekonstruktion, 2026-08-29).

Schliesst die Luecke aus STATUS ("TRAEGER-MANIFEST-GENERATOR fehlt"): im Baum
gab es nur LESER (corpus_dataset.py, train_manifest.py); das v20-Manifest
wurde laut PREREG_v20_campaign.md mit "Seed 20260806, zeitlich gestreute
Auswahl" ERZEUGT, das Skript aber nie committet (archive/history.md,
Berichtigung 2026-08-25). Dieses Werkzeug rekonstruiert die dokumentierte
Regel, ohne Kampagnen-Zahlen einzubacken -- Anzahl, Seed und Kandidatenmenge
sind Parameter; der konkrete v23-Zuschnitt (PREREG_v23_window.md par.1:
1.800 policy-aktive hv2-Partien) wird beim Aufruf der Kampagne registriert.

Auswahlregel ("zeitlich gestreute Auswahl", deterministisch):
  1. Kandidaten = sortierte Dateinamen (Namens-Sortierung = zeitliche
     Ordnung, die Zeitstempel stehen im Namen).
  2. Aufteilung in n Zeit-Straten moeglichst gleicher Groesse.
  3. Je Stratum EINE Datei, gezogen mit random.Random(seed) -- dieselbe
     Eingabe ergibt byte-gleich dasselbe Manifest.

Ausgabeformat = das, was die Leser erwarten (corpus_dataset.py:
`policy_carrier_files`; `carrier_prefixes` wird bewusst NICHT geschrieben --
das Feld wuerde den bootstrap_native-Kurzschluss abschalten, siehe dortigen
Kommentar), plus Herkunftskopf (`seed`, `design`) wie beim v20-Vorbild.

Aufruf (Beispiel, Zahlen sind KEINE Vorgabe):
    python tools/generate_carrier_manifest.py --pattern "selfplay_hv2_*.pkl" \
        --n-files 180 --seed 20260829 --out policy_carrier_manifest_v23.json
Kandidaten einschraenken (z.B. auf ein Rotationsfenster):
    --from-list <textdatei>   # ein Basename je Zeile, #-Kommentare erlaubt
Nur anzeigen, nichts schreiben: --dry-run
Zusaetzlich eine --file-list-kompatible Textdatei der Auswahl: --list-out
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import random
import sys
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_candidate_list(path):
    names = []
    for line in open(path, encoding="utf-8"):
        s = line.strip()
        if s and not s.startswith("#"):
            names.append(os.path.basename(s))
    return names


def stratified_pick(candidates, n_files, seed):
    """Je Zeit-Stratum eine Datei; deterministisch aus (candidates, n, seed)."""
    if n_files > len(candidates):
        raise SystemExit(f"n-files {n_files} > Kandidaten {len(candidates)}")
    rng = random.Random(seed)
    picked = []
    # Straten-Grenzen ueber Ganzzahl-Arithmetik: Stratum i = [i*L//n, (i+1)*L//n)
    length = len(candidates)
    for i in range(n_files):
        lo, hi = i * length // n_files, (i + 1) * length // n_files
        picked.append(candidates[rng.randrange(lo, hi)])
    return picked


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--pattern", default="selfplay_hv2_*.pkl",
                    help="Glob fuer die Kandidatenmenge")
    ap.add_argument("--from-list", default=None,
                    help="Kandidaten auf diese Liste einschraenken (ein Basename "
                         "je Zeile; fehlende Dateien brechen hart ab)")
    ap.add_argument("--n-files", type=int, required=True,
                    help="Anzahl Traeger-DATEIEN (Partien = Dateien x Partien/Datei; "
                         "das g-Suffix im Namen traegt den Zaehlstand)")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--out", required=True,
                    help="Manifest-Dateiname (landet in --data-dir)")
    ap.add_argument("--list-out", default=None,
                    help="zusaetzlich eine --file-list-kompatible Textdatei der Auswahl")
    ap.add_argument("--include-glob", default=None,
                    help="Glob, dessen Treffer VOLLSTAENDIG als Traeger dazukommen -- "
                         "ohne Stichprobe, zusaetzlich zur gestreuten Auswahl. Gedacht "
                         "fuer eine Korpus-Klasse, die per Design komplett Policy traegt "
                         "(v23: die Sockel-/Policy-Klasse). Ohne das wuerde ein Manifest "
                         "sie stillschweigend maskieren, denn Nicht-Gelistete sind "
                         "Nicht-Traeger (corpus_dataset._is_policy_carrier)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    candidates = sorted(os.path.basename(f)
                        for f in glob.glob(os.path.join(a.data_dir, a.pattern)))
    if a.from_list:
        allowed = load_candidate_list(a.from_list)
        missing = [n for n in allowed if n not in set(candidates)]
        if missing:
            raise SystemExit(f"--from-list: {len(missing)} Eintraege nicht in "
                             f"{a.data_dir}/{a.pattern}, z.B. {missing[:3]}")
        candidates = sorted(allowed)
    if not candidates:
        raise SystemExit(f"Keine Kandidaten fuer {a.pattern} in {a.data_dir}")

    picked = stratified_pick(candidates, a.n_files, a.seed)

    # Vollstaendig uebernommene Klasse (kein Ziehen): getrennt gehalten, damit
    # `design` ehrlich bleibt -- die Stichprobe betrifft nur `picked`.
    included = []
    if a.include_glob:
        included = sorted(os.path.basename(f)
                          for f in glob.glob(os.path.join(a.data_dir, a.include_glob)))
        if not included:
            raise SystemExit(f"--include-glob {a.include_glob!r}: kein Treffer in {a.data_dir} "
                             "-- laut statt still, sonst maskiert das Manifest die Klasse")
        overlap = sorted(set(included) & set(picked))
        if overlap:
            raise SystemExit(f"--include-glob ueberschneidet die Stichprobe ({len(overlap)} "
                             f"Dateien, z.B. {overlap[:3]}) -- Kandidatenmenge trennen")
        print(f"{len(included)} Dateien vollstaendig uebernommen (--include-glob "
              f"{a.include_glob})")

    manifest = {
        "generator": "tools/generate_carrier_manifest.py",
        "erzeugt": time.strftime("%Y-%m-%d %H:%M:%S"),
        "seed": a.seed,
        "design": (f"zeitlich gestreute Auswahl: {a.n_files} Zeit-Straten ueber "
                   f"{len(candidates)} sortierte Kandidaten ({a.pattern}"
                   + (f", eingeschraenkt per {os.path.basename(a.from_list)}" if a.from_list else "")
                   + "), je Stratum eine Datei via random.Random(seed)"),
        "include_glob": a.include_glob,
        "policy_carrier_files": sorted(picked + included),
    }
    print(f"{len(picked)} von {len(candidates)} Dateien gewaehlt "
          f"(Seed {a.seed}); erste/letzte: {picked[0]} / {picked[-1]}")
    if a.dry_run:
        print("--dry-run: nichts geschrieben")
        return
    out_path = os.path.join(a.data_dir, a.out)
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    print(f"Manifest geschrieben: {out_path}")
    if a.list_out:
        with open(a.list_out, "w", encoding="utf-8", newline="\n") as f:
            f.write(f"# Auswahl aus {a.pattern}, Seed {a.seed} (generate_carrier_manifest)\n")
            f.write("\n".join(picked) + "\n")
        print(f"Dateiliste geschrieben: {a.list_out}")


if __name__ == "__main__":
    main()
