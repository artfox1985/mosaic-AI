# -*- coding: utf-8 -*-
"""Diagnose-Sonde "Tiling-Ueberraschung" (evaluations/PREREG_tiling_surprise_probe.md par.2, par.3).

Frage: wie gut antizipiert das Netz, was der Tiling-Loeser am Rundenende tut? Je Partie und Runde r in
1..4 werden zwei Zustaende aus dem Record-Strom genommen und mit jedem Netz bewertet; die Differenz
v_net(S_post) - v_net(S_pre) ist die Ueberraschung. Kennzahl, Lesung und Grundmenge stehen in der
Prereg, nicht hier.

## Woher S_pre und S_post kommen (geprueft 2026-10-08)

Beide Zustaende stehen DIREKT im Korpus, ein Engine-Replay ist nicht noetig:

* Self-Play schreibt im Tiling JEDEN Loeser-Schritt als eigenen Record (`self_play.rs:6750-6775`,
  `recording`-Zweig), und der Record-Zustand ist der Zustand VOR dem Schritt (`state_to_json` in
  `tiling_step_with_variant`, `self_play.rs:2774`, angewandt erst danach `:2794-2804`).
* `S_pre` = Zustand des ERSTEN Tiling-Records der Runde = Zustand nach dem letzten Drafting-Zug (Record
  davor ist ein Drafting-Record derselben Runde; das prueft `extract_round_pairs`).
* `S_post` = Zustand des LETZTEN Tiling-Records der Runde. Dessen Aktion ist das zweite `end_tiling`;
  das erste `end_tiling` setzt nur `tiling_done` und den Spieler um (`game.rs:1412-1421`), das zweite
  loest `execute_end_tiling` aus (`game.rs:1423-1424`; Strafen, Rundenwechsel, Neubefuellung ab
  `game.rs:1429`). Der
  Zustand davor ist damit genau der "pre chance"-Zustand aus `round_transition.rs:108-118` (`PreChanceState`) und
  `:137-178` -- aber mit dem GESPIELTEN Loeser (`resolve_tiling_step_with_variant`: Huelle,
  Netz-Stichentscheid), nicht mit `best_first_step_exact`, das `resolve_to_pre_chance` benutzt.
  Ein Replay ueber `resolve_to_pre_chance` wuerde also ein anderes Tiling messen als das gespielte.
* Strafen sind in S_post NOCH NICHT abgezogen (die Steine liegen sichtbar auf der Strafleiste). Der
  Nullpunkt wird deshalb zweimal berichtet: `*_tiling_points` (Punktestand S_post - S_pre) und
  `*_settled_points` (Punktestand des ersten Records der Runde r+1 - S_pre, inkl. Strafen; der
  Neubefuellungs-Zufall beruehrt den Punktestand nicht). Der Record traegt nur den GEKLEMMTEN Stand
  (`serialize.rs:276`, `board.rs:329-332`).
* Partien aus Ausfluegen (`*_x1`) beginnen mitten in der Partie; ihre fruehen Runden fehlen und
  werden als `round_absent` gezaehlt, nicht als Fehler.

## Perspektive (par.5 Punkt 2)

Der Encoder rechnet in Ego-Perspektive von `current_player`: JSON-Pfad `features.rs:857-860`,
Planes `features.rs:1866-1872` (ueber `json_to_state`, `lib.rs:2084-2103`). In S_pre und S_post
steht fast immer ein ANDERER Spieler am Zug (erster gegen zweiten Tiler). Die Sonde haelt die
Perspektive fest, indem sie `current_player` im JSON auf den bewerteten Spieler setzt -- dasselbe
Vorgehen wie der Encoder-Test `features.rs:2402-2404`. Die uebrigen Spieler-Felder, die der Encoder
liest, sind perspektivneutral: `estimated_score` je Spieler (`serialize.rs:252`, gelesen
`features.rs:865`), `chippable_tiling_rows` fuer beide Spieler (`serialize.rs:758-783`).
Bewertet wird jedes Paar aus BEIDEN Perspektiven (Prereg par.2: "je Spieler"); die Teilmenge
`last_drafter` ist die woertliche Lesart "Spieler, dessen Record S_pre ist" (Spieler des letzten
Drafting-Records).

## Was die Koepfe schaetzen (par.5 Punkt 3)

* `value`: ONNX/Torch-Ausgabe `2*P(Sieg)-1` (`export_onnx.py:30-36`, `neural_net.py:2380-2385`);
  hier P(Sieg) = (v+1)/2.
* `points`: Ziel `tanh(eigener ENDSTAND/50)` (`corpus_dataset.py:1659-1674`, `VALUE_SCALE = 50.0`
  `neural_net.py:1357`), also inklusive der Tiling-Punkte dieser Runde. ABER: wo der Record
  `bootstrap_value` traegt, mischt `corpus_dataset.py:1738-1745` mit `TD_LAMBDA` (ungesetzt 0,5,
  `neural_net.py:1359-1365`; in den drei Trainings-Manifesten v34-b01, v35-b02, v35-b10 kein
  `MOSAIC_TD_LAMBDA`) eine GEWINNWAHRSCHEINLICHKEIT (2*bv-1) hinein. Der Kopf ist darum kein reiner
  Punkteschaetzer; die Umrechnung in Punkte (`50*atanh`) ist eine HERLEITUNG und steht neben den
  Rohwerten (`*_raw`, tanh-Einheiten).
* `opp_points`: gespiegelt auf den Gegner-Endstand (`corpus_dataset.py:1691`, Blend `:1747-1748`).
* Die Eingabe traegt die exakte Rundenprojektion schon selbst: `estimated_score` = optimale
  Tiling-Punkte plus feste Strafen (`tiling_solver.rs:611-613`, `serialize.rs:252`). Die Sonde
  berichtet deshalb auch `projection_gap_own` = gesetzte Rundenpunkte - `estimated_score(S_pre)`.

## Referenz root_q

Tiling-Records tragen kein `root_q` (Suche laeuft nur im Drafting). Referenz ist der letzte
Drafting-Record der Runde MIT `root_q`, auf die bewertete Perspektive gedreht (`1 - root_q` fuer den
anderen Spieler; Remisanteil vernachlaessigt, HERLEITUNG), mit Abstand `root_q_lag` in Records.

## Statistik

Summen je Datei (Block), gepoolte Mittel Summe/Summe, Block-Bootstrap mit der DATEI als Block nach
dem Muster `tools/checkpoint_val_eval.py:487-503`. Netzvergleiche sind gepaart: dieselben
Bootstrap-Ziehungen fuer alle Netze.

Aufruf (der Koordinator faehrt die Sonde; exklusiv wie jede netzgestuetzte Sonde, CLAUDE.md):

    python -X utf8 -u tools/probes/tiling_surprise_probe.py \\
        --models alphazero_v34-b01_brierbest alphazero_v35-b02_brierbest alphazero_v35-b10_brierbest \\
        --spec models/v34-b01_brierbest.spec.json --val-list data/window_v35_b02_val.txt

Ohne Netz (nur Zustandsauszug und Nullpunkt, kein Wheel-Export noetig): `--no-net`.
"""
from __future__ import annotations

