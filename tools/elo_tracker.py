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
  - Heuristik@150 Sims (nominal; Heuristik-Pfad nutzt dynamic_sims -> real Ø~330)   -- fester Elo-Anker, auf 1000 verankert (ANCHOR unten)
  - aktueller Netz-Champion@400 Sims   (derzeit v10_best)
  - vorheriger Netz-Champion@400 Sims  (sobald ein Nachfolger gated hat)

Warum die alten Heuristik-Matches NICHT in die CSV zurueckgefuellt wurden
--------------------------------------------------------------------------
Die historischen Netz-vs-Heuristik-Ergebnisse (z.B. die 17-26%-Session-
Baselines in tools/arena.py) liefen mit Heuristik@150 (dynamic_sims-skaliert, Ø~330
tatsaechliche Sims) UND unter dem alten Regelwerk vor dem Regelbuch-Audit
(82e8a88: Marker-/Tie-Break-/Monochrom-Fixes). Weder die Sims-Bedingung noch
die Spielregeln sind mit dem aktuellen Kader (Heuristik@150(dyn~330), neue Regeln)
vergleichbar -- ein Backfill wuerde Aepfel mit Birnen im selben Elo-Graphen
verrechnen. Die CSV startet daher bewusst NUR mit dem einen kader-validen
Bestandsergebnis (v11_best vs v10_best, 2026-07-22, siehe unten).

