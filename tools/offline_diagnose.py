"""
tools/offline_diagnose.py — Offline-Diagnose eines trainierten Checkpoints:
Value-Val-R² gesamt + pro Runde (1-5), Policy Top-1/Top-3 (nur echte
Drafting-Schritte, pol_w=1) -- auf demselben Val-DATEI-Split wie train.py
(Datei-Ebene-Split, Seed 20260707, val_frac=0.1), damit die Zahlen 1:1 gegen
den v12-Zyklus (evaluations/STATUS.md, "v12-Zyklus (2026-07-23)") vergleichbar
sind.

`tools/diagnosis.py` deckt das NICHT ab (keine Pro-Runde-R²-Aufschlüsselung,
kein Top-1/Top-3) -- Task #77 (v12b) brauchte genau diese Metriken erneut
und das beim v12-Zyklus dafür genutzte Skript war nirgends im Repo abgelegt
(weder committet noch als Arbeitsdatei liegen geblieben) -- dieses Skript
rekonstruiert das Vorgehen laut STATUS.md-Beschreibung ("mirrort MosaicDataset
1:1 inkl. Runden-Index je Schritt") und wird DIESMAL nach tools/ committet.

Value-Ziel-Berechnung ist 1:1 aus `neural_net.py::MosaicDataset.__init__`
kopiert (own_total/opp_total → tanh-Margin, `round_transition_value`-Override,
`bootstrap_value`-TD-Blend) -- bewusst NICHT der HDF5-Cache direkt
wiederverwendet, weil der keine Pro-Schritt-Rundennummer mitführt (nur die
bereits zu Tensoren geflachten Features). Policy-Ziel/Maske ebenfalls 1:1
kopiert (inkl. Selbstkonsistenz-Fix: gespielte Policy-Aktionen immer in die
Maske aufnehmen).

Verwendung:
    python tools/offline_diagnose.py --model v12_best
    python tools/offline_diagnose.py --model v12b_lr_best v12b_scratch_best v12_best
    python tools/offline_diagnose.py --model v12b_lr_best --out evaluations/offline_diagnose_v12b.json

Task #87 (--frozen): rechnet dieselben Metriken stattdessen auf dem
eingefrorenen, generationsuebergreifenden Set `evaluations/
frozen_eval_set.pkl` (gebaut von `tools/build_frozen_eval_set.py`,
Version "frozen_v1"). Motivation: `val_files()` zieht den Val-Split aus dem
JEWEILS AKTUELLEN data/-Inhalt -- Diagnose-Zahlen zwischen Generationen sind
dadurch NICHT vergleichbar, sobald sich data/ aendert (altes Korpus rotiert
raus). Das frozen Set ist fix (mehrere Korpora, stratifiziert nach Runde)
und macht Netz-Vergleiche ueber Generationen hinweg moeglich. Bestehendes
Verhalten (ohne --frozen) bleibt vollstaendig unveraendert.

    python tools/offline_diagnose.py --frozen --model v10_best v12_best v12b_lr_best
"""
import argparse
import glob
import json
import math
import os
import pickle
import random
import sys
from pathlib import Path

# Windows-Konsolen (cp1252) können die Emoji-Ausgaben sonst nicht kodieren
# (gleiches Muster wie train.py).
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine" / "py"))

from config import DATA_DIR, MODELS_DIR, NUM_ACTIONS, INPUT_SIZE
from neural_net import (
    state_to_tensor, state_to_planes, action_to_id,
    VALUE_SCALE, VALUE_OPP_EPSILON, TD_LAMBDA, build_model_from_checkpoint, encoder_from_state_dict,
)

# Muss 1:1 zu train.py::train() bleiben (val_frac=0.1-Default, Seed 20260707)
# -- sonst ist der Val-Split hier NICHT derselbe wie beim Training, und die
# Zahlen sind nicht vergleichbar.
VAL_SEED = 20260707
VAL_FRAC = 0.1

# Task #87: eingefrorenes generationsuebergreifendes Set (siehe
# tools/build_frozen_eval_set.py). Pfad + erwartete Version fix -- das Set
# ist ab "frozen_v1" unveraenderlich, ein spaeterer frozen_v2 bekaeme einen
# neuen Dateinamen statt diesen zu ueberschreiben.
FROZEN_EVAL_PATH = Path(__file__).resolve().parent.parent / "evaluations" / "frozen_eval_set.pkl"
FROZEN_EVAL_VERSION = "frozen_v1"


