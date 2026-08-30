# -*- coding: utf-8 -*-
"""Der Self-Play-Arm des Implicit-Minimax-Knopfs ist eine KORPUS-Frage.

PREREG_implicit_minimax_backup.md par.3a, woertlich: "Der Self-Play-Arm ist
deshalb keine Staerkefrage, sondern eine KORPUS-Frage, und sein Mass ist ein
anderes: Zielschaerfe und Zustandsabdeckung, gemessen wie beim v22-Korpus
(tools/corpus_sanity_check.py, tools/probes/corpus_state_diversity_probe.py),
plus die Orakelmetriken am daraus trainierten Netz." Wer ihn an der Siegquote
misst, misst die falsche Groesse (par.2c: netz-gegen-netz hebt sich auf).

Dieses Werkzeug fasst die beiden dort GENANNTEN Instrumente zusammen und legt
die dritte Groesse daneben, die par.3a mit "Zielschaerfe" meint und die keines
von beiden liefert: die Schaerfe der POLICY-ZIELE selbst (Top-1-Masse,
Entropie, effektiver Traeger der Wurzel-Besuchsverteilung je Record).

NICHT enthalten: die Orakelmetriken am daraus trainierten Netz. Die braeuchten
zwei Trainingslaeufe auf zwei Vollkorpora; der Nachtlauf misst die
Korpus-Groessen an je 200 Partien.

Aufruf:
    python -X utf8 -u tools/probes/implicit_minimax_selfplay_corpus_eval.py \\
        --arm-a imxb05a00 --arm-b imxb05a02 \\
        --out evaluations/artifacts/implicit_minimax_gating_b05.json
"""
import argparse
import glob
import json
import math
import os
import pathlib
import shutil
import sys
import time
from collections import Counter

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "tools"))
sys.path.insert(0, str(_ROOT / "tools" / "probes"))

from corpus_io import load_records
import corpus_sanity_check
import corpus_state_diversity_probe


def _mean(v):
    return sum(v) / len(v) if v else float("nan")


def _sd(v):
    if len(v) < 2:
        return float("nan")
    m = _mean(v)
    return (sum((x - m) ** 2 for x in v) / (len(v) - 1)) ** 0.5


def target_sharpness(files):
    """Zielschaerfe der Policy-Ziele plus Aktionsart-Verteilung.

    `policy` ist die Wurzel-Besuchsverteilung (self_play.rs-Vertrag). Drei
    Masse, weil eines allein taeuscht: Top-1-Masse sagt nichts ueber den Rest,
    die Entropie nichts ueber den Spitzenwert, und der effektive Traeger
    (exp(Entropie)) macht beide auf der Aktionsskala vergleichbar.

    `policy_target_valid=False` (PCR/Vorzug) wird ausgeschlossen -- so ein
    Record traegt kein Policy-Ziel, seine Schaerfe waere ein Phantom. Im
    network-Modus ohne PCR fehlt das Feld, dann zaehlt jeder Record.
    """
    top1, ent, eff, kandidaten = [], [], [], []
    kinds = Counter()
    kinds_valid = Counter()
    records = 0
    ungueltig = 0
    for f in files:
        for r in load_records(f):
            pol = r.get("policy")
            if not pol:
                continue
            records += 1
            art = ((pol[0] or {}).get("action") or {}).get("type") or "?"
            kinds[art] += 1
            if r.get("policy_target_valid") is False:
                ungueltig += 1
                continue
            kinds_valid[art] += 1
            ps = [max(0.0, float(e.get("prob") or 0.0)) for e in pol]
            s = sum(ps)
            if s <= 0:
                continue
            ps = [p / s for p in ps]
            h = -sum(p * math.log(p) for p in ps if p > 0)
            top1.append(max(ps))
            ent.append(h)
            eff.append(math.exp(h))
            kandidaten.append(float(len(ps)))
    return {
        "records_mit_policy": records,
        "davon_policy_target_valid_false": ungueltig,
        "top1_masse": _mean(top1), "top1_masse_sd": _sd(top1),
        "entropie": _mean(ent), "entropie_sd": _sd(ent),
        "effektiver_traeger": _mean(eff), "effektiver_traeger_sd": _sd(eff),
        "kandidaten_je_entscheidung": _mean(kandidaten),
        "aktionsarten": dict(kinds.most_common()),
        "aktionsarten_policy_tragend": dict(kinds_valid.most_common()),
    }


