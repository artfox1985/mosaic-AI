"""
Mosaic-AI — Arena (Rust-Engine)

Round-Robin-Turnier zwischen Heuristik-MCTS-Konfigurationen. Die komplette
Spiel- und Suchlogik läuft in Rust (`mosaic_rust.arena_match`, rayon-parallel).
Ein Wettkämpfer ist hier durch seine Basis-Simulationszahl definiert
(`{"sims": int, "elo": startwert}`). AlphaZero-/Netz-Agenten folgen mit dem
Network-Modus (Phase B).

Fairness: Brett 0 = Agent A, Brett 1 = Agent B; der Startspieler-Vorteil wird
über alternierende Startspieler je Spiel (i % 2) ausgeglichen.
"""
import sys
import time
import json
import random
import itertools

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

MARGIN_CAP       = 15   # Punktedifferenz ab der die Margin-Komponente maximal ist
MAX_WINNER_SCORE = 40   # Winner-Score ab dem die Score-Komponente maximal ist

try:
    import mosaic_rust as _mr
except ImportError as e:  # pragma: no cover
    raise SystemExit(
        "❌ Rust-Modul 'mosaic_rust' nicht gefunden. Bitte bauen:\n"
        "   cd engine && maturin build --release  (dann das Wheel installieren)\n"
        f"(Import-Fehler: {e})"
    )

# 0:0-Strafe (vermiedenswerte Strafleisten-Flut) — Kopie aus agents/neural_net.py,
# damit die Arena unabhängig von agents/ ist.


def compute_win_val(scores, winner, margin_cap=MARGIN_CAP, max_winner_score=MAX_WINNER_SCORE):
    """Abgestufte Siegstärke aus den Endscores (0.1 schwach … 1.0 klar).
    KEINE 0:0-Strafe: in der Arena gibt es kein Unentschieden — bei Punkte-
    gleichstand gewinnt der Startstein-Halter (determine_winner). Ein Marker-Sieg
    ohne Punkte ist ein schwacher Sieg (~0.1), kein bestrafter."""
    margin = abs(scores[0] - scores[1])
    winner_score = scores[winner]
    margin_part = min(0.45, (margin / margin_cap) * 0.45)
    score_part = min(0.45, (winner_score / max_winner_score) * 0.45)
    return min(1.0, 0.1 + margin_part + score_part)


def calculate_elo(rating_a, rating_b, actual_score_a, k=32):
    """Neue Elo-Ratings nach einer Partie."""
    expected_a = 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
    new_rating_a = rating_a + k * (actual_score_a - expected_a)
    new_rating_b = rating_b + k * ((1 - actual_score_a) - (1 - expected_a))
    return round(new_rating_a), round(new_rating_b)