def val_files() -> list[str]:
    all_files = sorted(glob.glob(str(DATA_DIR / "*.pkl")))
    shuffled = all_files[:]
    random.Random(VAL_SEED).shuffle(shuffled)
    n_val = max(1, round(len(shuffled) * VAL_FRAC))
    return sorted(shuffled[:n_val])


def load_val_samples(files: list[str], include_planes: bool = False):
    """Läd alle Val-Schritte direkt aus den Pickles -- Value-Ziel/Policy-
    Ziel/Maske sind 1:1-Kopien der Logik aus `MosaicDataset.__init__`
    (neural_net.py), zusätzlich mit Runden-Index je Schritt (der einzige
    Grund, warum hier nicht einfach der bestehende HDF5-Cache
    wiederverwendet wird).

    `include_planes` (Task #11 Phase 2, M3.3): zusätzlich `state_to_planes`
    je Schritt berechnen -- NUR wenn mindestens einer der angefragten
    Checkpoints ein 2D-Checkpoint ist (`main()` entscheidet das VORAB per
    `encoder_from_state_dict`), sonst bleibt das Bestandsverhalten
    unverändert und ungebremst (Planes-Berechnung kostet spürbar Zeit über
    den vollen Val-Split)."""
    states_l, values_l, rounds_l, polw_l = [], [], [], []
    policy_l, masks_l = [], []
    planes_l = [] if include_planes else None

    for f in files:
        with open(f, "rb") as fh:
            game_data = pickle.load(fh)
        for step in game_data:
            if "scores" not in step or "winner" not in step:
                continue
            state = step["state"]
            states_l.append(state_to_tensor(state).numpy())
            if planes_l is not None:
                planes_l.append(state_to_planes(state).numpy())
            rounds_l.append(int(state.get("round", 0)))

            p = step["player"]
            scores_src = step.get("scores_unclamped", step["scores"])
            own_total = float(scores_src[p])
            opp_total = float(scores_src[1 - p])
            val = math.tanh((own_total - opp_total) / VALUE_SCALE)

            rtv = step.get("round_transition_value")
            if rtv is not None:
                val = float(rtv[p]) * 2.0 - 1.0

            bv = step.get("bootstrap_value")
            if bv is not None:
                own_bootstrap = float(bv[p]) * 2.0 - 1.0
                val = TD_LAMBDA * own_bootstrap + (1.0 - TD_LAMBDA) * val
            values_l.append(val)

            t_policy = np.zeros(NUM_ACTIONS, dtype=np.float32)
            for pe in step["policy"]:
                t_policy[action_to_id(pe["action"])] += pe["prob"]
            s = t_policy.sum()
            if s > 0:
                t_policy /= s
            policy_l.append(t_policy)

            mask = np.zeros(NUM_ACTIONS, dtype=np.float32)
            moves = step.get("valid_actions") or state.get("valid_moves", [])
            for mv in moves:
                mask[action_to_id(mv)] = 1.0
            for pe in step["policy"]:
                mask[action_to_id(pe["action"])] = 1.0
            masks_l.append(mask)

            phase = state.get("phase")
            is_start = any(pe["action"].get("is_start") for pe in step["policy"])
            polw_l.append(1.0 if (phase == "drafting" and not is_start) else 0.0)

    planes_out = torch.from_numpy(np.array(planes_l, dtype=np.float32)) if planes_l is not None else None
    return (
        torch.from_numpy(np.array(states_l, dtype=np.float32)),
        np.array(values_l, dtype=np.float32),
        np.array(rounds_l, dtype=np.int64),
        np.array(polw_l, dtype=np.float32),
        np.array(policy_l, dtype=np.float32),
        np.array(masks_l, dtype=np.float32),
        planes_out,
    )


