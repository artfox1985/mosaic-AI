# -*- coding: utf-8 -*-
"""
tools/dome_split_diagnosis.py -- TASK B "Zerlegungs-Diagnose" (Nutzer-Auftrag
2026-08-09, AMENDMENT 2026-08-09). Prereg: evaluations/EXTERNAL_REVIEW_2026-
08-08.md, Abschnitte "TASK B -- Zerlegungs-Diagnose" (Punkt 3, urspruengliches
Design) und "TASK B: INSTRUMENT-AMENDMENT" (korrigiertes Design, bindend fuer
den Default-Modus). Beide sind Pflichtlektuere fuer Aenderungen an dieser
Datei.
============================================================================

Fragestellung
-------------
Die Kuppelplatten-Platzierung ist im Suchbaum ZWEISTUFIG zerlegt:
`Action::ChooseDomeSlot` (Kachel+Slot) auf der Wurzelebene, danach
`Action::ChooseDomeRotation` auf Tiefe 1 (siehe engine/src/game.rs::
apply_drafting/drafting_actions, `pending_dome_choice`). Die Gumbel-
Wurzelbreite vergleicht damit NIE vollstaendige (Slot, Rotation)-
Kombinationen -- kostet das etwas?

AMENDMENT (2026-08-09) -- warum es einen zweiten Modus gibt
-------------------------------------------------------------
Die urspruengliche erste Fassung dieses Werkzeugs (jetzt `--mode
isolated-vs-root`) verglich den ZWEISTUFIGEN Zug aus dem UNVERAENDERTEN
Wurzel-Suchaufruf (Wurzel sieht ALLE Zugarten, Gumbel-Top-m schneidet auf
z.B. 16 von 87 Kandidaten) gegen den FLACHEN Zug aus einem kachel-
isolierten Aufruf (Wurzel sieht NUR die Slots dieser einen Kachel, alle
9 von 9 Kandidaten betrachtet, volles Sims-Budget NUR fuer diese Kachel).
Koordinator-Befund (Selbsttest-Daten, `evaluations/dome_split_diagnosis.
json`, Felder `root_num_actions_considered` vs `per_tile_debug`):

| Arm       | Wurzel-Kandidaten | betrachtet | Sims-Budget      |
|-----------|-------------------|------------|------------------|
| zweistufig| 87 (alle Zugarten)| 16 (Gumbel)| 400 gesamt       |
| "flach"   | 9 (1 Kachel)      | 9 (alle)   | 400 JE KACHEL    |

Dieser Vergleich ueberlagert DREI Effekte -- Zerlegung, Wurzelbreite
(16 von 87) und Budget-Konzentration (bis 3x Gesamtbudget bei 3 Kacheln)
-- und schreibt alles der Zerlegung zu. Die Selbsttest-Zahlen (55%
"suboptimal", mittlere Q-Differenz 0,0138) sind daher KEIN Zerlegungs-
Befund; das Argument ist richtungsunabhaengig (haette auch ein 0%-
Ergebnis entwertet). Stuetzender Nebenbefund: 0 von 11 Abweichungen
betrafen die Rotation, alle betrafen Kachel/Slot -- also gerade NICHT
die Grenze, um die es in Task B geht.

Der NEUE Default-Modus (`--mode within-tree`) zieht BEIDE Lesarten aus
DEMSELBEN kachel-isolierten Suchbaum -- Budget und Wurzelbreite sind
damit fuer beide Seiten identisch, nur die AUSWAHLREGEL unterscheidet
sich:
  - zweistufig = `argmax_slot(root_child_q)` (Slot nach seinem EIGENEN,
    marginalen Root-Kind-Q gewaehlt -- exakt das, was die echte Wurzel-
    suche tut, wenn sie einen Slot waehlt, OHNE die Rotation vorher zu
    kennen), DANACH `best_rotation.q` GENAU DIESES Kindes.
  - flach = `argmax` ueber ALLE (Slot, Rotation)-Paare DESSELBEN Baums
    (d.h. `best_rotation.q` ueber ALLE Slot-Kinder, nicht nur das nach
    marginalem Q gewaehlte).
Divergenz heisst dann exakt: ein Slot mit niedrigerem marginalem Q
enthaelt die insgesamt beste Rotation -- das IST die Zerlegungsfrage,
ohne Budget-/Breiten-Konfundierung.

Methodik (beide Modi teilen sich Auswahl + Kachel-Isolation)
--------------------------------------------------------------
1. Auswahl: alle Zustaende aus `evaluations/frozen_eval_set_v2.pkl` mit
   Phase "drafting", mind. einem legalen "choose_dome_slot"-Zug in
   `record["valid_actions"]` (JSON-Name empirisch bestaetigt --
   `engine/src/self_play.rs::action_to_env_dict`/`self_play.rs:240`, exakt
   das Schema, das `frozen_eval_set*.pkl` ueber
   `tools/build_frozen_eval_set.py` einliest). Start-Platzierungs-
   angrenzende Zustaende (mind. ein Spieler `start_placed=false`) werden
   wie in `tools/build_frozen_oracle_labels.py::is_start_adjacent`
   ausgeschlossen.

2. Kachel-Isolation (identisch in beiden Modi, s.u. "Warum kein zweiter
   Suchaufruf..."): fuer JEDE im Zustand angebotene Kuppelplatte wird
   `dome_display` auf GENAU diese eine Kachel gekuerzt und JEDE
   Steinzug-/Bonuschip-Quelle geleert (`factories[*].sun/moon/bonus_chip/
   chip_revealed`, `large_factory.sun/moon`) -- der rekonstruierte
   Zustand hat dann NUR noch die Slot-Kandidaten dieser einen Kachel
   (+ `dome_stack_peek`, siehe Vorbehalte) als Wurzelzuege. EIN
   `net_search_state_json`-Aufruf mit vollem `sims`-Budget gibt dieser
   Kachel das GESAMTE Budget und liefert je Slot-Wurzelkind sowohl sein
   eigenes marginales `mcts_q` als auch (Task #97-Feld) `best_rotation`
   (Rotation + Q des meistbesuchten Rotations-Kindes).

3. `--mode within-tree` (DEFAULT seit dem Amendment): pro Kachel-Baum
   werden beide Lesarten wie oben beschrieben abgeleitet
   (`analyze_tile_tree`). Aggregation auf ZWEI Ebenen (Auftrag Punkt 3):
   (a) JEDE Kachel ist ein eigener Datenpunkt (mehr Datenpunkte, exakt
       gleiche Budget-/Breitenbedingungen je Datenpunkt);
   (b) zusaetzlich die kachel-uebergreifende ("cross-tile") Variante pro
       Zustand: welche Kachel gewinnt nach der zweistufigen Regel
       (max `twostage.q` ueber alle Kacheln-Baeume dieses Zustands)
       gegen welche Kachel nach der flachen Regel (max `flat_best.q`).
   Beide Zahlen werden GETRENNT berichtet, nicht gemittelt.

4. `--mode isolated-vs-root` (LEGACY, weiterhin verfuegbar): unveraendert
   die urspruengliche Fassung -- EIN Wurzel-Suchaufruf auf dem
   UNVERAENDERTEN Zustand bestimmt die zweistufige (Kachel,Slot)-Wahl,
   die kachel-isolierten Aufrufe liefern die flache Vergleichsmenge.
   AUSDRUECKLICH eine BUDGET-/BREITEN-DIAGNOSE (wie stark leidet die
   Slot-Wahl unter Wurzel-Verwaesserung + Sims-Verteilung ueber viele
   Zugarten), KEIN Zerlegungs-Test -- siehe Konfundierungs-Tabelle oben.
   Bleibt erhalten, weil die Frage ("kostet Wurzelbreite/Budget-Teilung
   etwas") fuer sich genommen legitim ist, nur eben eine ANDERE als
   Task B.

Warum kein zweiter Suchaufruf auf dem Post-Slot-Zwischenzustand (gilt
fuer BEIDE Modi -- deshalb die Kachel-Isolation ueberhaupt)
--------------------------------------------------------------
Die urspruengliche Auftragsformulierung beschrieb woertlich: Zustand
durchsuchen, gewaehlten Slot-Zug ANWENDEN, DANACH erneut durchsuchen, um
die Rotation zu erhalten. Das ist mit dem bestehenden Werkzeugkasten
NICHT umsetzbar: `state_to_json` serialisiert `pending_dome_choice`
NICHT (siehe `engine/src/serialize.rs`, Doku-Kommentar ueber
`json_to_state`, Kategorie 3, UND empirisch in `tools/build_frozen_
oracle_labels.py` dokumentiert: 125 von 1329 frozen_v1-Drafting-
Zustaenden sind exakt solche Zwischenzustaende und werden dort
AUSGESCHLOSSEN). Der Zustand "Kachel+Slot gewaehlt, Rotation offen" ist
im Wire-JSON-Format identisch mit dem Zustand DAVOR (die Kachel steht in
`dome_display` noch drin -- `execute_dome_move`, das sie entfernt, laeuft
erst bei `Action::ChooseDomeRotation`, siehe
`engine/src/game.rs::apply_drafting`). Ein zweiter `net_search_state_
json`-Aufruf auf demselben `state_json` wuerde daher NICHT die
Rotationswahl isoliert durchsuchen, sondern schlicht die komplette
Wurzel-Entscheidung ERNEUT treffen. Selbst mit einer LEBENDEN `PyGame`-
Instanz gibt es keinen Python-Ausweg: `apply_dome(tile_id, slot_row,
slot_col, rotation)` ist "nach aussen atomar" (Kommentar in
`tools/analyze_game_log.py`) -- es gibt keine offengelegte Methode, die
NUR die Slot-Wahl anwendet und dort haelt. Die Kachel-Isolation
reproduziert stattdessen, was die echte Partie-Schleife fuer JEDEN
Drafting-Entscheidungspunkt tatsaechlich tut (`engine/src/self_play.rs`
Zeile ~1814-1828 / ~1338-1351: ein EIGENER, frischer Such-Aufruf mit
vollem Sims-Budget je Entscheidungspunkt) -- nur eben ueber ALLE Slots
dieser Kachel gleichzeitig statt nur eine schon gewaehlte Rotation.

Seed-Schema
-----------
`seed = state_seed(record["state"])` -- SHA-256 von `json.dumps(state,
sort_keys=True)`, untere 63 Bit (Muster: `tools/build_frozen_oracle_
labels.py::state_seed`). DERSELBE Seed treibt ALLE kachel-isolierten
Aufrufe desselben Zustands (und, im Legacy-Modus, auch den Wurzel-
Aufruf) -- der Vergleich misst so keine Seed-Rauschen-Differenz.
`net_search_state_json` hat `add_root_noise=false` fest verdrahtet
(lib.rs), ist also bei festem Seed deterministisch; die einzige
Rauschquelle ist die RNG-Neumischung echter verdeckter Information
(Beutel/Turm/Kuppelstapel) in `json_to_state`, die von `dome_display`s
Laenge/Inhalt UNABHAENGIG ist (die Reihenfolge der RNG-Ziehungen haengt
nur an `bag_colors`/`tower_colors`/`dome_pool_mask`, die die Kachel-
Isolation nicht veraendert) -- verschiedene Kacheln DESSELBEN Zustands
sind also bei gleichem Seed hidden-info-konsistent, ueber Kacheln hinweg
vergleichbar.

Design-Entscheidungen, wo die Prereg/der Auftrag offen liess
---------------------------------------------------------------
1. Zwei-Suchaufrufe-Rezept durch Kachel-Isolation ersetzt (s.o.) --
   technisch erzwungen, kein Geschmacksurteil. Gilt fuer beide Modi.
2. Q-Feld-Wahl: `best_rotation.q` (= `node.value/node.visits` des
   Rotations-Kindknotens, Perspektive "Spieler, der den Zug macht" --
   siehe net_mcts.rs `node_own_value`/Backprop-Kommentar:
   `nodes[i].value += value[nodes[i].player_who_acted]`, UND
   `Action::ChooseDomeSlot`/`ChooseDomeRotation` wechseln den Spieler
   NICHT zwischeneinander -- `switch_player()` faellt erst nach der
   Rotation. Slot-Q (Tiefe 1, `mcts_q`) und Rotation-Q (Tiefe 2,
   `best_rotation.q`) sind daher OHNE Vorzeichenwechsel direkt
   vergleichbar.
3. `root_chose_non_dome`-Faelle (Legacy-Modus) bzw. keine Entsprechung
   noetig im within-tree-Modus (der gar keinen Wurzel-Aufruf mehr macht,
   s.u. Konfundierung 1) -- ausgeschlossen aus der Kern-Metrik, siehe
   Legacy-Docstring-Abschnitt oben.
4. "Suboptimal" ist WERT-basiert definiert (`q_diff > EPS`), nicht
   Tupel-Identitaet -- konsistent mit den Q-Differenz-Kennzahlen.
5. Kachel-Isolation leert Steinzug-/Bonuschip-Quellen, laesst aber
   `dome_stack_peek` (Kuppelstapel-Zug, EIGENE, hier bewusst NICHT
   untersuchte Mehrstufen-Zerlegung) als Wurzel-Konkurrenten stehen.
   Kostet etwas Budget-Anteil (identisch fuer beide Lesarten IM SELBEN
   Baum -- siehe Konfundierung 3 unten), aendert aber nichts an der
   Kern-Eigenschaft (Slots dieser EINEN Kachel bekommen weiterhin
   erheblich mehr Budget als im unveraenderten Zustand).
6. Slots ohne aufgeloeste `best_rotation` werden als "unscored" gezaehlt
   (Deckungsgrad wird berichtet). Ist der nach marginalem Q beste Slot
   selbst unscored, ist die Kachel (within-tree) bzw. der Zustand
   (Legacy) fuer die Kern-Metrik nicht auswertbar.

VERBLEIBENDE KONFUNDIERUNGEN im within-tree-Design (Antwort auf die
Koordinator-Frage "welche Konfundierung faellt beim Bauen noch auf")
---------------------------------------------------------------------
1. **`best_rotation` ist "meistbesucht", nicht "hoechstes Q"**
   (`net_mcts.rs`: `max_by_key(|(gnode, _)| gnode.visits)`, NICHT
   `max_by_key(q)`). Unter Sequential Halving konvergieren Besuche
   typischerweise zum hoechsten Q, aber NICHT garantiert -- bei
   niedrigen Besuchszahlen (im Selbsttest teils nur 8-9) kann die
   gemeldete "beste" Rotation eine andere sein als die tatsaechlich
   hoechst bewertete. Das betrifft BEIDE Lesarten gleich (dieselbe
   Zahl wird fuer zweistufig UND flach gelesen, wenn derselbe Slot
   gewinnt) -- also keine SYSTEMATISCHE Verzerrung ZWISCHEN den
   Lesarten, aber eine Rausch-/Genauigkeitsgrenze auf beiden Seiten.
2. **Direkte Konsequenz von (1): "rotation_only"-Divergenz ist unter
   dieser Metrik-Definition STRUKTURELL UNMESSBAR.** Sobald derselbe
   Slot gewinnt, wird fuer zweistufig UND flach dieselbe `best_rotation`
   gelesen -- es gibt keine zweite, unabhaengige "flache Rotationswahl"
   fuer denselben Slot. Divergenz kann nach dieser Definition NUR als
   Slot-Wechsel auftreten. Ein `n_rotation_only == 0` im Bericht ist
   daher KEIN empirischer Befund, sondern eine GARANTIE der
   Metrik-Konstruktion -- um "richtiger Slot, falsche Rotation"
   tatsaechlich zu pruefen, braeuchte es Zugriff auf ALLE (nicht nur
   die meistbesuchte) Rotations-Kandidaten je Slot, was die aktuelle
   `net_search_state_json`-Ausgabe nicht liefert (Engine-Aenderung
   noetig, hier bewusst nicht vorgenommen).
3. `dome_stack_peek` bleibt Wurzel-Konkurrent in JEDEM Kachel-Baum
   (Design-Entscheidung 5) -- verkleinert das effektive Slot-Budget
   etwas, GLEICH fuer beide Lesarten desselben Baums, erhoeht also nur
   das Rauschen (weniger Sims je Slot/Rotation), keine Asymmetrie.
4. Die kachel-uebergreifende ("cross-tile") Aggregation vergleicht
   Q-Werte aus VERSCHIEDENEN Suchbaeumen (je Kachel ein eigener Baum) --
   das setzt voraus, dass der Netz-Q-Massstab ueber verschiedene,
   unabhaengig durchsuchte Teilbaeume hinweg vergleichbar ist. Dieselbe
   Annahme steckte schon im Legacy-Design und in praktisch jedem
   Q-Vergleich dieses Projekts; kein NEUES Risiko, aber nicht durch das
   Amendment beseitigt.

Randbedingungen dieses Laufs
-----------------------------
Ein-Thread-Nutzung (kein Multiprocessing/Threading in diesem Skript).

Nutzung
-------
    python tools/dome_split_diagnosis.py --limit 30                       # within-tree (Default)
    python tools/dome_split_diagnosis.py --mode within-tree --limit 200
    python tools/dome_split_diagnosis.py --mode isolated-vs-root --limit 200
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
DEFAULT_MODE = "within-tree"

# Bestehende (Legacy-Modus-)Ausgabedateien -- NICHT anfassen/ueberschreiben
# ausser bei explizitem --mode isolated-vs-root-Lauf (deren natuerlicher,
# unveraenderter Default-Pfad). Der within-tree-Modus schreibt unter einem
# ANDEREN Namen (Koordinator-Vorgabe 2026-08-09: alte Datei ist als
# Budget-/Breiten-Diagnose committet, nicht ueberschreiben).
OUT_MD_LEGACY = ROOT / "evaluations" / "dome_split_diagnosis.md"
OUT_JSON_LEGACY = ROOT / "evaluations" / "artifacts" / "dome_split_diagnosis.json"
OUT_MD_WITHINTREE = ROOT / "evaluations" / "dome_split_diagnosis_withintree.md"
OUT_JSON_WITHINTREE = ROOT / "evaluations" / "artifacts" / "dome_split_diagnosis_withintree.json"

# Lesart-Schwellen woertlich aus der Prereg (EXTERNAL_REVIEW_2026-08-08.md,
# TASK B, unveraendert durch das Amendment): Anteil <5% ODER mittlere
# Q-Differenz <0,01 -> Zerlegung kostet nichts Messbares. NUR zum Berichten,
# nicht zum Selbst-Entscheiden. Im Legacy-Modus NICHT auf die Task-B-Frage
# anwendbar (Budget-/Breiten-Diagnose, s. Moduldoku) -- wird dort trotzdem
# ausgerechnet (Transparenz), aber mit deutlichem Disclaimer berichtet.
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
    Entscheidung 5 / Konfundierung 3)."""
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
    """Extrahiert alle 'choose_dome_slot'-Wurzelkinder aus EINEM Such-
    Ergebnis -- liefert je Eintrag {slot_row, slot_col, marginal_q, rotation,
    q, visits, scored}. `marginal_q` = `mcts_q` des Wurzelkindes selbst
    (Slot-Ebene, Tiefe 1); `q`/`rotation` = `best_rotation` (Rotation-Ebene,
    Tiefe 2, `None` falls die Suche dort nicht vertieft hat)."""
    out = []
    for m in moves:
        if m.get("type") != "choose_dome_slot":
            continue
        br = m.get("best_rotation")
        act = m.get("action") or {}
        entry = {
            "slot_row": act.get("slot_row"),
            "slot_col": act.get("slot_col"),
            "marginal_q": m.get("mcts_q"),
            "rotation": br.get("rotation") if br else None,
            "q": br.get("q") if br else None,
            "visits": br.get("visits") if br else None,
            "scored": br is not None,
        }
        out.append(entry)
    return out


