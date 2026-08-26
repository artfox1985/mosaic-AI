# -*- coding: utf-8 -*-
"""Schluessel-Tor fuer den Datei-Cache (PREREG_cache_build_time.md par.6).

Die ZWEITE der beiden Pflichtpruefungen aus par.6. Die erste (Bit-Identitaet,
`cache_parity_probe.py`) zeigt, dass gleiche Eingaben denselben Inhalt
ergeben -- das ist die leichtere Haelfte. Diese hier prueft die schwerere:
**ein geaenderter per-Datei-Parameter MUSS einen MISS erzeugen.** Ohne sie
belegt die Parität nur, dass der Cache trifft, nicht dass er zu Recht trifft.

Warum das die gefaehrliche Richtung ist: ein zu haeufiger MISS kostet
Rechenzeit und faellt sofort auf. Ein zu haeufiger TREFFER zieht STILL einen
veralteten Block ins Training -- die Falle, vor der die Key-Kommentare in
`neural_net.py` mehrfach warnen und die par.6 als das Risiko von Hebel (4)
benennt.

Geprueft werden beide Richtungen:
  A) MISS: je Parameter genau EINE Aenderung, alles andere gleich -> anderer
     Schluessel. Faellt ein Parameter durch, wird er NAMENTLICH gemeldet.
  B) TREFFER: zweimal derselbe Aufruf -> derselbe Schluessel (sonst waere der
     Cache wirkungslos, und A) bestuende trivial).

Zusaetzlich C): der Fenster-Schluessel darf NICHT im Datei-Schluessel stecken
-- zwei verschiedene Dateilisten, dieselbe Datei, gleicher Schluessel. Genau
das ist der Gewinn von Hebel (4); ohne diese Pruefung koennte der Datei-Cache
unbemerkt wieder am Fenster haengen.

Aufruf (netzfrei, Sekunden, keine Korpusdatei noetig):
    python -X utf8 -u tools/probes/file_cache_key_probe.py
"""
import json
import os
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "engine" / "py"))

BASIS = dict(value_target_variant="default", encoder="flat",
             conjunction_head=False, policy_carrier=True)

# Je Eintrag: Anzeigename, wie die Abweichung erzeugt wird.
#   ("arg", name, wert)  -> Aufrufargument aendern
#   ("env", name, wert)  -> Umgebungsknopf setzen (Modul wird neu geladen,
#                           weil _IGNORE_PTV beim Import gelesen wird)
ABWEICHUNGEN = [
    ("value_target_variant", "arg", "value_target_variant", "nortv"),
    ("encoder",              "arg", "encoder",              "2d"),
    ("conjunction_head",     "arg", "conjunction_head",     True),
    ("policy_carrier",       "arg", "policy_carrier",       False),
    ("MOSAIC_CACHE_NOPACK",  "env", "MOSAIC_CACHE_NOPACK",  "1"),
    ("MOSAIC_CACHE_F32",     "env", "MOSAIC_CACHE_F32",     "1"),
    ("MOSAIC_IGNORE_POLICY_TARGET_VALID", "env",
     "MOSAIC_IGNORE_POLICY_TARGET_VALID", "1"),
]


def _schluessel(basename, argaenderung=None, envaenderung=None):
    """Schluessel in einem FRISCHEN Import berechnen.

    Der Neu-Import ist Pflicht, nicht Kosmetik: `_IGNORE_PTV` wird EINMAL beim
    Import gelesen (bewusst, damit ein Prozess die Semantik nicht auf halber
    Strecke wechselt). Wer den Knopf nur setzt und dieselbe Modulinstanz
    befragt, misst den alten Wert und bekommt einen falschen GRUENEN Befund.
    """
    alt = {}
    if envaenderung:
        k, v = envaenderung
        alt[k] = os.environ.get(k)
        os.environ[k] = v
    try:
        for mod in ("neural_net",):
            sys.modules.pop(mod, None)
        import neural_net
        kw = dict(BASIS)
        if argaenderung:
            kw[argaenderung[0]] = argaenderung[1]
        return neural_net.per_file_cache_key(basename, **kw)
    finally:
        for k, v in alt.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def main() -> int:
    datei = "selfplay_hv2_g10_0001.pkl"
    referenz = _schluessel(datei)
    print(f"Referenz-Schluessel fuer {datei}: {referenz}", flush=True)

    befunde = {"referenz": referenz, "miss": {}, "treffer": None, "fenster_unabhaengig": None}
    versagt = []

    # --- A) jede Abweichung muss einen MISS erzeugen
    for anzeige, art, name, wert in ABWEICHUNGEN:
        if art == "arg":
            k = _schluessel(datei, argaenderung=(name, wert))
        else:
            k = _schluessel(datei, envaenderung=(name, wert))
        miss = (k != referenz)
        befunde["miss"][anzeige] = {"schluessel": k, "miss": miss}
        print(f"  {'OK  ' if miss else 'ROT '} {anzeige:38s} -> {k}"
              f"{'' if miss else '   ← TRIFFT DEN REFERENZ-CACHE'}", flush=True)
        if not miss:
            versagt.append(anzeige)

    # --- B) Gegenprobe: gleicher Aufruf, gleicher Schluessel
    wieder = _schluessel(datei)
    befunde["treffer"] = (wieder == referenz)
    print(f"  {'OK  ' if wieder == referenz else 'ROT '} Wiederholung ergibt denselben Schluessel",
          flush=True)
    if wieder != referenz:
        versagt.append("Wiederholbarkeit")

    # --- C) Fenster-Unabhaengigkeit: andere Datei -> anderer Schluessel,
    #        aber NICHTS an der Dateiliste geht ein (die Funktion kennt sie gar
    #        nicht -- diese Pruefung haelt das fest, damit es so bleibt).
    andere = _schluessel("selfplay_hv2_g10_0002.pkl")
    befunde["fenster_unabhaengig"] = (andere != referenz)
    print(f"  {'OK  ' if andere != referenz else 'ROT '} andere Datei -> anderer Schluessel",
          flush=True)
    if andere == referenz:
        versagt.append("Dateiname im Schluessel")

    ziel = pathlib.Path("evaluations/artifacts/file_cache_key_probe.json")
    ziel.parent.mkdir(parents=True, exist_ok=True)
    befunde["verdikt"] = "GRUEN" if not versagt else "ROT"
    befunde["versagt"] = versagt
    ziel.write_text(json.dumps(befunde, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    print(f"\nArtefakt: {ziel}")

    if versagt:
        print(f"\nROT -- diese Parameter aendern den Schluessel NICHT: {', '.join(versagt)}",
              file=sys.stderr)
        print("Ein Lauf mit dieser Abweichung wuerde still den vorhandenen Block laden.",
              file=sys.stderr)
        return 1
    print("\nGRUEN -- jeder per-Datei-Parameter erzeugt einen MISS.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
