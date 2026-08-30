# -*- coding: utf-8 -*-
"""Auswertung des Kontrollfluss-Knopfs MOSAIC_STACK_DRAW_RESEARCH.

PREREG_chance_nodes.md Entscheidungsregel 4 ("der Kontrollfluss-Knopf gehoert
in das naechste Self-Play") plus par.13 ("Die Frage, ob
MOSAIC_STACK_DRAW_RESEARCH=1 das Netz STAERKER macht, ist offen und
unveraendert eine Arena-Frage" -- "Es aendert also den SPIELER, nicht den
MASSSTAB").

ZWEI Teile, weil die Entscheidungsregel zwei Dinge verlangt:

1. STAERKE aus der gepaarten Zwei-Arm-Arena (`tools/paired_arena_env_ab.py`,
   je Arm ein eigener Prozess -- Pflicht, weil der Knopf prozessweit per
   OnceLock gelesen wird). Siege gepaart per McNemar, Punkte auf BLOCK-Ebene
   (stehende Regel seit 2026-08-04), dazu die sechs Standard-Kennzahlen je
   Seite und Arm.
2. POLICY-ZIEL-GUELTIGKEIT der Stapelzuege im MIT-Knopf-Korpus, im Muster von
   par.13: Datensaetze je Aktionsart und der Anteil mit gueltigem Policy-Ziel.
   Ohne den Knopf existieren die Unterentscheidungen `dome_stack` (Slot) und
   `dome_rotation` im Netz-Self-Play gar nicht als eigene Entscheidungen --
   sie werden sammelaufgeloest.

KEIN eigener Log-Parser: alles kommt aus den vorhandenen Helfern, damit eine
Aenderung am Logtext beide Seiten gemeinsam brechen laesst.

Aufruf:
    python -X utf8 -u tools/probes/stack_draw_research_arena_eval.py \\
        --arena evaluations/artifacts/paired_arena_env_stackdraw_b05.json \\
        --korpus-an data --korpus-an-version sdrb05an \\
        --korpus-aus data --korpus-aus-version sdrb05aus \\
        --block-size 5 --out evaluations/artifacts/stack_draw_research_b05.json
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import pathlib
import sys
import time
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "probes"))

from corpus_io import load_records  # noqa: E402
from analyze_game_log import PATTERNS, ROUND_PREFIX  # noqa: E402
from plate_points_from_arena import block_mean, t_value  # noqa: E402
from column_build_structural_probe import (  # noqa: E402
    column_fill, final_scoring_criteria_per_player, reconstruct_game, struktur_kennzahlen,
)

NET_NAME = "Netz"        # run_net_arena_match: names = ["Netz", "Heuristik"], Netz auf Brett 0
HEUR_NAME = "Heuristik"


def _mean(v):
    return sum(v) / len(v) if v else float("nan")


def standard_metrics(games: list[dict]) -> dict:
    """Die sechs Standard-Kennzahlen je Seite (CLAUDE.md 2026-08-23) plus die
    Punkte je Wertungskriterium. Netz sitzt bei `net_arena_match` immer auf
    Brett 0, die Namen im Log sind fest."""
    per_side = defaultdict(lambda: defaultdict(list))
    platten = defaultdict(lambda: defaultdict(list))
    for g in games:
        log = g.get("log") or []
        cells = reconstruct_game(log)
        rows, penalty = defaultdict(Counter), Counter()
        for raw_line in log:
            if raw_line.startswith("#"):
                continue
            m = ROUND_PREFIX.match(raw_line)
            text = m.group(2) if m else raw_line
            tp = PATTERNS["TILING_PLACE"].match(text)
            if tp:
                rows[tp.group("name")][2 * int(tp.group("r")) + int(tp.group("si")) // 2] += 1
                continue
            rs = PATTERNS["ROUND_STRAFE"].match(text)
            if rs:
                penalty[rs.group("name")] += int(rs.group("pen"))
        krit = final_scoring_criteria_per_player(log)
        for idx, name in ((0, NET_NAME), (1, HEUR_NAME)):
            k = struktur_kennzahlen(column_fill(cells.get(name, set())))
            for feld in ("volle_spalten", "max_hoehe", "teilspalten_ge3", "teilspalten_ge4"):
                per_side[name][feld].append(float(k[feld]))
            per_side[name]["reihen_zellen"].append(float(sum(rows.get(name, Counter()).values())))
            per_side[name]["strafpunkte"].append(float(penalty.get(name, 0)))
            per_side[name]["punkte"].append(float(g["scores"][idx]))
            per_side[name]["margin"].append(float(g["scores"][idx] - g["scores"][1 - idx]))
            for kname, kpunkte in (krit.get(name) or {}).items():
                platten[name][kname].append(float(kpunkte))
    out = {n: {f: _mean(v) for f, v in d.items()} for n, d in per_side.items()}
    for n in out:
        out[n]["punkte_je_wertungsplatte"] = {k: _mean(v) for k, v in platten[n].items()}
    return out


def korpus_aktionsarten(files: list[str]) -> dict:
    """par.13-Muster: Datensaetze je Aktionsart und Anteil mit gueltigem
    Policy-Ziel. `policy_target_valid is False` (PCR/Vorzug) und ein leeres
    bzw. entartetes Ziel zaehlen als NICHT policy-tragend."""
    gesamt = Counter()
    tragend = Counter()
    records = 0
    for f in files:
        for r in load_records(f):
            records += 1
            pol = r.get("policy")
            if not pol:
                continue
            art = ((pol[0] or {}).get("action") or {}).get("type") or "?"
            gesamt[art] += 1
            if r.get("policy_target_valid") is False:
                continue
            summe = sum(max(0.0, float(e.get("prob") or 0.0)) for e in pol)
            if summe > 0:
                tragend[art] += 1
    n = sum(gesamt.values())
    return {
        "records_gesamt": records,
        "records_mit_policy": n,
        "je_aktionsart": {
            art: {"datensaetze": gesamt[art],
                  "anteil_prozent": 100.0 * gesamt[art] / n if n else float("nan"),
                  "policy_tragend": tragend[art],
                  "policy_tragend_prozent": 100.0 * tragend[art] / gesamt[art] if gesamt[art] else float("nan")}
            for art, _ in gesamt.most_common()
        },
    }


def _files(data_dir: str, version: str) -> list[str]:
    f = sorted(glob.glob(os.path.join(data_dir, f"selfplay_{version}_*.pkl")))
    if not f:
        raise SystemExit(f"Keine Korpusdateien fuer {version} in {data_dir}")
    return f


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--arena", required=True, help="Artefakt von paired_arena_env_ab.py")
    ap.add_argument("--arm-aus", default="0")
    ap.add_argument("--arm-an", default="1")
    ap.add_argument("--data-dir", default=str(ROOT / "data"))
    ap.add_argument("--korpus-an-version", required=True)
    ap.add_argument("--korpus-aus-version", required=True)
    ap.add_argument("--block-size", type=int, required=True,
                    help="MUSS der --block-size des Arena-Laufs entsprechen -- der Block "
                         "IST die Laufeinheit des Orchestrators, nicht eine frei waehlbare "
                         "Zusammenfassung.")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    t0 = time.monotonic()
    d = json.loads(pathlib.Path(a.arena).read_text(encoding="utf-8"))
    arena_games = d["games"]
    aus, an = arena_games[a.arm_aus], arena_games[a.arm_an]
    if len(aus) != len(an):
        raise SystemExit(f"Arme ungleich lang: {len(aus)} gegen {len(an)}")

    # Gepaart je SPIELINDEX (identische Basis-Seeds ueber die Arme, siehe
    # paired_arena_env_ab.run_arm). Der t-Wert danach auf die BLOECKE.
    diffs = [float(an[i]["scores"][0] - aus[i]["scores"][0]) for i in range(len(an))]
    blocks = block_mean(diffs, a.block_size)
    mittel, t = t_value(blocks)
    margin_diffs = [float((an[i]["scores"][0] - an[i]["scores"][1])
                          - (aus[i]["scores"][0] - aus[i]["scores"][1])) for i in range(len(an))]
    margin_blocks = block_mean(margin_diffs, a.block_size)
    m_mittel, m_t = t_value(margin_blocks)

    files_an = _files(a.data_dir, a.korpus_an_version)
    files_aus = _files(a.data_dir, a.korpus_aus_version)

    erg = {
        "frage": "Kostet der Kontrollfluss-Knopf MOSAIC_STACK_DRAW_RESEARCH Staerke, und "
                 "tragen die Stapelzug-Datensaetze im Mit-Knopf-Korpus gueltige Policy-Ziele?",
        "vorregistrierung": "PREREG_chance_nodes.md Entscheidungsregel 4 + par.13",
        "instrument": {
            "arena": os.path.basename(a.arena),
            "warum_dieses": "Je Arm ein EIGENER Prozess (der Knopf ist prozessweit, OnceLock). "
                            "Netz gegen Heuristik statt Spiegelmatch, weil ein prozessweiter "
                            "Knopf im Spiegelmatch beide Seiten traefe. Auf DIESEM Pfad traegt "
                            "die Heuristik-Seite apply_via_chosen_action=false "
                            "(self_play.rs:2554), der Knopf beruehrt also nur die Netz-Seite -- "
                            "genau par.13s 'aendert den SPIELER, nicht den MASSSTAB'.",
            "modell": d.get("model"), "net_sims": d.get("net_sims"),
            "heur_sims": d.get("heur_sims"), "n_games": d.get("n_games"),
            "base_seed": d.get("base_seed"), "block_size": a.block_size,
        },
        "staerke": {
            "siege_aus": d["arm_wins"][a.arm_aus],
            "siege_an": d["arm_wins"][a.arm_an],
            "mcnemar": d["comparisons"].get(f"{a.arm_aus}_vs_{a.arm_an}"),
            "punkte_netz_an_minus_aus": {"block_mittel": mittel, "block_t": t, "n_bloecke": len(blocks)},
            "margin_an_minus_aus": {"block_mittel": m_mittel, "block_t": m_t, "n_bloecke": len(margin_blocks)},
        },
        "standard_kennzahlen": {
            "aus": standard_metrics(aus),
            "an": standard_metrics(an),
        },
        "korpus": {
            "an": dict(korpus_aktionsarten(files_an),
                       dateien=[os.path.basename(f) for f in files_an]),
            "aus": dict(korpus_aktionsarten(files_aus),
                        dateien=[os.path.basename(f) for f in files_aus]),
        },
        "laufzeit_arena": d.get("laufzeit"),
    }
    wand = time.monotonic() - t0
    erg["laufzeit"] = {"wanduhr_s": round(wand, 1), "cpu_s": round(time.process_time(), 1),
                       "threads": 1,
                       "s_je_partie": round(wand / max(1, 2 * len(an)), 3)}
    target_path = pathlib.Path(a.out)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(json.dumps(erg, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    print(json.dumps(erg["staerke"], indent=2, ensure_ascii=False))
    print(json.dumps({k: v["je_aktionsart"] for k, v in erg["korpus"].items()},
                     indent=2, ensure_ascii=False))
    print(f"\nArtefakt: {target_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