# ── within-tree: Kern je Kachel-Baum ────────────────────────────────────────

def analyze_tile_tree(iso_result: dict) -> dict:
    """Leitet aus EINEM kachel-isolierten Suchergebnis beide Lesarten ab
    (Amendment-Design, s. Moduldoku):
      zweistufig = argmax_slot(marginal_q) -> best_rotation.q GENAU dieses
                   Wurzelkindes.
      flach      = argmax ueber ALLE Slots' best_rotation.q IM SELBEN Baum.
    Status: 'no_legal_slots' | 'twostage_rotation_unresolved' | 'ok'."""
    entries = dome_slot_entries(iso_result.get("moves", []))
    n_legal = len(entries)
    n_scored = sum(1 for e in entries if e["scored"])
    if not entries:
        return {"status": "no_legal_slots", "n_legal": 0, "n_scored": 0, "entries": entries}

    twostage_entry = max(entries, key=lambda e: (e["marginal_q"] if e["marginal_q"] is not None else float("-inf")))
    if not twostage_entry["scored"]:
        return {
            "status": "twostage_rotation_unresolved",
            "n_legal": n_legal, "n_scored": n_scored, "entries": entries,
        }

    scored_entries = [e for e in entries if e["scored"]]
    flat_entry = max(scored_entries, key=lambda e: e["q"])

    q_twostage = twostage_entry["q"]
    q_flat = flat_entry["q"]
    q_diff = q_flat - q_twostage
    same_slot = (twostage_entry["slot_row"], twostage_entry["slot_col"]) == \
                (flat_entry["slot_row"], flat_entry["slot_col"])
    is_suboptimal = q_diff > EPS

    return {
        "status": "ok",
        "n_legal": n_legal, "n_scored": n_scored,
        "twostage": {
            "slot_row": twostage_entry["slot_row"], "slot_col": twostage_entry["slot_col"],
            "rotation": twostage_entry["rotation"], "q": q_twostage,
            "marginal_q": twostage_entry["marginal_q"],
        },
        "flat_best": {
            "slot_row": flat_entry["slot_row"], "slot_col": flat_entry["slot_col"],
            "rotation": flat_entry["rotation"], "q": q_flat,
        },
        "q_diff": q_diff,
        "is_suboptimal": is_suboptimal,
        # s. "VERBLEIBENDE KONFUNDIERUNGEN" Punkt 2 -- 'rotation_only' ist
        # unter dieser Metrik strukturell nie erreichbar (same_slot=True
        # impliziert q_diff==0, da beide Seiten dieselbe best_rotation
        # lesen), bleibt im Code stehen, um das explizit sichtbar/pruefbar
        # zu machen statt es stillschweigend anzunehmen.
        "divergence_kind": (None if not is_suboptimal else ("rotation_only" if same_slot else "slot")),
    }


