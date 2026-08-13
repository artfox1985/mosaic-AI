"""
tools/oracle_metrics.py -- Task #89 Teil B, Schritte 2-3: Offline-Metriken der
Kandidaten-Netze GEGEN das Oracle (tiefe v16_best-Suche,
evaluations/frozen_v1_oracle_labels.json, siehe
tools/build_frozen_oracle_labels.py), plus Rangkorrelation mit der bekannten
Elo-Reihenfolge.

Hypothese (project_hybrid_head_attribution / STATUS.md "Task #89"):
wertseitige Metriken gegen eine TIEFE-SUCHE-Referenz (statt reine
Val-R²/Top-1, die im v16-Zyklus nachweislich versagten) sollten Staerke
besser vorhersagen.

Vier Metriken je Netz, GESAMT + je Runde:
  1. Prior-Recall@16: Anteil der Zustaende, bei denen die Oracle-Bestaktion
     (hoechste mcts_visits im gewaehlten Suchzweig) unter den Top-16 der
     EIGENEN rohen Policy-Prior des Kandidaten-Netzes liegt (volle legale
     Aktionsmenge, nicht nur die vom Oracle-Suchlauf betrachteten 16).
  2. Prior-Masse auf Oracle-Top-3: Summe der Policy-Prior-Wahrscheinlichkeit
     des Kandidaten-Netzes auf den 3 Aktionen mit den meisten Oracle-
     Besuchen (aus den vom Oracle-Suchlauf betrachteten Wurzelkandidaten).
  3. Value-Korrelation (Pearson + Spearman): Kandidaten-Netz-Rohwert (tanh,
     Value-Head) vs. Oracle-Root-Value (Such-Q, Sieg-Wahrscheinlichkeit
     [0,1]) -- Pearson ist invariant unter separaten affinen Transformationen
     je Variable, die [-1,1]-vs-[0,1]-Skalendifferenz aendert also den
     Korrelationskoeffizienten NICHT.
  4. Kendall-Tau: Rangfolge der vom Oracle betrachteten Wurzelkandidaten nach
     Kandidaten-Netz-Prior vs. nach Oracle-Q (mcts_q) -- NUR ueber die vom
     Oracle-Suchlauf tatsaechlich untersuchten Kandidaten (die einzigen mit
     einem echten Q-Wert).

Reine Auswertung/Lesezugriffe -- evaluations/frozen_v1_oracle_labels.json
sowie frozen_eval_set.pkl werden nur GELESEN.

ADDITIV ERWEITERT 2026-08-09 (Task E, evaluations/PREREG_prior_blindfleck.md):
zusaetzliche Recall-Breiten (8/16/32/64, rauschfrei), eine rausch-treue
Gumbel-Top-m-Aufnahmerate (Monte Carlo auf logit+Gumbel(0,1), das ECHTE
Wurzelverfahren der Engine), Rangverteilung des Orakel-Top-1 im Prior sowie
Aufschluesselung nach Aktionsanzahl/Runde -- nur ueber neue Funktionen und
optionale, defaultfreie CLI-Flags (`--extra-metrics`, aus per Default); die
bestehenden Aufrufe/Ausgaben oben bleiben davon unberuehrt.
"""
import argparse
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "engine" / "py"))

from config import INPUT_SIZE, MODELS_DIR, NUM_ACTIONS  # noqa: E402
from neural_net import (action_to_id, state_to_tensor, state_to_planes,  # noqa: E402
                        build_model_from_checkpoint)

