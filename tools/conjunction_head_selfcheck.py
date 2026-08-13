# -*- coding: utf-8 -*-
"""
tools/conjunction_head_selfcheck.py -- Selbsttest der Konjunktions-Erweiterung
des Ownership-Kopfs (2026-08-10, Nutzer-Auftrag "bau in den ownership head die
konjunktionen ein").

Drei Suiten, alle ohne Korpus und ohne GPU lauffaehig:

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

  ENGINE  (neu, 2026-08-11) die ERSCHOEPFENDE Pruefung: dieselbe Funktion
          `_conjunctions_from_dome`, die das laufende Training als Ziel liest,
          gegen den ECHTEN kompilierten Rust-Kern (`mosaic_rust`), nicht gegen
          eine Rust-Reimplementierung der Spezifikation. Weg: konstruierte
          Kuppelraster als vollstaendiges `state_json` (Skelett von einem
          frischen `PyGame`, NUR `dome_grid` ersetzt) an
          `mosaic_rust.end_scoring_from_state_json` -- exakt derselbe
          PyO3-Pfad, den `serialize.rs::end_scoring_from_state` fuer
          `dome_grid` als "Space-fuer-Space EXAKT" dokumentiert (Test
          `end_scoring_from_state_is_exact_after_roundtrip`). Kein Korpus
          noetig, weil die 34 Labels auf dem Champion-/Self-Play-Korpus laut
          `PREREG_plate_head.md` fuer viele Atome praktisch konstant 0 sind
          (Diagonalen, Spalte 1, Reihen 5/6, untere Eckslots) -- eine Pruefung
          dort liefe genau an den Stellen leer, an denen ein Fehler am
          ehesten unentdeckt bliebe. Die Bretter hier sind darum von Hand so
          gebaut, dass jedes der 34 Label sowohl feuert als auch nicht
          feuert (Coverage-Assertion am Ende der Suite). NICHT uebersprungen,
          `mosaic_rust` ist Kernabhaengigkeit dieses Projekts.

          Was diese Suite NICHT prueft: die reine Rust-Spezifikation (ob
          `score_*` selbst den Docstring korrekt umsetzt) traegt zusaetzlich
          `engine/src/scoring.rs::plattenkopf_conjunction_atoms_match_spec`
          (nicht `#[ignore]`, cargo-test-Suite) -- eine Reimplementierung der
          34 Atome IN Rust gegen dieselben `score_*`-Funktionen. Diese
          Rust-Pruefung verifiziert die SPEZIFIKATION, NICHT
          `neural_net.py::_conjunctions_from_dome` selbst (die Labels laufen
          in Python auf der Dome-JSON-Struktur, die Wertung dort in Rust auf
          `PlayerBoard` -- zwei getrennte Implementierungen). Beide Suiten
          zusammen schliessen die Luecke: ENGINE deckt die echte
          Python-Implementierung ab, die Rust-Suite deckt die Engine-Seite
          als schneller Regressionstest ohne Python/PyO3-Umweg.

Aufruf:  python tools/conjunction_head_selfcheck.py
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "engine" / "py"))

import mosaic_rust  # noqa: E402 -- Kernabhaengigkeit, Suite 3 (ENGINE) unten
                     # prueft explizit gegen den echten kompilierten Kern und
                     # wird darum NICHT weich uebersprungen wie z.B. torch.

FAILS: list[str] = []


def expect(name, got, want):
    if got != want:
        FAILS.append(f"{name}: erwartet {want}, bekommen {got}")


# ── Suite 1: Labels ────────────────────────────────────────────────────────
IDX_ROW, IDX_COL, IDX_DIAG, IDX_CORNER, IDX_WILD, IDX_COLORFUL = 0, 6, 12, 14, 18, 19
# 25..33 ist LAYOUT, keine Konjunktion: traegt Slot s eine Jokerplatte?
# Schliesst den Multiplikator von Kriterium 3 (`2 x wild_total`).
IDX_WILDSLOT, N_CONJ = 25, 34

# Eckslot-Reihenfolge und Punktwerte wie `_conjunctions_from_dome` (Zeile 971)
# UND `scoring.rs::score_corner_tiles` (obere Ecken +3, untere +8) -- fuer
# Suite 3 (ENGINE) unten, dort gegen den echten Rust-Wert geprueft statt aus
# dieser Liste uebernommen.
CORNER_SLOTS = ((0, 0), (0, 2), (2, 0), (2, 2))
CORNER_WEIGHTS = (3, 3, 8, 8)
ENGINE_COLORS = ("blau", "gelb", "rot", "schwarz", "türkis")


def _empty_grid():
    return [[{"spaces": [{"type": "NORMAL", "color": None, "filled": None,
                          "locked": False} for _ in range(4)]}
             for _ in range(3)] for _ in range(3)]


def _cell(grid, r, c):
    return grid[r // 2][c // 2]["spaces"][(r % 2) * 2 + (c % 2)]


def check_labels(conj) -> None:
    g = _empty_grid()
    expect("leeres Brett", conj(g), [0] * N_CONJ)
    expect("Laenge", len(conj(g)), N_CONJ)

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

    # --- Layout-Block 25..33: traegt Slot s eine Jokerplatte?
    g = _empty_grid()
    expect("Layout: kein Wild irgendwo", conj(g)[IDX_WILDSLOT:IDX_WILDSLOT + 9], [0] * 9)

    # Ein WILD-Space in Slot (1,2) -- slot_row-major heisst Index 1*3+2 = 5.
    g = _empty_grid()
    g[1][2]["spaces"][0]["type"] = "WILD"
    want = [0] * 9
    want[5] = 1
    expect("Layout: nur Slot (1,2)", conj(g)[IDX_WILDSLOT:IDX_WILDSLOT + 9], want)

    # Unbelegt zaehlt trotzdem: das Label ist LAYOUT, nicht Fuellung.
    expect("Layout: zaehlt unbelegt", conj(g)[IDX_WILDSLOT + 5], 1)
    expect("Layout: Fuellungs-Label bleibt 0", conj(g)[IDX_WILD], 0)

    # Summe = wild_total, der gesuchte Multiplikator.
    g = _empty_grid()
    for sr, sc in ((0, 0), (0, 1), (2, 2)):
        g[sr][sc]["spaces"][3]["type"] = "WILD"
    expect("Layout: Summe ist wild_total", sum(conj(g)[IDX_WILDSLOT:IDX_WILDSLOT + 9]), 3)

    # Zwei WILD-Spaces in EINEM Slot zaehlen als EINS (Slot-Indikator, nicht
    # Feldzaehler) -- im echten Pool kommt das nicht vor (je Platte hoechstens
    # ein Wild), der Test haelt die Semantik trotzdem fest.
    g = _empty_grid()
    g[0][0]["spaces"][0]["type"] = "WILD"
    g[0][0]["spaces"][1]["type"] = "WILD"
    expect("Layout: zwei Wild in einem Slot = 1", conj(g)[IDX_WILDSLOT], 1)

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
    # encoding explizit: `text=True` allein dekodiert unter Windows mit
    # locale.getpreferredencoding() (cp1252) -- neural_net.py ist UTF-8 mit
    # Umlauten ("tuerkis"), das crasht im Reader-Thread und liefert stdout=None.
    old_src = subprocess.run(["git", "-C", str(REPO), "show", "HEAD:engine/py/neural_net.py"],
                             capture_output=True, text=True, encoding="utf-8",
                             check=True).stdout
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


# ── Suite 3: Engine (die echten Labels gegen den echten Rust-Kern) ─────────
#
# `mosaic_rust.end_scoring_from_state_json(state_json, tile_ids, seed)` ist
# eine bestehende, additive PyO3-Lesefunktion (`engine/src/lib.rs`, Aufruf
# `serialize::end_scoring_from_state`) fuer genau diesen Zweck: Endwertung
# eines EXTERN gespeicherten Zustands, ohne Suche/Produktion zu beruehren.
# `dome_grid` wird laut deren Doku-Kommentar "Space-fuer-Space EXAKT"
# rekonstruiert (`serialize.rs` Zeile 954), bewiesen durch den bestehenden
# Rust-Test `end_scoring_from_state_is_exact_after_roundtrip`. Ein frisches
# `PyGame` liefert das restliche Zustands-Skelett (Beutel/Fabriken/Log/...),
# das fuer die Wertung irrelevant ist -- ausschliesslich `dome_grid` wird pro
# Testbrett ersetzt.

def _engine_empty_grid():
    """3x3-Kuppelraster, JSON-Schema wie `serialize_dome_tile`/`serialize_space`
    (`serialize.rs` Zeile 81-106): jeder Slot ist eine vorhandene, aber leere
    Platte (id/bonus beliebig, hier slot-eindeutig) -- fuer die Wertung
    aequivalent zu einem fehlenden Slot (`None`), aber ohne Sonderfall-Code."""
    return [[{"id": sr * 3 + sc, "bonus": 0,
              "spaces": [{"type": "NORMAL", "color": None, "filled": None, "locked": False}
                         for _ in range(4)]}
             for sc in range(3)] for sr in range(3)]


def _engine_cell(grid, r, c):
    """6x6-Zelle -> Space-Dict, dieselbe Abbildung wie `_cell` oben und
    `DomeGrid::cell_to_dome_space` (`board.rs` Zeile 98)."""
    return grid[r // 2][c // 2]["spaces"][(r % 2) * 2 + (c % 2)]


def _engine_scores(base_state, dome_grid_p0):
    """Endwertung von Spieler 0 fuer alle 6 Kriterien, die `_conjunctions_from_dome`
    abdeckt (0,1,2,3,5,7 -- 4 und 6 NICHT, die deckt `_ownership_from_dome`,
    siehe Docstring dort). `{id: score}`."""
    import copy
    st = copy.deepcopy(base_state)
    st["players"][0]["dome_grid"] = dome_grid_p0
    st["players"][1]["dome_grid"] = _engine_empty_grid()
    raw = mosaic_rust.end_scoring_from_state_json(json.dumps(st), [0, 1, 2, 3, 5, 7], 0)
    result = json.loads(raw)
    return {d["id"]: d["score"] for d in result["player_0"]["details"]}


def _check_engine_board(name, base_state, grid, coverage):
    """Eine Identitaetspruefung: Python-Labels (`_conjunctions_from_dome`, die
    ECHTE, im Training verwendete Funktion) gegen den ECHTEN kompilierten
    Rust-Kern auf demselben konstruierten Brett. `coverage` wird je Label mit
    (gesehen True, gesehen False) aktualisiert -- Grundlage der
    Coverage-Assertion am Ende von `check_engine`."""
    from neural_net import _conjunctions_from_dome

    labels = _conjunctions_from_dome(grid)
    if len(labels) != N_CONJ:
        FAILS.append(f"ENGINE {name}: {len(labels)} Labels statt {N_CONJ}")
        return
    for i, v in enumerate(labels):
        seen_true, seen_false = coverage[i]
        coverage[i] = (seen_true or v == 1, seen_false or v == 0)

    scores = _engine_scores(base_state, grid)
    expect(f"ENGINE {name}: Reihen (3 x Label == score_horizontal_rows)",
           3 * sum(labels[IDX_ROW:IDX_ROW + 6]), scores[0])
    expect(f"ENGINE {name}: Spalten (7 x Label == score_vertical_rows)",
           7 * sum(labels[IDX_COL:IDX_COL + 6]), scores[1])
    expect(f"ENGINE {name}: Diagonalen (10 x Label == score_diagonal_rows)",
           10 * sum(labels[IDX_DIAG:IDX_DIAG + 2]), scores[2])
    expect(f"ENGINE {name}: Eckplatten (3/3/8/8 x Label == score_corner_tiles)",
           sum(labels[IDX_CORNER + i] * CORNER_WEIGHTS[i] for i in range(4)), scores[5])
    expect(f"ENGINE {name}: Farbenreiche Reihen (4 x Label == score_colorful_rows)",
           4 * sum(labels[IDX_COLORFUL:IDX_COLORFUL + 6]), scores[7])
    # Jokerfelder: Label 18 ist "ALLE Jokerfelder belegt". Wenn wahr, muss
    # `score_wild_fields` (id 3) `2 * wild_total` sein -- und `wild_total`
    # ist unabhaengig durch die Engine bestimmt (nicht aus den Testbrettern
    # abgeschrieben): aufgeloest aus `score_wild_fields = 2 * wild_total`
    # dividiert durch das bekannte Label 18. Die Layout-Summe (25..33) muss
    # mit GENAU diesem engine-abgeleiteten `wild_total` uebereinstimmen --
    # das ist die im PREREG geforderte Konsistenzpruefung "Layout vs.
    # wild_total DER ENGINE", nicht nur gegen die eigene Testbrett-Buchhaltung.
    layout_sum = sum(labels[IDX_WILDSLOT:IDX_WILDSLOT + 9])
    if labels[IDX_WILD] == 1:
        expect(f"ENGINE {name}: Jokerfelder (score_wild_fields == 2 x Label18-Summe)",
               scores[3], 2 * layout_sum)
    else:
        expect(f"ENGINE {name}: Jokerfelder (Bedingung falsch -> score_wild_fields == 0)",
               scores[3], 0)


def check_engine() -> None:
    """Suite 3: konstruierte Bretter, jedes der 34 Labels feuert und feuert
    NICHT mindestens einmal (PREREG-Vorgabe: auf echtem Korpus sind 16 der 34
    praktisch konstant 0, eine Pruefung dort waere dort gegenstandslos, wo sie
    gebraucht wird)."""
    g = mosaic_rust.PyGame(("h", "h"), 0, 42)
    base_state = json.loads(g.state_json())
    coverage = [(False, False)] * N_CONJ  # (gesehen True, gesehen False) je Label

    _check_engine_board("EMPTY", base_state, _engine_empty_grid(), coverage)

    # FULL: gesamtes 6x6-Raster gefuellt, 3 Felder davon WILD (Slots (0,0),
    # (1,1), (2,2) -- Layout-Label 25, 29, 33) -- deckt Reihen/Spalten/
    # Diagonalen/Eckplatten/Jokerfelder/Farbreihen komplett als "feuert" ab.
    g_full = _engine_empty_grid()
    for r in range(6):
        for c in range(6):
            _engine_cell(g_full, r, c)["filled"] = ENGINE_COLORS[(r + c) % 5]
    for (r, c) in ((0, 0), (2, 2), (4, 4)):
        _engine_cell(g_full, r, c)["type"] = "WILD"
    _check_engine_board("FULL", base_state, g_full, coverage)

    # LAYOUT_OTHER: Jokerfelder in den 6 Slots, die FULL nicht abdeckt (Label
    # 26,27,28,30,31,32) -- schliesst die Layout-Coverage.
    g_layout = _engine_empty_grid()
    for (r, c) in ((0, 2), (0, 4), (2, 0), (2, 4), (4, 0), (4, 2)):
        _engine_cell(g_layout, r, c)["type"] = "WILD"
        _engine_cell(g_layout, r, c)["filled"] = "blau"
    _check_engine_board("LAYOUT_OTHER", base_state, g_layout, coverage)

    # ROW3: genau eine volle Reihe, nur 2 Farben (nicht farbenreich) -- trennt
    # "Reihe voll" von "Reihe farbenreich".
    g_row3 = _engine_empty_grid()
    for c in range(6):
        _engine_cell(g_row3, 3, c)["filled"] = ENGINE_COLORS[c % 2]
    _check_engine_board("ROW3", base_state, g_row3, coverage)

    # COL5: genau eine volle Spalte.
    g_col5 = _engine_empty_grid()
    for r in range(6):
        _engine_cell(g_col5, r, 5)["filled"] = ENGINE_COLORS[r % 2]
    _check_engine_board("COL5", base_state, g_col5, coverage)

    # Vier isolierte Eckplatten -- EINZELN, damit eine Gewichts-Vertauschung
    # (z.B. (2,0) faelschlich mit +3 statt +8) nicht durch die Summenkonstanz
    # {3,3,8,8} der FULL-Pruefung verdeckt wird.
    for (sr, sc), weight in zip(CORNER_SLOTS, CORNER_WEIGHTS):
        gg = _engine_empty_grid()
        r0, c0 = sr * 2, sc * 2
        for dr in (0, 1):
            for dc in (0, 1):
                _engine_cell(gg, r0 + dr, c0 + dc)["filled"] = "blau"
        _check_engine_board(f"CORNER_{sr}{sc}", base_state, gg, coverage)

    # Diagonalen einzeln (6x6 ist geradzahlig -- Haupt- und Nebendiagonale
    # ueberschneiden sich nirgends, echte Trennung moeglich).
    g_diag_main = _engine_empty_grid()
    for i in range(6):
        _engine_cell(g_diag_main, i, i)["filled"] = ENGINE_COLORS[i % 5]
    _check_engine_board("DIAG_MAIN", base_state, g_diag_main, coverage)

    g_diag_anti = _engine_empty_grid()
    for i in range(6):
        _engine_cell(g_diag_anti, i, 5 - i)["filled"] = ENGINE_COLORS[i % 5]
    _check_engine_board("DIAG_ANTI", base_state, g_diag_anti, coverage)

    # Farbenreich OHNE volle Reihe (5 von 6 Zellen) -- die beiden Kriterien
    # sind unabhaengig lesbar, `row_unique_colors` verlangt keine Vollzeile.
    g_colorful_partial = _engine_empty_grid()
    for c in range(5):
        _engine_cell(g_colorful_partial, 2, c)["filled"] = ENGINE_COLORS[c]
    _check_engine_board("COLORFUL_PARTIAL", base_state, g_colorful_partial, coverage)

    # Jokerfelder vorhanden, aber NICHT alle belegt (Bedingung falsch) --
    # unterscheidet "Label 18 = 0 mangels Bedingung" von "= 0 mangels
    # Jokerfeldern" UND zeigt, dass Layout (25..33) unabhaengig vom
    # Fuellstand ist (ein Slot zaehlt, auch wenn sein Jokerfeld leer ist).
    g_wild_partial = _engine_empty_grid()
    _engine_cell(g_wild_partial, 0, 0)["type"] = "WILD"
    _engine_cell(g_wild_partial, 0, 0)["filled"] = "blau"
    _engine_cell(g_wild_partial, 2, 3)["type"] = "WILD"  # bleibt leer
    _check_engine_board("WILD_PARTIAL", base_state, g_wild_partial, coverage)

    missing = [i for i, (t, f) in enumerate(coverage) if not (t and f)]
    if missing:
        FAILS.append(f"ENGINE Coverage: Label-Indizes ohne beide Zustaende (feuert/feuert nicht): {missing}")
    else:
        print(f"ENGINE: alle {N_CONJ} Labels feuern UND feuern nicht mindestens einmal ueber die Testbretter.")


def main() -> int:
    from neural_net import _conjunctions_from_dome
    print("LABELS ...")
    check_labels(_conjunctions_from_dome)
    print("KOPF ...")
    head_ran = check_head()
    print("ENGINE ...")
    check_engine()

    if FAILS:
        print("\nFEHLGESCHLAGEN:")
        for f in FAILS:
            print("  -", f)
        return 1
    print(f"\nOK -- Labels, ENGINE{' und Kopf' if head_ran else ''} bestanden.")
    print("(c3/c6-9-Atom-Schema, Vorlaeufer dieses 34-Label-Kopfs: "
          "python tools/plate_head_labels.py check)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