def process_record_within_tree(idx: int, rec: dict, model_path: str, sims: int, c_puct: float) -> dict:
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

    tile_results = []
    for tile in state["dome_display"]:
        tile_id = tile.get("id")
        iso_state = isolate_tile_state(state, tile)
        iso_result = run_search(iso_state, model_path, sims, c_puct, seed)
        tr = analyze_tile_tree(iso_result)
        tr["tile_id"] = tile_id
        tr["iso_num_actions"] = iso_result.get("num_actions")
        tr["iso_num_actions_considered"] = iso_result.get("num_actions_considered")
        tile_results.append(tr)
    result["tile_results"] = tile_results

    ok_tiles = [t for t in tile_results if t["status"] == "ok"]
    if not ok_tiles:
        result["cross_tile"] = {"status": "no_ok_tiles"}
        result["status"] = "no_ok_tiles"
        return result

    best_by_twostage = max(ok_tiles, key=lambda t: t["twostage"]["q"])
    best_by_flat = max(ok_tiles, key=lambda t: t["flat_best"]["q"])
    q_twostage_cross = best_by_twostage["twostage"]["q"]
    q_flat_cross = best_by_flat["flat_best"]["q"]
    q_diff_cross = q_flat_cross - q_twostage_cross
    same_combo_cross = (
        best_by_twostage["tile_id"] == best_by_flat["tile_id"]
        and best_by_twostage["twostage"]["slot_row"] == best_by_flat["flat_best"]["slot_row"]
        and best_by_twostage["twostage"]["slot_col"] == best_by_flat["flat_best"]["slot_col"]
    )
    is_suboptimal_cross = q_diff_cross > EPS
    result["cross_tile"] = {
        "status": "ok",
        "twostage_tile_id": best_by_twostage["tile_id"],
        "twostage_combo": dict(best_by_twostage["twostage"]),
        "flat_tile_id": best_by_flat["tile_id"],
        "flat_best_combo": dict(best_by_flat["flat_best"]),
        "q_diff": q_diff_cross,
        "is_suboptimal": is_suboptimal_cross,
        "divergence_kind": (None if not is_suboptimal_cross else
                             ("rotation_only" if same_combo_cross else "slot")),
    }
    result["status"] = "ok"
    return result


