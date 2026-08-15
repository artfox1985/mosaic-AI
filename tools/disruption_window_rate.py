"""PREREG_opponent_disruption_v2.md, Stufe 0 + Stufe-1-Offline-Ersatz.

Beantwortet die billige Vorfrage VOR jedem Bau: **wie oft tritt ueberhaupt ein
Stoerfenster auf?** -- also eine Wurzelentscheidung, in der ein Q-nah
gleichwertiger Alternativzug dem Gegner mehr von einer akut gebrauchten Farbe
wegnimmt, ohne die eigene Strafleiste staerker zu fuellen.

WARUM OFFLINE UND NICHT WIE VORREGISTRIERT: Stufe 1 der Vorregistrierung sah
einen Rust-Zaehlmodus plus 200 Arena-Partien vor. Beides war zum Messzeitpunkt
gesperrt (laufender Sweep: kein Wheel-Install, keine Arena). Dieser Treiber
rechnet statt dessen auf BEREITS AUFGEZEICHNETEN Self-Play-Records -- kein Bau,
kein Wheel, keine Partie. Die Naeherungen, die das kostet, stehen unten und im
Ergebnis-JSON.

Datenquelle (Default): `data/ownership_corpus/selfplay_v21_own_a_*.pkl` --
Champion `v21_2d_brierbest`, 200 Sims, `add_root_noise=true`,
`gumbel_top_m=16` (Manifest `manifest_v21_own_a_20260814_141733.json`).

NAEHERUNGEN (jede senkt oder hebt die Rate in bekannter Richtung):
 1. **Keine Besuchszahlen aufgezeichnet.** Das E3b-Aequivalenzkriterium
    (Besuchs-Gate `N(a) >= f*N(b)` + Zwei-Anteils-SE, `net_mcts.rs:3015`) ist
    offline nicht nachbildbar. Ersatz: rohes eps-Fenster (E3-Definition,
    `net_mcts.rs:2936-2978`). Kalibrierung siehe Ergebnis-Kommentar.
 2. **Der gespielte Zug steht nicht im Record** (die Suche waehlt
    besuchsbasiert). Basiszug = `argmax(completed-Q)` als Naeherung.
 3. **untried-Kandidaten werden entfernt**: sie haben keinen eigenen Besuch
    und teilen sich exakt denselben `v_mix`-Platzhalter
    (`net_mcts.rs:4456-4468`); E3 wertet nur `nodes[0].children`
    (`net_mcts.rs:2921-2935`). Erkennung ueber den exakt wiederholten Q-Wert;
    der Treiber prueft gegen `gumbel_top_m` und meldet Auffaelligkeiten.

PORTIERTE ENGINE-LOGIK (Duplikate bewusst, weil der Rust-Weg gesperrt war --
`--validate` prueft beide Portierungen gegen die Engine selbst):
 - `tiles_taken`      <- `mcts.rs:573-595`
 - Strafleisten-Zuwachs <- `mcts.rs:634-642`, `board.rs:56-67`
 - `gegner_bedarf`    <- `provocation.rs:753-779`

CLI:
    python tools/disruption_window_rate.py --validate
    python tools/disruption_window_rate.py --out evaluations/disruption_window_rate.json
"""
from __future__ import annotations

import argparse
import json
import pickle
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CORPUS = BASE_DIR / "data" / "ownership_corpus"
PATTERN = "selfplay_v21_own_a_*.pkl"
MANIFEST = "manifest_v21_own_a_20260814_141733.json"
EPS_GRID = [0.01, 0.02, 0.03]
GUMBEL_TOP_M = 16
ABBRUCH_SCHWELLE_PCT = 5.0


# ── Portierungen aus der Engine ─────────────────────────────────────────────

def tiles_taken(state, color, source, factory_id) -> int:
    """Port `mcts.rs:573-595`: wie viele Steine ein Take-Zug entnimmt.
    Mond-Oberseite = LETZTES Stapelelement (`stack.last()`)."""
    facs = state["factories"]
    lf = state["large_factory"]
    if source == "SMALL_FACTORY_SUN":
        for f in facs:
            if f["id"] == factory_id:
                return sum(1 for c in f["sun"] if c == color)
        return 0
    if source == "LARGE_FACTORY_SUN":
        return sum(1 for c in lf["sun"] if c == color)
    if source == "LARGE_FACTORY_MOON":
        return sum(1 for c in lf["moon"] if c == color)
    if source == "SMALL_FACTORY_MOON":
        if factory_id is not None:
            for f in facs:
                if f["id"] == factory_id:
                    return sum(1 for s in f["moon"] if s and s[-1] == color)
            return 0
        small = sum(1 for f in facs for s in f["moon"] if s and s[-1] == color)
        return small + sum(1 for c in lf["moon"] if c == color)
    raise ValueError(f"unbekannte Quelle {source!r}")


