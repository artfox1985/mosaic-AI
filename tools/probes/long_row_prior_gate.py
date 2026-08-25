#!/usr/bin/env python
"""PREREG_long_row_payoff.md par.2, Zweig A: Prior-Sichtbarkeit.

Frage: schlaegt der ROHE Policy-Prior (vor jeder Suche) eine Fortsetzung
der langen Musterreihen 5/6 ueberhaupt vor, wenn sie objektiv erreichbar
ist -- oder ist die Unterdrueckung schon im gelernten Prior, bevor Suche
oder Value-Kopf eingreifen?

Zwei Messungen je qualifizierender Stellung (par.2, Punkt "Zwei
Messungen"):
  1. Roher Prior auf der langen-Reihe-Fortsetzung (Zeilen 5/6, 0-indexiert
     4/5) relativ zur Masse auf allen legalen kurzen-Reihe-Alternativen
     (Zeilen 1-3, 0-indexiert 0-2) -- normiert auf die legale Maske.
  2. Besuchsverteilung NACH der Suche an derselben Wurzel, dieselben
     Mengen -- trennt "der Prior schlaegt es vor, die Suche verwirft es"
     von "der Prior schlaegt es nie vor".

Qualifizierende Stellung (par.2 "Zustandsauswahl"): Reihe 5 ODER 6 traegt
bereits >= 2 Steine (Fortsetzung ist noch "billig"/erreichbar) UND unter
den legalen Aktionen existiert mindestens eine, die genau DIESE Reihe
weiterfuellt.

Instrument identisch zu floor_action_aversion_gate.py (selbes
`action_to_id`, selber Selbsttest, selber Modell-Ladepfad, selber
net_search_state_json-Wrapper) -- bewusst dupliziert statt importiert,
gleiche Begruendung wie dort (unabhaengige Testbarkeit je Sonde).

Referenzpunkt (par.2 "Referenzpunkt"): dieselbe Messung zusaetzlich auf dem
Heuristik-Self-Play-Korpus (`data/holdout`, der Abstammungs-Lehrer, der die
Spaetrunden-Umkehr bereits zeigt) -- als KONTRAST, kein Erfolgskriterium
fuer sich (par.2 woertlich).
"""
import glob
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch

ENGINE_PY = Path(__file__).resolve().parents[2] / "engine" / "py"
sys.path.insert(0, str(ENGINE_PY))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import mosaic_rust as m  # noqa: E402
from neural_net import (  # noqa: E402
    state_to_tensor, state_to_planes, action_to_id as ref_action_to_id,
    build_model_from_checkpoint,
)
from config import INPUT_SIZE, NUM_ACTIONS  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
EVAL = ROOT / "evaluations"
OUT_JSON = EVAL / "artifacts" / "long_row_prior_gate.json"

MODEL_ONNX = str(ROOT / "models" / "alphazero_v21_2d_brierbest.onnx")
MODEL_PTH = ROOT / "models" / "alphazero_v21_2d_brierbest.pth"
SIMS = 200
C_PUCT = 1.5

LONG_ROWS = {4, 5}    # 0-indexiert = Musterreihe 5/6
SHORT_ROWS = {0, 1, 2}  # 0-indexiert = Musterreihe 1/2/3
MIN_FILL_LONG_ROW = 2

COLOR_MAP = {"blau": 0, "gelb": 1, "rot": 2, "schwarz": 3, "türkis": 4, None: -1, "special": 5}


