"""
Mosaic-AI -- Elo-Tracking-Infrastruktur (Task #62)
====================================================

Reine Buchhaltung + Bradley-Terry-Elo-Fit ueber evaluations/elo_history.csv.
Startet SELBST KEINE Matches (kein Arena-Aufruf) -- das Skript liest/schreibt
nur die CSV und rechnet. Matches werden extern gespielt und ihr Ergebnis
danach per `add` eingetragen.

GEPAARTES GATING ALS STANDARD (Task #76, 2026-07-23): Champion-Ablösungs-
Entscheidungen (neuer Kandidat vs. amtierenden Champion) laufen ab jetzt ueber
`tools/paired_gating.py`, NICHT mehr ueber `tools/arena.py::run_net_vs_net`s
SPRT direkt. `paired_gating.py` spielt gepaarte Seed-Bloecke mit GETAUSCHTEN
Brettern je Paar (Brett-/Zugreihenfolge-Bias faellt pro Paar heraus, nicht nur
im Erwartungswert) und einen exakten Paar-Vorzeichentest statt SPRT. Das
Ergebnis (a_wins_total/b_wins_total/n_games_total) wird GENAUSO per `add`
eingetragen wie bisher -- dieses Skript hier aendert sich dadurch nicht,
nur die Herkunft der eingetragenen Zahlen. `tools/arena.py::run_net_vs_net` bleibt
fuer schnelle, nicht-gating-relevante Sanity-Checks nuetzlich.

Kader (Nutzer-Entscheidung, siehe MEMORY.md "Plan, delegate to Sonnet agents"):
  - Heuristik@200 Sims   -- fester Elo-Anker, auf 1000 verankert (ANCHOR unten)
  - aktueller Netz-Champion@400 Sims   (derzeit v10_best)
  - vorheriger Netz-Champion@400 Sims  (sobald ein Nachfolger gated hat)

Warum die alten Heuristik-Matches NICHT in die CSV zurueckgefuellt wurden
--------------------------------------------------------------------------
Die historischen Netz-vs-Heuristik-Ergebnisse (z.B. die 17-26%-Session-
Baselines in tools/arena.py) liefen mit Heuristik@150 (dynamic_sims-skaliert, Ø~330
tatsaechliche Sims) UND unter dem alten Regelwerk vor dem Regelbuch-Audit
(82e8a88: Marker-/Tie-Break-/Monochrom-Fixes). Weder die Sims-Bedingung noch
die Spielregeln sind mit dem aktuellen Kader (Heuristik@200, neue Regeln)
vergleichbar -- ein Backfill wuerde Aepfel mit Birnen im selben Elo-Graphen
verrechnen. Die CSV startet daher bewusst NUR mit dem einen kader-validen
Bestandsergebnis (v11_best vs v10_best, 2026-07-22, siehe unten).

Ablauf fuer kuenftige Generationen (AB TASK #76 GEPAART, siehe oben)
--------------------------------------------------------------------
1. Neues Modell (z.B. v12_best) spielt gegen JEDES Kader-Mitglied:
   - vs. Heuristik@200: weiterhin `tools/arena.py::run_net_arena` (kein Kandidat-
     vs-Kandidat-Brett-Bias moeglich, Heuristik ist kein Netz-Brett).
   - vs. amtierenden/vorherigen Champion (Netz vs. Netz): NEU per
     `tools/paired_gating.py`:
       python tools/paired_gating.py \\
           --model-a models/alphazero_v12_best.onnx --name-a v12_best \\
           --model-b models/alphazero_v10_best.onnx --name-b v10_best \\
           --sims 400 --seed <FIXER_SEED>
     Druckt am Ende bereits eine fertige `add`-Kommandozeile (siehe
     `paired_gating.py`-Modul-Docstring fuer das gepaarte Brett-Tausch-Design).
2. Jedes Ergebnis per `add` eintragen (Beispiel, Heuristik-Match):
       python tools/elo_tracker.py add --player-a v12_best --sims-a 400 \\
           --player-b Heuristik --sims-b 200 --wins-a 61 --wins-b 39 --n 100 \\
           --comment "Kader-Match v12-Zyklus"
3. `python tools/elo_tracker.py report` zeigt den aktuellen Elo-Verlauf
   (Bradley-Terry-Fit ueber den gesamten Graphen, Heuristik@200 fix auf 1000).
4. Gating-Regel: ein neues Modell loest den amtierenden Champion nur ab, wenn
   es GEGEN DEN AMTIERENDEN CHAMPION signifikant gewinnt -- ab jetzt per
   `paired_gating.py`s exaktem Paar-Vorzeichentest (p<0.05, siehe dort), NICHT
   mehr per `tools/arena.py::run_net_vs_net`s SPRT. Ein blosser Sieg gegen die
   Heuristik allein reicht weiterhin nicht.

Die ERSTEN echten Kader-Matches (v10_best und v11_best je vs. Heuristik@200)
wurden bewusst NICHT ausgefuehrt (Maschine ist mit Training belegt) -- siehe
Kommando-Vorlagen oben, Punkt 1. Der Koordinator triggert sie spaeter.

Bestandseintrag (bereits in elo_history.csv)
-----------------------------------------------
v11_best 43:57 v10_best (n=100, beide @400 Sims, 2026-07-22,
"Gating-Match v11-Zyklus"). Kader-valide (gleiche Sims-Bedingung, aktuelles
Regelwerk) -- deshalb als einziger Bestandswert uebernommen.

CLI
---
  python tools/elo_tracker.py report
  python tools/elo_tracker.py add --player-a NAME --sims-a INT \\
      --player-b NAME --sims-b INT --wins-a INT --wins-b INT --n INT \\
      [--date YYYY-MM-DD] [--comment TEXT]
"""
import argparse
import csv
import math
import os
import random
import sys
from collections import defaultdict
from datetime import date as _date
from pathlib import Path

