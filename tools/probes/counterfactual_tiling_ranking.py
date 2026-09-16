# -*- coding: utf-8 -*-
"""Counterfactual-Ranking-Sonde: trifft der Value-Kopf die REIHENFOLGE mehrerer
lokal plausibler Tiling-Plaene -- und ab welcher Runde darf er eine exakte
lokale Entscheidung ueberstimmen?

Vorregistriert in `evaluations/PREREG_round_transition_search_sampling.md`
par.16 (fuehrt par.14.3 Stufe 0 aus, beantwortet par.15 B6 und B7). Die
Wahrheitsquelle, die Kennzahlen, die Schwellen und die Lesart aller vier
Ausgaenge stehen DORT und nicht hier.

## Was diese Sonde anders macht als der Bestand

`tools/tiling_value_reference_main.py:146` schneidet auf PUNKTGLEICHE
Kandidaten zu (`tied = [c for c in cands if c["points"] == top]`) und misst
damit nie, ob das Netz einen Punktvorsprung zu Recht ueberstimmt. Der
gespielte Zug laesst genau das zu: `select_best_tiling_candidate`
(`tiling_solver.rs:944-964`, Modus 0) waehlt nach `punkte * P(Sieg)`. Diese
Sonde nimmt deshalb ALLE Kandidatenpaare und weist `dpoints == 0` und
`dpoints != 0` getrennt aus. Zusaetzlich: Runde 1 (vom aktiven Zweig
ausgeschlossen, `tiling_solver.rs:1407-1409`) und die RANGSTABILITAET der
Referenz ueber gekoppelte Neubefuellungen.

## Wahrheitsquelle (par.16.2), in zwei Guetegraden

Referenz ist eine Tiefensuche NACH gekoppelter Neubefuellung, mit einem
ZWEITEN Netz:

* Runde-4-Stellungen landen nach dem Uebergang im Runde-5-Drafting. Dort
  antwortet der Alpha-Beta-Endspielsolver; `net_search_state_json` traegt dann
  KEIN `root_value`, und das `mcts_q` des gewaehlten Zugs ist der
  Alpha-Beta-Wurzelwert (uebernommen aus
  `tools/tiling_value_reference_main.py:162-173`, dort NICHT am round5.rs-Code
  nachgeprueft). Diese Klasse ist wertkopf-frei, also nicht zirkulaer. Die Sonde
  protokolliert je Auswertung, welcher Grad gegriffen hat (`ref_grade`).
* Runden 1-3 haben nur den Grad NETZ: unabhaengige GEWICHTE, aber dieselbe
  ART von Schaetzer. Der eingebaute Selbsttest dagegen ist M3: kippt das
  Vorzeichen der Referenz ueber ihre eigenen gekoppelten Ziehungen, ist die
  Runde NICHT beantwortet (par.16.5 Ausgang 4).

## Bewertet wird derselbe Zustand wie im Spiel

`net_tiling_tiebreak_value` (`self_play.rs:2216-2226`) wertet das Netz auf dem
NACH-Tiling-Zustand aus und bildet `wp = (value + 1) / 2`; `final_state
.current_player == pi` ist dort strukturell zugesichert (`:2217-2220`). Genau
diese Abbildung steht unten in `net_win_prob`. Der optionale Punkte-Kopf-Term
(`tiling_punkte_weight()`, Default 0,0) ist NICHT nachgebaut -- die Sonde misst
das Default-Verhalten.

Die ONNX-Sitzung wird EINMAL gebaut (Muster
`tools/probes/column_build_prior_mass.py:191`); `mosaic_rust.onnx_eval` laedt
das Netz bei jedem Aufruf neu.
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import math
import os
import statistics
import sys
import time
from pathlib import Path

# corpus_io liegt im Projektstamm, mosaic_rust unter engine/py
# (Muster tools/probes/dead_unit_probe.py:49-50).
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "engine" / "py"))

import corpus_io  # noqa: E402
import mosaic_rust as mr  # noqa: E402
import numpy as np  # noqa: E402
import onnxruntime as ort  # noqa: E402


# ---------------------------------------------------------------- Statistik

def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95-Prozent-Wilson-Intervall. Schwelle (i) aus par.16.4 liest die
    untere Grenze; die Lesart "schadet" (par.16.5 Ausgang 3) die obere."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1.0 + z * z / n
    m = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, m - h), min(1.0, m + h))


def binom_p(k: int, n: int) -> float:
    """Exakter zweiseitiger Binomialtest gegen 50 Prozent
    (gleiche Formel wie tools/tiling_value_reference_main.py:48-53)."""
    if n == 0:
        return 1.0
    lo, hi = min(k, n - k), max(k, n - k)
    return min(1.0, 2 * min(sum(math.comb(n, i) for i in range(0, lo + 1)) / 2 ** n,
                            sum(math.comb(n, i) for i in range(hi, n + 1)) / 2 ** n))


# ------------------------------------------------------------ Netzbewertung

def net_win_prob(state: dict, sess) -> float:
    """P(Sieg) fuer `state.current_player` -- exakt die Abbildung aus
    `self_play.rs:2225-2226` (`wp = (value + 1) / 2`)."""
    js = json.dumps(state)
    flat = np.asarray(mr.state_features_from_json(js), dtype=np.float32)[None, :]
    planes, shape = mr.state_planes_from_json(js)
    planes = np.asarray(planes, dtype=np.float32).reshape((1,) + tuple(shape))
    out = sess.run(["value"], {"planes": planes, "state": flat})[0]
    v = float(np.asarray(out).ravel()[0])
    return (v + 1.0) / 2.0


def reference_batch(next_states: list[str], seeds: list[int], ref_path: str, sims: int,
                    c_puct: float, pi: int) -> list[tuple[float | None, str]]:
    """Referenzwerte der Zustaende NACH der gekoppelten Neubefuellung, aus der
    Perspektive von `pi`. Zweiter Rueckgabewert je Eintrag ist der Guetegrad
    (`exact_ab` oder `net_search`), siehe par.16.2.

    STAPEL-Einstieg, nicht der Einzel-Einstieg: `net_search_state_json` laedt
    das ONNX-Netz bei JEDEM Aufruf neu (`lib.rs:1100-1108` nennt genau das als
    Grund fuer die Stapelvariante). Im Trockenlauf dieser Sonde kostete der
    Einzelweg rund 3 s je Auswertung bei 20 Sims -- praktisch reine Ladezeit.
    """
    try:
        raw = mr.net_search_states_json_batch(next_states, ref_path, sims, c_puct, seeds)
    except Exception:
        return [(None, "error")] * len(next_states)
    out: list[tuple[float | None, str]] = []
    for s in raw:
        try:
            res = json.loads(s)
        except Exception:
            out.append((None, "error"))
            continue
        v = res.get("root_value")
        grade = "net_search"
        if v is None:
            # Runde-5-Drafting: der Alpha-Beta-Solver antwortet, kein root_value.
            moves = res.get("moves") or []
            v = next((m.get("mcts_q") for m in moves if m.get("chosen")), None)
            grade = "exact_ab"
        if v is None:
            out.append((None, "error"))
            continue
        mover = res.get("current_player")
        out.append((float(v) if mover == pi else 1.0 - float(v), grade))
    return out


# --------------------------------------------------------- Fall-Klassifikation

def player_marks(state: dict, pi: int) -> dict:
    """Strukturmerkmale des Nach-Tiling-Bretts, aus dem Spieler-JSON
    (`serialize.rs::serialize_player`). Grundlage der Fall-Klassen M6 und
    zugleich die vier Standard-Kennzahlen, die auf eine STELLUNG anwendbar
    sind (Reihe, Spalte, Strafleiste, Punkte je Wertungsplatte)."""
    p = state["players"][pi]
    floor = p.get("floor") or []
    # Die Geometrie-Groessen haengen unter `score_geo`, NICHT flach am Spieler
    # (am Baum nachgesehen: `score_geo` traegt col_fill/row_fill/special_*,
    # `col_f_max` ist die KAPAZITAET je Spalte, nicht ihr Fuellstand).
    geo = p.get("score_geo") or {}
    col_fill = list(geo.get("col_fill") or [])
    col_cap = list(p.get("col_f_max") or [])
    full_cols = sum(1 for i, c in enumerate(col_fill)
                    if i < len(col_cap) and col_cap[i] and c >= col_cap[i])
    return {
        "score": p.get("score", 0),
        "special_total": geo.get("special_total", 0),
        "special_empty": geo.get("special_empty", 0),
        "special_filled": geo.get("special_total", 0) - geo.get("special_empty", 0),
        "unused_chip_count": p.get("unused_chip_count", 0),
        "chips_taken": p.get("chips_taken", 0),
        "col_fill": col_fill,
        "row_fill": list(geo.get("row_fill") or []),
        "col_voll": full_cols,
        "col_max": max(col_fill) if col_fill else 0,
        "col_ge3": sum(1 for c in col_fill if c >= 3),
        "col_ge4": sum(1 for c in col_fill if c >= 4),
        "tiled_max_row": p.get("tiled_max_row", 0),
        "floor_len": len(floor) if isinstance(floor, list) else 0,
        # Liste ueber die 8 Kriterien -- Punkte je Wertungsplatte, exakt und
        # ohne Zusatzaufruf (Standard-Kennzahl 4 aus CLAUDE.md).
        "scoring_tile_points": list(p.get("scoring_tile_points") or []),
    }


def pair_classes(ma: dict, mb: dict) -> list[str]:
    """Worin unterscheiden sich zwei Kandidaten? Mehrfachnennung erlaubt."""
    cls = []
    if ma["special_filled"] != mb["special_filled"]:
        cls.append("spezialfeld")
    if ma["unused_chip_count"] != mb["unused_chip_count"] or ma["chips_taken"] != mb["chips_taken"]:
        cls.append("chip")
    if ma["col_fill"] != mb["col_fill"]:
        cls.append("spalte")
    if ma["row_fill"] != mb["row_fill"]:
        cls.append("reihe")
    # "Lange Reihe" getrennt von "Reihe": nur, wenn sich die laengste
    # bekachelte Reihe unterscheidet (B1-Lehre, lange Reihen sind ein eigener
    # Hebel, nicht dasselbe wie irgendein Reihenfortschritt).
    if ma["tiled_max_row"] != mb["tiled_max_row"]:
        cls.append("lange_reihe")
    if ma["floor_len"] != mb["floor_len"]:
        cls.append("strafleiste")
    return cls or ["sonstige"]


# ------------------------------------------------------------------- Auswertung

def summarize(pairs: list[dict], key_filter=None) -> dict:
    """M2/M3/M5 ueber eine Teilmenge der Paare. n, Grundmenge und Einheit
    schreibt der Aufrufer dazu (par.16.3)."""
    sel = [p for p in pairs if key_filter is None or key_filter(p)]
    out = {"n_paare": len(sel)}
    if not sel:
        return out
    for name, field in (("mittelwert", "ref_mean"), ("worst_case", "ref_worst")):
        agree = [p for p in sel if p["dwp"] * p[field] != 0.0]
        k = sum(1 for p in agree if p["dwp"] * p[field] > 0)
        lo, hi = wilson(k, len(agree))
        out[name] = {
            "n": len(agree), "treffer": k,
            "quote": round(k / len(agree), 4) if agree else None,
            "wilson95": [round(lo, 4), round(hi, 4)],
            "binom_p_gegen_50": round(binom_p(k, len(agree)), 6) if agree else None,
            "gleichstaende_ausgeschlossen": len(sel) - len(agree),
        }
    stable = [p for p in sel if p["ref_stable"]]
    out["m3_stabilitaet"] = round(len(stable) / len(sel), 4)
    agree_s = [p for p in stable if p["dwp"] * p["ref_mean"] != 0.0]
    k_s = sum(1 for p in agree_s if p["dwp"] * p["ref_mean"] > 0)
    lo, hi = wilson(k_s, len(agree_s))
    out["nur_stabile"] = {
        "n": len(agree_s), "treffer": k_s,
        "quote": round(k_s / len(agree_s), 4) if agree_s else None,
        "wilson95": [round(lo, 4), round(hi, 4)],
        "binom_p_gegen_50": round(binom_p(k_s, len(agree_s)), 6) if agree_s else None,
    }
    grades = {}
    for p in sel:
        grades[p["ref_grade"]] = grades.get(p["ref_grade"], 0) + 1
    out["ref_grade"] = grades
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rank-model", default="models/alphazero_v29-b03_brierbest.onnx",
                    help="Netz, dessen Value-Rangfolge geprueft wird (die Auswahlregel).")
    ap.add_argument("--ref-model", default="models/alphazero_v29-b05_brierbest.onnx",
                    help="UNABHAENGIGES Netz fuer die Referenz-Tiefensuche (par.16.2 Grad NETZ).")
    ap.add_argument("--pattern", default="data/selfplay_v28-b02-policy_*.pkl")
    ap.add_argument("--max-files", type=int, default=40)
    ap.add_argument("--max-positions", type=int, default=200,
                    help="Soll JE RUNDE an Stellungen MIT mindestens zwei Kandidaten (M1 "
                         "zaehlt alle gescannten). par.16.8: bewusst KEIN Gesamtdeckel -- die "
                         "mehrdeutigen Stellungen liegen stark ungleich ueber den Runden "
                         "(gemessen 20/48/71/73/13 von 400 fuer R1-R5), unter einem "
                         "Gesamtdeckel verdraengen R3/R4 genau die duennen Runden. Eine Runde, "
                         "die ihr Soll nicht erreicht, wird als NICHT ENTSCHIEDEN berichtet.")
    ap.add_argument("--max-per-file", type=int, default=2,
                    help="Deckel je Datei UND RUNDE, damit nicht eine Partie die Grundmenge "
                         "stellt. Je Runde, nicht je Datei: ein gemeinsamer Deckel ist in "
                         "Spielreihenfolge erschoepft, bevor Runde 4 drankommt (dieselbe Falle, "
                         "gegen die tools/tiling_value_reference_main.py:68-72 --only-round "
                         "eingefuehrt hat).")
    ap.add_argument("--k", type=int, default=12, help="Wie NET_TILING_TOPK (tiling_solver.rs:863).")
    ap.add_argument("--max-cands", type=int, default=4,
                    help="Hoechstens so viele Kandidaten je Stellung fortsetzen (Kostendeckel).")
    ap.add_argument("--draws", type=int, default=6,
                    help="M gekoppelte Neubefuellungen. Rauschboden von M3 ist 2*(1/2)^M.")
    ap.add_argument("--sims", type=int, default=400)
    ap.add_argument("--c-puct", type=float, default=1.5)
    ap.add_argument("--rounds", default="1,2,3,4")
    ap.add_argument("--progress-every", type=int, default=5)
    ap.add_argument("--out", default="evaluations/artifacts/counterfactual_tiling_ranking.json")
    a = ap.parse_args()

    rounds = {int(x) for x in a.rounds.split(",") if x.strip()}
    t0, c0 = time.time(), time.process_time()
    rank_path = str(REPO / a.rank_model) if not os.path.isabs(a.rank_model) else a.rank_model
    ref_path = str(REPO / a.ref_model) if not os.path.isabs(a.ref_model) else a.ref_model
    for p in (rank_path, ref_path):
        if not os.path.exists(p):
            raise SystemExit(f"Modell fehlt: {p}")

    opts = ort.SessionOptions()
    opts.intra_op_num_threads = 1
    sess = ort.InferenceSession(rank_path, sess_options=opts, providers=["CPUExecutionProvider"])

    files = sorted(glob.glob(str(REPO / a.pattern)))
    if not files:
        raise SystemExit(f"Keine Korpus-Dateien zu {a.pattern}")
    # Deterministisch ueber den Korpus streuen statt die ersten N Partien.
    step_f = max(1, len(files) // max(a.max_files, 1))
    files = files[::step_f][: a.max_files]

    print(f"Rang: {os.path.basename(rank_path)} | Referenz: {os.path.basename(ref_path)}"
          f"@{a.sims} Sims | M={a.draws} | Runden {sorted(rounds)} | {len(files)} Dateien",
          flush=True)

    scanned = {r: 0 for r in rounds}          # M1 Nenner
    ambiguous = {r: 0 for r in rounds}        # M1 Zaehler
    # par.16.8: der Deckel gilt JE RUNDE, nicht als Gesamtzahl. Grund ist die
    # gemessene Ungleichverteilung der mehrdeutigen Stellungen ueber die Runden
    # (tiling_candidate_spread_b01_v3.json: 20/48/71/73/13 von 400 fuer R1-R5).
    # Unter einem Gesamtdeckel verdraengen R3/R4 genau die duennen Runden, und
    # R1 kaeme mit rund zehn Faellen heim -- einer Zahl, die wie ein Befund
    # aussieht und unter der Schwelle von 16.4 keiner sein kann.
    used_by_round = {r: 0 for r in rounds}
    cand_counts = {r: [] for r in rounds}
    pairs: list[dict] = []
    marks_by_round = {r: [] for r in rounds}  # Standard-Kennzahlen je Kandidat
    n_used = n_err = 0
    done = False

    for fi, f in enumerate(files):
        if done:
            break
        try:
            recs = corpus_io.load_records(f)
        except Exception:
            n_err += 1
            continue
        per_file = {r: 0 for r in rounds}
        for rec in recs:
            if done or all(v >= a.max_per_file for v in per_file.values()):
                break
            st = rec.get("state") if isinstance(rec, dict) else None
            if not st or st.get("phase") != "tiling":
                continue
            rnd = int(st.get("round", 0))
            if rnd not in rounds or per_file[rnd] >= a.max_per_file:
                continue
            if used_by_round[rnd] >= a.max_positions:
                continue   # diese Runde ist voll, andere laufen weiter
            pi = int(st.get("current_player", 0))
            scanned[rnd] += 1
            try:
                cands = json.loads(mr.tiling_candidates_json(json.dumps(st), pi, a.k, 0))
            except Exception:
                n_err += 1
                continue
            cand_counts[rnd].append(len(cands))
            if len(cands) < 2:
                continue
            ambiguous[rnd] += 1
            per_file[rnd] += 1
            used_by_round[rnd] += 1
            n_used += 1
            cands = cands[: a.max_cands]

            wp = [net_win_prob(c["state"], sess) for c in cands]
            marks = [player_marks(c["state"], pi) for c in cands]
            marks_by_round[rnd].extend(marks)

            # Referenz: je Kandidat M gekoppelte Neubefuellungen, gleicher Seed
            # fuer alle Kandidaten derselben Ziehung (par.16.2, Kopplung).
            ref = [[None] * a.draws for _ in cands]
            batch_states: list[str] = []
            batch_seeds: list[int] = []
            batch_idx: list[tuple[int, int]] = []
            for d in range(a.draws):
                seed = 1000 + d
                for ci, c in enumerate(cands):
                    try:
                        nxt = mr.advance_after_tiling_json(json.dumps(c["state"]), seed)
                    except Exception:
                        n_err += 1
                        continue
                    batch_states.append(nxt)
                    batch_seeds.append(seed)
                    batch_idx.append((ci, d))
            grades: list[str] = []
            if batch_states:
                for (ci, d), (v, g) in zip(
                        batch_idx,
                        reference_batch(batch_states, batch_seeds, ref_path,
                                        a.sims, a.c_puct, pi)):
                    ref[ci][d] = v
                    grades.append(g)

            grade = max(set(grades), key=grades.count) if grades else "error"
            for ia in range(len(cands)):
                for ib in range(ia + 1, len(cands)):
                    da = [ref[ia][d] - ref[ib][d] for d in range(a.draws)
                          if ref[ia][d] is not None and ref[ib][d] is not None]
                    if len(da) < 2:
                        continue
                    signs = {1 if x > 0 else (-1 if x < 0 else 0) for x in da}
                    nz = {s for s in signs if s != 0}
                    dwp = wp[ia] - wp[ib]
                    dpts = cands[ia]["points"] - cands[ib]["points"]
                    mean = statistics.mean(da)
                    # Worst Case = unguenstigste Ziehung fuer den netz-
                    # bevorzugten Plan: das Minimum von da, wenn das Netz a
                    # vorzieht, sonst das Maximum (Vorzeichen bleibt lesbar).
                    worst = min(da) if dwp > 0 else max(da)
                    prod_a = cands[ia]["points"] * wp[ia]
                    prod_b = cands[ib]["points"] * wp[ib]
                    pairs.append({
                        "round": rnd,
                        "dwp": dwp,
                        "dpoints": dpts,
                        "ref_mean": mean,
                        "ref_worst": worst,
                        "ref_stable": len(nz) == 1 and len(da) == a.draws,
                        "ref_grade": grade,
                        "n_draws_ok": len(da),
                        "classes": pair_classes(marks[ia], marks[ib]),
                        # M4: kippt punkte*P(Sieg) die reine Punktereihenfolge?
                        "flip": (dpts != 0) and ((prod_a - prod_b) * dpts < 0),
                        "dend_scoring": cands[ia]["end_scoring"] - cands[ib]["end_scoring"],
                    })
            if all(v >= a.max_positions for v in used_by_round.values()):
                done = True
        if (fi + 1) % a.progress_every == 0 or done:
            el = time.time() - t0
            progress = " ".join(f"R{r}:{used_by_round[r]}" for r in sorted(rounds))
            print(f"  Datei {fi+1}/{len(files)} | je Runde (Soll {a.max_positions}): {progress}"
                  f" | Paare {len(pairs)} | Fehler {n_err} | {el:.0f}s", flush=True)

    if not pairs:
        raise SystemExit(
            f"Keine Kandidatenpaare -- Diagnose: gescannt {scanned}, mehrdeutig {ambiguous}, "
            f"Fehler {n_err}. Bei mehrdeutig ~ 0 ist das der STOPP aus par.16.5.")

    # ---- M1 Mehrdeutigkeit
    m1 = {}
    for r in sorted(rounds):
        cc = cand_counts[r]
        m1[f"r{r}"] = {
            "n": scanned[r], "grundmenge": "Tiling-Stellungen im Korpus", "einheit": "Stellungen",
            "anteil_mehrdeutig": round(ambiguous[r] / scanned[r], 4) if scanned[r] else None,
            "median_kandidaten": statistics.median(cc) if cc else None,
            "max_kandidaten": max(cc) if cc else None,
        }

    # ---- M2/M3/M5 je Runde und Punktabstandsklasse
    m2 = {}
    for r in sorted(rounds):
        m2[f"r{r}"] = {
            "alle": summarize(pairs, lambda p, r=r: p["round"] == r),
            "dpoints_0": summarize(pairs, lambda p, r=r: p["round"] == r and p["dpoints"] == 0),
            "dpoints_ne0": summarize(pairs, lambda p, r=r: p["round"] == r and p["dpoints"] != 0),
        }
    m2["gepoolt"] = summarize(pairs)

    # ---- M4 Ueberstimmung
    m4 = {}
    for r in sorted(rounds):
        sel = [p for p in pairs if p["round"] == r and p["dpoints"] != 0]
        fl = [p for p in sel if p["flip"]]
        ok = [p for p in fl if p["dwp"] * p["ref_mean"] > 0]
        lo, hi = wilson(len(ok), len(fl))
        m4[f"r{r}"] = {
            "n": len(sel), "grundmenge": "Kandidatenpaare mit Punktabstand != 0",
            "einheit": "Paare",
            "n_kippungen": len(fl),
            "anteil_kippungen": round(len(fl) / len(sel), 4) if sel else None,
            "kippung_richtig": len(ok),
            "quote_richtig": round(len(ok) / len(fl), 4) if fl else None,
            "wilson95": [round(lo, 4), round(hi, 4)] if fl else None,
        }

    # ---- M6 Fall-Klassen
    m6 = {}
    for r in sorted(rounds):
        per_class = {}
        for cls in ("spezialfeld", "chip", "spalte", "reihe", "lange_reihe",
                    "strafleiste", "sonstige"):
            sub = summarize(pairs, lambda p, r=r, c=cls: p["round"] == r and c in p["classes"])
            if sub["n_paare"]:
                per_class[cls] = sub
        m6[f"r{r}"] = per_class

    # ---- Standard-Kennzahlen je Runde (CLAUDE.md), soweit auf eine STELLUNG anwendbar
    std = {}
    for r in sorted(rounds):
        ms = marks_by_round[r]
        if not ms:
            continue
        n_criteria = max((len(m["scoring_tile_points"]) for m in ms), default=0)
        std[f"r{r}"] = {
            "n": len(ms), "grundmenge": "Tiling-Kandidaten (Nach-Tiling-Bretter)",
            "einheit": "Kandidaten",
            "reihenauslastung_median_summe_row_fill": statistics.median(
                [sum(m["row_fill"]) for m in ms]),
            "spaltenauslastung": {
                "median_max_spaltenhoehe": statistics.median([m["col_max"] for m in ms]),
                "median_volle_spalten": statistics.median([m["col_voll"] for m in ms]),
                "median_spalten_ge3": statistics.median([m["col_ge3"] for m in ms]),
                "median_spalten_ge4": statistics.median([m["col_ge4"] for m in ms]),
            },
            "strafleiste_median_len": statistics.median([m["floor_len"] for m in ms]),
            "plattenpunkte_median_je_kriterium": [
                statistics.median([m["scoring_tile_points"][k] for m in ms
                                   if k < len(m["scoring_tile_points"])])
                for k in range(n_criteria)
            ],
            "eigene_punkte_median": statistics.median([m["score"] for m in ms]),
            "spezialfelder_median_gefuellt": statistics.median([m["special_filled"] for m in ms]),
            "margin_zum_gegner": None,
        }

    el = time.time() - t0
    result = {
        "prereg": "PREREG_round_transition_search_sampling.md par.16",
        "frage": "Trifft der Value-Kopf die Reihenfolge lokal plausibler Tiling-Plaene, "
                 "und ab welcher Runde darf er eine exakte lokale Entscheidung ueberstimmen?",
        "wahrheitsquelle": "par.16.2 (c): Tiefensuche nach gekoppelter Neubefuellung; "
                           "Grad exact_ab nur fuer Runde-4-Stellungen (Runde-5-Alpha-Beta), "
                           "sonst Grad net_search mit unabhaengigem Netz.",
        "cli_args": vars(a),
        "modelle": {"rank": rank_path, "ref": ref_path},
        "schwellen_par_16_4": {"wilson_untergrenze_groesser": 0.50, "m3_stabilitaet_min": 0.60,
                               "m3_rauschboden": round(2 * 0.5 ** a.draws, 4)},
        "m1_mehrdeutigkeit": m1,
        "m2_m3_m5_richtung_stabilitaet_aggregatoren": m2,
        "m4_ueberstimmung": m4,
        "m6_fall_klassen": m6,
        "standard_kennzahlen": std,
        "hinweis_margin": "Margin zum Gegner ist auf einer STELLUNG ohne Fortsetzung nicht "
                          "definiert (kein Partieausgang); die Sonde misst Plaene, nicht Partien.",
        "fehler": n_err,
        "laufzeit": {
            "wanduhr_s": round(el, 1),
            "cpu_s": round(time.process_time() - c0, 1),
            "threads": 1,
            "stellungen": n_used,
            "paare": len(pairs),
            "s_je_stellung": round(el / max(n_used, 1), 3),
        },
    }
    outp = REPO / a.out if not os.path.isabs(a.out) else Path(a.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    io.open(outp, "w", encoding="utf-8").write(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({k: result[k] for k in
                      ("m1_mehrdeutigkeit", "m2_m3_m5_richtung_stabilitaet_aggregatoren",
                       "m4_ueberstimmung", "laufzeit")},
                     indent=2, ensure_ascii=False), flush=True)
    print(f"\nArtefakt: {outp}", flush=True)


if __name__ == "__main__":
    main()