def run_arena(competitors, games_per_matchup=100, threads=0, seed=None, chunk=10):
    """Round-Robin: jeder Wettkämpfer gegen jeden. `competitors` =
    {name: {"sims": int, "elo": int}}. `chunk` = Spiele pro Rust-Aufruf
    (kleiner = häufigere Live-Ausgabe, aber etwas mehr Overhead)."""
    chunk = max(1, chunk)
    print("🏟️ WILLKOMMEN IN DER Mosaic-AI ARENA (Rust) 🏟️")
    names = list(competitors.keys())
    print(f"Kämpfer: {names}")
    print("-" * 50)

    elo = {n: competitors[n].get("elo", 1000) for n in names}
    sims = {n: int(competitors[n]["sims"]) for n in names}
    wins = {n: 0 for n in names}
    wins["ZeroZero"] = 0  # echte 0:0-Spiele (beide ~nichts gescort) = Sauberkeits-Indikator
    penalties = {n: 0 for n in names}
    penalties_per_round = {n: {} for n in names}
    games_played = {n: 0 for n in names}

    matchups = list(itertools.combinations(names, 2))
    base_seed = seed if seed is not None else random.randint(0, 10**9)

    for mi, (A, B) in enumerate(matchups):
        print(f"\n⚔️ NEUES MATCHUP: {A} (Brett 0) vs {B} (Brett 1) "
              f"— {games_per_matchup} Spiele", flush=True)
        t0 = time.time()
        done = 0
        chunk_idx = 0
        a_wins = b_wins = 0   # laufender Matchup-Stand
        # In Chunks spielen, damit die Einzelergebnisse LIVE erscheinen (statt
        # alle erst nach dem kompletten Matchup-Aufruf). Rust spielt jeden Chunk
        # parallel über alle Threads; Elo wird sequentiell über die Reihenfolge
        # gerechnet.
        while done < games_per_matchup:
            n = min(chunk, games_per_matchup - done)
            raw = _mr.arena_match(sims[A], sims[B], n,
                                  seed=base_seed + mi * 1_000_000 + chunk_idx,
                                  num_threads=threads)
            results = json.loads(raw)
            chunk_idx += 1

            for g in results:
                done += 1
                scores = g["scores"]      # [Brett0=A, Brett1=B]
                winner = g["winner"]      # 0 oder 1 (Brett-Index)
                steps  = g["steps"]

                penalties[A] += g["total_floor"][0]
                penalties[B] += g["total_floor"][1]
                for slot, idx in ((A, 0), (B, 1)):
                    for r_idx, pen in enumerate(g["floor_per_round"][idx]):
                        bucket = penalties_per_round[slot].setdefault(r_idx, [0, 0])
                        bucket[0] += pen
                        bucket[1] += 1
                games_played[A] += 1
                games_played[B] += 1

                # Kein Unentschieden: determine_winner liefert 0/1 (Punkte­gleich-
                # stand → Startstein-Halter gewinnt).
                if winner == 0:
                    winner_name, score_a = A, 1.0
                    a_wins += 1
                else:
                    winner_name, score_a = B, 0.0
                    b_wins += 1
                wins[winner_name] += 1
                if scores[0] == 0 and scores[1] == 0:
                    wins["ZeroZero"] += 1   # beide 0 → degeneriertes Spiel (Floor-Flut)

                # Elo mit Siegstärke-skaliertem K. Strength aus Sicht des echten
                # Siegers (inkl. Startstein-Tiebreak bei Gleichstand).
                strength = compute_win_val(scores, winner)
                k = 32 * strength
                elo[A], elo[B] = calculate_elo(elo[A], elo[B], score_a, k=k)

                print(f"  #{done:>3}/{games_per_matchup}: {scores[0]:3d}:{scores[1]:<3d} "
                      f"-> {winner_name:<14} | Züge {steps:3d} | Strength {strength:.3f} "
                      f"| Stand {A} {a_wins}:{b_wins} {B} | Elo {elo[A]}/{elo[B]}",
                      flush=True)

        dur = time.time() - t0
        print(f"  ↳ Matchup fertig: {a_wins}:{b_wins} in {dur:.1f}s "
              f"({games_per_matchup/dur:.1f} Spiele/s)", flush=True)

    # ── Ergebnisse ────────────────────────────────────────────────────────────
    total    = sum(wins[n] for n in names)
    zerozero = wins["ZeroZero"]
    pct      = zerozero / total * 100 if total > 0 else 0

    print("\n" + "=" * 50)
    print("🏆 ARENA ERGEBNISSE 🏆")
    for name in names:
        print(f"Siege {name}: {wins[name]}")
    print(f"0:0 Spiele:    {zerozero} / {total} ({pct:.1f}%)")

    print("\n📉 DURCHSCHNITTLICHE STRAFPUNKTE (BODEN) pro Runde:")
    all_rounds = sorted({r for name in names for r in penalties_per_round[name]})
    if all_rounds:
        for name in names:
            cells = []
            for r in all_rounds:
                bucket = penalties_per_round[name].get(r)
                if bucket and bucket[1] > 0:
                    cells.append(f"{bucket[0] / bucket[1]:6.2f}")
                else:
                    cells.append(f"{'—':>6}")
            total_games = games_played[name]
            overall = (penalties[name] / total_games / len(all_rounds)) if total_games else 0
            print(f" - {name:17s}: " + " ".join(cells) + f"   |  {overall:6.2f}")
        print("   (Werte = Ø Strafpunkte in dieser Runde über alle Spiele)")

    print("\nFINALE ELO RATINGS:")
    for name in sorted(elo, key=elo.get, reverse=True):
        print(f" - {name:15s}: {elo[name]} Elo")


