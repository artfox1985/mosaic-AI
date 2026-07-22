"""
Mosaic-AI -- Self-Play-Diversitaets-Monitoring (Task #67)
==========================================================

Reine Lese-Analyse ueber vorhandene Self-Play-Pickles (data/selfplay_netcq_*.pkl
und den heuristischen Referenz-Korpus data/archive_domefactB_preRuleFix/).
Startet KEIN Self-Play, KEINE Arena, KEIN Training -- nur pickle.load + Auszaehlen.

Fragestellung: Kollabiert netzgefuehrtes Self-Play (v10 vs. sich selbst) in
immer gleiche Spielverlaeufe (Eroeffnungen, Laengen, Endstaende)?

Methodik "gespielte Aktion" ohne Engine-Re-Simulation
------------------------------------------------------
Jeder Record enthaelt state['log'] (kumulative, für Menschen lesbare Zugliste).
Zwischen Record i und i+1 waechst das Log um genau die Zeile(n), die die im
Schritt i getroffene Entscheidung beschreiben (mehrere Log-Zeilen pro Record-
Uebergang treten bei zusammengesetzten Zuegen auf, z.B. Stein-Zug + Mond-Stapel-
Update). Diese Log-Diffs sind exakte, spielerlesbare Beschreibungen der
tatsaechlich gespielten Aktion -- keine Naeherung ueber argmax(policy) noetig
(die waere bei Sampling-Temperatur > 0 ohnehin nicht zwangslaeufig die gespielte
Aktion). Die ersten 3 Log-Diffs eines Spiels (nach der Start-Zeile "Spiel
gestartet...") bilden die Eroeffnungssignatur: typischerweise Start-Dom 1,
Start-Dom 2, erster Stein/Mond-Zug.

Speicher-Disziplin: Dateien werden einzeln geladen, sofort in kompakte
Kennzahlen (Skalare/kurze Strings) verdichtet und dann verworfen (del + Schleife
laesst die grossen Record-Listen nicht liegen).
"""
import argparse
import glob
import math
import os
import pickle
import statistics
from collections import Counter, defaultdict


def load_games(filepath):
    """Laedt eine Pickle-Datei und gruppiert die Records nach game_id (Records
    liegen je Spiel garantiert kontig hintereinander -- siehe Exploration)."""
    with open(filepath, "rb") as f:
        data = pickle.load(f)
    games = []
    cur_id = None
    cur = []
    for r in data:
        if r["game_id"] != cur_id:
            if cur:
                games.append(cur)
            cur = []
            cur_id = r["game_id"]
        cur.append(r)
    if cur:
        games.append(cur)
    del data
    return games


def opening_events(records, n=3):
    """Erste n Log-Diff-Ereignisse eines Spiels (siehe Modulkopf)."""
    events = []
    prev_log_len = None
    for r in records:
        log = r["state"].get("log") or []
        if prev_log_len is None:
            prev_log_len = len(log)
            continue
        if len(log) > prev_log_len:
            new_lines = log[prev_log_len:]
            events.append(" | ".join(l.strip() for l in new_lines))
            prev_log_len = len(log)
        if len(events) >= n:
            break
    return events


def summarize_game(records):
    first, last = records[0], records[-1]
    scores = last.get("scores") or [None, None]
    return {
        "n_records": len(records),
        "starting_player": first["state"].get("current_player"),
        "winner": last.get("winner"),
        "score_p0": scores[0],
        "score_p1": scores[1],
        "opening": opening_events(records, n=3),
    }


def shannon_entropy(counter):
    total = sum(counter.values())
    if total == 0:
        return 0.0
    h = 0.0
    for c in counter.values():
        p = c / total
        h -= p * math.log2(p)
    return h


def analyze_corpus(filepaths, label, verbose=True):
    game_lengths = []
    scores_p0, scores_p1 = [], []
    winners = []
    starting_players = []
    sig1, sig2, sig3 = Counter(), Counter(), Counter()
    n_games = 0

    for i, fp in enumerate(filepaths):
        games = load_games(fp)
        for recs in games:
            s = summarize_game(recs)
            n_games += 1
            game_lengths.append(s["n_records"])
            if s["score_p0"] is not None and s["score_p1"] is not None:
                scores_p0.append(s["score_p0"])
                scores_p1.append(s["score_p1"])
            if s["winner"] is not None:
                winners.append(s["winner"])
            if s["starting_player"] is not None:
                starting_players.append((s["starting_player"], s["winner"]))
            op = s["opening"]
            if len(op) >= 1:
                sig1[tuple(op[:1])] += 1
            if len(op) >= 2:
                sig2[tuple(op[:2])] += 1
            if len(op) >= 3:
                sig3[tuple(op[:3])] += 1
        del games
        if verbose and (i + 1) % 25 == 0:
            print(f"  [{label}] {i+1}/{len(filepaths)} Dateien, {n_games} Spiele bisher...")

    return {
        "label": label,
        "n_files": len(filepaths),
        "n_games": n_games,
        "game_lengths": game_lengths,
        "scores_p0": scores_p0,
        "scores_p1": scores_p1,
        "winners": winners,
        "starting_players": starting_players,
        "sig1": sig1,
        "sig2": sig2,
        "sig3": sig3,
    }


def _hist_bounds(vals, n_bins=5):
    if not vals:
        return []
    lo, hi = min(vals), max(vals)
    if lo == hi:
        return [(lo, hi, len(vals))]
    width = (hi - lo) / n_bins
    bins = [0] * n_bins
    for v in vals:
        idx = min(n_bins - 1, int((v - lo) / width))
        bins[idx] += 1
    return [(round(lo + i * width, 1), round(lo + (i + 1) * width, 1), bins[i]) for i in range(n_bins)]


