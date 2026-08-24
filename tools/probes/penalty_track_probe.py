#!/usr/bin/env python
"""Strafleisten-Auslastung je Seite (Standard-Kennzahl 3, CLAUDE.md).

Anlass: die Reihen-Sonde hat gezeigt, dass der Champion flach 55-56 % seiner
Draft-Ziele auf die KURZEN Musterreihen 1-3 legt und Reihe 5/6 meidet, ohne
Spaetrunden-Anpassung -- der Heuristik-Lehrer macht spaet das Gegenteil.
Eine unbelegte Erklaerung dafuer ist STRAF-AVERSION: lange Reihen tragen
Ueberlaufrisiko, kurze nicht. Diese Sonde zieht die Zahl, die den Verdacht
stuetzt oder erledigt.

Startet KEIN Self-Play, KEINE Arena, KEIN Training -- nur vorhandene
Arena-Artefakte lesen und Logzeilen auszaehlen.

Quelle und warum: `paired_arena_env_imm_a02.json` traegt Champion (Netz) UND
Heuristik in DENSELBEN Partien auf denselben Seeds. Damit ist der Vergleich
gepaart je Partie -- kein Korpus-/Aera-Versatz, kein Gegnerwechsel zwischen
den Seiten. `paired_arena_env_imm_netvnet.json` und `..._swap.json` laufen als
ZWEITE gepaarte Quelle mit: dort steht dasselbe Netz auf beiden Seiten,
aber mit verschiedenen per-Seite-Specs (NetzA = champion_imm_a02,
NetzB = champion_frozen) -- ein gepaarter alpha-gegen-frozen Vergleich auf
identischen Seeds.

Vier Kennzahlen je Seite und Partie, alle aus `analyze_game_log.PATTERNS`:

  strafpunkte       Summe der Rundenend-Strafen (ROUND_STRAFE, Betrag).
                    Die Leiste zahlt -1/-2/-3/-4 je belegtem Slot
                    (engine_manual Z.161), ist also PROGRESSIV und bei
                    4 Slots gedeckelt -- nicht linear in Steinen.
  straf_ziele       Draft-ZUEGE, deren Ziel die Strafleiste ist
  straf_ziel_steine dieselben Zuege in STEINEN (vergleichbare Einheit
                    zu ueberlauf_steine)
  ueberlauf_steine  Steine, die aus einer vollen Musterreihe ueberlaufen
                    ("(+N Strafleiste)" an SUN_TAKE/MOON_GLOBAL_TAKE)
  strafrunden       Runden mit Strafe != 0

Auswertung auf BLOCK-Ebene (je Partie), nicht je Zug -- im Projekt sind
Paar-SEs schon einmal massiv unterschaetzt worden.
"""
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from analyze_game_log import PATTERNS, ROUND_PREFIX  # noqa: E402
from plate_points_from_arena import partien  # noqa: E402

EVAL = ROOT / "evaluations"
OUT_JSON = EVAL / "penalty_track_probe.json"

TAKE_CATS = ("SUN_TAKE", "MOON_GLOBAL_TAKE")


def penalties_from_log(log_lines):
    """Liefert {name: {kennzahl: wert}} fuer EINE Partie."""
    acc = defaultdict(lambda: dict(strafpunkte=0, straf_ziele=0,
                                   straf_ziel_steine=0,
                                   ueberlauf_steine=0, strafrunden=0,
                                   draft_zuege=0))
    for roh in log_lines:
        if roh.startswith("#"):
            continue
        m = ROUND_PREFIX.match(roh)
        text = m.group(2) if m else roh

        mm = PATTERNS["ROUND_STRAFE"].match(text)
        if mm:
            pen = int(mm.group("pen"))
            if pen != 0:
                acc[mm.group("name")]["strafpunkte"] += abs(pen)
                acc[mm.group("name")]["strafrunden"] += 1
            continue

        for cat in TAKE_CATS:
            mm = PATTERNS[cat].match(text)
            if not mm:
                continue
            a = acc[mm.group("name")]
            a["draft_zuege"] += 1
            if mm.group("dest") == "Strafleiste":
                a["straf_ziele"] += 1
                a["straf_ziel_steine"] += int(mm.group("n"))
            ov = mm.group("overflow")
            if ov:
                a["ueberlauf_steine"] += int(ov)
            break
    return acc


def collect(path, arm, side_filter):
    """{label: {seed: kennzahlen}} ueber alle Partien EINES Arms."""
    out = defaultdict(dict)
    for sp in partien(path, arm):
        seed = sp.get("game_seed")
        for name, vals in penalties_from_log(sp.get("log") or []).items():
            label = side_filter(name)
            if label is not None:
                out[label][seed] = vals
    return out


def summarize(per_seed):
    keys = ("strafpunkte", "straf_ziele", "straf_ziel_steine",
            "ueberlauf_steine", "strafrunden", "draft_zuege")
    n = len(per_seed)
    out = {"n_partien": n}
    for k in keys:
        vals = [v[k] for v in per_seed.values()]
        out[k + "_je_partie"] = round(statistics.mean(vals), 3) if vals else None
        out[k + "_median"] = statistics.median(vals) if vals else None
    return out


