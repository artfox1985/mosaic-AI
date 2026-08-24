#!/usr/bin/env python
"""Analytische Versorgungs-Schranke je Musterreihe -- Sanity-Check.

ANLASS (Nutzer-Auftrag 2026-08-24, "mach trotzdem die analytische probe.
sanity check"): das gemessene Mensch-Profil
(`tools/probes/human_row_profile_probe.py`) ist die erste unkontaminierte
empirische Referenz, aber n=10 und ein Spieler. Diese Sonde prueft es gegen
eine Rechnung, die gar keine Partien braucht -- stimmen beide ueberein, ist
das Profil belastbar; klaffen sie, ist eines von beiden falsch.

**Startet nichts.** Reine Kombinatorik plus eine kleine Monte-Carlo-Ziehung
fuer die Verteilung der Zugausbeute. Keine Engine, kein Netz, keine Arena.

## Modell (alle Konstanten aus docs/engine_manual.md, dort geprueft)

* 65 Normalfliesen in 5 Farben (Z.26) -> 13 je Farbe.
* 4 kleine Fabriken mit je 4 Sonnenseiten-Fliesen (Z.35), jede Runde neu
  befuellt (Z.56); 1 grosse mit 5, monochrom wird neu gezogen (Z.59), die
  maximale Einfarb-Ausbeute EINER Sonnenseite ist damit 4.
* 5 Runden -> **21 Fliesen je Runde, 105 Fliesen-Platzierungen je Partie**,
  die sich BEIDE Spieler teilen. Der Beutel wird ueber den Turm nachgefuellt,
  die 65 sind also kein Deckel fuer die Partie, nur fuer den Umlauf.
* Zug B nimmt ALLE Fliesen EINER Farbe von EINER Sonnenseite (Z.93).
* **Zweiter Kanal: Bonuschips.** 20 Stueck, 4 je Runde (Z.49-50), also ~10 je
  Spieler. Je fehlender Zelle 2 passende oder 3 beliebige Chips (Z.150-154)
  -> bis zu 5 zusaetzliche Zellen je Spieler und Partie.
* **Dritter Kanal: Spezialfliesen (Nutzer-Hinweis 2026-08-24, im ersten
  Modell schlicht vergessen).** 9 Stueck in einer SEPARATEN Reserve, zusaetzlich
  zu den 65 Normalfliesen (Z.28). Sie werden automatisch gesetzt, sobald die
  drei anderen regulaeren Zellen ihrer Kuppelplatte voll sind (Z.168-174), und
  kosten dabei keine eigene gedraftete Fliese. Sie zaehlen als gewoehnliche
  belegte Zelle fuer die Linien der Nachbarn (Z.176), **also auch fuer
  Spalten**, und zahlen Punkte in Hoehe der Rasterreihe 1..6 (Z.175).

  **"Gratis" waere falsch (Nutzer-Korrektur im selben Zug).** Die drei anderen
  Zellen muessen erst gefuellt werden, und jede davon kostet einen
  Musterreihen-Abschluss. Der richtige Ausdruck ist: **die vierte Zelle einer
  Platte zum Preis von dreien**, also 25 Prozent Rabatt auf genau diese Platte.
  Der Rabatt haengt an einer LOKALEN Figur (ein 2x2-Slot, Rasterreihen 2*tr und
  2*tr+1, Rasterspalten 2*tc und 2*tc+1) und nicht an einer globalen wie einer
  Spalte -- das ist der entscheidende Unterschied im Schwierigkeitsgrad.

## Die zwei bindenden Schranken

1. **Rundenschranke:** eine Musterreihe kann hoechstens EINMAL je Runde
   abschliessen (die Kachelphase laeuft einmal je Runde) -> max 5
   **erspielte** Zellen je Rasterreihe. **Sie ist KEINE Obergrenze fuer die
   belegten Zellen**: Spezialfliesen kommen dazu, ohne selbst einen
   Musterreihen-Abschluss zu kosten. Gemessen sind in
   Rasterreihe 1 und 2 tatsaechlich 5,05 und 5,06 belegte Zellen -- genau
   diese Diskrepanz hat den fehlenden dritten Kanal aufgedeckt.
2. **Versorgungsschranke:** `Summe ueber r von (Abschluesse_r * Kapazitaet_r)`
   ist die Zahl der verbrauchten Zellen und durch das Fliesen-Budget
   begrenzt. Fuer LANGE Reihen bindet diese.

Der Wechsel zwischen beiden erzeugt die Form des Profils. Genau das ist die
Frage: faellt es linear ab (Nutzer-Vermutung) oder bricht es ein?

## Was diese Sonde NICHT leistet

Sie rechnet eine SCHRANKE, kein Optimum. Wie ein guter Spieler sein Budget
ueber die Reihen verteilt, ist eine Optimierung unter Konkurrenz um dieselben
Fliesen und steckt hier nicht drin. Wer die Zahlen als Zielprofil liest,
macht denselben Fehler wie beim Self-Play-Profil, nur in die andere Richtung.
"""
from __future__ import annotations

