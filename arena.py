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
import math
import random
import itertools

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    import mosaic_rust as _mr
except ImportError as e:  # pragma: no cover
    raise SystemExit(
        "❌ Rust-Modul 'mosaic_rust' nicht gefunden. Bitte bauen:\n"
        "   cd engine && maturin build --release  (dann das Wheel installieren)\n"
        f"(Import-Fehler: {e})"
    )


def sprt_bounds(alpha=0.05, beta=0.10):
    """Abbruchschranken fuer den truncated SPRT (Wald 1945). H0: Agenten
    gleich stark (Δelo<=0), H1: A signifikant staerker (Δelo>=100, das
    entspricht p1=0.64 Gewinnchance, siehe sprt_llr_delta). `alpha` = Risiko
    fuer ein Falsch-Positiv (H1 angenommen obwohl H0 wahr), `beta` = Risiko,
    einen echten Fortschritt zu uebersehen (H0 angenommen obwohl H1 wahr).
    Untere Schranke A = ln(beta/(1-alpha)), obere Schranke B = ln((1-beta)/alpha)."""
    A = math.log(beta / (1 - alpha))
    B = math.log((1 - beta) / alpha)
    return A, B


def sprt_llr_delta(a_won, p0=0.5, p1=0.64):
    """LLR-Zuwachs fuer EIN Spiel (Log-Likelihood-Ratio H1 vs. H0). p0 =
    Gewinnwahrscheinlichkeit von A unter H0 (gleich stark), p1 = unter H1
    (A signifikant staerker). Aufsummiert ueber alle Spiele ergibt das die
    laufende SPRT-Teststatistik, die nach jedem Spiel gegen die Schranken aus
    sprt_bounds() geprueft wird."""
    if a_won:
        return math.log(p1 / p0)
    return math.log((1 - p1) / (1 - p0))


def smoothed_win_prob_and_elo(wins_a, n, p1=0.64):
    """NUR fuers Live-Monitoring/Logging (nicht fuer die SPRT-Abbruch-
    entscheidung selbst, die exakt auf den Rohdaten operieren muss):
    Laplace-geglaettete Gewinnwahrscheinlichkeit (ein fiktiver Sieg + eine
    fiktive Niederlage dazugerechnet), damit die ersten 5-10 Spiele nicht zu
    extremen Elo-Ausschlaegen fuehren, plus die daraus abgeleitete
    Elo-Differenz (klassische Elo-Umkehrformel)."""
    p_smooth = (wins_a + 1) / (n + 2)
    delta_elo = -400 * math.log10(1 / p_smooth - 1)
    return p_smooth, delta_elo