FROZEN_PKL = ROOT / "evaluations" / "frozen_eval_set.pkl"
# AKTIV SEIT 2026-08-02 (v19-Zyklus): das v18_best-Orakel
# (frozen_v1_oracle_labels_v18.json, 5000 Sims, 1185 Labels, 0 Mismatches,
# gebaut 2026-07-29). Umstellung wie unten geplant vollzogen, nachdem die
# v19-Kandidaten trainiert waren.
#
# HISTORISCH: frozen_v1_oracle_labels.json (v16_best-Orakel) -- galt fuer die
# Bewertung v14..v18 und die dortige Trefferbilanz (Daten-Regime 8/8,
# Architektur-Regime 0/1). Die alte Bilanz ist NICHT auf die neuen Labels
# uebertragbar; tools/offline_vs_arena.py sammelt ab v19 eine neue.
#
# HARTE REGEL (Task #89, am 2026-07-29 empirisch bestaetigt): die Orakel-QUELLE
# darf nicht zu den bewerteten Kandidaten zaehlen. Beleg: die VALUE-Metriken
# gipfeln exakt bei der Quelle v16_best (0,8835) und sagen genau die beiden
# Nach-Orakel-Paare falsch vorher (5/7), waehrend die beiden Policy-Metriken,
# fuer die der Naehe-Vorbehalt widerlegt ist, 8/8 treffen.
# KONKRET JETZT: v18_best (Quelle) wird unter diesen Labels nicht gescored --
# ueber v19-Kandidaten vs. Champion entscheidet allein die Arena.
ORACLE_JSON = ROOT / "evaluations" / "frozen_v1_oracle_labels_v18.json"
OUT_JSON = ROOT / "evaluations" / "task89_oracle_metrics.json"

CANDIDATE_MODELS = ["v14_best", "v14b_best", "v15_f2k_best", "v15_best", "v16_best", "v16"]

# Bekannte Elo-Reihenfolge (STATUS.md, aufsteigend) -- v16 (Epoche 15,
# NICHT der Gate-Champion) hat KEINEN eigenen Elo-Eintrag, siehe Auftrag
# ("v16 ohne Elo als Aussenpunkt kennzeichnen") -- daher hier `None`.
ELO = {
    "v14_best": 884,
    "v14b_best": 961,
    "v15_f2k_best": 987,
    "v15_best": 1029,
    "v16_best": 1132,
    "v16": None,
}


# Kein scipy-Requirement im Projekt (siehe tools/paired_arena_ismcts.py/
# paired_arena_round5.py, dieselbe Konvention) -- Pearson/Spearman/Kendall
# hier bewusst manuell mit numpy implementiert.

def _pearson_r(x: np.ndarray, y: np.ndarray) -> float | None:
    if len(x) < 2:
        return None
    sx, sy = x.std(), y.std()
    if sx < 1e-12 or sy < 1e-12:
        return None
    return float(np.corrcoef(x, y)[0, 1])


def _rankdata(x: np.ndarray) -> np.ndarray:
    """Rangzahlen (1-indiziert), Bindungen bekommen den Mittelwertsrang."""
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(len(x), dtype=float)
    sorted_x = x[order]
    n = len(x)
    i = 0
    while i < n:
        j = i
        while j + 1 < n and sorted_x[j + 1] == sorted_x[i]:
            j += 1
        avg_rank = (i + j) / 2.0 + 1.0
        ranks[order[i:j + 1]] = avg_rank
        i = j + 1
    return ranks


def _spearman_r(x, y) -> float | None:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(x) < 2:
        return None
    return _pearson_r(_rankdata(x), _rankdata(y))


