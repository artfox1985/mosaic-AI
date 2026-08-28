# -*- coding: utf-8 -*-
"""PREREG_heuristic_v2_long_rows.md par.3b.5 -- Lehrer-Treue der Policy nach SPIELTIEFE.

Frage der Registrierung: folgt die Policy von v22-b01 den LEHRER-Zuegen des
hv2-Korpus, und zwar aufgeschluesselt nach Runde (Bins 1/2/3/4) und -- wo n es
traegt -- nach frueh/spaet innerhalb der Runde? Die drei vorab festgelegten
Lesarten (par.3b.5) stehen unten als `READINGS` im Code und werden am Ende als
Auto-Hinweis auf die gemessenen Zahlen angewandt.

ANPASSUNG DER REGISTRIERTEN METRIKEN, ausdruecklich begruendet
--------------------------------------------------------------
Registriert sind `prior_mass_on_oracle_top3` und `kendall_tau` (die 7/7-
Arena-Praediktoren). Beide brauchen ein RANKING der Referenz. Der hv2-Korpus
liefert das nur auf einer seiner beiden Haelften:

* **Vorzugszuege** (`policy_target_valid=false`) tragen ein reines
  Demonstrations-Target: EIN Eintrag mit `prob=1.0` (self_play.rs:1566-1569).
  Ein one-hot-Lehrer hat keinen zweiten und dritten Platz -- `kendall_tau`
  ist dort nicht definiert, und `prior_mass_on_oracle_top3` faellt auf
  "Masse auf dem einen Lehrerzug" zusammen. Genau das ist hier die
  Hauptkennzahl `masse`: das one-hot-Analogon von `prior_mass`.
* **Such-getriebene Zuege** (Feld fehlt) tragen die volle Besuchsverteilung
  (im Stichprobenblick 3 Eintraege im Mittel, hoechstens 10). Dort werden die
  registrierten Metriken NATIV mitgerechnet (`top3_masse`, `kendall_tau`) --
  sie stehen in den Tabellen der Teilmenge `suche`.

Die spannende Haelfte ist laut Auftrag die VORZUGS-Haelfte: sie traegt den
Spaltenbau. Beide Teilmengen werden deshalb strikt getrennt ausgewiesen; ein
gepooltes Mittel gibt es bewusst nicht.

FELD-HERKUNFT (alles in dieser Sitzung am Code bzw. am Korpus geprueft)
----------------------------------------------------------------------
* **Teilmenge**: `record["policy_target_valid"]`. Das Feld wird nur bei
  Uebersteuerung geschrieben (self_play.rs:1917-1919, `if let Some(gueltig)`);
  im hv2-Korpus kommt ausschliesslich der Wert `false` vor (Stichprobe
  `selfplay_hv2_20260825_1727_g10.pkl`: 715 Records mit `false`, kein `true`).
  `is False` => Vorzugszug, Feld fehlt => such-getriebener Zug. Ein etwaiges
  `true` (PCR-Voll-Suche, anderer Schreiber) zaehlt als `suche` und wird im
  Zaehler `ptv_true` getrennt ausgewiesen.
* **Echte Wahl**: `len(record["valid_actions"]) > 1`. Der Ein-Aktion-
  Kurzschluss schreibt ebenfalls ein one-hot (self_play.rs:1563-1566) und ist
  KEINE Entscheidung -- ohne diesen Filter misst man Pflichtzuege mit.
* **Gewaehlte Lehrer-Aktion**: der Drafting-Record traegt KEIN eigenes Feld
  fuer die gespielte Aktion. Geschrieben werden nur `state`, `policy`,
  `valid_actions`, `moon_order_target`, `player` und optional `root_q`,
  `root_child_q`, `policy_target_valid` (self_play.rs:1893-1920; am Korpus
  gegengeprueft: genau diese Schluessel plus die Partie-Stempel
  `game_id`/`scores`/`scores_unclamped`/`winner`/`completed`/`bootstrap_value`).
  Referenz ist deshalb der ARGMAX des aufgezeichneten Policy-Ziels, nach
  Aktions-ID zusammengefasst:
  - Vorzugszug: das Ziel ist one-hot auf der uebersteuernden Aktion, und
    genau diese wird gespielt (`DraftingDecision.chosen`, angewandt in
    `apply_chosen_action`, self_play.rs:1830). Argmax == tatsaechlich
    gespielter Zug, exakt.
  - Such-getriebener Zug: der Argmax ist der MODALE Lehrerzug. Die Heuristik
    zieht mit Temperatur (self_play.rs:1379-1385), der gespielte Zug kann
    also abweichen und ist im Record nicht rekonstruierbar. Das ist im
    Artefakt als `referenz_suche` vermerkt, damit die Zahl nicht spaeter als
    "gespielter Zug" gelesen wird.
* **Tiefe**: `state["round"]` (Bins 1-4 der Registrierung; `5+` laeuft als
  Zusatzzeile OHNE Rolle im Auto-Hinweis mit). Der Zugindex INNERHALB der
  Runde steht in keinem Feld und wird aus der Record-Reihenfolge abgeleitet:
  Records stehen in Zugreihenfolge, je Partie zusammenhaengend (am Korpus
  geprueft). Gezaehlt werden alle Drafting-Records einer (Partie, Runde),
  also die Zugfolge der Runde ueber BEIDE Seiten; `frueh` ist die erste
  Haelfte dieser Folge, `spaet` die zweite.
* **Legalitaets-Maske**: `sorted(set(action_to_id(a) for a in valid_actions))`,
  Softmax nur ueber diese IDs (illegale auf -inf) -- dieselbe Maskierung wie
  im Training (neural_net.py) und in `tools/oracle_metrics.py::masked_softmax`.
  Die Dedup ist noetig, weil `action_to_id` mehrere Aktionen auf dieselbe ID
  abbilden kann (z.B. `moon_order` geht nicht in die ID ein).

Block-SE auf DATEI-Ebene (stehende Regel: Score-Auswertungen auf Block-Ebene,
Paar-SEs unterschaetzen massiv).

Stichprobe: `--files N` zieht ORDNUNGSFREI per Seed aus der sortierten
Gesamtliste, `--per-file M` ordnungsfrei je Datei. Beides absichtlich nicht
"die ersten N": "Erste N je Datei" ist ein stiller Rundenfilter
(docs/pitfalls.md, Vorfall 2026-08-25).

Aufruf (voller Lauf, exklusiv -- keine zweite Last auf der Maschine):

    python -u tools/probes/policy_teacher_fidelity_probe.py \
        --model models/alphazero_v22-b01_best.pth \
        --model models/alphazero_v22-b02_best.pth

Kleiner Formprobe-Lauf (die Zahlen sind dann kein Befund):

    python -u tools/probes/policy_teacher_fidelity_probe.py --files 3
"""
from __future__ import annotations

