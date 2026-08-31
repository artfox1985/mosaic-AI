# -*- coding: utf-8 -*-
"""Abnahme fuer Arm K: Bootstrap-Kohaerenz (Summen-Normierung) im WDL-Ziel.

Verlangt von `evaluations/PREREG_heuristic_v2_long_rows.md` par.3b.3
("Arm K -- Bootstrap-Kohaerenz"), eingetaktet VOR das v23-Training in
`PREREG_v23_window.md` par.4a2. Der Arm aendert eine ZIELDEFINITION und
wird VOR dem Caching eingerechnet -- dieselbe Fehlerklasse wie der
Nativ-Default (par.3b.3 Punkt 3), und darum derselbe Abnahme-Zuschnitt:

  A) MOSAIC_BOOTSTRAP_COHERENCE nicht gesetzt / "off" -> `values_wdl`
     traegt den unveraenderten Blend (Bestandsverhalten).
  B) "sum1" -> die beiden `bootstrap_value`-Eintraege eines Zustands
     werden vor dem Blend auf Summe 1 normiert; unabhaengig nachgerechnet.
  C) Gegenprobe, dass der Test etwas sieht: A und B muessen sich auf
     echten Records unterscheiden.
  D) Cache-Schluessel: "off" und "sum1" muessen verschiedene Schluessel
     ergeben (per-Datei UND Fenster), und "off" muss exakt den Schluessel
     des ungesetzten Knopfes treffen -- sonst verfaellt Bestand.
  E) Berichtsgroessen ohne Torfunktion: mittlere Bootstrap-Paarsumme (der
     Stufe-0-Befund lag bei ~1,13-1,14) und die mittlere Ziel-Verschiebung.

Die Nachrechnung ist BEWUSST nicht aus `corpus_dataset` importiert,
sondern nach der Formel des Baucodes nachgebaut -- ein Test, der dieselbe
Funktion aufruft, die er prueft, kann die Fallunterscheidung nicht mehr
falsifizieren (Muster aus bootstrap_native_default_probe.py).

Aufruf (netzfrei, eine Korpusdatei, Sekunden):
    python -X utf8 -u tools/probes/bootstrap_coherence_probe.py
    python -X utf8 -u tools/probes/bootstrap_coherence_probe.py --file <pfad.pkl>
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
import time

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "engine" / "py"))

PREREG = "PREREG_heuristic_v2_long_rows.md par.3b.3 (Arm K), PREREG_v23_window.md par.4a2"

# Der Test laeuft unter einem NATIV-Namen (nicht in der Blockliste): die
# Entstauchung ist hier nicht Gegenstand, sie hat ihren eigenen Test.
PROBE_NAME = "selfplay_hv2_20260101_0000_g10.pkl"

TOLERANCE = 1e-6


def destretch_prob(p):
    """Platt-Streckung, Formel aus corpus_dataset._destretch_prob."""
    import neural_net
    p = min(max(p, 1e-6), 1.0 - 1e-6)
    z = math.log(p / (1.0 - p))
    return 1.0 / (1.0 + math.exp(-(neural_net.DESTRETCH_A + neural_net.DESTRETCH_B * z)))


def expected_wdl_targets(records, td_lambda, *, destretch, sum1):
    """Rechnet das `values_wdl`-Ziel je Record unabhaengig nach.

    Gibt (ziele, paarsummen) zurueck; `ziele[i] is None` markiert den
    Sentinel-Zweig (abgebrochene Partie), der hier nicht Gegenstand ist.
    """
    out, pair_sums = [], []
    for step in records:
        p = int(step["player"])
        completed = step.get("completed", True) is not False
        if not completed or "winner" not in step or step["winner"] is None:
            out.append(None)
            continue
        outcome = 1.0 if int(step["winner"]) == p else 0.0
        bv = step.get("bootstrap_value")
        if bv is None:
            out.append(outcome)
            continue
        bvp = float(bv[p])
        bvo = float(bv[1 - p])
        if destretch:
            bvp, bvo = destretch_prob(bvp), destretch_prob(bvo)
        pair_sums.append(bvp + bvo)
        if sum1 and (bvp + bvo) > 0.0:
            bvp = bvp / (bvp + bvo)
        out.append(min(1.0, max(0.0, td_lambda * bvp + (1.0 - td_lambda) * outcome)))
    return out, pair_sums


def build_targets(tmp_dir, src_pkl, name, mode):
    """Kopiert `src_pkl` unter `name` und baut daraus die Ziele im Modus `mode`.

    `mode is None` = Knopf NICHT gesetzt (der Bestandsfall).
    """
    dst = os.path.join(tmp_dir, name)
    if not os.path.exists(dst):
        shutil.copyfile(src_pkl, dst)
    prev = os.environ.pop("MOSAIC_BOOTSTRAP_COHERENCE", None)
    try:
        if mode is not None:
            os.environ["MOSAIC_BOOTSTRAP_COHERENCE"] = mode
        import corpus_dataset
        ds = corpus_dataset.MosaicDataset(tmp_dir, files=[dst], encoder="flat")
        return [float(x) for x in ds.values_wdl.reshape(-1).tolist()]
    finally:
        os.environ.pop("MOSAIC_BOOTSTRAP_COHERENCE", None)
        if prev is not None:
            os.environ["MOSAIC_BOOTSTRAP_COHERENCE"] = prev


def keys_for(mode, name):
    """(per-Datei-Schluessel, Fenster-Schluessel) unter Modus `mode`."""
    prev = os.environ.pop("MOSAIC_BOOTSTRAP_COHERENCE", None)
    try:
        if mode is not None:
            os.environ["MOSAIC_BOOTSTRAP_COHERENCE"] = mode
        import neural_net
        import corpus_dataset
        k_file = neural_net.per_file_cache_key(
            name, value_target_variant="default", encoder="flat",
            conjunction_head=False, bootstrap_native=True)
        k_win = corpus_dataset.window_cache_key(
            data_dir="data", files=[name], value_target_variant="default",
            encoder="flat", conjunction_head=False).key
        return k_file, k_win
    finally:
        os.environ.pop("MOSAIC_BOOTSTRAP_COHERENCE", None)
        if prev is not None:
            os.environ["MOSAIC_BOOTSTRAP_COHERENCE"] = prev


def compare(label, got, want, findings, failures):
    """Ist gegen unabhaengige Nachrechnung, nur ueber Records mit hartem Ausgang."""
    checked, worst, worst_at = 0, 0.0, None
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
    print(f"  {'OK  ' if ok else 'ROT '} {label:38s} n={checked:5d}  max|delta|={worst:.3e}",
          flush=True)
    if not ok:
        failures.append(label)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--file", default=None,
                    help="Korpusdatei (Default: die erste data/selfplay_hv2_*.pkl).")
    args = ap.parse_args()
    t_wall, t_cpu = time.time(), time.process_time()

    import neural_net
    from corpus_io import load_records

    if PROBE_NAME.startswith(neural_net.LEGACY_STRETCHED_PREFIXES):
        print(f"ROT -- {PROBE_NAME} faellt unter LEGACY_STRETCHED_PREFIXES; dieser "
              "Test will den NATIV-Fall pruefen.", file=sys.stderr)
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
    print(f"TD_LAMBDA={neural_net.TD_LAMBDA}", flush=True)

    records = load_records(src)
    want_off, pair_sums = expected_wdl_targets(records, neural_net.TD_LAMBDA,
                                               destretch=False, sum1=False)
    want_sum1, _ = expected_wdl_targets(records, neural_net.TD_LAMBDA,
                                        destretch=False, sum1=True)

    findings = {"prereg": PREREG, "quelle": os.path.basename(src),
                "td_lambda": neural_net.TD_LAMBDA, "records": len(records)}
    failures = []

    with tempfile.TemporaryDirectory(prefix="bscoh_") as tmp:
        got_unset = build_targets(tmp, src, PROBE_NAME, None)
        got_off = build_targets(tmp, src, PROBE_NAME, "off")
        got_sum1 = build_targets(tmp, src, PROBE_NAME, "sum1")

    compare("A off = Bestands-Blend", got_off, want_off, findings, failures)
    compare("A' ungesetzt = off", got_unset, want_off, findings, failures)
    compare("B sum1 = normierter Blend", got_sum1, want_sum1, findings, failures)

    # --- C) Gegenprobe: der Knopf muss auf echten Records etwas bewegen
    n = min(len(got_off), len(got_sum1))
    spread = max((abs(got_off[i] - got_sum1[i]) for i in range(n)), default=0.0)
    differs = spread > TOLERANCE
    findings["C off != sum1"] = {"groesste_differenz": spread, "ok": differs}
    print(f"  {'OK  ' if differs else 'ROT '} {'C off != sum1':38s} n={n:5d}  "
          f"max|delta|={spread:.3e}", flush=True)
    if not differs:
        failures.append("C off != sum1")

    # --- D) Cache-Schluessel trennen die Zieldefinition
    kf_unset, kw_unset = keys_for(None, PROBE_NAME)
    kf_off, kw_off = keys_for("off", PROBE_NAME)
    kf_sum1, kw_sum1 = keys_for("sum1", PROBE_NAME)
    key_ok = (kf_off != kf_sum1 and kw_off != kw_sum1
              and kf_off == kf_unset and kw_off == kw_unset)
    findings["D cache-key"] = {"datei_off": kf_off, "datei_sum1": kf_sum1,
                               "fenster_off": kw_off, "fenster_sum1": kw_sum1,
                               "datei_ungesetzt": kf_unset, "fenster_ungesetzt": kw_unset,
                               "ok": key_ok}
    print(f"  {'OK  ' if key_ok else 'ROT '} {'D Schluessel trennen, off==ungesetzt':38s} "
          f"{kf_off}/{kf_sum1}", flush=True)
    if not key_ok:
        failures.append("D cache-key")

    # --- E) Berichtsgroessen (kein Tor)
    deltas = [abs(got_off[i] - got_sum1[i]) for i in range(n)]
    signed = [got_sum1[i] - got_off[i] for i in range(n)]
    findings["E berichtsgroessen"] = {
        "paarsumme_mittel": (sum(pair_sums) / len(pair_sums)) if pair_sums else None,
        "paarsumme_n": len(pair_sums),
        "ziel_delta_abs_mittel": (sum(deltas) / len(deltas)) if deltas else None,
        "ziel_delta_signiert_mittel": (sum(signed) / len(signed)) if signed else None,
        "ziel_delta_max": spread,
    }
    e = findings["E berichtsgroessen"]
    if e["paarsumme_mittel"] is not None:
        print(f"  --   Paarsumme im Mittel {e['paarsumme_mittel']:.4f} "
              f"(n={e['paarsumme_n']}), Ziel-Verschiebung "
              f"{e['ziel_delta_signiert_mittel']:+.4f} im Mittel, "
              f"|max| {spread:.4f}", flush=True)

    findings["verdikt"] = "GRUEN" if not failures else "ROT"
    findings["versagt"] = failures
    findings["laufzeit"] = {"wanduhr_s": round(time.time() - t_wall, 2),
                            "cpu_s": round(time.process_time() - t_cpu, 2),
                            "threads": 1,
                            "s_je_record": round((time.time() - t_wall) / max(1, len(records)), 6)}
    target = _ROOT / "evaluations" / "artifacts" / "bootstrap_coherence_probe.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(findings, indent=2, ensure_ascii=False),
                      encoding="utf-8", newline="\n")
    print(f"\nArtefakt: {target}")

    if failures:
        print(f"\nROT -- {', '.join(failures)}", file=sys.stderr)
        return 1
    print("\nGRUEN -- Arm K wirkt genau im aktiven Modus, Bestand bleibt unberuehrt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