Ablauf fuer kuenftige Generationen (AB TASK #76 GEPAART, siehe oben)
--------------------------------------------------------------------
1. Neues Modell (z.B. v12_best) spielt gegen JEDES Kader-Mitglied:
   - vs. Heuristik@150(dyn~330): weiterhin `tools/arena.py::run_net_arena` (kein Kandidat-
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
   (Bradley-Terry-Fit ueber den gesamten Graphen, Heuristik@150(dyn~330) fix auf 1000).
4. Gating-Regel: ein neues Modell loest den amtierenden Champion nur ab, wenn
   es GEGEN DEN AMTIERENDEN CHAMPION signifikant gewinnt -- ab jetzt per
   `paired_gating.py`s exaktem Paar-Vorzeichentest (p<0.05, siehe dort), NICHT
   mehr per `tools/arena.py::run_net_vs_net`s SPRT. Ein blosser Sieg gegen die
   Heuristik allein reicht weiterhin nicht.

Die ERSTEN echten Kader-Matches (v10_best und v11_best je vs. Heuristik@150(dyn~330))
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
# `contract` und `knobs` sind ADDITIV (2026-08-10, Nutzer-Auftrag
# "aktualisieren bzw. archivieren"): Altzeilen ohne diese Spalten bleiben
# lesbar, weil `load_rows` sie ueber `.get()` mit Default holt.
# Motivation: eine Elo-Leiter ist nur so gut wie ihre Rueckverfolgbarkeit.
#   `contract` = A2-Vertragsstempel des Binaries (`engine_config_json()`,
#                Hash ueber INPUT_SIZE/NUM_PLANES_CHANNELS/NUM_ACTIONS/Koepfe)
#                -- traegt die I/O-Form, NICHT das Verhalten.
#   `knobs`    = die zum Match aktiven NICHT-Default-`MOSAIC_*`-Variablen
#                -- genau die Spalte, die das Verhalten traegt. Ohne sie waere
#                ein Anker-Wechsel wie das Scharfschalten der
#                Runde-5-Zufallsknoten in der Leiter unsichtbar.
# `units` und `early_stop` sind ebenfalls ADDITIV (2026-09-12, Nutzer-Auftrag "mach das
# Werkzeug"): Altzeilen ohne die Spalten bleiben lesbar.
#   `units`      = Resampling-Einheiten der Kante als "k:w1,w2,...": k Partien je Einheit
#                  (ein Seed-Block des gepaarten Gatings = 5 Paare = 10 Partien), w_i = Siege
#                  von A in Einheit i. Der Bootstrap zieht dann EINHEITEN mit Zuruecklegen
#                  statt Einzelpartien: die Partien eines Blocks teilen den Seed und sind
#                  korreliert; als unabhaengige Bernoulli-Versuche gezogen waere das
#                  Intervall zu schmal. Leer = Einzelpartien (Referee-Kanten: ein Seed je
#                  Partie) oder unbekannt (Altzeilen), dann Binomial wie bisher.
#   `early_stop` = 1, wenn die Kante nach einer Stopp-Regel (SPRT, Binomial-Block-Abbruch)
#                  vor dem festen Umfang beendet wurde. Die Siegquote einer solchen Kante ist
#                  nach oben verzerrt; der Fit kann das nicht korrigieren, der Report weist
#                  es je Knoten und je Zeile aus.
HEADER = ["date", "player_a", "sims_a", "player_b", "sims_b", "wins_a", "wins_b", "n",
          "comment", "contract", "knobs", "units", "early_stop"]

# DER ANKER IST DAS EINGEFRORENE ARTEFAKT (Nutzer-Entscheid 2026-08-31).
#
# Vorher stand hier "Heuristik", also der IN-PROCESS-Pfad. Der ist aber eine
# ENTWICKLUNGSUMGEBUNG (Nutzer: "die in process heuristik ist kein guter
# vergleichswert") -- er wird weiterentwickelt und darf sich bewegen. Ein
# Fixpunkt, der sich bewegen darf, ist keiner. Der Anker gehoert deshalb an
# `models/frozen_heuristics/hv1_anchor`, das sich per Konstruktion nicht
# bewegen kann und seine Konservierung selbst beweist
# (`tools/verify_frozen_heuristic.py --venv`).
#
# WAS DAS REPARIERT: die Promotions-Checkliste schreibt seit dem 2026-08-28
# `Heuristik_hv1_anchor` in die Zeile, verankert war aber der LITERALE Name
# "Heuristik". Jede Anker-Kante seither erzeugte damit einen ZWEITEN, freien
# Knoten; `fit_all` zentriert ankerlose Komponenten auf das geometrische
# Mittel, und die gedruckten Zahlen trugen nur noch ihre Differenz (am
# 2026-08-31: v23-b01 1148 / hv1_anchor 852, Summe exakt 2000).
# NEUVERANKERUNG 2026-09-12 (PREREG_code_cleanup_closeout.md par.7a): der
# Phantom-Fix A2 hat den lebenden hv1 vom Artefakt `hv1_anchor` entfernt
# (Drift ROT ab Schritt 99). Nutzer-Entscheid: Anker neu setzen. Neues
# Segment: Artefakt `models/frozen_heuristics/hv4_anchor` (Wheel mit A2),
# frisches Register; das Alt-Register liegt in
# `archive/elo_history_pre_phantomfix.csv` und wird NIE mit diesem gemischt
# (Regel wie bei der R5-Neuverankerung 2026-08-21).
ANCHOR_NAME = "Heuristik_hv4_anchor"
# Korrigendum 2026-07-25: Anker lief faktisch IMMER mit HEUR_SIMS=150
# (nominal; dynamic_sims -> real Ø~330) -- Label war faelschlich 200.
ANCHOR_SIMS = 150
ANCHOR_ELO = 1000.0

# Zeilen VOR der Umbenennung (2026-08-28) fuehren den Anker als "Heuristik".
# Sie werden auf denselben Knoten gefaltet, sonst zerfaellt die Leiter in zwei
# Haelften: die Anker-Kanten von v19/v20/v21 haengen an dem alten Namen.
#
# GEDECKT durch Messung, aber NICHT vollstaendig: am 2026-08-31 wurde
# geprueft, dass der lebende hv1 und das Artefakt Zug fuer Zug dasselbe
# spielen (1.763 Schritte, Feld fuer Feld, beide Wheels gruen;
# `artifacts/anchor_drift_live_wheel_20260831.json`), und am 2026-08-27, dass
# Referee-Pfad und In-Process-Pfad dieselben Partien liefern (20/20).
# UNGEPRUEFT bleibt die Strecke 2026-08-20 (Datum der v19/v20/v21-Kanten) bis
# zum Einfriertag 2026-08-26: dafuer gibt es kein Wheel jener Tage im Baum.
# Waere der Anker DORT verschoben worden, mischte dieser Alias zwei Spieler in
# einem Knoten. Das ist die einzige unbelegte Fuge der Leiter -- sie gehoert
# benannt, nicht stillschweigend gefaltet.
#
# NICHT aliasiert wird `Heuristik_v2huelle`: das ist der hv2-Lehrer, ein
# ANDERER Spieler (Elo 1125 aus eigener Kante).
# Seit 2026-09-12 KEINE Aliase: "Heuristik" und "Heuristik_hv1_anchor" sind
# Spieler des Alt-Registers auf der Engine vor A2; im neuen Segment gibt es
# nur `hv4_anchor`.
ANCHOR_ALIASES = {}
LN10_OVER_400 = math.log(10) / 400.0


def node_key(player, sims):
    # Alias VOR der Schluesselbildung: sonst haette derselbe Spieler unter zwei
    # Namen zwei Knoten (siehe ANCHOR_ALIASES).
    player = ANCHOR_ALIASES.get(str(player), player)
    sims = "" if sims in (None, "") else str(int(sims))
    return f"{player}@{sims}" if sims else str(player)


ANCHOR_KEY = node_key(ANCHOR_NAME, ANCHOR_SIMS)


# ---------------------------------------------------------------- CSV I/O --

def ensure_csv():
    if not os.path.exists(CSV_PATH):
        # Release-Bundle-Fall (Rauchtest 2026-08-15): im PyInstaller-Bundle
        # existiert evaluations/ nicht -- open("w") wirft dann FileNotFoundError
        # BEVOR die Datei angelegt werden kann. Elternverzeichnis sicherstellen.
        os.makedirs(os.path.dirname(CSV_PATH) or ".", exist_ok=True)
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(HEADER)


def _migrate_header():
    """Hebt eine CSV mit aelterem Kopf auf HEADER an (fehlende Spalten leer).

    Noetig, weil `csv.DictReader` Felder JENSEITS des Kopfes still verwirft: eine
    13-Felder-Zeile unter einem 11-Spalten-Kopf verliert `units` und `early_stop`,
    ohne dass es jemand sieht (Testfund 2026-09-12)."""
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header == HEADER:
            return
        if header is None or any(col not in HEADER for col in header):
            raise ValueError(f"{CSV_PATH}: unbekannter Kopf {header}")
        rows = [dict(zip(header, r)) for r in reader]
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=HEADER)
        w.writeheader()
        for r in rows:
            w.writerow({col: r.get(col, "") for col in HEADER})


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
                "comment": r.get("comment", "") or "",
                "contract": r.get("contract", "") or "",
                "knobs": r.get("knobs", "") or "",
                "units": (r.get("units", "") or "").strip(),
                "early_stop": int(r.get("early_stop") or 0),
            })
    return rows


