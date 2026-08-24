#!/usr/bin/env python
"""PREREG_long_row_payoff.md par.3/B1, Messkette Schritt 2: Auswertung.

Liest die beiden gepaarten Arena-Artefakte (Arm und Brettwechsel) und liefert,
was par.3 verlangt: Siege auf BLOCK-Ebene, k1-Rate, Initiierungsrate,
**Vollendungsquote** (der registrierte Falsifikator) sowie die sechs
Standard-Kennzahlen je Seite (CLAUDE.md).

KEIN eigener Parser. Alles Vorhandene wird importiert, damit eine Aenderung am
Logtext beide Seiten gemeinsam brechen laesst statt hier still falsche Zahlen
zu erzeugen:

  plate_points_from_arena   partien, block_mittel, t_wert
  penalty_track_probe       penalties_from_log        (Kennzahl 3)
  column_build_struct...    rekonstruiere_partie, spalten_fuellung,
                            struktur_kennzahlen, endwertung_kriterien_je_spieler
                            (Kennzahl 2 und 4)
  row_preference_probe      row_choices_from_log      (Kennzahl 1)

NEU und nur hier: die drei Zaehler `long_rows_started` / `long_rows_completed`
/ `long_rows_cleared_unplaceable`, die seit dem erweiterten Arena-Mitschrieb im
Ergebnis-JSON stehen. Aus ihnen folgt die Vollendungsquote, die sich aus
Partie-Logs prinzipiell NICHT gewinnen laesst (round_end.rs leert
unplatzierbare Reihen ohne Logzeile -- daran ist par.2a Stufe 2 gescheitert).

## Zuordnung Knopf -> Brett

`tools/run_lr_init_arena.sh` faehrt zwei Laeufe:

  Datei 1 (`...lrinit_netvnet.json`)       spec-a = AN  auf Brett 0
  Datei 2 (`...lrinit_netvnet_swap.json`)  spec-a = AUS auf Brett 0

Der Brettwechsel ist Pflichtteil (PREREG_agent_encapsulation.md par.6a). Beide
Spieler heissen netz-gegen-netz "NetzA"/"NetzB", die Namensregel taugt hier
also nicht -- ausgewaehlt wird ueber den BRETT-INDEX.

## Statistik

Die Paarung sitzt INNERHALB der Partie: AN und AUS spielen dieselbe Partie
gegeneinander, die Differenz je Partie ist damit exakt gepaart, ohne Seed- oder
Aera-Versatz. Der t-Wert gehoert danach auf die BLOECKE, nicht auf die
Partien -- Paar-SEs sind im Projekt schon einmal massiv unterschaetzt worden
(stehende Regel seit 2026-08-04). `block_mittel` wird dafuer importiert.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "probes"))

from plate_points_from_arena import partien, block_mittel, t_wert  # noqa: E402
from penalty_track_probe import penalties_from_log  # noqa: E402
from row_preference_probe import row_choices_from_log  # noqa: E402
from column_build_structural_probe import (  # noqa: E402
    rekonstruiere_partie,
    spalten_fuellung,
    struktur_kennzahlen,
    endwertung_kriterien_je_spieler,
)

EVAL = ROOT / "evaluations"
OUT_JSON = EVAL / "long_row_init_arena_eval.json"
BLOCK = 25  # `paired_arena_env_ab.py --block-size` Default, so gefahren

K1_TILE_ID = 1
K1_NAME = "Vertikale Reihen"

# Datei -> Brett-Index, auf dem der Knopf AN ist.
QUELLEN = [
    ("paired_arena_env_lrinit_netvnet.json", 0),
    ("paired_arena_env_lrinit_netvnet_swap.json", 1),
]

# Zaehlerfelder aus dem erweiterten Mitschrieb.
LR_FELDER = ("long_rows_started", "long_rows_completed",
             "long_rows_cleared_unplaceable")


def seite_kennzahlen(sp: dict, i: int) -> dict:
    """Alle Kennzahlen EINER Partie-Seite (Brett `i`)."""
    namen = sp["names"]
    name = namen[i]
    log = sp.get("log") or []

    # Kennzahl 5/6: eigene Punkte und Marge. Sieg dazu.
    punkte = sp["scores"][i]
    marge = punkte - sp["scores"][1 - i]

    # Kennzahl 3: Strafleiste.
    straf = penalties_from_log(log).get(name, {})

    # Kennzahl 1: Reihenauslastung (Zugziele je Musterreihe 1..6).
    hist = Counter()
    for (_rnd, nm, reihe) in row_choices_from_log(log):
        if nm == name:
            hist[reihe] += 1
    n_reihenzuege = sum(hist.values())

    # Kennzahl 2: Spaltenauslastung aus dem rekonstruierten Kuppel-Endstand.
    zellen = rekonstruiere_partie(log).get(name, set())
    spalten = struktur_kennzahlen(spalten_fuellung(zellen))

    # Kennzahl 4: Punkte je Wertungsplatte.
    kriterien = endwertung_kriterien_je_spieler(log).get(name, {})

    # k1: nur dort auswertbar, wo die Platte ueberhaupt aktiv war.
    k1_aktiv = K1_TILE_ID in (sp.get("scoring_tile_ids") or [])
    k1_punkte = kriterien.get(K1_NAME)

    out = dict(
        punkte=punkte,
        marge=marge,
        sieg=1 if sp["winner"] == i else 0,
        # Strafleiste
        strafpunkte=straf.get("strafpunkte", 0),
        straf_ziele=straf.get("straf_ziele", 0),
        straf_ziel_steine=straf.get("straf_ziel_steine", 0),
        ueberlauf_steine=straf.get("ueberlauf_steine", 0),
        strafrunden=straf.get("strafrunden", 0),
        draft_zuege=straf.get("draft_zuege", 0),
        # Reihen
        n_reihenzuege=n_reihenzuege,
        reihen_kurz_1_3=sum(hist[r] for r in (1, 2, 3)),
        reihen_lang_4_6=sum(hist[r] for r in (4, 5, 6)),
        reihen_hist={str(r): hist[r] for r in range(1, 7)},
        # Spalten
        volle_spalten=spalten["volle_spalten"],
        max_spaltenhoehe=spalten["max_hoehe"],
        teilspalten_ge3=spalten["teilspalten_ge3"],
        teilspalten_ge4=spalten["teilspalten_ge4"],
        # Platten
        plattenpunkte_je_kriterium=kriterien,
        k1_aktiv=k1_aktiv,
        k1_punkte=k1_punkte,
        k1_getroffen=(1 if (k1_punkte or 0) > 0 else 0) if k1_aktiv else None,
    )
    for f in LR_FELDER:
        v = sp.get(f)
        if v is None:
            raise SystemExit(
                f"'{f}' fehlt in der Partie (seed {sp.get('game_seed')}). "
                "Das Artefakt stammt aus einem Wheel VOR der Mitschrieb-"
                "Erweiterung -- Lauf mit dem aktuellen Wheel wiederholen."
            )
        out[f] = v[i]
    return out


SKALARE = [
    "punkte", "marge", "sieg",
    "strafpunkte", "straf_ziele", "straf_ziel_steine", "ueberlauf_steine",
    "strafrunden", "draft_zuege",
    "n_reihenzuege", "reihen_kurz_1_3", "reihen_lang_4_6",
    "volle_spalten", "max_spaltenhoehe", "teilspalten_ge3", "teilspalten_ge4",
    "long_rows_started", "long_rows_completed", "long_rows_cleared_unplaceable",
]


def mittel(werte):
    return round(sum(werte) / len(werte), 4) if werte else None


def gepaart(diffs_je_datei: list[list[float]]) -> dict | None:
    """Block-Ebene: erst Blockmittel JE DATEI in Laufreihenfolge, dann t.

    Je Datei, nicht ueber beide zusammen: 407 Partien sind 16 volle Bloecke
    plus 7 Rest. Wuerde man beide Dateien hintereinanderhaengen, verschmoelze
    dieser Rest mit dem Anfang der zweiten Datei zu einem Block, der in
    Wahrheit nie eine Laufeinheit war -- und genau die Laufeinheit ist der
    Grund fuer die Block-Ebene."""
    bl: list[float] = []
    n_partien = 0
    for d in diffs_je_datei:
        n_partien += len(d)
        if len(d) >= 2:
            bl.extend(block_mittel(d, BLOCK))
    if len(bl) < 2:
        return None
    m, t = t_wert(bl)
    flach = [x for d in diffs_je_datei for x in d]
    return dict(n_partien=n_partien, n_bloecke=len(bl),
                mittel=round(m, 4), t=round(t, 2),
                mittel_je_partie=round(sum(flach) / len(flach), 4) if flach else None)


def main() -> None:
    an: list[dict] = []
    aus: list[dict] = []
    # je Kennzahl eine Liste JE DATEI (Blockgrenzen sind dateiweise, s.
    # `gepaart`), plus dieselbe Struktur fuer die Vollendungsquote.
    diffs: dict[str, list[list[float]]] = defaultdict(list)
    quoten_diff: list[list[float]] = []
    kriterien_summe: dict[str, dict[str, list[int]]] = {
        "an": defaultdict(list), "aus": defaultdict(list)}
    fehlende = []

    for dateiname, an_brett in QUELLEN:
        pfad = EVAL / dateiname
        if not pfad.exists():
            fehlende.append(dateiname)
            continue
        datei_diffs: dict[str, list[float]] = defaultdict(list)
        datei_quoten: list[float] = []
        # Der Lauf faehrt `--arms 0` (String, kein type= im Parser), der
        # Arm-Schluessel heisst also "0". Ein-Arm-Dateien lassen sich auch
        # ohne Schluessel lesen -- der Fallback deckt eine spaetere
        # Umbenennung ab, ohne bei Mehr-Arm-Dateien still das Falsche zu tun.
        try:
            spiele = partien(pfad, "0")
        except SystemExit:
            spiele = partien(pfad, None)
        for sp in spiele:
            a = seite_kennzahlen(sp, an_brett)
            b = seite_kennzahlen(sp, 1 - an_brett)
            an.append(a)
            aus.append(b)
            for k in SKALARE:
                datei_diffs[k].append(a[k] - b[k])
            # Quote nur, wo BEIDE Seiten ueberhaupt gestartet haben -- eine
            # Quote ohne Nenner ist kein Datenpunkt.
            if a["long_rows_started"] > 0 and b["long_rows_started"] > 0:
                datei_quoten.append(
                    a["long_rows_completed"] / a["long_rows_started"]
                    - b["long_rows_completed"] / b["long_rows_started"])
            for label, s in (("an", a), ("aus", b)):
                for krit, pkt in s["plattenpunkte_je_kriterium"].items():
                    kriterien_summe[label][krit].append(pkt)
        for k in SKALARE:
            diffs[k].append(datei_diffs[k])
        quoten_diff.append(datei_quoten)

    if fehlende:
        raise SystemExit("Artefakt(e) fehlen: " + ", ".join(fehlende))
    if not an:
        raise SystemExit("keine Partien gelesen")

    def quote(seiten):
        s = sum(x["long_rows_started"] for x in seiten)
        c = sum(x["long_rows_completed"] for x in seiten)
        r = sum(x["long_rows_cleared_unplaceable"] for x in seiten)
        return dict(
            starts_gesamt=s, vollendet_gesamt=c, geraeumt_gesamt=r,
            starts_je_partie=mittel([x["long_rows_started"] for x in seiten]),
            vollendungsquote=round(c / s, 4) if s else None,
            raeumquote=round(r / s, 4) if s else None,
            offen_am_ende=s - c - r,
        )

    def k1_rate(seiten):
        akt = [x for x in seiten if x["k1_aktiv"]]
        tr = sum(x["k1_getroffen"] for x in akt)
        return dict(n_k1_aktiv=len(akt), getroffen=tr,
                    rate=round(tr / len(akt), 4) if akt else None,
                    punkte_je_aktiver_partie=mittel(
                        [x["k1_punkte"] or 0 for x in akt]))

    ergebnis = dict(
        quellen=[d for d, _ in QUELLEN],
        n_partien_gesamt=len(an),
        block_size=BLOCK,
        hinweis_normierung=(
            "starts_je_partie ist NICHT dieselbe Groesse wie die 11,5/25,2 "
            "Prozent aus par.2a Stufe 3 (dort: Anteil der GELEGENHEITEN, bei "
            "denen initiiert wurde). Nicht verrechnen."
        ),
        siegquote_an=mittel([x["sieg"] for x in an]),
        lange_reihen=dict(an=quote(an), aus=quote(aus),
                          vollendungsquote_gepaart=gepaart(quoten_diff)),
        k1=dict(an=k1_rate(an), aus=k1_rate(aus)),
        mittel_an={k: mittel([x[k] for x in an]) for k in SKALARE},
        mittel_aus={k: mittel([x[k] for x in aus]) for k in SKALARE},
        gepaart_an_minus_aus={k: gepaart(diffs[k]) for k in SKALARE},
        reihen_hist_an={str(r): sum(x["reihen_hist"][str(r)] for x in an)
                        for r in range(1, 7)},
        reihen_hist_aus={str(r): sum(x["reihen_hist"][str(r)] for x in aus)
                         for r in range(1, 7)},
        plattenpunkte_je_kriterium=dict(
            an={k: mittel(v) for k, v in sorted(kriterien_summe["an"].items())},
            aus={k: mittel(v) for k, v in sorted(kriterien_summe["aus"].items())},
        ),
    )

    OUT_JSON.write_text(json.dumps(ergebnis, indent=2, ensure_ascii=False),
                        encoding="utf-8")

    lr = ergebnis["lange_reihen"]
    print(f"n = {len(an)} Partien (beide Dateien, Brettwechsel gepoolt)")
    print(f"Siegquote AN: {ergebnis['siegquote_an']}  "
          f"(gepaart: {ergebnis['gepaart_an_minus_aus']['sieg']})")
    print("\n-- Falsifikator --")
    print(f"  Starts/Partie   AN {lr['an']['starts_je_partie']}  "
          f"AUS {lr['aus']['starts_je_partie']}  "
          f"(gepaart {ergebnis['gepaart_an_minus_aus']['long_rows_started']})")
    print(f"  Vollendungsquote AN {lr['an']['vollendungsquote']}  "
          f"AUS {lr['aus']['vollendungsquote']}  "
          f"(gepaart {lr['vollendungsquote_gepaart']})")
    print(f"  Raeumquote       AN {lr['an']['raeumquote']}  "
          f"AUS {lr['aus']['raeumquote']}")
    print("\n-- k1 --")
    print(f"  AN  {ergebnis['k1']['an']}")
    print(f"  AUS {ergebnis['k1']['aus']}")
    print("\n-- Standard-Kennzahlen, gepaart AN minus AUS (Block-Ebene) --")
    for k in SKALARE:
        g = ergebnis["gepaart_an_minus_aus"][k]
        if g:
            print(f"  {k:32s} {g['mittel']:+8.4f}  t={g['t']:+6.2f}  "
                  f"({g['n_bloecke']} Bloecke)")
    print(f"\n-> {OUT_JSON}")


if __name__ == "__main__":
    main()
