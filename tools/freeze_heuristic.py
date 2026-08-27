# -*- coding: utf-8 -*-
"""Friert eine Heuristik als vollstaendiges Agenten-Artefakt ein.

Nutzer-Auftrag 2026-08-26. Gegenstueck zu `models/frozen_champions/` fuer die
NETZ-Seite, aber mit einem anderen Beweismittel -- und das ist der Kern dieses
Werkzeugs.

WARUM EINE HEURISTIK ANDERS EINGEFROREN WIRD ALS EIN NETZ
---------------------------------------------------------
Bei einem Netz-Champion traegt `model.onnx` das Verhalten; das Wheel ist
Beiwerk. Bei einer Heuristik ist es umgekehrt: es GIBT kein ONNX, das
Verhalten steckt vollstaendig im Wheel. Faellt das Wheel weg und war der Baum
unversioniert veraendert, ist der Agent unwiederbringlich.

Und die Golden Probe ist eine andere. Die Welle-3-Probe der Netz-Champions
(`build_frozen_golden_probe.py`) sammelt DRAFTING-Zustaende und prueft die
gewaehlte Aktion -- mehr kann sie nicht, weil der Referee Tiling und
Startsetzung selbst aufloest (`referee.rs:312` ruft `resolve_tiling_step`,
und das ist auf V1 hart verdrahtet). Fuer eine Heuristik waere das eine
HALBE Probe: v2huelle wirkt gerade im Platzierungs-Routing.

Die Probe hier ist deshalb ein SELF-PLAY-Lauf aus dem eigenen Wheel, byte-
verglichen (Nutzer-Vorschlag 2026-08-26: "laesst sich einfach pruefen ueber
10 self plays"). Der deckt Drafting UND Tiling UND Runde 5 ab und ist damit
strenger als das, was die Netz-Artefakte haben.

WAS INS ARTEFAKT GEHOERT
------------------------
  spec.json          was der Agent IST (heuristik_variante + Suchfelder)
  manifest.json      Herkunft: git_commit UND git_dirty, contract_hash,
                     engine_config, Rezept der Golden Probe
  <wheel>.whl        der Traeger des Verhaltens
  golden_probe/      der Referenzlauf, gegen den verglichen wird
  label_net.onnx     NUR wo der Agent ein Netz zum LABELN braucht (Bootstrap an
                     den Rundenuebergaengen + Drafting-Priors; am Spiel
                     self_play.rs:1234) -- als KOPIE, nicht als Verweis auf
                     models/: ein Artefakt, das auf einen geteilten Pfad
                     zeigt, ist nicht eingefroren, sondern ein Zeiger, der
                     wandern kann.
  venv/              wird gebaut, aber NICHT versioniert (aus dem Wheel neu
                     herstellbar, Pfade sind maschinenspezifisch)

`git_dirty` steht im Manifest, weil es dort weh tun soll. Am 2026-08-26 hat
ein `git_dirty: true` ohne festgehaltenen Anteil einen halben Tag gekostet --
erst mit dem Verdacht, der Erzeuger sei verloren, dann mit dem Nachweis, dass
er es nicht war.

Aufruf:
    python -X utf8 -u tools/freeze_heuristic.py --name v1_anchor --variante v1
    python -X utf8 -u tools/freeze_heuristic.py --name v2huelle_generator \\
        --variante v2huelle --tiling-net models/alphazero_v21_2d_brierbest.onnx
"""
import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "engine" / "py"))

TARGET_BASE = _ROOT / "models" / "frozen_heuristics"


def _git(*args) -> str:
    return subprocess.run(["git", *args], cwd=str(_ROOT), capture_output=True,
                          text=True, encoding="utf-8", timeout=30).stdout.strip()


def _git_provenance() -> dict:
    """Commit UND Schmutzigkeit -- beides, oder das Feld ist wertlos."""
    dirty = bool(_git("status", "--porcelain"))
    return {
        "git_commit": _git("rev-parse", "HEAD"),
        "git_dirty": dirty,
        "git_dirty_hinweis": (
            "TRUE heisst: der Baum trug beim Einfrieren unversionierte Aenderungen. "
            "Das Wheel im Artefakt ist dann NICHT aus dem Commit rekonstruierbar -- "
            "es ist die einzige Kopie des Verhaltens." if dirty else
            "FALSE heisst: das Wheel laesst sich aus dem Commit neu bauen. Die Kopie "
            "im Artefakt ist trotzdem der schnellere und sichere Weg."),
        "dirty_dateien": _git("status", "--porcelain").splitlines() if dirty else [],
    }


