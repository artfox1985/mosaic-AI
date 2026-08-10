# -*- coding: utf-8 -*-
"""Label-Extraktor fuer den Plattenkopf (`evaluations/PREREG_plattenkopf.md`).

Rechnet aus dem ENDBRETT einer Self-Play-Partie die Atome je Wertungsplatte und
stempelt sie -- wie `scores` -- auf ALLE Datensaetze derselben Partie: der Kopf
soll ja aus einem Mittelspiel-Zustand vorhersagen, was am Ende gilt.

Atome (je 9 Kuppelslots, Reihenfolge zeilenweise 0..8):
  Kriterium 6: Slot hat ein Spezialfeld, das am Ende LEER ist          -> x(-3)
  Kriterium 3: Slot hat ein BELEGTES Jokerfeld UND alle Jokerfelder
               des Bretts sind belegt                                  -> x(+2)

Die Konjunktion in Kriterium 3 ist der Grund, warum die Summe der Atome EXAKT
der Auszahlung entspricht (Nutzer-Zuschnitt 2026-08-10): tritt die Bedingung
ein, zaehlen die Atome die Jokerfelder; tritt sie nicht ein, sind alle null.

## Was dieses Skript NICHT kann

Der letzte Datensatz einer Partie ist der letzte TILING-SCHRITT, nicht der
Zustand nach Spielende -- exakte Endlabels liegen im Bestandskorpus nicht vor.
Die Labels sind damit minimal veraltet und unterzaehlen Fuellungen
systematisch. Gemessen (60 Partien, 120 Bretter): Kriterium 6 ist in 101/120
Brettern schon 6 Datensaetze vor Schluss final, Kriterium 3 in 109/120.
Fuer eine Machbarkeits-/Staerkeprobe tragbar; ein Champion-Kandidat braucht
exakte Labels aus einer Generierung, die sie stempelt.

Aufruf:

    python tools/plattenkopf_labels.py --check          # Identitaets-Pruefung
    python tools/plattenkopf_labels.py --stats          # Grundraten je Kriterium
"""
from __future__ import annotations

import argparse
import collections
import glob
import pickle
import statistics
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
NUM_SLOTS = 9

# Feldtypen, wie das State-JSON sie schreibt (`serialize.rs`).
T_SPECIAL = "SPECIAL"
T_WILD = "WILD"


def _spaces(slot: dict) -> list[dict]:
    return slot.get("spaces") or []


def _is_filled(space: dict) -> bool:
    """`filled` traegt die Farbe des liegenden Steins bzw. den Spezial-Marker."""
    return bool(space.get("filled"))


def _slots_flat(player: dict) -> list[dict | None]:
    """Die 9 Kuppelslots zeilenweise; leere Slots als None."""
    grid = player.get("dome_grid") or []
    flat: list[dict | None] = []
    for row in grid:
        for slot in row:
            flat.append(slot if slot else None)
    while len(flat) < NUM_SLOTS:
        flat.append(None)
    return flat[:NUM_SLOTS]


def atoms_criterion6(player: dict) -> list[int]:
    """Slot hat ein Spezialfeld, das am Ende LEER ist."""
    out = []
    for slot in _slots_flat(player):
        hit = 0
        if slot:
            for sp in _spaces(slot):
                if sp.get("type") == T_SPECIAL and not _is_filled(sp):
                    hit = 1
                    break
        out.append(hit)
    return out


def existence_criterion6(player: dict) -> list[int]:
    """Traegt Slot i am Ende UEBERHAUPT ein Spezialfeld? (1/0 je Slot.)

    Gebraucht, weil `atoms_criterion6` UNBEDINGT ist: es wirft "kein Special in
    diesem Slot" und "Special gefuellt" in dieselbe 0. Ohne diese Maske
    vermischt jede Auswertung Risikovorhersage mit dem bloßen Ablesen der
    ANWESENHEIT -- und die steht direkt in den Brettkanaelen, ist also eine
    Nachschlagefrage. Rechnerischer Beleg fuer die Vermischung: Mittel der neun
    Slot-Grundraten 0,442 (= die berichtete c6-Grundrate), bedingte Rate je
    Brett 0,833, und 0,833 x 4,50/9 = 0,417.
    """
    out = []
    for slot in _slots_flat(player):
        hit = 0
        if slot:
            for sp in _spaces(slot):
                if sp.get("type") == T_SPECIAL:
                    hit = 1
                    break
        out.append(hit)
    return out


