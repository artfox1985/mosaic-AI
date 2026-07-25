"""
tools/build_frozen_oracle_labels.py -- Task #89 Teil B, Schritt 1: Oracle-Labels
fuer evaluations/frozen_eval_set.pkl per tiefer v16_best-Netzsuche.

Voraussetzung (Teil A, abgeschlossen): engine/src/serialize.rs::json_to_state
(Umkehrung von state_to_json) + die neue PyO3-Funktion
mosaic_rust.net_search_state_json(state_json, model_path, sims, c_puct, seed)
-- siehe deren Doku-Kommentare fuer die Rekonstruktions-Details.

Scope-Einschraenkung (empirisch verifiziert, nicht geraten):
frozen_eval_set.pkl hat 1800 Records, davon:
  - 1329 mit state["phase"] == "drafting" (die einzige Phase, die
    net_search_with_tree ueberhaupt unterstuetzt -- Tiling/Scoring/etc.
    liefern strukturell IMMER ein leeres Ergebnis, das ist bestehendes
    Verhalten von net_search_with_tree selbst, keine Rekonstruktionsluecke).
  - Davon 19 "start-placement-angrenzend" (mind. ein Spieler mit
    start_placed=false): das Startkuppel-Legen laeuft NIE ueber die
    Netz-/PUCT-Suche (siehe py.rs::ai_start_tile_json -- reine Heuristik,
    self_play.rs::choose_start_placement), daher ist net_search_state_json
    hierfuer nicht das richtige Werkzeug (kein Fehler, schlicht ausserhalb
    des Suchumfangs).
  - Davon (nach Ausschluss der start-placement-Faelle) 125 Zustaende, bei
    denen valid_actions AUSSCHLIESSLICH aus "choose_dome_rotation"-Eintraegen
    besteht -- das sind die im json_to_state-Doku-Kommentar (Kategorie 3)
    dokumentierten PendingDomeChoice-Zwischenzustaende: state_to_json
    serialisiert `pending_dome_choice` nicht, die Rekonstruktion sieht daher
    faelschlich die VOLLE Drafting-Aktionsmenge statt nur die Rotationswahl.
  - Verbleiben 1185 "saubere" Drafting-Zustaende. Auf einer Stichprobe von
    80 dieser 1185 zeigte ein Kreuz-Check (Anzahl rekonstruierter
    Wurzelkandidaten vs. `len(record["valid_actions"])`, dem am echten
    Spielzustand VOR jeder JSON-Serialisierung erzeugten Referenzwert) 0
    Abweichungen -- die Rekonstruktion ist fuer diese Teilmenge nachweislich
    exakt (Wurzel-Aktionslegalitaet).

Sicherheitsnetz: JEDER Zustand wird beim echten 5000-Sim-Lauf zusaetzlich
gegen `len(record["valid_actions"])` geprueft (kostet nichts extra, num_actions
kommt im selben Suchergebnis mit) -- bei Abweichung wird der Zustand trotzdem
gelabelt, aber `root_candidates_mismatch=true` markiert (transparent, nicht
stillschweigend verworfen).

Seed-Schema (dokumentiert, deterministisch je Zustand): seed = die unteren
63 Bit von SHA-256(json.dumps(state, sort_keys=True)) -- stabil unter
Wiederholung, unabhaengig von der Position im Set.

Ablage: evaluations/frozen_v1_oracle_labels.json (+ Metadaten). NACH
Fertigstellung laut Auftrag UNVERAENDERLICH (wie frozen_eval_set.pkl selbst).

Laeuft sequenziell mit Fortschritts-Log (Prozess-Disziplin: kein Multi-
Processing noetig, ~1-2s/Zustand bei 5000 Sims -> geschaetzt ~25-35 Min
fuer 1185 Zustaende, siehe Timing-Messung im Task-Bericht).
"""
import hashlib
import json
import pickle
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import mosaic_rust  # noqa: E402

FROZEN_PKL = ROOT / "evaluations" / "frozen_eval_set.pkl"
OUT_JSON = ROOT / "evaluations" / "frozen_v1_oracle_labels.json"
MODEL_PATH = ROOT / "models" / "alphazero_v16_best.onnx"
SIMS = 5000
C_PUCT = 1.5


def _git_commit() -> str | None:
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, timeout=10)
        return out.stdout.strip() if out.returncode == 0 else None
    except Exception:
        return None


def state_seed(state: dict) -> int:
    """Deterministischer Seed je Zustand -- SHA-256 des kanonischen
    (schluessel-sortierten) JSON, untere 63 Bit (passt sicher in ein
    vorzeichenbehaftetes i64 auf der Rust-Seite)."""
    h = hashlib.sha256(json.dumps(state, sort_keys=True, ensure_ascii=True).encode("utf-8")).digest()
    return int.from_bytes(h[:8], "big") & 0x7FFFFFFFFFFFFFFF


def is_start_adjacent(rec: dict) -> bool:
    return any(not p["start_placed"] for p in rec["state"]["players"])


