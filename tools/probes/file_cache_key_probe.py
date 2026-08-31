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
             conjunction_head=False, bootstrap_native=True)

# Je Eintrag: Anzeigename, wie die Abweichung erzeugt wird.
#   ("arg", name, wert)  -> Aufrufargument aendern
#   ("env", name, wert)  -> Umgebungsknopf setzen (Modul wird neu geladen,
#                           weil _IGNORE_PTV beim Import gelesen wird)
DIVERGENCES = [
    ("value_target_variant", "arg", "value_target_variant", "nortv"),
    ("encoder",              "arg", "encoder",              "2d"),
    ("conjunction_head",     "arg", "conjunction_head",     True),
    # 2026-08-31 ENTFALLEN: der Traegerstatus ist kein Schluessel-Bestandteil
    # mehr. Der Block ist traegeragnostisch, die Maske kommt beim
    # Zusammenfuegen (build_cache_parallel.merge). Ein Divergenz-Fall dafuer
    # waere jetzt gegenstandslos -- die Invariante prueft
    # tools/probes/carrier_mask_at_merge_probe.py.
    # 2026-08-27: Zieldefinition je Datei (roher vs. Platt-entstauchter
    # Bootstrap in `values_wdl`) -- muss einen MISS erzeugen, sonst zieht ein
    # Lauf nach der Semantik-Umkehr still die entstauchten Bestands-Bloecke.
    ("bootstrap_native",     "arg", "bootstrap_native",     False),
    ("MOSAIC_CACHE_NOPACK",  "env", "MOSAIC_CACHE_NOPACK",  "1"),
    ("MOSAIC_CACHE_F32",     "env", "MOSAIC_CACHE_F32",     "1"),
    ("MOSAIC_IGNORE_POLICY_TARGET_VALID", "env",
     "MOSAIC_IGNORE_POLICY_TARGET_VALID", "1"),
]


def _key(basename, arg_change=None, env_change=None):
    """Schluessel in einem FRISCHEN Import berechnen.

    Der Neu-Import ist Pflicht, nicht Kosmetik: `_IGNORE_PTV` wird EINMAL beim
    Import gelesen (bewusst, damit ein Prozess die Semantik nicht auf halber
    Strecke wechselt). Wer den Knopf nur setzt und dieselbe Modulinstanz
    befragt, misst den alten Wert und bekommt einen falschen GRUENEN Befund.
    """
    old = {}
    if env_change:
        k, v = env_change
        old[k] = os.environ.get(k)
        os.environ[k] = v
    try:
        for mod in ("neural_net",):
            sys.modules.pop(mod, None)
        import neural_net
        kw = dict(BASIS)
        if arg_change:
            kw[arg_change[0]] = arg_change[1]
        return neural_net.per_file_cache_key(basename, **kw)
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def main() -> int:
    fname = "selfplay_hv2_g10_0001.pkl"
    reference = _key(fname)
    print(f"Referenz-Schluessel fuer {fname}: {reference}", flush=True)

    findings = {"referenz": reference, "miss": {}, "treffer": None, "fenster_unabhaengig": None}
    failures = []

    # --- A) jede Abweichung muss einen MISS erzeugen
    for display, kind, name, val in DIVERGENCES:
        if kind == "arg":
            k = _key(fname, arg_change=(name, val))
        else:
            k = _key(fname, env_change=(name, val))
        miss = (k != reference)
        findings["miss"][display] = {"schluessel": k, "miss": miss}
        print(f"  {'OK  ' if miss else 'ROT '} {display:38s} -> {k}"
              f"{'' if miss else '   ← TRIFFT DEN REFERENZ-CACHE'}", flush=True)
        if not miss:
            failures.append(display)

    # --- B) Gegenprobe: gleicher Aufruf, gleicher Schluessel
    again = _key(fname)
    findings["treffer"] = (again == reference)
    print(f"  {'OK  ' if again == reference else 'ROT '} Wiederholung ergibt denselben Schluessel",
          flush=True)
    if again != reference:
        failures.append("Wiederholbarkeit")

    # --- C) Fenster-Unabhaengigkeit: andere Datei -> anderer Schluessel,
    #        aber NICHTS an der Dateiliste geht ein (die Funktion kennt sie gar
    #        nicht -- diese Pruefung haelt das fest, damit es so bleibt).
    other = _key("selfplay_hv2_g10_0002.pkl")
    findings["fenster_unabhaengig"] = (other != reference)
    print(f"  {'OK  ' if other != reference else 'ROT '} andere Datei -> anderer Schluessel",
          flush=True)
    if other == reference:
        failures.append("Dateiname im Schluessel")

    target = pathlib.Path("evaluations/artifacts/file_cache_key_probe.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    findings["verdikt"] = "GRUEN" if not failures else "ROT"
    findings["versagt"] = failures
    target.write_text(json.dumps(findings, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    print(f"\nArtefakt: {target}")

    if failures:
        print(f"\nROT -- diese Parameter aendern den Schluessel NICHT: {', '.join(failures)}",
              file=sys.stderr)
        print("Ein Lauf mit dieser Abweichung wuerde still den vorhandenen Block laden.",
              file=sys.stderr)
        return 1
    print("\nGRUEN -- jeder per-Datei-Parameter erzeugt einen MISS.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