def stage_arm(files, target_path: pathlib.Path):
    """Legt eine Arm-Ansicht als eigenes Verzeichnis an (KOPIE, nichts wird
    verschoben oder geloescht): `corpus_sanity_check` und die Vielfalts-Sonde
    nehmen beide ein VERZEICHNIS und globben `*.pkl` -- in `data/` liegen die
    Arme aber nebeneinander."""
    target_path.mkdir(parents=True, exist_ok=True)
    for f in files:
        z = target_path / os.path.basename(f)
        if not z.exists():
            shutil.copy2(f, z)
    return str(target_path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--arm-a", required=True, help="Versionsname des Kontroll-Arms (alpha 0,0)")
    ap.add_argument("--arm-b", required=True, help="Versionsname des Test-Arms (alpha 0,2)")
    ap.add_argument("--data-dir", default=str(_ROOT / "data"))
    ap.add_argument("--stage-dir", required=True, help="Arbeitsordner fuer die Arm-Ansichten")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    t0 = time.monotonic()
    arms = {}
    for rolle, name in (("a", a.arm_a), ("b", a.arm_b)):
        files = sorted(glob.glob(os.path.join(a.data_dir, f"selfplay_{name}_*.pkl")))
        if not files:
            raise SystemExit(f"Keine Korpusdateien fuer Arm {name} in {a.data_dir}")
        manifeste = sorted(glob.glob(os.path.join(a.data_dir, f"manifest_{name}_*.json")))
        arms[rolle] = {"name": name, "dateien": [os.path.basename(f) for f in files],
                       "manifeste": [os.path.basename(m) for m in manifeste],
                       "_files": files}
        print(f"[eval] Arm {name}: {len(files)} Dateien, {len(manifeste)} Lauf-Manifeste", flush=True)

    # Lauf-Manifeste MITSCHREIBEN, nicht nur nennen: die cli_args des eigenen
    # Laufs gegen die des anderen Arms zu diffen ist die einzige Absicherung
    # dagegen, dass ein Default still einen dritten Faktor eingeschleppt hat.
    for rolle in ("a", "b"):
        arms[rolle]["cli_args"] = []
        for m in arms[rolle]["manifeste"]:
            d = json.loads(pathlib.Path(a.data_dir, m).read_text(encoding="utf-8"))
            arms[rolle]["cli_args"].append(d.get("cli_args"))
            arms[rolle].setdefault("laufzeit_erzeugung", []).append(d.get("laufzeit"))

    stage = pathlib.Path(a.stage_dir)
    dirs = {}
    for rolle in ("a", "b"):
        dirs[rolle] = stage_arm(arms[rolle]["_files"], stage / arms[rolle]["name"])
        print(f"[eval] Arm-Ansicht bereit: {dirs[rolle]}", flush=True)

    for rolle in ("a", "b"):
        print(f"[eval] Standard-Kennzahlen Arm {arms[rolle]['name']} ...", flush=True)
        arms[rolle]["standard_kennzahlen"] = corpus_sanity_check.auswerten(dirs[rolle])
        print(f"[eval] Zielschaerfe Arm {arms[rolle]['name']} ...", flush=True)
        arms[rolle]["zielschaerfe"] = target_sharpness(arms[rolle]["_files"])

    print("[eval] Zustandsabdeckung (Vielfalts-Sonde) ...", flush=True)
    div = [corpus_state_diversity_probe.auswerten(dirs[r], 10_000) for r in ("a", "b")]
    for rolle, d in zip(("a", "b"), div):
        arms[rolle]["zustandsabdeckung"] = d

    for rolle in ("a", "b"):
        arms[rolle].pop("_files")

    wand = time.monotonic() - t0
    games_total = sum(x["partien"] for x in div)
    erg = {
        "frage": "Aendert der Implicit-Minimax-Knopf (alpha 0,2) den Self-Play-KORPUS "
                 "so, dass er fuer die v23-Erzeugung eingeschaltet gehoert?",
        "vorregistrierung": "PREREG_implicit_minimax_backup.md par.3a (Mass: Zielschaerfe + "
                            "Zustandsabdeckung, NICHT Siegquote; Rueckfall Default 0,0)",
        "arme": arms,
        "vergleich": {
            "zustaende_b_durch_a": (div[1]["distinkte_zustaende"] / div[0]["distinkte_zustaende"]),
            "zustaende_je_record_b_durch_a": (div[1]["distinkte_je_record"] / div[0]["distinkte_je_record"]),
            "endbretter_b_durch_a": (div[1]["distinkte_endbretter"] / div[0]["distinkte_endbretter"]),
            "top1_masse_b_minus_a": (arms["b"]["zielschaerfe"]["top1_masse"]
                                     - arms["a"]["zielschaerfe"]["top1_masse"]),
            "entropie_b_minus_a": (arms["b"]["zielschaerfe"]["entropie"]
                                   - arms["a"]["zielschaerfe"]["entropie"]),
            "effektiver_traeger_b_minus_a": (arms["b"]["zielschaerfe"]["effektiver_traeger"]
                                             - arms["a"]["zielschaerfe"]["effektiver_traeger"]),
            "volle_spalten_b_minus_a": (arms["b"]["standard_kennzahlen"]["sp_voll"]
                                        - arms["a"]["standard_kennzahlen"]["sp_voll"]),
            "punkte_b_minus_a": (arms["b"]["standard_kennzahlen"]["punkte"]
                                 - arms["a"]["standard_kennzahlen"]["punkte"]),
        },
        "einschraenkung": "Die par.3a-Kette hat DREI Glieder; hier sind zwei gemessen. Das "
                          "dritte (Orakelmetriken am daraus trainierten Netz) braucht zwei "
                          "Trainingslaeufe auf Vollkorpora und ist im Nachtlauf nicht "
                          "gefahren. par.3a nennt fuer keines der Glieder eine Schwelle.",
        "laufzeit": {"wanduhr_s": round(wand, 1), "cpu_s": round(time.process_time(), 1),
                     "threads": 1, "s_je_partie": round(wand / max(1, games_total), 3)},
    }
    target_path = pathlib.Path(a.out)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(json.dumps(erg, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    print(f"\nArtefakt: {target_path}")
    print(json.dumps(erg["vergleich"], indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
