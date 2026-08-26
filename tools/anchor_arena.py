# -*- coding: utf-8 -*-
"""Arena gegen den EINGEFRORENEN Anker (B2 der Kapselungs-Kette).

WOZU: bis hierher misst jede Anker-Arena gegen die IN-PROCESS-Heuristik --
also gegen Code, der sich mit jedem Commit bewegen kann. Genau dagegen ist
`round5_anchor.rs` gebaut, und genau deshalb darf das Modul nicht fallen,
solange die Arenen so messen. Dieses Werkzeug misst stattdessen gegen
`models/frozen_heuristics/v1_anchor/` -- ein Artefakt mit eigenem Wheel, das
seine Golden Probe reproduziert.

**Dass der Pfadwechsel den Anker NICHT verschiebt, ist belegt**
(`tools/probes/anchor_referee_parity_probe.py`, 20/20 Partien identisch zu
`net_arena_match`) -- unter der Bedingung, dass der Anwendungsmodus je Seite
richtig gesetzt ist. Der Treiber tut das.

WAS ES NICHT TUT: es rechnet keine Elo. Es druckt die fertige
`elo_tracker add`-Zeile und laesst den Menschen entscheiden, ob die Kante
eingetragen wird -- dieselbe Trennung, die `elo_tracker.py` im Kopf
beschreibt ("startet SELBST KEINE Matches").

Aufruf:
    python -X utf8 -u tools/anchor_arena.py --model models/alphazero_v22_best.onnx \\
        --net-sims 400 --n-games 200 --workers 6
"""
import argparse
import json
import pathlib
import subprocess
import sys
import time

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "tools" / "probes"))

ANKER = _ROOT / "models" / "frozen_heuristics" / "v1_anchor"


