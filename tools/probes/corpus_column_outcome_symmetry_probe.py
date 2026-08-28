# -*- coding: utf-8 -*-
"""PREREG_heuristic_v2_long_rows.md par.3b.4, Stufe 0 -- Symmetrie-Pruefung.

Frage: trennt der Spaltenbau im hv2-Lehrerkorpus ueberhaupt Sieg von
Niederlage? Der Korpus laeuft mit `hv2` auf BEIDEN Seiten
(PREREG_v22_window.md par.2), also bauen beide -- dann waere das Value-Ziel
bezueglich des Spaltenbaus wegsymmetrisiert und der Value-Kopf koennte ueber
den WERT des Spaltenbaus nichts lernen, obwohl der Korpus ihn im Uebermass
zeigt. Derselbe Mechanismus ist in diesem Projekt schon einmal aufgetreten
(DOSSIER_ownership_head.md Abschnitt 7, Punkt 1: die Bauer-Knoepfe waren ein
Prozess-Schalter ohne Spielerparameter, "nicht das Falsche, sondern nichts").

Das ist eine HERLEITUNG aus der CLI-Zeile, nicht gemessen -- genau darum
diese Sonde. Reine Datenpassage ueber den fertigen Korpus: keine Engine, kein
Netz, nur gespeicherte Record-Felder.

Vorab festgelegte Lesart (par.3b.4):

* **Trennt die Spalten-Differenz den Ausgang NICHT** (punkt-biseriale
  Korrelation, Block-KI schliesst die 0 ein), dann misst das Spalten-Tor
  aus par.3b.2 nur Policy-VERHALTEN, waehrend der Value-Kopf blind bleibt --
  das Tor-Ergebnis ist dann entsprechend zu ETIKETTIEREN, und der
  w1-gegen-w0-Vergleich beantwortet die WERT-Frage nicht.
* **Trennt sie den Ausgang**, ist die Sorge vom Tisch.

Feld-Herkunft, in dieser Sitzung am Code geprueft:

* Endzustand je Partie -- der LETZTE Record mit gesetztem `winner`, gruppiert
  ueber `record["game_id"]` (Muster aus tools/corpus_sanity_check.py:36-56).
* Volle Spalten -- `state["players"][p]["score_geo"]["col_fill"]`, Sechserliste
  des GEBAUTEN Fuellstands (serialize.rs:200); voll heisst `>= 6`, gezaehlt
  wie in corpus_sanity_check.py:79.
* Ausgang -- `record["winner"]` als Spielerindex; Unentschieden (kein 0/1)
  wird gezaehlt und ausgelassen.

Zwei Kennzahlen je Partie, beide gegen denselben Ausgang:

1. `full_columns[0] - full_columns[1]` (volle Spalten, die Primaergroesse der
   Kampagne),
2. `sum(col_fill[0]) - sum(col_fill[1])` (Fuellstands-Differenz -- feiner
   aufgeloest, faengt halbfertige Spalten mit ein).

Ausgewiesen werden je Kennzahl die punkt-biseriale Korrelation gegen den
Ausgang und der Siegermittelwert (Sieger minus Verlierer), beides mit
Block-SE auf DATEI-Ebene (stehende Regel: Score-Auswertungen auf Block-Ebene,
Paar-SEs unterschaetzen massiv).

Aufruf (voller Lauf, exklusiv):
    python -u tools/probes/corpus_column_outcome_symmetry_probe.py

Smoke:
    python -u tools/probes/corpus_column_outcome_symmetry_probe.py --limit 3
"""
import argparse
import json
import math
import pathlib
import statistics as st
import sys
import time

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

from corpus_io import corpus_files, load_records  # noqa: E402

PREREG = "PREREG_heuristic_v2_long_rows.md par.3b.4 (Stufe 0)"

# Ein Spaltenfuellstand von 6 ist eine VOLLE Spalte (corpus_sanity_check.py:79).
FULL_COLUMN_FILL = 6
# Die beiden vorregistrierten Kennzahlen. Reihenfolge = Berichtsreihenfolge.
METRICS = ("full_columns", "col_fill_sum")


