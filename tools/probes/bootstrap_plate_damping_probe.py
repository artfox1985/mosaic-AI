# -*- coding: utf-8 -*-
"""PREREG_heuristic_v2_long_rows.md par.3b.3, Stufe 0 -- VORAB-SONDE.

Frage: unterbewertet die v21-Bootstrap-Haelfte der Value-Ziele den
Spaltenfortschritt? Reine Datenpassage ueber den fertigen Korpus, keine
Engine, kein Netz -- gelesen werden nur gespeicherte Record-Felder.

Vorab festgelegte Lesart (par.3b.3, Zeile 1089-1099): je Record mit
gespeichertem Bootstrap das Residuum `realisierter Ausgang minus Bootstrap`
auf der Gewinnskala [0,1] des ziehenden Spielers bilden, nach dem
Spaltenfortschritt der EIGENEN Seite binnen (`col_f_max`-Maximum, Bins
0-2 / 3 / 4 / 5 / 6) und je Bin n, mittleres Residuum und Block-SE auf
DATEI-Ebene ausweisen. **Daempfung bestaetigt**, wenn das mittlere Residuum
ueber die Bins monoton waechst UND im obersten Bin ueber +0,05 liegt; dann
wird Arm L (TD_LAMBDA-Leiter) Pflichtarm des v22-Trainings.

Feld-Herkunft, alles in dieser Sitzung am Code geprueft:

* `bootstrap_value` -- Liste je Spieler, BEREITS eine [0,1]-
  Gewinnwahrscheinlichkeit (corpus_dataset.py:900-902: "`bootstrap_value` ist
  bereits eine [0,1]-Gewinnwahrscheinlichkeit, hier direkt geblendet"). Nur
  Records mit dem Feld werden gelesen; es wird einmal je RUNDE berechnet und
  auf die Records dieser Runde gestempelt (Runden 1-4, Runde 5 traegt keinen).
* Ziehender Spieler -- `record["player"]`, dieselbe Wahl wie beim Ziel-Bau
  (corpus_dataset.py:804 `p = step["player"]`, dort auch `bv[p]`).
  `state["current_player"]` dient nur als Rueckfall; Abweichungen werden
  gezaehlt und im Artefakt ausgewiesen.
* Ausgang -- `record["winner"]` als Spielerindex, hartes 1/0 aus Sicht von
  `p` (corpus_dataset.py:910). Ein Record zaehlt nur, wenn
  `record.get("completed", True) is not False` (Audit-F2, corpus_dataset.py:802):
  Rust stempelt `scores`/`winner` auch bei Timeout-Abbruch.
* Spaltenfortschritt -- `state["players"][p]["col_f_max"]`, Sechserliste
  (neural_net.py:288-292 liest dasselbe Feld). ACHTUNG bei der Lesart:
  `col_f_max` ist die ERREICHBARE Spaltenfuellung, "Fuellstand + noch
  bedienbare leere Zellen je Spalte, gedeckelt bei 6"
  (serialize.rs:232-234, `plate_builder::achievable_column_fill`) -- der Wert
  startet bei 6 und faellt monoton, er waechst nicht mit dem Bau. Bin 6 heisst
  also "eine volle Spalte ist noch erreichbar", nicht "sechs Zellen liegen".
  Der Bin haengt dadurch mit der Runde zusammen; die Rundentabelle unten ist
  genau dafuer da (ohne Torfunktion).

**Zwei Binnungen, eine davon getort.** Getort wird nach dem Wortlaut der
Registrierung auf `col_f_max`. Gemessen am Smoke faellt dabei fast alles in
Bin 6 (4373 von 4386 Records, 3 Dateien) -- die erreichbare Fuellung bleibt
fast die ganze Partie bei 6, die Bins 0-2/3/4 bleiben leer und die Tabelle
hat kaum Aufloesung. Der GEBAUTE Fuellstand steht daneben im selben Zustand:
`state["players"][p]["score_geo"]["col_fill"]` (serialize.rs:200), und dessen
Maximum belegt alle fuenf Bins (Smoke: 309/186/315/145/298/145/61 auf 0..6).
Beide Tabellen laufen deshalb mit; `col_fill` ist ZUSATZ OHNE TORFUNKTION,
solange die Registrierung `col_f_max` nennt. Ob der Prereg-Text die
erreichbare oder die gebaute Fuellung meinte, entscheidet der Koordinator --
diese Sonde entscheidet es nicht still.

**Zwei Skalen, beide ausgewiesen.** Der Trainingspfad blendet nicht den rohen
Wert: fuer Dateien, deren Basename nicht mit `WDL_GENERATOR_PREFIXES`
("selfplay_v19wdl", "selfplay_v20wdl", neural_net.py:759) beginnt, laeuft
`bvp` zuerst durch die Platt-Entstauchung `_destretch_prob`
(corpus_dataset.py:702 setzt `bootstrap_native`, :917-919 wendet sie an).
`selfplay_hv2_*` faellt NICHT unter die Praefixe, im v22-Ziel steht also der
entstauchte Wert. Getort wird nach dem Wortlaut der Registrierung auf dem
GESPEICHERTEN (rohen) Bootstrap; die entstauchte Tabelle laeuft als zweite
Skala mit, und beide Verdikte stehen im Artefakt. Eine stille Skalenmischung
waere genau der Fehler, den diese Sonde suchen soll.

Aufruf (voller Lauf, exklusiv):
    python -u tools/probes/bootstrap_plate_damping_probe.py

Smoke:
    python -u tools/probes/bootstrap_plate_damping_probe.py --limit 3
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

PREREG = "PREREG_heuristic_v2_long_rows.md par.3b.3 (Stufe 0)"

# Vorregistrierte Bins (par.3b.3) -- als Konstante hier, damit sie in der
# Auswertung nicht nachgeschaerft werden.
BIN_LABELS = ("0-2", "3", "4", "5", "6")
# Vorregistrierte Schwelle fuer den obersten Bin.
TOP_BIN_THRESHOLD = 0.05
# Binnungs-Felder: das REGISTRIERTE zuerst, das Zusatzfeld ohne Torfunktion
# dahinter (siehe Modul-Doku "Zwei Binnungen").
GATING_FIELD = "col_f_max"
EXTRA_FIELD = "col_fill"

# Platt-Entstauchung, identisch zu corpus_dataset._destretch_prob
# (Konstanten aus neural_net.py:760-761). Hier nachgebaut statt importiert,
# damit die Sonde ohne torch/h5py-Abhaengigkeit laeuft.
DESTRETCH_A = 0.0051
DESTRETCH_B = 1.9269


def destretch_prob(p: float) -> float:
    """Platt-Streckung einer gestauchten Alt-Kopf-'Wahrscheinlichkeit'."""
    p = min(max(p, 1e-6), 1.0 - 1e-6)
    z = math.log(p / (1.0 - p))
    return 1.0 / (1.0 + math.exp(-(DESTRETCH_A + DESTRETCH_B * z)))


def column_progress_bin(values) -> str:
    """Bin-Label aus einer Spalten-Sechserliste (Maximum, Bins der Registrierung)."""
    top = int(round(max(float(x) for x in values)))
    if top <= 2:
        return "0-2"
    return str(min(top, 6))


def column_values(player_state, field):
    """Sechserliste je Binnungs-Feld, oder None wenn sie im Zustand fehlt."""
    if field == GATING_FIELD:
        return player_state.get("col_f_max") or None
    return (player_state.get("score_geo") or {}).get("col_fill") or None


class Accumulator:
    """Sammelt Residuen je (Seite, Binnungs-Feld, Skala, Bin) -- global und je Datei.

    Je Datei wird nur (Summe, n) gehalten; die Dateimittel sind die Bloecke
    fuer die Block-SE (stehende Regel: Score-Auswertungen auf Block-Ebene,
    Paar-SEs unterschaetzen massiv).
    """

    def __init__(self):
        self.total = {}        # (side, field, scale, bin) -> [sum, n]
        self.block_means = {}  # (side, field, scale, bin) -> [Dateimittel, ...]
        self.current = {}      # dito, aber nur die laufende Datei

    def add(self, side, field, scale, bin_label, residual):
        for store in (self.total, self.current):
            slot = store.setdefault((side, field, scale, bin_label), [0.0, 0])
            slot[0] += residual
            slot[1] += 1

    def close_file(self):
        for key, (total, n) in self.current.items():
            if n:
                self.block_means.setdefault(key, []).append(total / n)
        self.current = {}

    def table(self, side, field, scale):
        """Bin-Tabelle: n, gepooltes Mittel, Blockmittel, Block-SE, Bloecke."""
        rows = []
        for label in BIN_LABELS:
            total, n = self.total.get((side, field, scale, label), [0.0, 0])
            blocks = self.block_means.get((side, field, scale, label), [])
            block_se = (st.stdev(blocks) / math.sqrt(len(blocks))
                        if len(blocks) >= 2 else None)
            rows.append({
                "bin": label,
                "n": n,
                "mittel_residuum": (total / n) if n else None,
                "block_mittel": (sum(blocks) / len(blocks)) if blocks else None,
                "block_se": block_se,
                "bloecke": len(blocks),
            })
        return rows


def verdict_from_table(rows):
    """Vorregistrierte Entscheidungsregel (par.3b.3) auf einer Bin-Tabelle.

    Monoton wachsend ueber die besetzten Bins UND oberster Bin > +0,05
    => "DAEMPFUNG BESTAETIGT". Der Grenzfall-Ausweis meldet, wenn genau ein
    Kriterium haelt oder wenn die Schwelle innerhalb einer Block-SE liegt --
    dann traegt die Sonde die Entscheidung nicht allein.
    """
    filled = [r for r in rows if r["n"] > 0 and r["mittel_residuum"] is not None]
    if not filled:
        return {"verdikt": "KEINE DATEN", "monoton": None, "oberster_bin": None,
                "oberster_bin_ueber_schwelle": None, "grenzfall": None,
                "grenzfall_grund": "keine besetzten Bins"}
    means = [r["mittel_residuum"] for r in filled]
    monotone = all(a <= b for a, b in zip(means, means[1:]))
    strictly_monotone = all(a < b for a, b in zip(means, means[1:]))
    top = filled[-1]
    above = top["mittel_residuum"] > TOP_BIN_THRESHOLD
    confirmed = monotone and above
    reasons = []
    if monotone != above:
        reasons.append("nur eines der beiden Kriterien haelt")
    if top["block_se"] is not None and \
            abs(top["mittel_residuum"] - TOP_BIN_THRESHOLD) < top["block_se"]:
        reasons.append("oberster Bin liegt innerhalb einer Block-SE der Schwelle")
    if len(filled) < len(BIN_LABELS):
        reasons.append(f"nur {len(filled)} von {len(BIN_LABELS)} Bins besetzt")
    return {
        "verdikt": "DAEMPFUNG BESTAETIGT" if confirmed else "DAEMPFUNG NICHT BESTAETIGT",
        "monoton": monotone,
        "streng_monoton": strictly_monotone,
        "oberster_bin": top["bin"],
        "oberster_bin_mittel": top["mittel_residuum"],
        "oberster_bin_block_se": top["block_se"],
        "oberster_bin_ueber_schwelle": above,
        "schwelle": TOP_BIN_THRESHOLD,
        "grenzfall": bool(reasons),
        "grenzfall_grund": "; ".join(reasons) if reasons else "",
    }


def print_table(title, rows):
    print(f"\n{title}")
    print("  Bin    |      n | Mittel-Res | Blockmittel | Block-SE | Bloecke")
    for r in rows:
        if r["n"] == 0:
            print(f"  {r['bin']:<6} |      0 |          - |           - |        - |       0")
            continue
        se = f"{r['block_se']:8.4f}" if r["block_se"] is not None else "       -"
        print(f"  {r['bin']:<6} | {r['n']:6d} | {r['mittel_residuum']:+10.4f} | "
              f"{r['block_mittel']:+11.4f} | {se} | {r['bloecke']:7d}")


def main():
    parser = argparse.ArgumentParser(description=PREREG)
    parser.add_argument("--data-dir", default="data", help="Korpus-Verzeichnis (relativ)")
    parser.add_argument("--pattern", default="selfplay_hv2_*.pkl", help="Dateimuster")
    parser.add_argument("--limit", type=int, default=0,
                        help="nur die ersten N Dateien (0 = alle); fuer den Smoke")
    parser.add_argument("--out", default="evaluations/artifacts/bootstrap_plate_damping.json")
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

    acc = Accumulator()
    round_totals = {}   # Runde -> [sum, n], eigene Seite, rohe Skala
    counters = {"records": 0, "mit_bootstrap": 0, "gewertet": 0,
                "ohne_bootstrap": 0, "abgebrochen": 0, "ohne_winner": 0,
                "ohne_col_f_max": 0, "player_abweichung": 0, "unentschieden": 0}

    for index, path in enumerate(paths, 1):
        for record in load_records(path):
            counters["records"] += 1
            bootstrap = record.get("bootstrap_value")
            if bootstrap is None or len(bootstrap) < 2:
                counters["ohne_bootstrap"] += 1
                continue
            counters["mit_bootstrap"] += 1
            if record.get("completed", True) is False:
                counters["abgebrochen"] += 1
                continue
            winner = record.get("winner")
            if winner is None:
                counters["ohne_winner"] += 1
                continue
            state = record.get("state") or {}
            mover = record.get("player")
            if mover is None:
                mover = state.get("current_player")
            if mover is None:
                counters["ohne_winner"] += 1
                continue
            mover = int(mover)
            if state.get("current_player") is not None and \
                    int(state["current_player"]) != mover:
                counters["player_abweichung"] += 1
            winner = int(winner)
            if winner not in (0, 1):
                counters["unentschieden"] += 1
                continue
            players = state.get("players") or []
            if len(players) < 2 or column_values(players[mover], GATING_FIELD) is None \
                    or column_values(players[1 - mover], GATING_FIELD) is None:
                counters["ohne_col_f_max"] += 1
                continue

            counters["gewertet"] += 1
            sides = (("eigen", mover), ("gegner", 1 - mover))
            for side, player_index in sides:
                outcome = 1.0 if winner == player_index else 0.0
                raw = float(bootstrap[player_index])
                residuals = {"roh": outcome - raw,
                             "entstaucht": outcome - destretch_prob(raw)}
                for field in (GATING_FIELD, EXTRA_FIELD):
                    values = column_values(players[player_index], field)
                    if values is None:
                        if side == "eigen" and field == EXTRA_FIELD:
                            counters["ohne_col_fill"] += 1
                        continue
                    bin_label = column_progress_bin(values)
                    for scale, residual in residuals.items():
                        acc.add(side, field, scale, bin_label, residual)
                if side == "eigen":
                    game_round = int(state.get("round", 0))
                    slot = round_totals.setdefault(game_round, [0.0, 0])
                    slot[0] += outcome - raw
                    slot[1] += 1
        acc.close_file()
        if index % args.progress_every == 0 or index == len(paths):
            elapsed = time.time() - wall_start
            print(f"  {index}/{len(paths)} Dateien, {counters['gewertet']} Records "
                  f"gewertet, {elapsed:.0f} s", flush=True)

    tables = {side: {scale: acc.table(side, scale) for scale in ("roh", "entstaucht")}
              for side in ("eigen", "gegner")}
    verdict = verdict_from_table(tables["eigen"]["roh"])
    verdict_destretched = verdict_from_table(tables["eigen"]["entstaucht"])
    sanity_opponent = verdict_from_table(tables["gegner"]["roh"])

    print_table("EIGENE Seite, roher gespeicherter Bootstrap (TOR-Tabelle)",
                tables["eigen"]["roh"])
    print_table("EIGENE Seite, entstaucht (Skala des Trainingsziels, KEIN Tor)",
                tables["eigen"]["entstaucht"])
    print_table("GEGNER-Seite, roh (Sanity: Daempfung sollte seitensymmetrisch sein)",
                tables["gegner"]["roh"])

    round_rows = [{"runde": r, "n": n, "mittel_residuum": total / n}
                  for r, (total, n) in sorted(round_totals.items()) if n]
    print("\nEigene Seite je Runde (roh, KEIN Tor -- Bin-Runde-Konfundierung, siehe Doku)")
    for row in round_rows:
        print(f"  Runde {row['runde']}: n {row['n']:6d}  Mittel {row['mittel_residuum']:+.4f}")

    print(f"\nVERDIKT (par.3b.3, rohe Skala): {verdict['verdikt']}")
    print(f"  monoton: {verdict['monoton']}   oberster Bin {verdict['oberster_bin']}: "
          f"{verdict['oberster_bin_mittel']:+.4f} (Schwelle +{TOP_BIN_THRESHOLD})")
    if verdict["grenzfall"]:
        print(f"  GRENZFALL: {verdict['grenzfall_grund']}")
    print(f"  Zweitskala (entstaucht): {verdict_destretched['verdikt']}")

    wall = time.time() - wall_start
    cpu = time.process_time() - cpu_start
    result = {
        "prereg": PREREG,
        "korpus": {"verzeichnis": args.data_dir, "muster": args.pattern,
                   "dateien": len(paths), "limit": args.limit},
        "skalen": {
            "bootstrap_roh": "record['bootstrap_value'][p], bereits [0,1]-Gewinnwahrscheinlichkeit "
                             "(corpus_dataset.py:900-902)",
            "bootstrap_entstaucht": "destretch_prob(bootstrap_roh), Platt A=0,0051 B=1,9269 -- "
                                    "der Trainingspfad wendet das auf selfplay_hv2_* AN, weil der "
                                    "Basename nicht unter WDL_GENERATOR_PREFIXES faellt "
                                    "(corpus_dataset.py:702/917-919, neural_net.py:759)",
            "ausgang": "1/0 aus Sicht des ziehenden Spielers record['player'] "
                       "(corpus_dataset.py:804/910)",
            "residuum": "Ausgang minus Bootstrap, beides auf der Gewinnskala [0,1]",
            "bin": "max(state['players'][p]['col_f_max']) -- ERREICHBARE Spaltenfuellung "
                   "(serialize.rs:232-234), faellt ueber die Partie, startet bei 6",
        },
        "zaehler": counters,
        "tabellen": tables,
        "runden_eigen_roh": round_rows,
        "verdikt": verdict,
        "verdikt_entstaucht": verdict_destretched,
        "sanity_gegner_roh": sanity_opponent,
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
