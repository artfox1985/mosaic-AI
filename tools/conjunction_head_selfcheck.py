# -*- coding: utf-8 -*-
"""
tools/conjunction_head_selfcheck.py -- Selbsttest der Konjunktions-Erweiterung
des Ownership-Kopfs (2026-08-10, Nutzer-Auftrag "bau in den ownership head die
konjunktionen ein").

Zwei Suiten, beide ohne Korpus und ohne GPU lauffaehig:

  LABELS  synthetische Kuppelraster, ueber die INVERSE Positionsabbildung
          (sr=r//2, sc=c//2, si=(r%2)*2+(c%2)) gebaut -- damit wird die
          Abbildung selbst mitgeprueft, nicht nur die Praedikate. Referenz ist
          `scoring.rs::build_grid` (Zeile 271) bzw. `row_unique_colors` (302).

  KOPF    Flag AUS  -> `ownership_head` exakt OWNERSHIP_TARGETS breit UND das
                       Modell bit-identisch zum Stand in HEAD (alte Datei per
                       `git show` geholt, gleicher Seed, Ausgaben verglichen).
          Flag AN   -> Breite + CONJUNCTION_TARGETS.
          Dazu Erkennung aus dem Checkpoint und `build_model_from_checkpoint`-
          Rundlauf in BEIDEN Modellklassen.
          Wird uebersprungen, wenn torch fehlt.

Die ERSCHOEPFENDE Pruefung bleibt die Identitaet gegen die Engine-Wertung auf
echtem Korpus-Material -- die laeuft ueber `tools/plattenkopf_labels.py check`
und braucht `data/`, liegt also nicht in diesem Selbsttest.

Aufruf:  python tools/conjunction_head_selfcheck.py
"""
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "engine" / "py"))

FAILS: list[str] = []


def expect(name, got, want):
    if got != want:
        FAILS.append(f"{name}: erwartet {want}, bekommen {got}")


# ── Suite 1: Labels ────────────────────────────────────────────────────────
IDX_ROW, IDX_COL, IDX_DIAG, IDX_CORNER, IDX_WILD, IDX_COLORFUL = 0, 6, 12, 14, 18, 19


def _empty_grid():
    return [[{"spaces": [{"type": "NORMAL", "color": None, "filled": None,
                          "locked": False} for _ in range(4)]}
             for _ in range(3)] for _ in range(3)]