import argparse
import math
import os
import sys
import time
from collections import Counter, OrderedDict
from datetime import datetime
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "engine" / "py"))
sys.path.insert(0, str(_ROOT / "tools"))

PREREG = "PREREG_tiling_surprise_probe.md par.2/par.3"
ROUNDS = (1, 2, 3, 4)
ALL_ROUNDS_KEY = "R1-4"
SUBSETS = ("all", "last_drafter")
# Zielskala der Punktekoepfe: tanh(Punkte / VALUE_SCALE), neural_net.py:1357.
VALUE_SCALE = 50.0
# Abstand zum Rand vor atanh (die Koepfe enden in tanh, |x| < 1).
ATANH_CLIP = 1e-6
BOOTSTRAP_SEED_DEFAULT = 20261008
BOOTSTRAP_DRAWS_DEFAULT = 1000
# Wheel-Exporte, ohne die die Netzbewertung nicht laeuft (lib.rs:1997, lib.rs:2084).
REQUIRED_EXPORTS = ("state_features_from_json", "state_planes_from_json")
# Spalten einer Summenzeile je Datei: Anzahl, Summe, Quadratsumme, Betragssumme und die drei
# Summen fuer die Regressionssteigung gegen einen Regressor x (nur wo x mitgegeben wird).
SUM_FIELDS = ("n", "s", "ss", "sa", "sx", "sxx", "sxy")


# ---------------------------------------------------------------- Record-Strom

def group_games(records) -> "OrderedDict[str, list]":
    """Records je `game_id` in Dateireihenfolge."""
    games: OrderedDict = OrderedDict()
    for rec in records:
        if isinstance(rec, dict) and isinstance(rec.get("state"), dict):
            games.setdefault(str(rec.get("game_id")), []).append(rec)
    return games


def action_type(rec: dict):
    """Typ der Record-Aktion bei einem One-Hot-Record (Tiling: genau ein Policy-Eintrag)."""
    pol = rec.get("policy") or []
    if len(pol) != 1:
        return None
    return (pol[0].get("action") or {}).get("type")


def _phase(rec):
    return rec["state"].get("phase")


def _round(rec):
    return int(rec["state"].get("round", 0))


def _scores(state: dict) -> list:
    return [int(p.get("score", 0)) for p in state.get("players", [])]


def _estimated(state: dict) -> list:
    return [int(p.get("estimated_score", 0)) for p in state.get("players", [])]


