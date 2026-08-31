# -*- coding: utf-8 -*-
"""Fixier-Test: nativ ist der DEFAULT, entstaucht nur die Blockliste.

Verlangt von `evaluations/PREREG_heuristic_v2_long_rows.md` par.3b.3
"Nachtrag Stufe 0" Punkt 3 -- der Umbau aendert eine ZIELDEFINITION, und der
Fehler, den er behebt, war STILL: `selfplay_hv2_*` fiel nicht unter die alte
Allowliste `WDL_GENERATOR_PREFIXES`, sein nativer [0,1]-Bootstrap lief also
durch die Platt-Streckung (Logit mal B=1,9269), und nichts im Lauf hat das
angezeigt. Dieser Test nagelt beide Seiten fest, damit die Umkehr nicht
irgendwann still zurueckkippt.

Geprueft wird an EINER echten Korpusdatei, zweimal unter verschiedenem Namen
in ein Temp-Verzeichnis kopiert (kein fabrizierter Zustand -- die Records
sollen die sein, die auch trainiert werden):

  A) NATIV: Basename `selfplay_hv2_*` (nicht in `LEGACY_STRETCHED_PREFIXES`)
     -> `values_wdl` traegt den ROHEN `bootstrap_value`, geblendet mit
     TD_LAMBDA gegen den harten Ausgang. Der TD-Blend wird aus den Records
     unabhaengig nachgerechnet und muss exakt herauskommen.
  B) ALT: Basename `selfplay_v18_*` (in der Blockliste) -> derselbe Record
     liefert den ENTSTAUCHTEN Wert, ebenfalls nachgerechnet.
  C) Gegenprobe, dass der Test etwas sieht: A und B muessen sich
     unterscheiden (sonst wuerde er auch bei kaputter Fallunterscheidung
     gruen).
  D) Cache-Schluessel: derselbe Dateiname mit verschiedenem
     `bootstrap_native` muss verschiedene per-Datei-Schluessel ergeben --
     sonst zoege ein Lauf nach der Umkehr still die Bestands-Bloecke mit den
     entstauchten Zielen.

Aufruf (netzfrei, eine Korpusdatei, Sekunden):
    python -X utf8 -u tools/probes/bootstrap_native_default_probe.py
    python -X utf8 -u tools/probes/bootstrap_native_default_probe.py --file <pfad.pkl>
"""
import argparse
import glob
import json
import math
import os
import pathlib
import shutil
import sys
import tempfile

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "engine" / "py"))

PREREG = "PREREG_heuristic_v2_long_rows.md par.3b.3 (Nachtrag Stufe 0, Punkt 3)"

# Namen der beiden Kopien. Der ALT-Name muss ein echter Blocklisten-Praefix
# sein; er wird unten gegen die Konstante geprueft, damit dieser Test nicht
# still an einer umbenannten Blockliste vorbeilaeuft.
NATIVE_NAME = "selfplay_hv2_20260101_0000_g10.pkl"
LEGACY_NAME = "selfplay_v18_20260101_0000_g10.pkl"

TOLERANCE = 1e-6


def expected_wdl_targets(records, td_lambda, destretch):
    """Rechnet das `values_wdl`-Ziel je Record unabhaengig nach.

    Bewusst NICHT aus `corpus_dataset` importiert, sondern nach der Formel aus
    dem Baucode (corpus_dataset.py, WDL-Zweig) nachgebaut: ein Test, der
    dieselbe Funktion aufruft, die er prueft, kann die Fallunterscheidung
    nicht mehr falsifizieren.
    """
    out = []
    for step in records:
        p = int(step["player"])
        completed = step.get("completed", True) is not False
        if not completed or "winner" not in step or step["winner"] is None:
            out.append(None)          # Sentinel-Zweig, hier nicht Gegenstand
            continue
        outcome = 1.0 if int(step["winner"]) == p else 0.0
        bv = step.get("bootstrap_value")
        if bv is None:
            out.append(outcome)
            continue
        bvp = float(bv[p])
        if destretch:
            bvp = destretch_prob(bvp)
        out.append(min(1.0, max(0.0, td_lambda * bvp + (1.0 - td_lambda) * outcome)))
    return out


def destretch_prob(p, a=None, b=None):
    """Platt-Streckung, Formel aus corpus_dataset._destretch_prob."""
    import neural_net
    a = neural_net.DESTRETCH_A if a is None else a
    b = neural_net.DESTRETCH_B if b is None else b
    p = min(max(p, 1e-6), 1.0 - 1e-6)
    z = math.log(p / (1.0 - p))
    return 1.0 / (1.0 + math.exp(-(a + b * z)))


def build_targets(tmp_dir, src_pkl, name):
    """Kopiert `src_pkl` unter `name` und baut daraus die Ziele."""
    dst = os.path.join(tmp_dir, name)
    shutil.copyfile(src_pkl, dst)
    import corpus_dataset
    ds = corpus_dataset.MosaicDataset(tmp_dir, files=[dst], encoder="flat")
    # `values_wdl` kann [N] oder [N,1] sein -- flach lesen, ein Wert je Zug.
    return [float(x) for x in ds.values_wdl.reshape(-1).tolist()]


