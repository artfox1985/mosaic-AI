#!/usr/bin/env python
"""PREREG_bootstrap_horizon.md Stufe 1: das KOSTEN-GATE.

Frage: was kostet es, je Rundenuebergang BEIDE Bootstrap-Labels
(Horizont 2 und 3) mitzuschreiben, statt nur eines? Vorregistrierte
Entscheidungsregel: Aufschlag <= +25 Prozent Self-Play-Zeit -> Stufe 2 wird
gefahren; > +25 Prozent -> verworfen, ohne Rueckfrage.

## Abweichung vom vorregistrierten Messweg, mit Begruendung

Die Prereg nennt "Self-Play-Zeit je Partie mit einem Rollout gegen zwei
(~50 Partien, gleicher Seed)". Das setzt einen Eingriff in den Self-Play-Pfad
voraus (zweiter Rollout je Uebergang), also eine Verhaltensaenderung an genau
dem Code, dessen Paritaet die Kampagne bewacht.

Hier wird dieselbe Groesse aus ZWEI direkten Messungen zusammengesetzt, ohne
den Self-Play-Pfad anzufassen:

  A) Kosten je Label bei Horizont 2 gegen Horizont 3, GEPAART auf denselben
     Korpus-Zustaenden (`mosaic_rust.bootstrap_horizon_stage0_probe_json`,
     seit 2026-08-24 mit `horizon`-Parameter; ohne Angabe unveraendertes
     Bestandsverhalten, Paritaets-Hash geprueft).
  B) Anteil der Bootstrap-Labels an der gesamten Self-Play-Zeit, aus der
     vorhandenen Profilierung (`selfplay_profile_reset` /
     `selfplay_profile_json`, Kategorien `BootstrapValue` und
     `TotalSelfplay`).

Rechnung: beide Labels zu schreiben kostet zusaetzlich t(h=3) je Uebergang.
Der Aufschlag auf die Self-Play-Zeit ist damit

    Aufschlag = Anteil_Bootstrap * t(h=3) / t(h=2)

Beide Faktoren sind gemessen, nichts ist hergeleitet. Genau das ist der
Punkt: am 2026-08-24 wurde eine Kostenstruktur aus dem Code GESCHAETZT und
lag um Faktor 13 daneben (geschaetzt 1,5x, gemessen 20,1x fuer den
Anker-Arm) -- deshalb hier zwei Messungen statt einer Herleitung.

## Warum das Gate ueberhaupt noch laeuft

Der Anker-/rundenabhaengige Arm ist seit Stufe 0 geschlossen (Faktor 20,1).
Offen ist nur noch der klassische 2-gegen-3-Arm, und der ist strukturell
BILLIG: derselbe Ein-Stichproben-Pfad
(`bootstrap_value_after_rounds` ruft `sample_round_transition_value` mit
n_samples=1), nur eine `simulate_one_round`-Iteration mehr. Der Anker ist
dagegen die rtv-Kette mit `N_SAMPLES_TRAIN = 24` je Uebergang -- daher der
Faktor 20. Diese Sonde beziffert, ob "strukturell billig" auch "unter 25
Prozent" heisst.
"""
from __future__ import annotations

import glob
import json
import pickle
import random
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "engine" / "py"))

import mosaic_rust as mr  # noqa: E402

OUT_JSON = ROOT / "evaluations" / "bootstrap_horizon_cost_gate.json"
MODEL = str(ROOT / "models" / "alphazero_v21_2d_brierbest.onnx")

HORIZONTE = (2, 3)
N_ZUSTAENDE = 60
SELFPLAY_PARTIEN = 6
SELFPLAY_SIMS = 300
SCHWELLE = 0.25
RNG = random.Random(20260824)


def tiling_zustaende(cap: int) -> list[dict]:
    """Je Partei EIN Tiling-Zustand je Runde, wie in der Stufe-0-Sonde:
    der ERSTE Tiling-Record einer Runde. `resolve_to_pre_chance` loest ab
    jedem Tiling-Unterschritt deterministisch zum selben Vor-Chance-Zustand
    auf (dort empirisch verifiziert), die Wahl des ersten ist also keine
    Einschraenkung."""
    dateien = sorted(glob.glob(str(ROOT / "data" / "selfplay_*.pkl")))
    if not dateien:
        raise SystemExit("keine Korpus-Dateien in data/ gefunden")
    RNG.shuffle(dateien)
    raus: list[dict] = []
    for f in dateien:
        if len(raus) >= cap:
            break
        try:
            recs = pickle.load(open(f, "rb"))
        except Exception as e:  # defekte/halbe Datei ueberspringen, nicht abbrechen
            print(f"  uebersprungen ({Path(f).name}): {e}", file=sys.stderr)
            continue
        gesehen: set[tuple] = set()
        for r in recs:
            if len(raus) >= cap:
                break
            st = r.get("state") or {}
            if st.get("phase") != "tiling":
                continue
            key = (r.get("game_id"), st.get("round"))
            if key in gesehen:
                continue
            gesehen.add(key)
            raus.append(st)
    return raus