def extract_round_pairs(seq: list, rounds=ROUNDS):
    """S_pre/S_post je Runde aus der Record-Folge EINER Partie.

    Rueckgabe: (Liste von Paar-Dicts, Counter der Ausfallgruende). Ein Paar traegt `round`,
    `s_pre`, `s_post` (State-Dicts, unveraendert), `last_drafter`, `score_pre`, `score_post`,
    `score_next` (None ohne Folgerunde), `estimated_pre`, `root_q` (P(Sieg) aus Sicht von
    `root_q_player` oder None) und `root_q_lag`.
    """
    pairs, skips = [], Counter()
    for rnd in rounds:
        idx = [i for i, r in enumerate(seq) if _phase(r) == "tiling" and _round(r) == rnd]
        if not idx:
            skips["round_absent"] += 1
            continue
        if idx[-1] - idx[0] + 1 != len(idx):
            skips["tiling_not_contiguous"] += 1
            continue
        first, last = idx[0], idx[-1]
        if first == 0 or _phase(seq[first - 1]) != "drafting" or _round(seq[first - 1]) != rnd:
            skips["no_drafting_before_tiling"] += 1
            continue
        tiling = seq[first:last + 1]
        n_end = sum(1 for r in tiling if action_type(r) == "end_tiling")
        if action_type(seq[last]) != "end_tiling" or n_end != 2:
            skips["tiling_not_closed"] += 1
            continue
        # Drafting-Records derselben Runde direkt vor dem Tiling (rueckwaerts bis Rundenbeginn).
        drafting = []
        j = first - 1
        while j >= 0 and _phase(seq[j]) == "drafting" and _round(seq[j]) == rnd:
            drafting.append(seq[j])
            j -= 1
        root_q = root_q_player = root_q_lag = None
        for lag, rec in enumerate(drafting):
            if rec.get("root_q") is not None:
                root_q, root_q_player, root_q_lag = float(rec["root_q"]), int(rec["player"]), lag
                break
        nxt = seq[last + 1] if last + 1 < len(seq) else None
        score_next = _scores(nxt["state"]) if nxt is not None and _round(nxt) == rnd + 1 else None
        if score_next is None:
            skips["no_next_round_record"] += 1   # Paar bleibt, nur ohne gesetzte Punkte
        s_pre, s_post = seq[first]["state"], seq[last]["state"]
        pairs.append({
            "round": rnd,
            "s_pre": s_pre,
            "s_post": s_post,
            "last_drafter": int(drafting[0]["player"]),
            "score_pre": _scores(s_pre),
            "score_post": _scores(s_post),
            "score_next": score_next,
            "estimated_pre": _estimated(s_pre),
            "root_q": root_q,
            "root_q_player": root_q_player,
            "root_q_lag": root_q_lag,
        })
    return pairs, skips


def with_perspective(state: dict, player: int) -> dict:
    """Flache Kopie mit `current_player = player` -- legt die Ego-Perspektive des Encoders fest
    (features.rs:857). Das Original bleibt unveraendert."""
    out = dict(state)
    out["current_player"] = int(player)
    return out


def perspective_root_q(root_q, record_player, player):
    """root_q ist P(Sieg) des Record-Spielers; fuer den anderen Spieler 1 - root_q (Remis
    vernachlaessigt, HERLEITUNG)."""
    if root_q is None:
        return None
    return float(root_q) if int(record_player) == int(player) else 1.0 - float(root_q)


def win_prob(v: float) -> float:
    """Wertkopf-Ausgabe 2*P(Sieg)-1 -> P(Sieg) (export_onnx.py:30-36)."""
    return (float(v) + 1.0) / 2.0


def head_points(x: float) -> float:
    """tanh-Ausgabe eines Punktekopfs -> Punkte (Umkehr von tanh(P/VALUE_SCALE))."""
    x = max(-1.0 + ATANH_CLIP, min(1.0 - ATANH_CLIP, float(x)))
    return VALUE_SCALE * math.atanh(x)


def null_rows(pair: dict, player: int) -> dict:
    """Netzfreie Groessen je (Paar, Perspektive): Wert und optional Regressor."""
    o = 1 - player
    pre, post, nxt = pair["score_pre"], pair["score_post"], pair["score_next"]
    rows = {
        "own_tiling_points": (post[player] - pre[player], None),
        "opp_tiling_points": (post[o] - pre[o], None),
    }
    if nxt is not None:
        own_settled = nxt[player] - pre[player]
        rows["own_settled_points"] = (own_settled, None)
        rows["opp_settled_points"] = (nxt[o] - pre[o], None)
        rows["projection_gap_own"] = (own_settled - pair["estimated_pre"][player], None)
    if pair["root_q_lag"] is not None:
        rows["root_q_lag"] = (pair["root_q_lag"], None)
    return rows


def surprise_rows(pair: dict, player: int, out_pre: dict, out_post: dict) -> dict:
    """Netzabhaengige Ueberraschungen je (Paar, Perspektive). `out_*` sind die Kopfausgaben im
    Zustand mit festgehaltener Perspektive `player`: {"value", "points", "opp_points"}."""
    o = 1 - player
    own_tiling = pair["score_post"][player] - pair["score_pre"][player]
    opp_tiling = pair["score_post"][o] - pair["score_pre"][o]
    wp_pre, wp_post = win_prob(out_pre["value"]), win_prob(out_post["value"])
    rows = {
        "value": (wp_post - wp_pre, None),
        "value_level_pre": (wp_pre, None),
        "points_raw": (out_post["points"] - out_pre["points"], None),
        "points": (head_points(out_post["points"]) - head_points(out_pre["points"]), own_tiling),
    }
    if out_pre.get("opp_points") is not None and out_post.get("opp_points") is not None:
        rows["opp_points_raw"] = (out_post["opp_points"] - out_pre["opp_points"], None)
        rows["opp_points"] = (head_points(out_post["opp_points"])
                              - head_points(out_pre["opp_points"]), opp_tiling)
    rq = perspective_root_q(pair["root_q"], pair["root_q_player"], player) \
        if pair["root_q"] is not None else None
    if rq is not None:
        rows["value_vs_root_q"] = (wp_post - rq, None)
    return rows