def load_frozen_samples(path: Path = FROZEN_EVAL_PATH, include_planes: bool = False):
    """Laedt `evaluations/frozen_eval_set.pkl` (Task #87,
    tools/build_frozen_eval_set.py). Value-Ziel-/Policy-Ziel-/Masken-
    Berechnung ist 1:1 dieselbe wie in `load_val_samples()` -- die einzige
    Ergaenzung ist das Quellkorpus-Label je Zustand (`source_corpus`, z.B.
    "v10b"/"v12"), das `diagnose()` fuer die Verteilungs-Aufschluesselung
    braucht.

    `include_planes`: siehe `load_val_samples` -- Task #11 Phase 2 (M3.3),
    nur berechnet wenn mindestens ein angefragter Checkpoint ein
    2D-Checkpoint ist."""
    if not path.exists():
        raise SystemExit(
            f"Frozen-Eval-Set nicht gefunden unter {path} -- erst "
            "`python tools/build_frozen_eval_set.py` ausfuehren."
        )
    with open(path, "rb") as fh:
        blob = pickle.load(fh)
    version = blob.get("version")
    if version != FROZEN_EVAL_VERSION:
        print(f"⚠️  Warnung: Set-Version {version!r} != erwartet {FROZEN_EVAL_VERSION!r}")
    records = blob["records"]

    states_l, values_l, rounds_l, polw_l = [], [], [], []
    policy_l, masks_l, corpus_l = [], [], []
    planes_l = [] if include_planes else None

    for rec in records:
        state = rec["state"]
        states_l.append(state_to_tensor(state).numpy())
        if planes_l is not None:
            planes_l.append(state_to_planes(state).numpy())
        rounds_l.append(int(rec.get("round", state.get("round", 0))))
        corpus_l.append(rec["source_corpus"])

        p = rec["player"]
        scores_src = rec.get("scores_unclamped", rec.get("scores"))
        own_total = float(scores_src[p])
        opp_total = float(scores_src[1 - p])
        val = math.tanh((own_total - opp_total) / VALUE_SCALE)

        rtv = rec.get("round_transition_value")
        if rtv is not None:
            val = float(rtv[p]) * 2.0 - 1.0

        bv = rec.get("bootstrap_value")
        if bv is not None:
            own_bootstrap = float(bv[p]) * 2.0 - 1.0
            val = TD_LAMBDA * own_bootstrap + (1.0 - TD_LAMBDA) * val
        values_l.append(val)

        t_policy = np.zeros(NUM_ACTIONS, dtype=np.float32)
        for pe in rec["policy"]:
            t_policy[action_to_id(pe["action"])] += pe["prob"]
        s = t_policy.sum()
        if s > 0:
            t_policy /= s
        policy_l.append(t_policy)

        mask = np.zeros(NUM_ACTIONS, dtype=np.float32)
        moves = rec.get("valid_actions") or state.get("valid_moves", [])
        for mv in moves:
            mask[action_to_id(mv)] = 1.0
        for pe in rec["policy"]:
            mask[action_to_id(pe["action"])] = 1.0
        masks_l.append(mask)

        phase = state.get("phase")
        is_start = any(pe["action"].get("is_start") for pe in rec["policy"])
        polw_l.append(1.0 if (phase == "drafting" and not is_start) else 0.0)

    planes_out = torch.from_numpy(np.array(planes_l, dtype=np.float32)) if planes_l is not None else None
    return (
        torch.from_numpy(np.array(states_l, dtype=np.float32)),
        np.array(values_l, dtype=np.float32),
        np.array(rounds_l, dtype=np.int64),
        np.array(polw_l, dtype=np.float32),
        np.array(policy_l, dtype=np.float32),
        np.array(masks_l, dtype=np.float32),
        np.array(corpus_l),
        version,
        blob.get("seed"),
        len(records),
        planes_out,
    )


def _r2(y_true: np.ndarray, y_pred: np.ndarray) -> float | None:
    if len(y_true) == 0:
        return None
    ss_tot = float(np.sum((y_true - y_true.mean()) ** 2))
    if ss_tot <= 1e-9:
        return None
    ss_res = float(np.sum((y_true - y_pred) ** 2))
    return 1.0 - ss_res / ss_tot