def parse_units(units, wins_a, n):
    """"k:w1,w2,..." -> Liste (siege_a, partien) je Einheit; None bei leerem String.

    k = Partien je Einheit, w_i = Siege von A in Einheit i. Die letzte Einheit darf
    kleiner sein (angebrochener Block). Prueft Summe der Siege gegen wins_a und den
    Umfang gegen n; jede Abweichung ist ein Fehler, keine Warnung."""
    units = (units or "").strip()
    if not units:
        return None
    head, sep, body = units.partition(":")
    if not sep:
        raise ValueError(f"units ohne ':' -- erwartet 'k:w1,w2,...', bekommen {units!r}")
    k = int(head)
    ws = [int(x) for x in body.split(",") if x.strip() != ""]
    if k <= 0 or not ws:
        raise ValueError(f"units braucht k > 0 und mindestens eine Einheit: {units!r}")
    m = len(ws)
    if not ((m - 1) * k < n <= m * k):
        raise ValueError(f"units: {m} Einheiten a {k} passen nicht zu n={n}")
    sizes = [k] * (m - 1) + [n - (m - 1) * k]
    if sum(ws) != wins_a:
        raise ValueError(f"units: Siege {sum(ws)} != wins_a {wins_a}")
    for w, sz in zip(ws, sizes):
        if w < 0 or w > sz:
            raise ValueError(f"units: Einheit mit {w} Siegen bei {sz} Partien")
    return list(zip(ws, sizes))


def units_from_paired_artifact(path):
    """Leitet den `units`-String aus einem paired_gating-Artefakt ab: eine Einheit je
    Seed-Block (`per_pair_scores[*].block_seed`, in Reihenfolge des Auftretens), Umfang
    2 Partien je Paar, Siege = Summe `a_wins_pair`. Prueft gegen a_wins_total und
    n_games_total des Artefakts."""
    import json as _json
    with open(path, encoding="utf-8") as f:
        d = _json.load(f)
    order, groups = [], {}
    for p in d["per_pair_scores"]:
        key = p["block_seed"]
        if key not in groups:
            groups[key] = {"pairs": 0, "wins": 0}
            order.append(key)
        groups[key]["pairs"] += 1
        groups[key]["wins"] += int(p["a_wins_pair"])
    if not order:
        raise ValueError(f"{path}: per_pair_scores leer")
    sizes = [2 * groups[k]["pairs"] for k in order]
    k = sizes[0]
    if any(sz != k for sz in sizes[:-1]) or sizes[-1] > k:
        raise ValueError(f"{path}: Blockgroessen uneinheitlich {sizes}")
    ws = [groups[key]["wins"] for key in order]
    n = sum(sizes)
    if n != int(d["n_games_total"]) or sum(ws) != int(d["a_wins_total"]):
        raise ValueError(f"{path}: Einheiten {sum(ws)}/{n} passen nicht zu "
                         f"{d['a_wins_total']}/{d['n_games_total']}")
    return f"{k}:{','.join(str(w) for w in ws)}"


