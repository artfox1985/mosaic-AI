"""Positivraten der Konjunktions-Atome je Korpus-Quelle.

Zweck (Nutzer-Auftrag 2026-08-17): die URSACHE der schlechten Kalibrierung des
Konjunktions-Kopfes eingrenzen, BEVOR etwas dagegen gebaut wird. Gemessen ist
(PREREG_ownership_selector.md par.9.2): AUC 0,83-0,91, aber der Brier liegt nur
8-14 % unter der Grundrate, und ueber p=0,5 ueberschaetzt der Kopf deutlich.

Zwei konkurrierende Erklaerungen, und sie fuehren zu VERSCHIEDENEN Massnahmen:

  (a) VERTEILUNGSVERSCHIEBUNG -- der Kopf lernt auf den Bauer-Armen, in denen
      Spalten absichtlich geschlossen werden, und wird auf normalem Spiel
      benutzt, wo sie fast nie vorkommen. Dann UEBERSCHAETZT er zwangslaeufig,
      und die richtige Massnahme ist eine nachgelagerte Platt-Korrektur
      (Vorbild: neural_net.py::_destretch_prob).

  (b) ECHTE UEBERKONFIDENZ aus der Klassenschieflage -- der Ownership-Loss ist
      schlichtes maskiertes BCE ohne `pos_weight` (train.py:1082). Dann waere
      eine Loss-Aenderung noetig, die aber jeden Bestandsvergleich zerstoert.

Diese Sonde entscheidet zwischen beiden, indem sie die Positivrate je
Atomgruppe getrennt nach Quell-Praefix ausweist. Liegt sie in den Bauer-Armen
weit ueber der des Fensters, ist (a) belegt.

Reine Offline-Auswertung, kein Netz, keine GPU: die Labels kommen aus dem
ENDBRETT der Partien (`_conjunctions_from_dome`), nicht aus einer Vorhersage.
"""
import collections
import glob
import pickle
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))                      # config.py liegt in der Wurzel
sys.path.insert(0, str(REPO / "engine" / "py"))
from neural_net import _conjunctions_from_dome  # noqa: E402

# Atomgruppen laut `_conjunctions_from_dome`-Docstring -- ABGELESEN, nicht
# hergeleitet (config.py:91-116 nennt dieselbe Reihenfolge).
GRUPPEN = {
    "Reihen k0":       range(0, 6),
    "Spalten k1":      range(6, 12),
    "Diagonalen k2":   range(12, 14),
    "Ecken k5":        range(14, 18),
    "Joker k3":        range(18, 19),
    "farbenreich k7":  range(19, 25),
    "Layout (kein Kriterium)": range(25, 34),
}
DATEIEN_JE_PRAEFIX = 12   # Stichprobe je Quelle -- Raten brauchen keine Vollerhebung


def praefix(name: str) -> str:
    m = re.match(r"selfplay_(.+?)_\d{8}_", name)
    return m.group(1) if m else "?"


def main() -> None:
    quellen = collections.defaultdict(list)
    for muster in (str(REPO / "data" / "*.pkl"),
                   str(REPO / "data" / "ownership_corpus" / "*.pkl")):
        for f in glob.glob(muster):
            quellen[praefix(Path(f).name)].append(f)

    # je Quelle: Zaehler je Gruppe -> [positiv, gesamt]
    stat = {q: {g: [0, 0] for g in GRUPPEN} for q in quellen}
    games = collections.Counter()

    for q, dateien in sorted(quellen.items()):
        for f in sorted(dateien)[:DATEIEN_JE_PRAEFIX]:
            try:
                daten = pickle.load(open(f, "rb"))
            except Exception as e:
                print(f"  !! {Path(f).name}: {type(e).__name__} -- uebersprungen", flush=True)
                continue
            letzte = {}
            for s in daten:
                letzte[s.get("game_id")] = s
            for s in letzte.values():
                if not s.get("completed"):
                    continue
                st = s.get("state") or {}
                spieler = st.get("players") or []
                if len(spieler) < 2:
                    continue
                games[q] += 1
                for pl in spieler:
                    grid = pl.get("dome_grid")
                    if grid is None:
                        continue
                    atome = _conjunctions_from_dome(grid)
                    for g, idx in GRUPPEN.items():
                        for i in idx:
                            if i < len(atome):
                                stat[q][g][0] += atome[i]
                                stat[q][g][1] += 1

    kopf = ["Quelle", "Partien"] + [g.split(" ")[0] for g in GRUPPEN]
    print(f"\n{kopf[0]:14s} {kopf[1]:>8s} " + " ".join(f"{k:>12s}" for k in kopf[2:]))
    for q in sorted(stat, key=lambda x: -games[x]):
        if not games[q]:
            continue
        zellen = []
        for g in GRUPPEN:
            pos, ges = stat[q][g]
            zellen.append(f"{100*pos/ges:11.2f}%" if ges else "          --")
        print(f"{q:14s} {games[q]:8d} " + " ".join(zellen))
    print("\nAlle Werte sind Positivraten der ENDZUSTANDS-Labels, je Atom und Spieler.")
    print("Lesart: liegt 'Spalten' in den Bauer-Armen (k1/k2/k5/k6) weit ueber dem")
    print("Fenster (v18/v19wdl/v20wdl/v20wdlsw), ist die Verteilungsverschiebung belegt.")


if __name__ == "__main__":
    main()
