# -*- coding: utf-8 -*-
"""Wertungsplatten-Punkte und Strafleiste aus gepaarten Arena-Ergebnissen ziehen.

ANLASS (2026-08-11): die Injektions-Versuche brauchen nicht die Siegquote,
sondern das VERHALTEN -- wieviele Plattenpunkte macht das Netz, und was kostet
ihn das an Strafpunkten. `paired_arena_env_ab.py --log-games` legt die vollen
Partie-Logs ins Ergebnis-JSON; hier werden sie gelesen.

WARUM KEIN EIGENER PARSER: `tools/analyze_game_log.py` hat den Ausdruck fuer die
Endwertungs-Zeile schon (`PATTERNS["FINAL_SCORE"]`, dort Zeile 124) und die
Praefix-Behandlung (`ROUND_PREFIX`). Beides wird hier IMPORTIERT statt
nachgebaut. Folge, und sie ist beabsichtigt: aendert jemand den Logtext, brechen
beide Seiten gemeinsam, statt dass diese hier stumm falsche Zahlen liefert.
(Genau davor warnt auch `tools/hooks/pre-push` bei Log-Text-Aenderungen.)

Die Aufschlueselung JE PLATTE (`   🔲 Eckplatten: 3 Pkt`) kennt
`analyze_game_log.py` NICHT -- die kommt hier dazu, und zwar streng auf die
Zeilen NACH einer Endwertungs-Zeile begrenzt, damit sie nichts anderes
einsammelt.

2026-09-10: side_names
----------------------
Bis hierher wertete das Werkzeug je Artefakt EIN Brett aus (`@seite`, siehe
`evaluate`). Fuer ein gepaartes Gating ist das zu wenig: dort spielt jedes
Modell in beiden Orientierungen, einmal auf Brett 0 und einmal auf Brett 1.
`names` ist im Engine-Record nur das BRETT-Etikett ("NetzA"/"NetzB") und in
beiden Orientierungen dasselbe -- wer danach aggregiert, mischt die Modelle.
Damit war Standard-Kennzahl 4 aus CLAUDE.md ("erreichte Punkte je
Wertungsplatte, aufgeschluesselt je aktivem Kriterium") JE MODELL nicht
messbar; man bekam entweder eine Haelfte der Partien (`@seite`) oder einen
Mischwert aus beiden Modellen.

`tools/paired_gating.py --log-games` schreibt seit 2026-09-10 je Partie
`side_names` (die MODELLE in Brett-Reihenfolge), dazu `orientation`,
`pair_index` und `board0_name`. Traegt ein Artefakt `side_names`, laufen hier
beide Bretter durch `evaluate` und werden nach MODELL aggregiert -- Vorbild
ist `tools/probes/arena_column_probe.py` (dort Zeile 199). Zusaetzlich faellt
die GEPAARTE Differenz an: Modell A minus Modell B aus DERSELBEN Partie,
gemittelt je `pair_index`, mit 95-%-KI ueber die Paare. Artefakte ohne
`side_names` (jeder Altbestand) und jeder Aufruf mit ausdruecklichem `@seite`
laufen unveraendert durch den Bestandspfad.

Aufruf:
    python -X utf8 tools/plate_points_from_arena.py w0 w01 uni --bezug w0
    python -X utf8 -u tools/plate_points_from_arena.py \\
        evaluations/artifacts/paired_gating_<a>_vs_<b>_s35.json \\
        --out evaluations/artifacts/plate_points_<kuerzel>.json

Token-Form je Datei: `kuerzel[#arm][@seite]` -- `#arm` waehlt aus einer
Mehr-Arm-Datei, `@seite` (0/1) das BRETT (nur Netz-gegen-Netz noetig, siehe
`evaluate`).
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
from pathlib import Path

BASIS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASIS / "tools"))

from analyze_game_log import PATTERNS, ROUND_PREFIX  # noqa: E402  (bewusst nach sys.path)

# Nur auf Zeilen angewandt, die einer Endwertungs-Zeile FOLGEN -- siehe Modul-Doc.
KRITERIUM = re.compile(r"^\s+\S+ (?P<name>[^:]+): (?P<pkt>-?\d+) Pkt$")


def load_artifact(path: Path, arm: str | None = None) -> tuple[dict, list[dict]]:
    """Wie `game_list`, gibt aber den ARTEFAKT-Kopf mit zurueck (2026-09-10:
    der Modell-Modus braucht `name_a`/`name_b` fuer die Reihenfolge)."""
    d = json.load(open(path, encoding="utf-8"))
    g = d["games"]
    if isinstance(g, dict):  # Mehr-Arm-Form: {armwert: [game_list]}
        if arm is not None:
            if arm not in g:
                raise SystemExit(f"{path.name}: Arm {arm!r} nicht vorhanden "
                                 f"-- da sind {sorted(g)}")
            g = g[arm]
        elif len(g) != 1:
            raise SystemExit(f"{path.name}: {len(g)} Arme {sorted(g)} -- Arm mit "
                             f"'datei.json#arm' bzw. 'kuerzel#arm' waehlen")
        else:
            g = next(iter(g.values()))
    return d, g


def game_list(path: Path, arm: str | None = None) -> list[dict]:
    """Partien EINES Arms. `arm` waehlt aus der Mehr-Arm-Form
    (`{armwert: [game_list]}`, die `paired_arena_env_ab.py` schreibt, sobald
    `--arms` mehr als einen Wert traegt).

    ERWEITERT 2026-08-16 (Tor C, `PREREG_gate_c_consumer_sweep.md`): vorher
    brach das Werkzeug an jeder Mehr-Arm-Datei ab, was die Kampagne gezwungen
    haette, jeden Arm in einem EIGENEN Orchestrator-Lauf zu fahren -- damit
    waere der McNemar aus derselben Datei verloren gegangen. Ein Ein-Arm-File
    ohne `arm` verhaelt sich unveraendert."""
    return load_artifact(path, arm)[1]


def evaluate(sp: dict, seite: int | None = None) -> dict:
    """Eine Partie -> Kennzahlen des NETZ-Spielers.

    `seite` (2026-08-16, Destillations-Messung `PREREG_corpus_distillation.md`
    par.4.2): erzwingt einen BRETT-INDEX statt der Namensregel. Noetig fuer
    Netz-gegen-Netz-Partien -- dort heissen BEIDE Spieler "NetzA"/"NetzB",
    die Namensregel unten liefert dann immer Brett 0 und die Gegenseite waere
    unsichtbar. Genau die ist hier aber die Frage ("sammelt das Korpus-Netz
    die Platten ein, die der Champion liegen laesst"). `None` = unveraendert."""
    namen = sp["names"]
    ni = seite if seite is not None else \
        next((i for i, n in enumerate(namen) if "euristik" not in n), 0)
    netzname = namen[ni]

    platten_gesamt, je_kriterium = None, {}
    log_endstand = None  # `score` der Endwertungs-Zeile, Gegenprobe zu `scores`
    plazierung = 0       # Summe der Tiling-Punkte (`🎯 ... +N Pkt`)
    spezial_bonus = 0    # Summe der Kuppel-Boni (`⭐ ... +N Spezial-Punkte`)
    penalty_log = 0       # Summe der Rundenstrafen inkl. Startspieler-Marker (negativ)
    aktiv = None  # sammelt nur direkt nach der Endwertungs-Zeile des Netzes
    for roh in sp.get("log") or []:
        # Maschinenzeilen (`#a {...}`, PREREG_action_id_logging.md) und jede
        # andere `#`-Kommentarzeile ueberspringen -- genau wie
        # `analyze_game_log.load_log` es tut. Ohne diesen Filter wuerde eine
        # solche Zeile INNERHALB des Endwertungs-Blocks den `aktiv`-Sammler
        # abbrechen und `je_kriterium` still leeren (gemessen 2026-08-18:
        # {'Vertikale Reihen': 0, 'Eckplatten': 3, 'Spezialfelder': -12} -> {}).
        if roh.startswith("#"):
            continue
        m = ROUND_PREFIX.match(roh)
        text = m.group(2) if m else roh
        fs = PATTERNS["FINAL_SCORE"].match(text)
        if fs:
            aktiv = fs.group("name") == netzname
            if aktiv:
                platten_gesamt = int(fs.group("total"))
                log_endstand = int(fs.group("score"))
            continue
        if aktiv:
            k = KRITERIUM.match(text)
            if k:
                je_kriterium[k.group("name").strip()] = int(k.group("pkt"))
            else:
                aktiv = False  # Block zu Ende
        # Punktequellen mitzaehlen (2026-09-10, fuer die Bilanz-Gegenprobe):
        # Endstand = Startpunkte + Tiling-Punkte + Kuppel-Boni + Rundenstrafen
        # + Endwertung - Kaufkosten. Der Startstand ist 5 (board.rs:300),
        # `apply_paid_cost` (board.rs:361-366) zieht Kaeufe wie die
        # Stapel-Ziehung ab, und `apply_score` klemmt `score` bei 0
        # (board.rs:345). Die drei fehlen hier bewusst -- die Bilanz ist ein
        # Waechter fuer die LOG-Auslese, keine Nachrechnung des Motors.
        ts = PATTERNS["TILING_SCORE"].match(text)
        if ts and ts.group("name") == netzname:
            plazierung += int(ts.group("pts"))
            continue
        sb = PATTERNS["SPECIAL_BONUS"].match(text)
        if sb and sb.group("name") == netzname:
            spezial_bonus += int(sb.group("bonus"))
            continue
        rs = PATTERNS["ROUND_STRAFE"].match(text)
        if rs and rs.group("name") == netzname:
            penalty_log += int(rs.group("pen"))

    boden = sp["total_floor"]
    return dict(
        seed=sp["game_seed"],
        punkte=sp["scores"][ni],
        # ENDSTAND-MARGE (ergaenzt 2026-08-16, Tor C): der absolute Endstand
        # allein taeuscht, weil das veraenderte Netz-Spiel auch den GEGNER
        # bedient -- ein Arm, der 3 Punkte mehr macht und dem Gegner dabei 5
        # mehr laesst, sieht auf `punkte` besser aus und ist schlechter.
        marge=sp["scores"][ni] - sp["scores"][1 - ni],
        platten=platten_gesamt,
        je_kriterium=je_kriterium,
        boden=boden[ni] if isinstance(boden, list) else boden,
        sieg=1 if sp["winner"] == ni else 0,
        # Nur fuer die Plausibilitaets-Waechter (2026-09-10), von den
        # Bestands-Ausgaben unbenutzt.
        log_endstand=log_endstand,
        plazierung=plazierung,
        spezial_bonus=spezial_bonus,
        penalty_log=penalty_log,
    )


def t_value(werte: list[float]) -> tuple[float, float]:
    n = len(werte)
    if n < 2:
        return (werte[0] if werte else 0.0), 0.0
    m = sum(werte) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in werte) / (n - 1))
    return m, (m / (sd / math.sqrt(n)) if sd > 0 else 0.0)


