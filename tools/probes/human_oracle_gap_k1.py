# -*- coding: utf-8 -*-
"""Auswertung PREREG_human_game_oracle_gap.md par.4/par.5: k1-relevant vs neutral.

Frage: bewertet der Champion die PLATTENBAUENDEN Zuege eines Menschen
systematisch schlechter (falsches Vorzeichen) -- oder Menschen-Zuege allgemein
(Staerke-Effekt)? Erfolgsregel par.5 ist deshalb eine DIFFERENZ innerhalb
desselben Spielers: mittlerer Delta-win% der k1-relevanten Menschen-Zuege gegen
den der neutralen Zuege, gepaart je Partie, einseitig, p < 0,05, plus
Vorzeichen-Mehrheit ueber die Einzelpartien.

KLASSIFIKATION (par.4, operativ): ein Drafting-Zug (kind == "stone") heisst
k1-relevant, wenn die genommene Farbe von mindestens einer noch
UNVOLLSTAENDIGEN und noch VOLLENDBAREN Spalte des Ziehenden gebraucht wird --
Vollendbarkeit aus `mosaic_rust.plate_completability_json`
(`column_build::column_is_completable`), Farbbedarf aus den offenen
Normal-Zellen (`col_open_cells`, Bedarf > 0). Alle uebrigen bewerteten Zuege
heissen neutral. Wild-Fliesen ("bunt") fordern keine Farbe und zaehlen als
neutral; ihre Anzahl wird getrennt ausgewiesen.

EINGABEN je Partie (beide aus `tools/analyze_game_log.py`):
  --oracle-json  JSONL der Oracle-Records (Champion @400)
  --dump-states  JSONL der Zustaende VOR jedem Entscheidungspunkt (mit
                 `fields`, also der genommenen Farbe)
Der Mensch-Index kommt aus dem Log-Header (`ai_player`).

    python -X utf8 tools/probes/human_oracle_gap_k1.py \
        --dumps "<scratch>/dumps" --logs "static/log"
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import statistics
from pathlib import Path

BASIS = Path(__file__).resolve().parents[2]

FARBE_IDX = {"blau": 0, "gelb": 1, "rot": 2, "schwarz": 3, "türkis": 4}

# einseitige 5-%-Quantile der t-Verteilung, df = n_partien - 1
T_KRIT_EINSEITIG = {2: 2.920, 3: 2.353, 4: 2.132, 5: 2.015, 6: 1.943, 7: 1.895,
                    8: 1.860, 9: 1.833, 10: 1.812}


def lies_header(log_pfad: Path) -> dict:
    with open(log_pfad, encoding="utf-8") as fh:
        fh.readline()
        return json.loads(fh.readline().lstrip("# ").strip())


def klassifiziere(mr, state: dict, spieler: int, farbe: str) -> tuple[str, dict]:
    """'k1' | 'neutral' | 'wild' plus Detail fuer das Protokoll."""
    idx = FARBE_IDX.get(farbe)
    if idx is None:
        return "wild", {}
    d = json.loads(mr.plate_completability_json(json.dumps(state), spieler))
    for c in range(6):
        if not d["columns"][c] or d["col_fill"][c] >= 6:
            continue
        for z in d["col_open_cells"][c]:
            if z.get("kind") == "normal" and z.get("color_idx") == idx and z.get("need", 0) > 0:
                return "k1", {"spalte": c, "fill": d["col_fill"][c]}
    return "neutral", {}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dumps", required=True,
                    help="Verzeichnis mit game_*.jsonl und oracle_game_*.jsonl")
    ap.add_argument("--logs", default="static/log")
    a = ap.parse_args()

    import mosaic_rust as mr  # noqa: PLC0415

    games = []
    for orakel_pfad in sorted(glob.glob(str(Path(a.dumps) / "oracle_game_*.jsonl"))):
        stem = Path(orakel_pfad).stem.removeprefix("oracle_")
        dump_pfad = Path(a.dumps) / f"{stem}.jsonl"
        log_pfad = BASIS / a.logs / f"{stem}.log"
        if not dump_pfad.exists() or not log_pfad.exists():
            print(f"  UEBERSPRUNGEN (Dump/Log fehlt): {stem}")
            continue
        header = lies_header(log_pfad)
        mensch = 1 - int(header["ai_player"])

        dumps = {}
        for line in open(dump_pfad, encoding="utf-8"):
            d = json.loads(line)
            dumps[d["turn"]] = d

        deltas = {"k1": [], "neutral": []}
        wild = 0
        groesste = []
        for line in open(orakel_pfad, encoding="utf-8"):
            rec = json.loads(line)
            if not rec.get("evaluated") or rec.get("actor") != mensch:
                continue
            dwin = rec.get("delta_win_pct")
            if dwin is None:
                continue
            klasse = "neutral"
            det = {}
            dump = dumps.get(rec["turn_idx"])
            if rec.get("kind") == "stone" and dump is not None:
                farbe = (dump.get("fields") or {}).get("color")
                if farbe is not None:
                    klasse, det = klassifiziere(mr, dump["state"], mensch, farbe)
            if klasse == "wild":
                wild += 1
                klasse = "neutral"
            deltas[klasse].append(dwin)
            if klasse == "k1":
                groesste.append((dwin, rec["round_num"], rec["played_desc"], det))

        if not deltas["k1"] or not deltas["neutral"]:
            print(f"  {stem}: keine k1-relevanten ({len(deltas['k1'])}) oder keine "
                  f"neutralen ({len(deltas['neutral'])}) Zuege -- Partie ohne Paar-Differenz")
        m_k1 = statistics.mean(deltas["k1"]) if deltas["k1"] else None
        m_ne = statistics.mean(deltas["neutral"]) if deltas["neutral"] else None
        groesste.sort(reverse=True)
        games.append({
            "partie": stem, "mensch_idx": mensch,
            "n_k1": len(deltas["k1"]), "n_neutral": len(deltas["neutral"]), "n_wild": wild,
            "mittel_k1": m_k1, "mittel_neutral": m_ne,
            "differenz": (m_k1 - m_ne) if (m_k1 is not None and m_ne is not None) else None,
            "groesste_k1_abweichungen": [
                {"delta_win_pct": g[0], "runde": g[1], "zug": g[2], **g[3]} for g in groesste[:3]
            ],
        })

    print("\n  Partie                              | n_k1 | n_neu | wild | Mittel k1 | Mittel neu | Differenz")
    print("  ------------------------------------+------+-------+------+-----------+------------+----------")
    for p in games:
        d = p["differenz"]
        print(f"  {p['partie']:36}| {p['n_k1']:4} | {p['n_neutral']:5} | {p['n_wild']:4} |"
              f" {p['mittel_k1'] if p['mittel_k1'] is not None else float('nan'):9.2f} |"
              f" {p['mittel_neutral'] if p['mittel_neutral'] is not None else float('nan'):10.2f} |"
              f" {d if d is not None else float('nan'):8.2f}")

    diffs = [p["differenz"] for p in games if p["differenz"] is not None]
    verdikt = {"n_partien": len(diffs)}
    if len(diffs) >= 2:
        m = statistics.mean(diffs)
        s = statistics.stdev(diffs)
        t = m / (s / math.sqrt(len(diffs))) if s > 0 else float("inf")
        df = len(diffs) - 1
        t_krit = T_KRIT_EINSEITIG.get(df)
        pos = sum(1 for d in diffs if d > 0)
        try:
            from scipy import stats as sps  # noqa: PLC0415
            p_wert = float(sps.t.sf(t, df))
        except Exception:  # noqa: BLE001
            p_wert = None
        verdikt.update({"mittel_differenz": m, "sd": s, "t": t, "df": df,
                        "t_krit_einseitig_05": t_krit, "p_einseitig": p_wert,
                        "vorzeichen_positiv": pos})
        print(f"\n  gepaart ueber {len(diffs)} Partien: mittlere Differenz {m:+.2f} pp"
              f" (sd {s:.2f}), t = {t:.2f}, df = {df}"
              + (f", p(einseitig) = {p_wert:.4f}" if p_wert is not None else
                 f", t_krit(0,05) = {t_krit}"))
        print(f"  Vorzeichen: {pos}/{len(diffs)} Partien mit Differenz > 0")
        bestaetigt = (p_wert is not None and p_wert < 0.05 or
                      p_wert is None and t_krit is not None and t > t_krit) \
                     and pos > len(diffs) / 2
        verdikt["bestaetigt"] = bool(bestaetigt)
        print(f"\n  ERFOLGSREGEL par.5 (>= 5 Partien, einseitig p < 0,05, Vorzeichen-Mehrheit): "
              f"{'BESTAETIGT' if bestaetigt and len(diffs) >= 5 else 'NICHT BESTAETIGT'}"
              + ("" if len(diffs) >= 5 else f"  (erst {len(diffs)} Partien)"))

    (BASIS / "evaluations" / "probe_human_oracle_gap_k1.json").write_text(
        json.dumps({"games": games, "verdikt": verdikt}, indent=1, ensure_ascii=False),
        encoding="utf-8")
    print("\n  geschrieben: evaluations/probe_human_oracle_gap_k1.json")


if __name__ == "__main__":
    main()
