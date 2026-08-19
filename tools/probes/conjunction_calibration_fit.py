"""Kalibrierung des Konjunktions-Kopfes auf dem ausgesperrten Bewertungssatz.

Fit je Atomgruppe: p_kal = sigmoid(B * logit(p_roh) + A).

WARUM SO (Befundlage 2026-08-18, Einzelheiten in STATUS.md):
  * Der MITTELWERT-Versatz ist klein und keine Aufgabe (k1 0,35 Log-Odds).
    Offen ist die STEIGUNG -- der Kopf ueberschaetzt im oberen Bereich
    (Bauer-Arme: vorhergesagt 88 %, tatsaechlich 60 %).
  * Der obere Bereich existiert im normalen Spiel nicht (k1 3 Faelle von 7200,
    k2 null). Deshalb wird auf dem Bauer-lastigen Bewertungssatz gefittet.
  * GEPOOLT je Gruppe, nicht je Atom: die Arme schliessen bevorzugt die
    AEUSSEREN Spalten, ein Fit je Atom wuerde diese Geometrie erben.

Fit-Satz  : Arme a / k1 / k2 / k5 aus data/holdout
Transfer  : Arm heur -- der einzige plattenBEWUSSTE Spieler im Satz. Er prueft
            die Annahme, dass eine auf Bauer-Partien gefittete Kennlinie auf
            eine andere Politik uebertraegt. NICHT im Fit enthalten.

Die (A,B) sind MODELLSPEZIFISCH. Ein neuer Champion braucht einen neuen Fit --
der Bewertungssatz bleibt derselbe.

Aufruf: python conjunction_calibration_fit.py [checkpoint] [partien_je_arm]
"""
import collections
import glob
import json
import pickle
import re
import sys
from pathlib import Path

import numpy as np
import torch

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "engine" / "py"))
sys.path.insert(0, str(REPO / "tools" / "probes"))
import ownership_gate_a as GA  # noqa: E402

GRUPPEN = {
    "Reihen k0":      (0, 6),
    "Spalten k1":     (6, 12),
    "Diagonalen k2":  (12, 14),
    "Ecken k5":       (14, 18),
    "Joker k3":       (18, 19),
    "farbenreich k7": (19, 25),
    "Layout":         (25, 34),
}
FIT_ARME = ("a", "k1", "k2", "k5")
TRANSFER_ARM = "heur"
RUNDEN = (1, 2, 3, 4, 5)
CHECKPOINT = sys.argv[1] if len(sys.argv) > 1 else "alphazero_v21-b19_best.pth"
PARTIEN_JE_ARM = int(sys.argv[2]) if len(sys.argv) > 2 else 0   # 0 = alle
EPS = 1e-6


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def logit(p):
    p = np.clip(np.asarray(p, dtype=np.float64), EPS, 1 - EPS)
    return np.log(p / (1 - p))


def brier(y, p):
    return float(np.mean((np.asarray(p) - np.asarray(y)) ** 2))


def fit_platt(x, y, iterationen=100):
    """y ~ sigmoid(B*x + A) per IRLS. Gibt (B, A) zurueck, None bei Entartung."""
    X = np.column_stack([np.asarray(x, dtype=np.float64), np.ones(len(x))])
    y = np.asarray(y, dtype=np.float64)
    w = np.array([1.0, 0.0])
    for _ in range(iterationen):
        eta = X @ w
        p = sigmoid(eta)
        W = np.clip(p * (1 - p), 1e-12, None)
        z = eta + (y - p) / W
        A = X.T @ (X * W[:, None]) + 1e-8 * np.eye(2)
        try:
            neu = np.linalg.solve(A, X.T @ (W * z))
        except np.linalg.LinAlgError:
            return None
        if not np.all(np.isfinite(neu)):
            return None
        fertig = np.abs(neu - w).max() < 1e-10
        w = neu
        if fertig:
            break
    if abs(w[0]) > 50 or abs(w[1]) > 50:
        return None
    return float(w[0]), float(w[1])