try:
    import numpy as _np
except ImportError:  # pragma: no cover
    _np = None

# Datendatei bleibt in evaluations/ (Reorg 2026-07-23: Skript nach tools/
# verschoben, Ergebnisdaten bleiben repo-Konvention nach in evaluations/).
CSV_PATH = str(Path(__file__).resolve().parent.parent / "evaluations" / "elo_history.csv")
HEADER = ["date", "player_a", "sims_a", "player_b", "sims_b", "wins_a", "wins_b", "n", "comment"]

ANCHOR_NAME = "Heuristik"
ANCHOR_SIMS = 200
ANCHOR_ELO = 1000.0
LN10_OVER_400 = math.log(10) / 400.0


def node_key(player, sims):
    sims = "" if sims in (None, "") else str(int(sims))
    return f"{player}@{sims}" if sims else str(player)


ANCHOR_KEY = node_key(ANCHOR_NAME, ANCHOR_SIMS)


# ---------------------------------------------------------------- CSV I/O --

def ensure_csv():
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(HEADER)


def load_rows():
    ensure_csv()
    rows = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append({
                "date": r["date"],
                "player_a": r["player_a"],
                "sims_a": r["sims_a"],
                "player_b": r["player_b"],
                "sims_b": r["sims_b"],
                "wins_a": int(r["wins_a"]),
                "wins_b": int(r["wins_b"]),
                "n": int(r["n"]),
                "comment": r.get("comment", ""),
            })
    return rows


def add_result(player_a, sims_a, player_b, sims_b, wins_a, wins_b, n,
               date=None, comment=""):
    """Traegt EIN Match-Ergebnis (aggregiert ueber n Spiele) in die CSV ein.
    wins_a + wins_b muss n ergeben (kein Draw-Feld -- Unentschieden werden im
    Regelwerk per Marker-Tie-Break immer aufgeloest, siehe tools/arena.py `winner`)."""
    if wins_a + wins_b != n:
        raise ValueError(f"wins_a({wins_a}) + wins_b({wins_b}) != n({n})")
    if n <= 0:
        raise ValueError("n muss > 0 sein")
    date = date or _date.today().isoformat()
    ensure_csv()
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([date, player_a, sims_a, player_b, sims_b,
                                 wins_a, wins_b, n, comment])
    print(f"Eingetragen: {node_key(player_a, sims_a)} {wins_a}:{wins_b} "
          f"{node_key(player_b, sims_b)} (n={n}, {date})")


