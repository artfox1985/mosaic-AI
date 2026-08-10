# -*- coding: utf-8 -*-
"""Wie oft KANN Musterreihe r (Kapazitaet r) ueberhaupt geschlossen werden?

**Policy-unabhaengig**, rein aus der Fliesen-Versorgung gerechnet -- keine
Self-Play-Daten, kein Netz. Nutzer-Auftrag 2026-08-10: *"hier kannst aber
eigentlich statistisch ausrechnen (unabhaengig vom self play) wie oft die reihe
1..6 abgeschlossen werden kann. dann kannst es auf die runden runterbrechen."*

## Warum das gebraucht wird

Die Grundraten aus dem Korpus koennen NICHT trennen, ob etwas strukturell
unmoeglich ist oder ob die KI es bloss nicht kann -- und wir wissen inzwischen,
dass die KI ihre Spezialplatten ausgerechnet in die untersten Slots legt, wo sie
sie nie schliesst. Die Korpus-Referenz ist also mit dem Defekt kontaminiert,
den sie messen soll. Diese Rechnung liefert die DECKE, gegen die sich ein
Defizit ueberhaupt beziffern laesst.

Drei Referenzpunkte gehoeren zusammen:
  DECKE   diese Rechnung -- wie oft sind r gleichfarbige Steine verfuegbar
  BODEN   Zufalls-Drafting (`round_transition::drive_drafting_to_leaf_naive`,
          ueber `drive_to_game_end` erreichbar) -- was ohne Absicht passiert
  IST     Champion-Korpus

## Spielzahlen (aus dem Code, nicht geschaetzt)

  5 ziehbare Farben (Wild ist kein ziehbarer Stein, `tile.rs`)
  TILES_PER_COLOR = 13  ->  65 Steine im Kreislauf
  je Runde: 4 kleine Fabriken x TILES_PER_SMALL_FACTORY(4) = 16
            + TILES_PER_LARGE_FACTORY(5)                  =  5
            = 21 SONNEN-Fliesen
  Musterreihe r hat Kapazitaet r+1 (`board.rs::capacity`), r=0..5 -> 1..6 Steine
  Reihen bleiben ueber den Rundenwechsel LIEGEN (`execute_end_tiling` raeumt nur
  UNPLATZIERBARE Reihen ab) -> Ansammeln ueber Runden ist moeglich

## Was die Rechnung NICHT beruecksichtigt -- die Richtung ist wichtig

1. **Mondfliesen fehlen** (`moon_stacks`/`moon_pool`). Sie ERHOEHEN die
   Verfuegbarkeit, die Zahlen hier sind also eine UNTERGRENZE der
   Verfuegbarkeit und damit eine KONSERVATIVE Decke. Fuer die Diagnose ist das
   die sichere Richtung: liegt der Champion unter der konservativen Decke, ist
   das Defizit echt.
2. **Exakt nur fuer Runde 1.** Ab Runde 2 ist der Beutel abgereichert (Steine
   auf der Kuppel verlassen den Kreislauf dauerhaft) und der Turm speist zurueck
   -- die Zusammensetzung ist dann nicht mehr 13-je-Farbe.
3. **Kein Wettbewerb modelliert.** Die Spalte "1 Spieler" nimmt an, ein Spieler
   koennte alles nehmen; "geteilt" halbiert. Beides sind Naeherungen, die
   echte Aufteilung haengt an der Zugreihenfolge.
4. **Die Regel "alle Steine EINER Farbe aus EINER Fabrik"** begrenzt einen
   einzelnen Zug, nicht die Runde -- ueber mehrere Zuege ist Ansammeln moeglich.
   Deshalb rechnet dies mit der RUNDEN-Verfuegbarkeit, nicht mit der pro Zug.

Aufruf:  python tools/musterreihen_verfuegbarkeit.py
"""
from __future__ import annotations

from fractions import Fraction
from math import comb

FARBEN = 5
JE_FARBE = 13
GESAMT = FARBEN * JE_FARBE          # 65
PRO_RUNDE = 4 * 4 + 5               # 21 Sonnenfliesen
RUNDEN = 5
KAPAZITAETEN = [r + 1 for r in range(6)]   # 1..6


def hyp_pmf(k: int, N: int, K: int, n: int) -> Fraction:
    """P(genau k Treffer) bei Ziehen ohne Zuruecklegen."""
    if k < 0 or k > K or n - k < 0 or n - k > N - K:
        return Fraction(0)
    return Fraction(comb(K, k) * comb(N - K, n - k), comb(N, n))


