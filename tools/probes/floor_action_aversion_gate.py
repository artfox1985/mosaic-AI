#!/usr/bin/env python
"""Tor fuer PREREG_floor_action_aversion.md par.6: Prior gegen Suche.

Zwei Groessen je qualifizierender Stellung:
  1. ROHER Policy-Prior (Forward-Pass ohne Suche, PyTorch-Checkpoint, exakt
     das Muster aus tools/oracle_metrics.py::load_model/masked_softmax) auf
     dem Strafleisten-Ausgang gegen die Summe der ueberlauferzeugenden
     Reihen-Ausgaenge, normiert auf die legale Maske.
  2. Besuchsverteilung NACH der Suche (mosaic_rust.net_search_state_json,
     echte Gumbel-Suche auf demselben Zustand+Modell), dieselben zwei
     Mengen -- 0, wenn eine Aktion nicht unter den Gumbel-Top-m-Kandidaten
     war (informativ: die Suche hat sie nie in Betracht gezogen).

Qualifizierende Stellung: mindestens eine legale Strafleisten-Aktion
(row=-1) UND mindestens eine legale Reihen-Aktion, die NACHWEISLICH
Ueberlauf erzeugt. "Nachweislich" ist bewusst KONSERVATIV gefasst (zwei
exakte, unzweideutige Kriterien statt einer geschaetzten Mond-Stapel-
Aufloesung) -- eine dokumentierte Einschraenkung, keine stille Annahme:

  (a) FARB-KONFLIKT: die Zielreihe traegt schon eine andere Farbe als die
      gezogene -- laut Regelwerk (engine_manual Z.108-113) gehen dann ALLE
      gezogenen Steine auf die Strafleiste. Braucht keine Zugzahl, gilt
      fuer JEDE Quelle (Sonne, Mond, Grossfabrik).
  (b) GROSSFABRIK-SONNE UEBER KAPAZITAET: `factory_index==4` ist laut
      `self_play.rs::factory_index` UNZWEIDEUTIG `TakeSource::LargeFactorySun`
      (der einzige Source-Typ, der auf 4 abbildet) -- die Zugzahl ist exakt
      `large_factory["sun"].count(color)`, kein Stapel, keine Mehrdeutigkeit.

  AUSGESCHLOSSEN: Zuege mit `factory_index` 0-3 (SmallFactorySun UND
  SmallFactoryMoon koennen laut derselben `factory_index`-Funktion auf
  denselben Index fallen, ohne Unterscheidungsfeld waere die Zugzahl fuer
  den Mond-Fall nur zu SCHAETZEN) und `factory_index==5` (globaler
  Mond-Zug). Diese zaehlen nur ueber Kriterium (a) mit.

Selbsttest: die hier portierte `action_to_id` wird gegen (a) die
importierte Referenzfunktion aus neural_net.py und (b) die vom Rust-Engine
selbst vergebenen `action_id`-Werte aus `net_search_state_json` geprueft,
bevor irgendeine Kennzahl gezaehlt wird (REGEL 0).
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
# Vorgabe-Artefakt (Bestandslauf 2026-08-24). Mit Runden-Filter oder Seed
# schreibt `main` in eine ABGELEITETE Datei, damit der registrierte Lauf
# nie ueberschrieben wird.
OUT_JSON = EVAL / "artifacts" / "floor_action_aversion_gate.json"

MODEL_ONNX = str(ROOT / "models" / "alphazero_v21_2d_brierbest.onnx")
MODEL_PTH = ROOT / "models" / "alphazero_v21_2d_brierbest.pth"
SIMS = 200
C_PUCT = 1.5

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
        {"type": "stone", "color": "rot", "row": -1, "factory_index": 4},
        {"type": "stone", "color": "blau", "row": 5, "factory_index": 0},
        {"type": "choose_dome_slot", "display_index": 1, "slot_row": 0, "slot_col": 2},
        {"type": "stone", "color": "türkis", "row": 2, "factory_index": 3},
    ]:
        mine, ref = action_to_id(a), ref_action_to_id(a)
        assert mine == ref, f"Selbsttest (lokal vs. Referenz) FEHLGESCHLAGEN: {a} -> {mine} != {ref}"
    print("Selbsttest (lokal vs. neural_net.action_to_id): bestanden.", file=sys.stderr)


def selftest_vs_engine(state_json_str, all_ids):
    """KORREKTUR waehrend des Baus: `mv["action_id"]` in
    `net_search_state_json`s `moves` ist ein LOKALER Index in die
    zurueckgegebene Kandidatenliste (0,1,2,... in Rueckgabereihenfolge),
    NICHT dieselbe globale ID-Achse wie `action_to_id()` -- ein erster
    Versuch, beide direkt zu vergleichen, ist prompt fehlgeschlagen
    (`choose_dome_slot` bekam engine-seitig 0, waehrend 0 in der globalen
    Achse "pass" bedeutet). Deshalb HIER matchen ueber den INHALT: jede von
    der Suche zurueckgegebene Aktion wird per `action_to_id()` neu kodiert
    und muss ein Mitglied der LEGALEN Maske dieser Stellung sein -- das ist
    die tatsaechlich pruefbare Eigenschaft (jeder Suchkandidat ist ein
    legaler Zug) und der Grund, warum der Haupt-Loop unten NIE
    `mv["action_id"]` direkt verwendet."""
    out = m.net_search_state_json(state_json_str, MODEL_ONNX, 40, C_PUCT, 999)
    d = json.loads(out) if isinstance(out, str) else out
    checked = 0
    for mv in d.get("moves", []):
        mine = action_to_id(mv["action"])
        assert mine in all_ids, (
            f"Selbsttest (Suchkandidat legal?) FEHLGESCHLAGEN: {mv['action']} -> "
            f"id {mine} ist NICHT in der legalen Maske dieser Stellung")
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


def pattern_capacity_and_fill(state, player_idx):
    pls = state["players"][player_idx]["pattern_lines"]
    cap, fill, color = {}, {}, {}
    for row in pls:
        i = row["index"]
        cap[i] = row["capacity"]
        fill[i] = len(row["tiles"])
        color[i] = row.get("color")
    return cap, fill, color


def classify_actions(state, valid_actions):
    """(alle_legalen_ids, floor_ids, overflow_row_ids) fuer die ziehende Seite."""
    pi = state["current_player"]
    cap, fill, color = pattern_capacity_and_fill(state, pi)
    lf_sun = (state.get("large_factory") or {}).get("sun") or []

    all_ids, floor_ids, overflow_ids = set(), set(), set()
    for a in valid_actions:
        aid = action_to_id(a)
        all_ids.add(aid)
        if a.get("type") != "stone":
            continue
        row = a.get("row")
        if row == -1:
            floor_ids.add(aid)
            continue
        if row is None or row not in cap:
            continue
        row_color = color.get(row)
        color_mismatch = row_color is not None and row_color != a.get("color")
        gf_sun_overflow = False
        if a.get("factory_index") == 4:
            take_n = lf_sun.count(a.get("color"))
            gf_sun_overflow = take_n > (cap[row] - fill[row])
        if color_mismatch or gf_sun_overflow:
            overflow_ids.add(aid)
    return all_ids, floor_ids, overflow_ids


def stratified_sample(files, stride):
    groups = defaultdict(list)
    for f in files:
        mm = re.search(r"selfplay_([a-zA-Z0-9]+)_", Path(f).name)
        groups[mm.group(1) if mm else "?"].append(f)
    out = []
    for gen in sorted(groups):
        out.extend(sorted(groups[gen])[::stride])
    return sorted(out)


def collect_qualifying(files, cap_total, cap_per_file=3, rounds=None, seed=None):
    """Qualifizierende Stellungen einsammeln.

    `rounds`: Menge zugelassener Runden (1-basiert, wie `state["round"]`);
        None = alle.
    `seed`: None ist das BESTANDSVERHALTEN des Laufs vom 2026-08-24 -- die
        ERSTEN `cap_per_file` qualifizierenden Datensaetze je Datei, in
        Datensatz-Reihenfolge. Genau das erzeugt einen stillen Rundenfilter:
        Datensaetze stehen in Zugreihenfolge, der Deckel je Datei fuellt sich
        also mit Fruehspiel-Stellungen. Der registrierte Lauf hatte deshalb
        268 von 280 Stellungen in Runde 1 (`floor_action_aversion_gate.json`,
        `je_runde`) -- eine Eigenschaft der SAMMLUNG, nicht des Spiels
        (Befund 2026-08-25). Ist `seed` gesetzt, werden je Datei ALLE
        qualifizierenden Datensaetze gesammelt und daraus mit diesem Seed
        gezogen; die Auswahl ist damit reproduzierbar und ordnungsfrei.
    """
    import pickle
    import random
    rng = random.Random(seed) if seed is not None else None
    found = []
    for f in files:
        if len(found) >= cap_total:
            break
        with open(f, "rb") as fh:
            recs = pickle.load(fh)
        cands = []
        for r in recs:
            # Ohne Seed identisch zum Bestand: Abbruch, sobald der Deckel je
            # Datei erreicht ist (dieselbe Auswahl, byte-identisch).
            if rng is None and len(cands) >= cap_per_file:
                break
            st = r.get("state") or {}
            if st.get("phase") != "drafting":
                continue
            if rounds is not None and st.get("round") not in rounds:
                continue
            va = r.get("valid_actions") or []
            all_ids, floor_ids, overflow_ids = classify_actions(st, va)
            if floor_ids and overflow_ids:
                cands.append(dict(state=st, all_ids=all_ids, floor_ids=floor_ids,
                                  overflow_ids=overflow_ids, round=st.get("round"),
                                  file=f))
        if rng is not None:
            rng.shuffle(cands)
        found.extend(cands[: min(cap_per_file, cap_total - len(found))])
    return found


def main():
    selftest_local_vs_reference()

    # argv: [stride] [cap_total] [runden] [seed]
    #   runden: "2,3,4" oder "alle" (Vorgabe)
    #   seed:   gesetzt -> ordnungsfreie Auswahl je Datei (siehe
    #           collect_qualifying); weggelassen -> Bestandsverhalten
    stride = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    cap_total = int(sys.argv[2]) if len(sys.argv) > 2 else 240
    rounds = None
    if len(sys.argv) > 3 and sys.argv[3] not in ("", "alle"):
        rounds = {int(x) for x in sys.argv[3].split(",")}
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else None

    suffix = ""
    if rounds is not None:
        suffix += "_r" + "".join(str(r) for r in sorted(rounds))
    if seed is not None:
        suffix += f"_s{seed}"
    out_json = OUT_JSON if not suffix else EVAL / "artifacts" / f"floor_action_aversion_gate{suffix}.json"

    all_files = sorted(glob.glob(str(ROOT / "data" / "selfplay_*.pkl")))
    files = stratified_sample(all_files, stride)
    print(f"Scanne {len(files)} von {len(all_files)} Dateien (Stichprobe) "
          f"nach qualifizierenden Stellungen "
          f"[runden={sorted(rounds) if rounds else 'alle'}, seed={seed}] ...",
          file=sys.stderr)
    found = collect_qualifying(files, cap_total, rounds=rounds, seed=seed)
    print(f"{len(found)} qualifizierende Stellungen gefunden.", file=sys.stderr)
    if not found:
        print("Keine qualifizierenden Stellungen -- Tor nicht auswertbar.", file=sys.stderr)
        sys.exit(1)

    # Engine-Selbsttest auf der ersten qualifizierenden Stellung, VOR jeder
    # gezaehlten Kennzahl.
    selftest_vs_engine(json.dumps(found[0]["state"]), found[0]["all_ids"])

    model, encoder = rebuild_model()
    states = [q["state"] for q in found]
    print(f"Rohe Priors: Forward-Pass Batch ({encoder}-Encoder) ...", file=sys.stderr)
    logits = raw_prior_logits_batch(model, encoder, states)

    rows = []
    for i, q in enumerate(found):
        prior = masked_softmax(logits[i], q["all_ids"])
        prior_floor = float(sum(prior[j] for j in q["floor_ids"]))
        prior_overflow = float(sum(prior[j] for j in q["overflow_ids"]))

        out = m.net_search_state_json(json.dumps(q["state"]), MODEL_ONNX, SIMS, C_PUCT, 20260824 + i)
        d = json.loads(out) if isinstance(out, str) else out
        moves = d.get("moves", [])
        # `mv["action_id"]` ist ein LOKALER Index in `moves`, NICHT dieselbe
        # Achse wie unser globales action_to_id() -- siehe selftest_vs_engine
        # -- deshalb hier ueber den Aktions-INHALT neu kodieren und matchen.
        for mv in moves:
            mv["_global_id"] = action_to_id(mv["action"])
        total_visits = sum(mv.get("mcts_visits", 0) for mv in moves) or 1
        visits_floor = sum(mv.get("mcts_visits", 0) for mv in moves
                           if mv["_global_id"] in q["floor_ids"])
        visits_overflow = sum(mv.get("mcts_visits", 0) for mv in moves
                              if mv["_global_id"] in q["overflow_ids"])
        share_floor = visits_floor / total_visits
        share_overflow = visits_overflow / total_visits

        rows.append(dict(
            round=q["round"], n_floor_ids=len(q["floor_ids"]),
            n_overflow_ids=len(q["overflow_ids"]), n_legal=len(q["all_ids"]),
            prior_floor=round(prior_floor, 5), prior_overflow=round(prior_overflow, 5),
            search_floor_share=round(share_floor, 5),
            search_overflow_share=round(share_overflow, 5),
            n_moves_returned=len(moves), total_visits=total_visits,
        ))
        if (i + 1) % 40 == 0:
            print(f"  {i+1}/{len(found)} ausgewertet ...", file=sys.stderr)

    def summarize(sel, label):
        if not sel:
            return dict(n=0)
        pf = np.array([r["prior_floor"] for r in sel])
        po = np.array([r["prior_overflow"] for r in sel])
        sf = np.array([r["search_floor_share"] for r in sel])
        so = np.array([r["search_overflow_share"] for r in sel])
        return dict(
            n=len(sel), label=label,
            prior_floor_mean=round(float(pf.mean()), 5),
            prior_overflow_mean=round(float(po.mean()), 5),
            prior_ratio_floor_zu_overflow=round(float(pf.mean() / po.mean()), 3) if po.mean() > 0 else None,
            search_floor_share_mean=round(float(sf.mean()), 5),
            search_overflow_share_mean=round(float(so.mean()), 5),
            search_ratio_floor_zu_overflow=round(float(sf.mean() / so.mean()), 3) if so.mean() > 0 else None,
            delta_prior_zu_suche_floor=round(float(sf.mean() - pf.mean()), 5),
            delta_prior_zu_suche_overflow=round(float(so.mean() - po.mean()), 5),
        )

    gesamt = summarize(rows, "gesamt")
    je_runde = {}
    for rnd in sorted(set(r["round"] for r in rows if r["round"] is not None)):
        sel = [r for r in rows if r["round"] == rnd]
        je_runde[str(rnd)] = summarize(sel, f"runde_{rnd}")

    if gesamt["n"] == 0:
        lesart = "KEIN_DATENSATZ"
    else:
        pf, po = gesamt["prior_floor_mean"], gesamt["prior_overflow_mean"]
        sf, so = gesamt["search_floor_share_mean"], gesamt["search_overflow_share_mean"]
        prior_asym = pf < po
        search_widens = (pf - sf) if pf else 0
        if prior_asym and abs(sf - pf) < 0.03 and abs(so - po) < 0.03:
            lesart = "H1 (Prior schon asymmetrisch, Suche verschiebt kaum)"
        elif not prior_asym and (sf < so):
            lesart = "H2 (Prior symmetrisch, Suche erzeugt die Asymmetrie)"
        elif prior_asym and (sf < pf or so > po):
            lesart = "H1+H3 (Prior asymmetrisch, Suche verstaerkt es zusaetzlich)"
        else:
            lesart = "UNKLAR -- Rohdaten pruefen, keine der drei vorregistrierten Lesarten trifft glatt"

    result = dict(
        n_qualifizierende_stellungen=len(found),
        sims=SIMS, c_puct=C_PUCT, model=MODEL_ONNX,
        gesamt=gesamt, je_runde=je_runde, lesart=lesart,
        rows=rows,
        stichprobe=dict(
            stride=stride, cap_total=cap_total, cap_per_file=3,
            runden=sorted(rounds) if rounds else "alle", seed=seed,
            auswahl=("zufaellig je Datei (ordnungsfrei)" if seed is not None
                     else "erste N je Datei (Bestandsverhalten, "
                          "bevorzugt Fruehspiel-Stellungen)"),
        ),
        meta=dict(
            kriterien="(a) Farbkonflikt Zielreihe/Zugfarbe -- JEDE Quelle; "
                      "(b) Grossfabrik-Sonne (factory_index==4) ueber "
                      "Restkapazitaet -- exakt, keine Stapel-Schaetzung. "
                      "factory_index 0-3 und 5 NICHT ueber Kapazitaet "
                      "gewertet (Mehrdeutigkeit Sonne/Mond).",
        ),
    )
    out_json.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "rows"},
                     indent=2, ensure_ascii=False))
    print(f"\n-> {out_json}")


if __name__ == "__main__":
    main()
