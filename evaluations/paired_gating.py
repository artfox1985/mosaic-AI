"""Gepaartes Netz-vs-Netz-Gating als STANDARD-Werkzeug fuer Kandidaten-
Vergleiche (Task #76, Phase A, 2026-07-23; SPRT-Upgrade 2026-07-23,
Nutzer-Anstoss).

## Warum ein eigenes Skript (statt `arena.py::run_net_vs_net` weiterzunutzen)

`arena.py::run_net_vs_net` spielt Kandidat A vs. Kandidat B direkt gegeneinander
und entscheidet per SPRT -- schnell, aber NICHT gepaart: Startspieler/Brett
alternieren zwar ueber viele Spiele (i % 2), aber JE EINZELNES Spiel hat ein
Kandidat zufaellig das potenziell staerkere/schwaechere Brett (falls es einen
strukturellen Brett-/Zugreihenfolge-Bias gibt) UND es gibt keine Varianz-
reduktion durch geteilte Startbedingungen zwischen Vergleichs-Laeufen.
Dieses Skript ergaenzt (ersetzt NICHT) `run_net_vs_net` fuer die eigentliche
GATING-Entscheidung (loest ein neuer Kandidat den amtierenden Champion ab?):
gepaarte Spiel-PAARE mit identischem Seed und getauschten Brettern, dazu eine
sequenzielle Stopp-Entscheidung mit kontrolliertem Fehlerniveau.

## Design: gepaarte Spiele

Verifiziert (siehe `self_play.rs::run_net_vs_net_arena` bzw. der neue Rust-
Test `self_play::tests::run_net_vs_net_arena_seeds_deterministically_like_
run_net_arena_match`): `net_vs_net_arena_match`s interne Pro-Spiel-Seed-
Ableitung ist GENAUSO deterministisch aus `seed + i * const` wie
`net_arena_match`/`arena_match` -- zwei Aufrufe mit identischem `seed` und
`n_games` liefern daher fuer Spielindex `i` exakt dieselben Startbedingungen
(Wertungsplatten-Auswahl, Startspieler-Index), unabhaengig davon, welche
Modelle auf welchem Brett stehen.

Ein **Paar** = EIN Seed, ZWEI Spiele:
  - Orientierung 1: Kandidat A auf Brett 0, Kandidat B auf Brett 1.
  - Orientierung 2: Kandidat B auf Brett 0, Kandidat A auf Brett 1 (SELBER Seed).

Die Rust-API liefert kein eingebautes "ein Aufruf, Brett-Tausch pro Spielpaar"
-- deshalb zwei separate `net_vs_net_arena_match`-Aufrufe mit vertauschten
Modellpfaden (und vertauschten sims/c_puct, damit der jeweilige Kandidat
weiterhin seine EIGENEN Suchparameter behaelt) bei GLEICHEM `seed`. Damit
bekommt jeder Kandidat innerhalb eines Paares GENAU EIN Spiel auf Brett 0 und
EINS auf Brett 1 -- ein etwaiger Brett-/Zugreihenfolge-Bias faellt PRO PAAR
heraus, nicht erst im Erwartungswert ueber viele Paare.

Jedes Paar faellt in genau eine von drei Kategorien:
  - `b` ("A-Sweep")    : A gewinnt BEIDE Spiele des Paares (2:0) -- informativ, Beleg fuer A.
  - `c` ("B-Sweep")    : B gewinnt BEIDE Spiele des Paares (0:2) -- informativ, Beleg fuer B.
  - Split (1:1)        : NICHT informativ (Brett-/Reihenfolge-Grenzfall, wird
    weder in die SPRT-Statistik noch in den Vorzeichentest einbezogen -- analog
    zu einem "Draw" in einem klassischen Vorzeichentest). Empirisch (Plumbing-
    Smoke, siehe STATUS.md) typischerweise die HAEUFIGSTE Kategorie bei
    aehnlich starken Kandidaten.

## Statistik: Bernoulli-SPRT auf den informativen Paaren als STOPP-Regel
(Nutzer-Anstoss, 2026-07-23, Fishtest-Muster)

Die urspruengliche erste Fassung dieses Skripts brach bei "kumulativem
McNemar p<0.05 je Block" ab -- das ist ein informelles, wiederholtes
Signifikanztesten OHNE Sequenz-Korrektur (dasselbe Verfahrens-Problem, das in
der Floor-Shaping-Signifikanzanalyse beobachtet wurde: wiederholtes Peeking
bei einem festen Alpha-Niveau treibt das TATSAECHLICHE Fehlerniveau ueber
mehrere Blicke auf ca. 7-10% statt der nominellen 5%). Ersetzt durch ein
echtes Wald-SPRT (1945) -- exakt das Fishtest/Stockfish-Testmuster, hier auf
INFORMATIVE PAARE statt Einzelspiele angewendet:

  H0: P(A gewinnt ein informatives Paar) = p0 = 0.5 (kein Unterschied)
  H1: P(A gewinnt ein informatives Paar) = p1 = 0.65 (Standard, per
      `--h1`/`sprt_p1` anpassbar)
  alpha = beta = 0.05 (Standard, je per CLI anpassbar)

Log-Likelihood-Ratio je informativem Paar: `+ln(p1/p0)` wenn A das Paar
gewinnt (Sweep b), `+ln((1-p1)/(1-p0))` wenn B gewinnt (Sweep c); Splits
tragen NICHTS bei (weder zum LLR noch zur Paarzahl der SPRT). Wald-Schranken
`ln(beta/(1-alpha))` (untere) und `ln((1-beta)/alpha)` (obere) -- bei
alpha=beta=0.05 symmetrisch bei ca. ±2.944 (Rechen-Selbsttest: `ln(0.05/0.95)
= ln(0.95/0.05)*-1 = -2.9444...`, siehe `_sprt_bounds_selftest()` unten).
LLR-Update NACH JEDEM Block gegen diese Schranken:
  - LLR >= obere Schranke -> H1 angenommen, A signifikant besser -> GATING-
    Entscheid fuer A, Stopp.
  - LLR <= untere Schranke -> H0 angenommen, KEIN Beleg dass A besser ist ->
    kein Ablöse-Entscheid (Champion B bleibt), Stopp (spart Rechenzeit bei
    einem klar unterlegenen/gleich starken Kandidaten, statt bis zum harten
    Deckel weiterzuspielen).
  - Weder noch UND harter Deckel (Standard 200 Paare) erreicht -> Abbruch
    OHNE SPRT-Entscheid ("kein Entscheid im SPRT-Sinn"), die Fixed-n-
    Statistik unten gilt dann als Notbehelf-Auswertung.

`p1=0.65` als Konvention: bei einer typischen informativen-Paar-Rate von
~35% (Faustwert aus fruehen Beobachtungen, schwankt je Kandidatenpaar)
entspricht das ungefaehr einer Gesamt-Winrate-Differenz von +10 Prozentpunkten
zwischen den Kandidaten -- ein Schwellenwert in der Groessenordnung, ab der ein
Champion-Wechsel praktisch lohnt. Bei anderer informativer Rate verschiebt
sich die implizierte Winrate-Differenz entsprechend; `--h1` erlaubt eine
bewusste Neukalibrierung, ohne Code anzufassen.

**Der exakte Paar-Vorzeichentest (`mcnemar_exact_p`, gleiche Formel wie in
`paired_arena_speedbundle.py`/`paired_arena_ismcts.py`) UND die gepaarte
Differenz-KI bleiben erhalten** -- sie sind aber jetzt NUR NOCH die finale
Bericht-Statistik (am Ende des Laufs berechnet, egal ob per SPRT oder per
Deckel gestoppt), NICHT mehr die Stopp-Entscheidung selbst. Das SPRT
uebernimmt ausschliesslich das "wann aufhoeren" -- die deskriptive
Fixed-n-Auswertung bleibt unveraendert exakt (`p`, `mean_pair_diff`, `ci95`
im Ergebnis-JSON).

Bloecke a 25 Paare (= 50 Spiele je Block), harter Deckel 200 Paare
(= 400 Spiele) falls das SPRT nie entscheidet.

## Nutzung

    python evaluations/paired_gating.py --model-a models/alphazero_v12_best.onnx \\
        --model-b models/alphazero_v10_best.onnx --name-a v12_best --name-b v10_best \\
        --sims 400

Schreibt `evaluations/paired_gating_result_<name_a>_vs_<name_b>.json`
(inkl. Block-Logs mit LLR-Verlauf) und druckt am Ende eine fertige
`elo_tracker.py add`-Kommandozeile (Zahlen aus der Fixed-n-Statistik, nicht
aus dem SPRT-Zwischenstand).

WICHTIG (Phase A, 2026-07-23): dieses Skript ist reine Code-Lieferung.
Es wird NICHT fuer eine echte Gating-Entscheidung ausgefuehrt, solange der
aktuelle netcq2-Self-Play-Batch das installierte Wheel nutzt -- nur ein
Winz-Parameter-Plumbing-Smoke (n=2, sims=20, v10_best gegen sich selbst) ist
in Phase A erlaubt (siehe `evaluations/STATUS.md`, Abschnitt "Gepaartes
Gating als Standard").
"""
import sys
import os
import json
import time
import math
import random
import argparse
from pathlib import Path
from math import comb

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent

