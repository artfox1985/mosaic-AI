# -*- coding: utf-8 -*-
"""Strukturelle Spaltenbau-Messung an VORHANDENEN Arena-Partien (Auftrag
2026-08-23): verifiziert die Nutzer-Beobachtung "v21 baut so gut wie keine
Spalten, unabhaengig von den Wertungsplatten" strukturell -- am rekonstru-
ierten Kuppel-Endstand, nicht nur an den k1-Wertungszeilen.

LASTSPERRE (Koordinator-Auftrag): auf der Maschine laufen parallel
lastempfindliche Byte-Identitaets-Beweise eines anderen Agenten. Dieses
Werkzeug liest NUR Dateien und rechnet single-thread in Python -- KEIN
mosaic_rust-Import, KEIN Engine-Replay, kein Build.

Rekonstruktionsweg (Schritt 1 des Auftrags: "erst schauen was da ist"):
  - Log-Regexe/Praefix-Behandlung: `analyze_game_log.PATTERNS`/`ROUND_PREFIX`
    (1:1 aus den log_event(...)-Aufrufen der Engine transkribiert -- siehe
    dortiger Modul-Docstring; hier importiert, nicht nachgebaut).
  - Mehr-/Ein-Arm-JSON-Laden: `plate_points_from_arena.game_list()`.
  - Endwertungs-Kriterienzeile ("   emoji Name: N Pkt", NUR direkt nach
    einer Endwertungs-Zeile): `plate_points_from_arena.KRITERIUM`.
  - Spalten-Mapping (Slot (tr,tc), Space-Index si) -> Spalte `2*tc + si%2`:
    identisch zu `seed_position_curation.col_fill_py`, das seinerseits
    gegen `mosaic_rust.plate_completability_json` verifiziert ist (dortiger
    Modul-Docstring). Hier NUR aus Log-TEXTZEILEN gespeist statt aus dem
    Board-JSON -- die Geometrie wird UEBERNOMMEN, nicht neu erfunden.

Geometrie-Pruefstellen (GEPRUEFT, nicht vermutet):
  - docs/engine_manual.md Abschnitt 2 ("Player board"): Kuppel = 3x3 Slots,
    je Slot ein 2x2-Kuppelplaettchen -> 6x6-Endraster.
  - docs/engine_manual.md Abschnitt 6, Zeile "Vertikale Reihen": 7 Pkt je
    VOLLSTAENDIGE vertikale Spalte (6 Zellen).
  - engine/src/round_end.rs::execute_tiling_action / check_special_trigger
    (Zeilen ~252-354, gelesen in dieser Sitzung): der Spezialfeld-Slot einer
    Kuppelplatte wird IMMER in DERSELBEN `execute_full_tiling`-Aktion
    gefuellt, die ihn freischaltet (`try_unlock_special` unmittelbar gefolgt
    von `check_special_trigger` im selben Aufruf) -- die TILING_PLACE-Zeile
    mit Suffix " [Special freigeschaltet!]" fuellt also ZWEI Zellen der
    gleichen Kachel: die geloggte Farb-/Jokerzelle UND die Spezialfeld-
    zelle. Deren lokaler Index steht NICHT im Log und wird hier aus dem
    STATISCHEN 18-Kacheln-Katalog (engine/src/dome.rs::build_dome_tile_pool,
    Zeilen 201-233, unten wortgetreu transkribiert -- reine Konstanten-
    daten, kein Funktionsaufruf) plus der geloggten Rotation (DOME_PLACE/
    START_TILE) hergeleitet: `dome.rs::rotated_spaces`/`rotation_indices`
    (Zeilen 87-96) legen fest, dass nach einer Drehung um `deg` Grad gilt
    `neue_spaces[j] = alte_spaces[idx[j]]` -- der gesuchte neue Index des
    Spezialfelds ist also `idx.index(alter_index)`.

Korrektheitsbeweis (Schritt 2 des Auftrags): in JEDER Partie/Seite, in der
die Wertungsplatte "Vertikale Reihen" (k1, scoring_tile id=1) aktiv war,
MUSS die geloggte Punktzahl exakt `7 * <rekonstruierte volle Spalten>`
sein. Jede Abweichung ist ein Rekonstruktionsfehler -> Abbruch mit Beispiel.

Aufruf:
    python -X utf8 tools/probes/column_build_structural_probe.py
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from analyze_game_log import PATTERNS, ROUND_PREFIX  # noqa: E402
from plate_points_from_arena import game_list, KRITERIUM  # noqa: E402

EVAL = ROOT / "evaluations"
OUT_JSON = EVAL / "artifacts" / "column_build_structural_probe.json"

# ── Statischer Kuppelplaettchen-Katalog (engine/src/dome.rs:201-233, wort-
# getreu transkribiert -- KEIN Engine-Aufruf, reine Konstantendaten). Nur der
# lokale Index des SPECIAL-Space (0=oben-links,1=oben-rechts,2=unten-links,
# 3=unten-rechts) wird gebraucht; Farben sind fuer die Spaltenzaehlung ohne
# Belang (jede gefuellte Zelle zaehlt gleich, unabhaengig von der Farbe).
_DEFS_RAW = [
    ["n", "n", "n", "s"],  # 0
    ["w", "n", "n", "n"],  # 1
    ["n", "n", "n", "w"],  # 2
    ["n", "n", "n", "w"],  # 3
    ["n", "s", "n", "n"],  # 4
    ["n", "n", "w", "n"],  # 5
    ["s", "n", "n", "n"],  # 6
    ["n", "n", "n", "s"],  # 7
    ["n", "n", "n", "s"],  # 8
    ["n", "n", "w", "n"],  # 9
    ["n", "s", "n", "n"],  # 10
    ["n", "n", "n", "w"],  # 11
    ["n", "n", "s", "n"],  # 12
    ["n", "n", "n", "w"],  # 13
    ["n", "n", "w", "n"],  # 14
    ["s", "n", "n", "n"],  # 15
    ["n", "w", "n", "n"],  # 16
    ["s", "n", "n", "n"],  # 17
]
DOME_TILE_SPECIAL_LOCAL_IDX: dict[int, int | None] = {
    i: (row.index("s") if "s" in row else None) for i, row in enumerate(_DEFS_RAW)
}
assert sum(1 for v in DOME_TILE_SPECIAL_LOCAL_IDX.values() if v is not None) == 9, (
    "Katalog-Transkriptionsfehler: 9 der 18 Platten muessen ein Spezialfeld tragen "
    "(docs/engine_manual.md Abschnitt 5)"
)

# engine/src/dome.rs::rotation_indices (Zeilen 89-96), wortgetreu.
ROTATION_IDX: dict[int, tuple[int, int, int, int]] = {
    0: (0, 1, 2, 3),
    90: (2, 0, 3, 1),
    180: (3, 2, 1, 0),
    270: (1, 3, 0, 2),
}


def rotated_special_local_index(tile_id: int, rot: int) -> int | None:
    sp0 = DOME_TILE_SPECIAL_LOCAL_IDX.get(tile_id)
    if sp0 is None:
        return None
    idx = ROTATION_IDX[rot]
    return idx.index(sp0)


# ── Log -> Zellen je Spieler (nur Textzeilen, kein Replay) ─────────────────

def reconstruct_game(log: list[str]) -> dict[str, set[tuple[int, int, int]]]:
    """{spielername: {(slot_row, slot_col, space_index), ...}} -- alle
    gefuellten 6x6-Zellen, aus DOME_PLACE/START_TILE (Kachel+Rotation je
    Slot) und TILING_PLACE (gefuellte Farb-/Jokerzelle + ggf. mitgefuellte
    Spezialzelle, siehe Modul-Doc) hergeleitet."""
    slot_tile: dict[str, dict[tuple[int, int], tuple[int, int]]] = defaultdict(dict)
    cells: dict[str, set[tuple[int, int, int]]] = defaultdict(set)
    for roh in log or []:
        if roh.startswith("#"):
            continue
        m = ROUND_PREFIX.match(roh)
        text = m.group(2) if m else roh

        mm = PATTERNS["START_TILE"].match(text)
        if mm:
            slot_tile[mm.group("name")][(int(mm.group("row")), int(mm.group("col")))] = (
                int(mm.group("tile")), int(mm.group("rot")),
            )
            continue

        mm = PATTERNS["DOME_PLACE"].match(text)
        if mm:
            slot_tile[mm.group("name")][(int(mm.group("r")), int(mm.group("c")))] = (
                int(mm.group("tile")), int(mm.group("rot")),
            )
            continue

        mm = PATTERNS["TILING_PLACE"].match(text)
        if mm:
            name = mm.group("name")
            r, c, si = int(mm.group("r")), int(mm.group("c")), int(mm.group("si"))
            cells[name].add((r, c, si))
            if mm.group("special"):
                tile_rot = slot_tile[name].get((r, c))
                if tile_rot is None:
                    raise ValueError(
                        f"'[Special freigeschaltet!]' an Slot ({r},{c}) fuer {name}, "
                        "aber keine vorausgehende DOME_PLACE/START_TILE-Zeile fuer "
                        "diesen Slot bekannt -- Rekonstruktion inkonsistent."
                    )
                tile_id, rot = tile_rot
                sp_si = rotated_special_local_index(tile_id, rot)
                if sp_si is None:
                    raise ValueError(
                        f"'[Special freigeschaltet!]' an Kachel {tile_id} (Slot ({r},{c})), "
                        "aber Katalog kennt dort kein Spezialfeld -- Katalog-Fehler."
                    )
                cells[name].add((r, c, sp_si))
            continue
    return cells


def column_fill(cells: set[tuple[int, int, int]]) -> list[int]:
    """`col_fill_py`-Mapping (seed_position_curation.py, dort gegen die
    Engine verifiziert): Slot (tr,tc), Space si -> Spalte 2*tc + si%2."""
    fill = [0] * 6
    for (_r, c, si) in cells:
        fill[2 * c + (si % 2)] += 1
    return fill


def struktur_kennzahlen(fill: list[int]) -> dict:
    return {
        "fill": fill,
        "volle_spalten": sum(1 for f in fill if f == 6),
        "max_hoehe": max(fill) if fill else 0,
        "teilspalten_ge3": sum(1 for f in fill if f >= 3),
        "teilspalten_ge4": sum(1 for f in fill if f >= 4),
    }


def final_scoring_criteria_per_player(log: list[str]) -> dict[str, dict[str, int]]:
    """{spielername: {kriterium_name: punkte}} -- exakt die Logik aus
    `plate_points_from_arena.evaluate()`, nur nicht auf EINEN Netzname
    beschraenkt, sondern fuer BEIDE Spieler gesammelt."""
    out: dict[str, dict[str, int]] = defaultdict(dict)
    aktiv_name: str | None = None
    for roh in log or []:
        if roh.startswith("#"):
            continue
        m = ROUND_PREFIX.match(roh)
        text = m.group(2) if m else roh
        fs = PATTERNS["FINAL_SCORE"].match(text)
        if fs:
            aktiv_name = fs.group("name")
            continue
        if aktiv_name is not None:
            k = KRITERIUM.match(text)
            if k:
                out[aktiv_name][k.group("name").strip()] = int(k.group("pkt"))
            else:
                aktiv_name = None
    return out


# ── Quellen-Konfiguration ───────────────────────────────────────────────────
# side_of(names) -> {name: rolle}. "champion" umfasst JEDE Seite, die den
# v21_2d_brierbest-Champion spielt (auch unter neutralem Namen "NetzA"/
# "NetzB", wenn model==model_b -- GEPRUEFT je Datei per model/model_b-Feld).

QUELLEN = [
    {
        "kuerzel": "champion_netvnet",
        "dateien": ["paired_arena_env_imm_netvnet.json", "paired_arena_env_imm_netvnet_swap.json"],
        # beide Seiten sind der Champion (model == model_b in beiden Dateien,
        # GEPRUEFT via json.load(...)['model']/['model_b']).
        "rollen": lambda namen: {n: "champion" for n in namen},
    },
    {
        "kuerzel": "imm_a02",
        "dateien": ["paired_arena_env_imm_a02.json"],
        "arme": ["0", "0.2"],
        # Namen sind hier bereits explizit 'Netz'/'Heuristik' (GEPRUEFT).
        "rollen": lambda namen: {n: ("heuristik" if "euristik" in n else "champion") for n in namen},
    },
    {
        "kuerzel": "seedk1_nullarm",
        "dateien": ["paired_arena_env_seedk1_nullarm.json"],
        # Brett 0 = --model (seedk1), Brett 1 = --model-b (Champion) --
        # GEPRUEFT: paired_arena_arm_worker.py:74 Kommentar "Brett 0 = --model,
        # Brett 1 = --model-b" + arena.py-Docstring "Netz A (Brett 0) ...
        # Netz B (Brett 1)". model=v21-seedk1_best, model_b=v21_2d_brierbest.
        "rollen": lambda namen: {namen[0]: "seedk1", namen[1]: "champion_gegenseite"},
    },
]

K1_NAME = "Vertikale Reihen"
K1_TILE_ID = 1


def main() -> None:
    alle_seiten: list[dict] = []  # eine Zeile je (Partie, Spielername)
    korrekt_geprueft = 0
    abweichungen: list[dict] = []

    for quelle in QUELLEN:
        for dateiname in quelle["dateien"]:
            pfad = EVAL / "artifacts" / dateiname
            if not pfad.exists():
                print(f"FEHLT: {pfad}", file=sys.stderr)
                continue
            arme = quelle.get("arme", [None])
            for arm in arme:
                spiele = game_list(pfad, arm)
                for sp in spiele:
                    namen = sp["names"]
                    rollen = quelle["rollen"](namen)
                    log = sp.get("log") or []
                    cells_je_spieler = reconstruct_game(log)
                    kriterien_je_spieler = final_scoring_criteria_per_player(log)
                    k1_aktiv = K1_TILE_ID in (sp.get("scoring_tile_ids") or [])

                    for name in namen:
                        rolle = rollen.get(name)
                        if rolle is None:
                            continue
                        fill = column_fill(cells_je_spieler.get(name, set()))
                        kz = struktur_kennzahlen(fill)

                        if k1_aktiv:
                            geloggt = kriterien_je_spieler.get(name, {}).get(K1_NAME)
                            erwartet = 7 * kz["volle_spalten"]
                            if geloggt is None:
                                # Kann vorkommen, wenn die Partie durch einen
                                # Divergenzpfad frueh endet -- wird gezaehlt,
                                # nicht stillschweigend uebersprungen.
                                abweichungen.append({
                                    "quelle": quelle["kuerzel"], "datei": dateiname, "arm": arm,
                                    "game_seed": sp.get("game_seed"), "spieler": name,
                                    "problem": "keine 'Vertikale Reihen'-Zeile trotz k1 in scoring_tile_ids",
                                })
                            else:
                                korrekt_geprueft += 1
                                if geloggt != erwartet:
                                    abweichungen.append({
                                        "quelle": quelle["kuerzel"], "datei": dateiname, "arm": arm,
                                        "game_seed": sp.get("game_seed"), "spieler": name,
                                        "geloggt": geloggt, "erwartet_7x": erwartet,
                                        "volle_spalten_rekonstruiert": kz["volle_spalten"],
                                        "fill": fill,
                                    })

                        alle_seiten.append({
                            "quelle": quelle["kuerzel"], "rolle": rolle,
                            "k1_aktiv": k1_aktiv,
                            "game_seed": sp.get("game_seed"),
                            **kz,
                        })

    print(f"Korrektheitsbeweis: {korrekt_geprueft} k1-aktive Partie-Seiten geprueft, "
          f"{len(abweichungen)} Abweichungen.")
    if abweichungen:
        print("ABBRUCH-KANDIDAT -- erste 5 Abweichungen:")
        for a in abweichungen[:5]:
            print(" ", a)

    # ── Aggregation je (Quelle x Rolle x k1_aktiv) ─────────────────────────
    def describe(vals: list[float]) -> dict:
        n = len(vals)
        if n == 0:
            return {"n": 0}
        vals_sorted = sorted(vals)
        mean = sum(vals) / n
        return {
            "n": n, "mean": mean, "median": vals_sorted[n // 2],
            "min": vals_sorted[0], "max": vals_sorted[-1],
            "anteil_ge1_volle_spalte": sum(1 for v in vals if v >= 1) / n,
        }

    gruppen: dict[tuple[str, str, bool], list[dict]] = defaultdict(list)
    for s in alle_seiten:
        gruppen[(s["quelle"], s["rolle"], s["k1_aktiv"])].append(s)

    tabelle = []
    for (quelle, rolle, k1_aktiv), rows in sorted(gruppen.items()):
        volle = [r["volle_spalten"] for r in rows]
        hoehe = [r["max_hoehe"] for r in rows]
        t3 = [r["teilspalten_ge3"] for r in rows]
        t4 = [r["teilspalten_ge4"] for r in rows]
        hist = defaultdict(int)
        for v in volle:
            hist[v] += 1
        tabelle.append({
            "quelle": quelle, "rolle": rolle, "k1_aktiv": k1_aktiv,
            "n_partie_seiten": len(rows),
            "volle_spalten": describe(volle),
            "max_hoehe": describe(hoehe),
            "teilspalten_ge3": describe(t3),
            "teilspalten_ge4": describe(t4),
            "histogramm_volle_spalten": {str(k): hist[k] for k in sorted(hist)},
        })

    ergebnis = {
        "auftrag": "structural column-build verification, unabhaengig von k1-Wertungszeilen",
        "rekonstruktion": "nur Log-Textzeilen (DOME_PLACE/START_TILE/TILING_PLACE), kein Engine-Replay",
        "korrektheitsbeweis": {
            "k1_aktive_partie_seiten_geprueft": korrekt_geprueft,
            "abweichungen": abweichungen,
        },
        "tabelle": tabelle,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(ergebnis, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nGeschrieben: {OUT_JSON}")

    print(f"\n{'Quelle':<20}{'Rolle':<20}{'k1':<6}{'n':>6}{'MeanVolle':>11}{'MeanHoehe':>11}{'Mean>=3':>9}{'Mean>=4':>9}{'>=1voll':>9}")
    for row in tabelle:
        v = row["volle_spalten"]
        h = row["max_hoehe"]
        t3 = row["teilspalten_ge3"]
        t4 = row["teilspalten_ge4"]
        print(f"{row['quelle']:<20}{row['rolle']:<20}{str(row['k1_aktiv']):<6}{row['n_partie_seiten']:>6}"
              f"{v['mean']:>11.3f}{h['mean']:>11.3f}{t3['mean']:>9.3f}{t4['mean']:>9.3f}"
              f"{v['anteil_ge1_volle_spalte']:>9.3f}")


if __name__ == "__main__":
    main()