def floor_zuwachs(state, player, row, n) -> int:
    """Fliesen, die dieser Zug auf die Strafleiste legt.

    ABWEICHUNG VON PREREG §3 (dort: "0 fuer Bodenzuege") -- ein Bodenzug legt
    ALLE genommenen Fliesen auf die Strafleiste; 0 waere hier die falsche
    Zahl. Reihenzug: Ueberlauf nach `mcts.rs:636-638`.
    """
    if row < 0:
        return n
    pl = state["players"][player]["pattern_lines"][row]
    return max(0, n - (pl["capacity"] - len(pl["tiles"])))


def gegner_bedarf(state, aktueller_spieler):
    """Port `provocation.rs:753-779`. Rueckgabe `(akut, voll)`:
    `akut` = nur Musterreihen-Anteil (`provocation.rs:759-764`),
    `voll` = zzgl. offene Kuppelzellen mit Farbforderung (`:765-777`)."""
    akut, voll = Counter(), Counter()
    gegner = state["players"][1 - aktueller_spieler]
    for line in gegner["pattern_lines"]:
        if line["color"] is not None:
            akut[line["color"]] += line["capacity"] - len(line["tiles"])
    voll.update(akut)
    for row in gegner["dome_grid"]:
        for slot in row:
            if not slot:
                continue
            for sp in slot["spaces"]:
                if not sp.get("filled") and sp.get("color") is not None:
                    voll[sp["color"]] += 1
    return akut, voll


# ── Kandidatenaufbereitung ──────────────────────────────────────────────────

def vm_index(state):
    """`(color, row, factory_key) -> (source, factory_id)` aus
    `state['valid_moves']`. Join OHNE `moon_order`: die Suche zaehlt
    Moon-Order-Permutationen als eigene Kandidaten, `valid_moves` nicht.
    Geprueft: 193.319/193.319 Treffer, Quelle je Schluessel eindeutig."""
    idx = {}
    for m in state.get("valid_moves") or []:
        if m.get("type") != "stone":
            continue
        src, fid = m.get("source"), m.get("factory_id")
        key_fid = "LARGE" if src == "LARGE_FACTORY_SUN" else ("GLOBAL_MOON" if fid is None else fid)
        idx[(m["color"], m["row"], key_fid)] = (src, fid)
    return idx


def policy_key(state, a):
    """`factory_index` ist die POSITION in `state['factories']`
    (`self_play.rs:196-217`), 4 = Grossfabrik-Sonne, 5 = globaler Mondzug."""
    fi = a.get("factory_index")
    facs = state["factories"]
    if fi is not None and 0 <= fi < len(facs):
        return (a.get("color"), a.get("row"), facs[fi]["id"])
    if fi == 4:
        return (a.get("color"), a.get("row"), "LARGE")
    if fi == 5:
        return (a.get("color"), a.get("row"), "GLOBAL_MOON")
    return (a.get("color"), a.get("row"), fi)


def children_indices(rcq):
    """Indizes der echten Wurzelkinder (ohne die `v_mix`-Gruppe).
    Rueckgabe `(indices, verdaechtig)`."""
    n = len(rcq)
    if n <= GUMBEL_TOP_M:
        return list(range(n)), False
    val, c = Counter(rcq).most_common(1)[0]
    if c < 2:
        return list(range(n)), True
    idx = [i for i, q in enumerate(rcq) if q != val]
    return idx, len(idx) > GUMBEL_TOP_M


# ── Gegenprobe der Portierungen ─────────────────────────────────────────────

LOG_LINE = re.compile(
    r"(?P<n>\d+)×\s+(?P<color>\S+)\s+(?:von|vom)\s+(?P<src>F\d+|GF|Mondpool)\s+→\s+"
    r"(?P<dest>Reihe \d+|Strafleiste)(?:\s+\[\d+/\d+\])?"
    r"(?:\s+\(\+(?P<of>\d+) Strafleiste\))?"
)