def calculate_elo(rating_a, rating_b, actual_score_a, k=32):
    """Neue Elo-Ratings nach einer Partie -- rein sieg-/niederlage-basiert
    (actual_score_a ist 1.0 oder 0.0), kein Siegstärke-Multiplikator mehr:
    das laesst den Elo-Wert direkt mit der Gewinnwahrscheinlichkeit
    korrelieren, statt zusaetzlich von der Punktemarge beeinflusst zu sein."""
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

                elo[A], elo[B] = calculate_elo(elo[A], elo[B], score_a)

                print(f"  #{done:>3}/{games_per_matchup}: {scores[0]:3d}:{scores[1]:<3d} "
                      f"-> {winner_name:<14} | Züge {steps:3d} "
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


def run_net_arena(model, net_sims=200, heur_sims=60, games=100, threads=0,
                  seed=None, chunk=10, c=0.3, c_puct=1.5,
                  net_name=None, heur_name=None, early_stop=True,
                  sprt_alpha=0.05, sprt_beta=0.10, sprt_p1=0.64):
    """AlphaZero-Netz (ONNX) vs Heuristik-MCTS. Das Netz spielt Brett 0, die
    Heuristik Brett 1; der Startspieler-Vorteil wird über alternierende Start-
    spieler je Spiel (i % 2) ausgeglichen. Blattbewertung ist immer der exakte
    DFS-Solver (kein Value-Head mehr). Spielt in Chunks für LIVE-Ausgabe.
    `early_stop`: zwei parallele truncated SPRTs (Wald) -- einer testet
    "Netz signifikant staerker" (H1a), einer "Heuristik signifikant staerker"
    (H1b), je p1=0.64 (~+100 Elo). Bricht ab, sobald EINER seine obere
    Schranke reisst (dieser gewinnt); "Gleich stark" gilt erst, wenn BEIDE
    ihre H1 verwerfen (untere Schranke) oder Spiel `games` ohne Entscheidung
    erreicht wird -- ein einzelner verworfener Test heisst nur "diese Seite
    nicht bewiesen besser", NICHT automatisch Parität (siehe sprt_bounds)."""
    import os
    import statistics as _st
    chunk = max(1, chunk)
    net_name  = net_name  or f"AlphaZero({os.path.basename(model)})"
    heur_name = heur_name or f"Heuristik(s{heur_sims})"
    sprt_lower, sprt_upper = sprt_bounds(sprt_alpha, sprt_beta)

    print("🏟️ Mosaic-AI ARENA — Netz vs Heuristik (Rust) 🏟️")
    print(f"  {net_name} (Brett 0, {net_sims} Sims) "
          f"vs {heur_name} (Brett 1, {heur_sims} Sims) — {games} Spiele"
          + (f"  [SPRT p1={sprt_p1}, α={sprt_alpha}, β={sprt_beta}]" if early_stop else ""))
    print("-" * 50)

    elo  = {net_name: 1000, heur_name: 1000}
    wins = {net_name: 0, heur_name: 0, "ZeroZero": 0}
    floor = {net_name: 0, heur_name: 0}
    net_scores, heur_scores = [], []
    base_seed = seed if seed is not None else random.randint(0, 10**9)

    done = chunk_idx = 0
    n_wins = h_wins = 0
    llr_net = llr_heur = 0.0
    net_out = heur_out = False   # True = diese Seite hat ihre H1 (signifikant staerker) verworfen
    verdict = None   # None=laeuft noch, net_name/heur_name=Sieger, "PARITY"=Gleich stark
    t0 = time.time()
    while done < games:
        n = min(chunk, games - done)
        raw = _mr.net_arena_match(model, net_sims=net_sims, heur_sims=heur_sims,
                                  n_games=n, seed=base_seed + chunk_idx,
                                  num_threads=threads, c=c, c_puct=c_puct)
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

            net_won = (winner == 0)
            if net_won:
                winner_name, score_a = net_name, 1.0
                n_wins += 1
            else:
                winner_name, score_a = heur_name, 0.0
                h_wins += 1
            wins[winner_name] += 1
            if scores[0] == 0 and scores[1] == 0:
                wins["ZeroZero"] += 1

            elo[net_name], elo[heur_name] = calculate_elo(elo[net_name], elo[heur_name], score_a)
            _, delta_elo_smooth = smoothed_win_prob_and_elo(n_wins, done, p1=sprt_p1)

            if early_stop:
                if not net_out:
                    llr_net += sprt_llr_delta(net_won, p1=sprt_p1)
                    if llr_net >= sprt_upper:
                        verdict = net_name
                    elif llr_net <= sprt_lower:
                        net_out = True
                if verdict is None and not heur_out:
                    llr_heur += sprt_llr_delta(not net_won, p1=sprt_p1)
                    if llr_heur >= sprt_upper:
                        verdict = heur_name
                    elif llr_heur <= sprt_lower:
                        heur_out = True
                if verdict is None and net_out and heur_out:
                    verdict = "PARITY"

            print(f"  #{done:>3}/{games}: {scores[0]:3d}:{scores[1]:<3d} -> {winner_name:<24} "
                  f"| Züge {steps:3d} | LLR_Netz {llr_net:+.2f} | LLR_Heur {llr_heur:+.2f} "
                  f"| ΔElo~{delta_elo_smooth:+.0f} | Stand Netz {n_wins}:{h_wins} Heur "
                  f"| Elo {elo[net_name]}/{elo[heur_name]}",
                  flush=True)

            if verdict:
                label = (f"{verdict} signifikant staerker" if verdict != "PARITY"
                         else "Gleich stark (beide Seiten nicht signifikant staerker)")
                print(f"  ⏹️  SPRT-Entscheid nach {done} Spielen: {label} "
                      f"(LLR_Netz={llr_net:+.2f}, LLR_Heur={llr_heur:+.2f}).")
                break
        if verdict:
            break

    if early_stop and verdict is None:
        verdict = "PARITY"
        print(f"  ⏹️  Ressourcenlimit erreicht (Spiel {games}) ohne SPRT-Entscheidung -> Gleich stark "
              f"(LLR_Netz={llr_net:+.2f}, LLR_Heur={llr_heur:+.2f}).")

    dur = time.time() - t0
    print("-" * 50)
    print(f"🏆 ERGEBNIS: {net_name} {n_wins}:{h_wins} {heur_name} "
          f"({n_wins/done*100:.0f}% Netz-Siege) in {dur:.1f}s ({done/dur:.1f} Spiele/s)"
          + (f"  [vorzeitig nach {done}/{games} Spielen]" if early_stop and done < games else ""))
    print(f"   Ø Score: {net_name} {_st.mean(net_scores):.1f} | {heur_name} {_st.mean(heur_scores):.1f}")
    print(f"   0:0-Spiele: {wins['ZeroZero']}/{done} ({wins['ZeroZero']/done*100:.1f}%)  "
          f"(Sauberkeits-Indikator)")
    print(f"   Ø Floor-Strafe: {net_name} {floor[net_name]/done:.1f} | {heur_name} {floor[heur_name]/done:.1f}")
    print(f"   Elo: {net_name} {elo[net_name]} | {heur_name} {elo[heur_name]}")


def run_net_vs_net(model_a, model_b, sims_a=200, sims_b=200, games=100,
                   threads=0, seed=None, chunk=10, c_puct=1.5, c_puct_a=None, c_puct_b=None,
                   name_a=None, name_b=None, early_stop=True,
                   sprt_alpha=0.05, sprt_beta=0.10, sprt_p1=0.64):
    """Netz A (Brett 0) vs. Netz B (Brett 1) — Generationen-Vergleich. Start-
    spieler alternieren je Spiel. Blattbewertung ist immer der exakte
    DFS-Solver (kein Value-Head mehr). `c_puct_a`/`c_puct_b` überschreiben
    `c_puct` je Brett (z.B. um denselben Modell-Stand mit unterschiedlichem
    c_puct gegeneinander antreten zu lassen).
    `early_stop`: zwei parallele truncated SPRTs (Wald) -- einer testet
    "A signifikant staerker" (H1a), einer "B signifikant staerker" (H1b),
    je p1=0.64 (~+100 Elo). Bricht ab, sobald EINER seine obere Schranke
    reisst (dieser gewinnt); "Gleich stark" gilt erst, wenn BEIDE ihre H1
    verwerfen (untere Schranke) oder Spiel `games` ohne Entscheidung
    erreicht wird -- ein einzelner verworfener Test heisst nur "diese Seite
    nicht bewiesen besser", NICHT automatisch Parität (siehe sprt_bounds)."""
    import os
    import statistics as _st
    chunk = max(1, chunk)
    cp_a = c_puct_a if c_puct_a is not None else c_puct
    cp_b = c_puct_b if c_puct_b is not None else c_puct
    name_a = name_a or f"A({os.path.basename(model_a)})"
    name_b = name_b or f"B({os.path.basename(model_b)})"
    sprt_lower, sprt_upper = sprt_bounds(sprt_alpha, sprt_beta)

    print("🏟️ Mosaic-AI ARENA — Netz vs Netz (Rust) 🏟️")
    print(f"  {name_a} (Brett 0, {sims_a} Sims, c_puct={cp_a}) vs "
          f"{name_b} (Brett 1, {sims_b} Sims, c_puct={cp_b}) "
          f"— {games} Spiele"
          + (f"  [SPRT p1={sprt_p1}, α={sprt_alpha}, β={sprt_beta}]" if early_stop else ""))
    print("-" * 50)

    elo  = {name_a: 1000, name_b: 1000}
    wins = {name_a: 0, name_b: 0, "ZeroZero": 0}
    a_scores, b_scores = [], []
    base_seed = seed if seed is not None else random.randint(0, 10**9)

    done = chunk_idx = 0
    a_wins = b_wins = 0
    llr_a = llr_b = 0.0
    a_out = b_out = False   # True = diese Seite hat ihre H1 (signifikant staerker) verworfen
    verdict = None   # None=laeuft noch, name_a/name_b=Sieger, "PARITY"=Gleich stark
    t0 = time.time()
    while done < games:
        n = min(chunk, games - done)
        raw = _mr.net_vs_net_arena_match(model_a, model_b, sims_a=sims_a, sims_b=sims_b,
                                         n_games=n, seed=base_seed + chunk_idx,
                                         num_threads=threads, c_puct_a=cp_a, c_puct_b=cp_b)
        results = json.loads(raw)
        chunk_idx += 1
        for g in results:
            done += 1
            scores = g["scores"]      # [A=Brett0, B=Brett1]
            winner = g["winner"]      # 0 = A, 1 = B
            steps  = g["steps"]
            a_scores.append(scores[0]); b_scores.append(scores[1])
            a_won = (winner == 0)
            if a_won:
                winner_name, score_a = name_a, 1.0; a_wins += 1
            else:
                winner_name, score_a = name_b, 0.0; b_wins += 1
            wins[winner_name] += 1
            if scores[0] == 0 and scores[1] == 0:
                wins["ZeroZero"] += 1
            elo[name_a], elo[name_b] = calculate_elo(elo[name_a], elo[name_b], score_a)
            _, delta_elo_smooth = smoothed_win_prob_and_elo(a_wins, done, p1=sprt_p1)

            if early_stop:
                if not a_out:
                    llr_a += sprt_llr_delta(a_won, p1=sprt_p1)
                    if llr_a >= sprt_upper:
                        verdict = name_a
                    elif llr_a <= sprt_lower:
                        a_out = True
                if verdict is None and not b_out:
                    llr_b += sprt_llr_delta(not a_won, p1=sprt_p1)
                    if llr_b >= sprt_upper:
                        verdict = name_b
                    elif llr_b <= sprt_lower:
                        b_out = True
                if verdict is None and a_out and b_out:
                    verdict = "PARITY"

            print(f"  #{done:>3}/{games}: {scores[0]:3d}:{scores[1]:<3d} -> {winner_name:<22} "
                  f"| Züge {steps:3d} | LLR_A {llr_a:+.2f} | LLR_B {llr_b:+.2f} "
                  f"| ΔElo~{delta_elo_smooth:+.0f} | Stand {name_a} {a_wins}:{b_wins} {name_b} "
                  f"| Elo {elo[name_a]}/{elo[name_b]}",
                  flush=True)

            if verdict:
                label = (f"{verdict} signifikant staerker" if verdict != "PARITY"
                         else "Gleich stark (beide Seiten nicht signifikant staerker)")
                print(f"  ⏹️  SPRT-Entscheid nach {done} Spielen: {label} "
                      f"(LLR_A={llr_a:+.2f}, LLR_B={llr_b:+.2f}).")
                break
        if verdict:
            break

    if early_stop and verdict is None:
        verdict = "PARITY"
        print(f"  ⏹️  Ressourcenlimit erreicht (Spiel {games}) ohne SPRT-Entscheidung -> Gleich stark "
              f"(LLR_A={llr_a:+.2f}, LLR_B={llr_b:+.2f}).")

    dur = time.time() - t0
    print("-" * 50)
    print(f"🏆 ERGEBNIS: {name_a} {a_wins}:{b_wins} {name_b} "
          f"({a_wins/done*100:.0f}% A-Siege) in {dur:.1f}s ({done/dur:.1f} Spiele/s)"
          + (f"  [vorzeitig nach {done}/{games} Spielen]" if early_stop and done < games else ""))
    print(f"   Ø Score: {name_a} {_st.mean(a_scores):.1f} | {name_b} {_st.mean(b_scores):.1f}")
    print(f"   0:0-Spiele: {wins['ZeroZero']}/{done} ({wins['ZeroZero']/done*100:.1f}%)")
    print(f"   Elo: {name_a} {elo[name_a]} | {name_b} {elo[name_b]}")


def run_stage3_vs_stage1(model, sims1=200, stage3_shortlist_sims=100, stage3_rollout_sims=50,
                         top_k=2, n_reps=3, horizon_rounds=2, stage3_max_round=2,
                         alphabeta_depth=2, alphabeta_node_budget=100, games=50,
                         threads=0, seed=None, chunk=5, c_puct=1.5, name_a="Stufe3", name_b="Stufe1",
                         early_stop=True, sprt_alpha=0.05, sprt_beta=0.10, sprt_p1=0.64):
    """Stufe 3 (Brett 0: bis einschliesslich Runde `stage3_max_round` per
    Top-K-Kandidaten + gemittelten Rollouts über den Beutel-Zufall
    entschieden, begrenzt auf `horizon_rounds` Runden statt Spielende; danach
    faellt es auf reine Stufe 1 zurueck -- ein Besuchsanteil-/Q-Wert-
    basiertes "nur bei knappen Entscheidungen"-Kriterium wurde gemessen und
    verworfen, siehe evaluations/stage2_investigation.md, Stufe-3-
    Kalibrierung). Die Rollout-Fortsetzung selbst laeuft jetzt per Alpha-Beta-
    Minimax (Netz-Policy-Zugsortierung, `alphabeta_depth` Plies,
    `alphabeta_node_budget` Sicherheitsnetz) statt der vollen PUCT-Suche --
    guenstiger, weil unser DFS-Blatt exakt ist (siehe Referenz
    domwil.co.uk/posts/azul-ai). Vs. Stufe 1 (Brett 1: reine Netz-PUCT +
    DFS-Blatt), dasselbe Netz. Startspieler alternieren je Spiel.
    `early_stop`: dieselbe duale SPRT wie `run_net_vs_net` (siehe dort für
    die genaue Logik)."""
    import os
    import statistics as _st
    chunk = max(1, chunk)
    name_a = name_a or f"Stufe3({os.path.basename(model)})"
    name_b = name_b or f"Stufe1({os.path.basename(model)})"
    sprt_lower, sprt_upper = sprt_bounds(sprt_alpha, sprt_beta)

    print("🏟️ Mosaic-AI ARENA — Stufe 3 (Rollouts) vs Stufe 1 (Rust) 🏟️")
    print(f"  {name_a} (Brett 0, nur Runde 1-{stage3_max_round}, Top-{top_k}, {n_reps} Rollouts, "
          f"Horizont {horizon_rounds} Runden, Shortlist-Sims {stage3_shortlist_sims}, "
          f"Rollout-Sims {stage3_rollout_sims}) vs "
          f"{name_b} (Brett 1, {sims1} Sims, DFS-Blatt) — {games} Spiele"
          + (f"  [SPRT p1={sprt_p1}, α={sprt_alpha}, β={sprt_beta}]" if early_stop else ""))
    print("-" * 50)

    elo  = {name_a: 1000, name_b: 1000}
    wins = {name_a: 0, name_b: 0, "ZeroZero": 0}
    a_scores, b_scores = [], []
    base_seed = seed if seed is not None else random.randint(0, 10**9)

    done = chunk_idx = 0
    a_wins = b_wins = 0
    llr_a = llr_b = 0.0
    a_out = b_out = False
    verdict = None
    total_decisions = total_triggered = 0
    t0 = time.time()
    while done < games:
        n = min(chunk, games - done)
        raw = _mr.stage3_vs_stage1_arena_match(
            model_path=model, n_games=n, sims1=sims1,
            stage3_shortlist_sims=stage3_shortlist_sims, stage3_rollout_sims=stage3_rollout_sims,
            c_puct=c_puct, top_k=top_k, n_reps=n_reps, horizon_rounds=horizon_rounds,
            stage3_max_round=stage3_max_round, alphabeta_depth=alphabeta_depth,
            alphabeta_node_budget=alphabeta_node_budget, seed=base_seed + chunk_idx, num_threads=threads,
        )
        results = json.loads(raw)
        chunk_idx += 1
        diag = None
        for g in results:
            if g.get("stage3_diagnostics"):
                diag = g
                continue
            done += 1
            scores = g["scores"]      # [Stufe3=Brett0, Stufe1=Brett1]
            winner = g["winner"]      # 0 = Stufe3, 1 = Stufe1
            steps  = g["steps"]
            a_scores.append(scores[0]); b_scores.append(scores[1])
            a_won = (winner == 0)
            if a_won:
                winner_name, score_a = name_a, 1.0; a_wins += 1
            else:
                winner_name, score_a = name_b, 0.0; b_wins += 1
            wins[winner_name] += 1
            if scores[0] == 0 and scores[1] == 0:
                wins["ZeroZero"] += 1
            elo[name_a], elo[name_b] = calculate_elo(elo[name_a], elo[name_b], score_a)
            _, delta_elo_smooth = smoothed_win_prob_and_elo(a_wins, done, p1=sprt_p1)

            if early_stop:
                if not a_out:
                    llr_a += sprt_llr_delta(a_won, p1=sprt_p1)
                    if llr_a >= sprt_upper:
                        verdict = name_a
                    elif llr_a <= sprt_lower:
                        a_out = True
                if verdict is None and not b_out:
                    llr_b += sprt_llr_delta(not a_won, p1=sprt_p1)
                    if llr_b >= sprt_upper:
                        verdict = name_b
                    elif llr_b <= sprt_lower:
                        b_out = True
                if verdict is None and a_out and b_out:
                    verdict = "PARITY"

            print(f"  #{done:>3}/{games}: {scores[0]:3d}:{scores[1]:<3d} -> {winner_name:<22} "
                  f"| Züge {steps:3d} | LLR_A {llr_a:+.2f} | LLR_B {llr_b:+.2f} "
                  f"| ΔElo~{delta_elo_smooth:+.0f} | Stand {name_a} {a_wins}:{b_wins} {name_b} "
                  f"| Elo {elo[name_a]}/{elo[name_b]}",
                  flush=True)

            if verdict:
                label = (f"{verdict} signifikant staerker" if verdict != "PARITY"
                         else "Gleich stark (beide Seiten nicht signifikant staerker)")
                print(f"  ⏹️  SPRT-Entscheid nach {done} Spielen: {label} "
                      f"(LLR_A={llr_a:+.2f}, LLR_B={llr_b:+.2f}).")
                break
        if diag is not None:
            total_decisions += diag["decisions"]
            total_triggered += diag["rollouts_triggered"]
        if verdict:
            break

    if early_stop and verdict is None:
        verdict = "PARITY"
        print(f"  ⏹️  Ressourcenlimit erreicht (Spiel {games}) ohne SPRT-Entscheidung -> Gleich stark "
              f"(LLR_A={llr_a:+.2f}, LLR_B={llr_b:+.2f}).")

    dur = time.time() - t0
    print("-" * 50)
    print(f"🏆 ERGEBNIS: {name_a} {a_wins}:{b_wins} {name_b} "
          f"({a_wins/done*100:.0f}% A-Siege) in {dur:.1f}s ({done/dur:.1f} Spiele/s)"
          + (f"  [vorzeitig nach {done}/{games} Spielen]" if early_stop and done < games else ""))
    print(f"   Ø Score: {name_a} {_st.mean(a_scores):.1f} | {name_b} {_st.mean(b_scores):.1f}")
    print(f"   0:0-Spiele: {wins['ZeroZero']}/{done} ({wins['ZeroZero']/done*100:.1f}%)")
    print(f"   Elo: {name_a} {elo[name_a]} | {name_b} {elo[name_b]}")
    if total_decisions > 0:
        print(f"   Stufe-3-Entscheidungen (Runde 1-{stage3_max_round}): {total_decisions}, "
              f"davon per Rollout bewertet: {total_triggered}")


if __name__ == "__main__":
    import os
    # ── Teilnehmer hier manuell einstellen ───────────────────────────────────
    # AlphaZero-Netz (ONNX, Brett 0) vs Heuristik-MCTS (Brett 1). Werte anpassen.
    NET_MODEL = "models/alphazero_v2.onnx"   # Pfad zum ONNX-Netz
    NET_MODEL_PRE = "models/alphazero_v1c.onnx"
    NET_NAME = os.path.splitext(os.path.basename(NET_MODEL))[0].removeprefix("alphazero_")
    NET_NAME_PRE = os.path.splitext(os.path.basename(NET_MODEL_PRE))[0].removeprefix("alphazero_")
    NET_SIMS  = 200                            # Basis-Sims des Netzes
    HEUR_SIMS = NET_SIMS #60                             # Basis-Sims der Heuristik
    GAMES     = 100
    run_net_arena(NET_MODEL, net_sims=NET_SIMS, heur_sims=HEUR_SIMS, net_name = NET_NAME,
                  games=GAMES, threads=0)
    #run_net_vs_net(NET_MODEL, NET_MODEL_PRE, sims_a=NET_SIMS, sims_b=NET_SIMS, games=GAMES,
    #               threads=0, seed=None, chunk=10, c_puct=1.5, name_a=NET_NAME, name_b=NET_NAME_PRE)

    # ── Alternativ: reines Heuristik-Round-Robin (auskommentiert) ────────────
    # competitors = {
    #     "MCTS s50":  {"sims": 50,  "elo": 1000},
    #     "MCTS s100": {"sims": 100, "elo": 1000},
    #     "MCTS s200": {"sims": 200, "elo": 1000},
    # }
    # run_arena(competitors, games_per_matchup=100, threads=0)