def run_net_arena(model, net_sims=200, heur_sims=60, games=40, stage=1, threads=0,
                  seed=None, chunk=10, c=0.3, c_puct=1.5,
                  net_name=None, heur_name=None):
    """AlphaZero-Netz (ONNX) vs Heuristik-MCTS. Das Netz spielt Brett 0, die
    Heuristik Brett 1; der Startspieler-Vorteil wird über alternierende Start-
    spieler je Spiel (i % 2) ausgeglichen. `stage` 1 = DFS-Blatt (Stufe 1),
    2 = Netz-Value-Blatt (Stufe 2). Spielt in Chunks für LIVE-Ausgabe."""
    import os
    import statistics as _st
    chunk = max(1, chunk)
    dfs_leaf = (stage == 1)
    net_name  = net_name  or f"AlphaZero({os.path.basename(model)})"
    heur_name = heur_name or f"Heuristik(s{heur_sims})"
    leaf = "DFS-Blatt" if dfs_leaf else "Netz-Value-Blatt"

    print("🏟️ Mosaic-AI ARENA — Netz vs Heuristik (Rust) 🏟️")
    print(f"  {net_name} (Brett 0, {net_sims} Sims, Stufe {stage}/{leaf}) "
          f"vs {heur_name} (Brett 1, {heur_sims} Sims) — {games} Spiele")
    print("-" * 50)

    elo  = {net_name: 1000, heur_name: 1000}
    wins = {net_name: 0, heur_name: 0, "ZeroZero": 0}
    floor = {net_name: 0, heur_name: 0}
    net_scores, heur_scores = [], []
    base_seed = seed if seed is not None else random.randint(0, 10**9)

    done = chunk_idx = 0
    n_wins = h_wins = 0
    t0 = time.time()
    while done < games:
        n = min(chunk, games - done)
        raw = _mr.net_arena_match(model, net_sims=net_sims, heur_sims=heur_sims,
                                  n_games=n, seed=base_seed + chunk_idx,
                                  num_threads=threads, c=c, c_puct=c_puct, dfs_leaf=dfs_leaf)
        results = json.loads(raw)
        chunk_idx += 1

        for g in results:
            done += 1
            scores = g["scores"]      # [Netz=Brett0, Heuristik=Brett1]
            winner = g["winner"]      # 0 = Netz, 1 = Heuristik
            steps  = g["steps"]
            net_scores.append(scores[0]); heur_scores.append(scores[1])
            floor[net_name]  += g["total_floor"][0]
            floor[heur_name] += g["total_floor"][1]

            if winner == 0:
                winner_name, score_a = net_name, 1.0
                n_wins += 1
            else:
                winner_name, score_a = heur_name, 0.0
                h_wins += 1
            wins[winner_name] += 1
            if scores[0] == 0 and scores[1] == 0:
                wins["ZeroZero"] += 1

            strength = compute_win_val(scores, winner)
            k = 32 * strength
            elo[net_name], elo[heur_name] = calculate_elo(elo[net_name], elo[heur_name], score_a, k=k)

            print(f"  #{done:>3}/{games}: {scores[0]:3d}:{scores[1]:<3d} -> {winner_name:<24} "
                  f"| Züge {steps:3d} | Strength {strength:.3f} "
                  f"| Stand Netz {n_wins}:{h_wins} Heur | Elo {elo[net_name]}/{elo[heur_name]}",
                  flush=True)

    dur = time.time() - t0
    print("-" * 50)
    print(f"🏆 ERGEBNIS: {net_name} {n_wins}:{h_wins} {heur_name} "
          f"({n_wins/games*100:.0f}% Netz-Siege) in {dur:.1f}s ({games/dur:.1f} Spiele/s)")
    print(f"   Ø Score: {net_name} {_st.mean(net_scores):.1f} | {heur_name} {_st.mean(heur_scores):.1f}")
    print(f"   0:0-Spiele: {wins['ZeroZero']}/{games} ({wins['ZeroZero']/games*100:.1f}%)  "
          f"(Sauberkeits-Indikator)")
    print(f"   Ø Floor-Strafe: {net_name} {floor[net_name]/games:.1f} | {heur_name} {floor[heur_name]/games:.1f}")
    print(f"   Elo: {net_name} {elo[net_name]} | {heur_name} {elo[heur_name]}")


