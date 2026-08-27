# -*- coding: utf-8 -*-
"""PREREG_heuristic_v2_long_rows.md par.3b.3, Stufe 0 -- VORAB-SONDE.

Frage: unterbewertet die v21-Bootstrap-Haelfte der Value-Ziele den
Spaltenfortschritt? Reine Datenpassage ueber den fertigen Korpus, keine
Engine, kein Netz -- gelesen werden nur gespeicherte Record-Felder.

Vorab festgelegte Lesart (par.3b.3, in der BERICHTIGTEN Fassung "Nachtrag
Stufe 0" vom 2026-08-27): je Record mit gespeichertem Bootstrap das Residuum
`realisierter Ausgang minus Bootstrap` auf der Gewinnskala [0,1] des
ziehenden Spielers bilden, nach dem Spaltenfortschritt der EIGENEN Seite
binnen (Maximum des GEBAUTEN Fuellstands `col_fill`, Bins
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
* Spaltenfortschritt (TOR) -- `state["players"][p]["score_geo"]["col_fill"]`,
  Sechserliste, der GEBAUTE Fuellstand je Spalte (serialize.rs:200). Sein
  Maximum ist das Binnungsfeld der berichtigten Registrierung.

**Zwei Binnungen, eine davon getort -- die Zuordnung ist am 2026-08-27
GEWECHSELT.** Die Erstfassung der Registrierung nannte `col_f_max`; der
Sondenbau hat gezeigt, dass das die ERREICHBARE Fuellung ist, "Fuellstand +
noch bedienbare leere Zellen je Spalte, gedeckelt bei 6"
(serialize.rs:232-234, `plate_builder::achievable_column_fill`) -- der Wert
startet bei 6 und FAELLT, er waechst nicht mit dem Bau. Als Fortschritts-Bin
hatte er fast keine Aufloesung (Smoke: 4373 von 4386 Records in Bin 6). Der
Nutzer hat daraufhin auf den GEBAUTEN Fuellstand berichtigt (par.3b.3,
"Nachtrag Stufe 0" Punkt 1): getort wird auf `max(score_geo.col_fill)`, Bins
unveraendert; die `col_f_max`-Tabelle laeuft als ZUSATZ OHNE TORFUNKTION mit
(sie bleibt lesenswert, weil ihr Bin mit der Runde zusammenhaengt -- dafuer
ist auch die Rundentabelle unten da).

**Eine Zielskala, plus eine Vergleichsspalte.** Seit dem Umbau vom
2026-08-27 (par.3b.3 "Nachtrag Stufe 0" Punkt 3) ist NATIV der Default: der
Trainingspfad blendet den ROHEN gespeicherten `bootstrap_value` in
`values_wdl`, und entstaucht nur noch Dateien der Blockliste
`LEGACY_STRETCHED_PREFIXES` (tanh-Aera v10b/v12/v16/v17/v18,
neural_net.py). `selfplay_hv2_*` steht nicht darin -- **fuer diesen Korpus
sind ziel-aequivalente und rohe Skala also dasselbe**, und der Punkt 2 der
Berichtigung ("torte auf der ziel-aequivalenten Skala") ist damit
gegenstandslos vereinfacht.

Die entstauchte Tabelle laeuft weiter mit, aber NUR noch als klar etikettierte
Vergleichsspalte "so haette der ALTE Pfad geblendet" -- sie zeigt, wie gross
der behobene Fehler in dieser Auswertung gewesen waere. Sie hat keine
Torfunktion.

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
# Binnungs-Felder: das REGISTRIERTE (berichtigte) zuerst, das Zusatzfeld ohne
# Torfunktion dahinter (siehe Modul-Doku "Zwei Binnungen").
GATING_FIELD = "col_fill"
EXTRA_FIELD = "col_f_max"

# Platt-Entstauchung, identisch zu corpus_dataset._destretch_prob. Sie ist
# fuer diesen Korpus ALT-MECHANIK (hv2 ist nativ, siehe Modul-Doku) und
# liefert hier nur noch die Vergleichsspalte. Hier nachgebaut statt
# importiert, damit die Sonde ohne torch/h5py-Abhaengigkeit laeuft.
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
    """Sechserliste je Binnungs-Feld, oder None wenn sie im Zustand fehlt.

    Auf den FELDNAMEN geprueft, nicht auf `field == GATING_FIELD`: sonst
    wandert die Feld-Herkunft mit, sobald das Tor auf das andere Feld
    wechselt -- genau das ist am 2026-08-27 passiert.
    """
    if field == "col_f_max":
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
                # nach dem TOR-Feld benannt (seit 2026-08-27 col_fill); der
                # Zaehler fuer das Zusatzfeld fehlte bisher ganz und haette
                # beim ersten Treffer einen KeyError geworfen.
                f"ohne_{GATING_FIELD}": 0, f"ohne_{EXTRA_FIELD}": 0,
                "player_abweichung": 0, "unentschieden": 0}

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
                counters[f"ohne_{GATING_FIELD}"] += 1
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
                            counters[f"ohne_{EXTRA_FIELD}"] += 1
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

    # Die Sammlung laeuft je (Seite, FELD, Skala) -- der Akkumulator wollte
    # das immer schon (`table(side, field, scale)`), nur der Aufruf hier hat
    # das Feld unterschlagen (TypeError). Beide Felder werden ausgewiesen,
    # getort wird GATING_FIELD.
    tables = {side: {field: {scale: acc.table(side, field, scale)
                             for scale in ("roh", "entstaucht")}
                     for field in (GATING_FIELD, EXTRA_FIELD)}
              for side in ("eigen", "gegner")}
    verdict = verdict_from_table(tables["eigen"][GATING_FIELD]["roh"])
    verdict_destretched = verdict_from_table(tables["eigen"][GATING_FIELD]["entstaucht"])
    sanity_opponent = verdict_from_table(tables["gegner"][GATING_FIELD]["roh"])

    print_table(f"EIGENE Seite, Bin={GATING_FIELD}, roher Bootstrap "
                "(TOR-Tabelle; roh == Zielskala, hv2 ist nativ)",
                tables["eigen"][GATING_FIELD]["roh"])
    print_table(f"EIGENE Seite, Bin={GATING_FIELD}, entstaucht "
                "(VERGLEICH: so haette der ALTE Pfad geblendet, KEIN Tor)",
                tables["eigen"][GATING_FIELD]["entstaucht"])
    print_table(f"EIGENE Seite, Bin={EXTRA_FIELD}, roh "
                "(Zusatzfeld ohne Torfunktion, siehe Modul-Doku)",
                tables["eigen"][EXTRA_FIELD]["roh"])
    print_table(f"GEGNER-Seite, Bin={GATING_FIELD}, roh "
                "(Sanity: Daempfung sollte seitensymmetrisch sein)",
                tables["gegner"][GATING_FIELD]["roh"])

    round_rows = [{"runde": r, "n": n, "mittel_residuum": total / n}
                  for r, (total, n) in sorted(round_totals.items()) if n]
    print("\nEigene Seite je Runde (roh, KEIN Tor -- Bin-Runde-Konfundierung, siehe Doku)")
    for row in round_rows:
        print(f"  Runde {row['runde']}: n {row['n']:6d}  Mittel {row['mittel_residuum']:+.4f}")

    print(f"\nVERDIKT (par.3b.3, Bin={GATING_FIELD}, Zielskala = Rohwert): "
          f"{verdict['verdikt']}")
    print(f"  monoton: {verdict['monoton']}   oberster Bin {verdict['oberster_bin']}: "
          f"{verdict['oberster_bin_mittel']:+.4f} (Schwelle +{TOP_BIN_THRESHOLD})")
    if verdict["grenzfall"]:
        print(f"  GRENZFALL: {verdict['grenzfall_grund']}")
    print(f"  Vergleich (Alt-Pfad, entstaucht -- KEIN Tor): "
          f"{verdict_destretched['verdikt']}")

    wall = time.time() - wall_start
    cpu = time.process_time() - cpu_start
    result = {
        "prereg": PREREG,
        "korpus": {"verzeichnis": args.data_dir, "muster": args.pattern,
                   "dateien": len(paths), "limit": args.limit},
        "skalen": {
            "bootstrap_roh": "record['bootstrap_value'][p], bereits [0,1]-Gewinnwahrscheinlichkeit "
                             "-- seit dem Umbau vom 2026-08-27 zugleich die ZIELSKALA: nativ ist "
                             "der Default, entstaucht wird nur LEGACY_STRETCHED_PREFIXES "
                             "(v10b/v12/v16/v17/v18), und selfplay_hv2_* steht nicht darin",
            "bootstrap_entstaucht": "destretch_prob(bootstrap_roh), Platt A=0,0051 B=1,9269 -- "
                                    "VERGLEICHSSPALTE ohne Torfunktion: so haette der ALTE Pfad "
                                    "(Entstauchung als Default) diesen Korpus geblendet",
            "ausgang": "1/0 aus Sicht des ziehenden Spielers record['player'] "
                       "(corpus_dataset.py, WDL-Zweig)",
            "residuum": "Ausgang minus Bootstrap, beides auf der Gewinnskala [0,1]",
            "bin_tor": "max(state['players'][p]['score_geo']['col_fill']) -- GEBAUTER "
                       "Spaltenfuellstand (serialize.rs:200), Binnungsfeld der berichtigten "
                       "Registrierung",
            "bin_zusatz": "max(state['players'][p]['col_f_max']) -- ERREICHBARE Spaltenfuellung "
                          "(serialize.rs:232-234), faellt ueber die Partie, startet bei 6; "
                          "OHNE Torfunktion",
        },
        "tor_feld": GATING_FIELD,
        "zusatz_feld": EXTRA_FIELD,
        "zaehler": counters,
        "tabellen": tables,
        "runden_eigen_roh": round_rows,
        "verdikt": verdict,
        "vergleich_altpfad_entstaucht": verdict_destretched,
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