def column_stats(player_state):
    """(volle Spalten, Summe der Fuellstaende) einer Seite, oder None.

    None heisst: der Endzustand traegt kein `score_geo.col_fill` -- die Partie
    wird dann gezaehlt und ausgelassen, statt still als 0 einzugehen.
    """
    fills = (player_state.get("score_geo") or {}).get("col_fill")
    if not fills:
        return None
    values = [float(x) for x in fills]
    return (sum(1 for x in values if x >= FULL_COLUMN_FILL), sum(values))


def point_biserial(differences, outcomes):
    """Pearson-Korrelation zwischen einer Differenz und dem 0/1-Ausgang.

    Bei binaerem zweiten Argument ist das die punkt-biseriale Korrelation.
    None, wenn eine der beiden Reihen keine Streuung hat (dann ist sie nicht
    definiert -- das ist ein Befund, kein Fehler).
    """
    n = len(differences)
    if n < 2:
        return None
    mean_d = sum(differences) / n
    mean_o = sum(outcomes) / n
    cov = sum((d - mean_d) * (o - mean_o) for d, o in zip(differences, outcomes))
    var_d = sum((d - mean_d) ** 2 for d in differences)
    var_o = sum((o - mean_o) ** 2 for o in outcomes)
    if var_d <= 0.0 or var_o <= 0.0:
        return None
    return cov / math.sqrt(var_d * var_o)


def block_summary(block_values):
    """Blockmittel, Block-SE, t und 95-Prozent-KI ueber die Datei-Bloecke."""
    blocks = [v for v in block_values if v is not None]
    if not blocks:
        return {"bloecke": 0, "mittel": None, "block_se": None, "t": None,
                "ki_unten": None, "ki_oben": None, "null_im_ki": None}
    mean = sum(blocks) / len(blocks)
    if len(blocks) < 2:
        return {"bloecke": len(blocks), "mittel": mean, "block_se": None,
                "t": None, "ki_unten": None, "ki_oben": None, "null_im_ki": None}
    se = st.stdev(blocks) / math.sqrt(len(blocks))
    half = 1.96 * se
    return {
        "bloecke": len(blocks),
        "mittel": mean,
        "block_se": se,
        "t": (mean / se) if se > 0 else None,
        "ki_unten": mean - half,
        "ki_oben": mean + half,
        "null_im_ki": (mean - half) <= 0.0 <= (mean + half),
    }


class GameCollector:
    """Sammelt je Datei die Partie-Groessen und schliesst sie zu Bloecken.

    Je Datei entsteht EIN Block je Kennzahl und Ablesung; die Datei-Mittel
    sind die Einheiten der Block-SE.
    """

    def __init__(self):
        # Kennzahl -> Liste der Datei-Mittelwerte.
        self.winner_margin_blocks = {m: [] for m in METRICS}
        self.correlation_blocks = {m: [] for m in METRICS}
        # Kennzahl -> gepoolte Rohreihen ueber den ganzen Korpus.
        self.pooled_differences = {m: [] for m in METRICS}
        self.pooled_outcomes = []
        self.games = 0

    def add_file(self, games):
        """`games` = Liste von (differences_je_kennzahl, outcome_player0)."""
        if not games:
            return
        self.games += len(games)
        outcomes = [outcome for _, outcome in games]
        self.pooled_outcomes.extend(outcomes)
        for index, metric in enumerate(METRICS):
            differences = [diffs[index] for diffs, _ in games]
            self.pooled_differences[metric].extend(differences)
            # Sieger minus Verlierer: die Differenz ist auf Spieler 0
            # orientiert, das Vorzeichen dreht sich bei einem Sieg von 1.
            margins = [d if o == 1 else -d for d, o in zip(differences, outcomes)]
            self.winner_margin_blocks[metric].append(sum(margins) / len(margins))
            self.correlation_blocks[metric].append(
                point_biserial(differences, outcomes))

    def report(self, metric):
        return {
            "n_partien": len(self.pooled_differences[metric]),
            "korrelation_gepoolt": point_biserial(self.pooled_differences[metric],
                                                  self.pooled_outcomes),
            "korrelation_block": block_summary(self.correlation_blocks[metric]),
            "sieger_marge_block": block_summary(self.winner_margin_blocks[metric]),
        }