def compare(label, got, want, findings, failures):
    """Vergleicht Ist gegen unabhaengige Nachrechnung, nur ueber die Records
    mit hartem Ausgang (Sentinel-Zweig traegt eine weiche Projektion und ist
    hier nicht Gegenstand)."""
    checked = 0
    worst = 0.0
    worst_at = None
    for i, w in enumerate(want):
        if w is None or i >= len(got):
            continue
        d = abs(got[i] - w)
        checked += 1
        if d > worst:
            worst, worst_at = d, i
    ok = checked > 0 and worst <= TOLERANCE
    findings[label] = {"geprueft": checked, "groesste_abweichung": worst,
                       "bei_index": worst_at, "ok": ok}
    print(f"  {'OK  ' if ok else 'ROT '} {label:34s} n={checked:5d}  max|delta|={worst:.3e}",
          flush=True)
    if not ok:
        failures.append(label)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--file", default=None,
                    help="Korpusdatei (Default: die erste data/selfplay_hv2_*.pkl).")
    args = ap.parse_args()

    import neural_net
    from corpus_io import load_records

    # Selbstschutz: die Namen dieses Tests muessen zur Blockliste passen.
    if NATIVE_NAME.startswith(neural_net.LEGACY_STRETCHED_PREFIXES):
        print(f"ROT -- {NATIVE_NAME} faellt unter LEGACY_STRETCHED_PREFIXES; "
              "der 'nativ'-Fall dieses Tests ist gegenstandslos.", file=sys.stderr)
        return 1
    if not LEGACY_NAME.startswith(neural_net.LEGACY_STRETCHED_PREFIXES):
        print(f"ROT -- {LEGACY_NAME} faellt NICHT unter LEGACY_STRETCHED_PREFIXES; "
              "der 'entstaucht'-Fall dieses Tests ist gegenstandslos.", file=sys.stderr)
        return 1

    src = args.file
    if src is None:
        candidates = sorted(glob.glob(str(_ROOT / "data" / "selfplay_hv2_*.pkl")))
        if not candidates:
            print("ROT -- keine data/selfplay_hv2_*.pkl gefunden; --file angeben.",
                  file=sys.stderr)
            return 1
        src = candidates[0]
    print(f"Quelle: {os.path.basename(src)}", flush=True)
    print(f"TD_LAMBDA={neural_net.TD_LAMBDA}  "
          f"DESTRETCH_A={neural_net.DESTRETCH_A} DESTRETCH_B={neural_net.DESTRETCH_B}",
          flush=True)
    print(f"Blockliste: {neural_net.LEGACY_STRETCHED_PREFIXES}", flush=True)

    records = load_records(src)
    want_native = expected_wdl_targets(records, neural_net.TD_LAMBDA, destretch=False)
    want_legacy = expected_wdl_targets(records, neural_net.TD_LAMBDA, destretch=True)

    findings = {"prereg": PREREG, "quelle": os.path.basename(src),
                "td_lambda": neural_net.TD_LAMBDA,
                "blockliste": list(neural_net.LEGACY_STRETCHED_PREFIXES)}
    failures = []

    with tempfile.TemporaryDirectory(prefix="bsnative_") as tmp:
        got_native = build_targets(tmp, src, NATIVE_NAME)
        got_legacy = build_targets(tmp, src, LEGACY_NAME)

    # --- A) hv2-Name -> ROHER Bootstrap im Ziel
    compare("A nativ (hv2) = roh", got_native, want_native, findings, failures)
    # --- B) Blocklisten-Name -> ENTSTAUCHTER Bootstrap im Ziel
    compare("B alt (v18) = entstaucht", got_legacy, want_legacy, findings, failures)

    # --- C) Gegenprobe: die beiden Faelle muessen sich unterscheiden
    n = min(len(got_native), len(got_legacy))
    spread = max((abs(got_native[i] - got_legacy[i]) for i in range(n)), default=0.0)
    differs = spread > TOLERANCE
    findings["C unterschied nativ/alt"] = {"groesste_differenz": spread, "ok": differs}
    print(f"  {'OK  ' if differs else 'ROT '} {'C nativ != alt':34s} n={n:5d}  "
          f"max|delta|={spread:.3e}", flush=True)
    if not differs:
        failures.append("C nativ != alt")

    # --- D) Cache-Schluessel unterscheidet die Zieldefinition
    kw = dict(value_target_variant="default", encoder="flat",
              conjunction_head=False)
    k_native = neural_net.per_file_cache_key(NATIVE_NAME, bootstrap_native=True, **kw)
    k_legacy = neural_net.per_file_cache_key(NATIVE_NAME, bootstrap_native=False, **kw)
    key_ok = k_native != k_legacy
    findings["D cache-key"] = {"nativ": k_native, "entstaucht": k_legacy, "ok": key_ok}
    print(f"  {'OK  ' if key_ok else 'ROT '} {'D per-Datei-Schluessel trennt':34s} "
          f"{k_native} / {k_legacy}", flush=True)
    if not key_ok:
        failures.append("D cache-key")

    findings["verdikt"] = "GRUEN" if not failures else "ROT"
    findings["versagt"] = failures
    target = _ROOT / "evaluations" / "artifacts" / "bootstrap_native_default_probe.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(findings, indent=2, ensure_ascii=False),
                      encoding="utf-8", newline="\n")
    print(f"\nArtefakt: {target}")

    if failures:
        print(f"\nROT -- {', '.join(failures)}", file=sys.stderr)
        return 1
    print("\nGRUEN -- nativ ist Default, entstaucht wird nur die Blockliste.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
