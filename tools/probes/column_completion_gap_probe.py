# -*- coding: utf-8 -*-
"""Vollendungs-Luecken-Sonde (Auftrag 2026-08-23, Erweiterung von
`column_build_structural_probe.py`): der Champion baut Spalten bis auf
Hoehe ~4,66, vollendet aber nur 0,096/0,100 volle Spalten je Partie
(STATUS.md, Stand 2026-08-23). Diese Sonde misst WIE KNAPP und WANN --
je Partie-Seite:

  1. End-Zustand: wie viele Spalten stehen bei Spielende exakt auf Hoehe 5
     ("um eine Zelle verpasst") bzw. Hoehe 4.
  2. Zeitpunkt: fuer jede Spalte, die im Partieverlauf Hoehe 5 erreicht --
     in welcher RUNDE, und wie viele EIGENE Tiling-Aktionen danach noch
     kamen (Vollendungs-Gelegenheitsfenster).
  3. Ausgang je Hoehe-5-Spalte: wurde sie am Ende vollendet (Hoehe 6)?

LASTSPERRE (Koordinator-Auftrag, unveraendert gegenueber der Basissonde):
auf der Maschine laufen parallel lastempfindliche Byte-Identitaets-Beweise
eines anderen Agenten. Dieses Werkzeug liest NUR Dateien und rechnet
single-thread in Python -- KEIN mosaic_rust-Import, KEIN Engine-Replay,
kein Build.

WICHTIGE GRENZE (muss bei jeder Verwendung der Ergebnisse mitgedacht
werden): diese Sonde hat KEINEN Engine-Zugriff und kann daher NICHT
pruefen, ob eine Vollendung im Einzelfall LEGAL moeglich gewesen waere
(Kachel-/Farbverfuegbarkeit auf den Fabriken, Musterreihen-Kapazitaet,
Zugreihenfolge mit dem Gegner). Gemessen wird ein reines GELEGENHEITS-
FENSTER (Zahl eigener Tiling-Aktionen nach dem Erreichen von Hoehe 5),
NICHT Legalitaet. Eine Legalitaets-Stufe mit Engine-Gegenpruefung folgt
separat.

Rekonstruktionsweg: identisch zu `column_build_structural_probe.py`, dort
gegen 1.560 Wertungszeilen mit 0 Abweichungen bewiesen (Artefakt
evaluations/column_build_structural_probe.json). Die Slot->Kachel/
Rotation-Buchhaltung, der Special-Katalog und das Spalten-Mapping
(2*tc + si%2) werden HIER NICHT neu geschrieben, sondern aus dem Modul
importiert -- diese Sonde fuegt nur die ZEITLICHE Verfolgung (Reihenfolge
je Aktion statt nur die finale Zellmenge) hinzu.

Interne Konsistenzpruefung (an jeder Partie-Seite): der finale Fuellstand,
den diese Sonde aus der ZEITLICHEN Aktionsfolge aufsummiert, muss exakt
dem finalen Fuellstand entsprechen, den `column_build_structural_probe`
aus der (ungeordneten) Endzellmenge berechnet. Jede Abweichung ist ein
Rekonstruktionsfehler -> Abbruch mit Beispiel (dieselbe Disziplin wie der
k1=7x-Beweis der Basissonde).

Aufruf:
    python -X utf8 tools/probes/column_completion_gap_probe.py
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "probes"))

from analyze_game_log import PATTERNS, ROUND_PREFIX  # noqa: E402
from plate_points_from_arena import partien  # noqa: E402
from column_build_structural_probe import (  # noqa: E402
    rotated_special_local_index,
    rekonstruiere_partie,
    spalten_fuellung,
    QUELLEN,
    K1_TILE_ID,
)

EVAL = ROOT / "evaluations"
OUT_JSON = EVAL / "column_completion_gap_probe.json"


# ── Log -> GEORDNETE Aktionsfolge je Spieler ────────────────────────────────

def rekonstruiere_partie_sequenz(log: list[str]) -> dict[str, list[dict]]:
    """Wie `column_build_structural_probe.rekonstruiere_partie`, aber statt
    nur der finalen Zellmenge wird je Spieler die GEORDNETE Folge der
    Tiling-Aktionen zurueckgegeben: `[{"runde": int|None, "zellen": [(r,c,si),...]}, ...]`.
    Jede Aktion traegt 1 Zelle (reine Farb-/Jokerplatzierung) oder 2 Zellen
    (Farb-/Jokerzelle + mitgefuellte Spezialzelle im selben Slot, siehe
    Modul-Doc der Basissonde) -- dieselbe DOME_PLACE/START_TILE ->
    TILING_PLACE-Buchhaltung, nur mit Reihenfolge statt Set-Vereinigung."""
    slot_tile: dict[str, dict[tuple[int, int], tuple[int, int]]] = defaultdict(dict)
    sequenz: dict[str, list[dict]] = defaultdict(list)
    for roh in log or []:
        if roh.startswith("#"):
            continue
        m = ROUND_PREFIX.match(roh)
        runde = int(m.group(1)) if m else None
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
            neue_zellen = [(r, c, si)]
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
                neue_zellen.append((r, c, sp_si))
            sequenz[name].append({"runde": runde, "zellen": neue_zellen})
            continue
    return sequenz


def fuellstand_aus_sequenz(sequenz: list[dict]) -> list[int]:
    fill = [0] * 6
    for akt in sequenz:
        for (_r, c, si) in akt["zellen"]:
            fill[2 * c + (si % 2)] += 1
    return fill


def hoehe5_ereignisse(sequenz: list[dict]) -> list[dict]:
    """Je Spalte, die im Partieverlauf Hoehe 5 (oder in einem Schritt gleich
    Hoehe 6, siehe Randfall unten) erreicht: Runde des Erreichens,
    Gelegenheitsfenster (Zahl EIGENER Tiling-Aktionen danach) und Ausgang.

    Da Zellen nur HINZUGEFUEGT werden (kein Rueckbau), ist die Fuellhoehe
    je Spalte monoton steigend -- jede Spalte durchlaeuft Hoehe 5 hoechstens
    einmal, direkt bevor sie (falls ueberhaupt) auf 6 vollendet wird.

    RANDFALL (dokumentiert, kein Fehler): eine einzelne Tiling-Aktion kann
    ZWEI Zellen gleichzeitig legen (Farbzelle + mitgefuellte Spezialzelle).
    Landen beide in DERSELBEN Spalte, springt deren Fuellstand in EINER
    Aktion von <5 auf 6 -- Erreichen und Vollendung fallen dann zusammen,
    das Gelegenheitsfenster ist per Definition 0."""
    fill = [0] * 6
    n_aktionen = len(sequenz)
    ereignis_je_spalte: dict[int, dict] = {}
    for idx, akt in enumerate(sequenz):
        vor = list(fill)
        for (_r, c, si) in akt["zellen"]:
            fill[2 * c + (si % 2)] += 1
        for col in range(6):
            if vor[col] < 5 <= fill[col] and col not in ereignis_je_spalte:
                ereignis_je_spalte[col] = {
                    "spalte": col,
                    "runde": akt["runde"],
                    "aktionsindex": idx,
                    "sofort_vollendet": fill[col] >= 6,
                }
    ergebnisse = []
    for col, ev in ereignis_je_spalte.items():
        if ev["sofort_vollendet"]:
            fenster = 0
        else:
            fenster = n_aktionen - (ev["aktionsindex"] + 1)
        ergebnisse.append({
            "spalte": col,
            "runde": ev["runde"],
            "gelegenheitsfenster_eigene_zuege": fenster,
            # finaler Fuellstand nach ALLEN Aktionen (Schleife oben ist
            # bereits durchgelaufen, `fill` traegt den Endstand):
            "vollendet": fill[col] >= 6,
        })
    return ergebnisse


# ── Aggregation ──────────────────────────────────────────────────────────────

def describe(vals: list[float]) -> dict:
    n = len(vals)
    if n == 0:
        return {"n": 0}
    vals_sorted = sorted(vals)
    return {
        "n": n, "mean": sum(vals) / n, "median": vals_sorted[n // 2],
        "min": vals_sorted[0], "max": vals_sorted[-1],
    }


def main() -> None:
    alle_seiten: list[dict] = []
    konsistenz_abweichungen: list[dict] = []
    n_konsistent = 0

    for quelle in QUELLEN:
        for dateiname in quelle["dateien"]:
            pfad = EVAL / dateiname
            if not pfad.exists():
                print(f"FEHLT: {pfad}", file=sys.stderr)
                continue
            arme = quelle.get("arme", [None])
            for arm in arme:
                spiele = partien(pfad, arm)
                for sp in spiele:
                    namen = sp["names"]
                    rollen = quelle["rollen"](namen)
                    log = sp.get("log") or []
                    sequenz_je_spieler = rekonstruiere_partie_sequenz(log)
                    # Konsistenzpruefung gegen die (unabhaengig geordnete)
                    # Basissonden-Rekonstruktion -- siehe Modul-Doc.
                    cells_je_spieler = rekonstruiere_partie(log)
                    k1_aktiv = K1_TILE_ID in (sp.get("scoring_tile_ids") or [])

                    for name in namen:
                        rolle = rollen.get(name)
                        if rolle is None:
                            continue
                        sequenz = sequenz_je_spieler.get(name, [])
                        fill_final = fuellstand_aus_sequenz(sequenz)

                        fill_via_basissonde = spalten_fuellung(cells_je_spieler.get(name, set()))
                        n_konsistent += 1
                        if fill_final != fill_via_basissonde:
                            konsistenz_abweichungen.append({
                                "quelle": quelle["kuerzel"], "datei": dateiname, "arm": arm,
                                "game_seed": sp.get("game_seed"), "spieler": name,
                                "fill_sequenz": fill_final, "fill_basissonde": fill_via_basissonde,
                            })

                        ereignisse = hoehe5_ereignisse(sequenz)

                        alle_seiten.append({
                            "quelle": quelle["kuerzel"], "rolle": rolle,
                            "k1_aktiv": k1_aktiv, "game_seed": sp.get("game_seed"),
                            "n_hoehe5_ende": sum(1 for f in fill_final if f == 5),
                            "n_hoehe4_ende": sum(1 for f in fill_final if f == 4),
                            "fill_final": fill_final,
                            "hoehe5_ereignisse": ereignisse,
                        })

    print(f"Konsistenzpruefung (Sequenz- vs. Basissonden-Fuellstand): "
          f"{n_konsistent} Partie-Seiten geprueft, {len(konsistenz_abweichungen)} Abweichungen.")
    if konsistenz_abweichungen:
        print("ABBRUCH-KANDIDAT -- erste 5 Abweichungen:")
        for a in konsistenz_abweichungen[:5]:
            print(" ", a)

    # ── Gruppierung (Quelle x Rolle x k1_aktiv) ────────────────────────────
    gruppen: dict[tuple[str, str, bool], list[dict]] = defaultdict(list)
    for s in alle_seiten:
        gruppen[(s["quelle"], s["rolle"], s["k1_aktiv"])].append(s)

    tabelle = []
    for (quelle, rolle, k1_aktiv), rows in sorted(gruppen.items()):
        n_h5 = [r["n_hoehe5_ende"] for r in rows]
        n_h4 = [r["n_hoehe4_ende"] for r in rows]
        alle_ereignisse = [e for r in rows for e in r["hoehe5_ereignisse"]]
        n_vollendet = sum(1 for e in alle_ereignisse if e["vollendet"])
        n_ereignisse = len(alle_ereignisse)
        fenster_nicht_vollendet = [e["gelegenheitsfenster_eigene_zuege"] for e in alle_ereignisse if not e["vollendet"]]
        fenster_alle = [e["gelegenheitsfenster_eigene_zuege"] for e in alle_ereignisse]
        runden_hist: dict[int, int] = defaultdict(int)
        for e in alle_ereignisse:
            if e["runde"] is not None:
                runden_hist[e["runde"]] += 1

        tabelle.append({
            "quelle": quelle, "rolle": rolle, "k1_aktiv": k1_aktiv,
            "n_partie_seiten": len(rows),
            "hoehe5_spalten_am_ende": describe(n_h5),
            "hoehe4_spalten_am_ende": describe(n_h4),
            "n_hoehe5_ereignisse_gesamt": n_ereignisse,
            "vollendungsquote_erreichter_hoehe5": (n_vollendet / n_ereignisse) if n_ereignisse else None,
            "gelegenheitsfenster_alle": describe(fenster_alle),
            "gelegenheitsfenster_bei_nichtvollendung": describe(fenster_nicht_vollendet),
            "runden_verteilung_erreichen": {str(k): runden_hist[k] for k in sorted(runden_hist)},
        })

    ergebnis = {
        "auftrag": "Vollendungs-Luecken-Sonde: Zeitpunkt und Knappheit des Hoehe-5->6-Uebergangs je Spalte",
        "grenze_legalitaet": (
            "Kein Engine-Zugriff -- das Gelegenheitsfenster zaehlt EIGENE Tiling-Aktionen "
            "nach dem Erreichen von Hoehe 5, prueft aber NICHT, ob eine Vollendung in diesem "
            "Fenster LEGAL moeglich gewesen waere (Kachel-/Farbverfuegbarkeit, Musterreihen-"
            "Kapazitaet). Legalitaets-Stufe mit Engine-Gegenpruefung folgt separat."
        ),
        "konsistenzpruefung": {
            "partie_seiten_geprueft": n_konsistent,
            "abweichungen": konsistenz_abweichungen,
        },
        "tabelle": tabelle,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(ergebnis, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nGeschrieben: {OUT_JSON}")

    print(f"\n{'Quelle':<20}{'Rolle':<20}{'k1':<6}{'n':>5}{'MeanH5end':>11}{'MeanH4end':>11}"
          f"{'#Ereig':>8}{'Vollq':>8}{'MeanFenst':>11}")
    for row in tabelle:
        h5 = row["hoehe5_spalten_am_ende"]
        h4 = row["hoehe4_spalten_am_ende"]
        vq = row["vollendungsquote_erreichter_hoehe5"]
        fw = row["gelegenheitsfenster_alle"]
        vq_s = f"{vq:.3f}" if vq is not None else "n/a"
        fw_mean = f"{fw['mean']:.2f}" if fw.get("n", 0) else "n/a"
        print(f"{row['quelle']:<20}{row['rolle']:<20}{str(row['k1_aktiv']):<6}{row['n_partie_seiten']:>5}"
              f"{h5['mean']:>11.3f}{h4['mean']:>11.3f}{row['n_hoehe5_ereignisse_gesamt']:>8}"
              f"{vq_s:>8}{fw_mean:>11}")


if __name__ == "__main__":
    main()
