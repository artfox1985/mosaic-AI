#!/usr/bin/env python
"""Das Musterreihen-Profil eines Spielers, DER ES KANN.

ANLASS (Nutzer-Hinweis 2026-08-24): jede empirische Referenz der Kampagne
stammt bisher aus Self-Play von Netzen, die lange Musterreihen nicht
vollenden -- als NIVEAU ist so eine Zahl wertlos, sie misst die Unfaehigkeit
des Erzeugers. Der Nutzer hat aber selbst gegen den Champion gespielt und
dabei 8 von 9 Partien gewonnen. Diese Logs sind damit die EINZIGE
unkontaminierte empirische Quelle im Repo fuer die Frage, wie das
Reihen-Profil aussieht, wenn jemand das Spiel beherrscht.

Quelle: `static/log/game_*.log` (Web-Oberflaeche). Der JSON-Kopfkommentar
traegt `players`, `ai_player`, `ai_model`, `ai_sims` -- daraus fallen die
Rollen eindeutig, ohne Namensraterei.

**Warum das methodisch sauber ist, trotz n~10:** Mensch und Netz spielen
DIESELBE Partie. Der Vergleich ist gepaart je Partie, es gibt keinen
Aera-, Seed- oder Gegnerversatz. Die DIFFERENZ ist damit belastbar; das
absolute Niveau des Menschen ist eine Stichprobe eines einzigen Spielers.

**Vorbehalt, der in jeden Bericht gehoert:** der Gegner war schwach (der
Mensch gewinnt fast immer). Weniger Konkurrenz um dieselben Fliesen macht
lange Reihen billiger, als sie gegen einen starken Gegner waeren. Als
Existenzbeweis ("es geht, und es zahlt sich aus") traegt das; als exaktes
Zielprofil ist es eine Stichprobe.

KEIN eigener Parser -- dieselben Bausteine wie die Arena-Sonden:
`row_choices_from_log` (Zugziele), `rekonstruiere_partie` /
`spalten_fuellung` / `struktur_kennzahlen` (Kuppel-Endstand).

SELBSTTEST: das KI-Profil aus diesen Logs muss der unabhaengigen
Self-Play-Messung in `docs/domain_knowledge.md` §1 in der FORM entsprechen
(monotoner Einbruch ab Reihe 3, Reihe 6 unter 1,0). Zwei verschiedene
Quellen und zwei verschiedene Werkzeuge -- weicht das ab, ist die
Extraktion kaputt und nicht die Welt.

Aufruf:  python -X utf8 tools/probes/human_row_profile_probe.py
"""
from __future__ import annotations

import glob
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "probes"))

from row_preference_probe import row_choices_from_log  # noqa: E402
from column_build_structural_probe import (  # noqa: E402
    rekonstruiere_partie,
    spalten_fuellung,
    struktur_kennzahlen,
)

OUT_JSON = ROOT / "evaluations" / "human_row_profile.json"
LOGS = ROOT / "static" / "log"

# Referenz aus docs/domain_knowledge.md §1 (selfplay_v20wdl_*, 600 Partien).
# NICHT als Zielprofil -- nur als Formvergleich fuer den Selbsttest.
DOMAIN_KNOWLEDGE_KI = [4.80, 4.77, 2.84, 1.89, 0.84, 0.58]


def rasterreihe(space_index: int, tile_row: int) -> int:
    """Kuppel-Rasterreihe einer Zelle. Slot-Layout [0][1] / [2][3]
    (`dome.rs::rotation_indices`): Space 0/1 liegen in der oberen
    Teilreihe des Slots, 2/3 in der unteren. Gegenstueck zur
    Spalten-Formel in `spalten_fuellung` (2*tc + si%2)."""
    return 2 * tile_row + space_index // 2


def partie_auswerten(pfad: Path) -> dict | None:
    lines = pfad.read_text(encoding="utf-8", errors="replace").splitlines()
    kopf = next((l for l in lines[:6] if l.startswith("# {")), None)
    if not kopf:
        return None
    meta = json.loads(kopf[2:])
    namen, ai_i = meta.get("players"), meta.get("ai_player")
    if not namen or ai_i is None:
        return None
    rolle = {namen[ai_i]: "KI", namen[1 - ai_i]: "Mensch"}

    zuege = {"Mensch": Counter(), "KI": Counter()}
    for (_rnd, nm, reihe) in row_choices_from_log(lines):
        if nm in rolle:
            zuege[rolle[nm]][reihe] += 1

    abschluesse = {"Mensch": Counter(), "KI": Counter()}
    spalten = {}
    for nm, zellen in rekonstruiere_partie(lines).items():
        if nm not in rolle:
            continue
        lab = rolle[nm]
        for (tr, _tc, si) in zellen:
            abschluesse[lab][rasterreihe(si, tr)] += 1
        spalten[lab] = struktur_kennzahlen(spalten_fuellung(zellen))

    if len(spalten) != 2:
        return None
    return dict(datei=pfad.name, seed=meta.get("seed"),
                ai_model=meta.get("ai_model"), ai_sims=meta.get("ai_sims"),
                zuege=zuege, abschluesse=abschluesse, spalten=spalten)