def _git_provenance(path) -> str:
    """Pfad OHNE Rechnerstruktur -- repo-relativ, sonst nur der Dateiname.

    Das Repo ist oeffentlich (CLAUDE.md, Nutzer-Entscheid 2026-08-17): keine
    absoluten Pfade, kein Nutzername in neuen Dateien. Diese Funktion ist die
    Reparatur eines konkreten Regelbruchs -- die beiden Manifeste vom
    2026-08-26 trugen den vollen Build-Pfad und haben am 2026-08-27 den
    pre-push-Hook ausgeloest.

    Der Wert bleibt aussagekraeftig: er sagt WOHER im Repo die Datei kam
    (`engine/target/wheels/...`), nur nicht mehr, wie der Rechner heisst.
    """
    p = pathlib.Path(path).resolve()
    try:
        return p.relative_to(_ROOT).as_posix()
    except ValueError:
        return p.name


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--name", required=True, help="Artefaktname, z.B. v1_anchor")
    ap.add_argument("--variante", required=True, help="Heuristik-Variante, z.B. v1 / v2huelle")
    ap.add_argument("--wheel", default=None,
                    help="Pfad zum Wheel (Default: der frischeste Build in engine/target/wheels)")
    ap.add_argument("--tiling-net", default=None,
                    help="ONNX fuer die LABEL-Erzeugung (Rundenuebergangs-Bootstrap, Drafting-Priors); wird als label_net.onnx kopiert. Es entscheidet auf dem Heuristik-Erzeugerpfad NICHTS am Spiel -- dort steht tiling_net auf None.")
    ap.add_argument("--games", type=int, default=10, help="Partien der Golden Probe")
    ap.add_argument("--sims", type=int, default=600)
    ap.add_argument("--seed", type=int, default=20260826)
    ap.add_argument("--threads", type=int, default=11)
    ap.add_argument("--c-puct", dest="c_puct", type=float, default=1.5)
    ap.add_argument("--rolle", default=None,
                    help="Rolle im Klartext (z.B. 'Elo-Anker' oder 'Korpus-Generator v22')")
    a = ap.parse_args()

    import mosaic_rust as mr

    # KEINE eigene Variantenliste hier. Ein unbekannter Name wird von der
    # Engine abgewiesen (self_play.py: "Unbekannte Werte werden von der Engine
    # ABGEWIESEN, nicht still auf v1 gefaltet"), also scheitert der
    # Golden-Probe-Lauf unten hart und das Artefakt entsteht gar nicht erst.
    # Eine zweite Liste hier waere eine zweite Wahrheit.

    target = TARGET_BASE / a.name
    if target.exists():
        raise SystemExit(
            f"{target} existiert bereits. Ein Artefakt wird NICHT ueberschrieben -- "
            "es ist der Bezugspunkt fuer alles, was darauf gemessen wurde. "
            "Neuer Name, oder das alte bewusst von Hand entfernen.")
    target.mkdir(parents=True)
    t0 = time.monotonic()

    # --- Wheel
    wheel = pathlib.Path(a.wheel) if a.wheel else max(
        (_ROOT / "engine" / "target" / "wheels").glob("mosaic_rust-*.whl"),
        key=lambda p: p.stat().st_mtime)
    shutil.copy2(wheel, target / wheel.name)
    print(f"Wheel: {wheel.name}", flush=True)

    # --- Tiling-Netz (nur wo noetig), als KOPIE
    tiling_net = None
    if a.tiling_net:
        src = pathlib.Path(a.tiling_net)
        shutil.copy2(src, target / "label_net.onnx")
        tiling_net = {"datei": "label_net.onnx", "quelle": _git_provenance(src),
                      "rolle": ("Stichentscheid im Tiling-Durchfall (self_play.rs:1234: die "
                                "v2-Vorzugskarte greift nur, wenn sie einen Zug liefert -- sonst "
                                "faellt es auf das Netz durch) und Erzeuger der "
                                "bootstrap_value-Label")}
        print(f"Label-Netz kopiert: {src.name} -> label_net.onnx", flush=True)

    # --- Spec: was der Agent IST
    spec = {"implicit_minimax_alpha": 0.0, "long_row_init_shaping_w": 0.0,
            "heuristik_variante": a.variante}
    (target / "spec.json").write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n",
                                    encoding="utf-8", newline="\n")

    # --- Golden Probe: der Referenzlauf, aus DIESEM Wheel
    probe_dir = target / "golden_probe"
    probe_dir.mkdir()
    recipe = {
        "mode": "mcts", "games": a.games, "sims": a.sims, "version": "probe",
        "threads": a.threads, "chunk": a.games, "per_file": a.games, "seed": a.seed,
        "c_puct": a.c_puct, "add_root_noise": True, "deterministic": False,
        "record_rtv": False, "tau_argmax_from_move": 0,
        "heuristik_variante": a.variante,
        "model": "label_net.onnx" if tiling_net else None,
    }
    cmd = [sys.executable, "-X", "utf8", "-u", str(_ROOT / "self_play.py"),
           "--mode", "mcts", "--games", str(a.games), "--sims", str(a.sims),
           "--version", "probe", "--threads", str(a.threads), "--chunk", str(a.games),
           "--per-file", str(a.games), "--seed", str(a.seed), "--c-puct", str(a.c_puct),
           "--tau-argmax-from-move", "0",
           # Die Variante kommt aus der SPEC, nicht aus dem Gedaechtnis des
           # Aufrufers -- genau der Unterschied, den dieses Artefakt ausmacht.
           "--heuristik-variante", spec["heuristik_variante"]]
    if tiling_net:
        cmd += ["--model", str(target / "label_net.onnx")]
    env = dict(os.environ, MOSAIC_DATA_DIR=str(probe_dir))
    print(f"Golden Probe: {a.games} Partien, Variante {a.variante} ...", flush=True)
    r = subprocess.run(cmd, cwd=str(_ROOT), env=env, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise SystemExit(f"Golden-Probe-Lauf fehlgeschlagen (Code {r.returncode}) -- Artefakt "
                         f"unvollstaendig, {target} von Hand entfernen.")
    probe_files = sorted(p.name for p in probe_dir.glob("*.pkl"))
    if not probe_files:
        raise SystemExit("Golden-Probe-Lauf hat keine .pkl erzeugt -- Abbruch.")

    # --- Manifest
    manifest = {
        "artefakt": a.name,
        "rolle": a.rolle or f"eingefrorene Heuristik {a.variante}",
        "typ": "heuristik",
        "freeze_date": time.strftime("%Y-%m-%d"),
        "spec": spec,
        "wheel": {"datei": wheel.name, "quelle": _git_provenance(wheel),
                  "rolle": ("Traeger des VERHALTENS. Bei einer Heuristik gibt es kein ONNX, "
                            "das es mittraegt -- ohne dieses Wheel ist der Agent weg.")},
        "tiling_net": tiling_net,
        "herkunft": _git_provenance(),
        "contract_hash": json.loads(mr.engine_config_json()).get("contract_hash"),
        "engine_config": json.loads(mr.engine_config_json()),
        # WAS DER WORKER DIESES ARTEFAKTS BEANTWORTEN KANN. Geschrieben zur
        # EINFRIERZEIT, weil genau dann feststeht, was das mitgelieferte Wheel
        # kann -- nicht was die Engine irgendwann kann.
        #
        # Anlass 2026-08-26: die ersten beiden Artefakte wurden eingefroren,
        # bevor das erweiterte Protokoll fertig war. Ihr Worker kannte
        # `start_placement_choice_state_json` nicht, und der Treiber lief
        # mitten in der Partie in einen AttributeError. Ein Rueckfall auf
        # referee-aufgeloestes Tiling waere die schlechtere Antwort gewesen:
        # das Artefakt haette dann still als V1 gekachelt.
        "protokoll": {"kinds": ["drafting", "tiling", "start_placement"],
                      "hinweis": ("Fehlt dieses Feld, stammt das Artefakt aus der Zeit vor dem "
                                  "erweiterten Protokoll und kann seine Platzierung NICHT selbst "
                                  "entscheiden. Der Treiber verweigert dann, statt es als V1 "
                                  "kacheln zu lassen.")},
        "golden_probe": {
            "art": "self-play-reproduktion, byte-verglichen",
            "warum": ("Die Welle-3-Probe der Netz-Champions prueft nur DRAFTING-Entscheidungen; "
                      "der Referee loest Tiling und Startsetzung selbst auf und ist dabei auf V1"
                      " verdrahtet (referee.rs:312 -> self_play.rs:1207). Fuer eine Heuristik "
                      "waere das eine halbe Probe. Ein Self-Play-Lauf aus dem eigenen Wheel "
                      "deckt Drafting, Tiling und Runde 5 ab."),
            "rezept": recipe,
            "dateien": probe_files,
            "pruefbefehl": (f"python -X utf8 -u tools/verify_frozen_heuristic.py "
                            f"--artifact-dir models/frozen_heuristics/{a.name}"),
        },
        "laufzeit": {"wanduhr_s": round(time.monotonic() - t0, 1), "cpu_s": None,
                     "threads": a.threads, "s_je_partie": None},
    }
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                                        encoding="utf-8", newline="\n")

    print(f"\nArtefakt: {target}")
    print(f"  Wheel        {wheel.name}")
    print(f"  Variante     {a.variante}")
    print(f"  Golden Probe {len(probe_files)} Datei(en), {a.games} Partien")
    print(f"  git_dirty    {manifest['herkunft']['git_dirty']}")
    print(f"\nvenv wird NICHT hier gebaut -- siehe tools/verify_frozen_heuristic.py --build-venv.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