# ── isolated-vs-root: Legacy-Modus (Budget-/Breiten-Diagnose) ──────────────

def process_record_isolated_vs_root(idx: int, rec: dict, model_path: str, sims: int, c_puct: float) -> dict:
    """LEGACY (`--mode isolated-vs-root`). Unveraendert gegenueber der
    urspruenglichen Fassung -- siehe Moduldoku fuer die Konfundierungs-
    Tabelle, die diesen Modus zu einer Budget-/Breiten- statt Zerlegungs-
    Diagnose macht."""
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
    result["divergence_kind"] = ("rotation_only" if same_slot else "slot") if is_suboptimal else None
    return result


# ── Aggregations-Helfer ──────────────────────────────────────────────────────

def _agg_stats(items: list[dict]) -> dict:
    """Gemeinsamer Kennzahlen-Block (Anteil suboptimal, mittlere/maximale
    Q-Differenz, rotation_only vs slot) fuer eine Liste von Dicts mit
    `is_suboptimal`/`q_diff`/`divergence_kind`."""
    n = len(items)
    n_sub = sum(1 for it in items if it["is_suboptimal"])
    share = (n_sub / n) if n else float("nan")
    diffs = [it["q_diff"] for it in items]
    mean_diff = (sum(diffs) / n) if n else float("nan")
    max_diff = max(diffs) if diffs else float("nan")
    n_rot = sum(1 for it in items if it.get("divergence_kind") == "rotation_only")
    n_slot = sum(1 for it in items if it.get("divergence_kind") == "slot")
    return {
        "n": n, "n_suboptimal": n_sub, "share_suboptimal": share,
        "mean_q_diff": mean_diff, "max_q_diff": max_diff,
        "n_rotation_only": n_rot, "n_slot": n_slot,
    }