import os
import sys


def _early_thread_limit() -> int:
    """Liest `--threads` VOR dem torch-Import aus argv.

    OMP/MKL lesen ihre Grenzen beim Import; danach gesetzt wirken sie nicht
    mehr. Darum dieser Vorgriff statt argparse (gleiche Bauform wie
    tools/probes/column_build_prior_mass.py, das die Werte hart setzt).
    """
    for i, arg in enumerate(sys.argv):
        if arg == "--threads" and i + 1 < len(sys.argv):
            try:
                return max(1, int(sys.argv[i + 1]))
            except ValueError:
                return 1
        if arg.startswith("--threads="):
            try:
                return max(1, int(arg.split("=", 1)[1]))
            except ValueError:
                return 1
    return 1


_THREADS = _early_thread_limit()
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "-1")
os.environ["OMP_NUM_THREADS"] = str(_THREADS)
os.environ["MKL_NUM_THREADS"] = str(_THREADS)

import argparse  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import pathlib  # noqa: E402
import random  # noqa: E402
import statistics as st  # noqa: E402
import time  # noqa: E402

import numpy as np  # noqa: E402
import torch  # noqa: E402

torch.set_num_threads(_THREADS)

_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "engine" / "py"))
sys.path.insert(0, str(_ROOT / "tools"))

from config import INPUT_SIZE, NUM_ACTIONS  # noqa: E402
from corpus_io import corpus_files, load_records  # noqa: E402
from neural_net import (action_to_id, build_model_from_checkpoint,  # noqa: E402
                        state_to_planes, state_to_tensor)
from runtime_block import laufzeit_block  # noqa: E402  (CLAUDE.md-Pflichtblock)

PREREG = "PREREG_heuristic_v2_long_rows.md par.3b.5"

# Vorregistrierte Tiefen-Bins (par.3b.5). "5+" ist KEIN registrierter Bin und
# laeuft nur als Zusatzzeile mit -- der Auto-Hinweis fasst ihn nicht an.
ROUND_BINS = ("1", "2", "3", "4")
EXTRA_ROUND_BIN = "5+"
PHASE_BINS = ("frueh", "spaet")

# Teilmengen -- strikt getrennt ausgewiesen, kein gepooltes Mittel.
SUBSET_PREFERENCE = "vorzug"   # policy_target_valid=false, one-hot-Lehrerwahl
SUBSET_SEARCH = "suche"        # Feld fehlt: volle Besuchsverteilung

# Mindestbesetzung einer Zelle, damit die frueh/spaet-Aufteilung ueberhaupt
# berichtet wird ("wenn n es traegt", par.3b.5). GESETZT, nicht hergeleitet.
MIN_CELL_N = 200

# Orientierungs-Schwellen des Auto-Hinweises. AUSDRUECKLICH NICHT
# VORREGISTRIERT: par.3b.5 haelt die Schwellen "bewusst qualitativ
# (hoch/niedrig relativ zwischen den Tiefen-Bins)". Sie dienen nur dazu, das
# Muster zu BENENNEN; die Zahlen daneben entscheiden.
ORIENTATION_FALL_RATIO = 0.7   # Masse(Runde 4) / Masse(Runde 1)
ORIENTATION_LOW_LIFT = 3.0     # Masse / Zufallsniveau (1/n_legal) in Runde 1

READINGS = {
    "1": ("LESART 1 -- ZUSTANDS-DRIFT: Treue frueh hoch, faellt mit der Tiefe. "
          "Das Draft-Erbe ist da, die Tiling-Differenz entzieht ihm den Boden. "
          "Hebel: Tiling-ABSICHT zur Spielzeit (MOSAIC_OWNERSHIP_TILING_W mit "
          "b01-Kopf) und/oder On-Policy-Nachschaerfung."),
    "2": ("LESART 2 -- DESTILLATION: Treue schon frueh niedrig, das Erbe kommt "
          "gar nicht erst an. Hebel: Surprise-Weighting "
          "(PREREG_policy_surprise_weighting, waere v22-b03)."),
    "3": ("LESART 3 -- TILING-THESE in starker Form: Treue ueberall hoch. Gilt "
          "NUR zusammen mit der Spaltenquote bei ~0,3 (par.3b.2) -- dann "
          "verschenkt die Platzierung korrekt gedraftete Steine, und der "
          "Ownership-Pol-Arm traegt die Beweislast."),
}


