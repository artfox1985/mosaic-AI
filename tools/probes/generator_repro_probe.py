# -*- coding: utf-8 -*-
"""Reproduziert der heutige Build den v22-Korpus-Erzeuger? (Nutzer-Auftrag 2026-08-26)

DIE LAGE, die den Test noetig macht: `data/manifest_hv2_20260825_172710.json`
weist den Erzeuger als Commit `dbf6a086dc9f` mit `git_dirty: true` aus. Das
Erzeuger-Binary ist ueberschrieben, und der unversionierte Anteil ist nicht
rekonstruierbar. Es gibt nur Indizien fuer Verhaltensgleichheit -- die vier
Routing-Module sind gegen `dbf6a08` unveraendert und der `contract_hash`
stimmt (`a3f61f246d9bbf5c`) --, aber der Hash deckt den KNOPF-Vertrag ab, nicht
jedes Verhalten.

**Der Korpus ist seine eigene Golden Probe.** Das Rezept steht vollstaendig in
den `cli_args` des Manifests, und der Chunk-Seed ist `base_seed + chunk_idx`
(`self_play.py`, `make_chunk`) -- fuer den ERSTEN Chunk also der Basis-Seed
selbst. Mit `chunk = per_file = 10` faellt Chunk 0 genau auf die erste Datei.
Zehn Partien neu erzeugen und dagegenhalten kostet Minuten.

**VERGLICHEN WERDEN RECORDS, NICHT DATEIBYTES.** Der Korpus wurde am
2026-08-26 umgepackt (gzip, Faktor 35,4); die Dateibytes sind darum garantiert
verschieden, und ein Byte-Diff meldete eine Abweichung, die nichts mit dem
Erzeuger zu tun hat. `corpus_io.load_records` liest beide Formate am
Magic-Byte.

Aufruf:
    python -X utf8 -u tools/probes/generator_repro_probe.py \\
        --referenz data/selfplay_hv2_20260825_1727_g10.pkl \\
        --neu <scratch>/selfplay_hv2_<ts>_g10.pkl
"""
import argparse
import json
import pathlib
import sys
import time

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

from corpus_io import load_records  # noqa: E402


def _games(records):
    """Gruppiert die flache Schrittliste nach Partie.

    Die .pkl traegt eine flache Liste von Schritten; die Partie steht als Feld
    im Schritt. Gruppiert wird ueber den Wechsel der Partie-Kennung, nicht ueber
    ein Sortieren -- die Reihenfolge IST Teil dessen, was hier geprueft wird.
    """
    if not records:
        return []
    key_str = None
    for candidate in ("game_id", "game", "gid", "partie"):
        if candidate in records[0]:
            key_str = candidate
            break
    if key_str is None:
        return [records]  # keine Kennung: als EINE Einheit vergleichen
    game_list, current, last = [], [], object()
    for r in records:
        if r.get(key_str) != last and current:
            game_list.append(current)
            current = []
        last = r.get(key_str)
        current.append(r)
    if current:
        game_list.append(current)
    return game_list


# Felder, die eine LAUF-Identitaet tragen und kein Verhalten. `game_id` ist
# `hv2_<zeitstempel>_c<chunk>_g<nr>` (self_play.py) -- zwei Laeufe desselben
# Rezepts unterscheiden sich darin IMMER, auch wenn jeder Zug gleich ist.
# Ohne diese Ausnahme meldet der Vergleich Abweichung an Schritt 0 und
# verdeckt, dass alles dahinter uebereinstimmt. Gefunden an genau diesem Fall:
# die Selbstkontrolle zweier frischer Laeufe fiel nur hierueber.
IDENTITY_FIELDS = ("game_id",)