def _cell(grid, r, c):
    return grid[r // 2][c // 2]["spaces"][(r % 2) * 2 + (c % 2)]


def check_labels(conj) -> None:
    g = _empty_grid()
    expect("leeres Brett", conj(g), [0] * 25)
    expect("Laenge", len(conj(g)), 25)

    g = _empty_grid()
    for r in range(6):
        for c in range(6):
            _cell(g, r, c)["filled"] = "blau"
    lab = conj(g)
    expect("voll: Reihen", lab[IDX_ROW:IDX_ROW + 6], [1] * 6)
    expect("voll: Spalten", lab[IDX_COL:IDX_COL + 6], [1] * 6)
    expect("voll: Diagonalen", lab[IDX_DIAG:IDX_DIAG + 2], [1, 1])
    expect("voll: Ecken", lab[IDX_CORNER:IDX_CORNER + 4], [1] * 4)
    expect("voll: Wild ohne Wildfelder", lab[IDX_WILD], 0)
    expect("voll: farbenreich bei 1 Farbe", lab[IDX_COLORFUL:IDX_COLORFUL + 6], [0] * 6)

    g = _empty_grid()
    for c in range(6):
        _cell(g, 3, c)["filled"] = "blau"
    lab = conj(g)
    expect("nur Zeile 3: Reihen", lab[IDX_ROW:IDX_ROW + 6], [0, 0, 0, 1, 0, 0])
    expect("nur Zeile 3: Spalten", lab[IDX_COL:IDX_COL + 6], [0] * 6)

    g = _empty_grid()
    for r in range(6):
        _cell(g, r, 5)["filled"] = "blau"
    expect("nur Spalte 5", conj(g)[IDX_COL:IDX_COL + 6], [0, 0, 0, 0, 0, 1])

    g = _empty_grid()
    for i in range(6):
        _cell(g, i, i)["filled"] = "blau"
    expect("Hauptdiagonale", conj(g)[IDX_DIAG:IDX_DIAG + 2], [1, 0])
    g = _empty_grid()
    for i in range(6):
        _cell(g, i, 5 - i)["filled"] = "blau"
    expect("Nebendiagonale", conj(g)[IDX_DIAG:IDX_DIAG + 2], [0, 1])

    for k, (sr, sc) in enumerate([(0, 0), (0, 2), (2, 0), (2, 2)]):
        g = _empty_grid()
        for dr in (0, 1):
            for dc in (0, 1):
                _cell(g, sr * 2 + dr, sc * 2 + dc)["filled"] = "blau"
        want = [0] * 4
        want[k] = 1
        expect(f"Eckplatte {(sr, sc)}", conj(g)[IDX_CORNER:IDX_CORNER + 4], want)

    g = _empty_grid()
    _cell(g, 0, 0)["type"] = "WILD"
    _cell(g, 4, 5)["type"] = "WILD"
    expect("Wild: beide leer", conj(g)[IDX_WILD], 0)
    _cell(g, 0, 0)["filled"] = "blau"
    expect("Wild: eines belegt", conj(g)[IDX_WILD], 0)
    _cell(g, 4, 5)["filled"] = "rot"
    expect("Wild: beide belegt", conj(g)[IDX_WILD], 1)

    g = _empty_grid()
    for c, col in enumerate(["blau", "rot", "gelb", "gruen", "tuerkis", "blau"]):
        _cell(g, 2, c)["filled"] = col
    expect("farbenreich: 5 Farben", conj(g)[IDX_COLORFUL + 2], 1)
    g = _empty_grid()
    for c, col in enumerate(["blau", "rot", "gelb", "gruen", "special", "blau"]):
        _cell(g, 2, c)["filled"] = col
    expect("farbenreich: Spezialstein zaehlt nicht", conj(g)[IDX_COLORFUL + 2], 0)


# ── Suite 2: Kopf ──────────────────────────────────────────────────────────
def check_head() -> bool:
    try:
        import torch
    except ModuleNotFoundError:
        print("   (torch fehlt -- Kopf-Suite uebersprungen)")
        return False

    import importlib.util

    def load(path, name):
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        return mod

    new = load(REPO / "engine" / "py" / "neural_net.py", "nn_new")
    old_src = subprocess.run(["git", "-C", str(REPO), "show", "HEAD:engine/py/neural_net.py"],
                             capture_output=True, text=True, check=True).stdout
    tmp = Path(tempfile.mkdtemp()) / "neural_net_old.py"
    tmp.write_text(old_src, encoding="utf-8")
    old = load(tmp, "nn_old")

    IN, NA, HS = 708, 406, 256

    def build(mod, cls, **kw):
        torch.manual_seed(12345)
        m = getattr(mod, cls)(input_size=IN, num_actions=NA, hidden_size=HS, **kw)
        m.eval()
        return m

    for cls, needs_planes in (("MosaicNet", False), ("Mosaic2DNet", True)):
        m_new, m_old = build(new, cls), build(old, cls)
        expect(f"{cls}/aus: Breite", m_new.ownership_head[-1].out_features, new.OWNERSHIP_TARGETS)
        expect(f"{cls}/aus: state_dict",
               {k: tuple(v.shape) for k, v in m_new.state_dict().items()},
               {k: tuple(v.shape) for k, v in m_old.state_dict().items()})
        torch.manual_seed(7)
        x = torch.rand(2, IN)
        args = (torch.rand(2, 76, 6, 6), x) if needs_planes else (x,)
        with torch.no_grad():
            o_new, o_old = m_new(*args), m_old(*args)
        expect(f"{cls}/aus: Ausgabenzahl", len(o_new), len(o_old))
        expect(f"{cls}/aus: bit-identisch",
               all(torch.equal(a, b) for a, b in zip(o_new, o_old)
                   if isinstance(a, torch.Tensor) and isinstance(b, torch.Tensor)), True)

        m_on = build(new, cls, conjunction_head=True)
        expect(f"{cls}/an: Breite", m_on.ownership_head[-1].out_features,
               new.OWNERSHIP_TARGETS + new.CONJUNCTION_TARGETS)

        for flag in (False, True):
            m = build(new, cls, conjunction_head=flag)
            expect(f"{cls}/erkennung flag={flag}",
                   new.conjunction_head_present(m.state_dict()), flag)
            rebuilt, _ = new.build_model_from_checkpoint(
                {"model_state": m.state_dict(), "hidden_size": HS})
            expect(f"{cls}/rundlauf flag={flag}",
                   rebuilt.ownership_head[-1].out_features,
                   m.ownership_head[-1].out_features)
    return True


def main() -> int:
    from neural_net import _conjunctions_from_dome
    print("LABELS ...")
    check_labels(_conjunctions_from_dome)
    print("KOPF ...")
    head_ran = check_head()

    if FAILS:
        print("\nFEHLGESCHLAGEN:")
        for f in FAILS:
            print("  -", f)
        return 1
    print(f"\nOK -- Labels bestanden{' und Kopf bestanden' if head_ran else ''}.")
    print("Erschoepfende Identitaetspruefung auf echtem Korpus: "
          "python tools/plattenkopf_labels.py check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