def _rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float | None:
    """Absoluter Vorhersagefehler -- Task #20, Schritt 0.

    NOETIG NEBEN R2, weil R2 den Fehler ins Verhaeltnis zur VORHANDENEN Streuung
    setzt: sind in einer Runde viele Partien bereits entschieden, schrumpft die
    Ausgangsstreuung und R2 faellt, obwohl die Vorhersage gleich gut oder besser
    ist. Fuer die Frage "wie sehr darf ich dem Value-Head in dieser Runde
    trauen" ist der absolute Fehler das richtige Mass.

    Konkreter Anlass: v18_best hat R2 0.1842 in Runde 3, aber nur 0.1157 in
    Runde 4 -- nach R2 wuerde das Vertrauen zum Rundenende hin SINKEN, was der
    Intuition (kuerzerer Horizont = sicherer) widerspricht.
    """
    if len(y_true) == 0:
        return None
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def _target_std(y_true: np.ndarray) -> float | None:
    """Streuung des Ziels selbst -- macht sichtbar, ob ein R2-Abfall von einer
    schrumpfenden Ausgangsstreuung kommt statt von schlechterer Vorhersage."""
    if len(y_true) == 0:
        return None
    return float(np.std(y_true))


def diagnose(model_name: str, states, values, rounds, pol_w, policy_targets, masks,
             batch_size: int = 4096, hidden_override: int | None = None,
             corpus_labels: np.ndarray | None = None, planes=None) -> dict:
    """`planes`: Task #11 Phase 2 (M3.3) -- Planes-Tensor `[N,76,6,6]`, NUR
    gebraucht (und mit einem klaren Fehler statt stillem Ausfall geprüft),
    wenn dieser Checkpoint ein 2D-Checkpoint ist (`build_model_from_checkpoint`
    erkennt das aus dem `state_dict`, siehe `neural_net.py::encoder_from_state_dict`)."""
    ckpt_path = MODELS_DIR / f"alphazero_{model_name}.pth"
    ckpt = torch.load(str(ckpt_path), map_location="cpu")
    model, encoder = build_model_from_checkpoint(ckpt, input_size=INPUT_SIZE, num_actions=NUM_ACTIONS,
                                                  hidden_override=hidden_override)
    if encoder == "2d" and planes is None:
        raise RuntimeError(
            f"{model_name} ist ein 2D-Checkpoint, aber es wurden keine Planes-Daten geladen -- "
            f"main() muss `include_planes=True` an load_val_samples/load_frozen_samples uebergeben, "
            f"sobald mindestens ein angefragtes Modell encoder='2d' ist."
        )
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device).eval()

    n = states.shape[0]
    value_preds = np.zeros(n, dtype=np.float32)
    top1_hits = np.zeros(n, dtype=bool)
    top3_hits = np.zeros(n, dtype=bool)

    masks_t = torch.from_numpy(masks)
    target_argmax = policy_targets.argmax(axis=1)  # (n,) -- meist-besuchte Ziel-Aktion

    with torch.no_grad():
        for i in range(0, n, batch_size):
            sl = slice(i, i + batch_size)
            x = states[sl].to(device)
            m = masks_t[sl].to(device)
            if encoder == "2d":
                xp = planes[sl].to(device)
                pred_p, pred_v, _pred_moon, _pred_points, *_own = model(xp, x)
            else:
                pred_p, pred_v, _pred_moon, _pred_points, *_own = model(x)
            value_preds[sl] = pred_v.squeeze(-1).cpu().numpy()

            masked_logits = pred_p + (m - 1) * 1e9
            top3_idx = torch.topk(masked_logits, k=3, dim=1).indices.cpu().numpy()
            pred_top1 = top3_idx[:, 0]
            tgt = target_argmax[sl]
            top1_hits[sl] = pred_top1 == tgt
            top3_hits[sl] = (top3_idx == tgt[:, None]).any(axis=1)

    result: dict = {"model": model_name, "n_total": int(n)}

    result["value_r2_global"] = _r2(values, value_preds)
    per_round = {}
    for r in range(1, 6):
        rmask = rounds == r
        per_round[str(r)] = {
            "n": int(rmask.sum()),
            "r2": _r2(values[rmask], value_preds[rmask]),
            "rmse": _rmse(values[rmask], value_preds[rmask]),
            "target_std": _target_std(values[rmask]),
        }
    result["value_r2_by_round"] = per_round

    # Entscheidungsmetrik (Nutzer-Anstoss 2026-07-28, Task #15): das GLOBALE
    # Value-R² taugt nicht zur Modellauswahl, weil Runde 5 es nach oben zieht --
    # ausgerechnet die Runde, in der das Netz NIE konsultiert wird:
    # `net_mcts.rs:2265` bypassed den gesamten Netz-Suchpfad zu
    # `round5::choose_action` (exakte Alpha-Beta-Suche, gilt fuer Self-Play,
    # Arena UND Server), und der Runde-4-Bootstrap nutzt
    # `round5::exact_round5_outcome` -- auch dort haengt nichts am Netz-Value.
    # Gemessen entfallen ~17% der Value-Samples auf Runde 5, bei zugleich dem
    # hoechsten R² (~0.66-0.72). Dieses Aggregat laesst Runde 5 daher weg.
    r14_mask = (rounds >= 1) & (rounds <= 4)
    result["value_r2_rounds_1_4"] = _r2(values[r14_mask], value_preds[r14_mask])
    result["n_rounds_1_4"] = int(r14_mask.sum())
    r5_mask = rounds == 5
    result["n_round_5_excluded"] = int(r5_mask.sum())

    draft_mask = pol_w > 0.5
    n_draft = int(draft_mask.sum())
    result["policy_n_drafting"] = n_draft
    if n_draft > 0:
        result["policy_top1"] = float(top1_hits[draft_mask].mean())
        result["policy_top3"] = float(top3_hits[draft_mask].mean())
    else:
        result["policy_top1"] = None
        result["policy_top3"] = None

    # Task #87: Aufschluesselung je Quellkorpus (nur wenn --frozen genutzt
    # wurde) -- zeigt, ob Metriken durch die Korpus-Zusammensetzung des
    # jeweiligen Val-Splits verzerrt sind (Verteilungs-Effekt statt echtem
    # Staerke-/Stil-Unterschied).
    if corpus_labels is not None:
        by_corpus: dict = {}
        for c in sorted(set(corpus_labels.tolist())):
            cmask = corpus_labels == c
            entry: dict = {
                "n": int(cmask.sum()),
                "value_r2": _r2(values[cmask], value_preds[cmask]),
            }
            draft_c = cmask & draft_mask
            n_draft_c = int(draft_c.sum())
            entry["n_drafting"] = n_draft_c
            if n_draft_c > 0:
                entry["policy_top1"] = float(top1_hits[draft_c].mean())
                entry["policy_top3"] = float(top3_hits[draft_c].mean())
            else:
                entry["policy_top1"] = None
                entry["policy_top3"] = None
            by_corpus[str(c)] = entry
        result["by_corpus"] = by_corpus

    return result