def subsets_for(pair: dict, player: int):
    return ("all", "last_drafter") if player == pair["last_drafter"] else ("all",)


# ---------------------------------------------------------------- Statistik

class SumTable:
    """Summen je (Schluessel, Datei). Schluessel: (Bereich, Runde, Teilmenge, Groesse)."""

    def __init__(self, n_files: int):
        self.n_files = n_files
        self.rows: dict = {}

    def add(self, key, file_index: int, value: float, x=None) -> None:
        arr = self.rows.get(key)
        if arr is None:
            arr = self.rows[key] = np.zeros((self.n_files, len(SUM_FIELDS)), dtype=np.float64)
        v = float(value)
        a = arr[file_index]
        a[0] += 1.0
        a[1] += v
        a[2] += v * v
        a[3] += abs(v)
        if x is not None:
            xv = float(x)
            a[4] += xv
            a[5] += xv * xv
            a[6] += xv * v

    def keys(self):
        return list(self.rows.keys())


def _ratio(num, den):
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(den > 0, num / den, np.nan)


def _slope(t):
    """OLS-Steigung y auf x aus Summen; t[..., SUM_FIELDS]."""
    n, sy, sx, sxx, sxy = t[..., 0], t[..., 1], t[..., 4], t[..., 5], t[..., 6]
    with np.errstate(divide="ignore", invalid="ignore"):
        varx = sxx - sx * sx / np.where(n > 0, n, np.nan)
        cov = sxy - sx * sy / np.where(n > 0, n, np.nan)
        return np.where(varx > 0, cov / varx, np.nan)


def ci95(draws):
    d = np.asarray(draws, dtype=np.float64)
    d = d[np.isfinite(d)]
    if d.size == 0:
        return None
    return [float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))]


def boot_draws(arr, boot_idx) -> dict:
    """Bootstrap-Ziehungen der Kennzahlen; arr [F, 7], boot_idx [B, F] Dateiindizes."""
    t = arr[boot_idx].sum(axis=1)  # [B, 7]
    return {"mean": _ratio(t[:, 1], t[:, 0]), "mean_abs": _ratio(t[:, 3], t[:, 0]),
            "slope": _slope(t)}


def summarize(arr, boot_idx, with_slope: bool) -> dict:
    """Punktschaetzer und Datei-Bootstrap-CIs fuer eine Summenmatrix [F, 7]."""
    tot = arr.sum(axis=0)
    n = int(tot[0])
    out = {"n": n, "n_files_with_data": int((arr[:, 0] > 0).sum())}
    if n == 0:
        return out
    mean = tot[1] / n
    var = max(tot[2] / n - mean * mean, 0.0)
    out["mean"] = float(mean)
    out["sd"] = float(math.sqrt(var * n / (n - 1))) if n > 1 else None
    out["mean_abs"] = float(tot[3] / n)
    draws = boot_draws(arr, boot_idx)
    out["mean_ci95"] = ci95(draws["mean"])
    out["mean_abs_ci95"] = ci95(draws["mean_abs"])
    if with_slope:
        s = _slope(tot[None, :])[0]
        out["slope"] = None if not np.isfinite(s) else float(s)
        out["slope_ci95"] = ci95(draws["slope"])
    return out


def paired_difference(arr_a, arr_b, boot_idx) -> dict:
    """A minus B auf denselben Zustaenden und denselben Ziehungen (Mittel und mittlerer Betrag)."""
    ta, tb = arr_a.sum(axis=0), arr_b.sum(axis=0)
    if ta[0] == 0 or tb[0] == 0:
        return {"n": 0}
    da, db = boot_draws(arr_a, boot_idx), boot_draws(arr_b, boot_idx)
    return {
        "n": int(ta[0]),
        "mean_diff": float(ta[1] / ta[0] - tb[1] / tb[0]),
        "mean_diff_ci95": ci95(da["mean"] - db["mean"]),
        "mean_abs_diff": float(ta[3] / ta[0] - tb[3] / tb[0]),
        "mean_abs_diff_ci95": ci95(da["mean_abs"] - db["mean_abs"]),
    }


# ---------------------------------------------------------------- Standard-Kennzahlen

