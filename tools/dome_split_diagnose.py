# -*- coding: utf-8 -*-
"""
tools/dome_split_diagnose.py -- TASK B "Zerlegungs-Diagnose" (Nutzer-Auftrag
2026-08-09). Prereg: evaluations/EXTERNES_REVIEW_2026-08-08.md, Abschnitt
"TASK B -- Zerlegungs-Diagnose" (bindend) + Punkt 3 desselben Dokuments
(Kontext/Herleitung der Frage).
============================================================================

Fragestellung
-------------
Die Kuppelplatten-Platzierung ist im Suchbaum ZWEISTUFIG zerlegt:
`Action::ChooseDomeSlot` (Kachel+Slot) auf der Wurzelebene, danach
`Action::ChooseDomeRotation` auf Tiefe 1 (siehe engine/src/game.rs::
apply_drafting/drafting_actions, `pending_dome_choice`). Die Gumbel-
Wurzelbreite vergleicht damit NIE vollstaendige (Slot, Rotation)-
Kombinationen -- kostet das etwas? Bisher ungemessen.

Methodik
--------
1. Auswahl: alle Zustaende aus `evaluations/frozen_eval_set_v2.pkl` mit
   Phase "drafting", mind. einem legalen "choose_dome_slot"-Zug in
   `record["valid_actions"]` (JSON-Name empirisch bestaetigt --
   `engine/src/self_play.rs::action_to_env_dict`/`self_play.rs:240`, exakt
   das Schema, das `frozen_eval_set*.pkl` ueber
   `tools/build_frozen_eval_set.py` einliest). Start-Platzierungs-
   angrenzende Zustaende (mind. ein Spieler `start_placed=false`) werden
   wie in `tools/build_frozen_oracle_labels.py::is_start_adjacent`
   ausgeschlossen (`net_search_state_json` setzt eine abgeschlossene
   Start-Platzierung voraus, siehe dortige Doku).

2. ZWEISTUFIG (was die reale Suche tatsaechlich spielt): EIN
   `mosaic_rust.net_search_state_json(state_json, model, sims, c_puct,
   seed)`-Aufruf auf dem UNVERAENDERTEN Zustand. Ist die gewaehlte
   Wurzel-Aktion (`moves[i]["chosen"]`) selbst ein "choose_dome_slot"-Zug,
   ist (Kachel, Slot) damit bestimmt.

3. Rotation des zweistufigen Zugs + FLACHE Enumeration ALLER (Slot,
   Rotation)-Kombinationen: siehe "Warum kein zweiter Suchaufruf auf
   demselben Zustand" unten -- beides wird stattdessen ueber denselben
   Mechanismus gelesen: fuer JEDE im Zustand angebotene Kuppelplatte wird
   `dome_display` auf GENAU diese eine Kachel gekuerzt und JEDE
   Steinzug-/Bonuschip-Quelle geleert (`factories[*].sun/moon/bonus_chip/
   chip_revealed`, `large_factory.sun/moon`) -- der rekonstruierte Zustand
   hat dann NUR noch die Slot-Kandidaten dieser einen Kachel (+ optional
   `dome_stack_peek`, siehe Vorbehalte) als Wurzelzuege. EIN
   `net_search_state_json`-Aufruf mit demselben `sims`-Budget wie oben
   gibt dieser Kachel damit das GESAMTE Budget (kein Verwaesserungs-
   Wettbewerb mit anderen Kacheln/Steinzuegen) -- ausreichend, um fuer
   JEDEN Slot dieser Kachel eine Rotation zu explorieren
   (`moves[i]["best_rotation"]`, Task #97-Feld, siehe net_mcts.rs).
   Diese EINE Suche pro Kachel liefert damit ALLE (Slot, Rotation)-
   Kombinationen dieser Kachel gleichzeitig (kein Aufruf pro Kombination
   noetig). Die Vereinigung ueber alle Kacheln des Zustands = die flache
   Kombinationsmenge. Die zweistufige Kombination ist darin ENTHALTEN
   (derselbe Slot, aus dem GLEICHEN Kachel-isolierten Aufruf) -- die
   flach-beste Kombination ist per Konstruktion >= der zweistufigen.

Warum kein zweiter Suchaufruf auf demselben Zustand (Abweichung von der
Auftragsformulierung, s.u. Design-Entscheidung 1)
--------------------------------------------------
Der Auftrag beschreibt woertlich: Zustand durchsuchen, gewaehlten
Slot-Zug ANWENDEN, DANACH erneut durchsuchen, um die Rotation zu
erhalten. Das ist mit dem bestehenden Werkzeugkasten NICHT umsetzbar:
`state_to_json` serialisiert `pending_dome_choice` NICHT (siehe
`engine/src/serialize.rs`, Doku-Kommentar ueber `json_to_state`,
Kategorie 3, UND empirisch in `tools/build_frozen_oracle_labels.py`
dokumentiert: 125 von 1329 frozen_v1-Drafting-Zustaenden sind exakt
solche Zwischenzustaende und werden dort AUSGESCHLOSSEN). Der Zustand
"Kachel+Slot gewaehlt, Rotation offen" ist im Wire-JSON-Format identisch
mit dem Zustand DAVOR (die Kachel steht in `dome_display` noch drin --
`execute_dome_move`, das sie entfernt, laeuft erst bei
`Action::ChooseDomeRotation`, siehe `engine/src/game.rs::apply_drafting`).
Ein zweiter `net_search_state_json`-Aufruf auf demselben `state_json`
wuerde daher NICHT die Rotationswahl isoliert durchsuchen, sondern
schlicht die komplette Wurzel-Entscheidung ERNEUT treffen (moeglicherweise
mit einem GANZ ANDEREN Zug). Selbst mit einer LEBENDEN `PyGame`-Instanz
gibt es keinen Python-Ausweg: `apply_dome(tile_id, slot_row, slot_col,
rotation)` ist "nach aussen atomar" (Kommentar in
`tools/analyze_game_log.py`) -- es gibt keine offengelegte Methode, die
NUR die Slot-Wahl anwendet und dort haelt. `tools/analyze_game_log.py`
dokumentiert dieselbe Einschraenkung und weicht ihr aus, indem es die
Rotations-Zwischenstufe schlicht NICHT oracle-bewertet. Diese Datei
weicht ihr aus, indem sie die Rotation stattdessen aus GENAU DER SUCHE
liest, die (in echten Partien) tatsaechlich dafuer zustaendig ist: einer
FRISCHEN, NICHT mit anderen Wurzelkandidaten geteilten Suche (siehe
`engine/src/self_play.rs` Zeile ~1814-1828 / ~1338-1351: JEDER
Drafting-Entscheidungspunkt -- auch die Rotationswahl -- bekommt in der
echten Partie-Schleife einen EIGENEN, frischen `net_search_drafting_
action`-Aufruf mit vollem Sims-Budget, nicht anteilig vom Slot-Aufruf
"vererbt"). Die Kachel-Isolation oben reproduziert genau das: volles
Budget, nur eben ueber ALLE Slots dieser Kachel gleichzeitig statt nur
die eine schon gewaehlte Rotation -- eine Verschaerfung, keine
Verwaesserung, gegenueber der Auftragsformulierung.

Seed-Schema
-----------
`seed = state_seed(record["state"])` -- SHA-256 von `json.dumps(state,
sort_keys=True)`, untere 63 Bit (Muster: `tools/build_frozen_oracle_
labels.py::state_seed`). DERSELBE Seed treibt den Wurzel-Aufruf UND ALLE
Kachel-isolierten Aufruefe desselben Zustands (Auftragsvorgabe: "dieselbe
Seed-Ableitung", damit der Vergleich nicht Seed-Rauschen misst).
`net_search_state_json` hat `add_root_noise=false` fest verdrahtet
(lib.rs), ist also bei festem Seed deterministisch -- die einzige
Rauschquelle ist die RNG-Neumischung echter verdeckter Information
(Beutel/Turm/Kuppelstapel) in `json_to_state`, die bei gleichem Seed
gleich ausfaellt.

Design-Entscheidungen, wo die Prereg offen liess
-------------------------------------------------
1. Zwei-Suchaufrufe-Rezept durch Kachel-Isolation ersetzt (s.o.) --
   technisch erzwungen, kein Geschmacksurteil.
2. Q-Feld-Wahl: `best_rotation.q` (= `node.value/node.visits` des
   Rotations-Kindknotens, Perspektive "Spieler, der den Zug macht" --
   siehe net_mcts.rs `node_own_value`/Backprop-Kommentar:
   `nodes[i].value += value[nodes[i].player_who_acted]`, UND
   `Action::ChooseDomeSlot`/`ChooseDomeRotation` wechseln den Spieler
   NICHT zwischeneinander, siehe `game.rs::apply_drafting` --
   `switch_player()` faellt erst nach der Rotation. Slot-Q (Tiefe 1) und
   Rotation-Q (Tiefe 2) sind also OHNE Vorzeichenwechsel direkt
   vergleichbar, keine Perspektivumrechnung noetig.
   NICHT verwendet: `root_value`/`win_pct` der "Folgestellung" (der im
   Auftrag als Beispiel genannte Weg) -- das wuerde ENTWEDER die exakte
   Platzierungsmechanik (Rotation, Zellenbelegung, Kuppelbrett-Update)
   in Python nachbauen (Korrektheitsrisiko, siehe CLAUDE.md
   "Zustandsverwaltung muss immer validiert werden") ODER eine lebende
   `PyGame`-Instanz voraussetzen, die es fuer beliebige Frozen-Set-
   Zustaende nicht gibt (kein Konstruktor fuer beliebige JSON-Zustaende,
   siehe `tools/net_tiling_tiebreak_cost.py`-Doku). `best_rotation.q`
   ist bereits eine vom Engine-Code selbst berechnete, korrekte
   Wurzelkind-Bewertung -- kein Nachbau noetig.
3. Zustaende, an denen die zweistufige Suche an der Wurzel GAR KEINEN
   Kuppelzug waehlt (Stein/Bonuschip/Stapel bevorzugt), werden aus der
   KERN-Metrik ausgeschlossen (separat gezaehlt als
   `n_excluded_root_not_dome`) -- es gibt dort keine (Slot,Rotation)-
   Kombination zu vergleichen; ein Vergleich "Q(Stein) vs. flach-bester
   Kuppelzug" waere eine andere Frage (Kuppel- vs. Stein-Attraktivitaet),
   nicht die hier gestellte Zerlegungsfrage.
4. "Suboptimal" ist WERT-basiert definiert (`q_flat_best - q_twostage >
   EPS`), nicht Tupel-Identitaet -- ein Gleichstand mit anderer
   Tupel-Identitaet zaehlt NICHT als suboptimal (sonst waere die
   mittlere/maximale Q-Differenz inkonsistent mit dem Anteils-Kriterium).
5. Kachel-Isolation leert Steinzug-/Bonuschip-Quellen, laesst aber
   `dome_stack_peek` (Kuppelstapel-Zug, EIGENE, hier bewusst NICHT
   untersuchte Mehrstufen-Zerlegung -- Action::ChooseDrawStackSlot/
   DrawStackPeek) als Wurzel-Konkurrenten stehen. Kostet etwas Budget-
   Anteil, aendert aber nichts an der Schluessel-Eigenschaft (jede
   Kachel-Slot-Kombination dieser EINEN Kachel bekommt weiterhin
   erheblich mehr Budget als im unveraenderten Zustand).
6. Rotationen, die selbst im kachel-isolierten Aufruf keine
   `best_rotation` bekommen (Suche vertieft trotz vollem Budget nicht
   bis Tiefe 2 -- selten, aber moeglich bei vielen offenen Slots frueh
   im Spiel), werden als "unscored" gezaehlt und NICHT in die flache
   Kandidatenmenge aufgenommen (Deckungsgrad wird im Bericht
   ausgewiesen). Bleibt fuer den gewaehlten Zweistufer-Slot ebenfalls
   unscored, wird der ganze Zustand aus der Kern-Metrik ausgeschlossen
   (`n_excluded_rotation_unresolved`).

Randbedingungen dieses Laufs
-----------------------------
Ein-Thread-Nutzung (kein Multiprocessing/Threading in diesem Skript --
was die Rust-Seite pro `net_search_state_json`-Aufruf intern tut, ist
davon unabhaengig und liegt ausserhalb der Kontrolle dieses Skripts,
dieselbe Situation wie bei jedem anderen *_state_json-Werkzeug).

Nutzung
-------
    python tools/dome_split_diagnose.py --limit 50
    python tools/dome_split_diagnose.py --limit 200 --sims 400
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pickle
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import mosaic_rust  # noqa: E402

EPS = 1e-9

DEFAULT_FROZEN_SET = ROOT / "evaluations" / "frozen_eval_set_v2.pkl"
DEFAULT_SIMS = 400
DEFAULT_C_PUCT = 1.5  # Legacy-Durchreiche -- USE_GUMBEL_SEARCH=true (net_mcts.rs), c_puct
                      # ist im Gumbel-Wurzelpfad kein aktiver PUCT-Term mehr.
DEFAULT_LIMIT = 200
OUT_MD = ROOT / "evaluations" / "dome_split_diagnose.md"
OUT_JSON = ROOT / "evaluations" / "dome_split_diagnose.json"

# Lesart-Schwellen woertlich aus der Prereg (EXTERNES_REVIEW_2026-08-08.md,
# TASK B): Anteil <5% ODER mittlere Q-Differenz <0,01 -> Zerlegung kostet
# nichts Messbares. NUR zum Berichten, nicht zum Selbst-Entscheiden.
READING_SHARE_THRESHOLD = 0.05
READING_MEAN_DIFF_THRESHOLD = 0.01


# ── Modellpfad (Muster: tools/arena.py::_champion_model_path) ───────────────

def champion_model_path(fallback: str = "v18_best") -> str:
    """Identische Logik/Quelle wie tools/arena.py -- Champion-ONNX aus
    models/champion.txt (Memory: 'Check existing tools first')."""
    name = fallback
    try:
        cand = (ROOT / "models" / "champion.txt").read_text(encoding="utf-8").strip()
        if cand:
            name = cand
    except Exception:
        pass
    p = ROOT / "models" / f"alphazero_{name}.onnx"
    if not p.exists():
        raise FileNotFoundError(
            f"Champion-ONNX fehlt: {p} (champion.txt -> {name!r}). Kein stiller "
            f"Fallback -- models/ pruefen oder --model explizit angeben.")
    return str(p)


def resolve_model_path(spec: str | None) -> str:
    if spec is None:
        return champion_model_path()
    p = Path(spec)
    if p.is_file():
        return str(p)
    p2 = ROOT / spec
    if p2.is_file():
        return str(p2)
    p3 = ROOT / "models" / spec
    if p3.is_file():
        return str(p3)
    p4 = ROOT / "models" / f"alphazero_{spec}.onnx"
    if p4.is_file():
        return str(p4)
    raise FileNotFoundError(f"Modell nicht gefunden fuer --model {spec!r} (probiert: {p}, {p2}, {p3}, {p4}).")


# ── Seed (Muster: tools/build_frozen_oracle_labels.py::state_seed) ─────────

def state_seed(state: dict) -> int:
    h = hashlib.sha256(json.dumps(state, sort_keys=True, ensure_ascii=True).encode("utf-8")).digest()
    return int.from_bytes(h[:8], "big") & 0x7FFFFFFFFFFFFFFF


def _git_commit() -> str | None:
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, timeout=10)
        return out.stdout.strip() if out.returncode == 0 else None
    except Exception:
        return None


# ── Auswahl der Zustaende ───────────────────────────────────────────────────

def is_start_adjacent(state: dict) -> bool:
    """Wie tools/build_frozen_oracle_labels.py::is_start_adjacent --
    net_search_state_json setzt eine abgeschlossene Start-Kuppel-Platzierung
    voraus (apply_drafting lehnt sonst hart ab, siehe game.rs)."""
    return any(not p["start_placed"] for p in state["players"])


def has_dome_slot_move(valid_actions: list) -> bool:
    return any(a.get("type") == "choose_dome_slot" for a in valid_actions)


def load_eligible_records(pkl_path: Path, limit: int):
    with open(pkl_path, "rb") as fh:
        frozen = pickle.load(fh)
    records = frozen["records"]
    eligible = []
    n_non_drafting = 0
    n_start_adjacent = 0
    n_no_dome_move = 0
    for idx, rec in enumerate(records):
        state = rec["state"]
        if state.get("phase") != "drafting":
            n_non_drafting += 1
            continue
        if is_start_adjacent(state):
            n_start_adjacent += 1
            continue
        if not has_dome_slot_move(rec["valid_actions"]):
            n_no_dome_move += 1
            continue
        eligible.append((idx, rec))
        if len(eligible) >= limit:
            break
    scan_stats = {
        "n_frozen_records_total": len(records),
        "n_non_drafting_skipped": n_non_drafting,
        "n_start_adjacent_skipped": n_start_adjacent,
        "n_no_dome_move_skipped": n_no_dome_move,
        "frozen_version": frozen.get("version"),
    }
    return eligible, scan_stats


# ── Suchaufrufe ──────────────────────────────────────────────────────────────

def run_search(state: dict, model_path: str, sims: int, c_puct: float, seed: int) -> dict:
    out = mosaic_rust.net_search_state_json(json.dumps(state), model_path, sims, c_puct, seed)
    return json.loads(out)


def isolate_tile_state(state: dict, tile: dict) -> dict:
    """Kuerzt `dome_display` auf GENAU `tile` und leert alle Steinzug-/
    Bonuschip-Quellen (siehe Moduldoku, Abschnitt "Warum kein zweiter
    Suchaufruf..."). `dome_stack_peek` bleibt bewusst stehen (Design-
    Entscheidung 5)."""
    s = copy.deepcopy(state)
    s["dome_display"] = [tile]
    for f in s["factories"]:
        f["sun"] = []
        f["moon"] = []
        f["bonus_chip"] = None
        f["chip_revealed"] = False
    s["large_factory"]["sun"] = []
    s["large_factory"]["moon"] = []
    return s


def dome_slot_entries(moves: list) -> list[dict]:
    """Extrahiert alle 'choose_dome_slot'-Wurzelkinder mit AUFGELOESTER
    Rotation (`best_rotation` nicht null) aus einem Such-Ergebnis --
    liefert je Eintrag {slot_row, slot_col, rotation, q, visits}."""
    out = []
    for m in moves:
        if m.get("type") != "choose_dome_slot":
            continue
        br = m.get("best_rotation")
        act = m.get("action") or {}
        entry = {
            "slot_row": act.get("slot_row"),
            "slot_col": act.get("slot_col"),
            "rotation": br.get("rotation") if br else None,
            "q": br.get("q") if br else None,
            "visits": br.get("visits") if br else None,
            "scored": br is not None,
        }
        out.append(entry)
    return out


# ── Kern: ein Zustand ────────────────────────────────────────────────────────

def process_record(idx: int, rec: dict, model_path: str, sims: int, c_puct: float) -> dict:
    state = rec["state"]
    seed = state_seed(state)
    n_legal_dome_slot = sum(1 for a in rec["valid_actions"] if a.get("type") == "choose_dome_slot")

    result: dict = {
        "record_index": idx,
        "round": rec.get("round"),
        "seed": seed,
        "n_legal_dome_slot_actions": n_legal_dome_slot,
        "n_dome_display_tiles": len(state["dome_display"]),
    }

    root = run_search(state, model_path, sims, c_puct, seed)
    root_moves = root.get("moves", [])
    chosen = next((m for m in root_moves if m.get("chosen")), None)
    result["root_num_actions"] = root.get("num_actions")
    result["root_num_actions_considered"] = root.get("num_actions_considered")
    result["root_chosen_type"] = chosen.get("type") if chosen else None

    if chosen is None or chosen.get("type") != "choose_dome_slot":
        result["status"] = "root_chose_non_dome"
        return result

    chosen_action = chosen.get("action") or {}
    chosen_display_index = chosen_action.get("display_index")
    chosen_slot = (chosen_action.get("slot_row"), chosen_action.get("slot_col"))
    try:
        chosen_tile = state["dome_display"][chosen_display_index]
    except (TypeError, IndexError):
        result["status"] = "chosen_display_index_out_of_range"
        return result
    chosen_tile_id = chosen_tile.get("id")

    # Kachel-isolierte Suche je Kachel im Display (Design-Entscheidung 1/2).
    all_combos = []  # [(tile_id, slot_row, slot_col, rotation, q)]
    n_scored_total = 0
    per_tile_debug = []
    twostage_q = None
    twostage_rotation = None

    for tile in state["dome_display"]:
        tile_id = tile.get("id")
        iso_state = isolate_tile_state(state, tile)
        iso_result = run_search(iso_state, model_path, sims, c_puct, seed)
        entries = dome_slot_entries(iso_result.get("moves", []))
        per_tile_debug.append({
            "tile_id": tile_id,
            "iso_num_actions": iso_result.get("num_actions"),
            "iso_num_actions_considered": iso_result.get("num_actions_considered"),
            "n_entries": len(entries),
            "n_scored": sum(1 for e in entries if e["scored"]),
        })
        for e in entries:
            if not e["scored"]:
                continue
            n_scored_total += 1
            all_combos.append((tile_id, e["slot_row"], e["slot_col"], e["rotation"], e["q"]))
            if tile_id == chosen_tile_id and (e["slot_row"], e["slot_col"]) == chosen_slot:
                twostage_q = e["q"]
                twostage_rotation = e["rotation"]

    result["per_tile_debug"] = per_tile_debug
    result["n_flat_combos_scored"] = n_scored_total
    result["twostage_combo"] = {
        "tile_id": chosen_tile_id,
        "slot_row": chosen_slot[0],
        "slot_col": chosen_slot[1],
    }

    if twostage_q is None:
        result["status"] = "twostage_rotation_unresolved"
        return result

    result["twostage_combo"]["rotation"] = twostage_rotation
    result["twostage_combo"]["q"] = twostage_q

    if not all_combos:
        result["status"] = "no_flat_combos_scored"
        return result

    flat_tile, flat_row, flat_col, flat_rot, flat_q = max(all_combos, key=lambda c: c[4])
    q_diff = flat_q - twostage_q
    same_slot = (flat_tile == chosen_tile_id) and (flat_row == chosen_slot[0]) and (flat_col == chosen_slot[1])
    is_suboptimal = q_diff > EPS

    result["status"] = "ok"
    result["flat_best_combo"] = {
        "tile_id": flat_tile, "slot_row": flat_row, "slot_col": flat_col,
        "rotation": flat_rot, "q": flat_q,
    }
    result["q_diff"] = q_diff
    result["is_suboptimal"] = is_suboptimal
    if is_suboptimal:
        result["divergence_kind"] = "rotation_only" if same_slot else "slot"
    else:
        result["divergence_kind"] = None
    return result


# ── Report ───────────────────────────────────────────────────────────────────

def build_report(results: list[dict], scan_stats: dict, meta: dict) -> tuple[str, dict]:
    n_total = len(results)
    by_status: dict[str, int] = {}
    for r in results:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1

    core = [r for r in results if r["status"] == "ok"]
    n_core = len(core)
    n_suboptimal = sum(1 for r in core if r["is_suboptimal"])
    share_suboptimal = (n_suboptimal / n_core) if n_core else float("nan")
    diffs = [r["q_diff"] for r in core]
    mean_diff = (sum(diffs) / n_core) if n_core else float("nan")
    max_diff = max(diffs) if diffs else float("nan")
    n_rotation_only = sum(1 for r in core if r.get("divergence_kind") == "rotation_only")
    n_slot = sum(1 for r in core if r.get("divergence_kind") == "slot")

    coverage_ratios = []
    for r in results:
        if r.get("n_legal_dome_slot_actions") and r.get("n_flat_combos_scored") is not None:
            coverage_ratios.append(min(1.0, r["n_flat_combos_scored"] / r["n_legal_dome_slot_actions"]))
    mean_coverage = (sum(coverage_ratios) / len(coverage_ratios)) if coverage_ratios else float("nan")

    if n_core == 0:
        reading = "Keine auswertbaren Zustaende (n_core=0) -- keine Lesart moeglich."
    elif share_suboptimal < READING_SHARE_THRESHOLD or mean_diff < READING_MEAN_DIFF_THRESHOLD:
        reading = ("Anteil < 5% ODER mittlere Q-Differenz < 0,01 erfuellt -> laut Prereg "
                   "kostet die Zerlegung nichts Messbares (Punkt 3 des Reviews waere mit "
                   "Beleg geschlossen). NUR Bericht, keine Selbst-Entscheidung.")
    else:
        reading = ("Weder Anteil < 5% noch mittlere Q-Differenz < 0,01 erfuellt -> laut Prereg "
                   "wuerde eine faktorierte Policy/Action-Attention ein begruendeter Kandidat "
                   "(eigenes Prereg, Architektur-Kostenklasse). NUR Bericht, keine "
                   "Selbst-Entscheidung.")

    json_out = {
        "manifest": {
            **meta,
            "scan_stats": scan_stats,
            "n_selected": n_total,
            "n_by_status": by_status,
            "n_core": n_core,
            "n_suboptimal": n_suboptimal,
            "share_suboptimal": share_suboptimal,
            "mean_q_diff": mean_diff,
            "max_q_diff": max_diff,
            "n_divergence_rotation_only": n_rotation_only,
            "n_divergence_slot": n_slot,
            "mean_flat_coverage_ratio": mean_coverage,
            "reading_thresholds": {
                "share_threshold": READING_SHARE_THRESHOLD,
                "mean_diff_threshold": READING_MEAN_DIFF_THRESHOLD,
            },
            "reading": reading,
        },
        "results": results,
    }

    md = []
    md.append("# Zerlegungs-Diagnose: ChooseDomeSlot / ChooseDomeRotation (TASK B)\n")
    md.append(f"Prereg: `evaluations/EXTERNES_REVIEW_2026-08-08.md`, Abschnitt "
               f"\"TASK B -- Zerlegungs-Diagnose\" (Punkt 3). Werkzeug: "
               f"`tools/dome_split_diagnose.py`.\n")
    md.append("## Lauf-Parameter\n")
    md.append(f"- Frozen-Set: `{meta['frozen_set']}` (Version `{scan_stats.get('frozen_version')}`, "
               f"{scan_stats['n_frozen_records_total']} Records gesamt)")
    md.append(f"- Modell: `{meta['model_path']}`")
    md.append(f"- Sims/Zustand: {meta['sims']} | c_puct: {meta['c_puct']} (Legacy-Durchreiche, "
               f"USE_GUMBEL_SEARCH=true)")
    md.append(f"- Limit: {meta['limit']} | ausgewaehlte Zustaende: {n_total}")
    md.append(f"- Laufzeit: {meta['elapsed_seconds']:.1f}s ({meta['elapsed_seconds']/60:.1f} min)")
    md.append(f"- Git-Commit: `{meta.get('git_commit')}`\n")
    md.append("## Auswahl-Trichter\n")
    md.append(f"- Frozen-Records gesamt: {scan_stats['n_frozen_records_total']}")
    md.append(f"- nicht Phase=drafting (uebersprungen): {scan_stats['n_non_drafting_skipped']}")
    md.append(f"- Start-Platzierung ausstehend (uebersprungen): {scan_stats['n_start_adjacent_skipped']}")
    md.append(f"- kein choose_dome_slot legal (uebersprungen): {scan_stats['n_no_dome_move_skipped']}")
    md.append(f"- eligible (choose_dome_slot legal, ausgewertet bis --limit): {n_total}\n")
    md.append("## Status-Verteilung (alle ausgewaehlten Zustaende)\n")
    md.append("| Status | n |")
    md.append("|---|---|")
    for status, n in sorted(by_status.items(), key=lambda kv: -kv[1]):
        md.append(f"| {status} | {n} |")
    md.append("")
    md.append("## Kern-Kennzahlen (nur `status=ok`)\n")
    md.append(f"- n (auswertbar) = **{n_core}** von {n_total} ausgewaehlten Zustaenden")
    md.append(f"- Anteil suboptimal (zweistufig != flach-beste Kombination, wertbasiert, "
               f"epsilon={EPS:g}): **{n_suboptimal}/{n_core} = "
               f"{share_suboptimal*100:.2f}%**" if n_core else "- Anteil suboptimal: n/a")
    md.append(f"- mittlere Q-Differenz (flach-best minus zweistufig): **{mean_diff:.6f}**"
               if n_core else "- mittlere Q-Differenz: n/a")
    md.append(f"- maximale Q-Differenz: **{max_diff:.6f}**" if n_core else "- maximale Q-Differenz: n/a")
    md.append(f"- davon nur Rotation falsch (gleiche Kachel+Slot): {n_rotation_only}")
    md.append(f"- davon Slot falsch (andere Kachel oder Slot): {n_slot}")
    md.append(f"- mittlere Deckung der flachen Enumeration (n_scored/n_legal, gekappt bei 1.0): "
               f"{mean_coverage*100:.1f}%\n")
    md.append("## Lesart (woertlich aus der Prereg, NUR Bericht)\n")
    md.append(f"> {reading}\n")
    md.append("## Vorbehalte (siehe Moduldoku fuer die volle Begruendung)\n")
    md.append("1. Kein zweiter Suchaufruf auf dem Post-Slot-Zwischenzustand (nicht "
               "serialisierbar, `pending_dome_choice` ist nicht Teil des Wire-Formats) -- "
               "stattdessen Kachel-isolierte volle Suche pro Kachel im Display.")
    md.append("2. Q-Feld = `best_rotation.q` (Wurzelkind-Wert, dieselbe Spielerperspektive "
               "wie die Slot-Entscheidung, kein Vorzeichenwechsel).")
    md.append("3. Zustaende, in denen die zweistufige Suche an der Wurzel gar keinen "
               "Kuppelzug waehlt, sind aus der Kern-Metrik ausgeschlossen (Status "
               "`root_chose_non_dome`, s. Tabelle oben).")
    md.append("4. `dome_stack_peek` bleibt in den kachel-isolierten Aufrufen als "
               "Wurzel-Konkurrent stehen (eigene, hier nicht untersuchte Zerlegung).")
    md.append("5. Deckungsgrad der flachen Enumeration ist NICHT 100% garantiert (s. "
               "mittlere Deckung oben) -- Zustaende ohne aufgeloeste Zweistufer-Rotation "
               "sind separat gezaehlt (`twostage_rotation_unresolved`).\n")
    return "\n".join(md), json_out


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--frozen-set", default=str(DEFAULT_FROZEN_SET))
    ap.add_argument("--model", default=None, help="Pfad oder Versionsname (Default: models/champion.txt)")
    ap.add_argument("--sims", type=int, default=DEFAULT_SIMS)
    ap.add_argument("--c-puct", type=float, default=DEFAULT_C_PUCT)
    ap.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    ap.add_argument("--out-md", default=str(OUT_MD))
    ap.add_argument("--out-json", default=str(OUT_JSON))
    args = ap.parse_args()

    frozen_path = Path(args.frozen_set)
    if not frozen_path.is_absolute():
        frozen_path = ROOT / frozen_path
    if not frozen_path.exists():
        raise SystemExit(f"Frozen-Set nicht gefunden: {frozen_path}")

    model_path = resolve_model_path(args.model)
    print(f"Frozen-Set: {frozen_path}")
    print(f"Modell: {model_path}")
    print(f"Sims={args.sims} c_puct={args.c_puct} Limit={args.limit}\n")

    eligible, scan_stats = load_eligible_records(frozen_path, args.limit)
    print(f"Ausgewaehlte Zustaende (choose_dome_slot legal, bis --limit): {len(eligible)}")
    print(f"  ({scan_stats})\n")

    results = []
    t0 = time.time()
    for i, (idx, rec) in enumerate(eligible):
        r = process_record(idx, rec, model_path, args.sims, args.c_puct)
        results.append(r)
        if (i + 1) % 10 == 0 or (i + 1) == len(eligible):
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed if elapsed > 0 else 0.0
            eta = (len(eligible) - (i + 1)) / rate if rate > 0 else float("nan")
            print(f"  [{i + 1}/{len(eligible)}] elapsed={elapsed:.0f}s rate={rate:.2f}/s "
                  f"eta={eta:.0f}s status={r['status']}", flush=True)
    elapsed_seconds = time.time() - t0

    meta = {
        "frozen_set": str(frozen_path.relative_to(ROOT)).replace("\\", "/"),
        "model_path": str(Path(model_path).relative_to(ROOT)).replace("\\", "/")
        if Path(model_path).is_relative_to(ROOT) else model_path,
        "sims": args.sims,
        "c_puct": args.c_puct,
        "limit": args.limit,
        "elapsed_seconds": elapsed_seconds,
        "git_commit": _git_commit(),
        "seed_scheme": "SHA-256(json.dumps(state, sort_keys=True))[:8 bytes], big-endian, & 0x7FFFFFFFFFFFFFFF "
                       "(tools/build_frozen_oracle_labels.py-Muster); derselbe Seed treibt Wurzel- UND "
                       "alle kachel-isolierten Aufrufe desselben Zustands.",
    }

    md_text, json_out = build_report(results, scan_stats, meta)

    out_md = Path(args.out_md)
    out_json = Path(args.out_json)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(md_text, encoding="utf-8")
    out_json.write_text(json.dumps(json_out, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nFertig in {elapsed_seconds:.0f}s ({elapsed_seconds/60:.1f} min).")
    print(f"Bericht: {out_md}")
    print(f"JSON: {out_json}")
    print(f"\n{json_out['manifest']['reading']}")


if __name__ == "__main__":
    main()