def _first_divergence(a, b, ignore=IDENTITY_FIELDS):
    """Erste Abweichung als (schritt_index, feld, wert_a, wert_b) oder None.

    Meldet NAMENTLICH, welches Feld zuerst auseinanderlaeuft. Ein blosses
    "ungleich" waere hier wertlos: ob die Policy-Verteilung driftet oder eine
    Zugwahl kippt, sind voellig verschiedene Befunde.
    """
    import numpy as np

    for i, (ra, rb) in enumerate(zip(a, b)):
        fields = sorted((set(ra) | set(rb)) - set(ignore))
        for f in fields:
            if f not in ra or f not in rb:
                return i, f, "FEHLT" if f not in ra else "da", "FEHLT" if f not in rb else "da"
            va, vb = ra[f], rb[f]
            try:
                same = bool(np.array_equal(np.asarray(va), np.asarray(vb)))
            except Exception:
                same = va == vb
            if not same:
                return i, f, repr(va)[:120], repr(vb)[:120]
    if len(a) != len(b):
        return min(len(a), len(b)), "<schrittzahl>", len(a), len(b)
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    # Flags bleiben deutsch (Doku oben), die Bezeichner im Code englisch (Regel
    # 2026-08-24): seit 809b41d las main() `a.reference`/`a.new`, argparse lieferte
    # aber `a.referenz`/`a.neu` -- die Sonde brach beim ersten Aufruf ab (2026-09-03).
    ap.add_argument("--referenz", dest="reference", required=True, help="Korpusdatei aus dem Originallauf")
    ap.add_argument("--neu", dest="new", required=True, help="frisch erzeugte Datei mit demselben Rezept")
    ap.add_argument("--out", default="evaluations/artifacts/generator_repro.json")
    a = ap.parse_args()

    t0, c0 = time.monotonic(), time.process_time()
    ref = load_records(a.reference)
    new = load_records(a.new)
    print(f"Referenz: {a.reference}  ({len(ref)} Schritte)", flush=True)
    print(f"Neu:      {a.new}  ({len(new)} Schritte)", flush=True)

    p_ref, p_neu = _games(ref), _games(new)
    print(f"Partien: Referenz {len(p_ref)}, neu {len(p_neu)}", flush=True)

    div = _first_divergence(ref, new)
    identical = div is None and len(ref) == len(new)

    finding = {
        "frage": "Reproduziert der heutige Build den v22-Korpus-Erzeuger?",
        "referenz": a.reference, "neu": a.new,
        "schritte": {"referenz": len(ref), "neu": len(new)},
        "partien": {"referenz": len(p_ref), "neu": len(p_neu)},
        "verdikt": "REPRODUZIERT" if identical else "ABWEICHUNG",
        "erste_abweichung": None if div is None else {
            "schritt": div[0], "feld": div[1], "referenz": div[2], "neu": div[3],
        },
        "ignorierte_felder": list(IDENTITY_FIELDS),
        "hinweis": ("Verglichen wurden RECORDS ueber corpus_io, nicht Dateibytes -- der Korpus "
                    "ist umgepackt, die Bytes sind darum ohnehin verschieden. `game_id` traegt "
                    "einen Zeitstempel und ist Lauf-Identitaet, kein Verhalten."),
        "laufzeit": {"wanduhr_s": round(time.monotonic() - t0, 1),
                     "cpu_s": round(time.process_time() - c0, 1),
                     "threads": 1, "s_je_partie": None},
    }
    target = pathlib.Path(a.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(finding, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")

    if identical:
        print(f"\nREPRODUZIERT: {len(ref)} Schritte in {len(p_ref)} Partien, Feld fuer Feld gleich.")
    else:
        print(f"\nABWEICHUNG: {finding['erste_abweichung']}", file=sys.stderr)
        print("Der heutige Build erzeugt NICHT denselben Korpus. Das ist ein Befund, keine "
              "Panne -- der Erzeuger lief mit unversionierten Aenderungen (git_dirty).",
              file=sys.stderr)
    print(f"Artefakt: {target}")
    return 0 if identical else 1


if __name__ == "__main__":
    raise SystemExit(main())