class SideMetrics:
    """Standard-Kennzahlen (CLAUDE.md) je Runde und Sitz am Zustand S_post, plus Endstand und Marge
    je Sitz aus den Record-Feldern `scores_unclamped`. Nur Mittel, kein CI: Beschreibung der
    Grundmenge, keine Entscheidungsgroesse."""

    FIELDS = ("score", "margin", "floor_len", "col_voll", "col_max", "col_ge3", "col_ge4",
              "row_fill_sum")

    def __init__(self):
        self.sums: dict = {}
        self.counts: Counter = Counter()
        self.final = {0: [], 1: []}

    def add_post_state(self, rnd: int, state: dict) -> None:
        from counterfactual_tiling_ranking import player_marks  # Standard-Kennzahlen je Stellung
        scores = _scores(state)
        for seat in (0, 1):
            m = player_marks(state, seat)
            vals = {
                "score": scores[seat], "margin": scores[seat] - scores[1 - seat],
                "floor_len": m["floor_len"], "col_voll": m["col_voll"], "col_max": m["col_max"],
                "col_ge3": m["col_ge3"], "col_ge4": m["col_ge4"], "row_fill_sum": sum(m["row_fill"]),
            }
            key = (rnd, seat)
            acc = self.sums.setdefault(key, {f: 0.0 for f in self.FIELDS})
            for f in self.FIELDS:
                acc[f] += float(vals[f])
            stp = acc.setdefault("scoring_tile_points", [0.0] * len(m["scoring_tile_points"]))
            for i, v in enumerate(m["scoring_tile_points"][:len(stp)]):
                stp[i] += float(v)
            self.counts[key] += 1

    def add_game(self, seq: list) -> None:
        rec = seq[0]
        src = rec.get("scores_unclamped") or rec.get("scores")
        if not src or len(src) != 2 or rec.get("completed") is False:
            return
        for seat in (0, 1):
            self.final[seat].append((float(src[seat]), float(src[seat] - src[1 - seat])))

    def to_json(self) -> dict:
        per_round = {}
        for (rnd, seat), acc in sorted(self.sums.items()):
            n = self.counts[(rnd, seat)]
            entry = {"n": n}
            for f in self.FIELDS:
                entry[f] = acc[f] / n
            entry["scoring_tile_points_by_criterion"] = [v / n for v in acc["scoring_tile_points"]]
            per_round.setdefault(f"R{rnd}", {})[f"seat{seat}"] = entry
        final = {}
        for seat, rows in self.final.items():
            if rows:
                final[f"seat{seat}"] = {"n_games": len(rows),
                                        "final_score_mean": float(np.mean([r[0] for r in rows])),
                                        "final_margin_mean": float(np.mean([r[1] for r in rows]))}
        return {"at_s_post_by_round": per_round, "final_by_seat": final,
                "note": ("Zustand S_post (Strafen noch nicht abgezogen); Reihen-/Spaltenauslastung, "
                         "Strafleiste und Punkte je Wertungsplatte ueber "
                         "counterfactual_tiling_ranking.player_marks; Endstand/Marge aus "
                         "scores_unclamped der Partie. Keine Arme: alle Netze bewerten dieselben "
                         "Zustaende, eine Differenz zwischen Armen entfaellt.")}


# ---------------------------------------------------------------- Netzbewertung

def require_exports(module, names=REQUIRED_EXPORTS) -> None:
    """Bricht lesbar ab, wenn das geladene Wheel einen benoetigten Export nicht hat."""
    missing = [n for n in names if not hasattr(module, n)]
    if missing:
        raise SystemExit(
            f"ABBRUCH: das geladene mosaic_rust ({getattr(module, '__file__', '?')}) exportiert "
            f"{', '.join(missing)} nicht. Wheel neu bauen (python -m maturin build, dann pip "
            f"install) -- Exporte stehen in engine/src/lib.rs (#[pyfunction] plus m.add_function).")


def encode_states(mr, states: list):
    """Flachvektor und Planes je Zustand ueber die Rust-Exporte (dieselbe Route wie
    neural_net.state_to_tensor_rust / state_to_planes_rust, neural_net.py:140-182)."""
    import json
    flats, planes = [], []
    for st in states:
        js = json.dumps(st)
        flats.append(np.asarray(mr.state_features_from_json(js), dtype=np.float32))
        flat_planes, shape = mr.state_planes_from_json(js)
        planes.append(np.asarray(flat_planes, dtype=np.float32).reshape(tuple(shape)))
    return np.stack(planes), np.stack(flats)


def _fit_flat(flat, width: int, name: str):
    """Additive Eingabe-Regel wie neural_net.py:2360-2366: breiterer Encoder wird gekuerzt."""
    if flat.shape[1] > width:
        return flat[:, :width]
    if flat.shape[1] < width:
        raise SystemExit(f"ABBRUCH: {name} erwartet {width} Flachmerkmale, das Wheel liefert "
                         f"{flat.shape[1]} -- Wheel aelter als das Modell.")
    return flat