# ---------------------------------------------------------------------------
# Sammelstelle
# ---------------------------------------------------------------------------
class Accumulator:
    """Sammelt Kennzahlen je Zelle -- global gepoolt UND je Datei als Block.

    Zelle = (Modell, Teilmenge, Dimension, Bin). Dimension ist `runde` (Bins
    der Registrierung) oder `runde_phase` (Runde x frueh/spaet). Je Zelle und
    Metrik werden (Summe, n) gehalten; `close_file` legt das Dateimittel als
    BLOCK ab (Block-SE auf Datei-Ebene, stehende Regel).
    """

    def __init__(self) -> None:
        self.total: dict[tuple, list[float]] = {}
        self.blocks: dict[tuple, list[float]] = {}
        self.current: dict[tuple, list[float]] = {}

    def add(self, cell: tuple, metric: str, value: float) -> None:
        if value is None:
            return
        key = cell + (metric,)
        for store in (self.total, self.current):
            slot = store.setdefault(key, [0.0, 0])
            slot[0] += float(value)
            slot[1] += 1

    def close_file(self) -> None:
        for key, (total, n) in self.current.items():
            if n:
                self.blocks.setdefault(key, []).append(total / n)
        self.current = {}

    def cell(self, cell: tuple, metric: str) -> dict:
        total, n = self.total.get(cell + (metric,), [0.0, 0])
        blocks = self.blocks.get(cell + (metric,), [])
        block_se = (st.stdev(blocks) / math.sqrt(len(blocks))
                    if len(blocks) >= 2 else None)
        return {
            "n": n,
            "mittel": (total / n) if n else None,
            "block_mittel": (sum(blocks) / len(blocks)) if blocks else None,
            "block_se": block_se,
            "bloecke": len(blocks),
        }


METRICS = ("masse", "lift", "top1", "top3", "zufall", "n_legal",
           "top3_masse", "kendall_tau", "n_legal_le_3")


def cell_row(acc: Accumulator, cell: tuple) -> dict:
    """Eine Tabellenzeile: alle Metriken einer Zelle."""
    row = {}
    for metric in METRICS:
        row[metric] = acc.cell(cell, metric)
    row["n"] = row["masse"]["n"]
    row["bloecke"] = row["masse"]["bloecke"]
    return row


# ---------------------------------------------------------------------------
# Kennzahlen einer Entscheidung
# ---------------------------------------------------------------------------
def masked_probs(logits: np.ndarray, legal_ids: list[int]) -> np.ndarray:
    """Softmax NUR ueber die legalen Aktions-IDs (illegale auf -inf).

    Gleichwertig zur Trainings-/Orakel-Maskierung
    (`tools/oracle_metrics.py::masked_softmax`, dort additiv `(mask-1)*1e9`);
    hier ueber den Legal-Teilvektor, weil die Rueckgabe ohnehin nur auf diesem
    ausgewertet wird.
    """
    legal = logits[legal_ids].astype(np.float64)
    legal -= legal.max()
    ex = np.exp(legal)
    total = ex.sum()
    if total <= 0.0:
        return np.full(len(legal_ids), 1.0 / len(legal_ids))
    return ex / total


def kendall_tau_b(x: list[float], y: list[float]) -> float | None:
    """Kendall tau-b ueber wenige Kandidaten (O(k^2), k <= ~10 im hv2-Korpus).

    Eigenbau statt scipy: die Sonde soll ohne zusaetzliche Abhaengigkeit
    laufen, und die Kandidatenlisten sind winzig.
    """
    k = len(x)
    if k < 3:
        return None
    concordant = discordant = tie_x = tie_y = 0
    for i in range(k):
        for j in range(i + 1, k):
            dx = x[i] - x[j]
            dy = y[i] - y[j]
            if dx == 0.0 and dy == 0.0:
                tie_x += 1
                tie_y += 1
                continue
            if dx == 0.0:
                tie_x += 1
                continue
            if dy == 0.0:
                tie_y += 1
                continue
            if (dx > 0) == (dy > 0):
                concordant += 1
            else:
                discordant += 1
    pairs = k * (k - 1) / 2
    denom = math.sqrt((pairs - tie_x) * (pairs - tie_y))
    if denom <= 0.0:
        return None
    return (concordant - discordant) / denom


def teacher_distribution(policy_entries: list[dict]) -> dict[int, float]:
    """Lehrer-Ziel als {Aktions-ID: Wahrscheinlichkeit}.

    Nach ID zusammengefasst, weil `action_to_id` mehrere Aktionen auf dieselbe
    ID abbilden kann -- die Modell-Policy kann sie nicht trennen, das Ziel
    darf sie hier also auch nicht getrennt fuehren.
    """
    dist: dict[int, float] = {}
    for entry in policy_entries:
        action = entry.get("action")
        if not isinstance(action, dict):
            continue
        prob = float(entry.get("prob", 0.0))
        aid = action_to_id(action)
        dist[aid] = dist.get(aid, 0.0) + prob
    return dist


# ---------------------------------------------------------------------------
# Auswahl der Records
# ---------------------------------------------------------------------------
def round_bin(round_value) -> str:
    try:
        r = int(round_value)
    except (TypeError, ValueError):
        return EXTRA_ROUND_BIN
    return str(r) if 1 <= r <= 4 else EXTRA_ROUND_BIN


