"""Was sagt der Konjunktions-Kopf im NORMALEN Spiel voraus -- und was passiert?

WARUM DIESE SONDE (Befund 2026-08-17): der Versatz DELTA laesst sich zwar aus
zwei Label-Grundraten herleiten, aber das Ergebnis haengt daran, WELCHE
Referenz man fuer den Prior des Kopfes nimmt:

  * Bauer-Arme allein   -> k1: 2,43 % gegen 0,57 %  => DELTA = 1,47
  * Trainingsmischung   -> k1: ~0,93 % gegen 0,57 % => DELTA = 0,49

Faktor 3 zwischen zwei gleich plausiblen Herleitungen. Also nicht herleiten,
sondern messen: der Kopf wird auf normale Partien losgelassen und sein
MITTELWERT gegen die tatsaechliche Rate derselben Partien gestellt.

  DELTA_gemessen = logit(mittel(p_vorhergesagt)) - logit(rate_tatsaechlich)

Das ist genau die Zahl, die net_mcts.rs:1681 vor dem Sigmoid abziehen muss.
Kein ausgesperrter Bewertungssatz noetig: verglichen wird der Mittelwert des
Kopfes mit der LABEL-Rate, und dafuer waere ein Ueberfitten des Kopfes auf
seine Trainingsdateien ein konservativer Fehler (es macht DELTA kleiner, nicht
groesser). Der Bewertungssatz bleibt noetig, um B~1 zu pruefen -- also ob es
wirklich ein reiner Versatz ist und keine Stauchung.

ERGEBNIS DES ERSTEN LAUFS (b19_best, 150 Dateien, 1500 Partien, 3000 Bretter):
DELTA ist bei allen Gruppen ausser k2 KLEIN -- k1 0,35 statt der hergeleiteten
1,47, k0/k5/k3/k7/Layout praktisch null. Die geplante Platt-Korrektur je
Atomgruppe ist damit gegenstandslos; Einzelheiten in STATUS.md.

Dazu der Nutzer-Einwand, der auch die verbliebenen 0,35 entwertet: die
Normalspiel-Rate stammt aus Partien von Netzen, die die Wertungsplatten NICHT
beruecksichtigen. Den Kopf darauf zu eichen hiesse, ihn auf genau das Verhalten
zu kalibrieren, das das Projektziel abschaffen will.

Aufruf:  python conjunction_marginal_normal_play.py [dateien_je_praefix] [checkpoint]
"""
import collections
import glob
import re
import sys
from pathlib import Path

import numpy as np
import torch

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))                      # config.py liegt in der Wurzel
sys.path.insert(0, str(REPO / "engine" / "py"))
sys.path.insert(0, str(REPO / "tools" / "probes"))

# Bestandssonde wiederverwenden statt nachbauen (CLAUDE.md: erst schauen, was da
# ist). Von dort kommen Encoder, Modellbau und die Inferenz -- damit misst diese
# Sonde denselben Pfad wie Tor A und ist mit dessen Zahlen vergleichbar.
import ownership_gate_a as GA  # noqa: E402

GRUPPEN = {
    "Reihen k0":         (0, 6),
    "Spalten k1":        (6, 12),
    "Diagonalen k2":     (12, 14),
    "Ecken k5":          (14, 18),
    "Joker k3":          (18, 19),
    "farbenreich k7":    (19, 25),
    "Layout (k3-Input)": (25, 34),
}
DATEIEN_JE_PRAEFIX = int(sys.argv[1]) if len(sys.argv) > 1 else 30
CHECKPOINT = sys.argv[2] if len(sys.argv) > 2 else "alphazero_v21-b19_best.pth"


def praefix(name):
    m = re.match(r"selfplay_(.+?)_\d{8}_", name)
    return m.group(1) if m else "?"


def stichprobe(dateien, k):
    d = sorted(dateien)
    if len(d) <= k:
        return d
    schritt = len(d) / k
    return [d[int(i * schritt)] for i in range(k)]


def logit(p):
    p = min(max(float(p), 1e-9), 1 - 1e-9)
    return float(np.log(p / (1 - p)))