# ------------------------------------------------------- Bradley-Terry-Fit --

def _build_graph(rows):
    """wins[i][j] = Siege von i gegen j (aggregiert ueber alle Zeilen mit
    demselben Knotenpaar), games[i][j] = gespielte Partien i vs j."""
    wins = defaultdict(lambda: defaultdict(int))
    games = defaultdict(lambda: defaultdict(int))
    nodes = {ANCHOR_KEY}
    for r in rows:
        a = node_key(r["player_a"], r["sims_a"])
        b = node_key(r["player_b"], r["sims_b"])
        nodes.add(a); nodes.add(b)
        wins[a][b] += r["wins_a"]
        wins[b][a] += r["wins_b"]
        games[a][b] += r["n"]
        games[b][a] += r["n"]
    return nodes, wins, games


def _connected_components(nodes, games):
    adj = defaultdict(set)
    for i in nodes:
        for j in nodes:
            if i != j and games[i][j] > 0:
                adj[i].add(j)
    seen = set()
    comps = []
    for n in nodes:
        if n in seen:
            continue
        stack, comp = [n], set()
        while stack:
            x = stack.pop()
            if x in seen:
                continue
            seen.add(x)
            comp.add(x)
            stack.extend(adj[x] - seen)
        comps.append(comp)
    return comps


def _mm_fit(comp, wins, games, anchor=None, anchor_elo=ANCHOR_ELO, iters=500, floor=1e-9):
    """Minorization-Maximization-Fit des Bradley-Terry-Modells (Zermelo/
    Hunter 2004) -- konvergiert monoton zur MLE, ohne Matrixinversion.
    gamma_i = exp(beta_i); p(i schlaegt j) = gamma_i/(gamma_i+gamma_j).
    Bei vorhandenem `anchor` bleibt dessen gamma waehrend der Iteration fix
    (verankerter Fit); sonst wird am Ende auf geometrisches Mittel = 1
    zentriert (Skala sonst unbestimmt -- kein Pfad zum Anker vorhanden)."""
    gamma = {i: 1.0 for i in comp}
    for _ in range(iters):
        for i in comp:
            if i == anchor:
                continue
            num = sum(wins[i][j] for j in comp if j != i and games[i][j] > 0)
            denom = 0.0
            for j in comp:
                if j == i or games[i][j] == 0:
                    continue
                denom += games[i][j] / (gamma[i] + gamma[j])
            if denom > 0:
                gamma[i] = max(num / denom, floor) if num > 0 else floor
    if anchor is not None and anchor in comp:
        ref = gamma[anchor]
    else:
        logs = [math.log(max(g, floor)) for g in gamma.values()]
        ref = math.exp(sum(logs) / len(logs))
    return {i: anchor_elo + math.log(max(gamma[i], floor) / ref) / LN10_OVER_400 for i in comp}


def fit_all(rows):
    """Elo je Knoten ueber ALLE Zeilen, komponentenweise (siehe _mm_fit).
    Rueckgabe: {node: (elo, connected_to_anchor: bool)}."""
    nodes, wins, games = _build_graph(rows)
    comps = _connected_components(nodes, games)
    out = {}
    for comp in comps:
        has_anchor = ANCHOR_KEY in comp
        if len(comp) == 1:
            only = next(iter(comp))
            if only == ANCHOR_KEY:
                out[only] = (ANCHOR_ELO, True)
            else:
                out[only] = (None, False)  # keine Spiele -- kein Rating moeglich
            continue
        elo = _mm_fit(comp, wins, games, anchor=ANCHOR_KEY if has_anchor else None)
        for i in comp:
            out[i] = (elo[i], has_anchor)
    return out, nodes, wins, games