BLOCK_SIZE = 25
MAX_PAIRS = 200                 # harter Deckel (Nutzer-Anstoss: 150 -> 200)
DEFAULT_SIMS = 400
DEFAULT_C_PUCT = 1.5
DEFAULT_THREADS = 0

# SPRT-Konvention (Fishtest-Muster, Nutzer-Anstoss 2026-07-23) -- siehe
# Modul-Docstring fuer die volle Begruendung von p1=0.65.
SPRT_P0 = 0.5
SPRT_P1 = 0.65
SPRT_ALPHA = 0.05
SPRT_BETA = 0.05


def mcnemar_exact_p(b: int, c: int) -> float:
    """Exakter zweiseitiger Vorzeichentest auf den informativen Zellen (b, c)
    -- identische Formel wie in `paired_arena_speedbundle.py`/
    `paired_arena_ismcts.py`: X ~ Binomial(n=b+c, p=0.5),
    p = 2*min(P(X<=min(b,c)), P(X>=max(b,c))), gedeckelt bei 1.0. Dient hier
    NUR NOCH als finale Fixed-n-Bericht-Statistik (siehe Modul-Docstring) --
    nicht mehr als Stopp-Regel, das uebernimmt das SPRT unten."""
    n = b + c
    if n == 0:
        return 1.0
    lo, hi = min(b, c), max(b, c)
    p_le = sum(comb(n, k) for k in range(0, lo + 1)) / (2 ** n)
    p_ge = sum(comb(n, k) for k in range(hi, n + 1)) / (2 ** n)
    return min(1.0, 2 * min(p_le, p_ge))