import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "evaluations" / "row_supply_ceiling.json"
MESSUNG = ROOT / "evaluations" / "human_row_profile.json"

FARBEN = 5
FLIESEN_JE_FARBE = 13
KLEINE_FABRIKEN = 4
KLEIN_FLIESEN = 4
GROSS_FLIESEN = 5
RUNDEN = 5
KAPAZITAET = [1, 2, 3, 4, 5, 6]
CHIPS_GESAMT = 20
CHIPS_JE_ZELLE_PASSEND = 2
SPEZIALFLIESEN = 9          # separate Reserve, Z.28
SPEZIALFELDER_JE_PARTIE = 9  # ebensoviele Felder im Spiel, Z.173
DOME_SLOTS = 9               # 3x3-Raster, also hoechstens 9 Platten je Spieler
STRAFE_JE_LEEREM_SPEZIALFELD = 3  # Wertungskriterium 7, Z.196

FLIESEN_JE_RUNDE = KLEINE_FABRIKEN * KLEIN_FLIESEN + GROSS_FLIESEN
FLIESEN_JE_PARTIE = FLIESEN_JE_RUNDE * RUNDEN

N_MC = 200_000
RNG = random.Random(20260824)


def move_yield_distribution() -> dict:
    """Verteilung der BESTEN Einfarb-Ausbeute EINER Sonnenseite.

    Modelliert eine kleine Fabrik: 4 Fliesen, Farben gleichverteilt (der
    Beutel ist mit 13 je Farbe gross genug, dass Ziehen ohne Zuruecklegen
    kaum abweicht). `beste` = groesste Farbanzahl auf dieser Fabrik, also
    die Ausbeute, die ein Zug dort maximal bringt."""
    beste = Counter()
    genau = Counter()
    for _ in range(N_MC):
        c = Counter(RNG.randrange(FARBEN) for _ in range(KLEIN_FLIESEN))
        beste[max(c.values())] += 1
        # Ausbeute einer VORHER festgelegten Farbe (wer eine Reihe fuellt,
        # ist an deren Farbe gebunden, sobald die erste Fliese liegt).
        genau[c.get(0, 0)] += 1
    return dict(
        beste_ausbeute={str(k): round(v / N_MC, 4) for k, v in sorted(beste.items())},
        beste_ausbeute_mittel=round(sum(k * v for k, v in beste.items()) / N_MC, 3),
        festgelegte_farbe={str(k): round(v / N_MC, 4) for k, v in sorted(genau.items())},
        festgelegte_farbe_mittel=round(sum(k * v for k, v in genau.items()) / N_MC, 3),
    )


SPALTEN_KOSTEN = sum(KAPAZITAET)  # 21 Zellen je zusaetzlicher voller Spalte


def schranken(budget_zellen: float) -> dict:
    """Abschluss-Obergrenze je Reihe, wenn das GANZE Budget in diese eine
    Reihe ginge. Das ist bewusst grosszuegig: real konkurrieren die Reihen
    um dasselbe Budget."""
    return {str(r + 1): round(min(RUNDEN, budget_zellen / KAPAZITAET[r]), 2)
            for r in range(6)}