def report(result):
    label = result["label"]
    n_games = result["n_games"]
    gl = result["game_lengths"]
    print(f"\n=== {label} (n_games={n_games}, n_files={result['n_files']}) ===")

    print(f"-- Spiellaenge (Records/Spiel) --")
    if gl:
        print(f"   mean={statistics.mean(gl):.1f}  std={statistics.pstdev(gl):.1f}  "
              f"min={min(gl)}  max={max(gl)}")
        print(f"   Histogramm: {_hist_bounds(gl)}")

    print(f"-- Eroeffnungs-Diversitaet --")
    for k, sig in (("1-Zug", result["sig1"]), ("2-Zug", result["sig2"]), ("3-Zug", result["sig3"])):
        total = sum(sig.values())
        if total == 0:
            print(f"   {k}: keine Daten")
            continue
        uniq = len(sig)
        h = shannon_entropy(sig)
        h_max = math.log2(uniq) if uniq > 1 else 0.0
        top_count = sig.most_common(1)[0][1]
        top_share = top_count / total
        print(f"   {k}: unique={uniq}/{total}  entropy={h:.2f} bits (max={h_max:.2f}, "
              f"norm={h/h_max if h_max>0 else 1.0:.2f})  top_share={top_share:.1%}")

    print(f"-- Endscore-Verteilung --")
    sp0, sp1 = result["scores_p0"], result["scores_p1"]
    if sp0 and sp1:
        print(f"   Spieler0: mean={statistics.mean(sp0):.1f} std={statistics.pstdev(sp0):.1f}")
        print(f"   Spieler1: mean={statistics.mean(sp1):.1f} std={statistics.pstdev(sp1):.1f}")
        draws = sum(1 for a, b in zip(sp0, sp1) if a == b)
        print(f"   Unentschieden (score0==score1): {draws}/{len(sp0)} = {draws/len(sp0):.1%}")

    winners = result["winners"]
    if winners:
        wc = Counter(winners)
        total_w = sum(wc.values())
        print(f"-- Sieger-Verteilung Brett 0 vs 1 (roh, Sitz-Bias) --")
        print(f"   Brett0: {wc.get(0,0)}/{total_w} = {wc.get(0,0)/total_w:.1%}  |  "
              f"Brett1: {wc.get(1,0)}/{total_w} = {wc.get(1,0)/total_w:.1%}")

    sps = result["starting_players"]
    if sps:
        start_wins = sum(1 for start, win in sps if start == win)
        print(f"-- First-Player-Advantage (Startspieler gewinnt) --")
        print(f"   {start_wins}/{len(sps)} = {start_wins/len(sps):.1%} "
              f"(50% = kein Vorteil)")


def judge(netcq, ref):
    """Grobes Ampel-Urteil: kollabiert / grenzwertig / gesund, basierend auf
    3-Zug-Eroeffnungs-Entropie relativ zur Spielanzahl und top_share."""
    sig3 = netcq["sig3"]
    total = sum(sig3.values())
    if total == 0:
        return "KEINE DATEN"
    uniq = len(sig3)
    h = shannon_entropy(sig3)
    h_max = math.log2(uniq) if uniq > 1 else 0.0
    norm_h = h / h_max if h_max > 0 else 1.0
    top_share = sig3.most_common(1)[0][1] / total
    uniq_ratio = uniq / total

    ref_sig3 = ref["sig3"]
    ref_total = sum(ref_sig3.values())
    ref_uniq_ratio = (len(ref_sig3) / ref_total) if ref_total else None
    ref_top_share = (ref_sig3.most_common(1)[0][1] / ref_total) if ref_total else None

    print(f"\n=== URTEIL ===")
    print(f"netcq: unique_ratio={uniq_ratio:.2f} norm_entropy={norm_h:.2f} top_share={top_share:.1%}")
    if ref_total:
        print(f"ref (domefactB): unique_ratio={ref_uniq_ratio:.2f} top_share={ref_top_share:.1%}")

    if uniq_ratio < 0.05 or top_share > 0.5 or norm_h < 0.5:
        verdict = "KOLLABIERT"
    elif uniq_ratio < 0.3 or top_share > 0.2 or norm_h < 0.75:
        verdict = "GRENZWERTIG"
    else:
        verdict = "GESUND"
    print(f"Verdikt: {verdict}")
    return verdict


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--netcq-glob", default="selfplay_netcq_*.pkl")
    ap.add_argument("--netcq-limit", type=int, default=None, help="None = alle Dateien")
    ap.add_argument("--ref-dir", default="data/archive_domefactB_preRuleFix")
    ap.add_argument("--ref-sample", type=int, default=30)
    args = ap.parse_args()

    netcq_files = sorted(glob.glob(os.path.join(args.data_dir, args.netcq_glob)))
    if args.netcq_limit:
        netcq_files = netcq_files[: args.netcq_limit]

    ref_all = sorted(glob.glob(os.path.join(args.ref_dir, "*.pkl")))
    if args.ref_sample and len(ref_all) > args.ref_sample:
        step = len(ref_all) / args.ref_sample
        ref_files = [ref_all[int(i * step)] for i in range(args.ref_sample)]
    else:
        ref_files = ref_all

    print(f"netcq: {len(netcq_files)} Dateien | ref: {len(ref_files)} Dateien (von {len(ref_all)})")

    netcq_result = analyze_corpus(netcq_files, "netcq (v10 self-play)")
    ref_result = analyze_corpus(ref_files, "domefactB (heuristik, preRuleFix)")

    report(netcq_result)
    report(ref_result)
    judge(netcq_result, ref_result)


if __name__ == "__main__":
    main()