def paired_ci(diffs: list[int], z: float = 1.96) -> tuple[float, float, float]:
    """Normalapprox. 95%-KI (Standard z=1.96) fuer den Mittelwert der
    gepaarten Differenzen `d_i in {-2, 0, +2}`. Liefert (mean, lo, hi);
    bei n<2 kollabiert das KI auf den Mittelwert (keine Streuung schaetzbar)."""
    n = len(diffs)
    if n == 0:
        return 0.0, 0.0, 0.0
    mean = sum(diffs) / n
    if n < 2:
        return mean, mean, mean
    var = sum((d - mean) ** 2 for d in diffs) / (n - 1)
    se = (var / n) ** 0.5
    return mean, mean - z * se, mean + z * se


def sprt_bounds(alpha: float = SPRT_ALPHA, beta: float = SPRT_BETA) -> tuple[float, float]:
    """Wald-Abbruchschranken (1945) fuer den truncated SPRT -- identische
    Formel wie `arena.py::sprt_bounds` (dort auf EINZELSPIELE angewendet,
    hier auf INFORMATIVE PAARE, siehe Modul-Docstring). Untere Schranke
    `ln(beta/(1-alpha))`, obere Schranke `ln((1-beta)/alpha)`. Bei
    alpha=beta=0.05: ±ln(19) = ±2.9444... (symmetrisch, weil alpha=beta)."""
    lower = math.log(beta / (1 - alpha))
    upper = math.log((1 - beta) / alpha)
    return lower, upper