def drafting_positions(records: list[dict]) -> tuple[list, dict]:
    """Zugindex je Record plus Laenge je (Partie, Runde).

    Erster Rueckgabewert je Record: `None` (kein Drafting-Record) oder der
    Index in der Drafting-Zugfolge seiner (Partie, Runde). Zweiter: die Laenge
    dieser Folgen. Der Aufrufer verrechnet beides ueber `phase_label`.
    Voraussetzung, am Korpus geprueft: Records stehen in Zugreihenfolge und je
    Partie zusammenhaengend.
    """
    lengths: dict[tuple, int] = {}
    for rec in records:
        state = rec.get("state") or {}
        if state.get("phase") != "drafting":
            continue
        key = (rec.get("game_id"), state.get("round"))
        lengths[key] = lengths.get(key, 0) + 1
    seen: dict[tuple, int] = {}
    positions: list[int | None] = []
    for rec in records:
        state = rec.get("state") or {}
        if state.get("phase") != "drafting":
            positions.append(None)
            continue
        key = (rec.get("game_id"), state.get("round"))
        idx = seen.get(key, 0)
        seen[key] = idx + 1
        positions.append(idx)
    return positions, lengths


def phase_label(index: int, length: int) -> str:
    """Erste Haelfte der Rundenzugfolge = `frueh`, zweite = `spaet`."""
    return PHASE_BINS[0] if index < length / 2.0 else PHASE_BINS[1]


def collect_decisions(records: list[dict], counters: dict,
                      per_file: int, rng: random.Random) -> list[dict]:
    """Qualifizierende Drafting-Entscheidungen einer Datei.

    Qualifiziert (siehe Modul-Doku "FELD-HERKUNFT"): Phase `drafting`, mehr
    als eine legale Aktion (ECHTE Wahl), nicht-leeres Policy-Ziel, und der
    Lehrer-Argmax liegt in der Legalitaets-Maske.
    """
    positions, lengths = drafting_positions(records)
    out = []
    for rec, position in zip(records, positions):
        counters["records"] += 1
        state = rec.get("state") or {}
        if state.get("phase") != "drafting":
            counters["nicht_drafting"] += 1
            continue
        valid_actions = rec.get("valid_actions") or []
        if len(valid_actions) <= 1:
            counters["ohne_echte_wahl"] += 1
            continue
        policy_entries = rec.get("policy") or []
        if not policy_entries:
            counters["ohne_policy_ziel"] += 1
            continue
        ptv = rec.get("policy_target_valid")
        if ptv is True:
            counters["ptv_true"] += 1
        subset = SUBSET_PREFERENCE if ptv is False else SUBSET_SEARCH

        dist = teacher_distribution(policy_entries)
        if not dist:
            counters["ohne_policy_ziel"] += 1
            continue
        legal_ids = sorted(set(action_to_id(a) for a in valid_actions))
        teacher_id = max(dist.items(), key=lambda kv: kv[1])[0]
        if teacher_id not in legal_ids:
            # Nach Konstruktion unmoeglich (das Ziel stammt aus derselben
            # Aktionsliste); defensiv gezaehlt statt still verzerrt.
            counters["lehrerzug_nicht_legal"] += 1
            continue
        if subset == SUBSET_PREFERENCE and len(dist) != 1:
            # Ein Vorzugsziel ist per Konstruktion one-hot; ein anderer Fall
            # waere ein Befund ueber den Erzeuger, kein Messwert.
            counters["vorzug_nicht_onehot"] += 1

        key = (rec.get("game_id"), state.get("round"))
        out.append({
            "subset": subset,
            "round_bin": round_bin(state.get("round")),
            "phase_bin": phase_label(position, lengths.get(key, 1)),
            "legal_ids": legal_ids,
            "teacher_id": teacher_id,
            "teacher_dist": dist,
            "state": state,
        })
    if per_file and len(out) > per_file:
        # Ordnungsfrei, NICHT die ersten M -- "Erste N je Datei" ist ein
        # stiller Rundenfilter (docs/pitfalls.md, 2026-08-25).
        out = rng.sample(out, per_file)
    return out


# ---------------------------------------------------------------------------
# Modelle
# ---------------------------------------------------------------------------
def load_models(paths: list[str]) -> list[dict]:
    """Laedt die Checkpoints ueber `build_model_from_checkpoint`.

    `input_size=None`: Eingangsbreite UND `planes_channels` kommen aus dem
    Checkpoint (neural_net.py:1747-1757). Danach wird gegen die aktuelle
    `INPUT_SIZE` geprueft und bei Abweichung HART abgebrochen -- ein Modell
    mit anderer Merkmalsbreite wuerde von `state_to_tensor` falsch gefuettert,
    und das faellt sonst erst als sinnloser Messwert auf.
    """
    models = []
    for path in paths:
        ckpt = torch.load(str(path), map_location="cpu")
        model, encoder = build_model_from_checkpoint(ckpt, input_size=None,
                                                     num_actions=NUM_ACTIONS)
        model.eval()
        # Breiten AUS DEM state_dict, nicht aus dem Modellobjekt: `MosaicNet`
        # legt `input_size` nicht als Attribut ab, ein `getattr`-Rueckfall
        # waere eine stille Nicht-Pruefung. Dieselben Schluessel, die
        # `build_model_from_checkpoint` selbst liest (neural_net.py:1747-1765).
        state = ckpt["model_state"]
        if encoder == "2d":
            in_size = int(state["flat_branch.0.weight"].shape[1])
            planes_channels = int(state["conv.0.weight"].shape[1])
        else:
            in_size = int(state["body.0.weight"].shape[1])
            planes_channels = None
        if in_size != INPUT_SIZE:
            raise SystemExit(
                f"ABBRUCH: {path} erwartet Eingangsbreite {in_size}, "
                f"state_to_tensor liefert {INPUT_SIZE}. Der Checkpoint gehoert "
                "zu einem anderen Merkmalsschema.")
        label = pathlib.Path(path).stem
        models.append({"label": label, "pfad": str(path).replace("\\", "/"),
                       "model": model, "encoder": encoder,
                       "input_size": in_size, "planes_channels": planes_channels})
        # Regel-0-Pruefstelle im Log: welcher Checkpoint mit welcher Geometrie
        # tatsaechlich angesprochen wurde.
        print(f"[modell] {label}: encoder={encoder}, input_size={in_size}, "
              f"planes_channels={planes_channels}", flush=True)
    return models