def action_to_id(action):
    t = action.get("type", "")
    if t == "pass":
        return 0
    if t == "end_tiling":
        return 1
    if t == "stone":
        c_id = max(0, COLOR_MAP.get(action.get("color"), 0))
        r_id = action.get("row", 0) + 1
        f_idx = action.get("factory_index", 0)
        return min(10 + (c_id * 48) + (r_id * 6) + f_idx, 273)
    if t == "tiling":
        return 274 + (action.get("pattern_row", 0) * 9) + (action.get("slot_row", 0) * 3) + action.get("slot_col", 0)
    if t == "choose_dome_slot":
        return 328 + (action.get("display_index", 0) * 9) + (action.get("slot_row", 0) * 3) + action.get("slot_col", 0)
    if t == "choose_draw_stack_slot":
        p_idx = min(action.get("pending_index", 0), 4 - 1)
        return 355 + (p_idx * 9) + (action.get("slot_row", 0) * 3) + action.get("slot_col", 0)
    if t == "choose_dome_rotation":
        rot_idx = max(0, min(3, action.get("rotation", 0) // 90))
        return 391 + rot_idx
    if t == "use_chips":
        return 395 + action.get("pattern_row", 0)
    if t == "bonus_chip":
        return 401 + action.get("factory_index", 0)
    if t == "dome_stack_peek":
        return 405
    return 405


def selftest_local_vs_reference():
    for a in [
        {"type": "stone", "color": "rot", "row": 4, "factory_index": 4},
        {"type": "stone", "color": "blau", "row": 0, "factory_index": 0},
        {"type": "choose_dome_slot", "display_index": 1, "slot_row": 0, "slot_col": 2},
    ]:
        mine, ref = action_to_id(a), ref_action_to_id(a)
        assert mine == ref, f"Selbsttest (lokal vs. Referenz) FEHLGESCHLAGEN: {a} -> {mine} != {ref}"
    print("Selbsttest (lokal vs. neural_net.action_to_id): bestanden.", file=sys.stderr)


def selftest_vs_engine(state_json_str, all_ids):
    """Siehe floor_action_aversion_gate.py fuer die Begruendung: engine-
    seitige `action_id` in `net_search_state_json`s `moves` ist ein
    LOKALER Index, kein globaler -- deshalb Match ueber den Aktionsinhalt,
    Pruefung nur "ist jeder Suchkandidat legal"."""
    out = m.net_search_state_json(state_json_str, MODEL_ONNX, 40, C_PUCT, 999)
    d = json.loads(out) if isinstance(out, str) else out
    checked = 0
    for mv in d.get("moves", []):
        mine = action_to_id(mv["action"])
        assert mine in all_ids, (
            f"Selbsttest (Suchkandidat legal?) FEHLGESCHLAGEN: {mv['action']} -> id {mine}")
        checked += 1
    print(f"Selbsttest (jeder Suchkandidat liegt in der legalen Maske): "
          f"{checked} Aktionen, bestanden.", file=sys.stderr)


def rebuild_model():
    ckpt = torch.load(str(MODEL_PTH), map_location="cpu")
    model, encoder = build_model_from_checkpoint(ckpt, input_size=INPUT_SIZE, num_actions=NUM_ACTIONS)
    model.eval()
    return model, encoder


def raw_prior_logits_batch(model, encoder, states):
    with torch.no_grad():
        if encoder == "2d":
            planes = torch.stack([state_to_planes(s) for s in states])
            flats = torch.stack([state_to_tensor(s) for s in states])
            out = model(planes, flats)
        else:
            flats = torch.stack([state_to_tensor(s) for s in states])
            out = model(flats)
        logits = out[0]
    return logits.numpy()


def masked_softmax(logits, legal_ids):
    mask = np.zeros_like(logits)
    for i in legal_ids:
        mask[i] = 1.0
    masked = logits + (mask - 1.0) * 1e9
    e = np.exp(masked - masked.max())
    e = e * mask
    s = e.sum()
    return e / s if s > 0 else np.zeros_like(logits)


def classify_actions(state, valid_actions):
    """(alle_legalen_ids, lang_ids, kurz_ids) fuer die ziehende Seite."""
    pi = state["current_player"]
    pls = state["players"][pi]["pattern_lines"]
    fill = {row["index"]: len(row["tiles"]) for row in pls}

    all_ids, long_ids, short_ids = set(), set(), set()
    qualifies = False
    for a in valid_actions:
        aid = action_to_id(a)
        all_ids.add(aid)
        if a.get("type") != "stone":
            continue
        row = a.get("row")
        if row in LONG_ROWS:
            long_ids.add(aid)
            if fill.get(row, 0) >= MIN_FILL_LONG_ROW:
                qualifies = True
        elif row in SHORT_ROWS:
            short_ids.add(aid)
    return all_ids, long_ids, short_ids, qualifies


def stratified_sample(files, stride):
    groups = defaultdict(list)
    for f in files:
        mm = re.search(r"selfplay_([a-zA-Z0-9]+)_", Path(f).name)
        groups[mm.group(1) if mm else "?"].append(f)
    out = []
    for gen in sorted(groups):
        out.extend(sorted(groups[gen])[::stride])
    return sorted(out)


def collect_qualifying(files, cap_total, cap_per_file):
    import pickle
    found = []
    for f in files:
        if len(found) >= cap_total:
            break
        with open(f, "rb") as fh:
            recs = pickle.load(fh)
        n_this_file = 0
        for r in recs:
            if n_this_file >= cap_per_file or len(found) >= cap_total:
                break
            st = r.get("state") or {}
            if st.get("phase") != "drafting":
                continue
            # Runde 5 ausgeschlossen: par.1 der Prereg fokussiert R1-3 ("wo
            # die Reihe ueberhaupt noch offen ist"), UND net_search_state_json
            # faellt in Runde 5 auf einen alpha-beta-Loeser-Pfad zurueck
            # (andere Rueckgabe-Schema, kein "action"/"net_prob" je Move --
            # beim Testen entdeckt, siehe Modulkopf-Historie im Commit).
            if st.get("round") == 5:
                continue
            va = r.get("valid_actions") or []
            all_ids, long_ids, short_ids, qualifies = classify_actions(st, va)
            if qualifies and long_ids and short_ids:
                found.append(dict(state=st, all_ids=all_ids, long_ids=long_ids,
                                  short_ids=short_ids, round=st.get("round"), file=f))
                n_this_file += 1
    return found


def evaluate(found, model, encoder, label):
    if not found:
        return dict(n=0, label=label), []
    states = [q["state"] for q in found]
    logits = raw_prior_logits_batch(model, encoder, states)

    rows = []
    for i, q in enumerate(found):
        prior = masked_softmax(logits[i], q["all_ids"])
        prior_long = float(sum(prior[j] for j in q["long_ids"]))
        prior_short = float(sum(prior[j] for j in q["short_ids"]))

        out = m.net_search_state_json(json.dumps(q["state"]), MODEL_ONNX, SIMS, C_PUCT, 20260824 + i)
        d = json.loads(out) if isinstance(out, str) else out
        moves_raw = d.get("moves", [])
        # Defensiv: Eintraege ohne "action" (z.B. Alpha-Beta-Loeser-Schema
        # bei Rueckfall auf einen anderen Suchpfad) haben kein globales
        # action_to_id-Gegenstueck und zaehlen nicht mit -- sollte nach dem
        # Runde-5-Ausschluss oben nicht mehr vorkommen, hier nur als
        # zweite Sicherung.
        moves = [mv for mv in moves_raw if "action" in mv]
        if len(moves) != len(moves_raw):
            print(f"  WARNUNG: {len(moves_raw)-len(moves)} Move-Eintraege ohne "
                 f"'action' verworfen (Zustand round={q['round']})", file=sys.stderr)
        for mv in moves:
            mv["_global_id"] = action_to_id(mv["action"])
        total_visits = sum(mv.get("mcts_visits", 0) for mv in moves) or 1
        visits_long = sum(mv.get("mcts_visits", 0) for mv in moves if mv["_global_id"] in q["long_ids"])
        visits_short = sum(mv.get("mcts_visits", 0) for mv in moves if mv["_global_id"] in q["short_ids"])

        rows.append(dict(
            round=q["round"], prior_long=round(prior_long, 5), prior_short=round(prior_short, 5),
            search_long_share=round(visits_long / total_visits, 5),
            search_short_share=round(visits_short / total_visits, 5),
            n_moves_returned=len(moves), total_visits=total_visits,
        ))

    return summarize_rows(rows, label)


def summarize_rows(rows, label):
    """Reine Aggregation aus bereits berechneten Zeilen -- KEIN erneuter
    Modell-/Suchaufruf. Wiederverwendet fuer 'gesamt' und je Runde, damit
    keine Stellung zweimal durch net_search_state_json laeuft (das war ein
    Effizienzfehler im ersten Entwurf: die Runden-Aufschluesselung rief
    evaluate() erneut auf denselben Stellungen auf und verdoppelte die
    Laufzeit ohne neue Information)."""
    if not rows:
        return dict(n=0, label=label), rows
    pl = np.array([r["prior_long"] for r in rows])
    ps = np.array([r["prior_short"] for r in rows])
    sl = np.array([r["search_long_share"] for r in rows])
    ss = np.array([r["search_short_share"] for r in rows])
    summary = dict(
        n=len(rows), label=label,
        prior_long_mean=round(float(pl.mean()), 5), prior_short_mean=round(float(ps.mean()), 5),
        prior_ratio_lang_zu_kurz=round(float(pl.mean() / ps.mean()), 4) if ps.mean() > 0 else None,
        search_long_share_mean=round(float(sl.mean()), 5), search_short_share_mean=round(float(ss.mean()), 5),
        search_ratio_lang_zu_kurz=round(float(sl.mean() / ss.mean()), 4) if ss.mean() > 0 else None,
        delta_prior_zu_suche_long=round(float(sl.mean() - pl.mean()), 5),
        delta_prior_zu_suche_short=round(float(ss.mean() - ps.mean()), 5),
    )
    return summary, rows


def main():
    selftest_local_vs_reference()
    stride = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    cap_total = int(sys.argv[2]) if len(sys.argv) > 2 else 250
    cap_per_file = int(sys.argv[3]) if len(sys.argv) > 3 else 25

    all_files = sorted(glob.glob(str(ROOT / "data" / "selfplay_*.pkl")))
    net_files = stratified_sample(all_files, stride)
    print(f"Netz-Korpus: {len(all_files)} gesamt, Stichprobe {len(net_files)}", file=sys.stderr)
    net_found = collect_qualifying(net_files, cap_total, cap_per_file)
    print(f"Netz: {len(net_found)} qualifizierende Stellungen.", file=sys.stderr)

    heur_files = sorted(glob.glob(str(ROOT / "data" / "holdout" / "selfplay_hold_heur_*.pkl")))
    heur_found = collect_qualifying(heur_files, cap_total, cap_per_file) if heur_files else []
    print(f"Heuristik: {len(heur_found)} qualifizierende Stellungen "
          f"(aus {len(heur_files)} Dateien).", file=sys.stderr)

    if not net_found:
        print("Keine qualifizierenden Netz-Stellungen -- Tor nicht auswertbar.", file=sys.stderr)
        sys.exit(1)

    selftest_vs_engine(json.dumps(net_found[0]["state"]), net_found[0]["all_ids"])

    model, encoder = rebuild_model()
    print(f"Rohe Priors + Suche: {len(net_found)} Netz-Stellungen ...", file=sys.stderr)
    net_summary, net_rows = evaluate(net_found, model, encoder, "netz")
    heur_summary, heur_rows = evaluate(heur_found, model, encoder, "heuristik") if heur_found else (dict(n=0), [])

    je_runde = {}
    for rnd in sorted(set(r["round"] for r in net_rows if r["round"] is not None)):
        sel_rows = [r for r in net_rows if r["round"] == rnd]
        s, _ = summarize_rows(sel_rows, f"netz_runde_{rnd}")
        je_runde[str(rnd)] = s

    pl, ps = net_summary.get("prior_long_mean", 0), net_summary.get("prior_short_mean", 0)
    sl, ss = net_summary.get("search_long_share_mean", 0), net_summary.get("search_short_share_mean", 0)
    if net_summary["n"] == 0:
        lesart = "KEIN_DATENSATZ"
    elif pl < ps and abs(sl - pl) < 0.03 and abs(ss - ps) < 0.03:
        lesart = "Signal fehlt bereits im Prior -> Zweig B2 (Label/Training) ruecken vor"
    elif pl < ps and sl < ss:
        lesart = "Prior hoch relativ, Suche unterdrueckt zusaetzlich -> Zweig B1 (Suchseitiges Shaping)"
    else:
        lesart = "UNKLAR -- Rohdaten pruefen, keine der beiden vorregistrierten Lesarten trifft glatt"

    result = dict(netz=net_summary, heuristik=heur_summary, je_runde=je_runde,
                 lesart=lesart, sims=SIMS, c_puct=C_PUCT, model=MODEL_ONNX,
                 net_rows=net_rows, heur_rows=heur_rows)
    OUT_JSON.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k not in ("net_rows", "heur_rows")},
                     indent=2, ensure_ascii=False))
    print(f"\n-> {OUT_JSON}")


if __name__ == "__main__":
    main()