class TorchEvaluator:
    """Checkpoint (.pth) ueber neural_net.build_model_from_checkpoint (wie
    checkpoint_val_eval.py:768-773), Ausgabe-Reihenfolge neural_net.py:2390-2403."""

    def __init__(self, path: Path, device: str):
        import torch
        from neural_net import build_model_from_checkpoint
        self.torch = torch
        self.device = device
        ckpt = torch.load(str(path), map_location=device)
        self.model, self.encoder = build_model_from_checkpoint(ckpt)
        self.model.to(device)
        self.model.eval()
        self.name = path.name
        self.width = int(getattr(self.model, "input_size"))
        self.opp_index = None
        if getattr(self.model, "has_opp_points_head", False):
            self.opp_index = (5 + (1 if getattr(self.model, "points_dist_bins", 0) > 0 else 0)
                              + (1 if getattr(self.model, "value_head_variant", "tanh") == "wdl" else 0))

    def evaluate(self, planes, flat, batch_size: int) -> dict:
        torch = self.torch
        flat = _fit_flat(flat, self.width, self.name)
        vals, pts, opp = [], [], []
        with torch.no_grad():
            for b0 in range(0, len(flat), batch_size):
                f = torch.from_numpy(flat[b0:b0 + batch_size]).to(self.device)
                if self.encoder == "2d":
                    p = torch.from_numpy(planes[b0:b0 + batch_size]).to(self.device)
                    out = self.model(p, f)
                else:
                    out = self.model(f)
                vals.append(out[1][:, 0].float().cpu().numpy())
                pts.append(out[3][:, 0].float().cpu().numpy())
                if self.opp_index is not None:
                    opp.append(out[self.opp_index][:, 0].float().cpu().numpy())
        return {"value": np.concatenate(vals), "points": np.concatenate(pts),
                "opp_points": np.concatenate(opp) if opp else None}


class OnnxEvaluator:
    """ONNX-Sitzung, einmal gebaut (Muster counterfactual_tiling_ranking.py:285-287). Nur CPU,
    solange onnxruntime ohne CUDA-Provider installiert ist."""

    def __init__(self, path: Path, threads: int):
        import onnxruntime as ort
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = threads
        self.sess = ort.InferenceSession(str(path), sess_options=opts,
                                         providers=["CPUExecutionProvider"])
        self.name = path.name
        ins = {i.name: i for i in self.sess.get_inputs()}
        self.two_d = "planes" in ins
        self.flat_name = "state" if "state" in ins else self.sess.get_inputs()[-1].name
        shape = ins[self.flat_name].shape
        self.width = shape[1] if isinstance(shape[1], int) else None
        self.outputs = [o.name for o in self.sess.get_outputs()]

    def evaluate(self, planes, flat, batch_size: int) -> dict:
        if self.width is not None:
            flat = _fit_flat(flat, self.width, self.name)
        want = ["value", "points"] + (["opp_points"] if "opp_points" in self.outputs else [])
        vals, pts, opp = [], [], []
        for b0 in range(0, len(flat), batch_size):
            feed = {self.flat_name: flat[b0:b0 + batch_size]}
            if self.two_d:
                feed["planes"] = planes[b0:b0 + batch_size]
            res = self.sess.run(want, feed)
            vals.append(np.asarray(res[0]).reshape(-1))
            pts.append(np.asarray(res[1]).reshape(-1))
            if len(res) > 2:
                opp.append(np.asarray(res[2]).reshape(-1))
        return {"value": np.concatenate(vals), "points": np.concatenate(pts),
                "opp_points": np.concatenate(opp) if opp else None}


def _head(out: dict, i: int) -> dict:
    return {k: (None if v is None else float(v[i])) for k, v in out.items()}


# ---------------------------------------------------------------- Lauf

