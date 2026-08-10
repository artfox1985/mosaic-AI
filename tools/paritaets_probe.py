# -*- coding: utf-8 -*-
"""Paritaets-Sonde: belegt, dass ein Wheel-Neubau das Bestandsverhalten
BITGLEICH laesst (alle Env-Knoepfe auf Default).

Warum es dieses Werkzeug gibt: jeder Laufzeit-Knopf im Projekt hat einen
Default, der das vorherige Verhalten reproduzieren MUSS -- sonst waeren
Sweep-Arme, die vor und nach einem Wheel-Wechsel trainiert/gemessen wurden,
nicht mehr vergleichbar. Diese Sonde ist der Beweis dafuer: fixe Zustaende,
fixe Seeds, SHA256 ueber die Suchantworten.

Aufruf nach JEDER Wheel-Installation:

    python tools/paritaets_probe.py

Exit-Code 0 = Hash getroffen, 1 = Abweichung (dann sind die Defaults NICHT
byte-identisch und die Ursache gehoert geklaert, BEVOR irgendeine Messung
weiterlaeuft).

Verlagert aus dem Scratchpad einer alten Sitzung nach `tools/` (2026-08-10,
Nutzer-Auftrag "aktualisieren bzw. archivieren") -- vorher war der einzige
Beleg fuer die Byte-Identitaet ein Wegwerf-Skript in einem Temp-Verzeichnis.

PRUEFFLAECHE (bewusst eng): gehasht wird nur die Antwort von
`net_search_state_json`. `engine_config_json()` liegt AUSSERHALB -- ein
zusaetzliches Feld dort bricht die Sonde also nicht (so entschieden beim
A2-Vertragsstempel). Umgekehrt heisst das: die Sonde belegt Suchparitaet,
nicht Vertragsparitaet.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pickle
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "engine" / "py"))

# Erwarteter Hash der Default-Konfiguration. Aendert sich NUR, wenn das
# Bestandsverhalten absichtlich geaendert wird -- dann gehoert der neue Wert
# mit Begruendung in den Commit, nicht stillschweigend hierher.
EXPECTED = "8c6684ffba06cf3e16e898b83325f3154c04efac555c8e862c079b71155bd423"

MODEL = REPO / "models" / "alphazero_v20_2d_opp_brierbest.onnx"
FROZEN = REPO / "evaluations" / "frozen_eval_set.pkl"
SIMS = (150, 400)
ROUNDS = (1, 2, 3)  # Netzpfad aktiv; Runde 5 waere der round5.rs-Kurzschluss


def pick_states() -> list[dict]:
    """Je ein Drafting-Zustand aus den Runden 1-3, in Datei-Reihenfolge."""
    with FROZEN.open("rb") as fh:
        records = pickle.load(fh)["records"]
    states = []
    for rnd in ROUNDS:
        for rec in records:
            st = rec["state"]
            if st["round"] == rnd and st["phase"] == "drafting":
                states.append(st)
                break
    if len(states) != len(ROUNDS):
        raise SystemExit(
            f"Nur {len(states)} von {len(ROUNDS)} Zustaenden gefunden -- "
            f"{FROZEN.name} passt nicht zur Sonde."
        )
    return states


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--expected",
        default=EXPECTED,
        help="Soll-Hash (Default: der eingebaute Bestandswert)",
    )
    ap.add_argument(
        "--print-only",
        action="store_true",
        help="nur ausgeben, nicht vergleichen (fuer eine bewusste Neu-Festlegung)",
    )
    args = ap.parse_args()

    if not MODEL.exists():
        raise SystemExit(f"Modell fehlt: {MODEL}")

    import mosaic_rust

    digest = hashlib.sha256()
    for i, state in enumerate(pick_states()):
        for sims in SIMS:
            out = mosaic_rust.net_search_state_json(
                json.dumps(state), str(MODEL), sims, 1.5, 4242 + i
            )
            digest.update(out.encode("utf-8"))
    got = digest.hexdigest()
    print(f"PARITAETS-HASH: {got}")

    if args.print_only:
        return 0
    if got == args.expected:
        print("OK -- Defaults sind byte-identisch zum Bestand.")
        return 0
    print(f"ABWEICHUNG -- erwartet: {args.expected}")
    print(
        "Die Defaults reproduzieren das Bestandsverhalten NICHT. Ursache klaeren,\n"
        "bevor Messungen weiterlaufen: laufende Sweep-Arme waeren ueber den\n"
        "Wheel-Wechsel hinweg nicht mehr vergleichbar."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
