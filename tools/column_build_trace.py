# -*- coding: utf-8 -*-
"""Entscheidungs-Spur des Spaltenbauers auswerten (`[SB]`-Logzeilen).

ANLASS (Nutzer-Ergaenzung 2026-08-13, VOR der Runde-2-Abnahme fuer
`engine/src/column_build.rs` angefordert): "damit die Iteration sieht, WIE die
Entscheidungen fallen, nicht nur die Aggregate". Die Engine schreibt bei
`MOSAIC_SPALTENBAU=1 MOSAIC_SPALTENBAU_TRACE=1` je Entscheidung eine
zusaetzliche Logzeile mit Praefix `[SB]` ueber den bestehenden
`log_event`-Strom (additiv, siehe `column_build.rs::trace_zeile`-Doku) --
dieses Werkzeug liest sie aus einem Arena-JSON (`--log-games`) und baut je
Partie eine Entscheidungs-Zusammenfassung.

WARUM KEIN EIGENER PARSER FUER DAS DRUMHERUM: `tools/analyze_game_log.py`
(ROUND_PREFIX) und `tools/plate_points_from_arena.py` (`partien()`, liest
Ein- oder Mehrarm-JSON) werden importiert statt nachgebaut (CLAUDE.md:
Bestehendes wiederverwenden). Nur der `[SB]`-Zeileninhalt selbst ist neu.

Zeilenformat (siehe `column_build.rs::trace_zeile`):
    [SB] Spieler=<pi> Typ=<Drafting|Dome|Tiling> Ziel=<spalte>
         Top2=[<spalte>:<kosten>,<spalte>:<kosten>]
         Vorzug=<ja VorzugAktion=<debug>|nein Grund=<wort>>
         Aktion=<debug>[ Angebot=<quelle>:<farben>;...]
`VorzugAktion`/`Grund` sind bewusst NICHT `Aktion` genannt (Namenskollision
mit dem AEUSSEREN Aktion-Feld waere fuer den Parser nicht mehr trennbar).

Aufruf:
    python -X utf8 tools/column_build_trace.py evaluations/paired_arena_env_spaltenbau_r2.json
    python -X utf8 tools/column_build_trace.py DATEI.json --json out.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

BASIS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASIS / "tools"))

from analyze_game_log import ROUND_PREFIX  # noqa: E402
from plate_points_from_arena import partien  # noqa: E402

# Nicht-gierig fuer `vorzug`, weil sein Wert bei `ja` selbst ein
# `VorzugAktion=...`-Feld mit Leerzeichen enthaelt -- der Regex-Motor
# erweitert das Nicht-gierige automatisch so weit, bis das ERSTE echte
# " Aktion=" (das aeussere Feld) passt, weil "Aktion=" in `VorzugAktion=`
# bewusst NICHT vorkommt (siehe Modul-Doc).
SB_LINE = re.compile(
    r"^\[SB\] Spieler=(?P<spieler>\d+) Typ=(?P<typ>\S+) Ziel=(?P<ziel>\d+) "
    r"Top2=\[(?P<top2>[^\]]*)\] "
    r"Vorzug=(?P<vorzug>.*?) "
    r"Aktion=(?P<aktion>.*?)"
    r"(?: Angebot=(?P<angebot>.*))?$"
)


@dataclass
class Entscheidung:
    runde: int
    spieler: int
    typ: str
    ziel: int
    top2: str
    vorzug_ja: bool
    vorzug_grund: str | None
    vorzug_aktion: str | None
    aktion: str
    angebot: str | None


def parse_sb_zeilen(log: list[str]) -> list[Entscheidung]:
    """Alle `[SB]`-Zeilen EINER Partie -> geordnete Liste von Entscheidungen.
    Zeilen, die nicht passen (sollte bei unveraendertem Format nicht
    vorkommen), werden STILL uebersprungen -- dieses Werkzeug ist Diagnose,
    kein Korrektheitsnachweis der Engine (der liegt in `column_build.rs`s
    eigenen Rust-Tests)."""
    out: list[Entscheidung] = []
    for roh in log or []:
        m = ROUND_PREFIX.match(roh)
        if not m:
            continue
        runde = int(m.group(1))
        text = m.group(2)
        sb = SB_LINE.match(text)
        if not sb:
            continue
        vorzug_raw = sb.group("vorzug")
        vorzug_ja = vorzug_raw.startswith("ja")
        vorzug_grund = None
        vorzug_aktion = None
        if vorzug_ja:
            vm = re.match(r"^ja VorzugAktion=(.*)$", vorzug_raw)
            vorzug_aktion = vm.group(1) if vm else vorzug_raw
        else:
            gm = re.match(r"^nein Grund=(\S+)$", vorzug_raw)
            vorzug_grund = gm.group(1) if gm else vorzug_raw
        out.append(
            Entscheidung(
                runde=runde,
                spieler=int(sb.group("spieler")),
                typ=sb.group("typ"),
                ziel=int(sb.group("ziel")),
                top2=sb.group("top2"),
                vorzug_ja=vorzug_ja,
                vorzug_grund=vorzug_grund,
                vorzug_aktion=vorzug_aktion,
                aktion=sb.group("aktion"),
                angebot=sb.group("angebot"),
            )
        )
    return out


@dataclass
class PartieZusammenfassung:
    seed: int | None
    n_entscheidungen: int
    je_runde_entscheidungen: dict[int, int] = field(default_factory=dict)
    je_runde_vorzug_existiert: dict[int, int] = field(default_factory=dict)
    je_runde_vorzug_genutzt: dict[int, int] = field(default_factory=dict)
    ziel_verlauf: list[tuple[int, int]] = field(default_factory=list)  # (runde, ziel)
    ziel_stagnation_ab_runde: int | None = None
    blocker_ketten: list[str] = field(default_factory=list)


def zusammenfassen(entscheidungen: list[Entscheidung], seed: int | None) -> PartieZusammenfassung:
    z = PartieZusammenfassung(seed=seed, n_entscheidungen=len(entscheidungen))
    if not entscheidungen:
        return z

    for e in entscheidungen:
        # "existiert" heisst NUR `vorzug_ja` (ein echter Kandidat war da) --
        # `vorzug_grund` ist der GEGENTEIL-Fall (kein Kandidat, mit Begruendung
        # warum nicht) und darf hier NICHT mitzaehlen (Fund beim ersten Lauf:
        # jede Entscheidung hat entweder `ja` ODER `nein Grund=...`, "existiert
        # ODER hat einen Grund" ist also IMMER wahr und zaehlt schlicht alle
        # Entscheidungen -- kein sinnvolles Signal).
        z.je_runde_entscheidungen[e.runde] = z.je_runde_entscheidungen.get(e.runde, 0) + 1
        if e.vorzug_ja:
            z.je_runde_vorzug_existiert[e.runde] = z.je_runde_vorzug_existiert.get(e.runde, 0) + 1
            if e.vorzug_aktion == e.aktion:
                z.je_runde_vorzug_genutzt[e.runde] = z.je_runde_vorzug_genutzt.get(e.runde, 0) + 1

    # Zielspalten-Verlauf (nur EINE Zeile je Runde, die letzte Drafting-
    # Entscheidung dieser Runde reicht als Repraesentant).
    letzte_je_runde: dict[int, int] = {}
    for e in entscheidungen:
        if e.typ == "Drafting":
            letzte_je_runde[e.runde] = e.ziel
    z.ziel_verlauf = sorted(letzte_je_runde.items())

    # Stagnation: erste Runde, ab der die Zielspalte bis zum Partieende
    # unveraendert bleibt.
    if z.ziel_verlauf:
        letzter_wert = z.ziel_verlauf[-1][1]
        for runde, ziel in reversed(z.ziel_verlauf):
            if ziel != letzter_wert:
                z.ziel_stagnation_ab_runde = runde_nach(z.ziel_verlauf, runde)
                break
        else:
            z.ziel_stagnation_ab_runde = z.ziel_verlauf[0][0]

    # Blocker-Ketten: fuer jede Zeile/Grund-Kombination aus den nein-Faellen,
    # in welchen Runden sie auftrat und ob die geforderte Farbe in SPAETEREN
    # Runden ueberhaupt je im Angebot war (die "Farbe kam nie zusammen"-Frage).
    gruende_je_zeile: dict[str, list[int]] = defaultdict(list)
    for e in entscheidungen:
        if e.vorzug_grund and e.vorzug_grund.startswith("Zeile"):
            zeile_id = e.vorzug_grund.split(":", 1)[0]
            gruende_je_zeile[zeile_id + ":" + e.vorzug_grund.split(":", 1)[1]].append(e.runde)
    for grund, runden in sorted(gruende_je_zeile.items()):
        erste, letzte = min(runden), max(runden)
        z.blocker_ketten.append(
            f"{grund} blockierte Runde {erste}..{letzte} ({len(runden)}x)"
        )
    return z


def runde_nach(verlauf: list[tuple[int, int]], runde: int) -> int:
    """Kleinste Runde im Verlauf, die STRIKT nach `runde` liegt -- Hilfsfunktion
    fuer die Stagnations-Suche (naechste Runde nach dem letzten Wechsel)."""
    kandidaten = [r for r, _ in verlauf if r > runde]
    return min(kandidaten) if kandidaten else runde


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("datei", type=Path)
    p.add_argument("--json", type=Path, default=None, help="Zusammenfassung zusaetzlich als JSON schreiben")
    a = p.parse_args()

    spiele = partien(a.datei)
    zusammenfassungen: list[PartieZusammenfassung] = []
    ziel_haeufigkeit: Counter[int] = Counter()
    ohne_sb_zeilen = 0

    for sp in spiele:
        log = sp.get("log") or []
        entscheidungen = parse_sb_zeilen(log)
        if not entscheidungen:
            ohne_sb_zeilen += 1
            continue
        z = zusammenfassen(entscheidungen, sp.get("game_seed"))
        zusammenfassungen.append(z)
        for _, ziel in z.ziel_verlauf:
            ziel_haeufigkeit[ziel] += 1

    print(f"{len(spiele)} Partien, {len(zusammenfassungen)} mit [SB]-Zeilen, "
          f"{ohne_sb_zeilen} ohne (Trace-Knopf aus oder Spaltenbauer inaktiv).")
    print()
    print("Zielspalten-Verteilung (Ereignisse je Runde ueber alle Partien):")
    for spalte in range(6):
        print(f"  Spalte {spalte}: {ziel_haeufigkeit.get(spalte, 0)}")
    fehlende = [s for s in range(6) if ziel_haeufigkeit.get(s, 0) == 0]
    if fehlende:
        print(f"  WARNUNG: Spalten ohne jedes Ereignis: {fehlende}")
    print()

    print(f"{'Seed':>12} {'Entsch.':>8} {'Stagnation ab':>14}  Blocker-Ketten")
    for z in zusammenfassungen:
        stagn = str(z.ziel_stagnation_ab_runde) if z.ziel_stagnation_ab_runde is not None else "-"
        ketten = "; ".join(z.blocker_ketten) if z.blocker_ketten else "-"
        print(f"{str(z.seed):>12} {z.n_entscheidungen:>8} {stagn:>14}  {ketten}")

    if a.json:
        out = {
            "n_partien": len(spiele),
            "n_mit_trace": len(zusammenfassungen),
            "n_ohne_trace": ohne_sb_zeilen,
            "zielspalten_verteilung": {str(s): ziel_haeufigkeit.get(s, 0) for s in range(6)},
            "partien": [
                {
                    "seed": z.seed,
                    "n_entscheidungen": z.n_entscheidungen,
                    "ziel_verlauf": z.ziel_verlauf,
                    "ziel_stagnation_ab_runde": z.ziel_stagnation_ab_runde,
                    "je_runde_entscheidungen": z.je_runde_entscheidungen,
                    "je_runde_vorzug_existiert": z.je_runde_vorzug_existiert,
                    "je_runde_vorzug_genutzt": z.je_runde_vorzug_genutzt,
                    "blocker_ketten": z.blocker_ketten,
                }
                for z in zusammenfassungen
            ],
        }
        a.json.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\ngeschrieben -> {a.json}")


if __name__ == "__main__":
    main()