def print_table(results: list[dict]) -> None:
    names = [r["model"] for r in results]
    print("\n" + "=" * 70)
    print("  OFFLINE-DIAGNOSE (Val-Split Datei-Ebene, Seed 20260707, val_frac=0.1)")
    print("=" * 70)
    header = "Metrik".ljust(28) + "".join(n.rjust(16) for n in names)
    print(header)
    print("-" * len(header))

    def row(label, values):
        print(label.ljust(28) + "".join(v.rjust(16) for v in values))

    row("n (Val-Züge gesamt)", [str(r["n_total"]) for r in results])
    row("Policy Top-1 (Drafting)",
        [f"{r['policy_top1']*100:.1f}%" if r["policy_top1"] is not None else "n/a" for r in results])
    row("Policy Top-3 (Drafting)",
        [f"{r['policy_top3']*100:.1f}%" if r["policy_top3"] is not None else "n/a" for r in results])
    row("  (n Drafting)", [str(r["policy_n_drafting"]) for r in results])
    row("Value R² RUNDE 1-4  <- Entscheidungsmetrik",
        [f"{r.get('value_r2_rounds_1_4'):.4f}" if r.get("value_r2_rounds_1_4") is not None else "n/a"
         for r in results])
    row("Value Val-R² global (nur Info)",
        [f"{r['value_r2_global']:.4f}" if r["value_r2_global"] is not None else "n/a" for r in results])
    for rd in range(1, 6):
        label = f"R² Runde {rd}" + ("  (irrelevant: Alpha-Beta)" if rd == 5 else "")
        row(label,
            [(f"{r['value_r2_by_round'][str(rd)]['r2']:.4f}"
              if r['value_r2_by_round'][str(rd)]['r2'] is not None else "n/a") for r in results])
    print("-" * (34 + 16 * len(results)))
    print("  Absoluter Value-Fehler je Runde (RMSE) + Streuung des Ziels --")
    print("  Task #20: R² faellt, wenn die ZIELSTREUUNG schrumpft, auch bei gleicher")
    print("  Vorhersagequalitaet. Fuer Vertrauens-Gewichtung zaehlt der RMSE.")
    for rd in range(1, 6):
        row(f"RMSE Runde {rd}",
            [(f"{r['value_r2_by_round'][str(rd)]['rmse']:.4f}"
              if r['value_r2_by_round'][str(rd)].get('rmse') is not None else "n/a")
             for r in results])
    for rd in range(1, 6):
        row(f"  Zielstreuung R{rd}",
            [(f"{r['value_r2_by_round'][str(rd)]['target_std']:.4f}"
              if r['value_r2_by_round'][str(rd)].get('target_std') is not None else "n/a")
             for r in results])
    print("=" * 70)
    print("Hinweis: Runde 5 zaehlt NICHT zur Entscheidungsmetrik -- dort umgeht")
    print("net_mcts.rs:2265 das Netz komplett (exakte Alpha-Beta-Suche), und der")
    print("Runde-4-Bootstrap nutzt round5::exact_round5_outcome. Das globale R²")
    print("wird von Runde 5 nach oben gezogen und ist daher irrefuehrend.")


