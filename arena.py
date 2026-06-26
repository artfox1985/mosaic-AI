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

from config import MARGIN_CAP, MAX_WINNER_SCORE

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
    wins["ZeroZero"] = 0  # Punktegleichstand (Sieg per Startstein) — nur als Info
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
                if scores[0] == scores[1]:
                    wins["ZeroZero"] += 1   # Punktegleichstand (per Startstein entschieden)

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


if __name__ == "__main__":
    # Wettkämpfer = Heuristik-MCTS-Konfigurationen (durch Basis-Sims definiert).
    competitors = {
        "MCTS s50":  {"sims": 50,  "elo": 1000},
        "MCTS s100": {"sims": 100, "elo": 1000},
        "MCTS s200": {"sims": 200, "elo": 1000},
    }
    run_arena(competitors, games_per_matchup=100, threads=0)
