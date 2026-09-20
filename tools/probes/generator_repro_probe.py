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
# Unterfelder des Record-Zustands, die Anzeige sind und keine Zugwahl: `state.log`
# (letzte 30 Textzeilen, serialize.rs). Seit 2026-09-07 schreibt die Engine auch den
# Pass als Zeile (Nutzer-Auftrag); ein Vergleich, der den Text mitliest, meldet dann
# Drift, wo Zug fuer Zug alles gleich ist. Geprueft am Paritaets-Hash des Champions
# (self_play.rs net_parity_hash, 2026-09-07 00:45).
# Seit 2026-09-10 traegt `state` zusaetzlich `dome_pool_view` (sichtkonformer Wissensstand
# ueber den Kuppelstapel, PREREG_v28_window.md par.4): ein aus dem Zustand ABGELEITETES
# Anzeige-/Record-Feld, das keine Zugwahl beeinflusst und das die eingefrorenen Golden-
# Probes (Anker 2026-08-26) nicht kennen. Ohne die Ausnahme meldete die Anker-Drift-Pruefung
# am 2026-09-10 23:35 Abweichung an Schritt 0, Feld `state`, waehrend Zuege, Policy und
# Werte gleich waren. Alles andere im Zustand wird weiter Feld fuer Feld verglichen.
STATE_IGNORED_SUBFIELDS = ("log", "dome_pool_view")


def _strip_state(v):
    if isinstance(v, dict):
        return {k: x for k, x in v.items() if k not in STATE_IGNORED_SUBFIELDS}
    return v


# Farblisten von BONUSCHIPS werden vor dem Vergleich sortiert, auf beiden Seiten.
#
# Anlass 2026-09-20: der Vorrat fuehrt seine Chipfarben seit der Kanonisierung
# (`dome::build_bonus_chip_pool`) in fester Enum-Ordnung. Die eingefrorenen Golden
# Probes tragen die alte Schreibweise der Abschrift, in der zwei von fuenf
# Kombinationen verdreht stehen (`[Schwarz, Blau]` gegen `[Blau, Schwarz]`). Der
# Vergleich meldete deshalb ROT an Schritt 0, obwohl derselbe Lauf ueber 1.763
# Schritte dieselben Zuege, dieselbe Policy und dieselben Ergebnisse hatte
# (Diagnose in `evaluations/PREREG_code_cleanup_closeout.md` par.8e). Im Spiel
# bedeutet die Reihenfolge innerhalb eines Chips nichts; die Wertung liest ihn
# ohnehin als Farb-Bitmaske (`round_end::chip_sig`).
#
# ENG BEGRENZT, und das ist der Punkt: NUR diese zwei Felder. Ein Suffix-Kriterium
# ("endet auf colors") waere falsch -- im Zustand enden auch `row_colors` (Farbe je
# Musterreihe) und `moon_top_colors` (Koepfe der Mondstapel) darauf, und DORT traegt
# die Reihenfolge Bedeutung; bei den Mondstapeln ist sie sogar ein eigener Suchknoten
# (Aktionen 406-410). Eine Sortierung haette genau den Unterschied geschluckt, den
# dieser Waechter finden soll. Wer die Menge erweitert, weist vorher nach, dass die
# Reihenfolge im betroffenen Feld bedeutungslos ist -- sonst lernt der Waechter,
# Unterschiede zu schlucken ("ein umgangenes Tor erzieht zum Umgehen").
#
# WIE LANGE noch noetig, damit niemand raten muss: solange eine eingefrorene Golden
# Probe von VOR dem 2026-09-20 im Baum liegt. Am 2026-09-21 nachgezaehlt sind das
# `models/frozen_heuristics/hv4_anchor/golden_probe/` (vorkanonisch, und per Definition
# eingefroren, solange Leitersegment 2 laeuft) und `frozen_champions/v30-b02/` (traegt
# beide Schreibweisen). `frozen_champions/v31-b01/` ist bereits nachkanonisch. Diese
# Normalisierung ist damit DAUERHAFT, nicht uebergangsweise -- der Anker ist der Grund.
CHIP_COLOR_FIELDS = ("colors", "unused_chip_colors")


