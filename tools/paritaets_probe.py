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
A2-Vertragsstempel, verifiziert 2026-08-10: die Suchantwort enthaelt
`contract_hash`/`input_size`/`num_planes_channels` nicht). Umgekehrt heisst
das: die Sonde belegt Suchparitaet, nicht Vertragsparitaet.

# WHEEL-FRISCHE-CHECK (Nutzer-Auftrag 2026-08-13): die teuerste Fehlerklasse
# dieser Woche war eine Messung auf einem veralteten Wheel -- cargo test gruen,
# aber maturin/pip vergessen, 16 Minuten Messzeit auf totem Code (Beleg:
# PREREG_injektion_wertungsplatten.md, "bit-identische Gegenprobe"). Diese
# Probe laeuft vor jeder Messkampagne, also ist sie der richtige Waechter:
# ist eine Engine-Quelle JUENGER als die installierte .pyd, ist jede Messung
# mit dem installierten Wheel verdaechtig.
import importlib.util as _ilu
from pathlib import Path as _P
def _wheel_frische_warnung() -> None:
    try:
        spec = _ilu.find_spec("mosaic_rust")
        pyd = max(_P(spec.origin).parent.glob("*.pyd"), key=lambda f: f.stat().st_mtime)
        pyd_zeit = pyd.stat().st_mtime
        quellen = list((_P(__file__).resolve().parent.parent / "engine" / "src").glob("*.rs"))
        neuere = [q.name for q in quellen if q.stat().st_mtime > pyd_zeit]
        if neuere:
            print(f"WARNUNG WHEEL-FRISCHE: {len(neuere)} Engine-Quelle(n) sind JUENGER "
                  f"als die installierte Erweiterung ({pyd.name}): "
                  f"{', '.join(sorted(neuere)[:5])}{' ...' if len(neuere) > 5 else ''}")
            print("  -> maturin build --release && pip install --force-reinstall --no-deps, "
                  "sonst misst der naechste Lauf totes Verhalten.")
    except Exception as e:  # Frische-Check darf die Probe nie brechen
        print(f"(Wheel-Frische-Check uebersprungen: {e})")
_wheel_frische_warnung()

DIAGNOSE-FELDER WERDEN AUSGEBLENDET (`EXCLUDED_FIELDS`). Grund, und es ist
eine Lehre aus zwei Fehlalarmen derselben Art: der Soll-Hash wurde auf einer
Ausgabe OHNE die Stufe-2-Diagnosefelder gebildet. Wer die rohe Ausgabe
hasht, bekommt garantiert eine Abweichung, sobald irgendwann ein additives
Diagnosefeld hinzukam -- und muss dann jedes Mal von Hand nachweisen, dass
das Verhalten trotzdem gleich ist (beim zweiten Mal am 2026-08-10: 156
Vorkommen entfernt, `8c6684ff...` exakt reproduziert).

Die Liste ist bewusst eine ERLAUBNISLISTE mit festen Namen, kein Muster: ein
NEUES Feld bricht die Sonde weiterhin, und das ist gewollt -- dann soll ein
Mensch entscheiden, ob es Diagnose oder Verhalten ist. Wird ein Feld hier
aufgenommen, ist die Sonde fuer dessen Inhalt blind; das ist nur fuer reine
Diagnose zulaessig, die keine Zugwahl beeinflusst.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pickle
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "engine" / "py"))

# Erwarteter Hash der Default-Konfiguration. Aendert sich NUR, wenn das
# Bestandsverhalten absichtlich geaendert wird -- dann gehoert der neue Wert
# mit Begruendung in den Commit, nicht stillschweigend hierher.
#
# GEPRUEFT 2026-08-13 (PREREG_such_rng_trennen.md, RNG-Schnitt Suche/Partie):
# der Hash haelt UNVERAENDERT, ENTGEGEN der Prereg-Erwartung in §4a ("Hash
# MUSS brechen"). Grund, am Code nachgeprueft: diese Sonde haengt AUSSCHLIESSLICH
# an `net_search_state_json` (lib.rs) -> `net_search_with_tree`, und DIESER
# Aufruf war nie Teil des Schnitts -- er baut sich pro Aufruf einen FRISCHEN,
# eigenen `rng` (aus dem `seed`-Parameter) und gibt ihn NIE an eine
# fortlaufende Partie-Schleife weiter, die zusaetzlich echte Zustands-
# Ereignisse (Beutel-Refills) aus demselben Strom zoege -- exakt das
# Praezedenzmuster, das `tools/analyze_game_log.py::deterministic_seed()`
# fuer sein Orakel schon nutzt. Der reparierte Fehler (Suche verschiebt den
# GETEILTEN Partie-RNG in self_play.rs/py.rs) tritt hier also strukturell
# nicht auf; der Schnitt betraf `self_play.rs`s Spielschleifen und
# `py.rs::PyGame::ai_drafting_step`/`ai_drafting_net_step` (Live-KI-Zuege),
# NICHT diesen Einzelaufruf-Pfad. Die Prereg-Prognose war insofern falsch;
# die Basislinie bleibt deshalb UNVERAENDERT (kein neuer Hash noetig).
EXPECTED = "8c6684ffba06cf3e16e898b83325f3154c04efac555c8e862c079b71155bd423"

MODEL = REPO / "models" / "alphazero_v20_2d_opp_brierbest.onnx"
FROZEN = REPO / "evaluations" / "frozen_eval_set.pkl"
SIMS = (150, 400)
ROUNDS = (1, 2, 3)  # Netzpfad aktiv; Runde 5 waere der round5.rs-Kurzschluss

# Additive DIAGNOSE-Felder, die nicht in den Hash eingehen (siehe Modul-Doku).
# `net_raw_value`/`net_points_forecast`/`net_opp_points_forecast` kamen mit dem
# Stufe-2-Instrument (`PREREG_punktekopf_platten.md`) hinzu und beeinflussen die
# Zugwahl nicht -- sie werden je Wurzelkandidat nur mitgeschrieben.
EXCLUDED_FIELDS = ("net_raw_value", "net_points_forecast", "net_opp_points_forecast")
_EXCLUDE_RE = re.compile(
    r',"(?:' + "|".join(EXCLUDED_FIELDS) + r')":(?:-?[0-9.eE+]+|null)'
)


def strip_diagnostics(payload: str) -> tuple[str, int]:
    """Entfernt die Diagnose-Felder; gibt (bereinigt, Anzahl) zurueck."""
    return _EXCLUDE_RE.subn("", payload)


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
    stripped = 0
    for i, state in enumerate(pick_states()):
        for sims in SIMS:
            out = mosaic_rust.net_search_state_json(
                json.dumps(state), str(MODEL), sims, 1.5, 4242 + i
            )
            reduced, removed = strip_diagnostics(out)
            stripped += removed
            digest.update(reduced.encode("utf-8"))
    got = digest.hexdigest()
    print(f"PARITAETS-HASH: {got}  (ausgeblendete Diagnose-Vorkommen: {stripped})")

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
