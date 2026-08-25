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

Aufruf:
    python -X utf8 tools/plate_points_from_arena.py w0 w01 uni --bezug w0

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
from pathlib import Path

BASIS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASIS / "tools"))

from analyze_game_log import PATTERNS, ROUND_PREFIX  # noqa: E402  (bewusst nach sys.path)

# Nur auf Zeilen angewandt, die einer Endwertungs-Zeile FOLGEN -- siehe Modul-Doc.
KRITERIUM = re.compile(r"^\s+\S+ (?P<name>[^:]+): (?P<pkt>-?\d+) Pkt$")


def game_list(pfad: Path, arm: str | None = None) -> list[dict]:
    """Partien EINES Arms. `arm` waehlt aus der Mehr-Arm-Form
    (`{armwert: [game_list]}`, die `paired_arena_env_ab.py` schreibt, sobald
    `--arms` mehr als einen Wert traegt).

    ERWEITERT 2026-08-16 (Tor C, `PREREG_gate_c_consumer_sweep.md`): vorher
    brach das Werkzeug an jeder Mehr-Arm-Datei ab, was die Kampagne gezwungen
    haette, jeden Arm in einem EIGENEN Orchestrator-Lauf zu fahren -- damit
    waere der McNemar aus derselben Datei verloren gegangen. Ein Ein-Arm-File
    ohne `arm` verhaelt sich unveraendert."""
    d = json.load(open(pfad, encoding="utf-8"))
    g = d["games"]
    if isinstance(g, dict):  # Mehr-Arm-Form: {armwert: [game_list]}
        if arm is not None:
            if arm not in g:
                raise SystemExit(f"{pfad.name}: Arm {arm!r} nicht vorhanden "
                                 f"-- da sind {sorted(g)}")
            g = g[arm]
        elif len(g) != 1:
            raise SystemExit(f"{pfad.name}: {len(g)} Arme {sorted(g)} -- Arm mit "
                             f"'datei.json#arm' bzw. 'kuerzel#arm' waehlen")
        else:
            g = next(iter(g.values()))
    return g


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
            continue
        if aktiv:
            k = KRITERIUM.match(text)
            if k:
                je_kriterium[k.group("name").strip()] = int(k.group("pkt"))
            else:
                aktiv = False  # Block zu Ende

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
    a = p.parse_args()

    daten: dict[str, dict[int, dict]] = {}
    reihenfolge: dict[str, list[int]] = {}  # Laufreihenfolge je Kuerzel, fuer --block
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
        satz = [evaluate(s, seite) for s in game_list(pf, arm or None)]
        daten[k] = {r["seed"]: r for r in satz}
        reihenfolge[k] = [r["seed"] for r in satz]

    if not daten:
        raise SystemExit("keine Daten")

    fehlend = {k: sum(1 for r in v.values() if r["platten"] is None) for k, v in daten.items()}
    if any(fehlend.values()):
        print(f"WARNUNG: Endwertungs-Zeile nicht gefunden in {fehlend} Partien -- "
              f"Logtext geaendert? (siehe Modul-Doc)\n")

    bezug = daten.get(a.bezug) if a.bezug else None
    kopf = (f"{'Kuerzel':<10} {'n':>3} {'Sieg':>7} {'Punkte':>7} {'Marge':>7} "
            f"{'Platten':>8} {'Boden':>7}")
    if bezug:
        kopf += f" | {'ΔMarge':>8} {'t':>6} {'ΔPlatten':>9} {'t':>6} {'ΔBoden':>7} {'t':>6}"
    print(kopf)
    print("-" * len(kopf))
    for k, v in daten.items():
        ks = sorted(v)
        n = len(ks)
        mp = sum(v[s]["punkte"] for s in ks) / n
        mm = sum(v[s]["marge"] for s in ks) / n
        mpl = sum(v[s]["platten"] or 0 for s in ks) / n
        mb = sum(v[s]["boden"] for s in ks) / n
        w = sum(v[s]["sieg"] for s in ks)
        zeile = (f"{k:<10} {n:>3} {w:>3}/{n:<3} {mp:>7.2f} {mm:>7.2f} "
                 f"{mpl:>8.2f} {mb:>7.2f}")
        if bezug:
            gem = [s for s in ks if s in bezug]
            dp, tp = t_value([v[s]["marge"] - bezug[s]["marge"] for s in gem])
            dl, tl = t_value([(v[s]["platten"] or 0) - (bezug[s]["platten"] or 0) for s in gem])
            db, tb = t_value([v[s]["boden"] - bezug[s]["boden"] for s in gem])
            zeile += f" | {dp:>+8.2f} {tp:>6.2f} {dl:>+9.2f} {tl:>6.2f} {db:>+7.2f} {tb:>6.2f}"
        print(zeile)

    # BLOCK-Ebene (stehende Regel): dieselben gepaarten Differenzen, aber der
    # t-Wert ueber die Blockmittel statt ueber die Partien. Reihenfolge ist die
    # des BEZUGS-Laufs, damit alle Arme dieselbe Blockeinteilung bekommen.
    if bezug and a.block:
        ordn = [s for s in reihenfolge.get(a.bezug, sorted(bezug)) if s in bezug]
        kopf2 = (f"\nBLOCK-Ebene (Blockgroesse {a.block}, t ueber Blockmittel)\n"
                 f"{'Kuerzel':<10} {'Bloecke':>7} {'ΔMarge':>8} {'t':>6} "
                 f"{'ΔPlatten':>9} {'t':>6} {'ΔBoden':>7} {'t':>6}")
        print(kopf2)
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
    namen = sorted({n for v in daten.values() for r in v.values() for n in r["je_kriterium"]})
    if namen:
        print(f"\nPlattenpunkte je Kriterium (Mittel ueber die Partien, in denen die Platte aktiv war):")
        print(f"{'Kuerzel':<10}" + "".join(f"{n[:17]:>19}" for n in namen))
        for k, v in daten.items():
            zeile = f"{k:<10}"
            for n in namen:
                tr = [r["je_kriterium"][n] for r in v.values() if n in r["je_kriterium"]]
                zeile += f"{(sum(tr)/len(tr) if tr else float('nan')):>15.2f}({len(tr):>2})"
            print(zeile)

    # GEPAART je Kriterium -- das ist die Zielgroesse der Wertungsplatten-
    # Kampagne (Tor C, `PREREG_gate_c_consumer_sweep.md` par.5). Nur Partien,
    # in denen die Platte in BEIDEN Armen aktiv war; sie ist seed-bestimmt,
    # also immer beidseitig -- die Bedingung ist ein Waechter, keine Auswahl.
    if bezug and namen:
        print(f"\nGEPAART je Kriterium gegen '{a.bezug}' (Delta, t Partie-Ebene"
              + (f" / t Block-Ebene, Bloecke a {a.block}" if a.block else "") + "):")
        for k, v in daten.items():
            if k == a.bezug:
                continue
            ordn = [s for s in reihenfolge.get(a.bezug, sorted(bezug)) if s in v]
            print(f"  {k}")
            for n in namen:
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


if __name__ == "__main__":
    main()
