"""
tools/value_rank_metric.py -- Task #29: Value-Rangmetrik gegen das Orakel
(`value_kendall_tau_vs_oracle_q`) + Vorbereitung der historischen Validierung.

Design/Begruendung: siehe `evaluations/PREREG_value_rank_metric.md` (VOR der
ersten Berechnung geschrieben, danach nicht mehr geaendert). Kurzfassung:

Fuer jeden orakel-gelabelten frozen-Zustand (`frozen_v1_oracle_labels_v18.json`,
`tools/oracle_metrics.py`) werden die vom Orakel betrachteten Wurzelkandidaten
genommen und mit dem VALUE-KOPF des zu pruefenden Netzes auf dem jeweiligen
AFTERSTATE bewertet -- nicht ueber eine separate Zustandsrekonstruktion,
sondern ueber `mosaic_rust.net_search_state_json_trace(...)`s `moves[i].
net_leaf_value`-Feld: der Netz-Rohwert JEDES Wurzelkindes wird bei dessen
Expansion berechnet (`net_mcts.rs::make_node`) und unveraendert ausgegeben,
UNABHAENGIG vom Sim-Budget -- exakt der Wert, den die eigene Suche an ihren
Blaettern sieht (dieselbe Skala/Perspektive wie `mcts_q`: `[0,1]`-Sieg-
Wahrscheinlichkeit aus Sicht des ziehenden Spielers). Kendall-Tau (tau-a,
`oracle_metrics.py::_kendall_tau_a`) zwischen dieser Rangfolge und der
Orakel-Q-Ordnung (`mcts_q`), gemittelt ueber alle Zustaende -- exaktes
Analogon zu `kendall_tau_policy_vs_oracle_q`, nur auf der Value- statt der
Policy-Seite.

Funktioniert fuer JEDEN Checkpoint mit vorhandener `.onnx`-Datei (auch alte
Generationen) -- `Net::load_auto` (engine/src/net.rs) laedt ausschliesslich
ueber `tract_onnx`, ein `.pth`-Pfad existiert fuer diesen Suchweg ohnehin
nicht.

Verwendung:
    python tools/value_rank_metric.py --smoke
    python tools/value_rank_metric.py --models v19_best v18_best --out evaluations/value_rank_metric_v19_vs_v18.json
    python tools/value_rank_metric.py --validate

`--validate`: laeuft automatisch ueber alle ENTSCHIEDENEN historischen
Gating-Paare (McNemar p<0.05, `tools/offline_vs_arena.py::load_gatings`),
deren BEIDE Modelle noch eine `.onnx`-Datei besitzen -- identische Prozedur/
Erfolgskriterium wie bei den Orakel-Metriken (siehe PREREG). NICHT Teil des
`--smoke`-Auftrags (kostet je nach Anzahl entschiedener Paare Minuten bis
zweistellige Minuten, siehe PREREG-Laufzeitmessung) -- vom Koordinator
separat zu starten.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Windows-Konsolen (cp1252) -- gleiches Muster wie offline_diagnosis.py/train.py.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "engine" / "py"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import mosaic_rust  # noqa: E402
from config import MODELS_DIR  # noqa: E402
from neural_net import action_to_id  # noqa: E402

from oracle_metrics import (  # noqa: E402
    _kendall_tau_a,
    load_frozen_states,
    load_oracle,
)
from build_frozen_oracle_labels import state_seed  # noqa: E402

# Produktions-Standard (siehe PREREG, Abschnitt "Afterstate-Beschaffung"):
# `gumbel_top_m_for_budget(400) == 16 == GUMBEL_TOP_M`, dieselbe
# Kandidatenzahl-Obergrenze wie beim Bau der Orakel-Labels selbst (5000 Sims,
# ebenfalls auf 16 geclampt). Kleinere Sim-Budgets wurden empirisch
# (PREREG) getestet und liefern messbar schlechtere Ueberlappung.
DEFAULT_SIMS = 400
DEFAULT_C_PUCT = 1.5
MIN_CANDIDATES_FOR_TAU = 3  # identische Schwelle wie oracle_metrics.py

OUT_DEFAULT = ROOT / "evaluations" / "artifacts" / "value_rank_metric.json"


def usable_oracle_labels(labels: list[dict]) -> list[dict]:
    """Runde 1-4, mit Root-Value, mind. ein echter (nicht-Null) Wurzelkandidat --
    identischer Filter wie `oracle_metrics.py::add_oracle_metrics`/
    `compute_for_model` (Runde 5 = exakte Alpha-Beta-Suche, siehe dortige
    Kommentare)."""
    return [
        l for l in labels
        if l["round"] < 5 and l.get("root_value") is not None
        and l["moves"] and l["moves"][0].get("action") is not None
    ]


def compute_for_model(
    model_name: str,
    oracle_labels: list[dict],
    states_by_idx: dict[int, dict],
    sims: int = DEFAULT_SIMS,
    c_puct: float = DEFAULT_C_PUCT,
) -> list[dict]:
    """Ein `net_search_state_json_trace`-Aufruf je Zustand -- liest
    `moves[i].net_leaf_value` (Netz-Rohwert des Wurzelkindes, siehe Moduldoku)
    aus, matcht per `action_to_id` gegen die vom Orakel betrachteten
    Kandidaten, bildet Kendall-Tau NUR ueber die tatsaechliche Schnittmenge.
    Ueberlappung wird je Zustand mitprotokolliert (PREREG: Transparenz statt
    stillem Datenverlust bei abweichenden Root-Kandidatenmengen)."""
    model_path = MODELS_DIR / f"alphazero_{model_name}.onnx"
    if not model_path.exists():
        raise SystemExit(f"Modell nicht gefunden: {model_path}")

    print(f"  Netz {model_name} ({len(oracle_labels)} Zustaende, sims={sims}) ...", flush=True)
    per_state = []
    for i, lbl in enumerate(oracle_labels):
        rec = states_by_idx[lbl["record_index"]]
        state = rec["state"]
        oracle_moves = lbl["moves"]
        oracle_ids = [action_to_id(m["action"]) for m in oracle_moves]
        oracle_q_by_id = {aid: float(m["mcts_q"]) for aid, m in zip(oracle_ids, oracle_moves)}
        n_oracle = len(set(oracle_ids))

        seed = state_seed(state)
        out = json.loads(mosaic_rust.net_search_state_json_trace(
            json.dumps(state), str(model_path), sims, c_puct, seed))
        cand_moves = out.get("moves") or []
        cand_value_by_id = {
            action_to_id(m["action"]): float(m["net_leaf_value"])
            for m in cand_moves if m.get("action") is not None
        }

        overlap_ids = sorted(set(oracle_q_by_id) & set(cand_value_by_id))
        n_overlap = len(overlap_ids)
        tau = None
        if n_overlap >= MIN_CANDIDATES_FOR_TAU:
            cand_vals = [cand_value_by_id[aid] for aid in overlap_ids]
            oracle_vals = [oracle_q_by_id[aid] for aid in overlap_ids]
            tau = _kendall_tau_a(cand_vals, oracle_vals)

        per_state.append({
            "record_index": lbl["record_index"],
            "round": lbl["round"],
            "n_oracle_candidates": n_oracle,
            "n_search_candidates": len(cand_value_by_id),
            "n_overlap": n_overlap,
            "overlap_frac_of_oracle": (n_overlap / n_oracle) if n_oracle > 0 else None,
            "tau": tau,
        })
        if (i + 1) % 100 == 0:
            print(f"    {i + 1}/{len(oracle_labels)}", flush=True)
    return per_state


def aggregate(per_state: list[dict], rounds=range(1, 6)) -> dict:
    """Analog `oracle_metrics.py::aggregate` -- overall + je Runde."""
    def block(rows: list[dict]) -> dict:
        n = len(rows)
        if n == 0:
            return {"n": 0}
        taus = [r["tau"] for r in rows if r["tau"] is not None]
        overlap_fracs = [r["overlap_frac_of_oracle"] for r in rows
                          if r["overlap_frac_of_oracle"] is not None]
        return {
            "n": n,
            "n_tau_states": len(taus),
            "n_skipped_below_min_candidates": n - len(taus),
            "value_kendall_tau_vs_oracle_q": float(np.mean(taus)) if taus else None,
            "tau_std": float(np.std(taus)) if taus else None,
            "mean_overlap_frac_of_oracle": float(np.mean(overlap_fracs)) if overlap_fracs else None,
            "min_overlap_frac_of_oracle": float(np.min(overlap_fracs)) if overlap_fracs else None,
        }

    result = {"overall": block(per_state)}
    result["by_round"] = {str(r): block([x for x in per_state if x["round"] == r]) for r in rounds}
    return result


def run_models(model_names: list[str], n_states: int | None, sims: int, c_puct: float) -> dict:
    print("Lade Orakel-Labels ...")
    manifest, labels = load_oracle()
    usable = usable_oracle_labels(labels)
    if n_states is not None:
        usable = usable[:n_states]
    print(f"  {len(usable)} auswertbare Zustaende (von {len(labels)} gelabelten, "
          f"Runde 1-4, >= {MIN_CANDIDATES_FOR_TAU} Orakel-Kandidaten noetig fuer Tau)")
    states_by_idx = load_frozen_states([l["record_index"] for l in usable])

    per_model = {}
    aggregates = {}
    for name in model_names:
        per_state = compute_for_model(name, usable, states_by_idx, sims=sims, c_puct=c_puct)
        agg = aggregate(per_state)
        per_model[name] = per_state
        aggregates[name] = agg
        ov = agg["overall"]
        tau_str = f"{ov['value_kendall_tau_vs_oracle_q']:+.4f}" if ov.get("value_kendall_tau_vs_oracle_q") is not None else "n/a"
        print(f"    {name}: tau={tau_str}  n_tau_states={ov['n_tau_states']}/{ov['n']}  "
              f"mean_overlap={ov['mean_overlap_frac_of_oracle']:.3f}" if ov.get("mean_overlap_frac_of_oracle") is not None
              else f"    {name}: tau={tau_str}")

    return {
        "oracle_manifest": manifest,
        "sims": sims,
        "c_puct": c_puct,
        "n_states": len(usable),
        "models": model_names,
        "aggregates": aggregates,
        "per_model_states": per_model,
    }


def run_smoke(models: list[str], n_states: int, sims: int, c_puct: float) -> dict:
    print(f"\n=== SMOKE: {models} auf {n_states} Orakel-Zustaenden (sims={sims}) ===")
    result = run_models(models, n_states, sims, c_puct)

    print("\n--- Plausibilitaetspruefungen ---")
    ok = True
    for name in models:
        ov = result["aggregates"][name]["overall"]
        tau = ov.get("value_kendall_tau_vs_oracle_q")
        if tau is None:
            print(f"  [FEHLER] {name}: keine Tau-Werte berechenbar (n_tau_states=0)")
            ok = False
            continue
        in_range = -1.0 <= tau <= 1.0
        std = ov.get("tau_std") or 0.0
        degenerate = std < 1e-9
        print(f"  {name}: tau={tau:+.4f}  in [-1,1]={in_range}  std={std:.4f}  "
              f"degeneriert={degenerate}  n_tau_states={ov['n_tau_states']}")
        ok = ok and in_range and not degenerate

    if len(models) == 2:
        a, b = models
        ta = result["aggregates"][a]["overall"].get("value_kendall_tau_vs_oracle_q")
        tb = result["aggregates"][b]["overall"].get("value_kendall_tau_vs_oracle_q")
        if ta is not None and tb is not None:
            print(f"\n  {a} vs {b}: tau_a={ta:+.4f} tau_b={tb:+.4f}  "
                  f"{a} > {b}: {ta > tb} (erwartbar, wenn {a} der staerkere Champion ist -- "
                  f"KEIN Beweis, n={n_states} ist ein Rauchtest, keine Validierung)")

    print(f"\nRauchtest {'BESTANDEN' if ok else 'FEHLGESCHLAGEN'} (Plausibilitaet, keine Entscheidungsmetrik).")
    result["smoke_ok"] = ok
    return result


def run_validate(min_pairs: int, alpha_decisive: float, out_path: Path) -> None:
    """Volle historische Validierung -- identische Prozedur wie
    `offline_vs_arena.py` (Import, kein Nachbau), siehe PREREG Abschnitt
    "Validierungsregeln". NICHT Teil des `--smoke`-Auftrags -- Koordinator
    startet das separat (Laufzeit skaliert mit Anzahl entschiedener Paare ×
    ~950 Zustaenden × ~0.5s/Zustand)."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import offline_vs_arena as ova

    gatings = ova.load_gatings(min_pairs)

    def onnx_ok(name: str) -> bool:
        return (MODELS_DIR / f"alphazero_{name}.onnx").exists()

    usable_pairs = [g for g in gatings if onnx_ok(g["a"]) and onnx_ok(g["b"])]
    decisive_pairs = [g for g in usable_pairs
                       if g["mcnemar_p"] is not None and g["mcnemar_p"] < alpha_decisive]

    print(f"Gating-Paare gesamt: {len(gatings)} | mit beiden .onnx vorhanden: {len(usable_pairs)} "
          f"| davon ENTSCHIEDEN (McNemar p<{alpha_decisive}): {len(decisive_pairs)}")
    for g in decisive_pairs:
        print(f"  {g['a']} vs {g['b']}: pairs={g['pairs']} winrate_a={g['winrate_a']:.3f} "
              f"mcnemar_p={g['mcnemar_p']:.4f}")

    if not decisive_pairs:
        raise SystemExit("Keine entschiedenen, auswertbaren Paare gefunden.")

    model_names = sorted({n for g in decisive_pairs for n in (g["a"], g["b"])})
    print(f"\nBenoetigte Modelle: {model_names}")
    metrics_result = run_models(model_names, None, DEFAULT_SIMS, DEFAULT_C_PUCT)
    tau_by_model = {
        n: metrics_result["aggregates"][n]["overall"].get("value_kendall_tau_vs_oracle_q")
        for n in model_names
    }

    # Sekundaervergleich: value_r2_rounds_1_4 aus vorhandenen Frozen-Diagnosen.
    offline_r2, _versions = ova.load_offline()
    r2_by_model = {n: offline_r2.get(n, {}).get("value_r2_rounds_1_4") for n in model_names}

    rows = []
    n_correct_tau = 0
    n_correct_r2 = 0
    n_eval_tau = 0
    n_eval_r2 = 0
    print("\n" + "=" * 90)
    print(f"{'A vs B':<44}{'Siegq.A':>9}{'Δtau':>12}{'richtig?':>10}{'Δvalue_r2_1_4':>16}{'richtig?':>10}")
    print("-" * 90)
    for g in decisive_pairs:
        a, b, wr = g["a"], g["b"], g["winrate_a"]
        ta, tb = tau_by_model.get(a), tau_by_model.get(b)
        ra, rb = r2_by_model.get(a), r2_by_model.get(b)
        d_tau = (ta - tb) if (ta is not None and tb is not None) else None
        d_r2 = (ra - rb) if (ra is not None and rb is not None) else None
        correct_tau = ((d_tau > 0) == (wr > 0.5)) if d_tau not in (None, 0) else None
        correct_r2 = ((d_r2 > 0) == (wr > 0.5)) if d_r2 not in (None, 0) else None
        if correct_tau is not None:
            n_eval_tau += 1
            n_correct_tau += int(correct_tau)
        if correct_r2 is not None:
            n_eval_r2 += 1
            n_correct_r2 += int(correct_r2)
        rows.append({
            "a": a, "b": b, "pairs": g["pairs"], "winrate_a": wr, "mcnemar_p": g["mcnemar_p"],
            "tau_a": ta, "tau_b": tb, "delta_tau": d_tau, "tau_correct": correct_tau,
            "value_r2_a": ra, "value_r2_b": rb, "delta_value_r2": d_r2, "r2_correct": correct_r2,
        })
        fmt = lambda v: f"{v:+.4f}" if isinstance(v, (int, float)) else "n/a"
        print(f"{a + ' vs ' + b:<44}{wr:>9.3f}{fmt(d_tau):>12}{str(correct_tau):>10}"
              f"{fmt(d_r2):>16}{str(correct_r2):>10}")
    print("=" * 90)

    p_tau = ova.binom_p_two_sided(n_correct_tau, n_eval_tau) if n_eval_tau else None
    p_r2 = ova.binom_p_two_sided(n_correct_r2, n_eval_r2) if n_eval_r2 else None
    print(f"\nvalue_kendall_tau_vs_oracle_q: {n_correct_tau}/{n_eval_tau} richtig, Binomial p={p_tau}")
    print(f"value_r2_rounds_1_4 (informativ): {n_correct_r2}/{n_eval_r2} richtig, Binomial p={p_r2}")

    # Erfolgskriterium (PREREG, VORAB festgelegt): alle Richtungen korrekt UND p<0.05.
    all_correct = n_eval_tau > 0 and n_correct_tau == n_eval_tau
    validated = all_correct and p_tau is not None and p_tau < 0.05
    min_n_for_significance = 6  # p(6/6) = 0.03125 < 0.05; p(4/4)=0.125, p(5/5)=0.0625
    print(f"\nVerdikt: {'VALIDIERT' if validated else 'NICHT VALIDIERT'} "
          f"({n_correct_tau}/{n_eval_tau} korrekt, p={p_tau})")
    if not validated and all_correct and n_eval_tau < min_n_for_significance:
        print(f"  Hinweis (PREREG-Vorbehalt): ALLE {n_eval_tau} Richtungen korrekt, aber n={n_eval_tau} "
              f"ist strukturell zu klein fuer p<0.05 (erst ab n={min_n_for_significance} erreichbar). "
              f"'NICHT VALIDIERT' liegt hier an der Stichprobengroesse, nicht an falschen Richtungen.")

    out = {
        "alpha_decisive": alpha_decisive,
        "n_gatings_total": len(gatings),
        "n_usable_pairs": len(usable_pairs),
        "n_decisive_pairs": len(decisive_pairs),
        "rows": rows,
        "value_kendall_tau_vs_oracle_q": {"n_correct": n_correct_tau, "n_evaluable": n_eval_tau, "binom_p": p_tau},
        "value_r2_rounds_1_4": {"n_correct": n_correct_r2, "n_evaluable": n_eval_r2, "binom_p": p_r2},
        "validated": validated,
        "min_n_for_significance": min_n_for_significance,
        "metrics_result": {
            "sims": metrics_result["sims"], "c_puct": metrics_result["c_puct"],
            "n_states": metrics_result["n_states"], "aggregates": metrics_result["aggregates"],
        },
    }
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nErgebnis: {out_path}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--models", nargs="+", default=None,
                    help="Checkpoint-Namen ohne 'alphazero_'-Praefix/'.onnx'-Endung, z.B. v18_best")
    p.add_argument("--out", type=str, default=None, help=f"Ziel-JSON (Standard: {OUT_DEFAULT})")
    p.add_argument("--sims", type=int, default=DEFAULT_SIMS,
                    help=f"Sim-Budget je Zustand+Modell (Standard {DEFAULT_SIMS} -- Produktions-Standard, "
                         "siehe PREREG fuer die empirische Begruendung, NICHT kleiner waehlen).")
    p.add_argument("--c-puct", type=float, default=DEFAULT_C_PUCT)
    p.add_argument("--n-states", type=int, default=None,
                    help="Nur die ersten N auswertbaren Orakel-Zustaende (Standard: alle). "
                         "--smoke setzt dies automatisch auf 30, falls nicht angegeben.")
    p.add_argument("--smoke", action="store_true",
                    help="Rauchtest: 2 Modelle, 30 Zustaende, reine Plausibilitaetspruefung "
                         "(Tau in [-1,1], nicht degeneriert, erwartbare Champion>Vorgaenger-Richtung). "
                         "KEINE Entscheidungsmetrik.")
    p.add_argument("--validate", action="store_true",
                    help="Volle historische Validierung ueber alle entschiedenen Gating-Paare mit "
                         "vorhandenen .onnx-Dateien (siehe PREREG) -- NICHT fuer den Smoke-Auftrag, "
                         "kostet je nach Modellzahl mehrere Minuten.")
    p.add_argument("--min-pairs", type=int, default=50, help="Wie offline_vs_arena.py --min-pairs.")
    p.add_argument("--alpha-decisive", type=float, default=0.05)
    args = p.parse_args()

    if args.validate:
        out_path = Path(args.out) if args.out else ROOT / "evaluations" / "artifacts" / "value_rank_metric_validation.json"
        run_validate(args.min_pairs, args.alpha_decisive, out_path)
        return

    if args.smoke:
        models = args.models or ["v18_best", "v17_best"]
        n_states = args.n_states if args.n_states is not None else 30
        result = run_smoke(models, n_states, args.sims, args.c_puct)
        out_path = Path(args.out) if args.out else ROOT / "evaluations" / "artifacts" / "value_rank_metric_smoke.json"
    else:
        if not args.models:
            raise SystemExit("--models erforderlich (ausser bei --smoke/--validate).")
        result = run_models(args.models, args.n_states, args.sims, args.c_puct)
        out_path = Path(args.out) if args.out else OUT_DEFAULT

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\nErgebnis gespeichert unter: {out_path}")


if __name__ == "__main__":
    main()