def fit_glm(X, y, iterationen=100):
    """IRLS fuer beliebig viele Spalten -- gebraucht fuer V3 (geteilte Steigung
    je Runde + Versatz je Gruppe). Gibt den Koeffizientenvektor zurueck."""
    X = np.asarray(X, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    w = np.zeros(X.shape[1])
    for _ in range(iterationen):
        eta = X @ w
        pr = sigmoid(eta)
        W = np.clip(pr * (1 - pr), 1e-12, None)
        z = eta + (y - pr) / W
        A = X.T @ (X * W[:, None]) + 1e-8 * np.eye(X.shape[1])
        try:
            neu = np.linalg.solve(A, X.T @ (W * z))
        except np.linalg.LinAlgError:
            return None
        if not np.all(np.isfinite(neu)):
            return None
        fertig = np.abs(neu - w).max() < 1e-10
        w = neu
        if fertig:
            break
    return w


def sammle_zustaende(dateien, partien_je_arm=0):
    """Je Partie EIN Zustand je Runde (mittlerer Record der Runde) + Endlabel."""
    states, cps, labels, runden = [], [], [], []
    n_partien = 0
    for f in sorted(dateien):
        with open(f, "rb") as fh:
            daten = pickle.load(fh)
        je_spiel = collections.defaultdict(list)
        for s in daten:
            je_spiel[s["game_id"]].append(s)
        for _gid, recs in je_spiel.items():
            if not recs[-1].get("completed"):
                continue
            if partien_je_arm and n_partien >= partien_je_arm:
                break
            _o0, _o1, c0, c1 = GA.game_labels(recs[-1])
            lab = (c0, c1)
            nach_runde = collections.defaultdict(list)
            for r in recs:
                nach_runde[r["state"].get("round")].append(r)
            for rnd in RUNDEN:
                gruppe = nach_runde.get(rnd)
                if not gruppe:
                    continue
                rec = gruppe[len(gruppe) // 2]
                states.append(rec["state"])
                cps.append(rec["state"].get("current_player", 0))
                labels.append(lab)
                runden.append(rnd)
            n_partien += 1
        if partien_je_arm and n_partien >= partien_je_arm:
            break
    return states, cps, labels, runden


def vorhersagen(model, states, cps, labels):
    """-> (p_ego [2N,34], label_ego [2N,34]); beide Haelften uebereinandergestapelt."""
    planes, flat = GA.encode_states(states)
    p = GA.predict_ownership(model, planes, flat)
    O = 36
    conj_me = p[:, 2 * O: 2 * O + 34]
    conj_op = p[:, 2 * O + 34: 2 * O + 68]
    lab_me = np.stack([labels[i][cps[i]] for i in range(len(states))])
    lab_op = np.stack([labels[i][1 - cps[i]] for i in range(len(states))])
    return (np.concatenate([conj_me, conj_op], axis=0),
            np.concatenate([lab_me, lab_op], axis=0))


def main():
    arme = collections.defaultdict(list)
    for f in glob.glob(str(REPO / "data" / "holdout" / "*.pkl")):
        m = re.match(r"selfplay_hold_([a-z0-9]+)_", Path(f).name)
        if m:
            arme[m.group(1)].append(f)
    if not arme:
        sys.exit("ABBRUCH: keine Dateien in data/holdout gefunden.")

    ck = torch.load(REPO / "models" / CHECKPOINT, map_location="cpu", weights_only=False)
    model, _enc = GA.build_model_from_checkpoint(ck)
    model.eval().to(GA.DEVICE)
    print(f"Checkpoint {CHECKPOINT} auf {GA.DEVICE}", flush=True)

    cache = REPO / "evaluations" / f"conjunction_calibration_cache_{CHECKPOINT}.npz"
    daten = {}
    if PARTIEN_JE_ARM == 0 and cache.exists():
        roh = np.load(cache)
        for arm in list(FIT_ARME) + [TRANSFER_ARM]:
            if f"{arm}_p" in roh:
                daten[arm] = (roh[f"{arm}_p"], roh[f"{arm}_y"], roh[f"{arm}_r"])
        print(f"Vorhersagen aus Cache: {cache.name}", flush=True)
    if not daten:
        for arm in list(FIT_ARME) + [TRANSFER_ARM]:
            if arm not in arme:
                print(f"  !! Arm {arm} fehlt -- uebersprungen")
                continue
            st, cp, lb, rd = sammle_zustaende(arme[arm], PARTIEN_JE_ARM)
            p, y = vorhersagen(model, st, cp, lb)
            daten[arm] = (p, y, np.array(rd + rd))
            print(f"  Arm {arm}: {len(arme[arm])} Dateien -> {len(st)} Zustaende, "
                  f"{p.shape[0]} Bretter", flush=True)
        if PARTIEN_JE_ARM == 0:
            np.savez_compressed(cache, **{f"{a}_{k}": v
                                          for a, drei in daten.items()
                                          for k, v in zip(("p", "y", "r"), drei)})
            print(f"Vorhersagen zwischengespeichert: {cache.name}", flush=True)
    print()

    vorhanden = [a for a in FIT_ARME if a in daten]
    p_fit = np.concatenate([daten[a][0] for a in vorhanden])
    y_fit = np.concatenate([daten[a][1] for a in vorhanden])
    r_fit = np.concatenate([daten[a][2] for a in vorhanden])
    hat_transfer = TRANSFER_ARM in daten

    kopf = f"FIT je Gruppe -- Fit-Satz {p_fit.shape[0]} Bretter aus {'/'.join(vorhanden)}"
    if hat_transfer:
        kopf += f", Transfer {daten[TRANSFER_ARM][0].shape[0]} aus {TRANSFER_ARM}"
    print("=" * 100)
    print(kopf)
    print("=" * 100)
    print(f"{'Gruppe':16s} {'Pos':>7s} {'B':>7s} {'A':>7s} "
          f"{'Brier vor':>10s} {'Brier nach':>11s} {'Gewinn':>8s} "
          f"{'Transf. vor':>12s} {'nach':>11s} {'Gewinn':>8s}")
    ergebnis = {}
    for g, (a, b) in GRUPPEN.items():
        x = logit(p_fit[:, a:b].ravel())
        y = y_fit[:, a:b].ravel().astype(float)
        k = int(y.sum())
        w = fit_platt(x, y)
        if w is None:
            print(f"{g:16s} {k:7d}   -- kein Fit (Entartung)")
            continue
        B, A = w
        vor, nach = brier(y, sigmoid(x)), brier(y, sigmoid(B * x + A))
        zeile = (f"{g:16s} {k:7d} {B:7.3f} {A:7.3f} {vor:10.6f} {nach:11.6f} "
                 f"{100*(vor-nach)/vor:7.1f}%")
        eintrag = {"B": B, "A": A, "positive": k, "brier_vor": vor, "brier_nach": nach}
        if hat_transfer:
            pt, yt_all, _ = daten[TRANSFER_ARM]
            xt = logit(pt[:, a:b].ravel())
            yt = yt_all[:, a:b].ravel().astype(float)
            tvor, tnach = brier(yt, sigmoid(xt)), brier(yt, sigmoid(B * xt + A))
            zeile += f" {tvor:12.6f} {tnach:11.6f} {100*(tvor-tnach)/tvor:7.1f}%"
            eintrag.update({"transfer_positive": int(yt.sum()),
                            "transfer_brier_vor": tvor, "transfer_brier_nach": tnach})
        print(zeile)
        ergebnis[g] = eintrag

    print()
    print("=" * 100)
    print("KENNLINIE OBEN, vor und nach dem Fit (Fit-Satz)")
    print("=" * 100)
    BINS = [0.5, 0.7, 0.85, 1.0001]
    for g in ("Spalten k1", "Diagonalen k2", "Ecken k5"):
        if g not in ergebnis:
            continue
        a, b = GRUPPEN[g]
        x = logit(p_fit[:, a:b].ravel())
        y = y_fit[:, a:b].ravel().astype(float)
        pv = sigmoid(x)
        pn = sigmoid(ergebnis[g]["B"] * x + ergebnis[g]["A"])
        print(f"\n{g}:")
        print(f"{'Bin':>12s} {'Faelle':>8s} {'vorher':>9s} {'nachher':>9s} {'tatsaechlich':>13s}")
        for i in range(len(BINS) - 1):
            m = (pv >= BINS[i]) & (pv < BINS[i + 1])
            n = int(m.sum())
            if n == 0:
                continue
            grenze = f"{BINS[i]:.2f}-{min(BINS[i+1], 1.0):.2f}"
            print(f"{grenze:>12s} {n:8d} {100*pv[m].mean():8.1f}% "
                  f"{100*pn[m].mean():8.1f}% {100*y[m].mean():12.1f}%")

    print()
    print("=" * 100)
    print("VARIANTEN-VERGLEICH -- entschieden wird am TRANSFER, nicht am Fit")
    print("=" * 100)
    print("V0 = keine Korrektur | V1 = je Gruppe | V2 = je Gruppe UND Runde")
    print("V3 = Steigung je RUNDE (ueber die Gruppen geteilt) + Versatz je Gruppe")
    print("V3 hat 5+6 statt 2x6 (V1) bzw. 2x30 (V2) Parameter -- weniger Freiheit,")
    print("mehr Aussicht auf Transfer, und sie folgt dem gemessenen Muster.")
    print()

    KRIT = [g for g in GRUPPEN if g != "Layout"]

    def stapel(quelle):
        """-> x (Logit), y, runde, gruppenindex; alle Kriteriumsgruppen untereinander."""
        pp, yy, rr = quelle
        xs, ys, rs, gs = [], [], [], []
        for gi, g in enumerate(KRIT):
            a, b = GRUPPEN[g]
            n_at = b - a
            xs.append(logit(pp[:, a:b]).ravel())
            ys.append(yy[:, a:b].ravel().astype(float))
            rs.append(np.repeat(rr, n_at))
            gs.append(np.full(n_at * pp.shape[0], gi))
        return (np.concatenate(xs), np.concatenate(ys),
                np.concatenate(rs), np.concatenate(gs))

    def design_v3(x, r, g):
        sp = [np.where(r == rnd, x, 0.0) for rnd in RUNDEN]
        ic = [(g == gi).astype(float) for gi in range(len(KRIT))]
        return np.column_stack(sp + ic)

    xf, yf, rf, gf = stapel((p_fit, y_fit, r_fit))
    w3 = fit_glm(design_v3(xf, rf, gf), yf)

    v2 = {}
    for gi, g in enumerate(KRIT):
        for rnd in RUNDEN:
            m = (gf == gi) & (rf == rnd)
            v2[(g, rnd)] = fit_platt(xf[m], yf[m]) if yf[m].sum() >= 5 else None

    def anwenden(variante, x, r, g):
        if variante == "V0":
            return sigmoid(x)
        if variante == "V1":
            B = np.array([ergebnis[KRIT[i]]["B"] if KRIT[i] in ergebnis else 1.0 for i in range(len(KRIT))])
            A = np.array([ergebnis[KRIT[i]]["A"] if KRIT[i] in ergebnis else 0.0 for i in range(len(KRIT))])
            return sigmoid(B[g] * x + A[g])
        if variante == "V2":
            eta = np.empty_like(x)
            for gi, gg in enumerate(KRIT):
                for rnd in RUNDEN:
                    m = (g == gi) & (r == rnd)
                    w = v2[(gg, rnd)]
                    eta[m] = (w[0] * x[m] + w[1]) if w else x[m]
            return sigmoid(eta)
        if variante == "V3":
            if w3 is None:
                return sigmoid(x)
            return sigmoid(design_v3(x, r, g) @ w3)
        raise ValueError(variante)

    if w3 is not None:
        print("V3-Steigungen je Runde: "
              + "  ".join(f"R{r} {w3[i]:.3f}" for i, r in enumerate(RUNDEN)))
        print("V3-Versatz je Gruppe:   "
              + "  ".join(f"{g.split()[-1]} {w3[len(RUNDEN)+i]:+.3f}"
                          for i, g in enumerate(KRIT)))
    print()

    saetze = [("FIT-Satz", (p_fit, y_fit, r_fit))]
    if hat_transfer:
        saetze.append((f"TRANSFER {TRANSFER_ARM}", daten[TRANSFER_ARM]))
    for name, quelle in saetze:
        x, y, r, g = stapel(quelle)
        print(f"--- {name}  ({int(y.sum())} Positive, {len(y)} Paare)")
        print(f"{'Gruppe':16s} {'Pos':>7s} " + " ".join(f"{v:>11s}" for v in ("V0", "V1", "V2", "V3")))
        pv = {v: anwenden(v, x, r, g) for v in ("V0", "V1", "V2", "V3")}
        for gi, gg in enumerate(KRIT):
            m = g == gi
            zellen = [f"{brier(y[m], pv[v][m]):11.6f}" for v in ("V0", "V1", "V2", "V3")]
            print(f"{gg:16s} {int(y[m].sum()):7d} " + " ".join(zellen))
        gesamt = [brier(y, pv[v]) for v in ("V0", "V1", "V2", "V3")]
        print(f"{'GESAMT':16s} {int(y.sum()):7d} " + " ".join(f"{b:11.6f}" for b in gesamt))
        print(f"{'  vs V0':16s} {'':7s} " + " ".join(
            f"{100*(gesamt[0]-b)/gesamt[0]:10.2f}%" for b in gesamt))
        print()

    print("Entscheidungsregel (vorab): eine Variante wird nur gebaut, wenn sie im")
    print("TRANSFER besser ist als V0 -- im Fit-Satz ist jede Variante per")
    print("Konstruktion besser, das entscheidet nichts.")

    ziel = REPO / "evaluations" / "conjunction_calibration_fit.json"
    ziel.write_text(json.dumps({"checkpoint": CHECKPOINT, "fit_arme": vorhanden,
                                "transfer_arm": TRANSFER_ARM, "gruppen": ergebnis},
                               indent=1), encoding="utf-8")
    print(f"\nRohzahlen -> {ziel}")


if __name__ == "__main__":
    main()