def print_corpus_table(results: list[dict]) -> None:
    """Task #87: separate Tabelle je Quellkorpus (nur befuellt, wenn
    --frozen genutzt wurde -- zeigt Verteilungs-Effekte)."""
    if not results or "by_corpus" not in results[0]:
        return
    corpora = sorted(results[0]["by_corpus"].keys())
    names = [r["model"] for r in results]
    print("\n" + "=" * 70)
    print("  AUFSCHLUESSELUNG JE QUELLKORPUS (frozen set)")
    print("=" * 70)
    for c in corpora:
        header = f"Korpus '{c}'".ljust(28) + "".join(n.rjust(16) for n in names)
        print(header)
        print("-" * len(header))

        def row(label, values):
            print(("  " + label).ljust(28) + "".join(v.rjust(16) for v in values))

        row("n", [str(r["by_corpus"][c]["n"]) for r in results])
        row("Value R²",
            [f"{r['by_corpus'][c]['value_r2']:.4f}" if r["by_corpus"][c]["value_r2"] is not None else "n/a"
             for r in results])
        row("Policy Top-1",
            [f"{r['by_corpus'][c]['policy_top1']*100:.1f}%" if r["by_corpus"][c]["policy_top1"] is not None else "n/a"
             for r in results])
        row("Policy Top-3",
            [f"{r['by_corpus'][c]['policy_top3']*100:.1f}%" if r["by_corpus"][c]["policy_top3"] is not None else "n/a"
             for r in results])
        print()
    print("=" * 70)


# ── Orakel-Metriken (Task #19 A) ─────────────────────────────────────────────
# Nur die ZWEI gegen die Arena validierten Groessen. Belegt am 2026-07-28 gegen
# sieben ENTSCHIEDENE Gating-Paare (v14..v18, tools/offline_vs_arena.py):
#     prior_mass_on_oracle_top3        7/7   Binomial p=0.0156
#     kendall_tau_policy_vs_oracle_q   7/7   Binomial p=0.0156
#     value_pearson_r / value_spearman 5/7
#     prior_recall_at_16               6/7   -- GESAETTIGT (v17_best = 1.0000)
#     value_r2_rounds_1_4 (klassisch)  4/7   p=0.688
# Die beiden Value-Metriken gegen das Orakel scheitern genau an den zwei
# Nach-Orakel-Paaren und gipfeln exakt bei der Orakel-Quelle v16_best -- der in
# Task #89 vermutete Selbstbezugs-Vorteil ist damit fuer die VALUE-Seite
# bestaetigt, fuer die beiden Policy-Metriken dagegen widerlegt (sie steigen
# ueber v16 hinaus monoton weiter). Deshalb werden hier NUR die beiden
# ausgegeben, nicht alle fuenf.
ORACLE_KEYS = ("prior_mass_on_oracle_top3", "kendall_tau_policy_vs_oracle_q")