def block_mean(diffs: list[float], block: int) -> list[float]:
    """Gepaarte Differenzen in LAUFREIHENFOLGE zu Blockmitteln zusammenfassen.

    Stehende Regel seit 2026-08-04 ([[feedback_arena_block_correlation]]): auf
    Partie-Ebene sind die Paar-SEs massiv unterschaetzt, weil die Partien eines
    Blocks korreliert sind (gemeinsamer Worker-Prozess, benachbarte Seeds).
    Der t-Wert gehoert deshalb auf die BLOECKE, nicht auf die Partien. Die
    Reihenfolge ist die des Laufs (`games`-Liste), nicht die sortierte
    Seed-Reihenfolge -- der Block IST die Laufeinheit des Orchestrators
    (`paired_arena_env_ab.py --block-size`).

    Ein angebrochener letzter Block zaehlt mit, aber nur wenn er mindestens
    die halbe Blockgroesse traegt -- sonst waere ein 1-Partie-Rest ein
    vollwertiger Datenpunkt mit der Streuung einer Einzelpartie."""
    out = []
    for i in range(0, len(diffs), block):
        teil = diffs[i:i + block]
        if len(teil) >= max(1, block // 2):
            out.append(sum(teil) / len(teil))
    return out


# --------------------------------------------------------------------------
# 2026-09-10: Aggregation nach MODELL (`side_names`) -- siehe Modul-Doc.
# --------------------------------------------------------------------------

# Einheit und Grundmenge jeder tragenden Zahl, damit sie im Artefakt neben der
# Zahl steht (CLAUDE.md, Regel 0 Zusatz 2: n, GRUNDMENGE und EINHEIT).
EINHEIT = {
    "sieg": "Siege je Partie (1/0)",
    "punkte": "Punkte je Partie (Endstand, `scores`)",
    "marge": "Punkte je Partie (eigener minus gegnerischer Endstand)",
    "platten": "Punkte je Partie (Endwertung = Summe aller Plattenkriterien)",
    "boden": "Strafpunkte je Partie (`total_floor`, positiv gezaehlt; "
             "engine/src/round_end.rs:426-428)",
    "plazierung": "Punkte je Partie (Summe der Tiling-Punkte aus dem Log)",
    "spezial_bonus": "Punkte je Partie (Summe der Kuppel-Boni aus dem Log)",
    "penalty_log": "Punkte je Partie (Summe der Rundenstrafen inkl. "
                  "Startspieler-Marker, negativ)",
}
FELDER = ["sieg", "punkte", "marge", "platten", "boden",
          "plazierung", "spezial_bonus", "penalty_log"]


def stat(values: list[float]) -> dict:
    """Mittel, SD, SE und 95-%-KI (Normalapproximation) einer Werteliste."""
    n = len(values)
    if n == 0:
        return {"n": 0, "mittel": None, "sd": None, "se": None, "ci95": None}
    m = sum(values) / n
    if n < 2:
        return {"n": n, "mittel": m, "sd": None, "se": None, "ci95": None}
    sd = math.sqrt(sum((x - m) ** 2 for x in values) / (n - 1))
    se = sd / math.sqrt(n)
    return {"n": n, "mittel": m, "sd": sd, "se": se,
            "ci95": [m - 1.96 * se, m + 1.96 * se]}


def has_side_names(games: list[dict]) -> bool:
    """Traegt das Artefakt die MODELL-Namen je Brett (paired_gating seit
    2026-09-10)? Zwei gleiche Namen (Selbstvergleich) zaehlen NICHT -- dort
    liesse sich nach Modell nichts trennen und der Bestandspfad ist richtig."""
    for sp in games:
        sn = sp.get("side_names")
        if isinstance(sn, list) and len(sn) == 2 and sn[0] != sn[1]:
            return True
    return False


def paired_diff(pairs: dict, a: str, b: str, getter) -> dict:
    """Gepaarte Differenz A minus B, gemittelt JE PAAR, dann ueber die Paare.

    `paare` bildet `pair_index` auf die Partien des Paares ab; jede Partie
    traegt beide Bretter (`recs`). Die beiden Orientierungen eines Paares
    laufen auf DEMSELBEN Seed und sind damit korreliert -- Einheit der
    Mittelung ist deshalb das PAAR, nicht die Partie (dieselbe Wahl trifft
    `tools/paired_gating.py` mit `mean_pair_diff`).

    `hole(rec)` gibt den Wert oder None; eine Partie, in der einer der beiden
    Werte fehlt, faellt aus (Waechter, keine Auswahl: die Wertungsplatten sind
    seed-bestimmt und damit immer beidseitig aktiv)."""
    per_pair, n_games = [], 0
    for _pk, pair_games in pairs.items():
        diffs = []
        for ge in pair_games:
            ra, rb = ge["recs"].get(a), ge["recs"].get(b)
            if ra is None or rb is None:
                continue
            va, vb = getter(ra), getter(rb)
            if va is None or vb is None:
                continue
            diffs.append(va - vb)
        if diffs:
            per_pair.append(sum(diffs) / len(diffs))
            n_games += len(diffs)
    s = stat(per_pair)
    s["n_paare"] = s.pop("n")
    s["n_partien"] = n_games
    return s


def model_report(artifact: dict, games: list[dict]) -> dict:
    """Kennzahlen JE MODELL ueber beide Bretter/Orientierungen, plus die
    gepaarte Differenz je Modellpaar."""
    by_model: dict[str, list[dict]] = {}
    pairs: dict = {}
    skipped = 0
    for i, sp in enumerate(games):
        sn = sp.get("side_names")
        if not (isinstance(sn, list) and len(sn) == 2 and sn[0] != sn[1]):
            skipped += 1
            continue
        recs = {}
        for pi in (0, 1):
            r = evaluate(sp, pi)
            r["brett"] = pi
            r["orientierung"] = sp.get("orientation")
            by_model.setdefault(sn[pi], []).append(r)
            recs[sn[pi]] = r
        # Ohne `pair_index` ist jede Partie ihr eigenes Paar -- die Mittelung
        # laeuft dann auf Partie-Ebene, was im Artefakt vermerkt wird.
        pk = sp.get("pair_index")
        pairs.setdefault(pk if pk is not None else ("partie", i), []).append(
            {"pair_index": pk, "recs": recs})

    names = sorted(by_model)
    preferred = [artifact.get("name_a"), artifact.get("name_b")]
    if all(k in by_model for k in preferred):
        names = preferred  # Reihenfolge des Laufs: A vor B

    out = {
        "modus": "side_names",
        "grundmenge": "Bretter je Modell -- jede Partie liefert jedem Modell "
                      "genau ein Brett, ueber beide Orientierungen zusammen",
        "einheit": EINHEIT,
        "pair_index_vorhanden": any(
            p[0]["pair_index"] is not None for p in pairs.values()),
        "partien_ohne_side_names": skipped,
        "modelle": {},
        "reihenfolge": names,
    }

    criteria = sorted({k for rs in by_model.values() for r in rs
                        for k in r["je_kriterium"]})
    out["kriterien"] = criteria

    for name in names:
        rs = by_model[name]
        entry = {"n_bretter": len(rs)}
        for f in FELDER:
            values = [r[f] for r in rs if r[f] is not None]
            entry[f] = stat(values) | {"einheit": EINHEIT[f]}
        entry["je_kriterium"] = {}
        for k in criteria:
            values = [r["je_kriterium"][k] for r in rs if k in r["je_kriterium"]]
            if values:
                entry["je_kriterium"][k] = stat(values) | {
                    "einheit": "Punkte je Partie, in denen das Kriterium aktiv war",
                    "grundmenge": f"Bretter von {name} mit aktivem Kriterium"}
        # Plausibilitaets-Waechter, siehe Modul-Doc: (1) die Kriterien
        # summieren zur Endwertung, (2) der Endstand der Endwertungs-Zeile
        # deckt sich mit `scores`, (3) Bilanz aus den Punktequellen.
        criteria_ok = sum(1 for r in rs
                      if r["platten"] is not None
                      and sum(r["je_kriterium"].values()) == r["platten"])
        final_ok = sum(1 for r in rs if r["log_endstand"] == r["punkte"])
        balance = [r["punkte"] - (r["plazierung"] + r["spezial_bonus"]
                                 + r["penalty_log"] + (r["platten"] or 0))
                  for r in rs if r["platten"] is not None]
        entry["plausibilitaet"] = {
            "kriteriensumme_gleich_endwertung": f"{criteria_ok}/{len(rs)}",
            "log_endstand_gleich_scores": f"{final_ok}/{len(rs)}",
            "bilanz_rest": stat(balance) | {
                "einheit": "Punkte je Partie (Endstand minus [Tiling + Bonus + "
                           "Strafen + Endwertung]). Erwartet wird +5 minus "
                           "Kaufkosten plus/minus Clamping, NICHT 0: der "
                           "Startstand ist 5 (board.rs:300), Kaeufe laufen "
                           "ueber apply_paid_cost (board.rs:361-366) und "
                           "stehen nicht in den hier gelesenen Logzeilen. "
                           "Ein Ausreisser gegen den Lauf-Schnitt zeigt eine "
                           "kaputte Log-Auslese an, nicht die Zahl selbst."},
        }
        out["modelle"][name] = entry

    if len(names) == 2:
        a, b = names
        paired = {"a": a, "b": b,
               "einheit_hinweis": "je Partie; Mittelung ueber die Paare "
                                  "(pair_index), 95-%-KI = Normalapproximation "
                                  "1,96*SE ueber die Paare",
               "felder": {}, "je_kriterium": {}}
        for f in FELDER:
            paired["felder"][f] = paired_diff(pairs, a, b, lambda r, f=f: r[f]) | {
                "einheit": EINHEIT[f] + " (A minus B)"}
        for k in criteria:
            d = paired_diff(pairs, a, b,
                            lambda r, k=k: r["je_kriterium"].get(k))
            if d["n_paare"]:
                paired["je_kriterium"][k] = d | {
                    "einheit": "Punkte je Partie (A minus B), nur Partien mit "
                               "beidseitig aktivem Kriterium"}
        out["gepaart"] = paired
    return out


def _z(s: dict, key: str = "mittel", width: int = 8, nk: int = 2,
       vorz: bool = False) -> str:
    v = s.get(key)
    if v is None:
        return f"{'--':>{width}}"
    return f"{v:>{width}.{nk}f}" if not vorz else f"{v:>+{width}.{nk}f}"


def print_model_report(rep: dict, source: str) -> None:
    names = rep["reihenfolge"]
    print(f"\n=== {source} -- JE MODELL (side_names) ===")
    print(f"Grundmenge: {rep['grundmenge']}")
    if rep["partien_ohne_side_names"]:
        print(f"WARNUNG: {rep['partien_ohne_side_names']} Partien ohne "
              f"brauchbares `side_names` -- nicht enthalten")
    head = (f"{'Modell':<14} {'n':>4} {'Sieg':>10} {'Punkte':>8} {'+-95%':>7} "
            f"{'Marge':>8} {'+-95%':>7} {'Endwrt':>8} {'Strafl.':>8}")
    print(head)
    print("-" * len(head))
    for n in names:
        m = rep["modelle"][n]
        nb = m["n_bretter"]
        wins = round(m["sieg"]["mittel"] * nb) if m["sieg"]["mittel"] is not None else 0
        half = (m["punkte"]["ci95"][1] - m["punkte"]["mittel"]) if m["punkte"]["ci95"] else None
        half_m = (m["marge"]["ci95"][1] - m["marge"]["mittel"]) if m["marge"]["ci95"] else None
        print(f"{n[:14]:<14} {nb:>4} {wins:>5}/{nb:<4} {_z(m['punkte'])} "
              f"{(f'{half:>7.2f}' if half is not None else '     --')} "
              f"{_z(m['marge'], vorz=True)} "
              f"{(f'{half_m:>7.2f}' if half_m is not None else '     --')} "
              f"{_z(m['platten'], vorz=True)} {_z(m['boden'])}")

    print(f"\nPlattenpunkte je Kriterium, je Modell "
          f"(Mittel ueber die Bretter mit aktivem Kriterium; (n) = Bretter)")
    criteria = rep["kriterien"]
    print(f"{'Modell':<14}" + "".join(f"{k[:17]:>19}" for k in criteria))
    for n in names:
        line = f"{n[:14]:<14}"
        for k in criteria:
            s = rep["modelle"][n]["je_kriterium"].get(k)
            line += (f"{s['mittel']:>15.2f}({s['n']:>2})" if s
                      else f"{'--':>15}({0:>2})")
        print(line)

    for n in names:
        pl = rep["modelle"][n]["plausibilitaet"]
        print(f"  Waechter {n[:14]:<14} Kriteriensumme=Endwertung "
              f"{pl['kriteriensumme_gleich_endwertung']}, Log-Endstand=scores "
              f"{pl['log_endstand_gleich_scores']}, Bilanzrest "
              f"{_z(pl['bilanz_rest'], width=6)} Pkt/Partie")

    paired = rep.get("gepaart")
    if not paired:
        return
    unit = "Paar" if rep["pair_index_vorhanden"] else "Partie (kein pair_index!)"
    print(f"\nGEPAART: {paired['a']} minus {paired['b']} (je Partie, gemittelt je "
          f"{unit}, 95-%-KI ueber die Paare)")
    head2 = f"{'Groesse':<16} {'nPaare':>7} {'nPartien':>9} {'Delta':>9} {'95-%-KI':>22}"
    print(head2)
    print("-" * len(head2))
    for f in FELDER:
        s = paired["felder"][f]
        ci = (f"[{s['ci95'][0]:>+8.3f}, {s['ci95'][1]:>+8.3f}]"
              if s["ci95"] else f"{'--':>22}")
        print(f"{f:<16} {s['n_paare']:>7} {s['n_partien']:>9} "
              f"{_z(s, width=9, nk=3, vorz=True)} {ci:>22}")
    if paired["je_kriterium"]:
        print(f"\nGEPAART je Kriterium ({paired['a']} minus {paired['b']}):")
        for k, s in paired["je_kriterium"].items():
            ci = (f"[{s['ci95'][0]:>+7.3f}, {s['ci95'][1]:>+7.3f}]"
                  if s["ci95"] else "--")
            print(f"  {k[:24]:<26} nPaare={s['n_paare']:>4} "
                  f"nPartien={s['n_partien']:>4} "
                  f"{_z(s, width=8, nk=3, vorz=True)}  KI {ci}")


def write_out(a, model_reports: dict, legacy: dict,
                 t_wall: float, t_cpu: float, pair_games: int) -> None:
    """`--out`: alles Gerechnete als JSON, mit `laufzeit`-Block (CLAUDE.md,
    "Laufzeiten messen, nicht schaetzen"). `threads` ist hier immer 1 -- die
    Auswertung ist einkernige Textarbeit, ohne Partien und ohne Engine."""
    if not a.out:
        return
    target = Path(a.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    wall = time.time() - t_wall
    doc = {
        "werkzeug": "tools/plate_points_from_arena.py",
        "aufruf": {"kuerzel": a.kuerzel, "praefix": a.praefix,
                   "bezug": a.bezug, "block": a.block},
        "modell_reports": model_reports,
        "legacy": legacy,
        "laufzeit": {"wanduhr_s": round(wall, 2),
                     "cpu_s": round(time.process_time() - t_cpu, 2),
                     "threads": 1,
                     "s_je_partie": round(wall / pair_games, 4) if pair_games else None},
    }
    target.write_text(json.dumps(doc, indent=2, ensure_ascii=False),
                    encoding="utf-8", newline="\n")
    print(f"\nArtefakt: {target}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("kuerzel", nargs="+",
                   help="Out-Praefix-Kuerzel (z.B. w0 uni) oder ein Pfad zur JSON")
    p.add_argument("--praefix", default="platten",
                   help="gemeinsamer Namensteil vor dem Kuerzel (Default: platten)")
    p.add_argument("--bezug", default=None,
                   help="Kuerzel, gegen das GEPAART verglichen wird (ueber den Seed)")
    p.add_argument("--block", type=int, default=None,
                   help="Blockgroesse fuer die BLOCK-Ebene der gepaarten t-Werte "
                        "(stehende Regel seit 2026-08-04). Sollte der "
                        "--block-size des Laufs sein. Ohne Angabe nur Partie-Ebene.")
    p.add_argument("--out", default=None,
                   help="JSON-Artefakt mit allen Zahlen (n, Grundmenge, Einheit) "
                        "plus laufzeit-Block")
    a = p.parse_args()
    t_wall, t_cpu = time.time(), time.process_time()

    daten: dict[str, dict[int, dict]] = {}
    reihenfolge: dict[str, list[int]] = {}  # Laufreihenfolge je Kuerzel, fuer --block
    model_reports: dict[str, dict] = {}    # 2026-09-10: Token mit `side_names`
    games_total = 0
    for k in a.kuerzel:
        # Token-Form: kuerzel[#arm][@seite]. `@seite` (0/1) waehlt bei
        # Netz-gegen-Netz-Dateien das BRETT -- siehe `evaluate`-Docstring.
        rest, _, seite_s = k.partition("@")
        seite = int(seite_s) if seite_s else None
        if seite not in (None, 0, 1):
            raise SystemExit(f"{k}: @seite muss 0 oder 1 sein")
        roh, _, arm = rest.partition("#")
        pf = Path(roh) if roh.endswith(".json") else \
            BASIS / "evaluations" / "artifacts" / f"paired_arena_env_{a.praefix}_{roh}.json"
        if not pf.exists():
            print(f"{k}: FEHLT ({pf.name})")
            continue
        head, games = load_artifact(pf, arm or None)
        games_total += len(games)
        # MODELL-Modus nur, wenn das Artefakt `side_names` traegt UND der
        # Nutzer nicht ausdruecklich ein Brett gewaehlt hat. Ein `@seite`
        # bleibt das aeltere, engere Verlangen und schlaegt durch.
        if seite is None and has_side_names(games):
            rep = model_report(head, games)
            rep["artefakt"] = pf.name
            model_reports[k] = rep
            continue
        if seite is not None and has_side_names(games):
            # Doppelt schief auf einem gepaarten Gating, und beides gemessen
            # am s35-Artefakt (2026-09-10): Brett 0 traegt in Orientierung 1
            # ein anderes MODELL als in Orientierung 2, und beide Partien
            # eines Paares haben denselben `game_seed` -- der Seed-Schluessel
            # unten wirft die eine davon weg (400 Partien -> 200 Zeilen).
            # Bestandsverhalten bleibt, aber nicht stillschweigend.
            print(f"WARNUNG: {pf.name} traegt `side_names`; mit @seite mischt "
                  f"Brett {seite} beide Modelle und der Seed-Schluessel "
                  f"verwirft eine Orientierung je Paar. Ohne @seite laeuft der "
                  f"Modell-Modus.")
        satz = [evaluate(s, seite) for s in games]
        daten[k] = {r["seed"]: r for r in satz}
        reihenfolge[k] = [r["seed"] for r in satz]

    for k, rep in model_reports.items():
        print_model_report(rep, rep["artefakt"])

    if not daten:
        if model_reports:
            write_out(a, model_reports, {}, t_wall, t_cpu, games_total)
            return
        raise SystemExit("keine Daten")

    fehlend = {k: sum(1 for r in v.values() if r["platten"] is None) for k, v in daten.items()}
    if any(fehlend.values()):
        print(f"WARNUNG: Endwertungs-Zeile nicht gefunden in {fehlend} Partien -- "
              f"Logtext geaendert? (siehe Modul-Doc)\n")

    bezug = daten.get(a.bezug) if a.bezug else None
    head = (f"{'Kuerzel':<10} {'n':>3} {'Sieg':>7} {'Punkte':>7} {'Marge':>7} "
            f"{'Platten':>8} {'Boden':>7}")
    if bezug:
        head += f" | {'ΔMarge':>8} {'t':>6} {'ΔPlatten':>9} {'t':>6} {'ΔBoden':>7} {'t':>6}"
    print(head)
    print("-" * len(head))
    for k, v in daten.items():
        ks = sorted(v)
        n = len(ks)
        mp = sum(v[s]["punkte"] for s in ks) / n
        mm = sum(v[s]["marge"] for s in ks) / n
        mpl = sum(v[s]["platten"] or 0 for s in ks) / n
        mb = sum(v[s]["boden"] for s in ks) / n
        w = sum(v[s]["sieg"] for s in ks)
        line = (f"{k:<10} {n:>3} {w:>3}/{n:<3} {mp:>7.2f} {mm:>7.2f} "
                 f"{mpl:>8.2f} {mb:>7.2f}")
        if bezug:
            gem = [s for s in ks if s in bezug]
            dp, tp = t_value([v[s]["marge"] - bezug[s]["marge"] for s in gem])
            dl, tl = t_value([(v[s]["platten"] or 0) - (bezug[s]["platten"] or 0) for s in gem])
            db, tb = t_value([v[s]["boden"] - bezug[s]["boden"] for s in gem])
            line += f" | {dp:>+8.2f} {tp:>6.2f} {dl:>+9.2f} {tl:>6.2f} {db:>+7.2f} {tb:>6.2f}"
        print(line)

    # BLOCK-Ebene (stehende Regel): dieselben gepaarten Differenzen, aber der
    # t-Wert ueber die Blockmittel statt ueber die Partien. Reihenfolge ist die
    # des BEZUGS-Laufs, damit alle Arme dieselbe Blockeinteilung bekommen.
    if bezug and a.block:
        ordn = [s for s in reihenfolge.get(a.bezug, sorted(bezug)) if s in bezug]
        head2 = (f"\nBLOCK-Ebene (Blockgroesse {a.block}, t ueber Blockmittel)\n"
                 f"{'Kuerzel':<10} {'Bloecke':>7} {'ΔMarge':>8} {'t':>6} "
                 f"{'ΔPlatten':>9} {'t':>6} {'ΔBoden':>7} {'t':>6}")
        print(head2)
        for k, v in daten.items():
            if k == a.bezug:
                continue
            gem = [s for s in ordn if s in v]
            bp = block_mean([v[s]["marge"] - bezug[s]["marge"] for s in gem], a.block)
            bl = block_mean([(v[s]["platten"] or 0) - (bezug[s]["platten"] or 0)
                               for s in gem], a.block)
            bb = block_mean([v[s]["boden"] - bezug[s]["boden"] for s in gem], a.block)
            dp, tp = t_value(bp)
            dl, tl = t_value(bl)
            db, tb = t_value(bb)
            print(f"{k:<10} {len(bp):>7} {dp:>+8.2f} {tp:>6.2f} "
                  f"{dl:>+9.2f} {tl:>6.2f} {db:>+7.2f} {tb:>6.2f}")

    # Je Kriterium: nur Platten, die ueberhaupt vorkommen
    names = sorted({n for v in daten.values() for r in v.values() for n in r["je_kriterium"]})
    if names:
        print(f"\nPlattenpunkte je Kriterium (Mittel ueber die Partien, in denen die Platte aktiv war):")
        print(f"{'Kuerzel':<10}" + "".join(f"{n[:17]:>19}" for n in names))
        for k, v in daten.items():
            line = f"{k:<10}"
            for n in names:
                tr = [r["je_kriterium"][n] for r in v.values() if n in r["je_kriterium"]]
                line += f"{(sum(tr)/len(tr) if tr else float('nan')):>15.2f}({len(tr):>2})"
            print(line)

    # GEPAART je Kriterium -- das ist die Zielgroesse der Wertungsplatten-
    # Kampagne (Tor C, `PREREG_gate_c_consumer_sweep.md` par.5). Nur Partien,
    # in denen die Platte in BEIDEN Armen aktiv war; sie ist seed-bestimmt,
    # also immer beidseitig -- die Bedingung ist ein Waechter, keine Auswahl.
    if bezug and names:
        print(f"\nGEPAART je Kriterium gegen '{a.bezug}' (Delta, t Partie-Ebene"
              + (f" / t Block-Ebene, Bloecke a {a.block}" if a.block else "") + "):")
        for k, v in daten.items():
            if k == a.bezug:
                continue
            ordn = [s for s in reihenfolge.get(a.bezug, sorted(bezug)) if s in v]
            print(f"  {k}")
            for n in names:
                gem = [s for s in ordn
                       if n in v[s]["je_kriterium"] and n in bezug[s]["je_kriterium"]]
                if not gem:
                    continue
                diffs = [v[s]["je_kriterium"][n] - bezug[s]["je_kriterium"][n] for s in gem]
                d, t = t_value(diffs)
                rest = ""
                if a.block:
                    bd, bt = t_value(block_mean(diffs, a.block))
                    rest = f"   Block {bd:>+7.2f} t={bt:>6.2f} (nB={len(block_mean(diffs, a.block))})"
                print(f"    {n[:22]:<24} n={len(gem):>3}  {d:>+7.2f} t={t:>6.2f}{rest}")

    # `--out` fuer den Bestandspfad: dieselben Zahlen wie in der Tabelle oben,
    # nur mit n/Grundmenge/Einheit daneben. Die AUSGABE bleibt unberuehrt.
    legacy = {}
    for k, v in daten.items():
        rs = list(v.values())
        entry = {
            "n_partien": len(rs),
            "grundmenge": "Partien EINER Seite (Bestandspfad: Namensregel bzw. @seite)",
        }
        for f in FELDER:
            values = [r[f] for r in rs if r[f] is not None]
            entry[f] = stat(values) | {"einheit": EINHEIT[f]}
        entry["je_kriterium"] = {}
        for n in names:
            values = [r["je_kriterium"][n] for r in rs if n in r["je_kriterium"]]
            if values:
                entry["je_kriterium"][n] = stat(values) | {
                    "einheit": "Punkte je Partie, in denen das Kriterium aktiv war"}
        legacy[k] = entry
    write_out(a, model_reports, legacy, t_wall, t_cpu, games_total)


if __name__ == "__main__":
    main()