def atoms_criterion3(player: dict) -> list[int]:
    """Slot hat ein BELEGTES Jokerfeld UND alle Jokerfelder sind belegt."""
    wild = [sp for slot in _slots_flat(player) if slot
            for sp in _spaces(slot) if sp.get("type") == T_WILD]
    condition = bool(wild) and all(_is_filled(sp) for sp in wild)
    out = []
    for slot in _slots_flat(player):
        hit = 0
        if condition and slot:
            for sp in _spaces(slot):
                if sp.get("type") == T_WILD and _is_filled(sp):
                    hit = 1
                    break
        out.append(hit)
    return out


def labels_for_board(player: dict) -> dict[str, list[int]]:
    return {
        "c6": atoms_criterion6(player),
        "c3": atoms_criterion3(player),
        # Existenz-Maske je Slot -- ohne sie ist jede c6-Auswertung mit dem
        # Ablesen der Anwesenheit vermischt (siehe `existence_criterion6`).
        "c6_exists": existence_criterion6(player),
    }


def group_games(records: list[dict]) -> dict[str, list[dict]]:
    by = collections.defaultdict(list)
    for rec in records:
        by[rec["game_id"]].append(rec)
    return by


def iter_corpus(pattern: str, limit: int | None):
    files = sorted(glob.glob(str(REPO / "data" / pattern)))
    if limit:
        files = files[:limit]
    if not files:
        raise SystemExit(f"Keine Dateien fuer {pattern}")
    for path in files:
        with open(path, "rb") as fh:
            yield path, pickle.load(fh)


def cmd_check(args) -> int:
    """Identitaets-Pruefung gegen `scoring_tile_points` der Engine.

    -3 * sum(c6) muss dem Engine-Wert von Kriterium 6 entsprechen, 2 * sum(c3)
    dem von Kriterium 3 -- aber NUR wenn die Platte in der Partie aktiv ist
    (sonst rechnet die Engine sie nicht). Das ist derselbe Test, den
    `scoring.rs::plattenkopf_atom_identities_hold_on_real_end_boards` auf
    synthetischen Endbrettern fuehrt, hier auf echtem Korpus-Material.
    """
    ok = bad = skipped = 0
    mismatches = []
    for path, records in iter_corpus(args.pattern, args.files):
        for gid, recs in group_games(records).items():
            last = recs[-1]["state"]
            active = set(last.get("scoring_tile_ids") or [])
            for pi, player in enumerate(last["players"]):
                pts = player.get("scoring_tile_points") or []
                if len(pts) < 8:
                    skipped += 1
                    continue
                lab = labels_for_board(player)
                for crit, factor, key in ((6, -3, "c6"), (3, 2, "c3")):
                    if crit not in active:
                        continue
                    want = pts[crit]
                    got = factor * sum(lab[key])
                    if want == got:
                        ok += 1
                    else:
                        bad += 1
                        if len(mismatches) < 8:
                            mismatches.append(
                                f"{Path(path).name} {gid} P{pi} Kriterium {crit}: "
                                f"Engine {want}, Atome {got}"
                            )
    print(f"Identitaets-Pruefung: {ok} bestaetigt, {bad} abweichend, {skipped} uebersprungen")
    for m in mismatches:
        print("  ", m)
    if bad:
        print("\nABWEICHUNG -- die Atom-Definition trifft die Engine-Wertung nicht.")
        return 1
    print("\nOK -- beide Identitaeten halten auf echtem Korpus-Material.")
    return 0