def validate(files):
    """Zwei unabhaengige Gegenproben, bevor irgendeine Rate berichtet wird.

    A) Spiel-Log: zwei aufeinanderfolgende Records derselben Partie
       unterscheiden sich um genau eine Log-Zeile -- die vom ECHTEN Vollzug
       gebaute Zeile (`execution.rs:38-46`). Stueckzahl und
       Strafleisten-Zuwachs der Portierung muessen sie treffen.
    B) `moon_top_counts` (`serialize.rs:215-228`) ist per Konstruktion exakt
       `tiles_taken` des globalen Mondzugs -- ein vom Suchpfad unabhaengiger
       Serializer-Zweig.
    """
    a_ok = a_bad = b_ok = b_bad = 0
    quellen = Counter()
    beispiele = []
    for f in files:
        recs = pickle.load(open(f, "rb"))
        for r in recs:
            st = r.get("state") or {}
            if st.get("phase") != "drafting":
                continue
            for color, exp in (st.get("moon_top_counts") or {}).items():
                if tiles_taken(st, color, "SMALL_FACTORY_MOON", None) == exp:
                    b_ok += 1
                else:
                    b_bad += 1
        for a, b in zip(recs, recs[1:]):
            if a.get("game_id") != b.get("game_id"):
                continue
            la, lb = a["state"].get("log") or [], b["state"].get("log") or []
            if len(lb) != len(la) + 1:
                continue
            m = LOG_LINE.search(lb[-1])
            st = a["state"]
            if not m or st.get("phase") != "drafting":
                continue
            color, n_log = m.group("color"), int(m.group("n"))
            of_log = int(m.group("of") or 0)
            dest = m.group("dest")
            row = -1 if dest == "Strafleiste" else int(dest.split()[1]) - 1
            lbl = m.group("src")
            key_fid = "LARGE" if lbl == "GF" else ("GLOBAL_MOON" if lbl == "Mondpool" else int(lbl[1:]))
            hit = vm_index(st).get((color, row, key_fid))
            if hit is None:
                continue
            src, fid = hit
            quellen[src] += 1
            n_calc = tiles_taken(st, color, src, fid)
            of_calc = floor_zuwachs(st, st["current_player"], row, n_calc)
            good = n_calc == n_log and (row < 0 or of_calc == of_log)
            if good:
                a_ok += 1
            else:
                a_bad += 1
                if len(beispiele) < 5:
                    beispiele.append({"zeile": lb[-1], "n_calc": n_calc, "n_log": n_log,
                                      "of_calc": of_calc, "of_log": of_log})
    return {
        "log_gegenprobe_ok": a_ok,
        "log_gegenprobe_abweichend": a_bad,
        "log_gegenprobe_quellen": dict(quellen),
        "moon_top_counts_gegenprobe_ok": b_ok,
        "moon_top_counts_gegenprobe_abweichend": b_bad,
        "abweichungs_beispiele": beispiele,
    }


# ── Hauptlauf ───────────────────────────────────────────────────────────────