def policy_logits(entry: dict, planes: torch.Tensor, flat: torch.Tensor,
                  batch_size: int) -> np.ndarray:
    """Policy-Logits fuer einen ganzen Datei-Stapel, in Teilstapeln."""
    chunks = []
    with torch.no_grad():
        for start in range(0, flat.shape[0], batch_size):
            flat_chunk = flat[start:start + batch_size]
            if entry["encoder"] == "2d":
                planes_chunk = planes[start:start + batch_size]
                out = entry["model"](planes_chunk, flat_chunk)
            else:
                out = entry["model"](flat_chunk)
            chunks.append(out[0].numpy())
    return np.concatenate(chunks, axis=0) if chunks else np.zeros((0, NUM_ACTIONS))


# ---------------------------------------------------------------------------
# Auto-Hinweis
# ---------------------------------------------------------------------------
def within_round_ratios(rows_by_phase: dict) -> dict:
    """Verhaeltnis spaet/frueh INNERHALB jeder Runde, wo n es traegt.

    Zweite Tiefenachse der Registrierung ("innerhalb der Runde frueh/spaet
    nach Zugindex, wenn n es traegt"). Zellen unter `MIN_CELL_N` liefern
    `null` statt einer Zahl, die niemand tragen kann.
    """
    ratios = {}
    for label in ROUND_BINS:
        early = rows_by_phase.get(f"{label}/{PHASE_BINS[0]}")
        late = rows_by_phase.get(f"{label}/{PHASE_BINS[1]}")
        if not early or not late:
            ratios[label] = None
            continue
        if early["n"] < MIN_CELL_N or late["n"] < MIN_CELL_N:
            ratios[label] = None
            continue
        early_mass = early["masse"]["block_mittel"]
        late_mass = late["masse"]["block_mittel"]
        ratios[label] = (late_mass / early_mass
                         if early_mass not in (None, 0.0) and late_mass is not None
                         else None)
    return ratios


def reading_hint(rows_by_bin: dict, rows_by_phase: dict | None = None) -> dict:
    """Wendet die drei vorregistrierten Lesarten (par.3b.5) qualitativ an.

    Verglichen werden Runde 1 (frueh) und Runde 4 (spaet) DERSELBEN Teilmenge;
    die Aufteilung INNERHALB der Runden laeuft als Zusatzzahl mit
    (`within_round_ratios`) und faellt auf `null`, wo n sie nicht traegt.
    Reihenfolge der Pruefung: erst "frueh schon niedrig" (Lesart 2, sie
    dominiert -- ein Erbe, das nie ankam, kann nicht driften), dann "faellt"
    (Lesart 1), sonst "ueberall hoch" (Lesart 3).

    Die Schwellen sind ORIENTIERUNG, nicht vorregistriert (siehe
    `ORIENTATION_*`): par.3b.5 haelt sie bewusst qualitativ. Der Hinweis
    liefert deshalb die tragenden Zahlen mit.
    """
    inner = within_round_ratios(rows_by_phase) if rows_by_phase else {}
    early = rows_by_bin.get("1")
    late = rows_by_bin.get("4")
    if not early or not late or not early["n"] or not late["n"]:
        return {"muster": "N TRAEGT NICHT", "begruendung":
                "Runde 1 oder Runde 4 ist unbesetzt", "zahlen": {},
                "verhaeltnis_innerrunde": inner}
    early_mass = early["masse"]["block_mittel"]
    late_mass = late["masse"]["block_mittel"]
    early_lift = early["lift"]["block_mittel"]
    if early_mass in (None, 0.0) or late_mass is None or early_lift is None:
        return {"muster": "N TRAEGT NICHT", "begruendung":
                "kein Blockmittel fuer Runde 1 oder 4", "zahlen": {},
                "verhaeltnis_innerrunde": inner}
    ratio = late_mass / early_mass
    se_early = early["masse"]["block_se"] or 0.0
    se_late = late["masse"]["block_se"] or 0.0
    se_diff = math.sqrt(se_early ** 2 + se_late ** 2)
    drop = early_mass - late_mass
    numbers = {
        "masse_runde1": early_mass, "masse_runde4": late_mass,
        "verhaeltnis_spaet_frueh": ratio,
        "abfall": drop, "block_se_der_differenz": se_diff,
        "lift_runde1": early_lift,
        "top1_runde1": early["top1"]["block_mittel"],
        "top1_runde4": late["top1"]["block_mittel"],
    }
    if early_lift < ORIENTATION_LOW_LIFT:
        key = "2"
        why = (f"Lift in Runde 1 nur {early_lift:.2f} (Orientierung: unter "
               f"{ORIENTATION_LOW_LIFT}) -- die Treue ist schon frueh nahe am "
               "Zufallsniveau")
    elif ratio <= ORIENTATION_FALL_RATIO and drop > se_diff:
        key = "1"
        why = (f"Masse faellt von {early_mass:.3f} (R1) auf {late_mass:.3f} "
               f"(R4), Verhaeltnis {ratio:.2f} (Orientierung: <= "
               f"{ORIENTATION_FALL_RATIO}), Abfall {drop:+.3f} groesser als "
               f"die Block-SE der Differenz {se_diff:.3f}")
    else:
        key = "3"
        why = (f"Masse bleibt ueber die Tiefe stabil (R1 {early_mass:.3f}, "
               f"R4 {late_mass:.3f}, Verhaeltnis {ratio:.2f}) und liegt mit "
               f"Lift {early_lift:.2f} deutlich ueber dem Zufallsniveau")
    return {"muster": READINGS[key], "lesart": key, "begruendung": why,
            "zahlen": numbers,
            "verhaeltnis_innerrunde": inner,
            "schwellen_sind_orientierung": True}


