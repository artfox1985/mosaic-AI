# -*- coding: utf-8 -*-
"""Gepaarte Arena-Ergebnisse auf das Verwertbare eindampfen.

ANLASS (Nutzer-Ruege 2026-08-12): *"dir ist bewusst dass du gerade einen
datenfriedhof generierst weil ueberall die logs mitgeschrieben werden."* -- ja.
In einer Nacht 57 Dateien / 43,7 MB, davon 27,2 MB schon in der git-Historie.

WARUM `--log-games` UEBERHAUPT: die Verhaltensgroessen (Plattenpunkte je
Kriterium, Strafleiste) stehen NUR im Partie-Log; das Ergebnis-JSON ohne Logs
traegt allein Endstaende und Sieger. Der Schalter ist also noetig -- aber nur
WAEHREND des Laufs. Danach braucht kein Rasterpunkt mehr jede Platzierungszeile
jeder Runde.

Dieses Werkzeug zieht je Partie die acht Zahlen heraus, auf die es ankommt, und
schreibt sie als JSONL: eine Zeile je Partie, ~200 Byte statt ~25 kB. Damit
bleiben alle Auswertungen dieser Nacht reproduzierbar, ohne die Rohlogs zu halten.

Was es NICHT tut: Rohdateien loeschen. Das entscheidet der Nutzer pfadgenau
(stehende Projektregel). Dieses Werkzeug macht das Loeschen nur VERANTWORTBAR,
indem es das Verwertbare vorher sichert.

Aufruf:
    python -X utf8 tools/arena_compact.py                      # alle
    python -X utf8 tools/arena_compact.py --muster "vgrid2_*"  # Teilmenge
    python -X utf8 tools/arena_compact.py --pruefen            # nur vergleichen
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BASIS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASIS / "tools"))
from analyze_game_log import PATTERNS, ROUND_PREFIX  # noqa: E402
from plate_points_from_arena import KRITERIUM, game_list  # noqa: E402

ZIEL = BASIS / "evaluations" / "artifacts" / "arena_compact.jsonl"


def kompakt(sp: dict, quelle: str) -> dict:
    """Eine Partie -> die verwertbaren Zahlen, beide Spieler."""
    # Alt-Laeufe OHNE `--log-games` tragen weder `names` noch `game_seed` noch
    # `log` -- nur scores/winner/steps/total_floor. Die sind hier bewusst
    # zugelassen (sie sind ohnehin schlank), aber ihre Endwertung ist nicht
    # rekonstruierbar; das meldet die Zusammenfassung.
    namen = sp.get("names") or ["Netz", "Heuristik"]
    ni = next((i for i, n in enumerate(namen) if "euristik" not in n), 0)
    je_spieler: dict[str, dict[str, int]] = {}
    gesamt: dict[str, int] = {}
    aktiv = None
    for roh in sp.get("log") or []:
        m = ROUND_PREFIX.match(roh)
        text = m.group(2) if m else roh
        fs = PATTERNS["FINAL_SCORE"].match(text)
        if fs:
            aktiv = fs.group("name")
            gesamt[aktiv] = int(fs.group("total"))
            je_spieler.setdefault(aktiv, {})
            continue
        if aktiv:
            k = KRITERIUM.match(text)
            if k:
                je_spieler[aktiv][k.group("name").strip()] = int(k.group("pkt"))
            else:
                aktiv = None
    boden = sp.get("total_floor")
    return {
        "quelle": quelle,
        "seed": sp.get("game_seed"),
        "netz_index": ni,
        "namen": namen,
        "scores": sp.get("scores"),
        "scores_unclamped": sp.get("scores_unclamped"),
        "winner": sp.get("winner"),
        "steps": sp.get("steps"),
        "floor": boden if isinstance(boden, list) else [boden, None],
        "scoring_tile_ids": sp.get("scoring_tile_ids"),
        "endwertung_gesamt": gesamt,
        "endwertung_je_kriterium": je_spieler,
        # Zaehler der langen Musterreihen (PREREG_long_row_payoff.md par.3/B1,
        # Mitschrieb-Erweiterung 2026-08-24). MUSS mitgenommen werden: die
        # Vollendungsquote laesst sich aus dem Partie-LOG prinzipiell nicht
        # rekonstruieren (round_end.rs leert unplatzierbare Reihen ohne
        # Logzeile), sie steht ALLEIN in diesen Feldern. Ohne sie waere das
        # Eindampfen genau fuer die Messung verlustbehaftet, fuer die die
        # Felder gebaut wurden. `None` bei Artefakten aus aelteren Wheels --
        # der Auswerter unterscheidet "fehlt" von "null".
        "long_rows_started": sp.get("long_rows_started"),
        "long_rows_completed": sp.get("long_rows_completed"),
        "long_rows_cleared_unplaceable": sp.get("long_rows_cleared_unplaceable"),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--muster", default="*",
                   help="Glob auf den Teil nach paired_arena_env_ (Default: alle)")
    p.add_argument("--pruefen", action="store_true",
                   help="nur berichten, was eingedampft WUERDE, nichts schreiben")
    a = p.parse_args()

    dateien = sorted((BASIS / "evaluations").glob(
        f"paired_arena_env_{a.muster}.json"))
    if not dateien:
        raise SystemExit("keine passende Datei")

    zeilen, roh_bytes = [], 0
    ohne_log = []
    for f in dateien:
        roh_bytes += f.stat().st_size
        name = f.stem.replace("paired_arena_env_", "")
        # Mehr-Arm-Dateien: JE ARM eine eigene Quelle. KORREKTUR 2026-08-16
        # (Tor C): vorher wurden alle Arme zu EINER Quelle verschmolzen -- die
        # kompakte Form war damit fuer jeden Mehr-Arm-Lauf wertlos, weil sich
        # Test- und Kontrollpartien nicht mehr trennen liessen. Genau diese
        # Laeufe sind aber die, die eine Vorregistrierung als Beleg benennt.
        d = json.load(open(f, encoding="utf-8"))
        g = d["games"]
        quellen = ([(name, g)] if isinstance(g, list)
                   else [(f"{name}#{arm}", game_list(f, arm)) for arm in g])
        for quelle, sp_liste in quellen:
            if not any(sp.get("log") for sp in sp_liste):
                ohne_log.append(quelle)
            for sp in sp_liste:
                zeilen.append(kompakt(sp, quelle))

    # BESTAND ERHALTEN. KORREKTUR 2026-08-16 (Tor C): `ZIEL.write_text` hat den
    # Bestand bedingungslos ersetzt. Ein Lauf mit `--muster "gate_c_*"` haette
    # damit 14 961 Partien aus 33 aelteren Quellen geloescht, deren Rohdateien
    # teils nicht mehr existieren -- ein Datenverlust, den weder der Aufruf noch
    # die Ausgabe angekuendigt haetten. Jetzt werden nur die Zeilen der GERADE
    # eingedampften Quellen ersetzt, alle uebrigen bleiben stehen.
    neue_quellen = {z["quelle"] for z in zeilen}
    behalten = []
    if ZIEL.exists():
        for ln in ZIEL.read_text(encoding="utf-8").splitlines():
            if not ln.strip():
                continue
            alt = json.loads(ln)
            if alt.get("quelle") not in neue_quellen:
                behalten.append(alt)
    if behalten:
        print(f"Bestand: {len(behalten)} Partien aus "
              f"{len({z.get('quelle') for z in behalten})} anderen Quellen bleiben erhalten")
    neu_text = "\n".join(json.dumps(z, ensure_ascii=False) for z in zeilen)
    text = "\n".join(json.dumps(z, ensure_ascii=False)
                     for z in behalten + zeilen) + "\n"
    neu_bytes = len(neu_text.encode("utf-8"))
    print(f"{len(dateien)} Dateien, {len(zeilen)} Partien")
    print(f"roh      {roh_bytes / 1024 / 1024:8.1f} MB")
    # Die Quote bezieht sich auf die GERADE eingedampften Quellen, nicht auf die
    # ganze Zieldatei -- sonst waere sie nach der Bestandserhaltung sinnlos.
    print(f"kompakt  {neu_bytes / 1024 / 1024:8.1f} MB "
          f"({100 * neu_bytes / max(roh_bytes, 1):.1f} %)")
    if ohne_log:
        print(f"WARNUNG: {len(ohne_log)} Datei(en) ohne Partie-Logs -- deren "
              f"Endwertung ist NICHT rekonstruierbar und faellt bei einem "
              f"Loeschen der Rohdatei weg: {', '.join(ohne_log[:6])}"
              f"{' ...' if len(ohne_log) > 6 else ''}")
    fehlend = [z for z in zeilen if not z["endwertung_je_kriterium"]]
    if fehlend:
        print(f"WARNUNG: {len(fehlend)} Partien ohne Endwertungs-Aufschluesselung "
              f"-- Logtext geaendert? Rohdateien NICHT antasten.")
    if a.pruefen:
        print("\n--pruefen: nichts geschrieben.")
        return
    ZIEL.write_text(text, encoding="utf-8")
    print(f"\ngeschrieben -> {ZIEL.relative_to(BASIS)}")
    print("Die Rohdateien bleiben unangetastet -- ihr Loeschen ist eine "
          "Nutzer-Entscheidung, pfadgenau.")


if __name__ == "__main__":
    main()