def cost_per_label(zustaende: list[dict]) -> dict:
    """A) Gepaarte Laufzeit je Horizont auf DENSELBEN Zustaenden."""
    zeiten = {h: [] for h in HORIZONTE}
    verworfen = 0
    for i, st in enumerate(zustaende):
        sj = json.dumps(st)
        seed = 880000 + i
        try:
            # Identischer Seed je Zustand ueber beide Horizonte -- gepaart.
            paar = {h: json.loads(mr.bootstrap_horizon_stage0_probe_json(sj, MODEL, seed, h))
                    for h in HORIZONTE}
        except Exception as e:
            verworfen += 1
            if verworfen <= 3:
                print(f"  Zustand verworfen: {e}", file=sys.stderr)
            continue
        for h, d in paar.items():
            zeiten[h].append(d["bootstrap_time_ms"])
        if (i + 1) % 20 == 0:
            print(f"  {i+1}/{len(zustaende)} ...", file=sys.stderr)
    if len(zeiten[2]) < 10:
        raise SystemExit("zu wenige auswertbare Zustaende")
    out = {}
    for h in HORIZONTE:
        v = zeiten[h]
        out[str(h)] = dict(n=len(v), mittel_ms=round(statistics.mean(v), 1),
                           median_ms=round(statistics.median(v), 1))
    out["verhaeltnis_h3_zu_h2_mittel"] = round(
        statistics.mean(zeiten[3]) / statistics.mean(zeiten[2]), 3)
    out["verhaeltnis_h3_zu_h2_median"] = round(
        statistics.median(zeiten[3]) / statistics.median(zeiten[2]), 3)
    out["n_verworfen"] = verworfen
    return out


def bootstrap_share() -> dict:
    """B) Anteil der Bootstrap-Labels an der Self-Play-Gesamtzeit."""
    mr.selfplay_profile_reset()
    t0 = time.time()
    # EINTHREADIG (num_threads=1) und das ist wesentlich: die Profilierung
    # summiert Nanosekunden JE THREAD. Mehrthreadig uebersteigt
    # `bootstrap_value_ns` die Wanduhr (gemessen 11,4 s gegen 9,0 s) und der
    # Anteil ist nicht mehr bildbar. `total_selfplay_ns` bleibt in diesem
    # Einstieg 0 (die Kategorie wird dort nicht bedient), die Wanduhr ist
    # deshalb der Nenner -- einthreadig ist sie der richtige.
    mr.self_play_games_with_net_labels(
        MODEL, SELFPLAY_PARTIEN, SELFPLAY_SIMS, 0.3, 20260824, 1,
        "vcostgate", False, None, None,
    )
    wand_s = time.time() - t0
    prof = json.loads(mr.selfplay_profile_json())
    return dict(profil=prof, wanduhr_s=round(wand_s, 1),
                n_partien=SELFPLAY_PARTIEN, sims=SELFPLAY_SIMS)


def main() -> None:
    print(f"A) Kosten je Label, {N_ZUSTAENDE} Korpus-Zustaende, gepaart ...", file=sys.stderr)
    zust = tiling_zustaende(N_ZUSTAENDE)
    print(f"   {len(zust)} Tiling-Zustaende gesammelt", file=sys.stderr)
    a = cost_per_label(zust)

    print(f"B) Bootstrap-Anteil an der Self-Play-Zeit "
          f"({SELFPLAY_PARTIEN} Partien) ...", file=sys.stderr)
    b = bootstrap_share()

    prof = b["profil"]
    boot_ns = prof.get("bootstrap_value_ns") or 0
    # Nenner: `total_selfplay_ns` wenn die Kategorie bedient wird, sonst die
    # einthreadige Wanduhr. Beides in Nanosekunden.
    total_ns = prof.get("total_selfplay_ns") or 0
    if not total_ns:
        total_ns = b["wanduhr_s"] * 1e9
        b["nenner"] = "einthreadige Wanduhr (total_selfplay_ns wird nicht bedient)"
    else:
        b["nenner"] = "total_selfplay_ns"
    anteil = (boot_ns / total_ns) if total_ns else None

    ergebnis = dict(
        cost_per_label=a,
        selfplay=b,
        anteil_bootstrap_an_selfplay=round(anteil, 4) if anteil is not None else None,
        profil_schluessel=sorted(prof.keys()),
    )
    if anteil is not None:
        auf = anteil * a["verhaeltnis_h3_zu_h2_mittel"]
        ergebnis["aufschlag_selfplay_zeit"] = round(auf, 4)
        ergebnis["schwelle"] = SCHWELLE
        ergebnis["verdikt"] = ("GATE BESTANDEN -- Stufe 2 darf gefahren werden"
                               if auf <= SCHWELLE else
                               "GATE GERISSEN -- vorregistriert: verworfen, ohne Rueckfrage")
    OUT_JSON.write_text(json.dumps(ergebnis, indent=2, ensure_ascii=False), encoding="utf-8")

    print()
    for h in HORIZONTE:
        d = a[str(h)]
        print(f"  Horizont {h}: Mittel {d['mittel_ms']:8.1f} ms   "
              f"Median {d['median_ms']:8.1f} ms   (n={d['n']})")
    print(f"  Verhaeltnis h3/h2: {a['verhaeltnis_h3_zu_h2_mittel']} (Mittel), "
          f"{a['verhaeltnis_h3_zu_h2_median']} (Median)")
    print(f"\n  Bootstrap-Anteil an der Self-Play-Zeit: {ergebnis['anteil_bootstrap_an_selfplay']}")
    if "aufschlag_selfplay_zeit" in ergebnis:
        print(f"  -> Aufschlag fuer BEIDE Labels: "
              f"{100*ergebnis['aufschlag_selfplay_zeit']:.1f} % "
              f"(Schwelle {100*SCHWELLE:.0f} %)")
        print(f"  {ergebnis['verdikt']}")
    print(f"\n-> {OUT_JSON}")


if __name__ == "__main__":
    main()
