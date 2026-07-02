"""
floor_policy_vs_search.py — Diagnose: Flutet die ROHE Policy oder erst die SUCHE?

Frage: Das Netz-Self-Play wirft häufig auf die Strafleiste, obwohl die Heuristik-
Trainingsdaten Reihen-Züge bevorzugen. Liegt das an der gelernten Policy selbst,
oder erst an der MCTS-Suche (Value-Head lenkt die Visits in Floor-Stellungen)?

Vorgehen: Wir sammeln aus Self-Play-Daten die Stellungen, in denen die GESPEICHERTE
Policy (= Visit-Verteilung NACH Suche) einen Strafleisten-Zug als Top-Wahl hatte,
OBWOHL eine Reihen-Alternative verfügbar war. Für genau diese Stellungen fragen wir
das ROHE Netz (evaluate_raw, kein MCTS):
  - Bevorzugt die rohe Policy auch Floor?  → Policy hat Floor gelernt (Lernproblem)
  - Bevorzugt die rohe Policy eine Reihe?   → erst die SUCHE flutet (Value-Head schuld)

Aufruf:
  python -m utils.floor_policy_vs_search --version v1e [ORDNER] [--max 300]

  ORDNER ist optional (Default: data). Beispiele:
    python -m utils.floor_policy_vs_search --version v1e
    python -m utils.floor_policy_vs_search --version v1f data_v1f
    python -m utils.floor_policy_vs_search --version v1e data_v1e --max 500
"""
import argparse
import glob
import pickle
import os

# Strafleisten-Stone-IDs vom Mond (f_idx=5, alle 5 Farben)
PENALTY_MOON_IDS = {15, 63, 111, 159, 207}


def is_floor_action(a: dict) -> bool:
    """Strafleisten-Zug = stone mit row == -1 (landet auf Straffeld)."""
    return a.get("type") == "stone" and a.get("row", 0) == -1


def is_row_action(a: dict) -> bool:
    """Echter Reihen-Zug = stone in eine Musterreihe (row 0..6, nicht -1=Floor)."""
    return a.get("type") == "stone" and a.get("row", -1) >= 0


def top_action_of_policy(policy: list) -> dict:
    """Aktion mit höchster prob in einer gespeicherten Policy-Liste."""
    best, best_p = None, -1.0
    for entry in policy:
        p = entry.get("prob", 0.0)
        if p > best_p:
            best_p, best = p, entry.get("action", {})
    return best or {}


def count_open_rows(state: dict, player_idx: int) -> int:
    """
    Zählt die OFFENEN Musterreihen eines Spielers (begonnen, aber nicht voll) —
    exakt das A2-Maß der Heuristik (shaping.py): 0 < len(tiles) < capacity.
    Die Heuristik bestraft >2 offene Reihen, weil zu viele gleichzeitig offene
    Reihen am Rundenende zwangsläufig zu Strafleisten-Würfen führen (eingehende
    Steine passen nirgends mehr).
    """
    try:
        pl = state["players"][player_idx]
    except (KeyError, IndexError, TypeError):
        return 0
    n = 0
    for row in pl.get("pattern_lines", []):
        tiles = row.get("tiles", [])
        cap = row.get("capacity", row.get("index", 0) + 1)
        if 0 < len(tiles) < cap:
            n += 1
    return n


def analyze_buildup(files, max_steps=200000):
    """
    Modellfreie Buildup-Analyse: Wie viele Musterreihen hält der ziehende Spieler
    gleichzeitig offen? Vergleicht man Netz- vs. Heuristik-Daten, zeigt sich, ob
    das Netz sich durch Über-Öffnen von Reihen in die Floor-Sackgasse manövriert
    (ein Aufbau-/Policy-Problem, das kein Value-Head beheben kann).
    """
    import collections
    dist = collections.Counter()         # open_rows → Häufigkeit (alle Stellungen)
    by_round = collections.defaultdict(list)
    floor_open_rows = []                 # offene Reihen an Floor-Stellungen
    total = 0
    over_threshold = 0                   # Stellungen mit >2 offenen Reihen

    for f in files:
        with open(f, "rb") as fh:
            data = pickle.load(fh)
        for step in data:
            state = step.get("state")
            pl = step.get("player")
            if state is None or pl is None or not isinstance(state, dict):
                continue
            opn = count_open_rows(state, pl)
            dist[opn] += 1
            rnd = state.get("round", 0)
            by_round[rnd].append(opn)
            total += 1
            if opn > 2:
                over_threshold += 1

            # Floor-Stellung? (Suche wählte Floor, keine Reihen-Alternative)
            top = top_action_of_policy(step.get("policy", []))
            valid = step.get("valid_actions", [])
            if is_floor_action(top) and not any(is_row_action(a) for a in valid):
                floor_open_rows.append(opn)

            if total >= max_steps:
                break
        if total >= max_steps:
            break

    return dist, by_round, floor_open_rows, total, over_threshold