def is_pending_rotation(rec: dict) -> bool:
    types = set(a.get("type") for a in rec["valid_actions"])
    return types == {"choose_dome_rotation"}


def main() -> None:
    print(f"Lade {FROZEN_PKL} ...")
    with open(FROZEN_PKL, "rb") as fh:
        frozen = pickle.load(fh)
    records = frozen["records"]
    print(f"  {len(records)} Records insgesamt (frozen-Version {frozen.get('version')})")

    eligible = []
    n_non_drafting = 0
    n_start_adjacent = 0
    n_pending_rotation = 0
    for idx, rec in enumerate(records):
        if rec["state"].get("phase") != "drafting":
            n_non_drafting += 1
            continue
        if is_start_adjacent(rec):
            n_start_adjacent += 1
            continue
        if is_pending_rotation(rec):
            n_pending_rotation += 1
            continue
        eligible.append((idx, rec))

    print(f"  non-drafting: {n_non_drafting}")
    print(f"  start-placement-angrenzend (ausgeschlossen): {n_start_adjacent}")
    print(f"  PendingDomeChoice-Zwischenzustaende (ausgeschlossen): {n_pending_rotation}")
    print(f"  verbleiben (Oracle-Kandidaten): {len(eligible)}")

    labels = []
    t_start = time.time()
    n_mismatch = 0
    n_error = 0
    for i, (idx, rec) in enumerate(eligible):
        state = rec["state"]
        seed = state_seed(state)
        state_json = json.dumps(state)
        try:
            out = mosaic_rust.net_search_state_json(state_json, str(MODEL_PATH), SIMS, C_PUCT, seed)
            result = json.loads(out)
        except Exception as e:  # pragma: no cover -- defensiv, sollte bei "sauberen" Zustaenden nicht passieren
            n_error += 1
            print(f"  [FEHLER] record #{idx} (Runde {rec['round']}): {e}", flush=True)
            continue

        recorded_n = len(rec["valid_actions"])
        searched_n = result.get("num_actions")
        mismatch = recorded_n != searched_n
        if mismatch:
            n_mismatch += 1

        moves = result.get("moves", [])
        best = next((m for m in moves if m.get("chosen")), None)

        labels.append({
            "record_index": idx,
            "round": rec["round"],
            "source_corpus": rec.get("source_corpus"),
            "source_file": rec.get("source_file"),
            "seed": seed,
            "sims": SIMS,
            "root_value": result.get("root_value"),
            "num_actions": searched_n,
            "num_actions_considered": result.get("num_actions_considered"),
            "recorded_valid_actions_len": recorded_n,
            "root_candidates_mismatch": mismatch,
            "ai_action": result.get("ai_action"),
            "best_move": best,
            "moves": moves,
        })

        if (i + 1) % 25 == 0 or (i + 1) == len(eligible):
            elapsed = time.time() - t_start
            rate = (i + 1) / elapsed if elapsed > 0 else 0.0
            eta = (len(eligible) - (i + 1)) / rate if rate > 0 else float("nan")
            print(
                f"  [{i + 1}/{len(eligible)}] elapsed={elapsed:.0f}s rate={rate:.2f}/s "
                f"eta={eta:.0f}s mismatches={n_mismatch} errors={n_error}",
                flush=True,
            )

    total_elapsed = time.time() - t_start
    print(f"\nFertig: {len(labels)} Labels erzeugt in {total_elapsed:.0f}s "
          f"({total_elapsed/60:.1f} min), {n_mismatch} Mismatches, {n_error} Fehler.")

    manifest = {
        "version": "frozen_v1_oracle_v1",
        "based_on_frozen_version": frozen.get("version"),
        "build_date_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit(),
        "model": str(MODEL_PATH.relative_to(ROOT)).replace("\\", "/"),
        "sims": SIMS,
        "c_puct": C_PUCT,
        "seed_scheme": "SHA-256(json.dumps(state, sort_keys=True))[:8 bytes], big-endian, & 0x7FFFFFFFFFFFFFFF",
        "n_frozen_records_total": len(records),
        "n_non_drafting_excluded": n_non_drafting,
        "n_start_placement_adjacent_excluded": n_start_adjacent,
        "n_pending_dome_choice_excluded": n_pending_rotation,
        "n_labeled": len(labels),
        "n_root_candidates_mismatch": n_mismatch,
        "n_errors": n_error,
        "total_elapsed_seconds": total_elapsed,
        "immutable": True,
        "notes": (
            "Nur 'saubere' Phase::Drafting-Zustaende gelabelt -- siehe Docstring "
            "dieses Skripts fuer die genaue, empirisch verifizierte Scope-"
            "Einschraenkung (start-placement- und PendingDomeChoice-Zustaende "
            "ausgeschlossen, beide Kategorien im json_to_state-Doku-Kommentar "
            "in engine/src/serialize.rs dokumentiert)."
        ),
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump({"manifest": manifest, "labels": labels}, fh, ensure_ascii=False)
    print(f"Geschrieben: {OUT_JSON}")


if __name__ == "__main__":
    main()