def engine_contract() -> str:
    """A2-Vertragsstempel des INSTALLIERTEN Binaries, "" wenn nicht ermittelbar.

    Bewusst best-effort: die Buchhaltung darf nie daran scheitern, dass das
    Wheel gerade nicht importierbar ist."""
    try:
        import json as _json

        import mosaic_rust  # type: ignore

        cfg = _json.loads(mosaic_rust.engine_config_json())
        return str(cfg.get("contract", "") or cfg.get("contract_hash", ""))
    except Exception:
        return ""


def active_knobs() -> str:
    """Aktive NICHT-Default `MOSAIC_*`-Variablen als `k=v;k=v`.

    Was hier steht, ist die Verhaltens-Signatur des Matches. Leer = alles auf
    Default, also Bestandsverhalten."""
    items = sorted(
        (k, v) for k, v in os.environ.items()
        if k.startswith("MOSAIC_") and v not in ("", "0")
    )
    return ";".join(f"{k}={v}" for k, v in items)


def add_result(player_a, sims_a, player_b, sims_b, wins_a, wins_b, n,
               date=None, comment="", contract=None, knobs=None,
               units="", early_stop=False):
    """Traegt EIN Match-Ergebnis (aggregiert ueber n Spiele) in die CSV ein.
    wins_a + wins_b muss n ergeben (kein Draw-Feld -- Unentschieden werden im
    Regelwerk per Marker-Tie-Break immer aufgeloest, siehe tools/arena.py `winner`)."""
    if wins_a + wins_b != n:
        raise ValueError(f"wins_a({wins_a}) + wins_b({wins_b}) != n({n})")
    if n <= 0:
        raise ValueError("n muss > 0 sein")
    parse_units(units, wins_a, n)  # wirft bei Widerspruch zu wins_a/n
    date = date or _date.today().isoformat()
    ensure_csv()
    _migrate_header()
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([date, player_a, sims_a, player_b, sims_b,
                                 wins_a, wins_b, n, comment,
                                 engine_contract() if contract is None else contract,
                                 active_knobs() if knobs is None else knobs,
                                 (units or "").strip(), 1 if early_stop else 0])
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
    """95%-CI je Knoten per nonparametrischem Bootstrap, das BT-Modell je
    Wiederholung neu gefittet, ueber n_boot Wiederholungen die 2.5/97.5-Perzentile.

    Resampling je Match-Zeile:
    - MIT `units` (Seed-Bloecke): Einheiten mit Zuruecklegen ziehen, Siege und
      Partien aufsummieren (Block-Bootstrap; die Korrelation innerhalb eines
      Blocks bleibt erhalten).
    - OHNE `units`: Binomial(n, wins_a/n), also Einzelpartien als unabhaengige
      Bernoulli-Versuche (exakt fuer Referee-Kanten mit einem Seed je Partie,
      zu schmal fuer gepaarte Bloecke ohne Einheiten-Angabe)."""
    if not rows:
        return {}
    rng = _np.random.default_rng(seed) if _np is not None else random.Random(seed)
    units_per_row = [parse_units(r.get("units", ""), r["wins_a"], r["n"]) for r in rows]
    samples = defaultdict(list)
    for b in range(n_boot):
        boot_rows = []
        for r, units in zip(rows, units_per_row):
            if units:
                m = len(units)
                if _np is not None:
                    idx = rng.integers(0, m, m)
                else:
                    idx = [rng.randrange(m) for _ in range(m)]
                wa = int(sum(units[i][0] for i in idx))
                nn = int(sum(units[i][1] for i in idx))
                boot_rows.append({**r, "wins_a": wa, "wins_b": nn - wa, "n": nn})
                continue
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

    edges_total = defaultdict(int)
    edges_early = defaultdict(int)
    for r in rows:
        for node in (node_key(r["player_a"], r["sims_a"]), node_key(r["player_b"], r["sims_b"])):
            edges_total[node] += 1
            edges_early[node] += 1 if r.get("early_stop") else 0
    n_units = sum(1 for r in rows if (r.get("units") or "").strip())
    n_early = sum(1 for r in rows if r.get("early_stop"))

    print(f"=== Mosaic-AI Elo-Tabelle ({len(rows)} Match-Zeilen in {os.path.basename(CSV_PATH)}) ===")
    print(f"{'Modell':<20} {'Elo':>7} {'95%-CI':>18} {'Spiele':>7} {'W-L':>9} {'Frueh':>6}  Status")
    print("-" * 87)

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
        # Ein Knoten mit wenigen Bloecken kann in Bootstrap-Ziehungen ohne einen einzigen
        # Sieg landen (gamma auf dem Boden, Elo -> -2600): dann ist das Intervall keine
        # Aussage, sondern ein Artefakt der Stichprobe. Ausweisen statt drucken.
        if lo is not None and hi - lo > 600:
            ci_str = "degeneriert"
        else:
            ci_str = f"[{lo:.0f}, {hi:.0f}]" if lo is not None else "n/a"
        status = "Anker (fix)" if node == ANCHOR_KEY else ("" if connected else "NICHT mit Anker verbunden!")
        early = f"{edges_early[node]}/{edges_total[node]}"
        print(f"{node:<20} {elo:>7.0f} {ci_str:>18} {total_games:>7} "
              f"{f'{total_wins}-{total_losses}':>9} {early:>6}  {status}")

    print()
    print(f"Bootstrap: {n_units} Zeilen blockweise (units gesetzt), "
          f"{len(rows) - n_units} Zeilen binomial (Einzelpartien oder unbekannt); "
          f"{n_early} Zeilen frueh gestoppt (Spalte Frueh = gestoppte/alle Kanten je Knoten; "
          f"Siegquote dort nach oben verzerrt, nicht korrigiert).")
    print()
    print("Match-Historie:")
    for r in rows:
        a = node_key(r["player_a"], r["sims_a"])
        b = node_key(r["player_b"], r["sims_b"])
        flag = "[FRUEH-STOPP] " if r.get("early_stop") else ""
        units = parse_units(r.get("units", ""), r["wins_a"], r["n"])
        blocks = f" [Bloecke: {len(units)} x {units[0][1]}]" if units else ""
        print(f"  {r['date']}  {flag}{a} {r['wins_a']}:{r['wins_b']} {b}  (n={r['n']}){blocks}  {r['comment']}")


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
    # B3 (2026-08-26): eine Kante gegen ein EINGEFRORENES Artefakt soll sagen
    # koennen, wo ihre Knoepfe stehen. `active_knobs()` liest die
    # Prozessumgebung -- fuer ein Artefakt die falsche Quelle, seine Knoepfe
    # liegen in spec.json. Ohne Angabe bleibt es beim Bestandsverhalten.
    p_add.add_argument("--knobs", default=None,
                       help="Knopf-Herkunft ueberschreiben, z.B. 'spec:hv1_anchor/spec.json'. "
                            "Ohne Angabe: die aktiven MOSAIC_*-Variablen des Prozesses.")

    p_add.add_argument("--units", default="",
                       help="Resampling-Einheiten 'k:w1,w2,...' (k Partien je Seed-Block, "
                            "w_i Siege von A je Block). Leer = Einzelpartien/Binomial.")
    p_add.add_argument("--units-from-paired-artifact", default=None, metavar="JSON",
                       help="units aus einem paired_gating-Artefakt ableiten (ein Block je "
                            "block_seed); schliesst --units aus.")
    p_add.add_argument("--early-stop", action="store_true",
                       help="Kante wurde per Stopp-Regel vor dem festen Umfang beendet "
                            "(SPRT, Binomial-Block-Abbruch); der Report weist sie aus.")

    p_units = sub.add_parser("units", help="units-String aus einem paired_gating-Artefakt drucken")
    p_units.add_argument("--paired-artifact", required=True, metavar="JSON")

    args = ap.parse_args()
    if args.cmd == "report":
        report()
    elif args.cmd == "units":
        print(units_from_paired_artifact(args.paired_artifact))
    elif args.cmd == "add":
        units = args.units
        if args.units_from_paired_artifact:
            if units:
                ap.error("--units und --units-from-paired-artifact schliessen sich aus")
            units = units_from_paired_artifact(args.units_from_paired_artifact)
        add_result(args.player_a, args.sims_a, args.player_b, args.sims_b,
                   args.wins_a, args.wins_b, args.n, date=args.date, comment=args.comment,
                   knobs=args.knobs, units=units, early_stop=args.early_stop)
        report()


if __name__ == "__main__":
    sys.exit(main())