def _kennzahlen(spiele: list[dict], name_netz: str, name_anker: str) -> dict:
    """Die sechs Standard-Kennzahlen aus den Partie-Logs (CLAUDE.md 2026-08-23).

    Wiederverwendet die vorhandenen Helfer statt eigener Regexe -- dieselbe
    Quelle wie `v2_envelope_arena.py`, sonst sind die Zahlen nicht
    vergleichbar.
    """
    from collections import Counter, defaultdict

    from analyze_game_log import PATTERNS, ROUND_PREFIX
    from column_build_structural_probe import column_fill, reconstruct_game, struktur_kennzahlen

    je_seite = defaultdict(lambda: defaultdict(list))
    for g in spiele:
        log = g.get("log") or []
        zellen = reconstruct_game(log)
        reihen, unlocks, strafe = defaultdict(Counter), Counter(), Counter()
        for roh in log:
            if roh.startswith("#"):
                continue
            m = ROUND_PREFIX.match(roh)
            text = m.group(2) if m else roh
            tp = PATTERNS["TILING_PLACE"].match(text)
            if tp:
                reihen[tp.group("name")][2 * int(tp.group("r")) + int(tp.group("si")) // 2] += 1
                if tp.group("special"):
                    unlocks[tp.group("name")] += 1
                continue
            rs = PATTERNS["ROUND_STRAFE"].match(text)
            if rs:
                strafe[rs.group("name")] += int(rs.group("pen"))
        for idx, name in ((0, name_netz), (1, name_anker)):
            k = struktur_kennzahlen(column_fill(zellen.get(name, set())))
            # NUR die Skalare: `struktur_kennzahlen` liefert zusaetzlich das
            # Listenfeld `fill` (die Fuellstaende je Spalte). Dieselbe Auswahl
            # wie `v2_envelope_arena.py` -- sonst sind die Zahlen nicht
            # vergleichbar, und genau das ist der Zweck der Standard-Kennzahlen.
            for feld in ("volle_spalten", "max_hoehe", "teilspalten_ge3", "teilspalten_ge4"):
                je_seite[name][feld].append(float(k[feld]))
            je_seite[name]["spezial_freischaltungen"].append(float(unlocks.get(name, 0)))
            je_seite[name]["strafpunkte"].append(float(strafe.get(name, 0)))
            je_seite[name]["punkte"].append(float(g["scores"][idx]))
            je_seite[name]["margin"].append(float(g["scores"][idx] - g["scores"][1 - idx]))
            je_seite[name]["reihen"].append(float(sum(reihen.get(name, Counter()).values())))
    return {n: {f: (sum(v) / len(v) if v else 0.0) for f, v in d.items()}
            for n, d in je_seite.items()}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--model", required=True, help="ONNX der zu messenden Netz-Seite")
    ap.add_argument("--spec", default=None, help="Such-Spec der Netz-Seite")
    ap.add_argument("--net-sims", type=int, default=400)
    ap.add_argument("--anchor-sims", type=int, default=150)
    ap.add_argument("--n-games", type=int, default=200)
    ap.add_argument("--seed-base", type=int, default=900001)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--artifact-dir", default=str(ANKER))
    ap.add_argument("--out", default="evaluations/artifacts/anchor_arena.json")
    a = ap.parse_args()

    anker = pathlib.Path(a.artifact_dir)
    manifest = json.loads((anker / "manifest.json").read_text(encoding="utf-8"))
    # Der Anker-NAME traegt den Build, nicht nur die Gattung (B3): zwei Kanten
    # gegen VERSCHIEDENE Anker-Builds saehen in der CSV sonst gleich aus.
    anker_name = f"Heuristik_{manifest['artefakt']}"

    t0 = time.monotonic()
    roh_out = pathlib.Path(a.out).with_suffix(".referee.json")
    cmd = [sys.executable, "-X", "utf8", "-u", str(_ROOT / "tools" / "frozen_referee_match.py"),
           "--artifact-dir", str(anker), "--model-a", a.model,
           "--sims-a", str(a.net_sims), "--c-puct-a", "1.5",
           "--sims-worker", str(a.anchor_sims), "--c-puct-worker", "0.3",
           "--n-games", str(a.n_games), "--seed-base", str(a.seed_base),
           "--workers", str(a.workers), "--out", str(roh_out)]
    if a.spec:
        cmd += ["--spec-a", a.spec]
    r = subprocess.run(cmd, cwd=str(_ROOT), text=True, encoding="utf-8")
    if r.returncode != 0:
        raise SystemExit(f"Referee-Serie fehlgeschlagen (Code {r.returncode}).")

    d = json.loads(roh_out.read_text(encoding="utf-8"))
    spiele = d["games"]
    netz_name = pathlib.Path(a.model).stem
    # Die Namen im LOG stammen vom Treiber: Seite A heisst "EngineA" (kein
    # Artefakt), Seite B traegt den Artefaktnamen. Hier nicht raten -- die
    # Brett-Rekonstruktion schluesselt nach genau diesen Namen.
    kz = _kennzahlen(spiele, "EngineA", manifest["artefakt"])

    erg = {
        "frage": "Wie stark ist das Netz gegen den EINGEFRORENEN Anker?",
        "netz": {"modell": a.model, "spec": a.spec, "sims": a.net_sims},
        "anker": {"artefakt": str(anker).replace("\\", "/"), "name": anker_name,
                  "sims": a.anchor_sims,
                  "wheel": manifest["wheel"]["datei"],
                  "spec": manifest["spec"]},
        "handshake": d.get("handshake"),
        "n_games": d["n_games"], "wins_netz": d["wins_a"], "wins_anker": d["wins_b"],
        "draws": d["draws"],
        "kennzahlen": kz,
        # B3: die Zeile weiss, WO ihre Knoepfe stehen. `active_knobs()` des
        # Trackers erfasst die Prozessumgebung -- fuer ein Artefakt ist das die
        # falsche Quelle, seine Knoepfe liegen in spec.json.
        "elo_zeile": {
            "player_a": netz_name, "sims_a": a.net_sims,
            "player_b": anker_name, "sims_b": a.anchor_sims,
            "wins_a": d["wins_a"], "wins_b": d["wins_b"], "n": d["n_games"],
            "knobs": f"spec:{anker}/spec.json",
        },
        "laufzeit": {"wanduhr_s": round(time.monotonic() - t0, 1), "cpu_s": None,
                     "threads": a.workers,
                     "s_je_partie": round((time.monotonic() - t0) / max(1, d["n_games"]), 3)},
    }
    ziel = pathlib.Path(a.out)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(json.dumps(erg, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")

    print(f"\n{netz_name}@{a.net_sims} gegen {anker_name}@{a.anchor_sims}")
    print(f"  {d['wins_a']} : {d['wins_b']} bei n={d['n_games']} "
          f"({100 * d['wins_a'] / max(1, d['n_games']):.1f} % fuer das Netz)")
    print("\nFertige Eintragung (NICHT automatisch ausgefuehrt -- der Tracker traegt nur ein, "
          "was ein Mensch beauftragt):")
    print(f"  python tools/elo_tracker.py add --player-a {netz_name} --sims-a {a.net_sims} "
          f"--player-b {anker_name} --sims-b {a.anchor_sims} "
          f"--wins-a {d['wins_a']} --wins-b {d['wins_b']} --n {d['n_games']} "
          f"--knobs \"spec:{anker.name}/spec.json\" "
          f"--comment \"Anker aus dem Artefakt (B2), Handshake gruen\"")
    print(f"\nArtefakt: {ziel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