def paired_diff(a_per_seed, b_per_seed, key):
    """Gepaarte Differenz A minus B ueber gemeinsame Seeds (Block-Ebene)."""
    seeds = sorted(set(a_per_seed) & set(b_per_seed))
    d = [a_per_seed[s][key] - b_per_seed[s][key] for s in seeds]
    if len(d) < 2:
        return None
    mean = statistics.mean(d)
    sd = statistics.stdev(d)
    se = sd / len(d) ** 0.5
    return dict(n_paare=len(d), mittel=round(mean, 3), sd=round(sd, 3),
                se=round(se, 3), t=round(mean / se, 2) if se > 0 else None)


def main():
    result = {}

    p_a02 = EVAL / "paired_arena_env_imm_a02.json"
    for arm in ("0", "0.2"):
        got = collect(p_a02, arm,
                      lambda n: "Champion" if n == "Netz" else
                      ("Heuristik" if n == "Heuristik" else None))
        block = {lab: summarize(v) for lab, v in got.items()}
        if "Champion" in got and "Heuristik" in got:
            block["_gepaart_Champion_minus_Heuristik"] = {
                k: paired_diff(got["Champion"], got["Heuristik"], k)
                for k in ("strafpunkte", "straf_ziele", "straf_ziel_steine",
                          "ueberlauf_steine", "strafrunden")
            }
        result[f"champion_vs_heuristik_arm{arm}"] = block

    # Netz-gegen-Netz: SELBES Modell auf beiden Seiten, aber VERSCHIEDENE
    # per-Seite-Specs (spec_a = champion_imm_a02, spec_b = champion_frozen).
    # KORREKTUR 2026-08-24: eine erste Fassung labelte beide Seiten als
    # "Champion" und mischte damit zwei verhaltensverschiedene Agenten in
    # einen Topf. NetzA und NetzB sind hier ein gepaarter alpha-gegen-frozen
    # Vergleich -- dieselben Partien, dieselben Seeds, dasselbe Netz, nur der
    # Suchknopf unterscheidet sich. Genau die Arm-Struktur, die
    # PREREG_floor_action_aversion braucht, und sie kostet nichts.
    for fname, key in (("paired_arena_env_imm_netvnet.json", "netvnet"),
                       ("paired_arena_env_imm_netvnet_swap.json", "netvnet_swap")):
        p_nvn = EVAL / fname
        if not p_nvn.exists():
            continue
        d = json.load(open(p_nvn, encoding="utf-8"))
        spec_a = str(d.get("spec_a") or "")
        spec_b = str(d.get("spec_b") or "")
        assert d.get("model") == d.get("model_b"), (
            f"{fname}: model != model_b -- Annahme 'selbes Netz beidseitig' faellt")

        def spec_label(spec):
            # KORREKTUR (beim Nachziehen fuer Schritt 7 gefunden): eine
            # erste Fassung prüfte "imm_a02" NUR gegen spec_a und "frozen"
            # NUR gegen spec_b -- in der Swap-Datei liegen spec_a/spec_b
            # aber vertauscht (spec_a=champion_frozen, spec_b=champion_
            # imm_a02), und beide Labels fielen dort auf den generischen
            # "A:.../B:..."-Fallback zurueck. Jetzt POSITIONSUNABHAENGIG:
            # jeder String wird gegen BEIDE Substrings geprueft.
            if "imm_a02" in spec:
                return "alpha0.2"
            if "frozen" in spec:
                return "frozen"
            return f"unbekannt:{spec}"

        lab_a = spec_label(spec_a)
        lab_b = spec_label(spec_b)
        got = collect(p_nvn, None,
                      lambda n, a=lab_a, b=lab_b: a if n == "NetzA" else
                      (b if n == "NetzB" else None))
        block = {lab: summarize(v) for lab, v in got.items()}
        if lab_a in got and lab_b in got:
            block[f"_gepaart_{lab_a}_minus_{lab_b}"] = {
                k: paired_diff(got[lab_a], got[lab_b], k)
                for k in ("strafpunkte", "straf_ziele", "straf_ziel_steine",
                          "ueberlauf_steine", "strafrunden")
            }
        result[key] = block

    result["_meta"] = dict(
        frage="Meidet der Champion die Strafleiste staerker als der "
              "Heuristik-Lehrer? Wenn ja, ist Straf-Aversion ein Kandidat "
              "fuer die flache Kurzreihen-Praeferenz (Reihen-Sonde).",
        quelle_gepaart="paired_arena_env_imm_a02.json -- beide Seiten in "
                       "DENSELBEN Partien auf denselben Seeds",
        ebene="Block-Ebene (je Partie), nicht je Zug",
        caveat="Die Heuristik spielt hier GEGEN ein Netz, nicht gegen sich "
               "selbst. Ihr Strafverhalten kann davon abhaengen; der "
               "Vergleich ist bedingungsgleich, aber nicht "
               "kontextfrei.",
    )
    OUT_JSON.write_text(json.dumps(result, indent=2, ensure_ascii=False),
                        encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\n-> {OUT_JSON}")


if __name__ == "__main__":
    main()