def format_block(summary):
    if summary["mittel"] is None:
        return "keine Bloecke"
    if summary["block_se"] is None:
        return f"{summary['mittel']:+.4f} (nur {summary['bloecke']} Block)"
    return (f"{summary['mittel']:+.4f} +- {1.96 * summary['block_se']:.4f} "
            f"(SE {summary['block_se']:.4f}, t {summary['t']:+.2f}, "
            f"{summary['bloecke']} Bloecke)")


def print_report(metric, report):
    print(f"\nKennzahl {metric}  (n = {report['n_partien']} Partien)")
    pooled = report["korrelation_gepoolt"]
    pooled_text = f"{pooled:+.4f}" if pooled is not None \
        else "nicht definiert (keine Streuung)"
    print(f"  punkt-biserial, gepoolt : {pooled_text}")
    print(f"  punkt-biserial, Bloecke : {format_block(report['korrelation_block'])}")
    print(f"  Sieger minus Verlierer  : {format_block(report['sieger_marge_block'])}")


def verdict_from_report(report):
    """Vorregistrierte Lesart (par.3b.4) auf der Block-Korrelation.

    Schliesst das Block-KI der punkt-biserialen Korrelation die 0 ein, TRENNT
    die Differenz den Ausgang nicht -- dann ist das Spalten-Tor aus par.3b.2
    als reine Verhaltensmessung zu etikettieren.
    """
    block = report["korrelation_block"]
    if block["null_im_ki"] is None:
        return {"verdikt": "UNENTSCHEIDBAR",
                "grund": "zu wenige Bloecke fuer ein Block-KI",
                "null_im_ki": None}
    if block["null_im_ki"]:
        return {"verdikt": "TRENNT NICHT",
                "grund": "Block-KI der punkt-biserialen Korrelation schliesst die 0 ein "
                         "-- par.3b.2 misst nur Policy-Verhalten, das Tor-Ergebnis ist "
                         "entsprechend zu etikettieren",
                "null_im_ki": True}
    return {"verdikt": "TRENNT",
            "grund": "Block-KI schliesst die 0 aus -- die Symmetrie-Sorge ist vom Tisch",
            "null_im_ki": False}


