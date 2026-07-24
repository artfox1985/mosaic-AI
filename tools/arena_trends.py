"""Mosaic-AI — Arena-Trend-Log (Task #92, 2026-07-24, Nutzer-Anstoss).

Persistiert je Arena-/Gating-Lauf EINE CSV-Zeile aus Sicht des Kandidaten-
Modells nach `evaluations/arena_trends.csv` (append-only, Header legt sich
beim ersten Aufruf selbst an). Motivation: Elo/Winrate sagen nur "staerker
oder schwaecher", nicht ob die Partien selbst besser werden -- dieses Log
macht die durchschnittliche Punktzahl und die Floor-Strafen ueber die Zeit
sichtbar (Ziel: mehr Punkte, weniger Floor, als Qualitaetstrend zusaetzlich
zum Elo).

Wird von `tools/paired_gating.py` (Quelle "paired_gating") und
`tools/arena.py` (Quelle "arena_anchor" fuer Netz-vs-Heuristik-Anker,
"sonstige" fuer Netz-vs-Netz-Generationenvergleiche) nach jedem
abgeschlossenen Lauf aufgerufen. Reine Ergaenzung -- bestehende
Konsolenausgaben/Rueckgabewerte der aufrufenden Skripte bleiben
unveraendert.

## CSV-Schema

    iso_datum, quelle, modell, gegner, sims, n_spiele, winrate,
    avg_score, avg_score_gegner, avg_floor, avg_floor_gegner, zerozero_anteil

Eine Zeile je Lauf aus Sicht des Kandidaten (`modell`); `gegner` ist die
Referenzseite. `zerozero_anteil` = Anteil der Spiele, in denen BEIDE Seiten
0 Punkte erreichen (degeneriertes Spiel/Floor-Flut, siehe `arena.py`).

## CLI

    python tools/arena_trends.py report [--model NAME] [--quelle Q] [--csv PFAD]

druckt die CSV chronologisch (Einfuegereihenfolge = Aufruf-Reihenfolge) als
kompakte Tabelle, optional gefiltert.
"""
import csv
import argparse
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "evaluations" / "arena_trends.csv"

FIELDNAMES = [
    "iso_datum", "quelle", "modell", "gegner", "sims", "n_spiele",
    "winrate", "avg_score", "avg_score_gegner", "avg_floor",
    "avg_floor_gegner", "zerozero_anteil",
]


def _round_or_blank(v, ndigits):
    if v is None or v == "":
        return ""
    return round(v, ndigits)


def append_run(quelle, modell, gegner, sims, n_spiele, winrate, avg_score,
                avg_score_gegner, avg_floor, avg_floor_gegner,
                zerozero_anteil, csv_path=None, iso_datum=None):
    """Haengt EINE Zeile an die Trend-CSV an (Header selbstanlegend, falls die
    Datei noch nicht existiert oder leer ist). Bei `n_spiele<=0` (leerer/
    abgebrochener Lauf) wird bewusst NICHTS geschrieben und `None`
    zurueckgegeben -- kein Divide-by-Zero-Risiko beim Aufrufer, keine
    bedeutungslosen Zeilen im Log. Gibt sonst das geschriebene Zeilen-Dict
    zurueck (z.B. zum Einbetten ins Ergebnis-JSON des Aufrufers)."""
    if not n_spiele or n_spiele <= 0:
        return None
    path = Path(csv_path) if csv_path else CSV_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    is_new = (not path.exists()) or path.stat().st_size == 0
    row = {
        "iso_datum": iso_datum or datetime.now().isoformat(timespec="seconds"),
        "quelle": quelle,
        "modell": modell,
        "gegner": gegner,
        "sims": sims if sims is not None else "",
        "n_spiele": n_spiele,
        "winrate": _round_or_blank(winrate, 4),
        "avg_score": _round_or_blank(avg_score, 3),
        "avg_score_gegner": _round_or_blank(avg_score_gegner, 3),
        "avg_floor": _round_or_blank(avg_floor, 3),
        "avg_floor_gegner": _round_or_blank(avg_floor_gegner, 3),
        "zerozero_anteil": _round_or_blank(zerozero_anteil, 4),
    }
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if is_new:
            writer.writeheader()
        writer.writerow(row)
    return row


def _read_rows(csv_path=None):
    path = Path(csv_path) if csv_path else CSV_PATH
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _fmt(v):
    return v if v not in (None, "") else "—"


def _fmt_pct(v):
    try:
        return f"{float(v) * 100:5.1f}"
    except (ValueError, TypeError):
        return "  n/a"


def report(model=None, quelle=None, csv_path=None):
    """Druckt die (ggf. gefilterte) Trend-CSV in chronologischer
    Einfuegereihenfolge als feste-Breite-Tabelle auf stdout."""
    rows = _read_rows(csv_path)
    if model:
        rows = [r for r in rows if r["modell"] == model]
    if quelle:
        rows = [r for r in rows if r["quelle"] == quelle]
    if not rows:
        print("Keine Zeilen in der Arena-Trend-CSV "
              f"({csv_path or CSV_PATH}) -- ggf. Filter zu eng oder Log noch leer.")
        return
    hdr = (f"{'Datum':<20} {'Quelle':<20} {'Modell':<22} {'Gegner':<22} "
           f"{'Sims':>5} {'N':>5} {'Win%':>6} {'Score':>7} {'ScoreG':>7} "
           f"{'Floor':>7} {'FloorG':>7} {'0:0%':>6}")
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        print(f"{r['iso_datum']:<20} {r['quelle']:<20} {r['modell']:<22} {r['gegner']:<22} "
              f"{_fmt(r['sims']):>5} {_fmt(r['n_spiele']):>5} {_fmt_pct(r['winrate']):>6} "
              f"{_fmt(r['avg_score']):>7} {_fmt(r['avg_score_gegner']):>7} "
              f"{_fmt(r['avg_floor']):>7} {_fmt(r['avg_floor_gegner']):>7} "
              f"{_fmt_pct(r['zerozero_anteil']):>6}")
    print(f"\n({len(rows)} Zeile(n) aus {csv_path or CSV_PATH})")


def main():
    p = argparse.ArgumentParser(description="Arena-Trend-Log (Task #92)")
    sub = p.add_subparsers(dest="cmd", required=True)
    rep = sub.add_parser("report", help="Trend-CSV als Tabelle drucken")
    rep.add_argument("--model", default=None, help="Nur Zeilen mit diesem Modellnamen (Spalte 'modell')")
    rep.add_argument("--quelle", default=None, help="Nur Zeilen mit dieser Quelle")
    rep.add_argument("--csv", default=None, help="Alternativer CSV-Pfad (Default: evaluations/arena_trends.csv)")
    args = p.parse_args()
    if args.cmd == "report":
        report(model=args.model, quelle=args.quelle, csv_path=args.csv)


if __name__ == "__main__":
    main()