def print_buildup(files, label=""):
    dist, by_round, floor_open_rows, total, over_threshold = analyze_buildup(files)
    if total == 0:
        print("  Keine auswertbaren Stellungen.")
        return
    avg = sum(k * v for k, v in dist.items()) / total
    print(f"\n{'='*60}")
    print(f"  BUILDUP-ANALYSE — offene Reihen (A2-Maß){'  ' + label if label else ''}")
    print(f"  {len(files)} Dateien, {total} Stellungen")
    print(f"{'='*60}")
    print(f"  Ø offene Reihen (alle Stellungen): {avg:.2f}")
    print(f"  Anteil >2 offene Reihen (A2-Schwelle): "
          f"{100*over_threshold/total:.1f}%")
    print(f"{'-'*60}")
    print(f"  Verteilung offene Reihen:")
    for k in sorted(dist):
        bar = "█" * int(40 * dist[k] / total)
        print(f"    {k}: {dist[k]:6d} ({100*dist[k]/total:4.1f}%) {bar}")
    print(f"{'-'*60}")
    print(f"  Ø offene Reihen pro Runde (Aufbau wächst, Reset am Rundenende):")
    for r in sorted(by_round):
        vals = by_round[r]
        if vals:
            print(f"    Runde {r}: Ø {sum(vals)/len(vals):.2f} (n={len(vals)})")
    if floor_open_rows:
        fo = sum(floor_open_rows) / len(floor_open_rows)
        print(f"{'-'*60}")
        print(f"  An Floor-Stellungen (Suche→Floor, keine Reihen-Alt):")
        print(f"    Ø offene Reihen: {fo:.2f}  (n={len(floor_open_rows)})")
        print(f"    → Hoch (>2) = Brett verstopft durch Über-Öffnen → Aufbau-Problem")
        print(f"      Niedrig (≤2) = Floor eher strukturell (Steine passen nie)")
    print(f"{'='*60}")


def main():
    ap = argparse.ArgumentParser(
        description="Diagnose: flutet die rohe Policy oder erst die Suche? "
                    "Plus Buildup-Analyse (offene Reihen / A2-Maß). "
                    "Ordner mit den .pkl-Dateien als Argument angeben.")
    ap.add_argument("--version", default=None,
                    help="Netz-Version, z.B. v1e (nur für Policy-vs-Suche nötig)")
    ap.add_argument("data", nargs="?", default="data",
                    help="Ordner mit Self-Play .pkl (Unterordner-Name oder voller "
                         "Pfad). Default: data")
    ap.add_argument("--max", type=int, default=300,
                    help="max. Floor-Stellungen, die geprüft werden (Rechenzeit)")
    ap.add_argument("--buildup-only", action="store_true",
                    help="NUR Buildup-Analyse (offene Reihen), ohne Netz zu laden. "
                         "Für Heuristik-/Bootstrap-Daten ohne Versions-Modell.")
    args = ap.parse_args()

    # Ordner robust auflösen: nimm den Pfad wie angegeben, sonst relativ zum cwd.
    data_dir = args.data
    if not os.path.isdir(data_dir):
        print(f"❌ Ordner nicht gefunden: '{data_dir}'")
        # Hilfestellung: welche Unterordner mit .pkl gibt es?
        candidates = []
        for root, _dirs, files in os.walk("."):
            if any(fn.endswith(".pkl") for fn in files):
                candidates.append(os.path.relpath(root))
        if candidates:
            print("   Ordner mit .pkl-Dateien:")
            for c in sorted(set(candidates))[:15]:
                print(f"     {c}")
        return

    files = sorted(glob.glob(os.path.join(data_dir, "*.pkl")))
    if not files:
        print(f"Keine .pkl in {data_dir}")
        return

    # Buildup-Modus: rein datenbasiert, kein Netz nötig (läuft auf Heuristik-Daten).
    if args.buildup_only:
        print_buildup(files, label=f"({data_dir})")
        return

    # Policy-vs-Suche braucht das Netz.
    if not args.version:
        print("❌ Für die Policy-vs-Suche-Analyse wird --version benötigt.")
        print("   (Oder --buildup-only für die reine Buildup-Analyse ohne Netz.)")
        return

    # Netz laden (lazy, damit das Skript ohne torch zumindest importierbar ist)
    from agents.alphazero import AlphaZeroAgent
    from config import INPUT_SIZE
    agent = AlphaZeroAgent(model_version=args.version, input_size=INPUT_SIZE,
                           simulations=1)  # sims egal, wir nutzen nur evaluate_raw

    _run_policy_vs_search(agent, files, data_dir, args)
    # Buildup-Analyse hängt sich an die Policy-vs-Suche-Analyse an (gleicher Datensatz).
    print_buildup(files, label=f"({data_dir})")