def p_mindestens(r: int, n: int = PRO_RUNDE) -> Fraction:
    """P(mindestens r Steine EINER bestimmten Farbe in der Rundenversorgung)."""
    return sum((hyp_pmf(k, GESAMT, JE_FARBE, n) for k in range(r, min(JE_FARBE, n) + 1)),
               Fraction(0))


def p_irgendeine_farbe(r: int, n: int = PRO_RUNDE) -> float:
    """P(mindestens EINE der 5 Farben hat >= r Steine).

    Naeherung: 1 - (1-p)^5 unter Unabhaengigkeitsannahme. Die Farbzahlen sind
    NEGATIV korreliert (feste Gesamtzahl), die Naeherung UEBERSCHAETZT also
    leicht -- Richtung im Modulkopf vermerkt.
    """
    p = float(p_mindestens(r, n))
    return 1.0 - (1.0 - p) ** FARBEN


def main() -> int:
    print(f"Versorgung je Runde: {PRO_RUNDE} Sonnenfliesen aus {GESAMT} "
          f"({FARBEN} Farben x {JE_FARBE}); Erwartung je Farbe "
          f"{PRO_RUNDE*JE_FARBE/GESAMT:.2f}")
    print("Exakt fuer Runde 1; ab Runde 2 ist der Beutel abgereichert (s. Modulkopf).\n")

    print(f"{'Reihe':>5} {'braucht':>8} | {'P(Farbe X hat >=r)':>19} "
          f"{'P(irgendeine Farbe)':>20} | {'geteilt: erwartet':>18}")
    for r_idx, kap in enumerate(KAPAZITAETEN, start=1):
        pX = float(p_mindestens(kap))
        pAny = p_irgendeine_farbe(kap)
        # Geteilt: ein Spieler bekommt im Schnitt die Haelfte der Rundenversorgung
        pShare = float(p_mindestens(kap, PRO_RUNDE // 2))
        print(f"{r_idx:>5} {kap:>8} | {pX:>19.4f} {pAny:>20.4f} | {pShare:>18.4f}")

    print("\n--- Ansammeln ueber Runden (Reihen bleiben liegen) ---")
    erwartet_je_runde = PRO_RUNDE * JE_FARBE / GESAMT / 2.0   # geteilt
    print(f"Erwartete Steine EINER Farbe je Spieler und Runde: {erwartet_je_runde:.2f}")
    for r_idx, kap in enumerate(KAPAZITAETEN, start=1):
        runden = kap / erwartet_je_runde
        machbar = "ja" if runden <= RUNDEN else "NEIN"
        print(f"  Reihe {r_idx} ({kap} Steine): ~{runden:.1f} Runden noetig "
              f"von {RUNDEN} -> in 5 Runden {machbar}")

    # Eine "wie oft je Partie"-Zahl waere IRREFUEHREND: sie unterstellt, dass
    # eine Reihe die gesamte Farbaufnahme fuer sich hat. Tatsaechlich
    # konkurrieren SECHS Reihen um dieselben ~10,5 Steine je Runde, und jede
    # braucht eine EIGENE Farbe. Die Gesamtmenge reicht (5 x 10,5 = ~52 gegen
    # 1+2+..+6 = 21 fuer alle Reihen einmal) -- bindend ist die
    # FARBUEBEREINSTIMMUNG je Reihe, nicht die Menge. Das modelliert diese
    # Rechnung nicht, also macht sie dazu bewusst keine Aussage.
    print("")
    print("BEWUSST KEINE Angabe zu Abschluessen je Partie: sechs Reihen konkurrieren")
    print("um dieselbe Aufnahme, jede mit EIGENER Farbe. Bindend ist die Farb-")
    print("uebereinstimmung, nicht die Menge -- 5 Runden x ~10,5 = ~52 Steine stehen")
    print("gegen 21 fuer alle sechs Reihen einmal.")
    print("")
    print("\nLESART: das ist die DECKE der Verfuegbarkeit, nicht des Koennens --")
    print("sie sagt, was die Versorgung zulaesst, nicht was eine Strategie erreicht.")
    print("Der BODEN kommt aus Zufalls-Drafting, das IST aus dem Champion-Korpus.")
    print("Erst der Abstand IST-zu-DECKE ist ein Defizit; ein niedriger BODEN")
    print("beweist nur, dass Zufall schlecht spielt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