def sprt_llr_delta(a_won_pair: bool, p0: float = SPRT_P0, p1: float = SPRT_P1) -> float:
    """LLR-Zuwachs fuer EIN informatives Paar (identische Formel wie
    `arena.py::sprt_llr_delta`, hier pro Paar statt pro Einzelspiel).
    `a_won_pair`: True fuer einen A-Sweep (b), False fuer einen B-Sweep (c)
    -- Splits rufen diese Funktion nie auf (siehe Aufrufstelle)."""
    if a_won_pair:
        return math.log(p1 / p0)
    return math.log((1 - p1) / (1 - p0))


def _sprt_bounds_selftest() -> None:
    """Kurzer Rechen-Selbsttest (Nutzer-Anforderung): bestaetigt
    `sprt_bounds(0.05, 0.05)` gegen die per Hand ausgerechneten Werte
    `ln(0.05/0.95)` / `ln(0.95/0.05)` -- laeuft bei jedem Skript-Start einmal
    (billig, reine Arithmetik, keine Seiteneffekte)."""
    lower, upper = sprt_bounds(0.05, 0.05)
    hand_lower = math.log(0.05 / 0.95)
    hand_upper = math.log(0.95 / 0.05)
    assert abs(lower - hand_lower) < 1e-12, f"sprt_bounds untere Schranke weicht ab: {lower} vs {hand_lower}"
    assert abs(upper - hand_upper) < 1e-12, f"sprt_bounds obere Schranke weicht ab: {upper} vs {hand_upper}"
    assert abs(lower + upper) < 1e-12, "bei alpha=beta sollten die Schranken symmetrisch sein (lower == -upper)"


_sprt_bounds_selftest()


def play_pair_block(mr, model_a: str, model_b: str, sims_a: int, sims_b: int,
                     c_puct_a: float, c_puct_b: float, n: int, seed: int,
                     threads: int) -> tuple[list[dict], list[dict]]:
    """Spielt EINEN Block von `n` gepaarten Seeds -- je Seed zwei Spiele mit
    getauschten Brettern (siehe Modul-Docstring). `g1[i]`/`g2[i]` teilen sich
    denselben abgeleiteten Pro-Spiel-Seed (identisches `seed`+`n_games`,
    Index `i`), nur die Modell-Brett-Zuordnung ist vertauscht."""
    raw1 = mr.net_vs_net_arena_match(
        model_a, model_b, sims_a=sims_a, sims_b=sims_b, n_games=n, seed=seed,
        num_threads=threads, c_puct_a=c_puct_a, c_puct_b=c_puct_b,
    )
    raw2 = mr.net_vs_net_arena_match(
        model_b, model_a, sims_a=sims_b, sims_b=sims_a, n_games=n, seed=seed,
        num_threads=threads, c_puct_a=c_puct_b, c_puct_b=c_puct_a,
    )
    return json.loads(raw1), json.loads(raw2)


