"""E3b Stufe 1 (PREREG_denial_tiebreak.md): Feuerrate des Denial-Tie-Breaks
mit Unsicherheits-Fenster messen -- die BILLIGE Vorstufe, die ueber Stufe 2
(2x400 Arena) entscheidet. Abbruchregel der Vorregistrierung: Feuerrate
< 5% der Entscheidungen => E3b gilt als irrelevant, Punkt ohne Arena
geschlossen.

WARUM EIN EIGENER TREIBER (und nicht self_play.py / paired_arena_env_ab.py):
`DENIAL_TIEBREAK_FIRED/TOTAL` sind prozessglobale `AtomicU64` in der
Rust-Bibliothek. `self_play.py` startet je 10er-Chunk einen FRISCHEN
`mp.Process` (`_run_chunk_supervised`), und `paired_arena_env_ab.py` gibt je
Arm einen eigenen Worker-Prozess -- in beiden Faellen stirbt der Zaehler mit
dem Kind, und der Elternprozess liest (0, 0). Das saehe wie "Feuerrate 0%"
aus und wuerde die Vorregistrierungs-Abbruchregel FALSCH-POSITIV ausloesen.
`mosaic_rust.net_arena_match` dagegen spielt Rust-seitig gethreadet IM
SELBEN Prozess (siehe `tools/arena.py::run_net_arena`), dort ist der
Zaehler sichtbar.

DESHALB ZWEI PFLICHT-PLAUSIBILITAETSPRUEFUNGEN, bevor eine Rate berichtet
wird -- eine kaputte Messung darf nicht als Null-Befund durchgehen:
  1. `denial_tiebreak_stats` muss im Modul existieren (sonst: altes Wheel).
  2. `total > 0` muss gelten (sonst: Regler wirkungslos oder Netz ohne
     opp-Kopf -- `note_denial_tiebreak` wird dann nie erreicht).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def champion_model() -> str:
    name = (BASE_DIR / "models" / "champion.txt").read_text(encoding="utf-8").strip()
    p = BASE_DIR / "models" / f"alphazero_{name}.onnx"
    if not p.exists():
        raise SystemExit(f"Champion-ONNX fehlt: {p}")
    return str(p.resolve())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=None, help="Default: models/champion.txt")
    ap.add_argument("--n-games", type=int, default=200)
    ap.add_argument("--net-sims", type=int, default=400)
    ap.add_argument("--heur-sims", type=int, default=150)
    ap.add_argument("--threads", type=int, default=10)
    ap.add_argument("--chunk", type=int, default=25)
    ap.add_argument("--seed", type=int, default=20260826)
    ap.add_argument("--uncert-z", default="1.0")
    ap.add_argument("--min-visit-frac", default="0.5")
    ap.add_argument("--out", default="evaluations/e3b_firing_rate.json")
    args = ap.parse_args()

    # Regler VOR dem Import setzen: die Getter sind `OnceLock`, lesen also
    # genau einmal je Prozess. Ein spaeteres os.environ-Setzen waere je nach
    # Aufrufreihenfolge wirkungslos -- genau die Klasse stiller Fehler, die
    # dieser Task messen soll.
    os.environ["MOSAIC_DENIAL_UNCERT_Z"] = str(args.uncert_z)
    os.environ["MOSAIC_DENIAL_MIN_VISIT_FRAC"] = str(args.min_visit_frac)
    # Konflikt-Assert in der Engine: eps>0 UND z>0 gleichzeitig ist verboten
    # (zwei konkurrierende Aequivalenz-Definitionen). Explizit auf 0 setzen,
    # statt auf einen sauberen Prozess zu hoffen.
    os.environ["MOSAIC_DENIAL_TIEBREAK_EPS"] = "0.0"

    import mosaic_rust as mr  # noqa: E402  (Import bewusst nach os.environ)

    if not hasattr(mr, "denial_tiebreak_stats"):
        raise SystemExit(
            "ABBRUCH: das installierte mosaic_rust kennt `denial_tiebreak_stats` "
            "nicht -- altes Wheel. Erst `pip install --force-reinstall --no-deps "
            "engine/target/wheels/mosaic_rust-*.whl` (nur moeglich, wenn weder "
            "Server noch Training die DLL haelt), dann Paritaets-Probe."
        )

    model = args.model or champion_model()
    mr.reset_denial_tiebreak_stats()

    print(f"E3b Stufe 1 -- Feuerraten-Messung (z={args.uncert_z}, f={args.min_visit_frac})")
    print(f"  Modell {os.path.basename(model)} @{args.net_sims} Sims "
          f"vs Heuristik@{args.heur_sims}, {args.n_games} Partien, Seed {args.seed}")
    print("-" * 60)

    done = 0
    chunk_idx = 0
    net_wins = 0
    t0 = time.time()
    while done < args.n_games:
        n = min(args.chunk, args.n_games - done)
        raw = mr.net_arena_match(model, net_sims=args.net_sims, heur_sims=args.heur_sims,
                                 n_games=n, seed=args.seed + chunk_idx,
                                 num_threads=args.threads)
        for g in json.loads(raw):
            done += 1
            if g["winner"] == 0:
                net_wins += 1
        chunk_idx += 1
        fired, total = mr.denial_tiebreak_stats()
        rate = (fired / total) if total else None
        print(f"  Block {chunk_idx} (n={n}, {time.time() - t0:.0f}s kumulativ): "
              f"Partien {done}/{args.n_games}, Netz {net_wins}, "
              f"Tie-Break {fired}/{total}"
              + (f" = {rate * 100:.2f}%" if rate is not None else " (noch keine Auswertung)"))

    fired, total = mr.denial_tiebreak_stats()
    print("-" * 60)

    if total == 0:
        verdict = "INSTRUMENT KAPUTT"
        detail = ("total=0: `note_denial_tiebreak` wurde nie erreicht. Moegliche "
                  "Ursachen: Regler nicht wirksam (OnceLock-Reihenfolge), Netz ohne "
                  "opp_points-Kopf, oder der E3b-Pfad haengt an einer anderen "
                  "Bedingung. Das ist AUSDRUECKLICH KEINE Feuerrate von 0% und "
                  "loest die Prereg-Abbruchregel NICHT aus.")
        rate = None
    else:
        rate = fired / total
        if rate < 0.05:
            verdict = "STUFE 2 ENTFAELLT (Prereg-Abbruchregel)"
            detail = (f"Feuerrate {rate * 100:.2f}% < 5% -- E3b gilt als irrelevant, "
                      "Punkt ohne Arena geschlossen.")
        else:
            verdict = "STUFE 2 GERECHTFERTIGT"
            detail = f"Feuerrate {rate * 100:.2f}% >= 5% -- 2x400-Arena gemaess Prereg."

    print(f"Ergebnis: fired={fired} / total={total}"
          + (f" = {rate * 100:.2f}%" if rate is not None else ""))
    print(f"Verdikt : {verdict}")
    print(f"          {detail}")

    out = {
        "task": "E3b Stufe 1 (Feuerrate)",
        "prereg": "evaluations/PREREG_denial_tiebreak.md",
        "model": model,
        "net_sims": args.net_sims,
        "heur_sims": args.heur_sims,
        "n_games": args.n_games,
        "base_seed": args.seed,
        "uncert_z": args.uncert_z,
        "min_visit_frac": args.min_visit_frac,
        "denial_tiebreak_fired": fired,
        "denial_tiebreak_total": total,
        "firing_rate": rate,
        "net_wins": net_wins,
        "verdict": verdict,
        "detail": detail,
    }
    out_path = BASE_DIR / args.out
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Geschrieben: {out_path}")

    # Exit-Code 2 nur beim kaputten Instrument -- ein regulaerer Prereg-Abbruch
    # (Feuerrate < 5%) ist ein GUELTIGES Ergebnis und liefert 0.
    sys.exit(2 if total == 0 else 0)


if __name__ == "__main__":
    main()