# ---------------------------------------------------------------------------
# Ausgabe
# ---------------------------------------------------------------------------
def format_value(cell: dict, digits: int = 3) -> str:
    if not cell or cell["n"] == 0 or cell["block_mittel"] is None:
        return "        -"
    se = cell["block_se"]
    if se is None:
        return f"{cell['block_mittel']:9.{digits}f}"
    return f"{cell['block_mittel']:6.{digits}f}+-{se:.3f}"


def print_table(title: str, bins: list[str], rows_by_bin: dict) -> None:
    print(f"\n{title}")
    print("  Bin        |      n | Masse (Block+-SE) | Lift  | Top1        | "
          "Top3        | Zufall | n_leg | Bl.")
    for label in bins:
        row = rows_by_bin.get(label)
        if not row or not row["n"]:
            print(f"  {label:<10} |      0 |                 - |     - |"
                  "           - |           - |      - |     - |   0")
            continue
        lift = row["lift"]["block_mittel"]
        chance = row["zufall"]["block_mittel"]
        n_legal = row["n_legal"]["block_mittel"]
        print(f"  {label:<10} | {row['n']:6d} | {format_value(row['masse'])} | "
              f"{lift:5.2f} | {format_value(row['top1'])} | "
              f"{format_value(row['top3'])} | {chance:6.3f} | "
              f"{n_legal:5.1f} | {row['bloecke']:3d}")


def print_registered_metrics(title: str, bins: list[str], rows_by_bin: dict) -> None:
    """Die nativ registrierten Orakel-Metriken -- nur auf der Such-Teilmenge."""
    print(f"\n{title}")
    print("  Bin        |      n | top3_masse        | kendall_tau (n)")
    for label in bins:
        row = rows_by_bin.get(label)
        if not row or not row["n"]:
            print(f"  {label:<10} |      0 |                 - | -")
            continue
        tau = row["kendall_tau"]
        print(f"  {label:<10} | {row['n']:6d} | {format_value(row['top3_masse'])} | "
              f"{format_value(tau)} ({tau['n']})")