def run_paired_gating(model_a: str, model_b: str, name_a: str | None = None,
                       name_b: str | None = None, sims_a: int = DEFAULT_SIMS,
                       sims_b: int = DEFAULT_SIMS, c_puct_a: float = DEFAULT_C_PUCT,
                       c_puct_b: float = DEFAULT_C_PUCT, block_size: int = BLOCK_SIZE,
                       max_pairs: int = MAX_PAIRS, sprt_p1: float = SPRT_P1,
                       sprt_alpha: float = SPRT_ALPHA, sprt_beta: float = SPRT_BETA,
                       base_seed: int | None = None, threads: int = DEFAULT_THREADS) -> dict:
    """Orchestriert das volle gepaarte Gating (siehe Modul-Docstring). Die
    STOPP-Entscheidung ist ein Wald-SPRT auf den informativen Paaren (b/c);
    bricht NACH einem VOLLSTAENDIGEN Block ab, sobald die LLR eine der beiden
    Wald-Schranken erreicht, oder wenn `max_pairs` Paare erreicht sind (dann
    OHNE SPRT-Entscheid). Importiert `mosaic_rust` HIER (nicht auf
    Modulebene) -- welches Wheel geladen wird, entscheidet allein der
    aufrufende Python-Interpreter, nicht dieses Skript."""
    import mosaic_rust as mr

    name_a = name_a or os.path.basename(model_a)
    name_b = name_b or os.path.basename(model_b)
    base_seed = base_seed if base_seed is not None else random.randint(0, 10 ** 9)
    sprt_lower, sprt_upper = sprt_bounds(sprt_alpha, sprt_beta)

    pair_a_sweeps = pair_b_sweeps = splits = 0
    a_wins_total = b_wins_total = 0
    pair_diffs: list[int] = []
    llr = 0.0
    sprt_verdict = None   # None=laeuft noch, name_a=A signifikant besser, "H0"=kein Beleg fuer A
    done_pairs = 0
    block_idx = 0
    block_logs: list[dict] = []

    print(f"Gepaartes Gating (Task #76): {name_a}@{sims_a} (c_puct={c_puct_a}) vs "
          f"{name_b}@{sims_b} (c_puct={c_puct_b}) -- Basis-Seed={base_seed}, "
          f"Bloecke a {block_size} Paare, harter Deckel {max_pairs} Paare")
    print(f"  SPRT: H0 p={SPRT_P0} vs. H1 p={sprt_p1}, alpha={sprt_alpha} beta={sprt_beta}, "
          f"Wald-Schranken [{sprt_lower:+.4f}, {sprt_upper:+.4f}]")

    while done_pairs < max_pairs:
        n = min(block_size, max_pairs - done_pairs)
        seed = base_seed + block_idx * 1_000_000
        t0 = time.time()
        g1, g2 = play_pair_block(mr, model_a, model_b, sims_a, sims_b, c_puct_a, c_puct_b,
                                  n, seed, threads)
        dur = time.time() - t0

        for i in range(n):
            a_won_o1 = g1[i]["winner"] == 0  # A auf Brett 0 (Orientierung 1)
            a_won_o2 = g2[i]["winner"] == 1  # A auf Brett 1 (Orientierung 2, B auf Brett 0)
            a_wins_pair = int(a_won_o1) + int(a_won_o2)
            b_wins_pair = 2 - a_wins_pair
            a_wins_total += a_wins_pair
            b_wins_total += b_wins_pair
            pair_diffs.append(a_wins_pair - b_wins_pair)
            if a_wins_pair == 2:
                pair_a_sweeps += 1
                llr += sprt_llr_delta(True, p1=sprt_p1)
            elif b_wins_pair == 2:
                pair_b_sweeps += 1
                llr += sprt_llr_delta(False, p1=sprt_p1)
            else:
                splits += 1  # nicht informativ -- traegt NICHT zur LLR bei

        done_pairs += n
        block_idx += 1
        report_p = mcnemar_exact_p(pair_a_sweeps, pair_b_sweeps)
        mean_d, ci_lo, ci_hi = paired_ci(pair_diffs)
        block_log = {
            "block": block_idx, "seed": seed, "n_pairs_block": n, "done_pairs": done_pairs,
            "a_wins_total": a_wins_total, "b_wins_total": b_wins_total,
            "pair_a_sweeps_b": pair_a_sweeps, "pair_b_sweeps_c": pair_b_sweeps,
            "pair_splits": splits, "llr": llr, "sprt_bounds": [sprt_lower, sprt_upper],
            "report_mcnemar_p": report_p, "mean_pair_diff": mean_d, "ci95": [ci_lo, ci_hi],
            "duration_s": dur,
        }
        block_logs.append(block_log)
        print(f"  Block {block_idx} (Seed={seed}, n={n} Paare, {dur:.1f}s): kumulativ "
              f"{name_a} {a_wins_total}:{b_wins_total} {name_b} | Paare {done_pairs} "
              f"(A-Sweep b={pair_a_sweeps} B-Sweep c={pair_b_sweeps} Split={splits}) | "
              f"LLR={llr:+.3f} [{sprt_lower:+.3f},{sprt_upper:+.3f}] | "
              f"Bericht-McNemar p={report_p:.4f} | gepaarte Diff {mean_d:+.3f} "
              f"[{ci_lo:+.3f},{ci_hi:+.3f}]", flush=True)

        if llr >= sprt_upper:
            sprt_verdict = name_a
            print(f"  SPRT-Entscheid nach {done_pairs} Paaren: {name_a} signifikant besser "
                  f"(LLR={llr:+.3f} >= obere Schranke {sprt_upper:+.3f}).")
            break
        if llr <= sprt_lower:
            sprt_verdict = "H0"
            print(f"  SPRT-Entscheid nach {done_pairs} Paaren: KEIN Beleg dass {name_a} besser "
                  f"ist (LLR={llr:+.3f} <= untere Schranke {sprt_lower:+.3f}) -- {name_b} bleibt.")
            break
    else:
        sprt_verdict = "UNDECIDED_CAP_REACHED"
        print(f"  {max_pairs} Paare (harter Deckel) erreicht OHNE SPRT-Entscheid "
              f"(LLR={llr:+.3f}, Schranken [{sprt_lower:+.3f},{sprt_upper:+.3f}]) -- "
              f"Fixed-n-Auswertung unten gilt als Notbehelf.")

    final_p = mcnemar_exact_p(pair_a_sweeps, pair_b_sweeps)
    mean_d, ci_lo, ci_hi = paired_ci(pair_diffs)
    n_games_total = done_pairs * 2
    result = {
        "name_a": name_a, "name_b": name_b, "model_a": model_a, "model_b": model_b,
        "sims_a": sims_a, "sims_b": sims_b, "c_puct_a": c_puct_a, "c_puct_b": c_puct_b,
        "done_pairs": done_pairs, "n_games_total": n_games_total,
        "a_wins_total": a_wins_total, "b_wins_total": b_wins_total,
        "pair_a_sweeps_b": pair_a_sweeps, "pair_b_sweeps_c": pair_b_sweeps,
        "pair_splits": splits,
        "sprt_verdict": sprt_verdict, "sprt_llr": llr, "sprt_bounds": [sprt_lower, sprt_upper],
        "sprt_p0": SPRT_P0, "sprt_p1": sprt_p1, "sprt_alpha": sprt_alpha, "sprt_beta": sprt_beta,
        "report_mcnemar_p": final_p, "mean_pair_diff": mean_d, "ci95": [ci_lo, ci_hi],
        "base_seed": base_seed, "blocks": block_logs,
    }

    verdict_label = {
        name_a: f"{name_a} signifikant besser (SPRT)",
        "H0": f"kein Beleg, dass {name_a} besser ist (SPRT H0 angenommen)",
        "UNDECIDED_CAP_REACHED": "harter Deckel erreicht, KEIN SPRT-Entscheid",
    }[sprt_verdict]

    print("-" * 60)
    print(f"ERGEBNIS: {name_a} {a_wins_total}:{b_wins_total} {name_b} "
          f"(von {n_games_total} Spielen, {done_pairs} Paaren)")
    print(f"  SPRT-Entscheid: {verdict_label}")
    print(f"  Informative Paare: A-Sweep b={pair_a_sweeps}  B-Sweep c={pair_b_sweeps}  "
          f"Split={splits}")
    print(f"  Fixed-n-Bericht-Statistik (NICHT die Stopp-Entscheidung): "
          f"exakter Paar-Vorzeichentest p={final_p:.4f}")
    print(f"  Gepaarte Differenz (A-Siege minus B-Siege pro Paar): "
          f"{mean_d:+.3f}  95%-KI [{ci_lo:+.3f}, {ci_hi:+.3f}]")
    print(f"  Hinweis fuers elo_tracker-Protokoll:")
    print(f"    python evaluations/elo_tracker.py add --player-a {name_a} --sims-a {sims_a} "
          f"--player-b {name_b} --sims-b {sims_b} --wins-a {a_wins_total} "
          f"--wins-b {b_wins_total} --n {n_games_total} "
          f"--comment \"Gepaartes Gating (Task #76), SPRT={sprt_verdict}, p={final_p:.4f}\"")
    return result


