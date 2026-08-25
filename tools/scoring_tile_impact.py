# -*- coding: utf-8 -*-
"""
Mosaic-AI -- Wertungsplatten-Diagnose, Teil 1: Punkteanteil aus Wertungsplatten
(2026-07-26)
============================================================================

Fragestellung: wie viel Prozent der Gesamtpunkte am Spielende kommen aus den
Wertungsplatten (statt aus der laufenden Rundenwertung / Grundwertung)?
Reine Lese-Analyse ueber vorhandene Self-Play-Pickles + die neue additive
Rust-Funktion `end_scoring_from_state_json` (`engine/src/lib.rs`, siehe
`engine/src/serialize.rs::end_scoring_from_state` fuer den Exaktheitsnachweis).

Woher kommt der "letzte Zustand vor Spielende"?
-------------------------------------------------
Self-Play-Records (`self_play.rs::run_net_self_play`) speichern je Spiel-
Schritt EINEN "state"-Snapshot -- der Zustand VOR der jeweiligen Aktion. Der
allerletzte Tiling-Schritt eines Spiels (der die Runde faktisch beendet)
erzeugt KEINEN weiteren Snapshot (das Spiel ist danach vorbei, nichts mehr
zu entscheiden) -- der letzte gespeicherte Record eines Spiels ist daher per
Konstruktion der Zustand, an dem fuer BEIDE Spieler `valid_tiling_rows == []`
UND `chippable_tiling_rows == []` gilt (empirisch verifiziert, siehe
`_is_board_final`). Das `dome_grid` AN DIESEM PUNKT aendert sich bis zum
echten Spielende NICHT MEHR (Tiling ist abgeschlossen) -- die Wertungsplatten-
Endwertung auf diesem `dome_grid` ist daher EXAKT, keine Naeherung.

Validierungs-Formel (Gegenprobe gegen `scores`/`scores_unclamped`)
-------------------------------------------------------------------
Exakt hergeleitet aus dem Code (nicht angenommen!):
  - `game.rs::execute_end_tiling`: nach Tiling-Abschluss beider Spieler wird
    `round_end.rs::score_penalty` (Strafleiste `BROKEN_PENALTIES =
    [-1,-2,-3,-4]` je Fliese, ADDITIV bis zu 4 Fliesen, PLUS
    `FIRST_PLAYER_MARKER_PENALTY = -2` falls der Spieler die Startspieler-
    Fliese haelt) auf den zu diesem Zeitpunkt aktuellen Punktestand
    angewendet (`board.rs::apply_score`, klemmt `score` bei 0, laesst
    `score_unclamped` frei laufen).
  - `game.rs::apply_end_scoring`: ruft danach fuer JEDEN Spieler
    `scoring::calculate_end_scoring(player, scoring_tile_ids)` auf und
    addiert `res.total` per `apply_score` (nochmal geklemmt bei 0).
  => Gesamtpunkte(final, geklemmt) =
       max(0, max(0, score_letzter_snapshot + floor_penalty) + wertung_total)
Das PRUEFT dieses Skript aktiv gegen `scores`/`scores_unclamped` jedes
Spiels (siehe `_predict_final_score`) -- KEINE angenommene, sondern eine
verifizierte Formel (Report zeigt die Trefferquote).
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import pickle
import statistics as stats
from collections import Counter, defaultdict

import mosaic_rust

BROKEN_PENALTIES = [-1, -2, -3, -4]
MAX_BROKEN = 4
FIRST_PLAYER_MARKER_PENALTY = -2

TILE_NAMES = {
    0: "Horizontale Reihen", 1: "Vertikale Reihen", 2: "Diagonale Reihen",
    3: "Mehrfarbige Felder", 4: "Äußere Felder", 5: "Eckplatten",
    6: "Spezialfelder", 7: "Farbenreiche Reihen",
}


def broken_penalty(floor_tiles):
    """Port von `board.rs::PlayerBoard::broken_penalty` (Strafleiste)."""
    n = min(len(floor_tiles), MAX_BROKEN)
    return sum(BROKEN_PENALTIES[i] for i in range(n))


def score_penalty(player_json):
    """Port von `round_end.rs::score_penalty` (Strafleiste + Startspieler-
    Marker-Strafe, negatives Delta)."""
    pen = broken_penalty(player_json["floor"])
    if player_json["marker"]:
        pen += FIRST_PLAYER_MARKER_PENALTY
    return pen


def is_board_final(state):
    """True, wenn an diesem Zustand fuer KEINEN Spieler mehr eine Tiling-
    Platzierung offen ist (empirisch: das `dome_grid` aendert sich danach
    nicht mehr -- siehe Modul-Doku)."""
    return state["phase"] == "tiling" and not state["valid_tiling_rows"] and not state["chippable_tiling_rows"]


def load_final_game_records(filepath):
    """Gruppiert Records je Spiel (kontig, siehe `selfplay_diversity_report.
    py`), gibt je ABGESCHLOSSENEM Spiel den LETZTEN Record zurueck."""
    with open(filepath, "rb") as f:
        data = pickle.load(f)
    games = {}
    order = []
    for r in data:
        gid = r["game_id"]
        if gid not in games:
            games[gid] = []
            order.append(gid)
        games[gid].append(r)
    del data
    out = []
    for gid in order:
        recs = games[gid]
        last = recs[-1]
        if not last.get("completed"):
            continue
        out.append(last)
    return out


def predict_final_score(last_record, wertung_total):
    """Siehe Modul-Doku: max(0, max(0, score + floor_penalty) + wertung_total)
    je Spieler, geklemmte Variante (direkt vergleichbar mit `scores`)."""
    preds = []
    for pi, p in enumerate(last_record["state"]["players"]):
        pen = score_penalty(p)
        pre_end = max(0, p["score"] + pen)
        preds.append(max(0, pre_end + wertung_total[pi]))
    return preds


def analyze(files, model_hint=None):
    ratios_clamped = []      # wertung_total / max(1, final_score_clamped), je Spieler-Spiel
    ratios_unclamped = []    # wertung_total / final_score_unclamped (nur falls > 0, sonst nicht aussagekraeftig)
    wertung_totals = []      # ABSOLUTER Wertungsplatten-Punktetotal (Summe aller 3 aktiven Platten), je Spieler-Spiel --
                             # direkter, nicht durch den (stark verrauschten, teils negativen) Ratio-Nenner verzerrter Wert
    per_tile_scores = defaultdict(list)   # tile_id -> Liste der erzielten Punkte in Spielen, wo sie gewählt war
    per_tile_negative = Counter()         # tile_id -> Anzahl Spiele mit negativem Beitrag
    n_games_used = 0
    n_games_skipped_not_final = 0
    n_predictions_checked = 0
    n_predictions_matched = 0
    prediction_mismatches = []

    for fi, fp in enumerate(files):
        for last in load_final_game_records(fp):
            state = last["state"]
            if not is_board_final(state):
                n_games_skipped_not_final += 1
                continue
            tile_ids = state["scoring_tile_ids"]
            out = json.loads(mosaic_rust.end_scoring_from_state_json(json.dumps(state), tile_ids))
            wertung_total = [out["player_0"]["total"], out["player_1"]["total"]]
            final_clamped = last["scores"]
            final_unclamped = last["scores_unclamped"]

            n_games_used += 1
            for pi in range(2):
                wertung_totals.append(wertung_total[pi])
                denom_c = max(1, final_clamped[pi])
                ratios_clamped.append(wertung_total[pi] / denom_c)
                if final_unclamped[pi] > 0:
                    ratios_unclamped.append(wertung_total[pi] / final_unclamped[pi])
                for d in out[f"player_{pi}"]["details"]:
                    per_tile_scores[d["id"]].append(d["score"])
                    if d["score"] < 0:
                        per_tile_negative[d["id"]] += 1

            preds = predict_final_score(last, wertung_total)
            n_predictions_checked += 1
            if preds == list(final_clamped):
                n_predictions_matched += 1
            elif len(prediction_mismatches) < 10:
                prediction_mismatches.append({
                    "game_id": last["game_id"], "predicted": preds, "actual": final_clamped,
                    "wertung_total": wertung_total, "state_players_score": [p["score"] for p in state["players"]],
                })
        if (fi + 1) % 100 == 0:
            print(f"  {fi+1}/{len(files)} Dateien, {n_games_used} Spiele bisher...")

    def summarize(vals):
        vals = list(vals)
        if not vals:
            return None
        return {
            "n": len(vals), "mean": stats.mean(vals), "median": stats.median(vals),
            "stdev": stats.pstdev(vals) if len(vals) > 1 else 0.0,
            "p10": stats.quantiles(vals, n=10)[0] if len(vals) >= 10 else min(vals),
            "p90": stats.quantiles(vals, n=10)[-1] if len(vals) >= 10 else max(vals),
            "min": min(vals), "max": max(vals),
        }

    per_tile_summary = {}
    for tid in range(8):
        vals = per_tile_scores.get(tid, [])
        per_tile_summary[tid] = {
            "name": TILE_NAMES[tid],
            "n_games_chosen": len(vals),
            "mean_score": stats.mean(vals) if vals else None,
            "median_score": stats.median(vals) if vals else None,
            "share_negative_or_zero": (sum(1 for v in vals if v <= 0) / len(vals)) if vals else None,
            "n_negative": per_tile_negative.get(tid, 0),
        }

    return {
        "n_files": len(files),
        "n_games_used": n_games_used,
        "n_games_skipped_not_final": n_games_skipped_not_final,
        "ratio_clamped_summary": summarize(ratios_clamped),
        "ratio_unclamped_summary": summarize(ratios_unclamped),
        "wertung_total_summary": summarize(wertung_totals),
        "per_tile": per_tile_summary,
        "formula_validation": {
            "n_checked": n_predictions_checked,
            "n_matched": n_predictions_matched,
            "match_rate": n_predictions_matched / n_predictions_checked if n_predictions_checked else None,
            "mismatches_sample": prediction_mismatches,
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-glob", default="data/selfplay_v16_*.pkl")
    ap.add_argument("--limit-files", type=int, default=None, help="None = alle Dateien")
    ap.add_argument("--out", default="evaluations/artifacts/scoring_tile_impact_result.json")
    args = ap.parse_args()

    if not hasattr(mosaic_rust, "end_scoring_from_state_json"):
        raise SystemExit(
            "mosaic_rust.end_scoring_from_state_json fehlt im installierten Wheel -- "
            "Rust-Erweiterung gebaut (engine/src/lib.rs), aber `maturin develop`/Wheel-"
            "Neubau noch nicht durchgefuehrt (siehe evaluations/STATUS.md, "
            "'Wertungsplatten-Diagnose'). Erst nach Wheel-Update lauffaehig."
        )

    files = sorted(glob.glob(args.data_glob))
    if args.limit_files:
        files = files[: args.limit_files]
    if not files:
        raise SystemExit(f"Keine Dateien für Glob {args.data_glob!r} gefunden.")

    print(f"[scoring_tile_impact] {len(files)} Dateien (glob={args.data_glob})")
    result = analyze(files)

    print("\n=== ZUSAMMENFASSUNG ===")
    print(json.dumps({k: v for k, v in result.items() if k != "per_tile"}, indent=2, ensure_ascii=True))
    print("\n-- Je Wertungsplatte (nur Spiele, in denen sie gewaehlt war) --")
    for tid, s in result["per_tile"].items():
        print(f"   {tid} {s['name']:22s}: n={s['n_games_chosen']:5d}  "
              f"mean={s['mean_score']}  median={s['median_score']}")

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\nErgebnis geschrieben nach {args.out}")


if __name__ == "__main__":
    main()