def _kendall_tau_a(x, y) -> float | None:
    """Kendall's tau-a (KEINE Tie-Korrektur -- Bindungen zaehlen als weder
    konkordant noch diskordant, Nenner = alle Paare n*(n-1)/2). Einfacher als
    tau-b, bei den hier typischen kleinen, ueberwiegend bindungsfreien
    Kandidatenmengen (<=16 Aktionen je Zustand) eine vertretbare Vereinfachung
    -- explizit dokumentiert statt stillschweigend `scipy.stats.kendalltau`
    (tau-b) nachzuahmen."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    n = len(x)
    if n < 2:
        return None
    concordant = 0
    discordant = 0
    for i in range(n):
        dx = x[i + 1:] - x[i]
        dy = y[i + 1:] - y[i]
        prod = dx * dy
        concordant += int(np.sum(prod > 0))
        discordant += int(np.sum(prod < 0))
    total_pairs = n * (n - 1) // 2
    if total_pairs == 0:
        return None
    return (concordant - discordant) / total_pairs


def load_oracle(oracle_json: Path = ORACLE_JSON):
    with open(oracle_json, "r", encoding="utf-8") as fh:
        blob = json.load(fh)
    return blob["manifest"], blob["labels"]


def load_frozen_states(record_indices: list[int], frozen_pkl: Path = FROZEN_PKL) -> dict[int, dict]:
    with open(frozen_pkl, "rb") as fh:
        blob = pickle.load(fh)
    records = blob["records"]
    return {idx: records[idx] for idx in record_indices}


def load_model(name: str):
    """Gibt `(model, encoder)` zurueck -- `encoder` in {"flat","2d"} (Task #11
    Phase 2, M3.3), aus dem `state_dict` erkannt (`build_model_from_checkpoint`,
    `neural_net.py::encoder_from_state_dict`), rueckwirkend fuer JEDEN
    Checkpoint funktionsfaehig."""
    ckpt_path = MODELS_DIR / f"alphazero_{name}.pth"
    ckpt = torch.load(str(ckpt_path), map_location="cpu")
    model, encoder = build_model_from_checkpoint(ckpt, input_size=INPUT_SIZE, num_actions=NUM_ACTIONS)
    model.eval()
    return model, encoder


def masked_softmax(logits: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Softmax nur ueber legale Aktionen (mask==1), Rest 0 -- identisches
    Muster zu offline_diagnosis.py::diagnose (masked_logits = logits + (mask-1)*1e9)."""
    masked = logits + (mask - 1.0) * 1e9
    m = masked.max()
    e = np.exp(masked - m)
    e = e * mask  # numerische Sicherheit: illegale Eintraege exakt 0
    s = e.sum()
    if s <= 0:
        return np.zeros_like(logits)
    return e / s


# ---------------------------------------------------------------------------
# Task E (PREREG_prior_blindfleck.md) -- additive Erweiterung, aendert keine
# der obigen Funktionen/Konstanten.
# ---------------------------------------------------------------------------
DEFAULT_RECALL_WIDTHS = (8, 16, 32, 64)
DEFAULT_GUMBEL_SEED = 20260809
DEFAULT_GUMBEL_DRAWS = 200
ACTION_COUNT_BUCKETS = ("<=16", "17-32", "33-64", ">64")