def main() -> None:
    p = argparse.ArgumentParser(description="Gepaartes Netz-vs-Netz-Gating (Task #76)")
    p.add_argument("--model-a", required=True)
    p.add_argument("--model-b", required=True)
    p.add_argument("--name-a", default=None)
    p.add_argument("--name-b", default=None)
    p.add_argument("--sims", type=int, default=None, help="Setzt sims-a UND sims-b gleich")
    p.add_argument("--sims-a", type=int, default=DEFAULT_SIMS)
    p.add_argument("--sims-b", type=int, default=DEFAULT_SIMS)
    p.add_argument("--c-puct", type=float, default=None, help="Setzt c-puct-a UND c-puct-b gleich")
    p.add_argument("--c-puct-a", type=float, default=DEFAULT_C_PUCT)
    p.add_argument("--c-puct-b", type=float, default=DEFAULT_C_PUCT)
    p.add_argument("--block-size", type=int, default=BLOCK_SIZE)
    p.add_argument("--max-pairs", type=int, default=MAX_PAIRS, help="Harter SPRT-Deckel (Paare)")
    p.add_argument("--h1", type=float, default=SPRT_P1, dest="sprt_p1",
                    help="SPRT-Alternativhypothese P(A gewinnt informatives Paar) unter H1 (Standard 0.65)")
    p.add_argument("--sprt-alpha", type=float, default=SPRT_ALPHA)
    p.add_argument("--sprt-beta", type=float, default=SPRT_BETA)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--threads", type=int, default=DEFAULT_THREADS)
    p.add_argument("--out", default=None, help="Ziel-JSON-Pfad (Default: evaluations/paired_gating_result_<a>_vs_<b>.json)")
    args = p.parse_args()

    sims_a = args.sims if args.sims is not None else args.sims_a
    sims_b = args.sims if args.sims is not None else args.sims_b
    c_puct_a = args.c_puct if args.c_puct is not None else args.c_puct_a
    c_puct_b = args.c_puct if args.c_puct is not None else args.c_puct_b

    result = run_paired_gating(
        args.model_a, args.model_b, name_a=args.name_a, name_b=args.name_b,
        sims_a=sims_a, sims_b=sims_b, c_puct_a=c_puct_a, c_puct_b=c_puct_b,
        block_size=args.block_size, max_pairs=args.max_pairs, sprt_p1=args.sprt_p1,
        sprt_alpha=args.sprt_alpha, sprt_beta=args.sprt_beta,
        base_seed=args.seed, threads=args.threads,
    )

    out_path = Path(args.out) if args.out else (
        Path(__file__).resolve().parent
        / f"paired_gating_result_{result['name_a']}_vs_{result['name_b']}.json"
    )
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Ergebnis gespeichert: {out_path}")


if __name__ == "__main__":
    main()