def add_oracle_metrics(results: list[dict], model_names: list[str]) -> None:
    """Ergaenzt jedes Ergebnis um die beiden validierten Orakel-Metriken.

    Fehlschlaege sind BEWUSST nicht fatal: die Orakel-Labels sind ein
    optionales Artefakt, eine fehlende/veraltete Datei darf die normale
    Diagnose nicht kippen. Es wird dann eine Warnung ausgegeben.
    """
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from oracle_metrics import (aggregate, compute_for_model,  # noqa: E402
                                    load_frozen_states, load_oracle)
    except Exception as e:
        print(f"\n⚠️  Orakel-Metriken uebersprungen (Import): {e}")
        return
    try:
        manifest, labels = load_oracle()
        states_by_idx = load_frozen_states([l["record_index"] for l in labels])
    except FileNotFoundError:
        print("\n⚠️  Orakel-Metriken uebersprungen: keine Orakel-Labels vorhanden "
              "(tools/build_frozen_oracle_labels.py). Mit --no-oracle stumm schalten.")
        return
    except Exception as e:
        print(f"\n⚠️  Orakel-Metriken uebersprungen (Laden): {e}")
        return

    # manifest["model"] traegt den vollen ONNX-Pfad ("models/alphazero_v16_best.onnx")
    # -- auf den blossen Versionsnamen normalisieren, sonst greift die
    # Quellen-Erkennung unten nie.
    raw_src = manifest.get("oracle_model") or manifest.get("model") or "?"
    src = Path(raw_src).stem.removeprefix("alphazero_")
    print(f"\n🔮 Orakel-Metriken gegen {src} ({len(labels)} gelabelte Zustaende, "
          f"{manifest.get('sims', '?')} Sims)")
    for res, name in zip(results, model_names):
        if name == src:
            # Task #89, empirisch bestaetigt: ein Netz gegen die eigene tiefe
            # Suche zu vergleichen gibt einen rein mechanischen Vorteil.
            print(f"  ⚠️  {name} IST die Orakel-Quelle -- Werte nicht vergleichbar, markiert.")
            res["oracle_is_source"] = True
        try:
            agg = aggregate(compute_for_model(name, labels, states_by_idx))["overall"]
            for k in ORACLE_KEYS:
                res[k] = agg.get(k)
            res["oracle_n"] = agg.get("n")
            res["oracle_source"] = src
        except Exception as e:
            print(f"  ⚠️  {name}: {e}")


