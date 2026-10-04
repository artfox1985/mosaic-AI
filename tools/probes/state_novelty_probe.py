"""Zustandsbasiertes Mass "andere Stellungen" (evaluations/PREREG_asymmetric_selfplay.md par.5d2).

Liest die vorhandenen Sonden-Dateien in `data/probe_asym` (kein neuer Lauf) und rechnet je Klasse und Seite
(W = `dome_dice_side`, G = Gegenseite; Klassen ohne Wuerfel-Seite: beide Seiten gepoolt):

* M1 Platzierungen Runde 1: Verteilung der in Runde 1 gelegten Kuppelplatten als Tripel (Platten-ID, Rotation,
  Platz); Jensen-Shannon-Distanz (log2, Bereich 0-1) gegen den Sockel `policy` (beide Seiten gepoolt),
  Bootstrap-CI ueber Partien, distinkte Tripel, Entropie in bit. Die Startplatte (vor Runde 1,
  docs/engine_manual.md Abschnitt 3 "Opening placement") zaehlt NICHT mit.
* M2 Brettzustaende zu Beginn von Runde 2 und 3: Anteil der kanonisierten Kuppelbretter einer Klasse und
  Seite, die im Sockel nicht vorkommen, und umgekehrt; distinkte Zustaende je 100 Partien.
* M3 Entscheidungen der G-Seite nach der Wuerfelphase (Runde 2-4, `dice_phase` nicht true): Anteil der
  G-Entscheide, deren Zustand (Brett des Ziehenden, Brett des Gegners) im Sockel nie auftritt; mittlere
  Prior-Entropie (Generator-Netz, Softmax ueber die gueltigen Aktions-IDs, nat) und mittleres `root_q` je
  Runde gegen den Sockel, dazu Prior-Entropie neu gegen nicht neu innerhalb G.

Rauschbezug (par.5d2 Leseregel): dieselben Masse fuer Sockel-Dateien 1-5 gegen 6-10. Zusaetzlich (nicht
registriert, als Lesehilfe): fuer M1 eine Permutations-Nullverteilung (JS-Distanzen endlicher Stichproben sind
per Konstruktion > 0), fuer M2/M3 ein groessengleicher Vergleich gegen je eine Sockel-Haelfte.

Kanonisierung eines Kuppelbretts: 3x3 Plaetze zeilenweise; je Platz leer oder (Platten-ID, Rotation, Belegung
der vier Felder in gedrehter Reihenfolge). Drei Feinheiten: `slots` (nur welche Plaetze belegt), `plates`
(+ ID und Rotation), `full` (+ gelegte Farben). Die Rotation steht nicht im Zustand (dome.rs `apply_rotation`
dreht die Felder in place); sie wird aus dem Vergleich mit der ungedrehten Lage derselben Platte in Auslage
oder Stapelziehung (`dome_display`, `pending_stack_draw`) bestimmt, Indizes wie dome.rs `rotation_indices`.

Fortschritt mit flush=True; Artefakt mit `laufzeit`-Block.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "tools"))
sys.path.insert(0, str(BASE_DIR / "tools" / "probes"))
sys.path.insert(0, str(BASE_DIR / "engine" / "py"))
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

from runtime_block import laufzeit_block  # noqa: E402

# Kein Import aus asym_probe_report: dessen Importkette (targeted_branching_pretest, evaluator_pretests) setzt
# MOSAIC_FEATURES_FROM_RUST prozessweit und veraendert damit fremde Cache-Schluessel im selben Testprozess
# (file_cache_key.py). Die Variable setzt nur `main()` mit Netz, vor dem Import von neural_net.


def class_files(data: Path, cls: str) -> list[str]:
    """Dateien einer Sonden-Klasse; dieselbe Bauform wie asym_probe_report `class_files`."""
    import glob
    return sorted(glob.glob(str(data / f"selfplay_probe-v35-{cls}_*.pkl")))

BASELINE = "policy"
DEFAULT_CLASSES = ("policy-dice-r1", "policy-dice-r2", "policy-dice-src4", "policy-s400")
DEFAULT_PAIRED_CLASSES = ("policy-dice-v2-r1", "policy-dice-v2-r2")  # par.5d3, Bezug policy-m2-400g
SIDE_FIELD = "dome_dice_side"
LEVELS = ("slots", "plates", "full")
M3_ROUNDS = (2, 3, 4)
# dome.rs:89-96, Layout vor Rotation [0][1] / [2][3]
ROTATION_INDICES = {0: (0, 1, 2, 3), 90: (2, 0, 3, 1), 180: (3, 2, 1, 0), 270: (1, 3, 0, 2)}


# ---------------------------------------------------------------------------------------------------------------
# Kanonisierung
# ---------------------------------------------------------------------------------------------------------------

def space_layout(tile: dict) -> tuple:
    """Feldtyp und geforderte Farbe je Feld (ohne `filled`/`locked`), serialize.rs `serialize_space`."""
    return tuple((sp.get("type"), sp.get("color")) for sp in tile["spaces"])


def update_catalog(state: dict, catalog: dict, conflicts: set) -> None:
    """Ungedrehte Lage je Platten-ID aus Auslage und Stapelziehung (dort ist noch nichts gedreht)."""
    for tile in list(state.get("dome_display") or []) + list(state.get("pending_stack_draw") or []):
        if not tile:
            continue
        lay = space_layout(tile)
        prev = catalog.setdefault(int(tile["id"]), lay)
        if prev != lay:
            conflicts.add(int(tile["id"]))


def rotation_of(tile_id: int, layout: tuple, catalog: dict):
    """Drehwinkel (0/90/180/270), fuer den die Katalog-Lage gedreht `layout` ergibt; bei mehreren Treffern der
    kleinste. Ohne Katalog-Eintrag oder ohne Treffer: die Lage selbst als Ersatzschluessel (eindeutig je ID)."""
    base = catalog.get(tile_id)
    if base is not None:
        for deg, idx in ROTATION_INDICES.items():
            if tuple(base[i] for i in idx) == layout:
                return deg
    return "L" + repr(layout)


def raw_board(player: dict) -> tuple:
    """Rohform eines Kuppelbretts: 9 Eintraege zeilenweise, je None oder (ID, Lage, Belegung)."""
    out = []
    for row in player.get("dome_grid") or []:
        for slot in row:
            if not slot:
                out.append(None)
            else:
                out.append((int(slot["id"]), space_layout(slot), tuple(sp.get("filled") for sp in slot["spaces"])))
    return tuple(out)


def board_key(raw: tuple, level: str, catalog: dict) -> tuple:
    """Kanonischer Schluessel eines Rohbretts in der Feinheit `level`."""
    if level == "slots":
        return tuple(0 if s is None else 1 for s in raw)
    if level == "plates":
        return tuple(None if s is None else (s[0], rotation_of(s[0], s[1], catalog)) for s in raw)
    if level == "full":
        return tuple(None if s is None else (s[0], rotation_of(s[0], s[1], catalog), s[2]) for s in raw)
    raise ValueError(level)


def occupied(raw: tuple) -> set:
    return {i for i, s in enumerate(raw) if s is not None}


# ---------------------------------------------------------------------------------------------------------------
# Partien zerlegen
# ---------------------------------------------------------------------------------------------------------------

def split_games(records: list) -> dict:
    """Records je Partie (game_id ohne `_x`-Suffix, wie asym_probe_report `read_class`)."""
    by_game: dict[str, list] = defaultdict(list)
    for r in records:
        by_game[str(r.get("game_id", "")).split("_x")[0]].append(r)
    return by_game


def special_side(rs: list, side_field: str | None):
    if side_field is None:
        return None
    vals = {r.get(side_field) for r in rs if r.get(side_field) is not None}
    return int(next(iter(vals))) if len(vals) == 1 else None


def _state(r):
    st = r.get("state")
    return st if isinstance(st, dict) else None


def board_at_round_start(rs: list, p: int, k: int):
    """Kuppelbrett von Spieler p zu Beginn von Runde k (Rohform) oder None (nicht aufloesbar).

    Erwartet werden 1 + 2(k-1) Platten (Startplatte plus genau 2 je Runde, docs/engine_manual.md 4A). Genommen
    wird der Drafting-Record der Runde k mit den wenigsten Platten von p (Platten wachsen nur, also der frueheste;
    die Belegung der Felder aendert sich im Drafting nicht). Liegt dort schon eine Platte der Runde k (ein
    unaufgezeichneter erzwungener Zug), wird auf die Plaetze geschnitten, die schon im letzten Record der Runde
    k-1 belegt waren."""
    expected = 1 + 2 * (k - 1)
    cand = [_state(r) for r in rs]
    drafting_k = [s for s in cand if s and int(s.get("round", 0)) == k and s.get("phase") == "drafting"]
    if not drafting_k:
        return None
    boards = [raw_board(s["players"][p]) for s in drafting_k]
    first = min(boards, key=lambda b: len(occupied(b)))
    occ = occupied(first)
    if len(occ) == expected:
        return first
    if len(occ) < expected:
        return None
    prev = [raw_board(s["players"][p]) for s in cand if s and int(s.get("round", 0)) == k - 1]
    if not prev:
        return None
    keep = occ & occupied(max(prev, key=lambda b: len(occupied(b))))
    if len(keep) != expected:
        return None
    return tuple(s if i in keep else None for i, s in enumerate(first))


def start_slot(rs: list, p: int):
    """Platz der Startplatte von p: der einzige belegte Platz in einem Record, in dem p genau eine Platte hat
    (Records BEIDER Spieler zaehlen, jeder traegt beide Bretter)."""
    for r in rs:
        s = _state(r)
        if not s:
            continue
        occ = occupied(raw_board(s["players"][p]))
        if len(occ) == 1:
            return next(iter(occ))
    return None


def round1_placements(rs: list, p: int):
    """Die zwei in Runde 1 gelegten Platten von p als Liste (ID, Lage, Platz) oder None."""
    b2 = board_at_round_start(rs, p, 2)
    ss = start_slot(rs, p)
    if b2 is None or ss is None or ss not in occupied(b2):
        return None
    return [(b2[i][0], b2[i][1], i) for i in sorted(occupied(b2) - {ss})]


def pair_key(gid: str):
    """Partie-Index `_cX_gY` am Ende der game_id (Chunk und Partie im Chunk) oder None."""
    m = re.search(r"_c(\d+)_g(\d+)$", str(gid))
    return (int(m.group(1)), int(m.group(2))) if m else None


def display_ids(state: dict) -> tuple:
    return tuple(int(t["id"]) for t in (state.get("dome_display") or []) if t)


def game_sequence(rs: list) -> list:
    """Records einer Partie in Aufzeichnungsreihenfolge, ohne Platzwahl-Records (die gibt es nur in W-Klassen,
    sie wuerden die Folge gegen die Bezugspartie verschieben): je Eintrag (Spieler, Runde, Brett 0, Brett 1,
    Auslage-IDs). Erzwungene Wuerfelzuege tragen keinen Record (self_play.rs, par.3c)."""
    out = []
    for r in rs:
        s = _state(r)
        if not s or r.get("dice_place") or "player" not in r:
            continue
        out.append((int(r["player"]), int(s.get("round", 0)), raw_board(s["players"][0]),
                    raw_board(s["players"][1]), display_ids(s)))
    return out


def side_view(entry: tuple, p: int) -> tuple:
    """Zustand aus Sicht von Spieler p: (eigenes Brett, Gegnerbrett, Auslage)."""
    return (entry[2 + p], entry[3 - p], entry[4])


def first_divergence(seq_a: list, seq_b: list, p: int):
    """Erster eigener Entscheid von p, an dem sein Zustand in Partie A von Partie B abweicht.

    Ausgerichtet wird ueber die Ordnungszahl der Records von p (k-ter Entscheid von p in A gegen den k-ten in B),
    weil die Gesamtfolge in W-Partien durch die unaufgezeichneten erzwungenen Zuege verschoben ist. Rueckgabe
    None (keine Abweichung, gleiche Laenge) oder dict mit `k` (eigene Entscheide vor der Abweichung), `index`
    (Record-Index in A, beide Spieler, ohne Platzwahl-Records) und `round` (Runde in A)."""
    ia = [i for i, e in enumerate(seq_a) if e[0] == p]
    ib = [i for i, e in enumerate(seq_b) if e[0] == p]
    for k in range(min(len(ia), len(ib))):
        if side_view(seq_a[ia[k]], p) != side_view(seq_b[ib[k]], p):
            return {"k": k, "index": ia[k], "round": seq_a[ia[k]][1]}
    if len(ia) != len(ib):
        k = min(len(ia), len(ib))
        idx = ia[k] if k < len(ia) else (ia[-1] + 1 if ia else 0)
        return {"k": k, "index": idx, "round": seq_a[ia[k]][1] if k < len(ia) else None}
    return None


def decision_records(rs: list, players: set, rounds=M3_ROUNDS, post_dice: bool = True):
    """Drafting-Entscheide (ohne Platzwahl-Records, ohne completed=false) der Spieler `players` in `rounds`;
    mit `post_dice` nur Records ausserhalb der Wuerfelphase (`dice_phase` nicht true)."""
    out = []
    for r in rs:
        s = _state(r)
        if not s or s.get("phase") != "drafting" or r.get("dice_place") or r.get("completed", True) is False:
            continue
        if int(s.get("round", 0)) not in rounds or int(r.get("player", -1)) not in players:
            continue
        if post_dice and r.get("dice_phase") is True:
            continue
        out.append(r)
    return out


# ---------------------------------------------------------------------------------------------------------------
# Statistik
# ---------------------------------------------------------------------------------------------------------------

def js_distance(ca: Counter, cb: Counter) -> float:
    """Jensen-Shannon-Distanz (Wurzel der Divergenz, log2) zweier Zaehlungen; 0 = gleich, 1 = disjunkt."""
    na, nb = sum(ca.values()), sum(cb.values())
    if na == 0 or nb == 0:
        return float("nan")
    keys = set(ca) | set(cb)
    p = np.array([ca.get(k, 0) / na for k in keys])
    q = np.array([cb.get(k, 0) / nb for k in keys])
    m = 0.5 * (p + q)

    def kl(x):
        nz = x > 0
        return float(np.sum(x[nz] * np.log2(x[nz] / m[nz])))
    return float(np.sqrt(max(0.0, 0.5 * kl(p) + 0.5 * kl(q))))


def entropy_bits(c: Counter) -> float:
    n = sum(c.values())
    if n == 0:
        return float("nan")
    p = np.array(list(c.values()), dtype=float) / n
    return float(-np.sum(p * np.log2(p)))


def _pool(units, idx):
    c = Counter()
    for i in idx:
        c.update(units[i][1])
    return c


def _js_vec(p: np.ndarray, q: np.ndarray) -> float:
    """JS-Distanz zweier Zaehlvektoren ueber denselben Schluesselraum (wie `js_distance`)."""
    sp, sq = p.sum(), q.sum()
    if sp <= 0 or sq <= 0:
        return float("nan")
    p, q = p / sp, q / sq
    m = 0.5 * (p + q)
    with np.errstate(divide="ignore", invalid="ignore"):
        kp = np.where(p > 0, p * np.log2(p / m), 0.0).sum()
        kq = np.where(q > 0, q * np.log2(q / m), 0.0).sum()
    return float(np.sqrt(max(0.0, 0.5 * kp + 0.5 * kq)))


def _unit_matrix(units, index):
    mat = np.zeros((len(units), len(index)))
    for i, (_g, ks) in enumerate(units):
        for k in ks:
            mat[i, index[k]] += 1
    return mat


def _group_matrix(units, mat):
    gids = {}
    for _g, _ks in units:
        gids.setdefault(_g, len(gids))
    gm = np.zeros((len(gids), mat.shape[1]))
    for i, (g, _ks) in enumerate(units):
        gm[gids[g]] += mat[i]
    return gm


def m1_compare(units_a, units_b, rng, n_boot, n_perm, proj=None) -> dict:
    """JS-Distanz zweier Platzierungsmengen. `units` = Liste (Gruppe, [Schluessel]) je Partie und Seite; der
    Bootstrap zieht Gruppen (Partien), die Permutation tauscht Einheiten (Partie-Seiten) zwischen A und B."""
    if proj is not None:
        units_a = [(g, [proj(k) for k in ks]) for g, ks in units_a]
        units_b = [(g, [proj(k) for k in ks]) for g, ks in units_b]
    ca, cb = _pool(units_a, range(len(units_a))), _pool(units_b, range(len(units_b)))
    point = js_distance(ca, cb)
    index = {k: i for i, k in enumerate(set(ca) | set(cb))}
    ua, ub = _unit_matrix(units_a, index), _unit_matrix(units_b, index)
    ga, gb = _group_matrix(units_a, ua), _group_matrix(units_b, ub)
    boots = []
    if len(ga) and len(gb):
        for _ in range(n_boot):
            wa = np.bincount(rng.integers(0, len(ga), len(ga)), minlength=len(ga))
            wb = np.bincount(rng.integers(0, len(gb), len(gb)), minlength=len(gb))
            boots.append(_js_vec(wa @ ga, wb @ gb))
    allu = np.vstack([ua, ub]) if len(index) else np.zeros((0, 0))
    na = len(units_a)
    null = []
    if len(units_a) and len(units_b):
        for _ in range(n_perm):
            perm = rng.permutation(len(allu))
            null.append(_js_vec(allu[perm[:na]].sum(0), allu[perm[na:]].sum(0)))
    res = {"js": point, "n_a": int(sum(ca.values())), "n_b": int(sum(cb.values()))}
    res["js_ci95"] = [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))] if boots else None
    if null:
        null = np.array(null)
        res["perm_null"] = {"mittel": float(null.mean()), "q95": float(np.percentile(null, 95)),
                            "p": float((1 + np.sum(null >= point)) / (1 + len(null))), "n_perm": int(len(null))}
    return res


def novelty(query: list, reference: list) -> float:
    """Anteil der Schluessel in `query`, die in `reference` nicht vorkommen."""
    if not query:
        return float("nan")
    ref = set(reference)
    return float(np.mean([k not in ref for k in query]))


def novelty_boot(q_by_file: list, r_by_file: list, rng, n_boot) -> list | None:
    """95-%-Intervall des Neuheitsanteils, Dateien von Abfrage und Bezug je fuer sich gezogen."""
    kq, kr = len(q_by_file), len(r_by_file)
    if not kq or not kr or not any(q_by_file):
        return None
    # Vektorisiert: Zaehlmatrix Abfrage (Datei x Schluessel), Praesenzmatrix Bezug (Schluessel x Datei)
    index = {}
    for xs in q_by_file:
        for k in xs:
            index.setdefault(k, len(index))
    qm = np.zeros((kq, len(index)))
    for i, xs in enumerate(q_by_file):
        for k in xs:
            qm[i, index[k]] += 1
    pres = np.zeros((len(index), kr), dtype=bool)
    for j, xs in enumerate(r_by_file):
        for k in set(xs):
            if k in index:
                pres[index[k], j] = True
    out = []
    for _ in range(n_boot):
        counts = np.bincount(rng.integers(0, kq, kq), minlength=kq) @ qm
        drawn = np.zeros(kr, dtype=bool)
        drawn[rng.integers(0, kr, kr)] = True
        in_ref = pres[:, drawn].any(1)
        tot = counts.sum()
        if tot > 0:
            out.append(float(counts[~in_ref].sum() / tot))
    return [float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))] if out else None


def mean_diff_boot(a_by_file: list, b_by_file: list, rng, n_boot) -> dict:
    """Mittel(A) - Mittel(B), Block-Bootstrap ueber Dateien (A und B je fuer sich gezogen)."""
    a = np.concatenate([np.asarray(x, float) for x in a_by_file]) if a_by_file else np.array([])
    b = np.concatenate([np.asarray(x, float) for x in b_by_file]) if b_by_file else np.array([])
    res = {"n_a": int(a.size), "n_b": int(b.size), "mittel_a": float(a.mean()) if a.size else None,
           "mittel_b": float(b.mean()) if b.size else None}
    if not a.size or not b.size:
        res.update({"differenz": None, "ci95": None})
        return res
    res["differenz"] = float(a.mean() - b.mean())
    sa = np.array([float(np.sum(x)) for x in a_by_file]); na = np.array([len(x) for x in a_by_file], float)
    sb = np.array([float(np.sum(x)) for x in b_by_file]); nb = np.array([len(x) for x in b_by_file], float)
    ka, kb = len(a_by_file), len(b_by_file)
    da = rng.integers(0, ka, size=(n_boot, ka))
    db = rng.integers(0, kb, size=(n_boot, kb))
    ca, cb = na[da].sum(1), nb[db].sum(1)
    ok = (ca > 0) & (cb > 0)
    diffs = sa[da].sum(1)[ok] / ca[ok] - sb[db].sum(1)[ok] / cb[ok]
    res["ci95"] = [float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))] if diffs.size else None
    return res


def prior_entropy(logits_row: np.ndarray, ids) -> float:
    """Entropie (nat) der Softmax der Logits, eingeschraenkt auf die gueltigen Aktions-IDs."""
    ids = np.array(sorted(set(int(i) for i in ids)), dtype=np.int64)
    if ids.size < 1:
        return float("nan")
    lg = logits_row[ids].astype(np.float64)
    lg = lg - lg.max()
    p = np.exp(lg) / np.exp(lg).sum()
    return float(-np.sum(np.where(p > 0, p * np.log(np.clip(p, 1e-300, None)), 0.0)))


# ---------------------------------------------------------------------------------------------------------------
# Lesen
# ---------------------------------------------------------------------------------------------------------------

def extract_class(files: list, side_field: str | None, catalog: dict, conflicts: set, load, tag: str,
                  t_start: float, action_id=None, net_eval=None, batch: int = 256) -> dict:
    """Je Partie: Datei, Gruppe, Wuerfel-Seite, R1-Platzierungen und Bretter R2/R3 je Spieler, M3-Entscheide.

    M3-Entscheide: bei Klassen mit Wuerfel-Seite nur die der G-Seite (Runde 2-4, Flag `dice_phase` je Entscheid),
    sonst beider Seiten. `load(path)` liefert die Record-Liste; `action_id` (Aktion -> ID) und `net_eval`
    (Zustaende -> Logits) sind optional, ohne sie bleibt die Prior-Entropie leer."""
    games, unresolved = [], Counter()
    pending = []  # (Entscheid-Dict, Zustand, IDs) fuer die gebuendelte Netz-Auswertung

    def flush():
        if not pending:
            return
        logits = net_eval([x[1] for x in pending])
        for i, (d, _s, ids) in enumerate(pending):
            d["prior_entropy"] = prior_entropy(logits[i], ids)
        pending.clear()

    for fi, f in enumerate(files):
        recs = load(f)
        for r in recs:
            s = _state(r)
            if s:
                update_catalog(s, catalog, conflicts)
        for gid, rs in split_games(recs).items():
            if not any(r.get("winner") is not None for r in rs):
                unresolved["partie_ohne_sieger"] += 1
                continue
            sp = special_side(rs, side_field)
            g = {"file": fi, "group": f"{fi}:{gid}", "special": sp, "r1": {}, "start": {2: {}, 3: {}},
                 "decisions": [], "pair_key": pair_key(gid), "seq": game_sequence(rs)}
            if side_field is not None and sp is None:
                unresolved["ohne_wuerfelseite"] += 1
                continue
            for p in (0, 1):
                pl = round1_placements(rs, p)
                if pl is None:
                    unresolved["r1_nicht_aufloesbar"] += 1
                g["r1"][p] = pl
                for k in (2, 3):
                    b = board_at_round_start(rs, p, k)
                    if b is None:
                        unresolved[f"brett_r{k}_nicht_aufloesbar"] += 1
                    g["start"][k][p] = b
            movers = {0, 1} if sp is None else {1 - sp}
            for r in decision_records(rs, movers, post_dice=False):
                s = _state(r)
                p = int(r["player"])
                d = {"dice_phase": r.get("dice_phase") is True, "player": p, "round": int(s["round"]),
                     "mover": raw_board(s["players"][p]), "opp": raw_board(s["players"][1 - p]),
                     "root_q": float(r["root_q"]) if r.get("root_q") is not None else None,
                     "prior_entropy": None}
                g["decisions"].append(d)
                if action_id is not None and net_eval is not None:
                    try:
                        ids = [action_id(a) for a in (r.get("valid_actions") or [])]
                        if not ids:
                            ids = [action_id(pe["action"]) for pe in (r.get("policy") or [])]
                    except Exception:  # noqa: BLE001
                        unresolved["ids_nicht_lesbar"] += 1
                        continue
                    pending.append((d, s, ids))
                    if len(pending) >= batch:
                        flush()
            games.append(g)
        flush()
        print(f"[novelty] {tag} {fi + 1}/{len(files)} Dateien, {len(games)} Partien, "
              f"{time.monotonic() - t_start:.0f} s", flush=True)
    return {"games": games, "unresolved": dict(unresolved), "n_files": len(files)}


# ---------------------------------------------------------------------------------------------------------------
# Auswertung
# ---------------------------------------------------------------------------------------------------------------

def has_special(cls_data: dict) -> bool:
    return any(g["special"] is not None for g in cls_data["games"])


def side_players(g: dict, side: str) -> list:
    """Spielerindizes einer Partie fuer die Seite `side` ("W", "G" oder "beide")."""
    if side == "beide":
        return [0, 1]
    if g["special"] is None:
        return []
    return [g["special"]] if side == "W" else [1 - g["special"]]


def subset_games(cls_data: dict, files: set) -> dict:
    return {"games": [g for g in cls_data["games"] if g["file"] in files], "n_files": cls_data["n_files"]}


def m1_units(games: list, side: str, catalog: dict) -> list:
    """Je Partie und Seite eine Einheit (Partie-Gruppe, [Tripel (ID, Rotation, Platz)])."""
    units = []
    for g in games:
        for p in side_players(g, side):
            pl = g["r1"].get(p)
            if pl is None:
                continue
            units.append((g["group"], [(tid, rotation_of(tid, lay, catalog), slot) for tid, lay, slot in pl]))
    return units


def m1_row(units: list) -> dict:
    c = _pool(units, range(len(units)))
    return {"n_partien": len({u[0] for u in units}), "n_platzierungen": int(sum(c.values())),
            "distinkte_tripel": len(c), "entropie_bit": entropy_bits(c)}


def m1_full(units_a, units_b, rng, n_boot, n_perm) -> dict:
    res = m1_compare(units_a, units_b, rng, n_boot, n_perm)
    res["randverteilungen"] = {
        name: m1_compare(units_a, units_b, rng, n_boot, n_perm, proj=pr)
        for name, pr in (("platte", lambda k: k[0]), ("rotation", lambda k: k[1]), ("platz", lambda k: k[2]))}
    return res


def board_keys_by_file(games: list, side: str, k: int, level: str, catalog: dict, n_files: int) -> list:
    out = [[] for _ in range(n_files)]
    for g in games:
        for p in side_players(g, side):
            b = g["start"][k].get(p)
            if b is not None:
                out[g["file"]].append(board_key(b, level, catalog))
    return out


def _flat(by_file):
    return [x for xs in by_file for x in xs]


def m2_cell(q_by_file, base_by_file, half_a, half_b, n_games, rng, n_boot) -> dict:
    q, base = _flat(q_by_file), _flat(base_by_file)
    n_q = len(q)
    return {
        "n_bretter": n_q, "n_partien": n_games,
        "anteil_sockelfremd": novelty(q, base),
        "anteil_sockelfremd_ci95": novelty_boot(q_by_file, base_by_file, rng, n_boot),
        "anteil_sockel_klassenfremd": novelty(base, q),
        "anteil_sockel_klassenfremd_ci95": novelty_boot(base_by_file, q_by_file, rng, n_boot),
        "distinkt_je_100_partien": 100.0 * len(set(q)) / n_games if n_games else None,
        "distinkt_je_100_bretter": 100.0 * len(set(q)) / n_q if n_q else None,
        "groessengleich_gegen_sockelhaelften": float(np.mean([novelty(q, _flat(half_a)),
                                                              novelty(q, _flat(half_b))])),
        # par.5d2 Leseregel (praezisiert): gleich grosse Bezugsmenge wie der Rauschbezug Haelfte gegen Haelfte
        "gegen_sockelhaelfte_a": {"anteil": novelty(q, _flat(half_a)),
                                  "ci95": novelty_boot(q_by_file, half_a, rng, n_boot)},
        "gegen_sockelhaelfte_b": {"anteil": novelty(q, _flat(half_b)),
                                  "ci95": novelty_boot(q_by_file, half_b, rng, n_boot)},
    }


def decision_key(d: dict, level: str, catalog: dict) -> tuple:
    """Zustand eines Entscheids: (Brett des Ziehenden, Brett des Gegners); je Feinheit zwischengespeichert
    (der Katalog ist nach dem Lesen fest)."""
    memo = d.setdefault("_key", {})
    if level not in memo:
        memo[level] = (board_key(d["mover"], level, catalog), board_key(d["opp"], level, catalog))
    return memo[level]


def m3_decisions(cls_data: dict, post_only: bool) -> list:
    out = []
    for g in cls_data["games"]:
        for d in g["decisions"]:
            if post_only and d["dice_phase"]:
                continue
            out.append((g["file"], d))
    return out


def by_file_values(decs, n_files, fn, rounds=M3_ROUNDS) -> list:
    out = [[] for _ in range(n_files)]
    for fi, d in decs:
        if d["round"] in rounds:
            v = fn(d)
            if v is not None and not (isinstance(v, float) and np.isnan(v)):
                out[fi].append(v)
    return out


def m3_block(decs, n_files, base_decs, base_n_files, half_a_decs, half_b_decs, catalog, rng, n_boot) -> dict:
    res = {"n_entscheide": len(decs), "je_feinheit": {}, "je_runde": {}}
    for level in LEVELS:
        def key(d, lv=level):
            return decision_key(d, lv, catalog)
        q_by = by_file_values(decs, n_files, key)
        b_by = by_file_values(base_decs, base_n_files, key)
        base_set = set(_flat(b_by))
        cell = {"anteil_sockelfremd": novelty(_flat(q_by), _flat(b_by)),
                "anteil_sockelfremd_ci95": novelty_boot(q_by, b_by, rng, n_boot),
                "groessengleich_gegen_sockelhaelften": float(np.mean([
                    novelty(_flat(q_by), [key(d) for _f, d in half_a_decs]),
                    novelty(_flat(q_by), [key(d) for _f, d in half_b_decs])])),
                "je_runde": {str(k): novelty(_flat(by_file_values(decs, n_files, key, (k,))), list(base_set))
                             for k in M3_ROUNDS}}
        # Prior-Entropie neu gegen bekannt innerhalb der Klasse (ist G in neuen Stellungen unsicherer?)
        novel_by = by_file_values(decs, n_files, lambda d: d["prior_entropy"] if key(d) not in base_set else None)
        known_by = by_file_values(decs, n_files, lambda d: d["prior_entropy"] if key(d) in base_set else None)
        cell["prior_entropie_neu_minus_bekannt"] = mean_diff_boot(novel_by, known_by, rng, n_boot)
        res["je_feinheit"][level] = cell
    for k in M3_ROUNDS:
        res["je_runde"][str(k)] = {
            "prior_entropie_nat": mean_diff_boot(
                by_file_values(decs, n_files, lambda d: d["prior_entropy"], (k,)),
                by_file_values(base_decs, base_n_files, lambda d: d["prior_entropy"], (k,)), rng, n_boot),
            "root_q": mean_diff_boot(
                by_file_values(decs, n_files, lambda d: d["root_q"], (k,)),
                by_file_values(base_decs, base_n_files, lambda d: d["root_q"], (k,)), rng, n_boot)}
    return res


def noise_key(baseline: str, nb: int) -> str:
    """Schluessel des Rauschbezugs (erste gegen zweite Haelfte der Bezugsdateien)."""
    h = nb // 2
    return f"rauschbezug_{'sockel' if baseline == BASELINE else 'bezug'}_1-{h}_gegen_{h + 1}-{nb}"


def analyze(data: dict, classes: list, catalog: dict, rng, n_boot: int, n_perm: int, baseline: str = BASELINE,
            m2_levels=LEVELS) -> dict:
    """Alle drei Masse aus den gelesenen Klassen (`data[klasse]` aus `extract_class`); `classes` ohne Bezug.
    `baseline` ist die Bezugsklasse (Default Sockel `policy`), `m2_levels` die Feinheiten von M2."""
    base = data[baseline]
    nb = base["n_files"]
    nkey = noise_key(baseline, nb)
    half_a_files, half_b_files = set(range(nb // 2)), set(range(nb // 2, nb))
    half_a, half_b = subset_games(base, half_a_files), subset_games(base, half_b_files)
    base_units = m1_units(base["games"], "beide", catalog)
    out = {"M1": {"grundmenge": "in Runde 1 gelegte Kuppelplatten (ohne Startplatte), je Partie und Seite; "
                                f"Bezug `{baseline}` beide Seiten gepoolt",
                  "einheit": "Jensen-Shannon-Distanz (log2, 0-1) der Verteilung der Tripel (Platten-ID, Rotation, "
                             "Platz); Entropie in bit; CI Bootstrap ueber Partien",
                  "zeilen": {}},
           "M2": {"grundmenge": "kanonisierte Kuppelbretter je Spieler zu Beginn von Runde 2 bzw. 3 (ein Brett je "
                                "Partie und Seite); Sockel beide Seiten gepoolt",
                  "einheit": "Anteil der Bretter der Zeile, die im Bezug nicht vorkommen; distinkte Bretter je 100 "
                             "Partien bzw. je 100 Bretter; CI Bootstrap ueber Dateien",
                  "zeilen": {}},
           "M3": {"grundmenge": "Drafting-Entscheide Runde 2-4 der G-Seite nach der Wuerfelphase (dice_phase nicht "
                                "true, ohne Platzwahl-Records); Sockel und Klassen ohne Wuerfel-Seite: beide Seiten",
                  "einheit": "Anteil der Entscheide, deren Zustand (Brett Ziehender, Brett Gegner) im Sockel nie "
                             "auftritt; Prior-Entropie in nat (Generator, Softmax ueber gueltige IDs); root_q wie "
                             "im Record; Differenzen Klasse minus Sockel, CI Bootstrap ueber Dateien",
                  "zeilen": {}}}
    out["M1"]["zeilen"][f"{baseline}/beide"] = m1_row(base_units)
    ua, ub = m1_units(half_a["games"], "beide", catalog), m1_units(half_b["games"], "beide", catalog)
    out["M1"][nkey] = {**m1_full(ua, ub, rng, n_boot, n_perm),
                                                      "haelfte_a": m1_row(ua), "haelfte_b": m1_row(ub)}
    for cls in classes:
        d = data[cls]
        for side in (["W", "G"] if has_special(d) else ["beide"]):
            units = m1_units(d["games"], side, catalog)
            out["M1"]["zeilen"][f"{cls}/{side}"] = {**m1_row(units),
                                                   **m1_full(units, base_units, rng, n_boot, n_perm)}
    # M2
    noise2 = out["M2"][nkey] = {}
    for k in (2, 3):
        for level in m2_levels:
            bk = board_keys_by_file(base["games"], "beide", k, level, catalog, nb)
            ha = [bk[i] for i in sorted(half_a_files)]
            hb = [bk[i] for i in sorted(half_b_files)]
            key = f"runde{k}/{level}"
            flat_b = _flat(bk)
            out["M2"]["zeilen"].setdefault(f"{baseline}/beide", {})[key] = {
                "n_bretter": len(flat_b), "n_partien": len(base["games"]),
                "distinkt_je_100_partien": 100.0 * len(set(flat_b)) / max(1, len(base["games"])),
                "distinkt_je_100_bretter": 100.0 * len(set(flat_b)) / max(1, len(flat_b))}
            noise2[key] = {
                "anteil_a_fremd_in_b": novelty(_flat(ha), _flat(hb)),
                "anteil_a_fremd_in_b_ci95": novelty_boot(ha, hb, rng, n_boot),
                "anteil_b_fremd_in_a": novelty(_flat(hb), _flat(ha)),
                "anteil_b_fremd_in_a_ci95": novelty_boot(hb, ha, rng, n_boot),
                "n_bretter_a": len(_flat(ha)), "n_bretter_b": len(_flat(hb))}
            for cls in classes:
                d = data[cls]
                for side in (["W", "G"] if has_special(d) else ["beide"]):
                    q = board_keys_by_file(d["games"], side, k, level, catalog, d["n_files"])
                    out["M2"]["zeilen"].setdefault(f"{cls}/{side}", {})[key] = m2_cell(
                        q, bk, ha, hb, len(d["games"]), rng, n_boot)
    # M3
    base_decs = m3_decisions(base, post_only=False)
    ha_decs = [(f, x) for f, x in base_decs if f in half_a_files]
    hb_decs = [(f, x) for f, x in base_decs if f in half_b_files]
    out["M3"]["zeilen"][f"{baseline}/beide"] = {"n_entscheide": len(base_decs)}
    noise3 = out["M3"][nkey] = {}
    for level in LEVELS:
        ka = [decision_key(x, level, catalog) for _f, x in ha_decs]
        kb = [decision_key(x, level, catalog) for _f, x in hb_decs]
        noise3[level] = {"anteil_a_fremd_in_b": novelty(ka, kb), "anteil_b_fremd_in_a": novelty(kb, ka),
                         "n_a": len(ka), "n_b": len(kb)}
    for cls in classes:
        d = data[cls]
        side = has_special(d)
        decs = m3_decisions(d, post_only=side)
        note = None
        if side and not decs:
            decs = m3_decisions(d, post_only=False)
            note = "keine G-Entscheide nach der Wuerfelphase; Einordnung OHNE Phasenfilter (Wuerfelphase eingeschlossen)"
        row = m3_block(decs, d["n_files"], base_decs, nb, ha_decs, hb_decs, catalog, rng, n_boot)
        if note:
            row["hinweis"] = note
        out["M3"]["zeilen"][f"{cls}/{'G' if side else 'beide'}"] = row
    out["rauschbezug_schluessel"] = nkey
    out["bezug"] = baseline
    return out


# ---------------------------------------------------------------------------------------------------------------
# Gepaarter Modus (par.5d3 Leseregel d)
# ---------------------------------------------------------------------------------------------------------------

class PairingError(SystemExit):
    """Abbruch, wenn Klasse und Bezug nicht Partie fuer Partie gepaart sind."""


def games_by_pair_key(cls_data: dict, cls: str) -> dict:
    out, missing, dup = {}, 0, []
    for g in cls_data["games"]:
        k = g["pair_key"]
        if k is None:
            missing += 1
        elif k in out:
            dup.append(k)
        else:
            out[k] = g
    if missing or dup:
        raise PairingError(f"[novelty] PAARUNG: Klasse {cls}: {missing} Partien ohne Index _cX_gY, "
                           f"doppelte Indizes {dup[:5]}")
    return out


def check_pairing(base: dict, base_name: str, cls_data: dict, cls: str) -> dict:
    """Prueft die Paarung ueber den Partie-Index und die Auslage im ersten Record (gleicher Seed, gleiche Chunkung
    ergeben dieselbe Auslage, so in S5 fuer 4 x 100 Partien gesehen). Bricht mit klarer Meldung ab."""
    a, b = games_by_pair_key(cls_data, cls), games_by_pair_key(base, base_name)
    only_a, only_b = sorted(set(a) - set(b)), sorted(set(b) - set(a))
    if only_a or only_b:
        raise PairingError(f"[novelty] PAARUNG: {cls} gegen {base_name}: Indizes nur in der Klasse {len(only_a)} "
                           f"(z. B. {only_a[:5]}), nur im Bezug {len(only_b)} (z. B. {only_b[:5]}). Gleicher Seed "
                           f"und gleiche Chunkung noetig.")
    bad = [k for k in a if not a[k]["seq"] or not b[k]["seq"] or a[k]["seq"][0][4] != b[k]["seq"][0][4]]
    if bad:
        raise PairingError(f"[novelty] PAARUNG: {cls} gegen {base_name}: {len(bad)} von {len(a)} Partien mit "
                           f"anderer Auslage im ersten Record (z. B. {sorted(bad)[:5]}). Seeds verschieden?")
    return {"n_paare": len(a), "auslage_erster_record_gleich": len(a)}


def boot_mean_ci(by_file: list, rng, n_boot) -> list | None:
    s = np.array([float(np.sum(x)) for x in by_file])
    n = np.array([len(x) for x in by_file], float)
    if n.sum() == 0:
        return None
    draws = rng.integers(0, len(by_file), size=(n_boot, len(by_file)))
    c = n[draws].sum(1)
    ok = c > 0
    vals = s[draws].sum(1)[ok] / c[ok]
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))] if vals.size else None


def _quartiles(x: list) -> dict:
    if not x:
        return {"median": None, "q25": None, "q75": None}
    return {"median": float(np.median(x)), "q25": float(np.percentile(x, 25)), "q75": float(np.percentile(x, 75))}


def divergence_summary(cls_data: dict, base_by_key: dict, side: str, rng, n_boot) -> dict:
    """P1 fuer eine Seite: erster eigener Entscheid, an dem der Zustand (eigenes Brett, Gegnerbrett, Auslage)
    von der Bezugspartie gleichen Index abweicht."""
    nf = cls_data["n_files"]
    flags = [[] for _ in range(nf)]
    ks, idxs, rounds = [], [], Counter()
    for g in cls_data["games"]:
        p = g["special"] if side == "W" else 1 - g["special"]
        dv = first_divergence(g["seq"], base_by_key[g["pair_key"]]["seq"], p)
        flags[g["file"]].append(1.0 if dv is not None else 0.0)
        if dv is not None:
            ks.append(dv["k"])
            idxs.append(dv["index"])
            rounds[str(dv["round"])] += 1
    n = sum(len(f) for f in flags)
    return {"n_partien": n, "anteil_abweichend": float(np.mean(_flat(flags))) if n else None,
            "anteil_abweichend_ci95": boot_mean_ci(flags, rng, n_boot),
            "eigene_entscheide_bis_abweichung": _quartiles(ks),
            "record_index_bis_abweichung": _quartiles(idxs),
            "runde_der_abweichung": dict(sorted(rounds.items()))}


def novelty_boot_fixed_ref(q_by_file: list, reference: list, rng, n_boot) -> list | None:
    """95-%-Intervall des Neuheitsanteils, nur die Abfrage ueber Dateien gezogen, Bezug fest (ohne die
    Aufwaertsverzerrung durch einen verkleinerten Bezugstraeger)."""
    ref = set(reference)
    flags = [[0.0 if k in ref else 1.0 for k in xs] for xs in q_by_file]
    return boot_mean_ci(flags, rng, n_boot)


def paired_analysis(data: dict, classes: list, baseline: str, catalog: dict, rng, n_boot: int) -> dict:
    """Leseregel (d) aus par.5d3: P1 erste Abweichung je Seite, P2 Anteil der G-Entscheide R2-4 nach der
    Wuerfelphase, deren Paar (eigenes Brett, Gegnerbrett) in Feinheit `slots` im gesamten Bezug fehlt."""
    base = data[baseline]
    nb = base["n_files"]
    half_a_files, half_b_files = set(range(nb // 2)), set(range(nb // 2, nb))
    base_by_key = games_by_pair_key(base, baseline)
    level = "slots"

    def key(d):
        return decision_key(d, level, catalog)
    base_decs = m3_decisions(base, post_only=False)
    ref_by_file = by_file_values(base_decs, nb, key)
    ha = [ref_by_file[i] for i in sorted(half_a_files)]
    hb = [ref_by_file[i] for i in sorted(half_b_files)]
    out = {"P1": {"grundmenge": "Partien der W-Klasse mit Bezugspartie gleichen Index (_cX_gY); je Seite die Folge "
                                "ihrer eigenen Records (Drafting und Tiling, ohne Platzwahl-Records)",
                  "einheit": "eigene Entscheide der Seite bis zur ersten Abweichung des Zustands (eigenes Brett, "
                             "Gegnerbrett, Auslage-IDs; volle Belegung), dazu Record-Index beider Spieler und Runde; "
                             "Anteil abweichender Partien mit CI Bootstrap ueber Dateien",
                  "zeilen": {}},
           "P2": {"grundmenge": "Drafting-Entscheide Runde 2-4 der G-Seite nach der Wuerfelphase (dice_phase nicht "
                                "true, ohne Platzwahl-Records); Bezug: alle Entscheide Runde 2-4 beider Seiten der "
                                f"GESAMTEN Klasse `{baseline}`",
                  "einheit": "Anteil der Entscheide, deren Paar (eigenes Brett, Gegnerbrett) in Feinheit `slots` im "
                             "Bezug fehlt; CI Bootstrap ueber Dateien (ci95: Abfrage und Bezug gezogen; "
                             "ci95_bezug_fest: nur die Abfrage)",
                  "rauschbezug_bezug_haelften": {
                      "dateien_a": f"1-{nb // 2}", "dateien_b": f"{nb // 2 + 1}-{nb}",
                      "n_a": len(_flat(ha)), "n_b": len(_flat(hb)),
                      "anteil_a_fremd_in_b": novelty(_flat(ha), _flat(hb)),
                      "anteil_a_fremd_in_b_ci95": novelty_boot(ha, hb, rng, n_boot),
                      "anteil_a_fremd_in_b_ci95_bezug_fest": novelty_boot_fixed_ref(ha, _flat(hb), rng, n_boot),
                      "anteil_b_fremd_in_a": novelty(_flat(hb), _flat(ha)),
                      "anteil_b_fremd_in_a_ci95": novelty_boot(hb, ha, rng, n_boot),
                      "anteil_b_fremd_in_a_ci95_bezug_fest": novelty_boot_fixed_ref(hb, _flat(ha), rng, n_boot)},
                  "zeilen": {}},
           "paarung": {}}
    for cls in classes:
        d = data[cls]
        out["paarung"][cls] = check_pairing(base, baseline, d, cls)
        if not has_special(d):
            continue
        out["P1"]["zeilen"][cls] = {side: divergence_summary(d, base_by_key, side, rng, n_boot) for side in ("G", "W")}
        decs = m3_decisions(d, post_only=True)
        q_by = by_file_values(decs, d["n_files"], key)
        q = _flat(q_by)
        row = {"n_entscheide": len(q), "n_bezug": len(_flat(ref_by_file)),
               "anteil_bezugsfremd": novelty(q, _flat(ref_by_file)),
               "ci95": novelty_boot(q_by, ref_by_file, rng, n_boot),
               "ci95_bezug_fest": novelty_boot_fixed_ref(q_by, _flat(ref_by_file), rng, n_boot),
               "je_runde": {str(k): novelty(_flat(by_file_values(decs, d["n_files"], key, (k,))),
                                            _flat(ref_by_file)) for k in M3_ROUNDS}}
        for name, half in (("gegen_bezugshaelfte_a", ha), ("gegen_bezugshaelfte_b", hb)):
            row[name] = {"anteil": novelty(q, _flat(half)), "ci95": novelty_boot(q_by, half, rng, n_boot),
                         "ci95_bezug_fest": novelty_boot_fixed_ref(q_by, _flat(half), rng, n_boot),
                         "n_bezug": len(_flat(half))}
        out["P2"]["zeilen"][cls] = row
    return out


def print_paired(pres: dict) -> None:
    print("\nP1 erste Abweichung gegen die Bezugspartie (eigene Entscheide der Seite; Median [Q25; Q75])", flush=True)
    for cls, sides in pres["P1"]["zeilen"].items():
        for side, r in sides.items():
            kq, iq = r["eigene_entscheide_bis_abweichung"], r["record_index_bis_abweichung"]
            print(f"  {cls:24s} {side}: n={r['n_partien']} abweichend {_fmt(r['anteil_abweichend'])} "
                  f"{_ci(r['anteil_abweichend_ci95'])} k {_fmt(kq['median'], 1)} [{_fmt(kq['q25'], 1)}; "
                  f"{_fmt(kq['q75'], 1)}] Record-Index {_fmt(iq['median'], 1)} Runden {r['runde_der_abweichung']}",
                  flush=True)
    nz = pres["P2"]["rauschbezug_bezug_haelften"]
    print("\nP2 G-Entscheide R2-4 nach der Wuerfelphase, Paar in `slots` im Bezug fehlend", flush=True)
    print(f"  Rauschbezug Haelften A in B {_fmt(nz['anteil_a_fremd_in_b'])} {_ci(nz['anteil_a_fremd_in_b_ci95'])} "
          f"(fest {_ci(nz['anteil_a_fremd_in_b_ci95_bezug_fest'])}), B in A {_fmt(nz['anteil_b_fremd_in_a'])} "
          f"{_ci(nz['anteil_b_fremd_in_a_ci95'])} (n {nz['n_a']}/{nz['n_b']})", flush=True)
    for cls, r in pres["P2"]["zeilen"].items():
        a, b = r["gegen_bezugshaelfte_a"], r["gegen_bezugshaelfte_b"]
        print(f"  {cls:24s} n={r['n_entscheide']} gesamt {_fmt(r['anteil_bezugsfremd'])} {_ci(r['ci95'])} | "
              f"gg Haelfte A {_fmt(a['anteil'])} {_ci(a['ci95'])} | gg Haelfte B {_fmt(b['anteil'])} {_ci(b['ci95'])}",
              flush=True)


def _fmt(x, nd=3):
    return "-" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.{nd}f}"


def _ci(c, nd=3):
    return "-" if not c else f"[{c[0]:.{nd}f}; {c[1]:.{nd}f}]"


def print_tables(res: dict) -> None:
    m1 = res["M1"]
    print("\nM1 Platzierungen Runde 1, JS-Distanz gegen den Bezug (Grundmenge R1-Platten je Partie und Seite)", flush=True)
    print(f"{'Zeile':28s} {'n_part':>6s} {'n_pl':>5s} {'dist':>5s} {'H_bit':>6s} {'JS':>6s} {'CI95':>17s} "
          f"{'null_q95':>8s} {'p':>6s}", flush=True)
    rows = dict(m1["zeilen"])
    rows["Rauschbezug Haelften"] = m1[res["rauschbezug_schluessel"]]
    for name, r in rows.items():
        hz = r.get("haelfte_a", r)
        pn = r.get("perm_null") or {}
        print(f"{name:28s} {hz.get('n_partien', 0):6d} {hz.get('n_platzierungen', 0):5d} "
              f"{hz.get('distinkte_tripel', 0):5d} {_fmt(hz.get('entropie_bit'), 2):>6s} {_fmt(r.get('js')):>6s} "
              f"{_ci(r.get('js_ci95')):>17s} {_fmt(pn.get('q95')):>8s} {_fmt(pn.get('p')):>6s}", flush=True)
    print("\nM2 Bretter zu Rundenbeginn, Anteil sockelfremd (Feinheit slots/plates/full)", flush=True)
    noise = res["M2"][res["rauschbezug_schluessel"]]
    for key in noise:
        print(f"  {key}: Rauschbezug A->B {_fmt(noise[key]['anteil_a_fremd_in_b'])} "
              f"B->A {_fmt(noise[key]['anteil_b_fremd_in_a'])}", flush=True)
        for name, cells in res["M2"]["zeilen"].items():
            c = cells.get(key) or {}
            if "anteil_sockelfremd" not in c:
                print(f"    {name:26s} n={c.get('n_bretter')} distinkt/100 Bretter "
                      f"{_fmt(c.get('distinkt_je_100_bretter'), 1)}", flush=True)
                continue
            print(f"    {name:26s} n={c['n_bretter']:4d} fremd {_fmt(c['anteil_sockelfremd'])} "
                  f"{_ci(c['anteil_sockelfremd_ci95'])} groessengl {_fmt(c['groessengleich_gegen_sockelhaelften'])} "
                  f"umgekehrt {_fmt(c['anteil_sockel_klassenfremd'])} distinkt/100 Bretter "
                  f"{_fmt(c['distinkt_je_100_bretter'], 1)}", flush=True)
    print("\nM3 Entscheide R2-4 (G nach der Wuerfelphase) gegen Sockel", flush=True)
    noise = res["M3"][res["rauschbezug_schluessel"]]
    print("  Rauschbezug A->B/B->A: " + ", ".join(
        f"{lv} {_fmt(v['anteil_a_fremd_in_b'])}/{_fmt(v['anteil_b_fremd_in_a'])}" for lv, v in noise.items()), flush=True)
    for name, r in res["M3"]["zeilen"].items():
        if "je_feinheit" not in r:
            print(f"  {name:28s} n={r['n_entscheide']}", flush=True)
            continue
        fe = r["je_feinheit"]
        print(f"  {name:28s} n={r['n_entscheide']:5d} fremd " + " ".join(
            f"{lv} {_fmt(fe[lv]['anteil_sockelfremd'])} {_ci(fe[lv]['anteil_sockelfremd_ci95'])}" for lv in LEVELS)
            + (f"  ({r['hinweis']})" if r.get("hinweis") else ""), flush=True)
        for k, v in r["je_runde"].items():
            pe, rq = v["prior_entropie_nat"], v["root_q"]
            print(f"      R{k}: Prior-H {_fmt(pe['mittel_a'])} gg {_fmt(pe['mittel_b'])} d {_fmt(pe['differenz'])} "
                  f"{_ci(pe['ci95'])} | root_q {_fmt(rq['mittel_a'])} gg {_fmt(rq['mittel_b'])} d "
                  f"{_fmt(rq['differenz'])} {_ci(rq['ci95'])} (n {rq['n_a']}/{rq['n_b']})", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", default="data/probe_asym")
    ap.add_argument("--classes", default=None,
                    help="Klassen neben dem Bezug; Default die S5-Klassen, mit --paired-baseline "
                         + ",".join(DEFAULT_PAIRED_CLASSES))
    ap.add_argument("--paired-baseline", default=None,
                    help="par.5d3 (d): GEPAARTER Modus gegen diese Bezugsklasse (gleicher Seed, gleiche Chunkung, "
                         "Paarung ueber _cX_gY; Abbruch, wenn sie nicht stimmt): P1 erste Abweichung je Seite, P2 "
                         "G-Entscheide mit im Bezug fehlendem slots-Paar; M1/M3 gegen diesen Bezug, M2 nur slots")
    ap.add_argument("--model", default="models/alphazero_v34-b01_brierbest.pth",
                    help="Generator (.pth) fuer die Prior-Entropie (Manifeste der Klassen: v34-b01 brierbest)")
    ap.add_argument("--no-prior", action="store_true", help="Prior-Entropie auslassen (kein Netz)")
    ap.add_argument("--batch", type=int, default=256)
    ap.add_argument("--n-boot", type=int, default=2000)
    ap.add_argument("--n-perm", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=20261004)
    ap.add_argument("--out", default="evaluations/artifacts/state_novelty_s5.json")
    args = ap.parse_args()
    t_start, c_start = time.monotonic(), time.process_time()
    rng = np.random.default_rng(args.seed)
    from corpus_io import load_records

    action_id = net_eval = None
    threads = 1
    if not args.no_prior:
        os.environ["MOSAIC_FEATURES_FROM_RUST"] = "1"  # vor dem Import von neural_net (wie asym_probe_report)
        import torch
        import neural_net
        from neural_net import action_to_id, build_model_from_checkpoint, state_to_planes, state_to_tensor
        assert neural_net._FEATURES_FROM_RUST, "Rust-Bauer nicht aktiv"
        threads = max(1, (os.cpu_count() or 2) - 1)
        torch.set_num_threads(threads)
        blob = torch.load(BASE_DIR / args.model, map_location="cpu", weights_only=False)
        model, encoder = build_model_from_checkpoint(blob)[:2]
        model.eval()

        def net_eval(states):  # gleiche Bauform wie asym_probe_report `net_eval`, nur die Logits
            with torch.no_grad():
                flat = torch.stack([state_to_tensor(d) for d in states])
                o = model(torch.stack([state_to_planes(d) for d in states]), flat) if encoder == "2d" else model(flat)
            return o[0].numpy()
        action_id = action_to_id

    data_dir = BASE_DIR / args.data_dir
    baseline = args.paired_baseline or BASELINE
    default_classes = DEFAULT_PAIRED_CLASSES if args.paired_baseline else DEFAULT_CLASSES
    classes = [c for c in (args.classes or ",".join(default_classes)).split(",") if c and c != baseline]
    catalog, conflicts, data, n_files_total = {}, set(), {}, 0
    for cls in [baseline] + classes:
        files = class_files(data_dir, cls)
        if not files:
            raise SystemExit(f"keine Dateien fuer Klasse {cls} in {args.data_dir}")
        n_files_total += len(files)
        side_field = None if cls in (baseline, "policy-s400") else SIDE_FIELD
        data[cls] = extract_class(files, side_field, catalog, conflicts, load_records, cls, t_start,
                                  action_id=action_id, net_eval=net_eval, batch=args.batch)
        data[cls]["files"] = [os.path.basename(f) for f in files]
    print(f"[novelty] Lesen fertig, Auswertung ({args.n_boot} Bootstrap, {args.n_perm} Permutationen), "
          f"{time.monotonic() - t_start:.0f} s", flush=True)
    paired = None
    if args.paired_baseline:
        for cls in classes:  # Paarung VOR jeder Rechnung pruefen
            check_pairing(data[baseline], baseline, data[cls], cls)
        paired = paired_analysis(data, classes, baseline, catalog, rng, args.n_boot)
    res = analyze(data, classes, catalog, rng, args.n_boot, args.n_perm, baseline=baseline,
                  m2_levels=("slots",) if args.paired_baseline else LEVELS)
    out = {"prereg": "evaluations/PREREG_asymmetric_selfplay.md "
                     + ("par.5d3 Leseregel (d), gepaart" if args.paired_baseline else "par.5d2"),
           "data_dir": args.data_dir, "bezug": baseline, "gepaart": bool(args.paired_baseline),
           "model": None if args.no_prior else args.model, "seed": args.seed, "n_boot": args.n_boot,
           "n_perm": args.n_perm,
           "klassen": {c: {"n_dateien": data[c]["n_files"], "n_partien": len(data[c]["games"]),
                           "dateien": data[c]["files"], "nicht_aufloesbar": data[c]["unresolved"]}
                       for c in [baseline] + classes},
           "katalog": {"platten_mit_lage": len(catalog), "konflikte": sorted(conflicts)},
           "kanonisierung": "3x3 Plaetze zeilenweise; slots = belegt ja/nein; plates = (Platten-ID, Rotation); "
                            "full = plates plus gelegte Farbe je Feld (gedrehte Reihenfolge)",
           "zusatz_nicht_registriert": "M1 Permutations-Null (Partie-Seiten zwischen Klasse und Sockel getauscht) "
                                       "und Randverteilungen; M2/M3 groessengleicher Vergleich gegen je eine "
                                       "Sockel-Haelfte",
           **res}
    if paired is not None:
        out.update(paired)
    out["laufzeit"] = laufzeit_block(t_start, cpu_start=c_start, threads=threads, n_units=n_files_total,
                                     unit="datei")
    out_path = BASE_DIR / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print_tables(res)
    if paired is not None:
        print_paired(paired)
    print(f"\n[novelty] Artefakt {args.out}, laufzeit {out['laufzeit']}", flush=True)


if __name__ == "__main__":
    main()