def _reading(stats: dict) -> str:
    if stats["n"] == 0:
        return "Keine auswertbaren Datenpunkte (n=0) -- keine Lesart moeglich."
    if stats["share_suboptimal"] < READING_SHARE_THRESHOLD or stats["mean_q_diff"] < READING_MEAN_DIFF_THRESHOLD:
        return ("Anteil < 5% ODER mittlere Q-Differenz < 0,01 erfuellt -> laut Prereg "
                "kostet die Zerlegung nichts Messbares. NUR Bericht, keine Selbst-Entscheidung.")
    return ("Weder Anteil < 5% noch mittlere Q-Differenz < 0,01 erfuellt -> laut Prereg "
            "waere eine faktorierte Policy/Action-Attention ein begruendeter Kandidat "
            "(eigenes Prereg, Architektur-Kostenklasse). NUR Bericht, keine Selbst-Entscheidung.")


def _md_header(meta: dict, scan_stats: dict, n_total: int, title: str, subtitle: str) -> list[str]:
    md = [f"# {title}\n", f"{subtitle}\n"]
    md.append("## Lauf-Parameter\n")
    md.append(f"- Modus: `{meta['mode']}`")
    md.append(f"- Frozen-Set: `{meta['frozen_set']}` (Version `{scan_stats.get('frozen_version')}`, "
               f"{scan_stats['n_frozen_records_total']} Records gesamt)")
    md.append(f"- Modell: `{meta['model_path']}`")
    md.append(f"- Sims/Kachel-Baum: {meta['sims']} | c_puct: {meta['c_puct']} (Legacy-Durchreiche, "
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
    return md


def _md_stats_block(title: str, stats: dict) -> list[str]:
    md = [f"### {title}\n"]
    md.append(f"- n (auswertbar) = **{stats['n']}**")
    if stats["n"]:
        md.append(f"- Anteil suboptimal (wertbasiert, epsilon={EPS:g}): "
                   f"**{stats['n_suboptimal']}/{stats['n']} = {stats['share_suboptimal']*100:.2f}%**")
        md.append(f"- mittlere Q-Differenz (flach minus zweistufig): **{stats['mean_q_diff']:.6f}**")
        md.append(f"- maximale Q-Differenz: **{stats['max_q_diff']:.6f}**")
        md.append(f"- davon nur Rotation falsch (struktur. immer 0, s. Konfundierung 2): {stats['n_rotation_only']}")
        md.append(f"- davon Slot/Kachel falsch: {stats['n_slot']}")
    else:
        md.append("- (keine Datenpunkte)")
    md.append(f"- Lesart: {_reading(stats)}\n")
    return md


# ── Report: within-tree ──────────────────────────────────────────────────────

def build_report_within_tree(results: list[dict], scan_stats: dict, meta: dict) -> tuple[str, dict]:
    n_total = len(results)

    all_tiles = [t for r in results for t in r["tile_results"]]
    n_tiles_total = len(all_tiles)
    tile_status_counts: dict[str, int] = {}
    for t in all_tiles:
        tile_status_counts[t["status"]] = tile_status_counts.get(t["status"], 0) + 1
    ok_tiles = [t for t in all_tiles if t["status"] == "ok"]
    tile_stats = _agg_stats(ok_tiles)
    tile_coverage = [min(1.0, t["n_scored"] / t["n_legal"]) for t in all_tiles if t.get("n_legal")]
    mean_tile_coverage = (sum(tile_coverage) / len(tile_coverage)) if tile_coverage else float("nan")

    state_status_counts: dict[str, int] = {}
    for r in results:
        state_status_counts[r["status"]] = state_status_counts.get(r["status"], 0) + 1
    ok_states_cross = [r["cross_tile"] for r in results if r["cross_tile"]["status"] == "ok"]
    cross_stats = _agg_stats(ok_states_cross)

    json_out = {
        "manifest": {
            **meta,
            "scan_stats": scan_stats,
            "n_selected_states": n_total,
            "n_states_by_status": state_status_counts,
            "n_tiles_total": n_tiles_total,
            "n_tiles_by_status": tile_status_counts,
            "mean_tile_coverage_ratio": mean_tile_coverage,
            "per_tile_datapoint_stats": tile_stats,
            "cross_tile_stats": cross_stats,
            "reading_thresholds": {
                "share_threshold": READING_SHARE_THRESHOLD,
                "mean_diff_threshold": READING_MEAN_DIFF_THRESHOLD,
            },
            "reading_per_tile": _reading(tile_stats),
            "reading_cross_tile": _reading(cross_stats),
        },
        "results": results,
    }

    md = _md_header(
        meta, scan_stats, n_total,
        "Zerlegungs-Diagnose: within-tree (TASK B, korrigiertes Design)",
        "Prereg: `evaluations/EXTERNAL_REVIEW_2026-08-08.md`, Abschnitt "
        '"TASK B: INSTRUMENT-AMENDMENT". Beide Lesarten (zweistufig/flach) '
        "kommen aus DEMSELBEN kachel-isolierten Suchbaum -- Budget und "
        "Wurzelbreite sind identisch, siehe Moduldoku von "
        "`tools/dome_split_diagnosis.py`.",
    )

    md.append("## Kachel-Status-Verteilung\n")
    md.append("| Status | n Kacheln |")
    md.append("|---|---|")
    for status, n in sorted(tile_status_counts.items(), key=lambda kv: -kv[1]):
        md.append(f"| {status} | {n} |")
    md.append(f"\nMittlere Deckung (Slots mit >=1 bewerteter Rotation, gekappt bei 1.0): "
               f"{mean_tile_coverage*100:.1f}%\n")

    md.append("## Aggregation (a): jede Kachel ein Datenpunkt (mehr Datenpunkte)\n")
    md.extend(_md_stats_block(f"n_tiles_total={n_tiles_total}, davon `ok`", tile_stats))

    md.append("## Aggregation (b): kachel-uebergreifend je Zustand (\"cross-tile\")\n")
    md.append("| Status | n Zustaende |")
    md.append("|---|---|")
    for status, n in sorted(state_status_counts.items(), key=lambda kv: -kv[1]):
        md.append(f"| {status} | {n} |")
    md.append("")
    md.extend(_md_stats_block(f"n_selected_states={n_total}, davon cross_tile `ok`", cross_stats))

    md.append("## Verbleibende Konfundierungen (siehe Moduldoku fuer Details)\n")
    md.append("1. `best_rotation` ist die MEISTBESUCHTE, nicht die hoechst bewertete Rotation "
               "(`net_mcts.rs`: `max_by_key(visits)`) -- Rauschgrenze auf BEIDEN Lesarten gleich, "
               "keine Asymmetrie zwischen ihnen.")
    md.append("2. Direkte Folge von (1): `n_rotation_only` ist unter dieser Metrik-Definition "
               "STRUKTURELL immer 0 (Beleg, keine Ueberraschung) -- sobald derselbe Slot gewinnt, "
               "lesen beide Seiten dieselbe `best_rotation`. Echte Rotation-Suboptimalitaet "
               "(richtiger Slot, aber nicht die Q-hoechste Rotation) ist mit der aktuellen "
               "`net_search_state_json`-Ausgabe nicht messbar.")
    md.append("3. `dome_stack_peek` bleibt Wurzel-Konkurrent in jedem Kachel-Baum -- verkleinert das "
               "Slot-Budget etwas, gleich fuer beide Lesarten desselben Baums (Rauschen, keine Verzerrung).")
    md.append("4. Die kachel-uebergreifende Aggregation (b) vergleicht Q-Werte aus VERSCHIEDENEN "
               "Suchbaeumen -- setzt Massstabs-Vergleichbarkeit voraus (bestehende Annahme, nicht neu "
               "durch dieses Amendment).\n")
    return "\n".join(md), json_out


# ── Report: isolated-vs-root (Legacy) ───────────────────────────────────────

def build_report_isolated_vs_root(results: list[dict], scan_stats: dict, meta: dict) -> tuple[str, dict]:
    n_total = len(results)
    by_status: dict[str, int] = {}
    for r in results:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1

    core = [r for r in results if r["status"] == "ok"]
    stats = _agg_stats(core)

    coverage_ratios = []
    for r in results:
        if r.get("n_legal_dome_slot_actions") and r.get("n_flat_combos_scored") is not None:
            coverage_ratios.append(min(1.0, r["n_flat_combos_scored"] / r["n_legal_dome_slot_actions"]))
    mean_coverage = (sum(coverage_ratios) / len(coverage_ratios)) if coverage_ratios else float("nan")

    json_out = {
        "manifest": {
            **meta,
            "scan_stats": scan_stats,
            "n_selected": n_total,
            "n_by_status": by_status,
            "mean_flat_coverage_ratio": mean_coverage,
            "stats": stats,
            "reading_thresholds": {
                "share_threshold": READING_SHARE_THRESHOLD,
                "mean_diff_threshold": READING_MEAN_DIFF_THRESHOLD,
            },
            "reading": _reading(stats),
            "DISCLAIMER": "BUDGET-/BREITEN-DIAGNOSE, KEIN Zerlegungs-Test -- s. Moduldoku "
                           "Konfundierungs-Tabelle (Wurzelbreite 16/87 vs 9/9, Budget 400 gesamt vs "
                           "400 je Kachel). Fuer die Task-B-Frage --mode within-tree verwenden.",
        },
        "results": results,
    }

    md = _md_header(
        meta, scan_stats, n_total,
        "Zerlegungs-Diagnose: isolated-vs-root (LEGACY -- Budget-/Breiten-Diagnose)",
        "**ACHTUNG: Dies ist KEIN Zerlegungs-Test fuer TASK B.** Der zweistufige Arm "
        "kommt aus dem UNVERAENDERTEN Wurzel-Suchaufruf (Gumbel-Top-m schneidet die "
        "betrachteten Kandidaten, z.B. 16 von 87), der flache Arm aus einem "
        "kachel-isolierten Aufruf (alle Kandidaten betrachtet, volles Budget NUR fuer "
        "diese Kachel). Der Vergleich ueberlagert Zerlegung, Wurzelbreite UND Budget-"
        "Konzentration und attribuiert alles der Zerlegung -- siehe "
        '`evaluations/EXTERNAL_REVIEW_2026-08-08.md`, Abschnitt "TASK B: INSTRUMENT-'
        'AMENDMENT". Fuer die eigentliche Zerlegungsfrage `--mode within-tree` (Default) '
        "verwenden.",
    )

    md.append("## Status-Verteilung (alle ausgewaehlten Zustaende)\n")
    md.append("| Status | n |")
    md.append("|---|---|")
    for status, n in sorted(by_status.items(), key=lambda kv: -kv[1]):
        md.append(f"| {status} | {n} |")
    md.append("")
    md.extend(_md_stats_block(f"n_selected={n_total}, davon `ok`", stats))
    md.append(f"Mittlere Deckung der flachen Enumeration (n_scored/n_legal, gekappt bei 1.0): "
               f"{mean_coverage*100:.1f}%\n")
    md.append("**Diese Zahlen duerfen NICHT als Task-B-Ergebnis zitiert werden (s. Disclaimer oben).**\n")
    return "\n".join(md), json_out


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", choices=["within-tree", "isolated-vs-root"], default=DEFAULT_MODE)
    ap.add_argument("--frozen-set", default=str(DEFAULT_FROZEN_SET))
    ap.add_argument("--model", default=None, help="Pfad oder Versionsname (Default: models/champion.txt)")
    ap.add_argument("--sims", type=int, default=DEFAULT_SIMS)
    ap.add_argument("--c-puct", type=float, default=DEFAULT_C_PUCT)
    ap.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    ap.add_argument("--out-md", default=None, help="Default haengt von --mode ab (s. Moduldoku)")
    ap.add_argument("--out-json", default=None)
    args = ap.parse_args()

    frozen_path = Path(args.frozen_set)
    if not frozen_path.is_absolute():
        frozen_path = ROOT / frozen_path
    if not frozen_path.exists():
        raise SystemExit(f"Frozen-Set nicht gefunden: {frozen_path}")

    model_path = resolve_model_path(args.model)
    print(f"Modus: {args.mode}")
    print(f"Frozen-Set: {frozen_path}")
    print(f"Modell: {model_path}")
    print(f"Sims={args.sims} c_puct={args.c_puct} Limit={args.limit}\n")

    eligible, scan_stats = load_eligible_records(frozen_path, args.limit)
    print(f"Ausgewaehlte Zustaende (choose_dome_slot legal, bis --limit): {len(eligible)}")
    print(f"  ({scan_stats})\n")

    process_fn = process_record_within_tree if args.mode == "within-tree" else process_record_isolated_vs_root

    results = []
    t0 = time.time()
    for i, (idx, rec) in enumerate(eligible):
        r = process_fn(idx, rec, model_path, args.sims, args.c_puct)
        results.append(r)
        if (i + 1) % 10 == 0 or (i + 1) == len(eligible):
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed if elapsed > 0 else 0.0
            eta = (len(eligible) - (i + 1)) / rate if rate > 0 else float("nan")
            print(f"  [{i + 1}/{len(eligible)}] elapsed={elapsed:.0f}s rate={rate:.2f}/s "
                  f"eta={eta:.0f}s status={r['status']}", flush=True)
    elapsed_seconds = time.time() - t0

    meta = {
        "mode": args.mode,
        "frozen_set": str(frozen_path.relative_to(ROOT)).replace("\\", "/"),
        "model_path": str(Path(model_path).relative_to(ROOT)).replace("\\", "/")
        if Path(model_path).is_relative_to(ROOT) else model_path,
        "sims": args.sims,
        "c_puct": args.c_puct,
        "limit": args.limit,
        "elapsed_seconds": elapsed_seconds,
        "git_commit": _git_commit(),
        "seed_scheme": "SHA-256(json.dumps(state, sort_keys=True))[:8 bytes], big-endian, & 0x7FFFFFFFFFFFFFFF "
                       "(tools/build_frozen_oracle_labels.py-Muster); derselbe Seed treibt alle "
                       "kachel-isolierten Aufrufe desselben Zustands.",
    }

    if args.mode == "within-tree":
        md_text, json_out = build_report_within_tree(results, scan_stats, meta)
        default_out_md, default_out_json = OUT_MD_WITHINTREE, OUT_JSON_WITHINTREE
    else:
        md_text, json_out = build_report_isolated_vs_root(results, scan_stats, meta)
        default_out_md, default_out_json = OUT_MD_LEGACY, OUT_JSON_LEGACY

    out_md = Path(args.out_md) if args.out_md else default_out_md
    out_json = Path(args.out_json) if args.out_json else default_out_json
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(md_text, encoding="utf-8")
    out_json.write_text(json.dumps(json_out, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nFertig in {elapsed_seconds:.0f}s ({elapsed_seconds/60:.1f} min).")
    print(f"Bericht: {out_md}")
    print(f"JSON: {out_json}")
    if args.mode == "within-tree":
        print(f"\nLesart (pro Kachel): {json_out['manifest']['reading_per_tile']}")
        print(f"Lesart (cross-tile): {json_out['manifest']['reading_cross_tile']}")
    else:
        print(f"\n{json_out['manifest']['reading']}")
        print("ACHTUNG: Budget-/Breiten-Diagnose, kein Zerlegungs-Test (s. Disclaimer im Bericht).")


if __name__ == "__main__":
    main()