def main():
    quellen = collections.defaultdict(list)
    for f in glob.glob(str(REPO / "data" / "*.pkl")):
        quellen[praefix(Path(f).name)].append(f)
    dateien = []
    for q in sorted(quellen):
        dateien += stichprobe(quellen[q], DATEIEN_JE_PRAEFIX)
    print(f"{len(dateien)} Normalspiel-Dateien aus {len(quellen)} Generationen "
          f"({DATEIEN_JE_PRAEFIX} je Praefix)", flush=True)

    end_states, mid_states, end_cp, mid_cp, lab_conj = [], [], [], [], []
    n_games = n_skip = 0
    for f in dateien:
        for _gid, rec, mid in GA.iter_games(f):
            if not rec.get("completed") or mid is None:
                n_skip += 1
                continue
            _o0, _o1, c0, c1 = GA.game_labels(rec)
            lab_conj.append((c0, c1))
            end_states.append(rec["state"])
            end_cp.append(rec["state"].get("current_player", 0))
            mid_states.append(mid["state"])
            mid_cp.append(mid["state"].get("current_player", 0))
            n_games += 1
    print(f"{n_games} vollstaendige Partien ({n_skip} uebersprungen)", flush=True)

    print("Encoding ...", flush=True)
    end_planes, end_flat = GA.encode_states(end_states)
    mid_planes, mid_flat = GA.encode_states(mid_states)

    ck = torch.load(REPO / "models" / CHECKPOINT, map_location="cpu", weights_only=False)
    model, _enc = GA.build_model_from_checkpoint(ck)
    model.eval().to(GA.DEVICE)
    print(f"Checkpoint {CHECKPOINT} (Epochen {ck.get('epochs')}) auf {GA.DEVICE}", flush=True)

    p_end = GA.predict_ownership(model, end_planes, end_flat)
    p_mid = GA.predict_ownership(model, mid_planes, mid_flat)
    breite = p_end.shape[1]
    if breite < 140:
        sys.exit(f"ABBRUCH: Kopf ist {breite} breit, ohne Konjunktionsteil "
                 f"(<140) gibt es hier nichts zu messen.")

    O = 36  # OWNERSHIP_TARGETS je Spieler
    for name, p_all, cps in (("Runde 3 (Suchzustand)", p_mid, mid_cp),
                             ("Endzustand", p_end, end_cp)):
        # Ego-/Gegner-Haelfte des Konjunktionsblocks, wie net_mcts.rs:1677
        conj_me = p_all[:, 2 * O: 2 * O + 34]
        conj_op = p_all[:, 2 * O + 34: 2 * O + 68]
        lab_me = np.stack([lab_conj[i][cps[i]] for i in range(n_games)])
        lab_op = np.stack([lab_conj[i][1 - cps[i]] for i in range(n_games)])
        vorher = np.concatenate([conj_me, conj_op], axis=0)
        label = np.concatenate([lab_me, lab_op], axis=0)

        print("\n" + "=" * 84)
        print(f"{name} -- {vorher.shape[0]} Bretter, Checkpoint {CHECKPOINT}")
        print("=" * 84)
        print(f"{'Gruppe':20s} {'Kopf-Mittel':>12s} {'tatsaechlich':>13s} "
              f"{'Faktor':>8s} {'DELTA':>8s} {'Pos':>6s} {'+/-':>7s}")
        for g, (a, b) in GRUPPEN.items():
            p_m = float(vorher[:, a:b].mean())
            n = label[:, a:b].size
            k = int(label[:, a:b].sum())
            p_l = k / n
            d = logit(p_m) - logit(p_l)
            # Stichprobenfehler der LABEL-Seite in Log-Odds (die Kopfseite ist
            # ein Mittel ueber viele Werte und traegt dagegen kaum bei)
            se = (1.0 / np.sqrt(k)) if k > 0 else float("nan")
            print(f"{g:20s} {100*p_m:11.3f}% {100*p_l:12.3f}% "
                  f"{p_m/p_l if p_l > 0 else float('inf'):7.1f}x {d:8.2f} "
                  f"{k:6d} {se:7.2f}")

    print("\nDELTA ist der Wert, den net_mcts.rs vor dem Sigmoid abziehen muss.")
    print("Positiv = der Kopf ueberschaetzt im normalen Spiel.")
    print("'+/-' ist der Stichprobenfehler in Log-Odds (1/sqrt(Positive)).")
    print("\nVORBEHALT: geprueft ist damit nur der MITTELWERT (Versatz, B=1).")
    print("Ob die Kennlinie zusaetzlich gestaucht ist, sagt diese Sonde NICHT --")
    print("dafuer braucht es den ausgesperrten Bewertungssatz.")


if __name__ == "__main__":
    main()