def build_report(table: SumTable, scopes: list, boot_idx, reference: str | None) -> dict:
    """Artefakt-Teil `results`: je Bereich (Netz oder null), Runde, Teilmenge, Groesse."""
    slope_keys = {"points", "opp_points"}
    res: dict = {}
    for key in sorted(table.keys(), key=lambda k: (str(k[0]), str(k[1]), k[2], k[3])):
        scope, rnd, subset, qty = key
        res.setdefault(scope, {}).setdefault(rnd, {}).setdefault(subset, {})[qty] = summarize(
            table.rows[key], boot_idx, with_slope=qty in slope_keys)
    diffs: dict = {}
    if reference is not None:
        for scope in scopes:
            if scope == reference:
                continue
            for key in table.keys():
                if key[0] != scope:
                    continue
                ref_key = (reference,) + key[1:]
                if ref_key not in table.rows:
                    continue
                _, rnd, subset, qty = key
                diffs.setdefault(f"{scope}_minus_{reference}", {}).setdefault(rnd, {}).setdefault(
                    subset, {})[qty] = paired_difference(table.rows[key], table.rows[ref_key], boot_idx)
    return {"by_scope": res, "paired_vs_reference": diffs}


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--models", nargs="*", default=[],
                    help="Modellnamen ohne Endung (models/<name>.pth bzw. .onnx).")
    ap.add_argument("--model-dir", default="models")
    ap.add_argument("--backend", choices=("torch", "onnx"), default="torch",
                    help="torch: .pth auf --device (cuda, falls verfuegbar); onnx: .onnx auf CPU.")
    ap.add_argument("--device", default="auto", help="auto | cuda | cpu (nur --backend torch).")
    ap.add_argument("--threads", type=int, default=1,
                    help="CPU-Threads (onnxruntime intra_op; torch.set_num_threads auf CPU).")
    ap.add_argument("--spec", default="models/v34-b01_brierbest.spec.json",
                    help="Spec des Generators; wird nur protokolliert -- die rohe Netzbewertung "
                         "liest keinen Suchknopf, und S_post ist das GESPIELTE Tiling aus dem Record.")
    ap.add_argument("--val-list", default="data/window_v35_b02_val.txt")
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--max-files", type=int, default=0, help="0 = alle (nur fuer Rauchtests).")
    ap.add_argument("--batch-size", type=int, default=512)
    ap.add_argument("--bootstrap-draws", type=int, default=BOOTSTRAP_DRAWS_DEFAULT)
    ap.add_argument("--bootstrap-seed", type=int, default=BOOTSTRAP_SEED_DEFAULT)
    ap.add_argument("--no-net", action="store_true",
                    help="Nur Zustandsauszug, Nullpunkt und Standard-Kennzahlen; kein Netz, kein Wheel.")
    ap.add_argument("--out", default="evaluations/artifacts/tiling_surprise_probe.json")
    args = ap.parse_args(argv)

    import json
    import corpus_io
    from checkpoint_val_eval import git_state, read_list, rel, sha256_of
    from runtime_block import laufzeit_block

    if not args.no_net and not args.models:
        raise SystemExit("ABBRUCH: --models fehlt (oder --no-net fuer den netzfreien Auszug).")
    wall0, cpu0 = time.monotonic(), time.process_time()

    names = read_list(_ROOT / args.val_list)
    if args.max_files:
        names = names[: args.max_files]
    paths = [_ROOT / args.data_dir / n for n in names]
    missing = [p.name for p in paths if not p.exists()]
    if missing:
        raise SystemExit(f"ABBRUCH: {len(missing)} Val-Dateien fehlen, z. B. {missing[:3]}")

    mr = None
    evaluators: list = []
    threads_used = args.threads
    device = None
    if not args.no_net:
        import mosaic_rust as mr
        require_exports(mr)
        for m in args.models:
            path = _ROOT / args.model_dir / (m + (".pth" if args.backend == "torch" else ".onnx"))
            if not path.exists():
                raise SystemExit(f"ABBRUCH: Modell fehlt: {rel(path)}")
            if args.backend == "torch":
                import torch
                device = ("cuda" if torch.cuda.is_available() else "cpu") \
                    if args.device == "auto" else args.device
                if device == "cpu":
                    torch.set_num_threads(args.threads)
                threads_used = torch.get_num_threads()
                evaluators.append((m, path, TorchEvaluator(path, device)))
            else:
                device = "cpu"
                evaluators.append((m, path, OnnxEvaluator(path, args.threads)))
    scopes = ["null"] + [m for m, _, _ in evaluators]
    reference = evaluators[0][0] if evaluators else None

    print(f"Tiling-Ueberraschung | {len(paths)} Dateien | Netze: "
          f"{', '.join(m for m, _, _ in evaluators) or '(keine, --no-net)'} | backend "
          f"{args.backend if evaluators else '-'} {device or ''}", flush=True)

    table = SumTable(len(paths))
    side = SideMetrics()
    skips: Counter = Counter()
    n_games = n_pairs = n_evals = 0
    n_pairs_by_round: Counter = Counter()
    for fi, path in enumerate(paths):
        t_file = time.monotonic()
        recs = corpus_io.load_records(path)
        file_pairs = []
        for _gid, seq in group_games(recs).items():
            n_games += 1
            side.add_game(seq)
            pairs, sk = extract_round_pairs(seq)
            skips.update(sk)
            file_pairs.extend(pairs)
        for pair in file_pairs:
            n_pairs_by_round[pair["round"]] += 1
            side.add_post_state(pair["round"], pair["s_post"])
            for p in (0, 1):
                for subset in subsets_for(pair, p):
                    for rnd_key in (pair["round"], ALL_ROUNDS_KEY):
                        for qty, (val, x) in null_rows(pair, p).items():
                            table.add(("null", rnd_key, subset, qty), fi, val, x)
        n_pairs += len(file_pairs)

        if evaluators and file_pairs:
            states = []
            for pair in file_pairs:
                for p in (0, 1):
                    states.append(with_perspective(pair["s_pre"], p))
                    states.append(with_perspective(pair["s_post"], p))
            planes, flat = encode_states(mr, states)
            for name, _path, ev in evaluators:
                out = ev.evaluate(planes, flat, args.batch_size)
                n_evals += len(states)
                for i, pair in enumerate(file_pairs):
                    for p in (0, 1):
                        base = 4 * i + 2 * p
                        rows = surprise_rows(pair, p, _head(out, base), _head(out, base + 1))
                        for subset in subsets_for(pair, p):
                            for rnd_key in (pair["round"], ALL_ROUNDS_KEY):
                                for qty, (val, x) in rows.items():
                                    table.add((name, rnd_key, subset, qty), fi, val, x)
        print(f"[{fi + 1}/{len(paths)}] {path.name}: {len(file_pairs)} Paare | gesamt {n_pairs} Paare, "
              f"{n_games} Partien, {n_evals} Netzbewertungen | {time.monotonic() - t_file:.1f} s "
              f"(Lauf {time.monotonic() - wall0:.0f} s)", flush=True)

    rng = np.random.default_rng(args.bootstrap_seed)
    boot_idx = rng.integers(0, len(paths), size=(args.bootstrap_draws, len(paths)))
    report = build_report(table, scopes, boot_idx, reference)

    spec_path = _ROOT / args.spec
    lz = laufzeit_block(wall0, cpu_start=cpu0, threads=threads_used, n_games=n_games)
    lz["s_je_datei"] = round(lz["wanduhr_s"] / len(paths), 3) if paths else None
    lz["s_je_netzbewertung"] = round(lz["wanduhr_s"] / n_evals, 6) if n_evals else None
    lz["cpu_s_hinweis"] = "process_time des Python-Prozesses; GPU-Zeit ist darin nicht enthalten"
    artifact = {
        "prereg": PREREG,
        "created": datetime.now().isoformat(timespec="seconds"),
        **git_state(),
        "inputs": {
            "val_list": rel(_ROOT / args.val_list),
            "val_list_sha256": sha256_of(_ROOT / args.val_list),
            "n_files": len(paths),
            "max_files": args.max_files,
            "models": [{"name": m, "path": rel(p), "sha256": sha256_of(p)} for m, p, _ in evaluators],
            "backend": args.backend if evaluators else None,
            "device": device,
            "batch_size": args.batch_size,
            "spec": {"path": rel(spec_path),
                     "sha256": sha256_of(spec_path) if spec_path.exists() else None,
                     "consumed": False,
                     "note": "nur protokolliert: rohe Netzbewertung liest keinen Suchknopf; "
                             "S_post ist das im Record GESPIELTE Tiling"},
            "wheel": getattr(mr, "__file__", None) and Path(mr.__file__).name,
            "engine_config_contract_hash": (json.loads(mr.engine_config_json()).get("contract_hash")
                                            if mr is not None and hasattr(mr, "engine_config_json")
                                            else None),
        },
        "definitions": {
            "s_pre": "erster Tiling-Record der Runde (Zustand nach dem letzten Drafting-Zug)",
            "s_post": "letzter Tiling-Record der Runde (vor dem zweiten end_tiling = pre chance, "
                      "gespielter Loeser, Strafen noch offen)",
            "perspective": "current_player im JSON auf den bewerteten Spieler gesetzt; jedes Paar aus "
                           "beiden Perspektiven ('all'), 'last_drafter' = Spieler des letzten "
                           "Drafting-Records",
            "value": "P(Sieg)(S_post) - P(Sieg)(S_pre), P = (v+1)/2; Einheit Gewinnwahrscheinlichkeit",
            "value_level_pre": "P(Sieg)(S_pre) (Niveau, keine Differenz)",
            "value_vs_root_q": "P(Sieg)(S_post) - root_q des letzten Drafting-Records mit root_q, "
                               "auf die Perspektive gedreht",
            "points_raw / opp_points_raw": "Kopfdifferenz in tanh-Einheiten",
            "points / opp_points": "Kopfdifferenz in Punkten, 50*atanh (HERLEITUNG: Kopfziel ist mit "
                                   "TD_LAMBDA 0,5 auf bootstrap_value geblendet); slope = OLS gegen "
                                   "*_tiling_points (0 = vorweggenommen, 1 = nicht vorweggenommen)",
            "own/opp_tiling_points": "Punktestand S_post - S_pre",
            "own/opp_settled_points": "Punktestand erster Record Runde r+1 - S_pre (inkl. Strafen, geklemmt)",
            "projection_gap_own": "own_settled_points - estimated_score(S_pre) (Eingabe-Projektion)",
            "root_q_lag": "Abstand des root_q-Records zum letzten Drafting-Record (0 = derselbe)",
            "units_n": "n = Paar-Perspektiven (Paar = Partie x Runde); Grundmenge = Val-Dateien",
        },
        "counts": {
            "games": n_games,
            "pairs": n_pairs,
            "pairs_by_round": {f"R{r}": n_pairs_by_round[r] for r in ROUNDS},
            "skips": dict(skips),
            "net_evaluations": n_evals,
        },
        "bootstrap": {"draws": args.bootstrap_draws, "seed": args.bootstrap_seed, "unit": "file"},
        "results": report,
        "standard_metrics": side.to_json(),
        "laufzeit": lz,
    }
    out = _ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    from checkpoint_val_eval import json_safe
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(json_safe(artifact), fh, indent=1, ensure_ascii=False)
    print(f"Artefakt: {rel(out)} | {n_pairs} Paare, {n_games} Partien | "
          f"{lz['wanduhr_s']} s", flush=True)


if __name__ == "__main__":
    main()
