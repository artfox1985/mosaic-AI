"""PREREG_opponent_disruption_v2.md, Stufe 1 -- die ECHTE, vorregistrierte
Messung: Stoerfenster-Rate im Trockenlauf-Zaehlmodus der laufenden Engine.

Gezaehlt wird an der finalen Wurzelzugwahl (`net_mcts::color_denial_probe_with`,
gerufen aus `select_final_root_child`):

  total     -- ausgewertete Wurzelentscheidungen (inkl. Ein-Kandidaten-Faelle,
               gleicher Nenner-Zuschnitt wie `denial_tiebreak_stats`)
  fenster   -- davon mit >=1 nach E3b-Kriterium gleichwertigem Nicht-Sieger
               (Besuchs-Gate + Zwei-Anteils-SE, `denial_uncert_qualifies`)
  stoerbar  -- davon mit >=1 solchen Kandidaten, der dem Gegner MEHR von einer
               akut gebrauchten Farbe wegnimmt als der Suchsieger UND die
               eigene Strafleiste NICHT staerker fuellt

**Der Modus aendert die gespielte Aktion nicht.** `color_denial_probe_with`
gibt nichts zurueck und schreibt nur Zaehler; `select_final_root_child` liefert
weiterhin exakt `apply_denial_tiebreak(...)`. Behauptet wird das nicht --
`--golden` beweist es: dieselben Seeds mit Zaehler AUS und AN, die kompletten
Arena-JSONs muessen zeichengleich sein.

ZWEI PFLICHT-PLAUSIBILITAETSPRUEFUNGEN, bevor eine Rate berichtet wird
(Lehre aus `tools/e3b_firing_rate.py`, dessen Kopf die Falle erklaert):
  1. `color_denial_probe_stats` muss im Modul existieren (sonst altes Wheel).
  2. `total > 0` muss gelten. Die Zaehler sind prozessglobale `AtomicU64`;
     `self_play.py` (frischer `mp.Process` je Chunk) und
     `paired_arena_env_ab.py` (Worker je Arm) fuehren sie im KIND, der
     Elternprozess laese (0,0,0) -- das saehe wie "Rate 0%" aus und wuerde die
     Prereg-Abbruchregel FALSCH-POSITIV ausloesen. `net_arena_match` dagegen
     threadet Rust-seitig IM SELBEN Prozess.

Abbruchregel der Vorregistrierung (§5.2): `stoerbar/total < 5%` -> v2 gilt als
irrelevant, ohne Arena geschlossen.

CLI:
    python tools/color_denial_probe.py --golden --n-games 12
    python tools/color_denial_probe.py --n-games 200 --out evaluations/color_denial_probe.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ABBRUCH_SCHWELLE = 0.05


def champion_model() -> str:
    name = (BASE_DIR / "models" / "champion.txt").read_text(encoding="utf-8").strip()
    p = BASE_DIR / "models" / f"alphazero_{name}.onnx"
    if not p.exists():
        raise SystemExit(f"Champion-ONNX fehlt: {p}")
    return str(p.resolve())


def set_knobs(z: str, f: str) -> None:
    """Regler VOR dem Import setzen -- die Getter sind `OnceLock` und lesen
    genau einmal je Prozess. Die beiden E3/E3b-Regler werden ausdruecklich auf
    0 gesetzt: sie wuerden das SPIELVERHALTEN aendern und die
    Byte-Identitaets-Zusicherung dieses Zaehlmodus zunichte machen."""
    os.environ["MOSAIC_COLOR_DENIAL_PROBE_Z"] = str(z)
    os.environ["MOSAIC_COLOR_DENIAL_PROBE_MIN_VISIT_FRAC"] = str(f)
    os.environ["MOSAIC_DENIAL_TIEBREAK_EPS"] = "0.0"
    os.environ["MOSAIC_DENIAL_UNCERT_Z"] = "0.0"


def require_binding(mr) -> None:
    if not hasattr(mr, "color_denial_probe_stats"):
        raise SystemExit(
            "ABBRUCH: das installierte mosaic_rust kennt `color_denial_probe_stats` "
            "nicht -- altes Wheel. Erst `pip install --force-reinstall --no-deps "
            "engine/target/wheels/mosaic_rust-*.whl` (nur moeglich, wenn weder Server "
            "noch Training die DLL haelt), dann Paritaets-Probe, dann diese Messung."
        )


def run_games(mr, model, args, seed_offset=0):
    """Spielt `args.n_games` Partien in Bloecken und gibt die rohen
    Arena-JSON-Strings zurueck (fuer den Golden-Vergleich unveraendert)."""
    raws, done, chunk_idx, net_wins = [], 0, 0, 0
    t0 = time.time()
    while done < args.n_games:
        n = min(args.chunk, args.n_games - done)
        raw = mr.net_arena_match(model, net_sims=args.net_sims, heur_sims=args.heur_sims,
                                 n_games=n, seed=args.seed + seed_offset + chunk_idx,
                                 num_threads=args.threads)
        raws.append(raw)
        for g in json.loads(raw):
            done += 1
            net_wins += 1 if g["winner"] == 0 else 0
        chunk_idx += 1
        total, fenster, stoerbar = mr.color_denial_probe_stats()
        quote = f"{100 * stoerbar / total:.2f}%" if total else "(noch keine Auswertung)"
        print(f"  Block {chunk_idx} (n={n}, {time.time() - t0:.0f}s): Partien {done}/{args.n_games}, "
              f"Netz {net_wins}, Fenster {fenster}/{total}, stoerbar {stoerbar}/{total} = {quote}",
              flush=True)
    return raws, net_wins


def golden(mr, model, args) -> int:
    """Byte-Identitaets-Nachweis: identische Seeds, Zaehler AUS gegen AN.

    Der Zaehlmodus wird NICHT ueber die Env umgeschaltet (OnceLock, einmal je
    Prozess), sondern ueber zwei getrennte Kindprozesse desselben Skripts --
    jeder mit seinem eigenen `MOSAIC_COLOR_DENIAL_PROBE_Z`.
    """
    import subprocess

    def one(z: str) -> str:
        env = dict(os.environ)
        env["MOSAIC_COLOR_DENIAL_PROBE_Z"] = z
        env["MOSAIC_DENIAL_TIEBREAK_EPS"] = "0.0"
        env["MOSAIC_DENIAL_UNCERT_Z"] = "0.0"
        env["PYTHONIOENCODING"] = "utf-8"
        code = (
            "import json,os,sys;import mosaic_rust as mr;"
            f"raw=mr.net_arena_match({model!r}, net_sims={args.net_sims}, "
            f"heur_sims={args.heur_sims}, n_games={args.n_games}, seed={args.seed}, "
            f"num_threads={args.threads});"
            "sys.stdout.write(raw)"
        )
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                           encoding="utf-8", env=env, cwd=str(BASE_DIR))
        if r.returncode != 0:
            raise SystemExit(f"Golden-Lauf (z={z}) fehlgeschlagen:\n{r.stderr[-2000:]}")
        return r.stdout

    print(f"Golden-Vergleich: {args.n_games} Partien, Seed {args.seed}, "
          f"Zaehler AUS gegen AN ...", flush=True)
    aus = one("0.0")
    an = one(str(args.probe_z))
    if aus == an:
        print(f"BYTE-IDENTISCH: {len(aus)} Zeichen Arena-JSON stimmen exakt ueberein.")
        return 0
    a, b = json.loads(aus), json.loads(an)
    diff = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
    print("ABWEICHUNG: der Zaehlmodus hat das Spielverhalten veraendert.", file=sys.stderr)
    print(f"  {len(diff)} von {len(a)} Partien unterscheiden sich, erste: {diff[:5]}", file=sys.stderr)
    return 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default=None, help="Default: models/champion.txt")
    ap.add_argument("--n-games", type=int, default=200)
    ap.add_argument("--net-sims", type=int, default=400)
    ap.add_argument("--heur-sims", type=int, default=150)
    ap.add_argument("--threads", type=int, default=10)
    ap.add_argument("--chunk", type=int, default=25)
    ap.add_argument("--seed", type=int, default=20260901)
    ap.add_argument("--probe-z", default="1.0")
    ap.add_argument("--probe-min-visit-frac", default="0.5")
    ap.add_argument("--golden", action="store_true",
                    help="nur den Byte-Identitaets-Nachweis fahren")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)

    set_knobs("0.0" if args.golden else args.probe_z, args.probe_min_visit_frac)
    import mosaic_rust as mr  # noqa: E402  (Import bewusst NACH os.environ)
    require_binding(mr)
    model = args.model or champion_model()

    if args.golden:
        return golden(mr, model, args)

    mr.reset_color_denial_probe_stats()
    print(f"Stufe 1 -- Stoerfenster-Zaehlmodus (z={args.probe_z}, f={args.probe_min_visit_frac})")
    print(f"  {os.path.basename(model)} @{args.net_sims} Sims vs Heuristik@{args.heur_sims}, "
          f"{args.n_games} Partien, Seed {args.seed}")
    print("-" * 72, flush=True)
    _, net_wins = run_games(mr, model, args)
    total, fenster, stoerbar = mr.color_denial_probe_stats()
    print("-" * 72)

    if total == 0:
        verdict = "INSTRUMENT KAPUTT"
        detail = ("total=0: `color_denial_probe_with` wurde nie erreicht. Moegliche "
                  "Ursachen: Regler nicht wirksam (OnceLock-Reihenfolge), altes Wheel, "
                  "oder der Zaehler haengt hinter einer anderen Bedingung. Das ist "
                  "AUSDRUECKLICH KEINE Rate von 0% und loest die Abbruchregel NICHT aus.")
        rate = fenster_rate = None
    else:
        rate, fenster_rate = stoerbar / total, fenster / total
        if rate < ABBRUCH_SCHWELLE:
            verdict = "STUFE 2 ENTFAELLT (Prereg-Abbruchregel)"
            detail = (f"Stoerfensterrate {rate * 100:.2f}% < 5% -- v2 gilt als irrelevant, "
                      "Punkt ohne Arena geschlossen.")
        else:
            verdict = "ABBRUCHREGEL GREIFT NICHT"
            detail = (f"Stoerfensterrate {rate * 100:.2f}% >= 5%. Die Entscheidung ueber "
                      "Stufe 2 (Bau) trifft der Nutzer -- eine hohe Rate ist KEIN "
                      "Wirksamkeitsnachweis (E3b feuerte 36,52% und verlor 4,75pp).")

    print(f"Ergebnis: total={total}, fenster={fenster}"
          + (f" = {fenster_rate * 100:.2f}%" if fenster_rate is not None else "")
          + f", stoerbar={stoerbar}" + (f" = {rate * 100:.2f}%" if rate is not None else ""))
    print(f"Verdikt : {verdict}\n          {detail}")

    out = {
        "task": "PREREG_opponent_disruption_v2.md Stufe 1 (Stoerfenster-Zaehlmodus, live)",
        "prereg": "evaluations/PREREG_opponent_disruption_v2.md",
        "model": model,
        "net_sims": args.net_sims,
        "heur_sims": args.heur_sims,
        "n_games": args.n_games,
        "seed": args.seed,
        "probe_z": args.probe_z,
        "probe_min_visit_frac": args.probe_min_visit_frac,
        "net_wins": net_wins,
        "total": total,
        "fenster": fenster,
        "fenster_rate": fenster_rate,
        "stoerbar": stoerbar,
        "stoerbar_rate": rate,
        "abbruchschwelle": ABBRUCH_SCHWELLE,
        "verdikt": verdict,
        "detail": detail,
    }
    if args.out:
        Path(args.out).write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"geschrieben: {args.out}")
    return 0 if total > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