def main() -> int:
    parser = argparse.ArgumentParser(description=PREREG)
    parser.add_argument("--data-dir", default="data",
                        help="Korpus-Verzeichnis (relativ)")
    parser.add_argument("--pattern", default="selfplay_hv2_*.pkl",
                        help="Dateimuster des Lehrer-Korpus")
    parser.add_argument("--files", type=int, default=300,
                        help="Zahl ordnungsfrei gezogener Dateien (0 = alle)")
    parser.add_argument("--per-file", type=int, default=0,
                        help="qualifizierende Entscheidungen je Datei "
                             "(0 = alle), ordnungsfrei gezogen")
    parser.add_argument("--seed", type=int, default=20260828,
                        help="Seed der Dateien- und Record-Ziehung")
    parser.add_argument("--model", action="append", default=None,
                        help="Checkpoint (.pth), mehrfach angebbar -- alle "
                             "Modelle sehen DIESELBEN Zustaende")
    parser.add_argument("--batch", type=int, default=256,
                        help="Teilstapelgroesse des Forward-Passes")
    parser.add_argument("--threads", type=int, default=1,
                        help="torch/OMP-Faeden (vor dem Import gelesen)")
    parser.add_argument("--progress-every", type=int, default=25,
                        help="Fortschrittszeile alle N Dateien")
    parser.add_argument("--out",
                        default="evaluations/artifacts/policy_teacher_fidelity.json")
    args = parser.parse_args()

    model_paths = args.model or ["models/alphazero_v22-b01_best.pth"]
    wall_start, cpu_start = time.monotonic(), time.process_time()

    all_files = corpus_files(args.data_dir, args.pattern)
    if not all_files:
        print(f"Keine Dateien unter {args.data_dir}/{args.pattern}", flush=True)
        return 1
    rng = random.Random(args.seed)
    if args.files and args.files < len(all_files):
        paths = sorted(rng.sample(all_files, args.files))
        selection = f"{args.files} von {len(all_files)} ordnungsfrei (Seed {args.seed})"
    else:
        paths = all_files
        selection = f"alle {len(all_files)}"

    print(f"{PREREG}\nDateien: {selection}  ({args.data_dir}/{args.pattern})",
          flush=True)
    models = load_models(model_paths)

    acc = Accumulator()
    counters = {"records": 0, "nicht_drafting": 0, "ohne_echte_wahl": 0,
                "ohne_policy_ziel": 0, "lehrerzug_nicht_legal": 0,
                "vorzug_nicht_onehot": 0, "ptv_true": 0,
                "entscheidungen": 0,
                f"entscheidungen_{SUBSET_PREFERENCE}": 0,
                f"entscheidungen_{SUBSET_SEARCH}": 0}

    for index, path in enumerate(paths, 1):
        decisions = collect_decisions(load_records(path), counters,
                                      args.per_file, rng)
        if decisions:
            # `state_to_tensor` liefert bereits einen float32-Tensor
            # (neural_net.py:294), `state_to_planes` einen [C,6,6]-Tensor.
            flat = torch.stack([state_to_tensor(d["state"]) for d in decisions], dim=0)
            needs_planes = any(m["encoder"] == "2d" for m in models)
            planes = (torch.stack([state_to_planes(d["state"]) for d in decisions],
                                  dim=0) if needs_planes else None)
            for entry in models:
                logits = policy_logits(entry, planes, flat, args.batch)
                for j, decision in enumerate(decisions):
                    legal_ids = decision["legal_ids"]
                    probs = masked_probs(logits[j], legal_ids)
                    order = {aid: k for k, aid in enumerate(legal_ids)}
                    teacher_index = order[decision["teacher_id"]]
                    mass = float(probs[teacher_index])
                    n_legal = len(legal_ids)
                    ranked = np.argsort(-probs)
                    top1 = 1.0 if ranked[0] == teacher_index else 0.0
                    top3 = 1.0 if teacher_index in ranked[:3] else 0.0

                    dist = decision["teacher_dist"]
                    teacher_top3 = sorted(dist.items(), key=lambda kv: -kv[1])[:3]
                    top3_mass = float(sum(probs[order[aid]] for aid, _ in teacher_top3
                                          if aid in order))
                    candidate_ids = [aid for aid in dist if aid in order]
                    tau = None
                    if len(candidate_ids) >= 3:
                        tau = kendall_tau_b([dist[aid] for aid in candidate_ids],
                                            [float(probs[order[aid]]) for aid in candidate_ids])

                    for dimension, bin_label in (
                            ("runde", decision["round_bin"]),
                            ("runde_phase", f"{decision['round_bin']}/{decision['phase_bin']}")):
                        cell = (entry["label"], decision["subset"], dimension, bin_label)
                        acc.add(cell, "masse", mass)
                        acc.add(cell, "lift", mass * n_legal)
                        acc.add(cell, "top1", top1)
                        acc.add(cell, "top3", top3)
                        acc.add(cell, "zufall", 1.0 / n_legal)
                        acc.add(cell, "n_legal", float(n_legal))
                        acc.add(cell, "n_legal_le_3", 1.0 if n_legal <= 3 else 0.0)
                        acc.add(cell, "top3_masse", top3_mass)
                        if tau is not None:
                            acc.add(cell, "kendall_tau", tau)
            counters["entscheidungen"] += len(decisions)
            for decision in decisions:
                counters[f"entscheidungen_{decision['subset']}"] += 1
        acc.close_file()
        if index % args.progress_every == 0 or index == len(paths):
            elapsed = time.monotonic() - wall_start
            print(f"  {index}/{len(paths)} Dateien, "
                  f"{counters['entscheidungen']} Entscheidungen, "
                  f"{elapsed:.0f} s", flush=True)

    # ── Tabellen ────────────────────────────────────────────────────────────
    round_labels = list(ROUND_BINS) + [EXTRA_ROUND_BIN]
    phase_labels = [f"{r}/{p}" for r in ROUND_BINS for p in PHASE_BINS]
    tables: dict = {}
    hints: dict = {}
    for entry in models:
        label = entry["label"]
        tables[label] = {}
        hints[label] = {}
        for subset in (SUBSET_PREFERENCE, SUBSET_SEARCH):
            by_round = {b: cell_row(acc, (label, subset, "runde", b))
                        for b in round_labels}
            by_phase = {b: cell_row(acc, (label, subset, "runde_phase", b))
                        for b in phase_labels}
            thin = [b for b in phase_labels if 0 < by_phase[b]["n"] < MIN_CELL_N]
            tables[label][subset] = {
                "runde": by_round,
                "runde_phase": by_phase,
                "runde_phase_unterbesetzt": thin,
                "runde_phase_mindest_n": MIN_CELL_N,
            }
            hints[label][subset] = reading_hint(by_round, by_phase)

            print_table(f"MODELL {label} | Teilmenge {subset} | Tiefe = Runde "
                        f"(Bin '5+' ist Zusatz ohne Rolle im Hinweis)",
                        round_labels, by_round)
            if any(by_phase[b]["n"] >= MIN_CELL_N for b in phase_labels):
                print_table(f"MODELL {label} | Teilmenge {subset} | Tiefe = "
                            f"Runde x frueh/spaet (Zellen unter n={MIN_CELL_N} "
                            "tragen nicht)", phase_labels, by_phase)
            else:
                print(f"\nMODELL {label} | Teilmenge {subset} | Runde x "
                      f"frueh/spaet: keine Zelle erreicht n={MIN_CELL_N} -- "
                      "n traegt nicht, Tabelle nur im Artefakt.")
            if subset == SUBSET_SEARCH:
                print_registered_metrics(
                    f"MODELL {label} | Teilmenge {subset} | REGISTRIERTE "
                    "Orakel-Metriken (nur hier definiert, siehe Modul-Doku)",
                    round_labels, by_round)

    print("\n=== AUTO-HINWEIS (par.3b.5, qualitativ) ===")
    for entry in models:
        label = entry["label"]
        for subset in (SUBSET_PREFERENCE, SUBSET_SEARCH):
            hint = hints[label][subset]
            print(f"\n[{label} / {subset}] {hint['muster']}")
            print(f"  Begruendung: {hint['begruendung']}")
            inner = hint.get("verhaeltnis_innerrunde") or {}
            shown = {k: (f"{v:.2f}" if v is not None else "n traegt nicht")
                     for k, v in inner.items()}
            if shown:
                print(f"  Verhaeltnis spaet/frueh INNERHALB der Runde: {shown}")
    print("\nHINWEIS: die Schwellen des Auto-Hinweises sind ORIENTIERUNG, nicht "
          "vorregistriert -- par.3b.5 haelt sie bewusst qualitativ. Die "
          "Entscheidung faellt am Zahlenbild, nicht am Etikett.")

    result = {
        "prereg": PREREG,
        "korpus": {"verzeichnis": args.data_dir, "muster": args.pattern,
                   "dateien_gesamt": len(all_files), "dateien_genutzt": len(paths),
                   "auswahl": selection, "seed": args.seed,
                   "per_file": args.per_file or "alle"},
        "modelle": [{"label": m["label"], "pfad": m["pfad"],
                     "encoder": m["encoder"], "input_size": m["input_size"],
                     "planes_channels": m["planes_channels"]}
                    for m in models],
        "feld_herkunft": {
            "teilmenge": "record['policy_target_valid'] is False => 'vorzug' "
                         "(v2-Vorzug, one-hot-Lehrerwahl, self_play.rs:1917-1919); "
                         "Feld fehlt => 'suche' (volle Besuchsverteilung)",
            "echte_wahl": "len(record['valid_actions']) > 1 -- schliesst den "
                          "Ein-Aktion-Kurzschluss aus, der ebenfalls one-hot schreibt",
            "referenz_vorzug": "Argmax des Policy-Ziels == tatsaechlich gespielte "
                               "Aktion (one-hot auf der uebersteuernden Aktion, "
                               "angewandt in apply_chosen_action)",
            "referenz_suche": "Argmax des Policy-Ziels = MODALER Lehrerzug. Der "
                              "gespielte Zug steht in KEINEM Record-Feld (die "
                              "Heuristik zieht mit Temperatur) und ist nicht "
                              "rekonstruierbar",
            "tiefe": "state['round'] (Bins 1-4 registriert, '5+' als Zusatz); "
                     "Zugindex innerhalb der Runde aus der Record-Reihenfolge "
                     "je (Partie, Runde) abgeleitet, beide Seiten gemeinsam",
            "maske": "sorted(set(action_to_id(a) for a in valid_actions)), "
                     "Softmax nur darueber (illegale auf -inf)",
        },
        "metriken": {
            "masse": "Policy-Masse auf der Lehrer-Aktion (one-hot-Analogon von "
                     "prior_mass_on_oracle_top3)",
            "lift": "masse * n_legal, also masse / Zufallsniveau",
            "top1": "Lehrer-Aktion ist Argmax der maskierten Policy",
            "top3": "Lehrer-Aktion unter den Top 3 der maskierten Policy",
            "top3_masse": "REGISTRIERT: Modell-Masse auf den Top-3-Aktionen des "
                          "Lehrer-Ziels -- nur auf der Teilmenge 'suche' "
                          "aussagekraeftig (im 'vorzug'-Fall identisch zu masse)",
            "kendall_tau": "REGISTRIERT: tau-b zwischen Lehrer-Ziel und "
                           "Modell-Policy ueber die Kandidaten des Ziels; braucht "
                           ">= 3 Kandidaten, im 'vorzug'-Fall daher undefiniert",
            "zufall": "1/n_legal", "n_legal": "Zahl deduplizierter legaler IDs",
            "n_legal_le_3": "Anteil Entscheidungen mit hoechstens 3 legalen IDs "
                            "(dort ist top3 trivial)",
        },
        "block_ebene": "Datei (stehende Regel: Score-Auswertungen auf Block-Ebene)",
        "zaehler": counters,
        "tabellen": tables,
        "auto_hinweis": hints,
        "lesarten": READINGS,
        "orientierungs_schwellen": {
            "verhaeltnis_spaet_frueh": ORIENTATION_FALL_RATIO,
            "lift_runde1": ORIENTATION_LOW_LIFT,
            "hinweis": "NICHT vorregistriert -- par.3b.5 haelt die Schwellen "
                       "bewusst qualitativ; sie benennen nur das Muster",
        },
    }
    result["laufzeit"] = laufzeit_block(wall_start, cpu_start=cpu_start,
                                        threads=args.threads, n_games=None)
    result["laufzeit"]["s_je_datei"] = round(
        (time.monotonic() - wall_start) / max(1, len(paths)), 3)
    if args.files and args.files < len(all_files) and args.files < 25:
        result["hinweis"] = (f"FORMPROBE mit --files {args.files}: die Zahlen "
                             "sind kein Befund, die Block-SE steht auf "
                             f"{args.files} Bloecken.")

    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False),
                        encoding="utf-8", newline="\n")
    print(f"\nArtefakt: {args.out}  (wanduhr "
          f"{result['laufzeit']['wanduhr_s']} s, "
          f"{result['laufzeit']['s_je_datei']} s je Datei)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