def run_net_vs_net(model_a, model_b, sims_a=200, sims_b=200, stage=1, games=40,
                   threads=0, seed=None, chunk=10, c_puct=1.5, name_a=None, name_b=None):
    """Netz A (Brett 0) vs. Netz B (Brett 1) — Generationen-Vergleich. Start-
    spieler alternieren je Spiel. `stage` 1 = DFS-Blatt, 2 = Netz-Value-Blatt."""
    import os
    import statistics as _st
    chunk = max(1, chunk)
    dfs_leaf = (stage == 1)
    name_a = name_a or f"A({os.path.basename(model_a)})"
    name_b = name_b or f"B({os.path.basename(model_b)})"
    leaf = "DFS-Blatt" if dfs_leaf else "Netz-Value-Blatt"

    print("🏟️ Mosaic-AI ARENA — Netz vs Netz (Rust) 🏟️")
    print(f"  {name_a} (Brett 0, {sims_a} Sims) vs {name_b} (Brett 1, {sims_b} Sims) "
          f"— Stufe {stage}/{leaf} — {games} Spiele")
    print("-" * 50)

    elo  = {name_a: 1000, name_b: 1000}
    wins = {name_a: 0, name_b: 0, "ZeroZero": 0}
    a_scores, b_scores = [], []
    base_seed = seed if seed is not None else random.randint(0, 10**9)

    done = chunk_idx = 0
    a_wins = b_wins = 0
    t0 = time.time()
    while done < games:
        n = min(chunk, games - done)
        raw = _mr.net_vs_net_arena_match(model_a, model_b, sims_a=sims_a, sims_b=sims_b,
                                         n_games=n, seed=base_seed + chunk_idx,
                                         num_threads=threads, c_puct=c_puct, dfs_leaf=dfs_leaf)
        results = json.loads(raw)
        chunk_idx += 1
        for g in results:
            done += 1
            scores = g["scores"]      # [A=Brett0, B=Brett1]
            winner = g["winner"]      # 0 = A, 1 = B
            steps  = g["steps"]
            a_scores.append(scores[0]); b_scores.append(scores[1])
            if winner == 0:
                winner_name, score_a = name_a, 1.0; a_wins += 1
            else:
                winner_name, score_a = name_b, 0.0; b_wins += 1
            wins[winner_name] += 1
            if scores[0] == 0 and scores[1] == 0:
                wins["ZeroZero"] += 1
            strength = compute_win_val(scores, winner)
            elo[name_a], elo[name_b] = calculate_elo(elo[name_a], elo[name_b], score_a, k=32 * strength)
            print(f"  #{done:>3}/{games}: {scores[0]:3d}:{scores[1]:<3d} -> {winner_name:<22} "
                  f"| Züge {steps:3d} | Strength {strength:.3f} "
                  f"| Stand {name_a} {a_wins}:{b_wins} {name_b} | Elo {elo[name_a]}/{elo[name_b]}",
                  flush=True)

    dur = time.time() - t0
    print("-" * 50)
    print(f"🏆 ERGEBNIS: {name_a} {a_wins}:{b_wins} {name_b} "
          f"({a_wins/games*100:.0f}% A-Siege) in {dur:.1f}s ({games/dur:.1f} Spiele/s)")
    print(f"   Ø Score: {name_a} {_st.mean(a_scores):.1f} | {name_b} {_st.mean(b_scores):.1f}")
    print(f"   0:0-Spiele: {wins['ZeroZero']}/{games} ({wins['ZeroZero']/games*100:.1f}%)")
    print(f"   Elo: {name_a} {elo[name_a]} | {name_b} {elo[name_b]}")


if __name__ == "__main__":
    # ── Teilnehmer hier manuell einstellen ───────────────────────────────────
    # AlphaZero-Netz (ONNX, Brett 0) vs Heuristik-MCTS (Brett 1). Werte anpassen.
    NET_MODEL = "models/alphazero_v7.onnx"   # Pfad zum ONNX-Netz
    NET_MODEL_PRE = "models/alphazero_v4.onnx"
    NET_SIMS  = 200                            # Basis-Sims des Netzes
    STAGE     = 1                              # 1 = DFS-Blatt, 2 = Netz-Value-Blatt
    HEUR_SIMS = NET_SIMS #60                             # Basis-Sims der Heuristik
    GAMES     = 100
    run_net_arena(NET_MODEL, net_sims=NET_SIMS, heur_sims=HEUR_SIMS, net_name = "v7",
                  games=GAMES, stage=STAGE, threads=0)
    #run_net_vs_net(NET_MODEL, NET_MODEL_PRE, sims_a=NET_SIMS, sims_b=NET_SIMS, stage=STAGE, games=GAMES,
    #               threads=0, seed=None, chunk=10, c_puct=1.5, name_a="v7", name_b="v4")

    # ── Alternativ: reines Heuristik-Round-Robin (auskommentiert) ────────────
    # competitors = {
    #     "MCTS s50":  {"sims": 50,  "elo": 1000},
    #     "MCTS s100": {"sims": 100, "elo": 1000},
    #     "MCTS s200": {"sims": 200, "elo": 1000},
    # }
    # run_arena(competitors, games_per_matchup=100, threads=0)