def masked_logits(logits: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Rohe Netz-Logits mit additiver Grossstrafe auf illegale Aktionen --
    exakt dieselbe Konstruktion wie der interne `masked`-Schritt in
    masked_softmax() oben (logits + (mask-1)*1e9). Separat exponiert, weil
    die Gumbel-Top-m-Ziehung der Engine (logit + Gumbel(0,1), dann Top-m) auf
    LOGITS operiert, nicht auf Wahrscheinlichkeiten.
    Aequivalenz zu log(masked_softmax(logits, mask)): beide Groessen
    unterscheiden sich nur um logsumexp(masked_logits(logits, mask)), eine
    pro Zustand FIXE Konstante -- eine Verschiebung aller Werte um dieselbe
    Konstante aendert die argsort-Rangfolge von logit+Gumbel(0,1) nicht.
    Beide Varianten liefern also identische Gumbel-Top-m-Mengen; hier direkt
    die maskierten Rohlogits verwendet (kein Log/Exp-Umweg noetig)."""
    return logits + (mask - 1.0) * 1e9


def action_count_bucket(n_legal: int) -> str:
    """Bucket fuer die Miss-Rate-Aufschluesselung nach Wurzelbreite (Task E,
    Teil c). Prereg-Erwartung: der Fall mit vielen legalen Aktionen ist der
    interessante (Abdeckung dort laut dome_split_diagnosis.json nur ~10%)."""
    if n_legal <= 16:
        return "<=16"
    if n_legal <= 32:
        return "17-32"
    if n_legal <= 64:
        return "33-64"
    return ">64"


def gumbel_recall_rates(masked_logit_row: np.ndarray, best_id: int, widths,
                         rng: np.random.Generator, n_draws: int) -> dict[int, float]:
    """Rausch-treue Aufnahme-Rate des Orakel-Top-1 unter dem ECHTEN
    Wurzelverfahren der Engine: Gumbel-Top-m auf logit+Gumbel(0,1) (eine
    Ziehung ohne Zuruecklegen aus der Prior-Verteilung), dann die m
    hoechsten. Monte Carlo mit `n_draws` Ziehungen aus EINEM, von aussen
    uebergebenen Generator (Task E: ein Generator fuer den GANZEN Lauf, nicht
    einer pro Zustand, damit die komplette Sequenz vom festen Seed
    determiniert ist). Illegale Aktionen tragen die Grossstrafe aus
    masked_logits() und werden dadurch auch nach Gumbel-Rauschen praktisch
    nie gezogen (Selbsttest unten prueft das explizit)."""
    n = masked_logit_row.shape[0]
    gumbel = rng.gumbel(loc=0.0, scale=1.0, size=(n_draws, n))
    perturbed = masked_logit_row[None, :] + gumbel
    order = np.argsort(-perturbed, axis=1)
    rates: dict[int, float] = {}
    for m in widths:
        top = order[:, :m]
        hit = np.any(top == best_id, axis=1)
        rates[int(m)] = float(np.mean(hit))
    return rates


def compute_for_model(model_name: str, oracle_labels: list[dict], states_by_idx: dict[int, dict],
                       extra_metrics: bool = False,
                       recall_widths=DEFAULT_RECALL_WIDTHS,
                       gumbel_rng: np.random.Generator | None = None,
                       gumbel_draws: int = DEFAULT_GUMBEL_DRAWS):
    print(f"  Netz {model_name} ...", flush=True)
    model, encoder = load_model(model_name)

    # Batched Forward-Pass ueber ALLE gelabelten Zustaende (Reihenfolge wie oracle_labels).
    tensors = [state_to_tensor(states_by_idx[lbl["record_index"]]["state"]) for lbl in oracle_labels]
    batch = torch.stack(tensors, dim=0)
    with torch.no_grad():
        if encoder == "2d":
            planes_tensors = [state_to_planes(states_by_idx[lbl["record_index"]]["state"]) for lbl in oracle_labels]
            planes_batch = torch.stack(planes_tensors, dim=0)
            pred_p, pred_v, _pred_moon, _pred_points, *_own = model(planes_batch, batch)
        else:
            pred_p, pred_v, _pred_moon, _pred_points, *_own = model(batch)
    pred_p = pred_p.numpy()
    pred_v = pred_v.squeeze(-1).numpy()

    per_state = []
    for i, lbl in enumerate(oracle_labels):
        rec = states_by_idx[lbl["record_index"]]
        legal_ids = sorted(set(action_to_id(a) for a in rec["valid_actions"]))
        mask = np.zeros(NUM_ACTIONS, dtype=np.float32)
        mask[legal_ids] = 1.0
        prior = masked_softmax(pred_p[i], mask)

        moves = lbl["moves"]
        # Runde 5 (`round5::applies`) faellt in net_search_with_tree auf den
        # EXAKTEN Alpha-Beta-Solver zurueck (STATUS.md: "Runde 5: exakte
        # Alpha-Beta-Suche", `net_mcts.rs::net_search_with_tree`) -- KEINE
        # Netz-Suche, dessen "moves"-Eintraege tragen daher `mcts_visits`/
        # `net_prob`/`action`=null und `root_value`=null (andere Analyse-
        # Struktur, `round5::choose_action_with_analysis`). Architektonisch
        # bewusst kein Netz-Entscheid in dieser Engine -- fuer die Policy-
        # Prior-/Value-Korrelations-Metriken hier daher konsequent
        # ausgeschlossen (nicht nur ein Datenloch), analog zur bereits beim
        # Oracle-Labeling ausgeschlossenen Startkuppel-Platzierung.
        if lbl["round"] >= 5 or lbl.get("root_value") is None or not moves or moves[0].get("action") is None:
            continue
        # Oracle-Bestaktion: hoechste mcts_visits unter den betrachteten Kandidaten
        # (identisch zur "chosen"-Markierung, robust auch ohne sie).
        best_move = max(moves, key=lambda m: m["mcts_visits"])
        best_id = action_to_id(best_move["action"])

        # Top-16 des Kandidaten-Netzes ueber die VOLLE legale Aktionsmenge.
        top16_ids = set(np.argsort(-prior)[:16].tolist())
        recall16_hit = best_id in top16_ids

        # Oracle-Top-3 (nach mcts_visits unter den betrachteten Kandidaten).
        top3_moves = sorted(moves, key=lambda m: -m["mcts_visits"])[:3]
        top3_ids = [action_to_id(m["action"]) for m in top3_moves]
        prior_mass_top3 = float(sum(prior[aid] for aid in top3_ids))

        # Kendall-Tau ueber die vom Oracle betrachteten Kandidaten: Kandidat-
        # Prior-Rang vs. Oracle-Q-Rang. Braucht >=2 Kandidaten mit Varianz.
        cand_ids = [action_to_id(m["action"]) for m in moves]
        cand_prior = [float(prior[aid]) for aid in cand_ids]
        cand_q = [float(m["mcts_q"]) for m in moves]
        tau = None
        if len(moves) >= 3:
            tau = _kendall_tau_a(cand_prior, cand_q)

        row = {
            "record_index": lbl["record_index"],
            "round": lbl["round"],
            "value_pred": float(pred_v[i]),
            "oracle_root_value": lbl["root_value"],
            "recall16_hit": recall16_hit,
            "prior_mass_top3": prior_mass_top3,
            "kendall_tau": tau,
        }

        if extra_metrics:
            # Task E -- rein additiv: alle Basisfelder oben sind bereits
            # berechnet und unveraendert; hier werden nur ZUSAETZLICHE
            # Schluessel angehaengt.
            n_legal = len(legal_ids)
            order_full = np.argsort(-prior)  # identische Aufrufsignatur wie
                                              # oben (top16_ids) -- m=16 bleibt
                                              # dadurch bitgleich zum Altwert
            prior_rank_best = int(np.where(order_full == best_id)[0][0]) + 1

            recall_at_m = {}
            for m in recall_widths:
                recall_at_m[str(m)] = bool(best_id in set(order_full[:m].tolist()))
            if 16 in recall_widths:
                assert recall_at_m["16"] == recall16_hit, (
                    "Additivitaets-Konsistenzbruch: recall_at_m[16] != recall16_hit"
                )

            mlogits = masked_logits(pred_p[i], mask)
            # n_legal zusaetzlich als Selbsttest-Breite: bei m == Anzahl
            # legaler Aktionen MUSS die Gumbel-Aufnahmerate exakt 1.0 sein
            # (die Top-n_legal unter Grossstrafe-maskierten Logits sind immer
            # exakt die legalen Aktionen, egal welches Gumbel-Rauschen faellt).
            gumbel_widths = tuple(recall_widths) + (n_legal,)
            rates = gumbel_recall_rates(mlogits, best_id, gumbel_widths, gumbel_rng, gumbel_draws)

            row.update({
                "num_legal_actions": n_legal,
                "action_count_bucket": action_count_bucket(n_legal),
                "prior_rank_best": prior_rank_best,
                "recall_at_m": recall_at_m,
                "gumbel_recall_at_m": {str(m): rates[m] for m in recall_widths},
                "gumbel_selftest_rate_at_n_legal": rates[n_legal],
            })

        per_state.append(row)

    return per_state


def aggregate(per_state: list[dict], rounds=range(1, 6)) -> dict:
    def block(rows):
        n = len(rows)
        if n == 0:
            return {"n": 0}
        recall16 = float(np.mean([r["recall16_hit"] for r in rows]))
        prior_mass_top3 = float(np.mean([r["prior_mass_top3"] for r in rows]))
        vals_pred = np.array([r["value_pred"] for r in rows])
        vals_oracle = np.array([r["oracle_root_value"] for r in rows])
        pearson_r = spearman_r = None
        if n >= 3 and np.std(vals_pred) > 1e-9 and np.std(vals_oracle) > 1e-9:
            pearson_r = _pearson_r(vals_pred, vals_oracle)
            spearman_r = _spearman_r(vals_pred, vals_oracle)
        taus = [r["kendall_tau"] for r in rows if r["kendall_tau"] is not None]
        mean_tau = float(np.mean(taus)) if taus else None
        return {
            "n": n,
            "prior_recall_at_16": recall16,
            "prior_mass_on_oracle_top3": prior_mass_top3,
            "value_pearson_r": pearson_r,
            "value_spearman_r": spearman_r,
            "kendall_tau_policy_vs_oracle_q": mean_tau,
            "n_kendall_tau_states": len(taus),
        }

    result = {"overall": block(per_state)}
    result["by_round"] = {str(r): block([x for x in per_state if x["round"] == r]) for r in rounds}
    return result


def _task_e_block(rows: list[dict], recall_widths=DEFAULT_RECALL_WIDTHS) -> dict:
    """Ein Aggregations-Block (rauschfreie + rausch-treue Recall-Raten samt
    Miss-Rate bei m=16) ueber eine beliebige Teilmenge von Zeilen -- Baustein
    fuer overall/by_action_count_bucket/by_round in aggregate_task_e()."""
    n = len(rows)
    if n == 0:
        return {"n": 0}
    prior_recall = {
        f"prior_recall_at_{m}": float(np.mean([r["recall_at_m"][str(m)] for r in rows]))
        for m in recall_widths
    }
    gumbel_recall = {
        f"gumbel_recall_at_{m}": float(np.mean([r["gumbel_recall_at_m"][str(m)] for r in rows]))
        for m in recall_widths
    }
    out = {"n": n, **prior_recall, **gumbel_recall}
    if 16 in recall_widths:
        out["miss_rate_top16"] = 1.0 - prior_recall["prior_recall_at_16"]
        out["miss_rate_gumbel_m16"] = 1.0 - gumbel_recall["gumbel_recall_at_16"]
    return out


def aggregate_task_e(per_state: list[dict], recall_widths=DEFAULT_RECALL_WIDTHS,
                      rounds=range(1, 5)) -> dict:
    """Task E (PREREG_prior_blindfleck.md) -- Aggregation der Zusatzfelder aus
    compute_for_model(..., extra_metrics=True). Runde >=5 ist in per_state
    bereits nicht enthalten (Alpha-Beta-Ausschluss oben, unveraendert), daher
    `rounds` hier nur 1-4."""
    rows = [r for r in per_state if "gumbel_recall_at_m" in r]
    n = len(rows)
    if n == 0:
        return {"n": 0}

    overall = _task_e_block(rows, recall_widths)

    ranks = np.array([r["prior_rank_best"] for r in rows], dtype=float)
    overall["oracle_top1_prior_rank"] = {
        "median": float(np.median(ranks)),
        "p90": float(np.percentile(ranks, 90)),
        "max": float(np.max(ranks)),
    }

    selftest_rates = np.array([r["gumbel_selftest_rate_at_n_legal"] for r in rows], dtype=float)
    overall["gumbel_selftest"] = {
        "n": n,
        "all_exactly_1_0": bool(np.all(selftest_rates == 1.0)),
        "min_rate": float(np.min(selftest_rates)),
    }

    by_bucket = {b: _task_e_block([r for r in rows if r["action_count_bucket"] == b], recall_widths)
                 for b in ACTION_COUNT_BUCKETS}
    by_round = {str(rd): _task_e_block([r for r in rows if r["round"] == rd], recall_widths)
                for rd in rounds}

    return {
        "overall": overall,
        "by_action_count_bucket": by_bucket,
        "by_round": by_round,
    }


def spearman_with_elo(model_names: list[str], metric_values: dict[str, float | None]) -> dict:
    """Spearman-Rangkorrelation einer Metrik (ein Skalar je Netz) mit der
    bekannten Elo-Reihenfolge -- NUR ueber Netze mit einem Elo-Eintrag (v16
    ohne Gating-Elo bleibt Aussenpunkt, s.o.)."""
    names = [n for n in model_names if ELO.get(n) is not None and metric_values.get(n) is not None]
    if len(names) < 3:
        return {"n": len(names), "spearman_r": None, "note": "zu wenige Netze mit Elo+Metrik (n<3)"}
    elos = [ELO[n] for n in names]
    vals = [metric_values[n] for n in names]
    r = _spearman_r(elos, vals)
    return {"n": len(names), "models": names, "spearman_r": r}


# Gating-Rueckblick (Auftrag): bekannte reale Gating-Ausgaenge (STATUS.md),
# je ein Paar (Gewinner, Verlierer). Prueft, ob eine Metrik den Gewinner
# richtig als "besser" ausweist (metric[winner] > metric[loser]).
GATING_OUTCOMES = [
    ("v15_best", "v14b_best"),   # v15-Zyklus: v15_best schlaegt v14b_best (Champion-Wechsel)
    ("v16_best", "v15_best"),    # v16-Zyklus: v16_best schlaegt v15_best (Champion-Wechsel)
    ("v15_best", "v15_f2k_best"),  # Task #91 Frischdaten-Ablation: v15 voll > v15_f2k
]


def gating_retrospective(per_model_aggregate: dict, metric_keys: list[str]) -> dict:
    result = {}
    for mk in metric_keys:
        pair_results = []
        n_correct = 0
        n_evaluable = 0
        for winner, loser in GATING_OUTCOMES:
            vw = per_model_aggregate.get(winner, {}).get("overall", {}).get(mk)
            vl = per_model_aggregate.get(loser, {}).get("overall", {}).get(mk)
            if vw is None or vl is None:
                pair_results.append({"winner": winner, "loser": loser, "correct": None})
                continue
            correct = vw > vl
            n_evaluable += 1
            n_correct += int(correct)
            pair_results.append({
                "winner": winner, "loser": loser, "correct": correct,
                f"{mk}_winner": vw, f"{mk}_loser": vl,
            })
        result[mk] = {
            "pairs": pair_results,
            "n_correct": n_correct,
            "n_evaluable": n_evaluable,
        }
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--models", nargs="*", default=CANDIDATE_MODELS)
    # Alle folgenden Flags sind additiv (Task E) -- Default reproduziert das
    # Altverhalten exakt (gleiche Pfade, kein Zusatz-Block, keine RNG-Nutzung).
    ap.add_argument("--oracle-json", default=None,
                    help="Override fuer ORACLE_JSON (Default unveraendert: "
                         f"{ORACLE_JSON.name})")
    ap.add_argument("--frozen-set", default=None,
                    help="Override fuer FROZEN_PKL (Default unveraendert: "
                         f"{FROZEN_PKL.name})")
    ap.add_argument("--out", default=None,
                    help="Override fuer OUT_JSON (Default unveraendert: "
                         f"{OUT_JSON.name})")
    ap.add_argument("--extra-metrics", action="store_true",
                    help="Task E (PREREG_prior_blindfleck.md): zusaetzliche "
                         "Recall-Breiten, rausch-treue Gumbel-Top-m-"
                         "Aufnahmerate, Rangverteilung, Aufschluesselung nach "
                         "Aktionsanzahl/Runde. Default AUS -- ohne dieses "
                         "Flag bleibt Verhalten/Ausgabe unveraendert.")
    ap.add_argument("--recall-widths", nargs="*", type=int, default=list(DEFAULT_RECALL_WIDTHS))
    ap.add_argument("--gumbel-seed", type=int, default=DEFAULT_GUMBEL_SEED)
    ap.add_argument("--gumbel-draws", type=int, default=DEFAULT_GUMBEL_DRAWS)
    args = ap.parse_args()

    oracle_json = (ROOT / args.oracle_json) if args.oracle_json else ORACLE_JSON
    frozen_pkl = (ROOT / args.frozen_set) if args.frozen_set else FROZEN_PKL
    out_json = (ROOT / args.out) if args.out else OUT_JSON
    recall_widths = tuple(args.recall_widths)

    print(f"Lade Oracle-Labels von {oracle_json} ...")
    manifest, labels = load_oracle(oracle_json)
    print(f"  {len(labels)} Oracle-Labels (Modell {manifest['model']}, sims={manifest['sims']})")

    record_indices = [lbl["record_index"] for lbl in labels]
    print(f"Lade zugehoerige Zustaende aus {frozen_pkl} ...")
    states_by_idx = load_frozen_states(record_indices, frozen_pkl)

    # EIN Generator fuer den ganzen Lauf (Task E: Reproduzierbarkeit ueber
    # die komplette Ziehungssequenz, nicht pro Zustand neu geseedet).
    gumbel_rng = np.random.default_rng(args.gumbel_seed) if args.extra_metrics else None

    per_model_metrics = {}
    per_model_aggregate = {}
    per_model_task_e = {}
    for name in args.models:
        per_state = compute_for_model(
            name, labels, states_by_idx,
            extra_metrics=args.extra_metrics,
            recall_widths=recall_widths,
            gumbel_rng=gumbel_rng,
            gumbel_draws=args.gumbel_draws,
        )
        agg = aggregate(per_state)
        per_model_metrics[name] = per_state
        per_model_aggregate[name] = agg
        ov = agg["overall"]
        print(
            f"    n={ov['n']} recall@16={ov['prior_recall_at_16']:.3f} "
            f"top3mass={ov['prior_mass_on_oracle_top3']:.3f} "
            f"value_pearson={ov['value_pearson_r']} value_spearman={ov['value_spearman_r']} "
            f"tau={ov['kendall_tau_policy_vs_oracle_q']}"
        )
        if args.extra_metrics:
            task_e = aggregate_task_e(per_state, recall_widths=recall_widths)
            per_model_task_e[name] = task_e
            te_ov = task_e.get("overall", {})
            print(
                f"    [Task E] miss_rate_gumbel_m16={te_ov.get('miss_rate_gumbel_m16')} "
                f"miss_rate_top16={te_ov.get('miss_rate_top16')} "
                f"selftest_all_1.0={te_ov.get('gumbel_selftest', {}).get('all_exactly_1_0')}"
            )

    # Rangkorrelation jeder Metrik (Overall) mit der bekannten Elo-Reihenfolge.
    metric_keys = [
        "prior_recall_at_16",
        "prior_mass_on_oracle_top3",
        "value_pearson_r",
        "value_spearman_r",
        "kendall_tau_policy_vs_oracle_q",
    ]
    elo_correlations = {}
    for mk in metric_keys:
        vals = {name: per_model_aggregate[name]["overall"].get(mk) for name in args.models}
        elo_correlations[mk] = spearman_with_elo(args.models, vals)

    print("\nSpearman-Rangkorrelation Metrik <-> bekannte Elo-Reihenfolge:")
    for mk, res in elo_correlations.items():
        print(f"  {mk}: {res}")

    retro = gating_retrospective(per_model_aggregate, metric_keys)
    print("\nGating-Rueckblick (haette die Metrik den bekannten Gewinner richtig vorhergesagt?):")
    for mk, res in retro.items():
        print(f"  {mk}: {res['n_correct']}/{res['n_evaluable']} richtig")
        for p in res["pairs"]:
            print(f"    {p}")

    out = {
        "oracle_manifest": manifest,
        "elo_reference": ELO,
        "per_model_aggregate": per_model_aggregate,
        "elo_correlations": elo_correlations,
        "gating_retrospective": retro,
    }
    if args.extra_metrics:
        def _rel(p: Path) -> str:
            try:
                return str(p.relative_to(ROOT))
            except ValueError:
                return str(p)

        out["task_e_prior_blindfleck"] = per_model_task_e
        out["task_e_manifest"] = {
            "models": args.models,
            "oracle_label_file": _rel(oracle_json),
            "frozen_set_file": _rel(frozen_pkl),
            "n_states_labeled": len(labels),
            "gumbel_seed": args.gumbel_seed,
            "n_gumbel_draws": args.gumbel_draws,
            "recall_widths": list(recall_widths),
            "action_count_buckets": list(ACTION_COUNT_BUCKETS),
            "decision_metric": "miss_rate_gumbel_m16",
        }
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    print(f"\nGeschrieben: {out_json}")


if __name__ == "__main__":
    main()