def analyse(files, verbose=True):
    tot = 0
    suspicious = 0
    per_round = Counter()
    cand_hist = Counter()
    fenster = Counter()
    stoerbar = Counter()
    stoerbar_nofloor = Counter()
    stoerbar_voll = Counter()
    stoerbar_runde = defaultdict(Counter)
    mit_wahl = 0

    for i, f in enumerate(files):
        for r in pickle.load(open(f, "rb")):
            rcq = r.get("root_child_q")
            if not rcq or len(rcq) != len(r["policy"]):
                continue
            st = r["state"]
            idxs, susp = children_indices(rcq)
            suspicious += bool(susp)
            if not idxs:
                continue
            me = st["current_player"]
            akut, voll = gegner_bedarf(st, me)
            vmi = vm_index(st)
            cands = []
            for j in idxs:
                a = r["policy"][j]["action"]
                if a.get("type") != "stone":
                    continue
                hit = vmi.get(policy_key(st, a))
                if hit is None:
                    continue
                src, fid = hit
                n = tiles_taken(st, a["color"], src, fid)
                cands.append({
                    "q": rcq[j],
                    "n": n,
                    "akut": min(n, akut.get(a["color"], 0)),
                    "voll": min(n, voll.get(a["color"], 0)),
                    "floor": floor_zuwachs(st, me, a["row"], n),
                })
            if not cands:
                continue
            tot += 1
            per_round[st.get("round")] += 1
            cand_hist[min(len(cands), GUMBEL_TOP_M)] += 1
            if len(cands) > 1:
                mit_wahl += 1
            base = max(cands, key=lambda c: c["q"])
            qb = base["q"]
            for eps in EPS_GRID:
                win = [c for c in cands if c is not base and c["q"] >= qb - eps]
                if not win:
                    continue
                fenster[eps] += 1
                if any(c["akut"] > base["akut"] for c in win):
                    stoerbar_nofloor[eps] += 1
                if any(c["akut"] > base["akut"] and c["floor"] <= base["floor"] for c in win):
                    stoerbar[eps] += 1
                    stoerbar_runde[eps][st.get("round")] += 1
                if any(c["voll"] > base["voll"] and c["floor"] <= base["floor"] for c in win):
                    stoerbar_voll[eps] += 1
        if verbose and (i + 1) % 50 == 0:
            print(f"  ... {i+1}/{len(files)} Dateien, {tot} Entscheidungen", flush=True)

    def pct(x, d=None):
        d = d if d is not None else tot
        return round(100 * x / d, 2) if d else None

    raten = {}
    for eps in EPS_GRID:
        raten[str(eps)] = {
            "fenster_pct": pct(fenster[eps]),
            "stoerbar_n": stoerbar[eps],
            "stoerbar_pct": pct(stoerbar[eps]),
            "stoerbar_pct_nur_entscheidungen_mit_wahl": pct(stoerbar[eps], mit_wahl),
            "stoerbar_pct_ohne_strafleisten_filter": pct(stoerbar_nofloor[eps]),
            "stoerbar_pct_bedarf_inkl_kuppelzellen": pct(stoerbar_voll[eps]),
            "stoerbar_je_runde": dict(sorted(stoerbar_runde[eps].items(),
                                             key=lambda kv: (kv[0] is None, kv[0]))),
        }
    return {
        "entscheidungen_gesamt": tot,
        "entscheidungen_mit_echter_wahl": mit_wahl,
        "entscheidungen_je_runde": dict(sorted(per_round.items(),
                                               key=lambda kv: (kv[0] is None, kv[0]))),
        "kandidaten_histogramm": dict(sorted(cand_hist.items())),
        "verdaechtige_kandidatenmengen": suspicious,
        "raten": raten,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--files", type=int, default=None, help="nur die ersten N Korpusdateien")
    ap.add_argument("--validate-files", type=int, default=20, help="Dateien fuer die Gegenprobe")
    ap.add_argument("--validate", action="store_true", help="nur die Gegenprobe fahren")
    ap.add_argument("--out", type=Path, default=None, help="Ergebnis-JSON")
    args = ap.parse_args(argv)

    files = sorted(CORPUS.glob(PATTERN))
    if not files:
        print(f"FEHLER: keine Korpusdateien unter {CORPUS / PATTERN}", file=sys.stderr)
        return 2
    if args.files:
        files = files[: args.files]

    print(f"Gegenprobe der Portierungen ueber {min(args.validate_files, len(files))} Dateien ...", flush=True)
    val = validate(files[: args.validate_files])
    print(json.dumps(val, indent=1, ensure_ascii=False))
    if val["log_gegenprobe_abweichend"] or val["moon_top_counts_gegenprobe_abweichend"]:
        print("ABBRUCH: die Portierung weicht von der Engine ab -- keine Rate berichten.", file=sys.stderr)
        return 1
    if val["log_gegenprobe_ok"] == 0 or val["moon_top_counts_gegenprobe_ok"] == 0:
        print("ABBRUCH: INSTRUMENT KAPUTT (keine einzige Gegenprobe zustande gekommen).", file=sys.stderr)
        return 1
    if args.validate:
        return 0

    print(f"Analyse ueber {len(files)} Dateien ...", flush=True)
    res = analyse(files)
    res["gegenprobe"] = val
    res["quelle"] = {
        "glob": str(CORPUS / PATTERN),
        "dateien": len(files),
        "manifest": MANIFEST,
        "modell": "v21_2d_brierbest",
        "sims": 200,
        "add_root_noise": True,
        "gumbel_top_m": GUMBEL_TOP_M,
    }
    res["abbruchregel"] = {
        "schwelle_pct": ABBRUCH_SCHWELLE_PCT,
        "primaeres_eps": 0.01,
        "unterschritten": res["raten"]["0.01"]["stoerbar_pct"] < ABBRUCH_SCHWELLE_PCT,
    }
    print(json.dumps(res, indent=1, ensure_ascii=False))
    if args.out:
        args.out.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"geschrieben: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
