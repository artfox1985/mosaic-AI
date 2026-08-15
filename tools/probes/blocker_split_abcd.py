# -*- coding: utf-8 -*-
"""Aufspaltung des "Farbe nicht im Angebot"-Blockers (74-77%, PREREG_provokation
§11/§12) in a/b/c/d (Nutzer/Koordinator-Auftrag).

METHODE (v2 -- verbessert gegenueber der ersten Fassung: benutzt die FIXE
Kuppelplatten-Geometrie aus engine/src/dome.rs:201-233 (GEPRUEFT, Zeilen
zitiert) statt die geforderte Farbe aus den [SB]-Grund-Texten zu erraten --
`kein_vorzug_grund` nennt nur die ERSTE blockierende Zeile, das verdeckt die
Zeile, die uns tatsaechlich interessiert (die eine offene "Mauer"-Zelle),
in den meisten Partien. Die Kachel-Palette ist dagegen ein FESTER, 18-
Platten-Katalog (tile_id 0..18 fortlaufend, dome.rs:201 `build_dome_tile_pool`)
-- aus (tile_id, slot_row, slot_col, rotation), die JEDE "Kachel X -> Slot
(r,c) rot=d Grad"-Logzeile trägt, folgt die geforderte Farbe JEDER der 4
Zellen deterministisch, ohne jede Spielzustands-Abhaengigkeit.

Schritte:
1. Aus dem Log werden fuer den Netz-Spieler (immer Spieler 0 -- GEPRUEFT per
   Zaehlung: alle 1674 [SB]-Zeilen in r3 tragen Spieler=0) rekonstruiert:
   - grid_structure[(r,c)] = (space_type, required_color) aus jeder
     "Kachel/Startkachel ... -> Slot (sr,sc) rot=d" bzw. "-> (sr,sc) rot=d"
     Zeile, per rotation_indices (dome.rs:89-97, hier 1:1 uebernommen) und
     dem festen Kachel-Katalog.
   - grid_filled[(r,c)] = Farbe aus "<Name>: <Farbe> -> Slot (sr,sc) Space i"
     (Tiling-Platzierung).
   - pattern_color[r]: Farbe, an die Musterreihe r JETZT gebunden ist, aus
     "-> Reihe N [k/m]"; zurueckgesetzt bei Tiling-Platzierung derselben
     Zeile oder bei "... nicht platzierbar -> Strafleiste" (game.rs:844-850).
2. "Mauer"-Zelle: letzte Zielspalte aus dem [SB]-Trace (Ziel=..), darin GENAU
   EINE Zeile r_open ohne Fill, UND diese Zeile ist laut grid_structure
   Normal (Wild/Special sind kein Farb-Blocker in diesem Sinne -- eigene
   Kategorie unten). X = required_color dieser Zelle (jetzt IMMER bekannt,
   sobald ein Tile dort liegt -- 0 "X_unbekannt"-Faelle erwartet, ausser eine
   Partie hat dort nie eine Platte gelegt).
3. Klassifikation ueber alle Drafting-Entscheidungen der Partie (chronologisch,
   nicht nur mit Ziel==ziel -- die Zellen-Identitaet ist jetzt orts-fest durch
   grid_structure, unabhaengig von der zeitweiligen Zielspalten-Wahl):
   fuer jeden Moment, an dem X im Angebot war:
     - Zeile r_open zu diesem Zeitpunkt an ANDERE Farbe gebunden -> (b).
     - Zeile r_open offen (ungebunden), tatsaechliche Aktion nahm NICHT
       (X, r_open) -> (c) Vorzugs-Luecke.
     - Zeile r_open offen, Aktion nahm GENAU (X, r_open) -> kein Blocker,
       weitersuchen (das war der Erfolgsfall, sollte selten VOR Partieende
       auftreten, sonst waere die Zelle gefuellt).
   Kommt X in KEINEM Moment vor, waehrend r_open ungebunden war: entweder nie
   verfuegbar (a) oder verfuegbar NUR waehrend r_open falsch gebunden war
   (dann ist die FRUEHESTE solche Gelegenheit (b), s.o. -- wird in der Schleife
   bereits gefangen). Bleibt keine Gelegenheit uebrig: pruefen, ob X je an
   r_open GEBUNDEN wurde (reihe_fill-Ereignis) -- wenn ja, aber nie ankam:
   (d) gebunden-aber-nicht-angekommen (Routing/Strafleiste). Sonst (a).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from collections import Counter

REPO = Path(r"D:\OneDrive\Documents\Projekte\mosaic-AI")
sys.path.insert(0, str(REPO / "tools"))

from analyze_game_log import ROUND_PREFIX  # noqa: E402

# ── Kachel-Katalog, 1:1 aus dome.rs:201-233 (GEPRUEFT per Read) ─────────────
N, W, S = "N", "W", "S"  # Normal, Wild, Special
DOME_POOL: list[list[tuple[str, str | None]]] = [
    [(N, "Gelb"), (N, "Schwarz"), (N, "Tuerkis"), (S, None)],
    [(W, None), (N, "Blau"), (N, "Tuerkis"), (N, "Schwarz")],
    [(N, "Tuerkis"), (N, "Rot"), (N, "Blau"), (W, None)],
    [(N, "Schwarz"), (N, "Gelb"), (N, "Rot"), (W, None)],
    [(N, "Schwarz"), (S, None), (N, "Tuerkis"), (N, "Rot")],
    [(N, "Tuerkis"), (N, "Gelb"), (W, None), (N, "Schwarz")],
    [(S, None), (N, "Schwarz"), (N, "Rot"), (N, "Blau")],
    [(N, "Gelb"), (N, "Blau"), (N, "Schwarz"), (S, None)],
    [(N, "Tuerkis"), (N, "Rot"), (N, "Blau"), (S, None)],
    [(N, "Gelb"), (N, "Rot"), (W, None), (N, "Blau")],
    [(N, "Gelb"), (S, None), (N, "Schwarz"), (N, "Rot")],
    [(N, "Tuerkis"), (N, "Schwarz"), (N, "Rot"), (W, None)],
    [(N, "Blau"), (N, "Schwarz"), (S, None), (N, "Tuerkis")],
    [(N, "Rot"), (N, "Tuerkis"), (N, "Gelb"), (W, None)],
    [(N, "Tuerkis"), (N, "Blau"), (W, None), (N, "Gelb")],
    [(S, None), (N, "Tuerkis"), (N, "Gelb"), (N, "Blau")],
    [(N, "Rot"), (W, None), (N, "Blau"), (N, "Schwarz")],
    [(S, None), (N, "Gelb"), (N, "Blau"), (N, "Rot")],
]
ROTATION_IDX = {0: [0, 1, 2, 3], 90: [2, 0, 3, 1], 180: [3, 2, 1, 0], 270: [1, 3, 0, 2]}

_COLOR_MAP = {"rot": "Rot", "blau": "Blau", "gelb": "Gelb", "schwarz": "Schwarz", "türkis": "Tuerkis"}


def norm_color(raw: str) -> str:
    return _COLOR_MAP.get(raw.lower(), raw)


TILE_PLACE_RE = re.compile(r"^(Netz|Heuristik): (?:Startkachel|Kachel) (\d+) → \((\d+),(\d+)\)|^(Netz|Heuristik): Kachel (\d+) → Slot \((\d+),(\d+)\) rot=(\d+)°")
STARTKACHEL_RE = re.compile(r"^(Netz|Heuristik): Startkachel (\d+) → \((\d+),(\d+)\) rot=(\d+)°")
KACHEL_RE = re.compile(r"^(Netz|Heuristik): Kachel (\d+) → Slot \((\d+),(\d+)\) rot=(\d+)°")
FILL_RE = re.compile(r"^(Netz|Heuristik): (rot|blau|gelb|schwarz|türkis) → Slot \((\d+),(\d+)\) Space (\d+)", re.IGNORECASE)
REIHE_RE = re.compile(r"^.*?(Netz|Heuristik): .* → Reihe (\d+) \[(\d+)/(\d+)\]")
DISCARD_RE = re.compile(r"^.*?(Netz|Heuristik): Musterreihe (\d+) \((\w+)\) nicht platzierbar")
SB_RE = re.compile(
    r"^\[SB\] Spieler=(?P<spieler>\d+) Typ=(?P<typ>\S+) Ziel=(?P<ziel>\d+) "
    r"Top2=\[(?P<top2>[^\]]*)\] "
    r"Vorzug=(?P<vorzug>.*?) "
    r"Aktion=(?P<aktion>.*?)"
    r"(?: Angebot=(?P<angebot>.*))?$"
)
AKTION_COLOR_ROW = re.compile(r"color: (\w+),.*row_index: (\d+) \}")


def parse_angebot(angebot_raw: str | None) -> set[str]:
    if not angebot_raw or angebot_raw == "keine_zuege":
        return set()
    farben: set[str] = set()
    for teil in angebot_raw.split(";"):
        if ":" not in teil:
            continue
        _, farben_teil = teil.split(":", 1)
        farben.update(farben_teil.split("+"))
    return farben


def load_games(path: Path, arm: str = "1") -> list[dict]:
    d = json.loads(path.read_text(encoding="utf-8"))
    return d["games"][arm]


class GameRecon:
    def __init__(self, log: list[str]):
        self.pattern_color: list[str | None] = [None] * 6
        self.grid_filled: dict[tuple[int, int], str] = {}
        self.grid_structure: dict[tuple[int, int], tuple[str, str | None]] = {}
        self.ziel_verlauf: list[tuple[int, int]] = []
        self.events: list[dict] = []
        self._run(log)

    def _place_tile(self, tile_id: int, sr: int, sc: int, rot: int) -> None:
        tile = DOME_POOL[tile_id]
        idx = ROTATION_IDX[rot]
        for i in range(4):
            space_type, req = tile[idx[i]]
            r, c = sr * 2 + i // 2, sc * 2 + i % 2
            self.grid_structure[(r, c)] = (space_type, req)

    def _run(self, log: list[str]) -> None:
        for roh in log:
            m = ROUND_PREFIX.match(roh)
            if not m:
                continue
            runde = int(m.group(1))
            text = m.group(2)

            sk = STARTKACHEL_RE.match(text)
            if sk:
                who, tid, sr, sc, rot = sk.groups()
                if who == "Netz":
                    self._place_tile(int(tid), int(sr), int(sc), int(rot))
                continue

            km = KACHEL_RE.match(text)
            if km:
                who, tid, sr, sc, rot = km.groups()
                if who == "Netz":
                    self._place_tile(int(tid), int(sr), int(sc), int(rot))
                continue

            fm = FILL_RE.match(text)
            if fm:
                who, farbe, sr, sc, si = fm.groups()
                sr, sc, si = int(sr), int(sc), int(si)
                r, c = sr * 2 + si // 2, sc * 2 + si % 2
                if who == "Netz":
                    self.grid_filled[(r, c)] = norm_color(farbe)
                    self.events.append({"typ": "fill", "runde": runde, "row": r, "col": c, "farbe": norm_color(farbe)})
                continue

            rm = REIHE_RE.match(text)
            if rm:
                who = rm.group(1)
                row1 = int(rm.group(2))
                if who == "Netz":
                    r = row1 - 1
                    cm = re.search(r"\b(rot|blau|gelb|schwarz|türkis)\b", text, re.IGNORECASE)
                    farbe = norm_color(cm.group(1)) if cm else None
                    if farbe and 0 <= r < 6:
                        self.pattern_color[r] = farbe
                        self.events.append({"typ": "reihe_fill", "runde": runde, "row": r, "farbe": farbe})
                continue

            dm = DISCARD_RE.match(text)
            if dm:
                who, row, farbe = dm.groups()
                if who == "Netz":
                    r = int(row) - 1
                    self.events.append({"typ": "discard", "runde": runde, "row": r, "farbe": norm_color(farbe)})
                    if 0 <= r < 6:
                        self.pattern_color[r] = None
                continue

            sbm = SB_RE.match(text)
            if sbm:
                ziel = int(sbm.group("ziel"))
                typ = sbm.group("typ")
                self.ziel_verlauf.append((runde, ziel, typ))
                if typ == "Drafting":
                    angebot = parse_angebot(sbm.group("angebot"))
                    aktion_cm = AKTION_COLOR_ROW.search(sbm.group("aktion"))
                    aktion_farbe = norm_color(aktion_cm.group(1)) if aktion_cm else None
                    aktion_row = int(aktion_cm.group(2)) if aktion_cm else None
                    vorzug_raw = sbm.group("vorzug")
                    vorzug_ja = vorzug_raw.startswith("ja")
                    vorzug_aktion_row = None
                    if vorzug_ja:
                        vm = AKTION_COLOR_ROW.search(vorzug_raw)
                        if vm:
                            vorzug_aktion_row = int(vm.group(2))
                    self.events.append({
                        "typ": "drafting_sb", "runde": runde, "ziel": ziel, "angebot": angebot,
                        "aktion_farbe": aktion_farbe, "aktion_row": aktion_row,
                        "vorzug_ja": vorzug_ja, "vorzug_aktion_row": vorzug_aktion_row,
                        "pattern_snapshot": tuple(self.pattern_color),
                    })


def special_filled(recon: GameRecon, r: int, c: int) -> bool:
    """Eine Special-Zelle gilt als gefuellt, wenn ihre 3 Slot-Nachbarn (selber
    2x2-Slot, ueber BEIDE Spalten des Slots hinweg -- dome.rs::
    check_special_trigger) alle gefuellt sind. Deterministisch aus
    grid_structure/grid_filled ableitbar, ohne eigene Farbe (dome.rs:320-325:
    `placed_special=true`, keine Farbzuweisung)."""
    sr, sc = r // 2, c // 2
    for dr in range(2):
        for dc in range(2):
            rr, cc = sr * 2 + dr, sc * 2 + dc
            if (rr, cc) == (r, c):
                continue
            st = recon.grid_structure.get((rr, cc))
            if st is None:
                return False
            if st[0] == "S":
                continue  # zweite Special-Zelle im selben Slot kommt laut Katalog nie vor.
            if (rr, cc) not in recon.grid_filled:
                return False
    return True


def is_filled(recon: GameRecon, r: int, c: int) -> bool | None:
    st = recon.grid_structure.get((r, c))
    if st is None:
        return None
    if st[0] == "S":
        return special_filled(recon, r, c)
    return (r, c) in recon.grid_filled


def find_mauer_zellen(recon: GameRecon) -> list[tuple[int, int]]:
    """Alle Spalten mit GENAU 1 offener Zelle (von 6 belegten Slots) --
    unabhaengig von der zuletzt verfolgten Zielspalte (die Zielspalte kann
    zwischenzeitlich woandershin gezeigt haben, waehrend eine FRUeHERE Spalte
    tatsaechlich zur Mauer wurde)."""
    treffer = []
    for c in range(6):
        slots = [recon.grid_structure.get((r, c)) for r in range(6)]
        if any(s is None for s in slots):
            continue  # Spalte nicht komplett belegt (Platte fehlt), kein Urteil moeglich.
        offene = [r for r in range(6) if is_filled(recon, r, c) is False]
        if len(offene) == 1:
            treffer.append((offene[0], c))
    return treffer


def klassifiziere(recon: GameRecon, r_open: int, ziel: int) -> tuple[str, dict]:
    st = recon.grid_structure.get((r_open, ziel))
    if st is None:
        return "keine_platte_dort", {}
    space_type, x = st
    if space_type == "W":
        return "wild_ohne_farbzwang", {}
    if space_type == "S":
        return "special_zelle_offen_slot_nachbarn_unvollstaendig", {}
    if x is None:
        return "keine_platte_dort", {}

    for ev in recon.events:
        if ev["typ"] != "drafting_sb":
            continue
        if x not in ev["angebot"]:
            continue
        snap = ev["pattern_snapshot"][r_open]
        if snap is not None and snap != x:
            return "b_reihe_falsch_gebunden", {"x": x, "runde": ev["runde"], "gebunden_an": snap}
        if snap is None:
            if ev["aktion_farbe"] == x and ev["aktion_row"] == r_open:
                continue  # Erfolgsmoment, kein Blocker -- weitersuchen.
            # §17 Teil 2: Ursachen-Unterklassifikation des (c)-Falls anhand
            # der VORHANDENEN [SB]-Signale (Ziel=, Vorzug=ja/nein) -- KEINE
            # neue Instrumentierung, nur genauer gelesen.
            if ev["ziel"] != ziel:
                ursache = "c1_zielwahl_andere_spalte"
            elif ev["vorzug_ja"]:
                if ev["vorzug_aktion_row"] == r_open:
                    ursache = "c2_vorzug_empfahl_r_open_aktion_widersprach"
                else:
                    ursache = "c3_vorzug_waehlte_andere_zeile_derselben_spalte"
            else:
                ursache = "c4_kein_vorzugskandidat_trotz_verfuegbarkeit"
            return "c_vorzug_griff_nicht", {
                "x": x, "runde": ev["runde"], "tatsaechlich": ev["aktion_farbe"],
                "aktion_row": ev["aktion_row"], "ursache": ursache, "ziel_damals": ev["ziel"],
            }
        # snap == x: Zeile schon korrekt gebunden, kein Blocker.

    wurde_gebunden = any(
        ev["typ"] == "reihe_fill" and ev["row"] == r_open and ev["farbe"] == x for ev in recon.events
    )
    if wurde_gebunden:
        verworfen = any(
            ev["typ"] == "discard" and ev["row"] == r_open and ev["farbe"] == x for ev in recon.events
        )
        return "d_gebunden_aber_nicht_angekommen", {"x": x, "verworfen": verworfen}
    return "a_nie_verfuegbar", {"x": x}


def main() -> None:
    for runde_name, dateiname in [("Runde 3", "paired_arena_env_spaltenbau_r3.json"), ("Runde 2", "paired_arena_env_spaltenbau_r2.json")]:
        pfad = REPO / "evaluations" / dateiname
        if not pfad.exists():
            continue
        spiele = load_games(pfad)
        zaehler: Counter[str] = Counter()
        details = []
        n_partien_mit_mauer = 0
        n_mauer_zellen = 0
        for sp in spiele:
            recon = GameRecon(sp.get("log") or [])
            zellen = find_mauer_zellen(recon)
            if zellen:
                n_partien_mit_mauer += 1
            for r_open, ziel in zellen:
                n_mauer_zellen += 1
                kat, info = klassifiziere(recon, r_open, ziel)
                zaehler[kat] += 1
                details.append({"seed": sp.get("game_seed"), "spalte": ziel, "row": r_open, "kat": kat, "info": info})

        print(f"=== {runde_name} ({dateiname}) ===")
        print(f"{len(spiele)} Partien, {n_partien_mit_mauer} mit mindestens einer 5/6-Mauer-Spalte, "
              f"{n_mauer_zellen} Mauer-Zellen insgesamt (Partien koennen mehrere Wand-Spalten haben).")
        print()
        gesamt = sum(zaehler.values())
        for kat, n in sorted(zaehler.items(), key=lambda kv: -kv[1]):
            pct = 100.0 * n / gesamt if gesamt else 0.0
            print(f"  {kat:35s} {n:3d}  ({pct:5.1f}%)")
        print()
        for d in details:
            print(" ", d)
        print()


if __name__ == "__main__":
    main()