def print_oracle_table(results: list[dict]) -> None:
    if not any(k in r for r in results for k in ORACLE_KEYS):
        return
    print("\n" + "=" * 70)
    print("  ORAKEL-METRIKEN  (die einzigen arena-validierten Praediktoren)")
    print("=" * 70)
    names = [r["model"] for r in results]
    print(f"{'Metrik':<34}" + "".join(f"{n:>16}" for n in names))
    print("-" * 70)
    for k, lbl in zip(ORACLE_KEYS, ("Prior-Masse auf Top-3", "Kendall-Tau vs Orakel-Q")):
        row = "".join(
            f"{r.get(k):>16.4f}" if isinstance(r.get(k), (int, float)) else f"{'--':>16}"
            for r in results)
        print(f"{lbl:<34}{row}")
    if any(r.get("oracle_is_source") for r in results):
        print("\n⚠️  Mindestens ein Netz ist die Orakel-Quelle selbst -- dessen Werte sind")
        print("    mechanisch bevorteilt und NICHT mit den uebrigen vergleichbar.")
    print("\nHoeher ist besser. 7/7 richtige Richtung auf entschiedenen Gating-Paaren")
    print("(p=0.0156). ERSETZT DIE ARENA NICHT -- n=7, nicht unabhaengige Paare.")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--model", nargs="+", required=True,
                    help="Version-Name(en) OHNE 'alphazero_'-Präfix/'.pth'-Endung, z.B. v12_best")
    p.add_argument("--hidden", type=int, default=None, help="Hidden-Size-Override (Standard: aus Checkpoint)")
    p.add_argument("--batch-size", type=int, default=4096)
    p.add_argument("--out", type=str, default=None,
                    help="Ziel-JSON-Pfad (Standard: evaluations/offline_diagnose_<model1>_vs_....json)")
    p.add_argument("--frozen", action="store_true",
                    help="Task #87: statt val_files() das eingefrorene, generationsuebergreifende "
                         "Set evaluations/frozen_eval_set.pkl verwenden (Default AUS, "
                         "Bestandsverhalten unveraendert).")
    p.add_argument("--threads", type=int, default=None,
                    help="torch.set_num_threads-Override (Standard: max(1, CPU-2) -- "
                         "Schutz gegen parallel laufende Self-Play-Batches).")
    p.add_argument("--no-oracle", action="store_true",
                    help="Die beiden ORAKEL-Metriken weglassen. Standard: sie werden "
                         "berechnet, sobald --frozen gesetzt ist und die Orakel-Labels "
                         "vorliegen. Sie sind die einzigen gegen die Arena VALIDIERTEN "
                         "Praediktoren (7/7 auf entschiedenen Gating-Paaren, Binomial "
                         "p=0.0156) -- value_r2_rounds_1_4 kam auf 4/7 und ist unterhalb "
                         "einer Differenz von etwa 0.015 nachweislich blind. Siehe "
                         "STATUS.md 'Orakel-Metriken validiert (2026-07-28)'.")
    args = p.parse_args()

    threads = args.threads if args.threads is not None else max(1, (os.cpu_count() or 4) - 2)
    torch.set_num_threads(threads)
    print(f"🧵 torch threads: {threads}")

    # Task #11 Phase 2 (M3.3): VORAB pruefen, ob mindestens einer der
    # angefragten Checkpoints ein 2D-Checkpoint ist -- nur dann werden die
    # (spuerbar teureren) Planes mitgeladen. `torch.load` hier ist ein
    # zusaetzlicher, aber billiger Peek-Read (dieselbe Datei wird in
    # `diagnose()` je Modell ohnehin nochmal geladen).
    model_encoders = {}
    for name in args.model:
        ckpt_path = MODELS_DIR / f"alphazero_{name}.pth"
        if not ckpt_path.exists():
            raise SystemExit(f"❌ Modell nicht gefunden: {ckpt_path}")
        peek = torch.load(str(ckpt_path), map_location="cpu")
        model_encoders[name] = encoder_from_state_dict(peek["model_state"])
    need_planes = any(enc == "2d" for enc in model_encoders.values())
    if need_planes:
        two_d = [n for n, e in model_encoders.items() if e == "2d"]
        print(f"🧩 2D-Checkpoint(s) erkannt ({', '.join(two_d)}) -- Planes werden mitgeladen "
              f"(Task #11 Phase 2, kostet zusaetzliche Ladezeit).")

    corpus_labels = None
    frozen_meta = {}
    if args.frozen:
        states, values, rounds, pol_w, policy_targets, masks, corpus_labels, f_version, f_seed, f_n, planes = \
            load_frozen_samples(include_planes=need_planes)
        print(f"🧊 Frozen-Eval-Set: {FROZEN_EVAL_PATH} (Version {f_version}, Seed {f_seed}, n={f_n:,})")
        frozen_meta = {"frozen": True, "frozen_version": f_version, "frozen_seed": f_seed,
                       "frozen_path": str(FROZEN_EVAL_PATH)}
    else:
        files = val_files()
        print(f"📦 Val-Split: {len(files)} Dateien (Seed {VAL_SEED}, val_frac={VAL_FRAC})")
        states, values, rounds, pol_w, policy_targets, masks, planes = load_val_samples(
            files, include_planes=need_planes)
        frozen_meta = {"frozen": False, "val_seed": VAL_SEED, "val_frac": VAL_FRAC, "n_val_files": len(files)}
    print(f"   {len(states):,} Züge geladen.")

    results = []
    for name in args.model:
        print(f"\n🔎 Diagnose: {name} (encoder={model_encoders[name]})")
        res = diagnose(name, states, values, rounds, pol_w, policy_targets, masks,
                        batch_size=args.batch_size, hidden_override=args.hidden,
                        corpus_labels=corpus_labels, planes=planes)
        results.append(res)

    if args.frozen and not args.no_oracle:
        add_oracle_metrics(results, args.model)

    print_table(results)
    print_corpus_table(results)
    print_oracle_table(results)

    out_path = args.out
    if out_path is None:
        base = Path(__file__).resolve().parent.parent / "evaluations"
        suffix = "_frozen" if args.frozen else ""
        out_path = str(base / f"offline_diagnose_{'_vs_'.join(args.model)}{suffix}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            **frozen_meta,
            "results": results,
        }, f, indent=2, ensure_ascii=False)
    print(f"\n📝 Ergebnis gespeichert unter: {out_path}")


if __name__ == "__main__":
    main()
