# -*- coding: utf-8 -*-
"""Wieviel Stellungsvielfalt kostet der v2-Vorzug?

ANLASS 2026-08-25: der Vorzug setzt den Zug OHNE Suche und ohne Sampling und
umgeht damit `play_temp` (self_play.rs:374) auf rund 62 Prozent der
Draftingzuege. `play_temp` existiert genau fuer Zustandsvielfalt -- die Frage
ist also, wieviel Abdeckung der Korpus dadurch verliert. Der Value-Kopf, fuer
den v22 gebaut wird, lernt aus Zustaenden.

Gemessen wird die Brett-Belegung, NICHT der ganze Zustand: Fabriken und Beutel
wuerfeln ohnehin je Partie, dadurch waere praktisch jeder Zustand einmalig und
die Zahl wertlos. Kanonische Form je Record und Seite ist die 36-Bit-Maske der
gefuellten Kuppelfelder, plus die Runde.

Aufruf:
    python -X utf8 tools/probes/corpus_state_diversity_probe.py <dir_a> <dir_b> [n_partien] [out]
"""
import collections, glob, json, os, pathlib, sys, time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from corpus_io import load_records


def fill_mask(player):
    """36-Bit-Maske der gefuellten Kuppelfelder (3x3 Slots a 4 Felder).

    Der Bit-Index ist FEST an (slot_row, slot_col, space) gebunden, nicht
    fortlaufend gezaehlt: in fruehen Zustaenden sind noch nicht alle Slots
    belegt (`None`), und ein fortlaufender Zaehler wuerde die Maske dadurch
    verschieben -- gleiche Belegung saehe je nach Slot-Fuellstand anders aus.
    """
    m = 0
    grid = player.get("dome_grid") or []
    for sr in range(3):
        zeile = grid[sr] if sr < len(grid) else []
        for sc in range(3):
            slot = zeile[sc] if sc < len(zeile) else None
            spaces = (slot or {}).get("spaces") or []
            for si in range(4):
                sp = spaces[si] if si < len(spaces) else None
                if sp and sp.get("filled"):
                    m |= 1 << (sr * 12 + sc * 4 + si)
    return m


def auswerten(verzeichnis, n_partien):
    spiele = collections.defaultdict(list)
    # Ueber `load_records`, NICHT roh per `pickle.load`: seit corpus_io die
    # Korpus-Dateien gzip-komprimiert schreibt (Endung bleibt .pkl, erkannt
    # wird am Inhalt) starb diese Sonde an jedem heutigen Korpus mit
    # UnpicklingError. Bestandsdateien ohne gzip liest derselbe Aufruf weiter.
    for f in sorted(glob.glob(os.path.join(verzeichnis, "*.pkl"))):
        for r in load_records(f):
            spiele[r.get("game_id")].append(r)
    ids = sorted(spiele)[:n_partien]

    alle = collections.Counter()          # (runde, maske) -> Haeufigkeit
    je_partie = []                        # distinkte Masken je Partie
    endbretter = set()
    records = 0
    for gid in ids:
        lokal = set()
        for r in spiele[gid]:
            st = r.get("state") or {}
            rd = st.get("round")
            for p in st.get("players", []):
                k = (rd, fill_mask(p))
                alle[k] += 1
                lokal.add(k)
            records += 1
        je_partie.append(len(lokal))
        letzte = spiele[gid][-1]
        for p in (letzte.get("state") or {}).get("players", []):
            endbretter.add(fill_mask(p))

    geteilt = sum(1 for k, v in alle.items() if v > 1)
    return {
        "verzeichnis": verzeichnis,
        "partien": len(ids),
        "records": records,
        "distinkte_zustaende": len(alle),
        "distinkte_je_partie": sum(je_partie) / len(je_partie),
        "distinkte_je_record": len(alle) / records,
        "mehrfach_vorkommend": geteilt,
        "mehrfach_anteil": geteilt / len(alle),
        "distinkte_endbretter": len(endbretter),
        "endbretter_je_seite": len(endbretter) / (2 * len(ids)),
    }


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit("Aufruf: ... <dir_a> <dir_b> [n_partien] [out]")
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 200
    # Vierter Parameter, weil der feste Pfad sonst das Artefakt der VORIGEN
    # Messung ueberschreibt (Anlass-Messung "v2-Vorzug"). Ein zweiter Lauf mit
    # anderer Frage darf den ersten Befund nicht loeschen.
    out_path = sys.argv[4] if len(sys.argv) > 4 else "evaluations/artifacts/corpus_state_diversity.json"
    t0 = time.time()
    ergebnisse = [auswerten(v, n) for v in sys.argv[1:3]]
    for e in ergebnisse:
        print(f"\n=== {e['verzeichnis']} ===")
        print(f"  Partien {e['partien']}, Records {e['records']}")
        print(f"  distinkte (Runde, Brettmaske)      : {e['distinkte_zustaende']:,}")
        print(f"  davon in >1 Vorkommen              : {e['mehrfach_vorkommend']:,} "
              f"({100*e['mehrfach_anteil']:.1f} %)")
        print(f"  distinkte je Partie                : {e['distinkte_je_partie']:.1f}")
        print(f"  distinkte je Record                : {e['distinkte_je_record']:.3f}")
        print(f"  distinkte ENDbretter (von {2*e['partien']} Seiten): {e['distinkte_endbretter']:,} "
              f"= {100*e['endbretter_je_seite']:.1f} %")
    a, b = ergebnisse
    print(f"\nVerhaeltnis A/B distinkte Zustaende : {a['distinkte_zustaende']/b['distinkte_zustaende']:.3f}")
    print(f"Verhaeltnis A/B je Record          : {a['distinkte_je_record']/b['distinkte_je_record']:.3f}")
    wand = time.time() - t0
    print(f"\nLaufzeit {wand:.1f} s")

    erg = {
        "anlass": "der v2-Vorzug setzt den Zug ohne Suche und umgeht play_temp",
        "arme": ergebnisse,
        "verhaeltnis_distinkte_zustaende": a["distinkte_zustaende"] / b["distinkte_zustaende"],
        "verhaeltnis_je_record": a["distinkte_je_record"] / b["distinkte_je_record"],
        "einschraenkung": "gemessen ist BRETT-Vielfalt (Runde + 36-Bit-Fuellmaske), nicht "
                          "Trajektorien-Vielfalt. Fuer den Value-Kopf die richtige Groesse, "
                          "ueber die Breite der Policy-Exploration sagt sie nichts.",
        "laufzeit": {"wanduhr_s": round(wand, 1), "cpu_s": round(time.process_time(), 1),
                     "threads": 1, "s_je_partie": round(wand / max(1, 2 * n), 3)},
    }
    ziel = pathlib.Path(out_path)  # konvention-ok: Bestandsname dieser Datei, hier nur der Wert geaendert
    ziel.parent.mkdir(parents=True, exist_ok=True)
    for _ in range(5):
        try:
            ziel.write_text(json.dumps(erg, indent=2, ensure_ascii=False),
                            encoding="utf-8", newline="\n")
            print(f"Artefakt: {ziel}")
            break
        except OSError as e:
            print("Retry:", e, flush=True)
            time.sleep(1)