def _run_policy_vs_search(agent, files, data_dir, args):
    # Zähler
    checked = 0            # geprüfte Floor-Stellungen (Suche wählte Floor trotz Reihen-Alt)
    raw_also_floor = 0     # rohe Policy wählt AUCH Floor
    raw_picks_row = 0      # rohe Policy wählt eine REIHE
    raw_picks_other = 0    # rohe Policy wählt etwas anderes (Kuppel/Chip/...)
    sum_floor_prob_raw = 0.0   # Ø rohe Prob, die das Netz dem Floor-Zug gibt
    sum_row_prob_raw = 0.0     # Ø rohe Prob auf die beste Reihen-Alternative

    for f in files:
        if checked >= args.max:
            break
        with open(f, "rb") as fh:
            data = pickle.load(fh)
        for step in data:
            if checked >= args.max:
                break
            policy = step.get("policy", [])
            valid = step.get("valid_actions", [])
            state = step.get("state")
            if not policy or not valid or state is None:
                continue

            # Bedingung: Suche wählte Floor als Top, UND es gab eine Reihen-Alternative
            top = top_action_of_policy(policy)
            if not is_floor_action(top):
                continue
            if not any(is_row_action(a) for a in valid):
                continue  # keine Reihen-Alternative → strukturell erzwungen, überspringen

            # Rohe Netz-Policy auf derselben Stellung
            res = agent.evaluate_raw(state, valid)
            per = res.get("per_action", [])
            if not per:
                continue
            raw_top = per[0]["action"]

            checked += 1
            if is_floor_action(raw_top):
                raw_also_floor += 1
            elif is_row_action(raw_top):
                raw_picks_row += 1
            else:
                raw_picks_other += 1

            # Wieviel rohe Prob gibt das Netz dem Floor-Zug vs. der besten Reihe?
            floor_p = max((e["prob_renormalized"] for e in per
                           if is_floor_action(e["action"])), default=0.0)
            row_p = max((e["prob_renormalized"] for e in per
                         if is_row_action(e["action"])), default=0.0)
            sum_floor_prob_raw += floor_p
            sum_row_prob_raw += row_p

    # Auswertung
    print(f"\n{'='*60}")
    print(f"  FLOOR: ROHE POLICY vs SUCHE — {args.version}")
    print(f"  Daten: {data_dir}  ({len(files)} Dateien)")
    print(f"{'='*60}")
    if checked == 0:
        print("  Keine passenden Floor-Stellungen gefunden (Suche wählte nie Floor")
        print("  bei verfügbarer Reihen-Alternative). Das wäre bereits ein gutes Zeichen.")
        return

    print(f"  Geprüfte Stellungen (Suche→Floor trotz Reihen-Alt): {checked}")
    print(f"{'-'*60}")
    print(f"  Rohe Policy wählt ebenfalls FLOOR : {raw_also_floor:4d}  ({100*raw_also_floor/checked:.1f}%)")
    print(f"  Rohe Policy wählt eine REIHE      : {raw_picks_row:4d}  ({100*raw_picks_row/checked:.1f}%)")
    print(f"  Rohe Policy wählt anderes         : {raw_picks_other:4d}  ({100*raw_picks_other/checked:.1f}%)")
    print(f"{'-'*60}")
    print(f"  Ø rohe Prob auf Floor-Zug         : {sum_floor_prob_raw/checked:.3f}")
    print(f"  Ø rohe Prob auf beste Reihe       : {sum_row_prob_raw/checked:.3f}")
    print(f"{'='*60}")

    # Interpretation
    frac_floor = raw_also_floor / checked
    print("  DEUTUNG:")
    if frac_floor >= 0.6:
        print("  → Die ROHE POLICY flutet selbst. Das Netz hat die Reihen-Präferenz")
        print("    der Heuristik-Daten nicht gelernt. Lern-/Kapazitäts-/Feature-Problem,")
        print("    NICHT die Suche. Hebel: Policy-Training, Repräsentation, mehr Daten.")
    elif frac_floor <= 0.4:
        print("  → Die rohe Policy bevorzugt REIHEN, erst die SUCHE flutet. Der")
        print("    Value-Head lenkt die Visits in Floor-Stellungen. Hebel: Value-Head")
        print("    (z.B. Auxiliary-Floor-Head), nicht die Policy.")
    else:
        print("  → Gemischtes Bild. Beide Anteile relevant — Policy teilweise schwach,")
        print("    Suche verstärkt es. Beide Hebel im Blick behalten.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()