def cmd_stats(args) -> int:
    """Grundraten, die ueber die Brauchbarkeit des Kopfes entscheiden."""
    c6_rate, c3_cond, wild_counts, special_counts = [], [], [], []
    active_counter = collections.Counter()
    boards = 0
    for _, records in iter_corpus(args.pattern, args.files):
        for _gid, recs in group_games(records).items():
            last = recs[-1]["state"]
            for cid in last.get("scoring_tile_ids") or []:
                active_counter[cid] += 1
            for player in last["players"]:
                boards += 1
                slots = _slots_flat(player)
                specials = [sp for s in slots if s for sp in _spaces(s) if sp.get("type") == T_SPECIAL]
                wilds = [sp for s in slots if s for sp in _spaces(s) if sp.get("type") == T_WILD]
                special_counts.append(len(specials))
                wild_counts.append(len(wilds))
                if specials:
                    empty = sum(1 for sp in specials if not _is_filled(sp))
                    c6_rate.append(empty / len(specials))
                if wilds:
                    c3_cond.append(1 if all(_is_filled(sp) for sp in wilds) else 0)

    mean = lambda v: statistics.mean(v) if v else float("nan")
    print(f"{boards} Endbretter")
    print(f"  Kriterium 6 -- Anteil LEERER Spezialfelder je Brett: {mean(c6_rate)*100:.1f}%")
    print(f"     Spezialfelder je Brett: Mittel {mean(special_counts):.2f}")
    print(f"  Kriterium 3 -- Grundrate 'alle Jokerfelder belegt': {mean(c3_cond)*100:.1f}%")
    print(f"     Jokerfelder je Brett: Mittel {mean(wild_counts):.2f}, "
          f"Spanne {min(wild_counts)}..{max(wild_counts)}")
    print("  Aktive Kriterien (Haeufigkeit ueber Partien):",
          dict(sorted(active_counter.items())))
    print("\nLesart: eine Grundrate nahe 0 oder 1 macht den Brier trivial gut und")
    print("die Trennleistung wertlos -- dann entscheidet der Brier-SKILL-Score")
    print("gegen die Grundrate, nicht der rohe Brier (PREREG_plattenkopf.md).")
    return 0


def cmd_dump(args) -> int:
    """Schreibt die Labels als eigenstaendige Datei: Partie -> 9 Atome je Spieler.

    Bewusst als SEITENDATEI und nicht in den HDF5-Cache: der Cache-Bau ist der
    gemeinsame Pfad aller Trainings, und die Labels lassen sich jederzeit
    deterministisch neu erzeugen. Wer sie in den Cache zieht, braucht dort
    zusaetzlich den Key-Suffix `+plate_v1` (Muster `+enc2d_v1`), damit der
    vorhandene v21-Cache NICHT entwertet wird -- ein
    `VALUE_SCHEMA_VERSION`-Bump waere dafuer das falsche Werkzeug.

    Nur Kriterium 6 (c6): c3 hat im Rauchtest keinen Skill, siehe
    `evaluations/PREREG_plattenkopf.md`.
    """
    import json

    out = {}
    files_done = 0
    for path, records in iter_corpus(args.pattern, args.files):
        files_done += 1
        for gid, recs in group_games(records).items():
            last = recs[-1]["state"]
            active = sorted(last.get("scoring_tile_ids") or [])
            per_player = [atoms_criterion6(p) for p in last["players"]]
            out[gid] = {"c6": per_player, "active": active}
        if files_done % 200 == 0:
            print(f"  {files_done} Dateien, {len(out)} Partien ...", flush=True)

    dest = REPO / args.out
    dest.write_text(json.dumps({
        "version": "plate_v1",
        "criterion": 6,
        "slots": NUM_SLOTS,
        "note": ("Atome je Kuppelslot: 1 = Spezialfeld am Ende LEER. Labels aus dem "
                 "LETZTEN Tiling-Schritt, nicht dem Zustand nach Spielende -- exakte "
                 "Endlabels liegen im Bestandskorpus nicht vor (siehe PREREG)."),
        "games": out,
    }), encoding="utf-8")
    print(f"{len(out)} Partien aus {files_done} Dateien -> {dest}")
    print(f"Groesse: {dest.stat().st_size/2**20:.1f} MiB")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pattern", default="selfplay_v20wdl_*.pkl",
                    help="Glob unter data/ (Default: ein v20wdl-Block)")
    ap.add_argument("--files", type=int, default=8, help="max. Dateien (0 = alle)")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("check")
    sub.add_parser("stats")
    d = sub.add_parser("dump")
    d.add_argument("--out", default="data/plate_labels_v1.json")
    args = ap.parse_args()
    args.files = args.files or None
    if args.cmd == "stats":
        return cmd_stats(args)
    if args.cmd == "dump":
        return cmd_dump(args)
    return cmd_check(args)


if __name__ == "__main__":
    raise SystemExit(main())