def bootstrap_ci(rows, n_boot=2000, seed=0, alpha=0.05):
    """95%-CI je Knoten per nonparametrischem Bootstrap: jede Match-Zeile
    wird durch Binomial(n, wins_a/n) resampled (= Ziehen mit Zurueglegen aus
    den n Bernoulli-Spielausgaengen dieser Zeile), das BT-Modell neu
    gefittet, ueber n_boot Wiederholungen die 2.5/97.5-Perzentile genommen."""
    if not rows:
        return {}
    rng = _np.random.default_rng(seed) if _np is not None else random.Random(seed)
    samples = defaultdict(list)
    for b in range(n_boot):
        boot_rows = []
        for r in rows:
            p = r["wins_a"] / r["n"]
            if _np is not None:
                wa = int(rng.binomial(r["n"], p))
            else:
                wa = sum(1 for _ in range(r["n"]) if rng.random() < p)
            boot_rows.append({**r, "wins_a": wa, "wins_b": r["n"] - wa})
        fitted, _, _, _ = fit_all(boot_rows)
        for node, (elo, _) in fitted.items():
            if elo is not None:
                samples[node].append(elo)
    ci = {}
    lo_q, hi_q = 100 * alpha / 2, 100 * (1 - alpha / 2)
    for node, vals in samples.items():
        if len(vals) < 10:
            continue
        vals_sorted = sorted(vals)
        lo = vals_sorted[int(lo_q / 100 * len(vals_sorted))]
        hi = vals_sorted[min(len(vals_sorted) - 1, int(hi_q / 100 * len(vals_sorted)))]
        ci[node] = (lo, hi)
    return ci


# --------------------------------------------------------------- Reporting --

def report(n_boot=1000):
    rows = load_rows()
    fitted, nodes, wins, games = fit_all(rows)
    ci = bootstrap_ci(rows, n_boot=n_boot) if rows else {}

    print(f"=== Mosaic-AI Elo-Tabelle ({len(rows)} Match-Zeilen in {os.path.basename(CSV_PATH)}) ===")
    print(f"{'Modell':<20} {'Elo':>7} {'95%-CI':>18} {'Spiele':>7} {'W-L':>9}  Status")
    print("-" * 80)

    def sort_key(item):
        node, (elo, _) = item
        return -(elo if elo is not None else -1e9)

    for node, (elo, connected) in sorted(fitted.items(), key=sort_key):
        total_games = sum(games[node][j] for j in nodes if j != node)
        total_wins = sum(wins[node][j] for j in nodes if j != node)
        total_losses = total_games - total_wins
        if elo is None:
            print(f"{node:<20} {'--':>7} {'--':>18} {0:>7} {'--':>9}  keine Spiele")
            continue
        lo, hi = ci.get(node, (None, None))
        ci_str = f"[{lo:.0f}, {hi:.0f}]" if lo is not None else "n/a"
        status = "Anker (fix)" if node == ANCHOR_KEY else ("" if connected else "NICHT mit Anker verbunden!")
        print(f"{node:<20} {elo:>7.0f} {ci_str:>18} {total_games:>7} "
              f"{f'{total_wins}-{total_losses}':>9}  {status}")

    print()
    print("Match-Historie:")
    for r in rows:
        a = node_key(r["player_a"], r["sims_a"])
        b = node_key(r["player_b"], r["sims_b"])
        print(f"  {r['date']}  {a} {r['wins_a']}:{r['wins_b']} {b}  (n={r['n']})  {r['comment']}")


# ------------------------------------------------------------------- CLI --

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("report", help="Aktuelle Elo-Tabelle drucken")

    p_add = sub.add_parser("add", help="Match-Ergebnis eintragen")
    p_add.add_argument("--player-a", required=True)
    p_add.add_argument("--sims-a", type=int, required=True)
    p_add.add_argument("--player-b", required=True)
    p_add.add_argument("--sims-b", type=int, required=True)
    p_add.add_argument("--wins-a", type=int, required=True)
    p_add.add_argument("--wins-b", type=int, required=True)
    p_add.add_argument("--n", type=int, required=True)
    p_add.add_argument("--date", default=None)
    p_add.add_argument("--comment", default="")

    args = ap.parse_args()
    if args.cmd == "report":
        report()
    elif args.cmd == "add":
        add_result(args.player_a, args.sims_a, args.player_b, args.sims_b,
                   args.wins_a, args.wins_b, args.n, date=args.date, comment=args.comment)
        report()


if __name__ == "__main__":
    sys.exit(main())