def main() -> None:
    partien = [p for p in (partie_auswerten(Path(f))
                           for f in sorted(glob.glob(str(LOGS / "game_*.log")))) if p]
    if len(partien) < 3:
        raise SystemExit(f"nur {len(partien)} auswertbare Logs -- zu wenig")
    n = len(partien)

    ergebnis = {"n_partien": n,
                "quellen": [p["datei"] for p in partien],
                "ai_modelle": sorted({p["ai_model"] for p in partien}),
                "vorbehalt": ("gepaart je Partie (Mensch und Netz spielen dieselbe "
                              "Partie), Differenz belastbar; absolutes Niveau ist eine "
                              "Stichprobe EINES Spielers gegen einen schwachen Gegner")}

    for lab in ("Mensch", "KI"):
        zuege_ges = sum(sum(p["zuege"][lab].values()) for p in partien)
        ergebnis[lab] = dict(
            zugziele_anteil_prozent={
                str(r): round(100.0 * sum(p["zuege"][lab][r] for p in partien) / zuege_ges, 2)
                for r in range(1, 7)} if zuege_ges else None,
            n_reihenzuege=zuege_ges,
            abschluesse_je_partie={
                str(r + 1): round(sum(p["abschluesse"][lab][r] for p in partien) / n, 3)
                for r in range(6)},
            volle_spalten_je_partie=round(
                sum(p["spalten"][lab]["volle_spalten"] for p in partien) / n, 3),
            max_spaltenhoehe=round(
                sum(p["spalten"][lab]["max_hoehe"] for p in partien) / n, 3),
            teilspalten_ge4=round(
                sum(p["spalten"][lab]["teilspalten_ge4"] for p in partien) / n, 3),
        )

    # Gepaarte Differenz je Partie -- die belastbare Groesse (s. Kopf).
    ergebnis["gepaart_mensch_minus_ki"] = dict(
        abschluesse_je_reihe={
            str(r + 1): round(sum(p["abschluesse"]["Mensch"][r] - p["abschluesse"]["KI"][r]
                                  for p in partien) / n, 3)
            for r in range(6)},
        volle_spalten=round(sum(p["spalten"]["Mensch"]["volle_spalten"]
                                - p["spalten"]["KI"]["volle_spalten"]
                                for p in partien) / n, 3),
    )

    ki = [ergebnis["KI"]["abschluesse_je_partie"][str(r + 1)] for r in range(6)]
    selbsttest_ok = ki[5] < 1.0 and ki[2] < ki[1] and ki[5] < ki[4] < ki[3]
    ergebnis["selbsttest"] = dict(
        bestanden=bool(selbsttest_ok),
        ki_profil=ki,
        referenz_domain_knowledge=DOMAIN_KNOWLEDGE_KI,
        kriterium=("KI-Profil muss die Form der unabhaengigen Self-Play-Messung "
                   "haben: Einbruch ab Reihe 3, monoton fallend R4>R5>R6, R6 unter 1,0"),
    )

    OUT_JSON.write_text(json.dumps(ergebnis, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"{n} Partien, Modelle: {', '.join(ergebnis['ai_modelle'])}\n")
    print("Zugziele je Musterreihe (Prozent der Draft-Zuege):")
    for lab in ("Mensch", "KI"):
        z = ergebnis[lab]["zugziele_anteil_prozent"]
        print(f"  {lab:7s} " + "  ".join(f"R{r}:{z[str(r)]:5.1f}" for r in range(1, 7)))
    print("\nAbschluesse je Musterreihe und Partie (max 5):")
    for lab in ("Mensch", "KI"):
        a = ergebnis[lab]["abschluesse_je_partie"]
        print(f"  {lab:7s} " + "  ".join(f"R{r}:{a[str(r)]:5.2f}" for r in range(1, 7)))
    d = ergebnis["gepaart_mensch_minus_ki"]["abschluesse_je_reihe"]
    print("  " + "Delta  " + "  ".join(f"R{r}:{d[str(r)]:+5.2f}" for r in range(1, 7)))
    print("\nSpalten je Partie:")
    for lab in ("Mensch", "KI"):
        e = ergebnis[lab]
        print(f"  {lab:7s} voll {e['volle_spalten_je_partie']:.2f}   "
              f"max Hoehe {e['max_spaltenhoehe']:.2f}   >=4 {e['teilspalten_ge4']:.2f}")
    print(f"  Delta voll {ergebnis['gepaart_mensch_minus_ki']['volle_spalten']:+.2f}")
    print(f"\nSelbsttest KI-Profil gegen domain_knowledge: "
          f"{'BESTANDEN' if selbsttest_ok else 'GESCHEITERT'}")
    print(f"-> {OUT_JSON}")
    if not selbsttest_ok:
        raise SystemExit("Selbsttest gescheitert -- Extraktion pruefen, nicht die Zahlen glauben")


if __name__ == "__main__":
    main()
