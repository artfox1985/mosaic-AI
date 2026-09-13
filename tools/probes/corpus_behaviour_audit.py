# -*- coding: utf-8 -*-
"""Verhaltens-Audit ueber den Self-Play-Korpus (Arme A1, A2, B, C).

Vorregistriert in `evaluations/PREREG_corpus_behaviour_audit.md` par.2/par.3.
Gefragt ist, ob drei Muster, die beim Spielen gegen den Champion auffielen, sich
auch im Korpus zeigen und in welcher Groessenordnung.

**Die Quelle sind die RECORDS, nicht Partielogs** (par.3, GEPRUEFT 2026-09-11):
`--log-games` ist ein Arena-Flag, `self_play.py` schreibt keine Partielogs. Jeder
Record traegt aber `state.log`, ein mitlaufendes FENSTER der letzten rund 30
Zeilen; da es je Zug einen Record gibt, ueberlappen sich die Fenster. Wer sie
UEBERLAPPEND zusammensetzt, bekommt den vollstaendigen Log zurueck -- ein `set`
verliert die Wiederholungen (gemessen: 1 bis 6 Zeilen je Partie).

Die Arme:

* **A1 Ziehungen je Plattenplatzierung, BEDINGT auf den Punktestand.** Aufgeteilt
  nach Stand 0 und Stand > 0 VOR der ersten Ziehung der Serie. Die Konfundierung
  ist benannt (par.2): wer bei 0 steht, steht meist schlecht; die Frage ist nicht,
  OB schlechte Lagen mehr ziehen, sondern ob die Ziehzahl an der 0-Grenze SPRINGT.
* **A2 Zwangsraeumungen**, aufgeschluesselt nach Musterreihe und Runde.
* **B Sturz auf 0 in RUNDE 1 gegen Siegquote.** Runde 1, weil dort jede Seite bei
  5 Punkten startet und der einzige Weg nach unten die eigenen Ziehungen sind --
  das schliesst den Rueckwaerts-Konfounder weitgehend aus. Spaetere Runden werden
  getrennt ausgewiesen, aber nicht als Beleg verwendet.
* **C Plattenkonditionierung**: Zielstrukturen mit und ohne die passende
  Wertungsplatte.

Auswertung auf BLOCK-Ebene (Blockgroesse 5), wie fuer jede Score-Analyse in
diesem Projekt vorgeschrieben.

Aufruf:
    python -X utf8 -u tools/probes/corpus_behaviour_audit.py \\
        --files data/selfplay_v29-*.pkl \\
        --out evaluations/artifacts/corpus_behaviour_v29.json

Rechenlast: nur Lesen und Zaehlen, kein Netz, keine Suche, keine Arena.
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import re
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "engine" / "py"))

import corpus_io  # noqa: E402

BLOCK_SIZE = 5
# Punktestand, mit dem jede Seite in die Partie geht (docs/engine_manual.md;
# par.2 Arm B: "dort startet jede Seite bei 5 Punkten").
START_SCORE = 5

# Die Logzeilen tragen ein Rundenpraefix ("[R2] ..."), die Muster in
# tools/analyze_game_log.py sind ohne dieses Praefix verankert. Deshalb hier
# eigene Muster, die es mitlesen statt es wegzuwerfen: die Runde ist fuer A2
# und B eine Auswertungsdimension.
RE_ROUND_PREFIX = re.compile(r"^\[R(?P<round>\d+)\]\s*")

# "[R2] 📦 Netz: 1. Kachel vom Stapel gezogen (Rueckseite: Special) -1 Pkt -> 7 Gesamt"
# Das Minus ist ein UNICODE-Minus (U+2212), der Pfeil U+2192; beide sind unten
# ausdruecklich zugelassen, damit ein ASCII-Log nicht still durchfaellt.
RE_STACK_DRAW = re.compile(
    r"\U0001F4E6\s*(?P<name>.+?):\s*(?P<n>\d+)\.\s*Kachel vom Stapel gezogen"
    r"(?:\s*\((?:Rückseite|Rueckseite):\s*(?P<back>[^)]+)\))?"
    r"(?:\s*(?P<delta>[−+-]?\d+)\s*Pkt)?"
    r"(?:\s*[→>-]+\s*(?P<total>[−-]?\d+)\s*Gesamt)?"
)

# Jede Zeile, die einen Punktestand fortschreibt ("... -> 7 Gesamt"): Ziehung,
# Strafe, Tiling-Wertung. Daraus wird je Spieler der LAUFENDE Stand gefuehrt.
#
# Warum das noetig ist (Befund 2026-09-13, beim Selbsttest gefunden): der Stand
# ist bei 0 GECLAMPT. Die Engine schreibt auch dann weiter "-1 Pkt", der Stand
# bleibt aber 0 -- gemessen 66 von 324 Ziehzeilen in sechs Korpusdateien. Wer
# den Stand vor einer Ziehung als `total - delta` rechnet, haelt jede dieser
# Gratis-Ziehungen faelschlich fuer bezahlt und sieht ausserdem nie eine Serie,
# die bei 0 STARTET (sie sieht dort 1). Genau die beiden Zahlen, nach denen
# par.2 fragt, waeren damit kaputt.
RE_SCORE_UPDATE = re.compile(
    r"(?P<name>[^:\[\]]+?):\s.*?[\u2192>-]+\s*(?P<total>[\u2212-]?\d+)\s*Gesamt"
)

# "[R4] ⚠️  Netz: Musterreihe 4 (gelb) nicht platzierbar -> 2x Strafleiste"
RE_FORCED_CLEAR = re.compile(
    r"⚠️?\s*(?P<name>.+?):\s*Musterreihe\s*(?P<row>\d+)"
    r"(?:\s*\((?P<color>[^)]+)\))?\s*nicht platzierbar"
    r"(?:\s*[→>-]+\s*(?P<tiles>\d+)\s*[×x]\s*Strafleiste)?"
)


def to_int(text: str | None) -> int | None:
    """Zahl mit moeglichem Unicode-Minus."""
    if text is None:
        return None
    return int(text.replace("−", "-").replace("+", ""))


def join_overlapping(windows: list[list[str]]) -> list[str]:
    """Setzt aufeinanderfolgende Logfenster ueber ihre Ueberlappung zusammen.

    Jedes Fenster ist das Ende des vollstaendigen Logs zu seinem Zeitpunkt.
    Fuer jedes neue Fenster wird der laengste Suffix des bisherigen Logs
    gesucht, der ein Praefix des Fensters ist; nur der Rest wird angehaengt.
    Ein `set` waere falsch: gleiche Zeilen kommen in einer Partie mehrfach vor
    (par.3).
    """
    out: list[str] = []
    for w in windows:
        if not w:
            continue
        if not out:
            out.extend(w)
            continue
        max_k = min(len(out), len(w))
        k = 0
        for cand in range(max_k, 0, -1):
            if out[-cand:] == w[:cand]:
                k = cand
                break
        out.extend(w[k:])
    return out


def split_round(line: str) -> tuple[int | None, str]:
    """Trennt das Rundenpraefix ab und gibt (Runde, Rest)."""
    m = RE_ROUND_PREFIX.match(line)
    if not m:
        return None, line
    return int(m.group("round")), line[m.end():]


class GameAudit:
    """Zaehlungen einer einzelnen Partie."""

    def __init__(self, game_id, names: list[str]):
        self.game_id = game_id
        self.names = names
        # A1: je Serie ein Eintrag (Name, Runde, Stand vorher, Ziehungen).
        self.draw_series: list[dict] = []
        # A2: je Vorfall ein Eintrag.
        self.forced_clears: list[dict] = []
        # B: je Seite, ob sie in Runde r auf <= 0 faellt.
        self.zero_round: dict[str, int | None] = {}
        self.scores: list[int] = []
        self.winner: int | None = None
        self.scoring_tile_ids: list[int] = []
        self.completed = False

    def read_log(self, lines: list[str]) -> None:
        """Liest den zusammengesetzten Log und fuellt A1, A2 und B.

        Der Punktestand wird je Spieler LAUFEND mitgefuehrt (aus jeder Zeile,
        die ihn fortschreibt), nicht aus der einzelnen Ziehzeile zurueckgerechnet
        -- der Stand ist bei 0 geclampt, siehe RE_SCORE_UPDATE.
        """
        current: dict | None = None
        # Jede Seite startet mit START_SCORE Punkten (Regel; par.2 Arm B nennt
        # sie ausdruecklich). Ohne diese Vorbelegung haetten die Serien VOR der
        # ersten Punktzeile keinen Stand und fielen aus A1 heraus.
        score: dict[str, int] = {n: START_SCORE for n in self.names}
        for raw in lines:
            rnd, text = split_round(raw)

            m = RE_STACK_DRAW.search(text)
            if m:
                name = m.group("name").strip()
                n = int(m.group("n"))
                total = to_int(m.group("total"))
                before = score.get(name)
                if n == 1 or current is None or current["name"] != name:
                    current = {
                        "name": name,
                        "round": rnd,
                        "score_before": before,
                        "draws": 0,
                        "paid": 0,
                        "free": 0,
                        "backs": [],
                    }
                    self.draw_series.append(current)
                current["draws"] = max(current["draws"], n)
                # Bezahlt, wenn der Stand VOR dieser Ziehung ueber 0 lag; bei 0
                # ist sie umsonst, auch wenn die Zeile weiter "-1 Pkt" schreibt.
                if before is not None:
                    if before > 0:
                        current["paid"] += 1
                    else:
                        current["free"] += 1
                if m.group("back"):
                    current["backs"].append(m.group("back").strip())
                if total is not None:
                    score[name] = total
                    if total <= 0:
                        prev = self.zero_round.get(name)
                        if rnd is not None and (prev is None or rnd < prev):
                            self.zero_round[name] = rnd
                continue

            # Keine Ziehzeile: Stand trotzdem fortschreiben, wenn die Zeile ihn
            # nennt (Strafe, Tiling-Wertung, Endwertung).
            ms = RE_SCORE_UPDATE.search(text)
            if ms:
                total = to_int(ms.group("total"))
                if total is not None:
                    score[ms.group("name").strip()] = total

            m = RE_FORCED_CLEAR.search(text)
            if m:
                self.forced_clears.append(
                    {
                        "name": m.group("name").strip(),
                        "round": rnd,
                        "row": int(m.group("row")),
                        "color": (m.group("color") or "").strip() or None,
                        "tiles": to_int(m.group("tiles")) or 0,
                    }
                )
                current = None
                continue

            # Jede andere Zeile beendet eine laufende Ziehserie.
            current = None


def audit_file(path: Path, limit_games: int | None = None) -> list[GameAudit]:
    records = corpus_io.load_records(path)
    if isinstance(records, dict):
        records = records.get("records", [])
    by_game: "collections.OrderedDict[object, list]" = collections.OrderedDict()
    for r in records:
        if isinstance(r, dict):
            by_game.setdefault(r.get("game_id"), []).append(r)

    games: list[GameAudit] = []
    for gid, recs in by_game.items():
        if limit_games is not None and len(games) >= limit_games:
            break
        last = recs[-1]
        state = last.get("state") or {}
        names = [p.get("name", f"P{i}") for i, p in enumerate(state.get("players") or [])]
        g = GameAudit(gid, names)
        g.scores = list(last.get("scores") or [])
        g.winner = last.get("winner")
        g.completed = bool(last.get("completed"))
        g.scoring_tile_ids = list(state.get("scoring_tile_ids") or [])
        g.read_log(join_overlapping([r.get("state", {}).get("log") or [] for r in recs]))
        games.append(g)
    return games


def blocks(items: list, size: int = BLOCK_SIZE) -> list[list]:
    return [items[i:i + size] for i in range(0, len(items), size)]


def summarize(values: list[float]) -> dict:
    if not values:
        return {"n": 0, "mittel": None, "median": None, "max": None}
    return {
        "n": len(values),
        "mittel": round(statistics.fmean(values), 4),
        "median": round(statistics.median(values), 4),
        "max": round(max(values), 4),
    }


def arm_a1(games: list[GameAudit]) -> dict:
    """Ziehungen je Serie, getrennt nach Stand 0 und Stand > 0 VOR der Serie
    (der registrierte Zuschnitt, par.2), PLUS der Aufschluesselung in bezahlte
    und gratis Ziehungen INNERHALB der Serie.

    Warum die Ergaenzung (Befund 2026-09-13): im Korpus startet praktisch keine
    Serie bei Stand 0 -- der Stand erholt sich zwischen den Zuegen durch die
    Wertung. Die registrierte Zweiteilung hat damit eine leere Haelfte und kann
    die Frage von par.2 ("springt die Ziehzahl an der 0-Grenze?") nicht
    beantworten. Was im Korpus tatsaechlich passiert, ist das Muster aus g07:
    der Spieler zahlt sich INNERHALB einer Serie auf 0 herunter und zieht dann
    gratis weiter. Genau diese beiden Zahlen werden hier zusaetzlich berichtet;
    die registrierte Zweiteilung bleibt unveraendert stehen, ihre leere Haelfte
    IST ein Befund.
    """
    at_zero: list[int] = []
    above: list[int] = []
    unknown = 0
    paid: list[int] = []
    free: list[int] = []
    free_series = 0
    total_series = 0
    by_score_before: dict[int, list[int]] = {}
    for g in games:
        for s in g.draw_series:
            total_series += 1
            if s["score_before"] is None:
                unknown += 1
            elif s["score_before"] <= 0:
                at_zero.append(s["draws"])
            else:
                above.append(s["draws"])
                by_score_before.setdefault(s["score_before"], []).append(s["draws"])
            paid.append(s["paid"])
            free.append(s["free"])
            if s["free"] > 0:
                free_series += 1
    return {
        "grundmenge": "Ziehserien je Seite und Runde",
        "einheit": "Ziehungen je Plattenplatzierung",
        "stand_null": summarize(at_zero),
        "stand_ueber_null": summarize(above),
        "ohne_standangabe": unknown,
        "ergaenzung_bezahlt_gratis": {
            "warum": "im Korpus startet kaum eine Serie bei 0; der Sturz passiert INNERHALB der Serie",
            "bezahlte_ziehungen": summarize([float(x) for x in paid]),
            "gratis_ziehungen": summarize([float(x) for x in free]),
            "serien_mit_gratis_ziehungen": free_series,
            "serien_gesamt": total_series,
            "anteil_serien_mit_gratis": (
                round(free_series / total_series, 4) if total_series else None
            ),
        },
        "ziehungen_nach_stand_vorher": {
            str(k): summarize([float(x) for x in v])
            for k, v in sorted(by_score_before.items())
        },
    }


def arm_a2(games: list[GameAudit]) -> dict:
    """Zwangsraeumungen je Partie, nach Musterreihe und Runde."""
    per_game: list[int] = []
    by_row: collections.Counter = collections.Counter()
    by_round: collections.Counter = collections.Counter()
    tiles: list[int] = []
    for g in games:
        per_game.append(len(g.forced_clears))
        for fc in g.forced_clears:
            by_row[fc["row"]] += 1
            if fc["round"] is not None:
                by_round[fc["round"]] += 1
            tiles.append(fc["tiles"])
    return {
        "grundmenge": "Partien",
        "einheit": "Vorfaelle je Partie, Steine je Vorfall",
        "vorfaelle_je_partie": summarize([float(x) for x in per_game]),
        "steine_je_vorfall": summarize([float(x) for x in tiles]),
        "nach_musterreihe": dict(sorted(by_row.items())),
        "nach_runde": dict(sorted(by_round.items())),
    }


def arm_b(games: list[GameAudit]) -> dict:
    """Siegquote, gruppiert nach Sturz auf 0 in Runde 1. Auf Blockebene."""
    rows: list[tuple[bool, int]] = []  # (faellt in R1 auf 0, Sieg)
    later: list[tuple[bool, int]] = []
    for g in games:
        if not g.completed or g.winner is None or len(g.names) < 2:
            continue
        for idx, name in enumerate(g.names):
            won = 1 if g.winner == idx else 0
            zr = g.zero_round.get(name)
            rows.append((zr == 1, won))
            later.append((zr is not None and zr > 1, won))

    def rate(pairs: list[tuple[bool, int]], flag: bool) -> dict:
        sel = [w for f, w in pairs if f == flag]
        return {"n": len(sel), "siegquote": round(sum(sel) / len(sel), 4) if sel else None}

    # Blockweise, damit die Differenz eine Streuung bekommt (Blockgroesse 5
    # Partien = 10 Seiten).
    per_block = []
    for blk in blocks(rows, BLOCK_SIZE * 2):
        a = [w for f, w in blk if f]
        b = [w for f, w in blk if not f]
        if a and b:
            per_block.append(sum(a) / len(a) - sum(b) / len(b))
    return {
        "grundmenge": "Seiten (zwei je Partie)",
        "einheit": "Siege je Seite",
        "sturz_in_runde_1": rate(rows, True),
        "kein_sturz_in_runde_1": rate(rows, False),
        "sturz_spaeter_nur_nachrichtlich": rate(later, True),
        "blockdifferenz": summarize(per_block),
        "bloecke": len(per_block),
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--files",
        nargs="+",
        required=True,
        help="Korpusdateien oder Glob-Muster (z.B. 'data/selfplay_v29-*.pkl')",
    )
    ap.add_argument(
        "--limit-games",
        type=int,
        default=None,
        help="Nur die ersten N Partien JE DATEI lesen (Probelauf)",
    )
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    paths: list[Path] = []
    for pattern in a.files:
        hits = sorted(glob.glob(pattern))
        paths.extend(Path(h) for h in hits) if hits else paths.append(Path(pattern))
    paths = [p for p in paths if p.exists()]
    if not paths:
        raise SystemExit(
            f"keine Datei zu {a.files} gefunden -- der Lauf darf nicht leer gruen durchgehen."
        )

    t0 = time.time()
    games: list[GameAudit] = []
    for i, p in enumerate(paths, 1):
        games.extend(audit_file(p, a.limit_games))
        if i % 25 == 0 or i == len(paths):
            print(
                f"  {i}/{len(paths)} Dateien, {len(games)} Partien "
                f"({time.time() - t0:.1f}s)",
                flush=True,
            )
    if not games:
        raise SystemExit("keine Partien gelesen -- kein stiller Skip.")

    out = {
        "dateien": len(paths),
        "partien": len(games),
        "block_size": BLOCK_SIZE,
        "arm_a1_ziehsucht": arm_a1(games),
        "arm_a2_zwangsraeumungen": arm_a2(games),
        "arm_b_null_sturz": arm_b(games),
    }

    a1 = out["arm_a1_ziehsucht"]
    print(f"\n== A1 Ziehungen je Serie ({len(games)} Partien)")
    print(f"   Stand 0:    {a1['stand_null']}")
    print(f"   Stand > 0:  {a1['stand_ueber_null']}")
    erg = a1["ergaenzung_bezahlt_gratis"]
    print(f"   bezahlt:    {erg['bezahlte_ziehungen']}")
    print(f"   gratis:     {erg['gratis_ziehungen']}")
    print(
        f"   Serien mit Gratis-Ziehungen: {erg['serien_mit_gratis_ziehungen']}"
        f"/{erg['serien_gesamt']} ({erg['anteil_serien_mit_gratis']})"
    )
    a2 = out["arm_a2_zwangsraeumungen"]
    print("\n== A2 Zwangsraeumungen")
    print(f"   je Partie:  {a2['vorfaelle_je_partie']}")
    print(f"   nach Reihe: {a2['nach_musterreihe']}")
    print(f"   nach Runde: {a2['nach_runde']}")
    b = out["arm_b_null_sturz"]
    print("\n== B Sturz auf 0 in Runde 1")
    print(f"   mit Sturz:  {b['sturz_in_runde_1']}")
    print(f"   ohne:       {b['kein_sturz_in_runde_1']}")
    print(f"   Blockdiff:  {b['blockdifferenz']} ueber {b['bloecke']} Bloecke")

    wall = time.time() - t0
    out["laufzeit"] = {
        "wanduhr_s": round(wall, 1),
        "cpu_s": round(time.process_time(), 1),
        "threads": 1,
        "s_je_partie": round(wall / len(games), 4),
    }
    if a.out:
        Path(a.out).write_text(
            json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
        )
        print(f"\nArtefakt: {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