def main():
    parser = argparse.ArgumentParser(description=PREREG)
    parser.add_argument("--data-dir", default="data", help="Korpus-Verzeichnis (relativ)")
    parser.add_argument("--pattern", default="selfplay_hv2_*.pkl", help="Dateimuster")
    parser.add_argument("--limit", type=int, default=0,
                        help="nur die ersten N Dateien (0 = alle); fuer den Smoke")
    parser.add_argument("--out",
                        default="evaluations/artifacts/corpus_column_outcome_symmetry.json")
    parser.add_argument("--progress-every", type=int, default=50,
                        help="Fortschrittszeile alle N Dateien")
    args = parser.parse_args()

    wall_start, cpu_start = time.time(), time.process_time()

    paths = corpus_files(args.data_dir, args.pattern)
    if args.limit:
        paths = paths[:args.limit]
    if not paths:
        print(f"Keine Dateien unter {args.data_dir}/{args.pattern}", flush=True)
        return 1
    print(f"{PREREG}\nDateien: {len(paths)}  ({args.data_dir}/{args.pattern})", flush=True)

    collector = GameCollector()
    counters = {"records": 0, "partien_mit_winner": 0, "gewertet": 0,
                "unentschieden": 0, "ohne_col_fill": 0, "ohne_zwei_spieler": 0}

    for index, path in enumerate(paths, 1):
        finals = {}  # game_id -> letzter Record mit gesetztem winner
        for record in load_records(path):
            counters["records"] += 1
            if record.get("winner") is not None:
                finals[record.get("game_id")] = record
        counters["partien_mit_winner"] += len(finals)

        games = []
        for record in finals.values():
            winner = record.get("winner")
            try:
                winner = int(winner)
            except (TypeError, ValueError):
                counters["unentschieden"] += 1
                continue
            if winner not in (0, 1):
                counters["unentschieden"] += 1
                continue
            players = (record.get("state") or {}).get("players") or []
            if len(players) < 2:
                counters["ohne_zwei_spieler"] += 1
                continue
            first, second = column_stats(players[0]), column_stats(players[1])
            if first is None or second is None:
                counters["ohne_col_fill"] += 1
                continue
            counters["gewertet"] += 1
            # Differenzen IMMER auf Spieler 0 orientiert; der Ausgang traegt
            # das Vorzeichen, nicht die Kennzahl (sonst korreliert die
            # Groesse per Konstruktion mit sich selbst).
            games.append(((first[0] - second[0], first[1] - second[1]),
                          1 if winner == 0 else 0))
        collector.add_file(games)

        if index % args.progress_every == 0 or index == len(paths):
            elapsed = time.time() - wall_start
            print(f"  {index}/{len(paths)} Dateien, {counters['gewertet']} Partien "
                  f"gewertet, {elapsed:.0f} s", flush=True)

    reports = {metric: collector.report(metric) for metric in METRICS}
    for metric in METRICS:
        print_report(metric, reports[metric])

    # Getort wird auf der PRIMAERGROESSE der Kampagne (volle Spalten); die
    # Fuellstands-Differenz laeuft ohne Torfunktion mit.
    verdict = verdict_from_report(reports["full_columns"])
    secondary = verdict_from_report(reports["col_fill_sum"])
    print(f"\nVERDIKT (par.3b.4, Tor auf full_columns): {verdict['verdikt']}")
    print(f"  {verdict['grund']}")
    print(f"  Nebengroesse col_fill_sum (KEIN Tor): {secondary['verdikt']}")
    print(f"\nZaehler: {counters}", flush=True)

    wall = time.time() - wall_start
    cpu = time.process_time() - cpu_start
    result = {
        "prereg": PREREG,
        "korpus": {"verzeichnis": args.data_dir, "muster": args.pattern,
                   "dateien": len(paths), "limit": args.limit},
        "groessen": {
            "full_columns": "Anzahl Spalten mit score_geo.col_fill >= 6 im Endzustand "
                            "(serialize.rs:200; Zaehlweise wie corpus_sanity_check.py)",
            "col_fill_sum": "Summe der sechs col_fill-Werte im Endzustand -- feiner "
                            "aufgeloest, faengt halbfertige Spalten mit ein",
            "differenz": "IMMER Spieler 0 minus Spieler 1; der Ausgang traegt das "
                         "Vorzeichen, nicht die Kennzahl",
            "ausgang": "1, wenn record['winner'] == 0, sonst 0",
            "block": "eine Korpus-DATEI ist ein Block (stehende Regel: Block-Ebene, "
                     "Paar-SEs unterschaetzen massiv)",
        },
        "tor_kennzahl": "full_columns",
        "zaehler": counters,
        "kennzahlen": reports,
        "verdikt": verdict,
        "nebengroesse_col_fill_sum": secondary,
        "laufzeit": {"wanduhr_s": round(wall, 1), "cpu_s": round(cpu, 1), "threads": 1,
                     "s_je_datei": round(wall / max(1, len(paths)), 3)},
    }
    if args.limit:
        result["hinweis"] = (f"SMOKE mit --limit {args.limit}: die Zahlen sind eine "
                             "Formprobe, kein Befund -- die Block-SE steht auf "
                             f"{args.limit} Bloecken.")

    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False),
                        encoding="utf-8", newline="\n")
    print(f"\nArtefakt: {args.out}  (wanduhr {wall:.1f} s, "
          f"{wall / max(1, len(paths)):.3f} s je Datei)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