def columns_under_uniform_distribution(budget_zellen: float) -> float:
    """Wieviele volle Spalten ein Budget TRAEGT, wenn es gleichmaessig auf
    alle sechs Reihen verteilt wird.

    Eine volle Spalte braucht EINE Zelle in JEDER Rasterreihe, also je einen
    Abschluss jeder Musterreihe. k Spalten kosten damit
    k * (1+2+3+4+5+6) = 21k Zellen -- unabhaengig davon, wie geschickt
    platziert wird. Das ist die eigentliche Strukturaussage dieser Sonde:
    **die Spaltenzahl haengt nicht am Fliesen-Zufluss, sondern an der
    VERTEILUNG ueber die Reihen.** Ein Profil, das kurze Reihen haeuft,
    verbraucht dasselbe Budget und traegt weniger Spalten."""
    return min(RUNDEN, budget_zellen / SPALTEN_KOSTEN)


def main() -> None:
    verteilung = move_yield_distribution()

    # Fliesen-Budget je Spieler, wenn beide gleich viel abbekommen.
    budget_gleichverteilt = FLIESEN_JE_PARTIE / 2
    chip_zellen_je_spieler = (CHIPS_GESAMT / 2) / CHIPS_JE_ZELLE_PASSEND

    ergebnis = dict(
        modell=dict(
            fliesen_je_runde=FLIESEN_JE_RUNDE,
            fliesen_je_partie=FLIESEN_JE_PARTIE,
            budget_je_spieler_bei_gleichverteilung=budget_gleichverteilt,
            chip_zellen_je_spieler=chip_zellen_je_spieler,
            max_einfarb_ausbeute_eines_zuges=KLEIN_FLIESEN,
            rundenschranke_erspielte_zellen_je_reihe=RUNDEN,
            spezialfliesen_reserve=SPEZIALFLIESEN,
            hinweis_spezialfliesen=(
                "kosten keine EIGENE gedraftete Fliese, setzen aber die drei "
                "anderen Zellen ihrer Platte voraus (vierte Zelle zum Preis von "
                "dreien). Zaehlen "
                "aber fuer Spalten mit. Deshalb koennen belegte Zellen je "
                "Rasterreihe die Rundenschranke 5 UEBERSTEIGEN."),
        ),
        zugausbeute=verteilung,
        # Strukturaussage, die keine Simulation braucht:
        mindestzuege_je_kapazitaet={
            str(r + 1): -(-KAPAZITAET[r] // KLEIN_FLIESEN) for r in range(6)},
        schranke_wenn_alles_in_eine_reihe=schranken(
            budget_gleichverteilt + chip_zellen_je_spieler),
        spalten_kosten_je_einheit=SPALTEN_KOSTEN,
        spalten_decke_analytisch=round(columns_under_uniform_distribution(
            budget_gleichverteilt + chip_zellen_je_spieler), 2),
    )

    # --- Sanity-Check gegen das gemessene Mensch-Profil -------------------
    if MESSUNG.exists():
        m = json.loads(MESSUNG.read_text(encoding="utf-8"))
        pruef = {}
        for lab in ("Mensch", "KI"):
            a = m[lab]["abschluesse_je_partie"]
            zellen = sum(a[str(r + 1)] * KAPAZITAET[r] for r in range(6))
            pruef[lab] = dict(
                verbrauchte_zellen=round(zellen, 2),
                anteil_am_partie_budget=round(zellen / FLIESEN_JE_PARTIE, 3),
                # Eine volle Spalte braucht EINE Zelle in JEDER Rasterreihe.
                # Die Zahl voller Spalten ist damit durch die SCHWAECHSTE
                # Reihe gedeckelt -- eine reine Strukturaussage.
                spalten_decke_schwaechste_reihe=round(
                    min(a[str(r + 1)] for r in range(6)), 2),
                spalten_gemessen=m[lab]["volle_spalten_je_partie"],
                # Was DASSELBE Budget getragen haette, gleichmaessig verteilt.
                # Die Luecke dazu ist ein reines VERTEILUNGS-Defizit: sie
                # kostet keine einzige zusaetzliche Fliese.
                spalten_moeglich_bei_gleichverteilung=round(
                    columns_under_uniform_distribution(zellen), 2),
            )
            d = pruef[lab]
            d["umsetzungsgrad"] = (round(d["spalten_gemessen"]
                                         / d["spalten_decke_schwaechste_reihe"], 3)
                                   if d["spalten_decke_schwaechste_reihe"] else None)
        summe = sum(v["verbrauchte_zellen"] for v in pruef.values())
        pruef["_beide_zusammen"] = dict(
            verbrauchte_zellen=round(summe, 2),
            analytisches_partie_budget=FLIESEN_JE_PARTIE,
            auslastung=round(summe / FLIESEN_JE_PARTIE, 3),
            hinweis=("Fliesen auf der Strafleiste und in unvollendeten Reihen sind "
                     "hier NICHT mitgezaehlt, Chip-Zellen dagegen schon -- die "
                     "Auslastung ist deshalb eine Naeherung, kein Kassensturz."),
        )
        ergebnis["sanity_check"] = pruef

    OUT_JSON.write_text(json.dumps(ergebnis, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Fliesen je Partie (beide Spieler): {FLIESEN_JE_PARTIE}")
    print(f"Budget je Spieler bei Gleichverteilung: {budget_gleichverteilt}"
          f" + {chip_zellen_je_spieler} Chip-Zellen")
    print(f"\nBeste Einfarb-Ausbeute EINES Zuges (kleine Fabrik, 4 Fliesen):")
    for k, v in verteilung["beste_ausbeute"].items():
        print(f"   {k} Fliesen: {100*v:5.1f} %")
    print(f"   Mittel {verteilung['beste_ausbeute_mittel']}"
          f"   (bei FESTGELEGTER Farbe nur {verteilung['festgelegte_farbe_mittel']})")
    print("\nMindestzahl Zuege je Kapazitaet (max 4 je Zug):")
    print("   " + "  ".join(f"R{r}:{ergebnis['mindestzuege_je_kapazitaet'][str(r)]}"
                            for r in range(1, 7)))
    print("\nSchranke je Reihe, wenn das GANZE Budget dort hineinginge:")
    s = ergebnis["schranke_wenn_alles_in_eine_reihe"]
    print("   " + "  ".join(f"R{r}:{s[str(r)]:5.2f}" for r in range(1, 7)))

    if "sanity_check" in ergebnis:
        print("\n=== Sanity-Check gegen das gemessene Profil ===")
        for lab in ("Mensch", "KI"):
            d = ergebnis["sanity_check"][lab]
            print(f"  {lab:7s} verbrauchte Zellen {d['verbrauchte_zellen']:6.2f}"
                  f"  ({100*d['anteil_am_partie_budget']:4.1f} % des Partie-Budgets)"
                  f"   Spalten-Decke {d['spalten_decke_schwaechste_reihe']:.2f}"
                  f"  gemessen {d['spalten_gemessen']:.2f}"
                  f"  Umsetzung {d['umsetzungsgrad']}")
            print(f"          dasselbe Budget gleichmaessig verteilt truege "
                  f"{d['spalten_moeglich_bei_gleichverteilung']:.2f} Spalten "
                  f"-- ohne eine einzige zusaetzliche Fliese")
        print()
        print("  Spezialfelder (Kriterium 7, -3 Pkt je leerem Feld):")
        print("    gemessen -11,94 / -12,23 Punkte je Partie-Seite "
              "(long_row_init_arena_eval.json) -> rund 4 leere Felder je Seite")
        print("    Das sind KEINE Gratis-Zellen: die drei anderen regulaeren")
        print("    Zellen der Platte muessen erst gefuellt sein, und jede kostet")
        print("    einen Musterreihen-Abschluss. Richtig ist: die VIERTE Zelle")
        print("    einer Platte zum Preis von DREIEN, also 25 Prozent Rabatt auf")
        print("    genau diese Platte -- gebunden an eine lokale Figur (2x2-Slot),")
        print("    nicht an eine globale wie eine Spalte.")
        b = ergebnis["sanity_check"]["_beide_zusammen"]
        print(f"  beide zusammen {b['verbrauchte_zellen']} von {b['analytisches_partie_budget']}"
              f" analytisch verfuegbaren Zellen ({100*b['auslastung']:.1f} %)")
    print(f"\n-> {OUT_JSON}")


if __name__ == "__main__":
    main()