def _canonical_chip_colors(v):
    """Chip-Farblisten kanonisch ordnen, rekursiv; alles andere unveraendert.

    Greift nur auf Listen reiner Zeichenketten unter `CHIP_COLOR_FIELDS` --
    `bag_colors`/`tower_colors` sind Zaehlungen je Farbe und damit ohnehin
    ausgenommen, weil sie keine Zeichenketten enthalten.
    """
    if isinstance(v, dict):
        out = {}
        for k, x in v.items():
            if (k in CHIP_COLOR_FIELDS and isinstance(x, list)
                    and all(isinstance(e, str) for e in x)):
                out[k] = sorted(x)
            else:
                out[k] = _canonical_chip_colors(x)
        return out
    if isinstance(v, list):
        return [_canonical_chip_colors(e) for e in v]
    return v


def _values_equal(va, vb):
    """Blattvergleich, numpy-tolerant (Bestandsverhalten von `_first_divergence`)."""
    import numpy as np

    try:
        return bool(np.array_equal(np.asarray(va), np.asarray(vb)))
    except Exception:
        return va == vb


def _compare_upward_tolerant(va, vb, path, added):
    """Vergleicht REFERENZ `va` gegen NEU `vb`, aufwaerts-tolerant.

    Nutzer-Entscheid 2026-09-13 ("Vorschlag d umsetzen"), Anlass: der P.14-Record
    `tiled_max_row` liess die Anker-Drift ROT melden, obwohl die Zugfolge Zug fuer
    Zug identisch war (Beleg `anchor_drift_counterproof_20260913_wheel1.json`:
    0 von 1.763 Records abweichend, sobald das neue Feld und der `game_id`-
    Zeitstempel abgezogen sind; Konservierung gegen dieselbe Probe GRUEN).

    Die Regel bildet die additive Konvention des Projekts ab
    (`project_2d_encoder_must_be_additive`), OHNE die Pruefung stumpf zu machen:

    - Ein Feld, das im NEUEN Record steht und der Referenz fehlt, ist ein
      ADDITIVER Zuwachs: es wird ignoriert und sein Pfad in `added` protokolliert.
    - Ein Feld, das die Referenz hat und dem neuen Record FEHLT, bleibt ROT --
      ein Rueckschritt ist kein Zuwachs.
    - Listen unterschiedlicher Laenge bleiben ROT.
    - Alles Uebrige wird weiter Wert fuer Wert verglichen.

    Rueckgabe: `None` bei Gleichheit, sonst der Pfad der ersten Abweichung.
    """
    if isinstance(va, dict) and isinstance(vb, dict):
        for k in sorted(va):
            if k not in vb:
                return f"{path}/{k} FEHLT im neuen Record"
            deeper = _compare_upward_tolerant(va[k], vb[k], f"{path}/{k}", added)
            if deeper is not None:
                return deeper
        for k in sorted(vb):
            if k not in va:
                added.append(f"{path}/{k}")
        return None
    if isinstance(va, list) and isinstance(vb, list):
        if len(va) != len(vb):
            return f"{path} LAENGE {len(va)} != {len(vb)}"
        for i, (xa, xb) in enumerate(zip(va, vb)):
            deeper = _compare_upward_tolerant(xa, xb, f"{path}[{i}]", added)
            if deeper is not None:
                return deeper
        return None
    return None if _values_equal(va, vb) else path


def _first_divergence(a, b, ignore=IDENTITY_FIELDS, added=None):
    """Erste Abweichung als (schritt_index, feld, wert_a, wert_b) oder None.

    Meldet NAMENTLICH, welches Feld zuerst auseinanderlaeuft. Ein blosses
    "ungleich" waere hier wertlos: ob die Policy-Verteilung driftet oder eine
    Zugwahl kippt, sind voellig verschiedene Befunde.

    `a` ist die REFERENZ, `b` der neue Lauf -- die Richtung zaehlt, seit der
    Vergleich aufwaerts-tolerant ist (siehe `_compare_upward_tolerant`). Wer
    die Pfade der additiv hinzugekommenen Felder braucht, reicht eine Liste
    als `added` herein.
    """
    if added is None:
        added = []
    for i, (ra, rb) in enumerate(zip(a, b)):
        fields = sorted((set(ra) | set(rb)) - set(ignore))
        for f in fields:
            if f not in rb:
                return i, f, "da", "FEHLT"
            if f not in ra:
                added.append(f"/{f}")
                continue
            va, vb = ra[f], rb[f]
            if f == "state":
                va = _canonical_chip_colors(_strip_state(va))
                vb = _canonical_chip_colors(_strip_state(vb))
            path = _compare_upward_tolerant(va, vb, f"/{f}", added)
            if path is not None:
                return i, path, repr(va)[:120], repr(vb)[:120]
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
        "ignorierte_felder": list(IDENTITY_FIELDS) + [f"state.{x}" for x in STATE_IGNORED_SUBFIELDS],
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
